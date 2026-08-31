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

<!--Trình bày theo định dạng bìa chuẩn của đồ án tốt nghiệp đại học Việt Nam. Khi kết xuất sang PDF/Word, toàn bộ khối dưới đây căn giữa trang, không đánh số trang. Bìa cứng (bìa ngoài) và bìa lót (bìa trong) có nội dung giống nhau; bìa lót bổ sung dòng giảng viên hướng dẫn nếu quy chế của khoa yêu cầu.
-->

<div align="center">

**ĐẠI HỌC QUỐC GIA TP. HỒ CHÍ MINH**

**TRƯỜNG ĐẠI HỌC CÔNG NGHỆ THÔNG TIN**

<br/>

_<!-- chèn logo Trường Đại học Công nghệ Thông tin khi kết xuất bản in -->_

<br/><br/>

# ĐỒ ÁN TỐT NGHIỆP ĐẠI HỌC

<br/>

### Đề tài:

# XÂY DỰNG HỆ THỐNG NHẬN DIỆN BIỂN SỐ XE BẰNG TRÍ TUỆ NHÂN TẠO

_Developing an AI-based vehicle license plate recognition system_

<br/><br/>

|                           |                                          |
| ------------------------: | :--------------------------------------- |
|                **Ngành:** | Trí tuệ nhân tạo                         |
|         **Chuyên ngành:** | Trí tuệ nhân tạo                         |
|  **Sinh viên thực hiện:** | **Phạm Công Thành** — MSSV **25410013**  |
|                           | **Nguyễn Minh Hiếu** — MSSV **25410007** |
|                  **Lớp:** | AI503.F3.LT.TTNT                         |
|                 **Khoá:** | 2025                                     |
| **Giảng viên hướng dẫn:** | ThS. Cáp Phạm Đình Thăng                 |

<br/><br/>

**TP. Hồ Chí Minh, tháng 9 năm 2026**

</div>

---

## B. LỜI CAM ĐOAN

Nhóm thực hiện xin cam đoan đồ án tốt nghiệp **"Xây dựng hệ thống nhận diện biển số xe bằng trí tuệ nhân tạo"** là công trình do chính nhóm thực hiện dưới sự hướng dẫn của ThS. Cáp Phạm Đình Thăng.

Toàn bộ số liệu thực nghiệm trình bày trong quyển do nhóm tự đo trên máy và cấu hình phần cứng nêu tại mục 5.2; mọi kết quả trích từ công trình của tác giả khác đều được ghi rõ nguồn trong danh mục tài liệu tham khảo, kèm tên bộ dữ liệu và điều kiện đo gốc. Các mô hình, thư viện và bộ dữ liệu công khai được sử dụng lại đều ghi công đầy đủ tại mục 1.4 và Phụ lục II.

Nhóm thực hiện cam đoan không sao chép nội dung từ bất kỳ công trình nào mà không trích dẫn, và chịu hoàn toàn trách nhiệm về tính trung thực của các số liệu công bố trong quyển.

<div align="right">

TP. Hồ Chí Minh, tháng 9 năm 2026

**Nhóm thực hiện**

«Ký và ghi rõ họ tên»

</div>

---

## C. LỜI CẢM ƠN

Nhóm thực hiện xin gửi lời cảm ơn chân thành tới **ThS. Cáp Phạm Đình Thăng** — giảng viên hướng dẫn — vì những góp ý đã định hình cách đặt vấn đề và giao thức đánh giá của đề tài, đặc biệt là yêu cầu mọi con số công bố phải kèm điều kiện đo.

Nhóm cũng xin cảm ơn quý thầy cô Trường Đại học Công nghệ Thông tin – Đại học Quốc gia TP. Hồ Chí Minh đã trang bị nền tảng kiến thức để thực hiện đề tài, và cảm ơn các tác giả đã công khai bộ dữ liệu biển số xe Việt Nam — không có phần dữ liệu ấy, đề tài không thể tiến hành.

---

## E. MỤC LỤC

<!-- Sinh tự động bằng scripts/gen_front_matter_lists.py từ chính các tệp
     chương. Không sửa tay — chạy lại script sau mỗi lần đổi cấu trúc.
     Số trang do Word điền khi xuất .docx. -->

