"""AMS AI Matching service: API-07 matchSkills (T18–T22, FR-08, FR-09, NFR-03, NFR-06).

Since B-04 the embeddings come from the Gemini API (free tier) instead of a local model process
(OD-8 as revised for deployment). This module splits the position into requirements, embeds them
with the verified skills, and groups requirements into matched and missing (OD-7). It sends only
skill texts and requirement texts, never holder identity (design rule 3), and returns no total score.
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
# OD-7 started at 0.60; A-10 tuned it to 0.55 for MiniLM. Re-tuned for Gemini in B-04 on the three
# seed positions: every requirement scored 0.746 or more against a skill of its own domain, and at
# most 0.703 against skills of other domains, so 0.72 separates them.
THRESHOLD = 0.72
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
    requirements: list[str],
    skills: list[dict[str, object]],
    requirement_vectors: dict[str, np.ndarray],
    skill_vectors: dict[str, np.ndarray],
) -> tuple[list[MatchedSkill], list[MissingRequirement]]:
    """Each requirement goes to its most similar verified skill (label or alias) if that clears
    THRESHOLD; otherwise it is missing. Similarity stays per pair and is never summed."""

    def unit(vector: np.ndarray) -> np.ndarray:
        return vector / (np.linalg.norm(vector) or 1.0)

    matched: list[MatchedSkill] = []
    missing: list[MissingRequirement] = []
    for requirement in requirements:
        best: tuple[float, str, str] | None = None
        for skill in skills:
            label = str(skill["label"])
            for text in [label, *skill["aliases"]]:  # type: ignore[misc]
                score = float(unit(requirement_vectors[requirement]) @ unit(skill_vectors[text]))
                if best is None or score > best[0]:
                    best = (score, label, text)
        if best is not None and best[0] >= THRESHOLD:
            score, label, via = best
            matched.append(MatchedSkill(skill=label, requirement=requirement, similarity=round(score, 2), reason=_reason(score, via, label)))
        else:
            note = "No verified skill is close enough." if skills else "The holder did not share skills in this link."
            missing.append(MissingRequirement(requirement=requirement, note=note))
    return matched, missing


GEMINI_MODEL = "gemini-embedding-001"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:batchEmbedContents"
# Requirements are embedded as queries and skills as documents: on the seed positions this asymmetric
# pair separated right from wrong skills, and SEMANTIC_SIMILARITY did not (B-04).
MODEL_VERSION = f"{GEMINI_MODEL} (Gemini API, RETRIEVAL_QUERY/RETRIEVAL_DOCUMENT)"
_BATCH = 100  # most texts batchEmbedContents takes in one call
# Catalog skill texts only, so position text is never kept. Empties when the process restarts.
_skill_vectors: dict[str, np.ndarray] = {}


def _unavailable() -> ApiError:
    return ApiError(503, "AI_UNAVAILABLE", "The AI service is unavailable. Verification still works.")


def _gemini(texts: list[str], task: str) -> list[np.ndarray]:
    vectors: list[np.ndarray] = []
    for start in range(0, len(texts), _BATCH):
        chunk = texts[start : start + _BATCH]
        requests = [{"model": f"models/{GEMINI_MODEL}", "content": {"parts": [{"text": t}]}, "taskType": task} for t in chunk]
        try:
            response = httpx.post(
                GEMINI_URL, json={"requests": requests}, headers={"x-goog-api-key": config.GEMINI_API_KEY}, timeout=30
            )
            response.raise_for_status()
            embeddings = response.json()["embeddings"]
            if len(embeddings) != len(chunk):
                raise ValueError("Gemini returned a different number of embeddings")
            vectors += [np.array(e["values"]) for e in embeddings]
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:  # network, quota, bad key, odd body
            raise _unavailable() from exc
    return vectors


def embed(
    requirements: list[str], skill_texts: list[str]
) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray], str]:
    """Embeds the requirements and the verified skills' labels and aliases with Gemini; skill vectors
    are cached. 503 AI_UNAVAILABLE when GEMINI_API_KEY is unset or Gemini fails (TC-10)."""
    if not config.GEMINI_API_KEY:
        raise _unavailable()
    unique = list(dict.fromkeys(requirements))
    new = [t for t in dict.fromkeys(skill_texts) if t not in _skill_vectors]
    requirement_vectors = dict(zip(unique, _gemini(unique, "RETRIEVAL_QUERY"), strict=True))
    _skill_vectors.update(zip(new, _gemini(new, "RETRIEVAL_DOCUMENT"), strict=True))
    return requirement_vectors, {t: _skill_vectors[t] for t in skill_texts}, MODEL_VERSION


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
    skill_texts = [str(t) for s in skills for t in [s["label"], *s["aliases"]]]
    requirement_vectors, skill_vectors, model_version = embed(requirements, skill_texts)  # T21
    matched, missing = group(requirements, skills, requirement_vectors, skill_vectors)

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
