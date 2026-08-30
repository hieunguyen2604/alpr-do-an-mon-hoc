# Bản nộp

Thư mục này gom **bản thành phẩm** của đồ án về một chỗ, để lúc nộp không phải
đi tìm giữa `docs/papers/` và `docs/slides/`, và không đính nhầm tệp.

Nội dung là **bản sao**, không phải bản gốc. Mọi tệp nguồn `.md` và mọi tệp
kết xuất vẫn nằm nguyên chỗ cũ; không có script, liên kết hay tham chiếu chéo
nào bị đổi đường dẫn.

## Có gì trong này

| Tệp | Sinh từ | Nội dung |
|---|---|---|
| `01-do-an-tot-nghiep.pdf` | `docs/papers/thesis-full.pdf` | Quyển đồ án tốt nghiệp đầy đủ, **93 trang** |
| `01-do-an-tot-nghiep.docx` | `docs/papers/thesis-full.docx` | Cùng nội dung, bản Word để hội đồng ghi chú |
| `02-slide-bao-ve.pptx` | `docs/slides/slides.pptx` | Slide bảo vệ đầy đủ — 31 slide chính + 7 slide dự phòng |
| `04-do-an-mon-hoc.pdf` | `docs/papers/mon-hoc/thesis-full.pdf` | Bản đồ án môn học **Xử lý ảnh và ứng dụng**, **44 trang** |
| `04-do-an-mon-hoc.docx` | `docs/papers/mon-hoc/thesis-full.docx` | Cùng nội dung, bản Word |
| `05-slide-mon-hoc.pptx` | `docs/slides/12-slides-mon-hoc.pptx` | Slide báo cáo môn học, **16 slide** |

Nhóm `01` và nhóm `04` là **hai quyển riêng**, không phải hai phiên bản của cùng
một quyển: khác bố cục, khác cao độ trình bày, khác danh mục tài liệu tham khảo.
Xem `docs/papers/mon-hoc/README.md`.

---

## ✂️ Kế Hoạch Tinh Gọn Quyển ĐATN Xuống 70 Trang (Nâng Cấp Sau)

Khi cần rút gọn quyển Đồ án tốt nghiệp từ **93 trang $\rightarrow$ chuẩn 70 trang** (giảm ~23 trang) để nộp theo khung quy định 60–75 trang:

| Chương | Trang hiện tại | Phần Cắt Bỏ / Thu Gọn | Mục tiêu giảm |
|---|---|---|---|
| **Chương 2: Cơ sở lý thuyết** | 12 trang | • **Bỏ:** Các đoạn lý thuyết giáo khoa về mạng tích chập cổ điển (CNN, VGG) và lịch sử phát triển YOLOv1–v7.<br>• **Giữ:** Đi thẳng vào cơ chế **YOLO11 (C3k2, SPPF)** và **CRNN + CTC Loss của PaddleOCR**. | **-5 trang** |
| **Chương 3: Khảo sát & Lựa chọn** | 6 trang | • **Gom:** Ghép các tiêu chí so sánh rời rạc thành 1 bảng ma trận đánh giá tổng hợp duy nhất (YOLO11 vs YOLOv8/Faster R-CNN, PP-OCRv5 vs Tesseract/EasyOCR). | **-2 trang** |
| **Chương 4: Phân tích & Thiết kế** | 24 trang | • **Bỏ:** Các đoạn văn xuôi mô tả chi tiết CRUD API, cấu trúc bảng CSDL SQLite/Pydantic thông thường.<br>• **Giữ:** Giữ trọn vẹn **Sơ đồ kiến trúc 3 tầng**, **Pipeline 5 bước**, và **Thuật toán phân tách biển 2 dòng**. | **-4 trang** |
| **Chương 5: Thực nghiệm & Đánh giá** | 24 trang | • **Bỏ:** Các đoạn văn xuôi diễn giải lại số liệu đã có trong bảng.<br>• **Giữ:** Toàn bộ **Bảng số liệu đo thật** (mAP50=0.9829, độ trễ CPU=168.41ms, so sánh 1 dòng vs 2 dòng, phân tích ca lỗi Error Analysis). | **-4 trang** |
| **Chương 9: Phụ lục** | 12 trang | • **Bỏ:** Bảng tra cứu chi tiết 63/34 tỉnh thành dài 4-5 trang và các đoạn log đo thô.<br>• **Gom:** Thành bảng tóm tắt mã vùng biển số 1 trang. | **-8 trang** |
| **TỔNG CỘNG** | **93 trang** | **Giữ lại 100% cốt lõi học thuật, mô hình AI & số liệu đo thật** | **$\approx$ 70 trang** |

---

## Cách dựng lại

Thư mục được làm mới ở **mỗi** lần chạy, nên nó không thể âm thầm giữ bản cũ —
đó là lỗi mà một thư mục chép tay luôn mắc phải.

```bash
python scripts/build_thesis.py
python scripts/build_thesis.py --src docs/papers/mon-hoc
python scripts/build_thesis.py --slides docs/slides/12-slides-mon-hoc.md
```
