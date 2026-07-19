"""Export a trained YOLO11 detector to CPU-friendly inference formats.

The deployment target has no CUDA GPU, so the exported format is not a detail --
it is the difference between a usable demo and an unusable one. Phase 1 measured
ONNX Runtime at roughly **3.7x** the throughput of eager PyTorch on CPU for this
model class, and OpenVINO is typically faster still on Intel hardware (the
development machine is an Intel CPU with UHD 770 graphics).

Every export is **verified by loading it back and running a real forward pass**
on a synthetic image. An export that writes a file but produces a model nobody
can load is worse than a failed export, because it is discovered later.

Examples:
    Export the published model to both CPU formats::

        python -m ai.training.export --weights models/best.pt --format all

    ONNX only, at a smaller input size::

        python -m ai.training.export --weights models/best.pt \\
            --format onnx --imgsz 480
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path
from typing import Any, Final

from ai.training.config import DEFAULT_MODELS_DIR, PROJECT_ROOT

__all__ = ["SUPPORTED_FORMATS", "export_model", "verify_exported_model", "main"]

LOGGER = logging.getLogger("ai.training.export")

SUPPORTED_FORMATS: Final[tuple[str, ...]] = ("onnx", "openvino", "torchscript")
"""Formats this script can produce.

* ``onnx``        -- portable, runs under ONNX Runtime; the primary CPU target.
* ``openvino``    -- Intel-optimised; usually the fastest option on this machine.
* ``torchscript`` -- no extra runtime dependency; useful as a fallback and as a
  control measurement in the benchmark.
