"""AMS AI Matching service: API-07 matchSkills (T18–T22, FR-08, FR-09, NFR-03, NFR-06).

The model runs in its own process (app/ams_server.py, OD-8). This module splits the position into
requirements, asks that process for embeddings, and groups requirements into matched and missing
(OD-7). It sends only skill texts and requirement texts, never holder identity, and returns no
total score.
"""

import re
from typing import Annotated, Literal

import httpx
import numpy as np
from fastapi import APIRouter, Depends
from psycopg.types.json import Jsonb

from app import aas, config, vrs
from app.errors import ApiError
from app.ias import Conn, Principal, require_roles
from app.models import ApiModel

router = APIRouter()

LABEL = "REKOMENDASI"
# OD-7 started at 0.60. Tuned on the three seed positions in A-10: every requirement a credential
# covers scored 0.59 or more, and the best wrong-skill score was 0.54, so 0.55 separates them.
THRESHOLD = 0.55
MAX_TITLE, MAX_DESCRIPTION = 200, 2000  # OD-4
_SPLIT = re.compile(r"[.;,!?\n]+|\s+(?:dan|and)\s+", re.IGNORECASE)
LIMITATIONS = [
    "Text similarity is not proof of ability.",
    "Only the skills the issuer recorded and the holder shared are compared.",
    f"A requirement counts as matched at a similarity of {THRESHOLD:.2f} or higher; the value is indicative only.",
    "This is a recommendation, not a decision. The hiring decision stays with you.",
]


def split_requirements(description: str) -> list[str]:
    """OD-7: split at sentence ends, commas, semicolons, and the words "dan" or "and"."""
    parts = (part.strip(" -•\t") for part in _SPLIT.split(description))
    return list(dict.fromkeys(part for part in parts if len(part) >= 2))


class MatchedSkill(ApiModel):
    skill: str
    requirement: str
    similarity: float
    reason: str


class MissingRequirement(ApiModel):
    requirement: str
    note: str


def _reason(similarity: float, via: str, label: str) -> str:
    strength = "Very close" if similarity >= 0.85 else "Close" if similarity >= 0.70 else "Related"
    source = "the skill name" if via == label else f'the alias "{via}"'
    return f"{strength} in meaning to {source}."


def group(
    requirements: list[str], skills: list[dict[str, object]], vectors: dict[str, np.ndarray]
) -> tuple[list[MatchedSkill], list[MissingRequirement]]:
    """Each requirement goes to its most similar verified skill (label or alias) if that clears
    THRESHOLD; otherwise it is missing. Similarity stays per pair and is never summed."""

    def unit(text: str) -> np.ndarray:
        vector = vectors[text]
        return vector / (np.linalg.norm(vector) or 1.0)

    matched: list[MatchedSkill] = []
    missing: list[MissingRequirement] = []
    for requirement in requirements:
        best: tuple[float, str, str] | None = None
        for skill in skills:
            label = str(skill["label"])
            for text in [label, *skill["aliases"]]:  # type: ignore[misc]
                score = float(unit(requirement) @ unit(text))
                if best is None or score > best[0]:
                    best = (score, label, text)
        if best is not None and best[0] >= THRESHOLD:
            score, label, via = best
            matched.append(MatchedSkill(skill=label, requirement=requirement, similarity=round(score, 2), reason=_reason(score, via, label)))
        else:
            note = "No verified skill is close enough." if skills else "The holder did not share skills in this link."
            missing.append(MissingRequirement(requirement=requirement, note=note))
    return matched, missing


def embed(texts: list[str]) -> tuple[dict[str, np.ndarray], str]:
    """Calls the AMS model process. 503 AI_UNAVAILABLE when it is down (TC-10)."""
    unique = list(dict.fromkeys(texts))
    try:
        response = httpx.post(f"{config.AMS_URL}/embed", json={"texts": unique}, timeout=30)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise ApiError(503, "AI_UNAVAILABLE", "The AI service is unavailable. Verification still works.") from exc
    body = response.json()
    return dict(zip(unique, (np.array(v) for v in body["vectors"]), strict=True)), str(body["model_version"])


# --- API-07 POST /matchings -------------------------------------------------------------


class Position(ApiModel):
    title: str
    description: str


class MatchingRequest(ApiModel):
    verification_id: str
    position: Position


class MatchingResult(ApiModel):
    matching_id: str
    label: Literal["REKOMENDASI"]
    matched_skills: list[MatchedSkill]
    missing_requirements: list[MissingRequirement]
    limitations: list[str]
    model_version: str


@router.post("/matchings", response_model=MatchingResult, tags=["AMS"])
def match_skills(
    body: MatchingRequest,
    principal: Annotated[Principal, Depends(require_roles("verifier"))],
    conn: Conn,
) -> MatchingResult:
    """API-07: a labeled recommendation for a VALID verification the caller ran (design rule 1.3)."""
    verification = vrs.get_verification(conn, body.verification_id)  # T19, 404
    if verification["verifier"] != principal.username:
        raise ApiError(403, "VERIFICATION_NOT_OWNED", "This verification was run by another verifier.")
    if verification["result"] != "VALID":
        raise ApiError(409, "VERIFICATION_NOT_VALID", f"Skill fit needs a VALID verification, not {verification['result']}.")

    title, description = body.position.title.strip(), body.position.description.strip()
    requirements = split_requirements(description)
    if not 1 <= len(title) <= MAX_TITLE or not 1 <= len(description) <= MAX_DESCRIPTION or not requirements:
        raise ApiError(
            422, "INVALID_POSITION_TEXT",
            f"Give a position title (1-{MAX_TITLE} characters) and a description (1-{MAX_DESCRIPTION} characters).",
        )

    skills = [dict(row) for row in vrs.verified_skills(conn, verification)]  # T20
    texts = requirements + [str(t) for s in skills for t in [s["label"], *s["aliases"]]]
    vectors, model_version = embed(texts)  # T21
    matched, missing = group(requirements, skills, vectors)

    result = {
        "matchedSkills": [m.model_dump(by_alias=True) for m in matched],
        "missingRequirements": [m.model_dump(by_alias=True) for m in missing],
        "limitations": LIMITATIONS,
    }
    row = conn.execute(
        "INSERT INTO matchings (verification_id, position_title, result, model_version)"
        " VALUES (%s, %s, %s, %s) RETURNING matching_id",
        (body.verification_id, title, Jsonb(result), model_version),
    ).fetchone()
    assert row is not None
    aas.record_audit(conn, principal.role, "matchSkills", row["matching_id"], "success")
    conn.commit()
    return MatchingResult(
        matching_id=row["matching_id"],
        label=LABEL,
        matched_skills=matched,
        missing_requirements=missing,
        limitations=LIMITATIONS,
        model_version=model_version,
    )
