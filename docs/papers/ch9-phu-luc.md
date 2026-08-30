# PHỤ LỤC

Phụ lục giữ phần tra cứu: quy mô mã nguồn, cấu hình huấn luyện, xuất xứ và giấy phép từng bộ dữ liệu, kết quả kiểm thử và đặc tả giao diện lập trình. Mọi số liệu lấy trực tiếp từ kho mã và các tệp kết quả đã lưu, không có số nào nhập tay.

---

## Phụ lục A. Mã nguồn

### A.1. Quy mô

Số liệu đếm trên kho mã tại thời điểm nộp, không tính thư mục phụ thuộc
(`node_modules`, môi trường ảo), dữ liệu ảnh, trọng số mô hình và các tệp sinh
tự động.

**Bảng A.1.** Quy mô mã nguồn theo thành phần

| Thành phần                                               | Ngôn ngữ               |  Số tệp |    Số dòng |
| -------------------------------------------------------- | ---------------------- | ------: | ---------: |
| `ai/` — tầng trí tuệ nhân tạo                            | Python                 |      31 |     16.949 |
| `scripts/` — công cụ dựng dữ liệu, đo đạc, xuất tài liệu | Python                 |      32 |     17.395 |
| `tests/` — kiểm thử tự động                              | Python                 |      23 |      9.246 |
| `backend/` — dịch vụ web và truy cập dữ liệu             | Python                 |      29 |      9.992 |
| `frontend/` — giao diện người dùng                       | TypeScript / TSX / CSS |      52 |     10.471 |
| `ai/` — cấu hình huấn luyện và bộ dữ liệu                | YAML                   |       3 |        328 |
| `deployment/`, `docker-compose.yml`                      | Dockerfile / YAML      |       5 |        780 |
| **Tổng**                                                 |                        | **178** | **65.805** |

Tỷ trọng đáng chú ý: phần **kiểm thử và công cụ đo đạc** (`tests/` + `scripts/`)
chiếm **26.641 dòng, tức 40,5%** toàn bộ mã nguồn — nhiều hơn cả tầng AI. Đây là
hệ quả trực tiếp của nguyên tắc trình bày đã nêu ở mục 5.1.2: mỗi con số công bố
trong Chương 5 phải sinh ra được bằng một lệnh chạy lại được.

### A.2. Tổ chức thư mục

Cây thư mục và ranh giới giữa các tầng trình bày ở **mục 4.2.2**.

Ranh giới quan trọng nhất trong cây thư mục: **`ai/` không được import bất cứ
thứ gì từ `backend/`**. Ràng buộc này là NFR-M1 và được canh giữ tự động bởi
`tests/test_architecture.py` — không phải bằng quy ước mà bằng một test sẽ fail
nếu ai đó vi phạm. Lý do và hệ quả trình bày ở mục 4.2.1 và 5.5.1.

---

## Phụ lục B. Siêu tham số huấn luyện

Cấu hình đầy đủ của lượt huấn luyện sinh ra `models/best.pt` — mô hình được dùng
cho mọi số liệu công bố trong Chương 5. Nguồn: `runs/final-640-v3/args.yaml`.

**Bảng B.1.** Siêu tham số huấn luyện YOLO11n

| Nhóm               | Tham số                     |             Giá trị | Ghi chú                                     |
| ------------------ | --------------------------- | ------------------: | ------------------------------------------- |
| Mô hình            | `model`                     |        `yolo11n.pt` | Khởi tạo từ trọng số tiền huấn luyện COCO   |
|                    | Số tham số                  |           2.590.035 | Biến thể nano — do ràng buộc CPU            |
| Dữ liệu            | `data`                      | `yolo_v3/data.yaml` | Phép chia tập v3                                    |
|                    | `imgsz`                     |                 640 | Đúng độ phân giải mà NFR-A1/A2 đặt chỉ tiêu |
|                    | `fraction`                  |                 1,0 | Dùng toàn bộ dữ liệu                        |
| Lịch huấn luyện    | `epochs`                    |                  20 |                                             |
|                    | `patience`                  |                  20 | Dừng sớm không kích hoạt                    |
|                    | `batch`                     |                   8 | Giới hạn bởi RAM và tốc độ CPU              |
|                    | `close_mosaic`              |                  10 | Tắt mosaic trong 10 epoch cuối              |
| Tối ưu hoá         | `optimizer`                 |               AdamW |                                             |
|                    | `lr0` / `lrf`               |        0,001 / 0,01 | Tốc độ học đầu và hệ số cuối                |
|                    | `cos_lr`                    |              `true` | Lịch cosine                                 |
|                    | `momentum`                  |               0,937 |                                             |
|                    | `weight_decay`              |              0,0005 |                                             |
|                    | `warmup_epochs`             |                 3,0 |                                             |
| Trọng số mất mát   | `box` / `cls` / `dfl`       |     8,0 / 0,5 / 1,5 |                                             |
| Tăng cường dữ liệu | `hsv_h` / `hsv_s` / `hsv_v` |   0,015 / 0,7 / 0,4 |                                             |
| Thiết bị           | `device`                    |               `cpu` | Không có GPU CUDA (ràng buộc CON-02)        |

