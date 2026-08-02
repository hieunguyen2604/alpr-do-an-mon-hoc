# CHƯƠNG 7. KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN

Năm chương trước đã đi hết một vòng: Chương 1 đặt bài toán và cam kết các chỉ tiêu định lượng, Chương 2 dựng cơ sở lý thuyết, Chương 4 thiết kế hệ thống, Chương 5 trình bày bản cài đặt đã chạy được, và Chương 6 đo hệ thống đó trên tập test độc lập rồi đối chiếu với từng chỉ tiêu. Chương kết luận này không đo lại bất kỳ chỉ tiêu nào của Chương 6. Nó có dẫn một số con số **không xuất hiện ở Chương 6** — độ chính xác của bộ nhận màu nền (mục 7.2.5), kết quả kiểm kê loại biển của tập đánh giá (mục 7.3.8) và hiệu quả của bước cứu biển hai dòng (mục 7.4.1) — vì các phép đo đó được thực hiện **sau khi Chương 6 đã chốt**; mỗi con số đều ghi kèm tệp báo cáo gốc để đối chiếu. Nhiệm vụ của chương là ba việc: **tổng kết** những gì đã thực sự làm ra, **thừa nhận trung thực** những gì chưa đạt cùng nguyên nhân đã được định vị bằng số liệu, và **chỉ ra hướng phát triển** mà bản thân kết quả thực nghiệm — chứ không phải phỏng đoán — đã vạch sẵn.

Có một nguyên tắc chi phối toàn chương, kế thừa trực tiếp từ ranh giới liêm chính học thuật đã giữ suốt Chương 6: **không tô hồng**. Hệ thống này đạt chỉ tiêu ở tầng phát hiện và tầng phần mềm, nhưng **không đạt ba chỉ tiêu độ chính xác OCR (A5, A6, A7; A4 đạt ngưỡng tối thiểu)**, và nguyên nhân nằm gần như trọn vẹn ở quần thể biển hai dòng. Một quyển đồ án trình bày thất bại đó kèm phân tích nguyên nhân đúng chỗ có giá trị hơn hẳn một quyển giấu nó sau một con số tổng đẹp. Vì vậy mục 7.3 (các hạn chế) được viết với dung lượng tương xứng với mục 7.2 (các kết quả đạt được), không bị nén thành một dòng lấy lệ.

---

## 7.1. Tổng kết công việc đã thực hiện

### 7.1.1. Điểm lại mười một giai đoạn — mỗi giai đoạn một sản phẩm thật

Đồ án được tổ chức thành mười hai giai đoạn (Phase 0 đến Phase 11), trong đó mười một giai đoạn đầu đã tạo ra sản phẩm bàn giao được, còn giai đoạn cuối (đóng gói bàn giao) phụ thuộc việc bảo vệ. Bảng dưới đây điểm lại từng giai đoạn bằng đúng một câu về **sản phẩm có thật** mà nó để lại, không phải kế hoạch của nó.

| Giai đoạn | Sản phẩm thật đã bàn giao |
|:---:|---|
| **Phase 0 — Phân tích yêu cầu** | Bộ tài liệu SRS, 34 yêu cầu chức năng và bảy nhóm yêu cầu phi chức năng, mọi chỉ tiêu đều **đo được bằng số**, chốt mốc M0. |
| **Phase 1 — Nghiên cứu** | Bảy báo cáo khảo sát và 232 mục trích dẫn BibTeX đã qua kiểm chứng đối kháng, phát hiện và sửa 25 lỗi (3 lỗi mức critical, gồm việc căn cứ pháp lý TT 24/2023/TT-BCA đã hết hiệu lực), chốt mốc M1. |
| **Phase 2 — Xây dựng bộ dữ liệu** | Bộ dữ liệu v3 gồm **15.133 ảnh** hợp nhất từ bảy bộ tải về (còn **sáu nguồn nguyên tố** sau khử trùng lặp), chia train 10.592 / val 3.027 / test 1.514 ở ngưỡng gộp trùng lặp 10. |
| **Phase 3 — Huấn luyện bộ phát hiện** | Mô hình chính thức `models/best.pt` — YOLO11n [16]<!-- jocher_2024_yolo11 -->, 2.590.035 tham số, `imgsz=640`, 20 epoch trên CPU — đạt mAP@0.5 = 0,9829 trên tập test v3. |
| **Phase 4 — Nhận dạng ký tự và hậu xử lý** | Khối OCR dựng trên PaddleOCR PP-OCRv5 mobile [17]<!-- cui_2026_ppocrv5 --> cộng bộ luật hậu xử lý theo vị trí; đo được đóng góp thuần **+11,39 điểm** của khối hậu xử lý trên 2.801 biển có nhãn chuỗi. |
| **Phase 5 — Backend** | Backend FastAPI với **10 thao tác trên 9 đường dẫn**, xác minh bằng HTTP sống (`/health` trả `model_loaded: true`), Alembic migrate xong, Swagger render đầy đủ, chốt mốc M5. |
| **Phase 6 — Frontend** | Ứng dụng React một trang, build sạch, khớp toàn bộ 10 thao tác API, phủ năm màn hình tại thời điểm chốt phase (Dashboard, Nhận dạng ảnh, Video, Webcam, Lịch sử). *Ngày 2026-07-20, giao diện được thu gọn hai đợt liên tiếp còn **ba màn hình** — Nhận dạng ảnh (trang chủ), Nhận dạng video, Lịch sử: đợt 1 gỡ trang Webcam, đợt 2 gỡ trang Tổng quan (Dashboard). Cả hai năng lực đều giữ nguyên ở tầng API (`POST /api/detect/frame`, `GET /api/statistics`, `GET /health`) và đều còn kiểm thử tích hợp; hệ quả về yêu cầu — gồm việc **FR-4.1 mức Must bị đưa ra khỏi phạm vi** — ghi ở mục 7.3.6.* |
| **Phase 7 — Kiểm thử và đo hiệu năng** | **882 test thu thập, 881 pass, 1 xfail, 0 fail, 0 skip** (lần chạy 2026-07-20, `docs/reports/13-refactor-result.json`); sau khi bổ sung test cho bộ nhận màu nền, bước cứu biển hai dòng và ba cột CSDL mới, lần chạy cuối cùng cùng ngày cho **913 thu thập, 912 pass, 1 xfail, 0 fail**; lần chạy gần nhất (2026-08-02, sau khi bổ sung test cho công tắc bỏ bước phát hiện chữ và cột `upper_char_count`) cho **1.001 thu thập, 1.000 pass, 1 xfail, 0 fail**; độ bao phủ tầng nghiệp vụ **87,7%** ở mốc `13-refactor-result.json` — số đo ở Phase 7 trước đó là 88,1% (`docs/reports/07-testing-report.md`); toàn bộ chỉ tiêu hiệu năng ngoài đường suy luận được đo và đạt. |
| **Phase 8 — Đóng gói Docker** | Hai image, stack `docker compose up` chạy được trên máy sạch, kiểm bằng `curl` từ ngoài container, chốt mốc M8. |
| **Phase 9 — Tài liệu** | Quyển đồ án — Chương 1 đến Chương 5 hoàn tất trước, Chương 6 và Chương 7 hoàn tất sau khi có `best.pt` và số liệu thực nghiệm. |
| **Phase 10 — Bảo vệ** | Khung 21 slide, poster, kịch bản demo và 56 câu hỏi phản biện dự kiến. |

> **Một lưu ý về tên gọi để tránh hiểu nhầm khi bảo vệ.** Thư mục bộ dữ liệu tên `yolo_v3` là **phiên bản thứ ba của bộ dữ liệu**, không liên quan đến kiến trúc "YOLOv3". Mô hình dùng trong toàn đồ án là **YOLO11n** [16]<!-- jocher_2024_yolo11 -->, họ YOLO thế hệ 11, biến thể nano.

Điểm cần nhấn: trong suốt Phase 5 đến Phase 7, hệ thống từng chạy bằng một pipeline giả lập (`StubPipeline`) cài đúng giao diện trừu tượng của tầng AI. Đó là lựa chọn kiến trúc có chủ đích — nó cho phép phát triển và kiểm thử toàn bộ backend, cơ sở dữ liệu và giao diện **trước khi** có trọng số, đồng thời chứng minh trên thực tế rằng ràng buộc NFR-M5 (thay được bộ nhận dạng mà không sửa mã tầng API) là khả thi. Ở trạng thái hiện tại, `StubPipeline` **đã bị đưa ra khỏi đường chạy chính**: đường chạy chính là pipeline thật với `best.pt`, và phương án lùi khi thiếu trọng số là `UnavailablePipeline` — vốn **ném lỗi** thay vì bịa ra biển số. Không một con số nào trong quyển này do stub sinh ra.

### 7.1.2. Bảng đối chiếu mục tiêu Phase 0 với kết quả thật

Bảng dưới đây đặt cạnh nhau **chỉ tiêu đã cam kết ở Phase 0** và **con số đo được thật trên `best.pt`** ở Chương 6. Nó là phiên bản cô đọng của bảng T6.7, giữ lại các chỉ tiêu có kết luận rõ ràng. Cột "Kết quả" ghi trung thực cả đạt lẫn không đạt.

**Bảng 7.1.** Đối chiếu chỉ tiêu cam kết ở Phase 0 với số đo trên `best.pt`

| Mã | Chỉ tiêu | Mục tiêu Phase 0 | Đo được (`best.pt`) | Kết quả |
|:---:|---|---:|---:|:---:|
| A1 | mAP@0.5 phát hiện | 0,90 | **0,9829** | ✅ đạt |
| A2 | mAP@0.5:0.95 phát hiện | 0,65 | **0,7834** | ✅ đạt |
| A3-P | Precision phát hiện | 0,92 | **0,9837** | ✅ đạt |
| A3-R | Recall phát hiện | 0,90 | **0,9714** | ✅ đạt |
| A4 | 1 − CER (mức ký tự) | 0,95 | **0,9454** | 🟡 đạt ngưỡng tối thiểu (0,92) |
| A5 | Chuỗi trước hậu xử lý | 0,85 | **0,6373** | ❌ không đạt |
| A6 | Chuỗi sau hậu xử lý | 0,90 | **0,7512** | ❌ không đạt |
| A6−A5 | Đóng góp hậu xử lý (điểm %) | — | **+11,39** | (đóng góp thuần dương) |
| A7 | Độ chính xác E2E toàn trình | 0,88 | **0,5552** | ❌ không đạt* |
| A8 | Chênh lệch layout, phát hiện (điểm %) | — | **2,09** | (rất nhỏ) |
| P1 | Độ trễ E2E một ảnh, p95 (ms) | ≤ 800 | **1.143,10** | 🟡 đạt ngưỡng tối thiểu (1.500) |
| P4 | Thời gian nạp mô hình (s) | ≤ 15 | **6,41** | ✅ đạt |
| P5 | Overhead API, p95 (ms) | ≤ 50 | **19,01** | ✅ đạt |
| P6 | Truy vấn 10.000 bản ghi, p95 (ms) | ≤ 500 | **18,71** | ✅ đạt |
| P7a | RSS pipeline (GB) | ≤ 2 | **0,759** | ✅ đạt |
| P7b | RSS máy chủ backend (GB) | ≤ 2 | **0,806** | ✅ đạt |
| R4 | Tỉ lệ thành công khi chạy liên tục | ≥ 99% | **100%** (2.028 yêu cầu, soak 15 phút) | ✅ đạt |
| SC1 | Số yêu cầu đồng thời ổn định | ≥ 5 | **10** | ✅ đạt |
| M2 | Độ bao phủ test tầng nghiệp vụ | — | **87,7%** đo 2026-07-20 (881/882 pass, 1 xfail); lần chạy cuối cùng cùng ngày: 912/913 pass; trước đó Phase 7 đo 88,1% | (tham chiếu) |

\* A7 = 0,5552 phải đọc như **cận dưới bi quan** — nó đo trên ảnh crop biển số (ngoài phân bố huấn luyện của bộ phát hiện), khiến tỉ lệ bỏ sót ở tầng phát hiện bị thổi phồng; xem phân tích ở mục 7.3.1.

Đọc bảng theo hàng dọc cho thấy một hình mẫu rõ ràng, và nó chính là câu chuyện của đồ án: **mọi chỉ tiêu phát hiện, độ tin cậy và khả năng chịu tải đều đạt, thường với biên rộng; mọi chỉ tiêu độ chính xác OCR chuỗi đầy đủ đều không đạt.** Vạch ngăn giữa "đạt" và "không đạt" trùng khít với vạch ngăn giữa tầng phát hiện và tầng nhận dạng ký tự. Đây không phải trùng hợp — nó là kết luận trung tâm mà Chương 6 chứng minh và Chương 7 khai thác để định hướng phát triển.

