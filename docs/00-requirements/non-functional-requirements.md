# Yêu cầu phi chức năng (Non-Functional Requirements)

**Thuộc:** [SRS.md](SRS.md) — Phase 0
**Phiên bản:** 1.0 · **Ngày:** 2026-07-19

---

## 0. Nguyên tắc đặt chỉ tiêu

> **Mọi chỉ tiêu dưới đây đều là chỉ tiêu CPU.**

Máy phát triển **không có GPU CUDA** (ràng buộc CON-02 — chỉ có Intel UHD Graphics 770). Việc huấn luyện diễn ra trên GPU miễn phí của Colab/Kaggle, nhưng **suy luận và toàn bộ phần demo bảo vệ chạy trên CPU**.

Đây là lý do các chỉ tiêu độ trễ dưới đây trông "rộng rãi" hơn so với các bài báo ALPR thường công bố (thường đo trên RTX/V100 và báo cáo vài chục mili-giây). Trong quyển đồ án, **phải nêu rõ điều này** — công bố một con số FPS mà không kèm cấu hình phần cứng là lỗi phương pháp luận, và là câu hỏi phản biện gần như chắc chắn sẽ bị hỏi.

**Quy tắc:** mọi số liệu hiệu năng công bố phải kèm: model CPU, số luồng, kích thước ảnh đầu vào, backend suy luận (PyTorch / ONNX / OpenVINO), và cỡ mẫu đo.

---

## 1. NFR-P — Hiệu năng (Performance)

| Mã | Chỉ tiêu | Mục tiêu | Ngưỡng tối thiểu | Phương pháp đo |
|---|---|---|---|---|
| **NFR-P1** | Độ trễ E2E một ảnh (p95) | ≤ 800 ms | ≤ 1500 ms | 100 ảnh test, đo p50/p95/p99 |
| **NFR-P2** | Tốc độ khung hình chế độ thời gian thực (webcam) | ≥ 5 FPS hiệu dụng | ≥ 3 FPS | Đo trong 60 giây liên tục, ở **tầng API** (xem ghi chú dưới bảng) |
| **NFR-P3** | Tốc độ xử lý video | ≥ 0.3× thời gian thực | ≥ 0.15× | Video 60 giây xử lý ≤ 200 giây |
| **NFR-P4** | Thời gian nạp mô hình khi khởi động | ≤ 15 giây | ≤ 30 giây | Đo từ lúc khởi động đến khi `/health` báo sẵn sàng |
| **NFR-P5** | Overhead của API (không tính thời gian suy luận) | ≤ 50 ms | ≤ 100 ms | So sánh tổng thời gian request và thời gian pipeline |
| **NFR-P6** | Thời gian phản hồi truy vấn lịch sử (10.000 bản ghi) | ≤ 500 ms | ≤ 1000 ms | Đo có phân trang và bộ lọc |
| **NFR-P7** | Bộ nhớ thường trú của backend | ≤ 2 GB | ≤ 4 GB | Theo dõi RSS khi chạy tải liên tục |

> **Ghi chú NFR-P2 (2026-07-20):** giao diện webcam đã gỡ khỏi phạm vi (FR-3.1/FR-3.4 chuyển M → W — xem [functional-requirements.md](functional-requirements.md)). Chỉ tiêu **giữ nguyên** nhưng được đo ở **tầng API**: gọi `POST /api/detect/frame` liên tục trong 60 giây và tính FPS hiệu dụng. Phía gọi API tự triển khai bỏ bớt khung hình (frame skipping) và/hoặc hàng đợi một khe để không dồn ứ yêu cầu.

**Phân rã ngân sách độ trễ NFR-P1** *(ước lượng ban đầu, sẽ hiệu chỉnh sau Phase 3–4)*:

| Bước | Ngân sách |
|---|---|
| Giải mã ảnh + tiền xử lý | ~50 ms |
| Suy luận YOLO11n @ 640px (CPU) | ~150 ms |
| Cắt + tiền xử lý vùng biển số | ~30 ms |
| PaddleOCR (mỗi biển) | ~120 ms |
| Hậu xử lý regex + kiểm tra hợp lệ | < 5 ms |
| Ghi CSDL + lưu ảnh | ~50 ms |
| **Tổng (1 biển số)** | **~405 ms** |

