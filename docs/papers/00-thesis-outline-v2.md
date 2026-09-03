# Mục lục — cấu trúc 7 chương

> ⚠️ **Bản thực thi cuối đã GỘP về 6 chương** — khác đề cương 7 chương dưới đây:
> nội dung "xây dựng & huấn luyện" của Chương 5 (cũ) nhập vào Chương 4 (thiết kế
> và cài đặt), "thực nghiệm" giữ Chương 5, "kết luận" thành Chương 6. Nguồn sự
> thật: `CHAPTER_FILENAMES` trong `scripts/build_thesis.py` và cây tệp trong
> [`THESIS-README.md`](THESIS-README.md). Toàn bộ đánh số mục/hình/bảng trong
> các tệp chương đã theo cấu trúc 6 chương; phần thân tài liệu này giữ nguyên
> như bản ghi lịch sử của lần đề xuất 02/08/2026.

**Ngày lập:** 2026-08-02 · **Trạng thái:** ✅ **ĐÃ ÁP DỤNG 02/08/2026**
**Thay cho:** đề cương 6 chương cũ (đã xoá 03/09/2026, tra lại qua git history)

> **Đã thực hiện bằng công cụ, không sửa tay.** Việc tái cấu trúc do
> `scripts/restructure_thesis.py` thực hiện, kèm hai lớp kiểm chứng chạy trước
> và sau:
>
> | Kiểm chứng | Công cụ | Kết quả |
> |---|---|---|
> | Mọi tham chiếu chéo trỏ tới mục có thật | `scripts/check_thesis_refs.py` | **416 tham chiếu, 0 chết** |
> | Không đánh rơi đoạn nào khi di chuyển | `scripts/check_thesis_conservation.py` | **4.199 → 4.198 dòng**, chênh lệch đúng bằng 1 đoạn dẫn nhập đã chuyển có chủ đích |
>
> Quy mô thay đổi: 158/224 mục đổi số, 29/29 mã bảng đổi mã, 111 tham chiếu
> "Chương N", 277 tham chiếu "mục N.M", 33 chú thích hình. Năm chuỗi
> `paddlepaddle 3.3.1` được **chặn tường minh** vì trùng dạng số mục — đây là
> lỗi mà mắt người không đọc ra trên bản in.
>
> Ngoài bảng ánh xạ dưới đây, ba việc phát sinh đã làm luôn: thêm chú thích
> nhìn thấy được cho **43 bảng** vốn chỉ có neo máy đọc hoặc không có gì (Chương
> 1, 4, 5, 6, 7); sinh lại **Mục lục / Danh mục hình / Danh mục bảng** từ chính
> nội dung chương bằng `scripts/gen_front_matter_lists.py` (trước đó là
> placeholder liệt kê những mục không tồn tại); và đổi tên hai mục cho khớp cấp
> độ tiêu đề chương.

---

## 0. Vì sao đề xuất này, và một lỗ hổng phải xử lý trước

**Điều cấu trúc hiện tại làm chưa tốt.** Phần *"Lựa chọn công nghệ"* — thứ hội
đồng hỏi nhiều nhất — đang là **§2.8, 159 dòng nằm cuối một chương 1.193 dòng**.
Người đọc mục lục không thấy nó. Tách ra thành chương riêng là cải thiện thật.

**Lỗ hổng trong đề xuất 7 chương.** Chương *"Xây dựng và huấn luyện mô hình"*
theo tên chỉ nhận nội dung về mô hình. Nhưng Chương 4 hiện hành có 1.622 dòng,
trong đó chỉ khoảng 850 dòng là về mô hình:

| Mục hiện tại | Dòng | Về mô hình? |
|---|---:|:---:|
| 4.2 Cài đặt tầng AI | 682 | ✅ |
| 4.5 Xây dựng bộ dữ liệu | 160 | ✅ |
| 4.3 Cài đặt backend | 370 | ❌ |
| 4.4 Cài đặt frontend | 158 | ❌ |
| 4.6 Triển khai Docker | 55 | ❌ |
| 4.1 Môi trường · 4.7 Lệch thiết kế | 158 | ❌ |

