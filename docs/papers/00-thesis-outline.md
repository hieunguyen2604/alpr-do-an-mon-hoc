# Đề cương chi tiết quyển đồ án tốt nghiệp

**Đề tài:** Xây dựng hệ thống nhận dạng biển số xe Việt Nam ứng dụng Trí tuệ nhân tạo
*(Developing an AI-based Vietnamese License Plate Recognition System)*

| Mục | Nội dung |
|---|---|
| Mã tài liệu | `THESIS-OUTLINE-v1.0` |
| Giai đoạn | Phase 9 — Documentation (khởi động sớm, song song Phase 2–4) |
| Ngày lập | 2026-07-19 |
| Trạng thái | **Khung đã chốt — cả sáu chương đã viết xong (cập nhật 2026-07-20)** |

---

## 0. Mục đích và cách dùng tài liệu này

Tài liệu này là **bản thiết kế của quyển đồ án**, không phải một chương của quyển. Nó có ba chức năng:

1. **Cố định cấu trúc** — danh sách chương và mục con đến cấp 3, đánh số theo kiểu `1.1`, `1.1.1` để công cụ sinh mục lục tự động hoạt động được.
2. **Truy vết nguồn** — mỗi mục ghi rõ lấy nội dung từ tài liệu Phase 0 hoặc Phase 1 nào. Nguyên tắc bắt buộc: **không nghiên cứu lại** những gì đã hoàn thành và đã kiểm chứng ở Phase 0–1.
3. **Ghi trung thực trạng thái** — mục nào chưa viết được thì ghi rõ chưa viết được và lý do, thay vì để trống một cách im lặng.

> **Quy tắc vàng của toàn bộ quyển đồ án:** không viết về kết quả chưa có. Chỗ nào cần số liệu thực nghiệm mà chưa đo được thì ghi *"sẽ được trình bày ở Chương 5"*, tuyệt đối không phỏng đoán, không điền số tạm.

---

## 1. Trạng thái thực tế của dự án tại thời điểm lập đề cương

Phần này tồn tại để người đọc đề cương biết mỗi chương dựa trên nền tảng kỹ thuật nào. Tính đến 2026-07-20, **cả sáu chương đều đã viết xong**.

| Hạng mục | Trạng thái | Hệ quả với quyển đồ án |
|---|---|---|
| Phase 0 — Requirement Analysis | ✅ Hoàn thành, chốt mốc **M0** | Cung cấp toàn bộ nguyên liệu cho Chương 3 |
| Phase 1 — Research | ✅ Hoàn thành, chốt mốc **M1** | Cung cấp toàn bộ nguyên liệu cho Chương 2 |
| Backend FastAPI | ✅ **Đã chạy được** — xác minh bằng HTTP thật: **10 endpoint** phản hồi đúng, Alembic migrate xong, Swagger render được | Chương 3 mô tả được thiết kế đã cài đặt, không phải thiết kế trên giấy |
| Frontend React | ✅ **Hoàn thành** — build sạch, khớp 10 endpoint | Chương 3 mô tả thiết kế; ảnh chụp màn hình thuộc Chương 4 |
| **Huấn luyện mô hình** | ✅ **Mô hình chính thức `best.pt` đã xong** (`imgsz=640`, split v3, 20 epoch): detection đạt cả bốn chỉ tiêu (mAP@0.5 0,9829). `baseline-416-v1.pt` giữ làm đối chứng | **Chương 5 đã viết được**: số công bố lấy từ `best.pt`, không dùng số baseline (sai độ phân giải + rò rỉ) |
| Pipeline nhận dạng đang chạy | ✅ `ALPRPipeline` **thật** — `/health` trả `model_loaded: true`, engine `yolo:best.pt+paddleocr-PP-OCRv5-mobile` | Số liệu đánh giá Chương 5 đo trên `best.pt` |

> **Điểm phải nói thẳng khi bảo vệ.** Trong giai đoạn Phase 5–7 hệ thống từng chạy bằng pipeline giả lập `StubPipeline`; nay stub đã ra khỏi đường chạy chính và **không một con số nào do stub hay `baseline-416-v1.pt` sinh ra được phép vào Chương 5** — số công bố lấy từ `best.pt`. Giải thích đầy đủ lý do dùng stub, cơ chế `ALPR_USE_STUB` / `UnavailablePipeline` và ranh giới số liệu: xem `THESIS-README.md` §2.

---

## 2. Bản đồ nguồn tài liệu

Ký hiệu rút gọn dùng trong toàn bộ đề cương:

| Ký hiệu | Tệp nguồn |
|---|---|
| `SRS` | `docs/00-requirements/SRS.md` |
| `FR` | `docs/00-requirements/functional-requirements.md` |
| `NFR` | `docs/00-requirements/non-functional-requirements.md` |
| `SCOPE` | `docs/00-requirements/project-scope.md` |
| `TIME` | `docs/00-requirements/timeline.md` |
| `ENV` | `docs/00-requirements/environment.md` |
| `ARCH` | `docs/architecture/system-architecture.md` |
| `RESEARCH` | `docs/reports/01-research-report.md` |
| `VNPLATE` | `docs/reports/01-vn-plate-standards.md` |
| `YOLO` | `docs/reports/01-yolo-comparison.md` |
| `OCR` | `docs/reports/01-ocr-comparison.md` |
| `TECH` | `docs/reports/01-technology-comparison.md` |
| `DATASET` | `docs/reports/01-dataset-survey.md` |
| `CITEMAP` | `docs/reports/01-citation-map.md` |
| `BIB` | `docs/references.bib` (232 entry) |

---

## 3. Tổng quan cấu trúc và ước lượng số trang

| Phần | Tên | Ước lượng số trang | Trạng thái |
|:---:|---|:---:|---|
| — | Phần đầu quyển (bìa → abstract) | 10–12 | ✅ **Đã viết** (`01-front-matter.md`) |
| **1** | Mở đầu | 8–10 | ✅ **Đã viết** (`ch1-mo-dau.md`) |
| **2** | Tổng quan và cơ sở lý thuyết | 28–34 | ✅ **Đã viết** (`ch2-tong-quan.md`) |
| **3** | Phân tích và thiết kế hệ thống | 22–26 | ✅ **Đã viết** (`ch3-phan-tich-thiet-ke.md`) |
| **4** | Cài đặt hệ thống | 20–24 | ✅ **Đã viết** (`ch4-cai-dat.md`) |
| **5** | Thực nghiệm và đánh giá | 22–28 | ✅ **Đã viết** (`ch5-thuc-nghiem.md`) |
| **6** | Kết luận và hướng phát triển | 5–7 | ✅ **Đã viết** (`ch6-ket-luan.md`) |
| — | Tài liệu tham khảo | 8–12 | 🔵 Sinh từ `BIB` khi ghép |
| — | Phụ lục | 6–10 | 🔵 Trích từ Chương 4–5 khi ghép |
| | **Tổng dự kiến** | **129–163** | |

> Ước lượng theo khổ A4, font 13pt, giãn dòng 1,5 — quy ước phổ biến của đồ án tốt nghiệp đại học Việt Nam. Con số chỉ mang tính định hướng phân bổ công sức; **không được coi là chỉ tiêu phải đạt**. Viết đủ ý quan trọng hơn viết đủ trang.
>
> Phần thân chính (Chương 1–6) chiếm khoảng 105–129 trang. Nếu quy chế của khoa giới hạn dưới mức này, hạng mục cắt trước tiên là các bảng so sánh chi tiết ở Chương 2 — chúng chuyển xuống Phụ lục, giữ lại bảng tổng hợp trong thân bài.

