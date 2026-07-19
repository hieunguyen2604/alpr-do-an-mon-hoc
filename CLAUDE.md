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
