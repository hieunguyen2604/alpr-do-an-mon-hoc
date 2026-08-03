# CHƯƠNG 5. THỰC NGHIỆM VÀ ĐÁNH GIÁ

Chương 5 trình bày hệ thống *đã được xây dựng* như thế nào. Chương này trả lời hai câu hỏi trọng số ngang nhau: hệ thống đó **hoạt động tốt đến mức nào**, và **những con số đó có đáng tin không** — nên mỗi con số đều đi kèm ngữ cảnh đo của nó.

---

## 5.1. Mục tiêu và phương pháp đánh giá

### 5.1.1. Các câu hỏi nghiên cứu mà chương này trả lời

Sáu câu hỏi cụ thể hoá từ `docs/00-requirements/non-functional-requirements.md`. **RQ1** — YOLO11n có đạt chỉ tiêu định vị biển số Việt Nam không (5.5; NFR-A1…A3; 5.4)? **RQ2** — độ chính xác nhận dạng chênh bao nhiêu giữa biển một dòng và hai dòng (NFR-A8; 5.4.3, 5.5.3)? **RQ3** — **khối hậu xử lý theo luật đóng góp bao nhiêu điểm phần trăm** vào độ chính xác chuỗi đầy đủ (NFR-A5 ↔ A6; 5.5.2)? **RQ4** — có đạt chỉ tiêu độ trễ trên phần cứng CPU-only không, **nút thắt ở đâu** (5.7; NFR-P1…P7; 5.6)? **RQ5** — bảng luật sửa lỗi ký tự, vốn suy từ **hình dạng chữ** chứ không từ đo đạc, có khớp các cặp thực sự bị nhầm không (5.5.4; `VNPLATE` §9.8)? **RQ6** — số liệu chịu **mối đe doạ nào đến tính hợp lệ** (5.9.3)? RQ3 và RQ5 mang **đóng góp học thuật riêng** — một lượng hoá khối chức năng mà tài liệu ALPR chỉ mô tả định tính, một thay tri thức suy đoán bằng tri thức đo được; RQ6 quyết định giá trị của năm câu còn lại.

### 5.1.2. Hai nguyên tắc trình bày bắt buộc

**Một — mọi số hiệu năng phải kèm cấu hình phần cứng**: đồ án suy luận **hoàn toàn trên CPU** nên so với các con số FPS đo trên GPU là không hợp lệ nếu không ghi rõ; cấu hình ở 5.2 là điều kiện diễn giải cho toàn mục 5.6. **Hai — mọi số độ chính xác phải kèm tên tập dữ liệu và số mẫu**, vì độ chính xác là thuộc tính của **cặp (mô hình, tập đánh giá)**; hệ quả: NFR-A4…A7 chỉ đo được trên tập con có nhãn chuỗi, nhỏ hơn nhiều tập test phát hiện, mẫu số đó không được giấu. **Ký hiệu:** ✅ đạt mục tiêu · 🟡 chỉ đạt ngưỡng tối thiểu · ❌ không đạt · ⬜ chưa đo · ➖ không áp dụng.

> **Cảnh báo trích dẫn.** Cặp số **94,3%** (biển một dòng) ↔ **45,7%** (biển hai dòng), chênh **48,6 điểm phần trăm**, đo trên bộ dữ liệu **RodoSol-ALPR của Brazil** [7]<!-- laroca_2022_crossdataset -->. Đây **không phải** số liệu Việt Nam; mỗi lần dẫn, tên bộ dữ liệu và quốc gia phải xuất hiện **ngay trong câu**, và nó chỉ dùng như *analogue định lượng* về độ khó tương đối của biển hai dòng, không bao giờ như mốc chuẩn phải vượt.

### 5.1.3. Giao thức đo

![](figures/fig-ch6-01.png)

**Hình 5.1.** Giao thức đo và ràng buộc phụ thuộc giữa các bước đánh giá.

**Không bước đo nào chạy trước khi trọng số được đóng băng**; **tập test không được chạm vào trong huấn luyện lẫn chọn epoch** — chọn epoch chỉ dựa vào validation. Ba quy ước: **kích thước lô = 1 khi đo độ trễ** (riêng mAP dùng lô lớn hơn vì không phụ thuộc kích thước lô); **bỏ 3 lượt khởi động nóng**; **báo cáo p50/p95/p99, không báo cáo trung bình**, vì trung bình che đuôi phân bố còn NFR-P1 phát biểu ở p95.

---

## 5.2. Môi trường thực nghiệm

Toàn bộ số liệu đo trên **một máy trạm cá nhân duy nhất** (`docs/00-requirements/environment.md`): **Windows 11 Pro 10.0.26200**, **Python 3.13.12**, CPU **Intel Raptor Lake** (Family 6, Model 183) — **14 nhân vật lý / 20 nhân logic**, **không có GPU CUDA** nên mọi suy luận và huấn luyện chạy trên CPU (`device=cpu`); chế độ đo **lô = 1, bỏ 3 lượt khởi động nóng**. Đây là **tiền tố ngầm định của mọi con số hiệu năng ở 5.6**.

Phiên bản thư viện trích từ `pip freeze` đúng thời điểm chạy phép đo cuối cùng (2026-07-20), không chép từ `requirements.txt` (tệp yêu cầu ghi *ràng buộc*, không ghi *phiên bản đã cài*); một môi trường ảo hợp nhất `backend/.venv`: `ultralytics` 8.4.101 · `torch` 2.13.0+cpu · `torchvision` 0.28.0+cpu · `paddleocr` 3.7.0 (PP-OCRv5 mobile) · `paddlepaddle` 3.3.1 · `onnxruntime` 1.27.0 · `openvino` 2026.2.1 (backend thay thế, 5.6.3) · `opencv-python` 4.10.0.84 · `numpy` 2.4.5 · `fastapi` 0.139.2 · `uvicorn` 0.51.0 · `sqlalchemy` 2.0.51 · `imagehash` 4.7.2 · `pytest` 9.1.1.

### 5.2.3. Vì sao ràng buộc CPU-only là ràng buộc thiết kế, không phải hạn chế tạm thời

Lập luận đầy đủ ở **4.3.1**. NFR-P1 phát biểu *kèm* ràng buộc CPU, nên kết luận "đạt sàn, không đạt mục tiêu" ở 5.6 là kết luận về hệ thống trong đúng bối cảnh vận hành thật, không phải con số chờ nâng cấp phần cứng. Cấu hình mô hình cũng do ràng buộc phần cứng quyết định — **YOLO11n** (2.590.035 tham số) [16]<!-- jocher_2024_yolo11 --> và **PP-OCRv5 mobile** [118]<!-- paddlepaddle_2026_ppocrv5docs -->. Về quy mô: **35,6 phút mỗi epoch**, một lượt 20 epoch mất khoảng **12 giờ** liên tục, khiến **tìm kiếm siêu tham số bất khả thi**; chương này báo cáo *một* cấu hình huấn luyện, không phải kết quả của một quá trình tối ưu — giới hạn thật, ghi ở 5.9.3.

---

## 5.3. Bộ dữ liệu thực nghiệm

> **Lưu ý về cách đặt tên.** Thư mục `yolo_v2/` và `yolo_v3/` chỉ **phiên bản của bộ dữ liệu**, **không** liên quan đến kiến trúc YOLOv2 hay YOLOv3. Mô hình dùng trong toàn đồ án là **YOLO11n**.

<!-- {{T5.3a}} so sanh ba phien ban bo du lieu — DA CO SO, khong can dien -->
<!-- {{T5.3b}} so cap gan trung xuyen split theo nguong Hamming -->

**Bảng 5.1.** Ba phiên bản bộ dữ liệu và số cặp ảnh gần trùng xuyên split theo ngưỡng Hamming

| Thuộc tính / ngưỡng | v1 | v2 | **v3** |
|---|---:|---:|---:|
| Tổng số ảnh | 4.578 | 15.133 | **15.133** |
| Ngưỡng Hamming gộp trùng lặp | 5 | 5 | **10** |
| Số ảnh train / val / test | — | — | **10.592 / 3.027 / 1.514** |
| Dùng cho | `baseline-416-v1.pt` | bị loại bỏ | **`best.pt`** |
| Cặp gần trùng xuyên split, Hamming 0 | — | — | **0** *(thông tin mới)* |
| Hamming 5 | — | — | **0** *(= ngưỡng gộp v1, v2 — không mang thông tin mới)* |
| **Hamming 10** | **619** | **2.699** | **0** *(= ngưỡng gộp v3 — không mang thông tin mới)* |
| Hamming 12 · 15 | — | — | **791** · **3.529** *(thông tin mới)* |
| Hamming 20 | — | — | **137.506** *(ngưỡng đã lỏng tới mức nhiều cặp là dương tính giả)* |

> Mẫu số phần rò rỉ: 10.592 × 1.514 = **16.036.288 cặp**. Khoảng cách Hamming **nhỏ nhất quan sát được là 12** — giá trị chẵn kế tiếp sau ngưỡng gộp 10, một tất yếu toán học (mọi mã băm đều có đúng 32 bit 1 nên khoảng cách luôn chẵn), **không phải dấu vết rò rỉ bị cắt cụt tại ngưỡng**; kiểm chứng (15.133/15.133 mã băm popcount chẵn; 4.498.500/4.498.500 cặp lấy mẫu có khoảng cách chẵn) ở [`02-dataset-report.md` mục 6bis.1](../reports/02-dataset-report.md). Cột v1/v2 chỉ có số ở ngưỡng 10 vì đó là con số đã đo trước đó; ô trống **không được suy ra**.

**v1 quá nhỏ và chỉ một nguồn** (1 bộ vào hợp nhất, 1 nguồn nguyên tố) — động cơ tải thêm **tám bộ** (tổng **9 bộ**), trong đó **sáu bộ** vào hợp nhất detection cùng bộ gốc (v2, v3: **7 bộ vào hợp nhất, 6 nguồn nguyên tố**), hai bộ nhãn mức ký tự tách riêng cho OCR. **v2 sửa được quy mô nhưng không sửa được rò rỉ:** lên 15.133 ảnh lại *tăng* cặp gần trùng xuyên split lên 2.699 vì các nguồn chứa ảnh có nguồn gốc chung. **v3 giữ nguyên corpus** (cùng 15.133 ảnh), khác biệt duy nhất là ngưỡng khử trùng lặp 5 → 10 và split sinh lại — cô lập biến có chủ ý, cho phép quy kết mọi thay đổi kết quả cho *chất lượng split*, không cho *lượng dữ liệu*.

### 5.3.2. Khử trùng lặp: hai tỉ lệ, hai mẫu số khác nhau

Trước hợp nhất, trên toàn bộ ảnh của 7 bộ vào hợp nhất detection: loại **11.978 / 27.111 = 44,2%**. Sau hợp nhất, ở ngưỡng 10 trên corpus đã hợp nhất: loại **7.227 / 15.133 = 47,8%**. Hai tỉ lệ **không cộng dồn và không thay thế nhau** — số thứ nhất là mức trùng lặp *giữa và trong* 7 bộ, số thứ hai là mức còn lại *trong corpus đã hợp nhất* (Phụ lục C.3). *Mẫu số 27.111* là tổng ảnh của **7 bộ vào hợp nhất detection** (4.578 + 8.254 + 236 + 840 + 8.357 + 3.841 + 1.005), **không phải** 9 bộ đã tải; hai bộ còn lại — `roboflow_ocr_plate` (3.819 ảnh, 30 lớp ký tự) và `roboflow_ocr_conversion` (200 ảnh, 22 lớp ký tự) — là **nhãn mức ký tự**, tách riêng cho tầng OCR (`datasets/reports/merge_report.json`, `images_per_dataset` có đúng 7 khoá). Mọi lần trích dẫn một trong hai tỉ lệ phải kèm mẫu số tương ứng.

### 5.3.3. Kiểm chứng rò rỉ dữ liệu — và vì sao con số "0 cặp rò rỉ" không chứng minh được điều gì

Rò rỉ xảy ra khi tập test chứa ảnh gần trùng ảnh train: mô hình *ghi nhớ* thay vì *tổng quát hoá*, mọi chỉ số bị thổi phồng — với corpus ghép từ nhiều nguồn công khai đây là rủi ro hệ thống [7]<!-- laroca_2022_crossdataset -->. Công cụ đo là **băm tri giác** (`imagehash.phash`, 64 bit).

> **Lập luận vòng tròn.** v3 được khử trùng lặp ở ngưỡng Hamming 10; đo rò rỉ ở đúng ngưỡng đã dùng để gộp trùng lặp là **kiểm tra lại chính định nghĩa của mình**, không phải kiểm chứng độc lập. Kết quả bằng 0 ở đó chứng minh bước khử trùng lặp *đã chạy đúng đặc tả*, và **không chứng minh gì thêm** về mức độ "sạch" của tập test.

Chỉ các ngưỡng **12 (791 cặp), 15 (3.529 cặp), 20 (137.506 cặp)** mang thông tin mới, và ngay cả chúng cũng **không** chứng minh tập test sạch. **Ba giới hạn của phash:** (1) phash chỉ bắt tương đồng ở mức **bố cục sáng-tối tổng thể** — hai ảnh *cùng một chiếc xe* ở hai góc khác nhau, hay hai khung hình cách nhau vài giây trong cùng video, vẫn mang **cùng một biển số** dù Hamming lớn; loại rò rỉ ngữ nghĩa này **không khử được bằng bất kỳ ngưỡng phash nào**; (2) **không có định danh phương tiện hay chuỗi biển cho toàn corpus** nên không chia split theo **nhóm biển số** được — chính hạn chế dẫn tới mẫu số nhỏ của các bảng OCR ở 5.5; (3) **ngưỡng cao sinh dương tính giả**, nên 137.506 là **cận trên bi quan**. **Kết luận trung thực:** khẳng định được *bước khử trùng lặp ở ngưỡng 10 đã chạy đúng đặc tả*; **không** khẳng định được *tập test độc lập với tập train*. Rò rỉ tồn dư ở mức ngữ nghĩa **không đo được bằng công cụ hiện có** — mối đe doạ đầu tiên ở 5.9.3; mọi chỉ số ở 5.4 phải đọc kèm ghi chú này.

### 5.3.4. Phân bố nguồn dữ liệu giữa các split

Cột `source_dataset` trong `split_manifest.csv` chứa một **tập xuất xứ** ngăn bằng `|`: một ảnh có thể đến từ nhiều nguồn, nên v3 gồm **16 tổ hợp xuất xứ** dựng từ đúng **6 nguồn nguyên tố**. Cộng dồn số đếm của 6 nguồn cho **33.828**, vượt xa 15.133 vì ảnh đa nguồn bị đếm nhiều lần — **không được dùng 33.828 làm mẫu số**. Toàn tập chia **15.133 = 10.592 / 3.027 / 1.514**, tức **70,0% / 20,0% / 10,0%**; bảng đầy đủ 16 tổ hợp ở `split_manifest.csv` và Phụ lục C. Phải phân biệt ba con số nguồn: **9 bộ đã tải về**, **7 bộ vào hợp nhất detection**, **6 nguồn nguyên tố**.