Ngân sách 800 ms để lại khoảng ~2× dự phòng cho ảnh nhiều biển số và biến động của máy.

> **Cảnh báo rủi ro:** nếu đo thực tế ở Phase 4 vượt ngưỡng, các phương án giảm tải theo thứ tự ưu tiên là: (1) xuất mô hình sang **ONNX Runtime hoặc OpenVINO** — thường nhanh gấp 2–3× so với PyTorch trên CPU Intel; (2) giảm `imgsz` xuống 480; (3) dùng biến thể PaddleOCR mobile thay vì server. Chỉ hạ chỉ tiêu **sau khi** đã thử hết ba phương án này.

---

## 2. NFR-A — Độ chính xác (Accuracy)

| Mã | Chỉ tiêu | Mục tiêu | Ngưỡng tối thiểu | Ghi chú |
|---|---|---|---|---|
| **NFR-A1** | mAP@0.5 của bộ phát hiện | ≥ 0.90 | ≥ 0.85 | Trên tập test độc lập |
| **NFR-A2** | mAP@0.5:0.95 của bộ phát hiện | ≥ 0.65 | ≥ 0.55 | Chỉ tiêu chặt hơn, phản ánh chất lượng khớp box |
| **NFR-A3** | Precision / Recall phát hiện | ≥ 0.92 / ≥ 0.90 | ≥ 0.88 / ≥ 0.85 | Tại ngưỡng confidence tối ưu theo F1 |
| **NFR-A4** | Độ chính xác OCR mức ký tự (1 − CER) | ≥ 0.95 | ≥ 0.92 | Trên vùng biển số đã cắt chuẩn |
| **NFR-A5** | Độ chính xác biển đầy đủ **trước** hậu xử lý | ≥ 0.85 | ≥ 0.80 | Khớp chuỗi tuyệt đối |
| **NFR-A6** | Độ chính xác biển đầy đủ **sau** hậu xử lý | ≥ 0.90 | ≥ 0.85 | Đo mức cải thiện do regex đem lại |
| **NFR-A7** | Độ chính xác E2E toàn trình (ảnh vào → biển đúng) | ≥ 0.88 | ≥ 0.82 | Chỉ tiêu quan trọng nhất với hội đồng |

> **NFR-A5 và NFR-A6 phải được đo tách bạch.** Hiệu số giữa chúng chính là **đóng góp định lượng của khối hậu xử lý** — một đóng góp kỹ thuật có thể trình bày và bảo vệ được, thay vì chỉ nói "chúng em có thêm bước sửa lỗi regex".

**Yêu cầu phân tích bổ sung** (phục vụ chương Đánh giá của đồ án):

- NFR-A8: Báo cáo độ chính xác **tách riêng theo biển 1 dòng và 2 dòng** — biển 2 dòng dự kiến khó hơn rõ rệt.
- NFR-A9: Báo cáo độ chính xác theo **điều kiện ảnh** (ban ngày / ban đêm / nghiêng / mờ), nếu bộ dữ liệu có nhãn phù hợp.

---

## 3. NFR-R — Độ tin cậy (Reliability)

| Mã | Chỉ tiêu | Mục tiêu |
|---|---|---|
| **NFR-R1** | Hệ thống **không sập** khi gặp đầu vào hỏng, sai định dạng hoặc độc hại | 100% — mọi lỗi đều bị bắt và xử lý |
| **NFR-R2** | Ảnh không phát hiện được biển số ⇒ trả kết quả rỗng hợp lệ, không phải lỗi | Trả HTTP 200 với danh sách rỗng |
| **NFR-R3** | Tác vụ video thất bại giữa chừng không để lại bản ghi hoặc tệp rác | Giao dịch có tính nguyên tử |
| **NFR-R4** | Tỉ lệ thành công khi chạy liên tục 1 giờ | ≥ 99% |
| **NFR-R5** | CSDL sống sót qua khởi động lại mà không mất dữ liệu | 100% |

---

## 4. NFR-U — Khả năng sử dụng (Usability)

