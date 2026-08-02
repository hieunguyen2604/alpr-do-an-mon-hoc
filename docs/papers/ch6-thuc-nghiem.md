# CHƯƠNG 6. THỰC NGHIỆM VÀ ĐÁNH GIÁ

Chương 5 đã trình bày hệ thống *đã được xây dựng* như thế nào. Chương này trả lời câu hỏi kế tiếp và cũng là câu hỏi khó nhất: hệ thống đó **hoạt động tốt đến mức nào**, và **những con số đó có đáng tin không**.

Hai vế của câu hỏi có trọng số ngang nhau. Một chương thực nghiệm chỉ liệt kê các chỉ số cao mà không nói rõ chúng được đo trên tập dữ liệu nào, bằng phần cứng nào, và với những nhiễu loạn phương pháp luận nào, thì không phải là bằng chứng — nó là quảng cáo. Vì vậy chương này được tổ chức sao cho **mỗi con số đều đi kèm ngữ cảnh đo của nó**, và các mục có giá trị phương pháp luận cao nhất (kiểm chứng rò rỉ dữ liệu ở 6.3.3, đóng góp định lượng của khối hậu xử lý ở 6.5.2, các mối đe doạ đến tính hợp lệ ở 6.9.3) được dành dung lượng tương xứng với tầm quan trọng của chúng, chứ không bị nén thành một dòng chú thích.

---

## 6.1. Mục tiêu và phương pháp đánh giá

### 6.1.1. Các câu hỏi nghiên cứu mà chương này trả lời

Chương thực nghiệm không tồn tại để "chạy thử cho biết". Nó tồn tại để trả lời một tập câu hỏi đã được đặt ra từ Chương 1 và được cụ thể hoá thành chỉ tiêu định lượng trong `docs/00-requirements/non-functional-requirements.md`. Sáu câu hỏi dưới đây là toàn bộ nội dung mà chương phải chứng minh hoặc bác bỏ:

| Mã | Câu hỏi nghiên cứu | Mục trả lời | Chỉ tiêu đối chiếu |
|:---:|---|:---:|---|
| **RQ1** | Bộ phát hiện YOLO11n huấn luyện trên bộ dữ liệu tự xây dựng có định vị được biển số Việt Nam với độ chính xác đạt chỉ tiêu không? | 5.5 | NFR-A1, A2, A3 |
| **RQ2** | Độ chính xác nhận dạng có **chênh lệch có ý nghĩa** giữa biển một dòng và biển hai dòng không, và chênh bao nhiêu? | 6.4.3, 6.5.3 | NFR-A8 |
| **RQ3** | **Khối hậu xử lý theo luật đóng góp bao nhiêu điểm phần trăm** vào độ chính xác chuỗi biển đầy đủ? | 6.5.2 | NFR-A5 ↔ A6 |
| **RQ4** | Hệ thống có đạt chỉ tiêu độ trễ đầu-cuối trên phần cứng CPU-only không? Nếu không, **nút thắt nằm ở đâu** và có tối ưu được không? | 5.7 | NFR-P1…P7 |
| **RQ5** | Bảng luật sửa lỗi ký tự hiện hành — vốn được suy ra từ **hình dạng chữ** chứ không từ đo đạc — có khớp với các cặp ký tự thực sự bị nhầm không? | 6.5.4 | `VNPLATE` §9.8 |
| **RQ6** | Các số liệu của chương này chịu những **mối đe doạ nào đến tính hợp lệ**, và mức độ nghiêm trọng ra sao? | 6.9.3 | — |

RQ3 và RQ5 là hai câu hỏi mang **đóng góp học thuật riêng** của đồ án. RQ3 lượng hoá một khối chức năng mà phần lớn công trình ALPR chỉ mô tả định tính ("có thêm bước hậu xử lý regex"); RQ5 thay một bảng tri thức suy đoán bằng một bảng tri thức đo được. RQ6 không phải câu hỏi bổ sung cho đủ — nó quyết định giá trị của năm câu còn lại.

### 6.1.2. Hai nguyên tắc trình bày bắt buộc

Toàn chương tuân thủ nghiêm ngặt hai nguyên tắc sau. Chúng được phát biểu tường minh ở đây để người đọc có thể kiểm tra chương này có tự vi phạm quy tắc của chính nó hay không.

**Nguyên tắc 1 — Mọi số liệu hiệu năng phải công bố kèm cấu hình phần cứng.** Một con số "độ trễ 5.857 ms" không mang thông tin nếu không biết nó được đo trên CPU nào, có GPU hay không, ở độ phân giải đầu vào nào và với bao nhiêu biển số trên ảnh. Đồ án này chạy suy luận **hoàn toàn trên CPU**, nên mọi so sánh với các con số FPS trong tài liệu — vốn hầu hết đo trên GPU — đều là so sánh không hợp lệ nếu không ghi rõ điều đó. Bảng cấu hình phần cứng ở mục 6.2.1 vì vậy không phải phần dạo đầu mang tính thủ tục; nó là **điều kiện diễn giải** cho mọi bảng hiệu năng ở mục 6.6.

**Nguyên tắc 2 — Mọi số liệu độ chính xác phải công bố kèm tên tập dữ liệu và số mẫu.** Độ chính xác không phải thuộc tính của mô hình; nó là thuộc tính của **cặp (mô hình, tập đánh giá)**. Mỗi bảng độ chính xác trong chương này bắt buộc có cột hoặc chú thích ghi rõ: tên split, số ảnh, số đối tượng (hoặc số biển có nhãn chuỗi). Hệ quả trực tiếp: các chỉ số OCR (NFR-A4…A7) chỉ đo được trên **tập con có nhãn chuỗi ký tự**, vốn nhỏ hơn nhiều so với tập test phát hiện — và mẫu số đó phải hiện diện trong bảng, không được giấu.

Nguyên tắc 2 kéo theo một quy tắc trích dẫn:

> **Cảnh báo trích dẫn.** Cặp số **94,3%** (biển một dòng) ↔ **45,7%** (biển hai dòng), chênh **48,6 điểm phần trăm**, được đo trên bộ dữ liệu **RodoSol-ALPR của Brazil** [7]<!-- laroca_2022_crossdataset -->. Đây **không phải** số liệu Việt Nam. Trong toàn chương, mỗi lần cặp số này được dẫn, tên bộ dữ liệu và quốc gia phải xuất hiện **ngay trong câu**. Nó chỉ được dùng như một *analogue định lượng* về mức độ khó tương đối của biển hai dòng, không bao giờ như một mốc chuẩn mà hệ thống này phải vượt qua.

### 6.1.3. Giao thức đo

Sơ đồ dưới mô tả trình tự đo và ràng buộc phụ thuộc giữa các bước. Điểm cần chú ý: **không bước đo nào được phép chạy trước khi trọng số chính thức được đóng băng**, và **tập test không được chạm vào trong suốt quá trình huấn luyện và chọn epoch** — việc chọn epoch tốt nhất chỉ dựa vào tập validation.

![](figures/fig-ch6-01.png)

*Hình 6.1. Giao thức đo và ràng buộc phụ thuộc giữa các bước đánh giá.*

Ba quy ước đo được áp dụng thống nhất:

1. **Kích thước lô bằng 1 khi đo độ trễ.** Hệ thống phục vụ theo yêu cầu đơn lẻ (một ảnh tải lên → một phản hồi), nên đo theo lô sẽ cho con số thông lượng đẹp hơn nhưng không phản ánh trải nghiệm thật. Riêng lúc tính mAP thì dùng lô lớn hơn vì mAP không phụ thuộc kích thước lô.
2. **Bỏ qua các lượt khởi động nóng.** Ba lần suy luận đầu tiên bị loại khỏi thống kê để tránh chi phí cấp phát bộ nhớ và nạp nhân tính toán lần đầu làm lệch phân vị.
3. **Báo cáo phân vị, không báo cáo trung bình.** Với độ trễ, trung bình che giấu đuôi phân bố — vốn chính là thứ người dùng cảm nhận. Chỉ tiêu NFR-P1 được phát biểu ở **p95**, nên p50/p95/p99 được báo cáo đầy đủ.

---

## 6.2. Môi trường thực nghiệm

### 6.2.1. Cấu hình phần cứng và hệ thống

Toàn bộ số liệu trong chương này được đo trên **một máy trạm cá nhân duy nhất**. Cấu hình đã được khảo sát và ghi nhận chính thức trong `docs/00-requirements/environment.md`.

<!-- {{T6.2a}} cau hinh phan cung va he thong — DA CO SO, khong can dien -->

**Bảng 6.1.** Cấu hình phần cứng và hệ thống của máy thực nghiệm

| Hạng mục | Cấu hình thực tế |
|---|---|
| Hệ điều hành | Windows 11 Pro, phiên bản 10.0.26200 |
| CPU | Intel Raptor Lake (CPU Family 6, Model 183) |
| Số nhân | **14 nhân vật lý / 20 nhân logic** |
| GPU dùng cho suy luận | **Không có GPU CUDA** — mọi suy luận chạy trên CPU |
| Thiết bị huấn luyện | `device=cpu` |
| Python | 3.13.12 |
| Chế độ đo | Kích thước lô = 1, bỏ 3 lượt khởi động nóng đầu tiên |

Bảng này phải được coi là **tiền tố ngầm định của mọi con số hiệu năng trong mục 6.6**. Khi chương báo cáo "độ trễ p95 là X ms", phát biểu đầy đủ là "độ trễ p95 là X ms trên Intel Raptor Lake 14 nhân, Windows 11, CPU-only, lô đơn".

### 6.2.2. Phiên bản thư viện

Kết quả học sâu nhạy cảm với phiên bản thư viện ở mức có thể thay đổi số ở chữ số thập phân thứ hai. Bảng dưới được điền bằng cách trích trực tiếp từ `pip freeze` của từng môi trường ảo tại thời điểm đo, không chép lại từ tệp `requirements.txt` (tệp yêu cầu ghi *ràng buộc*, không ghi *phiên bản đã cài*).

<!-- {{T6.2b}} phien ban thu vien tai thoi diem do — dien tu pip freeze -->

**Bảng 6.2.** Phiên bản thư viện tại thời điểm đo

| Gói | Vai trò | Phiên bản đo được (`backend/.venv`) |
|---|---|:---:|
| `ultralytics` | Huấn luyện và suy luận YOLO11 | 8.4.101 |
| `torch` | Backend tensor cho Ultralytics | 2.13.0+cpu |
| `torchvision` | Biến đổi ảnh, NMS | 0.28.0+cpu |
| `paddleocr` | Nhận dạng ký tự PP-OCRv5 mobile | 3.7.0 |
| `paddlepaddle` | Backend tensor cho PaddleOCR | 3.3.1 |
| `onnxruntime` | Backend suy luận thay thế (mục 6.6.3) | 1.27.0 |
| `openvino` | Backend suy luận thay thế (mục 6.6.3) | 2026.2.1 |
| `opencv-python` | Giải mã và tiền xử lý ảnh | 4.10.0.84 |
| `numpy` | Hạ tầng số học | 2.4.5 |
| `fastapi` | Tầng API | 0.139.2 |
| `uvicorn` | Máy chủ ASGI | 0.51.0 |
| `sqlalchemy` | ORM | 2.0.51 |
| `imagehash` | Băm tri giác cho kiểm chứng rò rỉ (6.3.3) | 5.6.2 |
| `pytest` | Khung kiểm thử | 9.1.1 |

> Số ở cột trên trích trực tiếp từ `pip freeze` của môi trường ảo `backend/.venv` tại đúng thời điểm chạy phép đo cuối cùng (2026-07-20). Đồ án dùng **một môi trường ảo hợp nhất** chứa cả ngăn xếp suy luận (`ultralytics`, `torch`, `paddleocr`, `paddlepaddle`) lẫn ngăn xếp API (`fastapi`, `uvicorn`, `sqlalchemy`), thay vì hai môi trường tách rời như phác thảo ban đầu — nên bảng này chỉ còn một cột phiên bản thay vì hai.

### 6.2.3. Vì sao ràng buộc CPU-only là ràng buộc thiết kế, không phải hạn chế tạm thời

Lập luận đầy đủ vì sao "không có GPU" được coi là **ràng buộc thiết kế** chứ không phải hạn chế tạm thời đã trình bày ở **mục 5.1.2**; ở đây chỉ nêu hệ quả với việc **diễn giải số đo** của chương này.

**Hệ quả với cách đọc mọi con số hiệu năng.** Chỉ tiêu NFR-P1 được phát biểu *kèm* ràng buộc CPU, nên khi mục 6.6 kết luận NFR-P1 **đạt ngưỡng tối thiểu nhưng không đạt mục tiêu** (p95 = 1.143,10 ms; sàn 1.500 ms, mục tiêu 800 ms), đó là kết luận về hệ thống trong đúng bối cảnh vận hành thật của nó — không phải một con số chờ nâng cấp phần cứng mới có ý nghĩa. Ngược lại, cấu hình mô hình được đánh giá cũng là cấu hình *do ràng buộc phần cứng quyết định* — **YOLO11n** (2.590.035 tham số) [16]<!-- jocher_2024_yolo11 --> và **PP-OCRv5 mobile** [118]<!-- paddlepaddle_2026_ppocrv5docs --> — nên mọi kết quả độ chính xác phải đọc kèm lựa chọn đó, không tách rời.

**Hệ quả với quy mô thực nghiệm.** Với khoảng 35,6 phút mỗi epoch trên CPU, một lượt huấn luyện 20 epoch mất khoảng 12 giờ liên tục. Điều này khiến **tìm kiếm siêu tham số trở nên bất khả thi trong khuôn khổ đồ án**, và giải thích vì sao chương này báo cáo *một* cấu hình huấn luyện chứ không phải một khảo sát siêu tham số. Đó là giới hạn thật của công trình và được ghi nhận trong mục 6.9.3, không được che giấu bằng cách trình bày cấu hình duy nhất ấy như thể nó là kết quả của một quá trình tối ưu.

---

## 6.3. Bộ dữ liệu thực nghiệm

### 6.3.1. Ba phiên bản bộ dữ liệu và lý do tồn tại của từng phiên bản

Bộ dữ liệu của đồ án trải qua ba phiên bản. Mỗi phiên bản ra đời để sửa một khiếm khuyết cụ thể của phiên bản trước, và việc trình bày đủ cả ba — thay vì chỉ trình bày phiên bản cuối — chính là phần ghi nhận quá trình làm việc thật.

> **Lưu ý về cách đặt tên.** Thư mục `yolo_v2/` và `yolo_v3/` chỉ ra **phiên bản của bộ dữ liệu**, hoàn toàn **không** liên quan đến kiến trúc YOLOv2 hay YOLOv3. Mô hình dùng trong toàn đồ án là **YOLO11n**.

<!-- {{T6.3a}} so sanh ba phien ban bo du lieu — DA CO SO, khong can dien -->

**Bảng 6.3.** So sánh ba phiên bản bộ dữ liệu

| Thuộc tính | v1 (`processed/yolo/`) | v2 (`processed/yolo_v2/`) | **v3 (`processed/yolo_v3/`)** |
|---|---:|---:|---:|
| Tổng số ảnh | 4.578 | 15.133 | **15.133** |
| Số bộ dữ liệu vào bước hợp nhất detection | 1 | 7 | **7** |
| Số nguồn nguyên tố còn lại sau khử trùng lặp chéo bộ | 1 | 6 | **6** |
| Ngưỡng Hamming dùng để gộp trùng lặp | 5 | 5 | **10** |
| Tình trạng rò rỉ train↔test (đo ở ngưỡng phash 10) | **Có — 619 cặp** | **Có — 2.699 cặp** | (xem mục 6.3.3) |
| Số ảnh tập train | — | — | **10.592** |
| Số ảnh tập val | — | — | **3.027** |
| Số ảnh tập test | — | — | **1.514** |
| Dùng cho | Baseline `baseline-416-v1.pt` | Bị loại bỏ | **Mô hình chính thức `best.pt`** |

Ba nhận xét về bảng trên.

**v1 quá nhỏ và chỉ một nguồn.** 4.578 ảnh từ một nguồn duy nhất khiến mô hình có nguy cơ học đặc trưng của nguồn thay vì đặc trưng của biển số. Đây là động cơ trực tiếp để tải thêm **tám bộ dữ liệu** nữa (tổng cộng 9 bộ tải về), trong đó **sáu bộ** đi vào bước hợp nhất detection cùng bộ gốc, hai bộ nhãn mức ký tự được tách riêng phục vụ đánh giá OCR.

**v2 sửa được quy mô nhưng không sửa được rò rỉ.** Việc mở rộng lên 15.133 ảnh — hợp nhất từ 7 bộ dữ liệu, còn 6 nguồn nguyên tố sau khử trùng lặp chéo bộ — làm *tăng* số cặp gần trùng xuyên split lên 2.699, vì các nguồn khác nhau chứa những ảnh có nguồn gốc chung.

**v3 giữ nguyên corpus, chỉ thay ngưỡng gộp trùng lặp và cách chia.** Đây là điểm cần nhấn mạnh: v3 **không** thêm dữ liệu mới so với v2 (cùng 15.133 ảnh). Khác biệt duy nhất là ngưỡng khử trùng lặp được nâng từ 5 lên 10 và split được sinh lại. Cách cô lập biến này là có chủ ý — nó cho phép quy kết mọi thay đổi kết quả cho *chất lượng split*, không cho *lượng dữ liệu*.

### 6.3.2. Khử trùng lặp: hai tỉ lệ, hai mẫu số khác nhau

Quá trình khử trùng lặp diễn ra ở hai giai đoạn khác nhau, cho ra hai tỉ lệ khác nhau. Trộn lẫn hai con số này là lỗi thường gặp, nên chúng được trình bày kèm **mẫu số tường minh**:

| Giai đoạn | Phạm vi áp dụng | Số ảnh bị loại / tổng | Tỉ lệ |
|---|---|---:|---:|
| Trước khi hợp nhất | Toàn bộ ảnh của 7 bộ vào hợp nhất detection | **11.978 / 27.111** | **44,2%** |
| Sau khi hợp nhất, ngưỡng 10 | Corpus đã hợp nhất | **7.227 / 15.133** | **47,8%** |

Hai tỉ lệ không cộng dồn và không thay thế nhau: con số thứ nhất mô tả mức trùng lặp *giữa và trong* 7 bộ đi vào hợp nhất detection; con số thứ hai mô tả mức trùng lặp còn lại *trong corpus đã hợp nhất* khi siết ngưỡng tri giác.

*Về mẫu số 27.111:* đây là tổng ảnh của **7 bộ vào bước hợp nhất detection** (4.578 + 8.254 + 236 + 840 + 8.357 + 3.841 + 1.005), **không phải** toàn bộ 9 bộ đã tải về. Hai bộ còn lại — `roboflow_ocr_plate` (3.819 ảnh, 30 lớp ký tự) và `roboflow_ocr_conversion` (200 ảnh, 22 lớp ký tự) — là bộ **nhãn mức ký tự**, được tách riêng có chủ đích để phục vụ đánh giá tầng OCR chứ không phải tầng phát hiện. Nguồn: `datasets/reports/merge_report.json`, trường `images_per_dataset` có đúng 7 khoá. Mọi lần trích dẫn một trong hai tỉ lệ này ở phần khác của quyển đồ án đều phải kèm mẫu số tương ứng.

### 6.3.3. Kiểm chứng rò rỉ dữ liệu — và vì sao con số "0 cặp rò rỉ" không chứng minh được điều gì

Đây là mục có giá trị phương pháp luận cao nhất của cả chương. Nó không báo cáo một kết quả tốt; nó báo cáo một **giới hạn nhận thức** mà đồ án đã phát hiện ra ở chính quy trình của mình.

**Bối cảnh.** Rò rỉ dữ liệu (*data leakage*) xảy ra khi tập test chứa ảnh gần trùng với ảnh trong tập train. Mô hình khi đó không *tổng quát hoá* mà *ghi nhớ*, và mọi chỉ số đo trên tập test bị thổi phồng. Trong các bộ dữ liệu ALPR ghép từ nhiều nguồn công khai, đây là rủi ro hệ thống chứ không phải rủi ro hiếm gặp: cùng một ảnh có thể xuất hiện ở nhiều bộ dữ liệu khác nhau dưới tên tệp khác nhau, và vấn đề tổng quát hoá xuyên tập dữ liệu đã được ghi nhận rõ trong tài liệu [7]<!-- laroca_2022_crossdataset -->.

**Công cụ đo.** Đồ án dùng **băm tri giác** (`imagehash.phash`, 64 bit) và đếm số cặp ảnh xuyên split có khoảng cách Hamming nhỏ hơn hoặc bằng một ngưỡng cho trước. Ngưỡng càng lớn thì tiêu chuẩn "gần trùng" càng lỏng và số cặp phát hiện được càng nhiều.

**Lập luận vòng tròn — vấn đề trung tâm của mục này.** Bộ dữ liệu v3 được xây dựng bằng cách **khử trùng lặp ở ngưỡng Hamming 10**. Nếu sau đó ta *kiểm chứng rò rỉ cũng ở ngưỡng 10*, thì kết quả "0 cặp rò rỉ" là **tất yếu về mặt logic**, không phải phát hiện thực nghiệm. Nói cách khác:

> Đo rò rỉ ở đúng ngưỡng đã dùng để gộp trùng lặp là **kiểm tra lại chính định nghĩa của mình**, chứ không phải kiểm chứng độc lập. Kết quả bằng 0 ở đây chứng minh rằng bước khử trùng lặp *đã chạy đúng như đặc tả*, và **không chứng minh gì thêm** về mức độ "sạch" của tập test.

Đây là lý do bảng dưới đo ở **nhiều ngưỡng**, trong đó có các ngưỡng **cao hơn** ngưỡng gộp. Chỉ những ô ở ngưỡng > 10 mới mang thông tin mới; các ô ở ngưỡng ≤ 10 được giữ lại để người đọc tự kiểm chứng lập luận vòng tròn nói trên.

<!-- {{T6.3b}} so cap gan trung xuyen split theo nguong Hamming -->

**Bảng 6.4.** Số cặp ảnh gần trùng xuyên split theo ngưỡng Hamming

| Ngưỡng Hamming | v1 — số cặp train↔test | v2 — số cặp train↔test | **v3 — số cặp train↔test** | Ô này có mang thông tin mới không? |
|:---:|---:|---:|---:|---|
| 0 (trùng khít bit-hash) | — | — | **0** | Có |
| 5 | — | — | **0** | Không với v1, v2 (bằng ngưỡng gộp của chúng) |
| **10** | **619** | **2.699** | **0** | **Không với v3** — bằng ngưỡng gộp |
| 12 | — | — | **791** | **Có** |
| 15 | — | — | **3.529** | **Có** |
| 20 | — | — | **137.506** | Có, nhưng ngưỡng đã lỏng tới mức nhiều cặp là dương tính giả |

> Mẫu số: 10.592 ảnh train × 1.514 ảnh test = 16.036.288 cặp đã so sánh (`imagehash.phash` 64 bit). Khoảng cách Hamming **nhỏ nhất quan sát được là 12** — chính giá trị chẵn kế tiếp sau ngưỡng gộp 10, một tất yếu toán học (mọi mã băm đều có đúng 32 bit 1 nên khoảng cách luôn chẵn), **không phải dấu vết rò rỉ bị cắt cụt tại ngưỡng** — chứng minh và số liệu kiểm chứng (15.133/15.133 mã băm có popcount chẵn; 4.498.500/4.498.500 cặp lấy mẫu có khoảng cách chẵn) ở [`docs/reports/02-dataset-report.md` mục 6bis.1](../reports/02-dataset-report.md). Cột v1/v2 chỉ có số ở ngưỡng 10 vì đó là con số đã đo trước đó trên hai bộ ấy; các ô trống còn lại **không được suy ra**.

