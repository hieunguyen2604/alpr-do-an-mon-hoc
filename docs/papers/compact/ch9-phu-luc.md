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

| Thành phần | Ngôn ngữ | Số tệp | Số dòng |
|---|---|---:|---:|
| `ai/` — tầng trí tuệ nhân tạo | Python | 31 | 16.949 |
| `scripts/` — công cụ dựng dữ liệu, đo đạc, xuất tài liệu | Python | 32 | 17.395 |
| `tests/` — kiểm thử tự động | Python | 23 | 9.246 |
| `backend/` — dịch vụ web và truy cập dữ liệu | Python | 29 | 9.992 |
| `frontend/` — giao diện người dùng | TypeScript / TSX / CSS | 52 | 10.471 |
| `ai/` — cấu hình huấn luyện và bộ dữ liệu | YAML | 3 | 328 |
| `deployment/`, `docker-compose.yml` | Dockerfile / YAML | 5 | 780 |
| **Tổng** | | **178** | **65.805** |

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

| Nhóm | Tham số | Giá trị | Ghi chú |
|---|---|---:|---|
| Mô hình | `model` | `yolo11n.pt` | Khởi tạo từ trọng số tiền huấn luyện COCO |
| | Số tham số | 2.590.035 | Biến thể nano — do ràng buộc CPU |
| Dữ liệu | `data` | `yolo_v3/data.yaml` | Split v3 |
| | `imgsz` | 640 | Đúng độ phân giải mà NFR-A1/A2 đặt chỉ tiêu |
| | `fraction` | 1,0 | Dùng toàn bộ dữ liệu |
| Lịch huấn luyện | `epochs` | 20 | |
| | `patience` | 20 | Dừng sớm không kích hoạt |
| | `batch` | 8 | Giới hạn bởi RAM và tốc độ CPU |
| | `close_mosaic` | 10 | Tắt mosaic trong 10 epoch cuối |
| Tối ưu hoá | `optimizer` | AdamW | |
| | `lr0` / `lrf` | 0,001 / 0,01 | Tốc độ học đầu và hệ số cuối |
| | `cos_lr` | `true` | Lịch cosine |
| | `momentum` | 0,937 | |
| | `weight_decay` | 0,0005 | |
| | `warmup_epochs` | 3,0 | |
| Trọng số mất mát | `box` / `cls` / `dfl` | 8,0 / 0,5 / 1,5 | |
| Tăng cường dữ liệu | `hsv_h` / `hsv_s` / `hsv_v` | 0,015 / 0,7 / 0,4 | |
| Thiết bị | `device` | `cpu` | Không có GPU CUDA (ràng buộc CON-02) |

**Hai giá trị đáng giải thích thêm.** `batch = 8` không phải lựa chọn tối ưu mà
là giới hạn phần cứng; `epochs = 20` là con số bị ngân sách thời gian CPU quyết
định chứ không phải điểm hội tụ — chi phí và hệ quả của cả hai trình bày ở mục
4.5.1 và 3.6.

Cấu hình tinh chỉnh bộ nhận dạng ký tự (30 epoch, 6.672 mẫu, bộ ký tự 36) trình
bày tại mục 4.5.3 cùng kết quả đo bốn cấu hình. **Bản giao hàng không dùng mô hình
tinh chỉnh** — lý do ở cùng mục.

---

## Phụ lục C. Bộ dữ liệu

### C.1. Nguồn và giấy phép — nhánh phát hiện biển số

**Bảng C.1.** Bảy bộ dữ liệu đã hợp nhất, kèm giấy phép và số ảnh còn lại

| # | Bộ (slug) | Nguồn | Giấy phép | Vào gộp | Còn lại |
|---|---|---|---|---:|---:|
| 1 | `roboflow_school_fuhih` | Roboflow `school-fuhih/vietnamese-license-plate-tptd0` v1 | CC BY 4.0 | 8.357 | 6.868 |
| 2 | `hf_vn_plates_segment` | HuggingFace `hoanglvuit/Vietnam_License_Plate_Segment_Datasets` | ⚠️ chưa xác nhận | 4.578 | 4.375 |
| 3 | `roboflow_traffic_camera` | Roboflow `traffic-camera/vietnam-license-plate-hayn8` v4 | CC BY 4.0 | 3.843 | 3.162 |
| 4 | `roboflow_eric_nguyen` | Roboflow `eric-nguyen-knfxn/vietnam-license-plate-curhr` v1 | CC BY 4.0 | 840 | 353 |
| 5 | `roboflow_demo_tracking` | Roboflow `demo-tracking/license-plate-vietnam-car` v2 | CC BY 4.0 | 236 | 235 |
| 6 | `roboflow_cuong_ta` | Roboflow `cuong-ta-ulxex/vietnamese-car-license-plate` v1 | Public Domain *(người đăng tự khai)* | 8.254 | 140 |
| 7 | `roboflow_tran_ngoc_xuan_tin` | Roboflow `tran-ngoc-xuan-tin-k15-hcm-dpuid/vietnam-license-plate-h8t3n` v1 | CC BY 4.0 | 1.005 | 0 |
| | **Tổng** | | | **27.113** | **15.133** |

**Ghi công theo giấy phép.** Năm bộ ở trên phát hành theo **CC BY 4.0**, bắt buộc
ghi công tác giả — bảng này chính là phần ghi công đó. Một bộ được người đăng tự
khai **Public Domain**, nhưng đồ án **không khẳng định** đó là Public Domain thật
vì ảnh nguồn có dấu hiệu là ảnh báo chí. Một bộ trên HuggingFace **chưa xác nhận
được giấy phép**; nó đóng góp 28,91% corpus nên đây là rủi ro pháp lý phải nêu
chứ không phải chi tiết bỏ qua được.

**Bộ thứ bảy còn lại 0 ảnh** sau khử trùng lặp — toàn bộ 1.005 ảnh của nó trùng
với ảnh đã có ở các bộ khác. Con số "hợp nhất từ 7 bộ" vì vậy phải đọc là **6
nguồn nguyên tố**, và điều này được nêu nhất quán ở mục 4.4.2 và 6.3.1.

### C.2. Nguồn nhãn chuỗi ký tự — nhánh nhận dạng

**Bảng C.2.** Hai bộ nhãn mức ký tự

| Bộ | Nguồn | Giấy phép | Chuỗi dùng được |
|---|---|---|---:|
| `roboflow_ocr_plate` | Roboflow, nhãn mức ký tự | CC BY 4.0 | 2.650 |
| `roboflow_ocr_conversion` | Roboflow, nhãn mức ký tự | CC BY 4.0 | 151 |
| | | **Tổng** | **2.801** |

Toàn bộ số liệu độ chính xác OCR trong Chương 5 đo trên 2.801 mẫu này. Giới hạn
phạm vi kết luận kéo theo (97,68% mẫu là biển trắng) nêu tại Phụ lục G.2.7.

### C.3. Khử trùng lặp và chia tập

**Bảng C.3.** Hai phép khử trùng lặp, hai mẫu số khác nhau

| Phép đo | Mẫu số | Ngưỡng Hamming | Ảnh có thể loại | Tỷ lệ | Đã xoá thật |
|---|---:|---:|---:|---:|---|
| (a) Trên toàn bộ ảnh của 7 bộ vào hợp nhất | 27.111 | 5 | 11.978 | 44,2% | Rồi |
| (b) Trên corpus đã gộp `merged_v2` còn lại | 15.133 | 10 | 7.227 | 47,8% | Chưa |

Nguồn: `datasets/reports/v2/deduplication_report.json` và
`datasets/reports/v3/deduplication_report.json`.

Hai con số 44,2% và 47,8% **không cộng được với nhau** vì mẫu số khác nhau — đây
là chỗ rất dễ đọc nhầm và được phân tích riêng ở mục 5.3.2. Bài học về giới hạn
của băm tri giác — nó tóm tắt bố cục khung ảnh chứ không tóm tắt chiếc xe — trình
bày ở mục 4.4.3.

---

### C.4. Phân bố nguồn dữ liệu giữa các split

Cột `source_dataset` trong `split_manifest.csv` chứa một **tập xuất xứ** ngăn bằng `|`: một ảnh có thể đến từ nhiều nguồn, nên v3 gồm **16 tổ hợp xuất xứ** dựng từ đúng **6 nguồn nguyên tố**. Cộng dồn số đếm của 6 nguồn cho **33.828**, vượt xa 15.133 vì ảnh đa nguồn bị đếm nhiều lần — **không được dùng 33.828 làm mẫu số**. Toàn tập chia **15.133 = 10.592 / 3.027 / 1.514**, tức **70,0% / 20,0% / 10,0%**; bảng đầy đủ 16 tổ hợp ở `split_manifest.csv` và Phụ lục C. Phải phân biệt ba con số nguồn: **9 bộ đã tải về**, **7 bộ vào hợp nhất detection**, **6 nguồn nguyên tố**.

**Tiêu chí đọc:** tỉ lệ một nguồn trong tập test lệch quá 10 điểm phần trăm so với tỉ lệ tổng thể (10,0%) thì phải nêu tên. Hai tổ hợp vượt: `roboflow_traffic_camera` thuần (**2.582** ảnh) có **20,3%** rơi vào test — gấp đôi tỉ lệ tổng thể; `roboflow_school_fuhih|roboflow_traffic_camera` (**250** ảnh) có tới **69,6%**. Nghĩa là **tập test nghiêng về ảnh camera giao thông** — góc rộng, biển nhỏ — nên khi đọc mAP theo dải kích thước (5.4.4) phải nhớ đối tượng nhỏ trong tập test tập trung ở một nguồn. Hệ quả của việc các tổ hợp nhỏ khó chia đều, ghi nhận như yếu tố đọc kèm chứ không phải khiếm khuyết vô hiệu hoá kết quả.

**Một bộ dữ liệu dư thừa hoàn toàn.** `roboflow_tran_ngoc_xuan_tin` vào hợp nhất với **1.005 ảnh**, ra khỏi khử trùng lặp chéo bộ với **0 ảnh — loại 100,0% (1.005/1.005)**: cả 1.005 ảnh đều dính ít nhất một cặp gần trùng (**1.577** cặp với `roboflow_school_fuhih`, **1.569** với `roboflow_cuong_ta`, **8** với `hf_vn_plates_segment`, **35** cặp nội bộ); kiểm chứng độc lập: `split_manifest.csv` không chứa tên bộ này lần nào. Đây là **bằng chứng định lượng** cho cảnh báo ở Phase 1 rằng các bộ Roboflow tái sử dụng ảnh của nhau rất nặng, và là lý do **không được cộng dồn `expected_images` để suy ra quy mô thật** ([`02-dataset-report.md`](../reports/02-dataset-report.md) mục 5.3.1).

## Phụ lục D. Hướng dẫn cài đặt và chạy

### D.1. Yêu cầu

| Hạng mục | Yêu cầu |
|---|---|
| Hệ điều hành | Windows 10/11, macOS hoặc Linux |
| Docker | Docker Engine 24+ và Docker Compose v2 |
| Bộ nhớ | Tối thiểu 4 GB RAM trống |
| Đĩa | Khoảng 6 GB cho image và dữ liệu |
| GPU | **Không cần** — toàn hệ thống chạy trên CPU |

### D.2. Chạy bằng Docker Compose (khuyến nghị)

```bash
git clone <địa chỉ kho mã>
cd vn-license-plate-recognition
docker compose up -d --build
```

Sau khi các container khởi động, mở trình duyệt tại:

| Địa chỉ | Nội dung |
|---|---|
| `http://localhost:5173` | Giao diện người dùng |
| `http://localhost:8000/docs` | Tài liệu API (Swagger UI, tự sinh) |
| `http://localhost:8000/health` | Trạng thái hệ thống |

Kiểm tra hệ thống đã nạp được mô hình:

```bash
curl http://localhost:8000/health
```

Trường `model_loaded` phải trả về `true`. Nếu trả về `false`, hệ thống vẫn chạy
nhưng mọi yêu cầu nhận dạng sẽ trả lỗi thay vì trả kết quả bịa — cơ chế
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

> **Lưu ý về môi trường ảo.** Đồ án dùng **ba môi trường ảo Python tách biệt**,
> không phải một. Lý do bắt buộc phải tách — xung đột phiên bản giữa hai framework
> học sâu — trình bày ở mục 4.3.2. Gộp chúng lại sẽ hỏng.

### D.4. Biến môi trường đáng chú ý

| Biến | Mặc định | Tác dụng |
|---|---|---|
| `ALPR_MODEL_PATH` | `models/best.pt` | Đường dẫn trọng số bộ phát hiện |
| `ALPR_RECTIFY_ENABLED` | `true` | Bật bước nắn hình biển nghiêng |
| `ALPR_SR_RETRY_ENABLED` | `false` | Bậc siêu phân giải — **tắt mặc định**, xem mục 5.5.7 |
| `ALPR_OCR_SKIP_DETECTION` | `false` | Bỏ bước phát hiện chữ — **tắt mặc định**, xem mục 5.6.6 |
| `ALPR_OCR_REC_MODEL_DIR` | *(rỗng)* | Thư mục mô hình nhận dạng tinh chỉnh; để rỗng là dùng mô hình gốc |

Chi tiết đầy đủ về triển khai — kiến trúc mạng Docker, các volume, cách xử lý sự
cố thường gặp và lưu ý dung lượng image — ở `deployment/README.md`.

---

## Phụ lục E. Kết quả kiểm thử

### E.1. Tổng hợp

**Bảng E.1.** Kết quả chạy bộ kiểm thử tự động

| Hạng mục | Kết quả |
|---|---|
| Số test thu thập | **1.001** |
| Đạt | **1.000** |
| `xfail` *(dự kiến hỏng, có ghi lý do)* | 1 |
| Fail | **0** |
| Skip | 0 |
| Ngày chạy | 02/08/2026 |

### E.2. Phân nhóm

| Nhóm | Kiểm chứng điều gì |
|---|---|
| Kiểm thử đơn vị | Bộ luật hậu xử lý theo vị trí, phân loại layout, chuẩn hoá chuỗi, quy tắc hiển thị |
| Kiểm thử tích hợp | Toàn bộ 10 endpoint qua HTTP thật, kèm cơ sở dữ liệu thật và migration |
| Kiểm thử kiến trúc | Ranh giới `ai/` không import `backend/` (NFR-M1) — fail nếu ai đó vi phạm |
| Kiểm thử hồi quy | Các ca lỗi đã từng xảy ra, mỗi ca một test để không tái diễn |

