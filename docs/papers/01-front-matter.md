<!-- PHẦN ĐẦU QUYỂN (front matter) — khối này là ghi chú biên soạn, không in ra.

     Đề tài: Xây dựng hệ thống nhận diện biển số xe bằng trí tuệ nhân tạo
     (Developing an AI-based vehicle license plate recognition system)

     Tên đề tài lấy nguyên văn theo Đề cương chi tiết đã đăng ký
     (GVHD: ThS. Cáp Phạm Đình Thăng; thực hiện 16/07/2026 – 24/09/2026).
     Bản nháp trước dùng "Xây dựng hệ thống nhận dạng biển số xe Việt Nam
     ứng dụng Trí tuệ nhân tạo" — đã thay ở mọi vị trí để bìa khớp hồ sơ.

     Mọi chỗ đặt trong dấu «…» là chỗ trống phải điền thông tin thật.
-->

## A. TRANG BÌA

> Trình bày theo định dạng bìa chuẩn của đồ án tốt nghiệp đại học Việt Nam. Khi kết xuất sang PDF/Word, toàn bộ khối dưới đây căn giữa trang, không đánh số trang. Bìa cứng (bìa ngoài) và bìa lót (bìa trong) có nội dung giống nhau; bìa lót bổ sung dòng giảng viên hướng dẫn nếu quy chế của khoa yêu cầu.

<div align="center">

**ĐẠI HỌC QUỐC GIA TP. HỒ CHÍ MINH**

**TRƯỜNG ĐẠI HỌC CÔNG NGHỆ THÔNG TIN**

<br/>

*(chèn logo Trường Đại học Công nghệ Thông tin khi kết xuất bản in)*

<br/><br/>

# ĐỒ ÁN TỐT NGHIỆP ĐẠI HỌC

<br/>

### Đề tài:

# XÂY DỰNG HỆ THỐNG NHẬN DIỆN BIỂN SỐ XE BẰNG TRÍ TUỆ NHÂN TẠO

*Developing an AI-based vehicle license plate recognition system*

<br/><br/>

| | |
|---:|:---|
| **Ngành:** | Trí tuệ nhân tạo |
| **Chuyên ngành:** | Trí tuệ nhân tạo |
| **Sinh viên thực hiện:** | **Phạm Công Thành** — MSSV **25410013** |
| | **Nguyễn Minh Hiếu** — MSSV **25410007** |
| **Lớp:** | AI503.F3.LT.TTNT |
| **Khoá:** | 2025 |
| **Giảng viên hướng dẫn:** | ThS. Cáp Phạm Đình Thăng |

<br/><br/>

**TP. Hồ Chí Minh, tháng 9 năm 2026**

</div>

---

## B. TRANG NHIỆM VỤ ĐỒ ÁN VÀ NHẬN XÉT

> Ba trang dưới đây là biểu mẫu do khoa cấp, nội dung do khoa và giảng viên điền. Giữ chỗ ở đây để thứ tự trang khi ghép quyển không bị lệch. Nếu quy chế của khoa không yêu cầu trang nào, **xoá hẳn trang đó** thay vì để trống.

### B.1. Phiếu giao nhiệm vụ đồ án tốt nghiệp

*«Theo biểu mẫu của Khoa — gồm: thông tin sinh viên, tên đề tài, nội dung nhiệm vụ, số liệu ban đầu, ngày giao, ngày hoàn thành, chữ ký giảng viên hướng dẫn và trưởng bộ môn.»*

### B.2. Nhận xét của giảng viên hướng dẫn

*«Do giảng viên hướng dẫn viết và ký.»*

### B.3. Nhận xét của giảng viên phản biện

*«Do giảng viên phản biện viết và ký.»*

---

## C. LỜI CAM ĐOAN

<div align="center">

**LỜI CAM ĐOAN**

</div>

Chúng tôi xin cam đoan đồ án tốt nghiệp với đề tài **"Xây dựng hệ thống nhận diện biển số xe bằng trí tuệ nhân tạo"** là công trình nghiên cứu của nhóm chúng tôi, được thực hiện dưới sự hướng dẫn khoa học của **ThS. Cáp Phạm Đình Thăng**.

Các nội dung nghiên cứu, kết quả thực nghiệm và số liệu trình bày trong đồ án là trung thực và do chính chúng tôi thực hiện. Các thư viện, mô hình và bộ dữ liệu mã nguồn mở được sử dụng lại đều được nêu rõ nguồn gốc, phiên bản và điều kiện giấy phép tại các chương tương ứng.

Mọi tài liệu tham khảo, số liệu, bảng biểu và hình vẽ được trích dẫn từ công trình của tác giả khác đều được ghi rõ nguồn trong phần Tài liệu tham khảo theo đúng quy định về trích dẫn học thuật. Các văn bản quy phạm pháp luật được viện dẫn trong đồ án đã được đối chiếu với văn bản gốc và kiểm tra hiệu lực tại thời điểm thực hiện.