**Tiêu chí đọc:** tỉ lệ một nguồn trong tập test lệch quá 10 điểm phần trăm so với tỉ lệ tổng thể (10,0%) thì phải nêu tên. Hai tổ hợp vượt: `roboflow_traffic_camera` thuần (**2.582** ảnh) có **20,3%** rơi vào test — gấp đôi tỉ lệ tổng thể; `roboflow_school_fuhih|roboflow_traffic_camera` (**250** ảnh) có tới **69,6%**. Nghĩa là **tập test nghiêng về ảnh camera giao thông** — góc rộng, biển nhỏ — nên khi đọc mAP theo dải kích thước (5.4.4) phải nhớ đối tượng nhỏ trong tập test tập trung ở một nguồn. Hệ quả của việc các tổ hợp nhỏ khó chia đều, ghi nhận như yếu tố đọc kèm chứ không phải khiếm khuyết vô hiệu hoá kết quả.

**Một bộ dữ liệu dư thừa hoàn toàn.** `roboflow_tran_ngoc_xuan_tin` vào hợp nhất với **1.005 ảnh**, ra khỏi khử trùng lặp chéo bộ với **0 ảnh — loại 100,0% (1.005/1.005)**: cả 1.005 ảnh đều dính ít nhất một cặp gần trùng (**1.577** cặp với `roboflow_school_fuhih`, **1.569** với `roboflow_cuong_ta`, **8** với `hf_vn_plates_segment`, **35** cặp nội bộ); kiểm chứng độc lập: `split_manifest.csv` không chứa tên bộ này lần nào. Đây là **bằng chứng định lượng** cho cảnh báo ở Phase 1 rằng các bộ Roboflow tái sử dụng ảnh của nhau rất nặng, và là lý do **không được cộng dồn `expected_images` để suy ra quy mô thật** ([`02-dataset-report.md`](../reports/02-dataset-report.md) mục 5.3.1).

---

## 5.4. Đánh giá bộ phát hiện biển số

Toàn bộ 5.4 đo trên **tập test v3: 1.514 ảnh, 1.611 đối tượng nhãn thật**, `imgsz=640`, `device=cpu`; tập test chưa từng dùng trong huấn luyện hay chọn epoch.

### 5.4.1. Chỉ số tổng thể

<!-- {{T5.4a}} ket qua detection tong the tren tap test v3 (1.514 anh) — chuyen thanh van xuoi, doi chieu nguong o T5.7 -->

**Cả bốn chỉ tiêu bắt buộc đều đạt mục tiêu**, đo trên `ultralytics_val`: **mAP@0.5 = 0,9829** (NFR-A1; sàn 0,85, mục tiêu 0,90 ✅), **mAP@0.5:0.95 = 0,7834** (NFR-A2; sàn 0,55, mục tiêu 0,65 ✅), **Precision = 0,9837** và **Recall = 0,9714** (NFR-A3; sàn 0,88 / 0,85, mục tiêu 0,92 / 0,90 ✅), **F1 = 0,9775** tại ngưỡng confidence 0,25; đối chiếu ở Bảng 5.10. Ba lưu ý: (1) **bài toán chỉ có một lớp** (`plate`), mAP một lớp không so trực tiếp được với mAP nhiều lớp trên COCO nên giá trị cao là bình thường, **không phải bằng chứng về độ khó đã vượt qua**; (2) chỉ số quyết định là **mAP@0.5:0.95** vì độ khớp box ảnh hưởng trực tiếp đến chất lượng vùng cắt đưa sang OCR; (3) **chỉ số tổng thể che giấu phân bố**.

Ba hình chẩn đoán của khối phát hiện — đường cong PR tách theo layout (`05-detection-pr-curve.png`), ma trận nhầm lẫn nhận biết layout (`05-detection-confusion-matrix.png`), đường cong F1 theo ngưỡng confidence (`05-detection-f1-curve.png`) trong `docs/reports/figures/` — **chưa sinh**. Hình F1 có vai trò thực tiễn: **ngưỡng confidence chạy thật phải là ngưỡng tối ưu F1 đo được ở đó**, không phải mặc định 0,25 của Ultralytics; nếu hai giá trị lệch nhau thì cấu hình suy luận phải được cập nhật và ghi lại.

### 5.4.3. Tách theo biển một dòng và biển hai dòng (NFR-A8)

Layout xác định theo nhãn lớp khi bộ dữ liệu có khai báo, và theo **ngưỡng tỉ lệ khung hình 2,5** khi không có — nằm giữa tỉ lệ chuẩn của biển một dòng (4,727) và biển hai dòng (2,000 / 1,357) theo QCVN 08:2024/BCA.

<!-- {{T5.4b}} detection tach theo layout mot dong / hai dong (NFR-A8) -->

**Bảng 5.2.** Kết quả phát hiện tách theo biển một dòng và hai dòng (NFR-A8)

| Chỉ số | Biển **một dòng** | Biển **hai dòng** | Chênh (điểm %) |
|---|---:|---:|---:|
| Số đối tượng nhãn thật *(tổng 1.611)* | 286 | 1.325 | n/a |
| mAP@0.5 | 0,9884 | 0,9675 | 2,09 |
| mAP@0.5:0.95 | 0,7526 | 0,7649 | −1,23 |
| Precision · Recall · F1 | 0,9861 · 0,9895 · 0,9878 | 0,9735 · 0,9691 · 0,9713 | 1,26 · 2,04 · 1,65 |

> **Nhãn layout là ước lượng, không phải nhãn thật:** bộ dữ liệu không khai báo lớp layout nên layout suy từ ngưỡng tỉ lệ khung hình 2,5 (**100% số ô** suy bằng heuristic). Mọi kết luận về NFR-A8 ở tầng phát hiện phải nêu rõ điều này.

**Chênh lệch ở tầng phát hiện rất nhỏ, đúng dự đoán** — ở mAP@0.5:0.95 biển hai dòng thậm chí *nhỉnh hơn* 1,23 điểm, tức dao động trong phạm vi nhiễu; cùng bậc với baseline (`baseline-416-v1.pt`, split v1, imgsz 416: một dòng 0,9856 so với hai dòng 0,9592, chênh 2,6 điểm — **số của baseline, không được chuyển thành số của `best.pt`**). **Việc *định vị một hình chữ nhật* gần như không phụ thuộc vào việc bên trong có một hay hai dòng ký tự.** Vì vậy **tuyệt đối không được** dùng 2,09 điểm để kết luận "hệ thống xử lý tốt biển hai dòng" — chênh lệch thật nằm ở tầng OCR và chỉ lộ ra ở Bảng 5.5, nơi khoảng cách nhảy lên **25,45 điểm**.

### 5.4.4. Tách theo dải kích thước hộp giới hạn

Mục này tồn tại vì **bộ dữ liệu không đạt tiêu chí chất lượng Q6**: **10,91% số hộp có diện tích dưới 0,5% diện tích ảnh**, vượt ngưỡng 10%. Đối tượng nhỏ là chế độ thất bại đã ghi nhận rộng rãi của bộ phát hiện một giai đoạn [119]<!-- ultralytics_2026_modelevaluation -->, biển số độ phân giải thấp đã thành hướng nghiên cứu riêng [71]<!-- laroca_2026_icprlrlpr -->; một con số mAP tổng sẽ **giấu chế độ thất bại sau giá trị trung bình**.

<!-- {{T5.4c}} detection tach theo dai kich thuoc hop gioi han -->

**Bảng 5.3.** Kết quả phát hiện tách theo dải kích thước hộp giới hạn

| Dải (diện tích box / diện tích ảnh) | Số đối tượng | Tỉ lệ tập test | mAP@0.5 | mAP@0.5:0.95 | Recall |
|---|---:|---:|---:|---:|---:|
| **Rất nhỏ** — dưới 0,5% | 262 | 16,26% | 0,8553 | 0,5249 | 0,8740 |
| **Nhỏ** — 0,5% đến 1% | 124 | 7,70% | 0,9755 | 0,7055 | 0,9758 |
| **Trung bình** — 1% đến 5% | 900 | 55,87% | 0,9913 | 0,8005 | 0,9922 |
| **Lớn** — 5% đến 15% | 297 | 18,44% | 0,9966 | 0,8394 | 0,9966 |
| **Rất lớn** — trên 15% | 28 ⚠ | 1,74% | 1,0000 | 0,8562 | 1,0000 |
| **Toàn tập test** | **1.611** | 100% | 0,9711 | 0,7625 | 0,9727 |

> Dòng ⚠ (28 đối tượng < 30) **không có ý nghĩa thống kê**, không đưa vào so sánh. Dải tính từ `(w×h)` của hộp nhãn thật chia diện tích ảnh gốc; số box không gán được dải: 0.

**Chế độ thất bại ở đối tượng nhỏ được xác nhận có thật:** Recall dải "rất nhỏ" 0,8740 so với 0,9922 của dải "trung bình" vốn chiếm hơn nửa tập test — **bỏ sót nhiều biển nhỏ hơn hẳn**. Đây là hậu quả đo được của tiêu chí Q6 không đạt, không phải cảnh báo lý thuyết; kết hợp với 5.3.4, dải "rất nhỏ" chiếm **16,26%** tập test, cao hơn tỉ lệ **10,91%** của toàn corpus, nghĩa là **tập test khó hơn trung bình ở đúng khía cạnh này**. Khắc phục: tăng `imgsz`, cắt ảnh theo ô (*tiling*), hoặc lọc bỏ đối tượng quá nhỏ khỏi tập huấn luyện. Nếu chỉ báo cáo một con số tổng thì chế độ thất bại này đã bị **giấu sau giá trị trung bình**.

---

## 5.5. Đánh giá khối OCR và hậu xử lý

> **Ràng buộc mẫu số.** NFR-A4…A7 chỉ đo được trên **tập con có nhãn chuỗi ký tự** (`datasets/annotations/plate_labels.csv`) — **2.801 biển**, không phải trên 1.514 ảnh test. Thiếu nhãn chuỗi cho phần lớn corpus là hạn chế thật, ghi ở 5.9.3.

### 5.5.1. Độ chính xác mức ký tự (NFR-A4)

Chỉ số là **CER** theo khoảng cách Levenshtein, chuẩn hoá theo độ dài nhãn thật, với $S$ ký tự thay thế, $D$ bị xoá, $I$ chèn thừa, $N$ tổng ký tự nhãn thật; NFR-A4 phát biểu theo **1 − CER**.

$$\mathrm{CER} = \frac{S + D + I}{N}$$

**NFR-A4 đạt ngưỡng tối thiểu:** 1 − CER = **0,9454** (sàn 0,92, mục tiêu 0,95 — 🟡), cách mục tiêu khoảng 0,5 điểm; chuỗi thô cho 0,9061, CER 0,0939 → **0,0546** (sàn ≤ 0,08, mục tiêu ≤ 0,05). Chỉ tiêu này từng ghi là **không đạt** (0,8848, đo 20/07/2026); lượt đo lại 28/07 trên đúng bộ trọng số ấy cho 0,9454 — chênh lệch **không** đến từ mô hình khác mà từ các bản sửa ở tầng suy luận và từ việc harness được nối đúng với pipeline giao hàng.

> **Nguồn số liệu.** Toàn bộ 5.5 lấy từ `docs/reports/05-results.json` — lượt đo 2026-07-28 trên máy rảnh, `models/best.pt` (`imgsz = 640`), 2.801 ảnh có nhãn chuỗi, đúng cấu hình giao hàng (nắn hình bật, siêu phân giải tắt — 5.5.7). Lượt này thay bộ số 20/07 vì hai lý do độc lập: **một**, bốn đợt sửa độ chính xác rơi vào 21–28/07 nên số cũ mô tả một hệ thống không còn tồn tại; **hai**, harness đo trước 28/07 **chưa bao giờ gọi** bậc thang thử-lại — cả nhánh vùng cắt lẫn nhánh đầu-cuối đều chép lại các bước pipeline rồi dừng ở bước cứu dòng trên, nên mọi con số A4–A7 công bố trước đó mô tả một pipeline **ngắn hơn bản giao hàng** (5.5.6). $S$/$D$/$I$ đo trên **chuỗi thô trước hậu xử lý** ($S$ = tổng ô ngoài đường chéo ma trận nhầm lẫn, $D$ = tổng xoá, $I$ = tổng chèn, $N$ = tổng ma trận cộng $D$) nên giống nhau ở cả hai cột — cũng vì vậy bước cứu dòng trên lẫn bậc thang thử-lại, vốn chạy **sau** chuẩn hoá, không làm ba con số này thay đổi.

Đáng chú ý hơn con số tổng là **cấu trúc lỗi**: tổng thao tác chỉnh sửa 3.092 → **2.241**, nhưng ba thành phần giảm rất không đều — chèn thừa $I$ 903 → **107** (−88,1%), thay thế $S$ 1.007 → **862** (−14,4%), xoá $D$ 1.182 → **1.272** (+7,6%). **Ký tự chèn thừa gần như biến mất** — dấu vân tay của các bản sửa đọc biển hai dòng (trước đây vùng chồng lấn bị đọc hai lần nên sinh ký tự lặp, viền biển và vết bẩn bị đọc thành ký tự); ngược lại **ký tự bị xoá nhích lên** và nay chiếm **56,8%** toàn bộ lỗi, tức phần lỗi còn lại đã dịch hẳn về dạng **đọc hụt ký tự**. Bảng luật mạnh ở việc sửa $S$ nhưng **về nguyên tắc không thể phục hồi một ký tự chưa từng được đọc ra**, nên khi $D$ chi phối thì hướng cải thiện phải chuyển sang tầng nhận dạng (7.4). Ba loại lỗi gợi ba nguyên nhân: $S$ → nhầm ký tự (xử lý được bằng bảng luật, 5.5.4), $D$ → bỏ sót ký tự do vùng cắt thiếu hoặc ký tự mờ, $I$ → nhiễu bị đọc thành ký tự.

### 5.5.2. Chuỗi đầy đủ: trước và sau hậu xử lý (NFR-A5 ↔ NFR-A6)

