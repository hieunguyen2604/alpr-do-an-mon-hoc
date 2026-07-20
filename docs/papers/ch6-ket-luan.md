# CHƯƠNG 6. KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN

Năm chương trước đã đi hết một vòng: Chương 1 đặt bài toán và cam kết các chỉ tiêu định lượng, Chương 2 dựng cơ sở lý thuyết, Chương 3 thiết kế hệ thống, Chương 4 trình bày bản cài đặt đã chạy được, và Chương 5 đo hệ thống đó trên tập test độc lập rồi đối chiếu với từng chỉ tiêu. Chương kết luận này không đo lại bất kỳ chỉ tiêu nào của Chương 5. Nó có dẫn một số con số **không xuất hiện ở Chương 5** — độ chính xác của bộ nhận màu nền (mục 6.2.5), kết quả kiểm kê loại biển của tập đánh giá (mục 6.3.8) và hiệu quả của bước cứu biển hai dòng (mục 6.4.1) — vì các phép đo đó được thực hiện **sau khi Chương 5 đã chốt**; mỗi con số đều ghi kèm tệp báo cáo gốc để đối chiếu. Nhiệm vụ của chương là ba việc: **tổng kết** những gì đã thực sự làm ra, **thừa nhận trung thực** những gì chưa đạt cùng nguyên nhân đã được định vị bằng số liệu, và **chỉ ra hướng phát triển** mà bản thân kết quả thực nghiệm — chứ không phải phỏng đoán — đã vạch sẵn.

Có một nguyên tắc chi phối toàn chương, kế thừa trực tiếp từ ranh giới liêm chính học thuật đã giữ suốt Chương 5: **không tô hồng**. Hệ thống này đạt chỉ tiêu ở tầng phát hiện và tầng phần mềm, nhưng **không đạt bốn chỉ tiêu độ chính xác OCR**, và nguyên nhân nằm gần như trọn vẹn ở quần thể biển hai dòng. Một quyển đồ án trình bày thất bại đó kèm phân tích nguyên nhân đúng chỗ có giá trị hơn hẳn một quyển giấu nó sau một con số tổng đẹp. Vì vậy mục 6.3 (các hạn chế) được viết với dung lượng tương xứng với mục 6.2 (các kết quả đạt được), không bị nén thành một dòng lấy lệ.

---

## 6.1. Tổng kết công việc đã thực hiện

### 6.1.1. Điểm lại mười một giai đoạn — mỗi giai đoạn một sản phẩm thật

Đồ án được tổ chức thành mười hai giai đoạn (Phase 0 đến Phase 11), trong đó mười một giai đoạn đầu đã tạo ra sản phẩm bàn giao được, còn giai đoạn cuối (đóng gói bàn giao) phụ thuộc việc bảo vệ. Bảng dưới đây điểm lại từng giai đoạn bằng đúng một câu về **sản phẩm có thật** mà nó để lại, không phải kế hoạch của nó.

| Giai đoạn | Sản phẩm thật đã bàn giao |
|:---:|---|
| **Phase 0 — Phân tích yêu cầu** | Bộ tài liệu SRS, 34 yêu cầu chức năng và bảy nhóm yêu cầu phi chức năng, mọi chỉ tiêu đều **đo được bằng số**, chốt mốc M0. |
| **Phase 1 — Nghiên cứu** | Bảy báo cáo khảo sát và 232 mục trích dẫn BibTeX đã qua kiểm chứng đối kháng, phát hiện và sửa 25 lỗi (3 lỗi mức critical, gồm việc căn cứ pháp lý TT 24/2023/TT-BCA đã hết hiệu lực), chốt mốc M1. |
| **Phase 2 — Xây dựng bộ dữ liệu** | Bộ dữ liệu v3 gồm **15.133 ảnh** hợp nhất từ bảy bộ tải về (còn **sáu nguồn nguyên tố** sau khử trùng lặp), chia train 10.592 / val 3.027 / test 1.514 ở ngưỡng gộp trùng lặp 10. |
| **Phase 3 — Huấn luyện bộ phát hiện** | Mô hình chính thức `models/best.pt` — YOLO11n [1]<!-- jocher_2024_yolo11 -->, 2.590.035 tham số, `imgsz=640`, 20 epoch trên CPU — đạt mAP@0.5 = 0,9829 trên tập test v3. |
| **Phase 4 — Nhận dạng ký tự và hậu xử lý** | Khối OCR dựng trên PaddleOCR PP-OCRv5 mobile [2]<!-- cui_2026_ppocrv5 --> cộng bộ luật hậu xử lý theo vị trí; đo được đóng góp thuần **+4,57 điểm** của khối hậu xử lý trên 2.801 biển có nhãn chuỗi. |
| **Phase 5 — Backend** | Backend FastAPI với **10 thao tác trên 9 đường dẫn**, xác minh bằng HTTP sống (`/health` trả `model_loaded: true`), Alembic migrate xong, Swagger render đầy đủ, chốt mốc M5. |
| **Phase 6 — Frontend** | Ứng dụng React một trang, build sạch, khớp toàn bộ 10 thao tác API, phủ năm màn hình tại thời điểm chốt phase (Dashboard, Nhận dạng ảnh, Video, Webcam, Lịch sử). *Ngày 2026-07-20, giao diện được thu gọn hai đợt liên tiếp còn **ba màn hình** — Nhận dạng ảnh (trang chủ), Nhận dạng video, Lịch sử: đợt 1 gỡ trang Webcam, đợt 2 gỡ trang Tổng quan (Dashboard). Cả hai năng lực đều giữ nguyên ở tầng API (`POST /api/detect/frame`, `GET /api/statistics`, `GET /health`) và đều còn kiểm thử tích hợp; hệ quả về yêu cầu — gồm việc **FR-4.1 mức Must bị đưa ra khỏi phạm vi** — ghi ở mục 6.3.6.* |
| **Phase 7 — Kiểm thử và đo hiệu năng** | **882 test thu thập, 881 pass, 1 xfail, 0 fail, 0 skip** (lần chạy 2026-07-20, `docs/reports/13-refactor-result.json`); sau khi bổ sung test cho bộ nhận màu nền, bước cứu biển hai dòng và ba cột CSDL mới, lần chạy cuối cùng cùng ngày cho **913 thu thập, 912 pass, 1 xfail, 0 fail**; độ bao phủ tầng nghiệp vụ **87,7%** ở mốc `13-refactor-result.json` — số đo ở Phase 7 trước đó là 88,1% (`docs/reports/07-testing-report.md`); toàn bộ chỉ tiêu hiệu năng ngoài đường suy luận được đo và đạt. |
| **Phase 8 — Đóng gói Docker** | Hai image, stack `docker compose up` chạy được trên máy sạch, kiểm bằng `curl` từ ngoài container, chốt mốc M8. |
| **Phase 9 — Tài liệu** | Quyển đồ án — Chương 1 đến Chương 4 hoàn tất trước, Chương 5 và Chương 6 hoàn tất sau khi có `best.pt` và số liệu thực nghiệm. |
| **Phase 10 — Bảo vệ** | Khung 21 slide, poster, kịch bản demo và 56 câu hỏi phản biện dự kiến. |

> **Một lưu ý về tên gọi để tránh hiểu nhầm khi bảo vệ.** Thư mục bộ dữ liệu tên `yolo_v3` là **phiên bản thứ ba của bộ dữ liệu**, không liên quan đến kiến trúc "YOLOv3". Mô hình dùng trong toàn đồ án là **YOLO11n** [1]<!-- jocher_2024_yolo11 -->, họ YOLO thế hệ 11, biến thể nano.

Điểm cần nhấn: trong suốt Phase 5 đến Phase 7, hệ thống từng chạy bằng một pipeline giả lập (`StubPipeline`) cài đúng giao diện trừu tượng của tầng AI. Đó là lựa chọn kiến trúc có chủ đích — nó cho phép phát triển và kiểm thử toàn bộ backend, cơ sở dữ liệu và giao diện **trước khi** có trọng số, đồng thời chứng minh trên thực tế rằng ràng buộc NFR-M5 (thay được bộ nhận dạng mà không sửa mã tầng API) là khả thi. Ở trạng thái hiện tại, `StubPipeline` **đã bị đưa ra khỏi đường chạy chính**: đường chạy chính là pipeline thật với `best.pt`, và phương án lùi khi thiếu trọng số là `UnavailablePipeline` — vốn **ném lỗi** thay vì bịa ra biển số. Không một con số nào trong quyển này do stub sinh ra.

### 6.1.2. Bảng đối chiếu mục tiêu Phase 0 với kết quả thật

Bảng dưới đây đặt cạnh nhau **chỉ tiêu đã cam kết ở Phase 0** và **con số đo được thật trên `best.pt`** ở Chương 5. Nó là phiên bản cô đọng của bảng T5.9, giữ lại các chỉ tiêu có kết luận rõ ràng. Cột "Kết quả" ghi trung thực cả đạt lẫn không đạt.

