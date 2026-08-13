# PHỤ LỤC

Phụ lục cung cấp các thông tin chi tiết được nhắc tới trong thân đồ án nhưng
không đưa vào thân bài để giữ mạch đọc: quy mô và tổ chức mã nguồn, cấu hình
huấn luyện đầy đủ, xuất xứ và giấy phép của từng bộ dữ liệu, hướng dẫn cài đặt,
kết quả kiểm thử và đặc tả giao diện lập trình.

Mọi số liệu trong phụ lục lấy trực tiếp từ kho mã nguồn và các tệp kết quả đã
được lưu, không có số nào nhập tay.

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

```
ai/
  inference/      pipeline suy luận — detector, recognizer, hậu xử lý, hai dòng
  evaluation/     đo độ chính xác, hiệu năng, phân tích lỗi, kiểm rò rỉ
  training/       cấu hình và notebook huấn luyện
backend/
  api/            các route FastAPI
  services/       tầng nghiệp vụ — điều phối, không chứa logic AI
  repositories/   truy cập cơ sở dữ liệu
  models/         mô hình dữ liệu SQLAlchemy
  migrations/     Alembic
frontend/
  src/pages/      ba trang: nhận dạng ảnh, nhận dạng video, lịch sử
  src/components/ thành phần dùng chung
  src/api/        tầng gọi API và ánh xạ kiểu dữ liệu
tests/            kiểm thử đơn vị, tích hợp, kiến trúc
scripts/          dựng bộ dữ liệu, đo đạc, dựng quyển và slide
deployment/       Dockerfile, nginx, entrypoint
models/           trọng số đã huấn luyện
docs/             tài liệu, báo cáo, quyển đồ án
```

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

## Phụ lục D. Hướng dẫn cài đặt và chạy

### D.1. Yêu cầu

| Hạng mục     | Yêu cầu                                     |
| ------------ | ------------------------------------------- |
| Hệ điều hành | Windows 10/11, macOS hoặc Linux             |
| Docker       | Docker Engine 24+ và Docker Compose v2      |
| Bộ nhớ       | Tối thiểu 4 GB RAM trống                    |
| Đĩa          | Khoảng 6 GB cho image và dữ liệu            |
| GPU          | **Không cần** — toàn hệ thống chạy trên CPU |

### D.2. Chạy bằng Docker Compose (khuyến nghị)

```bash
git clone <địa chỉ kho mã>
cd vn-license-plate-recognition
docker compose up -d --build
```

Sau khi các container khởi động, mở trình duyệt tại:

| Địa chỉ                        | Nội dung                           |
| ------------------------------ | ---------------------------------- |
| `http://localhost:5173`        | Giao diện người dùng               |
| `http://localhost:8000/docs`   | Tài liệu API (Swagger UI, tự sinh) |
| `http://localhost:8000/health` | Trạng thái hệ thống                |

Kiểm tra hệ thống đã nạp được mô hình:

```bash
curl http://localhost:8000/health
```

Trường `model_loaded` phải trả về `true`. Nếu trả về `false`, hệ thống vẫn chạy
nhưng mọi yêu cầu nhận dạng sẽ trả lỗi thay vì trả kết quả giả lập — cơ chế
`UnavailablePipeline`, trình bày ở mục 4.7.4.

### D.3. Chạy trực tiếp không dùng Docker

```bash
# Tầng AI và backend
python -m venv backend/.venv
backend/.venv/Scripts/pip install -r backend/requirements.txt
backend/.venv/Scripts/alembic upgrade head
backend/.venv/Scripts/uvicorn backend.main:app --port 8000

# Giao diện, ở một cửa sổ lệnh khác
cd frontend && npm install && npm run dev
```

> **Lưu ý về môi trường ảo.** Nhóm thực hiện dùng **ba môi trường ảo Python tách biệt**,
> không phải một. Lý do bắt buộc phải tách — xung đột phiên bản giữa hai framework
> học sâu — trình bày ở mục 4.3.2. Gộp chúng lại sẽ hỏng.

### D.4. Biến môi trường đáng chú ý

| Biến                      | Mặc định         | Tác dụng                                                          |
| ------------------------- | ---------------- | ----------------------------------------------------------------- |
| `ALPR_MODEL_PATH`         | `models/best.pt` | Đường dẫn trọng số bộ phát hiện                                   |
| `ALPR_RECTIFY_ENABLED`    | `true`           | Bật bước nắn hình biển nghiêng                                    |
| `ALPR_SR_RETRY_ENABLED`   | `false`          | Bậc siêu phân giải — **tắt mặc định**, xem mục 5.5.7              |
| `ALPR_OCR_SKIP_DETECTION` | `false`          | Bỏ bước phát hiện chữ — **tắt mặc định**, xem mục 5.6.6           |
| `ALPR_OCR_REC_MODEL_DIR`  | _(rỗng)_         | Thư mục mô hình nhận dạng tinh chỉnh; để rỗng là dùng mô hình gốc |

