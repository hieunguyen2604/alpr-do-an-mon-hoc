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
| `02-slide-bao-ve.pptx` | `docs/slides/slides.pptx` | Slide bảo vệ ĐATN đầy đủ — **31 slide chính + 7 slide dự phòng** (Chuẩn 15 phút) |
| `04-do-an-mon-hoc.pdf` | `docs/papers/mon-hoc/thesis-full.pdf` | Bản đồ án môn học **Xử lý ảnh và ứng dụng**, **44 trang** |
| `04-do-an-mon-hoc.docx` | `docs/papers/mon-hoc/thesis-full.docx` | Cùng nội dung, bản Word |
| `05-slide-mon-hoc.pptx` | `docs/slides/12-slides-mon-hoc.pptx` | Slide báo cáo môn học, **16 slide** (Chuẩn 7–10 phút) |

Nhóm `01` và nhóm `04` là **hai quyển riêng**, không phải hai phiên bản của cùng
một quyển: khác bố cục, khác cao độ trình bày, khác danh mục tài liệu tham khảo.
Xem `docs/papers/mon-hoc/README.md`.

---

## ✂️ 1. Kế Hoạch Tinh Gọn Quyển ĐATN Xuống 70 Trang (Nâng Cấp Sau)

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

## 📽️ 2. Kế Hoạch Rút Gọn Slide Thuyết Trình (Khi Hội Đồng Giới Hạn 10–12 Phút)

Slide bảo vệ hiện tại ([`02-slide-bao-ve.pptx`](02-slide-bao-ve.pptx)) gồm **31 slide chính + 7 slide backup** (tổng 38 slide, chuẩn 15 phút). Nếu Hội đồng chỉ cho phép trình bày trong **10–12 phút**, rút gọn về **20 slide chính** theo kế hoạch sau:

| Khối nội dung | Bản 15 phút (Hiện tại) | Bản 10 phút (Rút gọn) | Nội dung giữ lại |
|---|---|---|---|
| **Khối 1: Đặt vấn đề & Pháp lý** | 8 slide (S1–S8) | **4 slide** | Bìa $\rightarrow$ Tính cấp thiết (85% xe máy) $\rightarrow$ Căn cứ TT 79/2024 & TT 51/2025 $\rightarrow$ Mục tiêu đề tài. |
| **Khối 2: Kiến trúc & AI Pipeline** | 5 slide (S9–S13) | **3 slide** | Sơ đồ hệ thống 3 tầng $\rightarrow$ Pipeline 2-Stage $\rightarrow$ Kỹ thuật tách biển 2 dòng. |
| **Khối 3: Dữ liệu & Huấn luyện** | 4 slide (S14–S17) | **3 slide** | Bộ dữ liệu thực nghiệm $\rightarrow$ Siêu tham số & Đường cong huấn luyện YOLO11n. |
| **Khối 4: Thực nghiệm & Đánh giá** | 9 slide (S18–S26) | **6 slide** | Bảng độ chính xác (mAP50=0.9829) $\rightarrow$ Phân rã độ trễ CPU (168ms) $\rightarrow$ Đóng góp luật chuẩn hóa $\rightarrow$ Phân tích ca lỗi. |
| **Khối 5: Demo & Kết luận** | 5 slide (S27–S31) | **4 slide** | Video demo / Web Live $\rightarrow$ Đóng góp đạt được $\rightarrow$ Hạn chế & Hướng phát triển $\rightarrow$ Cảm ơn. |
| **TỔNG SLIDE CHÍNH** | **31 slide (15 phút)** | **20 slide (10 phút)** | *(Chuyển 11 slide bớt đi sang phần Backup dự phòng)* |

---

## 🚀 3. Phương Án Phân Bổ 7 Slide Backup Vào Thẳng Luồng Slide Chính (Bản 18–20 Phút)

Khi Hội đồng cho phép trình bày **18–20 phút** và muốn đi sâu trực tiếp vào bản chất thuật toán / số liệu ngay trong bài thuyết trình:

1. **Khối 1 (Tổng quan & Pháp lý):**
   - Ghép **Backup 6 (Căn cứ khoa học Laroca 2022 & TT 79/2024)** trực tiếp vào Slide 3 & Slide 4.
2. **Khối 2 (Kiến trúc & Giải pháp AI):**
   - Ghép **Backup 1 (Kiến trúc sâu YOLO11n: C3k2, SPPF)** trực tiếp vào Slide 10 (sau phần chọn detector).
   - Ghép **Backup 2 (Kiến trúc sâu PP-OCRv5: SVTR-HG, CTC Loss)** trực tiếp vào Slide 12 (sau phần nhận dạng ký tự).
3. **Khối 3 (Dữ liệu & Huấn luyện):**
   - Ghép **Backup 5 (Bảng siêu tham số huấn luyện AdamW, loss curve 20 epochs)** trực tiếp vào Slide 16.
