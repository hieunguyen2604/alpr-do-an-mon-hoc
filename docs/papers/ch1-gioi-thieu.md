# CHƯƠNG 1. GIỚI THIỆU

## 1.1. Đặt vấn đề

### 1.1.1. Bối cảnh giao thông Việt Nam và nhu cầu tự động hoá

Tính đến tháng 9/2024, Việt Nam có khoảng **77 triệu xe máy đã đăng ký, tương đương 770 xe trên 1.000 dân**; xe máy chiếm khoảng **85–90% lưu lượng phương tiện trên đường**. Điều này kéo theo ba hệ quả (Chương 4): (i) biển hai dòng chiếm đa số vì mọi xe mô tô đều mang biển hai dòng; (ii) mật độ cao gây che khuất và nhiều biển trong một khung hình; (iii) biển xe mô tô chỉ 140 × 190 mm nên là đối tượng nhỏ. Vì vậy, ghi nhận thủ công không phù hợp và cần **nhận dạng biển số xe tự động (ALPR)** [1]<!-- du_2013_review -->.

### 1.1.2. Ứng dụng thực tế của hệ thống ALPR

ALPR là lõi của bốn nhóm ứng dụng tại Việt Nam: **bãi đỗ xe thông minh**; **thu phí không dừng ETC**; **giám sát giao thông** (xử phạt nguội); **kiểm soát ra vào**. Cả bốn đo cùng một thứ: **không phải mAP của khâu phát hiện, mà là tỉ lệ đọc đúng toàn bộ chuỗi biển số** (plate-level exact match) — đọc đúng 9 trên 10 ký tự vẫn là đọc sai biển. Nhận định này định hình chỉ tiêu ở mục 1.2.2 và cách đánh giá ở Chương 5.

### 1.1.3. Vì sao không thể dùng trực tiếp giải pháp nước ngoài

**(a) Biển hai dòng là điểm suy giảm đã đo được, không phải rủi ro giả định.** Trên tập kiểm thử cân bằng có chủ ý của bộ **RodoSol-ALPR (Brazil)** — 4.000 ảnh ô tô biển **một dòng**, 4.000 ảnh xe máy biển **hai dòng** — hệ thống thương mại **OpenALPR** nhận đúng **94,3% biển một dòng nhưng chỉ 45,7% biển hai dòng, chênh 48,6 điểm phần trăm**, không biến số nào khác thay đổi ngoài bố cục biển [2]<!-- laroca_2022_crossdataset -->. Cũng nghiên cứu này: cả 12 phương pháp và 2 hệ thống thương mại đều **không vượt quá 70%** recognition rate, và có công trình phải **loại bỏ hoàn toàn xe máy** khỏi thí nghiệm [2]<!-- laroca_2022_crossdataset -->.

> **Ghi chú về phạm vi áp dụng của số liệu.** Cặp **94,3% / 45,7%** (chênh **48,6 điểm phần trăm**) đo trên **RodoSol-ALPR của Brazil**, **không phải trên dữ liệu Việt Nam**; dẫn như một ***analogue*** định lượng về độ khó của biển hai dòng, chọn Brazil vì cũng là nước có tỉ lệ xe máy cao. **Tuyệt đối không được trình bày cặp số này như số liệu Việt Nam** — số liệu Việt Nam do chính nhóm thực hiện đo nằm ở **Chương 5**.

