"""Render the plate-processing chain as one strip of *real* intermediate images.

Why this exists
---------------
Section 3.4 of the report spends ten pages describing what happens to a plate
crop between the detector and the OCR engine: classify by aspect ratio, cut into
two overlapping halves, stack them side by side, then upscale, grey, equalise
and denoise. A reader has to hold all of that in their head.

This script runs one real photograph through the **delivered pipeline
functions** and captures the image after every step, so the whole chain becomes
one picture. It calls :mod:`ai.inference.two_line` directly rather than
reimplementing any of it -- change the CLAHE clip limit or the overlap ratio and
this figure changes with it. A hand-drawn diagram cannot make that promise, and
``docs/slides/figures/fig-two-line.png`` (drawn by ``make_slide_figures.py``) is
exactly such a diagram.

Step order matters and is taken from the shipped code, not from intuition. In
:meth:`~ai.inference.recognizer.PaddleOcrRecognizer.recognize` the line count is
estimated on the **raw crop**, the split and merge happen next, and
``preprocess_plate`` -- upscale, greyscale, CLAHE, bilateral filter -- runs
**after** the merge, on the stacked strip. Deskewing is *not* on this path at
all; it belongs to the failure-retry ladder in ``pipeline.py`` and only runs
once a read has already failed.

Run::

    backend/.venv/Scripts/python scripts/make_pipeline_strip.py
    backend/.venv/Scripts/python scripts/make_pipeline_strip.py --anh demo/images/2dong-2.png
"""

from __future__ import annotations

import argparse
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
    LOWER_HALF_START_RATIO,
    MIN_MERGE_HEIGHT,
    UPPER_HALF_END_RATIO,
    estimate_line_count,
    merge_two_line,
    preprocess_plate,
    split_two_line,
)

# Matches make_slide_figures.py so the two figure sets look like one family.
BLUE = "#1a4fd6"
RED = "#d62728"
INK = "#16233d"
MUTED = "#6b7793"

plt.rcParams.update(
    {
        "font.family": "Segoe UI",
        "font.size": 11,
        "text.color": INK,
        "figure.facecolor": "white",
    }
)

# The recogniser upscales small crops to this height before enhancing them, so
# the figure has to use the same value or the CLAHE panel would be equalising a
# different image than production does.
_UPSCALE_HEIGHT = 64


def _to_rgb(image: np.ndarray) -> np.ndarray:
    """Convert an OpenCV image to RGB for matplotlib.

    Args:
        image: Grayscale or BGR array.

    Returns:
        An RGB array.
    """
    if image.ndim == 2:
        return cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)


def cat_vung_bien(anh: np.ndarray) -> tuple[np.ndarray, tuple[int, int, int, int]]:
    """Locate one plate with the real detector and return its crop.

    Args:
        anh: The scene photograph, BGR.

    Returns:
        ``(crop, (x, y, w, h))`` for the highest-confidence plate.

    Raises:
        SystemExit: If no model is available or no plate is found -- both are
            reasons to stop rather than draw a figure about nothing.
    """
    from ai.inference.config import InferenceConfig
    from ai.inference.detector import YoloPlateDetector

    cau_hinh = InferenceConfig.from_env()
    if not Path(cau_hinh.model_path).is_file():
        raise SystemExit(f"[loi] khong thay trong so: {cau_hinh.model_path}")

    hop = YoloPlateDetector(cau_hinh).detect(anh)
    if not hop:
        raise SystemExit("[loi] khong phat hien duoc bien so nao trong anh")

    tot_nhat = max(hop, key=lambda d: d.confidence).bbox
    x, y, w, h = tot_nhat.x, tot_nhat.y, tot_nhat.width, tot_nhat.height
    return anh[y : y + h, x : x + w].copy(), (x, y, w, h)


