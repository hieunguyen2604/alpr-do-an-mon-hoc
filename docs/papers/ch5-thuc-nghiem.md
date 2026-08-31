# CHƯƠNG 5. THỰC NGHIỆM VÀ ĐÁNH GIÁ

Chương 5 trình bày kết quả đánh giá hệ thống sau khi xây dựng. Chương này tập trung trả lời hai câu hỏi trọng tâm: hệ thống **đáp ứng yêu cầu kỹ thuật ở mức độ nào**, và **độ tin cậy của các số liệu đo lường**; do đó, mọi số liệu đều được trình bày kèm theo ngữ cảnh thực nghiệm cụ thể.

---

## 5.1. Mục tiêu và phương pháp đánh giá

### 5.1.1. Các câu hỏi nghiên cứu mà chương này trả lời

Chương này trả lời sáu câu hỏi từ đặc tả phi chức năng: **RQ1** — YOLO11n có đạt chỉ tiêu phát hiện biển số Việt Nam không (5.4; NFR-A1…A3)? **RQ2** — độ chính xác khác nhau thế nào giữa biển một dòng và hai dòng (NFR-A8; 5.4.2, 5.5.3)? **RQ3** — hậu xử lý đóng góp bao nhiêu vào độ chính xác chuỗi (NFR-A5 ↔ A6; 5.5.2)? **RQ4** — hệ thống có đạt chỉ tiêu độ trễ trên CPU không và điểm nghẽn ở đâu (5.6; NFR-P1…P7)? **RQ5** — bảng luật sửa ký tự có khớp các cặp nhầm lẫn đo được không (5.5.4)? **RQ6** — yếu tố nào đe doạ tính hợp lệ của kết quả (5.9.1)? RQ3 và RQ5 lần lượt lượng hoá đóng góp của hậu xử lý và thay giả định bằng dữ liệu đo được.

### 5.1.2. Hai nguyên tắc trình bày bắt buộc

**Một — mọi số hiệu năng phải kèm cấu hình phần cứng**: đồ án suy luận **hoàn toàn trên CPU** nên so với các con số FPS đo trên GPU là không hợp lệ nếu không ghi rõ; cấu hình ở 5.2 là điều kiện diễn giải cho toàn mục 5.6. **Hai — mọi số độ chính xác phải kèm tên tập dữ liệu và số mẫu**, vì độ chính xác là thuộc tính của **cặp (mô hình, tập đánh giá)**; hệ quả: NFR-A4…A7 chỉ đo được trên tập con có nhãn chuỗi, nhỏ hơn nhiều tập test phát hiện, mẫu số đó không được giấu. **Ký hiệu:** ✅ đạt mục tiêu · 🟡 chỉ đạt ngưỡng tối thiểu · ❌ không đạt · ⬜ chưa đo · ➖ không áp dụng.

> **Ghi chú về cách trích dẫn.** Cặp số **94,3%** (biển một dòng) ↔ **45,7%** (biển hai dòng), chênh **48,6 điểm phần trăm**, đo trên bộ dữ liệu **RodoSol-ALPR của Brazil** [2]<!-- laroca_2022_crossdataset -->. Đây **không phải** số liệu Việt Nam; mỗi lần dẫn, tên bộ dữ liệu và quốc gia phải xuất hiện **ngay trong câu**, và nó chỉ dùng như _analogue định lượng_ về độ khó tương đối của biển hai dòng, không bao giờ như mốc chuẩn phải vượt.

### 5.1.3. Giao thức đo

![](figures/fig-ch6-01.png)

**Hình 5.1.** Giao thức đo và ràng buộc phụ thuộc giữa các bước đánh giá.

**Không bước đo nào chạy trước khi trọng số được đóng băng**; **tập test không được chạm vào trong huấn luyện lẫn chọn epoch** — chọn epoch chỉ dựa vào validation. Ba quy ước: **kích thước lô = 1 khi đo độ trễ** (riêng mAP dùng lô lớn hơn vì không phụ thuộc kích thước lô); **bỏ 3 lượt khởi động nóng**; **báo cáo p50/p95/p99, không báo cáo trung bình**, vì trung bình che đuôi phân bố còn NFR-P1 phát biểu ở p95.

Độ chính xác nhận dạng trải qua **năm lượt hiệu chỉnh**; **mọi con số trong chương này thuộc lượt 5 — cấu hình của bản giao hàng**. Các lượt trước bị thay thế vì ba lý do khác hẳn nhau về tính chất: *(a)* **hệ thống thật sự thay đổi** (lượt 2, 3, 5 — mỗi lần cải tiến một khâu là mọi con số cũ mô tả một hệ thống không còn tồn tại); *(b)* **công cụ đo sai** (lượt 4 — công cụ tự dựng lại các bước xử lý thay vì gọi đúng đường mà hệ thống thật chạy, nên bỏ sót hẳn một bước); *(c)* **điều kiện đo sai** (một lần ở phép đo tốc độ khung hình, 5.6.3). Loại lỗi *(b)* lặp lại **bốn lần** và được ghi thành một mối đe doạ tính hợp lệ ở mục 5.9.1.

<!-- {{T5.1a}} tien trien do chinh xac qua nam luot hieu chinh -->

**Bảng 5.1.** Tiến triển độ chính xác qua năm lượt hiệu chỉnh

| Lượt | Thay đổi chính | A4 | A6 |
| :--: | --- | ---: | ---: |
| 1 | Lượt đo đầu tiên | 0,8734 | 0,6555 |
| 2 | Trả lại tỷ lệ đúng cho ảnh biển; phục hồi dòng trên _(5.5.6)_ | 0,8848 | 0,6730 |
| 3 | Bốn đợt sửa độ chính xác ở khối đọc ký tự | 0,9416 | 0,7437 |
| 4 | Công cụ đo chạy đúng đường xử lý của bản giao hàng _(5.5.7)_ | 0,9454 | 0,7512 |
| **5** | **Bảng sửa ký tự dựng từ ma trận nhầm lẫn đo được** _(5.5.4)_ | **0,9483** | **0,7701** |
| ✗ | _(đối chứng)_ Bộ đọc ký tự đã tinh chỉnh — **kém hơn bản gốc**, đã bác bỏ | 0,9252 | 0,6762 |

Nguyên tắc rút ra và áp dụng từ đó: **một con số chỉ được đưa vào quyển khi công cụ đo đi qua đúng đường xử lý mà bản giao hàng đi**, và mọi tuỳ chọn cấu hình phải đọc từ cùng một nguồn với hệ thống đang chạy thật.

---

## 5.2.---

## 5.2. Môi trường thực nghiệm

Toàn bộ số liệu đo trên **một máy trạm cá nhân duy nhất**: **Windows 11 Pro 10.0.26200**, **Python 3.13.12**, CPU **Intel Raptor Lake** (Family 6, Model 183) — **14 nhân vật lý / 20 nhân logic**, **không có GPU CUDA** nên mọi suy luận và huấn luyện chạy trên CPU; chế độ đo **lô = 1, bỏ 3 lượt khởi động nóng**. Đây là **tiền tố ngầm định của mọi con số hiệu năng ở 5.6**.

Phiên bản thư viện được trích từ môi trường thực thi đúng thời điểm chạy phép đo cuối cùng chứ không lấy từ tệp khai báo phụ thuộc, vì tệp khai báo ghi _ràng buộc phiên bản_ chứ không ghi _phiên bản đã cài đặt_: `ultralytics` 8.4.101 · `torch` 2.13.0+cpu · `torchvision` 0.28.0+cpu · `paddleocr` 3.7.0 (PP-OCRv5 mobile) · `paddlepaddle` 3.3.1 · `onnxruntime` 1.27.0 · `openvino` 2026.2.1 (nền tảng suy luận thay thế, xem 3.4) · `opencv-python` 4.10.0.84 · `numpy` 2.4.5 · `fastapi` 0.139.2 · `uvicorn` 0.51.0 · `sqlalchemy` 2.0.51 · `imagehash` 4.7.2 · `pytest` 9.1.1.

