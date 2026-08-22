# CHƯƠNG 6. KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN

## 6.1. Kết quả đạt được

Nhóm thực hiện đã bàn giao một hệ thống nhận dạng biển số xe Việt Nam hoàn chỉnh, chạy đầu cuối trên máy **không có GPU**: bộ phát hiện tự huấn luyện, khối nhận dạng ký tự, bộ luật hậu xử lý theo quy chuẩn Việt Nam, REST API, giao diện web, cơ sở dữ liệu và đóng gói Docker. Trạng thái xác minh bằng HTTP thật — 10 thao tác trên 9 đường dẫn phản hồi đúng, **1.002/1.002** kiểm thử tự động đạt, bao phủ tầng nghiệp vụ 87,7%.

**Bảng 6.1.** Đối chiếu chỉ tiêu đặt ra ở giai đoạn phân tích yêu cầu với số đo trên `models/best.pt`

|      Mã       | Chỉ tiêu                                                      |            Mục tiêu |                  Đo được |       |
| :-----------: | ------------------------------------------------------------- | ------------------: | -----------------------: | :---: |
|    A1 · A2    | mAP@0,5 · mAP@0,5:0,95 (phát hiện)                            |         0,90 · 0,65 |      **0,9829 · 0,7834** |  ✅   |
|      A3       | Precision · Recall (phát hiện)                                |         0,92 · 0,90 |      **0,9837 · 0,9714** |  ✅   |
|      A4       | 1 − CER (mức ký tự)                                           |                0,95 |               **0,9483** |  🟡   |
|    A5 · A6    | Chuỗi trước · sau hậu xử lý                                   |         0,85 · 0,90 |      **0,6373 · 0,7701** |  ❌   |
|      A7       | Toàn trình từ ảnh gốc                                         |                0,88 |               **0,563** ❌ | ⬜ \* |
|      A8       | Chênh lệch bố cục ở tầng phát hiện (điểm %)                   |                   — |                 **2,09** |   —   |
|      P1       | Độ trễ p95 một ảnh (ms)                                       |               ≤ 800 |             **1.143,10** |  🟡   |
| P4 · P5 · P6  | Nạp mô hình (s) · Overhead API · Truy vấn 10.000 bản ghi (ms) | ≤ 15 · ≤ 50 · ≤ 500 | **6,41 · 19,01 · 18,71** |  ✅   |
| P7 · R4 · SC1 | RSS (GB) · Thành công khi chạy liên tục · Yêu cầu đồng thời   |   ≤ 2 · ≥ 99% · ≥ 5 |    **0,806 · 100% · 10** |  ✅   |

\* A7 đo ở **mức ảnh toàn cảnh** — ước lượng phân tầng trên 1.606 khung biển của 1.514 ảnh hiện trường, 608 khung có nhãn. **Nhãn do mô hình ngôn ngữ-thị giác đọc, không phải người**, nên phải đọc như ước lượng có nguồn nhãn máy sinh (mục 5.5.5). Con số cũ 0,5552 đo trên ảnh cắt sẵn đã bị rút vì không tái lập được.

Các chỉ tiêu về phát hiện, thông lượng, độ tin cậy và chịu tải đều đạt; các chỉ tiêu về độ chính xác chuỗi chưa đạt ngưỡng. Riêng NFR-P1 chỉ đạt ngưỡng tối thiểu do bậc thử lại tăng thêm 34 biển nhận dạng đúng nhưng làm tăng độ trễ p95 — một thoái lui có chủ ý.

**Bốn đại lượng đo được mà khảo sát không tìm thấy tương đương trong tài liệu Việt Nam.**