def dung_cac_buoc(crop: np.ndarray) -> list[tuple[str, str, np.ndarray]]:
    """Run the crop through the shipped chain, keeping every intermediate.

    Args:
        crop: The plate crop straight from the detector, BGR.

    Returns:
        A list of ``(title, caption, image)`` panels in processing order.
    """
    cao, rong = crop.shape[0], crop.shape[1]
    ti_le = rong / cao
    so_dong = estimate_line_count(crop)

    panels: list[tuple[str, str, np.ndarray]] = [
        (
            "1 · Vùng cắt từ bộ phát hiện",
            f"{rong} × {cao} px · tỉ lệ {ti_le:.2f}",
            crop,
        )
    ]

    if so_dong == 2:
        # Panel 2 annotates rather than transforms: the classification step
        # changes no pixels, it changes which branch the crop takes. Drawing
        # the two cut lines on the crop is what makes that visible.
        danh_dau = _ve_duong_cat(crop)
        panels.append(
            (
                "2 · Ước lượng số dòng",
                f"tỉ lệ {ti_le:.2f} < 2,50 → hai dòng",
                danh_dau,
            )
        )

        tren, duoi = split_two_line(crop)
        panels.append(
            (
                "3 · Tách hai nửa có chồng lấn",
                f"trên {tren.shape[1]}×{tren.shape[0]} · dưới {duoi.shape[1]}×{duoi.shape[0]} px",
                _xep_doc(tren, duoi),
            )
        )

        ghep = merge_two_line(tren, duoi)
        panels.append(
            (
                "4 · Ghép ngang",
                f"{ghep.shape[1]} × {ghep.shape[0]} px · tỉ lệ {ghep.shape[1] / ghep.shape[0]:.2f}"
                f" · một hàng ký tự nhận trọn {ghep.shape[0]} px chiều cao",
                ghep,
            )
        )
    else:
        ghep = crop
        panels.append(
            ("2 · Ước lượng số dòng", f"tỉ lệ {ti_le:.2f} ≥ 2,50 → một dòng, không tách", crop)
        )

    # preprocess_plate does upscale -> grey -> CLAHE -> denoise in one call.
    # Calling it three times with the switches stepped on one at a time gives
    # genuine intermediates from the production function instead of a
    # re-implementation that could drift away from it.
    chung = {"upscale_to_height": _UPSCALE_HEIGHT, "denoise": False}
    xam = preprocess_plate(ghep, apply_clahe=False, **chung)
    clahe = preprocess_plate(ghep, apply_clahe=True, **chung)
    cuoi = preprocess_plate(ghep, upscale_to_height=_UPSCALE_HEIGHT)

    n = len(panels)
    panels += [
        (f"{n + 1} · Phóng đại và chuyển thang xám", f"cao {xam.shape[0]} px · 3 kênh → 1", xam),
        (f"{n + 2} · CLAHE", "giới hạn tương phản 2,0 · lưới ô 8 × 8 · hết mảng chói", clahe),
        (f"{n + 3} · Lọc song phương", "khử nhiễu mà giữ biên · đầu vào của bộ nhận dạng", cuoi),
    ]
    return panels


def _ve_duong_cat(crop: np.ndarray) -> np.ndarray:
    """Draw the two cut lines and shade the overlap band.

    Args:
        crop: The plate crop, BGR.

    Returns:
        A copy of ``crop`` with the split geometry drawn on it.
    """
    ra = crop.copy()
    if ra.ndim == 2:
        ra = cv2.cvtColor(ra, cv2.COLOR_GRAY2BGR)
    cao = ra.shape[0]
    bat_dau = int(LOWER_HALF_START_RATIO * cao)
    ket_thuc = int(UPPER_HALF_END_RATIO * cao)

    lop = ra.copy()
    cv2.rectangle(lop, (0, bat_dau), (ra.shape[1], ket_thuc), (60, 60, 220), thickness=-1)
    ra = cv2.addWeighted(lop, 0.22, ra, 0.78, 0)
    for y in (bat_dau, ket_thuc):
        cv2.line(ra, (0, y), (ra.shape[1], y), (60, 60, 220), 1)
    return ra