**Giải thích chi tiết hai giá trị.** `batch = 8` không phải lựa chọn tối ưu mà
là giới hạn phần cứng; `epochs = 20` là con số bị ngân sách thời gian CPU quyết
định chứ không phải điểm hội tụ — chi phí và hệ quả của cả hai trình bày ở mục
4.5.1 và 3.6.

Cấu hình tinh chỉnh bộ nhận dạng ký tự (30 epoch, 6.672 mẫu, bộ ký tự 36) trình
bày tại mục 4.5.3 cùng kết quả đo bốn cấu hình. **Bản bàn giao không dùng mô hình
tinh chỉnh** — lý do ở cùng mục.

---

## Phụ lục C. Bộ dữ liệu

### C.1. Nguồn và giấy phép — nhánh phát hiện biển số

**Bảng C.1.** Bảy bộ dữ liệu đã hợp nhất, kèm giấy phép và số ảnh còn lại

| #   | Bộ (slug)                     | Nguồn                                                                      | Giấy phép                            |    Vào gộp |    Còn lại |
| --- | ----------------------------- | -------------------------------------------------------------------------- | ------------------------------------ | ---------: | ---------: |
| 1   | `roboflow_school_fuhih`       | Roboflow `school-fuhih/vietnamese-license-plate-tptd0` v1                  | CC BY 4.0                            |      8.357 |      6.868 |
| 2   | `hf_vn_plates_segment`        | HuggingFace `hoanglvuit/Vietnam_License_Plate_Segment_Datasets`            | ⚠️ chưa xác nhận                     |      4.578 |      4.375 |
| 3   | `roboflow_traffic_camera`     | Roboflow `traffic-camera/vietnam-license-plate-hayn8` v4                   | CC BY 4.0                            |      3.843 |      3.162 |
| 4   | `roboflow_eric_nguyen`        | Roboflow `eric-nguyen-knfxn/vietnam-license-plate-curhr` v1                | CC BY 4.0                            |        840 |        353 |
| 5   | `roboflow_demo_tracking`      | Roboflow `demo-tracking/license-plate-vietnam-car` v2                      | CC BY 4.0                            |        236 |        235 |
| 6   | `roboflow_cuong_ta`           | Roboflow `cuong-ta-ulxex/vietnamese-car-license-plate` v1                  | Public Domain _(người đăng tự khai)_ |      8.254 |        140 |
| 7   | `roboflow_tran_ngoc_xuan_tin` | Roboflow `tran-ngoc-xuan-tin-k15-hcm-dpuid/vietnam-license-plate-h8t3n` v1 | CC BY 4.0                            |      1.005 |          0 |
|     | **Tổng**                      |                                                                            |                                      | **27.113** | **15.133** |

**Ghi công theo giấy phép.** Năm bộ ở trên phát hành theo **CC BY 4.0**, bắt buộc
ghi công tác giả — bảng này chính là phần ghi công đó. Một bộ được người đăng tự
khai **Public Domain**, nhưng đồ án **không khẳng định** đó là Public Domain thật
vì ảnh nguồn có dấu hiệu là ảnh báo chí. Một bộ trên HuggingFace **chưa xác nhận
được giấy phép**; nó đóng góp 28,91% ngữ liệu nên đây là rủi ro pháp lý phải nêu
chứ không phải chi tiết bỏ qua được.

