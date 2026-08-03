# CHƯƠNG 6. THỰC NGHIỆM VÀ ĐÁNH GIÁ

Chương 5 trình bày hệ thống *đã được xây dựng* như thế nào. Chương này trả lời hai câu hỏi có trọng số ngang nhau: hệ thống đó **hoạt động tốt đến mức nào**, và **những con số đó có đáng tin không**. Vì vậy **mỗi con số đều đi kèm ngữ cảnh đo của nó**, và các mục có giá trị phương pháp luận cao nhất — kiểm chứng rò rỉ dữ liệu (6.3.3), đóng góp định lượng của khối hậu xử lý (6.5.2), các mối đe doạ đến tính hợp lệ (6.9.3) — được dành dung lượng tương xứng.

---

## 6.1. Mục tiêu và phương pháp đánh giá

### 6.1.1. Các câu hỏi nghiên cứu mà chương này trả lời

Sáu câu hỏi cụ thể hoá từ `docs/00-requirements/non-functional-requirements.md`. **RQ1** — bộ phát hiện YOLO11n có định vị được biển số Việt Nam đạt chỉ tiêu không (5.5; NFR-A1, A2, A3)? **RQ2** — độ chính xác nhận dạng có **chênh lệch có ý nghĩa** giữa biển một dòng và hai dòng không, chênh bao nhiêu (6.4.3, 6.5.3; NFR-A8)? **RQ3** — **khối hậu xử lý theo luật đóng góp bao nhiêu điểm phần trăm** vào độ chính xác chuỗi đầy đủ (6.5.2; NFR-A5 ↔ A6)? **RQ4** — hệ thống có đạt chỉ tiêu độ trễ trên phần cứng CPU-only không, nếu không thì **nút thắt ở đâu** (5.7; NFR-P1…P7)? **RQ5** — bảng luật sửa lỗi ký tự, vốn suy ra từ **hình dạng chữ** chứ không từ đo đạc, có khớp với các cặp ký tự thực sự bị nhầm không (6.5.4; `VNPLATE` §9.8)? **RQ6** — các số liệu chịu những **mối đe doạ nào đến tính hợp lệ** (6.9.3)?

RQ3 và RQ5 mang **đóng góp học thuật riêng**: RQ3 lượng hoá một khối chức năng mà phần lớn công trình ALPR chỉ mô tả định tính, RQ5 thay tri thức suy đoán bằng tri thức đo được. RQ6 quyết định giá trị của năm câu còn lại.

### 6.1.2. Hai nguyên tắc trình bày bắt buộc

**Nguyên tắc 1 — mọi số liệu hiệu năng phải công bố kèm cấu hình phần cứng.** Đồ án chạy suy luận **hoàn toàn trên CPU**, nên mọi so sánh với các con số FPS trong tài liệu — hầu hết đo trên GPU — là không hợp lệ nếu không ghi rõ. Bảng 6.1 là **điều kiện diễn giải** cho mọi bảng hiệu năng ở mục 6.6. **Nguyên tắc 2 — mọi số liệu độ chính xác phải công bố kèm tên tập dữ liệu và số mẫu**, vì độ chính xác là thuộc tính của **cặp (mô hình, tập đánh giá)**. Hệ quả trực tiếp: các chỉ số OCR (NFR-A4…A7) chỉ đo được trên **tập con có nhãn chuỗi ký tự**, nhỏ hơn nhiều tập test phát hiện — mẫu số đó phải hiện diện trong bảng, không được giấu.

> **Cảnh báo trích dẫn.** Cặp số **94,3%** (biển một dòng) ↔ **45,7%** (biển hai dòng), chênh **48,6 điểm phần trăm**, được đo trên bộ dữ liệu **RodoSol-ALPR của Brazil** [7]<!-- laroca_2022_crossdataset -->. Đây **không phải** số liệu Việt Nam. Mỗi lần cặp số này được dẫn, tên bộ dữ liệu và quốc gia phải xuất hiện **ngay trong câu**; nó chỉ được dùng như *analogue định lượng* về mức độ khó tương đối của biển hai dòng, không bao giờ như mốc chuẩn phải vượt.

### 6.1.3. Giao thức đo

![](figures/fig-ch6-01.png)

**Hình 6.1.** ** Giao thức đo và ràng buộc phụ thuộc giữa các bước đánh giá.

Ràng buộc cốt lõi: **không bước đo nào chạy trước khi trọng số được đóng băng**, và **tập test không được chạm vào trong huấn luyện lẫn chọn epoch** — chọn epoch chỉ dựa vào tập validation. Ba quy ước: **kích thước lô = 1 khi đo độ trễ** (hệ thống phục vụ yêu cầu đơn lẻ; riêng mAP dùng lô lớn hơn vì mAP không phụ thuộc kích thước lô); **bỏ 3 lượt khởi động nóng** đầu để chi phí cấp phát bộ nhớ lần đầu không làm lệch phân vị; **báo cáo p50/p95/p99, không báo cáo trung bình**, vì trung bình che giấu đuôi phân bố và NFR-P1 phát biểu ở p95.

---

## 6.2. Môi trường thực nghiệm

### 6.2.1. Cấu hình phần cứng và hệ thống

<!-- {{T6.2a}} cau hinh phan cung va he thong — DA CO SO, khong can dien -->

**Bảng 6.1.** Cấu hình phần cứng và hệ thống của máy thực nghiệm

| Hạng mục | Cấu hình thực tế |
|---|---|
| Hệ điều hành · Python | Windows 11 Pro 10.0.26200 · Python 3.13.12 |
| CPU | Intel Raptor Lake (CPU Family 6, Model 183) — **14 nhân vật lý / 20 nhân logic** |
| GPU dùng cho suy luận | **Không có GPU CUDA** — mọi suy luận chạy trên CPU |
| Thiết bị huấn luyện | `device=cpu` |
| Chế độ đo | Kích thước lô = 1, bỏ 3 lượt khởi động nóng đầu tiên |

Toàn bộ số liệu chương này đo trên **một máy trạm cá nhân duy nhất** (`docs/00-requirements/environment.md`). Bảng này là **tiền tố ngầm định của mọi con số hiệu năng ở mục 6.6**.

### 6.2.2. Phiên bản thư viện

<!-- {{T6.2b}} phien ban thu vien tai thoi diem do — dien tu pip freeze -->

**Bảng 6.2.** Phiên bản thư viện tại thời điểm đo

| Nhóm | Gói và phiên bản đo được (`backend/.venv`) |
|---|---|
| Ngăn xếp suy luận | `ultralytics` 8.4.101 · `torch` 2.13.0+cpu · `torchvision` 0.28.0+cpu · `paddleocr` 3.7.0 (PP-OCRv5 mobile) · `paddlepaddle` 3.3.1 |
| Backend suy luận thay thế (6.6.3) | `onnxruntime` 1.27.0 · `openvino` 2026.2.1 |
| Ảnh và số học | `opencv-python` 4.10.0.84 · `numpy` 2.4.5 |
| Tầng API và dữ liệu | `fastapi` 0.139.2 · `uvicorn` 0.51.0 · `sqlalchemy` 2.0.51 |
| Đánh giá và kiểm thử | `imagehash` 5.6.2 · `pytest` 9.1.1 |

> Trích trực tiếp từ `pip freeze` đúng thời điểm chạy phép đo cuối cùng (2026-07-20), không chép từ `requirements.txt` (tệp yêu cầu ghi *ràng buộc*, không ghi *phiên bản đã cài*). Đồ án dùng **một môi trường ảo hợp nhất** chứa cả ngăn xếp suy luận lẫn ngăn xếp API, nên bảng chỉ còn một cột phiên bản thay vì hai như phác thảo ban đầu.

### 6.2.3. Vì sao ràng buộc CPU-only là ràng buộc thiết kế, không phải hạn chế tạm thời

Lập luận đầy đủ ở **5.1.2**; ở đây chỉ nêu hệ quả với việc diễn giải số đo. NFR-P1 được phát biểu *kèm* ràng buộc CPU, nên kết luận "đạt sàn, không đạt mục tiêu" ở 6.6 là kết luận về hệ thống trong đúng bối cảnh vận hành thật, không phải con số chờ nâng cấp phần cứng. Cấu hình mô hình cũng do ràng buộc phần cứng quyết định — **YOLO11n** (2.590.035 tham số) [16]<!-- jocher_2024_yolo11 --> và **PP-OCRv5 mobile** [118]<!-- paddlepaddle_2026_ppocrv5docs --> — nên mọi kết quả độ chính xác phải đọc kèm lựa chọn đó. Về quy mô: **35,6 phút mỗi epoch** trên CPU, một lượt 20 epoch mất khoảng **12 giờ** liên tục, khiến **tìm kiếm siêu tham số bất khả thi**; đó là lý do chương này báo cáo *một* cấu hình huấn luyện chứ không phải một khảo sát siêu tham số — giới hạn thật, ghi ở 6.9.3, không được trình bày như thể là kết quả của một quá trình tối ưu.

---

## 6.3. Bộ dữ liệu thực nghiệm

### 6.3.1. Ba phiên bản bộ dữ liệu và lý do tồn tại của từng phiên bản

> **Lưu ý về cách đặt tên.** Thư mục `yolo_v2/` và `yolo_v3/` chỉ **phiên bản của bộ dữ liệu**, hoàn toàn **không** liên quan đến kiến trúc YOLOv2 hay YOLOv3. Mô hình dùng trong toàn đồ án là **YOLO11n**.

<!-- {{T6.3a}} so sanh ba phien ban bo du lieu — DA CO SO, khong can dien -->

**Bảng 6.3.** So sánh ba phiên bản bộ dữ liệu

| Thuộc tính | v1 (`processed/yolo/`) | v2 (`processed/yolo_v2/`) | **v3 (`processed/yolo_v3/`)** |
|---|---:|---:|---:|
| Tổng số ảnh | 4.578 | 15.133 | **15.133** |
| Số bộ vào hợp nhất detection | 1 | 7 | **7** |
| Nguồn nguyên tố sau khử trùng lặp chéo bộ | 1 | 6 | **6** |
| Ngưỡng Hamming gộp trùng lặp | 5 | 5 | **10** |
| Rò rỉ train↔test (đo ở ngưỡng phash 10) | **Có — 619 cặp** | **Có — 2.699 cặp** | (xem 6.3.3) |
| Số ảnh train / val / test | — | — | **10.592 / 3.027 / 1.514** |
| Dùng cho | Baseline `baseline-416-v1.pt` | Bị loại bỏ | **Mô hình chính thức `best.pt`** |

**v1 quá nhỏ và chỉ một nguồn** — động cơ trực tiếp để tải thêm **tám bộ** nữa (tổng 9 bộ tải về), trong đó **sáu bộ** đi vào hợp nhất detection cùng bộ gốc, hai bộ nhãn mức ký tự tách riêng phục vụ đánh giá OCR. **v2 sửa được quy mô nhưng không sửa được rò rỉ:** mở rộng lên 15.133 ảnh lại *tăng* số cặp gần trùng xuyên split lên 2.699, vì các nguồn khác nhau chứa ảnh có nguồn gốc chung. **v3 giữ nguyên corpus** (cùng 15.133 ảnh), khác biệt duy nhất là ngưỡng khử trùng lặp nâng từ 5 lên 10 và split sinh lại — cô lập biến có chủ ý, cho phép quy kết mọi thay đổi kết quả cho *chất lượng split*, không cho *lượng dữ liệu*.

### 6.3.2. Khử trùng lặp: hai tỉ lệ, hai mẫu số khác nhau

Trước khi hợp nhất, trên toàn bộ ảnh của 7 bộ vào hợp nhất detection: loại **11.978 / 27.111 = 44,2%**. Sau khi hợp nhất, ở ngưỡng 10 trên corpus đã hợp nhất: loại **7.227 / 15.133 = 47,8%**. Hai tỉ lệ không cộng dồn và không thay thế nhau — số thứ nhất là mức trùng lặp *giữa và trong* 7 bộ, số thứ hai là mức trùng lặp còn lại *trong corpus đã hợp nhất*. *Về mẫu số 27.111:* tổng ảnh của **7 bộ vào hợp nhất detection** (4.578 + 8.254 + 236 + 840 + 8.357 + 3.841 + 1.005), **không phải** toàn bộ 9 bộ đã tải; hai bộ còn lại — `roboflow_ocr_plate` (3.819 ảnh, 30 lớp ký tự) và `roboflow_ocr_conversion` (200 ảnh, 22 lớp ký tự) — là bộ **nhãn mức ký tự**, tách riêng để đánh giá tầng OCR (`datasets/reports/merge_report.json`, trường `images_per_dataset` có đúng 7 khoá). Mọi lần trích dẫn một trong hai tỉ lệ đều phải kèm mẫu số tương ứng.

### 6.3.3. Kiểm chứng rò rỉ dữ liệu — và vì sao con số "0 cặp rò rỉ" không chứng minh được điều gì

Mục này báo cáo một **giới hạn nhận thức** mà đồ án phát hiện ở chính quy trình của mình. Rò rỉ dữ liệu xảy ra khi tập test chứa ảnh gần trùng ảnh train: mô hình *ghi nhớ* thay vì *tổng quát hoá*, mọi chỉ số bị thổi phồng — với corpus ghép từ nhiều nguồn công khai đây là rủi ro hệ thống, và vấn đề tổng quát hoá xuyên tập dữ liệu đã được ghi nhận rõ [7]<!-- laroca_2022_crossdataset -->. Công cụ đo là **băm tri giác** (`imagehash.phash`, 64 bit), đếm số cặp xuyên split có khoảng cách Hamming ≤ ngưỡng.

> **Lập luận vòng tròn.** Bộ v3 được khử trùng lặp ở ngưỡng Hamming 10; đo rò rỉ ở đúng ngưỡng đã dùng để gộp trùng lặp là **kiểm tra lại chính định nghĩa của mình**, không phải kiểm chứng độc lập. Kết quả bằng 0 ở đó chứng minh bước khử trùng lặp *đã chạy đúng đặc tả*, và **không chứng minh gì thêm** về mức độ "sạch" của tập test.

<!-- {{T6.3b}} so cap gan trung xuyen split theo nguong Hamming -->

**Bảng 6.4.** Số cặp ảnh gần trùng xuyên split theo ngưỡng Hamming

| Ngưỡng Hamming | v1 | v2 | **v3** | Ô này có mang thông tin mới không? |
|:---:|---:|---:|---:|---|
| 0 (trùng khít bit-hash) | — | — | **0** | Có |
| 5 | — | — | **0** | Không với v1, v2 (bằng ngưỡng gộp của chúng) |
| **10** | **619** | **2.699** | **0** | **Không với v3** — bằng ngưỡng gộp |
| 12 | — | — | **791** | **Có** |
| 15 | — | — | **3.529** | **Có** |
| 20 | — | — | **137.506** | Có, nhưng ngưỡng đã lỏng tới mức nhiều cặp là dương tính giả |

> Mẫu số: 10.592 ảnh train × 1.514 ảnh test = 16.036.288 cặp đã so sánh. Khoảng cách Hamming **nhỏ nhất quan sát được là 12** — giá trị chẵn kế tiếp sau ngưỡng gộp 10, một tất yếu toán học (mọi mã băm đều có đúng 32 bit 1 nên khoảng cách luôn chẵn), **không phải dấu vết rò rỉ bị cắt cụt tại ngưỡng**; số liệu kiểm chứng (15.133/15.133 mã băm có popcount chẵn; 4.498.500/4.498.500 cặp lấy mẫu có khoảng cách chẵn) ở [`02-dataset-report.md` mục 6bis.1](../reports/02-dataset-report.md). Cột v1/v2 chỉ có số ở ngưỡng 10 vì đó là con số đã đo trước đó; các ô trống **không được suy ra**.

Chỉ các ngưỡng **12 (791 cặp), 15 (3.529 cặp), 20 (137.506 cặp)** mang thông tin mới, và ngay cả chúng cũng **không** chứng minh tập test sạch. **Ba giới hạn của phương pháp phash:** (1) phash chỉ bắt tương đồng ở mức **bố cục sáng-tối tổng thể** — hai ảnh *cùng một chiếc xe* ở hai góc khác nhau, hoặc hai khung hình cách nhau vài giây trong cùng video, vẫn mang **cùng một biển số** dù khoảng cách Hamming lớn; loại rò rỉ ngữ nghĩa này **không khử được bằng bất kỳ ngưỡng phash nào**; (2) **không có định danh phương tiện hay chuỗi biển cho toàn corpus** nên không chia split theo **nhóm biển số** được — chính hạn chế dẫn tới mẫu số nhỏ của các bảng OCR ở 6.5; (3) **ngưỡng cao sinh dương tính giả**, nên 137.506 là **cận trên bi quan**, không phải ước lượng điểm.

**Kết luận trung thực.** Có thể khẳng định: *bước khử trùng lặp ở ngưỡng 10 đã chạy đúng đặc tả, và số cặp gần trùng ở các ngưỡng lỏng hơn nằm ở mức đã ghi trong Bảng 6.4*. **Không** thể khẳng định: *tập test hoàn toàn độc lập với tập train*. Rò rỉ tồn dư ở mức ngữ nghĩa là **không đo được bằng công cụ hiện có** — mối đe doạ đầu tiên ở 6.9.3; mọi chỉ số ở 6.4 phải đọc kèm ghi chú này.

