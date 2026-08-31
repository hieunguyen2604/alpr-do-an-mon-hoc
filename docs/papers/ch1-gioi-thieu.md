# CHƯƠNG 1. GIỚI THIỆU

## 1.1. Đặt vấn đề

### 1.1.1. Bối cảnh giao thông Việt Nam và nhu cầu tự động hoá

Tính đến tháng 9/2024, Việt Nam có khoảng **77 triệu xe máy đã đăng ký, tương đương 770 xe trên 1.000 dân**; xe máy chiếm khoảng **85–90% lưu lượng phương tiện trên đường**. Điều này kéo theo ba hệ quả (Chương 4): (i) biển hai dòng chiếm đa số vì mọi xe mô tô đều mang biển hai dòng; (ii) mật độ cao gây che khuất và nhiều biển trong một khung hình; (iii) biển xe mô tô chỉ 140 × 190 mm nên là đối tượng nhỏ. Vì vậy, ghi nhận thủ công không phù hợp và cần **nhận dạng biển số xe tự động (ALPR)** [1]<!-- du_2013_review -->.

### 1.1.2. Ứng dụng thực tế của hệ thống ALPR

ALPR là lõi của bốn nhóm ứng dụng tại Việt Nam: **bãi đỗ xe thông minh**; **thu phí không dừng ETC**; **giám sát giao thông** (xử phạt nguội); **kiểm soát ra vào**. Cả bốn đo cùng một thứ: **không phải mAP của khâu phát hiện, mà là tỉ lệ đọc đúng toàn bộ chuỗi biển số** (plate-level exact match) — đọc đúng 9 trên 10 ký tự vẫn là đọc sai biển. Nhận định này định hình chỉ tiêu ở mục 1.2.2 và cách đánh giá ở Chương 5.

### 1.1.3. Vì sao không thể dùng trực tiếp giải pháp nước ngoài

**(a) Biển hai dòng là điểm suy giảm đã đo được, không phải rủi ro giả định.** Trên tập kiểm thử cân bằng có chủ ý của bộ **RodoSol-ALPR (Brazil)** — 4.000 ảnh ô tô biển **một dòng**, 4.000 ảnh xe máy biển **hai dòng** — hệ thống thương mại **OpenALPR** nhận đúng **94,3% biển một dòng nhưng chỉ 45,7% biển hai dòng, chênh 48,6 điểm phần trăm**, không biến số nào khác thay đổi ngoài bố cục biển [2]<!-- laroca_2022_crossdataset -->. **Cặp số này đo trên dữ liệu Brazil, dẫn ra như một *analogue* định lượng về độ khó của biển hai dòng; số liệu Việt Nam do nhóm tự đo nằm ở Chương 5.** Cũng nghiên cứu này: cả 12 phương pháp và 2 hệ thống thương mại đều **không vượt quá 70%** recognition rate, và có công trình phải **loại bỏ hoàn toàn xe máy** khỏi thí nghiệm [2]<!-- laroca_2022_crossdataset -->.

Hai đặc thù nữa **không học được từ dữ liệu nước ngoài**: tập ký tự sê-ri của biển Việt Nam **phụ thuộc vị trí trong chuỗi** — vị trí thứ nhất thuộc một tập 20 chữ cái có `G` không có `R`, vị trí thứ hai của biển mô tô thuộc một tập 20 chữ **khác** có `R` không có `G` [7]<!-- bocongan_2024_nhandienbienso -->; và mã địa phương chỉ có **81 giá trị** hợp lệ trong dải 11–99. Căn cứ pháp lý là **TT 79/2024/TT-BCA** [3]<!-- bocongan_2024_tt79 --> cùng hai thông tư sửa đổi [4]<!-- bocongan_2025_tt13 --> [5]<!-- bocongan_2025_tt51 --> và **QCVN 08:2024/BCA** [6]<!-- bocongan_2024_qcvn08 -->; chi tiết ở mục 2.2.

**Kết luận mục 1.1:** bài toán cần **hệ thống huấn luyện trên dữ liệu Việt Nam và khối hậu xử lý xây theo quy chuẩn Việt Nam.**

## 1.2. Mục tiêu đề tài

### 1.2.1. Mục tiêu tổng quát

Xây dựng hệ thống nhận dạng biển số xe Việt Nam gồm mô hình phát hiện tự huấn luyện, nhận dạng ký tự, hậu xử lý theo quy chuẩn Việt Nam, REST API, giao diện web, cơ sở dữ liệu và đóng gói triển khai; hỗ trợ biển một dòng, hai dòng và suy luận trên CPU. Hệ thống phục vụ mục đích học thuật, không phải sản phẩm thương mại.

