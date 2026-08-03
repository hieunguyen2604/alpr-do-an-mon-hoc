# CHƯƠNG 6. KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN

Chương này tổng kết sản phẩm, thừa nhận phần chưa đạt cùng nguyên nhân đã định vị bằng số liệu, và nêu hướng phát triển. Ba nhóm số không có ở Chương 5 (6.2.5, 6.3.8, 6.4.1) được đo sau khi chương đó đã chốt, kèm tệp báo cáo gốc. Nguyên tắc chi phối là **không tô hồng**: hệ thống đạt chỉ tiêu ở tầng phát hiện và tầng phần mềm nhưng **không đạt ba chỉ tiêu độ chính xác OCR (A5, A6, A7; A4 chỉ đạt ngưỡng tối thiểu)**, nguyên nhân nằm gần trọn ở quần thể biển hai dòng.

---

## 6.1. Tổng kết công việc đã thực hiện

### 6.1.1. Điểm lại mười một giai đoạn — mỗi giai đoạn một sản phẩm thật

| Giai đoạn | Sản phẩm thật đã bàn giao |
|:---:|---|
| **Phase 0–1 — Yêu cầu, nghiên cứu** | SRS, 34 yêu cầu chức năng, bảy nhóm phi chức năng, chỉ tiêu đo được bằng số (M0); bảy báo cáo khảo sát, 232 mục BibTeX, sửa 25 lỗi (3 critical) (M1). |
| **Phase 2 — Dữ liệu** | Bộ v3 **15.133 ảnh** từ bảy bộ tải về (**sáu nguồn nguyên tố** sau khử trùng lặp), train 10.592 / val 3.027 / test 1.514. |
| **Phase 3 — Phát hiện** | `models/best.pt` — YOLO11n [16]<!-- jocher_2024_yolo11 -->, mAP@0.5 = 0,9829 trên test v3. |
| **Phase 4 — OCR** | PaddleOCR PP-OCRv5 mobile [17]<!-- cui_2026_ppocrv5 --> cộng luật hậu xử lý theo vị trí; đóng góp thuần **+11,39 điểm** trên 2.801 biển có nhãn chuỗi. |
| **Phase 5–6 — Backend, frontend** | FastAPI, **10 thao tác trên 9 đường dẫn**, Swagger đầy đủ (M5); React, build sạch; *2026-07-20 thu gọn còn **ba màn hình** — **FR-4.1 mức Must ra khỏi phạm vi** (6.3.6).* |
| **Phase 7 — Kiểm thử** | Gần nhất 2026-08-02: **1.001 thu thập / 1.000 pass / 1 xfail / 0 fail**; bao phủ tầng nghiệp vụ **87,7%** (`07-testing-report.md`). |
| **Phase 8–10 — Triển khai, tài liệu, bảo vệ** | Hai image, `docker compose up` trên máy sạch, kiểm bằng `curl` từ ngoài container (M8); quyển đồ án; 21 slide, poster, kịch bản demo, 56 câu hỏi phản biện. |

> **Lưu ý tên gọi.** `yolo_v3` là **phiên bản thứ ba của bộ dữ liệu**, không liên quan "YOLOv3"; mô hình dùng là **YOLO11n**. Pipeline giả lập `StubPipeline` (chứng minh NFR-M5) đã ra khỏi đường chạy chính; phương án lùi `UnavailablePipeline` ném lỗi thay vì bịa biển số. **Không con số nào trong quyển này do stub sinh ra.**

### 6.1.2. Bảng đối chiếu mục tiêu Phase 0 với kết quả thật

**Bảng 6.1.** Đối chiếu chỉ tiêu cam kết ở Phase 0 với số đo trên `best.pt` (bản cô đọng của T5.7)

| Mã | Chỉ tiêu | Mục tiêu Phase 0 | Đo được (`best.pt`) | Kết quả |
|:---:|---|---:|---:|:---:|
| A1 · A2 · A3-P · A3-R | mAP@0.5 · mAP@0.5:0.95 · Precision · Recall (phát hiện) | 0,90 · 0,65 · 0,92 · 0,90 | **0,9829 · 0,7834 · 0,9837 · 0,9714** | ✅ đạt |
| A4 | 1 − CER (mức ký tự) | 0,95 | **0,9454** | 🟡 đạt ngưỡng tối thiểu (0,92) |
| A5 · A6 · A6−A5 | Chuỗi trước · sau hậu xử lý · đóng góp hậu xử lý (điểm %) | 0,85 · 0,90 · — | **0,6373 · 0,7512 · +11,39** | ❌ · ❌ · (thuần dương) |
| A7 | Độ chính xác E2E toàn trình | 0,88 | **0,5552** | ❌ không đạt* |
| A8 | Chênh lệch layout, phát hiện (điểm %) | — | **2,09** | (rất nhỏ) |
| P1 | Độ trễ E2E một ảnh, p95 (ms) | ≤ 800 | **1.143,10** | 🟡 đạt ngưỡng tối thiểu (1.500) |
| P4 · P5 · P6 | Nạp mô hình (s) · Overhead API p95 (ms) · Truy vấn 10.000 bản ghi p95 (ms) | ≤ 15 · ≤ 50 · ≤ 500 | **6,41 · 19,01 · 18,71** | ✅ đạt |
| P7a · P7b · R4 · SC1 | RSS pipeline · RSS máy chủ backend (GB) · Thành công khi chạy liên tục · Yêu cầu đồng thời ổn định | ≤ 2 · ≤ 2 · ≥ 99% · ≥ 5 | **0,759 · 0,806 · 100%** (2.028 yêu cầu, soak 15 phút) · **10** | ✅ đạt |