def _xep_doc(tren: np.ndarray, duoi: np.ndarray) -> np.ndarray:
    """Stack the two halves with a visible gap, so the split reads as a split.

    Args:
        tren: Upper half.
        duoi: Lower half.

    Returns:
        A single image with the halves separated by a white band.
    """
    rong = max(tren.shape[1], duoi.shape[1])

    def dem(a: np.ndarray) -> np.ndarray:
        if a.ndim == 2:
            a = cv2.cvtColor(a, cv2.COLOR_GRAY2BGR)
        return cv2.copyMakeBorder(
            a, 0, 0, 0, rong - a.shape[1], cv2.BORDER_CONSTANT, value=(255, 255, 255)
        )

    khe = np.full((max(4, tren.shape[0] // 6), rong, 3), 255, dtype=np.uint8)
    return np.vstack((dem(tren), khe, dem(duoi)))


def ve(panels: list[tuple[str, str, np.ndarray]], dich: Path, ket_qua: str | None) -> None:
    """Compose the panels into one figure and write it to disk.

    Args:
        panels: ``(title, caption, image)`` triples in processing order.
        dich: Destination PNG path.
        ket_qua: Final recognised string, or ``None`` when OCR was skipped.
    """
    # Two-part layout, driven by the images themselves. The steps before the
    # merge are near-square crops and the steps after it are wide strips; giving
    # every panel a full-width row made the figure 3,586 px tall and printed at
    # page width it would be unreadable. Squares go side by side in one row,
    # strips stack below at full width.
    #
    # Every panel still keeps its true aspect ratio. That is not cosmetic: the
    # whole point of the figure is that step 4 turns a 1.12 ratio into a 4.42
    # one, and normalising the boxes would erase exactly that.
    NGUONG_DET = 2.0
    hep = [p for p in panels if p[2].shape[1] / p[2].shape[0] < NGUONG_DET]
    det = [p for p in panels if p[2].shape[1] / p[2].shape[0] >= NGUONG_DET]

    RONG = 7.2
    NHAN = 0.66  # inches reserved for the title above and caption below
    so_cot = max(len(hep), 1)

    cao_hang: list[float] = []
    if hep:
        rong_o = RONG / so_cot
        cao_hang.append(max(rong_o * p[2].shape[0] / p[2].shape[1] for p in hep) + NHAN)
    cao_hang += [max(0.42, RONG * p[2].shape[0] / p[2].shape[1]) + NHAN for p in det]

    fig = plt.figure(figsize=(RONG + 0.6, sum(cao_hang)))
    luoi = fig.add_gridspec(len(cao_hang), so_cot, height_ratios=cao_hang, wspace=0.18)

    o: list[plt.Axes] = []
    hang = 0
    if hep:
        o += [fig.add_subplot(luoi[0, i]) for i in range(len(hep))]
        hang = 1
    o += [fig.add_subplot(luoi[hang + i, :]) for i in range(len(det))]

    for ax, (tieu_de, chu_thich, anh) in zip(o, hep + det):
        ax.imshow(_to_rgb(anh))
        ax.set_xticks([])
        ax.set_yticks([])
        for canh in ax.spines.values():
            canh.set_edgecolor(MUTED)
            canh.set_linewidth(0.8)
        ax.set_title(tieu_de, fontsize=11, fontweight="bold", color=BLUE, loc="left", pad=5)
        ax.set_xlabel(chu_thich, fontsize=9, color=MUTED, labelpad=4)

    if ket_qua:
        fig.text(
            0.5,
            0.004,
            f"Kết quả nhận dạng:  {ket_qua}",
            ha="center",
            fontsize=13,
            fontweight="bold",
            color=INK,
            bbox={"facecolor": "#eef2ff", "edgecolor": BLUE, "boxstyle": "round,pad=0.45"},
        )

    fig.tight_layout(rect=(0, 0.03 if ket_qua else 0, 1, 1))
    dich.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(dich, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def doc_ket_qua(anh: np.ndarray) -> str | None:
    """Run the full pipeline once so the figure can end with the real answer.

    Args:
        anh: The scene photograph, BGR.

    Returns:
        The display-formatted plate string, or ``None`` if the pipeline could
        not run. A missing OCR runtime is not a reason to lose the figure.
    """
    try:
        from ai.inference.pipeline import build_default_pipeline

        ket = build_default_pipeline().process(anh)
        if not ket.results:
            return None
        bien = max(ket.results, key=lambda r: r.detection.confidence)
        doc = bien.recognition
        if doc is None:
            return None
        return doc.display_text or doc.text or None
    except Exception as loi:  # noqa: BLE001 - the figure is still worth having
        print(f"[warn] bo qua buoc doc chuoi: {loi}", file=sys.stderr)
        return None


def main(argv: list[str] | None = None) -> int:
    """Entry point.

    Args:
        argv: Optional explicit argument list.

    Returns:
        Process exit code.
    """
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--anh",
        type=Path,
        default=REPO_ROOT / "demo" / "images" / "2dong-1.png",
        help="Anh dau vao (mac dinh: demo/images/2dong-1.png, mot bien hai dong).",
    )
    ap.add_argument(
        "--dich",
        type=Path,
        default=REPO_ROOT / "docs" / "papers" / "figures" / "fig-pipeline-strip.png",
        help="Duong dan PNG dau ra.",
    )
    ap.add_argument(
        "--khong-doc",
        action="store_true",
        help="Bo qua buoc chay OCR (nhanh hon, khong can nap mo hinh nhan dang).",
    )
    args = ap.parse_args(argv)

    anh = cv2.imread(str(args.anh))
    if anh is None:
        raise SystemExit(f"[loi] khong doc duoc anh: {args.anh}")

    crop, hop = cat_vung_bien(anh)
    print(f"[info] hop bao: x={hop[0]} y={hop[1]} w={hop[2]} h={hop[3]}")

    panels = dung_cac_buoc(crop)
    ket_qua = None if args.khong_doc else doc_ket_qua(anh)

    ve(panels, args.dich, ket_qua)
    print(f"[ok] {len(panels)} buoc -> {args.dich}")
    if ket_qua:
        print(f"[ok] ket qua nhan dang: {ket_qua}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
