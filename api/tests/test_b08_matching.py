"""B-08: the LLM judge in API-07, its labeled fallbacks (cached result, embedding only, 503), the
committed cache, and the gold set and scoring that chose the judge (scripts/eval_matching.py).
Gemini is always faked here; the real judge is exercised by TC-08 in test_a10_matching.py."""

import json
from collections import Counter
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app import ams, config, db, seed
from scripts import eval_matching
from tests.conftest import ISSUE_REQUEST
from tests.test_a04_auth_rbac import assert_error
from tests.test_a10_matching import FRONTEND, SECURITY, FakeGemini, gemini, match, valid_verification  # noqa: F401  (fixture)

Conn = db.psycopg.Connection[db.DictRow]
SHARED = sorted(ISSUE_REQUEST["skills"])  # type: ignore[arg-type]
CATALOG = {skill_id: {"label": label, "aliases": aliases} for skill_id, label, aliases in seed.SKILLS}


def cache_entry(description: str, *, computed_at: str = "2026-11-20T10:00:00Z") -> tuple[str, dict[str, Any]]:
    skills = [CATALOG[s] for s in SHARED]
    entry = {
        "skills": skills,
        "description": description,
        "matchedSkills": [{"skill": "OWASP Top 10", "requirement": "memahami OWASP Top 10", "similarity": 0.78, "reason": "Named directly."}],
        "missingRequirements": [{"requirement": "memantau log dengan SIEM", "note": "No skill covers SIEM monitoring."}],
        "modelVersion": f"{ams.MODEL_VERSION} + {ams.JUDGE_MODEL} judge",
        "computedAt": computed_at,
    }
    return ams.cache_key(skills, description), entry


# --- Judged result -----------------------------------------------------------------------


def test_b08_judge_decides_and_writes_the_reason(client: TestClient, conn: Conn, gemini: FakeGemini) -> None:
    verification_id = valid_verification(client)
    response = match(client, verification_id)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["modelVersion"] == f"{ams.MODEL_VERSION} + {ams.JUDGE_MODEL} judge"
    assert body["limitations"] == ams.LIMITATIONS and ams.JUDGE_MODEL in body["limitations"][2]
    assert body["matchedSkills"], "the fake judge matches requirements that share a word with a skill"
    assert all(m["reason"].startswith("Shares a word with") and 0 <= m["similarity"] <= 1 for m in body["matchedSkills"])
    assert {"requirement": "memantau log dengan SIEM", "note": ams.NOT_CLOSE} in body["missingRequirements"]

    call = gemini.judge_calls[0]
    assert call["url"] == f"{ams.GEMINI_API}/{ams.JUDGE_MODEL}:generateContent"
    config_ = call["json"]["generationConfig"]
    assert config_["temperature"] == 0 and config_["responseMimeType"] == "application/json"
    verdict = config_["responseSchema"]["properties"]["verdicts"]["items"]["properties"]
    assert verdict["skill"]["enum"] == ["S1", "S2", "S3", "NONE"]
    assert verdict["requirement"]["enum"] == ["R1", "R2", "R3", "R4"]
    assert call["json"]["systemInstruction"]["parts"][0]["text"] == ams.JUDGE_PROMPT


def test_b08_judge_similarity_is_the_embedding_similarity_of_the_chosen_pair(monkeypatch: pytest.MonkeyPatch) -> None:
    import numpy as np

    skills = [{"label": "A", "aliases": []}, {"label": "B", "aliases": ["b2"]}]
    vectors = {"r": np.array([1.0, 0.0]), "A": np.array([0.0, 1.0]), "B": np.array([1.0, 1.0]), "b2": np.array([1.0, 0.2])}
    scores = ams.pair_scores(["r"], skills, vectors, vectors)
    monkeypatch.setattr(ams, "judge", lambda *a, **k: [ams.Verdict(1, "B covers r.")])
    rec = ams.judged(["r"], skills, scores, "emb")
    assert rec.matched[0].skill == "B" and rec.matched[0].similarity == round(float(1 / np.sqrt(1.04)), 2)
    assert rec.model_version == f"emb + {ams.JUDGE_MODEL} judge"


