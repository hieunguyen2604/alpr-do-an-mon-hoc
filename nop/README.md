# Bản nộp

Thư mục này gom **bản thành phẩm** của đồ án về một chỗ, để lúc nộp không phải
đi tìm giữa `docs/papers/` và `docs/slides/`, và không đính nhầm tệp.

Nội dung là **bản sao**, không phải bản gốc. Mọi tệp nguồn `.md` và mọi tệp
kết xuất vẫn nằm nguyên chỗ cũ; không có script, liên kết hay tham chiếu chéo
nào bị đổi đường dẫn.

## Có gì trong này

| Tệp | Sinh từ | Nội dung |
|---|---|---|
| `01-do-an-tot-nghiep.pdf` | `docs/papers/thesis-full.pdf` | Quyển đồ án, 93 trang |
| `01-do-an-tot-nghiep.docx` | `docs/papers/thesis-full.docx` | Cùng nội dung, bản Word để hội đồng ghi chú |
| `02-slide-bao-ve.pptx` | `docs/slides/slides.pptx` | Slide bảo vệ đầy đủ — 31 slide chính + 7 slide dự phòng |
| `03-slide-bao-cao-ky-thuat.pptx` | `docs/slides/11-slides-ky-thuat.pptx` | Bản gọn theo khuôn báo cáo kỹ thuật, 11 slide |

Poster (`docs/poster/poster.pdf`) **không** nằm ở đây. Muốn thêm thì bổ sung một
dòng vào `BUNDLE_FILES` trong `scripts/build_thesis.py`.

## Cách dựng lại

Thư mục được làm mới ở **mỗi** lần chạy, nên nó không thể âm thầm giữ bản cũ —
đó là lỗi mà một thư mục chép tay luôn mắc phải.

```bash
backend/.venv/Scripts/python.exe scripts/build_thesis.py
backend/.venv/Scripts/python.exe scripts/build_thesis.py --slides docs/slides/11-slides-ky-thuat.md
powershell -File scripts/export_thesis_pdf.ps1
```

Lệnh đầu dựng quyển Word và slide bảo vệ; lệnh hai dựng slide báo cáo kỹ thuật;
lệnh ba dựng PDF bằng Word rồi tự chép sang đây. Cả `build_thesis.py` lẫn
`export_thesis_pdf.ps1` đều cập nhật thư mục này, nên chạy lệnh nào cũng không
để lại bản lệch.

Tệp nào chưa dựng thì bị bỏ qua kèm dòng báo `(chưa có: ...)`, không phải lỗi.

## Vì sao git không theo dõi nội dung

Bốn tệp trên là **bản sao đúng từng byte** của những tệp git đã theo dõi ở
`docs/papers/` và `docs/slides/`. Theo dõi thêm ở đây sẽ nhân đôi 13 MB nhị phân
vào lịch sử git mỗi lần dựng lại, đổi lấy đúng con số không. `.gitignore` vì vậy
bỏ qua nội dung và chỉ giữ lại chính tệp README này.
