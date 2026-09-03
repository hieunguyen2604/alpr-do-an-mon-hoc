# Bản nộp — nhánh `do-an-mon-hoc`

Thư mục này gom **bản thành phẩm** của đồ án môn học về một chỗ, để lúc nộp
không phải đi tìm giữa `docs/papers/` và `docs/slides/`, và không đính nhầm tệp.

Nội dung là **bản sao**, không phải bản gốc. Mọi tệp nguồn `.md` và mọi tệp
kết xuất vẫn nằm nguyên chỗ cũ; không có script, liên kết hay tham chiếu chéo
nào bị đổi đường dẫn.

> Nhánh này chỉ giữ đồ án môn học. Gói nộp đồ án tốt nghiệp (quyển + slide
> bảo vệ) nằm trong `nop/` của nhánh `main`.

## Có gì trong này

| Tệp | Sinh từ | Nội dung |
|---|---|---|
| `01-do-an-mon-hoc.pdf` | `docs/papers/mon-hoc/thesis-full.pdf` | Quyển đồ án môn học **Xử lý ảnh và ứng dụng**, **43 trang** |
| `01-do-an-mon-hoc.docx` | `docs/papers/mon-hoc/thesis-full.docx` | Cùng nội dung, bản Word để hội đồng ghi chú |
| `02-slide-mon-hoc.pptx` | `docs/slides/12-slides-mon-hoc.pptx` | Slide báo cáo môn học, **16 slide** (Chuẩn 7–10 phút) |

Quyển này là **quyển riêng**, không phải bản rút gọn của quyển tốt nghiệp:
khác bố cục, khác cao độ trình bày, khác danh mục tài liệu tham khảo.
Xem `docs/papers/mon-hoc/README.md`.

---

## Cách dựng lại

Thư mục được làm mới ở **mỗi** lần chạy, nên nó không thể âm thầm giữ bản cũ —
đó là lỗi mà một thư mục chép tay luôn mắc phải.

```bash
python scripts/build_thesis.py
powershell -File scripts/export_thesis_pdf.ps1
```

(Mặc định trên nhánh này đã trỏ vào bản môn học — không cần `--src` hay `-Nguon`.)

Bước PowerShell là **bắt buộc chạy sau cùng**: nó để Word điền số trang cho mục
lục và hai danh mục rồi ghi ngược vào `.docx`. Chỉ chạy `build_thesis.py` thì
bản `.docx` trong đây sẽ có cột Trang toàn số 0 — script có in cảnh báo khi
điều đó xảy ra.