| Mã | Chỉ tiêu | Mục tiêu Phase 0 | Đo được (`best.pt`) | Kết quả |
|:---:|---|---:|---:|:---:|
| A1 | mAP@0.5 phát hiện | 0,90 | **0,9829** | ✅ đạt |
| A2 | mAP@0.5:0.95 phát hiện | 0,65 | **0,7834** | ✅ đạt |
| A3-P | Precision phát hiện | 0,92 | **0,9837** | ✅ đạt |
| A3-R | Recall phát hiện | 0,90 | **0,9714** | ✅ đạt |
| A4 | 1 − CER (mức ký tự) | 0,95 | **0,8734** | ❌ không đạt |
| A5 | Chuỗi trước hậu xử lý | 0,85 | **0,6098** | ❌ không đạt |
| A6 | Chuỗi sau hậu xử lý | 0,90 | **0,6555** | ❌ không đạt |
| A6−A5 | Đóng góp hậu xử lý (điểm %) | — | **+4,57** | (đóng góp thuần dương) |
| A7 | Độ chính xác E2E toàn trình | 0,88 | **0,5227** | ❌ không đạt* |
| A8 | Chênh lệch layout, phát hiện (điểm %) | — | **2,09** | (rất nhỏ) |
| P1 | Độ trễ E2E một ảnh, p95 (ms) | ≤ 800 | **731,15** | ✅ đạt |
| P4 | Thời gian nạp mô hình (s) | ≤ 15 | **6,41** | ✅ đạt |
| P5 | Overhead API, p95 (ms) | ≤ 50 | **19,01** | ✅ đạt |
| P6 | Truy vấn 10.000 bản ghi, p95 (ms) | ≤ 500 | **18,71** | ✅ đạt |
| P7a | RSS pipeline (GB) | ≤ 2 | **0,759** | ✅ đạt |
| P7b | RSS máy chủ backend (GB) | ≤ 2 | **0,806** | ✅ đạt |
| R4 | Tỉ lệ thành công soak 300 s | ≥ 99% | **100%** (1.684 yêu cầu) | ✅ đạt |
| SC1 | Số yêu cầu đồng thời ổn định | ≥ 5 | **10** | ✅ đạt |
| M2 | Độ bao phủ test tầng nghiệp vụ | — | **87,7%** đo 2026-07-20 (881/882 pass, 1 xfail); lần chạy cuối cùng cùng ngày: 912/913 pass; trước đó Phase 7 đo 88,1% | (tham chiếu) |

\* A7 = 0,5227 phải đọc như **cận dưới bi quan** — nó đo trên ảnh crop biển số (ngoài phân bố huấn luyện của bộ phát hiện), khiến tỉ lệ bỏ sót ở tầng phát hiện bị thổi phồng; xem phân tích ở mục 6.3.1.

Đọc bảng theo hàng dọc cho thấy một hình mẫu rõ ràng và chính là toàn bộ câu chuyện của đồ án: **mọi chỉ tiêu phát hiện, hiệu năng, độ tin cậy và khả năng chịu tải đều đạt, thường với biên rộng; mọi chỉ tiêu độ chính xác OCR đều không đạt.** Vạch ngăn giữa "đạt" và "không đạt" trùng khít với vạch ngăn giữa tầng phát hiện và tầng nhận dạng ký tự. Đây không phải sự trùng hợp — nó là kết luận trung tâm mà Chương 5 đã chứng minh và Chương 6 sẽ khai thác để định hướng phát triển.

Các chỉ tiêu **chưa đo được** (không đưa vào bảng trên) gồm NFR-P2 (FPS webcam), NFR-P3 (tốc độ xử lý video), NFR-A9 (tách theo điều kiện ảnh) và NFR-R5 (CSDL sống sót qua khởi động lại). Lý do của từng ô được ghi ở mục 6.3.5; việc phân biệt "chưa đo vì chưa tới lượt" với "không đo được vì thiếu điều kiện" được giữ nguyên tinh thần của mục 5.11.2.

---

## 6.2. Các kết quả đạt được

### 6.2.1. Một hệ thống hoàn chỉnh, chạy được, xác minh bằng HTTP thật

Sản phẩm đầu tiên và bao trùm nhất không phải một con số mà là **một hệ thống phần mềm hoàn chỉnh, đầu-cuối, thực sự chạy**. Bốn tầng của nó — backend FastAPI, frontend React, pipeline AI (`ALPRPipeline`) và lớp dữ liệu SQLite/SQLAlchemy — được đóng gói bằng Docker và khởi động bằng một lệnh `docker compose up` trên máy sạch, không cần kết nối Internet khi vận hành.

Điều làm cho tuyên bố này khác một lời hứa là nó **kiểm chứng được**, và đã được kiểm chứng: 10 thao tác API (trên 9 đường dẫn) phản hồi đúng qua HTTP sống; `/health` báo `model_loaded: true` với engine thật `yolo:best.pt + paddleocr-PP-OCRv5-mobile`; Alembic migrate hoàn tất; Swagger render đầy đủ; và stack Docker được kiểm bằng `curl` từ **ngoài** container chứ không chỉ bên trong. Bốn nguyên tắc kiến trúc đặt ra ở Chương 3 — không trộn mã AI với mã API, thay thế được thành phần, không hard-code đường dẫn, chạy được không cần GPU — không dừng ở khẩu hiệu: ràng buộc "tầng AI không có mũi tên đi lên" kiểm chứng được bằng một lệnh `grep`, và khả năng thay thế bộ nhận dạng (NFR-M5) đã được chứng minh bằng chính sự tồn tại của `StubPipeline` và `UnavailablePipeline` như các bản cài thay thế của cùng một giao diện.

Ở góc độ kỹ nghệ, đây là đóng góp vững nhất của đồ án: một hệ thống ALPR tái lập được, chạy hoàn toàn trên CPU, khởi động một lệnh, không phụ thuộc dịch vụ ngoài — phù hợp bối cảnh triển khai nội bộ mà đề tài nhắm tới.

### 6.2.2. Bộ phát hiện đạt toàn bộ chỉ tiêu với biên rộng

Trên tập test v3 (1.514 ảnh, 1.611 đối tượng nhãn thật), bộ phát hiện YOLO11n [1]<!-- jocher_2024_yolo11 --> vượt **cả bốn** chỉ tiêu phát hiện, và vượt *mục tiêu* chứ không chỉ *ngưỡng tối thiểu*:

- mAP@0.5 = **0,9829** (mục tiêu 0,90);
- mAP@0.5:0.95 = **0,7834** (mục tiêu 0,65) — đây là chỉ số quyết định vì nó khắt khe với chất lượng định vị hộp, và biên vượt vẫn rất rộng;
- Precision = **0,9837**, Recall = **0,9714**, F1 = **0,9775**.

Hai kết quả phụ củng cố độ tin cậy của con số tổng. Thứ nhất, chênh lệch giữa hai layout ở tầng phát hiện chỉ **2,09 điểm** mAP@0.5 (biển một dòng 0,9884 so với biển hai dòng 0,9675) — xác nhận rằng *việc định vị box* gần như không phụ thuộc layout, một điểm quan trọng vì nó tách bạch trách nhiệm: nếu độ chính xác toàn trình kém trên biển hai dòng thì lỗi **không** nằm ở khâu phát hiện. Thứ hai, khi tách theo dải kích thước (bảng T5.5c), mô hình phơi bày trung thực điểm yếu duy nhất của mình: dải đối tượng "rất nhỏ" (dưới 0,5% diện tích ảnh) chỉ đạt mAP@0.5 = 0,8553 — hệ quả đo được của việc bộ dữ liệu không đạt tiêu chí về tỉ lệ đối tượng nhỏ, được báo cáo tách bạch thay vì che sau một con số tổng.

Cần đọc con số cao này kèm điều kiện đã nêu ở Chương 5: đây là bài toán **một lớp** (chỉ phát hiện "biển số"), nên mAP@0.5 cao là điều bình thường và không nên bị hiểu là thành tựu vượt trội. Giá trị thật nằm ở chỗ mô hình đạt mức đó một cách nhất quán trên cả hai layout và ở độ phân giải 640 đúng chỉ tiêu.

### 6.2.3. Đo được đóng góp định lượng của khối hậu xử lý

Đây là **đóng góp khoa học riêng thứ nhất** của đồ án. Phần lớn công trình ALPR chỉ mô tả bước hậu xử lý một cách định tính ("có thêm một bước sửa lỗi bằng regex"), hiếm khi lượng hoá xem bước đó đóng góp bao nhiêu. Đồ án này đo tách bạch, hai lần trên cùng 2.801 biển có nhãn chuỗi:

- Độ chính xác chuỗi đầy đủ **trước** hậu xử lý (A5) = 0,6098;
- Độ chính xác chuỗi đầy đủ **sau** hậu xử lý (A6) = 0,6555;
- Hiệu số **A6 − A5 = +4,57 điểm phần trăm** — chính là đóng góp thuần của khối hậu xử lý theo luật.

Quan trọng hơn con số là **hình dạng** của đóng góp: bộ luật sửa đúng **128 biển** và làm hỏng **0 biển**. Đây là một cải thiện thuần một chiều — bằng chứng rằng bộ luật đủ bảo thủ để không tự tạo ra lỗi mới, đúng như thiết kế "sửa lỗi theo vị trí, có vùng cấm sửa" ở Chương 3. Đóng góp bị chặn ở mức nhỏ **không phải vì luật kém**, mà vì nút thắt độ chính xác nằm ở tầng OCR — nơi luật, vốn chỉ sửa được nhầm ký tự lẻ tẻ ở đúng vị trí, về bản chất không với tới được các chuỗi sai nhiều ký tự do engine đọc hụt cả cụm. Việc đóng góp là dương và không rủi ro, dù nhỏ, là một kết quả có giá trị tự thân: nó xác nhận thiết kế hậu xử lý đúng đắn về nguyên lý, và định vị chính xác rằng cải thiện lớn phải đến từ tầng khác.

### 6.2.4. Đo được rủi ro R-04 bằng số liệu Việt Nam thật

Đây là **đóng góp khoa học riêng thứ hai**, và có lẽ là đóng góp thực nghiệm đáng giá nhất. Rủi ro R-04 — "pipeline OCR dựng sẵn gãy trên biển hai dòng" — được xác định từ Phase 0 như một rủi ro *định tính*. Đồ án này biến nó thành một con số *đo được trên dữ liệu Việt Nam*. Tách theo layout (bảng T5.6c):

| Chỉ số | Biển một dòng (567 mẫu) | Biển hai dòng (2.234 mẫu) | Chênh lệch |
|---|---:|---:|---:|
| 1 − CER (mức ký tự) | 0,9900 | 0,8462 | 14,38 điểm |
| Chuỗi trước hậu xử lý (A5) | 0,9418 | 0,5255 | 41,63 điểm |
| Chuỗi sau hậu xử lý (A6) | 0,9489 | 0,5810 | **36,79 điểm** |

Biển **một dòng về cơ bản đã giải xong**: A6 = 0,9489 vượt mục tiêu 0,90, và 1 − CER = 0,9900. Toàn bộ khoảng thiếu của con số tổng nằm ở biển **hai dòng**, vốn chiếm **79,8%** tập có nhãn chuỗi — một tỉ lệ phản ánh trực tiếp mật độ xe máy áp đảo trong giao thông Việt Nam, nơi có tới 77 triệu xe máy [3]<!-- dantri_2024_77trieuxemay -->. Nói cách khác, quần thể khó nhất về mặt kỹ thuật lại là quần thể phổ biến nhất về mặt thực tế.

Chênh lệch **36,79 điểm** A6 giữa hai layout là một phát hiện có định vị rõ ràng, không phải một thất bại mơ hồ. Nó **cùng bậc độ lớn** với mốc tham chiếu quốc tế: Laroca và cộng sự (VISAPP 2022) đo chênh lệch **48,6 điểm** giữa biển một dòng (94,3%) và biển hai dòng (45,7%) trên bộ dữ liệu **RodoSol-ALPR của Brazil** [4]<!-- laroca_2022_crossdataset -->.

> **Cảnh báo trích dẫn bắt buộc, lặp lại theo đúng quy tắc của Chương 5.** Cặp số 94,3% / 45,7% và chênh lệch 48,6 điểm đo trên **RodoSol-ALPR (Brazil)** [4]<!-- laroca_2022_crossdataset -->, **không phải** số liệu Việt Nam. Nó chỉ được dùng như một *analogue định lượng* về độ khó tương đối của biển hai dòng, không bao giờ như một mốc chuẩn mà hệ thống này phải vượt. Con số 36,79 điểm mới là con số đo trên dữ liệu Việt Nam của đồ án.

Giá trị học thuật ở đây là lấp một khoảng trống cụ thể: chưa có nghiên cứu biển số Việt Nam công khai nào công bố hai con số một dòng / hai dòng **tách bạch trên cùng một hệ thống**. Kết luận rút ra — biển hai dòng là một *đặc tính có cấu trúc của bài toán* chứ không phải một lỗi cài đặt sửa nhanh được — đặt nền cho hướng phát triển trọng tâm ở mục 6.4.1, và cũng nhất quán với dòng nghiên cứu quốc tế coi tính độc lập với layout là một yêu cầu thiết kế riêng chứ không phải hệ quả miễn phí [5]<!-- laroca_2021_layout -->.

### 6.2.5. Bộ nhận màu nền biển đạt 97,89% — một nguồn bằng chứng mà chuỗi ký tự không thể mang

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

Hạn chế bắt buộc phải nêu kèm: bộ dữ liệu dùng để đo **không chứa biển đỏ và không chứa biển ngoại giao**, nên hai nhánh đó của bộ phân loại chưa có số đo. Xem mục 6.3.8.

### 6.2.6. Một quy trình đánh giá có kiểm chứng — bản thân tính trung thực là một kết quả

Đóng góp cuối trong nhóm này không phải một con số cao mà là **cách các con số được kiểm tra**. Trong quá trình đánh giá, năm lần quy trình tự bắt được lỗi hoặc ngộ nhận của chính nó, và cả năm đều được ghi lại thay vì che đi:

**(1) Phát hiện và sửa rò rỉ dữ liệu train↔test.** Bước khử trùng lặp ban đầu chạy ở ngưỡng gộp 5; kiểm tra lại phát hiện split cũ có hàng nghìn cặp ảnh gần trùng vắt qua ranh giới train↔test. Ngưỡng gộp được nâng lên 10 và bộ dữ liệu chia lại thành v3. Quan trọng hơn, việc rò rỉ được **đo ở nhiều ngưỡng cao hơn ngưỡng gộp** để phơi bày phần tồn dư thay vì tuyên bố "đã sạch" (xem tiếp mục 6.3.2).

**(2) Phát hiện một lập luận vòng tròn trong chính phép kiểm chứng rò rỉ.** Ở ngưỡng Hamming 10, tập v3 cho **0 cặp** vắt split. Thoạt nhìn đây có vẻ là bằng chứng "tập test sạch". Nhưng đó là một **hệ quả định nghĩa**, không phải một phát hiện thực nghiệm: v3 được *khử trùng lặp ở đúng ngưỡng 10*, nên đo lại rò rỉ ở ngưỡng 10 chắc chắn ra 0 — con số này không mang thông tin. Chỉ các ngưỡng **cao hơn** ngưỡng gộp (12, 15, 20) mới mang thông tin mới. Nhận ra và ghi rõ vòng lặp lý luận này quan trọng vì nó ngăn một tuyên bố sai ("đã kiểm chứng là sạch") lọt vào chương thực nghiệm.

**(3) Phát hiện phash chỉ nhận giá trị khoảng cách chẵn, khiến ngưỡng lẻ vô nghĩa.** Băm tri giác `phash` 64 bit trong cài đặt này sinh ra hash có **đúng 32 bit bằng 1** (so với trung vị). Với hai hash cùng có 32 bit 1, khoảng cách Hamming giữa chúng luôn bằng $64 - 2k$ với $k$ là số bit 1 trùng vị trí — tức **luôn là số chẵn**. Hệ quả: đặt ngưỡng lẻ (ví dụ 11 hay 13) cho kết quả **y hệt** ngưỡng chẵn liền trước, nên mọi ngưỡng lẻ là vô nghĩa và không được đưa vào bảng đo. Điều này cũng giải thích vì sao khoảng cách nhỏ nhất quan sát được (12) là một số chẵn — đó là tất yếu toán học của cách dựng hash, không phải một đặc điểm của dữ liệu.

