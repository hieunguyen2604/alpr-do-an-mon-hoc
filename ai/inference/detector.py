"""YOLO11-based license plate detector.

This module provides the only concrete :class:`~ai.inference.interfaces.BaseDetector`
of the project: :class:`YoloPlateDetector`, a thin adapter over Ultralytics YOLO.

The adapter exists so that Ultralytics stays an *implementation detail*. Nothing
outside this module handles an Ultralytics ``Results`` object, a torch tensor or
a class index: the boundary converts everything into the project's own
:class:`~ai.inference.types.PlateDetection` / :class:`~ai.inference.types.BoundingBox`
value objects. Replacing YOLO11 with another architecture therefore means adding
one file, not editing the pipeline.

Design notes:

* **Ultralytics is imported lazily**, inside :func:`_load_yolo_model`. That keeps
  ``import ai.inference.detector`` cheap and lets the unit tests exercise the
  conversion logic without the (heavy) ML runtime installed.
* **Both ``.pt`` and ``.onnx`` weights are supported** -- Ultralytics loads both
  through the same ``YOLO`` entry point, which is what makes the CPU-oriented
  ONNX export of ``ai.training.export`` usable at inference time with no code
  change.
* **Finding no plate is never an error.** An image with no plate yields an empty
  list; only a genuine failure of the runtime raises
  :class:`~ai.inference.exceptions.DetectionError`.

Architectural constraint (NFR-M1): this module imports NumPy, the standard
library and Ultralytics only -- never the web framework (FastAPI) or its schema
library (Pydantic).
"""

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
    """Normalise a model class name for alias comparison.

    Args:
        name: Raw class name as stored in the weights, e.g. ``"License-Plate"``.

    Returns:
        The lower-cased name with spaces and hyphens folded to underscores.
    """
    return name.strip().lower().replace("-", "_").replace(" ", "_")


def _is_openvino_model_dir(path: Path) -> bool:
    """Return whether a directory holds an OpenVINO IR model.

    Ultralytics exports OpenVINO as a directory containing a ``.xml`` topology
    file next to its ``.bin`` weights, unlike every other supported format which
    is a single file. Detecting it by content rather than by directory name
    keeps the check working if the directory is renamed.

    Args:
        path: Directory to inspect.

    Returns:
        ``True`` when the directory contains at least one ``.xml`` file.
    """
    try:
        return any(path.glob("*.xml"))
    except OSError:  # pragma: no cover - unreadable directory
        return False


def _to_numpy(value: Any) -> np.ndarray:
    """Convert a torch tensor -- or anything array-like -- to a NumPy array.

    Ultralytics returns torch tensors that may live on a GPU. Going through this
    helper avoids importing torch here just to call ``.cpu()``, and lets tests
    feed plain NumPy arrays or lists in place of tensors.

    Args:
        value: A torch tensor, NumPy array or sequence of numbers.

    Returns:
        A NumPy view or copy of the input.
    """
    cpu = getattr(value, "cpu", None)
    if callable(cpu):
        value = cpu()
    numpy_method = getattr(value, "numpy", None)
    if callable(numpy_method):
        return np.asarray(numpy_method())
    return np.asarray(value)