Chi tiết đầy đủ về triển khai — kiến trúc mạng Docker, các volume, cách xử lý sự
cố thường gặp và lưu ý dung lượng image — ở `deployment/README.md`.

---

## Phụ lục E. Kết quả kiểm thử

### E.1. Tổng hợp

**Bảng E.1.** Kết quả chạy bộ kiểm thử tự động

| Hạng mục                               | Kết quả    |
| -------------------------------------- | ---------- |
| Số test thu thập                       | **1.002**  |
| Đạt                                    | **1.001**  |
| `xfail` _(dự kiến hỏng, có ghi lý do)_ | 1          |
| Fail                                   | **0**      |
| Skip                                   | 0          |
| Ngày chạy                              | 02/08/2026 |

### E.2. Phân nhóm

| Nhóm               | Kiểm chứng điều gì                                                                 |
| ------------------ | ---------------------------------------------------------------------------------- |
| Kiểm thử đơn vị    | Bộ luật hậu xử lý theo vị trí, phân loại bố cục, chuẩn hoá chuỗi, quy tắc hiển thị |
| Kiểm thử tích hợp  | Toàn bộ 10 endpoint qua HTTP thật, kèm cơ sở dữ liệu thật và migration             |
| Kiểm thử kiến trúc | Ranh giới `ai/` không import `backend/` (NFR-M1) — fail nếu ai đó vi phạm          |
| Kiểm thử hồi quy   | Các ca lỗi đã từng xảy ra, mỗi ca một test để không tái diễn                       |

**Lưu ý về kết quả kiểm thử.** Kết quả 0 thất bại thể hiện hệ thống đã vượt qua các kịch bản kiểm thử tự động được thiết lập, nhưng **không** đồng nghĩa với việc hoàn thành tất cả chỉ tiêu phi chức năng. Ba
chỉ tiêu phi chức năng hiện không đạt (NFR-A5, A6, A7) và một chỉ tiêu trượt sàn
(NFR-P2) — bảng đối chiếu đầy đủ ở mục 5.7 và phân tích ở mục 5.9.2.

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
quyết định thiết kế API — ở mục 4.7.3. Tài liệu OpenAPI do FastAPI **tự sinh**
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

Bốn mục dưới đây là **tài liệu tra cứu**, không phải mạch lập luận: đặc tả
từng use case, bảng 34 yêu cầu chức năng, bảng chỉ tiêu phi chức năng, và đặc
tả từng trường của cơ sở dữ liệu. Chương 4 nêu quyết định thiết kế và lý do;
phần liệt kê đầy đủ để ở đây.

---

### H.2. Bảng 34 yêu cầu chức năng

Đồ án đặc tả **34 yêu cầu chức năng** trong **6 nhóm**, mỗi yêu cầu có mã, mức MoSCoW và một tiêu chí chấp nhận kiểm chứng được. Phân bố: FR-1 (ảnh tĩnh) **7 Must**; FR-2 (video) **4 Must + 2 Won't**; FR-3 (thời gian thực, tầng API) **3 Must + 2 Won't**; FR-4 (thống kê – lịch sử – tra cứu) **4 Must + 1 Should + 1 Could + 2 Won't**; FR-5 (quản lý dữ liệu) **2 Should + 2 Could**; FR-6 (hệ thống, vận hành) **2 Must + 2 Should**. Tổng **20 Must, 5 Should, 3 Could, 6 Won't = 34**.