Chúng tôi xin cam đoan không sao chép nguyên văn hoặc sử dụng kết quả của người khác mà không ghi nguồn. Chúng tôi xin chịu hoàn toàn trách nhiệm trước Nhà trường và Hội đồng đánh giá về lời cam đoan này.

<div align="right">

*TP. Hồ Chí Minh, ngày 24 tháng 9 năm 2026*

**Sinh viên thực hiện**

*(Ký và ghi rõ họ tên)*

<br/><br/>

**Phạm Công Thành**  ·  **Nguyễn Minh Hiếu**

</div>

---

## D. LỜI CẢM ƠN

<div align="center">

**LỜI CẢM ƠN**

</div>

Để hoàn thành đồ án tốt nghiệp này, chúng tôi đã nhận được sự giúp đỡ và hướng dẫn tận tình từ nhiều thầy cô, gia đình và bạn bè.

Trước hết, chúng tôi xin bày tỏ lòng biết ơn sâu sắc tới **ThS. Cáp Phạm Đình Thăng** — người đã trực tiếp hướng dẫn chúng tôi trong suốt quá trình thực hiện đồ án. Thầy không chỉ định hướng về mặt chuyên môn mà còn chỉ ra cho chúng tôi những yêu cầu nghiêm ngặt về tính trung thực trong nghiên cứu khoa học: mọi số liệu công bố đều phải kiểm chứng được, mọi trích dẫn đều phải truy về nguồn gốc, và những gì chưa đo được thì không được suy đoán.

Chúng tôi xin chân thành cảm ơn quý thầy cô Trường Đại học Công nghệ Thông tin — Đại học Quốc gia TP. Hồ Chí Minh đã truyền đạt cho chúng tôi nền tảng kiến thức trong suốt những năm học vừa qua — đó là cơ sở để chúng tôi tiếp cận và giải quyết bài toán của đồ án này.

Chúng tôi cũng xin gửi lời cảm ơn tới cộng đồng mã nguồn mở, các nhóm nghiên cứu đã công bố công trình, mã nguồn và bộ dữ liệu về nhận dạng biển số xe. Đồ án này được xây dựng trên nền tảng những đóng góp đó.

Cuối cùng, chúng tôi xin cảm ơn gia đình và bạn bè đã luôn động viên, ủng hộ trong suốt quá trình học tập và thực hiện đồ án.

Do giới hạn về thời gian, phần cứng và kinh nghiệm, đồ án chắc chắn còn nhiều thiếu sót. Chúng tôi rất mong nhận được ý kiến đóng góp của quý thầy cô và Hội đồng để hoàn thiện hơn.

Chúng tôi xin chân thành cảm ơn!

<div align="right">

*TP. Hồ Chí Minh, ngày 24 tháng 9 năm 2026*

**Nhóm sinh viên thực hiện**

<br/>

**Phạm Công Thành**  ·  **Nguyễn Minh Hiếu**

</div>

---

## E. MỤC LỤC

<!-- Sinh tự động bằng scripts/gen_front_matter_lists.py từ chính các tệp
     chương. Không sửa tay — chạy lại script sau mỗi lần đổi cấu trúc.
     Số trang do Word điền khi xuất .docx. -->