**Đây là mục quan trọng nhất của cả chương.** Khối hậu xử lý theo luật — chuẩn hoá ký tự, áp mặt nạ vị trí chữ số / chữ cái theo định dạng biển số Việt Nam, sửa cặp ký tự đồng hình, kiểm tra mã tỉnh — là **đóng góp kỹ thuật riêng** của đồ án, không có sẵn trong thư viện nào. Câu hỏi *khối đó đóng góp bao nhiêu?* chỉ trả lời được nếu **đo hai lần trên cùng một tập mẫu**: chuỗi thô PaddleOCR trả về (A5) và chuỗi sau khi áp toàn bộ luật (A6). Đây cũng là lý do kỹ thuật khiến trường `raw_ocr_text` tồn tại bên cạnh `plate_text` trong lược đồ cơ sở dữ liệu — **điều kiện cần để phép đo này thực hiện được**, phải có từ giai đoạn thiết kế.

<!-- {{T5.5a}} do chinh xac muc ky tu NFR-A4 -->
<!-- {{T5.5b}} do chinh xac chuoi day du truoc va sau hau xu ly — DONG GOP DINH LUONG CUA KHOI HAU XU LY -->

**Bảng 5.4.** Độ chính xác OCR trước và sau hậu xử lý, trên 2.801 biển có nhãn chuỗi

| Chỉ số | Sàn | Mục tiêu | **Trước hậu xử lý** | **Sau hậu xử lý** | Chênh (điểm %) |
|---|---:|---:|---:|---:|---:|
| 1 − CER (NFR-A4) | 0,92 | 0,95 | 0,9061 | **0,9454** 🟡 | n/a |
| CER | ≤ 0,08 | ≤ 0,05 | 0,0939 | 0,0546 | n/a |
| Chuỗi đầy đủ đúng (A5 → A6) | 0,80 → 0,85 | 0,85 → 0,90 | **0,6373** ❌ | **0,7512** ❌ | **+11,39** |
| $N$ / $S$ / $D$ / $I$ trên chuỗi thô | — | — | 23.855 / 862 / 1.272 / 107 | (không đổi) | n/a |
| Biển **sửa đúng** / **bị làm hỏng** / sai cả trước lẫn sau | — | — | — | **319** / **0** / **697** | n/a |

Dòng "sửa đúng / làm hỏng" quan trọng ngang dòng hiệu số: cùng một mức cải thiện thuần có thể đến từ "sửa đúng nhiều, làm hỏng nhiều" hoặc "sửa đúng ít, không làm hỏng biển nào" — **hai kết luận kỹ thuật khác nhau** về chất lượng bộ luật.

> **Phân rã đóng góp theo từng nhóm luật — *(chưa đo)*.** Năm nhóm cần bóc tách: chuẩn hoá cơ bản (bỏ ký tự phân tách, viết hoa, `Đ`→`D`), mặt nạ vị trí + `TO_DIGIT`, mặt nạ vị trí + `TO_LETTER`, ghép dòng cho biển hai dòng, kiểm tra mã tỉnh; mỗi nhóm cần số biển bị thay đổi, số sửa **đúng**, số bị làm **hỏng**, đóng góp thuần — tất cả *(chưa đo)* vì `ai/inference/plate_rules.py` chưa có cơ chế bật/tắt từng nhóm luật (hạng mục cần viết mã, mục D.2). Hai bậc cứu chữa chạy **sau** chuẩn hoá thì đã cô lập được nhờ đo A/B ở 5.5.6 và 5.5.7: **cứu dòng trên 209 biển**, **bậc thang thử-lại 34 biển**.

Hiệu số **A6 − A5 = 0,7512 − 0,6373 = +11,39 điểm phần trăm** trên **2.801 biển**, kèm **319 sửa đúng, 0 làm hỏng** — **không phải một đánh đổi** mà là **cải thiện thuần một chiều**: các mặt nạ vị trí và ràng buộc mã tỉnh đủ bảo thủ để không tự tạo lỗi mới. Nhưng dù đóng góp gần gấp đôi lượt 20/07 (+6,32 → **+11,39**), cả A5 lẫn A6 vẫn **không đạt** sàn (0,80 và 0,85) — A6 còn thiếu **9,88 điểm**. **Đóng góp phân bố rất không đều:** biển một dòng A5 0,9418 → A6 0,9541, **+1,23 điểm** ứng **7 biển**; biển hai dòng 0,5600 → 0,6996, **+13,97 điểm** ứng **312 biển**. Trên biển một dòng hậu xử lý gần như không có việc để làm (chuỗi thô đã đúng 94,18%); toàn bộ giá trị dồn vào **biển hai dòng** — bằng chứng rằng bộ luật thực sự bù đắp điểm yếu của tầng nhận dạng chứ không chỉ làm đẹp chuỗi.

Vì sao vẫn không đủ? **Chuỗi sai nhiều ký tự cùng lúc:** chỉ **1.251 / 2.234 biển hai dòng = 56,0%** đọc đúng trước hậu xử lý; khi bộ nhận dạng đọc hỏng cả cụm thì không luật thay-ký-tự nào cứu được, và **697 biển sai cả trước lẫn sau** chính là quần thể này. **Ký tự chưa từng được đọc ra thì không luật nào phục hồi được** — ràng buộc nguyên tắc, không phải khiếm khuyết cài đặt: với $D$ = 1.272 (56,8% toàn bộ lỗi), nhiều chuỗi ngắn hơn độ dài mong đợi khiến mặt nạ lệch pha và luật khi đó **không dám sửa** chứ không sửa bừa — **0 biển bị làm hỏng** là hệ quả quan sát được của thiết kế bảo thủ đó. Kết luận đúng phạm vi cho RQ3: *khối hậu xử lý đóng góp **+11,39 điểm** trên 2.801 biển — **+13,97 điểm riêng trên biển hai dòng** — cải thiện thuần không rủi ro (319 / 0), nhưng không đủ đưa A6 tới ngưỡng vì phần lỗi còn lại đã dịch sang dạng đọc hụt ký tự, nơi hậu xử lý theo luật về nguyên tắc không với tới được.* Rất ít công trình ALPR đo tách bạch đại lượng này.

### 5.5.3. Tách theo biển một dòng và hai dòng cho OCR

<!-- {{T5.5c}} OCR tach theo layout mot dong / hai dong -->

**Bảng 5.5.** Độ chính xác nhận dạng tách theo biển một dòng và hai dòng

| Chỉ số | Biển **một dòng** | Biển **hai dòng** | Chênh (điểm %) |
|---|---:|---:|---:|
| Số mẫu có nhãn chuỗi *(tổng 2.801)* | **567** | **2.234** | n/a |
| 1 − CER (NFR-A4) | 0,9925 | 0,9344 | 5,81 |
| Chuỗi đúng **trước** hậu xử lý (A5) | 0,9418 | 0,5600 | 38,18 |
| Chuỗi đúng **sau** hậu xử lý (A6) | 0,9541 | 0,6996 | 25,45 |
| Cải thiện do hậu xử lý (A6 − A5) | +1,23 | +13,97 | n/a |
| Độ chính xác E2E (A7) | 0,6861 | 0,5219 | — |

**Đây là kết quả khoa học quan trọng nhất của chương.** Chênh lệch mà tầng phát hiện gần như che khuất (2,09 điểm, Bảng 5.2) nay lộ ra ở tầng OCR với **biên độ khác hẳn cấp**: 5,81 điểm ở mức ký tự, **25,45 điểm** ở A6, **38,18 điểm** ở A5. **Biển một dòng về cơ bản đã giải xong** (A6 = 0,9541 vượt cả mục tiêu 0,90), toàn bộ việc "OCR không đạt" là do **biển hai dòng kéo xuống**; vì biển hai dòng chiếm **2.234 / 2.801 = 79,8%** tập có nhãn chuỗi (phản ánh tỉ lệ xe máy rất cao ở Việt Nam), con số tổng bị quần thể khó này chi phối. **25,45 điểm là con số *sau* khi đã áp cả hai bậc cứu chữa** (5.5.6, 5.5.7): ở lượt 20/07, A6 biển hai dòng là 0,5810 và khoảng cách là 36,79 điểm — chuỗi biện pháp đã thu hẹp **11,34 điểm**, một dịch chuyển thật nhưng vẫn để lại một phần tư khoảng cách; phần còn lại nằm ở **năng lực nhận dạng ký tự**, không ở khâu cắt/ghép hay hình học, vì cả hai khâu sau đã xử lý và đo tách bạch.

**Mốc tham chiếu quốc tế — phải đọc kèm cảnh báo.** Laroca và cộng sự (VISAPP 2022) báo cáo **94,3%** trên biển một dòng và **45,7%** trên biển hai dòng, chênh **48,6 điểm phần trăm**, đo trên bộ dữ liệu **RodoSol-ALPR của Brazil** [7]<!-- laroca_2022_crossdataset -->. **Đây là số liệu Brazil, không phải Việt Nam**, và biển hai dòng Brazil khác biển hai dòng Việt Nam cả về tỉ lệ khung hình lẫn bộ ký tự. **Đối chiếu bậc độ lớn:** **25,45 điểm** (biển số **Việt Nam thật**, 2.801 biển có nhãn chuỗi) so với **48,6 điểm** trên RodoSol-ALPR **Brazil** — **cùng bậc độ lớn**. Không được kết luận mạnh hơn: 25,45 < 48,6 **không** có nghĩa hệ thống này "tốt hơn", vì hai phép đo khác bộ dữ liệu, khác bộ ký tự, khác tỉ lệ khung hình, khác mẫu số. Kết luận hợp lệ duy nhất: khoảng cách hai layout **thuộc đúng bậc độ lớn** mà tài liệu quốc tế đã ghi nhận — đặc tính có cấu trúc của bài toán, không phải khiếm khuyết riêng của hệ thống. **Chưa có nghiên cứu Việt Nam nào công bố hai con số này tách bạch trên cùng một hệ thống**; Bảng 5.5 lấp khoảng trống đó và trả lời RQ2: **có, chênh lệch có ý nghĩa và rất lớn (25,45 điểm A6), nằm ở tầng OCR chứ không ở tầng phát hiện.**

### 5.5.4. Ma trận nhầm lẫn ký tự 36×36

Mục này trả lời RQ5: **thay tri thức suy đoán bằng tri thức đo được.** Bảng luật hiện hành trong `ai/inference/plate_rules.py` gồm `TO_DIGIT = {O→0, Q→0, D→0, I→1, J→1, L→1, Z→2, A→4, S→5, G→6, T→7, B→8}` và `TO_LETTER = {0→D, 1→L, 2→Z, 3→B, 4→A, 5→S, 6→G, 7→T, 8→B}`. Docstring thừa nhận nguồn gốc: *"This table is derived from glyph-shape reasoning, not from measurement"*, và đánh dấu một số cặp (đặc biệt `L→1`) là **phỏng đoán yếu**. Ma trận 36×36 (10 chữ số + 26 chữ cái) đo trên các cặp ký tự đã căn chỉnh là bằng chứng thực nghiệm để chuyển giả thuyết đó thành tri thức. Hai hình minh hoạ — ma trận 36×36 thang log(1+n) (`04-ocr-confusion-matrix.png`) và biểu đồ cột 15 cặp bị nhầm nhiều nhất (`04-ocr-top-confusions.png`) — **chưa sinh**.

<!-- {{T5.5d}} top cac cap ky tu bi nham thuc te, doi chieu bang luat hien hanh -->

**Bảng 5.6.** Các cặp ký tự bị nhầm nhiều nhất, đối chiếu bảng luật hiện hành

| Hạng | Ký tự thật → bị đọc thành | Số lần | Tỉ lệ trong tổng lỗi thay thế | Bảng luật có phủ không? |
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

**RQ5 được trả lời theo hướng ít ai ngờ: bảng luật hiện hành phần lớn *không khớp* các cặp nhầm thật.** Chỉ **2/10** cặp nhầm nhiều nhất được phủ; **8 cặp còn lại chưa có luật nào phủ** — đáng chú ý `E→F`, `4→L`, `U→1`, đều là cặp **suy đoán hình dạng không dự đoán được**, phát sinh từ đặc thù phông chữ biển số và điều kiện ảnh thật. Ngược lại, bảy cặp *có* trong bảng luật lại có **số lần quan sát bằng 0** và thuộc diện *xem xét loại*: `D→0`, `J→1`, `A→4`, `T→7`, `B→8` (`TO_DIGIT`) và `2→Z`, `3→B` (`TO_LETTER`).

> **Hai chiều của cùng một cặp glyph.** `L → 1` (ký tự thật L bị đọc thành chữ số 1) quan sát **90 lần**; nhưng chiều ghi trong `TO_DIGIT` là "khi engine đọc ra `L` tại vị trí chữ số thì đổi `L → 1`" — chiều này chỉ khớp **2 lần**. Bất đối xứng ấy đúng chứ không phải lỗi: bảng luật sửa ký tự *engine đọc ra*, ma trận nhầm lẫn đếm ký tự *thật bị đọc sai*. Đề xuất hiệu chỉnh đầy đủ ở khoá `doi_chieu_bang_luat.proposed_updates` trong `05-results.json`.

`O → 0` hợp lệ tại vị trí chữ số, nhưng `0 → O` **không bao giờ** hợp lệ vì `O` không phải chữ cái sê-ri hợp pháp; loại cả `O` và `Q` thì ứng viên đồng hình duy nhất ở vị trí chữ cái là `D`, nên chiều đúng là `O → 0` tại vị trí chữ số và `0 → D` tại vị trí chữ cái. Ma trận chỉ đếm tần suất; chuyển từ tần suất sang luật vẫn cần **ràng buộc miền** từ quy chuẩn biển số. **Tiêu chí chấp nhận một cặp vào bảng luật đã hiệu chỉnh** (định trước để tránh chọn theo kết quả): (1) tần suất vượt một ngưỡng thống kê tối thiểu; (2) chiều ánh xạ **tương thích với ràng buộc vị trí** của định dạng biển số Việt Nam; (3) áp vào toàn tập cho **đóng góp thuần không âm**. Không thoả cả ba thì loại, **kể cả khi nghe có vẻ hợp lý về hình dạng chữ**.

### 5.5.5. Độ chính xác đầu-cuối toàn trình (NFR-A7)

<!-- {{T5.5e}} do chinh xac E2E toan trinh NFR-A7 — chuyen thanh van xuoi -->

NFR-A7 đo **ảnh đầu vào → phát hiện → cắt → OCR → hậu xử lý → chuỗi cuối**; khác A6 ở chỗ A6 đo trên **vùng biển cắt chuẩn theo nhãn thật** còn A7 đo trên vùng biển do **chính bộ phát hiện** tìm ra, nên A7 tích luỹ cả hai nguồn sai số và theo lý thuyết luôn ≤ A6. Trên 2.801 mẫu: **A7 = 0,5552** (sàn 0,82, mục tiêu 0,88 — ❌); **E2E với điều kiện đã phát hiện được biển = 0,6306**; tỉ lệ biển **bỏ sót** ở tầng phát hiện **0,1196**; phát hiện đúng nhưng **đọc sai chuỗi 0,3694**; chênh **A6 − A7 = 19,60 điểm**.

