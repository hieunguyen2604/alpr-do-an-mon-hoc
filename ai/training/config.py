"""Hyper-parameter configuration for YOLO11 license-plate detector training.

Everything that can be tuned lives in :class:`TrainingConfig`. Scripts never
hard-code a hyper-parameter or a filesystem path: they load a YAML file from
``ai/training/configs/`` and, at most, override a couple of fields from the
command line. That is what makes a training run reproducible and what lets the
same config file drive a slow CPU run on the Windows development machine and a
fast GPU run on Colab.

Two domain rules are enforced here rather than left to convention:

* ``fliplr`` **must** be ``0.0``. Horizontal flipping mirrors the glyphs on the
  plate, which destroys the very signal the downstream OCR stage depends on.
* ``seed`` defaults to ``42`` and ``deterministic`` to ``True`` so that a run
  quoted in the thesis can actually be reproduced.
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Any, Final

import yaml

__all__ = [
    "PROJECT_ROOT",
    "CONFIGS_DIR",
    "DEFAULT_DATA_YAML",
    "DEFAULT_RUNS_DIR",
    "SUPPORTED_MODEL_VARIANTS",
    "TrainingConfig",
]

LOGGER = logging.getLogger(__name__)

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
"""Repository root, derived from ``<root>/ai/training/config.py``.

Resolved from this file's own location so that the checkout can be moved,
renamed, or cloned into ``/content`` on Colab without breaking any path.
"""

CONFIGS_DIR: Final[Path] = Path(__file__).resolve().parent / "configs"
"""Directory holding the shipped YAML configurations."""

DEFAULT_DATA_YAML: Final[Path] = PROJECT_ROOT / "datasets" / "processed" / "data.yaml"
"""Default Ultralytics dataset descriptor produced by the Phase 2 pipeline."""

DEFAULT_RUNS_DIR: Final[Path] = PROJECT_ROOT / "runs"
"""Default parent directory for training runs (git-ignored)."""

DEFAULT_MODELS_DIR: Final[Path] = PROJECT_ROOT / "models"
"""Directory where the promoted ``best.pt`` is published."""

SUPPORTED_MODEL_VARIANTS: Final[tuple[str, ...]] = (
    "yolo11n",
    "yolo11s",
    "yolo11m",
    "yolo11l",
    "yolo11x",
)
"""Model variants accepted by :class:`TrainingConfig`.

