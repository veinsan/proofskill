"""B-08: evaluates API-07 skill matching on the locked gold set api/evals/matching_gold.json and writes
docs/evidence/matching-eval/ (README.md and results.json).

It runs the product's own functions (ams.pair_scores, ams.judge) and compares:
- embedding only at the shipped THRESHOLD, and at the threshold with the best F1 on the dev split;
- the LLM judge, for every model in --models and every candidate floor in --floors.
Every choice is made on the dev split. The test split is only reported, never tuned on.

Needs GEMINI_API_KEY. Gemini answers are cached in api/evals/.cache/ (untracked), so a re-run with
the same inputs sends nothing. Run from api/:
    uv run --env-file ../.env python -m scripts.eval_matching
"""

import argparse
import hashlib
import json
import statistics
import subprocess
import time
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

from app import ams, config, seed
from app.errors import ApiError

API_DIR = Path(__file__).resolve().parents[1]
GOLD = API_DIR / "evals" / "matching_gold.json"
CACHE_DIR = API_DIR / "evals" / ".cache"
OUT = API_DIR.parent / "docs" / "evidence" / "matching-eval"
CHUNK = 8  # requirements per judge call, about one position's worth
EMBED_CHUNK = 80  # the free tier allows about 100 embedded texts per minute
JUDGE_GAP = 4.5  # seconds between judge calls, under the free tier's per-minute limit
B04_THRESHOLD = 0.72  # the embedding threshold B-04 shipped, kept as the baseline
THRESHOLDS = [round(t, 3) for t in np.arange(0.50, 0.9501, 0.005)]


# --- Scoring (unit-tested in tests/test_b08_matching.py) ---------------------------------


def outcome(expected: list[str], predicted: str | None) -> str:
    """TP: a right skill; WRONG: a skill that does not cover it; FN: not matched although covered;
    FP: matched although nothing covers it; TN: correctly not matched."""
    if expected:
        if predicted is None:
            return "FN"
        return "TP" if predicted in expected else "WRONG"
    return "TN" if predicted is None else "FP"


def metrics(outcomes: list[str]) -> dict[str, Any]:
    """A WRONG skill counts as both a false match and a missed requirement."""
    c = Counter(outcomes)
    tp, tn, wrong = c["TP"], c["TN"], c["WRONG"]
    fp, fn = c["FP"] + wrong, c["FN"] + wrong
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    n = len(outcomes)
    return {
        "n": n, "tp": tp, "tn": tn, "fp": c["FP"], "fn": c["FN"], "wrong": wrong,
        "precision": round(precision, 4), "recall": round(recall, 4), "f1": round(f1, 4),
        "accuracy": round((tp + tn) / n, 4) if n else 0.0,
    }


# --- Gemini, with an on-disk cache -------------------------------------------------------


def _load(name: str) -> dict[str, Any]:
    path = CACHE_DIR / name
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _save(name: str, data: dict[str, Any]) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    (CACHE_DIR / name).write_text(json.dumps(data), encoding="utf-8")


def embed_all(texts: list[str], task: str, cache: dict[str, list[float]]) -> None:
    todo = [t for t in dict.fromkeys(texts) if f"{task}|{t}" not in cache]
    for start in range(0, len(todo), EMBED_CHUNK):
        if start:
            time.sleep(65)
        chunk = todo[start : start + EMBED_CHUNK]
        for attempt in range(4):
            try:
                vectors = ams._gemini(chunk, task)
                break
            except ApiError:
                if attempt == 3:
                    raise
                print(f"  embedding quota or error, waiting 65 s (attempt {attempt + 1})")
                time.sleep(65)
        cache.update({f"{task}|{t}": v.tolist() for t, v in zip(chunk, vectors, strict=True)})
        _save("embeddings.json", cache)