Cột cuối cùng của bảng không phải chú thích trang trí; nó là phần **diễn giải bắt buộc** đi kèm bảng. Không có nó, người đọc sẽ đọc ô "v3, ngưỡng 10" như một bằng chứng, trong khi thực chất đó là một hệ quả định nghĩa: v3 được khử trùng lặp ở đúng ngưỡng 10, nên đo rò rỉ lại ở ngưỡng 10 tất yếu cho 0 cặp. Chỉ các ngưỡng **12 (791 cặp), 15 (3.529 cặp), 20 (137.506 cặp)** mới mang thông tin mới; và ngay cả các con số này cũng **không** chứng minh tập test sạch, vì `phash` không bắt được rò rỉ ở mức ngữ nghĩa (cùng một biển số chụp ở góc khác nhau). Con số 137.506 ở ngưỡng 20 là **cận trên bi quan** — ở ngưỡng lỏng đó phần lớn cặp chỉ giống nhau về bố cục sáng-tối tổng thể chứ không cùng biển số.

**Ba giới hạn còn lại của phương pháp phash.** Ngay cả khi các ngưỡng cao cho kết quả thấp, vẫn **không** kết luận được rằng tập test "sạch":

1. **phash chỉ bắt được tương đồng ở mức bố cục sáng-tối tổng thể.** Hai ảnh chụp *cùng một chiếc xe* ở hai góc khác nhau, hoặc hai khung hình cách nhau vài giây trong cùng một video, có thể có khoảng cách Hamming lớn nhưng vẫn mang **cùng một biển số** — tức vẫn là rò rỉ ở mức ngữ nghĩa. Loại rò rỉ này **không khử được bằng bất kỳ ngưỡng phash nào**.
2. **Không có định danh phương tiện hay định danh chuỗi biển số cho toàn corpus.** Cách khử rò rỉ triệt để là chia split theo **nhóm biển số** (mọi ảnh của cùng một biển đều nằm cùng một phía). Đồ án không làm được điều này vì phần lớn corpus **không có nhãn chuỗi ký tự** — chính hạn chế đã dẫn tới mẫu số nhỏ của các bảng OCR ở mục 6.5.
3. **Ngưỡng cao sinh dương tính giả.** Ở ngưỡng 20, nhiều cặp bị đánh dấu "gần trùng" thực ra chỉ giống nhau về bố cục chung (xe sẫm màu trên nền sáng). Do đó con số ở ngưỡng 20 là **cận trên bi quan**, không phải ước lượng điểm.

**Kết luận trung thực của mục 6.3.3.** Có thể khẳng định: *bước khử trùng lặp ở ngưỡng 10 đã chạy đúng đặc tả, và số cặp gần trùng ở các ngưỡng lỏng hơn ngưỡng gộp nằm ở mức [điền từ bảng T6.3b]*. **Không** thể khẳng định: *tập test hoàn toàn độc lập với tập train*. Rò rỉ tồn dư ở mức ngữ nghĩa là **không đo được bằng công cụ hiện có**, và vì vậy nó được liệt kê như mối đe doạ đầu tiên đến tính hợp lệ ở mục 6.9.3. Mọi chỉ số ở mục 6.4 phải được đọc với ghi chú này kèm theo.

### 6.3.4. Phân bố nguồn dữ liệu giữa các split

Nếu một nguồn dữ liệu tập trung bất cân xứng vào một split, chỉ số trên split đó sẽ phản ánh đặc tính của nguồn chứ không phản ánh năng lực tổng quát của mô hình. Bảng dưới kiểm tra điều đó.

<!-- {{T6.3c}} phan bo nguon du lieu giua cac split cua v3 -->

**Bảng 6.5.** Phân bố nguồn dữ liệu giữa các split của phiên bản v3

| Tổ hợp xuất xứ | Tổng số ảnh | Train (số / %) | Val (số / %) | Test (số / %) | Ghi chú |
|---|---:|---:|---:|---:|---|
| `hf_vn_plates_segment\|roboflow_cuong_ta\|roboflow_eric_nguyen\|roboflow_school_fuhih\|roboflow_traffic_camera` | 4.411 | 4.411 / 100,0% | 0 / 0,0% | 0 / 0,0% | — |
| `roboflow_school_fuhih` | 3.599 | 2.275 / 63,2% | 938 / 26,1% | 386 / 10,7% | — |
| `hf_vn_plates_segment` | 2.820 | 1.933 / 68,5% | 574 / 20,3% | 313 / 11,1% | — |
| `roboflow_traffic_camera` | 2.582 | 1.368 / 53,0% | 689 / 26,7% | 525 / 20,3% | **lệch > 10 điểm %** so với tỉ lệ test tổng thể |
| `hf_vn_plates_segment\|roboflow_school_fuhih` | 634 | 78 / 12,3% | 527 / 83,1% | 29 / 4,6% | — |
| `roboflow_eric_nguyen` | 351 | 228 / 65,0% | 77 / 21,9% | 46 / 13,1% | — |
| `roboflow_school_fuhih\|roboflow_traffic_camera` | 250 | 4 / 1,6% | 72 / 28,8% | 174 / 69,6% | **lệch > 10 điểm %** so với tỉ lệ test tổng thể |
| `roboflow_demo_tracking` | 210 | 139 / 66,2% | 51 / 24,3% | 20 / 9,5% | — |
| `roboflow_cuong_ta` | 136 | 88 / 64,7% | 33 / 24,3% | 15 / 11,0% | — |
| `roboflow_demo_tracking\|roboflow_traffic_camera` | 57 | 32 / 56,1% | 22 / 38,6% | 3 / 5,3% | — |
| `hf_vn_plates_segment\|roboflow_traffic_camera` | 50 | 29 / 58,0% | 18 / 36,0% | 3 / 6,0% | — |
| `hf_vn_plates_segment\|roboflow_school_fuhih\|roboflow_traffic_camera` | 20 | 0 / 0,0% | 20 / 100,0% | 0 / 0,0% | — |
| `hf_vn_plates_segment\|roboflow_demo_tracking\|roboflow_traffic_camera` | 4 | 0 / 0,0% | 4 / 100,0% | 0 / 0,0% | — |
| `roboflow_cuong_ta\|roboflow_school_fuhih` | 4 | 2 / 50,0% | 2 / 50,0% | 0 / 0,0% | — |
| `hf_vn_plates_segment\|roboflow_eric_nguyen\|roboflow_school_fuhih` | 3 | 3 / 100,0% | 0 / 0,0% | 0 / 0,0% | — |
| `roboflow_demo_tracking\|roboflow_school_fuhih` | 2 | 2 / 100,0% | 0 / 0,0% | 0 / 0,0% | — |
| **Tổng** | **15.133** | **10.592 / 70,0%** | **3.027 / 20,0%** | **1.514 / 10,0%** | |

**Bảng gồm 16 dòng — mỗi dòng là một *tổ hợp xuất xứ*, không phải một nguồn.** Sau khử trùng lặp, một ảnh giữ lại có thể đến từ nhiều nguồn cùng lúc, và manifest ghi cả tập xuất xứ ngăn cách bằng `|`; 16 tổ hợp này được dựng từ đúng **6 nguồn nguyên tố** (`roboflow_school_fuhih`, `hf_vn_plates_segment`, `roboflow_traffic_camera`, `roboflow_eric_nguyen`, `roboflow_cuong_ta`, `roboflow_demo_tracking`). Không được cộng dồn số đếm của từng nguồn nguyên tố: tổng đó (33.828) vượt xa 15.133 vì ảnh đa nguồn bị đếm nhiều lần, nên **không được dùng làm mẫu số**. Tỉ lệ train/val/test của mỗi dòng tính theo mẫu số là tổng số ảnh của **chính dòng đó**. Cũng cần phân biệt ba con số nguồn ở ba ngữ cảnh khác nhau: **9 bộ đã tải về** (khâu thu thập), **7 bộ vào hợp nhất detection** (2 bộ nhãn ký tự tách riêng cho đánh giá OCR), và **6 nguồn nguyên tố** trong tập v3. Bộ thứ 7 — `roboflow_tran_ngoc_xuan_tin` — bị khử trùng lặp chéo bộ loại **100%** nên không xuất hiện trong bất kỳ tổ hợp nào; chi tiết ở ghi chú cuối mục.

**Hai tổ hợp lệch quá 10 điểm phần trăm ở tập test cần thảo luận.** Tổ hợp thuần `roboflow_traffic_camera` (2.582 ảnh) có **20,3%** rơi vào tập test — gấp đôi tỉ lệ tổng thể 10,0%; và tổ hợp `roboflow_school_fuhih|roboflow_traffic_camera` (250 ảnh) có tới **69,6%** ở tập test. Nghĩa là **tập test nghiêng về ảnh có nguồn gốc camera giao thông** — vốn thường là ảnh hiện trường góc rộng, biển số nhỏ. Điều này hệ quả trực tiếp với mục 6.4.4: dải "rất nhỏ" của tập test được nuôi chủ yếu bởi chính nguồn này, nên khi đọc mAP theo dải kích thước phải nhớ rằng đối tượng nhỏ trong tập test không phân bố ngẫu nhiên mà tập trung ở một nguồn. Đây không phải lỗi chia split cố ý — split được sinh ngẫu nhiên phân tầng — mà là hệ quả của việc các tổ hợp nhỏ khó chia đều; nó được ghi nhận như một yếu tố đọc kèm, không phải một khiếm khuyết vô hiệu hoá kết quả.

> **Cách đếm — bắt buộc đọc trước khi điền bảng.** Cột `source_dataset` trong `datasets/processed/yolo_v3/split_manifest.csv` chứa một **tập xuất xứ** ngăn cách bằng `|`: sau khử trùng lặp, một ảnh giữ lại có thể đến từ nhiều nguồn cùng lúc (15.133 dòng manifest trải trên 16 tổ hợp xuất xứ phân biệt). Vì vậy phải đếm theo **tập ảnh**, không đếm theo dòng đã tách rời — cộng dồn số đếm của 6 nguồn nguyên tố cho ra **33.828**, vượt xa 15.133 vì ảnh đa nguồn bị đếm nhiều lần. **Không được dùng 33.828 làm mẫu số.** Tỉ lệ train/val/test của mỗi dòng phải tính theo mẫu số là tổng số ảnh của **chính dòng đó**.

**Tiêu chí đọc bảng:** nếu tỉ lệ của một nguồn trong tập test lệch quá 10 điểm phần trăm so với tỉ lệ tổng thể (10,0%), phải nêu tên nguồn đó và thảo luận ảnh hưởng. Trường hợp xấu nhất — một nguồn chiếm phần lớn tập test — sẽ biến "độ chính xác trên tập test" thành "độ chính xác trên nguồn đó", và kết luận của mục 6.4 phải được phát biểu lại tương ứng.

**Một bộ dữ liệu dư thừa hoàn toàn.** Lý do bảng T6.3c chỉ dựng trên **6 nguồn nguyên tố** (thay vì 7 bộ vào hợp nhất) đáng được ghi nhận riêng, vì nó là một kết quả đo chứ không phải một chi tiết kế toán. Bộ `roboflow_tran_ngoc_xuan_tin` đi vào bước hợp nhất với **1.005 ảnh** và ra khỏi bước khử trùng lặp chéo bộ với **0 ảnh — tỉ lệ loại 100,0% (1.005/1.005)**. Đếm trực tiếp trên `datasets/reports/v2/duplicate_pairs.csv` cho thấy **cả 1.005 ảnh đều dính vào ít nhất một cặp gần trùng**: 1.577 cặp với `roboflow_school_fuhih`, 1.569 cặp với `roboflow_cuong_ta`, 8 cặp với `hf_vn_plates_segment`, và 35 cặp trùng nội bộ. Toàn bộ nội dung của bộ này đã có sẵn ở nơi khác. Kiểm chứng độc lập: cột `source_dataset` của `split_manifest.csv` không chứa tên bộ này dù chỉ một lần.

Ý nghĩa với chương này gồm hai điểm. Thứ nhất, đây là **bằng chứng định lượng** cho cảnh báo nêu ở Phase 1 rằng các bộ Roboflow tái sử dụng ảnh của nhau rất nặng — mức nghiêm trọng còn vượt dự kiến, vì ngoài cặp `cuong_ta` ↔ `school_fuhih` còn có hẳn một bộ là **tập con thực sự** của hai bộ đó. Thứ hai, nó là lý do **không được cộng dồn `expected_images` của các bộ Roboflow để suy ra quy mô thật**: phép cộng đó giả định các bộ độc lập, trong khi thực tế một bộ 1.005 ảnh có thể đóng góp đúng 0. Quy mô thật chỉ xác định được *sau* khử trùng lặp chéo bộ. Chi tiết đầy đủ ở mục 6.3.1 của [`docs/reports/02-dataset-report.md`](../reports/02-dataset-report.md).

---

## 6.4. Đánh giá bộ phát hiện biển số

Toàn bộ mục 6.4 đo trên **tập test của bộ dữ liệu v3: 1.514 ảnh**, tại `imgsz=640`, `device=cpu`. Tập test này chưa từng được dùng trong huấn luyện hay chọn epoch.

### 6.4.1. Chỉ số tổng thể

<!-- {{T6.4a}} ket qua detection tong the tren tap test v3 (1.514 anh) -->

**Bảng 6.6.** Kết quả phát hiện tổng thể trên tập test v3

| Chỉ số | Mã NFR | Ngưỡng tối thiểu | Mục tiêu | **Đo được** | Kết quả |
|---|:---:|---:|---:|---:|:---:|
| mAP@0.5 | NFR-A1 | 0,85 | 0,90 | **0,9829** | ✅ đạt |
| mAP@0.5:0.95 | NFR-A2 | 0,55 | 0,65 | **0,7834** | ✅ đạt |
| Precision | NFR-A3 | 0,88 | 0,92 | **0,9837** | ✅ đạt |
| Recall | NFR-A3 | 0,85 | 0,90 | **0,9714** | ✅ đạt |
| F1 (tại ngưỡng confidence đo) | — | — | — | **0,9775** | n/a |
| Ngưỡng confidence dùng khi đo | — | — | — | 0,25 | n/a |
| Số ảnh tập test | — | — | — | **1.514** | n/a |
| Số đối tượng nhãn thật (ground truth) | — | — | — | **1.611** | n/a |

Ký hiệu cột **Kết quả**: ✅ đạt mục tiêu · 🟡 chỉ đạt ngưỡng tối thiểu · ❌ không đạt · ⬜ chưa đo.

**Cả bốn chỉ tiêu bắt buộc của tầng phát hiện đều đạt mục tiêu.** mAP@0.5 = 0,9829 (mục tiêu 0,90), mAP@0.5:0.95 = 0,7834 (mục tiêu 0,65), Precision = 0,9837 (mục tiêu 0,92), Recall = 0,9714 (mục tiêu 0,90). Con số đo trên `ultralytics_val` tại ngưỡng confidence cố định 0,25; F1 = 0,9775 tại ngưỡng đó. Ngưỡng vận hành tối ưu theo F1 phải đọc từ Hình 6.4, không suy từ bảng này.

**Cách phải đọc bảng này.** Ba lưu ý bắt buộc kèm theo, bất kể con số cuối cùng là bao nhiêu:

1. **Bài toán chỉ có một lớp** (`plate`). mAP một lớp không so sánh trực tiếp được với mAP nhiều lớp trên COCO; giá trị cao ở đây là điều bình thường và **không phải bằng chứng về độ khó đã được vượt qua**.
2. **mAP@0.5 gần như bão hoà** không đồng nghĩa bài toán đã giải xong. Chỉ số quyết định là **mAP@0.5:0.95**, vì độ khớp box ảnh hưởng trực tiếp đến chất lượng vùng cắt đưa sang OCR — và OCR mới là nút thắt độ chính xác thật của hệ thống (mục 6.5).
3. **Chỉ số tổng thể che giấu phân bố.** Đó chính là lý do có hai mục tách nhỏ ngay sau đây (6.4.3 theo layout, 6.4.4 theo dải kích thước). Không được kết luận về năng lực hệ thống chỉ từ bảng T6.4a.

### 6.4.2. Đường cong PR và ma trận nhầm lẫn

*Hình 6.2.* Đường cong Precision–Recall trên tập test, vẽ tách theo layout (một dòng / hai dòng).
Đường dẫn hình: `docs/reports/figures/05-detection-pr-curve.png` *(chưa sinh)*

*Hình 6.3.* Ma trận nhầm lẫn nhận biết layout: hàng là quần thể nhãn thật (một dòng / hai dòng / nền), cột là dự đoán.
Đường dẫn hình: `docs/reports/figures/05-detection-confusion-matrix.png` *(chưa sinh)*

*Hình 6.4.* Đường cong F1 theo ngưỡng confidence — dùng để xác định ngưỡng vận hành.
Đường dẫn hình: `docs/reports/figures/05-detection-f1-curve.png` *(chưa sinh)*

Hình 6.4 có vai trò thực tiễn trực tiếp: **ngưỡng confidence dùng trong hệ thống chạy thật phải là ngưỡng tối ưu F1 đo được ở đây**, không phải giá trị mặc định 0,25 của Ultralytics. Nếu hai giá trị lệch nhau, cấu hình suy luận phải được cập nhật và việc cập nhật đó phải được ghi lại.

### 6.4.3. Tách theo biển một dòng và biển hai dòng (NFR-A8)

Biển hai dòng là thách thức kỹ thuật lớn nhất của bài toán biển số Việt Nam, vì tỉ lệ xe máy trong lưu lượng giao thông rất cao. NFR-A8 yêu cầu báo cáo **tách bạch** hai quần thể này thay vì gộp thành một con số.

Trong bảng dưới, layout được xác định theo nhãn lớp khi bộ dữ liệu có khai báo, và theo **ngưỡng tỉ lệ khung hình 2,5** khi không có — giá trị này nằm giữa tỉ lệ chuẩn của biển một dòng (4,727) và biển hai dòng (2,000 / 1,357) theo QCVN 08:2024/BCA.

<!-- {{T6.4b}} detection tach theo layout mot dong / hai dong (NFR-A8) -->

**Bảng 6.7.** Kết quả phát hiện tách theo biển một dòng và hai dòng (NFR-A8)

| Chỉ số | Biển **một dòng** | Biển **hai dòng** | Chênh lệch (điểm %) | Mẫu số |
|---|---:|---:|---:|---:|
| Số đối tượng nhãn thật | 286 | 1.325 | n/a | 1.611 |
| mAP@0.5 | 0,9884 | 0,9675 | 2,09 | |
| mAP@0.5:0.95 | 0,7526 | 0,7649 | −1,23 | |
| Precision | 0,9861 | 0,9735 | 1,26 | |
| Recall | 0,9895 | 0,9691 | 2,04 | |
| F1 | 0,9878 | 0,9713 | 1,65 | |

> **Nhãn layout là ước lượng, không phải nhãn thật.** Bộ dữ liệu không khai báo lớp layout, nên layout được suy từ ngưỡng tỉ lệ khung hình 2,5 cho phần lớn hộp giới hạn (100% số ô được suy bằng heuristic). Mọi kết luận về NFR-A8 ở tầng phát hiện phải nêu rõ điều này.

**Chênh lệch ở tầng phát hiện là rất nhỏ, đúng như dự đoán.** mAP@0.5 chênh **2,09 điểm phần trăm** giữa một dòng (0,9884) và hai dòng (0,9675); ở mAP@0.5:0.95 biển hai dòng thậm chí *nhỉnh hơn* 1,23 điểm — dao động trong phạm vi nhiễu chứ không phải một xu hướng. Con số này cùng bậc với mốc tham chiếu baseline (`baseline-416-v1.pt`, split v1, imgsz 416: một dòng 0,9856 so với hai dòng 0,9592, chênh 2,6 điểm — **số của baseline, không được chuyển thành số của `best.pt`**). Nó xác nhận điều đã lập luận từ đầu: **việc *định vị một hình chữ nhật* gần như không phụ thuộc vào việc bên trong có một dòng hay hai dòng ký tự.** Vì vậy **tuyệt đối không được** dùng con số nhỏ 2,09 điểm ở đây để kết luận "hệ thống xử lý tốt biển hai dòng" — chênh lệch thật của bài toán nằm ở tầng OCR và chỉ lộ ra ở bảng T6.5c, nơi khoảng cách nhảy vọt lên **25,45 điểm**.

### 6.4.4. Tách theo dải kích thước hộp giới hạn

Mục này tồn tại vì một lý do cụ thể và phải được nêu thẳng: **bộ dữ liệu không đạt tiêu chí chất lượng Q6**. Cụ thể, **10,91% số hộp giới hạn có diện tích dưới 0,5% diện tích ảnh**, trong khi ngưỡng cho phép của tiêu chí là 10%. Đối tượng nhỏ là chế độ thất bại đã được ghi nhận rộng rãi của các bộ phát hiện một giai đoạn [119]<!-- ultralytics_2026_modelevaluation -->, và bài toán biển số ở độ phân giải thấp đã trở thành một hướng nghiên cứu riêng [71]<!-- laroca_2026_icprlrlpr -->.

Báo cáo một con số mAP tổng trong tình huống này sẽ **giấu chế độ thất bại phía sau giá trị trung bình**. Bảng dưới là cách trả lời trung thực: nếu mô hình yếu ở dải nhỏ, bảng sẽ cho thấy điều đó.

<!-- {{T6.4c}} detection tach theo dai kich thuoc hop gioi han -->

**Bảng 6.8.** Kết quả phát hiện tách theo dải kích thước hộp giới hạn

| Dải kích thước (diện tích box / diện tích ảnh) | Số đối tượng | Tỉ lệ trong tập test | mAP@0.5 | mAP@0.5:0.95 | Recall |
|---|---:|---:|---:|---:|---:|
| **Rất nhỏ** — dưới 0,5% | 262 | 16,26% | 0,8553 | 0,5249 | 0,8740 |
| **Nhỏ** — 0,5% đến 1% | 124 | 7,70% | 0,9755 | 0,7055 | 0,9758 |
| **Trung bình** — 1% đến 5% | 900 | 55,87% | 0,9913 | 0,8005 | 0,9922 |
| **Lớn** — 5% đến 15% | 297 | 18,44% | 0,9966 | 0,8394 | 0,9966 |
| **Rất lớn** — trên 15% | 28 ⚠ | 1,74% | 1,0000 | 0,8562 | 1,0000 |
| **Toàn tập test** | **1.611** | 100% | 0,9711 | 0,7625 | 0,9727 |

> Dòng ⚠ (dải "rất lớn", 28 đối tượng < 30) **không có ý nghĩa thống kê** và không được đưa vào so sánh. Các dải được tính từ `(w×h)` của hộp nhãn thật chia cho diện tích ảnh gốc; số box không gán được dải: 0.

**Chế độ thất bại ở đối tượng nhỏ được xác nhận có thật.** Dải "rất nhỏ" (dưới 0,5% diện tích ảnh, 262 đối tượng) có mAP@0.5 = **0,8553** và mAP@0.5:0.95 = **0,5249** — thấp hơn rõ rệt so với toàn tập (0,9711 / 0,7625) và cách biệt rất lớn so với dải "trung bình" (0,9913 / 0,8005), vốn chiếm hơn nửa tập test. Recall dải này cũng chỉ 0,8740 so với 0,9922 ở dải trung bình, tức bộ phát hiện **bỏ sót nhiều biển nhỏ hơn hẳn**. Đây là xác nhận trực tiếp rằng tiêu chí chất lượng Q6 không đạt (10,91% số hộp dưới 0,5% diện tích, vượt ngưỡng 10%) đã gây hậu quả đo được, chứ không phải một cảnh báo lý thuyết. Kết hợp với nhận xét ở mục 6.3.4 — tập test nghiêng về nguồn `roboflow_traffic_camera` (ảnh camera giao thông, biển nhỏ) — có thể thấy dải "rất nhỏ" chiếm tới 16,26% tập test, cao hơn tỉ lệ 10,91% của toàn corpus, nghĩa là **tập test khó hơn trung bình ở đúng khía cạnh này**. Phương án khắc phục đã liệt kê: tăng `imgsz`, cắt ảnh theo ô (*tiling*), hoặc lọc bỏ đối tượng quá nhỏ khỏi tập huấn luyện. Điều đáng chú ý về mặt trình bày: dù dải nhỏ kéo mAP tổng xuống, chỉ số tổng thể vẫn đạt mục tiêu — nếu chỉ báo cáo một con số tổng thì chế độ thất bại này đã bị **giấu sau giá trị trung bình**, đúng như lý do mục này tồn tại.

---

## 6.5. Đánh giá khối OCR và hậu xử lý

