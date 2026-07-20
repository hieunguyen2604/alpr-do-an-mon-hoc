# Báo cáo Phase 7 — Kiểm thử

**Ngày đo:** 19/07/2026
**Ngày cập nhật:** 20/07/2026 (đo lại trên mô hình chính thức `models/best.pt`; số lượng test cập nhật theo lần chạy hồi quy ghi tại [13-refactor-result.json](13-refactor-result.json))
**Trạng thái:** Bộ kiểm thử chạy sạch (**882 test thu thập / 881 đạt, 1 `xfail`, 0 fail**). **NFR-P1 ĐẠT** trên `best.pt` (5.857 ms → **731 ms** client-side / **780 ms** in-process p95). Rò rỉ dữ liệu **đã xử lý** bằng bộ `yolo_v3`; detection đo trên `best.pt` đạt cả bốn chỉ tiêu (mAP@0.5 0,9829 / mAP@0.5:0.95 0,7834). Nút thắt còn lại là **NFR-A4/A5/A6: độ chính xác OCR biển 2 dòng** (KHÔNG ĐẠT — kết quả thật, xem báo cáo OCR).

---

## 0. Ba điều phải đọc trước khi tin bất kỳ con số nào

> **⚠️ 1 — Số công bố NFR-A1/A2/A3 và NFR-P1 đã đo lại trên mô hình chính thức.**
> Các mục lịch sử dưới đây (đo trên `models/checkpoints/best-cpu-epoch7.pt`) được
> **giữ lại để ghi lại quá trình**, nhưng **số công bố** giờ đo trên
> `models/best.pt` (YOLO11n, `imgsz=640`, split v3, 20 epoch): detection mAP@0.5 =
> **0,9829**, mAP@0.5:0.95 = **0,7834**, P = **0,9837**, R = **0,9714** (đều đạt);
> NFR-P1 p95 = **731,15 ms** client-side / **780,36 ms** in-process (đạt mục tiêu
> 800 ms). Nguồn: [05-tables.md](05-tables.md), [07-benchmark-p1-resolved.json](07-benchmark-p1-resolved.json).

> **⚠️ 2 — Máy đo đang bận nặng.** Trong toàn bộ đợt đo, một tiến trình huấn
> luyện khác (`ai.training.train`, PID 27516) chiếm **~740–793% CPU** liên tục,
> và `psutil` ghi nhận CPU nền **45,3%** đã bận trước khi phép đo bắt đầu. Mọi
> con số **độ trễ** vì thế là **bi quan** — trên máy rảnh chúng sẽ tốt hơn. Mọi
> con số **độ chính xác** không bị ảnh hưởng (chúng không phụ thuộc thời gian).
> Điều này được ghi lại tự động trong trường `competing_processes` của mỗi tệp
> kết quả, không phải một lời bào chữa viết thêm về sau.

> **⚠️ 3 — Tập test có rò rỉ dữ liệu thật (bộ v1 và v2); bộ v3 đã xử lý.**
> Xem mục 6. Kết quả kiểm chứng ở ngưỡng Hamming = 5 là **0 cặp**, nhưng con số
> đó **vô nghĩa về mặt thống kê** vì mang tính vòng tròn — và lập luận đó vẫn
> đứng vững. Ở ngưỡng 10 — dải bộ chia tách **không** bảo vệ — bộ v1 có **619**
> cặp train↔test và bộ v2 có **9.126** cặp trên cả ba ranh giới. Bộ
> **`yolo_v3`** (gom nhóm ở ngưỡng **10**) đạt **0 cặp** ở ngưỡng 10 và còn
> 2.462 cặp ở ngưỡng 12 — mà kiểm bằng mắt cho thấy dải d = 12 **không chứa
> trùng lặp thật nào** (mục 6.6).
>
> **Hai đính chính đối với bản trước, cả hai đều làm bản trước SAI:**
> (a) chi tiết *"khoảng cách nhỏ nhất = 6 là dấu vết phân bố bị cắt cụt"* — SAI,
> đó là **tính chẵn cố hữu của `phash`** (mục 6.1);
> (b) cáo buộc *"cùng một tấm ảnh nằm ở hai bộ dữ liệu"* đối với cặp
> `hf_vn_plates_segment_000032` ↔ `roboflow_school_fuhih_001383` — **SAI**, kiểm
> bằng mắt cho thấy **hai xe khác nhau, hai biển số khác nhau**, chung một camera
> cố định (mục 6.5.1).

---

## 1. Chiến lược kiểm thử

Bộ kiểm thử được chia thành năm mức, mỗi mức trả lời một câu hỏi khác nhau và
được chạy bằng công cụ khác nhau.

| Mức | Câu hỏi cần trả lời | Công cụ | Nơi lưu kết quả |
|---|---|---|---|
| **Unit** | Từng đơn vị logic có đúng theo đặc tả không? | `pytest` trên `tests/test_*.py`, `tests/backend/` | mục 3 |
| **Integration** | Các tầng ghép lại qua HTTP thật có đúng không? | `pytest` + `TestClient` trên `tests/integration/` | mục 3 |
| **Kiến trúc** | Ràng buộc kiến trúc còn được giữ không? | `tests/test_architecture.py` (subprocess + quét mã nguồn) | mục 4 |
| **Độ chính xác AI** | Bộ phát hiện tốt đến đâu, và trên dữ liệu nào? | `ai/evaluation/evaluate.py` + `leak_check.py` | mục 5, 6 |
| **Hiệu năng / chịu tải** | Hệ thống đáp ứng chỉ tiêu NFR-P nào? | `ai/evaluation/benchmark_system.py`, `stress_test.py` | [07-benchmark-report.md](07-benchmark-report.md) |

**Nguyên tắc chi phối cả năm mức:** một phép kiểm thử chỉ có giá trị nếu nó có
thể **trượt**. Ba hệ quả cụ thể được áp dụng trong bộ này:

1. **Kiểm tra kiến trúc chạy trong tiến trình con.** Kiểm `sys.modules` trong
   chính tiến trình pytest là vô dụng, vì các test tích hợp đã nạp FastAPI vào
   `sys.modules` trước đó. Phép kiểm phải quan sát một trình thông dịch **sạch**.
2. **Lỗi đã biết được đánh dấu `xfail` kèm mô tả hậu quả**, không phải bị xoá đi
   hay `skip` cho qua (mục 8).
3. **Kiểm chứng rò rỉ dữ liệu được chạy ở nhiều ngưỡng**, vì chạy ở đúng ngưỡng
   mà bộ chia tách đã dùng thì kết quả "sạch" là **được bảo đảm bởi cấu tạo**,
   không phải bằng chứng.

**Cái không được kiểm thử trong phase này** — nêu thẳng: kiểm thử frontend
(Vitest), kiểm thử OCR mức ký tự (NFR-A4/A5/A6/A7), NFR-P2 (FPS webcam) và
NFR-P3 (tốc độ video). Xem mục 9.

---

## 2. Môi trường kiểm thử

Cấu hình lấy tự động bằng `platform` + `psutil` tại thời điểm đo, ghi vào
`docs/reports/07-benchmark-system.json`.

| Hạng mục | Giá trị đo được |
|---|---|
| **CPU** | **Intel(R) Core(TM) i5-14600K** |
| **Số nhân vật lý / luồng logic** | **14 / 20** |
| **RAM tổng** | **31,77 GiB** (`psutil.virtual_memory().total`) |
| **Hệ điều hành** | **Windows 11** (bản dựng Pro 26200) |
| **Python** | **3.13.12** |
| PyTorch | 2.13.0**+cpu** |
| Số luồng PyTorch | 14 |
| GPU dùng cho suy luận | **không có** — CPU-only theo quyết định AD-06 |
| CPU nền lúc bắt đầu đo | **45,3% đã bận** |
| Tiến trình cạnh tranh | `ai.training.train` @ ~793% CPU; `System` @ 29% |
| Môi trường ảo chạy test | `backend/.venv` |

> **Về con số RAM.** Tài liệu Phase 8 ghi 34,1 GB còn ở đây là 31,77 GiB. Đây là
> **cùng một thanh RAM**: 31,77 GiB × 1,0737 ≈ 34,1 GB thập phân. Báo cáo này
> dùng đơn vị nhị phân vì đó là đơn vị `psutil` trả về.

---

## 3. Kết quả unit + integration

Lệnh chạy (từ `d:/DATN`):

```bash
backend/.venv/Scripts/python.exe -m pytest --cov=ai --cov=backend \
    --cov-report=term --cov-report=html -q
```

### 3.1. Tổng kết chạy

> **Mốc số liệu.** Bảng dưới là lần chạy **mới nhất, ngày 20/07/2026**
> (`backend/.venv/Scripts/python.exe -m pytest -q`, chạy từ gốc kho `D:/DATN`),
> ghi lại tại [13-refactor-result.json](13-refactor-result.json). Lần chạy Phase 7
> ban đầu (19/07/2026) thu thập **862** test / **861** đạt — con số đó nay **đã
> lạc hậu**, bộ test được bổ sung thêm `tests/test_ocr_accuracy.py` và một test
> trong `tests/test_recognizer.py`.

| Chỉ số | Giá trị |
|---|---|
| Số test thu thập | **882** |
| **Pass** | **881** |
| **Fail** | **0** |
| `xfail` (lỗi đã biết, có mô tả) | **1** |
| `skip` | 0 |
| `error` | 0 |
| Thời gian chạy | **15,93 giây** (lệnh `pytest -q`, không bật đo bao phủ; lần chạy Phase 7 có `--cov` mất 36,70 giây) |
| Cảnh báo | 17 (đều là `DeprecationWarning` của thư viện bên thứ ba) |

### 3.2. Phân bố test theo tệp

| Tệp | Số test | Mức |
|---|---:|---|
| `tests/test_plate_rules.py` | 140 | unit |
| `tests/backend/test_schemas.py` | 87 | unit |
| `tests/backend/test_repositories.py` | 83 | unit |
| `tests/test_normalizer.py` | 79 | unit |
| `tests/backend/test_storage_service.py` | 76 | unit |
| `tests/integration/test_api_history.py` | 75 | integration |
| `tests/test_config.py` | 57 | unit |
| `tests/integration/test_api_detection.py` | 52 | integration |
| `tests/integration/test_api_statistics.py` | 40 | integration |
| `tests/test_detector.py` | 38 | unit |
| `tests/test_pipeline.py` | 31 | unit |
| `tests/test_two_line.py` | 28 | unit |
| `tests/backend/test_job_repository.py` | 26 | unit |
| `tests/test_recognizer.py` | 24 | unit |
| `tests/test_ocr_accuracy.py` | 19 | unit |
| `tests/integration/test_api_health.py` | 9 | integration |
| **`tests/test_architecture.py`** | **18** | **kiến trúc** |
| **Tổng** | **882** | |

Chia theo mức: **688 unit** (78,0%), **176 integration** (20,0%), **18 kiến
trúc** (2,0%).

### 3.3. Độ bao phủ — đối chiếu NFR-M2 (≥ 70%)

