"""AMS AI Matching service: API-07 matchSkills (T18–T22, FR-08, FR-09, NFR-03, NFR-06).

Since B-04 the embeddings come from the Gemini API (free tier) instead of a local model process
(OD-8 as revised for deployment). Since B-08 a Gemini language model judges each requirement against
the verified skills, because embedding similarity alone cannot read a negation or tell a related
technology from the one asked for; the choice of judge was made on the locked gold set in
api/evals/ (docs/evidence/matching-eval/). This module splits the position into requirements
(OD-7), embeds them with the verified skills, lets the judge decide each match and write its
reason, and keeps the embedding similarity of each pair for reference. It sends only skill texts
and requirement texts, never holder identity (design rule 3), and returns no total score.

When the judge does not answer, a backup judge model is asked; when Gemini still does not answer, the
result degrades in steps, and each step is labeled in `modelVersion` and the limitations: a result
computed earlier for the same skills and position text (matching_cache.json), then embedding
similarity alone, then 503 AI_UNAVAILABLE. With GEMINI_API_KEY unset the AI is switched off and
API-07 always returns 503 (TC-10).
"""

import hashlib
import json
import logging
import re
from pathlib import Path
from typing import Annotated, Any, Literal, NamedTuple

import httpx
import numpy as np
from fastapi import APIRouter, Depends
from psycopg.types.json import Jsonb

from app import aas, config, vrs
from app.errors import ApiError
from app.ias import Conn, Principal, require_roles
from app.models import ApiModel

router = APIRouter()
logger = logging.getLogger(__name__)

LABEL = "REKOMENDASI"
# Embedding-only threshold, used when the judge does not answer. OD-7 started at 0.60; A-10 tuned it
# to 0.55 for MiniLM; B-04 re-tuned it to 0.72 for Gemini on the three seed positions; B-08 set it to
# the best F1 on the gold set's dev split (docs/evidence/matching-eval/).
THRESHOLD = 0.71
MAX_TITLE, MAX_DESCRIPTION = 200, 2000  # OD-4
_SPLIT = re.compile(r"[.;,!?\n]+|\s+(?:dan|and)\s+", re.IGNORECASE)
NO_SKILLS = "The holder did not share skills in this link."
NOT_CLOSE = "No verified skill is close enough."


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


# --- Embedding similarity (B-04) ---------------------------------------------------------


def pair_scores(
    requirements: list[str],
    skills: list[dict[str, Any]],
    requirement_vectors: dict[str, np.ndarray],
    skill_vectors: dict[str, np.ndarray],
) -> list[list[tuple[float, str]]]:
    """scores[i][j] is the best cosine similarity between requirement i and skill j's label or one
    of its aliases, with the text that gave it."""

    def unit(vector: np.ndarray) -> np.ndarray:
        return vector / (np.linalg.norm(vector) or 1.0)

    scores = []
    for requirement in requirements:
        r = unit(requirement_vectors[requirement])
        row = []
        for skill in skills:
            best: tuple[float, str] | None = None
            for text in [str(skill["label"]), *skill["aliases"]]:
                score = float(r @ unit(skill_vectors[text]))
                if best is None or score > best[0]:
                    best = (score, text)
            assert best is not None
            row.append(best)
        scores.append(row)
    return scores


def _reason(similarity: float, via: str, label: str) -> str:
    strength = "Very close" if similarity >= 0.85 else "Close" if similarity >= 0.70 else "Related"
    source = "the skill name" if via == label else f'the alias "{via}"'
    return f"{strength} in meaning to {source}."


def group(
    requirements: list[str],
    skills: list[dict[str, Any]],
    requirement_vectors: dict[str, np.ndarray],
    skill_vectors: dict[str, np.ndarray],
) -> tuple[list[MatchedSkill], list[MissingRequirement]]:
    """Embedding only: each requirement goes to its most similar verified skill (label or alias) if
    that clears THRESHOLD; otherwise it is missing. Similarity stays per pair and is never summed."""
    scores = pair_scores(requirements, skills, requirement_vectors, skill_vectors)
    matched: list[MatchedSkill] = []
    missing: list[MissingRequirement] = []
    for requirement, row in zip(requirements, scores, strict=True):
        j = max(range(len(row)), key=lambda k: row[k][0], default=None)
        if j is not None and row[j][0] >= THRESHOLD:
            score, via = row[j]
            label = str(skills[j]["label"])
            matched.append(MatchedSkill(skill=label, requirement=requirement, similarity=round(score, 2), reason=_reason(score, via, label)))
        else:
            missing.append(MissingRequirement(requirement=requirement, note=NOT_CLOSE if skills else NO_SKILLS))
    return matched, missing


