# CHƯƠNG 3. KHẢO SÁT CÔNG NGHỆ VÀ LỰA CHỌN MÔ HÌNH

## 3.1. Phương pháp khảo sát và tiêu chí lựa chọn

Mỗi lựa chọn trình bày theo cùng một khuôn: phương án đã xét, tiêu chí, kết luận, **đánh đổi phải chấp nhận**. Khi bằng chứng không đủ phân định, mục này nói rõ là không đủ.

### 3.1.1. Bốn ràng buộc chi phối mọi lựa chọn

Bốn ràng buộc sau thu hẹp không gian phương án **trước khi** so sánh — vì sao một số ứng viên mạnh bị loại sớm.

| # | Ràng buộc | Hệ quả trực tiếp lên việc chọn |
|:--:|---|---|
| 1 | **Suy luận trên CPU, không có GPU CUDA** (CON-02, mục 4.3.1) | Phương án không công bố tốc độ CPU đều **không có căn cứ để đánh giá**; mô hình hàng trăm triệu tham số loại từ đầu |
| 2 | **Biển số Việt Nam có biển hai dòng** | Engine giả định văn bản một dòng gãy ở đây; tiêu chí phân loại, không phải điểm cộng |
| 3 | **Phải đóng gói và bàn giao được** | Giấy phép, dung lượng mô hình, số phụ thuộc là tiêu chí thật |
| 4 | **Ngân sách thời gian CPU hữu hạn** | Một số phép so sánh đã thiết kế nhưng **không chạy được**; mục 3.1.2 nói rõ là những phép nào |

### 3.1.2. Ranh giới giữa cái đã đo và cái mới chỉ khảo sát tài liệu

Không phải mọi lựa chọn đều qua thực nghiệm: có phép đồ án tự chạy trên chính máy và dữ liệu của mình, có phép chỉ dựa số liệu nhà phát hành, và có phép **chưa bao giờ chạy được**.

**Bảng 3.1.** Mức bằng chứng của từng phép so sánh trong chương

| Phép so sánh | Mức bằng chứng | Trình bày ở |
|---|---|:---:|
| PP-OCRv5_mobile ↔ PP-OCRv6_medium | ✅ **Tự đo** — 200 vùng cắt biển số, cùng máy, cùng thứ tự ảnh | 3.3.2 |
| Bộ nhận dạng gốc ↔ bản tinh chỉnh | ✅ **Tự đo** — 2.801 biển có nhãn chuỗi, bốn cấu hình | 5.4 |
| YOLO11n ↔ YOLOv8n và năm thế hệ YOLO khác | 📄 **Khảo sát tài liệu** — theo benchmark chính thức của nhà phát hành, đồ án **không tự chạy lại** | 3.2 |
| PaddleOCR ↔ EasyOCR ↔ Tesseract | ✅ **Tự đo 03/08/2026** — 2.801 biển có nhãn chuỗi, ba nhánh, cùng tầng bao quanh | 3.3.3 |
| PyTorch ↔ ONNX Runtime ↔ OpenVINO | ❌ **Chưa đo** — chọn theo benchmark bên thứ ba, chưa có số tự đo | 3.4 · 5.6.3 |
| Độ phân giải 416 ↔ 640 | 🟡 **Có số đo nhưng không quy kết được** — ba biến đổi đồng thời và ngược chiều nhau | 3.6 |

Dòng ❌ còn lại là khoản nợ thực sự, ghi nhận ở mục 6.3:

- **So sánh runtime chưa chạy** ⇒ chọn ONNX Runtime đứng vững nhờ **lý do vận hành** (một runtime duy nhất cho cả hai mô hình, tránh xung đột hai framework học sâu), không nhờ số liệu tốc độ tự đo.

## 3.2. Mô hình phát hiện: YOLO11

**Các phương án đã xét.** Bảy thế hệ YOLO từ YOLOv8 trở về sau — mốc chuyển sang anchor-free, có ý nghĩa trực tiếp với bài toán biển số (mục 2.3.1): YOLOv8 [49], YOLOv9 [53], YOLOv10 [46], YOLO11 [16], YOLOv12 [54], YOLOv13 [55], YOLO26 [47]. Họ two-stage (Faster R-CNN, Mask R-CNN) loại từ đầu vì chi phí tính toán không hợp ràng buộc CPU.

## 3.3. Engine nhận dạng ký tự