Phase 1 selected **yolo11n** as the primary variant (CPU-friendly) and
**yolo11s** as the escalation option if nano does not reach the mAP target.
The larger variants are listed so that an experiment is not blocked by
validation, but they are out of scope for the CPU deployment target.
"""

SUPPORTED_OPTIMIZERS: Final[tuple[str, ...]] = (
    "SGD",
    "Adam",
    "AdamW",
    "NAdam",
    "RAdam",
    "RMSProp",
    "auto",
)
"""Optimizer names understood by Ultralytics ``model.train()``."""

_ZERO_TO_ONE_FIELDS: Final[tuple[str, ...]] = (
    "lrf",
    "momentum",
    "hsv_h",
    "hsv_s",
    "hsv_v",
    "translate",
    "flipud",
    "fliplr",
    "mosaic",
    "mixup",
    "copy_paste",
    "erasing",
    "fraction",
)
"""Fields whose valid range is ``[0.0, 1.0]``."""

_NON_NEGATIVE_FIELDS: Final[tuple[str, ...]] = (
    "weight_decay",
    "warmup_epochs",
    "warmup_momentum",
    "warmup_bias_lr",
    "box",
    "cls",
    "dfl",
    "degrees",
    "scale",
    "shear",
    "perspective",
)
"""Fields that must not be negative."""

# Keys that describe *what* to train rather than *how*, and therefore must not
# be forwarded verbatim to Ultralytics ``model.train()``.
_NON_ULTRALYTICS_FIELDS: Final[frozenset[str]] = frozenset(
    {"model_variant", "pretrained_weights", "description"}
)


def _resolve_under_root(value: str | Path) -> Path:
    """Resolve a possibly relative path against the repository root.

    Relative paths are interpreted relative to :data:`PROJECT_ROOT`, never to
    the current working directory, so a config behaves identically no matter
    where the process was launched from.

    Args:
        value: Absolute or relative path, as a string or :class:`~pathlib.Path`.

    Returns:
        An absolute path.
    """
    candidate = Path(value).expanduser()
    if not candidate.is_absolute():
        candidate = PROJECT_ROOT / candidate
    return candidate


@dataclass(slots=True)
class TrainingConfig:
    """Complete hyper-parameter set for one YOLO11 detector training run.

    Field groups, in the order they appear below: model selection, data, core
    schedule, optimiser, loss weights, augmentation, runtime/bookkeeping.

    Attributes:
        model_variant: YOLO11 size to train, one of
            :data:`SUPPORTED_MODEL_VARIANTS`. Phase 1 selected ``"yolo11n"``.
        pretrained_weights: Checkpoint to initialise from. ``"yolo11n.pt"``
            fine-tunes from the COCO-pretrained weights (downloaded on first
            use); an empty string trains from a randomly initialised backbone.
            Fine-tuning is strongly preferred on a ~37k-image dataset.
        description: Free-text note describing the intent of this configuration.
            Carried through YAML round-trips so a run's provenance survives.
        data: Path to the Ultralytics dataset descriptor (``data.yaml``).
            Relative values resolve against the repository root.
        imgsz: Square training resolution in pixels; must be a positive multiple
            of 32. 640 is the Phase 1 baseline: plates are small objects, so
            reducing this hurts recall more than it saves time.
        epochs: Maximum number of epochs.
        batch: Images per batch. A negative value (``-1``) asks Ultralytics to
            auto-size the batch to ~60% of available VRAM -- useful on Colab,
            where the assigned GPU varies between sessions.
        patience: Early-stopping patience in epochs with no fitness improvement.
        optimizer: Optimiser name, one of :data:`SUPPORTED_OPTIMIZERS`.
        lr0: Initial learning rate.
        lrf: Final learning-rate factor; the schedule ends at ``lr0 * lrf``.
        momentum: SGD momentum, or beta1 for the Adam family.
        weight_decay: L2 regularisation coefficient.
        warmup_epochs: Length of the linear learning-rate warm-up.
        warmup_momentum: Momentum at the start of warm-up.
        warmup_bias_lr: Bias-parameter learning rate during warm-up.
        box: Weight of the bounding-box regression loss. Raised above the
            Ultralytics default for this project: localisation quality directly
            determines crop quality, and a sloppy crop breaks OCR.
        cls: Weight of the classification loss. Kept low -- the detector has
            very few classes, so classification is the easy part.
        dfl: Weight of the distribution-focal loss.
        hsv_h: Hue jitter fraction. Kept small: Vietnamese plate background
            colour is semantically meaningful (white/yellow/blue/red encode the
            vehicle category), so hue must not be scrambled.
        hsv_s: Saturation jitter fraction.
        hsv_v: Brightness jitter fraction. Generous, to cover night captures,
            headlight glare and backlit plates.
        degrees: Maximum rotation in degrees. Small on purpose: real plates are
            near-horizontal, and large rotations teach the model poses that do
            not occur.
        translate: Maximum translation as a fraction of image size.
        scale: Scale jitter gain.
        shear: Maximum shear in degrees.
        perspective: Perspective-warp gain; simulates off-axis camera angles,
            which are extremely common in real gate/parking footage.
        flipud: Vertical-flip probability. **Must be 0.0** -- an upside-down
            plate is not a real-world input.
        fliplr: Horizontal-flip probability. **Must be 0.0.** Mirroring the
            image mirrors the glyphs; the detector would learn mirror-image
            plates that never occur, and any downstream OCR training reusing
            this augmentation policy would be actively harmed.
        copy_paste: Copy-paste augmentation probability (segmentation-oriented;
            0.0 for pure detection).
        erasing: Random-erasing probability, for partially occluded plates.
        mosaic: Mosaic augmentation probability. Very effective for small
            objects such as plates.
        close_mosaic: Number of final epochs with mosaic disabled, so the model
            finishes on undistorted images.
        mixup: MixUp probability. Left at 0.0: blending two plates produces
            unreadable text and no useful detection signal.
        device: ``"auto"`` (resolved at runtime by
            :func:`ai.training.train.resolve_device`), ``"cpu"``, ``"0"``,
            ``"0,1"``, or ``"mps"``.
        workers: Dataloader worker processes. On Windows, keep this modest;
            each worker re-imports the module.
        project: Parent directory for run folders.
        name: Run folder name inside :attr:`project`.
        exist_ok: Allow reusing an existing run directory instead of creating
            ``name2``, ``name3``, ...
        seed: Random seed. 42 by default so results are reproducible.
        deterministic: Force deterministic kernels. Slightly slower, but a
            thesis number that cannot be reproduced is not worth much.
        save_period: Save a numbered checkpoint every N epochs. **Positive by
            default on purpose**: Colab disconnects mid-session regularly, and
            a run with only ``last.pt`` can lose hours of GPU time.
        val: Run validation each epoch.
        plots: Emit training curves, PR curves and the confusion matrix.
        cache: Image caching strategy: ``False``, ``"ram"`` or ``"disk"``.
        amp: Automatic mixed precision. Ignored on CPU.
        rect: Rectangular batching (disabled by default; incompatible with
            shuffling benefits during training).
        cos_lr: Use a cosine learning-rate schedule instead of linear.
        single_cls: Treat every annotated object as one class. Useful when
            merging datasets whose class taxonomies disagree.
        fraction: Fraction of the training set to use. Lower it for a quick
            smoke test without editing the dataset.
        verbose: Verbose Ultralytics logging.

    Raises:
        ValueError: If any field is out of range or if ``fliplr``/``flipud`` is
            non-zero.
    """

    # --- Model selection -----------------------------------------------------
    model_variant: str = "yolo11n"
    pretrained_weights: str = "yolo11n.pt"
    description: str = ""

    # --- Data ----------------------------------------------------------------
    data: Path = field(default_factory=lambda: DEFAULT_DATA_YAML)

    # --- Core schedule -------------------------------------------------------
    imgsz: int = 640
    epochs: int = 100
    batch: int = 16
    patience: int = 20

    # --- Optimiser -----------------------------------------------------------
    optimizer: str = "AdamW"
    lr0: float = 0.001
    lrf: float = 0.01
    momentum: float = 0.937
    weight_decay: float = 0.0005
    warmup_epochs: float = 3.0
    warmup_momentum: float = 0.8
    warmup_bias_lr: float = 0.1
    cos_lr: bool = False

    # --- Loss weights --------------------------------------------------------
    box: float = 7.5
    cls: float = 0.5
    dfl: float = 1.5

    # --- Augmentation --------------------------------------------------------
    hsv_h: float = 0.015
    hsv_s: float = 0.7
    hsv_v: float = 0.4
    degrees: float = 5.0
    translate: float = 0.1
    scale: float = 0.5
    shear: float = 2.0
    perspective: float = 0.0005
    flipud: float = 0.0
    # SAFETY-CRITICAL: horizontal flip mirrors the characters printed on the
    # plate. Validation below rejects any non-zero value.
    fliplr: float = 0.0
    copy_paste: float = 0.0
    erasing: float = 0.4
    mosaic: float = 1.0
    close_mosaic: int = 10
    mixup: float = 0.0

    # --- Runtime / bookkeeping ----------------------------------------------
    device: str = "auto"
    workers: int = 8
    project: Path = field(default_factory=lambda: DEFAULT_RUNS_DIR)
    name: str = "yolo11n_baseline"
    exist_ok: bool = False
    seed: int = 42
    deterministic: bool = True
    save_period: int = 10
    val: bool = True
    plots: bool = True
    cache: bool | str = False
    amp: bool = True
    rect: bool = False
    single_cls: bool = False
    fraction: float = 1.0
    verbose: bool = True

    def __post_init__(self) -> None:
        """Normalise paths and validate every field.

        Called automatically by the dataclass machinery. Failing here -- before
        a single image is loaded -- is far cheaper than discovering a bad
        hyper-parameter three hours into a Colab run.

        Raises:
            ValueError: If any field is out of range, unknown, or violates a
                domain rule (non-zero flip probability).
        """
        self.data = _resolve_under_root(self.data)
        self.project = _resolve_under_root(self.project)

        if self.model_variant not in SUPPORTED_MODEL_VARIANTS:
            raise ValueError(
                f"model_variant must be one of {list(SUPPORTED_MODEL_VARIANTS)}, "
                f"got {self.model_variant!r}"
            )
        if self.optimizer not in SUPPORTED_OPTIMIZERS:
            raise ValueError(
                f"optimizer must be one of {list(SUPPORTED_OPTIMIZERS)}, " f"got {self.optimizer!r}"
            )
        if self.imgsz <= 0 or self.imgsz % 32 != 0:
            raise ValueError(f"imgsz must be a positive multiple of 32, got {self.imgsz}")
        if self.epochs <= 0:
            raise ValueError(f"epochs must be positive, got {self.epochs}")
        if self.batch == 0:
            raise ValueError("batch must be non-zero; use a positive size or -1 for AutoBatch")
        if self.patience < 0:
            raise ValueError(f"patience must not be negative, got {self.patience}")
        if self.lr0 <= 0.0:
            raise ValueError(f"lr0 must be positive, got {self.lr0}")
        if self.workers < 0:
            raise ValueError(f"workers must not be negative, got {self.workers}")
        if self.close_mosaic < 0:
            raise ValueError(f"close_mosaic must not be negative, got {self.close_mosaic}")
        if self.close_mosaic > self.epochs:
            raise ValueError(
                f"close_mosaic ({self.close_mosaic}) cannot exceed epochs "
                f"({self.epochs}); mosaic would never be enabled at all"
            )
        if not self.name:
            raise ValueError("name must be a non-empty string")
        if not self.device:
            raise ValueError("device must be non-empty, e.g. 'auto', 'cpu' or '0'")
        if self.cache not in (True, False, "ram", "disk"):
            raise ValueError(f"cache must be True, False, 'ram' or 'disk', got {self.cache!r}")

        for name in _ZERO_TO_ONE_FIELDS:
            value = float(getattr(self, name))
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within [0.0, 1.0], got {value}")
        for name in _NON_NEGATIVE_FIELDS:
            value = float(getattr(self, name))
            if value < 0.0:
                raise ValueError(f"{name} must not be negative, got {value}")
        if self.fraction <= 0.0:
            raise ValueError(f"fraction must be positive, got {self.fraction}")

        # --- Domain rule: never mirror a license plate -----------------------
        # A mirrored plate is not a rotation of a real plate, it is a different
        # (non-existent) object. Allowing this silently would be a subtle,
        # expensive bug: training would converge fine and accuracy on real
        # plates would simply be worse than it should be.
        if self.fliplr != 0.0:
            raise ValueError(
                "fliplr must be 0.0: horizontal flipping mirrors the characters "
                f"printed on the plate and corrupts the training signal (got "
                f"{self.fliplr})"
            )
        if self.flipud != 0.0:
            raise ValueError(
                "flipud must be 0.0: upside-down plates do not occur in the "
                f"target deployment (got {self.flipud})"
            )

        if (
            self.model_variant == "yolo11n"
            and self.pretrained_weights.startswith("yolo11")
            and not self.pretrained_weights.startswith("yolo11n")
        ):
            LOGGER.warning(
                "model_variant=%s but pretrained_weights=%s; Ultralytics will "
                "follow the checkpoint architecture, so the trained model may "
                "not be the variant you expect",
                self.model_variant,
                self.pretrained_weights,
            )

    # --- Derived values ------------------------------------------------------

    @property
    def run_dir(self) -> Path:
        """Absolute directory Ultralytics will write this run into.

        Returns:
            ``<project>/<name>``. Note that with ``exist_ok=False`` Ultralytics
            may append a numeric suffix, in which case the real directory is
            reported by the trainer at runtime.
        """
        return self.project / self.name

    @property
    def initial_weights(self) -> str:
        """Argument to pass to the ``YOLO(...)`` constructor.

        Returns:
            :attr:`pretrained_weights` when set (fine-tuning from an existing
            checkpoint), otherwise ``"<model_variant>.yaml"``, which builds the
            architecture from scratch with random initialisation.
        """
        return self.pretrained_weights or f"{self.model_variant}.yaml"

    # --- Serialisation -------------------------------------------------------

    @classmethod
    def field_names(cls) -> tuple[str, ...]:
        """List every configurable field name.

        Returns:
            Field names in declaration order.
        """
        return tuple(f.name for f in fields(cls))

    @classmethod
    def from_dict(cls, values: dict[str, Any]) -> TrainingConfig:
        """Build a configuration from a plain mapping.

        Unknown keys are rejected rather than ignored: a typo such as
        ``epoch: 100`` would otherwise silently train for the default number of
        epochs.

        Args:
            values: Mapping of field name to value.

        Returns:
            A validated configuration.

        Raises:
            TypeError: If ``values`` is not a mapping.
            ValueError: If it contains unknown keys, or if validation fails.
        """
        if not isinstance(values, dict):
            raise TypeError(f"Expected a mapping of config values, got {type(values).__name__}")
        known = set(cls.field_names())
        unknown = sorted(set(values) - known)
        if unknown:
            raise ValueError(
                f"Unknown configuration key(s): {unknown}. " f"Valid keys are: {sorted(known)}"
            )
        return cls(**values)

    @classmethod
    def from_yaml(cls, path: str | Path) -> TrainingConfig:
        """Load a configuration from a YAML file.

        Args:
            path: Path to the YAML file. A bare name with no directory part is
                also looked up inside :data:`CONFIGS_DIR`, so
                ``--config yolo11n_baseline.yaml`` works from anywhere.

        Returns:
            A validated configuration.

        Raises:
            FileNotFoundError: If no such file exists.
            ValueError: If the file is not valid YAML, does not contain a
                mapping, contains unknown keys, or fails validation.
        """
        candidate = Path(path).expanduser()
        if not candidate.exists() and candidate.parent == Path("."):
            candidate = CONFIGS_DIR / candidate.name
        if not candidate.exists():
            available = sorted(p.name for p in CONFIGS_DIR.glob("*.yaml"))
            raise FileNotFoundError(
                f"Training config not found: {path}. "
                f"Available configs in {CONFIGS_DIR}: {available}"
            )

        try:
            raw = yaml.safe_load(candidate.read_text(encoding="utf-8"))
        except yaml.YAMLError as error:
            raise ValueError(f"{candidate} is not valid YAML: {error}") from error
        except OSError as error:
            raise ValueError(f"Cannot read {candidate}: {error}") from error

        if raw is None:
            raise ValueError(f"{candidate} is empty; expected a YAML mapping")
        if not isinstance(raw, dict):
            raise ValueError(
                f"{candidate} must contain a YAML mapping at the top level, "
                f"got {type(raw).__name__}"
            )

        try:
            config = cls.from_dict(raw)
        except ValueError as error:
            raise ValueError(f"Invalid training config {candidate}: {error}") from error

        LOGGER.info("Loaded training config from %s", candidate)
        return config

    def to_dict(self) -> dict[str, Any]:
        """Convert to a plain, YAML-serialisable dictionary.

        Returns:
            Field name to value, with :class:`~pathlib.Path` values rendered as
            POSIX-style strings so the file stays readable on every platform.
        """
        payload = asdict(self)
        for key, value in payload.items():
            if isinstance(value, Path):
                payload[key] = value.as_posix()
        return payload

    def to_yaml(self, path: str | Path) -> Path:
        """Write this configuration to a YAML file.

        Used by :mod:`ai.training.train` to snapshot the exact hyper-parameters
        next to the run's artefacts, so a result can always be traced back to
        the settings that produced it.

        Args:
            path: Destination file. Parent directories are created.

        Returns:
            The absolute path written.

        Raises:
            ValueError: If the file cannot be written.
        """
        destination = Path(path).expanduser()
        if not destination.is_absolute():
            destination = PROJECT_ROOT / destination
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(
                yaml.safe_dump(self.to_dict(), sort_keys=False, allow_unicode=True),
                encoding="utf-8",
            )
        except OSError as error:
            raise ValueError(f"Cannot write config to {destination}: {error}") from error
        LOGGER.info("Wrote training config to %s", destination)
        return destination

    def to_ultralytics_kwargs(self) -> dict[str, Any]:
        """Render the keyword arguments for ``ultralytics.YOLO.train()``.

        Project-specific bookkeeping fields (:attr:`model_variant`,
        :attr:`pretrained_weights`, :attr:`description`) are stripped, because
        Ultralytics rejects unknown keyword arguments.

        Note that ``device`` is passed through verbatim: resolving ``"auto"``
        into a concrete device is the caller's job (see
        :func:`ai.training.train.resolve_device`), so that the choice can be
        logged and warned about.

        Returns:
            Keyword arguments ready to splat into ``model.train(**kwargs)``.
        """
        payload = asdict(self)
        for key in _NON_ULTRALYTICS_FIELDS:
            payload.pop(key, None)
        payload["data"] = str(self.data)
        payload["project"] = str(self.project)
        return payload
