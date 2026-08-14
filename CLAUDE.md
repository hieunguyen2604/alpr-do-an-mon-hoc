# AI Graduation Project

## Project Information

**Project Title**

Developing an AI-based Vietnamese License Plate Recognition System

**Objective**

Build a complete AI-powered Automatic License Plate Recognition (ALPR) system suitable for a graduation thesis.

The final deliverable must include:

* AI Model
* Dataset
* Backend
* Frontend
* Database
* Deployment
* Documentation
* Thesis
* Presentation
* Demo
* Testing Report

This project should be production-like rather than a simple demo.

---

# Your Role

You are acting as a complete engineering team:

* AI Researcher
* Computer Vision Engineer
* Machine Learning Engineer
* Backend Engineer
* Frontend Engineer
* DevOps Engineer
* Database Designer
* Software Architect
* QA Engineer
* Technical Writer

Never act as a code generator only.

Always think like an experienced software architect.

---

# General Principles

Always:

* Think before coding.
* Explain architecture first.
* Build incrementally.
* Keep code modular.
* Use Clean Architecture.
* Follow SOLID principles.
* Write reusable code.
* Avoid duplicated code.
* Prefer maintainability over shortcuts.
* Every module must contain documentation.
* Every implementation must update project documentation.

Never generate everything at once.

Always wait for approval before moving to the next major phase.

---

# Technology Stack

## AI

* Python 3.12
* PyTorch
* YOLO11
* PaddleOCR
* OpenCV
* NumPy

## Backend

* FastAPI
* SQLAlchemy
* Alembic
* SQLite

## Frontend

* React
* Vite
* TypeScript
* TailwindCSS

## Database

SQLite

## Deployment

Docker

Docker Compose

## Development

Git

VS Code

macOS Apple Silicon (M3 Pro)

> **Ghi chú Phase 0 (2026-07-19):** dòng môi trường phát triển ở trên **không khớp với máy thực tế**.
> Máy đang dùng là **Windows 11 Pro, Python 3.13, không có GPU CUDA**.
> Xem [docs/00-requirements/environment.md](docs/00-requirements/environment.md) để biết chi tiết và tác động.

---

# Functional Requirements

The system shall support

## Image Detection

Upload image

Detect license plate

Recognize text

Store result

Display result

---

## Video Detection

Upload video

Extract frames

Detect plates

Recognize plates

Generate processed video

Store history

---

## Realtime Detection

Webcam

Realtime detection

Realtime OCR

Bounding boxes

Recognition history

> **Ghi chú 2026-07-20:** trang Webcam đã **gỡ khỏi giao diện web** theo quyết định thu gọn phạm vi (xem Nhật ký quyết định). Năng lực thời gian thực giữ ở tầng API `POST /api/detect/frame`. FR-3.1/FR-3.4 → Won't; chi tiết tại [functional-requirements.md](docs/00-requirements/functional-requirements.md#4-fr-3--nhận-dạng-thời-gian-thực-webcam).

---

## Dashboard

Statistics

History

Search

Filter

Preview images

Download result

---

## Detection Output

Plate Number

Confidence

Processing Time

Input Type

Image

Cropped Plate

Timestamp

---

# AI Pipeline

Image / Video / Webcam

↓

YOLO11

↓

Crop Plate

↓

PaddleOCR

↓

Regex Correction

↓

Vietnamese Plate Validation

↓

Database

↓

REST API

↓

Dashboard

---

# Database

DetectionHistory

* Id
* PlateNumber
* Confidence
* InputType
* ImagePath
* PlateImagePath
* ProcessingTime
* DetectedTime
* CreatedAt

