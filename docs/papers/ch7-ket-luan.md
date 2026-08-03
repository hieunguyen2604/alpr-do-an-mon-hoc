# CHƯƠNG 7. KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN

Chương này không đo lại chỉ tiêu nào của Chương 6: nó tổng kết sản phẩm đã làm ra, thừa nhận những gì chưa đạt cùng nguyên nhân đã định vị bằng số liệu, và chỉ ra hướng phát triển do chính kết quả thực nghiệm vạch sẵn. Ba nhóm số **không có ở Chương 6** — độ chính xác bộ nhận màu nền (7.2.5), kiểm kê loại biển của tập đánh giá (7.3.8), hiệu quả bước cứu biển hai dòng (7.4.1) — được đo **sau khi Chương 6 đã chốt**, mỗi con số kèm tệp báo cáo gốc. Nguyên tắc chi phối toàn chương là **không tô hồng**: hệ thống đạt chỉ tiêu ở tầng phát hiện và tầng phần mềm nhưng **không đạt ba chỉ tiêu độ chính xác OCR (A5, A6, A7; A4 chỉ đạt ngưỡng tối thiểu)**, nguyên nhân nằm gần như trọn vẹn ở quần thể biển hai dòng.

---

## 7.1. Tổng kết công việc đã thực hiện

### 7.1.1. Điểm lại mười một giai đoạn — mỗi giai đoạn một sản phẩm thật

| Giai đoạn | Sản phẩm thật đã bàn giao |
|:---:|---|
| **Phase 0 — Yêu cầu** | SRS, 34 yêu cầu chức năng, bảy nhóm yêu cầu phi chức năng, mọi chỉ tiêu **đo được bằng số**; chốt M0. |
| **Phase 1 — Nghiên cứu** | Bảy báo cáo khảo sát, 232 mục BibTeX qua kiểm chứng đối kháng, sửa 25 lỗi (3 critical, gồm căn cứ pháp lý TT 24/2023/TT-BCA đã hết hiệu lực); chốt M1. |
| **Phase 2 — Dữ liệu** | Bộ v3 **15.133 ảnh** từ bảy bộ tải về (**sáu nguồn nguyên tố** sau khử trùng lặp), train 10.592 / val 3.027 / test 1.514, ngưỡng gộp trùng lặp 10. |
| **Phase 3 — Phát hiện** | `models/best.pt` — YOLO11n [16]<!-- jocher_2024_yolo11 -->, 2.590.035 tham số, `imgsz=640`, 20 epoch trên CPU — mAP@0.5 = 0,9829 trên test v3. |
| **Phase 4 — OCR** | PaddleOCR PP-OCRv5 mobile [17]<!-- cui_2026_ppocrv5 --> cộng luật hậu xử lý theo vị trí; đóng góp thuần **+11,39 điểm** trên 2.801 biển có nhãn chuỗi. |
| **Phase 5 — Backend** | FastAPI, **10 thao tác trên 9 đường dẫn**, `/health` trả `model_loaded: true`, Alembic migrate xong, Swagger đầy đủ; chốt M5. |
| **Phase 6 — Frontend** | React một trang, build sạch, khớp 10 thao tác API, năm màn hình lúc chốt phase; *2026-07-20 thu gọn hai đợt còn **ba màn hình**, năng lực giữ ở tầng API và vẫn có kiểm thử — **FR-4.1 mức Must ra khỏi phạm vi** (7.3.6).* |
| **Phase 7 — Kiểm thử** | **882 thu thập / 881 pass / 1 xfail / 0 fail / 0 skip** (2026-07-20, `docs/reports/13-refactor-result.json`); cuối cùng ngày **913 / 912 / 1 xfail / 0 fail**; gần nhất 2026-08-02 **1.001 / 1.000 / 1 xfail / 0 fail**; bao phủ tầng nghiệp vụ **87,7%**, trước đó Phase 7 đo 88,1% (`docs/reports/07-testing-report.md`). |
| **Phase 8 — Docker** | Hai image, `docker compose up` chạy trên máy sạch, kiểm bằng `curl` từ ngoài container; chốt M8. |
| **Phase 9 — Tài liệu** | Quyển đồ án: Chương 1–5 trước, Chương 6–7 sau khi có `best.pt` và số liệu. |
| **Phase 10 — Bảo vệ** | Khung 21 slide, poster, kịch bản demo, 56 câu hỏi phản biện dự kiến. |

> **Lưu ý tên gọi.** Thư mục `yolo_v3` là **phiên bản thứ ba của bộ dữ liệu**, không liên quan kiến trúc "YOLOv3"; mô hình dùng trong toàn đồ án là **YOLO11n** [16]<!-- jocher_2024_yolo11 -->, biến thể nano của họ YOLO thế hệ 11.

Trong Phase 5–7 hệ thống chạy bằng pipeline giả lập `StubPipeline` để kiểm thử backend, CSDL và giao diện **trước khi** có trọng số, đồng thời chứng minh NFR-M5 khả thi; nay `StubPipeline` **đã ra khỏi đường chạy chính**, phương án lùi khi thiếu trọng số là `UnavailablePipeline` vốn **ném lỗi** thay vì bịa biển số. Không con số nào trong quyển này do stub sinh ra.

### 7.1.2. Bảng đối chiếu mục tiêu Phase 0 với kết quả thật

**Bảng 7.1.** Đối chiếu chỉ tiêu cam kết ở Phase 0 với số đo trên `best.pt` (bản cô đọng của T6.7)

| Mã | Chỉ tiêu | Mục tiêu Phase 0 | Đo được (`best.pt`) | Kết quả |
|:---:|---|---:|---:|:---:|
| A1 · A2 · A3-P · A3-R | mAP@0.5 · mAP@0.5:0.95 · Precision · Recall (phát hiện) | 0,90 · 0,65 · 0,92 · 0,90 | **0,9829 · 0,7834 · 0,9837 · 0,9714** | ✅ đạt |
| A4 | 1 − CER (mức ký tự) | 0,95 | **0,9454** | 🟡 đạt ngưỡng tối thiểu (0,92) |
| A5 | Chuỗi trước hậu xử lý | 0,85 | **0,6373** | ❌ không đạt |
| A6 | Chuỗi sau hậu xử lý | 0,90 | **0,7512** | ❌ không đạt |
| A6−A5 | Đóng góp hậu xử lý (điểm %) | — | **+11,39** | (thuần dương) |
| A7 | Độ chính xác E2E toàn trình | 0,88 | **0,5552** | ❌ không đạt* |
| A8 | Chênh lệch layout, phát hiện (điểm %) | — | **2,09** | (rất nhỏ) |
| P1 | Độ trễ E2E một ảnh, p95 (ms) | ≤ 800 | **1.143,10** | 🟡 đạt ngưỡng tối thiểu (1.500) |
| P4 · P5 · P6 | Nạp mô hình (s) · Overhead API p95 (ms) · Truy vấn 10.000 bản ghi p95 (ms) | ≤ 15 · ≤ 50 · ≤ 500 | **6,41 · 19,01 · 18,71** | ✅ đạt |
| P7a · P7b | RSS pipeline · RSS máy chủ backend (GB) | ≤ 2 · ≤ 2 | **0,759 · 0,806** | ✅ đạt |
| R4 · SC1 | Thành công khi chạy liên tục · Yêu cầu đồng thời ổn định | ≥ 99% · ≥ 5 | **100%** (2.028 yêu cầu, soak 15 phút) · **10** | ✅ đạt |
| M2 | Bao phủ test tầng nghiệp vụ | — | **87,7%** (2026-07-20, 881/882 pass, 1 xfail); cuối cùng ngày 912/913; Phase 7 trước đó 88,1% | (tham chiếu) |

\* A7 = 0,5552 phải đọc như **cận dưới bi quan**: nó đo trên ảnh crop biển số, ngoài phân bố huấn luyện của bộ phát hiện, nên tỉ lệ bỏ sót bị thổi phồng (7.3.1).