**583 dòng backend/frontend/Docker không có chương nào nhận.** Đây là một hệ
thống hoàn chỉnh, không phải một bài huấn luyện mô hình — bỏ phần này khỏi mục
lục là giấu đi một phần ba khối lượng công việc.

**Cách xử lý (khuyến nghị):** đổi tên chương 5 thành **"Xây dựng hệ thống và
huấn luyện mô hình"**. Vẫn 7 chương như bạn đề xuất, nhưng tên khớp nội dung.

---

## 1. Mục lục chi tiết

Cột cuối ghi **nội dung lấy từ đâu** — mọi mục đều có nguồn thật, không mục nào
là chỗ trống chờ viết.

### Chương 1 — Giới thiệu · *~445 dòng, giữ nguyên*

| Mục | Nguồn |
|---|---|
| 1.1. Đặt vấn đề | ch1 §1.1 |
| 1.2. Mục tiêu đề tài | ch1 §1.2 |
| 1.3. Đối tượng và phạm vi nghiên cứu | ch1 §1.3 |
| 1.4. Phương pháp nghiên cứu | ch1 §1.4 |
| 1.5. Ý nghĩa khoa học và thực tiễn | ch1 §1.5 |
| 1.6. Đóng góp của đề tài | ch1 §1.6 |
| 1.7. Bố cục quyển đồ án | ch1 §1.7 — **phải viết lại theo 7 chương** |

### Chương 2 — Cơ sở lý thuyết · *~1.030 dòng*

| Mục | Nguồn |
|---|---|
| 2.1. Tổng quan bài toán ALPR | ch2 §2.1 |
| 2.2. Lịch sử phát triển các phương pháp | ch2 §2.2 |
| 2.3. Phân loại các hướng tiếp cận hiện nay | ch2 §2.3 |
| 2.4. Cơ sở lý thuyết về phát hiện đối tượng | ch2 §2.4 |
| 2.5. Cơ sở lý thuyết về nhận dạng ký tự | ch2 §2.5 |
| 2.6. Quy chuẩn biển số xe Việt Nam | ch2 §2.6 |
| 2.7. Các công trình liên quan | ch2 §2.7 |

> §2.8 *"Lựa chọn công nghệ"* chuyển sang Chương 3.

### Chương 3 — Khảo sát công nghệ và lựa chọn mô hình · *~350 dòng*

**Đây là chương mới, và là lý do chính của việc tái cấu trúc.**

| Mục | Nguồn |
|---|---|
| 3.1. Phương pháp khảo sát và tiêu chí lựa chọn | **viết mới** — nêu rõ cái nào đo, cái nào chỉ khảo sát |
| 3.2. Mô hình phát hiện: YOLO11 so với YOLOv8 | ch2 §2.8.1 |
| 3.3. Engine nhận dạng ký tự | ch2 §2.8.2 |
| 3.3.1. PaddleOCR, EasyOCR, Tesseract — khảo sát tài liệu | ch2 §2.8.2 |
| 3.3.2. PP-OCRv5 mobile so với PP-OCRv6 — **đo trên máy đồ án** | báo cáo [35](../reports/35-ppocrv6-evaluation.md) |
| 3.4. Runtime suy luận trên CPU: ONNX Runtime, OpenVINO | ch2 §2.8.3 |
| 3.5. Các lựa chọn công nghệ nền tảng khác | ch2 §2.8.4 |
| 3.6. Ảnh hưởng của độ phân giải đầu vào | ch5 §5.8 |
| 3.7. Kết luận chương — bảng tổng hợp quyết định | **viết mới** |

