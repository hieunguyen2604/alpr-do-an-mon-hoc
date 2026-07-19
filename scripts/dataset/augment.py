"""Augment the training split with albumentations transforms suited to plates.

Usage examples::

    python scripts/dataset/augment.py --multiplier 2
    python scripts/dataset/augment.py --multiplier 3 --seed 7
    python scripts/dataset/augment.py --output-dir datasets/processed/yolo_aug

Why there is no horizontal flip
--------------------------------
``HorizontalFlip`` is in almost every default augmentation recipe, and it is
**wrong** for license plate recognition. A plate is text. Mirroring it produces
an image that no camera could ever capture: ``51F-12345`` becomes an unreadable
reversal, and characters map onto each other misleadingly -- a flipped ``2``
resembles a ``5``, a flipped ``E`` resembles a ``3``.

The damage is easy to miss because it is invisible at the detection stage. A
detector trained with flips still finds plate-shaped rectangles and its mAP
looks fine, so the augmentation appears harmless. The cost lands entirely on the
OCR stage, which has been taught that mirrored glyphs are legitimate, and shows
up much later as unexplained character confusion. The same argument rules out
vertical flips, 90-degree rotations and transposes.

Everything here is a distortion a real traffic camera actually produces:

===================  =========================================================
Transform            What it simulates
===================  =========================================================
Rotation +/-10 deg   Camera tilt and a plate mounted slightly askew. Kept small
                     because a plate rotated far past 10 degrees is a different
                     problem (needing rectification, not augmentation).
Brightness/contrast  Time of day, headlight glare, shadow under a bridge.
Motion blur          A moving vehicle at a slow shutter speed. The single most
                     common real-world failure.
Gaussian noise       High-ISO capture at night.
JPEG compression     Almost every CCTV stream is compressed; training only on
                     clean images leaves the model unprepared for artefacts.
Mild perspective     The camera is never perpendicular to the plate.
===================  =========================================================

Only the training split is touched
-----------------------------------
Augmenting validation or test data invalidates the evaluation: the metric would
be measured on synthetic images that no longer represent the deployment
distribution, and augmented copies of a validation image are near-duplicates of
it, which inflates the score. This script refuses to write into ``val`` or
``test`` and there is no flag to override that.
"""

from __future__ import annotations

import argparse
import logging
import random
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (  # noqa: E402
    add_common_arguments,
    bootstrap_project_path,
    configure_logging,
    iter_image_files,
    resolve_dataset_paths,
    write_json,
)

bootstrap_project_path()

from ai.data.schema import (  # noqa: E402
    BoxRecord,
    LabelParseError,
    image_path_to_label_path,
    parse_yolo_label_file,
    write_yolo_label_file,
)

LOGGER = logging.getLogger("dataset.augment")

FORBIDDEN_SPLITS: Final[frozenset[str]] = frozenset({"val", "valid", "validation", "test"})
"""Splits this script will never write into. Not overridable by design."""

AUGMENTED_SUFFIX: Final[str] = "aug"
"""Marker inserted into generated file names, e.g. ``vnlp_000001_aug1.jpg``."""