"""

_RUNTIME_HINTS: Final[dict[str, str]] = {
    "onnx": "pip install onnx onnxruntime onnxslim",
    "openvino": "pip install openvino",
    "torchscript": "(no extra dependency; ships with torch)",
}


def _resolve(path: str | Path) -> Path:
    """Resolve a path against the repository root when it is relative.

    Args:
        path: Absolute or relative path.

    Returns:
        An absolute path.
    """
    candidate = Path(path).expanduser()
    return candidate if candidate.is_absolute() else PROJECT_ROOT / candidate


def verify_exported_model(exported: Path, imgsz: int) -> dict[str, Any]:
    """Load an exported model back and run one forward pass on a dummy image.

    Args:
        exported: Path to the exported artefact (a file, or a directory in the
            OpenVINO case).
        imgsz: Input size the model was exported at.

    Returns:
        Mapping with ``path``, ``exists``, ``size_mb``, ``loaded``,
        ``inference_ok``, ``latency_ms`` and ``error``.

    Raises:
        RuntimeError: If NumPy or Ultralytics is unavailable.
    """
    try:
        import numpy as np
        from ultralytics import YOLO
    except ImportError as error:  # pragma: no cover - environment problem
        raise RuntimeError(
            "numpy and ultralytics are required to verify an export"
        ) from error

    report: dict[str, Any] = {
        "path": str(exported),
        "exists": exported.exists(),
        "size_mb": None,
        "loaded": False,
        "inference_ok": False,
        "latency_ms": None,
        "error": None,
    }
    if not exported.exists():
        report["error"] = "artefact does not exist on disk"
        return report

    if exported.is_dir():
        size_bytes = sum(f.stat().st_size for f in exported.rglob("*") if f.is_file())
    else:
        size_bytes = exported.stat().st_size
    report["size_mb"] = round(size_bytes / (1024 * 1024), 2)

    # A mid-grey frame: content is irrelevant, the point is that the graph runs
    # end to end and produces a Results object rather than raising.
    dummy = np.full((imgsz, imgsz, 3), 128, dtype=np.uint8)
    try:
        model = YOLO(str(exported), task="detect")
        report["loaded"] = True
        started = time.perf_counter()
        model.predict(dummy, imgsz=imgsz, device="cpu", verbose=False)
        report["latency_ms"] = round((time.perf_counter() - started) * 1000.0, 2)
        report["inference_ok"] = True
    except Exception as error:  # noqa: BLE001 - any failure means unusable output
        report["error"] = f"{type(error).__name__}: {error}"
    return report


def export_model(
    weights: Path,
    export_format: str,
    imgsz: int = 640,
    half: bool = False,
    dynamic: bool = False,
    simplify: bool = True,
    opset: int | None = None,
    batch: int = 1,
    verify: bool = True,
) -> dict[str, Any]:
    """Export one trained checkpoint to a single target format.

    Args:
        weights: Path to a ``.pt`` checkpoint.
        export_format: One of :data:`SUPPORTED_FORMATS`.
        imgsz: Square input size baked into the exported graph.
        half: Export in FP16. **Ignored on CPU** by most runtimes and often
            slower there than FP32; a warning is emitted when it is requested
            for a CPU-oriented format.
        dynamic: Allow a dynamic batch/spatial axis. Costs some speed; only
            useful when the input size genuinely varies at runtime.
        simplify: Run the ONNX graph simplifier (ONNX export only).
        opset: ONNX opset version; ``None`` lets Ultralytics choose.
        batch: Batch size baked into the graph.
        verify: Load the result back and run a forward pass.

    Returns:
        Mapping with ``format``, ``output``, ``elapsed_seconds`` and, when
        ``verify`` is set, ``verification``.

    Raises:
        FileNotFoundError: If the checkpoint does not exist.
        ValueError: If ``export_format`` or ``imgsz`` is invalid.
        RuntimeError: If Ultralytics is missing or the export itself fails.
    """
    if export_format not in SUPPORTED_FORMATS:
        raise ValueError(
            f"format must be one of {list(SUPPORTED_FORMATS)}, got {export_format!r}"
        )
    if imgsz <= 0 or imgsz % 32 != 0:
        raise ValueError(f"imgsz must be a positive multiple of 32, got {imgsz}")
    if not weights.is_file():
        raise FileNotFoundError(
            f"Checkpoint not found: {weights}\n"
            "Train a model first (python -m ai.training.train --config ...), or "
            "pass --weights explicitly."
        )

    try:
        from ultralytics import YOLO
    except ImportError as error:  # pragma: no cover - environment problem
        raise RuntimeError(
            "ultralytics is not installed. Run: pip install -r ai/requirements.txt"
        ) from error

    if half:
        LOGGER.warning(
            "--half requested for %s: FP16 is a GPU optimisation. On CPU it is "
            "usually ignored or emulated, and can be SLOWER than FP32. Measure "
            "with ai/evaluation/benchmark_cpu.py before trusting it.",
            export_format,
        )

    LOGGER.info(
        "Exporting %s -> %s (imgsz=%d, half=%s, dynamic=%s, batch=%d)",
        weights.name,
        export_format,
        imgsz,
        half,
        dynamic,
        batch,
    )

    kwargs: dict[str, Any] = {
        "format": export_format,
        "imgsz": imgsz,
        "half": half,
        "dynamic": dynamic,
        "batch": batch,
        "device": "cpu",
        "verbose": False,
    }
    if export_format == "onnx":
        kwargs["simplify"] = simplify
        if opset is not None:
            kwargs["opset"] = opset

    started = time.perf_counter()
    try:
        model = YOLO(str(weights))
        output = model.export(**kwargs)
    except ImportError as error:
        raise RuntimeError(
            f"Export to {export_format} needs an extra package that is not "
            f"installed ({error}). Install it with: "
            f"{_RUNTIME_HINTS.get(export_format, 'see the Ultralytics docs')}"
        ) from error
    except Exception as error:  # noqa: BLE001 - convert to an actionable message
        raise RuntimeError(
            f"Export to {export_format} failed: {error}\n"
            f"Hint: {_RUNTIME_HINTS.get(export_format, '')}. If the checkpoint "
            "was trained with a different ultralytics version, re-export from "
            "the version that produced it."
        ) from error
    elapsed = time.perf_counter() - started

    output_path = Path(str(output))
    LOGGER.info("Exported in %.1fs -> %s", elapsed, output_path)

    result: dict[str, Any] = {
        "format": export_format,
        "output": output_path,
        "elapsed_seconds": elapsed,
    }
    if verify:
        LOGGER.info("Verifying %s export by loading it back...", export_format)
        report = verify_exported_model(output_path, imgsz)
        result["verification"] = report
        if report["inference_ok"]:
            LOGGER.info(
                "  OK: %s loads and runs (%.2f MB, first inference %.1f ms)",
                export_format,
                report["size_mb"],
                report["latency_ms"],
            )
        else:
            LOGGER.error(
                "  FAILED verification for %s: %s", export_format, report["error"]
            )
    return result


def build_parser() -> argparse.ArgumentParser:
    """Construct the command-line parser.

    Returns:
        The configured :class:`argparse.ArgumentParser`.
    """
    parser = argparse.ArgumentParser(
        prog="python -m ai.training.export",
        description=(
            "Export a trained YOLO11 checkpoint to ONNX / OpenVINO / TorchScript "
            "for CPU inference. Every export is verified by loading it back and "
            "running a forward pass."
        ),
        epilog=(
            "Examples:\n"
            "  python -m ai.training.export --weights models/best.pt --format all\n"
            "  python -m ai.training.export --weights models/best.pt --format onnx --imgsz 480\n"
            "\n"
            "Extra runtime packages (not in ai/requirements.txt by default):\n"
            "  onnx     : pip install onnx onnxruntime onnxslim\n"
            "  openvino : pip install openvino\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--weights",
        default=str(DEFAULT_MODELS_DIR / "best.pt"),
        help="Checkpoint to export (default: models/best.pt).",
    )
    parser.add_argument(
        "--format",
        default="all",
        choices=(*SUPPORTED_FORMATS, "all"),
        help="Target format, or 'all' for every supported format (default: all).",
    )
    parser.add_argument(
        "--imgsz",
        type=int,
        default=640,
        help="Input size baked into the exported graph (default: 640).",
    )
    parser.add_argument(
        "--half",
        action="store_true",
        help="Export in FP16. GPU-oriented; usually pointless or slower on CPU.",
    )
    parser.add_argument(
        "--dynamic",
        action="store_true",
        help="Allow dynamic input axes (slower; only if input size varies).",
    )
    parser.add_argument(
        "--no-simplify",
        action="store_true",
        help="Skip the ONNX graph simplifier.",
    )
    parser.add_argument(
        "--opset",
        type=int,
        default=None,
        help="ONNX opset version (default: chosen by Ultralytics).",
    )
    parser.add_argument(
        "--batch",
        type=int,
        default=1,
        help="Batch size baked into the graph (default: 1).",
    )
    parser.add_argument(
        "--no-verify",
        action="store_true",
        help="Skip the load-back verification step (not recommended).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Command-line entry point.

    Args:
        argv: Argument list; defaults to :data:`sys.argv`.

    Returns:
        ``0`` if every requested export succeeded and verified, ``1`` otherwise.
    """
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stdout,
    )

    weights = _resolve(args.weights)
    formats = list(SUPPORTED_FORMATS) if args.format == "all" else [args.format]

    LOGGER.info("Checkpoint : %s", weights)
    LOGGER.info("Formats    : %s", ", ".join(formats))

    results: list[dict[str, Any]] = []
    failures: list[str] = []
    for export_format in formats:
        try:
            results.append(
                export_model(
                    weights=weights,
                    export_format=export_format,
                    imgsz=args.imgsz,
                    half=args.half,
                    dynamic=args.dynamic,
                    simplify=not args.no_simplify,
                    opset=args.opset,
                    batch=args.batch,
                    verify=not args.no_verify,
                )
            )
        except FileNotFoundError as error:
            LOGGER.error("%s", error)
            return 1
        except (ValueError, RuntimeError) as error:
            # One missing optional runtime must not abort the other exports.
            LOGGER.error("%s export skipped: %s", export_format, error)
            failures.append(export_format)

    LOGGER.info("=" * 72)
    LOGGER.info("%-14s %-10s %-10s %s", "FORMAT", "SIZE (MB)", "VERIFIED", "OUTPUT")
    LOGGER.info("-" * 72)
    for result in results:
        report = result.get("verification") or {}
        LOGGER.info(
            "%-14s %-10s %-10s %s",
            result["format"],
            report.get("size_mb", "-"),
            "yes" if report.get("inference_ok") else ("skipped" if not report else "NO"),
            result["output"],
        )
        if report and not report.get("inference_ok"):
            failures.append(result["format"])
    LOGGER.info("=" * 72)

    if failures:
        LOGGER.error("Failed format(s): %s", ", ".join(sorted(set(failures))))
        return 1

    LOGGER.info(
        "Next step: python -m ai.evaluation.benchmark_cpu --weights %s", weights
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
