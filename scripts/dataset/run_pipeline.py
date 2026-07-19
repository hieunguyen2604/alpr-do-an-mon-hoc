"""Run the whole Phase 2 dataset pipeline, or any subset of its steps.

Usage examples::

    python scripts/dataset/run_pipeline.py --dry-run
    python scripts/dataset/run_pipeline.py
    python scripts/dataset/run_pipeline.py --steps dedup merge split stats
    python scripts/dataset/run_pipeline.py --steps split stats --stratify

Step order and why it is this order
-----------------------------------
=========  ============================================================
Step       What it does and what it depends on
=========  ============================================================
download   Fetches the raw datasets. Everything depends on it.
verify     Checks raw annotation quality. Run before merging so a broken
           source is caught while it can still be traced to its origin.
dedup      Perceptual-hash search over ``datasets/raw``. Runs before
           merge so its report is written in terms of original paths;
           ``split.py`` translates those through the merge manifest.
merge      Unifies everything into one class space with unique names.
split      Deals the corpus into train/val/test, keeping duplicate groups
           intact. Requires dedup's output to do that.
augment    Optional, and **off by default**: it multiplies dataset size
           several-fold on disk, which is a decision the user should make
           deliberately rather than inherit from a default.
stats      Charts and ``statistics.json`` over the final split.
=========  ============================================================

Steps run in this canonical order regardless of the order given on the command
line, so ``--steps stats merge`` still merges before it computes statistics.

Failure handling
----------------
A failing step stops the run by default: every later step consumes the previous
one's output, so continuing would produce results computed from a broken input
without saying so. ``--continue-on-error`` overrides this for debugging.

Each step is invoked in-process by calling its ``main()``, so a traceback points
at the real line rather than at a subprocess boundary.
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Final, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (  # noqa: E402
    DatasetPaths,
    add_common_arguments,
    bootstrap_project_path,
    configure_logging,
    resolve_dataset_paths,
    write_json,
)

bootstrap_project_path()

import augment as augment_step  # noqa: E402
import deduplicate as dedup_step  # noqa: E402
import download as download_step  # noqa: E402
import merge as merge_step  # noqa: E402
import split as split_step  # noqa: E402
import verify_annotations as verify_step  # noqa: E402

LOGGER = logging.getLogger("dataset.pipeline")


def _load_statistics_module() -> Any:
    """Load ``statistics.py`` from this directory under a non-colliding name.

    A plain ``import statistics`` would work -- this directory is at the front
    of ``sys.path`` -- but it would also bind the *standard library's* module
    name to this project's script for the rest of the process. Anything that
    later did ``import statistics`` expecting ``median`` would get a confusing
    ``AttributeError``. Loading it by path under the name
    ``dataset_statistics`` keeps the stdlib name free.

    Returns:
        The loaded module.

    Raises:
        ImportError: If the file is missing or cannot be executed.
    """
    import importlib.util

    module_path = Path(__file__).resolve().parent / "statistics.py"
    spec = importlib.util.spec_from_file_location("dataset_statistics", module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load the statistics step from {module_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules["dataset_statistics"] = module
    spec.loader.exec_module(module)
    return module


statistics_step = _load_statistics_module()

STEP_ORDER: Final[tuple[str, ...]] = (
    "download",
    "verify",
    "dedup",
    "merge",
    "split",
    "augment",
    "stats",
)
DEFAULT_STEPS: Final[tuple[str, ...]] = (
    "download",
    "verify",
    "dedup",
    "merge",
    "split",
    "stats",
)


@dataclass(slots=True)
class StepResult:
    """The outcome of one pipeline step.

    Attributes:
        name: Step name.
        exit_code: What the step's ``main()`` returned; ``0`` means success.
        duration: Wall-clock seconds the step took.
        argv: The arguments the step was invoked with, for reproducing it.
        error: Exception text when the step raised rather than returned.
    """

    name: str
    exit_code: int
    duration: float
    argv: list[str] = field(default_factory=list)
    error: str | None = None

    @property
    def ok(self) -> bool:
        """Return ``True`` when the step succeeded."""
        return self.exit_code == 0 and self.error is None

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable view."""
        return {
            "step": self.name,
            "exit_code": self.exit_code,
            "duration_seconds": round(self.duration, 2),
            "argv": self.argv,
            "error": self.error,
            "ok": self.ok,
        }