Hình mẫu của bảng là câu chuyện của đồ án: **mọi chỉ tiêu phát hiện, độ tin cậy và chịu tải đều đạt, thường với biên rộng; mọi chỉ tiêu độ chính xác OCR chuỗi đầy đủ đều không đạt** — vạch ngăn "đạt / không đạt" trùng khít vạch ngăn giữa tầng phát hiện và tầng nhận dạng ký tự. Riêng NFR-P1 chỉ đạt ngưỡng tối thiểu và NFR-P2 trượt cả sàn (7.3.4, 7.3.5), cùng nguyên nhân là đuôi độ trễ của bậc thang thử-lại và cùng một đánh đổi có chủ ý lấy 34 biển đọc thêm; nói "mọi chỉ tiêu hiệu năng đều đạt" sẽ là một khẳng định sai.

---

## 7.2. Các kết quả đạt được

### 7.2.1. Một hệ thống hoàn chỉnh, chạy được, xác minh bằng HTTP thật

Backend FastAPI, frontend React, pipeline AI (`ALPRPipeline`) và lớp dữ liệu SQLite/SQLAlchemy được đóng gói Docker và khởi động bằng một lệnh `docker compose up` trên máy sạch, không cần Internet. Kiểm chứng: 10 thao tác API trên 9 đường dẫn phản hồi đúng qua HTTP sống; `/health` báo `model_loaded: true` với engine thật `yolo:best.pt + paddleocr-PP-OCRv5-mobile`; Alembic migrate hoàn tất; Swagger render đầy đủ; stack Docker kiểm bằng `curl` từ **ngoài** container. Ràng buộc "tầng AI không có mũi tên đi lên" kiểm chứng được bằng một lệnh `grep`; NFR-M5 được chứng minh bằng chính `StubPipeline` và `UnavailablePipeline` như hai bản cài của cùng một giao diện.

### 7.2.2. Bộ phát hiện đạt toàn bộ chỉ tiêu với biên rộng

Trên tập test v3 (1.514 ảnh, 1.611 đối tượng nhãn thật), YOLO11n [16]<!-- jocher_2024_yolo11 --> vượt **cả bốn** chỉ tiêu, và vượt *mục tiêu* chứ không chỉ *ngưỡng tối thiểu*: mAP@0.5 = **0,9829** (mục tiêu 0,90); mAP@0.5:0.95 = **0,7834** (mục tiêu 0,65); Precision = **0,9837**, Recall = **0,9714**, F1 = **0,9775**. Chênh lệch giữa hai layout chỉ **2,09 điểm** mAP@0.5 (một dòng 0,9884, hai dòng 0,9675), nên nếu độ chính xác toàn trình kém trên biển hai dòng thì lỗi **không** ở khâu phát hiện. Tách theo dải kích thước (T6.4c) phơi bày điểm yếu duy nhất: dải "rất nhỏ" (dưới 0,5% diện tích ảnh) chỉ đạt mAP@0.5 = **0,8553**, hệ quả đo được của việc bộ dữ liệu không đạt tiêu chí tỉ lệ đối tượng nhỏ. Đọc con số cao này kèm điều kiện đã nêu ở Chương 6: đây là bài toán **một lớp**, nên mAP@0.5 cao là bình thường.

### 7.2.3. Đo được đóng góp định lượng của khối hậu xử lý

**Đóng góp khoa học riêng thứ nhất.** Phần lớn công trình ALPR chỉ mô tả hậu xử lý một cách định tính; đồ án đo tách bạch trên cùng 2.801 biển có nhãn chuỗi: A5 (trước) = 0,6373, A6 (sau) = 0,7512, **A6 − A5 = +11,39 điểm phần trăm**. Bộ luật sửa đúng **319 biển**, làm hỏng **0 biển**, và dồn gần trọn vào biển hai dòng (**+13,97 điểm** so với **+1,23 điểm** ở biển một dòng) — đúng nơi tầng nhận dạng yếu nhất, và cải thiện thuần một chiều là bằng chứng bộ luật đủ bảo thủ để không tự tạo lỗi mới. Đóng góp bị chặn ở mức nhỏ **không phải vì luật kém** mà vì nút thắt ở tầng OCR: luật không với tới chuỗi sai nhiều ký tự do engine đọc hụt cả cụm.

### 7.2.4. Đo được rủi ro R-04 bằng số liệu Việt Nam thật

**Đóng góp khoa học riêng thứ hai.** Rủi ro R-04 — "pipeline OCR dựng sẵn gãy trên biển hai dòng" — vốn là rủi ro *định tính* từ Phase 0, nay thành con số *đo được trên dữ liệu Việt Nam* (T6.5c):

| Chỉ số | Biển một dòng (567 mẫu) | Biển hai dòng (2.234 mẫu) | Chênh lệch |
|---|---:|---:|---:|
| 1 − CER (mức ký tự) | 0,9925 | 0,9344 | 5,81 điểm |
| Chuỗi trước hậu xử lý (A5) | 0,9418 | 0,5600 | 38,18 điểm |
| Chuỗi sau hậu xử lý (A6) | 0,9541 | 0,6996 | **25,45 điểm** |

Biển **một dòng về cơ bản đã giải xong** (A6 = 0,9541 vượt mục tiêu 0,90); toàn bộ khoảng thiếu nằm ở biển **hai dòng**, chiếm **79,8%** tập có nhãn chuỗi — tỉ lệ phản ánh mật độ xe máy áp đảo ở Việt Nam, nơi có tới 77 triệu xe máy [1]<!-- dantri_2024_77trieuxemay -->: quần thể khó nhất về kỹ thuật lại phổ biến nhất trong thực tế. Chênh lệch **25,45 điểm** A6 **cùng bậc độ lớn** với mốc quốc tế: Laroca và cộng sự (VISAPP 2022) đo chênh lệch **48,6 điểm** giữa biển một dòng (94,3%) và hai dòng (45,7%) trên bộ dữ liệu **RodoSol-ALPR của Brazil** [7]<!-- laroca_2022_crossdataset -->.

> **Cảnh báo trích dẫn bắt buộc, theo đúng quy tắc của Chương 6.** Cặp số 94,3% / 45,7% và chênh lệch 48,6 điểm đo trên **RodoSol-ALPR (Brazil)** [7]<!-- laroca_2022_crossdataset -->, **không phải** số liệu Việt Nam. Nó chỉ dùng như *analogue định lượng* về độ khó tương đối của biển hai dòng, không bao giờ như mốc chuẩn mà hệ thống này phải vượt. Con số 25,45 điểm mới là số đo trên dữ liệu Việt Nam của đồ án.

Giá trị học thuật là lấp một khoảng trống cụ thể: chưa nghiên cứu biển số Việt Nam công khai nào công bố hai con số một dòng / hai dòng **tách bạch trên cùng một hệ thống**. Kết luận — biển hai dòng là *đặc tính có cấu trúc của bài toán* chứ không phải lỗi cài đặt sửa nhanh được — đặt nền cho 7.4.1, nhất quán với dòng nghiên cứu coi tính độc lập với layout là yêu cầu thiết kế riêng [23]<!-- laroca_2021_layout -->.

### 7.2.5. Bộ nhận màu nền biển đạt 97,89% — một nguồn bằng chứng mà chuỗi ký tự không thể mang

**Đóng góp kỹ thuật riêng thứ ba**, và nó **bổ sung một năng lực hệ thống trước đó không có**. Theo Thông tư 79/2024/TT-BCA, biển vàng xe kinh doanh vận tải mang **đúng cùng bố cục ký tự** với biển trắng xe cá nhân (`29E-015.66` hợp lệ cho cả hai) nên **khác biệt không nằm trong chuỗi**; ngược lại biển ngoại giao có nền trắng như biển cá nhân nên màu cũng không đủ — chỉ *cặp* (chuỗi, màu) mới định danh được loại phương tiện.

`ai/inference/plate_color.py` đọc màu nền bằng biểu đồ HSV trên **vùng giữa ảnh cắt** (18% mỗi biên bị loại vì khung phát hiện thường lỏng), trả `unknown` khi không dải màu nào chiếm đủ 30% vùng lấy mẫu. Đo trên bộ `nguyenluanai/license-plate-color` v4 (CC BY 4.0) — bộ mà **bộ phân loại chưa từng được hiệu chỉnh theo**: vàng **98,56%** trên 694 ảnh, trắng **97,40%** trên 808 ảnh, xanh **96,83%** trên 63 ảnh, **tổng 97,89% trên 1.565 ảnh** (`docs/reports/19-color-accuracy.json`); 542 ảnh bị loại khỏi phép tính là toàn bộ lớp `bien_unknown` — ảnh đêm hoặc hồng ngoại lỗi cân bằng trắng mà **chính người gán nhãn cũng không đọc được màu nền**.