**Nhóm hiệu năng nằm ngoài hình mẫu đó và phải nói riêng.** Nó tách làm hai: mọi chỉ tiêu *ngoài* đường xử lý ảnh — nạp mô hình, overhead API, truy vấn cơ sở dữ liệu, bộ nhớ, độ ổn định khi chạy dài — đều đạt với biên rất rộng; nhưng hai chỉ tiêu *trên* chính đường ấy thì không: **NFR-P1 chỉ đạt ngưỡng tối thiểu** (p95 = 1.143,10 ms, mục tiêu 800 ms) và **NFR-P2 trượt cả sàn** (2,379 FPS, sàn 3). Cả hai cùng một nguyên nhân — đuôi độ trễ của bậc thang thử-lại — và cùng một đánh đổi có chủ ý: 34 biển đọc thêm. Nói "mọi chỉ tiêu hiệu năng đều đạt" sẽ là một khẳng định sai.

Ba trong bốn chỉ tiêu từng bỏ trống đã được đo ngày **02/08/2026** ([33-runtime-nfr.json](../reports/33-runtime-nfr.json)): **NFR-P3 đạt** (0,746× thời gian thực), **NFR-R5 đạt** (0/9.031 bản ghi mất sau khởi động lại), còn **NFR-P2 không đạt** — 2,379 FPS, trượt cả sàn 3 FPS. Chỉ còn **NFR-A9** (tách theo điều kiện ảnh) là chưa đo, và nó thuộc loại *thiếu điều kiện* chứ không phải *chưa tới lượt*: không bộ dữ liệu nào của đồ án có nhãn điều kiện ảnh. Phân biệt hai loại đó được giữ nguyên tinh thần của mục 6.9.2; chi tiết ở mục 7.3.5.

---

## 7.2. Các kết quả đạt được

### 7.2.1. Một hệ thống hoàn chỉnh, chạy được, xác minh bằng HTTP thật

Sản phẩm đầu tiên và bao trùm nhất không phải một con số mà là **một hệ thống phần mềm hoàn chỉnh, đầu-cuối, thực sự chạy**. Bốn tầng của nó — backend FastAPI, frontend React, pipeline AI (`ALPRPipeline`) và lớp dữ liệu SQLite/SQLAlchemy — được đóng gói bằng Docker và khởi động bằng một lệnh `docker compose up` trên máy sạch, không cần kết nối Internet khi vận hành.

Điều làm cho tuyên bố này khác một lời hứa là nó **kiểm chứng được**, và đã được kiểm chứng: 10 thao tác API (trên 9 đường dẫn) phản hồi đúng qua HTTP sống; `/health` báo `model_loaded: true` với engine thật `yolo:best.pt + paddleocr-PP-OCRv5-mobile`; Alembic migrate hoàn tất; Swagger render đầy đủ; và stack Docker được kiểm bằng `curl` từ **ngoài** container chứ không chỉ bên trong. Bốn nguyên tắc kiến trúc đặt ra ở Chương 4 — không trộn mã AI với mã API, thay thế được thành phần, không hard-code đường dẫn, chạy được không cần GPU — không dừng ở khẩu hiệu: ràng buộc "tầng AI không có mũi tên đi lên" kiểm chứng được bằng một lệnh `grep`, và khả năng thay thế bộ nhận dạng (NFR-M5) đã được chứng minh bằng chính sự tồn tại của `StubPipeline` và `UnavailablePipeline` như các bản cài thay thế của cùng một giao diện.

Ở góc độ kỹ nghệ, đây là đóng góp vững nhất của đồ án: một hệ thống ALPR tái lập được, chạy hoàn toàn trên CPU, khởi động một lệnh, không phụ thuộc dịch vụ ngoài — phù hợp bối cảnh triển khai nội bộ mà đề tài nhắm tới.

### 7.2.2. Bộ phát hiện đạt toàn bộ chỉ tiêu với biên rộng

Trên tập test v3 (1.514 ảnh, 1.611 đối tượng nhãn thật), bộ phát hiện YOLO11n [16]<!-- jocher_2024_yolo11 --> vượt **cả bốn** chỉ tiêu phát hiện, và vượt *mục tiêu* chứ không chỉ *ngưỡng tối thiểu*:

- mAP@0.5 = **0,9829** (mục tiêu 0,90);
- mAP@0.5:0.95 = **0,7834** (mục tiêu 0,65) — đây là chỉ số quyết định vì nó khắt khe với chất lượng định vị hộp, và biên vượt vẫn rất rộng;
- Precision = **0,9837**, Recall = **0,9714**, F1 = **0,9775**.

Hai kết quả phụ củng cố độ tin cậy của con số tổng. Thứ nhất, chênh lệch giữa hai layout ở tầng phát hiện chỉ **2,09 điểm** mAP@0.5 (biển một dòng 0,9884 so với biển hai dòng 0,9675) — xác nhận rằng *việc định vị box* gần như không phụ thuộc layout, một điểm quan trọng vì nó tách bạch trách nhiệm: nếu độ chính xác toàn trình kém trên biển hai dòng thì lỗi **không** nằm ở khâu phát hiện. Thứ hai, khi tách theo dải kích thước (bảng T6.4c), mô hình phơi bày trung thực điểm yếu duy nhất của mình: dải đối tượng "rất nhỏ" (dưới 0,5% diện tích ảnh) chỉ đạt mAP@0.5 = 0,8553 — hệ quả đo được của việc bộ dữ liệu không đạt tiêu chí về tỉ lệ đối tượng nhỏ, được báo cáo tách bạch thay vì che sau một con số tổng.

Cần đọc con số cao này kèm điều kiện đã nêu ở Chương 6: đây là bài toán **một lớp** (chỉ phát hiện "biển số"), nên mAP@0.5 cao là điều bình thường và không nên bị hiểu là thành tựu vượt trội. Giá trị thật nằm ở chỗ mô hình đạt mức đó một cách nhất quán trên cả hai layout và ở độ phân giải 640 đúng chỉ tiêu.

### 7.2.3. Đo được đóng góp định lượng của khối hậu xử lý

Đây là **đóng góp khoa học riêng thứ nhất** của đồ án. Phần lớn công trình ALPR chỉ mô tả bước hậu xử lý một cách định tính ("có thêm một bước sửa lỗi bằng regex"), hiếm khi lượng hoá xem bước đó đóng góp bao nhiêu. Đồ án này đo tách bạch, hai lần trên cùng 2.801 biển có nhãn chuỗi:

- Độ chính xác chuỗi đầy đủ **trước** hậu xử lý (A5) = 0,6373;
- Độ chính xác chuỗi đầy đủ **sau** hậu xử lý (A6) = 0,7512;
- Hiệu số **A6 − A5 = +11,39 điểm phần trăm** — chính là đóng góp thuần của khối hậu xử lý theo luật.

Quan trọng hơn con số là **hình dạng** của đóng góp: bộ luật sửa đúng **319 biển** và làm hỏng **0 biển**, và đóng góp ấy dồn gần như trọn vẹn vào biển hai dòng (**+13,97 điểm**, so với +1,23 điểm ở biển một dòng) — tức đúng nơi tầng nhận dạng yếu nhất. Đây là một cải thiện thuần một chiều — bằng chứng rằng bộ luật đủ bảo thủ để không tự tạo ra lỗi mới, đúng như thiết kế "sửa lỗi theo vị trí, có vùng cấm sửa" ở Chương 4. Đóng góp bị chặn ở mức nhỏ **không phải vì luật kém**, mà vì nút thắt độ chính xác nằm ở tầng OCR — nơi luật, vốn chỉ sửa được nhầm ký tự lẻ tẻ ở đúng vị trí, về bản chất không với tới được các chuỗi sai nhiều ký tự do engine đọc hụt cả cụm. Việc đóng góp là dương và không rủi ro, dù nhỏ, là một kết quả có giá trị tự thân: nó xác nhận thiết kế hậu xử lý đúng đắn về nguyên lý, và định vị chính xác rằng cải thiện lớn phải đến từ tầng khác.

### 7.2.4. Đo được rủi ro R-04 bằng số liệu Việt Nam thật

Đây là **đóng góp khoa học riêng thứ hai**, và có lẽ là đóng góp thực nghiệm đáng giá nhất. Rủi ro R-04 — "pipeline OCR dựng sẵn gãy trên biển hai dòng" — được xác định từ Phase 0 như một rủi ro *định tính*. Đồ án này biến nó thành một con số *đo được trên dữ liệu Việt Nam*. Tách theo layout (bảng T6.5c):

| Chỉ số | Biển một dòng (567 mẫu) | Biển hai dòng (2.234 mẫu) | Chênh lệch |
|---|---:|---:|---:|
| 1 − CER (mức ký tự) | 0,9925 | 0,9344 | 5,81 điểm |
| Chuỗi trước hậu xử lý (A5) | 0,9418 | 0,5600 | 38,18 điểm |
| Chuỗi sau hậu xử lý (A6) | 0,9541 | 0,6996 | **25,45 điểm** |

Biển **một dòng về cơ bản đã giải xong**: A6 = 0,9541 vượt mục tiêu 0,90, và 1 − CER = 0,9925. Toàn bộ khoảng thiếu của con số tổng nằm ở biển **hai dòng**, vốn chiếm **79,8%** tập có nhãn chuỗi — một tỉ lệ phản ánh trực tiếp mật độ xe máy áp đảo trong giao thông Việt Nam, nơi có tới 77 triệu xe máy [1]<!-- dantri_2024_77trieuxemay -->. Nói cách khác, quần thể khó nhất về mặt kỹ thuật lại là quần thể phổ biến nhất về mặt thực tế.

Chênh lệch **25,45 điểm** A6 giữa hai layout là một phát hiện có định vị rõ ràng, không phải một thất bại mơ hồ. Nó **cùng bậc độ lớn** với mốc tham chiếu quốc tế: Laroca và cộng sự (VISAPP 2022) đo chênh lệch **48,6 điểm** giữa biển một dòng (94,3%) và biển hai dòng (45,7%) trên bộ dữ liệu **RodoSol-ALPR của Brazil** [7]<!-- laroca_2022_crossdataset -->.

> **Cảnh báo trích dẫn bắt buộc, lặp lại theo đúng quy tắc của Chương 6.** Cặp số 94,3% / 45,7% và chênh lệch 48,6 điểm đo trên **RodoSol-ALPR (Brazil)** [7]<!-- laroca_2022_crossdataset -->, **không phải** số liệu Việt Nam. Nó chỉ được dùng như một *analogue định lượng* về độ khó tương đối của biển hai dòng, không bao giờ như một mốc chuẩn mà hệ thống này phải vượt. Con số 25,45 điểm mới là con số đo trên dữ liệu Việt Nam của đồ án.

Giá trị học thuật ở đây là lấp một khoảng trống cụ thể: chưa có nghiên cứu biển số Việt Nam công khai nào công bố hai con số một dòng / hai dòng **tách bạch trên cùng một hệ thống**. Kết luận rút ra — biển hai dòng là một *đặc tính có cấu trúc của bài toán* chứ không phải một lỗi cài đặt sửa nhanh được — đặt nền cho hướng phát triển trọng tâm ở mục 7.4.1, và cũng nhất quán với dòng nghiên cứu quốc tế coi tính độc lập với layout là một yêu cầu thiết kế riêng chứ không phải hệ quả miễn phí [23]<!-- laroca_2021_layout -->.

### 7.2.5. Bộ nhận màu nền biển đạt 97,89% — một nguồn bằng chứng mà chuỗi ký tự không thể mang

Đây là **đóng góp kỹ thuật riêng thứ ba**, và nó khác hai đóng góp trên ở chỗ: hai đóng góp kia lượng hoá một thứ đã tồn tại, còn đóng góp này **bổ sung một năng lực mà hệ thống trước đó không có**.

Xuất phát điểm là một giới hạn có tính nguyên tắc, không phải một lỗi cài đặt. Theo Thông tư 79/2024/TT-BCA, biển vàng của xe kinh doanh vận tải mang **đúng cùng một bố cục ký tự** với biển trắng của xe cá nhân: `29E-015.66` là chuỗi hợp lệ cho cả hai. Không lượng công sức nào bỏ vào biểu thức chính quy phân biệt được hai loại xe đó, vì **khác biệt không nằm trong chuỗi**. Ngược lại, biển ngoại giao có nền trắng như biển cá nhân, nên màu cũng không đủ — chỉ chuỗi mới nhận ra nó. Hai nguồn bằng chứng **bù trừ cho nhau**, và chỉ *cặp* (chuỗi, màu) mới định danh được loại phương tiện.