> ⚠ **Cảnh báo hiệu lực — phải đọc trước khi diễn giải A7.** Con số 0,5552 đo trên **ảnh crop biển số**, không phải ảnh hiện trường, vì không bộ dữ liệu nào trong đồ án có đồng thời ảnh toàn cảnh *và* chuỗi biển số nhãn thật. Bộ phát hiện được huấn luyện trên ảnh giao thông đầy đủ nên ảnh chỉ có biển số chiếm gần hết khung là **ngoài phân bố huấn luyện**: phần lớn thất bại ở đây do bộ phát hiện không bắt được box trên ảnh crop (bỏ sót 11,96%), **không** phải do OCR đọc sai. Bằng chứng: trên ảnh hiện trường thật, Phase 7 đo mAP@0.5 = 0,9829, tương thích với 5.4.1. Muốn đo NFR-A7 đúng cách cần gán nhãn chuỗi cho một phân bố test có ảnh hiện trường (ví dụ một phần yolo_v2) — **việc này chưa làm.**

Nguồn lỗi được phân tách rõ: **335 / 2.801 = 11,96%** biển bỏ sót ở tầng phát hiện, và trong số đã phát hiện được, **36,94%** đọc sai chuỗi. Do cảnh báo hiệu lực, tỉ lệ bỏ sót 11,96% **bị thổi phồng bởi việc đo trên ảnh crop ngoài phân bố**; kết luận đúng phạm vi: *A7 = 0,5552 phản ánh giới hạn của **giao thức đo hiện có** chồng lên giới hạn thật của tầng OCR trên biển hai dòng — **cận dưới bi quan**, không phải ước lượng điểm.* Chỉ tăng recall bộ phát hiện cũng không đưa A7 lên quá 0,6306; trần thật bị chặn bởi tầng OCR. **Vì sao A7 tăng chậm hơn A6:** mọi biện pháp cứu chữa áp vào **cả hai** đường đo nhưng bị **pha loãng** ở A7 vì 11,96% số biển thất bại ngay ở tầng phát hiện, phần cải thiện chỉ tác động trên **88,04%** mẫu còn lại. Giữa 20/07 và 28/07, **`missed_by_detector` giữ nguyên đúng 335 và tỉ lệ phát hiện giữ nguyên đúng 0,8804** — bộ trọng số phát hiện không đổi, nên toàn bộ mức tăng của A7 đến từ khối nhận dạng, đo đúng bằng độ chính xác có điều kiện: 0,6014 → **0,6306**, tức **+2,92 điểm**; A7 tăng ít hơn (**+2,57 điểm**) vì bị 335 ca vô vọng kéo xuống — hệ quả số học, **không** phải dấu hiệu sai sót.

### 5.5.6. Bước "cứu dòng trên" cho biển hai dòng — thiết kế, kiểm chứng A/B và kết quả trên toàn tập

<!-- {{T5.5f}} A/B hai chien luoc doc bien hai dong — chuyen thanh van xuoi -->
<!-- {{T5.5g}} A/B buoc cuu dong tren, hai mau doc lap — chuyen thanh van xuoi -->
<!-- {{T5.5h}} truoc/sau buoc cuu dong tren tren toan tap co nhan chuoi — chuyen thanh van xuoi -->

Hồ sơ lỗi thiên về *xoá* ($D$ = 1.272 > $S$ = 862) trên biển hai dòng có cách giải thích tự nhiên: **mất hẳn một dòng**. Hệ thống đọc biển hai dòng bằng **ghép-rồi-đọc** (*split-then-hstack*): cắt vùng biển thành hai nửa chồng lấn, xếp cạnh nhau thành dải ngang, chạy OCR **một lần**. Phương án thay thế — đọc riêng từng nửa rồi nối chuỗi — đã được đo A/B chứ không bị loại bằng lập luận, trên 200 biển hai dòng (`seed = 20260720`, `docs/reports/15-two-line-ab.json`): **A, ghép rồi OCR một lần** *(đang dùng)* đúng **129/200 = 64,50%**, 2 ca OCR trả chuỗi rỗng, 340,11 ms; **B, OCR từng nửa rồi nối** đúng **7/200 = 3,50%**, 9 ca chuỗi rỗng, 391,35 ms — B kém A **61,00 điểm phần trăm** và đắt hơn **51,24 ms**; **122** ca A thắng B, **0** ca B thắng A. **Giả thuyết "đọc riêng từng dòng thì chính xác hơn" bị bác bỏ dứt khoát.** Nguyên nhân đọc được ngay trong dữ liệu: hai nửa **cố ý chồng lấn** để không cắt cụt ký tự, nên đọc riêng thì dải chồng lấn bị đọc **hai lần** và ký tự bị nhân đôi — `84G122593` thành `84-G124E009.01225.93`. Một kết quả âm có giá trị: lựa chọn kiến trúc ở Chương 5 không tuỳ tiện.

Dải ghép vẫn có chế độ thất bại riêng: khi **dòng trên nằm lệch thấp** trong vùng cắt rộng rãi, bộ dò chữ chỉ tìm thấy **một vùng văn bản** — dòng dưới — và mã tỉnh cùng chữ cái sê-ri **mất hoàn toàn** (`29E-015.66` → `015.66`, năm chữ số trần không khớp định dạng nào nên khối kiểm tra hợp lệ **bác bỏ đúng**); chính sự bác bỏ đó là tín hiệu dùng được. Bước **cứu dòng trên** (`rescue_two_line_upper`) có cổng rất hẹp: (1) chỉ kích hoạt khi **cả ba** điều kiện đồng thời đúng — `line_count = 2`, chuỗi sau chuẩn hoá **không hợp lệ định dạng**, chuỗi thô **không rỗng**; (2) đọc **riêng nửa trên** bằng một lời gọi OCR bổ sung; (3) nối `nửa trên + chuỗi thô của dải ghép` rồi cho qua lại khối chuẩn hoá; (4) **chỉ giữ kết quả mới nếu nó hợp lệ định dạng**, mọi trường hợp khác — kể cả ngoại lệ — trả về kết quả cũ. Điều kiện (1) khiến bước này **về mặt cấu trúc không thể làm hỏng** một biển vốn đã đọc đúng.

Kiểm chứng A/B trên **hai mẫu độc lập** (`15-two-line-fallback-700.json`, `15-two-line-fallback.json`; hai seed khác nhau). **700 biển, `seed = 7`:** 421/700 = **60,14%** → 434/700 = **62,00%**, **+1,86 điểm**, **13 biển được cứu**, **0 bị hỏng**, kích hoạt 21,14% (148/700), 362,41 → 383,52 ms. **200 biển, `seed = 20260720`:** 129/200 = **64,50%** → 130/200 = **65,00%**, **+0,50 điểm**, **1 biển được cứu**, **0 bị hỏng**, kích hoạt 18,00% (36/200), 346,70 → 361,97 ms. **Dấu của hiệu số nhất quán trên cả hai mẫu và không mẫu nào có ca bị làm hỏng**, đúng dự đoán từ cấu trúc cổng; nhưng **độ lớn không nhất quán** (+1,86 so với +0,50) — với mẫu 200 biển, một biển được cứu đã bằng 0,5 điểm nên +0,50 nằm hoàn toàn trong dao động lấy mẫu và **không được dùng làm bằng chứng độc lập**, nó chỉ xác nhận *không có hồi quy*. Chi phí khoảng **21 ms** mỗi biển, chỉ trên những vùng cắt vốn đã thất bại.

> ⚠ **Số liệu toàn tập của riêng bước cứu là số lịch sử 20/07, giữ nguyên mốc.** Trên 2.801 ảnh có nhãn chuỗi (`16-ocr-accuracy-rescued.json`, `best.pt`, `imgsz = 640`; cột "trước" là lượt đo trước đó trên đúng cùng tập mẫu và cùng mô hình): A4 0,8734 → **0,8848** (**+1,14**; sàn 0,92 ❌); A5 0,6098 → **0,6098** (**0,00**; sàn 0,80 ❌); A6 0,6555 → **0,6730** (**+1,75**; sàn 0,85 ❌); A7 0,5227 → **0,5295** (**+0,68**; sàn 0,82 ❌); A6 riêng biển **một dòng** 0,9489 → **0,9489** (**0,00**); A6 riêng biển **hai dòng** 0,5810 → **0,6030** (**+2,20**); biển bị can thiệp / thành đúng hoàn toàn / bị làm hỏng = **89 / 2.801** · **49** · **0**. Bảng số này trả lời đúng một câu hỏi — *riêng bước cứu dòng trên đóng góp bao nhiêu* — và câu trả lời ấy không đổi theo thời gian; nhưng **các giá trị tuyệt đối đã bị vượt qua** (A6 hiện là 0,7512 chứ không phải 0,6730) nên **không được trích cột "sau bước cứu" như số hiện hành**. Trên lượt 28/07, bước cứu dòng trên cho câu trả lời cuối ở **209 biển**.

**Ba ô "không đổi" phải đọc như bằng chứng, không như thiếu sót:** A5 không đổi vì bước cứu chạy **sau** khối chuẩn hoá nên **không thể** tác động lên chỉ số đo *trước* chuẩn hoá; biển một dòng không đổi vì cổng yêu cầu `line_count = 2` và toàn bộ 89 biển can thiệp đều là biển hai dòng; số bị làm hỏng bằng 0 vì chuỗi đã hợp lệ không bao giờ được thử lại. Tác dụng thật nằm đúng nơi được nhắm — **biển hai dòng, +2,20 điểm** — và vẫn để lại **bốn chỉ tiêu OCR đều không đạt**.

**Ghi chú phương pháp đo — ba lần cùng một loại lỗi, ghi lại thay vì giấu đi.** Lượt đo lại **đầu tiên** sau khi thêm bước cứu cho kết quả tự mâu thuẫn: **A6 tăng 1,75 điểm trong khi A7 đứng yên ở đúng 0,5227**. A7 **bao hàm** phần A6 đo, nên một biện pháp đang thực sự chạy **không thể** nâng chỉ số con mà để chỉ số bao hàm nó bất động ở từng chữ số thập phân. Nguyên nhân: trong `ai/evaluation/ocr_accuracy.py`, bước cứu mới chỉ nối vào nhánh A5/A6, còn **hàm dựng đường E2E vẫn gọi thẳng bộ chuẩn hoá rồi trả kết quả**; nối xong và đo lại, A7 mới lên 0,5295. Đó là **lần thứ hai**; lần thứ nhất ở chính nhánh A5/A6, cả hai lần triệu chứng đều là một chỉ số **đứng yên một cách vô lý** — dễ được cho qua hơn nhiều so với một con số sai.

> Khi chỉ số $X$ **bao hàm** chỉ số $Y$ về mặt định nghĩa, mà một can thiệp làm $Y$ dịch chuyển còn $X$ thì không nhúc nhích, **giả thuyết đầu tiên phải là đường đo của $X$ bị lệch khỏi đường chạy thật**.

**Biện pháp đặt ra khi đó — viết bước cứu thành hàm tự do dùng chung — đã thất bại.** Ngày 28/07/2026, **đúng loại lỗi ấy xuất hiện lần thứ ba**: bậc thang thử-lại (5.5.7), thêm vào pipeline ngày 21/07, **chưa bao giờ được kịch bản đánh giá gọi** ở cả hai nhánh, nên mọi con số A4–A7 công bố từ 21/07 đến 28/07 mô tả một pipeline ngắn hơn bản giao hàng. Bậc thang **đã** được viết đúng như biện pháp quy định (`should_retry_skewed`, `retry_skewed_variants` là hàm tự do dùng chung) — biện pháp được tuân thủ đầy đủ mà lỗi vẫn tái diễn, vì hàm dùng chung chỉ bảo đảm **nếu** kịch bản gọi thì gọi đúng bản cài đặt, chứ **không** bảo đảm kịch bản có gọi. Nguyên nhân gốc: `measure_crops` và `_run_pipeline` **dựng lại đường xử lý thay vì gọi nó**, nên mỗi bậc mới thêm vào `ALPRPipeline._process_one` đều **mặc định rơi ra ngoài phép đo**, im lặng.

> Một đường đo **liệt kê lại** các bước của hệ thống sẽ lệch khỏi hệ thống ở đúng thời điểm hệ thống thay đổi — tức đúng thời điểm phép đo cần chính xác nhất. Chia sẻ mã ở mức *hàm* không đủ; chỉ **gọi thẳng cùng một điểm vào** mới đủ.

Hai chốt chặn được thêm: kịch bản ghi thẳng **trạng thái các công tắc** vào tệp kết quả, và ghi **số biển mà từng bậc cứu được** (`recovery_contribution`) — một bậc không được gọi giờ hiện ra dưới dạng số 0 có nhãn thay vì biến mất không dấu vết. Biện pháp triệt để — cho harness đầu-cuối gọi thẳng `ALPRPipeline.process` — vẫn là **việc bỏ ngỏ**, ghi ở 5.9.2.

### 5.5.7. Bậc thang thử-lại cho biển nghiêng/méo — chi phí, lợi ích và một quyết định tắt tính năng

<!-- {{T5.5i}} chi phi - loi ich cua tung bac trong bac thang thu-lai — chuyen thanh van xuoi -->

Chế độ thất bại thứ hai: **biển bị nghiêng hoặc méo phối cảnh**, khiến tỉ lệ khung hình lệch đủ để bộ phân loại bố cục xếp nhầm, hoặc khiến ký tự dính vào nhau. Bậc thang thử-lại dùng ba biến thể theo thứ tự rẻ trước: **nắn hình trong mặt phẳng**, **giãn dọc chống méo phối cảnh**, **siêu phân giải** cho vùng cắt quá nhỏ. **Điểm mấu chốt là cổng kích hoạt, không phải các biến thể:** hình học từng được đo ở dạng *luôn bật* và kết quả là **mất** — 42 lần đọc hợp lệ tụt xuống 40, vì một hình chữ nhật khớp sai trên vùng cắt nhỏ và mờ sẽ cắt cụt ký tự của một biển vốn đang đọc tốt. Đặt nó **sau cổng "lần đọc đầu đã thất bại"** đảo ngược kinh tế học: đường đi của biển đọc đúng **không bị chạm tới về mặt cấu trúc**, mọi ca cứu được là lãi ròng.

