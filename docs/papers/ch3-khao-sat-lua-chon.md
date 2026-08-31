# CHƯƠNG 3. KHẢO SÁT CÔNG NGHỆ VÀ LỰA CHỌN MÔ HÌNH

## 3.1. Phương pháp khảo sát và tiêu chí lựa chọn

> **Một nguyên tắc chi phối toàn chương.** Mọi bảng dưới đây phân biệt rõ hai loại bằng chứng: **số tự đo trên máy thực nghiệm** và **số trích từ tài liệu của người khác**. Loại thứ hai luôn kèm tên bộ dữ liệu và quốc gia, vì một con số đo trên ngữ liệu khác không nói được điều gì chắc chắn về ngữ liệu này. Chỗ nào chưa đo thì ghi thẳng là chưa đo, chứ không mượn số của người khác làm kết luận cho đồ án.

Mỗi lựa chọn trình bày theo cùng một khuôn: phương án đã xét, tiêu chí, kết luận, **đánh đổi phải chấp nhận**. Khi bằng chứng không đủ phân định, mục này nói rõ là không đủ.

### 3.1.1. Bốn ràng buộc chi phối mọi lựa chọn

Bốn ràng buộc thu hẹp không gian phương án **trước khi** so sánh. **(1) Suy luận trên CPU, không có GPU CUDA** (CON-02): phương án không công bố tốc độ CPU không có căn cứ để đánh giá, mô hình hàng trăm triệu tham số loại từ đầu. **(2) Biển số Việt Nam có biển hai dòng**: bộ nhận dạng giả định văn bản một dòng sẽ hỏng — đây là tiêu chí phân loại, không phải điểm cộng. **(3) Phải đóng gói và bàn giao được**: giấy phép, dung lượng mô hình, số phụ thuộc là tiêu chí thật. **(4) Ngân sách thời gian CPU hữu hạn**: một số phép so sánh đã thiết kế nhưng không chạy được, và mỗi bảng ghi thẳng ô nào chưa đo.

## 3.2. Mô hình phát hiện: YOLO11

**Các phương án đã xét.** Các thế hệ YOLO từ YOLOv8 trở về sau — mốc chuyển sang anchor-free, có ý nghĩa trực tiếp với bài toán biển số (mục 2.3.1). Bốn thế hệ có khác biệt kiến trúc đáng kể với bài toán này được đối chiếu ở Bảng 2.1: YOLOv8 [13], YOLOv10 [19]<!-- wang_2024_yolov10paper -->, YOLO11 [9] và YOLO26 [20]<!-- jocher_2025_yolo26 -->. Họ two-stage (Faster R-CNN, Mask R-CNN) loại từ đầu vì chi phí tính toán không hợp ràng buộc CPU.

## 3.3. Bộ nhận dạng ký tự

Đây là lựa chọn trình bày **trung thực nhất về mức độ chắc chắn**: chọn _họ bộ nhận dạng_ theo khảo sát tài liệu (3.3.1), rồi chọn _bậc mô hình_ theo phép đo tự chạy (3.3.2).

### 3.3.1. PaddleOCR, EasyOCR, Tesseract — khảo sát tài liệu

**Các phương án đã xét:** tám bộ nhận dạng — PaddleOCR, EasyOCR, Tesseract, TrOCR, docTR, MMOCR, fast-plate-ocr và RapidOCR/OnnxTR.

### 3.3.2. PP-OCRv5 mobile so với PP-OCRv6 — đo trên máy đồ án

Mục này chọn **bậc mô hình** bên trong họ đã chọn, dựa trên số liệu **tự đo**; danh sách các bậc mô hình nhận dạng lấy từ tài liệu chính thức của PaddleOCR [21]<!-- paddleocr_rec_module --> (Bảng 3.1).