Mô-đun `ai/inference/plate_color.py` đọc màu nền bằng biểu đồ HSV trên **vùng giữa ảnh cắt** (18% mỗi biên bị loại, vì khung phát hiện thường lỏng và một chiếc xe sơn đỏ phía sau biển trắng sẽ thắng phiếu nếu lấy cả rìa), và trả `unknown` thay vì đoán khi không dải màu nào chiếm đủ 30% vùng lấy mẫu. Kết quả đo trên bộ `nguyenluanai/license-plate-color` v4 (CC BY 4.0) — bộ dữ liệu mà **bộ phân loại chưa từng được hiệu chỉnh theo**, nên đây là phép đo ngoài dữ liệu hiệu chỉnh:

| Lớp nhãn người gán | Số ảnh | Độ chính xác |
|---|---:|---:|
| Biển vàng | 694 | **98,56%** |
| Biển trắng | 808 | **97,40%** |
| Biển xanh | 63 | **96,83%** |
| **Tổng** | **1.565** | **97,89%** |

Nguồn: `docs/reports/19-color-accuracy.json`. Có 542 ảnh bị loại khỏi phép tính — toàn bộ lớp `bien_unknown` của bộ dữ liệu, gồm ảnh chụp đêm hoặc hồng ngoại bị lỗi cân bằng trắng, ám tím, mà **chính người gán nhãn cũng không đọc được màu nền**; chấm điểm trên các ảnh không có đáp án đúng là vô nghĩa.

Điều đáng nói về mặt thiết kế không phải con số 97,89% mà là **ràng buộc an toàn của phép hợp nhất hai nguồn**. Biển xanh là trường hợp duy nhất mà chuỗi ký tự bó tay hoàn toàn: với `80A12345`, bộ luật trả về **bốn ứng viên ngang nhau** và tự đánh dấu là nhập nhằng. Ở đúng và chỉ đúng tình huống đó, màu được phép **nâng cấp một ứng viên mà chuỗi đã coi là hợp lý** — và không hơn. Màu không thể bịa ra một họ biển mà bộ luật ký tự đã bác bỏ, nên **một biển quân đội bị đọc nhầm màu thì vẫn là biển quân đội**. Điều tệ nhất một màu sai có thể gây ra là chọn nhầm phần tử trong một tập mà chính chuỗi đã tuyên bố là ngang khả năng.

Cùng đợt này, hai thông tin vốn **đã được tính ra rồi bị vứt đi** trước khi tới cơ sở dữ liệu được giữ lại: kết quả phân loại họ biển (chín giá trị `PlateKind`) và chuỗi hiển thị đúng định dạng vật lý (`29E-015.66`). Hệ quả trực tiếp là chữa được một phát biểu sai của giao diện: một biển đỏ quân đội đọc đúng ở độ tin cậy 0,999 từng bị hiển thị là **"Sai định dạng biển số"** — biển quân đội là biển hợp lệ, chỉ nằm ngoài hệ đăng ký dân sự.

Hạn chế bắt buộc phải nêu kèm: bộ dữ liệu dùng để đo **không chứa biển đỏ và không chứa biển ngoại giao**, nên hai nhánh đó của bộ phân loại chưa có số đo. Xem mục 7.3.8.

### 7.2.6. Một quy trình đánh giá có kiểm chứng — bản thân tính trung thực là một kết quả

Đóng góp cuối trong nhóm này không phải một con số cao mà là **cách các con số được kiểm tra**. Trong quá trình đánh giá, năm lần quy trình tự bắt được lỗi hoặc ngộ nhận của chính nó, và cả năm đều được ghi lại thay vì che đi:

**(1) Phát hiện và sửa rò rỉ dữ liệu train↔test.** Bước khử trùng lặp ban đầu chạy ở ngưỡng gộp 5; kiểm tra lại phát hiện split cũ có hàng nghìn cặp ảnh gần trùng vắt qua ranh giới train↔test. Ngưỡng gộp được nâng lên 10 và bộ dữ liệu chia lại thành v3. Quan trọng hơn, việc rò rỉ được **đo ở nhiều ngưỡng cao hơn ngưỡng gộp** để phơi bày phần tồn dư thay vì tuyên bố "đã sạch" (xem tiếp mục 7.3.2).

**(2) Phát hiện một lập luận vòng tròn trong chính phép kiểm chứng rò rỉ.** Ở ngưỡng Hamming 10, tập v3 cho **0 cặp** vắt split. Thoạt nhìn đây có vẻ là bằng chứng "tập test sạch". Nhưng đó là một **hệ quả định nghĩa**, không phải một phát hiện thực nghiệm: v3 được *khử trùng lặp ở đúng ngưỡng 10*, nên đo lại rò rỉ ở ngưỡng 10 chắc chắn ra 0 — con số này không mang thông tin. Chỉ các ngưỡng **cao hơn** ngưỡng gộp (12, 15, 20) mới mang thông tin mới. Nhận ra và ghi rõ vòng lặp lý luận này quan trọng vì nó ngăn một tuyên bố sai ("đã kiểm chứng là sạch") lọt vào chương thực nghiệm.

**(3) Phát hiện phash chỉ nhận giá trị khoảng cách chẵn, khiến ngưỡng lẻ vô nghĩa.** Băm tri giác `phash` 64 bit trong cài đặt này sinh ra hash có **đúng 32 bit bằng 1** (so với trung vị). Với hai hash cùng có 32 bit 1, khoảng cách Hamming giữa chúng luôn bằng $64 - 2k$ với $k$ là số bit 1 trùng vị trí — tức **luôn là số chẵn**. Hệ quả: đặt ngưỡng lẻ (ví dụ 11 hay 13) cho kết quả **y hệt** ngưỡng chẵn liền trước, nên mọi ngưỡng lẻ là vô nghĩa và không được đưa vào bảng đo. Điều này cũng giải thích vì sao khoảng cách nhỏ nhất quan sát được (12) là một số chẵn — đó là tất yếu toán học của cách dựng hash, không phải một đặc điểm của dữ liệu.

**(4) Phát hiện bộ đo độ chính xác OCR không đi qua đường mã của sản phẩm.** Đây là phát hiện có hệ quả rộng nhất trong cả năm, vì nó không nói về một con số cụ thể mà về **toàn bộ cách đồ án đo chính mình**. Script `ai/evaluation/ocr_accuracy.py` — nơi sinh ra các chỉ số NFR-A4 đến A7 công bố ở Chương 6 — gọi thẳng bộ nhận dạng và bộ chuẩn hoá, **không dựng `ALPRPipeline`**. Hệ quả logic: mọi logic đặt ở tầng điều phối đều **vô hình** đối với các con số công bố. Phát hiện xảy ra khi cài đặt bước cứu biển hai dòng (mục 5.5.5f): nếu bước cứu được viết như một phương thức riêng của pipeline — cách viết tự nhiên nhất — thì chương thực nghiệm sẽ đo một đường mã mà sản phẩm thật **không chạy**, và sẽ báo cáo một hệ thống kém hơn hệ thống đang giao. Bản sửa là tách bước cứu thành hai hàm tự do dùng chung (`should_rescue_two_line`, `rescue_two_line_upper` trong `ai/inference/pipeline.py`) để cả hai bên gọi cùng một đường. Điều cần nhấn mạnh khi bảo vệ: khoảng cách này **không gây lỗi, không sinh cảnh báo** và không bị bộ kiểm thử kiến trúc nào bắt được — nó chỉ lộ ra khi có người đối chiếu đường mã của bộ đo với đường mã của sản phẩm. Ranh giới giữa *hệ thống* và *phép đo hệ thống* vì vậy cũng là một ranh giới kiến trúc, và hiện chưa có cơ chế tự động nào canh giữ nó.

**(5) Một giả thuyết sửa lỗi hợp lý bị chính dữ liệu bác bỏ.** Khi biển `29E-015.66` bị đọc thành `015.66`, giả thuyết hiển nhiên là bỏ phép ghép hai nửa và đọc riêng từng nửa rồi nối chuỗi. Giả thuyết này đủ hợp lý để không thể bác bỏ bằng lập luận, nên nó được đo trên 200 biển hai dòng: cách đọc riêng đạt **3,5%** so với **64,5%** của cách ghép hiện hành — thắng ở 0/200 ảnh (`docs/reports/15-two-line-ab.json`). Nguyên nhân hoá ra nằm ở chính chi tiết thiết kế tưởng như không liên quan: hai nửa được cắt **chồng lấn có chủ ý**, nên khi đọc rời, dải chồng lấn bị đọc hai lần và sinh ký tự rác (`84G122593` ra thành `84-G124E009.01225.93`). Phép bác bỏ vì thế mang lại nhiều hơn một câu trả lời "không": nó phơi bày rằng phép ghép ngang còn giữ một vai trò thứ hai chưa từng được nhận ra — **trao cho bộ phát hiện văn bản cơ hội loại bỏ vùng chồng lấn**. Bản sửa cuối cùng do đó *giữ nguyên* thiết kế cũ và chỉ vá điểm mù của nó, với cổng kích hoạt đặt sau kiểm tra định dạng nên **không thể làm giảm độ chính xác về mặt cấu trúc** — đo trên 900 biển qua hai mẫu độc lập: 0 ca hỏng.

Ngoài năm lần trên, quy trình còn **bác bỏ một con số độ trễ cũ** (mục 7.3.4 và 6.6.1): báo cáo trước đây từng ghi p95 = 5.857 ms và kết luận NFR-P1 không đạt; truy nguyên cho thấy phép đo đó bị nhiễm tranh chấp CPU (một tiến trình huấn luyện chạy song song) và đo trên sai checkpoint có lỗi crop, nên đã bị loại và đo lại đúng cách. Sáu sự việc này gộp lại tạo thành một đóng góp phương pháp luận: **một chương đánh giá chỉ trưng ra các con số đẹp và không kể lại lần nào nó tự nghi ngờ chính mình là một chương đã tự tước bỏ khả năng bị kiểm chứng.**

---

## 7.3. Các hạn chế của đồ án

Mục này là phần quan trọng nhất của chương, và được viết theo nguyên tắc của mục 6.9.3: **nêu hạn chế, đánh giá mức nghiêm trọng, nói rõ đã làm gì để giảm thiểu — kể cả khi câu trả lời là "chưa làm được gì".**

### 7.3.1. Hạn chế lớn nhất: OCR biển hai dòng còn yếu, kéo E2E chưa đạt

*Mức nghiêm trọng: cao. Đây là hạn chế trung tâm của toàn đồ án.*

Ba chỉ tiêu độ chính xác OCR không đạt (NFR-A4 đã vượt ngưỡng tối thiểu ở lượt đo 28/07):

- NFR-A5 (chuỗi trước hậu xử lý) = **0,6373**, thiếu 16,27 điểm so với ngưỡng 0,80;
- NFR-A6 (chuỗi sau hậu xử lý) = **0,7512**, thiếu 9,88 điểm so với ngưỡng 0,85;
- NFR-A7 (E2E toàn trình) = **0,5552**, thiếu 26,48 điểm so với ngưỡng 0,82.

NFR-A4 (1 − CER) = **0,9454** vượt ngưỡng tối thiểu 0,92 nhưng vẫn dưới mục tiêu 0,95.

Điều phải nói thẳng — và cũng là điều làm cho hạn chế này *có thể hành động được* thay vì mơ hồ — là **nguyên nhân đã được định vị bằng số liệu, và nó nằm ở tầng OCR, không phải tầng hậu xử lý**. Ba bằng chứng độc lập cùng chỉ về một chỗ:

1. **Tách theo layout** (T6.5c): trên biển một dòng, hệ thống đạt hoặc vượt ngưỡng (A6 = 0,9541); toàn bộ khoảng thiếu nằm ở biển hai dòng (A6 = 0,6996). Vì biển hai dòng chiếm 79,8% tập, con số tổng bị quần thể này chi phối.
2. **Phân tích lỗi** (T6.8): trong 445 ca nhầm ký tự, **428 ca** thuộc biển hai dòng; trong 73 ca thiếu ký tự, **cả 73 ca** đều thuộc biển hai dòng — không một ngoại lệ. Lỗi tập trung gần như tuyệt đối ở một layout.
3. **Đóng góp hậu xử lý bị chặn trên** (T6.5b): khối luật thêm được +11,39 điểm — không nhỏ — nhưng vẫn không đủ, vì phần lỗi còn lại đã dịch sang dạng **đọc hụt ký tự** (ký tự bị xoá chiếm 56,8% toàn bộ lỗi), mà một ký tự chưa từng được đọc ra thì **về nguyên tắc** không luật nào phục hồi được. Nếu lỗi là ở hậu xử lý, tăng luật sẽ cứu được; thực tế là không, vì lỗi ở tầng dưới.