**(4) Phát hiện bộ đo độ chính xác OCR không đi qua đường mã của sản phẩm.** Đây là phát hiện có hệ quả rộng nhất trong cả năm, vì nó không nói về một con số cụ thể mà về **toàn bộ cách đồ án đo chính mình**. Script `ai/evaluation/ocr_accuracy.py` — nơi sinh ra các chỉ số NFR-A4 đến A7 công bố ở Chương 5 — gọi thẳng bộ nhận dạng và bộ chuẩn hoá, **không dựng `ALPRPipeline`**. Hệ quả logic: mọi logic đặt ở tầng điều phối đều **vô hình** đối với các con số công bố. Phát hiện xảy ra khi cài đặt bước cứu biển hai dòng (mục 4.2.5f): nếu bước cứu được viết như một phương thức riêng của pipeline — cách viết tự nhiên nhất — thì chương thực nghiệm sẽ đo một đường mã mà sản phẩm thật **không chạy**, và sẽ báo cáo một hệ thống kém hơn hệ thống đang giao. Bản sửa là tách bước cứu thành hai hàm tự do dùng chung (`should_rescue_two_line`, `rescue_two_line_upper` trong `ai/inference/pipeline.py`) để cả hai bên gọi cùng một đường. Điều cần nhấn mạnh khi bảo vệ: khoảng cách này **không gây lỗi, không sinh cảnh báo** và không bị bộ kiểm thử kiến trúc nào bắt được — nó chỉ lộ ra khi có người đối chiếu đường mã của bộ đo với đường mã của sản phẩm. Ranh giới giữa *hệ thống* và *phép đo hệ thống* vì vậy cũng là một ranh giới kiến trúc, và hiện chưa có cơ chế tự động nào canh giữ nó.

**(5) Một giả thuyết sửa lỗi hợp lý bị chính dữ liệu bác bỏ.** Khi biển `29E-015.66` bị đọc thành `015.66`, giả thuyết hiển nhiên là bỏ phép ghép hai nửa và đọc riêng từng nửa rồi nối chuỗi. Giả thuyết này đủ hợp lý để không thể bác bỏ bằng lập luận, nên nó được đo trên 200 biển hai dòng: cách đọc riêng đạt **3,5%** so với **64,5%** của cách ghép hiện hành — thắng ở 0/200 ảnh (`docs/reports/15-two-line-ab.json`). Nguyên nhân hoá ra nằm ở chính chi tiết thiết kế tưởng như không liên quan: hai nửa được cắt **chồng lấn có chủ ý**, nên khi đọc rời, dải chồng lấn bị đọc hai lần và sinh ký tự rác (`84G122593` ra thành `84-G124E009.01225.93`). Phép bác bỏ vì thế mang lại nhiều hơn một câu trả lời "không": nó phơi bày rằng phép ghép ngang còn giữ một vai trò thứ hai chưa từng được nhận ra — **trao cho bộ phát hiện văn bản cơ hội loại bỏ vùng chồng lấn**. Bản sửa cuối cùng do đó *giữ nguyên* thiết kế cũ và chỉ vá điểm mù của nó, với cổng kích hoạt đặt sau kiểm tra định dạng nên **không thể làm giảm độ chính xác về mặt cấu trúc** — đo trên 900 biển qua hai mẫu độc lập: 0 ca hỏng.

Ngoài năm lần trên, quy trình còn **bác bỏ một con số độ trễ cũ** (mục 6.3.4 và 5.7.1): báo cáo trước đây từng ghi p95 = 5.857 ms và kết luận NFR-P1 không đạt; truy nguyên cho thấy phép đo đó bị nhiễm tranh chấp CPU (một tiến trình huấn luyện chạy song song) và đo trên sai checkpoint có lỗi crop, nên đã bị loại và đo lại đúng cách. Sáu sự việc này gộp lại tạo thành một đóng góp phương pháp luận: **một chương đánh giá chỉ trưng ra các con số đẹp và không kể lại lần nào nó tự nghi ngờ chính mình là một chương đã tự tước bỏ khả năng bị kiểm chứng.**

---

## 6.3. Các hạn chế của đồ án

Mục này là phần quan trọng nhất của chương, và được viết theo nguyên tắc của mục 5.11.3: **nêu hạn chế, đánh giá mức nghiêm trọng, nói rõ đã làm gì để giảm thiểu — kể cả khi câu trả lời là "chưa làm được gì".**

### 6.3.1. Hạn chế lớn nhất: OCR biển hai dòng còn yếu, kéo E2E chưa đạt

*Mức nghiêm trọng: cao. Đây là hạn chế trung tâm của toàn đồ án.*

Bốn chỉ tiêu độ chính xác OCR đều không đạt:

- NFR-A4 (1 − CER) = **0,8734**, thiếu 4,66 điểm so với ngưỡng tối thiểu 0,92;
- NFR-A5 (chuỗi trước hậu xử lý) = **0,6098**, thiếu 19 điểm so với ngưỡng 0,80;
- NFR-A6 (chuỗi sau hậu xử lý) = **0,6555**, thiếu 19,45 điểm so với ngưỡng 0,85;
- NFR-A7 (E2E toàn trình) = **0,5227**, thiếu 29,73 điểm so với ngưỡng 0,82.

Điều phải nói thẳng — và cũng là điều làm cho hạn chế này *có thể hành động được* thay vì mơ hồ — là **nguyên nhân đã được định vị bằng số liệu, và nó nằm ở tầng OCR, không phải tầng hậu xử lý**. Ba bằng chứng độc lập cùng chỉ về một chỗ:

1. **Tách theo layout** (T5.6c): trên biển một dòng, hệ thống đạt hoặc vượt ngưỡng (A6 = 0,9489); toàn bộ khoảng thiếu nằm ở biển hai dòng (A6 = 0,5810). Vì biển hai dòng chiếm 79,8% tập, con số tổng bị quần thể này chi phối.
2. **Phân tích lỗi** (T5.10): trong 376 ca nhầm ký tự, **358 ca** thuộc biển hai dòng; trong 217 ca thiếu ký tự, **216 ca** thuộc biển hai dòng. Lỗi tập trung gần như tuyệt đối ở một layout.
3. **Đóng góp hậu xử lý bị chặn** (T5.6b): khối luật chỉ thêm được +4,57 điểm vì nó sửa được nhầm ký tự lẻ tẻ nhưng bất lực trước chuỗi sai nhiều ký tự khi OCR đọc hụt cả cụm. Nếu lỗi là ở hậu xử lý, tăng luật sẽ cứu được; thực tế là không, vì lỗi ở tầng dưới.

Kết luận: **hướng khắc phục bắt buộc nằm ở tầng nhận dạng — huấn luyện hoặc thay mô hình OCR chuyên cho biển số hai dòng — chứ không ở tầng hậu xử lý** (triển khai ở mục 6.4.1). Việc trút thêm luật vào `plate_rules.py` sẽ không đụng đến nút thắt thật.

**Một cảnh báo hiệu lực về con số A7 = 0,5227.** Con số này đo trên ảnh **crop biển số** — ngoài phân bố huấn luyện của bộ phát hiện — nên tỉ lệ bỏ sót 11,96% bị thổi phồng và A7 phải đọc như **cận dưới bi quan**, không phải ước lượng điểm. Lập luận và số liệu đầy đủ ở **mục 5.6.5**; đo A7 đúng cách đòi hỏi một tập test hiện trường có nhãn chuỗi, việc chưa làm được (mục 6.4.3).

### 6.3.2. Rò rỉ dữ liệu tồn dư không khử được bằng băm tri giác

*Mức nghiêm trọng: cao.*

Như mục 6.2.6 đã nêu, bước khử trùng lặp đã chạy đúng đặc tả ở ngưỡng gộp 10. Nhưng điều đó **không** đồng nghĩa tập test tách sạch khỏi tập train. Đo ở các ngưỡng cao hơn ngưỡng gộp phơi bày phần tồn dư có thật, đo được: ngay ngoài vùng bảo vệ của ngưỡng 10, tại ngưỡng Hamming **12** vẫn còn **791 cặp** ảnh gần trùng train↔test, và tại ngưỡng **15** là **3.529 cặp**. Nghĩa là tập test **không** hoàn toàn độc lập với tập train ở mức bố cục sáng-tối.

Nghiêm trọng hơn là loại rò rỉ mà **không ngưỡng phash nào bắt được**: hai ảnh của *cùng một chiếc xe* chụp ở góc khác nhau, hoặc hai khung hình cách nhau vài giây trong cùng một video, mang **cùng một biển số** nhưng có khoảng cách Hamming lớn. Đây là rò rỉ ở mức **ngữ nghĩa**, và phash — vốn chỉ đo tương đồng bố cục — mù trước nó. Chính vì thế, kết quả phash thấp ở ngưỡng gộp **không chứng minh** tập test độc lập.

*Biện pháp giảm thiểu đã áp dụng:* nâng ngưỡng gộp từ 5 lên 10, và đo rò rỉ ở nhiều ngưỡng cao hơn để phơi bày phần tồn dư thay vì che nó. *Biện pháp triệt để chưa áp dụng được:* chia split **theo nhóm biển số** (mọi ảnh của cùng một biển phải nằm cùng một phía của split) — bất khả thi ở hiện tại vì phần lớn corpus thiếu nhãn chuỗi để nhóm. **Hệ quả bắt buộc phải nêu khi bảo vệ: mọi chỉ số ở tầng phát hiện và OCR phải được coi là cận trên lạc quan.**

### 6.3.3. Tập test không xuyên bộ dữ liệu, nên mAP lạc quan hơn khi triển khai