GEMINI_API = "https://generativelanguage.googleapis.com/v1beta/models"
GEMINI_MODEL = "gemini-embedding-001"
GEMINI_URL = f"{GEMINI_API}/{GEMINI_MODEL}:batchEmbedContents"
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


# --- LLM judge (B-08) --------------------------------------------------------------------

# Chosen on the gold set's dev split (docs/evidence/matching-eval/README.md).
JUDGE_MODEL = "gemini-3.1-flash-lite"
# Second on the dev split, asked only when JUDGE_MODEL does not answer: on 2026-11-20 the free tier's
# 3.1 model answered 503 or hung on about half the calls, while this one answered every call. Its
# misses on the gold set were all "not covered", never a false match.
JUDGE_BACKUP = "gemini-3.5-flash-lite"
# Seconds per call: the chosen model's answers took 1.6-5.8 s, the backup's 1.6-9.3 s.
_JUDGE_TIMEOUTS = {JUDGE_MODEL: 8.0, JUDGE_BACKUP: 15.0}
# Skills below this embedding similarity are not offered to the judge, and a requirement with no
# skill above it is not covered without asking; None would offer every verified skill.
CANDIDATE_FLOOR: float | None = 0.60
_MAX_REASON = 240
JUDGE_PROMPT = """You check a job position's requirements against the verified skills of a training credential.
For each requirement, decide whether one of its candidate skills covers it, and name that skill.

Rules:
- A skill covers a requirement only when the skill, by its name or one of its aliases, clearly gives the ability the requirement asks for. Paraphrases and other languages (Indonesian or English) count.
- A related but different technology, tool, language, or field does not cover it. For example, a skill in C# does not cover a requirement for Go, and a skill in network administration does not cover database administration.
- A requirement that says an ability is not needed, optional, or not a condition is not covered by any skill.
- Duties and soft skills that no skill names are not covered.
- Choose only from the requirement's candidates. Pick the single best one. When unsure, answer NONE.
- Write the reason first: one short English sentence, at most 25 words, naming the skill or saying what is missing. Never mention a person.

The input is JSON. Answer only with the JSON the schema asks for, with one verdict per requirement."""


class Verdict(NamedTuple):
    skill: int | None  # index into the skills list, None when not covered
    reason: str


class JudgeFailed(Exception):
    """The judge did not answer, or its answer broke the schema; the caller degrades."""


