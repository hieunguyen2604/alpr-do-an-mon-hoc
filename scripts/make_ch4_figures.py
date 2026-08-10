"""Two figures for the results chapter of the course-project report.

Chapter 4 carries thirteen tables and no figure at all. Two of its findings are
badly served by that: the reader sees error *counts* without ever seeing what an
error looks like, and the single most important number of the chapter -- the
25.45-point gap between one-line and two-line plates -- sits inside a six-row
table.

Both figures are built from ``docs/reports/27-ocr-accuracy-with-ladder.json``,
which is the run every number in Chapter 4 comes from. Nothing is recomputed
here; the script reads the measured values and the per-sample records so the
figures cannot drift away from the text.

Produces:

* ``fig-ch4-loi.png``    -- six real crops: three the post-processing rescued,
  three still wrong, each with the label and what was read.
* ``fig-ch4-layout.png`` -- one-line versus two-line across three metrics.

Run::

    backend/.venv/Scripts/python scripts/make_ch4_figures.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import cv2
import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

REPO_ROOT: Path = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from ai.evaluation.ocr_accuracy import restore_aspect_ratio  # noqa: E402

KET_QUA: Path = REPO_ROOT / "docs" / "reports" / "27-ocr-accuracy-with-ladder.json"
THU_MUC: Path = REPO_ROOT / "docs" / "papers" / "figures"

BLUE = "#1a4fd6"
RED = "#d62728"
GREEN = "#2a9d5c"
INK = "#16233d"
MUTED = "#6b7793"

plt.rcParams.update(
    {
        "font.family": "Segoe UI",
        "font.size": 11,
        "text.color": INK,
        "figure.facecolor": "white",
        "axes.edgecolor": MUTED,
    }
)


def _gon(chuoi: str) -> str:
    """Strip separators so a raw OCR string can be compared with a label.

    Args:
        chuoi: Raw or normalised plate string.

    Returns:
        Upper-case alphanumerics only.
    """
    return re.sub(r"[^A-Z0-9]", "", (chuoi or "").upper())


def doc_mau() -> tuple[dict, list[dict]]:
    """Load the measurement file.

    Returns:
        ``(whole document, per-sample records)``.

    Raises:
        SystemExit: If the file is missing -- the figures have no other source.
    """
    if not KET_QUA.is_file():
        raise SystemExit(f"[loi] khong thay tep ket qua: {KET_QUA}")
    d = json.loads(KET_QUA.read_text(encoding="utf-8"))
    return d, d["samples"]


def chon_vi_du(mau: list[dict]) -> tuple[list[dict], list[dict]]:
    """Pick three rescued cases and three still-wrong cases.

    Two-line plates are preferred throughout because they are where both the
    gains and the remaining failures are concentrated.

    Args:
        mau: The per-sample records.

    Returns:
        ``(rescued, still wrong)``, three of each.
    """
    cuu, hong = [], []
    for x in mau:
        that, cuoi, tho = x["truth"], x["plate_number"], _gon(x["raw_ocr_text"])
        if not tho:
            continue
        if cuoi == that and tho != that:
            cuu.append(x)
        elif cuoi != that:
            hong.append(x)

    hai_dong = lambda ds: sorted(ds, key=lambda x: (x["line_count"] != 2, len(x["truth"])))

    # One of each failure shape, so the panel is not three copies of the same
    # story. Length tells them apart: shorter than the label means characters
    # were dropped, longer means characters were invented.
    def theo_dang(ds: list[dict], dang: str) -> list[dict]:
        def khop(x: dict) -> bool:
            t, p = len(x["truth"]), len(x["plate_number"])
            return {"thieu": p < t, "thua": p > t, "nham": p == t}[dang]

        return hai_dong([x for x in ds if khop(x)])

    hong_chon = [
        ds[0] for ds in (theo_dang(hong, d) for d in ("nham", "thieu", "thua")) if ds
    ]
    return hai_dong(cuu)[:3], hong_chon[:3]


def _anh(x: dict) -> np.ndarray:
    """Read a crop and undo the corpus's square-framing.

    Args:
        x: One sample record.

    Returns:
        The crop in RGB at a plausible plate aspect ratio.
    """
    im = cv2.imread(x["image_path"])
    im = restore_aspect_ratio(im, x["line_count"])
    return cv2.cvtColor(im, cv2.COLOR_BGR2RGB)


def hinh_loi(mau: list[dict], dich: Path) -> None:
    """Draw the six-panel gallery of rescued and failed reads.

    Args:
        mau: The per-sample records.
        dich: Destination PNG path.
    """
    cuu, hong = chon_vi_du(mau)
    if len(cuu) < 3 or len(hong) < 3:
        raise SystemExit("[loi] khong du vi du de dung hinh")

    fig, axes = plt.subplots(2, 3, figsize=(9.6, 5.4))
    for cot, x in enumerate(cuu + hong):
        ax = axes[0 if cot < 3 else 1][cot % 3]
        ax.imshow(_anh(x))
        ax.set_xticks([])
        ax.set_yticks([])
        duoc_cuu = cot < 3
        for canh in ax.spines.values():
            canh.set_edgecolor(GREEN if duoc_cuu else RED)
            canh.set_linewidth(1.6)

        that, cuoi, tho = x["truth"], x["plate_number"], _gon(x["raw_ocr_text"])
        if duoc_cuu:
            chu = f"nhãn  {that}\nOCR thô  {tho}\nsau hậu xử lý  {cuoi}"
        else:
            chu = f"nhãn  {that}\nđọc ra  {cuoi or '(rỗng)'}"
        ax.set_xlabel(chu, fontsize=9.5, color=INK, labelpad=5, linespacing=1.5)

    axes[0][0].set_title(
        "Ba ca hậu xử lý SỬA ĐƯỢC", fontsize=11.5, fontweight="bold", color=GREEN, loc="left"
    )
    axes[1][0].set_title(
        "Ba ca VẪN SAI sau hậu xử lý", fontsize=11.5, fontweight="bold", color=RED, loc="left"
    )

    # Chu thich duoi moi khung cao ba dong, nen khoang cach mac dinh giua
    # hai hang khong du: tieu de hang duoi dam len chu thich hang tren.
    fig.tight_layout(h_pad=3.2)
    dich.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(dich, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def hinh_layout(theo_dong: dict, dich: Path) -> None:
    """Draw the one-line versus two-line comparison.

    Args:
        theo_dong: The ``by_line_count`` block of the measurement file.
        dich: Destination PNG path.
    """
    mot, hai = theo_dong["one_line"], theo_dong["two_line"]
    nhom = [
        ("Đúng mức ký tự\n(1 − CER)", mot["char_accuracy_post_norm"], hai["char_accuracy_post_norm"]),
        ("Đúng cả chuỗi\nTRƯỚC hậu xử lý", mot["exact_pre_norm"], hai["exact_pre_norm"]),
        ("Đúng cả chuỗi\nSAU hậu xử lý", mot["exact_post_norm"], hai["exact_post_norm"]),
    ]

    x = np.arange(len(nhom))
    rong = 0.34
    fig, ax = plt.subplots(figsize=(8.4, 4.6))

    a = ax.bar(x - rong / 2, [n[1] for n in nhom], rong,
               label=f"Biển MỘT dòng  (n = {mot['count']:,})".replace(",", "."), color=BLUE)
    b = ax.bar(x + rong / 2, [n[2] for n in nhom], rong,
               label=f"Biển HAI dòng  (n = {hai['count']:,})".replace(",", "."), color=RED)

    for thanh in (a, b):
        ax.bar_label(
            thanh,
            labels=[f"{v:.4f}".replace(".", ",") for v in thanh.datavalues],
            fontsize=9.5,
            padding=2,
            color=INK,
        )

    # The gap is the finding; drawing it as a labelled span beats leaving the
    # reader to subtract two bar labels.
    for i, (_, m, h) in enumerate(nhom):
        ax.annotate(
            f"chênh {(m - h) * 100:.2f} điểm".replace(".", ","),
            xy=(i, min(m, h) - 0.085),
            ha="center",
            fontsize=10,
            fontweight="bold",
            color=INK,
            bbox={"facecolor": "#fff6d6", "edgecolor": "#d9b441", "boxstyle": "round,pad=0.3"},
        )

    ax.axhline(0.90, color=MUTED, linestyle="--", linewidth=1.2)
    # Ben phai nhom cuoi la khoang duy nhat phia tren duong nguong con trong.
    ax.text(len(nhom) - 0.55, 0.915, "mục tiêu 0,90", fontsize=9, color=MUTED, ha="left")

    ax.set_xticks(x, [n[0] for n in nhom], fontsize=10.5)
    ax.set_ylim(0, 1.13)
    ax.set_yticks(np.arange(0, 1.01, 0.2))
    ax.set_ylabel("Tỉ lệ đúng", fontsize=10.5)
    ax.legend(loc="lower left", fontsize=10, framealpha=0.95)
    ax.spines[["top", "right"]].set_visible(False)

    fig.tight_layout()
    dich.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(dich, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main() -> int:
    """Entry point.

    Returns:
        Process exit code.
    """
    tai_lieu, mau = doc_mau()

    a = THU_MUC / "fig-ch4-loi.png"
    hinh_loi(mau, a)
    print(f"[ok] hinh cac ca doc sai -> {a}")

    b = THU_MUC / "fig-ch4-layout.png"
    hinh_layout(tai_lieu["by_line_count"], b)
    print(f"[ok] hinh doi chieu bo cuc -> {b}")

    # Bo slide mon hoc dung ca hai hinh nay, va deck resolve `figures/` theo
    # thu muc cua chinh no — mot tep khong phuc vu duoc ca hai cho. Chep o day
    # thay vi de nguoi dung tu chep: mot deck mang hinh cu la thu khong gi bat
    # duoc.
    for tep in (a, b):
        ban_sao = REPO_ROOT / "docs" / "slides" / "figures" / tep.name
        ban_sao.parent.mkdir(parents=True, exist_ok=True)
        ban_sao.write_bytes(tep.read_bytes())
    print("[ok] ban sao cho slide -> docs/slides/figures/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