```
LỜI CAM ĐOAN
LỜI CẢM ƠN
MỤC LỤC
DANH MỤC HÌNH VẼ
DANH MỤC BẢNG BIỂU
DANH MỤC TỪ VIẾT TẮT
TÓM TẮT ĐỒ ÁN
ABSTRACT

CHƯƠNG 1. GIỚI THIỆU
    1.1. Đặt vấn đề
    1.2. Mục tiêu đề tài
    1.3. Đối tượng và phạm vi nghiên cứu
    1.4. Phương pháp nghiên cứu
    1.5. Ý nghĩa khoa học và thực tiễn
    1.6. Đóng góp của đề tài
    1.7. Bố cục quyển đồ án
    Tóm tắt chương

CHƯƠNG 2. CƠ SỞ LÝ THUYẾT
    2.1. Tổng quan bài toán ALPR
    2.2. Quy chuẩn biển số xe Việt Nam
    2.3. Lịch sử phát triển các phương pháp
    2.4. Phân loại các hướng tiếp cận hiện nay
    2.5. Cơ sở lý thuyết về phát hiện đối tượng
    2.6. Cơ sở lý thuyết về nhận dạng ký tự
    2.7. Các công trình liên quan
    2.8. Kết luận chương

CHƯƠNG 3. KHẢO SÁT CÔNG NGHỆ VÀ LỰA CHỌN MÔ HÌNH
    3.1. Phương pháp khảo sát và tiêu chí lựa chọn
    3.2. Mô hình phát hiện: YOLO11
    3.3. Engine nhận dạng ký tự
    3.4. Runtime suy luận trên CPU: ONNX Runtime
    3.5. Các lựa chọn công nghệ nền tảng khác
    3.6. Khảo sát ảnh hưởng của độ phân giải và chất lượng split
    3.7. Kết luận chương

CHƯƠNG 4. PHÂN TÍCH VÀ THIẾT KẾ HỆ THỐNG
    4.1. Phân tích yêu cầu
    4.2. Kiến trúc hệ thống
    4.3. Thiết kế chi tiết
    4.4. Thiết kế cơ sở dữ liệu
    4.5. Thiết kế giao diện người dùng
    4.6. Kết luận chương

CHƯƠNG 5. XÂY DỰNG HỆ THỐNG VÀ HUẤN LUYỆN MÔ HÌNH
    5.1. Môi trường và công cụ phát triển
    5.2. Xây dựng bộ dữ liệu
    5.3. Huấn luyện bộ phát hiện biển số
    5.4. Tinh chỉnh bộ nhận dạng ký tự
    5.5. Cài đặt tầng AI
    5.6. Cài đặt backend
    5.7. Cài đặt frontend
    5.8. Triển khai bằng Docker
    5.9. Những chỗ cài đặt lệch khỏi thiết kế ở Chương 4, và lý do
    5.10. Kết luận chương

CHƯƠNG 6. THỰC NGHIỆM VÀ ĐÁNH GIÁ
    6.1. Mục tiêu và phương pháp đánh giá
    6.2. Môi trường thực nghiệm
    6.3. Bộ dữ liệu thực nghiệm
    6.4. Đánh giá bộ phát hiện biển số
    6.5. Đánh giá khối OCR và hậu xử lý
    6.6. Đánh giá hiệu năng
    6.7. Đối chiếu toàn bộ chỉ tiêu phi chức năng
    6.8. Phân tích lỗi
    6.9. Bàn luận
    6.10. Đối chiếu với các công trình đã công bố
    6.11. Kết luận chương

CHƯƠNG 7. KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN
    7.1. Tổng kết công việc đã thực hiện
    7.2. Các kết quả đạt được
    7.3. Các hạn chế của đồ án
    7.4. Hướng phát triển
    7.5. Kết luận chung

TÀI LIỆU THAM KHẢO
PHỤ LỤC
```

---

## F. DANH MỤC HÌNH VẼ

<!-- Sinh tự động bằng scripts/gen_front_matter_lists.py từ chính các tệp
     chương. Không sửa tay — chạy lại script sau mỗi lần đổi cấu trúc.
     Số trang do Word điền khi xuất .docx. -->
<!-- Quy ước: Hình <chương>.<thứ tự>. Chú thích đặt DƯỚI hình, căn giữa.
     Hình lấy/phỏng theo nguồn khác bắt buộc ghi nguồn kèm [n]. -->

| Ký hiệu | Tên hình | Trang |
|---|---|:---:|
| Hình 2.1 | * Sơ đồ pipeline ALPR điển hình (tổng hợp từ [2], [3], [20], [22], [23]) | — |
| Hình 2.2 | ** Chuỗi văn bản pháp lý về biển số xe đang có hiệu lực | — |
| Hình 2.3 | * Khoảng trống tỷ lệ khung hình giữa biển hai dòng và biển một dòng (dẫn xuất từ [11]) | — |
| Hình 2.4 | ** Sơ đồ phân loại hai trục các hướng tiếp cận ALPR và định vị lựa chọn của đồ án | — |
| Hình 2.5 | * Kiến trúc tổng quát backbone – neck – head của YOLO11 (theo [49], [16]) | — |
| Hình 2.6 | * Cấu trúc phân cấp của khối C2PSA trong YOLO11 (đối chiếu mã nguồn [51]) | — |
| Hình 2.7 | * Cơ chế sụp đổ của CTC trên ảnh văn bản hai dòng (theo [61]) | — |
| Hình 5.1 | * Đường cong hàm mất mát theo epoch — box_loss, cls_loss, dfl_loss, tách riêng train và val | — |
| Hình 5.2 | * Tiến triển mAP@0.5 và mAP@0.5:0.95 trên tập validation theo epoch | — |
| Hình 5.3 | * Tiến triển precision và recall trên tập validation theo epoch | — |
| Hình 6.1 | Giao thức đo và ràng buộc phụ thuộc giữa các bước đánh giá | — |
| Hình 6.2 | * Đường cong Precision–Recall trên tập test, vẽ tách theo layout (một dòng / hai dòng) | — |
| Hình 6.3 | * Ma trận nhầm lẫn nhận biết layout: hàng là quần thể nhãn thật (một dòng / hai dòng / nền), cột là dự đoán | — |
| Hình 6.4 | * Đường cong F1 theo ngưỡng confidence — dùng để xác định ngưỡng vận hành | — |
| Hình 6.5 | * Ma trận nhầm lẫn ký tự 36×36, thang log(1+n), đo trên chuỗi thô trước hậu xử lý | — |
| Hình 6.6 | * Biểu đồ cột 15 cặp ký tự bị nhầm nhiều nhất | — |
| Hình 6.7 | * Phân bố độ trễ đầu-cuối — biểu đồ tần suất kèm vạch đánh dấu p50/p95/p99 và hai ngưỡng chỉ tiêu | — |
| Hình 6.8 | * Biểu đồ cột chồng phân rã ngân sách độ trễ: ước lượng Phase 0 so với số đo thật | — |
| Hình 6.9 | * Đường cong thông lượng và tỉ lệ lỗi theo mức đồng thời 1 / 2 / 5 / 10 | — |
| Hình 6.10 | * Ảnh minh hoạ loại E1 — biển bị bỏ sót. Ghi rõ: kích thước box tương đối, điều kiện ảnh quan sát được | — |
| Hình 6.11 | * Ảnh minh hoạ loại E3 — nhầm ký tự. Hiển thị vùng cắt, chuỗi thô, chuỗi sau hậu xử lý, nhãn thật | — |
| Hình 6.12 | * Ảnh minh hoạ loại E6 — sai thứ tự trên biển hai dòng | — |
| Hình 6.13 | * Ca mà hậu xử lý làm hỏng một chuỗi vốn đã đúng — nếu tồn tại ca như vậy, bắt buộc phải trưng ra, vì nó là bằng chứng phản biện đối với đóng góp được công bố ở mục 6.5.2 | — |

