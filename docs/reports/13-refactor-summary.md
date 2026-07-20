# Báo cáo tổng kết đợt Refactor / Đánh bóng

**Ngày:** 2026-07-20
**Nhánh:** `main` · **Commit gốc đối chiếu:** `f0f6202`
**Nguyên tắc chi phối:** hệ thống đã chạy được và đã đẩy lên GitHub — mục tiêu của
đợt này là **đánh bóng, không phải xây lại**. Không đổi kiến trúc, không đổi tên
API công khai, không đổi schema CSDL, không đổi hợp đồng endpoint, không đổi cấu
trúc thư mục.

Tài liệu số liệu gốc:
[`13-refactor-baseline.json`](13-refactor-baseline.json) ·
[`13-refactor-result.json`](13-refactor-result.json)

---

## 1. Mốc đối chiếu (baseline → kết quả)

Mọi bước sửa mã đều phải chạy lại toàn bộ bộ kiểm thử và so với hàng dưới đây.
Bất kỳ mục nào tụt so với baseline sẽ bị **hoàn nguyên ngay**.

| Mục đo | Baseline | Sau đợt refactor | Kết quả |
|---|---:|---:|---|
| pytest — thu thập | 882 | 882 | giữ nguyên |
| pytest — pass | 881 | 881 | giữ nguyên |
| pytest — fail | 0 | 0 | giữ nguyên |
| pytest — xfail | 1 | 1 | giữ nguyên |
| pytest — skip | 0 | 0 | giữ nguyên |
| pytest — cảnh báo | 17 | 17 | giữ nguyên |
| pytest — thời gian | 15,51 s | 16,06 s | tương đương (nhiễu đo) |
| `tsc --noEmit` | 0 lỗi | 0 lỗi | giữ nguyên |
| `eslint` | 0 lỗi / 0 cảnh báo | 0 lỗi / 0 cảnh báo | giữ nguyên |
| `vite build` | thành công | thành công | giữ nguyên |
| build — số module | 2.489 | 2.480 | **tốt hơn** (−9) |
| build — thời gian | 3,27 s | 2,95 s | **tốt hơn** (−0,32 s) |
| chunk khởi động `index` | 179,96 KB (gzip 59,07) | 179,22 KB (gzip 58,86) | **tốt hơn** (−0,74 KB) |
| chunk `vendor` biểu đồ | 374,97 KB | 374,97 KB | giữ nguyên |
| CSS | 32,97 KB | 30,61 KB | **tốt hơn** (−2,36 KB) |
| NFR-M1 (`ai/` không dính FastAPI) | đạt | đạt | giữ nguyên (18/18 test kiến trúc) |
| **`black --check`** | 1 tệp cần định dạng lại | **0** (96/96 sạch) | **tốt hơn** |
| **`ruff check`** | 113 lỗi | **83 lỗi** | **tốt hơn** (−30) |
| Độ bao phủ test | *(không ghi ở baseline)* | 87,7% (2.931 câu lệnh) | đo lần đầu |

**Kết luận:** không có mục nào tụt. Bốn mục frontend và hai mục lint tốt hơn.

---

## 2. Những gì đã dọn / đã sửa

### 2.1. Gỡ trang Webcam khỏi giao diện (quyết định 2026-07-20)

Theo quyết định thu gọn giao diện còn 4 trang, đã xoá route, mục menu, trang và
toàn bộ thư mục component `frontend/src/components/detection/webcam/` (9 tệp) cùng
`pages/WebcamDetection.tsx`.

> **Quan trọng — năng lực thời gian thực KHÔNG bị gỡ.** Endpoint
> `POST /api/v1/detect/frame` và bộ test của nó **giữ nguyên không đổi**. Chỉ lớp
> giao diện bị thu gọn. Đây là lý do chính khiến CSS giảm 2,36 KB và chunk khởi
> động giảm 0,74 KB.

### 2.2. Chốt cấu hình chất lượng mã Python (NFR-M6)

Thêm [`pyproject.toml`](../../pyproject.toml) — trước đợt này dự án **không có**
tệp cấu hình lint nào, nên NFR-M6 chỉ là lời hứa không đo được.

