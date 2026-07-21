"""Curate extra demo media from the locally vetted datasets.

Builds ``demo/images-extra/`` (still images covering every plate family the
local corpora can supply) and two synthetic test videos, from sources that are
already on disk and already licence-vetted in
``docs/reports/17-plate-type-dataset-survey.md``:

* ``datasets/raw/roboflow_plate_color`` -- CC BY 4.0; the TRUE plate string is
  embedded in each filename (``crop_..._79E00392_...``), which makes these the
  cheapest ground truth available.
* ``datasets/raw/commons_vn_plates`` -- Wikimedia Commons photographs:
  diplomatic, military, bus/truck and government plates that no Roboflow set
  carries.
* ``datasets/processed/yolo_v3/images/test`` -- full street scenes from the
  detector's own held-out split, so nothing here ever touched training.

The videos are generated (pan/zoom over scenes, plus a deliberately tilted
segment) rather than downloaded: a downloaded traffic clip has unverifiable
licensing and no ground truth, while a generated one is reproducible from this
script and inherits the ground truth of its source images. The original
``demo-video.mp4`` follows the same philosophy.

Run from the project root::

    python scripts/make_demo_media.py
"""

from __future__ import annotations

import random
import shutil
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
OUT_IMAGES = ROOT / "demo" / "images-extra"
OUT_VIDEO_TYPES = ROOT / "demo" / "demo-video-cac-loai-bien.mp4"
OUT_VIDEO_TRAFFIC = ROOT / "demo" / "demo-video-giao-thong.mp4"

PLATE_COLOR = ROOT / "datasets" / "raw" / "roboflow_plate_color"
COMMONS = ROOT / "datasets" / "raw" / "commons_vn_plates" / "images"
SCENES = ROOT / "datasets" / "processed" / "yolo_v3" / "images" / "test"
SCENE_LABELS = ROOT / "datasets" / "processed" / "yolo_v3" / "labels" / "test"

# (source file stem fragment, output name) -- plate_color picks, chosen from
# the test/valid splits only. The plate string in the name is the ground truth.
PLATE_COLOR_PICKS = [
    ("crop_caunamprc555_79E00392_04-02-2024_16-15-23", "vang-79E00392.jpg"),
    ("crop_garagecuong554_50F01690_28-01-2024_17-16-49", "vang-50F01690.jpg"),
    ("crop_garagecuong554_61C15282_04-02-2024_16-57-44", "vang-61C15282.jpg"),
    ("crop_garagecuong554_86A00519_04-02-2024_14-01-58", "xanh-86A00519.jpg"),
    ("crop_xom7vinhtan554_80A04285_31-01-2024_09-28-58", "xanh-80A04285.jpg"),
    ("crop_xom7vinhtan554_85A00190_31-01-2024_15-17-28", "xanh-85A00190.jpg"),
]

# Wikimedia Commons picks: the families the Roboflow sets cannot supply.
COMMONS_PICKS = [
    ("Diplomatic_plate_of_Vietnam.jpg", "ngoai-giao-commons-1.jpg"),
    ("Vietnam_CD_plate.jpg", "ngoai-giao-cd.jpg"),
    ("Vietnam_Diplomatic_license_plate_NG-651-01.gif", "ngoai-giao-ng-651-01.png"),
    ("Militair_plate_Vietnam.jpg", "quan-doi-commons.jpg"),
    ("Bus_licenceplate_Vietnam_rear.jpg", "xe-buyt.jpg"),
    ("Truck_plate_of_Vietnam.jpg", "xe-tai.jpg"),
    ("Trailer_plate_Vietnam.jpg", "ro-mooc.jpg"),
    ("Vietnamese_numberplate_72A-076.04_BMW_M3.jpg", "o-to-72A07604.jpg"),
    ("Government_car_licenseplate_Vietnam.jpg", "xanh-nha-nuoc-commons.jpg"),
]

SCENE_SAMPLE_SEED = 42
SCENE_SINGLE_COUNT = 3
SCENE_MULTI_COUNT = 5

VIDEO_FPS = 24
SECONDS_PER_IMAGE = 2.5
VIDEO_SIZE = (1280, 720)  # width, height


def _find_one(root: Path, fragment: str) -> Path:
    matches = [p for p in root.rglob(f"*{fragment}*") if p.suffix.lower() in (".jpg", ".png")]
    if not matches:
        raise FileNotFoundError(f"no file matching {fragment!r} under {root}")
    return matches[0]


def _copy_image(source: Path, target: Path) -> None:
    """Copy, converting to the target's format when the suffixes differ."""
    if source.suffix.lower() == target.suffix.lower():
        shutil.copy2(source, target)
        return
    image = cv2.imread(str(source))
    if image is None:
        raise OSError(f"unreadable image: {source}")
    cv2.imwrite(str(target), image)


def _scene_box_count(scene: Path) -> int:
    label = SCENE_LABELS / (scene.stem + ".txt")
    if not label.exists():
        return 0
    return sum(1 for line in label.read_text().splitlines() if line.strip())