**Bảng 3.1.**[]{#tbl-3-1} PP-OCRv6_medium_rec so với PP-OCRv5_mobile_rec, đo trên 200 vùng cắt biển số của đồ án

| Mô hình                               |          Đúng chuỗi |    Trung vị |      p95 |
| ------------------------------------- | ------------------: | ----------: | -------: |
| **PP-OCRv5_mobile_rec** — _đang dùng_ | 134/200 = **67,0%** | **23,0 ms** |  31,9 ms |
| PP-OCRv6_medium_rec                   | 145/200 = **72,5%** |    386,9 ms | 429,0 ms |

PP-OCRv6_medium_rec đọc đúng hơn **5,5 điểm** nhưng chậm gấp **16,8 lần**. Cộng thêm 364 ms vào p95 hiện tại cho khoảng **1.507 ms**, vượt ngưỡng tối đa 1.500 ms của NFR-P1 — đây là **phép chiếu từ độ trễ nhánh nhận dạng, chưa đo lại trên toàn đường ống**, nhưng kết luận không đổi ở mọi biên sai số. Giữ **PP-OCRv5_mobile_rec**.

### 3.3.3. Benchmark ba bộ nhận dạng trên 2.801 biển số Việt Nam

Mục 3.3.1 kết thúc bằng một hạng mục chưa giải quyết: giữ PaddleOCR dựa trên lý do kỹ thuật, **không** dựa trên bằng chứng độ chính xác, trong khi tài liệu công khai nghiêng về EasyOCR. Mục này trả nợ đó.

**a) Thiết kế phép đo.** Cả ba bộ nhận dạng chạy trong **đúng một tầng bao quanh** — sao đúng chuỗi bước của bản bàn giao — trên **cùng một mảng ảnh đã chuẩn bị xong**, nên khác biệt duy nhất còn lại là bộ nhận dạng; đây cũng là bằng chứng thực nghiệm cho NFR-M5. Một chỗ cố ý không cào bằng: Tesseract chạy kèm whitelist `A-Z0-9`, vì giới hạn tập ký tự là **năng lực gốc** của nó. Công cụ đo được kiểm chứng bằng cách đối chiếu nhánh có tách đôi của PaddleOCR — **63,73%**, khớp NFR-A5 = 0,6373 đã công bố (Bảng 3.2).

**Bảng 3.2.**[]{#tbl-3-2} So sánh ba bộ nhận dạng ký tự trên 2.801 biển số Việt Nam (567 một dòng, 2.234 hai dòng)

| Bộ nhận dạng        | Nhánh       |    Toàn bộ |    1 dòng |    2 dòng |       CER | Rỗng |    p50 |
| ------------- | ----------- | ---------: | --------: | --------: | --------: | ---: | -----: |
| **PaddleOCR** | tắt tách đôi   |     28,81% |     94,2% |     12,2% |     0,588 |    6 | 295 ms |
| **PaddleOCR** | có tách đôi    | **63,73%** |     94,2% |     56,0% |     0,094 |   11 | 405 ms |
| **PaddleOCR** | + hậu xử lý | **68,87%** | **94,9%** | **62,3%** | **0,089** |   11 | 402 ms |
| EasyOCR       | tắt tách đôi   |      6,53% |     15,3% |      4,3% |     0,647 |    4 |  84 ms |
| EasyOCR       | có tách đôi    |     10,35% |     15,3% |      9,1% |     0,282 |    1 | 248 ms |
| EasyOCR       | + hậu xử lý |     14,28% |     28,6% |     10,7% |     0,269 |    1 | 249 ms |
| Tesseract     | tắt tách đôi   |      9,57% |     47,3% |  **0,0%** |     0,777 |  960 | 101 ms |
| Tesseract     | có tách đôi    |      9,60% |     47,3% |  **0,0%** |     0,565 |  700 | 108 ms |
| Tesseract     | + hậu xử lý |     10,28% |     50,4% |  **0,1%** |     0,567 |  700 | 106 ms |

**b) Kết quả.** Ở cấu hình bản bàn giao, PaddleOCR đạt **68,87%**, cao hơn EasyOCR **54,59 điểm** và Tesseract **58,59 điểm**. Kết luận ở mục 3.3.1 — *tài liệu công khai không cho thấy PaddleOCR vượt EasyOCR trên ảnh biển số* — vẫn đúng với các tài liệu đã khảo sát, nhưng phép đo trên biển số Việt Nam trong cùng tầng bao quanh cho kết quả khác, nên quyết định giữ PaddleOCR có thêm căn cứ thực nghiệm.