1. **Đóng góp thuần của khối hậu xử lý theo vị trí: +13,28 điểm** — sửa đúng 372 biển, làm hỏng 0 biển trên 2.801 mẫu.
2. **Chênh lệch giữa hai bố cục biển trên dữ liệu Việt Nam thật: 23,07 điểm** ở khối nhận dạng, so với chỉ 2,09 điểm ở khối phát hiện. Rủi ro R-04 vì vậy nằm trọn ở tầng đọc ký tự.
3. **Benchmark ba bộ nhận dạng ký tự trên 2.801 biển, cùng một tầng bao quanh:** PaddleOCR đạt **68,87%**, so với EasyOCR (14,28%) và Tesseract (10,28%). Phép đo bổ sung bằng chứng thực nghiệm trên biển số Việt Nam cho lựa chọn bộ nhận dạng trong cấu hình của đồ án; kết quả này không được suy rộng thành so sánh tuyệt đối giữa các bộ nhận dạng. Thực nghiệm cũng cho một kết quả khác với dự đoán ban đầu: kỹ thuật tách và ghép ngang giúp độ chính xác của PaddleOCR tăng 34,92% nhưng chỉ cải thiện 0,03% đối với Tesseract; do đó, đây là **điều kiện cần, nhưng chưa đủ**.
4. **Bộ nhận màu nền biển đạt 97,89%** trên 1.565 ảnh có nhãn, cung cấp nguồn bằng chứng mà chuỗi ký tự không mang được: phân giải nhập nhằng giữa biển xanh nhà nước và biển trắng cá nhân khi hai chuỗi giống hệt nhau.

Ngoài các con số, nhóm thực hiện để lại **một quy trình đánh giá có kiểm chứng**: mọi số liệu sinh lại được bằng một lệnh, mọi phép so sánh kèm điều kiện đo, và các kết quả âm — hai lượt tinh chỉnh bộ nhận dạng đều không thắng model gốc ở chế độ vận hành — được ghi lại thay vì bỏ đi.

## 6.2. Hạn chế

**Bảng 6.2.** Mười hạn chế của đồ án

|  #  | Hạn chế                                                             |    Mức     | Hệ quả cần lưu ý                                                                                       |
| :-: | ------------------------------------------------------------------- | :--------: | ------------------------------------------------------------------------------------------------------ |
|  1  | **OCR biển hai dòng còn yếu, kéo độ chính xác toàn trình chưa đạt** |    Cao     | A6 = 0,7701 dưới ngưỡng — điểm nghẽn lớn nhất. A7 không đo được vì giao thức đo không đại diện (5.9.2)                                        |
|  2  | **Bộ dữ liệu lệch nặng về biển trắng**                              |    Cao     | 97,68% mẫu thuộc một lớp, nên kết luận về độ chính xác OCR **chỉ áp cho biển trắng**                   |
|  3  | Rò rỉ dữ liệu tồn dư không khử được bằng băm tri giác               | Trung bình | phash chỉ bắt tương đồng bố cục sáng-tối, không bắt "cùng xe, khác ngày"                               |
|  4  | Tập test không xuyên bộ dữ liệu                                     | Trung bình | mAP 0,9829 **lạc quan hơn** mức gặp khi triển khai với nguồn ảnh mới                                   |
|  5  | Độ trễ chỉ đạt ngưỡng tối thiểu                                     | Trung bình | p95 = 1.143,10 ms; đánh đổi có chủ ý lấy 34 biển đọc thêm                                              |
|  6  | **Bốn** yêu cầu mức _Must_ (FR-3.1, FR-3.4, FR-4.1, FR-2.5) chuyển sang _Won't_ | Trung bình | Ba yêu cầu đầu chỉ mất **màn hình hiển thị** — năng lực vẫn phục vụ ở tầng API và vẫn có kiểm thử; **riêng FR-2.5 mất chính năng lực** (không xuất được video đã chú thích). Nêu rõ cả bốn khi bảo vệ |
|  7  | SQLite chỉ cho phép một tiến trình ghi tại một thời điểm            |    Thấp    | Đủ cho quy mô đồ án, chặn ở triển khai đa người dùng                                                   |
|  8  | Xem trực tiếp và xử lý nền tranh chấp CPU với nhau                  |    Thấp    | Chạy video nền làm chậm luồng nhận dạng ảnh                                                            |
|  9  | **NFR-A9 không đo được** — độ chính xác theo điều kiện ảnh           | Trung bình | Không bộ dữ liệu nguồn nào gán nhãn ban ngày, ban đêm, chụp nghiêng hay ảnh mờ. Đây là **thiếu điều kiện quan sát**, không phải phép đo bị bỏ quên: chỉ tiêu ghi ⬜ chứ không ghi ❌ (mục 5.9.2) |
| 10  | **Biển đỏ quân đội và biển ngoại giao không có mẫu đánh giá**        | Trung bình | Bộ dữ liệu không chứa hai loại này, nên hai nhánh phân loại tuy đã cài đặt và chạy đúng trên ảnh demo vẫn **chưa có số liệu định lượng** |