### 6.3.4. Phân bố nguồn dữ liệu giữa các split

<!-- {{T6.3c}} phan bo nguon du lieu giua cac split cua v3 -->

**Bảng 6.5.** Phân bố nguồn dữ liệu giữa các split của phiên bản v3

| Tổ hợp xuất xứ | Tổng | Train (số / %) | Val (số / %) | Test (số / %) |
|---|---:|---:|---:|---:|
| `hf_vn_plates_segment\|roboflow_cuong_ta\|roboflow_eric_nguyen\|roboflow_school_fuhih\|roboflow_traffic_camera` | 4.411 | 4.411 / 100,0% | 0 / 0,0% | 0 / 0,0% |
| `roboflow_school_fuhih` | 3.599 | 2.275 / 63,2% | 938 / 26,1% | 386 / 10,7% |
| `hf_vn_plates_segment` | 2.820 | 1.933 / 68,5% | 574 / 20,3% | 313 / 11,1% |
| `roboflow_traffic_camera` ⚠ **lệch > 10 điểm %** | 2.582 | 1.368 / 53,0% | 689 / 26,7% | 525 / 20,3% |
| `hf_vn_plates_segment\|roboflow_school_fuhih` | 634 | 78 / 12,3% | 527 / 83,1% | 29 / 4,6% |
| `roboflow_eric_nguyen` | 351 | 228 / 65,0% | 77 / 21,9% | 46 / 13,1% |
| `roboflow_school_fuhih\|roboflow_traffic_camera` ⚠ **lệch > 10 điểm %** | 250 | 4 / 1,6% | 72 / 28,8% | 174 / 69,6% |
| `roboflow_demo_tracking` | 210 | 139 / 66,2% | 51 / 24,3% | 20 / 9,5% |
| `roboflow_cuong_ta` | 136 | 88 / 64,7% | 33 / 24,3% | 15 / 11,0% |
| `roboflow_demo_tracking\|roboflow_traffic_camera` | 57 | 32 / 56,1% | 22 / 38,6% | 3 / 5,3% |
| `hf_vn_plates_segment\|roboflow_traffic_camera` | 50 | 29 / 58,0% | 18 / 36,0% | 3 / 6,0% |
| `hf_vn_plates_segment\|roboflow_school_fuhih\|roboflow_traffic_camera` | 20 | 0 / 0,0% | 20 / 100,0% | 0 / 0,0% |
| `hf_vn_plates_segment\|roboflow_demo_tracking\|roboflow_traffic_camera` | 4 | 0 / 0,0% | 4 / 100,0% | 0 / 0,0% |
| `roboflow_cuong_ta\|roboflow_school_fuhih` | 4 | 2 / 50,0% | 2 / 50,0% | 0 / 0,0% |
| `hf_vn_plates_segment\|roboflow_eric_nguyen\|roboflow_school_fuhih` | 3 | 3 / 100,0% | 0 / 0,0% | 0 / 0,0% |
| `roboflow_demo_tracking\|roboflow_school_fuhih` | 2 | 2 / 100,0% | 0 / 0,0% | 0 / 0,0% |
| **Tổng** | **15.133** | **10.592 / 70,0%** | **3.027 / 20,0%** | **1.514 / 10,0%** |

> **Cách đếm — bắt buộc đọc trước khi điền bảng.** Cột `source_dataset` trong `split_manifest.csv` chứa một **tập xuất xứ** ngăn cách bằng `|`: một ảnh giữ lại có thể đến từ nhiều nguồn cùng lúc, nên 16 dòng trên là **tổ hợp xuất xứ**, không phải nguồn, dựng từ đúng **6 nguồn nguyên tố** (`roboflow_school_fuhih`, `hf_vn_plates_segment`, `roboflow_traffic_camera`, `roboflow_eric_nguyen`, `roboflow_cuong_ta`, `roboflow_demo_tracking`). Cộng dồn số đếm của 6 nguồn cho **33.828**, vượt xa 15.133 vì ảnh đa nguồn bị đếm nhiều lần — **không được dùng 33.828 làm mẫu số**; tỉ lệ mỗi dòng tính theo tổng ảnh của **chính dòng đó**. Phải phân biệt ba con số nguồn: **9 bộ đã tải về**, **7 bộ vào hợp nhất detection**, **6 nguồn nguyên tố** trong v3.

**Tiêu chí đọc bảng:** nếu tỉ lệ của một nguồn trong tập test lệch quá 10 điểm phần trăm so với tỉ lệ tổng thể (10,0%) thì phải nêu tên và thảo luận. Hai tổ hợp vượt: `roboflow_traffic_camera` thuần (2.582 ảnh) có **20,3%** rơi vào test — gấp đôi tỉ lệ tổng thể; `roboflow_school_fuhih|roboflow_traffic_camera` (250 ảnh) có tới **69,6%**. Nghĩa là **tập test nghiêng về ảnh camera giao thông** — ảnh hiện trường góc rộng, biển nhỏ — nên khi đọc mAP theo dải kích thước (6.4.4) phải nhớ đối tượng nhỏ trong tập test không phân bố ngẫu nhiên mà tập trung ở một nguồn. Đây là hệ quả của việc các tổ hợp nhỏ khó chia đều (split sinh ngẫu nhiên phân tầng), ghi nhận như yếu tố đọc kèm chứ không phải khiếm khuyết vô hiệu hoá kết quả.

**Một bộ dữ liệu dư thừa hoàn toàn.** `roboflow_tran_ngoc_xuan_tin` vào hợp nhất với **1.005 ảnh** và ra khỏi khử trùng lặp chéo bộ với **0 ảnh — tỉ lệ loại 100,0% (1.005/1.005)**: **cả 1.005 ảnh đều dính ít nhất một cặp gần trùng** (1.577 cặp với `roboflow_school_fuhih`, 1.569 cặp với `roboflow_cuong_ta`, 8 cặp với `hf_vn_plates_segment`, 35 cặp trùng nội bộ — `datasets/reports/v2/duplicate_pairs.csv`); kiểm chứng độc lập: `split_manifest.csv` không chứa tên bộ này dù chỉ một lần. Đây là **bằng chứng định lượng** cho cảnh báo ở Phase 1 rằng các bộ Roboflow tái sử dụng ảnh của nhau rất nặng — có hẳn một bộ là **tập con thực sự** của hai bộ khác — và là lý do **không được cộng dồn `expected_images` để suy ra quy mô thật**: phép cộng đó giả định các bộ độc lập, trong khi một bộ 1.005 ảnh có thể đóng góp đúng 0 ([`02-dataset-report.md`](../reports/02-dataset-report.md) mục 6.3.1).

---

## 6.4. Đánh giá bộ phát hiện biển số

Toàn bộ mục 6.4 đo trên **tập test v3: 1.514 ảnh**, `imgsz=640`, `device=cpu`; tập test chưa từng dùng trong huấn luyện hay chọn epoch.

### 6.4.1. Chỉ số tổng thể

<!-- {{T6.4a}} ket qua detection tong the tren tap test v3 (1.514 anh) -->

**Bảng 6.6.** Kết quả phát hiện tổng thể trên tập test v3

| Chỉ số | Mã NFR | Ngưỡng tối thiểu | Mục tiêu | **Đo được** | Kết quả |
|---|:---:|---:|---:|---:|:---:|
| mAP@0.5 | NFR-A1 | 0,85 | 0,90 | **0,9829** | ✅ đạt |
| mAP@0.5:0.95 | NFR-A2 | 0,55 | 0,65 | **0,7834** | ✅ đạt |
| Precision | NFR-A3 | 0,88 | 0,92 | **0,9837** | ✅ đạt |
| Recall | NFR-A3 | 0,85 | 0,90 | **0,9714** | ✅ đạt |
| F1 tại ngưỡng confidence đo (0,25) | — | — | — | **0,9775** | n/a |
| Số ảnh test / số đối tượng nhãn thật | — | — | — | **1.514 / 1.611** | n/a |

Ký hiệu cột **Kết quả**: ✅ đạt mục tiêu · 🟡 chỉ đạt ngưỡng tối thiểu · ❌ không đạt · ⬜ chưa đo.

**Cả bốn chỉ tiêu bắt buộc của tầng phát hiện đều đạt mục tiêu**, đo trên `ultralytics_val`; ngưỡng vận hành tối ưu theo F1 phải đọc từ Hình 6.4, không suy từ bảng này. Ba lưu ý bắt buộc: (1) **bài toán chỉ có một lớp** (`plate`), mAP một lớp không so trực tiếp được với mAP nhiều lớp trên COCO nên giá trị cao là bình thường và **không phải bằng chứng về độ khó đã được vượt qua**; (2) chỉ số quyết định là **mAP@0.5:0.95** vì độ khớp box ảnh hưởng trực tiếp đến chất lượng vùng cắt đưa sang OCR — nút thắt độ chính xác thật (6.5); (3) **chỉ số tổng thể che giấu phân bố**, nên không được kết luận về năng lực hệ thống chỉ từ Bảng 6.6.

### 6.4.2. Đường cong PR và ma trận nhầm lẫn

*Hình 6.2.* Đường cong Precision–Recall tách theo layout — `05-detection-pr-curve.png` *(chưa sinh)*. *Hình 6.3.* Ma trận nhầm lẫn nhận biết layout (hàng: nhãn thật một dòng / hai dòng / nền; cột: dự đoán) — `05-detection-confusion-matrix.png` *(chưa sinh)*. *Hình 6.4.* Đường cong F1 theo ngưỡng confidence — `05-detection-f1-curve.png` *(chưa sinh)*. Cả ba ở `docs/reports/figures/`.

Hình 6.4 có vai trò thực tiễn trực tiếp: **ngưỡng confidence dùng trong hệ thống chạy thật phải là ngưỡng tối ưu F1 đo được ở đây**, không phải mặc định 0,25 của Ultralytics; nếu hai giá trị lệch nhau thì cấu hình suy luận phải được cập nhật và việc đó phải được ghi lại.

### 6.4.3. Tách theo biển một dòng và biển hai dòng (NFR-A8)

NFR-A8 yêu cầu báo cáo **tách bạch** hai quần thể. Layout xác định theo nhãn lớp khi bộ dữ liệu có khai báo, và theo **ngưỡng tỉ lệ khung hình 2,5** khi không có — nằm giữa tỉ lệ chuẩn của biển một dòng (4,727) và biển hai dòng (2,000 / 1,357) theo QCVN 08:2024/BCA.

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

> **Nhãn layout là ước lượng, không phải nhãn thật.** Bộ dữ liệu không khai báo lớp layout nên layout suy từ ngưỡng tỉ lệ khung hình 2,5 (100% số ô được suy bằng heuristic). Mọi kết luận về NFR-A8 ở tầng phát hiện phải nêu rõ điều này.

**Chênh lệch ở tầng phát hiện rất nhỏ, đúng dự đoán** — ở mAP@0.5:0.95 biển hai dòng thậm chí *nhỉnh hơn* 1,23 điểm, tức dao động trong phạm vi nhiễu chứ không phải xu hướng; cùng bậc với mốc baseline (`baseline-416-v1.pt`, split v1, imgsz 416: một dòng 0,9856 so với hai dòng 0,9592, chênh 2,6 điểm — **số của baseline, không được chuyển thành số của `best.pt`**). Kết luận: **việc *định vị một hình chữ nhật* gần như không phụ thuộc vào việc bên trong có một dòng hay hai dòng ký tự.** Vì vậy **tuyệt đối không được** dùng con số 2,09 điểm để kết luận "hệ thống xử lý tốt biển hai dòng" — chênh lệch thật nằm ở tầng OCR và chỉ lộ ra ở Bảng 6.11, nơi khoảng cách nhảy lên **25,45 điểm**.

### 6.4.4. Tách theo dải kích thước hộp giới hạn

Mục này tồn tại vì **bộ dữ liệu không đạt tiêu chí chất lượng Q6**: **10,91% số hộp giới hạn có diện tích dưới 0,5% diện tích ảnh**, vượt ngưỡng cho phép 10%. Đối tượng nhỏ là chế độ thất bại đã được ghi nhận rộng rãi của các bộ phát hiện một giai đoạn [119]<!-- ultralytics_2026_modelevaluation -->, và biển số độ phân giải thấp đã thành hướng nghiên cứu riêng [71]<!-- laroca_2026_icprlrlpr -->; báo cáo một con số mAP tổng sẽ **giấu chế độ thất bại phía sau giá trị trung bình**.

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

> Dòng ⚠ (28 đối tượng < 30) **không có ý nghĩa thống kê** và không được đưa vào so sánh. Dải tính từ `(w×h)` của hộp nhãn thật chia cho diện tích ảnh gốc; số box không gán được dải: 0.

**Chế độ thất bại ở đối tượng nhỏ được xác nhận có thật:** dải "rất nhỏ" thấp hơn rõ rệt toàn tập và cách biệt lớn so với dải "trung bình" vốn chiếm hơn nửa tập test, Recall 0,8740 so với 0,9922 — bộ phát hiện **bỏ sót nhiều biển nhỏ hơn hẳn**. Đây là xác nhận trực tiếp rằng tiêu chí Q6 không đạt đã gây hậu quả đo được, không phải cảnh báo lý thuyết; kết hợp với 6.3.4, dải "rất nhỏ" chiếm **16,26%** tập test cao hơn tỉ lệ **10,91%** của toàn corpus, nghĩa là **tập test khó hơn trung bình ở đúng khía cạnh này**. Phương án khắc phục: tăng `imgsz`, cắt ảnh theo ô (*tiling*), hoặc lọc bỏ đối tượng quá nhỏ khỏi tập huấn luyện. Đáng chú ý: dù dải nhỏ kéo mAP tổng xuống, chỉ số tổng thể vẫn đạt mục tiêu — nếu chỉ báo cáo một con số tổng thì chế độ thất bại này đã bị **giấu sau giá trị trung bình**.

---

## 6.5. Đánh giá khối OCR và hậu xử lý

> **Ràng buộc mẫu số.** NFR-A4…A7 chỉ đo được trên **tập con có nhãn chuỗi ký tự** (`datasets/annotations/plate_labels.csv`), không phải trên toàn bộ 1.514 ảnh test; tập con nhỏ hơn nhiều lần. Mọi bảng trong 6.5 đều có dòng "số mẫu" và dòng đó **không được để trống khi công bố**. Việc thiếu nhãn chuỗi cho phần lớn corpus là hạn chế thật, ghi ở 6.9.3.

### 6.5.1. Độ chính xác mức ký tự (NFR-A4)

Chỉ số là **CER** theo khoảng cách Levenshtein, chuẩn hoá theo độ dài nhãn thật, với $S$ số ký tự thay thế, $D$ số bị xoá, $I$ số chèn thừa, $N$ tổng ký tự nhãn thật; NFR-A4 phát biểu theo **1 − CER**.

$$\mathrm{CER} = \frac{S + D + I}{N}$$

<!-- {{T6.5a}} do chinh xac muc ky tu NFR-A4 -->

**Bảng 6.9.** Độ chính xác mức ký tự (NFR-A4)

| Chỉ số | Ngưỡng tối thiểu | Mục tiêu | **Trước hậu xử lý** | **Sau hậu xử lý** | Kết quả |
|---|---:|---:|---:|---:|:---:|
| 1 − CER (NFR-A4) | 0,92 | 0,95 | 0,9061 | **0,9454** | 🟡 đạt ngưỡng tối thiểu |
| CER | ≤ 0,08 | ≤ 0,05 | 0,0939 | 0,0546 | n/a |
| $N$ / $S$ / $D$ / $I$ | — | — | 23.855 / 862 / 1.272 / 107 | 23.855 / 862 / 1.272 / 107 | n/a |
| **Số biển có nhãn chuỗi (mẫu số)** | — | — | **2.801** | **2.801** | n/a |

> **Nguồn số liệu.** Toàn bộ 6.5 lấy từ `docs/reports/05-results.json` — lượt đo 2026-07-28 trên máy rảnh, `models/best.pt` (`imgsz = 640`), 2.801 ảnh có nhãn chuỗi, đúng cấu hình giao hàng (nắn hình bật, siêu phân giải tắt — 6.5.7). Lượt này thay bộ số 20/07 vì hai lý do độc lập: **một**, bốn đợt sửa độ chính xác rơi vào 21–28/07 nên số cũ mô tả một hệ thống không còn tồn tại; **hai**, nghiêm trọng hơn, harness đo trước 28/07 **chưa bao giờ gọi** bậc thang thử-lại — cả nhánh vùng cắt lẫn nhánh đầu-cuối đều chép lại các bước pipeline rồi dừng ở bước cứu dòng trên, nên mọi con số A4–A7 công bố trước đó mô tả một pipeline **ngắn hơn bản giao hàng** (6.5.7; `docs/reports/27-retry-ladder-cost-benefit.md`).
>
> $S$/$D$/$I$ đo trên **chuỗi thô trước hậu xử lý** (dẫn từ ma trận nhầm lẫn: $S$ = tổng ô ngoài đường chéo, $D$ = tổng xoá, $I$ = tổng chèn, $N$ = tổng ma trận cộng $D$) nên giống nhau ở cả hai cột — cũng vì vậy bước cứu dòng trên lẫn bậc thang thử-lại, vốn chạy **sau** chuẩn hoá, không làm ba con số này thay đổi.

