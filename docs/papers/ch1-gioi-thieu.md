# CHƯƠNG 1. GIỚI THIỆU

## 1.1. Đặt vấn đề

### 1.1.1. Bối cảnh giao thông Việt Nam và nhu cầu tự động hoá

Tính đến tháng 9/2024, Việt Nam có khoảng **77 triệu xe máy đã đăng ký, tương đương 770 xe trên 1.000 dân**; xe máy chiếm khoảng **85–90% lưu lượng phương tiện lưu thông trên đường** [1]<!-- dantri_2024_77trieuxemay -->. Đây không chỉ là thống kê quy mô mà là **ràng buộc kỹ thuật trực tiếp** đối với mọi hệ thống thị giác máy tính làm việc với giao thông Việt Nam, với ba hệ quả xuyên suốt các quyết định thiết kế ở Chương 4: (i) **biển hai dòng dạng gần vuông chiếm đa số tuyệt đối** chứ không phải thiểu số như tại Hoa Kỳ hay châu Âu, vì toàn bộ xe mô tô mang biển hai dòng; (ii) **mật độ phương tiện cao gây che khuất (occlusion) lẫn nhau**, đồng thời khiến mỗi khung hình thường chứa **nhiều biển số** phải xử lý đồng thời; (iii) **diện tích biển số trên khung hình nhỏ** — biển xe mô tô chỉ 140 × 190 mm — dẫn tới bài toán phát hiện đối tượng nhỏ. Ở quy mô hàng chục triệu phương tiện, ghi nhận và tra cứu biển số thủ công không còn khả thi; đó là lý do tồn tại của lớp bài toán **ALPR (Automatic License Plate Recognition)**, một trong những bài toán ứng dụng lâu đời và được nghiên cứu bền bỉ nhất của thị giác máy tính [2]<!-- anagnostopoulos_2008_survey --> [3]<!-- du_2013_review -->.

### 1.1.2. Ứng dụng thực tế của hệ thống ALPR

Tại Việt Nam, ALPR là thành phần lõi của bốn nhóm ứng dụng vận hành thực tế: **bãi đỗ xe thông minh** (ghi nhận biển lúc vào và lúc ra để tính phí và chống tráo xe — xử lý cả xe máy lẫn ô tô, đòi khớp chuỗi tuyệt đối, hoạt động liên tục [4]<!-- eparking_nd_nhandangbienso -->); **thu phí không dừng ETC** (đọc biển làm kênh đối chiếu song song với thẻ định danh phục vụ hậu kiểm và xử lý tranh chấp — phương tiện tốc độ cao, ảnh chụp ở tốc độ màn trập ngắn [5]<!-- vetc_nd_thuphikhongdung -->); **giám sát giao thông** (truy vết phương tiện, xử phạt nguội — ánh sáng biến thiên lớn, ảnh đêm, ngược sáng); và **kiểm soát ra vào** cơ quan, khu công nghiệp, chung cư (triển khai tại chỗ, không phụ thuộc kết nối Internet [6]<!-- viscom_nd_vietanpr -->). Điểm chung của cả bốn nhóm: **chỉ số có ý nghĩa với người dùng cuối không phải mAP của khâu phát hiện, mà là tỉ lệ đọc đúng toàn bộ chuỗi biển số** (plate-level exact match) — một hệ thống bãi xe đọc đúng 9 trên 10 ký tự vẫn là hệ thống đọc sai biển số. Nhận định này định hình cách đặt chỉ tiêu ở mục 1.2.2 và cách đánh giá ở Chương 6.

### 1.1.3. Vì sao không thể dùng trực tiếp giải pháp nước ngoài

**(a) Biển hai dòng là một điểm gãy đã đo được, không phải một rủi ro giả định.** Nghiên cứu *On the Cross-Dataset Generalization in License Plate Recognition* thiết kế một tập kiểm thử **cân bằng có chủ ý** trên bộ dữ liệu RodoSol-ALPR: 4.000 ảnh ô tô mang biển **một dòng** và 4.000 ảnh xe máy mang biển **hai dòng**. Trên cùng một hệ thống, cùng tập kiểm thử, cùng điều kiện đo, **OpenALPR** — một hệ thống ALPR thương mại đã trưởng thành — nhận đúng **3.772 / 4.000 biển một dòng (94,3%)** nhưng chỉ **1.827 / 4.000 biển hai dòng (45,7%)**, **chênh lệch 48,6 điểm phần trăm**, không có biến số nào khác thay đổi ngoài bố cục biển số [7]<!-- laroca_2022_crossdataset -->. Cũng trong nghiên cứu này, toàn bộ 12 phương pháp và 2 hệ thống thương mại được đánh giá đều **không vượt quá 70%** recognition rate; đáng chú ý hơn, bài báo ghi nhận có công trình **không thể chỉnh sửa phương pháp để xử lý biển nhiều dòng** nên đã phải **loại bỏ hoàn toàn xe máy** khỏi thí nghiệm [7]<!-- laroca_2022_crossdataset -->. Ý nghĩa với đề tài: một hệ thống ALPR xuất sắc ở thị trường nơi biển một dòng chiếm đa số hoàn toàn có thể **sụp đổ về gần một nửa hiệu năng** khi gặp phân bố phương tiện Việt Nam — đây không phải suy đoán mà là kết quả đo.

> ⚠️ **Cảnh báo phạm vi áp dụng của số liệu.** Cặp số **94,3% / 45,7%** được đo trên **RodoSol-ALPR của Brazil**, **không phải trên dữ liệu Việt Nam**. Nó được dẫn ở đây như một ***analogue*** định lượng về độ khó vượt trội của biển hai dòng — Brazil được chọn làm đối chiếu vì cũng là quốc gia có tỉ lệ xe máy cao. **Tuyệt đối không được trình bày cặp số này như số liệu Việt Nam.** Số liệu tương ứng cho biển số Việt Nam do chính đồ án đo sẽ được trình bày ở **Chương 6**.