*Mức nghiêm trọng: cao.*

Tập train và tập test được lấy từ **cùng sáu nguồn nguyên tố** đã hợp nhất. Thiết lập này đo được năng lực tổng quát hoá *trong phân bố*, nhưng **không** đo được năng lực tổng quát hoá *xuyên phân bố* — vốn mới là thứ quyết định khi triển khai trên camera mới, địa điểm mới, điều kiện chiếu sáng mới. Tài liệu đã chỉ ra rằng độ chính xác ALPR sụt giảm đáng kể khi đánh giá xuyên bộ dữ liệu [4]<!-- laroca_2022_crossdataset -->. Do đó con số mAP@0.5 = 0,9829 gần như chắc chắn **lạc quan hơn** hiệu năng thực tế khi gặp phân bố ảnh chưa từng thấy.

*Biện pháp giảm thiểu:* không có trong khuôn khổ đồ án. Cách đúng là giữ lại một nguồn hoàn toàn không dùng để huấn luyện làm tập test xuyên bộ; điều này chưa thực hiện và chuyển thành hướng phát triển ở mục 6.4.2.

### 6.3.4. Độ trễ — đã đạt sau khi giải quyết mâu thuẫn số liệu

*Kết luận: NFR-P1 ĐẠT. Ghi lại đầy đủ vì đây là một mâu thuẫn từng tồn tại và đã được giải quyết, không được lờ đi.*

NFR-P1 **đạt mục tiêu**: độ trễ E2E một ảnh, p95 = **731,15 ms**, dưới mục tiêu 800 ms (dư 68,85 ms) và thoả cả ngưỡng tối thiểu 1.500 ms. Con số công bố này đo **client-side qua HTTP** trên `best.pt`, máy rảnh (CPU idle ~5%, không có tiến trình huấn luyện chạy song song), warmup rồi đo 100 ảnh test v3. Một phép đo độc lập **in-process** (gọi thẳng pipeline trong tiến trình) cho p95 = **780,36 ms** — hai con số **đồng thuận trong phạm vi ~7%** (biến động lấy mẫu CPU), cùng khẳng định độ trễ E2E thật ở khoảng **700–780 ms**.

Phải ghi lại vì sao con số này từng bị nghi ngờ. Một báo cáo trước đây ghi p95 = **5.857 ms** và kết luận NFR-P1 "không đạt" — chênh **7,5 lần** so với con số hiện tại. Phép đo cũ đã bị **bác bỏ** vì điều kiện đo bị nhiễm, chứ không vì mô hình chậm; toàn bộ quá trình truy nguyên (ba nguyên nhân, và việc loại tường minh hai giả thuyết thay thế) trình bày ở **mục 5.7.1**.

Phân rã ngân sách độ trễ thật (T5.7b): OCR chiếm **64,3%** (112,55 ms/biển), phát hiện chiếm **34,2%** (59,83 ms) — **không** phải tỉ lệ 93,3% / 6,7% của báo cáo cũ. Kết luận: kiến trúc phần mềm và độ trễ **không phải vấn đề**; tối ưu thêm là tuỳ chọn chứ không bắt buộc (mục 6.4.4).

### 6.3.5. Nút "Huỷ tác vụ" video chưa hoàn chỉnh; một số chỉ tiêu chưa đo

*Mức nghiêm trọng: trung bình đến thấp, tuỳ hạng mục.*

Có hai nhóm khiếm khuyết cần thừa nhận rõ ràng, tránh để người đọc tự phát hiện khi bảo vệ.

**Một chức năng cài đặt lệch khỏi thiết kế.** Thiết kế ở Chương 3 mô tả khả năng huỷ một tác vụ xử lý video đang chạy. Bản cài đặt hiện tại **chưa có route HTTP nào đặt được trạng thái huỷ** — tài liệu OpenAPI đang chạy công bố 9 đường dẫn, không đường dẫn nào huỷ một tác vụ. Chức năng "Huỷ tác vụ" vì vậy chưa hoàn chỉnh ở tầng backend; đây là một hạng mục cài đặt còn treo, không phải một quyết định thiết kế.

**Bốn chỉ tiêu chưa đo, phân biệt rõ hai loại lý do:**

| Mã | Chỉ tiêu | Lý do chưa đo | Loại |
|:---:|---|---|---|
| P2 | FPS webcam | Chưa có kịch bản đo, cần kèm định nghĩa "FPS hiệu dụng" | Chưa tới lượt (khắc phục được) |
| P3 | Tốc độ xử lý video | Chưa có kịch bản đo | Chưa tới lượt (khắc phục được) |
| R5 | CSDL sống sót qua khởi động lại | Chưa chạy kịch bản khởi động lại | Chưa tới lượt (khắc phục được) |
| A9 | Tách theo điều kiện ảnh | **Bộ dữ liệu không có nhãn điều kiện ảnh** | Thiếu điều kiện (hạn chế thật) |

Sự phân biệt ở cột cuối là quan trọng: P2, P3, R5 chỉ là *chưa tới lượt đo* và khắc phục được bằng cách viết kịch bản; còn NFR-A9 là *không đo được vì thiếu nhãn* — đây mới là một hạn chế thật của công trình, chỉ khắc phục được bằng gán nhãn thủ công cho một tập con. Riêng P2, kịch bản đo sẽ gọi trực tiếp `POST /api/detect/frame`, vì trang Webcam của giao diện đã được gỡ theo quyết định thu gọn phạm vi ngày 2026-07-20 — một quyết định phạm vi có chủ đích, không phải một khiếm khuyết cài đặt; mã giao diện tương ứng còn nguyên trong lịch sử git.

### 6.3.6. Một yêu cầu mức *Must* (FR-4.1) đã bị đưa ra khỏi phạm vi

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

Điều cần nói ngay sau đó, để bức tranh không bị méo theo chiều ngược lại: **phần mất đi là màn hình hiển thị, không phải năng lực hệ thống.** Toàn bộ phép tính thống kê vẫn nằm trong `StatisticsService`, vẫn phơi ra qua `GET /api/statistics` với đầy đủ các chỉ số mà FR-4.1 và FR-4.2 đòi hỏi (tổng lượt, tổng biển số, độ tin cậy trung bình, thời gian xử lý trung bình, phân bố theo loại đầu vào, chuỗi số liệu theo ngày), vẫn nằm trong tài liệu OpenAPI đang phục vụ, và **vẫn có kiểm thử tích hợp** — `tests/integration/test_api_statistics.py` và `test_api_health.py` đều nằm trong bộ 913 test. Không một endpoint nào bị xoá. Sáu yêu cầu FR-4.3 đến FR-4.8 (lịch sử, tìm kiếm, lọc, chi tiết, tải về, sắp xếp) không đổi mức và vẫn dùng được đầy đủ trên trang Lịch sử.

*Đánh đổi thu được:* gỡ thư viện biểu đồ `recharts` cùng trang Tổng quan làm gói tải về của giao diện giảm từ khoảng **730 KB xuống 328,8 KB (−55%)**, và số mô-đun frontend giảm từ 60 xuống 48.

*Biện pháp giảm thiểu đã áp dụng:* mã nguồn của cả hai trang còn nguyên trong lịch sử git, và các kiểu dữ liệu `Statistics`, `StatisticsQuery`, `HealthStatus`, `InputTypeBreakdown` được **giữ lại có chủ đích** trong `frontend/src/types/index.ts` để hợp đồng của phần API còn sống không bị mất theo trang. Việc khôi phục vì vậy là một thao tác phục hồi có chi phí thấp, không phải xây mới — triển khai ở mục 6.4.6.

### 6.3.7. SQLite chỉ cho phép một tiến trình ghi tại một thời điểm

*Mức nghiêm trọng: thấp trong phạm vi đồ án, cần nêu vì là câu hỏi phản biện dễ gặp.*

Hệ thống dùng SQLite cho lớp dữ liệu. SQLite khoá ghi ở mức toàn tệp: chỉ **một tiến trình ghi tại một thời điểm**. Với bối cảnh triển khai nội bộ, một người vận hành, mà đồ án nhắm tới (giả định A-04), đây không phải nút thắt — phép đo chịu tải cho thấy hệ thống xử lý ổn định 10 yêu cầu đồng thời và soak 300 giây thành công 100%. Nhưng nếu triển khai đa người dùng ghi đồng thời, giới hạn này sẽ trở thành thực. Hướng khắc phục là chuyển sang PostgreSQL (mục 6.4.7); nhờ đã dùng SQLAlchemy 2.0 như tầng trừu tượng, việc chuyển này không đụng đến mã nghiệp vụ.

### 6.3.8. Bộ dữ liệu lệch nặng về biển trắng, nên kết luận về độ chính xác OCR chỉ áp cho biển trắng

