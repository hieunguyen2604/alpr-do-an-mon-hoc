"""Dựng các sơ đồ mermaid trong quyển thành ảnh PNG và thay khối mã bằng ảnh.

Vấn đề
------
Quyển có 24 sơ đồ viết bằng mermaid. Pandoc **không dựng mermaid** — nó xuất
nguyên khối mã ra tệp `.docx`. Hệ quả: bản in **không có hình nào** (0 ảnh nhúng
trong `word/media/`), mà thay vào đó là 167 dòng ``A --> B`` in như văn bản, và
danh mục hình vẽ liệt kê 23 hình không tồn tại.

Đây vừa là lỗi trình bày nghiêm trọng, vừa là một phần lớn số trang: 972 dòng
khối mã chiếm 21% quyển, riêng Chương 4 là 42%.

Cách xử lý
----------
Dựng từng sơ đồ thành PNG bằng ``@mermaid-js/mermaid-cli`` (dùng Chrome sẵn có
trên máy, không tải Chromium), rồi thay khối ``` ```mermaid ``` ``` bằng một
tham chiếu ảnh. Chú thích ``**Hình N.M.**`` nằm ngay dưới **giữ nguyên** — quy
ước đó đã đúng sẵn.

Chạy::

    backend/.venv/Scripts/python scripts/render_mermaid.py           # chay kho
    backend/.venv/Scripts/python scripts/render_mermaid.py --apply   # dung + thay
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

for _l in (sys.stdout, sys.stderr):
    if hasattr(_l, "reconfigure"):
        _l.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
PAPERS = ROOT / "docs" / "papers"
HINH = PAPERS / "figures"

# mermaid-cli duoc cai o thu muc lam viec tam cua phien; cho phep ghi de.
MMDC = Path(os.environ.get("MMDC_CLI", "")) if os.environ.get("MMDC_CLI") else None
CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")

FEN_MO = re.compile(r"^\s*```mermaid\s*$")
FEN_DONG = re.compile(r"^\s*```\s*$")


def tim_mmdc() -> Path:
    """Tìm ``cli.js`` của mermaid-cli — trong kho, hoặc ở thư mục tạm của phiên."""
    if MMDC and MMDC.is_file():
        return MMDC
    ung_vien = [
        ROOT / "node_modules" / "@mermaid-js" / "mermaid-cli" / "src" / "cli.js",
        Path(tempfile.gettempdir()) / "claude",
    ]
    for u in ung_vien:
        if u.is_file():
            return u
        if u.is_dir():
            for p in u.rglob("@mermaid-js/mermaid-cli/src/cli.js"):
                return p
    raise SystemExit(
        "Khong tim thay mermaid-cli. Cai bang:\n"
        "  npm install @mermaid-js/mermaid-cli\n"
        "roi dat bien moi truong MMDC_CLI tro toi src/cli.js"
    )


def tach_khoi(dong: list[str]) -> list[tuple[int, int, list[str]]]:
    """Trả về [(dòng mở, dòng đóng, nội dung sơ đồ)] cho từng khối mermaid."""
    ra: list[tuple[int, int, list[str]]] = []
    i = 0
    while i < len(dong):
        if FEN_MO.match(dong[i]):
            j = i + 1
            while j < len(dong) and not FEN_DONG.match(dong[j]):
                j += 1
            ra.append((i, j, dong[i + 1 : j]))
            i = j
        i += 1
    return ra


def main() -> None:
    ap = "--apply" in sys.argv
    cli = tim_mmdc()
    print(f"mermaid-cli: {cli}")
    if not CHROME.is_file():
        raise SystemExit(f"Khong thay Chrome tai {CHROME}")

    cau_hinh = HINH / "_puppeteer.json"
    if ap:
        HINH.mkdir(parents=True, exist_ok=True)
        cau_hinh.write_text(
            json.dumps({"executablePath": str(CHROME).replace("\\", "/"),
                        "args": ["--no-sandbox", "--disable-dev-shm-usage"]}),
            encoding="utf-8",
        )

    tong = loi = 0
    for f in sorted(PAPERS.glob("ch[1-7]*.md")):
        dong = f.read_text(encoding="utf-8").splitlines()
        khoi = tach_khoi(dong)
        if not khoi:
            continue
        ch = f.name[2]
        print(f"\n{f.name}: {len(khoi)} sơ đồ")
        # Thay tu DUOI len de chi so dong phia tren khong bi xe dich.
        for k, (a, b, noi_dung) in reversed(list(enumerate(khoi, 1))):
            ten = f"fig-ch{ch}-{k:02d}.png"
            tong += 1
            if ap:
                src = HINH / f"{ten}.mmd"
                src.write_text("\n".join(noi_dung) + "\n", encoding="utf-8")
                r = subprocess.run(
                    ["node", str(cli), "-i", str(src), "-o", str(HINH / ten),
                     "-p", str(cau_hinh), "-b", "white", "-s", "2"],
                    capture_output=True, text=True,
                )
                src.unlink(missing_ok=True)
                if not (HINH / ten).is_file():
                    loi += 1
                    print(f"   ✗ {ten}: {r.stderr.strip().splitlines()[-1][:90] if r.stderr.strip() else 'khong ro'}")
                    continue
                kb = (HINH / ten).stat().st_size // 1024
                print(f"   ✓ {ten}  {kb} KB  ({b - a - 1} dòng mã → 1 ảnh)")
                # Khong gan {width=...}: pandoc doc nguon o che do gfm, ma gfm
                # KHONG ho tro link_attributes nen chuoi do se in nguyen van ra
                # ban giay. Kich thuoc in do --dpi cua build_thesis.py quyet dinh.
                dong[a : b + 1] = [f"![]({HINH.name}/{ten})"]
            else:
                print(f"   · {ten}  ({b - a - 1} dòng mã)")
        if ap:
            f.write_text("\n".join(dong) + "\n", encoding="utf-8")

    print(f"\nTổng: {tong} sơ đồ" + (f", {loi} lỗi" if loi else ""))
    if not ap:
        print("(chạy khô — thêm --apply để dựng và thay)")


if __name__ == "__main__":
    main()