Ràng buộc an toàn của phép hợp nhất hai nguồn: chỉ khi chuỗi bó tay hoàn toàn — với `80A12345` bộ luật trả **bốn ứng viên ngang nhau** và tự đánh dấu nhập nhằng — màu mới được **nâng cấp một ứng viên mà chuỗi đã coi là hợp lý**, nên **biển quân đội bị đọc nhầm màu thì vẫn là biển quân đội**. Cùng đợt, họ biển (chín giá trị `PlateKind`) và chuỗi hiển thị đúng định dạng vật lý (`29E-015.66`) được giữ lại thay vì bị vứt đi trước khi tới CSDL, chữa được một phát biểu sai: biển đỏ quân đội đọc đúng ở độ tin cậy 0,999 từng bị hiển thị là **"Sai định dạng biển số"**. Hạn chế kèm theo: bộ dữ liệu đo **không chứa biển đỏ và không chứa biển ngoại giao**, nên hai nhánh đó **chưa có số đo** (7.3.8).

### 7.2.6. Một quy trình đánh giá có kiểm chứng — bản thân tính trung thực là một kết quả

Đóng góp cuối là **cách các con số được kiểm tra**: năm lần quy trình tự bắt lỗi hoặc ngộ nhận của chính nó, cả năm đều được ghi lại.

**(1) Rò rỉ dữ liệu train↔test.** Khử trùng lặp ban đầu chạy ở ngưỡng gộp 5; kiểm tra lại phát hiện split cũ có hàng nghìn cặp ảnh gần trùng vắt qua ranh giới. Ngưỡng nâng lên 10, dữ liệu chia lại thành v3, và rò rỉ được **đo ở nhiều ngưỡng cao hơn ngưỡng gộp** thay vì tuyên bố "đã sạch" (7.3.2).

**(2) Một lập luận vòng tròn trong chính phép kiểm chứng rò rỉ.** Ở ngưỡng Hamming 10, v3 cho **0 cặp** vắt split — thoạt nhìn là bằng chứng sạch, thực chất là **hệ quả định nghĩa**, vì v3 khử trùng lặp ở đúng ngưỡng 10. Chỉ ngưỡng **cao hơn** (12, 15, 20) mới mang thông tin mới.

**(3) phash chỉ nhận khoảng cách chẵn, nên ngưỡng lẻ vô nghĩa.** `phash` 64 bit ở cài đặt này sinh hash có **đúng 32 bit bằng 1**, nên khoảng cách Hamming luôn bằng $64 - 2k$ với $k$ là số bit 1 trùng vị trí — **luôn chẵn**. Ngưỡng lẻ (11, 13) cho kết quả **y hệt** ngưỡng chẵn liền trước nên bị loại khỏi bảng đo; đây cũng là lý do khoảng cách nhỏ nhất quan sát được (12) là số chẵn.

**(4) Bộ đo độ chính xác OCR không đi qua đường mã của sản phẩm.** `ai/evaluation/ocr_accuracy.py` — nơi sinh các chỉ số NFR-A4 đến A7 công bố ở Chương 6 — gọi thẳng bộ nhận dạng và bộ chuẩn hoá, **không dựng `ALPRPipeline`**, nên mọi logic ở tầng điều phối đều **vô hình** với các con số công bố; nếu bước cứu biển hai dòng (5.5.5f) được viết như phương thức riêng của pipeline thì chương thực nghiệm sẽ đo một đường mã sản phẩm **không chạy**. Bản sửa tách bước cứu thành hai hàm dùng chung (`should_rescue_two_line`, `rescue_two_line_upper` trong `ai/inference/pipeline.py`). Khoảng cách này **không gây lỗi, không sinh cảnh báo**, không bộ kiểm thử kiến trúc nào bắt được, và **chưa có cơ chế tự động nào canh giữ nó**.

**(5) Một giả thuyết sửa lỗi hợp lý bị chính dữ liệu bác bỏ.** Khi `29E-015.66` bị đọc thành `015.66`, giả thuyết hiển nhiên là đọc riêng từng nửa rồi nối chuỗi; đo trên 200 biển hai dòng, cách đọc riêng đạt **3,5%** so với **64,5%** của cách ghép hiện hành, thắng ở **0/200** ảnh (`docs/reports/15-two-line-ab.json`). Nguyên nhân là hai nửa được cắt **chồng lấn có chủ ý** nên đọc rời sinh ký tự rác (`84G122593` ra `84-G124E009.01225.93`); phép ghép ngang hoá ra còn **trao cho bộ phát hiện văn bản cơ hội loại bỏ vùng chồng lấn**. Bản sửa cuối *giữ nguyên* thiết kế cũ, với cổng đặt sau kiểm tra định dạng nên **không thể làm giảm độ chính xác về mặt cấu trúc**: đo trên 900 biển qua hai mẫu độc lập, **0 ca hỏng**.

Ngoài năm lần trên, quy trình còn **bác bỏ một con số độ trễ cũ** (7.3.4). Sáu sự việc này là một đóng góp phương pháp luận: **một chương đánh giá chỉ trưng ra các con số đẹp và không kể lại lần nào nó tự nghi ngờ chính mình là một chương đã tự tước bỏ khả năng bị kiểm chứng.**

---

## 7.3. Các hạn chế của đồ án

Mục này viết theo nguyên tắc của 6.9.3: **nêu hạn chế, đánh giá mức nghiêm trọng, nói rõ đã làm gì để giảm thiểu — kể cả khi câu trả lời là "chưa làm được gì".**

### 7.3.1. Hạn chế lớn nhất: OCR biển hai dòng còn yếu, kéo E2E chưa đạt

*Mức nghiêm trọng: cao — hạn chế trung tâm của toàn đồ án.* NFR-A5 = **0,6373**, thiếu 16,27 điểm so với ngưỡng 0,80; NFR-A6 = **0,7512**, thiếu 9,88 điểm so với ngưỡng 0,85; NFR-A7 = **0,5552**, thiếu 26,48 điểm so với ngưỡng 0,82; NFR-A4 (1 − CER) = **0,9454** vượt ngưỡng tối thiểu 0,92 ở lượt đo 28/07 nhưng vẫn dưới mục tiêu 0,95. **Nguyên nhân đã định vị bằng số liệu và nó ở tầng OCR chứ không phải tầng hậu xử lý**, với ba bằng chứng độc lập: *tách theo layout* (T6.5c) cho thấy toàn bộ khoảng thiếu nằm ở biển hai dòng, vốn chiếm 79,8% tập nên chi phối con số tổng; *phân tích lỗi* (T6.8) cho thấy trong 445 ca nhầm ký tự có **428 ca** thuộc biển hai dòng, còn trong 73 ca thiếu ký tự thì **cả 73 ca** đều thuộc biển hai dòng, không một ngoại lệ; *đóng góp hậu xử lý bị chặn trên* (T6.5b) — luật thêm được +11,39 điểm nhưng phần lỗi còn lại đã dịch sang **đọc hụt ký tự** (ký tự bị xoá chiếm 56,8% toàn bộ lỗi), mà ký tự chưa từng được đọc ra thì **về nguyên tắc** không luật nào phục hồi được. **Hướng khắc phục bắt buộc nằm ở tầng nhận dạng** (7.4.1); trút thêm luật vào `plate_rules.py` không đụng đến nút thắt thật.

> **Cảnh báo hiệu lực về con số A7 = 0,5552.** Con số này đo trên ảnh **crop biển số**, ngoài phân bố huấn luyện của bộ phát hiện, nên tỉ lệ bỏ sót 11,96% bị thổi phồng và A7 phải đọc như **cận dưới bi quan**, không phải ước lượng điểm (6.5.5). Đo A7 đúng cách đòi hỏi một tập test hiện trường có nhãn chuỗi — việc **chưa làm được** (7.4.3).

### 7.3.2. Rò rỉ dữ liệu tồn dư không khử được bằng băm tri giác