class Judge:
    """Calls ams.judge with pacing and retries. Answers and their latency are cached on disk; with
    fresh=True the cache is neither read nor written (repeat runs)."""

    def __init__(self) -> None:
        self.cache: dict[str, dict[str, Any]] = _load("judge.json")
        self.last = 0.0
        self.failures: Counter[str] = Counter()

    def __call__(
        self, model: str, requirements: list[str], skills: list[dict[str, Any]], candidates: list[list[int]], fresh: bool = False
    ) -> tuple[list[ams.Verdict], float | None]:
        """Returns the verdicts and the call's latency in seconds (None when no call was needed)."""
        key = hashlib.sha256(json.dumps(
            [model, ams.JUDGE_PROMPT, requirements, [[s["label"], s["aliases"]] for s in skills], candidates], ensure_ascii=False
        ).encode()).hexdigest()
        if fresh or key not in self.cache:
            latency: float | None = None
            for attempt in range(3):
                time.sleep(max(0.0, self.last + JUDGE_GAP - time.monotonic()))
                start = time.monotonic()
                try:
                    verdicts = ams.judge(requirements, skills, candidates, model=model)
                    if any(candidates):
                        latency = time.monotonic() - start
                    break
                except ams.JudgeFailed as exc:
                    self.failures[model] += 1
                    print(f"  judge {model} failed ({exc}), attempt {attempt + 1}")
                    if attempt == 2:
                        raise
                    time.sleep(30)
                finally:
                    self.last = time.monotonic()
            if fresh:
                return verdicts, latency
            self.cache[key] = {"verdicts": [list(v) for v in verdicts], "latency": latency}
            _save("judge.json", self.cache)
        entry = self.cache[key]
        return [ams.Verdict(*v) for v in entry["verdicts"]], entry["latency"]


# --- Evaluation --------------------------------------------------------------------------


