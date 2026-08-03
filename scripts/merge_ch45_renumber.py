"""Đổi số sau khi gộp Chương 4 và Chương 5 — quyển từ 7 chương còn 6.

Bối cảnh
--------
Chương 4 (*Phân tích và thiết kế*) và Chương 5 (*Xây dựng và huấn luyện*) mô tả
**cùng một thứ hai lần**: chương này nói module X *nên* được thiết kế thế nào,
chương kia nói module X *đã* được cài đặt thế nào. Gộp lại thành **Chương 4 —
Thiết kế và cài đặt hệ thống** bỏ được phần trùng lặp đó, và là khoản tiết kiệm
số trang lớn nhất khi đưa quyển từ 231 trang về ~120.

Hệ quả: quyển còn 6 chương, nên hai chương cuối phải lùi số.

Việc script này làm
-------------------
1. Đổi tên tệp: ``ch6-thuc-nghiem`` → Chương 5, ``ch7-ket-luan`` → Chương 6.
2. Đổi số mọi tiêu đề trong hai tệp đó.
3. Thay **mọi tham chiếu chéo** trên toàn quyển, theo ba nguồn ánh xạ:
   - bảng ánh xạ ``4.x`` và ``5.x`` cũ → mục mới, do tác nhân gộp cung cấp
     (đọc từ ``docs/papers/_anhxa-gop.json``);
   - ``6.x`` → ``5.x`` và ``7.x`` → ``6.x``, suy ra máy móc;
   - ``Chương 6`` → ``Chương 5``, ``Chương 7`` → ``Chương 6``.

Dùng **một lượt quét duy nhất** với hàm gọi lại: mỗi vị trí chỉ được chạm đúng
một lần, nên không thể va chạm giữa các phép đổi — cùng kỹ thuật đã dùng ở
``restructure_thesis.py``.

Chạy::

    ... scripts/merge_ch45_renumber.py           # chay kho
    ... scripts/merge_ch45_renumber.py --apply   # ghi that
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

for _l in (sys.stdout, sys.stderr):
    if hasattr(_l, "reconfigure"):
        _l.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
PAPERS = ROOT / "docs" / "papers"
ANH_XA = PAPERS / "_anhxa-gop.json"

DOI_TEN = {
    "ch6-thuc-nghiem.md": ("ch5-thuc-nghiem.md", "6", "5"),
    "ch7-ket-luan.md": ("ch6-ket-luan.md", "7", "6"),
}
CHUONG_MAP = {"6": "5", "7": "6"}

HEAD = re.compile(r"^(#{1,6})\s+(.*)$")
SO = re.compile(r"^(\d+(?:\.\d+)+)\.\s*(.*)$")
FENCE = re.compile(r"^\s*(```|~~~)")


def doc_anh_xa() -> dict[str, str]:
    """Bảng ánh xạ mục cũ → mục mới do tác nhân gộp cung cấp."""
    if not ANH_XA.is_file():
        raise SystemExit(
            f"Khong thay {ANH_XA}.\n"
            "Tep nay chua bang anh xa 4.x/5.x cu -> muc moi, do tac nhan gop sinh ra."
        )
    thoi = json.loads(ANH_XA.read_text(encoding="utf-8"))
    return {str(r["cu"]): str(r["moi"]) for r in thoi if str(r.get("moi", "")).upper() != "BO"}


def main() -> None:
    ap = "--apply" in sys.argv
    gop = doc_anh_xa()
    print(f"Ánh xạ từ tác nhân gộp: {len(gop)} mục")

    # --- doi so tieu de trong hai tep se lui chuong -------------------------
    noi_dung: dict[Path, list[str]] = {}
    for ten, (moi_ten, cu_ch, moi_ch) in DOI_TEN.items():
        p = PAPERS / ten
        if not p.is_file():
            raise SystemExit(f"Khong thay {p}")
        ra: list[str] = []
        fence = False
        for ln in p.read_text(encoding="utf-8").splitlines():
            if FENCE.match(ln):
                fence = not fence
            m = None if fence else HEAD.match(ln)
            if m:
                sm = SO.match(m.group(2))
                if sm and sm.group(1).split(".")[0] == cu_ch:
                    ra.append(f"{m.group(1)} {moi_ch}{sm.group(1)[len(cu_ch):]}. {sm.group(2)}")
                    continue
            ra.append(ln)
        noi_dung[PAPERS / moi_ten] = ra
        # bo sung anh xa muc cua hai chuong nay
        for ln in ra:
            m = HEAD.match(ln)
            if m:
                sm = SO.match(m.group(2))
                if sm and sm.group(1).startswith(moi_ch + "."):
                    gop[cu_ch + sm.group(1)[len(moi_ch):]] = sm.group(1)

    # --- quet toan quyen ----------------------------------------------------
    DAN = r"(?i:xem|ở|tại|theo|nêu ở|trình bày ở|hạn chế|đóng góp|mục|Mục)\s+"
    QUET = re.compile(
        r"(?P<chuong>\bChương\s+(?P<cs>\d+)\b)"
        r"|(?P<muc>\b[Mm]ục\s+(?P<ms>\d+(?:\.\d+){1,2})\b)"
        rf"|(?P<tran>(?<![\w.\-])(?P<ts>\d\.\d{{1,2}}(?:\.\d{{1,2}})?)(?![\d.]))"
    )
    dem = {"chuong": 0, "muc": 0, "tran": 0}
    chua_tra: list[str] = []

    def thay(m: re.Match[str], dong: str) -> str:
        if m.group("chuong"):
            v = CHUONG_MAP.get(m.group("cs"))
            if v:
                dem["chuong"] += 1
                return f"Chương {v}"
        elif m.group("muc"):
            if ".md" in dong[: m.start()]:
                return m.group(0)
            v = gop.get(m.group("ms"))
            if v:
                dem["muc"] += 1
                return f"{m.group(0)[:3]} {v}"
            if m.group("ms").split(".")[0] in ("4", "5", "6", "7"):
                chua_tra.append(m.group("ms"))
        elif m.group("tran"):
            s = m.group("ts")
            # chi doi dang BA thanh phan; dang hai thanh phan de nham voi so
            # phien ban va nguong nen bo qua tru khi co tu dan (nhanh `muc`).
            if s.count(".") == 2 and s in gop:
                dem["tran"] += 1
                return gop[s]
        return m.group(0)

    def quet_dong(ln: str) -> str:
        m = HEAD.match(ln)
        if not m:
            return QUET.sub(lambda x: thay(x, ln), ln)
        sm = SO.match(m.group(2))
        if not sm:
            return ln
        return f"{m.group(1)} {sm.group(1)}. {QUET.sub(lambda x: thay(x, sm.group(2)), sm.group(2))}"

    # Chinh tep chuong gop KHONG duoc ap bang anh xa 4.x/5.x.
    #
    # No da duoc viet lai voi danh so MOI, va cac so moi (4.3, 4.4.3, 4.6…)
    # TRUNG KHOA voi cac muc CU trong bang anh xa: "muc 4.4.3" trong tep moi la
    # "Gioi han cua perceptual hash", nhung khoa 4.4.3 cu tro toi 4.7.2. Ap
    # nguyen bang se bien dung nhung tham chieu vua duoc viet dung thanh sai.
    # Tep nay chi can lui so chuong 6->5 va 7->6.
    QUET_CHUONG = re.compile(
        r"(?P<chuong>\bChương\s+(?P<cs>\d+)\b)"
        r"|(?P<muc>\b[Mm]ục\s+(?P<ms>[67](?:\.\d+){1,2})\b)"
        r"|(?P<tran>(?<![\w.\-])(?P<ts>[67]\.\d{1,2}\.\d{1,2})(?![\d.]))"
    )

    def chi_lui_chuong(ln: str) -> str:
        def _t(m: re.Match[str]) -> str:
            if m.group("chuong"):
                v = CHUONG_MAP.get(m.group("cs"))
                return f"Chương {v}" if v else m.group(0)
            s = m.group("ms") or m.group("ts")
            v = CHUONG_MAP.get(s.split(".")[0])
            if not v:
                return m.group(0)
            moi_s = v + s[1:]
            dem["muc" if m.group("ms") else "tran"] += 1
            return f"{m.group(0)[:3]} {moi_s}" if m.group("ms") else moi_s
        return QUET_CHUONG.sub(_t, ln)

    ket: dict[Path, list[str]] = {}
    for p in sorted(PAPERS.glob("ch*.md")):
        if p.name in DOI_TEN:
            continue
        ham = chi_lui_chuong if p.name == "ch4-phan-tich-thiet-ke.md" else quet_dong
        ket[p] = [ham(l) for l in p.read_text(encoding="utf-8").splitlines()]
    for p, dong in noi_dung.items():
        ket[p] = [quet_dong(l) for l in dong]

    print("Đã thay: " + ", ".join(f"{k}={v}" for k, v in dem.items()))
    if chua_tra:
        from collections import Counter
        print(f"⚠ {len(chua_tra)} tham chiếu KHÔNG tra được: "
              f"{Counter(chua_tra).most_common(15)}")

    if not ap:
        print("\n(chạy khô — thêm --apply để ghi)")
        return

    for p, dong in ket.items():
        p.write_text("\n".join(dong).rstrip() + "\n", encoding="utf-8")
    for ten in DOI_TEN:
        (PAPERS / ten).unlink(missing_ok=True)
    print(f"\nĐã ghi {len(ket)} tệp, xoá {len(DOI_TEN)} tệp cũ.")


if __name__ == "__main__":
    main()