def judge(
    requirements: list[str],
    skills: list[dict[str, Any]],
    candidates: list[list[int]],
    model: str = JUDGE_MODEL,
    timeout: float = 30.0,
) -> list[Verdict]:
    """One Gemini call that judges every requirement against its candidate skills (indices into
    `skills`). Sends only skill labels, aliases, and requirement text."""
    verdicts: list[Verdict | None] = [None] * len(requirements)
    asked = [i for i, c in enumerate(candidates) if c]
    for i, c in enumerate(candidates):
        if not c:
            verdicts[i] = Verdict(None, NOT_CLOSE)
    if asked:
        skill_ids = [f"S{j + 1}" for j in range(len(skills))]
        requirement_ids = {f"R{i + 1}": i for i in asked}
        payload = {
            "skills": [{"id": skill_ids[j], "name": str(s["label"]), "aliases": list(s["aliases"])} for j, s in enumerate(skills)],
            "requirements": [
                {"id": f"R{i + 1}", "text": requirements[i], "candidates": [skill_ids[j] for j in candidates[i]]} for i in asked
            ],
        }
        verdict_schema = {
            "type": "OBJECT",
            "properties": {
                "requirement": {"type": "STRING", "enum": list(requirement_ids)},
                "reason": {"type": "STRING"},
                "skill": {"type": "STRING", "enum": [*skill_ids, "NONE"]},
            },
            "required": ["requirement", "reason", "skill"],
            "propertyOrdering": ["requirement", "reason", "skill"],
        }
        body = {
            "systemInstruction": {"parts": [{"text": JUDGE_PROMPT}]},
            "contents": [{"role": "user", "parts": [{"text": json.dumps(payload, ensure_ascii=False)}]}],
            "generationConfig": {
                "temperature": 0,
                "responseMimeType": "application/json",
                "responseSchema": {
                    "type": "OBJECT",
                    "properties": {"verdicts": {"type": "ARRAY", "items": verdict_schema}},
                    "required": ["verdicts"],
                },
            },
        }
        try:
            response = httpx.post(
                f"{GEMINI_API}/{model}:generateContent",
                json=body,
                headers={"x-goog-api-key": config.GEMINI_API_KEY},
                timeout=timeout,
            )
            response.raise_for_status()
            parts = response.json()["candidates"][0]["content"]["parts"]
            answer = json.loads("".join(p.get("text", "") for p in parts))
            for item in answer["verdicts"]:
                i = requirement_ids[item["requirement"]]
                pick, reason = item["skill"], " ".join(str(item["reason"]).split())
                if verdicts[i] is not None or not reason:
                    raise ValueError("duplicate verdict or empty reason")
                if pick == "NONE":
                    verdicts[i] = Verdict(None, reason[:_MAX_REASON])
                else:
                    j = skill_ids.index(pick)
                    if j not in candidates[i]:
                        raise ValueError("the judge picked a skill that was not a candidate")
                    verdicts[i] = Verdict(j, reason[:_MAX_REASON])
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError, AttributeError) as exc:
            raise JudgeFailed(type(exc).__name__) from exc
    if any(v is None for v in verdicts):
        raise JudgeFailed("a requirement got no verdict")
    return [v for v in verdicts if v is not None]


def candidates_for(scores: list[list[tuple[float, str]]], floor: float | None = None) -> list[list[int]]:
    return [[j for j, (score, _) in enumerate(row) if floor is None or score >= floor] for row in scores]


# --- Recommendation, with labeled fallbacks ----------------------------------------------


_BASE = [
    "Text similarity is not proof of ability.",
    "Only the skills the issuer recorded and the holder shared are compared.",
]
def _judged(model: str) -> str:
    return (
        f"An AI language model ({model}) decided each match from the skill and requirement text and wrote"
        " the reason; the similarity is the embedding similarity of that pair, for reference only."
    )


_DECISION = "This is a recommendation, not a decision. The hiring decision stays with you."


def limitations_judged(model: str) -> list[str]:
    return [*_BASE, _judged(model), _DECISION]


LIMITATIONS = limitations_judged(JUDGE_MODEL)
LIMITATIONS_EMBEDDING_ONLY = [
    *_BASE,
    f"The AI judge did not answer, so requirements were matched by embedding similarity alone: {THRESHOLD:.2f}"
    " or higher counts as matched, and the value is indicative only.",
    _DECISION,
]
LIMITATIONS_NO_SKILLS = [*_BASE, _DECISION]


class Recommendation(NamedTuple):
    matched: list[MatchedSkill]
    missing: list[MissingRequirement]
    limitations: list[str]
    model_version: str


def judged(
    requirements: list[str], skills: list[dict[str, Any]], scores: list[list[tuple[float, str]]], embedding_version: str
) -> Recommendation:
    """Lets the judge decide each requirement, asking JUDGE_BACKUP when JUDGE_MODEL does not answer;
    raises JudgeFailed when neither does."""
    candidates = candidates_for(scores, CANDIDATE_FLOOR)
    for model in (JUDGE_MODEL, JUDGE_BACKUP):
        try:
            verdicts = judge(requirements, skills, candidates, model=model, timeout=_JUDGE_TIMEOUTS[model])
            break
        except JudgeFailed as exc:
            logger.warning("AMS judge %s did not answer (%s)", model, exc)
    else:
        raise JudgeFailed("no judge answered")
    matched: list[MatchedSkill] = []
    missing: list[MissingRequirement] = []
    for requirement, row, verdict in zip(requirements, scores, verdicts, strict=True):
        if verdict.skill is None:
            missing.append(MissingRequirement(requirement=requirement, note=verdict.reason))
        else:
            label = str(skills[verdict.skill]["label"])
            matched.append(MatchedSkill(skill=label, requirement=requirement, similarity=round(row[verdict.skill][0], 2), reason=verdict.reason))
    return Recommendation(matched, missing, limitations_judged(model), f"{embedding_version} + {model} judge")


