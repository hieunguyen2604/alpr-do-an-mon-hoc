"""Kiểm tra mọi tham chiếu chéo trong luận văn có trỏ tới mục CÓ THẬT không.

Vì sao cần
----------
Quyển đồ án có hơn 500 tham chiếu dạng *"mục 5.6.5"*, *"Chương 3"*, *"bảng
T5.7b"*. Chúng là **văn bản thuần** — không có gì kiểm tra chúng, nên một lần
đổi số mục là đủ để tạo ra hàng chục tham chiếu chết mà không ai biết cho tới
lúc hội đồng lật tới trang đó.

Script này biến chúng thành thứ kiểm được. Chạy TRƯỚC khi tái cấu trúc để biết
hiện trạng, và chạy LẠI sau đó — số lỗi không được tăng.

Chạy::

    backend/.venv/Scripts/python scripts/check_thesis_refs.py
"""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

for _l in (sys.stdout, sys.stderr):
    if hasattr(_l, "reconfigure"):
        _l.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
PAPERS = ROOT / "docs" / "papers"

CHUONG_RE = re.compile(r"^#\s+CHƯƠNG\s+(\d+)", re.M)
MUC_RE = re.compile(r"^#{2,4}\s+(\d+(?:\.\d+)+)\.", re.M)
BANG_RE = re.compile(r"\{\{(T\d+(?:\.\d+)?[a-z]?)\}\}")

# Cac dang tham chieu trong van xuoi. Hai dang cuoi la dang KHONG co tu dan
# ("xem 5.8.1", "o T5.5b") — chung tung song sot qua mot lan doi so vi bo quet
# chi bat dang co "muc"/"bang" dung truoc.
DAN = r"(?:xem|ở|tại|theo|nêu ở|trình bày ở)\s+"
REF_MUC = re.compile(r"mục\s+(\d+\.\d+(?:\.\d+)?)")
REF_CHUONG = re.compile(r"Chương\s+(\d+)")
REF_BANG = re.compile(r"[Bb]ảng\s+(T\d+(?:\.\d+)?[a-z]?)")
REF_TRAN_MUC = re.compile(rf"(?<![\w.]){DAN}(\d\.\d+(?:\.\d+)?)\b")
REF_TRAN_BANG = re.compile(rf"(?<![\w.]){DAN}(T\d+(?:\.\d+)?[a-z]?)\b")


def quet(files: list[Path]) -> tuple[set[str], set[str], set[str]]:
    """Trả về (tập số chương, tập mã mục, tập mã bảng) thực sự tồn tại."""
    chuong: set[str] = set()
    muc: set[str] = set()
    bang: set[str] = set()
    for f in files:
        t = f.read_text(encoding="utf-8")
        chuong |= set(CHUONG_RE.findall(t))
        muc |= set(MUC_RE.findall(t))
        bang |= set(BANG_RE.findall(t))
    return chuong, muc, bang


def main() -> None:
    # Tham so tuy chon: thu muc con chua cac tep chuong, tinh tu docs/papers/.
    # Mac dinh la chinh docs/papers/.
    thu_muc = PAPERS / sys.argv[1] if len(sys.argv) > 1 else PAPERS
    files = sorted(thu_muc.glob("ch*.md"))
    if not files:
        raise SystemExit(f"Khong tim thay tep chuong nao trong {thu_muc}")
    chuong, muc, bang = quet(files)

    print(f"Quét {len(files)} tệp chương")
    print(f"  chương tồn tại : {len(chuong)}")
    print(f"  mục tồn tại    : {len(muc)}")
    print(f"  mã bảng tồn tại: {len(bang)}\n")

    hong: dict[str, list[str]] = defaultdict(list)
    tong = 0

    for f in files:
        for i, dong in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            # Ma neo `{{T6.6c}}` chi duoc nam trong chu thich HTML. Lot ra van
            # xuoi thi no IN NGUYEN VAN ra ban giay — mot lan da xay ra that.
            if "{{" in dong and not dong.lstrip().startswith("<!--"):
                tong += 1
                hong[f.name].append(f"  {i:>5}  mã neo lọt ra văn xuôi: {dong.strip()[:70]}")
            for m in REF_MUC.finditer(dong):
                # "docs/reports/02-....md muc 7.3" tro sang TEP KHAC, khong phai quyen.
                if ".md" in dong[: m.start()]:
                    continue
                tong += 1
                if m.group(1) not in muc:
                    hong[f.name].append(f"  {i:>5}  mục {m.group(1)}")
            for m in REF_CHUONG.finditer(dong):
                tong += 1
                if m.group(1) not in chuong:
                    hong[f.name].append(f"  {i:>5}  Chương {m.group(1)}")
            for m in REF_BANG.finditer(dong):
                tong += 1
                if m.group(1) not in bang:
                    hong[f.name].append(f"  {i:>5}  bảng {m.group(1)}")
            for m in REF_TRAN_BANG.finditer(dong):
                tong += 1
                if m.group(1) not in bang:
                    hong[f.name].append(f"  {i:>5}  (trần) {m.group(0).strip()}")
            for m in REF_TRAN_MUC.finditer(dong):
                # Dang tran de nham voi so lieu ("tren 2.801 bien"), nen chi bao
                # khi so DO GIONG mot ma muc cua ban CU — tuc la mot chuoi sot lai.
                if ".md" in dong[: m.start()] or m.group(1) in muc:
                    continue
                if re.fullmatch(r"\d\.\d{1,2}(\.\d{1,2})?", m.group(1)):
                    tong += 1
                    hong[f.name].append(f"  {i:>5}  (trần) {m.group(0).strip()}")

    # --- Duong dan anh -------------------------------------------------------
    # Cong cu nay von chi kiem tham chieu MUC va BANG, khong kiem anh. Hau qua:
    # mot dot chuan hoa tu ngu tung thay ca ten TEP anh -- "pipeline" thanh
    # "duong ong", "layout" thanh "bo cuc" -- lam hong hai hinh trong ban mon
    # hoc, va khong ai thay vi khong ai mo lai PDF ban do. Mot tham chieu anh
    # chet khong bao loi luc dung: Pandoc van chay, PDF van ra, chi la thieu hinh.
    so_anh = 0
    for f in files:
        for i, dong in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            for m in re.finditer(r"!\[[^\]]*\]\(([^)]+)\)", dong):
                duong = m.group(1).split("#")[0].strip()
                if duong.startswith(("http://", "https://", "data:")):
                    continue
                so_anh += 1
                # Ban mon hoc nam o docs/papers/mon-hoc/ nhung dung chung thu
                # muc anh voi ban chinh, va Pandoc phan giai theo docs/papers/.
                # Vi vay phai thu CA HAI goc, khong chi thu muc cua tep chuong.
                if not ((f.parent / duong).is_file() or (PAPERS / duong).is_file()):
                    hong[f.name].append(f"  {i:>5}  (ảnh) {duong}")

    so_hong = sum(len(v) for v in hong.values())
    print(f"Tham chiếu kiểm được: {tong}")
    print(f"Đường dẫn ảnh kiểm được: {so_anh}")
    print(f"Tham chiếu CHẾT     : {so_hong}\n")

    for ten in sorted(hong):
        print(f"-- {ten} --")
        for d in hong[ten][:25]:
            print(d)
        if len(hong[ten]) > 25:
            print(f"  ... còn {len(hong[ten]) - 25} chỗ nữa")
        print()

    sys.exit(1 if so_hong else 0)


if __name__ == "__main__":
    main()