Hai con số được công bố, không phải một. Con số nào áp cho NFR-M2 được nói rõ.

| Phạm vi đo | Câu lệnh | Statements | Miss | Branch | Partial | **Cover** |
|---|---|---:|---:|---:|---:|---:|
| **Tầng nghiệp vụ** (`ai.inference` + `backend`) | cấu hình `.coveragerc` mặc định | 2.900 | 305 | 566 | 72 | **88,1%** |
| Toàn kho, gồm cả công cụ ngoại tuyến | bỏ `omit` của `ai/training`, `ai/evaluation`, `ai/data` | 5.956 | 3.348 | 1.344 | 72 | **42,0%** |

> **NFR-M2 áp cho con số 88,1%** và **đạt** (88,1% ≥ 70%), vượt chỉ tiêu 18,1
> điểm phần trăm.
>
> **Hai mốc đo, không được trộn lẫn.** Con số **88,1%** ở bảng trên là lần đo
> Phase 7 ngày **19/07/2026** (2.900 statement). Lần đo lại ngày **20/07/2026**,
> sau khi bộ test lên 882 và mã nguồn được tinh gọn, cho **87,7%** trên 2.931
> statement (317 miss) — nguồn:
> [13-refactor-result.json](13-refactor-result.json). Cả hai đều là số đo thật ở
> hai thời điểm khác nhau; khi trích dẫn phải nêu rõ mốc và nguồn. NFR-M2 vẫn
> **đạt** ở cả hai mốc (≥ 70%).
>
> **Vì sao được phép loại trừ ba gói kia — và vì sao vẫn phải công bố 42,0%.**
> `ai/training`, `ai/evaluation`, `ai/data` là **công cụ chạy ngoại tuyến từ
> dòng lệnh**: các điểm vào huấn luyện (kiểm chứng bằng cách chạy thật một lần
> huấn luyện), các bộ đo lường (chúng **tạo ra** chính những con số trong báo
> cáo này — chúng là dụng cụ đo, không phải đối tượng đo), và các script dựng bộ
> dữ liệu. NFR-M2 đặt sàn cho **mã chạy khi hệ thống phục vụ một request**.
> Nhưng loại trừ mà giấu đi con số toàn kho thì là gian lận thống kê, nên **cả
> hai đều được ghi**. Lý do loại trừ được viết sẵn thành chú thích trong
> `.coveragerc` — nó không phải quyết định đưa ra sau khi nhìn thấy kết quả.

**Bao phủ chi tiết theo module** (`--cov-report=term`, đã lọc bỏ các `__init__.py`
đạt 100%) — **số của lần đo Phase 7 ngày 19/07/2026**; số theo module của lần đo
lại ngày 20/07/2026 nằm trong [13-refactor-result.json](13-refactor-result.json):

| Module | Stmts | Miss | Cover |
|---|---:|---:|---:|
| `ai/inference/config.py` | 78 | 0 | **100,0%** |
| `ai/inference/plate_rules.py` | 97 | 0 | **100,0%** |
| `ai/inference/normalizer.py` | 84 | 1 | 98,1% |
| `ai/inference/types.py` | 70 | 2 | 95,9% |
| `ai/inference/pipeline.py` | 143 | 10 | 93,1% |
| `ai/inference/two_line.py` | 105 | 7 | 90,6% |
| `ai/inference/detector.py` | 158 | 12 | 90,5% |
| `ai/inference/recognizer.py` | 138 | 16 | 89,9% |
| `ai/inference/interfaces.py` | 11 | 2 | 81,8% |
| `backend/schemas/detection.py` | 132 | 0 | **100,0%** |
| `backend/api/routes/history.py` | 50 | 0 | **100,0%** |
| `backend/api/routes/statistics.py` | 12 | 0 | **100,0%** |
| `backend/core/exceptions.py` | 60 | 1 | 96,8% |
| `backend/models/detection.py` | 95 | 3 | 96,2% |
| `backend/repositories/job_repository.py` | 97 | 2 | 96,2% |
| `backend/api/routes/detection.py` | 38 | 1 | 95,2% |
| `backend/services/history_service.py` | 140 | 4 | 94,9% |
| `backend/services/storage_service.py` | 164 | 11 | 93,7% |
| `backend/services/statistics_service.py` | 67 | 3 | 92,0% |
| `backend/api/routes/health.py` | 31 | 3 | 90,3% |
| `backend/repositories/detection_repository.py` | 205 | 14 | 90,0% |
| `backend/core/logging.py` | 103 | 7 | 89,1% |
| `backend/core/config.py` | 130 | 12 | 87,5% |
| `backend/api/deps.py` | 44 | 6 | 82,6% |
| `backend/repositories/base.py` | 119 | 18 | 81,4% |
| **`backend/main.py`** | 136 | 48 | **63,2%** |
| **`backend/services/detection_service.py`** | 282 | 101 | **60,8%** |
| **`backend/models/database.py`** | 53 | 21 | **59,6%** |
| **TỔNG** | **2.900** | **305** | **88,1%** |

**Ba module dưới 70% — nói rõ vì sao và đó có phải vấn đề không:**

| Module | Cover | Phần chưa bao phủ | Đánh giá |
|---|---:|---|---|
| `backend/main.py` | 63,2% | dòng 192–262, 281–343 — thân hàm `build_pipeline()` nạp mô hình thật và vòng đời `lifespan` | **Chấp nhận được.** Bao phủ được đồng nghĩa với nạp `ultralytics` + PaddleOCR trong mỗi lần chạy test (≈6,4 s/lần, xem NFR-P4). Đường dẫn này **đã được kiểm chứng bằng cách chạy thật** trong đợt đo API (mục 5 của báo cáo benchmark) và bằng `curl` vào container Docker. |
| `backend/services/detection_service.py` | 60,8% | 691–754, 777–802 — nhánh xử lý **video** và **webcam** | **Nợ kỹ thuật có thật.** Chỉ nhánh ảnh tĩnh được kiểm thử tự động đầy đủ. Đây cũng là lý do NFR-P2/P3 chưa đo được (mục 9). |
| `backend/models/database.py` | 59,6% | 88–99, 177–181, 206–214 — cấu hình engine cho PostgreSQL và các nhánh dọn dẹp | **Chấp nhận được.** Hệ thống chạy trên SQLite (quyết định kiến trúc); nhánh PostgreSQL là mã dự phòng chưa dùng đến. |

Báo cáo HTML đầy đủ: `htmlcov/index.html`.

---

## 4. Kiểm thử kiến trúc tự động (NFR-M1, NFR-M4, NFR-M5)

`tests/test_architecture.py` — **18/18 pass**.

Đây là phần đáng chú ý nhất về mặt phương pháp: nó biến ba dòng văn xuôi trong
tài liệu kiến trúc thành ba phép kiểm có thể trượt.

### 4.1. NFR-M1 — `ai/` không được import FastAPI/Pydantic

| Nhóm kiểm | Số test | Cách kiểm | Kết quả |
|---|---:|---|---|
| Quét tĩnh toàn bộ `ai/` với 4 module cấm (`fastapi`, `pydantic`, `pydantic_settings`, `starlette`) | 4 | regex trên **câu lệnh import chữ thường**, quét mọi tệp `.py` | **0 vi phạm** |
| Quét tĩnh `ai/inference/` với 6 module cấm (thêm `sqlalchemy`, `backend`) | 6 | như trên, phạm vi chặt hơn | **0 vi phạm** |
| Import trong **trình thông dịch sạch** (subprocess) rồi soi `sys.modules` | 1 | `subprocess` + `python -c` | **không module cấm nào bị nạp** |
| Mỗi module trong `ai/inference/` import độc lập được | 1 | 10 lần import riêng lẻ | **pass** |
| Dựng được `ALPRPipeline` từ các đối tượng giả, **không cần runtime ML** | 1 | tiêm phụ thuộc bằng fake | **pass** |
| `ai/evaluation/` giữ các import `backend` ở **mức hàm** | 1 | quét vị trí câu lệnh import | **pass** |
| Gói `ai/` thật sự có tệp mã nguồn (chống test rỗng) | 1 | đếm tệp | **pass** |

**Hai chi tiết thiết kế đáng bảo vệ trước hội đồng:**

1. **Vì sao phải dùng subprocess.** Cách kiểm hiển nhiên — `import ai.inference`
   rồi nhìn `sys.modules` — **vô giá trị bên trong bộ test này**, vì 176 test
   tích hợp đã import `backend` và nạp FastAPI vào `sys.modules` từ trước.
   Phép kiểm bắt buộc phải quan sát một trình thông dịch chưa import gì cả.
2. **Vì sao chỉ khớp import chữ thường.** Tài liệu bên trong `ai/` cố tình viết
   hoa tên sản phẩm ("FastAPI", "Pydantic") để văn xuôi **giải thích** ràng buộc
   không bị chính phép kiểm ràng buộc đó bắt nhầm. Đây là một quy ước có chủ ý,
   ghi rõ trong docstring của tệp test.

**Ngoại lệ được cấp cho `ai/evaluation/`, và lý do.** Gói này được phép import
`sqlalchemy`/`backend`, nhưng **chỉ ở mức hàm**. Lý do: bộ `stress_test.py` tồn
tại để đo **NFR-P6 — truy vấn lịch sử trên 10.000 bản ghi**; nó không thể đo
được điều đó nếu không chạm tới chính cái schema đang là đối tượng đo. Cấm nó
không làm kiến trúc sạch hơn — chỉ làm chỉ tiêu trở nên **không đo được**. Vì
import nằm trong thân hàm, việc `import ai.evaluation` không kéo theo gì cả.
Ranh giới này được thực thi bằng một test riêng, không phải bằng lời hứa.

### 4.2. NFR-M4 — không hard-code đường dẫn

| Kiểm | Kết quả |
|---|---|
| Không tệp nào trong `ai/` chứa literal đường dẫn tuyệt đối | **pass** |
| Không tệp nào trong `backend/` chứa literal đường dẫn tuyệt đối | **pass** |
| Cả hai module cấu hình đều suy ra thư mục gốc từ `__file__` | **pass** |

**NFR-M4: đạt — 0 vi phạm**, kiểm bằng phân tích tự động chứ không bằng grep thủ công.

### 4.3. NFR-M5 — thay được bộ OCR mà không sửa tầng API

Kiểm chứng gián tiếp và có thật: `ALPRPipeline.__init__(detector, recognizer,
normalizer, config=None)` nhận toàn bộ phụ thuộc qua tham số. Test
`test_the_pipeline_can_be_built_from_fakes_without_an_ml_runtime` dựng được một
pipeline hoàn chỉnh từ ba đối tượng giả, **không cần ultralytics hay PaddleOCR**.
Nếu tầng API có nắm giữ một engine cụ thể, test này sẽ không chạy nổi.
**NFR-M5: đạt.**

---

## 5. Độ chính xác của bộ phát hiện

**Nguồn:** `docs/reports/03-evaluation-07-detection-test.json`, hợp nhất vào
`07-benchmark-data.json`.

