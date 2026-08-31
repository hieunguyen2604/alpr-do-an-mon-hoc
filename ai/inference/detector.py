"""YOLO11-based license plate detector."""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Final

import numpy as np

from ai.inference.config import InferenceConfig
from ai.inference.exceptions import (
    DetectionError,
    InvalidImageError,
    ModelLoadError,
)
from ai.inference.interfaces import BaseDetector
from ai.inference.types import BoundingBox, ImageArray, PlateDetection

__all__ = ["PLATE_CLASS_ALIASES", "SUPPORTED_WEIGHT_SUFFIXES", "YoloPlateDetector"]

LOGGER = logging.getLogger("ai.inference.detector")

PLATE_CLASS_ALIASES: Final[frozenset[str]] = frozenset(
    {"license_plate", "licence_plate", "plate", "license-plate", "bien_so"}
)
"""Class names accepted as "this box is a license plate".

The project's own dataset ships a single class, ``license_plate``. The aliases
cover weights obtained from public datasets, which name the same concept
differently. Matching is case-insensitive and treats ``-`` and spaces as ``_``
(see :func:`_canonical_class_name`).
"""

SUPPORTED_WEIGHT_SUFFIXES: Final[tuple[str, ...]] = (".pt", ".onnx", ".torchscript")
"""Weight file extensions this detector is known to handle.

Ultralytics accepts more formats than these (OpenVINO directories, TensorRT
engines...), so an unknown suffix produces a warning and an attempt, never a
hard refusal.
"""

_TRAINING_HINT: Final[str] = (
    "Train the detector first:\n"
    "    python -m ai.training.train --config yolo11n_finetune.yaml\n"
    "The script publishes the winning weights to <project root>/models/best.pt.\n"
    "Alternatively point ALPR_MODEL_PATH at an existing .pt or .onnx file."
)


def _canonical_class_name(name: str) -> str:
    """Normalise a model class name for alias comparison."""
    return name.strip().lower().replace("-", "_").replace(" ", "_")


def _is_openvino_model_dir(path: Path) -> bool:
    """Return whether a directory holds an OpenVINO IR model."""
    try:
        return any(path.glob("*.xml"))
    except OSError:  # pragma: no cover - unreadable directory
        return False


def _to_numpy(value: Any) -> np.ndarray:
    """Convert a torch tensor -- or anything array-like -- to a NumPy array."""
    cpu = getattr(value, "cpu", None)
    if callable(cpu):
        value = cpu()
    numpy_method = getattr(value, "numpy", None)
    if callable(numpy_method):
        return np.asarray(numpy_method())
    return np.asarray(value)


def _load_yolo_model(weights_path: Path, task: str = "detect") -> Any:
    """Load Ultralytics YOLO weights from disk."""
    try:
        from ultralytics import YOLO
    except ImportError as error:  # pragma: no cover - depends on environment
        raise ModelLoadError(
            "The 'ultralytics' package is required to run the YOLO detector but "
            f"could not be imported ({error}). Install it with: pip install ultralytics"
        ) from error

    try:
        return YOLO(str(weights_path), task=task)
    except Exception as error:
        raise ModelLoadError(
            f"Failed to load YOLO weights from '{weights_path}': {error}. "
            "The file exists but is unreadable, corrupted, or was produced by an "
            "incompatible Ultralytics/PyTorch version."
        ) from error