Đây là lựa chọn trình bày **trung thực nhất về mức độ chắc chắn**: chọn *họ engine* theo khảo sát tài liệu (3.3.1), rồi chọn *bậc mô hình* theo phép đo tự chạy (3.3.2).

### 3.3.1. PaddleOCR, EasyOCR, Tesseract — khảo sát tài liệu

**Các phương án đã xét:** tám engine — PaddleOCR, EasyOCR, Tesseract, TrOCR, docTR, MMOCR, fast-plate-ocr và RapidOCR/OnnxTR.

### 3.3.2. PP-OCRv5 mobile so với PP-OCRv6 — đo trên máy đồ án

Mục này chọn **bậc mô hình** bên trong họ đã chọn, dựa trên số liệu **tự đo**.

**Bảng 3.2.** PP-OCRv6_medium_rec so với PP-OCRv5_mobile_rec, đo trên 200 vùng cắt biển số của đồ án

| Mô hình | Đúng chuỗi | Trung vị | p95 |
|---|---:|---:|---:|
| **PP-OCRv5_mobile_rec** — *đang dùng* | 134/200 = **67,0%** | **23,0 ms** | 31,9 ms |
| PP-OCRv6_medium_rec | 145/200 = **72,5%** | 386,9 ms | 429,0 ms |


> **Ghi chú: đây là phép chiếu, không phải phép đo.** Cộng 364 ms vào p95 hiện hành cho khoảng **1.507 ms**, tức **vượt sàn 1.500 ms** và đẩy NFR-P1 từ 🟡 xuống ❌. Con số này suy ra từ độ trễ nhánh nhận dạng đo cô lập, **chưa chạy lại toàn đường ống** — muốn công bố phải đo thật. Nhưng ngay cả với sai số rộng, hướng của kết luận không đổi: NFR-P2 vốn đã trượt sàn thì chắc chắn trượt sâu hơn.

> **Lưu ý bắt buộc khi trích bài PP-OCRv6.** Cặp *"+5,1 / +4,6 điểm"* mà bài v6 công bố được tính trên **baseline của chính nó** (v5_server 78,1% / 81,6%), không phải trên baseline trong tài liệu PaddleX (86,38% / 83,8%). Ghép hai nguồn sẽ **đảo chiều kết luận**. Trích thì phải trích kèm baseline gốc.

### 3.3.3. Benchmark ba engine trên 2.801 biển số Việt Nam — đo 03/08/2026

Mục 3.3.1 kết thúc bằng một khoản nợ: giữ PaddleOCR dựa trên lý do kỹ thuật, **không** dựa trên bằng chứng độ chính xác, trong khi tài liệu công khai nghiêng về EasyOCR. Mục này trả nợ đó.

**a) Vì sao phép đo này khó làm đúng.** Bốn lượt chạy đầu đều cho số vô nghĩa; mỗi lượt hỏng lộ ra một điều kiện bắt buộc — truyền tên model tường minh, tắt backend oneDNN (mục 4.6.3), khôi phục tỷ lệ khung hình, lọc mảnh vụn ở mép dải ghép. Bài học chung: **phần lớn năng lực đọc biển số không nằm trong engine** mà ở tầng bao quanh nó. So sánh ba engine với ba tầng bao quanh khác nhau là đo tầng bao quanh chứ không đo engine.

**b) Thiết kế.** Cả ba engine chạy trong **đúng một tầng bao quanh** — sao đúng chuỗi bước của bộ nhận dạng bản giao hàng — trên **cùng một mảng NumPy đã chuẩn bị xong**; khác biệt duy nhất còn lại là engine. Đây cũng là bằng chứng thực nghiệm cho NFR-M5. Một chỗ cố ý không cào bằng: Tesseract chạy kèm whitelist `A-Z0-9`, vì giới hạn tập ký tự là **năng lực gốc** của nó; cắt bỏ "cho công bằng" mới là làm sai.

*Kiểm chứng harness:* nhánh có-split của PaddleOCR đo được **63,73%**, khớp **chính xác** NFR-A5 = 0,6373 công bố từ trước bằng một đường đo hoàn toàn khác — cùng một số tới bốn chữ số.

**Bảng 3.3.** So sánh ba engine OCR trên 2.801 biển số Việt Nam (567 một dòng, 2.234 hai dòng)

