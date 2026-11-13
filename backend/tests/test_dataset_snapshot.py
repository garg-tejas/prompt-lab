from types import SimpleNamespace

import pytest

from app.core.dataset_snapshot import dataset_fingerprint, snapshot_status
from app.services.ab_test_service import _owned_runs
from app.services.eval_service import _summarize
from unittest.mock import AsyncMock
import asyncio


def row(identity="a", **changes):
    fields = {"id": identity, "question": "Question?", "context": "Evidence", "expected_answer": None, "extras": {"topic": "test"}}
    return SimpleNamespace(**{**fields, **changes})


def test_fingerprint_ignores_row_order_and_extra_key_order():
    assert dataset_fingerprint([row("a"), row("b")]) == dataset_fingerprint([row("b"), row("a")])
    assert dataset_fingerprint([row(extras={"a": 1, "b": 2})]) == dataset_fingerprint([row(extras={"b": 2, "a": 1})])


@pytest.mark.parametrize("changes", [{"question": "Different?"}, {"context": "Different context"}, {"expected_answer": "A reference"}, {"extras": {"topic": "changed"}}, {"id": "different-row"}])
def test_fingerprint_changes_when_any_input_changes(changes):
    assert dataset_fingerprint([row()]) != dataset_fingerprint([row(**changes)])


def test_duplicate_ids_fail():
    with pytest.raises(ValueError, match="Duplicate"):
        dataset_fingerprint([row(), row()])


def test_legacy_snapshot_identity_remains_unknown():
    assert snapshot_status({}, {"dataset_fingerprint": "hash"}) == "unknown"
    assert snapshot_status({"dataset_fingerprint": "first"}, {"dataset_fingerprint": "second"}) == "different"


def test_same_dataset_id_with_different_input_fingerprints_is_rejected():
    a = SimpleNamespace(id="a", created_by="owner", status="completed", dataset_id="same", results_summary={"dataset_fingerprint": "first"})
    b = SimpleNamespace(id="b", created_by="owner", status="completed", dataset_id="same", results_summary={"dataset_fingerprint": "second"})
    result = SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: [a, b]))
    db = SimpleNamespace(execute=AsyncMock(return_value=result))
    with pytest.raises(ValueError, match="snapshots differ"):
        asyncio.run(_owned_runs(db, "a", "b", "owner"))


def test_summary_carries_hash_without_storing_dataset_content():
    summary = _summarize({}, 1, 0, 0, input_fingerprint="digest")
    assert summary["dataset_fingerprint"] == "digest"
    assert "question" not in summary
