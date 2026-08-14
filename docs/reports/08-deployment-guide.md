# Báo cáo Phase 8 — Đóng gói Docker: build thật và chạy thử

**Ngày thực hiện:** 19/07/2026
**Trạng thái:** ✅ Build thành công, stack đã chạy và được kiểm thử bằng HTTP thật

---

## 0. Tóm tắt

Trước phase này, `Dockerfile.backend`, `Dockerfile.frontend`, `nginx.conf` và
`docker-compose.yml` mới chỉ được **kiểm tra cú pháp** bằng `docker compose config`.
Chưa từng có lần build nào.

Lần này cả hai image đã được build thật, stack đã chạy, và toàn bộ đường dây
nhận dạng đầu-cuối đã được kiểm chứng bằng `curl` từ **ngoài** container.

**Kết quả:** thành công, sau khi sửa **bốn lỗi thật** phát hiện trong quá trình
build và chạy (mục 6).

> **Đã chạy lại ngày 14/08/2026 trên bản giao hàng.** Image dựng lại từ mã hiện
> tại (gồm cả bản sửa `_create_job`), container nạp đúng `/app/models/best.pt`.
> Kết quả tóm tắt ở mục 5.3 và 6.1; số liệu thô:
> [39-docker-e2e.json](39-docker-e2e.json).
>
> Các mục **3 (thời gian build)** và **7 (bốn lỗi thật đã gặp)** giữ nguyên từ
> lượt Phase 8 — chúng ghi lại quá trình dựng và gỡ lỗi, không phụ thuộc mô hình.
> Riêng những số đo **độ chính xác** trong bản Phase 8 chạy trên checkpoint giữa
> chừng `best-cpu-epoch7.pt` (nay đã xoá khỏi kho) nên **không dùng để nói về độ
> chính xác của hệ thống** — số có thẩm quyền nằm ở Chương 5 của quyển.

---

## 1. Cấu hình phần cứng đã đo

Mọi số liệu hiệu năng trong tài liệu này đều gắn với cấu hình sau:

| Hạng mục | Giá trị |
|---|---|
| CPU | **Intel(R) Core(TM) i5-14600K** |
| Số nhân / luồng | **14 nhân vật lý / 20 luồng** |
| RAM máy chủ | **34,1 GB** |
| Hệ điều hành máy chủ | Windows 11 Pro 26200 |
| Docker | Engine 29.4.3, Desktop 4.74.0, Compose v5.1.4 |
| Backend engine | linux/amd64 (WSL2) |
| GPU dùng cho suy luận | **không có** — CPU-only theo quyết định AD-06 |

**Lưu ý quan trọng khi đọc số:** container backend bị giới hạn
`cpus: 4` và `OMP_NUM_THREADS=4`. Nghĩa là các số độ trễ dưới đây được đo trên
**4 nhân**, không phải 20 luồng của máy chủ.

---

## 2. Yêu cầu hệ thống

| Hạng mục | Tối thiểu | Ghi chú |
|---|---|---|
| Docker Engine | ≥ 23 | cần BuildKit |
| Docker Compose | ≥ 2.24 | cần cú pháp `env_file: required: false` |
| RAM | 8 GB | đo thực tế container backend dùng 719 MiB |
| **Dung lượng đĩa** | **~15 GB** | xem phân rã bên dưới |
| GPU | không cần | |
| Mạng lúc chạy lần đầu | **bắt buộc** | PaddleOCR tải trọng số từ HuggingFace |

Phân rã dung lượng đĩa:

| Thành phần | Dung lượng |
|---|---|
| Image `alpr-backend` | 4,12 GB |
| Image `alpr-frontend` | 97,7 MB |
| Base image kéo về (`python:3.12-slim`, `node:20-alpine`, `nginx:alpine`) | ~0,5 GB |
| Build cache BuildKit (wheel đã tải) | ~3–5 GB |
| Named volume (`alpr-data`, `alpr-model-cache`) | vài trăm MB |

---

## 3. Thời gian build thực tế

| Lần build | Thời gian | Ghi chú |
|---|---|---|
| **Lần 1 — cache trống** | **274 giây (4 phút 34 giây)** | tải toàn bộ wheel |
| Lần 2 — sau khi sửa `.dockerignore` | **8 giây** | các lớp `pip install` dùng lại cache |
| Lần 3 — sau khi sửa biến storage | **16 giây** (gồm cả `up -d`) | chỉ build lại lớp `COPY` + `ENV` |