> ### ⚠️ Tên chương và phạm vi — điểm phải cẩn thận nhất
>
> Đề xuất ban đầu ghi *"so sánh YOLOv8/YOLOv11, PP-OCRv5, EasyOCR, Tesseract"*.
> Nhưng chính ch2 §2.8 ghi trung thực rằng **benchmark engine chưa bao giờ chạy
> được**: *"PaddleOCR PP-OCRv5_mobile được giữ làm engine duy nhất vì các lý do
> kỹ thuật, không phải vì đã chứng minh được nó chính xác hơn EasyOCR"*.
>
> | So sánh | Trạng thái |
> |---|---|
> | YOLO11n ↔ YOLOv8n | có căn cứ — số liệu chính thức và lý do chọn |
> | PP-OCRv5 ↔ PP-OCRv6 | ✅ **tự đo** — 67,0% / 23,0 ms so với 72,5% / 386,9 ms |
> | Model gốc ↔ fine-tune | ✅ **tự đo** — 2.801 mẫu và 608 khung ảnh toàn cảnh |
> | EasyOCR, Tesseract | ❌ **chỉ khảo sát tài liệu, chưa đo lần nào** |
>
> Mục lục là thứ hội đồng đọc đầu tiên. Đặt tên hứa bốn so sánh trong khi hai
> cái chưa đo sẽ biến một hạn chế đã thừa nhận thành một khẳng định. **§3.1 phải
> nói thẳng bảng trên ngay đầu chương.**

### Chương 4 — Phân tích và thiết kế hệ thống · *~1.341 dòng, giữ nguyên*

| Mục | Nguồn |
|---|---|
| 4.1. Phân tích yêu cầu | ch3 §3.1 |
| 4.2. Kiến trúc hệ thống | ch3 §3.2 |
| 4.3. Thiết kế chi tiết các khối | ch3 §3.3 |
| 4.4. Thiết kế cơ sở dữ liệu | ch3 §3.4 |
| 4.5. Thiết kế giao diện người dùng | ch3 §3.5 |

### Chương 5 — Xây dựng hệ thống và huấn luyện mô hình · *~1.780 dòng*

| Mục | Nguồn |
|---|---|
| 5.1. Môi trường và công cụ phát triển | ch4 §4.1 |
| **5.2. Xây dựng bộ dữ liệu** | ch4 §4.5 |
| 5.2.1. Đường ống sáu bước | ch4 §4.5.1 |
| 5.2.2. Khử trùng lặp chéo bộ | ch4 §4.5.2 |
| 5.2.3. Bài học về perceptual hash | ch4 §4.5.3 |
| **5.3. Huấn luyện mô hình phát hiện** | ch5 §5.4 |
| 5.3.1. Siêu tham số | ch5 §5.4.1 |
| 5.3.2. Đường cong huấn luyện | ch5 §5.4.2 |
| 5.3.3. Tiến triển mAP theo mốc epoch | ch5 §5.4.3 |
| 5.3.4. Chi phí huấn luyện | ch5 §5.4.4 |
| **5.4. Tinh chỉnh bộ nhận dạng ký tự** | ch5 §5.6.8 + báo cáo [30](../reports/30-rare-plate-integration.md), [31](../reports/31-detection-stage-ablation.md) |
| 5.5. Cài đặt tầng AI | ch4 §4.2 |
| 5.6. Cài đặt backend | ch4 §4.3 |
| 5.7. Cài đặt frontend | ch4 §4.4 |
| 5.8. Triển khai bằng Docker | ch4 §4.6 |
| 5.9. Những chỗ cài đặt lệch khỏi thiết kế, và lý do | ch4 §4.7 |

> **Vì sao gộp cả hai.** Tách "huấn luyện mô hình" khỏi "cài đặt hệ thống" thành
> hai chương sẽ thành **8 chương**. Giữ 7 chương thì tên phải bao cả hai — nếu
> không, 583 dòng backend/frontend/Docker không có chỗ đứng trong mục lục.

### Chương 6 — Thực nghiệm và đánh giá · *~1.320 dòng*

