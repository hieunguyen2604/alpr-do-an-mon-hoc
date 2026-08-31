# PHỤ LỤC

## Phụ lục I. Mã vùng biển số

**Bảng I.1.** 81 mã vùng biển số đang sử dụng, dải 11–99

| 11 | 12 | 14 | 15 | 16 | 17 | 18 | 19 | 20 |
|---|---|---|---|---|---|---|---|---|
| 21 | 22 | 23 | 24 | 25 | 26 | 27 | 28 | 29 |
| 30 | 31 | 32 | 33 | 34 | 35 | 36 | 37 | 38 |
| 39 | 40 | 41 | 43 | 47 | 48 | 49 | 50 | 51 |
| 52 | 53 | 54 | 55 | 56 | 57 | 58 | 59 | 60 |
| 61 | 62 | 63 | 64 | 65 | 66 | 67 | 68 | 69 |
| 70 | 71 | 72 | 73 | 74 | 75 | 76 | 77 | 78 |
| 79 | 80 | 81 | 82 | 83 | 84 | 85 | 86 | 88 |
| 89 | 90 | 92 | 93 | 94 | 95 | 97 | 98 | 99 |

Dải 11–99 có 89 số; **8 mã chưa cấp**: `13`, `42`, `44`, `45`, `46`, `87`, `91`, `96`. Từ 01/7/2025 cả nước còn **34 tỉnh, thành phố**, và ký hiệu sau hợp nhất **giữ toàn bộ ký hiệu của các địa phương được hợp nhất** — nên số mã vẫn nhiều hơn số tỉnh. Danh sách này là nguồn sinh ra nhóm bắt mã tỉnh trong biểu thức kiểm tra hợp lệ (mục 4.6.5), nên nó không thể lệch khỏi mã đang chạy.

---

## Phụ lục II. Ghi công giấy phép bộ dữ liệu

Bộ dữ liệu hợp nhất từ bảy nguồn công khai. **Năm bộ phát hành theo giấy phép CC BY 4.0**, giấy phép này **bắt buộc ghi công tác giả**: Roboflow `school-fuhih/vietnamese-license-plate-tptd0`, `traffic-camera/vietnam-license-plate-hayn8`, `eric-nguyen-knfxn/vietnam-license-plate-curhr`, `demo-tracking/license-plate-vietnam-car`, và `tran-ngoc-xuan-tin-k15-hcm-dpuid/vietnam-license-plate-h8t3n`. Bộ `cuong-ta-ulxex/vietnamese-car-license-plate` được người đăng tự khai Public Domain — đồ án **không khẳng định** điều đó vì ảnh nguồn có dấu hiệu là ảnh báo chí. Bộ `hoanglvuit/Vietnam_License_Plate_Segment_Datasets` trên HuggingFace **chưa xác nhận được giấy phép** và đóng góp 28,91% ngữ liệu; đây là rủi ro pháp lý được nêu ở mục 6.2 chứ không phải chi tiết bỏ qua được.

---

## Phụ lục III. Nơi tra cứu phần chi tiết

Các bảng tra cứu dưới đây không lặp lại trong quyển vì chúng đã nằm trong thân bài hoặc trong bộ tài liệu đi kèm.

| Nội dung | Nơi tra cứu |
|---|---|
| Siêu tham số huấn luyện đầy đủ | Mục 4.5.1; nguyên văn tại `runs/final-640-v3/args.yaml` |
| Quy mô và tổ chức mã nguồn | Mục 4.2.2 |
| Kết quả kiểm thử theo nhóm | Mục 5.7; chi tiết tại `docs/reports/07-testing-report.md` |
| Danh sách endpoint và cấu hình triển khai | Mục 4.7.4 và 4.9; OpenAPI tự sinh tại `/docs` |
| Đặc tả 34 yêu cầu chức năng và chỉ tiêu phi chức năng | `docs/00-requirements/` |
| Chỉ mục báo cáo đo dạng JSON chống lưng từng con số | `docs/reports/README.md` |
| Hướng dẫn cài đặt và vận hành | `docs/manuals/installation-guide.md` |

---

## Phụ lục IV. Phân định phần tự xây dựng và phần dùng lại

**Bảng IV.1.** Phân định công việc theo từng thành phần