*Mức nghiêm trọng: cao.* Khử trùng lặp chạy đúng đặc tả ở ngưỡng gộp 10, nhưng tại ngưỡng Hamming **12** vẫn còn **791 cặp** ảnh gần trùng train↔test, tại ngưỡng **15** là **3.529 cặp**. Nghiêm trọng hơn là loại rò rỉ **không ngưỡng phash nào bắt được**: hai ảnh của *cùng một chiếc xe* chụp khác góc, hoặc hai khung cách nhau vài giây trong cùng một video, mang **cùng một biển số** nhưng khoảng cách Hamming lớn — rò rỉ ở mức **ngữ nghĩa**, mà phash vốn chỉ đo tương đồng bố cục thì mù trước nó. *Đã áp dụng:* nâng ngưỡng gộp 5 → 10 và đo rò rỉ ở nhiều ngưỡng cao hơn. *Chưa áp dụng được:* chia split **theo nhóm biển số**, bất khả thi hiện tại vì phần lớn corpus thiếu nhãn chuỗi để nhóm. **Hệ quả bắt buộc nêu khi bảo vệ: mọi chỉ số ở tầng phát hiện và OCR phải được coi là cận trên lạc quan.**

### 7.3.3. Tập test không xuyên bộ dữ liệu, nên mAP lạc quan hơn khi triển khai

*Mức nghiêm trọng: cao.* Train và test lấy từ **cùng sáu nguồn nguyên tố** đã hợp nhất, nên thiết lập này đo được tổng quát hoá *trong phân bố* nhưng **không** đo được *xuyên phân bố* — thứ quyết định khi triển khai trên camera, địa điểm và điều kiện chiếu sáng mới. Tài liệu đã chỉ ra độ chính xác ALPR sụt giảm đáng kể khi đánh giá xuyên bộ dữ liệu [7]<!-- laroca_2022_crossdataset -->, nên mAP@0.5 = 0,9829 gần như chắc chắn **lạc quan hơn** hiệu năng thực tế. *Biện pháp giảm thiểu: không có trong khuôn khổ đồ án*; cách đúng là giữ một nguồn hoàn toàn không dùng để huấn luyện làm tập test xuyên bộ, **chưa thực hiện** (7.4.2).

### 7.3.4. Độ trễ — đạt ngưỡng tối thiểu, và mức vượt mục tiêu là một đánh đổi có chủ ý

Độ trễ E2E một ảnh p95 = **1.143,10 ms** — dưới sàn 1.500 ms nhưng vượt mục tiêu 800 ms 1,43 lần; trung vị chỉ **405,77 ms**. Đo in-process trên `best.pt`, cấu hình giao hàng, máy rảnh (CPU idle ~5%, không có tiến trình huấn luyện song song), warmup rồi đo 100 ảnh test v3.

**Đây là thoái lui có chủ ý, đã định lượng, đổi lấy độ chính xác.** Tắt hẳn bậc thang thử-lại cho biển nghiêng/méo đưa p95 về **866,3 ms**, tức toàn bộ +277 ms là của nó, đổi lại 34 biển đọc thêm (+0,75 điểm A6); vì bậc thang chỉ chạy **sau khi lần đọc đầu thất bại**, chi phí dồn cả vào đuôi phân phối còn trung vị giảm nhẹ so với lượt trước (6.5.7, 6.6.1). Với cả ba biến thể bật, p95 là **1.514,26 ms** — vượt cả ngưỡng tối thiểu; bậc **siêu phân giải** chiếm hơn nửa chi phí đó (+319 ms ở p95, +1.381 ms ở p99) mà **không mua được biển nào đo được**, nên bị tắt mặc định. Giới hạn của lập luận phải nói rõ: số 0 của siêu phân giải là **số 0 cấu trúc** — cổng chỉ mở cho vùng cắt dưới 200 px, mà **0/120 mẫu ngữ liệu lọt cổng** — nên quyết định dựa trên "chi phí đã đo được và lớn, lợi ích **chưa ai đo được**"; mã và công tắc giữ nguyên để bật lại khi có dữ liệu đo tử tế.

Con số này từng bị nghi ngờ theo hướng ngược lại: một báo cáo trước ghi p95 = **5.857 ms** và kết luận NFR-P1 "không đạt", con số đó đã bị **bác bỏ** vì điều kiện đo bị nhiễm (tranh chấp CPU do một tiến trình huấn luyện chạy song song, sai checkpoint, lỗi crop) chứ không vì mô hình chậm (6.6.1). Phân rã ngân sách thật (T6.6b): OCR chiếm **64,3%** (108,28 ms/biển), phát hiện **34,0%** (57,27 ms) — **không** phải tỉ lệ 93,3% / 6,7% của báo cáo cũ. Kiến trúc phần mềm **không phải vấn đề**; hướng tối ưu đúng là **giảm số lần phải thử lại** bằng huấn luyện lại bộ nhận dạng (7.4.1) chứ không phải tối ưu từng lượt gọi (7.4.4).

### 7.3.5. Nút "Huỷ tác vụ" video chưa hoàn chỉnh; một số chỉ tiêu chưa đo

*Mức nghiêm trọng: trung bình đến thấp, tuỳ hạng mục.* Chương 4 mô tả khả năng huỷ một tác vụ video đang chạy, nhưng bản cài đặt hiện tại **chưa có route HTTP nào đặt được trạng thái huỷ** — OpenAPI đang chạy công bố 9 đường dẫn, không đường dẫn nào huỷ tác vụ; đây là hạng mục cài đặt còn treo, không phải quyết định thiết kế.

**Bảng chỉ tiêu chưa đo từng có bốn hàng; ba hàng đã đo xong ngày 02/08/2026** ([33-runtime-nfr.json](../reports/33-runtime-nfr.json)) **bằng `scripts/benchmark_runtime_nfr.py`, còn một.** P2 (FPS webcam): ❌ **2,379 FPS**, đã đo, **không đạt** (sàn 3). P3 (tốc độ xử lý video): ✅ **0,746×** thời gian thực, đạt. R5 (CSDL sống sót qua khởi động lại): ✅ **0/9.031 bản ghi mất**, đạt. A9 (tách theo điều kiện ảnh): ⬜ **chưa đo — bộ dữ liệu không có nhãn điều kiện ảnh**, tức *thiếu điều kiện* (hạn chế thật) chứ không phải *chưa tới lượt*, chỉ khắc phục được bằng gán nhãn thủ công cho một tập con; phân biệt này giữ đúng tinh thần mục 6.9.2. **Một trong ba mã đo ra kết quả trượt, và điều đó đáng ghi nhận:** "chưa đo" không đồng nghĩa với "sẽ đạt" — P2 trượt cả sàn vì đuôi độ trễ của bậc thang thử-lại chứ không phải vì tốc độ trung bình, trung vị 180 ms tương đương 5,6 FPS vẫn vượt mục tiêu (6.6.4). Phép đo gọi trực tiếp `POST /api/detect/frame` vì trang Webcam đã gỡ theo quyết định thu gọn phạm vi ngày 2026-07-20 — quyết định phạm vi có chủ đích, không phải khiếm khuyết cài đặt; mã giao diện còn nguyên trong lịch sử git.

### 7.3.6. Một yêu cầu mức *Must* (FR-4.1) đã bị đưa ra khỏi phạm vi

*Mức nghiêm trọng: trung bình. Đây là hạn chế duy nhất phát sinh từ một **quyết định** chứ không từ giới hạn kỹ thuật, nên càng phải nói thẳng.* Ngày 2026-07-20 giao diện thu gọn hai đợt — gỡ trang Webcam, rồi gỡ trang Tổng quan — còn **ba trang**: Nhận dạng ảnh (chủ), Nhận dạng video, Lịch sử. Hệ quả: **FR-3.1** (xin quyền và hiển thị luồng webcam) M → W; **FR-3.4** (vẽ chồng bounding box lên khung hình trực tiếp) M → W; **FR-4.1** (Dashboard hiển thị các chỉ số tổng hợp) **M → W**; **FR-4.2** (biểu đồ số lượt nhận dạng theo thời gian) S → W. Bảng đếm MoSCoW chuyển từ 22/7/3/2 sang **21 Must / 6 Should / 3 Could / 4 Won't** trên tổng 34 yêu cầu.