**Ý nghĩa của con số 0 fail cần được đọc đúng.** Nó nói rằng hệ thống làm đúng
những gì bộ kiểm thử kiểm; nó **không** nói rằng hệ thống đạt mọi chỉ tiêu. Ba
chỉ tiêu phi chức năng hiện không đạt (NFR-A5, A6, A7) và một chỉ tiêu trượt sàn
(NFR-P2) — bảng đối chiếu đầy đủ ở mục 5.7 và phân tích ở mục 5.9.2.

Báo cáo kiểm thử chi tiết theo từng nhóm: `docs/reports/07-testing-report.md`.

---

## Phụ lục F. Giao diện lập trình và cấu hình triển khai

### F.1. Danh sách endpoint

**Bảng F.1.** Mười endpoint của hệ thống

| # | Phương thức | Đường dẫn | Chức năng |
|:--:|---|---|---|
| 1 | `POST` | `/api/detect/image` | Nhận dạng biển số từ một ảnh tĩnh |
| 2 | `POST` | `/api/detect/video` | Tạo tác vụ nhận dạng trên video, xử lý nền |
| 3 | `POST` | `/api/detect/frame` | Nhận dạng một khung hình — dùng cho chế độ thời gian thực |
| 4 | `GET` | `/api/jobs/{job_id}` | Trạng thái và tiến độ của một tác vụ video |
| 5 | `GET` | `/api/history` | Danh sách lịch sử, có tìm kiếm, lọc, phân trang |
| 6 | `GET` | `/api/history/{detection_id}` | Chi tiết một lần nhận dạng |
| 7 | `GET` | `/api/history/export` | Xuất lịch sử theo bộ lọc hiện hành |
| 8 | `DELETE` | `/api/history/{detection_id}` | Xoá một bản ghi |
| 9 | `GET` | `/api/statistics` | Số liệu thống kê tổng hợp theo cửa sổ thời gian |
| 10 | `GET` | `/health` | Trạng thái hệ thống và tình trạng nạp mô hình |

Đặc tả đầy đủ — kiểu dữ liệu đầu vào, cấu trúc đầu ra, mã trạng thái và các
quyết định thiết kế API — ở mục 4.7.3. Tài liệu OpenAPI do FastAPI **tự sinh**
tại `/docs` và `/openapi.json`, nên nó không bao giờ lệch với mã nguồn.

### F.2. Cấu hình Docker Compose

**Bảng F.2.** Thành phần trong `docker-compose.yml`

| Thành phần | Loại | Vai trò |
|---|---|---|
| `backend` | dịch vụ | FastAPI + uvicorn, chạy pipeline AI trên CPU |
| `frontend` | dịch vụ | nginx:alpine — phục vụ tệp tĩnh và reverse proxy sang backend |
| `alpr-net` | mạng | Mạng nội bộ giữa hai dịch vụ |
| `alpr-data` | volume | Cơ sở dữ liệu SQLite — dữ liệu sống qua lần khởi động lại |
| `alpr-model-cache` | volume | Bộ nhớ đệm trọng số PaddleOCR — tránh tải lại mỗi lần dựng |

Ngoài hai volume có tên ở trên, thư mục `./storage` (ảnh và video đã tải lên) và
`./models` (trọng số bộ phát hiện, gắn **chỉ đọc**) được gắn trực tiếp từ máy chủ.

Bộ ba tệp triển khai: `deployment/docker/Dockerfile.backend` (build hai giai
đoạn), `Dockerfile.frontend` (build rồi phục vụ tĩnh) và `nginx.conf`. Phân tích
từng tệp ở mục 4.9.

---

## Phụ lục G. Kết quả, hạn chế và hướng phát triển — phân tích chi tiết

Chương 6 trình bày kết luận ở dạng cô đọng: bảng chỉ tiêu, bảng hạn chế, bảng
hướng phát triển. Phụ lục này giữ **nguyên văn phần phân tích** của từng mục —
mức nghiêm trọng, bằng chứng số, điều kiện khắc phục.

Tách ra đây để thân bài gọn mà **không phải cắt bằng chứng**: một hạn chế nêu
suông không kèm số đo thì hội đồng không kiểm được, mà kiểm được hay không mới
là thứ phân biệt một lời thừa nhận với một lời nói cho có.

---

### G.1. Các kết quả đạt được — phân tích chi tiết

#### G.1.1. Một hệ thống hoàn chỉnh, chạy được, xác minh bằng HTTP thật


Backend FastAPI, frontend React, pipeline AI và lớp dữ liệu SQLite/SQLAlchemy đóng gói Docker, khởi động một lệnh trên máy sạch. Kiểm chứng: 10 thao tác API phản hồi đúng qua HTTP sống; `/health` báo `model_loaded: true` với engine thật; stack Docker kiểm bằng `curl` từ **ngoài** container.


#### G.1.2. Bộ phát hiện đạt toàn bộ chỉ tiêu với biên rộng


Trên tập test v3 (1.514 ảnh, 1.611 đối tượng), YOLO11n [16]<!-- jocher_2024_yolo11 --> vượt **cả bốn** chỉ tiêu ở mức *mục tiêu* chứ không chỉ *ngưỡng tối thiểu* (Bảng 6.1), mAP@0.5 tới **0,9829**. Chênh lệch hai layout chỉ **2,09 điểm** — nếu toàn trình kém trên biển hai dòng thì lỗi **không** ở khâu phát hiện. Điểm yếu duy nhất (T5.4c): dải "rất nhỏ" (dưới 0,5% diện tích ảnh) chỉ đạt **0,8553**. Điều kiện đọc kèm: bài toán **một lớp**, nên mAP@0.5 cao là bình thường.


#### G.1.3. Đo được đóng góp định lượng của khối hậu xử lý


**Đóng góp khoa học riêng thứ nhất.** Phần lớn công trình ALPR chỉ mô tả hậu xử lý định tính; đồ án đo tách bạch trên 2.801 biển có nhãn chuỗi: A5 = 0,6373, A6 = 0,7512, **A6 − A5 = +11,39 điểm phần trăm**. Bộ luật sửa đúng **319 biển**, làm hỏng **0 biển**, dồn gần trọn vào biển hai dòng (**+13,97** so với **+1,23 điểm**); cải thiện thuần một chiều chứng tỏ bộ luật đủ bảo thủ. Đóng góp bị chặn vì nút thắt ở tầng OCR: luật không với tới chuỗi sai nhiều ký tự do engine đọc hụt cả cụm.


#### G.1.4. Đo được rủi ro R-04 bằng số liệu Việt Nam thật


**Đóng góp khoa học riêng thứ hai.** Rủi ro R-04 — "pipeline OCR dựng sẵn gãy trên biển hai dòng" — vốn *định tính* từ Phase 0, nay đo được trên dữ liệu Việt Nam (T5.5c). Trên 567 biển một dòng so với 2.234 biển hai dòng, A6 đạt 0,9541 so với 0,6996 — chênh **25,45 điểm** (chênh 1 − CER và A5 lần lượt 5,81 và 38,18 điểm). Biển **một dòng về cơ bản đã giải xong** (A6 vượt mục tiêu 0,90); toàn bộ khoảng thiếu nằm ở biển **hai dòng**, chiếm **79,8%** tập có nhãn chuỗi — phản ánh 77 triệu xe máy Việt Nam [1]<!-- dantri_2024_77trieuxemay -->. Chênh lệch này **cùng bậc độ lớn** với mốc quốc tế: Laroca và cộng sự (VISAPP 2022) đo chênh **48,6 điểm** giữa biển một dòng (94,3%) và hai dòng (45,7%) trên bộ dữ liệu **RodoSol-ALPR của Brazil** [7]<!-- laroca_2022_crossdataset -->.

> **Cảnh báo trích dẫn bắt buộc.** Cặp số 94,3% / 45,7% và chênh 48,6 điểm đo trên **RodoSol-ALPR (Brazil)** [7]<!-- laroca_2022_crossdataset -->, **không phải** số liệu Việt Nam — chỉ là *analogue định lượng* về độ khó của biển hai dòng. Con số 25,45 điểm mới là số đo Việt Nam của đồ án.

Giá trị học thuật: chưa nghiên cứu biển số Việt Nam công khai nào công bố hai con số một dòng / hai dòng tách bạch trên cùng một hệ thống; kết luận — biển hai dòng là *đặc tính có cấu trúc của bài toán* — đặt nền cho 6.4.1, nhất quán với dòng nghiên cứu coi tính độc lập layout là yêu cầu thiết kế [23]<!-- laroca_2021_layout -->.


#### G.1.5. Bộ nhận màu nền biển đạt 97,89% — một nguồn bằng chứng mà chuỗi ký tự không thể mang


**Đóng góp kỹ thuật riêng thứ ba.** Theo Thông tư 79/2024/TT-BCA, biển vàng kinh doanh vận tải mang **đúng cùng bố cục ký tự** với biển trắng cá nhân; biển ngoại giao lại nền trắng — chỉ *cặp* (chuỗi, màu) mới định danh được loại phương tiện. Bộ phân loại (`ai/inference/plate_color.py`) đọc biểu đồ HSV, trả `unknown` khi không chắc chắn. Đo trên bộ `nguyenluanai/license-plate-color` v4 (CC BY 4.0) — bộ mà bộ phân loại **chưa từng được hiệu chỉnh theo**: vàng **98,56%** (694 ảnh), trắng **97,40%** (808), xanh **96,83%** (63), **tổng 97,89% trên 1.565 ảnh** (`19-color-accuracy.json`); 542 ảnh bị loại là toàn bộ lớp `bien_unknown` — ảnh mà chính người gán nhãn cũng không đọc được màu nền.

Ràng buộc an toàn khi hợp nhất hai nguồn: màu chỉ được nâng cấp một ứng viên mà bộ luật chuỗi đã coi là hợp lý và tự đánh dấu nhập nhằng, nên **biển quân đội bị đọc nhầm màu thì vẫn là biển quân đội**. Cùng đợt, họ biển (chín giá trị `PlateKind`) và chuỗi hiển thị đúng định dạng được giữ tới CSDL, chữa lỗi biển đỏ đọc đúng từng bị hiển thị "Sai định dạng biển số". Hạn chế: bộ dữ liệu đo **không chứa biển đỏ và biển ngoại giao** (6.3.8).


#### G.1.6. Một quy trình đánh giá có kiểm chứng — bản thân tính trung thực là một kết quả


Đóng góp cuối là **cách các con số được kiểm tra**: năm lần quy trình tự bắt lỗi của chính nó, cả năm đều được ghi lại. **(1)** Rò rỉ train↔test: split cũ có hàng nghìn cặp gần trùng vắt ranh giới; nâng ngưỡng gộp 5 → 10, chia lại thành v3 (6.3.2). **(2)** Một lập luận vòng tròn trong chính phép kiểm đó: 0 cặp vắt split ở ngưỡng Hamming 10 là **hệ quả định nghĩa**, không phải bằng chứng sạch. **(3)** phash ở cài đặt này chỉ sinh khoảng cách Hamming **chẵn**, nên ngưỡng lẻ vô nghĩa. **(4)** Bộ đo OCR **không đi qua đường mã sản phẩm**: `ai/evaluation/ocr_accuracy.py` không dựng `ALPRPipeline`, nên logic tầng điều phối vô hình với con số công bố; bản sửa tách bước cứu biển hai dòng thành hai hàm dùng chung; khoảng cách này không gây lỗi và **chưa có cơ chế tự động nào canh giữ nó**. **(5)** Một giả thuyết sửa lỗi hợp lý — đọc riêng từng nửa biển hai dòng rồi nối chuỗi — bị chính dữ liệu bác bỏ áp đảo (`15-two-line-ab.json`); bản sửa cuối giữ thiết kế ghép hiện hành, đo 900 biển không ca hỏng nào. Ngoài ra quy trình còn **bác bỏ một con số độ trễ cũ** (6.3.4). **Một chương đánh giá không kể lại lần nào nó tự nghi ngờ chính mình là một chương đã tự tước bỏ khả năng bị kiểm chứng.**

---


---

### G.2. Các hạn chế của đồ án — phân tích chi tiết

#### G.2.1. Hạn chế lớn nhất: OCR biển hai dòng còn yếu, kéo E2E chưa đạt


*Mức nghiêm trọng: cao — hạn chế trung tâm của toàn đồ án.* NFR-A5 = **0,6373** (thiếu 16,27 điểm so với ngưỡng 0,80); NFR-A6 = **0,7512** (thiếu 9,88 so với 0,85); NFR-A7 = **0,5552** (thiếu 26,48 so với 0,82); NFR-A4 = **0,9454**, vượt ngưỡng tối thiểu 0,92 nhưng dưới mục tiêu 0,95. **Nguyên nhân ở tầng OCR chứ không phải tầng hậu xử lý**, ba bằng chứng độc lập: *tách theo layout* (T5.5c) — toàn bộ khoảng thiếu nằm ở biển hai dòng, chiếm 79,8% tập; *phân tích lỗi* (T5.8) — 428/445 ca nhầm ký tự và **73/73** ca thiếu ký tự thuộc biển hai dòng; *đóng góp hậu xử lý bị chặn trên* (T5.5b) — ký tự bị xoá chiếm 56,8% toàn bộ lỗi, mà ký tự chưa từng được đọc ra thì **về nguyên tắc** không luật nào phục hồi được. Hướng khắc phục bắt buộc nằm ở tầng nhận dạng (6.4.1).

> **Cảnh báo hiệu lực.** A7 = 0,5552 đo trên ảnh **crop biển số**, ngoài phân bố huấn luyện của bộ phát hiện, nên tỉ lệ bỏ sót 11,96% bị thổi phồng — **cận dưới bi quan** (5.5.5). Đo A7 đúng cách đòi hỏi tập test hiện trường có nhãn chuỗi, việc chưa làm được (6.4.3).


#### G.2.2. Rò rỉ dữ liệu tồn dư không khử được bằng băm tri giác