* `line-length = 100` — chọn khớp với chiều dài dòng phổ biến của mã sẵn có, để
  **tránh một đợt reformat ồ ạt vô nghĩa** làm nhiễu lịch sử git.
* `target-version = "py313"` — khớp môi trường thật (`backend/.venv`, Python 3.13.12).
* Ruff bật `E` (pycodestyle error), `F` (pyflakes), `W` (warning), `I` (sắp xếp
  import). **Cố ý không bật** các nhóm style gây tranh cãi.
* Loại trừ `backend/.venv`, `datasets`, `models`, `runs`, `node_modules`,
  `notebooks`, `htmlcov`, `storage`.
* Cấu hình pytest **để nguyên ở `pytest.ini`**, không gộp vào — gộp sẽ có nguy cơ
  đổi hành vi thu thập test.

### 2.3. Xử lý 30 lỗi `F811` — bằng cấu hình, không sửa mã test

30 lỗi `F811` (“định nghĩa trùng”) đều nằm ở `tests/backend/test_job_repository.py`,
nơi một fixture (`jobs`, `detections`, `session`, `make_job`…) được import từ
`test_repositories.py` rồi lại xuất hiện làm **tên tham số** của hàm test. Đó chính
là cách pytest dùng lại fixture dùng chung — **dương tính giả**, không phải lỗi mã.
Đổi tên tham số sẽ phá cơ chế tiêm fixture và làm hỏng 30 test.

Đã xử lý bằng `per-file-ignores` cho `tests/**/*.py`, kèm chú thích lý do ngay
trong `pyproject.toml`. **Không một dòng mã test nào bị sửa.**

### 2.4. Định dạng `scripts/build_thesis.py`

Tệp duy nhất `black` báo cần định dạng lại. Đã chạy `black` lên nó; đây là script
sinh tài liệu độc lập, không có test nào phụ thuộc. Sau khi định dạng: cú pháp
kiểm tra bằng `ast.parse` đạt, bộ test vẫn 881 pass.

### 2.5. Dọn tệp `.gitkeep` thừa

Xoá 15 tệp `.gitkeep` ở các thư mục nay đã có nội dung thật (`ai/inference/`,
`backend/`, `tests/`, `scripts/`, `models/`, `demo/`, `docs/papers/`,
`docs/reports/`, `docs/slides/`, `docs/poster/`, `frontend/`,
`deployment/docker/`, `datasets/*`). Không ảnh hưởng hành vi.

### 2.6. Đồng bộ tài liệu

Cập nhật NFR-M6 ở ba nơi cho nhất quán với số đo thật:
[`07-testing-report.md`](07-testing-report.md) §7.4 và §7.6 (bảng NFR + bảng hạn
chế mục 9), [`ch5-thuc-nghiem.md`](../papers/ch5-thuc-nghiem.md) §5.9.2 (và bản
gộp `thesis-full.md`), [`timeline.md`](../00-requirements/timeline.md) mốc M7.

NFR-M6 chuyển từ ⬜ *chưa đo* sang ⚠️ *đo được, đạt một phần* — **không** đánh dấu
✅ vì vẫn còn 83 cảnh báo `E501`. Số chỉ tiêu đã đo tăng từ 19 lên 20.

---

## 3. Những gì đã hoàn nguyên

**Không có.** Không thay đổi nào làm tụt bộ kiểm thử, nên không phải
`git checkout --` bất kỳ tệp nào.

---

## 4. Nợ kỹ thuật còn lại — có chủ đích