**FR-4.1 là yêu cầu mức *Must* đầu tiên và duy nhất bị đưa ra khỏi phạm vi trong toàn đồ án.** Theo quy ước MoSCoW chốt ở Phase 0, *Must* nghĩa là "thiếu ⇒ đồ án không đạt", nên tiêu chí thành công số 1 ở mục 1.2.3 chỉ đúng khi hiểu theo bộ **21** yêu cầu *Must* **sau** thay đổi phạm vi. Nhưng **phần mất đi là màn hình hiển thị, không phải năng lực hệ thống**: phép tính thống kê vẫn trong `StatisticsService`, vẫn phơi qua `GET /api/statistics` với đủ các chỉ số FR-4.1 và FR-4.2 đòi hỏi, và **vẫn có kiểm thử tích hợp** (`tests/integration/test_api_statistics.py`, `test_api_health.py` trong bộ 1.001 test); không endpoint nào bị xoá, FR-4.3–FR-4.8 không đổi mức. *Đánh đổi:* gỡ `recharts` cùng trang Tổng quan làm gói tải về giảm từ khoảng **730 KB xuống 328,8 KB (−55%)**, số mô-đun frontend giảm 60 → 48. *Giảm thiểu:* mã cả hai trang và hợp đồng kiểu tương ứng được **giữ có chủ đích** (7.4.6).

### 7.3.7. SQLite chỉ cho phép một tiến trình ghi tại một thời điểm

*Mức nghiêm trọng: thấp trong phạm vi đồ án, nêu vì là câu hỏi phản biện dễ gặp.* SQLite khoá ghi ở mức toàn tệp. Với bối cảnh triển khai nội bộ, một người vận hành (giả định A-04), đây không phải nút thắt — phép đo chịu tải cho thấy hệ thống ổn định ở 10 yêu cầu đồng thời và soak 300 giây thành công 100%; nhưng nếu triển khai đa người dùng ghi đồng thời thì giới hạn này thành thực. Hướng khắc phục là PostgreSQL (7.4.7); nhờ SQLAlchemy 2.0 làm tầng trừu tượng, việc chuyển không đụng mã nghiệp vụ.

### 7.3.8. Bộ dữ liệu lệch nặng về biển trắng, nên kết luận về độ chính xác OCR chỉ áp cho biển trắng

*Mức nghiêm trọng: cao. Hạn chế này quy định **phạm vi hiệu lực** của mọi con số OCR trong quyển.* Chạy bộ phân loại màu nền lên toàn bộ **2.801 ảnh biển số có nhãn ký tự** — chính là tập sinh ra NFR-A4 đến A7 — cho phân bố (`docs/reports/17-plate-type-audit.json`): trắng (dân sự) **2.736 ảnh / 97,68%**; vàng (kinh doanh vận tải) **20 / 0,71%**; xanh (cơ quan Nhà nước) **4 / 0,14%**; đỏ (quân đội) **0 / 0%**; NG/QT (ngoại giao) **0 / 0%**; không đọc được màu **41 / 1,46%**. Hệ quả: **con số độ chính xác OCR mà đồ án công bố thực chất là độ chính xác trên biển trắng** — câu phát biểu đúng khi bảo vệ là *"1 − CER = 0,9454 trên một tập gồm 97,7% biển trắng"*, không phải *"trên biển số Việt Nam"*. Cùng loại hạn chế phạm vi với 7.3.3, chỉ khác trục: ở đó là trục nguồn ảnh, ở đây là trục loại biển.

> ### Cập nhật 02/08/2026 — hạn chế này đã được thu hẹp, nhưng **chưa gỡ**
>
> **Mọi con số A4–A7 công bố trong quyển này vẫn đo trên ngữ liệu 2.801 mẫu ở trên**; phần dưới là nguyên liệu chuẩn bị cho lần đo sau, **không phải một bộ số mới**.
>
> **(a) Đã gộp 521 biển hiếm vào ngữ liệu nhãn ký tự** từ `nguyenluanai/license-plate-color` v4 (CC BY 4.0), thẩm định ở [30-rare-plate-integration.md](../reports/30-rare-plate-integration.md): tổng ngữ liệu **2.801 → 3.322**, vàng **20 → 476**, xanh **4 → 45**, tỷ lệ biển hiếm **0,86% → 15,7%**. Biển vàng chuyển từ *"n = 20, không có ý nghĩa thống kê"* sang **đánh giá được**; biển xanh (n = 45) vẫn phải báo cáo kèm khoảng tin cậy.
>
> **(b) Mệnh đề "không bộ dữ liệu nào của đồ án chứa biển đỏ" nay chỉ còn đúng cho ngữ liệu ảnh cắt sẵn.** Tập ảnh toàn cảnh gán nhãn ngày 02/08 ([34-scene-level-a7.md](../reports/34-scene-level-a7.md)) **có** biển đỏ quân đội (`PK-53-46` ×2, `QC 10-21`, `VT 1A-16`), biển xanh nhà nước (`80A-068.89`), ngoại giao (`41-291-NG-01`) và sê-ri LD (`93LD-001.03`) — quá nhỏ để công bố độ chính xác theo loại biển, nhưng đủ để **không còn nói "bằng không"**.
>
> **(c) Biển đỏ và ngoại giao vẫn không có nguồn công khai đủ lớn.** Khảo sát 286 project Roboflow và toàn bộ Kaggle ([17-plate-type-dataset-survey.md](../reports/17-plate-type-dataset-survey.md)) kết luận biển quân đội Việt Nam hiếm trên đường và nhạy cảm khi công khai, *"không nên kỳ vọng tìm được nguồn công khai tốt hơn"* — hạn chế **thật**, không phải "chưa tới lượt".

Hai điều rất dễ bị gộp khi trả lời phản biện cần tách bạch. **Hệ thống *có* năng lực phân loại loại biển** — chín giá trị `PlateKind` và bốn màu nền, **đã kiểm chứng trên ảnh thật** ở 97,89% trên 1.565 ảnh có nhãn màu do người gán (7.2.5). Nhưng **hệ thống *chưa có dữ liệu* để đo độ chính xác nhận dạng ký tự cho các loại biển hiếm**: với biển vàng (n = 20) và xanh (n = 4) mọi con số đều không có ý nghĩa thống kê, còn biển đỏ và ngoại giao thì **không đánh giá được** vì tập không chứa mẫu nào. **"Chưa đo được" không đồng nghĩa với "không làm được", và cũng không được phép trình bày như thể đã đo được.** *Chưa áp dụng được:* bổ sung chính các mẫu đó vào tập đánh giá (6.4.8, 7.4.8) — vướng thêm một ràng buộc kỹ thuật nêu ở 7.4.8 khiến nguồn biển vàng dồi dào nhất **không dùng được để đánh giá OCR**.

### 7.3.9. Bước làm thẳng biển nghiêng (rectify) chưa được cài đặt — ĐÃ XỬ LÝ 21/07/2026, xem cuối mục

Nhật ký quyết định mô tả luồng biển hai dòng gồm bốn bước **rectify → phân loại số dòng → tách đôi → ghép ngang**, nhưng bước đầu **chưa từng được cài đặt**; nghiêm trọng hơn, một chú thích trong `ai/inference/recognizer.py` từng khẳng định *"ảnh cắt đã được bộ phát hiện làm thẳng"* — **sai**, vì hộp bao của YOLO là hộp trục-thẳng; chú thích đó đã được sửa. Hệ quả đo được trên khung 168 của `demo/demo-video.mp4`: biển thật (đọc bằng mắt) `77-H5` / `4374`, hai dòng, **nghiêng rõ**; hộp bao trục-thẳng **146 × 42 px, tỷ lệ 3,48**; ngưỡng phân loại một dòng / hai dòng **2,50**; kết quả phân loại **một dòng (sai)**; chuỗi OCR **rỗng**. Biển hai dòng chụp nghiêng có hộp bao rộng bất thường nên tỷ lệ vọt lên trên ngưỡng, còn ép tách cũng không cứu được vì vết cắt ngang chém **chéo** qua cả hai hàng ký tự; bằng chứng sạch nhất là cùng biển ấy chụp gần chính diện (`demo/images/nhieu-bien-3.png`) hệ thống đọc **đúng** `77H5-4374`. Cảnh báo về vùng xám tỷ lệ khung hình đã ghi trong tài liệu `estimate_line_count` từ Phase 4 nhưng chỉ nêu chiều **giảm**; chiều **tăng** không được lường trước, mà trên đường phố nó phổ biến hơn. **Cập nhật 21/07/2026 — hạn chế này đã được xử lý** bằng bậc thang thử-lại mô tả ở 7.4.9; số liệu, bài học và giới hạn còn lại (**nắn phối cảnh bốn điểm chưa cài**) nằm ở đó và ở `docs/reports/21-skew-retry.md`.

