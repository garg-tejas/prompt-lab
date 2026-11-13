"""Deterministic paired comparison of recorded scores; never calls a model."""
import math

from app.core.stats import paired_stats


QUALITY_METRICS = {
    "faithfulness", "answer_relevance", "context_precision", "context_recall",
    "answer_correctness",
}
LOWER_IS_BETTER = {
    "latency_ms", "estimated_cost", "input_tokens", "output_tokens", "total_tokens",
}
CONDITIONAL_METRICS = {"context_recall", "answer_correctness"}


def matching_eligibility(summary_a: dict, summary_b: dict) -> dict:
    """Use only matching evaluation-time manifests, never today's dataset rows."""
    manifest_a = summary_a.get("metric_eligible_rows")
    manifest_b = summary_b.get("metric_eligible_rows")
    if not isinstance(manifest_a, dict) or not isinstance(manifest_b, dict):
        return {}
    result = {}
    for name in CONDITIONAL_METRICS:
        rows_a, rows_b = manifest_a.get(name), manifest_b.get(name)
        if not isinstance(rows_a, list) or not isinstance(rows_b, list):
            continue
        if not all(isinstance(row, str) for row in rows_a + rows_b):
            continue
        if len(rows_a) != len(set(rows_a)) or len(rows_b) != len(set(rows_b)):
            continue
        if set(rows_a) == set(rows_b):
            result[name] = rows_a
    return result


def metric_direction(name: str) -> str | None:
    if name in LOWER_IS_BETTER:
        return "lower"
    if name in QUALITY_METRICS:
        return "higher"
    return None


def _numeric(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def compare_scores(scores_a: dict, scores_b: dict, expected_a=None, expected_b=None, *, eligible_rows=None) -> tuple:
    """Keep raw A-B deltas, orient winners, and expose all omitted observations.

    An overall winner requires complete recorded coverage and agreement across
    every quality metric. This is a descriptive comparison, not a release gate or
    a multiple-comparison-adjusted statistical claim.
    """
    rows_a, rows_b = set(scores_a), set(scores_b)
    union = sorted(rows_a | rows_b)
    common = rows_a & rows_b
    eligible_rows = eligible_rows or {}
    names = sorted({name for rows in (scores_a, scores_b) for values in rows.values() for name in values} | set(eligible_rows))
    metrics = {}
    for name in names:
        # Conditional metrics require the original evaluation applicability
        # manifest. An absent score alone cannot distinguish inapplicability
        # (no reference answer) from scoring failure.
        eligibility_known = name in eligible_rows or name not in CONDITIONAL_METRICS
        eligible = set(eligible_rows[name]) if name in eligible_rows else set(union)
        valid_a = {row for row in rows_a & eligible if _numeric(scores_a[row].get(name))}
        valid_b = {row for row in rows_b & eligible if _numeric(scores_b[row].get(name))}
        paired = sorted(valid_a & valid_b)
        stats = paired_stats([scores_a[row][name] - scores_b[row][name] for row in paired])
        direction = metric_direction(name)
        if direction == "lower" and stats["winner"] != "tie":
            stats["winner"] = "b" if stats["winner"] == "a" else "a"
        elif direction is None:
            stats["winner"] = "tie"
        stats.update({
            "direction": direction,
            "available_a": len(valid_a), "available_b": len(valid_b),
            "excluded_row_ids": sorted(eligible - set(paired)),
            "coverage_status": ("complete" if set(paired) == eligible else "incomplete") if eligibility_known else "unknown",
            "expected_eligible": len(eligible) if eligibility_known else None,
            "missing_score_row_ids": sorted(eligible - set(paired)) if eligibility_known else None,
            "not_applicable_row_ids": sorted(set(union) - eligible) if eligibility_known else None,
        })
        metrics[name] = stats

    coverage = {
        "observed_a": len(rows_a), "observed_b": len(rows_b),
        "expected_a": expected_a, "expected_b": expected_b,
        "paired_rows": len(common), "union_rows": len(union),
        "only_a_row_ids": sorted(rows_a - rows_b),
        "only_b_row_ids": sorted(rows_b - rows_a),
        "missing_results_a": max(0, expected_a - len(rows_a)) if expected_a is not None else None,
        "missing_results_b": max(0, expected_b - len(rows_b)) if expected_b is not None else None,
    }
    row_complete = (
        expected_a is not None and expected_b is not None
        and expected_a == expected_b == len(common) == len(union)
    )
    metric_statuses = {metric["coverage_status"] for metric in metrics.values()}
    metric_coverage = "incomplete" if "incomplete" in metric_statuses else "unknown" if "unknown" in metric_statuses else "complete"
    quality = [metrics[name]["winner"] for name in names if name in QUALITY_METRICS and metrics[name]["expected_eligible"] != 0]
    overall = quality[0] if row_complete and metric_coverage == "complete" and quality and len(set(quality)) == 1 else "tie"
    coverage["complete"] = row_complete
    coverage["metric_coverage"] = metric_coverage
    summary = {
        "metrics": metrics, "coverage": coverage,
        "overall_winner": overall,
        "overall_method": "complete_coverage_unanimous_quality_metrics",
        "decision_note": "Descriptive comparison only; no primary release metric or multiplicity correction is configured. Conditional metric applicability is unknown without an evaluation-time eligibility manifest.",
        "a_wins": sum(metric["winner"] == "a" for metric in metrics.values()),
        "b_wins": sum(metric["winner"] == "b" for metric in metrics.values()),
        "total_samples": len(common),
    }
    per_sample = []
    for row in union:
        wins = {"a": 0, "b": 0, "tie": 0}
        missing = []
        not_applicable = []
        for name in names:
            if name in eligible_rows and row not in eligible_rows[name]:
                not_applicable.append(name)
                continue
            a, b = scores_a.get(row, {}).get(name), scores_b.get(row, {}).get(name)
            direction = metric_direction(name)
            if not _numeric(a) or not _numeric(b) or direction is None:
                missing.append(name)
                continue
            if a == b:
                wins["tie"] += 1
            else:
                wins["a" if (a > b) == (direction == "higher") else "b"] += 1
        per_sample.append({"dataset_row_id": row, "wins": wins, "excluded_metrics": missing, "not_applicable_metrics": not_applicable})
    return summary, per_sample