### 5.2.1. Ràng buộc CPU-only: Quyết định thiết kế cốt lõi

Lập luận đầy đủ ở **4.3.1**. NFR-P1 phát biểu _kèm_ ràng buộc CPU, nên kết luận "đạt sàn, không đạt mục tiêu" ở 5.6 là kết luận về hệ thống trong đúng bối cảnh vận hành thật, không phải con số chờ nâng cấp phần cứng. Cấu hình mô hình cũng do ràng buộc phần cứng quyết định — **YOLO11n** (2.590.035 tham số) [9]<!-- jocher_2024_yolo11 --> và **PP-OCRv5 mobile** [10]<!-- cui_2026_ppocrv5 -->. Về quy mô: **30,2 phút mỗi epoch**, một lượt 20 epoch mất **10,05 giờ** liên tục, khiến **tìm kiếm siêu tham số bất khả thi**; chương này báo cáo _một_ cấu hình huấn luyện, không phải kết quả của một quá trình tối ưu — giới hạn thật, ghi ở 5.9.1.

---

## 5.3. Bộ dữ liệu thực nghiệm

> **Lưu ý về cách đặt tên.** Thư mục `yolo_v2/` và `yolo_v3/` chỉ **phiên bản của bộ dữ liệu**, **không** liên quan đến kiến trúc YOLOv2 hay YOLOv3. Mô hình dùng trong toàn đồ án là **YOLO11n**.

<!-- {{T5.3a}} so sanh ba phien ban bo du lieu — DA CO SO, khong can dien -->

<!-- {{T5.3b}} so cap gan trung xuyen split theo nguong Hamming -->

**Bảng 5.2.** Ba phiên bản bộ dữ liệu và số cặp ảnh gần trùng xuyên tập con theo ngưỡng Hamming

| Thuộc tính / ngưỡng                  |                   v1 |         v2 |                                                             **v3** |
| ------------------------------------ | -------------------: | ---------: | -----------------------------------------------------------------: |
| Tổng số ảnh                          |                4.578 |     15.133 |                                                         **15.133** |
| Ngưỡng Hamming gộp trùng lặp         |                    5 |          5 |                                                             **10** |
| Số ảnh train / val / test            |                    — |          — |                                         **10.592 / 3.027 / 1.514** |
| Dùng cho                             | `baseline-416-v1.pt` | bị loại bỏ |                                                      **`best.pt`** |
| Cặp gần trùng xuyên tập con, Hamming 0 |                    — |          — |                                            **0** _(thông tin mới)_ |
| Hamming 5                            |                    — |          — |           **0** _(= ngưỡng gộp v1, v2 — không mang thông tin mới)_ |
| **Hamming 10**                       |              **619** |  **2.699** |               **0** _(= ngưỡng gộp v3 — không mang thông tin mới)_ |
| Hamming 12 · 15                      |                    — |          — |                              **791** · **3.529** _(thông tin mới)_ |
| Hamming 20                           |                    — |          — | **137.506** _(ngưỡng đã lỏng tới mức nhiều cặp là dương tính giả)_ |

**v1 quá nhỏ và chỉ một nguồn** (1 bộ vào hợp nhất, 1 nguồn nguyên tố) — động cơ tải thêm **tám bộ** (tổng **9 bộ**), trong đó **sáu bộ** vào hợp nhất cho bài toán phát hiện cùng bộ gốc (v2, v3: **7 bộ vào hợp nhất, 6 nguồn nguyên tố**), hai bộ nhãn mức ký tự tách riêng cho OCR. **v2 sửa được quy mô nhưng không sửa được rò rỉ:** lên 15.133 ảnh lại _tăng_ cặp gần trùng xuyên tập con lên 2.699 vì các nguồn chứa ảnh có nguồn gốc chung. **v3 giữ nguyên ngữ liệu** (cùng 15.133 ảnh), khác biệt duy nhất là ngưỡng khử trùng lặp 5 → 10 và phép chia tập sinh lại — cô lập biến có chủ ý, cho phép quy kết mọi thay đổi kết quả cho _chất lượng phép chia tập_, không cho _lượng dữ liệu_.

### 5.3.1. Khử trùng lặp: hai tỉ lệ, hai mẫu số khác nhau

Có **hai tỉ lệ khử trùng lặp trên hai mẫu số khác nhau**: **44,2%** (11.978/27.111, trước hợp nhất, trên 7 bộ vào hợp nhất cho bài toán phát hiện) và **47,8%** (7.227/15.133, sau hợp nhất). Hai số **không cộng dồn và không thay thế nhau**; cơ chế và cách đọc trình bày ở mục 4.4.1. Điểm phải nhớ khi trích: mẫu số 27.111 là tổng ảnh của **7 bộ vào hợp nhất cho bài toán phát hiện**, **không phải** 9 bộ đã tải — hai bộ còn lại mang **nhãn mức ký tự**, tách riêng cho tầng OCR.

### 5.3.2. Phân bố nguồn dữ liệu giữa các phép chia tập

Toàn tập chia **15.133 = 10.592 / 3.027 / 1.514**, tức **70,0% / 20,0% / 10,0%**. Hai đặc điểm cần lưu ý khi đọc mọi kết quả của chương. **Thứ nhất, tập test nghiêng về ảnh camera giao thông** — một nguồn ảnh camera giao thông có **20,3%** số ảnh rơi vào test, gấp đôi tỉ lệ tổng thể 10,0% — nên khi đọc mAP theo dải kích thước (5.4.3) phải nhớ rằng đối tượng nhỏ trong tập test tập trung ở một nguồn. **Thứ hai, một bộ dữ liệu dư thừa hoàn toàn:** một bộ vào hợp nhất với 1.005 ảnh và ra khỏi khử trùng lặp chéo bộ với **0 ảnh — loại 100,0%**, bằng chứng định lượng cho việc các bộ Roboflow tái sử dụng ảnh của nhau rất nặng và là lý do **không được cộng dồn số ảnh công bố của từng bộ để suy ra quy mô thật**.

---

## 5.4. Đánh giá bộ phát hiện biển số

Toàn bộ 5.4 đo trên **tập test v3: 1.514 ảnh, 1.611 đối tượng nhãn thật**, `imgsz=640`, `device=cpu`; tập test chưa từng dùng trong huấn luyện hay chọn epoch.

### 5.4.1. Chỉ số tổng thể

<!-- {{T5.4a}} ket qua detection tong the tren tap test v3 (1.514 anh) — chuyen thanh van xuoi, doi chieu nguong o T5.7 -->

> **Một điểm yếu lộ ra khi tách theo kích thước đối tượng.** Bộ dữ liệu có **10,91% số hộp giới hạn chiếm dưới 0,5% diện tích ảnh**, và ở dải đó mAP@0.5 rớt xuống **0,8553** so với 0,9913 ở dải trung bình. Biển ở xa là chỗ bộ phát hiện yếu nhất, và đây là căn cứ cho hướng phát triển siêu phân giải ở mục 6.3.

**Cả bốn chỉ tiêu bắt buộc đều đạt mục tiêu**, đo bằng công cụ đánh giá chuẩn của thư viện: **mAP@0.5 = 0,9829** (NFR-A1; sàn 0,85, mục tiêu 0,90 ✅), **mAP@0.5:0.95 = 0,7834** (NFR-A2; sàn 0,55, mục tiêu 0,65 ✅), **Precision = 0,9837** và **Recall = 0,9714** (NFR-A3; sàn 0,88 / 0,85, mục tiêu 0,92 / 0,90 ✅), **F1 = 0,9775** tại ngưỡng confidence 0,25; đối chiếu ở Bảng 5.11. Ba lưu ý: (1) **bài toán chỉ có một lớp**, mAP một lớp không so trực tiếp được với mAP nhiều lớp trên COCO nên giá trị cao là bình thường, **không phải bằng chứng về độ khó đã vượt qua**; (2) chỉ số quyết định là **mAP@0.5:0.95** vì độ khớp box ảnh hưởng trực tiếp đến chất lượng vùng cắt đưa sang OCR; (3) **chỉ số tổng thể che giấu phân bố**.