| Mục | Nguồn |
|---|---|
| 6.1. Mục tiêu và phương pháp đánh giá | ch5 §5.1 |
| 6.2. Môi trường thực nghiệm | ch5 §5.2 |
| 6.3. Bộ dữ liệu thực nghiệm | ch5 §5.3 |
| 6.4. Đánh giá bộ phát hiện biển số | ch5 §5.5 |
| 6.5. Đánh giá khối OCR và hậu xử lý | ch5 §5.6 *(trừ §5.6.8, đã chuyển)* |
| 6.6. Đánh giá hiệu năng | ch5 §5.7 |
| 6.7. Đối chiếu toàn bộ chỉ tiêu phi chức năng | ch5 §5.9 |
| 6.8. Phân tích lỗi | ch5 §5.10 |
| 6.9. Bàn luận và các mối đe doạ đến tính hợp lệ | ch5 §5.11 |
| Phụ lục — Ánh xạ số liệu và lệnh tái lập | ch5, phụ lục kỹ thuật |

### Chương 7 — Kết luận và hướng phát triển · *~541 dòng, giữ nguyên*

| Mục | Nguồn |
|---|---|
| 7.1. Tổng kết công việc đã thực hiện | ch6 §6.1 |
| 7.2. Các kết quả đạt được | ch6 §6.2 |
| 7.3. Các hạn chế của đồ án | ch6 §6.3 |
| 7.4. Hướng phát triển | ch6 §6.4 |
| 7.5. Kết luận chung | ch6 §6.5 |

---

## 2. Cân đối khối lượng

| Chương | Dòng | Ghi chú |
|---|---:|---|
| 1. Giới thiệu | ~445 | |
| 2. Cơ sở lý thuyết | ~1.030 | giảm 163 do chuyển §2.8 |
| 3. Khảo sát và lựa chọn mô hình | ~350 | **mỏng nhất** — chấp nhận được vì đây là chương quyết định, không phải chương trình bày |
| 4. Phân tích và thiết kế | ~1.341 | |
| 5. Xây dựng hệ thống và huấn luyện | ~1.780 | **dày nhất** |
| 6. Thực nghiệm và đánh giá | ~1.320 | |
| 7. Kết luận | ~541 | |

Chênh lệch giữa chương dày nhất và mỏng nhất là **5 lần**. Đó là bình thường với
đồ án kỹ thuật — chương quyết định ngắn, chương cài đặt dài.

---

## 3. Chi phí và rủi ro khi áp dụng

**505 tham chiếu chéo phải rà lại.** Đánh số 6→7 chương làm mọi *"Chương 3"*,
*"mục 5.6.5"*, *"bảng T5.7b"* sai:

| Tệp | Tham chiếu |
|---|---:|
| ch5 | **192** |
| ch6 | 84 |
| ch3 | 65 |
| ch2 | 64 |
| ch4 | 57 |
| ch1 | 43 |

**Đây không phải rủi ro giả định.** Riêng ngày 02/08/2026, một vòng soát tự động
đã tìm ra **32 con số lỗi thời** trong ch5/ch6, gồm cả một bảng ngân sách độ trễ
mang nguyên bộ số của lần đo cũ mà không có chú dẫn nào. Tái cấu trúc mà không
chạy lại vòng soát ấy gần như chắc chắn để lọt tham chiếu chết.

**Thứ tự thực hiện đề nghị:**

1. Đổi tên chương và đánh số lại — thay đổi cơ học, kiểm được bằng script
2. Di chuyển nội dung theo bảng ánh xạ ở mục 1
3. Viết mới §3.1 (phương pháp khảo sát) và §3.7 (bảng tổng hợp quyết định)
4. Viết lại §1.7 (bố cục quyển) theo 7 chương
5. **Chạy lại vòng soát số liệu và tham chiếu chéo** — bắt buộc, không để tới lúc in
6. Dựng lại `thesis-full.docx` và `.pdf`, dựng lại slide (slide có nhắc "Chương 3")

Bước 5 là bước dễ bị bỏ nhất và cũng là bước đắt nhất nếu bỏ.