**Bộ thứ bảy còn lại 0 ảnh** sau khử trùng lặp — toàn bộ 1.005 ảnh của nó trùng
với ảnh đã có ở các bộ khác. Con số "hợp nhất từ 7 bộ" vì vậy phải đọc là **6
nguồn nguyên tố**, và điều này được nêu nhất quán ở mục 4.4.2 và 6.3.1.

## Phụ lục D. Cài đặt và chạy hệ thống

Quy trình cài đặt, lệnh chạy bằng Docker Compose, cách chạy trực tiếp không
dùng Docker và danh sách biến môi trường được trình bày đầy đủ ở hai tài liệu
vận hành đi kèm, nên không lặp lại ở đây:

| Nội dung | Tài liệu |
|---|---|
| Yêu cầu hệ thống, cài đặt từng bước, biến môi trường | `docs/manuals/installation-guide.md` |
| Dựng ảnh Docker, kiểm chứng container, bốn lỗi thật đã gặp | `docs/reports/08-deployment-guide.md` |

Kiến trúc triển khai và lý do chọn Docker trình bày ở **mục 4.9**.

## Phụ lục E. Kết quả kiểm thử

### E.1. Tổng hợp

**Bảng E.1.** Kết quả chạy bộ kiểm thử tự động

| Hạng mục                               | Kết quả    |
| -------------------------------------- | ---------- |
| Số test thu thập                       | **1.004**  |
| Đạt                                    | **1.004**  |
| `xfail` _(dự kiến hỏng)_               | 0          |
| Fail                                   | **0**      |
| Skip                                   | 0          |

### E.2. Phân nhóm

| Nhóm               | Kiểm chứng điều gì                                                                 |
| ------------------ | ---------------------------------------------------------------------------------- |
| Kiểm thử đơn vị    | Bộ luật hậu xử lý theo vị trí, phân loại bố cục, chuẩn hoá chuỗi, quy tắc hiển thị |
| Kiểm thử tích hợp  | Toàn bộ 10 endpoint qua HTTP thật, kèm cơ sở dữ liệu thật và migration             |
| Kiểm thử kiến trúc | Ranh giới `ai/` không import `backend/` (NFR-M1) — fail nếu ai đó vi phạm          |
| Kiểm thử hồi quy   | Các ca lỗi đã từng xảy ra, mỗi ca một test để không tái diễn                       |

**Lưu ý về kết quả kiểm thử.** Kết quả 0 thất bại thể hiện hệ thống đã vượt qua các kịch bản kiểm thử tự động được thiết lập, nhưng **không** đồng nghĩa với việc hoàn thành tất cả chỉ tiêu phi chức năng. Ba
chỉ tiêu phi chức năng hiện không đạt (NFR-A5, A6, A7) — bảng đối chiếu đầy đủ ở mục 5.7 và phân tích ở mục 5.9.2.

Báo cáo kiểm thử chi tiết theo từng nhóm: `docs/reports/07-testing-report.md`.

---

## Phụ lục F. Giao diện lập trình và cấu hình triển khai

### F.1. Danh sách endpoint

**Bảng F.1.** Mười endpoint của hệ thống

|  #  | Phương thức | Đường dẫn                     | Chức năng                                                 |
| :-: | ----------- | ----------------------------- | --------------------------------------------------------- |
|  1  | `POST`      | `/api/detect/image`           | Nhận dạng biển số từ một ảnh tĩnh                         |
|  2  | `POST`      | `/api/detect/video`           | Tạo tác vụ nhận dạng trên video, xử lý nền                |
|  3  | `POST`      | `/api/detect/frame`           | Nhận dạng một khung hình — dùng cho chế độ thời gian thực |
|  4  | `GET`       | `/api/jobs/{job_id}`          | Trạng thái và tiến độ của một tác vụ video                |
|  5  | `GET`       | `/api/history`                | Danh sách lịch sử, có tìm kiếm, lọc, phân trang           |
|  6  | `GET`       | `/api/history/{detection_id}` | Chi tiết một lần nhận dạng                                |
|  7  | `GET`       | `/api/history/export`         | Xuất lịch sử theo bộ lọc hiện hành                        |
|  8  | `DELETE`    | `/api/history/{detection_id}` | Xoá một bản ghi                                           |
|  9  | `GET`       | `/api/statistics`             | Số liệu thống kê tổng hợp theo cửa sổ thời gian           |
| 10  | `GET`       | `/health`                     | Trạng thái hệ thống và tình trạng nạp mô hình             |