Chi tiết các bước tốn thời gian nhất trong lần build 1:

| Bước | Thời gian |
|---|---|
| `npm ci` + `vite build` (frontend) | 19,7 s (bundle build trong 10,43 s) |
| `pip install torch torchvision` (index CPU) | 48,2 s |
| `pip install -r requirements-inference.txt` | 58,5 s |
| Gửi build context (**trước** khi sửa `.dockerignore`) | 66,5 s / 1,22 GB |
| Xuất và giải nén image backend | 91,8 s |

> **274 giây là thời gian trên đường truyền cụ thể của máy này.** Riêng
> `torch` (191,8 MB) và `paddlepaddle` (194,8 MB) đã là ~390 MB tải về. Trên
> mạng chậm hơn, con số 10–20 phút như dự kiến ban đầu là hoàn toàn hợp lý.

---

## 4. Lệnh build và chạy

```bash
# Chạy từ THƯ MỤC GỐC dự án (d:/DATN), không phải deployment/docker
cd d:/DATN

# 1. Chuẩn bị (chỉ làm một lần)
mkdir -p storage models

# 2. Build
docker compose build

# 3. Chạy — mô hình chính thức models/best.pt đã có, dùng mặc định
docker compose up -d

# 4. Kiểm tra
curl http://localhost:8000/health
docker compose ps

# 5. Dừng (giữ lại dữ liệu trong volume)
docker compose down

# 5b. Dừng và XOÁ luôn cơ sở dữ liệu
docker compose down -v
```

Sau khi huấn luyện xong và có `models/best.pt`, bỏ biến `ALPR_MODEL_FILE` đi:

```bash
docker compose up -d
```

---

## 5. Kết quả kiểm thử — mã trạng thái THẬT

Tất cả đo bằng `curl` từ máy chủ Windows, **ngoài** container, sau khi backend
báo `healthy`.

### 5.1. Các endpoint

> **Lưu ý cách đọc bảng.** Đây là bảng **phép thử khói**, không phải bảng liệt kê
> endpoint của hệ thống. Hệ thống định nghĩa **10 endpoint** (10 thao tác HTTP
> trên 9 đường dẫn — xem `docs/manuals/api-documentation.md` mục 4.2). Các URL
> `/docs` và `/openapi.json` ở phép thử 2, 3, 6 là đường dẫn do **FastAPI tự
> sinh**, được thử ở đây chỉ để xác nhận container phục vụ được tài liệu; chúng
> **không tính vào 10 endpoint** của đồ án.

| # | Phép thử | URL | Mã trả về | Kết quả |
|---|---|---|---|---|
| 1 | Backend health | `http://localhost:8000/health` | **200** | ✅ |
| 2 | Swagger UI | `http://localhost:8000/docs` | **200** | ✅ |
| 3 | OpenAPI schema | `http://localhost:8000/openapi.json` | **200** | ✅ |
| 4 | Frontend qua nginx | `http://localhost:5173/` | **200** | ✅ |
| 5 | Health qua nginx | `http://localhost:5173/health` | **200** | ✅ |
| 6 | Swagger qua nginx | `http://localhost:5173/docs` | **200** | ✅ |
| 7 | **`/api/health` qua nginx** | `http://localhost:5173/api/health` | **404** | ⚠️ đúng thiết kế |
| 8 | POST ảnh → backend | `http://localhost:8000/api/detect/image` | **200** | ✅ |
| 9 | POST ảnh → qua nginx | `http://localhost:5173/api/detect/image` | **200** | ✅ |

**Giải thích phép thử 7.** Router health được gắn ở **gốc**, cố ý nằm ngoài
tiền tố `/api`. Client trong `frontend/src/services/api.ts` cũng gọi `/health`,
và `nginx.conf` có khối `location = /health` riêng cho việc đó. Vậy 404 ở
`/api/health` là **hành vi đúng**, còn đường dẫn cần dùng là `/health` (phép
thử 5, trả về 200). Không có gì phải sửa.

Nội dung `/health` trả về:

```json
{"status":"ok","app_name":"Vietnamese ALPR API","version":"0.1.0",
 "database_connected":true,"model_loaded":true,"uptime_seconds":35.2}
```

### 5.2. Nhận dạng thật trên ảnh thật