\* A7 phải đọc như **cận dưới bi quan**: đo trên ảnh crop, ngoài phân bố huấn luyện của bộ phát hiện, nên tỉ lệ bỏ sót bị thổi phồng (6.3.1).

Vạch ngăn "đạt / không đạt" trùng khít vạch ngăn giữa tầng phát hiện và tầng nhận dạng ký tự: **mọi chỉ tiêu phát hiện, độ tin cậy và chịu tải đều đạt; mọi chỉ tiêu độ chính xác OCR chuỗi đầy đủ đều không đạt.** Riêng NFR-P1 chỉ đạt ngưỡng tối thiểu và NFR-P2 trượt cả sàn (6.3.4, 6.3.5) — đánh đổi có chủ ý lấy 34 biển đọc thêm.

---

## 6.2. Các kết quả đạt được

### 6.2.1. Một hệ thống hoàn chỉnh, chạy được, xác minh bằng HTTP thật

Backend FastAPI, frontend React, pipeline AI và lớp dữ liệu SQLite/SQLAlchemy đóng gói Docker, khởi động một lệnh trên máy sạch. Kiểm chứng: 10 thao tác API phản hồi đúng qua HTTP sống; `/health` báo `model_loaded: true` với engine thật; stack Docker kiểm bằng `curl` từ **ngoài** container.

### 6.2.2. Bộ phát hiện đạt toàn bộ chỉ tiêu với biên rộng

Trên tập test v3 (1.514 ảnh, 1.611 đối tượng), YOLO11n [16]<!-- jocher_2024_yolo11 --> vượt **cả bốn** chỉ tiêu ở mức *mục tiêu* chứ không chỉ *ngưỡng tối thiểu* (Bảng 6.1), mAP@0.5 tới **0,9829**. Chênh lệch hai layout chỉ **2,09 điểm** — nếu toàn trình kém trên biển hai dòng thì lỗi **không** ở khâu phát hiện. Điểm yếu duy nhất (T5.4c): dải "rất nhỏ" (dưới 0,5% diện tích ảnh) chỉ đạt **0,8553**. Điều kiện đọc kèm: bài toán **một lớp**, nên mAP@0.5 cao là bình thường.

### 6.2.3. Đo được đóng góp định lượng của khối hậu xử lý

**Đóng góp khoa học riêng thứ nhất.** Phần lớn công trình ALPR chỉ mô tả hậu xử lý định tính; đồ án đo tách bạch trên 2.801 biển có nhãn chuỗi: A5 = 0,6373, A6 = 0,7512, **A6 − A5 = +11,39 điểm phần trăm**. Bộ luật sửa đúng **319 biển**, làm hỏng **0 biển**, dồn gần trọn vào biển hai dòng (**+13,97** so với **+1,23 điểm**); cải thiện thuần một chiều chứng tỏ bộ luật đủ bảo thủ. Đóng góp bị chặn vì nút thắt ở tầng OCR: luật không với tới chuỗi sai nhiều ký tự do engine đọc hụt cả cụm.

### 6.2.4. Đo được rủi ro R-04 bằng số liệu Việt Nam thật

**Đóng góp khoa học riêng thứ hai.** Rủi ro R-04 — "pipeline OCR dựng sẵn gãy trên biển hai dòng" — vốn *định tính* từ Phase 0, nay đo được trên dữ liệu Việt Nam (T5.5c). Trên 567 biển một dòng so với 2.234 biển hai dòng, A6 đạt 0,9541 so với 0,6996 — chênh **25,45 điểm** (chênh 1 − CER và A5 lần lượt 5,81 và 38,18 điểm). Biển **một dòng về cơ bản đã giải xong** (A6 vượt mục tiêu 0,90); toàn bộ khoảng thiếu nằm ở biển **hai dòng**, chiếm **79,8%** tập có nhãn chuỗi — phản ánh 77 triệu xe máy Việt Nam [1]<!-- dantri_2024_77trieuxemay -->. Chênh lệch này **cùng bậc độ lớn** với mốc quốc tế: Laroca và cộng sự (VISAPP 2022) đo chênh **48,6 điểm** giữa biển một dòng (94,3%) và hai dòng (45,7%) trên bộ dữ liệu **RodoSol-ALPR của Brazil** [7]<!-- laroca_2022_crossdataset -->.

> **Cảnh báo trích dẫn bắt buộc.** Cặp số 94,3% / 45,7% và chênh 48,6 điểm đo trên **RodoSol-ALPR (Brazil)** [7]<!-- laroca_2022_crossdataset -->, **không phải** số liệu Việt Nam — chỉ là *analogue định lượng* về độ khó của biển hai dòng. Con số 25,45 điểm mới là số đo Việt Nam của đồ án.