| Thành phần | Nguồn gốc | Nhóm thực hiện đã làm gì |
|---|---|---|
| Bộ phát hiện biển số | Kiến trúc YOLO11n có sẵn, trọng số khởi đầu từ COCO | **Tự huấn luyện** trên dữ liệu Việt Nam do nhóm hợp nhất; chọn siêu tham số; đánh giá |
| Bộ nhận dạng ký tự | Mô hình PP-OCRv5 mobile tiền huấn luyện | Tích hợp; **tự đo** so với hai bộ nhận dạng khác; thử tinh chỉnh và **báo cáo cả kết quả âm** |
| **Khối xử lý ảnh vùng biển** | — | **Tự thiết kế và cài đặt toàn bộ**: nắn hình, phân loại bố cục, tách hai nửa, ghép ngang |
| **Khối hậu xử lý theo quy chuẩn** | — | **Tự thiết kế và cài đặt toàn bộ**: mặt nạ vị trí, tập mã tỉnh, bảng ánh xạ nhầm lẫn |
| Bộ dữ liệu | 7 bộ ảnh công khai, giấy phép ở Phụ lục C | **Tự hợp nhất, khử trùng lặp chéo bộ, chia tập có kiểm soát rò rỉ**; gán nhãn chuỗi cho tập con |
| Máy chủ, giao diện, đóng gói | Thư viện mã nguồn mở (FastAPI, React, Docker) | **Tự thiết kế kiến trúc và cài đặt**; viết bộ kiểm thử |
| Quy trình đo và báo cáo | — | **Tự xây dựng toàn bộ**: công cụ đo, giao thức, phân tích lỗi |

---

## Phụ lục V. Quy chuẩn biển số và chỉ số đánh giá — bảng chi tiết

**Bảng V.1.** Tổng hợp các tập ký tự seri

| Tập | Số lượng | Nội dung |
|---|:--:|---|
| Chữ cái thứ nhất của seri | 20 | A B C D E F **G** H K L M N P S T U V X Y Z |
| Chữ cái thứ hai của seri xe máy | 20 | A B C D E F H K L M N P **R** S T U V X Y Z |
| Seri biển nền xanh | 11 | A B C D E F G H K L M |
| **Bị loại trừ khỏi toàn hệ thống** | **5** | **I, J, O, Q, W** |
| Tập ký tự an toàn tối thiểu cho OCR | 21 | 20 chữ ở vị trí thứ nhất, hợp thêm R |

**Bảng V.2.** Màu nền biển số và đối tượng áp dụng [7]

| Màu nền / màu chữ | Đối tượng | Ghi chú cho ALPR |
|---|---|---|
| Trắng / đen | Tổ chức, cá nhân trong nước, xe **không** kinh doanh vận tải | Phổ biến nhất |
| Vàng / đen | Xe **kinh doanh vận tải** | Tín hiệu phân loại **duy nhất còn hợp lệ** |
| Xanh dương / trắng | Cơ quan Đảng, Nhà nước, công an | Seri chỉ dùng 11 chữ cái |
| Trắng / **đỏ** | Xe ngoại giao (`NG`) và tổ chức quốc tế (`QT`) | Cấu trúc chuỗi khác hẳn |
| Đỏ / trắng | Xe quân đội và doanh nghiệp quân đội | **Ngoài phạm vi** TT 79/2024, thuộc TT 169/2021/TT-BQP [8] |

**Bảng V.3.** Kích thước và tỷ lệ khung hình của các loại biển số [6]

| Loại biển | Kích thước (dài × cao) | Tỷ lệ khung hình | Số dòng |
|---|---|:--:|:--:|
| Ô tô — biển **dài** | **520 × 110 mm** | **4,727** | **1 dòng** |
| Ô tô — biển **ngắn** | **330 × 165 mm** | **2,000** | **2 dòng** |
| **Xe mô tô, xe gắn máy** | **190 × 140 mm** | **1,357** | **2 dòng** |

**Bảng V.4.** Khoảng cách giữa mAP@0.5 và mAP@0.5:0.95 ở ba công trình về biển số

| Công trình | Bộ dữ liệu · quốc gia | mAP@0.5 | mAP@0.5:0.95 | Chênh (điểm %) |
|---|---|---:|---:|---:|
| Batra và cộng sự (2022) [15]<!-- batra_2022_yolov5 --> | biển số Ấn Độ | 87,2% | 46,5% | **40,7** |
| Một nghiên cứu YOLOv11 (2025) [16]<!-- jaic_2025_yolov11alpr --> | không nêu rõ | 90,6% | 63,1% | **27,5** |
| Biển xe máy Indonesia (2025) [17]<!-- jcosine_2025_yolo11plate --> | Indonesia | 99,5% | 80,7% | **18,8** |

---

## Phụ lục VI. Tổng hợp quyết định công nghệ nền tảng

**Bảng VI.1.** Tổng hợp quyết định công nghệ nền tảng