**FR-1:** tiếp nhận, kiểm tra hợp lệ, phát hiện _tất cả_ vùng biển, cắt và nhận dạng, hậu xử lý, lưu kết quả, hiển thị có bounding box. FR-1.5 quy định lưu **cả chuỗi OCR thô lẫn chuỗi đã sửa** — điều kiện cần để đo đóng góp hậu xử lý ở Chương 5 (4.7.2b). **FR-2:** thêm trích khung theo bước nhảy, **gộp trùng** (FR-2.4 — thiếu nó một video 30 giây sinh hàng nghìn bản ghi về cùng vài chiếc xe, phá hỏng thống kê FR-4), kết xuất video gắn nhãn và huỷ tác vụ — hai yêu cầu cuối đưa ra khỏi phạm vi ngày 03/08/2026. **FR-3:** theo quyết định 2026-07-20, hai yêu cầu thuần giao diện FR-3.1, FR-3.4 chuyển **M → W**; FR-3.2/3.3/3.5 vẫn Must, kiểm chứng ở tầng API. **FR-4:** chỉ số tổng hợp (FR-4.1), biểu đồ theo thời gian (FR-4.2), danh sách phân trang, tìm kiếm khớp một phần, lọc, chi tiết, tải ảnh, sắp xếp; **FR-4.3 → 4.8 không đổi**. **FR-5:** xoá bản ghi kèm tệp, xuất CSV/JSON (CSV phải UTF-8 **có BOM** kẻo Excel hiển thị sai tiếng Việt), dọn tệp mồ côi, xoá hàng loạt. **FR-6:** health check báo trạng thái mô hình và CSDL; log có cấu trúc; thông báo lỗi thân thiện không lộ stack trace; cấu hình qua biến môi trường.

> ### Bốn yêu cầu mức Won't và hai đợt thu gọn phạm vi ngày 2026-07-20
>
> Bốn yêu cầu Won't đầu tiên đều **thuần giao diện**, chuyển mức trong cùng ngày qua hai đợt: đợt 1 gỡ trang Webcam (FR-3.1, FR-3.4 **M → W**; năng lực còn ở `POST /api/detect/frame`); đợt 2 gỡ trang Tổng quan (**FR-4.1 M → W**, FR-4.2 S → W; năng lực còn ở `GET /api/statistics` và `GET /health`).
>
> **Lưu ý về phạm vi:** Hai yêu cầu mức _Must_ đã được điều chỉnh ra khỏi phạm vi thực hiện — FR-4.1 ngày 20/07/2026 và FR-2.5 ngày 03/08/2026. Phân bố các mức yêu cầu được cập nhật thành **20 Must, 5 Should, 3 Could, 6 Won't**, và được ghi nhận minh bạch tại mục 6.2. Cần lưu ý rằng hai đợt điều chỉnh này chỉ thu gọn **giao diện hiển thị**, không làm mất đi **năng lực xử lý của hệ thống** — các endpoint API vẫn phục vụ bình thường, nằm trong tài liệu OpenAPI và được kiểm thử tự động đầy đủ (`tests/integration/test_api_statistics.py`, `test_api_health.py`). Đánh đổi đo được: việc loại bỏ `recharts` giúp dung lượng gói tải về của giao diện giảm từ ~730 KB xuống **328,8 KB** (−55%).

**Ma trận truy vết:** mỗi nhóm truy vết tới giai đoạn cài đặt và hình thức kiểm chứng (FR-1: unit + integration; FR-2: integration + performance; FR-3: performance ở tầng API; FR-4: integration + UI test cho FR-4.3→4.8; FR-5: unit; FR-6: smoke + stress). Kết quả ở Chương 5.

---

### H.3. Bảng chỉ tiêu phi chức năng

Bảy nhóm: hiệu năng (NFR-P), độ chính xác (NFR-A), tin cậy (NFR-R), khả dụng (NFR-U), bảo trì (NFR-M), bảo mật (NFR-S), tương thích – triển khai (NFR-C), mở rộng (NFR-SC).

#### a) Nguyên tắc nền tảng: mọi chỉ tiêu hiệu năng đều là chỉ tiêu CPU

> **Toàn bộ chỉ tiêu hiệu năng của đồ án là chỉ tiêu đo trên CPU.**

Máy thực hiện chạy Windows 11, Python 3.13, **không có GPU CUDA** (Intel UHD 770 tích hợp, PyTorch không dùng được để tăng tốc). Huấn luyện trên GPU miễn phí Colab/Kaggle, nhưng **suy luận và buổi bảo vệ chạy trên CPU máy cá nhân**. Đây là **ràng buộc thiết kế**, không phải hạn chế tạm thời, vì bốn lẽ: nó cố định trong toàn bộ vòng đời và tại chính buổi bảo vệ; nó đổi _bậc độ lớn_ của độ trễ (ở 20 ms/khung, video đồng bộ và webcam xử lý mọi khung là hợp lý — ở mốc thực tế 400 ms cả hai bất khả thi, trực tiếp sinh ra hai quyết định kiến trúc: video bất đồng bộ AD-02 và webcam bỏ khung hàng đợi một khe); nó chi phối chọn biến thể mô hình (n/s/m), biến thể OCR (mobile/server), kích thước ảnh và **nền tảng suy luận** — benchmark chính thức trên CPU i7-13700H cho thấy YOLOv8n qua ONNX Runtime nhanh hơn PyTorch khoảng **3,73 lần** (104,61 → 28,02 ms) [23]<!-- ultralytics_2026_openvinoexport -->, lợi ích lớn nhất đúng ở phân khúc mô hình nhỏ [24]<!-- onnxruntime_2025_threading -->; và nó buộc phương pháp công bố chặt hơn — quy tắc CON-06: **mọi số liệu hiệu năng phải kèm model CPU, số luồng, kích thước ảnh, nền tảng suy luận và cỡ mẫu đo**. Các chỉ tiêu độ trễ vì vậy "rộng rãi" hơn văn liệu quốc tế đo trên GPU — đó là trung thực về điều kiện đo, không phải dễ dãi.

