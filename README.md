# Hệ thống nhận dạng biển số xe Việt Nam ứng dụng AI

> **Developing an AI-based Vietnamese License Plate Recognition System**
> Đồ án tốt nghiệp — hệ thống ALPR hoàn chỉnh từ mô hình AI đến giao diện người dùng và triển khai.

<p>
<img alt="Phase" src="https://img.shields.io/badge/Phase-9%20Documentation-blue">
<img alt="Status" src="https://img.shields.io/badge/M0%20%C2%B7%20M1-%C4%90%C3%A3%20ph%C3%AA%20duy%E1%BB%87t-brightgreen">
<img alt="Python" src="https://img.shields.io/badge/Python-3.13-blue">
<img alt="License" src="https://img.shields.io/badge/License-Academic-lightgrey">
</p>

---

## 1. Giới thiệu

Hệ thống tự động **phát hiện** và **đọc** biển số xe Việt Nam từ ảnh tĩnh và tệp video trên giao diện web, cùng năng lực nhận dạng **thời gian thực qua API** (`POST /api/detect/frame`). Kết quả được chuẩn hoá theo định dạng biển số Việt Nam, lưu vào cơ sở dữ liệu và tra cứu được trên trang **Lịch sử** (tìm kiếm, lọc, xem chi tiết, xuất CSV); số liệu tổng hợp phục vụ qua `GET /api/statistics`.

**Giao diện gồm 3 trang:** Nhận dạng ảnh *(trang chủ, `/`)* · Nhận dạng video *(`/video`)* · Lịch sử *(`/history`)*.

