# Bản nộp

Thư mục này gom **bản thành phẩm** của đồ án về một chỗ, để lúc nộp không phải
đi tìm giữa `docs/papers/` và `docs/slides/`, và không đính nhầm tệp.

Nội dung là **bản sao**, không phải bản gốc. Mọi tệp nguồn `.md` và mọi tệp
kết xuất vẫn nằm nguyên chỗ cũ; không có script, liên kết hay tham chiếu chéo
nào bị đổi đường dẫn.

## Có gì trong này

| Tệp | Sinh từ | Nội dung |
|---|---|---|
| `01-do-an-tot-nghiep.pdf` | `docs/papers/thesis-full.pdf` | Quyển đồ án tốt nghiệp, **93 trang** |
| `01-do-an-tot-nghiep.docx` | `docs/papers/thesis-full.docx` | Cùng nội dung, bản Word để hội đồng ghi chú |
| `02-slide-bao-ve.pptx` | `docs/slides/slides.pptx` | Slide bảo vệ đầy đủ — 31 slide chính + 7 slide dự phòng |
| `03-slide-bao-cao-ky-thuat.pptx` | `docs/slides/11-slides-ky-thuat.pptx` | Bản gọn theo khuôn báo cáo kỹ thuật, 11 slide |
| `04-do-an-mon-hoc.pdf` | `docs/papers/mon-hoc/thesis-full.pdf` | Bản đồ án môn học **Xử lý ảnh và ứng dụng**, **44 trang** |
| `04-do-an-mon-hoc.docx` | `docs/papers/mon-hoc/thesis-full.docx` | Cùng nội dung, bản Word |
| `05-slide-mon-hoc.pptx` | `docs/slides/12-slides-mon-hoc.pptx` | Slide báo cáo môn học, **16 slide** |

Nhóm `01` và nhóm `04` là **hai quyển riêng**, không phải hai phiên bản của cùng
một quyển: khác bố cục, khác cao độ trình bày, khác danh mục tài liệu tham khảo.
Xem `docs/papers/mon-hoc/README.md`.

Poster (`docs/poster/poster.pdf`) **không** nằm ở đây. Muốn thêm thì bổ sung một
dòng vào `BUNDLE_FILES` trong `scripts/build_thesis.py`.

## Cách dựng lại

Thư mục được làm mới ở **mỗi** lần chạy, nên nó không thể âm thầm giữ bản cũ —
đó là lỗi mà một thư mục chép tay luôn mắc phải.

```bash
backend/.venv/Scripts/python.exe scripts/build_thesis.py
backend/.venv/Scripts/python.exe scripts/build_thesis.py --slides docs/slides/11-slides-ky-thuat.md
backend/.venv/Scripts/python.exe scripts/build_thesis.py --src docs/papers/mon-hoc
backend/.venv/Scripts/python.exe scripts/build_thesis.py --slides docs/slides/12-slides-mon-hoc.md
powershell -File scripts/export_thesis_pdf.ps1
powershell -File scripts/export_thesis_pdf.ps1 -Nguon docs/papers/mon-hoc/thesis-full.docx -Dich docs/papers/mon-hoc/thesis-full.pdf
```

Bốn lệnh đầu dựng lần lượt: quyển tốt nghiệp cùng slide bảo vệ, slide báo cáo kỹ
thuật, quyển môn học, và slide môn học. Hai lệnh sau dựng PDF bằng Word rồi tự chép sang đây.
Cả `build_thesis.py` lẫn `export_thesis_pdf.ps1` đều cập nhật thư mục này, nên
chạy lệnh nào cũng không để lại bản lệch.

`export_thesis_pdf.ps1` **suy tên tệp đích từ đường dẫn nguồn**, không đặt cứng.
Điều này là bắt buộc từ khi có hai quyển: bản đầu tiên đặt tên cứng, và lần xuất
quyển môn học đầu tiên đã chép đè lên quyển tốt nghiệp trong chính thư mục này.

Tệp nào chưa dựng thì bị bỏ qua kèm dòng báo `(chưa có: ...)`, không phải lỗi.

## Vì sao git không theo dõi nội dung

Bốn tệp trên là **bản sao đúng từng byte** của những tệp git đã theo dõi ở
`docs/papers/` và `docs/slides/`. Theo dõi thêm ở đây sẽ nhân đôi 13 MB nhị phân
vào lịch sử git mỗi lần dựng lại, đổi lấy đúng con số không. `.gitignore` vì vậy
bỏ qua nội dung và chỉ giữ lại chính tệp README này.
