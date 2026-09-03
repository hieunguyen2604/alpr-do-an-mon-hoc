# CHƯƠNG 1. GIỚI THIỆU

## 1.1. Đặt vấn đề

Tính đến tháng 9/2024, Việt Nam có khoảng **77 triệu xe máy đã đăng ký**, chiếm **85–90% lưu lượng phương tiện trên đường** [1]. Con số này là một ràng buộc kỹ thuật trực tiếp chứ không phải bối cảnh xã hội: mọi xe mô tô đều mang **biển hai dòng gần vuông**, nên ở Việt Nam biển hai dòng là dạng phổ biến chứ không phải ngoại lệ. Biển xe mô tô chỉ 140 × 190 mm, nên đây đồng thời là bài toán phát hiện **đối tượng nhỏ**.

Nhận dạng biển số xe tự động (ALPR) là lõi của bãi đỗ xe thông minh, thu phí không dừng, kiểm soát ra vào và giám sát giao thông. Cả bốn ứng dụng đều đo cùng một đại lượng: **tỉ lệ đọc đúng toàn bộ chuỗi biển số**, chứ không phải tỉ lệ đọc đúng từng ký tự — đọc đúng 9 trên 10 ký tự vẫn là đọc sai biển.

**Không thể dùng trực tiếp giải pháp nước ngoài**, vì hai lý do đo được và một lý do pháp lý.

**Thứ nhất, biển hai dòng là điểm suy giảm đã đo được.** Trên tập kiểm thử cân bằng của bộ **RodoSol-ALPR (Brazil)** — 4.000 ảnh ô tô biển một dòng, 4.000 ảnh xe máy biển hai dòng — hệ thống thương mại OpenALPR nhận đúng **94,3% biển một dòng nhưng chỉ 45,7% biển hai dòng**, chênh **48,6 điểm phần trăm**, không biến số nào khác thay đổi ngoài bố cục biển [2]. Cặp số này đo trên **dữ liệu Brazil, không phải dữ liệu Việt Nam**; đồ án dẫn nó như một dẫn chứng định lượng về độ khó của biển hai dòng tại một quốc gia cũng có tỉ lệ xe máy cao, không phải như mốc chuẩn.

**Thứ hai, cấu trúc chuỗi và hình học biển là đặc thù quốc gia.** Biển số Việt Nam theo Thông tư 79/2024/TT-BCA [3], mã tỉnh theo Thông tư 51/2025/TT-BCA [4], kích thước vật lý theo QCVN 08:2024/BCA [5]. Ba đặc thù ở Chương 2 không học được từ dữ liệu nước ngoài, trong đó **tỉ lệ khung hình** là đại lượng thuần hình học mà toàn bộ khối xử lý ảnh của đồ án dựa vào.

**Thứ ba, điều kiện thu nhận ảnh khác biệt:** biển bám bụi, cong vênh, chụp nghiêng, ngược sáng, ảnh đêm, bề mặt phản quang gây chói cục bộ — đúng nhóm vấn đề mà môn Xử lý ảnh cung cấp công cụ để giải.

## 1.2. Mục tiêu và phạm vi

### 1.2.1. Mục tiêu

Xây dựng một hệ thống nhận dạng biển số xe Việt Nam chạy được đầu cuối, **suy luận hoàn toàn trên CPU**, hỗ trợ cả biển một dòng và biển hai dòng. Trọng tâm của đồ án môn học đặt ở **khối xử lý ảnh** nằm giữa bộ phát hiện và bộ nhận dạng ký tự: chuẩn hoá, tăng cường tương phản, khử nhiễu bảo toàn biên, nắn hình, phân loại bố cục theo hình học, tách và ghép ảnh, phân tích màu trong không gian HSV (Bảng 1.1).