| Ảnh | Mã | Số biển | Kết quả đọc được | Đúng định dạng |
|---|---|---|---|---|
| `1dong-1.png` (biển 1 dòng) | 200 | 1 | `51G-316.91` → `51G31691` | ✅ |
| `2dong-1.png` (biển 2 dòng) | 200 | 1 | `59-K1 201.73` → `59K120173` | ✅ |
| `nhieu-bien-1.png` (nhiều biển) | 200 | 3 | 2 biển đọc đúng, 1 biển `null` | phần đúng ✅ |
| `khong-co-bien-so.jpg` | 200 | 0 | không trả về gì | ✅ |

Hai điểm đáng ghi nhận về **tính trung thực** của đường dây:

* Với biển thứ ba trong `nhieu-bien-1.png`, hệ thống phát hiện được vùng biển
  (`detection_confidence` 0,91) nhưng OCR không đọc nổi, và nó trả về
  `plate_number: null`, `ocr_confidence: 0.0` — **không bịa ra biển số**.
* Với ảnh không có biển, nó trả về mảng rỗng chứ không cố tìm cho ra.

Độ tin cậy OCR trên các biển đọc được: **0,975 – 0,999**.

### 5.3. Kiểm chứng cấu hình bên trong container

**Chạy lại 14/08/2026:**

```
$ docker exec alpr-backend sh -c 'echo $ALPR_MODEL_PATH'
/app/models/best.pt

$ curl -s http://127.0.0.1:8000/health
{"status":"ok","database_connected":true,"model_loaded":true, ...}

$ docker exec alpr-backend touch /app/models/x
touch: cannot touch '/app/models/x': Read-only file system    # ✅ mount :ro có hiệu lực
```

---

### 5.4. ⚠ Cạm bẫy đo lường: `localhost` trên Windows cộng thêm ~2,1 giây

Khi chạy lại lượt đo này, mọi yêu cầu qua `http://localhost:8000` mất **~2.300 ms**
trong khi máy chủ tự báo `processing_time` chỉ **~200 ms**. Khoảng chênh **không
phụ thuộc kích thước ảnh** — ảnh 33 KB và ảnh 516 KB đều cộng đúng ~2.100 ms —
nên nó không thể là băng thông.

Nguyên nhân: máy khách phân giải `localhost` ra IPv6 `::1` trước, chờ hết giờ rồi
mới lùi về IPv4. Đổi sang `127.0.0.1` thì overhead rơi từ **2.083 ms xuống 58 ms**.

| Địa chỉ | Tương tác (trung vị) | Máy chủ tự báo | Overhead |
|---|---:|---:|---:|
| `localhost` | 2.286 ms | 201 ms | **2.083 ms** |
| `127.0.0.1` | **372 ms** | 314 ms | **58 ms** |

**Ai đo container qua `localhost` trên Windows sẽ công bố một con số cao gấp bảy
lần sự thật.** Luôn dùng `127.0.0.1` khi đo.

---

## 6. Hiệu năng đo được

> Đo trên **Intel Core i5-14600K, container giới hạn 4 nhân**, mô hình
> **checkpoint epoch 7** (chưa phải mô hình cuối).

### 6.1. Độ trễ đầu-cuối một ảnh (NFR-P1)

**Đo lại 14/08/2026** trên bản giao hàng: **30 ảnh khác nhau** lấy từ tập test,
mỗi ảnh gọi `POST /api/detect/image` một lần qua `127.0.0.1` (xem cạm bẫy 5.4):

| Chỉ số | Giá trị |
|---|---:|
| min | 163 ms |
| trung vị | 288 ms |
| **p95** | **319 ms** |
| max | 333 ms |
| Suy luận thuần (máy chủ tự báo), trung vị | 253 ms |

| Chỉ tiêu | Ngưỡng | Đo được | Kết luận |
|---|---|---:|---|
| NFR-P1 mục tiêu | p95 ≤ 800 ms | **319 ms** | ✅ đạt, biên 2,5× |
| NFR-P1 ngưỡng tối thiểu | p95 ≤ 1500 ms | **319 ms** | ✅ đạt |

