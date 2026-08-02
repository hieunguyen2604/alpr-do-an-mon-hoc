"""Chứng minh việc tái cấu trúc **không làm mất chữ**.

So sánh tập hợp các dòng nội dung (bỏ dòng trống và dòng tiêu đề) giữa hai lần
chụp. Tái cấu trúc chỉ được phép **di chuyển** và **đánh số lại**, tuyệt đối
không được đánh rơi một đoạn nào — mà mất một đoạn giữa 6.639 dòng thì đọc bằng
mắt không bao giờ phát hiện ra.

Chạy::

    ... scripts/check_thesis_conservation.py truoc   # chup truoc khi doi
    ... scripts/check_thesis_conservation.py sau     # chup sau, roi doi chieu
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

for _l in (sys.stdout, sys.stderr):
    if hasattr(_l, "reconfigure"):
        _l.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
PAPERS = ROOT / "docs" / "papers"
# Anh chup la tep tam, KHONG de trong docs/papers — build_thesis.py liet ke tep
# tuong minh nen no khong bi gop nham, nhung mot tep 800 KB nam canh cac chuong
# la thu se bi commit nham som muon.
SNAP = ROOT / "build" / "thesis-conservation.json"

HEAD = re.compile(r"^#{1,6}\s")
# Bo phan bi danh so lai de so sanh dung phan NOI DUNG.
CHUAN = [
    (re.compile(r"\bChương\s+\d+\b"), "«CH»"),
    (re.compile(r"\b[Mm]ục\s+\d+(?:\.\d+){1,2}\b"), "«MUC»"),
    (re.compile(r"\{\{T[\d.]+[a-z]?\}\}"), "«NEO»"),
    (re.compile(r"\b[Bb]ảng\s+T[\d.]+[a-z]?\b"), "«BANGT»"),
    (re.compile(r"\b[HhBb](?:ình|ảng)\s+\d+\.\d+\b"), "«CT»"),
    # Dang tran, phai chuan hoa sau cung — neu chuan hoa truoc thi no an het
    # cac dang co tu dan o tren va lam phep so sanh mat do phan giai.
    (re.compile(r"(?<![\w.\-{])T\d+(?:\.\d+)?[a-z]?\b"), "«T»"),
    (re.compile(r"(?<![\w.\-])\d\.\d{1,2}\.\d{1,2}(?![\d.])"), "«S3»"),
]


def chup() -> Counter[str]:
    c: Counter[str] = Counter()
    for f in sorted(PAPERS.glob("ch*.md")):
        for ln in f.read_text(encoding="utf-8").splitlines():
            s = ln.strip()
            if not s or HEAD.match(s):
                continue
            for pat, rep in CHUAN:
                s = pat.sub(rep, s)
            c[s] += 1
    return c


def main() -> None:
    che_do = sys.argv[1] if len(sys.argv) > 1 else "truoc"
    hien = chup()
    if che_do == "truoc":
        SNAP.parent.mkdir(parents=True, exist_ok=True)
        SNAP.write_text(json.dumps(hien, ensure_ascii=False), encoding="utf-8")
        print(f"Đã chụp {sum(hien.values())} dòng nội dung ({len(hien)} dòng khác nhau).")
        return

    truoc = Counter(json.loads(SNAP.read_text(encoding="utf-8")))
    mat = truoc - hien
    them = hien - truoc
    print(f"Trước: {sum(truoc.values())} dòng · Sau: {sum(hien.values())} dòng\n")
    for ten, d in (("MẤT", mat), ("THÊM", them)):
        print(f"{ten}: {sum(d.values())} dòng")
        for s, n in list(d.items())[:20]:
            print(f"  ×{n}  {s[:150]}")
        if len(d) > 20:
            print(f"  ... còn {len(d) - 20} dòng nữa")
        print()
    sys.exit(1 if (mat or them) else 0)


if __name__ == "__main__":
    main()
