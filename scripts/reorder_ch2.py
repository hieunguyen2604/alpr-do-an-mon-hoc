"""Đưa mục *Quy chuẩn biển số xe Việt Nam* lên sớm trong Chương 2.

Vì sao
------
Đề tài là nhận dạng biển số **Việt Nam**, nhưng phần đặc tả quy chuẩn biển số
Việt Nam đang là **§2.6**, nằm sau ba mục lý thuyết chung. Người đọc phải đi qua
lịch sử phương pháp, phân loại hướng tiếp cận và hai mục lý thuyết trước khi gặp
phần đặc thù miền — thứ chi phối gần như mọi quyết định thiết kế về sau.

Chuyển nó lên **§2.2**, ngay sau phần tổng quan bài toán.

Vì sao chuyển được mà không gãy mạch
-------------------------------------
Đã rà: trong 298 dòng của mục này chỉ có **đúng một** tham chiếu ngược lên các
mục sẽ bị đẩy xuống sau nó. Câu đó được sửa lại thành tham chiếu tiến.

Chạy::

    backend/.venv/Scripts/python scripts/reorder_ch2.py           # chay kho
    backend/.venv/Scripts/python scripts/reorder_ch2.py --apply   # ghi that
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

for _l in (sys.stdout, sys.stderr):
    if hasattr(_l, "reconfigure"):
        _l.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
PAPERS = ROOT / "docs" / "papers"
CH2 = PAPERS / "ch2-co-so-ly-thuyet.md"

# muc cu -> muc moi. Chi 2.2..2.6 doi cho; 2.1, 2.7, 2.8 giu nguyen.
DOI = {"2.6": "2.2", "2.2": "2.3", "2.3": "2.4", "2.4": "2.5", "2.5": "2.6"}

HEAD = re.compile(r"^(#{1,6})\s+(.*)$")
SO = re.compile(r"^(\d+(?:\.\d+)+)\.\s*(.*)$")
FENCE = re.compile(r"^\s*(```|~~~)")


def tach_h2(dong: list[str]) -> list[tuple[str, list[str]]]:
    """Cắt tệp thành [(số mục hoặc '', các dòng)] ở cấp H2."""
    ra: list[tuple[str, list[str]]] = [("", [])]
    fence = False
    for ln in dong:
        if FENCE.match(ln):
            fence = not fence
        m = None if fence else HEAD.match(ln)
        if m and len(m.group(1)) == 2:
            sm = SO.match(m.group(2))
            ra.append((sm.group(1) if sm else "", [ln]))
        else:
            ra[-1][1].append(ln)
    return ra


def main() -> None:
    ap = "--apply" in sys.argv
    khoi = tach_h2(CH2.read_text(encoding="utf-8").splitlines())
    co = [k for k, _ in khoi if k]
    print("Thứ tự cũ:", " ".join(co))

    # --- xep lai: 2.6 chen ngay sau 2.1 -----------------------------------
    i26 = next(i for i, (k, _) in enumerate(khoi) if k == "2.6")
    i21 = next(i for i, (k, _) in enumerate(khoi) if k == "2.1")
    b26 = khoi.pop(i26)
    khoi.insert(i21 + 1, b26)

    # --- doi so tieu de ----------------------------------------------------
    moi: list[tuple[str, list[str]]] = []
    for k, dong in khoi:
        if k in DOI:
            cu, mo = k, DOI[k]
            ra_dong = []
            fence = False
            for ln in dong:
                if FENCE.match(ln):
                    fence = not fence
                m = None if fence else HEAD.match(ln)
                if m:
                    sm = SO.match(m.group(2))
                    if sm and (sm.group(1) == cu or sm.group(1).startswith(cu + ".")):
                        ra_dong.append(f"{m.group(1)} {mo}{sm.group(1)[len(cu):]}. {sm.group(2)}")
                        continue
                ra_dong.append(ln)
            moi.append((mo, ra_dong))
        else:
            moi.append((k, dong))
    print("Thứ tự mới:", " ".join(k for k, _ in moi if k))

    ra = [ln for _, d in moi for ln in d]

    # --- danh so lai chu thich bang / hinh theo VI TRI ---------------------
    dem_b = dem_h = 0
    cap_b: dict[str, str] = {}
    cap_h: dict[str, str] = {}
    for ln in ra:
        for m in re.finditer(r"\*\*Bảng (2\.\d+)\.?\*\*", ln):
            dem_b += 1
            cap_b[m.group(1)] = f"2.{dem_b}"
        for m in re.finditer(r"\*+Hình (2\.\d+)\.", ln):
            dem_h += 1
            cap_h[m.group(1)] = f"2.{dem_h}"
    print(f"Chú thích: {sum(a != b for a, b in cap_b.items())}/{len(cap_b)} bảng, "
          f"{sum(a != b for a, b in cap_h.items())}/{len(cap_h)} hình đổi số")

    # --- thay tham chieu tren TOAN BO cac chuong ---------------------------
    QUET = re.compile(
        r"(?P<muc>\b[Mm]ục\s+(?P<ms>2\.\d(?:\.\d+)?)\b)"
        r"|(?P<bang>\b(?P<bw>[Bb]ảng)\s+(?P<bs>2\.\d+)\b)"
        r"|(?P<hinh>\b(?P<hw>[Hh]ình)\s+(?P<hs>2\.\d+)\b)"
        r"|(?P<tran>(?<![\w.\-])(?P<ts>2\.\d\.\d+)(?![\d.]))"
    )
    dem = {"muc": 0, "bang": 0, "hinh": 0, "tran": 0}

    def doi_muc(s: str) -> str | None:
        """2.4.2 -> 2.5.2 ; 2.6 -> 2.2. Trả None nếu không đổi."""
        g = s.split(".")
        goc = ".".join(g[:2])
        return DOI[goc] + s[len(goc):] if goc in DOI else None

    def thay(m: re.Match[str], dong: str) -> str:
        if m.group("muc"):
            v = doi_muc(m.group("ms"))
            if v:
                dem["muc"] += 1
                return f"{m.group(0)[:3]} {v}"
        elif m.group("bang"):
            v = cap_b.get(m.group("bs"))
            if v:
                dem["bang"] += 1
                return f"{m.group('bw')} {v}"
        elif m.group("hinh"):
            v = cap_h.get(m.group("hs"))
            if v:
                dem["hinh"] += 1
                return f"{m.group('hw')} {v}"
        elif m.group("tran"):
            v = doi_muc(m.group("ts"))
            if v:
                dem["tran"] += 1
                return v
        return m.group(0)

    def quet_dong(ln: str) -> str:
        """Không đụng phần SỐ của tiêu đề — nó đã đánh lại ở trên rồi."""
        m = HEAD.match(ln)
        if not m:
            return QUET.sub(lambda x: thay(x, ln), ln)
        sm = SO.match(m.group(2))
        if not sm:
            return ln
        than = QUET.sub(lambda x: thay(x, sm.group(2)), sm.group(2))
        return f"{m.group(1)} {sm.group(1)}. {than}"

    ket: dict[Path, list[str]] = {CH2: [quet_dong(ln) for ln in ra]}
    for f in sorted(PAPERS.glob("ch*.md")):
        if f == CH2:
            continue
        ket[f] = [quet_dong(ln) for ln in f.read_text(encoding="utf-8").splitlines()]

    print("Đã thay: " + ", ".join(f"{k}={v}" for k, v in dem.items()))

    if not ap:
        print("\n(chạy khô — thêm --apply để ghi)")
        return
    for f, d in ket.items():
        f.write_text("\n".join(d).rstrip() + "\n", encoding="utf-8")
    print(f"\nĐã ghi {len(ket)} tệp.")


if __name__ == "__main__":
    main()