---

## G. DANH MỤC BẢNG BIỂU

<!-- Sinh tự động bằng scripts/gen_front_matter_lists.py từ chính các tệp
     chương. Không sửa tay — chạy lại script sau mỗi lần đổi cấu trúc.
     Số trang do Word điền khi xuất .docx. -->
<!-- Quy ước: Bảng <chương>.<thứ tự>. Chú thích đặt TRÊN bảng.
     Bảng tổng hợp từ nguồn khác bắt buộc ghi nguồn kèm [n]. -->

| Ký hiệu | Tên bảng | Trang |
|---|---|:---:|
| Bảng 1.1 | Nhóm chỉ tiêu độ chính xác | — |
| Bảng 1.2 | Nhóm chỉ tiêu hiệu năng trên CPU | — |
| Bảng 1.3 | Phạm vi trong nghiên cứu | — |
| Bảng 1.4 | Các hạng mục nằm ngoài phạm vi và lý do loại trừ | — |
| Bảng 1.5 | Mười hai giai đoạn thực hiện, công sức và điều kiện thông qua | — |
| Bảng 2.1 | Các nhóm ứng dụng của hệ thống ALPR | — |
| Bảng 2.2 | Các văn bản pháp lý là căn cứ của đồ án | — |
| Bảng 2.3 | Phân rã thành phần biển số ô tô | — |
| Bảng 2.4 | Hai kiểu seri biển xe máy đang cùng lưu hành | — |
| Bảng 2.5 | Tám mã không được sử dụng | — |
| Bảng 2.6 | Tổng hợp các tập ký tự seri | — |
| Bảng 2.7 | Các ký hiệu seri đặc biệt [29] | — |
| Bảng 2.8 | Màu nền biển số và đối tượng áp dụng [13] | — |
| Bảng 2.9 | Số lượng và dạng biển số theo loại phương tiện [32] | — |
| Bảng 2.10 | Kích thước và tỷ lệ khung hình của các loại biển số [11] | — |
| Bảng 2.11 | Ngưỡng phân loại bố cục theo tỷ lệ khung hình — đề xuất của đồ án | — |
| Bảng 2.12 | Bố cục nội dung của biển hai dòng | — |
| Bảng 2.13 | Từ quy chuẩn pháp lý tới quyết định thiết kế | — |
| Bảng 2.14 | So sánh phương pháp xử lý ảnh cổ điển và phương pháp học sâu | — |
| Bảng 2.15 | Bốn nhánh kỹ thuật của hướng segmentation-free | — |
| Bảng 2.16 | So sánh khác biệt kiến trúc giữa các phiên bản YOLO gần đây | — |
| Bảng 2.17 | So sánh OCR văn bản tài liệu và OCR biển số xe | — |
| Bảng 2.18 | Tác động của việc resize về chiều cao cố định 48 px lên crop biển xe máy | — |
| Bảng 2.19 | Các phương pháp phân biệt biển một dòng và biển hai dòng | — |
| Bảng 2.20 | Các công trình quốc tế tiêu biểu về ALPR | — |
| Bảng 2.21 | Các công trình về nhận dạng biển số xe Việt Nam | — |
| Bảng 2.22 | So sánh các bộ dữ liệu chuẩn quốc tế | — |
| Bảng 2.23 | Sáu khoảng trống nghiên cứu và cách đồ án lấp | — |
| Bảng 3.1 | Mức bằng chứng của từng phép so sánh trong chương | — |
| Bảng 3.2 | So sánh các engine OCR ứng viên | — |
| Bảng 3.3 | PP-OCRv6_medium_rec so với PP-OCRv5_mobile_rec, đo trên 200 vùng cắt biển số của đồ án | — |
| Bảng 3.4 | Tổng hợp quyết định công nghệ nền tảng | — |
| Bảng 3.5 | So sánh baseline-416-v1.pt với best.pt — ba biến thay đổi đồng thời | — |
| Bảng 3.6 | Tổng hợp các quyết định công nghệ và căn cứ | — |
| Bảng 4.1 | Phân bố 34 yêu cầu chức năng theo nhóm và mức ưu tiên MoSCoW | — |
| Bảng 4.2 | Chỉ tiêu phi chức năng nhóm hiệu năng (NFR-P) | — |
| Bảng 4.3 | Chỉ tiêu phi chức năng nhóm độ chính xác (NFR-A) | — |
| Bảng 4.4 | Bốn ràng buộc kiến trúc và hệ quả trực tiếp | — |
| Bảng 4.5 | Trách nhiệm của từng tầng trong kiến trúc phân tầng | — |
| Bảng 4.6 | Các quyết định kiến trúc AD-01 … AD-08 | — |
| Bảng 4.7 | Đặc tả các endpoint REST API | — |
| Bảng 4.8 | Đặc tả trường của bảng detection_job | — |
| Bảng 4.9 | Đặc tả trường của bảng detection_history | — |
| Bảng 5.1 | Siêu tham số huấn luyện mô hình chính thức | — |
| Bảng 5.2 | Tiến triển chỉ số trên tập validation theo mốc epoch | — |
| Bảng 5.3 | So sánh bộ nhận dạng gốc và bản tinh chỉnh trên cùng ngữ liệu | — |
| Bảng 6.1 | Cấu hình phần cứng và hệ thống của máy thực nghiệm | — |
| Bảng 6.2 | Phiên bản thư viện tại thời điểm đo | — |
| Bảng 6.3 | So sánh ba phiên bản bộ dữ liệu | — |
| Bảng 6.4 | Số cặp ảnh gần trùng xuyên split theo ngưỡng Hamming | — |
| Bảng 6.5 | Phân bố nguồn dữ liệu giữa các split của phiên bản v3 | — |
| Bảng 6.6 | Kết quả phát hiện tổng thể trên tập test v3 | — |
| Bảng 6.7 | Kết quả phát hiện tách theo biển một dòng và hai dòng (NFR-A8) | — |
| Bảng 6.8 | Kết quả phát hiện tách theo dải kích thước hộp giới hạn | — |
| Bảng 6.9 | Độ chính xác mức ký tự (NFR-A4) | — |
| Bảng 6.10 | Độ chính xác chuỗi đầy đủ trước và sau hậu xử lý | — |
| Bảng 6.11 | Độ chính xác nhận dạng tách theo biển một dòng và hai dòng | — |
| Bảng 6.12 | Các cặp ký tự bị nhầm nhiều nhất, đối chiếu bảng luật hiện hành | — |
| Bảng 6.13 | Độ chính xác đầu-cuối toàn trình (NFR-A7) | — |
| Bảng 6.14 | So sánh A/B hai chiến lược đọc biển hai dòng | — |
| Bảng 6.15 | So sánh A/B bước cứu dòng trên trên hai mẫu độc lập | — |
| Bảng 6.16 | Trước và sau bước cứu dòng trên, đo trên toàn tập có nhãn chuỗi | — |
| Bảng 6.17 | Chi phí và lợi ích của từng bậc trong bậc thang thử-lại | — |
| Bảng 6.18 | Độ trễ đầu-cuối một ảnh, đối chiếu NFR-P1 | — |
| Bảng 6.19 | Phân rã ngân sách độ trễ theo từng bước | — |
| Bảng 6.20 | So sánh backend suy luận cho bộ phát hiện | — |
| Bảng 6.21 | Hiệu năng chế độ webcam và xử lý video | — |
| Bảng 6.22 | Chịu tải, bộ nhớ và độ tin cậy | — |
| Bảng 6.23 | Bỏ bước phát hiện chữ — hai ngữ liệu, hai kết luận ngược nhau | — |
| Bảng 6.24 | Đối chiếu toàn bộ chỉ tiêu phi chức năng | — |
| Bảng 6.25 | Tần suất từng loại lỗi | — |
| Bảng 7.1 | Đối chiếu chỉ tiêu cam kết ở Phase 0 với số đo trên best.pt | — |