---

## 4. CHƯƠNG 1 — MỞ ĐẦU

**Trạng thái:** ✅ **Đã viết** — tệp `docs/papers/ch1-mo-dau.md` · **Độ dài ước lượng:** 8–10 trang
**Nguồn chính:** `SRS` §1–2, `SCOPE`, `RESEARCH` §2.8, §2.11, `TIME`

Chương này trả lời bốn câu hỏi theo đúng thứ tự: *vì sao làm*, *làm gì*, *làm đến đâu*, *làm bằng cách nào*. Nó phải đọc được độc lập — người đọc chỉ đọc Chương 1 vẫn nắm được toàn bộ đề tài.

### 1.1. Đặt vấn đề

| Mục | Nội dung | Nguồn |
|---|---|---|
| 1.1.1. Nhu cầu tự động hoá nhận dạng biển số xe | Bãi đỗ xe thông minh, thu phí không dừng, giám sát giao thông, kiểm soát ra vào | `SRS` §2.1; `RESEARCH` §2.2.2 |
| 1.1.2. Đặc thù bài toán tại Việt Nam | Mật độ xe máy áp đảo; biển hai dòng phổ biến; nhiều nền màu mang ngữ nghĩa; điều kiện thu nhận ảnh khắc nghiệt; định dạng ký tự riêng | `SRS` §2.1; `RESEARCH` §2.8.1–2.8.4 |
| 1.1.3. Khoảng trống thực tiễn và học thuật | Sáu khoảng trống đã xác định từ khảo sát Phase 1 | `RESEARCH` §2.11.3 |

**Số liệu bắt buộc phải có trích dẫn ở mục này:**

- Quy mô xe máy tại Việt Nam <!-- dantri_2024_77trieuxemay -->
- Chênh lệch độ chính xác biển một dòng ↔ biển hai dòng **đo trên bộ RodoSol-ALPR (Brazil)**: 94,3% ↔ 45,7%, chênh 48,6 điểm phần trăm <!-- laroca_2022_crossdataset -->
  > ⚠️ **Cảnh báo trích dẫn bắt buộc.** Cặp số này đo trên **RodoSol-ALPR (Brazil)**, **không phải dữ liệu Việt Nam**. Chỉ được dẫn như một *analogue* định lượng về độ khó của biển hai dòng. Trình bày nó như số liệu Việt Nam là lỗi trích dẫn nghiêm trọng. Nguồn gốc cảnh báo: `DATASET` §4.2.4, `RESEARCH` §2.8.2.

### 1.2. Mục tiêu đề tài

| Mục | Nội dung | Nguồn |
|---|---|---|
| 1.2.1. Mục tiêu tổng quát | Xây dựng hệ thống ALPR hoàn chỉnh cho biển số Việt Nam, hỗ trợ cả biển một dòng và hai dòng, suy luận trên CPU | `SCOPE` §1; `RESEARCH` §2.11.2 |
| 1.2.2. Mục tiêu cụ thể | Bảy mục tiêu bám theo sản phẩm bàn giao: mô hình detection, module OCR + hậu xử lý, backend, frontend, CSDL, kiểm thử, đóng gói | `SCOPE` §2, §5 |
| 1.2.3. Tiêu chí thành công | Năm tiêu chí định lượng và kiểm chứng được | `SCOPE` §6 |

### 1.3. Đối tượng và phạm vi nghiên cứu

| Mục | Nội dung | Nguồn |
|---|---|---|
| 1.3.1. Đối tượng nghiên cứu | Biển số xe cơ giới Việt Nam theo quy chuẩn hiện hành; mô hình phát hiện đối tượng họ YOLO; engine OCR | `SCOPE` §2; `VNPLATE` §1.3 |
| 1.3.2. Phạm vi trong | Bốn nhóm: AI, dữ liệu, phần mềm, kiểm thử–tài liệu | `SCOPE` §2 |
| 1.3.3. Phạm vi ngoài | Mười một hạng mục loại trừ, **kèm lý do loại trừ cho từng hạng mục** | `SCOPE` §3 |

> **Vì sao mục 1.3.3 quan trọng hơn vẻ ngoài của nó.** Danh sách "ngoài phạm vi" là hàng rào bảo vệ trước câu hỏi phản biện lạc hướng. Mỗi dòng phải nêu lý do loại trừ, không được chỉ liệt kê. `SCOPE` §3 đã viết sẵn cột lý do — dùng nguyên.

### 1.4. Phương pháp nghiên cứu

| Mục | Nội dung | Nguồn |
|---|---|---|
| 1.4.1. Nghiên cứu lý thuyết | Khảo sát tài liệu có hệ thống; đối chiếu văn bản pháp quy gốc; kiểm chứng đối kháng nguồn trích dẫn | `RESEARCH`; `VNPLATE` §1; `CITEMAP` |
| 1.4.2. Nghiên cứu thực nghiệm | Huấn luyện có kiểm soát, đo trên tập test độc lập, công bố kèm cấu hình phần cứng | `NFR` §0; `RESEARCH` §2.9.4 |
| 1.4.3. Quy trình theo giai đoạn | 12 phase, 77 ngày-người, 12 mốc chốt M0–M11 | `TIME` §2, §6 |

**Nguyên tắc phương pháp luận phải nêu rõ ở 1.4.2** (`NFR` §0): mọi số liệu hiệu năng công bố bắt buộc kèm **model CPU, số luồng, kích thước ảnh đầu vào, backend suy luận, và cỡ mẫu đo**. Công bố FPS không kèm cấu hình phần cứng là lỗi phương pháp luận và gần như chắc chắn bị hỏi khi bảo vệ.

### 1.5. Đóng góp của đồ án

| Mục | Nội dung | Nguồn |
|---|---|---|
| 1.5.1. Tuyên bố trung thực về mức đóng góp | Đồ án **không** tạo ra kết quả state-of-the-art, và nói rõ điều đó ngay từ đầu | `RESEARCH` §2.11.1 |
| 1.5.2. Đóng góp kỹ thuật | Bộ luật hậu xử lý **ràng buộc theo vị trí** cho biển số Việt Nam | `RESEARCH` §2.11.4 (1); `VNPLATE` §9 |
| 1.5.3. Đóng góp thực nghiệm | Báo cáo hiệu năng **tách theo layout** một dòng / hai dòng và theo điều kiện ảnh | `RESEARCH` §2.11.4 (2); `NFR` A8, A9 |
| 1.5.4. Đóng góp kỹ nghệ | Hệ thống hoàn chỉnh, tái lập được, chạy CPU, khởi động một lệnh, không cần Internet | `RESEARCH` §2.11.4 (3) |
| 1.5.5. Những gì đồ án không tuyên bố | Bốn điều loại trừ tường minh | `RESEARCH` §2.11.5 |

> **Bẫy phải tránh ở 1.5.2.** `RESEARCH` §2.11.4 đã ghi rõ: mệnh đề "loại trừ 6 chữ cái I J O Q R W" là **SAI**. Tập loại trừ toàn hệ thống chỉ có **5 chữ: I, J, O, Q, W**; chữ **R hợp lệ** ở vị trí seri thứ hai của biển xe máy. Đóng góp phải được trình bày là **đúng đắn về pháp lý và đúng cấu trúc theo vị trí**, không được trình bày như một cải thiện lớn về không gian tìm kiếm.