| Mã | Chỉ tiêu | Mục tiêu |
|---|---|---|
| **NFR-U1** | Người dùng mới hoàn thành lượt nhận dạng ảnh đầu tiên mà không cần đọc tài liệu | ≤ 3 thao tác click |
| **NFR-U2** | Mọi thao tác chạy lâu đều có phản hồi trực quan (spinner / thanh tiến độ) | 100% các thao tác > 500 ms |
| **NFR-U3** | Thông báo lỗi bằng tiếng Việt, nêu rõ nguyên nhân và cách khắc phục | Không hiển thị mã lỗi kỹ thuật cho người dùng cuối |
| **NFR-U4** | Giao diện dùng được ở độ phân giải từ 1366×768 trở lên | Không vỡ layout |
| **NFR-U5** | Tương phản màu đạt WCAG AA cho chữ chính | Tỉ lệ tương phản ≥ 4.5:1 |

---

## 5. NFR-M — Khả năng bảo trì (Maintainability)

| Mã | Chỉ tiêu | Mục tiêu |
|---|---|---|
| **NFR-M1** | **Mã AI tách biệt hoàn toàn khỏi mã API** — pipeline nhận dạng không import bất cứ thứ gì của FastAPI | Kiểm tra bằng phân tích import; đây là ràng buộc cứng từ `CLAUDE.md` |
| **NFR-M2** | Độ bao phủ test cho tầng nghiệp vụ | ≥ 70% |
| **NFR-M3** | Mọi hàm public đều có type hint và docstring | 100% |
| **NFR-M4** | Không hard-code đường dẫn — mọi đường dẫn qua cấu hình | Kiểm tra bằng grep, 0 vi phạm |
| **NFR-M5** | Có thể thay bộ OCR khác mà không sửa mã tầng API | Ràng buộc bằng interface / abstract base class |
| **NFR-M6** | Mã tuân thủ định dạng và lint tự động | `ruff` + `black` cho Python, `eslint` + `prettier` cho TypeScript |

> **NFR-M1 và NFR-M5 là các yêu cầu kiến trúc, không phải nguyện vọng.** Chúng là lý do tồn tại của tầng `ai/inference` độc lập trong sơ đồ kiến trúc — xem [system-architecture.md](../architecture/system-architecture.md).

---

## 6. NFR-S — Bảo mật (Security)

Hệ thống chạy nội bộ (giả định A-04), nên mô hình đe doạ ở mức hạn chế. Tuy vậy vẫn yêu cầu:

| Mã | Chỉ tiêu | Mục tiêu |
|---|---|---|
| **NFR-S1** | Kiểm tra tệp tải lên bằng **magic bytes**, không tin phần mở rộng | Tệp giả mạo bị chặn |
| **NFR-S2** | Chống path traversal ở mọi thao tác tệp | Tên tệp được chuẩn hoá, sinh lại bằng UUID |
| **NFR-S3** | Giới hạn kích thước tệp tải lên, thực thi ở tầng server | Vượt hạn mức ⇒ HTTP 413 |
| **NFR-S4** | CORS chỉ cho phép origin đã khai báo, **không dùng `*`** | Cấu hình rõ ràng |
| **NFR-S5** | Không ghi dữ liệu nhạy cảm vào log | Không log toàn bộ nội dung tệp |
| **NFR-S6** | Truy vấn CSDL luôn tham số hoá qua ORM | Không nối chuỗi SQL thủ công |

---

## 7. NFR-C — Khả năng tương thích và triển khai (Compatibility & Portability)

| Mã | Chỉ tiêu | Mục tiêu |
|---|---|---|
| **NFR-C1** | Chạy được trên Windows, Linux và macOS thông qua Docker | `docker compose up` là lệnh duy nhất cần chạy |
| **NFR-C2** | Hoạt động **không cần GPU** | Đây là chế độ mặc định, không phải chế độ dự phòng |
| **NFR-C3** | Hỗ trợ trình duyệt Chrome, Edge, Firefox phiên bản mới | Kiểm thử thủ công ở Phase 7 |
| **NFR-C4** | Cài đặt từ đầu bằng README trên máy sạch | ≤ 15 phút, không cần hỏi thêm |

