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


def _box(
    ax: plt.Axes,
    xy: tuple[float, float],
    size: tuple[float, float],
    text: str,
    *,
    face: str = "white",
    edge: str = MUTED,
    color: str = INK,
    weight: str = "normal",
    fontsize: float = 11.5,
) -> tuple[float, float]:
    """Draw one rounded box with centred text.

    Args:
        ax: Target axes.
        xy: Centre of the box.
        size: ``(width, height)``.
        text: Label, newlines allowed.
        face: Fill colour.
        edge: Border colour.
        color: Text colour.
        weight: Font weight.
        fontsize: Point size.

    Returns:
        The centre, so callers can chain arrows without recomputing it.
    """
    x, y = xy
    width, height = size
    ax.add_patch(
        patches.FancyBboxPatch(
            (x - width / 2, y - height / 2),
            width,
            height,
            boxstyle="round,pad=0.02,rounding_size=0.12",
            facecolor=face,
            edgecolor=edge,
            linewidth=1.6,
            zorder=2,
        )
    )
    ax.text(x, y, text, ha="center", va="center", fontsize=fontsize,
            color=color, fontweight=weight, zorder=3, linespacing=1.35)
    return x, y


def _arrow(ax: plt.Axes, start: tuple[float, float], end: tuple[float, float],
           color: str = MUTED, style: str = "-|>") -> None:
    """Draw one connector between two points."""
    ax.annotate(
        "", xy=end, xytext=start,
        arrowprops={"arrowstyle": style, "color": color, "lw": 1.8,
                    "shrinkA": 2, "shrinkB": 2},
        zorder=1,
    )


def figure_pipeline() -> None:
    """The inference pipeline as a diagram rather than an ASCII drawing.

    The slide previously carried this as a monospaced code block. That reads
    badly on a projector -- the box-drawing characters depend on the font
    keeping perfect column alignment, which a presentation theme does not
    guarantee, and the branch structure disappears entirely once a line wraps.
    Drawing it makes the two-line branch -- the project's own contribution --
    visible at a glance instead of buried in the middle of a text block.
    """
    # Khung gần vuông và KHÔNG rộng hơn mức cần. Ô nội dung của layout chỉ
    # khoảng 654 px, nên mỗi phần thừa bề ngang đều biến thành chữ nhỏ đi khi
    # hình được thu vào đó. Bản đầu có một chú thích chạy dài sang phải, kéo
    # hình rộng ra và làm mọi hộp co lại tới mức không đọc nổi từ cuối phòng;
    # chú thích ấy chuyển sang phần chữ của slide.
    fig, ax = plt.subplots(figsize=(7.4, 7.0))
    ax.set_xlim(0.2, 9.8)
    ax.set_ylim(0, 10)
    ax.axis("off")

    wide, tall = 7.2, 0.82
    half = 3.5
    body = 14.5

    top = _box(ax, (5, 9.45), (3.4, 0.68), "Ảnh vào", face="#eef2fb",
               edge=BLUE, color=BLUE, weight="bold", fontsize=body)
    detect = _box(ax, (5, 8.3), (wide, tall), "YOLO11n — phát hiện vùng biển",
                  weight="bold", fontsize=body)
    _arrow(ax, (5, 9.11), (5, 8.71))

    crop = _box(ax, (5, 7.2), (wide, tall), "Cắt vùng biển", fontsize=body)
    _arrow(ax, (5, 7.91), (5, 7.59))

    split = _box(ax, (5, 6.1), (wide, tall),
                 "Phân loại số dòng — tỉ lệ 2,5", weight="bold", fontsize=body)
    _arrow(ax, (5, 6.79), (5, 6.51))

    one = _box(ax, (2.7, 4.8), (half, 0.72), "1 dòng", fontsize=body)
    two = _box(ax, (7.3, 4.8), (half, 0.72), "2 dòng",
               face="#fdeaea", edge=RED, color=RED, weight="bold", fontsize=body)
    _arrow(ax, (4.0, 5.69), (3.1, 5.16))
    _arrow(ax, (6.0, 5.69), (6.9, 5.16), color=RED)

    # Đóng góp kỹ thuật lõi của đồ án: tô riêng để nhìn ra ngay.
    hstack = _box(ax, (7.3, 3.55), (half, 1.0),
                  "nắn hình → tách\n→ ghép ngang",
                  face="#fdeaea", edge=RED, color=RED, weight="bold",
                  fontsize=body - 1.5)
    _arrow(ax, (7.3, 4.44), (7.3, 4.05), color=RED)

    ocr = _box(ax, (5, 2.4), (wide, tall), "PaddleOCR — đọc MỘT lần",
               weight="bold", fontsize=body)
    _arrow(ax, (2.7, 4.44), (4.0, 2.81))
    _arrow(ax, (7.3, 3.05), (6.0, 2.81), color=RED)

    norm = _box(ax, (5, 1.3), (wide, tall),
                "Chuẩn hoá + sửa theo VỊ TRÍ", weight="bold", fontsize=body)
    _arrow(ax, (5, 1.99), (5, 1.71))

    _box(ax, (5, 0.35), (wide, 0.74),
         "Lưu CẢ chuỗi thô LẪN chuỗi đã sửa",
         face="#eef2fb", edge=BLUE, color=BLUE, weight="bold", fontsize=body)
    _arrow(ax, (5, 0.89), (5, 0.72))

    del top, detect, crop, split, one, two, hstack, ocr, norm

    save(fig, "fig-pipeline.png")