```{=openxml}
<w:p><w:r><w:fldChar w:fldCharType="begin" w:dirty="true"/></w:r><w:r><w:instrText xml:space="preserve"> TOC \o "1-2" \h \z \u </w:instrText></w:r><w:r><w:fldChar w:fldCharType="separate"/></w:r><w:r><w:t>Mở tệp trong Word rồi bấm Ctrl+A, F9 để cập nhật mục lục.</w:t></w:r><w:r><w:fldChar w:fldCharType="end"/></w:r></w:p>
```

<!-- Bản đối chiếu (không in ra):

     CHƯƠNG 1. GIỚI THIỆU
         1.1. Đặt vấn đề
         1.2. Mục tiêu đề tài
         1.3. Đối tượng và phạm vi nghiên cứu
         1.4. Phương pháp nghiên cứu
         1.5. Đóng góp của đề tài

     CHƯƠNG 2. CƠ SỞ LÝ THUYẾT
         2.1. Phạm vi và bố cục cơ sở lý thuyết
         2.2. Quy chuẩn biển số xe Việt Nam
         2.3. Cơ sở lý thuyết về phát hiện đối tượng
         2.4. Cơ sở lý thuyết về nhận dạng ký tự
         2.5. Các công trình liên quan

     CHƯƠNG 3. KHẢO SÁT CÔNG NGHỆ VÀ LỰA CHỌN MÔ HÌNH
         3.1. Phương pháp khảo sát và tiêu chí lựa chọn
         3.2. Mô hình phát hiện: YOLO11
         3.3. Bộ nhận dạng ký tự
         3.4. Nền tảng suy luận trên CPU: ONNX Runtime
         3.5. Các lựa chọn công nghệ nền tảng khác
         3.6. Độ phân giải đầu vào: 640 thay vì 416

     CHƯƠNG 4. THIẾT KẾ VÀ CÀI ĐẶT HỆ THỐNG
         4.1. Phân tích yêu cầu
         4.2. Kiến trúc hệ thống
         4.3. Môi trường và công cụ phát triển
         4.4. Xây dựng bộ dữ liệu
         4.5. Huấn luyện mô hình
         4.6. Tầng AI — thiết kế và cài đặt
         4.7. Máy chủ và cơ sở dữ liệu
         4.8. Giao diện người dùng
         4.9. Triển khai bằng Docker

     CHƯƠNG 5. THỰC NGHIỆM VÀ ĐÁNH GIÁ
         5.1. Mục tiêu và phương pháp đánh giá
         5.2.---
         5.2. Môi trường thực nghiệm
         5.3. Bộ dữ liệu thực nghiệm
         5.4. Đánh giá bộ phát hiện biển số
         5.5. Đánh giá khối OCR và hậu xử lý
         5.6. Đánh giá hiệu năng
         5.7. Đối chiếu toàn bộ chỉ tiêu phi chức năng
         5.8. Phân tích lỗi
         5.9. Bàn luận

     CHƯƠNG 6. KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN
         6.1. Kết quả đạt được
         6.2. Hạn chế
         6.3. Hướng phát triển
         6.4. Kết luận chung
-->

---

## F. DANH MỤC HÌNH VẼ

<!-- Sinh tự động bằng scripts/gen_front_matter_lists.py từ chính các tệp
     chương. Không sửa tay — chạy lại script sau mỗi lần đổi cấu trúc.
     Số trang do Word điền khi xuất .docx. -->
<!-- Quy ước: Hình <chương>.<thứ tự>. Chú thích đặt DƯỚI hình, căn giữa.
     Hình lấy/phỏng theo nguồn khác bắt buộc ghi nguồn kèm [n]. -->