### 1.6. Cấu trúc quyển đồ án

Đoạn văn ngắn giới thiệu nội dung sáu chương. Viết **sau cùng**, khi cả sáu chương đã xong, để mô tả khớp với nội dung thật.

---

## 5. CHƯƠNG 2 — TỔNG QUAN VÀ CƠ SỞ LÝ THUYẾT

**Trạng thái:** ✅ **Đã viết** — tệp `docs/papers/ch2-tong-quan.md` · **Độ dài ước lượng:** 28–34 trang
**Nguồn chính:** `RESEARCH` (toàn bộ), `VNPLATE`, `YOLO`, `OCR`, `TECH`, `DATASET`

Đây là chương dài nhất và là chương có sẵn nhiều nguyên liệu nhất. Phần lớn công việc là **biên tập và cô đọng** sáu báo cáo Phase 1 thành văn bản liền mạch, không phải nghiên cứu mới.

> **Cảnh báo về cách chuyển nguồn.** Sáu báo cáo Phase 1 dẫn nguồn bằng **URL markdown nội tuyến** để đọc được trực tiếp trên GitHub. Quyển đồ án dùng **ký hiệu `[n]` + khoá BibTeX trong comment HTML**. Việc chuyển đổi tra qua `CITEMAP`. **Không sửa sáu báo cáo gốc** — làm vậy sẽ phá khả năng đọc trực tiếp của chúng, đúng như `CITEMAP` đã cảnh báo.

### 2.1. Tổng quan bài toán ALPR

| Mục | Nội dung | Nguồn |
|---|---|---|
| 2.1.1. Định nghĩa và các thành phần của một hệ thống ALPR | Bốn khối kinh điển: phát hiện xe → phát hiện biển → tách ký tự → nhận dạng ký tự | `RESEARCH` §2.2.1, §2.2.3 |
| 2.1.2. Ứng dụng thực tế | Thu phí, bãi xe, giám sát, kiểm soát ra vào | `RESEARCH` §2.2.2 |
| 2.1.3. Lịch sử phát triển qua ba giai đoạn | Xử lý ảnh cổ điển (trước ~2015) → deep learning hai giai đoạn (~2016–2020) → end-to-end, Transformer và VLM (2020–2026) | `RESEARCH` §2.3.1–2.3.3 |

### 2.2. Phân loại các hướng tiếp cận

| Mục | Nội dung | Nguồn |
|---|---|---|
| 2.2.1. Two-stage và end-to-end | Ưu nhược của từng hướng | `RESEARCH` §2.4.1 |
| 2.2.2. Segmentation-based và segmentation-free | Vì sao segmentation-free thắng thế | `RESEARCH` §2.4.2 |
| 2.2.3. Hai chiến lược đối lập cho vấn đề đa layout | Chuẩn hoá hình học trước OCR, hoặc để mô hình tự học layout | `RESEARCH` §2.4.3 |

Kết thúc mục 2.2 phải nêu rõ **đồ án chọn hướng nào và vì sao**: two-stage + segmentation-free, vì cho phép thay bộ OCR mà không huấn luyện lại toàn hệ thống — một ràng buộc kiến trúc cứng (NFR-M5), không phải sở thích (`RESEARCH` §2.11.2).

### 2.3. Các công trình tiêu biểu

| Mục | Nội dung | Nguồn |
|---|---|---|
| 2.3.1. Công trình quốc tế | Bảng tổng hợp theo năm, phương pháp, bộ dữ liệu, kết quả | `RESEARCH` §2.5.1 |
| 2.3.2. Ba lưu ý khi đọc bảng so sánh | Số liệu không so sánh trực tiếp được giữa các bài | `RESEARCH` §2.5.2 |
| 2.3.3. Nghiên cứu về biển số Việt Nam | Dòng chảy nghiên cứu trong nước; hiện trạng; hệ sinh thái mã nguồn mở; giải pháp thương mại | `RESEARCH` §2.7.1–2.7.6 |
| 2.3.4. Khoảng trống nghiên cứu | Sáu khoảng trống — nối trực tiếp sang mục 1.5 | `RESEARCH` §2.11.3 |

### 2.4. Cơ sở lý thuyết phát hiện đối tượng

| Mục | Nội dung | Nguồn |
|---|---|---|
| 2.4.1. Mạng nơ-ron tích chập | Tích chập, pooling, backbone — trình bày ở mức đủ dùng, không sa đà | Kiến thức nền; đối chiếu `YOLO` §3 |
| 2.4.2. Bài toán phát hiện đối tượng và họ YOLO | One-stage vs two-stage; lịch sử YOLOv1 → YOLO26 | `YOLO` §1, §2 |
| 2.4.3. Kiến trúc YOLO11 | Backbone–neck–head; các khối C3k2, C2PSA, SPPF | `YOLO` §3.4 |
| 2.4.4. NMS, hàm mất mát và siêu tham số then chốt | | `YOLO` §3, §6 |
| 2.4.5. Luận cứ chọn YOLO11 | So sánh benchmark; vấn đề giấy phép AGPL-3.0; phù hợp bài toán biển số | `YOLO` §4, §6, §7, §9 |

> **Vấn đề giấy phép phải nêu, không được lờ đi** (`YOLO` §7): Ultralytics phát hành theo **AGPL-3.0**. Với một đồ án học thuật không thương mại hoá thì chấp nhận được, nhưng phải ghi rõ điều kiện — đây là câu hỏi phản biện có thật.

### 2.5. Cơ sở lý thuyết nhận dạng ký tự quang học

| Mục | Nội dung | Nguồn |
|---|---|---|
| 2.5.1. Hai giai đoạn: text detection và text recognition | | `OCR` §2.1 |
| 2.5.2. Kiến trúc CRNN và hàm mất mát CTC | CNN trích đặc trưng → BiLSTM mô hình hoá chuỗi → CTC giải mã không cần căn chỉnh | `OCR` §2 |
| 2.5.3. Khảo sát các engine OCR | PaddleOCR, EasyOCR, Tesseract, TrOCR, docTR, MMOCR, fast-plate-ocr, RapidOCR | `OCR` §2, §3 |
| 2.5.4. Luận cứ chọn PaddleOCR | Kèm phần tự phản biện: PaddleOCR có thực sự là lựa chọn đúng không | `OCR` §5, §6 |
| 2.5.5. Vấn đề biển số hai dòng — rủi ro R-04 | Vì sao pipeline OCR dựng sẵn gãy trên biển hai dòng; các phương án tách–ghép | `OCR` §4; `SCOPE` §7 R-04 |

Mục 2.5.5 là **mục kỹ thuật quan trọng nhất của Chương 2**. Nó thiết lập cơ sở lý thuyết cho khối thiết kế tương ứng ở mục 3.3.3 và cho phân tích lỗi ở Chương 5.

### 2.6. Quy chuẩn biển số xe Việt Nam

**Nguồn duy nhất được phép dùng cho toàn bộ mục 2.6: `VNPLATE`.** Đây là tài liệu chuẩn pháp lý của dự án, đã qua vòng kiểm chứng đối kháng.