@dataclass(slots=True)
class AugmentStats:
    """Counters for one augmentation run.

    Attributes:
        source_images: Training images read.
        generated: Augmented images written.
        skipped_unreadable: Images OpenCV could not decode.
        skipped_no_boxes: Images with no boxes, which are not augmented.
        dropped_empty: Augmented results discarded because every box was
            transformed out of the frame.
    """

    source_images: int = 0
    generated: int = 0
    skipped_unreadable: int = 0
    skipped_no_boxes: int = 0
    dropped_empty: int = 0

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable view."""
        return {
            "source_images": self.source_images,
            "generated_images": self.generated,
            "skipped_unreadable": self.skipped_unreadable,
            "skipped_no_boxes": self.skipped_no_boxes,
            "dropped_all_boxes_lost": self.dropped_empty,
        }


def build_pipeline(
    *,
    rotate_degrees: float = 10.0,
    perspective_scale: float = 0.05,
    min_visibility: float = 0.35,
) -> Any:
    """Construct the albumentations pipeline.

    Note the deliberate absence of ``HorizontalFlip``, ``VerticalFlip``,
    ``RandomRotate90`` and ``Transpose`` -- see the module docstring.

    Args:
        rotate_degrees: Maximum absolute rotation in degrees.
        perspective_scale: Upper bound of the perspective distortion. Kept
            small; a strong warp turns a plate into a shape the detector will
            never encounter.
        min_visibility: Fraction of a box that must survive for it to be kept.
            A box clipped below this is dropped rather than retained as a
            sliver, because a sliver labelled "plate" is a wrong label.

    Returns:
        A configured ``albumentations.Compose`` expecting ``image``, ``bboxes``
        in YOLO format and ``class_labels``.

    Raises:
        ImportError: If albumentations or OpenCV is not installed.
        ValueError: If a parameter is out of range.
    """
    if rotate_degrees < 0:
        raise ValueError(f"rotate_degrees must be non-negative, got {rotate_degrees}")
    if not 0.0 <= perspective_scale < 0.5:
        raise ValueError(f"perspective_scale must be in [0, 0.5), got {perspective_scale}")
    if not 0.0 <= min_visibility <= 1.0:
        raise ValueError(f"min_visibility must be in [0, 1], got {min_visibility}")

    try:
        import albumentations as A
        import cv2
    except ImportError as exc:  # pragma: no cover - dependency is declared
        raise ImportError(
            "Augmentation needs albumentations and opencv-python. Install them with:\n"
            "    pip install albumentations opencv-python"
        ) from exc

    return A.Compose(
        [
            # Geometry first, so photometric noise is applied to the final shape
            # rather than being resampled (and partly smoothed away) by the warp.
            A.Affine(
                rotate=(-rotate_degrees, rotate_degrees),
                scale=(0.95, 1.05),
                translate_percent=(-0.02, 0.02),
                border_mode=cv2.BORDER_CONSTANT,
                fill=0,
                p=0.7,
            ),
            A.Perspective(
                scale=(0.02, perspective_scale),
                keep_size=True,
                border_mode=cv2.BORDER_CONSTANT,
                fill=0,
                p=0.3,
            ),
            A.RandomBrightnessContrast(
                brightness_limit=(-0.25, 0.25), contrast_limit=(-0.25, 0.25), p=0.7
            ),
            A.MotionBlur(blur_limit=(3, 7), p=0.3),
            A.GaussNoise(std_range=(0.02, 0.12), p=0.3),
            A.ImageCompression(compression_type="jpeg", quality_range=(45, 95), p=0.4),
        ],
        bbox_params=A.BboxParams(
            format="yolo",
            label_fields=["class_labels"],
            min_visibility=min_visibility,
            clip=True,
        ),
        seed=None,
    )


def load_image(image_path: Path) -> Any | None:
    """Decode an image into a BGR NumPy array.

    Args:
        image_path: The image to read.

    Returns:
        The array, or ``None`` if OpenCV cannot decode it.
    """
    try:
        import cv2
        import numpy as np

        # np.fromfile + imdecode instead of cv2.imread: imread cannot open
        # non-ASCII paths on Windows.
        buffer = np.fromfile(str(image_path), dtype=np.uint8)
        if buffer.size == 0:
            return None
        return cv2.imdecode(buffer, cv2.IMREAD_COLOR)
    except Exception as exc:  # noqa: BLE001
        LOGGER.debug("Cannot decode %s: %s", image_path, exc)
        return None


def save_image(image: Any, destination: Path, *, quality: int = 95) -> bool:
    """Write a BGR array to disk as JPEG or PNG.

    Args:
        image: The array to write.
        destination: Target path; the suffix decides the format.
        quality: JPEG quality.

    Returns:
        ``True`` on success, ``False`` if encoding or writing failed.
    """
    try:
        import cv2

        destination.parent.mkdir(parents=True, exist_ok=True)
        params = (
            [cv2.IMWRITE_JPEG_QUALITY, quality]
            if destination.suffix.lower() in {".jpg", ".jpeg"}
            else []
        )
        ok, encoded = cv2.imencode(destination.suffix, image, params)
        if not ok:
            return False
        encoded.tofile(str(destination))
        return True
    except Exception as exc:  # noqa: BLE001
        LOGGER.warning("Cannot write %s: %s", destination, exc)
        return False


def augment_image(
    pipeline: Any, image: Any, boxes: Sequence[BoxRecord]
) -> tuple[Any, list[BoxRecord]] | None:
    """Apply the pipeline to one image and its boxes.

    Args:
        pipeline: The ``albumentations.Compose`` from :func:`build_pipeline`.
        image: BGR image array.
        boxes: The image's boxes, in normalised YOLO coordinates.

    Returns:
        ``(augmented_image, augmented_boxes)``, or ``None`` when the transform
        failed or pushed every box out of frame. A plate image with no plate in
        it is not a useful training sample, and keeping it would teach the
        detector that plate-like scenes contain nothing.
    """
    # Drop malformed boxes before albumentations sees them. It raises on a
    # degenerate box, which would discard the whole image -- including its good
    # boxes -- over one bad label. verify_annotations.py is where such labels get
    # reported; here the job is simply not to lose usable data because of them.
    usable = [box for box in boxes if not box.validate()]
    if len(usable) < len(boxes):
        LOGGER.debug(
            "Ignoring %d malformed box(es) during augmentation", len(boxes) - len(usable)
        )
    if not usable:
        return None

    payload_boxes = [
        [box.x_center, box.y_center, box.width, box.height] for box in usable
    ]
    class_labels = [box.class_id for box in usable]

    try:
        result = pipeline(image=image, bboxes=payload_boxes, class_labels=class_labels)
    except Exception as exc:  # noqa: BLE001 - transform failures must not abort the run
        LOGGER.warning("Augmentation failed for one image: %s", exc)
        return None

    new_boxes = [
        BoxRecord(
            x_center=float(coords[0]),
            y_center=float(coords[1]),
            width=float(coords[2]),
            height=float(coords[3]),
            class_id=int(label),
            plate_text=usable[index].plate_text if index < len(usable) else None,
            line_count=usable[index].line_count if index < len(usable) else None,
        )
        for index, (coords, label) in enumerate(zip(result["bboxes"], result["class_labels"]))
    ]

    if not new_boxes:
        return None
    return result["image"], new_boxes


def augment_split(
    images_dir: Path,
    output_images_dir: Path,
    output_labels_dir: Path,
    *,
    multiplier: int,
    pipeline: Any,
    seed: int,
    jpeg_quality: int,
) -> AugmentStats:
    """Generate augmented copies of every image in a split.

    Args:
        images_dir: Source images (the training split).
        output_images_dir: Where augmented images go.
        output_labels_dir: Where augmented labels go.
        multiplier: Augmented copies per source image.
        pipeline: The albumentations pipeline.
        seed: Base random seed, so a run is reproducible.
        jpeg_quality: Quality for written JPEGs.

    Returns:
        The run counters.
    """
    stats = AugmentStats()
    image_paths = list(iter_image_files(images_dir))
    LOGGER.info("Augmenting %d training images x%d", len(image_paths), multiplier)

    output_images_dir.mkdir(parents=True, exist_ok=True)
    output_labels_dir.mkdir(parents=True, exist_ok=True)

    iterator: Any = image_paths
    if len(image_paths) >= 200:
        try:
            from tqdm import tqdm

            iterator = tqdm(image_paths, desc="Augmenting", unit="img")
        except ImportError:
            pass

    for image_path in iterator:
        # Skip anything this script produced, so re-running does not augment
        # augmentations into an ever-degrading chain.
        if f"_{AUGMENTED_SUFFIX}" in image_path.stem:
            continue

        stats.source_images += 1

        label_path = image_path_to_label_path(image_path)
        if not label_path.is_file():
            stats.skipped_no_boxes += 1
            continue
        try:
            boxes = parse_yolo_label_file(label_path)
        except (LabelParseError, OSError) as exc:
            LOGGER.warning("Skipping %s: %s", image_path.name, exc)
            stats.skipped_no_boxes += 1
            continue
        if not boxes:
            stats.skipped_no_boxes += 1
            continue

        image = load_image(image_path)
        if image is None:
            LOGGER.warning("Cannot decode %s; skipping", image_path)
            stats.skipped_unreadable += 1
            continue

        for copy_index in range(1, multiplier + 1):
            # Seeding per image keeps the output reproducible regardless of the
            # order files are visited in.
            random.seed(f"{seed}:{image_path.name}:{copy_index}")
            try:
                import numpy as np

                np.random.seed(
                    abs(hash(f"{seed}:{image_path.name}:{copy_index}")) % (2**32)
                )
            except ImportError:  # pragma: no cover
                pass

            outcome = augment_image(pipeline, image, boxes)
            if outcome is None:
                stats.dropped_empty += 1
                continue

            augmented_image, augmented_boxes = outcome
            new_stem = f"{image_path.stem}_{AUGMENTED_SUFFIX}{copy_index}"
            destination = output_images_dir / f"{new_stem}{image_path.suffix}"
            if not save_image(augmented_image, destination, quality=jpeg_quality):
                continue
            write_yolo_label_file(output_labels_dir / f"{new_stem}.txt", augmented_boxes)
            stats.generated += 1

    return stats


def resolve_split_dirs(dataset_dir: Path, split: str) -> tuple[Path, Path]:
    """Locate the image and label directories of a split.

    Handles both layouts in circulation: ``images/train`` + ``labels/train``
    (what ``split.py`` writes, and the Ultralytics default) and
    ``train/images`` + ``train/labels``.

    Args:
        dataset_dir: Root of the split dataset.
        split: Split name.

    Returns:
        ``(images_dir, labels_dir)``.

    Raises:
        FileNotFoundError: If neither layout is present.
    """
    candidates = [
        (dataset_dir / "images" / split, dataset_dir / "labels" / split),
        (dataset_dir / split / "images", dataset_dir / split / "labels"),
    ]
    for images_dir, labels_dir in candidates:
        if images_dir.is_dir():
            return images_dir, labels_dir

    raise FileNotFoundError(
        f"No '{split}' split under {dataset_dir}. Expected "
        f"{dataset_dir / 'images' / split} or {dataset_dir / split / 'images'}. "
        "Run split.py first."
    )


def build_parser() -> argparse.ArgumentParser:
    """Construct the command-line parser.

    Returns:
        The configured parser.
    """
    parser = argparse.ArgumentParser(
        prog="augment.py",
        description=(
            "Augment the TRAINING split only, with transforms appropriate for "
            "license plates. Horizontal flip is deliberately excluded: plates "
            "carry text and mirroring it teaches the OCR stage wrong glyphs."
        ),
        epilog=(
            "Examples:\n"
            "  python augment.py --multiplier 2\n"
            "  python augment.py --multiplier 3 --rotate-degrees 8 --seed 7\n\n"
            "Writing into val or test is refused; there is no override."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=None,
        metavar="DIR",
        help="Split dataset produced by split.py (default: <datasets>/processed/yolo).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        metavar="DIR",
        help=(
            "Where to write the augmented files. Defaults to the input dataset, "
            "adding augmented images alongside the originals in the train split."
        ),
    )
    parser.add_argument(
        "--split",
        default="train",
        help=(
            "Split to augment. Only 'train' is accepted; val/test are refused "
            "(default: %(default)s)."
        ),
    )
    parser.add_argument(
        "--multiplier",
        type=int,
        default=2,
        metavar="N",
        help="Augmented copies to generate per source image (default: %(default)s).",
    )
    parser.add_argument(
        "--rotate-degrees",
        type=float,
        default=10.0,
        metavar="DEG",
        help="Maximum absolute rotation (default: %(default)s).",
    )
    parser.add_argument(
        "--perspective-scale",
        type=float,
        default=0.05,
        metavar="S",
        help="Upper bound of the perspective warp (default: %(default)s).",
    )
    parser.add_argument(
        "--min-visibility",
        type=float,
        default=0.35,
        metavar="F",
        help=(
            "Fraction of a box that must survive the transform for it to be "
            "kept (default: %(default)s)."
        ),
    )
    parser.add_argument(
        "--jpeg-quality",
        type=int,
        default=95,
        metavar="Q",
        help="JPEG quality for written images (default: %(default)s).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        metavar="N",
        help="Random seed, so the augmentation is reproducible (default: %(default)s).",
    )
    return add_common_arguments(parser)


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point.

    Args:
        argv: Argument list, defaulting to ``sys.argv[1:]``.

    Returns:
        ``0`` on success; ``1`` if the split is forbidden or missing, a
        parameter is invalid, or nothing could be generated.
    """
    args = build_parser().parse_args(argv)
    configure_logging(args.log_level)

    if args.split.lower() in FORBIDDEN_SPLITS:
        LOGGER.error(
            "Refusing to augment the '%s' split. Augmenting validation or test "
            "data invalidates the evaluation: the metric would be measured on "
            "synthetic images, and augmented copies are near-duplicates of the "
            "originals, which inflates the score.",
            args.split,
        )
        return 1

    if args.multiplier < 1:
        LOGGER.error("--multiplier must be at least 1, got %d", args.multiplier)
        return 1

    paths = resolve_dataset_paths(args.datasets_dir)
    input_dir = (args.input_dir or (paths.processed / "yolo")).expanduser().resolve()
    output_dir = (args.output_dir or input_dir).expanduser().resolve()

    try:
        images_dir, _ = resolve_split_dirs(input_dir, args.split)
    except FileNotFoundError as exc:
        LOGGER.error("%s", exc)
        return 1

    output_images_dir = output_dir / "images" / args.split
    output_labels_dir = output_dir / "labels" / args.split

    try:
        pipeline = build_pipeline(
            rotate_degrees=args.rotate_degrees,
            perspective_scale=args.perspective_scale,
            min_visibility=args.min_visibility,
        )
    except (ImportError, ValueError) as exc:
        LOGGER.error("%s", exc)
        return 1

    LOGGER.info("Source: %s", images_dir)
    LOGGER.info("Output: %s", output_images_dir)
    LOGGER.info("Transforms exclude every kind of flip -- plates carry text.")

    stats = augment_split(
        images_dir,
        output_images_dir,
        output_labels_dir,
        multiplier=args.multiplier,
        pipeline=pipeline,
        seed=args.seed,
        jpeg_quality=args.jpeg_quality,
    )

    summary = stats.as_dict()
    summary.update(
        {
            "input_dir": str(input_dir),
            "output_dir": str(output_dir),
            "split": args.split,
            "multiplier": args.multiplier,
            "seed": args.seed,
            "rotate_degrees": args.rotate_degrees,
            "perspective_scale": args.perspective_scale,
            "min_visibility": args.min_visibility,
            "horizontal_flip": False,
            "horizontal_flip_note": (
                "Excluded on purpose. Plates are text; a mirrored plate is an "
                "image no camera can produce and it teaches the OCR stage "
                "reversed glyphs. The detector's mAP hides the damage, which is "
                "why the mistake usually goes unnoticed until OCR accuracy is "
                "measured."
            ),
        }
    )
    write_json(paths.reports / "augmentation_report.json", summary)

    LOGGER.info("=" * 70)
    LOGGER.info("Source images    : %d", stats.source_images)
    LOGGER.info("Generated images : %d", stats.generated)
    if stats.dropped_empty:
        LOGGER.warning(
            "Dropped (all boxes transformed out of frame): %d", stats.dropped_empty
        )
    if stats.skipped_no_boxes:
        LOGGER.info("Skipped, no boxes: %d", stats.skipped_no_boxes)
    if stats.skipped_unreadable:
        LOGGER.warning("Skipped, unreadable: %d", stats.skipped_unreadable)
    LOGGER.info("=" * 70)

    if stats.generated == 0:
        LOGGER.error("No augmented images were produced. Check the counts above.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
