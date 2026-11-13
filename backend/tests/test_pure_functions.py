"""Unit tests for pure helper functions in services."""
import pytest

from app.core.crypto import decrypt_secret, encrypt_secret
from app.core.stats import student_t_two_tailed_p
from app.services.ab_test_service import _paired_stats
from app.services.metrics import (
    parse_verdict_payload,
    regression_drops,
    score_from_verdicts,
    split_context_chunks,
)
from app.services.eval_service import fill_template, metrics_for_row
from app.services.file_parser import parse_csv_file
from app.services.prompt_service import compute_diff, extract_variables, version_text


# ---------------------------------------------------------------------------
# _paired_stats (AB test statistics)
# ---------------------------------------------------------------------------

class TestPairedStats:
    def test_empty_list(self):
        """An empty diff list should return neutral stats with no winner."""
        result = _paired_stats([])
        assert result["mean_diff"] is None
        assert result["significant"] is False
        assert result["winner"] == "tie"

    def test_single_element(self):
        """Keep the observed difference without inventing inferential statistics."""
        result = _paired_stats([0.5])
        assert result["mean_diff"] == 0.5
        assert result["std_dev"] is None
        assert result["std_error"] is None
        assert result["t_stat"] is None
        assert result["ci_95"] is None
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


class TestPairedPValue:
    def test_critical_value_near_five_percent(self):
        """df=10 two-sided 5% critical value is about 2.228."""
        p = student_t_two_tailed_p(2.228, 10)
        assert p == pytest.approx(0.05, abs=0.004)

    def test_clear_winner_reports_p_value(self):
        diffs = [0.8, 0.9, 0.7, 0.85, 0.75, 0.95, 0.8, 0.9, 0.85, 0.8]
        result = _paired_stats(diffs)
        assert result["p_value"] < 0.05
        assert result["ci_95"][0] > 0


class TestVerdictScoring:
    def test_empty_verdicts_are_not_a_zero(self):
        assert score_from_verdicts([]) is None

    def test_half_the_claims_pass(self):
        assert score_from_verdicts([True, False]) == 0.5

    def test_chunks_split_on_blank_lines(self):
        assert split_context_chunks("one\n\ntwo") == ["one", "two"]

    def test_parse_counts_passes(self):
        payload = '{"verdicts":[{"statement":"a","pass":true},{"statement":"b","pass":false}],"explanation":"ok"}'
        parsed = parse_verdict_payload(payload)
        assert parsed["score"] == 0.5
        assert parsed["explanation"].startswith("1/2")

    def test_regression_uses_the_baseline_average(self):
        current = {"faithfulness": {"mean": 0.4}}
        history = [
            {"faithfulness": {"mean": 0.8}},
            {"faithfulness": {"mean": 0.6}},
        ]
        drops = regression_drops(current, history, 0.1)
        assert drops[0]["previous"] == 0.7
        assert drops[0]["drop"] == 0.3


class TestTemplateAndMetrics:
    def test_fill_template_uses_every_key(self):
        text = fill_template("{{question}} / {{domain}}", {"question": "Q", "domain": "law"})
        assert text == "Q / law"

    def test_ground_truth_metrics_need_an_answer(self):
        assert "answer_correctness" not in metrics_for_row(None)
        assert "context_recall" in metrics_for_row("Paris")

    def test_csv_keeps_extra_columns(self):
        raw = b"question,context,expected_answer,domain\nWhat?,Some text,Paris,geo\n"
        rows = parse_csv_file(raw)
        assert rows[0]["extras"]["domain"] == "geo"
        assert "question" not in rows[0]["extras"]

    def test_variables_include_system_prompt(self):
        names = extract_variables("Hello {{name}}", "You know {{city}}")
        assert names == ["name", "city"]

    def test_version_text_includes_system_and_messages(self):
        version = type(
            "Version",
            (),
            {
                "system_content": "Be brief",
                "messages": [{"role": "user", "content": "Example"}],
                "content": "Answer {{question}}",
            },
        )()
        text = version_text(version)
        assert "Be brief" in text
        assert "Example" in text
        assert "Answer {{question}}" in text


class TestSecrets:
    def test_round_trip(self):
        stored = encrypt_secret("sk-test")
        assert stored.startswith("enc:v1:")
        assert decrypt_secret(stored) == "sk-test"
        assert decrypt_secret("legacy-plain") == "legacy-plain"