def figure_architecture() -> None:
    """Năm tầng, và tính chất khiến kiến trúc này đáng bảo vệ.

    Bảng liệt kê tầng thì đọc được, nhưng nó không nói được điều quan trọng
    nhất: tầng AI **không có mũi tên nào đi lên**. Đó mới là thứ cho phép thay
    engine OCR mà không đụng mã API, và nó là một tính chất về *hướng phụ
    thuộc* — vẽ ra thì thấy ngay, liệt kê thì không.
    """
    fig, ax = plt.subplots(figsize=(8.4, 6.6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")

    layers = [
        ("L1 — Trình bày", "React · TypeScript · Tailwind · 3 trang", "#eef2fb", BLUE),
        ("L2 — API", "FastAPI · Swagger · 10 endpoint", "#eef2fb", BLUE),
        ("L3 — Nghiệp vụ", "Detection · Video · History · Storage", "#eef2fb", BLUE),
        ("L4 — AI", "Python thuần · YOLO11 + PaddleOCR + Normalizer", "#fdeaea", RED),
        ("L5 — Dữ liệu", "SQLite · SQLAlchemy · Alembic", "#eef2fb", BLUE),
    ]

    height, gap = 1.5, 0.32
    top_y = 9.0
    centres: list[float] = []
    for index, (name, detail, face, edge) in enumerate(layers):
        y = top_y - index * (height + gap)
        centres.append(y)
        bold = edge == RED
        ax.add_patch(
            patches.FancyBboxPatch(
                (0.6, y - height / 2), 7.4, height,
                boxstyle="round,pad=0.02,rounding_size=0.1",
                facecolor=face, edgecolor=edge,
                linewidth=2.4 if bold else 1.6, zorder=2,
            )
        )
        ax.text(0.95, y + 0.28, name, ha="left", va="center", fontsize=15,
                fontweight="bold", color=edge, zorder=3)
        ax.text(0.95, y - 0.32, detail, ha="left", va="center", fontsize=12,
                color=INK, zorder=3)

    # Mũi tên phụ thuộc: chỉ đi xuống. Đây là toàn bộ luận điểm của slide.
    for upper, lower in zip(centres, centres[1:]):
        _arrow(ax, (8.35, upper - height / 2 + 0.05),
               (8.35, lower + height / 2 - 0.05), color=MUTED)

    ax.annotate(
        "", xy=(9.35, centres[3] - height / 2 - 0.1),
        xytext=(9.35, centres[3] + height / 2 + 0.1),
        arrowprops={"arrowstyle": "-", "color": RED, "lw": 2.2},
    )
    ax.text(9.55, centres[3], "không có\nmũi tên\nĐI LÊN", ha="left", va="center",
            fontsize=12, color=RED, fontweight="bold", linespacing=1.3)
    ax.text(5.0, 0.5, "→ thay engine OCR không đụng một dòng mã API",
            ha="center", va="center", fontsize=13.5, color=INK, fontweight="bold")

    save(fig, "fig-architecture.png")


def figure_training_curve() -> None:
    """Đường cong huấn luyện thật, đọc thẳng từ ``results.csv``.

    Slide huấn luyện trước đó chỉ có gạch đầu dòng về cấu hình. Đường cong nói
    được thứ gạch đầu dòng không nói: mô hình **đã hội tụ**, nên 20 epoch là đủ
    chứ không phải dừng non. Đó chính là câu trả lời cho câu hỏi phản biện
    "sao không huấn luyện lâu hơn".
    """
    import csv

    path = REPO_ROOT / "runs" / "final-640-v3" / "results.csv"
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    epochs = [int(float(r["epoch"])) for r in rows]
    m50 = [float(r["metrics/mAP50(B)"]) for r in rows]
    m5095 = [float(r["metrics/mAP50-95(B)"]) for r in rows]

    fig, ax = plt.subplots(figsize=(8.4, 6.2))
    ax.plot(epochs, m50, color=BLUE, lw=2.6, marker="o", ms=4, label="mAP@0.5")
    ax.plot(epochs, m5095, color=RED, lw=2.6, marker="s", ms=4, label="mAP@0.5:0.95")

    # Nhãn ngưỡng đặt BÊN TRONG khung và NGAY TRÊN đường kẻ. Đặt ở mép phải
    # thì bbox_inches='tight' cắt mất một phần, và chúng còn đè lên chú giải.
    ax.axhline(0.90, color=BLUE, ls=":", lw=1.6, alpha=0.7)
    ax.text(1.2, 0.912, "chỉ tiêu mAP@0.5 ≥ 0,90", fontsize=11.5, color=BLUE,
            va="bottom", fontweight="bold")
    ax.axhline(0.65, color=RED, ls=":", lw=1.6, alpha=0.7)
    ax.text(1.2, 0.662, "chỉ tiêu mAP@0.5:0.95 ≥ 0,65", fontsize=11.5, color=RED,
            va="bottom", fontweight="bold")

    # Điểm mà mAP50 thôi tăng: lý lẽ để nói 20 epoch là đủ.
    best = max(range(len(m50)), key=lambda i: m50[i])
    ax.annotate(
        f"bão hoà từ ~epoch 10\nđỉnh {m50[best]:.4f}".replace(".", ","),
        xy=(epochs[best], m50[best]), xytext=(6.0, 0.815),
        fontsize=12, color=INK, fontweight="bold", linespacing=1.35,
        arrowprops={"arrowstyle": "-|>", "color": MUTED, "lw": 1.5},
    )

    ax.set_xlabel("Epoch", fontsize=13)
    ax.set_ylim(0.60, 1.02)
    ax.set_xlim(0.5, 20.8)
    ax.set_xticks([1, 5, 10, 15, 20])
    ax.legend(fontsize=12.5, loc="center right", frameon=False)
    ax.grid(axis="y", color="#e6e9f2", lw=1)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)

    save(fig, "fig-training-curve.png")


def figure_position_rules() -> None:
    """Bộ luật sửa theo vị trí, vẽ trên một chuỗi biển thật.

    "Theo vị trí" là một tính chất **không gian**. Bảng liệt kê luật thì đúng
    nhưng không cho thấy điều cốt lõi: cùng một cặp ký tự ``O``/``0`` bị ép
    theo **hai chiều ngược nhau** ở hai vị trí cách nhau vài ký tự. Vẽ ra thì
    một cái nhìn là hiểu vì sao bảng thay thế toàn cục không dùng được.
    """
    fig, ax = plt.subplots(figsize=(8.6, 6.0))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")

    plate = "59K1-201.73"
    zones = [
        (0.6, 2.4, "#dbe6ff", BLUE, "mã tỉnh", "phải là CHỮ SỐ\n81 mã hợp lệ", "O→0  I→1  S→5"),
        (3.0, 2.2, "#ffe0e0", RED, "sê-ri", "phải là CHỮ CÁI", "0→O  1→I  5→S"),
        (5.2, 4.2, "#dbe6ff", BLUE, "số đăng ký", "phải là CHỮ SỐ", "ép về chữ số"),
    ]

    ax.text(5, 8.9, plate, ha="center", va="center", fontsize=44,
            fontweight="bold", color=INK, family="Consolas")

    for x, width, face, edge, name, rule, fix in zones:
        ax.add_patch(patches.FancyBboxPatch(
            (x, 6.5), width, 1.0,
            boxstyle="round,pad=0.02,rounding_size=0.1",
            facecolor=face, edgecolor=edge, lw=2, zorder=2))
        ax.text(x + width / 2, 7.0, name, ha="center", va="center",
                fontsize=13.5, fontweight="bold", color=edge, zorder=3)
        ax.text(x + width / 2, 5.75, rule, ha="center", va="center",
                fontsize=11.5, color=INK, linespacing=1.3)
        ax.text(x + width / 2, 4.75, fix, ha="center", va="center",
                fontsize=12.5, color=edge, fontweight="bold", family="Consolas")

    # Cùng một cặp ký tự, hai chiều ngược nhau — điểm cốt lõi của slide.
    ax.add_patch(patches.FancyBboxPatch(
        (0.6, 2.5), 8.8, 1.55,
        boxstyle="round,pad=0.02,rounding_size=0.1",
        facecolor="#fff8e6", edgecolor="#c9922a", lw=1.8, zorder=2))
    ax.text(5, 3.62, "Cùng ký tự  O / 0  bị ép theo HAI CHIỀU NGƯỢC NHAU",
            ha="center", va="center", fontsize=13.5, fontweight="bold", color="#8a6414")
    ax.text(5, 2.95, "một bảng thay thế toàn cục sẽ làm hỏng một trong hai vị trí",
            ha="center", va="center", fontsize=12, color=INK)

    ax.add_patch(patches.FancyBboxPatch(
        (0.6, 0.7), 8.8, 1.25,
        boxstyle="round,pad=0.02,rounding_size=0.1",
        facecolor="#f2f4f9", edgecolor=MUTED, lw=1.6, zorder=2))
    ax.text(5, 1.62, "VÙNG CẤM SỬA", ha="center", va="center",
            fontsize=13, fontweight="bold", color=INK)
    ax.text(5, 1.05, "nơi cả chữ và số đều hợp lệ — tuyệt đối không đụng vào",
            ha="center", va="center", fontsize=12, color=MUTED)

    save(fig, "fig-position-rules.png")


def figure_postprocess_gain() -> None:
    """Đóng góp của hậu xử lý, tách theo bố cục biển.

    Con số tổng ``+11,39 điểm`` không nói được điều đáng nói nhất: gần như toàn
    bộ mức tăng dồn vào biển hai dòng. Hai cặp cột cạnh nhau cho thấy ngay bộ
    luật bù đắp đúng chỗ tầng nhận dạng yếu.
    """
    fig, ax = plt.subplots(figsize=(8.4, 6.0))

    groups = ["Toàn tập", "Biển 1 dòng", "Biển 2 dòng"]
    before = [0.6373, 0.9418, 0.5600]
    after = [0.7512, 0.9541, 0.6996]
    # Lấy thẳng từ tệp kết quả. Tự trừ hai số ĐÃ LÀM TRÒN ở trên cho ra 13,96
    # cho biển hai dòng, trong khi mọi tài liệu khác của đồ án ghi 13,97 — một
    # lệch nhỏ nhưng hội đồng nhìn thấy được, và nó khiến hình mâu thuẫn với
    # chính bảng đứng cạnh nó.
    gains = [11.39, 1.23, 13.97]
    positions = range(len(groups))
    width = 0.34

    b1 = ax.bar([p - width / 2 for p in positions], before, width,
                color="#c3cde3", label="trước hậu xử lý (A5)", zorder=3)
    b2 = ax.bar([p + width / 2 for p in positions], after, width,
                color=BLUE, label="sau hậu xử lý (A6)", zorder=3)

    for bars in (b1, b2):
        for bar in bars:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.015,
                    f"{bar.get_height():.4f}".replace(".", ","),
                    ha="center", va="bottom", fontsize=11.5, color=INK)

    for index, (hi, gain) in enumerate(zip(after, gains)):
        colour = RED if gain > 10 else MUTED
        ax.text(index, hi + 0.10, f"+{gain:.2f}".replace(".", ",") + " điểm",
                ha="center", va="bottom", fontsize=14, fontweight="bold",
                color=colour)

    ax.set_xticks(list(positions))
    ax.set_xticklabels(groups, fontsize=13)
    ax.set_ylim(0, 1.18)
    ax.set_yticks([])
    ax.legend(fontsize=12, loc="upper center", ncol=2, frameon=False,
              bbox_to_anchor=(0.5, -0.06))
    ax.tick_params(axis="x", length=0)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(MUTED)

    save(fig, "fig-postprocess-gain.png")


def main() -> int:
    """Render every deck figure.

    Returns:
        Process exit code.
    """
    figure_gap()
    figure_two_line()
    figure_layouts()
    figure_pipeline()
    figure_architecture()
    figure_training_curve()
    figure_position_rules()
    figure_postprocess_gain()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