| Engine | Nhánh | Toàn bộ | 1 dòng | 2 dòng | CER | Rỗng | p50 |
|---|---|---:|---:|---:|---:|---:|---:|
| **PaddleOCR** | tắt split | 28,81% | 94,2% | 12,2% | 0,588 | 6 | 295 ms |
| **PaddleOCR** | có split | **63,73%** | 94,2% | 56,0% | 0,094 | 11 | 405 ms |
| **PaddleOCR** | + hậu xử lý | **68,87%** | **94,9%** | **62,3%** | **0,089** | 11 | 402 ms |
| EasyOCR | tắt split | 6,53% | 15,3% | 4,3% | 0,647 | 4 | 84 ms |
| EasyOCR | có split | 10,35% | 15,3% | 9,1% | 0,282 | 1 | 248 ms |
| EasyOCR | + hậu xử lý | 14,28% | 28,6% | 10,7% | 0,269 | 1 | 249 ms |
| Tesseract | tắt split | 9,57% | 47,3% | **0,0%** | 0,777 | 960 | 101 ms |
| Tesseract | có split | 9,60% | 47,3% | **0,0%** | 0,565 | 700 | 108 ms |
| Tesseract | + hậu xử lý | 10,28% | 50,4% | **0,1%** | 0,567 | 700 | 106 ms |

**c) PaddleOCR thắng dứt khoát — và điều này bác bỏ tài liệu công khai.** Ở cấu hình bản giao hàng, PaddleOCR đạt **68,87%**, hơn EasyOCR **54,59 điểm** và hơn Tesseract **58,59 điểm** — khoảng cách quá lớn để quy cho nhiễu. Kết luận *"tài liệu công khai không cho thấy PaddleOCR vượt EasyOCR trên ảnh biển số"* ở mục 3.3.1 **vẫn đúng về tài liệu công khai**, nhưng nay đồ án có số liệu của chính mình trên biển số Việt Nam và nó nói ngược lại. Quyết định giữ PaddleOCR nay **có thêm căn cứ độ chính xác**.

**d) Tách-rồi-ghép-ngang KHÔNG độc lập engine — kết quả bất ngờ nhất.**

| Engine | tắt split → có split | Mức tăng |
|---|---|---:|
| PaddleOCR | 28,81% → 63,73% | **+34,92 điểm** |
| EasyOCR | 6,53% → 10,35% | +3,82 điểm |
| Tesseract | 9,57% → 9,60% | **+0,03 điểm** |

Nếu cả ba cùng tăng mạnh, đóng góp kỹ thuật của đồ án sẽ độc lập với engine — một khẳng định mạnh. **Dữ liệu không cho phép nói thế.** Phát biểu đúng: tách-rồi-ghép-ngang là điều kiện **cần** để đọc biển hai dòng — nó biến bài toán đa dòng thành bài toán một dòng — nhưng **không đủ**; engine phải đủ mạnh để tận dụng dải ảnh đã ghép.

Ngược lại, **bộ luật hậu xử lý giúp cả ba** (+5,14 · +3,93 · +0,68 điểm). Đóng góp (b) của đồ án vì vậy **là** đóng góp độc lập engine, khác với tách-rồi-ghép-ngang.

**e) Tesseract không đọc được biển hai dòng.** **0,0% trên 2.234 biển hai dòng**, kể cả sau khi đã ghép thành một dòng, trong khi đọc được 47,3% biển một dòng. Đã kiểm bằng mắt để loại khả năng lỗi công cụ: nó **có** đọc ra chữ nhưng luôn kèm ký tự rác, và 700/2.801 lần trả chuỗi rỗng. Dự đoán *"Tesseract vỡ khi crop nhiều dòng"* ở mục 3.3.1 được xác nhận, ở mức nghiêm trọng hơn.

> **Hai điều phép đo này không trả lời.** Thứ nhất, nó đo trên **vùng biển đã cắt sẵn**; báo cáo 31 cho thấy thứ tự xếp hạng có thể **đảo ngược** trên ảnh toàn cảnh qua bộ phát hiện thật, nên kết luận chỉ áp cho tầng nhận dạng. Thứ hai, nó **không** kết luận engine nào tốt hơn nói chung — chỉ kết luận engine nào đọc biển số Việt Nam tốt hơn *bên trong tầng bao quanh của đồ án*; một hệ thống thiết kế quanh EasyOCR, với tiền xử lý riêng của nó, có thể cho số khác.