### 5.4.2. Tách theo biển một dòng và biển hai dòng (NFR-A8)

Bố cục xác định theo nhãn lớp khi bộ dữ liệu có khai báo, và theo **ngưỡng tỉ lệ khung hình 2,5** khi không có — nằm giữa tỉ lệ chuẩn của biển một dòng (4,727) và biển hai dòng (2,000 / 1,357) theo QCVN 08:2024/BCA.

<!-- {{T5.4b}} detection tach theo layout mot dong / hai dong (NFR-A8) -->

**Bảng 5.3.** Kết quả phát hiện tách theo biển một dòng và hai dòng (NFR-A8)

| Chỉ số                                |        Biển **một dòng** |        Biển **hai dòng** |     Chênh (điểm %) |
| ------------------------------------- | -----------------------: | -----------------------: | -----------------: |
| Số đối tượng nhãn thật _(tổng 1.611)_ |                      286 |                    1.325 |                n/a |
| mAP@0.5                               |                   0,9884 |                   0,9675 |               2,09 |
| mAP@0.5:0.95                          |                   0,7526 |                   0,7649 |              −1,23 |
| Precision · Recall · F1               | 0,9861 · 0,9895 · 0,9878 | 0,9735 · 0,9691 · 0,9713 | 1,26 · 2,04 · 1,65 |

## 5.5. Đánh giá khối OCR và hậu xử lý

> **Ràng buộc mẫu số.** NFR-A4…A7 chỉ đo được trên **tập con có nhãn chuỗi ký tự** — **2.801 biển**, không phải trên 1.514 ảnh test. Thiếu nhãn chuỗi cho phần lớn ngữ liệu là hạn chế thật, ghi ở 5.9.1.

> **Cấu hình khối OCR trong bản giao hàng, nói trước để mọi số dưới đây có nghĩa.** Hệ thống chạy **model gốc PP-OCRv5 mobile**, đủ hai bước *phát hiện chữ* và *nhận dạng* (`ocr_rec_model_dir` để trống). Hai biến thể đã đo và **cả hai đều bị bác bỏ**.
>
> **Một, lượt tinh chỉnh bộ nhận dạng**, đo đủ bốn cấu hình: thắng **+12,46 điểm** ở chế độ chỉ-nhận-dạng nhưng **thua 7,50 điểm** ở đúng chế độ vận hành — mà bản giao hàng chạy chế độ vận hành.
>
> **Hai, bỏ hẳn bước phát hiện chữ**: trên 2.801 mẫu thắng **+12,46 điểm** và rẻ hơn ~290 ms mỗi ảnh, nhưng đo lại trên **ảnh toàn cảnh qua bộ phát hiện thật** thì thứ tự **đảo ngược**, 17/22 xuống 13/22. Cả 2.801 mẫu đều là vùng biển **cắt sẵn**, còn chế độ chỉ-nhận-dạng **không thể trả chuỗi rỗng** (0/1.606 khung, so với 173 của bản đang giao) nên nó **bịa ra biển số** khi bộ phát hiện bắt nhầm. Công tắc `ALPR_OCR_SKIP_DETECTION` giữ trong mã, mặc định tắt. Số liệu đầy đủ ở báo cáo 31 và 30.

### 5.5.1. Độ chính xác mức ký tự (NFR-A4)

Chỉ số là **CER** theo khoảng cách Levenshtein, chuẩn hoá theo độ dài nhãn thật, với $S$ ký tự thay thế, $D$ bị xoá, $I$ chèn thừa, $N$ tổng ký tự nhãn thật; NFR-A4 phát biểu theo **1 − CER**.

### 5.5.2. Chuỗi đầy đủ: trước và sau hậu xử lý (NFR-A5 ↔ NFR-A6)

Khối hậu xử lý theo luật — chuẩn hoá ký tự, áp mặt nạ vị trí chữ số / chữ cái theo định dạng biển số Việt Nam, sửa cặp ký tự đồng hình, kiểm tra mã tỉnh — là **đóng góp kỹ thuật riêng** của đồ án, không có sẵn trong thư viện nào. Câu hỏi _khối đó đóng góp bao nhiêu?_ chỉ trả lời được nếu **đo hai lần trên cùng một tập mẫu**: chuỗi thô PaddleOCR trả về (A5) và chuỗi sau khi áp toàn bộ luật (A6). Đây cũng là lý do kỹ thuật khiến hai cột riêng cho chuỗi thô và chuỗi đã chuẩn hoá cùng tồn tại trong lược đồ cơ sở dữ liệu — **điều kiện cần để phép đo này thực hiện được**, phải có từ giai đoạn thiết kế.

<!-- {{T5.5a}} do chinh xac muc ky tu NFR-A4 -->

<!-- {{T5.5b}} do chinh xac chuoi day du truoc va sau hau xu ly — DONG GOP DINH LUONG CUA KHOI HAU XU LY -->

**Bảng 5.4.** Độ chính xác OCR trước và sau hậu xử lý, trên 2.801 biển có nhãn chuỗi

| Chỉ số                                                     |         Sàn |    Mục tiêu |        **Trước hậu xử lý** |         **Sau hậu xử lý** | Chênh (điểm %) |
| ---------------------------------------------------------- | ----------: | ----------: | -------------------------: | ------------------------: | -------------: |
| 1 − CER (NFR-A4)                                           |        0,92 |        0,95 |                     0,9061 |             **0,9483** 🟡 |            n/a |
| CER                                                        |      ≤ 0,08 |      ≤ 0,05 |                     0,0939 |                    0,0546 |            n/a |
| Chuỗi đầy đủ đúng (A5 → A6)                                | 0,80 → 0,85 | 0,85 → 0,90 |              **0,6373** ❌ |             **0,7701** ❌ |     **+13,28** |
| $N$ / $S$ / $D$ / $I$ trên chuỗi thô                       |           — |           — | 23.855 / 862 / 1.272 / 107 |               (không đổi) |            n/a |
| Biển **sửa đúng** / **bị làm hỏng** / sai cả trước lẫn sau |           — |           — |                          — | **372** / **0** / **644** |            n/a |

### 5.5.3. Tách theo biển một dòng và hai dòng cho OCR

<!-- {{T5.5c}} OCR tach theo layout mot dong / hai dong -->

**Bảng 5.5.** Độ chính xác nhận dạng tách theo biển một dòng và hai dòng

| Chỉ số                              | Biển **một dòng** | Biển **hai dòng** | Chênh (điểm %) |
| ----------------------------------- | ----------------: | ----------------: | -------------: |
| Số mẫu có nhãn chuỗi _(tổng 2.801)_ |           **567** |         **2.234** |            n/a |
| 1 − CER (NFR-A4)                    |            0,9925 |            0,9380 |           5,81 |
| Chuỗi đúng **trước** hậu xử lý (A5) |            0,9418 |            0,5600 |          38,18 |
| Chuỗi đúng **sau** hậu xử lý (A6)   |            0,9541 |            0,7234 |          23,07 |
| Cải thiện do hậu xử lý (A6 − A5)    |             +1,23 |            +16,34 |            n/a |
| Độ chính xác E2E _(giao thức cũ, đã rút — xem 5.5.5)_ |            0,6861 |            0,5219 |              — |

