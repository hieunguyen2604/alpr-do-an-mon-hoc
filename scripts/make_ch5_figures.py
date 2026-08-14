"""Dung hai hinh cho Chuong 5 tu so lieu DA DO, khong ve tay con so nao.

Chuong 5 dai 423 dong nhung chi co dung mot hinh -- ma no lai la chuong trinh
bay ket qua, noi doc gia can nhin thay hinh dang cua so lieu chu khong chi doc
bang. Hai hinh o day lam ro hai lap luan kho theo doi nhat khi chi doc chu:

fig-ch5-backends
    Ba nen tang suy luan tren CPU. Diem chinh khong phai "OpenVINO nhanh hon"
    ma la **duoi hep lai**: p99 tu 54,42 ms xuong 25,68 ms. Voi ky luat hang
    doi mot khe o che do thoi gian thuc, duoi hep dang gia hon trung binh thap.

fig-ch5-nfr-p2
    Sau lan do NFR-P2. Day la hinh lam viec nang nhat trong hai hinh: no cho
    thay lan do 02/08 co trung vi gan nhu may ranh nhung duoi gap 6,93 lan --
    mot chu ky KHAC HAN voi tai canh tranh, von nang ca phan bo deu tay. Lap
    luan do viet bang chu thi phai doc ba lan; nhin hinh thi thay ngay.

Nguon so lieu:
    docs/reports/03-cpu-benchmark.json
    docs/reports/37-nfr-p2-*.json, docs/reports/33-runtime-nfr.json
"""

from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

GOC = Path(__file__).resolve().parents[1]
HINH = GOC / "docs" / "papers" / "figures"
BAOCAO = GOC / "docs" / "reports"

MUC = "#1f3864"
PHU = "#8faadc"
NHAN = "#c00000"
XAM = "#7f7f7f"

plt.rcParams.update({
    "font.family": "Segoe UI",
    "font.size": 10,
    "axes.edgecolor": "#404040",
    "axes.labelcolor": "#202020",
    "text.color": "#202020",
    "xtick.color": "#404040",
    "ytick.color": "#404040",
})


def _doc(ten: str) -> dict:
    return json.load(io.open(BAOCAO / ten, encoding="utf-8"))


def ve_nen_tang(dich: Path) -> None:
    """Bieu do cot: do tre bo phat hien tren ba nen tang, theo phan vi."""
    r = _doc("03-cpu-benchmark.json")["results"]
    ten = ["PyTorch", "ONNX Runtime", "OpenVINO"]
    khoa = ["pytorch", "onnx", "openvino"]
    phan_vi = [("p50", "p50_ms"), ("p95", "p95_ms"), ("p99", "p99_ms")]

    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    rong = 0.26
    mau = [MUC, PHU, "#d6dce5"]
    for i, (nhan, k) in enumerate(phan_vi):
        gt = [r[b][k] for b in khoa]
        x = [j + (i - 1) * rong for j in range(3)]
        thanh = ax.bar(x, gt, rong, label=nhan, color=mau[i],
                       edgecolor="#404040", linewidth=0.6)
        for t, v in zip(thanh, gt):
            ax.text(t.get_x() + t.get_width() / 2, v + 0.8, f"{v:.1f}".replace(".", ","),
                    ha="center", va="bottom", fontsize=8)

    ax.set_xticks(range(3))
    ax.set_xticklabels([f"{n}\n{r[k]['mean_ms']:.2f} ms trung bình".replace(".", ",")
                        for n, k in zip(ten, khoa)])
    ax.set_ylabel("Độ trễ mỗi ảnh (ms)")
    ax.set_ylim(0, 62)
    ax.legend(frameon=False, ncol=3, loc="upper right")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#d9d9d9", linewidth=0.6)
    ax.set_axisbelow(True)

    goc = r["pytorch"]["p99_ms"]
    moi = r["openvino"]["p99_ms"]
    ax.annotate(f"đuôi hẹp lại {goc / moi:.1f} lần".replace(".", ","),
                xy=(2 + rong, moi * 0.55), xytext=(1.05, 46), color=NHAN, fontsize=9,
                arrowprops={"arrowstyle": "->", "color": NHAN, "linewidth": 1.1,
                            "shrinkB": 2})

    fig.tight_layout()
    fig.savefig(dich, dpi=200)
    plt.close(fig)
    print(f"[ok] {dich.name}")


