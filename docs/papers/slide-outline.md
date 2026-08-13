# DÀN Ý SLIDE BẢO VỆ ĐỒ ÁN TỐT NGHIỆP

**Thời lượng dự kiến:** 15-20 phút
**Số lượng slide khuyến nghị:** 15-18 slide

> [!TIP]
> **Nguyên tắc làm slide:** 
> - Ít chữ, nhiều hình ảnh, sơ đồ và biểu đồ.
> - Nội dung trên slide chỉ là "từ khóa", bạn sẽ là người diễn giải chi tiết.
> - Bám sát các kết quả đã đo được trong Chương 5 và sự đánh đổi (trade-off) trong thiết kế.

---

## Phần 1: Mở đầu (2-3 slide)

**Slide 1: Tiêu đề**
- Tên đồ án: Nhận dạng biển số xe Việt Nam
- Sinh viên thực hiện & Giảng viên hướng dẫn.

**Slide 2: Đặt vấn đề & Bối cảnh**
- Xe máy chiếm áp đảo tại VN $\rightarrow$ Biển 2 dòng rất phổ biến nhưng ít được nghiên cứu sâu.
- Các mô hình mở thường yêu cầu cấu hình GPU cao.
- Luật định dạng biển số thay đổi liên tục (QCVN 08:2024/BCA).

**Slide 3: Mục tiêu & Ràng buộc (Lấy từ Chương 1)**
- **Mục tiêu:** Xây dựng hệ thống ALPR end-to-end xử lý cả biển 1 dòng và 2 dòng.
- **Ràng buộc cốt lõi:** Suy luận hoàn toàn trên **CPU** (không cần GPU CUDA).

---

## Phần 2: Phương pháp và Thiết kế (4-5 slide)

**Slide 4: Kiến trúc hệ thống (Chương 4)**
- Phương pháp Two-stage: Phát hiện (YOLO11) $\rightarrow$ Cắt & Chỉnh phẳng $\rightarrow$ Nhận dạng (PaddleOCR) $\rightarrow$ Hậu xử lý (Biểu thức chính quy).
- *Visual:* Chèn sơ đồ khối kiến trúc hệ thống (Hình 4.1 hoặc tương đương).

**Slide 5: Đóng góp kỹ thuật 1 - Xử lý biển 2 dòng**
- Thuật toán "Tách-rồi-ghép-ngang": Biến bài toán đa dòng về một dòng.
- *Visual:* Ảnh minh họa trước và sau khi cắt ngang và ghép biển số xe máy.

**Slide 6: Đóng góp kỹ thuật 2 - Bộ luật Hậu xử lý**
- Chuẩn hóa theo vị trí ký tự dựa trên luật biển số Việt Nam (34 tỉnh thành, các ký tự bị loại trừ).
- Vai trò: Gánh vác những sai sót không thể tránh khỏi của OCR. Phân biệt được O/0, 8/B.

**Slide 7: Dữ liệu huấn luyện (Chương 5)**
- Bộ dữ liệu gộp từ nhiều nguồn, được làm sạch (khử trùng lặp Hamming) còn **15.133 ảnh**.
- Việc chia Split được làm cẩn thận để tránh rò rỉ dữ liệu.

---

## Phần 3: Kết quả Thực nghiệm (5-6 slide)

> [!IMPORTANT]
> Đây là phần hội đồng quan tâm nhất. Hãy đưa ra các con số đã được kiểm chứng.

**Slide 8: Hiệu năng Phát hiện (YOLO11)**
- Các chỉ số: mAP@0.5 đạt **0,9829** (Vượt mục tiêu).
- *Visual:* Bảng/Biểu đồ so sánh độ chính xác phát hiện.

**Slide 9: Hiệu năng Nhận dạng (OCR Benchmark)**
- Kết quả đối đầu: PaddleOCR (**68,87%**) vượt xa EasyOCR (14,28%) và Tesseract.
- Khẳng định: Năng lực của Engine kết hợp với lớp bao quanh (tiền/hậu xử lý) mới tạo ra kết quả này.

**Slide 10: Tác động của Hậu xử lý & Xử lý 2 dòng**
- Chênh lệch lớn giữa biển 1 dòng (đã giải quyết xuất sắc) và 2 dòng (còn khó khăn).
- *Visual:* Ma trận nhầm lẫn (Confusion Matrix) trước và sau khi có hậu xử lý.

**Slide 11: Đánh giá Tốc độ & Chịu tải (CPU)**
- Trả lời câu hỏi: Có chạy được trên CPU không?
- Đạt chỉ tiêu về độ tin cậy và chịu tải. Chỉ tiêu độ trễ (NFR-P1) đạt mức ngưỡng tối thiểu — một sự **đánh đổi có chủ ý** để nhận diện thêm được 34 biển số.

---

## Phần 4: Demo & Tổng kết (3-4 slide)

**Slide 12: Giao diện và Ứng dụng thực tế**
- *Visual:* Screenshot hoặc Video/GIF (tùy chọn) quay lại màn hình hệ thống đang nhận dạng.
- Minh họa cách API kết nối với Frontend.

**Slide 13: Những điều chưa làm được (Hạn chế)**
- Nêu trung thực: Điểm gãy của OCR đối với biển 2 dòng.
- Đóng góp tách ghép ngang là điều kiện *cần* nhưng chưa *đủ* nếu engine không đủ mạnh.

**Slide 14: Kết luận & Hướng phát triển**
- Đã đóng gói được một hệ thống đo lường minh bạch, có cơ sở.
- Hướng phát triển: Huấn luyện một mô hình OCR chuyên biệt cho biển số VN thay vì dùng OCR đa dụng.

**Slide 15: Q&A**
- Lời cảm ơn hội đồng và mời đặt câu hỏi.

---
> [!NOTE]
> Bạn có thể copy nội dung này vào PowerPoint. Nhớ dùng các hình ảnh sơ đồ từ file báo cáo để slide thêm trực quan nhé!