### 5.1. Điều kiện đo

> ### ✅ SỐ CÔNG BỐ ĐÃ ĐO LẠI TRÊN `best.pt` / SPLIT V3
>
> Toàn bộ mục 5 này là phép đo **lịch sử** trên checkpoint epoch 7 và bộ v1 (458
> ảnh test). **Số detection công bố** giờ đo trên mô hình chính thức `models/best.pt`
> (split v3, 1.514 ảnh test): mAP@0.5 = **0,9829**, mAP@0.5:0.95 = **0,7834**,
> Precision = **0,9837**, Recall = **0,9714** — đều **ĐẠT**, đo trên split đã khử
> trùng lặp nên **không còn bị rò rỉ thổi phồng** như bộ v1. Nguồn: [05-tables.md §T5.5a](05-tables.md).

| Hạng mục | Giá trị |
|---|---|
| Trọng số | `models/checkpoints/best-cpu-epoch7.pt` (20,22 MB) — **checkpoint giữa chừng, chỉ lịch sử** |
| Bộ dữ liệu | `datasets/processed/yolo/data.yaml`, split **test** |
| Số ảnh | **458** |
| Số box ground-truth | **512** |
| Lớp | 1 lớp — `license_plate` |
| `imgsz` | 640 |
| `conf` / `iou` | 0,25 / 0,45 |
| Thiết bị | CPU |
| Ngưỡng phân loại 1 dòng / 2 dòng | tỉ lệ khung ≥ 2,5 ⇒ 1 dòng |
| Chất lượng nhãn | 0 ảnh thiếu nhãn, 0 dòng nhãn hỏng, 512/512 box phân nhóm được |

> **Lưu ý về bộ dữ liệu.** Đây là bộ **v1** (`datasets/processed/yolo/`,
> 3.203 train / 917 val / 458 test = 4.578 ảnh), **không phải bộ v3** 15.133 ảnh.
> Mô hình cuối cùng `best.pt` đã huấn luyện và đánh giá trên **v3**; con số ở mục
> này không so trực tiếp được với số công bố.

### 5.2. Hai bộ số, và bộ nào áp cho NFR-A3

Đây là điểm dễ bị hội đồng chất vấn nhất, nên nói thẳng: **báo cáo có hai bộ
Precision/Recall khác nhau rất xa**, và chúng không mâu thuẫn.

| Nguồn số | mAP@0.5 | mAP@0.5:0.95 | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|
| **Ultralytics `val()`** — tại ngưỡng confidence **tối ưu theo F1** | **0,9827** | **0,8043** | **0,9346** | **0,9453** | **0,9399** |
| Bộ đo riêng — tại ngưỡng confidence **cố định 0,25** | 0,9635 | 0,7931 | 0,7372 | 0,9805 | 0,8416 |

**Giải thích chênh lệch.** Ở `conf = 0,25`, mô hình sinh **681 dự đoán** cho
**512 box thật**: 502 TP, **179 FP**, 10 FN. Recall rất cao (0,980) đúng như kỳ
vọng của một ngưỡng thấp, nhưng 179 dự đoán thừa kéo Precision xuống 0,737. Khi
nâng ngưỡng lên mức tối ưu F1, phần lớn FP bị loại và Precision lên 0,935 với
Recall gần như không đổi.

**NFR-A3 quy định rõ trong đặc tả: "Tại ngưỡng confidence tối ưu theo F1".** Vì
vậy **bộ số Ultralytics là bộ áp cho NFR-A3**, và nó **đạt** (P 0,935 ≥ 0,92;
R 0,945 ≥ 0,90). Bộ số ở ngưỡng cố định được giữ lại trong báo cáo vì nó cho
biết một điều mà bộ kia giấu đi: **ngưỡng mặc định 0,25 quá thấp cho mô hình
này** — một quan sát có giá trị vận hành trực tiếp.

### 5.3. NFR-A8 — tách riêng biển 1 dòng và 2 dòng

| Chỉ số | **Biển 1 dòng** | **Biển 2 dòng** | Chênh lệch |
|---|---:|---:|---:|
| Số box ground-truth | 153 (29,9%) | **359 (70,1%)** | |
| mAP@0.5 | **0,9856** | 0,9592 | −0,0264 |
| mAP@0.5:0.95 | 0,7548 | **0,8086** | **+0,0538** |
| Precision (@conf 0,25) | 0,8032 | 0,7120 | −0,0912 |
| Recall (@conf 0,25) | 0,9869 | 0,9777 | −0,0092 |
| F1 (@conf 0,25) | 0,8856 | 0,8239 | −0,0617 |
| TP / FP / FN | 151 / 37 / 2 | 351 / 142 / 8 | |

**Khoảng cách AP50 (NFR-A8): 0,0264.**

**Ba nhận định — và một trong số đó đi ngược trực giác:**

1. **Ở mức phát hiện, biển 2 dòng không hề khó hơn đáng kể.** Chênh lệch mAP@0.5
   chỉ 2,6 điểm phần trăm. Rủi ro R-04 ("biển 2 dòng là điểm gãy") được đặt ra ở
   Phase 0 là rủi ro của khâu **OCR**, không phải khâu **phát hiện** — và số liệu
   này ủng hộ đúng cách đọc đó.
2. **Biển 2 dòng lại khớp box *chính xác hơn*** — mAP@0.5:0.95 cao hơn 5,4 điểm
   phần trăm. Giải thích hợp lý: biển 2 dòng gần hình vuông, tỉ lệ khung ổn định
   hơn nên hồi quy box dễ hơn; biển 1 dòng rất dẹt, chỉ lệch vài pixel theo chiều
   cao là IoU tụt nhanh. Đây là hệ quả hình học, không phải hệ quả của dữ liệu.
3. **Precision của biển 2 dòng thấp hơn rõ (0,712 vs 0,803).** 142/179 tổng số
   FP rơi vào nhóm 2 dòng. Cần lưu ý: nhóm này cũng chiếm 70,1% dữ liệu, nên một
   phần chênh lệch chỉ là hiệu ứng tỉ trọng.

**Chưa làm được:** NFR-A9 (tách theo điều kiện ảnh: ngày/đêm/nghiêng/mờ) — bộ dữ
liệu hiện không có nhãn điều kiện. Và **chưa tách theo dải kích thước box**, dù
báo cáo dataset v2 đã ghi nhận 10,91% box nhỏ hơn 0,5% diện tích ảnh (vi phạm
tiêu chí Q6) và yêu cầu bắt buộc phải tách. Đây là món nợ phải trả khi đo lại
trên mô hình cuối.

### 5.4. Độ trễ của riêng bộ phát hiện

| Chỉ số | Giá trị |
|---|---:|
| Số mẫu | 150 |
| Trung bình | 57,95 ms |
| p50 | **49,61 ms** |
| p95 | 64,54 ms |
| p99 | 74,78 ms |
| min / max | 28,32 / **1.240,26** ms |
| FPS tại p50 | **20,16** |

Giá trị `max` 1.240 ms là **lần suy luận đầu tiên** (chi phí khởi động lười của
PyTorch), không phải hành vi ổn định — chênh 25 lần so với p99 xác nhận điều đó.

**Biểu đồ:** `figures/07-detection-test_pr_curve.png` (đường PR tách theo số
dòng), `figures/07-detection-test_confusion_matrix.png`,
`figures/07-detection-test_latency.png`, cùng bộ biểu đồ gốc của Ultralytics
(`figures/ultralytics_Box*.png`).

---

## 6. Kiểm chứng rò rỉ dữ liệu — mục quan trọng nhất của báo cáo này

**Nguồn:** `docs/reports/07-leak-check.json` (ngưỡng 5),
`07-leak-check-t10.json` (ngưỡng 10). Phương pháp: `imagehash.phash`, 64 bit,
so khoảng cách Hamming từng cặp ảnh chéo split.

### 6.1. Ở ngưỡng Hamming ≤ 5 — kết quả "sạch", nhưng KHÔNG được dùng làm bằng chứng

| Cặp split | Số ảnh A | Số ảnh B | Số cặp so sánh | **Cặp gần trùng** | Khoảng cách nhỏ nhất |
|---|---:|---:|---:|---:|---:|
| train ↔ val | 3.203 | 917 | 2.937.151 | **0** | 6 |
| **train ↔ test** | 3.203 | 458 | 1.466.974 | **0** | 6 |
| val ↔ test | 917 | 458 | 419.986 | **0** | 6 |

**Kết quả: 0 cặp trên 4,82 triệu phép so sánh. Và con số này gần như vô giá trị.**

Lý do — trích thẳng cảnh báo do chính công cụ đo sinh ra:

> Đường dây dựng bộ dữ liệu (`scripts/dataset/deduplicate.py`) gom nhóm ảnh bằng
> `imagehash.phash` ở `DEFAULT_THRESHOLD = 5`, và `scripts/dataset/split.py` giữ
> nguyên vẹn mỗi nhóm trùng lặp trong **cùng một** split. Phép kiểm này dùng
> **cùng một hàm băm và cùng một ngưỡng**, nên kết quả 0 cặp là **được bảo đảm
> bởi cấu tạo**. Nó xác nhận bộ chia tách đã làm đúng việc của nó; nó **KHÔNG**
> phải bằng chứng độc lập rằng bài toán khó hay rằng split không bị nhiễm bẩn.

Đây là **lập luận vòng tròn**: đo bằng chính thước đã dùng để cắt. Lập luận này
vẫn đúng nguyên vẹn, và nó là kết luận có giá trị nhất của mục 6.

> #### ⚠️ Đính chính một lập luận phụ trong bản trước
>
> Bản trước của mục này còn viết thêm: *"chi tiết «khoảng cách nhỏ nhất = 6» ở cả
> ba cặp split là dấu vết lộ liễu của điều đó — phân bố bị cắt cụt đúng tại
> ngưỡng"*. **Lập luận phụ này SAI, và đã được bác bỏ bằng phép đo.** Khoảng cách
> Hamming giữa hai giá trị `imagehash.phash` trên corpus này **luôn là số chẵn**,
> nên "nhỏ nhất = 6" chỉ là giá trị chẵn kế tiếp sau ngưỡng 5 chứ không phải phân
> bố bị cắt cụt; hệ quả vận hành là mọi ngưỡng lẻ đều vô nghĩa (15 hệt 14). Chứng
> minh và số liệu kiểm chứng: [`02-dataset-report.md` §6bis.1](02-dataset-report.md).
>
> Kết luận vòng tròn **không phụ thuộc** vào lập luận phụ này. Nó đứng vững chỉ
> bằng một sự kiện: cùng hàm băm, cùng ngưỡng, dùng cho cả khâu chia lẫn khâu kiểm.

### 6.2. Ở ngưỡng Hamming ≤ 10 — có rò rỉ thật

Chạy lại ở ngưỡng 10, tức là **dải mà bộ chia tách không hề bảo vệ**:

| Cặp split | Số cặp so sánh | **Cặp gần trùng (≤10)** | Kết luận |
|---|---:|---:|---|
| **train ↔ test** | 1.466.974 | **619** | **PHÁT HIỆN RÒ RỈ** |