**Không được đọc con số này như "NFR-P1 trong Docker tốt hơn khi chạy trực tiếp".**
Chỉ tiêu NFR-P1 công bố ở Chương 5 là **1.143,10 ms p95**, đo trên ngữ liệu khác
và **có bậc thang thử-lại nổ** — bậc thang chỉ chạy sau khi đọc hỏng, nên ngữ liệu
nào nhiều biển khó thì đuôi dài ra. 30 ảnh ở đây không đủ để chạm vào đuôi đó.
Điều lượt đo này chứng minh là **đóng gói container không thêm chi phí đáng kể**,
không phải là một con số NFR-P1 mới.

Lượt Phase 8 trước đó cho p95 = 823 ms trên **10 lần gọi cùng một ảnh**, chạy trên
checkpoint giữa chừng; chính bản báo cáo khi đó đã tự ghi *"chưa nên kết luận"* vì
cỡ mẫu quá nhỏ. Lượt này thay thế nó.

Ảnh nhiều biển tốn nhiều hơn hẳn: `nhieu-bien-1.png` (3 biển, 600×450) mất
**2,50 s**, vì OCR chạy một lần cho mỗi biển.

### 6.2. Thời gian nạp mô hình (NFR-P4, ngưỡng ≤ 15 s)

| Tình huống | Thời gian | Kết luận |
|---|---|---|
| **Khởi động nguội** (lần đầu, phải tải trọng số OCR) | **16,15 s** | ❌ vượt ngưỡng |
| **Khởi động ấm** (đã có cache) | **3,07 s** | ✅ đạt |

Phân rã lần khởi động ấm:

| Bước | Thời gian |
|---|---|
| Nạp detector YOLO | 1,689 s |
| Warmup detector | 1,075 s |
| Nạp engine PaddleOCR | 0,823 s |
| Warmup OCR | 1,997 s |
| **Tổng warmup đường dây** | **3,072 s** |

Lần nguội mất 16,15 s vì PaddleOCR tải 6 tệp trọng số PP-OCRv5 từ HuggingFace.
Đây là **chi phí một lần**: named volume `alpr-model-cache` giữ lại kết quả tải
về. `HEALTHCHECK` đã đặt `start-period=60s` nên lần khởi động nguội không bị
báo `unhealthy` oan.

### 6.3. Bộ nhớ (NFR-P7, ngưỡng ≤ 2 GB)

| Container | RAM dùng | Hạn mức |
|---|---|---|
| `alpr-backend` | **719 MiB** | 4 GiB |
| `alpr-frontend` | 23,9 MiB | — |

✅ **Đạt**, còn dư nhiều so với ngưỡng 2 GB.

### 6.4. Chưa đo trong phase này

NFR-P2 (webcam FPS), NFR-P3 (video), NFR-P5 (overhead API), NFR-P6 (truy vấn
10.000 bản ghi) **chưa được đo** trong Docker. NFR-A1/A2/A3 phải chờ mô hình
cuối cùng.

---

## 7. Bốn lỗi THẬT đã gặp và cách sửa

### Lỗi 1 — `.dockerignore` không chặn được venv, image phình 2,29 GB

**Phát hiện.** Dòng `transferring context: 1.22GB` trong log build.

**Nguyên nhân.** Cả ba tệp `.dockerignore` chỉ có dòng `.venv/`. Mẫu này **neo
vào thư mục gốc**, chỉ khớp `d:/DATN/.venv`. Các venv thật tên là `.venv-ai`,
`.venv-ocr`, `backend/.venv` — không cái nào bị loại. `backend/.venv` nặng
**2,0 GB** và chứa wheel **Windows**, bị `COPY backend/` nướng thẳng vào image
**Linux**.

**Sửa.** Thêm vào cả ba tệp:

```
.venv*/
**/.venv/
**/.venv*/
**/venv/
```

**Kết quả đo được:** context 1,22 GB → **633 kB**; image 6,41 GB → **4,12 GB**.

### Lỗi 2 — Sai tên biến khiến `./storage` không bao giờ được ghi

**Phát hiện.** Sau khi nhận dạng thành công, `ls ./storage` trên máy chủ vẫn
rỗng. `find` trong container cho thấy ảnh nằm ở `/app/data/uploads`.

**Nguyên nhân.** Compose đặt `ALPR_STORAGE_DIR`, nhưng trường cấu hình thật tên
là `storage_root` ⇒ biến đúng là **`ALPR_STORAGE_ROOT`**. Model cấu hình khai
báo `extra="ignore"` nên biến sai tên **bị nuốt trong im lặng**, không cảnh báo
gì. `storage_root` giữ mặc định `data`, nên ảnh gốc và ảnh biển cắt ra đều rơi
vào named volume của SQLite thay vì bind mount.