Chênh lệch 2,09 điểm ở tầng phát hiện tăng lên ở tầng OCR: 5,45 điểm ở mức ký tự, **23,07 điểm** ở A6 và **38,18 điểm** ở A5. Biển một dòng đạt A6 = 0,9541, vượt mục tiêu 0,90; kết quả OCR chung chưa đạt chủ yếu do biển hai dòng, chiếm **2.234 / 2.801 = 79,8%** tập có nhãn chuỗi. Sau hai bậc cứu chữa (5.5.6, 5.5.7), khoảng cách A6 giảm từ 36,79 xuống **23,07 điểm**, tức giảm **13,72 điểm**. Phần còn lại thuộc về năng lực nhận dạng ký tự, không phải khâu cắt, ghép hoặc hiệu chỉnh hình học.

### 5.5.4. Ma trận nhầm lẫn ký tự 36×36

Ma trận nhầm lẫn 36 × 36 đầy đủ đặt ở **Phụ lục VIII**. Mười cặp bị nhầm nhiều nhất chiếm **47,1%** tổng lỗi thay thế, dẫn đầu là `L → 1` (90 lần), `E → F` (73) và `4 → L` (53).

**Bảng luật ban đầu suy từ hình dạng ký tự chỉ phủ 2 trong 10 cặp, và một trong
hai suy sai chiều.** Cặp `4 → L` là ví dụ rõ nhất: khi một vị trí bắt buộc là số
mà bộ nhận dạng đọc ra `L`, sự thật là `4` **53 lần** và là `1` **đúng một lần** —
bảng cũ lại sửa `L` thành `1`. Trực giác hình dạng ghép **đúng cặp nhưng sai
chiều**.

Nhóm thực hiện thay bảng bằng bảng trích từ chính ma trận này, với ngưỡng thống
kê: **một mục chỉ được đổi khi ứng viên đo được xuất hiện ít nhất 10 lần và ít
nhất gấp đôi ứng viên đứng nhì**. Lấy argmax thô sẽ cho 23 mục, nhưng phần lớn
dựa trên một đến ba lần xuất hiện — đó là nhiễu, không phải tín hiệu. Qua ngưỡng
chỉ có **hai mục**: `L → 4` và `7 → Z`; năm mục khác được số liệu **xác nhận** là
đã đúng, phần còn lại giữ nguyên phỏng đoán cũ vì bằng chứng quá mỏng.

Hai mục đó nâng số cặp được phủ từ **2 lên 4 trên 10**, và đo lại trên toàn bộ
2.801 biển cho **A6 = 0,7701** so với 0,7512 — thêm **53 biển đọc đúng, làm hỏng
0 biển**, toàn bộ nằm ở biển hai dòng (Bảng 5.1, lượt 5).

**Sáu cặp còn lại không sửa được bằng cơ chế này**, và lý do đáng nói: `E → F`,
`X → Y`, `B → R`, `2 → 7` và `9 → 0` là những cặp mà **cả hai ký tự cùng loại** —
cùng là chữ, hoặc cùng là số. Bộ luật hậu xử lý chỉ can thiệp khi loại ký tự đọc
được mâu thuẫn với loại mà vị trí đó bắt buộc; hai chữ cái nhầm lẫn nhau thì
không vị trí nào phát hiện được. Sửa chúng đòi hỏi mô hình nhận dạng đọc đúng
ngay từ đầu, không phải thêm luật.

### 5.5.5. Độ chính xác đầu cuối toàn trình (NFR-A7)

<!-- {{T5.5e}} do chinh xac E2E toan trinh NFR-A7 — chuyen thanh van xuoi -->

NFR-A7 đo **ảnh đầu vào → phát hiện → cắt → OCR → hậu xử lý → chuỗi cuối**; khác A6 ở chỗ A6 đo trên **vùng biển cắt chuẩn theo nhãn thật** còn A7 đo trên vùng biển do **chính bộ phát hiện** tìm ra, nên A7 tích luỹ cả hai nguồn sai số và theo lý thuyết luôn ≤ A6. Trên 2.801 mẫu, lượt 4 (Bảng 5.1) cho **A7 = 0,5552**; **E2E với điều kiện đã phát hiện được biển = 0,6306**; tỉ lệ biển **bỏ sót** ở tầng phát hiện **0,1196**; phát hiện đúng nhưng **đọc sai chuỗi 0,3694**; chênh **A6 − A7 = 19,60 điểm**.

> **E2 không áp dụng cho ngữ liệu này, và đó là kết luận chứ không phải khoảng trống.** Cả 2.801 mẫu đều là **vùng biển đã cắt sẵn**, nên không có bước phát hiện nào chạy và một ca *phát hiện nhầm* về nguyên tắc không thể xuất hiện. Tỉ lệ phát hiện nhầm thật được đo ở **tầng bộ phát hiện**, trên 1.514 ảnh toàn cảnh của tập kiểm tra: **39 dương tính giả trên 1.606 phát hiện**, tương ứng precision **0,9757** (mục 5.4).

> **Con số 0,5552 bị rút, vì giao thức đo hỏng.** Chạy lại trên **cùng 2.801 mẫu, cùng bộ phát hiện, cùng `imgsz = 640`** cho **A7 = 0,0000** — con số của lượt 4 **không tái lập được**. Đây không phải hệ thống tệ đi mà là **lỗi thiết kế phép đo**: cả 2.801 mẫu đều là **vùng biển đã cắt sẵn**, trong khi bộ phát hiện được huấn luyện trên ảnh giao thông đầy đủ, nên một tấm ảnh mà biển chiếm gần hết khung nằm **ngoài phân bố huấn luyện**. Phần lớn thất bại ở đó do bộ phát hiện không bắt được hộp giới hạn (bỏ sót 11,96%), **không** phải do OCR đọc sai. Trên đầu vào ngoài phân bố, một thay đổi nhỏ ở tầng suy luận đủ để lật hoàn toàn kết quả — dấu hiệu phép đo **không đo cái nó tưởng đang đo** ([báo cáo 41](../reports/41-measured-confusion-tables.md)).

**A7 đo lại ở mức ảnh toàn cảnh.** Phép đo đúng nghĩa đòi ảnh hiện trường **có nhãn chuỗi biển số**, và tập nhãn ấy đã được dựng: **608 khung biển có nhãn** trong tổng **1.606 khung** của **1.514 ảnh** hiện trường thuộc tập kiểm tra. Vì 1.232 khung (76,7%) rơi vào nhóm khó, dùng riêng nhóm ấy sẽ cho con số **bi quan sai lệch**, nên ước lượng được **phân tầng** theo Bảng 5.6: tầng đồng thuận gán nhãn **372/374** — gần như đếm hết chứ không còn là mẫu, nên sai số của ước lượng chỉ còn đến từ tầng bất đồng.

<!-- {{T5.5e2}} NFR-A7 uoc luong phan tang tren anh toan canh -->

**Bảng 5.6.** NFR-A7 ở mức ảnh toàn cảnh — ước lượng phân tầng trên 1.606 khung biển

| Tầng | Kích thước | Đã gán nhãn | Độ chính xác |
| --- | ---: | ---: | ---: |
| Đồng thuận _(ca dễ)_ | 374 | **372** _(99,5%)_ | **96,8%** |
| Bất đồng _(ca khó)_ | 1.232 | 236 _(19,2%)_ | **44,1%** |
| **A7 phân tầng** | **1.606** | **608** _(37,9%)_ | **56,3%** _(KTC 95% [52,0 ; 60,7])_ |

**NFR-A7 = 56,3%, không đạt ❌** — dưới cả ngưỡng tối thiểu 0,82. Kết quả nhất quán với hai quan sát độc lập: đường ống bản giao hàng đọc đúng **17/22 biển** trên bộ ảnh toàn cảnh dùng để trình diễn, gồm cả biển đỏ quân đội, hai biển ngoại giao, biển vàng kinh doanh và hai biển xanh nhà nước; và chênh lệch giữa A6 = 0,7701 (đo trên vùng biển cắt chuẩn) với A7 phản ánh đúng phần sai số mà tầng phát hiện đóng góp thêm.

