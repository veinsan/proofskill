"""A-10 completion criteria: F-06 skill matching through API-07 (TC-08, TC-09, TC-10, TC-15;
FR-08, FR-09, NFR-03, NFR-06, design rule 1.3). The logic tests use a word-overlap fake embedder;
TC-08 and TC-10 run the real model process."""

import zlib

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app import ams, config, db, seed
from tests.conftest import ams_process, issue, login, share
from tests.test_a04_auth_rbac import assert_error
from tests.test_a08_verification import verify

Conn = db.psycopg.Connection[db.DictRow]
SECURITY = {"title": seed.POSITIONS[0][0], "description": seed.POSITIONS[0][1]}  # report API-07 example
FRONTEND = {"title": seed.POSITIONS[2][0], "description": seed.POSITIONS[2][1]}


def fake_embed(texts: list[str]) -> tuple[dict[str, np.ndarray], str]:
    def vector(text: str) -> np.ndarray:
        v = np.zeros(256)
        for word in text.lower().split():
            v[zlib.crc32(word.encode()) % 256] += 1
        return v

    return {t: vector(t) for t in texts}, "fake-word-overlap"


@pytest.fixture
def fake_ai(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ams, "embed", fake_embed)


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
    matched, missing = ams.group(["a", "b"], [{"label": "Skill A", "aliases": ["alias b"]}], vectors)
    assert [(m.requirement, m.skill, m.similarity) for m in matched] == [("a", "Skill A", 0.99), ("b", "Skill A", 0.96)]
    assert 'alias "alias b"' in matched[1].reason
    matched, missing = ams.group(["a"], [], vectors)
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
    stored = conn.execute("SELECT verification_id, position_title, model_version FROM matchings").fetchone()
    assert stored == {"verification_id": verification_id, "position_title": SECURITY["title"], "model_version": "fake-word-overlap"}
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


# --- Real model process ------------------------------------------------------------------


def test_tc08_matching_after_a_valid_verification_with_the_real_model(
    client: TestClient, ams_url: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(config, "AMS_URL", ams_url)
    verification_id = valid_verification(client)
    body = match(client, verification_id).json()
    pairs = {(m["requirement"], m["skill"]) for m in body["matchedSkills"]}
    assert pairs == {
        ("Menganalisis kerentanan aplikasi web", "OWASP Top 10"),
        ("memahami OWASP Top 10", "OWASP Top 10"),
        ("melakukan pengujian keamanan dasar", "Web Security Testing"),
    }
    assert [m["requirement"] for m in body["missingRequirements"]] == ["memantau log dengan SIEM"]
    assert all(ams.THRESHOLD <= m["similarity"] <= 1 for m in body["matchedSkills"])
    assert body["label"] == "REKOMENDASI" and "score" not in str(body).lower()
    assert body["modelVersion"].startswith("paraphrase-multilingual-MiniLM-L12-v2@")

    # AI differentiator: the same security credential against a frontend position covers nothing.
    unrelated = match(client, verification_id, FRONTEND).json()
    assert unrelated["matchedSkills"] == []
    assert len(unrelated["missingRequirements"]) == len(ams.split_requirements(FRONTEND["description"]))


def test_tc10_ai_switched_off_returns_503_and_verification_keeps_working(
    client: TestClient, conn: Conn, monkeypatch: pytest.MonkeyPatch
) -> None:
    issue(client)
    token = share(client, "CRD-0001")["shareToken"]
    with ams_process(8012) as url:
        monkeypatch.setattr(config, "AMS_URL", url)
        first = verify(client, token).json()
        assert match(client, first["verificationId"]).status_code == 200
    # The AMS process is now stopped (OD-8).
    assert_error(match(client, first["verificationId"]), 503, "AI_UNAVAILABLE")
    again = verify(client, token)
    assert again.status_code == 200 and again.json()["result"] == "VALID"
    assert conn.execute("SELECT count(*) AS n FROM matchings").fetchone() == {"n": 1}
