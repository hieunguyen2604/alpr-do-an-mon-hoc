# Phần đầu quyển đồ án (Front Matter)

**Đề tài:** Xây dựng hệ thống nhận dạng biển số xe Việt Nam ứng dụng Trí tuệ nhân tạo
*(Developing an AI-based Vietnamese License Plate Recognition System)*

| Mục | Nội dung |
|---|---|
| Mã tài liệu | `THESIS-FRONT-v1.0` |
| Giai đoạn | Phase 9 — Documentation |
| Ngày lập | 2026-07-19 |
| Trạng thái | Danh mục từ viết tắt và hai abstract: **đã hoàn chỉnh**. Bìa, lời cam đoan, lời cảm ơn: **mẫu, chờ điền thông tin cá nhân**. Mục lục, danh mục hình, danh mục bảng: **placeholder, sinh tự động khi ghép** |

> **Quy ước ký hiệu trong tài liệu này:** mọi chỗ đặt trong dấu `«…»` là **chỗ trống phải điền** thông tin thật (tên trường, khoa, sinh viên, giảng viên hướng dẫn, mã số sinh viên…). Không được để nguyên `«…»` trong bản nộp.

---

## A. TRANG BÌA

> Trình bày theo định dạng bìa chuẩn của đồ án tốt nghiệp đại học Việt Nam. Khi kết xuất sang PDF/Word, toàn bộ khối dưới đây căn giữa trang, không đánh số trang. Bìa cứng (bìa ngoài) và bìa lót (bìa trong) có nội dung giống nhau; bìa lót bổ sung dòng giảng viên hướng dẫn nếu quy chế của khoa yêu cầu.

<div align="center">

**BỘ GIÁO DỤC VÀ ĐÀO TẠO**

**«TÊN TRƯỜNG ĐẠI HỌC»**

**«TÊN KHOA / VIỆN»**

<br/>

*«Logo trường»*

<br/><br/>

# ĐỒ ÁN TỐT NGHIỆP ĐẠI HỌC

<br/>

### Đề tài:

# XÂY DỰNG HỆ THỐNG NHẬN DẠNG BIỂN SỐ XE VIỆT NAM ỨNG DỤNG TRÍ TUỆ NHÂN TẠO

*Developing an AI-based Vietnamese License Plate Recognition System*

<br/><br/>

| | |
|---:|:---|
| **Ngành:** | «Tên ngành — SV bổ sung» |
| **Chuyên ngành:** | Trí tuệ nhân tạo |
| **Mã ngành:** | «Mã ngành — SV bổ sung» |
| **Sinh viên thực hiện:** | **Phạm Công Thành** — MSSV **25410013** |
| | **Nguyễn Minh Hiếu** — MSSV **25410007** |
| **Lớp:** | AI503.F3.LT.TTNT |
| **Khoá:** | «Khoá — SV bổ sung» |
| **Giảng viên hướng dẫn:** | ThS. Cáp Phạm Đình Thăng |

<br/><br/>

**«Địa danh — SV bổ sung», tháng 7 năm 2026**

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

Chúng tôi xin cam đoan đồ án tốt nghiệp với đề tài **"Xây dựng hệ thống nhận dạng biển số xe Việt Nam ứng dụng Trí tuệ nhân tạo"** là công trình nghiên cứu của nhóm chúng tôi, được thực hiện dưới sự hướng dẫn khoa học của **ThS. Cáp Phạm Đình Thăng**.

Các nội dung nghiên cứu, kết quả thực nghiệm và số liệu trình bày trong đồ án là trung thực và do chính chúng tôi thực hiện. Các thư viện, mô hình và bộ dữ liệu mã nguồn mở được sử dụng lại đều được nêu rõ nguồn gốc, phiên bản và điều kiện giấy phép tại các chương tương ứng.

Mọi tài liệu tham khảo, số liệu, bảng biểu và hình vẽ được trích dẫn từ công trình của tác giả khác đều được ghi rõ nguồn trong phần Tài liệu tham khảo theo đúng quy định về trích dẫn học thuật. Các văn bản quy phạm pháp luật được viện dẫn trong đồ án đã được đối chiếu với văn bản gốc và kiểm tra hiệu lực tại thời điểm thực hiện.

Chúng tôi xin cam đoan không sao chép nguyên văn hoặc sử dụng kết quả của người khác mà không ghi nguồn. Chúng tôi xin chịu hoàn toàn trách nhiệm trước Nhà trường và Hội đồng đánh giá về lời cam đoan này.

<div align="right">

*«Địa danh — SV bổ sung», ngày «DD» tháng 7 năm 2026*

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