Phân bố khoảng cách train ↔ test:

| Dải khoảng cách Hamming | Số cặp | Ghi chú |
|---|---:|---|
| 0 | 0 | |
| 1–5 | 0 | dải bộ chia tách đã bảo vệ |
| **6–10** | **619** | **dải KHÔNG được bảo vệ — đây là phần rò rỉ** |
| 11–15 | 3.016 | |
| 16–20 | 26.135 | |
| > 20 | 1.437.204 | 97,97% — phần lớn dữ liệu thật sự khác nhau |

Phân bố khoảng cách trong 400 cặp mẫu được ghi lại: **27 cặp ở d=6, 107 cặp ở
d=8, 266 cặp ở d=10**. Ví dụ đầu tiên:

```
train: images/train/hf_vn_plates_segment_000006.png
test:  images/test/hf_vn_plates_segment_000061.png    (d = 10)
```

Kiểm tra bằng mắt các cặp gần nhất cho thấy **cùng một chiếc xe và cùng một
chuỗi biển số xuất hiện ở cả train lẫn test**.

### 6.3. Đánh giá trung thực và ảnh hưởng lên mAP

> **✅ Đã xử lý ở mô hình chính thức.** Phần rò rỉ 619 cặp dưới đây là của **bộ v1**
> (mô hình baseline đối chứng). Mô hình chính thức `best.pt` huấn luyện trên
> **split v3 đã khử trùng lặp ở ngưỡng 10**, nên mAP công bố (0,9829) **không còn
> bị rò rỉ thổi phồng** như con số 0,9933 của baseline v1. Lưu ý phương pháp luận
> giữ nguyên: phash không bắt được rò rỉ ở mức ngữ nghĩa (cùng biển chụp góc khác),
> nên không thể khẳng định tuyệt đối tập test v3 "sạch" — xem T5.3b.

**Kết luận (áp cho bộ v1 / baseline): có rò rỉ dữ liệu thật. mAP@0.5 = 0,9827 (baseline epoch 7 trên v1) là con số LẠC QUAN.**

Định lượng mức ảnh hưởng:

- 619 cặp rò rỉ liên quan tối đa 619 ảnh test (thực tế ít hơn, vì một ảnh train
  có thể ghép với nhiều ảnh test và ngược lại). Tập test chỉ có **458 ảnh**.
- Giới hạn trên xấu nhất: nếu mỗi cặp là một ảnh test riêng biệt thì toàn bộ tập
  test đã bị nhiễm. Giới hạn dưới lạc quan nhất: nếu 619 cặp chỉ tập trung vào
  vài chục ảnh thì mức nhiễm là nhỏ.
- **Số ảnh test bị nhiễm thực sự chưa được đếm** — công cụ hiện chỉ đếm *cặp*,
  chưa đếm *ảnh riêng biệt*. Đây là hạn chế của phép đo, ghi nhận ở mục 9.

**Ba lý do không được đổ hết mAP cao cho rò rỉ:**

1. Ngay cả ở dải 6–10, phần lớn 619 cặp nằm ở d=10 — mức "cùng cảnh, khác khung
   hình" chứ chưa hẳn là ảnh trùng.
2. 97,97% số cặp có khoảng cách > 20, tức phần lớn tập test vẫn khác train.
3. Bài toán phát hiện 1 lớp trên biển số vốn dễ đạt mAP@0.5 cao; 0,98 không phải
   con số bất thường đến mức chỉ có thể giải thích bằng rò rỉ.

**Nhưng cũng không được dùng ba lý do trên để bỏ qua vấn đề.** Có bằng chứng
trực tiếp bằng mắt về cùng xe, cùng biển ở hai split.

### 6.4. Trùng lặp trong nội bộ từng split (ngưỡng 5)

| Split | Số ảnh | Cặp gần trùng nội bộ |
|---|---:|---:|
| train | 3.203 | 131 |
| val | 917 | 41 |
| test | **458** | **21** |

21 cặp trùng nội bộ trong tập test 458 ảnh nghĩa là tập test **kém đa dạng hơn
kích thước danh nghĩa của nó**, làm mọi ước lượng độ chính xác có phương sai
lớn hơn con số điểm gợi ý.

### 6.5. Bộ v2 ở ngưỡng 10 — rò rỉ trên toàn bộ ba cặp split

Bản trước chỉ đo được cặp train ↔ test của bộ **v1**. Đã chạy đủ ba cặp trên bộ
**v2** (`datasets/processed/yolo_v2/`, 15.133 ảnh) ở ngưỡng 10 — dải mà
`split.py` **không** bảo vệ:

| Cặp split | **Cặp gần trùng (d ≤ 10)** | d = 6 | d = 8 | d = 10 | Số cặp so sánh | Tỷ lệ |
|---|---:|---:|---:|---:|---:|---:|
| **train ↔ val** | **5.637** | 462 | 1.339 | 3.836 | 32.066.520 | 0,0176% |
| **train ↔ test** | **2.699** | 240 | 676 | 1.783 | 16.043.850 | 0,0168% |
| **val ↔ test** | **790** | 71 | 191 | 528 | 4.587.420 | 0,0172% |
| **Tổng** | **9.126** | 773 | 2.206 | 6.147 | 52.697.790 | — |

Khoảng cách nhỏ nhất là **6** ở cả ba cặp — nhưng theo đính chính ở mục 6.1, đó
là **hệ quả của tính chẵn của `phash`**, không phải dấu hiệu phân bố bị cắt cụt.

**So với v1, v2 tốt hơn về mặt tương đối:** tỷ lệ cặp train ↔ test giảm từ
0,0422% (v1) xuống 0,0168% (v2), tức **tốt hơn khoảng 2,5 lần**. Việc gộp thêm
bộ nguồn làm phân bố rộng ra thật, không chỉ làm số ảnh to ra.

#### 6.5.1. Một cáo buộc trong bản trước đã bị bác bỏ

Bản trước cáo buộc cặp `hf_vn_plates_segment_000032.png` ↔
`roboflow_school_fuhih_001383.jpg` (d = 10) là "cùng một tấm ảnh nằm ở hai bộ dữ
liệu khác nhau". **Đã kiểm tra bằng mắt: cáo buộc SAI** — đó là hai xe khác nhau
(Land Cruiser 52Y-6490 vs Hiace 51F-220.29) chỉ chung một camera barrier cố
định, tức **dương tính giả** của `phash` trên corpus bị camera tĩnh chi phối.
Bảng đối chiếu đầy đủ: [`02-dataset-report.md` §6bis.3 và khối đính chính kèm
theo](02-dataset-report.md).

Ghi lại sai sót này là bắt buộc: bản trước đã kết luận "cùng một tấm ảnh" **chỉ
từ khoảng cách hash, không mở ảnh ra xem**. Đó đúng là lỗi phương pháp mà mục 6
này tồn tại để chống lại.

### 6.6. Kiểm tra bằng mắt theo từng mức khoảng cách — trùng thật nằm ở đâu

Nguồn: `datasets/reports/v3/visual_inspection.json`. Phương pháp: dựng ảnh ghép
đôi ở từng khoảng cách Hamming cố định, đọc bằng mắt, và với mỗi cặp trả lời một
câu hỏi duy nhất — **cùng một chiếc xe (cùng chuỗi biển số)**, hay chỉ **cùng
một cảnh camera**?

| d | Phán quyết | Ví dụ **trùng thật** | Ví dụ **dương tính giả** |
|:-:|---|---|---|
| **6** | HỖN HỢP | Hyundai đỏ 30F-322.45 xuất hiện hai lần, crop gần như y hệt; xe máy trắng, khung hình y hệt, cùng dấu thời gian 2000-01-09 07:14:43 | 63-H5 1336 vs 72-C1 050.18; 51-U7 4598 vs 51-V4 4579 |
| **8** | HỖN HỢP | Hyundai trắng 30A-620.43, cùng xe, hai khung hình liên tiếp | 63-B8 552.46 vs 93-L1 012.80; 75-F1 298.30 vs 73-G1 175.44 |
| **10** | HỖN HỢP — **xác nhận trùng chéo nguồn** | Biển **59-L2 237.14**, cùng một xe máy, có mặt trong **cả** `hf_vn_plates_segment_001346.png` **và** `roboflow_school_fuhih_005961.jpg` | 61-D1 079.11 vs 59-Y1 919.82; 55-P2 3999 vs 63-V5 0914 |
| **12** | **KHÔNG thấy trùng thật nào** trong mẫu | *(không có)* | 59-B3 761.93 vs 59-L2 054.42; Mazda 30F-204.49 vs Chevrolet 29D-215.96; Ford 30A-601.68 vs Ford 61A-775.29 |
| **14** | Hầu hết là dương tính giả, nhưng **có một cặp cùng xe** | Biển **51F-155.85**, cùng chiếc Hyundai trắng, **hai lần ghé** cùng một barrier (04/12/2017 07:47:33 và 02/12/2017 13:08:21) | 51F-222.61 vs Audi 51G-510.08; 51A-554.33 vs 29D-3263 |

Ảnh ghép đôi đã lưu tại `datasets/reports/v3/cross_split_samples/`.

**Ba kết luận rút ra, và cả ba đều đi ngược trực giác ban đầu:**

1. **Trùng lặp thật sống ở dải d = 6–10**, chứ không phải ở d ≤ 5. Ngưỡng 5 của
   `DEFAULT_THRESHOLD` là **quá chặt** — nó bỏ sót phần lớn trùng lặp thật.
2. **Từ d = 12 trở lên, mẫu bị dương tính giả chi phối.** Nới ngưỡng thêm nữa
   không mua thêm được độ sạch, chỉ mua thêm nhiễu.
3. **Cặp `51F-155.85` ở d = 14 là rủi ro tồn dư có thật và không xoá được bằng
   `phash`.** Đó không phải cùng một tấm ảnh mà là **cùng một chiếc xe quay lại
   cùng một camera vào một ngày khác**. Không hàm băm tri giác nào tách được
   trường hợp này khỏi một chiếc xe lạ trong cùng khung cảnh; chỉ có gom nhóm
   **theo chuỗi biển số** mới làm được, mà corpus phát hiện này **không có** bản
   chép chuỗi biển số (chỉ bộ `roboflow_ocr_plate` riêng biệt mới có).

### 6.7. Bộ v3 sau khi chia lại — kết quả kiểm chứng

Bộ **`datasets/processed/yolo_v3/`** được chia lại từ `merged_v2` với **ngưỡng
gom nhóm = 10** (không phải 12 — lý do ở mục 6.7.1), giữ nguyên mỗi nhóm trong
cùng một split.

**Nguồn:** `datasets/reports/split_report.json`,
`datasets/reports/v3/leakage_by_threshold.json`.

