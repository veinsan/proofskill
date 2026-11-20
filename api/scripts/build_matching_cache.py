"""B-08: builds api/app/matching_cache.json, the judged results that API-07 serves, labeled as cached,
when Gemini does not answer. It covers the synthetic sample positions (seed.POSITIONS, also the web
form's samples) against the skill sets of the demo credentials. Only skill and requirement text is
sent to Gemini, as in API-07, and only judged results are stored.

Run from api/ after changing the judge, the prompt, the catalog, or the sample positions:
    uv run --env-file ../.env python -m scripts.build_matching_cache [--skills SK-014,SK-021,SK-033 --skills SK-041]
"""

import argparse
import json
import time
from datetime import UTC, datetime

from app import ams, config, seed

DEFAULT_SETS = ["SK-014,SK-021,SK-033", "SK-041"]  # the deployed demo credentials' skills


def build(skill_sets: list[list[str]]) -> dict[str, dict[str, object]]:
    catalog = {skill_id: {"label": label, "aliases": aliases} for skill_id, label, aliases in seed.SKILLS}
    entries: dict[str, dict[str, object]] = {}
    for skill_ids in skill_sets:
        skills = [catalog[s] for s in sorted(skill_ids)]  # API-07 reads them ordered by skill_id
        for _, description in seed.POSITIONS:
            description = description.strip()
            requirements = ams.split_requirements(description)
            skill_texts = [t for s in skills for t in [s["label"], *s["aliases"]]]
            rv, sv, version = ams.embed(requirements, skill_texts)
            scores = ams.pair_scores(requirements, skills, rv, sv)
            for attempt in range(3):
                try:
                    rec = ams.judged(requirements, skills, scores, version)
                    break
                except ams.JudgeFailed:
                    if attempt == 2:
                        raise
                    time.sleep(30)
            entries[ams.cache_key(skills, description)] = {
                "skills": skills,
                "description": description,
                "matchedSkills": [m.model_dump(by_alias=True) for m in rec.matched],
                "missingRequirements": [m.model_dump(by_alias=True) for m in rec.missing],
                "modelVersion": rec.model_version,
                "computedAt": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
            print(f"{','.join(skill_ids)} x {requirements[0]}...: {len(rec.matched)} matched")
            time.sleep(4.5)  # free-tier per-minute limit
    return dict(sorted(entries.items()))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skills", action="append", help="comma-separated skill IDs of one credential; repeatable")
    args = parser.parse_args()
    if not config.GEMINI_API_KEY:
        raise SystemExit("GEMINI_API_KEY is not set (pass --env-file ../.env)")
    entries = build([s.split(",") for s in (args.skills or DEFAULT_SETS)])
    document = {
        "description": "Judged API-07 results for the synthetic sample positions, served only when Gemini does not answer"
        " and always labeled as cached. Built by api/scripts/build_matching_cache.py; keys are ams.cache_key(skills, description).",
        "entries": entries,
    }
    ams.CACHE_FILE.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(entries)} entries to {ams.CACHE_FILE}")


if __name__ == "__main__":
    main()