*Mức nghiêm trọng: cao.* Tại ngưỡng Hamming **12** vẫn còn **791 cặp** train↔test gần trùng, tại ngưỡng **15** là **3.529 cặp**. Nghiêm trọng hơn là rò rỉ **ngữ nghĩa** không ngưỡng phash nào bắt được: cùng một xe ở góc khác mang cùng biển số nhưng khoảng cách Hamming lớn. *Đã áp dụng:* nâng ngưỡng gộp 5 → 10, đo rò rỉ ở nhiều ngưỡng. *Chưa áp dụng được:* chia split theo nhóm biển số — bất khả thi vì phần lớn corpus thiếu nhãn chuỗi. **Hệ quả bắt buộc nêu khi bảo vệ: mọi chỉ số ở tầng phát hiện và OCR phải được coi là cận trên lạc quan.**


#### G.2.3. Tập test không xuyên bộ dữ liệu, nên mAP lạc quan hơn khi triển khai


*Mức nghiêm trọng: cao.* Train và test lấy từ cùng sáu nguồn nguyên tố, nên thiết lập chỉ đo tổng quát hoá *trong phân bố*. Độ chính xác ALPR sụt đáng kể khi đánh giá xuyên bộ dữ liệu [7]<!-- laroca_2022_crossdataset -->, nên mAP@0.5 = 0,9829 gần như chắc chắn lạc quan hơn thực tế. *Giảm thiểu trong khuôn khổ đồ án: không có*; cách đúng ở G.3.2.


#### G.2.4. Độ trễ — đạt ngưỡng tối thiểu, và mức vượt mục tiêu là một đánh đổi có chủ ý


p95 = **1.143,10 ms** — dưới sàn 1.500 ms nhưng vượt mục tiêu 800 ms 1,43 lần; trung vị **405,77 ms** (100 ảnh test v3, máy rảnh). **Thoái lui có chủ ý:** tắt bậc thang thử-lại đưa p95 về **866,3 ms** nhưng mất 34 biển đọc thêm (+0,75 điểm A6); chi phí dồn vào đuôi vì bậc thang chỉ chạy sau khi lần đọc đầu thất bại. Bật cả ba biến thể: p95 **1.514,26 ms**, vượt cả sàn; riêng bậc **siêu phân giải** chiếm hơn nửa (+319 ms p95) mà không mua được biển nào, nên tắt mặc định — số 0 ấy là **số 0 cấu trúc** (cổng chỉ mở cho vùng cắt dưới 200 px, 0/120 mẫu lọt): "chi phí đã đo, lợi ích chưa ai đo được". Một báo cáo trước ghi p95 = **5.857 ms**; con số đó đã bị **bác bỏ** vì điều kiện đo bị nhiễm (5.6.1). Ngân sách thật (T5.6b): OCR **64,3%**, phát hiện **34,0%**; hướng tối ưu đúng là **giảm số lần phải thử lại** (6.4.1).


#### G.2.5. Một yêu cầu mức *Must* (FR-4.1) đã bị đưa ra khỏi phạm vi


*Mức nghiêm trọng: trung bình. Hạn chế duy nhất phát sinh từ một **quyết định** chứ không từ giới hạn kỹ thuật.* Ngày 2026-07-20 giao diện thu gọn hai đợt còn **ba trang**: FR-3.1, FR-3.4 M → W; **FR-4.1 M → W**; FR-4.2 S → W; bảng MoSCoW từ 22/7/3/2 sang **21 Must / 6 Should / 3 Could / 4 Won't** trên 34 yêu cầu. **FR-4.1 là yêu cầu *Must* đầu tiên và duy nhất bị đưa ra khỏi phạm vi**; tiêu chí thành công số 1 ở mục 1.2.3 chỉ đúng theo bộ **21** *Must* sau thay đổi. Nhưng **phần mất đi là màn hình hiển thị, không phải năng lực hệ thống**: `GET /api/statistics` vẫn phục vụ và vẫn có kiểm thử tích hợp; FR-4.3–FR-4.8 không đổi. *Đánh đổi:* gỡ `recharts`, gói tải về giảm ~730 KB → **328,8 KB (−55%)**. *Giảm thiểu:* mã hai trang giữ có chủ đích (6.4.6).


#### G.2.6. SQLite chỉ cho phép một tiến trình ghi tại một thời điểm


*Mức nghiêm trọng: thấp trong phạm vi đồ án.* SQLite khoá ghi mức toàn tệp. Với một người vận hành (giả định A-04) đây không phải nút thắt — hệ thống ổn định ở 10 yêu cầu đồng thời, soak 100%; đa người dùng ghi đồng thời thì giới hạn thành thực; hướng khắc phục: PostgreSQL (6.4.7).


#### G.2.7. Bộ dữ liệu lệch nặng về biển trắng, nên kết luận về độ chính xác OCR chỉ áp cho biển trắng


*Mức nghiêm trọng: cao. Hạn chế này quy định **phạm vi hiệu lực** của mọi con số OCR trong quyển.* Phân bố của **2.801 ảnh có nhãn ký tự** — tập sinh ra NFR-A4 đến A7 (`17-plate-type-audit.json`): trắng **2.736 / 97,68%**; vàng **20 / 0,71%**; xanh **4 / 0,14%**; đỏ **0**; NG/QT **0**; không đọc được màu **41 / 1,46%**. Hệ quả: câu phát biểu đúng khi bảo vệ là *"1 − CER = 0,9454 trên một tập gồm 97,7% biển trắng"*, không phải *"trên biển số Việt Nam"*.

> **Cập nhật 02/08/2026 — hạn chế đã thu hẹp, nhưng chưa gỡ.** **Mọi con số A4–A7 trong quyển vẫn đo trên ngữ liệu 2.801 mẫu**; phần dưới là nguyên liệu cho lần đo sau. **(a)** Đã gộp **521 biển hiếm** từ `nguyenluanai/license-plate-color` v4 ([30-rare-plate-integration.md](../reports/30-rare-plate-integration.md)): tổng ngữ liệu **2.801 → 3.322**, vàng **20 → 476**, xanh **4 → 45**, tỷ lệ biển hiếm **0,86% → 15,7%**; biển vàng chuyển sang **đánh giá được**. **(b)** Tập ảnh toàn cảnh gán nhãn 02/08 ([34-scene-level-a7.md](../reports/34-scene-level-a7.md)) **có** biển đỏ quân đội, biển xanh, ngoại giao và sê-ri LD — quá nhỏ để công bố độ chính xác theo loại, nhưng đủ để không còn nói "bằng không". **(c)** Biển đỏ và ngoại giao vẫn không có nguồn công khai đủ lớn ([17-plate-type-dataset-survey.md](../reports/17-plate-type-dataset-survey.md)) — hạn chế **thật**, không phải "chưa tới lượt".

Hai điều dễ bị gộp khi trả lời phản biện: **hệ thống *có* năng lực phân loại loại biển** (kiểm chứng 97,89% trên 1.565 ảnh, 6.2.5) nhưng ***chưa có dữ liệu* đo độ chính xác ký tự cho biển hiếm** — vàng (n = 20) và xanh (n = 4) không có ý nghĩa thống kê, đỏ và ngoại giao không đánh giá được. **"Chưa đo được" không đồng nghĩa "không làm được", và không được trình bày như thể đã đo được** (6.4.8).


#### G.2.8. Xem trực tiếp và xử lý nền tranh chấp CPU với nhau


Trang nhận dạng video chạy đồng thời xem trực tiếp (`POST /api/detect/frame` từng khung) và tác vụ nền trên cùng CPU không GPU. Đo cùng một ảnh: **89–97 ms**/khung khi không có tác vụ nền, **230–462 ms** khi có — chậm **2,5–5 lần**. Đây là hệ quả quyết định môi trường Phase 0 (suy luận CPU), không phải lỗi lập trình; mọi số đo độ trễ của xem trực tiếp vì thế phụ thuộc việc có tác vụ nền hay không (6.4.10).

---


---

### G.3. Hướng phát triển — chi tiết kỹ thuật và chi phí

#### G.3.1. Huấn luyện lại module nhận dạng (rec) riêng cho biển số Việt Nam — hướng quan trọng nhất


Vì nút thắt nằm ở tầng OCR (6.3.1), hướng tác động lớn nhất là **thay hoặc huấn luyện lại riêng module rec** thay vì dùng trọng số PaddleOCR đa mục đích [17]<!-- cui_2026_ppocrv5 -->. Bốn cách, đầu tư tăng dần: (1) fine-tune module rec theo công thức PP-OCR trên CCPD [67]<!-- paddlepaddle_nd_plateapp -->; (2) mô hình rec hỗ trợ biển đa dòng từ thiết kế — TransLPRNet [121]<!-- arxiv_2025_translprnet --> hay LPTR-AFLNet [75]<!-- xu_2025_lptraflnet -->; (3) tách–ghép biển hai dòng trước khi đưa vào rec [64]<!-- we0091234_nd_doubleplatesplit -->; (4) mô hình chuyên biệt huấn luyện từ đầu — CRNN kèm chú ý [70]<!-- dang_2024_crnn --> hoặc pipeline chuyên xe máy Việt Nam [21]<!-- le_2023_vnmotorcycle -->. Nhờ NFR-M5, thay module rec không đụng mã tầng API.

**Ba phép đo độc lập cùng củng cố thứ tự ưu tiên này**, cả ba can thiệp ngoài mô hình nhận dạng: luật hậu xử lý **+11,39 điểm** A6 · 319 biển (6.2.3); bước cứu dòng trên **209 biển** (5.5.6); bậc thang thử-lại **+0,75 điểm** A6 · 34 biển (5.5.7). Cộng lại chúng nâng A6 từ **0,6098** lên **0,7512** không tốn một giây GPU — nhưng vẫn thiếu **9,88 điểm**, và **dư địa đã cạn**: can thiệp mới nhất chỉ mua thêm 34 biển trên 2.801. Ký tự chèn thừa gần như biến mất (giảm 88%) trong khi ký tự **bị xoá** chiếm 56,8% toàn bộ lỗi (5.5.1): lỗi đã dịch sang "ký tự chưa từng được đọc ra", thứ không tầng nào ngoài mô hình nhận dạng phục hồi được. Mục 6.4.3 là điều kiện tiên quyết.

> **Hai lượt thử đã thực hiện và đều thất bại — kết quả âm cũng là kết quả.** Lượt **thứ nhất** (28/07/2026): model đọc **0/7** ảnh demo so với **7/7** của model gốc, do tập huấn luyện **sai nhãn sinh ra một cách im lặng**: cơ chế "ảnh thay thế" kích hoạt khi không mở được ảnh gốc — mà `datasets/raw/**` nằm trong `.gitignore` — nên mọi nhãn bị ghép với ảnh của biển khác; cơ chế đã gỡ (`25-finetune-attempt-failed.md`). Lượt **thứ hai** (02/08/2026) huấn luyện thành công nhưng không được giao: qua đường ống thật nó **kém hơn model gốc** (A6 = 0,6762 so với 0,7512) — PaddleOCR đánh giá nhánh rec bằng *nguyên ảnh*, còn đường ống *phát hiện chữ trước*, nên model fine-tune đọc mảnh vụn rất kém. Bỏ bước phát hiện chữ thì nó thắng đậm (A6 = **0,8758**, hơn **12,46 điểm**), nhưng cấu hình ấy vẫn bị bác: trên bộ demo ảnh toàn cảnh qua bộ phát hiện thật, thứ tự **đảo ngược** (17/22 tụt còn 13/22), và chế độ chỉ-nhận-dạng **không thể trả chuỗi rỗng** (0/1.606 khung so với 173) nên khi bộ phát hiện bắt nhầm thì nó *bịa* ra biển. Lượt một là **lỗi dữ liệu**, lượt hai là **lỗi phép đo** (`31-detection-stage-ablation.md`).


#### G.3.2. Xây dựng tập test xuyên bộ dữ liệu


Để chữa G.2.3: giữ một nguồn không dùng huấn luyện làm tập test xuyên bộ, báo cáo song song mAP trong phân bố và xuyên bộ [7]<!-- laroca_2022_crossdataset -->; kết hợp **chia split theo nhóm biển số** để khử cả rò rỉ ngữ nghĩa ở G.2.2.


#### G.3.3. Bổ sung nhãn chuỗi biển số cho toàn tập


Hiện chỉ **2.801** biển có nhãn chuỗi trong khi corpus có 15.133 ảnh; mẫu số nhỏ này đe doạ tính hợp lệ (5.9.3) và chặn việc đo NFR-A7 trên ảnh hiện trường (6.3.1). Hướng khắc phục: gán nhãn chuỗi bán tự động — hệ thống sinh nhãn nháp, người soát lại — hoặc bổ sung dữ liệu tổng hợp theo hướng hợp nhất đa nguồn [122]<!-- arxiv_2026_multinationalfusion -->.


#### G.3.4. Tăng tốc suy luận: lượng tử hoá OCR, đóng gói ONNX/OpenVINO cả hai tầng


Phân rã ngân sách (mục 5.6.2) chỉ ra việc phải làm: OCR chiếm 64,3%, phát hiện 34,2%. **Lượng tử hoá INT8 module OCR** tận dụng tập lệnh VNNI/AVX-512 trên CPU Intel [123]<!-- onnxruntime_2025_quantization --> có đòn bẩy cao nhất. **Đóng gói cả hai tầng sang ONNX Runtime hoặc OpenVINO** [18]<!-- ultralytics_2026_openvinoexport -->[96]<!-- ultralytics_2026_export -->; hiện đường suy luận chạy PyTorch thuần, và **thí nghiệm so sánh backend (mục 5.6.3) là hạng mục đã chuẩn bị nhưng chưa chạy**. Mọi con số tăng tốc phải đo trên cùng cấu hình phần cứng và công bố kèm cấu hình.


#### G.3.5. Bám vết đối tượng qua khung hình cho video (SORT/DeepSORT)


Hệ thống hiện gộp các lần nhận dạng trùng theo **chuỗi ký tự** — gãy khi OCR đọc sai cùng một biển ở các khung khác nhau. Hướng đúng là bám vết bằng SORT/DeepSORT: gộp theo ID theo dõi, ổn định trước lỗi OCR lẻ tẻ, mở đường cho **bỏ phiếu theo thời gian**.


#### G.3.6. Khôi phục hai màn hình đã gỡ, từ lịch sử git