| Ký hiệu | Tên hình | Trang |
|---|---|:---:|
| Hình 1.1 | ** Ranh giới hệ thống — phần bên trong là hệ thống bàn giao, Colab/Kaggle nằm ngoài | — |
| Hình 2.1 | * Kiến trúc tổng quát backbone – neck – head của YOLO11 (theo [13], [9]) | — |
| Hình 2.2 | ** Kiến trúc CRNN và cách CTC gộp chuỗi thô | — |
| Hình 2.3 | ** Cơ chế sụp đổ của CTC trên ảnh văn bản hai dòng | — |
| Hình 4.1 | ** Sơ đồ use case — hai tác nhân và bốn use case | — |
| Hình 4.2 | ** Kiến trúc phân tầng năm tầng và chiều phụ thuộc | — |
| Hình 4.3 | ** Luồng xử lý của đường ống AI, các khối tô đỏ là nhánh biển hai dòng | — |
| Hình 4.4 | ** Đường ống sáu bước xây dựng bộ dữ liệu | — |
| Hình 4.5 | ** Đường cong huấn luyện theo epoch — ba hàm mất mát và bốn chỉ số trên tập kiểm định | — |
| Hình 4.6 | ** Ba lớp trừu tượng và cài đặt tương ứng — bằng chứng cài đặt cho NFR-M5 | — |
| Hình 4.7 | ** Thuật toán chuẩn hoá chuỗi biển số theo bộ luật ràng buộc vị trí | — |
| Hình 5.1 | ** Giao thức đo và ràng buộc phụ thuộc giữa các bước đánh giá | — |
| Hình 5.2 | ** Sáu lần đo NFR-P2 trong các điều kiện máy khác nhau | — |
| Hình 5.3 | ** Một ca khử trùng lặp thật, cắt trực tiếp từ video demo | — |

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
| Bảng 2.1 | So sánh khác biệt kiến trúc giữa các phiên bản YOLO gần đây | — |
| Bảng 2.2 | So sánh OCR văn bản tài liệu và OCR biển số xe | — |
| Bảng 2.3 | Sáu khoảng trống nghiên cứu và cách nhóm thực hiện lấp | — |
| Bảng 3.1 | PP-OCRv6_medium_rec so với PP-OCRv5_mobile_rec, đo trên 200 vùng cắt biển số của đồ án | — |
| Bảng 3.2 | So sánh ba bộ nhận dạng ký tự trên 2.801 biển số Việt Nam (567 một dòng, 2.234 hai dòng) | — |
| Bảng 4.1 | Bốn ràng buộc kiến trúc và cách kiểm chứng từng ràng buộc | — |
| Bảng 4.2 | Tám quyết định kiến trúc — mỗi dòng kèm đánh đổi phải chấp nhận | — |
| Bảng 4.3 | Đóng góp của từng bộ dữ liệu trước và sau khử trùng lặp | — |
| Bảng 4.4 | Tiến triển chỉ số trên tập validation theo mốc epoch | — |
| Bảng 5.1 | Ba phiên bản bộ dữ liệu và số cặp ảnh gần trùng xuyên tập con theo ngưỡng Hamming | — |
| Bảng 5.2 | Kết quả phát hiện tách theo biển một dòng và hai dòng (NFR-A8) | — |
| Bảng 5.3 | Độ chính xác OCR trước và sau hậu xử lý, trên 2.801 biển có nhãn chuỗi | — |
| Bảng 5.4 | Độ chính xác nhận dạng tách theo biển một dòng và hai dòng | — |
| Bảng 5.5 | NFR-A7 ở mức ảnh toàn cảnh — ước lượng phân tầng trên 1.606 khung biển | — |
| Bảng 5.6 | Chi phí và lợi ích của từng bậc trong thang thử lại | — |
| Bảng 5.7 | Độ trễ đầu cuối một ảnh, đối chiếu NFR-P1 | — |
| Bảng 5.8 | Phân rã ngân sách độ trễ theo từng bước | — |
| Bảng 5.9 | Các chỉ tiêu hiệu năng ngoài đường xử lý ảnh | — |
| Bảng 5.10 | Đối chiếu chỉ tiêu phi chức năng, gom theo nhóm | — |
| Bảng 5.11 | Tần suất từng loại lỗi trên 2.801 biển có nhãn chuỗi, cấu hình giao hàng | — |
| Bảng 5.12 | Đối chiếu kết quả của đồ án với các con số đã công bố | — |
| Bảng 5.13 | Tám mối đe doạ đến tính hợp lệ của kết quả | — |
| Bảng 6.1 | Đối chiếu chỉ tiêu đặt ra ở giai đoạn phân tích yêu cầu với số đo trên models/best.pt | — |
| Bảng 6.2 | Mười hạn chế của đồ án | — |
| Bảng 6.3 | Mười một hướng phát triển, xếp theo mức tác động | — |