Chúng tôi xin chân thành cảm ơn quý thầy cô «Khoa / Viện — SV bổ sung», «Trường Đại học — SV bổ sung» đã truyền đạt cho chúng tôi nền tảng kiến thức trong suốt những năm học vừa qua — đó là cơ sở để chúng tôi tiếp cận và giải quyết bài toán của đồ án này.

Chúng tôi cũng xin gửi lời cảm ơn tới cộng đồng mã nguồn mở, các nhóm nghiên cứu đã công bố công trình, mã nguồn và bộ dữ liệu về nhận dạng biển số xe. Đồ án này được xây dựng trên nền tảng những đóng góp đó.

Cuối cùng, chúng tôi xin cảm ơn gia đình và bạn bè đã luôn động viên, ủng hộ trong suốt quá trình học tập và thực hiện đồ án.

Do giới hạn về thời gian, phần cứng và kinh nghiệm, đồ án chắc chắn còn nhiều thiếu sót. Chúng tôi rất mong nhận được ý kiến đóng góp của quý thầy cô và Hội đồng để hoàn thiện hơn.

Chúng tôi xin chân thành cảm ơn!

<div align="right">

*«Địa danh — SV bổ sung», ngày «DD» tháng 7 năm 2026*

**Nhóm sinh viên thực hiện**

<br/>

**Phạm Công Thành**  ·  **Nguyễn Minh Hiếu**

</div>

---

## E. MỤC LỤC

> **Placeholder — sinh tự động khi ghép quyển.** Không gõ tay. Cấu trúc dưới đây chỉ để kiểm tra rằng đánh số mục ở các chương khớp với đề cương `00-thesis-outline.md`. Xem hướng dẫn sinh mục lục tại `THESIS-README.md` §5.

```
LỜI CAM ĐOAN .............................................................. i
LỜI CẢM ƠN ................................................................ ii
MỤC LỤC ................................................................... iii
DANH MỤC HÌNH VẼ .......................................................... vi
DANH MỤC BẢNG BIỂU ........................................................ viii
DANH MỤC TỪ VIẾT TẮT ...................................................... x
TÓM TẮT ĐỒ ÁN ............................................................. xii
ABSTRACT .................................................................. xiii

CHƯƠNG 1. MỞ ĐẦU .......................................................... 1
    1.1. Đặt vấn đề
    1.2. Mục tiêu đề tài
    1.3. Đối tượng và phạm vi nghiên cứu
    1.4. Phương pháp nghiên cứu
    1.5. Đóng góp của đồ án
    1.6. Cấu trúc quyển đồ án

CHƯƠNG 2. TỔNG QUAN VÀ CƠ SỞ LÝ THUYẾT ....................................
    2.1. Tổng quan bài toán ALPR
    2.2. Phân loại các hướng tiếp cận
    2.3. Các công trình tiêu biểu
    2.4. Cơ sở lý thuyết phát hiện đối tượng
    2.5. Cơ sở lý thuyết nhận dạng ký tự quang học
    2.6. Quy chuẩn biển số xe Việt Nam
    2.7. Các chỉ số đánh giá
    2.8. Khảo sát bộ dữ liệu
    2.9. Công nghệ nền tảng
    2.10. Tóm tắt chương

CHƯƠNG 3. PHÂN TÍCH VÀ THIẾT KẾ HỆ THỐNG ..................................
    3.1. Phân tích yêu cầu
    3.2. Kiến trúc tổng thể
    3.3. Thiết kế pipeline AI
    3.4. Thiết kế backend
    3.5. Thiết kế cơ sở dữ liệu
    3.6. Thiết kế giao diện người dùng
    3.7. Thiết kế bảo mật và kiểm soát đầu vào
    3.8. Các quyết định thiết kế và đánh đổi
    3.9. Tóm tắt chương

CHƯƠNG 4. CÀI ĐẶT HỆ THỐNG ................................................
    4.1. Môi trường và công cụ phát triển
    4.2. Cài đặt tầng AI
    4.3. Cài đặt backend
    4.4. Cài đặt frontend
    4.5. Xây dựng bộ dữ liệu
    4.6. Triển khai bằng Docker
    4.7. Những chỗ cài đặt lệch khỏi thiết kế ở Chương 3, và lý do
    4.8. Kết luận chương

CHƯƠNG 5. THỰC NGHIỆM VÀ ĐÁNH GIÁ .........................................
    5.1. Mục tiêu và phương pháp đánh giá
    5.2. Môi trường thực nghiệm
    5.3. Bộ dữ liệu thực nghiệm
    5.4. Quá trình huấn luyện
    5.5. Đánh giá bộ phát hiện biển số
    5.6. Đánh giá khối OCR và hậu xử lý
    5.7. Đánh giá hiệu năng
    5.8. Khảo sát ảnh hưởng của độ phân giải và chất lượng split
    5.9. Đối chiếu toàn bộ chỉ tiêu phi chức năng
    5.10. Phân tích lỗi
    5.11. Bàn luận
    5.12. Kết luận chương

CHƯƠNG 6. KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN ....................................
    6.1. Tổng kết công việc đã thực hiện
    6.2. Các kết quả đạt được
    6.3. Các hạn chế của đồ án
    6.4. Hướng phát triển
    6.5. Kết luận chung

TÀI LIỆU THAM KHẢO ........................................................
PHỤ LỤC ...................................................................
```

