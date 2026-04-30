"""Unit tests for pure helper functions in services."""
import pytest

from app.services.ab_test_service import _paired_stats
from app.services.prompt_service import compute_diff


# ---------------------------------------------------------------------------
# _paired_stats (AB test statistics)
# ---------------------------------------------------------------------------

class TestPairedStats:
    def test_empty_list(self):
        """An empty diff list should return neutral stats with no winner."""
        result = _paired_stats([])
        assert result["mean_diff"] == 0.0
        assert result["significant"] is False
        assert result["winner"] == "tie"

    def test_single_element(self):
        """A single diff cannot produce a meaningful std-dev — returns neutral stats."""
        result = _paired_stats([0.5])
        assert result["mean_diff"] == 0.0  # early-return guard for n < 2
        assert result["std_dev"] == 0.0
        assert result["significant"] is False
        assert result["winner"] == "tie"

    def test_clear_winner_significant(self):
        """A large, consistent diff should be significant with a declared winner."""
        diffs = [0.8, 0.9, 0.7, 0.85, 0.75, 0.95, 0.8, 0.9, 0.85, 0.8]
        # 10 samples -> threshold 2.2
        result = _paired_stats(diffs)
        assert result["mean_diff"] == pytest.approx(0.83, abs=0.01)
        assert result["significant"] is True
        assert result["winner"] == "a"
        assert result["n"] == 10
        assert "ci_95" in result

    def test_clear_loser_significant(self):
        """A large negative diff should declare 'b' as winner."""
        diffs = [-0.8, -0.9, -0.7, -0.85, -0.75, -0.95, -0.8, -0.9, -0.85, -0.8]
        result = _paired_stats(diffs)
        assert result["significant"] is True
        assert result["winner"] == "b"

    def test_tie_no_significance(self):
        """Small/noisy diffs around zero should not be significant."""
        diffs = [0.02, -0.01, 0.03, -0.02, 0.01]
        result = _paired_stats(diffs)
        assert result["significant"] is False
        assert result["winner"] == "tie"

    def test_zero_std_error_is_significant(self):
        """If all diffs are identical, std_error is 0 and significance is True."""
        diffs = [0.5, 0.5, 0.5, 0.5]
        result = _paired_stats(diffs)
        assert result["std_error"] == 0.0
        assert result["significant"] is True
        assert result["winner"] == "a"

    def test_ci_bounds(self):
        """95% CI should be ordered [lower, upper] and straddle the mean."""
        diffs = [0.5, 0.6, 0.4, 0.55, 0.45]
        result = _paired_stats(diffs)
        lower, upper = result["ci_95"]
        assert lower <= result["mean_diff"] <= upper


# ---------------------------------------------------------------------------
# compute_diff (prompt diff utility)
# ---------------------------------------------------------------------------

class TestComputeDiff:
    def test_identical_content(self):
        """Identical strings should produce an empty diff."""
        text = "Hello world\nLine two"
        diff = compute_diff(text, text)
        assert diff == ""

    def test_added_line(self):
        """A single added line should appear in the unified diff."""
        old = "line one\nline two"
        new = "line one\nline two\nline three"
        diff = compute_diff(old, new)
        assert "+line three" in diff
        assert "--- a" in diff
        assert "+++ b" in diff

    def test_removed_line(self):
        """A removed line should appear with a minus prefix."""
        old = "line one\nline two\nline three"
        new = "line one\nline three"
        diff = compute_diff(old, new)
        assert "-line two" in diff

    def test_modified_line(self):
        """A changed line should show both old and new versions."""
        old = "foo = 1"
        new = "foo = 2"
        diff = compute_diff(old, new)
        assert "-foo = 1" in diff
        assert "+foo = 2" in diff

    def test_multiline_diff(self):
        """Complex diffs should preserve all line changes."""
        old = "a\nb\nc\nd"
        new = "a\nB\nc\nD\ne"
        diff = compute_diff(old, new)
        assert "-b" in diff
        assert "+B" in diff
        assert "-d" in diff
        assert "+D" in diff
        assert "+e" in diff