4. **Khối 4 (Thực nghiệm & Đánh giá):**
   - Ghép **Backup 4 (Ablation Study: bóc tách đóng góp luật chuẩn hoá +13,28 điểm)** vào Slide 23.
   - Ghép **Backup 3 (Error Analysis: phân loại 6 ca lỗi E1–E6 trên 2.801 biển)** vào Slide 25.
5. **Khối 5 (Demo & Tổng kết):**
   - Ghép **Backup 7 (Bảng tra nhanh số liệu tổng thể)** vào Slide 30.

*$\rightarrow$ Tổng cộng: **36 slide chính liền mạch**, thuyết trình hoàn hảo trong **18–20 phút**.*

---

## 🛠️ 4. Bảng Ghi Nhận Các Cải Tiến Kỹ Thuật Đã Hoàn Thành (Cập Nhật Báo Cáo & Slide)

Dưới đây là 5 cải tiến kỹ thuật thực tế đã triển khai và kiểm chứng trên hệ thống, dùng để cập nhật vào Chương 4, Chương 5 và Slide thuyết trình:

| STT | Cải tiến kỹ thuật | Vị trí mã nguồn | Chi tiết & Số liệu thực nghiệm | Vị trí đưa vào Báo cáo & Slide |
|---|---|---|---|---|
| **1** | **Tối ưu tốc độ suy luận CPU Sub-100ms** | `backend/main.py`<br>`ai/inference/detector.py` | • Kích hoạt `torch.inference_mode()` tắt autograd.<br>• Phân luồng `torch.set_num_threads()` & OpenCV SIMD AVX2 theo nhân CPU thực.<br>• **Kết quả:** Thời gian xử lý 1 biển số giảm từ 168 ms xuống **~81,7 ms** (biển 1 dòng chỉ 57 ms), bảo toàn 100% độ chính xác OCR (99,92%). | **Chương 4 (§4.4 Tối ưu CPU)**<br>**Chương 5 (§5.3 Phân rã độ trễ)**<br>**Slide 20 (Độ trễ suy luận)** |
| **2** | **Khử trùng lặp mờ thông minh (Fuzzy Deduplication)** | `backend/services/detection_service.py`<br>`useLiveVideoDetection.ts` | • Thuật toán tính khoảng cách Levenshtein $\le 2$ kết hợp tiền tố mã tỉnh và số đuôi trong cửa sổ $3,5$ giây.<br>• Tự động gom các biến thể đọc nhầm do bóng đổ / lóa sáng (như `52Z-1513` gộp vào `52Z2-0513`), luôn giữ bản ghi chuẩn TT 79 có độ tin cậy cao nhất. | **Chương 4 (§4.3 Xử lý Video)**<br>**Chương 5 (§5.4 Khử trùng lặp)**<br>**Slide 24 (Xử lý Video)** |
| **3** | **Quét Webcam Laptop Thời Gian Thực (Live Scanner)** | `frontend/src/pages/WebcamDetection.tsx` | • Luồng xử lý **Single-Slot Worker Loop** kết hợp **Frame Skipping** qua endpoint `POST /api/detect/frame`.<br>• Tránh hoàn toàn tích tụ trễ trên CPU, vẽ Bounding Box neon thời gian thực, bảng HUD đo FPS và độ trễ trực tiếp. | **Chương 4 (§4.6 Giao diện Demo)**<br>**Slide 27 (Live Demo)** |
| **4** | **Hàng đợi Đa ảnh & Giao diện Single-Screen** | `ImageDetection.tsx`<br>`ImageUploadPanel.tsx` | • Hỗ trợ chọn và xử lý hàng loạt nhiều ảnh với dải phim cuộn ngang (Filmstrip Carousel).<br>• Bố cục 2 cột gọn gàng hiển thị tức thì kết quả và chuyển đổi giữa các ảnh mà không cần cuộn trang. | **Chương 4 (§4.6)**<br>**Slide 28 (Ảnh Demo)** |
| **5** | **Tăng cường khả năng chịu lỗi Polling (Resilience)** | `frontend/src/hooks/useJobPolling.ts` | • Nâng ngưỡng chịu lỗi mạng liên tiếp từ 3 lên 10 lần, tự động duy trì kết nối khi máy chủ khởi động lại hoặc mạng trễ. | **Chương 4 (§4.5 API Service)** |

---

## Cách dựng lại

Thư mục được làm mới ở **mỗi** lần chạy, nên nó không thể âm thầm giữ bản cũ —
đó là lỗi mà một thư mục chép tay luôn mắc phải.

```bash
python scripts/build_thesis.py
python scripts/build_thesis.py --src docs/papers/mon-hoc
python scripts/build_thesis.py --slides docs/slides/12-slides-mon-hoc.md
```