> ⚠️ **Thu gọn phạm vi — ba đợt.**
> **20/07/2026, hai lần liên tiếp:** gỡ trang **Webcam** (FR-3.1, FR-3.4: Must → Won't), rồi gỡ
> trang **Tổng quan / Dashboard** (**FR-4.1: Must → Won't**, FR-4.2: Should → Won't).
> **03/08/2026:** đưa **FR-2.5** (xuất video đã chú thích, Must → Won't) và **FR-2.6** (huỷ tác vụ
> đang chạy, Should → Won't) ra khỏi phạm vi — cả hai đang dở dang, và nút huỷ đã được **gỡ khỏi
> giao diện** thay vì để ở trạng thái vô hiệu hoá. Tổng cộng **hai** yêu cầu mức *Must* bị đưa ra
> khỏi phạm vi (FR-4.1 và FR-2.5); ghi rõ ở đây thay vì để người đọc tự phát hiện.
> **Không đổi:** `POST /api/detect/frame`, `GET /api/statistics` và `GET /health` vẫn phục vụ,
> vẫn có kiểm thử tích hợp; FR-4.3–FR-4.8 (trang Lịch sử) giữ nguyên; mã giao diện đã gỡ còn
> nguyên trong lịch sử git. **Đánh đổi đo được:** gỡ `recharts` ⇒ gói tải về của giao diện giảm
> từ ~730 KB xuống **328,8 KB (−55%)**. Bảng MoSCoW nay: **34 FR = 20 Must · 5 Should · 3 Could ·
> 6 Won't**. Chi tiết: [functional-requirements.md](docs/00-requirements/functional-requirements.md).

Điểm khác biệt so với việc ghép các thư viện có sẵn:

- **Mô hình phát hiện được huấn luyện riêng** trên dữ liệu biển số Việt Nam, không dùng model dựng sẵn của nước ngoài.
- **Hỗ trợ biển số 2 dòng** — chiếm phần lớn xe máy tại Việt Nam và là điểm gãy của hầu hết pipeline OCR thông dụng.
- **Hậu xử lý bằng luật riêng** cho định dạng biển số Việt Nam, và **đo được mức đóng góp định lượng** của bước này.
- **Chạy không cần GPU** khi vận hành.

---

## 2. Kiến trúc

```
Ảnh / Video / Khung hình thời gian thực (API)
        ↓
    YOLO11  ──────────► phát hiện vùng biển số
        ↓
    Cắt vùng biển số
        ↓
    PaddleOCR ────────► nhận dạng ký tự
        ↓
    Chuẩn hoá + regex ► sửa nhầm O↔0, I↔1, B↔8...
        ↓
    Kiểm tra định dạng biển số Việt Nam
        ↓
    SQLite ──► REST API ──► Giao diện web (3 trang)
```

Sơ đồ chi tiết, sơ đồ tuần tự và các quyết định kiến trúc: [docs/architecture/system-architecture.md](docs/architecture/system-architecture.md)

---

## 3. Công nghệ sử dụng

| Tầng | Công nghệ |
|---|---|
| **AI** | Python 3.13 · PyTorch · YOLO11 (Ultralytics) · PaddleOCR · OpenCV · NumPy |
| **Backend** | FastAPI · SQLAlchemy · Alembic · SQLite |
| **Frontend** | React · Vite · TypeScript · TailwindCSS |
| **Triển khai** | Docker · Docker Compose |
| **Kiểm thử** | pytest · Vitest |

---

## 4. Tình trạng hiện tại

| Phase | Nội dung | Trạng thái |
|:---:|---|:---:|
| **0** | Requirement Analysis | ✅ **Hoàn thành** (chốt M0) |
| **1** | Research | ✅ **Hoàn thành** (chốt M1) |
| **2** | Dataset | 🟢 **Tập v2 sẵn sàng** — 15.133 ảnh / 6 nguồn nguyên tố (hợp nhất từ 7 bộ) |
| **3** | Model Training | ✅ **Mô hình chính thức `best.pt` xong** (`imgsz=640`, split v3, 20 epoch): mAP@0.5 = **0,9829** / mAP@0.5:0.95 = **0,7834** / P **0,9837** / R **0,9714** — đạt |
| **4** | OCR | ✅ **Hoàn thành** — 145 test pass; đã đo A4–A7 (OCR biển 2 dòng KHÔNG đạt — kết quả thật) |
| **5** | Backend | ✅ **Hoàn thành** — đã nối `ALPRPipeline` thật, xác minh bằng HTTP sống |
| **6** | Frontend | ✅ **Hoàn thành** — build sạch, 10 endpoint khớp; **3 trang** sau thu gọn phạm vi 2026-07-20, gói tải về **328,8 KB** (−55%) |
| **7** | Testing | 🟠 **Đã đo xong** — **1.002 test thu thập / 1.002 pass / 0 fail** (13/08/2026), bao phủ tầng nghiệp vụ **87,7%**; 🟡 **NFR-P1 chỉ đạt sàn** (p95 **1.143 ms**, sàn 1.500, mục tiêu 800) và ✅ **NFR-P2 đạt** (5,257 FPS; sàn 3, mục tiêu 5 — đo lại 13/08) — riêng NFR-P1 là đánh đổi có chủ ý lấy 34 biển; chốt M7 vẫn bị chặn bởi **NFR-A5/A6** (độ chính xác OCR biển 2 dòng) |
| **8** | Deployment | ✅ **Build thật thành công** — 2 image, stack chạy `Healthy`, 4 lỗi đã sửa |
| **9** | Documentation | 🟡 Chương 1–4, sổ tay kỹ thuật, tài liệu API xong — **chờ chương 5–6** |
| **10** | Presentation | 🟡 58 câu Q&A, demo, 21 slide, poster — chờ số liệu cuối |
| 11 | Final Package | ⚪ Chưa bắt đầu |

**Đã chạy được thật:**

- **Dataset v3 — bộ đang dùng để huấn luyện** — `datasets/processed/yolo_v3/`: **15.133 ảnh** (train 10.592 / val 3.027 / test 1.514), gom nhóm ở **ngưỡng phash 10**. Hợp nhất từ **7 bộ dữ liệu**, còn **6 nguồn nguyên tố** sau khử trùng lặp chéo bộ — bộ thứ 7 (`roboflow_tran_ngoc_xuan_tin`, 1.005 ảnh) bị loại **100%** vì mọi ảnh đều có bản gần trùng ở bộ khác. Tổng cộng **9 bộ đã tải về** (8 Roboflow + 1 HuggingFace); 2 bộ nhãn mức ký tự tách riêng phục vụ đánh giá OCR. **8/9 bộ có giấy phép tường minh.**
  - Khử trùng lặp loại **11.978 / 27.111 ảnh (44,2%)** — mẫu số là toàn bộ ảnh của **7 bộ vào hợp nhất detection**, đo trước khi gộp. Đo lại trên corpus **đã gộp** (`merged_v2`, ngưỡng 10) cho con số khác: **7.227 / 15.133 (47,8%)**. Hai tỉ lệ này **khác mẫu số**, không mâu thuẫn nhau.
  - ⚠️ **Kiểm chứng rò rỉ ở ngưỡng bằng đúng ngưỡng đã gom là lập luận vòng tròn** — kết quả 0 cặp là tất yếu theo cấu tạo, không phải bằng chứng độc lập. Đo ở dải **ngoài** vùng bảo vệ (d = 12) còn **2.462 cặp** vắt qua split. Không thể khẳng định tập test đã sạch; xem [07-testing-report.md §6](docs/reports/07-testing-report.md).
  - `yolo_v2/` (gom ở ngưỡng 5) **vẫn còn rò rỉ**: **2.699 cặp train↔test** ở d ≤ 10 (tổng cả ba cặp split là **9.126** = 2.699 + 5.637 + 790) — giữ lại chỉ để đối chiếu.
  - **Chọn ngưỡng gom nhóm 10 — có căn cứ.** Quét toàn dải 5→20 và **kiểm bằng mắt** ở từng khoảng cách: trùng lặp thật sống ở **d = 6–10**, còn từ **d = 12** trở lên mẫu bị **dương tính giả cùng-camera** chi phối; ngưỡng 12 làm thành phần liên thông lớn nhất phình tới **54,6%** corpus và ngưỡng 14+ khiến phép chia 70/20/10 **bất khả thi**. **Chi phí:** **55,49%** ảnh bị ràng buộc vào nhóm, số đơn vị chia giảm từ 15.133 xuống **7.906**, một nhóm duy nhất chiếm **41,64%** tập train. Chi tiết: [02-dataset-report.md](docs/reports/02-dataset-report.md).
- **Nhãn ký tự** — **4.019 chuỗi biển số tái tạo được**, trong đó **2.801 chuỗi hợp lệ**. Đủ để đo NFR-A4/A5/A6. Kiểm chứng thực nghiệm: **0 lần xuất hiện** của `I J O Q W` trên toàn bộ corpus.
- **Backend** — xác minh bằng HTTP thật vào tiến trình uvicorn sống: **10 endpoint** phản hồi đúng (10 thao tác HTTP phân bố trên 9 đường dẫn — `/api/history/{detection_id}` mang cả `GET` lẫn `DELETE`; `/docs`, `/redoc`, `/openapi.json` do FastAPI **tự sinh** nên không tính vào 10), Swagger render được, Alembic migrate xong (`detection_history` 18 cột, `detection_job` 11 cột). Quy tắc đếm thống kê đã kiểm chứng: 1 ảnh chứa 3 biển = **1 lượt**, không phải 3.
- **Pipeline nhận dạng thật** — hệ thống chạy `ALPRPipeline` thật với `models/best.pt` (mô hình chính thức): `GET /health` trả `model_loaded: true`, `engine = 'yolo:best.pt+paddleocr-PP-OCRv5-mobile'`. `StubPipeline` **đã bị đưa ra khỏi đường chạy chính** — phương án lùi khi thiếu trọng số là `UnavailablePipeline`, nó **ném lỗi** thay vì bịa ra biển số; stub chỉ chạy khi đặt tường minh `ALPR_USE_STUB=true`.
- **Ràng buộc kiến trúc** — `ai/` không import FastAPI/Pydantic (kiểm cả bằng `sys.modules` lúc chạy); không hard-code đường dẫn; abstract base class thật.
- **Kiểm thử** — **1.002/1.002 test pass, 0 fail, 0 `xfail`** (chạy 13/08/2026 bằng `backend/.venv/Scripts/python.exe -m pytest -q` từ gốc kho); bao phủ tầng nghiệp vụ **87,7%** theo lần đo 20/07/2026 ([13-refactor-result.json](docs/reports/13-refactor-result.json)) và **88,1%** theo lần đo Phase 7 trước đó ([07-testing-report.md](docs/reports/07-testing-report.md)) — NFR-M2 ≥ 70% ⇒ đạt ở cả hai mốc; 18/18 test kiến trúc pass.
- **Benchmark (Phase 7)** — đo trên **Intel i5-14600K, 14 nhân vật lý / 20 luồng logic, 31,77 GiB RAM, Windows 11, Python 3.13.12, torch 2.13.0+cpu, CPU-only**. 🟡 **NFR-P1 = 1.143,10 ms p95** ở cấu hình giao hàng — đạt sàn 1.500 ms nhưng vượt mục tiêu 800 ms 1,43 lần; trung vị chỉ 405,77 ms. Cặp 731,15 / 780,36 ms là lần đo **20/07**, trước khi có bậc thang thử-lại. Phân rã bước: OCR **64,3%** (~112,55 ms/biển), detect **34,2%** (~59,83 ms). Truy vấn CSDL 10.000 bản ghi **18,71 ms** (chỉ tiêu 500 ms), overhead API **19,01 ms** (50 ms), RAM **0,88 GB** (2 GB), khởi động **8,36 s** (15 s) *(P4–P7 đo trên baseline)*, 0 lỗi ở mức đồng thời 10, soak 15 phút 100% trên 2.028 yêu cầu. **NFR-P2/P3/R4/R5 đã đo 02/08/2026** ([33-runtime-nfr.json](docs/reports/33-runtime-nfr.json)): ✅ **P2 = 5,257 FPS** (đo lại 13/08 trên máy rảnh; vượt cả mục tiêu 5. Con số 2,379 công bố 02/08 đo khi máy đang cõng ~560% CPU của tiến trình khác và harness đã tự dán nhãn *bi quan* — xem [38](docs/reports/38-runtime-backend-and-nfr-p2.md)); ✅ P3 = 0,785× · ✅ R4 = 100% trên 2.028 yêu cầu · ✅ R5 = 0/9.031 bản ghi mất. Con số cũ 5.857 ms (epoch 7, máy bận, lỗi crop) **đã bị bác bỏ** — xem [07-benchmark-p1-resolved.json](docs/reports/07-benchmark-p1-resolved.json). Chi tiết: [07-benchmark-report.md](docs/reports/07-benchmark-report.md).
- **Docker (Phase 8)** — build thật thành công: `alpr-backend` 4,12 GB + `alpr-frontend` 97,7 MB, stack chạy, kiểm chứng bằng `curl` từ ngoài container. 3 lỗi thật đã phát hiện và sửa. Chi tiết: [08-deployment-guide.md](docs/reports/08-deployment-guide.md).

**Sáu giới hạn cần biết:**

1. **✅ Mô hình chính thức `best.pt` đã có và đang chạy** (`models/best.pt`, YOLO11n, `imgsz=640`, split v3, 20 epoch): mAP@0.5 = **0,9829**, mAP@0.5:0.95 = **0,7834**, P = **0,9837**, R = **0,9714** — **đạt cả bốn**, đo trên split v3 khử trùng lặp (không còn rò rỉ tên-tệp thổi phồng). Backend nạp chính mô hình này — `GET /health` trả **`model_loaded: true`**, `engine = 'yolo:best.pt+paddleocr-PP-OCRv5-mobile'`. `baseline-416-v1.pt` (40 epoch, `imgsz=416`, split v1, mAP@0.5 = 0,9933) giờ là **mô hình đối chứng** — ⚠️ **không được báo cáo là "đạt"** vì hai khiếm khuyết: (a) `imgsz` = 416 ≠ 640; (b) split v1 **có rò rỉ train↔test** (xem giới hạn 5). Xem [models/README.md](models/README.md).
2. **Mọi số liệu trong quyển đồ án phải đo trên mô hình tự huấn luyện** — không lấy số của `models/pretrained/yolo11n-coco.pt` (trọng số COCO, **không phát hiện được biển số**). Xem [models/README.md](models/README.md).
3. **Tiêu chí Q6 của dataset KHÔNG đạt ở v2** — 10,91% box nhỏ hơn 0,5% diện tích ảnh (ngưỡng cho phép là 10%). Đây là hồi quy có thật so với v1 và được ghi nhận thay vì hạ ngưỡng; bắt buộc báo cáo mAP tách theo dải kích thước box.
4. **Chưa có tập test xuyên dataset.** Tập test hiện là mẫu ngẫu nhiên từ cả 6 bộ nguồn, nên mAP đo được vẫn lạc quan hơn hiệu năng thực tế. Đây là việc quan trọng nhất còn nợ ở khâu dữ liệu.
5. **⚠️ CÓ RÒ RỈ DỮ LIỆU THẬT ở bộ v1 và v2 — đã xử lý ở bộ v3 (xem mục 8).** Phép kiểm ở ngưỡng Hamming 5 báo "0 cặp — sạch", nhưng đó là **lập luận vòng tròn**: bộ chia tách dùng đúng hàm băm `phash` và đúng ngưỡng 5 đó, nên kết quả 0 là **được bảo đảm bởi cấu tạo**. Lập luận này vẫn đứng vững. Chạy lại ở **ngưỡng 10** — dải bộ chia tách không bảo vệ — phát hiện **619 cặp train↔test** ở v1 và ở v2 là **2.699 cặp train↔test** (9.126 cặp nếu tính cả ba ranh giới split). ⚠️ **Hai đính chính đối với bản trước:** (a) chi tiết *"khoảng cách nhỏ nhất luôn = 6 là dấu vết phân bố bị cắt cụt"* là **SAI** — `phash` cho khoảng cách **luôn chẵn** (cả 15.133 hash đều có 32 bit bật), nên 6 chỉ là giá trị chẵn kế tiếp sau 5; (b) cáo buộc *"cùng một tấm ảnh nằm ở hai bộ dữ liệu"* với cặp `hf_vn_plates_segment_000032` ↔ `roboflow_school_fuhih_001383` là **SAI** — kiểm bằng mắt cho thấy **Land Cruiser 52Y-6490** và **Hiace 51F-220.29**, hai xe khác nhau chung một camera cố định. Chi tiết: [07-testing-report.md](docs/reports/07-testing-report.md) mục 6.
6. **✅ NFR-P1 (độ trễ E2E) ĐẠT trên `best.pt` — mâu thuẫn 5.857 ms đã được giải quyết.** Bản trước ghi p95 = **5.857 ms** (trượt cả ngưỡng tối thiểu 1.500 ms) và quy kết cho *"PaddleOCR chiếm phần lớn thời gian"*. **Đo lại trên `models/best.pt`, máy rảnh: p95 = 731,15 ms** (client-side qua HTTP) và **780,36 ms** (in-process) — đều dưới mục tiêu 800 ms. Phép đo cũ **bị bác bỏ** vì ba lý do cộng dồn: (a) tiến trình huấn luyện chiếm **~793% CPU** song song làm nhiễm vùng mẫu p95; (b) đo trên checkpoint epoch 7, không phải `best.pt`; (c) **lỗi crop quá lớn khiến PaddleOCR đọc trên ảnh crop ~1322 ms/ảnh**, thổi phồng tỷ trọng OCR. Tỷ trọng thật trên `best.pt` (T5.7b) là **OCR 64,3% / phát hiện 34,2%** (~112,55 ms/biển vs ~59,83 ms), không phải con số cũ. Giả thuyết "oneDNN/cold-start" và "baseline vốn chậm" đều bị bác bỏ (`enable_mkldnn=false`, cold-start p95 chỉ 176 ms; baseline đo client-side ra 763,75 ms, gần y hệt best.pt). Chi tiết: [07-benchmark-p1-resolved.json](docs/reports/07-benchmark-p1-resolved.json).

7. **🔴 Nút thắt đã dịch sang độ chính xác OCR biển 2 dòng — đây là món nợ kỹ thuật lớn nhất còn lại.** Đo trên 2.801 biển: **NFR-A4 = 0,9454** (sàn 0,92 ✅, mục tiêu 0,95) · **NFR-A5 = 0,6373** (0,85) · **NFR-A6 = 0,7512** (0,90) — **A4 đạt sàn, A5 và A6 chưa**. Nhưng toàn bộ khoảng cách nằm ở **biển 2 dòng**: biển 1 dòng đạt **0,9925 / 0,9418 / 0,9541**, tức **vượt cả ba mục tiêu**; biển 2 dòng chỉ **0,9344 / 0,5600 / 0,6996** — chênh **25,45 điểm** ở mức chuỗi. Đóng góp của khối hậu xử lý là **+11,39 điểm** (319 biển sửa đúng, 0 biển hỏng ở mức chuỗi) — nhưng ở **mức ký tự** thì bảng ánh xạ **có chỗ sai**: hai quy tắc `L → 1` và `7 → T` kích hoạt đúng chỗ nhưng **ánh xạ tới ký tự sai** (phải là `L → 4` và `7 → Z`), khiến lỗi bị **dời chỗ** chứ không bị xoá. Chi tiết: [04-ocr-report.md](docs/reports/04-ocr-report.md) mục 6.1b.

8. **🟡 Rò rỉ dữ liệu đã GIẢM MẠNH ở bộ `yolo_v3`, nhưng KHÔNG khẳng định là sạch tuyệt đối.** Bộ v2 có **9.126** cặp ảnh vắt qua ranh giới split ở ngưỡng Hamming 10 (2.699 riêng train↔test). Bộ **v3** gom nhóm ở **ngưỡng 10**, nên đo lại **cũng ở ngưỡng 10** ra **0 cặp** — nhưng con số 0 đó là **lập luận vòng tròn**, được bảo đảm bởi cấu tạo, **không phải bằng chứng sạch** (xem giới hạn 5). Kiểm chứng trung thực phải đo ở dải **ngoài** vùng bảo vệ: ở **d = 12**, v3 vẫn còn **791 cặp train↔test** (2.462 cặp tính cả ba split). Ngưỡng 10 được chọn có căn cứ (quét dải 5→20, kiểm bằng mắt: trùng thật ở d = 6–10, từ d = 12 là dương tính giả cùng-camera; ngưỡng 12+ làm cụm lớn nhất phình 54,6% và phá vỡ tỉ lệ chia). ⚠️ **Rủi ro tồn dư mà `phash` không khử được:** biển `51F-155.85` — **cùng một chiếc xe ghé cùng barrier vào hai ngày khác nhau** — rơi vào hai split của chính v3. Chỉ **test xuyên bộ dữ liệu** mới khép được, và đó là món nợ ở giới hạn 4. Chi tiết: [02-dataset-report.md](docs/reports/02-dataset-report.md), [07-testing-report.md §6](docs/reports/07-testing-report.md).

9. **Cảnh báo đánh giá (đã tuân thủ): không dùng `baseline-416-v1.pt` để đo trên tập test v3.** Mô hình baseline huấn luyện trên split **v1**, và **289 / 1.514 ảnh test của v3 (19,1%)** nằm trong tập train+val của v1 — trùng khớp **tên tệp chính xác**. Vì vậy NFR-A1/A2/A3 công bố **chỉ** lấy từ `models/best.pt` (train đúng trên split v3, `runs/final-640-v3`): mAP@0.5 = **0,9829**.

**Chưa đo được (đã thu hẹp):** NFR-A9 (thiếu nhãn điều kiện ảnh), NFR-M3 (chưa kiểm tự động), NFR-M6 (chưa chạy lint trong đợt này), và kiểm thử frontend.

**Đã đo bổ sung trong đợt này:** NFR-A4/A5/A6/A7 (mục 7 ở trên), **NFR-P2 = 5,257 FPS** (✅ vượt cả mục tiêu 5; xấu nhất đo được dưới tải nặng **4,057**, vẫn trên OpenVINO@640), **NFR-P3 = 0,754×** ✅ (mục tiêu 0,3×), **NFR-R5 = 0 bản ghi mất** ✅ (4.470 → 4.470, tắt bằng `TerminateProcess` chứ không tắt êm). **NFR-R4** đã nâng từ 5 lên **15 phút / 3.928 request / 0 lỗi**, nhưng đặc tả yêu cầu **60 phút** nên vẫn chỉ là bằng chứng một phần.

---

## 5. Tài liệu

### Phase 0 — Phân tích yêu cầu

| Tài liệu | Nội dung |
|---|---|
| [SRS.md](docs/00-requirements/SRS.md) | Đặc tả yêu cầu phần mềm — tài liệu gốc |
| [functional-requirements.md](docs/00-requirements/functional-requirements.md) | 34 yêu cầu chức năng có tiêu chí chấp nhận |
| [non-functional-requirements.md](docs/00-requirements/non-functional-requirements.md) | Chỉ tiêu hiệu năng, độ chính xác, bảo mật |
| [project-scope.md](docs/00-requirements/project-scope.md) | Phạm vi in/out, sản phẩm bàn giao, rủi ro |
| [timeline.md](docs/00-requirements/timeline.md) | Kế hoạch 77 ngày-người, đường găng, điểm chốt |
| [environment.md](docs/00-requirements/environment.md) | Khảo sát môi trường thực tế và tác động |
| [system-architecture.md](docs/architecture/system-architecture.md) | Kiến trúc, sơ đồ ER, quyết định thiết kế |

### Phase 1 — Nghiên cứu

> **Bắt đầu từ [01-README.md](docs/reports/01-README.md)** — chỉ mục Phase 1: ánh xạ task, danh mục 76 bảng so sánh, khuyến nghị và việc còn treo.

| Tài liệu | Nội dung |
|---|---|
| [01-README.md](docs/reports/01-README.md) | **Chỉ mục Phase 1** — cửa vào của toàn bộ 7 tài liệu nghiên cứu |
| [01-research-report.md](docs/reports/01-research-report.md) | Tổng quan nghiên cứu ALPR — dùng làm Chương 2 của quyển đồ án |
| [01-vn-plate-standards.md](docs/reports/01-vn-plate-standards.md) | Quy chuẩn biển số Việt Nam — **nguồn chuẩn về căn cứ pháp lý** của dự án |
| [01-yolo-comparison.md](docs/reports/01-yolo-comparison.md) | So sánh YOLOv8 → YOLO26, chốt **YOLO11n** cho Phase 3 |
| [01-ocr-comparison.md](docs/reports/01-ocr-comparison.md) | So sánh 9 engine OCR, chuyên sâu biển 2 dòng |
| [01-technology-comparison.md](docs/reports/01-technology-comparison.md) | Luận cứ lựa chọn toàn bộ stack phần mềm |
| [01-dataset-survey.md](docs/reports/01-dataset-survey.md) | Khảo sát bộ dữ liệu — đầu vào trực tiếp của Phase 2 |
| [01-citation-map.md](docs/reports/01-citation-map.md) · [references.bib](docs/references.bib) | 232 entry BibTeX và bản đồ ánh xạ trích dẫn |

> ⚠️ **Căn cứ pháp lý.** Thông tư **24/2023/TT-BCA đã hết hiệu lực từ 01/01/2025**. Văn bản hiện hành: **TT 79/2024/TT-BCA** (sửa đổi bởi TT 13/2025 và TT 51/2025); kích thước biển số theo **QCVN 08:2024/BCA**.

> ⚠️ **Đính chính Phase 1.** Bộ dữ liệu **VNLP** được [01-dataset-survey.md](docs/reports/01-dataset-survey.md) khuyến nghị làm bộ chính **không truy cập được** (HuggingFace trả HTTP 401). Phương án thực tế đã dùng là **8 bộ Roboflow + 1 bộ HuggingFace**. Đính chính đầy đủ ở mục 5 của tài liệu đó.

### Phase 2 — Dữ liệu

| Tài liệu | Nội dung |
|---|---|
| [02-dataset-report.md](docs/reports/02-dataset-report.md) | **Báo cáo dataset v2** — 9 bộ tải về / 7 bộ hợp nhất / 6 nguồn nguyên tố, ma trận trùng lặp chéo bộ, kiểm chứng rò rỉ, thống kê + 8 biểu đồ, nhãn ký tự |
| `scripts/dataset/README.md` | Hướng dẫn vận hành pipeline dữ liệu |
| `datasets/statistics/v2/` | `statistics.json` + 8 biểu đồ PNG |

### Phase 3–6 — Mô hình, OCR, Backend, Giao diện

| Tài liệu | Nội dung |
|---|---|
| [03-training-setup.md](docs/reports/03-training-setup.md) | Cấu hình huấn luyện, siêu tham số, kế hoạch xử lý chênh lệch `imgsz` |
| [04-ocr-report.md](docs/reports/04-ocr-report.md) | Thiết kế khối OCR và cách đo NFR-A4/A5/A6 — đã có số đầy đủ; riêng NFR-A7 xem mục 6.6 của báo cáo |
| [06-ui-documentation.md](docs/reports/06-ui-documentation.md) | Tài liệu giao diện người dùng |

### Phase 7 — Kiểm thử và Benchmark

| Tài liệu | Nội dung |
|---|---|
| [07-testing-report.md](docs/reports/07-testing-report.md) | **Báo cáo kiểm thử** — ⚠️ có biển cảnh báo ở đầu: ba con số trong báo cáo đã lỗi thời (số test, NFR-P1, bốn NFR runtime). Nội dung: 882 test ở thời điểm đo (881 pass, 1 `xfail`, 0 fail), bao phủ tầng nghiệp vụ 88,1% (đo Phase 7) / 87,7% (đo lại 20/07/2026), kiểm kiến trúc tự động, độ chính xác tách 1 dòng/2 dòng, **kiểm chứng rò rỉ dữ liệu**, bảng đối chiếu toàn bộ NFR, lỗi đã phát hiện, hạn chế |
| [07-benchmark-report.md](docs/reports/07-benchmark-report.md) | **Báo cáo benchmark** — độ trễ E2E, **phân rã ngân sách đo thật so với ước lượng**, PyTorch với ONNX, chịu tải, truy vấn CSDL |
| `docs/reports/07-*.json` | Toàn bộ dữ liệu đo gốc (benchmark, chịu tải, CSDL, overhead API, rò rỉ) |
| `docs/reports/figures/` | 8 biểu đồ Phase 7 + 6 biểu đồ gốc Ultralytics |

### Phase 8 — Triển khai

| Tài liệu | Nội dung |
|---|---|
| [08-deployment-guide.md](docs/reports/08-deployment-guide.md) | Build Docker thật, thời gian build, mã trạng thái đo được, 3 lỗi đã sửa |

---

## 6. Môi trường phát triển

> ⚠️ **Lưu ý quan trọng:** máy phát triển là **Windows 11, không có GPU CUDA**. Điều này khác với mô tả trong `CLAUDE.md` và ảnh hưởng trực tiếp đến chiến lược huấn luyện. Chi tiết: [environment.md](docs/00-requirements/environment.md).

| Thành phần | Yêu cầu | Ghi chú |
|---|---|---|
| Python | 3.13 (hoặc 3.12) | PaddlePaddle 3.3.1 có wheel cho 3.13 |
| Node.js | ≥ 18 | Đã chuyển sang **v20.19.6** qua nvm (trước đó là v14, quá cũ cho Vite 5) |
| Docker | Bất kỳ bản mới | Dùng cho Phase 8 |
| GPU | **Không bắt buộc** | Huấn luyện chạy trên Colab/Kaggle |

**Phân chia môi trường:**

- 🖥️ **Local (CPU)** — phát triển, suy luận, demo
- ☁️ **Colab / Kaggle (GPU)** — chỉ dùng để huấn luyện, xuất ra `models/best.pt`

---

## 7. Cấu trúc thư mục

```
DATN/
├── ai/                 # Mã AI — độc lập hoàn toàn với FastAPI
│   ├── inference/          # Detector, recognizer, normalizer, pipeline
│   ├── training/           # Script huấn luyện (chạy được cả trên Colab)
│   └── evaluation/         # Đánh giá và sinh biểu đồ
├── backend/            # FastAPI + SQLAlchemy
├── frontend/           # React + Vite + TypeScript
├── datasets/           # raw / processed / annotations / statistics
├── models/             # best.pt và các model đã xuất
├── deployment/docker/  # Dockerfile, docker-compose
├── tests/              # Unit + integration test
├── scripts/            # Tiện ích dòng lệnh
├── demo/               # Tài nguyên demo
└── docs/               # Toàn bộ tài liệu
    ├── 00-requirements/    architecture/
    ├── papers/  reports/  slides/  poster/
```

---

## 8. Hướng dẫn cài đặt

> 📖 **Hướng dẫn đầy đủ từng bước:** [docs/manuals/installation-guide.md](docs/manuals/installation-guide.md)
> — yêu cầu hệ thống, hai đường cài, cách kiểm chứng sau khi cài, bảng sự cố thường gặp. Phần dưới đây
> chỉ là bản rút gọn cho người đã quen dự án.

### Chạy trực tiếp (đang dùng để phát triển)

```bash
# Backend — từ thư mục gốc d:/DATN
backend/.venv/Scripts/python.exe -m uvicorn backend.main:app --port 8000
# Swagger: http://localhost:8000/docs

# Frontend — cần Node >= 18
cd frontend && npm install && npm run dev
# Giao diện: http://localhost:5173
```

### Chạy bằng Docker

> Đã **build thật thành công** ở Phase 8: `alpr-backend` 4,12 GB + `alpr-frontend` 97,7 MB, stack chạy, kiểm chứng bằng `curl` từ ngoài container. Chi tiết: [08-deployment-guide.md](docs/reports/08-deployment-guide.md).
>
> ```bash
> docker compose up
> ```

---

## 9. Quy ước dự án

- **Tài liệu học thuật viết bằng tiếng Việt** — quyển đồ án, slide, poster, sổ tay người dùng.
- **Mã nguồn viết bằng tiếng Anh** — định danh, chú thích, docstring, tài liệu Swagger.
- **Mã AI không được import FastAPI** — ràng buộc kiến trúc, kiểm tra tự động ở Phase 7.
- **Không hard-code đường dẫn** — mọi đường dẫn đi qua đối tượng cấu hình.
- **Tài liệu tiến hoá cùng mã nguồn** — mỗi lần cài đặt phải cập nhật tài liệu tương ứng.

---

## 10. Giấy phép

Sử dụng cho mục đích học thuật. Các bộ dữ liệu và mô hình bên thứ ba tuân theo giấy phép gốc của chúng.

**Giấy phép các bộ dữ liệu đang dùng** (danh sách đầy đủ ở [02-dataset-report.md](docs/reports/02-dataset-report.md) mục 2.1):

| Giấy phép | Số bộ | Nghĩa vụ |
|---|---|---|
| **CC BY 4.0** | 6 | **Bắt buộc ghi công tác giả** — đã liệt kê trong báo cáo dataset |
| **Public Domain (CC0)** | 2 | Không ràng buộc |
| Chưa xác nhận | 1 (`hoanglvuit/Vietnam_License_Plate_Segment_Datasets`) | ⚠️ Cần liên hệ tác giả trước khi công bố |
