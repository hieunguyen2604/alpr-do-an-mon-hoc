# Rà soát Definition of Done — 23 hạng mục

> **Ngày rà soát:** 20/07/2026
> **Căn cứ:** mục "Definition of Done" trong [CLAUDE.md](../../CLAUDE.md) (dòng 650–678) — đúng 23 hạng mục.
> **Phương pháp:** mọi kết luận dưới đây dựa trên **kiểm tra file thật trên đĩa** (`ls`/`find`/`grep`/`wc`),
> không dựa trên nội dung tự khai của tài liệu khác, không suy đoán.
> **Nguyên tắc:** không tô hồng. Một hạng mục chỉ `done` khi **tồn tại**, **đầy đủ**, và **khớp thực tế đo được**.

---

## 0. Ba điều phải đọc trước

**Một.** Nút thắt "`models/best.pt` chưa huấn luyện xong" của các bản trước **đã được gỡ**: mô hình chính thức
`models/best.pt` (5,4 MB, YOLO11n, `imgsz=640`, split v3, 20 epoch) đã có trên đĩa. Detection đạt cả bốn chỉ tiêu
(mAP@0.5 = 0,9829; mAP@0.5:0.95 = 0,7834; P = 0,9837; R = 0,9714).

**Hai.** Nút thắt còn lại **không phải** ở phần detection mà ở **độ chính xác OCR biển 2 dòng**: A4 = 0,8734;
A5 = 0,6098; A6 = 0,6555; A7 = 0,5227 — **KHÔNG đạt** (kết quả thật, không phải rủi ro giả định).
Kéo theo: "Evaluation reports" và "Performance report" chỉ đạt mức `partial`.

**Ba.** Có một nhóm hạng mục tài liệu tồn tại dưới dạng **bản nháp markdown / outline** chưa kết xuất thành
sản phẩm cuối (thesis chưa ghép PDF, slide còn là outline, poster còn là layout, front-matter còn placeholder).
Những hạng mục này được ghi `partial` một cách trung thực.

---

## 1. Bảng 23 hạng mục