class YoloPlateDetector(BaseDetector):
    """Locate Vietnamese license plates with an Ultralytics YOLO11 model."""

    def __init__(
        self,
        config: InferenceConfig,
        model_loader: Any = _load_yolo_model,
    ) -> None:
        """Load the detector weights and resolve which classes count as plates."""
        self.config = config
        self._weights_path: Path = Path(config.model_path)
        self._verify_weights_exist()

        if (
            not _is_openvino_model_dir(self._weights_path)
            and self._weights_path.suffix.lower() not in SUPPORTED_WEIGHT_SUFFIXES
        ):
            LOGGER.warning(
                "detector.weights.unknown_suffix path=%s suffix=%s supported=%s",
                self._weights_path,
                self._weights_path.suffix or "<none>",
                ",".join(SUPPORTED_WEIGHT_SUFFIXES),
            )

        started = time.perf_counter()
        self._model: Any = model_loader(self._weights_path)
        load_seconds = time.perf_counter() - started

        self._class_names: dict[int, str] = self._read_class_names()
        self._plate_class_ids: frozenset[int] | None = self._resolve_plate_class_ids()

        LOGGER.info(
            "detector.loaded name=%s path=%s classes=%d plate_class_ids=%s "
            "device=%s conf=%.2f iou=%.2f imgsz=%d load_seconds=%.3f",
            self.name,
            self._weights_path,
            len(self._class_names),
            "all" if self._plate_class_ids is None else sorted(self._plate_class_ids),
            self.config.device,
            self.config.conf_threshold,
            self.config.iou_threshold,
            self.config.imgsz,
            load_seconds,
        )

    # --- Construction helpers ---
    def _verify_weights_exist(self) -> None:
        """Check that the configured weights path points at loadable weights."""
        if self._weights_path.is_file():
            return

        if self._weights_path.is_dir():
            if _is_openvino_model_dir(self._weights_path):
                return
            raise ModelLoadError(
                f"Detector weights path '{self._weights_path}' is a directory but "
                "does not contain an OpenVINO model (no .xml file found). Point "
                "ALPR_MODEL_PATH at a .pt/.onnx file, or at a directory produced "
                "by: python -m ai.training.export --format openvino"
            )

        raise ModelLoadError(
            f"Detector weights not found at '{self._weights_path}'.\n{_TRAINING_HINT}"
        )

    def _read_class_names(self) -> dict[int, str]:
        """Read the ``{index: name}`` class map from the loaded model."""
        raw_names = getattr(self._model, "names", None)
        if isinstance(raw_names, dict):
            return {int(index): str(name) for index, name in raw_names.items()}
        if isinstance(raw_names, (list, tuple)):
            return {index: str(name) for index, name in enumerate(raw_names)}

        LOGGER.warning(
            "detector.class_names.unavailable path=%s -- class filtering disabled",
            self._weights_path,
        )
        return {}

    def _resolve_plate_class_ids(self) -> frozenset[int] | None:
        """Decide which class indices are kept by :meth:`detect`."""
        if not self._class_names:
            return None

        if len(self._class_names) == 1:
            only_index, only_name = next(iter(self._class_names.items()))
            if _canonical_class_name(only_name) not in PLATE_CLASS_ALIASES:
                LOGGER.info(
                    "detector.class_filter.single_class index=%d name=%s "
                    "-- treated as the plate class",
                    only_index,
                    only_name,
                )
            return None

        matched = frozenset(
            index
            for index, name in self._class_names.items()
            if _canonical_class_name(name) in PLATE_CLASS_ALIASES
        )
        if not matched:
            LOGGER.warning(
                "detector.class_filter.no_plate_class path=%s classes=%d -- "
                "this model has no license-plate class, detect() will always "
                "return an empty list",
                self._weights_path,
                len(self._class_names),
            )
        return matched

    # BaseDetector contract
    @property
    def name(self) -> str:
        """Return the identifier of the weights in use, e.g. ``"best"``."""
        return f"yolo:{self._weights_path.stem}{self._weights_path.suffix}"

    @property
    def class_names(self) -> dict[int, str]:
        """Return a copy of the model's ``{index: name}`` class map."""
        return dict(self._class_names)

    def detect(self, image: ImageArray) -> list[PlateDetection]:
        """Locate every license plate in an image."""
        self._validate_image(image)
        height, width = int(image.shape[0]), int(image.shape[1])

        started = time.perf_counter()
        try:
            try:
                import torch
                inference_ctx = torch.inference_mode()
            except Exception:
                from contextlib import nullcontext
                inference_ctx = nullcontext()

            with inference_ctx:
                predictions = self._model.predict(
                    source=image,
                    conf=self.config.conf_threshold,
                    iou=self.config.iou_threshold,
                    imgsz=self.config.imgsz,
                    device=self.config.device,
                    verbose=False,
                )
        except Exception as error:
            raise DetectionError(
                f"YOLO inference failed on a {width}x{height} image using "
                f"'{self._weights_path}' (device={self.config.device}): {error}"
            ) from error
        inference_seconds = time.perf_counter() - started

        detections = self._convert_predictions(predictions, width, height)
        detections.sort(key=lambda detection: detection.confidence, reverse=True)

        LOGGER.info(
            "detector.detect model=%s image=%dx%d boxes=%d conf_threshold=%.2f "
            "device=%s inference_seconds=%.3f",
            self.name,
            width,
            height,
            len(detections),
            self.config.conf_threshold,
            self.config.device,
            inference_seconds,
        )
        return detections

    def warmup(self) -> None:
        """Run one throwaway inference on a black image to prime the model."""
        blank = np.zeros((self.config.imgsz, self.config.imgsz, 3), dtype=np.uint8)
        started = time.perf_counter()
        self.detect(blank)
        LOGGER.info(
            "detector.warmup model=%s imgsz=%d seconds=%.3f",
            self.name,
            self.config.imgsz,
            time.perf_counter() - started,
        )

    # Internals
    @staticmethod
    def _validate_image(image: ImageArray) -> None:
        """Reject anything that is not a usable image before touching the model."""
        if image is None:
            raise InvalidImageError("Input image is None; nothing to detect.")
        if not isinstance(image, np.ndarray):
            raise InvalidImageError(
                "Input image must be a numpy.ndarray in OpenCV BGR format, got "
                f"{type(image).__name__}."
            )
        if image.size == 0:
            raise InvalidImageError(
                f"Input image is empty (shape={image.shape}); it was most likely "
                "produced by a failed decode."
            )
        if image.ndim not in (2, 3):
            raise InvalidImageError(
                "Input image must have 2 dimensions (grayscale) or 3 "
                f"(height, width, channels), got {image.ndim} (shape={image.shape})."
            )
        if image.ndim == 3 and image.shape[2] not in (1, 3, 4):
            raise InvalidImageError(
                "Input image must have 1, 3 or 4 channels, got "
                f"{image.shape[2]} (shape={image.shape})."
            )
        if image.shape[0] <= 0 or image.shape[1] <= 0:
            raise InvalidImageError(f"Input image has a zero-sized axis (shape={image.shape}).")

    def _convert_predictions(
        self, predictions: Any, width: int, height: int
    ) -> list[PlateDetection]:
        """Turn Ultralytics results into the project's own detection objects."""
        if predictions is None:
            return []
        try:
            result = predictions[0] if len(predictions) else None
        except TypeError as error:
            raise DetectionError(
                f"Unexpected YOLO output type {type(predictions).__name__}; "
                "expected a sequence of Results objects."
            ) from error
        if result is None:
            return []

        boxes = getattr(result, "boxes", None)
        if boxes is None or len(boxes) == 0:
            return []

        try:
            xyxy = _to_numpy(boxes.xyxy).reshape(-1, 4)
            confidences = _to_numpy(boxes.conf).reshape(-1)
            class_ids = _to_numpy(boxes.cls).reshape(-1).astype(int)
        except (AttributeError, ValueError) as error:
            raise DetectionError(
                f"Could not read boxes from the YOLO result: {error}. "
                "This usually means an incompatible ultralytics version."
            ) from error

        detections: list[PlateDetection] = []
        for corners, confidence, class_id in zip(xyxy, confidences, class_ids):
            if not self._is_plate_class(int(class_id)):
                continue
            bbox = self._build_clamped_bbox(corners, width, height)
            if bbox is None:
                continue
            detections.append(PlateDetection(bbox=bbox, confidence=float(confidence)))
        return detections

    def _is_plate_class(self, class_id: int) -> bool:
        """Return whether a predicted class index should be kept."""
        if self._plate_class_ids is None:
            return True
        return class_id in self._plate_class_ids

    @staticmethod
    def _build_clamped_bbox(corners: np.ndarray, width: int, height: int) -> BoundingBox | None:
        """Clamp a raw ``xyxy`` box to the image and convert it to a bounding box."""
        x1, y1, x2, y2 = (float(value) for value in corners[:4])
        if x2 < x1:
            x1, x2 = x2, x1
        if y2 < y1:
            y1, y2 = y2, y1

        left = min(max(x1, 0.0), float(width))
        top = min(max(y1, 0.0), float(height))
        right = min(max(x2, 0.0), float(width))
        bottom = min(max(y2, 0.0), float(height))

        try:
            return BoundingBox.from_xyxy(left, top, right, bottom)
        except ValueError:
            LOGGER.warning(
                "detector.box.degenerate raw=(%.1f,%.1f,%.1f,%.1f) "
                "clamped=(%.1f,%.1f,%.1f,%.1f) image=%dx%d -- skipped",
                x1,
                y1,
                x2,
                y2,
                left,
                top,
                right,
                bottom,
                width,
                height,
            )
            return None