> **Cảnh báo trích dẫn.** Bảng benchmark nguồn có cột mAP nhưng đo trên tập `coco8` chỉ **8 ảnh**, không có ý nghĩa thống kê; nhóm thực hiện chỉ dùng cột thời gian và cố ý lược bỏ cột độ chính xác.

#### b) Chỉ tiêu định lượng nhóm hiệu năng và nhóm độ chính xác

<!-- {{T4.1}} chi tieu phi chuc nang dinh luong NFR-P va NFR-A -->

**Bảng 4.1.** Chỉ tiêu phi chức năng định lượng: hiệu năng (NFR-P) và độ chính xác (NFR-A)

| Mã         | Chỉ tiêu                                                  | Mục tiêu              | Ngưỡng tối thiểu |
| ---------- | --------------------------------------------------------- | --------------------- | ---------------- |
| **NFR-P1** | Độ trễ toàn trình một ảnh (p95)                           | ≤ 800 ms              | ≤ 1500 ms        |
| **NFR-P2** | Tốc độ khung hình thời gian thực (webcam — đo ở tầng API) | ≥ 5 FPS hiệu dụng     | ≥ 3 FPS          |
| **NFR-P3** | Tốc độ xử lý video                                        | ≥ 0,3× thời gian thực | ≥ 0,15×          |
| **NFR-P4** | Thời gian nạp mô hình khi khởi động                       | ≤ 15 giây             | ≤ 30 giây        |
| **NFR-P5** | Overhead của tầng API (không tính suy luận)               | ≤ 50 ms               | ≤ 100 ms         |
| **NFR-P6** | Thời gian truy vấn lịch sử (10.000 bản ghi)               | ≤ 500 ms              | ≤ 1000 ms        |
| **NFR-P7** | Bộ nhớ thường trú của máy chủ                             | ≤ 2 GB                | ≤ 4 GB           |
| **NFR-A1** | mAP@0.5 của bộ phát hiện                                  | ≥ 0,90                | ≥ 0,85           |
| **NFR-A2** | mAP@0.5:0.95 của bộ phát hiện                             | ≥ 0,65                | ≥ 0,55           |
| **NFR-A3** | Precision / Recall phát hiện                              | ≥ 0,92 / ≥ 0,90       | ≥ 0,88 / ≥ 0,85  |
| **NFR-A4** | Độ chính xác OCR mức ký tự (1 − CER)                      | ≥ 0,95                | ≥ 0,92           |
| **NFR-A5** | Độ chính xác biển đầy đủ **trước** hậu xử lý              | ≥ 0,85                | ≥ 0,80           |
| **NFR-A6** | Độ chính xác biển đầy đủ **sau** hậu xử lý                | ≥ 0,90                | ≥ 0,85           |
| **NFR-A7** | Độ chính xác toàn trình (ảnh vào → biển đúng)             | ≥ 0,88                | ≥ 0,82           |

**Phương pháp đo NFR-P:** P1 trên 100 ảnh test, báo p50/p95/p99; P2 đo liên tục 60 giây; P3 bằng video 60 giây phải xong trong ≤ 200 giây; P4 từ khởi động đến khi `/health` sẵn sàng; P5 là hiệu tổng thời gian request trừ thời gian đường ống; P6 có phân trang và bộ lọc trên 10.000 bản ghi; P7 theo dõi RSS khi chạy tải liên tục.

