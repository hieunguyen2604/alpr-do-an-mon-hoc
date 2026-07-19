"""Train a YOLO11 Vietnamese license-plate detector.

The script is a thin, well-instrumented wrapper around Ultralytics: all
hyper-parameters come from a YAML file under ``ai/training/configs/`` (see
:class:`ai.training.config.TrainingConfig`), and only a handful of operational
overrides are accepted on the command line.

Responsibilities that justify the wrapper existing at all:

* resolve ``device: auto`` explicitly, and shout when the answer is CPU;
* log to both stdout and a timestamped file, so a Colab session that dies still
  leaves evidence behind;
* snapshot the effective config next to the run artefacts;
* resume cleanly from ``last.pt`` after the inevitable Colab disconnect;
* publish the winning ``best.pt`` into ``models/`` when the run finishes.

Examples:
    Fine-tune on whatever hardware is present::

        python -m ai.training.train --config yolo11n_finetune.yaml

    Resume after a dropped Colab session::

        python -m ai.training.train --config yolo11n_finetune.yaml --resume

    Quick local smoke test on CPU (deliberately tiny)::

        python -m ai.training.train --config yolo11n_finetune.yaml \\
            --device cpu --epochs 1 --fraction 0.01 --name smoke_test
"""

from __future__ import annotations

import argparse
import logging
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ai.training.config import (
    DEFAULT_MODELS_DIR,
    PROJECT_ROOT,
    TrainingConfig,
)

__all__ = [
    "resolve_device",
    "find_resume_checkpoint",
    "publish_best_weights",
    "run_training",
    "main",
]

LOGGER = logging.getLogger("ai.training.train")

DEFAULT_LOG_DIR: Path = PROJECT_ROOT / "logs" / "training"
"""Where run logs are written when ``--log-dir`` is not given."""

_CPU_WARNING_BANNER = (
    "=" * 78
    + "\nCANH BAO: dang huan luyen tren CPU, se rat cham.\n"
    + "  - Khong tim thay GPU CUDA. Mot epoch tren ~37.000 anh co the mat nhieu gio.\n"
    + "  - Khuyen nghi: chay tren Google Colab GPU bang notebooks/train_colab.ipynb.\n"
    + "  - Neu chi muon kiem tra duong ong chay duoc, hay dung:\n"
    + "      --epochs 1 --fraction 0.01 --batch 2\n"
    + "=" * 78
)


# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #
def configure_logging(log_dir: Path, run_name: str, verbose: bool = True) -> Path:
    """Send log records to stdout and to a timestamped file.

    A file handler is not a nicety here: Colab tears down the VM when a session
    ends, and the browser scrollback is often the only other record of what
    happened. Writing to disk (ideally a Drive-mounted directory) means the run
    can still be diagnosed afterwards.

    Args:
        log_dir: Directory for the log file; created if missing.
        run_name: Run name, used in the log filename.
        verbose: Emit ``DEBUG`` records as well as ``INFO``.

    Returns:
        Path to the log file.

    Raises:
        ValueError: If the log directory cannot be created or written to.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    log_file = log_dir / f"{run_name}_{timestamp}.log"
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
    except OSError as error:
        raise ValueError(f"Cannot write training log to {log_dir}: {error}") from error

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler(stream=sys.stdout)
    stream_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG if verbose else logging.INFO)
    # Replace any handlers installed by an earlier call (e.g. re-running the
    # cell in a notebook), otherwise every record is duplicated.
    for handler in list(root.handlers):
        root.removeHandler(handler)
    root.addHandler(stream_handler)
    root.addHandler(file_handler)

    # Third-party libraries are extremely chatty at DEBUG (matplotlib alone
    # emits font-cache and backend records on every import). Left unfiltered
    # they bury the training output that the log exists to preserve.
    for noisy in ("matplotlib", "PIL", "fsspec", "urllib3", "git"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    LOGGER.info("Logging to %s", log_file)
    return log_file


# --------------------------------------------------------------------------- #
# Device selection
# --------------------------------------------------------------------------- #
def resolve_device(requested: str) -> str:
    """Turn a requested device string into a concrete Ultralytics device.

    ``"auto"`` prefers CUDA, then Apple MPS, then CPU. Any other value is
    honoured as-is, but a request for CUDA on a machine without it is downgraded
    to CPU with a warning rather than left to fail deep inside the trainer.

    Args:
        requested: ``"auto"``, ``"cpu"``, ``"cuda"``, ``"0"``, ``"0,1"`` or
            ``"mps"``.

    Returns:
        A device string that Ultralytics accepts.

    Raises:
        RuntimeError: If PyTorch is not installed.
    """
    try:
        import torch
    except ImportError as error:  # pragma: no cover - environment problem
        raise RuntimeError(
            "PyTorch is not installed. Install the AI requirements first: "
            "pip install -r ai/requirements.txt"
        ) from error

    has_cuda = bool(torch.cuda.is_available())
    has_mps = bool(getattr(torch.backends, "mps", None)) and bool(
        torch.backends.mps.is_available()
    )

    normalised = requested.strip().lower()
    if normalised == "auto":
        if has_cuda:
            device = "0"
            LOGGER.info(
                "device=auto -> CUDA GPU: %s (%d device(s) visible)",
                torch.cuda.get_device_name(0),
                torch.cuda.device_count(),
            )
        elif has_mps:
            device = "mps"
            LOGGER.info("device=auto -> Apple MPS")
        else:
            device = "cpu"
            LOGGER.info("device=auto -> CPU (no CUDA and no MPS available)")
    elif normalised.startswith("cuda") or normalised.isdigit() or "," in normalised:
        if not has_cuda:
            LOGGER.error(
                "Requested device %r but no CUDA GPU is visible to PyTorch; "
                "falling back to CPU",
                requested,
            )
            device = "cpu"
        else:
            device = normalised.replace("cuda:", "").replace("cuda", "0")
    else:
        device = normalised

    if device == "cpu":
        LOGGER.warning("\n%s", _CPU_WARNING_BANNER)

    return device


def log_environment() -> None:
    """Log the versions and hardware that produced this run.

    Recorded so that a number quoted in the thesis can be tied to a concrete
    software/hardware combination.
    """
    import platform

    LOGGER.info("Python      : %s", sys.version.split()[0])
    LOGGER.info("Platform    : %s %s", platform.system(), platform.release())
    LOGGER.info("Processor   : %s", platform.processor() or "unknown")
    try:
        import torch

        LOGGER.info("torch       : %s", torch.__version__)
        LOGGER.info("CUDA build  : %s", torch.version.cuda or "none (CPU-only build)")
        LOGGER.info("CUDA avail. : %s", torch.cuda.is_available())
    except ImportError:  # pragma: no cover - environment problem
        LOGGER.error("torch is not installed")
    try:
        import ultralytics

        LOGGER.info("ultralytics : %s", ultralytics.__version__)
    except ImportError:  # pragma: no cover - environment problem
        LOGGER.error("ultralytics is not installed")


# --------------------------------------------------------------------------- #
# Checkpoints
# --------------------------------------------------------------------------- #
def find_resume_checkpoint(config: TrainingConfig, explicit: str | None) -> Path:
    """Locate the checkpoint to resume training from.

    Args:
        config: Configuration whose :attr:`~TrainingConfig.run_dir` is searched
            when no explicit path is given.
        explicit: Optional user-supplied path to a ``.pt`` file.

    Returns:
        Absolute path to an existing checkpoint.

    Raises:
        FileNotFoundError: If the explicit path does not exist, or if no
            ``last.pt`` can be found for the configured run.
    """
    if explicit:
        candidate = Path(explicit).expanduser()
        if not candidate.is_absolute():
            candidate = PROJECT_ROOT / candidate
        if not candidate.is_file():
            raise FileNotFoundError(f"Resume checkpoint not found: {candidate}")
        return candidate

    # Ultralytics may have suffixed the run directory (name, name2, name3, ...).
    # Prefer the exact name, then fall back to the most recently modified match.
    candidates = [config.run_dir / "weights" / "last.pt"]
    candidates.extend(
        sorted(
            config.project.glob(f"{config.name}*/weights/last.pt"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
    )
    for candidate in candidates:
        if candidate.is_file():
            LOGGER.info("Resuming from %s", candidate)
            return candidate

    raise FileNotFoundError(
        f"No checkpoint to resume: expected {config.run_dir / 'weights' / 'last.pt'}. "
        "Start a fresh run by omitting --resume, or pass an explicit path "
        "(--resume path/to/last.pt)."
    )


def inspect_checkpoint(checkpoint: Path) -> dict[str, Any]:
    """Read the training state stored inside an Ultralytics checkpoint.

    Args:
        checkpoint: Path to a ``.pt`` file.

    Returns:
        Mapping with ``last_epoch`` (``-1`` once training has finished),
        ``total_epochs``, ``data`` and ``readable``. Values are ``None`` when
        the checkpoint could not be inspected.
    """
    report: dict[str, Any] = {
        "readable": False,
        "last_epoch": None,
        "total_epochs": None,
        "data": None,
    }
    try:
        import torch

        payload = torch.load(checkpoint, map_location="cpu", weights_only=False)
    except Exception as error:  # noqa: BLE001 - inspection is best-effort
        LOGGER.warning("Could not inspect %s: %s", checkpoint, error)
        return report

    report["readable"] = True
    report["last_epoch"] = payload.get("epoch")
    train_args = payload.get("train_args") or {}
    if isinstance(train_args, dict):
        report["total_epochs"] = train_args.get("epochs")
        report["data"] = train_args.get("data")
    return report


def assert_resumable(checkpoint: Path) -> None:
    """Refuse to resume a checkpoint whose training has already completed.

    This guard exists because of a genuinely dangerous Ultralytics behaviour:
    calling ``train(resume=True)`` on a *finished* checkpoint does not raise --
    it silently discards the resume request and starts a brand-new run with
    **default** arguments, i.e. training on COCO. The run looks superficially
    normal, finishes, and its worthless weights are then published over a good
    ``best.pt``. Failing loudly here is the only safe behaviour.

    Args:
        checkpoint: Path to the ``last.pt`` being resumed.

    Raises:
        ValueError: If the checkpoint's training run already finished.
    """
    state = inspect_checkpoint(checkpoint)
    if not state["readable"]:
        LOGGER.warning(
            "Checkpoint %s could not be inspected; proceeding with resume, but "
            "verify the dataset name in the Ultralytics banner below",
            checkpoint,
        )
        return

    last_epoch = state["last_epoch"]
    LOGGER.info(
        "Checkpoint state: last_epoch=%s, total_epochs=%s, data=%s",
        last_epoch,
        state["total_epochs"],
        state["data"],
    )
    if last_epoch is None or last_epoch < 0:
        raise ValueError(
            f"{checkpoint} belongs to a run that already COMPLETED "
            f"(epoch marker = {last_epoch}); there is nothing to resume.\n"
            "Resuming it would make Ultralytics silently start a NEW run with "
            "default settings (training on COCO, not your plates) and overwrite "
            "your published best.pt.\n"
            "Do one of the following instead:\n"
            "  - drop --resume and pass a new --name to start a fresh run;\n"
            "  - raise 'epochs' in the config and start a fresh run to train longer;\n"
            "  - point --resume at the last.pt of a genuinely interrupted run."
        )


def publish_best_weights(
    run_dir: Path,
    models_dir: Path = DEFAULT_MODELS_DIR,
    filename: str = "best.pt",
) -> Path | None:
    """Copy the run's best checkpoint into the project's model directory.

    ``models/best.pt`` is the artefact the inference layer loads by default
    (``ALPR_MODEL_PATH``), so promoting it is the final step of a training run.
    An existing file is moved aside with a timestamp suffix rather than
    overwritten -- losing a previously trained model to a worse run is an
    expensive, silent mistake.

    Args:
        run_dir: Ultralytics run directory containing ``weights/best.pt``.
        models_dir: Destination directory; created if missing.
        filename: Destination file name.

    Returns:
        The published path, or ``None`` if the run produced no ``best.pt``.

    Raises:
        ValueError: If the file cannot be copied.
    """
    source = run_dir / "weights" / "best.pt"
    if not source.is_file():
        LOGGER.error(
            "No best.pt in %s -- the run may have been interrupted before the "
            "first validation pass; nothing published",
            source.parent,
        )
        return None

    destination = models_dir / filename
    try:
        models_dir.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
            backup = destination.with_name(f"{destination.stem}_{stamp}{destination.suffix}")
            shutil.move(str(destination), str(backup))
            LOGGER.warning("Existing %s moved aside to %s", destination.name, backup)
        shutil.copy2(source, destination)
    except OSError as error:
        raise ValueError(f"Cannot publish {source} to {destination}: {error}") from error

    size_mb = destination.stat().st_size / (1024 * 1024)
    LOGGER.info("Published best weights -> %s (%.1f MB)", destination, size_mb)
    return destination


# --------------------------------------------------------------------------- #
# Training
# --------------------------------------------------------------------------- #
def _validate_dataset(config: TrainingConfig) -> None:
    """Check the dataset descriptor exists and looks usable.

    Args:
        config: Configuration to check.

    Raises:
        FileNotFoundError: If the ``data.yaml`` descriptor is missing.
        ValueError: If it is not readable YAML or lacks the required keys.
    """
    import yaml

    if not config.data.is_file():
        raise FileNotFoundError(
            f"Dataset descriptor not found: {config.data}\n"
            "Run the Phase 2 dataset pipeline first, or point --data at an "
            "existing Ultralytics data.yaml."
        )
    try:
        payload = yaml.safe_load(config.data.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise ValueError(f"Cannot read dataset descriptor {config.data}: {error}") from error
    if not isinstance(payload, dict):
        raise ValueError(f"{config.data} must contain a YAML mapping")
    missing = [key for key in ("train", "val", "names") if key not in payload]
    if missing:
        raise ValueError(
            f"{config.data} is missing required key(s): {missing}. "
            "An Ultralytics dataset descriptor needs at least train/val/names."
        )
    LOGGER.info(
        "Dataset: %s | classes=%s", config.data, list(payload["names"]) or "<empty>"
    )


def run_training(
    config: TrainingConfig,
    resume_from: Path | None = None,
    models_dir: Path = DEFAULT_MODELS_DIR,
) -> dict[str, Any]:
    """Execute one training run end to end.

    Args:
        config: Fully resolved hyper-parameters.
        resume_from: Checkpoint to continue from, or ``None`` for a fresh run.
        models_dir: Directory the winning ``best.pt`` is published into.

    Returns:
        A summary mapping with keys ``run_dir``, ``best_weights``,
        ``published_weights``, ``elapsed_seconds`` and ``metrics``.

    Raises:
        RuntimeError: If Ultralytics is unavailable or training fails.
        FileNotFoundError: If the dataset descriptor is missing.
        ValueError: If the configuration or dataset is malformed.
    """
    try:
        from ultralytics import YOLO
    except ImportError as error:  # pragma: no cover - environment problem
        raise RuntimeError(
            "ultralytics is not installed. Run: pip install -r ai/requirements.txt"
        ) from error

    _validate_dataset(config)

    device = resolve_device(config.device)
    kwargs = config.to_ultralytics_kwargs()
    kwargs["device"] = device

    if device == "cpu":
        # AMP is a GPU feature; leaving it on merely produces a confusing
        # Ultralytics warning and an unnecessary AMP-check download on CPU.
        kwargs["amp"] = False

    if resume_from is not None:
        assert_resumable(resume_from)
        weights = str(resume_from)
        # Ultralytics restores the full argument set from the checkpoint when
        # resume=True. Passing the original hyper-parameters back in is not just
        # redundant, it is rejected -- so send the minimum.
        kwargs = {"resume": True, "device": device}
        LOGGER.info("Resuming training from checkpoint %s", resume_from)
    else:
        weights = config.initial_weights
        kwargs["resume"] = False
        LOGGER.info(
            "Starting fresh run: variant=%s, weights=%s, epochs=%d, imgsz=%d, "
            "batch=%s, optimizer=%s, seed=%d",
            config.model_variant,
            weights,
            config.epochs,
            config.imgsz,
            config.batch,
            config.optimizer,
            config.seed,
        )
        if config.save_period <= 0:
            LOGGER.warning(
                "save_period=%d disables periodic checkpoints. On Colab this "
                "risks losing the entire run when the session is reclaimed.",
                config.save_period,
            )

    try:
        model = YOLO(weights)
    except Exception as error:  # noqa: BLE001 - surface any loader failure clearly
        raise RuntimeError(
            f"Cannot load model weights {weights!r}: {error}\n"
            "For a pretrained variant, check network access (Ultralytics "
            "downloads yolo11*.pt on first use). For a resume, the checkpoint "
            "may be truncated -- try an earlier epoch*.pt from the same run."
        ) from error

    started = time.perf_counter()
    try:
        model.train(**kwargs)
    except KeyboardInterrupt:
        LOGGER.warning(
            "Training interrupted by user. Resume with: "
            "python -m ai.training.train --config <your.yaml> --resume"
        )
        raise
    except Exception as error:  # noqa: BLE001 - convert to an actionable message
        raise RuntimeError(
            f"Training failed: {error}\n"
            "Common causes: out-of-memory (lower `batch`), a corrupted image or "
            "label in the dataset (see the Ultralytics scan output above), or a "
            "wrong path in data.yaml."
        ) from error
    elapsed = time.perf_counter() - started

    # The trainer knows the real output directory, which may carry a numeric
    # suffix when exist_ok=False and the name was already taken.
    run_dir = Path(getattr(model.trainer, "save_dir", config.run_dir))
    LOGGER.info("Training finished in %.1f min. Run directory: %s", elapsed / 60.0, run_dir)

    # Safety net: confirm the trainer really used our dataset. Ultralytics falls
    # back to its default (COCO) descriptor in a few edge cases -- most notably a
    # rejected resume -- and the resulting run looks entirely normal until its
    # useless weights are published over a good model.
    trained_on = str(getattr(getattr(model.trainer, "args", None), "data", "") or "")
    if trained_on and Path(trained_on).name != config.data.name and resume_from is None:
        raise RuntimeError(
            f"Ultralytics trained on {trained_on!r}, not the requested "
            f"{config.data}. Refusing to publish these weights. This usually "
            "means the dataset descriptor was rejected and a default config was "
            "substituted; check the Ultralytics banner above."
        )

    # Snapshot the effective configuration beside the artefacts. Ultralytics
    # writes its own args.yaml, but this one round-trips back into
    # TrainingConfig.from_yaml() without editing.
    try:
        config.to_yaml(run_dir / "training_config.yaml")
    except ValueError as error:
        LOGGER.error("Could not snapshot config into the run directory: %s", error)

    metrics: dict[str, Any] = {}
    results = getattr(model.trainer, "metrics", None)
    if isinstance(results, dict):
        metrics = {str(k): float(v) for k, v in results.items() if isinstance(v, (int, float))}
        for key, value in metrics.items():
            LOGGER.info("  %-24s %.5f", key, value)

    published = publish_best_weights(run_dir, models_dir=models_dir)

    return {
        "run_dir": run_dir,
        "best_weights": run_dir / "weights" / "best.pt",
        "published_weights": published,
        "elapsed_seconds": elapsed,
        "metrics": metrics,
    }


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def build_parser() -> argparse.ArgumentParser:
    """Construct the command-line parser.

    Returns:
        The configured :class:`argparse.ArgumentParser`.
    """
    parser = argparse.ArgumentParser(
        prog="python -m ai.training.train",
        description=(
            "Train a YOLO11 Vietnamese license-plate detector from a YAML "
            "configuration. Hyper-parameters live in ai/training/configs/; the "
            "flags below are operational overrides only."
        ),
        epilog=(
            "Examples:\n"
            "  python -m ai.training.train --config yolo11n_finetune.yaml\n"
            "  python -m ai.training.train --config yolo11n_finetune.yaml --resume\n"
            "  python -m ai.training.train --config yolo11n_finetune.yaml "
            "--device cpu --epochs 1 --fraction 0.01 --name smoke_test\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--config",
        required=True,
        help=(
            "Training configuration YAML. A bare filename is looked up in "
            "ai/training/configs/ (e.g. yolo11n_finetune.yaml)."
        ),
    )
    parser.add_argument(
        "--resume",
        nargs="?",
        const="",
        default=None,
        metavar="CHECKPOINT",
        help=(
            "Resume an interrupted run. With no value, the newest last.pt for "
            "this config's run name is used; otherwise pass a path to a .pt "
            "checkpoint. Use this after a Colab session drops."
        ),
    )
    parser.add_argument(
        "--device",
        default=None,
        help="Override config device: auto | cpu | 0 | 0,1 | mps.",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=None,
        help="Override the configured number of epochs.",
    )
    parser.add_argument(
        "--batch",
        type=int,
        default=None,
        help="Override batch size (-1 asks Ultralytics to auto-size it).",
    )
    parser.add_argument(
        "--imgsz",
        type=int,
        default=None,
        help="Override training image size (must be a multiple of 32).",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Override the number of dataloader workers.",
    )
    parser.add_argument(
        "--data",
        default=None,
        help="Override the dataset descriptor (Ultralytics data.yaml).",
    )
    parser.add_argument(
        "--name",
        default=None,
        help="Override the run name (output goes to <project>/<name>).",
    )
    parser.add_argument(
        "--project",
        default=None,
        help=(
            "Override the run parent directory. On Colab, point this at a "
            "Google Drive path so checkpoints survive a disconnect."
        ),
    )
    parser.add_argument(
        "--fraction",
        type=float,
        default=None,
        help="Override the fraction of the training set to use (0 < f <= 1).",
    )
    parser.add_argument(
        "--models-dir",
        default=None,
        help=f"Directory to publish best.pt into (default: {DEFAULT_MODELS_DIR}).",
    )
    parser.add_argument(
        "--log-dir",
        default=None,
        help=f"Directory for the run log file (default: {DEFAULT_LOG_DIR}).",
    )
    parser.add_argument(
        "--print-config",
        action="store_true",
        help="Print the effective configuration and exit without training.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Log at INFO level instead of DEBUG.",
    )
    return parser


def _apply_overrides(
    config: TrainingConfig, args: argparse.Namespace
) -> TrainingConfig:
    """Apply command-line overrides on top of a loaded configuration.

    Rebuilding the dataclass (rather than mutating it) re-runs validation, so an
    invalid override is rejected immediately.

    Args:
        config: Configuration loaded from YAML.
        args: Parsed command-line arguments.

    Returns:
        A new, validated configuration.

    Raises:
        ValueError: If an override produces an invalid configuration.
    """
    values = config.to_dict()
    overrides = {
        "device": args.device,
        "epochs": args.epochs,
        "batch": args.batch,
        "imgsz": args.imgsz,
        "workers": args.workers,
        "data": args.data,
        "name": args.name,
        "project": args.project,
        "fraction": args.fraction,
    }
    applied = {key: value for key, value in overrides.items() if value is not None}
    values.update(applied)
    for key, value in applied.items():
        LOGGER.info("CLI override: %s = %r (was %r)", key, value, config.to_dict()[key])

    # close_mosaic is validated against epochs; shrinking epochs from the CLI
    # (a smoke test, typically) would otherwise fail validation for no good
    # reason. Clamp it and say so.
    if values["close_mosaic"] > values["epochs"]:
        LOGGER.warning(
            "close_mosaic (%s) exceeds the overridden epochs (%s); clamping to %s",
            values["close_mosaic"],
            values["epochs"],
            values["epochs"],
        )
        values["close_mosaic"] = values["epochs"]

    return TrainingConfig.from_dict(values)


def main(argv: list[str] | None = None) -> int:
    """Command-line entry point.

    Args:
        argv: Argument list; defaults to :data:`sys.argv`.

    Returns:
        Process exit code: ``0`` on success, ``1`` on a handled error, ``130``
        if interrupted.
    """
    args = build_parser().parse_args(argv)

    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s | %(message)s", stream=sys.stdout
    )

    try:
        config = TrainingConfig.from_yaml(args.config)
        config = _apply_overrides(config, args)
    except (FileNotFoundError, ValueError, TypeError) as error:
        LOGGER.error("Configuration error: %s", error)
        return 1

    log_dir = Path(args.log_dir).expanduser() if args.log_dir else DEFAULT_LOG_DIR
    if not log_dir.is_absolute():
        log_dir = PROJECT_ROOT / log_dir
    try:
        configure_logging(log_dir, config.name, verbose=not args.quiet)
    except ValueError as error:
        LOGGER.error("%s", error)
        return 1

    LOGGER.info("=" * 78)
    LOGGER.info("Vietnamese ALPR -- YOLO11 detector training")
    LOGGER.info("=" * 78)
    log_environment()
    if config.description:
        LOGGER.info("Config note : %s", config.description.strip())
    LOGGER.info("Effective configuration:")
    for key, value in config.to_dict().items():
        LOGGER.info("  %-20s %s", key, value)

    if args.print_config:
        LOGGER.info("--print-config given; exiting without training.")
        return 0

    models_dir = (
        Path(args.models_dir).expanduser() if args.models_dir else DEFAULT_MODELS_DIR
    )
    if not models_dir.is_absolute():
        models_dir = PROJECT_ROOT / models_dir

    resume_from: Path | None = None
    if args.resume is not None:
        try:
            resume_from = find_resume_checkpoint(config, args.resume or None)
        except FileNotFoundError as error:
            LOGGER.error("%s", error)
            return 1

    try:
        summary = run_training(config, resume_from=resume_from, models_dir=models_dir)
    except KeyboardInterrupt:
        return 130
    except (FileNotFoundError, ValueError, RuntimeError) as error:
        LOGGER.error("%s", error)
        return 1

    LOGGER.info("=" * 78)
    LOGGER.info("DONE in %.1f min", summary["elapsed_seconds"] / 60.0)
    LOGGER.info("Run directory   : %s", summary["run_dir"])
    LOGGER.info("Best weights    : %s", summary["best_weights"])
    LOGGER.info("Published to    : %s", summary["published_weights"] or "<not published>")
    LOGGER.info(
        "Next step       : python -m ai.evaluation.evaluate --weights %s",
        summary["published_weights"] or summary["best_weights"],
    )
    LOGGER.info("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
