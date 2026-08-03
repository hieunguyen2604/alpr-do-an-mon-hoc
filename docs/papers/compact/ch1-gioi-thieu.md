# CHƯƠNG 1. GIỚI THIỆU

## 1.1. Đặt vấn đề

### 1.1.1. Bối cảnh giao thông Việt Nam và nhu cầu tự động hoá

Tính đến tháng 9/2024, Việt Nam có khoảng **77 triệu xe máy đã đăng ký, tương đương 770 xe trên 1.000 dân**; xe máy chiếm khoảng **85–90% lưu lượng phương tiện trên đường** [1]<!-- dantri_2024_77trieuxemay -->. Con số đó là **ràng buộc kỹ thuật trực tiếp**, kéo theo ba hệ quả (Chương 4): (i) **biển hai dòng gần vuông chiếm đa số tuyệt đối** vì mọi xe mô tô đều mang biển hai dòng; (ii) **mật độ cao gây che khuất**, mỗi khung hình thường có **nhiều biển số**; (iii) biển xe mô tô chỉ 140 × 190 mm nên đây là **bài toán phát hiện đối tượng nhỏ**. Ở quy mô đó, ghi nhận thủ công không khả thi — lý do tồn tại của **ALPR (Automatic License Plate Recognition)** [2]<!-- anagnostopoulos_2008_survey --> [3]<!-- du_2013_review -->.

### 1.1.2. Ứng dụng thực tế của hệ thống ALPR

ALPR là lõi của bốn nhóm ứng dụng tại Việt Nam: **bãi đỗ xe thông minh** [4]<!-- eparking_nd_nhandangbienso -->; **thu phí không dừng ETC** [5]<!-- vetc_nd_thuphikhongdung -->; **giám sát giao thông** (xử phạt nguội); **kiểm soát ra vào** [6]<!-- viscom_nd_vietanpr -->. Cả bốn đo cùng một thứ: **không phải mAP của khâu phát hiện, mà là tỉ lệ đọc đúng toàn bộ chuỗi biển số** (plate-level exact match) — đọc đúng 9 trên 10 ký tự vẫn là đọc sai biển. Nhận định này định hình chỉ tiêu ở mục 1.2.2 và cách đánh giá ở Chương 5.

### 1.1.3. Vì sao không thể dùng trực tiếp giải pháp nước ngoài

**(a) Biển hai dòng là điểm gãy đã đo được, không phải rủi ro giả định.** Trên tập kiểm thử cân bằng có chủ ý của bộ **RodoSol-ALPR (Brazil)** — 4.000 ảnh ô tô biển **một dòng**, 4.000 ảnh xe máy biển **hai dòng** — hệ thống thương mại **OpenALPR** nhận đúng **94,3% biển một dòng nhưng chỉ 45,7% biển hai dòng, chênh 48,6 điểm phần trăm**, không biến số nào khác thay đổi ngoài bố cục biển [7]<!-- laroca_2022_crossdataset -->. Cũng nghiên cứu này: cả 12 phương pháp và 2 hệ thống thương mại đều **không vượt quá 70%** recognition rate, và có công trình phải **loại bỏ hoàn toàn xe máy** khỏi thí nghiệm [7]<!-- laroca_2022_crossdataset -->.

> ⚠️ **Cảnh báo phạm vi áp dụng của số liệu.** Cặp **94,3% / 45,7%** (chênh **48,6 điểm phần trăm**) đo trên **RodoSol-ALPR của Brazil**, **không phải trên dữ liệu Việt Nam**; dẫn như một ***analogue*** định lượng về độ khó của biển hai dòng, chọn Brazil vì cũng là nước có tỉ lệ xe máy cao. **Tuyệt đối không được trình bày cặp số này như số liệu Việt Nam** — số liệu Việt Nam do chính đồ án đo nằm ở **Chương 5**.

