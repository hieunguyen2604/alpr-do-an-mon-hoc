"""Unit tests for the video de-duplication path of the detection service."""

from __future__ import annotations

from ai.inference.types import (
    BoundingBox,
    DetectionResult,
    PipelineResult,
    PlateDetection,
    PlateRecognition,
)
from backend.services.detection_service import DetectionService, _within_one_edit


def _entry(
    text: str | None,
    *,
    confidence: float = 0.9,
    kind: str = "car",
    is_valid: bool = True,
) -> DetectionResult:
    """Build a minimal pipeline entry, textless when ``text`` is ``None``."""
    detection = PlateDetection(
        bbox=BoundingBox(x=10, y=10, width=100, height=40),
        confidence=0.8,
    )
    if text is None:
        return DetectionResult(detection=detection, recognition=None)
    recognition = PlateRecognition(
        text=text,
        raw_text=text,
        confidence=confidence,
        line_count=2,
        is_valid_format=is_valid,
        kind=kind,
    )
    return DetectionResult(detection=detection, recognition=recognition)


def _frame(*entries: DetectionResult) -> PipelineResult:
    return PipelineResult(results=list(entries), total_time=0.0, image_width=640, image_height=480)


def _texts(sightings: list[tuple[DetectionResult, int]]) -> set[str]:
    return {
        entry.recognition.text for entry, _ in sightings if entry.recognition is not None
    }


class TestMergeFrameResults:
    """What is allowed into the accumulator at all."""

    def test_textless_box_is_dropped(self) -> None:
        acc: dict[str, tuple[DetectionResult, int, int]] = {}
        DetectionService._merge_frame_results(acc, _frame(_entry(None)), 0)
        assert acc == {}

    def test_short_unclassified_fragment_is_dropped(self) -> None:
        acc: dict[str, tuple[DetectionResult, int, int]] = {}
        for fragment in ("S", "BEK", "187", "27793"):
            DetectionService._merge_frame_results(
                acc, _frame(_entry(fragment, kind="unknown", is_valid=False)), 0
            )
        assert acc == {}

    def test_short_military_plate_is_kept(self) -> None:
        acc: dict[str, tuple[DetectionResult, int, int]] = {}
        DetectionService._merge_frame_results(
            acc, _frame(_entry("KV6938", kind="military", is_valid=False)), 0
        )
        assert set(acc) == {"KV6938"}

    def test_long_unclassified_string_is_kept(self) -> None:
        acc: dict[str, tuple[DetectionResult, int, int]] = {}
        DetectionService._merge_frame_results(
            acc, _frame(_entry("51NG16633", kind="unknown", is_valid=False)), 0
        )
        assert set(acc) == {"51NG16633"}

    def test_repeat_sightings_count_and_keep_best(self) -> None:
        acc: dict[str, tuple[DetectionResult, int, int]] = {}
        DetectionService._merge_frame_results(acc, _frame(_entry("51G31691", confidence=0.7)), 0)
        DetectionService._merge_frame_results(acc, _frame(_entry("51G31691", confidence=0.9)), 5)
        DetectionService._merge_frame_results(acc, _frame(_entry("51G31691", confidence=0.8)), 10)
        entry, frame_index, seen = acc["51G31691"]
        assert seen == 3
        assert frame_index == 5  # the highest-confidence sighting's frame
        assert entry.recognition is not None
        assert entry.recognition.confidence == 0.9


class TestCollapseVariants:
    """Which accumulator rows survive to become history records."""

    def test_one_edit_variants_in_window_merge_by_majority(self) -> None:
        acc: dict[str, tuple[DetectionResult, int, int]] = {
            # Wrong spelling: higher confidence, single frame.
            "51P51578": (_entry("51P51578", confidence=0.919), 200, 1),
            # Right spelling: lower confidence, majority of frames.
            "51P54578": (_entry("51P54578", confidence=0.913), 210, 3),
        }
        survivors = DetectionService._collapse_variants(acc, max_frame_gap=48)
        assert _texts(survivors) == {"51P54578"}

    def test_distant_in_time_does_not_merge(self) -> None:
        acc: dict[str, tuple[DetectionResult, int, int]] = {
            "51P54578": (_entry("51P54578"), 0, 2),
            "51P54579": (_entry("51P54579"), 500, 2),
        }
        survivors = DetectionService._collapse_variants(acc, max_frame_gap=48)
        assert _texts(survivors) == {"51P54578", "51P54579"}

    def test_two_edits_apart_merges_when_province_and_tail_match(self) -> None:
        """Hai sai khac, nhung cung ma tinh va cung ba so cuoi -> gop."""
        acc: dict[str, tuple[DetectionResult, int, int]] = {
            "76B141873": (_entry("76B141873"), 100, 2),
            "76S111873": (_entry("76S111873"), 105, 1),
        }
        survivors = DetectionService._collapse_variants(acc, max_frame_gap=48)
        assert _texts(survivors) == {"76B141873"}

    def test_two_edits_apart_does_not_merge_across_provinces(self) -> None:
        """Rao mac tinh: hai sai khac nhung KHAC ma tinh thi khong duoc gop."""
        acc: dict[str, tuple[DetectionResult, int, int]] = {
            "76B141873": (_entry("76B141873"), 100, 2),
            "51B111873": (_entry("51B111873"), 105, 1),
        }
        survivors = DetectionService._collapse_variants(acc, max_frame_gap=48)
        assert _texts(survivors) == {"76B141873", "51B111873"}

    def test_two_edits_apart_does_not_merge_without_shared_tail(self) -> None:
        """Cung ma tinh, khac chu seri, va ba so cuoi KHONG trung -> khong gop."""
        acc: dict[str, tuple[DetectionResult, int, int]] = {
            "76B141873": (_entry("76B141873"), 100, 2),
            "76S141592": (_entry("76S141592"), 105, 1),
        }
        survivors = DetectionService._collapse_variants(acc, max_frame_gap=48)
        assert _texts(survivors) == {"76B141873", "76S141592"}

    def test_invalid_variant_absorbed_into_valid(self) -> None:
        acc: dict[str, tuple[DetectionResult, int, int]] = {
            "59F227793": (_entry("59F227793"), 100, 1),
            "59F22779": (_entry("59F22779", kind="unknown", is_valid=False), 104, 2),
        }
        survivors = DetectionService._collapse_variants(acc, max_frame_gap=48)
        assert _texts(survivors) == {"59F227793"}

    def test_unknown_fps_disables_merging(self) -> None:
        acc: dict[str, tuple[DetectionResult, int, int]] = {
            "51P51578": (_entry("51P51578"), 200, 1),
            "51P54578": (_entry("51P54578"), 210, 3),
        }
        survivors = DetectionService._collapse_variants(acc, max_frame_gap=0)
        assert _texts(survivors) == {"51P51578", "51P54578"}


class TestWithinOneEdit:
    """The bounded edit-distance predicate."""

    def test_identical(self) -> None:
        assert _within_one_edit("51G31691", "51G31691")

    def test_substitution(self) -> None:
        assert _within_one_edit("51P51578", "51P54578")

    def test_insertion_and_deletion(self) -> None:
        assert _within_one_edit("59F22779", "59F227793")
        assert _within_one_edit("59F227793", "59F22779")

    def test_two_substitutions_rejected(self) -> None:
        assert not _within_one_edit("76B141873", "76S111873")

    def test_length_gap_of_two_rejected(self) -> None:
        assert not _within_one_edit("59F2277", "59F227793")

    def test_empty_against_one_char(self) -> None:
        assert _within_one_edit("", "A")
        assert not _within_one_edit("", "AB")
