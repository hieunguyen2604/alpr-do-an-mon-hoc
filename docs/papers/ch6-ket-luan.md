# CHƯƠNG 6. KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN

## 6.1. Kết quả đạt được

Đồ án đã bàn giao một hệ thống nhận dạng biển số xe Việt Nam hoàn chỉnh, chạy đầu cuối trên máy **không có GPU**: bộ phát hiện tự huấn luyện, khối nhận dạng ký tự, bộ luật hậu xử lý theo quy chuẩn Việt Nam, REST API, giao diện web, cơ sở dữ liệu và đóng gói Docker. Trạng thái xác minh bằng HTTP thật — 10 thao tác trên 9 đường dẫn phản hồi đúng, **1.001/1.002** kiểm thử tự động đạt, bao phủ tầng nghiệp vụ 87,7%.

**Bảng 6.1.** Đối chiếu chỉ tiêu đặt ra ở giai đoạn phân tích yêu cầu với số đo trên `models/best.pt`

|      Mã       | Chỉ tiêu                                                      |            Mục tiêu |                  Đo được |       |
| :-----------: | ------------------------------------------------------------- | ------------------: | -----------------------: | :---: |
|    A1 · A2    | mAP@0,5 · mAP@0,5:0,95 (phát hiện)                            |         0,90 · 0,65 |      **0,9829 · 0,7834** |  ✅   |
|      A3       | Precision · Recall (phát hiện)                                |         0,92 · 0,90 |      **0,9837 · 0,9714** |  ✅   |
|      A4       | 1 − CER (mức ký tự)                                           |                0,95 |               **0,9454** |  🟡   |
|    A5 · A6    | Chuỗi trước · sau hậu xử lý                                   |         0,85 · 0,90 |      **0,6373 · 0,7512** |  ❌   |
|      A7       | Toàn trình từ ảnh gốc                                         |                0,88 |               **0,5552** | ❌ \* |
|      A8       | Chênh lệch bố cục ở tầng phát hiện (điểm %)                   |                   — |                 **2,09** |   —   |
|      P1       | Độ trễ p95 một ảnh (ms)                                       |               ≤ 800 |             **1.143,10** |  🟡   |
| P4 · P5 · P6  | Nạp mô hình (s) · Overhead API · Truy vấn 10.000 bản ghi (ms) | ≤ 15 · ≤ 50 · ≤ 500 | **6,41 · 19,01 · 18,71** |  ✅   |
| P7 · R4 · SC1 | RSS (GB) · Thành công khi chạy liên tục · Yêu cầu đồng thời   |   ≤ 2 · ≥ 99% · ≥ 5 |    **0,806 · 100% · 10** |  ✅   |

\* A7 phải đọc như **cận dưới bi quan** — đo trên ảnh nằm ngoài phân bố huấn luyện của bộ phát hiện nên tỉ lệ bỏ sót bị đánh giá cao hơn thực tế.

Các chỉ tiêu về phát hiện, độ tin cậy và chịu tải đều đạt; các chỉ tiêu về độ chính xác chuỗi chưa đạt ngưỡng. NFR-P1 chỉ đạt ngưỡng tối thiểu do bậc thử lại tăng thêm 34 biển nhận dạng đúng nhưng làm tăng độ trễ p95.

**Bốn đại lượng đo được mà khảo sát không tìm thấy tương đương trong tài liệu Việt Nam.**

1. **Đóng góp thuần của khối hậu xử lý theo vị trí: +11,39 điểm** — sửa đúng 319 biển, làm hỏng 0 biển trên 2.801 mẫu.
2. **Chênh lệch giữa hai bố cục biển trên dữ liệu Việt Nam thật: 25,45 điểm** ở khối nhận dạng, so với chỉ 2,09 điểm ở khối phát hiện. Rủi ro R-04 vì vậy nằm trọn ở tầng đọc ký tự.
3. **Benchmark ba bộ nhận dạng ký tự trên 2.801 biển, cùng một tầng bao quanh:** PaddleOCR đạt **68,87%**, so với EasyOCR (14,28%) và Tesseract (10,28%). Phép đo bổ sung bằng chứng thực nghiệm trên biển số Việt Nam cho lựa chọn bộ nhận dạng trong cấu hình của đồ án; kết quả này không được suy rộng thành so sánh tuyệt đối giữa các bộ nhận dạng. Thực nghiệm cũng cho một kết quả khác với dự đoán ban đầu: kỹ thuật tách và ghép ngang giúp độ chính xác của PaddleOCR tăng 34,92% nhưng chỉ cải thiện 0,03% đối với Tesseract; do đó, đây là **điều kiện cần, nhưng chưa đủ**.
4. **Bộ nhận màu nền biển đạt 97,89%** trên 1.565 ảnh có nhãn, cung cấp nguồn bằng chứng mà chuỗi ký tự không mang được: phân giải nhập nhằng giữa biển xanh nhà nước và biển trắng cá nhân khi hai chuỗi giống hệt nhau.

Ngoài các con số, đồ án để lại **một quy trình đánh giá có kiểm chứng**: mọi số liệu sinh lại được bằng một lệnh, mọi phép so sánh kèm điều kiện đo, và các kết quả âm — hai lượt tinh chỉnh bộ nhận dạng đều không thắng model gốc ở chế độ vận hành — được ghi lại thay vì bỏ đi.

## 6.2. Hạn chế

**Bảng 6.2.** Tám hạn chế của đồ án