| Mục | Nội dung | Nguồn |
|---|---|---|
| 2.6.1. Căn cứ pháp lý hiện hành | TT 79/2024/TT-BCA (ký 15/11/2024, hiệu lực 01/01/2025), sửa đổi bởi TT 13/2025 và TT 51/2025; kích thước theo QCVN 08:2024/BCA | `VNPLATE` §1.2 |
| 2.6.2. Cấu trúc biển số ô tô | Mã tỉnh + 1 chữ cái seri + 4–5 chữ số | `VNPLATE` §2 |
| 2.6.3. Cấu trúc biển số xe máy | Hai kiểu lưu hành song song: seri 2 chữ cái (từ 15/8/2023) và kiểu cũ 1 chữ cái + 1 chữ số | `VNPLATE` §3 |
| 2.6.4. Bảng mã tỉnh/thành phố | **81 mã đang dùng**; **8 mã không dùng: 13, 42, 44, 45, 46, 87, 91, 96**; bối cảnh sáp nhập đơn vị hành chính 2025 | `VNPLATE` §4 |
| 2.6.5. Tập ký tự seri hợp lệ | Vị trí 1 thuộc 20 chữ (có G, không R); vị trí 2 của biển xe máy thuộc 20 chữ **KHÁC** (có R, không G); loại trừ toàn hệ thống 5 chữ **I J O Q W** | `VNPLATE` §5 |
| 2.6.6. Màu nền và ý nghĩa | QCVN 08:2024/BCA chỉ có 4 tổ hợp màu; xe điện **không** có biển riêng | `VNPLATE` §6 |
| 2.6.7. Kích thước vật lý và tỷ lệ khung hình | Ô tô dài 520×110 mm (AR 4,727 — 1 dòng); ô tô ngắn 330×165 mm (AR 2,000 — 2 dòng); xe máy 190×140 mm (AR 1,357 — 2 dòng) | `VNPLATE` §7.2 |
| 2.6.8. Khoảng trống tỷ lệ khung hình | Cơ sở định lượng cho ngưỡng phân loại layout tự động | `VNPLATE` §7.3 |
| 2.6.9. Các trường hợp đặc biệt | Biển quân đội (TT 169/2021/TT-BQP, ngoài phạm vi TT 79/2024), biển ngoại giao, biển định danh | `VNPLATE` §10 |

**Ba cảnh báo bắt buộc phải giữ nguyên khi viết mục 2.6:**

1. **Thông tư 24/2023/TT-BCA đã HẾT HIỆU LỰC từ 01/01/2025.** Chỉ được nhắc như bối cảnh lịch sử, tuyệt đối không dùng làm căn cứ. `VNPLATE` §1.1 ghi đây là lỗi mức critical đã phát hiện và sửa trong vòng phản biện Phase 1.
2. **Tập loại trừ là 5 chữ, không phải 6.** Chữ **R hợp lệ**. `VNPLATE` §5.2.
3. **Charset huấn luyện OCR vẫn nên dùng đầy đủ A–Z + 0–9.** Ràng buộc ký tự áp ở tầng **hậu xử lý theo vị trí**, không áp ở tầng OCR — nếu ép charset ngay từ OCR thì mất khả năng phát hiện lỗi và mất luôn dữ liệu để phân tích. `VNPLATE` §9.4 (vùng cấm sửa lỗi).

### 2.7. Các chỉ số đánh giá

| Mục | Nội dung | Nguồn |
|---|---|---|
| 2.7.1. Nhóm chỉ số phát hiện | IoU, precision, recall, F1, mAP@0.5, mAP@0.5:0.95 — kèm công thức | `RESEARCH` §2.9.1 |
| 2.7.2. Nhóm chỉ số nhận dạng | CER, WER, plate-level accuracy (khớp chuỗi tuyệt đối) | `RESEARCH` §2.9.2 |
| 2.7.3. Nhóm chỉ số end-to-end và chỉ số hiệu năng | E2E accuracy; độ trễ p50/p95/p99; FPS | `RESEARCH` §2.9.3; `NFR` §1 |
| 2.7.4. Cảnh báo về tính so sánh được | Vì sao không so sánh trực tiếp số liệu giữa các công trình khác tập dữ liệu | `RESEARCH` §2.9.4 |

### 2.8. Khảo sát bộ dữ liệu

| Mục | Nội dung | Nguồn |
|---|---|---|
| 2.8.1. Bộ dữ liệu quốc tế | CCPD, UFPR-ALPR, RodoSol-ALPR, AOLP, OpenALPR benchmarks, Global License Plate Dataset | `DATASET` §3; `RESEARCH` §2.6.1 |
| 2.8.2. Bộ dữ liệu biển số Việt Nam công khai | Bảng tổng hợp kèm quy mô, định dạng nhãn, giấy phép | `DATASET` §2; `RESEARCH` §2.7.3 |
| 2.8.3. Vấn đề chất lượng nhãn và giấy phép | Cảnh báo giấy phép; nhãn sai của bộ công khai | `DATASET` §4, §6 |
| 2.8.4. Ước lượng quy mô dữ liệu cần thiết | Cơ sở định lượng cho mục tiêu mAP ≥ 0,90 | `DATASET` §7 |

### 2.9. Công nghệ nền tảng

| Mục | Nội dung | Nguồn |
|---|---|---|
| 2.9.1. Backend: FastAPI, SQLAlchemy 2.0, Alembic, SQLite | | `TECH` §2, §3, §4 |
| 2.9.2. Frontend: React, Vite, TypeScript, TailwindCSS | | `TECH` §5, §6, §7 |
| 2.9.3. Framework học sâu và runtime suy luận CPU | PyTorch; PyTorch thuần vs ONNX Runtime vs OpenVINO | `TECH` §8, §9 |
| 2.9.4. Bảng tổng hợp quyết định công nghệ | 13 dòng quyết định kèm lý do, phương án thay thế và đánh đổi | `TECH` §10 |
| 2.9.5. Các lựa chọn KHÔNG chọn và vì sao | Django, Flask, Vue, CRA, Next.js, TensorFlow... — mỗi mục nêu điều kiện mà lựa chọn bị loại sẽ trở thành đúng | `TECH` §11 |

**Số liệu ONNX Runtime — dùng kèm cảnh báo bắt buộc:** ONNX Runtime nhanh hơn PyTorch khoảng **3,73 lần** trên CPU Intel Core i7-13700H (104,61 ms → 28,02 ms) <!-- ultralytics_2026_benchmark -->.

> ⚠️ **Cảnh báo phương pháp luận không được lược bỏ.** Con số mAP đi kèm phép đo này được đo trên **coco8 — một tập chỉ 8 ảnh**, nên **vô nghĩa về mặt thống kê**. Chỉ được dẫn phần **tốc độ**, và phải ghi rõ phần mAP không dùng được. Nguồn gốc cảnh báo: `YOLO` §5.3 và phụ lục "Danh mục các con số không được đưa vào bảng so sánh chính".

### 2.10. Tóm tắt chương

---

## 6. CHƯƠNG 3 — PHÂN TÍCH VÀ THIẾT KẾ HỆ THỐNG

**Trạng thái:** ✅ **Đã viết** — tệp `docs/papers/ch3-phan-tich-thiet-ke.md` · **Độ dài ước lượng:** 22–26 trang
**Nguồn chính:** `SRS`, `FR`, `NFR`, `ARCH`, `VNPLATE` §8–9, `OCR` §4

