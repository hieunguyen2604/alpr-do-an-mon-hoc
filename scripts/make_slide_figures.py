"""Render the figures the defence deck needs but no other artefact produces.

The evaluation pipeline already emits plenty of charts into
``docs/reports/figures/``, and the deck reuses those directly. What it cannot
reuse are the three pictures that carry the *argument* rather than a
measurement:

* the 94.3 / 45.7 gap, which opens the talk and has to land in one glance;
* the split-then-hstack transform, which is the project's core technical
  contribution and is genuinely hard to follow as prose;
* the aspect-ratio basis for classifying line count, which is a claim about
  Vietnamese plate geometry and is best made by showing two real plates.

All three are drawn from the project's own code and demo images rather than
mocked up, so a figure cannot drift away from what the system actually does:
the two-line panel is produced by calling :mod:`ai.inference.two_line`, the
same functions the deployed recogniser calls.

Run from the project root with the inference venv::

    backend/.venv/Scripts/python scripts/make_slide_figures.py

Output lands in ``docs/slides/figures/`` and is committed, so building the
deck does not require running this.
"""

from __future__ import annotations

import sys
from pathlib import Path

import cv2
import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import patches  # noqa: E402

REPO_ROOT: Path = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from ai.inference.two_line import (  # noqa: E402
    merge_two_line,
    rectify_plate,
    split_two_line,
)

OUT_DIR: Path = REPO_ROOT / "docs" / "slides" / "figures"
DEMO_DIR: Path = REPO_ROOT / "demo" / "images"

# The deck's own palette, taken from the UIT template so the figures do not
# look pasted in from somewhere else.
BLUE = "#1a4fd6"
RED = "#d62728"
INK = "#16233d"
MUTED = "#6b7793"

plt.rcParams.update(
    {
        "font.family": "Segoe UI",
        "font.size": 13,
        "axes.edgecolor": MUTED,
        "text.color": INK,
        "axes.labelcolor": INK,
        "xtick.color": INK,
        "ytick.color": INK,
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
    }
)


def save(fig: plt.Figure, name: str) -> None:
    """Write one figure and report it.

    Args:
        fig: The figure to write.
        name: File name inside :data:`OUT_DIR`.
    """
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / name
    fig.savefig(path, dpi=170, bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)
    print(f"[ok] {path.relative_to(REPO_ROOT)}  ({path.stat().st_size // 1024} KB)")


def figure_gap() -> None:
    """The opening number: 94.3% against 45.7%, one glance.

    Two bars and nothing else. The slide outline was explicit that this chart
    works precisely because it is bare -- axes furniture, gridlines and a
    legend would all dilute a comparison that has only one variable.
    """
    fig, ax = plt.subplots(figsize=(7.0, 4.6))

    labels = ["Ô tô\nbiển 1 dòng", "Xe máy\nbiển 2 dòng"]
    values = [94.3, 45.7]
    bars = ax.bar(labels, values, color=[BLUE, RED], width=0.5, zorder=3)

    for bar, value in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value + 2.5,
            f"{value:.1f}%".replace(".", ","),
            ha="center",
            va="bottom",
            fontsize=30,
            fontweight="bold",
            color=bar.get_facecolor(),
        )

    # The gap is the point of the chart, so it gets drawn, not left to the eye.
    ax.annotate(
        "",
        xy=(0, 94.3),
        xytext=(1, 45.7),
        arrowprops={"arrowstyle": "<->", "color": MUTED, "lw": 1.6},
    )
    ax.text(
        0.5,
        70,
        "chênh\n48,6 điểm",
        ha="center",
        va="center",
        fontsize=15,
        fontweight="bold",
        color=INK,
        bbox={"facecolor": "white", "edgecolor": MUTED, "boxstyle": "round,pad=0.4"},
    )

    ax.set_ylim(0, 118)
    ax.set_yticks([])
    ax.tick_params(axis="x", length=0, labelsize=14)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(MUTED)

    save(fig, "fig-gap.png")


def _panel(ax: plt.Axes, image: np.ndarray, title: str, subtitle: str = "") -> None:
    """Draw one BGR image panel with a caption."""
    ax.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_color(MUTED)
    ax.set_title(title, fontsize=14, fontweight="bold", color=INK, pad=8)
    if subtitle:
        ax.set_xlabel(subtitle, fontsize=11, color=MUTED, labelpad=6)