*Mức nghiêm trọng: cao. Đây là hạn chế quy định **phạm vi hiệu lực** của mọi con số OCR trong quyển này, nên phải đọc nó trước khi đọc bất kỳ con số nào ở Chương 5.*

Chạy bộ phân loại màu nền lên toàn bộ **2.801 ảnh biển số có nhãn ký tự** của đồ án — chính là tập sinh ra các chỉ số NFR-A4 đến A7 — cho phân bố sau (`docs/reports/17-plate-type-audit.json`):

| Loại biển | Số ảnh | Tỷ lệ |
|---|---:|---:|
| Trắng (dân sự) | 2.736 | **97,68%** |
| Vàng (kinh doanh vận tải) | 20 | 0,71% |
| Xanh (cơ quan Nhà nước) | 4 | 0,14% |
| Đỏ (Quân đội) | **0** | 0% |
| NG/QT (ngoại giao) | **0** | 0% |
| Không đọc được màu | 41 | 1,46% |

Hệ quả phải nói thẳng, và nó nghiêm khắc hơn vẻ ngoài của bảng: **con số độ chính xác OCR mà đồ án công bố thực chất là độ chính xác trên biển trắng.** Với 97,68% mẫu thuộc một lớp duy nhất, mọi chỉ số tổng hợp đều bị lớp đó chi phối gần như hoàn toàn. Câu phát biểu đúng khi bảo vệ là *"1 − CER = 0,8734 trên một tập gồm 97,7% biển trắng"*, không phải *"1 − CER = 0,8734 trên biển số Việt Nam"*. Đây là cùng một loại hạn chế phạm vi với mục 6.3.3 (tập test không xuyên bộ dữ liệu), chỉ khác trục: ở đó là trục nguồn ảnh, ở đây là trục loại biển.

Cần tách bạch hai điều rất dễ bị gộp làm một khi trả lời phản biện:

- **Hệ thống *có* năng lực phân loại loại biển.** Nó phân được chín giá trị `PlateKind` và bốn màu nền, và năng lực này **đã được kiểm chứng trên ảnh thật** — 97,89% trên 1.565 ảnh có nhãn màu do người gán (mục 6.2.5).
- **Hệ thống *chưa có dữ liệu* để đo độ chính xác **nhận dạng ký tự** cho các loại biển hiếm.** Với biển vàng (n = 20) và biển xanh (n = 4), mọi con số độ chính xác đều không có ý nghĩa thống kê; với biển đỏ và biển ngoại giao thì đơn giản là **không đánh giá được**, vì tập không chứa mẫu nào. Bộ dữ liệu dùng để đo màu ở mục 6.2.5 cũng **không** lấp được khoảng trống này: nó không chứa biển đỏ và không chứa biển ngoại giao.

Nói cách khác: **"chưa đo được" không đồng nghĩa với "không làm được", và cũng không được phép trình bày như thể đã đo được.**

*Biện pháp giảm thiểu đã áp dụng:* thực hiện kiểm kê định lượng nói trên thay vì để phân bố tiềm ẩn, và khảo sát các nguồn công khai có thể lấp từng loại biển thiếu (`docs/reports/17-plate-type-dataset-survey.md`). *Biện pháp chưa áp dụng được:* bổ sung chính các mẫu đó vào tập đánh giá — chuyển thành hướng phát triển ở mục 6.4.8.

Một ràng buộc kỹ thuật phát hiện trong quá trình khảo sát cần được ghi lại vì nó thu hẹp giá trị của nguồn bổ sung dồi dào nhất: bộ `nguyenluanai/license-plate-color` — nguồn duy nhất có sẵn 694 ảnh biển vàng — có **mọi ảnh bị kéo méo về khuôn 640×640** trước khi tải lên. Bộ này vì vậy **không dùng được để đánh giá OCR**, vì bước ước lượng số dòng của hệ thống dựa trên **tỷ lệ khung hình** và phép kéo phá huỷ đúng đại lượng đó. Màu nền thì không bị phép kéo làm thay đổi — nên bộ này trả lời được câu hỏi về màu và **chỉ** câu hỏi về màu, và nó đã được dùng đúng như vậy.

---

## 6.4. Hướng phát triển

Điểm chung của các hướng dưới đây: chúng **bắt nguồn từ số liệu Chương 5**, không phải từ một danh sách mong muốn chung chung. Thứ tự phản ánh mức ưu tiên do chính kết quả quyết định — hướng đầu tiên nhắm thẳng vào nút thắt thật.

### 6.4.1. Huấn luyện lại module nhận dạng (rec) riêng cho biển số Việt Nam — hướng quan trọng nhất

Mục 6.3.1 đã chứng minh bằng ba bằng chứng độc lập rằng nút thắt độ chính xác nằm ở **tầng OCR**, cụ thể là engine nhận dạng đọc hụt trên biển hai dòng. Do đó hướng phát triển có tác động lớn nhất — vượt xa mọi hướng còn lại — là **thay hoặc huấn luyện lại riêng module nhận dạng ký tự (rec)** cho biển số Việt Nam, thay vì dùng trọng số PaddleOCR đa mục đích pre-trained [2]<!-- cui_2026_ppocrv5 -->.

Có ít nhất bốn cách triển khai cụ thể, xếp theo mức đầu tư tăng dần:

1. **Fine-tune module rec của PaddleOCR trên biển số**, theo đúng công thức mà chính PaddleOCR đã trình bày cho bài toán biển số (fine-tune PP-OCR trên CCPD) [6]<!-- paddlepaddle_nd_plateapp -->. Đây là bước rẻ nhất, tận dụng lại hạ tầng hiện có.
2. **Dùng một mô hình rec hỗ trợ biển đa dòng ngay từ thiết kế.** Các mạng nhận dạng gần đây xử lý cả biển một dòng và hai dòng trong một mô hình thống nhất, chẳng hạn TransLPRNet cho biển một/hai dòng [7]<!-- arxiv_2025_translprnet --> hay LPTR-AFLNet tích hợp nắn chỉnh và nhận dạng nhẹ [8]<!-- xu_2025_lptraflnet -->. Hướng này giải quyết biển hai dòng ở gốc thay vì vá bằng hậu xử lý.
3. **Tách–ghép biển hai dòng trước khi đưa vào rec.** Cách tiếp cận đã được cộng đồng biển số Trung Quốc dùng: cắt nửa trên và nửa dưới rồi ghép ngang thành một dòng để engine một dòng đọc [9]<!-- we0091234_nd_doubleplatesplit -->. Rẻ về huấn luyện nhưng nhạy với chất lượng tách.
4. **Huấn luyện một mô hình nhận dạng chuyên biệt cho biển số Việt Nam từ đầu**, ví dụ theo kiểu CRNN kèm cơ chế chú ý đã được chứng minh trên biển Việt Nam [10]<!-- dang_2024_crnn -->, hoặc các pipeline chuyên xe máy Việt Nam [11]<!-- le_2023_vnmotorcycle -->. Đây là hướng tốn công nhất nhưng có trần chất lượng cao nhất, và phù hợp nhất với đặc thù ký tự và bố cục biển Việt Nam.

Ràng buộc kiến trúc thuận lợi: nhờ NFR-M5, việc thay module rec **không đụng đến mã tầng API** — chỉ cần cài lại giao diện `PlateRecognizer`. Đây chính là lý do khoản đầu tư kiến trúc "tầng AI thay thế được" từ đầu dự án nay sinh lời.

**Một bằng chứng bổ sung, thu được sau khi Chương 5 đã đo xong, củng cố thứ tự ưu tiên này.** Bước cứu dòng trên cho biển hai dòng (mục 4.2.5f, và mục 6.2.6 điểm (5)) là một can thiệp ở **tầng điều phối**, được thiết kế đúng theo chẩn đoán ở mục 6.3.1 và có tính chất bảo đảm không làm hỏng biển nào. Nó vẫn chỉ thu được **+1,86 điểm** trên mẫu 700 biển hai dòng và **+0,5 điểm** trên mẫu 200 (`docs/reports/15-two-line-fallback-700.json`, `15-two-line-fallback.json`) — cứu được 13 và 1 ảnh, làm hỏng 0. Con số nhỏ này **không** phải dấu hiệu bước cứu được thiết kế kém; nó là một phép đo nữa về trần của mọi can thiệp nằm **ngoài** mô hình nhận dạng. Cộng với trần của khối hậu xử lý theo luật (+4,57 điểm, mục 6.2.3), hai phép đo độc lập cùng nói một điều: phần độ chính xác còn thiếu **không nằm ở nơi có thể vá bằng luật hay bằng điều phối**. Bất kỳ mức cải thiện đáng kể nào cũng phải đến từ chính module rec — và mục 6.4.3 (bổ sung nhãn chuỗi) là điều kiện tiên quyết để làm được điều đó.

### 6.4.2. Xây dựng tập test xuyên bộ dữ liệu