Giá trị học thuật: chưa nghiên cứu biển số Việt Nam công khai nào công bố hai con số một dòng / hai dòng tách bạch trên cùng một hệ thống; kết luận — biển hai dòng là *đặc tính có cấu trúc của bài toán* — đặt nền cho 6.4.1, nhất quán với dòng nghiên cứu coi tính độc lập layout là yêu cầu thiết kế [23]<!-- laroca_2021_layout -->.

### 6.2.5. Bộ nhận màu nền biển đạt 97,89% — một nguồn bằng chứng mà chuỗi ký tự không thể mang

**Đóng góp kỹ thuật riêng thứ ba.** Theo Thông tư 79/2024/TT-BCA, biển vàng kinh doanh vận tải mang **đúng cùng bố cục ký tự** với biển trắng cá nhân; biển ngoại giao lại nền trắng — chỉ *cặp* (chuỗi, màu) mới định danh được loại phương tiện. Bộ phân loại (`ai/inference/plate_color.py`) đọc biểu đồ HSV, trả `unknown` khi không chắc chắn. Đo trên bộ `nguyenluanai/license-plate-color` v4 (CC BY 4.0) — bộ mà bộ phân loại **chưa từng được hiệu chỉnh theo**: vàng **98,56%** (694 ảnh), trắng **97,40%** (808), xanh **96,83%** (63), **tổng 97,89% trên 1.565 ảnh** (`19-color-accuracy.json`); 542 ảnh bị loại là toàn bộ lớp `bien_unknown` — ảnh mà chính người gán nhãn cũng không đọc được màu nền.

Ràng buộc an toàn khi hợp nhất hai nguồn: màu chỉ được nâng cấp một ứng viên mà bộ luật chuỗi đã coi là hợp lý và tự đánh dấu nhập nhằng, nên **biển quân đội bị đọc nhầm màu thì vẫn là biển quân đội**. Cùng đợt, họ biển (chín giá trị `PlateKind`) và chuỗi hiển thị đúng định dạng được giữ tới CSDL, chữa lỗi biển đỏ đọc đúng từng bị hiển thị "Sai định dạng biển số". Hạn chế: bộ dữ liệu đo **không chứa biển đỏ và biển ngoại giao** (6.3.8).

### 6.2.6. Một quy trình đánh giá có kiểm chứng — bản thân tính trung thực là một kết quả

Đóng góp cuối là **cách các con số được kiểm tra**: năm lần quy trình tự bắt lỗi của chính nó, cả năm đều được ghi lại. **(1)** Rò rỉ train↔test: split cũ có hàng nghìn cặp gần trùng vắt ranh giới; nâng ngưỡng gộp 5 → 10, chia lại thành v3 (6.3.2). **(2)** Một lập luận vòng tròn trong chính phép kiểm đó: 0 cặp vắt split ở ngưỡng Hamming 10 là **hệ quả định nghĩa**, không phải bằng chứng sạch. **(3)** phash ở cài đặt này chỉ sinh khoảng cách Hamming **chẵn**, nên ngưỡng lẻ vô nghĩa. **(4)** Bộ đo OCR **không đi qua đường mã sản phẩm**: `ai/evaluation/ocr_accuracy.py` không dựng `ALPRPipeline`, nên logic tầng điều phối vô hình với con số công bố; bản sửa tách bước cứu biển hai dòng thành hai hàm dùng chung; khoảng cách này không gây lỗi và **chưa có cơ chế tự động nào canh giữ nó**. **(5)** Một giả thuyết sửa lỗi hợp lý — đọc riêng từng nửa biển hai dòng rồi nối chuỗi — bị chính dữ liệu bác bỏ áp đảo (`15-two-line-ab.json`); bản sửa cuối giữ thiết kế ghép hiện hành, đo 900 biển không ca hỏng nào. Ngoài ra quy trình còn **bác bỏ một con số độ trễ cũ** (6.3.4). **Một chương đánh giá không kể lại lần nào nó tự nghi ngờ chính mình là một chương đã tự tước bỏ khả năng bị kiểm chứng.**

---

## 6.3. Các hạn chế của đồ án

Mục này theo nguyên tắc 5.9.3: nêu hạn chế, mức nghiêm trọng, và đã làm gì để giảm thiểu — kể cả khi câu trả lời là "chưa làm được gì".

### 6.3.1. Hạn chế lớn nhất: OCR biển hai dòng còn yếu, kéo E2E chưa đạt

*Mức nghiêm trọng: cao — hạn chế trung tâm của toàn đồ án.* NFR-A5 = **0,6373** (thiếu 16,27 điểm so với ngưỡng 0,80); NFR-A6 = **0,7512** (thiếu 9,88 so với 0,85); NFR-A7 = **0,5552** (thiếu 26,48 so với 0,82); NFR-A4 = **0,9454**, vượt ngưỡng tối thiểu 0,92 nhưng dưới mục tiêu 0,95. **Nguyên nhân ở tầng OCR chứ không phải tầng hậu xử lý**, ba bằng chứng độc lập: *tách theo layout* (T5.5c) — toàn bộ khoảng thiếu nằm ở biển hai dòng, chiếm 79,8% tập; *phân tích lỗi* (T5.8) — 428/445 ca nhầm ký tự và **73/73** ca thiếu ký tự thuộc biển hai dòng; *đóng góp hậu xử lý bị chặn trên* (T5.5b) — ký tự bị xoá chiếm 56,8% toàn bộ lỗi, mà ký tự chưa từng được đọc ra thì **về nguyên tắc** không luật nào phục hồi được. Hướng khắc phục bắt buộc nằm ở tầng nhận dạng (6.4.1).

