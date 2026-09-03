# Đồ án môn học — Xử lý ảnh và ứng dụng

> Nhận dạng biển số xe Việt Nam: khảo sát đóng góp của **từng bước xử lý ảnh**
> trong một hệ thống ALPR chạy đầu cuối trên CPU.
>
> **Sinh viên thực hiện:** Phạm Công Thành — 25410013 · Nguyễn Minh Hiếu — 25410007
> **Giảng viên hướng dẫn:** ThS. Cáp Phạm Đình Thăng · UIT — ĐHQG TP.HCM

> ### ⚠ Đây là nhánh `do-an-mon-hoc`
>
> Nhánh này **chỉ giữ phần đồ án môn học** và đã được dọn mạnh cho gói nộp:
> quyển đồ án tốt nghiệp, tài liệu bảo vệ, toàn bộ báo cáo đo lường
> (`docs/reports/`), dữ liệu khảo sát (`datasets/`) và tài liệu quy trình
> nằm nguyên trên nhánh `main` — không có gì bị mất, chuyển nhánh là thấy lại.
>
> **Không merge nhánh này về `main`** — merge sẽ xoá các phần trên.
> Muốn đưa thay đổi ngược về thì cherry-pick từng commit.

---

## 1. Sản phẩm nộp

| Tệp trong `nop/` | Nội dung |
|---|---|
| `01-do-an-mon-hoc.pdf` | Quyển đồ án, **43 trang** (bản Word cùng tên để ghi chú) |
| `02-slide-mon-hoc.pptx` | Slide báo cáo, **16 slide**, chuẩn 7–10 phút |

Kết quả chính (đo trên Intel i5-14600K, chỉ CPU): phát hiện **mAP@0.5 = 0,9829**
(YOLO11n tự huấn luyện, `models/best.pt`); đọc đúng cả chuỗi sau hậu xử lý
**77,01%** trên 2.801 biển có nhãn (khối hậu xử lý đóng góp **+13,28 điểm** —
372 biển sửa đúng, 0 biển hỏng); độ trễ p95 một ảnh **≈ 510 ms**.

---

## 2. Hệ thống

```
Ảnh → YOLO11n phát hiện biển → cắt + nắn hình → tách 2 dòng, ghép ngang
    → PaddleOCR PP-OCRv5 mobile → hậu xử lý theo luật biển số VN → kết quả
```

- `ai/` — pipeline suy luận + huấn luyện (Python thuần, không import web)
- `backend/` — FastAPI + SQLAlchemy + SQLite, REST API, Swagger
- `frontend/` — React + Vite + TypeScript: Nhận dạng ảnh · Video · Lịch sử
- `tests/` — 1.004 test tự động
- `demo/` — ảnh mẫu 1 dòng / 2 dòng / nhiều biển + video, dùng khi trình bày
- `docs/papers/mon-hoc/` — nguồn Markdown của quyển; `docs/slides/` — nguồn deck

## 3. Chạy ứng dụng

```bash
# Backend — từ thư mục gốc
backend/.venv/Scripts/python.exe -m uvicorn backend.main:app --port 8000
# Swagger: http://localhost:8000/docs

# Frontend — cần Node >= 18
cd frontend && npm install && npm run dev
# Giao diện: http://localhost:5173
```

Hoặc bằng Docker:

```bash
docker compose up
```

## 4. Dựng lại quyển và slide

```bash
python scripts/build_thesis.py
powershell -File scripts/export_thesis_pdf.ps1
```

Mặc định trên nhánh này đã trỏ vào bản môn học. Bước PowerShell bắt buộc chạy
sau cùng — nó để Word điền số trang cho mục lục rồi chép PDF + DOCX vào `nop/`.
Kiểm tra tham chiếu chéo: `python scripts/check_thesis_refs.py` (0 chết);
kiểm slide sau khi dựng: `powershell -File scripts/check_slides.ps1`.

## 5. Quy ước

- Tài liệu học thuật tiếng Việt; mã nguồn, chú thích và Swagger tiếng Anh.
- Mã AI không import FastAPI; không hard-code đường dẫn.
- Mọi con số trong quyển/slide truy được về phép đo thật
  (hồ sơ đo đầy đủ: `docs/reports/` trên nhánh `main`).

## 6. Giấy phép

Sử dụng cho mục đích học thuật. Bộ dữ liệu và mô hình bên thứ ba theo giấy phép
gốc; dữ liệu biển hiếm từ workspace `nguyenluanAI` (Roboflow) — **CC BY 4.0**.