Để chữa hạn chế 6.3.3, cần một quy trình đánh giá đo được tổng quát hoá *xuyên phân bố*. Cách làm: **giữ nguyên một nguồn hoàn toàn không dùng để huấn luyện**, chỉ dùng làm tập test xuyên bộ; báo cáo hai con số song song — mAP trong phân bố (như hiện tại) và mAP xuyên bộ — để người đọc thấy khoảng cách giữa chúng. Đây là cách chuẩn mực mà tài liệu cross-dataset khuyến nghị [4]<!-- laroca_2022_crossdataset -->. Kết hợp với việc **chia split theo nhóm biển số** (mọi ảnh cùng một biển nằm cùng một phía) sẽ khử được cả rò rỉ ngữ nghĩa mà phash không bắt được ở 6.3.2.

### 6.4.3. Bổ sung nhãn chuỗi biển số cho toàn tập

Hiện chỉ **2.801** biển trong tập đánh giá có nhãn chuỗi ký tự, trong khi corpus có 15.133 ảnh phần lớn chỉ có nhãn hộp giới hạn. Mẫu số nhỏ này là một mối đe doạ đến tính hợp lệ (mục 5.11.3) và cũng là thứ chặn việc đo NFR-A7 đúng cách trên ảnh hiện trường (mục 6.3.1). Hướng khắc phục là **gán nhãn chuỗi cho một phân bố hiện trường** đủ lớn, cho phép: (i) đo A7 trên ảnh toàn cảnh thay vì ảnh crop ngoài phân bố; (ii) chia split theo nhóm biển; (iii) có đủ dữ liệu để fine-tune module rec ở 6.4.1. Chi phí gán nhãn có thể giảm bằng bán tự động — dùng chính hệ thống hiện tại sinh nhãn nháp rồi người soát lại — hoặc bổ sung dữ liệu tổng hợp và dữ liệu thật theo hướng hợp nhất đa nguồn đã được nghiên cứu [12]<!-- arxiv_2026_multinationalfusion -->.

### 6.4.4. Tăng tốc suy luận: lượng tử hoá OCR, đóng gói ONNX/OpenVINO cả hai tầng

Dù NFR-P1 đã đạt (6.3.4), phân rã ngân sách cho thấy còn dư địa: OCR chiếm 64,3% và phát hiện 34,2% thời gian suy luận. Ba hướng tối ưu, không còn bắt buộc nhưng đáng làm nếu nhắm phần cứng yếu hơn:

- **Lượng tử hoá INT8 module OCR** với một tập hiệu chuẩn, tận dụng tập lệnh vector VNNI/AVX-512 trên CPU Intel [13]<!-- onnxruntime_2025_quantization -->. Vì OCR là phần chiếm thời gian lớn nhất, tối ưu ở đây có đòn bẩy cao nhất.
- **Đóng gói cả hai tầng sang ONNX Runtime hoặc OpenVINO.** Bộ phát hiện YOLO11 xuất sang OpenVINO tối ưu cho CPU Intel [14]<!-- ultralytics_2026_openvinoexport -->, và Ultralytics hỗ trợ hơn hai mươi định dạng xuất [15]<!-- ultralytics_2026_export -->. Hiện đường suy luận chạy PyTorch thuần; thí nghiệm so sánh backend (bảng T5.7c) là hạng mục đã chuẩn bị nhưng chưa chạy.
- Lưu ý phương pháp luận bắt buộc: mọi con số tăng tốc phải đo lại **trên cùng cấu hình phần cứng** và công bố kèm cấu hình, vì cả ONNX Runtime lẫn OpenVINO đều nhạy với kiến trúc CPU và cấu hình luồng cụ thể.

### 6.4.5. Bám vết đối tượng qua khung hình cho video (SORT/DeepSORT)

Hiện tại, khi xử lý video, hệ thống gộp các lần nhận dạng trùng theo **chuỗi ký tự** — cách này gãy khi OCR đọc sai cùng một biển ở các khung khác nhau thành các chuỗi khác nhau. Hướng đúng là **bám vết đối tượng qua khung hình** bằng thuật toán như SORT hoặc DeepSORT: gán một ID theo dõi ổn định cho mỗi xe/biển xuyên suốt các khung, rồi gộp theo ID thay vì theo chuỗi. Cách này vừa ổn định hơn trước lỗi OCR lẻ tẻ, vừa mở đường cho việc **bỏ phiếu theo thời gian** (chọn chuỗi xuất hiện nhiều nhất qua nhiều khung của cùng một track) để nâng độ chính xác video vượt độ chính xác từng khung.

Một hướng mở liên quan là **khôi phục giao diện thời gian thực** — trình bày chung với hướng khôi phục màn hình thống kê ở mục 6.4.6 ngay dưới đây, vì cả hai cùng một bản chất và cùng một cách làm.

### 6.4.6. Khôi phục hai màn hình đã gỡ, từ lịch sử git

Đây là hướng chữa trực tiếp cho hạn chế 6.3.6, và là hướng **rẻ nhất trong toàn bộ mục 6.4** — nó không đòi hỏi nghiên cứu, dữ liệu hay huấn luyện, chỉ đòi hỏi một quyết định về phạm vi.

Hai màn hình bị gỡ ngày 2026-07-20 — **Webcam** và **Tổng quan (Dashboard)** — đều nằm trong tình trạng giống nhau ở ba điểm, và chính ba điểm này làm cho việc khôi phục là *phục hồi* chứ không phải *xây mới*:

1. **Năng lực phía máy chủ chưa bao giờ bị gỡ.** `POST /api/detect/frame` phục vụ FR-3.x; `GET /api/statistics` và `GET /health` phục vụ FR-4.1/FR-4.2. Cả ba vẫn nằm trong tài liệu OpenAPI đang chạy và đều có kiểm thử tích hợp trong bộ 913 test.
2. **Mã giao diện còn nguyên trong lịch sử git** — gồm `pages/WebcamDetection.tsx` cùng cơ chế hàng đợi một khe mô tả ở mục 4.4.3, `pages/Dashboard.tsx`, cả thư mục `components/dashboard/`, hook `useApi.ts`, và các hàm `detectFrame` / `getStatistics` / `getHealth` trong `services/api.ts`.
3. **Hợp đồng kiểu vẫn được duy trì** trong `frontend/src/types/index.ts` (`DetectionResponse`, `Statistics`, `StatisticsQuery`, `HealthStatus`, `InputTypeBreakdown`), nên mã khôi phục sẽ biên dịch lại đúng vào cùng các kiểu mà backend đang trả về.

Quy trình khôi phục vì thế gồm ba bước: lấy lại tệp từ lịch sử git, nối lại route trong `App.tsx` và mục tương ứng trong thanh điều hướng, rồi chạy `tsc --noEmit` cùng `vite build` để xác nhận hợp đồng kiểu chưa trôi. Chỉ một điểm cần cân nhắc lại chứ không phục hồi nguyên trạng: **thư viện biểu đồ**. Việc gỡ `recharts` là thứ mang lại phần lớn mức giảm 730 KB → 328,8 KB, nên nếu dựng lại màn hình thống kê thì nên chọn một thư viện nhẹ hơn, hoặc nạp trễ (lazy-load) riêng phần biểu đồ để không kéo lại toàn bộ chi phí đã cắt được.

Cần đặt hướng này đúng chỗ trong thang ưu tiên: nó **khôi phục một chỉ tiêu đã cam kết** (FR-4.1 mức Must) chứ không nâng chất lượng nhận dạng. Nếu chỉ có thể làm một việc, mục 6.4.1 vẫn là việc đáng làm trước — nhưng nếu mục tiêu là tuyên bố đồ án đáp ứng đủ bộ yêu cầu *Must* ban đầu, thì đây là hướng duy nhất đưa được FR-4.1 trở lại.

### 6.4.7. Chuyển sang PostgreSQL nếu triển khai đa người dùng

Để chữa hạn chế 6.3.7, khi triển khai thực tế có nhiều người ghi đồng thời, nên chuyển lớp dữ liệu từ SQLite sang **PostgreSQL** — vốn hỗ trợ nhiều tiến trình ghi đồng thời và điều khiển đồng thời ở mức hàng. Nhờ toàn bộ truy cập dữ liệu đã đi qua SQLAlchemy 2.0 và tầng repository, việc chuyển đổi giới hạn ở lớp cấu hình kết nối và migration, **không** đụng đến mã nghiệp vụ hay mã API. Đây là một ví dụ nữa cho thấy các quyết định kiến trúc bảo thủ ở đầu dự án (dùng ORM thay vì SQL thô, tách repository khỏi service) trả cổ tức ở giai đoạn mở rộng.

### 6.4.8. Thu thập dữ liệu cho các loại biển hiếm — điều kiện để mở rộng phạm vi kết luận