## 3.4. Runtime suy luận trên CPU: ONNX Runtime

**Các phương án đã xét:** chạy trực tiếp tệp trọng số PyTorch, ONNX Runtime, OpenVINO. **Tiêu chí:** tốc độ CPU, mức đa nền tảng, độ nặng phụ thuộc khi đóng gói, khả năng cùng tồn tại với framework khác.

> **Ghi chú về cách trích dẫn.** Chỉ được dùng **phần số liệu tốc độ** của bảng benchmark này. Các con số mAP đi kèm được đo trên tập `coco8` chỉ gồm **8 ảnh**, nên **vô nghĩa về mặt thống kê** và không được trích dẫn dưới bất kỳ hình thức nào.

## 3.5. Các lựa chọn công nghệ nền tảng khác

Phần lớn quyết định còn lại là **ràng buộc của đề bài**; ghi lại kèm lý do và đánh đổi để Chương 4 tham chiếu.

**Bảng 3.4.** Tổng hợp quyết định công nghệ nền tảng

| # | Hạng mục | Lựa chọn (phương án thay thế) | Lý do chính | Đánh đổi phải chấp nhận |
|:--:|---|---|---|---|
| 1 | Web framework backend | **FastAPI** (Django, Flask) | Tự sinh đặc tả OpenAPI — tạo sẵn một sản phẩm bàn giao; có sẵn WebSocket và tác vụ nền | Phải biết khi nào **không** dùng hàm bất đồng bộ; nguy cơ tranh chấp với luồng suy luận |
| 2 | ORM và migration | **SQLAlchemy 2.0 + Alembic** (Tortoise ORM, Peewee) | Tích hợp sâu kiểu tĩnh; lược đồ đã thay đổi nên nhu cầu migration là có thật | Đường cong học dốc nhất trong nhóm |
| 3 | Cơ sở dữ liệu | **SQLite** (PostgreSQL, MySQL) | Ghi có thể xếp hàng vì suy luận CPU mới là nút cổ chai; không thêm dịch vụ khi đóng gói | **Chỉ một tiến trình ghi tại một thời điểm**; vượt ngưỡng tải phải chuyển PostgreSQL |
| 4 | Frontend | **React + TypeScript + Vite + TailwindCSS** (Vue, Angular, Svelte) | Hệ sinh thái lớn nhất; công cụ build tiền nhiệm ngừng bảo trì; kiểu tĩnh nối tiếp từ backend | Tự lắp ghép routing, quản lý trạng thái, thành phần giao diện |
| 5 | Framework học sâu | **PyTorch** (TensorFlow) | Ultralytics khai báo PyTorch là phụ thuộc lõi — chọn YOLO11 là chọn PyTorch | Kéo theo framework học sâu **thứ hai** (PaddlePaddle) do lựa chọn OCR — giải bằng mục 3.4 |
| 6 | Đóng gói | **Docker + Compose** | Yêu cầu tái lập và khởi động bằng một lệnh | Kích thước image là rủi ro do có framework học sâu |

## 3.6. Độ phân giải đầu vào: 640 thay vì 416

Đồ án có sẵn hai mô hình để đối chiếu — baseline-416-v1.pt và best.pt — nhưng **phép so sánh giữa chúng không quy kết được nguyên nhân**: giữa hai lượt huấn luyện có **ba biến thay đổi đồng thời và ngược chiều nhau** (độ phân giải 416 → 640, bộ dữ liệu v1 → v3 đã khử rò rỉ, số epoch), nên chênh lệch chỉ số **không gán được cho riêng biến nào**. Điều này phải nói rõ vì bản nháp trước từng trình bày best.pt như mô hình "tệ hơn baseline", trong khi ở tầng phát hiện nó **vượt mọi ngưỡng NFR** (mục 5.4.1).

Lựa chọn **640** vì vậy đứng trên căn cứ khác: đó là độ phân giải mà chỉ tiêu NFR-A1/A2 đặt ra và là độ phân giải mọi số liệu tốc độ CPU chính thức của Ultralytics được đo. Muốn quy kết nguyên nhân cần một ma trận thí nghiệm cô lập từng biến (E1 – E3), ước tính **≈ 33 giờ CPU** — vượt ngân sách còn lại, ghi nhận là **chưa thực hiện** ở mục 6.3.