> **Hạn chế phải nói kèm mỗi lần trích con số này: nhãn do một mô hình ngôn ngữ-thị giác đọc, không phải do người.** Nhãn ấy **độc lập với cả bốn cấu hình được so sánh** nên phép đo không mắc lập luận vòng tròn — nếu lấy đồng thuận của chính các cấu hình làm nhãn thì mọi cấu hình sẽ tự động đúng trên mọi mẫu đồng thuận, kể cả khi tất cả cùng đọc sai. Nhưng một mô hình đọc nhãn vẫn có thể sai theo cách riêng của nó, và điều đó **không kiểm chứng được nếu không có người đọc lại**. Vì vậy 56,3% phải đọc là **ước lượng có nguồn nhãn máy sinh**, không phải con số nhãn vàng. Gán nhãn thủ công cho cùng tập này là **hướng phát triển số 3** ở mục 6.3.

### 5.5.6. Bước "phục hồi dòng trên" cho biển hai dòng — thiết kế, kiểm chứng A/B và kết quả trên toàn tập

<!-- {{T5.5f}} A/B hai chien luoc doc bien hai dong — chuyen thanh van xuoi -->

<!-- {{T5.5g}} A/B buoc cuu dong tren, hai mau doc lap — chuyen thanh van xuoi -->

<!-- {{T5.5h}} truoc/sau buoc cuu dong tren tren toan tap co nhan chuoi — chuyen thanh van xuoi -->

Hồ sơ lỗi thiên về **xoá** ($D$ = 1.272 > $S$ = 862) trên biển hai dòng có cách giải thích tự nhiên: **mất hẳn một dòng**. Hệ thống đọc biển hai dòng bằng **ghép rồi đọc** (*split-then-hstack*): cắt vùng biển thành hai nửa chồng lấn, xếp cạnh nhau thành dải ngang, chạy OCR **một lần**.

Phương án thay thế — đọc riêng từng nửa rồi nối chuỗi — được đo A/B trên 200 biển hai dòng với hạt giống ngẫu nhiên cố định. **Phương án A (ghép rồi đọc một lần, đang dùng) đạt 64,50%; phương án B (đọc từng nửa rồi nối) đạt 3,50%** — kém 61,00 điểm phần trăm và tốn thêm 51,24 ms, thắng ở **0/200** trường hợp. Nguyên nhân đọc được ngay trong dữ liệu: hai nửa **cố ý chồng lấn** để không cắt cụt ký tự, nên đọc riêng thì dải chồng lấn bị đọc **hai lần** và ký tự bị nhân đôi — `84G122593` thành `84-G124E009.01225.93`.

Riêng bước phục hồi dòng trên, đo trên toàn tập 2.801 ảnh có nhãn chuỗi ở lượt 2, đóng góp **+1,75 điểm A6** (0,6555 → 0,6730) và **+2,20 điểm** trên riêng biển hai dòng; nó cho câu trả lời cuối ở **209 biển**, làm hỏng **0**. Các giá trị tuyệt đối của lượt 2 đã bị vượt qua (A6 hiện là 0,7701) nên **không được trích như số hiện hành**.

### 5.5.7. Bậc thang thử lại cho biển nghiêng/méo — chi phí, lợi ích và một quyết định tắt tính năng

Khi lần đọc đầu trả về chuỗi không hợp lệ, hệ thống thử lại trên các biến thể hình học của vùng biển thay vì chấp nhận thất bại. Bậc thang có ba bậc, và **chỉ hai bậc đầu được bật trong bản giao hàng**.

<!-- {{T5.5i}} chi phi va loi ich cua tung bac trong thang thu lai -->

**Bảng 5.7.** Chi phí và lợi ích của từng bậc trong thang thử lại

| Bậc | Chi phí độ trễ | Lợi ích đo được | Trong bản giao hàng |
| --- | ---: | ---: | :--: |
| Nắn hình + giãn dọc | +244 ms p95 | **+34 biển đọc đúng** | ✅ bật |
| Siêu phân giải (FSRCNN) | **+319 ms p95, +1.381 ms p99** | **0 biển** | ❌ tắt |

**Hai bậc đầu** đổi độ trễ đuôi lấy 34 biển đọc thêm, còn **trung vị không tăng** (bậc thang chỉ chạy sau khi lần đọc đầu thất bại, nên toàn bộ chi phí dồn vào đuôi phân bố). **Bậc thứ ba bị tắt mặc định**: một mình siêu phân giải đẩy p95 lên **1.514,26 ms**, vượt cả ngưỡng tối thiểu 1.500 ms, trong khi cứu được **0 biển**; mã và công tắc vẫn giữ nguyên, chỉ đổi giá trị mặc định.

> **Số 0 ấy phải đọc cho đúng.** Cổng vào bậc siêu phân giải chỉ mở cho vùng cắt **nhỏ hơn 200 điểm ảnh**, và **0 trên 120 mẫu ngữ liệu lọt qua cổng đó**. Đây là **số 0 cấu trúc**: chi phí đã đo được, còn lợi ích thì **chưa ai đo được** — khác hẳn *đã đo và thấy vô dụng*. Đo lại bậc này trên ngữ liệu có biển thật sự nhỏ là hướng phát triển ở mục 6.3.

## 5.6. Đánh giá hiệu năng

> Mọi số trong 5.6 phải đọc cùng cấu hình ở 5.2: **Intel Raptor Lake 14 nhân / 20 luồng, Windows 11, CPU-only, kích thước lô = 1**.

### 5.6.1. Độ trễ đầu cuối (NFR-P1)

<!-- {{T5.6a}} do tre dau-cuoi mot anh, doi chieu NFR-P1 -->

**Bảng 5.8.** Độ trễ đầu cuối một ảnh, đối chiếu NFR-P1

| Chỉ số                       |        Sàn |  Mục tiêu | Trước bậc thang | Sau bậc thang | **Cấu hình giao hàng** | Kết quả |
| ---------------------------- | ---------: | --------: | --------------: | ------------: | ---------------------: | :-----: |
| p50 (ms)                     |          — |         — |          414,67 |        405,77 |             **150,07** |   n/a   |
| **p95 (ms)**                 | **≤ 1500** | **≤ 800** |          731,15 |      1.143,10 |             **509,76** | **✅**  |
| p99 (ms)                     |          — |         — |          947,83 |      1.420,07 |           **1.124,13** |   n/a   |
| Trung bình (ms)              |          — |         — |          400,74 |        447,38 |             **222,34** |   n/a   |
| Nhanh nhất (ms)              |          — |         — |               — |             — |              **74,25** |   n/a   |
| Số ảnh đo                    |          — |         — |             100 |           100 |                    100 |   n/a   |
| Bội số so với sàn / mục tiêu |          — |         — |   0,49× / 0,91× | 0,76× / 1,43× |  **0,34× / 0,64×**     |   n/a   |

**NFR-P1 đạt mục tiêu.** p95 = **509,76 ms**, dưới mục tiêu 800 ms với biên **290 ms**, và chỉ bằng **0,34×** ngưỡng tối thiểu. Đây là lần đầu chỉ tiêu này vượt mục tiêu chứ không chỉ đạt sàn.

Cột thứ tư kể phần còn lại của câu chuyện, và nó là một chuỗi hai bước ngược chiều nhau. **Bước lùi:** bậc thang thử lại (5.5.7) đẩy p95 từ 731,15 lên 1.143,10 ms — thoái lui **có chủ ý và đã định lượng**, đổi 412 ms ở đuôi lấy 34 biển đọc đúng thêm; trung vị gần như không đổi vì bậc thang chỉ chạy sau khi đọc hỏng. **Bước tiến:** đợt tối ưu tầng suy luận (4.4) đưa p95 xuống 509,76 ms, tức **thấp hơn cả mốc 731,15 ms trước khi có bậc thang** — hệ thống nay vừa giữ 34 biển ấy vừa nhanh hơn điểm xuất phát.