> **Cảnh báo hiệu lực.** A7 = 0,5552 đo trên ảnh **crop biển số**, ngoài phân bố huấn luyện của bộ phát hiện, nên tỉ lệ bỏ sót 11,96% bị thổi phồng — **cận dưới bi quan** (5.5.5). Đo A7 đúng cách đòi hỏi tập test hiện trường có nhãn chuỗi, việc chưa làm được (6.4.3).

### 6.3.2. Rò rỉ dữ liệu tồn dư không khử được bằng băm tri giác

*Mức nghiêm trọng: cao.* Tại ngưỡng Hamming **12** vẫn còn **791 cặp** train↔test gần trùng, tại ngưỡng **15** là **3.529 cặp**. Nghiêm trọng hơn là rò rỉ **ngữ nghĩa** không ngưỡng phash nào bắt được: cùng một xe ở góc khác mang cùng biển số nhưng khoảng cách Hamming lớn. *Đã áp dụng:* nâng ngưỡng gộp 5 → 10, đo rò rỉ ở nhiều ngưỡng. *Chưa áp dụng được:* chia split theo nhóm biển số — bất khả thi vì phần lớn corpus thiếu nhãn chuỗi. **Hệ quả bắt buộc nêu khi bảo vệ: mọi chỉ số ở tầng phát hiện và OCR phải được coi là cận trên lạc quan.**

### 6.3.3. Tập test không xuyên bộ dữ liệu, nên mAP lạc quan hơn khi triển khai

*Mức nghiêm trọng: cao.* Train và test lấy từ cùng sáu nguồn nguyên tố, nên thiết lập chỉ đo tổng quát hoá *trong phân bố*. Độ chính xác ALPR sụt đáng kể khi đánh giá xuyên bộ dữ liệu [7]<!-- laroca_2022_crossdataset -->, nên mAP@0.5 = 0,9829 gần như chắc chắn lạc quan hơn thực tế. *Giảm thiểu trong khuôn khổ đồ án: không có*; cách đúng ở 6.4.2.

### 6.3.4. Độ trễ — đạt ngưỡng tối thiểu, và mức vượt mục tiêu là một đánh đổi có chủ ý

p95 = **1.143,10 ms** — dưới sàn 1.500 ms nhưng vượt mục tiêu 800 ms 1,43 lần; trung vị **405,77 ms** (100 ảnh test v3, máy rảnh). **Thoái lui có chủ ý:** tắt bậc thang thử-lại đưa p95 về **866,3 ms** nhưng mất 34 biển đọc thêm (+0,75 điểm A6); chi phí dồn vào đuôi vì bậc thang chỉ chạy sau khi lần đọc đầu thất bại. Bật cả ba biến thể: p95 **1.514,26 ms**, vượt cả sàn; riêng bậc **siêu phân giải** chiếm hơn nửa (+319 ms p95) mà không mua được biển nào, nên tắt mặc định — số 0 ấy là **số 0 cấu trúc** (cổng chỉ mở cho vùng cắt dưới 200 px, 0/120 mẫu lọt): "chi phí đã đo, lợi ích chưa ai đo được". Một báo cáo trước ghi p95 = **5.857 ms**; con số đó đã bị **bác bỏ** vì điều kiện đo bị nhiễm (5.6.1). Ngân sách thật (T5.6b): OCR **64,3%**, phát hiện **34,0%**; hướng tối ưu đúng là **giảm số lần phải thử lại** (6.4.1).

### 6.3.5. Nút "Huỷ tác vụ" video chưa hoàn chỉnh; một số chỉ tiêu chưa đo

*Mức nghiêm trọng: trung bình đến thấp.* Chương 4 mô tả khả năng huỷ tác vụ video, nhưng bản cài đặt **chưa có route HTTP nào đặt được trạng thái huỷ** — hạng mục còn treo. Trong bốn chỉ tiêu chưa đo, **ba đã đo xong 02/08/2026** ([33-runtime-nfr.json](../reports/33-runtime-nfr.json)): P2 (FPS webcam) ❌ **2,379 FPS** (sàn 3); P3 (xử lý video) ✅ **0,746×** thời gian thực; R5 (CSDL qua khởi động lại) ✅ **0/9.031 bản ghi mất**; A9 (tách theo điều kiện ảnh) ⬜ chưa đo — bộ dữ liệu **không có nhãn điều kiện ảnh**, tức *thiếu điều kiện* chứ không phải *chưa tới lượt*. **Một trong ba mã đo ra kết quả trượt** — P2 trượt vì đuôi độ trễ của bậc thang thử-lại, trung vị 180 ms (≈5,6 FPS) vẫn vượt mục tiêu (5.6.4). Phép đo gọi trực tiếp `POST /api/detect/frame` vì trang Webcam đã gỡ 2026-07-20.

### 6.3.6. Một yêu cầu mức *Must* (FR-4.1) đã bị đưa ra khỏi phạm vi