**(b) Căn cứ pháp lý và cấu trúc chuỗi ký tự là đặc thù quốc gia.** Biển số xe Việt Nam theo **TT 79/2024/TT-BCA** (hiệu lực 01/01/2025) [8]<!-- bocongan_2024_tt79 -->, sửa đổi bởi **TT 13/2025/TT-BCA** [9]<!-- bocongan_2025_tt13 --> và **TT 51/2025/TT-BCA** [10]<!-- bocongan_2025_tt51 -->; kích thước vật lý theo **QCVN 08:2024/BCA** [11]<!-- bocongan_2024_qcvn08 -->. **Đính chính:** nhiều tài liệu trong nước vẫn viện dẫn **TT 24/2023/TT-BCA** [12]<!-- bocongan_2023_tt24 --> — **đã hết hiệu lực từ 01/01/2025**. Ba đặc thù sau **không học được từ dữ liệu nước ngoài**. **(i) Tập ký tự seri phụ thuộc vị trí:** seri **vị trí thứ nhất** thuộc tập **20 chữ cái** (có `G`, không có `R`) [13]<!-- bocongan_2024_nhandienbienso -->; **vị trí thứ hai** của biển xe mô tô thuộc tập **20 chữ cái khác** (có `R`, không có `G`); tập loại trừ đúng cho toàn hệ thống chỉ gồm **5 chữ `I`, `J`, `O`, `Q`, `W`** — charset theo "danh sách phẳng 20 chữ cái" sẽ **sai hệ thống trên toàn bộ lớp biển xe máy có `R` ở vị trí thứ hai**, lỗi không cứu được ở hậu xử lý. **(ii) Mã địa phương hữu hạn, có lỗ hổng:** dải 11–99 chỉ có **81 mã đang được sử dụng**; **8 mã — 13, 42, 44, 45, 46, 87, 91, 96 — không được gán** [14]<!-- thuviennhadat_2025_kyhieu34tinh -->, nên `\d{2}` cho qua 8 chuỗi không bao giờ tồn tại. **(iii) Tỉ lệ khung hình phân tách rõ hai bố cục** [11]<!-- bocongan_2024_qcvn08 -->: 110 × 520 mm → **4,727** (1 dòng); 165 × 330 mm → **2,000** (2 dòng); 140 × 190 mm → **1,357** (2 dòng); không loại biển nào rơi vào khoảng mở **(2,000 ; 4,727)** — cơ sở hình học để phân loại số dòng.

**(c) Điều kiện thu nhận ảnh khác biệt:** biển bị che, bám bụi, cong vênh, chụp nghiêng, ngược sáng, ảnh đêm — khác các bộ dữ liệu quốc tế lớn (CCPD, AOLP, SSIG) vốn lấy ô tô làm trung tâm. **Kết luận mục 1.1:** bài toán này cần **hệ thống huấn luyện trên dữ liệu Việt Nam và khối hậu xử lý xây theo quy chuẩn Việt Nam.**

## 1.2. Mục tiêu đề tài

### 1.2.1. Mục tiêu tổng quát

Xây dựng một **hệ thống nhận dạng biển số xe Việt Nam hoàn chỉnh, chất lượng gần sản phẩm thực tế**: mô hình phát hiện tự huấn luyện trên dữ liệu Việt Nam, khối nhận dạng ký tự, khối hậu xử lý theo quy chuẩn Việt Nam, backend REST API, giao diện web, cơ sở dữ liệu lịch sử, đóng gói triển khai, tài liệu học thuật đầy đủ; hỗ trợ **cả biển một dòng và hai dòng**, **suy luận hoàn toàn trên CPU**. Đây **không phải** demo dạng notebook, cũng **không phải** sản phẩm thương mại.

### 1.2.2. Mục tiêu cụ thể

