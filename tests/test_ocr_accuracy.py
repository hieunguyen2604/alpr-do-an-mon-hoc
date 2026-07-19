"""Tests for the NFR-A4..A8 measurement harness.

The harness produces the numbers the thesis defends, so the parts of it that
*decide* something -- how an error is classified, how a rate is aggregated,
how a verdict is reached -- are tested directly. A bug in any of them would not
crash anything; it would quietly publish a wrong figure.
"""

from __future__ import annotations

import numpy as np
import pytest

from ai.evaluation.ocr_accuracy import (
    CANONICAL_ASPECT_RATIO,
    Sample,
    accuracy_block,
    classify_error,
    confusion_recommendations,
    corpus_cer,
    restore_aspect_ratio,
)


def _sample(truth: str, raw: str, post: str, line_count: int = 1) -> Sample:
    """Build a measured sample with only the fields the metrics read.

    Args:
        truth: Ground-truth plate string.
        raw: The NFR-A5 string (engine output, cleaned).
        post: The NFR-A6 string (normalised output).
        line_count: 1 or 2.

    Returns:
        A populated :class:`~ai.evaluation.ocr_accuracy.Sample`.
    """
    return Sample(
        image_path="x.jpg",
        truth=truth,
        line_count=line_count,
        source_dataset="test",
        split="train",
        raw_ocr_text=raw,
        plate_number=post,
        ocr_ms=1.0,
    )


class TestClassifyError:
    """One misread must land in exactly one class."""

    @pytest.mark.parametrize(
        ("truth", "prediction", "expected"),
        [
            ("30A1234", "30A1234", "correct"),
            ("30A1234", "", "empty_read"),
            ("30A1234", "3OA1234", "substitution"),
            ("30A1234", "30A123", "missing_chars"),
            ("30A1234", "30A12345", "extra_chars"),
            ("30A1234", "30A1243", "transposition"),
            ("30A1234", "3OA123", "mixed"),
        ],
    )
    def test_classes(self, truth: str, prediction: str, expected: str) -> None:
        """Each canonical failure shape maps to its own class."""
        assert classify_error(truth, prediction) == expected

    def test_transposition_beats_substitution(self) -> None:
        """A reordering is reported as such, not as two substitutions.

        This is the one class a character error rate cannot see: a reordered
        string has the same character histogram as the truth, so CER-based
        reporting would show it as an ordinary error. On a two-line plate it is
        the signature of the halves being merged in the wrong order (R-04).
        """
        assert classify_error("29B18888", "88889B12") == "transposition"


class TestCorpusCer:
    """Corpus-level aggregation, not the mean of per-sample rates."""

    def test_weights_by_reference_length(self) -> None:
        """A long plate contributes more reference characters than a short one.

        Two samples, one perfect 9-character plate and one 7-character plate
        with a single substitution: corpus CER is 1/16, whereas the mean of the
        per-sample rates would be 1/14. The harness must report the former.
        """
        pairs = [("123456789", "123456789"), ("30A1234", "30A1235")]
        assert corpus_cer(pairs) == pytest.approx(1 / 16)

    def test_empty_corpus_is_zero(self) -> None:
        """No data yields 0.0 rather than a division by zero."""
        assert corpus_cer([]) == 0.0