*Mức nghiêm trọng: trung bình. Hạn chế duy nhất phát sinh từ một **quyết định** chứ không từ giới hạn kỹ thuật.* Ngày 2026-07-20 giao diện thu gọn hai đợt còn **ba trang**: FR-3.1, FR-3.4 M → W; **FR-4.1 M → W**; FR-4.2 S → W; bảng MoSCoW từ 22/7/3/2 sang **21 Must / 6 Should / 3 Could / 4 Won't** trên 34 yêu cầu. **FR-4.1 là yêu cầu *Must* đầu tiên và duy nhất bị đưa ra khỏi phạm vi**; tiêu chí thành công số 1 ở mục 1.2.3 chỉ đúng theo bộ **21** *Must* sau thay đổi. Nhưng **phần mất đi là màn hình hiển thị, không phải năng lực hệ thống**: `GET /api/statistics` vẫn phục vụ và vẫn có kiểm thử tích hợp; FR-4.3–FR-4.8 không đổi. *Đánh đổi:* gỡ `recharts`, gói tải về giảm ~730 KB → **328,8 KB (−55%)**. *Giảm thiểu:* mã hai trang giữ có chủ đích (6.4.6).

### 6.3.7. SQLite chỉ cho phép một tiến trình ghi tại một thời điểm

*Mức nghiêm trọng: thấp trong phạm vi đồ án.* SQLite khoá ghi mức toàn tệp. Với một người vận hành (giả định A-04) đây không phải nút thắt — hệ thống ổn định ở 10 yêu cầu đồng thời, soak 100%; đa người dùng ghi đồng thời thì giới hạn thành thực; hướng khắc phục: PostgreSQL (6.4.7).

### 6.3.8. Bộ dữ liệu lệch nặng về biển trắng, nên kết luận về độ chính xác OCR chỉ áp cho biển trắng

*Mức nghiêm trọng: cao. Hạn chế này quy định **phạm vi hiệu lực** của mọi con số OCR trong quyển.* Phân bố của **2.801 ảnh có nhãn ký tự** — tập sinh ra NFR-A4 đến A7 (`17-plate-type-audit.json`): trắng **2.736 / 97,68%**; vàng **20 / 0,71%**; xanh **4 / 0,14%**; đỏ **0**; NG/QT **0**; không đọc được màu **41 / 1,46%**. Hệ quả: câu phát biểu đúng khi bảo vệ là *"1 − CER = 0,9454 trên một tập gồm 97,7% biển trắng"*, không phải *"trên biển số Việt Nam"*.

> **Cập nhật 02/08/2026 — hạn chế đã thu hẹp, nhưng chưa gỡ.** **Mọi con số A4–A7 trong quyển vẫn đo trên ngữ liệu 2.801 mẫu**; phần dưới là nguyên liệu cho lần đo sau. **(a)** Đã gộp **521 biển hiếm** từ `nguyenluanai/license-plate-color` v4 ([30-rare-plate-integration.md](../reports/30-rare-plate-integration.md)): tổng ngữ liệu **2.801 → 3.322**, vàng **20 → 476**, xanh **4 → 45**, tỷ lệ biển hiếm **0,86% → 15,7%**; biển vàng chuyển sang **đánh giá được**. **(b)** Tập ảnh toàn cảnh gán nhãn 02/08 ([34-scene-level-a7.md](../reports/34-scene-level-a7.md)) **có** biển đỏ quân đội, biển xanh, ngoại giao và sê-ri LD — quá nhỏ để công bố độ chính xác theo loại, nhưng đủ để không còn nói "bằng không". **(c)** Biển đỏ và ngoại giao vẫn không có nguồn công khai đủ lớn ([17-plate-type-dataset-survey.md](../reports/17-plate-type-dataset-survey.md)) — hạn chế **thật**, không phải "chưa tới lượt".

Hai điều dễ bị gộp khi trả lời phản biện: **hệ thống *có* năng lực phân loại loại biển** (kiểm chứng 97,89% trên 1.565 ảnh, 6.2.5) nhưng ***chưa có dữ liệu* đo độ chính xác ký tự cho biển hiếm** — vàng (n = 20) và xanh (n = 4) không có ý nghĩa thống kê, đỏ và ngoại giao không đánh giá được. **"Chưa đo được" không đồng nghĩa "không làm được", và không được trình bày như thể đã đo được** (6.4.8).

### 6.3.9. Bước làm thẳng biển nghiêng (rectify) chưa được cài đặt — ĐÃ XỬ LÝ 21/07/2026, xem cuối mục

Luồng biển hai dòng gồm bốn bước **rectify → phân loại số dòng → tách đôi → ghép ngang**, nhưng bước đầu chưa từng được cài đặt; một chú thích trong `ai/inference/recognizer.py` từng khẳng định sai rằng ảnh cắt đã được làm thẳng — hộp bao YOLO là hộp trục-thẳng; đã sửa. Hệ quả ở khung 168 của video demo: biển hai dòng nghiêng có hộp bao rộng bất thường, tỷ lệ 3,48 vượt ngưỡng 2,50, bị phân loại **một dòng (sai)**, chuỗi OCR rỗng; cùng biển ấy chụp gần chính diện đọc **đúng** `77H5-4374`. **Cập nhật 21/07/2026 — đã xử lý** bằng bậc thang thử-lại (6.4.9); còn lại: **nắn phối cảnh bốn điểm chưa cài**.