**NFR-A4 đạt ngưỡng tối thiểu**, còn cách mục tiêu 0,95 khoảng 0,5 điểm. Chỉ tiêu này từng ghi là **không đạt** (0,8848, đo 20/07/2026); lượt đo lại 28/07 trên đúng bộ trọng số ấy cho 0,9454 — chênh lệch **không** đến từ mô hình khác mà từ các bản sửa ở tầng suy luận và từ việc harness được nối đúng với pipeline giao hàng.

Đáng chú ý hơn con số tổng là **cấu trúc lỗi**: tổng thao tác chỉnh sửa giảm từ 3.092 xuống **2.241**, nhưng ba thành phần giảm rất không đều — chèn thừa $I$ 903 → **107** (−88,1%), thay thế $S$ 1.007 → **862** (−14,4%), xoá $D$ 1.182 → **1.272** (+7,6%). **Ký tự chèn thừa gần như biến mất** — dấu vân tay của các bản sửa đọc biển hai dòng (trước đây vùng chồng lấn bị đọc hai lần nên sinh ký tự lặp, viền biển và vết bẩn bị đọc thành ký tự); ngược lại **ký tự bị xoá nhích lên** và nay chiếm **56,8%** toàn bộ lỗi, tức phần lỗi còn lại đã dịch hẳn về dạng **đọc hụt ký tự**, không phải đọc nhầm. Điều này định hình trước mọi kết luận sau: bảng luật mạnh ở việc sửa $S$ nhưng **về nguyên tắc không thể phục hồi một ký tự chưa từng được đọc ra**, nên khi $D$ chi phối thì hướng cải thiện phải chuyển sang tầng nhận dạng (mục 7.4). Ba loại lỗi gợi ba nguyên nhân khác nhau: $S$ → nhầm ký tự (xử lý được bằng bảng luật, 6.5.4), $D$ → bỏ sót ký tự do vùng cắt thiếu hoặc ký tự mờ, $I$ → nhiễu bị đọc thành ký tự; phân tích ở 6.8 dựa trực tiếp vào bộ ba này.

### 6.5.2. Chuỗi đầy đủ: trước và sau hậu xử lý (NFR-A5 ↔ NFR-A6)

**Đây là mục quan trọng nhất của cả chương.** Khối hậu xử lý theo luật — chuẩn hoá ký tự, áp mặt nạ vị trí chữ số / chữ cái theo định dạng biển số Việt Nam, sửa cặp ký tự đồng hình, kiểm tra mã tỉnh — là **đóng góp kỹ thuật riêng** của đồ án, không có sẵn trong thư viện nào. Câu hỏi *khối đó đóng góp bao nhiêu?* chỉ trả lời được nếu **đo hai lần trên cùng một tập mẫu**: chuỗi thô do PaddleOCR trả về (NFR-A5) và chuỗi sau khi áp toàn bộ luật (NFR-A6); hiệu số **chính là** đóng góp định lượng của khối hậu xử lý. Đây cũng là lý do kỹ thuật khiến trường `raw_ocr_text` tồn tại bên cạnh `plate_text` trong lược đồ cơ sở dữ liệu — nó là **điều kiện cần để phép đo này thực hiện được**, phải có từ giai đoạn thiết kế chứ không thể thêm lúc viết chương đánh giá.

<!-- {{T6.5b}} do chinh xac chuoi day du truoc va sau hau xu ly — DONG GOP DINH LUONG CUA KHOI HAU XU LY -->

**Bảng 6.10.** Độ chính xác chuỗi đầy đủ trước và sau hậu xử lý

| Chỉ số | Mã NFR | Ngưỡng tối thiểu | Mục tiêu | **Đo được** | Kết quả |
|---|:---:|---:|---:|---:|:---:|
| Độ chính xác chuỗi **trước** hậu xử lý | NFR-A5 | 0,80 | 0,85 | **0,6373** | ❌ không đạt |
| Độ chính xác chuỗi **sau** hậu xử lý | NFR-A6 | 0,85 | 0,90 | **0,7512** | ❌ không đạt |
| **Mức cải thiện (A6 − A5), điểm phần trăm** | — | — | — | **+11,39** | n/a |
| Số biển **được sửa đúng** / **bị làm hỏng** | — | — | — | **319** / **0** | n/a |
| Số biển sai cả trước lẫn sau | — | — | — | **697** | n/a |
| **Số mẫu (biển có nhãn chuỗi)** | — | — | — | **2.801** | n/a |

Dòng "sửa đúng / làm hỏng" quan trọng ngang dòng hiệu số: một mức cải thiện thuần +5 điểm có thể là sửa đúng 60 và làm hỏng 10, hoặc sửa đúng 50 và không làm hỏng biển nào — hai tình huống **hàm ý hai kết luận kỹ thuật khác nhau** về chất lượng bộ luật.

> **Phân rã đóng góp theo từng nhóm luật — *(chưa đo)*.** Năm nhóm cần bóc tách: chuẩn hoá cơ bản (bỏ ký tự phân tách, viết hoa, `Đ`→`D`), mặt nạ vị trí + `TO_DIGIT`, mặt nạ vị trí + `TO_LETTER`, ghép dòng cho biển hai dòng, kiểm tra mã tỉnh hợp lệ; với mỗi nhóm cần số biển bị thay đổi, số sửa **đúng**, số bị làm **hỏng**, đóng góp thuần — tất cả *(chưa đo)* vì `ai/inference/plate_rules.py` chưa có cơ chế bật/tắt từng nhóm luật riêng lẻ. Hạng mục cần viết mã (mục D.2 tài liệu vận hành); hiện chỉ đo được đóng góp *tổng*. Hai bậc cứu chữa chạy **sau** chuẩn hoá thì đã cô lập riêng được nhờ đo A/B ở 6.5.6 và 6.5.7: **cứu dòng trên** cho **209 biển**, **bậc thang thử-lại** cho **34 biển**.

Hiệu số **A6 − A5 = 0,7512 − 0,6373 = +11,39 điểm phần trăm** trên **2.801 biển**, kèm chi tiết định tính rất mạnh: **319 sửa đúng, 0 làm hỏng**. Đây **không phải một đánh đổi** mà là **cải thiện thuần một chiều** — các mặt nạ vị trí và ràng buộc mã tỉnh đủ bảo thủ để không tự tạo lỗi mới. Nhưng phải trung thực về **giới hạn**: dù đóng góp gần gấp đôi lượt 20/07 (+6,32 → **+11,39**), cả A5 lẫn A6 vẫn **không đạt** ngưỡng tối thiểu (0,80 và 0,85) — A6 còn thiếu 9,88 điểm.

**Đóng góp phân bố rất không đều giữa hai bố cục**, và chính sự lệch đó nói lên bản chất bộ luật: biển một dòng A5 = 0,9418 → A6 = 0,9541, tức **+1,23 điểm** ứng với **7 biển**; biển hai dòng 0,5600 → 0,6996, tức **+13,97 điểm** ứng với **312 biển**. Trên biển một dòng hậu xử lý gần như không có việc để làm (chuỗi thô đã đúng 94,18%); toàn bộ giá trị dồn vào **biển hai dòng** — bằng chứng định lượng rằng bộ luật **không** chỉ làm đẹp chuỗi mà thực sự bù đắp cho điểm yếu của tầng nhận dạng.

Vì sao vẫn không đủ? Cơ chế áp mặt nạ rồi ánh xạ ký tự đồng hình bất lực trước hai tình huống. **Chuỗi sai nhiều ký tự cùng lúc:** chỉ 1.251 / 2.234 biển hai dòng — **56,0%** — đọc đúng trước hậu xử lý (6.5.3); khi bộ nhận dạng đọc hỏng cả cụm thì không luật thay-ký-tự nào cứu được, và **697 biển sai cả trước lẫn sau** chính là quần thể này. **Ký tự chưa từng được đọc ra thì không luật nào phục hồi được** — ràng buộc nguyên tắc, không phải khiếm khuyết cài đặt: với $D$ = 1.272 (56,8% toàn bộ lỗi sau khi $I$ giảm 88%), nhiều chuỗi ngắn hơn độ dài mong đợi khiến mặt nạ lệch pha và luật khi đó **không dám sửa** chứ không sửa bừa — con số **0 biển bị làm hỏng** là hệ quả quan sát được của thiết kế bảo thủ đó.

Kết luận đúng phạm vi cho RQ3: *khối hậu xử lý đóng góp **+11,39 điểm** trên 2.801 biển — **+13,97 điểm riêng trên biển hai dòng** — là cải thiện thuần không rủi ro (319 / 0), nhưng không đủ đưa A6 tới ngưỡng vì phần lỗi còn lại đã dịch sang dạng **đọc hụt ký tự**, nơi hậu xử lý theo luật về nguyên tắc không với tới được.* Rất ít công trình ALPR đo tách bạch đại lượng này; ở đây nó được lượng hoá cùng chứng cứ về giới hạn của chính nó.

### 6.5.3. Tách theo biển một dòng và hai dòng cho OCR

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

**Đây là kết quả khoa học quan trọng nhất của chương.** Chênh lệch mà tầng phát hiện gần như che khuất (2,09 điểm, Bảng 6.7) nay lộ ra ở tầng OCR với **biên độ khác hẳn cấp**: 5,81 điểm ở mức ký tự, **25,45 điểm** ở A6, **38,18 điểm** ở A5. Nói cách khác **biển một dòng về cơ bản đã giải xong** (A6 = 0,9541 vượt cả mục tiêu 0,90), và toàn bộ việc "OCR không đạt" là do **biển hai dòng kéo xuống**; vì biển hai dòng chiếm **2.234 / 2.801 = 79,8%** tập có nhãn chuỗi (phản ánh tỉ lệ xe máy rất cao trong giao thông Việt Nam), con số tổng bị quần thể khó này chi phối.

**Khoảng cách 25,45 điểm là con số *sau* khi đã áp cả hai bậc cứu chữa** (6.5.6, 6.5.7). Ở lượt 20/07, A6 của biển hai dòng là 0,5810 và khoảng cách là 36,79 điểm — chuỗi biện pháp đã thu hẹp **11,34 điểm**, một dịch chuyển thật nhưng vẫn để lại một phần tư khoảng cách; phần còn lại nằm ở **năng lực nhận dạng ký tự**, không ở khâu cắt/ghép hay hình học, vì cả hai khâu sau đã xử lý và đo tách bạch.

**Mốc tham chiếu quốc tế — phải đọc kèm cảnh báo.** Laroca và cộng sự (VISAPP 2022) báo cáo **94,3%** trên biển một dòng và **45,7%** trên biển hai dòng, chênh **48,6 điểm phần trăm**, đo trên bộ dữ liệu **RodoSol-ALPR của Brazil** [7]<!-- laroca_2022_crossdataset -->. **Đây là số liệu Brazil, không phải Việt Nam**, và biển hai dòng Brazil khác biển hai dòng Việt Nam cả về tỉ lệ khung hình lẫn bộ ký tự. **Đối chiếu bậc độ lớn:** **25,45 điểm** (biển số **Việt Nam thật**, 2.801 biển có nhãn chuỗi) so với **48,6 điểm** trên RodoSol-ALPR **Brazil** — **cùng bậc độ lớn**. Không được kết luận mạnh hơn: 25,45 < 48,6 **không** có nghĩa hệ thống này "tốt hơn", vì hai phép đo khác bộ dữ liệu, khác bộ ký tự, khác tỉ lệ khung hình, khác mẫu số. Kết luận hợp lệ duy nhất: khoảng cách hai layout **thuộc đúng bậc độ lớn** mà tài liệu quốc tế đã ghi nhận — đặc tính có cấu trúc của bài toán, không phải khiếm khuyết riêng của hệ thống.

**Chưa có nghiên cứu Việt Nam nào công bố hai con số này tách bạch trên cùng một hệ thống**; Bảng 6.11 lấp vào khoảng trống đó — lý do mục này không được bỏ dù mẫu số nhỏ — và trả lời trực tiếp RQ2: **có, chênh lệch là có ý nghĩa và rất lớn (25,45 điểm A6), và nó nằm ở tầng OCR chứ không ở tầng phát hiện.**

### 6.5.4. Ma trận nhầm lẫn ký tự 36×36

Mục này trả lời RQ5 với mục đích cụ thể: **thay thế tri thức suy đoán bằng tri thức đo được.** Bảng luật hiện hành trong `ai/inference/plate_rules.py`:

```
TO_DIGIT  = {O→0, Q→0, D→0, I→1, J→1, L→1, Z→2, A→4, S→5, G→6, T→7, B→8}
TO_LETTER = {0→D, 1→L, 2→Z, 3→B, 4→A, 5→S, 6→G, 7→T, 8→B}
```

Docstring của hai hằng số thừa nhận nguồn gốc: *"This table is derived from glyph-shape reasoning, not from measurement"*, và đánh dấu một số cặp (đặc biệt `L→1`) là **phỏng đoán yếu** — trình bày một giả thuyết như giả thuyết chờ kiểm chứng thì trung thực và mạnh hơn là trình bày nó như kết luận đã chốt. Ma trận 36×36 (10 chữ số + 26 chữ cái) đo trên các cặp ký tự đã căn chỉnh là **bằng chứng thực nghiệm** để chuyển giả thuyết đó thành tri thức.

*Hình 6.5.* Ma trận nhầm lẫn ký tự 36×36, thang log(1+n), đo trên chuỗi thô trước hậu xử lý — `04-ocr-confusion-matrix.png` *(chưa sinh)*. *Hình 6.6.* Biểu đồ cột 15 cặp ký tự bị nhầm nhiều nhất — `04-ocr-top-confusions.png` *(chưa sinh)*.

<!-- {{T6.5d}} top cac cap ky tu bi nham thuc te, doi chieu bang luat hien hanh -->

**Bảng 6.12.** Các cặp ký tự bị nhầm nhiều nhất, đối chiếu bảng luật hiện hành

| Hạng | Ký tự thật → bị đọc thành | Số lần | Tỉ lệ trong tổng lỗi thay thế | Bảng luật hiện có phủ cặp này không? |
|:---:|:---:|---:|---:|---|
| 1 | L → 1 | 90 | 10,44% | có (`TO_DIGIT`) — đúng chiều |
| 2 | E → F | 73 | 8,47% | không |
| 3 | 4 → L | 53 | 6,15% | không |
| 4 | U → 1 | 38 | 4,41% | không |
| 5 | D → 0 | 34 | 3,94% | có (`TO_DIGIT`) — đúng chiều |
| 6 | Z → 7 | 32 | 3,71% | không |
| 7 | 2 → 7 | 26 | 3,02% | không |
| 8 | X → Y | 21 | 2,44% | không |
| 9 | B → R | 20 | 2,32% | không |
| 10 | 9 → 0 | 19 | 2,20% | không |

> Ma trận 36×36, mẫu số 2.801 biển có nhãn chuỗi, tổng lỗi thay thế $S$ = 862 (cột tỉ lệ lấy $S$ làm mẫu số).

**RQ5 được trả lời theo hướng ít ai ngờ: bảng luật hiện hành phần lớn *không khớp* với các cặp nhầm thật.** Chỉ **2/10** cặp nhầm nhiều nhất được phủ; **8 cặp còn lại chưa có luật nào phủ** — đáng chú ý `E→F` (73 lần), `4→L` (54 lần), `U→1` (38 lần), đều là các cặp **suy đoán hình dạng không dự đoán được**, phát sinh từ đặc thù phông chữ biển số và điều kiện ảnh thật. Ngược lại, bảy cặp *có* trong bảng luật lại có **số lần quan sát bằng 0** và đều thuộc diện *xem xét loại*: `D→0`, `J→1`, `A→4`, `T→7`, `B→8` (`TO_DIGIT`) và `2→Z`, `3→B` (`TO_LETTER`).

> **Hai chiều của cùng một cặp glyph.** `L → 1` (ký tự thật L bị đọc thành chữ số 1) quan sát **90 lần**; nhưng chiều ghi trong `TO_DIGIT` là "khi engine đọc ra `L` tại vị trí chữ số thì đổi `L → 1`" — chiều này chỉ khớp **2 lần**. Bất đối xứng ấy đúng chứ không phải lỗi: bảng luật sửa ký tự *engine đọc ra*, ma trận nhầm lẫn đếm ký tự *thật bị đọc sai*. Danh sách đề xuất hiệu chỉnh đầy đủ ở khoá `doi_chieu_bang_luat.proposed_updates` trong `05-results.json`.