**(b) Căn cứ pháp lý và cấu trúc chuỗi ký tự là đặc thù quốc gia.** Biển số xe Việt Nam theo **TT 79/2024/TT-BCA** (hiệu lực 01/01/2025) [3]<!-- bocongan_2024_tt79 -->, sửa đổi bởi **TT 13/2025/TT-BCA** [4]<!-- bocongan_2025_tt13 --> và **TT 51/2025/TT-BCA** [5]<!-- bocongan_2025_tt51 -->; kích thước vật lý theo **QCVN 08:2024/BCA** [6]<!-- bocongan_2024_qcvn08 -->. **Đính chính:** nhiều tài liệu trong nước vẫn viện dẫn **TT 24/2023/TT-BCA** — **đã hết hiệu lực từ 01/01/2025**. Ba đặc thù sau **không học được từ dữ liệu nước ngoài**. **(i) Tập ký tự seri phụ thuộc vị trí:** seri **vị trí thứ nhất** thuộc tập **20 chữ cái** (có `G`, không có `R`) [7]<!-- bocongan_2024_nhandienbienso -->; **vị trí thứ hai** của biển xe mô tô thuộc tập **20 chữ cái khác** (có `R`, không có `G`); tập loại trừ toàn hệ thống chỉ gồm **5 chữ `I`, `J`, `O`, `Q`, `W`**; nếu áp dụng danh sách phẳng 20 chữ cái chung, hệ thống sẽ **nhận dạng sai toàn bộ lớp biển xe máy có `R` ở vị trí thứ hai**, đây là lỗi không thể khắc phục trong bước hậu xử lý. **(ii) Mã địa phương hữu hạn, có lỗ hổng:** dải 11–99 chỉ có **81 mã đang được sử dụng**; **8 mã — 13, 42, 44, 45, 46, 87, 91, 96 — không được gán**, nên `\d{2}` cho qua 8 chuỗi không bao giờ tồn tại. **(iii) Tỉ lệ khung hình phân tách rõ hai bố cục** [6]<!-- bocongan_2024_qcvn08 -->: 110 × 520 mm → **4,727** (1 dòng); 165 × 330 mm → **2,000** (2 dòng); 140 × 190 mm → **1,357** (2 dòng); không loại biển nào rơi vào khoảng mở **(2,000 ; 4,727)** — cơ sở hình học để phân loại số dòng.

**(c) Điều kiện thu nhận ảnh khác biệt:** biển bị che, bám bụi, cong vênh, chụp nghiêng, ngược sáng, ảnh đêm — khác các bộ dữ liệu quốc tế lớn (CCPD, AOLP, SSIG) vốn lấy ô tô làm trung tâm. **Kết luận mục 1.1:** bài toán này cần **hệ thống huấn luyện trên dữ liệu Việt Nam và khối hậu xử lý xây theo quy chuẩn Việt Nam.**

## 1.2. Mục tiêu đề tài

### 1.2.1. Mục tiêu tổng quát

Xây dựng hệ thống nhận dạng biển số xe Việt Nam gồm mô hình phát hiện tự huấn luyện, nhận dạng ký tự, hậu xử lý theo quy chuẩn Việt Nam, REST API, giao diện web, cơ sở dữ liệu và đóng gói triển khai; hỗ trợ biển một dòng, hai dòng và suy luận trên CPU. Hệ thống phục vụ mục đích học thuật, không phải sản phẩm thương mại.

### 1.2.2. Mục tiêu cụ thể