**Sửa.** Đổi tên biến trong `docker-compose.yml`, `Dockerfile.backend`,
`deployment/.env.example` và bảng biến trong `deployment/README.md`.

**Kiểm chứng sau khi sửa:** `./storage/plates/` và `./storage/uploads/` trên
máy chủ đã có tệp.

**Bài học.** `extra="ignore"` biến lỗi gõ sai thành lỗi câm. Phải kiểm chứng
bằng hành vi quan sát được, không chỉ đọc lại cấu hình.

### Lỗi 3 — `.env` của máy chủ rò đường dẫn Windows vào container

**Nguyên nhân.** `.env` ở thư mục gốc chứa `ALPR_MODEL_PATH=models/best.pt` và
`ALPR_DATABASE_URL=sqlite:///./data/alpr.db` (đường dẫn dành cho máy chủ).
Compose nội suy `${ALPR_MODEL_PATH:-...}` từ **chính tệp đó**, nên giá trị máy
chủ chảy thẳng vào container.

**Sửa.** Cố định đường dẫn tuyệt đối trong container, chỉ cho cấu hình tên tệp:

```yaml
ALPR_MODEL_PATH: /app/models/${ALPR_MODEL_FILE:-best.pt}
ALPR_DATABASE_URL: sqlite:////app/data/alpr.db
ALPR_STORAGE_ROOT: /app/storage
```

Đồng thời **bỏ `env_file` khỏi service frontend**: đó là nginx phục vụ tệp
tĩnh, biến lúc chạy không có tác dụng gì, mà nạp `.env` thì chép luôn khoá API
Roboflow/Kaggle vào một container không cần đến chúng.

### Lỗi 4 — Bind mount trên Windows làm backend chết ngay khi khởi động

*(Phát hiện 20/07/2026, khi chạy lại stack sau đợt sửa giao diện.)*

**Triệu chứng.** `docker compose ps` cho thấy `alpr-frontend` khoẻ mạnh nhưng
`alpr-backend` ở trạng thái `Restarting (1)` và lặp lại vô hạn. Vết lỗi cuối:

```
File "/app/backend/core/config.py", line 496, in ensure_directories
    directory.mkdir(parents=True, exist_ok=True)
PermissionError: [Errno 13] Permission denied: '/app/storage/uploads'
```

**Nguyên nhân.** Image chạy máy chủ bằng người dùng không đặc quyền (UID 1000)
và `Dockerfile.backend` đã `chown` sẵn `/app/storage` cho người dùng đó. Nhưng
`docker-compose.yml` **gắn đè** một thư mục host lên đúng đường dẫn ấy, và bind
mount mang theo quyền sở hữu của phía host — quyền do image đặt bị thay thế
hoàn toàn. Trên Windows 11 + Docker Desktop 29.4.3, thư mục đó hiện ra bên
trong container là `root:root` quyền `755`, nên UID 1000 không tạo được thư mục
con.

Điều khiến lỗi này khó thấy trước: `deployment/README.md` khi ấy khẳng định
*"trên Windows và macOS, quyền truy cập bind mount được ánh xạ tự động nên
không cần bước này"*. Khẳng định đó **sai**, và vì nó nằm đúng chỗ người đọc
tìm đến khi gặp vấn đề nên nó dẫn người đọc đi sai hướng. Bài học rút ra: một
câu tài liệu nói "trên nền tảng X thì không sao" mà chưa từng được chạy thử
trên nền tảng X là một khẳng định chưa có bằng chứng.

**Sửa.** Thêm [`deployment/docker/entrypoint-backend.sh`](../../deployment/docker/entrypoint-backend.sh).
Container khởi động bằng `root` **chỉ đủ lâu** để `chown` ba điểm gắn ghi được
(`/app/storage`, `/app/data`, `/home/appuser`), rồi `setpriv` **thay thế hẳn
tiến trình** bằng máy chủ chạy dưới UID 1000. Vì `exec` thay thế chứ không sinh
tiến trình con, không còn tiến trình `root` nào sống sót sang giai đoạn phục vụ
— tức là vẫn giữ nguyên nguyên tắc "không chạy máy chủ bằng root".

Cách kiểm chứng, chạy được bất cứ lúc nào:

```bash
docker compose exec backend sh -c 'grep ^Uid: /proc/1/status'
# Uid:  1000  1000  1000  1000       <- PID 1 là uvicorn, không phải root
```

**Kết quả sau khi sửa.** `alpr-backend` lên `Healthy`; `/health` trả
`model_loaded: true`; nhận dạng thật qua stack cho biển 1 dòng `51G31691`
(0,228 s), biển 2 dòng `59K120173` (0,789 s), ảnh 3 biển (1,591 s), ảnh không
có biển trả mảng rỗng HTTP 200; ảnh cắt được ghi ra `./storage/plates/` trên
host đúng như thiết kế bind mount.

**Lưu ý cho người vận hành.** Nếu bạn tự đặt `user:` trong compose hoặc
`--user` trên dòng lệnh, entrypoint nhận ra mình không phải root và chạy thẳng
lệnh mà không đụng vào quyền.

### Các lỗi được DỰ ĐOÁN nhưng KHÔNG xảy ra

Đề bài dự kiến sẽ gặp lỗi thiếu thư viện hệ thống. **Không lỗi nào xảy ra**, vì
`Dockerfile.backend` đã cài sẵn từ trước:

| Thư viện | Cho ai | Kết quả |
|---|---|---|
| `libgl1`, `libglib2.0-0` | OpenCV | ✅ không lỗi |
| `libgomp1` | OpenMP (torch + Paddle) | ✅ không lỗi |
| `libmagic1` | python-magic | ✅ không lỗi |

Kiến trúc wheel cũng đúng ngay từ đầu: `paddlepaddle-3.3.1-cp312-cp312-manylinux1_x86_64.whl`
và `torch-2.13.0+cpu-cp312-cp312-manylinux_2_28_x86_64.whl`.

---

## 8. Một rủi ro còn tồn tại: ba gói cùng chiếm namespace `cv2`

Trong image có **ba** gói cùng cài vào thư mục `cv2`:

| Gói | Phiên bản | Ai kéo vào |
|---|---|---|
| `opencv-python-headless` | 4.13.0.92 | `backend/requirements.txt` |
| `opencv-python` | 5.0.0.93 | `ultralytics` |
| `opencv-contrib-python` | 4.10.0.84 | `paddleocr` / `paddlex` |

Chúng ghi đè lẫn nhau, gói cài sau thắng. **Đã kiểm chứng bằng thực nghiệm là
hiện tại KHÔNG hỏng**: `import cv2` chạy được, YOLO và PaddleOCR đều hoạt động,
đường dây nhận dạng cho kết quả đúng.

Nhưng đây là **rủi ro thật**, vì trộn tệp của nhánh 4.x và 5.x trong cùng một
thư mục là tình huống không ai bảo đảm. Nếu về sau `import cv2` báo lỗi lạ
(thiếu symbol, sai chữ ký hàm), hãy ghim cả ba về **cùng một phiên bản** trong
`backend/requirements-inference.txt` — tiền lệ là `.venv-ocr` đã ghim
`opencv-python==4.10.0.84` đúng vì lý do này.

Chưa xử lý ngay vì nguyên tắc: **không sửa cái đang chạy được dựa trên suy
đoán**. Nhưng phải ghi lại để người sau biết.

---

## 9. Bảng biến môi trường

### 9.1. Suy luận

| Biến | Mặc định trong container | Ý nghĩa |
|---|---|---|
| `ALPR_MODEL_PATH` | `/app/models/best.pt` | Đường dẫn trọng số. **Không đặt trực tiếp** — dùng `ALPR_MODEL_FILE` |
| `ALPR_MODEL_FILE` | `best.pt` | Tên tệp mô hình, tương đối từ `models/` |
| `ALPR_DEVICE` | `cpu` | `cpu` hoặc `cuda` (chưa hỗ trợ GPU) |
| `ALPR_CONF_THRESHOLD` | `0.25` | Ngưỡng tin cậy phát hiện |
| `ALPR_IOU_THRESHOLD` | `0.45` | Ngưỡng IoU cho NMS |
| `ALPR_IMGSZ` | `640` | Kích thước ảnh đầu vào YOLO |
| `ALPR_OCR_LANG` | `en` | Ngôn ngữ OCR |
| `ALPR_OCR_USE_GPU` | `false` | GPU cho OCR |
| `ALPR_TWO_LINE_ASPECT_RATIO` | `2.5` | Ngưỡng tỉ lệ phân biệt biển 1/2 dòng |