### 6.3.10. Xem trực tiếp và xử lý nền tranh chấp CPU với nhau

Trang nhận dạng video chạy đồng thời xem trực tiếp (`POST /api/detect/frame` từng khung) và tác vụ nền trên cùng CPU không GPU. Đo cùng một ảnh: **89–97 ms**/khung khi không có tác vụ nền, **230–462 ms** khi có — chậm **2,5–5 lần**. Đây là hệ quả quyết định môi trường Phase 0 (suy luận CPU), không phải lỗi lập trình; mọi số đo độ trễ của xem trực tiếp vì thế phụ thuộc việc có tác vụ nền hay không (6.4.10).

---

## 6.4. Hướng phát triển

Các hướng dưới đây **bắt nguồn từ số liệu Chương 5**; thứ tự là mức ưu tiên do chính kết quả quyết định.

### 6.4.1. Huấn luyện lại module nhận dạng (rec) riêng cho biển số Việt Nam — hướng quan trọng nhất

Vì nút thắt nằm ở tầng OCR (6.3.1), hướng tác động lớn nhất là **thay hoặc huấn luyện lại riêng module rec** thay vì dùng trọng số PaddleOCR đa mục đích [17]<!-- cui_2026_ppocrv5 -->. Bốn cách, đầu tư tăng dần: (1) fine-tune module rec theo công thức PP-OCR trên CCPD [67]<!-- paddlepaddle_nd_plateapp -->; (2) mô hình rec hỗ trợ biển đa dòng từ thiết kế — TransLPRNet [121]<!-- arxiv_2025_translprnet --> hay LPTR-AFLNet [75]<!-- xu_2025_lptraflnet -->; (3) tách–ghép biển hai dòng trước khi đưa vào rec [64]<!-- we0091234_nd_doubleplatesplit -->; (4) mô hình chuyên biệt huấn luyện từ đầu — CRNN kèm chú ý [70]<!-- dang_2024_crnn --> hoặc pipeline chuyên xe máy Việt Nam [21]<!-- le_2023_vnmotorcycle -->. Nhờ NFR-M5, thay module rec không đụng mã tầng API.

**Ba phép đo độc lập cùng củng cố thứ tự ưu tiên này**, cả ba can thiệp ngoài mô hình nhận dạng: luật hậu xử lý **+11,39 điểm** A6 · 319 biển (6.2.3); bước cứu dòng trên **209 biển** (5.5.6); bậc thang thử-lại **+0,75 điểm** A6 · 34 biển (5.5.7). Cộng lại chúng nâng A6 từ **0,6098** lên **0,7512** không tốn một giây GPU — nhưng vẫn thiếu **9,88 điểm**, và **dư địa đã cạn**: can thiệp mới nhất chỉ mua thêm 34 biển trên 2.801. Ký tự chèn thừa gần như biến mất (giảm 88%) trong khi ký tự **bị xoá** chiếm 56,8% toàn bộ lỗi (5.5.1): lỗi đã dịch sang "ký tự chưa từng được đọc ra", thứ không tầng nào ngoài mô hình nhận dạng phục hồi được. Mục 6.4.3 là điều kiện tiên quyết.

> **Hai lượt thử đã thực hiện và đều thất bại — kết quả âm cũng là kết quả.** Lượt **thứ nhất** (28/07/2026): model đọc **0/7** ảnh demo so với **7/7** của model gốc, do tập huấn luyện **sai nhãn sinh ra một cách im lặng**: cơ chế "ảnh thay thế" kích hoạt khi không mở được ảnh gốc — mà `datasets/raw/**` nằm trong `.gitignore` — nên mọi nhãn bị ghép với ảnh của biển khác; cơ chế đã gỡ (`25-finetune-attempt-failed.md`). Lượt **thứ hai** (02/08/2026) huấn luyện thành công nhưng không được giao: qua đường ống thật nó **kém hơn model gốc** (A6 = 0,6762 so với 0,7512) — PaddleOCR đánh giá nhánh rec bằng *nguyên ảnh*, còn đường ống *phát hiện chữ trước*, nên model fine-tune đọc mảnh vụn rất kém. Bỏ bước phát hiện chữ thì nó thắng đậm (A6 = **0,8758**, hơn **12,46 điểm**), nhưng cấu hình ấy vẫn bị bác: trên bộ demo ảnh toàn cảnh qua bộ phát hiện thật, thứ tự **đảo ngược** (17/22 tụt còn 13/22), và chế độ chỉ-nhận-dạng **không thể trả chuỗi rỗng** (0/1.606 khung so với 173) nên khi bộ phát hiện bắt nhầm thì nó *bịa* ra biển. Lượt một là **lỗi dữ liệu**, lượt hai là **lỗi phép đo** (`31-detection-stage-ablation.md`).

### 6.4.2. Xây dựng tập test xuyên bộ dữ liệu

Để chữa 6.3.3: giữ một nguồn không dùng huấn luyện làm tập test xuyên bộ, báo cáo song song mAP trong phân bố và xuyên bộ [7]<!-- laroca_2022_crossdataset -->; kết hợp **chia split theo nhóm biển số** để khử cả rò rỉ ngữ nghĩa ở 6.3.2.

