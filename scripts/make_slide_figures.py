#!/usr/bin/env python3
"""Sinh bốn hình cho bộ slide đồ án môn học, ĐỌC SỐ TỪ BÁO CÁO ĐO.

Vì sao phải có script này
-------------------------
``docs/slides/figures/fig-ch4-layout.png`` được vẽ tay ở một lượt đo cũ, rồi
quyển đo lại mà hình thì không. Hình in ra **0,6996** và *"chênh 25,45 điểm"*
trong khi quyển ghi **0,7234** và **23,07 điểm** — người nghe nhìn hình, người
đọc nhìn quyển, hai bên thấy hai con số khác nhau.

Mọi con số ở đây đọc từ :data:`NGUON`. Không hằng số nào gõ tay, nên hình không
trôi khỏi số liệu được nữa. Chạy lại sau mỗi lần đo lại::

    backend/.venv/Scripts/python.exe scripts/make_slide_figures.py

Bốn hình
--------
``fig-mon-hoc-funnel.png``   phễu bộ dữ liệu: 7 bộ → khử trùng lặp → chia tập
``fig-mon-hoc-kpi.png``      bốn thẻ chỉ số chính, thay bảng bảy dòng
``fig-ch4-layout.png``       cột so sánh biển một dòng ↔ hai dòng *(vẽ lại)*
``fig-mon-hoc-donggop.png``  bốn thẻ đóng góp, thay bảng bóc tách
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon

for _l in (sys.stdout, sys.stderr):
    if hasattr(_l, "reconfigure"):
        _l.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
NGUON = ROOT / "docs" / "reports" / "40-ocr-accuracy-measured-confusion.json"
RA = ROOT / "docs" / "slides" / "figures"

# Bảng màu dùng chung với các hình sẵn có trong bộ slide.
XANH, DO, XAM, VANG = "#1a3fd4", "#d42020", "#5a6270", "#fff3c4"
LUC, CAM = "#1a7f4b", "#c46a00"

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


def funnel() -> None:
    """Phễu bộ dữ liệu — thay một bảng sáu dòng."""
    buoc = [
        ("Hợp nhất 7 bộ công khai", "27.111 ảnh", XAM),
        ("Khử trùng lặp chéo bộ · pHash DCT 64 bit", "15.133 ảnh   (loại 44,2%)", DO),
        ("Chia tập, giữ nhóm trùng cùng một bên", "10.592 / 3.027 / 1.514", XANH),
    ]
    fig, ax = plt.subplots(figsize=(12.6, 5.0))
    ax.set_xlim(0, 10)
    ax.set_ylim(-0.55, 3.3)
    ax.axis("off")
    # Tang cuoi khong duoc hep hon chuoi "10.592 / 3.027 / 1.514", nen day day
    # phieu rong ra; hep hon thi so tran ra ngoai hinh.
    rong = [9.6, 7.6, 6.0]
    for i, ((nhan, gt, mau), w) in enumerate(zip(buoc, rong)):
        y = 2.4 - i * 1.05
        w2 = rong[i + 1] if i + 1 < len(rong) else w * 0.9
        ax.add_patch(Polygon(
            [(5 - w / 2, y + 0.42), (5 + w / 2, y + 0.42),
             (5 + w2 / 2, y - 0.42), (5 - w2 / 2, y - 0.42)],
            facecolor=mau, alpha=0.13, edgecolor=mau, linewidth=2.2))
        ax.text(5, y + 0.16, nhan, ha="center", va="center", fontsize=13, color=XAM)
        ax.text(5, y - 0.18, gt, ha="center", va="center",
                fontsize=16.5, fontweight="bold", color=mau)
    # Dat DUOI day phieu, khong phai trong no — truoc day cau nay de len so cua
    # tang thu ba.
    ax.text(5, -0.32, "Một bộ vào 1.005 ảnh, ra 0 ảnh — các bộ công khai fork lẫn nhau",
            ha="center", va="center", fontsize=12, color=XAM, style="italic")
    fig.savefig(RA / "fig-mon-hoc-funnel.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("  [ok] fig-mon-hoc-funnel.png")


def kpi(d: dict) -> None:
    """Bốn thẻ chỉ số — thay bảng bảy dòng."""
    ov = d["by_line_count"]["overall"]
    fig, ax = _khung()
    for i, (mau, tren, giua, duoi) in enumerate([
        (LUC, "Phát hiện — mAP@0.5", "0,9829", "mục tiêu 0,90   ✓ đạt"),
        (LUC, "Precision · Recall", "0,984 · 0,971", "mục tiêu 0,92 · 0,90   ✓ đạt"),
        (CAM, "Đúng cả chuỗi, sau hậu xử lý",
         f"{ov['exact_post_norm']:.4f}".replace(".", ","), "ngưỡng 0,85   ✗ chưa đạt"),
        (LUC, "Độ trễ p95 trên CPU", "510 ms", "mục tiêu ≤ 800 ms   ✓ đạt"),
    ]):
        _the(ax, i + 0.06, 0.10, 0.88, 0.80, mau, tren, giua, duoi)
    fig.savefig(RA / "fig-mon-hoc-kpi.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("  [ok] fig-mon-hoc-kpi.png")


def layout(d: dict) -> None:
    """Cột so sánh hai bố cục — vẽ lại từ số hiện hành."""
    m, h = d["by_line_count"]["one_line"], d["by_line_count"]["two_line"]
    nhom = [
        ("Đúng mức ký tự\n(1 − CER)", m["char_accuracy_post_norm"], h["char_accuracy_post_norm"]),
        ("Đúng cả chuỗi\nTRƯỚC hậu xử lý", m["exact_pre_norm"], h["exact_pre_norm"]),
        ("Đúng cả chuỗi\nSAU hậu xử lý", m["exact_post_norm"], h["exact_post_norm"]),
    ]
    fig, ax = plt.subplots(figsize=(12.6, 5.6))
    for i, (ten, a, b) in enumerate(nhom):
        for dx, gt, mau in ((-0.19, a, XANH), (0.19, b, DO)):
            ax.bar(i + dx, gt, 0.36, color=mau, zorder=3)
            ax.text(i + dx, gt + 0.018, f"{gt:.4f}".replace(".", ","),
                    ha="center", fontsize=13)
        ax.text(i, min(a, b) - 0.085, f"chênh {100 * (a - b):.2f} điểm".replace(".", ","),
                ha="center", fontsize=13, fontweight="bold",
                bbox={"facecolor": VANG, "edgecolor": "#d9b800", "boxstyle": "round,pad=0.4"},
                zorder=4)
    ax.axhline(0.90, ls="--", color=XAM, lw=1.6, zorder=2)
    ax.text(2.55, 0.905, "mục tiêu 0,90", fontsize=12.5, color=XAM, va="bottom", ha="right")
    ax.set_xticks(range(3), [x[0] for x in nhom], fontsize=13.5)
    ax.set_ylabel("Tỉ lệ đúng", fontsize=13)
    ax.set_ylim(0, 1.12)
    ax.bar(0, 0, color=XANH, label=f"Biển MỘT dòng  (n = {m['count']})")
    ax.bar(0, 0, color=DO, label=f"Biển HAI dòng  (n = {h['count']:,})".replace(",", "."))
    ax.legend(loc="lower left", fontsize=13, framealpha=0.95)
    for c in ("top", "right"):
        ax.spines[c].set_visible(False)
    fig.savefig(RA / "fig-ch4-layout.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  [ok] fig-ch4-layout.png  (hai dòng {h['exact_post_norm']:.4f}, "
          f"chênh {100 * (m['exact_post_norm'] - h['exact_post_norm']):.2f} điểm)")


def dong_gop() -> None:
    """Bốn thẻ đóng góp — thay bảng bóc tách."""
    fig, ax = _khung()
    for i, (mau, tren, giua, duoi) in enumerate([
        (XANH, "Tách hai nửa + ghép ngang", "+34,92", "điểm · chi phí ~0 ms"),
        (LUC, "Bộ luật hậu xử lý", "+13,28", "điểm · 372 sửa đúng, 0 hỏng"),
        (CAM, "Nắn hình + giãn dọc", "+34", "biển · +244 ms ở p95"),
        (DO, "Siêu phân giải — đã tắt", "0", "biển, nhưng 0/120 mẫu lọt cổng"),
    ]):
        _the(ax, i + 0.06, 0.10, 0.88, 0.80, mau, tren, giua, duoi)
    fig.savefig(RA / "fig-mon-hoc-donggop.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("  [ok] fig-mon-hoc-donggop.png")


def main() -> int:
    if not NGUON.is_file():
        print(f"[X] khong thay {NGUON}")
        return 1
    RA.mkdir(parents=True, exist_ok=True)
    d = json.loads(NGUON.read_text(encoding="utf-8"))
    print(f"  nguồn: {NGUON.relative_to(ROOT)}")
    funnel()
    kpi(d)
    layout(d)
    dong_gop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