Ba can thiệp làm nên bước tiến đó đều nằm ở tầng chạy, không đụng trọng số: `torch.inference_mode()` bỏ chi phí ghi sổ đồ thị đạo hàm, ghim số luồng cho torch và OpenCV để tránh tranh khoá, và truyền `cpu_threads` xuống PaddleOCR. **Không chỉ số độ chính xác nào đổi** — A4, A5, A6, mAP và bảng nhầm lẫn giữ nguyên, vì ba can thiệp ấy chỉ đổi cách tính toán được lập lịch chứ không đổi phép tính.

> **Về con số "sub-100 ms".** Ảnh nhanh nhất trong lượt đo đạt **74,25 ms**, và một biển một dòng sạch có thể xuống dưới 100 ms. Nhưng đó là **cận dưới của một mẫu**, không phải chỉ số của hệ thống; số dùng để đối chiếu chỉ tiêu là trung vị 150,07 ms và p95 509,76 ms. Tương tự, **không được lấy 1/độ_trễ làm thông lượng**: nghịch đảo của 81 ms là 12 khung/giây, trong khi thông lượng thật đo qua giao diện lập trình với hàng đợi một khe là **5,63 khung/giây** (5.6.3). Hai đại lượng đo hai thứ khác nhau.g**: tắt hẳn bậc thang thử lại đưa p95 về **866,3 ms**, tức toàn bộ **+277 ms** là của nó; nhưng vì bậc thang chỉ chạy **sau khi lần đọc đầu thất bại** nên nó không chạm vào trường hợp thường — **trung vị thậm chí giảm nhẹ** (414,67 → 405,77 ms), chi phí dồn hết vào đuôi. Với hệ thống mà 95% ảnh xong dưới 1,15 giây và một nửa xong dưới 0,41 giây, p50 mô tả trải nghiệm điển hình còn p95 mô tả trường hợp xấu; NFR-P1 phát biểu theo p95 nên kết luận chính thức là **đạt sàn, không đạt mục tiêu**. Ở lượt đo đầu với cả ba biến thể bật, p95 là **1.514,26 ms** — **vượt cả ngưỡng tối thiểu**; bóc tách chỉ ra bậc siêu phân giải chiếm hơn nửa chi phí đó mà không cải thiện được biển nào đo được nên nó bị **tắt mặc định**, đưa p95 về 1.143,10 ms.

### 5.6.2. Phân rã ngân sách độ trễ theo từng bước

<!-- {{T5.6b}} phan ra ngan sach do tre theo tung buoc, doi chieu uoc luong ban dau -->

**Bảng 5.9.** Phân rã ngân sách độ trễ theo từng bước

| Bước xử lý                        | Ước lượng ban đầu (ms) | **Đo thật (ms)** | Chênh (lần) |    % tổng |
| --------------------------------- | ---------------------: | ---------------: | ----------: | --------: |
| Giải mã ảnh + tiền xử lý          |                     50 |         **1,78** |        0,04 |  **1,2%** |
| Suy luận YOLO11n @ 640px (CPU)    |                    150 |        **55,66** |        0,37 | **38,0%** |
| Cắt + tiền xử lý vùng biển số     |                     30 |         **0,00** |        0,00 |  **0,0%** |
| **PaddleOCR (mỗi biển)**          |                **120** |        **89,16** |        0,74 | **60,8%** |
| Hậu xử lý regex + kiểm tra hợp lệ |                      5 |         **0,03** |        0,01 |  **0,0%** |
| Ghi CSDL + lưu ảnh                |                     50 |                — |           — |         — |
| **Tổng (một biển số)**            |                **405** |       **146,63** |        0,36 |  **100%** |

Ba phát hiện. **Một, ước lượng ở giai đoạn phân tích yêu cầu khá sát ở tổng nhưng lệch ở phân bổ:** tổng suy luận thuần **146,63 ms/biển**, chỉ bằng 0,36 lần ước lượng ban đầu 405 ms. Sai lệch **không** tới một bậc độ lớn. **Hai, điểm nghẽn là PaddleOCR nhưng KHÔNG áp đảo như báo cáo cũ:** 60,8% so với 38,0% của bộ phát hiện, **thay thế** con số cũ "OCR 93,3% / detect 6,5%" vốn đo trên hệ thống đang có lỗi cắt ảnh (~1.322 ms/ảnh); nguyên nhân OCR đắt vẫn đúng — PaddleOCR là **đường ống nhiều giai đoạn** (phát hiện văn bản → phân loại hướng → nhận dạng) thiết kế cho ảnh tài liệu tổng quát, nên hệ thống trả chi phí cho năng lực mà vùng biển đã cắt không cần. **Ba, chiến lược tối ưu đổi hẳn:** theo định luật Amdahl, tăng tốc detector 2–3× có thể kéo E2E xuống quãng **15–23%**, khác hẳn kết luận cũ "chỉ giảm tối đa 6,7%". Dự đoán này **đã được kiểm chứng** bằng phép đo riêng (mục 3.4): OpenVINO nhanh 1,57× ở tầng bộ phát hiện và nâng thông lượng đầu cuối **+20,0%** — nằm trong khoảng dự đoán. Vì NFR-P1 mới đạt sàn, tối ưu hiệu năng vẫn nằm trên đường tới chỉ tiêu chứ không chỉ là _dư địa cải thiện thêm_.

### 5.6.3. Chế độ webcam (tầng API) và xử lý video (NFR-P2, NFR-P3)

<!-- {{T5.6d}} hieu nang che do webcam va xu ly video — gop vao T5.7 -->

**NFR-P2 đạt: 5,63 FPS** (sàn 3, mục tiêu 5) — vượt cả mục tiêu, không chỉ sàn. Con số này đo **sau đợt tối ưu tầng suy luận** (4.4); trước đó là 5,257 FPS. Trong 60,0 giây, camera ảo 30 khung/giây chào **1.801 khung**, hệ thống nhận và trả kết quả cho **338 khung**, bỏ 1.463 khung ở hàng đợi, **0 lỗi**. Giao diện thời gian thực dùng **hàng đợi một khe**: chỉ một yêu cầu bay tại một thời điểm, khung sinh ra trong lúc chờ bị bỏ thay vì xếp hàng; ở kỷ luật đó thông lượng bị chi phối bởi những lần chậm nhất, nên phân vị đuôi mới là đại lượng quyết định. Đo được p50 = **164,08 ms**, p95 = **204,52 ms** — đuôi chỉ rộng gấp 1,25 lần trung vị. NFR-P3 cũng **đạt**: video 14,25 giây xử lý hết **16,4 giây** (sàn ≤ 95 s, mục tiêu ≤ 47,5 s), tức **0,8695×** thời gian thực, `vid_stride = 5` — cũng đo sau đợt tối ưu, trước đó là 0,785×.

Con số này thay thế một lượt đo cũ cho **2,379 FPS (trượt sàn)**. Đo lại trên **mã nguồn giống hệt từng byte**, cùng cấu hình và cùng dãy ảnh phát lại, cho 5,257 rồi 5,213 FPS ở hai lần chạy độc lập; log lượt cũ cho thấy máy khi đó đang cõng ~**560% CPU** của tiến trình khác và harness **đã in cảnh báo** rằng số liệu là *bi quan*. Nguyên nhân chính xác của đuôi hôm đó **không xác định được** và được ghi đúng như vậy; quy tắc rút ra: **một lần đo có cảnh báo tải cạnh tranh không được phép thành số liệu công bố**.

Biên an toàn được kiểm chứng bằng cách ép tải tổng hợp: ở mức xấu nhất — 12 trên 20 luồng bị tiến trình khác chiếm trọn — hệ thống vẫn đạt **4,057 FPS, trên sàn 35%**. Sáu lần đo trong các điều kiện máy khác nhau đặt ở **Phụ lục VIII**; trong đó có một lượt chạy **OpenVINO đạt 6,310 FPS**, nhanh 1,57× ở riêng bước phát hiện và không suy giảm mAP — nhưng **bản giao hàng chạy PyTorch**, vì NFR-P2 đã đạt mà không cần đổi, còn đổi thì mọi con số độ trễ trong chương này sẽ lệch khỏi hệ thống thực sự được bàn giao.