---

## H. DANH MỤC TỪ VIẾT TẮT

> Tổng hợp từ toàn bộ tài liệu Phase 0 và Phase 1. Sắp xếp theo bảng chữ cái A–Z. Mỗi mục gồm ba cột: **từ viết tắt · dạng đầy đủ tiếng Anh · nghĩa tiếng Việt**.
>
> **Quy ước dùng thuật ngữ trong quyển đồ án:** giữ nguyên thuật ngữ tiếng Anh khi đó là cách dùng thông thường trong chuyên ngành (*bounding box*, *pipeline*, *dataset*, *confidence*, *mAP*, *backbone*, *checkpoint*…). Ở **lần xuất hiện đầu tiên** trong thân bài, viết dạng đầy đủ kèm từ viết tắt trong ngoặc, ví dụ: *"nhận dạng biển số xe tự động (Automatic License Plate Recognition — ALPR)"*; các lần sau chỉ dùng từ viết tắt.
>
> Một số mục là **từ viết tắt tiếng Việt** (CSDL, QCVN, TT) — với các mục này, cột giữa ghi thuật ngữ tiếng Anh tương đương để đối chiếu.

| Từ viết tắt | Dạng đầy đủ (tiếng Anh) | Nghĩa tiếng Việt |
|---|---|---|
| **AGPL** | Affero General Public License | Giấy phép công cộng Affero — giấy phép mã nguồn mở của Ultralytics YOLO |
| **ALPR** | Automatic License Plate Recognition | Nhận dạng biển số xe tự động |
| **ANPR** | Automatic Number Plate Recognition | Nhận dạng biển số xe tự động — tên gọi khác của ALPR, phổ biến ở châu Âu |
| **API** | Application Programming Interface | Giao diện lập trình ứng dụng |
| **AOLP** | Application-Oriented License Plate (dataset) | Bộ dữ liệu biển số theo hướng ứng dụng (Đài Loan) |
| **AR** | Aspect Ratio | Tỷ lệ khung hình — tỷ số chiều rộng trên chiều cao |
| **AVX-512** | Advanced Vector Extensions 512-bit | Tập lệnh vector 512 bit của bộ xử lý Intel |
| **BiLSTM** | Bidirectional Long Short-Term Memory | Mạng LSTM hai chiều |
| **BOM** | Byte Order Mark | Dấu thứ tự byte — đặt ở đầu tệp UTF-8 để tránh lỗi hiển thị tiếng Việt |
| **CCPD** | Chinese City Parking Dataset | Bộ dữ liệu biển số bãi đỗ xe Trung Quốc |
| **CER** | Character Error Rate | Tỉ lệ lỗi ở mức ký tự |
| **CLAHE** | Contrast Limited Adaptive Histogram Equalization | Cân bằng lược đồ xám thích nghi có giới hạn tương phản |
| **CNN** | Convolutional Neural Network | Mạng nơ-ron tích chập |
| **COCO** | Common Objects in Context | Bộ dữ liệu chuẩn cho bài toán phát hiện đối tượng |
| **CORS** | Cross-Origin Resource Sharing | Cơ chế chia sẻ tài nguyên giữa các nguồn khác nhau |
| **CPU** | Central Processing Unit | Bộ xử lý trung tâm |
| **CRAFT** | Character Region Awareness for Text Detection | Mô hình phát hiện văn bản dựa trên vùng ký tự — dùng trong EasyOCR |
| **CRNN** | Convolutional Recurrent Neural Network | Mạng tích chập kết hợp hồi quy — kiến trúc nền của nhiều bộ nhận dạng ký tự |
| **CRUD** | Create, Read, Update, Delete | Tạo, đọc, cập nhật, xoá — bốn thao tác cơ bản trên dữ liệu |
| **CSDL** | Database | Cơ sở dữ liệu *(viết tắt tiếng Việt)* |
| **CSV** | Comma-Separated Values | Định dạng tệp văn bản phân tách bằng dấu phẩy |
| **CTC** | Connectionist Temporal Classification | Hàm mất mát cho bài toán chuỗi không cần căn chỉnh trước giữa đầu vào và nhãn |
| **CUDA** | Compute Unified Device Architecture | Nền tảng tính toán song song trên GPU của NVIDIA |
| **DBNet** | Differentiable Binarization Network | Mạng phát hiện văn bản dùng nhị phân hoá khả vi — dùng trong PP-OCR |
| **DI** | Dependency Injection | Tiêm phụ thuộc — kỹ thuật cấp phát phụ thuộc từ bên ngoài |
| **DTO** | Data Transfer Object | Đối tượng truyền dữ liệu giữa các tầng |
| **E2E** | End-to-End | Toàn trình — từ đầu vào đến kết quả cuối cùng |
| **ER** | Entity–Relationship | Thực thể – liên kết, mô hình thiết kế cơ sở dữ liệu |
| **F1** | F1-score | Trung bình điều hoà của precision và recall |
| **FP16 / FP32** | 16-bit / 32-bit Floating Point | Số thực dấu phẩy động 16 bit / 32 bit |
| **FPN** | Feature Pyramid Network | Mạng kim tự tháp đặc trưng |
| **FPS** | Frames Per Second | Số khung hình xử lý được trong một giây |
| **FR** | Functional Requirement | Yêu cầu chức năng |
| **GFLOPs** | Giga Floating Point Operations | Tỉ phép tính dấu phẩy động — thước đo khối lượng tính toán của mô hình |
| **GPU** | Graphics Processing Unit | Bộ xử lý đồ hoạ |
| **HTTP** | HyperText Transfer Protocol | Giao thức truyền siêu văn bản |
| **INT8** | 8-bit Integer | Số nguyên 8 bit — định dạng lượng tử hoá mô hình |
| **IoU** | Intersection over Union | Tỉ lệ chồng lấn giữa hai bounding box |
| **JSON** | JavaScript Object Notation | Định dạng trao đổi dữ liệu dạng văn bản |
| **LSTM** | Long Short-Term Memory | Mạng nơ-ron bộ nhớ dài – ngắn hạn |
| **mAP** | mean Average Precision | Độ chính xác trung bình — chỉ số chuẩn của bài toán phát hiện đối tượng |
| **MAPR** | Multimedia Analysis and Pattern Recognition | Hội nghị về phân tích đa phương tiện và nhận dạng mẫu |
| **MoSCoW** | Must have / Should have / Could have / Won't have | Phương pháp xếp mức ưu tiên yêu cầu phần mềm |
| **NFR** | Non-Functional Requirement | Yêu cầu phi chức năng |
| **NMS** | Non-Maximum Suppression | Loại bỏ các bounding box trùng lặp không cực đại |
| **OCR** | Optical Character Recognition | Nhận dạng ký tự quang học |
| **ONNX** | Open Neural Network Exchange | Định dạng trao đổi mô hình học sâu mở, độc lập framework |
| **OpenAPI** | OpenAPI Specification | Đặc tả mô tả REST API, cơ sở để sinh tài liệu Swagger |
| **ORM** | Object–Relational Mapping | Ánh xạ đối tượng – quan hệ giữa mã nguồn và cơ sở dữ liệu |
| **p95** | 95th percentile | Phân vị thứ 95 — giá trị mà 95% số phép đo nằm dưới |
| **PP-OCR** | PaddlePaddle Optical Character Recognition | Bộ công cụ OCR của PaddlePaddle (PaddleOCR) |
| **QCVN** | National Technical Regulation | Quy chuẩn kỹ thuật quốc gia *(viết tắt tiếng Việt)* |
| **REST** | Representational State Transfer | Kiến trúc dịch vụ web dựa trên tài nguyên |
| **RSS** | Resident Set Size | Dung lượng bộ nhớ thường trú của tiến trình |
| **SOTA** | State of the Art | Kết quả tốt nhất được công bố tại thời điểm hiện tại |
| **SPA** | Single Page Application | Ứng dụng web một trang |
| **SPPF** | Spatial Pyramid Pooling – Fast | Khối gộp kim tự tháp không gian phiên bản nhanh, dùng trong YOLO |
| **SQL** | Structured Query Language | Ngôn ngữ truy vấn có cấu trúc |
| **SRS** | Software Requirements Specification | Đặc tả yêu cầu phần mềm |
| **SVTR** | Scene Text Recognition with a Single Visual Model | Mô hình nhận dạng văn bản cảnh dùng một mạng thị giác duy nhất |
| **TT** | Circular | Thông tư — văn bản quy phạm pháp luật *(viết tắt tiếng Việt)* |
| **UUID** | Universally Unique Identifier | Định danh duy nhất toàn cục — dùng đặt tên tệp để chống path traversal |
| **VLM** | Vision–Language Model | Mô hình kết hợp thị giác và ngôn ngữ |
| **VNNI** | Vector Neural Network Instructions | Tập lệnh tăng tốc mạng nơ-ron của Intel, điều kiện để lượng tử hoá INT8 có lợi |
| **WCAG** | Web Content Accessibility Guidelines | Hướng dẫn về khả năng tiếp cận nội dung web |
| **WER** | Word Error Rate | Tỉ lệ lỗi ở mức từ |
| **WPOD** | Warped Planar Object Detection (Network) | Mạng phát hiện đối tượng phẳng bị biến dạng, dùng để nắn thẳng biển số |
| **YOLO** | You Only Look Once | Họ mô hình phát hiện đối tượng một giai đoạn |