| Chỉ số | Giá trị |
|---|---:|
| Ảnh tổng | 15.133 |
| train / val / test | **10.592 / 3.027 / 1.514** (0,6999 / 0,200 / 0,100) |
| Đơn vị chia (nhóm + ảnh đơn) | 7.906 |
| Nhóm nhiều hơn 1 ảnh | 1.171 |
| Ảnh nằm trong nhóm | 8.398 (**55,49%**) |
| Nhóm lớn nhất | **4.411 ảnh** (29,15% corpus) — nằm trọn trong train |

Kết quả kiểm chứng rò rỉ, chạy ở **năm** ngưỡng:

| Ngưỡng | Trạng thái phép đo | **Tổng cặp vắt split** | train↔val | train↔test | val↔test | d nhỏ nhất |
|---:|---|---:|---:|---:|---:|---:|
| 5 | *bảo đảm bởi cấu tạo* | **0** | 0 | 0 | 0 | — |
| **10** | *bảo đảm bởi cấu tạo* | **0** | 0 | 0 | 0 | — |
| **12** | **ĐỘC LẬP** | **2.462** | 1.454 | 791 | 217 | **12** |
| **15** | **ĐỘC LẬP** | **10.798** | 6.391 | 3.529 | 878 | **12** |
| **20** | **ĐỘC LẬP** | **429.548** | 256.557 | 137.506 | 35.485 | **12** |

**Cách đọc bảng này — quan trọng, và chính công cụ đo tự ghi ra cảnh báo:**

> Các dòng ghi *"bảo đảm bởi cấu tạo"* là **hệ quả logic** của việc gom nhóm ở
> ngưỡng 10 rồi chia theo nhóm. Số 0 ở đó xác nhận **bộ chia tách chạy đúng**,
> nhưng **KHÔNG** phải bằng chứng rằng ngưỡng đã đủ. Chỉ các dòng *"ĐỘC LẬP"*
> mới mang thông tin — và ngay cả chúng cũng chỉ là **giới hạn trên**: trên một
> corpus bị camera tĩnh chi phối, hai khung hình của hai xe khác nhau từ cùng
> một camera là gần nhau về tri giác mà không hề trùng lặp.

**Vậy kết quả thật là gì?** Ba điều, nói thẳng:

1. **Ở ngưỡng 10 — ngưỡng mà mục 6.6 xác nhận bằng mắt là nơi trùng lặp thật kết
   thúc — bộ v3 sạch tuyệt đối trên cả ba cặp split.** So với bộ v2 ở cùng ngưỡng
   (9.126 cặp), đây là mức cải thiện **tuyệt đối**, không phải tương đối.
2. **Ở ngưỡng 12 vẫn còn 2.462 cặp.** Nhưng mục 6.6 cho thấy mẫu ở d = 12 **không
   chứa trùng lặp thật nào** khi soi bằng mắt — nên con số này gần như hoàn toàn
   là dương tính giả cùng-camera.
3. **Rủi ro tồn dư vẫn còn và phải ghi nhận:** cặp `51F-155.85` ở d = 14 (mục
   6.6) là **cùng một chiếc xe rơi vào hai split khác nhau của chính `yolo_v3`**.
   `phash` không xoá được nó. Bộ v3 **sạch về trùng ảnh**, **chưa sạch tuyệt đối
   về trùng phương tiện**.

#### 6.7.1. Vì sao chọn ngưỡng 10 chứ không phải 12 như đề xuất ban đầu

Hướng xử lý #1 ở bản trước đề nghị nâng ngưỡng lên 10 rồi kiểm ở 15. Trong quá
trình thực hiện đã quét ngưỡng từ 5 đến 20 và phát hiện một trở ngại mà đề xuất
ban đầu không lường trước.

**Nguồn:** `datasets/reports/v3/grouping_threshold_sweep.json`.

| Ngưỡng | Số cặp | Số nhóm | Ảnh trong nhóm | % corpus | **Thành phần liên thông lớn nhất** | % corpus | Chia 70/20/10 khả thi? |
|---:|---:|---:|---:|---:|---:|---:|:---:|
| 5 | 0 | 0 | 0 | 0,0% | 1 | 0,0% | ✅ |
| 6 | 1.637 | 965 | 2.510 | 16,6% | 50 | 0,3% | ✅ |
| 8 | 6.303 | 1.244 | 5.634 | 37,2% | 1.171 | 7,7% | ✅ |
| **10** | 19.277 | 1.171 | 8.398 | 55,5% | **4.411** | **29,1%** | ✅ **← đã chọn** |
| 12 | 51.467 | 852 | 10.596 | 70,0% | **8.262** | **54,6%** | ✅ *(nhưng xem dưới)* |
| 14 | 122.837 | 382 | 12.690 | 83,9% | **11.673** | **77,1%** | ❌ |
| 15 | 122.837 | 382 | 12.690 | 83,9% | 11.673 | 77,1% | ❌ *(hệt 14 — tính chẵn)* |
| 20 | 1.471.347 | 1 | 15.133 | 100,0% | **15.133** | **100,0%** | ❌ |

**Ngưỡng 10 là giá trị cao nhất thoả đồng thời hai điều kiện:** (a) vẫn còn xác
nhận được trùng lặp thật bằng mắt (mục 6.6), và (b) chưa làm phép chia sụp đổ vì
hiện tượng **bao đóng bắc cầu bị thẩm thấu** — từ ngưỡng 12 trở lên thành phần
liên thông lớn nhất nuốt quá nửa corpus, và từ 14 trở lên vượt 70% nên **không
thể** chia 70/20/10 nữa. Lập luận percolation đầy đủ và phân tích từng mức ngưỡng
10 / 12 / 14: [`02-dataset-report.md` §6bis.2](02-dataset-report.md).

#### 6.7.2. Chi phí của việc chia lại

Việc gom nhóm ở ngưỡng 10 **không miễn phí**. Nguồn:
`datasets/reports/v3/regroup_cost.json`.

| Chi phí | Số đo | Ý nghĩa |
|---|---:|---|
| Ảnh bị ràng buộc vào nhóm | **8.398 / 15.133 (55,49%)** | Hơn nửa corpus mất tự do phân bổ; bộ chia chỉ còn **7.906** đơn vị thay vì 15.133 |
| Thành phần lớn nhất | **4.411 ảnh** | Một khối duy nhất bằng 29,15% corpus, **41,64%** tập train — buộc phải vào train, không có lựa chọn |
| Đơn vị đơn lẻ còn lại | 6.735 | Chỉ số này mới là "bậc tự do" thật của phép chia |
| Mười nhóm lớn nhất | 4.411 · 368 · 170 · 168 · 70 · 63 · 44 · 35 · 20 · 18 | Phân bố đuôi dài cực đoan — một nhóm áp đảo, phần còn lại nhỏ |

**Hệ quả phải chấp nhận:** vì thành phần 4.411 ảnh bị ghim vào train, tỷ lệ
nguồn giữa ba split **không còn cân bằng như bộ v2** — tập test nghiêng về
`roboflow_traffic_camera` (35,3% test so với 18,0% train) và nhẹ đi ở
`hf_vn_plates_segment` (21,7% so với 31,2%). Đây thực chất là **hiệu ứng có lợi**
(test lệch ra xa train ⇒ ước lượng bi quan chứ không lạc quan), nhưng phải công
bố vì nó có nghĩa là v3 test **không** phải mẫu ngẫu nhiên đại diện cho corpus.
Cân bằng số dòng biển (tiêu chí phân tầng) thì vẫn giữ được ở cả ba split.
Bảng phân bố nguồn và bảng số dòng biển đầy đủ:
[`02-dataset-report.md` §6bis.5](02-dataset-report.md).

### 6.8. Hướng xử lý — ba việc cụ thể, xếp theo mức độ quan trọng

| # | Việc | Vì sao | Trạng thái |
|:-:|---|---|---|
| **1** | **Nâng ngưỡng gom nhóm lên 10** rồi chia lại, và **kiểm chứng ở ngưỡng cao hơn** | Phá vỡ tính vòng tròn ở mục 6.1 | ✅ **ĐÃ LÀM** — bộ `yolo_v3`, gom nhóm ở 10, kiểm độc lập ở 12/15/20 (mục 6.7). Ngưỡng 15 mà bản trước đề nghị hoá ra **bất khả thi để chia** (mục 6.7.1) |
| **2** | **Dựng tập test xuyên bộ dữ liệu** (giữ trọn 1–2 bộ nguồn ra ngoài, không trộn) | Đây là cách duy nhất loại bỏ triệt để rò rỉ theo cảnh/theo xe, đồng thời đo được khả năng khái quát hoá. README đã ghi đây là món nợ lớn nhất của khâu dữ liệu | **Chưa làm** — và mục 6.6 làm nó **cấp thiết hơn**: rủi ro tồn dư `51F-155.85` (cùng xe, hai ngày, hai split) chỉ biến mất khi tách theo nguồn |
| **3** | **Sửa công cụ để đếm số *ảnh test* bị nhiễm**, không chỉ đếm số *cặp* | Không có con số này thì không định lượng được mức ảnh hưởng lên mAP | **Chưa làm** — nhưng đã **giảm mức quan trọng**: trên `yolo_v3` số cặp ở ngưỡng 10 là 0, nên không còn ảnh nhiễm nào để đếm ở dải đó |

**Biểu đồ:** `figures/07-leak-distance-distribution.png`.

#### 6.8.1. Việc mới phát sinh — bắt buộc, chưa làm

| # | Việc | Vì sao |
|:-:|---|---|
| **4** | **Đánh giá lại mọi mô hình trên đúng bộ mà nó được huấn luyện.** Cụ thể: **KHÔNG** dùng `baseline-416-v1.pt` (huấn luyện trên split **v1**) để đo trên tập test **v3** | **289 / 1.514 ảnh test của v3 (19,1%) nằm trong tập train+val của v1** — kiểm bằng trùng khớp **tên tệp chính xác**, không phải hash. Xem cảnh báo ở mục 7.2 |
| **5** | **Sửa `DEFAULT_THRESHOLD` trong `scripts/dataset/deduplicate.py` từ 5 lên 10** và ghi chú tính chẵn của `phash` vào mã nguồn | Bộ v3 đã được chia ở ngưỡng 10, nhưng giá trị mặc định trong mã vẫn là 5. Ai chạy lại đường dây mà không truyền tham số sẽ tái tạo đúng lỗi cũ |

---

## 7. Bảng đối chiếu toàn bộ chỉ tiêu NFR

Ký hiệu: ✅ đạt mục tiêu · ⚠️ chỉ đạt ngưỡng tối thiểu · ❌ không đạt ·
⬜ chưa đo được.

### 7.1. NFR-P — Hiệu năng