**Bảng 1.1.**[]{#tbl-1-1} Chỉ tiêu đặt ra, mỗi chỉ tiêu có ngưỡng tối thiểu và mục tiêu

| Đo cái gì | Ngưỡng tối thiểu | Mục tiêu |
|---|:--:|:--:|
| mAP@0,5 của bộ phát hiện biển số | 0,85 | 0,90 |
| mAP@0,5:0,95 của bộ phát hiện | 0,55 | 0,65 |
| Độ chính xác mức ký tự (1 − CER) | 0,92 | 0,95 |
| Đúng cả chuỗi, **trước** hậu xử lý | 0,80 | 0,85 |
| Đúng cả chuỗi, **sau** hậu xử lý | 0,85 | 0,90 |
| Độ trễ xử lý một ảnh, p95, **trên CPU** | ≤ 1.500 ms | ≤ 800 ms |

Hai chỉ tiêu *trước* và *sau* hậu xử lý được đo tách bạch có chủ đích: **hiệu số giữa chúng chính là đóng góp định lượng của khối hậu xử lý**, đại lượng mà phần lớn tài liệu chỉ mô tả định tính.

Ngưỡng độ trễ rộng hơn các bài báo ALPR vì máy thực hiện **không có GPU CUDA**: huấn luyện chạy trên GPU đám mây, còn toàn bộ suy luận và trình diễn chạy trên CPU, trong khi các bài báo thường đo trên GPU rời. Mọi số liệu hiệu năng trong đồ án vì vậy bắt buộc kèm cấu hình phần cứng.

### 1.2.2. Phạm vi

**Trong phạm vi:** thu thập và làm sạch bộ dữ liệu ảnh; khử trùng lặp bằng băm tri giác; huấn luyện bộ phát hiện; toàn bộ khối xử lý ảnh vùng biển; bộ luật hậu xử lý chuỗi theo quy chuẩn Việt Nam; phân loại màu nền; đánh giá đầy đủ kèm phân tích lỗi; một ứng dụng web tối thiểu để trình diễn.

**Ngoài phạm vi:** xác thực và phân quyền (hệ thống chạy nội bộ); bám vết đối tượng qua khung hình; ước lượng tốc độ và phát hiện vi phạm; biển số nước ngoài; huấn luyện bộ nhận dạng ký tự từ đầu — đồ án dùng mô hình tiền huấn luyện và chỉ tinh chỉnh; suy luận trên GPU.

## 1.3. Lựa chọn công nghệ

Mỗi lựa chọn dưới đây bị chi phối bởi cùng bốn ràng buộc: **không có GPU**, **phải xử lý được biển hai dòng**, **phải đóng gói bàn giao được**, và **ngân sách thời gian máy hữu hạn** (Bảng 1.2).

**Bảng 1.2.**[]{#tbl-1-2} Các quyết định công nghệ và lý do

| Hạng mục | Chọn | Phương án đã xét | Lý do chính | Đánh đổi |
|---|---|---|---|---|
| Thư viện xử lý ảnh | **OpenCV** [16] | scikit-image, Pillow | Đủ cả CLAHE, lọc song phương, biến đổi phối cảnh, HSV trong một thư viện; ràng buộc thời gian thực | API kiểu C cũ, dễ nhầm thứ tự kênh BGR/RGB |
| Bộ phát hiện | **YOLO11n** [7] | Faster R-CNN, SSD, YOLOv8 | Họ một giai đoạn, **anchor-free** — hồi quy trực tiếp khoảng cách tâm tới bốn cạnh nên xử lý được cả tỉ lệ 4,7:1 lẫn 1,4:1 bằng một cơ chế; biến thể `n` chỉ 2,59 triệu tham số | Họ hai giai đoạn chính xác hơn nhưng không hợp ràng buộc CPU |
| Nhận dạng ký tự | **PaddleOCR PP-OCRv5 mobile** [8] | EasyOCR, Tesseract | Cao hơn hẳn hai bộ nhận dạng kia trên chính ảnh biển số Việt Nam, trong cấu hình đánh giá của đồ án (mục 4.3.4) | Là đường ống nhiều giai đoạn thiết kế cho ảnh tài liệu, nên trả chi phí cho năng lực mà vùng biển đã cắt không cần |
| Hậu xử lý | **Bộ luật tự thiết kế** | Mô hình ngôn ngữ, từ điển | Biển số không có từ vựng để dựa vào; ràng buộc cú pháp lại rất chặt và kiểm được bằng biểu thức chính quy | Phải cập nhật khi văn bản pháp quy thay đổi |
| Ứng dụng trình diễn | **FastAPI + React + Docker** | Notebook, ứng dụng desktop | Yêu cầu chạy được bằng một lệnh trên máy sạch | Không phải trọng tâm của môn học |

Việc chọn **PaddleOCR** là kết quả của một phép đo do đồ án tự chạy chứ không phải suy đoán từ tài liệu: một số tài liệu công khai nghiêng về EasyOCR, còn phép đo trên 2.801 biển số Việt Nam ở mục 4.3.4 cho kết quả ngược lại **trong cấu hình đánh giá của đồ án**.