**c) Bước tách rồi ghép ngang KHÔNG độc lập với bộ nhận dạng.** Mức tăng khi bật tách đôi rất chênh nhau: PaddleOCR **+34,92 điểm** (28,81% → 63,73%), EasyOCR +3,82, Tesseract **+0,03**. Kỹ thuật chuyển bài toán đa dòng về một dòng vì vậy là điều kiện **cần nhưng chưa đủ** — nó còn đòi hỏi bộ nhận dạng đủ năng lực đọc dải ảnh đã ghép. Ngược lại, **bộ luật hậu xử lý giúp cả ba** (+5,14 · +3,93 · +0,68 điểm), nên đóng góp này **là** đóng góp độc lập bộ nhận dạng.

**d) Tesseract không đọc được biển hai dòng: 0,0% trên 2.234 mẫu**, kể cả sau khi đã ghép thành một dòng, trong khi đọc được 47,3% biển một dòng; nó có đọc ra chữ nhưng luôn kèm ký tự rác, và trả chuỗi rỗng 700/2.801 lần.

Phép đo này chạy trên **vùng biển đã cắt sẵn** nên kết luận chỉ áp cho tầng nhận dạng bên trong tầng bao quanh của đồ án — trên ảnh toàn cảnh qua bộ phát hiện thật, thứ tự xếp hạng có thể đảo ngược (5.5).

## 3.4. Nền tảng suy luận trên CPU: ONNX Runtime

**Các phương án đã xét:** chạy trực tiếp tệp trọng số PyTorch, ONNX Runtime, OpenVINO. **Tiêu chí:** tốc độ CPU, mức đa nền tảng, độ nặng phụ thuộc khi đóng gói. Bản giao hàng **chạy PyTorch**: nó đã đạt mọi chỉ tiêu độ trễ, còn hai phương án kia được đo và giữ lại như đường nâng cấp (5.6.3).

## 3.5. Các lựa chọn công nghệ nền tảng khác

Phần lớn quyết định còn lại là **ràng buộc của đề bài**; ghi lại kèm lý do và đánh đổi để Chương 4 tham chiếu.

Sáu quyết định nền tảng: **FastAPI** (tự sinh đặc tả OpenAPI, có sẵn WebSocket và tác vụ nền), **SQLAlchemy 2.0 + Alembic** (lược đồ đã thay đổi nên nhu cầu migration là có thật), **SQLite** (không thêm dịch vụ khi đóng gói; đánh đổi là chỉ một tiến trình ghi), **React + TypeScript + Vite + TailwindCSS**, **PyTorch** (Ultralytics khai báo là phụ thuộc lõi) và **Docker Compose**. Bảng đầy đủ kèm phương án thay thế và đánh đổi ở **Phụ lục VI**.

## 3.6. Độ phân giải đầu vào: 640 thay vì 416

Đồ án có sẵn hai mô hình để đối chiếu — `baseline-416-v1.pt` và `best.pt` — nhưng **phép so sánh giữa chúng không quy kết được nguyên nhân**: giữa hai lượt huấn luyện có **ba biến thay đổi đồng thời** (độ phân giải 416 → 640, bộ dữ liệu v1 → v3 đã khử rò rỉ, số epoch).

Lựa chọn **640** vì vậy đứng trên căn cứ khác: đó là độ phân giải mà chỉ tiêu NFR-A1/A2 đặt ra và là độ phân giải mọi số liệu tốc độ CPU chính thức của Ultralytics được đo. Muốn quy kết nguyên nhân cần một ma trận thí nghiệm cô lập từng biến (E1 – E3), ước tính **≈ 33 giờ CPU** — vượt ngân sách còn lại, ghi nhận là **chưa thực hiện** ở mục 6.3.
