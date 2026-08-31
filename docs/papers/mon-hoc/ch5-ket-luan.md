# CHƯƠNG 5. KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN

## 5.1. Kết quả đạt được

Nhóm thực hiện đã xây dựng một hệ thống nhận dạng biển số xe Việt Nam chạy đầu cuối trên máy **không có GPU**, gồm bộ phát hiện tự huấn luyện, khối xử lý ảnh vùng biển, khối nhận dạng ký tự và bộ luật hậu xử lý theo quy chuẩn Việt Nam, kèm một ứng dụng web để trình diễn (Bảng 5.1).

**Bảng 5.1.**[]{#tbl-5-1} Đối chiếu chỉ tiêu đặt ra với kết quả đo được

| Đo cái gì | Ngưỡng tối thiểu | Mục tiêu | Đo được | |
|---|:--:|:--:|---:|:--:|
| mAP@0,5 · mAP@0,5:0,95 của bộ phát hiện | 0,85 · 0,55 | 0,90 · 0,65 | **0,9829 · 0,7834** | ✅ |
| Precision · Recall | 0,88 · 0,85 | 0,92 · 0,90 | **0,9837 · 0,9714** | ✅ |
| **C** — đúng mức ký tự | 0,92 | 0,95 | **0,9483** | 🟡 |
| **S₀ → S₁** — đúng cả chuỗi | 0,80 → 0,85 | 0,85 → 0,90 | **0,6373 → 0,7701** | ❌ |
| Độ trễ một ảnh, p95, trên CPU | ≤ 1.500 ms | ≤ 800 ms | **509,76 ms** | ✅ |

**Vạch ngăn giữa "đạt" và "không đạt" trùng khít vạch ngăn giữa hai tầng:** mọi chỉ tiêu của bộ phát hiện đều đạt với biên rộng, còn chỉ tiêu độ chính xác chuỗi đầy đủ thì không. Và phần thiếu hụt đó **nằm gần như trọn ở biển hai dòng** — biển một dòng đạt S₁ = 0,9541, vượt cả mục tiêu.

Ba đại lượng đo được đáng ghi nhận, đều liên quan trực tiếp tới nội dung môn học:

**Một — đóng góp thuần của khối hậu xử lý: +13,28 điểm**, sửa đúng 372 biển và làm hỏng 0 biển trên 2.801 mẫu, với chi phí tính toán 0,03 ms mỗi biển. Con số này chỉ đo được nhờ một quyết định thiết kế dữ liệu từ đầu: **lưu song song chuỗi thô và chuỗi đã chuẩn hoá**.

**Hai — bước tách rồi ghép ngang đóng góp 34,92 điểm cho PaddleOCR nhưng chỉ 0,03 điểm cho Tesseract.** Đây là kết quả khác với dự đoán ban đầu và làm **yếu đi** khẳng định ban đầu: phép biến đổi ảnh này là **điều kiện cần, không đủ**. Nó biến bài toán đa dòng thành bài toán một dòng, nhưng bộ nhận dạng vẫn phải đủ mạnh để tận dụng.

**Ba — trực giác hình dạng ký tự ghép đúng cặp nhưng sai chiều.** Bảng ánh xạ ban đầu suy từ hình dạng chỉ phủ 2 trên 10 cặp nhầm phổ biến nhất, và cặp `L` thì suy **ngược**: khi một vị trí bắt buộc là số mà bộ nhận dạng đọc ra `L`, sự thật là `4` **53 lần** và là `1` **đúng một lần**. Thay hai mục bằng bảng trích từ ma trận nhầm lẫn đo được — chỉ những cặp vượt ngưỡng thống kê — mua thêm **53 biển đọc đúng và làm hỏng 0 biển**, toàn bộ nằm ở biển hai dòng.

Ngoài các con số, nhóm thực hiện để lại **một quy trình đánh giá có kiểm chứng**: mọi bước xử lý ảnh bật tắt được độc lập nên đóng góp của từng bước đo được riêng, và các kết quả âm — phương án đọc riêng từng nửa thua 61 điểm, bậc siêu phân giải không cải thiện được biển nào — được ghi lại thay vì bỏ đi (Bảng 5.2).

## 5.2. Hạn chế

**Bảng 5.2.**[]{#tbl-5-2} Sáu hạn chế của đồ án

| # | Hạn chế | Mức | Hệ quả |
|:--:|---|:--:|---|
| 1 | **Nhận dạng biển hai dòng còn yếu** | Cao | S₁ = 0,7234 so với 0,9541 của biển một dòng — điểm nghẽn lớn nhất |
| 2 | **Bộ dữ liệu lệch nặng về biển trắng** (97,68%) | Cao | Kết luận về độ chính xác nhận dạng **chỉ áp cho biển trắng** |
| 3 | **Rò rỉ dữ liệu tồn dư** không khử được bằng băm tri giác | Cao | Băm tri giác tóm tắt bố cục khung ảnh, không tóm tắt chiếc xe (mục 3.2.3) |
| 4 | Tập kiểm thử **không xuyên bộ dữ liệu** | Trung bình | mAP 0,9829 lạc quan hơn mức gặp khi triển khai với nguồn ảnh mới |
| 5 | ~~Độ trễ p95 chỉ đạt ngưỡng tối thiểu~~ — **đã khép** | Thấp | p95 nay **509,76 ms**, vượt mục tiêu 800 ms; bậc thang thử lại vẫn giữ cùng 34 biển đọc thêm |
| 6 | **Biển đỏ quân đội và biển ngoại giao không có mẫu đánh giá** | Trung bình | Bộ dữ liệu không chứa hai loại này, nên hai nhánh phân loại tuy đã cài đặt và chạy đúng trên ảnh demo vẫn **chưa có số liệu định lượng** |

## 5.3. Hướng phát triển

Sáu hướng phát triển, xếp theo mức tác động, tổng hợp ở Bảng 5.3.

**Bảng 5.3.**[]{#tbl-5-3} Sáu hướng phát triển, xếp theo mức tác động

| # | Hướng | Giải hạn chế | Ghi chú |
|:--:|---|:--:|---|
| 1 | **Huấn luyện lại bộ nhận dạng ký tự riêng cho biển số Việt Nam** | 1 | Hướng quan trọng nhất. Phân tích ở mục 4.3.2 đã định vị điểm nghẽn nằm ở năng lực mô hình ký tự, không ở khâu xử lý ảnh |
| 2 | **Mở rộng bảng ánh xạ nhầm lẫn khi ngữ liệu lớn hơn** | 1 | Vòng đầu **đã làm** và mua được 53 biển; năm mục còn lại chưa đủ bằng chứng (thắng dưới 10 lần) nên vẫn giữ phỏng đoán theo hình dạng — ngữ liệu lớn hơn sẽ quyết được |
| 3 | Thu thập dữ liệu biển vàng, xanh, đỏ và ngoại giao | 2, 6 | Điều kiện để mở rộng kết luận ra ngoài biển trắng, và để hai nhánh biển đỏ · ngoại giao có số liệu đánh giá |
| 4 | **Khử rò rỉ theo chuỗi biển số thay vì theo băm tri giác** | 3, 4 | Gom nhóm theo chuỗi ký tự thay vì theo tương đồng ảnh; giải đúng loại rò rỉ mà pHash không thấy |
| 5 | Đo lại bậc siêu phân giải trên ngữ liệu có biển thật sự nhỏ | — | Mục 4.4.3: số 0 hiện tại do **thiếu điều kiện quan sát**, không phải do đã quan sát thấy vô dụng |
| 6 | Tăng tốc khối nhận dạng: lượng tử hoá, đóng gói ONNX hoặc OpenVINO | 5 | Khối nhận dạng chiếm 60,8% ngân sách độ trễ (Bảng 4.10). Riêng bộ phát hiện đã đo: OpenVINO nhanh **1,57×** mà không giảm mAP |

## 5.4. Kết luận chung

Đề tài đặt ra một bài toán có ràng buộc rõ: nhận dạng biển số xe Việt Nam, hỗ trợ **cả biển một dòng và biển hai dòng**, suy luận hoàn toàn trên CPU. Hệ thống đáp ứng ràng buộc vận hành và đạt toàn bộ chỉ tiêu ở tầng phát hiện với biên rộng, nhưng chưa đạt chỉ tiêu độ chính xác ở tầng nhận dạng ký tự.

Xét từ góc độ môn học, kết quả đáng chú ý nhất không phải một con số cao mà là **quan hệ giữa phép biến đổi ảnh và giả định của mô hình**. Bài toán biển hai dòng không được giải bằng cách thay một mô hình mạnh hơn, mà bằng cách **biến đổi ảnh đầu vào cho khớp giả định của mô hình sẵn có**: hạ một ảnh hai dòng thành một dải một dòng, và trong lúc đó tăng gấp đôi số điểm ảnh dành cho mỗi hàng ký tự. Phép biến đổi đó đóng góp **34,92 điểm** — nhiều hơn bất kỳ thay đổi nào khác trong đồ án.

Đồng thời, chính phép đo đó cũng chỉ ra giới hạn của cách tiếp cận: nó đóng góp **0,03 điểm** cho Tesseract. Xử lý ảnh dọn đường cho mô hình, nhưng không thay được năng lực của mô hình.
