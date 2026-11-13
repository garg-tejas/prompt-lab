"""Immutable input identity for evaluation comparisons; no dataset content stored."""
import hashlib
import json


def dataset_fingerprint(rows):
    items = [
        {"id": str(row.id), "question": row.question, "context": row.context,
         "expected_answer": row.expected_answer, "extras": row.extras}
        for row in rows
    ]
    if len({row["id"] for row in items}) != len(items):
        raise ValueError("Duplicate row IDs in evaluation sample")
    encoded = json.dumps(sorted(items, key=lambda row: row["id"]), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def snapshot_status(summary_a, summary_b):
    first, second = summary_a.get("dataset_fingerprint"), summary_b.get("dataset_fingerprint")
    if not isinstance(first, str) or not isinstance(second, str) or not first or not second:
        return "unknown"
    return "matching" if first == second else "different"