> **Ràng buộc mẫu số phải nêu ngay đầu mục.** Các chỉ số NFR-A4…A7 chỉ đo được trên **tập con có nhãn chuỗi ký tự** (`datasets/annotations/plate_labels.csv`), chứ không phải trên toàn bộ 1.514 ảnh tập test. Tập con này nhỏ hơn nhiều lần. Mọi bảng trong mục 6.5 vì vậy đều có dòng "số mẫu" và dòng đó **không được phép để trống khi công bố**. Việc thiếu nhãn chuỗi cho phần lớn corpus là một hạn chế thật của đồ án, được ghi nhận ở mục 6.9.3.

### 6.5.1. Độ chính xác mức ký tự (NFR-A4)

Chỉ số dùng ở đây là **CER** (*Character Error Rate*), tính theo khoảng cách Levenshtein giữa chuỗi dự đoán và chuỗi nhãn thật, chuẩn hoá theo độ dài chuỗi nhãn thật:

$$\mathrm{CER} = \frac{S + D + I}{N}$$

trong đó $S$ là số ký tự thay thế, $D$ số ký tự bị xoá, $I$ số ký tự bị chèn thừa, $N$ là tổng số ký tự trong nhãn thật. Chỉ tiêu NFR-A4 được phát biểu theo **1 − CER**.

<!-- {{T6.5a}} do chinh xac muc ky tu NFR-A4 -->

**Bảng 6.9.** Độ chính xác mức ký tự (NFR-A4)

| Chỉ số | Ngưỡng tối thiểu | Mục tiêu | **Đo được (trước hậu xử lý)** | **Đo được (sau hậu xử lý)** | Kết quả |
|---|---:|---:|---:|---:|:---:|
| 1 − CER (NFR-A4) | 0,92 | 0,95 | 0,9061 | **0,9454** | 🟡 đạt ngưỡng tối thiểu |
| CER | ≤ 0,08 | ≤ 0,05 | 0,0939 | 0,0546 | n/a |
| Số ký tự nhãn thật ($N$) | — | — | 23.855 | 23.855 | n/a |
| Số ký tự thay thế ($S$) | — | — | 862 | 862 | n/a |
| Số ký tự bị xoá ($D$) | — | — | 1.272 | 1.272 | n/a |
| Số ký tự chèn thừa ($I$) | — | — | 107 | 107 | n/a |
| **Số biển có nhãn chuỗi (mẫu số)** | — | — | **2.801** | **2.801** | n/a |

> **Nguồn số liệu.** Toàn bộ mục 6.5 lấy số từ `docs/reports/05-results.json` — lượt đo ngày 2026-07-28 trên máy rảnh, mô hình `models/best.pt` (`imgsz = 640`), 2.801 ảnh có nhãn chuỗi, chạy đúng cấu hình giao hàng (nắn hình bật, siêu phân giải tắt — mục 6.5.7).
>
> Lượt này thay thế bộ số ngày 20/07 vì hai lý do độc lập. **Một**, bốn đợt sửa độ chính xác đã rơi vào khoảng 21–28/07 nên số cũ mô tả một hệ thống không còn tồn tại. **Hai**, và nghiêm trọng hơn: harness đo trước ngày 28/07 **chưa bao giờ gọi** bậc thang thử-lại — cả nhánh vùng cắt lẫn nhánh đầu-cuối đều chép lại các bước của pipeline rồi dừng ở bước cứu dòng trên, nên mọi con số A4–A7 công bố trước đó mô tả một pipeline **ngắn hơn bản giao hàng**. Chi tiết ở mục 6.5.7 và `docs/reports/27-retry-ladder-cost-benefit.md`.

> Ba cột $S$/$D$/$I$ đo trên **chuỗi thô trước hậu xử lý** (dẫn ra từ ma trận nhầm lẫn: $S$ = tổng ô ngoài đường chéo, $D$ = tổng xoá, $I$ = tổng chèn, $N$ = tổng ma trận cộng $D$), nên chúng giống nhau ở cả hai cột đo được — và cũng vì vậy bước cứu dòng trên lẫn bậc thang thử-lại, vốn chạy **sau** chuẩn hoá, không làm ba con số này thay đổi. Hậu xử lý nâng 1 − CER từ 0,9061 lên 0,9454.

**NFR-A4 đạt ngưỡng tối thiểu: 1 − CER = 0,9454, vượt sàn 0,92 nhưng còn cách mục tiêu 0,95 khoảng 0,5 điểm.** Chỉ tiêu này từng được ghi là **không đạt** (0,8848, đo 20/07/2026); lượt đo lại ngày 28/07 trên đúng bộ trọng số ấy cho 0,9454. Chênh lệch **không** đến từ một mô hình khác mà từ các bản sửa ở tầng suy luận và từ việc harness đo được nối đúng với pipeline giao hàng (mục 6.5.7).

Đáng chú ý hơn con số tổng là **thay đổi trong cấu trúc lỗi**. Trên 23.855 ký tự nhãn thật, tổng thao tác chỉnh sửa giảm từ 3.092 xuống **2.241**, nhưng ba thành phần giảm rất không đều:

| Loại lỗi | 20/07 | 28/07 | Thay đổi |
|---|---:|---:|---:|
| Chèn thừa ($I$) | 903 | **107** | −88,1% |
| Thay thế ($S$) | 1.007 | **862** | −14,4% |
| Xoá ($D$) | 1.182 | **1.272** | +7,6% |

**Ký tự chèn thừa gần như biến mất.** Đó là dấu vân tay của các bản sửa đọc biển hai dòng: trước đây vùng chồng lấn giữa hai nửa bị đọc hai lần nên sinh ký tự lặp, còn viền biển và vết bẩn bị đọc thành ký tự. Ngược lại **số ký tự bị xoá lại nhích lên** và giờ chiếm **56,8%** toàn bộ lỗi — tức phần lỗi còn lại đã dịch hẳn về một dạng: **đọc hụt ký tự**, không phải đọc nhầm.

Điều này định hình trước mọi kết luận sau đó. Bảng luật hậu xử lý mạnh ở việc sửa $S$ — nhầm ký tự đồng hình ở vị trí đã biết — nhưng **về nguyên tắc không thể phục hồi một ký tự chưa từng được đọc ra**. Khi $D$ trở thành thành phần chi phối, dư địa của hậu xử lý thu hẹp lại, và hướng cải thiện phải chuyển sang tầng nhận dạng (fine-tune bộ nhận dạng trên vùng cắt biển Việt Nam, mục 7.4) chứ không phải thêm luật.

Việc tách $S$, $D$, $I$ không phải chi tiết thừa. Ba loại lỗi này gợi ra ba nguyên nhân khác nhau: $S$ cao trỏ tới **nhầm ký tự** (xử lý được bằng bảng luật sửa lỗi, mục 6.5.4); $D$ cao trỏ tới **bỏ sót ký tự**, thường do vùng cắt bị thiếu hoặc ký tự bị mờ; $I$ cao trỏ tới **nhiễu bị đọc thành ký tự**, thường là viền biển hoặc vết bẩn. Phân tích ở mục 6.8 dựa trực tiếp vào bộ ba này.

### 6.5.2. Chuỗi đầy đủ: trước và sau hậu xử lý (NFR-A5 ↔ NFR-A6)

**Đây là mục quan trọng nhất của cả chương.**

Khối hậu xử lý theo luật — chuẩn hoá ký tự, áp mặt nạ vị trí chữ số / chữ cái theo định dạng biển số Việt Nam, sửa các cặp ký tự đồng hình, kiểm tra mã tỉnh hợp lệ — là **đóng góp kỹ thuật riêng** của đồ án, phần không có sẵn trong bất kỳ thư viện nào và phải được viết từ đặc tả biển số Việt Nam. Câu hỏi tự nhiên của hội đồng phản biện là: *khối đó đóng góp bao nhiêu?*

Câu hỏi ấy chỉ trả lời được nếu **đo hai lần trên cùng một tập mẫu**: một lần với chuỗi thô do PaddleOCR trả về (NFR-A5), một lần với chuỗi sau khi áp toàn bộ luật (NFR-A6). Hiệu số giữa hai lần đo **chính là** đóng góp định lượng của khối hậu xử lý.

> Đây cũng là lý do kỹ thuật khiến trường `raw_ocr_text` tồn tại trong lược đồ cơ sở dữ liệu bên cạnh trường `plate_text` đã chuẩn hoá. Trường đó không phải dữ liệu gỡ lỗi thừa; nó là **điều kiện cần để phép đo này thực hiện được**, và nó phải tồn tại từ giai đoạn thiết kế chứ không thể thêm vào lúc viết chương đánh giá.

<!-- {{T6.5b}} do chinh xac chuoi day du truoc va sau hau xu ly — DONG GOP DINH LUONG CUA KHOI HAU XU LY -->

**Bảng 6.10.** Độ chính xác chuỗi đầy đủ trước và sau hậu xử lý

| Chỉ số | Mã NFR | Ngưỡng tối thiểu | Mục tiêu | **Đo được** | Kết quả |
|---|:---:|---:|---:|---:|:---:|
| Độ chính xác chuỗi **trước** hậu xử lý | NFR-A5 | 0,80 | 0,85 | **0,6373** | ❌ không đạt |
| Độ chính xác chuỗi **sau** hậu xử lý | NFR-A6 | 0,85 | 0,90 | **0,7512** | ❌ không đạt |
| **Mức cải thiện (A6 − A5), điểm phần trăm** | — | — | — | **+11,39** | n/a |
| Số biển **được sửa đúng** nhờ hậu xử lý | — | — | — | **319** | n/a |
| Số biển **bị hậu xử lý làm hỏng** | — | — | — | **0** | n/a |
| Số biển sai cả trước lẫn sau | — | — | — | **697** | n/a |
| **Số mẫu (biển có nhãn chuỗi)** | — | — | — | **2.801** | n/a |

Ba dòng cuối cùng quan trọng ngang dòng hiệu số. Một mức cải thiện thuần +5 điểm có thể là kết quả của việc sửa đúng 60 biển và làm hỏng 10 biển, hoặc sửa đúng 50 và không làm hỏng biển nào. Hai tình huống này **hàm ý hai kết luận kỹ thuật khác nhau** về chất lượng bộ luật, nên hiệu số thuần một mình là không đủ.

**Phân rã đóng góp theo từng nhóm luật** (bảng phụ trợ, giúp trả lời "luật nào đáng giữ") — *(chưa đo)*:

| Nhóm luật hậu xử lý | Số biển bị nhóm luật này thay đổi | Số biển được sửa **đúng** | Số biển bị làm **hỏng** | Đóng góp thuần (điểm %) |
|---|---:|---:|---:|---:|
| Chuẩn hoá cơ bản (bỏ ký tự phân tách, viết hoa, `Đ`→`D`) | *(chưa đo)* | *(chưa đo)* | *(chưa đo)* | *(chưa đo)* |
| Áp mặt nạ vị trí + bảng `TO_DIGIT` | *(chưa đo)* | *(chưa đo)* | *(chưa đo)* | *(chưa đo)* |
| Áp mặt nạ vị trí + bảng `TO_LETTER` | *(chưa đo)* | *(chưa đo)* | *(chưa đo)* | *(chưa đo)* |
| Ghép dòng cho biển hai dòng | *(chưa đo)* | *(chưa đo)* | *(chưa đo)* | *(chưa đo)* |
| Kiểm tra mã tỉnh hợp lệ | *(chưa đo)* | *(chưa đo)* | *(chưa đo)* | *(chưa đo)* |
| **Tổng** | *(chưa đo)* | *(chưa đo)* | *(chưa đo)* | *(chưa đo)* |

> Bảng phân rã theo nhóm luật **chưa đo được**: `ai/inference/plate_rules.py` hiện chưa có cơ chế bật/tắt từng nhóm luật riêng lẻ để chạy lại phép đo. Đây là hạng mục cần viết mã (mục D.2 của tài liệu vận hành) trước khi định vị được đóng góp về từng nhóm; hiện chỉ đo được đóng góp *tổng* +11,39 điểm.
>
> Hai bậc cứu chữa chạy **sau** chuẩn hoá đã cô lập được riêng, nhờ các phép đo A/B ở mục 6.5.6 và 6.5.7: **bước cứu dòng trên** cung cấp câu trả lời cuối cho **209 biển**, **bậc thang thử-lại biển nghiêng/méo** cho **34 biển**.

#### Đóng góp định lượng của khối hậu xử lý (hiệu số A6 − A5 là số dương)

Hiệu số **A6 − A5 = 0,7512 − 0,6373 = +11,39 điểm phần trăm**, đo trên **2.801 biển có nhãn chuỗi**. Đây là đóng góp thuần của khối hậu xử lý theo luật, và nó đi kèm một chi tiết định tính rất mạnh: trong 2.801 biển, hậu xử lý **sửa đúng 319 biển và làm hỏng 0 biển**. Nói cách khác đây **không phải một đánh đổi** (sửa được nhiều nhưng phá hỏng một ít) mà là **cải thiện thuần một chiều** — mọi thay đổi mà khối luật áp vào đều đúng hướng hoặc vô hại trên tập này. Về mặt chất lượng bộ luật, đó là kết quả tốt: nó cho thấy các mặt nạ vị trí và ràng buộc mã tỉnh đủ bảo thủ để không tự tạo ra lỗi mới.

Nhưng phải trung thực về **giới hạn**: dù đóng góp gần gấp đôi so với lượt đo 20/07 (+6,32 → **+11,39 điểm**), cả A5 (0,6373) lẫn A6 (0,7512) vẫn **không đạt** ngưỡng tối thiểu tương ứng (0,80 và 0,85) — A6 còn thiếu 9,88 điểm.

**Đóng góp ấy phân bố rất không đều giữa hai bố cục biển**, và chính sự lệch đó nói lên bản chất của bộ luật:

| | Biển một dòng | Biển hai dòng |
|---|---:|---:|
| A5 (trước hậu xử lý) | 0,9418 | 0,5600 |
| A6 (sau hậu xử lý) | 0,9541 | 0,6996 |
| **Đóng góp (điểm %)** | **+1,23** | **+13,97** |
| Số biển được sửa đúng | 7 | **312** |

Trên biển một dòng, hậu xử lý gần như không có việc để làm — chuỗi thô đã đúng 94,18%. Toàn bộ giá trị của khối luật dồn vào **biển hai dòng**, đúng nơi đề tài đặt trọng tâm, và cũng đúng nơi bố cục hai dòng khiến bộ nhận dạng đọc sai nhiều nhất. Đây là bằng chứng định lượng rằng bộ luật **không** chỉ làm đẹp chuỗi mà thực sự bù đắp cho điểm yếu đã xác định của tầng nhận dạng.

Vì sao đóng góp vẫn không đủ để đạt ngưỡng? Cơ chế của bộ luật là áp mặt nạ "vị trí này phải là chữ số / chữ cái" rồi ánh xạ ký tự đồng hình về đúng lớp. Cơ chế đó bất lực trước hai tình huống vẫn chi phối phần lỗi còn lại:

1. **Chuỗi sai nhiều ký tự cùng lúc.** Chỉ 1.251 trên 2.234 biển hai dòng — 56,0% — đọc đúng trước hậu xử lý (6.5.3). Khi bộ nhận dạng đọc hỏng cả cụm, chuỗi thô đã sai ở mức không một luật thay-ký-tự nào cứu được. **697 biển sai cả trước lẫn sau** hậu xử lý chính là quần thể này.
2. **Ký tự chưa từng được đọc ra thì không luật nào phục hồi được.** Đây là ràng buộc nguyên tắc, không phải khiếm khuyết cài đặt. Với $D$ = 1.272 ký tự bị xoá — chiếm 56,8% toàn bộ lỗi sau khi $I$ đã giảm 88% (T6.5a) — nhiều chuỗi ngắn hơn độ dài mong đợi, mặt nạ vị trí bị lệch pha, và luật khi đó **không dám sửa** (giữ nguyên: an toàn nhưng không cải thiện) chứ không sửa bừa. Con số **0 biển bị làm hỏng** chính là hệ quả quan sát được của thiết kế bảo thủ đó.

Vậy kết luận đúng phạm vi cho RQ3 là: *khối hậu xử lý theo luật đóng góp **+11,39 điểm** độ chính xác chuỗi đầy đủ trên mẫu 2.801 biển — **+13,97 điểm riêng trên biển hai dòng** — là cải thiện thuần không rủi ro (319 sửa đúng / 0 làm hỏng), nhưng vẫn không đủ đưa A6 tới ngưỡng vì phần lỗi còn lại đã dịch sang dạng **đọc hụt ký tự**, nơi hậu xử lý theo luật về nguyên tắc không với tới được.* Rất ít công trình ALPR đo tách bạch phần đóng góp của khối hậu xử lý; ở đây nó được lượng hoá cùng với chứng cứ về giới hạn của chính nó, và giới hạn ấy chỉ thẳng sang hướng khắc phục ở tầng nhận dạng (mục 7.4). Việc định vị đóng góp về **từng nhóm luật** (bảng phân rã ở trên) là bước tiếp theo, hiện chưa đo được vì thiếu cơ chế bật/tắt luật.

### 6.5.3. Tách theo biển một dòng và hai dòng cho OCR

Nếu bảng T6.4b cho thấy tầng phát hiện gần như không phân biệt hai layout, thì bảng dưới là nơi chênh lệch thật sự lộ ra. Đọc chuỗi ký tự trên biển hai dòng khó hơn về bản chất: hệ thống phải xác định thứ tự dòng, ghép hai dòng đúng chiều, và làm việc với ký tự nhỏ hơn ở cùng một diện tích biển.

<!-- {{T6.5c}} OCR tach theo layout mot dong / hai dong -->

**Bảng 6.11.** Độ chính xác nhận dạng tách theo biển một dòng và hai dòng

| Chỉ số | Biển **một dòng** | Biển **hai dòng** | Chênh lệch (điểm %) |
|---|---:|---:|---:|
| Số mẫu có nhãn chuỗi | **567** | **2.234** | n/a |
| 1 − CER (NFR-A4) | 0,9925 | 0,9344 | 5,81 |
| Chuỗi đúng **trước** hậu xử lý (A5) | 0,9418 | 0,5600 | 38,18 |
| Chuỗi đúng **sau** hậu xử lý (A6) | 0,9541 | 0,6996 | 25,45 |
| Mức cải thiện do hậu xử lý (A6 − A5) | +1,23 | +13,97 | n/a |
| Độ chính xác E2E (A7) | 0,6861 | 0,5219 | — |

**Đây là kết quả khoa học quan trọng nhất của chương.** Chênh lệch giữa hai layout mà tầng phát hiện gần như che khuất (2,09 điểm ở T6.4b) nay lộ ra ở tầng OCR với **biên độ hoàn toàn khác cấp**:

- Ở **độ chính xác ký tự** (1 − CER), biển một dòng đạt **0,9925** — gần hoàn hảo — trong khi biển hai dòng đạt **0,9344**, chênh **5,81 điểm**.
- Ở **độ chính xác chuỗi đầy đủ sau hậu xử lý** (A6), biển một dòng đạt **0,9541** (vượt cả mục tiêu 0,90), còn biển hai dòng chỉ **0,6996**, chênh **25,45 điểm**.
- Ở **chuỗi trước hậu xử lý** (A5) khoảng cách còn rộng hơn: **38,18 điểm** (0,9418 so với 0,5600).

Nói cách khác, **biển một dòng của hệ thống này về cơ bản đã giải xong** (A6 = 0,9541 vượt mục tiêu; 1 − CER = 0,9925), và toàn bộ việc "OCR không đạt" ở các bảng tổng hợp là do **biển hai dòng kéo xuống**. Vì biển hai dòng chiếm **2.234 / 2.801 = 79,8%** tập có nhãn chuỗi (phản ánh tỉ lệ xe máy rất cao trong giao thông Việt Nam), con số tổng bị chi phối bởi quần thể khó này. Cũng đáng lưu ý: hậu xử lý theo luật đóng góp **+13,97 điểm cho biển hai dòng** so với chỉ **+1,23 điểm cho biển một dòng** — hợp lý, vì biển một dòng gần như đã đúng sẵn nên không còn nhiều chỗ để sửa.

**Khoảng cách 25,45 điểm này là con số *sau* khi đã áp cả hai bậc cứu chữa** — bước cứu dòng trên (6.5.6) và bậc thang thử-lại biển nghiêng/méo (6.5.7). Ở lượt đo 20/07, trước khi các bản sửa đọc biển hai dòng và bậc thang được nối vào đường đo, A6 của biển hai dòng là 0,5810 và khoảng cách là 36,79 điểm. Nghĩa là chuỗi biện pháp nhắm đúng chế độ thất bại của biển hai dòng đã thu hẹp khoảng cách **11,34 điểm** — một dịch chuyển thật và đáng kể, nhưng vẫn để lại một phần tư khoảng cách. Bằng chứng: phần còn lại nằm ở **năng lực nhận dạng ký tự**, không ở khâu cắt/ghép hay hình học, vì cả hai khâu sau đã được xử lý và đo tách bạch.

**Mốc tham chiếu quốc tế — phải đọc kèm cảnh báo.** Công trình của Laroca và cộng sự tại VISAPP 2022 báo cáo độ chính xác **94,3%** trên biển một dòng và **45,7%** trên biển hai dòng, chênh **48,6 điểm phần trăm**; phép đo này thực hiện trên bộ dữ liệu **RodoSol-ALPR của Brazil** [7]<!-- laroca_2022_crossdataset -->. **Đây là số liệu Brazil, không phải số liệu Việt Nam**, và biển hai dòng Brazil khác biển hai dòng Việt Nam cả về tỉ lệ khung hình lẫn bộ ký tự. Con số 48,6 điểm chỉ được dùng như **một mốc tham chiếu về bậc độ lớn** của khoảng cách giữa hai layout, cho phép trả lời câu hỏi: *chênh lệch đo được của hệ thống này thuộc cùng bậc độ lớn, nhỏ hơn hẳn, hay lớn hơn?* Nó **không** phải chỉ tiêu cần vượt qua, và **không** được trình bày như số liệu so sánh trực tiếp.

**Đối chiếu bậc độ lớn.** Chênh lệch A6 đo được của hệ thống này là **25,45 điểm** (đo trên biển số **Việt Nam thật**, trên 2.801 biển có nhãn chuỗi), so với **48,6 điểm** của Laroca và cộng sự trên RodoSol-ALPR **Brazil**. Hai con số **cùng bậc độ lớn** — cùng cho thấy biển hai dòng khó hơn biển một dòng vài chục điểm phần trăm ở tầng nhận dạng chuỗi. Không được kết luận mạnh hơn thế: 25,45 < 48,6 **không** có nghĩa hệ thống này "tốt hơn" công trình Brazil, vì hai phép đo dùng bộ dữ liệu khác nhau, bộ ký tự khác nhau, tỉ lệ khung hình biển khác nhau, và mẫu số khác nhau. Kết luận hợp lệ duy nhất: khoảng cách hai layout mà hệ thống này đo được **thuộc đúng bậc độ lớn** mà tài liệu quốc tế đã ghi nhận cho bài toán biển hai dòng — tức đây là một đặc tính có cấu trúc của bài toán, không phải một khiếm khuyết riêng của hệ thống.

Cần nhắc lại một khoảng trống đã xác định từ khảo sát tài liệu: **chưa có nghiên cứu Việt Nam nào công bố hai con số này tách bạch trên cùng một hệ thống**. Bảng T6.5c chính là phần lấp vào khoảng trống đó — đây là lý do mục này không được phép bỏ dù mẫu số nhỏ, và cũng là câu trả lời trực tiếp cho RQ2: **có, chênh lệch giữa hai layout là có ý nghĩa và rất lớn (25,45 điểm A6), và nó nằm ở tầng OCR chứ không ở tầng phát hiện.**

### 6.5.4. Ma trận nhầm lẫn ký tự 36×36

Mục này trả lời RQ5 và có một mục đích rất cụ thể: **thay thế tri thức suy đoán bằng tri thức đo được**.

Bảng luật sửa lỗi hiện hành trong `ai/inference/plate_rules.py` gồm hai ánh xạ:

```
TO_DIGIT  = {O→0, Q→0, D→0, I→1, J→1, L→1, Z→2, A→4, S→5, G→6, T→7, B→8}
TO_LETTER = {0→D, 1→L, 2→Z, 3→B, 4→A, 5→S, 6→G, 7→T, 8→B}
```