def run(models: list[str], floors: list[float | None], repeats: int) -> dict[str, Any]:
    gold = json.loads(GOLD.read_text(encoding="utf-8"))
    items, profiles = gold["items"], gold["profiles"]
    catalog = {skill_id: {"skillId": skill_id, "label": label, "aliases": aliases} for skill_id, label, aliases in seed.SKILLS}
    skills_of = {name: [catalog[s] for s in ids] for name, ids in profiles.items()}

    vectors: dict[str, list[float]] = _load("embeddings.json")
    skill_texts = [t for s in catalog.values() for t in [s["label"], *s["aliases"]]]
    embed_all([i["requirement"] for i in items], "RETRIEVAL_QUERY", vectors)
    embed_all(skill_texts, "RETRIEVAL_DOCUMENT", vectors)
    rv = {i["requirement"]: np.array(vectors[f"RETRIEVAL_QUERY|{i['requirement']}"]) for i in items}
    sv = {t: np.array(vectors[f"RETRIEVAL_DOCUMENT|{t}"]) for t in skill_texts}
    scores = {i["id"]: ams.pair_scores([i["requirement"]], skills_of[i["profile"]], rv, sv)[0] for i in items}

    def evaluate(predict: dict[str, str | None]) -> dict[str, Any]:
        rows = {i["id"]: outcome(i["expected"], predict[i["id"]]) for i in items}
        result: dict[str, Any] = {s: metrics([rows[i["id"]] for i in items if i["split"] == s]) for s in ("dev", "test")}
        tags = sorted({i["tag"] for i in items})
        result["testByTag"] = {
            t: metrics([rows[i["id"]] for i in items if i["split"] == "test" and i["tag"] == t])["accuracy"] for t in tags
            if any(i["split"] == "test" and i["tag"] == t for i in items)
        }
        result["predictions"] = {i["id"]: {"predicted": predict[i["id"]], "outcome": rows[i["id"]]} for i in items}
        return result

    def embedding_only(threshold: float) -> dict[str, str | None]:
        out: dict[str, str | None] = {}
        for i in items:
            row = scores[i["id"]]
            j = max(range(len(row)), key=lambda k: row[k][0])
            out[i["id"]] = skills_of[i["profile"]][j]["skillId"] if row[j][0] >= threshold else None
        return out

    variants: dict[str, dict[str, Any]] = {}
    sweep = [(t, evaluate(embedding_only(t))) for t in THRESHOLDS]
    tuned_t, tuned = max(sweep, key=lambda x: (x[1]["dev"]["f1"], x[1]["dev"]["precision"], x[0]))
    variants[f"embedding@{B04_THRESHOLD:.3f} (B-04 baseline)"] = {"kind": "embedding", "threshold": B04_THRESHOLD, **evaluate(embedding_only(B04_THRESHOLD))}
    variants[f"embedding@{tuned_t:.3f} (best dev F1)"] = {"kind": "embedding", "threshold": tuned_t, **tuned}

    judge = Judge()

    def judge_all(model: str, floor: float | None, fresh: bool = False) -> tuple[dict[str, str | None], dict[str, str], list[float]]:
        predict: dict[str, str | None] = {}
        why: dict[str, str] = {}
        latencies: list[float] = []
        for profile in profiles:
            group = [i for i in items if i["profile"] == profile]
            for start in range(0, len(group), CHUNK):
                chunk = group[start : start + CHUNK]
                skills = skills_of[profile]
                candidates = ams.candidates_for([scores[i["id"]] for i in chunk], floor)
                verdicts, latency = judge(model, [i["requirement"] for i in chunk], skills, candidates, fresh)
                if latency is not None:
                    latencies.append(latency)
                for i, v in zip(chunk, verdicts, strict=True):
                    predict[i["id"]] = None if v.skill is None else skills[v.skill]["skillId"]
                    why[i["id"]] = v.reason
        return predict, why, latencies

    reasons: dict[str, dict[str, str]] = {}
    for model in models:
        for floor in floors:
            name = f"judge {model}, floor {'none' if floor is None else f'{floor:.2f}'}"
            print(name)
            try:
                predict, why, latencies = judge_all(model, floor)
            except ams.JudgeFailed as exc:
                variants[name] = {"kind": "judge", "model": model, "floor": floor, "error": str(exc)}
                continue
            variants[name] = {
                "kind": "judge", "model": model, "floor": floor, "calls": len(latencies),
                "latencyMedianS": round(statistics.median(latencies), 2) if latencies else None,
                "latencyMaxS": round(max(latencies), 2) if latencies else None,
                **evaluate(predict),
            }
            reasons[name] = why

    judged = {k: v for k, v in variants.items() if v["kind"] == "judge" and "error" not in v}
    chosen = max(judged, key=lambda k: (judged[k]["dev"]["f1"], judged[k]["dev"]["precision"], -(judged[k]["latencyMedianS"] or 0))) if judged else None

    # Stability: the chosen variant again, uncached, at the same temperature 0.
    repeat_runs: list[dict[str, Any]] = []
    if chosen:
        first = judged[chosen]["predictions"]
        for n in range(repeats):
            print(f"repeat {n + 1} of {chosen}")
            try:
                predict, _, _ = judge_all(judged[chosen]["model"], judged[chosen]["floor"], fresh=True)
            except ams.JudgeFailed as exc:
                repeat_runs.append({"error": str(exc)})
                continue
            again = evaluate(predict)
            repeat_runs.append({
                "devF1": again["dev"]["f1"], "testF1": again["test"]["f1"], "testAccuracy": again["test"]["accuracy"],
                "changedItems": sorted(k for k in first if first[k]["predicted"] != predict[k]),
            })
    return {
        "generatedAt": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "commit": subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, cwd=API_DIR).stdout.strip(),
        "gold": {"version": gold["version"], "items": len(items), **{s: sum(1 for i in items if i["split"] == s) for s in ("dev", "test")}},
        "embeddingModel": ams.MODEL_VERSION,
        "product": product_setting(),
        "chosenJudge": chosen,
        "repeats": repeat_runs,
        "tunedThreshold": tuned_t,
        "judgeFailures": dict(judge.failures),
        "thresholdSweepDevF1": {f"{t:.3f}": r["dev"]["f1"] for t, r in sweep},
        "variants": variants,
        "reasons": reasons,
        "items": items,
    }