Bất đối xứng của ánh xạ cần nhấn mạnh: `O → 0` hợp lệ tại vị trí chữ số, nhưng `0 → O` **không bao giờ** hợp lệ vì `O` không phải chữ cái sê-ri hợp pháp; khi loại cả `O` và `Q` thì ứng viên đồng hình duy nhất ở vị trí chữ cái là `D`, nên chiều đúng là `O → 0` tại vị trí chữ số và `0 → D` tại vị trí chữ cái. Ma trận chỉ đếm tần suất; chuyển từ tần suất sang luật vẫn cần **ràng buộc miền** từ quy chuẩn biển số. **Tiêu chí chấp nhận một cặp vào bảng luật đã hiệu chỉnh** (định trước để tránh chọn theo kết quả): (1) tần suất vượt một ngưỡng thống kê tối thiểu; (2) chiều ánh xạ **tương thích với ràng buộc vị trí** của định dạng biển số Việt Nam; (3) áp vào toàn tập cho **đóng góp thuần không âm** ở Bảng 6.10. Không thoả cả ba thì loại, **kể cả khi nghe có vẻ hợp lý về hình dạng chữ**; việc loại bỏ phải ghi vào Chương 7 như một hạn chế đã được sửa chứ không phải thất bại được giấu.

### 6.5.5. Độ chính xác đầu-cuối toàn trình (NFR-A7)

NFR-A7 đo **ảnh đầu vào → phát hiện → cắt → OCR → hậu xử lý → chuỗi cuối**; khác A6 ở chỗ A6 đo trên **vùng biển cắt chuẩn theo nhãn thật** còn A7 đo trên vùng biển do **chính bộ phát hiện** tìm ra, nên A7 tích luỹ cả hai nguồn sai số và theo lý thuyết luôn ≤ A6.

<!-- {{T6.5e}} do chinh xac E2E toan trinh NFR-A7 -->

**Bảng 6.13.** Độ chính xác đầu-cuối toàn trình (NFR-A7)

| Chỉ số | Ngưỡng tối thiểu | Mục tiêu | **Đo được** | Kết quả |
|---|---:|---:|---:|:---:|
| Độ chính xác E2E (NFR-A7) | 0,82 | 0,88 | **0,5552** | ❌ không đạt |
| E2E **với điều kiện đã phát hiện được biển** | — | — | 0,6306 | n/a |
| Tỉ lệ biển **bị bỏ sót** ở tầng phát hiện | — | — | 0,1196 | n/a |
| Phát hiện đúng nhưng **đọc sai chuỗi** *(mẫu số riêng: số biển đã phát hiện được)* | — | — | 0,3694 | n/a |
| Chênh lệch A6 − A7 (phần mất do tầng phát hiện) | — | — | 19,60 | n/a |
| **Số mẫu** | — | — | **2.801** | n/a |

> ⚠ **Cảnh báo hiệu lực — phải đọc trước khi diễn giải A7.** Con số 0,5552 đo trên **ảnh crop biển số**, không phải ảnh hiện trường, vì không bộ dữ liệu nào trong đồ án có đồng thời ảnh toàn cảnh *và* chuỗi biển số nhãn thật. Bộ phát hiện được huấn luyện trên ảnh giao thông đầy đủ nên ảnh chỉ có biển số chiếm gần hết khung là **ngoài phân bố huấn luyện**: phần lớn thất bại ở đây do bộ phát hiện không bắt được box trên ảnh crop (bỏ sót 11,96%), **không** phải do OCR đọc sai. Bằng chứng: trên ảnh hiện trường thật, Phase 7 đo mAP@0.5 = 0,9829, tương thích với Bảng 6.6. Muốn đo NFR-A7 đúng cách cần gán nhãn chuỗi cho một phân bố test có ảnh hiện trường (ví dụ một phần yolo_v2) — **việc này chưa làm.**

**A7 không đạt, nhưng nguồn lỗi được phân tách rõ:** 11,96% biển **bỏ sót** ở tầng phát hiện (335 / 2.801), và trong số đã phát hiện được, 36,94% **đọc sai chuỗi**; chênh A6 − A7 = 19,60 điểm là phần mất khi chuyển từ vùng cắt chuẩn sang vùng do hệ thống tìm ra. Do cảnh báo hiệu lực, **tỉ lệ bỏ sót 11,96% bị thổi phồng bởi việc đo trên ảnh crop ngoài phân bố**. Kết luận đúng phạm vi: *A7 = 0,5552 phản ánh giới hạn của **giao thức đo hiện có** chồng lên giới hạn thật của tầng OCR trên biển hai dòng; đây là **cận dưới bi quan**, không phải ước lượng điểm.* Dòng "với điều kiện đã phát hiện được biển" tồn tại để phân tách hai nguồn lỗi: chỉ tăng recall bộ phát hiện cũng không đưa A7 lên quá 0,6306 — trần thật vẫn bị chặn bởi tầng OCR.

**Vì sao A7 tăng chậm hơn A6.** Mọi biện pháp cứu chữa đều áp vào **cả hai** đường đo, nhưng bị **pha loãng** ở A7 vì 11,96% số biển thất bại ngay ở tầng phát hiện, không bao giờ tới được khối OCR — phần cải thiện chỉ có chỗ tác động trên 88,04% mẫu còn lại. Con số tách bạch chứng minh: giữa lượt 20/07 và 28/07, **`missed_by_detector` giữ nguyên đúng 335 và tỉ lệ phát hiện giữ nguyên đúng 0,8804** — bộ trọng số phát hiện không đổi, nên toàn bộ mức tăng của A7 đến từ khối nhận dạng, và đại lượng đo đúng mức tăng ấy là độ chính xác có điều kiện: 0,6014 → **0,6306**, tức **+2,92 điểm**. A7 tăng ít hơn (+2,57 điểm) chỉ vì đã bị 335 ca vô vọng kéo xuống — hệ quả số học, **không** phải dấu hiệu sai sót.

### 6.5.6. Bước "cứu dòng trên" cho biển hai dòng — thiết kế, kiểm chứng A/B và kết quả trên toàn tập

Hồ sơ lỗi thiên về *xoá* ($D$ = 1.272 > $S$ = 862) trên biển hai dòng có cách giải thích tự nhiên: **mất hẳn một dòng**, chứ không phải đọc nhầm lẻ tẻ. Cách xử lý biển hai dòng của hệ thống là **ghép-rồi-đọc** (*split-then-hstack*): cắt vùng biển thành hai nửa chồng lấn, xếp cạnh nhau thành dải ngang, chạy OCR **một lần**. Phương án thay thế hiển nhiên — đọc riêng từng nửa rồi nối chuỗi — đã được đo A/B chứ không bị loại bằng lập luận.

<!-- {{T6.5f}} A/B hai chien luoc doc bien hai dong -->

**Bảng 6.14.** So sánh A/B hai chiến lược đọc biển hai dòng

| Chiến lược | Số biển đúng / 200 | Độ chính xác | Số ca OCR trả chuỗi rỗng | Thời gian trung bình (ms) |
|---|---:|---:|---:|---:|
| **A — ghép hai nửa rồi OCR một lần** *(đang dùng)* | **129** | **64,50%** | 2 | 340,11 |
| B — OCR từng nửa rồi nối chuỗi | 7 | 3,50% | 9 | 391,35 |
| **Chênh lệch (B − A), điểm phần trăm** | — | **−61,00** | — | +51,24 |

> Mẫu 200 biển hai dòng, `seed = 20260720`, nguồn `datasets/annotations/plate_text_labels_vn.csv`. Số ca A thắng B: **122**; số ca B thắng A: **0**. Tệp: `docs/reports/15-two-line-ab.json`.

**Giả thuyết "đọc riêng từng dòng thì chính xác hơn" bị bác bỏ dứt khoát, biên 61 điểm và 0 ca thắng ngược.** Nguyên nhân đọc được ngay trong dữ liệu: hai nửa **cố ý chồng lấn** để không cắt cụt ký tự, nên khi đọc riêng thì dải chồng lấn bị đọc **hai lần** và ký tự bị nhân đôi — biển `84G122593` thành `84-G124E009.01225.93`. Một kết quả âm có giá trị: lựa chọn kiến trúc ở Chương 5 không tuỳ tiện.

Dải ghép vẫn có chế độ thất bại riêng: khi **dòng trên nằm lệch thấp** trong vùng cắt rộng rãi, bộ dò chữ chỉ tìm thấy **một vùng văn bản** — dòng dưới — và mã tỉnh cùng chữ cái sê-ri **mất hoàn toàn** (`29E-015.66` → `015.66`, năm chữ số trần không khớp định dạng nào nên khối kiểm tra hợp lệ **bác bỏ đúng**); chính sự bác bỏ đó là tín hiệu dùng được. Bước **cứu dòng trên** (`rescue_two_line_upper` trong `ai/inference/pipeline.py`) có cổng rất hẹp: (1) chỉ kích hoạt khi **cả ba** điều kiện đồng thời đúng — `line_count = 2`, chuỗi sau chuẩn hoá **không hợp lệ định dạng**, chuỗi thô **không rỗng**; (2) đọc **riêng nửa trên** bằng một lời gọi OCR bổ sung; (3) nối `nửa trên + chuỗi thô của dải ghép` rồi cho qua lại khối chuẩn hoá; (4) **chỉ giữ kết quả mới nếu nó hợp lệ định dạng**, mọi trường hợp khác — kể cả ngoại lệ — trả về nguyên kết quả cũ. Điều kiện (1) khiến bước này **về mặt cấu trúc không thể làm hỏng** một biển vốn đã đọc đúng: con số 0 ở cột "bị làm hỏng" là **hệ quả của thiết kế**, không phải may mắn thống kê.

<!-- {{T6.5g}} A/B buoc cuu dong tren, hai mau doc lap -->

**Bảng 6.15.** So sánh A/B bước cứu dòng trên trên hai mẫu độc lập

| Mẫu | Chỉ *ghép* (A) | Ghép **+ cứu dòng trên** (C) | Chênh (điểm %) | Số biển được cứu | Số biển bị hỏng | Tỉ lệ kích hoạt | Thời gian TB (ms) |
|---|---:|---:|---:|---:|---:|---:|---:|
| 700 biển, `seed = 7` | 421 / 700 = **60,14%** | 434 / 700 = **62,00%** | **+1,86** | 13 | **0** | 21,14% (148/700) | 362,41 → 383,52 |
| 200 biển, `seed = 20260720` | 129 / 200 = **64,50%** | 130 / 200 = **65,00%** | **+0,50** | 1 | **0** | 18,00% (36/200) | 346,70 → 361,97 |

> Tệp: `docs/reports/15-two-line-fallback-700.json` và `15-two-line-fallback.json`. Hai mẫu dùng **seed khác nhau** nên là hai lượt lấy mẫu độc lập.

**Dấu của hiệu số nhất quán trên cả hai mẫu và không mẫu nào có ca bị làm hỏng**, đúng dự đoán từ cấu trúc cổng kích hoạt; nhưng **độ lớn không nhất quán** (+1,86 so với +0,50) — với mẫu 200 biển, một biển được cứu đã bằng 0,5 điểm nên +0,50 nằm hoàn toàn trong dao động lấy mẫu và **không được dùng làm bằng chứng độc lập**, nó chỉ xác nhận *không có hồi quy*. Chi phí: bước cứu kích hoạt trên khoảng một phần năm số vùng cắt hai dòng — chỉ trên những vùng vốn đã thất bại — đổi lấy khoảng **21 ms** mỗi biển.

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
| Số biển bị can thiệp / thành đúng hoàn toàn / bị làm hỏng | — | **89 / 2.801** · **49** · **0** | — | — | n/a |

> Nguồn: `docs/reports/16-ocr-accuracy-rescued.json`, đo 2026-07-20 trên máy rảnh, `models/best.pt`, `imgsz = 640`, 2.801 ảnh có nhãn chuỗi; cột "trước" là lượt đo trước đó trên đúng cùng tập mẫu và cùng mô hình.
>
> ⚠ **Đây là bảng A/B lịch sử, giữ nguyên số ngày 20/07.** Nó trả lời đúng một câu hỏi — *riêng bước cứu dòng trên đóng góp bao nhiêu* — và câu trả lời ấy không đổi theo thời gian. Nhưng **các giá trị tuyệt đối đã bị vượt qua**: A6 hiện là 0,7512 chứ không phải 0,6730. Không được trích cột "sau bước cứu" như số hiện hành (số hiện hành ở Bảng 6.10 và 6.5.7). Trên lượt 28/07, bước cứu dòng trên cung cấp câu trả lời cuối cho **209 biển**.

**Ba ô "không đổi" phải đọc như bằng chứng, không như thiếu sót.** *A5 không đổi là đúng thiết kế:* bước cứu chạy **sau** khối chuẩn hoá nên **không thể** tác động lên chỉ số đo *trước* chuẩn hoá — nếu A5 xê dịch thì đó mới là dấu hiệu phép đo bị lệch. *Biển một dòng không đổi là đúng:* cổng yêu cầu `line_count = 2`, toàn bộ 89 biển can thiệp đều là biển hai dòng. *Số bị làm hỏng bằng 0 là đúng:* chuỗi đã hợp lệ không bao giờ được thử lại. Tác dụng thật nằm đúng nơi được nhắm — **biển hai dòng, +2,20 điểm** — và vẫn để lại **bốn chỉ tiêu OCR đều không đạt**: một cải thiện, không phải một lời giải.

**Ghi chú phương pháp đo — một lỗi có giá trị học thuật, được ghi lại thay vì giấu đi.** Lượt đo lại **đầu tiên** sau khi thêm bước cứu cho kết quả tự mâu thuẫn: **A6 tăng 1,75 điểm trong khi A7 đứng yên ở đúng 0,5227**. A7 **bao hàm** toàn bộ phần A6 đo, nên một biện pháp đang thực sự chạy **không thể** nâng chỉ số con mà để chỉ số bao hàm nó bất động ở từng chữ số thập phân — xác suất để 49 biển được sửa đúng ở nhánh A6 mà **không một biển nào** đi trọn đường E2E là quá nhỏ. Nguyên nhân: trong `ai/evaluation/ocr_accuracy.py`, bước cứu mới chỉ nối vào nhánh A5/A6, còn **hàm dựng đường E2E vẫn gọi thẳng bộ chuẩn hoá rồi trả kết quả** — con số A7 đang mô tả một hệ thống **ngắn hơn** hệ thống thật. Nối xong và đo lại, A7 mới lên 0,5295. **Đây là lần thứ hai cùng một loại lỗi**; lần thứ nhất ở chính nhánh A5/A6, và cả hai lần triệu chứng đều là một chỉ số **đứng yên một cách vô lý** — một con số không đổi thì dễ được cho qua hơn nhiều so với một con số sai.

> Khi chỉ số $X$ **bao hàm** chỉ số $Y$ về mặt định nghĩa, mà một can thiệp làm $Y$ dịch chuyển còn $X$ thì không nhúc nhích, **giả thuyết đầu tiên phải là đường đo của $X$ bị lệch khỏi đường chạy thật**, chứ không phải "can thiệp không có tác dụng ở mức toàn trình". Chỉ được kết luận vế thứ hai sau khi đã đối chiếu mã của hai đường đo.

**Biện pháp đặt ra khi đó đã thất bại, và lần thứ ba chứng minh vì sao.** Biện pháp là viết bước cứu thành **hàm tự do dùng chung** (`should_rescue_two_line`, `rescue_two_line_upper`) thay vì phương thức riêng của lớp pipeline. Ngày 28/07/2026, **đúng loại lỗi ấy xuất hiện lần thứ ba**: bậc thang thử-lại (6.5.7), thêm vào pipeline ngày 21/07, **chưa bao giờ được kịch bản đánh giá gọi** ở cả hai nhánh, nên mọi con số A4–A7 công bố từ 21/07 đến 28/07 mô tả một pipeline ngắn hơn bản giao hàng. Điều đáng nói: bậc thang **đã** được viết đúng như biện pháp quy định (`should_retry_skewed`, `retry_skewed_variants` là hàm tự do dùng chung) — biện pháp được tuân thủ đầy đủ, và lỗi vẫn tái diễn, vì nó giải quyết sai vấn đề: hàm dùng chung chỉ bảo đảm **nếu** kịch bản gọi thì gọi đúng bản cài đặt, chứ **không** bảo đảm kịch bản có gọi hay không. Nguyên nhân gốc là **kịch bản đánh giá dựng lại đường xử lý thay vì gọi nó**: `measure_crops` và `_run_pipeline` lần lượt liệt kê các bước — nhận dạng, chuẩn hoá, cứu dòng trên — nên mỗi bậc mới thêm vào `ALPRPipeline._process_one` đều **mặc định rơi ra ngoài phép đo**, im lặng.

> Một đường đo **liệt kê lại** các bước của hệ thống sẽ lệch khỏi hệ thống ở đúng thời điểm hệ thống thay đổi — tức đúng thời điểm phép đo cần chính xác nhất. Chia sẻ mã ở mức *hàm* không đủ; chỉ **gọi thẳng cùng một điểm vào** mới đủ. Biện pháp "viết thành hàm dùng chung" đã được tuân thủ và vẫn thất bại, nên nó là bằng chứng thực nghiệm cho luận điểm này chứ không phải phản ví dụ.