def _load_yolo_model(weights_path: Path, task: str = "detect") -> Any:
    """Load Ultralytics YOLO weights from disk.

    Ultralytics is imported here rather than at module level so that this module
    can be imported -- and unit-tested -- without the ML runtime present.

    Args:
        weights_path: Absolute path to a ``.pt`` or ``.onnx`` weights file.
        task: Ultralytics task name. Required for ``.onnx`` weights, which do not
            always carry their task in the file metadata.

    Returns:
        The loaded ``ultralytics.YOLO`` instance.

    Raises:
        ModelLoadError: If Ultralytics is not installed, or the file exists but
            cannot be loaded.
    """
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
    """Locate Vietnamese license plates with an Ultralytics YOLO11 model.

    The model is loaded eagerly in the constructor: a missing or broken weights
    file must fail at start-up, with a message naming the path that was tried,
    rather than at the first user request.

    Example:
        Detect plates in an image already decoded by OpenCV::

            config = InferenceConfig.from_env()
            detector = YoloPlateDetector(config)
            detector.warmup()
            plates = detector.detect(cv2.imread("car.jpg"))

    Attributes:
        config: The configuration this detector was built with. Thresholds are
            read from it on every call, so tuning at runtime takes effect
            immediately.

    Args:
        config: Runtime settings. :attr:`~ai.inference.config.InferenceConfig.model_path`
            selects the weights, and ``conf_threshold`` / ``iou_threshold`` /
            ``imgsz`` / ``device`` are forwarded to every inference call.
        model_loader: Injection point for the weights loader, used by the tests
            to avoid a real Ultralytics dependency. Production code leaves it at
            its default.

    Raises:
        ModelLoadError: If the weights file does not exist, or exists but cannot
            be loaded.
    """

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

    # ----------------------------------------------------------------- #
    # Construction helpers
    # ----------------------------------------------------------------- #
    def _verify_weights_exist(self) -> None:
        """Check that the configured weights path points at loadable weights.

        Accepts either a weights *file* (``.pt``, ``.onnx``, ``.torchscript``) or
        an OpenVINO model *directory* -- OpenVINO is the one supported format
        that is a directory rather than a single file, and it is the fastest
        detector backend measured on this project's Intel CPU (Phase 7), so
        rejecting directories outright would make the winning configuration
        unreachable through ``ALPR_MODEL_PATH``.

        Raises:
            ModelLoadError: If the path is missing, or is a directory that does
                not look like an OpenVINO model. The message names the exact
                path tried and how to produce the file, because "model not
                found" is the single most likely failure a first-time user of
                this project will hit.
        """
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
        """Read the ``{index: name}`` class map from the loaded model.

        Returns:
            The class map, or an empty dict when the model does not expose one
            (some exported formats do not). An empty map disables class
            filtering, which is the safe default: dropping every box because the
            metadata is missing would be a silent failure.
        """
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
        """Decide which class indices are kept by :meth:`detect`.

        Three cases, in order:

        1. The model exposes no class map -> keep everything (``None``).
        2. The model is single-class (the project's own detector) -> keep
           everything; its one class *is* the plate whatever it is called.
        3. The model is multi-class -> keep only classes whose name matches
           :data:`PLATE_CLASS_ALIASES`. A multi-class model with no such class,
           for instance the 80-class COCO checkpoint, keeps nothing and always
           returns an empty detection list. That is correct behaviour, not a bug.

        Returns:
            The set of class indices to keep, or ``None`` meaning "keep all".
        """
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

    # ----------------------------------------------------------------- #
    # BaseDetector contract
    # ----------------------------------------------------------------- #
    @property
    def name(self) -> str:
        """Return the identifier of the weights in use, e.g. ``"best"``.

        The stem of the weights file is used because that is what distinguishes
        one trained run from another in the benchmark reports; the ``yolo``
        prefix marks the architecture family.
        """
        return f"yolo:{self._weights_path.stem}{self._weights_path.suffix}"

    @property
    def class_names(self) -> dict[int, str]:
        """Return a copy of the model's ``{index: name}`` class map."""
        return dict(self._class_names)

    def detect(self, image: ImageArray) -> list[PlateDetection]:
        """Locate every license plate in an image.

        Args:
            image: Source image as a BGR ``uint8`` array of shape
                ``(height, width, 3)`` -- what ``cv2.imread`` returns.

        Returns:
            One :class:`~ai.inference.types.PlateDetection` per plate found,
            already filtered by the configured confidence threshold and by
            non-maximum suppression, sorted by descending confidence. Every box
            is clamped to the image bounds, so each one can be used directly to
            crop. An empty list means no plate was found -- a normal outcome.

        Raises:
            InvalidImageError: If the array is not a usable image.
            DetectionError: If inference itself fails.
        """
        self._validate_image(image)
        height, width = int(image.shape[0]), int(image.shape[1])

        started = time.perf_counter()
        try:
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
        """Run one throwaway inference on a black image to prime the model.

        The first inference of a process pays for paging weights in and building
        lazy kernels. Doing that here keeps the cost out of the first real
        request and out of the latency measurements (NFR-P1).

        Raises:
            DetectionError: If the warm-up inference fails, which means the model
                is unusable and it is better to learn that at start-up.
        """
        blank = np.zeros((self.config.imgsz, self.config.imgsz, 3), dtype=np.uint8)
        started = time.perf_counter()
        self.detect(blank)
        LOGGER.info(
            "detector.warmup model=%s imgsz=%d seconds=%.3f",
            self.name,
            self.config.imgsz,
            time.perf_counter() - started,
        )

    # ----------------------------------------------------------------- #
    # Internals
    # ----------------------------------------------------------------- #
    @staticmethod
    def _validate_image(image: ImageArray) -> None:
        """Reject anything that is not a usable image before touching the model.

        Args:
            image: The candidate input.

        Raises:
            InvalidImageError: If the input is ``None``, not a NumPy array, has
                the wrong dimensionality, has a zero-sized axis, or has an
                unusual channel count.
        """
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
        """Turn Ultralytics results into the project's own detection objects.

        Args:
            predictions: What ``YOLO.predict`` returned -- a sequence of
                ``Results``, one per input image. Only the first is used, since
                this detector is fed a single image at a time.
            width: Source image width, used to clamp boxes.
            height: Source image height, used to clamp boxes.

        Returns:
            The converted detections, unsorted.

        Raises:
            DetectionError: If the results have a shape this adapter cannot read,
                which would mean an incompatible Ultralytics version.
        """
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
        """Return whether a predicted class index should be kept.

        Args:
            class_id: Class index predicted by the model.

        Returns:
            ``True`` when the class is a license-plate class, or when class
            filtering is disabled (single-class or metadata-less model).
        """
        if self._plate_class_ids is None:
            return True
        return class_id in self._plate_class_ids

    @staticmethod
    def _build_clamped_bbox(corners: np.ndarray, width: int, height: int) -> BoundingBox | None:
        """Clamp a raw ``xyxy`` box to the image and convert it to a bounding box.

        YOLO can emit boxes that stick out past the image border by a pixel or
        two. Clamping here -- rather than in the caller -- is what lets the
        contract promise that every returned box is directly usable for cropping.

        Args:
            corners: A 4-element ``(x1, y1, x2, y2)`` array in pixel units.
            width: Source image width.
            height: Source image height.

        Returns:
            The clamped bounding box, or ``None`` if the box collapsed to zero
            area once clamped and rounded -- a degenerate prediction that is
            logged and skipped rather than raised, so one bad box cannot lose an
            otherwise good frame.
        """
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