Hướng chữa trực tiếp 6.3.6 và **rẻ nhất trong mục 6.4** — chỉ đòi hỏi một quyết định phạm vi. Đây là *phục hồi* chứ không phải *xây mới*: năng lực máy chủ chưa bao giờ bị gỡ (`POST /api/detect/frame`, `GET /api/statistics`, `GET /health` đều có kiểm thử tích hợp); mã giao diện và hợp đồng kiểu còn nguyên trong lịch sử git. Quy trình: lấy lại tệp, nối route, chạy `tsc --noEmit` và `vite build`; thư viện biểu đồ nên chọn bản nhẹ hơn `recharts` hoặc nạp trễ. Hướng này khôi phục một chỉ tiêu đã cam kết (FR-4.1 mức Must) chứ không nâng chất lượng nhận dạng — nếu chỉ làm được một việc thì 6.4.1 vẫn đáng làm trước.


#### G.3.7. Chuyển sang PostgreSQL nếu triển khai đa người dùng


Khi có nhiều người ghi đồng thời nên chuyển sang **PostgreSQL** (khoá mức hàng). Nhờ truy cập dữ liệu đi qua SQLAlchemy 2.0 và tầng repository, việc chuyển giới hạn ở cấu hình kết nối và migration, không đụng mã nghiệp vụ hay API.


#### G.3.8. Thu thập dữ liệu cho các loại biển hiếm — điều kiện để mở rộng phạm vi kết luận


Hướng chữa trực tiếp 6.3.8, **không đòi hỏi thay đổi gì trong hệ thống**: năng lực phân loại đã kiểm chứng (6.2.5), thứ thiếu là dữ liệu để đo. Ba việc, mức khó tăng dần: (1) **biển vàng — đã có nguồn**: 694 ảnh của `nguyenluanai/license-plate-color`, tên tệp chứa sẵn chuỗi biển số; trở ngại là phép kéo méo về 640×640, xử lý bằng lấy ảnh gốc rồi soát nhãn; (2) **biển đỏ và ngoại giao**: nguồn công khai rất nhỏ — đủ cho tập kiểm thử, không đủ huấn luyện; cần gom bản tăng cường theo ảnh gốc và soát giấy phép tự khai; (3) **biển chuyên dùng (LD, DA, RM, HC, KT, CD, T)**: chưa có nguồn — thu thập tại chỗ hoặc ghi rõ ngoài phạm vi. Giá trị của hướng này là **mở rộng phạm vi mà các kết luận có hiệu lực**, không phải nâng độ chính xác.


#### G.3.9. Tách lịch chạy giữa xem trực tiếp và xử lý nền


Ba hướng cho 6.3.10: **chạy tuần tự** — hoãn tác vụ nền tới khi dừng xem trực tiếp; **giới hạn số luồng CPU của tác vụ nền**; **tách tiến trình suy luận khỏi tiến trình API** với hàng đợi có ưu tiên — đúng nhất về kiến trúc, chỉ đáng làm khi triển khai nhiều người dùng cùng 6.4.7. Mọi con số độ trễ của tính năng này bắt buộc kèm điều kiện đo.

---

---

## Phụ lục H. Đặc tả yêu cầu và thiết kế dữ liệu

Bốn mục dưới đây là **tài liệu tra cứu**, không phải mạch lập luận: đặc tả
từng use case, bảng 34 yêu cầu chức năng, bảng chỉ tiêu phi chức năng, và đặc
tả từng trường của cơ sở dữ liệu. Chương 4 nêu quyết định thiết kế và lý do;
phần liệt kê đầy đủ để ở đây.

---

### H.1. Đặc tả use case


![](figures/fig-ch4-01.png)

**Hình 4.1.** Sơ đồ use case tổng quát của hệ thống

Ba quan hệ đáng chú ý: **UC-02 «include» UC-09** — video là tác vụ nền nên bắt buộc kéo theo theo dõi tiến độ; **UC-08 «include» UC-01, UC-02** — REST API là *một lối vào khác* cho cùng nghiệp vụ; **UC-04 «extend» UC-06** — xuất kết quả là mở rộng tuỳ chọn của tra cứu. UC-03 gắn với nhà phát triển vì từ 2026-07-20 chức năng này chỉ còn lối vào qua `POST /api/detect/frame`.

**UC-01 — Nhận dạng từ ảnh tĩnh** (bắt buộc). Luồng chính: người dùng chọn tệp (JPEG/PNG/WebP/BMP); máy chủ kiểm tra bằng **magic bytes** và hạn mức kích thước, tạo `DetectionJob` loại `image`, lưu tệp với tên sinh từ UUID, gọi pipeline AI, lưu ảnh biển đã cắt, ghi mỗi biển một bản ghi `DetectionHistory`, trả bounding box, chuỗi biển số, hai độ tin cậy và thời gian xử lý. **Ngoại lệ:** A1 — tệp không phải ảnh: HTTP 400, tiến trình không sập; A2 — vượt hạn mức: 413; A3 — ảnh không chứa biển số: HTTP **200** danh sách rỗng — một *câu trả lời*, không phải lỗi; A4 — phát hiện được nhưng OCR không đọc ra: bản ghi **vẫn lưu** với `plate_number` rỗng (4.7.2e); A5 — chuỗi không khớp định dạng: lưu với `is_valid_format = false`; A6 — lỗi nội bộ: 500, không lộ stack trace. A3 và A4 phân biệt thiết kế nghiêm túc với bản demo: âm thầm loại bỏ ca đọc hỏng sẽ làm sai lệch chính các số liệu Chương 5 cần.

**UC-02 — Nhận dạng từ video.** Hệ thống lưu tệp (MP4/AVI/MOV/MKV), tạo `DetectionJob` trạng thái `pending`, **trả ngay HTTP 202 kèm `job_id`**. Tác vụ nền chuyển `processing`, trích khung theo bước nhảy cấu hình được, cập nhật tiến độ; kết quả cùng biển số trên nhiều khung được **gộp trùng** giữ lần đọc tin cậy nhất; xong thì kết xuất video gắn nhãn, ghi CSDL, chuyển `completed`; giao diện hỏi tiến độ định kỳ. `pending` tách khỏi `processing` để phân biệt tác vụ *đang xếp hàng* với tác vụ *đã treo*. **Vì sao bất đồng bộ:** một khung mất ~400 ms trên CPU (4.1.4b); video 60 giây lấy mẫu 1/5 vẫn là 360 khung ≈ 145 giây — vượt timeout của hầu hết proxy và trình duyệt, nên xử lý đồng bộ là **không khả thi** chứ không phải lựa chọn kém.

> ⚠️ **Thay đổi phạm vi 2026-07-20:** trang Webcam đã được **gỡ khỏi giao diện web** theo quyết định thu gọn phạm vi demo. **UC-03 — Nhận dạng thời gian thực** vì vậy được hiện thực và kiểm chứng **ở tầng API** (`POST /api/detect/frame`); tác nhân chính trở thành một *client thời gian thực* bất kỳ gọi API — trang webcam trước đây của giao diện chính là một client như vậy. Các bước thuần giao diện (FR-3.1, FR-3.4) chuyển mức ưu tiên **M → W**.

**UC-03** yêu cầu client có nguồn thu hình, mã hoá khung thành JPEG/PNG, gửi theo chu kỳ cấu hình được. Lời gọi đầu không kèm định danh nên máy chủ tạo tác vụ mới trả `job_id`; các lời gọi sau gửi kèm nên cả phiên quy về **một** bản ghi tác vụ, biển đã gộp trùng trong phạm vi phiên. `job_id` không tồn tại thì hệ thống **âm thầm mở phiên mới** để tải lại trang không làm hỏng luồng chụp. **Ràng buộc riêng:** không có GPU nên bắt buộc bỏ bớt khung kết hợp hàng đợi một khe phía client — nếu không, tốc độ chụp (~30 fps) vượt xa tốc độ xử lý (~3–5 fps), hàng đợi phình vô hạn và độ trễ tăng tuyến tính (cài đặt ở 4.8.4).


---

### H.2. Bảng 34 yêu cầu chức năng


Đồ án đặc tả **34 yêu cầu chức năng** trong **6 nhóm**, mỗi yêu cầu có mã, mức MoSCoW và một tiêu chí chấp nhận kiểm chứng được. Phân bố: FR-1 (ảnh tĩnh) **7 Must**; FR-2 (video) **5 Must + 1 Should**; FR-3 (thời gian thực, tầng API) **3 Must + 2 Won't**; FR-4 (thống kê – lịch sử – tra cứu) **4 Must + 1 Should + 1 Could + 2 Won't**; FR-5 (quản lý dữ liệu) **2 Should + 2 Could**; FR-6 (hệ thống, vận hành) **2 Must + 2 Should**. Tổng **21 Must, 6 Should, 3 Could, 4 Won't = 34**.

**FR-1:** tiếp nhận, kiểm tra hợp lệ, phát hiện *tất cả* vùng biển, cắt và nhận dạng, hậu xử lý, lưu kết quả, hiển thị có bounding box. FR-1.5 quy định lưu **cả chuỗi OCR thô lẫn chuỗi đã sửa** — điều kiện cần để đo đóng góp hậu xử lý ở Chương 5 (4.7.2b). **FR-2:** thêm trích khung theo bước nhảy, **gộp trùng** (FR-2.4 — thiếu nó một video 30 giây sinh hàng nghìn bản ghi về cùng vài chiếc xe, phá hỏng thống kê FR-4), kết xuất video gắn nhãn; Should duy nhất là tiến độ phần trăm và huỷ tác vụ. **FR-3:** theo quyết định 2026-07-20, hai yêu cầu thuần giao diện FR-3.1, FR-3.4 chuyển **M → W**; FR-3.2/3.3/3.5 vẫn Must, kiểm chứng ở tầng API. **FR-4:** chỉ số tổng hợp (FR-4.1), biểu đồ theo thời gian (FR-4.2), danh sách phân trang, tìm kiếm khớp một phần, lọc, chi tiết, tải ảnh, sắp xếp; **FR-4.3 → 4.8 không đổi**. **FR-5:** xoá bản ghi kèm tệp, xuất CSV/JSON (CSV phải UTF-8 **có BOM** kẻo Excel hiển thị sai tiếng Việt), dọn tệp mồ côi, xoá hàng loạt. **FR-6:** health check báo trạng thái mô hình và CSDL; log có cấu trúc; thông báo lỗi thân thiện không lộ stack trace; cấu hình qua biến môi trường.

> ### Bốn yêu cầu mức Won't và hai đợt thu gọn phạm vi ngày 2026-07-20
>
> Cả bốn yêu cầu Won't đều **thuần giao diện**, chuyển mức trong cùng ngày qua hai đợt: đợt 1 gỡ trang Webcam (FR-3.1, FR-3.4 **M → W**; năng lực còn ở `POST /api/detect/frame`); đợt 2 gỡ trang Tổng quan (**FR-4.1 M → W**, FR-4.2 S → W; năng lực còn ở `GET /api/statistics` và `GET /health`).
>
> **Phải nói thẳng: FR-4.1 là yêu cầu mức *Must* đầu tiên — và duy nhất — bị đưa ra khỏi phạm vi trong toàn bộ đồ án.** Con số đếm vì vậy giảm từ 22/7/3/2 xuống **21/6/3/4**, và mục 6.3 ghi nhận đây là **hạn chế thật**. Điều **không** thay đổi: cả hai đợt chỉ gỡ **màn hình hiển thị**, không gỡ **năng lực hệ thống** — các endpoint vẫn phục vụ, vẫn trong tài liệu OpenAPI, vẫn có kiểm thử tích hợp (`tests/integration/test_api_statistics.py`, `test_api_health.py`), thiết kế API ở 4.7.3 giữ nguyên không sửa một dòng — bằng chứng thực tế cho nguyên tắc tách tầng ở 4.2. Đánh đổi đo được của đợt 2: gỡ `recharts` làm gói tải về giảm từ ~730 KB xuống **328,8 KB** (−55%).

**Ma trận truy vết:** mỗi nhóm truy vết tới giai đoạn cài đặt và hình thức kiểm chứng (FR-1: unit + integration; FR-2: integration + performance; FR-3: performance ở tầng API; FR-4: integration + UI test cho FR-4.3→4.8; FR-5: unit; FR-6: smoke + stress). Kết quả ở Chương 5.


---

### H.3. Bảng chỉ tiêu phi chức năng


Bảy nhóm: hiệu năng (NFR-P), độ chính xác (NFR-A), tin cậy (NFR-R), khả dụng (NFR-U), bảo trì (NFR-M), bảo mật (NFR-S), tương thích – triển khai (NFR-C), mở rộng (NFR-SC).

#### a) Nguyên tắc nền tảng: mọi chỉ tiêu hiệu năng đều là chỉ tiêu CPU

> **Toàn bộ chỉ tiêu hiệu năng của đồ án là chỉ tiêu đo trên CPU.**

Máy thực hiện chạy Windows 11, Python 3.13, **không có GPU CUDA** (Intel UHD 770 tích hợp, PyTorch không dùng được để tăng tốc). Huấn luyện trên GPU miễn phí Colab/Kaggle, nhưng **suy luận và buổi bảo vệ chạy trên CPU máy cá nhân**. Đây là **ràng buộc thiết kế**, không phải hạn chế tạm thời, vì bốn lẽ: nó cố định trong toàn bộ vòng đời và tại chính buổi bảo vệ; nó đổi *bậc độ lớn* của độ trễ (ở 20 ms/khung, video đồng bộ và webcam xử lý mọi khung là hợp lý — ở mốc thực tế 400 ms cả hai bất khả thi, trực tiếp sinh ra hai quyết định kiến trúc: video bất đồng bộ AD-02 và webcam bỏ khung hàng đợi một khe); nó chi phối chọn biến thể mô hình (n/s/m), biến thể OCR (mobile/server), kích thước ảnh và **backend suy luận** — benchmark chính thức trên CPU i7-13700H cho thấy YOLOv8n qua ONNX Runtime nhanh hơn PyTorch khoảng **3,73 lần** (104,61 → 28,02 ms) [18]<!-- ultralytics_2026_openvinoexport -->, lợi ích lớn nhất đúng ở phân khúc mô hình nhỏ [117]<!-- onnxruntime_2025_threading -->; và nó buộc phương pháp công bố chặt hơn — quy tắc CON-06: **mọi số liệu hiệu năng phải kèm model CPU, số luồng, kích thước ảnh, backend suy luận và cỡ mẫu đo**. Các chỉ tiêu độ trễ vì vậy "rộng rãi" hơn văn liệu quốc tế đo trên GPU — đó là trung thực về điều kiện đo, không phải dễ dãi.