Hướng này chữa trực tiếp hạn chế 6.3.8, và điểm đáng chú ý của nó là **nó không đòi hỏi thay đổi gì trong hệ thống**: năng lực phân loại chín họ biển và bốn màu nền đã có sẵn và đã được kiểm chứng (mục 6.2.5). Thứ còn thiếu là **dữ liệu để đo**, không phải mã để chạy. Vì vậy đây là hướng có tỷ lệ *mở rộng phạm vi kết luận trên một đơn vị công sức* cao nhất trong mục 6.4.

Ba việc cụ thể, xếp theo mức khó tăng dần:

1. **Biển vàng — đã có nguồn, cần xử lý đúng.** Bộ `nguyenluanai/license-plate-color` (CC BY 4.0) cung cấp 694 ảnh biển vàng, gấp khoảng 35 lần số hiện có, và **tên tệp đã chứa sẵn chuỗi biển số** nên nhãn ký tự gần như miễn phí. Trở ngại duy nhất là phép kéo méo về 640×640 nêu ở mục 6.3.8; cách xử lý là lấy ảnh gốc từ nguồn thay vì bản đã kéo, sau đó soát lại nhãn bằng mắt trước khi công bố bất kỳ con số nào.
2. **Biển đỏ quân đội và biển ngoại giao — cần chuyển từ "0 mẫu" sang "đo được".** Khảo sát ở `docs/reports/17-plate-type-dataset-survey.md` đã xác định được nguồn công khai chứa hai loại này, nhưng ở quy mô rất nhỏ (khoảng một trăm ảnh gốc biển đỏ, và chỉ khoảng mười tám ảnh gốc biển ngoại giao). Quy mô đó **đủ để có một tập kiểm thử báo cáo được** — thứ hiện đang bằng không — nhưng **không đủ để huấn luyện**, và sự phân biệt này phải được giữ nguyên khi báo cáo. Hai rủi ro bắt buộc xử lý trước khi nhập: các bản tăng cường trong nguồn bị chia lẫn giữa train/valid/test nên phải gom theo ảnh gốc rồi tự chia lại, và giấy phép của các nguồn này là do người đăng tự khai chứ không phải giấy phép của ảnh gốc.
3. **Biển chuyên dùng (LD, DA, RM, HC, KT, CD, T) — chưa tìm được nguồn nào.** Với nhóm này, con đường khả dĩ duy nhất là thu thập và gán nhãn tại chỗ, hoặc chấp nhận rằng chúng nằm ngoài phạm vi đánh giá và ghi rõ như vậy.

Cần đặt hướng này đúng vị trí trong thang ưu tiên: nó **không** nâng độ chính xác của hệ thống lên một điểm nào. Giá trị của nó là **mở rộng phạm vi mà các kết luận của đồ án có hiệu lực** — chuyển câu phát biểu từ *"đo trên một tập gồm 97,7% biển trắng"* sang một câu có phân tầng theo loại biển. Với một công trình mà đóng góp chính là *đo được những thứ trước đây chỉ được mô tả định tính*, việc mở rộng phạm vi hiệu lực của phép đo là một hướng phát triển đúng bản chất của công trình chứ không phải một việc phụ.

---

## 6.5. Kết luận chung

Đồ án đặt ra mục tiêu xây dựng một hệ thống nhận dạng biển số xe Việt Nam hoàn chỉnh, chạy trên CPU, hỗ trợ cả biển một dòng và hai dòng. Đối chiếu trung thực với mục tiêu đó, kết quả có thể tổng kết trong ba mệnh đề, không tô hồng và cũng không tự hạ thấp.

**Thứ nhất, hệ thống hoàn chỉnh và chạy được — điều này là chắc chắn, kiểm chứng được, không phải lời hứa.** Bốn tầng backend–frontend–AI–dữ liệu được đóng gói Docker, khởi động một lệnh, xác minh bằng HTTP sống và bằng stack Docker kiểm từ ngoài container. Bộ phát hiện đạt **toàn bộ** chỉ tiêu với biên rộng (mAP@0.5 = 0,9829, mAP@0.5:0.95 = 0,7834). Mọi chỉ tiêu hiệu năng, độ tin cậy và chịu tải đều đạt, gồm cả NFR-P1 (p95 = 731 ms) sau khi giải quyết một mâu thuẫn số liệu tồn đọng. Một điều chỉnh phải nói kèm ngay ở đây để mệnh đề này không bị đọc rộng hơn sự thật: giao diện web đã được thu gọn còn **ba màn hình** ngày 2026-07-20, và cùng đợt đó **một yêu cầu mức *Must* — FR-4.1, màn hình thống kê tổng hợp — bị đưa ra khỏi phạm vi** (mục 6.3.6). Năng lực tương ứng vẫn phục vụ và vẫn có kiểm thử ở tầng API, nhưng bộ yêu cầu *Must* mà hệ thống đáp ứng là bộ **21**, không phải bộ 22 ban đầu.

**Thứ hai, đồ án đo được hai đại lượng mà tài liệu Việt Nam chưa công bố tách bạch.** Đóng góp thuần của khối hậu xử lý theo luật — **+4,57 điểm**, 128 biển sửa đúng, 0 biển làm hỏng — được lượng hoá thay vì mô tả định tính. Và rủi ro R-04 được đo bằng **số liệu Việt Nam thật**: chênh lệch **36,79 điểm** độ chính xác chuỗi giữa biển một dòng và biển hai dòng, cùng bậc độ lớn với mốc 48,6 điểm mà Laroca và cộng sự đo trên RodoSol-ALPR của **Brazil** [4]<!-- laroca_2022_crossdataset --> — một analogue quốc tế, không phải số Việt Nam.

**Thứ ba, và phải nói thẳng: nhận dạng ký tự trên biển hai dòng vẫn là một bài toán mở.** Bốn chỉ tiêu độ chính xác OCR đều không đạt, và nguyên nhân đã được định vị chính xác — không phải ở tầng hậu xử lý, không phải ở tầng phát hiện, mà ở tầng nhận dạng ký tự trên quần thể biển hai dòng, vốn chiếm 79,8% dữ liệu vì phản ánh mật độ xe máy Việt Nam. Biển một dòng về cơ bản đã giải xong (A6 = 0,9489); biển hai dòng thì chưa (A6 = 0,5810). Đây là hạn chế trung tâm, và nó vạch sẵn hướng phát triển quan trọng nhất: huấn luyện lại module nhận dạng riêng cho biển số Việt Nam.

**Một điều kiện phạm vi phải đi kèm mệnh đề thứ ba, và nó cũng giới hạn cả mệnh đề thứ hai.** Tập 2.801 biển có nhãn chuỗi mà mọi con số OCR ở trên dựa vào gồm **97,68% biển trắng**, chỉ 20 biển vàng, 4 biển xanh, và **không một biển đỏ hay biển ngoại giao nào** (mục 6.3.8). Vì vậy các chỉ số A4–A7 phải được phát biểu là *"đo trên một tập gồm 97,7% biển trắng"*, không phải *"đo trên biển số Việt Nam"*. Hệ thống **có** năng lực phân loại chín họ biển và bốn màu nền — đã kiểm chứng ở 97,89% trên 1.565 ảnh có nhãn màu do người gán — nhưng **chưa có dữ liệu** để đo độ chính xác nhận dạng ký tự cho các loại biển hiếm. "Chưa đo được" không đồng nghĩa với "không làm được", và cũng không được trình bày như thể đã đo được.

Giá trị của đồ án vì vậy không nằm ở một con số state-of-the-art — điều mà Chương 1 đã cam kết ngay từ đầu là *không* tuyên bố. Nó nằm ở ba chỗ khác: **một hệ thống đầy đủ và tái lập được**; **ba đại lượng đo được mà trước đó chỉ được mô tả định tính** (đóng góp hậu xử lý, rủi ro R-04 trên dữ liệu Việt Nam, và độ chính xác của bộ nhận màu nền — nguồn bằng chứng duy nhất tách được biển vàng kinh doanh khỏi biển trắng cá nhân, thứ mà chuỗi ký tự về nguyên tắc không làm được); và **một quy trình đánh giá tự kiểm chứng** đã bắt được rò rỉ dữ liệu, một lập luận vòng tròn, một đặc tính toán học của phash, một con số độ trễ bị nhiễm, một giả thuyết sửa lỗi hợp lý bị chính dữ liệu bác bỏ, và — nghiêm trọng nhất — **một bộ đo đi tắt qua đường mã của chính sản phẩm nó đang đo** — rồi ghi lại tất cả thay vì che đi. Một hệ thống trung thực về giới hạn của chính mình, kèm một bản đồ số liệu chỉ rõ bước tiếp theo phải làm ở đâu, là một điểm khởi hành vững hơn nhiều so với một con số đẹp không kiểm chứng được.