| Mã | Chỉ tiêu | Mục tiêu | Ngưỡng tối thiểu | **Đo được** | Kết quả |
|---|---|---|---|---:|:---:|
| ~~NFR-P1~~ *(lịch sử — epoch 7, máy bận, có lỗi crop)* | Độ trễ E2E một ảnh (p95) | ≤ 800 ms | ≤ 1.500 ms | ~~5.857,19 ms~~ | *(bác bỏ)* |
| **NFR-P1** *(`best.pt`, client-side qua HTTP)* | Độ trễ E2E một ảnh (p95) | ≤ 800 ms | ≤ 1.500 ms | **731,15 ms** | **✅** |
| **NFR-P1** *(`best.pt`, in-process — T5.7a)* | Độ trễ E2E một ảnh (p95) | ≤ 800 ms | ≤ 1.500 ms | **780,36 ms** | **✅** |
| NFR-P2 | FPS chế độ webcam | ≥ 5 FPS | ≥ 3 FPS | **—** *(chưa đo trên `best.pt`)* | ⬜ |
| NFR-P3 | Tốc độ xử lý video | ≥ 0,3× | ≥ 0,15× | **—** *(chưa đo trên `best.pt`)* | ⬜ |
| NFR-P4 | Nạp mô hình (trong tiến trình) | ≤ 15 s | ≤ 30 s | **6,41 s** *(baseline)* | ✅ |
| NFR-P4b | Khởi động server đến `/health` sẵn sàng | ≤ 15 s | ≤ 30 s | **8,36 s** *(baseline)* | ✅ |
| NFR-P5 | Overhead API (p95) | ≤ 50 ms | ≤ 100 ms | **19,01 ms** *(baseline)* | ✅ |
| NFR-P6 | Truy vấn lịch sử 10.000 bản ghi (p95 xấu nhất) | ≤ 500 ms | ≤ 1.000 ms | **18,71 ms** | ✅ |
| NFR-P7a | RSS pipeline trong tiến trình (đỉnh) | ≤ 2 GB | ≤ 4 GB | **0,759 GB** | ✅ |
| NFR-P7b | RSS server uvicorn dưới tải | ≤ 2 GB | ≤ 4 GB | **0,806 GB** | ✅ |

> #### 🔴→✅ NFR-P1 ĐẠT trên mô hình chính thức `best.pt` — mâu thuẫn 5.857 ms đã giải quyết
>
> **Cấu hình đo:** `models/best.pt` (YOLO11n, `imgsz=640`, split v3), PyTorch,
> PaddleOCR **PP-OCRv5-mobile**, `enable_mkldnn=false`, CPU-only trên **Intel
> i5-14600K (14 nhân / 20 luồng), 32 GB RAM, Windows 11, torch 2.13.0+cpu**,
> **máy RẢNH** (không có tiến trình huấn luyện chạy song song).
> Đo được **p95 = 731,15 ms** (client-side qua HTTP, 100 mẫu) và **780,36 ms**
> (in-process, T5.7a), đều **dưới mục tiêu 800 ms**. Nguồn:
> [07-benchmark-p1-resolved.json](07-benchmark-p1-resolved.json), [05-tables.md §T5.7a](05-tables.md).
>
> **Vì sao con số cũ 5.857 ms sai (chênh 7,5 lần):** phép đo cũ bị nhiễm bởi tải
> cạnh tranh (~793% CPU), chạy trên sai checkpoint (`best-cpu-epoch7.pt`) và có
> lỗi crop đẩy OCR lên ~1.322 ms/ảnh; hai giả thuyết thay thế (oneDNN/cold-start,
> "baseline vốn chậm") đều đã bị bác bỏ bằng số đo. Truy nguyên đầy đủ năm điểm:
> [07-benchmark-report.md §0 và §9.2](07-benchmark-report.md).
>
> **Phân rã bước trên `best.pt` (T5.7b):** OCR ~112,55 ms/biển = **64,3%**, detect
> ~59,83 ms = **34,2%**, decode 2,65 ms, normalize 0,03 ms. OCR vẫn là bước tốn
> kém nhất nhưng **không còn áp đảo** như con số cũ — tối ưu bộ phát hiện (34,2%)
> giờ mới có ý nghĩa thực sự.
>
> **NFR-P2/P3 chưa đo trên `best.pt`:** chưa có kịch bản đo webcam/video. Ghi nhận
> là món nợ, không phải "không áp dụng".

### 7.2. NFR-A — Độ chính xác

| Mã | Chỉ tiêu | Mục tiêu | Ngưỡng tối thiểu | **Đo được** | Kết quả |
|---|---|---|---|---:|:---:|
| **NFR-A1** | mAP@0.5 | ≥ 0,90 | ≥ 0,85 | **0,9829** | ✅ |
| **NFR-A2** | mAP@0.5:0.95 | ≥ 0,65 | ≥ 0,55 | **0,7834** | ✅ |
| **NFR-A3a** | Precision (tại ngưỡng tối ưu F1) | ≥ 0,92 | ≥ 0,88 | **0,9837** | ✅ |
| **NFR-A3b** | Recall (tại ngưỡng tối ưu F1) | ≥ 0,90 | ≥ 0,85 | **0,9714** | ✅ |
| **NFR-A4** | Độ chính xác ký tự (1 − CER) | ≥ 0,95 | ≥ 0,92 | **0,8734** | **❌** |
| **NFR-A5** | Chuỗi đầy đủ **trước** hậu xử lý | ≥ 0,85 | ≥ 0,80 | **0,6098** | **❌** |
| **NFR-A6** | Chuỗi đầy đủ **sau** hậu xử lý | ≥ 0,90 | ≥ 0,85 | **0,6555** | **❌** |
| **A6 − A5** | *Đóng góp của khối hậu xử lý* | *(không có chỉ tiêu)* | — | **+4,57 điểm** (128 biển sửa đúng, 0 biển hỏng) | — |
| **NFR-A7** | Độ chính xác E2E toàn trình | ≥ 0,88 | ≥ 0,82 | **0,5227** — ⛔ **KHÔNG ĐẠI DIỆN** | **❌** |
| NFR-A8 | Tách 1 dòng / 2 dòng (detection) | *(phân tích)* | — | **0,9884 / 0,9675** (Δ 2,09 điểm) | ✅ |
| NFR-A9 | Tách theo điều kiện ảnh | *(phân tích)* | — | *(chưa đo — thiếu nhãn)* | ⬜ |

> **A1/A2/A3 giờ đo trên mô hình chính thức `models/best.pt`**, huấn luyện trên
> **split v3 đã khử trùng lặp ở ngưỡng 10**. Khác với bản đầu (đo trên checkpoint
> epoch 7 và bộ v1 có 619 cặp rò rỉ), số này **KHÔNG còn caveat "checkpoint giữa
> chừng" hay "rò rỉ thổi phồng"** — cả bốn chỉ tiêu **đạt** một cách hợp lệ. Nguồn:
> [05-tables.md §T5.5a](05-tables.md). A8 (chênh layout ở tầng detection) chỉ 2,09
> điểm — detection ít nhạy với layout; điểm yếu biển 2 dòng nằm ở tầng OCR (A4–A7).
>
> **NFR-A4/A5/A6 — đã đo, và trượt cả ba.** Nguồn: `04-ocr-accuracy.json`, 2.801
> biển số, `backend/.venv`, Intel i5-14600K 14 nhân / 20 luồng, CPU-only. Toàn bộ
> khoảng cách nằm ở **biển 2 dòng**: biển 1 dòng đạt A4 = 0,9900 / A5 = 0,9418 /
> A6 = 0,9489 (**vượt cả ba mục tiêu**), biển 2 dòng chỉ đạt 0,8462 / 0,5255 /
> 0,5810. Chênh lệch A6 giữa hai loại là **36,8 điểm**. Chi tiết:
> [04-ocr-report.md](04-ocr-report.md) mục 6.
>
> **NFR-A7 = 0,5227 KHÔNG được trích dẫn như năng lực hệ thống.** Trong đồ án
> **không có bộ dữ liệu nào vừa có ảnh toàn cảnh vừa có chuỗi biển số**, nên phép
> đo buộc phải chạy trên chính **ảnh crop**, tức bắt bộ phát hiện tìm một biển số
> chiếm gần hết khung hình — hoàn toàn **ngoài phân bố** huấn luyện. Hệ quả (T5.6e):
> **tỉ lệ biển bị bỏ sót ở tầng phát hiện 11,96%**, tỉ lệ phát hiện đúng nhưng đọc
> sai chuỗi 40,63%; A7 với điều kiện đã phát hiện được biển = 0,5937. Đây phần lớn
> là lỗi **bố cục đầu vào**, không phải lỗi OCR — trên ảnh hiện trường thật, bộ
> phát hiện `best.pt` đo được mAP@0.5 = **0,9829** (T5.5a, tập test v3). Việc cần làm: gán nhãn chuỗi cho
> 300–500 ảnh của tập test `yolo_v3`. **Chưa làm.**

> #### ✅ ĐÃ GIẢI QUYẾT — A1/A2/A3 đo trên `best.pt` train đúng split v3
>
> Bản trước ghi rằng A1/A2/A3 phải được đo lại "trên một split đã sửa, bằng mô
> hình train đúng trên split đó". **Việc này nay đã hoàn tất.** Lượt
> `runs/final-640-v3` đã chạy xong và cho `models/best.pt` (YOLO11n, `imgsz=640`,
> 20 epoch), huấn luyện **trên chính split v3**.
>
> **Số công bố (đo trên `best.pt`, tập test v3, 1.514 ảnh):** mAP@0.5 = **0,9829**,
> mAP@0.5:0.95 = **0,7834**, Precision = **0,9837**, Recall = **0,9714** — cả bốn
> **ĐẠT**. Vì mô hình và tập test cùng thuộc v3 (khử trùng lặp ở ngưỡng 10), **không
> còn** hiện tượng "mô hình đã nhìn thấy tập test" như khi lấy `baseline-416-v1.pt`
> (train trên v1) đo trên test v3 (289/1.514 = 19,1% trùng tên tệp — đó là lý do
> **không** được làm vậy).
>
> **Lưu ý phương pháp giữ nguyên:** phash không bắt được rò rỉ ở mức ngữ nghĩa
> (cùng biển chụp góc khác), nên không khẳng định tuyệt đối tập test v3 "sạch"
> hoàn toàn (T5.3b). Nhưng mAP 0,9829 **không còn bị thổi phồng bởi rò rỉ tên-tệp**
> như baseline. **Chốt M3 — detection: đạt.**

### 7.3. NFR-R — Độ tin cậy

| Mã | Chỉ tiêu | Mục tiêu | **Đo được** | Kết quả |
|---|---|---|---:|:---:|
| NFR-R1 | Không sập với đầu vào hỏng/độc hại | 100% | 52 test tại `test_api_detection.py` đều pass | ✅ |
| NFR-R2 | Ảnh không có biển ⇒ HTTP 200, danh sách rỗng | 200 + rỗng | pass (test tích hợp) | ✅ |
| NFR-R3 | Tác vụ video hỏng không để lại rác | nguyên tử | pass cho nhánh video | ⚠️ |
| **NFR-R4** | Tỉ lệ thành công khi chạy liên tục | ≥ 99% | **100%** (**3.928/3.928** request, soak **15 phút**) | ⚠️ |
| **NFR-R5** | CSDL sống qua khởi động lại | 100% | **0 bản ghi mất** (4.470 → 4.470), khởi động lại sau **TerminateProcess** | ✅ |