Đặc tả đầy đủ — kiểu dữ liệu đầu vào, cấu trúc đầu ra, mã trạng thái và các
quyết định thiết kế API — ở mục 4.7.4. Tài liệu OpenAPI do FastAPI **tự sinh**
tại `/docs` và `/openapi.json`, nên nó không bao giờ lệch với mã nguồn.

### F.2. Cấu hình Docker Compose

**Bảng F.2.** Thành phần trong `docker-compose.yml`

| Thành phần         | Loại    | Vai trò                                                       |
| ------------------ | ------- | ------------------------------------------------------------- |
| `backend`          | dịch vụ | FastAPI + uvicorn, chạy đường ống AI trên CPU                  |
| `frontend`         | dịch vụ | nginx:alpine — phục vụ tệp tĩnh và chuyển tiếp yêu cầu sang máy chủ |
| `alpr-net`         | mạng    | Mạng nội bộ giữa hai dịch vụ                                  |
| `alpr-data`        | volume  | Cơ sở dữ liệu SQLite — dữ liệu sống qua lần khởi động lại     |
| `alpr-model-cache` | volume  | Bộ nhớ đệm trọng số PaddleOCR — tránh tải lại mỗi lần dựng    |

Ngoài hai volume có tên ở trên, thư mục `./storage` (ảnh và video đã tải lên) và
`./models` (trọng số bộ phát hiện, gắn **chỉ đọc**) được gắn trực tiếp từ máy chủ.

Bộ ba tệp triển khai: `deployment/docker/Dockerfile.backend` (build hai giai
đoạn), `Dockerfile.frontend` (build rồi phục vụ tĩnh) và `nginx.conf`. Phân tích
từng tệp ở mục 4.9.

---

## Phụ lục H. Đặc tả yêu cầu và thiết kế dữ liệu

Đặc tả đầy đủ — từng use case, bảng 34 yêu cầu chức năng kèm tiêu chí chấp nhận, bảng chỉ tiêu phi chức năng và đặc tả từng trường của cơ sở dữ liệu — nằm trong bộ tài liệu yêu cầu đi kèm. Chương 4 nêu quyết định thiết kế và lý do; phần liệt kê đầy đủ không lặp lại ở đây.

**Bảng H.1.** Nơi tra cứu đặc tả đầy đủ

| Nội dung | Tài liệu |
|---|---|
| 34 yêu cầu chức năng, 6 nhóm, mức MoSCoW, tiêu chí chấp nhận | `docs/00-requirements/functional-requirements.md` |
| Chỉ tiêu phi chức năng bảy nhóm, ngưỡng và phương pháp đo | `docs/00-requirements/non-functional-requirements.md` |
| Đặc tả use case | `docs/00-requirements/SRS.md` |
| Lược đồ cơ sở dữ liệu, từng trường | Chương 4 mục 4.7.3, Bảng 4.5 |
| Phân bố mức yêu cầu và diễn biến thay đổi phạm vi | Chương 4 mục 4.1.3; Chương 1 ghi chú sau mục 1.2 |

Hai ràng buộc của đặc tả đáng nhắc lại vì chúng chi phối toàn bộ phần đánh giá: **mọi chỉ tiêu hiệu năng đều là chỉ tiêu đo trên CPU** — máy thực hiện không có GPU CUDA (mục 4.3.1); và **cặp NFR-A5/A6 được đặt tách bạch có chủ đích**, vì hiệu số giữa chúng chính là đóng góp định lượng của khối hậu xử lý, đo được nhờ cột `raw_ocr_text` (mục 4.7.3).


## Phụ lục O. Tệp cấu hình gốc, báo cáo đo và mã nguồn