Kết luận: **hướng khắc phục bắt buộc nằm ở tầng nhận dạng — huấn luyện hoặc thay mô hình OCR chuyên cho biển số hai dòng — chứ không ở tầng hậu xử lý** (triển khai ở mục 7.4.1). Việc trút thêm luật vào `plate_rules.py` sẽ không đụng đến nút thắt thật.

**Một cảnh báo hiệu lực về con số A7 = 0,5552.** Con số này đo trên ảnh **crop biển số** — ngoài phân bố huấn luyện của bộ phát hiện — nên tỉ lệ bỏ sót 11,96% bị thổi phồng và A7 phải đọc như **cận dưới bi quan**, không phải ước lượng điểm. Lập luận và số liệu đầy đủ ở **mục 6.5.5**; đo A7 đúng cách đòi hỏi một tập test hiện trường có nhãn chuỗi, việc chưa làm được (mục 7.4.3).

### 7.3.2. Rò rỉ dữ liệu tồn dư không khử được bằng băm tri giác

*Mức nghiêm trọng: cao.*

Như mục 7.2.6 đã nêu, bước khử trùng lặp đã chạy đúng đặc tả ở ngưỡng gộp 10. Nhưng điều đó **không** đồng nghĩa tập test tách sạch khỏi tập train. Đo ở các ngưỡng cao hơn ngưỡng gộp phơi bày phần tồn dư có thật, đo được: ngay ngoài vùng bảo vệ của ngưỡng 10, tại ngưỡng Hamming **12** vẫn còn **791 cặp** ảnh gần trùng train↔test, và tại ngưỡng **15** là **3.529 cặp**. Nghĩa là tập test **không** hoàn toàn độc lập với tập train ở mức bố cục sáng-tối.

Nghiêm trọng hơn là loại rò rỉ mà **không ngưỡng phash nào bắt được**: hai ảnh của *cùng một chiếc xe* chụp ở góc khác nhau, hoặc hai khung hình cách nhau vài giây trong cùng một video, mang **cùng một biển số** nhưng có khoảng cách Hamming lớn. Đây là rò rỉ ở mức **ngữ nghĩa**, và phash — vốn chỉ đo tương đồng bố cục — mù trước nó. Chính vì thế, kết quả phash thấp ở ngưỡng gộp **không chứng minh** tập test độc lập.

*Biện pháp giảm thiểu đã áp dụng:* nâng ngưỡng gộp từ 5 lên 10, và đo rò rỉ ở nhiều ngưỡng cao hơn để phơi bày phần tồn dư thay vì che nó. *Biện pháp triệt để chưa áp dụng được:* chia split **theo nhóm biển số** (mọi ảnh của cùng một biển phải nằm cùng một phía của split) — bất khả thi ở hiện tại vì phần lớn corpus thiếu nhãn chuỗi để nhóm. **Hệ quả bắt buộc phải nêu khi bảo vệ: mọi chỉ số ở tầng phát hiện và OCR phải được coi là cận trên lạc quan.**

### 7.3.3. Tập test không xuyên bộ dữ liệu, nên mAP lạc quan hơn khi triển khai

*Mức nghiêm trọng: cao.*

Tập train và tập test được lấy từ **cùng sáu nguồn nguyên tố** đã hợp nhất. Thiết lập này đo được năng lực tổng quát hoá *trong phân bố*, nhưng **không** đo được năng lực tổng quát hoá *xuyên phân bố* — vốn mới là thứ quyết định khi triển khai trên camera mới, địa điểm mới, điều kiện chiếu sáng mới. Tài liệu đã chỉ ra rằng độ chính xác ALPR sụt giảm đáng kể khi đánh giá xuyên bộ dữ liệu [7]<!-- laroca_2022_crossdataset -->. Do đó con số mAP@0.5 = 0,9829 gần như chắc chắn **lạc quan hơn** hiệu năng thực tế khi gặp phân bố ảnh chưa từng thấy.

*Biện pháp giảm thiểu:* không có trong khuôn khổ đồ án. Cách đúng là giữ lại một nguồn hoàn toàn không dùng để huấn luyện làm tập test xuyên bộ; điều này chưa thực hiện và chuyển thành hướng phát triển ở mục 7.4.2.

### 7.3.4. Độ trễ — đạt ngưỡng tối thiểu, và mức vượt mục tiêu là một đánh đổi có chủ ý

*Kết luận: NFR-P1 đạt ngưỡng tối thiểu, không đạt mục tiêu. Ghi lại đầy đủ vì con số này đã đi qua hai lần đảo chiều, và cả hai lần đều có nguyên nhân xác định được.*

NFR-P1 **đạt ngưỡng tối thiểu nhưng không đạt mục tiêu**: độ trễ E2E một ảnh, p95 = **1.143,10 ms** — dưới sàn 1.500 ms, nhưng vượt mục tiêu 800 ms 1,43 lần. Trung vị chỉ **405,77 ms**. Đo in-process trên `best.pt`, cấu hình giao hàng, máy rảnh (CPU idle ~5%, không có tiến trình huấn luyện chạy song song), warmup rồi đo 100 ảnh test v3.

**Đây là một thoái lui có chủ ý, đã định lượng, và đổi lấy độ chính xác.** Nguyên nhân là bậc thang thử-lại cho biển nghiêng/méo: tắt hẳn nó đưa p95 về **866,3 ms**, tức toàn bộ +277 ms là của nó, đổi lại 34 biển đọc được thêm (+0,75 điểm A6). Vì bậc thang chỉ chạy **sau khi lần đọc đầu thất bại**, nó không chạm vào trường hợp thường — trung vị thậm chí giảm nhẹ so với lượt đo trước. Toàn bộ chi phí dồn vào đuôi phân phối, đúng nơi tập trung những ảnh mà hệ thống phải làm việc nhiều lần mới đọc được. Phân tích đầy đủ ở **mục 6.5.7** và **6.6.1**.

**Một quyết định đã được đưa ra để giữ chỉ tiêu này trong ngưỡng.** Với cả ba biến thể của bậc thang bật, p95 là **1.514,26 ms** — vượt cả ngưỡng tối thiểu. Phép bóc tách chỉ ra bậc **siêu phân giải** chiếm hơn nửa chi phí đó (+319 ms ở p95, +1.381 ms ở p99) mà **không mua được biển nào đo được**, nên nó bị tắt mặc định, đưa p95 về 1.143,10 ms. Cần nói rõ giới hạn của lập luận này: số 0 của siêu phân giải là **số 0 cấu trúc** — cổng của nó chỉ mở cho vùng cắt dưới 200 px, trong khi 0/120 mẫu ngữ liệu lọt cổng — nên quyết định dựa trên "chi phí đã đo được và lớn, lợi ích chưa ai đo được", không phải "đã đo và thấy vô dụng". Mã và công tắc được giữ nguyên để bật lại khi có dữ liệu đo tử tế (mục 6.5.7).

Cũng phải ghi lại vì sao con số này từng bị nghi ngờ theo hướng ngược lại. Một báo cáo trước đây ghi p95 = **5.857 ms** và kết luận NFR-P1 "không đạt" — con số đó đã bị **bác bỏ** vì điều kiện đo bị nhiễm (tranh chấp CPU, sai checkpoint, lỗi crop), chứ không vì mô hình chậm; toàn bộ quá trình truy nguyên trình bày ở **mục 6.6.1**.

Phân rã ngân sách độ trễ thật (T6.6b): OCR chiếm **64,3%** (108,28 ms/biển), phát hiện chiếm **34,0%** (57,27 ms) — **không** phải tỉ lệ 93,3% / 6,7% của báo cáo cũ. Kết luận: kiến trúc phần mềm **không phải vấn đề**; nút thắt còn lại là chi phí của các lượt gọi OCR lặp trong bậc thang, và hướng tối ưu đúng là **giảm số lần phải thử lại** — tức nâng chất lượng lần đọc đầu bằng huấn luyện lại bộ nhận dạng (mục 7.4.1) — chứ không phải tối ưu từng lượt gọi (mục 7.4.4).

### 7.3.5. Nút "Huỷ tác vụ" video chưa hoàn chỉnh; một số chỉ tiêu chưa đo

*Mức nghiêm trọng: trung bình đến thấp, tuỳ hạng mục.*

Có hai nhóm khiếm khuyết cần thừa nhận rõ ràng, tránh để người đọc tự phát hiện khi bảo vệ.

**Một chức năng cài đặt lệch khỏi thiết kế.** Thiết kế ở Chương 4 mô tả khả năng huỷ một tác vụ xử lý video đang chạy. Bản cài đặt hiện tại **chưa có route HTTP nào đặt được trạng thái huỷ** — tài liệu OpenAPI đang chạy công bố 9 đường dẫn, không đường dẫn nào huỷ một tác vụ. Chức năng "Huỷ tác vụ" vì vậy chưa hoàn chỉnh ở tầng backend; đây là một hạng mục cài đặt còn treo, không phải một quyết định thiết kế.

**Bảng này từng có bốn hàng; ba hàng đã đo xong ngày 02/08/2026, còn một.**

| Mã | Chỉ tiêu | Trạng thái | Loại |
|:---:|---|---|---|
| P2 | FPS webcam | ❌ **2,379 FPS** — đã đo, **không đạt** (sàn 3) | Đã đo, kết quả trượt |
| P3 | Tốc độ xử lý video | ✅ **0,746×** — đã đo, đạt | Đã đo |
| R5 | CSDL sống sót qua khởi động lại | ✅ **0/9.031 mất** — đã đo, đạt | Đã đo |
| A9 | Tách theo điều kiện ảnh | ⬜ chưa đo — **bộ dữ liệu không có nhãn điều kiện ảnh** | Thiếu điều kiện (hạn chế thật) |

Sự phân biệt ở cột cuối vẫn là điều đáng giữ. P2, P3, R5 thuộc loại *chưa tới lượt đo* — và đúng như dự đoán, chúng khắc phục được chỉ bằng cách viết kịch bản đo, việc đã làm bằng `scripts/benchmark_runtime_nfr.py`. NFR-A9 thì khác hẳn: nó *không đo được vì thiếu nhãn*, và đó mới là hạn chế thật của công trình, chỉ khắc phục được bằng gán nhãn thủ công cho một tập con.

**Một trong ba mã đo ra kết quả trượt, và điều đó cũng đáng ghi nhận về mặt phương pháp:** "chưa đo" không đồng nghĩa với "sẽ đạt". P2 được đo và **trượt cả sàn** vì đuôi độ trễ của bậc thang thử-lại, không phải vì tốc độ trung bình — trung vị 180 ms tương đương 5,6 FPS, vượt mục tiêu. Chi tiết ở mục 6.6.4.

Phép đo P2 gọi trực tiếp `POST /api/detect/frame`, vì trang Webcam của giao diện đã được gỡ theo quyết định thu gọn phạm vi ngày 2026-07-20 — một quyết định phạm vi có chủ đích, không phải khiếm khuyết cài đặt; mã giao diện tương ứng còn nguyên trong lịch sử git.

### 7.3.6. Một yêu cầu mức *Must* (FR-4.1) đã bị đưa ra khỏi phạm vi

*Mức nghiêm trọng: trung bình. Đây là hạn chế duy nhất của đồ án phát sinh từ một **quyết định** chứ không từ một giới hạn kỹ thuật, và vì thế càng phải nói thẳng.*

Ngày 2026-07-20, giao diện web được thu gọn hai đợt liên tiếp: đợt thứ nhất gỡ trang Webcam, đợt thứ hai gỡ trang Tổng quan (Dashboard). Ứng dụng còn **ba trang** — Nhận dạng ảnh (trang chủ), Nhận dạng video, Lịch sử.

Hệ quả về yêu cầu, ghi đúng như nó là:

| Yêu cầu | Mức cũ | Mức mới | Nội dung |
|---|:--:|:--:|---|
| FR-3.1 | M | W | Xin quyền và hiển thị luồng webcam |
| FR-3.4 | M | W | Vẽ chồng bounding box lên khung hình trực tiếp |
| **FR-4.1** | **M** | **W** | **Dashboard hiển thị các chỉ số tổng hợp** |
| FR-4.2 | S | W | Biểu đồ số lượt nhận dạng theo thời gian |

Bảng đếm MoSCoW vì vậy chuyển từ 22/7/3/2 sang **21 Must / 6 Should / 3 Could / 4 Won't** trên tổng 34 yêu cầu.