Bóc tách chi phí – lợi ích từng bậc (độ chính xác trên 2.801 biển có nhãn chuỗi; độ trễ trên 100 ảnh hiện trường của tập test v3, máy rảnh; nguồn `27-ocr-accuracy-with-ladder.json` và ba lượt `ai.evaluation.benchmark_system` bóc tách qua `ALPR_RECTIFY_ENABLED` / `ALPR_SR_RETRY_ENABLED`; phân tích đầy đủ ở `docs/reports/27-retry-ladder-cost-benefit.md`): **tắt hẳn bậc thang** — 1 − CER 0,9416, A6 0,7437, **0 biển được cứu**, p95 **866,3 ms**, p99 1.101,1 ms; **nắn hình / giãn dọc** *(cấu hình giao hàng)* — 1 − CER **0,9454**, A6 **0,7512**, **34 biển được cứu**, p95 **1.110,4 ms**, p99 1.349,0 ms; **thêm siêu phân giải** — 1 − CER 0,9454, A6 0,7512, vẫn **34 biển**, p95 **1.428,7 ms**, p99 **2.730,4 ms**.

**Bậc thang gần như miễn phí ở trường hợp thường và rất đắt ở đuôi:** trung vị chỉ tăng 3,7% (405,8 ms) trong khi p99 tăng 148%. **Nắn hình / giãn dọc: giữ** — mua 34 biển (+0,75 điểm A6, +0,38 điểm A4) với giá +244 ms ở p95. **Siêu phân giải: tắt mặc định** — mua **0 biển** với giá **+319 ms ở p95 và +1.381 ms ở p99**, và một mình nó đẩy NFR-P1 vượt ngưỡng tối thiểu 1.500 ms. **Vì sao số 0 đó không phải bằng chứng nó vô dụng:** cổng của bậc này chỉ mở cho vùng cắt có cạnh dài **≤ 200 px**, mà đo trên **120 mẫu** ngẫu nhiên của tập có nhãn chuỗi, cạnh dài sau bước khôi phục tỉ lệ khung hình có **giá trị nhỏ nhất 565 px, trung vị 868 px** — **0/120 mẫu lọt cổng**. Ngữ liệu này **không thể kích hoạt** nên **không thể đo** bậc siêu phân giải; số 0 là **số 0 cấu trúc**, không phải kết quả âm. Suy ra: toàn bộ 34 biển cứu được đều là công của nắn hình / giãn dọc, và quyết định tắt **không** dựa trên "đã đo và thấy vô dụng".

> Chi phí đã đo được và lớn; lợi ích **chưa ai đo được** trên bất kỳ tập đại diện nào; trong khi NFR-P1 là yêu cầu mức *Must* và riêng bậc này làm nó vượt ngưỡng. Một lợi ích chưa định lượng không đủ để biện minh cho một vi phạm đã định lượng.

Bằng chứng duy nhất hiện có cho bậc siêu phân giải vẫn là **một vùng cắt demo được chọn tay trong bốn ca thử**. Mã, kiểm thử, công tắc và báo cáo **giữ nguyên**; `ALPR_SR_RETRY_ENABLED=true` là bật lại. Muốn đo cho tử tế cần một tập **vùng cắt nhỏ do chính bộ phát hiện sinh ra, có nhãn chuỗi** — đồ án không có, hạng mục bỏ ngỏ ghi ở 5.11.

---

## 5.6. Đánh giá hiệu năng

> Mọi số trong 5.6 phải đọc cùng cấu hình ở 5.2: **Intel Raptor Lake 14 nhân / 20 luồng, Windows 11, CPU-only, kích thước lô = 1**.

### 5.6.1. Độ trễ đầu-cuối (NFR-P1)

<!-- {{T5.6a}} do tre dau-cuoi mot anh, doi chieu NFR-P1 -->

**Bảng 5.7.** Độ trễ đầu-cuối một ảnh, đối chiếu NFR-P1

| Chỉ số | Sàn | Mục tiêu | **Trước bậc thang (20/07)** | **Cấu hình giao hàng (28/07)** | Kết quả |
|---|---:|---:|---:|---:|:---:|
| p50 (ms) | — | — | 414,67 | 405,77 | n/a |
| **p95 (ms)** | **≤ 1500** | **≤ 800** | **731,15** | **1.143,10** | **🟡** |
| p99 (ms) | — | — | 947,83 | 1.420,07 | n/a |
| Trung bình (ms) | — | — | 400,74 | 447,38 | n/a |
| Số ảnh đo | — | — | 100 | 100 | n/a |
| Bội số so với sàn / mục tiêu | — | — | 0,49× / 0,91× | **0,76×** / **1,43×** | n/a |

> Số biển trung bình mỗi ảnh 1,33, cùng 100 ảnh test v3, cùng máy rảnh (CPU idle ~5%, không có tiến trình huấn luyện song song). **Hai cột đo hai phiên bản hệ thống, không phải hai phương pháp đo**: cột trái là trạng thái 20/07 trước khi có bậc thang (client-side qua HTTP, `07-benchmark-p1-resolved.json`); cột phải là cấu hình giao hàng 28/07 (in-process, `benchmark_system.py`, `05-results.json`). Chênh lệch phương pháp giữa hai cách đo là **~7%** — kiểm chứng ngày 20/07 khi cả hai cùng chạy trên một hệ thống (731,15 so với 780,36 ms) — nên nó **không** giải thích được mức tăng ở đây. Hình phân bố độ trễ kèm vạch p50/p95/p99 (`07-latency-distribution.png`) **đã có nhưng cần vẽ lại cho `best.pt`**.

**NFR-P1 đạt ngưỡng tối thiểu nhưng không đạt mục tiêu**, và đây là **thoái lui có chủ ý và đã định lượng**: tắt hẳn bậc thang thử-lại đưa p95 về **866,3 ms**, tức toàn bộ **+277 ms** là của nó; nhưng vì bậc thang chỉ chạy **sau khi lần đọc đầu thất bại** nên nó không chạm vào trường hợp thường — **trung vị thậm chí giảm nhẹ** (414,67 → 405,77 ms), chi phí dồn hết vào đuôi. Với hệ thống mà 95% ảnh xong dưới 1,15 giây và một nửa xong dưới 0,41 giây, p50 mô tả trải nghiệm điển hình còn p95 mô tả trường hợp xấu; NFR-P1 phát biểu theo p95 nên kết luận chính thức là **đạt sàn, không đạt mục tiêu**. Ở lượt đo đầu với cả ba biến thể bật, p95 là **1.514,26 ms** — **vượt cả ngưỡng tối thiểu**; bóc tách chỉ ra bậc siêu phân giải chiếm hơn nửa chi phí đó mà không mua được biển nào đo được nên nó bị **tắt mặc định**, đưa p95 về 1.143,10 ms.

**Giải quyết mâu thuẫn với con số cũ 5.857 ms.** Báo cáo Phase 7 trước đây ghi p95 = 5.857,19 ms và kết luận NFR-P1 "không đạt" — chênh **7,5 lần**. Phép đo cũ đã bị **bác bỏ**: (1) **nhiễu do tranh chấp CPU** — `07-benchmark-data.json` ghi rõ có tiến trình `ai.training.train` chiếm 793% CPU chạy song song, và chính báo cáo cũ khi tính lại trên 80 mẫu ít nhiễu đã ra ~3.283 ms; (2) đo trên **checkpoint epoch 7**, không phải `best.pt`; (3) checkpoint đó có **lỗi crop** khiến PaddleOCR chạy cả khối phát hiện văn bản trên ảnh lớn (~1.322 ms/ảnh). Đo lại trên máy rảnh với `best.pt`: p95 còn 731 ms. Giả thuyết "cold-start / oneDNN chưa tắt" **không** phải nguyên nhân — server chạy `enable_mkldnn=false` và có warmup (cold-start đo được chỉ **176 ms** p95); giả thuyết "baseline-416-v1 vốn chậm" cũng bị loại — client-side nó ra **763,75 ms** p95, gần y hệt `best.pt`.

### 5.6.2. Phân rã ngân sách độ trễ theo từng bước

<!-- {{T5.6b}} phan ra ngan sach do tre theo tung buoc, doi chieu uoc luong Phase 0 -->

**Bảng 5.8.** Phân rã ngân sách độ trễ theo từng bước

| Bước xử lý | Ước lượng Phase 0 (ms) | **Đo thật (ms)** | Chênh (lần) | % tổng |
|---|---:|---:|---:|---:|
| Giải mã ảnh + tiền xử lý | 50 | **2,83** | 0,06 | **1,7%** |
| Suy luận YOLO11n @ 640px (CPU) | 150 | **57,27** | 0,38 | **34,0%** |
| Cắt + tiền xử lý vùng biển số | 30 | **0,00** | 0,00 | **0,0%** |
| **PaddleOCR (mỗi biển)** | **120** | **108,28** | 0,90 | **64,3%** |
| Hậu xử lý regex + kiểm tra hợp lệ | 5 | **0,03** | 0,01 | **0,0%** |
| Ghi CSDL + lưu ảnh | 50 | — | — | — |
| **Tổng (một biển số)** | **405** | **168,41** | 0,47 | **100%** |

> Mẫu số: 40 ảnh, trung bình 1,57 biển mỗi ảnh, đo trên `best.pt`. Bước "ghi CSDL + lưu ảnh" giữ `—` vì `benchmark_system` đo pipeline suy luận thuần, không đi qua tầng API; cột chênh lệch ở dòng tổng so với ước lượng **cùng phạm vi** (đã trừ ghi CSDL, **~355 ms**), không so với 405 ms tròn. Hình cột chồng đối chiếu ước lượng với số đo (`07-latency-budget.png`) **đã có nhưng cần vẽ lại**.

Ba phát hiện. **Một, ước lượng Phase 0 sát bất ngờ ở tổng nhưng lệch ở phân bổ:** tổng suy luận thuần **168,41 ms/biển**, nhỏ hơn cả ước lượng Phase 0 — ước lượng ban đầu **không** sai một bậc độ lớn như con số nhiễu 5.857 ms từng khiến người ta tin. **Hai, nút thắt là PaddleOCR nhưng KHÔNG áp đảo như báo cáo cũ:** 64,3% so với 34,0% của bộ phát hiện, **thay thế** con số cũ "OCR 93,3% / detect 6,5%" vốn đo trên hệ thống đang có lỗi crop (~1.322 ms/ảnh); nguyên nhân OCR đắt vẫn đúng — PaddleOCR là **pipeline nhiều giai đoạn** (phát hiện văn bản → phân loại hướng → nhận dạng) thiết kế cho ảnh tài liệu tổng quát, nên hệ thống trả chi phí cho năng lực mà vùng biển đã cắt không cần. **Ba, chiến lược tối ưu đổi hẳn:** theo định luật Amdahl, tăng tốc detector 2–3× có thể kéo E2E xuống quãng **15–23%**, khác hẳn kết luận cũ "chỉ giảm tối đa 6,7%"; và vì NFR-P1 mới đạt sàn còn NFR-P2 trượt cả sàn (2,379 FPS, sàn 3), tối ưu hiệu năng nằm trên đường tới chỉ tiêu chứ không chỉ là *dư địa cải thiện thêm*.

### 5.6.3. So sánh backend suy luận: PyTorch, ONNX Runtime và OpenVINO

<!-- {{T5.6c}} so sanh backend suy luan cho bo phat hien -->

**Phép so sánh backend *(chưa đo)*.** Lượt `benchmark_cpu --backends pytorch onnx openvino` **chưa chạy**, nên toàn bộ các ô — độ trễ p50/p95 riêng bộ phát hiện, mức tăng tốc so với PyTorch (mốc **1,00×**), độ trễ E2E p95 và phần trăm cải thiện E2E của ONNX Runtime và OpenVINO — đều *(chưa đo)*. Chỉ tiêu **mAP@0.5 sau khi xuất** phải đo cùng lúc để kiểm tra việc chuyển đổi định dạng **không làm suy giảm độ chính xác**; nếu có suy giảm, mức tăng tốc phải được đánh giá như một đánh đổi. Khi đo xong sẽ điền từ `docs/reports/07-benchmark-optimized.json`. Thí nghiệm vẫn đáng làm dù kết luận đoán trước được từ 5.6.2: nó **kiểm chứng** lập luận Amdahl bằng số liệu [18]<!-- ultralytics_2026_openvinoexport --> [117]<!-- onnxruntime_2025_threading -->.

> **Tối ưu backend của bộ phát hiện GIỜ có ý nghĩa, nhưng chưa đủ một mình.** Vì NFR-P1 **chỉ đạt sàn** còn NFR-P2 **trượt sàn**, đây không phải dư địa cải thiện thêm mà là đường dẫn tới chỉ tiêu; muốn giảm mạnh hơn thì khối OCR (64,3%) vẫn là mục tiêu lớn nhất.

Bốn hướng tấn công khối OCR theo chi phí tăng dần (chi tiết ở Chương 6): **tắt các giai đoạn không cần thiết của pipeline PaddleOCR**; **bật MKL-DNN và chỉnh số luồng CPU**; **xuất mô hình nhận dạng sang ONNX Runtime**; **thay bằng mô hình nhận dạng chuyên cho biển số** huấn luyện trên tập ký tự hẹp (10 chữ số + tập chữ cái hợp lệ) — tiềm năng lớn nhất, tốn công nhất.

### 5.6.4. Chế độ webcam (tầng API) và xử lý video (NFR-P2, NFR-P3)

<!-- {{T5.6d}} hieu nang che do webcam va xu ly video — gop vao T5.7 -->

> Từ 2026-07-20, trang Webcam đã gỡ khỏi giao diện web (thu gọn phạm vi — 4.1.3b); chế độ thời gian thực chỉ còn ở tầng API, nên NFR-P2 đo bằng kịch bản gọi trực tiếp `POST /api/detect/frame`. Số liệu đầy đủ ở Bảng 5.10.

**NFR-P2 không đạt (2,379 FPS; sàn 3, mục tiêu 5), nguyên nhân không phải tốc độ trung bình mà là *đuôi phân bố*.** Trung vị mỗi khung chỉ **180,05 ms** — tương ứng 5,6 FPS, vượt mục tiêu — nhưng p95 là **1.247,70 ms**, và giao diện thời gian thực dùng **hàng đợi một khe**: chỉ một yêu cầu bay tại một thời điểm, khung sinh ra trong lúc chờ bị bỏ thay vì xếp hàng; ở kỷ luật đó thông lượng bị chi phối bởi những lần chậm nhất. Đuôi ấy chính là bậc thang thử-lại (5.5.7) — **đánh đổi đã biết**: cùng cơ chế đó mua thêm 34 biển đọc đúng và đẩy NFR-P1 từ ✅ xuống 🟡. Ngược lại NFR-P3 **đạt**: video 14,25 giây xử lý hết **19,1 giây** (sàn ≤ 95 s, mục tiêu ≤ 47,5 s), tức **0,746×** thời gian thực — **0,546 s mỗi khung phân tích**, `vid_stride = 5`.