Chương này mô tả **thiết kế**, không mô tả **mã nguồn**. Ranh giới với Chương 4: Chương 3 trả lời *"hệ thống được thiết kế thế nào và vì sao"*; Chương 4 trả lời *"nó được cài đặt bằng gì và ra sao"*.

> **Lợi thế cần khai thác.** Backend đã chạy được và đã xác minh bằng HTTP thật (**10 endpoint** — 10 thao tác trên 9 đường dẫn; `/docs`, `/redoc`, `/openapi.json` do FastAPI tự sinh nên không tính vào con số này — Alembic migrate xong, Swagger render được). Nghĩa là Chương 3 mô tả một thiết kế **đã được kiểm chứng bằng cài đặt**, không phải thiết kế trên giấy. Điều này nên được nói rõ, vì nó làm chương mạnh hơn hẳn.

### 3.1. Phân tích yêu cầu

| Mục | Nội dung | Nguồn |
|---|---|---|
| 3.1.1. Đặc điểm người dùng và sơ đồ use case | Bốn vai trò: người vận hành, người phân tích, nhà phát triển, hội đồng đánh giá | `SRS` §2.3; `FR` §1 |
| 3.1.2. Yêu cầu chức năng | **34 FR** chia 6 nhóm — **21 Must, 6 Should, 3 Could, 4 Won't** (MoSCoW). Bốn yêu cầu Won't (FR-3.1, FR-3.4, FR-4.1, FR-4.2) đều thuần giao diện, chuyển mức trong hai đợt thu gọn phạm vi 2026-07-20; **FR-4.1 là yêu cầu mức Must đầu tiên bị đưa ra khỏi phạm vi** — phải nêu thẳng, không giấu | `FR` §2–7 |
| 3.1.3. Yêu cầu phi chức năng | 7 nhóm: NFR-P, A, R, U, M, S, C, SC — mọi chỉ tiêu đều **đo được bằng số** | `NFR` §1–8 |
| 3.1.4. Ràng buộc, giả định và phụ thuộc | CON-01…CON-06; A-01…A-04; D-01…D-03 | `SRS` §2.4, §2.5 |
| 3.1.5. Phân tích rủi ro | R-01…R-07 kèm phương án ứng phó | `SCOPE` §7 |

**Điểm phải nhấn ở 3.1.3** (`NFR` §0): mọi chỉ tiêu hiệu năng là **chỉ tiêu CPU**, do máy phát triển không có GPU CUDA (CON-02). Đây là lý do các ngưỡng độ trễ trông "rộng rãi" hơn các bài báo ALPR đo trên GPU. Nói rõ điều này là yêu cầu về trung thực học thuật.

**Điểm phải nhấn ở 3.1.3** (`NFR` §2): **NFR-A5 và NFR-A6 phải đo tách bạch.** Hiệu số giữa chúng chính là đóng góp định lượng của khối hậu xử lý — nối thẳng sang mục 1.5.2 và mục 5.4.

### 3.2. Kiến trúc tổng thể

| Mục | Nội dung | Nguồn |
|---|---|---|
| 3.2.1. Bốn nguyên tắc kiến trúc | Không trộn mã AI với mã API; thay thế được thành phần; không hard-code đường dẫn; chạy được không cần GPU | `ARCH` §1 |
| 3.2.2. Kiến trúc phân tầng năm tầng | Trình bày → API → nghiệp vụ → AI → dữ liệu | `ARCH` §2 |
| 3.2.3. Ranh giới hệ thống | Colab nằm **ngoài** ranh giới — hệ thống khi vận hành không phụ thuộc dịch vụ ngoài nào | `SCOPE` §4 |
| 3.2.4. Cấu trúc thư mục dự án | | `ARCH` §7 |

> **Điểm mấu chốt của mục 3.2.2** (`ARCH` §2): trong sơ đồ kiến trúc, tầng AI **không có mũi tên nào đi lên**. Nó không biết gì về HTTP, về CSDL, hay về việc ai gọi nó. Đây là điều làm cho NFR-M1 và NFR-M5 kiểm chứng được bằng một lệnh `grep`, chứ không phải một lời hứa.

### 3.3. Thiết kế pipeline AI

| Mục | Nội dung | Nguồn |
|---|---|---|
| 3.3.1. Luồng xử lý tổng quát | Sơ đồ mermaid: tiền xử lý → detection → cắt → phân nhánh layout → OCR → chuẩn hoá → kiểm tra hợp lệ → lưu | `ARCH` §3 |
| 3.3.2. Khối phát hiện biển số | `PlateDetector` — YOLO11, ngưỡng confidence, NMS | `ARCH` §2; `YOLO` §9 |
| 3.3.3. Khối phân loại layout và tách biển hai dòng | Phân loại theo tỷ lệ khung hình; thuật toán tách trên/dưới rồi ghép | `VNPLATE` §7.3; `OCR` §4 |
| 3.3.4. Khối nhận dạng ký tự | `PlateRecognizer` — PaddleOCR, xử lý ba bẫy đã biết của PaddleOCR | `OCR` §7.4 |
| 3.3.5. Khối chuẩn hoá và hậu xử lý theo vị trí | Regex theo từng loại biển; mặt nạ vị trí; bảng ép về chữ số / ép về chữ cái; **vùng cấm sửa lỗi** | `VNPLATE` §8, §9 |
| 3.3.6. Giao diện trừu tượng và khả năng thay thế | Cơ sở của NFR-M5; cũng là lý do `StubPipeline` tồn tại được | `ARCH` §1; `NFR` M5 |

**Nội dung kỹ thuật đặc sắc nhất của Chương 3 nằm ở 3.3.5.** Ý tưởng trung tâm (`VNPLATE` §9.1): **sửa lỗi theo VỊ TRÍ, không sửa lỗi toàn cục**. Mặt nạ vị trí phân biệt ba loại ô: `D` bắt buộc là chữ số, `L` bắt buộc là chữ cái, `?` là wildcard — **tuyệt đối không ép kiểu ở ô wildcard**. Ví dụ luật đúng: `0 → D` chứ **không phải** `0 → O`, vì O không thuộc tập seri hợp lệ.

> **Ghi chú trung thực bắt buộc** (`VNPLATE` §9.8): bảng luật sửa lỗi OCR hiện dựa trên **suy luận về hình dạng ký tự**, chưa có số liệu đo. Ma trận nhầm lẫn ký tự 36×36 để hiệu chỉnh bảng luật này là việc còn treo, phải làm ở Phase 4. Chương 3 phải ghi rõ điều này thay vì trình bày bảng luật như một kết quả đã được xác nhận bằng thực nghiệm.

### 3.4. Thiết kế backend

| Mục | Nội dung | Nguồn |
|---|---|---|
| 3.4.1. Phân tầng router – service – repository | | `ARCH` §2 |
| 3.4.2. Đặc tả các nhóm endpoint | Nhóm detect, history, statistics, health | `ARCH` §2; `FR` |
| 3.4.3. Sơ đồ tuần tự — nhận dạng ảnh | | `ARCH` §4 |
| 3.4.4. Sơ đồ tuần tự — nhận dạng video bất đồng bộ | Trả `202 Accepted` kèm `job_id`, không giữ kết nối chờ | `ARCH` §5 |
| 3.4.5. Xử lý lỗi và ghi log có cấu trúc | Không rò rỉ stack trace ra người dùng cuối | `FR` FR-6.2, FR-6.3 |