![](figures/fig-ch5-nfr-p2.png)

**Hình 5.3.** Sáu lần đo NFR-P2. Trung vị của lượt đo cũ nằm ngang với các lần đo trên máy rảnh, nhưng đuôi p95 cao gấp sáu lần; ép tải tới 12 lõi cũng chỉ đẩy tỉ lệ p95/p50 lên 1,24× trong khi lượt đo cũ là **6,93×**.

### 5.6.4. Khử trùng lặp mờ cho chuỗi khung hình video

Một xe đi qua khung hình xuất hiện trong hàng chục khung liên tiếp, và khối nhận dạng đọc lại nó ở mỗi khung. Nếu mọi lần đọc đều cho cùng một chuỗi thì gom theo chuỗi là đủ. Thực tế không vậy: **cùng một biển, cùng một chất lượng ảnh, hai khung cách nhau vài phần trăm giây vẫn có thể cho hai chuỗi khác nhau**. Hệ quả trực tiếp là danh sách kết quả của một video ngắn phình ra thành nhiều dòng cho cùng một chiếc xe.

**Cơ chế.** Sau khi gom theo chuỗi, một lượt thứ hai hợp nhất các biến thể của cùng một biển vật lý. Hai chuỗi được coi là cùng một biển khi thoả **đồng thời** hai điều kiện:

1. **Gần nhau về chuỗi** — khoảng cách Levenshtein $\le 2$;
2. **Gần nhau về thời gian** — hai lần đọc cách nhau không quá 48 khung.

Riêng với khoảng cách bằng 2, chỉ điều kiện chuỗi là chưa đủ, vì hai biển **thật sự khác nhau** cũng có thể chỉ cách nhau hai ký tự. Vì vậy mức này còn phải qua một rào ngữ nghĩa: **cùng mã tỉnh hai chữ số**, và **hoặc** cùng chữ cái sê-ri **hoặc** cùng ba chữ số cuối. Bỏ rào ấy đi thì thuật toán sẽ gộp nhầm hai xe khác nhau đỗ cạnh nhau.

**Bản nào sống sót được quyết bằng bằng chứng, không bằng thứ tự đến.** Thứ tự ưu tiên: đúng quy chuẩn định dạng trước, rồi tới **số khung đã bỏ phiếu** cho cách đọc đó, cuối cùng mới tới độ tin cậy OCR. Độ tin cậy một mình là trọng tài kém ở mức một ký tự — một lần đọc sai vẫn có thể mang điểm cao.

**Kết quả đo.** Chạy toàn bộ đường ống trên `demo-video-giao-thong.mp4`, lấy mẫu một khung trong mỗi bốn khung: khối nhận dạng trả về **44 chuỗi khác nhau**, sau khi hợp nhất còn **27** — **17 chuỗi được gom vào một bản ghi khác**, tức gần **bốn trên mười** dòng kết quả là trùng lặp của một biển đã có.

<!-- {{F5.4}} ca khu trung lap mo tren video demo -->

![](figures/fig-ch5-dedup-51H14573.png)

**Hình 5.4.** Một ca khử trùng lặp thật, cắt trực tiếp từ video demo. Cùng một chiếc xe máy được đọc thành **năm chuỗi khác nhau** ở năm khung hình khác nhau; bốn bản viền đỏ bị gom vào bản viền xanh. Điều đáng chú ý là **năm vùng cắt gần như không phân biệt được bằng mắt** — khác biệt không đến từ loá sáng hay che khuất mà từ **tính không tất định của khối nhận dạng giữa các khung gần giống nhau**. Bản `51H14573` thắng nhờ **11 khung** bỏ phiếu, trong khi bốn bản còn lại mỗi bản chỉ có một khung; nếu xét riêng độ tin cậy thì `51H4573` (0,994) đã suýt vượt qua.

**Phạm vi của kết quả này, nói cho đúng.** Đây là cải thiện ở **tầng trình bày kết quả video**, không phải ở độ chính xác nhận dạng: nó không sửa được một ký tự đọc sai, chỉ chọn ra cách đọc được nhiều khung ủng hộ nhất. Vì vậy **các chỉ số NFR-A4…A6 ở mục 5.5 không đổi** — chúng đo trên ngữ liệu ảnh cắt sẵn, mỗi biển một lần, nên bước hợp nhất này không tham gia. Rủi ro còn lại cũng phải nêu: rào ngữ nghĩa thu hẹp chứ **không loại trừ** khả năng gộp nhầm hai biển thật sự khác nhau khi chúng cùng tỉnh, cùng ba số cuối và cùng xuất hiện trong một cửa sổ 48 khung. Trên bộ demo chưa gặp ca nào như vậy, nhưng đó là **chưa quan sát thấy**, không phải **đã chứng minh không xảy ra**.

### 5.6.5. Chịu tải, bộ nhớ và độ tin cậy (NFR-SC1, NFR-P4…P7, NFR-R4)

<!-- {{T5.6e}} chiu tai, bo nho, do tin cay — gop vao T5.7 -->

**Mọi chỉ tiêu hiệu năng _ngoài đường xử lý ảnh_ đều đạt với biên rất rộng.**

**Bảng 5.10.** Các chỉ tiêu hiệu năng ngoài đường xử lý ảnh

| Chỉ tiêu | Đo được | Ngưỡng | Biên |
|---|---:|---:|---:|
| Nạp mô hình | **6,41 s** | ≤ 30 s | 4,7× |
| Khởi động tới khi `/health` sẵn sàng | **8,36 s** | ≤ 30 s | 3,6× |
| Overhead tầng API (p95) | **19,01 ms** | ≤ 100 ms | 5,3× |
| Truy vấn lịch sử 10.000 bản ghi (p95) | **18,71 ms** | ≤ 500 ms | **~27×** |
| Bộ nhớ thường trú — đường ống · máy chủ | **0,759 · 0,806 GB** | ≤ 4 GB | ~5× |
| Yêu cầu đồng thời ổn định | **10** | ≥ 5 | 2× |
| Chạy liên tục 15 phút | **100,0% / 5.337 yêu cầu**, 0 lỗi | ≥ 99% | — |
| Khởi động lại cơ sở dữ liệu | **0/7.977 bản ghi mất** | 0 mất | — |

Hai dòng cuối là bằng chứng **không rò rỉ bộ nhớ** và **không mất dữ liệu**; đối chiếu đầy đủ từng mã chỉ tiêu ở Bảng 5.11.

**Trên chính đường xử lý ảnh, cả ba chỉ tiêu độ trễ nay đều đạt mục tiêu:** p95 một ảnh **509,76 ms** (mục tiêu 800), NFR-P2 **5,63 khung/giây** (mục tiêu 5) và NFR-P3 **0,8695×** thời gian thực (mục tiêu 0,3×). Bậc thang thử lại vẫn là một thoái lui có chủ ý đổi lấy 34 biển đọc thêm (5.5.7), nhưng đợt tối ưu tầng suy luận (4.4) đã bù lại và còn dư. **Kiến trúc phần mềm không còn là vấn đề** — tầng API, tầng dữ liệu, bộ nhớ, độ ổn định đều dư biên. Hai nhánh đi tiếp: nâng _độ chính xác_ OCR biển hai dòng (5.5), và cắt _đuôi độ trễ_ của chế độ ảnh tĩnh — đặt trần thời gian cho bậc thang, hoặc chuyển bộ phát hiện sang OpenVINO, hướng đã đo được **1,57×** ở mục 3.4.

## 5.7. Đối chiếu toàn bộ chỉ tiêu phi chức năng