Docstring của chính hai hằng số này thừa nhận thẳng nguồn gốc của chúng: *"This table is derived from glyph-shape reasoning, not from measurement"* — bảng được suy ra từ hình dạng chữ, không từ đo đạc, và một số cặp (đặc biệt `L→1`) được đánh dấu là **phỏng đoán yếu**. Việc mã nguồn tự ghi nhận điều này là một quyết định đúng: trình bày một giả thuyết như giả thuyết chờ kiểm chứng thì trung thực hơn và cũng mạnh hơn là trình bày nó như kết luận đã chốt.

Ma trận nhầm lẫn 36×36 (10 chữ số + 26 chữ cái) đo trên các cặp ký tự đã căn chỉnh giữa chuỗi dự đoán và chuỗi nhãn thật là **bằng chứng thực nghiệm** cần thiết để chuyển giả thuyết đó thành tri thức.

*Hình 6.5.* Ma trận nhầm lẫn ký tự 36×36, thang log(1+n), đo trên chuỗi thô trước hậu xử lý.
Đường dẫn hình: `docs/reports/figures/04-ocr-confusion-matrix.png` *(chưa sinh)*

*Hình 6.6.* Biểu đồ cột 15 cặp ký tự bị nhầm nhiều nhất.
Đường dẫn hình: `docs/reports/figures/04-ocr-top-confusions.png` *(chưa sinh)*

<!-- {{T6.5d}} top cac cap ky tu bi nham thuc te, doi chieu bang luat hien hanh -->

**Bảng 6.12.** Các cặp ký tự bị nhầm nhiều nhất, đối chiếu bảng luật hiện hành

| Hạng | Ký tự thật | Ký tự bị đọc thành | Số lần | Tỉ lệ trong tổng số lỗi thay thế | Bảng luật hiện có phủ cặp này không? | Hướng ánh xạ có đúng không? |
|:---:|:---:|:---:|---:|---:|:---:|---|
| 1 | L | 1 | 90 | 10,44% | có (`TO_DIGIT`) | đúng chiều — luật `L → 1` thuộc TO_DIGIT |
| 2 | E | F | 73 | 8,47% | không | chưa có luật nào phủ cặp này |
| 3 | 4 | L | 53 | 6,15% | không | chưa có luật nào phủ cặp này |
| 4 | U | 1 | 38 | 4,41% | không | chưa có luật nào phủ cặp này |
| 5 | D | 0 | 34 | 3,94% | có (`TO_DIGIT`) | đúng chiều — luật `D → 0` thuộc TO_DIGIT |
| 6 | Z | 7 | 32 | 3,71% | không | chưa có luật nào phủ cặp này |
| 7 | 2 | 7 | 26 | 3,02% | không | chưa có luật nào phủ cặp này |
| 8 | X | Y | 21 | 2,44% | không | chưa có luật nào phủ cặp này |
| 9 | B | R | 20 | 2,32% | không | chưa có luật nào phủ cặp này |
| 10 | 9 | 0 | 19 | 2,20% | không | chưa có luật nào phủ cặp này |

> Ma trận 36×36, mẫu số 2.801 biển có nhãn chuỗi, tổng số lỗi thay thế $S$ = 862. Cột tỉ lệ lấy $S$ làm mẫu số.

**Kết quả này trả lời RQ5 theo hướng ít ai ngờ: bảng luật hiện hành phần lớn *không khớp* với các cặp nhầm thật.** Trong 10 cặp bị nhầm nhiều nhất, **chỉ 2 cặp** (`L→1` hạng 1, `D→0` hạng 5) được bảng luật hiện có phủ; **8 cặp còn lại chưa có luật nào phủ** — đáng chú ý là `E→F` (73 lần), `4→L` (54 lần), `U→1` (38 lần). Đây đều là các cặp **suy đoán hình dạng không dự đoán được**: chúng phát sinh từ đặc thù phông chữ biển số và điều kiện ảnh thật, không từ sự giống nhau về nét chữ theo trực giác. Ngược lại, nhiều cặp *có* trong bảng luật lại gần như không xuất hiện.

Bảng đối chiếu ngược — các cặp **có trong bảng luật nhưng không quan sát thấy trong dữ liệu** (số lần quan sát = 0):

| Cặp trong bảng luật | Thuộc bảng | Số lần quan sát thực tế | Đề xuất |
|---|:---:|---:|---|
| `D → 0` | `TO_DIGIT` | 0 | Xem xét loại — không quan sát thấy chiều này |
| `J → 1` | `TO_DIGIT` | 0 | Xem xét loại |
| `A → 4` | `TO_DIGIT` | 0 | Xem xét loại |
| `T → 7` | `TO_DIGIT` | 0 | Xem xét loại |
| `B → 8` | `TO_DIGIT` | 0 | Xem xét loại |
| `2 → Z` | `TO_LETTER` | 0 | Xem xét loại |
| `3 → B` | `TO_LETTER` | 0 | Xem xét loại |

> **Lưu ý về hai chiều của cùng một cặp glyph.** Cặp `L → 1` (ký tự thật L bị đọc thành chữ số 1) quan sát được **90 lần** và là cặp nhầm nhiều nhất; nhưng chiều ghi trong bảng `TO_DIGIT` là "khi engine đọc ra `L` tại vị trí chữ số thì đổi `L → 1`" — chiều này chỉ khớp **2 lần** trong dữ liệu. Sự bất đối xứng này đúng chứ không phải lỗi: bảng luật sửa ký tự *engine đọc ra*, còn ma trận nhầm lẫn đếm ký tự *thật bị đọc sai*; hai chiều không nhất thiết cân bằng. Danh sách đề xuất hiệu chỉnh đầy đủ (thêm/đổi/giữ từng ánh xạ, kèm mức hỗ trợ quan sát) nằm ở khoá `doi_chieu_bang_luat.proposed_updates` trong `05-results.json`.

**Một tính chất của bảng luật cần nhấn mạnh vì nó thường bị hiểu sai: ánh xạ không đối xứng, và sự bất đối xứng đó là đúng chứ không phải lỗi.** Cặp `O → 0` là hợp lệ tại vị trí chữ số. Nhưng chiều ngược lại `0 → O` **không bao giờ** hợp lệ, vì `O` không phải chữ cái sê-ri hợp pháp trong định dạng biển số Việt Nam. Khi loại cả `O` và `Q`, ứng viên đồng hình duy nhất còn lại ở vị trí chữ cái là `D`. Do đó chiều đúng là `O → 0` tại vị trí chữ số và `0 → D` tại vị trí chữ cái. Ma trận nhầm lẫn không tự nó biết điều này — nó chỉ đếm tần suất; việc chuyển từ tần suất sang luật vẫn cần **ràng buộc miền** từ quy chuẩn biển số.

**Tiêu chí chấp nhận một cặp vào bảng luật đã hiệu chỉnh** (định trước, để tránh chọn theo kết quả):

1. Cặp phải xuất hiện với tần suất vượt một ngưỡng thống kê tối thiểu, không phải một hai lần lẻ tẻ.
2. Chiều ánh xạ phải **tương thích với ràng buộc vị trí** của định dạng biển số Việt Nam — ký tự đích phải hợp pháp tại vị trí đó.
3. Áp cặp đó vào toàn tập phải cho **đóng góp thuần không âm** ở bảng T6.5b.

Cặp nào không thoả cả ba tiêu chí thì bị loại khỏi bảng luật, **kể cả khi nó nghe có vẻ hợp lý về mặt hình dạng chữ**. Việc loại bỏ, nếu xảy ra, phải được ghi vào Chương 7 như một hạn chế đã được sửa chứ không phải một thất bại được giấu.

### 6.5.5. Độ chính xác đầu-cuối toàn trình (NFR-A7)

NFR-A7 đo chuỗi xử lý hoàn chỉnh: **ảnh đầu vào → phát hiện → cắt → OCR → hậu xử lý → chuỗi biển số cuối cùng**. Khác biệt so với NFR-A6 là ở chỗ A6 đo trên **vùng biển đã cắt chuẩn theo nhãn thật**, còn A7 đo trên vùng biển do **chính bộ phát hiện của hệ thống** tìm ra. Vì vậy A7 tích luỹ cả sai số phát hiện lẫn sai số nhận dạng, và theo lý thuyết luôn thấp hơn hoặc bằng A6.

<!-- {{T6.5e}} do chinh xac E2E toan trinh NFR-A7 -->

**Bảng 6.13.** Độ chính xác đầu-cuối toàn trình (NFR-A7)

| Chỉ số | Ngưỡng tối thiểu | Mục tiêu | **Đo được** | Kết quả |
|---|---:|---:|---:|:---:|
| Độ chính xác E2E (NFR-A7) | 0,82 | 0,88 | **0,5552** | ❌ không đạt |
| Độ chính xác E2E **với điều kiện đã phát hiện được biển** | — | — | 0,6306 | n/a |
| Tỉ lệ biển **bị bỏ sót** ở tầng phát hiện | — | — | 0,1196 | n/a |
| Tỉ lệ biển phát hiện đúng nhưng **đọc sai chuỗi** *(mẫu số riêng: số biển đã phát hiện được)* | — | — | 0,3694 | n/a |
| Chênh lệch A6 − A7 (phần mất do tầng phát hiện) | — | — | 19,60 | n/a |
| **Số mẫu** | — | — | **2.801** | n/a |

> ⚠ **Cảnh báo hiệu lực — phải đọc trước khi diễn giải A7.** Con số A7 = 0,5552 đo trên **ảnh crop biển số**, không phải ảnh hiện trường, vì không bộ dữ liệu nào trong đồ án có đồng thời ảnh toàn cảnh *và* chuỗi biển số nhãn thật. Bộ phát hiện được huấn luyện trên ảnh giao thông đầy đủ, nên một tấm ảnh chỉ có biển số chiếm gần hết khung là **ngoài phân bố huấn luyện** của nó: phần lớn thất bại ở đây là do bộ phát hiện không bắt được box trên ảnh crop (tỉ lệ bỏ sót 11,96%), **không** phải do OCR đọc sai. Bằng chứng: trên ảnh hiện trường thật, Phase 7 đo được mAP@0.5 = 0,9829 cho bộ phát hiện — hoàn toàn tương thích với T6.4a. Muốn đo NFR-A7 đúng cách cần gán nhãn chuỗi biển số cho một phân bố test có ảnh hiện trường (ví dụ một phần của yolo_v2) — **việc này chưa làm.**

**A7 không đạt (0,5552), nhưng nguồn lỗi được phân tách rõ.** Độ chính xác *có điều kiện đã phát hiện được biển* là 0,6306 — cao hơn A7 (0,5552) đúng bằng phần mất do bỏ sót ở tầng phát hiện. Cụ thể: 11,96% biển bị **bỏ sót** ở tầng phát hiện (335 / 2.801), và trong số biển đã phát hiện được, 36,94% **đọc sai chuỗi**. Chênh A6 − A7 = 19,60 điểm chính là phần độ chính xác mất đi khi chuyển từ "vùng biển cắt chuẩn theo nhãn thật" (A6) sang "vùng biển do chính hệ thống tìm ra" (A7). Tuy nhiên, do cảnh báo hiệu lực ở trên, **tỉ lệ bỏ sót 11,96% này bị thổi phồng bởi việc đo trên ảnh crop ngoài phân bố** — trên ảnh hiện trường thật bộ phát hiện gần như không bỏ sót (mAP@0.5 = 0,9829). Vì vậy kết luận đúng phạm vi là: *A7 = 0,5552 phản ánh giới hạn của **giao thức đo hiện có** (thiếu tập test hiện trường có nhãn chuỗi) chồng lên giới hạn thật của tầng OCR trên biển hai dòng; con số này là **cận dưới bi quan** của năng lực E2E thật, không phải ước lượng điểm.* Dòng "với điều kiện đã phát hiện được biển" tồn tại chính để phân tách hai nguồn lỗi này: nếu chỉ tăng recall bộ phát hiện thì cũng không đưa A7 lên quá 0,6306 — trần thật vẫn bị chặn bởi tầng OCR trên biển hai dòng.

**Vì sao A7 luôn tăng chậm hơn A6.** Mọi biện pháp cứu chữa ở tầng nhận dạng — bước cứu dòng trên (6.5.6) và bậc thang thử-lại (6.5.7) — đều được áp vào **cả hai** đường đo, nhưng mức cải thiện bị **pha loãng** ở A7: 11,96% số biển thất bại ngay ở tầng phát hiện, tức chúng không bao giờ tới được khối OCR để mà được cứu. Phần cải thiện chỉ có chỗ tác động trên 88,04% mẫu còn lại.

Con số tách bạch chứng minh điều đó: giữa lượt 20/07 và lượt 28/07, **`missed_by_detector` giữ nguyên đúng 335 và tỉ lệ phát hiện giữ nguyên đúng 0,8804** — bộ trọng số phát hiện không hề thay đổi. Toàn bộ mức tăng của A7 vì vậy đến từ khối nhận dạng, và đại lượng đo đúng mức tăng ấy là **độ chính xác có điều kiện đã phát hiện được**: 0,6014 → **0,6306**, tức **+2,92 điểm**. Con số A7 tăng ít hơn (+2,57 điểm) chỉ vì nó là đại lượng trên đã bị 335 ca vô vọng kéo xuống. Chênh lệch giữa hai mức tăng **không** phải dấu hiệu sai sót — nó là hệ quả số học của việc A7 bao hàm thêm một tầng có thể thất bại trước.

### 6.5.6. Bước "cứu dòng trên" cho biển hai dòng — thiết kế, kiểm chứng A/B và kết quả trên toàn tập

Mục 6.5.3 xác định biển hai dòng là nguồn gần như duy nhất của lỗi nhận dạng, và bảng T6.5a chỉ ra chế độ thất bại cụ thể: **số ký tự bị xoá ($D$ = 1.272) nhiều hơn số bị thay thế ($S$ = 862)**. Một hồ sơ lỗi thiên về *xoá* trên biển hai dòng có một cách giải thích tự nhiên — **mất hẳn một dòng**, chứ không phải đọc nhầm lẻ tẻ. Mục này trình bày biện pháp nhắm đúng chế độ thất bại đó, và quan trọng hơn, trình bày **cách nó đã được kiểm chứng trước khi được tin**.

#### Giả thuyết bị bác bỏ trước: "đọc riêng từng dòng rồi ghép"

Cách xử lý biển hai dòng của hệ thống là **ghép-rồi-đọc** (*split-then-hstack*): cắt vùng biển thành hai nửa chồng lấn, xếp cạnh nhau thành một dải ngang, rồi chạy OCR **một lần** trên dải đó. Phương án thay thế hiển nhiên — đọc riêng từng nửa rồi nối hai chuỗi — đã được đo A/B chứ không bị loại bằng lập luận.

<!-- {{T6.5f}} A/B hai chien luoc doc bien hai dong -->

**Bảng 6.14.** So sánh A/B hai chiến lược đọc biển hai dòng

| Chiến lược | Số biển đúng / 200 | Độ chính xác | Số ca OCR trả chuỗi rỗng | Thời gian trung bình (ms) |
|---|---:|---:|---:|---:|
| **A — ghép hai nửa rồi OCR một lần** *(đang dùng)* | **129** | **64,50%** | 2 | 340,11 |
| B — OCR từng nửa rồi nối chuỗi | 7 | 3,50% | 9 | 391,35 |
| **Chênh lệch (B − A), điểm phần trăm** | — | **−61,00** | — | +51,24 |

> Mẫu 200 biển hai dòng, `seed = 20260720`, nguồn `datasets/annotations/plate_text_labels_vn.csv`. Số ca A thắng B: **122**; số ca B thắng A: **0**. Tệp kết quả: `docs/reports/15-two-line-ab.json`.

**Giả thuyết "đọc riêng từng dòng thì chính xác hơn" bị bác bỏ dứt khoát, với biên 61 điểm và 0 ca thắng ngược.** Nguyên nhân đọc được ngay trong dữ liệu: hai nửa **cố ý chồng lấn** để không cắt cụt ký tự, nên khi đọc riêng, dải chồng lấn bị đọc **hai lần** và ký tự bị nhân đôi — biển `84G122593` trở thành `84-G124E009.01225.93`. Ghép trước chính là điều cho phép bộ dò chữ loại bỏ dải chồng lấn đó. Đây là một kết quả âm có giá trị: nó cho thấy lựa chọn kiến trúc ở Chương 5 không phải tuỳ tiện.

#### Chế độ thất bại còn lại của chiến lược ghép, và biện pháp

Dải ghép có một chế độ thất bại riêng. Khi **dòng trên nằm lệch thấp** trong một vùng cắt rộng rãi, bộ dò chữ chỉ tìm thấy **một vùng văn bản duy nhất** — dòng dưới — và mã tỉnh cùng chữ cái sê-ri **mất hoàn toàn**: `29E-015.66` trở về `015.66`, năm chữ số trần không khớp bất kỳ định dạng biển số Việt Nam nào, nên khối kiểm tra hợp lệ **bác bỏ đúng**. Chính sự bác bỏ đó là tín hiệu dùng được.

Bước **cứu dòng trên** (`rescue_two_line_upper` trong `ai/inference/pipeline.py`) hoạt động như sau, và cổng mở của nó rất hẹp:

1. Chỉ kích hoạt khi **cả ba** điều kiện đồng thời đúng: biển có `line_count = 2`, chuỗi sau chuẩn hoá **không hợp lệ định dạng**, và chuỗi thô **không rỗng**.
2. Đọc **riêng nửa trên** bằng một lời gọi OCR bổ sung.
3. Nối `nửa trên + chuỗi thô của dải ghép` rồi cho đi qua lại khối chuẩn hoá.
4. **Chỉ giữ kết quả mới nếu nó hợp lệ định dạng**; mọi trường hợp khác — kể cả ngoại lệ trong lúc thử — trả về nguyên kết quả cũ.

Điều kiện (1) là thứ khiến bước này **về mặt cấu trúc không thể làm hỏng** một biển vốn đã đọc đúng: một chuỗi đã hợp lệ thì không bao giờ được thử lại. Đó là lý do cột "số biển bị làm hỏng" bằng 0 trong mọi phép đo dưới đây — con số 0 ấy là **hệ quả của thiết kế**, không phải may mắn thống kê.

#### Kiểm chứng A/B trên hai mẫu độc lập

<!-- {{T6.5g}} A/B buoc cuu dong tren, hai mau doc lap -->

**Bảng 6.15.** So sánh A/B bước cứu dòng trên trên hai mẫu độc lập

| Mẫu | Chỉ *ghép* (A) | Ghép **+ cứu dòng trên** (C) | Chênh (điểm %) | Số biển được cứu | Số biển bị hỏng | Tỉ lệ bước cứu kích hoạt | Thời gian TB (ms) |
|---|---:|---:|---:|---:|---:|---:|---:|
| 700 biển, `seed = 7` | 421 / 700 = **60,14%** | 434 / 700 = **62,00%** | **+1,86** | 13 | **0** | 21,14% (148/700) | 362,41 → 383,52 |
| 200 biển, `seed = 20260720` | 129 / 200 = **64,50%** | 130 / 200 = **65,00%** | **+0,50** | 1 | **0** | 18,00% (36/200) | 346,70 → 361,97 |

> Tệp kết quả: `docs/reports/15-two-line-fallback-700.json` và `docs/reports/15-two-line-fallback.json`. Hai mẫu dùng **seed khác nhau** nên là hai lượt lấy mẫu độc lập.

Ba điều đọc được từ bảng này. Thứ nhất, **dấu của hiệu số nhất quán trên cả hai mẫu** và **không mẫu nào có ca bị làm hỏng** — đúng như dự đoán từ cấu trúc cổng kích hoạt. Thứ hai, **độ lớn thì không nhất quán** (+1,86 so với +0,50): với mẫu 200 biển, một biển được cứu đã bằng 0,5 điểm, nên con số +0,50 nằm hoàn toàn trong dao động lấy mẫu và **không được dùng làm bằng chứng độc lập** — nó chỉ có giá trị xác nhận *không có hồi quy*. Thứ ba, **chi phí đo được**: bước cứu kích hoạt trên khoảng một phần năm số vùng cắt hai dòng — và chỉ trên những vùng vốn đã thất bại — đổi lấy khoảng **21 ms** thời gian trung bình mỗi biển. Đó là một đánh đổi rẻ vì nó không chạm vào đường đi của các biển đọc đúng.

#### Kết quả trên toàn tập 2.801 biển có nhãn chuỗi

<!-- {{T6.5h}} truoc/sau buoc cuu dong tren tren toan tap co nhan chuoi -->

**Bảng 6.16.** Trước và sau bước cứu dòng trên, đo trên toàn tập có nhãn chuỗi

| Chỉ tiêu | Trước bước cứu | **Sau bước cứu** | Chênh (điểm %) | Ngưỡng tối thiểu | Kết quả |
|---|---:|---:|---:|---:|:---:|
| NFR-A4 — độ chính xác ký tự (1 − CER) | 0,8734 | **0,8848** | **+1,14** | 0,92 | ❌ vẫn không đạt |
| NFR-A5 — chuỗi đúng **trước** hậu xử lý | 0,6098 | **0,6098** | **0,00** | 0,80 | ❌ vẫn không đạt |
| NFR-A6 — chuỗi đúng **sau** hậu xử lý | 0,6555 | **0,6730** | **+1,75** | 0,85 | ❌ vẫn không đạt |
| NFR-A7 — đầu-cuối toàn trình | 0,5227 | **0,5295** | **+0,68** | 0,82 | ❌ vẫn không đạt |
| A6 — riêng biển **một dòng** | 0,9489 | **0,9489** | **0,00** | — | n/a |
| A6 — riêng biển **hai dòng** | 0,5810 | **0,6030** | **+2,20** | — | n/a |
| Số biển bị bước cứu can thiệp | — | **89 / 2.801** | — | — | n/a |
| Trong đó thành chuỗi đúng hoàn toàn | — | **49** | — | — | n/a |
| Số biển bị bước cứu làm hỏng | — | **0** | — | — | n/a |

> Nguồn: `docs/reports/16-ocr-accuracy-rescued.json`, đo 2026-07-20 trên máy rảnh, `models/best.pt` với `imgsz = 640`, 2.801 ảnh có nhãn chuỗi. Cột "trước" là lượt đo trước đó trên đúng cùng tập mẫu và cùng mô hình.
>
> ⚠ **Đây là bảng A/B lịch sử, giữ nguyên số của ngày 20/07.** Nó trả lời đúng một câu hỏi — *riêng bước cứu dòng trên đóng góp bao nhiêu* — và câu trả lời ấy không đổi theo thời gian. Nhưng **các giá trị tuyệt đối trong bảng đã bị vượt qua**: A6 hiện là 0,7512 chứ không phải 0,6730, sau các bản sửa đọc biển hai dòng và sau khi harness đo được nối đúng với pipeline giao hàng. Không được trích cột "sau bước cứu" như số hiện hành; số hiện hành nằm ở T6.5b và mục 6.5.7. Trên lượt đo 28/07, bước cứu dòng trên cung cấp câu trả lời cuối cho **209 biển**.

**Ba ô "không đổi" trong bảng trên phải được đọc như bằng chứng, không như thiếu sót.** Mỗi ô đều có một lý do cấu trúc kiểm chứng được:

- **NFR-A5 không đổi là đúng thiết kế.** Bước cứu chạy **sau** khối chuẩn hoá — nó chỉ được gọi khi chuỗi *đã chuẩn hoá* thất bại kiểm tra định dạng. Một bước nằm sau chuẩn hoá thì **không thể** tác động lên chỉ số đo *trước* chuẩn hoá. Nếu A5 có xê dịch, đó mới là dấu hiệu phép đo bị lệch.
- **Biển một dòng không đổi là đúng.** Cổng kích hoạt yêu cầu `line_count = 2`; toàn bộ 89 biển được can thiệp đều là biển hai dòng. Không một biển một dòng nào bị chạm tới.
- **Số biển bị làm hỏng bằng 0 là đúng.** Chuỗi đã hợp lệ không bao giờ được thử lại (điều kiện 1 ở trên).

Tác dụng thật nằm ở đúng nơi được nhắm: **biển hai dòng, +2,20 điểm**. Và tác dụng đó vẫn để lại **bốn chỉ tiêu OCR đều không đạt** — đây là một cải thiện, không phải một lời giải.

#### Ghi chú phương pháp đo — một lỗi có giá trị học thuật, được ghi lại thay vì giấu đi