Mỗi chỉ tiêu có **mục tiêu** và **ngưỡng tối thiểu** (bắt buộc đạt). Về chức năng và chất lượng phần mềm: **34 yêu cầu chức năng** (20 *Must*, 5 *Should*, 3 *Could*, 6 *Won't*) trong **sáu nhóm** (mục 4.1.3); **NFR-M1** mã đường ống AI **không import FastAPI**; **NFR-M5** thay được bộ OCR không sửa mã tầng API; **NFR-M2** độ bao phủ kiểm thử tầng nghiệp vụ **≥ 70%**; **khởi động một lệnh** `docker compose up`, demo **không cần Internet**. **NFR-A5 và NFR-A6 đo tách bạch có chủ đích** — hiệu số là **đóng góp định lượng của khối hậu xử lý** (mục 1.5); thêm **NFR-A8** (tách riêng biển một dòng / hai dòng) và **NFR-A9** (theo điều kiện ảnh, nếu có nhãn phù hợp).

**Bảng 1.1.** Nhóm chỉ tiêu độ chính xác

| Mã | Chỉ tiêu | Mục tiêu | Ngưỡng tối thiểu |
|---|---|:--:|:--:|
| NFR-A1 | mAP@0.5 của bộ phát hiện biển số | ≥ 0,90 | ≥ 0,85 |
| NFR-A2 | mAP@0.5:0.95 của bộ phát hiện | ≥ 0,65 | ≥ 0,55 |
| NFR-A3 | Precision / Recall phát hiện | ≥ 0,92 / ≥ 0,90 | ≥ 0,88 / ≥ 0,85 |
| NFR-A4 | Độ chính xác OCR mức ký tự (1 − CER) | ≥ 0,95 | ≥ 0,92 |
| NFR-A5 | Độ chính xác biển đầy đủ **trước** hậu xử lý | ≥ 0,85 | ≥ 0,80 |
| NFR-A6 | Độ chính xác biển đầy đủ **sau** hậu xử lý | ≥ 0,90 | ≥ 0,85 |
| **NFR-A7** | **Độ chính xác E2E toàn trình (ảnh vào → biển đúng)** | **≥ 0,88** | **≥ 0,82** |

**Bảng 1.2.** Nhóm chỉ tiêu hiệu năng trên CPU

| Mã | Chỉ tiêu | Mục tiêu | Ngưỡng tối thiểu |
|---|---|:--:|:--:|
| **NFR-P1** | **Độ trễ E2E một ảnh (p95)** | **≤ 800 ms** | **≤ 1500 ms** |
| NFR-P2 | Tốc độ khung hình thời gian thực (webcam — đo ở tầng API) | ≥ 5 FPS hiệu dụng | ≥ 3 FPS |
| NFR-P3 | Tốc độ xử lý video | ≥ 0,3× thời gian thực | ≥ 0,15× |
| NFR-P4 | Thời gian nạp mô hình khi khởi động | ≤ 15 s | ≤ 30 s |
| NFR-P5 | Overhead của tầng API (không tính suy luận) | ≤ 50 ms | ≤ 100 ms |
| NFR-P6 | Thời gian truy vấn lịch sử (10.000 bản ghi) | ≤ 500 ms | ≤ 1000 ms |
| NFR-P7 | Bộ nhớ thường trú của máy chủ | ≤ 2 GB | ≤ 4 GB |

Các chỉ tiêu độ trễ "rộng rãi" hơn bài báo ALPR vì máy phát triển **không có GPU CUDA** (CON-02): huấn luyện trên GPU Colab/Kaggle, **toàn bộ suy luận và demo chạy trên CPU**, còn bài báo thường đo trên GPU RTX/V100. Mọi số liệu hiệu năng **bắt buộc kèm cấu hình phần cứng**.

> **Ghi chú về sáu yêu cầu mức *Won't*.** Bốn yêu cầu đầu đều **thuần giao diện**, chuyển mức trong hai đợt thu gọn giao diện web: đợt 1 gỡ trang Webcam → **FR-3.1 và FR-3.4 chuyển M → W** (năng lực nhận dạng thời gian thực vẫn phục vụ ở tầng giao diện lập trình và vẫn có kiểm thử); đợt 2 gỡ trang Tổng quan (Dashboard) → **FR-4.1 chuyển M → W**, **FR-4.2 chuyển S → W** (thống kê và chuỗi thời gian vẫn truy vấn được và vẫn có kiểm thử tích hợp). Đợt thứ ba đưa nốt **FR-2.5** (xuất video đã chú thích, *Must* → *Won't*) và **FR-2.6** (huỷ tác vụ đang chạy, *Should* → *Won't*) ra khỏi phạm vi: cả hai đang dở dang, và việc bàn giao một tính năng chưa hoàn thiện có thể ảnh hưởng đến tính ổn định chung. **Tổng cộng bốn yêu cầu mức *Must* đã chuyển sang *Won't*: FR-3.1, FR-3.4, FR-4.1 và FR-2.5**, được nêu rõ tại đây cũng như ở mục 4.1.3, mục 6.2 và trong đặc tả yêu cầu. Cần phân biệt hai loại mất mát khác hẳn nhau bên trong con số bốn ấy: **ba yêu cầu FR-3.1, FR-3.4 và FR-4.1 chỉ mất *màn hình hiển thị*** — năng lực tương ứng vẫn phục vụ ở tầng giao diện lập trình và vẫn có kiểm thử tự động; **riêng FR-2.5 mất chính *năng lực*** vì hệ thống không còn xuất được video đã chú thích. Đây là **quyết định phạm vi có chủ đích**, không phải hạng mục bỏ sót, và toàn bộ mã liên quan còn nguyên trong lịch sử kho mã. Đợt thu gọn thứ hai đồng thời loại bỏ thư viện biểu đồ đi kèm, làm giảm hơn một nửa dung lượng gói tải về của giao diện.

### 1.2.3. Tiêu chí thành công

Đề tài thành công khi **đồng thời**: (1) toàn bộ yêu cầu *Must* hoạt động và demo được — theo bộ 20 *Must* **sau** ba đợt thu gọn phạm vi, sáu yêu cầu đã chuyển *Won't* (FR-2.5, FR-2.6, FR-3.1, FR-3.4, FR-4.1, FR-4.2) **không** tính là đạt; (2) mọi chỉ tiêu đạt **ngưỡng tối thiểu** và **có bằng chứng đo đạc**; (3) đủ 12 sản phẩm bàn giao; (4) khởi động trên máy sạch bằng một lệnh `docker compose up`; (5) demo trực tiếp không cần Internet.

> **Trạng thái tại thời điểm viết chương này.** Các chỉ tiêu ở mục 1.2.2 là **chỉ tiêu đặt ra**. Hệ thống chạy đường ống nhận dạng **thật** với `models/best.pt` (`imgsz=640`, phép chia tập v3); các chỉ tiêu phát hiện đều đạt (mAP@0.5 = 0,9829). Với cấu hình giao hàng, NFR-P1 đạt **ngưỡng tối thiểu** nhưng chưa đạt mục tiêu (p95 = 1.143,10 ms; ngưỡng 1.500 ms, mục tiêu 800 ms). Cặp 731/780 ms là kết quả đo trước khi bật bậc thử lại và chỉ được dùng để phân tích đánh đổi. Chỉ tiêu độ chính xác OCR đã đo; kết quả đối với biển hai dòng chưa đạt. **Đối chiếu đầy đủ từng chỉ tiêu ở Chương 5.**

## 1.3. Đối tượng và phạm vi nghiên cứu

### 1.3.1. Đối tượng nghiên cứu

Ba nhóm. **(1) Biển số xe cơ giới Việt Nam** theo TT 79/2024/TT-BCA [3]<!-- bocongan_2024_tt79 --> (sửa đổi bởi TT 13/2025 [4]<!-- bocongan_2025_tt13 --> và TT 51/2025 [5]<!-- bocongan_2025_tt51 -->) và QCVN 08:2024/BCA [6]<!-- bocongan_2024_qcvn08 -->; biển nền đỏ quân đội thuộc TT 169/2021/TT-BQP [8]<!-- boquocphong_2021_tt169 -->, chỉ xử lý ở mức nhận biết ký hiệu. **(2) Mô hình phát hiện họ YOLO** — cụ thể YOLO11 [9]<!-- jocher_2024_yolo11 -->. **(3) Bộ nhận dạng ký tự** không cần phân đoạn ký tự: PaddleOCR [10]<!-- cui_2026_ppocrv5 --> là **phương án khởi điểm**, EasyOCR ngang hàng, Tesseract là mốc dưới, kèm bộ luật hậu xử lý theo vị trí. **Lựa chọn bộ nhận dạng ký tự chưa chốt ở giai đoạn thiết kế** — quyết định thuộc về benchmark do chính nhóm thực hiện chạy (**mục 3.3**, **Chương 5**).

### 1.3.2. Phạm vi trong nghiên cứu

Bốn nhóm. **(a) Trí tuệ nhân tạo:** huấn luyện YOLO11 trên dữ liệu Việt Nam, so sánh biến thể n / s / m, kèm YOLO26n đối chứng (mục 3.2); **benchmark các bộ nhận dạng ký tự** trên chính tập kiểm thử biển số Việt Nam rồi tích hợp bộ nhận dạng được chọn; hậu xử lý theo luật hợp lệ theo vị trí; **hỗ trợ cả biển một dòng và hai dòng**; đánh giá đầy đủ (mAP, precision, recall, F1, ma trận nhầm lẫn); đo hiệu năng trên CPU. **(b) Dữ liệu:** thu thập, gộp, làm sạch bộ công khai; sửa nhãn; loại ảnh trùng lặp; tăng cường; chia train / val / test **có kiểm soát rò rỉ dữ liệu**; thống kê. **(c) Phần mềm:** FastAPI + Swagger; nhận dạng ảnh, video và khung hình thời gian thực qua `POST /api/detect/frame`; lịch sử bằng SQLite + SQLAlchemy + Alembic; giao diện React + Vite + TypeScript + TailwindCSS **ba trang** (Nhận dạng ảnh — trang chủ, Nhận dạng video, Lịch sử) sau hai đợt thu gọn; tìm kiếm, lọc, tải về; thống kê ở tầng API (`GET /api/statistics`); Docker và Docker Compose. **(d) Kiểm thử, tài liệu:** unit test, integration test, kiểm thử độ chính xác AI, hiệu năng, chịu tải; tài liệu học thuật và kỹ thuật.

### 1.3.3. Phạm vi ngoài nghiên cứu

Danh sách này nhằm xác định rõ giới hạn của đề tài; việc loại trừ các hạng mục này là quyết định có chủ đích, không phải do giới hạn về thời gian. **Mười một hạng mục bao gồm:** (1) **xác thực, phân quyền** — chạy nội bộ `localhost`/LAN (giả định A-04); (2) **đa camera / đa luồng**; (3) **bám vết qua khung hình (SORT / DeepSORT)** — thay bằng **gộp trùng theo chuỗi ký tự**; (4) **phân loại loại xe** — từ 01/01/2025 TT 79/2024 **đã bỏ** quy tắc suy loại xe từ chữ cái seri; (5) **ước lượng tốc độ, phát hiện vi phạm** — cần hiệu chuẩn camera riêng; (6) **biển số nước ngoài**; (7) **barie / cổng tự động** — cần thiết bị vật lý; (8) **cloud, multi-tenant, CI/CD production** — **Docker Compose đã đủ**; (9) **ứng dụng di động** — web responsive đã đáp ứng; (10) **huấn luyện bộ nhận dạng ký tự từ đầu** — dùng pre-trained rồi **tinh chỉnh**; tinh chỉnh nằm **trong** phạm vi (mục 2.4.3(f)); (11) **suy luận thời gian thực trên GPU** — máy phát triển **không có GPU CUDA** (CON-02) ⇒ mọi số liệu là **số liệu CPU**.

### 1.3.4. Ranh giới hệ thống

![](figures/fig-ch1-01.png)

**Hình 1.1.** Ranh giới hệ thống — phần bên trong là hệ thống bàn giao, Colab/Kaggle nằm ngoài

Colab/Kaggle nằm **ngoài** ranh giới khi vận hành — chỉ là công cụ ngoại tuyến sản xuất best.pt; hệ thống khi chạy **không phụ thuộc dịch vụ ngoài nào** (mục 1.2.3). Sau khi trang webcam bị gỡ, client gửi khung hình trực tiếp qua `POST /api/detect/frame`.

## 1.4. Phương pháp nghiên cứu

Đề tài dùng **ba phương pháp bổ trợ nhau**: nghiên cứu lý thuyết (khảo sát tài liệu có trích dẫn, đối chiếu văn bản pháp quy hiện hành); nghiên cứu thực nghiệm (**mọi khẳng định về hiệu năng và độ chính xác đều phải có số đo tái lập được**, kèm cấu hình phần cứng và cỡ mẫu); và quy trình phát triển theo giai đoạn, mỗi giai đoạn khép lại bằng một bộ tài liệu và một mốc kiểm chứng.

### 1.4.1. Phân định phần tự xây dựng và phần dùng lại

Để tránh mọi nhập nhằng khi đánh giá, bảng dưới nêu rõ với từng thành phần: nguồn gốc của nó và **phần việc nhóm thực hiện đã làm**.

**Bảng 1.3.** Phân định công việc theo từng thành phần

| Thành phần | Nguồn gốc | Nhóm thực hiện đã làm gì |
|---|---|---|
| Bộ phát hiện biển số | Kiến trúc YOLO11n có sẵn, trọng số khởi đầu từ COCO | **Tự huấn luyện** trên dữ liệu Việt Nam do nhóm hợp nhất; chọn siêu tham số; đánh giá |
| Bộ nhận dạng ký tự | Mô hình PP-OCRv5 mobile tiền huấn luyện | Tích hợp; **tự đo** so với hai bộ nhận dạng khác; thử tinh chỉnh và **báo cáo cả kết quả âm** |
| **Khối xử lý ảnh vùng biển** | — | **Tự thiết kế và cài đặt toàn bộ**: nắn hình, phân loại bố cục, tách hai nửa, ghép ngang |
| **Khối hậu xử lý theo quy chuẩn** | — | **Tự thiết kế và cài đặt toàn bộ**: mặt nạ vị trí, tập mã tỉnh, bảng ánh xạ nhầm lẫn |
| Bộ dữ liệu | 7 bộ ảnh công khai, giấy phép ở Phụ lục C | **Tự hợp nhất, khử trùng lặp chéo bộ, chia tập có kiểm soát rò rỉ**; gán nhãn chuỗi cho tập con |
| Máy chủ, giao diện, đóng gói | Thư viện mã nguồn mở (FastAPI, React, Docker) | **Tự thiết kế kiến trúc và cài đặt**; viết bộ kiểm thử |
| Quy trình đo và báo cáo | — | **Tự xây dựng toàn bộ**: công cụ đo, giao thức, phân tích lỗi |

Hai khối in đậm ở giữa bảng là phần **không có sẵn trong bất kỳ thư viện nào** và là đóng góp kỹ thuật chính của đề tài.

## 1.5. Đóng góp của đề tài

### 1.5.1. Tuyên bố trung thực về mức đóng góp

> **Đề tài này không tạo ra kết quả state-of-the-art.**

Các kết quả trên 99% trong tài liệu ALPR quốc tế thường dựa trên hạ tầng GPU và dữ liệu riêng. Nhóm thực hiện làm việc trên máy không có GPU CUDA nên không đặt mục tiêu tương tự. Đóng góp tập trung ở sáu nội dung có thể kiểm chứng.

**Sáu đóng góp.**

**(a) Hệ thống hoàn chỉnh, có kiến trúc phần mềm** — không phải tập script rời rạc: đường ống AI tách hoàn toàn khỏi tầng API (NFR-M1), interface trừu tượng cho phép thay bộ nhận dạng ký tự mà không sửa tầng API (NFR-M5), REST API có tài liệu tự sinh, giao diện web ba màn hình, cơ sở dữ liệu có migration, Docker một lệnh. Trạng thái đã đo: bao phủ kiểm thử tầng nghiệp vụ **87,7%**, **1.002 test thu thập / 1.002 đạt / 0 thất bại**. Khảo sát cho thấy mã nguồn mở ALPR Việt Nam chủ yếu là script rời rạc **không công bố số liệu độ chính xác** — đây là **khoảng trống kỹ nghệ**, không phải khoảng trống thuật toán, nhưng vẫn có thật.

**(b) Bộ luật hậu xử lý ràng buộc theo VỊ TRÍ** cho biển số Việt Nam, khai thác ba ràng buộc đặc thù: tập hợp lệ **khác nhau theo từng vị trí** — mã địa phương thuộc **81 giá trị** chứ không phải `\d{2}`, seri **thứ nhất** thuộc 20 chữ cái có `G` không có `R` [7]<!-- bocongan_2024_nhandienbienso -->, seri **thứ hai** của biển xe mô tô thuộc **20 chữ cái KHÁC** có `R` không có `G`; cấu trúc chuỗi và độ dài theo quy chuẩn; và bảng ánh xạ nhầm lẫn ký tự **không đối xứng**.

> **Ghi chú về mức độ của đóng góp này.** Luận điểm dự kiến ban đầu — *"khai thác bộ 20 chữ cái, loại trừ 6 chữ `I J O Q R W`"* — **sai và đã bị bác bỏ**: tập loại trừ toàn hệ thống chỉ có **5 chữ**, còn `R` **hợp lệ** ở vị trí seri thứ hai của biển xe mô tô. Sửa lại **làm yếu đi** phần đóng góp nếu tính theo "số ký tự loại trừ được". Đổi lại, phần có giá trị nằm ở ràng buộc **phụ thuộc vị trí**: một hệ thống dùng danh sách phẳng 20 chữ cái sẽ sai hệ thống trên mọi biển xe máy có `R`.

**(c) Đo được ĐỊNH LƯỢNG đóng góp của bước hậu xử lý.** Phần lớn công trình mô tả bước này ở mức định tính, không trả lời được *nó đóng góp bao nhiêu*. Đề tài giải quyết ở tầng dữ liệu — **lưu đồng thời chuỗi OCR thô và chuỗi đã sửa** — nên hiệu số giữa **NFR-A5** (trước) và **NFR-A6** (sau) là một **con số đo được**.

**(d) Đánh giá tách riêng biển một dòng và biển hai dòng.** **NFR-A8** biến phép tách này thành **nghĩa vụ báo cáo bắt buộc** chứ không phải phân tích tuỳ chọn, kèm **NFR-A9** — báo cáo theo điều kiện ảnh, nếu bộ dữ liệu có nhãn phù hợp.

**(e) Công bố hiệu năng kèm cấu hình phần cứng CPU cụ thể** — mọi số liệu kèm model CPU, số luồng, kích thước ảnh đầu vào, nền tảng suy luận và cỡ mẫu đo. FPS không kèm phần cứng thì không tái lập được, cũng không so sánh được.

**(f) Đo trên chính ảnh biển số Việt Nam.** Khảo sát xác định **không tồn tại benchmark công khai nào so sánh các bộ nhận dạng ký tự trên riêng ảnh biển số xe máy Việt Nam hai dòng**, và hai số liệu thường được viện dẫn để chứng minh ưu thế của một bộ nhận dạng đã **bị bác bỏ khi truy ngược về nguồn gốc** (mục 3.3). Đề tài đã chạy ba phép so sánh trên chính ảnh biển số Việt Nam, cùng máy và cùng ngữ liệu: **PP-OCRv5_mobile ↔ PP-OCRv6_medium** (mục 3.3.2), **bộ nhận dạng gốc ↔ bản tinh chỉnh** (mục 4.5.3), và **PaddleOCR ↔ EasyOCR ↔ Tesseract trên toàn bộ 2.801 biển** (mục 3.3.3) — kết quả PaddleOCR **68,87%**, hơn EasyOCR 54,59 điểm và hơn Tesseract 58,59 điểm, **bác bỏ** tài liệu công khai vốn nghiêng về EasyOCR. Một kết quả **khác với dự đoán ban đầu**: kỹ thuật tách và ghép ngang giúp độ chính xác của PaddleOCR tăng **34,92%** nhưng chỉ cải thiện **0,03%** đối với Tesseract, nên đây **không** phải kỹ thuật độc lập bộ nhận dạng như giả định ban đầu.

### 1.5.2. Những gì đề tài KHÔNG tuyên bố

Bốn điều loại trừ. **Không** tuyên bố vượt các con số độ chính xác cao nhất trong nước — chúng đo trên tập dữ liệu riêng không công khai, **không có cơ sở so sánh công bằng**. **Không** đề xuất kiến trúc mạng nơ-ron mới; đề tài **tích hợp và tinh chỉnh**. **Không** giải quyết các thách thức mở — độ phân giải rất thấp, tổng quát hoá xuyên tập dữ liệu, che khuất nặng (**Hướng phát triển, Chương 6**). Mọi số liệu hiệu năng là **số liệu CPU**, **không so sánh trực tiếp được** với FPS đo trên GPU.