def test_b08_candidate_floor_offers_only_close_skills_and_skips_the_rest(monkeypatch: pytest.MonkeyPatch) -> None:
    scores = [[(0.75, "A"), (0.55, "B")], [(0.40, "A"), (0.59, "B")]]
    assert ams.candidates_for(scores, 0.60) == [[0], []]
    assert ams.candidates_for(scores, None) == [[0, 1], [0, 1]]
    fake = FakeGemini()
    monkeypatch.setattr(ams.httpx, "post", fake)
    verdicts = ams.judge(["r1", "r2"], [{"label": "A", "aliases": ["r1"]}, {"label": "B", "aliases": []}], ams.candidates_for(scores, 0.60))
    sent = json.loads(fake.judge_calls[0]["json"]["contents"][0]["parts"][0]["text"])
    assert [r["text"] for r in sent["requirements"]] == ["r1"] and sent["requirements"][0]["candidates"] == ["S1"]
    assert verdicts[0].skill == 0 and verdicts[1] == ams.Verdict(None, ams.NOT_CLOSE)


def test_b08_judge_is_not_called_when_no_requirement_has_a_candidate(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ams.httpx, "post", lambda *a, **k: pytest.fail("no call expected"))
    assert ams.judge(["x", "y"], [{"label": "A", "aliases": []}], [[], []]) == [ams.Verdict(None, ams.NOT_CLOSE)] * 2


@pytest.mark.parametrize(
    "answer",
    [
        "not json",
        json.dumps({"verdicts": []}),  # a requirement left out
        json.dumps({"verdicts": [{"requirement": "R1", "reason": "x", "skill": "S9"}]}),  # unknown skill
        json.dumps({"verdicts": [{"requirement": "R1", "reason": "", "skill": "NONE"}]}),  # no reason
        json.dumps({"verdicts": [{"requirement": "R1", "reason": "a", "skill": "NONE"}, {"requirement": "R1", "reason": "b", "skill": "NONE"}]}),
    ],
)
def test_b08_malformed_judge_answer_raises(monkeypatch: pytest.MonkeyPatch, answer: str) -> None:
    fake = FakeGemini()
    fake.judge_text = answer
    monkeypatch.setattr(ams.httpx, "post", fake)
    with pytest.raises(ams.JudgeFailed):
        ams.judge(["r"], [{"label": "A", "aliases": []}], [[0]])


