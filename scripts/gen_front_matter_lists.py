"""Sinh MỤC LỤC, DANH MỤC HÌNH VẼ và DANH MỤC BẢNG BIỂU từ chính nội dung chương.

Vì sao phải sinh thay vì gõ
---------------------------
Ba danh mục này ở đầu quyển đều mang nhãn *"placeholder — sinh tự động khi ghép
quyển"*, nhưng thực tế **chưa có gì sinh chúng**. Hệ quả: chúng đã trôi rất xa
khỏi nội dung thật — mục lục liệt kê những mục không tồn tại (*"2.10. Tóm tắt
chương"*), danh mục hình bỏ trống nguyên Chương 4 và 5.

Một mục lục sai còn tệ hơn không có mục lục, vì nó là thứ hội đồng đọc đầu tiên.

Script này đọc trực tiếp các tệp chương và ghi đè ba mục ``E``, ``F``, ``G``
trong ``01-front-matter.md``. Chạy lại sau mỗi lần đổi cấu trúc::

    backend/.venv/Scripts/python scripts/gen_front_matter_lists.py --apply
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
FRONT = PAPERS / "01-front-matter.md"

CHUONG_H1 = re.compile(r"^#\s+(CHƯƠNG\s+\d+\..*)$")
MUC_H2 = re.compile(r"^##\s+(\d+\.\d+)\.\s+(.*)$")
CAP_HINH = re.compile(r"^\*+Hình (\d+\.\d+)\.\s*(.*?)\**$")
CAP_BANG = re.compile(r"^\*\*Bảng (\d+\.\d+)\.?\*\*\s*(.*)$")
FENCE = re.compile(r"^\s*(```|~~~)")

# Thu tu dong quyen — phai khop CHAPTER_FILENAMES cua build_thesis.py.
CHUONG = [
    "ch1-gioi-thieu.md",
    "ch2-co-so-ly-thuyet.md",
    "ch3-khao-sat-lua-chon.md",
    "ch4-phan-tich-thiet-ke.md",
    "ch5-xay-dung-huan-luyen.md",
    "ch6-thuc-nghiem.md",
    "ch7-ket-luan.md",
]


def don(s: str) -> str:
    """Bỏ đánh dấu Markdown khỏi tiêu đề để danh mục đọc được khi in."""
    s = re.sub(r"\*\*(.+?)\*\*", r"\1", s)
    s = re.sub(r"\*(.+?)\*", r"\1", s)
    s = re.sub(r"`(.+?)`", r"\1", s)
    return s.rstrip(" .*")


def quet() -> tuple[list[str], list[tuple[str, str]], list[tuple[str, str]]]:
    muc_luc: list[str] = []
    hinh: list[tuple[str, str]] = []
    bang: list[tuple[str, str]] = []
    for ten in CHUONG:
        trong_fence = False
        for ln in (PAPERS / ten).read_text(encoding="utf-8").splitlines():
            if FENCE.match(ln):
                trong_fence = not trong_fence
                continue
            if trong_fence:
                continue
            if m := CHUONG_H1.match(ln):
                muc_luc.append("")
                muc_luc.append(don(m.group(1)))
            elif m := MUC_H2.match(ln):
                muc_luc.append(f"    {m.group(1)}. {don(m.group(2))}")
            elif ln.startswith("## ") and not MUC_H2.match(ln):
                muc_luc.append(f"    {don(ln[3:])}")
            elif m := CAP_HINH.match(ln):
                hinh.append((m.group(1), don(m.group(2))))
            elif m := CAP_BANG.match(ln):
                bang.append((m.group(1), don(m.group(2))))
    return muc_luc, hinh, bang


def bang_md(muc: list[tuple[str, str]], nhan: str) -> list[str]:
    ra = [f"| Ký hiệu | Tên {nhan} | Trang |", "|---|---|:---:|"]
    ra += [f"| {nhan.capitalize()} {so} | {ten} | — |" for so, ten in muc]
    return ra


def thay_muc(goc: str, tieu_de: str, than: list[str]) -> str:
    """Thay phần thân của một mục ``## X. TÊN`` bằng nội dung mới."""
    dong = goc.splitlines()
    dau = next(i for i, l in enumerate(dong) if l.startswith(tieu_de))
    cuoi = next((i for i in range(dau + 1, len(dong)) if dong[i].startswith("## ")), len(dong))
    # Giu lai dau phan cach '---' neu co ngay truoc muc ke tiep.
    duoi = dong[cuoi:]
    while duoi and not duoi[0].strip():
        duoi.pop(0)
    return "\n".join(dong[:dau + 1] + [""] + than + ["", "---", ""] + duoi)


def main() -> None:
    ap = "--apply" in sys.argv
    muc_luc, hinh, bang = quet()

    ghi_chu = (
        "> **Sinh tự động** bằng `scripts/gen_front_matter_lists.py` từ chính các "
        "tệp chương. Không gõ tay — chạy lại script sau mỗi lần đổi cấu trúc. Số "
        "trang do Word điền khi xuất bản `.docx`."
    )

    e = [ghi_chu, "", "```"] + [
        "LỜI CAM ĐOAN", "LỜI CẢM ƠN", "MỤC LỤC", "DANH MỤC HÌNH VẼ",
        "DANH MỤC BẢNG BIỂU", "DANH MỤC TỪ VIẾT TẮT", "TÓM TẮT ĐỒ ÁN", "ABSTRACT",
    ] + muc_luc + ["", "TÀI LIỆU THAM KHẢO", "PHỤ LỤC", "```"]

    f = [ghi_chu, "",
         "> **Quy ước đánh số hình:** `Hình <số chương>.<số thứ tự trong chương>`. "
         "Chú thích đặt **phía dưới** hình, căn giữa. Hình lấy hoặc phỏng theo nguồn "
         "khác **bắt buộc** ghi nguồn ngay trong chú thích, kèm ký hiệu `[n]`.", ""
         ] + bang_md(hinh, "hình")

    g = [ghi_chu, "",
         "> **Quy ước đánh số bảng:** `Bảng <số chương>.<số thứ tự trong chương>`. "
         "Chú thích đặt **phía trên** bảng. Bảng tổng hợp số liệu từ nguồn khác bắt "
         "buộc có cột hoặc dòng ghi nguồn kèm ký hiệu `[n]`.", ""
         ] + bang_md(bang, "bảng")

    print(f"Mục lục : {sum(1 for l in muc_luc if l.strip())} dòng")
    print(f"Hình    : {len(hinh)}")
    print(f"Bảng    : {len(bang)}")
    thieu = [f"ch{c}" for c in "1234567"
             if not any(s.startswith(c + ".") for s, _ in bang)]
    if thieu:
        print(f"⚠ Chương không có bảng nào được đánh số: {', '.join(thieu)}")

    if not ap:
        print("\n(chạy khô — thêm --apply để ghi)")
        return

    goc = FRONT.read_text(encoding="utf-8")
    goc = thay_muc(goc, "## E. MỤC LỤC", e)
    goc = thay_muc(goc, "## F. DANH MỤC HÌNH VẼ", f)
    goc = thay_muc(goc, "## G. DANH MỤC BẢNG BIỂU", g)
    FRONT.write_text(goc.rstrip() + "\n", encoding="utf-8")
    print("\nĐã ghi lại ba mục E, F, G của 01-front-matter.md")


if __name__ == "__main__":
    main()