---

## F. DANH MỤC HÌNH VẼ

> **Placeholder — sinh tự động khi ghép quyển.**
>
> **Quy ước đánh số hình:** `Hình <số chương>.<số thứ tự trong chương>` — ví dụ `Hình 2.3`. Chú thích đặt **phía dưới** hình, căn giữa. Hình lấy hoặc phỏng theo nguồn khác **bắt buộc** ghi nguồn ngay trong chú thích, kèm ký hiệu `[n]`.

| Ký hiệu | Tên hình | Trang | Trạng thái |
|---|---|:---:|---|
| Hình 1.1 | Sơ đồ khối tổng quát của một hệ thống ALPR | — | Chờ Chương 1 |
| Hình 2.x | *(các hình của Chương 2 — kiến trúc YOLO11, kiến trúc CRNN, cấu trúc biển số ô tô và xe máy, phân bố tỷ lệ khung hình theo loại biển…)* | — | Chờ Chương 2 |
| Hình 3.1 | Sơ đồ use case của hệ thống | — | Chờ Chương 3 |
| Hình 3.2 | Kiến trúc phân tầng của hệ thống | — | Chờ Chương 3 |
| Hình 3.3 | Luồng xử lý của pipeline AI | — | Chờ Chương 3 |
| Hình 3.4 | Sơ đồ tuần tự — nhận dạng ảnh | — | Chờ Chương 3 |
| Hình 3.5 | Sơ đồ tuần tự — nhận dạng video bất đồng bộ | — | Chờ Chương 3 |
| Hình 3.6 | Sơ đồ thực thể – liên kết của cơ sở dữ liệu | — | Chờ Chương 3 |
| Hình 4.x | *(các hình của Chương 4)* | — | Chờ Chương 4 |
| Hình 5.x | *(các hình của Chương 5 — đường cong loss, ma trận nhầm lẫn, biểu đồ độ trễ…)* | — | Chờ Chương 5 |

---

## G. DANH MỤC BẢNG BIỂU

> **Placeholder — sinh tự động khi ghép quyển.**
>
> **Quy ước đánh số bảng:** `Bảng <số chương>.<số thứ tự trong chương>` — ví dụ `Bảng 2.5`. Chú thích đặt **phía trên** bảng. Bảng tổng hợp số liệu từ nguồn khác bắt buộc có cột hoặc dòng ghi nguồn kèm ký hiệu `[n]`.

| Ký hiệu | Tên bảng | Trang | Trạng thái |
|---|---|:---:|---|
| Bảng 1.1 | Phạm vi trong và ngoài của đồ án | — | Chờ Chương 1 |
| Bảng 2.x | *(các bảng của Chương 2 — so sánh các phiên bản YOLO, so sánh các engine OCR, bảng mã tỉnh, tập ký tự seri, kích thước và tỷ lệ khung hình, so sánh bộ dữ liệu, tổng hợp quyết định công nghệ…)* | — | Chờ Chương 2 |
| Bảng 3.1 | Tổng hợp 34 yêu cầu chức năng theo mức ưu tiên MoSCoW | — | Chờ Chương 3 |
| Bảng 3.2 | Tổng hợp chỉ tiêu phi chức năng | — | Chờ Chương 3 |
| Bảng 3.3 | Ràng buộc, giả định và phụ thuộc | — | Chờ Chương 3 |
| Bảng 3.4 | Đặc tả trường của bảng `DetectionHistory` | — | Chờ Chương 3 |
| Bảng 3.5 | Các quyết định thiết kế AD-01 … AD-08 | — | Chờ Chương 3 |
| Bảng 4.x | *(các bảng của Chương 4)* | — | Chờ Chương 4 |
| Bảng 5.x | *(các bảng của Chương 5 — kết quả detection, OCR, end-to-end, tách theo layout, hiệu năng CPU, đối chiếu NFR…)* | — | Chờ Chương 5 |

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

