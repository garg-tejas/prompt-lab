"""Judge scoring helpers. The model returns verdicts; the score is computed here."""

import json
from typing import List


def split_context_chunks(context: str) -> List[str]:
    parts = [part.strip() for part in (context or "").split("\n\n") if part.strip()]
    if parts:
        return parts
    text = (context or "").strip()
    return [text] if text else []


def score_from_verdicts(verdicts: List[bool]) -> float | None:
    if not verdicts:
        return None
    return round(sum(1 for item in verdicts if item) / len(verdicts), 4)


def effective_score(score: float | None, human_score: float | None) -> float | None:
    if human_score is not None:
        return human_score
    return score


def parse_verdict_payload(content: str) -> dict:
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        start = content.find("{")
        end = content.rfind("}")
        if start == -1 or end == -1:
            raise
        data = json.loads(content[start : end + 1])
    if not isinstance(data, dict):
        raise ValueError("Judge response was not an object")

    verdicts: List[bool] = []
    statements: List[str] = []
    for item in data.get("verdicts") or []:
        if not isinstance(item, dict) or "pass" not in item:
            continue
        verdicts.append(bool(item["pass"]))
        statements.append(str(item.get("statement", "")))

    explanation = str(data.get("explanation") or "")
    if verdicts:
        passed = sum(1 for item in verdicts if item)
        detail = f"{passed}/{len(verdicts)} passed. {explanation}".strip()
        return {
            "score": score_from_verdicts(verdicts),
            "explanation": detail,
            "verdicts": verdicts,
        }

    if "score" in data and data["score"] is not None:
        score = max(0.0, min(1.0, float(data["score"])))
        return {"score": round(score, 4), "explanation": explanation, "verdicts": []}

    raise ValueError("Judge response had no verdicts")


def regression_drops(current: dict, history: List[dict], threshold: float) -> List[dict]:
    """Compare current means to the average of earlier run means."""
    drops = []
    for name, stats in current.items():
        if not isinstance(stats, dict) or stats.get("mean") is None:
            continue
        baselines = []
        for previous in history:
            before = (previous or {}).get(name)
            if isinstance(before, dict) and before.get("mean") is not None:
                baselines.append(before["mean"])
        if not baselines:
            continue
        baseline = sum(baselines) / len(baselines)
        delta = round(baseline - stats["mean"], 4)
        if delta >= threshold:
            drops.append(
                {
                    "metric": name,
                    "previous": round(baseline, 4),
                    "current": stats["mean"],
                    "drop": delta,
                    "baseline_runs": len(baselines),
                }
            )
    return drops