**Định nghĩa đã dùng, nêu rõ để không phóng đại:** "FPS hiệu dụng" là **số khung được nhận dạng xong mỗi giây** (**144 khung** trong **60,52 giây**, **0 yêu cầu lỗi**), không phải số khung hiển thị; camera ảo chào **1.815 khung** ở 30 FPS và **1.671 khung bị bỏ** — con số bỏ này được báo cáo chứ không giấu, vì công bố riêng "144 khung, 0 lỗi" sẽ khiến người đọc hiểu nhầm là hệ thống theo kịp nguồn. **Con số này là cận trên:** phép đo chạy qua HTTP loopback với ảnh có sẵn trên đĩa nên **không** tính thời gian camera thu hình, mã hoá JPEG trong trình duyệt và vẽ canvas. Dự đoán trước đó là **~1,4 FPS** (suy từ p95 0,73 giây và giả định xử lý tuần tự); số đo thực **2,379 FPS** cao hơn dự đoán nhưng vẫn dưới sàn 3 FPS — **kết luận của dự đoán đúng dù con số thì lệch**, ghi lại để thấy giới hạn của việc suy diễn từ độ trễ thay vì đo.

### 5.6.5. Chịu tải, bộ nhớ và độ tin cậy (NFR-SC1, NFR-P4…P7, NFR-R4)

<!-- {{T5.6e}} chiu tai, bo nho, do tin cay — gop vao T5.7 -->

**Mọi chỉ tiêu hiệu năng *ngoài đường xử lý ảnh* đều đạt với biên rất rộng** (chi tiết ở Bảng 5.10): nạp mô hình **6,41 s**, khởi động tới khi `/health` sẵn sàng **8,36 s** (sàn 30 s); overhead API p95 **19,01 ms**; truy vấn lịch sử 10.000 bản ghi p95 **18,71 ms** — nhanh hơn mục tiêu **~27 lần**; RSS pipeline / máy chủ backend **0,759 / 0,806 GB** so với sàn 4 GB, tức phẳng ở khoảng **0,8 GB**; **10 yêu cầu đồng thời** ổn định so với ngưỡng 5; soak 15 phút **100,0% thành công trên 2.028 yêu cầu**, RSS chỉ tăng **+0,094 GB** (0,726 → 0,820) — **không rò rỉ**; cơ sở dữ liệu sống sót qua khởi động lại với **0/9.031 bản ghi mất**. Hình đường cong thông lượng và tỉ lệ lỗi theo mức đồng thời 1 / 2 / 5 / 10 (`07-concurrency.png`) **đã có nhưng cần vẽ lại**.

**Nhưng hai chỉ tiêu trên chính đường xử lý ảnh thì không:** NFR-P1 chỉ đạt sàn và **NFR-P2 trượt cả sàn**, cùng nguyên nhân là đuôi độ trễ do bậc thang thử-lại. **Kiến trúc phần mềm không còn là vấn đề** — tầng API, tầng dữ liệu, bộ nhớ, độ ổn định đều dư biên; **nhưng *độ trễ suy luận* thì vẫn là vấn đề**. Hai nhánh đi tiếp: nâng *độ chính xác* OCR biển hai dòng (5.5), và cắt *đuôi độ trễ* — đặt trần thời gian cho bậc thang, hoặc chỉ chạy nó ở chế độ ảnh tĩnh.

### 5.6.6. Bỏ bước phát hiện chữ của PaddleOCR: một quyết định suýt sai

Mục 4.5.3 để ngỏ một câu hỏi: chế độ **chỉ nhận dạng** cho model fine-tune thêm **12,46 điểm** A6 và rẻ hơn **~290 ms** mỗi ảnh — vì sao không bật? Vì ngữ liệu chứng minh nó **không có thẩm quyền trả lời câu hỏi đó**.

<!-- {{T5.6f}} bo buoc phat hien chu: hai ngu lieu, hai ket luan nguoc nhau -->

**Bảng 5.9.** Bỏ bước phát hiện chữ — ba ngữ liệu, hai kết luận ngược nhau

| Cấu hình | A6 trên 2.801 ảnh **cắt sẵn** | Bộ demo **ảnh toàn cảnh** | Tầng dễ *(n=372)* | Tầng khó *(n=236)* | **A7 hiện trường** | KTC 95% |
|---|---:|---:|---:|---:|---:|:---:|
| Model gốc, det + rec — *bản giao hàng* | 0,7512 | **17 / 22** | 96,8% | 44,1% | **56,3%** | [52,0 ; 60,7] |
| Model gốc, chỉ rec | 0,7508 | 13 / 22 | 96,8% | 19,9% | 37,8% | [34,3 ; 41,3] |
| Model fine-tune, det + rec | 0,6762 | 14 / 22 | 96,8% | 30,9% | 46,3% | [42,2 ; 50,3] |
| Model fine-tune, chỉ rec | **0,8758** | 15 / 22 | **94,1%** | 44,5% | 56,0% | [51,7 ; 60,4] |

> Nguồn: `29-reconly-ablation.json`, `31-demo-ab-reconly.json`, [34-scene-level-a7.md](../reports/34-scene-level-a7.md).

**Cột trái và các cột phải cho hai thứ tự ngược nhau, và các cột phải mới là cột đúng.** Mọi ảnh trong ngữ liệu 2.801 mẫu là bản xuất Roboflow **đã cắt khít quanh biển** — bộ dò chữ đặt vào đó thì không còn gì để khoanh. Nhưng vùng cắt mà hệ thống thật sự phải đọc do **YOLO sinh ra từ ảnh toàn cảnh** và lỏng hơn nhiều (dính cản xe, kính chắn gió, nền đường); bỏ bước phát hiện thì bộ nhận dạng đọc luôn phần nền thành ký tự — `TCA7A22104`, `5KB274184` trên `nhieu-bien-2.png`. **Một khác biệt nữa, nghiêm trọng hơn:** chế độ chỉ-nhận-dạng **không có khả năng trả về chuỗi rỗng** — trên **1.606 khung** biển do bộ phát hiện sinh ra nó trả chuỗi ở **cả 1.606**, trong khi bản giao hàng trả rỗng ở **173 khung**; khi bộ phát hiện bắt nhầm một tấm biển quảng cáo, bản giao hàng **im lặng** còn chế độ chỉ-rec **bịa ra một biển số**, và với hệ thống ghi vào cơ sở dữ liệu thì bịa nguy hiểm hơn im lặng. **Quyết định: giữ bước phát hiện chữ.** Công tắc `ALPR_OCR_SKIP_DETECTION` được cài đặt, mặc định **tắt**, ghim bằng kiểm thử; không xoá vì hiệu ứng "chỉ-rec giúp model fine-tune, hại model gốc" là thật — chỉ là 22 biển thì quá ít để đổi cấu hình đem giao.

**Điều kiện để xét lại là một tập ảnh toàn cảnh có nhãn chuỗi — lỗ hổng đó đã được lấp ngày 02/08/2026:** **608 khung biển** trên ảnh hiện trường được gán nhãn chuỗi. Bắt buộc lấy mẫu **phân tầng** vì **1.232/1.606** khung thuộc nhóm bất đồng — dùng riêng nhóm đó sẽ cho con số bi quan sai lệch; tầng đồng thuận được **đếm hết** (**372/374**). **Phải phát biểu cho đúng mức:** bản giao hàng đứng đầu, nhưng chênh với ứng viên gần nhất chỉ **0,3 điểm** và hai khoảng tin cậy **chồng gần như hoàn toàn** — về thống kê hai cấu hình đó **không phân biệt được** trên tập này, nên kết luận đúng không phải *"bản giao hàng chính xác hơn"* mà là **"không có bằng chứng để đổi"**; hai cấu hình còn lại thua rõ, nằm ngoài khoảng tin cậy. Cột "tầng dễ" hé lộ điều mà ngữ liệu ảnh cắt sẵn không thấy được: fine-tune + chỉ rec là cấu hình **duy nhất kém đi ở ca dễ** — 94,1% so với 96,8%, tức **10 biển đọc hỏng thêm** trên 372 khung đã đếm hết; nó thắng ở ca khó nhưng đánh mất ca dễ, và đó là lý do lợi thế 12,46 điểm không sống sót ở đường chạy thật.

> **Ghi lại vì đây là lần thứ tư cùng một họ lỗi, và là lần đầu chặn được trước khi vào bản giao.** Ba lần trước — siêu phân giải, công cụ đo bỏ sót bậc thang thử-lại, val acc của lượt fine-tune — đều là lỗi đã mắc rồi mới phát hiện. Lần này phép đo nói "lãi 12,46 điểm" và chỉ vì bộ demo được chạy lại **trước** khi đổi mặc định mới lộ ra rằng nó làm hệ thống **tệ đi 4 biển**. Quy tắc rút ra: *không đổi cấu hình mặc định dựa trên một phép đo mà đầu vào của nó khác đầu vào thật.*

---

## 5.7. Đối chiếu toàn bộ chỉ tiêu phi chức năng

Bảng tổng hợp trình bày khi bảo vệ, liệt kê **đầy đủ mọi mã NFR** đã đặt ra ở Phase 0, không lọc bỏ mã nào — kể cả những mã không đạt.

<!-- {{T5.7}} doi chieu toan bo chi tieu NFR -->

**Bảng 5.10.** Đối chiếu toàn bộ chỉ tiêu phi chức năng

| Mã | Chỉ tiêu | Sàn | Mục tiêu | **Đo được** | KQ | Mục |
|:---:|---|---:|---:|---:|:---:|:---:|
| P1 | Độ trễ E2E một ảnh, p95 | ≤ 1500 ms | ≤ 800 ms | **1.143,10 ms** *(p50 405,77 ms)* | 🟡 | 5.6.1 |
| P2 | FPS webcam (tầng API) | ≥ 3 | ≥ 5 | **2,379** *(144 khung xong / 1.815 chào / 1.671 bỏ trong 60,52 s, 0 lỗi; p50 180,05 ms, p95 1.247,70 ms)* | ❌ | 5.6.4 |
| P3 | Tốc độ xử lý video | ≥ 0,15× | ≥ 0,3× | **0,746×** *(0,546 s/khung; video 14,25 s xong trong 19,1 s, sàn ≤ 95 s / mục tiêu ≤ 47,5 s; `vid_stride` 5)* | ✅ | 5.6.4 |
| P4 / P4b | Nạp mô hình / khởi động tới `/health` | ≤ 30 s | ≤ 15 s | **6,41 s** / **8,36 s** *(baseline)* | ✅ | 5.6.5 |
| P5 | Overhead API, p95 | ≤ 100 ms | ≤ 50 ms | **19,01 ms** *(baseline)* | ✅ | 5.6.5 |
| P6 | Truy vấn lịch sử 10.000 bản ghi, p95 | ≤ 1000 ms | ≤ 500 ms | **18,71 ms** *(baseline)* | ✅ | 5.6.5 |
| P7a / P7b | RSS pipeline / RSS backend | ≤ 4 GB | ≤ 2 GB | **0,759 / 0,806 GB** *(sau soak 0,726 → 0,820, +0,094 GB)* | ✅ | 5.6.5 |
| A1 | mAP@0.5 của bộ phát hiện | ≥ 0,85 | ≥ 0,90 | **0,9829** | ✅ | 5.4.1 |
| A2 | mAP@0.5:0.95 của bộ phát hiện | ≥ 0,55 | ≥ 0,65 | **0,7834** | ✅ | 5.4.1 |
| A3 | Precision / Recall phát hiện | ≥ 0,88 / 0,85 | ≥ 0,92 / 0,90 | **0,9837 / 0,9714** *(F1 0,9775; 1.514 ảnh / 1.611 đối tượng)* | ✅ | 5.4.1 |
| A4 | Độ chính xác OCR mức ký tự (1 − CER) | ≥ 0,92 | ≥ 0,95 | **0,9454** | 🟡 | 5.5.1 |
| A5 | Chuỗi đầy đủ **trước** hậu xử lý | ≥ 0,80 | ≥ 0,85 | **0,6373** | ❌ | 5.5.2 |
| A6 | Chuỗi đầy đủ **sau** hậu xử lý | ≥ 0,85 | ≥ 0,90 | **0,7512** | ❌ | 5.5.2 |
| **A6 − A5** | **Đóng góp của khối hậu xử lý** | — | — | **+11,39 điểm** *(319 sửa đúng / 0 làm hỏng)* | ✅ | **5.5.2** |
| A7 | Độ chính xác E2E toàn trình | ≥ 0,82 | ≥ 0,88 | **0,5552** *(ảnh crop)*; **0,563** *(ảnh toàn cảnh; KTC 95% [0,520 ; 0,607])* | ❌ | 5.5.5 |
| A8 | Tách theo layout một dòng / hai dòng | báo cáo tách bạch | — | phát hiện **2,09 điểm**; OCR (A6) **25,45 điểm** | 🟡 | 5.4.3, 5.5.3 |
| A9 | Tách theo điều kiện ảnh | báo cáo nếu có nhãn | — | — *(bộ dữ liệu không có nhãn điều kiện chụp)* | ⬜ | 5.7 |
| R4 | Tỉ lệ thành công khi chạy liên tục | ≥ 99% | ≥ 99% | **100,0%** *(2.028 yêu cầu, soak 15 phút)* | ✅ | 5.6.5 |
| R5 | CSDL sống sót qua khởi động lại | 100% | 100% | **0/9.031 bản ghi mất** | ✅ | 5.6.5 |
| SC1 | Số yêu cầu đồng thời xử lý ổn định | ≥ 5 | ≥ 5 | **10** | ✅ | 5.6.5 |
| M2 | Độ bao phủ test tầng nghiệp vụ | ≥ 70% | ≥ 70% | **87,7%** *(2026-07-20)* | ✅ | 5.7 |
| M6 | Tuân thủ lint và định dạng tự động | sạch | sạch | **black 96/96 sạch; ruff còn 83 `E501`** | ⚠️ | 5.7 |
| C2 | Hoạt động không cần GPU | mặc định | — | **có** | ✅ | 5.2.3 |
| R1–R3, SC2–SC3 | Không sập với đầu vào hỏng / độc hại · ảnh không có biển ⇒ HTTP 200 + danh sách rỗng · tác vụ video lỗi không để lại rác · ≥ 100.000 bản ghi không suy giảm hiệu năng · tác vụ video chạy nền | — | — | — | ⬜ | 5.7 |
| M1, M3–M5, S1–S6, C1, C3–C4, U1–U5 | Tách mã AI khỏi mã API · type hint + docstring · không hard-code đường dẫn · thay được bộ OCR không sửa mã API · sáu chỉ tiêu bảo mật (magic bytes, path traversal, HTTP 413, CORS không dùng `*`, không log dữ liệu nhạy cảm, ORM tham số hoá) · ba chỉ tiêu tương thích (Windows / Linux / macOS qua `docker compose up`, Chrome / Edge / Firefox, cài từ đầu ≤ 15 phút) · năm chỉ tiêu khả dụng (≤ 3 click, phản hồi trực quan > 500 ms, lỗi tiếng Việt, dùng được từ 1366×768, tương phản WCAG AA ≥ 4,5:1) | — | — | — | ⬜ | 5.7 |