Lượt đo lại **đầu tiên** sau khi thêm bước cứu cho ra một kết quả tự mâu thuẫn: **NFR-A6 tăng 1,75 điểm trong khi NFR-A7 đứng yên ở đúng 0,5227**. Chính sự đứng yên đó là dấu hiệu.

Lập luận: A7 đo chuỗi *phát hiện → cắt → OCR → hậu xử lý*, tức nó **bao hàm** toàn bộ phần mà A6 đo. Một biện pháp cải thiện khâu nhận dạng, nếu thật sự đang chạy, **không thể** nâng chỉ số con mà để chỉ số bao hàm nó bất động ở từng chữ số thập phân. Xác suất để 49 biển được sửa đúng ở nhánh A6 mà **không một biển nào** trong đó đi trọn được đường E2E là quá nhỏ để chấp nhận. Nguyên nhân tìm được ngay: trong `ai/evaluation/ocr_accuracy.py`, bước cứu mới chỉ được nối vào nhánh đo A5/A6; **hàm dựng đường E2E vẫn gọi thẳng bộ chuẩn hoá rồi trả kết quả**, bỏ qua bước cứu. Nói cách khác, con số A7 đang mô tả một hệ thống **ngắn hơn** hệ thống thật mà người dùng chạy. Sau khi nối bước cứu vào cả đường E2E và đo lại, A7 mới lên 0,5295.

**Đây là lần thứ hai cùng một loại lỗi xuất hiện trong đồ án**, và việc ghi nhận điều đó quan trọng hơn việc lặng lẽ sửa nó. Lần thứ nhất chính là ở nhánh A5/A6: kịch bản đánh giá vốn dựng lại đường xử lý của riêng nó, nên khi khối suy luận sản phẩm có thêm một bước, kịch bản đánh giá **không tự động có** bước ấy. Cả hai lần, triệu chứng đều là một chỉ số **đứng yên một cách vô lý**, không phải một chỉ số sai lệch rõ ràng — và một con số không đổi thì dễ được cho qua hơn nhiều so với một con số sai.

Bài học phương pháp luận, phát biểu ở dạng dùng lại được:

> Khi chỉ số $X$ **bao hàm** chỉ số $Y$ về mặt định nghĩa, mà một can thiệp làm $Y$ dịch chuyển còn $X$ thì không nhúc nhích, **giả thuyết đầu tiên phải là đường đo của $X$ bị lệch khỏi đường chạy thật**, chứ không phải "can thiệp không có tác dụng ở mức toàn trình". Chỉ được kết luận vế thứ hai sau khi đã đối chiếu mã của hai đường đo.

Biện pháp đã áp dụng lúc đó: bước cứu được viết thành **hàm tự do dùng chung** (`should_rescue_two_line` và `rescue_two_line_upper` trong `ai/inference/pipeline.py`) thay vì phương thức riêng của lớp pipeline, để kịch bản đánh giá — vốn điều khiển thẳng bộ nhận dạng và bộ chuẩn hoá mà không dựng pipeline — gọi được **đúng một bản cài đặt** đó.

#### Biện pháp đó đã thất bại, và lần thứ ba chứng minh vì sao

Ngày 28/07/2026, **đúng loại lỗi ấy xuất hiện lần thứ ba**. Bậc thang thử-lại biển nghiêng/méo (mục 6.5.7), thêm vào pipeline ngày 21/07, **chưa bao giờ được kịch bản đánh giá gọi** — ở cả nhánh vùng cắt lẫn nhánh đầu-cuối. Mọi con số A4–A7 công bố từ 21/07 đến 28/07 vì vậy mô tả một pipeline ngắn hơn bản giao hàng.

Điều đáng nói: bậc thang **đã** được viết đúng như biện pháp trên quy định — là hàm tự do dùng chung (`should_retry_skewed`, `retry_skewed_variants`), không phải phương thức riêng. Biện pháp được tuân thủ đầy đủ, và lỗi vẫn tái diễn.

Lý do là biện pháp ấy giải quyết sai vấn đề. Viết thành hàm dùng chung chỉ bảo đảm **nếu** kịch bản đánh giá gọi bước đó thì nó gọi đúng bản cài đặt — nó **không** bảo đảm kịch bản có gọi hay không. Nguyên nhân gốc không nằm ở chỗ hàm được đặt ở đâu mà ở chỗ **kịch bản đánh giá dựng lại đường xử lý thay vì gọi nó**: `measure_crops` và `_run_pipeline` lần lượt liệt kê các bước — nhận dạng, chuẩn hoá, cứu dòng trên — nên mỗi bậc mới thêm vào `ALPRPipeline._process_one` đều **mặc định rơi ra ngoài phép đo**, im lặng, cho tới khi có ai đó tình cờ đối chiếu hai đoạn mã.

Phát biểu lại bài học ở dạng đúng hơn:

> Một đường đo **liệt kê lại** các bước của hệ thống sẽ lệch khỏi hệ thống ở đúng thời điểm hệ thống thay đổi — tức đúng thời điểm phép đo cần chính xác nhất. Chia sẻ mã ở mức *hàm* không đủ; chỉ **gọi thẳng cùng một điểm vào** mới đủ. Biện pháp "viết thành hàm dùng chung" đã được tuân thủ và vẫn thất bại, nên nó là bằng chứng thực nghiệm cho luận điểm này chứ không phải phản ví dụ.

Lần này, ngoài việc nối bậc thang vào cả hai nhánh đo, hai chốt chặn cụ thể đã được thêm: kịch bản đánh giá ghi thẳng **trạng thái các công tắc** vào tệp kết quả, và ghi **số biển mà từng bậc cứu được** (`recovery_contribution`). Một bậc không được gọi giờ sẽ hiện ra dưới dạng số 0 có nhãn, thay vì biến mất không dấu vết. Biện pháp triệt để — cho harness đầu-cuối gọi thẳng `ALPRPipeline.process` — vẫn là **việc bỏ ngỏ**, ghi ở mục 6.10.

### 6.5.7. Bậc thang thử-lại cho biển nghiêng/méo — chi phí, lợi ích và một quyết định tắt tính năng

Bước cứu dòng trên (6.5.6) nhắm vào biển hai dòng bị mất một dòng. Còn một chế độ thất bại khác: **biển bị nghiêng trong ảnh hoặc bị méo phối cảnh**, khiến tỉ lệ khung hình lệch đủ để bộ phân loại bố cục xếp nhầm, hoặc khiến ký tự dính vào nhau. Bậc thang thử-lại xử lý nhóm này bằng ba biến thể, thử theo thứ tự giả thuyết rẻ trước: **nắn hình trong mặt phẳng**, **giãn dọc chống méo phối cảnh**, và **siêu phân giải** cho vùng cắt quá nhỏ.

**Điểm mấu chốt của thiết kế là cổng kích hoạt, không phải các biến thể.** Hình học đã từng được đo ở dạng *luôn bật* trước mọi lần đọc, và kết quả là **mất**: 42 lần đọc hợp lệ tụt xuống 40, vì một hình chữ nhật khớp sai trên vùng cắt nhỏ và mờ sẽ cắt cụt ký tự của một biển vốn đang đọc tốt. Chuyển đúng hình học ấy ra **sau một cổng "lần đọc đầu đã thất bại"** đảo ngược hoàn toàn kinh tế học của nó: đường đi của biển đọc đúng **không bị chạm tới về mặt cấu trúc**, mọi ca cứu được đều là lãi ròng, và một biến thể đọc tệ hơn sẽ bị tiêu chí hợp lệ loại bỏ. Đây là cùng một hợp đồng chống thoái lui với bước cứu dòng trên.

#### Chi phí và lợi ích, đo trên cùng dữ liệu

Độ chính xác đo trên 2.801 biển có nhãn chuỗi; độ trễ đo trên 100 ảnh hiện trường của tập test v3, máy rảnh:

<!-- {{T6.5i}} chi phi - loi ich cua tung bac trong bac thang thu-lai -->

**Bảng 6.17.** Chi phí và lợi ích của từng bậc trong bậc thang thử-lại

| Cấu hình | 1 − CER (A4) | A6 | Biển được cứu | p95 (ms) | p99 (ms) |
|---|---:|---:|---:|---:|---:|
| Tắt hẳn bậc thang | 0,9416 | 0,7437 | 0 | **866,3** | 1.101,1 |
| **Nắn hình / giãn dọc** *(cấu hình giao hàng)* | **0,9454** | **0,7512** | **34** | **1.110,4** | 1.349,0 |
| Thêm siêu phân giải | 0,9454 | 0,7512 | 34 | **1.428,7** | **2.730,4** |

> Nguồn: `docs/reports/27-ocr-accuracy-with-ladder.json` và ba lượt `ai.evaluation.benchmark_system` bóc tách qua `ALPR_RECTIFY_ENABLED` / `ALPR_SR_RETRY_ENABLED`. Phân tích đầy đủ: `docs/reports/27-retry-ladder-cost-benefit.md`.

**Bậc thang gần như miễn phí ở trường hợp thường và rất đắt ở đuôi.** Trung vị chỉ tăng 3,7% (405,8 ms) trong khi p99 tăng 148% — đúng bản chất của một cơ chế chỉ chạy khi lần đọc đầu thất bại: đại đa số ảnh không bao giờ chạm tới nó, còn ảnh nào chạm tới thì trả giá bằng nhiều lượt gọi OCR liên tiếp.

**Nắn hình / giãn dọc: giữ.** Mua 34 biển (+0,75 điểm A6, +0,38 điểm A4) với giá +244 ms ở p95. Đây là mức giá chấp nhận được cho một cơ chế không thể làm hỏng kết quả đang đúng.

**Siêu phân giải: tắt mặc định.** Mua **0 biển** với giá **+319 ms ở p95 và +1.381 ms ở p99**, và một mình nó đẩy NFR-P1 vượt ngưỡng tối thiểu 1.500 ms.

#### Vì sao số 0 của siêu phân giải không phải bằng chứng nó vô dụng

Điểm này phải nói rõ, nếu không bảng trên bị đọc sai theo hướng mạnh hơn dữ liệu cho phép.

Cổng của bậc siêu phân giải chỉ mở cho vùng cắt có cạnh dài **≤ 200 px** — vì thiếu điểm ảnh mới là chế độ thất bại mà nó nhắm tới. Đo trên 120 mẫu lấy ngẫu nhiên của tập có nhãn chuỗi, cạnh dài sau bước khôi phục tỉ lệ khung hình có **giá trị nhỏ nhất là 565 px và trung vị 868 px**: **0/120 mẫu lọt cổng**. Tập ngữ liệu này **không thể kích hoạt** bậc siêu phân giải, nên nó **không thể đo** bậc siêu phân giải. Số 0 trong bảng là **số 0 cấu trúc**, không phải kết quả âm.

Suy ra hai hệ quả. Thứ nhất, toàn bộ 34 biển mà bậc thang cứu được đều là công của nắn hình / giãn dọc. Thứ hai, quyết định tắt siêu phân giải **không** dựa trên "đã đo và thấy vô dụng" mà trên một lập luận khác, yếu hơn nhưng trung thực hơn:

> Chi phí đã đo được và lớn; lợi ích **chưa ai đo được** trên bất kỳ tập đại diện nào; trong khi NFR-P1 là yêu cầu mức *Must* và riêng bậc này làm nó vượt ngưỡng. Một lợi ích chưa định lượng không đủ để biện minh cho một vi phạm đã định lượng.

Bằng chứng duy nhất hiện có cho bậc siêu phân giải vẫn là **một vùng cắt demo được chọn tay trong bốn ca thử**. Mã, kiểm thử, công tắc và báo cáo của nó **giữ nguyên**; đặt `ALPR_SR_RETRY_ENABLED=true` là bật lại. Muốn đo cho tử tế cần một tập **vùng cắt nhỏ do chính bộ phát hiện sinh ra, có nhãn chuỗi** — đồ án không có, và đó là hạng mục bỏ ngỏ được ghi ở mục 6.11 chứ không phải một điểm bị lờ đi.

---

## 6.6. Đánh giá hiệu năng

> Mọi số trong mục 6.6 phải đọc cùng bảng T6.2a: **Intel Raptor Lake 14 nhân / 20 luồng, Windows 11, CPU-only, kích thước lô = 1**.

### 6.6.1. Độ trễ đầu-cuối (NFR-P1)

<!-- {{T6.6a}} do tre dau-cuoi mot anh, doi chieu NFR-P1 -->

**Bảng 6.18.** Độ trễ đầu-cuối một ảnh, đối chiếu NFR-P1

| Chỉ số | Ngưỡng tối thiểu | Mục tiêu | **Trước bậc thang thử-lại (20/07)** | **Cấu hình giao hàng (28/07)** | Kết quả |
|---|---:|---:|---:|---:|:---:|
| Độ trễ E2E p50 (ms) | — | — | 414,67 | 405,77 | n/a |
| **Độ trễ E2E p95 (ms)** | **≤ 1500** | **≤ 800** | **731,15** | **1.143,10** | **🟡 đạt ngưỡng tối thiểu** |
| Độ trễ E2E p99 (ms) | — | — | 947,83 | 1.420,07 | n/a |
| Độ trễ trung bình (ms) | — | — | 400,74 | 447,38 | n/a |
| Số ảnh đo | — | — | 100 | 100 | n/a |
| Bội số so với ngưỡng tối thiểu | — | — | 0,49× | **0,76×** | n/a |
| Bội số so với mục tiêu | — | — | 0,91× | **1,43×** | n/a |

*Hình 6.7.* Phân bố độ trễ đầu-cuối — biểu đồ tần suất kèm vạch đánh dấu p50/p95/p99 và hai ngưỡng chỉ tiêu.
Đường dẫn hình: `docs/reports/figures/07-latency-distribution.png` *(đã có, cần vẽ lại cho `best.pt`)*

> Số biển trung bình mỗi ảnh: 1,33, cùng 100 ảnh test v3, cùng máy rảnh (CPU idle ~5%, không có tiến trình huấn luyện song song). **Hai cột đo hai phiên bản hệ thống, không phải hai phương pháp đo**: cột trái là trạng thái ngày 20/07, trước khi bậc thang thử-lại được thêm vào (đo client-side qua HTTP, `07-benchmark-p1-resolved.json`); cột phải là cấu hình giao hàng ngày 28/07 (đo in-process bằng `benchmark_system.py`, `05-results.json` → T6.6a). Chênh lệch phương pháp giữa hai cách đo là **~7%** — đã kiểm chứng ngày 20/07 khi cả hai cùng chạy trên một hệ thống (731,15 so với 780,36 ms) — nên nó **không** giải thích được mức tăng ở đây.

**NFR-P1 đạt ngưỡng tối thiểu nhưng không đạt mục tiêu: p95 = 1.143,10 ms, dưới sàn 1.500 ms nhưng vượt mục tiêu 800 ms 1,43 lần.** Đây là một **thoái lui có chủ ý và đã định lượng**, không phải một con số xấu đi ngoài tầm kiểm soát, nên phải trình bày kèm nguyên nhân.

**Nguyên nhân là bậc thang thử-lại (6.5.7), và cái giá ấy đổi lấy độ chính xác.** Bằng chứng nằm ở phép bóc tách: tắt hẳn bậc thang đưa p95 về **866,3 ms**, tức toàn bộ +277 ms là của nó. Nhưng bậc thang chỉ chạy **sau khi lần đọc đầu thất bại**, nên nó không hề chạm vào trường hợp thường — **trung vị thậm chí giảm nhẹ** (414,67 → 405,77 ms). Chi phí dồn hết vào đuôi phân phối, đúng nơi tập trung những ảnh mà hệ thống phải làm việc nhiều lần mới đọc được.

**Chỉ số nào nên dùng để đánh giá trải nghiệm ở đây là một câu hỏi thật.** Với một hệ thống mà 95% ảnh xong dưới 1,15 giây và một nửa xong dưới 0,41 giây, p50 mô tả trải nghiệm điển hình còn p95 mô tả trường hợp xấu. Chỉ tiêu NFR-P1 phát biểu theo p95 nên kết luận chính thức phải theo p95 — và theo đó, **hệ thống đạt sàn chứ không đạt mục tiêu**.

**Một quyết định đã được đưa ra để bảo vệ chỉ tiêu này.** Ở lượt đo đầu với cả ba biến thể bật, p95 là **1.514,26 ms** — **vượt cả ngưỡng tối thiểu**. Phép bóc tách chỉ ra bậc siêu phân giải chiếm hơn nửa chi phí đó mà không mua được biển nào đo được, nên nó bị **tắt mặc định** (6.5.7), đưa p95 về 1.143,10 ms. Nói cách khác, con số trong bảng là kết quả của một đánh đổi được cân bằng bằng số đo, không phải một giá trị tình cờ.

**Giải quyết mâu thuẫn với con số cũ 5.857 ms.** Báo cáo Phase 7 trước đây ghi p95 = 5.857,19 ms và kết luận NFR-P1 "không đạt" — chênh **7,5 lần** so với con số hiện tại. Phép đo cũ đã bị **bác bỏ** sau khi truy nguyên: (1) nó **bị nhiễu do tranh chấp CPU** — tệp đo gốc `07-benchmark-data.json` ghi rõ có một tiến trình `ai.training.train` chiếm 793% CPU chạy song song lúc đo, đẩy đuôi phân phối lên; chính báo cáo cũ khi tính lại trên 80 mẫu ít nhiễu đã ra ~3.283 ms; (2) nó đo trên **checkpoint epoch 7**, không phải `best.pt` chính thức; (3) checkpoint đó có **lỗi crop** khiến PaddleOCR chạy cả khối phát hiện văn bản trên ảnh lớn (~1.322 ms/ảnh), thổi phồng phần OCR. Đo lại trên máy rảnh với `best.pt`: p95 chỉ còn 731 ms. Giả thuyết "cold-start / oneDNN chưa tắt" **không** phải nguyên nhân — server chạy với `enable_mkldnn=false` và có warmup ngay khi khởi động (cold-start đo được chỉ 176 ms p95). Cũng cần loại một giả thuyết khác: baseline-416-v1 **không** vốn chậm — đo client-side nó ra 763,75 ms p95, gần như y hệt `best.pt`; chênh lệch 7,5 lần của con số cũ **không** đến từ mô hình.

### 6.6.2. Phân rã ngân sách độ trễ theo từng bước

Đây là mục có giá trị chẩn đoán cao nhất của phần hiệu năng. Nó đối chiếu **ước lượng ngân sách lập ở Phase 0** — trước khi viết bất kỳ dòng mã suy luận nào — với **số đo thật**.

<!-- {{T6.6b}} phan ra ngan sach do tre theo tung buoc, doi chieu uoc luong Phase 0 -->

**Bảng 6.19.** Phân rã ngân sách độ trễ theo từng bước

| Bước xử lý | Ước lượng Phase 0 (ms) | **Đo thật (ms)** | Chênh lệch (lần) | % tổng thời gian |
|---|---:|---:|---:|---:|
| Giải mã ảnh + tiền xử lý | 50 | **2,83** | 0,06 | **1,7%** |
| Suy luận YOLO11n @ 640px (CPU) | 150 | **57,27** | 0,38 | **34,0%** |
| Cắt + tiền xử lý vùng biển số | 30 | **0,00** | 0,00 | **0,0%** |
| **PaddleOCR (mỗi biển)** | **120** | **108,28** | 0,90 | **64,3%** |
| Hậu xử lý regex + kiểm tra hợp lệ | 5 | **0,03** | 0,01 | **0,0%** |
| Ghi CSDL + lưu ảnh | 50 | — | — | — |
| **Tổng (một biển số)** | **405** | **168,41** | 0,47 | **100%** |

*Hình 6.8.* Biểu đồ cột chồng phân rã ngân sách độ trễ: ước lượng Phase 0 so với số đo thật.
Đường dẫn hình: `docs/reports/figures/07-latency-budget.png` *(đã có, cần vẽ lại)*

> Mẫu số: 40 ảnh, trung bình 1,57 biển mỗi ảnh, đo trên `best.pt`. Bước "ghi CSDL + lưu ảnh" giữ `—` vì `benchmark_system` đo pipeline suy luận thuần, không đi qua tầng API. Cột chênh lệch ở dòng tổng vì vậy so với ước lượng **cùng phạm vi** (đã trừ bước ghi CSDL), không so với 405 ms tròn.

**Ba phát hiện chi phối toàn bộ phần bàn luận về hiệu năng:**

**Phát hiện 1 — ước lượng Phase 0 sát bất ngờ ở tổng, nhưng lệch ở phân bổ.** Tổng ngân sách suy luận thuần đo thật là **168,41 ms/biển**, nhỏ hơn cả ước lượng Phase 0 (405 ms gồm cả ghi CSDL, hay ~355 ms nếu trừ ghi CSDL). Nghĩa là ước lượng ban đầu **không** sai một bậc độ lớn như con số nhiễu 5.857 ms từng khiến người ta tin — pipeline thật nhanh hơn dự trù. Đây là hệ quả trực tiếp của việc bác bỏ phép đo cũ ở mục 6.6.1.

**Phát hiện 2 — nút thắt là PaddleOCR, nhưng KHÔNG áp đảo như báo cáo cũ.** PaddleOCR chiếm **64,3%** tổng thời gian (108,28 ms/biển); bộ phát hiện chiếm **34,0%** (57,27 ms). Con số này **thay thế** con số cũ "OCR 93,3% / detect 6,5%" — vốn đo trên một hệ thống đang có lỗi crop khiến PaddleOCR đọc ảnh quá lớn (~1.322 ms/ảnh). Sau khi sửa crop, OCR còn ~108,28 ms/biển. OCR **vẫn** là bước tốn kém nhất, nhưng ở tỉ trọng 64,3% chứ không phải 93,3%. Nguyên nhân OCR đắt vẫn đúng: PaddleOCR là một **pipeline nhiều giai đoạn** (phát hiện văn bản → phân loại hướng → nhận dạng) thiết kế cho ảnh tài liệu tổng quát, nên hệ thống đang trả chi phí cho năng lực mà vùng biển đã cắt không cần.

**Phát hiện 3 — hệ quả cho chiến lược tối ưu đổi hẳn so với kết luận cũ.** Với breakdown thật, định luật Amdahl cho trần cải thiện khác trước: tối ưu bộ phát hiện (34,0%) giờ **có ý nghĩa thực sự** — nếu ONNX Runtime hoặc OpenVINO tăng tốc detector 2–3×, tổng E2E có thể giảm quãng 15–23%, khác hẳn kết luận cũ "chỉ giảm tối đa 6,7%". Còn tối ưu OCR (64,3%) vẫn là hướng có dư địa lớn nhất. Điểm mấu chốt: NFR-P1 mới chỉ đạt sàn chứ chưa đạt mục tiêu (p95 = 1.143,10 ms so với mục tiêu 800 ms) và NFR-P2 còn trượt cả sàn (2,379 FPS, sàn 3), tối ưu hiệu năng vẫn nằm trên đường tới chỉ tiêu chứ không chỉ là *dư địa cải thiện thêm* — và cả hai khối (detect + OCR) đều đáng tấn công, không chỉ riêng OCR như báo cáo cũ nhận định.

### 6.6.3. So sánh backend suy luận: PyTorch, ONNX Runtime và OpenVINO

Thí nghiệm này được thực hiện dù kết luận đã đoán trước được từ mục 6.6.2, vì hai lý do: nó **kiểm chứng** lập luận Amdahl bằng số liệu thay vì để nó ở dạng suy luận, và nó cung cấp số liệu về mức tăng tốc thật của từng backend trên CPU Intel — thông tin có giá trị độc lập [18]<!-- ultralytics_2026_openvinoexport --> [117]<!-- onnxruntime_2025_threading -->.

<!-- {{T6.6c}} so sanh backend suy luan cho bo phat hien -->

**Bảng 6.20.** So sánh backend suy luận cho bộ phát hiện

