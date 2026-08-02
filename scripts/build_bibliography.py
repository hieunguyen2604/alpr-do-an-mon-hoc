"""Đánh số trích dẫn toàn cục và sinh phần *Tài liệu tham khảo* từ ``references.bib``.

Vấn đề đang có
--------------
Mỗi chương đánh số trích dẫn **cục bộ trong chương đó**: Chương 1 dùng ``[1]``
đến ``[18]``, Chương 2 dùng ``[1]`` đến ``[90]``, và cứ thế. Khi bảy tệp được
ghép thành một quyển, ``[1]`` mang **bảy nghĩa khác nhau** — mà không có gì
trong bản in cho người đọc biết điều đó.

Quyển cũng chưa từng có phần *Tài liệu tham khảo*: ``references.bib`` có 232
entry nhưng chưa có gì đọc nó.

Cách giải
---------
Quy ước sẵn có trong các tệp chương đã đủ để giải bài này một cách máy móc: lần
xuất hiện đầu của mỗi số đều kèm khoá BibTeX trong chú thích HTML —
``[28]<!-- jocher_2024_yolo11 -->``. Từ đó suy ra ánh xạ *số cục bộ → khoá*,
rồi cấp lại số **theo thứ tự xuất hiện trong quyển** (đúng chuẩn IEEE).

Một ngoại lệ: Chương 3 tách ra từ §2.8 cũ nên **kế thừa cách đánh số của Chương
2** mà không mang theo phần định nghĩa. Mười sáu số mồ côi ấy tra ngược sang
bảng của Chương 2 — tất cả đều tra được.

Chạy::

    backend/.venv/Scripts/python scripts/build_bibliography.py           # chay kho
    backend/.venv/Scripts/python scripts/build_bibliography.py --apply   # ghi that
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
BIB = ROOT / "docs" / "references.bib"
RA = PAPERS / "ch8-tai-lieu-tham-khao.md"

CHUONG = [
    "ch1-gioi-thieu.md",
    "ch2-co-so-ly-thuyet.md",
    "ch3-khao-sat-lua-chon.md",
    "ch4-phan-tich-thiet-ke.md",
    "ch5-xay-dung-huan-luyen.md",
    "ch6-thuc-nghiem.md",
    "ch7-ket-luan.md",
]

TRICH = re.compile(r"\[(\d{1,3})\]")
TRICH_KHOA = re.compile(r"\[(\d{1,3})\]\s*<!--\s*([a-z][a-z0-9_]*)\s*-->")
FENCE = re.compile(r"^\s*(```|~~~)")


# --------------------------------------------------------------------------
# Doc file .bib
# --------------------------------------------------------------------------

def doc_bib() -> dict[str, dict[str, str]]:
    """Đọc ``references.bib`` thành ``{khoá: {trường: giá trị}}``.

    Bộ phân tích tối giản, đủ cho định dạng của tệp này: mỗi entry mở bằng
    ``@loại{khoá,`` và đóng bằng một dấu ``}`` ở đầu dòng.
    """
    ra: dict[str, dict[str, str]] = {}
    khoa = ""
    truong: dict[str, str] = {}
    dem = ""
    for ln in BIB.read_text(encoding="utf-8").splitlines():
        if m := re.match(r"^@(\w+)\{([^,]+),", ln):
            khoa = m.group(2).strip()
            truong = {"__loai__": m.group(1).lower()}
            continue
        if not khoa:
            continue
        if ln.strip() == "}":
            ra[khoa] = truong
            khoa = ""
            continue
        if m := re.match(r"^\s*(\w+)\s*=\s*(.*)$", ln):
            dem = m.group(1).lower()
            truong[dem] = m.group(2).strip()
        elif dem:
            truong[dem] += " " + ln.strip()
    return {k: {a: go(b) for a, b in v.items()} for k, v in ra.items()}


def go(s: str) -> str:
    """Gỡ cú pháp BibTeX: ngoặc nhọn, dấu phẩy cuối, escape và gạch nối kép.

    Thứ tự quan trọng: phải đổi ``---`` trước ``--``, nếu không ``---`` bị cắt
    thành ``–-`` (gạch ngang dài rồi thừa một gạch nối).
    """
    s = s.strip().rstrip(",").strip()
    while s.startswith("{") and s.endswith("}"):
        s = s[1:-1].strip()
    s = s.replace("{", "").replace("}", "")
    s = s.replace("---", "—").replace("--", "–")
    for esc, that in (("\\&", "&"), ("\\%", "%"), ("\\_", "_"), ("\\$", "$"), ("\\#", "#")):
        s = s.replace(esc, that)
    return s


def tac_gia(s: str) -> str:
    """``Last, First and Last, First`` → ``F. Last, F. Last`` (kiểu IEEE)."""
    if not s.strip():
        return ""
    ten = []
    for a in s.split(" and "):
        a = a.strip()
        if "," in a:
            ho, dem_ten = (x.strip() for x in a.split(",", 1))
            viet_tat = " ".join(f"{p[0]}." for p in dem_ten.split() if p)
            ten.append(f"{viet_tat} {ho}".strip())
        else:
            ten.append(a)
    if len(ten) > 6:
        return f"{ten[0]} và cộng sự"
    return ", ".join(ten)


def dinh_dang(e: dict[str, str]) -> str:
    """Kết xuất một entry theo kiểu IEEE, phần nhãn bằng tiếng Việt."""
    p: list[str] = []
    if ten := tac_gia(e.get("author", "")):
        p.append(ten + ",")
    if t := e.get("title"):
        p.append(f'"{t},"')
    loai = e.get("__loai__", "misc")
    if loai == "article":
        if j := e.get("journal"):
            p.append(f"*{j}*,")
        if v := e.get("volume"):
            p.append(f"q. {v},")
        if n := e.get("number"):
            p.append(f"s. {n},")
        if pg := e.get("pages"):
            p.append(f"tr. {pg},")
    elif loai == "inproceedings":
        if b := e.get("booktitle"):
            p.append(f"trong *{b}*,")
        if pub := e.get("publisher"):
            p.append(f"{pub},")
    else:
        if o := e.get("organization") or e.get("publisher") or e.get("institution"):
            p.append(f"{o},")
    p.append(f"{e['year']}." if e.get("year") else "không rõ năm.")
    if doi := e.get("doi"):
        p.append(f"doi: {doi}.")
    elif url := e.get("url"):
        ngay = f" (truy cập ngày {e['urldate']})" if e.get("urldate") else ""
        p.append(f"[Trực tuyến]. Địa chỉ: <{url}>{ngay}.")
    return " ".join(p)


# --------------------------------------------------------------------------
# Danh so toan cuc
# --------------------------------------------------------------------------

def anh_xa(t: str) -> dict[int, str]:
    return {int(n): k for n, k in TRICH_KHOA.findall(t)}


def main() -> None:
    ap = "--apply" in sys.argv
    bib = doc_bib()
    print(f"references.bib: {len(bib)} entry\n")

    goc = {f: (PAPERS / f).read_text(encoding="utf-8") for f in CHUONG}
    cuc_bo = {f: anh_xa(t) for f, t in goc.items()}
    # Chuong 3 tach ra tu §2.8 cu nen ke thua cach danh so cua Chuong 2.
    du_phong = {"ch3-khao-sat-lua-chon.md": cuc_bo["ch2-co-so-ly-thuyet.md"]}

    toan_cuc: dict[str, int] = {}
    thu_tu: list[str] = []
    khong_tra: list[str] = []
    thieu_bib: set[str] = set()
    moi: dict[str, str] = {}

    for f in CHUONG:
        tra = dict(du_phong.get(f, {}))
        tra.update(cuc_bo[f])
        trong_fence = False
        ra_dong: list[str] = []
        for ln in goc[f].splitlines():
            if FENCE.match(ln):
                trong_fence = not trong_fence
                ra_dong.append(ln)
                continue
            if trong_fence:
                ra_dong.append(ln)
                continue

            def thay(m: re.Match[str], _f: str = f, _tra: dict[int, str] = tra) -> str:
                n = int(m.group(1))
                khoa = _tra.get(n)
                if khoa is None:
                    khong_tra.append(f"{_f} [{n}]")
                    return m.group(0)
                if khoa not in bib:
                    thieu_bib.add(khoa)
                if khoa not in toan_cuc:
                    toan_cuc[khoa] = len(toan_cuc) + 1
                    thu_tu.append(khoa)
                return f"[{toan_cuc[khoa]}]"

            ra_dong.append(TRICH.sub(thay, ln))
        moi[f] = "\n".join(ra_dong) + "\n"

    print(f"Trích dẫn khác nhau : {len(toan_cuc)}")
    print(f"Entry .bib không dùng: {len(bib) - len([k for k in toan_cuc if k in bib])}")
    if khong_tra:
        print(f"⚠ KHÔNG tra được {len(khong_tra)}: {khong_tra[:12]}")
    if thieu_bib:
        print(f"⚠ Khoá được trích nhưng KHÔNG có trong .bib ({len(thieu_bib)}): {sorted(thieu_bib)}")

    than = [
        "# TÀI LIỆU THAM KHẢO",
        "",
        "> **Sinh tự động** bằng `scripts/build_bibliography.py` từ `docs/references.bib`. "
        "Không gõ tay. Đánh số theo **thứ tự xuất hiện lần đầu trong quyển** (kiểu IEEE); "
        "chạy lại script sau mỗi lần thêm hoặc đổi chỗ trích dẫn.",
        "",
    ]
    for i, k in enumerate(thu_tu, 1):
        e = bib.get(k)
        than.append(f"[{i}] {dinh_dang(e) if e else f'**THIẾU trong references.bib:** `{k}`'}")
        than.append("")

    if not ap:
        print("\n8 mục đầu:")
        for d in than[4:20]:
            if d.strip():
                print("  " + d[:150])
        print("\n(chạy khô — thêm --apply để ghi)")
        return

    for f, t in moi.items():
        (PAPERS / f).write_text(t, encoding="utf-8")
    RA.write_text("\n".join(than).rstrip() + "\n", encoding="utf-8")
    print(f"\nĐã ghi {RA.name} ({len(thu_tu)} mục) và đánh số lại 7 tệp chương.")


if __name__ == "__main__":
    main()