**Ghi chú về NFR-A9.** Chỉ tiêu phát biểu **có điều kiện** từ Phase 0: *"báo cáo độ chính xác theo điều kiện ảnh (ban ngày / ban đêm / nghiêng / mờ), **nếu bộ dữ liệu có nhãn phù hợp**"*. Bộ v3 **không có nhãn điều kiện chụp thống nhất**, nên **không** gán nhãn bằng suy đoán (ví dụ dùng độ sáng trung bình để suy ra "ban đêm") vì nhãn suy đoán tạo ra bảng kết quả trông chặt chẽ nhưng đo một đại lượng không xác định; trạng thái đúng để báo cáo là **NFR-A9 không đánh giá được vì thiếu nhãn**. Phương án nếu có thời gian: gán nhãn thủ công cho tập con **khoảng 200–300 ảnh** và **công bố rõ đó là tập con gán nhãn thủ công**.

**Kết quả kiểm thử phần mềm.** Nhóm NFR-M, S, C, U kiểm chứng bằng bộ kiểm thử tự động: **1.001 test thu thập, 1.000 pass, 1 xfail, 0 fail, 0 skip** (chạy `pytest -q` tại gốc kho ngày 2026-08-02); độ bao phủ **tầng nghiệp vụ 87,7%** — mốc 2026-07-20 trong `13-refactor-result.json` (**2.931 câu lệnh / 317 bỏ sót**, số test khi ấy **882/881**) — so với chỉ tiêu ≥ 70% của NFR-M2, ✅ đạt; cặp **862/861** trong các bản tài liệu trước là lần chạy cũ hơn và đã bị thay thế. Bao phủ tầng nghiệp vụ đo ở Phase 7 trước đó là **88,1%**, bao phủ **toàn kho mã** ở Phase 7 là **42,0%** (`07-testing-report.md`) — cả hai đều là số đo thật ở hai thời điểm khác nhau, giữ nguyên kèm mốc thời gian thay vì chọn một con số rồi xoá con số kia. Chênh lệch 88,1% ↔ 42,0% là **có chủ ý**: NFR-M2 đặt ngưỡng cho **tầng nghiệp vụ** — nơi chứa logic có thể sai âm thầm (luật hậu xử lý, xác thực đầu vào, thao tác cơ sở dữ liệu) — còn 42,0% toàn kho gồm cả script tiện ích, mã sinh biểu đồ, mã tải bộ dữ liệu, những phần chi phí viết test cao mà rủi ro sai thầm lặng thấp; công bố riêng 88,1% mà không nói mẫu số là một dạng chọn lọc số liệu có lợi. Test `xfail` duy nhất phải được nêu tên khi công bố — nó đánh dấu một hành vi đã biết là chưa đúng, không phải test bị vô hiệu hoá để bảng kết quả sạch: `tests/integration/test_api_detection.py::TestErrorBodies::test_a_failed_image_detection_records_the_failed_job`, trong đó `DetectionService._fail_job` gọi `db.rollback()` trước khi ghi bản ghi thất bại còn `_create_job` mới chỉ `flush`, nên dòng job bị huỷ và một lần tải ảnh thất bại hiện **không để lại dòng nào** trong bảng `DetectionJob`.

---

## 5.8. Phân tích lỗi

Sáu loại lỗi **đầy đủ và loại trừ lẫn nhau**, mỗi ca sai gán đúng một loại theo thứ tự ưu tiên: **E1 bỏ sót biển** (ảnh có biển nhưng không hộp nào khớp), **E2 phát hiện nhầm** (hộp ở vùng không phải biển), **E3 nhầm ký tự** (đúng độ dài, sai ký tự), **E4 thiếu ký tự**, **E5 thừa ký tự**, **E6 sai thứ tự** (đủ ký tự nhưng sắp sai, hầu như chỉ ở biển hai dòng do ghép nhầm chiều). E6 đáng chú ý riêng vì nó **chỉ tồn tại do bài toán có biển hai dòng** và là loại lỗi hậu xử lý sửa được triệt để nếu logic ghép dòng đúng.

<!-- {{T5.8}} tan suat cac loai loi -->

**Bảng 5.11.** Tần suất từng loại lỗi

| Mã | Loại lỗi | Số ca | Tỉ lệ trong tổng ca sai | Tỉ lệ toàn tập đánh giá | Một dòng | Hai dòng |
|:---:|---|---:|---:|---:|---:|---:|
| E1 | Bỏ sót biển | 335 | — | — | — | — |
| E2 | Phát hiện nhầm | *(chưa đo)* | — | — | — | — |
| E3 | Nhầm ký tự | 445 | 63,85% | 15,89% | 17 | 428 |
| E4 | Thiếu ký tự | 73 | 10,47% | 2,61% | 0 | 73 |
| E5 | Thừa ký tự | 18 | 2,58% | 0,64% | 5 | 13 |
| E6 | Sai thứ tự | 0 | 0,00% | 0,00% | 0 | 0 |
| | **Tổng số ca sai** | **697** | 100% | 24,88% | — | — |
| | **Tổng ca đánh giá (mẫu số)** | **2.801** | n/a | 100% | — | — |

> **Mẫu số của E1 khác mẫu số của E3–E6.** E1 lấy từ lượt đo E2E ở 5.5.5 trên 2.801 mẫu; tỉ lệ E1 trên mẫu số riêng của nó là **11,96%**, nên hai cột tỉ lệ **cố ý để trống ở dòng E1**. E2 để *(chưa đo)*. **Hai loại lỗi ngoài khung E1–E6:** `empty_read` = **10** (OCR trả chuỗi rỗng) và `mixed` = **151** (một biển vừa thiếu vừa thừa vừa nhầm ký tự) — có trong cài đặt nhưng không có mã E riêng; ghi nhận để tránh ảo giác "các mã E cộng lại đủ 100% số ca sai" (E3+E4+E5+E6 = **536**, phần còn lại tới 697 là 151 ca `mixed` và 10 ca `empty_read`). **Nguồn:** khoá `by_line_count.*.error_classes` của `05-results.json` — cùng lượt 28/07 với 5.5, tức **đã có** cả bước cứu dòng trên lẫn bậc thang thử-lại.

**So với lượt 20/07, phân bố lỗi đã đổi hình rõ rệt** — tổng ca sai **916 → 697**, giảm **219** ca. Giảm mạnh nhất là `mixed` (277 → 151) và E5 (95 → 18), tức các chuỗi **hỏng về cấu trúc** đã xử lý phần lớn; ngược lại E3 **tăng** (399 → 445) — hiện tượng **phân loại lại** chứ không phải thoái lui, vì một biển trước cho chuỗi sai độ dài (rơi vào `mixed` hoặc E4) nay cho chuỗi đúng độ dài nhưng sai một ký tự. **Cấu trúc lỗi xác nhận chẩn đoán ở 4.7.1:** gần như toàn bộ lỗi ký tự dồn về biển hai dòng (E3 428/445, E4 **73/73 — tuyệt đối, không một ca nào thuộc biển một dòng**, E5 13/18), biển một dòng chỉ sinh **22 ca** trên cả ba loại; khớp với chênh lệch 25,45 điểm A6 ở 5.5.3. E6 = **0** trên toàn tập: logic ghép hai dòng hoạt động đúng, không ca nào ghép nhầm chiều.

**Bước cứu dòng trên để lại dấu vết đo được ngay trong bảng này.** So với lượt đo trước khi có bước cứu, **E4 giảm mạnh nhất: 217 → 134 ca**, trong khi E3 tăng 376 → 399 và `mixed` tăng 266 → 277: bước cứu nhắm đúng chế độ "mất hẳn dòng trên" nên rút bớt quần thể E4, còn những ca cứu được một phần **chuyển sang** E3 hoặc `mixed` thay vì biến mất — kiểm chứng chéo độc lập, vì nếu bước cứu chỉ "làm số đẹp lên" thì phân bố sẽ co lại đồng đều chứ không dịch chuyển có hướng. Dù vậy, E4 (**73 ca**) và $D$ = **1.272** ký tự bị xoá vẫn cùng trỏ về chế độ thất bại còn lại: OCR đọc **hụt** ký tự trên biển hai dòng.

Bốn hình minh hoạ ca điển hình **chưa sinh**: E1 biển bị bỏ sót kèm kích thước box tương đối và điều kiện ảnh (`05-error-e1-missed.png`); E3 nhầm ký tự với vùng cắt, chuỗi thô, chuỗi sau hậu xử lý và nhãn thật (`05-error-e3-substitution.png`); E6 sai thứ tự trên biển hai dòng (`05-error-e6-order.png`); và ca mà **hậu xử lý làm hỏng** một chuỗi vốn đã đúng — nếu tồn tại ca như vậy, **bắt buộc phải trưng ra**, vì nó là bằng chứng phản biện đối với đóng góp công bố ở 5.5.2; một chương đánh giá chỉ trưng ra các ca hệ thống làm tốt là một chương đã tự loại bỏ khả năng bị kiểm chứng.

---

## 5.9. Bàn luận

### 5.9.1. Những gì đạt được

Bốn kết quả, mọi con số đã dẫn ở mục tương ứng: **bộ phát hiện đạt toàn bộ chỉ tiêu với biên rộng** (5.4.1), điểm yếu duy nhất được phơi bày chứ không giấu là dải "rất nhỏ" (5.4.4); **khối hậu xử lý đóng góp thuần dương, không rủi ro** — câu trả lời định lượng cho RQ3, dồn gần trọn vào biển hai dòng, hai bậc cứu chữa cô lập được bằng đo A/B với **0 ca hồi quy** (5.5.2); **biển một dòng về cơ bản đã giải xong** nên "OCR không đạt" là một phát hiện **có định vị**, không phải thất bại mơ hồ (5.5.3); **hiệu năng và kiến trúc phần mềm đều trong ngưỡng**, mức vượt mục tiêu của NFR-P1 là **cái giá đã định lượng** của bậc thang thử-lại (5.6.1, 5.6.5).

**Bản thân tính trung thực của quy trình đánh giá là một kết quả:** 5.3.3 (lập luận vòng tròn trong kiểm chứng rò rỉ), 5.6.1 (bác bỏ con số 5.857 ms bị nhiễm tải), 3.6.1 (ba biến cùng đổi) và 5.5.6 (phát hiện **ba lần** đường đo chạy một pipeline ngắn hơn pipeline sản phẩm — lần đầu nhờ dấu hiệu "chỉ số bao hàm đứng yên", lần thứ ba nhờ mức chênh đúng bằng 0,0000 trên bốn chữ số thập phân). Lần thứ ba đáng ghi vì nó chứng minh biện pháp phòng ngừa sau lần thứ hai **đã được tuân thủ đầy đủ mà vẫn thất bại**, do nhắm sai nguyên nhân gốc.

### 5.9.2. Những gì KHÔNG đạt được, và vì sao

Hai chỉ tiêu **chuyển trạng thái** sau lượt đo lại 28/07: **NFR-A4 từ ❌ sang 🟡** (0,8848 → **0,9454**, vượt sàn 0,92); **NFR-P1 từ ✅ sang 🟡** (731 ms → **1.143 ms**, vẫn dưới sàn 1.500 ms nhưng vượt mục tiêu 800 ms) — **thoái lui có chủ ý**, cái giá của bậc thang thử-lại đổi lấy 34 biển. **Ba chỉ tiêu OCR còn lại không đạt, nguyên nhân chung là biển hai dòng:** A5 = **0,6373** thiếu **16,27 điểm** so với sàn 0,80; A6 = **0,7512** thiếu **9,88 điểm** so với 0,85; A7 = **0,5552** thiếu **26,48 điểm** so với 0,82.

> Ba con số trên là kết quả **sau** khi đã áp cả hai bậc cứu chữa và các bản sửa đọc biển hai dòng. So với lượt 20/07, A6 tăng **7,82 điểm** — mức cải thiện lớn nhất của cả đồ án ở tầng nhận dạng, đạt được **không tốn một giây GPU nào**. Nhưng **không chỉ tiêu nào trong ba chỉ tiêu này chuyển sang đạt** — một cải thiện đo được, không phải một lời giải.

Nguyên nhân **định lượng và có định vị**: toàn bộ khoảng thiếu nằm ở biển **hai dòng** vốn chiếm **79,8%** tập có nhãn chuỗi (5.5.3) — **đặc tính có cấu trúc của bài toán**: khoảng cách **25,45 điểm** A6 cùng bậc độ lớn với mốc **48,6 điểm** mà Laroca và cộng sự đo trên bộ dữ liệu **RodoSol-ALPR của Brazil** (5.5.3), chứ không phải lỗi cài đặt sửa nhanh được. Phần lỗi còn lại đã dịch từ "đọc hỏng cả chuỗi" sang **"đọc hụt ký tự"** (5.5.1), mà hậu xử lý theo luật **về nguyên tắc không thể phục hồi một ký tự chưa từng được đọc ra**, nên hướng khắc phục bắt buộc nằm ở **tầng nhận dạng** — không ở hậu xử lý, cũng không ở hình học (đã đo tách bạch ở 5.5.7). **Cảnh báo hiệu lực về A7:** 0,5552 bị hạ thêm bởi giới hạn giao thức đo (ảnh crop ngoài phân bố huấn luyện) nên phải đọc như **cận dưới bi quan** (5.5.5).

**Sáu hạng mục chưa đo và trạng thái khắc phục.** *NFR-A9* — **không có nhãn điều kiện ảnh**; khắc phục **một phần** bằng gán nhãn thủ công cho tập con. *So sánh backend suy luận* (5.6.3) — **chưa chạy** `benchmark_cpu`; **có** thể làm. *Phân rã đóng góp theo từng nhóm luật* (5.5.2) — **chưa có** cơ chế bật/tắt luật trong `plate_rules.py`; **có** thể làm, cần viết mã. *Thí nghiệm cô lập biến E1–E3* (mục 3.6.2) — chi phí ≈ **33 giờ CPU**, vượt ngân sách; **không** làm được trong khuôn khổ đồ án. *Benchmark engine OCR* hứa ở mục 3.3 — ✅ **đã chạy 03/08/2026** (mục 3.3.3): PaddleOCR **68,87%** so với EasyOCR **14,28%** và Tesseract **10,28%** trên 2.801 biển, cùng tầng bao quanh, nên quyết định giữ PaddleOCR nay **có căn cứ độ chính xác**. *So sánh YOLO26n làm đối chứng* hứa ở mục 2.7 — **chưa huấn luyện** vì ngân sách CPU dồn hết cho lượt `best.pt`; **có** thể làm. Phân biệt "chưa đo vì chưa tới lượt" với "không đo được vì thiếu điều kiện" (NFR-A9 thiếu nhãn, A7 thiếu tập hiện trường có nhãn chuỗi) là quan trọng: chỉ nhóm thứ hai mới là hạn chế thật của công trình.