| # | Món nợ | Vì sao cố ý giữ | Cách trả |
|:-:|---|---|---|
| 1 | **83 lỗi `ruff` `E501`** (dòng > 100 ký tự): `scripts/fill_chapter5.py` (71), `ai/evaluation/benchmark_ocr.py` (6), `scripts/labeling/label_tool.py` (4), `ai/evaluation/evaluate.py` (1), `ai/evaluation/ocr_accuracy.py` (1) | Toàn bộ nằm trong **chuỗi ký tự tiếng Việt dài** của script sinh tài liệu và in báo cáo. Cắt dòng chỉ để lấy con số 0 sẽ làm chuỗi **khó đọc hơn** mà không cải thiện chất lượng mã. **Không tệp nào thuộc `ai/inference/` hay `backend/`** — mã chạy trong production đã sạch lint hoàn toàn | Nếu muốn về 0: thêm `per-file-ignores` cho nhóm script sinh tài liệu, hoặc nâng `line-length` cho riêng chúng |
| 2 | **1 test `xfail`** — `TestErrorBodies::test_a_failed_image_detection_records_the_failed_job` | Lỗi **đã biết và đã ghi rõ**: `DetectionService._fail_job` gọi `db.rollback()` trước khi ghi bản ghi thất bại, trong khi `_create_job` mới chỉ FLUSH (chưa commit) ở nhánh ảnh/webcam ⇒ rollback huỷ luôn dòng job, upload ảnh thất bại **không để lại dòng nào**. Sửa đúng đòi hỏi đổi ranh giới giao dịch của service — **vượt phạm vi một đợt đánh bóng** và có rủi ro lan rộng | Commit job ngay trong `_create_job`, hoặc chèn lại trong `_fail_job` sau rollback. Nhánh video không bị ảnh hưởng vì `create_video_job` commit trước khi xử lý |
| 3 | **Không có CI chạy `ruff`/`black`** | Chưa dựng pipeline CI cho dự án | Thêm bước lint vào CI để chống thoái lui NFR-M6 |
| 4 | **NFR-M3** (type hint + docstring 100%) chưa kiểm tự động | Cần `mypy` và một vòng chỉnh cấu hình riêng | Thêm `mypy --strict` theo từng module |
| 5 | Độ bao phủ thấp ở `detection_service.py` (60,8%) và `main.py` (63,2%) | Phần thiếu chủ yếu là **nhánh xử lý video chạy nền** và `lifespan` khởi động — cần môi trường thật mới phủ được | Viết integration test có worker video thật |
| 6 | **17 cảnh báo pytest** (`StarletteDeprecationWarning: HTTP_422_UNPROCESSABLE_ENTITY`) | Đến từ **thư viện `starlette` bên thứ ba**, không phải mã dự án | Tự hết khi nâng starlette/FastAPI |
| 7 | Chunk `vendor` biểu đồ 374,97 KB (gzip 104,3 KB) | `recharts` là phụ thuộc nặng nhưng **đã được tách chunk riêng** và chỉ tải khi vào trang Tổng quan — code-splitting theo route hoạt động đúng | Chỉ đáng làm nếu đổi thư viện biểu đồ |

---

## 5. Kiểm chứng hệ thống chạy thật

Ngoài bộ kiểm thử tự động, đã dựng server thật (`uvicorn`, cổng 8156) và chạy
smoke test đầu-cuối — chi tiết ở
[`13-refactor-result.json`](13-refactor-result.json) mục `system_smoke`:

* Mô hình tải được từ `models/best.pt`, thiết bị `cpu`, warm-up 2.639 ms.
* `GET /health` → 200, `model_loaded: true`, `database_connected: true`.
* Biển **1 dòng** (`51G31691`, conf 0,873 / OCR 0,999) và biển **2 dòng**
  (`59K120173`, conf 0,921 / OCR 0,954) đều đọc đúng — nhánh *split-then-hstack*
  hoạt động đúng.
* Ảnh **không có biển số** → mảng rỗng kèm HTTP 200, không báo lỗi giả.
* `GET /api/history` và `GET /api/statistics` đều 200, đầy đủ trường
  `bbox` / `raw_ocr_text` / `source_job_id`.
* Tắt server, cổng 8156 được giải phóng sạch.
* `docker compose config --quiet` hợp lệ (không rebuild image — không tệp
  Dockerfile/deployment nào bị sửa trong đợt này).

---

## 6. Trạng thái chốt

| | |
|---|---|
| **Kết luận** | 🟢 **Xanh** — không thoái lui, có cải thiện đo được |
| **Bộ kiểm thử** | 882 thu thập · **881 pass** · 1 xfail · **0 fail** |
| **Frontend** | `tsc` 0 lỗi · `eslint` sạch · build thành công |
| **Lint Python** | `black` 96/96 sạch · `ruff` 83 `E501` (nợ có chủ đích) |
| **Đã hoàn nguyên** | không có |
| **Sẵn sàng commit** | có — người điều phối thực hiện commit |