|  #  | Hạng mục              | Lựa chọn (phương án thay thế)                                      | Lý do chính                                                                                  | Đánh đổi phải chấp nhận                                                                   |
| :-: | --------------------- | ------------------------------------------------------------------ | -------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
|  1  | Nền tảng web phía máy chủ | **FastAPI** (Django, Flask)                                        | Tự sinh đặc tả OpenAPI — tạo sẵn một sản phẩm bàn giao; có sẵn WebSocket và tác vụ nền       | Phải biết khi nào **không** dùng hàm bất đồng bộ; nguy cơ tranh chấp với luồng suy luận   |
|  2  | ORM và migration      | **SQLAlchemy 2.0 + Alembic** (Tortoise ORM, Peewee)                | Tích hợp sâu kiểu tĩnh; lược đồ đã thay đổi nên nhu cầu migration là có thật                 | Đường cong học dốc nhất trong nhóm                                                        |
|  3  | Cơ sở dữ liệu         | **SQLite** (PostgreSQL, MySQL)                                     | Ghi có thể xếp hàng vì suy luận CPU mới là nút cổ chai; không thêm dịch vụ khi đóng gói      | **Chỉ một tiến trình ghi tại một thời điểm**; vượt ngưỡng tải phải chuyển PostgreSQL      |
|  4  | Giao diện              | **React + TypeScript + Vite + TailwindCSS** (Vue, Angular, Svelte) | Hệ sinh thái lớn nhất; công cụ build tiền nhiệm ngừng bảo trì; kiểu tĩnh nối tiếp từ máy chủ | Tự lắp ghép routing, quản lý trạng thái, thành phần giao diện                             |
|  5  | Framework học sâu     | **PyTorch** (TensorFlow)                                           | Ultralytics khai báo PyTorch là phụ thuộc lõi — chọn YOLO11 là chọn PyTorch                  | Kéo theo framework học sâu **thứ hai** (PaddlePaddle) do lựa chọn OCR — giải bằng mục 3.4 |
|  6  | Đóng gói              | **Docker + Compose**                                               | Yêu cầu tái lập và khởi động bằng một lệnh                                                   | Kích thước image là rủi ro do có framework học sâu                                        |

---

## Phụ lục VII. Máy chủ và cơ sở dữ liệu — bảng chi tiết

**Bảng VII.1.** Ba quy tắc giữ cho tầng nghiệp vụ tách biệt

| Quy tắc | Nội dung | Hệ quả |
|---|---|---|
| Tầng định tuyến **không chứa truy vấn** | Mọi truy cập dữ liệu đi qua tầng kho dữ liệu | Một thay đổi lược đồ có **bán kính ảnh hưởng gói trong một mô-đun**, không lan ra tầng định tuyến |
| Tầng kho **không tự xác nhận giao dịch** | Chỉ đẩy thay đổi xuống phiên làm việc; việc xác nhận thuộc về tầng gọi | Lưu một lượt nhận dạng cùng toàn bộ biển số thuộc lượt đó là **một thao tác logic duy nhất** — xác nhận giữa chừng sẽ để lại bản ghi nửa vời |
| Mỗi ngoại lệ mang **hai mô tả** | Thông điệp tiếng Việt kèm hành động khắc phục đi vào thân phản hồi HTTP; mô tả kỹ thuật chỉ đi vào nhật ký | Cây ngoại lệ ánh xạ thẳng sang mã trạng thái HTTP, kèm bộ xử lý bắt tất cả để ngoại lệ ngoài dự kiến **không làm lộ vết ngăn xếp** ra người dùng (NFR-S4) |

**Bảng VII.2.** Lược đồ cơ sở dữ liệu — hai bảng, quan hệ một–nhiều

