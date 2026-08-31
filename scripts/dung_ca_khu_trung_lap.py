"""Dung lai mot ca khu trung lap mo THAT tu video demo, kem anh cat doi chung."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2

GOC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GOC))

from ai.inference.config import InferenceConfig  # noqa: E402
from ai.inference.detector import YoloPlateDetector  # noqa: E402
from ai.inference.normalizer import VietnamesePlateNormalizer  # noqa: E402
from ai.inference.pipeline import ALPRPipeline  # noqa: E402
from ai.inference.recognizer import PaddleOcrRecognizer  # noqa: E402
from backend.services.detection_service import DetectionService  # noqa: E402


def dung_duong_ong() -> ALPRPipeline:
    """Dung dung cau hinh cua ban giao hang, doc tu bien moi truong."""
    cfg = InferenceConfig.from_env()
    return ALPRPipeline(
        detector=YoloPlateDetector(cfg),
        recognizer=PaddleOcrRecognizer(cfg),
        normalizer=VietnamesePlateNormalizer(),
    )


def quet(video: Path, buoc: int, gioi_han: int) -> dict:
    """Tra ve {chuoi: (ket_qua_tot_nhat, khung_dau, khung_cuoi, so_lan, anh_cat)}."""
    ong = dung_duong_ong()
    cap = cv2.VideoCapture(str(video))
    if not cap.isOpened():
        raise SystemExit(f"Khong mo duoc {video}")

    gom: dict = {}
    idx = da_xu_ly = 0
    while da_xu_ly < gioi_han:
        ok, khung = cap.read()
        if not ok:
            break
        if idx % buoc == 0:
            for r in ong.process(khung).results:
                chuoi = r.recognition.text
                if not chuoi:
                    continue
                cat = r.plate_image
                cu = gom.get(chuoi)
                if cu is None or r.recognition.confidence > cu[0].recognition.confidence:
                    gom[chuoi] = (r, idx, idx, (cu[3] + 1) if cu else 1, cat)
                else:
                    gom[chuoi] = (cu[0], cu[1], idx, cu[3] + 1, cu[4])
            da_xu_ly += 1
        idx += 1
    cap.release()
    return gom


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--video", default="demo/videos/demo-video-giao-thong.mp4")
    p.add_argument("--step", type=int, default=5, help="Lay 1 khung moi N khung.")
    p.add_argument("--limit", type=int, default=120, help="So khung toi da xu ly.")
    p.add_argument("--out-dir", default="docs/papers/figures")
    p.add_argument("--case", default="", help="Chuoi song sot dung lam ca minh hoa.")
    a = p.parse_args()

    video = GOC / a.video
    print(f"[i] quet {video.name} — moi {a.step} khung, toi da {a.limit} khung")
    gom = quet(video, a.step, a.limit)
    print(f"[i] doc duoc {len(gom)} chuoi khac nhau")

    # Goi dung ham cua ban giao hang
    acc = {k: (v[0], v[1], v[3]) for k, v in gom.items()}
    song_sot = DetectionService._collapse_variants(acc, max_frame_gap=48)
    con = {r.recognition.text for r, _ in song_sot}
    bi_gop = sorted(set(gom) - con)

    print(f"\n[i] sau khi gop: {len(con)} chuoi song sot, {len(bi_gop)} bi gop vao chuoi khac")
    for k in sorted(gom):
        nhan = "GOP VAO" if k in bi_gop else "giu"
        r, d, c, n, _ = gom[k]
        print(f"    {k:14s} conf={r.recognition.confidence:.3f}"
              f"  hop_le={r.recognition.is_valid_format}"
              f"  khung {d}-{c}  x{n}  [{nhan}]")

    if not bi_gop:
        print("\n[!] Khong co cap nao bi gop trong doan nay — thu --step nho hon,")
        print("    --limit lon hon, hoac video khac.")
        return 1

    if not a.case:
        print("\n[i] Chon mot chuoi song sot lam ca minh hoa roi chay lai voi --case.")
        return 0

    thang = a.case
    if thang not in con:
        raise SystemExit(f"{thang} khong phai chuoi song sot")
    # Cac bien the bi gop VAO chuoi nay: cung nhom theo ham that cua ban giao hang
    from backend.services.detection_service import _is_fuzzy_duplicate_plate
    nhom = [k for k in bi_gop if _is_fuzzy_duplicate_plate(k, thang)]
    if not nhom:
        raise SystemExit(f"khong bien the nao gop vao {thang}")

    ve_hinh(gom, thang, nhom, GOC / a.out_dir / f"fig-ch5-dedup-{thang}.png")
    return 0


def ve_hinh(gom: dict, thang: str, nhom: list[str], dich: Path) -> None:
    """Ve mot hinh doi chung: cac bien the bi gop, va ban song sot."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    cot = nhom + [thang]
    fig, axes = plt.subplots(1, len(cot), figsize=(2.1 * len(cot), 2.6))
    if len(cot) == 1:
        axes = [axes]
    for ax, k in zip(axes, cot):
        r, d, c, n, cat = gom[k]
        if cat is not None and cat.size:
            ax.imshow(cv2.cvtColor(cat, cv2.COLOR_BGR2RGB))
        ax.set_xticks([])
        ax.set_yticks([])
        la_thang = k == thang
        for s in ax.spines.values():
            s.set_edgecolor("#1f7a1f" if la_thang else "#b03030")
            s.set_linewidth(2.4 if la_thang else 1.4)
        ax.set_title(
            f"{k}\n{n} khung · tin cậy {r.recognition.confidence:.3f}"
            + ("\n✔ bản giữ lại" if la_thang else ""),
            fontsize=8.5, fontweight="bold" if la_thang else "normal",
            color="#1f7a1f" if la_thang else "#404040", pad=5)
    fig.suptitle(
        f"Khử trùng lặp mờ: {len(nhom)} cách đọc sai được gom vào một bản ghi",
        fontsize=10.5, fontweight="bold", y=1.02)
    fig.tight_layout()
    dich.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(dich, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"[ok] {dich}")


if __name__ == "__main__":
    sys.exit(main())