### 9.2. Ứng dụng

| Biến | Mặc định trong container | Ý nghĩa |
|---|---|---|
| `ALPR_DATABASE_URL` | `sqlite:////app/data/alpr.db` | **4 dấu gạch** = đường dẫn tuyệt đối |
| **`ALPR_STORAGE_ROOT`** | `/app/storage` | ⚠️ **không phải** `ALPR_STORAGE_DIR` |
| `ALPR_LOG_LEVEL` | `info` | Mức ghi log |
| `ALPR_CORS_ORIGINS` | `http://localhost:5173,...` | Danh sách origin, không dùng `*` |
| `ALPR_MAX_UPLOAD_MB` | `200` | Phải ≤ `client_max_body_size` của nginx |
| `ALPR_USE_STUB` | *(không đặt)* | ⚠️ Bật sẽ **bịa** kết quả. Chỉ dùng để thử API |

### 9.3. Tài nguyên và cổng

| Biến | Mặc định | Ý nghĩa |
|---|---|---|
| `OMP_NUM_THREADS` / `MKL_NUM_THREADS` / `OPENBLAS_NUM_THREADS` | `4` | Số luồng CPU. **Không vượt quá `ALPR_CPU_LIMIT`** |
| `ALPR_CPU_LIMIT` | `4` | Hạn mức nhân CPU |
| `ALPR_MEMORY_LIMIT` | `4g` | Hạn mức RAM |
| `ALPR_BACKEND_PORT` | `8000` | Cổng API trên máy chủ |
| `ALPR_BACKEND_BIND` | `127.0.0.1` | Đặt `0.0.0.0` để mở ra LAN |
| `ALPR_FRONTEND_PORT` | `5173` | Cổng giao diện |

### 9.4. Chỉ dùng lúc build

| Biến | Mặc định | Ý nghĩa |
|---|---|---|
| `TORCH_INDEX_URL` | `https://download.pytorch.org/whl/cpu` | ⚠️ Đổi sang PyPI mặc định sẽ kéo về bản CUDA, image tăng ~2,5 GB vô ích |
| `VITE_API_BASE_URL` | `/api` | Vite nhúng lúc **build**, đổi sau phải build lại |
| `APP_UID` / `APP_GID` | `1000` | Khớp với UID máy chủ trên Linux |

---

## 10. Tệp đã thay đổi trong phase này

| Tệp | Thay đổi |
|---|---|
| `backend/requirements-inference.txt` | **MỚI** — ultralytics, paddlepaddle, paddleocr, paddlex |
| `deployment/docker/Dockerfile.backend` | Thêm lớp cài inference; sửa `ALPR_STORAGE_DIR` → `ALPR_STORAGE_ROOT`; thêm `PADDLE_PDX_CACHE_HOME` |
| `deployment/docker/.dockerignore` | Loại trừ venv đệ quy |
| `deployment/docker/Dockerfile.backend.dockerignore` | như trên |
| `deployment/docker/Dockerfile.frontend.dockerignore` | như trên |
| `docker-compose.yml` | Cố định đường dẫn container; `ALPR_MODEL_FILE`; sửa tên biến storage; bỏ `env_file` của frontend |
| `deployment/.env.example` | Sửa tên biến storage |
| `deployment/README.md` | Cập nhật trạng thái, dung lượng thật, mục đưa mô hình vào, 4 mục xử lý sự cố thật |

---

## 11. Việc còn phải làm

1. **Đo lại toàn bộ trên `models/best.pt`** khi huấn luyện xong. Mọi số ở đây
   là của checkpoint epoch 7.
2. **Đo lại NFR-P1 với ≥ 100 mẫu.** p95 trên 10 mẫu không đủ tin cậy để kết
   luận đạt hay không đạt.
3. **Đo NFR-P2, P3, P5, P6** trong môi trường Docker.
4. **Theo dõi rủi ro `cv2`** ở mục 8.
5. **Cân nhắc giảm dung lượng image 4,12 GB** — `paddlex` kéo theo `polars`,
   `pandas`, `matplotlib`, `modelscope` mà đường suy luận gần như không dùng.

---

## 12. Tài liệu liên quan

* `deployment/README.md` — hướng dẫn vận hành chi tiết
* `docs/00-requirements/non-functional-requirements.md` — định nghĩa NFR
* `models/README.md` — quản lý trọng số