def build_step_arguments(
    step: str, args: argparse.Namespace, paths: DatasetPaths
) -> list[str]:
    """Build the argument list for one step from the pipeline's own options.

    Keeping this in one place is what lets the pipeline stay a thin wrapper:
    the steps' defaults do the real work, and only genuinely cross-cutting
    options are forwarded.

    Args:
        step: Step name.
        args: Parsed pipeline arguments.
        paths: Resolved dataset layout.

    Returns:
        The argv list to hand to that step's ``main()``.

    Raises:
        ValueError: If ``step`` is not a known step name.
    """
    common = ["--datasets-dir", str(paths.root), "--log-level", args.log_level]

    if step == "download":
        argv = list(common)
        if args.config:
            argv += ["--config", str(args.config)]
        if args.datasets:
            argv += ["--datasets", *args.datasets]
        return argv

    if step == "verify":
        argv = list(common) + ["--input-dir", str(paths.raw)]
        if args.strict_verify:
            argv.append("--strict")
        if args.allow_missing_labels:
            argv.append("--allow-missing-labels")
        return argv

    if step == "dedup":
        argv = list(common) + [
            "--input-dir",
            str(paths.raw),
            "--threshold",
            str(args.dedup_threshold),
        ]
        if args.apply_dedup:
            argv.append("--apply")
        return argv

    if step == "merge":
        argv = list(common) + [
            "--input-dir",
            str(paths.raw),
            "--output-dir",
            str(paths.processed / "merged"),
        ]
        if args.datasets:
            argv += ["--datasets", *args.datasets]
        if args.link:
            argv.append("--link")
        if args.include_extras:
            argv.append("--include-extras")
        return argv

    if step == "split":
        argv = list(common) + [
            "--input-dir",
            str(paths.processed / "merged"),
            "--output-dir",
            str(paths.processed / "yolo"),
            "--ratios",
            *[str(ratio) for ratio in args.ratios],
            "--seed",
            str(args.seed),
        ]
        if args.stratify:
            argv.append("--stratify")
        if args.link:
            argv.append("--link")
        if "dedup" not in _selected_steps(args):
            # Without a dedup run in this pipeline there may be no group file,
            # and split.py refuses to proceed unprotected unless told to.
            argv.append("--allow-no-groups")
        return argv

    if step == "augment":
        return list(common) + [
            "--input-dir",
            str(paths.processed / "yolo"),
            "--multiplier",
            str(args.augment_multiplier),
            "--seed",
            str(args.seed),
        ]

    if step == "stats":
        return list(common) + [
            "--input-dir",
            str(paths.processed / "yolo"),
            "--output-dir",
            str(paths.statistics),
        ]

    raise ValueError(f"Unknown pipeline step {step!r}")


def _selected_steps(args: argparse.Namespace) -> list[str]:
    """Return the requested steps in canonical pipeline order.

    Args:
        args: Parsed pipeline arguments.

    Returns:
        The step names, reordered so dependencies always run first.
    """
    requested = set(args.steps or DEFAULT_STEPS)
    return [step for step in STEP_ORDER if step in requested]


def step_entry_points() -> dict[str, Callable[[Sequence[str]], int]]:
    """Map step names to the ``main()`` functions that implement them.

    Returns:
        The dispatch table.
    """
    return {
        "download": download_step.main,
        "verify": verify_step.main,
        "dedup": dedup_step.main,
        "merge": merge_step.main,
        "split": split_step.main,
        "augment": augment_step.main,
        "stats": statistics_step.main,
    }