> **NFR-A9 mang ký hiệu ⬜, khác hẳn ❌.** Chỉ tiêu này đòi báo cáo độ chính xác tách theo điều kiện ảnh (ban ngày, ban đêm, ngược sáng, mưa). Bộ dữ liệu **không có nhãn điều kiện chụp**, nên không phải hệ thống trượt mà là **thiếu điều kiện quan sát** — ⬜ nghĩa là chưa đo được, ❌ nghĩa là đã đo và trượt; ghi nhầm loại này thành loại kia là vu cho hệ thống một thất bại chưa từng đo.

Bảng tổng hợp trình bày khi bảo vệ, liệt kê **đầy đủ mọi mã chỉ tiêu phi chức năng** đã đặt ra ở giai đoạn phân tích yêu cầu, không lọc bỏ mã nào — kể cả những mã không đạt.

<!-- {{T5.7}} doi chieu toan bo chi tieu NFR -->

**Bảng 5.11.** Đối chiếu chỉ tiêu phi chức năng, gom theo nhóm

| Nhóm                                                   | Số chỉ tiêu | Kết quả                     | Con số quyết định                                                                                                                                          |
| ------------------------------------------------------ | :---------: | --------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Độ chính xác — phát hiện** (A1, A2, A3)              |      3      | ✅ **đạt cả ba, biên rộng** | mAP@0,5 = **0,9829** (mục tiêu 0,90); Precision · Recall = 0,9837 · 0,9714                                                                                 |
| **Độ chính xác — nhận dạng chuỗi** (A4 – A7)           |      4      | 🟡 **một**, ❌ **ba**             | A4 = **0,9483** (vượt sàn 0,92, dưới mục tiêu 0,95); A5 · A6 = **0,6373 · 0,7701**, cả hai dưới sàn; **A7 ❌ 0,563** ở mức ảnh toàn cảnh (xem 5.5.5)                                           |
| **Đóng góp hậu xử lý** (A6 − A5)                       |      1      | ✅                          | **+13,28 điểm** — 372 sửa đúng, **0 làm hỏng**, trên 2.801 biển                                                                                            |
| **Báo cáo tách bạch** (A8, A9)                         |      2      | 🟡 A8, ⬜ A9                | Chênh lệch bố cục: **2,09 điểm** ở phát hiện so với **23,07 điểm** ở nhận dạng. A9 không đo được — bộ dữ liệu **không có nhãn điều kiện chụp**             |
| **Hiệu năng — độ trễ** (P1, P2, P3)                    |      3      | ✅ **đạt cả ba**            | p95 một ảnh **509,76 ms** (sàn 1.500, mục tiêu 800; p50 chỉ 150,07 ms). FPS thời gian thực **5,63** — vượt cả mục tiêu 5; xấu nhất đo được dưới tải nặng **4,057**, vẫn trên sàn 3. Video **0,8695×** — vượt mục tiêu 0,3× |
| **Hiệu năng — tài nguyên** (P4 – P7)                   |      5      | ✅ **đạt cả năm**           | Nạp mô hình **6,41 s**; overhead API **19,01 ms**; truy vấn 10.000 bản ghi **18,71 ms**; RSS **0,806 GB**                                                  |
| **Độ tin cậy và chịu tải** (R1 – R5, SC1 – SC3)        |      8      | ✅ **đạt cả tám**           | **100,0%** thành công qua 5.337 yêu cầu soak 15 phút; **0/7.977** bản ghi mất sau khởi động lại; **10** yêu cầu đồng thời ổn định                          |
| **Bảo trì, bảo mật, khả dụng, ràng buộc** (M, S, U, C) |     14      | ✅ **đạt cả mười bốn**      | Bao phủ kiểm thử tầng nghiệp vụ **87,7%** (sàn 70%); chạy không cần GPU; M6 đã sạch — `ruff check` trả về **0 cảnh báo** trên toàn kho                     |

## 5.8. Phân tích lỗi

**Bảng 5.12.** Tần suất từng loại lỗi

| Mã  | Loại lỗi                      |       Số ca | Tỉ lệ trong tổng ca sai | Tỉ lệ toàn tập đánh giá | Một dòng | Hai dòng |
| :-: | ----------------------------- | ----------: | ----------------------: | ----------------------: | -------: | -------: |
| E1  | Bỏ sót biển                   |         335 |                       — |                       — |        — |        — |
| E2  | Phát hiện nhầm                |          ➖ |                       — |                       — |        — |        — |
| E3  | Nhầm ký tự                    |         445 |                  63,85% |                  15,89% |       17 |      428 |
| E4  | Thiếu ký tự                   |          73 |                  10,47% |                   2,61% |        0 |       73 |
| E5  | Thừa ký tự                    |          18 |                   2,58% |                   0,64% |        5 |       13 |
| E6  | Sai thứ tự                    |           0 |                   0,00% |                   0,00% |        0 |        0 |
|     | **Tổng số ca sai**            |     **697** |                    100% |                  24,88% |        — |        — |
|     | **Tổng ca đánh giá (mẫu số)** |   **2.801** |                     n/a |                    100% |        — |        — |

## 5.9. Bàn luận

### 5.9.1. Các mối đe doạ đến tính hợp lệ của kết quả

Nguyên tắc: **nêu mối đe doạ, đánh giá mức nghiêm trọng, nói rõ đã làm gì để giảm thiểu — kể cả khi biện pháp giảm thiểu là "không có".**

**Bảng 5.13.** Tám mối đe doạ đến tính hợp lệ của kết quả

|  #  | Mối đe doạ                                                               |    Mức     | Biện pháp giảm thiểu đã áp dụng                                                                                                                                                                                                                   |
| :-: | ------------------------------------------------------------------------ | :--------: | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
|  1  | **Rò rỉ dữ liệu tồn dư không khử được bằng băm tri giác**                |    Cao     | Nâng ngưỡng gộp 5 → 10 và đo ở nhiều ngưỡng cao hơn ngưỡng gộp. Vẫn còn **791 cặp** ở Hamming 12; rò rỉ _ngữ nghĩa_ (cùng một xe, góc khác) **không ngưỡng phash nào phát hiện được** ⇒ mọi chỉ số ở 5.4 và 5.6 phải coi là **cận trên lạc quan** |
|  2  | **Tập test không xuyên bộ dữ liệu**                                      |    Cao     | **Không có** — cách đúng là giữ lại một nguồn hoàn toàn không dùng để huấn luyện; **chưa thực hiện**                                                                                                                                              |
|  3  | **Mẫu số nhỏ cho các chỉ số OCR** (2.801 / 15.133 ảnh có nhãn chuỗi)     |    Cao     | Công bố mẫu số ở mọi bảng của 5.5; **không** rút kết luận về chênh lệch nhỏ                                                                                                                                                                       |
|  4  | Đo trên **một cấu hình phần cứng duy nhất**                              | Trung bình | Công bố cấu hình đầy đủ ở 5.2; **không ngoại suy** sang CPU, hệ điều hành hay số nhân khác                                                                                                                                                        |
|  5  | **Một lượt huấn luyện duy nhất**, không ước lượng được phương sai        | Trung bình | Cố định `seed = 42` để tái lập; không phát biểu so sánh dựa trên chênh lệch nhỏ                                                                                                                                                                   |
|  6  | Bộ dữ liệu **không đạt tiêu chí Q6** về tỉ lệ đối tượng nhỏ (10,91%)     | Trung bình | Báo cáo mAP **tách theo dải kích thước**: dải dưới 0,5% diện tích rớt về 0,8553 (5.4.1)                                                                                                                                                                                                  |
|  7  | Nhãn bố cục **suy ra từ tỉ lệ khung hình** khi bộ dữ liệu không khai báo | Thấp – TB  | Ưu tiên nhãn lớp tường minh khi có; ghi rõ tỉ lệ ô suy bằng heuristic                                                                                                                                                                             |
|  8  | Ma trận nhầm lẫn ký tự **phụ thuộc thuật toán căn chỉnh chuỗi**          |    Thấp    | Áp ngưỡng tần suất tối thiểu trước khi đưa một cặp vào bảng luật (5.5.4)                                                                                                                                                                          |