---

## D. TÓM TẮT ĐỒ ÁN

<div align="center">

**TÓM TẮT ĐỒ ÁN**

</div>

Nhận dạng biển số xe tự động (ALPR) là bài toán nền tảng của bãi đỗ xe thông minh, thu phí không dừng và giám sát giao thông. Tại Việt Nam, biển số hai dòng chiếm tỷ lệ lớn do mật độ xe máy cao, trong khi đa số bộ dữ liệu quốc tế chỉ có biển một dòng, khiến các mô hình huấn luyện trên dữ liệu nước ngoài không áp dụng trực tiếp được. Khác biệt này đã được đo lường: trên bộ RodoSol-ALPR của Brazil, hệ thống OpenALPR đạt 94,3% với ô tô biển một dòng nhưng chỉ 45,7% với xe máy biển hai dòng [1]<!-- laroca_2022_crossdataset -->.

Đồ án xây dựng một hệ thống ALPR hoàn chỉnh cho biển số xe Việt Nam theo hướng tiếp cận hai giai đoạn: phát hiện vùng biển số bằng YOLO11, nhận dạng ký tự bằng PaddleOCR, và hậu xử lý bằng bộ luật chuẩn hoá theo quy chuẩn hiện hành. Hệ thống hỗ trợ cả biển một dòng và hai dòng, nhận đầu vào là ảnh, video hoặc khung hình thời gian thực gửi qua API (endpoint `POST /api/detect/frame`), và suy luận hoàn toàn trên CPU.

Đóng góp chính là bộ luật hậu xử lý **ràng buộc theo vị trí ký tự**, xây dựng trên Thông tư 79/2024/TT-BCA [2]<!-- bocongan_2024_tt79 --> và QCVN 08:2024/BCA [3]<!-- bocongan_2024_qcvn08 -->: mã tỉnh thuộc 81 giá trị hợp lệ, chữ cái sê-ri thứ nhất và thứ hai thuộc hai tập ký tự khác nhau. Cách tiếp cận này khắc phục hạn chế của các hệ thống áp một danh sách ký tự phẳng cho toàn chuỗi.

Về mặt kỹ nghệ, đồ án cài đặt kiến trúc phân tầng tách biệt tầng AI khỏi tầng API, gồm backend FastAPI, giao diện web React và đóng gói Docker.

Trên tập kiểm tra của split v3 (1.514 ảnh, đã khử trùng lặp giữa các tập), bộ phát hiện YOLO11n đạt mAP@0.5 = 0,9829 và mAP@0.5:0.95 = 0,7834 (precision 0,9837; recall 0,9714). Khối nhận dạng đạt độ chính xác mức ký tự (1 − CER) 0,9483; độ chính xác toàn chuỗi tăng từ 0,6373 lên 0,7701 nhờ bộ luật hậu xử lý (sửa đúng 372 biển, không làm hỏng biển nào). Chỉ số end-to-end đo ở **mức ảnh toàn cảnh** đạt **0,563** (khoảng tin cậy 95% [0,520 ; 0,607]), ước lượng phân tầng trên 1.606 khung biển của 1.514 ảnh hiện trường — chưa đạt ngưỡng 0,82, và phải đọc kèm hạn chế nhãn do mô hình ngôn ngữ-thị giác sinh chứ không phải người gán. Khoảng cách lớn nhất nằm ở layout: biển một dòng đạt 0,9541 còn biển hai dòng chỉ đạt 0,7234 — chênh 23,07 điểm phần trăm, trong khi biển hai dòng chiếm 79,8% tập đánh giá. Độ trễ xử lý một ảnh ở phân vị 95 là 509,76 ms trên CPU (trung vị 150,07 ms), đạt cả ngưỡng tối thiểu 1.500 ms lẫn mục tiêu 800 ms sau đợt tối ưu tầng suy luận. Chi tiết và phân tích lỗi được trình bày ở Chương 5.

**Từ khoá:** nhận dạng biển số xe, biển số Việt Nam, YOLO11, PaddleOCR, biển số hai dòng, hậu xử lý theo vị trí, suy luận trên CPU.