def run_step(
    step: str, argv: Sequence[str], entry_points: dict[str, Callable[[Sequence[str]], int]]
) -> StepResult:
    """Execute one step and capture its outcome.

    Args:
        step: Step name.
        argv: Arguments for the step.
        entry_points: The dispatch table from :func:`step_entry_points`.

    Returns:
        The result. An exception raised inside a step is caught and recorded
        rather than propagated, so the pipeline can still write its report.
    """
    LOGGER.info("")
    LOGGER.info("#" * 74)
    LOGGER.info("# STEP: %s", step)
    LOGGER.info("# args: %s", " ".join(argv))
    LOGGER.info("#" * 74)

    started = time.perf_counter()
    try:
        exit_code = entry_points[step](list(argv))
        error = None
    except SystemExit as exc:
        # argparse calls sys.exit on a bad argument; treat that as a step failure
        # rather than letting it kill the whole pipeline process.
        exit_code = int(exc.code) if isinstance(exc.code, int) else 1
        error = None if exit_code == 0 else f"step exited with code {exit_code}"
    except Exception as exc:  # noqa: BLE001 - the report must survive any failure
        LOGGER.exception("Step %s raised an exception", step)
        exit_code = 1
        error = f"{type(exc).__name__}: {exc}"

    duration = time.perf_counter() - started
    result = StepResult(
        name=step, exit_code=exit_code, duration=duration, argv=list(argv), error=error
    )
    LOGGER.info(
        "STEP %s finished in %.1fs with exit code %d", step, duration, exit_code
    )
    return result


