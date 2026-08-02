"""Gộp 571 biển vàng/xanh vào ngữ liệu nhãn ký tự của đồ án.

Vì sao cần
----------
Ngữ liệu 2.801 biển hiện có gồm **97,68% biển trắng**, 20 vàng, 4 xanh, và
không một biển đỏ hay ngoại giao nào (``docs/reports/17-plate-type-audit.json``).
Hệ quả là mọi con số OCR mà đồ án công bố thực chất là **độ chính xác trên biển
trắng** — một hạn chế phạm vi phải nêu ở mọi phát biểu.

Bộ ``nguyenluanai/license-plate-color`` v4 (CC BY 4.0) bù được phần lớn khoảng
trống đó: 509 biển vàng và 62 biển xanh, mỗi biển có sẵn chuỗi ký tự trong tên
tệp và đã qua validator của chính đồ án. Thẩm định đầy đủ ở
``docs/reports/30-rare-plate-integration.md``.

Bốn bước, và bước nào cũng cần thiết
-------------------------------------
1. **Khử trùng lặp trong bộ mới.** 74 biển xuất hiện nhiều hơn một lần (165
   ảnh). Giữ một ảnh cho mỗi chuỗi biển.
2. **Khử giao với ngữ liệu cũ.** Đúng một biển trùng (``29H03102``). Một biển
   trên 1.570 là không đáng kể, nhưng để lại thì tập kiểm thử không còn sạch.
3. **Chia lại theo BIỂN SỐ, không theo tệp.** Cùng một biển số chụp hai lần mà
   rơi vào hai tập khác nhau thì phép đo đang đo khả năng ghi nhớ.
4. **Gộp, giữ nguyên tỷ lệ chia của ngữ liệu cũ** (79,4% train / 20,4% valid)
   để hai nửa ngữ liệu không lệch nhau về cách chia.

Chạy::

    backend/.venv/Scripts/python scripts/dataset/merge_rare_plates.py
"""

from __future__ import annotations

import argparse
import csv
import random
import sys
from collections import Counter
from pathlib import Path

# Console Windows mac dinh cp1252, khong in duoc tieng Viet co dau. Dat truoc
# moi lenh print de script chay duoc ca khi goi tu cmd.exe lan tu bash.
for _luong in (sys.stdout, sys.stderr):
    if hasattr(_luong, "reconfigure"):
        _luong.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[2]
GOC = ROOT / "datasets" / "annotations" / "plate_labels.csv"
HIEM = ROOT / "datasets" / "annotations" / "plate_labels_rare.csv"
RA = ROOT / "datasets" / "annotations" / "plate_labels_merged.csv"

SEED = 42
TY_LE_TRAIN = 0.794
"""Khớp tỷ lệ của ngữ liệu gốc: 2.224 train / 571 valid trên 2.795 dòng có chia."""

COT = ["image_path", "plate_text", "line_count", "split", "source_dataset", "plate_color"]


def doc(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    parser = argparse.ArgumentParser(prog="merge_rare_plates")
    parser.add_argument("--output", default=str(RA))
    parser.add_argument(
        "--in-place",
        action="store_true",
        help=(
            "Ghi đè plate_labels.csv thay vì tạo tệp mới. Mặc định KHÔNG, để "
            "bộ số đã công bố còn tái lập được cho tới khi có người xem lại."
        ),
    )
    args = parser.parse_args()

    goc = doc(GOC)
    hiem = doc(HIEM)
    print(f"ngữ liệu gốc : {len(goc)} dòng")
    print(f"bộ biển hiếm : {len(hiem)} dòng")

    # --- 1. khử trùng lặp trong bộ mới ------------------------------------
    da_thay: dict[str, dict[str, str]] = {}
    trung = 0
    for row in hiem:
        text = row["plate_text"]
        if text in da_thay:
            trung += 1
            continue
        da_thay[text] = row
    print(f"  1. khử trùng trong bộ mới : bỏ {trung}, còn {len(da_thay)}")

    # --- 2. khử giao với ngữ liệu cũ --------------------------------------
    cu = {r["plate_text"] for r in goc}
    giao = sorted(set(da_thay) & cu)
    for text in giao:
        del da_thay[text]
    print(f"  2. khử giao với ngữ liệu cũ: bỏ {len(giao)} {giao or ''}, còn {len(da_thay)}")

    # --- 3. chia lại theo biển số ------------------------------------------
    bien = sorted(da_thay)
    rng = random.Random(SEED)
    rng.shuffle(bien)
    cat = int(len(bien) * TY_LE_TRAIN)
    chia = {t: ("train" if i < cat else "valid") for i, t in enumerate(bien)}
    print(f"  3. chia lại theo biển số  : {cat} train / {len(bien) - cat} valid")

    # --- 4. gộp -------------------------------------------------------------
    ra: list[dict[str, str]] = []
    for row in goc:
        ra.append({
            "image_path": row["image_path"],
            "plate_text": row["plate_text"],
            "line_count": row["line_count"],
            "split": row["split"],
            "source_dataset": row["source_dataset"],
            # Ngữ liệu cũ không có nhãn màu do người gán. Để trống là "không
            # ghi nhận", không phải "màu trắng" -- 17-plate-type-audit.json đo
            # bằng bộ phân loại chứ không phải nhãn tay, nên chép nó vào đây sẽ
            # biến một phép đo thành một nhãn.
            "plate_color": "",
        })
    for text in bien:
        row = da_thay[text]
        ra.append({
            "image_path": row["image_path"],
            "plate_text": text,
            "line_count": row["line_count"],
            "split": chia[text],
            "source_dataset": row["source_dataset"],
            "plate_color": row["plate_color"],
        })

    out = Path(GOC if args.in_place else args.output)
    with out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COT)
        writer.writeheader()
        writer.writerows(ra)

    mau = Counter(r["plate_color"] or "(không ghi)" for r in ra)
    chia_dem = Counter(r["split"] or "(không chia)" for r in ra)
    print(f"\nngữ liệu gộp : {len(ra)} dòng -> {out}")
    print(f"  theo chia  : {dict(chia_dem)}")
    print(f"  theo màu   : {dict(mau)}")
    hiem_moi = mau.get("yellow", 0) + mau.get("blue", 0)
    print(f"  biển hiếm  : {hiem_moi}/{len(ra)} = {hiem_moi / len(ra) * 100:.1f}% "
          f"(trước khi gộp: 24/2801 = 0,86%)")


if __name__ == "__main__":
    main()