Cơ sở của thiết kế bất đồng bộ ở 3.4.4 (`ARCH` §5): một video 60 giây trên CPU mất khoảng 200 giây, chắc chắn vượt timeout HTTP thông thường. Đây là ràng buộc NFR-SC3, không phải lựa chọn thẩm mỹ.

### 3.5. Thiết kế cơ sở dữ liệu

| Mục | Nội dung | Nguồn |
|---|---|---|
| 3.5.1. Sơ đồ thực thể – liên kết (ER) | Hai bảng: `DetectionHistory` và `DetectionJob` | `ARCH` §6.1 |
| 3.5.2. Bảng `DetectionHistory` | Đặc tả từng trường | `ARCH` §6.1 |
| 3.5.3. Sáu trường mở rộng và luận cứ | `raw_ocr_text`, `ocr_confidence`, `bbox_*`, `is_valid_format`, `plate_line_count`, `source_job_id` | `ARCH` §6.2 |
| 3.5.4. Bảng `DetectionJob` | Bảng mới, cần cho FR-2.1 và FR-2.6 | `ARCH` §6.2 |
| 3.5.5. Quản lý migration bằng Alembic | | `TECH` §3 |

> **Luận cứ đắt giá nhất ở 3.5.3** (`ARCH` §6.2): thiếu `raw_ocr_text` thì **không thể đo được NFR-A5 so với NFR-A6**, tức mất luôn một đóng góp học thuật định lượng. Thiếu `source_job_id` thì một ảnh chứa 3 biển số thành 3 bản ghi rời rạc, và `GET /api/statistics` sẽ đếm thành "3 lượt nhận dạng" thay vì "1 ảnh có 3 biển số" — toàn bộ thống kê FR-4.1 sai lệch. Đây là ví dụ tốt cho thấy thiết kế CSDL là quyết định học thuật, không phải chi tiết vụn vặt.

### 3.6. Thiết kế giao diện người dùng

| Mục | Nội dung | Nguồn |
|---|---|---|
| 3.6.1. Kiến trúc SPA và sơ đồ điều hướng | **Ba màn hình**: Nhận dạng ảnh (trang chủ `/`), Nhận dạng video (`/video`), Lịch sử (`/history`); đường dẫn không tồn tại chuyển hướng về `/`. *Hai đợt thu gọn phạm vi ngày 2026-07-20 đã gỡ trang Webcam rồi tới trang Tổng quan (Dashboard) — năng lực thời gian thực và số liệu thống kê đều giữ ở tầng API* | `SRS` §5.1 |
| 3.6.2. Thiết kế từng màn hình | Ba màn hình hiện hành, cộng ghi chú lịch sử về hai màn hình đã gỡ. *(FR-3.1/FR-3.4 chuyển M→W ở đợt 1; **FR-4.1 chuyển M→W** và FR-4.2 chuyển S→W ở đợt 2)* | `FR` FR-1.7, FR-2.6, FR-4.x |
| 3.6.3. Nguyên tắc phản hồi và thông báo lỗi | Phản hồi trực quan cho mọi thao tác > 500 ms; thông báo lỗi tiếng Việt nêu rõ cách khắc phục | `NFR` U2, U3 |
| 3.6.4. Khả năng tiếp cận | Tương phản đạt WCAG AA (≥ 4,5:1) | `NFR` U5 |

### 3.7. Thiết kế bảo mật và kiểm soát đầu vào

| Mục | Nội dung | Nguồn |
|---|---|---|
| 3.7.1. Mô hình đe doạ trong phạm vi đồ án | Hệ thống chạy nội bộ (giả định A-04) | `NFR` §6 |
| 3.7.2. Kiểm tra tệp tải lên bằng magic bytes | Không tin phần mở rộng tệp | `NFR` S1 |
| 3.7.3. Chống path traversal, đặt tên tệp bằng UUID | | `NFR` S2; `ARCH` AD-08 |
| 3.7.4. Giới hạn kích thước, CORS, tham số hoá truy vấn | | `NFR` S3, S4, S6 |

### 3.8. Các quyết định thiết kế và đánh đổi

Bảng **AD-01 … AD-08** (`ARCH` §8), mỗi dòng gồm: quyết định, lựa chọn, lý do, đánh đổi phải chấp nhận. Phần thảo luận sâu về **AD-03** (vì sao chọn HTTP thay vì WebSocket cho chế độ thời gian thực) nên giữ nguyên lập luận gốc: ở mức ~5 FPS trên CPU, nút thắt là **thời gian suy luận** (~300–400 ms/khung), không phải overhead HTTP (vài ms). WebSocket sẽ thêm độ phức tạp mà không chạm vào nút thắt thật. Lập luận không đổi sau khi trang Webcam được gỡ khỏi giao diện (2026-07-20): "client" trong quyết định nay là bất kỳ chương trình nào gọi `POST /api/detect/frame`.

### 3.9. Tóm tắt chương

---

## 7. CHƯƠNG 4 — CÀI ĐẶT HỆ THỐNG ✅ ĐÃ VIẾT

**Trạng thái:** ✅ **Đã viết** — tệp `docs/papers/ch4-cai-dat.md` · **Độ dài ước lượng:** 20–24 trang

### Điều kiện tiền đề — đều đã thoả

| Khối | Trạng thái | Phục vụ mục nào |
|---|---|---|
| Bộ dữ liệu đã làm sạch | ✅ Split v3 đã chốt: train 10.592 / val 3.027 / test 1.514 | 4.5 |
| Mô hình `best.pt` | ✅ **Đã huấn luyện xong** (YOLO11n, `imgsz=640`, split v3, 20 epoch; mAP@0.5 0,9829) | 4.2 |
| Module OCR + hậu xử lý thực | ✅ Đã cài đặt và đo (A5 0,6098 → A6 0,6555) | 4.2 |
| Backend | ✅ Đã chạy — 10 endpoint | 4.3 |
| Frontend | ✅ **Hoàn thành**, build sạch | 4.4 |
| Docker / Docker Compose | ✅ Đã đóng gói | 4.6 |

### Khung mục thực tế của chương đã viết

| Mục | Nội dung |
|---|---|
| 4.1. Môi trường và công cụ phát triển | Cấu hình local, môi trường huấn luyện từ xa, môi trường Docker (`ENV`) |
| 4.2. Cài đặt tầng AI | Detector YOLO11n, tích hợp PaddleOCR, xử lý biển hai dòng, khối chuẩn hoá và hậu xử lý theo vị trí |
| 4.3. Cài đặt backend | Router, service, repository, model, migration |
| 4.4. Cài đặt frontend | Ba màn hình (48 mô-đun), tầng gọi API sáu hàm, ánh xạ kiểu, vẽ overlay; ghi chú lịch sử về hai màn hình đã gỡ 2026-07-20 |
| 4.5. Xây dựng bộ dữ liệu | Thu thập, gộp, làm sạch, kiểm tra nhãn, khử trùng lặp, chia tập, augmentation |
| 4.6. Triển khai bằng Docker | Dockerfile, docker-compose |
| 4.7. Những chỗ cài đặt lệch khỏi thiết kế ở Chương 3, và lý do | |
| 4.8. Kết luận chương | |