**(b) Căn cứ pháp lý và cấu trúc chuỗi ký tự là đặc thù quốc gia.** Biển số xe Việt Nam được quy định bởi **Thông tư 79/2024/TT-BCA** (ký 15/11/2024, hiệu lực từ 01/01/2025) [8]<!-- bocongan_2024_tt79 -->, sửa đổi bổ sung bởi **Thông tư 13/2025/TT-BCA** [9]<!-- bocongan_2025_tt13 --> và **Thông tư 51/2025/TT-BCA** [10]<!-- bocongan_2025_tt51 -->; kích thước và hình thức vật lý theo **QCVN 08:2024/BCA** [11]<!-- bocongan_2024_qcvn08 -->. **Đính chính căn cứ pháp lý:** nhiều tài liệu kỹ thuật và mã nguồn mở trong nước hiện vẫn viện dẫn **Thông tư 24/2023/TT-BCA** [12]<!-- bocongan_2023_tt24 -->, văn bản này **đã hết hiệu lực từ 01/01/2025** và trong quyển chỉ được nhắc tới như bối cảnh lịch sử; toàn bộ luật kiểm tra tính hợp lệ được xây trên căn cứ hiện hành (chi tiết khảo sát pháp lý ở **Chương 2**). Ba đặc thù cấu trúc dưới đây không tồn tại trong bất kỳ bộ quy tắc biển số nước ngoài nào, do đó không thể học được từ dữ liệu nước ngoài. **Thứ nhất, tập ký tự seri phụ thuộc vị trí:** chữ cái seri ở **vị trí thứ nhất** thuộc một tập **20 chữ cái** (có `G`, không có `R`) [13]<!-- bocongan_2024_nhandienbienso -->, còn chữ cái seri ở **vị trí thứ hai** của biển xe mô tô thuộc một tập **20 chữ cái khác** (có `R`, không có `G`); tập loại trừ đúng cho toàn hệ thống chỉ gồm **5 chữ `I`, `J`, `O`, `Q`, `W`** — nên một hệ thống xây charset OCR theo "danh sách phẳng 20 chữ cái" sẽ **sai hệ thống trên toàn bộ lớp biển xe máy có `R` ở vị trí thứ hai**, loại lỗi không sửa được bằng hậu xử lý vì thông tin đã mất ở tầng mô hình. **Thứ hai, mã địa phương là tập hữu hạn có lỗ hổng:** dải 11–99 có 89 giá trị nhưng chỉ **81 mã đang được sử dụng** (80 mã địa phương và 01 mã Cục CSGT); **8 mã — 13, 42, 44, 45, 46, 87, 91, 96 — không được gán cho bất kỳ địa phương nào** [14]<!-- thuviennhadat_2025_kyhieu34tinh -->, nên biểu thức chính quy dùng `\d{2}` sẽ cho qua 8 chuỗi không bao giờ tồn tại. **Thứ ba, tỉ lệ khung hình phân tách rõ ràng giữa hai bố cục** theo QCVN 08:2024/BCA [11]<!-- bocongan_2024_qcvn08 -->: ô tô biển dài 110 × 520 mm cho tỉ lệ **4,727** (1 dòng), ô tô biển ngắn 165 × 330 mm cho **2,000** (2 dòng), xe mô tô 140 × 190 mm cho **1,357** (2 dòng) — không loại biển nào rơi vào khoảng mở **(2,000 ; 4,727)**, và khoảng trống rộng 2,727 đơn vị này là cơ sở hình học để phân loại số dòng một cách đáng tin cậy.

**(c) Điều kiện thu nhận ảnh khác biệt:** mật độ xe máy cao, biển bị che khuất bởi xe khác hoặc người ngồi sau, biển bám bụi, cong vênh, góc chụp nghiêng do camera gắn cao trong không gian hẹp, ảnh ngược sáng và ảnh đêm — tổ hợp này khác biệt đáng kể so với các bộ dữ liệu quốc tế lớn (CCPD, AOLP, SSIG) vốn lấy ô tô làm trung tâm. **Kết luận mục 1.1:** chênh lệch hiệu năng đã đo giữa hai bố cục biển, cấu trúc chuỗi do văn bản pháp quy Việt Nam quy định, và phân bố điều kiện thu nhận ảnh cùng dẫn tới một kết luận — **bài toán ALPR cho biển số Việt Nam cần một hệ thống được huấn luyện trên dữ liệu Việt Nam và có khối hậu xử lý xây theo quy chuẩn Việt Nam.** Đây là lý do tồn tại của đề tài.

## 1.2. Mục tiêu đề tài

### 1.2.1. Mục tiêu tổng quát

Xây dựng một **hệ thống nhận dạng biển số xe Việt Nam hoàn chỉnh, có chất lượng gần với sản phẩm thực tế**, gồm: mô hình phát hiện đối tượng tự huấn luyện trên dữ liệu biển số Việt Nam, khối nhận dạng ký tự, khối hậu xử lý theo quy chuẩn Việt Nam, backend REST API, giao diện web, cơ sở dữ liệu lịch sử, đóng gói triển khai và bộ tài liệu học thuật đầy đủ. Hệ thống phải hỗ trợ **cả biển một dòng và biển hai dòng**, và **suy luận hoàn toàn trên CPU** — chế độ mặc định, không phải chế độ dự phòng. Hai giới hạn được tuyên bố ngay tại đây: đây **không phải** một bản demo dạng notebook, và cũng **không phải** một sản phẩm thương mại triển khai thật.

### 1.2.2. Mục tiêu cụ thể