> **Cảnh báo trích dẫn.** Bảng benchmark nguồn có cột mAP nhưng đo trên tập `coco8` chỉ **8 ảnh**, không có ý nghĩa thống kê; đồ án chỉ dùng cột thời gian và cố ý lược bỏ cột độ chính xác.

#### b) Chỉ tiêu định lượng nhóm hiệu năng và nhóm độ chính xác

<!-- {{T4.1}} chi tieu phi chuc nang dinh luong NFR-P va NFR-A -->

**Bảng 4.1.** Chỉ tiêu phi chức năng định lượng: hiệu năng (NFR-P) và độ chính xác (NFR-A)

| Mã | Chỉ tiêu | Mục tiêu | Ngưỡng tối thiểu |
|---|---|---|---|
| **NFR-P1** | Độ trễ toàn trình một ảnh (p95) | ≤ 800 ms | ≤ 1500 ms |
| **NFR-P2** | Tốc độ khung hình thời gian thực (webcam — đo ở tầng API) | ≥ 5 FPS hiệu dụng | ≥ 3 FPS |
| **NFR-P3** | Tốc độ xử lý video | ≥ 0,3× thời gian thực | ≥ 0,15× |
| **NFR-P4** | Thời gian nạp mô hình khi khởi động | ≤ 15 giây | ≤ 30 giây |
| **NFR-P5** | Overhead của tầng API (không tính suy luận) | ≤ 50 ms | ≤ 100 ms |
| **NFR-P6** | Thời gian truy vấn lịch sử (10.000 bản ghi) | ≤ 500 ms | ≤ 1000 ms |
| **NFR-P7** | Bộ nhớ thường trú của backend | ≤ 2 GB | ≤ 4 GB |
| **NFR-A1** | mAP@0.5 của bộ phát hiện | ≥ 0,90 | ≥ 0,85 |
| **NFR-A2** | mAP@0.5:0.95 của bộ phát hiện | ≥ 0,65 | ≥ 0,55 |
| **NFR-A3** | Precision / Recall phát hiện | ≥ 0,92 / ≥ 0,90 | ≥ 0,88 / ≥ 0,85 |
| **NFR-A4** | Độ chính xác OCR mức ký tự (1 − CER) | ≥ 0,95 | ≥ 0,92 |
| **NFR-A5** | Độ chính xác biển đầy đủ **trước** hậu xử lý | ≥ 0,85 | ≥ 0,80 |
| **NFR-A6** | Độ chính xác biển đầy đủ **sau** hậu xử lý | ≥ 0,90 | ≥ 0,85 |
| **NFR-A7** | Độ chính xác toàn trình (ảnh vào → biển đúng) | ≥ 0,88 | ≥ 0,82 |

**Phương pháp đo NFR-P:** P1 trên 100 ảnh test, báo p50/p95/p99; P2 đo liên tục 60 giây; P3 bằng video 60 giây phải xong trong ≤ 200 giây; P4 từ khởi động đến khi `/health` sẵn sàng; P5 là hiệu tổng thời gian request trừ thời gian pipeline; P6 có phân trang và bộ lọc trên 10.000 bản ghi; P7 theo dõi RSS khi chạy tải liên tục.

NFR-P1 xuất phát từ **phân rã ngân sách độ trễ**: giải mã ~50 ms; phát hiện @640 px ~150 ms; cắt ~30 ms; OCR mỗi biển ~120 ms; hậu xử lý < 5 ms; ghi CSDL ~50 ms — **tổng ~405 ms cho ảnh một biển**; ngân sách 800 ms để dự phòng ảnh nhiều biển và biến động tải. Đây là **ước lượng thiết kế, không phải kết quả đo** (số đo ở Chương 5). Ngân sách lập cho runtime mặc định đã chốt ở mục 3.4 là **ONNX Runtime** — điểm đã đổi so với AD-05 sơ bộ. Nếu vượt ngưỡng, thứ tự giảm tải định trước: (1) INT8 OpenVINO; (2) giảm ảnh xuống 480 px; (3) biến thể OCR nhẹ hơn — chỉ hạ chỉ tiêu **sau khi** thử hết ba phương án.

Cặp NFR-A5/A6 đặt **tách bạch** có chủ đích: hiệu số giữa chúng là đóng góp định lượng của khối hậu xử lý — đo được nhờ quyết định lưu cả chuỗi thô lẫn chuỗi sửa ở tầng dữ liệu (4.7.2b). Bổ sung: **NFR-A8** — báo cáo độ chính xác **tách riêng biển một dòng và hai dòng**, căn cứ số liệu 94,3% / 45,7% **đo trên bộ RodoSol-ALPR (Brazil)** đã dẫn ở 4.1.1, vì một con số tổng thể sẽ che giấu đúng điểm gãy cần phân tích; **NFR-A9** — báo cáo theo điều kiện ảnh nếu bộ dữ liệu có nhãn phù hợp.

#### c) Các nhóm yêu cầu phi chức năng còn lại

**NFR-R:** không sập với đầu vào hỏng/độc hại (100% lỗi bị bắt); ảnh không biển trả rỗng hợp lệ HTTP 200; video thất bại không để lại rác; tỉ lệ thành công chạy liên tục một giờ ≥ 99%; CSDL sống sót khởi động lại. **NFR-U:** lượt nhận dạng đầu tiên ≤ 3 nhấp chuột, không cần tài liệu; thao tác > 500 ms có phản hồi trực quan; thông báo lỗi tiếng Việt nêu nguyên nhân và cách khắc phục; dùng được từ 1366×768; tương phản WCAG AA ≥ 4,5:1. **NFR-M:** mã AI tách hoàn toàn khỏi mã API (M1); bao phủ test tầng nghiệp vụ ≥ 70% (M2); type hint + docstring (M3); không hard-code đường dẫn (M4); thay bộ OCR không sửa tầng API (M5); lint tự động (M6) — M1 và M5 **là yêu cầu kiến trúc**, lý do tồn tại của tầng AI độc lập (4.2). **NFR-S:** kiểm tra magic bytes; chống path traversal bằng tên tệp UUID; giới hạn kích thước phía máy chủ; CORS không ký tự đại diện; không log dữ liệu nhạy cảm; truy vấn tham số hoá qua ORM. **NFR-C:** chạy Windows/Linux/macOS qua Docker một lệnh; **không cần GPU là chế độ mặc định**; Chrome/Edge/Firefox; cài từ máy sạch ≤ 15 phút. **NFR-SC:** ổn định ≥ 5 yêu cầu đồng thời; không suy giảm ở 100.000 bản ghi; video nền không chặn yêu cầu khác.

> **Giới hạn đã biết cần công bố.** SQLite chỉ cho **một tiến trình ghi tại một thời điểm** — chấp nhận được ở quy mô đồ án, nhưng phải nêu trong phần Hạn chế kèm hướng khắc phục (PostgreSQL) nếu triển khai thực tế.

---


---

### H.4. Lược đồ cơ sở dữ liệu và lịch sử di trú


![](figures/fig-ch4-09.png)

**Hình 4.6.** Sơ đồ thực thể — liên kết của cơ sở dữ liệu

Hai thực thể quan hệ một–nhiều: một lần sử dụng (ảnh, video, phiên webcam) là một `DetectionJob`; mỗi biển tìm thấy là một `DetectionHistory` (không, một, hoặc nhiều bản ghi con). Sau ba lần di trú Alembic: `detection_history` **21 cột**, `detection_job` **11 cột**; đặc tả từng trường ở `backend/db/models.py`. Điểm chịu lực của `detection_job`: khoá chính **UUID** vì định danh trả cho client — số tự tăng đoán được cho phép liệt kê tác vụ người khác; `status` năm giá trị vòng đời, `progress` ràng buộc [0, 1]; `error_message` **chỉ dùng phía máy chủ** (có thể chứa đường dẫn, phiên bản — rò rỉ thông tin); bốn chỉ mục. `detection_history` có 5 chỉ mục, trong đó chỉ mục **tổ hợp** `(input_type, detected_time)` phục vụ truy vấn mặc định của màn hình lịch sử; đo được **p95 = 18,71 ms** trên 10.000 bản ghi so với chỉ tiêu NFR-P6 500 ms. **Tám ràng buộc CHECK** mức CSDL (ví dụ `CHECK (plate_line_count IS NULL OR plate_line_count IN (1, 2))`); enum lưu văn bản kèm CHECK vì SQLite không có enum. Năm quyết định dưới đây đều xuất phát từ một yêu cầu đo lường cụ thể — bỏ qua thì hậu quả là **một con số sai mà không có gì báo hiệu**.

**a) Tách `confidence` và `ocr_confidence`.** Hai đại lượng khác bản chất: "vùng này có phải biển số?" và "chuỗi đọc được có đúng?". Gộp một cột thì **không phân tích lỗi được nữa**; tách hai cột cho bảng chẩn đoán bốn tổ hợp (cao–thấp: định vị đúng đọc kém ⇒ cải thiện tiền xử lý/tách dòng; thấp–cao: hạ ngưỡng, huấn luyện thêm; thấp–thấp: dương tính giả). Bộ lọc `min_confidence` của endpoint lịch sử cũng chỉ phát biểu rõ được khi hai cột tách.

**b) Lưu cả `raw_ocr_text` lẫn `plate_number`** — quyết định có giá trị học thuật cao nhất trong lược đồ. Câu hỏi tất yếu từ hội đồng: khối hậu xử lý đóng góp bao nhiêu? Chỉ lưu chuỗi đã sửa thì câu trả lời là định tính; lưu cả hai thì tỉ lệ khớp của `raw_ocr_text` là **NFR-A5**, của `plate_number` là **NFR-A6**, và **hiệu số là đóng góp định lượng của hậu xử lý**. Phép đo còn tách được **sửa đúng** với **sửa hỏng** (thô đúng, sửa sai) — loại thứ hai bị che khuất hoàn toàn nếu chỉ nhìn con số tổng. Chi phí vài chục byte mỗi bản ghi; không lưu thì bằng chứng bị **xoá âm thầm ngay lúc ghi dữ liệu**.

**c) `source_job_id`.** Một ảnh có thể chứa nhiều biển (A-02) — thông thường chứ không ngoại lệ. Không có khoá nhóm thì "tổng lượt nhận dạng" chỉ đếm được bằng số dòng lịch sử: **một ảnh ba biển bị đếm thành ba lượt**, chỉ số nhân 2–3 lần, video còn nặng hơn — và lỗi **không tự bộc lộ**: con số vẫn trông hợp lý, chỉ sai theo hướng có lợi. Với khoá nhóm, ba câu hỏi tách bạch: lượt dùng đếm `detection_job`, biển đã đọc đếm `detection_history`, trung bình là tỉ số. Cột **NOT NULL** để bản ghi mồ côi thành lỗi ồn ào lúc chèn thay vì mâu thuẫn ngầm. Lập luận không mất hiệu lực khi trang Tổng quan bị gỡ: phép tính vẫn ở `StatisticsService`, khoá nhóm sai vẫn cho con số sai — chỉ là sai trong JSON thay vì trên màn hình.

**d) `plate_line_count` là trường bắt buộc về nghiệp vụ.** *Vai trò 1:* NFR-A8 yêu cầu báo cáo tách một dòng / hai dòng, căn cứ số liệu 94,3% / 45,7% **đo trên bộ RodoSol-ALPR (Brazil)** đã dẫn ở 4.1.1 [7]<!-- laroca_2022_crossdataset -->; một con số tổng (ví dụ 81,5% khi 70% tập là một dòng đạt 95% còn hai dòng chỉ 50%) che lấp hoàn toàn điểm gãy trên nhóm phương tiện đa số ở Việt Nam. *Vai trò 2:* khử nhập nhằng trong chính hậu xử lý — chuỗi `29B11234` phân giải được thành `29B-112.34` (ô tô, một dòng) hoặc `29-B1 1234` (xe máy kiểu cũ, hai dòng); chỉ nhìn chuỗi thì **không cách nào phân biệt** (2.2.2c), và ràng buộc tập chữ sê-ri không gỡ được vì cả hai cách phân giải đều đặt `B` ở vị trí thứ nhất. Thông tin số dòng đến từ nguồn khác hẳn — **hình học bounding box** đối chiếu kích thước chuẩn QCVN 08:2024/BCA [11]<!-- bocongan_2024_qcvn08 --> — thứ bộ OCR không có và không suy ra được từ chuỗi. Cột cho phép rỗng (lý do ở e) nhưng CHECK bảo đảm chỉ 1 hoặc 2.

**e) Vì sao các cột liên quan tới OCR đều cho phép giá trị rỗng.** Bốn cột `plate_number`, `raw_ocr_text`, `ocr_confidence`, `plate_line_count` cho phép rỗng; bốn cột toạ độ và `confidence` phát hiện thì bắt buộc. Quy tắc duy nhất:

> **Một biển số phát hiện được vẫn đáng lưu, kể cả khi bộ OCR không đọc ra ký tự nào.**

Bản ghi tồn tại vì bộ phát hiện đã tìm thấy vùng; mọi cột dẫn xuất từ OCR có thể vắng vì biển **được định vị nhưng không đọc được** là kết quả có thật, xảy ra thường xuyên (biển xa, bẩn, ngược sáng, nghiêng, đêm). Vứt bỏ các bản ghi này là **thiên lệch chọn mẫu**: chúng biến mất khỏi mẫu số và hệ thống chỉ được đánh giá trên chính những ca đã thành công. Ví dụ số: 100 biển phát hiện, 80 đọc ra chuỗi trong đó 76 đúng — giữ mọi bản ghi cho 76/100 = **76,0%** (năng lực toàn trình thật); vứt bỏ cho 76/80 = **95,0%**, lệch 19 điểm. Con số 95% đúng cho câu hỏi khác ("khi đọc được thì đúng bao nhiêu?"), nhưng câu hỏi thật là xác suất trả biển đúng khi đưa ảnh vào. Lỗi này nguy hiểm vì **luôn thiên vị theo hướng có lợi** nên ít bị nghi ngờ. Kết hợp (a), các bản ghi `confidence` cao nhưng `plate_number` rỗng là tập mẫu giá trị nhất để phân tích lỗi ở Chương 5.

