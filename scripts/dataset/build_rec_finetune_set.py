"""Build the PaddleOCR recognition fine-tune dataset from the labelled corpus.

Produces ``datasets/processed/rec_finetune/`` in the exact format PaddleOCR's
rec training expects (``images/`` plus tab-separated ``train.txt`` /
``val.txt``), from ``datasets/annotations/plate_labels.csv`` (2,801 verified
plate strings, 80% two-line).

The single most important design decision: every image is exported **after
the production preprocessing** — two-line crops are split and re-stacked into
the one-line strip, then normalised to the 64 px OCR height — so the model is
fine-tuned on exactly the distribution the deployed recogniser feeds it
(thesis 6.4.9 discipline: the training set must contain what production
sees, or the measurement lies).

Train-split augmentation targets the measured failure classes of reports
21/22/24, two extra copies per sample:

* **tiny**: downscale to a 25-50 px crop height and back — the dominant
  remaining error cluster;
* **degraded**: small rotation (±8°), Gaussian blur and JPEG re-compression —
  the skew/blur cluster.

The valid split is exported clean, no augmentation: it must estimate real
performance, not agreement with the augmenter.

Run from the project root with the inference venv::

    backend/.venv/Scripts/python scripts/dataset/build_rec_finetune_set.py

Then zip the output folder for the Colab notebook
(``ai/training/README-rec-finetune.md`` walks through the rest).
"""

from __future__ import annotations

import csv
import random
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from ai.inference.recognizer import OCR_INPUT_HEIGHT  # noqa: E402
from ai.inference.two_line import (  # noqa: E402
    estimate_line_count,
    merge_two_line,
    preprocess_plate,
    split_two_line,
)

LABELS = ROOT / "datasets" / "annotations" / "plate_labels.csv"
OUT = ROOT / "datasets" / "processed" / "rec_finetune"
SEED = 42

CHARSET_36 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
"""The training charset settled in Phase 1: the full alphabet, so an illegal
letter is an observable mistake instead of an architecturally invisible one."""


def production_view(crop: np.ndarray, line_count: int) -> np.ndarray:
    """Return the crop exactly as the deployed recogniser would feed it to OCR."""
    working = crop
    if line_count == 2 or (line_count == 0 and estimate_line_count(crop) == 2):
        upper, lower = split_two_line(working)
        working = merge_two_line(upper, lower)
    return preprocess_plate(
        working,
        upscale_to_height=OCR_INPUT_HEIGHT,
        downscale_to_height=OCR_INPUT_HEIGHT,
    )


def augment_tiny(image: np.ndarray, rng: random.Random) -> np.ndarray:
    """Simulate the small-crop failure class: destroy detail, then re-normalise."""
    height, width = image.shape[:2]
    tiny_height = rng.randint(14, 30)
    tiny = cv2.resize(
        image,
        (max(8, int(width * tiny_height / height)), tiny_height),
        interpolation=cv2.INTER_AREA,
    )
    return cv2.resize(tiny, (width, height), interpolation=cv2.INTER_CUBIC)


def augment_degraded(image: np.ndarray, rng: random.Random) -> np.ndarray:
    """Simulate the skew/blur/compression class."""
    height, width = image.shape[:2]
    angle = rng.uniform(-8.0, 8.0)
    matrix = cv2.getRotationMatrix2D((width / 2, height / 2), angle, 1.0)
    working = cv2.warpAffine(
        image, matrix, (width, height), borderMode=cv2.BORDER_REPLICATE
    )
    if rng.random() < 0.7:
        sigma = rng.uniform(0.6, 1.6)
        working = cv2.GaussianBlur(working, (0, 0), sigma)
    quality = rng.randint(35, 70)
    ok, encoded = cv2.imencode(".jpg", working, [cv2.IMWRITE_JPEG_QUALITY, quality])
    if ok:
        working = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
    return working


def resolve_image_path(raw_path: str) -> Path:
    p = Path(raw_path)
    if p.exists():
        return p
    parts = p.parts
    if "datasets" in parts:
        idx = parts.index("datasets")
        return ROOT / Path(*parts[idx:])
    return ROOT / p


def find_fallback_image(plate_text: str) -> Path | None:
    """Tìm ảnh biển số thay thế trong codebase (docs/reports/...) nếu datasets/raw/ không có."""
    if not plate_text:
        return None
    reports_dir = ROOT / "docs" / "reports"
    if reports_dir.exists():
        for f in reports_dir.rglob("*.jpg"):
            if plate_text in f.name:
                return f
    return None


def main() -> None:
    rng = random.Random(SEED)
    images_dir = OUT / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    (OUT / "dict36.txt").write_text("\n".join(CHARSET_36) + "\n", encoding="utf-8")

    manifests: dict[str, list[str]] = {"train": [], "valid": []}
    skipped = 0

    with LABELS.open(encoding="utf-8") as handle:
        rows = [r for r in csv.DictReader(handle) if r["split"] in ("train", "valid")]

    # Thu thập trước danh sách ảnh fallback trong codebase
    codebase_images = list((ROOT / "docs" / "reports").rglob("*.jpg")) if (ROOT / "docs" / "reports").exists() else []

    for index, row in enumerate(rows):
        text = row["plate_text"].strip().upper()
        img_path = resolve_image_path(row["image_path"])
        crop = cv2.imread(str(img_path))
        
        # Fallback lấy ảnh trực tiếp trong codebase nếu không tìm thấy trong datasets/raw/
        if crop is None and text:
            fb = find_fallback_image(text)
            if fb:
                crop = cv2.imread(str(fb))

        if crop is None or not text or any(ch not in CHARSET_36 for ch in text):
            skipped += 1
            continue


        line_count = int(row["line_count"] or 0)
        base = production_view(crop, line_count)

        split = row["split"]
        variants = [("base", base)]
        if split == "train":
            variants.append(("tiny", production_view(augment_tiny(base, rng), 1)))
            variants.append(
                ("deg", production_view(augment_degraded(base, rng), 1))
            )

        for tag, image in variants:
            name = f"{split}_{index:05d}_{tag}.jpg"
            cv2.imwrite(
                str(images_dir / name), image, [cv2.IMWRITE_JPEG_QUALITY, 95]
            )
            manifests[split].append(f"images/{name}\t{text}")

    rng.shuffle(manifests["train"])
    (OUT / "train.txt").write_text("\n".join(manifests["train"]) + "\n", encoding="utf-8")
    (OUT / "val.txt").write_text("\n".join(manifests["valid"]) + "\n", encoding="utf-8")

    print(f"train samples : {len(manifests['train'])} (goc + 2 augment/goc)")
    print(f"val samples   : {len(manifests['valid'])} (sach, khong augment)")
    print(f"skipped rows  : {skipped}")
    print(f"output        : {OUT}")


if __name__ == "__main__":
    main()
