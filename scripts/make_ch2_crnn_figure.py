"""Dung so do CRNN + CTC cho muc co so ly thuyet, bang matplotlib.

Vi sao rieng muc nay dang mot HINH chu khong phai bang: no mo ta mot PHEP BIEN
DOI HINH DANG DU LIEU qua ba tang -- anh 2D thanh chuoi vector 1D, roi chuoi
xac suat theo thoi gian, roi chuoi ky tu. Doc bang chu thi phai tu dung hinh
trong dau; mot hinh noi thang.

Diem mau chot cua CRNN nam o cho ma van xuoi de luot qua: tang tich chap
downsample CHIEU CAO VE 1, bien ban do dac trung thanh chuoi vector theo chieu
rong. Hinh nay ve dung cho do.

Phan CTC minh hoa bang mot vi du that: chuoi tho co ky tu lap va ky hieu tron
(blank), sau khi gop lai cho ra chuoi cuoi.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle  # noqa: E402

GOC = Path(__file__).resolve().parents[1]
HINH = GOC / "docs" / "papers" / "figures"

MUC = "#1f3864"
PHU = "#8faadc"
NHAT = "#dce3f0"
VIEN = "#404040"
XAM = "#7f7f7f"
NHAN = "#c00000"

plt.rcParams.update({"font.family": "Segoe UI", "font.size": 9, "text.color": "#202020"})


def _hop(ax, x, y, w, h, nhan, mau, co=9, dam=True, chu="#202020"):
    """Ve hop bo goc kem nhan. `chu` de doi mau chu khi nen mau dam."""
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0.01,rounding_size=0.02",
        facecolor=mau, edgecolor=VIEN, linewidth=0.9, zorder=2))
    ax.text(x + w / 2, y + h / 2, nhan, ha="center", va="center", color=chu,
            fontsize=co, fontweight="bold" if dam else "normal", zorder=3)


def _ten(ax, x1, x2, y, nhan=None):
    ax.add_patch(FancyArrowPatch((x1, y), (x2, y), arrowstyle="-|>",
                                 mutation_scale=11, linewidth=1.0, color=VIEN,
                                 shrinkA=2, shrinkB=2, zorder=1))
    if nhan:
        ax.text((x1 + x2) / 2, y + 0.10, nhan, ha="center", va="bottom",
                fontsize=7.5, color=XAM)


def ve(dich: Path) -> None:
    fig, ax = plt.subplots(figsize=(7.8, 4.3))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5.4)
    ax.axis("off")

    y = 3.95

    # --- Anh vao: luoi 2D ---
    for c in range(6):
        for r in range(3):
            ax.add_patch(Rectangle((0.30 + c * 0.115, y + r * 0.115), 0.105, 0.105,
                                   facecolor=NHAT, edgecolor=VIEN, lw=0.5, zorder=2))
    ax.text(0.65, y - 0.20, "Ảnh vùng biển\n(2 chiều)", ha="center", va="top", fontsize=8)

    _ten(ax, 1.10, 1.85, y + 0.17)

    # --- Tang tich chap ---
    _hop(ax, 1.90, y - 0.10, 1.75, 0.62, "Tầng tích chập", PHU, co=8.5)
    ax.text(2.78, y - 0.20, "hạ chiều cao về 1", ha="center", va="top",
            fontsize=8, color=NHAN, fontweight="bold")

    _ten(ax, 3.70, 4.35, y + 0.21)

    # --- Chuoi vector 1D ---
    for c in range(6):
        ax.add_patch(Rectangle((4.42 + c * 0.115, y + 0.06), 0.105, 0.30,
                               facecolor=NHAT, edgecolor=VIEN, lw=0.5, zorder=2))
    ax.text(4.77, y - 0.20, "Chuỗi vector\ntheo chiều rộng", ha="center", va="top", fontsize=8)

    _ten(ax, 5.22, 5.85, y + 0.21)

    # --- Bi-LSTM ---
    _hop(ax, 5.90, y - 0.10, 1.65, 0.62, "Bi-LSTM", PHU, co=8.5)
    ax.text(6.72, y - 0.20, "ngữ cảnh hai chiều", ha="center", va="top",
            fontsize=8, color=XAM)

    _ten(ax, 7.60, 8.20, y + 0.21)

    # --- Tang phien ma ---
    _hop(ax, 8.25, y - 0.10, 1.50, 0.62, "Phiên mã\nCTC", MUC, co=8.5, chu="white")
    ax.text(9.00, y - 0.20, "→ chuỗi ký tự", ha="center", va="top", fontsize=8, color=XAM)

    # --- Duong phan cach ---
    ax.plot([0.2, 9.8], [3.30, 3.30], color="#d9d9d9", lw=0.9)

    # --- Phan CTC ---
    ax.text(0.25, 2.92, "Cách CTC gộp chuỗi thô — ví dụ đọc biển  "
            r"$\bf{51G}$", fontsize=9, va="center", color=MUC, fontweight="bold")

    tho = ["5", "5", "—", "1", "—", "—", "G", "G"]
    x0, w = 1.05, 0.62
    for i, k in enumerate(tho):
        mau = "#f2f2f2" if k == "—" else NHAT
        _hop(ax, x0 + i * (w + 0.10), 2.05, w, 0.52, k, mau, co=10)
    ax.text(0.72, 2.31, "thô", ha="right", va="center", fontsize=8.5, color=XAM)
    ax.text(x0 + 8 * (w + 0.10) + 0.10, 2.31,
            "  ký hiệu  —  là trốn (blank)",
            ha="left", va="center", fontsize=8, color=XAM)

    ax.add_patch(FancyArrowPatch((3.2, 1.95), (3.2, 1.52), arrowstyle="-|>",
                                 mutation_scale=11, linewidth=1.0, color=VIEN))
    ax.text(3.40, 1.73, "bỏ ký tự lặp liền kề, rồi bỏ ký hiệu trốn",
            ha="left", va="center", fontsize=8.5)

    for i, k in enumerate(["5", "1", "G"]):
        _hop(ax, x0 + i * (w + 0.10), 0.85, w, 0.52, k, PHU, co=10)
    ax.text(0.72, 1.11, "cuối", ha="right", va="center", fontsize=8.5, color=XAM)

    ax.text(0.25, 0.32,
            "Nhờ ký hiệu trốn, CTC không cần nhãn vị trí từng ký tự — chỉ cần "
            "chuỗi nhãn đúng. Đó là lý do nó\nthành chuẩn cho nhận dạng chuỗi, "
            "và cũng là lý do nó gặp khó với văn bản nhiều dòng (mục 2.4.3).",
            fontsize=8.5, va="top", color="#202020")

    fig.tight_layout()
    fig.savefig(dich, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"[ok] {dich.name}")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out-dir", default=str(HINH))
    a = p.parse_args()
    d = Path(a.out_dir)
    d.mkdir(parents=True, exist_ok=True)
    ve(d / "fig-ch2-crnn-ctc.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())