**f) Ba cột phân loại phương tiện — di trú `0002_plate_kind_and_color`.** Thêm `plate_kind`, `plate_color`, `plate_color_confidence` — lặp lại nguyên tắc của cặp `raw_ocr_text`/`plate_number`: **thông tin đã tính ra thì phải được ghi lại** (biển quân đội đọc đúng 0,999 không được phép chỉ còn là `is_valid_format = 0`). **Cả ba cho phép NULL, không có mặc định:** dòng ghi trước di trú **thật sự không có giá trị**; `NULL` nghĩa là *chưa bao giờ đo*, `"unknown"` nghĩa là *đã đo, không kết luận được* — **một giá trị vắng mặt phải trông như vắng mặt.** SQLite hỗ trợ `ADD COLUMN` trực tiếp cho cột NULL nên không ràng buộc nào bị mất âm thầm.

**g) Xử lý múi giờ.** SQLite không có kiểu datetime bản địa và định dạng chuỗi của SQLAlchemy **đánh rơi phần bù múi giờ** — không lỗi, không cảnh báo. Hai hệ quả: `utcnow() - row.created_at` ném `TypeError`, và mốc naive sang JSON **không có hậu tố `Z`** nên trình duyệt đọc là giờ địa phương — trên máy UTC+7 mọi mốc lệch bảy giờ, đủ hợp lý để không ai để ý và đủ sai để hỏng mọi phân tích thời gian. Sửa ở **mức kiểu**: `TypeDecorator` tên `UtcDateTime` chuẩn hoá UTC khi ghi, gắn lại UTC khi đọc; `utcnow()` phía Python thay `CURRENT_TIMESTAMP` vì bản SQLite sinh chuỗi naive độ phân giải một giây — quá thô để sắp thứ tự các phát hiện từ cùng một video.

---

### H.5. Tám quyết định kiến trúc AD-01 … AD-08

**Bảng 4.1.** Các quyết định kiến trúc AD-01 … AD-08

| Mã | Quyết định về | Lựa chọn | Lý do | Đánh đổi phải chấp nhận |
|---|---|---|---|---|
| **AD-01** | Quan hệ giữa tầng AI và tầng API | Tầng AI là package Python độc lập | NFR-M1; kiểm thử độc lập, tái dùng được trong script huấn luyện và đánh giá (mục 4.2.3) | Thêm một lớp gián tiếp giữa hai tầng |
| **AD-02** | Xử lý video | **Bất đồng bộ, trả `job_id` ngay** | Thời gian xử lý vượt xa timeout HTTP (NFR-SC3); xem mục 4.1.2 | Giao diện phải hỏi tiến độ định kỳ; cần quản lý vòng đời tác vụ |
| **AD-03** | Thời gian thực (webcam) | Client gửi từng khung qua HTTP (`POST /detect/frame`) | Đơn giản, dễ gỡ lỗi, đủ cho mức ~5 FPS | Cần tốc độ khung hình cao hơn thì phải chuyển sang WebSocket |
| **AD-04** | Gộp trùng biển số | Theo chuỗi ký tự kết hợp cửa sổ thời gian | Đơn giản hơn nhiều so với bám vết đối tượng, đủ dùng cho FR-2.4 | Kém chính xác nếu hai xe cùng biển số trong một video — thực tế không xảy ra |
| **AD-05** | Runtime suy luận | **ONNX Runtime làm mặc định**, OpenVINO là tối ưu bổ sung | Nhanh hơn PyTorch khoảng 3,73 lần ở phân khúc nano; một runtime duy nhất cho cả hai mô hình loại bỏ xung đột framework (mục 3.4) | Thêm bước xuất mô hình; phải đặt tường minh số luồng nội bộ |
| **AD-06** | Thiết bị suy luận | Cấu hình được, mặc định `cpu` | CON-02 — máy phát triển không có GPU CUDA | — |
| **AD-07** | Lưu trữ ảnh và video | Tệp trên đĩa, CSDL chỉ giữ đường dẫn | Tránh phình tệp SQLite do BLOB (mục 4.7.1) | Phải giữ đồng bộ giữa tệp và bản ghi (FR-5.1, FR-5.3) |
| **AD-08** | Đặt tên tệp | Sinh từ UUID, không dùng tên gốc | NFR-S2 — chống path traversal | Phải lưu tên gốc ở một trường riêng nếu muốn hiển thị lại |

## Phụ lục I. Chi tiết cài đặt backend, frontend và đóng gói

Năm mục dưới đây là **chi tiết cài đặt**, không phải quyết định thiết kế.
Chương 4 nêu *có* cơ chế gì và *vì sao* cần nó; phần liệt kê từng lớp ngoại lệ,
từng cờ cấu hình và từng dòng Dockerfile để ở đây, phục vụ người tái lập hệ
thống chứ không phải người đọc mạch lập luận.

---

### I.1. Xử lý lỗi, log có cấu trúc và `request_id`


**Mỗi ngoại lệ mang hai mô tả cho hai độc giả:** `user_message` — tiếng Việt, ngắn, có hành động, vào thân HTTP; `internal_detail` — tiếng Anh, kỹ thuật, chỉ vào log. Cây ngoại lệ: `APIError` (mang `status_code`) với `ValidationError` 400, `NotFoundError` 404, `FileTooLargeError` 413, `UnsupportedMediaTypeError` 415, `ProcessingError` 500. **Bốn bộ xử lý được đăng ký** — `APIError`, `RequestValidationError`, `StarletteHTTPException` và một bộ **bắt tất cả** cho `Exception` (không có nó, ngoại lệ ngoài dự kiến ở cấu hình debug hiển thị cả stack trace — NFR-S4). Thân lỗi dựng **từ danh sách khoá an toàn tường minh** nên trường mới không thể rò rỉ theo mặc định; `RequestValidationError` được viết lại vì thân lỗi gốc liệt kê giá trị vi phạm — tốt cho lập trình viên, sai với người dùng cuối.

**Log có cấu trúc: mỗi dòng một đối tượng JSON** — log video xen kẽ log tải lên đồng thời, văn bản thuần không tách lại được; với JSON, `jq 'select(.request_id == ...)'` dựng lại toàn bộ câu chuyện một yêu cầu. **`request_id` đi trong `ContextVar`**, không truyền tay — mọi hàm quên chuyển tiếp sẽ âm thầm đứt vết. Middleware tôn trọng `X-Request-ID` từ ngoài; cả `X-Request-ID` lẫn `X-Process-Time` khai trong `expose_headers` CORS. `safe_extra()` xử lý việc `logging` từ chối một số tên khoá trong `extra=` và ném `KeyError` — sự cố ném bởi chính lời gọi log, đúng lúc log quan trọng nhất — bằng cách **đổi tên** khoá trùng (tiền tố `ctx_`) thay vì bỏ. Log ra `stdout` vì runtime container sở hữu việc thu thập.


---

### I.2. Ba lỗi thực tế đã gặp và sửa trong quá trình cài đặt


Cả ba đều **đi qua được kiểm thử đơn vị** — test xanh không phải bằng chứng đầy đủ khi lỗi nằm ở ranh giới giữa mã và môi trường.

**a) pydantic-settings JSON-decode trường list *trước* validator.** Dòng `.env` tự nhiên nhất (`ALPR_CORS_ORIGINS=a,b`) làm dịch vụ **sập lúc khởi động** với `json.JSONDecodeError`, vì thư viện chạy `json.loads` trên giá trị thô của trường `list[str]` trước mọi validator; unit test vẫn xanh vì nguồn `init` **không** JSON-decode — test và môi trường chạy đi qua hai nhánh mã khác nhau của cùng thư viện. Sửa: `StringList = Annotated[list[str], NoDecode]` cho ba trường danh sách, đưa giá trị thô tới `_split_list` nhận cả hai dạng; validator từ chối `"*"` và danh sách rỗng ngay lúc khởi động.

**b) SQLite âm thầm nuốt `tzinfo`** — cơ chế và cách sửa ở 4.7.2g. Lọt qua rà soát vì bản ghi 14:30 hiển thị 21:30 vẫn là mốc bình thường — không gì trông sai, nhưng mọi phân tích thời gian vô hiệu.

**c) Log tiếng Việt làm sập console `cp1252` trên Windows.** Một dòng log tiếng Việt ném `UnicodeEncodeError` **bên trong cỗ máy logging** (console Windows mặc định `cp1252`, `JsonFormatter` đặt `ensure_ascii=False` có chủ ý) — sự cố trong lúc đang báo cáo sự cố, phá huỷ chính thông tin chẩn đoán. Container Linux dùng UTF-8 nên lỗi **chỉ xuất hiện trên Windows** và **sống sót qua toàn bộ kiểm thử trong Docker**. Sửa: `_utf8_stdout()` gọi `reconfigure(encoding="utf-8", errors="backslashreplace")` trước khi gắn handler, bọc trong `try/except`.

**Điểm chung:** cả ba nằm ở ranh giới mã–môi trường (nguồn cấu hình, tầng lưu trữ, bảng mã đầu ra) — lập luận cụ thể cho việc bộ kiểm thử phải gồm kiểm thử tích hợp chạy trên đường dẫn thật.




---

### I.3. Tầng gọi API và ánh xạ kiểu dữ liệu


`services/api.ts` là **nơi duy nhất frontend biết về axios hoặc mã HTTP**: component nhận dữ liệu đã có kiểu hoặc `ApiError` chuẩn hoá. **Sáu hàm gọi API** ứng một–một với sáu endpoint, cộng hai hàm dựng URL (`exportHistoryUrl`, `fileUrl`). **Ba endpoint còn lại không còn hàm gọi phía giao diện** nhưng **vẫn hoạt động ở backend**: `detect/frame` do client thời gian thực gọi, `statistics` do script và kiểm thử tích hợp, `health` do Docker HEALTHCHECK — cần phân biệt **hàm gọi bị xoá** với **endpoint thì không**. **Không hostname viết cứng:** origin đọc từ biến môi trường lúc build, **mặc định rỗng** (cùng-origin); `resolveOrigin()` cắt `/` cuối và hậu tố `/api` — không cắt thì `/health` (chủ ý nằm ngoài tiền tố `/api`) không với tới được. Riêng `PlateLineCount` khai là `1 | 2` chứ không `number` — kiểu tĩnh mã hoá lại ràng buộc `CHECK` của CSDL ở đầu bên kia đường truyền.


---

### I.4. Hàng đợi một khe ở client thời gian thực (trang webcam đã gỡ 2026-07-20)


Trang webcam đã gỡ khỏi frontend, nhưng lập luận thiết kế dưới đây vẫn đúng và trở thành **khuyến nghị bắt buộc cho bất kỳ client nào** gọi `POST /api/detect/frame`. Suy luận CPU ~5 FPS, nên bộ đếm giờ ngây thơ `await` từng phản hồi sẽ, ngay khi một khung mất 900 ms, khởi động yêu cầu thứ hai trước khi yêu cầu thứ nhất trở về — tồn đọng chỉ tăng và tab đứng hình. **Giải pháp: một khe duy nhất** — giữ đúng một yêu cầu đang bay; `inFlightRef` đang đặt thì khung bị **bỏ qua** (tăng `framesSkipped`) chứ không xếp hàng: bỏ một khung không tốn gì (khung sau cập nhật hơn), xếp hàng thì tốn tất cả. Giải phóng khe đặt trong `finally` — nếu trong `try`, một khung lỗi khoá vòng lặp vĩnh viễn. Hai bảo vệ kèm: **tự tạm dừng sau 5 lỗi liên tiếp**, và **`AbortController`** huỷ yêu cầu đang bay (huỷ chủ động không báo là lỗi). **Một `job_id` cho cả phiên** — nếu không, ba mươi giây chụp thành ~40 lượt tải lên thay vì 1. Khoá khử trùng bỏ ký tự không phải chữ-số và viết hoa (`"90C-76040"` ≡ `"90c 76040"`), nhưng là **khoá, không phải giá trị hiển thị**: một `O` do OCR đọc ra vẫn là `O` — âm thầm sửa thành `0` sẽ **che giấu đúng loại sai lầm mà chương đánh giá cần đo**.



---

### I.5. Triển khai bằng Docker


Đóng gói phục vụ NFR-C1: môi trường chạy tái lập được, không phụ thuộc máy cá nhân.

**`Dockerfile.backend` — build hai giai đoạn**, với bốn quyết định: **hai tệp requirements cài thành hai lớp riêng** (web + CSDL trước, ngăn xếp ML sau) nên thay đổi một tầng không mất bộ đệm tầng kia — hệ quả trực tiếp của 4.3.2; chạy dưới người dùng không đặc quyền `appuser`; **`ENV OMP_NUM_THREADS=4`** tường minh, vì không có nó BLAS/OpenMP dùng toàn bộ nhân và hai container cạnh tranh đến mức cùng chậm; **`HEALTHCHECK` gọi `/health`** với `--start-period=60s` vì nạp trọng số mất vài chục giây. `models/` gắn từ ngoài — **trọng số không nằm trong ảnh Docker**.

**`Dockerfile.frontend` — build rồi phục vụ tĩnh.** `builder` dùng `node:20-alpine` + `npm ci` rồi build; `runtime` dùng `nginx:alpine` chỉ chép `dist/` — không Node, không `node_modules`, không mã nguồn. `VITE_API_BASE_URL` truyền lúc **build** (`ARG`) vì Vite nhúng biến `VITE_*` vào bundle khi biên dịch — hạn chế thật: frontend không đổi được origin API mà không build lại; mặc định chuỗi rỗng (same-origin) được chọn chính để tránh điều đó.

**`docker-compose.yml`** khai báo hai dịch vụ, mạng bridge riêng `alpr-net`, volume `alpr-data` (CSDL, ảnh) và `alpr-model-cache` cho bộ đệm mô hình PaddleOCR — không có volume này, mỗi lần `down && up` tải lại vài trăm MB, và không có mạng thì container không khởi động được. Chi tiết ở **Phụ lục F.2**. **Trạng thái kiểm chứng:** `docker compose config` hợp lệ; đo hiệu năng trong container thuộc Chương 5.

---

### I.6. Cài đặt chi tiết hai adapter mô hình

Mục 4.6.2 nêu hợp đồng và phát hiện đáng kể; phần dưới giữ nguyên văn mô tả
cài đặt của `YoloPlateDetector` và `PaddleOcrRecognizer`.