def product_setting() -> dict[str, Any]:
    return {"judgeModel": ams.JUDGE_MODEL, "judgeBackup": ams.JUDGE_BACKUP, "candidateFloor": ams.CANDIDATE_FLOOR, "threshold": ams.THRESHOLD}


def _pct(x: float) -> str:
    return f"{100 * x:.1f}%"


def write(result: dict[str, Any]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    variants, items = result["variants"], {i["id"]: i for i in result["items"]}
    chosen, baseline = result["chosenJudge"], next(iter(variants))
    tuned_embedding = list(variants)[1]
    lines = [
        "# Skill matching evaluation (B-08)",
        "",
        f"Generated by `api/scripts/eval_matching.py` on {result['generatedAt']}, commit {result['commit']}. "
        f"Gold set `api/evals/matching_gold.json` version {result['gold']['version']}: {result['gold']['items']} items, "
        f"{result['gold']['dev']} dev and {result['gold']['test']} test. Embeddings: {result['embeddingModel']}. All data is synthetic (A6).",
        "",
        "Each item is one requirement (as OD-7 splits it) against the verified skills of one credential profile. A prediction is "
        "right when it names a skill the gold set lists for that requirement, or names none when the list is empty. A wrong skill "
        "counts as both a false match and a missed requirement. Precision answers \"when the system says covered, is it right?\", "
        "recall answers \"of the covered requirements, how many did it find?\".",
        "",
        "**Selection rule, fixed before the run:** the embedding threshold and the judge variant are chosen by F1 on the dev split "
        "(ties: higher precision, then lower latency). The test split is reported as is and was never used to choose anything.",
        "",
        "| Variant | Dev P | Dev R | Dev F1 | Test P | Test R | Test F1 | Test accuracy | Judge call latency, median |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for name, v in variants.items():
        if "error" in v:
            lines.append(f"| {name} | failed: {v['error']} | | | | | | | |")
            continue
        d, t = v["dev"], v["test"]
        lat = f"{v['latencyMedianS']} s (max {v['latencyMaxS']} s)" if v.get("latencyMedianS") is not None else "—"
        mark = " **(chosen)**" if name == chosen else ""
        lines.append(
            f"| {name}{mark} | {_pct(d['precision'])} | {_pct(d['recall'])} | {_pct(d['f1'])} | {_pct(t['precision'])} | "
            f"{_pct(t['recall'])} | {_pct(t['f1'])} | {_pct(t['accuracy'])} | {lat} |"
        )
    compare = [baseline, tuned_embedding] + ([chosen] if chosen else [])
    tags = list(variants[baseline]["testByTag"])
    lines += ["", "## Test accuracy by kind of requirement", "", "| Kind | Items | " + " | ".join(compare) + " |", "| --- | --- |" + " --- |" * len(compare)]
    for tag in tags:
        count = sum(1 for i in items.values() if i["split"] == "test" and i["tag"] == tag)
        lines.append(f"| {tag} | {count} | " + " | ".join(_pct(variants[c]["testByTag"][tag]) for c in compare) + " |")
    product = result["product"]
    if chosen:
        v = variants[chosen]
        errors = [k for k, p in v["predictions"].items() if items[k]["split"] == "test" and p["outcome"] not in ("TP", "TN")]
        lines += ["", f"## Test items the chosen judge got wrong ({len(errors)})", ""]
        if errors:
            lines += ["| Item | Profile | Requirement | Expected | Predicted | Judge's reason |", "| --- | --- | --- | --- | --- | --- |"]
            for k in errors:
                i = items[k]
                lines.append(
                    f"| {k} | {i['profile']} | {i['requirement']} | {', '.join(i['expected']) or 'none'} | "
                    f"{v['predictions'][k]['predicted'] or 'none'} | {result['reasons'][chosen][k]} |"
                )
        else:
            lines.append("None.")
        lines += ["", f"## Stability of the chosen judge ({len(result['repeats'])} more uncached runs)", ""]
        for n, r in enumerate(result["repeats"], 2):
            if "error" in r:
                lines.append(f"- Run {n}: failed ({r['error']}).")
            else:
                changed = ", ".join(r["changedItems"]) or "none"
                lines.append(
                    f"- Run {n}: dev F1 {_pct(r['devF1'])}, test F1 {_pct(r['testF1'])}, test accuracy {_pct(r['testAccuracy'])}; "
                    f"items whose prediction changed from run 1: {changed}."
                )
        same = v["model"] == product["judgeModel"] and v["floor"] == product["candidateFloor"]
        lines += [
            "",
            "## Product setting",
            "",
            f"`app/ams.py` ships `JUDGE_MODEL = \"{product['judgeModel']}\"` and `CANDIDATE_FLOOR = {product['candidateFloor']}`, "
            + ("the variant chosen above." if same else f"**which differs from the chosen variant ({chosen}); update it.**"),
        ]
        floor = "none" if product["candidateFloor"] is None else f"{product['candidateFloor']:.2f}"
        backup = variants.get(f"judge {product['judgeBackup']}, floor {floor}", {})
        if "dev" in backup:
            lines.append(
                f"When it does not answer, AMS asks the backup judge `{product['judgeBackup']}` (dev F1 {_pct(backup['dev']['f1'])}, "
                f"test F1 {_pct(backup['test']['f1'])}, test precision {_pct(backup['test']['precision'])}); `modelVersion` names the model that judged."
            )
        lines += [
            f"The embedding-only fallback, used when neither judge answers, ships `THRESHOLD = {product['threshold']}`; "
            f"the best dev threshold was {result['tunedThreshold']:.3f}"
            + ("." if abs(product["threshold"] - result["tunedThreshold"]) < 1e-9 else "; **update it.**"),
        ]
    lines += [
        "",
        "## Limits of this evaluation",
        "",
        "- The labels were drafted by the coding agent from the skill catalog and must be reviewed by the team; debatable pairs were left out, so the set is easier than real postings.",
        f"- The test split has {result['gold']['test']} items, so one item moves test accuracy by about {100 / result['gold']['test']:.1f} points.",
        "- Each variant ran once at temperature 0; only the chosen one was repeated (above).",
        "- Latency is per judge call from a laptop in Indonesia to the Gemini API's free tier, not end to end.",
        f"- Judge calls that failed and were retried: {result['judgeFailures'] or 'none'}.",
    ]
    (OUT / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", default="gemini-3.1-flash-lite,gemini-3.5-flash-lite")
    parser.add_argument("--floors", default="none,0.60")
    parser.add_argument("--repeats", type=int, default=2, help="extra uncached runs of the chosen judge")
    parser.add_argument("--rewrite", action="store_true", help="only re-render README.md from results.json with the current product setting")
    args = parser.parse_args()
    if args.rewrite:
        result = json.loads((OUT / "results.json").read_text(encoding="utf-8"))
        result["product"] = product_setting()
        write(result)
        print(f"re-rendered {OUT / 'README.md'}")
        return
    if not config.GEMINI_API_KEY:
        raise SystemExit("GEMINI_API_KEY is not set (pass --env-file ../.env)")
    floors = [None if f == "none" else float(f) for f in args.floors.split(",")]
    result = run(args.models.split(","), floors, args.repeats)
    write(result)
    print(f"chosen: {result['chosenJudge']}; wrote {OUT}")


if __name__ == "__main__":
    main()