---

## I. TÓM TẮT ĐỒ ÁN

<div align="center">

**TÓM TẮT ĐỒ ÁN**

</div>

Nhận dạng biển số xe tự động (ALPR) là bài toán nền tảng của bãi đỗ xe thông minh, thu phí không dừng và giám sát giao thông. Tại Việt Nam, biển số hai dòng chiếm tỷ lệ lớn do mật độ xe máy cao, trong khi đa số bộ dữ liệu quốc tế chỉ có biển một dòng, khiến các mô hình huấn luyện trên dữ liệu nước ngoài không áp dụng trực tiếp được. Khác biệt này đã được đo lường: trên bộ RodoSol-ALPR của Brazil, hệ thống OpenALPR đạt 94,3% với ô tô biển một dòng nhưng chỉ 45,7% với xe máy biển hai dòng [1]<!-- laroca_2022_crossdataset -->.

Đồ án xây dựng một hệ thống ALPR hoàn chỉnh cho biển số xe Việt Nam theo hướng tiếp cận hai giai đoạn: phát hiện vùng biển số bằng YOLO11, nhận dạng ký tự bằng PaddleOCR, và hậu xử lý bằng bộ luật chuẩn hoá theo quy chuẩn hiện hành. Hệ thống hỗ trợ cả biển một dòng và hai dòng, nhận đầu vào là ảnh, video hoặc khung hình thời gian thực gửi qua API (endpoint `POST /api/detect/frame`), và suy luận hoàn toàn trên CPU.