### 7.3.10. Xem trực tiếp và xử lý nền tranh chấp CPU với nhau

Trang nhận dạng video chạy đồng thời bản **xem trực tiếp** (gửi từng khung lên `POST /api/detect/frame`) và **tác vụ nền** xử lý toàn bộ video trên cùng một CPU không GPU. Đo trên backend với cùng một ảnh, chỉ khác điều kiện: **89–97 ms** một khung (chế độ chỉ phát hiện) khi không có tác vụ nền, **230–462 ms** khi có — chậm đi **2,5–5 lần**, quan hệ hai chiều, và vì chọn tệp là khởi động cả hai cùng lúc nên **cả hai cùng tệ đi mà không bên nào được lợi**. Đây là hệ quả của quyết định môi trường ở Phase 0 (suy luận trên CPU, không GPU) chứ không phải lỗi lập trình, và nó làm **mọi số đo độ trễ của bản xem trực tiếp phụ thuộc việc lúc đó có tác vụ nền hay không** (7.4.10).

---

## 7.4. Hướng phát triển

Các hướng dưới đây **bắt nguồn từ số liệu Chương 6**; thứ tự phản ánh mức ưu tiên do chính kết quả quyết định.

### 7.4.1. Huấn luyện lại module nhận dạng (rec) riêng cho biển số Việt Nam — hướng quan trọng nhất

Vì nút thắt nằm ở **tầng OCR** (7.3.1), hướng tác động lớn nhất là **thay hoặc huấn luyện lại riêng module rec** thay vì dùng trọng số PaddleOCR đa mục đích pre-trained [17]<!-- cui_2026_ppocrv5 -->. Bốn cách, xếp theo mức đầu tư tăng dần: (1) **fine-tune module rec của PaddleOCR trên biển số** theo đúng công thức PaddleOCR đã trình bày (fine-tune PP-OCR trên CCPD) [67]<!-- paddlepaddle_nd_plateapp -->, rẻ nhất; (2) **dùng mô hình rec hỗ trợ biển đa dòng ngay từ thiết kế** — TransLPRNet [121]<!-- arxiv_2025_translprnet --> hay LPTR-AFLNet tích hợp nắn chỉnh và nhận dạng nhẹ [75]<!-- xu_2025_lptraflnet -->; (3) **tách–ghép biển hai dòng trước khi đưa vào rec** như cộng đồng biển số Trung Quốc dùng [64]<!-- we0091234_nd_doubleplatesplit -->, rẻ nhưng nhạy với chất lượng tách; (4) **huấn luyện mô hình chuyên biệt cho biển Việt Nam từ đầu**, ví dụ CRNN kèm cơ chế chú ý [70]<!-- dang_2024_crnn --> hoặc pipeline chuyên xe máy Việt Nam [21]<!-- le_2023_vnmotorcycle -->, trần chất lượng cao nhất. Nhờ NFR-M5, thay module rec **không đụng mã tầng API**, chỉ cần cài lại giao diện `PlateRecognizer`.

**Ba phép đo độc lập thu được sau khi Chương 6 đã đo xong cùng củng cố thứ tự ưu tiên này**, cả ba đều là can thiệp ở **tầng ngoài mô hình nhận dạng**: bộ luật hậu xử lý theo vị trí thu **+11,39 điểm** A6 · 319 biển (7.2.3); bước cứu dòng trên thu **209 biển** (6.5.6); bậc thang thử-lại biển nghiêng/méo thu **+0,75 điểm** A6 · 34 biển (6.5.7). Cộng lại, chúng nâng A6 từ **0,6098** (lượt đo ban đầu, chỉ có chuỗi thô) lên **0,7512** mà **không tốn một giây GPU nào** — nhưng vẫn thiếu **9,88 điểm** so với ngưỡng, và **dư địa đã cạn**: bậc thang hình học, can thiệp mới nhất và tốn kém nhất (p95 tăng 32%), chỉ còn mua được 34 biển trên 2.801. Ký tự **chèn thừa** nay gần như biến mất (giảm 88%) trong khi ký tự **bị xoá** chiếm 56,8% toàn bộ lỗi (6.5.1): phần lỗi đã dịch từ "chuỗi hỏng về cấu trúc" sang "**ký tự chưa từng được đọc ra**", thứ **về nguyên tắc** không tầng nào ngoài mô hình nhận dạng phục hồi được. Mục 7.4.3 là điều kiện tiên quyết.

> **Hai lượt thử đã thực hiện và đều thất bại, ghi lại vì kết quả âm cũng là kết quả.** Lượt **thứ nhất** (28/07/2026) cho model đọc **0/7** ảnh demo đúng so với **7/7** của model gốc. Nguyên nhân ở **tập huấn luyện sai nhãn, sinh ra một cách im lặng**: kịch bản sinh dữ liệu có cơ chế "ảnh thay thế" kích hoạt khi không mở được ảnh gốc, mà `datasets/raw/**` nằm trong `.gitignore` nên máy huấn luyện không hề có ảnh gốc, khiến mọi nhãn bị ghép với ảnh của một biển khác; cơ chế đó đã bị gỡ và thay bằng chốt chặn cứng (`docs/reports/25-finetune-attempt-failed.md`).
>
> **Lượt thứ hai** (02/08/2026) huấn luyện thành công nhưng cũng **không được đem giao**: val acc **0,8809** trên tập kiểm định của chính nó, nhưng đo qua đường ống thật lại **kém hơn model gốc** (A6 = 0,6762 so với 0,7512). Truy nguyên: phép đo lúc huấn luyện và hệ thống lúc chạy **đo hai chế độ khác nhau** — PaddleOCR đánh giá nhánh nhận dạng bằng cách đưa *nguyên ảnh* biển, còn đường ống triển khai *phát hiện chữ trước rồi mới nhận dạng*, tức cắt ảnh thành nhiều mảnh, nên model fine-tune đọc mảnh vụn rất kém (0,2667 so với 0,8233 trên **chính những ảnh nó đã huấn luyện trên đó**). Bỏ bước phát hiện chữ thì nó thắng đậm (A6 = **0,8758**, hơn model gốc **12,46 điểm**), nhưng cấu hình ấy vẫn không được giao vì ngữ liệu 2.801 mẫu **toàn ảnh đã cắt sẵn**: đo lại trên bộ demo gồm ảnh toàn cảnh qua bộ phát hiện thật thì thứ tự **đảo ngược** (model gốc 17/22 tụt còn 13/22), và chế độ chỉ-nhận-dạng **không có khả năng trả chuỗi rỗng** (0/1.606 khung so với 173 của bản đang giao) nên khi bộ phát hiện bắt nhầm thì nó *bịa* ra biển thay vì im lặng. Cả hai lượt đều là **kết quả âm được ghi lại**, bài học khác nhau: lượt một là lỗi dữ liệu, lượt hai là **lỗi phép đo** — một con số đúng về số học nhưng đo một chế độ mà hệ thống không dùng (`docs/reports/31-detection-stage-ablation.md`).

### 7.4.2. Xây dựng tập test xuyên bộ dữ liệu

Để chữa 7.3.3, cần **giữ nguyên một nguồn hoàn toàn không dùng để huấn luyện** làm tập test xuyên bộ và báo cáo song song mAP trong phân bố với mAP xuyên bộ, đúng cách chuẩn mực mà tài liệu cross-dataset khuyến nghị [7]<!-- laroca_2022_crossdataset -->. Kết hợp **chia split theo nhóm biển số** sẽ khử được cả rò rỉ ngữ nghĩa mà phash không bắt được ở 6.3.2.

### 7.4.3. Bổ sung nhãn chuỗi biển số cho toàn tập