NFR-P1 xuất phát từ **phân rã ngân sách độ trễ**: giải mã ~50 ms; phát hiện @640 px ~150 ms; cắt ~30 ms; OCR mỗi biển ~120 ms; hậu xử lý < 5 ms; ghi CSDL ~50 ms — **tổng ~405 ms cho ảnh một biển**; ngân sách 800 ms để dự phòng ảnh nhiều biển và biến động tải. Đây là **ước lượng thiết kế, không phải kết quả đo** (số đo ở Chương 5). Ngân sách lập cho nền tảng suy luận mặc định đã chốt ở mục 3.4 là **ONNX Runtime** — điểm đã đổi so với AD-05 sơ bộ. Nếu vượt ngưỡng, thứ tự giảm tải định trước: (1) INT8 OpenVINO; (2) giảm ảnh xuống 480 px; (3) biến thể OCR nhẹ hơn — chỉ hạ chỉ tiêu **sau khi** thử hết ba phương án.

Cặp NFR-A5/A6 đặt **tách bạch** có chủ đích: hiệu số giữa chúng là đóng góp định lượng của khối hậu xử lý — đo được nhờ quyết định lưu cả chuỗi thô lẫn chuỗi sửa ở tầng dữ liệu (4.7.2b). Bổ sung: **NFR-A8** — báo cáo độ chính xác **tách riêng biển một dòng và hai dòng**, căn cứ số liệu 94,3% / 45,7% **đo trên bộ RodoSol-ALPR (Brazil)** đã dẫn ở 4.1.1, vì một con số tổng thể sẽ che giấu đúng chế độ thất bại cần phân tích; **NFR-A9** — báo cáo theo điều kiện ảnh nếu bộ dữ liệu có nhãn phù hợp.

#### c) Các nhóm yêu cầu phi chức năng còn lại

**NFR-R:** không sập với đầu vào hỏng/độc hại (100% lỗi bị bắt); ảnh không biển trả rỗng hợp lệ HTTP 200; video thất bại không để lại rác; tỉ lệ thành công chạy liên tục một giờ ≥ 99%; CSDL sống sót khởi động lại. **NFR-U:** lượt nhận dạng đầu tiên ≤ 3 nhấp chuột, không cần tài liệu; thao tác > 500 ms có phản hồi trực quan; thông báo lỗi tiếng Việt nêu nguyên nhân và cách khắc phục; dùng được từ 1366×768; tương phản WCAG AA ≥ 4,5:1. **NFR-M:** mã AI tách hoàn toàn khỏi mã API (M1); bao phủ test tầng nghiệp vụ ≥ 70% (M2); type hint + docstring (M3); không hard-code đường dẫn (M4); thay bộ OCR không sửa tầng API (M5); lint tự động (M6) — M1 và M5 **là yêu cầu kiến trúc**, lý do tồn tại của tầng AI độc lập (4.2). **NFR-S:** kiểm tra magic bytes; chống path traversal bằng tên tệp UUID; giới hạn kích thước phía máy chủ; CORS không ký tự đại diện; không log dữ liệu nhạy cảm; truy vấn tham số hoá qua ORM. **NFR-C:** chạy Windows/Linux/macOS qua Docker một lệnh; **không cần GPU là chế độ mặc định**; Chrome/Edge/Firefox; cài từ máy sạch ≤ 15 phút. **NFR-SC:** ổn định ≥ 5 yêu cầu đồng thời; không suy giảm ở 100.000 bản ghi; video nền không chặn yêu cầu khác.

> **Giới hạn đã biết cần công bố.** SQLite chỉ cho **một tiến trình ghi tại một thời điểm** — chấp nhận được ở quy mô đồ án, nhưng phải nêu trong phần Hạn chế kèm hướng khắc phục (PostgreSQL) nếu triển khai thực tế.

---

---

## Phụ lục O. Tệp cấu hình gốc, báo cáo đo và mã nguồn

Phụ lục này giữ **hiện vật thô** — thứ cần để tái lập chứ không cần để đọc hiểu.
Phụ lục B trình bày siêu tham số dưới dạng bảng đã biên tập; mục O.1 dưới đây là
**nguyên văn tệp máy sinh**, vì một bảng biên tập lại không thay được tệp gốc khi
có người muốn chạy lại đúng lượt huấn luyện ấy.

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
| `07-benchmark-optimized.json`      | _(chưa chạy)_ So sánh PyTorch ↔ ONNX Runtime ↔ OpenVINO                         |    5.6.3     |

Thư mục còn **23 tệp JSON khác** thuộc các lượt đo trung gian đã bị lượt sau
thay thế; chúng được giữ lại trong kho để đối chiếu lịch sử chứ không được trích
dẫn trong quyển. Nguyên tắc áp dụng xuyên suốt: **một số liệu chỉ được đưa vào**
**quyển khi tệp sinh ra nó còn trong kho và chạy lại được.**

---
