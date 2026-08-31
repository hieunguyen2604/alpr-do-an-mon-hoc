# Bản nộp

Thư mục này gom **bản thành phẩm** của đồ án về một chỗ, để lúc nộp không phải
đi tìm giữa `docs/papers/` và `docs/slides/`, và không đính nhầm tệp.

Nội dung là **bản sao**, không phải bản gốc. Mọi tệp nguồn `.md` và mọi tệp
kết xuất vẫn nằm nguyên chỗ cũ; không có script, liên kết hay tham chiếu chéo
nào bị đổi đường dẫn.

## Có gì trong này

| Tệp | Sinh từ | Nội dung |
|---|---|---|
| `01-do-an-tot-nghiep.pdf` | `docs/papers/thesis-full.pdf` | Quyển đồ án tốt nghiệp đầy đủ, **79 trang** |
| `01-do-an-tot-nghiep.docx` | `docs/papers/thesis-full.docx` | Cùng nội dung, bản Word để hội đồng ghi chú |
| `02-slide-bao-ve.pptx` | `docs/slides/slides.pptx` | Slide bảo vệ ĐATN đầy đủ — **24 slide chính + 4 slide dự phòng** (Chuẩn 15 phút) |
| `04-do-an-mon-hoc.pdf` | `docs/papers/mon-hoc/thesis-full.pdf` | Bản đồ án môn học **Xử lý ảnh và ứng dụng**, **44 trang** |
| `04-do-an-mon-hoc.docx` | `docs/papers/mon-hoc/thesis-full.docx` | Cùng nội dung, bản Word |
| `05-slide-mon-hoc.pptx` | `docs/slides/12-slides-mon-hoc.pptx` | Slide báo cáo môn học, **16 slide** (Chuẩn 7–10 phút) |

Nhóm `01` và nhóm `04` là **hai quyển riêng**, không phải hai phiên bản của cùng
một quyển: khác bố cục, khác cao độ trình bày, khác danh mục tài liệu tham khảo.
Xem `docs/papers/mon-hoc/README.md`.

---

## Cách dựng lại

Thư mục được làm mới ở **mỗi** lần chạy, nên nó không thể âm thầm giữ bản cũ —
đó là lỗi mà một thư mục chép tay luôn mắc phải.

```bash
python scripts/build_thesis.py
python scripts/build_thesis.py --src docs/papers/mon-hoc
python scripts/build_thesis.py --slides docs/slides/12-slides-mon-hoc.md
powershell -File scripts/export_thesis_pdf.ps1
powershell -File scripts/export_thesis_pdf.ps1 -Nguon docs/papers/mon-hoc/thesis-full.docx -Dich docs/papers/mon-hoc/thesis-full.pdf
```

Bước PowerShell là **bắt buộc chạy sau cùng**: nó để Word điền số trang cho mục
lục và hai danh mục rồi ghi ngược vào `.docx`. Chỉ chạy `build_thesis.py` thì
bản `.docx` trong đây sẽ có cột Trang toàn số 0 — script có in cảnh báo khi
điều đó xảy ra.