Đóng góp chính là bộ luật hậu xử lý **ràng buộc theo vị trí ký tự**, xây dựng trên Thông tư 79/2024/TT-BCA [2]<!-- bocongan_2024_tt79 --> và QCVN 08:2024/BCA [3]<!-- bocongan_2024_qcvn08 -->: mã tỉnh thuộc 81 giá trị hợp lệ, chữ cái sê-ri thứ nhất và thứ hai thuộc hai tập ký tự khác nhau. Cách tiếp cận này khắc phục hạn chế của các hệ thống áp một danh sách ký tự phẳng cho toàn chuỗi.

Về mặt kỹ nghệ, đồ án cài đặt kiến trúc phân tầng tách biệt tầng AI khỏi tầng API, gồm backend FastAPI, giao diện web React và đóng gói Docker.

Trên tập kiểm tra của split v3 (1.514 ảnh, đã khử trùng lặp giữa các tập), bộ phát hiện YOLO11n đạt mAP@0.5 = 0,9829 và mAP@0.5:0.95 = 0,7834 (precision 0,9837; recall 0,9714). Khối nhận dạng đạt độ chính xác mức ký tự (1 − CER) 0,9454; độ chính xác toàn chuỗi tăng từ 0,6373 lên 0,7512 nhờ bộ luật hậu xử lý (sửa đúng 319 biển, không làm hỏng biển nào), và độ chính xác end-to-end đạt 0,5552. Khoảng cách lớn nhất nằm ở layout: biển một dòng đạt 0,9541 còn biển hai dòng chỉ đạt 0,6996 — chênh 25,45 điểm phần trăm, trong khi biển hai dòng chiếm 79,8% tập đánh giá. Độ trễ xử lý một ảnh ở phân vị 95 là 1.143,10 ms trên CPU (trung vị 405,77 ms), đạt ngưỡng tối thiểu 1.500 ms nhưng chưa đạt mục tiêu 800 ms — cái giá đã định lượng của bậc thang thử-lại dành cho biển nghiêng, méo. Chi tiết và phân tích lỗi được trình bày ở Chương 5.