def test_b08_judge_cannot_pick_a_skill_that_was_not_a_candidate(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeGemini()
    fake.judge_text = json.dumps({"verdicts": [{"requirement": "R1", "reason": "B fits.", "skill": "S2"}]})
    monkeypatch.setattr(ams.httpx, "post", fake)
    with pytest.raises(ams.JudgeFailed):
        ams.judge(["r"], [{"label": "A", "aliases": []}, {"label": "B", "aliases": []}], [[0]])


# --- Labeled fallbacks -------------------------------------------------------------------


def test_b08_judge_down_falls_back_to_embedding_only_and_says_so(client: TestClient, conn: Conn, gemini: FakeGemini) -> None:
    verification_id = valid_verification(client)
    gemini.judge_status = 429
    body = match(client, verification_id).json()
    assert body["label"] == "REKOMENDASI"
    assert body["modelVersion"] == f"{ams.MODEL_VERSION}; judge unavailable, embedding only"
    assert body["limitations"] == ams.LIMITATIONS_EMBEDDING_ONLY
    assert all(m["similarity"] >= ams.THRESHOLD for m in body["matchedSkills"])
    stored = conn.execute("SELECT model_version FROM matchings").fetchone()
    assert stored == {"model_version": body["modelVersion"]}


def test_b08_judge_down_prefers_a_cached_judged_result(client: TestClient, gemini: FakeGemini, monkeypatch: pytest.MonkeyPatch) -> None:
    key, entry = cache_entry(SECURITY["description"])
    monkeypatch.setattr(ams, "_cache", {key: entry})
    verification_id = valid_verification(client)
    gemini.judge_text = "not json"
    body = match(client, verification_id).json()
    assert body["modelVersion"] == f"{entry['modelVersion']} · cached 2026-11-20"
    assert body["matchedSkills"] == entry["matchedSkills"]
    assert "computed earlier (2026-11-20)" in body["limitations"][-2]


def test_b08_gemini_down_serves_the_cached_result_with_its_label(client: TestClient, conn: Conn, gemini: FakeGemini, monkeypatch: pytest.MonkeyPatch) -> None:
    key, entry = cache_entry(SECURITY["description"])
    monkeypatch.setattr(ams, "_cache", {key: entry})
    verification_id = valid_verification(client)
    gemini.status = 429  # embeddings fail
    body = match(client, verification_id).json()
    assert body["modelVersion"].endswith("· cached 2026-11-20")
    assert body["missingRequirements"] == entry["missingRequirements"]
    assert body["limitations"][-1] == "This is a recommendation, not a decision. The hiring decision stays with you."
    assert gemini.judge_calls == []
    stored = conn.execute("SELECT model_version FROM matchings").fetchone()
    assert stored == {"model_version": body["modelVersion"]}

    # Another position has no cached result, so it still gets 503.
    assert_error(match(client, verification_id, FRONTEND), 503, "AI_UNAVAILABLE")


def test_b08_tc10_switched_off_ai_ignores_the_cache(client: TestClient, gemini: FakeGemini, monkeypatch: pytest.MonkeyPatch) -> None:
    key, entry = cache_entry(SECURITY["description"])
    monkeypatch.setattr(ams, "_cache", {key: entry})
    verification_id = valid_verification(client)
    monkeypatch.setattr(config, "GEMINI_API_KEY", "")
    assert_error(match(client, verification_id), 503, "AI_UNAVAILABLE")
    assert gemini.calls == [] and gemini.judge_calls == []


def test_b08_no_shared_skills_calls_no_model(client: TestClient, gemini: FakeGemini) -> None:
    verification_id = valid_verification(client, ["program.title"])
    body = match(client, verification_id).json()
    assert body["matchedSkills"] == [] and body["limitations"] == ams.LIMITATIONS_NO_SKILLS
    assert gemini.calls == [] and gemini.judge_calls == []


# --- Committed cache ---------------------------------------------------------------------


def test_b08_committed_cache_is_consistent_and_holds_no_identity() -> None:
    document = json.loads(ams.CACHE_FILE.read_text(encoding="utf-8"))
    entries = document["entries"]
    assert entries, "run scripts/build_matching_cache.py"
    descriptions = {d.strip() for _, d in seed.POSITIONS}
    catalog = list(CATALOG.values())
    for key, entry in entries.items():
        assert set(entry) == {"skills", "description", "matchedSkills", "missingRequirements", "modelVersion", "computedAt"}
        assert key == ams.cache_key(entry["skills"], entry["description"])
        assert entry["description"] in descriptions and all(s in catalog for s in entry["skills"])
        assert f"+ {ams.JUDGE_MODEL} judge" in entry["modelVersion"], "rebuild the cache after changing the judge"
        requirements = ams.split_requirements(entry["description"])
        covered = [m["requirement"] for m in entry["matchedSkills"]] + [m["requirement"] for m in entry["missingRequirements"]]
        assert sorted(covered) == sorted(requirements)
        labels = {s["label"] for s in entry["skills"]}
        assert all(ams.MatchedSkill.model_validate(m).skill in labels for m in entry["matchedSkills"])
        assert all(ams.MissingRequirement.model_validate(m) for m in entry["missingRequirements"])
    assert "HLD-" not in json.dumps(document) and "CRD-" not in json.dumps(document)


# --- Gold set and scoring (scripts/eval_matching.py) ------------------------------------


def test_b08_gold_set_is_well_formed_and_split_without_leaks() -> None:
    gold = json.loads(eval_matching.GOLD.read_text(encoding="utf-8"))
    items, profiles = gold["items"], gold["profiles"]
    assert len({i["id"] for i in items}) == len(items)
    assert all(set(ids) <= set(CATALOG) for ids in profiles.values())
    assert all(i["split"] in {"dev", "test"} and set(i["expected"]) <= set(profiles[i["profile"]]) for i in items)
    assert len({(i["profile"], i["requirement"]) for i in items}) == len(items)
    split_of: dict[str, set[str]] = {}
    for i in items:
        split_of.setdefault(i["requirement"], set()).add(i["split"])
    assert all(len(s) == 1 for s in split_of.values()), "a requirement text is in both splits"
    seed_texts = {r for _, d in seed.POSITIONS for r in ams.split_requirements(d)}
    assert all(i["split"] == "dev" for i in items if i["requirement"] in seed_texts), "B-04 tuned on the seed positions"
    test = [i for i in items if i["split"] == "test"]
    assert Counter(bool(i["expected"]) for i in test)[True] >= 15 and Counter(i["tag"] for i in test)["negation"] >= 5


def test_b08_scoring_counts_a_wrong_skill_as_a_false_match_and_a_miss() -> None:
    assert [eval_matching.outcome(e, p) for e, p in [(["A"], "A"), (["A", "B"], "B"), (["A"], "C"), (["A"], None), ([], None), ([], "A")]] == [
        "TP", "TP", "WRONG", "FN", "TN", "FP"
    ]
    m = eval_matching.metrics(["TP", "TP", "WRONG", "FN", "TN", "FP"])
    assert (m["tp"], m["tn"], m["wrong"]) == (2, 1, 1)
    assert m["precision"] == round(2 / 4, 4) and m["recall"] == round(2 / 4, 4) and m["f1"] == 0.5
    assert m["accuracy"] == round(3 / 6, 4)
    assert eval_matching.metrics(["TN"])["f1"] == 0.0