| Backend | Độ trễ **chỉ bộ phát hiện** p50 (ms) | p95 (ms) | Tăng tốc so với PyTorch | Độ trễ **E2E** p95 (ms) | Cải thiện E2E (%) | mAP@0.5 sau khi xuất |
|---|---:|---:|---:|---:|---:|---:|
| PyTorch (mốc so sánh) | *(chưa đo)* | *(chưa đo)* | 1,00× | *(chưa đo)* | 0% | *(chưa đo)* |
| ONNX Runtime | *(chưa đo)* | *(chưa đo)* | *(chưa đo)* | *(chưa đo)* | *(chưa đo)* | *(chưa đo)* |
| OpenVINO | *(chưa đo)* | *(chưa đo)* | *(chưa đo)* | *(chưa đo)* | *(chưa đo)* | *(chưa đo)* |

> **Bảng T6.6c chưa đo** — phép so sánh backend (`benchmark_cpu` với `--backends pytorch onnx openvino`) chưa chạy. Cột "mAP@0.5 sau khi xuất" tồn tại để kiểm tra việc chuyển đổi định dạng **không làm suy giảm độ chính xác**; nếu có suy giảm, mức tăng tốc phải được đánh giá như một đánh đổi. Khi đo xong sẽ điền từ `docs/reports/07-benchmark-optimized.json`.

**Kết luận định hướng của mục này, cập nhật theo breakdown thật ở 6.6.2** (34,0% detect / 64,3% OCR, khác con số cũ 6,7% / 93,3%):

> **Tối ưu backend của bộ phát hiện GIỜ có ý nghĩa, nhưng chưa đủ một mình.** Bộ phát hiện chiếm 34,0% tổng thời gian, nên theo định luật Amdahl, tăng tốc detector 2–3× (mức thường thấy của ONNX Runtime / OpenVINO trên CPU Intel) có thể kéo E2E xuống quãng 15–23% — không còn bị chặn ở 6,7% như báo cáo cũ lầm tưởng. Và vì NFR-P1 **chỉ đạt sàn** (p95 = 1.143,10 ms, mục tiêu 800 ms) còn NFR-P2 thì **trượt sàn**, đây không phải dư địa cải thiện thêm mà là đường dẫn tới chỉ tiêu. Muốn giảm mạnh hơn nữa thì khối OCR (64,3%) vẫn là mục tiêu lớn nhất.

Bốn hướng tấn công khối OCR, xếp theo chi phí thực hiện tăng dần — được nêu ở đây như phần chẩn đoán của Chương 6, và triển khai chi tiết thuộc về Chương 7:

1. **Tắt các giai đoạn không cần thiết của pipeline PaddleOCR.** Vùng biển số đã được cắt sẵn nên giai đoạn phát hiện văn bản gần như thừa; giai đoạn phân loại hướng cũng có thể bỏ nếu vùng cắt đã được nắn.
2. **Bật MKL-DNN và chỉnh số luồng CPU** cho backend PaddlePaddle.
3. **Xuất mô hình nhận dạng sang ONNX Runtime** để bỏ hoàn toàn phụ thuộc runtime PaddlePaddle.
4. **Thay bằng một mô hình nhận dạng chuyên cho biển số**, huấn luyện riêng trên tập ký tự hẹp (10 chữ số + tập chữ cái hợp lệ) thay vì dùng mô hình đa ngữ tổng quát. Đây là hướng có tiềm năng cải thiện lớn nhất nhưng cũng tốn công nhất, và đã được ghi vào phạm vi mở rộng của đề tài.

### 6.6.4. Chế độ webcam (tầng API) và xử lý video (NFR-P2, NFR-P3)

> Từ 2026-07-20, trang Webcam đã được gỡ khỏi giao diện web (thu gọn phạm vi — mục 4.1.3b); chế độ thời gian thực chỉ còn ở tầng API. Phép đo NFR-P2 vì vậy được thực hiện bằng kịch bản gọi trực tiếp `POST /api/detect/frame`, không qua giao diện.

<!-- {{T6.6d}} hieu nang che do webcam va xu ly video -->

**Bảng 6.21.** Hiệu năng chế độ webcam và xử lý video

| Chỉ số | Mã NFR | Ngưỡng tối thiểu | Mục tiêu | **Đo được** | Kết quả |
|---|:---:|---:|---:|---:|:---:|
| Tốc độ khung hình webcam hiệu dụng (FPS) | NFR-P2 | ≥ 3 | ≥ 5 | **2,379** | ❌ không đạt |
| Thời gian đo liên tục (giây) | — | 60 | 60 | **60,52** | n/a |
| Khung hình camera chào / gửi đi / bỏ | — | — | — | **1.815 / 144 / 1.671** | n/a |
| Số yêu cầu lỗi trong 60 giây | — | 0 | 0 | **0** | ✅ |
| Độ trễ mỗi khung, p50 / p95 (ms) | — | — | — | **180,05 / 1.247,70** | n/a |
| Tốc độ xử lý video (× thời gian thực) | NFR-P3 | ≥ 0,15× | ≥ 0,3× | **0,746×** | ✅ đạt |
| Thời gian xử lý video 14,25 giây (giây) | NFR-P3 | ≤ 95 | ≤ 47,5 | **19,1** | ✅ đạt |
| Bước nhảy khung hình đã dùng (`vid_stride`) | — | — | — | **5** | n/a |

**NFR-P2 không đạt, và nguyên nhân không phải tốc độ trung bình mà là *đuôi phân bố*.** Trung vị mỗi khung chỉ **180 ms** — tương ứng 5,6 FPS, tức vượt mục tiêu. Nhưng p95 là **1.247,7 ms**, và giao diện thời gian thực dùng **hàng đợi một khe**: chỉ một yêu cầu được bay tại một thời điểm, khung hình sinh ra trong lúc chờ bị bỏ thay vì xếp hàng. Ở kỷ luật đó, thông lượng bị chi phối bởi những lần chậm nhất chứ không phải lần trung bình, nên 2,379 FPS thấp hơn hẳn con số suy ra từ trung vị. Đuôi ấy chính là bậc thang thử-lại (mục 6.5.7) — nó chỉ chạy sau khi đọc hỏng, nên trên ảnh khó nó cộng thêm gần một giây.

Đây là một **đánh đổi đã biết chứ không phải bất ngờ**: cùng cơ chế đó mua thêm 34 biển đọc đúng và đẩy NFR-P1 từ ✅ xuống 🟡 (mục 6.6.1). NFR-P2 là chỗ thứ hai phải trả giá.

**Định nghĩa đã dùng, nêu rõ để không phóng đại.** "FPS hiệu dụng" ở đây là **số khung hình được nhận dạng xong mỗi giây**, không phải số khung hiển thị: 144 khung xử lý trong 60,52 giây. Camera ảo chào 1.815 khung ở 30 FPS và 1.671 khung bị bỏ — con số bỏ này được báo cáo chứ không giấu, vì nếu chỉ công bố "144 khung, 0 lỗi" thì người đọc sẽ hiểu nhầm là hệ thống theo kịp nguồn.

**Con số này là cận trên.** Phép đo chạy qua HTTP loopback với ảnh đã có sẵn trên đĩa, nên nó **không** tính thời gian camera thu hình, mã hoá JPEG trong trình duyệt và vẽ canvas — ba khoản mà một triển khai thật đều phải trả thêm.

Dự đoán trước đó trong bản thảo này là **~1,4 FPS**, suy từ độ trễ p95 0,73 giây và giả định xử lý tuần tự từng khung. Số đo thực **2,379 FPS** cao hơn dự đoán nhưng vẫn dưới sàn 3 FPS, nên **kết luận của dự đoán đúng dù con số thì lệch** — ghi lại ở đây để thấy giới hạn của việc suy diễn từ độ trễ thay vì đo.

### 6.6.5. Chịu tải, bộ nhớ và độ tin cậy (NFR-SC1, NFR-P4…P7, NFR-R4)

<!-- {{T6.6e}} chiu tai, bo nho, do tin cay -->

**Bảng 6.22.** Chịu tải, bộ nhớ và độ tin cậy

| Chỉ số | Mã NFR | Ngưỡng tối thiểu | Mục tiêu | **Đo được** | Kết quả |
|---|:---:|---:|---:|---:|:---:|
| Thời gian nạp mô hình (giây) | NFR-P4 | ≤ 30 | ≤ 15 | **6,41** *(baseline)* | ✅ đạt |
| Thời gian khởi động đến khi `/health` sẵn sàng (giây) | NFR-P4b | ≤ 30 | ≤ 15 | **8,36** *(baseline)* | ✅ đạt |
| Overhead của API, p95 (ms) | NFR-P5 | ≤ 100 | ≤ 50 | **19,01** *(baseline)* | ✅ đạt |
| Truy vấn lịch sử 10.000 bản ghi, p95 (ms) | NFR-P6 | ≤ 1000 | ≤ 500 | **18,71** *(baseline)* | ✅ đạt |
| RSS pipeline (GB) | NFR-P7a | ≤ 4 | ≤ 2 | **0,759** | ✅ đạt |
| RSS máy chủ backend (GB) | NFR-P7b | ≤ 4 | ≤ 2 | **0,806** | ✅ đạt |
| Số yêu cầu đồng thời xử lý ổn định | NFR-SC1 | ≥ 5 | ≥ 5 | **10** | ✅ đạt |
| Tỉ lệ thành công khi chạy tải liên tục (soak 15 phút) | NFR-R4 | ≥ 99% | ≥ 99% | **100,0% (2.028 yêu cầu)** | ✅ đạt |
| Tăng RSS sau soak 15 phút (GB) | — | không có | không có | **+0,094** *(0,726 → 0,820)* | ✅ không rò rỉ |
| Cơ sở dữ liệu sống sót qua khởi động lại | NFR-R5 | 100% | 100% | **0/9.031 bản ghi mất** | ✅ đạt |

*Hình 6.9.* Đường cong thông lượng và tỉ lệ lỗi theo mức đồng thời 1 / 2 / 5 / 10.
Đường dẫn hình: `docs/reports/figures/07-concurrency.png` *(đã có, cần vẽ lại)*

**Mọi chỉ tiêu hiệu năng *ngoài đường xử lý ảnh* đều đạt với biên rất rộng**: overhead API 19,01 ms so với mục tiêu 50 ms, truy vấn lịch sử 18,71 ms so với mục tiêu 500 ms (nhanh hơn ~27 lần), soak 15 phút thành công 100% trên 2.028 yêu cầu, RSS phẳng ở 0,8 GB, và chịu 10 yêu cầu đồng thời so với ngưỡng 5. **Cơ sở dữ liệu cũng sống sót nguyên vẹn qua khởi động lại**: 9.031 bản ghi trước và sau, không mất bản nào.

**Nhưng hai chỉ tiêu trên chính đường xử lý ảnh thì không.** NFR-P1 chỉ đạt ngưỡng tối thiểu (p95 = 1.143 ms, mục tiêu 800 ms) và **NFR-P2 trượt cả sàn** (2,379 FPS, sàn 3). Cả hai cùng một nguyên nhân — đuôi độ trễ do bậc thang thử-lại — và cùng một đánh đổi có chủ ý: 34 biển đọc thêm.

Kết luận vì vậy phải nói làm hai vế. **Kiến trúc phần mềm không còn là vấn đề** — tầng API, tầng dữ liệu, bộ nhớ, độ ổn định đều dư biên và không đáng đầu tư thêm. **Nhưng *độ trễ suy luận* thì vẫn là vấn đề**, và nó ràng buộc trực tiếp năng lực thời gian thực. Hướng đi tiếp có hai nhánh tách bạch: nâng *độ chính xác* OCR biển hai dòng (mục 6.5), và cắt *đuôi độ trễ* — chẳng hạn đặt trần thời gian cho bậc thang thử-lại, hoặc chỉ chạy nó ở chế độ ảnh tĩnh chứ không ở chế độ thời gian thực.

---

### 6.6.6. Bỏ bước phát hiện chữ của PaddleOCR: một quyết định suýt sai

Mục 5.4 để ngỏ một câu hỏi: chế độ **chỉ nhận dạng** cho model fine-tune thêm
12,46 điểm A6 và rẻ hơn ~290 ms mỗi ảnh. Vì sao không bật?

Vì ngữ liệu chứng minh nó **không có thẩm quyền trả lời câu hỏi đó**.

<!-- {{T6.6f}} bo buoc phat hien chu: hai ngu lieu, hai ket luan nguoc nhau -->

**Bảng 6.23.** Bỏ bước phát hiện chữ — hai ngữ liệu, hai kết luận ngược nhau

| Cấu hình | A6 trên 2.801 ảnh **cắt sẵn** | Biển đọc đúng trên bộ demo **ảnh toàn cảnh** |
|---|---:|---:|
| Model gốc, det + rec — *bản giao hàng* | 0,7512 | **17 / 22** |
| Model gốc, chỉ rec | 0,7508 | 13 / 22 |
| Model fine-tune, det + rec | 0,6762 | 14 / 22 |
| Model fine-tune, chỉ rec | **0,8758** | 15 / 22 |

Nguồn: `docs/reports/29-reconly-ablation.json`,
`docs/reports/31-demo-ab-reconly.json`.

**Cột trái và cột phải cho hai thứ tự ngược nhau, và cột phải mới là cột đúng.**
Mọi ảnh trong ngữ liệu 2.801 mẫu là bản xuất Roboflow **đã cắt khít quanh biển**
— một bộ dò chữ đặt vào đó thì không còn gì để khoanh, nên cột trái đọc ra như
thể bước phát hiện là thừa. Nhưng vùng cắt mà hệ thống thật sự phải đọc do
**YOLO sinh ra từ ảnh toàn cảnh**, và chúng lỏng hơn nhiều: dính cản xe, kính
chắn gió, nền đường. Ở đó bước phát hiện làm đúng việc của nó, và bỏ nó đi thì
bộ nhận dạng đọc luôn phần nền thành ký tự — `TCA7A22104`, `5KB274184` trên
`nhieu-bien-2.png`.

**Một khác biệt nữa, độc lập với độ chính xác và nghiêm trọng hơn.** Chế độ
chỉ-nhận-dạng **không có khả năng trả về chuỗi rỗng**: trên 1.606 khung biển do
bộ phát hiện sinh ra, nó trả chuỗi ở **cả 1.606**, trong khi bản giao hàng trả
rỗng ở **173 khung**. Khi bộ phát hiện bắt nhầm một tấm biển quảng cáo hay một
mảng cản xe, bản giao hàng **im lặng** còn chế độ chỉ-rec **bịa ra một biển số**.
Với một hệ thống ghi vào cơ sở dữ liệu, bịa nguy hiểm hơn im lặng.

**Quyết định: giữ bước phát hiện chữ.** Công tắc `ALPR_OCR_SKIP_DETECTION` được
cài đặt, mặc định **tắt**, và được ghim bằng kiểm thử. Nó không bị xoá vì hiệu
ứng "chỉ-rec giúp model fine-tune, hại model gốc" là thật và có cơ chế rõ ràng
— chỉ là 22 biển thì quá ít để đổi cấu hình đem giao.

**Điều kiện để xét lại:** một tập **ảnh toàn cảnh có nhãn chuỗi biển số** — cùng
một lỗ hổng dữ liệu chặn cả câu hỏi này lẫn nhãn "không đại diện" của NFR-A7.

**Lỗ hổng đó đã được lấp ngày 02/08/2026** ([34-scene-level-a7.md](../reports/34-scene-level-a7.md)):
**608 khung biển** trên ảnh hiện trường được gán nhãn chuỗi. Bắt buộc lấy mẫu
**phân tầng** vì 1.232/1.606 khung thuộc nhóm bất đồng — dùng riêng nhóm đó sẽ cho
con số bi quan sai lệch. Tầng đồng thuận được **đếm hết** (372/374), nên sai số chỉ
còn đến từ tầng bất đồng.

| Cấu hình | Tầng dễ *(n=372)* | Tầng khó *(n=236)* | **A7** | KTC 95% |
|---|---:|---:|---:|:---:|
| **Gốc + det+rec** — *bản giao hàng* | 96,8% | 44,1% | **56,3%** | [52,0 ; 60,7] |
| Gốc + chỉ rec | 96,8% | 19,9% | 37,8% | [34,3 ; 41,3] |
| Fine-tune + det+rec | 96,8% | 30,9% | 46,3% | [42,2 ; 50,3] |
| Fine-tune + chỉ rec | **94,1%** | 44,5% | 56,0% | [51,7 ; 60,4] |

**Phải phát biểu cho đúng mức.** Bản giao hàng đứng đầu, nhưng chênh với ứng viên
gần nhất chỉ **0,3 điểm** và hai khoảng tin cậy **chồng gần như hoàn toàn** — về
thống kê, hai cấu hình đó **không phân biệt được** trên tập này. Kết luận đúng
không phải *"bản giao hàng chính xác hơn"* mà là **"không có bằng chứng để đổi"**.
Hai cấu hình còn lại thì thua rõ, nằm ngoài khoảng tin cậy.

Cột "tầng dễ" hé lộ điều mà phép đo trên ngữ liệu ảnh cắt sẵn không thấy được:
fine-tune + chỉ rec là cấu hình **duy nhất kém đi ở ca dễ** — 94,1% so với 96,8%,
tức **10 biển đọc hỏng thêm** trên 372 khung đã đếm hết, ở đúng nhóm mà mọi cấu
hình khác đều đọc được. Nó thắng ở ca khó nhưng đánh mất ca dễ, và đó là lý do lợi
thế 12,46 điểm đo trên ngữ liệu cắt sẵn không sống sót ở đường chạy thật.

> **Ghi lại vì đây là lần thứ tư cùng một họ lỗi, và là lần đầu chặn được trước
> khi vào bản giao.** Ba lần trước — siêu phân giải, công cụ đo bỏ sót bậc thang
> thử-lại, val acc của fine-tune — đều là lỗi đã mắc rồi mới phát hiện. Lần này
> phép đo nói "lãi 12,46 điểm" và chỉ vì bộ demo được chạy lại **trước** khi đổi
> mặc định mới lộ ra rằng nó làm hệ thống **tệ đi 4 biển**. Quy tắc rút ra:
> *không đổi cấu hình mặc định dựa trên một phép đo mà đầu vào của nó khác đầu
> vào thật.*

---

## 6.7. Đối chiếu toàn bộ chỉ tiêu phi chức năng

Bảng dưới là bảng tổng hợp trình bày khi bảo vệ. Nó liệt kê **đầy đủ mọi mã NFR** đã đặt ra ở Phase 0, không lọc bỏ mã nào — kể cả những mã không đạt.

**Ký hiệu:** ✅ đạt mục tiêu · 🟡 chỉ đạt ngưỡng tối thiểu · ❌ không đạt · ⬜ chưa đo · ➖ không áp dụng cho chương này

<!-- {{T6.7}} doi chieu toan bo chi tieu NFR -->

**Bảng 6.24.** Đối chiếu toàn bộ chỉ tiêu phi chức năng

| Mã | Chỉ tiêu | Ngưỡng tối thiểu | Mục tiêu | **Đo được** | Kết quả | Mục |
|:---:|---|---:|---:|---:|:---:|:---:|
| **NFR-P — Hiệu năng** | | | | | | |
| P1 | Độ trễ E2E một ảnh, p95 | ≤ 1500 ms | ≤ 800 ms | **1.143,10 ms** *(p50 = 405,77 ms)* | 🟡 | 6.6.1 |
| P2 | Tốc độ khung hình webcam (tầng API) | ≥ 3 FPS | ≥ 5 FPS | **2,379 FPS** *(144/1.815 khung, 0 lỗi)* | ❌ | 6.6.4 |
| P3 | Tốc độ xử lý video | ≥ 0,15× | ≥ 0,3× | **0,746×** *(0,546 s/khung phân tích)* | ✅ | 6.6.4 |
| P4 | Thời gian nạp mô hình | ≤ 30 s | ≤ 15 s | **6,41 s** | ✅ | 6.6.5 |
| P4b | Khởi động đến khi `/health` sẵn sàng | ≤ 30 s | ≤ 15 s | **8,36 s** | ✅ | 6.6.5 |
| P5 | Overhead API, p95 | ≤ 100 ms | ≤ 50 ms | **19,01 ms** | ✅ | 6.6.5 |
| P6 | Truy vấn lịch sử 10.000 bản ghi, p95 | ≤ 1000 ms | ≤ 500 ms | **18,71 ms** | ✅ | 6.6.5 |
| P7a | RSS pipeline | ≤ 4 GB | ≤ 2 GB | **0,759 GB** | ✅ | 6.6.5 |
| P7b | RSS máy chủ backend | ≤ 4 GB | ≤ 2 GB | **0,806 GB** | ✅ | 6.6.5 |
| **NFR-A — Độ chính xác** | | | | | | |
| A1 | mAP@0.5 của bộ phát hiện | ≥ 0,85 | ≥ 0,90 | **0,9829** | ✅ | 6.4.1 |
| A2 | mAP@0.5:0.95 của bộ phát hiện | ≥ 0,55 | ≥ 0,65 | **0,7834** | ✅ | 6.4.1 |
| A3 | Precision / Recall phát hiện | ≥ 0,88 / 0,85 | ≥ 0,92 / 0,90 | **0,9837 / 0,9714** | ✅ | 6.4.1 |
| A4 | Độ chính xác OCR mức ký tự (1 − CER) | ≥ 0,92 | ≥ 0,95 | **0,9454** | 🟡 | 6.5.1 |
| A5 | Chuỗi đầy đủ **trước** hậu xử lý | ≥ 0,80 | ≥ 0,85 | **0,6373** | ❌ | 6.5.2 |
| A6 | Chuỗi đầy đủ **sau** hậu xử lý | ≥ 0,85 | ≥ 0,90 | **0,7512** | ❌ | 6.5.2 |
| **A6 − A5** | **Đóng góp của khối hậu xử lý** | — | — | **+11,39 điểm** | ✅ | **6.5.2** |
| A7 | Độ chính xác E2E toàn trình | ≥ 0,82 | ≥ 0,88 | **0,563** *(ảnh toàn cảnh; KTC 95% [0,520 ; 0,607])* | ❌ | 6.5.5 |
| A8 | Tách theo layout một dòng / hai dòng | báo cáo tách bạch | — | detection: **2,09 điểm**; OCR (A6): **25,45 điểm** | 🟡 | 6.4.3, 6.5.3 |
| A9 | Tách theo điều kiện ảnh | báo cáo nếu có nhãn | — | — | ⬜ | 6.7.1 |
| **NFR-R — Độ tin cậy** | | | | | | |
| R1 | Không sập với đầu vào hỏng / độc hại | 100% | 100% | — | ⬜ | 6.6.5 |
| R2 | Ảnh không có biển ⇒ kết quả rỗng hợp lệ | HTTP 200, danh sách rỗng | — | — | ⬜ | 6.6.5 |
| R3 | Tác vụ video lỗi không để lại rác | nguyên tử | — | — | ⬜ | 6.6.5 |
| R4 | Tỉ lệ thành công khi chạy liên tục | ≥ 99% | ≥ 99% | **100% (2.028 yêu cầu, 15 phút)** | ✅ | 6.6.5 |
| R5 | CSDL sống sót qua khởi động lại | 100% | 100% | **0/9.031 bản ghi mất** | ✅ | 6.6.5 |
| **NFR-SC — Khả năng mở rộng** | | | | | | |
| SC1 | Số yêu cầu đồng thời xử lý ổn định | ≥ 5 | ≥ 5 | **10** | ✅ | 6.6.5 |
| SC2 | Số bản ghi không làm suy giảm hiệu năng | ≥ 100.000 | ≥ 100.000 | — | ⬜ | 6.6.5 |
| SC3 | Tác vụ video chạy nền, không chặn | bắt buộc | — | — | ⬜ | 6.6.5 |
| **NFR-M — Khả năng bảo trì** | | | | | | |
| M1 | Mã AI tách biệt hoàn toàn khỏi mã API | 0 vi phạm | 0 vi phạm | — | ⬜ | 6.7.2 |
| M2 | Độ bao phủ test tầng nghiệp vụ | ≥ 70% | ≥ 70% | **87,7%** (2026-07-20) | ✅ | 6.7.2 |
| M3 | Type hint và docstring cho hàm public | 100% | 100% | — | ⬜ | 6.7.2 |
| M4 | Không hard-code đường dẫn | 0 vi phạm | 0 vi phạm | — | ⬜ | 6.7.2 |
| M5 | Thay được bộ OCR mà không sửa mã API | ràng buộc bằng interface | — | — | ⬜ | 6.7.2 |
| M6 | Tuân thủ lint và định dạng tự động | sạch | sạch | **black 96/96 sạch; ruff còn 83 `E501`** | ⚠️ | 6.7.2 |
| **NFR-S — An toàn** | | | | | | |
| S1 | Kiểm tra tệp bằng magic bytes | chặn được tệp giả mạo | — | — | ⬜ | 6.7.2 |
| S2 | Chống path traversal | 100% | — | — | ⬜ | 6.7.2 |
| S3 | Giới hạn kích thước tệp, thực thi ở server | HTTP 413 | — | — | ⬜ | 6.7.2 |
| S4 | CORS chỉ cho phép origin đã khai báo | không dùng `*` | — | — | ⬜ | 6.7.2 |
| S5 | Không ghi dữ liệu nhạy cảm vào log | 0 vi phạm | — | — | ⬜ | 6.7.2 |
| S6 | Truy vấn CSDL tham số hoá qua ORM | 0 nối chuỗi SQL | — | — | ⬜ | 6.7.2 |
| **NFR-C — Tương thích** | | | | | | |
| C1 | Chạy được trên Windows / Linux / macOS qua Docker | `docker compose up` | — | — | ⬜ | 6.7.2 |
| C2 | Hoạt động không cần GPU | mặc định | — | **có** | ✅ | 6.2.3 |
| C3 | Hỗ trợ Chrome, Edge, Firefox | thủ công | — | — | ⬜ | 6.7.2 |
| C4 | Cài đặt từ đầu bằng README | ≤ 15 phút | — | — | ⬜ | 6.7.2 |
| **NFR-U — Khả dụng** | | | | | | |
| U1 | Lượt nhận dạng đầu tiên không cần đọc tài liệu | ≤ 3 click | — | — | ⬜ | 6.7.2 |
| U2 | Phản hồi trực quan cho thao tác > 500 ms | 100% | — | — | ⬜ | 6.7.2 |
| U3 | Thông báo lỗi tiếng Việt, nêu cách khắc phục | 100% | — | — | ⬜ | 6.7.2 |
| U4 | Dùng được từ độ phân giải 1366×768 | không vỡ layout | — | — | ⬜ | 6.7.2 |
| U5 | Tương phản màu đạt WCAG AA | ≥ 4,5:1 | — | — | ⬜ | 6.7.2 |