CACHE_FILE = Path(__file__).with_name("matching_cache.json")
_cache: dict[str, dict[str, Any]] | None = None


def cache_key(skills: list[dict[str, Any]], description: str) -> str:
    """Same skills (label and aliases) and same position description, whatever the credential."""
    canonical = {"description": description, "skills": sorted([str(s["label"]), list(s["aliases"])] for s in skills)}
    return hashlib.sha256(json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _cache_entries() -> dict[str, dict[str, Any]]:
    global _cache
    if _cache is None:
        _cache = json.loads(CACHE_FILE.read_text(encoding="utf-8"))["entries"] if CACHE_FILE.exists() else {}
    return _cache


def cached(skills: list[dict[str, Any]], description: str) -> Recommendation | None:
    """A judged result computed earlier for the same input, labeled as such (scripts/build_matching_cache.py)."""
    entry = _cache_entries().get(cache_key(skills, description))
    if entry is None:
        return None
    day = str(entry["computedAt"])[:10]
    found = re.search(r"\+ (\S+) judge", str(entry["modelVersion"]))
    judge_model = found.group(1) if found else JUDGE_MODEL
    return Recommendation(
        [MatchedSkill.model_validate(m) for m in entry["matchedSkills"]],
        [MissingRequirement.model_validate(m) for m in entry["missingRequirements"]],
        [
            *_BASE,
            _judged(judge_model),
            f"Gemini did not answer, so this result was computed earlier ({day}) for the same skills and position text.",
            _DECISION,
        ],
        f"{entry['modelVersion']} · cached {day}",
    )


def recommend(requirements: list[str], skills: list[dict[str, Any]], description: str) -> Recommendation:
    """T21: judged result, else cached, else embedding only, else 503 AI_UNAVAILABLE."""
    if not config.GEMINI_API_KEY:  # the AI is switched off on purpose (TC-10); no cache either
        raise _unavailable()
    if not skills:
        missing = [MissingRequirement(requirement=r, note=NO_SKILLS) for r in requirements]
        return Recommendation([], missing, LIMITATIONS_NO_SKILLS, "none: the link shares no skills")
    skill_texts = [str(t) for s in skills for t in [s["label"], *s["aliases"]]]
    try:
        requirement_vectors, skill_vectors, embedding_version = embed(requirements, skill_texts)
    except ApiError:
        if (hit := cached(skills, description)) is not None:
            return hit
        raise
    scores = pair_scores(requirements, skills, requirement_vectors, skill_vectors)
    try:
        return judged(requirements, skills, scores, embedding_version)
    except JudgeFailed as exc:
        logger.warning("AMS judge unavailable (%s); degrading", exc)
        if (hit := cached(skills, description)) is not None:
            return hit
        matched, missing = group(requirements, skills, requirement_vectors, skill_vectors)
        return Recommendation(matched, missing, LIMITATIONS_EMBEDDING_ONLY, f"{embedding_version}; judge unavailable, embedding only")


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
    rec = recommend(requirements, skills, description)  # T21

    result = {
        "matchedSkills": [m.model_dump(by_alias=True) for m in rec.matched],
        "missingRequirements": [m.model_dump(by_alias=True) for m in rec.missing],
        "limitations": rec.limitations,
    }
    row = conn.execute(
        "INSERT INTO matchings (verification_id, position_title, result, model_version)"
        " VALUES (%s, %s, %s, %s) RETURNING matching_id",
        (body.verification_id, title, Jsonb(result), rec.model_version),
    ).fetchone()
    assert row is not None
    aas.record_audit(conn, principal.role, "matchSkills", row["matching_id"], "success")
    conn.commit()
    return MatchingResult(
        matching_id=row["matching_id"],
        label=LABEL,
        matched_skills=rec.matched,
        missing_requirements=rec.missing,
        limitations=rec.limitations,
        model_version=rec.model_version,
    )