| # | Hạng mục | Trạng thái | Bằng chứng (đường dẫn thật) | Còn thiếu |
|---|---|---|---|---|
| 1 | Complete source code | **done** | `ai/` `backend/` `frontend/` `scripts/` `tests/`; 98 file `.py` (ngoài venv/pycache), 69 file `.ts/.tsx` trong `frontend/src/` | — |
| 2 | AI model | **done** (sắc thái) | `models/best.pt`, `models/best.onnx`, `models/best-640-v3-ep20.pt`, `models/best-640-v3.results.csv`, `models/README.md` | **Detection** đạt đủ 4 chỉ tiêu. **OCR** biển 2 dòng CHƯA đạt (xem hạng mục 5, 12 và mục 5). |
| 3 | Dataset | **done** (có cảnh báo) | `datasets/processed/` (`merged`, `merged_v2`, `yolo`, `yolo_v2`, `yolo_v3`), `datasets/raw/`, `datasets/annotations/`, `datasets/statistics/`, `datasets/reports/`, `docs/reports/02-dataset-report.md` | Còn **rò rỉ tồn dư** ở split v3 (791 cặp train–test khoảng cách d = 12) — chưa khẳng định sạch. Ảnh hưởng tính hợp lệ của một phần số liệu eval. |
| 4 | Training scripts | **done** | `ai/training/train.py` (834 dòng), `ai/training/export.py` (409), `ai/training/config.py` (586), `ai/training/configs/`, `ai/training/README.md` | — |
| 5 | Evaluation reports | **partial** | `docs/reports/03-evaluation-ch5-best-test.json`, `03-evaluation-07-detection-test.json`, `03-training-setup.md` (993 dòng), `04-ocr-report.md` (931 dòng), `04-ocr-accuracy.json`, `05-results.json` | Báo cáo detection đầy đủ và đạt; **báo cáo OCR cho kết quả KHÔNG đạt** (A4–A7). Một phần số liệu dựa trên split còn rò rỉ tồn dư. |
| 6 | Backend | **done** | `backend/` (`api/`, `core/`, `services/`, `repositories/`, `schemas/`, `models/`, `main.py`, `migrations/`); 10 endpoint thật, `/health` trả `model_loaded=true` | — |
| 7 | Frontend | **done** (sắc thái) | `frontend/src/`, `frontend/dist/` (đã build), `package.json`, `vite.config.ts`, `tailwind.config.js`, `tsconfig.json`; **3 trang**: Nhận dạng ảnh *(trang chủ)* · Nhận dạng video · Lịch sử | Thu gọn phạm vi 2026-07-20: gỡ trang Webcam rồi gỡ trang Tổng quan ⇒ **FR-4.1 (Must) → Won't**, FR-4.2 (Should) → Won't. `GET /api/statistics` và `GET /health` vẫn phục vụ, vẫn có test tích hợp. Xem mục 5. |
| 8 | Database | **done** | `backend/models/database.py`, `backend/models/detection.py`, `backend/migrations/versions/0001_initial.py`, `data/alpr.db` (tồn tại thật) | — |
| 9 | Docker deployment | **done** | `deployment/docker/Dockerfile.backend`, `Dockerfile.frontend`, `nginx.conf`, `docker-compose.yml` (gốc), `deployment/README.md` (30 KB); build thật thành công (backend 4,12 GB + frontend 97,7 MB) | — |
| 10 | Unit tests | **done** | `tests/test_*.py` (detector, normalizer, pipeline, plate_rules, recognizer, two_line, config, architecture, ocr_accuracy), `tests/backend/test_*.py` — **688 test unit + 18 test kiến trúc** trong tổng **882 test thu thập** | — |
| 11 | Integration tests | **done** | `tests/integration/` có thật: `test_api_detection.py`, `test_api_health.py`, `test_api_history.py`, `test_api_statistics.py`, `conftest.py` — **176 test tích hợp**. Toàn bộ bộ test: **882 thu thập / 881 đạt / 1 `xfail` / 0 fail** ([13-refactor-result.json](13-refactor-result.json), 20/07/2026) | — |
| 12 | Performance report | **partial** | `docs/reports/07-benchmark-report.md` (895 dòng), `07-testing-report.md` (1.046 dòng), `07-benchmark-*.json`, `07-stress-*.json`, `07-leak-check*.json`, `05-stress-test.json` | NFR-P1 = 731 ms đã đạt. Nhưng **P2/P3/A9/R5 chưa đo**; một số P4–P7 có vấn đề trên baseline (mới ghi nhận). |
| 13 | API documentation | **done** | `docs/manuals/api-documentation.md` (1682 dòng) + Swagger `/docs` `/redoc` `/openapi.json` tự sinh | — |
| 14 | User manual | **done** | `docs/manuals/user-manual.md`, có `docs/screenshots/` (**3 ảnh**: `image-detection`, `video-detection`, `history` — `webcam.png` xoá cùng trang Webcam và `dashboard.png` xoá cùng trang Tổng quan, cả hai ngày 2026-07-20) | Ảnh chụp còn hiển thị sidebar 5 mục cũ; **phải chụp lại** trên giao diện **3 trang** hiện hành (Nhận dạng ảnh *(trang chủ)* · Nhận dạng video · Lịch sử) trước khi nộp. |
| 15 | Technical manual | **done** | `docs/manuals/technical-manual.md` (1389 dòng) | — |
| 16 | Deployment guide | **done** | `docs/reports/08-deployment-guide.md` (449 dòng) + `deployment/README.md` (10 mục: kiến trúc, build, env, backup, troubleshooting) | — |
| 17 | Installation guide | **partial** | Nội dung cài đặt có thật nhưng **nằm rải trong** `README.md` mục 8 "Hướng dẫn cài đặt", `docs/manuals/user-manual.md` (dòng 140–168), `deployment/README.md` mục 3 | **KHÔNG có tài liệu cài đặt độc lập** tách riêng khỏi deployment guide; DoD liệt kê đây là 2 hạng mục riêng. |
| 18 | Thesis | **partial** | `docs/papers/`: ch1 (433), ch2 (1146), ch3 (1322), ch4 (1327), ch5 (1135), ch6 (264) — **6/6 chương có nội dung thật**; `01-front-matter.md` (388), `00-thesis-outline.md` | Front-matter: bìa/lời cam đoan/lời cảm ơn còn **placeholder «…»** chờ điền; **mục lục / danh mục hình / danh mục bảng còn placeholder, sinh tự động khi ghép**. Chưa kết xuất PDF/Word bản nộp. |
| 19 | Presentation slides | **partial** | `docs/slides/10-slides-outline.md` (920 dòng, kèm speaker notes), `docs/slides/README.md` | Còn là **outline markdown**, **chưa kết xuất thành bộ slide** `.pptx`/PDF để bảo vệ. |
| 20 | Poster | **partial** | `docs/poster/10-poster-layout.md` (489 dòng) | Còn là **đặc tả layout markdown**, **chưa kết xuất thành poster** ảnh/PDF in được. |
| 21 | Demo script | **done** | `docs/slides/10-demo-script.md` (447 dòng; ngân sách 320 s bắt buộc / 360 s kể cả bước tuỳ chọn) + tài nguyên thật: `demo/demo-video.mp4` (2,9 MB), `demo/images/` (10 ảnh: 1dong×3, 2dong×3, nhieu-bien×3, khong-co-bien-so) | — |
| 22 | Defense Q&A | **done** | `docs/slides/10-defense-qa.md` (1.079 dòng, 58 câu — bổ sung **E4c** về việc FR-4.1 mức *Must* bị đưa ra khỏi phạm vi) | — |
| 23 | README | **done** | `README.md` (26 KB, ~26 396 byte) | — |