Gói gồm mười một mô-đun cùng `__init__.py`, tổng **4.852 dòng**: `types.py`, `interfaces.py`, `config.py` (`InferenceConfig`), `exceptions.py` (cây `ALPRError`), `plate_rules.py`, `normalizer.py`, `detector.py`, `recognizer.py`, `two_line.py`, `plate_color.py`, `pipeline.py`. Ràng buộc "không import FastAPI" kiểm chứng tự động ở 4.2.3; lý do nền tảng: gói phải chạy được trong Jupyter, script benchmark và Colab.

Ba lớp trừu tượng: **`BaseDetector.detect(image) → list[PlateDetection]`** — đã lọc ngưỡng và NMS, mọi hộp **kẹp trong biên ảnh**, và **danh sách rỗng là kết quả bình thường**, không bao giờ là lỗi. **`BaseRecognizer.recognize(plate_image) → PlateRecognition`** — trả chuỗi thô kèm độ tin cậy; sửa lỗi ký tự và kiểm tra định dạng **không** thuộc trách nhiệm của nó — chính việc tách đó làm đóng góp hậu xử lý **đo được** qua hiệu giữa `raw_ocr_text` và `plate_number`; không đọc được thì trả chuỗi rỗng, không ném ngoại lệ. **`BaseNormalizer.normalize(raw_text) → tuple[str, bool]`** — kết quả không hợp lệ vẫn **trả về**, vì loại bỏ sẽ xoá đúng những thất bại chương đánh giá cần đếm. Hợp đồng "trả rỗng, không ném" nhất quán NFR-R2: **không tìm thấy** và **lỗi** là hai chuyện khác nhau. Hai lớp đầu có `warmup()` để chuyển chi phí nạp trọng số ra khỏi yêu cầu đầu tiên (NFR-P1).

Các kiểu dữ liệu khai báo **bất biến** (`frozen dataclass`) ở chỗ có thể; riêng `DetectionResult`/`PipelineResult` không bất biến vì chứa mảng ảnh nặng cần giải phóng sau khi lưu. `BoundingBox` lưu `(x, y, width, height)` khớp trực tiếp bốn cột `bbox_*`, kèm thuộc tính `aspect_ratio` phục vụ phân loại số dòng. Tên thuộc tính đặt **trùng tên cột CSDL có chủ đích** để tầng lưu trữ sao chép trường-sang-trường — một lớp biên dịch trung gian là thêm một chỗ để `confidence` và `ocr_confidence` bị hoán đổi (4.7.2a).

#### Bộ phát hiện — `YoloPlateDetector`

Adapter mỏng trên Ultralytics: không nơi nào ngoài mô-đun này chạm vào `Results` hay tensor. **Import trễ** (`from ultralytics import YOLO` trong `_load_yolo_model`) cho unit test không cần ngăn xếp ML; ngược lại **trọng số nạp ngay trong hàm khởi tạo** để tệp thiếu làm hệ thống thất bại lúc khởi động kèm hướng dẫn khắc phục. Bốn chi tiết: nhận `.pt`/`.onnx`/`.torchscript` cộng **thư mục** OpenVINO (kiểm tệp `.xml`) — từ chối thư mục sẽ khiến cấu hình nhanh nhất trên CPU Intel không cấu hình được; `_resolve_plate_class_ids` giữ tất cả khi mô hình một lớp (trường hợp của đồ án), mô hình nhiều lớp chỉ giữ lớp khớp `PLATE_CLASS_ALIASES` — checkpoint COCO 80 lớp trả danh sách rỗng là đúng, không phải lỗi; `_build_clamped_bbox` kẹp về biên, hoán đổi nếu `x2 < x1`, trả `None` kèm log nếu hộp suy biến; `name` trả `yolo:{stem}{suffix}` vì một con số benchmark chỉ tái lập được nếu nêu đúng bộ trọng số.

#### Bộ nhận dạng ký tự — `PaddleOcrRecognizer`

Ba đặc điểm: **khởi tạo trễ và tái sử dụng** (máy OCR đắt để dựng); **ghim phiên bản** `OCR_VERSION = "PP-OCRv5"` tường minh — nâng cấp thư viện không được âm thầm đổi mô hình đứng sau benchmark đã công bố; **tắt tiền xử lý mức tài liệu** vì đầu vào đã là vùng biển cắt sẵn.

**Phát hiện kỹ thuật: backend oneDNN làm sập suy luận trên PP-OCRv5.** Trên đúng nền tảng mục tiêu (`paddlepaddle` 3.3.1, Windows, CPU), chạy mô hình phát hiện văn bản qua oneDNN kết thúc bằng `NotImplementedError: (Unimplemented) ConvertPirAttribute2RuntimeAttribute not support [pir::ArrayAttribute<pir::DoubleAttribute>]` — khiếm khuyết phía thư viện, không phải lỗi cấu hình. Xử lý: hằng số có tài liệu `DEFAULT_ENABLE_MKLDNN: Final[bool] = False`. Đây là **núm hiệu năng, không phải núm độ chính xác** — khi lỗi thượng nguồn được sửa chỉ cần lật giá trị và đo lại; nó cũng giải thích một phần NFR-P1: một con đường tăng tốc CPU hiển nhiên đang bị chặn bởi lỗi thư viện chứ không phải chưa được thử.

**Lọc mảnh văn bản theo hình học.** CLAHE khuếch đại nhiễu ở vùng gần đồng nhất, có thể sinh mảnh rác đọc thành chuỗi vô nghĩa với độ tin cậy cao (đã gặp mảnh cao 10 px, độ tin cậy 0,84) — **ngưỡng tin cậy không tách được**, hình học mới tách được: `MIN_FRAGMENT_HEIGHT_RATIO = 0.35` đo **so với mảnh cao nhất**, và `_drop_short_fragments` trả nguyên đầu vào nếu không mảnh nào báo được hình học. **Tổng hợp độ tin cậy** dùng **trung bình có trọng số theo độ dài mảnh** — trung bình cộng cho phép mảnh một ký tự 0,99 che lấp mảnh bảy ký tự 0,40, trong khi mảnh dài mới mang danh tính biển số.

## Phụ lục J. Danh mục khảo sát công trình và bộ dữ liệu

Hai bảng dưới đây là **danh mục tra cứu** của phần khảo sát ở mục 2.7. Phần
luận điểm rút ra từ chúng — ba lưu ý bắt buộc khi đọc, quan sát về khoảng cách
giữa số công bố và số đo lại, ba nhận xét về bộ dữ liệu — nằm trong thân bài;
phần liệt kê từng công trình và từng bộ dữ liệu để ở đây.

---

### J.1. Các công trình quốc tế tiêu biểu về ALPR (2018 – 2026)


| # | Tác giả, năm — đóng góp, dataset và kết quả chính |
|:--:|---|
| 1 | **Zherzdev và Gruzdev, 2018.** **LPRNet** — segmentation-free, CTC, không RNN; biển Trung Quốc, tới **95%** accuracy, **3 ms/biển** trên GTX 1080 và **1,3 ms/biển** trên CPU i7-6700K [40] |
| 2 | **Laroca và cộng sự, 2018.** Pipeline YOLO nhiều giai đoạn; SSIG (2.000 khung hình, 101 xe): **93,53%** recognition rate ở **47 FPS** [37] |
| 3 | **Xu và cộng sự, 2018.** **RPnet** end-to-end, dự đoán đồng thời hộp bao và chuỗi; công bố **CCPD**: **98,5%** accuracy, trên **61 FPS** [38] |
| 6 | **Laroca và cộng sự, 2021.** Hợp nhất detection và **phân loại layout** trong một mạng YOLO: **96,9%** end-to-end trung bình trên 8 tập công khai từ 5 khu vực [23] |
| 7 | **Wang và cộng sự, 2021.** **VSNet** (VertexNet, SCR-Net) cascade: trên **99%** trên CCPD và AOLP, **149 FPS trên GPU**, giảm hơn 50% lỗi tương đối [45] |
| 8 | **Laroca và cộng sự, 2022.** **Tổng quát hoá xuyên tập dữ liệu**, 9 tập và 12 mô hình OCR; công bố **RodoSol-ALPR**: trung bình sụt **82,4% → 74,5%** với giao thức *leave-one-dataset-out*, AOLP sụt **90,8% → 62,7%** [7] |
| 9 | **Batra và cộng sự, 2022.** YOLOv5 học chuyển giao kết hợp EasyOCR; biển Ấn Độ (5.991 ảnh): **mAP@0.5 = 87,2%**, **mAP@0.5:0.95 = 46,5%**, Recall 82,2%, Precision 88,2%, mô hình **14 MB**, detection **4,8 ms trên Nvidia T4**, toàn hệ thống 85 ms [56] |
| 10 | **Del Castillo Velarde và Velarde, 2022.** Benchmark độc lập LPRNet với Tesseract, 1.000 ảnh mỗi tập: LPRNet **90%** trên biển thật, 89% trên biển tổng hợp; Tesseract **93%** *chỉ* trên dữ liệu tổng hợp *và chỉ sau tiền xử lý* [72]<!-- velarde_2022_benchmarking --> |
| 11 | **Tao và cộng sự, 2024.** **YOLOv5-PDLPR** — Multi-Head Attention, giải mã song song; CCPD tổng thể **99,4%** ở **159,8 FPS trên GPU**, Base 99,9%, **Challenge chỉ 94,1%**, PKUData 95,5% [73]<!-- tao_2024_pdlpr --> |
| 13 | **AlDahoul và cộng sự, 2024 – 2025.** **VehiclePaliGemma** — tinh chỉnh VLM cho biển Malaysia điều kiện phức tạp: **87,6%** accuracy nhưng chỉ **7 FPS trên GPU A100-80GB** [43] |
| 14 | **Shpir và cộng sự, 2025.** Sinh dữ liệu biển Ukraine bằng **mô hình khuếch tán**; tập tổng hợp gán nhãn giả cải thiện **+3%** so với baseline [74]<!-- shpir_2025_diffusion --> |
| 16 | **Xu và cộng sự, 2025.** **LPTR-AFLNet** hợp nhất nắn chỉnh và nhận dạng, cả biển 1 và 2 dòng; biển Trung Quốc: **99,37%** riêng trên biển 2 dòng với 2,7 triệu tham số [75]<!-- xu_2025_lptraflnet --> |
| 17 | **Wójcik và cộng sự, 2025.** **LPLC** — bài toán phân loại độ đọc được; cả ba baseline (ViT, ResNet, YOLO) đều **F1 dưới 80%** [76]<!-- wojcik_2025_lplc --> |
| 19 | **Vargoorani và cộng sự, 2025.** Gán nhãn giả bằng Grounding DINO kết hợp YOLOv8: **recall phát hiện** 94% trên CENPARMI và 91% trên UFPR-ALPR [77]<!-- vargoorani_2025_pseudolabel --> |
| 21 | **Laroca và cộng sự, 2026.** **ICPR 2026 LRLPR** — benchmark biển độ phân giải thấp dữ liệu thật (LRLPR-26): đội vô địch chỉ **82,13%**, chỉ **4/99 đội** vượt mốc 80% [71] |

---

### J.2. Các bộ dữ liệu chuẩn của lĩnh vực


| Bộ dữ liệu (năm, vùng) | Quy mô | Đặc điểm nổi bật và giấy phép |
|---|---|---|
| **CCPD** [86]<!-- xu_2018_ccpdrepo --> (2018 / 2019, Trung Quốc) | Trên **250.000** ảnh (bản 2018); trên **300.000** sau 2019 | Nhãn nhúng trong **tên tệp**: tỷ lệ diện tích, độ nghiêng, hộp bao, **4 đỉnh**, chỉ số ký tự, độ sáng, độ mờ. MIT |
| **AOLP** [87]<!-- hyperai_nd_aolp --> (2013, Đài Loan) | **2.049** ảnh (AC 681, LE 757, RP 611) | Ba kịch bản theo độ khó tăng dần. Học thuật, cấm thương mại |
| **UFPR-ALPR** [25] (2018, Brazil) | **4.500** ảnh, trên 30.000 ký tự, từ 150 xe | **Cả xe lẫn camera chuyển động**. Học thuật, cấm phân phối lại, phải xin quyền |
| **RodoSol-ALPR** [88]<!-- laroca_2022_rodosol --> (2022, Brazil) | **20.000** ảnh, 4 nhóm mỗi nhóm 5.000 | Camera tĩnh trạm thu phí; ngày và đêm; 2 layout; **số mẫu dễ và khó bằng nhau**. Xem kho chính thức |
| **CLPD** [41] (2020, Trung Quốc) | **1.200** ảnh từ cả 31 tỉnh thành | Kiểm tra tổng quát hoá địa lý rộng. Xem kho chính thức |
| **OpenALPR benchmark** [89]<!-- openalpr_2016_benchmarks --> (2016, đa quốc gia) | 445 ảnh (EU 108, US 222, BR 115) | Quá nhỏ để huấn luyện; **chỉ để benchmark xuyên tập**. AGPL-3.0 |
| **LPLC** [76] (2025) | **10.210** ảnh xe, **12.687** biển gán nhãn | Nhãn che khuất cấp xe và cấp biển; **4 mức độ đọc được**. Xem kho chính thức |
| **LRLPR-26** [71] (2026, đa quốc gia) | **20.000** track huấn luyện, 3.000 track kiểm thử | Benchmark đầu tiên cho biển độ phân giải thấp **dữ liệu thật**. Theo điều lệ cuộc thi |
| **Global License Plate Dataset** [90]<!-- agrawal_2024_globallpdataset --> (2024, 74 quốc gia) | Trên **5.000.000** ảnh từ **74** quốc gia | Nhãn đầy đủ: ký tự, mặt nạ, 4 đỉnh, thông tin xe. Không phải giấy phép chuẩn — rủi ro pháp lý trung bình |

---

## Phụ lục K. Nhật ký phương pháp đo — ba lần cùng một loại lỗi

Mục 5.5.6 tóm tắt bài học; phụ lục này giữ **diễn biến đầy đủ** của cả ba lần
công cụ đánh giá lệch khỏi đường chạy thật, vì bài học chỉ kiểm chứng được khi
người đọc thấy được triệu chứng, nguyên nhân gốc và cả biện pháp **đã thất bại**.

---

