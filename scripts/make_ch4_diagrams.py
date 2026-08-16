"""Dung hai so do cho Chuong 4 bang matplotlib, khong can mermaid-cli.

Vi sao khong dung mermaid: may nay khong cai `mermaid-cli`, va cai no keo theo
Chromium ~300 MB chi de ve hai hinh. Matplotlib da co san va da dung cho hai
hinh Chuong 5.

Hai cho duoc chon vi chung dang mo ta CAU TRUC bang van xuoi:

fig-ch4-usecase
    Muc 4.1.2 ten la "So do use case va ba use case chinh" nhung KHONG CO so do
    nao -- chi co van xuoi. Mot muc mang chu "so do" trong tieu de ma thieu so
    do la cho de bi hoi nhat khi bao ve.

fig-ch4-interfaces
    Muc 4.6.1 mo ta ba lop truu tuong va hop dong cua chung bang van xuoi. Day
    la rang buoc kien truc trung tam cua do an (tang AI khong biet gi ve tang
    web), nen no dang duoc mot hinh.

Ten lop va ten phuong thuc lay TRUC TIEP tu ai/inference/interfaces.py va cac
tep cai dat, khong go tay -- de so do khong troi khoi ma khi ma doi.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

GOC = Path(__file__).resolve().parents[1]
HINH = GOC / "docs" / "papers" / "figures"
NGUON = GOC / "ai" / "inference"

MUC = "#1f3864"
PHU = "#8faadc"
NHAT = "#dce3f0"
VIEN = "#404040"
XAM = "#7f7f7f"

plt.rcParams.update({
    "font.family": "Segoe UI",
    "font.size": 9.5,
    "text.color": "#202020",
})


def _hop(ax, x, y, w, h, nhan, mau, dam=False, co=9.5):
    """Ve mot hop bo goc kem nhan o giua."""
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0.012,rounding_size=0.02",
        facecolor=mau, edgecolor=VIEN, linewidth=0.9, zorder=2))
    ax.text(x + w / 2, y + h / 2, nhan, ha="center", va="center",
            fontsize=co, fontweight="bold" if dam else "normal", zorder=3)


def _mui_ten(ax, xy1, xy2, net="-|>", mau=VIEN, kieu="-"):
    ax.add_patch(FancyArrowPatch(
        xy1, xy2, arrowstyle=net, mutation_scale=11, linewidth=1.0,
        color=mau, linestyle=kieu, shrinkA=3, shrinkB=3, zorder=1))


def ve_usecase(dich: Path) -> None:
    """So do use case: hai tac nhan, ba use case chinh, hai use case phu."""
    fig, ax = plt.subplots(figsize=(7.6, 3.5))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4.9)
    ax.axis("off")

    # Tac nhan
    for y, ten in ((3.3, "Người dùng"), (1.2, "Quản trị viên")):
        ax.plot(0.62, y + 0.34, "o", ms=9, mfc="white", mec=VIEN, mew=1.1, zorder=3)
        ax.plot([0.62, 0.62], [y + 0.05, y + 0.28], color=VIEN, lw=1.1, zorder=3)
        ax.plot([0.38, 0.86], [y + 0.20, y + 0.20], color=VIEN, lw=1.1, zorder=3)
        ax.plot([0.62, 0.40], [y + 0.05, y - 0.22], color=VIEN, lw=1.1, zorder=3)
        ax.plot([0.62, 0.84], [y + 0.05, y - 0.22], color=VIEN, lw=1.1, zorder=3)
        ax.text(0.62, y - 0.46, ten, ha="center", va="top", fontsize=9)

    # Ranh gioi he thong
    ax.add_patch(FancyBboxPatch(
        (2.15, 0.25), 7.6, 4.05, boxstyle="round,pad=0.01,rounding_size=0.03",
        facecolor="none", edgecolor=XAM, linewidth=1.0, linestyle=(0, (5, 3)), zorder=0))
    ax.text(5.95, 4.40, "Hệ thống ALPR", ha="center", va="bottom",
            fontsize=9, color=XAM)

    uc = [
        (3.55, "UC-01  Nhận dạng từ ảnh", True),
        (2.55, "UC-02  Nhận dạng từ video", True),
        (1.55, "UC-05  Tra cứu lịch sử", True),
        (0.60, "UC-06  Xem thống kê", False),
    ]
    for y, nhan, chinh in uc:
        _hop(ax, 3.05, y - 0.02, 5.9, 0.66, nhan,
             PHU if chinh else NHAT, dam=chinh)

    for y in (3.55, 2.55, 1.55):
        _mui_ten(ax, (0.98, 3.5), (3.02, y + 0.31), net="-")
    _mui_ten(ax, (0.98, 1.4), (3.02, 0.93), net="-")

    ax.text(5.95, 0.02, "Ba use case tô đậm là use case chính; đường nối thể hiện "
            "quan hệ liên kết giữa tác nhân và use case",
            ha="center", va="bottom", fontsize=8, color=XAM)

    fig.tight_layout()
    fig.savefig(dich, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"[ok] {dich.name}")


def _doc_lop() -> list[tuple[str, str, str]]:
    """Doc ten lop truu tuong, phuong thuc chinh va lop cai dat TU MA NGUON."""
    itf = (NGUON / "interfaces.py").read_text(encoding="utf-8")
    truu = re.findall(r"^class (Base\w+)\(ABC\):(.*?)(?=^class |\Z)", itf, re.S | re.M)
    cai: dict[str, str] = {}
    for f in NGUON.glob("*.py"):
        for m in re.finditer(r"^class (\w+)\((Base\w+)\):", f.read_text(encoding="utf-8"), re.M):
            cai[m.group(2)] = m.group(1)
    ra = []
    for ten, than in truu:
        pt = [p for p in re.findall(r"^    def (\w+)\(", than, re.M)
              if p not in ("name", "warmup")]
        ra.append((ten, pt[0] if pt else "?", cai.get(ten, "?")))
    return ra


def ve_interfaces(dich: Path) -> None:
    """Ba lop truu tuong, hop dong va lop cai dat tuong ung."""
    lop = _doc_lop()
    fig, ax = plt.subplots(figsize=(7.6, 3.9))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5.0)
    ax.axis("off")

    ax.text(2.55, 4.72, "Hợp đồng (trừu tượng)", ha="center", fontsize=9.5,
            fontweight="bold", color=MUC)
    ax.text(7.45, 4.72, "Cài đặt cụ thể", ha="center", fontsize=9.5,
            fontweight="bold", color=MUC)

    y = 3.55
    for ten, pt, cu_the in lop:
        _hop(ax, 0.55, y, 4.0, 0.92, f"{ten}\n$\\it{{{pt}()}}$", NHAT, dam=True, co=9)
        _hop(ax, 5.45, y, 4.0, 0.92, cu_the, PHU, dam=True, co=9)
        _mui_ten(ax, (5.42, y + 0.46), (4.60, y + 0.46), net="-|>", kieu=(0, (5, 3)))
        y -= 1.28

    ax.text(5.02, 0.62, "nét đứt + mũi tên = quan hệ hiện thực hoá (implements)",
            ha="center", fontsize=8, color=XAM)
    ax.text(5.02, 0.20,
            "Đường ống chỉ giữ tham chiếu tới cột trái, nên thay một cài đặt "
            "không đụng phần còn lại",
            ha="center", fontsize=8.5, color="#202020")

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
    ve_usecase(d / "fig-ch4-usecase.png")
    ve_interfaces(d / "fig-ch4-interfaces.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())