### 1.2.2. Mục tiêu cụ thể

Mỗi chỉ tiêu có **mục tiêu** và **ngưỡng tối thiểu** (bắt buộc đạt). Về chức năng và chất lượng phần mềm: **34 yêu cầu chức năng** (22 *Must*, 5 *Should*, 3 *Could*, 4 *Won't*) trong **sáu nhóm** (mục 4.1.3); **NFR-M1** mã đường ống AI **không import FastAPI**; **NFR-M5** thay được bộ OCR không sửa mã tầng API; **NFR-M2** độ bao phủ kiểm thử tầng nghiệp vụ **≥ 70%**; **khởi động một lệnh** `docker compose up`, demo **không cần Internet**. **NFR-A5 và NFR-A6 đo tách bạch có chủ đích** — hiệu số là **đóng góp định lượng của khối hậu xử lý** (mục 1.5); thêm **NFR-A8** (tách riêng biển một dòng / hai dòng) và **NFR-A9** (theo điều kiện ảnh, nếu có nhãn phù hợp) (Bảng 1.1).

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

Nhóm chỉ tiêu thứ hai đặt cho hiệu năng khi chạy trên CPU (Bảng 1.2).

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

Bốn yêu cầu ở mức *Won't* nằm ngoài phạm vi bản giao hàng; trong đó **FR-2.5** (xuất video đã chú thích) là yêu cầu duy nhất làm hệ thống **mất một năng lực**, các yêu cầu còn lại chỉ mất màn hình hiển thị. Chi tiết ở mục 4.1.3 và 6.2.

### 1.2.3. Tiêu chí thành công

Đề tài thành công khi **đồng thời**: (1) toàn bộ yêu cầu *Must* hoạt động và demo được — theo bộ 20 *Must* **sau** ba đợt thu gọn phạm vi, sáu yêu cầu đã chuyển *Won't* (FR-2.5, FR-2.6, FR-3.1, FR-3.4, FR-4.1, FR-4.2) **không** tính là đạt; (2) mọi chỉ tiêu đạt **ngưỡng tối thiểu** và **có bằng chứng đo đạc**; (3) đủ 12 sản phẩm bàn giao; (4) khởi động trên máy sạch bằng một lệnh `docker compose up`; (5) demo trực tiếp không cần Internet.

> **Trạng thái tại thời điểm viết chương này.** Các chỉ tiêu ở mục 1.2.2 là **chỉ tiêu đặt ra**; đối chiếu đầy đủ từng chỉ tiêu ở Chương 5. Hệ thống chạy đường ống thật với `models/best.pt`: nhóm phát hiện đạt cả bốn chỉ tiêu (mAP@0.5 = 0,9829), NFR-P1 đạt mục tiêu (p95 = 509,76 ms so với 800 ms), còn **độ chính xác đọc chuỗi trên biển hai dòng chưa đạt**.

## 1.3. Đối tượng và phạm vi nghiên cứu

### 1.3.1. Đối tượng nghiên cứu

Ba nhóm. **(1) Biển số xe cơ giới Việt Nam** theo TT 79/2024/TT-BCA [3]<!-- bocongan_2024_tt79 --> (sửa đổi bởi TT 13/2025 [4]<!-- bocongan_2025_tt13 --> và TT 51/2025 [5]<!-- bocongan_2025_tt51 -->) và QCVN 08:2024/BCA [6]<!-- bocongan_2024_qcvn08 -->; biển nền đỏ quân đội thuộc TT 169/2021/TT-BQP [8]<!-- boquocphong_2021_tt169 -->, chỉ xử lý ở mức nhận biết ký hiệu. **(2) Mô hình phát hiện họ YOLO** — cụ thể YOLO11 [9]<!-- jocher_2024_yolo11 -->. **(3) Bộ nhận dạng ký tự** không cần phân đoạn ký tự: PaddleOCR [10]<!-- cui_2026_ppocrv5 --> là **phương án khởi điểm**, EasyOCR ngang hàng, Tesseract là mốc dưới, kèm bộ luật hậu xử lý theo vị trí. **Lựa chọn bộ nhận dạng ký tự chưa chốt ở giai đoạn thiết kế** — quyết định thuộc về benchmark do chính nhóm thực hiện chạy (**mục 3.3**, **Chương 5**).

### 1.3.2. Phạm vi trong nghiên cứu

Bốn nhóm. **(a) Trí tuệ nhân tạo:** huấn luyện YOLO11 trên dữ liệu Việt Nam, so sánh biến thể n / s / m, kèm YOLO26n đối chứng (mục 3.2); **benchmark các bộ nhận dạng ký tự** trên chính tập kiểm thử biển số Việt Nam rồi tích hợp bộ nhận dạng được chọn; hậu xử lý theo luật hợp lệ theo vị trí; **hỗ trợ cả biển một dòng và hai dòng**; đánh giá đầy đủ (mAP, precision, recall, F1, ma trận nhầm lẫn); đo hiệu năng trên CPU. **(b) Dữ liệu:** thu thập, gộp, làm sạch bộ công khai; sửa nhãn; loại ảnh trùng lặp; tăng cường; chia train / val / test **có kiểm soát rò rỉ dữ liệu**; thống kê. **(c) Phần mềm:** FastAPI + Swagger; nhận dạng ảnh, video và khung hình thời gian thực qua `POST /api/detect/frame`; lịch sử bằng SQLite + SQLAlchemy + Alembic; giao diện React + Vite + TypeScript + TailwindCSS **ba trang** (Nhận dạng ảnh — trang chủ, Nhận dạng video, Lịch sử) sau hai đợt thu gọn; tìm kiếm, lọc, tải về; thống kê ở tầng API (`GET /api/statistics`); Docker và Docker Compose. **(d) Kiểm thử, tài liệu:** unit test, integration test, kiểm thử độ chính xác AI, hiệu năng, chịu tải; tài liệu học thuật và kỹ thuật.

### 1.3.3. Phạm vi ngoài nghiên cứu

Danh sách này nhằm xác định rõ giới hạn của đề tài; việc loại trừ các hạng mục này là quyết định có chủ đích, không phải do giới hạn về thời gian. **Mười một hạng mục bao gồm:** (1) **xác thực, phân quyền** — chạy nội bộ `localhost`/LAN (giả định A-04); (2) **đa camera / đa luồng**; (3) **bám vết qua khung hình (SORT / DeepSORT)** — thay bằng **gộp trùng theo chuỗi ký tự**; (4) **phân loại loại xe** — từ 01/01/2025 TT 79/2024 **đã bỏ** quy tắc suy loại xe từ chữ cái seri; (5) **ước lượng tốc độ, phát hiện vi phạm** — cần hiệu chuẩn camera riêng; (6) **biển số nước ngoài**; (7) **barie / cổng tự động** — cần thiết bị vật lý; (8) **cloud, multi-tenant, CI/CD production** — **Docker Compose đã đủ**; (9) **ứng dụng di động** — web responsive đã đáp ứng; (10) **huấn luyện bộ nhận dạng ký tự từ đầu** — dùng pre-trained rồi **tinh chỉnh**; tinh chỉnh nằm **trong** phạm vi (mục 2.4.3(f)); (11) **suy luận thời gian thực trên GPU** — máy phát triển **không có GPU CUDA** (CON-02) ⇒ mọi số liệu là **số liệu CPU** (Hình 1.1).

### 1.3.4. Ranh giới hệ thống

![](figures/fig-ch1-01.png)

**Hình 1.1.** Ranh giới hệ thống — phần bên trong là hệ thống bàn giao, Colab/Kaggle nằm ngoài

Colab/Kaggle nằm **ngoài** ranh giới khi vận hành — chỉ là công cụ ngoại tuyến sản xuất best.pt; hệ thống khi chạy **không phụ thuộc dịch vụ ngoài nào** (mục 1.2.3). Sau khi trang webcam bị gỡ, client gửi khung hình trực tiếp qua `POST /api/detect/frame`.

## 1.4. Phương pháp nghiên cứu

Đề tài dùng **ba phương pháp bổ trợ nhau**: nghiên cứu lý thuyết (khảo sát tài liệu có trích dẫn, đối chiếu văn bản pháp quy hiện hành); nghiên cứu thực nghiệm (**mọi khẳng định về hiệu năng và độ chính xác đều phải có số đo tái lập được**, kèm cấu hình phần cứng và cỡ mẫu); và quy trình phát triển theo giai đoạn, mỗi giai đoạn khép lại bằng một bộ tài liệu và một mốc kiểm chứng.

### 1.4.1. Phân định phần tự xây dựng và phần dùng lại

Bảng phân định chi tiết từng thành phần — nguồn gốc và phần việc nhóm thực hiện đã làm — đặt ở **Phụ lục IV**. Hai khối **không có sẵn trong bất kỳ thư viện nào** và là đóng góp kỹ thuật chính của đề tài: khối xử lý ảnh vùng biển (nắn hình, phân loại bố cục, tách hai nửa, ghép ngang) và khối hậu xử lý theo quy chuẩn (mặt nạ vị trí, tập mã tỉnh, bảng ánh xạ nhầm lẫn).

## 1.5. Đóng góp của đề tài

### 1.5.1. Tuyên bố trung thực về mức đóng góp

> **Đề tài không tạo ra kết quả state-of-the-art.** Các con số trên 99% trong tài liệu ALPR quốc tế thường dựa trên hạ tầng GPU và dữ liệu riêng; đồ án làm việc trên máy không có GPU CUDA nên không đặt mục tiêu tương tự.

**Ba đóng góp có thể kiểm chứng.**

**(a) Bộ luật hậu xử lý ràng buộc theo VỊ TRÍ trong chuỗi**, khai thác ba ràng buộc đặc thù của quy chuẩn Việt Nam: mã địa phương thuộc **81 giá trị** chứ không phải `\d{2}`; sê-ri **thứ nhất** thuộc 20 chữ cái có `G` không có `R` [7]<!-- bocongan_2024_nhandienbienso -->, sê-ri **thứ hai** của biển mô tô thuộc **20 chữ cái khác** có `R` không có `G`; và bảng ánh xạ nhầm lẫn ký tự **không đối xứng**. Một hệ thống dùng danh sách phẳng sẽ sai có hệ thống trên mọi biển xe máy mang `R`.

**(b) Đo được ĐỊNH LƯỢNG đóng góp của khối hậu xử lý** — phần lớn công trình mô tả bước này ở mức định tính, không trả lời được *nó đóng góp bao nhiêu*. Đồ án giải quyết ở tầng dữ liệu, **lưu song song chuỗi OCR thô và chuỗi đã sửa**, nên hiệu số NFR-A6 − NFR-A5 là một con số đo được: **+13,28 điểm, sửa đúng 372 biển, làm hỏng 0** trên 2.801 mẫu. Cùng nguyên tắc ấy áp cho **NFR-A8**, biến việc **báo cáo tách riêng biển một dòng và hai dòng** thành nghĩa vụ bắt buộc thay vì phân tích tuỳ chọn.

**(c) Đo trên chính ảnh biển số Việt Nam.** Khảo sát không tìm thấy benchmark công khai nào so sánh các bộ nhận dạng ký tự trên riêng ảnh biển số xe máy Việt Nam hai dòng. Đồ án chạy ba phép so sánh trên cùng máy và cùng ngữ liệu — PP-OCRv5_mobile ↔ PP-OCRv6_medium (3.3.2), bộ nhận dạng gốc ↔ bản tinh chỉnh (5.5), và **PaddleOCR ↔ EasyOCR ↔ Tesseract trên toàn bộ 2.801 biển** (3.3.3): PaddleOCR **68,87%**, hơn EasyOCR 54,59 điểm và Tesseract 58,59 điểm. Một kết quả **khác dự đoán ban đầu**: bước tách rồi ghép ngang nâng PaddleOCR **34,92 điểm** nhưng chỉ nâng Tesseract **0,03 điểm**, nên nó **không** phải kỹ thuật độc lập bộ nhận dạng như giả định.

Ngoài ba đóng góp trên, đồ án bàn giao một hệ thống có kiến trúc phần mềm đầy đủ — tầng AI tách hoàn toàn khỏi tầng API, REST API tự sinh tài liệu, giao diện web, cơ sở dữ liệu có migration, đóng gói Docker, **1.004 kiểm thử tự động đạt, bao phủ tầng nghiệp vụ 87,7%** — và mọi số liệu hiệu năng công bố kèm cấu hình phần cứng. Đây là phần **kỹ nghệ**, nêu ra để mô tả sản phẩm bàn giao chứ không tính là đóng góp khoa học.

### 1.5.2. Những gì đề tài KHÔNG tuyên bố

Đề tài **không** tuyên bố vượt các con số độ chính xác cao nhất trong nước (chúng đo trên tập dữ liệu riêng không công khai, không có cơ sở so sánh công bằng), **không** đề xuất kiến trúc mạng nơ-ron mới, và **không** giải quyết các thách thức mở như độ phân giải rất thấp hay tổng quát hoá xuyên tập dữ liệu (Chương 6). Mọi số liệu hiệu năng là **số liệu CPU**, không so sánh trực tiếp được với FPS đo trên GPU.