**FR-4.1 là yêu cầu mức *Must* đầu tiên và duy nhất bị đưa ra khỏi phạm vi trong toàn bộ đồ án.** Theo đúng quy ước MoSCoW đã chốt ở Phase 0, mức *Must* nghĩa là "thiếu ⇒ đồ án không đạt". Tiêu chí thành công số 1 ở mục 1.2.3 — "toàn bộ yêu cầu mức *Must* hoạt động được và demo được" — do đó chỉ đúng khi hiểu theo bộ 21 yêu cầu *Must* **sau** thay đổi phạm vi, chứ không đúng với bộ 22 yêu cầu ban đầu. Đây là một hạn chế thật, không phải một thủ tục hành chính, và nó được nêu ở đây thay vì để hội đồng tự đối chiếu bảng yêu cầu mà phát hiện ra.

Điều cần nói ngay sau đó, để bức tranh không bị méo theo chiều ngược lại: **phần mất đi là màn hình hiển thị, không phải năng lực hệ thống.** Toàn bộ phép tính thống kê vẫn nằm trong `StatisticsService`, vẫn phơi ra qua `GET /api/statistics` với đầy đủ các chỉ số mà FR-4.1 và FR-4.2 đòi hỏi (tổng lượt, tổng biển số, độ tin cậy trung bình, thời gian xử lý trung bình, phân bố theo loại đầu vào, chuỗi số liệu theo ngày), vẫn nằm trong tài liệu OpenAPI đang phục vụ, và **vẫn có kiểm thử tích hợp** — `tests/integration/test_api_statistics.py` và `test_api_health.py` đều nằm trong bộ 1.001 test. Không một endpoint nào bị xoá. Sáu yêu cầu FR-4.3 đến FR-4.8 (lịch sử, tìm kiếm, lọc, chi tiết, tải về, sắp xếp) không đổi mức và vẫn dùng được đầy đủ trên trang Lịch sử.

*Đánh đổi thu được:* gỡ thư viện biểu đồ `recharts` cùng trang Tổng quan làm gói tải về của giao diện giảm từ khoảng **730 KB xuống 328,8 KB (−55%)**, và số mô-đun frontend giảm từ 60 xuống 48.

*Biện pháp giảm thiểu đã áp dụng:* mã nguồn của cả hai trang còn nguyên trong lịch sử git, và các kiểu dữ liệu `Statistics`, `StatisticsQuery`, `HealthStatus`, `InputTypeBreakdown` được **giữ lại có chủ đích** trong `frontend/src/types/index.ts` để hợp đồng của phần API còn sống không bị mất theo trang. Việc khôi phục vì vậy là một thao tác phục hồi có chi phí thấp, không phải xây mới — triển khai ở mục 7.4.6.

### 7.3.7. SQLite chỉ cho phép một tiến trình ghi tại một thời điểm

*Mức nghiêm trọng: thấp trong phạm vi đồ án, cần nêu vì là câu hỏi phản biện dễ gặp.*

Hệ thống dùng SQLite cho lớp dữ liệu. SQLite khoá ghi ở mức toàn tệp: chỉ **một tiến trình ghi tại một thời điểm**. Với bối cảnh triển khai nội bộ, một người vận hành, mà đồ án nhắm tới (giả định A-04), đây không phải nút thắt — phép đo chịu tải cho thấy hệ thống xử lý ổn định 10 yêu cầu đồng thời và soak 300 giây thành công 100%. Nhưng nếu triển khai đa người dùng ghi đồng thời, giới hạn này sẽ trở thành thực. Hướng khắc phục là chuyển sang PostgreSQL (mục 7.4.7); nhờ đã dùng SQLAlchemy 2.0 như tầng trừu tượng, việc chuyển này không đụng đến mã nghiệp vụ.

### 7.3.8. Bộ dữ liệu lệch nặng về biển trắng, nên kết luận về độ chính xác OCR chỉ áp cho biển trắng

*Mức nghiêm trọng: cao. Đây là hạn chế quy định **phạm vi hiệu lực** của mọi con số OCR trong quyển này, nên phải đọc nó trước khi đọc bất kỳ con số nào ở Chương 6.*

Chạy bộ phân loại màu nền lên toàn bộ **2.801 ảnh biển số có nhãn ký tự** của đồ án — chính là tập sinh ra các chỉ số NFR-A4 đến A7 — cho phân bố sau (`docs/reports/17-plate-type-audit.json`):

| Loại biển | Số ảnh | Tỷ lệ |
|---|---:|---:|
| Trắng (dân sự) | 2.736 | **97,68%** |
| Vàng (kinh doanh vận tải) | 20 | 0,71% |
| Xanh (cơ quan Nhà nước) | 4 | 0,14% |
| Đỏ (Quân đội) | **0** | 0% |
| NG/QT (ngoại giao) | **0** | 0% |
| Không đọc được màu | 41 | 1,46% |

Hệ quả phải nói thẳng, và nó nghiêm khắc hơn vẻ ngoài của bảng: **con số độ chính xác OCR mà đồ án công bố thực chất là độ chính xác trên biển trắng.** Với 97,68% mẫu thuộc một lớp duy nhất, mọi chỉ số tổng hợp đều bị lớp đó chi phối gần như hoàn toàn. Câu phát biểu đúng khi bảo vệ là *"1 − CER = 0,9454 trên một tập gồm 97,7% biển trắng"*, không phải *"1 − CER = 0,9454 trên biển số Việt Nam"*. Đây là cùng một loại hạn chế phạm vi với mục 7.3.3 (tập test không xuyên bộ dữ liệu), chỉ khác trục: ở đó là trục nguồn ảnh, ở đây là trục loại biển.

> ### Cập nhật 02/08/2026 — hạn chế này đã được thu hẹp, nhưng **chưa gỡ**
>
> **Mọi con số A4–A7 công bố trong quyển này vẫn đo trên ngữ liệu 2.801 mẫu ở
> bảng trên.** Phần dưới đây mô tả nguyên liệu đã chuẩn bị cho lần đo sau, không
> phải một bộ số mới.
>
> **(a) Đã gộp 521 biển hiếm vào ngữ liệu nhãn ký tự.** Từ bộ
> `nguyenluanai/license-plate-color` v4 (CC BY 4.0), thẩm định ở
> [30-rare-plate-integration.md](../reports/30-rare-plate-integration.md):
>
> | | Trước | Sau |
> |---|---:|---:|
> | Tổng ngữ liệu | 2.801 | **3.322** |
> | Vàng | 20 | **476** |
> | Xanh | 4 | **45** |
> | **Tỷ lệ biển hiếm** | **0,86%** | **15,7%** |
>
> Biển vàng chuyển từ *"n = 20, không có ý nghĩa thống kê"* sang **đánh giá được**.
> Biển xanh (n = 45) vẫn phải báo cáo kèm khoảng tin cậy.
>
> **(b) Mệnh đề "không bộ dữ liệu nào của đồ án chứa biển đỏ" nay chỉ còn đúng cho
> ngữ liệu ảnh cắt sẵn.** Tập ảnh toàn cảnh được gán nhãn ngày 02/08
> ([34-scene-level-a7.md](../reports/34-scene-level-a7.md)) **có** biển đỏ quân đội
> (`PK-53-46` ×2, `QC 10-21`, `VT 1A-16`), biển xanh nhà nước (`80A-068.89`), biển
> ngoại giao (`41-291-NG-01`) và cả sê-ri LD (`93LD-001.03`). Số lượng quá nhỏ để
> công bố độ chính xác theo loại biển, nhưng đủ để **không còn nói "bằng không"**.
>
> **(c) Biển đỏ và ngoại giao vẫn không có nguồn công khai đủ lớn.** Khảo sát 286
> project Roboflow và toàn bộ Kaggle
> ([17-plate-type-dataset-survey.md](../reports/17-plate-type-dataset-survey.md))
> kết luận: biển quân đội Việt Nam hiếm trên đường và nhạy cảm khi công khai,
> *"không nên kỳ vọng tìm được nguồn công khai tốt hơn"*. Đây là hạn chế **thật**,
> không phải hạn chế "chưa tới lượt".

Cần tách bạch hai điều rất dễ bị gộp làm một khi trả lời phản biện:

- **Hệ thống *có* năng lực phân loại loại biển.** Nó phân được chín giá trị `PlateKind` và bốn màu nền, và năng lực này **đã được kiểm chứng trên ảnh thật** — 97,89% trên 1.565 ảnh có nhãn màu do người gán (mục 7.2.5).
- **Hệ thống *chưa có dữ liệu* để đo độ chính xác **nhận dạng ký tự** cho các loại biển hiếm.** Với biển vàng (n = 20) và biển xanh (n = 4), mọi con số độ chính xác đều không có ý nghĩa thống kê; với biển đỏ và biển ngoại giao thì đơn giản là **không đánh giá được**, vì tập không chứa mẫu nào. Bộ dữ liệu dùng để đo màu ở mục 7.2.5 cũng **không** lấp được khoảng trống này: nó không chứa biển đỏ và không chứa biển ngoại giao.

Nói cách khác: **"chưa đo được" không đồng nghĩa với "không làm được", và cũng không được phép trình bày như thể đã đo được.**

*Biện pháp giảm thiểu đã áp dụng:* thực hiện kiểm kê định lượng nói trên thay vì để phân bố tiềm ẩn, và khảo sát các nguồn công khai có thể lấp từng loại biển thiếu (`docs/reports/17-plate-type-dataset-survey.md`). *Biện pháp chưa áp dụng được:* bổ sung chính các mẫu đó vào tập đánh giá — chuyển thành hướng phát triển ở mục 6.4.8.

Một ràng buộc kỹ thuật phát hiện trong quá trình khảo sát cần được ghi lại vì nó thu hẹp giá trị của nguồn bổ sung dồi dào nhất: bộ `nguyenluanai/license-plate-color` — nguồn duy nhất có sẵn 694 ảnh biển vàng — có **mọi ảnh bị kéo méo về khuôn 640×640** trước khi tải lên. Bộ này vì vậy **không dùng được để đánh giá OCR**, vì bước ước lượng số dòng của hệ thống dựa trên **tỷ lệ khung hình** và phép kéo phá huỷ đúng đại lượng đó. Màu nền thì không bị phép kéo làm thay đổi — nên bộ này trả lời được câu hỏi về màu và **chỉ** câu hỏi về màu, và nó đã được dùng đúng như vậy.

### 7.3.9. Bước làm thẳng biển nghiêng (rectify) chưa được cài đặt — ĐÃ XỬ LÝ 21/07/2026, xem cuối mục

Nhật ký quyết định của đồ án mô tả luồng xử lý biển hai dòng gồm bốn bước: **rectify → phân loại số dòng → tách đôi → ghép ngang**. Bước đầu tiên **chưa từng được cài đặt**. Nghiêm trọng hơn, một chú thích trong `ai/inference/recognizer.py` từng khẳng định *"ảnh cắt đã được bộ phát hiện làm thẳng"* — điều này **sai**: hộp bao của YOLO là hộp trục-thẳng, nó cắt ra một hình chữ nhật chứ không nắn hình. Chú thích sai đó đã được sửa lại đúng sự thật.

Hệ quả đo được, trên khung hình thứ 168 của `demo/demo-video.mp4`:

| Đại lượng | Giá trị |
|---|---|
| Biển thật (đọc bằng mắt) | `77-H5` / `4374`, hai dòng, **nghiêng rõ** |
| Hộp bao trục-thẳng | 146 × 42 px, tỷ lệ **3,48** |
| Ngưỡng phân loại một dòng / hai dòng | 2,50 |
| Kết quả phân loại | **một dòng** (sai) |
| Chuỗi OCR trả về | rỗng |

Cơ chế xảy ra rõ ràng: một biển hai dòng bị chụp nghiêng có **hộp bao rộng bất thường**, vì hộp phải bao trọn hình chữ nhật đã xoay. Tỷ lệ vọt lên trên ngưỡng, hệ thống coi đó là biển một dòng nên không tách đôi, và OCR thất bại. Ép tách hai dòng cũng không cứu được, vì vết cắt ngang chém **chéo** qua cả hai hàng ký tự.

Điều đáng chú ý là cùng một biển số ấy: khi chụp gần như chính diện (ảnh `demo/images/nhieu-bien-3.png`) hệ thống đọc **đúng** `77H5-4374`; khi nghiêng thì **không đọc nổi**. Cùng một chuỗi ký tự, cùng một mô hình — chỉ khác góc chụp. Đây là bằng chứng trực tiếp và sạch nhất cho khoảng trống này.