### 6.7.1. Ghi chú về NFR-A9 — đánh giá theo điều kiện ảnh

NFR-A9 được phát biểu **có điều kiện** ngay từ Phase 0: *"báo cáo độ chính xác theo điều kiện ảnh (ban ngày / ban đêm / nghiêng / mờ), **nếu bộ dữ liệu có nhãn phù hợp**"*. Bộ dữ liệu v3, hợp nhất từ bảy bộ dữ liệu công khai (còn sáu nguồn nguyên tố sau khử trùng lặp), **không có nhãn điều kiện chụp thống nhất**. Do đó:

- **Không** gán nhãn điều kiện ảnh bằng suy đoán (ví dụ dùng độ sáng trung bình để suy ra "ban đêm"), vì một nhãn suy đoán sẽ tạo ra một bảng kết quả trông có vẻ chặt chẽ nhưng thực chất đo một đại lượng không xác định.
- Trạng thái đúng để báo cáo là: **NFR-A9 không đánh giá được vì thiếu nhãn**, kèm ghi nhận đây là hạn chế của bộ dữ liệu.
- Phương án thực hiện được nếu có thời gian: gán nhãn thủ công cho một tập con nhỏ (khoảng 200–300 ảnh) đủ để làm khảo sát định hướng, và **công bố rõ rằng đó là tập con được gán nhãn thủ công**, không phải toàn tập test.

### 6.7.2. Kết quả kiểm thử phần mềm

Nhóm NFR-M, S, C, U được kiểm chứng bằng bộ kiểm thử tự động chứ không bằng đo hiệu năng.

| Hạng mục | **Đo được** | Chỉ tiêu | Kết quả |
|---|---:|---:|:---:|
| Tổng số test thu thập | **1.001** | — | n/a |
| Số test pass | **1.000** | — | ✅ |
| Số test xfail (dự kiến thất bại) | **1** | — | n/a |
| Số test fail | **0** | 0 | ✅ |
| Số test skip | **0** | — | n/a |
| Độ bao phủ **tầng nghiệp vụ** (đo 2026-07-20) | **87,7%** | ≥ 70% (NFR-M2) | ✅ |
| Độ bao phủ **tầng nghiệp vụ** (đo ở Phase 7, trước đó) | **88,1%** | ≥ 70% (NFR-M2) | ✅ |
| Độ bao phủ **toàn kho mã** (đo ở Phase 7) | **42,0%** | — | n/a |

> **Nguồn và mốc đo.** Bốn dòng đầu lấy từ lần chạy `backend/.venv/Scripts/python.exe -m pytest -q` tại gốc kho ngày 2026-08-02 (**1.001 thu thập / 1.000 pass / 1 `xfail` / 0 fail / 0 skip**). Độ bao phủ 87,7% là mốc đo 2026-07-20 ghi trong `docs/reports/13-refactor-result.json`, nơi số test khi ấy là 882/881 — hai con số đến từ hai lượt chạy khác nhau, nêu tách bạch để người tái lập không bị lệch. Cặp số **862/861** trong các bản tài liệu trước là kết quả một lần chạy cũ hơn và đã bị thay thế. Về bao phủ: **87,7%** là số đo mới nhất cùng ngày 2026-07-20 (`docs/reports/13-refactor-result.json`, 2.931 câu lệnh / 317 bỏ sót); **88,1%** và **42,0%** là số đo ở Phase 7 (`docs/reports/07-testing-report.md`). Cả hai đều là số đo thật ở hai thời điểm khác nhau — giữ nguyên cả hai kèm mốc thời gian thay vì chọn một con số rồi xoá con số kia.

Chênh lệch giữa 88,1% và 42,0% (cùng một mốc đo Phase 7) là chênh lệch **có chủ ý và cần giải thích**, không phải dấu hiệu kiểm thử thiếu sót. Chỉ tiêu NFR-M2 đặt ngưỡng cho **tầng nghiệp vụ** — nơi chứa logic có thể sai một cách âm thầm: luật hậu xử lý biển số, xác thực đầu vào, thao tác cơ sở dữ liệu. Con số 42,0% toàn kho bao gồm cả mã script tiện ích, mã sinh biểu đồ, mã tải bộ dữ liệu — những phần mà chi phí viết test cao còn rủi ro sai thầm lặng thấp. Việc công bố **cả hai con số** thay vì chỉ con số cao hơn là điều kiện để bảng này trung thực; công bố riêng 88,1% mà không nói mẫu số là một dạng chọn lọc số liệu có lợi.

Test `xfail` duy nhất phải được nêu tên và giải thích khi công bố: nó đánh dấu một hành vi đã biết là chưa đúng và được ghi nhận công khai, chứ không phải một test bị vô hiệu hoá để bảng kết quả sạch. Cụ thể, đó là `tests/integration/test_api_detection.py::TestErrorBodies::test_a_failed_image_detection_records_the_failed_job`: `DetectionService._fail_job` gọi `db.rollback()` trước khi ghi bản ghi thất bại, trong khi `_create_job` mới chỉ `flush`, nên dòng job bị huỷ — một lần tải ảnh thất bại hiện **không để lại dòng nào** trong bảng `DetectionJob`.

---

## 6.8. Phân tích lỗi

Bảng chỉ số cho biết hệ thống sai **bao nhiêu**; mục này cho biết hệ thống sai **như thế nào**. Đây là phần cung cấp nguyên liệu trực tiếp cho hướng phát triển ở Chương 7.

### 6.8.1. Phân loại các ca sai

Sáu loại lỗi dưới đây là **đầy đủ và loại trừ lẫn nhau** — mỗi ca sai được gán đúng một loại, theo thứ tự ưu tiên từ trên xuống.

| Mã | Loại lỗi | Định nghĩa | Tầng chịu trách nhiệm |
|:---:|---|---|---|
| **E1** | **Bỏ sót biển** | Ảnh có biển nhưng bộ phát hiện không trả về hộp nào khớp | Phát hiện |
| **E2** | **Phát hiện nhầm** | Bộ phát hiện trả về hộp ở vùng không phải biển số | Phát hiện |
| **E3** | **Nhầm ký tự** | Chuỗi đúng độ dài nhưng có ký tự bị đọc sai (thay thế) | OCR |
| **E4** | **Thiếu ký tự** | Chuỗi ngắn hơn nhãn thật (xoá) | OCR / cắt vùng |
| **E5** | **Thừa ký tự** | Chuỗi dài hơn nhãn thật (chèn) | OCR / cắt vùng |
| **E6** | **Sai thứ tự** | Đủ ký tự nhưng sắp sai thứ tự — hầu như chỉ xảy ra ở biển hai dòng, do ghép nhầm chiều hai dòng | Hậu xử lý |

Loại E6 đáng được chú ý riêng: nó **chỉ tồn tại vì bài toán có biển hai dòng**, và nó là loại lỗi mà khối hậu xử lý có thể sửa triệt để nếu logic ghép dòng đúng. Nếu bảng T6.8 cho thấy E6 chiếm tỉ trọng đáng kể, đó là một hướng cải thiện chi phí thấp, hiệu quả cao.

### 6.8.2. Tần suất từng loại lỗi

<!-- {{T6.8}} tan suat cac loai loi -->

**Bảng 6.25.** Tần suất từng loại lỗi

| Mã | Loại lỗi | Số ca | Tỉ lệ trong tổng số ca sai | Tỉ lệ trong toàn tập đánh giá | Biển một dòng | Biển hai dòng |
|:---:|---|---:|---:|---:|---:|---:|
| E1 | Bỏ sót biển | 335 | — | — | — | — |
| E2 | Phát hiện nhầm | *(chưa đo)* | — | — | — | — |
| E3 | Nhầm ký tự | 445 | 63,85% | 15,89% | 17 | 428 |
| E4 | Thiếu ký tự | 73 | 10,47% | 2,61% | 0 | 73 |
| E5 | Thừa ký tự | 18 | 2,58% | 0,64% | 5 | 13 |
| E6 | Sai thứ tự | 0 | 0,00% | 0,00% | 0 | 0 |
| | **Tổng số ca sai** | **697** | 100% | 24,88% | — | — |
| | **Tổng số ca đánh giá (mẫu số)** | **2.801** | n/a | 100% | — | — |

> **Mẫu số của E1 khác mẫu số của E3–E6.** E1 (bỏ sót biển) lấy từ lượt đo E2E của bảng T6.5e trên 2.801 mẫu; tỉ lệ E1 trên mẫu số riêng của nó là **11,96%**. Vì thế hai cột tỉ lệ **cố ý để trống ở dòng E1** — gộp chung một mẫu số sẽ cho con số vô nghĩa. E2 (phát hiện nhầm) để *(chưa đo)*: số dương tính giả nằm ở T6.4a và cũng không cùng mẫu số với E3–E6.
>
> **Hai loại lỗi ngoài khung E1–E6:** `empty_read` = 10 (OCR trả chuỗi rỗng) và `mixed` = 151 (một biển vừa thiếu vừa thừa vừa nhầm ký tự). Hai loại này có trong cài đặt nhưng không có mã E riêng ở bảng phân loại tại mục 6.8.1; chúng được ghi nhận ở đây để tổng loại lỗi khớp với thực tế, tránh ảo giác "các mã E cộng lại đủ 100% số ca sai" (thực chất E3+E4+E5+E6 = 536, phần còn lại tới 697 là 151 ca `mixed` và 10 ca `empty_read`).
>
> **So với lượt đo 20/07, phân bố lỗi đã đổi hình rõ rệt** — tổng ca sai giảm từ 916 xuống 697. Hai nhóm giảm mạnh nhất là `mixed` (277 → 151) và E5 thừa ký tự (95 → 18), tức các chuỗi **hỏng về cấu trúc** đã được xử lý phần lớn. Ngược lại E3 nhầm ký tự **tăng** (399 → 445): đây là hiện tượng **phân loại lại**, không phải thoái lui — một biển trước kia cho ra chuỗi sai độ dài (rơi vào `mixed` hoặc E4) nay cho ra chuỗi đúng độ dài nhưng sai một ký tự, nên chuyển sang E3. Tổng thể vẫn giảm 219 ca sai. Kết luận thực tiễn: phần lỗi còn lại đã dồn về **nhầm và hụt ký tự đơn lẻ trên biển hai dòng**, đúng nhóm mà việc huấn luyện lại bộ nhận dạng nhắm tới.
>
> **Nguồn của bảng này.** Số ca lấy từ khoá `by_line_count.*.error_classes` của `docs/reports/05-results.json` (T6.8) — cùng lượt đo 28/07 với mục 6.5, tức **đã có** cả bước cứu dòng trên lẫn bậc thang thử-lại.

**Cấu trúc lỗi xác nhận chẩn đoán ở 5.6.3.** Hai cột cuối cho phép kiểm chứng chéo với bảng T6.5c, và chúng cho thấy phân bố loại lỗi của hai layout **khác nhau về chất, không chỉ về lượng**: gần như **toàn bộ** lỗi ký tự dồn về biển hai dòng — E3 (nhầm ký tự) 428/445 là hai dòng, E4 (thiếu ký tự) **73/73 — tuyệt đối, không một ca nào thuộc biển một dòng**, E5 (thừa ký tự) 13/18 là hai dòng. Biển một dòng chỉ sinh 22 ca trên cả ba loại. Điều này khớp chính xác với chênh lệch 25,45 điểm A6 ở mục 6.5.3: biển hai dòng không chỉ khó hơn *một chút* mà là **nguồn gần như duy nhất** của lỗi nhận dạng. Về E6 (sai thứ tự): số ca = **0** trên toàn tập — logic ghép hai dòng của khối hậu xử lý hoạt động đúng, không có ca nào ghép nhầm chiều; đây là một điểm mạnh nhỏ nhưng thật của bộ luật.

**Bước cứu dòng trên để lại dấu vết đo được ngay trong bảng này.** So với lượt đo trước khi có bước cứu (mục 6.5.6), **E4 giảm mạnh nhất: 217 → 134 ca**, trong khi E3 tăng 376 → 399 và `mixed` tăng 266 → 277. Diễn giải: bước cứu nhắm đúng chế độ thất bại "mất hẳn dòng trên", nên nó rút bớt quần thể E4; những ca được cứu một phần — lấy lại được dòng trên nhưng vẫn còn ký tự đọc sai — **chuyển sang** E3 hoặc `mixed` thay vì biến mất. Đây là kiểm chứng chéo độc lập cho cơ chế đã mô tả ở 6.5.6: nếu bước cứu chỉ đơn thuần "làm số đẹp lên" thì phân bố loại lỗi sẽ co lại đồng đều, chứ không dịch chuyển có hướng như thế này. Dù vậy, E4 (**73 ca**) và mức $D$ = **1.272** ký tự bị xoá ở T6.5a vẫn cùng trỏ về một chế độ thất bại còn lại: OCR đọc **hụt** ký tự trên biển hai dòng — hướng khắc phục nằm ở tầng nhận dạng, không ở hậu xử lý.

### 6.8.3. Các ca điển hình

*Hình 6.10.* Ảnh minh hoạ loại E1 — biển bị bỏ sót. Ghi rõ: kích thước box tương đối, điều kiện ảnh quan sát được.
Đường dẫn hình: `docs/reports/figures/05-error-e1-missed.png` *(chưa sinh)*

*Hình 6.11.* Ảnh minh hoạ loại E3 — nhầm ký tự. Hiển thị vùng cắt, chuỗi thô, chuỗi sau hậu xử lý, nhãn thật.
Đường dẫn hình: `docs/reports/figures/05-error-e3-substitution.png` *(chưa sinh)*

*Hình 6.12.* Ảnh minh hoạ loại E6 — sai thứ tự trên biển hai dòng.
Đường dẫn hình: `docs/reports/figures/05-error-e6-order.png` *(chưa sinh)*

*Hình 6.13.* Ca mà **hậu xử lý làm hỏng** một chuỗi vốn đã đúng — nếu tồn tại ca như vậy, **bắt buộc phải trưng ra**, vì nó là bằng chứng phản biện đối với đóng góp được công bố ở mục 6.5.2.

Hình 6.13 không phải để cân bằng hình thức. Một chương đánh giá chỉ trưng ra các ca mà hệ thống làm tốt là một chương đã tự loại bỏ khả năng bị kiểm chứng.

---

## 6.9. Bàn luận

### 6.9.1. Những gì đạt được

Bốn nhóm kết quả dưới đây đều trỏ về ô đã điền số thật trong các bảng T6.4a đến T6.7.

1. **Bộ phát hiện đạt toàn bộ chỉ tiêu, với biên rộng.** Theo T6.4a: mAP@0.5 = 0,9829 (mục tiêu 0,90), mAP@0.5:0.95 = 0,7834 (mục tiêu 0,65), Precision = 0,9837, Recall = 0,9714 — cả bốn đều vượt *mục tiêu* chứ không chỉ ngưỡng tối thiểu. Đọc kèm điều kiện ở 6.4.1: đây là bài toán một lớp nên mAP cao là bình thường, và chỉ số quyết định là mAP@0.5:0.95 = 0,7834 — vẫn vượt mục tiêu 0,65 một biên lớn. Chênh lệch giữa hai layout ở tầng phát hiện chỉ 2,09 điểm (T6.4b), xác nhận việc *định vị box* không phụ thuộc layout. Điểm yếu duy nhất được phơi bày trung thực ở T6.4c: dải đối tượng "rất nhỏ" (dưới 0,5% diện tích) có mAP@0.5 chỉ 0,8553 — hệ quả đo được của tiêu chí Q6 không đạt.

2. **Khối hậu xử lý đóng góp thuần dương, không rủi ro.** Theo T6.5b: A6 − A5 = **+11,39 điểm**, sửa đúng 319 biển, làm hỏng 0 biển trên 2.801 mẫu. Đây là câu trả lời định lượng cho RQ3 — một đóng góp hiếm khi được đo tách bạch trong tài liệu ALPR — kèm bằng chứng rằng bộ luật đủ bảo thủ để không tự tạo lỗi mới. Đóng góp ấy **dồn gần như trọn vẹn vào biển hai dòng** (+13,97 điểm, so với +1,23 điểm ở biển một dòng), tức đúng nơi tầng nhận dạng yếu nhất. Hai bậc cứu chữa chạy sau chuẩn hoá cũng được cô lập bằng đo A/B với **0 ca hồi quy**: bước **cứu dòng trên** cung cấp câu trả lời cuối cho **209 biển** (6.5.6), **bậc thang thử-lại** cho **34 biển** (6.5.7). Đóng góp tổng vẫn không đủ đưa A6 tới ngưỡng vì phần lỗi còn lại đã dịch sang dạng đọc hụt ký tự, nơi luật không với tới (6.5.2).

3. **Biển một dòng về cơ bản đã giải xong.** Tách theo layout (T6.5c) cho thấy biển một dòng đạt 1 − CER = 0,9925 và A6 = 0,9541 (vượt mục tiêu 0,90). Toàn bộ việc "OCR không đạt" ở con số tổng là do quần thể biển hai dòng (79,8% tập) kéo xuống — một phát hiện có định vị rõ ràng, không phải một thất bại mơ hồ.

4. **Hiệu năng và kiến trúc phần mềm đều trong ngưỡng.** NFR-P1 đạt sàn nhưng không đạt mục tiêu (p95 = 1.143 ms, sàn 1.500 ms, mục tiêu 800 ms — 6.6.1), và mức vượt mục tiêu là **cái giá đã định lượng** của bậc thang thử-lại: tắt nó đưa p95 về 866 ms, còn trung vị thì không đổi (405,77 ms). Mọi chỉ tiêu ngoài đường suy luận đạt với biên rộng (overhead API 19,01 ms, truy vấn lịch sử 18,71 ms — nhanh hơn mục tiêu ~27 lần); soak 15 phút thành công 100% trên 2.028 yêu cầu, không rò rỉ bộ nhớ; chịu 10 yêu cầu đồng thời so với ngưỡng 5. Độ bao phủ test tầng nghiệp vụ 87,7% (đo 2026-07-20); **1.000/1.001 test pass, 1 `xfail`, 0 fail** (chạy 2026-08-02).

5. **Bản thân tính trung thực của quy trình đánh giá là một kết quả.** Mục 6.3.3 (phát hiện lập luận vòng tròn trong kiểm chứng rò rỉ), mục 6.6.1 (bác bỏ con số độ trễ cũ 5.857 ms bị nhiễm tải), mục 3.6.1 (thừa nhận ba biến cùng đổi, giải thích vì sao mAP thấp hơn baseline lại đáng tin hơn), và mục 6.5.6 (phát hiện **ba lần** đường đo chạy một pipeline ngắn hơn pipeline sản phẩm — lần đầu nhờ dấu hiệu "chỉ số bao hàm đứng yên", lần thứ ba nhờ một mức chênh đúng bằng 0,0000 trên bốn chữ số thập phân) là những đóng góp phương pháp luận có giá trị dù không phải con số cao. Lần thứ ba đặc biệt đáng ghi: nó chứng minh biện pháp phòng ngừa đặt ra sau lần thứ hai **đã được tuân thủ đầy đủ mà vẫn thất bại**, vì nó nhắm sai nguyên nhân gốc.

### 6.9.2. Những gì KHÔNG đạt được, và vì sao

Mục này trình bày các chỉ tiêu **không đạt**, không giấu — nhưng trước hết phải nói rõ hai chỉ tiêu đã **chuyển trạng thái** sau lượt đo lại ngày 28/07, vì trình bày số cũ sẽ mô tả sai hệ thống hiện tại:

- **NFR-A4 chuyển từ ❌ sang 🟡**: 0,8848 → **0,9454**, vượt ngưỡng tối thiểu 0,92 (6.5.1).
- **NFR-P1 chuyển từ ✅ sang 🟡**: 731 ms → **1.143 ms**, vẫn dưới sàn 1.500 ms nhưng vượt mục tiêu 800 ms (6.6.1). Đây là **thoái lui có chủ ý**: cái giá của bậc thang thử-lại, đổi lấy 34 biển đọc được thêm.

**Ba chỉ tiêu OCR còn lại không đạt, và nguyên nhân chung là biển hai dòng.**

- **NFR-A5 (chuỗi trước hậu xử lý) = 0,6373**, thiếu 16,27 điểm so với ngưỡng 0,80 (T6.5b).
- **NFR-A6 (chuỗi sau hậu xử lý) = 0,7512**, thiếu 9,88 điểm so với ngưỡng 0,85 (T6.5b).
- **NFR-A7 (E2E toàn trình) = 0,5552**, thiếu 26,48 điểm so với ngưỡng 0,82 (T6.5e).

> Ba con số trên là kết quả **sau** khi đã áp cả hai bậc cứu chữa (6.5.6, 6.5.7) và các bản sửa đọc biển hai dòng. So với lượt đo 20/07, A6 tăng **7,82 điểm** — mức cải thiện lớn nhất của cả đồ án ở tầng nhận dạng, và đạt được **không tốn một giây GPU nào**. Nhưng **không chỉ tiêu nào trong ba chỉ tiêu này chuyển sang đạt**: khoảng thiếu còn lại vẫn tính bằng hàng chục điểm ở A5 và A7, gần mười điểm ở A6. Phải phát biểu đúng như vậy — đây là một cải thiện đo được, không phải một lời giải.

Nguyên nhân đã được xác định **định lượng và có định vị**, không phỏng đoán. Tách theo layout (T6.5c) cho thấy trên biển **một dòng** hệ thống đạt hoặc vượt ngưỡng (1 − CER = 0,9925; A6 = 0,9541); toàn bộ khoảng thiếu nằm ở biển **hai dòng** (1 − CER = 0,9344; A6 = 0,6996). Vì biển hai dòng chiếm **79,8%** tập có nhãn chuỗi (phản ánh tỉ lệ xe máy cao trong giao thông Việt Nam), con số tổng bị quần thể khó này chi phối. Đây là **đặc tính có cấu trúc của bài toán** — khoảng cách 25,45 điểm A6 giữa hai layout cùng bậc độ lớn với mốc 48,6 điểm mà Laroca và cộng sự đo trên RodoSol-ALPR Brazil (6.5.3) — chứ không phải một lỗi cài đặt sửa nhanh được.