def ve_nfr_p2(dich: Path) -> None:
    """Sau lan do NFR-P2: trung vi thap khong cuu duoc thong luong neu duoi dai."""
    lan = [
        ("02/08\nmáy tải nặng", "33-runtime-nfr.json", True),
        ("13/08\nmáy rảnh", "37-nfr-p2-pytorch.json", False),
        ("13/08\nmáy rảnh (2)", "37-nfr-p2-pytorch-lan2.json", False),
        ("ép tải\n6 lõi", "37-nfr-p2-co-tai-canh-tranh.json", False),
        ("ép tải\n12 lõi", "37-nfr-p2-tai-nang.json", False),
        ("OpenVINO\nmáy rảnh", "37-nfr-p2-openvino.json", False),
    ]
    nhan, p50, p95, fps, la_cu = [], [], [], [], []
    for ten, tep, cu in lan:
        d = _doc(tep)["nfr_p2_webcam_fps"]
        m = d["per_frame_latency_ms"]
        nhan.append(ten)
        p50.append(m["p50_ms"])
        p95.append(m["p95_ms"])
        fps.append(d["effective_fps"])
        la_cu.append(cu)

    fig, (tr, du) = plt.subplots(1, 2, figsize=(9.6, 3.8),
                                 gridspec_kw={"width_ratios": [1.35, 1]})

    x = range(len(nhan))
    rong = 0.38
    tr.bar([i - rong / 2 for i in x], p50, rong, label="p50 (trung vị)",
           color=PHU, edgecolor="#404040", linewidth=0.6)
    tr.bar([i + rong / 2 for i in x], p95, rong, label="p95 (đuôi)",
           color=[NHAN if c else MUC for c in la_cu],
           edgecolor="#404040", linewidth=0.6)
    for i, v in enumerate(p95):
        tr.text(i + rong / 2, v + 22, f"{v:.0f}", ha="center", fontsize=8,
                color=NHAN if la_cu[i] else "#202020")
    tr.set_xticks(list(x))
    tr.set_xticklabels(nhan, fontsize=8)
    tr.set_ylabel("Độ trễ mỗi khung (ms)")
    tr.set_ylim(0, 1450)
    tr.legend(frameon=False, fontsize=9)
    tr.spines[["top", "right"]].set_visible(False)
    tr.grid(axis="y", color="#d9d9d9", linewidth=0.6)
    tr.set_axisbelow(True)
    tr.set_title("Trung vị gần như nhau — đuôi thì không", fontsize=10, pad=8)

    ty = [b / a for a, b in zip(p50, p95)]
    mau = [NHAN if c else MUC for c in la_cu]
    du.barh(list(x), ty, 0.6, color=mau, edgecolor="#404040", linewidth=0.6)
    for i, v in enumerate(ty):
        du.text(v + 0.12, i, f"{v:.2f}×".replace(".", ","), va="center", fontsize=9,
                color=NHAN if la_cu[i] else "#202020")
    du.set_yticks(list(x))
    du.set_yticklabels(nhan, fontsize=8)
    du.invert_yaxis()
    du.set_xlabel("Tỉ lệ p95 / p50")
    du.set_xlim(0, 8.4)
    du.axvline(1.25, color=XAM, linestyle="--", linewidth=0.9)
    du.text(1.42, 3.4, "vùng bình thường ≈ 1,2×", fontsize=8, color=XAM,
            rotation=90, va="center", ha="left")
    du.spines[["top", "right"]].set_visible(False)
    du.grid(axis="x", color="#d9d9d9", linewidth=0.6)
    du.set_axisbelow(True)
    du.set_title("Chữ ký của hai hiện tượng khác nhau", fontsize=10, pad=8)

    fig.tight_layout()
    fig.savefig(dich, dpi=200)
    plt.close(fig)
    print(f"[ok] {dich.name}")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out-dir", default=str(HINH))
    a = p.parse_args()
    d = Path(a.out_dir)
    d.mkdir(parents=True, exist_ok=True)
    ve_nen_tang(d / "fig-ch5-backends.png")
    ve_nfr_p2(d / "fig-ch5-nfr-p2.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())