Cảnh báo về vùng xám tỷ lệ khung hình đã được ghi sẵn trong tài liệu của `estimate_line_count` từ Phase 4, nhưng chỉ nêu chiều **giảm** (biển một dòng chụp nghiêng bị tụt xuống dưới ngưỡng). Chiều **tăng** — biển hai dòng nghiêng vọt lên trên ngưỡng — không được lường trước, và trong thực tế đường phố nó phổ biến hơn. Chuyển thành hướng phát triển ở mục 7.4.9.
**Cập nhật 21/07/2026 — hạn chế này đã được xử lý.** Khi bắt tay cài đặt theo
hướng 7.4.9, phép đo trên chính các ảnh cắt do detector sinh ra (36 khung của
video demo) làm lộ thêm hai sự thật mà mô tả ban đầu chưa thấy hết: *(i)* bản
rectify **luôn-bật** làm hại nhiều hơn lợi (42 → 40 lần đọc hợp lệ, vì hình
chữ nhật fit sai trên crop nhỏ cắt mất ký tự của biển đang đọc tốt); *(ii)*
chính biển `77-H5 / 4374` ở khung 168 **không xoay trong mặt phẳng** mà bị
**ngửa ra sau** — foreshortening phối cảnh nén chiều dọc, thứ mà xoay phẳng
về nguyên tắc không chữa được. Thiết kế cuối cùng vì thế là một **bậc thang
thử-lại chỉ kích hoạt khi lần đọc đầu thất bại** (xoay phẳng, rồi giãn dọc ×2
cho dải tỷ lệ mơ hồ 2,5–4,2, mỗi biến thể được hưởng trọn chuỗi đọc + cứu
dòng trên; chỉ nhận khi chuỗi mới hợp lệ). Kết quả đo trên cùng 36 khung:
**42 → 48 lần đọc hợp lệ, 0 thoái lui** (bất biến theo cấu trúc), và khung
168 đọc đúng `77H5-4374` ở độ tin cậy 0,785. Chi tiết, số liệu thô và các
giới hạn còn lại (nắn phối cảnh 4 điểm chưa cài; 3/6 lần đọc mới là đọc sai
của biển quá mờ) tại `docs/reports/21-skew-retry.md`.

### 7.3.10. Xem trực tiếp và xử lý nền tranh chấp CPU với nhau

Trang nhận dạng video chạy đồng thời hai việc trên cùng một CPU không GPU: bản **xem trực tiếp** gửi từng khung hình lên `POST /api/detect/frame`, và **tác vụ nền** xử lý toàn bộ video để cho ra kết quả chính thức. Đo trực tiếp trên backend, cùng một ảnh, chỉ khác điều kiện:

| Điều kiện | Thời gian một khung (chế độ chỉ phát hiện) |
|---|---|
| Không có tác vụ nền chạy | **89–97 ms** |
| Có tác vụ nền đang chạy | **230–462 ms** |

Chậm đi **2,5–5 lần**, và quan hệ này hai chiều: các khung trực tiếp cũng làm tác vụ nền chậm lại. Vì chọn tệp là khởi động cả hai cùng lúc, **cả hai cùng tệ đi mà không bên nào được lợi**.

Đây là hệ quả trực tiếp của quyết định môi trường ở Phase 0 — suy luận chạy trên CPU, không GPU — chứ không phải một lỗi lập trình: hai khối tính toán nặng chia nhau một tài nguyên hữu hạn. Cần ghi nhận vì nó làm **mọi số đo độ trễ của bản xem trực tiếp phụ thuộc vào việc lúc đó có tác vụ nền hay không**, nên một con số độ trễ đơn lẻ không có ý nghĩa nếu không kèm điều kiện đo. Hướng xử lý ở mục 7.4.10.

---

## 7.4. Hướng phát triển

Điểm chung của các hướng dưới đây: chúng **bắt nguồn từ số liệu Chương 6**, không phải từ một danh sách mong muốn chung chung. Thứ tự phản ánh mức ưu tiên do chính kết quả quyết định — hướng đầu tiên nhắm thẳng vào nút thắt thật.

### 7.4.1. Huấn luyện lại module nhận dạng (rec) riêng cho biển số Việt Nam — hướng quan trọng nhất

Mục 7.3.1 đã chứng minh bằng ba bằng chứng độc lập rằng nút thắt độ chính xác nằm ở **tầng OCR**, cụ thể là engine nhận dạng đọc hụt trên biển hai dòng. Do đó hướng phát triển có tác động lớn nhất — vượt xa mọi hướng còn lại — là **thay hoặc huấn luyện lại riêng module nhận dạng ký tự (rec)** cho biển số Việt Nam, thay vì dùng trọng số PaddleOCR đa mục đích pre-trained [17]<!-- cui_2026_ppocrv5 -->.

Có ít nhất bốn cách triển khai cụ thể, xếp theo mức đầu tư tăng dần:

1. **Fine-tune module rec của PaddleOCR trên biển số**, theo đúng công thức mà chính PaddleOCR đã trình bày cho bài toán biển số (fine-tune PP-OCR trên CCPD) [67]<!-- paddlepaddle_nd_plateapp -->. Đây là bước rẻ nhất, tận dụng lại hạ tầng hiện có.
2. **Dùng một mô hình rec hỗ trợ biển đa dòng ngay từ thiết kế.** Các mạng nhận dạng gần đây xử lý cả biển một dòng và hai dòng trong một mô hình thống nhất, chẳng hạn TransLPRNet cho biển một/hai dòng [121]<!-- arxiv_2025_translprnet --> hay LPTR-AFLNet tích hợp nắn chỉnh và nhận dạng nhẹ [76]<!-- xu_2025_lptraflnet -->. Hướng này giải quyết biển hai dòng ở gốc thay vì vá bằng hậu xử lý.
3. **Tách–ghép biển hai dòng trước khi đưa vào rec.** Cách tiếp cận đã được cộng đồng biển số Trung Quốc dùng: cắt nửa trên và nửa dưới rồi ghép ngang thành một dòng để engine một dòng đọc [64]<!-- we0091234_nd_doubleplatesplit -->. Rẻ về huấn luyện nhưng nhạy với chất lượng tách.
4. **Huấn luyện một mô hình nhận dạng chuyên biệt cho biển số Việt Nam từ đầu**, ví dụ theo kiểu CRNN kèm cơ chế chú ý đã được chứng minh trên biển Việt Nam [70]<!-- dang_2024_crnn -->, hoặc các pipeline chuyên xe máy Việt Nam [21]<!-- le_2023_vnmotorcycle -->. Đây là hướng tốn công nhất nhưng có trần chất lượng cao nhất, và phù hợp nhất với đặc thù ký tự và bố cục biển Việt Nam.

Ràng buộc kiến trúc thuận lợi: nhờ NFR-M5, việc thay module rec **không đụng đến mã tầng API** — chỉ cần cài lại giao diện `PlateRecognizer`. Đây chính là lý do khoản đầu tư kiến trúc "tầng AI thay thế được" từ đầu dự án nay sinh lời.

**Ba phép đo độc lập, thu được sau khi Chương 6 đã đo xong, cùng củng cố thứ tự ưu tiên này.** Cả ba đều là can thiệp ở **tầng ngoài mô hình nhận dạng**, đều được thiết kế đúng theo chẩn đoán ở mục 7.3.1, và đều có tính chất bảo đảm không làm hỏng biển nào:

| Can thiệp | Tầng | Thu được | Ghi ở |
|---|---|---:|---|
| Bộ luật hậu xử lý theo vị trí | luật | **+11,39 điểm** A6 · 319 biển | 7.2.3 |
| Bước cứu dòng trên | điều phối | 209 biển | 6.5.6 |
| Bậc thang thử-lại biển nghiêng/méo | hình học | **+0,75 điểm** A6 · 34 biển | 6.5.7 |

Cộng lại, ba can thiệp này đã nâng A6 từ **0,6098** (lượt đo ban đầu, chỉ có chuỗi thô) lên **0,7512** — một quãng đáng kể, và đạt được **không tốn một giây GPU nào**. Nhưng chúng vẫn để A6 thiếu **9,88 điểm** so với ngưỡng, và **dư địa của hướng này đã cạn**: bậc thang hình học — can thiệp mới nhất và tốn kém nhất, làm p95 tăng 32% (866,3 → 1.143,10 ms) — chỉ còn mua được 34 biển trên 2.801.

Cấu trúc phần lỗi còn lại nói rõ vì sao. Sau các can thiệp, ký tự **chèn thừa** gần như biến mất (giảm 88%) trong khi ký tự **bị xoá** nay chiếm 56,8% toàn bộ lỗi (mục 6.5.1). Nghĩa là phần lỗi đã dịch từ "chuỗi hỏng về cấu trúc" — thứ mà luật và điều phối sửa được — sang "**ký tự chưa từng được đọc ra**", thứ mà **về nguyên tắc** không tầng nào ngoài mô hình nhận dạng phục hồi được.

Ba phép đo độc lập vì vậy cùng nói một điều, và nói mỗi lúc một dứt khoát hơn: phần độ chính xác còn thiếu **không nằm ở nơi có thể vá bằng luật, bằng điều phối hay bằng hình học**. Bất kỳ mức cải thiện đáng kể nào cũng phải đến từ chính module rec — và mục 7.4.3 (bổ sung nhãn chuỗi) là điều kiện tiên quyết để làm được điều đó.

> **Một lần thử đã được thực hiện và đã thất bại, ghi lại vì kết quả âm cũng là kết quả.** Lượt fine-tune bộ nhận dạng đầu tiên (28/07/2026) cho ra model đọc **0/7** ảnh demo đúng, so với **7/7** của model gốc — không phải kém hơn một chút mà là chuỗi rác hoàn toàn. Nguyên nhân không nằm ở siêu tham số mà ở **tập huấn luyện sai nhãn, sinh ra một cách im lặng**: kịch bản sinh dữ liệu có cơ chế "ảnh thay thế" kích hoạt khi không mở được ảnh gốc, mà `datasets/raw/**` nằm trong `.gitignore` nên máy huấn luyện không hề có ảnh gốc — kết quả là mọi nhãn bị ghép với ảnh của một biển khác. Cơ chế đó đã bị gỡ bỏ và thay bằng một chốt chặn cứng. Chi tiết: `docs/reports/25-finetune-attempt-failed.md`.
>
> **Lượt thứ hai (02/08/2026) huấn luyện thành công nhưng cũng không được đem giao — vì một lý do khác hẳn, và lý do ấy đáng kể lại.** Model đạt val acc **0,8809** trên tập kiểm định của chính nó, nhưng đo qua đường ống thật lại **kém hơn model gốc**: A6 = 0,6762 so với 0,7512. Truy nguyên cho thấy phép đo lúc huấn luyện và hệ thống lúc chạy **đo hai chế độ khác nhau**: PaddleOCR đánh giá nhánh nhận dạng bằng cách đưa *nguyên ảnh* biển, còn đường ống triển khai chạy *phát hiện chữ trước rồi mới nhận dạng*, tức cắt ảnh thành nhiều mảnh. Model fine-tune chỉ học đọc cả biển một lần nên đọc mảnh vụn rất kém — 0,2667 so với 0,8233 trên **chính những ảnh nó đã huấn luyện trên đó**.
>
> Bỏ bước phát hiện chữ đi thì nó thắng đậm: A6 = **0,8758**, hơn model gốc **12,46 điểm**. Nhưng cấu hình ấy vẫn không được giao, vì ngữ liệu 2.801 mẫu **toàn ảnh đã cắt sẵn**; đo lại trên bộ demo gồm ảnh toàn cảnh qua bộ phát hiện thật thì thứ tự **đảo ngược** (model gốc 17/22 tụt còn 13/22). Ngoài ra chế độ chỉ-nhận-dạng **không có khả năng trả chuỗi rỗng** — 0/1.606 khung, so với 173 của bản đang giao — nên khi bộ phát hiện bắt nhầm thì nó *bịa* ra biển thay vì im lặng, một hành vi tệ hơn nhiều đối với hệ thống có ghi cơ sở dữ liệu.
>
> Cả hai lượt vì vậy đều là **kết quả âm được ghi lại**, nhưng bài học khác nhau: lượt một là lỗi dữ liệu, lượt hai là **lỗi phép đo** — một con số đúng về số học nhưng đo một chế độ mà hệ thống không dùng. Chi tiết: `docs/reports/31-detection-stage-ablation.md`.

### 7.4.2. Xây dựng tập test xuyên bộ dữ liệu

Để chữa hạn chế 7.3.3, cần một quy trình đánh giá đo được tổng quát hoá *xuyên phân bố*. Cách làm: **giữ nguyên một nguồn hoàn toàn không dùng để huấn luyện**, chỉ dùng làm tập test xuyên bộ; báo cáo hai con số song song — mAP trong phân bố (như hiện tại) và mAP xuyên bộ — để người đọc thấy khoảng cách giữa chúng. Đây là cách chuẩn mực mà tài liệu cross-dataset khuyến nghị [7]<!-- laroca_2022_crossdataset -->. Kết hợp với việc **chia split theo nhóm biển số** (mọi ảnh cùng một biển nằm cùng một phía) sẽ khử được cả rò rỉ ngữ nghĩa mà phash không bắt được ở 6.3.2.