---

## 8. NFR-SC — Khả năng mở rộng (Scalability)

| Mã | Chỉ tiêu | Mục tiêu |
|---|---|---|
| **NFR-SC1** | Số yêu cầu đồng thời xử lý ổn định | ≥ 5 |
| **NFR-SC2** | Số bản ghi CSDL không làm suy giảm hiệu năng | ≥ 100.000 bản ghi |
| **NFR-SC3** | Tác vụ video chạy nền, không chặn các yêu cầu khác | Bắt buộc — dùng background task |

> **Giới hạn đã biết:** SQLite chỉ cho phép **một tiến trình ghi tại một thời điểm**. Với quy mô đồ án điều này chấp nhận được, nhưng **phải nêu rõ trong phần Hạn chế của quyển đồ án**, kèm hướng khắc phục (chuyển sang PostgreSQL) nếu triển khai thực tế. Đây là câu hỏi phản biện rất dễ gặp.

---

## 9. Tổng hợp chỉ tiêu then chốt

Bảng này dùng làm bảng "chốt hạ" trình bày khi bảo vệ:

| Hạng mục | Chỉ tiêu | Trạng thái *(cập nhật 2026-07-28)* |
|---|---|---|
| mAP@0.5 | ≥ 0.90 | ✅ **0,9829** trên `models/best.pt`, tập test split v3 ([07-benchmark-report.md](../reports/07-benchmark-report.md)) |
| Chính xác ký tự (A4) | ≥ 0.92 | 🟡 **0,9454** — đạt ngưỡng tối thiểu, dưới mục tiêu 0,95. Lật từ ❌ 0,8848 (đo 20/07) nhờ các bản sửa đọc biển 2 dòng và bậc thang thử-lại ([27](../reports/27-retry-ladder-cost-benefit.md)) |
| Chuỗi đúng sau hậu xử lý (A6) | ≥ 0.85 | ❌ **0,7512** ([05-results.json](../reports/05-results.json) T5.9). Toàn bộ khoảng cách nằm ở biển 2 dòng: biển 1 dòng đạt **0,9489**, biển 2 dòng **~0,70**. Hậu xử lý đóng góp **+11,39 điểm** và không phá hỏng biển nào |
| Độ chính xác E2E (A7) | ≥ 0.88 | ❌ **0,5552** — **cận dưới bi quan, không đại diện**: phép đo đưa ảnh biển *đã cắt sẵn* vào bộ phát hiện vốn huấn luyện trên ảnh toàn cảnh, nên 335/2.801 ca hỏng ngay ở bước phát hiện. Cùng bộ trọng số đạt mAP 0,9829 trên ảnh hiện trường. Chi tiết [27](../reports/27-retry-ladder-cost-benefit.md) mục 6 |
| Độ trễ 1 ảnh (p95, CPU) | ≤ 800 ms | 🟡 **1.143,1 ms** in-process — đạt sàn 1.500 ms, trên mục tiêu 800 ms. Bậc thang thử-lại là nguyên nhân (chỉ chạy khi đọc hỏng: p50 chỉ 405,8 ms). Tắt siêu phân giải mặc định đã kéo p95 từ 1.514 xuống 1.143 ms ([27](../reports/27-retry-ladder-cost-benefit.md) mục 5) |
| Webcam FPS (CPU) | ≥ 5 | ⬜ **Chưa đo trên `best.pt`** — đo ở tầng API `POST /api/detect/frame` (giao diện webcam đã gỡ 2026-07-20) |
| Bao phủ test | ≥ 70% | ✅ **882 test thu thập / 881 đạt + 1 `xfail`, 0 fail**. Bao phủ tầng nghiệp vụ: **87,7%** (đo 20/07/2026, [13-refactor-result.json](../reports/13-refactor-result.json)); **88,1%** ở lần đo Phase 7 trước đó ([07-testing-report.md](../reports/07-testing-report.md) mục 3.3). Cả hai mốc đều đạt |
| Triển khai một lệnh | `docker compose up` | ✅ Đã dựng và xác minh chạy được ([08-deployment-guide.md](../reports/08-deployment-guide.md)) |