Lần này, ngoài việc nối bậc thang vào cả hai nhánh đo, hai chốt chặn được thêm: kịch bản ghi thẳng **trạng thái các công tắc** vào tệp kết quả, và ghi **số biển mà từng bậc cứu được** (`recovery_contribution`) — một bậc không được gọi giờ hiện ra dưới dạng số 0 có nhãn thay vì biến mất không dấu vết. Biện pháp triệt để — cho harness đầu-cuối gọi thẳng `ALPRPipeline.process` — vẫn là **việc bỏ ngỏ**, ghi ở mục 6.10.

### 6.5.7. Bậc thang thử-lại cho biển nghiêng/méo — chi phí, lợi ích và một quyết định tắt tính năng

Chế độ thất bại thứ hai: **biển bị nghiêng hoặc méo phối cảnh**, khiến tỉ lệ khung hình lệch đủ để bộ phân loại bố cục xếp nhầm, hoặc khiến ký tự dính vào nhau. Bậc thang thử-lại xử lý bằng ba biến thể theo thứ tự giả thuyết rẻ trước: **nắn hình trong mặt phẳng**, **giãn dọc chống méo phối cảnh**, **siêu phân giải** cho vùng cắt quá nhỏ. **Điểm mấu chốt là cổng kích hoạt, không phải các biến thể:** hình học từng được đo ở dạng *luôn bật* và kết quả là **mất** — 42 lần đọc hợp lệ tụt xuống 40, vì một hình chữ nhật khớp sai trên vùng cắt nhỏ và mờ sẽ cắt cụt ký tự của một biển vốn đang đọc tốt. Đặt nó **sau cổng "lần đọc đầu đã thất bại"** đảo ngược kinh tế học: đường đi của biển đọc đúng **không bị chạm tới về mặt cấu trúc**, mọi ca cứu được là lãi ròng, biến thể đọc tệ hơn bị tiêu chí hợp lệ loại bỏ — cùng hợp đồng chống thoái lui với bước cứu dòng trên. Độ chính xác dưới đây đo trên 2.801 biển có nhãn chuỗi; độ trễ đo trên 100 ảnh hiện trường của tập test v3, máy rảnh.

<!-- {{T6.5i}} chi phi - loi ich cua tung bac trong bac thang thu-lai -->

**Bảng 6.17.** Chi phí và lợi ích của từng bậc trong bậc thang thử-lại

| Cấu hình | 1 − CER (A4) | A6 | Biển được cứu | p95 (ms) | p99 (ms) |
|---|---:|---:|---:|---:|---:|
| Tắt hẳn bậc thang | 0,9416 | 0,7437 | 0 | **866,3** | 1.101,1 |
| **Nắn hình / giãn dọc** *(cấu hình giao hàng)* | **0,9454** | **0,7512** | **34** | **1.110,4** | 1.349,0 |
| Thêm siêu phân giải | 0,9454 | 0,7512 | 34 | **1.428,7** | **2.730,4** |

> Nguồn: `docs/reports/27-ocr-accuracy-with-ladder.json` và ba lượt `ai.evaluation.benchmark_system` bóc tách qua `ALPR_RECTIFY_ENABLED` / `ALPR_SR_RETRY_ENABLED`. Phân tích đầy đủ: `docs/reports/27-retry-ladder-cost-benefit.md`.

**Bậc thang gần như miễn phí ở trường hợp thường và rất đắt ở đuôi:** trung vị chỉ tăng 3,7% (405,8 ms) trong khi p99 tăng 148%. **Nắn hình / giãn dọc: giữ** — mua 34 biển (+0,75 điểm A6, +0,38 điểm A4) với giá +244 ms ở p95, chấp nhận được cho một cơ chế không thể làm hỏng kết quả đang đúng. **Siêu phân giải: tắt mặc định** — mua **0 biển** với giá **+319 ms ở p95 và +1.381 ms ở p99**, và một mình nó đẩy NFR-P1 vượt ngưỡng tối thiểu 1.500 ms.

**Vì sao số 0 của siêu phân giải không phải bằng chứng nó vô dụng.** Cổng của bậc này chỉ mở cho vùng cắt có cạnh dài **≤ 200 px**. Đo trên 120 mẫu ngẫu nhiên của tập có nhãn chuỗi, cạnh dài sau bước khôi phục tỉ lệ khung hình có **giá trị nhỏ nhất 565 px, trung vị 868 px**: **0/120 mẫu lọt cổng**. Ngữ liệu này **không thể kích hoạt** nên **không thể đo** bậc siêu phân giải — số 0 trong bảng là **số 0 cấu trúc**, không phải kết quả âm. Suy ra: toàn bộ 34 biển cứu được đều là công của nắn hình / giãn dọc; và quyết định tắt **không** dựa trên "đã đo và thấy vô dụng".

> Chi phí đã đo được và lớn; lợi ích **chưa ai đo được** trên bất kỳ tập đại diện nào; trong khi NFR-P1 là yêu cầu mức *Must* và riêng bậc này làm nó vượt ngưỡng. Một lợi ích chưa định lượng không đủ để biện minh cho một vi phạm đã định lượng.

Bằng chứng duy nhất hiện có cho bậc siêu phân giải vẫn là **một vùng cắt demo được chọn tay trong bốn ca thử**. Mã, kiểm thử, công tắc và báo cáo **giữ nguyên**; `ALPR_SR_RETRY_ENABLED=true` là bật lại. Muốn đo cho tử tế cần một tập **vùng cắt nhỏ do chính bộ phát hiện sinh ra, có nhãn chuỗi** — đồ án không có, và đó là hạng mục bỏ ngỏ ghi ở 6.11.

---

## 6.6. Đánh giá hiệu năng

> Mọi số trong 6.6 phải đọc cùng Bảng 6.1: **Intel Raptor Lake 14 nhân / 20 luồng, Windows 11, CPU-only, kích thước lô = 1**.

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
| Bội số so với ngưỡng tối thiểu / mục tiêu | — | — | 0,49× / 0,91× | **0,76×** / **1,43×** | n/a |

*Hình 6.7.* Phân bố độ trễ đầu-cuối — biểu đồ tần suất kèm vạch p50/p95/p99 và hai ngưỡng chỉ tiêu — `07-latency-distribution.png` *(đã có, cần vẽ lại cho `best.pt`)*.

> Số biển trung bình mỗi ảnh: 1,33, cùng 100 ảnh test v3, cùng máy rảnh (CPU idle ~5%, không có tiến trình huấn luyện song song). **Hai cột đo hai phiên bản hệ thống, không phải hai phương pháp đo**: cột trái là trạng thái 20/07 trước khi có bậc thang (đo client-side qua HTTP, `07-benchmark-p1-resolved.json`); cột phải là cấu hình giao hàng 28/07 (đo in-process bằng `benchmark_system.py`, `05-results.json`). Chênh lệch phương pháp giữa hai cách đo là **~7%** — đã kiểm chứng ngày 20/07 khi cả hai cùng chạy trên một hệ thống (731,15 so với 780,36 ms) — nên nó **không** giải thích được mức tăng ở đây.

**NFR-P1 đạt ngưỡng tối thiểu nhưng không đạt mục tiêu**, và đây là một **thoái lui có chủ ý và đã định lượng**. Nguyên nhân là bậc thang thử-lại (6.5.7): tắt hẳn nó đưa p95 về **866,3 ms**, tức toàn bộ +277 ms là của nó; nhưng vì bậc thang chỉ chạy **sau khi lần đọc đầu thất bại** nên nó không chạm vào trường hợp thường — **trung vị thậm chí giảm nhẹ** (414,67 → 405,77 ms), chi phí dồn hết vào đuôi phân phối. Với hệ thống mà 95% ảnh xong dưới 1,15 giây và một nửa xong dưới 0,41 giây, p50 mô tả trải nghiệm điển hình còn p95 mô tả trường hợp xấu; NFR-P1 phát biểu theo p95 nên kết luận chính thức là **đạt sàn, không đạt mục tiêu**. Ở lượt đo đầu với cả ba biến thể bật, p95 là **1.514,26 ms** — **vượt cả ngưỡng tối thiểu**; bóc tách chỉ ra bậc siêu phân giải chiếm hơn nửa chi phí đó mà không mua được biển nào đo được nên nó bị **tắt mặc định**, đưa p95 về 1.143,10 ms — một đánh đổi được cân bằng bằng số đo, không phải giá trị tình cờ.

**Giải quyết mâu thuẫn với con số cũ 5.857 ms.** Báo cáo Phase 7 trước đây ghi p95 = 5.857,19 ms và kết luận NFR-P1 "không đạt" — chênh **7,5 lần**. Phép đo cũ đã bị **bác bỏ**: (1) **nhiễu do tranh chấp CPU** — `07-benchmark-data.json` ghi rõ có tiến trình `ai.training.train` chiếm 793% CPU chạy song song, và chính báo cáo cũ khi tính lại trên 80 mẫu ít nhiễu đã ra ~3.283 ms; (2) đo trên **checkpoint epoch 7**, không phải `best.pt`; (3) checkpoint đó có **lỗi crop** khiến PaddleOCR chạy cả khối phát hiện văn bản trên ảnh lớn (~1.322 ms/ảnh). Đo lại trên máy rảnh với `best.pt`: p95 còn 731 ms. Giả thuyết "cold-start / oneDNN chưa tắt" **không** phải nguyên nhân — server chạy `enable_mkldnn=false` và có warmup khi khởi động (cold-start đo được chỉ 176 ms p95); giả thuyết "baseline-416-v1 vốn chậm" cũng bị loại — đo client-side nó ra 763,75 ms p95, gần y hệt `best.pt`.

### 6.6.2. Phân rã ngân sách độ trễ theo từng bước

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

*Hình 6.8.* Biểu đồ cột chồng phân rã ngân sách độ trễ: ước lượng Phase 0 so với số đo thật — `07-latency-budget.png` *(đã có, cần vẽ lại)*.

> Mẫu số: 40 ảnh, trung bình 1,57 biển mỗi ảnh, đo trên `best.pt`. Bước "ghi CSDL + lưu ảnh" giữ `—` vì `benchmark_system` đo pipeline suy luận thuần, không đi qua tầng API; cột chênh lệch ở dòng tổng vì vậy so với ước lượng **cùng phạm vi** (đã trừ bước ghi CSDL), không so với 405 ms tròn.

Mục này đối chiếu **ước lượng ngân sách lập ở Phase 0** — trước khi viết dòng mã suy luận nào — với **số đo thật**, và cho ba phát hiện chi phối phần bàn luận hiệu năng. **Một, ước lượng Phase 0 sát bất ngờ ở tổng nhưng lệch ở phân bổ:** tổng suy luận thuần **168,41 ms/biển**, nhỏ hơn cả ước lượng Phase 0 (405 ms gồm ghi CSDL, ~355 ms nếu trừ) — ước lượng ban đầu **không** sai một bậc độ lớn như con số nhiễu 5.857 ms từng khiến người ta tin. **Hai, nút thắt là PaddleOCR nhưng KHÔNG áp đảo như báo cáo cũ:** 64,3% so với 34,0% của bộ phát hiện, **thay thế** con số cũ "OCR 93,3% / detect 6,5%" vốn đo trên hệ thống đang có lỗi crop (~1.322 ms/ảnh); nguyên nhân OCR đắt vẫn đúng — PaddleOCR là **pipeline nhiều giai đoạn** (phát hiện văn bản → phân loại hướng → nhận dạng) thiết kế cho ảnh tài liệu tổng quát, nên hệ thống đang trả chi phí cho năng lực mà vùng biển đã cắt không cần. **Ba, chiến lược tối ưu đổi hẳn:** theo định luật Amdahl, tăng tốc detector 2–3× có thể kéo E2E xuống quãng **15–23%**, khác hẳn kết luận cũ "chỉ giảm tối đa 6,7%"; và vì NFR-P1 mới đạt sàn còn NFR-P2 trượt cả sàn (2,379 FPS, sàn 3), tối ưu hiệu năng nằm trên đường tới chỉ tiêu chứ không chỉ là *dư địa cải thiện thêm*.

### 6.6.3. So sánh backend suy luận: PyTorch, ONNX Runtime và OpenVINO

<!-- {{T6.6c}} so sanh backend suy luan cho bo phat hien -->

**Bảng 6.20.** So sánh backend suy luận cho bộ phát hiện

| Backend | Chỉ bộ phát hiện p50 (ms) | p95 (ms) | Tăng tốc so với PyTorch | E2E p95 (ms) | Cải thiện E2E (%) | mAP@0.5 sau khi xuất |
|---|---:|---:|---:|---:|---:|---:|
| PyTorch (mốc so sánh) | *(chưa đo)* | *(chưa đo)* | 1,00× | *(chưa đo)* | 0% | *(chưa đo)* |
| ONNX Runtime | *(chưa đo)* | *(chưa đo)* | *(chưa đo)* | *(chưa đo)* | *(chưa đo)* | *(chưa đo)* |
| OpenVINO | *(chưa đo)* | *(chưa đo)* | *(chưa đo)* | *(chưa đo)* | *(chưa đo)* | *(chưa đo)* |

> **Bảng 6.20 chưa đo** — phép so sánh backend (`benchmark_cpu --backends pytorch onnx openvino`) chưa chạy. Cột "mAP@0.5 sau khi xuất" tồn tại để kiểm tra việc chuyển đổi định dạng **không làm suy giảm độ chính xác**; nếu có suy giảm, mức tăng tốc phải được đánh giá như một đánh đổi. Khi đo xong sẽ điền từ `docs/reports/07-benchmark-optimized.json`.

Thí nghiệm này vẫn đáng làm dù kết luận đoán trước được từ 6.6.2: nó **kiểm chứng** lập luận Amdahl bằng số liệu, và cung cấp mức tăng tốc thật của từng backend trên CPU Intel [18]<!-- ultralytics_2026_openvinoexport --> [117]<!-- onnxruntime_2025_threading -->.

> **Tối ưu backend của bộ phát hiện GIỜ có ý nghĩa, nhưng chưa đủ một mình.** Bộ phát hiện chiếm 34,0% tổng thời gian nên tăng tốc 2–3× có thể kéo E2E xuống quãng 15–23% — không còn bị chặn ở 6,7% như báo cáo cũ lầm tưởng. Và vì NFR-P1 **chỉ đạt sàn** còn NFR-P2 **trượt sàn**, đây không phải dư địa cải thiện thêm mà là đường dẫn tới chỉ tiêu. Muốn giảm mạnh hơn thì khối OCR (64,3%) vẫn là mục tiêu lớn nhất.

Bốn hướng tấn công khối OCR, xếp theo chi phí tăng dần (triển khai chi tiết thuộc Chương 7): **tắt các giai đoạn không cần thiết của pipeline PaddleOCR** (vùng biển đã cắt sẵn nên giai đoạn phát hiện văn bản gần như thừa, giai đoạn phân loại hướng cũng bỏ được nếu vùng cắt đã nắn); **bật MKL-DNN và chỉnh số luồng CPU** cho backend PaddlePaddle; **xuất mô hình nhận dạng sang ONNX Runtime** để bỏ phụ thuộc runtime PaddlePaddle; **thay bằng mô hình nhận dạng chuyên cho biển số**, huấn luyện trên tập ký tự hẹp (10 chữ số + tập chữ cái hợp lệ) — tiềm năng lớn nhất, tốn công nhất, đã ghi vào phạm vi mở rộng.

### 6.6.4. Chế độ webcam (tầng API) và xử lý video (NFR-P2, NFR-P3)

> Từ 2026-07-20, trang Webcam đã gỡ khỏi giao diện web (thu gọn phạm vi — 4.1.3b); chế độ thời gian thực chỉ còn ở tầng API, nên NFR-P2 đo bằng kịch bản gọi trực tiếp `POST /api/detect/frame`, không qua giao diện.

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
| Bước nhảy khung hình (`vid_stride`) | — | — | — | **5** | n/a |

**NFR-P2 không đạt, và nguyên nhân không phải tốc độ trung bình mà là *đuôi phân bố*.** Trung vị mỗi khung chỉ **180 ms** — tương ứng 5,6 FPS, vượt mục tiêu — nhưng p95 là **1.247,7 ms**, và giao diện thời gian thực dùng **hàng đợi một khe**: chỉ một yêu cầu bay tại một thời điểm, khung sinh ra trong lúc chờ bị bỏ thay vì xếp hàng; ở kỷ luật đó thông lượng bị chi phối bởi những lần chậm nhất. Đuôi ấy chính là bậc thang thử-lại (6.5.7) — một **đánh đổi đã biết chứ không phải bất ngờ**: cùng cơ chế đó mua thêm 34 biển đọc đúng và đẩy NFR-P1 từ ✅ xuống 🟡; NFR-P2 là chỗ thứ hai phải trả giá.

**Định nghĩa đã dùng, nêu rõ để không phóng đại:** "FPS hiệu dụng" là **số khung được nhận dạng xong mỗi giây** (144 khung trong 60,52 giây), không phải số khung hiển thị; camera ảo chào 1.815 khung ở 30 FPS và 1.671 khung bị bỏ — con số bỏ này được báo cáo chứ không giấu, vì công bố riêng "144 khung, 0 lỗi" sẽ khiến người đọc hiểu nhầm là hệ thống theo kịp nguồn. **Con số này là cận trên:** phép đo chạy qua HTTP loopback với ảnh có sẵn trên đĩa nên **không** tính thời gian camera thu hình, mã hoá JPEG trong trình duyệt và vẽ canvas. Dự đoán trước đó trong bản thảo là **~1,4 FPS** (suy từ p95 0,73 giây và giả định xử lý tuần tự); số đo thực **2,379 FPS** cao hơn dự đoán nhưng vẫn dưới sàn 3 FPS — **kết luận của dự đoán đúng dù con số thì lệch**, ghi lại để thấy giới hạn của việc suy diễn từ độ trễ thay vì đo.