def build_parser() -> argparse.ArgumentParser:
    """Construct the command-line parser.

    Returns:
        The configured parser.
    """
    parser = argparse.ArgumentParser(
        prog="run_pipeline.py",
        description=(
            "Run the Phase 2 dataset pipeline: download -> verify -> dedup -> "
            "merge -> split -> stats (augment is opt-in)."
        ),
        epilog=(
            "Examples:\n"
            "  python run_pipeline.py --dry-run\n"
            "  python run_pipeline.py\n"
            "  python run_pipeline.py --steps merge split stats --stratify\n"
            "  python run_pipeline.py --steps augment --augment-multiplier 3\n\n"
            "Steps always run in canonical order, whatever order you list them in."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--steps",
        nargs="+",
        choices=list(STEP_ORDER),
        default=None,
        metavar="STEP",
        help=(
            f"Steps to run, from {', '.join(STEP_ORDER)}. "
            f"Default: {', '.join(DEFAULT_STEPS)} (augment is opt-in because it "
            "multiplies dataset size on disk)."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the plan and each step's arguments, then exit without running.",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help=(
            "Keep going after a failing step. Off by default: later steps consume "
            "earlier output, so continuing produces results derived from a broken "
            "input without saying so."
        ),
    )

    download_group = parser.add_argument_group("download")
    download_group.add_argument(
        "--config", type=Path, default=None, metavar="FILE", help="Dataset catalogue YAML."
    )
    download_group.add_argument(
        "--datasets",
        nargs="+",
        metavar="NAME",
        help="Restrict download and merge to these datasets.",
    )

    verify_group = parser.add_argument_group("verify")
    verify_group.add_argument(
        "--strict-verify",
        action="store_true",
        help="Fail the pipeline when annotation errors are found.",
    )
    verify_group.add_argument(
        "--allow-missing-labels",
        action="store_true",
        help="Treat images with no label as background images rather than errors.",
    )

    dedup_group = parser.add_argument_group("dedup")
    dedup_group.add_argument(
        "--dedup-threshold",
        type=int,
        default=dedup_step.DEFAULT_THRESHOLD,
        metavar="N",
        help="Perceptual-hash Hamming distance threshold (default: %(default)s).",
    )
    dedup_group.add_argument(
        "--apply-dedup",
        action="store_true",
        help=(
            "Actually delete duplicate images. Off by default: the split stays "
            "leak-free from the report alone, so deletion is optional."
        ),
    )

    split_group = parser.add_argument_group("split")
    split_group.add_argument(
        "--ratios",
        nargs=3,
        type=float,
        default=list(split_step.DEFAULT_RATIOS),
        metavar=("TRAIN", "VAL", "TEST"),
        help="Split ratios (default: 0.7 0.2 0.1).",
    )
    split_group.add_argument(
        "--stratify",
        action="store_true",
        help="Balance the estimated one-line/two-line mix across splits.",
    )
    split_group.add_argument(
        "--seed", type=int, default=42, metavar="N", help="Random seed (default: %(default)s)."
    )

    other_group = parser.add_argument_group("merge and augment")
    other_group.add_argument(
        "--link",
        action="store_true",
        help="Hard link instead of copying during merge and split, saving disk space.",
    )
    other_group.add_argument(
        "--include-extras",
        action="store_true",
        help="Carry plate_text and line_count into the merged labels.",
    )
    other_group.add_argument(
        "--augment-multiplier",
        type=int,
        default=2,
        metavar="N",
        help="Augmented copies per training image, when the augment step runs.",
    )

    return add_common_arguments(parser)


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point.

    Args:
        argv: Argument list, defaulting to ``sys.argv[1:]``.

    Returns:
        ``0`` if every step succeeded, ``1`` otherwise.
    """
    args = build_parser().parse_args(argv)
    configure_logging(args.log_level)

    paths = resolve_dataset_paths(args.datasets_dir)
    paths.ensure()
    steps = _selected_steps(args)

    if not steps:
        LOGGER.error("No steps selected.")
        return 1

    LOGGER.info("=" * 74)
    LOGGER.info("Phase 2 dataset pipeline")
    LOGGER.info("Datasets root : %s", paths.root)
    LOGGER.info("Steps         : %s", " -> ".join(steps))
    LOGGER.info("=" * 74)

    if args.dry_run:
        for step in steps:
            LOGGER.info("%-10s %s", step, " ".join(build_step_arguments(step, args, paths)))
        LOGGER.info("Dry run: nothing was executed.")
        return 0

    entry_points = step_entry_points()
    results: list[StepResult] = []
    started = time.perf_counter()

    for step in steps:
        step_argv = build_step_arguments(step, args, paths)
        result = run_step(step, step_argv, entry_points)
        results.append(result)

        if not result.ok and not args.continue_on_error:
            LOGGER.error(
                "Step '%s' failed; stopping. Every later step consumes its output, "
                "so continuing would hide the failure. Use --continue-on-error to "
                "override.",
                step,
            )
            break

    total = time.perf_counter() - started
    summary = {
        "datasets_root": str(paths.root),
        "requested_steps": steps,
        "total_duration_seconds": round(total, 2),
        "results": [result.as_dict() for result in results],
    }
    write_json(paths.reports / "pipeline_report.json", summary)

    LOGGER.info("")
    LOGGER.info("=" * 74)
    LOGGER.info("PIPELINE SUMMARY (%.1fs total)", total)
    for result in results:
        LOGGER.info(
            "  %-10s %-7s %6.1fs%s",
            result.name,
            "OK" if result.ok else "FAILED",
            result.duration,
            f"  ({result.error})" if result.error else "",
        )
    skipped = [step for step in steps if step not in {r.name for r in results}]
    for step in skipped:
        LOGGER.warning("  %-10s SKIPPED (an earlier step failed)", step)
    LOGGER.info("Report: %s", paths.reports / "pipeline_report.json")
    LOGGER.info("=" * 74)

    return 0 if all(result.ok for result in results) and not skipped else 1


if __name__ == "__main__":
    raise SystemExit(main())