Hiện chỉ **2.801** biển có nhãn chuỗi trong khi corpus có 15.133 ảnh phần lớn chỉ có nhãn hộp giới hạn; mẫu số nhỏ này là mối đe doạ đến tính hợp lệ (6.9.3) và là thứ chặn việc đo NFR-A7 đúng cách trên ảnh hiện trường (7.3.1). Hướng khắc phục là **gán nhãn chuỗi cho một phân bố hiện trường** đủ lớn, cho phép đo A7 trên ảnh toàn cảnh, chia split theo nhóm biển, và có đủ dữ liệu fine-tune module rec ở 6.4.1; chi phí giảm được bằng bán tự động — dùng chính hệ thống hiện tại sinh nhãn nháp rồi người soát lại — hoặc bổ sung dữ liệu tổng hợp và dữ liệu thật theo hướng hợp nhất đa nguồn [122]<!-- arxiv_2026_multinationalfusion -->.

### 7.4.4. Tăng tốc suy luận: lượng tử hoá OCR, đóng gói ONNX/OpenVINO cả hai tầng

NFR-P1 chỉ đạt ngưỡng tối thiểu chứ không đạt mục tiêu (7.3.4), và phân rã ngân sách chỉ ra việc phải làm: OCR chiếm 64,3%, phát hiện 34,2% thời gian suy luận. **Lượng tử hoá INT8 module OCR** với một tập hiệu chuẩn, tận dụng tập lệnh vector VNNI/AVX-512 trên CPU Intel [123]<!-- onnxruntime_2025_quantization -->, có đòn bẩy cao nhất. **Đóng gói cả hai tầng sang ONNX Runtime hoặc OpenVINO**: YOLO11 xuất sang OpenVINO tối ưu cho CPU Intel [18]<!-- ultralytics_2026_openvinoexport -->, Ultralytics hỗ trợ hơn hai mươi định dạng xuất [96]<!-- ultralytics_2026_export -->; hiện đường suy luận chạy PyTorch thuần, và **thí nghiệm so sánh backend (bảng T6.6c) là hạng mục đã chuẩn bị nhưng chưa chạy**. Lưu ý phương pháp luận bắt buộc: mọi con số tăng tốc phải đo lại **trên cùng cấu hình phần cứng** và công bố kèm cấu hình.

### 7.4.5. Bám vết đối tượng qua khung hình cho video (SORT/DeepSORT)

Hiện khi xử lý video, hệ thống gộp các lần nhận dạng trùng theo **chuỗi ký tự** — cách này gãy khi OCR đọc sai cùng một biển ở các khung khác nhau thành các chuỗi khác nhau. Hướng đúng là **bám vết đối tượng qua khung hình** bằng SORT hoặc DeepSORT: gán ID theo dõi ổn định cho mỗi xe/biển rồi gộp theo ID, vừa ổn định hơn trước lỗi OCR lẻ tẻ vừa mở đường cho **bỏ phiếu theo thời gian**. Hướng mở liên quan là **khôi phục giao diện thời gian thực**, trình bày chung với 7.4.6.

### 7.4.6. Khôi phục hai màn hình đã gỡ, từ lịch sử git

Hướng chữa trực tiếp 7.3.6 và **rẻ nhất trong toàn bộ mục 7.4** — chỉ đòi hỏi một quyết định về phạm vi. Việc khôi phục là *phục hồi* chứ không phải *xây mới* nhờ ba điểm: **năng lực phía máy chủ chưa bao giờ bị gỡ** (`POST /api/detect/frame`, `GET /api/statistics` và `GET /health` vẫn trong OpenAPI đang chạy và đều có kiểm thử tích hợp trong bộ 1.001 test); **mã giao diện còn nguyên trong lịch sử git** (`pages/WebcamDetection.tsx` cùng cơ chế hàng đợi một khe ở mục 5.7.3, `pages/Dashboard.tsx`, thư mục `components/dashboard/`, hook `useApi.ts`, các hàm `detectFrame` / `getStatistics` / `getHealth` trong `services/api.ts`); và **hợp đồng kiểu vẫn được duy trì** trong `frontend/src/types/index.ts`. Quy trình: lấy lại tệp từ git, nối lại route trong `App.tsx` và mục tương ứng trong thanh điều hướng, rồi chạy `tsc --noEmit` cùng `vite build`. Chỉ **thư viện biểu đồ** cần cân nhắc lại: gỡ `recharts` mang lại phần lớn mức giảm gói tải về nêu ở 7.3.6, nên nếu dựng lại màn hình thống kê thì nên chọn thư viện nhẹ hơn hoặc nạp trễ riêng phần biểu đồ. Hướng này **khôi phục một chỉ tiêu đã cam kết** (FR-4.1 mức Must) chứ không nâng chất lượng nhận dạng — nếu chỉ làm được một việc thì 7.4.1 vẫn đáng làm trước.

### 7.4.7. Chuyển sang PostgreSQL nếu triển khai đa người dùng

Để chữa 7.3.7, khi triển khai có nhiều người ghi đồng thời nên chuyển lớp dữ liệu từ SQLite sang **PostgreSQL**, vốn hỗ trợ nhiều tiến trình ghi đồng thời và điều khiển đồng thời ở mức hàng. Nhờ toàn bộ truy cập dữ liệu đã đi qua SQLAlchemy 2.0 và tầng repository, việc chuyển đổi giới hạn ở lớp cấu hình kết nối và migration, **không** đụng mã nghiệp vụ hay mã API.

### 7.4.8. Thu thập dữ liệu cho các loại biển hiếm — điều kiện để mở rộng phạm vi kết luận

Hướng chữa trực tiếp 7.3.8, và **nó không đòi hỏi thay đổi gì trong hệ thống**: năng lực phân loại chín họ biển và bốn màu nền đã có và đã kiểm chứng (7.2.5), thứ còn thiếu là **dữ liệu để đo**. Ba việc, xếp theo mức khó tăng dần. (1) **Biển vàng — đã có nguồn, cần xử lý đúng**: `nguyenluanai/license-plate-color` (CC BY 4.0) cung cấp 694 ảnh biển vàng, gấp khoảng 35 lần số hiện có, và **tên tệp đã chứa sẵn chuỗi biển số** nên nhãn ký tự gần như miễn phí; trở ngại duy nhất là phép kéo méo về 640×640 nêu ở 7.3.8, cách xử lý là lấy ảnh gốc từ nguồn rồi soát lại nhãn bằng mắt. (2) **Biển đỏ quân đội và ngoại giao — cần chuyển từ "0 mẫu" sang "đo được"**: khảo sát ở `docs/reports/17-plate-type-dataset-survey.md` xác định được nguồn công khai chứa hai loại này nhưng quy mô rất nhỏ (khoảng một trăm ảnh gốc biển đỏ, chỉ khoảng mười tám ảnh gốc biển ngoại giao) — **đủ để có một tập kiểm thử báo cáo được**, thứ hiện đang bằng không, nhưng **không đủ để huấn luyện**; phải xử lý trước hai rủi ro là các bản tăng cường trong nguồn bị chia lẫn giữa train/valid/test (phải gom theo ảnh gốc rồi tự chia lại) và giấy phép do người đăng tự khai chứ không phải giấy phép của ảnh gốc. (3) **Biển chuyên dùng (LD, DA, RM, HC, KT, CD, T) — chưa tìm được nguồn nào**, nên con đường khả dĩ duy nhất là thu thập và gán nhãn tại chỗ, hoặc chấp nhận chúng nằm ngoài phạm vi đánh giá và ghi rõ như vậy. Hướng này **không** nâng độ chính xác lên một điểm nào; giá trị của nó là **mở rộng phạm vi mà các kết luận có hiệu lực** — chuyển câu phát biểu từ *"đo trên một tập gồm 97,7% biển trắng"* sang một câu có phân tầng theo loại biển.

### 7.4.9. Cài đặt bước làm thẳng biển nghiêng — ĐÃ THỰC HIỆN 21/07/2026