### 6.6.5. Chịu tải, bộ nhớ và độ tin cậy (NFR-SC1, NFR-P4…P7, NFR-R4)

<!-- {{T6.6e}} chiu tai, bo nho, do tin cay -->

**Bảng 6.22.** Chịu tải, bộ nhớ và độ tin cậy

| Chỉ số | Mã NFR | Ngưỡng tối thiểu | Mục tiêu | **Đo được** | Kết quả |
|---|:---:|---:|---:|---:|:---:|
| Thời gian nạp mô hình (giây) | NFR-P4 | ≤ 30 | ≤ 15 | **6,41** *(baseline)* | ✅ đạt |
| Khởi động đến khi `/health` sẵn sàng (giây) | NFR-P4b | ≤ 30 | ≤ 15 | **8,36** *(baseline)* | ✅ đạt |
| Overhead của API, p95 (ms) | NFR-P5 | ≤ 100 | ≤ 50 | **19,01** *(baseline)* | ✅ đạt |
| Truy vấn lịch sử 10.000 bản ghi, p95 (ms) | NFR-P6 | ≤ 1000 | ≤ 500 | **18,71** *(baseline)* | ✅ đạt |
| RSS pipeline / RSS máy chủ backend (GB) | NFR-P7a, P7b | ≤ 4 | ≤ 2 | **0,759** / **0,806** | ✅ đạt |
| Số yêu cầu đồng thời xử lý ổn định | NFR-SC1 | ≥ 5 | ≥ 5 | **10** | ✅ đạt |
| Tỉ lệ thành công khi chạy tải liên tục (soak 15 phút) | NFR-R4 | ≥ 99% | ≥ 99% | **100,0% (2.028 yêu cầu)** | ✅ đạt |
| Tăng RSS sau soak 15 phút (GB) | — | không có | không có | **+0,094** *(0,726 → 0,820)* | ✅ không rò rỉ |
| Cơ sở dữ liệu sống sót qua khởi động lại | NFR-R5 | 100% | 100% | **0/9.031 bản ghi mất** | ✅ đạt |

*Hình 6.9.* Đường cong thông lượng và tỉ lệ lỗi theo mức đồng thời 1 / 2 / 5 / 10 — `07-concurrency.png` *(đã có, cần vẽ lại)*.

**Mọi chỉ tiêu hiệu năng *ngoài đường xử lý ảnh* đều đạt với biên rất rộng** — truy vấn lịch sử nhanh hơn mục tiêu ~27 lần, RSS phẳng ở 0,8 GB. **Nhưng hai chỉ tiêu trên chính đường xử lý ảnh thì không:** NFR-P1 chỉ đạt ngưỡng tối thiểu và **NFR-P2 trượt cả sàn**, cùng một nguyên nhân là đuôi độ trễ do bậc thang thử-lại, cùng một đánh đổi có chủ ý: 34 biển đọc thêm. Kết luận hai vế: **kiến trúc phần mềm không còn là vấn đề** — tầng API, tầng dữ liệu, bộ nhớ, độ ổn định đều dư biên; **nhưng *độ trễ suy luận* thì vẫn là vấn đề** và nó ràng buộc trực tiếp năng lực thời gian thực. Hai nhánh đi tiếp tách bạch: nâng *độ chính xác* OCR biển hai dòng (6.5), và cắt *đuôi độ trễ* — đặt trần thời gian cho bậc thang thử-lại, hoặc chỉ chạy nó ở chế độ ảnh tĩnh chứ không ở chế độ thời gian thực.

### 6.6.6. Bỏ bước phát hiện chữ của PaddleOCR: một quyết định suýt sai

Mục 5.4 để ngỏ một câu hỏi: chế độ **chỉ nhận dạng** cho model fine-tune thêm 12,46 điểm A6 và rẻ hơn ~290 ms mỗi ảnh — vì sao không bật? Vì ngữ liệu chứng minh nó **không có thẩm quyền trả lời câu hỏi đó**.

<!-- {{T6.6f}} bo buoc phat hien chu: hai ngu lieu, hai ket luan nguoc nhau -->

**Bảng 6.23.** Bỏ bước phát hiện chữ — hai ngữ liệu, hai kết luận ngược nhau

| Cấu hình | A6 trên 2.801 ảnh **cắt sẵn** | Biển đọc đúng trên bộ demo **ảnh toàn cảnh** |
|---|---:|---:|
| Model gốc, det + rec — *bản giao hàng* | 0,7512 | **17 / 22** |
| Model gốc, chỉ rec | 0,7508 | 13 / 22 |
| Model fine-tune, det + rec | 0,6762 | 14 / 22 |
| Model fine-tune, chỉ rec | **0,8758** | 15 / 22 |

> Nguồn: `docs/reports/29-reconly-ablation.json`, `docs/reports/31-demo-ab-reconly.json`.

**Cột trái và cột phải cho hai thứ tự ngược nhau, và cột phải mới là cột đúng.** Mọi ảnh trong ngữ liệu 2.801 mẫu là bản xuất Roboflow **đã cắt khít quanh biển** — bộ dò chữ đặt vào đó thì không còn gì để khoanh, nên cột trái đọc ra như thể bước phát hiện là thừa. Nhưng vùng cắt mà hệ thống thật sự phải đọc do **YOLO sinh ra từ ảnh toàn cảnh** và lỏng hơn nhiều (dính cản xe, kính chắn gió, nền đường); bỏ bước phát hiện thì bộ nhận dạng đọc luôn phần nền thành ký tự — `TCA7A22104`, `5KB274184` trên `nhieu-bien-2.png`. **Một khác biệt nữa, độc lập với độ chính xác và nghiêm trọng hơn:** chế độ chỉ-nhận-dạng **không có khả năng trả về chuỗi rỗng** — trên 1.606 khung biển do bộ phát hiện sinh ra nó trả chuỗi ở **cả 1.606**, trong khi bản giao hàng trả rỗng ở **173 khung**; khi bộ phát hiện bắt nhầm một tấm biển quảng cáo, bản giao hàng **im lặng** còn chế độ chỉ-rec **bịa ra một biển số**, và với hệ thống ghi vào cơ sở dữ liệu thì bịa nguy hiểm hơn im lặng. **Quyết định: giữ bước phát hiện chữ.** Công tắc `ALPR_OCR_SKIP_DETECTION` được cài đặt, mặc định **tắt**, ghim bằng kiểm thử; không xoá vì hiệu ứng "chỉ-rec giúp model fine-tune, hại model gốc" là thật và có cơ chế rõ ràng — chỉ là 22 biển thì quá ít để đổi cấu hình đem giao.

**Điều kiện để xét lại là một tập ảnh toàn cảnh có nhãn chuỗi — lỗ hổng đó đã được lấp ngày 02/08/2026** ([34-scene-level-a7.md](../reports/34-scene-level-a7.md)): **608 khung biển** trên ảnh hiện trường được gán nhãn chuỗi. Bắt buộc lấy mẫu **phân tầng** vì 1.232/1.606 khung thuộc nhóm bất đồng — dùng riêng nhóm đó sẽ cho con số bi quan sai lệch; tầng đồng thuận được **đếm hết** (372/374) nên sai số chỉ còn đến từ tầng bất đồng.

| Cấu hình | Tầng dễ *(n=372)* | Tầng khó *(n=236)* | **A7** | KTC 95% |
|---|---:|---:|---:|:---:|
| **Gốc + det+rec** — *bản giao hàng* | 96,8% | 44,1% | **56,3%** | [52,0 ; 60,7] |
| Gốc + chỉ rec | 96,8% | 19,9% | 37,8% | [34,3 ; 41,3] |
| Fine-tune + det+rec | 96,8% | 30,9% | 46,3% | [42,2 ; 50,3] |
| Fine-tune + chỉ rec | **94,1%** | 44,5% | 56,0% | [51,7 ; 60,4] |

**Phải phát biểu cho đúng mức.** Bản giao hàng đứng đầu, nhưng chênh với ứng viên gần nhất chỉ **0,3 điểm** và hai khoảng tin cậy **chồng gần như hoàn toàn** — về thống kê hai cấu hình đó **không phân biệt được** trên tập này, nên kết luận đúng không phải *"bản giao hàng chính xác hơn"* mà là **"không có bằng chứng để đổi"**; hai cấu hình còn lại thua rõ, nằm ngoài khoảng tin cậy. Cột "tầng dễ" hé lộ điều mà ngữ liệu ảnh cắt sẵn không thấy được: fine-tune + chỉ rec là cấu hình **duy nhất kém đi ở ca dễ** — 94,1% so với 96,8%, tức **10 biển đọc hỏng thêm** trên 372 khung đã đếm hết; nó thắng ở ca khó nhưng đánh mất ca dễ, và đó là lý do lợi thế 12,46 điểm không sống sót ở đường chạy thật.

> **Ghi lại vì đây là lần thứ tư cùng một họ lỗi, và là lần đầu chặn được trước khi vào bản giao.** Ba lần trước — siêu phân giải, công cụ đo bỏ sót bậc thang thử-lại, val acc của fine-tune — đều là lỗi đã mắc rồi mới phát hiện. Lần này phép đo nói "lãi 12,46 điểm" và chỉ vì bộ demo được chạy lại **trước** khi đổi mặc định mới lộ ra rằng nó làm hệ thống **tệ đi 4 biển**. Quy tắc rút ra: *không đổi cấu hình mặc định dựa trên một phép đo mà đầu vào của nó khác đầu vào thật.*

---

## 6.7. Đối chiếu toàn bộ chỉ tiêu phi chức năng

Bảng tổng hợp trình bày khi bảo vệ, liệt kê **đầy đủ mọi mã NFR** đã đặt ra ở Phase 0, không lọc bỏ mã nào — kể cả những mã không đạt. **Ký hiệu:** ✅ đạt mục tiêu · 🟡 chỉ đạt ngưỡng tối thiểu · ❌ không đạt · ⬜ chưa đo · ➖ không áp dụng cho chương này.

<!-- {{T6.7}} doi chieu toan bo chi tieu NFR -->

**Bảng 6.24.** Đối chiếu toàn bộ chỉ tiêu phi chức năng

| Mã | Chỉ tiêu | Ngưỡng tối thiểu | Mục tiêu | **Đo được** | Kết quả | Mục |
|:---:|---|---:|---:|---:|:---:|:---:|
| P1 | Độ trễ E2E một ảnh, p95 | ≤ 1500 ms | ≤ 800 ms | **1.143,10 ms** *(p50 = 405,77 ms)* | 🟡 | 6.6.1 |
| P2 | Tốc độ khung hình webcam (tầng API) | ≥ 3 FPS | ≥ 5 FPS | **2,379 FPS** *(144/1.815 khung, 0 lỗi)* | ❌ | 6.6.4 |
| P3 | Tốc độ xử lý video | ≥ 0,15× | ≥ 0,3× | **0,746×** *(0,546 s/khung phân tích)* | ✅ | 6.6.4 |
| P4 / P4b | Nạp mô hình / khởi động đến khi `/health` sẵn sàng | ≤ 30 s | ≤ 15 s | **6,41 s** / **8,36 s** | ✅ | 6.6.5 |
| P5 | Overhead API, p95 | ≤ 100 ms | ≤ 50 ms | **19,01 ms** | ✅ | 6.6.5 |
| P6 | Truy vấn lịch sử 10.000 bản ghi, p95 | ≤ 1000 ms | ≤ 500 ms | **18,71 ms** | ✅ | 6.6.5 |
| P7a / P7b | RSS pipeline / RSS máy chủ backend | ≤ 4 GB | ≤ 2 GB | **0,759 GB** / **0,806 GB** | ✅ | 6.6.5 |
| A1 | mAP@0.5 của bộ phát hiện | ≥ 0,85 | ≥ 0,90 | **0,9829** | ✅ | 6.4.1 |
| A2 | mAP@0.5:0.95 của bộ phát hiện | ≥ 0,55 | ≥ 0,65 | **0,7834** | ✅ | 6.4.1 |
| A3 | Precision / Recall phát hiện | ≥ 0,88 / 0,85 | ≥ 0,92 / 0,90 | **0,9837 / 0,9714** | ✅ | 6.4.1 |
| A4 | Độ chính xác OCR mức ký tự (1 − CER) | ≥ 0,92 | ≥ 0,95 | **0,9454** | 🟡 | 6.5.1 |
| A5 | Chuỗi đầy đủ **trước** hậu xử lý | ≥ 0,80 | ≥ 0,85 | **0,6373** | ❌ | 6.5.2 |
| A6 | Chuỗi đầy đủ **sau** hậu xử lý | ≥ 0,85 | ≥ 0,90 | **0,7512** | ❌ | 6.5.2 |
| **A6 − A5** | **Đóng góp của khối hậu xử lý** | — | — | **+11,39 điểm** | ✅ | **6.5.2** |
| A7 | Độ chính xác E2E toàn trình | ≥ 0,82 | ≥ 0,88 | **0,563** *(ảnh toàn cảnh; KTC 95% [0,520 ; 0,607])* | ❌ | 6.5.5 |
| A8 | Tách theo layout một dòng / hai dòng | báo cáo tách bạch | — | detection **2,09 điểm**; OCR (A6) **25,45 điểm** | 🟡 | 6.4.3, 6.5.3 |
| A9 | Tách theo điều kiện ảnh | báo cáo nếu có nhãn | — | — | ⬜ | 6.7.1 |
| R1–R3 | Không sập với đầu vào hỏng / độc hại (100%) · ảnh không có biển ⇒ HTTP 200 + danh sách rỗng · tác vụ video lỗi không để lại rác (nguyên tử) | — | — | — | ⬜ | 6.6.5 |
| R4 | Tỉ lệ thành công khi chạy liên tục | ≥ 99% | ≥ 99% | **100% (2.028 yêu cầu, 15 phút)** | ✅ | 6.6.5 |
| R5 | CSDL sống sót qua khởi động lại | 100% | 100% | **0/9.031 bản ghi mất** | ✅ | 6.6.5 |
| SC1 | Số yêu cầu đồng thời xử lý ổn định | ≥ 5 | ≥ 5 | **10** | ✅ | 6.6.5 |
| SC2–SC3 | ≥ 100.000 bản ghi không làm suy giảm hiệu năng · tác vụ video chạy nền, không chặn | — | — | — | ⬜ | 6.6.5 |
| M1, M3–M5 | Mã AI tách biệt khỏi mã API (0 vi phạm) · type hint + docstring cho hàm public (100%) · không hard-code đường dẫn (0 vi phạm) · thay được bộ OCR không sửa mã API | — | — | — | ⬜ | 6.7.2 |
| M2 | Độ bao phủ test tầng nghiệp vụ | ≥ 70% | ≥ 70% | **87,7%** (2026-07-20) | ✅ | 6.7.2 |
| M6 | Tuân thủ lint và định dạng tự động | sạch | sạch | **black 96/96 sạch; ruff còn 83 `E501`** | ⚠️ | 6.7.2 |
| S1–S6 | Magic bytes chặn tệp giả mạo · chống path traversal (100%) · giới hạn kích thước tệp ở server (HTTP 413) · CORS không dùng `*` · không ghi dữ liệu nhạy cảm vào log · truy vấn ORM tham số hoá (0 nối chuỗi SQL) | 0 vi phạm | — | — | ⬜ | 6.7.2 |
| C1, C3, C4 | Chạy được Windows / Linux / macOS qua `docker compose up` · hỗ trợ Chrome, Edge, Firefox · cài đặt từ đầu bằng README ≤ 15 phút | — | — | — | ⬜ | 6.7.2 |
| C2 | Hoạt động không cần GPU | mặc định | — | **có** | ✅ | 6.2.3 |
| U1–U5 | Lượt nhận dạng đầu tiên ≤ 3 click · phản hồi trực quan cho thao tác > 500 ms (100%) · thông báo lỗi tiếng Việt nêu cách khắc phục (100%) · dùng được từ 1366×768 · tương phản WCAG AA ≥ 4,5:1 | — | — | — | ⬜ | 6.7.2 |

### 6.7.1. Ghi chú về NFR-A9 — đánh giá theo điều kiện ảnh

NFR-A9 được phát biểu **có điều kiện** từ Phase 0: *"báo cáo độ chính xác theo điều kiện ảnh (ban ngày / ban đêm / nghiêng / mờ), **nếu bộ dữ liệu có nhãn phù hợp**"*. Bộ v3, hợp nhất từ bảy bộ công khai (còn sáu nguồn nguyên tố sau khử trùng lặp), **không có nhãn điều kiện chụp thống nhất**. Do đó **không** gán nhãn bằng suy đoán (ví dụ dùng độ sáng trung bình để suy ra "ban đêm"), vì nhãn suy đoán tạo ra bảng kết quả trông chặt chẽ nhưng đo một đại lượng không xác định; trạng thái đúng để báo cáo là **NFR-A9 không đánh giá được vì thiếu nhãn**. Phương án thực hiện được nếu có thời gian: gán nhãn thủ công cho một tập con nhỏ (khoảng 200–300 ảnh) đủ làm khảo sát định hướng, và **công bố rõ đó là tập con gán nhãn thủ công**, không phải toàn tập test.

