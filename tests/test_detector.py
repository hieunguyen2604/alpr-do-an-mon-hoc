"""Unit tests for :mod:`ai.inference.detector`."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import numpy as np
import pytest

# The project is run from its root and has no installed package metadata, so the
# repository root has to be importable for `import ai...` to resolve.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai.inference.config import InferenceConfig  # noqa: E402
from ai.inference.detector import YoloPlateDetector, _canonical_class_name  # noqa: E402
from ai.inference.exceptions import (  # noqa: E402
    DetectionError,
    InvalidImageError,
    ModelLoadError,
)
from ai.inference.types import PlateDetection  # noqa: E402


# --------------------------------------------------------------------------- #
# Test doubles
# --------------------------------------------------------------------------- #
class FakeBoxes:
    """Stand-in for ``ultralytics.engine.results.Boxes``."""

    def __init__(
        self,
        xyxy: list[list[float]],
        conf: list[float],
        cls: list[int],
    ) -> None:
        self.xyxy = np.asarray(xyxy, dtype=np.float32).reshape(-1, 4)
        self.conf = np.asarray(conf, dtype=np.float32)
        self.cls = np.asarray(cls, dtype=np.float32)

    def __len__(self) -> int:
        return int(self.xyxy.shape[0])


class FakeResult:
    """Stand-in for a single ``ultralytics.engine.results.Results`` object."""

    def __init__(self, boxes: FakeBoxes | None) -> None:
        self.boxes = boxes


class FakeYolo:
    """Stand-in for ``ultralytics.YOLO``."""

    def __init__(
        self,
        names: dict[int, str] | list[str] | None,
        boxes: FakeBoxes | None = None,
        raise_on_predict: Exception | None = None,
    ) -> None:
        if names is not None:
            self.names = names
        self._boxes = boxes
        self._raise_on_predict = raise_on_predict
        self.predict_calls: list[dict[str, Any]] = []

    def predict(self, **kwargs: Any) -> list[FakeResult]:
        self.predict_calls.append(kwargs)
        if self._raise_on_predict is not None:
            raise self._raise_on_predict
        return [FakeResult(self._boxes)]


def make_detector(
    tmp_path: Path,
    names: dict[int, str] | list[str] | None = None,
    boxes: FakeBoxes | None = None,
    raise_on_predict: Exception | None = None,
    weights_name: str = "best.pt",
    **config_overrides: Any,
) -> tuple[YoloPlateDetector, FakeYolo]:
    """Build a detector backed by a fake model and a real (empty) weights file."""
    weights = tmp_path / weights_name
    weights.write_bytes(b"not-real-weights")
    config = InferenceConfig(model_path=weights, **config_overrides)
    fake = FakeYolo(names=names, boxes=boxes, raise_on_predict=raise_on_predict)
    detector = YoloPlateDetector(config, model_loader=lambda path: fake)
    return detector, fake


@pytest.fixture
def image() -> np.ndarray:
    """Return a valid 480x640 BGR image."""
    return np.zeros((480, 640, 3), dtype=np.uint8)


# --------------------------------------------------------------------------- #
# Model loading
# --------------------------------------------------------------------------- #
class TestModelLoading:
    """Failures while loading weights must surface as ModelLoadError."""

    def test_missing_weights_file_raises_model_load_error(self, tmp_path: Path) -> None:
        """A missing file must fail loudly, naming the path that was tried."""
        missing = tmp_path / "models" / "best.pt"
        config = InferenceConfig(model_path=missing)

        with pytest.raises(ModelLoadError) as excinfo:
            YoloPlateDetector(config, model_loader=lambda path: FakeYolo({0: "x"}))

        message = str(excinfo.value)
        assert str(missing) in message, "the message must name the path tried"
        assert "ai.training.train" in message, "the message must suggest training"

    def test_missing_weights_does_not_return_silently(self, tmp_path: Path) -> None:
        """The loader must never be reached when the file is absent."""
        calls: list[Path] = []

        def loader(path: Path) -> FakeYolo:
            calls.append(path)
            return FakeYolo({0: "license_plate"})

        config = InferenceConfig(model_path=tmp_path / "nope.pt")
        with pytest.raises(ModelLoadError):
            YoloPlateDetector(config, model_loader=loader)
        assert calls == []

    def test_directory_instead_of_file_raises_model_load_error(self, tmp_path: Path) -> None:
        """Pointing at a directory is a configuration mistake, not a crash."""
        directory = tmp_path / "weights_dir"
        directory.mkdir()
        config = InferenceConfig(model_path=directory)

        with pytest.raises(ModelLoadError, match="is a directory"):
            YoloPlateDetector(config, model_loader=lambda path: FakeYolo({0: "x"}))

    def test_corrupted_weights_raise_model_load_error(self, tmp_path: Path) -> None:
        """An underlying loader failure is wrapped, not leaked."""
        weights = tmp_path / "best.pt"
        weights.write_bytes(b"garbage")
        config = InferenceConfig(model_path=weights)

        def failing_loader(path: Path) -> Any:
            from ai.inference.detector import _load_yolo_model

            return _load_yolo_model(path)

        with pytest.raises(ModelLoadError) as excinfo:
            YoloPlateDetector(config, model_loader=failing_loader)
        assert str(weights) in str(excinfo.value)

    def test_onnx_weights_are_accepted(self, tmp_path: Path) -> None:
        """ONNX exports must load through the same code path as .pt weights."""
        detector, _ = make_detector(tmp_path, names={0: "license_plate"}, weights_name="best.onnx")
        assert detector.name == "yolo:best.onnx"

    def test_name_property_reports_the_weights_in_use(self, tmp_path: Path) -> None:
        """The engine identifier must trace a result back to its weights."""
        detector, _ = make_detector(
            tmp_path, names={0: "license_plate"}, weights_name="yolo11n-coco.pt"
        )
        assert detector.name == "yolo:yolo11n-coco.pt"


# --------------------------------------------------------------------------- #
# Input validation
# --------------------------------------------------------------------------- #
class TestInvalidImages:
    """Every unusable input must raise InvalidImageError before inference."""

    @pytest.mark.parametrize(
        ("bad_image", "reason"),
        [
            (None, "None input"),
            (np.zeros((0, 0, 3), dtype=np.uint8), "empty array"),
            (np.zeros((0, 640, 3), dtype=np.uint8), "zero-height array"),
            (np.zeros((4, 4, 4, 3), dtype=np.uint8), "4-dimensional array"),
            (np.zeros((10, 10, 5), dtype=np.uint8), "unsupported channel count"),
            ("not-an-image", "string instead of array"),
            (42, "scalar instead of array"),
        ],
    )
    def test_invalid_image_raises(self, tmp_path: Path, bad_image: Any, reason: str) -> None:
        detector, fake = make_detector(tmp_path, names={0: "license_plate"})
        with pytest.raises(InvalidImageError):
            detector.detect(bad_image)
        assert fake.predict_calls == [], f"model must not be invoked for {reason}"

    def test_grayscale_image_is_accepted(self, tmp_path: Path) -> None:
        """2-D input is unusual but decodable; it must not be rejected."""
        detector, fake = make_detector(tmp_path, names={0: "license_plate"})
        assert detector.detect(np.zeros((100, 200), dtype=np.uint8)) == []
        assert len(fake.predict_calls) == 1


# --------------------------------------------------------------------------- #
# Coordinate conversion
# --------------------------------------------------------------------------- #
class TestCoordinateConversion:
    """xyxy floats from YOLO must become clamped integer xywh boxes."""

    def test_xyxy_is_converted_to_xywh(self, tmp_path: Path, image: np.ndarray) -> None:
        boxes = FakeBoxes([[100.0, 50.0, 220.0, 110.0]], [0.9], [0])
        detector, _ = make_detector(tmp_path, names={0: "license_plate"}, boxes=boxes)

        (detection,) = detector.detect(image)

        assert isinstance(detection, PlateDetection)
        assert (detection.bbox.x, detection.bbox.y) == (100, 50)
        assert (detection.bbox.width, detection.bbox.height) == (120, 60)
        assert detection.bbox.to_xyxy() == (100, 50, 220, 110)
        assert detection.confidence == pytest.approx(0.9, abs=1e-6)

    def test_float_coordinates_are_rounded(self, tmp_path: Path, image: np.ndarray) -> None:
        boxes = FakeBoxes([[10.4, 20.6, 50.5, 80.4]], [0.5], [0])
        detector, _ = make_detector(tmp_path, names={0: "license_plate"}, boxes=boxes)

        (detection,) = detector.detect(image)
        assert (detection.bbox.x, detection.bbox.y) == (10, 21)
        assert detection.bbox.to_xyxy() == (10, 21, 50, 80)

    def test_out_of_bounds_box_is_clamped_to_the_image(
        self, tmp_path: Path, image: np.ndarray
    ) -> None:
        """Boxes running past the border must be usable for cropping."""
        boxes = FakeBoxes([[-15.0, -8.0, 900.0, 700.0]], [0.8], [0])
        detector, _ = make_detector(tmp_path, names={0: "license_plate"}, boxes=boxes)

        (detection,) = detector.detect(image)

        assert detection.bbox.to_xyxy() == (0, 0, 640, 480)
        crop = image[detection.bbox.y : detection.bbox.y2, detection.bbox.x : detection.bbox.x2]
        assert crop.shape == (480, 640, 3)

    def test_swapped_corners_are_normalised(self, tmp_path: Path, image: np.ndarray) -> None:
        boxes = FakeBoxes([[220.0, 110.0, 100.0, 50.0]], [0.7], [0])
        detector, _ = make_detector(tmp_path, names={0: "license_plate"}, boxes=boxes)

        (detection,) = detector.detect(image)
        assert detection.bbox.to_xyxy() == (100, 50, 220, 110)

    def test_degenerate_box_is_skipped_not_raised(self, tmp_path: Path, image: np.ndarray) -> None:
        """One collapsed box must not lose the good boxes in the same frame."""
        boxes = FakeBoxes(
            [[10.0, 10.0, 10.0, 40.0], [100.0, 50.0, 220.0, 110.0]],
            [0.95, 0.6],
            [0, 0],
        )
        detector, _ = make_detector(tmp_path, names={0: "license_plate"}, boxes=boxes)

        detections = detector.detect(image)
        assert len(detections) == 1
        assert detections[0].bbox.to_xyxy() == (100, 50, 220, 110)

    def test_results_are_sorted_by_descending_confidence(
        self, tmp_path: Path, image: np.ndarray
    ) -> None:
        boxes = FakeBoxes(
            [[0.0, 0.0, 10.0, 10.0], [20.0, 20.0, 40.0, 40.0], [50.0, 50.0, 70.0, 70.0]],
            [0.30, 0.90, 0.60],
            [0, 0, 0],
        )
        detector, _ = make_detector(tmp_path, names={0: "license_plate"}, boxes=boxes)

        confidences = [d.confidence for d in detector.detect(image)]
        assert confidences == sorted(confidences, reverse=True)

    def test_aspect_ratio_is_available_for_line_count_heuristic(
        self, tmp_path: Path, image: np.ndarray
    ) -> None:
        """A 520x110 single-line plate must land above the 2.5 threshold."""
        boxes = FakeBoxes([[0.0, 0.0, 520.0, 110.0]], [0.9], [0])
        detector, _ = make_detector(tmp_path, names={0: "license_plate"}, boxes=boxes)

        (detection,) = detector.detect(image)
        assert detection.bbox.aspect_ratio == pytest.approx(4.727, abs=0.01)


# --------------------------------------------------------------------------- #
# Class filtering
# --------------------------------------------------------------------------- #
class TestClassFiltering:
    """Only license-plate boxes may leave the detector."""

    def test_single_class_model_keeps_everything(self, tmp_path: Path, image: np.ndarray) -> None:
        boxes = FakeBoxes([[10.0, 10.0, 50.0, 30.0]], [0.9], [0])
        detector, _ = make_detector(tmp_path, names={0: "license_plate"}, boxes=boxes)
        assert len(detector.detect(image)) == 1

    def test_multiclass_model_keeps_only_the_plate_class(
        self, tmp_path: Path, image: np.ndarray
    ) -> None:
        boxes = FakeBoxes(
            [[10.0, 10.0, 50.0, 30.0], [60.0, 60.0, 120.0, 90.0]],
            [0.9, 0.8],
            [2, 5],
        )
        names = {0: "person", 2: "car", 5: "license_plate", 7: "truck"}
        detector, _ = make_detector(tmp_path, names=names, boxes=boxes)

        detections = detector.detect(image)
        assert len(detections) == 1
        assert detections[0].bbox.to_xyxy() == (60, 60, 120, 90)

    def test_coco_style_model_yields_no_plates(self, tmp_path: Path, image: np.ndarray) -> None:
        """The COCO checkpoint has no plate class: an empty list, never an error."""
        coco_names = {index: f"class_{index}" for index in range(80)}
        coco_names.update({0: "person", 2: "car", 3: "motorcycle"})
        boxes = FakeBoxes(
            [[10.0, 10.0, 100.0, 100.0], [120.0, 30.0, 300.0, 200.0]],
            [0.95, 0.88],
            [2, 0],
        )
        detector, _ = make_detector(tmp_path, names=coco_names, boxes=boxes)

        assert detector.detect(image) == []

    def test_alias_class_names_are_recognised(self, tmp_path: Path, image: np.ndarray) -> None:
        boxes = FakeBoxes([[10.0, 10.0, 50.0, 30.0]], [0.9], [1])
        names = {0: "car", 1: "License-Plate"}
        detector, _ = make_detector(tmp_path, names=names, boxes=boxes)
        assert len(detector.detect(image)) == 1

    def test_model_without_class_map_keeps_everything(
        self, tmp_path: Path, image: np.ndarray
    ) -> None:
        """Missing metadata must not silently drop every detection."""
        boxes = FakeBoxes([[10.0, 10.0, 50.0, 30.0]], [0.9], [0])
        detector, _ = make_detector(tmp_path, names=None, boxes=boxes)
        assert len(detector.detect(image)) == 1

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("License-Plate", "license_plate"),
            ("  LICENSE PLATE ", "license_plate"),
            ("license_plate", "license_plate"),
        ],
    )
    def test_canonical_class_name(self, raw: str, expected: str) -> None:
        assert _canonical_class_name(raw) == expected


# --------------------------------------------------------------------------- #
# Inference behaviour
# --------------------------------------------------------------------------- #
class TestInference:
    """Thresholds, empty results, failures and warm-up."""

    def test_config_thresholds_are_forwarded(self, tmp_path: Path, image: np.ndarray) -> None:
        detector, fake = make_detector(
            tmp_path,
            names={0: "license_plate"},
            conf_threshold=0.42,
            iou_threshold=0.33,
            imgsz=480,
            device="cpu",
        )
        detector.detect(image)

        (call,) = fake.predict_calls
        assert call["conf"] == pytest.approx(0.42)
        assert call["iou"] == pytest.approx(0.33)
        assert call["imgsz"] == 480
        assert call["device"] == "cpu"
        assert call["verbose"] is False

    def test_no_boxes_returns_empty_list(self, tmp_path: Path, image: np.ndarray) -> None:
        """No plate in the image is a normal outcome, not an error."""
        detector, _ = make_detector(tmp_path, names={0: "license_plate"}, boxes=None)
        assert detector.detect(image) == []

    def test_empty_boxes_object_returns_empty_list(self, tmp_path: Path, image: np.ndarray) -> None:
        detector, _ = make_detector(
            tmp_path, names={0: "license_plate"}, boxes=FakeBoxes([], [], [])
        )
        assert detector.detect(image) == []

    def test_runtime_failure_becomes_detection_error(
        self, tmp_path: Path, image: np.ndarray
    ) -> None:
        detector, _ = make_detector(
            tmp_path,
            names={0: "license_plate"},
            raise_on_predict=RuntimeError("CUDA out of memory"),
        )
        with pytest.raises(DetectionError, match="CUDA out of memory"):
            detector.detect(image)

    def test_warmup_runs_one_inference_at_configured_size(self, tmp_path: Path) -> None:
        detector, fake = make_detector(tmp_path, names={0: "license_plate"}, imgsz=320)
        detector.warmup()

        (call,) = fake.predict_calls
        assert call["source"].shape == (320, 320, 3)
        assert call["source"].dtype == np.uint8
        assert not call["source"].any(), "warm-up must use a black image"

    def test_detect_after_warmup_still_works(self, tmp_path: Path, image: np.ndarray) -> None:
        boxes = FakeBoxes([[10.0, 10.0, 50.0, 30.0]], [0.9], [0])
        detector, fake = make_detector(tmp_path, names={0: "license_plate"}, boxes=boxes)
        detector.warmup()
        assert len(detector.detect(image)) == 1
        assert len(fake.predict_calls) == 2

    def test_class_names_property_returns_a_copy(self, tmp_path: Path) -> None:
        detector, _ = make_detector(tmp_path, names={0: "license_plate"})
        names = detector.class_names
        names[99] = "tampered"
        assert 99 not in detector.class_names


# --------------------------------------------------------------------------- #
# Contract conformance
# --------------------------------------------------------------------------- #
def test_detector_implements_base_detector(tmp_path: Path) -> None:
    """The adapter must be usable anywhere a BaseDetector is expected."""
    from ai.inference.interfaces import BaseDetector

    detector, _ = make_detector(tmp_path, names={0: "license_plate"})
    assert isinstance(detector, BaseDetector)


def test_module_is_framework_free() -> None:
    """NFR-M1: the ai package must not depend on the web framework layer."""
    source = (PROJECT_ROOT / "ai" / "inference" / "detector.py").read_text(encoding="utf-8")
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith(("import ", "from ")):
            assert "fastapi" not in stripped.lower()
            assert "pydantic" not in stripped.lower()