### 7.4.3. Bổ sung nhãn chuỗi biển số cho toàn tập

Hiện chỉ **2.801** biển trong tập đánh giá có nhãn chuỗi ký tự, trong khi corpus có 15.133 ảnh phần lớn chỉ có nhãn hộp giới hạn. Mẫu số nhỏ này là một mối đe doạ đến tính hợp lệ (mục 6.9.3) và cũng là thứ chặn việc đo NFR-A7 đúng cách trên ảnh hiện trường (mục 7.3.1). Hướng khắc phục là **gán nhãn chuỗi cho một phân bố hiện trường** đủ lớn, cho phép: (i) đo A7 trên ảnh toàn cảnh thay vì ảnh crop ngoài phân bố; (ii) chia split theo nhóm biển; (iii) có đủ dữ liệu để fine-tune module rec ở 6.4.1. Chi phí gán nhãn có thể giảm bằng bán tự động — dùng chính hệ thống hiện tại sinh nhãn nháp rồi người soát lại — hoặc bổ sung dữ liệu tổng hợp và dữ liệu thật theo hướng hợp nhất đa nguồn đã được nghiên cứu [122]<!-- arxiv_2026_multinationalfusion -->.

### 7.4.4. Tăng tốc suy luận: lượng tử hoá OCR, đóng gói ONNX/OpenVINO cả hai tầng

NFR-P1 chỉ đạt ngưỡng tối thiểu chứ không đạt mục tiêu (p95 = 1.143,10 ms, sàn 1.500 ms, mục tiêu 800 ms — mục 7.3.4), nên phân rã ngân sách chỉ ra việc phải làm chứ không phải dư địa: OCR chiếm 64,3% và phát hiện 34,2% thời gian suy luận. Ba hướng tối ưu, không còn bắt buộc nhưng đáng làm nếu nhắm phần cứng yếu hơn:

- **Lượng tử hoá INT8 module OCR** với một tập hiệu chuẩn, tận dụng tập lệnh vector VNNI/AVX-512 trên CPU Intel [123]<!-- onnxruntime_2025_quantization -->. Vì OCR là phần chiếm thời gian lớn nhất, tối ưu ở đây có đòn bẩy cao nhất.
- **Đóng gói cả hai tầng sang ONNX Runtime hoặc OpenVINO.** Bộ phát hiện YOLO11 xuất sang OpenVINO tối ưu cho CPU Intel [18]<!-- ultralytics_2026_openvinoexport -->, và Ultralytics hỗ trợ hơn hai mươi định dạng xuất [97]<!-- ultralytics_2026_export -->. Hiện đường suy luận chạy PyTorch thuần; thí nghiệm so sánh backend (bảng T6.6c) là hạng mục đã chuẩn bị nhưng chưa chạy.
- Lưu ý phương pháp luận bắt buộc: mọi con số tăng tốc phải đo lại **trên cùng cấu hình phần cứng** và công bố kèm cấu hình, vì cả ONNX Runtime lẫn OpenVINO đều nhạy với kiến trúc CPU và cấu hình luồng cụ thể.

### 7.4.5. Bám vết đối tượng qua khung hình cho video (SORT/DeepSORT)

Hiện tại, khi xử lý video, hệ thống gộp các lần nhận dạng trùng theo **chuỗi ký tự** — cách này gãy khi OCR đọc sai cùng một biển ở các khung khác nhau thành các chuỗi khác nhau. Hướng đúng là **bám vết đối tượng qua khung hình** bằng thuật toán như SORT hoặc DeepSORT: gán một ID theo dõi ổn định cho mỗi xe/biển xuyên suốt các khung, rồi gộp theo ID thay vì theo chuỗi. Cách này vừa ổn định hơn trước lỗi OCR lẻ tẻ, vừa mở đường cho việc **bỏ phiếu theo thời gian** (chọn chuỗi xuất hiện nhiều nhất qua nhiều khung của cùng một track) để nâng độ chính xác video vượt độ chính xác từng khung.

Một hướng mở liên quan là **khôi phục giao diện thời gian thực** — trình bày chung với hướng khôi phục màn hình thống kê ở mục 7.4.6 ngay dưới đây, vì cả hai cùng một bản chất và cùng một cách làm.

### 7.4.6. Khôi phục hai màn hình đã gỡ, từ lịch sử git

Đây là hướng chữa trực tiếp cho hạn chế 7.3.6, và là hướng **rẻ nhất trong toàn bộ mục 7.4** — nó không đòi hỏi nghiên cứu, dữ liệu hay huấn luyện, chỉ đòi hỏi một quyết định về phạm vi.

Hai màn hình bị gỡ ngày 2026-07-20 — **Webcam** và **Tổng quan (Dashboard)** — đều nằm trong tình trạng giống nhau ở ba điểm, và chính ba điểm này làm cho việc khôi phục là *phục hồi* chứ không phải *xây mới*:

1. **Năng lực phía máy chủ chưa bao giờ bị gỡ.** `POST /api/detect/frame` phục vụ FR-3.x; `GET /api/statistics` và `GET /health` phục vụ FR-4.1/FR-4.2. Cả ba vẫn nằm trong tài liệu OpenAPI đang chạy và đều có kiểm thử tích hợp trong bộ 1.001 test.
2. **Mã giao diện còn nguyên trong lịch sử git** — gồm `pages/WebcamDetection.tsx` cùng cơ chế hàng đợi một khe mô tả ở mục 5.7.3, `pages/Dashboard.tsx`, cả thư mục `components/dashboard/`, hook `useApi.ts`, và các hàm `detectFrame` / `getStatistics` / `getHealth` trong `services/api.ts`.
3. **Hợp đồng kiểu vẫn được duy trì** trong `frontend/src/types/index.ts` (`DetectionResponse`, `Statistics`, `StatisticsQuery`, `HealthStatus`, `InputTypeBreakdown`), nên mã khôi phục sẽ biên dịch lại đúng vào cùng các kiểu mà backend đang trả về.

Quy trình khôi phục vì thế gồm ba bước: lấy lại tệp từ lịch sử git, nối lại route trong `App.tsx` và mục tương ứng trong thanh điều hướng, rồi chạy `tsc --noEmit` cùng `vite build` để xác nhận hợp đồng kiểu chưa trôi. Chỉ một điểm cần cân nhắc lại chứ không phục hồi nguyên trạng: **thư viện biểu đồ**. Việc gỡ `recharts` là thứ mang lại phần lớn mức giảm 730 KB → 328,8 KB, nên nếu dựng lại màn hình thống kê thì nên chọn một thư viện nhẹ hơn, hoặc nạp trễ (lazy-load) riêng phần biểu đồ để không kéo lại toàn bộ chi phí đã cắt được.

Cần đặt hướng này đúng chỗ trong thang ưu tiên: nó **khôi phục một chỉ tiêu đã cam kết** (FR-4.1 mức Must) chứ không nâng chất lượng nhận dạng. Nếu chỉ có thể làm một việc, mục 7.4.1 vẫn là việc đáng làm trước — nhưng nếu mục tiêu là tuyên bố đồ án đáp ứng đủ bộ yêu cầu *Must* ban đầu, thì đây là hướng duy nhất đưa được FR-4.1 trở lại.

### 7.4.7. Chuyển sang PostgreSQL nếu triển khai đa người dùng

Để chữa hạn chế 7.3.7, khi triển khai thực tế có nhiều người ghi đồng thời, nên chuyển lớp dữ liệu từ SQLite sang **PostgreSQL** — vốn hỗ trợ nhiều tiến trình ghi đồng thời và điều khiển đồng thời ở mức hàng. Nhờ toàn bộ truy cập dữ liệu đã đi qua SQLAlchemy 2.0 và tầng repository, việc chuyển đổi giới hạn ở lớp cấu hình kết nối và migration, **không** đụng đến mã nghiệp vụ hay mã API. Đây là một ví dụ nữa cho thấy các quyết định kiến trúc bảo thủ ở đầu dự án (dùng ORM thay vì SQL thô, tách repository khỏi service) trả cổ tức ở giai đoạn mở rộng.

### 7.4.8. Thu thập dữ liệu cho các loại biển hiếm — điều kiện để mở rộng phạm vi kết luận

Hướng này chữa trực tiếp hạn chế 7.3.8, và điểm đáng chú ý của nó là **nó không đòi hỏi thay đổi gì trong hệ thống**: năng lực phân loại chín họ biển và bốn màu nền đã có sẵn và đã được kiểm chứng (mục 7.2.5). Thứ còn thiếu là **dữ liệu để đo**, không phải mã để chạy. Vì vậy đây là hướng có tỷ lệ *mở rộng phạm vi kết luận trên một đơn vị công sức* cao nhất trong mục 7.4.

Ba việc cụ thể, xếp theo mức khó tăng dần:

1. **Biển vàng — đã có nguồn, cần xử lý đúng.** Bộ `nguyenluanai/license-plate-color` (CC BY 4.0) cung cấp 694 ảnh biển vàng, gấp khoảng 35 lần số hiện có, và **tên tệp đã chứa sẵn chuỗi biển số** nên nhãn ký tự gần như miễn phí. Trở ngại duy nhất là phép kéo méo về 640×640 nêu ở mục 7.3.8; cách xử lý là lấy ảnh gốc từ nguồn thay vì bản đã kéo, sau đó soát lại nhãn bằng mắt trước khi công bố bất kỳ con số nào.
2. **Biển đỏ quân đội và biển ngoại giao — cần chuyển từ "0 mẫu" sang "đo được".** Khảo sát ở `docs/reports/17-plate-type-dataset-survey.md` đã xác định được nguồn công khai chứa hai loại này, nhưng ở quy mô rất nhỏ (khoảng một trăm ảnh gốc biển đỏ, và chỉ khoảng mười tám ảnh gốc biển ngoại giao). Quy mô đó **đủ để có một tập kiểm thử báo cáo được** — thứ hiện đang bằng không — nhưng **không đủ để huấn luyện**, và sự phân biệt này phải được giữ nguyên khi báo cáo. Hai rủi ro bắt buộc xử lý trước khi nhập: các bản tăng cường trong nguồn bị chia lẫn giữa train/valid/test nên phải gom theo ảnh gốc rồi tự chia lại, và giấy phép của các nguồn này là do người đăng tự khai chứ không phải giấy phép của ảnh gốc.
3. **Biển chuyên dùng (LD, DA, RM, HC, KT, CD, T) — chưa tìm được nguồn nào.** Với nhóm này, con đường khả dĩ duy nhất là thu thập và gán nhãn tại chỗ, hoặc chấp nhận rằng chúng nằm ngoài phạm vi đánh giá và ghi rõ như vậy.

Cần đặt hướng này đúng vị trí trong thang ưu tiên: nó **không** nâng độ chính xác của hệ thống lên một điểm nào. Giá trị của nó là **mở rộng phạm vi mà các kết luận của đồ án có hiệu lực** — chuyển câu phát biểu từ *"đo trên một tập gồm 97,7% biển trắng"* sang một câu có phân tầng theo loại biển. Với một công trình mà đóng góp chính là *đo được những thứ trước đây chỉ được mô tả định tính*, việc mở rộng phạm vi hiệu lực của phép đo là một hướng phát triển đúng bản chất của công trình chứ không phải một việc phụ.

### 7.4.9. Cài đặt bước làm thẳng biển nghiêng — ĐÃ THỰC HIỆN 21/07/2026

Hướng này chữa trực tiếp hạn chế 7.3.9, và điểm hấp dẫn của nó là **thiết kế đã có sẵn**: nhật ký quyết định đã mô tả bước rectify đứng đầu luồng xử lý biển hai dòng, việc còn lại là cài đặt đúng thứ đã thiết kế chứ không phải nghĩ ra cách tiếp cận mới.

Đường đi cụ thể, xếp theo mức đầu tư tăng dần:

1. **Ước lượng góc nghiêng bằng `cv2.minAreaRect` rồi xoay ngược.** Nhị phân hoá ảnh cắt, lấy hình chữ nhật nhỏ nhất bao lấy vùng sáng, đọc góc, rồi `warpAffine` xoay về ngang. Khoảng bốn mươi dòng mã, không cần huấn luyện, không cần dữ liệu mới.
2. **Đo lại số dòng trên ảnh đã nắn thay vì trên hộp bao.** Chính tài liệu của `estimate_line_count` đã đề xuất điều này từ Phase 4 nhưng chưa thực hiện. Sau khi nắn, tỷ lệ khung hình mới phản ánh hình dạng thật của biển, nên ngưỡng 2,5 mới có ý nghĩa như thiết kế.
3. **Nắn phối cảnh bốn điểm** cho trường hợp biển bị chụp chéo chứ không chỉ xoay phẳng. Đắt hơn và cần một bước tìm bốn góc biển đáng tin cậy.