| Bảng | Cột | Kiểu | Ghi chú |
|---|---|---|---|
| **`detection_job`** _(11 cột)_ | `id` | `VARCHAR(36)` | Khoá chính, UUID |
| | `input_type` · `status` | `VARCHAR(16)` | `image`\|`video`\|`webcam`; `pending`\|`processing`\|`completed`\|`failed`\|`cancelled` |
| | `progress` | `FLOAT` | 0,0 – 1,0 |
| | `source_path` · `output_path` | `VARCHAR(512)` | Cho phép rỗng |
| | `error_message` | `TEXT` | Chỉ phía máy chủ, không trả ra API |
| | `total_frames` · `processed_frames` | `INTEGER` | Dùng cho tác vụ video |
| | `created_at` · `completed_at` | `DATETIME` | |
| **`detection_history`** _(23 cột)_ | `id` | `INTEGER` | Khoá chính |
| | `plate_number` · `raw_ocr_text` | `VARCHAR(32)` | **Lưu song song** chuỗi đã chuẩn hoá và chuỗi thô |
| | `confidence` · `ocr_confidence` | `FLOAT` | Của **bộ phát hiện** và của **bộ nhận dạng** — hai đại lượng khác nhau |
| | `image_path` · `plate_image_path` | `VARCHAR(512)` | Ảnh gốc và vùng biển đã cắt |
| | `bbox_x` · `bbox_y` · `bbox_w` · `bbox_h` | `INTEGER` | Hộp giới hạn |
| | `is_valid_format` | `BOOLEAN` | Có khớp quy chuẩn Việt Nam không |
| | `plate_line_count` · `upper_char_count` | `INTEGER` | 1 hoặc 2 dòng; số ký tự dòng trên (3 hoặc 4) |
| | `plate_kind` · `plate_color` · `plate_color_confidence` | `VARCHAR(16)` · `FLOAT` | Họ biển và màu nền, cho phép rỗng |
| | `video_time_seconds` | `FLOAT` | Mốc thời gian trong video, rỗng với ảnh tĩnh |
| | `processing_time` · `detected_time` · `created_at` | `FLOAT` · `DATETIME` | |
| | `source_job_id` | `VARCHAR(36)` | **Khoá ngoại** trỏ `detection_job.id` |

Biến môi trường của bản đóng gói Docker liệt kê trong tệp `deployment/docker/.env.example` đi kèm mã nguồn.

---

## Phụ lục VIII. Số liệu thực nghiệm chi tiết

**Bảng VIII.1.** Các cặp ký tự bị nhầm nhiều nhất, đối chiếu bảng luật hiện hành

| Hạng | Ký tự thật → bị đọc thành | Số lần | Tỉ lệ trong tổng lỗi thay thế | Bảng luật có phủ không? |
| :--: | :-----------------------: | -----: | ----------------------------: | ----------------------- |
|  1   |           L → 1           |     90 |                        10,44% | có — đúng chiều         |
|  2   |           E → F           |     73 |                         8,47% | không                   |
|  3   |           4 → L           |     53 |                         6,15% | **có — đã bổ sung**     |
|  4   |           U → 1           |     38 |                         4,41% | không                   |
|  5   |           D → 0           |     34 |                         3,94% | có — đúng chiều         |
|  6   |           Z → 7           |     32 |                         3,71% | **có — đã bổ sung**     |
|  7   |           2 → 7           |     26 |                         3,02% | không                   |
|  8   |           X → Y           |     21 |                         2,44% | không                   |
|  9   |           B → R           |     20 |                         2,32% | không                   |
|  10  |           9 → 0           |     19 |                         2,20% | không                   |

**Bảng VIII.2.** Sáu lần đo NFR-P2 trong các điều kiện máy khác nhau

| Điều kiện | FPS hiệu dụng | p50 | p95 | p95/p50 | Kết luận |
|---|---:|---:|---:|---:|:--:|
| Lượt đo cũ — máy đang tải nặng | 2,379 | 180,05 | **1.247,70** | **6,93** | ❌ |
| Máy rảnh, lần 1 | **5,257** | 164,08 | 204,52 | 1,25 | ✅ |
| Máy rảnh, lần 2 | **5,213** | 165,13 | 199,33 | 1,21 | ✅ |
| Ép tải 6 lõi | 4,367 | 201,76 | 238,97 | 1,18 | 🟡 |
| Ép tải 12 lõi | 4,057 | 215,69 | 268,40 | 1,24 | 🟡 |
| OpenVINO, máy rảnh | **6,310** | 129,60 | 148,50 | 1,15 | ✅ |

---

## Phụ lục IX. Năm lượt hiệu chỉnh độ chính xác nhận dạng

**Bảng IX.1.** Tiến triển độ chính xác qua năm lượt hiệu chỉnh

| Lượt | Thay đổi chính | A4 | A6 |
| :--: | --- | ---: | ---: |
| 1 | Lượt đo đầu tiên | 0,8734 | 0,6555 |
| 2 | Trả lại tỷ lệ đúng cho ảnh biển; phục hồi dòng trên _(5.5.6)_ | 0,8848 | 0,6730 |
| 3 | Bốn đợt sửa độ chính xác ở khối đọc ký tự | 0,9416 | 0,7437 |
| 4 | Công cụ đo chạy đúng đường xử lý của bản giao hàng _(5.5.7)_ | 0,9454 | 0,7512 |
| **5** | **Bảng sửa ký tự dựng từ ma trận nhầm lẫn đo được** _(5.5.4)_ | **0,9483** | **0,7701** |
| ✗ | _(đối chứng)_ Bộ đọc ký tự đã tinh chỉnh — **kém hơn bản gốc**, đã bác bỏ | 0,9252 | 0,6762 |