---

## 8. CHƯƠNG 5 — THỰC NGHIỆM VÀ ĐÁNH GIÁ ✅ ĐÃ VIẾT

**Trạng thái:** ✅ **Đã viết** — tệp `docs/papers/ch5-thuc-nghiem.md` · **Độ dài ước lượng:** 22–28 trang

### Nguồn số liệu của chương

Mô hình chính thức `models/best.pt` (YOLO11n, `imgsz=640`, split v3, 20 epoch) **đã huấn luyện xong**; `/health` báo `model_loaded: true` với engine `yolo:best.pt+paddleocr-PP-OCRv5-mobile`. Toàn bộ số công bố trong chương lấy từ mô hình này.

`models/baseline-416-v1.pt` **chỉ còn là mô hình đối chứng** và **tuyệt đối không dùng làm số liệu công bố**, vì hai khiếm khuyết độc lập: huấn luyện ở `imgsz=416` trong khi chỉ tiêu NFR-A1/A2 đặt ở 640, và dùng split v1 vốn **có rò rỉ train↔test** (619 cặp ảnh gần trùng ở ngưỡng phash 10). Số của nó (mAP@0.5 0,9933; mAP@0.5:0.95 0,8597) **cao hơn** `best.pt` chính vì rò rỉ thổi phồng — đây là ví dụ điển hình cần nêu khi bảo vệ.

**Kết quả chính đã đo:**

| Nhóm | Kết quả | Ngưỡng | Kết luận |
|---|---|---|---|
| Detection (NFR-A1/A2/A3) | mAP@0.5 0,9829 · mAP@0.5:0.95 0,7834 · P 0,9837 · R 0,9714 | — | ✅ Đạt cả bốn |
| NFR-A4 (1 − CER) | 0,8734 | 0,92 | ❌ Chưa đạt |
| NFR-A5 (trước hậu xử lý) | 0,6098 | 0,80 | ❌ Chưa đạt |
| NFR-A6 (sau hậu xử lý) | 0,6555 (+4,57 điểm; 128 biển sửa đúng, 0 biển hỏng) | 0,85 | ❌ Chưa đạt |
| NFR-A7 (end-to-end) | 0,5227 | 0,82 | ❌ Chưa đạt |
| NFR-A8 (tách theo layout) | 1 dòng A6 0,9489 (567 mẫu) ↔ 2 dòng A6 0,5810 (2.234 mẫu); chênh 36,79 điểm | — | ✅ Đã đo |
| NFR-P1 (độ trễ ảnh p95) | 731,15 ms client-side / 780,36 ms in-process | 800 ms | ✅ Đạt |

> **Ranh giới liêm chính học thuật.** Bốn chỉ tiêu A4–A7 **chưa đạt ngưỡng** và chương đã ghi đúng như vậy. Không được làm tròn lên, không được đổi ngưỡng cho khớp kết quả. Một quyển trung thực về chỉ tiêu chưa đạt vẫn bảo vệ được; một quyển sửa số thì không.

### Khung mục thực tế của chương đã viết

| Mục | Nội dung | Chỉ tiêu đối chiếu |
|---|---|---|
| 5.1. Mục tiêu và phương pháp đánh giá | Giao thức đo, định nghĩa chỉ tiêu | `NFR` §0 |
| 5.2. Môi trường thực nghiệm | Cấu hình phần cứng, số luồng, backend suy luận | `NFR` §0 |
| 5.3. Bộ dữ liệu thực nghiệm | Split v3, khử trùng lặp, kiểm tra rò rỉ | — |
| 5.4. Quá trình huấn luyện | Siêu tham số, đường cong loss | `SCOPE` §2.1 |
| 5.5. Đánh giá bộ phát hiện biển số | mAP@0.5, mAP@0.5:0.95, precision, recall | NFR-A1, A2, A3 |
| 5.6. Đánh giá khối OCR và hậu xử lý | CER; **độ chính xác trước và sau hậu xử lý, đo tách bạch**; tách theo layout | NFR-A4, **A5 vs A6**, A7, **A8** |
| 5.7. Đánh giá hiệu năng | Độ trễ p50/p95/p99, nạp mô hình, overhead API, truy vấn, bộ nhớ | NFR-P1…P7 |
| 5.8. Khảo sát ảnh hưởng của độ phân giải và chất lượng split | 416/v1 ↔ 640/v3, phân tích rò rỉ | — |
| 5.9. Đối chiếu toàn bộ chỉ tiêu phi chức năng | Bảng "chốt hạ" trình bày khi bảo vệ | `NFR` §9 |
| 5.10. Phân tích lỗi | Các trường hợp thất bại điển hình | `VNPLATE` §9.8 |
| 5.11. Bàn luận | | |
| 5.12. Kết luận chương | | |
| Phụ lục kỹ thuật | Ánh xạ số liệu và lệnh tái lập | — |

> **Các phép đo chưa thực hiện, đã ghi rõ trong chương:** NFR-P2 (FPS webcam), NFR-P3 (tốc độ xử lý video), NFR-A9 (đánh giá theo điều kiện ảnh — bộ dữ liệu không có nhãn phù hợp), NFR-R5.

**Hai nội dung là đóng góp học thuật cốt lõi, không được bỏ:**

- **Hiệu số A6 − A5 = +4,57 điểm** (0,6098 → 0,6555; 128 biển sửa đúng, 0 biển hỏng) chính là đóng góp định lượng của khối hậu xử lý (mục 1.5.2).
- **Bảng tách theo layout** (1 dòng A6 0,9489 ↔ 2 dòng A6 0,5810, chênh 36,79 điểm) lấp đúng khoảng trống đã xác định: chưa nghiên cứu Việt Nam nào công bố hai con số này tách bạch trên cùng một hệ thống (`RESEARCH` §2.8.2, §2.11.3).

---

## 9. CHƯƠNG 6 — KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN ✅ ĐÃ VIẾT

**Trạng thái:** ✅ **Đã viết** — tệp `docs/papers/ch6-ket-luan.md` · **Độ dài ước lượng:** 5–7 trang

Chương kết luận đối chiếu kết quả thật ở Chương 5 với mục tiêu đề ra ở Chương 1.

### Khung mục thực tế của chương đã viết

| Mục | Nội dung |
|---|---|
| 6.1. Tổng kết công việc đã thực hiện | Toàn bộ 11 phase |
| 6.2. Các kết quả đạt được | Đối chiếu với mục tiêu 1.2 và tiêu chí thành công `SCOPE` §6 |
| 6.3. Các hạn chế của đồ án | Xem danh sách bên dưới |
| 6.4. Hướng phát triển | Xem danh sách bên dưới |
| 6.5. Kết luận chung | |

**Mục 6.3 — các hạn chế**, gồm nhóm đã xác định trước từ Phase 0–1 và nhóm phát sinh từ kết quả thực nghiệm:

- **Bốn chỉ tiêu độ chính xác chưa đạt ngưỡng đề ra:** A4 0,8734 (ngưỡng 0,92), A5 0,6098 (0,80), A6 0,6555 (0,85), A7 0,5227 (0,82). Nguyên nhân chi phối là biển hai dòng — chiếm 79,8% tập đánh giá nhưng A6 chỉ đạt 0,5810 so với 0,9489 của biển một dòng.
- **Một số phép đo chưa thực hiện:** NFR-P2 (FPS webcam), NFR-P3 (video), NFR-A9, NFR-R5.
- **Một yêu cầu mức *Must* bị đưa ra khỏi phạm vi (mục 6.3.6):** FR-4.1 (màn hình thống kê tổng hợp) chuyển M→W, kèm FR-4.2 chuyển S→W, khi trang Tổng quan bị gỡ khỏi giao diện ngày 2026-07-20. **Đây là lần đầu và duy nhất trong đồ án một yêu cầu Must bị hạ mức** — phải nêu thẳng khi bảo vệ. Năng lực vẫn phục vụ và vẫn có kiểm thử ở tầng API (`GET /api/statistics`, `GET /health`); bộ Must đáp ứng được là bộ **21**, không phải 22.

- SQLite chỉ cho phép **một tiến trình ghi tại một thời điểm**; hướng khắc phục là chuyển sang PostgreSQL nếu triển khai thực tế (`NFR` §8). Đây là câu hỏi phản biện rất dễ gặp.
- Mọi số liệu hiệu năng là **số liệu CPU**, không so sánh trực tiếp được với các con số FPS đo trên GPU (`RESEARCH` §2.11.5).
- Bảng luật sửa lỗi OCR dựa trên suy luận hình dạng ký tự, chưa hiệu chỉnh bằng ma trận nhầm lẫn đo được (`VNPLATE` §9.8).
- Đồ án không giải quyết các thách thức mở: độ phân giải thấp, tổng quát hoá xuyên tập dữ liệu, che khuất nặng (`RESEARCH` §2.10, §2.11.5).

**Mục 6.4 — các hướng phát triển đã được xác định trước:**

- Bám vết đối tượng qua khung hình (SORT/DeepSORT) thay cho gộp trùng theo chuỗi ký tự (`SCOPE` §3).
- **Khôi phục hai màn hình đã gỡ từ lịch sử git** (mục 6.4.6): Webcam và Tổng quan. Endpoint, kiểm thử và các kiểu dữ liệu hợp đồng đều còn nguyên, nên đây là thao tác phục hồi chứ không phải xây mới; nếu dựng lại phần biểu đồ thì nên chọn thư viện nhẹ hơn `recharts` để không mất mức giảm 730 KB → 328,8 KB.
- Huấn luyện riêng một mô hình OCR cho biển số Việt Nam thay vì dùng PaddleOCR pre-trained (`SCOPE` §3).
- Chuyển sang WebSocket nếu đo được HTTP là nút cổ chai thực sự (`ARCH` AD-03).
- Lượng tử hoá INT8 với tập hiệu chuẩn để tối ưu thêm trên CPU Intel (`TECH` §9).
- Năm xu hướng nghiên cứu mới 2024–2026: super-resolution, sinh dữ liệu bằng diffusion, VLM, pseudo-labeling, mô hình layout-independent (`RESEARCH` §2.10.2).

---

## 10. Phần cuối quyển

| Phần | Nội dung | Trạng thái |
|---|---|---|
| Tài liệu tham khảo | Sinh từ `BIB` (232 entry, 211 đã được trích ở Phase 1) | 🔵 Sinh khi ghép |
| Phụ lục A | Bảng mã tỉnh/thành phố đầy đủ (`VNPLATE` §4) | ✅ Sẵn sàng |
| Phụ lục B | Toàn bộ regex và bảng luật sửa lỗi (`VNPLATE` §8, §9) | ✅ Sẵn sàng |
| Phụ lục C | Đặc tả đầy đủ 34 yêu cầu chức năng (`FR`) | ✅ Sẵn sàng |
| Phụ lục D | Đặc tả API / trích Swagger | 🔵 Backend đã chạy — trích được |
| Phụ lục E | Bảng số liệu thực nghiệm chi tiết | ✅ Sẵn sàng — trích từ phụ lục kỹ thuật của Chương 5 và `docs/reports/05-results.json` |

> **Lưu ý về nhóm *Further reading* trong `BIB`.** 21 entry ở nhóm `% === Further reading (not cited) ===` **chưa được trích ở bất kỳ báo cáo Phase 1 nào**. Trước khi dùng bất kỳ entry nào trong số đó cho quyển đồ án, phải đọc và kiểm chứng lại nguồn, rồi chuyển entry lên đúng mục chủ đề trong `.bib`. Không được `\cite{}` thẳng từ nhóm này (`CITEMAP`).

---

## 11. Thứ tự viết đề nghị

Không viết theo thứ tự chương. Thứ tự dưới đây tối ưu theo mức độ sẵn sàng của nguyên liệu — **các bước 1–7 đều đã hoàn thành**:

| Bước | Việc | Phụ thuộc | Trạng thái |
|:---:|---|---|---|
| 1 | Phần đầu quyển: danh mục từ viết tắt, hai abstract | ✅ Không | ✅ Xong (abstract đã cập nhật số thật) |
| 2 | **Chương 2** — nhiều nguyên liệu nhất, ít phụ thuộc nhất | ✅ Không | ✅ Xong |
| 3 | **Chương 3** — backend đã chạy, thiết kế đã được kiểm chứng | ✅ Không | ✅ Xong |
| 4 | **Chương 1** — viết sau Chương 2–3 để phần đóng góp bám sát nội dung thật | Bước 2, 3 | ✅ Xong |
| 5 | Chương 4 | `best.pt` | ✅ Xong |
| 6 | Chương 5 | Chương 4 | ✅ Xong |
| 7 | Chương 6 | Chương 5 | ✅ Xong |
| 8 | Mục lục + danh mục hình/bảng + ghép quyển + điền thông tin cá nhân | Toàn bộ | 🔵 Việc còn lại duy nhất |

`TIME` §5 đã ghi sẵn: *"Viết chương Tổng quan và Cơ sở lý thuyết của đồ án"* là việc nên chen vào thời gian chờ huấn luyện ở Phase 2–4. Thứ tự trên là hiện thực hoá khuyến nghị đó.

---

## 12. Tóm tắt

Đề cương này cố định cấu trúc sáu chương của quyển đồ án, ánh xạ từng mục về tài liệu nguồn Phase 0–1 tương ứng, và ước lượng 129–163 trang cho toàn quyển.

Ba chương đầu (**Mở đầu**, **Tổng quan và cơ sở lý thuyết**, **Phân tích và thiết kế hệ thống**) viết trước vì toàn bộ nguyên liệu đã hoàn thành và đã qua kiểm chứng đối kháng ở Phase 0–1, và vì backend đã chạy được nên phần thiết kế mô tả một hệ thống có thật.

**Cả sáu chương nay đã viết xong.** Mô hình chính thức `models/best.pt` (YOLO11n, `imgsz=640`, split v3, 20 epoch) đã huấn luyện xong với mAP@0.5 0,9829, và toàn bộ NFR-A4/A5/A6/A7 cùng NFR-P1 đã đo, nên **Chương 5 (Thực nghiệm và đánh giá)** và **Chương 6 (Kết luận)** đều đã viết với số liệu thật. `models/baseline-416-v1.pt` chỉ còn giữ vai trò đối chứng và không đóng góp con số nào vào Chương 5. Việc còn lại của quyển đồ án là ghép quyển: sinh mục lục và danh mục hình/bảng, điền thông tin cá nhân vào trang bìa và các biểu mẫu của khoa.