Mục tiêu cụ thể được phát biểu dưới dạng **chỉ tiêu đo được bằng số**, bám theo bộ yêu cầu phi chức năng đã chốt ở giai đoạn phân tích yêu cầu; mỗi chỉ tiêu có hai mức: **mục tiêu** và **ngưỡng tối thiểu** (bắt buộc phải đạt để đề tài được coi là thành công). Về **chức năng, chất lượng phần mềm và triển khai**, đề tài phải hiện thực **34 yêu cầu chức năng** (21 *Must*, 6 *Should*, 3 *Could*, 4 *Won't*) tổ chức thành **sáu nhóm** — nhận dạng ảnh, nhận dạng video, nhận dạng thời gian thực qua API, thống kê – lịch sử – tra cứu, quản lý dữ liệu, và hệ thống–vận hành (chi tiết ở mục 4.1.3); bảo đảm **tách biệt kiến trúc bắt buộc** (NFR-M1: mã pipeline AI **không import bất cứ thành phần nào của FastAPI**, kiểm chứng bằng phân tích import) và **khả năng thay thế bộ OCR** không phải sửa mã tầng API (NFR-M5); đạt **độ bao phủ kiểm thử tầng nghiệp vụ ≥ 70%** (NFR-M2); và **khởi động một lệnh duy nhất** `docker compose up` trên máy sạch, demo hoạt động **không cần kết nối Internet**. Trong nhóm độ chính xác, **NFR-A5 và NFR-A6 được đo tách bạch một cách có chủ đích** vì hiệu số giữa hai con số này chính là **đóng góp định lượng của khối hậu xử lý** (mục 1.6); bổ sung hai yêu cầu phân tích phục vụ chương đánh giá là **NFR-A8** — báo cáo độ chính xác **tách riêng cho biển một dòng và biển hai dòng** — và **NFR-A9** — báo cáo theo **điều kiện ảnh** (ban ngày / ban đêm / nghiêng / mờ), nếu bộ dữ liệu có nhãn phù hợp.

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

> **Vì sao các chỉ tiêu độ trễ này "rộng rãi" hơn số liệu thường thấy trong các bài báo ALPR.** Máy phát triển của đồ án **không có GPU CUDA** (ràng buộc CON-02); huấn luyện diễn ra trên GPU miễn phí của Colab/Kaggle, nhưng **toàn bộ suy luận và phần demo bảo vệ chạy trên CPU**. Các bài báo ALPR thường đo trên RTX/V100 và công bố vài chục mili-giây; đặt hai loại số liệu này cạnh nhau là so sánh sai. Đây là lý do mọi số liệu hiệu năng của đồ án đều **bắt buộc công bố kèm cấu hình phần cứng** — xem mục 1.4.2.

> ⚠️ **Bốn yêu cầu mức *Won't* — phải nói thẳng.** Cả bốn đều là **yêu cầu thuần giao diện**, cùng chuyển mức trong hai đợt thu gọn phạm vi giao diện web ngày **2026-07-20**: đợt 1 gỡ trang Webcam khiến **FR-3.1 và FR-3.4 chuyển M → W** (nhận dạng thời gian thực vẫn phục vụ và vẫn có kiểm thử ở tầng API qua `POST /api/detect/frame`); đợt 2 gỡ trang Tổng quan (Dashboard) khiến **FR-4.1 chuyển M → W** và **FR-4.2 chuyển S → W** (số liệu thống kê và biểu đồ theo thời gian vẫn truy vấn được và vẫn có kiểm thử tích hợp qua `GET /api/statistics`, `GET /health`). **FR-4.1 là yêu cầu mức *Must* đầu tiên và duy nhất bị đưa ra khỏi phạm vi trong toàn bộ đồ án.** Điều này được nêu ở đây, ở mục 4.1.3, ở mục 7.3 và trong đặc tả yêu cầu, chứ không để hội đồng tự phát hiện. Đây là một **quyết định phạm vi có chủ đích** nhằm thu gọn phần demo, không phải một hạng mục bị bỏ sót: cả bốn yêu cầu đều mất **màn hình hiển thị**, không mất **năng lực hệ thống**, và mã giao diện tương ứng còn nguyên trong lịch sử git. Đánh đổi đo được của đợt 2: gỡ thư viện biểu đồ `recharts` cùng trang Tổng quan làm gói tải về của giao diện giảm từ ~730 KB xuống **328,8 KB** (−55%).

### 1.2.3. Tiêu chí thành công

Đề tài được coi là thành công khi **đồng thời** đạt năm điều kiện: (1) toàn bộ yêu cầu mức *Must* hoạt động được và demo được — hiểu theo bộ 21 yêu cầu *Must* **sau** hai đợt thu gọn phạm vi giao diện ngày 2026-07-20, trong đó bốn yêu cầu đã chuyển sang mức *Won't* (FR-3.1, FR-3.4, FR-4.1, FR-4.2) **không** được tính là đạt và riêng FR-4.1 vốn ở mức *Must* (xem khung ghi chú ở mục 1.2.2); (2) toàn bộ chỉ tiêu ở **ngưỡng tối thiểu** nêu tại mục 1.2.2 được đáp ứng và **đo đạc có bằng chứng**; (3) toàn bộ 12 sản phẩm bàn giao của lộ trình tồn tại; (4) hệ thống khởi động được trên máy sạch bằng một lệnh `docker compose up`; (5) demo trực tiếp chạy được không cần kết nối Internet.

> **Trạng thái tại thời điểm viết chương này.** Các chỉ tiêu ở mục 1.2.2 là **chỉ tiêu đặt ra**. Hệ thống chạy pipeline nhận dạng **thật** với mô hình chính thức `models/best.pt` (`imgsz=640`, split v3); các chỉ tiêu phát hiện **đều đạt** (mAP@0.5 = 0,9829) và độ trễ NFR-P1 **đạt** (p95 731/780 ms). Các chỉ tiêu độ chính xác OCR **đã đo** và biển hai dòng **chưa đạt** (kết quả thật). **Kết quả đo đầy đủ đối chiếu với từng chỉ tiêu được trình bày ở Chương 6.**

## 1.3. Đối tượng và phạm vi nghiên cứu

### 1.3.1. Đối tượng nghiên cứu

Đối tượng nghiên cứu gồm ba nhóm. **(1) Biển số xe cơ giới Việt Nam** theo quy chuẩn hiện hành — Thông tư 79/2024/TT-BCA [8]<!-- bocongan_2024_tt79 --> (sửa đổi bởi TT 13/2025 [9]<!-- bocongan_2025_tt13 --> và TT 51/2025 [10]<!-- bocongan_2025_tt51 -->) về cấu trúc chuỗi ký tự, màu nền và ký hiệu seri, cùng QCVN 08:2024/BCA [11]<!-- bocongan_2024_qcvn08 --> về kích thước và hình thức vật lý; biển nền đỏ của xe quân đội nằm **ngoài phạm vi** TT 79/2024, thuộc TT 169/2021/TT-BQP [15]<!-- boquocphong_2021_tt169 -->, và chỉ được xử lý ở mức nhận biết ký hiệu. **(2) Mô hình phát hiện đối tượng họ YOLO** — cụ thể là YOLO11 [16]<!-- jocher_2024_yolo11 --> — trong vai trò bộ phát hiện vùng biển số một giai đoạn. **(3) Engine nhận dạng ký tự quang học (OCR)** không cần phân đoạn ký tự, với PaddleOCR [17]<!-- cui_2026_ppocrv5 --> giữ vai trò **baseline**, EasyOCR là ứng viên ngang hàng và Tesseract là mốc so sánh dưới, cùng bộ luật hậu xử lý ràng buộc theo vị trí. Cần nói rõ ngay: **lựa chọn engine OCR chưa được chốt ở giai đoạn thiết kế** — khảo sát ở Phase 1 kết luận không tồn tại số liệu công khai nào phân định được PaddleOCR và EasyOCR trên ảnh biển số, nên quyết định cuối cùng thuộc về benchmark do chính đồ án chạy (luận cứ ở **mục 3.3**, kết quả ở **Chương 6**).

### 1.3.2. Phạm vi trong nghiên cứu

**Bảng 1.3.** Phạm vi trong nghiên cứu

| Nhóm | Nội dung trong phạm vi |
|---|---|
| **(a) Trí tuệ nhân tạo** | Huấn luyện bộ phát hiện biển số YOLO11 trên dữ liệu Việt Nam; so sánh các biến thể kích thước (n / s / m) để chọn điểm cân bằng tốc độ – độ chính xác, kèm huấn luyện YOLO26n song song làm đối chứng (mục 3.2); **benchmark các engine OCR ứng viên** trên chính tập kiểm thử biển số Việt Nam rồi tích hợp engine thắng cuộc (đã tinh chỉnh); hậu xử lý bằng biểu thức chính quy và luật kiểm tra tính hợp lệ theo vị trí; **hỗ trợ cả biển một dòng và hai dòng**; đánh giá đầy đủ (mAP, precision, recall, F1, ma trận nhầm lẫn, đường cong loss); đo hiệu năng suy luận trên CPU |
| **(b) Dữ liệu** | Thu thập, gộp và làm sạch các bộ dữ liệu công khai; kiểm tra và sửa nhãn; loại bỏ ảnh trùng lặp; tăng cường dữ liệu; chia tập train / val / test **có kiểm soát rò rỉ dữ liệu**; thống kê và trực quan hoá |
| **(c) Phần mềm** | REST API bằng FastAPI có Swagger tự sinh; nhận dạng từ ảnh, video và khung hình thời gian thực gửi qua API (`POST /api/detect/frame`); lưu lịch sử bằng SQLite + SQLAlchemy + Alembic; giao diện web React + Vite + TypeScript + TailwindCSS gồm **ba trang** — Nhận dạng ảnh (trang chủ), Nhận dạng video, Lịch sử — sau hai đợt thu gọn phạm vi ngày 2026-07-20 đã gỡ trang Webcam rồi tới trang Tổng quan; tìm kiếm, lọc, xem chi tiết và tải về trên giao diện, còn thống kê tổng hợp phục vụ ở tầng API (`GET /api/statistics`); đóng gói bằng Docker và Docker Compose |
| **(d) Kiểm thử và tài liệu** | Unit test, integration test, kiểm thử độ chính xác AI, kiểm thử hiệu năng và chịu tải; bộ tài liệu học thuật và kỹ thuật đầy đủ |

### 1.3.3. Phạm vi ngoài nghiên cứu

Ghi rõ những gì **không làm** quan trọng ngang với ghi những gì sẽ làm: danh sách dưới đây giữ đề tài khỏi phình phạm vi và là **hàng rào bảo vệ trước câu hỏi phản biện dạng "sao không làm X"**; mỗi hạng mục đều nêu lý do, không hạng mục nào bị loại trừ vì "không kịp làm".

**Bảng 1.4.** Các hạng mục nằm ngoài phạm vi và lý do loại trừ

| # | Hạng mục loại trừ | Lý do loại trừ |
|:-:|---|---|
| 1 | Xác thực và phân quyền người dùng | Hệ thống chạy nội bộ trên `localhost` hoặc LAN (giả định A-04); **không đóng góp học thuật** cho bài toán nhận dạng |
| 2 | Đa camera / đa luồng đồng thời | Nhân đôi độ phức tạp hạ tầng (đồng bộ, hàng đợi, cân bằng tải) mà **không thêm giá trị nghiên cứu** |
| 3 | Bám vết đối tượng qua khung hình (SORT / DeepSORT) | Hệ thống dùng **gộp trùng theo chuỗi ký tự** thay thế — đơn giản hơn và đủ dùng. *Nêu ở Hướng phát triển* |
| 4 | Phân loại loại xe (ô tô / xe máy / xe tải) | **Bài toán phân lớp khác**; ngoài ra từ 01/01/2025 TT 79/2024 **đã bỏ** quy tắc dùng chữ cái seri để suy ra loại phương tiện |
| 5 | Ước lượng tốc độ, phát hiện vi phạm | Bài toán khác, cần hiệu chuẩn camera và mô hình hình học riêng |
| 6 | Nhận dạng biển số nước ngoài | Đối tượng đề tài là **biển số Việt Nam**; khối hậu xử lý xây trên quy chuẩn Việt Nam nên không tổng quát hoá được |
| 7 | Tích hợp phần cứng barie / cổng tự động | Cần thiết bị vật lý và giao thức điều khiển — **không khả thi** trong khuôn khổ đồ án |
| 8 | Cloud, multi-tenant, CI/CD production | Ngoài mục tiêu học thuật; **Docker Compose là mức triển khai đã đủ** để chứng minh khả năng tái lập |
| 9 | Ứng dụng di động | Giao diện web responsive **đã đáp ứng đủ** nhu cầu vận hành và demo |
| 10 | Huấn luyện engine OCR **từ đầu** | Dùng engine pre-trained rồi **tinh chỉnh** trên dữ liệu biển số, kết hợp hậu xử lý; **huấn luyện một kiến trúc OCR riêng từ con số không là một đồ án độc lập**. Tinh chỉnh nằm **trong** phạm vi và là bắt buộc, xem mục 2.6.3(f). *Nêu ở Hướng phát triển* |
| 11 | Suy luận thời gian thực trên GPU | Máy phát triển **không có GPU CUDA** (CON-02) — chỉ có Intel UHD Graphics 770; mọi số liệu do đó là **số liệu CPU** |

### 1.3.4. Ranh giới hệ thống

![](figures/fig-ch1-01.png)

**Hình 1.1.** Ranh giới hệ thống — phần bên trong là hệ thống bàn giao, Colab/Kaggle nằm ngoài

Colab/Kaggle nằm **ngoài** ranh giới hệ thống khi vận hành — chúng chỉ là công cụ ngoại tuyến sản xuất ra tệp trọng số `best.pt`. Hệ thống khi chạy **không phụ thuộc vào bất kỳ dịch vụ ngoài nào**, đây là hệ quả trực tiếp của tiêu chí "demo chạy được không cần Internet" ở mục 1.2.3. Với luồng thời gian thực, sau khi trang webcam được gỡ khỏi giao diện web (thu gọn phạm vi 2026-07-20), client gửi khung hình **trực tiếp vào tầng API** qua `POST /api/detect/frame` thay vì đi qua frontend.

## 1.4. Phương pháp nghiên cứu

Đề tài kết hợp **nghiên cứu lý thuyết** để chọn công nghệ và xác định khoảng trống với **nghiên cứu thực nghiệm** để xây dựng, đo đạc và đánh giá hệ thống; cả hai được tổ chức trong một **quy trình phát triển theo giai đoạn có điểm chốt**.

### 1.4.1. Nghiên cứu lý thuyết

**(a) Khảo sát tài liệu có hệ thống** theo bốn trục: tổng quan và lịch sử bài toán ALPR; so sánh các thế hệ mô hình phát hiện đối tượng họ YOLO; so sánh các engine OCR; khảo sát các bộ dữ liệu biển số công khai, đặc biệt là dữ liệu Việt Nam. Kết quả được tổng hợp thành **232 mục tài liệu tham khảo** trong `references.bib`, kèm một **bản đồ trích dẫn** ánh xạ từng khoá BibTeX tới vị trí sử dụng, bảo đảm mọi khẳng định đều truy vết được về nguồn gốc. **(b) Đối chiếu văn bản pháp quy gốc** (Thông tư của Bộ Công an và Quy chuẩn kỹ thuật quốc gia) thay vì dựa vào bài tổng hợp thứ cấp — phương pháp này đã trực tiếp phát hiện ra rằng căn cứ pháp lý mà nhiều tài liệu kỹ thuật trong nước đang dùng, TT 24/2023/TT-BCA, **đã hết hiệu lực**. **(c) Kiểm chứng đối kháng nguồn trích dẫn:** mỗi số liệu định lượng đều được truy về nguồn gốc đầu tiên, kiểm tra điều kiện đo, và **loại bỏ hoặc gắn nhãn cảnh báo** nếu không tái lập được. Quy trình này đã phát hiện và sửa **25 lỗi**, trong đó **3 lỗi mức nghiêm trọng**. Hai ví dụ cho thấy nó ảnh hưởng trực tiếp tới thiết kế hệ thống. **Mệnh đề bị bác bỏ:** giả thuyết ban đầu "biển số Việt Nam loại trừ 6 chữ cái `I J O Q R W`" đã bị **bác bỏ** — tập loại trừ đúng chỉ gồm **5 chữ** (`I J O Q W`), còn `R` **hợp lệ** ở vị trí seri thứ hai của biển xe mô tô; hệ quả thiết kế là charset huấn luyện OCR dùng **đủ A–Z + 0–9**, ràng buộc hợp lệ áp ở **tầng hậu xử lý** nơi có thể sửa và ghi log được. **Số liệu được giữ nhưng gắn cảnh báo:** benchmark chính thức trên CPU Intel Core i7-13700H cho thấy **ONNX Runtime nhanh gấp khoảng 3,73 lần PyTorch** ở phân khúc mô hình nano (104,61 ms → 28,02 ms, `imgsz` 640, FP32) [18]<!-- ultralytics_2026_openvinoexport -->; con số thời gian này được giữ làm căn cứ cho phương án giảm tải độ trễ, nhưng **cột mAP đi kèm trong bảng gốc bị loại bỏ có chủ ý** vì đo trên `coco8.yaml` — một tập chỉ **8 ảnh** — nên **không có ý nghĩa thống kê**.

### 1.4.2. Nghiên cứu thực nghiệm

**(a) Xây dựng hệ thống** theo kiến trúc phân tầng với ràng buộc cứng về tách biệt trách nhiệm (mục 1.2.2), cho phép thay thế từng thành phần độc lập. **(b) Huấn luyện có kiểm soát:** mô hình được huấn luyện trên tập dữ liệu đã làm sạch, **chia train/val/test có kiểm soát rò rỉ dữ liệu** (loại bỏ ảnh trùng lặp trước khi chia); đánh giá thực hiện trên **tập test độc lập**, không tham gia bất kỳ bước chọn siêu tham số nào. **(c) Đo đạc và công bố** theo một nguyên tắc phương pháp luận bắt buộc:

> **Mọi số liệu hiệu năng công bố đều phải kèm: model CPU, số luồng, kích thước ảnh đầu vào (`imgsz`), backend suy luận (PyTorch / ONNX / OpenVINO), và cỡ mẫu đo.**

Công bố một con số FPS mà không kèm cấu hình phần cứng là **lỗi phương pháp luận**. Nguyên tắc này cũng cấm đặt cạnh nhau các số liệu đo trên phần cứng khác nhau (ví dụ: không so cột đo trên NVIDIA A100 với cột đo trên NVIDIA T4), và cấm so sánh trực tiếp `mAP@0.5` với `mAP@0.5:0.95` vì đây là **hai định nghĩa chỉ số khác nhau**. **(d) Đánh giá tách bạch** — ba phép tách bắt buộc, mỗi phép phục vụ một câu hỏi: trước ↔ sau hậu xử lý trả lời *khối hậu xử lý đóng góp bao nhiêu điểm phần trăm* (NFR-A5 ↔ NFR-A6); biển một dòng ↔ hai dòng trả lời *hệ thống có bị điểm gãy như OpenALPR không* (NFR-A8); và theo điều kiện ảnh trả lời *hệ thống bền vững tới đâu* (NFR-A9).

### 1.4.3. Quy trình phát triển theo giai đoạn

Đề tài được thực hiện theo quy trình **12 giai đoạn (Phase 0 – Phase 11)**, tổng công sức ước lượng **77 ngày-người** (quy ước 1 ngày-người ≈ 6 giờ làm việc tập trung). Mỗi giai đoạn kết thúc bằng một **điểm chốt (milestone)** có điều kiện thông qua tường minh; **không tự động chuyển sang giai đoạn tiếp theo** khi điểm chốt chưa đạt.

**Bảng 1.5.** Mười hai giai đoạn thực hiện, công sức và điều kiện thông qua

| Phase | Tên giai đoạn | Công sức | Điểm chốt | Điều kiện thông qua |
|:---:|---|:---:|:---:|---|
| 0 | Requirement Analysis | 2 | M0 | Yêu cầu được phê duyệt, phạm vi được chốt |
| 1 | Research | 5 | M1 | Đã chọn xong công nghệ, có căn cứ trích dẫn |
| 2 | Dataset | 10 | M2 | Bộ dữ liệu đạt chất lượng, thống kê hợp lý |
| 3 | Model Training | 12 | M3 | Mô hình đạt chỉ tiêu NFR-A1, A2, A3 |
| 4 | OCR | 8 | M4 | Pipeline E2E đạt chỉ tiêu NFR-A7 |
| 5 | Backend | 8 | M5 | API hoạt động đầy đủ, Swagger đầy đủ |
| 6 | Frontend | 8 | M6 | Giao diện dùng được toàn bộ yêu cầu *Must* |
| 7 | Testing | 6 | M7 | Mọi chỉ tiêu NFR được đo và đạt ngưỡng |
| 8 | Deployment | 4 | M8 | `docker compose up` chạy được trên máy sạch |
| 9 | Documentation | 8 | M9 | Bộ tài liệu đầy đủ |
| 10 | Presentation | 4 | M10 | Slide và demo sẵn sàng bảo vệ |
| 11 | Final Package | 2 | M11 | Gói bàn giao hoàn chỉnh |
| | **Tổng** | **77** | | |

Đường găng gần như tuyến tính hoàn toàn (`P0 → P1 → … → P11`), và **ba giai đoạn nặng nhất — Dataset (10), Model Training (12) và OCR (8) — chiếm 42% tổng công sức**. Đây cũng là ba mắt xích rủi ro nhất: **P2 → P3** vì chất lượng dữ liệu quyết định **trần** độ chính xác của mô hình, nhãn xấu thì không siêu tham số nào cứu được (dấu hiệu cảnh giác: nhãn không nhất quán, ảnh trùng lặp giữa train và test); **P3 → P4** vì bounding box lệch ⇒ vùng cắt lệch ⇒ OCR sai dù OCR có hoàn hảo (dấu hiệu: `mAP@0.5:0.95` thấp dù `mAP@0.5` cao); và **P4** với **biển hai dòng** — chính là rủi ro đã được định lượng ở mục 1.1.3 (dấu hiệu: độ chính xác biển hai dòng thấp hơn biển một dòng rõ rệt). **Trạng thái tại thời điểm viết chương này:** Phase 0 và Phase 1 đã hoàn thành, chốt M0 và M1. Backend FastAPI đã chạy được và được xác minh bằng yêu cầu HTTP thật (10 endpoint phản hồi đúng, migration cơ sở dữ liệu hoàn tất, tài liệu Swagger render được); frontend đã hoàn thành và build sạch. **Hệ thống đang vận hành pipeline nhận dạng thật** với mô hình chính thức `models/best.pt` — `/health` báo `model_loaded: true`, engine `yolo:best.pt+paddleocr-PP-OCRv5-mobile`. Mô hình chính thức (YOLO11n, `imgsz=640`, split v3, 20 epoch) **đã huấn luyện xong**, đạt mAP@0.5 = 0,9829 và mAP@0.5:0.95 = 0,7834; các chỉ tiêu NFR-A4/A5/A6/A7 và NFR-P1 **đã được đo**. `models/baseline-416-v1.pt` chỉ còn giữ vai trò **mô hình đối chứng** và không đóng góp con số nào vào kết quả công bố, vì hai khiếm khuyết đã biết: huấn luyện ở `imgsz=416` trong khi chỉ tiêu đặt ở 640, và dùng split v1 vốn có rò rỉ train↔test. **Toàn bộ kết quả thực nghiệm được trình bày ở Chương 6.**

## 1.5. Ý nghĩa khoa học và thực tiễn

### 1.5.1. Ý nghĩa khoa học

**(a) Lấp một khoảng trống báo cáo có thật:** khảo sát ở Phase 1 cho thấy **chưa có công trình Việt Nam nào công bố bảng so sánh tách riêng độ chính xác giữa biển một dòng và biển hai dòng trên cùng một hệ thống**, trong khi bằng chứng từ Brazil (mục 1.1.3) cho thấy chênh lệch giữa hai bố cục có thể lên tới 48,6 điểm phần trăm [7]<!-- laroca_2022_crossdataset --> — nghĩa là **một con số tổng thể có thể che giấu hoàn toàn điểm gãy của hệ thống**. **(b) Hệ thống hoá bộ luật hậu xử lý theo cấu trúc vị trí:** các mô tả hiện có phần lớn dừng ở mức "danh sách ký tự cho phép" phẳng áp chung cho toàn chuỗi, còn đề tài mô tả có hệ thống ràng buộc **phụ thuộc vị trí** trên căn cứ pháp lý hiện hành. **(c) Đóng góp về phương pháp luận báo cáo:** đề tài trình bày tường minh một bộ quy tắc công bố số liệu (mục 1.4.2) nhằm khắc phục ba lỗi phổ biến quan sát được trong khảo sát — công bố FPS không kèm phần cứng, chỉ báo cáo mAP của khâu phát hiện mà bỏ qua độ chính xác toàn trình, và so sánh chéo các chỉ số có định nghĩa khác nhau.

### 1.5.2. Ý nghĩa thực tiễn

**(a) Một hệ thống chạy được, không phải một notebook:** sản phẩm có API, giao diện web, cơ sở dữ liệu, bộ kiểm thử và đóng gói triển khai — khởi động bằng một lệnh và hoạt động không cần Internet, do đó có thể dùng làm **nền tảng khởi đầu** cho triển khai quy mô nhỏ (bãi giữ xe cơ quan, kiểm soát ra vào khu công nghiệp, chung cư); tại thời điểm viết, tầng API, tầng nghiệp vụ và cơ sở dữ liệu đã cài đặt và chạy được, giao diện web đã hoàn thành và build sạch, bộ kiểm thử (Phase 7) và đóng gói Docker/Docker Compose (Phase 8) **đã thực hiện xong** (xem mục 1.4.3). **(b) Chạy được trên phần cứng phổ thông:** toàn bộ chỉ tiêu hiệu năng là chỉ tiêu **CPU**, mà các đơn vị triển khai quy mô nhỏ tại Việt Nam thường không có ngân sách cho máy chủ GPU, nên một hệ thống đạt độ trễ chấp nhận được trên CPU phổ thông có khả năng triển khai rộng hơn hẳn. **(c) Cập nhật căn cứ pháp lý và bảo đảm khả năng tái lập:** bộ hằng số đúng theo TT 79/2024 + QCVN 08:2024 (81 mã tỉnh hợp lệ, hai tập chữ cái seri khác nhau theo vị trí, ba mức tỉ lệ khung hình) có giá trị sử dụng lại cho các nhóm phát triển khác, và tài liệu đi kèm ghi rõ giao thức đo, tập kiểm thử, nguồn gốc dữ liệu và cấu hình phần cứng, cho phép các nhóm sau **đối chứng** kết quả.

## 1.6. Đóng góp của đề tài

### 1.6.1. Tuyên bố trung thực về mức đóng góp

> **Đề tài này không tạo ra kết quả state-of-the-art.**

Các con số vượt 99% xuất hiện trong tài liệu ALPR quốc tế là sản phẩm của những nhóm nghiên cứu chuyên nghiệp với nhiều năm tích luỹ, hạ tầng GPU quy mô lớn và các tập dữ liệu độc quyền. Một đồ án tốt nghiệp đại học, thực hiện trên máy không có GPU CUDA và trong khung thời gian giới hạn, **không đặt mục tiêu đó** — và việc tuyên bố ngược lại sẽ là thiếu trung thực học thuật. Đóng góp thực sự nằm ở sáu chỗ khác, cụ thể và kiểm chứng được, trình bày dưới đây.

### 1.6.2. Đóng góp (a) — Hệ thống hoàn chỉnh từ mô hình AI đến giao diện và triển khai

Sản phẩm là một hệ thống có **kiến trúc phần mềm**, không phải một tập script rời rạc: pipeline AI tách biệt hoàn toàn khỏi tầng API (NFR-M1, kiểm chứng được bằng phân tích import), interface trừu tượng cho phép thay thế engine OCR mà không sửa mã tầng API (NFR-M5), REST API có tài liệu tự sinh, giao diện web **ba màn hình** (thu gọn từ năm qua hai đợt gỡ trang ngày 2026-07-20 — năng lực thời gian thực và số liệu thống kê đều giữ ở tầng API), cơ sở dữ liệu có migration, bộ kiểm thử độ bao phủ ≥ 70%, và đóng gói Docker khởi động một lệnh. Khảo sát ở Phase 1 cho thấy hệ sinh thái mã nguồn mở ALPR Việt Nam chủ yếu gồm các script rời rạc **không công bố số liệu độ chính xác** và **không có kiến trúc phần mềm** — đây là **khoảng trống kỹ nghệ** chứ không phải khoảng trống thuật toán, nhưng vẫn là khoảng trống có thật.

> **Mức độ hoàn thành tại thời điểm viết.** Bốn hạng mục đầu — tách tầng AI, interface trừu tượng, REST API có tài liệu tự sinh, cơ sở dữ liệu có migration — **đã được cài đặt và xác minh bằng yêu cầu HTTP thật**. Giao diện web **đã hoàn thành** và build sạch. Chỉ tiêu độ bao phủ kiểm thử ≥ 70% **đã đạt và đã đo**: **87,7%** ở tầng nghiệp vụ theo lần đo mới nhất ngày 2026-07-20 (`docs/reports/13-refactor-result.json`; lần đo ở Phase 7 trước đó là 88,1% theo `docs/reports/07-testing-report.md`, và 42,0% trên toàn kho), với **882 test thu thập / 881 đạt / 1 xfail / 0 thất bại**. Đóng gói Docker và Docker Compose **đã hoàn thành**. Số liệu chi tiết của từng hạng mục được báo cáo ở **Chương 6**.

### 1.6.3. Đóng góp (b) — Bộ luật hậu xử lý ràng buộc theo VỊ TRÍ cho biển số Việt Nam

Bộ luật khai thác ba ràng buộc đặc thù của quy chuẩn Việt Nam: **(i) tập hợp lệ khác nhau theo từng vị trí** — mã địa phương thuộc **81 giá trị hợp lệ** chứ không phải `\d{2}` [14]<!-- thuviennhadat_2025_kyhieu34tinh -->, chữ cái seri **thứ nhất** thuộc tập **20 chữ cái** có `G` không có `R` [13]<!-- bocongan_2024_nhandienbienso -->, chữ cái seri **thứ hai** của biển xe mô tô thuộc một tập **20 chữ cái KHÁC** có `R` không có `G`, và vị trí thứ hai cũng có thể là **chữ số 1–9** (không có `0`) với biển kiểu cũ; **(ii) cấu trúc chuỗi và độ dài** theo quy chuẩn, cho phép sinh mặt nạ vị trí cho từng dạng biển; **(iii) sự cùng tồn tại của định dạng cũ và mới**, buộc bộ luật chấp nhận cả hai mà không làm hỏng dạng còn lại. Điểm mấu chốt: bộ luật sửa lỗi OCR theo **vị trí trong chuỗi chứ không theo ánh xạ hai chiều** — với cặp `O ↔ 0`, ánh xạ đúng **không** phải là hai chiều `O → 0` và `0 → O` (bởi `O` không nằm trong tập chữ cái seri hợp lệ), mà là `O → 0` tại vị trí chữ số và `0 → D` tại vị trí chữ cái.

> ⚠️ **Nói thẳng về độ lớn của đóng góp này.** Trước khi rà soát lại căn cứ pháp lý, luận điểm dự kiến của đề tài là *"khai thác bộ 20 chữ cái, loại trừ 6 chữ `I J O Q R W`"*. **Mệnh đề đó sai và đã bị bác bỏ ở Phase 1:** tập loại trừ toàn hệ thống thực sự chỉ có **5 chữ** (`I`, `J`, `O`, `Q`, `W`), chữ `R` **hợp lệ** ở vị trí seri thứ hai của biển xe mô tô. Việc sửa lại **làm yếu đi** phần đóng góp nếu tính theo tiêu chí "số ký tự loại trừ được" — không gian tìm kiếm bị thu hẹp ít hơn dự kiến ban đầu. Đổi lại, phần thực sự có giá trị chuyển sang một chỗ khác và khó hơn: ràng buộc **phụ thuộc vị trí**, chứ không phải một bộ ký tự phẳng áp cho cả chuỗi — một hệ thống dùng danh sách phẳng 20 chữ cái sẽ **sai hệ thống trên toàn bộ lớp biển xe máy có `R` ở vị trí thứ hai**, và đây mới là lỗi mà bộ luật của đề tài ngăn được. **Đóng góp này vì vậy được trình bày là *đúng đắn về mặt pháp lý và đúng cấu trúc theo vị trí*, không phải là một cải thiện lớn về không gian tìm kiếm.**

### 1.6.4. Đóng góp (c) — Đo được ĐỊNH LƯỢNG đóng góp của bước hậu xử lý

Phần lớn công trình mô tả bước hậu xử lý ở mức định tính ("có thêm bước sửa lỗi bằng regex"), không trả lời được câu hỏi *bước đó đóng góp bao nhiêu*. Đề tài giải quyết bằng một quyết định thiết kế cụ thể ở tầng dữ liệu: **lưu đồng thời cả chuỗi OCR thô và chuỗi đã sửa** cho mỗi lần nhận dạng; nhờ đó hiệu số giữa **NFR-A5** (độ chính xác biển đầy đủ *trước* hậu xử lý) và **NFR-A6** (*sau* hậu xử lý) trở thành một **con số đo được** — chính là đóng góp định lượng của khối hậu xử lý, sẽ được trình bày ở **Chương 6**.

### 1.6.5. Đóng góp (d) — Đánh giá tách riêng biển một dòng và biển hai dòng

Như đã nêu ở mục 1.5.1, đây là khoảng trống báo cáo đã xác định trong khảo sát. Yêu cầu **NFR-A8** đưa phép tách này thành nghĩa vụ báo cáo bắt buộc của đề tài, chứ không phải một phân tích tuỳ chọn; kèm theo là **NFR-A9** — báo cáo theo điều kiện ảnh, nếu bộ dữ liệu có nhãn phù hợp.

### 1.6.6. Đóng góp (e) — Công bố hiệu năng kèm cấu hình phần cứng CPU cụ thể

Mọi số liệu hiệu năng của đề tài được công bố kèm **model CPU, số luồng, kích thước ảnh đầu vào, backend suy luận và cỡ mẫu đo** (mục 1.4.2). Đây là phản ứng trực tiếp với một lỗi phổ biến quan sát được trong khảo sát: **số liệu FPS thường được công bố mà không kèm phần cứng**, khiến chúng không thể tái lập và không thể so sánh.

### 1.6.7. Đóng góp (f) — Đo trên chính ảnh biển số Việt Nam, và một khoản nợ được ghi nhận

Khảo sát ở Phase 1 xác định rằng **không tồn tại benchmark công khai nào so sánh các engine OCR trên riêng ảnh biển số xe máy Việt Nam hai dòng**; hơn nữa, hai số liệu thường được viện dẫn để chứng minh ưu thế của một engine cụ thể đã **bị bác bỏ khi truy ngược về nguồn gốc** (chi tiết ở mục 3.3) — đây là lý do lựa chọn engine OCR được để mở một cách có chủ ý ở giai đoạn thiết kế thay vì được khẳng định không căn cứ. **Phần đã làm được:** đồ án tự chạy hai phép so sánh trên chính ảnh biển số Việt Nam của mình, cùng máy và cùng ngữ liệu — **PP-OCRv5_mobile so với PP-OCRv6_medium** trên 200 vùng cắt biển số (67,0% ở 23,0 ms so với 72,5% ở 386,9 ms, mục 3.3.2), và **bộ nhận dạng gốc so với bản tinh chỉnh** trên 2.801 biển có nhãn chuỗi với bốn cấu hình (mục 5.4). Cả hai đều cho kết quả **trái với kỳ vọng ban đầu**, và đó chính là giá trị của việc tự đo: nếu chỉ đọc tài liệu rồi chọn theo con số cao nhất thì cả hai quyết định đều sẽ sai.

> ✅ **Khoản nợ này đã trả, ngày 03/08/2026.** Ma trận so sánh **PaddleOCR ↔ EasyOCR ↔ Tesseract** — đúng khoảng trống số 4 mà Chương 2 đánh giá là có giá trị khoa học cao nhất — **đã chạy trên toàn bộ 2.801 biển** (mục 3.3.3). Kết quả: PaddleOCR **68,87%**, hơn EasyOCR 54,59 điểm và hơn Tesseract 58,59 điểm. Điều này **bác bỏ** tài liệu công khai vốn nghiêng về EasyOCR, và bổ sung căn cứ độ chính xác cho một quyết định trước đó chỉ dựa trên lý do kỹ thuật. Phép đo còn cho một kết quả **trái kỳ vọng**: bước tách-rồi-ghép-ngang mua 34,92 điểm cho PaddleOCR nhưng chỉ 0,03 điểm cho Tesseract, nên nó **không** phải kỹ thuật độc lập engine — chỉ bộ luật hậu xử lý mới là.

### 1.6.8. Những gì đề tài KHÔNG tuyên bố

Để tránh mọi hiểu nhầm khi bảo vệ, bốn điều loại trừ được ghi rõ. Đề tài **không** tuyên bố vượt qua các con số độ chính xác cao nhất đã công bố trong nước, vì các con số đó được đo trên tập dữ liệu riêng không công khai nên **không tồn tại cơ sở để so sánh công bằng**. Đề tài **không** đề xuất kiến trúc mạng nơ-ron mới; nó **tích hợp và tinh chỉnh** các thành phần đã có. Đề tài **không** giải quyết các thách thức mở của lĩnh vực — nhận dạng ở độ phân giải rất thấp, tổng quát hoá xuyên tập dữ liệu, che khuất nặng — những vấn đề này được nêu ở phần **Hướng phát triển (Chương 7)**. Và mọi số liệu hiệu năng của đề tài là **số liệu CPU**, **không so sánh trực tiếp được** với các con số FPS đo trên GPU trong tài liệu tham khảo.

## 1.7. Bố cục quyển đồ án

Quyển đồ án gồm bảy chương. **Chương 1 — Giới thiệu:** bối cảnh và lý do chọn đề tài, mục tiêu dưới dạng chỉ tiêu đo được, đối tượng và phạm vi, phương pháp nghiên cứu, ý nghĩa và đóng góp. **Chương 2 — Cơ sở lý thuyết:** tổng quan bài toán ALPR và lịch sử phát triển, phân loại các hướng tiếp cận, cơ sở lý thuyết về phát hiện đối tượng họ YOLO và nhận dạng ký tự không phân đoạn, **quy chuẩn biển số Việt Nam theo TT 79/2024 và QCVN 08:2024**, các công trình liên quan và khoảng trống nghiên cứu. **Chương 3 — Khảo sát công nghệ và lựa chọn mô hình:** tiêu chí lựa chọn và **ranh giới giữa cái đã đo và cái mới chỉ khảo sát tài liệu**, chọn mô hình phát hiện trong bảy thế hệ YOLO, chọn engine OCR trong tám ứng viên kèm phép đo PP-OCRv5 mobile so với PP-OCRv6, chọn runtime suy luận trên CPU, ảnh hưởng của độ phân giải đầu vào. **Chương 4 — Phân tích và thiết kế hệ thống:** phân tích yêu cầu (34 FR, các nhóm NFR, ràng buộc, rủi ro), kiến trúc tổng thể và nguyên tắc tách tầng, thiết kế pipeline AI, khối hậu xử lý theo vị trí, cơ sở dữ liệu, API và giao diện. **Chương 5 — Xây dựng hệ thống và huấn luyện mô hình:** môi trường và công cụ, xây dựng bộ dữ liệu, huấn luyện bộ phát hiện, **tinh chỉnh bộ nhận dạng ký tự và phép đo có/không tinh chỉnh**, hiện thực tầng AI – backend – frontend, đóng gói triển khai, những chỗ cài đặt lệch khỏi thiết kế và lý do. **Chương 6 — Thực nghiệm và đánh giá:** giao thức đo, đánh giá bộ phát hiện và khối OCR, **đánh giá toàn trình tách riêng biển một dòng và hai dòng**, **đo đóng góp định lượng của khối hậu xử lý**, đo hiệu năng CPU kèm cấu hình phần cứng, đối chiếu từng chỉ tiêu NFR, phân tích ca lỗi và các mối đe doạ đến tính hợp lệ. **Chương 7 — Kết luận và hướng phát triển:** tổng kết kết quả đạt được và chưa đạt, hạn chế, hướng phát triển. Phần cuối quyển gồm **Tài liệu tham khảo** và các **Phụ lục** (bảng mã tỉnh đầy đủ, bảng tổng hợp yêu cầu chức năng, đặc tả API, hướng dẫn cài đặt và vận hành).

> **Vì sao khảo sát công nghệ được tách thành chương riêng.** Ở bản thảo trước, toàn bộ luận cứ chọn mô hình nằm gọn trong một mục cuối chương cơ sở lý thuyết — chỗ người đọc mục lục không nhìn thấy, trong khi lại là phần một hội đồng hỏi nhiều nhất. Chương 3 tồn tại để câu hỏi *"vì sao chọn YOLO11 chứ không phải YOLOv8, vì sao PaddleOCR chứ không phải EasyOCR, vì sao bản mobile của v5 chứ không phải v6"* có một chỗ trả lời tường minh — kể cả khi câu trả lời trung thực đôi lúc là *"chưa đo được"*.

## Tóm tắt chương

Chương 1 đã xác lập bốn nền tảng cho toàn bộ quyển. **Thứ nhất, lý do tồn tại của đề tài:** với 77 triệu xe máy và tỉ lệ 770 xe trên 1.000 dân [1]<!-- dantri_2024_77trieuxemay -->, phân bố phương tiện Việt Nam khiến **biển hai dòng trở thành đa số tuyệt đối** — trái ngược với giả định thiết kế của phần lớn hệ thống ALPR quốc tế; bằng chứng định lượng mạnh nhất là kết quả của OpenALPR trên tập kiểm thử cân bằng — **94,3% trên biển một dòng nhưng chỉ 45,7% trên biển hai dòng, chênh 48,6 điểm phần trăm**, đo trên bộ **RodoSol-ALPR (Brazil)** [7]<!-- laroca_2022_crossdataset --> (dẫn như *analogue*, không phải số liệu Việt Nam) — cộng thêm cấu trúc chuỗi ký tự do TT 79/2024 và QCVN 08:2024 quy định (81 mã tỉnh hợp lệ, hai tập chữ cái seri **khác nhau theo vị trí**, ba mức tỉ lệ khung hình phân tách rõ ràng), dẫn tới kết luận các giải pháp huấn luyện trên dữ liệu nước ngoài **không thể áp dụng trực tiếp**. **Thứ hai, mục tiêu đo được**, với ba chỉ tiêu then chốt: **mAP@0.5 ≥ 0,90**, **độ chính xác toàn trình ≥ 0,88**, và **độ trễ p95 ≤ 800 ms trên CPU**. **Thứ ba, ranh giới rõ ràng:** phạm vi trong gồm bốn nhóm, phạm vi ngoài gồm **11 hạng mục, mỗi hạng mục kèm lý do loại trừ tường minh**. **Thứ tư, đóng góp trung thực.** Đề tài **không tạo ra kết quả state-of-the-art** và tuyên bố điều đó ngay từ đầu. Đóng góp thực sự nằm ở sáu chỗ: (a) hệ thống hoàn chỉnh có kiến trúc phần mềm chứ không phải notebook demo; (b) bộ luật hậu xử lý **ràng buộc theo vị trí** — trình bày đúng mức là *đúng đắn về pháp lý và cấu trúc*, sau khi mệnh đề "loại trừ 6 chữ cái" đã bị bác bỏ; (c) **đo định lượng** đóng góp của bước hậu xử lý nhờ lưu song song chuỗi OCR thô và chuỗi đã sửa; (d) **đánh giá tách riêng** biển một dòng và hai dòng; (e) công bố hiệu năng **kèm cấu hình phần cứng CPU cụ thể**; và (f) **benchmark các engine OCR trên chính ảnh biển số Việt Nam** — khoảng trống mà Chương 2 đánh giá là đóng góp khoa học có giá trị nhất của đồ án. Chương 2 tiếp theo trình bày tổng quan bài toán ALPR, cơ sở lý thuyết của các thành phần được lựa chọn, quy chuẩn biển số Việt Nam, và căn cứ so sánh dẫn tới các quyết định công nghệ của đề tài.