### 6.4.3. Bổ sung nhãn chuỗi biển số cho toàn tập

Hiện chỉ **2.801** biển có nhãn chuỗi trong khi corpus có 15.133 ảnh; mẫu số nhỏ này đe doạ tính hợp lệ (5.9.3) và chặn việc đo NFR-A7 trên ảnh hiện trường (6.3.1). Hướng khắc phục: gán nhãn chuỗi bán tự động — hệ thống sinh nhãn nháp, người soát lại — hoặc bổ sung dữ liệu tổng hợp theo hướng hợp nhất đa nguồn [122]<!-- arxiv_2026_multinationalfusion -->.

### 6.4.4. Tăng tốc suy luận: lượng tử hoá OCR, đóng gói ONNX/OpenVINO cả hai tầng

Phân rã ngân sách (6.3.4) chỉ ra việc phải làm: OCR chiếm 64,3%, phát hiện 34,2%. **Lượng tử hoá INT8 module OCR** tận dụng tập lệnh VNNI/AVX-512 trên CPU Intel [123]<!-- onnxruntime_2025_quantization --> có đòn bẩy cao nhất. **Đóng gói cả hai tầng sang ONNX Runtime hoặc OpenVINO** [18]<!-- ultralytics_2026_openvinoexport -->[96]<!-- ultralytics_2026_export -->; hiện đường suy luận chạy PyTorch thuần, và **thí nghiệm so sánh backend (bảng T5.6c) là hạng mục đã chuẩn bị nhưng chưa chạy**. Mọi con số tăng tốc phải đo trên cùng cấu hình phần cứng và công bố kèm cấu hình.

### 6.4.5. Bám vết đối tượng qua khung hình cho video (SORT/DeepSORT)

Hệ thống hiện gộp các lần nhận dạng trùng theo **chuỗi ký tự** — gãy khi OCR đọc sai cùng một biển ở các khung khác nhau. Hướng đúng là bám vết bằng SORT/DeepSORT: gộp theo ID theo dõi, ổn định trước lỗi OCR lẻ tẻ, mở đường cho **bỏ phiếu theo thời gian**.

### 6.4.6. Khôi phục hai màn hình đã gỡ, từ lịch sử git

Hướng chữa trực tiếp 6.3.6 và **rẻ nhất trong mục 6.4** — chỉ đòi hỏi một quyết định phạm vi. Đây là *phục hồi* chứ không phải *xây mới*: năng lực máy chủ chưa bao giờ bị gỡ (`POST /api/detect/frame`, `GET /api/statistics`, `GET /health` đều có kiểm thử tích hợp); mã giao diện và hợp đồng kiểu còn nguyên trong lịch sử git. Quy trình: lấy lại tệp, nối route, chạy `tsc --noEmit` và `vite build`; thư viện biểu đồ nên chọn bản nhẹ hơn `recharts` hoặc nạp trễ. Hướng này khôi phục một chỉ tiêu đã cam kết (FR-4.1 mức Must) chứ không nâng chất lượng nhận dạng — nếu chỉ làm được một việc thì 6.4.1 vẫn đáng làm trước.

### 6.4.7. Chuyển sang PostgreSQL nếu triển khai đa người dùng

Khi có nhiều người ghi đồng thời nên chuyển sang **PostgreSQL** (khoá mức hàng). Nhờ truy cập dữ liệu đi qua SQLAlchemy 2.0 và tầng repository, việc chuyển giới hạn ở cấu hình kết nối và migration, không đụng mã nghiệp vụ hay API.

### 6.4.8. Thu thập dữ liệu cho các loại biển hiếm — điều kiện để mở rộng phạm vi kết luận

Hướng chữa trực tiếp 6.3.8, **không đòi hỏi thay đổi gì trong hệ thống**: năng lực phân loại đã kiểm chứng (6.2.5), thứ thiếu là dữ liệu để đo. Ba việc, mức khó tăng dần: (1) **biển vàng — đã có nguồn**: 694 ảnh của `nguyenluanai/license-plate-color`, tên tệp chứa sẵn chuỗi biển số; trở ngại là phép kéo méo về 640×640, xử lý bằng lấy ảnh gốc rồi soát nhãn; (2) **biển đỏ và ngoại giao**: nguồn công khai rất nhỏ — đủ cho tập kiểm thử, không đủ huấn luyện; cần gom bản tăng cường theo ảnh gốc và soát giấy phép tự khai; (3) **biển chuyên dùng (LD, DA, RM, HC, KT, CD, T)**: chưa có nguồn — thu thập tại chỗ hoặc ghi rõ ngoài phạm vi. Giá trị của hướng này là **mở rộng phạm vi mà các kết luận có hiệu lực**, không phải nâng độ chính xác.

### 6.4.9. Cài đặt bước làm thẳng biển nghiêng — ĐÃ THỰC HIỆN 21/07/2026

Ba bậc: (1) `cv2.minAreaRect` rồi `warpAffine` xoay ngược; (2) đo lại số dòng trên ảnh đã nắn; (3) nắn phối cảnh bốn điểm. **Kỷ luật đo lường**: tập nhãn hiện có gồm ảnh cắt sẵn gần chính diện, không chứa dạng lỗi này, nên phải đo trên tập ảnh cắt **do chính bộ phát hiện sinh ra từ ảnh toàn cảnh** — *tập đánh giá phải chứa dạng lỗi mà bản sửa nhắm tới*.