**Từ khoá:** nhận dạng biển số xe, biển số Việt Nam, YOLO11, PaddleOCR, biển số hai dòng, hậu xử lý theo vị trí, suy luận trên CPU.

---

## J. ABSTRACT

<div align="center">

**ABSTRACT**

</div>

Automatic License Plate Recognition (ALPR) underpins smart parking systems, electronic toll collection, and traffic surveillance. In Vietnam, the task presents characteristics that prevent the direct reuse of models trained on foreign data: two-line plates account for a large share of vehicles because of the country's high motorcycle density, whereas most international datasets contain single-line plates only. The severity of this gap has been quantified: on the Brazilian RodoSol-ALPR dataset, the OpenALPR system reached 94.3% on single-line car plates but only 45.7% on two-line motorcycle plates — a gap of 48.6 percentage points [1]<!-- laroca_2022_crossdataset -->.

This thesis develops a complete ALPR system for Vietnamese license plates following a two-stage approach: plate region detection with a YOLO11 model, character recognition with PaddleOCR, and post-processing through a normalization rule set derived from the applicable national regulations. The system supports both single-line and two-line plates, accepts images, video files, or real-time frames submitted through the API (the `POST /api/detect/frame` endpoint) as input, and performs inference entirely on CPU.

The principal contribution is a **position-constrained post-processing rule set** grounded in Circular 79/2024/TT-BCA [2]<!-- bocongan_2024_tt79 --> and the national technical regulation QCVN 08:2024/BCA [3]<!-- bocongan_2024_qcvn08 -->: the province code is restricted to 81 valid values, and the first and second serial letters are drawn from two different character sets. This design corrects a limitation of systems that apply a single flat character whitelist across the entire plate string.

From a software engineering perspective, the thesis implements a layered architecture that fully decouples the AI layer from the API layer, comprising a FastAPI backend, a React web interface, and Docker packaging.

On the held-out test split (1,514 images, de-duplicated across splits), the YOLO11n detector reaches mAP@0.5 = 0.9829 and mAP@0.5:0.95 = 0.7834 (precision 0.9837, recall 0.9714). The recognition stage attains a character-level accuracy (1 − CER) of 0.8734; full-string accuracy rises from 0.6098 to 0.6555 under the post-processing rule set (128 plates corrected, none corrupted), and end-to-end accuracy reaches 0.5227. The dominant gap is layout-related: single-line plates score 0.9489 whereas two-line plates score only 0.5810 — a 36.79 percentage-point gap — while two-line plates constitute 79.8% of the evaluation set. The 95th-percentile latency for a single image is 731.15 ms on CPU, meeting the 800 ms target. Chapter 5 reports the full results and error analysis.

**Keywords:** license plate recognition, Vietnamese license plates, YOLO11, PaddleOCR, two-line plates, position-constrained post-processing, CPU inference.
