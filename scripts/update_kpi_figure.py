from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]
RA = ROOT / "docs" / "slides" / "figures"

XAM = "#5a6270"
LUC = "#1a7f4b"
CAM = "#c46a00"

plt.rcParams.update({
    "font.family": ["Segoe UI", "DejaVu Sans", "sans-serif"],
    "axes.edgecolor": XAM,
    "figure.facecolor": "white",
})

def _the(ax, x, y, w, h, mau, tren, giua, duoi) -> None:
    """Vẽ một thẻ chỉ số: nhãn nhỏ ở trên, số lớn ở giữa, chú thích ở dưới."""
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0.012,rounding_size=0.03",
        facecolor="white", edgecolor=mau, linewidth=2.6, zorder=2))
    ax.text(x + w / 2, y + h * 0.80, tren, ha="center", va="center",
            fontsize=12.5, color=XAM, zorder=3)
    ax.text(x + w / 2, y + h * 0.47, giua, ha="center", va="center",
            fontsize=27, fontweight="bold", color=mau, zorder=3)
    ax.text(x + w / 2, y + h * 0.15, duoi, ha="center", va="center",
            fontsize=11.5, color=XAM, zorder=3)

def _khung(n_the: float = 4):
    fig, ax = plt.subplots(figsize=(13.2, 3.5))
    ax.set_xlim(0, n_the)
    ax.set_ylim(0, 1)
    ax.axis("off")
    return fig, ax

def update_kpi() -> None:
    fig, ax = _khung()
    cards = [
        (LUC, "Phát hiện — mAP@0,5", "0,9829", "Mục tiêu 0,90 — ĐẠT"),
        (LUC, "Precision · Recall", "0,984 · 0,971", "Mục tiêu 0,92 · 0,90 — ĐẠT"),
        (CAM, "Đúng cả chuỗi, sau hậu xử lý", "0,7701", "Ngưỡng 0,85 — CHƯA ĐẠT"),
        (LUC, "Độ trễ p95 trên CPU", "510 ms", "Mục tiêu ≤ 800 ms — ĐẠT"),
    ]
    for i, (mau, tren, giua, duoi) in enumerate(cards):
        _the(ax, i + 0.06, 0.10, 0.88, 0.80, mau, tren, giua, duoi)
    RA.mkdir(parents=True, exist_ok=True)
    out_path = RA / "fig-mon-hoc-kpi.png"
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"[ok] generated {out_path}")

if __name__ == "__main__":
    update_kpi()