### 5.9.3. Các mối đe doạ đến tính hợp lệ của kết quả

Nguyên tắc: **nêu mối đe doạ, đánh giá mức nghiêm trọng, nói rõ đã làm gì để giảm thiểu — kể cả khi biện pháp giảm thiểu là "không có".**

**(1) Rò rỉ dữ liệu tồn dư không khử được bằng băm tri giác.** *Cao.* Bảng 5.1 cho thấy rò rỉ tồn dư **có thật, đo được**: ngoài vùng bảo vệ của ngưỡng gộp, tại Hamming **12** vẫn còn **791 cặp** và tại 15 là **3.529 cặp**; nghiêm trọng hơn, hai ảnh của **cùng một chiếc xe** ở góc khác nhau vẫn mang cùng biển số nhưng Hamming lớn — rò rỉ **ngữ nghĩa** mà không ngưỡng phash nào phát hiện được. *Đã áp dụng:* nâng ngưỡng gộp 5 → 10, đo ở nhiều ngưỡng cao hơn ngưỡng gộp. *Chưa áp dụng được:* chia split theo nhóm biển số, bất khả thi vì thiếu nhãn chuỗi cho phần lớn corpus. **Hệ quả: mọi chỉ số ở 5.4 và 5.6 phải coi là cận trên lạc quan.**

**(2) Tập test không xuyên bộ dữ liệu.** *Cao.* Train và test đều lấy từ **cùng sáu nguồn nguyên tố**, nên chỉ đo được tổng quát hoá *trong phân bố*, **không** đo được *xuyên phân bố* — thứ quyết định khi triển khai trên camera mới, địa điểm mới, chiếu sáng mới; tài liệu đã chỉ ra độ chính xác ALPR **sụt giảm đáng kể** khi đánh giá xuyên bộ dữ liệu [7]<!-- laroca_2022_crossdataset -->. *Giảm thiểu:* không có — cách đúng là giữ lại một nguồn hoàn toàn không dùng để huấn luyện làm tập test xuyên bộ; **chưa thực hiện**.

**(3) Mẫu số nhỏ cho các chỉ số OCR.** *Cao.* Phần lớn corpus 15.133 ảnh **chỉ có nhãn hộp giới hạn, không có nhãn chuỗi ký tự**, nên A4…A7 đo trên tập con **2.801 biển**; với mẫu số nhỏ, chênh lệch vài điểm phần trăm có thể nằm trong dao động ngẫu nhiên. *Giảm thiểu:* công bố mẫu số ở mọi bảng của 5.5, **không** rút kết luận về chênh lệch nhỏ.

**(4) Đo trên một cấu hình phần cứng duy nhất.** *Trung bình.* Mọi số hiệu năng đo trên một máy Intel Raptor Lake 14 nhân chạy Windows 11 và **không ngoại suy** sang CPU khác kiến trúc, sang Linux, hay máy khác số nhân — đặc biệt vì ONNX Runtime và OpenVINO đều nhạy với cấu hình luồng và tập lệnh vector [117]<!-- onnxruntime_2025_threading --> [120]<!-- openvino_2024_performancehints -->. *Giảm thiểu:* công bố cấu hình đầy đủ ở 5.2 và nhắc lại ở đầu 5.6.

**(5) Một lượt huấn luyện duy nhất, không ước lượng được phương sai.** *Trung bình.* Với `seed=42` cố định và ngân sách khoảng 12 giờ CPU cho một lượt, mọi chỉ số là kết quả của **một lần chạy**. *Giảm thiểu:* cố định seed để đảm bảo tái lập; không phát biểu so sánh nào dựa trên chênh lệch nhỏ hơn dao động giữa các seed dự kiến.

**(6) Bộ dữ liệu không đạt tiêu chí Q6 về tỉ lệ đối tượng nhỏ.** *Trung bình.* **10,91%** số hộp có diện tích dưới 0,5% diện tích ảnh, vượt ngưỡng 10%. *Giảm thiểu:* báo cáo mAP **tách theo dải kích thước** ở 5.4.4.

**(7) Nhãn layout suy ra từ tỉ lệ khung hình khi bộ dữ liệu không khai báo.** *Thấp đến trung bình.* Ngưỡng 2,5 có cơ sở từ QCVN 08:2024/BCA nhưng vẫn là heuristic; biển chụp nghiêng mạnh có thể bị phân loại nhầm. *Giảm thiểu:* ưu tiên nhãn lớp tường minh khi có, ghi rõ ở chú thích Bảng 5.2 tỉ lệ ô nào suy bằng heuristic.

**(8) Ma trận nhầm lẫn ký tự phụ thuộc thuật toán căn chỉnh chuỗi.** *Thấp.* Khi hai chuỗi khác độ dài, việc gán cặp "ký tự thật ↔ ký tự đọc được" phụ thuộc cách căn chỉnh Levenshtein xử lý các đường đi tối ưu đồng hạng, nên với chuỗi nhiều lỗi chèn/xoá, ma trận có thể ghi nhận cặp không phản ánh nhầm lẫn thị giác thật. *Giảm thiểu:* áp ngưỡng tần suất tối thiểu trước khi đưa một cặp vào bảng luật (tiêu chí 1 ở 5.5.4).

---

## 5.10. Đối chiếu với các công trình đã công bố

Ba khác biệt khiến việc đặt cạnh nhau hai con số độ chính xác của hai công trình là **không hợp lệ về phương pháp**, trừ khi cả ba đều trùng. **Bộ dữ liệu và quốc gia:** biển Trung Quốc chủ yếu một dòng, biển Brazil có bố cục và phông chữ riêng, biển Việt Nam có tỷ lệ biển hai dòng cao. **Định nghĩa chỉ số:** *"accuracy"* trong các bài được khảo sát khi thì là mức ký tự, khi là mức chuỗi, khi là toàn trình tính cả bước phát hiện. **Điều kiện ảnh:** camera tĩnh ở trạm thu phí khác hẳn ảnh chụp tự do. Bằng chứng mạnh nhất đến từ chính lĩnh vực: Laroca và cộng sự (2022) chạy **12 mô hình OCR trên 9 tập dữ liệu công khai**, độ chính xác trung bình **sụt từ 82,4% xuống 45,2%** khi đánh giá xuyên tập dữ liệu.

> ⚠️ **Hệ quả bắt buộc cho toàn mục này.** Mọi con số của công trình khác đều **kèm tên bộ dữ liệu và quốc gia ngay trong bảng**, và không con số nào được dùng để kết luận rằng hệ thống của đồ án tốt hơn hay kém hơn. Chúng chỉ trả lời một câu hỏi hẹp hơn nhiều: *kết quả của đồ án có nằm trong vùng giá trị mà lĩnh vực đã ghi nhận hay không.*

<!-- {{T5.10}} doi chieu ket qua voi cac cong trinh da cong bo -->

**Bảng 5.12.** Đối chiếu với các công trình đã công bố — mọi dòng kèm bộ dữ liệu và quốc gia

| Khối | Công trình | Bộ dữ liệu · quốc gia | Chỉ số công bố | Giá trị |
|---|---|---|---|---:|
| Phát hiện | Batra và cộng sự (2022) | Google Open Images + biển Ấn Độ, 5.991 ảnh | mAP@0.5 | 87,2% |
| Phát hiện | Ba nghiên cứu dùng YOLO11 cho ALPR (mục 3.2) | các tập khác nhau | mAP@0.5 | 90,6% – 99,5% |
| Phát hiện | **Đồ án này** | **corpus Việt Nam hợp nhất, 1.514 ảnh test** | mAP@0.5 | **98,29%** |
| Nhận dạng | Xu và cộng sự — RPnet (2018) | CCPD · Trung Quốc | accuracy end-to-end | 98,5% |
| Nhận dạng | Laroca và cộng sự (2021) | 8 tập từ 5 khu vực | recognition rate trung bình | 96,9% |
| Nhận dạng | Xu và cộng sự — LPTR-AFLNet (2025) | biển Trung Quốc | accuracy **riêng biển hai dòng** | 99,37% |
| Nhận dạng | Tran và Bui (2024) | biển Việt Nam, chạy trên Raspberry Pi 4 | accuracy | 95,68% |
| Nhận dạng | **Đồ án này** | **2.801 biển Việt Nam có nhãn chuỗi** | **A6 / A7** | **75,12% / 55,52%** |

Khối phát hiện so sánh được nhiều nhất vì mAP@0.5 có định nghĩa thống nhất; kết quả của đồ án nằm trong vùng đã công bố — điều này **không** chứng minh mô hình tốt hơn hay kém hơn công trình nào, mỗi dòng đo trên một tập khác nhau, nhưng xác nhận khối phát hiện không có bất thường. Điều kiện phải nêu kèm: tập test của đồ án **không xuyên bộ dữ liệu**, nên **98,29%** **lạc quan hơn** mức đạt được khi gặp nguồn ảnh hoàn toàn mới (mục 5.3.3).

**Ở khối nhận dạng, khoảng cách là thật và không được lấy khác biệt bộ dữ liệu ra biện minh cho toàn bộ nó.** Nhưng chẩn đoán ở 5.5.3 định vị nó rất rõ: phần thiếu hụt nằm gần như trọn ở biển hai dòng — loại biển chiếm tỷ lệ lớn ở Việt Nam nhưng tỷ lệ nhỏ trong các bộ dữ liệu Trung Quốc mà phần lớn công trình ở bảng trên dùng. Hai dòng đáng đọc kỹ nhất là **LPTR-AFLNet (99,37% riêng biển hai dòng)** và **Tran–Bui (95,68% trên biển Việt Nam)**: cả hai cho thấy vùng giá trị này **đạt được**, tức khoảng cách của đồ án không phải giới hạn của bài toán mà là giới hạn của lựa chọn kỹ thuật — đồ án dùng engine OCR **đa ngữ tổng quát chưa tinh chỉnh**, hai công trình kia dùng mô hình huấn luyện riêng cho biển số. Đây là hướng phát triển ưu tiên cao nhất ở mục 5.4.1, và mục 4.5.3 đã đo thử một bước theo hướng đó.

**Bốn điều đồ án báo cáo mà khảo sát (mục 2.7.4) không tìm thấy tương đương**, đều thuộc cách **báo cáo** kết quả: *tách riêng độ chính xác biển một dòng và hai dòng trên cùng hệ thống* (Bảng 5.5); *báo cáo độ chính xác toàn trình mức chuỗi bên cạnh mAP khâu phát hiện* — **98,29%** và **55,52%**, mà **con số thứ hai kém hơn hẳn con số thứ nhất**, chính là lý do khoảng trống này tồn tại vì báo cáo toàn trình thì phải công bố cả phần hỏng; *công bố số hiệu năng kèm phần cứng* (5.2); và *đóng góp thuần của khối hậu xử lý theo luật* (5.5.2).

---

## 5.11. Kết luận chương

**Trả lời trực tiếp sáu câu hỏi nghiên cứu.** *RQ1:* bộ phát hiện YOLO11n đạt **toàn bộ** chỉ tiêu, vượt mục tiêu (5.4.1). *RQ2:* có, chênh lệch giữa hai layout **có ý nghĩa và rất lớn** — **25,45 điểm** A6 — nhưng nằm ở tầng OCR (Bảng 5.5) chứ không ở tầng phát hiện (2,09 điểm, Bảng 5.2). *RQ3:* khối hậu xử lý đóng góp **+11,39 điểm**, sửa đúng **319** biển, làm hỏng **0** (Bảng 5.4), dồn gần trọn vào biển hai dòng (**+13,97 điểm**) nhưng không đủ tới ngưỡng; việc định vị đóng góp về từng nhóm luật **chưa đo được** và là hạng mục cần viết mã. *RQ4:* NFR-P1 **chỉ đạt ngưỡng tối thiểu** (🟡) với p95 = **1.143,10 ms** — thoái lui có chủ ý đổi lấy 34 biển đọc thêm; cùng nguyên nhân đó làm **NFR-P2 trượt cả sàn** (**2,379 FPS**, sàn 3); nút thắt thời gian vẫn là OCR (**64,3%**) và detector (**34,0%**), không phải 93,3% / 6,7% như báo cáo cũ, nên tối ưu detector giờ có ý nghĩa thật. *RQ5:* bảng luật hiện hành **phần lớn không khớp** cặp nhầm thật — chỉ **2/10** cặp nhầm nhiều nhất được phủ (Bảng 5.6). *RQ6:* các mối đe doạ liệt kê và đánh giá ở 5.9.3, ba mối nghiêm trọng nhất ở mức "cao". Kết luận hiệu năng đã **đảo hai lần** — con số cũ 5.857 ms bị bác bỏ, rồi bậc thang thử-lại đảo ngược lần nữa (5.6.1): **kiến trúc phần mềm không còn là vấn đề; nhưng độ trễ suy luận thì vẫn là vấn đề**, bên cạnh độ chính xác OCR trên biển hai dòng.

**Các giới hạn nghiêm trọng nhất** (5.9.3): (i) rò rỉ tồn dư không khử được — ở Hamming 12 vẫn còn **791 cặp** gần trùng train↔test, rò rỉ ngữ nghĩa thì không đo được; (ii) tập test **không xuyên bộ dữ liệu**; (iii) mẫu số nhỏ cho chỉ số OCR (**2.801** biển có nhãn chuỗi trên 15.133 ảnh); (iv) chưa có tập vùng cắt nhỏ do chính bộ phát hiện sinh ra kèm nhãn chuỗi nên bậc siêu phân giải **chưa đo được** lợi ích. Hệ quả: **mọi chỉ số độ chính xác trong chương nên được đọc như cận trên lạc quan**; riêng A7 = 0,5552 thì ngược lại — **cận dưới bi quan** do giao thức đo trên ảnh crop.

**Chuyển tiếp sang Chương 6.** Chương này xác định bằng số liệu — không bằng phỏng đoán — ba nhóm hướng phát triển: (i) **tối ưu hoặc thay thế khối OCR** cho biển hai dòng, từ 5.5.3 và breakdown 5.6.2; (ii) **hiệu chỉnh bảng luật sửa lỗi theo ma trận nhầm lẫn đo được** (8/10 cặp nhầm nhiều nhất chưa có luật phủ), từ 5.5.4, với ràng buộc phải kiểm chứng trên tập giữ riêng để tránh khớp luật trên chính tập đánh giá; (iii) **xây dựng tập test xuyên bộ dữ liệu, chia split theo nhóm biển số, và gán nhãn chuỗi cho một phân bố hiện trường** để đo NFR-A7 và NFR-A9 đúng cách, từ 5.3.3, 5.5.5 và 5.11.3.
