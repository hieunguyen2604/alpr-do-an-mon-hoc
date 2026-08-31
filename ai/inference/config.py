"""Centralised configuration dataclass for the ALPR inference package (NFR-M4)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

__all__ = ["PROJECT_ROOT", "DEFAULT_ENV_PREFIX", "InferenceConfig"]

PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]
"""Repository root, resolved from this file (``<root>/ai/inference/config.py``).

Deriving the root this way keeps the package relocatable: moving or renaming
the checkout does not break anything, and no absolute path is hard-coded.
"""

DEFAULT_ENV_PREFIX: str = "ALPR_"
"""Prefix for all environment variables read by :meth:`InferenceConfig.from_env`."""

_DEFAULT_MODEL_RELATIVE_PATH = Path("models") / "best.pt"
_TRUE_VALUES = frozenset({"1", "true", "yes", "on"})
_FALSE_VALUES = frozenset({"0", "false", "no", "off"})


def _read_str(prefix: str, key: str, default: str) -> str:
    """Read a string environment variable.

    Args:
        prefix: Environment-variable prefix, e.g. ``"ALPR_"``.
        key: Variable name without the prefix.
        default: Value returned when the variable is unset or empty.

    Returns:
        The configured value, stripped of surrounding whitespace.
    """
    raw = os.environ.get(f"{prefix}{key}", "").strip()
    return raw if raw else default


def _read_float(prefix: str, key: str, default: float) -> float:
    """Read a floating-point environment variable.

    Args:
        prefix: Environment-variable prefix.
        key: Variable name without the prefix.
        default: Value returned when the variable is unset or empty.

    Returns:
        The parsed value.

    Raises:
        ValueError: If the variable is set but is not a valid number. Failing
            loudly is intentional -- silently falling back to a default would
            hide a typo in a deployment configuration.
    """
    raw = os.environ.get(f"{prefix}{key}", "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError as error:
        raise ValueError(
            f"Environment variable {prefix}{key}={raw!r} is not a valid number"
        ) from error


def _read_int(prefix: str, key: str, default: int) -> int:
    """Read an integer environment variable.

    Args:
        prefix: Environment-variable prefix.
        key: Variable name without the prefix.
        default: Value returned when the variable is unset or empty.

    Returns:
        The parsed value.

    Raises:
        ValueError: If the variable is set but is not a valid integer.
    """
    raw = os.environ.get(f"{prefix}{key}", "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError as error:
        raise ValueError(
            f"Environment variable {prefix}{key}={raw!r} is not a valid integer"
        ) from error


def _read_bool(prefix: str, key: str, default: bool) -> bool:
    """Read a boolean environment variable.

    Accepts ``1/true/yes/on`` and ``0/false/no/off``, case-insensitively.

    Args:
        prefix: Environment-variable prefix.
        key: Variable name without the prefix.
        default: Value returned when the variable is unset or empty.

    Returns:
        The parsed value.

    Raises:
        ValueError: If the variable is set to an unrecognised value.
    """
    raw = os.environ.get(f"{prefix}{key}", "").strip().lower()
    if not raw:
        return default
    if raw in _TRUE_VALUES:
        return True
    if raw in _FALSE_VALUES:
        return False
    raise ValueError(
        f"Environment variable {prefix}{key}={raw!r} is not a valid boolean; "
        "use one of 1/0, true/false, yes/no, on/off"
    )


def _read_path(prefix: str, key: str, default: Path) -> Path:
    """Read a filesystem path from an environment variable.

    A relative value is resolved against :data:`PROJECT_ROOT` so that the same
    setting behaves identically no matter which directory the process was
    started from.

    Args:
        prefix: Environment-variable prefix.
        key: Variable name without the prefix.
        default: Value returned when the variable is unset or empty.

    Returns:
        An absolute path.
    """
    raw = os.environ.get(f"{prefix}{key}", "").strip()
    if not raw:
        return default
    candidate = Path(raw).expanduser()
    if not candidate.is_absolute():
        candidate = PROJECT_ROOT / candidate
    return candidate


def _read_optional_path(prefix: str, key: str) -> Path | None:
    """Read a path that has no default: unset or empty simply means ``None``.

    Unlike :func:`_read_path` there is no fallback value to return, because
    the setting is a pure opt-in (a fine-tuned model directory). Resolution
    of a relative value against :data:`PROJECT_ROOT` matches ``__post_init__``.

    Args:
        prefix: Environment-variable prefix.
        key: Variable name without the prefix.

    Returns:
        An absolute path, or ``None`` when the variable is unset or empty.
    """
    raw = os.environ.get(f"{prefix}{key}", "").strip()
    if not raw:
        return None
    candidate = Path(raw).expanduser()
    if not candidate.is_absolute():
        candidate = PROJECT_ROOT / candidate
    return candidate


@dataclass(slots=True)
class InferenceConfig:
    """Runtime settings for the detection and recognition stages.

    An instance is built once at start-up and injected into the detector, the
    recognizer and the pipeline. Components receive their configuration rather
    than reading the environment themselves, which keeps them testable: a unit
    test just constructs a config with the values it needs.

    Attributes:
        model_path: Path to the trained detector weights. Defaults to
            ``<project root>/models/best.pt``.
        device: Torch device string, ``"cpu"`` or ``"cuda"``. Defaults to
            ``"cpu"``: the target machine has no CUDA GPU, and inference is
            expected to run on CPU (decision AD-06).
        conf_threshold: Minimum detector confidence for a box to be kept, in
            ``[0.0, 1.0]``. Lower values find more plates but add false
            positives.
        iou_threshold: IoU threshold for non-maximum suppression, in
            ``[0.0, 1.0]``. Controls how aggressively overlapping boxes for the
            same plate are merged.
        imgsz: Square input size, in pixels, that images are resized to before
            detection. Must be a positive multiple of 32, as required by the
            YOLO architecture.
        ocr_lang: Language code passed to the OCR engine. Vietnamese plates
            carry only Latin letters and digits, so the English model is both
            correct and faster than a multilingual one.
        ocr_use_gpu: Whether the OCR engine may use a GPU. Defaults to
            ``False`` for the same reason as :attr:`device`.
        ocr_rec_model_dir: Directory holding a FINE-TUNED recognition
            inference model (exported by the Colab notebook in
            ``ai/training``). ``None`` — the default — uses the stock
            ``en_PP-OCRv5_mobile_rec`` weights. When set, the directory must
            exist: a mistyped path failing at start-up beats a container that
            silently recognises with the wrong model.
        ocr_skip_detection: Whether to feed the whole prepared crop straight to
            the recognition model instead of running PaddleOCR's text-DETECTION
            stage first. **Off by default** -- see the second table below, which
            is the reason.

            On the 2,801-plate label corpus, skipping detection looks like a
            large win (``docs/reports/29-reconly-ablation.json``):

            ======================== ============ ============ ==========
            Configuration            NFR-A5       NFR-A6       ms / crop
            ======================== ============ ============ ==========
            stock, det + rec         0.6373       0.7512       328.8
            stock, rec only          0.6776       0.7508        35.7
            fine-tuned, det + rec    0.5998       0.6762           --
            fine-tuned, rec only     0.8618       0.8758        38.5
            ======================== ============ ============ ==========

            **That corpus cannot settle the question, because every image in it
            is a pre-cropped Roboflow export.** A crop that is already tight
            around the plate gives a text detector nothing to do. The crops the
            deployed system actually recognises come from YOLO, on full scenes,
            and they are looser -- they carry bumper, windscreen and background.

            Re-measured on the demo set, the only material in this project that
            runs whole scenes through the real detector
            (``docs/reports/31-demo-ab-reconly.json``, 22 plates):

            ======================== ==========
            Configuration            plates read
            ======================== ==========
            stock, det + rec         **17 / 22**
            stock, rec only          13 / 22
            fine-tuned, det + rec    14 / 22
            fine-tuned, rec only     15 / 22
            ======================== ==========

            The ordering reverses. On loose detector crops the detection stage
            earns its 290 ms: it re-localises the text inside the crop, and
            without it the recogniser reads the surrounding clutter as
            characters (``TCA7A22104``, ``5KB274184`` on ``nhieu-bien-2.png``).

            Note what survives both tables: rec-only helps the **fine-tuned**
            model (+1 plate on demo, +12.46 points on corpus) and hurts the
            **stock** one (-4 plates on demo). A model fine-tuned on whole-plate
            images has never seen a fragment. That is a real effect, and it is
            why this switch exists rather than being deleted -- but 22 plates is
            too small a sample to change what ships.

            Set ``ALPR_OCR_SKIP_DETECTION=1`` to enable it for ablation. Turning
            it on for production needs a scene-level corpus with plate-string
            labels, which this project does not have (see NFR-A7's validity
            note in ``docs/reports/27-ocr-accuracy-with-ladder.json``).
        two_line_aspect_ratio_threshold: Width/height ratio below which a plate
            crop is treated as a two-line plate. Vietnamese single-line plates
            are much wider than tall; two-line plates are nearly square. A crop
            with a ratio under this value is split into two lines before OCR.
        rectify_enabled: Whether the failure-retry ladder
            (:func:`~ai.inference.pipeline.retry_skewed_variants`) may re-read
            a crop whose first read failed validation, through a deskewed
            and/or vertically-stretched variant. On by default: the ladder
            runs only after a failure and keeps a result only when it
            validates, so it can recover reads but never lose one. The switch
            exists so Phase 7 can ablate it and attribute its contribution.
        sr_retry_enabled: Whether the same ladder may additionally try
            super-resolved variants of a SMALL failed crop
            (:mod:`ai.inference.superres`). Independent of
            ``rectify_enabled`` so each contribution can be ablated on its
            own. Harmless when the environment lacks ``cv2.dnn_superres`` --
            the variant is simply skipped.

            **Off by default since 28/07/2026, on measurement.** The ablation
            in ``docs/reports/27-retry-ladder-cost-benefit.md`` put its price
            at +319 ms on p95 latency and +1381 ms on p99, against a
            contribution of exactly zero plates on the 2801-sample labelled
            corpus -- and zero there is structural, not empirical: every
            corpus crop is at least 565 px on its long side while the SR gate
            only opens below :data:`~ai.inference.pipeline.RETRY_SR_MAX_SIDE`
            (200 px), so the corpus cannot exercise this rung at all. The only
            evidence for it remains one hand-picked demo crop out of four
            tried (report 24). An unquantified benefit cannot justify pushing
            a Must-level requirement (NFR-P1) past its floor, so the rung
            ships off, with the code, the tests and this switch intact:
            ``ALPR_SR_RETRY_ENABLED=true`` restores it. Measuring it honestly
            needs a labelled set of small, detector-produced crops, which the
            project does not have.

    Raises:
        ValueError: If any value is outside its valid range.
    """

    model_path: Path = field(default_factory=lambda: PROJECT_ROOT / _DEFAULT_MODEL_RELATIVE_PATH)
    device: str = "cpu"
    conf_threshold: float = 0.25
    iou_threshold: float = 0.45
    imgsz: int = 640
    ocr_lang: str = "en"
    ocr_use_gpu: bool = False
    ocr_rec_model_dir: Path | None = None
    ocr_skip_detection: bool = False
    two_line_aspect_ratio_threshold: float = 2.5
    rectify_enabled: bool = True
    sr_retry_enabled: bool = False

    def __post_init__(self) -> None:
        """Normalise the model path and validate every field.

        Configuration errors are caught here, at start-up, instead of surfacing
        later as a confusing failure in the middle of inference.

        Raises:
            ValueError: If any value is outside its valid range.
        """
        self.model_path = Path(self.model_path).expanduser()
        if not self.model_path.is_absolute():
            self.model_path = PROJECT_ROOT / self.model_path

        if not 0.0 <= self.conf_threshold <= 1.0:
            raise ValueError(f"conf_threshold must be within [0.0, 1.0], got {self.conf_threshold}")
        if not 0.0 <= self.iou_threshold <= 1.0:
            raise ValueError(f"iou_threshold must be within [0.0, 1.0], got {self.iou_threshold}")
        if self.imgsz <= 0 or self.imgsz % 32 != 0:
            raise ValueError(f"imgsz must be a positive multiple of 32, got {self.imgsz}")
        if self.two_line_aspect_ratio_threshold <= 0.0:
            raise ValueError(
                "two_line_aspect_ratio_threshold must be positive, got "
                f"{self.two_line_aspect_ratio_threshold}"
            )
        if not self.device:
            raise ValueError("device must be a non-empty string, e.g. 'cpu' or 'cuda'")
        if not self.ocr_lang:
            raise ValueError("ocr_lang must be a non-empty string, e.g. 'en'")

        if self.ocr_rec_model_dir is not None:
            self.ocr_rec_model_dir = Path(self.ocr_rec_model_dir).expanduser()
            if not self.ocr_rec_model_dir.is_absolute():
                self.ocr_rec_model_dir = PROJECT_ROOT / self.ocr_rec_model_dir
            if not self.ocr_rec_model_dir.is_dir():
                raise ValueError(
                    "ocr_rec_model_dir does not exist or is not a directory: "
                    f"{self.ocr_rec_model_dir}"
                )

    @classmethod
    def from_env(cls, prefix: str = DEFAULT_ENV_PREFIX) -> InferenceConfig:
        """Build a configuration from environment variables.

        Any variable that is unset or empty falls back to the field default, so
        the pipeline runs with no environment configured at all. Variables read
        (with the default ``ALPR_`` prefix):

        =================================== ==============================
        Variable                            Field
        =================================== ==============================
        ``ALPR_MODEL_PATH``                 :attr:`model_path`
        ``ALPR_DEVICE``                     :attr:`device`
        ``ALPR_CONF_THRESHOLD``             :attr:`conf_threshold`
        ``ALPR_IOU_THRESHOLD``              :attr:`iou_threshold`
        ``ALPR_IMGSZ``                      :attr:`imgsz`
        ``ALPR_OCR_LANG``                   :attr:`ocr_lang`
        ``ALPR_OCR_USE_GPU``                :attr:`ocr_use_gpu`
        ``ALPR_OCR_REC_MODEL_DIR``          :attr:`ocr_rec_model_dir`
        ``ALPR_OCR_SKIP_DETECTION``         :attr:`ocr_skip_detection`
        ``ALPR_TWO_LINE_ASPECT_RATIO``      :attr:`two_line_aspect_ratio_threshold`
        ``ALPR_RECTIFY_ENABLED``            :attr:`rectify_enabled`
        ``ALPR_SR_RETRY_ENABLED``           :attr:`sr_retry_enabled`
        =================================== ==============================

        A relative ``ALPR_MODEL_PATH`` is resolved against the project root,
        not the current working directory.

        Args:
            prefix: Prefix shared by all variable names. Override it to run two
                configurations side by side, for example in tests.

        Returns:
            A validated configuration instance.

        Raises:
            ValueError: If a variable is set to an unparsable or out-of-range
                value.
        """
        defaults = cls()
        return cls(
            model_path=_read_path(prefix, "MODEL_PATH", defaults.model_path),
            device=_read_str(prefix, "DEVICE", defaults.device),
            conf_threshold=_read_float(prefix, "CONF_THRESHOLD", defaults.conf_threshold),
            iou_threshold=_read_float(prefix, "IOU_THRESHOLD", defaults.iou_threshold),
            imgsz=_read_int(prefix, "IMGSZ", defaults.imgsz),
            ocr_lang=_read_str(prefix, "OCR_LANG", defaults.ocr_lang),
            ocr_use_gpu=_read_bool(prefix, "OCR_USE_GPU", defaults.ocr_use_gpu),
            ocr_rec_model_dir=_read_optional_path(prefix, "OCR_REC_MODEL_DIR"),
            ocr_skip_detection=_read_bool(
                prefix, "OCR_SKIP_DETECTION", defaults.ocr_skip_detection
            ),
            two_line_aspect_ratio_threshold=_read_float(
                prefix,
                "TWO_LINE_ASPECT_RATIO",
                defaults.two_line_aspect_ratio_threshold,
            ),
            rectify_enabled=_read_bool(prefix, "RECTIFY_ENABLED", defaults.rectify_enabled),
            sr_retry_enabled=_read_bool(prefix, "SR_RETRY_ENABLED", defaults.sr_retry_enabled),
        )