Trên tập kiểm tra của split v3 (1.514 ảnh, đã khử trùng lặp giữa các tập), bộ phát hiện YOLO11n đạt mAP@0.5 = 0,9829 và mAP@0.5:0.95 = 0,7834 (precision 0,9837; recall 0,9714). Khối nhận dạng đạt độ chính xác mức ký tự (1 − CER) 0,8734; độ chính xác toàn chuỗi tăng từ 0,6098 lên 0,6555 nhờ bộ luật hậu xử lý (sửa đúng 128 biển, không làm hỏng biển nào), và độ chính xác end-to-end đạt 0,5227. Khoảng cách lớn nhất nằm ở layout: biển một dòng đạt 0,9489 còn biển hai dòng chỉ đạt 0,5810 — chênh 36,79 điểm phần trăm, trong khi biển hai dòng chiếm 79,8% tập đánh giá. Độ trễ xử lý một ảnh ở phân vị 95 là 731,15 ms trên CPU, đạt chỉ tiêu 800 ms. Chi tiết và phân tích lỗi được trình bày ở Chương 5.

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

---

## K. Ghi chú về trạng thái của phần đầu quyển

| Phần | Trạng thái | Việc còn lại |
|---|---|---|
| A. Trang bìa | 🟡 Mẫu | Điền thông tin trường, khoa, sinh viên, giảng viên hướng dẫn |
| B. Nhiệm vụ đồ án và nhận xét | 🟡 Giữ chỗ | Lấy biểu mẫu của khoa; xoá trang nào khoa không yêu cầu |
| C. Lời cam đoan | 🟡 Mẫu chuẩn | Điền tên, địa danh, ngày tháng |
| D. Lời cảm ơn | 🟡 Mẫu | Điền tên, cá nhân hoá nếu muốn |
| E. Mục lục | ⚪ Placeholder | Sinh tự động sau khi ghép đủ 6 chương |
| F. Danh mục hình vẽ | ⚪ Placeholder | Sinh tự động khi ghép quyển (Chương 4 và 5 đã viết xong) |
| G. Danh mục bảng biểu | ⚪ Placeholder | Sinh tự động khi ghép quyển (Chương 4 và 5 đã viết xong) |
| H. **Danh mục từ viết tắt** | ✅ **Hoàn chỉnh** | Rà lại một lượt khi ghép quyển |
| I. **Tóm tắt đồ án (tiếng Việt)** | ✅ **Hoàn chỉnh — bản v2, đã có số liệu thật** | — |
| J. **Abstract (tiếng Anh)** | ✅ **Hoàn chỉnh — bản v2, đã có số liệu thật** | — |

> **Ghi chú về hai bản tóm tắt.** Bản v1 được viết khi mô hình chính thức chưa huấn luyện xong nên kết lại bằng câu *"Kết quả thực nghiệm định lượng sẽ được trình bày ở Chương 5"* / *"will be reported in Chapter 5, once model training has been completed"*. Mô hình `models/best.pt` (YOLO11n, `imgsz=640`, split v3, 20 epoch) **đã huấn luyện xong** và toàn bộ chỉ tiêu NFR-A4/A5/A6/A7 cùng NFR-P1 **đã đo**, nên bản v2 hiện tại đã thay câu chờ đó bằng số liệu thật. Mọi lần cập nhật số liệu về sau **phải sửa đồng thời cả hai bản** để tiếng Việt và tiếng Anh không lệch nhau.
>
> **Cảnh báo trích dẫn — áp dụng cho cả hai bản tóm tắt.** Cặp số 94,3% / 45,7% được đo trên **RodoSol-ALPR (Brazil)**, **không phải trên dữ liệu Việt Nam**. Cả hai bản đã ghi rõ nguồn gốc bộ dữ liệu ngay trong câu văn. Tuyệt đối không được rút gọn thành "OpenALPR đạt 94,3% trên biển một dòng" mà bỏ mất mệnh đề nêu bộ dữ liệu — làm vậy sẽ biến một *analogue* định lượng thành một tuyên bố sai về dữ liệu Việt Nam.
>
> **Về số hiệu trích dẫn `[1]`, `[2]`, `[3]`:** đây là số **tạm thời**, sẽ được đánh lại toàn quyển khi ghép. Khoá BibTeX trong comment HTML mới là thông tin gốc và luôn đúng. Xem `THESIS-README.md` §4.