> **Ghi chú Phase 0 — ✅ ĐÃ PHÊ DUYỆT 2026-07-19:** schema chính thức đã được **mở rộng** so với 9 trường ở trên.
> Bổ sung: `raw_ocr_text`, `ocr_confidence`, `bbox_x/y/w/h`, `is_valid_format`, `plate_line_count`, `source_job_id`.
> Thêm **bảng mới `DetectionJob`** (theo dõi trạng thái tác vụ video).
> Lý do chính: schema gốc không nhóm được nhiều biển số thuộc cùng một lần tải lên ⇒ thống kê đếm sai;
> và không lưu chuỗi OCR thô ⇒ không đo được đóng góp của bước hậu xử lý.
> Đặc tả đầy đủ: [docs/architecture/system-architecture.md](docs/architecture/system-architecture.md#62-mở-rộng-so-với-claudemd--đã-phê-duyệt-2026-07-19).

---

# Project Folder Structure

```
project/

docs/

papers/

reports/

slides/

poster/

datasets/

raw/

processed/

annotations/

statistics/

backend/

frontend/

ai/

training/

evaluation/

inference/

deployment/

docker/

tests/

demo/

models/

scripts/

README.md

CLAUDE.md
```

---

# Development Roadmap

## Phase 0

Requirement Analysis

Deliverables

* Requirement Specification
* Functional Requirements
* Non-functional Requirements
* Project Scope
* Timeline

---

## Phase 1

Research

Tasks

* Literature Review
* Related Works
* Technology Comparison
* YOLO Comparison
* OCR Comparison
* Vietnamese License Plate Standards

Deliverables

* Research Report
* References
* Comparison Tables

---

## Phase 2

Dataset

Tasks

* Search public datasets
* Download datasets
* Merge datasets
* Verify dataset
* Remove duplicates
* Organize folders
* Annotation verification
* Data augmentation
* Split train/val/test
* Generate statistics

Deliverables

* Dataset Report
* Dataset Statistics
* Dataset Visualization
* Download Scripts
* Verification Scripts

---

## Phase 3

Model Training

Tasks

* Configure YOLO11
* Hyperparameter tuning
* Train
* Validate
* Evaluate
* Export best model

Deliverables

* best.pt
* Training Log
* Precision
* Recall
* mAP
* F1
* Loss Curve
* Confusion Matrix
* Evaluation Report

---

## Phase 4

OCR

Tasks

* PaddleOCR integration
* OCR optimization
* Vietnamese regex
* Plate correction

Deliverables

* OCR Benchmark
* OCR Accuracy Report

---

## Phase 5

Backend

Tasks

* FastAPI
* SQLAlchemy
* SQLite
* REST API
* Swagger
* Image Upload
* Video Upload
* Webcam API

Deliverables

* API Documentation
* Backend README

---

## Phase 6

Frontend

Tasks

* Dashboard
* Upload Image
* Upload Video
* Webcam
* Detection History
* Statistics
* Search
* Filter

Deliverables

* UI Documentation
* Frontend README

---

## Phase 7

Testing

Tasks

* Unit Test
* Integration Test
* AI Accuracy Test
* Performance Test
* Stress Test

Deliverables

* Testing Report
* Benchmark Report

---

## Phase 8

Deployment

Tasks

* Docker
* Docker Compose
* Installation
* User Guide

Deliverables

* Deployment Guide
* Installation Guide

---

## Phase 9

Documentation

Generate

* Proposal
* Thesis
* User Manual
* Technical Manual
* API Documentation
* Deployment Guide
* Installation Guide

Every implementation must update the corresponding documentation.

---

## Phase 10

Presentation

Generate

* Defense Slides
* Speaker Notes
* Demo Script
* Poster
* Defense Questions
* Suggested Answers

---

## Phase 11

Final Package

Must contain

Source Code

Dataset

Trained Model

Docker

Backend

Frontend

README

API Documentation

User Manual

Technical Manual

Deployment Guide

Installation Guide

Testing Report

Benchmark Report

Thesis

Slides

Poster

Demo Video

Defense Script

---

# Coding Rules

Always

* Type hints
* Docstrings
* Comments
* Logging
* Error handling
* Validation
* Modular design
* Dependency Injection where appropriate

Never

* Hardcode paths
* Duplicate logic
* Mix AI code with API logic
* Skip documentation

---

# Documentation Rules

Every phase must generate:

* README
* Architecture Diagram
* Flow Diagram
* Sequence Diagram
* ER Diagram (if changed)
* API Documentation (if changed)
* User Guide (if changed)
* Thesis Section (if changed)
* Slide Update (if changed)

Documentation must evolve together with the source code.

---

# Working Process

For every phase

1. Explain objectives.
2. Explain architecture.
3. Explain design decisions.
4. List tasks.
5. Estimate outputs.
6. Implement.
7. Explain how to run.
8. Explain how to test.
9. Update documentation.
10. Wait for approval.

Do not continue automatically to the next phase.

---

# Definition of Done

The project is complete only when all of the following exist:

* Complete source code
* AI model
* Dataset
* Training scripts
* Evaluation reports
* Backend
* Frontend
* Database
* Docker deployment
* Unit tests
* Integration tests
* Performance report
* API documentation
* User manual
* Technical manual
* Deployment guide
* Installation guide
* Thesis
* Presentation slides
* Poster
* Demo script
* Defense Q&A
* README

If any item is missing, the project is NOT complete.

---

# Project Decisions Log

Các quyết định đã chốt, bổ sung cho tài liệu gốc:

| Ngày | Quyết định | Lý do | Tài liệu |
|---|---|---|---|
| 2026-07-19 | Huấn luyện trên **Colab/Kaggle GPU**, suy luận local bằng CPU | Máy phát triển không có GPU CUDA | [environment.md](docs/00-requirements/environment.md) |
| 2026-07-19 | Tài liệu học thuật viết **tiếng Việt**, mã nguồn **tiếng Anh** | Bảo vệ bằng tiếng Việt, mã nguồn theo chuẩn quốc tế | — |
| 2026-07-19 | **Không có hạn nộp cố định** — thực hiện đủ 11 phase, ưu tiên chất lượng | Người thực hiện xác nhận | [timeline.md](docs/00-requirements/timeline.md) |
| 2026-07-19 | ✅ **Duyệt Phase 0 — chốt M0** | Đủ 5/5 deliverable, 5/5 sơ đồ bắt buộc | [SRS.md](docs/00-requirements/SRS.md) |
| 2026-07-19 | ✅ **Duyệt mở rộng schema CSDL** (6 trường + bảng `DetectionJob`) | Schema gốc gây đếm sai thống kê và không đo được hiệu quả hậu xử lý | [system-architecture.md](docs/architecture/system-architecture.md#62-mở-rộng-so-với-claudemd--đã-phê-duyệt-2026-07-19) |
| 2026-07-19 | Cập nhật căn cứ pháp lý: TT 24/2023 (hết hiệu lực 01/01/2025) → TT 79/2024 + TT 13/2025 + TT 51/2025 + QCVN 08:2024/BCA | Phát hiện ở Phase 1 khi đối chiếu nguồn pháp lý gốc | [01-vn-plate-standards.md](docs/reports/01-vn-plate-standards.md) |
| 2026-07-19 | ✅ **Duyệt Phase 1 — chốt M1.** Hoàn thành 6/6 task và 3/3 deliverable **sau khi sửa 25 lỗi do vòng phản biện phát hiện** (20 lỗi số liệu + 5 lỗi trích dẫn/phương pháp luận; 3 lỗi mức critical) | Đủ điều kiện M1: đã chọn xong công nghệ, có căn cứ trích dẫn (232 entry BibTeX, 247 khẳng định qua kiểm chứng đối kháng) | [01-README.md](docs/reports/01-README.md) |
| 2026-07-19 | **YOLO11n** làm mô hình detection chính cho Phase 3; **YOLO26n** huấn luyện song song làm đối chứng; tự đo mọi số liệu tốc độ trên máy thật | Phiên bản duy nhất vừa có số liệu tốc độ CPU chính thức, vừa có kiến trúc phù hợp đối tượng nhỏ / tỷ lệ khung hình dẹt, vừa có bằng chứng thực nghiệm trên ALPR | [01-yolo-comparison.md](docs/reports/01-yolo-comparison.md) mục 9.2, 9.3 |
| 2026-07-19 | **PaddleOCR PP-OCRv5_mobile là baseline, KHÔNG phải kết luận** — EasyOCR là ứng viên ngang hàng, quyết định cuối cùng thuộc benchmark **Phase 4** | Hai bằng chứng từng dùng biện minh cho PaddleOCR đã bị bác bỏ ở vòng kiểm chứng | [01-ocr-comparison.md](docs/reports/01-ocr-comparison.md) mục 5.1, 6.1 |
| 2026-07-19 | Biển 2 dòng xử lý bằng **split-then-hstack** (rectify → phân loại → tách → ghép ngang → OCR một lần → validate từng dòng) | trên bộ RodoSol-ALPR của Brazil, OpenALPR đo được 94,3% trên biển 1 dòng nhưng chỉ 45,7% trên biển 2 dòng (số liệu Brazil, KHÔNG phải Việt Nam) — điểm gãy đã đo, không phải rủi ro giả định | [01-ocr-comparison.md](docs/reports/01-ocr-comparison.md) mục 4.5 |
| 2026-07-19 | **VNLP là dataset chính** của Phase 2 (có điều kiện: xin được xác nhận giấy phép, nếu không chuyển Phương án B) | Bộ duy nhất đủ quy mô và có nhãn layout cho cả 3 nhánh detector / layout classifier / OCR | [01-dataset-survey.md](docs/reports/01-dataset-survey.md) mục 5.3, 6.1 |
| 2026-07-19 | **Charset OCR huấn luyện đủ A–Z + 0–9 (36 ký tự)**, ràng buộc hợp lệ đặt ở tầng hậu xử lý — **cấm** thu hẹp còn 20 chữ cái | Chữ `R` hợp lệ ở vị trí thứ hai của seri xe máy; charset 20 chữ làm mất thông tin ngay ở tầng mô hình, hậu xử lý không cứu được | [01-vn-plate-standards.md](docs/reports/01-vn-plate-standards.md) mục 5.2, 5.3 |
| 2026-07-20 | **Thu gọn giao diện web còn 4 trang**: trang chủ đổi thành Nhận dạng ảnh, Tổng quan lùi cuối menu (`/dashboard`), **gỡ trang Webcam** (route, menu, page, components, hàm `detectFrame`) | Người thực hiện yêu cầu tinh gọn cho demo. FR-3.1/FR-3.4 chuyển M→W; năng lực thời gian thực giữ nguyên ở tầng API `POST /api/detect/frame` (endpoint + test không đổi) | [functional-requirements.md](docs/00-requirements/functional-requirements.md#4-fr-3--nhận-dạng-thời-gian-thực-webcam) |
| 2026-07-20 | **Gỡ tiếp trang Tổng quan (Dashboard)** — giao diện còn **3 trang**: Nhận dạng ảnh (chủ), Nhận dạng video, Lịch sử. Xoá `pages/Dashboard.tsx`, `components/dashboard/` (10 tệp), hook `useApi`, hàm `getStatistics`/`getHealth`, và **gói `recharts`** | Người thực hiện yêu cầu. **FR-4.1 (Must) và FR-4.2 (Should) → W** — đây là lần đầu một yêu cầu **Must** bị gỡ khỏi phạm vi, phải nêu rõ khi bảo vệ. Endpoint `GET /api/statistics` và `/health` **vẫn phục vụ và vẫn có test**; FR-4.3–4.8 (lịch sử, tìm kiếm, lọc, chi tiết, tải về, sắp xếp) không đổi. Đổi lại: gói tải về giảm từ ~730 KB xuống 329 KB (−55%) | [functional-requirements.md](docs/00-requirements/functional-requirements.md#5-fr-4--dashboard-lịch-sử-và-tra-cứu) |
| 2026-07-28 | **Đo lại toàn bộ Chương 5** sau khi phát hiện bộ số cũ (20/07) mô tả một hệ thống không còn tồn tại | Bốn đợt sửa độ chính xác rơi vào 21–28/07. A4 lật ❌→🟡 (0,8848 → **0,9454**), A6 0,6730 → **0,7512**, A7 0,5295 → **0,5552** | [27-retry-ladder-cost-benefit.md](docs/reports/27-retry-ladder-cost-benefit.md) |
| 2026-07-28 | **Nối bậc thang thử-lại vào harness đo** (cả nhánh vùng cắt lẫn nhánh đầu-cuối) | `ocr_accuracy.py` chép lại các bước pipeline nên **chưa bao giờ gọi** `retry_skewed_variants` ⇒ mọi con số A4–A7 công bố 21–28/07 mô tả một pipeline **ngắn hơn bản giao hàng**. Đây là lần **thứ ba** cùng loại lỗi; biện pháp phòng ngừa đặt ra sau lần thứ hai đã được tuân thủ đầy đủ mà vẫn thất bại vì nhắm sai nguyên nhân gốc | ch5 mục 5.6.6 |
| 2026-07-28 | **Ba công cụ đo đọc `InferenceConfig.from_env()`** thay vì dựng trực tiếp | `ALPR_RECTIFY_ENABLED` / `ALPR_SR_RETRY_ENABLED` bị bỏ qua ở `benchmark_system.py`, `ocr_accuracy.py`, `benchmark_ocr.py` — hai công tắc sinh ra để Phase 7 bóc tách lại không tới được chính công cụ của Phase 7 | — |
| 2026-07-28 | ⚠ **Tắt siêu phân giải mặc định** (`sr_retry_enabled = False`); giữ nắn hình/giãn dọc | Nắn hình mua **34 biển** (+0,75 điểm A6) với giá +244 ms p95 — giữ. Siêu phân giải mua **0** với giá +319 ms p95 / +1.381 ms p99 và một mình đẩy NFR-P1 vượt sàn 1.500 ms. **Số 0 đó là số 0 cấu trúc**: cổng SR chỉ mở cho crop < 200 px, 0/120 mẫu ngữ liệu lọt cổng ⇒ quyết định dựa trên "chi phí đã đo, lợi ích chưa ai đo được", không phải "đã đo thấy vô dụng". Mã + công tắc giữ nguyên | [27](docs/reports/27-retry-ladder-cost-benefit.md) mục 5 |
| 2026-07-28 | **NFR-P1 chuyển ✅→🟡**: p95 731 ms → **1.143 ms** (sàn 1.500, mục tiêu 800) | Thoái lui **có chủ ý**, đổi lấy 34 biển đọc thêm. Trung vị không đổi (405,77 ms) vì bậc thang chỉ chạy sau khi đọc hỏng | ch5 mục 5.7.1 |
| 2026-08-02 | **Giữ bước phát hiện chữ của PaddleOCR**; thêm công tắc `ALPR_OCR_SKIP_DETECTION` **mặc định tắt** | Trên ngữ liệu 2.801 mẫu, bỏ det thắng **+12,46 điểm** A6 — nhưng mọi ảnh trong ngữ liệu đó là **ảnh cắt sẵn**. Đo lại trên bộ demo (ảnh toàn cảnh qua detector thật) thì **thứ tự đảo ngược**: model gốc 17/22 xuống 13/22. Ngoài ra chế độ chỉ-rec **không có khả năng trả chuỗi rỗng** (0/1.606 khung so với 173 của bản đang giao) nên nó *bịa* khi detector bắt nhầm | [31-detection-stage-ablation.md](docs/reports/31-detection-stage-ablation.md) |
| 2026-08-02 | ✅ **Duyệt mở rộng schema: thêm cột `upper_char_count` vào `detection_history`** (nullable, CHECK ∈ {3,4}), migration `0004_upper_char_count` | Chuỗi 8 ký tự của biển 2 dòng **nhập nhằng về nguyên tắc**: `67C10815` là `67C-108.15` nếu dòng trên đọc `67C`, là `67C1-0815` nếu đọc `67C1` — cả hai đều hợp lệ, không luật nào trên chuỗi phẳng phân định được. Chính bước split-then-hstack (đóng góp kỹ thuật lõi) là thứ **vứt mất ranh giới dòng**. Sau khi ghép, OCR trả một mảnh cho mỗi nửa nên độ dài mảnh đầu **chính là** số ký tự dòng trên — lấy được miễn phí. Lưu *bằng chứng*, vẫn suy ra *cách trình bày* lúc đọc, đúng lối `plate_line_count`/`plate_kind`. Đo trên bộ demo: **39/49 → 46/49 đúng hoàn toàn, 0 ca lệch định dạng** | [23-display-format-rules.md](docs/reports/23-display-format-rules.md) |
| 2026-08-02 | **Tái cấu trúc quyển: 6 chương → 7 chương.** Tách *Lựa chọn công nghệ* (§2.8 cũ) thành **Chương 3** riêng; dồn phần huấn luyện mô hình về cùng Chương 5 với phần cài đặt; ch3→4, ch5 còn lại→6, ch6→7 | Phần hội đồng hỏi nhiều nhất đang là 159 dòng nằm **cuối một chương 1.193 dòng** — người đọc mục lục không thấy nó. Làm bằng script kèm hai lớp kiểm chứng: **416 tham chiếu chéo 0 chết**, và nội dung bảo toàn **4.199→4.198 dòng** (chênh đúng 1 đoạn dẫn nhập chuyển có chủ đích). Kèm theo: chú thích cho **43 bảng** vốn chỉ có neo máy đọc, mục lục/danh mục hình/bảng **sinh tự động**, và danh mục **Tài liệu tham khảo 123 mục** đánh số toàn cục kiểu IEEE (trước đó mỗi chương đánh số cục bộ nên `[1]` mang 7 nghĩa khác nhau) | [00-thesis-outline-v2.md](docs/papers/00-thesis-outline-v2.md) |
| 2026-08-02 | ⛔ **DỪNG fine-tune bộ nhận dạng** — không chạy lượt fine-tune trên ngữ liệu đã gộp 521 biển hiếm | Bản giao hàng **vốn đã dùng model gốc** (`ocr_rec_model_dir = None`), nên không có mã nào chờ lượt này. Đồ án đã có **một lượt fine-tune hoàn chỉnh và đo đủ 4 cấu hình** ở mục 5.4: ở đúng chế độ production (det+rec) nó **thua 7,50 điểm**; chỉ thắng +12,46 điểm ở chế độ chỉ-rec, mà chế độ đó đã bị bác trên ảnh toàn cảnh. Quyển đã ghi rõ phần gộp biển hiếm là *“nguyên liệu chuẩn bị cho lần đo sau”* nên **không hứa việc chưa làm**. Giá phải trả: biển vàng vẫn kẹt ở n = 20 ⇒ kết luận độ chính xác OCR **vẫn chỉ áp cho biển trắng** (mục 7.3.8) | [30-rare-plate-integration.md](docs/reports/30-rare-plate-integration.md) mục 8.3 |
| 2026-08-13 | ✅ **NFR-P2 lật ❌ → ✅: 2,379 → 5,257 FPS** (sàn 3, mục tiêu 5). Con số cũ **không tái lập được** ở bất kỳ điều kiện nào trong 6 lần đo | Mã suy luận **giống hệt từng byte** giữa hai thời điểm. Lần đo 02/08 chạy khi máy cõng ~560% CPU của tiến trình khác và harness **đã tự dán nhãn PESSIMISTIC** — cảnh báo được in ra nhưng không được đọc. Giả thuyết tải cạnh tranh sau đó bị **chính thí nghiệm đối chứng bác bỏ**: ép tải 12 lõi chỉ xuống 4,057 FPS và nâng *cả* phân bố đều tay (p95/p50 ≈ 1,2), còn lần 02/08 có trung vị gần như máy rảnh nhưng đuôi gấp **6,93 lần** trung vị. Quy kết cũ cho bậc thang thử-lại cũng sai: nó chỉ nổ **6 lần trên 144 khung**, giải thích được ~52 ms trong 225 ms chênh lệch. **Nguyên nhân chính xác không xác định được và được ghi đúng như vậy.** Quy tắc mới: một lần đo có cảnh báo tải cạnh tranh **không được phép** thành số liệu công bố | [38](docs/reports/38-runtime-backend-and-nfr-p2.md) |
| 2026-08-13 | **Đo xong so sánh nền tảng suy luận; vẫn GIỮ PyTorch làm mặc định** | PyTorch 33,09 ms / ONNX 24,48 ms (1,35×) / **OpenVINO 21,12 ms (1,57×)**, mAP **không suy giảm** (0,983 so 0,9829), đầu cuối **+20%** (5,257 → 6,310 FPS). Không đổi mặc định vì NFR-P2 **đã đạt** mà không cần đổi, còn đổi thì mọi con số độ trễ ở Chương 5 sẽ lệch khỏi bản giao hàng — đồ án đã ba lần trả giá cho việc đo lại nửa vời. Bật lên chỉ cần đổi `ALPR_MODEL_PATH` | ch5 mục 5.6.3 |
| 2026-08-14 | ✅ **Thay bảng ánh xạ nhầm lẫn bằng bảng trích từ ma trận đo được** — chỉ hai mục vượt ngưỡng: `TO_DIGIT['L']` 1 → **4**, `TO_LETTER['7']` T → **Z** | Mã tự ghi lời hứa này trong docstring từ Phase 7 nhưng chưa ai làm, dù ma trận 36×36 đã nằm sẵn trong báo cáo 27. Ngưỡng đặt ra: **thắng ≥ 10 lần và ≥ 2× ứng viên nhì** — argmax thô cho 23 mục nhưng phần lớn dựa trên 1–3 lần, là nhiễu. Mục `L` đáng kể nhất: trực giác hình dạng ghép **đúng cặp nhưng sai chiều** (4:53 lần so với 1:1 lần). Kết quả trên 2.801 biển: **A6 0,7512 → 0,7701**, biển hai dòng **0,6996 → 0,7234**, hậu xử lý sửa **319 → 372 biển, làm hỏng 0**. **A5 đứng yên tới bốn chữ số** — đó là kiểm chứng quan trọng nhất, vì A5 đo *trước* hậu xử lý nên nó bất động chứng minh toàn bộ chênh lệch quy được cho đúng hai hằng số vừa đổi | [41](docs/reports/41-measured-confusion-tables.md) |
| 2026-08-14 | ⬜ **NFR-A7 chuyển ❌ → ⬜ _không đo được một cách có ý nghĩa_**, cùng cách xử lý NFR-A9 | Con số **0,5552** công bố 28/07 **không tái lập được**: chạy lại trên cùng 2.801 mẫu, cùng bộ phát hiện, cùng `imgsz = 640` cho **0,0000**. Không phải hệ thống hỏng — đường ống bản giao hàng trên **ảnh toàn cảnh thật đọc đúng 17/22 biển**, gồm cả biển quân đội, ngoại giao, vàng và xanh. Nguyên nhân là **thiết kế phép đo**: nhánh e2e nạp ảnh vuông 640×640 đã bóp méo tỷ lệ vào một detector huấn luyện trên ảnh giao thông toàn cảnh; harness đã tự dán nhãn KHÔNG ĐẠI DIỆN từ trước. Trên đầu vào ngoài phân bố, một thay đổi nhỏ ở tầng suy luận đủ lật hoàn toàn kết quả — dấu hiệu phép đo **không đo cái nó tưởng đang đo**. Suýt nữa công bố một **hồi quy giả**: lượt đầu cho 0,2588 chỉ vì `--detector-imgsz` mặc định 416 trong khi bản giao hàng chạy 640 — **lỗi thứ ba cùng họ trong ngày**, công cụ đo không khớp bản giao hàng | [41](docs/reports/41-measured-confusion-tables.md) mục 4–5 |