Phụ lục này giữ **hiện vật thô** — thứ cần để tái lập chứ không cần để đọc hiểu.
Phụ lục B trình bày siêu tham số dưới dạng bảng đã biên tập. Tệp tham số nguyên
văn do thư viện sinh ra nằm trong kho mã tại `runs/`, vì một bảng biên tập lại
không thay được tệp gốc khi có người muốn chạy lại đúng lượt huấn luyện ấy.

---

### O.2. Danh mục báo cáo đo dạng JSON

Toàn bộ số liệu công bố trong báo cáo được tổng hợp từ các tệp dữ liệu kiểm thử nằm tại thư mục `docs/reports/`. Danh mục **không chép nguyên văn nội dung tệp** để tránh làm tăng dung lượng tài liệu không cần thiết. Thay vào đó, mỗi dòng trình bày rõ **mục đích kiểm chứng của tệp** và **mục tham chiếu tương ứng**, đảm bảo mọi số liệu đều có thể truy xuất nguồn gốc minh bạch.

**Bảng O.1.** Báo cáo đo dạng JSON và mục sử dụng

| Tệp trong `docs/reports/`          | Mục đích kiểm chứng / Nội dung đo đạc                                           |  Dùng ở mục  |
| ---------------------------------- | ------------------------------------------------------------------------------- | :----------: |
| `03-evaluation-ch5-best-test.json` | mAP, Precision, Recall của `best.pt` trên tập test v3                           |    5.4.1     |
| `07-leak-check-t10.json`           | Số cặp ảnh gần trùng train↔test theo từng ngưỡng Hamming                        |    5.3.2     |
| `17-plate-type-audit.json`         | Phân bố màu nền của 2.801 mẫu có nhãn chuỗi — căn cứ cảnh báo 97,68% biển trắng |   5.3, 6.2   |
| `04-ocr-accuracy.json`             | A4–A7 lượt đo cơ sở                                                             |     5.5      |
| `16-ocr-accuracy-rescued.json`     | A4–A7 sau khi thêm bước phục hồi dòng trên                                           |    5.5.6     |
| `28-ocr-accuracy-finetuned.json`   | A4–A7 của bộ nhận dạng đã tinh chỉnh                                            |    4.5.3     |
| `29-reconly-ablation.json`         | Bốn cấu hình det+rec ↔ chỉ nhận dạng, hai model                                       | 4.5.3, 5.6.6 |
| `15-two-line-ab.json`              | A/B ghép rồi đọc ↔ đọc từng nửa, 200 biển hai dòng                              |    5.5.6     |
| `15-two-line-fallback-700.json`    | A/B bước phục hồi dòng trên, mẫu 700 biển                                            |    5.5.6     |
| `15-two-line-fallback.json`        | A/B bước phục hồi dòng trên, mẫu 200 biển                                            |    5.5.6     |
| `15-two-line-rescue-ladder.json`   | Chi phí và lợi ích từng bậc của bậc thang thử lại                               |    5.5.7     |
| `15-fragment-height-ab.json`       | Ngưỡng lọc mảnh văn bản theo hình học                                           |    4.6.3     |
| `19-color-accuracy.json`           | Độ chính xác bộ nhận màu nền trên 1.565 ảnh ngoài hiệu chỉnh                    |    4.6.7     |
| `07-benchmark-p1-resolved.json`    | Độ trễ đầu cuối p50/p95 và phân rã theo bước                                    | 5.6.1, 5.6.2 |
| `07-api-overhead.json`             | Overhead của tầng API so với gọi đường ống trực tiếp                             |    5.6.5     |
| `07-stress-load.json`              | Chịu tải đồng thời và tỉ lệ thành công khi chạy liên tục                        |    5.6.5     |
| `07-stress-db.json`                | Thời gian truy vấn lịch sử trên 10.000 bản ghi                                  |    5.6.5     |
| `03-cpu-benchmark.json`            | So sánh PyTorch ↔ ONNX Runtime ↔ OpenVINO trên CPU                              |    5.6.3     |

Thư mục còn **23 tệp JSON khác** thuộc các lượt đo trung gian đã bị lượt sau
thay thế; chúng được giữ lại trong kho để đối chiếu lịch sử chứ không được trích
dẫn trong quyển. Nguyên tắc áp dụng xuyên suốt: **một số liệu chỉ được đưa vào**
**quyển khi tệp sinh ra nó còn trong kho và chạy lại được.**

---