---

## 2. Tóm tắt

| Trạng thái | Số lượng | Hạng mục |
|---|---:|---|
| **done** | **17** | Source code, AI model (sắc thái), Dataset (cảnh báo), Training scripts, Backend, Frontend, Database, Docker, Unit tests, Integration tests, API doc, User manual, Technical manual, Deployment guide, Demo script, Defense Q&A, README |
| **partial** | **6** | Evaluation reports, Performance report, Installation guide, Thesis, Presentation slides, Poster |
| **missing** | **0** | — |

Không có hạng mục nào **missing** (mọi hạng mục đều có tệp tồn tại trên đĩa). Nhưng theo câu cuối của DoD
("If any item is missing, the project is NOT complete"), 6 hạng mục `partial` khiến dự án **CHƯA hoàn tất**.

---

## 3. Việc chặn nộp đồ án (ưu tiên)

Đây là các việc mà nếu không làm thì **không thể nộp / không thể bảo vệ**:

1. **Kết xuất Thesis thành bản nộp** — điền toàn bộ placeholder `«…»` ở front-matter (tên trường, khoa, sinh viên,
   MSSV, GVHD), sinh mục lục + danh mục hình + danh mục bảng, ghép 6 chương thành một quyển PDF/Word. *(hạng mục 18)*
2. **Kết xuất bộ slide bảo vệ** từ `10-slides-outline.md` thành `.pptx`/PDF thật. *(hạng mục 19)*
3. **Kết xuất poster** từ `10-poster-layout.md` thành ảnh/PDF in được. *(hạng mục 20)*
4. **Tài liệu cài đặt độc lập** — hoặc tạo một `installation-guide` riêng, hoặc ghi rõ trong DoD/README rằng
   installation được gộp trong deployment guide (nếu hội đồng chấp nhận gộp). *(hạng mục 17)*

> Ba việc 1–3 chủ yếu là **kết xuất định dạng**, nội dung đã có sẵn — không phải viết lại từ đầu.

---

## 4. Việc nên làm nhưng không chặn

Không chặn nộp, nhưng làm thì đồ án chắc chắn hơn và trả lời phản biện tốt hơn:

1. **Đo nốt các NFR còn trống** — P2, P3, A9, R5 chưa đo; hoàn tất để bảng Performance report đủ. *(hạng mục 12)*
2. **Rà lại các mục P4–P7 đang có vấn đề trên baseline** — hiện mới ghi nhận, chưa xử lý. *(hạng mục 12)*
3. **Xử lý rò rỉ tồn dư ở split v3** (791 cặp train–test d = 12) và **đo lại** các chỉ số bị ảnh hưởng để
   khẳng định số liệu sạch. *(hạng mục 3, 5)*