def curate_images() -> list[Path]:
    OUT_IMAGES.mkdir(parents=True, exist_ok=True)
    copied: list[Path] = []

    for fragment, name in PLATE_COLOR_PICKS:
        target = OUT_IMAGES / name
        _copy_image(_find_one(PLATE_COLOR, fragment), target)
        copied.append(target)

    for source_name, name in COMMONS_PICKS:
        target = OUT_IMAGES / name
        _copy_image(COMMONS / source_name, target)
        copied.append(target)

    rng = random.Random(SCENE_SAMPLE_SEED)
    scenes = sorted(SCENES.glob("*.png")) + sorted(SCENES.glob("*.jpg"))
    singles = [s for s in scenes if _scene_box_count(s) == 1]
    multis = [s for s in scenes if _scene_box_count(s) >= 3]
    for index, scene in enumerate(rng.sample(singles, SCENE_SINGLE_COUNT)):
        target = OUT_IMAGES / f"canh-mot-bien-{index + 1}{scene.suffix}"
        _copy_image(scene, target)
        copied.append(target)
    for index, scene in enumerate(rng.sample(multis, SCENE_MULTI_COUNT)):
        target = OUT_IMAGES / f"canh-nhieu-bien-{index + 1}{scene.suffix}"
        _copy_image(scene, target)
        copied.append(target)

    return copied


def _letterbox(image: np.ndarray) -> np.ndarray:
    """Fit an image into the video frame on a dark canvas."""
    target_w, target_h = VIDEO_SIZE
    height, width = image.shape[:2]
    scale = min(target_w / width, target_h / height)
    resized = cv2.resize(image, (int(width * scale), int(height * scale)))
    canvas = np.full((target_h, target_w, 3), 24, dtype=np.uint8)
    y0 = (target_h - resized.shape[0]) // 2
    x0 = (target_w - resized.shape[1]) // 2
    canvas[y0 : y0 + resized.shape[0], x0 : x0 + resized.shape[1]] = resized
    return canvas


def _ken_burns_frames(image: np.ndarray, tilt_degrees: float = 0.0):
    """Yield slow-zoom frames, optionally with a constant tilt.

    The tilt segments are the whole point of the traffic video: they present
    the recogniser with the skewed geometry the retry ladder exists for,
    something a flat slideshow never does.
    """
    frame_count = int(VIDEO_FPS * SECONDS_PER_IMAGE)
    base = _letterbox(image)
    height, width = base.shape[:2]
    center = (width / 2, height / 2)
    for i in range(frame_count):
        progress = i / max(1, frame_count - 1)
        zoom = 1.0 + 0.12 * progress
        matrix = cv2.getRotationMatrix2D(center, tilt_degrees, zoom)
        yield cv2.warpAffine(base, matrix, (width, height), flags=cv2.INTER_LINEAR)


def make_video(images: list[tuple[Path, float]], target: Path) -> None:
    writer = cv2.VideoWriter(
        str(target), cv2.VideoWriter_fourcc(*"mp4v"), VIDEO_FPS, VIDEO_SIZE
    )
    try:
        for path, tilt in images:
            image = cv2.imread(str(path))
            if image is None:
                print(f"  skipping unreadable {path}")
                continue
            for frame in _ken_burns_frames(image, tilt):
                writer.write(frame)
    finally:
        writer.release()
    print(f"wrote {target} ({target.stat().st_size / 1e6:.1f} MB)")


def main() -> None:
    copied = curate_images()
    print(f"curated {len(copied)} images into {OUT_IMAGES}")

    type_show = [
        (OUT_IMAGES / "o-to-72A07604.jpg", 0.0),
        (OUT_IMAGES / "vang-79E00392.jpg", 0.0),
        (OUT_IMAGES / "vang-50F01690.jpg", -4.0),
        (OUT_IMAGES / "xanh-86A00519.jpg", 0.0),
        (OUT_IMAGES / "xanh-80A04285.jpg", 3.0),
        (OUT_IMAGES / "quan-doi-commons.jpg", 0.0),
        (OUT_IMAGES / "ngoai-giao-commons-1.jpg", 0.0),
        (OUT_IMAGES / "ngoai-giao-ng-651-01.png", 0.0),
        (OUT_IMAGES / "xe-buyt.jpg", -3.0),
        (OUT_IMAGES / "xe-tai.jpg", 0.0),
    ]
    make_video(type_show, OUT_VIDEO_TYPES)

    traffic = [(OUT_IMAGES / f"canh-mot-bien-{i + 1}.png", 0.0) for i in range(SCENE_SINGLE_COUNT)]
    traffic += [
        (OUT_IMAGES / f"canh-nhieu-bien-{i + 1}.png", tilt)
        for i, tilt in zip(range(SCENE_MULTI_COUNT), (0.0, -6.0, 0.0, 5.0, 0.0))
    ]
    traffic = [(p, t) for p, t in traffic if p.exists()] + [
        (p.with_suffix(".jpg"), t) for p, t in traffic if not p.exists()
    ]
    make_video(traffic, OUT_VIDEO_TRAFFIC)


if __name__ == "__main__":
    main()