## 6.3. Hướng phát triển

**Bảng 6.3.** Mười một hướng phát triển, xếp theo mức tác động

|  #  | Hướng                                                          | Giải hạn chế | Ghi chú                                                                                            |
| :-: | -------------------------------------------------------------- | :----------: | -------------------------------------------------------------------------------------------------- |
|  1  | **Huấn luyện lại module nhận dạng riêng cho biển số Việt Nam** |      1       | Hướng quan trọng nhất. Hai lượt tinh chỉnh đã thực hiện đều chưa thắng model gốc ở chế độ vận hành |
|  2  | Thu thập dữ liệu cho các loại biển hiếm                        |    2, 10     | Điều kiện để mở rộng kết luận ra ngoài biển trắng, và để hai nhánh biển đỏ · ngoại giao có số liệu đánh giá                                                  |
|  3  | Bổ sung nhãn chuỗi cho toàn tập                                |     1, 2     | Hiện chỉ 2.801/15.133 ảnh có nhãn chuỗi                                                            |
|  4  | Xây dựng tập test xuyên bộ dữ liệu                             |     3, 4     | Giữ nguyên một nguồn hoàn toàn không dùng để huấn luyện                                            |
|  5  | Tăng tốc suy luận: lượng tử hoá OCR, bật OpenVINO cho bộ phát hiện |      5       | **Đã đo** (5.6.3): OpenVINO nhanh **1,57×**, mAP không giảm, đầu cuối **+20%**. Còn lại là lượng tử hoá khối OCR — phần chiếm 64,3% ngân sách |
|  6  | Thí nghiệm cô lập biến độ phân giải · dữ liệu · số epoch       |      4       | Ma trận E1–E3, ước tính ≈ 33 giờ CPU                                                               |
|  7  | **Gán nhãn điều kiện chụp cho tập kiểm tra** (ban ngày · ban đêm · nghiêng · mờ) |      9       | Điều kiện **duy nhất** để NFR-A9 đo được. Rẻ: gán nhãn bốn lớp trên một tập con, không cần huấn luyện lại gì |
|  8  | Bám vết đối tượng qua khung hình cho video (SORT/DeepSORT)     |      —       | Gộp nhiều lần đọc cùng một biển thành một kết quả                                                  |
|  9  | Tách lịch chạy giữa xem trực tiếp và xử lý nền                 |      8       | Hàng đợi ưu tiên hoặc giới hạn luồng cho tác vụ nền                                                |
| 10  | Chuyển sang PostgreSQL nếu triển khai đa người dùng            |      7       | Chỉ cần khi vượt quy mô một tiến trình ghi                                                         |
| 11  | **Khôi phục hai yêu cầu _Must_ đã đưa ra khỏi phạm vi** — trang Tổng quan và xuất video đã chú thích |      6       | Thuần giao diện, không đụng tầng AI. Cả hai endpoint phục vụ chúng (`GET /api/statistics`, worker video) **vẫn chạy và vẫn có kiểm thử**, nên chỉ còn phần hiển thị |

## 6.4. Kết luận chung

Đề tài nhận dạng biển số xe Việt Nam, hỗ trợ biển một dòng, hai dòng và suy luận trên CPU. Hệ thống đạt các chỉ tiêu phát hiện nhưng chưa đạt chỉ tiêu độ chính xác nhận dạng ký tự; hạn chế chủ yếu nằm ở biển hai dòng.

Giá trị của đồ án vì vậy không nằm ở một con số cao nhất. Nó nằm ở ba chỗ: **một hệ thống hoàn chỉnh chạy được trong đúng ràng buộc phần cứng đã tuyên bố**; **bốn đại lượng đo được mà tài liệu trong nước chưa công bố tách bạch**, trong đó có benchmark ba bộ nhận dạng ký tự trên chính ảnh biển số Việt Nam; và **lối trình bày trong đó phần chưa đạt được phản ánh với cùng mức chi tiết như phần đạt** — kể cả khi điều đó có nghĩa là công bố rằng một đóng góp kỹ thuật lõi không độc lập với bộ nhận dạng như đã kỳ vọng.

Hướng ưu tiên là thay module nhận dạng ký tự bằng mô hình huấn luyện riêng cho biển số Việt Nam. Kiến trúc NFR-M5 cho phép thay bộ nhận dạng mà không sửa phần còn lại của hệ thống.
