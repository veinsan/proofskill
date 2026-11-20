"""A-10 completion criteria: F-06 skill matching through API-07 (TC-08, TC-09, TC-10, TC-15;
FR-08, FR-09, NFR-03, NFR-06, design rule 1.3). The logic tests use a word-overlap fake embedder or
a fake Gemini endpoint; TC-08 calls the real Gemini API (B-04) when GEMINI_API_KEY is set."""

import json
import zlib
from typing import Any

import httpx
import numpy as np
import pytest
from fastapi.testclient import TestClient

from app import ams, config, db, seed
from tests.conftest import ISSUE_REQUEST, issue, login, share
from tests.test_a04_auth_rbac import assert_error
from tests.test_a08_verification import verify

Conn = db.psycopg.Connection[db.DictRow]
SECURITY = {"title": seed.POSITIONS[0][0], "description": seed.POSITIONS[0][1]}  # report API-07 example
FRONTEND = {"title": seed.POSITIONS[2][0], "description": seed.POSITIONS[2][1]}


def word_vector(text: str) -> np.ndarray:
    v = np.zeros(256)
    for word in text.lower().split():
        v[zlib.crc32(word.encode()) % 256] += 1
    return v


def fake_embed(requirements: list[str], skill_texts: list[str]) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray], str]:
    return {t: word_vector(t) for t in requirements}, {t: word_vector(t) for t in skill_texts}, "fake-word-overlap"