def figure_two_line() -> None:
    """The split-then-hstack transform, step by step, on a real plate.

    Every panel is produced by the deployed functions rather than redrawn, so
    the slide cannot claim a transform the system does not perform.
    """
    source = DEMO_DIR / "2dong-1.png"
    image = cv2.imread(str(source))
    if image is None:
        raise SystemExit(f"[loi] khong doc duoc {source}")

    # The demo file is a full scene; the transform operates on the plate crop,
    # so detect it the way the pipeline does rather than hard-coding a box.
    from ai.inference.config import InferenceConfig
    from ai.inference.detector import YoloPlateDetector

    detector = YoloPlateDetector(InferenceConfig.from_env())
    detections = detector.detect(image)
    if not detections:
        raise SystemExit("[loi] khong phat hien duoc bien so trong anh demo")
    x1, y1, x2, y2 = max(detections, key=lambda d: d.confidence).bbox.to_xyxy()
    crop = image[y1:y2, x1:x2]

    rectified = rectify_plate(crop)
    upper, lower = split_two_line(rectified)
    merged = merge_two_line(upper, lower)

    # Two rows, not one strip. The slide's content frame is close to square, so
    # a 4-across layout scales down to fit the width and leaves most of the
    # frame empty -- the panels end up too small to read from the back of a
    # room. Roughly matching the frame's aspect ratio is what makes the picture
    # large, and on this figure that matters more than reading order elegance.
    fig = plt.figure(figsize=(9.0, 6.4))
    grid = fig.add_gridspec(2, 2, hspace=0.42, wspace=0.18, height_ratios=[1.0, 0.92])

    ratio = f"{crop.shape[1] / crop.shape[0]:.2f}".replace(".", ",")
    _panel(fig.add_subplot(grid[0, 0]), crop, "1 · Vùng cắt", f"tỉ lệ {ratio}")
    _panel(fig.add_subplot(grid[0, 1]), rectified, "2 · Nắn hình", "khử nghiêng")

    ax_split = fig.add_subplot(grid[1, 0])
    gap = np.full((6, upper.shape[1], 3), 255, dtype=np.uint8)
    lower_resized = cv2.resize(lower, (upper.shape[1], lower.shape[0]))
    _panel(ax_split, np.vstack([upper, gap, lower_resized]), "3 · Tách hai nửa", "có chồng lấn")

    _panel(
        fig.add_subplot(grid[1, 1]),
        merged,
        "4 · Ghép ngang → OCR một lần",
        "đọc từng nửa 3,5%  ·  ghép ngang 64,5%",
    )

    save(fig, "fig-two-line.png")


def figure_layouts() -> None:
    """Two real plates against the aspect-ratio band that separates them."""
    # Stacked, for the same reason as the two-line figure: the slide's content
    # frame is near-square, so a wide side-by-side layout would render small.
    fig = plt.figure(figsize=(8.2, 6.6))
    grid = fig.add_gridspec(2, 1, height_ratios=[1.55, 1.0], hspace=0.45)

    inner = grid[0].subgridspec(1, 2, wspace=0.22)
    from ai.inference.config import InferenceConfig
    from ai.inference.detector import YoloPlateDetector

    detector = YoloPlateDetector(InferenceConfig.from_env())
    for row, (name, label) in enumerate(
        [("1dong-1.png", "Ô tô — 1 dòng"), ("2dong-2.png", "Xe máy — 2 dòng")]
    ):
        image = cv2.imread(str(DEMO_DIR / name))
        detections = detector.detect(image)
        x1, y1, x2, y2 = max(detections, key=lambda d: d.confidence).bbox.to_xyxy()
        crop = image[y1:y2, x1:x2]
        ratio = crop.shape[1] / crop.shape[0]
        _panel(
            fig.add_subplot(inner[row]),
            crop,
            label,
            f"tỉ lệ đo được ≈ {ratio:.2f}".replace(".", ","),
        )

    ax = fig.add_subplot(grid[1])
    ax.add_patch(patches.Rectangle((2.0, 0.35), 2.727, 0.3, color="#e8edfa", zorder=1))
    ax.text(3.36, 0.5, "vùng trống\n(2,000 ; 4,727)", ha="center", va="center",
            fontsize=12, color=BLUE, fontweight="bold", zorder=2)

    for value, label, color in [
        (1.357, "xe mô tô\n1,357", RED),
        (2.000, "ô tô ngắn\n2,000", RED),
        (4.727, "ô tô dài\n4,727", BLUE),
    ]:
        ax.plot([value, value], [0.3, 0.7], color=color, lw=3, zorder=3)
        ax.text(value, 0.2, label, ha="center", va="top", fontsize=11,
                color=color, fontweight="bold")

    ax.set_xlim(0.9, 5.3)
    ax.set_ylim(-0.05, 1.0)
    ax.set_yticks([])
    ax.set_xlabel("Tỉ lệ khung hình (rộng / cao)", fontsize=12, labelpad=8)
    ax.set_title("Ngưỡng phân loại đặt tại 2,5", fontsize=13, fontweight="bold", pad=10)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)

    save(fig, "fig-layouts.png")


def main() -> int:
    """Render every deck figure.

    Returns:
        Process exit code.
    """
    figure_gap()
    figure_two_line()
    figure_layouts()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