### 6.7.2. Kết quả kiểm thử phần mềm

Nhóm NFR-M, S, C, U kiểm chứng bằng bộ kiểm thử tự động chứ không bằng đo hiệu năng: **1.001 test thu thập, 1.000 pass, 1 xfail, 0 fail, 0 skip**; độ bao phủ **tầng nghiệp vụ 87,7%** (đo 2026-07-20) so với chỉ tiêu ≥ 70% của NFR-M2 — ✅ đạt; độ bao phủ tầng nghiệp vụ đo ở Phase 7 trước đó là **88,1%**, độ bao phủ **toàn kho mã** ở Phase 7 là **42,0%**.

> **Nguồn và mốc đo.** Bốn số đầu từ lần chạy `backend/.venv/Scripts/python.exe -m pytest -q` tại gốc kho ngày 2026-08-02. Độ bao phủ 87,7% là mốc 2026-07-20 trong `docs/reports/13-refactor-result.json` (2.931 câu lệnh / 317 bỏ sót), nơi số test khi ấy là 882/881 — hai con số từ hai lượt chạy khác nhau, nêu tách bạch để người tái lập không bị lệch; cặp **862/861** trong các bản tài liệu trước là lần chạy cũ hơn và đã bị thay thế. **88,1%** và **42,0%** là số đo Phase 7 (`docs/reports/07-testing-report.md`) — cả hai đều là số đo thật ở hai thời điểm khác nhau, giữ nguyên kèm mốc thời gian thay vì chọn một con số rồi xoá con số kia.

Chênh lệch 88,1% ↔ 42,0% (cùng mốc Phase 7) là **có chủ ý**, không phải dấu hiệu kiểm thử thiếu sót: NFR-M2 đặt ngưỡng cho **tầng nghiệp vụ** — nơi chứa logic có thể sai âm thầm (luật hậu xử lý biển số, xác thực đầu vào, thao tác cơ sở dữ liệu) — còn 42,0% toàn kho gồm cả script tiện ích, mã sinh biểu đồ, mã tải bộ dữ liệu, những phần chi phí viết test cao mà rủi ro sai thầm lặng thấp; công bố riêng 88,1% mà không nói mẫu số là một dạng chọn lọc số liệu có lợi. Test `xfail` duy nhất phải được nêu tên khi công bố — nó đánh dấu một hành vi đã biết là chưa đúng và được ghi nhận công khai, không phải test bị vô hiệu hoá để bảng kết quả sạch: `tests/integration/test_api_detection.py::TestErrorBodies::test_a_failed_image_detection_records_the_failed_job`, trong đó `DetectionService._fail_job` gọi `db.rollback()` trước khi ghi bản ghi thất bại còn `_create_job` mới chỉ `flush`, nên dòng job bị huỷ và một lần tải ảnh thất bại hiện **không để lại dòng nào** trong bảng `DetectionJob`.

---

## 6.8. Phân tích lỗi

### 6.8.1. Phân loại các ca sai

Sáu loại lỗi **đầy đủ và loại trừ lẫn nhau** — mỗi ca sai được gán đúng một loại theo thứ tự ưu tiên: **E1 bỏ sót biển** (ảnh có biển nhưng bộ phát hiện không trả hộp nào khớp; tầng phát hiện), **E2 phát hiện nhầm** (hộp ở vùng không phải biển; tầng phát hiện), **E3 nhầm ký tự** (đúng độ dài, sai ký tự; OCR), **E4 thiếu ký tự** (ngắn hơn nhãn thật; OCR / cắt vùng), **E5 thừa ký tự** (dài hơn nhãn thật; OCR / cắt vùng), **E6 sai thứ tự** (đủ ký tự nhưng sắp sai, hầu như chỉ ở biển hai dòng do ghép nhầm chiều; hậu xử lý). E6 đáng chú ý riêng vì nó **chỉ tồn tại do bài toán có biển hai dòng** và là loại lỗi hậu xử lý sửa được triệt để nếu logic ghép dòng đúng.

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

> **Mẫu số của E1 khác mẫu số của E3–E6.** E1 lấy từ lượt đo E2E của Bảng 6.13 trên 2.801 mẫu; tỉ lệ E1 trên mẫu số riêng của nó là **11,96%**, nên hai cột tỉ lệ **cố ý để trống ở dòng E1**. E2 để *(chưa đo)*: số dương tính giả nằm ở Bảng 6.6 và cũng không cùng mẫu số với E3–E6.
>
> **Hai loại lỗi ngoài khung E1–E6:** `empty_read` = 10 (OCR trả chuỗi rỗng) và `mixed` = 151 (một biển vừa thiếu vừa thừa vừa nhầm ký tự) — có trong cài đặt nhưng không có mã E riêng ở 6.8.1; ghi nhận ở đây để tránh ảo giác "các mã E cộng lại đủ 100% số ca sai" (E3+E4+E5+E6 = 536, phần còn lại tới 697 là 151 ca `mixed` và 10 ca `empty_read`).
>
> **So với lượt 20/07, phân bố lỗi đã đổi hình rõ rệt** — tổng ca sai giảm từ 916 xuống 697. Giảm mạnh nhất là `mixed` (277 → 151) và E5 (95 → 18), tức các chuỗi **hỏng về cấu trúc** đã xử lý phần lớn; ngược lại E3 **tăng** (399 → 445) — hiện tượng **phân loại lại** chứ không phải thoái lui, vì một biển trước cho chuỗi sai độ dài (rơi vào `mixed` hoặc E4) nay cho chuỗi đúng độ dài nhưng sai một ký tự; tổng thể vẫn giảm 219 ca sai. Phần lỗi còn lại đã dồn về **nhầm và hụt ký tự đơn lẻ trên biển hai dòng**.
>
> **Nguồn:** khoá `by_line_count.*.error_classes` của `docs/reports/05-results.json` — cùng lượt đo 28/07 với 6.5, tức **đã có** cả bước cứu dòng trên lẫn bậc thang thử-lại.

**Cấu trúc lỗi xác nhận chẩn đoán ở 5.6.3.** Phân bố loại lỗi của hai layout **khác nhau về chất, không chỉ về lượng**: gần như **toàn bộ** lỗi ký tự dồn về biển hai dòng — E3 428/445, E4 **73/73 — tuyệt đối, không một ca nào thuộc biển một dòng**, E5 13/18 — trong khi biển một dòng chỉ sinh 22 ca trên cả ba loại; khớp chính xác với chênh lệch 25,45 điểm A6 ở 6.5.3. Về E6, số ca = **0** trên toàn tập: logic ghép hai dòng hoạt động đúng, không ca nào ghép nhầm chiều — một điểm mạnh nhỏ nhưng thật của bộ luật.

**Bước cứu dòng trên để lại dấu vết đo được ngay trong bảng này.** So với lượt đo trước khi có bước cứu (6.5.6), **E4 giảm mạnh nhất: 217 → 134 ca**, trong khi E3 tăng 376 → 399 và `mixed` tăng 266 → 277: bước cứu nhắm đúng chế độ "mất hẳn dòng trên" nên rút bớt quần thể E4, còn những ca cứu được một phần **chuyển sang** E3 hoặc `mixed` thay vì biến mất — kiểm chứng chéo độc lập cho cơ chế đã mô tả, vì nếu bước cứu chỉ "làm số đẹp lên" thì phân bố sẽ co lại đồng đều chứ không dịch chuyển có hướng. Dù vậy, E4 (**73 ca**) và mức $D$ = **1.272** ký tự bị xoá vẫn cùng trỏ về chế độ thất bại còn lại: OCR đọc **hụt** ký tự trên biển hai dòng — khắc phục ở tầng nhận dạng, không ở hậu xử lý.

### 6.8.3. Các ca điển hình

*Hình 6.10.* Loại E1 — biển bị bỏ sót, ghi rõ kích thước box tương đối và điều kiện ảnh quan sát được — `05-error-e1-missed.png` *(chưa sinh)*. *Hình 6.11.* Loại E3 — nhầm ký tự, hiển thị vùng cắt, chuỗi thô, chuỗi sau hậu xử lý, nhãn thật — `05-error-e3-substitution.png` *(chưa sinh)*. *Hình 6.12.* Loại E6 — sai thứ tự trên biển hai dòng — `05-error-e6-order.png` *(chưa sinh)*. *Hình 6.13.* Ca mà **hậu xử lý làm hỏng** một chuỗi vốn đã đúng — nếu tồn tại ca như vậy, **bắt buộc phải trưng ra**, vì nó là bằng chứng phản biện đối với đóng góp công bố ở 6.5.2; một chương đánh giá chỉ trưng ra các ca hệ thống làm tốt là một chương đã tự loại bỏ khả năng bị kiểm chứng.

---

## 6.9. Bàn luận

### 6.9.1. Những gì đạt được

1. **Bộ phát hiện đạt toàn bộ chỉ tiêu, với biên rộng** (Bảng 6.6), chênh lệch hai layout chỉ 2,09 điểm (Bảng 6.7). Điểm yếu duy nhất được phơi bày trung thực ở Bảng 6.8: dải "rất nhỏ" có mAP@0.5 chỉ 0,8553 — hệ quả đo được của tiêu chí Q6 không đạt.

2. **Khối hậu xử lý đóng góp thuần dương, không rủi ro** (Bảng 6.10): **+11,39 điểm**, 319 sửa đúng / 0 làm hỏng trên 2.801 mẫu — câu trả lời định lượng cho RQ3, đại lượng hiếm khi được đo tách bạch trong tài liệu ALPR, **dồn gần trọn vào biển hai dòng** (+13,97 so với +1,23 điểm). Hai bậc cứu chữa cô lập được bằng đo A/B với **0 ca hồi quy**: **cứu dòng trên 209 biển**, **bậc thang thử-lại 34 biển**.

3. **Biển một dòng về cơ bản đã giải xong** (Bảng 6.11): A6 = 0,9541 vượt mục tiêu 0,90; toàn bộ việc "OCR không đạt" ở con số tổng là do quần thể biển hai dòng (79,8% tập) kéo xuống — phát hiện có định vị rõ ràng, không phải thất bại mơ hồ.

4. **Hiệu năng và kiến trúc phần mềm đều trong ngưỡng.** Mức vượt mục tiêu của NFR-P1 là **cái giá đã định lượng** của bậc thang thử-lại (tắt nó đưa p95 về 866 ms; trung vị không đổi ở 405,77 ms). Mọi chỉ tiêu ngoài đường suy luận đạt với biên rộng; soak 15 phút thành công 100% trên 2.028 yêu cầu, không rò rỉ bộ nhớ; chịu 10 yêu cầu đồng thời so với ngưỡng 5; bao phủ test tầng nghiệp vụ 87,7%, **1.000/1.001 test pass, 1 `xfail`, 0 fail**.

5. **Bản thân tính trung thực của quy trình đánh giá là một kết quả:** 6.3.3 (lập luận vòng tròn trong kiểm chứng rò rỉ), 6.6.1 (bác bỏ con số 5.857 ms bị nhiễm tải), 3.6.1 (ba biến cùng đổi, giải thích vì sao mAP thấp hơn baseline lại đáng tin hơn) và 6.5.6 (phát hiện **ba lần** đường đo chạy một pipeline ngắn hơn pipeline sản phẩm — lần đầu nhờ dấu hiệu "chỉ số bao hàm đứng yên", lần thứ ba nhờ mức chênh đúng bằng 0,0000 trên bốn chữ số thập phân). Lần thứ ba đặc biệt đáng ghi vì nó chứng minh biện pháp phòng ngừa sau lần thứ hai **đã được tuân thủ đầy đủ mà vẫn thất bại**, do nhắm sai nguyên nhân gốc.

### 6.9.2. Những gì KHÔNG đạt được, và vì sao

Hai chỉ tiêu đã **chuyển trạng thái** sau lượt đo lại 28/07, phải nói rõ vì trình bày số cũ sẽ mô tả sai hệ thống hiện tại: **NFR-A4 từ ❌ sang 🟡** (0,8848 → **0,9454**, vượt ngưỡng tối thiểu 0,92); **NFR-P1 từ ✅ sang 🟡** (731 ms → **1.143 ms**, vẫn dưới sàn 1.500 ms nhưng vượt mục tiêu 800 ms) — **thoái lui có chủ ý**, cái giá của bậc thang thử-lại đổi lấy 34 biển. **Ba chỉ tiêu OCR còn lại không đạt, nguyên nhân chung là biển hai dòng:** A5 = **0,6373** thiếu 16,27 điểm so với ngưỡng 0,80; A6 = **0,7512** thiếu 9,88 điểm so với 0,85; A7 = **0,5552** thiếu 26,48 điểm so với 0,82.

> Ba con số trên là kết quả **sau** khi đã áp cả hai bậc cứu chữa và các bản sửa đọc biển hai dòng. So với lượt 20/07, A6 tăng **7,82 điểm** — mức cải thiện lớn nhất của cả đồ án ở tầng nhận dạng, đạt được **không tốn một giây GPU nào**. Nhưng **không chỉ tiêu nào trong ba chỉ tiêu này chuyển sang đạt**: khoảng thiếu còn lại vẫn tính bằng hàng chục điểm ở A5 và A7, gần mười điểm ở A6 — một cải thiện đo được, không phải một lời giải.

Nguyên nhân được xác định **định lượng và có định vị**, không phỏng đoán: trên biển **một dòng** hệ thống đạt hoặc vượt ngưỡng (1 − CER = 0,9925; A6 = 0,9541), toàn bộ khoảng thiếu nằm ở biển **hai dòng** (0,9344; 0,6996) vốn chiếm **79,8%** tập có nhãn chuỗi. Đây là **đặc tính có cấu trúc của bài toán** — khoảng cách 25,45 điểm A6 cùng bậc độ lớn với mốc 48,6 điểm mà Laroca và cộng sự đo trên RodoSol-ALPR Brazil (6.5.3) — chứ không phải lỗi cài đặt sửa nhanh được. **Cấu trúc phần lỗi còn lại chỉ thẳng sang hướng khắc phục:** ký tự chèn thừa gần như biến mất (903 → 107, giảm 88%) trong khi ký tự bị xoá vẫn ở 1.272 và chiếm 56,8% toàn bộ lỗi, tức lỗi đã dịch từ "đọc hỏng cả chuỗi" sang "đọc hụt ký tự"; hậu xử lý theo luật **về nguyên tắc không thể phục hồi một ký tự chưa từng được đọc ra**, nên hướng khắc phục bắt buộc nằm ở **tầng nhận dạng**, không ở hậu xử lý và cũng không ở hình học (đã xử lý và đo tách bạch ở 6.5.7). **Cảnh báo hiệu lực về A7:** con số 0,5552 bị hạ thêm bởi giới hạn giao thức đo (ảnh crop ngoài phân bố huấn luyện của bộ phát hiện) nên phải đọc như **cận dưới bi quan**; lập luận đầy đủ ở **6.5.5**.

| Mã | Lý do chưa đo | Có khắc phục được trong khuôn khổ đồ án không? |
|:---:|---|---|
| NFR-A9 | **Bộ dữ liệu không có nhãn điều kiện ảnh** | Một phần — gán nhãn thủ công cho tập con |
| Bảng 6.20 — so sánh backend | Chưa chạy `benchmark_cpu` | **Có** |
| Bảng 6.10 — phân rã theo nhóm luật | Chưa có cơ chế bật/tắt luật trong `plate_rules.py` | **Có** — cần viết mã |
| Thí nghiệm cô lập biến E1–E3 (mục 3.6.2) | Chi phí ≈ 33 giờ CPU, vượt ngân sách thời gian | **Không** — chuyển sang hướng phát triển |
| ~~Benchmark engine OCR (PaddleOCR ↔ EasyOCR ↔ Tesseract)~~ — hứa ở mục 3.3 | ✅ **Đã chạy 03/08/2026** (mục 3.3.3). PaddleOCR **68,87%** so với EasyOCR 14,28% và Tesseract 10,28% trên 2.801 biển, cùng tầng bao quanh. Quyết định giữ PaddleOCR nay **có căn cứ độ chính xác**, không chỉ lý do kỹ thuật | Không còn |
| So sánh YOLO26n làm đối chứng — hứa ở mục 2.7 | Chưa huấn luyện. Ngân sách CPU dồn hết cho lượt `best.pt` chính thức | **Có** — cần thêm một lượt huấn luyện |

Phân biệt "chưa đo vì chưa tới lượt" (phần lớn khắc phục được) với "không đo được vì thiếu điều kiện" (NFR-A9 thiếu nhãn, A7 thiếu tập hiện trường có nhãn chuỗi) là quan trọng: chỉ nhóm thứ hai mới là hạn chế thật của công trình.

### 6.9.3. Các mối đe doạ đến tính hợp lệ của kết quả