def overlap_verdicts(requirements: list[dict[str, Any]], skills: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Fake judge: a candidate skill covers a requirement when they share a word."""
    verdicts = []
    for r in requirements:
        words = set(r["text"].lower().split())
        pick = next((s for s in skills if s["id"] in r["candidates"] and words & set(" ".join([s["name"], *s["aliases"]]).lower().split())), None)
        reason = f"Shares a word with {pick['name']}." if pick else ams.NOT_CLOSE
        verdicts.append({"requirement": r["id"], "reason": reason, "skill": pick["id"] if pick else "NONE"})
    return verdicts


def fake_judge(requirements: list[str], skills: list[dict[str, Any]], candidates: list[list[int]], model: str = ams.JUDGE_MODEL) -> list[ams.Verdict]:
    payload_skills = [{"id": f"S{j + 1}", "name": s["label"], "aliases": list(s["aliases"])} for j, s in enumerate(skills)]
    payload = [{"id": f"R{i + 1}", "text": r, "candidates": [f"S{j + 1}" for j in candidates[i]]} for i, r in enumerate(requirements)]
    return [
        ams.Verdict(None if v["skill"] == "NONE" else int(v["skill"][1:]) - 1, v["reason"])
        for v in overlap_verdicts(payload, payload_skills)
    ]


class FakeGemini:
    """Stands in for httpx.post to batchEmbedContents and the judge's generateContent, and records
    every request AMS sends."""

    def __init__(self, status: int = 200) -> None:
        self.status = status
        self.judge_status = 200
        self.judge_text: str | None = None  # a raw judge answer, to test malformed replies
        self.calls: list[dict[str, Any]] = []
        self.judge_calls: list[dict[str, Any]] = []
        self.real_post = httpx.post  # RGS shares the httpx module for JSON-RPC

    def __call__(self, url: str, **kwargs: Any) -> httpx.Response:
        json_body, headers = kwargs.get("json"), kwargs.get("headers")
        if url.startswith(ams.GEMINI_API) and url.endswith(":generateContent"):
            self.judge_calls.append({"url": url, "json": json_body, "headers": headers})
            payload = json.loads(json_body["contents"][0]["parts"][0]["text"])
            text = self.judge_text if self.judge_text is not None else json.dumps({"verdicts": overlap_verdicts(payload["requirements"], payload["skills"])})
            body = {"candidates": [{"content": {"parts": [{"text": text}]}}]} if self.judge_status == 200 else {"error": {}}
            return httpx.Response(self.judge_status, json=body, request=httpx.Request("POST", url))
        if url != ams.GEMINI_URL:
            return self.real_post(url, **kwargs)
        self.calls.append({"url": url, "json": json_body, "headers": headers})
        texts = [r["content"]["parts"][0]["text"] for r in json_body["requests"]]
        body = {"embeddings": [{"values": word_vector(t).tolist()} for t in texts]} if self.status == 200 else {"error": {}}
        return httpx.Response(self.status, json=body, request=httpx.Request("POST", url))

    def texts(self, task: str) -> list[str]:
        return [r["content"]["parts"][0]["text"] for c in self.calls for r in c["json"]["requests"] if r["taskType"] == task]


@pytest.fixture
def gemini(monkeypatch: pytest.MonkeyPatch) -> FakeGemini:
    fake = FakeGemini()
    monkeypatch.setattr(ams.httpx, "post", fake)
    monkeypatch.setattr(config, "GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(ams, "_skill_vectors", {})
    monkeypatch.setattr(ams, "_cache", {})  # no cached result unless a test adds one
    monkeypatch.setattr(ams, "CANDIDATE_FLOOR", None)  # word-overlap vectors are not on Gemini's scale
    return fake


@pytest.fixture
def fake_ai(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ams, "embed", fake_embed)
    monkeypatch.setattr(ams, "judge", fake_judge)
    monkeypatch.setattr(config, "GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(ams, "_cache", {})
    monkeypatch.setattr(ams, "CANDIDATE_FLOOR", None)


def valid_verification(client: TestClient, scope: list[str] | None = None, username: str = "verifier.a") -> str:
    issue(client)
    token = share(client, "CRD-0001", scope)["shareToken"]
    body = verify(client, token, username).json()
    assert body["result"] == "VALID"
    return str(body["verificationId"])


def match(client: TestClient, verification_id: str, position: dict[str, str] = SECURITY, username: str = "verifier.a"):  # type: ignore[no-untyped-def]
    return client.post(
        "/api/v1/matchings", json={"verificationId": verification_id, "position": position}, headers=login(client, username)
    )


# --- Pure logic -------------------------------------------------------------------------


def test_split_requirements_follows_od7_on_the_report_example() -> None:
    assert ams.split_requirements(SECURITY["description"]) == [
        "Menganalisis kerentanan aplikasi web",
        "memahami OWASP Top 10",
        "melakukan pengujian keamanan dasar",
        "memantau log dengan SIEM",
    ]
    assert ams.split_requirements("SQL and Python; Excel.\n- Git") == ["SQL", "Python", "Excel", "Git"]


def test_group_matches_by_best_pair_and_never_totals() -> None:
    vectors = {"a": np.array([1.0, 0.0]), "b": np.array([0.0, 1.0]), "Skill A": np.array([0.9, 0.1]), "alias b": np.array([0.3, 1.0])}
    matched, missing = ams.group(["a", "b"], [{"label": "Skill A", "aliases": ["alias b"]}], vectors, vectors)
    assert [(m.requirement, m.skill, m.similarity) for m in matched] == [("a", "Skill A", 0.99), ("b", "Skill A", 0.96)]
    assert 'alias "alias b"' in matched[1].reason
    matched, missing = ams.group(["a"], [], vectors, vectors)
    assert matched == [] and missing[0].note == "The holder did not share skills in this link."


# --- API-07 with the fake embedder -------------------------------------------------------


def test_api07_returns_a_labeled_recommendation_and_stores_it(client: TestClient, conn: Conn, fake_ai: None) -> None:
    verification_id = valid_verification(client)
    response = match(client, verification_id)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["matchingId"] == "MAT-0001"
    assert body["label"] == "REKOMENDASI"
    assert set(body) == {"matchingId", "label", "matchedSkills", "missingRequirements", "limitations", "modelVersion"}
    assert {m["skill"] for m in body["matchedSkills"]} <= {"OWASP Top 10", "Web Security Testing", "Secure Coding"}
    assert {"requirement": "memantau log dengan SIEM", "note": "No verified skill is close enough."} in body["missingRequirements"]
    assert "The hiring decision stays with you." in body["limitations"][-1]
    assert body["limitations"] == ams.LIMITATIONS
    stored = conn.execute("SELECT verification_id, position_title, model_version FROM matchings").fetchone()
    assert stored == {
        "verification_id": verification_id,
        "position_title": SECURITY["title"],
        "model_version": f"fake-word-overlap + {ams.JUDGE_MODEL} judge",
    }
    audit = conn.execute("SELECT object_id FROM audit_events WHERE operation = 'matchSkills'").fetchone()
    assert audit == {"object_id": "MAT-0001"}


def test_api07_does_not_read_skills_the_holder_did_not_share(client: TestClient, fake_ai: None) -> None:
    verification_id = valid_verification(client, ["program.title"])
    body = match(client, verification_id).json()
    assert body["matchedSkills"] == []
    assert all(m["note"] == "The holder did not share skills in this link." for m in body["missingRequirements"])


def test_tc09_verification_that_is_not_valid_gets_409(client: TestClient, conn: Conn, fake_ai: None) -> None:
    issue(client)
    token = share(client, "CRD-0001")["shareToken"]
    conn.execute("UPDATE credentials SET criteria = 'diubah' WHERE credential_id = 'CRD-0001'")
    conn.commit()
    tampered = verify(client, token).json()
    assert tampered["result"] == "TAMPERED"
    assert_error(match(client, tampered["verificationId"]), 409, "VERIFICATION_NOT_VALID")


def test_tc15_another_verifiers_verification_gets_403(client: TestClient, fake_ai: None) -> None:
    verification_id = valid_verification(client, username="verifier.a")
    assert_error(match(client, verification_id, username="verifier.b"), 403, "VERIFICATION_NOT_OWNED")


def test_api07_unknown_verification_gets_404(client: TestClient, fake_ai: None) -> None:
    assert_error(match(client, "VER-9999"), 404, "VERIFICATION_NOT_FOUND")


@pytest.mark.parametrize(
    "position",
    [
        {"title": "Analyst", "description": ""},
        {"title": "Analyst", "description": "   "},
        {"title": "", "description": "SQL"},
        {"title": "Analyst", "description": "x" * 2001},
        {"title": "Analyst", "description": ",,, ;"},
    ],
)
def test_api07_empty_or_oversized_position_text_gets_422(client: TestClient, fake_ai: None, position: dict[str, str]) -> None:
    verification_id = valid_verification(client)
    assert_error(match(client, verification_id, position), 422, "INVALID_POSITION_TEXT")


@pytest.mark.parametrize("username", ["holder.a", "admin.iss001"])
def test_api07_other_roles_get_403_forbidden_role(client: TestClient, fake_ai: None, username: str) -> None:
    assert_error(match(client, "VER-0001", username=username), 403, "FORBIDDEN_ROLE")


# --- Gemini adapter (B-04) ---------------------------------------------------------------


def test_b04_only_skill_and_requirement_text_leaves_the_api(client: TestClient, gemini: FakeGemini) -> None:
    verification_id = valid_verification(client)
    assert match(client, verification_id).status_code == 200
    shared = ISSUE_REQUEST["skills"]
    skill_texts = {t for skill_id, label, aliases in seed.SKILLS if skill_id in shared for t in [label, *aliases]}  # type: ignore[operator]
    requirements = set(ams.split_requirements(SECURITY["description"]))
    assert set(gemini.texts("RETRIEVAL_QUERY")) == requirements
    assert set(gemini.texts("RETRIEVAL_DOCUMENT")) == skill_texts
    assert len(gemini.judge_calls) == 1  # one judge call per matching (B-08)
    sent = json.dumps([c["json"] for c in gemini.calls + gemini.judge_calls], ensure_ascii=False)
    identity = ["Peserta Contoh A", "HLD-2026-0007", "CRD-0001", "verifier.a", SECURITY["title"], ISSUE_REQUEST["program"]["title"]]  # type: ignore[index]
    assert all(value not in sent for value in identity)
    judged = json.loads(gemini.judge_calls[0]["json"]["contents"][0]["parts"][0]["text"])
    assert {s["name"] for s in judged["skills"]} == {label for skill_id, label, _ in seed.SKILLS if skill_id in shared}  # type: ignore[operator]
    assert [r["text"] for r in judged["requirements"]] == ams.split_requirements(SECURITY["description"])
    assert all(c["headers"] == {"x-goog-api-key": "test-key"} and "key=" not in c["url"] for c in gemini.calls + gemini.judge_calls)

    # Skill vectors are cached; the next matching sends only its requirements.
    gemini.calls.clear()
    assert match(client, verification_id, FRONTEND).status_code == 200
    assert set(gemini.texts("RETRIEVAL_QUERY")) == set(ams.split_requirements(FRONTEND["description"]))
    assert gemini.texts("RETRIEVAL_DOCUMENT") == []


def test_b04_gemini_error_returns_503(client: TestClient, gemini: FakeGemini) -> None:
    verification_id = valid_verification(client)
    gemini.status = 429  # free-tier quota exhausted
    assert_error(match(client, verification_id), 503, "AI_UNAVAILABLE")


def test_tc10_ai_switched_off_returns_503_and_verification_keeps_working(
    client: TestClient, conn: Conn, gemini: FakeGemini, monkeypatch: pytest.MonkeyPatch
) -> None:
    issue(client)
    token = share(client, "CRD-0001")["shareToken"]
    first = verify(client, token).json()
    assert match(client, first["verificationId"]).status_code == 200
    monkeypatch.setattr(config, "GEMINI_API_KEY", "")  # the deployment switch-off (OD-8 revised)
    calls = len(gemini.calls)
    assert_error(match(client, first["verificationId"]), 503, "AI_UNAVAILABLE")
    assert len(gemini.calls) == calls  # nothing was sent without a key
    again = verify(client, token)
    assert again.status_code == 200 and again.json()["result"] == "VALID"
    assert conn.execute("SELECT count(*) AS n FROM matchings").fetchone() == {"n": 1}


@pytest.mark.skipif(not config.GEMINI_API_KEY, reason="needs GEMINI_API_KEY (real Gemini call)")
def test_tc08_matching_after_a_valid_verification_with_gemini(client: TestClient) -> None:
    verification_id = valid_verification(client)
    body = match(client, verification_id).json()
    pairs = {m["requirement"]: m["skill"] for m in body["matchedSkills"]}
    # The gold set (api/evals/matching_gold.json, G001-G004) accepts either skill for the first one.
    assert set(pairs) == {"Menganalisis kerentanan aplikasi web", "memahami OWASP Top 10", "melakukan pengujian keamanan dasar"}
    assert pairs["Menganalisis kerentanan aplikasi web"] in {"OWASP Top 10", "Web Security Testing"}
    assert pairs["memahami OWASP Top 10"] == "OWASP Top 10"
    assert pairs["melakukan pengujian keamanan dasar"] == "Web Security Testing"
    assert [m["requirement"] for m in body["missingRequirements"]] == ["memantau log dengan SIEM"]
    assert all(0 < m["similarity"] <= 1 and m["reason"] for m in body["matchedSkills"])
    assert body["label"] == "REKOMENDASI" and "score" not in str(body).lower()
    assert body["modelVersion"] == f"{ams.MODEL_VERSION} + {ams.JUDGE_MODEL} judge"
    assert body["limitations"] == ams.LIMITATIONS

    # AI differentiator: the same security credential against a frontend position covers nothing.
    unrelated = match(client, verification_id, FRONTEND).json()
    assert unrelated["matchedSkills"] == []
    assert len(unrelated["missingRequirements"]) == len(ams.split_requirements(FRONTEND["description"]))