**Ghi chú phương pháp đo — ba lần cùng một loại lỗi, ghi lại thay vì giấu đi.** Lượt đo lại **đầu tiên** sau khi thêm bước cứu cho kết quả tự mâu thuẫn: **A6 tăng 1,75 điểm trong khi A7 đứng yên ở đúng 0,5227**. A7 **bao hàm** phần A6 đo, nên một biện pháp đang thực sự chạy **không thể** nâng chỉ số con mà để chỉ số bao hàm nó bất động ở từng chữ số thập phân. Nguyên nhân: trong `ai/evaluation/ocr_accuracy.py`, bước cứu mới chỉ nối vào nhánh A5/A6, còn **hàm dựng đường E2E vẫn gọi thẳng bộ chuẩn hoá rồi trả kết quả**; nối xong và đo lại, A7 mới lên 0,5295. Đó là **lần thứ hai**; lần thứ nhất ở chính nhánh A5/A6, cả hai lần triệu chứng đều là một chỉ số **đứng yên một cách vô lý** — dễ được cho qua hơn nhiều so với một con số sai.

> Khi chỉ số $X$ **bao hàm** chỉ số $Y$ về mặt định nghĩa, mà một can thiệp làm $Y$ dịch chuyển còn $X$ thì không nhúc nhích, **giả thuyết đầu tiên phải là đường đo của $X$ bị lệch khỏi đường chạy thật**.

**Biện pháp đặt ra khi đó — viết bước cứu thành hàm tự do dùng chung — đã thất bại.** Ngày 28/07/2026, **đúng loại lỗi ấy xuất hiện lần thứ ba**: bậc thang thử-lại (5.5.7), thêm vào pipeline ngày 21/07, **chưa bao giờ được kịch bản đánh giá gọi** ở cả hai nhánh, nên mọi con số A4–A7 công bố từ 21/07 đến 28/07 mô tả một pipeline ngắn hơn bản giao hàng. Bậc thang **đã** được viết đúng như biện pháp quy định (`should_retry_skewed`, `retry_skewed_variants` là hàm tự do dùng chung) — biện pháp được tuân thủ đầy đủ mà lỗi vẫn tái diễn, vì hàm dùng chung chỉ bảo đảm **nếu** kịch bản gọi thì gọi đúng bản cài đặt, chứ **không** bảo đảm kịch bản có gọi. Nguyên nhân gốc: `measure_crops` và `_run_pipeline` **dựng lại đường xử lý thay vì gọi nó**, nên mỗi bậc mới thêm vào `ALPRPipeline._process_one` đều **mặc định rơi ra ngoài phép đo**, im lặng.

> Một đường đo **liệt kê lại** các bước của hệ thống sẽ lệch khỏi hệ thống ở đúng thời điểm hệ thống thay đổi — tức đúng thời điểm phép đo cần chính xác nhất. Chia sẻ mã ở mức *hàm* không đủ; chỉ **gọi thẳng cùng một điểm vào** mới đủ.

Hai chốt chặn được thêm: kịch bản ghi thẳng **trạng thái các công tắc** vào tệp kết quả, và ghi **số biển mà từng bậc cứu được** (`recovery_contribution`) — một bậc không được gọi giờ hiện ra dưới dạng số 0 có nhãn thay vì biến mất không dấu vết. Biện pháp triệt để — cho harness đầu-cuối gọi thẳng `ALPRPipeline.process` — vẫn là **việc bỏ ngỏ**, ghi ở 5.9.2.

---

## Phụ lục L. Các mối đe doạ đến tính hợp lệ — phân tích chi tiết

Mục 5.9.3 liệt kê tám mối đe doạ ở dạng bảng. Phụ lục này giữ **nguyên văn phần
phân tích** của từng mục: bằng chứng số, biện pháp đã áp dụng, biện pháp **chưa**
áp dụng được và lý do, cùng hệ quả phải nhớ khi đọc các con số của chương.

---

**(1) Rò rỉ dữ liệu tồn dư không khử được bằng băm tri giác.** *Cao.* Bảng 5.1 cho thấy rò rỉ tồn dư **có thật, đo được**: ngoài vùng bảo vệ của ngưỡng gộp, tại Hamming **12** vẫn còn **791 cặp** và tại 15 là **3.529 cặp**; nghiêm trọng hơn, hai ảnh của **cùng một chiếc xe** ở góc khác nhau vẫn mang cùng biển số nhưng Hamming lớn — rò rỉ **ngữ nghĩa** mà không ngưỡng phash nào phát hiện được. *Đã áp dụng:* nâng ngưỡng gộp 5 → 10, đo ở nhiều ngưỡng cao hơn ngưỡng gộp. *Chưa áp dụng được:* chia split theo nhóm biển số, bất khả thi vì thiếu nhãn chuỗi cho phần lớn corpus. **Hệ quả: mọi chỉ số ở 5.4 và 5.6 phải coi là cận trên lạc quan.**

**(2) Tập test không xuyên bộ dữ liệu.** *Cao.* Train và test đều lấy từ **cùng sáu nguồn nguyên tố**, nên chỉ đo được tổng quát hoá *trong phân bố*, **không** đo được *xuyên phân bố* — thứ quyết định khi triển khai trên camera mới, địa điểm mới, chiếu sáng mới; tài liệu đã chỉ ra độ chính xác ALPR **sụt giảm đáng kể** khi đánh giá xuyên bộ dữ liệu [7]<!-- laroca_2022_crossdataset -->. *Giảm thiểu:* không có — cách đúng là giữ lại một nguồn hoàn toàn không dùng để huấn luyện làm tập test xuyên bộ; **chưa thực hiện**.

**(3) Mẫu số nhỏ cho các chỉ số OCR.** *Cao.* Phần lớn corpus 15.133 ảnh **chỉ có nhãn hộp giới hạn, không có nhãn chuỗi ký tự**, nên A4…A7 đo trên tập con **2.801 biển**; với mẫu số nhỏ, chênh lệch vài điểm phần trăm có thể nằm trong dao động ngẫu nhiên. *Giảm thiểu:* công bố mẫu số ở mọi bảng của 5.5, **không** rút kết luận về chênh lệch nhỏ.

**(4) Đo trên một cấu hình phần cứng duy nhất.** *Trung bình.* Mọi số hiệu năng đo trên một máy Intel Raptor Lake 14 nhân chạy Windows 11 và **không ngoại suy** sang CPU khác kiến trúc, sang Linux, hay máy khác số nhân — đặc biệt vì ONNX Runtime và OpenVINO đều nhạy với cấu hình luồng và tập lệnh vector [117]<!-- onnxruntime_2025_threading --> [120]<!-- openvino_2024_performancehints -->. *Giảm thiểu:* công bố cấu hình đầy đủ ở 5.2 và nhắc lại ở đầu 5.6.

**(5) Một lượt huấn luyện duy nhất, không ước lượng được phương sai.** *Trung bình.* Với `seed=42` cố định và ngân sách khoảng 12 giờ CPU cho một lượt, mọi chỉ số là kết quả của **một lần chạy**. *Giảm thiểu:* cố định seed để đảm bảo tái lập; không phát biểu so sánh nào dựa trên chênh lệch nhỏ hơn dao động giữa các seed dự kiến.

**(6) Bộ dữ liệu không đạt tiêu chí Q6 về tỉ lệ đối tượng nhỏ.** *Trung bình.* **10,91%** số hộp có diện tích dưới 0,5% diện tích ảnh, vượt ngưỡng 10%. *Giảm thiểu:* báo cáo mAP **tách theo dải kích thước** ở 5.4.4.

**(7) Nhãn layout suy ra từ tỉ lệ khung hình khi bộ dữ liệu không khai báo.** *Thấp đến trung bình.* Ngưỡng 2,5 có cơ sở từ QCVN 08:2024/BCA nhưng vẫn là heuristic; biển chụp nghiêng mạnh có thể bị phân loại nhầm. *Giảm thiểu:* ưu tiên nhãn lớp tường minh khi có, ghi rõ ở chú thích Bảng 5.2 tỉ lệ ô nào suy bằng heuristic.

**(8) Ma trận nhầm lẫn ký tự phụ thuộc thuật toán căn chỉnh chuỗi.** *Thấp.* Khi hai chuỗi khác độ dài, việc gán cặp "ký tự thật ↔ ký tự đọc được" phụ thuộc cách căn chỉnh Levenshtein xử lý các đường đi tối ưu đồng hạng, nên với chuỗi nhiều lỗi chèn/xoá, ma trận có thể ghi nhận cặp không phản ánh nhầm lẫn thị giác thật. *Giảm thiểu:* áp ngưỡng tần suất tối thiểu trước khi đưa một cặp vào bảng luật (tiêu chí 1 ở 5.5.4).

### J.3. Các công trình về nhận dạng biển số xe Việt Nam

**Bảng 2.8.** Các công trình về nhận dạng biển số xe Việt Nam

| # | Nhóm tác giả — năm — nơi công bố — phương pháp và kết quả |
|:--:|---|
| 1 | **Học viện Kỹ thuật Quân sự — 2021 — MAPR 2021.** Phát hiện điểm đặc trưng cho detection, encoder-decoder **segmentation-free** cho OCR, môi trường không ràng buộc: detection **mIoU 95,01%**, $P_{75}$ 99,5%; OCR **99,28% mức chuỗi**, 99,7% mức ký tự [59] |
| 2 | **Trần Anh Đạt, Trần Khánh Linh, Vũ Hoài Nam — 2023 — arXiv.** **Mô hình đa góc nhìn** kết hợp CnOCR; công bố **PTITPlates** (500 ảnh): **F1 91,3%** (baseline: YOLOv5 + OCR cơ bản 75,2%; YOLOv8 + Tesseract 82,9%; YOLOv8 + CnOCR 85,2%) [79]<!-- trananh_2023_multiangle --> |
| 3 | **Le, Mazumder, Quach, Banerjee, Nguyen — 2023 — FDSE 2023.** Kiến trúc **3 giai đoạn** toàn YOLOv8 (xe máy → biển → ký tự): **mAP 93%** sau 300 epoch [21] |
| 4 | **Tran, Bui — 2024 — MIWAI 2024.** SSD MobileNetV2 cho detection, YOLOv8-nano cho ký tự, trên **Raspberry Pi 4**: **95,68%** độ chính xác trung bình, **0,478 giây/ảnh** [80]<!-- tran_2024_embeddedlpr --> |
| 5 | **Dang và cộng sự — 2024 — IJITSR.** YOLO phát hiện xe, WPOD-NET nắn phẳng, **CRNN cải tiến** huấn luyện đồng thời CTC và attention: **WER 0,014** trên bãi đỗ xe **trong nhà** [70] |
| 6 | **Trần Hải và cộng sự — 2023 — IJMRAP.** Tuỳ chỉnh OpenALPR cho Việt Nam, template hậu xử lý; tập kiểm thử chỉ 120 ảnh, **không công bố** độ chính xác cuối [81]<!-- tran_2023_openalpr --> |
| 7 | **Đặng Thị Dung và cộng sự — 2024 — TNU Journal of Science and Technology.** So sánh YOLOv8 và YOLO-NAS trên 1.567 ảnh: YOLO-NAS-S Accuracy **83,92%**, F1 0,9125; YOLOv8n Accuracy 81,4%, F1 0,8979. **Không đo FPS** [82]<!-- dlu_2024_yolov8nas --> |
| 8 | **2012 — SoICT 2012.** ALPR cho trạm thu phí dùng *peak-to-valley* tách ký tự trên **cả biển 1 dòng và 2 dòng**; nền tảng tiền học sâu [83]<!-- acm_2012_tollbooth --> |
| 9 | **VAPR và Trường ĐH Công nghệ Thông tin – ĐHQG TP.HCM — 2018 — MAPR 2018 Challenge.** Cuộc thi *Vietnamese Bike License Plate Recognition*; dataset **3.000 ảnh xe máy** (2.000 huấn luyện, 1.000 kiểm thử), **kết quả xếp hạng không được công bố** [84]<!-- vapr_2018_mapr --> |
| 10 | **Nguyễn Thanh Lợi và cộng sự — 2023 — Tạp chí Khoa học Trường ĐH Mở Hà Nội.** Đề xuất YOLOv5; bài chỉ ghi "độ chính xác cao", **không công bố số liệu cụ thể** [85]<!-- nguyen_2023_yolov5bienso --> |

---

## Phụ lục M. Bảng đối chiếu hai mô hình phát hiện

Mục 3.6 giải thích vì sao phép so sánh này **không quy kết được nguyên nhân**
— ba biến thay đổi đồng thời. Bảng số đầy đủ để ở đây.

---

### M.1. So sánh `baseline-416-v1.pt` với `best.pt`

**Bảng 3.6.** So sánh `baseline-416-v1.pt` với `best.pt` — ba biến thay đổi đồng thời

| Hạng mục | `baseline-416-v1.pt` | `best.pt` (chính thức) | Chênh lệch |
|---|---:|---:|---:|
| **Cấu hình** | | | |
| `imgsz` | 416 | **640** | +224 px |
| Bộ dữ liệu | v1 — 4.578 ảnh, 1 nguồn | **v3 — 15.133 ảnh, 6 nguồn nguyên tố (hợp nhất từ 7 bộ)** | ×3,3 |
| Ngưỡng gộp trùng lặp | 5 | **10** | +5 |
| Rò rỉ train↔test (ngưỡng 10) | **619 cặp** | **0 cặp** *(hệ quả định nghĩa, xem T5.3b)* | |
| Số epoch | 40 | **20** | −20 |
| Tổng thời gian huấn luyện | 156 phút | **≈ 712 phút** | |
| **Kết quả trên tập test tương ứng** | | | |
| mAP@0.5 | **0,9933** *(epoch 38)* | **0,9829** | −0,0104 |
| mAP@0.5:0.95 | **0,8597** *(epoch 38)* | **0,7834** | −0,0763 |
| Precision | **0,9822** | **0,9837** | +0,0015 |
| Recall | **0,9810** | **0,9714** | −0,0096 |
| mAP biển một dòng | **0,9856** | **0,9884** | +0,0028 |
| mAP biển hai dòng | **0,9592** | **0,9675** | +0,0083 |
| Chênh lệch theo layout (điểm %) | **2,6** | **2,09** | −0,51 |
| Độ trễ E2E p95 (ms) | **763,75** *(client-side)* | **1.143,10** *(in-process, có bậc thang thử-lại)* | — |