class TestAccuracyBlock:
    """The NFR figures, and the post-processing contribution."""

    def test_empty_group_reports_no_data_not_zero(self) -> None:
        """An empty group says count=0 and publishes no rates.

        "Not measured" and "zero per cent" are different statements; emitting
        0.0 for an empty group would let an unmeasured split read as a total
        failure.
        """
        block = accuracy_block([])
        assert block == {"count": 0}
        assert "exact_post_norm" not in block

    def test_postprocessing_gain_is_a5_to_a6_in_points(self) -> None:
        """The headline contribution is the difference of the two rates."""
        samples = [
            _sample("30A1234", "3OA1234", "30A1234"),  # fixed by the rules
            _sample("30A1235", "30A1235", "30A1235"),  # already right
            _sample("30A1236", "30A9999", "30A9999"),  # unrecoverable
            _sample("30A1237", "30A1237", "30A1237"),
        ]
        block = accuracy_block(samples)

        assert block["exact_pre_norm"] == pytest.approx(0.50)
        assert block["exact_post_norm"] == pytest.approx(0.75)
        assert block["postprocessing_gain_points"] == pytest.approx(25.0)
        assert block["postprocessing_fixed"] == 1
        assert block["postprocessing_broke"] == 0

    def test_a_regression_caused_by_the_rules_is_counted(self) -> None:
        """Normalisation breaking a correct string is reported, not hidden.

        A negative contribution is a real possible outcome of the positional
        repair rules, and the report has to be able to state it.
        """
        samples = [_sample("30A1234", "30A1234", "30A1239")]
        block = accuracy_block(samples)

        assert block["postprocessing_broke"] == 1
        assert block["postprocessing_gain_points"] == pytest.approx(-100.0)


class TestRestoreAspectRatio:
    """The repair for the square-exported label corpus."""

    @pytest.mark.parametrize("line_count", [1, 2])
    def test_reshapes_to_the_regulation_ratio(self, line_count: int) -> None:
        """Width follows QCVN 08:2024/BCA; height is left alone."""
        image = np.zeros((640, 640, 3), dtype=np.uint8)
        result = restore_aspect_ratio(image, line_count)

        assert result.shape[0] == 640
        assert result.shape[1] / result.shape[0] == pytest.approx(
            CANONICAL_ASPECT_RATIO[line_count], rel=0.01
        )

    def test_unknown_line_count_is_a_no_op(self) -> None:
        """An unexpected label degrades to a pass-through, not an exception."""
        image = np.zeros((64, 64, 3), dtype=np.uint8)
        assert restore_aspect_ratio(image, 3) is image

    def test_one_line_and_two_line_are_distinguishable_afterwards(self) -> None:
        """The repair restores the signal estimate_line_count depends on.

        Both crops start square, so the estimator cannot tell them apart. After
        the repair one sits above the 2.5 threshold and the other below it,
        which is the entire purpose of the step.
        """
        from ai.inference.two_line import estimate_line_count

        square = np.zeros((640, 640, 3), dtype=np.uint8)
        assert estimate_line_count(restore_aspect_ratio(square, 1)) == 1
        assert estimate_line_count(restore_aspect_ratio(square, 2)) == 2


class TestConfusionRecommendations:
    """Confronting the shape-based repair tables with measured data."""

    def test_splits_confirmed_from_unobserved(self) -> None:
        """A table entry the data never exercises is reported as unobserved.

        ``TO_DIGIT`` maps ``O -> 0``, which is the claim "a 0 misread as an O".
        Feeding exactly that confusion in must mark the rule confirmed, and
        must leave the rules with no supporting evidence in the other list.
        """
        charset = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        matrix = [[0] * 36 for _ in range(36)]
        matrix[charset.index("0")][charset.index("O")] = 12
        confusion = {
            "charset": charset,
            "matrix": matrix,
            "top_confusions": [{"true": "0", "predicted": "O", "count": 12}],
        }

        review = confusion_recommendations(confusion)
        confirmed = {item["rule"] for item in review["confirmed"]}
        unobserved = {item["rule"] for item in review["unobserved"]}

        assert "O -> 0" in confirmed
        assert "O -> 0" not in unobserved
        assert unobserved  # every other hypothesis is still unsupported

    def test_reports_frequent_confusions_absent_from_the_tables(self) -> None:
        """A confusion no rule covers is surfaced as a proposed addition."""
        charset = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        matrix = [[0] * 36 for _ in range(36)]
        matrix[charset.index("N")][charset.index("M")] = 40
        confusion = {"charset": charset, "matrix": matrix, "top_confusions": []}

        missing = confusion_recommendations(confusion)["missing_from_tables"]
        assert {"true": "N", "predicted": "M", "count": 40} in missing
