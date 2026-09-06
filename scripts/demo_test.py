#!/usr/bin/env python3
"""Chạy đường ống bàn giao trên 39 ảnh demo và đối chiếu với kết quả đã ghi nhận."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import cv2

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from ai.inference.config import InferenceConfig  # noqa: E402
from ai.inference.detector import YoloPlateDetector  # noqa: E402
from ai.inference.normalizer import VietnamesePlateNormalizer  # noqa: E402
from ai.inference.pipeline import ALPRPipeline  # noqa: E402
from ai.inference.recognizer import PaddleOcrRecognizer  # noqa: E402

for _l in (sys.stdout, sys.stderr):
    if hasattr(_l, "reconfigure"):
        _l.reconfigure(encoding="utf-8", errors="replace")

DEMO = _PROJECT_ROOT / "demo"
NHOM = ("1-line", "2-line", "multi-plate")
ANH = (".png", ".jpg", ".jpeg", ".bmp", ".webp")


TRUONG = ("plate", "display", "kind", "color", "valid", "lines")


def chuan(muc: list[dict[str, object]] | None) -> list[tuple[object, ...]]:
    """Rút mỗi biển về sáu trường đo được, quy chuỗi rỗng về None."""
    # Ban ghi co them truong `note` viet tay va dung null o cho he thong tra
    # chuoi rong; so nguyen khoi se bao lech o cho hai ben thuc ra khop nhau.
    return [
        tuple(None if (v := p.get(k)) == "" else v for k in TRUONG)
        for p in (muc or [])
    ]


def doc_anh() -> dict[str, Path]:
    """Gom mọi ảnh demo theo tên tệp — tên tệp là khoá trong expected.json."""
    return {
        p.name: p
        for nhom in NHOM
        for p in sorted((DEMO / nhom).glob("*"))
        if p.suffix.lower() in ANH
    }


def do_mot_bien(ket_qua, chuan_hoa: VietnamesePlateNormalizer) -> dict[str, object]:
    """Rút một biển thành đúng sáu trường mà phiên bản bàn giao trả cho người dùng."""
    # Chuoi hien thi phai dung format_for_display kem upper_char_count y nhu
    # detection_service.display_text — doc thang display_text cua tang AI se ra
    # chuoi khac o bien hai dong, tuc do mot he thong khong phai he thong duoc giao.
    nhan = ket_qua.recognition
    if nhan is None:
        return dict.fromkeys(TRUONG) | {"color": ket_qua.plate_color or None}

    # Chuoi rong van la mot ket qua: bien duoc phat hien, chi khong doc duoc chu.
    # Bon truong con lai VAN co gia tri va bo giao dien van hien chung.

    # Chi 3 hoac 4 moi duoc dung: cot CSDL rang buoc CHECK IN (3,4) va
    # detection_service loai moi gia tri khac truoc khi luu, nen chuoi hien thi
    # cua phien ban ban giao khong bao gio thay gia tri ngoai mien do.
    tren = nhan.upper_char_count if nhan.upper_char_count in (3, 4) else 0
    hien = None
    if nhan.text:
        try:
            hien = chuan_hoa.format_for_display(
                nhan.text,
                line_count=nhan.line_count,
                kind=nhan.kind or None,
                upper_char_count=tren,
            )
        except Exception:  # noqa: BLE001 — trình bày hỏng không được làm hỏng phép đo
            hien = nhan.text
    return {
        "plate": nhan.text or None,
        "display": hien,
        "kind": nhan.kind,
        "color": ket_qua.plate_color or None,
        "valid": nhan.is_valid_format,
        "lines": nhan.line_count,
    }


def dung_duong_ong() -> ALPRPipeline:
    """Dựng đúng đường ống mà máy chủ dựng, để phép đo không đo một hệ thống khác."""
    # from_env(): moi cong tac ALPR_* co hieu luc o day y het luc chay that.
    # Cong cu do tu dung cau hinh rieng la loi da lap bon lan trong do an nay.
    config = InferenceConfig.from_env()
    duong_ong = ALPRPipeline(
        detector=YoloPlateDetector(config),
        recognizer=PaddleOcrRecognizer(config),
        normalizer=VietnamesePlateNormalizer(),
        config=config,
    )
    duong_ong.warmup()
    return duong_ong


def main() -> int:
    bo = argparse.ArgumentParser(description=__doc__)
    bo.add_argument("--ghi-lai", action="store_true",
                    help="Ghi đè expected.json bằng kết quả lượt chạy này")
    args = bo.parse_args()

    moc = json.loads((DEMO / "expected.json").read_text(encoding="utf-8"))
    anh = doc_anh()
    thieu = sorted(set(moc) - set(anh))
    if thieu:
        print(f"[X] expected.json nhắc {len(thieu)} ảnh không có trên đĩa: {thieu[:5]}")
        return 1

    print(f"Đang nạp mô hình từ {InferenceConfig.from_env().model_path} …")
    duong_ong = dung_duong_ong()
    chuan_hoa = VietnamesePlateNormalizer()
    print(f"Đường ống: {duong_ong.name}\n")

    moi: dict[str, list[dict[str, object]]] = {}
    lech: list[str] = []
    khop_nhom: dict[str, list[int]] = {n: [0, 0] for n in NHOM}
    bat_dau = time.perf_counter()

    for ten, duong in anh.items():
        nhom = duong.parent.name
        khung = cv2.imread(str(duong))
        if khung is None:
            print(f"[X] không đọc được ảnh {duong}")
            return 1

        ket_qua = duong_ong.process(khung)
        thuc = [do_mot_bien(r, chuan_hoa) for r in ket_qua.results]
        moi[ten] = thuc

        khop_nhom[nhom][1] += 1
        if chuan(thuc) == chuan(moc.get(ten)):
            khop_nhom[nhom][0] += 1
        else:
            a, b = chuan(moc.get(ten)), chuan(thuc)
            dong = [f"  {ten}"]
            if len(a) != len(b):
                dong.append(f"      số biển: đã ghi {len(a)} · lần này {len(b)}")
            for i, (x, y) in enumerate(zip(a, b)):
                for k, cu, nay in zip(TRUONG, x, y):
                    if cu != nay:
                        dong.append(f"      biển #{i + 1} {k}: {cu!r} -> {nay!r}")
            lech.append("\n".join(dong))

    giay = time.perf_counter() - bat_dau
    tong_khop = sum(v[0] for v in khop_nhom.values())
    tong = sum(v[1] for v in khop_nhom.values())

    print("Đối chiếu với kết quả đã ghi nhận trong demo/expected.json:\n")
    for nhom, (k, n) in khop_nhom.items():
        print(f"  {nhom:<12} {k}/{n} ảnh khớp")
    print(f"\n  Tổng: {tong_khop}/{tong} ảnh khớp · {giay:.1f} s "
          f"({giay / max(tong, 1) * 1000:.0f} ms mỗi ảnh)")

    if lech:
        print(f"\n{len(lech)} ảnh lệch so với bản ghi:")
        for d in lech:
            print(d)

    if args.ghi_lai:
        (DEMO / "expected.json").write_text(
            json.dumps(moi, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"\n[ok] đã ghi lại expected.json theo lượt chạy này ({tong} ảnh)")
        return 0

    return 0 if not lech else 1


if __name__ == "__main__":
    raise SystemExit(main())