> **NFR-R3 gắn ⚠️:** nhánh **ảnh tĩnh** có lỗi nguyên tử đã biết — xem mục 8.1.
> Nhánh video không dính lỗi này.
>
> **NFR-R4 gắn ⚠️ — đã cải thiện nhưng vẫn chưa khép.** Bản trước đo 5 phút /
> 185 request; nay đã đo **15 phút / 3.928 request, 0 lỗi, RSS chỉ tăng 0,015 GB**
> (p50 = 227,28 ms, p95 = 263,27 ms, 4,364 req/s). Nhưng đặc tả yêu cầu **60
> phút**, nên 15 phút vẫn chỉ là **bằng chứng một phần**. Không được ghi ✅.
>
> **NFR-R5 — đã kiểm và đạt, với một chi tiết làm kết quả mạnh hơn.** Tiến trình
> bị kết liễu bằng **`TerminateProcess` trên Windows**, tức **không** có hook tắt
> êm và **không** đóng kết nối có trật tự — gần với một cú sập hơn là một lần
> dừng sạch. Cả hai ảnh chụp trước/sau đều đọc qua `GET /api/history` và
> `GET /api/statistics`, nên phép kiểm chứng minh các bản ghi vẫn **truy cập được
> bởi ứng dụng**, chứ không chỉ chứng minh một tệp còn tồn tại. Server sẵn sàng
> lại sau **8,81 s**.

### 7.4. NFR-M — Khả năng bảo trì

| Mã | Chỉ tiêu | Mục tiêu | **Đo được** | Kết quả |
|---|---|---|---:|:---:|
| **NFR-M1** | `ai/` không import FastAPI/Pydantic | 0 vi phạm | **0 vi phạm** (18 test tự động, có kiểm subprocess) | ✅ |
| **NFR-M2** | Bao phủ test tầng nghiệp vụ | ≥ 70% | **88,1%** (đo Phase 7, 19/07/2026) · **87,7%** (đo lại 20/07/2026, `13-refactor-result.json`) | ✅ |
| NFR-M3 | Mọi hàm public có type hint + docstring | 100% | *(chưa kiểm tự động)* | ⬜ |
| **NFR-M4** | Không hard-code đường dẫn | 0 vi phạm | **0 vi phạm** | ✅ |
| **NFR-M5** | Thay được bộ OCR không sửa tầng API | ràng buộc bằng ABC | pipeline dựng được từ fake, không cần runtime ML | ✅ |
| **NFR-M6** | Tuân thủ lint/format | ruff + black | **black: 96/96 tệp đạt (0 tệp cần định dạng lại); ruff: 0 lỗi logic (E/F/W/I), còn 83 cảnh báo E501** | ⚠️ |

> **NFR-M6 — đã đo thật (2026-07-20, đợt refactor).** Cấu hình nằm ở
> [`pyproject.toml`](../../pyproject.toml): `line-length = 100`, `target-version = "py313"`,
> ruff bật nhóm `E` (pycodestyle error), `F` (pyflakes), `W` (pycodestyle warning),
> `I` (sắp xếp import). Lệnh chạy:
>
> ```bash
> backend/.venv/Scripts/python.exe -m black --check .   # black 26.5.1
> backend/.venv/Scripts/python.exe -m ruff check .      # ruff 0.15.22
> ```
>
> Kết quả:
>
> | Công cụ | Trước đợt refactor | Sau đợt refactor |
> |---|---:|---:|
> | `black --check` | 1 tệp cần định dạng lại (`scripts/build_thesis.py`) | **0** — 96/96 tệp đạt |
> | `ruff check` | 113 lỗi | **83 lỗi** |
> | ├─ `F811` (định nghĩa trùng) | 30 | **0** |
> | └─ `E501` (dòng quá 100 ký tự) | 83 | 83 |
>
> **30 lỗi `F811` là dương tính giả**, không phải lỗi mã. Chúng phát sinh ở
> `tests/backend/test_job_repository.py`, nơi một fixture (`jobs`, `detections`,
> `session`…) được import từ `test_repositories.py` rồi lại xuất hiện làm **tên
> tham số** của hàm test — đúng cách pytest dùng lại fixture dùng chung. Đổi tên
> tham số sẽ làm hỏng cơ chế tiêm fixture. Đã xử lý bằng `per-file-ignores` cho
> `tests/**/*.py` trong `pyproject.toml`, kèm chú thích lý do — **không sửa mã test**.
>
> **83 lỗi `E501` còn lại là nợ kỹ thuật có chủ đích**, phân bố: `scripts/fill_chapter5.py`
> (71), `ai/evaluation/benchmark_ocr.py` (6), `scripts/labeling/label_tool.py` (4),
> `ai/evaluation/evaluate.py` (1), `ai/evaluation/ocr_accuracy.py` (1). Toàn bộ nằm
> trong **chuỗi ký tự tiếng Việt dài** của các script sinh tài liệu / in báo cáo —
> cắt dòng chỉ để lấy con số 0 sẽ làm chuỗi khó đọc hơn mà không cải thiện chất
> lượng mã. **Không có tệp nào thuộc `ai/inference/` hay `backend/` vi phạm** —
> nghĩa là toàn bộ mã chạy trong production đã sạch lint.

### 7.5. Chỉ tiêu chịu tải

| Mã | Chỉ tiêu | Mục tiêu | **Đo được** | Kết quả |
|---|---|---|---:|:---:|
| NFR-SC1 | Mức đồng thời cao nhất không lỗi | ≥ 5 | **10** (0 lỗi ở mọi mức 1/2/5/10) | ✅ |

### 7.6. Tổng kết

Cập nhật sau đợt đo bổ sung (bộ v3, mô hình `baseline-416-v1`, các backend đã tối ưu):

| | Số lượng | Chi tiết |
|---|---:|---|
| Chỉ tiêu **đã đo** | **20** | thêm **M6** ở đợt refactor 2026-07-20 |
| ✅ **Đạt mục tiêu** | **15** | P1, P4, P4b, P5, P6, P7a, P7b, A1, A2, A3a, A3b, R1, R2, R5, M1, M2, M4, M5, SC1 |
| ⚠️ **Chỉ đạt ngưỡng tối thiểu, hoặc bằng chứng chưa đủ** | **3** | **R3** (nhánh ảnh tĩnh), **R4** (soak 300 s < 60 phút), **M6** (black sạch tuyệt đối; ruff còn 83 `E501` trong chuỗi tiếng Việt của script sinh tài liệu — mã production sạch) |
| ❌ **Không đạt** | **4** | **A4** (0,8734), **A5** (0,6098), **A6** (0,6555), **A7** (0,5227 — và không đại diện) |
| ⬜ **Chưa đo được** | **4** | **P2/P3** (chưa có kịch bản webcam/video trên `best.pt`), **A9** (thiếu nhãn điều kiện ảnh), **M3** (chưa kiểm tự động) |

\* NFR-P1 đạt trên **mô hình chính thức `best.pt`, máy rảnh**: p95 = **731,15 ms**
client-side / **780,36 ms** in-process. Con số cũ 5.857,19 ms (epoch 7, máy bận,
có lỗi crop) **đã bị bác bỏ**. A1/A2/A3 đo trên `best.pt` / split v3 — **không còn
caveat "mô hình sai"**. Xem mục 7.1 và 7.2.

**Chốt M7 ("mọi chỉ tiêu NFR được đo và đạt ngưỡng") vẫn CHƯA thông qua.** Nhưng
lý do đã **đổi hẳn**, và đây là thay đổi quan trọng nhất của đợt đo này:

| | Chặn M7 trước đây | Chặn M7 bây giờ |
|---|---|---|
| Nguyên nhân | **NFR-P1** trượt cả ngưỡng tối thiểu (gấp 3,9× ngưỡng) | **NFR-A4/A5/A6** — độ chính xác OCR trên **biển 2 dòng** |
| Bản chất | Vấn đề **hiệu năng** | Vấn đề **chất lượng nhận dạng** |
| Đã giải quyết chưa | ✅ Đã giải quyết (mục 7.1) | ❌ Chưa — và **ba phương án giảm tải không liên quan gì đến nó** |

Nói cách khác: **nút thắt của đồ án đã dịch từ tốc độ sang độ chính xác OCR biển
2 dòng.** Toàn bộ 36,8 điểm chênh lệch giữa biển 1 dòng và 2 dòng là món nợ kỹ
thuật còn lại lớn nhất.

---

## 8. Các lỗi phát hiện trong quá trình kiểm thử

### 8.1. Lỗi trong mã ứng dụng — 1 lỗi, đã khoanh vùng bằng `xfail`

**Lỗi: tác vụ ảnh thất bại KHÔNG để lại bản ghi nào.**

- **Vị trí:** `backend/services/detection_service.py` — `_fail_job()` / `_create_job()`
- **Phát hiện bởi:** `tests/integration/test_api_detection.py::TestErrorBodies::test_a_failed_image_detection_records_the_failed_job`
- **Cơ chế:** `_fail_job()` gọi `db.rollback()` **trước khi** ghi bản ghi thất
  bại. Nhưng với nhánh **ảnh** và **webcam**, `_create_job()` mới chỉ `flush()`
  chứ chưa `commit()`. Lệnh rollback vì thế **xoá luôn chính dòng job đó**;
  `db.get()` trả về `None` và **không có gì được ghi lại cả**.
- **Hậu quả:** một lượt tải ảnh thất bại để lại **0 dòng** trong CSDL. Các lượt
  hỏng trở nên **vô hình** với dashboard: `total_jobs` âm thầm đếm thiếu, và hệ
  thống trông như chưa bao giờ hỏng. Đây là lỗi **làm sai lệch số liệu thống kê**,
  không chỉ là lỗi ghi log.
- **Nhánh video không dính lỗi này**, vì `create_video_job()` commit trước khi
  bắt đầu xử lý.
- **Cách xử lý đã chọn:** đánh dấu `xfail` **kèm mô tả đầy đủ cơ chế, hậu quả và
  cách sửa**, thay vì xoá test hoặc `skip`. Test vẫn chạy mỗi lần; ngày nào lỗi
  được sửa, nó sẽ chuyển thành `XPASS` và báo ngay.
- **Cách sửa đề xuất:** commit dòng job trong `_create_job()`, hoặc chèn lại dòng
  đó trong `_fail_job()` sau khi rollback.
- **Trạng thái: CHƯA SỬA.** Đây là lỗi ứng dụng duy nhất còn treo.

### 8.2. Lỗi trong bản thân phép đo — 1 lỗi phương pháp luận

**Lỗi: phép kiểm chứng rò rỉ dữ liệu ban đầu là lập luận vòng tròn.**

Bản đầu tiên chạy ở ngưỡng Hamming 5 và báo "0 cặp — SẠCH", và con số đó suýt
nữa đã được đưa vào báo cáo như bằng chứng bảo vệ cho mAP 0,98. Sự thật là bộ
chia tách dùng **đúng hàm băm đó, đúng ngưỡng đó**, nên kết quả 0 là tất yếu về
mặt toán học.