**Kết quả (21/07/2026).** Kỷ luật trên **bác bỏ thiết kế đầu tiên**: bậc 1+2 dạng tiền xử lý luôn-bật qua toàn bộ kiểm thử tổng hợp nhưng trên 36 khung do detector sinh từ video demo lại **thua baseline 42 → 40** (`minAreaRect` fit sai trên crop nhỏ). Thiết kế cuối là *bậc thang thử-lại* chỉ chạy khi lần đọc đầu thất bại — xoay phẳng, và **giãn dọc ×2** khi tỷ lệ hộp trong dải mơ hồ 2,5–4,2 — mỗi biến thể chỉ được nhận khi chuỗi mới validate, nên baseline bất biến theo cấu trúc: **42 → 48 lần đọc hợp lệ, 0 thoái lui**; khung 168 đọc đúng `77H5-4374` (`21-skew-retry.md`). Một sự cố thực địa (thử lại biển quân đội `KV-69-38` rồi nhoè thành chuỗi dân sự "hợp lệ") buộc thêm hai cổng chặn có kiểm thử ghim: chỉ thử lại khi lần đọc đầu **không phân loại được**, không bao giờ trên **nền đỏ**. Còn lại: **nắn phối cảnh bốn điểm chưa cài**.

### 6.4.10. Tách lịch chạy giữa xem trực tiếp và xử lý nền

Ba hướng cho 6.3.10: **chạy tuần tự** — hoãn tác vụ nền tới khi dừng xem trực tiếp; **giới hạn số luồng CPU của tác vụ nền**; **tách tiến trình suy luận khỏi tiến trình API** với hàng đợi có ưu tiên — đúng nhất về kiến trúc, chỉ đáng làm khi triển khai nhiều người dùng cùng 6.4.7. Mọi con số độ trễ của tính năng này bắt buộc kèm điều kiện đo.

---

## 6.5. Kết luận chung

**Thứ nhất, hệ thống hoàn chỉnh, chạy được, kiểm chứng được.** Bốn tầng backend–frontend–AI–dữ liệu đóng gói Docker, khởi động một lệnh, xác minh bằng HTTP sống; bộ phát hiện đạt **toàn bộ** chỉ tiêu với biên rộng; mọi chỉ tiêu hiệu năng, độ tin cậy và chịu tải đều đạt, trừ NFR-P1 (chỉ đạt ngưỡng tối thiểu) và NFR-P2 (trượt cả sàn). Phải nói kèm: giao diện còn **ba màn hình** và một yêu cầu mức *Must* — FR-4.1 — bị đưa ra khỏi phạm vi (6.3.6), nên bộ *Must* hệ thống đáp ứng là bộ **21**, không phải 22.

**Thứ hai, đồ án đo được hai đại lượng mà tài liệu Việt Nam chưa công bố tách bạch:** đóng góp thuần của khối hậu xử lý theo luật (**+11,39 điểm**, 319 biển sửa đúng, 0 biển làm hỏng); và rủi ro R-04 đo bằng **số liệu Việt Nam thật** — chênh **25,45 điểm** độ chính xác chuỗi giữa biển một dòng và hai dòng, cùng bậc độ lớn với mốc **48,6 điểm** Laroca đo trên **RodoSol-ALPR của Brazil** [7]<!-- laroca_2022_crossdataset --> — analogue quốc tế, **không phải số Việt Nam**.

**Thứ ba, và phải nói thẳng: nhận dạng ký tự trên biển hai dòng vẫn là một bài toán mở.** Ba chỉ tiêu độ chính xác OCR không đạt; nguyên nhân không ở tầng hậu xử lý, tầng phát hiện hay tầng hình học — cả ba đã xử lý và đo tách bạch — mà ở **tầng nhận dạng ký tự** trên quần thể biển hai dòng, chiếm 79,8% dữ liệu. Điều kiện phạm vi: tập 2.801 biển gồm **97,68% biển trắng** (6.3.8), nên phải phát biểu là *"đo trên một tập gồm 97,7% biển trắng"*. Hệ thống **có** năng lực phân loại chín họ biển và bốn màu nền (97,89% trên 1.565 ảnh) nhưng **chưa có dữ liệu** đo độ chính xác ký tự cho biển hiếm; "chưa đo được" không đồng nghĩa "không làm được".

Giá trị của đồ án vì vậy không nằm ở một con số state-of-the-art — điều Chương 1 đã cam kết là *không* tuyên bố — mà ở ba chỗ: **một hệ thống đầy đủ và tái lập được**; **ba đại lượng đo được mà trước đó chỉ được mô tả định tính** (đóng góp hậu xử lý, rủi ro R-04 trên dữ liệu Việt Nam, bộ nhận màu nền); và **một quy trình đánh giá tự kiểm chứng** đã bắt được rò rỉ dữ liệu, lập luận vòng tròn, đặc tính chẵn của phash, một con số độ trễ bị nhiễm, một giả thuyết bị dữ liệu bác bỏ, và một bộ đo đi tắt qua đường mã của chính sản phẩm nó đang đo — rồi ghi lại tất cả thay vì che đi.