Mỗi chỉ tiêu có **mục tiêu** và **ngưỡng tối thiểu** (bắt buộc đạt). Về chức năng và chất lượng phần mềm: **34 yêu cầu chức năng** (21 *Must*, 6 *Should*, 3 *Could*, 4 *Won't*) trong **sáu nhóm** (mục 4.1.3); **NFR-M1** mã pipeline AI **không import FastAPI**; **NFR-M5** thay được bộ OCR không sửa mã tầng API; **NFR-M2** độ bao phủ kiểm thử tầng nghiệp vụ **≥ 70%**; **khởi động một lệnh** `docker compose up`, demo **không cần Internet**. **NFR-A5 và NFR-A6 đo tách bạch có chủ đích** — hiệu số là **đóng góp định lượng của khối hậu xử lý** (mục 1.6); thêm **NFR-A8** (tách riêng biển một dòng / hai dòng) và **NFR-A9** (theo điều kiện ảnh, nếu có nhãn phù hợp).

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
| NFR-P7 | Bộ nhớ thường trú của backend | ≤ 2 GB | ≤ 4 GB |

Các chỉ tiêu độ trễ "rộng rãi" hơn bài báo ALPR vì máy phát triển **không có GPU CUDA** (CON-02): huấn luyện trên GPU Colab/Kaggle, **toàn bộ suy luận và demo chạy trên CPU**, còn bài báo thường đo trên GPU RTX/V100. Mọi số liệu hiệu năng **bắt buộc kèm cấu hình phần cứng** (Phụ lục P.1).

> ⚠️ **Bốn yêu cầu mức *Won't* — phải nói thẳng.** Cả bốn đều **thuần giao diện**, chuyển mức trong hai đợt thu gọn giao diện web ngày **2026-07-20**: đợt 1 gỡ trang Webcam → **FR-3.1 và FR-3.4 chuyển M → W** (nhận dạng thời gian thực vẫn phục vụ và vẫn có kiểm thử ở tầng API qua `POST /api/detect/frame`); đợt 2 gỡ trang Tổng quan (Dashboard) → **FR-4.1 chuyển M → W**, **FR-4.2 chuyển S → W** (thống kê và biểu đồ theo thời gian vẫn truy vấn được và vẫn có kiểm thử tích hợp qua `GET /api/statistics`, `GET /health`). **FR-4.1 là yêu cầu mức *Must* đầu tiên và duy nhất bị đưa ra khỏi phạm vi trong toàn bộ đồ án** — nêu ở đây, ở mục 4.1.3, mục 6.3 và trong đặc tả yêu cầu, không để hội đồng tự phát hiện. Đây là **quyết định phạm vi có chủ đích**, không phải hạng mục bỏ sót: cả bốn mất **màn hình hiển thị**, không mất **năng lực hệ thống**, mã giao diện còn nguyên trong lịch sử git. Đánh đổi đo được của đợt 2: gỡ thư viện biểu đồ `recharts` cùng trang Tổng quan làm gói tải về của giao diện giảm từ ~730 KB xuống **328,8 KB** (−55%).

### 1.2.3. Tiêu chí thành công

Đề tài thành công khi **đồng thời**: (1) toàn bộ yêu cầu *Must* hoạt động và demo được — theo bộ 21 *Must* **sau** hai đợt thu gọn 2026-07-20, bốn yêu cầu đã chuyển *Won't* (FR-3.1, FR-3.4, FR-4.1, FR-4.2) **không** tính là đạt; (2) mọi chỉ tiêu đạt **ngưỡng tối thiểu** và **có bằng chứng đo đạc**; (3) đủ 12 sản phẩm bàn giao; (4) khởi động trên máy sạch bằng một lệnh `docker compose up`; (5) demo trực tiếp không cần Internet.

> **Trạng thái tại thời điểm viết chương này.** Các chỉ tiêu ở mục 1.2.2 là **chỉ tiêu đặt ra**. Hệ thống chạy pipeline nhận dạng **thật** với `models/best.pt` (`imgsz=640`, split v3); chỉ tiêu phát hiện **đều đạt** (mAP@0.5 = 0,9829), độ trễ NFR-P1 **đạt** (p95 731/780 ms); chỉ tiêu độ chính xác OCR **đã đo** và biển hai dòng **chưa đạt** (kết quả thật). **Đối chiếu đầy đủ từng chỉ tiêu ở Chương 5.**

## 1.3. Đối tượng và phạm vi nghiên cứu

### 1.3.1. Đối tượng nghiên cứu

Ba nhóm. **(1) Biển số xe cơ giới Việt Nam** theo TT 79/2024/TT-BCA [8]<!-- bocongan_2024_tt79 --> (sửa đổi bởi TT 13/2025 [9]<!-- bocongan_2025_tt13 --> và TT 51/2025 [10]<!-- bocongan_2025_tt51 -->) và QCVN 08:2024/BCA [11]<!-- bocongan_2024_qcvn08 -->; biển nền đỏ quân đội thuộc TT 169/2021/TT-BQP [15]<!-- boquocphong_2021_tt169 -->, chỉ xử lý ở mức nhận biết ký hiệu. **(2) Mô hình phát hiện họ YOLO** — cụ thể YOLO11 [16]<!-- jocher_2024_yolo11 -->. **(3) Engine OCR** không cần phân đoạn ký tự: PaddleOCR [17]<!-- cui_2026_ppocrv5 --> là **baseline**, EasyOCR ngang hàng, Tesseract là mốc dưới, kèm bộ luật hậu xử lý theo vị trí. **Lựa chọn engine OCR chưa chốt ở giai đoạn thiết kế** — quyết định thuộc về benchmark do chính đồ án chạy (**mục 3.3**, **Chương 5**).

### 1.3.2. Phạm vi trong nghiên cứu

Bốn nhóm. **(a) Trí tuệ nhân tạo:** huấn luyện YOLO11 trên dữ liệu Việt Nam, so sánh biến thể n / s / m, kèm YOLO26n đối chứng (mục 3.2); **benchmark các engine OCR** trên chính tập kiểm thử biển số Việt Nam rồi tích hợp engine thắng cuộc; hậu xử lý theo luật hợp lệ theo vị trí; **hỗ trợ cả biển một dòng và hai dòng**; đánh giá đầy đủ (mAP, precision, recall, F1, ma trận nhầm lẫn); đo hiệu năng trên CPU. **(b) Dữ liệu:** thu thập, gộp, làm sạch bộ công khai; sửa nhãn; loại ảnh trùng lặp; tăng cường; chia train / val / test **có kiểm soát rò rỉ dữ liệu**; thống kê. **(c) Phần mềm:** FastAPI + Swagger; nhận dạng ảnh, video và khung hình thời gian thực qua `POST /api/detect/frame`; lịch sử bằng SQLite + SQLAlchemy + Alembic; giao diện React + Vite + TypeScript + TailwindCSS **ba trang** (Nhận dạng ảnh — trang chủ, Nhận dạng video, Lịch sử) sau hai đợt thu gọn 2026-07-20; tìm kiếm, lọc, tải về; thống kê ở tầng API (`GET /api/statistics`); Docker và Docker Compose. **(d) Kiểm thử, tài liệu:** unit test, integration test, kiểm thử độ chính xác AI, hiệu năng, chịu tải; tài liệu học thuật và kỹ thuật.

### 1.3.3. Phạm vi ngoài nghiên cứu

Danh sách này là **hàng rào trước câu hỏi "sao không làm X"**; không hạng mục nào bị loại vì "không kịp làm". **Mười một hạng mục:** (1) **xác thực, phân quyền** — chạy nội bộ `localhost`/LAN (giả định A-04); (2) **đa camera / đa luồng**; (3) **bám vết qua khung hình (SORT / DeepSORT)** — thay bằng **gộp trùng theo chuỗi ký tự**; (4) **phân loại loại xe** — từ 01/01/2025 TT 79/2024 **đã bỏ** quy tắc suy loại xe từ chữ cái seri; (5) **ước lượng tốc độ, phát hiện vi phạm** — cần hiệu chuẩn camera riêng; (6) **biển số nước ngoài**; (7) **barie / cổng tự động** — cần thiết bị vật lý; (8) **cloud, multi-tenant, CI/CD production** — **Docker Compose đã đủ**; (9) **ứng dụng di động** — web responsive đã đáp ứng; (10) **huấn luyện engine OCR từ đầu** — dùng pre-trained rồi **tinh chỉnh**; tinh chỉnh nằm **trong** phạm vi (mục 2.4.3(f)); (11) **suy luận thời gian thực trên GPU** — máy phát triển **không có GPU CUDA** (CON-02) ⇒ mọi số liệu là **số liệu CPU**.

### 1.3.4. Ranh giới hệ thống

![](figures/fig-ch1-01.png)

**Hình 1.1.** Ranh giới hệ thống — phần bên trong là hệ thống bàn giao, Colab/Kaggle nằm ngoài

Colab/Kaggle nằm **ngoài** ranh giới khi vận hành — chỉ là công cụ ngoại tuyến sản xuất `best.pt`; hệ thống khi chạy **không phụ thuộc dịch vụ ngoài nào** (mục 1.2.3). Sau khi trang webcam bị gỡ (2026-07-20), client gửi khung hình trực tiếp qua `POST /api/detect/frame`.

## 1.4. Phương pháp nghiên cứu

Đề tài dùng **ba phương pháp bổ trợ nhau**: nghiên cứu lý thuyết (khảo sát tài liệu có trích dẫn, đối chiếu văn bản pháp quy hiện hành); nghiên cứu thực nghiệm (**mọi khẳng định về hiệu năng và độ chính xác đều phải có số đo tái lập được**, kèm cấu hình phần cứng và cỡ mẫu); và quy trình phát triển theo giai đoạn, mỗi giai đoạn khép lại bằng một bộ tài liệu và một mốc kiểm chứng. Mô tả đầy đủ ba phương pháp cùng danh sách mười một giai đoạn ở **Phụ lục P.1**.

## 1.5. Ý nghĩa khoa học và thực tiễn

### 1.5.1. Ý nghĩa khoa học

**(a) Lấp một khoảng trống báo cáo có thật:** khảo sát Phase 1 cho thấy **chưa có công trình Việt Nam nào công bố bảng so sánh tách riêng độ chính xác giữa biển một dòng và biển hai dòng trên cùng một hệ thống**, trong khi trên bộ RodoSol-ALPR của Brazil chênh lệch giữa hai bố cục có thể tới 48,6 điểm phần trăm [7]<!-- laroca_2022_crossdataset --> — **một con số tổng thể có thể che giấu hoàn toàn điểm gãy của hệ thống**. **(b)** Hệ thống hoá bộ luật hậu xử lý theo **cấu trúc vị trí** trên căn cứ pháp lý hiện hành (mục 1.6.3). **(c)** Bộ quy tắc công bố số liệu ở Phụ lục P.1.

### 1.5.2. Ý nghĩa thực tiễn

**(a)** Sản phẩm là hệ thống chạy được chứ không phải notebook, khởi động một lệnh, không cần Internet, dùng được làm **nền tảng khởi đầu** cho triển khai quy mô nhỏ; kiểm thử (Phase 7) và đóng gói Docker (Phase 8) **đã xong**. **(b)** Toàn bộ chỉ tiêu hiệu năng là chỉ tiêu **CPU** — nơi triển khai quy mô nhỏ thường không có máy chủ GPU. **(c)** Bộ hằng số theo TT 79/2024 + QCVN 08:2024 (81 mã tỉnh, hai tập chữ cái seri theo vị trí, ba mức tỉ lệ khung hình) dùng lại được; tài liệu ghi rõ giao thức đo và cấu hình phần cứng để nhóm sau **đối chứng**.

## 1.6. Đóng góp của đề tài

### 1.6.1. Tuyên bố trung thực về mức đóng góp

> **Đề tài này không tạo ra kết quả state-of-the-art.**

Các con số vượt 99% trong tài liệu ALPR quốc tế đến từ nhóm nghiên cứu chuyên nghiệp có hạ tầng GPU lớn và dữ liệu độc quyền. Một đồ án làm trên máy không có GPU CUDA **không đặt mục tiêu đó** — tuyên bố ngược lại là thiếu trung thực học thuật. Đóng góp thực sự nằm ở sáu chỗ, cụ thể và kiểm chứng được.

### 1.6.2. Đóng góp (a) — Hệ thống hoàn chỉnh từ mô hình AI đến giao diện và triển khai

Sản phẩm có **kiến trúc phần mềm**, không phải tập script rời rạc: pipeline AI tách hoàn toàn khỏi tầng API (NFR-M1), interface trừu tượng thay engine OCR không sửa tầng API (NFR-M5), REST API có tài liệu tự sinh, giao diện web **ba màn hình**, cơ sở dữ liệu có migration, kiểm thử ≥ 70%, Docker một lệnh. Khảo sát Phase 1: mã nguồn mở ALPR Việt Nam chủ yếu là script rời rạc **không công bố số liệu độ chính xác** — **khoảng trống kỹ nghệ**, không phải khoảng trống thuật toán, nhưng vẫn có thật.

> **Mức độ hoàn thành tại thời điểm viết.** Tách tầng AI, interface trừu tượng, REST API, migration **đã cài đặt và xác minh bằng yêu cầu HTTP thật**; giao diện web **đã hoàn thành**, build sạch. Độ bao phủ ≥ 70% **đã đạt và đã đo**: **87,7%** tầng nghiệp vụ (đo 2026-07-20, `docs/reports/13-refactor-result.json`; Phase 7 trước đó 88,1%, toàn kho 42,0%), **882 test thu thập / 881 đạt / 1 xfail / 0 thất bại**. Docker và Docker Compose **đã hoàn thành**. Chi tiết ở **Chương 5**.

### 1.6.3. Đóng góp (b) — Bộ luật hậu xử lý ràng buộc theo VỊ TRÍ cho biển số Việt Nam

Bộ luật khai thác ba ràng buộc đặc thù: **(i) tập hợp lệ khác nhau theo từng vị trí** — mã địa phương thuộc **81 giá trị hợp lệ** chứ không phải `\d{2}` [14]<!-- thuviennhadat_2025_kyhieu34tinh -->, seri **thứ nhất** thuộc **20 chữ cái** có `G` không có `R` [13]<!-- bocongan_2024_nhandienbienso -->, seri **thứ hai** của biển xe mô tô thuộc **20 chữ cái KHÁC** có `R` không có `G`, hoặc **chữ số 1–9** (không có `0`) với biển kiểu cũ; **(ii) cấu trúc chuỗi và độ dài** theo quy chuẩn, cho phép sinh mặt nạ vị trí cho từng dạng biển; **(iii) định dạng cũ và mới cùng tồn tại**. Mấu chốt: sửa lỗi OCR theo **vị trí trong chuỗi chứ không theo ánh xạ hai chiều** — với cặp `O ↔ 0`, ánh xạ đúng là `O → 0` tại vị trí chữ số và `0 → D` tại vị trí chữ cái, **không** phải `O → 0` và `0 → O`.

> ⚠️ **Nói thẳng về độ lớn của đóng góp này.** Luận điểm dự kiến ban đầu — *"khai thác bộ 20 chữ cái, loại trừ 6 chữ `I J O Q R W`"* — **sai và đã bị bác bỏ ở Phase 1**: tập loại trừ toàn hệ thống chỉ có **5 chữ** (`I`, `J`, `O`, `Q`, `W`), chữ `R` **hợp lệ** ở vị trí seri thứ hai của biển xe mô tô. Sửa lại **làm yếu đi** phần đóng góp nếu tính theo "số ký tự loại trừ được" — không gian tìm kiếm thu hẹp ít hơn dự kiến. Đổi lại, phần có giá trị nằm ở ràng buộc **phụ thuộc vị trí**: hệ thống dùng danh sách phẳng 20 chữ cái sẽ **sai hệ thống trên toàn bộ lớp biển xe máy có `R` ở vị trí thứ hai**, và đây mới là lỗi mà bộ luật của đề tài ngăn được. **Đóng góp này vì vậy được trình bày là *đúng đắn về mặt pháp lý và đúng cấu trúc theo vị trí*, không phải một cải thiện lớn về không gian tìm kiếm.**

### 1.6.4. Đóng góp (c) — Đo được ĐỊNH LƯỢNG đóng góp của bước hậu xử lý

Phần lớn công trình mô tả bước hậu xử lý ở mức định tính, không trả lời được *bước đó đóng góp bao nhiêu*. Đề tài giải quyết ở tầng dữ liệu: **lưu đồng thời cả chuỗi OCR thô và chuỗi đã sửa** cho mỗi lần nhận dạng; hiệu số giữa **NFR-A5** (*trước*) và **NFR-A6** (*sau* hậu xử lý) do đó là một **con số đo được**, trình bày ở **Chương 5**.

### 1.6.5. Đóng góp (d) — Đánh giá tách riêng biển một dòng và biển hai dòng

Khoảng trống báo cáo đã xác định ở mục 1.5.1; **NFR-A8** biến phép tách này thành nghĩa vụ báo cáo bắt buộc chứ không phải phân tích tuỳ chọn, kèm **NFR-A9** — báo cáo theo điều kiện ảnh, nếu bộ dữ liệu có nhãn phù hợp.

### 1.6.6. Đóng góp (e) — Công bố hiệu năng kèm cấu hình phần cứng CPU cụ thể

Mọi số liệu hiệu năng công bố kèm **model CPU, số luồng, kích thước ảnh đầu vào, backend suy luận và cỡ mẫu đo** (Phụ lục P.1) — FPS không kèm phần cứng thì không thể tái lập, không thể so sánh.

### 1.6.7. Đóng góp (f) — Đo trên chính ảnh biển số Việt Nam, và một khoản nợ được ghi nhận

Phase 1 xác định **không tồn tại benchmark công khai nào so sánh các engine OCR trên riêng ảnh biển số xe máy Việt Nam hai dòng**; hai số liệu thường được viện dẫn để chứng minh ưu thế của một engine đã **bị bác bỏ khi truy ngược về nguồn gốc** (mục 3.3). **Phần đã làm được:** hai phép so sánh trên chính ảnh biển số Việt Nam, cùng máy và cùng ngữ liệu — **PP-OCRv5_mobile so với PP-OCRv6_medium** trên 200 vùng cắt (67,0% ở 23,0 ms so với 72,5% ở 386,9 ms, mục 3.3.2), và **bộ nhận dạng gốc so với bản tinh chỉnh** trên 2.801 biển có nhãn chuỗi với bốn cấu hình (mục 4.5.3). Cả hai đều cho kết quả **trái kỳ vọng ban đầu**: chỉ đọc tài liệu rồi chọn theo con số cao nhất thì cả hai quyết định đều sai.

> ✅ **Khoản nợ này đã trả, ngày 03/08/2026.** Ma trận so sánh **PaddleOCR ↔ EasyOCR ↔ Tesseract** — đúng khoảng trống số 4 mà Chương 2 đánh giá là có giá trị khoa học cao nhất — **đã chạy trên toàn bộ 2.801 biển** (mục 3.3.3). Kết quả: PaddleOCR **68,87%**, hơn EasyOCR 54,59 điểm và hơn Tesseract 58,59 điểm, **bác bỏ** tài liệu công khai vốn nghiêng về EasyOCR. Một kết quả **trái kỳ vọng** khác: bước tách-rồi-ghép-ngang mua 34,92 điểm cho PaddleOCR nhưng chỉ 0,03 điểm cho Tesseract, nên nó **không** phải kỹ thuật độc lập engine — chỉ bộ luật hậu xử lý mới là.

### 1.6.8. Những gì đề tài KHÔNG tuyên bố

Bốn điều loại trừ. **Không** tuyên bố vượt các con số độ chính xác cao nhất trong nước — chúng đo trên tập dữ liệu riêng không công khai, **không có cơ sở so sánh công bằng**. **Không** đề xuất kiến trúc mạng nơ-ron mới; đề tài **tích hợp và tinh chỉnh**. **Không** giải quyết các thách thức mở — độ phân giải rất thấp, tổng quát hoá xuyên tập dữ liệu, che khuất nặng (**Hướng phát triển, Chương 6**). Mọi số liệu hiệu năng là **số liệu CPU**, **không so sánh trực tiếp được** với FPS đo trên GPU.

## 1.7. Bố cục quyển đồ án

Quyển gồm sáu chương. **Chương 2 — Cơ sở lý thuyết:** ALPR, YOLO, nhận dạng ký tự không phân đoạn, **quy chuẩn biển số Việt Nam theo TT 79/2024 và QCVN 08:2024**, công trình liên quan và khoảng trống nghiên cứu. **Chương 3 — Khảo sát công nghệ và lựa chọn mô hình:** bảy thế hệ YOLO, tám engine OCR ứng viên (kèm benchmark ba engine tự đo trên 2.801 biển), runtime CPU, độ phân giải đầu vào, và **ranh giới giữa cái đã đo và cái mới chỉ khảo sát tài liệu**. **Chương 4 — Thiết kế và cài đặt hệ thống:** yêu cầu, kiến trúc tách tầng, bộ dữ liệu, huấn luyện bộ phát hiện, **tinh chỉnh bộ nhận dạng và phép đo có/không tinh chỉnh**, pipeline AI — backend — giao diện, Docker, và những chỗ cài đặt lệch khỏi thiết kế. **Chương 5 — Thực nghiệm và đánh giá:** giao thức đo, **tách riêng biển một dòng và hai dòng**, **đo đóng góp định lượng của khối hậu xử lý**, hiệu năng CPU kèm cấu hình phần cứng, đối chiếu từng chỉ tiêu NFR, ca lỗi và mối đe doạ đến tính hợp lệ. **Chương 6 — Kết luận và hướng phát triển.** Cuối quyển là **Tài liệu tham khảo** và **Phụ lục**.

> **Vì sao khảo sát công nghệ tách thành chương riêng:** đây là phần hội đồng hỏi nhiều nhất, bản thảo trước lại để khuất cuối chương cơ sở lý thuyết; Chương 3 gom về một chỗ trả lời tường minh — kể cả khi câu trả lời trung thực đôi lúc là *"chưa đo được"*.

## Tóm tắt chương

Chương 1 xác lập bốn nền tảng. **Lý do tồn tại của đề tài:** với 77 triệu xe máy [1]<!-- dantri_2024_77trieuxemay -->, **biển hai dòng là đa số tuyệt đối**; OpenALPR trên tập kiểm thử cân bằng của bộ **RodoSol-ALPR (Brazil)** đạt **94,3% trên biển một dòng nhưng chỉ 45,7% trên biển hai dòng, chênh 48,6 điểm phần trăm** [7]<!-- laroca_2022_crossdataset --> — dẫn như *analogue*, **không phải số liệu Việt Nam**; cộng với cấu trúc chuỗi theo TT 79/2024 và QCVN 08:2024 ⇒ giải pháp huấn luyện trên dữ liệu nước ngoài **không áp dụng trực tiếp được**. **Mục tiêu đo được:** **mAP@0.5 ≥ 0,90**, **độ chính xác toàn trình ≥ 0,88**, **độ trễ p95 ≤ 800 ms trên CPU**. **Ranh giới:** phạm vi trong bốn nhóm, phạm vi ngoài **11 hạng mục kèm lý do loại trừ tường minh**. **Đóng góp trung thực:** đề tài **không tạo ra kết quả state-of-the-art**; sáu đóng góp: (a) hệ thống hoàn chỉnh có kiến trúc phần mềm; (b) bộ luật hậu xử lý **ràng buộc theo vị trí**; (c) **đo định lượng** đóng góp của hậu xử lý; (d) **tách riêng** biển một dòng và hai dòng; (e) hiệu năng **kèm cấu hình phần cứng CPU cụ thể**; (f) **benchmark engine OCR trên chính ảnh biển số Việt Nam**. Chương 2 trình bày cơ sở lý thuyết và quy chuẩn biển số Việt Nam.