4. **Cải thiện OCR biển 2 dòng** (A4–A7) hoặc nêu rõ giới hạn trong thesis/Q&A như một hạn chế đã biết. *(hạng mục 2, 5)*

---

## 5. Những hạn chế đã ghi nhận trung thực

Các điểm dưới đây là **sự thật đã đo**, ghi ra để không ai bị bất ngờ khi bảo vệ:

- **OCR biển 2 dòng chưa đạt.** A4 = 0,8734; A5 = 0,6098; A6 = 0,6555; A7 = 0,5227. Biển 1 dòng đạt/vượt,
  biển 2 dòng yếu (A6 riêng ≈ 0,581). Hậu xử lý chỉ +4,57 điểm (sửa 128 mẫu, 0 mẫu hỏng ở mức chuỗi).
  Đây là nút thắt kỹ thuật còn lại, **không** phải lỗi detection.
- **Rò rỉ tồn dư trong dữ liệu.** Split v3 còn 791 cặp train–test gần nhau (d = 12). Chưa khẳng định tập
  đã sạch hoàn toàn ⇒ một phần số liệu eval/OCR có thể lạc quan hơn thực tế.
- **Bộ chỉ số hiệu năng chưa đầy đủ.** NFR-P1 = 731 ms đã đạt (mục tiêu 800 ms; số cũ 5 857 ms đã bị bác bỏ).
  Nhưng **P2/P3/A9/R5 chưa đo**, và vài mục P4–P7 còn vấn đề trên baseline.
- **Thesis chưa phải bản nộp.** Nội dung 6 chương có thật nhưng bìa/lời cam đoan/lời cảm ơn còn placeholder,
  mục lục và các danh mục hình/bảng chưa sinh, chưa ghép PDF.
- **Slide và poster còn ở dạng nguồn** (outline / layout markdown), chưa kết xuất thành sản phẩm trình chiếu/in.
- **Installation guide chưa tách riêng** khỏi deployment guide; nội dung nằm rải ở README, user-manual và
  deployment/README.
- **Một yêu cầu mức *Must* đã bị đưa ra khỏi phạm vi.** Ngày 2026-07-20 giao diện được thu gọn hai lần:
  gỡ trang **Webcam** (FR-3.1, FR-3.4 → *Won't*), rồi gỡ trang **Tổng quan / Dashboard** (**FR-4.1: Must →
  *Won't***, FR-4.2: Should → *Won't*). Đây là **lần đầu** một yêu cầu mức *Must* rời phạm vi. Đó là quyết
  định thu gọn demo do người thực hiện yêu cầu, **không** phải chức năng làm không được — trang đã chạy
  thật và còn nguyên trong lịch sử git. Năng lực bên dưới giữ nguyên: `GET /api/statistics` và
  `GET /health` vẫn phục vụ và vẫn có kiểm thử tích hợp; FR-4.3–FR-4.8 (trang Lịch sử) không đổi.
  Đánh đổi đo được: gỡ `recharts` ⇒ gói tải về giảm ~730 KB → **328,8 KB (−55%)**.
  Bảng MoSCoW sau thay đổi: **34 FR = 21 Must · 6 Should · 3 Could · 4 Won't**.
- **Docker chỉ chạy CPU**, một rủi ro namespace `cv2` (ba gói cùng chiếm) đã được ghi nhận trong deployment guide.

---

> **Kết luận trung thực:** phần **kỹ thuật lõi** (mô hình detection, backend, frontend, database, docker, test)
> đã ở mức nộp được. Phần **chưa xong** tập trung ở (a) độ chính xác **OCR biển 2 dòng**, (b) **số liệu eval/hiệu năng**
> còn thiếu và chịu ảnh hưởng rò rỉ tồn dư, và (c) **kết xuất tài liệu cuối** (thesis PDF, slide, poster, installation guide riêng).
> Dự án **CHƯA** thoả toàn bộ Definition of Done: **17 done · 6 partial · 0 missing**.
