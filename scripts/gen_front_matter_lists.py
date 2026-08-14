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
# Tham so tuy chon: thu muc con chua cac tep chuong, tinh tu docs/papers/.
# Mac dinh la chinh docs/papers/.
_BAN = next((a for a in sys.argv[1:] if not a.startswith("-")), "")
PAPERS = ROOT / "docs" / "papers" / _BAN if _BAN else ROOT / "docs" / "papers"
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
    "ch5-thuc-nghiem.md",
    "ch6-ket-luan.md",
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
    """Thay phần thân của một mục ``## X. TÊN`` bằng nội dung mới.

    Mục không tồn tại thì **trả nguyên văn bản**, không tạo mới. Bản rút gọn đã
    gỡ hẳn các mục E, F, G theo yêu cầu người thực hiện; nếu hàm này dựng lại
    chúng thì mỗi lần chạy script lại làm sống lại phần vừa gỡ.
    """
    dong = goc.splitlines()
    dau = next((i for i, ln in enumerate(dong) if ln.startswith(tieu_de)), None)
    if dau is None:
        return goc
    cuoi = next((i for i in range(dau + 1, len(dong)) if dong[i].startswith("## ")), len(dong))
    # Giu lai dau phan cach '---' neu co ngay truoc muc ke tiep.
    duoi = dong[cuoi:]
    while duoi and not duoi[0].strip():
        duoi.pop(0)
    return "\n".join(dong[:dau + 1] + [""] + than + ["", "---", ""] + duoi)


def main() -> None:
    ap = "--apply" in sys.argv
    muc_luc, hinh, bang = quet()

    # Ghi chu nay danh cho NGUOI SOAN, khong danh cho hoi dong. Phai la chu
    # thich HTML — de o dang chu thuong thi Pandoc in thang no vao quyen, va
    # ban nop se co dong "Khong go tay — chay lai script..." giua Muc luc.
    ghi_chu = (
        "<!-- Sinh tự động bằng scripts/gen_front_matter_lists.py từ chính các tệp\n"
        "     chương. Không sửa tay — chạy lại script sau mỗi lần đổi cấu trúc.\n"
        "     Số trang do Word điền khi xuất .docx. -->"
    )

    # Muc E KHONG chua muc luc ASCII. Word da co truong TOC tu sinh (pandoc
    # --toc); in them mot ban liet ke tay la quyen co HAI muc luc — loi da xay
    # ra that o ban 231 trang. Ban ASCII chi de doi chieu, nam trong chu thich.
    # Truong TOC cua Word, chen THANG vao day duoi dang OpenXML tho.
    #
    # Truoc day muc luc do `pandoc --toc` sinh, va pandoc luon dat no o DAU tai
    # lieu — tuc la TRUOC CA TRANG BIA. Ban 171 trang co hai trang muc luc dung
    # truoc bia, con muc "E. MUC LUC" thi in ra mot muc rong. Chen truong TOC
    # tai cho nhu duoi day dat muc luc dung vi tri cua no va bo luon `--toc`.
    #
    # `\o "1-2"` = lay tieu de cap 1 va 2; `\h` = moi dong la sieu lien ket;
    # `\z` = an so trang o ban Web Layout; `\u` = dung muc luc theo outline.
    # scripts/export_thesis_pdf.ps1 goi Fields.Update() nen so trang duoc dien
    # luc xuat PDF; mo file .docx truc tiep thi bam Ctrl+A roi F9.
    e = [ghi_chu, "",
         "```{=openxml}",
         "<w:p><w:r><w:fldChar w:fldCharType=\"begin\" w:dirty=\"true\"/></w:r>"
         "<w:r><w:instrText xml:space=\"preserve\">"
         r' TOC \o "1-2" \h \z \u '
         "</w:instrText></w:r>"
         "<w:r><w:fldChar w:fldCharType=\"separate\"/></w:r>"
         "<w:r><w:t>Mở tệp trong Word rồi bấm Ctrl+A, F9 để cập nhật mục lục.</w:t></w:r>"
         "<w:r><w:fldChar w:fldCharType=\"end\"/></w:r></w:p>",
         "```", "",
         "<!-- Bản đối chiếu (không in ra):",
         ] + [("     " + ln) if ln.strip() else "" for ln in muc_luc] + ["-->"]

    # Quy uoc danh so cung la chi dan bien soan, khong phai noi dung quyen.
    f = [ghi_chu,
         "<!-- Quy ước: Hình <chương>.<thứ tự>. Chú thích đặt DƯỚI hình, căn giữa.\n"
         "     Hình lấy/phỏng theo nguồn khác bắt buộc ghi nguồn kèm [n]. -->", ""
         ] + bang_md(hinh, "hình")

    g = [ghi_chu,
         "<!-- Quy ước: Bảng <chương>.<thứ tự>. Chú thích đặt TRÊN bảng.\n"
         "     Bảng tổng hợp từ nguồn khác bắt buộc ghi nguồn kèm [n]. -->", ""
         ] + bang_md(bang, "bảng")

    print(f"Mục lục : {sum(1 for ln in muc_luc if ln.strip())} dòng")
    print(f"Hình    : {len(hinh)}")
    print(f"Bảng    : {len(bang)}")
    thieu = [f"ch{c}" for c in "123456"
             if not any(s.startswith(c + ".") for s, _ in bang)]
    if thieu:
        print(f"⚠ Chương không có bảng nào được đánh số: {', '.join(thieu)}")

    if not ap:
        print("\n(chạy khô — thêm --apply để ghi)")
        return

    truoc = FRONT.read_text(encoding="utf-8")
    goc = truoc
    da_ghi: list[str] = []
    for tieu_de, than in (
        ("## E. MỤC LỤC", e),
        ("## F. DANH MỤC HÌNH VẼ", f),
        ("## G. DANH MỤC BẢNG BIỂU", g),
    ):
        moi = thay_muc(goc, tieu_de, than)
        if moi != goc:
            da_ghi.append(tieu_de.split(". ", 1)[1])
        goc = moi

    if goc == truoc:
        # Ba mục E/F/G đã bị gỡ có chủ ý ở đợt rút trang, nên không có gì để
        # ghi. Trước đây chỗ này luôn in "đã ghi lại ba mục" kể cả khi không
        # dòng nào đổi — một thông điệp đánh lừa đúng người chạy nó để kiểm tra.
        print("\nKhông mục nào để ghi — E/F/G không có trong 01-front-matter.md")
        return

    FRONT.write_text(goc.rstrip() + "\n", encoding="utf-8")
    print("\nĐã ghi lại: " + ", ".join(da_ghi))


if __name__ == "__main__":
    main()