Ba bậc, xếp theo mức đầu tư tăng dần: (1) **ước lượng góc nghiêng bằng `cv2.minAreaRect` rồi `warpAffine` xoay ngược** — khoảng bốn mươi dòng mã, không cần huấn luyện, không cần dữ liệu mới; (2) **đo lại số dòng trên ảnh đã nắn thay vì trên hộp bao** — chính tài liệu `estimate_line_count` đã đề xuất từ Phase 4, sau khi nắn thì ngưỡng 2,5 mới có ý nghĩa như thiết kế; (3) **nắn phối cảnh bốn điểm** cho trường hợp chụp chéo. **Kỷ luật đo lường bắt buộc**, rút từ chính kinh nghiệm của đồ án: tập nhãn hiện có gồm **ảnh cắt sẵn của bộ dữ liệu**, phần lớn gần chính diện, nên nó **không chứa dạng lỗi này** và một phép đo trên tập đó nhiều khả năng cho "không đổi" rồi bị hiểu nhầm thành "không có tác dụng"; muốn đo đúng phải dựng tập gồm **ảnh cắt do chính bộ phát hiện sinh ra từ ảnh chụp toàn cảnh**. Nguyên tắc rút ra: **tập đánh giá phải chứa dạng lỗi mà bản sửa nhắm tới, nếu không phép đo chỉ chứng minh được tính an toàn chứ không chứng minh được lợi ích.**

**Kết quả thực hiện (21/07/2026).** Kỷ luật đo lường trên đã **bác bỏ thiết kế đầu tiên**: bậc 1+2 cài dưới dạng tiền xử lý luôn-bật qua được toàn bộ kiểm thử hình học tổng hợp nhưng đo trên 36 khung ảnh cắt do detector sinh ra từ video demo thì **thua baseline 42 → 40**, vì trên crop nhỏ và mờ `minAreaRect` thi thoảng fit sai và cắt mất ký tự của một biển đang đọc tốt; cùng phép đo cho thấy ca khung 168 thực chất là **foreshortening phối cảnh** (biển ngửa ra sau), nằm ngoài tầm với của xoay phẳng. Thiết kế cuối giữ nguyên hình học nhưng đổi **vị trí đứng trong luồng**: một *bậc thang thử-lại* chỉ chạy khi lần đọc đầu đã thất bại — biến thể xoay phẳng, và biến thể **giãn dọc ×2** khi tỷ lệ hộp nằm trong dải mơ hồ **2,5–4,2** — mỗi biến thể chỉ được nhận khi chuỗi mới validate, nên baseline bất biến theo cấu trúc. Trên cùng 36 khung: **42 → 48 lần đọc hợp lệ, 0 thoái lui**; khung 168 đọc đúng `77H5-4374` (độ tin cậy 0,785) qua chuỗi giãn dọc → đọc dòng dưới → cứu dòng trên tại vết cắt 0,55; **ba trong sáu lần đọc mới là đọc sai** của các biển quá mờ ở xa (`docs/reports/21-skew-retry.md`). Một sự cố thực địa buộc bổ sung hai cổng chặn: phiên bản đầu coi biển quân đội đọc đúng (cố ý mang cờ *invalid* theo nguyên tắc nhận-để-loại-trừ) là lần đọc hỏng, đọc lại và nhoè `KV-69-38` thành chuỗi dân sự "hợp lệ" `14D7-069.38` — đúng lớp lỗi tự tin-mà-sai từng phải sửa ở Phase 4; bản cuối chỉ thử lại khi lần đọc đầu **không phân loại được** và không bao giờ thử lại trên **nền đỏ**, cả hai cổng đều có kiểm thử ghim. Việc còn lại thu hẹp về bậc 3: **nắn phối cảnh bốn điểm chưa cài**.

### 7.4.10. Tách lịch chạy giữa xem trực tiếp và xử lý nền

Ba hướng xử lý cho 7.3.10: **chạy tuần tự thay vì song song** — hoãn tác vụ nền tới khi người dùng dừng xem trực tiếp, cái giá là kết quả đầy đủ có muộn hơn (đơn giản nhất cho một máy đơn); **giới hạn số luồng CPU của tác vụ nền** — không đổi trải nghiệm nhưng làm tác vụ nền chậm đi và cần đo để chọn mức chia; **tách tiến trình suy luận ra khỏi tiến trình API** rồi xếp hàng có mức ưu tiên — đúng đắn nhất về kiến trúc và cũng nặng nhất, chỉ đáng làm nếu triển khai nhiều người dùng, khi đó đi kèm hướng 6.4.7. Hệ quả về phương pháp: **mọi con số độ trễ công bố cho tính năng này bắt buộc phải kèm điều kiện đo** — một con số trần trụi sẽ đúng hoặc sai gấp năm lần tuỳ hoàn cảnh.

---

## 7.5. Kết luận chung

**Thứ nhất, hệ thống hoàn chỉnh và chạy được, kiểm chứng được.** Bốn tầng backend–frontend–AI–dữ liệu đóng gói Docker, khởi động một lệnh, xác minh bằng HTTP sống và bằng stack Docker kiểm từ ngoài container; bộ phát hiện đạt **toàn bộ** chỉ tiêu với biên rộng; mọi chỉ tiêu hiệu năng, độ tin cậy và chịu tải đều đạt, trừ NFR-P1 (chỉ đạt ngưỡng tối thiểu) và NFR-P2 (trượt cả sàn). Phải nói kèm: giao diện đã thu gọn còn **ba màn hình** và **một yêu cầu mức *Must* — FR-4.1 — bị đưa ra khỏi phạm vi** (7.3.6), nên bộ *Must* hệ thống đáp ứng là bộ **21**, không phải bộ 22 ban đầu.

**Thứ hai, đồ án đo được hai đại lượng mà tài liệu Việt Nam chưa công bố tách bạch:** đóng góp thuần của khối hậu xử lý theo luật (**+11,39 điểm**, 319 biển sửa đúng, 0 biển làm hỏng); và rủi ro R-04 đo bằng **số liệu Việt Nam thật** — chênh lệch **25,45 điểm** độ chính xác chuỗi giữa biển một dòng và hai dòng, cùng bậc độ lớn với mốc **48,6 điểm** mà Laroca và cộng sự đo trên **RodoSol-ALPR của Brazil** [7]<!-- laroca_2022_crossdataset -->, một analogue quốc tế **không phải số Việt Nam**.

**Thứ ba, và phải nói thẳng: nhận dạng ký tự trên biển hai dòng vẫn là một bài toán mở.** Ba chỉ tiêu độ chính xác OCR không đạt, nguyên nhân không ở tầng hậu xử lý, không ở tầng phát hiện, không ở tầng hình học (cả ba đều đã xử lý và đo tách bạch), mà ở **tầng nhận dạng ký tự** trên quần thể biển hai dòng, vốn chiếm 79,8% dữ liệu vì phản ánh mật độ xe máy Việt Nam.

**Một điều kiện phạm vi đi kèm mệnh đề thứ ba và cũng giới hạn mệnh đề thứ hai.** Tập 2.801 biển có nhãn chuỗi mà mọi con số OCR dựa vào gồm **97,68% biển trắng** và **không một biển đỏ hay biển ngoại giao nào** (7.3.8); ngữ liệu đã gộp thêm biển vàng/xanh ngày 02/08/2026, nhưng **các con số A4–A7 trong quyển này vẫn đo trên ngữ liệu cũ**, nên chúng phải được phát biểu là *"đo trên một tập gồm 97,7% biển trắng"*, không phải *"đo trên biển số Việt Nam"*. Hệ thống **có** năng lực phân loại chín họ biển và bốn màu nền (kiểm chứng ở 97,89% trên 1.565 ảnh có nhãn màu do người gán) nhưng **chưa có dữ liệu** để đo độ chính xác nhận dạng ký tự cho các loại biển hiếm; **"chưa đo được" không đồng nghĩa với "không làm được", và cũng không được trình bày như thể đã đo được.**

Giá trị của đồ án vì vậy không nằm ở một con số state-of-the-art — điều Chương 1 đã cam kết ngay từ đầu là *không* tuyên bố — mà ở ba chỗ khác: **một hệ thống đầy đủ và tái lập được**; **ba đại lượng đo được mà trước đó chỉ được mô tả định tính** (đóng góp hậu xử lý, rủi ro R-04 trên dữ liệu Việt Nam, và độ chính xác bộ nhận màu nền); và **một quy trình đánh giá tự kiểm chứng** đã bắt được rò rỉ dữ liệu, một lập luận vòng tròn, một đặc tính toán học của phash, một con số độ trễ bị nhiễm, một giả thuyết sửa lỗi bị chính dữ liệu bác bỏ, và — nghiêm trọng nhất — **một bộ đo đi tắt qua đường mã của chính sản phẩm nó đang đo** — rồi ghi lại tất cả thay vì che đi.