|  #  | Hạn chế                                                             |    Mức     | Hệ quả cần lưu ý                                                                                       |
| :-: | ------------------------------------------------------------------- | :--------: | ------------------------------------------------------------------------------------------------------ |
|  1  | **OCR biển hai dòng còn yếu, kéo độ chính xác toàn trình chưa đạt** |    Cao     | A6 = 0,7512 và A7 = 0,5552 cùng dưới ngưỡng — điểm nghẽn lớn nhất                                        |
|  2  | **Bộ dữ liệu lệch nặng về biển trắng**                              |    Cao     | 97,68% mẫu thuộc một lớp, nên kết luận về độ chính xác OCR **chỉ áp cho biển trắng**                   |
|  3  | Rò rỉ dữ liệu tồn dư không khử được bằng băm tri giác               | Trung bình | phash chỉ bắt tương đồng bố cục sáng-tối, không bắt "cùng xe, khác ngày"                               |
|  4  | Tập test không xuyên bộ dữ liệu                                     | Trung bình | mAP 0,9829 **lạc quan hơn** mức gặp khi triển khai với nguồn ảnh mới                                   |
|  5  | Độ trễ chỉ đạt ngưỡng tối thiểu                                     | Trung bình | p95 = 1.143,10 ms; đánh đổi có chủ ý lấy 34 biển đọc thêm                                              |
|  6  | **Hai** yêu cầu mức _Must_ (FR-4.1, FR-2.5) bị đưa ra khỏi phạm vi  | Trung bình | Trang Tổng quan gỡ 20/07/2026; xuất video đã chú thích và huỷ tác vụ gỡ 03/08/2026 — nêu rõ khi bảo vệ |
|  7  | SQLite chỉ cho phép một tiến trình ghi tại một thời điểm            |    Thấp    | Đủ cho quy mô đồ án, chặn ở triển khai đa người dùng                                                   |
|  8  | Xem trực tiếp và xử lý nền tranh chấp CPU với nhau                  |    Thấp    | Chạy video nền làm chậm luồng nhận dạng ảnh                                                            |

## 6.3. Hướng phát triển

**Bảng 6.3.** Chín hướng phát triển, xếp theo mức tác động

|  #  | Hướng                                                          | Giải hạn chế | Ghi chú                                                                                            |
| :-: | -------------------------------------------------------------- | :----------: | -------------------------------------------------------------------------------------------------- |
|  1  | **Huấn luyện lại module nhận dạng riêng cho biển số Việt Nam** |      1       | Hướng quan trọng nhất. Hai lượt tinh chỉnh đã thực hiện đều chưa thắng model gốc ở chế độ vận hành |
|  2  | Thu thập dữ liệu cho các loại biển hiếm                        |      2       | Điều kiện để mở rộng kết luận ra ngoài biển trắng                                                  |
|  3  | Bổ sung nhãn chuỗi cho toàn tập                                |     1, 2     | Hiện chỉ 2.801/15.133 ảnh có nhãn chuỗi                                                            |
|  4  | Xây dựng tập test xuyên bộ dữ liệu                             |     3, 4     | Giữ nguyên một nguồn hoàn toàn không dùng để huấn luyện                                            |
|  5  | Tăng tốc suy luận: lượng tử hoá OCR, đóng gói ONNX/OpenVINO    |      5       | Phép so sánh nền tảng suy luận **chưa chạy** — có phương pháp và công cụ, chỉ thiếu thời gian máy            |
|  6  | Thí nghiệm cô lập biến độ phân giải · dữ liệu · số epoch       |      4       | Ma trận E1–E3, ước tính ≈ 33 giờ CPU                                                               |
|  7  | Bám vết đối tượng qua khung hình cho video (SORT/DeepSORT)     |      —       | Gộp nhiều lần đọc cùng một biển thành một kết quả                                                  |
|  8  | Tách lịch chạy giữa xem trực tiếp và xử lý nền                 |      8       | Hàng đợi ưu tiên hoặc giới hạn luồng cho tác vụ nền                                                |
|  9  | Chuyển sang PostgreSQL nếu triển khai đa người dùng            |      7       | Chỉ cần khi vượt quy mô một tiến trình ghi                                                         |

## 6.4. Kết luận chung

Đề tài nhận dạng biển số xe Việt Nam, hỗ trợ biển một dòng, hai dòng và suy luận trên CPU. Hệ thống đạt các chỉ tiêu phát hiện nhưng chưa đạt chỉ tiêu độ chính xác nhận dạng ký tự; hạn chế chủ yếu nằm ở biển hai dòng.

Giá trị của đồ án vì vậy không nằm ở một con số cao nhất. Nó nằm ở ba chỗ: **một hệ thống hoàn chỉnh chạy được trong đúng ràng buộc phần cứng đã tuyên bố**; **bốn đại lượng đo được mà tài liệu trong nước chưa công bố tách bạch**, trong đó có benchmark ba bộ nhận dạng ký tự trên chính ảnh biển số Việt Nam; và **lối trình bày trong đó phần chưa đạt được phản ánh với cùng mức chi tiết như phần đạt** — kể cả khi điều đó có nghĩa là công bố rằng một đóng góp kỹ thuật lõi không độc lập với bộ nhận dạng như đã kỳ vọng.

Hướng ưu tiên là thay module nhận dạng ký tự bằng mô hình huấn luyện riêng cho biển số Việt Nam. Kiến trúc NFR-M5 cho phép thay bộ nhận dạng mà không sửa phần còn lại của hệ thống.