**Cách xử lý:** chạy lại ở ngưỡng 10 ⇒ phát hiện **619 cặp rò rỉ thật**; và ghi
thẳng cảnh báo về tính vòng tròn vào **chính tệp kết quả JSON**, để nó đi kèm số
liệu ở mọi nơi số liệu đó được trích dẫn. Chi tiết ở mục 6.

Đây là lỗi nghiêm trọng nhất phát hiện trong Phase 7 — nghiêm trọng hơn lỗi mã
nguồn ở 8.1, vì nó suýt tạo ra một **kết luận sai trong quyển đồ án**.

### 8.3. Lỗi phát hiện khi đóng gói Docker — 3 lỗi, đã sửa

Ghi đầy đủ ở [08-deployment-guide.md](08-deployment-guide.md) mục 7; tóm tắt:

| # | Lỗi | Cơ chế | Kết quả sau khi sửa |
|:-:|---|---|---|
| 1 | `.dockerignore` không chặn được venv | Mẫu `.venv/` neo vào thư mục gốc, không khớp `.venv-ai`, `.venv-ocr`, `backend/.venv`. `backend/.venv` (2,0 GB, wheel **Windows**) bị `COPY` thẳng vào image **Linux** | Build context 1,22 GB → **633 kB**; image 6,41 GB → **4,12 GB** |
| 2 | Sai tên biến môi trường ⇒ `./storage` không bao giờ được ghi | Compose đặt `ALPR_STORAGE_DIR` nhưng trường cấu hình tên là `storage_root` ⇒ biến đúng là `ALPR_STORAGE_ROOT`. `extra="ignore"` **nuốt lỗi gõ sai trong im lặng** | Đổi tên ở 4 nơi; kiểm chứng bằng tệp thật xuất hiện trong `./storage/` |
| 3 | `.env` máy chủ rò đường dẫn Windows vào container | Compose nội suy `${ALPR_MODEL_PATH:-...}` từ chính `.env` của máy chủ | Cố định đường dẫn tuyệt đối trong container; bỏ `env_file` khỏi service frontend (nó còn chép cả khoá API Roboflow/Kaggle vào một container không cần đến) |

**Bài học rút ra từ lỗi 2** — đáng ghi vào quyển đồ án: `extra="ignore"` biến
một lỗi gõ sai thành **lỗi câm**. Cấu hình phải được kiểm chứng bằng **hành vi
quan sát được**, không phải bằng cách đọc lại tệp cấu hình.

**Các lỗi được dự đoán nhưng KHÔNG xảy ra:** thiếu thư viện hệ thống
(`libgl1`, `libglib2.0-0`, `libgomp1`, `libmagic1`) — không lỗi nào xảy ra vì
`Dockerfile.backend` đã cài sẵn từ trước.

---

## 9. Hạn chế của bộ kiểm thử

Xếp theo mức độ nghiêm trọng.

| # | Hạn chế | Ảnh hưởng | Cách khắc phục |
|:-:|---|---|---|
| **1** | ✅ **Đã xử lý cho mô hình công bố.** Rò rỉ 619 cặp là của bộ **v1** (baseline). Mô hình `best.pt` train trên split **v3** khử trùng lặp ở ngưỡng 10 | mAP@0.5 = 0,9829 **không còn bị rò rỉ tên-tệp thổi phồng**. Lưu ý phash không bắt rò rỉ ngữ nghĩa (T5.3b) | Dựng tập test xuyên bộ dữ liệu vẫn là món nợ (mục 6.5) |
| **2** | ✅ **Đã xử lý.** Số công bố A1/A2/A3 đo trên `models/best.pt`, không còn dùng checkpoint epoch 7 | — | — |
| **3** | ✅ **Đã đo — và trượt A4/A5/A6 (kết quả thật).** 2.801 biển có nhãn chuỗi | A4 = 0,8734 / A5 = 0,6098 / A6 = 0,6555, đều **không đạt**; A6 − A5 = +4,57 điểm (128 biển sửa đúng, 0 hỏng). Toàn bộ khoảng cách nằm ở biển 2 dòng | Trình bày trung thực; cải thiện OCR biển 2 dòng là món nợ kỹ thuật |
| **4** | **NFR-P2 (webcam) và NFR-P3 (video) chưa đo trên `best.pt`** | Hai trong ba chế độ đầu vào chưa có số hiệu năng. Trùng khớp với việc `detection_service.py` chỉ bao phủ phần thiếu là hai nhánh đó | Viết bộ đo cho nhánh video/webcam |
| **5** | ✅ **Đã xử lý.** NFR-P1 đo lại trên máy rảnh với `best.pt`: p95 731 ms (client) / 780 ms (in-process), **đạt** | Con số cũ 5.857 ms bị nhiễm do tải cạnh tranh — đã bác bỏ | — |
| **6** | **NFR-R4 soak 300 s thay vì 1 giờ như đặc tả** | Rò rỉ bộ nhớ chậm có thể lọt lưới. Điểm tích cực: RSS **giảm** trong soak, không có dấu hiệu rò rỉ | Chạy soak 1 giờ |
| **7** | **Frontend không có kiểm thử tự động trong đợt này** | Vitest được khai trong stack nhưng không có kết quả nào trong Phase 7. Toàn bộ NFR-U1…U5 chưa kiểm | Viết bộ test component + kiểm tương phản WCAG |
| **8** | ✅ **Đã xử lý một phần.** Hạn chế "tập test chỉ **458 ảnh** (21 cặp trùng nội bộ)" là của lượt đo cũ trên checkpoint epoch 7 / bộ v1. Số công bố A1/A2/A3 nay đo trên **tập test v3, 1.514 ảnh** | Cỡ mẫu không còn là điểm yếu chính. Tồn dư: **vẫn chưa tính khoảng tin cậy** cho bất kỳ con số độ chính xác nào | Báo cáo kèm CI bootstrap trên tập test v3 (1.514 ảnh) |
| **9** | ✅ **NFR-M6 đã đo thật** (đợt refactor 2026-07-20): `black --check` sạch 96/96 tệp, `ruff check` còn 83 `E501` — tất cả nằm trong chuỗi tiếng Việt của script sinh tài liệu, **không tệp nào thuộc `ai/inference/` hay `backend/`**. Cấu hình chốt ở `pyproject.toml`. Còn lại: **NFR-M3** (type hint + docstring) chưa kiểm tự động | NFR-M6 không còn là "lời hứa"; NFR-R5 đã có phép đo restart ở mục 7.3 | Thêm `ruff`/`black` vào CI để chống thoái lui; dùng `mypy` cho NFR-M3 |
| **10** | Bộ kiểm rò rỉ đếm **cặp**, không đếm **ảnh test bị nhiễm** | Không định lượng được mức ảnh hưởng lên mAP | Sửa `leak_check.py` để xuất số ảnh riêng biệt |

---

## 10. Kết luận

**Điều bộ kiểm thử này chứng minh được:**

- Phần mềm **chạy đúng và ổn định**: **881/882 test pass, 1 `xfail`, 0 fail**;
  bao phủ tầng nghiệp vụ 88,1% ở lần đo Phase 7 ngày 19/07/2026 và 87,7% ở lần
  đo lại ngày 20/07/2026 ([13-refactor-result.json](13-refactor-result.json)) —
  cả hai đều vượt NFR-M2 (≥ 70%); 100% thành công qua 185 request liên tục,
  không rò rỉ bộ nhớ trong 5 phút.
- **Ràng buộc kiến trúc được thực thi bằng máy, không bằng lời hứa**: NFR-M1,
  M4, M5 đều có phép kiểm tự động có thể trượt, và đều đạt.
- **Toàn bộ chỉ tiêu tầng hạ tầng đều đạt thoải mái**: truy vấn CSDL nhanh hơn
  chỉ tiêu **27 lần**, overhead API nhanh hơn **2,6 lần**, bộ nhớ dùng chưa tới
  **40%** hạn mức.

**Điều bộ kiểm thử này KHÔNG chứng minh được — và phải nói thẳng:**

- **Khâu OCR không đạt chỉ tiêu — đây là kết quả THẬT, trình bày trung thực:**
  A4 = 0,8734 (< 0,92), A5 = 0,6098 (< 0,80), A6 = 0,6555 (< 0,85), A7 = 0,5227.
  Toàn bộ khoảng cách nằm ở **biển 2 dòng** (char_acc 0,846 so với 0,990 biển 1
  dòng; chênh A6 36,8 điểm). Biển 2 dòng chiếm 79,8% tập nhãn (xe máy) nên kéo tổng
  xuống. Chi tiết: [04-ocr-report.md](04-ocr-report.md).
- **NFR-P2/P3 (webcam/video), A9 (điều kiện ảnh), R5 (CSDL sau restart) chưa đo.**

**Điều đã được chứng minh:** NFR-P1 **đạt** trên `best.pt` (731/780 ms p95, đã giải
quyết mâu thuẫn 5.857 ms), detection **đạt cả bốn chỉ tiêu** trên split v3 sạch rò
rỉ tên-tệp (mAP@0.5 0,9829).

**Đóng góp có giá trị học thuật của Phase 7** không nằm ở con số mAP 0,98 — mà
nằm ở việc phát hiện được rằng **phép kiểm chứng rò rỉ dữ liệu ban đầu là lập
luận vòng tròn**, ở việc chạy lại ở ngưỡng cao hơn để tìm ra rò rỉ thật của bộ v1,
và ở việc **giải quyết mâu thuẫn phép đo NFR-P1** (5.857 ms là tạo tác của tải cạnh
tranh + lỗi crop + sai checkpoint, không phải hiệu năng thật). Trình bày trung thực
khâu OCR không đạt, kèm phân tích nguyên nhân (biển 2 dòng), có giá trị hơn một con
số làm đẹp.

---

## 11. Tệp dữ liệu gốc

| Tệp | Nội dung |
|---|---|
| `docs/reports/07-benchmark-data.json` | Tệp hợp nhất — mọi con số trong hai báo cáo Phase 7 |
| `docs/reports/07-benchmark-system.json` | Độ trễ E2E, phân rã ngân sách, so sánh PyTorch/ONNX |
| `docs/reports/03-evaluation-07-detection-test.json` | Độ chính xác phát hiện, tách theo số dòng |
| `docs/reports/07-leak-check.json` | Kiểm rò rỉ ở ngưỡng Hamming 5 |
| `docs/reports/07-leak-check-t10.json` | Kiểm rò rỉ ở ngưỡng 10 — **619 cặp**, 400 cặp ví dụ |
| `docs/reports/07-stress-load.json` | Chịu tải và soak |
| `docs/reports/07-stress-db.json` | Truy vấn CSDL 10.000 bản ghi |
| `docs/reports/07-api-overhead.json` | Overhead API, khởi động, RSS server |
| `docs/reports/07-api-overhead.server.log` | Log uvicorn của đợt đo overhead |
| `htmlcov/index.html` | Báo cáo bao phủ dạng HTML |
| `docs/reports/figures/` | 8 biểu đồ của Phase 7 + 6 biểu đồ gốc Ultralytics |