**Cấu trúc phần lỗi còn lại chỉ thẳng sang hướng khắc phục.** Sau các bản sửa, ký tự **chèn thừa** gần như biến mất (903 → 107 ca, giảm 88%) trong khi ký tự **bị xoá** vẫn ở 1.272 và nay chiếm 56,8% toàn bộ lỗi (T6.5a). Nghĩa là phần lỗi đã dịch từ "đọc hỏng cả chuỗi" sang "đọc hụt ký tự". Hậu xử lý theo luật mạnh ở việc sửa ký tự nhầm nhưng **về nguyên tắc không thể phục hồi một ký tự chưa từng được đọc ra** — đó là lý do +11,39 điểm vẫn không đủ. Hướng khắc phục bắt buộc nằm ở **tầng nhận dạng**: huấn luyện lại bộ nhận dạng trên vùng cắt biển số Việt Nam, chứ không ở tầng hậu xử lý và cũng không ở tầng hình học (đã xử lý và đo tách bạch ở 6.5.7).

**Một cảnh báo hiệu lực về A7.** A7 = 0,5552 bị hạ thêm bởi giới hạn của giao thức đo (đo trên ảnh crop ngoài phân bố huấn luyện của bộ phát hiện) nên phải đọc như **cận dưới bi quan**, không phải ước lượng điểm. Lập luận và số liệu đầy đủ: **mục 6.5.5**.

**Các chỉ tiêu chưa đo được và lý do:**

| Mã | Lý do chưa đo | Có khắc phục được trong khuôn khổ đồ án không? |
|:---:|---|---|
| NFR-A9 | **Bộ dữ liệu không có nhãn điều kiện ảnh** | Một phần — gán nhãn thủ công cho tập con |
| T6.6c — so sánh backend | Chưa chạy `benchmark_cpu` | **Có** |
| T6.5b — phân rã theo nhóm luật | Chưa có cơ chế bật/tắt luật trong `plate_rules.py` | **Có** — cần viết mã |
| Thí nghiệm cô lập biến E1–E3 (mục 3.6.2) | Chi phí ≈ 33 giờ CPU, vượt ngân sách thời gian | **Không** — chuyển sang hướng phát triển |
| Benchmark engine OCR (PaddleOCR ↔ EasyOCR ↔ Tesseract) — hứa ở mục 3.3 | Chưa chạy. PaddleOCR PP-OCRv5_mobile được giữ nguyên làm engine duy nhất vì các lý do kỹ thuật ở mục 3.3 (nhẹ hơn EasyOCR gần 10 lần, mạnh trên ảnh xoay), **không phải vì đã chứng minh được nó chính xác hơn** | **Có** — cần chạy ma trận thí nghiệm ở mục 3.3 |
| So sánh YOLO26n làm đối chứng — hứa ở mục 2.7 | Chưa huấn luyện. Ngân sách CPU dồn hết cho lượt `best.pt` chính thức | **Có** — cần thêm một lượt huấn luyện |

Việc phân biệt "chưa đo vì chưa tới lượt" (phần lớn khắc phục được) với "không đo được vì thiếu điều kiện" (NFR-A9 thiếu nhãn, A7 thiếu tập hiện trường có nhãn chuỗi) là quan trọng: chỉ nhóm thứ hai mới là hạn chế thật của công trình.

### 6.9.3. Các mối đe doạ đến tính hợp lệ của kết quả

Mục này liệt kê các yếu tố có thể khiến kết luận của chương sai hoặc bị phóng đại. Nó được viết theo nguyên tắc: **nêu mối đe doạ, đánh giá mức nghiêm trọng, và nói rõ đã làm gì để giảm thiểu — kể cả khi biện pháp giảm thiểu là "không có".**

**(1) Rò rỉ dữ liệu tồn dư không khử được bằng băm tri giác.** *Mức nghiêm trọng: cao.* Như đã phân tích ở mục 6.3.3, phash chỉ bắt được tương đồng ở mức bố cục sáng-tối. Ngay ở mức bố cục, T6.3b cho thấy rò rỉ tồn dư **có thật, đo được**: ngay ngoài vùng bảo vệ của ngưỡng gộp (ngưỡng 10, cho 0 cặp theo định nghĩa), tại ngưỡng Hamming **12** vẫn còn **791 cặp** gần trùng train↔test, và tại ngưỡng 15 là 3.529 cặp — nghĩa là tập test **không** hoàn toàn tách khỏi tập train dù bước khử trùng lặp đã chạy đúng đặc tả. Nghiêm trọng hơn, hai ảnh của **cùng một chiếc xe** chụp ở góc khác nhau, hoặc hai khung hình cách nhau vài giây trong cùng một video, vẫn mang cùng một biển số nhưng có khoảng cách Hamming lớn — tức rò rỉ ở mức **ngữ nghĩa** mà không ngưỡng phash nào phát hiện được. *Biện pháp giảm thiểu đã áp dụng:* nâng ngưỡng gộp từ 5 lên 10 và đo rò rỉ ở nhiều ngưỡng cao hơn ngưỡng gộp để phơi bày phần tồn dư thay vì che nó. *Biện pháp triệt để chưa áp dụng được:* chia split theo nhóm biển số, bất khả thi vì thiếu nhãn chuỗi cho phần lớn corpus. **Hệ quả: mọi chỉ số ở mục 6.4 và 5.6 phải được coi là cận trên lạc quan.**

**(2) Tập test không xuyên bộ dữ liệu.** *Mức nghiêm trọng: cao.* Tập train và tập test đều được lấy từ **cùng sáu nguồn nguyên tố** đã hợp nhất. Điều này đo được năng lực tổng quát hoá *trong phân bố*, nhưng **không** đo được năng lực tổng quát hoá *xuyên phân bố* — vốn là thứ quyết định khi triển khai thực tế trên camera mới, địa điểm mới, điều kiện chiếu sáng mới. Tài liệu đã chỉ ra rằng độ chính xác ALPR **sụt giảm đáng kể** khi đánh giá xuyên bộ dữ liệu [7]<!-- laroca_2022_crossdataset -->. *Biện pháp giảm thiểu:* không có trong khuôn khổ đồ án. Cách đúng là giữ lại một nguồn hoàn toàn không dùng để huấn luyện làm tập test xuyên bộ; điều này chưa thực hiện và được ghi vào hướng phát triển.

**(3) Mẫu số nhỏ cho các chỉ số OCR.** *Mức nghiêm trọng: cao.* Phần lớn corpus 15.133 ảnh **chỉ có nhãn hộp giới hạn, không có nhãn chuỗi ký tự**. Do đó NFR-A4…A7 đo trên một tập con nhỏ hơn nhiều. Với mẫu số nhỏ, một chênh lệch vài điểm phần trăm có thể nằm trong dao động ngẫu nhiên. *Biện pháp giảm thiểu:* công bố mẫu số ở mọi bảng của mục 6.5, và **không** rút kết luận về chênh lệch nhỏ khi mẫu số dưới ngưỡng có ý nghĩa.

**(4) Đo trên một cấu hình phần cứng duy nhất.** *Mức nghiêm trọng: trung bình.* Mọi số hiệu năng đo trên một máy Intel Raptor Lake 14 nhân chạy Windows 11. Chúng **không ngoại suy** sang CPU khác kiến trúc, sang Linux, hay sang máy có số nhân khác — đặc biệt vì cả ONNX Runtime lẫn OpenVINO đều nhạy với cấu hình luồng và tập lệnh vector của CPU cụ thể [117]<!-- onnxruntime_2025_threading --> [120]<!-- openvino_2024_performancehints -->. *Biện pháp giảm thiểu:* công bố cấu hình đầy đủ ở bảng T6.2a và nhắc lại ràng buộc ở đầu mục 6.6.

**(5) Một lượt huấn luyện duy nhất, không ước lượng được phương sai.** *Mức nghiêm trọng: trung bình.* Với `seed=42` cố định và ngân sách khoảng 12 giờ CPU cho một lượt, không có nhiều lượt để tính khoảng tin cậy. Mọi chỉ số là kết quả của **một lần chạy**. *Biện pháp giảm thiểu:* cố định seed để ít nhất đảm bảo tái lập; không phát biểu bất kỳ so sánh nào dựa trên chênh lệch nhỏ hơn dao động giữa các seed dự kiến.

**(6) Bộ dữ liệu không đạt tiêu chí Q6 về tỉ lệ đối tượng nhỏ.** *Mức nghiêm trọng: trung bình.* 10,91% số hộp có diện tích dưới 0,5% diện tích ảnh, vượt ngưỡng cho phép 10%. *Biện pháp giảm thiểu:* báo cáo mAP **tách theo dải kích thước** ở mục 6.4.4 thay vì che sau một con số tổng.

**(7) Nhãn layout suy ra từ tỉ lệ khung hình khi bộ dữ liệu không khai báo.** *Mức nghiêm trọng: thấp đến trung bình.* Khi nguồn không có nhãn lớp phân biệt layout, layout được suy từ ngưỡng tỉ lệ khung hình 2,5. Ngưỡng này có cơ sở từ QCVN 08:2024/BCA, nhưng vẫn là một heuristic; biển bị chụp nghiêng mạnh có thể bị phân loại nhầm. *Biện pháp giảm thiểu:* ưu tiên nhãn lớp tường minh khi có, chỉ dùng heuristic khi không có, và ghi rõ trong chú thích bảng T6.4b tỉ lệ ô nào được suy bằng heuristic.

**(8) Ma trận nhầm lẫn ký tự phụ thuộc thuật toán căn chỉnh chuỗi.** *Mức nghiêm trọng: thấp.* Khi chuỗi dự đoán và chuỗi nhãn thật khác độ dài, việc gán cặp "ký tự thật ↔ ký tự đọc được" phụ thuộc vào cách căn chỉnh Levenshtein giải quyết các trường hợp có nhiều đường đi tối ưu. Với chuỗi có nhiều lỗi chèn/xoá, ma trận có thể ghi nhận các cặp không phản ánh nhầm lẫn thị giác thật. *Biện pháp giảm thiểu:* áp dụng ngưỡng tần suất tối thiểu trước khi đưa một cặp vào bảng luật (tiêu chí 1 ở mục 6.5.4).

---

## 6.10. Đối chiếu với các công trình đã công bố

Mục này đặt kết quả của đồ án cạnh các công trình đã khảo sát ở mục 2.7. Nó bắt
đầu bằng phần **không so được** chứ không bằng bảng số, vì đó mới là phần quyết
định cách đọc mọi con số phía sau.

### 6.10.1. Vì sao phần lớn các con số không so trực tiếp được

Ba khác biệt khiến việc đặt cạnh nhau hai con số độ chính xác của hai công trình
khác nhau là **không hợp lệ về phương pháp**, trừ khi cả ba đều trùng:

| Khác biệt | Vì sao nó phá vỡ phép so |
|---|---|
| **Bộ dữ liệu và quốc gia** | Biển Trung Quốc chủ yếu một dòng; biển Brazil có bố cục và phông chữ riêng; biển Việt Nam có tỷ lệ biển hai dòng cao. Cùng một mô hình cho ra con số rất khác trên ba tập này |
| **Định nghĩa chỉ số** | *"Accuracy"* trong các bài được khảo sát khi thì là mức ký tự, khi là mức chuỗi, khi là toàn trình có tính cả bước phát hiện. Ba định nghĩa này không cùng thang |
| **Điều kiện ảnh** | Camera tĩnh ở trạm thu phí khác hẳn ảnh chụp tự do; độ phân giải vùng biển chênh nhau nhiều lần |

Bằng chứng mạnh nhất cho luận điểm này đến từ chính lĩnh vực: Laroca và cộng sự
(2022) chạy **12 mô hình OCR trên 9 tập dữ liệu công khai** và ghi nhận độ chính
xác trung bình **sụt từ 82,4% xuống 45,2%** khi chuyển sang đánh giá xuyên tập
dữ liệu. Nói cách khác, **cùng một mô hình mất gần một nửa độ chính xác chỉ vì
đổi tập kiểm thử**. Một bảng xếp hạng ghép số từ nhiều bài khác nhau vì vậy đo
sự khác nhau của các tập dữ liệu nhiều hơn là đo sự khác nhau của các mô hình.

> ⚠️ **Hệ quả bắt buộc cho toàn mục này.** Mọi con số của công trình khác dẫn ở
> dưới đều **kèm tên bộ dữ liệu và quốc gia ngay trong bảng**, và không con số
> nào được dùng để kết luận rằng hệ thống của đồ án tốt hơn hay kém hơn. Chúng
> chỉ trả lời một câu hỏi hẹp hơn nhiều: *kết quả của đồ án có nằm trong vùng
> giá trị mà lĩnh vực đã ghi nhận hay không.*

### 6.10.2. Khối phát hiện — nằm trong vùng giá trị đã công bố

Đây là khối so sánh được nhiều nhất, vì chỉ số mAP@0.5 có định nghĩa thống nhất
và phần lớn công trình trong nước đều báo cáo nó.

| Công trình | Bộ dữ liệu · quốc gia | mAP@0.5 |
|---|---|---:|
| Batra và cộng sự (2022) | Google Open Images + biển Ấn Độ, 5.991 ảnh | 87,2% |
| Ba nghiên cứu dùng YOLO11 cho ALPR (mục 3.2) | các tập khác nhau | 90,6% – 99,5% |
| **Đồ án này** | **corpus Việt Nam hợp nhất, 1.514 ảnh test** | **98,29%** |

Kết quả của đồ án nằm trong vùng trên. Điều này **không** chứng minh mô hình tốt
hơn hay kém hơn công trình nào — mỗi dòng đo trên một tập khác nhau — nhưng nó
xác nhận khối phát hiện không có bất thường so với mặt bằng đã công bố.

Một điều kiện phải nêu kèm: tập test của đồ án **không xuyên bộ dữ liệu**. Theo
đúng phát hiện của Laroca ở trên, con số 98,29% vì vậy **lạc quan hơn** mức mà hệ
thống đạt được khi gặp nguồn ảnh hoàn toàn mới. Hạn chế này ghi ở mục 7.3.3.

### 6.10.3. Khối nhận dạng — chỗ đồ án thua, và thua ở đâu

| Công trình | Bộ dữ liệu · quốc gia | Chỉ số công bố | Giá trị |
|---|---|---|---:|
| Xu và cộng sự — RPnet (2018) | CCPD · Trung Quốc | accuracy end-to-end | 98,5% |
| Laroca và cộng sự (2021) | 8 tập từ 5 khu vực | recognition rate trung bình | 96,9% |
| Xu và cộng sự — LPTR-AFLNet (2025) | biển Trung Quốc | accuracy **riêng biển hai dòng** | 99,37% |
| Tran và Bui (2024) | biển Việt Nam, chạy trên Raspberry Pi 4 | accuracy | 95,68% |
| **Đồ án này** | **2.801 biển Việt Nam có nhãn chuỗi** | **chuỗi đầy đủ sau hậu xử lý (A6)** | **75,12%** |
| **Đồ án này** | *(cùng tập)* | **toàn trình từ ảnh gốc (A7)** | **55,52%** |

**Khoảng cách là thật và không được lấy khác biệt bộ dữ liệu ra biện minh cho
toàn bộ nó.** Nhưng chẩn đoán ở mục 6.5.3 định vị khoảng cách ấy rất rõ: chênh
lệch giữa biển một dòng và biển hai dòng ở khối OCR là **25,45 điểm**. Phần thiếu
hụt nằm gần như trọn ở biển hai dòng — loại biển chiếm tỷ lệ lớn ở Việt Nam
nhưng chiếm tỷ lệ nhỏ trong các bộ dữ liệu Trung Quốc mà phần lớn công trình ở
bảng trên dùng để đánh giá.

Hai dòng đáng đọc kỹ nhất trong bảng là **LPTR-AFLNet (99,37% riêng biển hai
dòng)** và **Tran–Bui (95,68% trên biển Việt Nam)**. Cả hai cho thấy vùng giá trị
này là **đạt được**, tức khoảng cách của đồ án không phải giới hạn của bài toán
mà là giới hạn của lựa chọn kỹ thuật: đồ án dùng một engine OCR **đa ngữ tổng
quát chưa tinh chỉnh**, trong khi cả hai công trình kia dùng mô hình huấn luyện
riêng cho biển số. Đây chính là hướng phát triển được xếp ưu tiên cao nhất ở mục
7.4.1, và mục 5.4 đã đo thử một bước theo hướng đó.

### 6.10.4. Ba điều đồ án báo cáo mà khảo sát không tìm thấy tương đương

Khảo sát ở mục 2.7.4 xác định sáu khoảng trống. Ba trong số đó liên quan trực
tiếp tới cách **báo cáo** kết quả, và đây là chỗ đồ án đóng góp được:

| Khoảng trống | Đồ án báo cáo |
|---|---|
| Chưa có công trình Việt Nam nào tách riêng độ chính xác biển một dòng và hai dòng trên cùng hệ thống | Bảng 6.11 — tách bạch, chênh **25,45 điểm** |
| Hầu hết công trình trong nước chỉ báo cáo mAP của khâu phát hiện, không báo cáo độ chính xác toàn trình mức chuỗi | Báo cáo cả hai: mAP 98,29% **và** A7 = 55,52% |
| Số liệu hiệu năng thường công bố không kèm phần cứng | Mọi số hiệu năng kèm model CPU, số luồng, kích thước ảnh (mục 6.2.1) |

Điều đáng nói là **con số thứ hai kém hơn hẳn con số thứ nhất**, và đó chính là
lý do khoảng trống này tồn tại: báo cáo toàn trình thì phải công bố cả phần
hỏng. Một hệ thống chỉ công bố mAP của khâu phát hiện luôn trông tốt hơn thực tế
mà người dùng gặp.

Ngoài ba mục trên, đồ án còn đo được **đóng góp thuần của khối hậu xử lý theo
luật** — **+11,39 điểm**, sửa đúng 319 biển, làm hỏng 0 biển (mục 6.5.2). Khảo
sát không tìm thấy công trình Việt Nam nào công bố đại lượng này tách bạch.

## 6.11. Kết luận chương

**Trả lời trực tiếp sáu câu hỏi nghiên cứu.** *RQ1:* bộ phát hiện YOLO11n đạt **toàn bộ** chỉ tiêu — mAP@0.5 = 0,9829, mAP@0.5:0.95 = 0,7834, Precision = 0,9837, Recall = 0,9714 (T6.4a), vượt mục tiêu. *RQ2:* có, chênh lệch giữa biển một dòng và hai dòng là **có ý nghĩa và rất lớn** — 25,45 điểm A6, nhưng nằm ở tầng OCR (T6.5c) chứ không ở tầng phát hiện (chỉ 2,09 điểm, T6.4b). *RQ3:* khối hậu xử lý đóng góp **+11,39 điểm** chuỗi đầy đủ, sửa đúng **319** biển, làm hỏng 0 (T6.5b). *RQ4:* NFR-P1 **chỉ đạt ngưỡng tối thiểu** (🟡): p95 = 1.143,10 ms — dưới sàn 1.500 ms nhưng vượt mục tiêu 800 ms 1,43 lần (T6.6a). Đây là thoái lui có chủ ý, đổi lấy 34 biển đọc thêm từ bậc thang thử-lại; cùng nguyên nhân đó làm **NFR-P2 trượt cả sàn** (2,379 FPS, sàn 3). Nút thắt thời gian vẫn là OCR (64,3%) và detector (34,0%, T6.6b). *RQ5:* bảng luật hiện hành **phần lớn không khớp** cặp nhầm thật — chỉ 2/10 cặp nhầm nhiều nhất được phủ (T6.5d). *RQ6:* các mối đe doạ được liệt kê và đánh giá ở 6.9.3, ba mối nghiêm trọng nhất ở mức "cao".

**Tầng phát hiện.** Trên tập test v3 (1.514 ảnh, 1.611 đối tượng), mô hình vượt mọi ngưỡng NFR với biên rộng; chỉ số quyết định mAP@0.5:0.95 = 0,7834 vượt mục tiêu 0,65. Điểm yếu duy nhất được phơi bày trung thực: dải đối tượng "rất nhỏ" (dưới 0,5% diện tích ảnh) chỉ đạt mAP@0.5 = 0,8553 (T6.4c) — hệ quả đo được của tiêu chí Q6 không đạt, trầm trọng thêm vì tập test nghiêng về nguồn camera giao thông (6.3.4).

**Đóng góp định lượng của khối hậu xử lý — đóng góp khoa học riêng của đồ án.** Đo hai lần trên cùng 2.801 biển có nhãn chuỗi cho hiệu số A6 − A5 = **+11,39 điểm**, là cải thiện thuần một chiều (319 sửa đúng / 0 làm hỏng). Đóng góp dồn gần trọn vào biển hai dòng (+13,97 điểm) nhưng vẫn không đủ tới ngưỡng, vì phần lỗi còn lại nằm ở tầng OCR — nơi hậu xử lý theo luật, vốn chỉ sửa được nhầm ký tự lẻ tẻ, về bản chất không với tới được các chuỗi sai nhiều ký tự trên biển hai dòng. Việc định vị đóng góp về từng nhóm luật (T6.5b) chưa đo được và là hạng mục cần viết mã.

**Hiệu năng — kết luận đã đảo so với dự kiến ban đầu.** Sau khi giải quyết mâu thuẫn số liệu (con số cũ 5.857 ms bị bác bỏ vì nhiễm tranh chấp CPU và đo sai checkpoint; đo lại trên máy rảnh với `best.pt` cho 731 ms), NFR-P1 **đã đạt mục tiêu ở thời điểm 20/07**. Cặp số đồng thuận khi ấy — client-side 731 ms, in-process 780 ms — xác nhận phương pháp đo, không mô tả hệ thống giao hàng.

**Nhưng bậc thang thử-lại thêm sau đó đã đảo kết luận này một lần nữa.** Ở cấu hình giao hàng (28/07), p95 là **1.143,10 ms**: NFR-P1 chuyển sang 🟡 — dưới sàn 1.500 ms nhưng vượt mục tiêu 800 ms 1,43 lần. Cùng đuôi độ trễ đó làm **NFR-P2 trượt cả sàn** (2,379 FPS, sàn 3). Breakdown thật là OCR 64,3% / detector 34,0% (T6.6b), không phải 93,3% / 6,7% như báo cáo cũ, nên tối ưu detector giờ có ý nghĩa thật.

Kết luận phải nói làm hai vế: **kiến trúc phần mềm không còn là vấn đề** — tầng API, tầng dữ liệu, bộ nhớ, độ ổn định đều dư biên; **nhưng độ trễ suy luận thì vẫn là vấn đề**, bên cạnh độ chính xác OCR trên biển hai dòng.

**Các giới hạn nghiêm trọng nhất.** Ba mối đe doạ hàng đầu (6.9.3): (i) rò rỉ tồn dư không khử được — ngay ngoài ngưỡng gộp, ở Hamming 12 vẫn còn 791 cặp gần trùng train↔test, và rò rỉ ngữ nghĩa thì không đo được; (ii) tập test không xuyên bộ dữ liệu — chỉ đo được tổng quát hoá *trong* phân bố; (iii) mẫu số nhỏ cho chỉ số OCR (2.801 biển có nhãn chuỗi trên 15.133 ảnh). Hệ quả: **mọi chỉ số độ chính xác trong chương nên được đọc như cận trên lạc quan.** Riêng A7 = 0,5552 thì ngược lại — là cận dưới bi quan do giao thức đo trên ảnh crop.

**Chuyển tiếp sang Chương 7.** Chương này xác định bằng số liệu — không bằng phỏng đoán — ba nhóm hướng phát triển: (i) **tối ưu hoặc thay thế khối OCR** cho biển hai dòng, bắt nguồn từ 6.5.3 và breakdown 6.6.2; (ii) **hiệu chỉnh bảng luật sửa lỗi theo ma trận nhầm lẫn đo được** (8/10 cặp nhầm nhiều nhất chưa có luật phủ), bắt nguồn từ 6.5.4, với ràng buộc phải kiểm chứng trên tập giữ riêng để tránh khớp luật trên chính tập đánh giá; (iii) **xây dựng tập test xuyên bộ dữ liệu, chia split theo nhóm biển số, và gán nhãn chuỗi cho một phân bố hiện trường** để đo NFR-A7 và NFR-A9 đúng cách, bắt nguồn từ 6.3.3, 6.5.5 và 5.11.3.