Cần nhấn mạnh **kỷ luật đo lường bắt buộc** cho hướng này, rút ra từ chính kinh nghiệm của đồ án: tập nhãn hiện có gồm **ảnh cắt sẵn của bộ dữ liệu**, phần lớn đã gần chính diện, nên nó **không chứa dạng lỗi này**. Một phép đo trên tập đó nhiều khả năng cho kết quả "không đổi" và sẽ bị hiểu nhầm thành "không có tác dụng". Muốn đo đúng thì phải dựng một tập đánh giá gồm **ảnh cắt do chính bộ phát hiện sinh ra từ ảnh chụp toàn cảnh**, tức đúng thứ hệ thống gặp khi chạy thật. Bài học này đã lặp lại hai lần trong đồ án và nên được ghi lại như một nguyên tắc: **tập đánh giá phải chứa dạng lỗi mà bản sửa nhắm tới, nếu không phép đo chỉ chứng minh được tính an toàn chứ không chứng minh được lợi ích.**
**Kết quả thực hiện (21/07/2026).** Hướng này đã được cài đặt, và kỷ luật đo
lường nêu trên phát huy tác dụng theo đúng nghĩa đen — nó **bác bỏ thiết kế
đầu tiên**. Bậc 1+2 cài dưới dạng bước tiền xử lý luôn-bật vượt qua toàn bộ
kiểm thử hình học tổng hợp, nhưng đo trên 36 khung ảnh cắt do detector sinh
ra từ video demo thì **thua baseline 42 → 40**: trên crop nhỏ và mờ,
`minAreaRect` thi thoảng fit sai và vết cắt lại lấy mất ký tự của một biển
đang đọc tốt. Cùng phép đo cũng cho thấy ca khung 168 thực chất là
**foreshortening phối cảnh** (biển ngửa ra sau, không xoay trong mặt phẳng),
nằm ngoài tầm với của phép xoay phẳng.

Thiết kế cuối cùng giữ nguyên hình học nhưng đổi **vị trí đứng trong luồng**:
một *bậc thang thử-lại* chỉ chạy khi lần đọc đầu đã thất bại — biến thể xoay
phẳng khi phép nắn thật sự thay đổi crop, biến thể **giãn dọc ×2** khi tỷ lệ
hộp nằm trong dải mơ hồ 2,5–4,2 (giải quyết đúng ca foreshortening), mỗi biến
thể được hưởng trọn chuỗi đọc + cứu dòng trên, và chỉ được nhận khi chuỗi mới
validate. Baseline vì thế bất biến theo cấu trúc. Kết quả đo cuối trên cùng
36 khung: **42 → 48 lần đọc hợp lệ, 0 thoái lui**; khung 168 đọc đúng
`77H5-4374` (độ tin cậy 0,785) qua đúng chuỗi giãn dọc → đọc dòng dưới →
cứu dòng trên tại vết cắt 0,55. Ba trong sáu lần đọc mới là đọc sai của các
biển quá mờ ở xa — ghi nhận trung thực tại `docs/reports/21-skew-retry.md`
cùng số liệu thô. Một sự cố thực địa ngay sau triển khai buộc bổ sung hai
cổng chặn: bậc thang phiên bản đầu coi biển quân đội đọc đúng (cố ý mang cờ
*invalid* theo nguyên tắc nhận-để-loại-trừ) là lần đọc hỏng, đọc lại và nhoè
`KV-69-38` thành chuỗi dân sự "hợp lệ" `14D7-069.38` — đúng lớp lỗi tự
tin-mà-sai từng phải sửa ở Phase 4. Bản cuối chỉ thử lại khi lần đọc đầu
**không phân loại được**, và không bao giờ thử lại trên **nền đỏ**; cả hai
cổng đều có kiểm thử ghim. Bài học: cờ *không hợp lệ* trong hệ thống này mang
hai nghĩa (đọc thất bại ↔ nhận diện thành công một biển ngoài phạm vi dân sự),
và mọi quyết định dựa trên nó phải phân biệt được hai nghĩa ấy. Việc còn lại của hướng này thu hẹp về bậc 3: nắn phối cảnh
bốn điểm cho các góc chéo sâu mà giãn dọc thô không mô hình hoá được.

### 7.4.10. Tách lịch chạy giữa xem trực tiếp và xử lý nền

Hạn chế 7.3.10 cho thấy hai khối tính toán nặng đang giành một CPU và **cùng chậm đi**. Ba hướng xử lý, mỗi hướng có cái giá riêng:

1. **Chạy tuần tự thay vì song song.** Hoãn tác vụ nền cho tới khi người dùng dừng xem trực tiếp. Cả hai đều nhanh hơn hẳn so với chạy chồng; cái giá là kết quả đầy đủ có muộn hơn. Đây là hướng đơn giản nhất và nhiều khả năng đúng nhất cho một máy đơn.
2. **Giới hạn số luồng CPU của tác vụ nền**, chừa chỗ cho khung trực tiếp. Không đổi trải nghiệm người dùng, nhưng làm tác vụ nền chậm đi và cần đo để chọn mức chia.
3. **Tách tiến trình suy luận ra khỏi tiến trình API**, rồi xếp hàng có mức ưu tiên. Đúng đắn nhất về kiến trúc và cũng nặng nhất; chỉ đáng làm nếu hệ thống được triển khai nhiều người dùng, và khi đó nó đi kèm với hướng 6.4.7.

Cần ghi kèm một hệ quả về phương pháp: vì độ trễ của bản xem trực tiếp phụ thuộc mạnh vào việc lúc đó có tác vụ nền hay không, **mọi con số độ trễ công bố cho tính năng này bắt buộc phải kèm điều kiện đo**. Một con số trần trụi sẽ đúng hoặc sai gấp năm lần tuỳ hoàn cảnh, và đó là kiểu số liệu mà phần lớn công việc kiểm chứng của đồ án này được dựng lên để loại bỏ.

---

## 7.5. Kết luận chung

Đồ án đặt ra mục tiêu xây dựng một hệ thống nhận dạng biển số xe Việt Nam hoàn chỉnh, chạy trên CPU, hỗ trợ cả biển một dòng và hai dòng. Đối chiếu trung thực với mục tiêu đó, kết quả có thể tổng kết trong ba mệnh đề, không tô hồng và cũng không tự hạ thấp.

**Thứ nhất, hệ thống hoàn chỉnh và chạy được — điều này là chắc chắn, kiểm chứng được, không phải lời hứa.** Bốn tầng backend–frontend–AI–dữ liệu được đóng gói Docker, khởi động một lệnh, xác minh bằng HTTP sống và bằng stack Docker kiểm từ ngoài container. Bộ phát hiện đạt **toàn bộ** chỉ tiêu với biên rộng (mAP@0.5 = 0,9829, mAP@0.5:0.95 = 0,7834). Mọi chỉ tiêu hiệu năng, độ tin cậy và chịu tải đều đạt, trừ hai chỉ tiêu trên chính đường xử lý ảnh: NFR-P1 chỉ đạt ngưỡng tối thiểu (p95 = **1.143,10 ms**, trung vị 405,77 ms; mục tiêu 800 ms) và NFR-P2 trượt cả sàn (**2,379 FPS**, sàn 3). Cả hai cùng một nguyên nhân là đuôi độ trễ của bậc thang thử-lại, và cùng một đánh đổi có chủ ý. Một điều chỉnh phải nói kèm ngay ở đây để mệnh đề này không bị đọc rộng hơn sự thật: giao diện web đã được thu gọn còn **ba màn hình** ngày 2026-07-20, và cùng đợt đó **một yêu cầu mức *Must* — FR-4.1, màn hình thống kê tổng hợp — bị đưa ra khỏi phạm vi** (mục 7.3.6). Năng lực tương ứng vẫn phục vụ và vẫn có kiểm thử ở tầng API, nhưng bộ yêu cầu *Must* mà hệ thống đáp ứng là bộ **21**, không phải bộ 22 ban đầu.

**Thứ hai, đồ án đo được hai đại lượng mà tài liệu Việt Nam chưa công bố tách bạch.** Đóng góp thuần của khối hậu xử lý theo luật — **+11,39 điểm**, 319 biển sửa đúng, 0 biển làm hỏng — được lượng hoá thay vì mô tả định tính. Và rủi ro R-04 được đo bằng **số liệu Việt Nam thật**: chênh lệch **25,45 điểm** độ chính xác chuỗi giữa biển một dòng và biển hai dòng, cùng bậc độ lớn với mốc 48,6 điểm mà Laroca và cộng sự đo trên RodoSol-ALPR của **Brazil** [7]<!-- laroca_2022_crossdataset --> — một analogue quốc tế, không phải số Việt Nam.

**Thứ ba, và phải nói thẳng: nhận dạng ký tự trên biển hai dòng vẫn là một bài toán mở.** Ba chỉ tiêu độ chính xác OCR không đạt, và nguyên nhân đã được định vị chính xác — không phải ở tầng hậu xử lý, không phải ở tầng phát hiện, không phải ở tầng hình học (cả ba đều đã được xử lý và đo tách bạch), mà ở **tầng nhận dạng ký tự** trên quần thể biển hai dòng, vốn chiếm 79,8% dữ liệu vì phản ánh mật độ xe máy Việt Nam. Biển một dòng về cơ bản đã giải xong (A6 = 0,9541); biển hai dòng thì chưa (A6 = 0,6996). Đây là hạn chế trung tâm, và nó vạch sẵn hướng phát triển quan trọng nhất: huấn luyện lại module nhận dạng riêng cho biển số Việt Nam.

**Một điều kiện phạm vi phải đi kèm mệnh đề thứ ba, và nó cũng giới hạn cả mệnh đề thứ hai.** Tập 2.801 biển có nhãn chuỗi mà mọi con số OCR ở trên dựa vào gồm **97,68% biển trắng**, chỉ 20 biển vàng, 4 biển xanh, và **không một biển đỏ hay biển ngoại giao nào** (mục 7.3.8). Ngày 02/08/2026 ngữ liệu đã được gộp thêm 521 biển vàng/xanh, đưa tỷ lệ biển hiếm lên 15,7% — nhưng **các con số A4–A7 trong quyển này vẫn đo trên ngữ liệu cũ**, nên điều kiện phạm vi dưới đây giữ nguyên hiệu lực cho đến khi có lần đo mới. Vì vậy các chỉ số A4–A7 phải được phát biểu là *"đo trên một tập gồm 97,7% biển trắng"*, không phải *"đo trên biển số Việt Nam"*. Hệ thống **có** năng lực phân loại chín họ biển và bốn màu nền — đã kiểm chứng ở 97,89% trên 1.565 ảnh có nhãn màu do người gán — nhưng **chưa có dữ liệu** để đo độ chính xác nhận dạng ký tự cho các loại biển hiếm. "Chưa đo được" không đồng nghĩa với "không làm được", và cũng không được trình bày như thể đã đo được.

Giá trị của đồ án vì vậy không nằm ở một con số state-of-the-art — điều mà Chương 1 đã cam kết ngay từ đầu là *không* tuyên bố. Nó nằm ở ba chỗ khác: **một hệ thống đầy đủ và tái lập được**; **ba đại lượng đo được mà trước đó chỉ được mô tả định tính** (đóng góp hậu xử lý, rủi ro R-04 trên dữ liệu Việt Nam, và độ chính xác của bộ nhận màu nền — nguồn bằng chứng duy nhất tách được biển vàng kinh doanh khỏi biển trắng cá nhân, thứ mà chuỗi ký tự về nguyên tắc không làm được); và **một quy trình đánh giá tự kiểm chứng** đã bắt được rò rỉ dữ liệu, một lập luận vòng tròn, một đặc tính toán học của phash, một con số độ trễ bị nhiễm, một giả thuyết sửa lỗi hợp lý bị chính dữ liệu bác bỏ, và — nghiêm trọng nhất — **một bộ đo đi tắt qua đường mã của chính sản phẩm nó đang đo** — rồi ghi lại tất cả thay vì che đi. Một hệ thống trung thực về giới hạn của chính mình, kèm một bản đồ số liệu chỉ rõ bước tiếp theo phải làm ở đâu, là một điểm khởi hành vững hơn nhiều so với một con số đẹp không kiểm chứng được.