Nguyên tắc: **nêu mối đe doạ, đánh giá mức nghiêm trọng, nói rõ đã làm gì để giảm thiểu — kể cả khi biện pháp giảm thiểu là "không có".**

**(1) Rò rỉ dữ liệu tồn dư không khử được bằng băm tri giác.** *Mức nghiêm trọng: cao.* Ngay ở mức bố cục, Bảng 6.4 cho thấy rò rỉ tồn dư **có thật, đo được**: ngay ngoài vùng bảo vệ của ngưỡng gộp (ngưỡng 10, cho 0 cặp theo định nghĩa), tại Hamming **12** vẫn còn **791 cặp** và tại ngưỡng 15 là **3.529 cặp**. Nghiêm trọng hơn, hai ảnh của **cùng một chiếc xe** ở góc khác nhau vẫn mang cùng biển số nhưng khoảng cách Hamming lớn — rò rỉ **ngữ nghĩa** mà không ngưỡng phash nào phát hiện được. *Đã áp dụng:* nâng ngưỡng gộp từ 5 lên 10 và đo ở nhiều ngưỡng cao hơn ngưỡng gộp để phơi bày phần tồn dư. *Chưa áp dụng được:* chia split theo nhóm biển số, bất khả thi vì thiếu nhãn chuỗi cho phần lớn corpus. **Hệ quả: mọi chỉ số ở 6.4 và 5.6 phải coi là cận trên lạc quan.**

**(2) Tập test không xuyên bộ dữ liệu.** *Mức nghiêm trọng: cao.* Train và test đều lấy từ **cùng sáu nguồn nguyên tố**, nên chỉ đo được tổng quát hoá *trong phân bố*, **không** đo được *xuyên phân bố* — thứ quyết định khi triển khai trên camera mới, địa điểm mới, điều kiện chiếu sáng mới; tài liệu đã chỉ ra độ chính xác ALPR **sụt giảm đáng kể** khi đánh giá xuyên bộ dữ liệu [7]<!-- laroca_2022_crossdataset -->. *Biện pháp giảm thiểu:* không có trong khuôn khổ đồ án — cách đúng là giữ lại một nguồn hoàn toàn không dùng để huấn luyện làm tập test xuyên bộ; chưa thực hiện, ghi vào hướng phát triển.

**(3) Mẫu số nhỏ cho các chỉ số OCR.** *Mức nghiêm trọng: cao.* Phần lớn corpus 15.133 ảnh **chỉ có nhãn hộp giới hạn, không có nhãn chuỗi ký tự**, nên A4…A7 đo trên tập con nhỏ hơn nhiều; với mẫu số nhỏ, chênh lệch vài điểm phần trăm có thể nằm trong dao động ngẫu nhiên. *Giảm thiểu:* công bố mẫu số ở mọi bảng của 6.5, và **không** rút kết luận về chênh lệch nhỏ khi mẫu số dưới ngưỡng có ý nghĩa.

**(4) Đo trên một cấu hình phần cứng duy nhất.** *Mức nghiêm trọng: trung bình.* Mọi số hiệu năng đo trên một máy Intel Raptor Lake 14 nhân chạy Windows 11 và **không ngoại suy** sang CPU khác kiến trúc, sang Linux, hay sang máy khác số nhân — đặc biệt vì ONNX Runtime và OpenVINO đều nhạy với cấu hình luồng và tập lệnh vector của CPU cụ thể [117]<!-- onnxruntime_2025_threading --> [120]<!-- openvino_2024_performancehints -->. *Giảm thiểu:* công bố cấu hình đầy đủ ở Bảng 6.1 và nhắc lại ràng buộc ở đầu 6.6.

**(5) Một lượt huấn luyện duy nhất, không ước lượng được phương sai.** *Mức nghiêm trọng: trung bình.* Với `seed=42` cố định và ngân sách khoảng 12 giờ CPU cho một lượt, mọi chỉ số là kết quả của **một lần chạy**. *Giảm thiểu:* cố định seed để đảm bảo tái lập; không phát biểu so sánh nào dựa trên chênh lệch nhỏ hơn dao động giữa các seed dự kiến.

**(6) Bộ dữ liệu không đạt tiêu chí Q6 về tỉ lệ đối tượng nhỏ.** *Mức nghiêm trọng: trung bình.* 10,91% số hộp có diện tích dưới 0,5% diện tích ảnh, vượt ngưỡng 10%. *Giảm thiểu:* báo cáo mAP **tách theo dải kích thước** ở 6.4.4 thay vì che sau một con số tổng.

**(7) Nhãn layout suy ra từ tỉ lệ khung hình khi bộ dữ liệu không khai báo.** *Mức nghiêm trọng: thấp đến trung bình.* Ngưỡng 2,5 có cơ sở từ QCVN 08:2024/BCA nhưng vẫn là heuristic; biển chụp nghiêng mạnh có thể bị phân loại nhầm. *Giảm thiểu:* ưu tiên nhãn lớp tường minh khi có, và ghi rõ trong chú thích Bảng 6.7 tỉ lệ ô nào suy bằng heuristic.

**(8) Ma trận nhầm lẫn ký tự phụ thuộc thuật toán căn chỉnh chuỗi.** *Mức nghiêm trọng: thấp.* Khi hai chuỗi khác độ dài, việc gán cặp "ký tự thật ↔ ký tự đọc được" phụ thuộc cách căn chỉnh Levenshtein xử lý các đường đi tối ưu đồng hạng, nên với chuỗi nhiều lỗi chèn/xoá, ma trận có thể ghi nhận cặp không phản ánh nhầm lẫn thị giác thật. *Giảm thiểu:* áp ngưỡng tần suất tối thiểu trước khi đưa một cặp vào bảng luật (tiêu chí 1 ở 6.5.4).

---

## 6.10. Đối chiếu với các công trình đã công bố

### 6.10.1. Vì sao phần lớn các con số không so trực tiếp được

Ba khác biệt khiến việc đặt cạnh nhau hai con số độ chính xác của hai công trình là **không hợp lệ về phương pháp**, trừ khi cả ba đều trùng. **Bộ dữ liệu và quốc gia:** biển Trung Quốc chủ yếu một dòng, biển Brazil có bố cục và phông chữ riêng, biển Việt Nam có tỷ lệ biển hai dòng cao. **Định nghĩa chỉ số:** *"accuracy"* trong các bài được khảo sát khi thì là mức ký tự, khi là mức chuỗi, khi là toàn trình tính cả bước phát hiện. **Điều kiện ảnh:** camera tĩnh ở trạm thu phí khác hẳn ảnh chụp tự do, độ phân giải vùng biển chênh nhau nhiều lần. Bằng chứng mạnh nhất đến từ chính lĩnh vực: Laroca và cộng sự (2022) chạy **12 mô hình OCR trên 9 tập dữ liệu công khai** và ghi nhận độ chính xác trung bình **sụt từ 82,4% xuống 45,2%** khi đánh giá xuyên tập dữ liệu — cùng một mô hình mất gần một nửa độ chính xác chỉ vì đổi tập kiểm thử.

> ⚠️ **Hệ quả bắt buộc cho toàn mục này.** Mọi con số của công trình khác dẫn ở dưới đều **kèm tên bộ dữ liệu và quốc gia ngay trong bảng**, và không con số nào được dùng để kết luận rằng hệ thống của đồ án tốt hơn hay kém hơn. Chúng chỉ trả lời một câu hỏi hẹp hơn nhiều: *kết quả của đồ án có nằm trong vùng giá trị mà lĩnh vực đã ghi nhận hay không.*

### 6.10.2. Khối phát hiện — nằm trong vùng giá trị đã công bố

| Công trình | Bộ dữ liệu · quốc gia | mAP@0.5 |
|---|---|---:|
| Batra và cộng sự (2022) | Google Open Images + biển Ấn Độ, 5.991 ảnh | 87,2% |
| Ba nghiên cứu dùng YOLO11 cho ALPR (mục 3.2) | các tập khác nhau | 90,6% – 99,5% |
| **Đồ án này** | **corpus Việt Nam hợp nhất, 1.514 ảnh test** | **98,29%** |

Đây là khối so sánh được nhiều nhất vì mAP@0.5 có định nghĩa thống nhất. Kết quả của đồ án nằm trong vùng trên; điều này **không** chứng minh mô hình tốt hơn hay kém hơn công trình nào — mỗi dòng đo trên một tập khác nhau — nhưng xác nhận khối phát hiện không có bất thường so với mặt bằng đã công bố. Điều kiện phải nêu kèm: tập test của đồ án **không xuyên bộ dữ liệu**, nên con số 98,29% **lạc quan hơn** mức đạt được khi gặp nguồn ảnh hoàn toàn mới (hạn chế ghi ở mục 7.3.3).

### 6.10.3. Khối nhận dạng — chỗ đồ án thua, và thua ở đâu

| Công trình | Bộ dữ liệu · quốc gia | Chỉ số công bố | Giá trị |
|---|---|---|---:|
| Xu và cộng sự — RPnet (2018) | CCPD · Trung Quốc | accuracy end-to-end | 98,5% |
| Laroca và cộng sự (2021) | 8 tập từ 5 khu vực | recognition rate trung bình | 96,9% |
| Xu và cộng sự — LPTR-AFLNet (2025) | biển Trung Quốc | accuracy **riêng biển hai dòng** | 99,37% |
| Tran và Bui (2024) | biển Việt Nam, chạy trên Raspberry Pi 4 | accuracy | 95,68% |
| **Đồ án này** | **2.801 biển Việt Nam có nhãn chuỗi** | **chuỗi đầy đủ sau hậu xử lý (A6)** | **75,12%** |
| **Đồ án này** | *(cùng tập)* | **toàn trình từ ảnh gốc (A7)** | **55,52%** |

**Khoảng cách là thật và không được lấy khác biệt bộ dữ liệu ra biện minh cho toàn bộ nó.** Nhưng chẩn đoán ở 6.5.3 định vị nó rất rõ: chênh lệch một dòng ↔ hai dòng ở khối OCR là **25,45 điểm**, và phần thiếu hụt nằm gần như trọn ở biển hai dòng — loại biển chiếm tỷ lệ lớn ở Việt Nam nhưng chiếm tỷ lệ nhỏ trong các bộ dữ liệu Trung Quốc mà phần lớn công trình ở bảng trên dùng. Hai dòng đáng đọc kỹ nhất là **LPTR-AFLNet (99,37% riêng biển hai dòng)** và **Tran–Bui (95,68% trên biển Việt Nam)**: cả hai cho thấy vùng giá trị này là **đạt được**, tức khoảng cách của đồ án không phải giới hạn của bài toán mà là giới hạn của lựa chọn kỹ thuật — đồ án dùng engine OCR **đa ngữ tổng quát chưa tinh chỉnh**, trong khi hai công trình kia dùng mô hình huấn luyện riêng cho biển số. Đây là hướng phát triển ưu tiên cao nhất ở mục 7.4.1, và mục 5.4 đã đo thử một bước theo hướng đó.

### 6.10.4. Ba điều đồ án báo cáo mà khảo sát không tìm thấy tương đương

Khảo sát ở mục 2.7.4 xác định sáu khoảng trống; ba trong số đó liên quan trực tiếp tới cách **báo cáo** kết quả. *Chưa có công trình Việt Nam nào tách riêng độ chính xác biển một dòng và hai dòng trên cùng hệ thống* — đồ án báo cáo ở Bảng 6.11, chênh **25,45 điểm**. *Hầu hết công trình trong nước chỉ báo cáo mAP khâu phát hiện, không báo cáo độ chính xác toàn trình mức chuỗi* — đồ án báo cáo cả hai: mAP 98,29% **và** A7 = 55,52%. *Số liệu hiệu năng thường công bố không kèm phần cứng* — mọi số hiệu năng ở đây kèm model CPU, số luồng, kích thước ảnh (6.2.1). Điều đáng nói là **con số thứ hai kém hơn hẳn con số thứ nhất**, và đó chính là lý do khoảng trống này tồn tại: báo cáo toàn trình thì phải công bố cả phần hỏng, còn một hệ thống chỉ công bố mAP khâu phát hiện luôn trông tốt hơn thực tế người dùng gặp. Ngoài ba mục trên, đồ án còn đo được **đóng góp thuần của khối hậu xử lý theo luật** — **+11,39 điểm**, sửa đúng 319 biển, làm hỏng 0 (6.5.2); khảo sát không tìm thấy công trình Việt Nam nào công bố đại lượng này tách bạch.

## 6.11. Kết luận chương

**Trả lời trực tiếp sáu câu hỏi nghiên cứu.** *RQ1:* bộ phát hiện YOLO11n đạt **toàn bộ** chỉ tiêu, vượt mục tiêu (Bảng 6.6). *RQ2:* có, chênh lệch giữa hai layout là **có ý nghĩa và rất lớn** — 25,45 điểm A6 — nhưng nằm ở tầng OCR (Bảng 6.11) chứ không ở tầng phát hiện (2,09 điểm, Bảng 6.7). *RQ3:* khối hậu xử lý đóng góp **+11,39 điểm**, sửa đúng **319** biển, làm hỏng 0 (Bảng 6.10). *RQ4:* NFR-P1 **chỉ đạt ngưỡng tối thiểu** (🟡) với p95 = 1.143,10 ms — thoái lui có chủ ý đổi lấy 34 biển đọc thêm; cùng nguyên nhân đó làm **NFR-P2 trượt cả sàn** (2,379 FPS, sàn 3); nút thắt thời gian vẫn là OCR (64,3%) và detector (34,0%, Bảng 6.19). *RQ5:* bảng luật hiện hành **phần lớn không khớp** cặp nhầm thật — chỉ 2/10 cặp nhầm nhiều nhất được phủ (Bảng 6.12). *RQ6:* các mối đe doạ được liệt kê và đánh giá ở 6.9.3, ba mối nghiêm trọng nhất ở mức "cao".

**Đóng góp định lượng của khối hậu xử lý — đóng góp khoa học riêng của đồ án.** Đo hai lần trên cùng 2.801 biển cho **+11,39 điểm**, cải thiện thuần một chiều (319 sửa đúng / 0 làm hỏng), dồn gần trọn vào biển hai dòng (+13,97 điểm) nhưng vẫn không đủ tới ngưỡng vì phần lỗi còn lại nằm ở tầng OCR, nơi hậu xử lý theo luật về bản chất không với tới được. Việc định vị đóng góp về từng nhóm luật (Bảng 6.10) chưa đo được và là hạng mục cần viết mã.

**Hiệu năng — kết luận đã đảo hai lần.** Sau khi giải quyết mâu thuẫn số liệu (con số cũ 5.857 ms bị bác bỏ vì nhiễm tranh chấp CPU và đo sai checkpoint; đo lại trên máy rảnh với `best.pt` cho 731 ms), NFR-P1 **đã đạt mục tiêu ở thời điểm 20/07** — cặp số đồng thuận khi ấy, client-side 731 ms và in-process 780 ms, xác nhận phương pháp đo chứ không mô tả hệ thống giao hàng. **Nhưng bậc thang thử-lại thêm sau đó đã đảo kết luận một lần nữa** (p95 = 1.143,10 ms, 🟡; NFR-P2 trượt cả sàn). Breakdown thật là OCR 64,3% / detector 34,0%, không phải 93,3% / 6,7% như báo cáo cũ, nên tối ưu detector giờ có ý nghĩa thật. Kết luận hai vế: **kiến trúc phần mềm không còn là vấn đề**; **nhưng độ trễ suy luận thì vẫn là vấn đề**, bên cạnh độ chính xác OCR trên biển hai dòng.

**Các giới hạn nghiêm trọng nhất** (6.9.3): (i) rò rỉ tồn dư không khử được — ở Hamming 12 vẫn còn 791 cặp gần trùng train↔test, và rò rỉ ngữ nghĩa thì không đo được; (ii) tập test không xuyên bộ dữ liệu — chỉ đo được tổng quát hoá *trong* phân bố; (iii) mẫu số nhỏ cho chỉ số OCR (2.801 biển có nhãn chuỗi trên 15.133 ảnh). Hệ quả: **mọi chỉ số độ chính xác trong chương nên được đọc như cận trên lạc quan**; riêng A7 = 0,5552 thì ngược lại — cận dưới bi quan do giao thức đo trên ảnh crop.

**Chuyển tiếp sang Chương 7.** Chương này xác định bằng số liệu — không bằng phỏng đoán — ba nhóm hướng phát triển: (i) **tối ưu hoặc thay thế khối OCR** cho biển hai dòng, từ 6.5.3 và breakdown 6.6.2; (ii) **hiệu chỉnh bảng luật sửa lỗi theo ma trận nhầm lẫn đo được** (8/10 cặp nhầm nhiều nhất chưa có luật phủ), từ 6.5.4, với ràng buộc phải kiểm chứng trên tập giữ riêng để tránh khớp luật trên chính tập đánh giá; (iii) **xây dựng tập test xuyên bộ dữ liệu, chia split theo nhóm biển số, và gán nhãn chuỗi cho một phân bố hiện trường** để đo NFR-A7 và NFR-A9 đúng cách, từ 6.3.3, 6.5.5 và 5.11.3.
