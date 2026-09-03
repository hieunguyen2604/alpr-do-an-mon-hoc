---
name: slide-deck-builder
description: Hướng dẫn chuyên sâu và quy chuẩn xây dựng slide thuyết trình bảo vệ Đồ án Tốt nghiệp (ĐATN), Đồ án Môn học (ĐAMH), slide báo cáo kỹ thuật; quy tắc bố cục Pandoc/Marp, kịch bản thuyết trình (Speaker Notes), phân bổ thời gian (Timing Budget) và kiểm tra lỗi tràn chữ/đè khối. Kích hoạt skill này khi người dùng yêu cầu soạn thảo, chỉnh sửa, dàn trang hoặc biên dịch slide trình chiếu PowerPoint/PDF.
---

# Kỹ Năng Xây Dựng Slide Thuyết Trình (Slide Deck Builder)

Skill này cung cấp các nguyên tắc vàng, cấu trúc chuẩn, quy tắc kỹ thuật và quy trình biên dịch slide cho các bài báo cáo Đồ án Tốt nghiệp, Đồ án Môn học và Báo cáo Kỹ thuật.

---

## 1. Nguyên Tắc Thiết Kế Slide Trình Chiếu

1. **"Một slide — Một thông điệp chính":**
   - Slide là thứ **chiếu lên màn hình**, không phải tài liệu đọc. Người nghe chỉ mất 3–5 giây để nắm bắt ý chính.
   - Dùng gạch đầu dòng ngắn (tối đa 3–5 gạch đầu dòng/slide, 5–10 từ/dòng).
   - In đậm (**bold**) các chỉ số quan trọng (mAP, độ trễ ms, % chính xác).
2. **Quy tắc bố cục Pandoc bắt buộc:**
   - Sử dụng cấp `##` cho mỗi slide (`--slide-level=2`).
   - **Bảng hoặc Hình ảnh phải là khối CUỐI CÙNG của slide** và **chỉ được có tối đa 1 bảng HOẶC 1 hình** trên mỗi slide (để tránh Pandoc tự ngắt thành slide mồ côi).
   - Đoạn văn/câu dẫn trên hình/bảng tối đa **3 dòng** để tránh bị lỗi vẽ đè chữ lên hình/bảng.
3. **Phân biệt hai tệp song hành:**
   - `*-slides.md`: Nội dung ngắn gọn chiếu lên màn hình.
   - `*-slides-outline.md`: Kịch bản chi tiết, số liệu đầy đủ, speaker notes và ngân sách thời gian cho người thuyết trình.
4. **Quy tắc hạng mục chưa hoàn thành:**
   - Các slide chính (S1–S26) chỉ trình bày những gì **đã làm và có số liệu thực nghiệm thật**.
   - Mọi hạn chế, tính năng chưa xong, hoặc mô hình thử nghiệm không đạt $\rightarrow$ **tuyệt đối không đưa vào slide chính**, chỉ xuất hiện tại slide **Hạn chế** và slide **Hướng phát triển** (S29–S30) hoặc slide **Backup Q&A**.

---

## 2. Cấu Trúc Các Bộ Slide Có Sẵn

### A. Slide Đồ Án Tốt Nghiệp (15–20 phút) — *trên nhánh `main`, không có ở nhánh này*
- **Tệp nguồn:** `docs/slides/10-slides.md` (28 slide: 24 chính + 4 backup)
- **Kịch bản:** `docs/slides/10-kich-ban-noi.md` (ngân sách 885 s ≈ 14:45)

### B. Slide Đồ Án Môn Học (7–10 phút) — *bộ duy nhất trên nhánh này*
- **Tệp nguồn:** `docs/slides/12-slides-mon-hoc.md` (**15 slide** `##`)
- **Trọng tâm:** Pipeline thị giác máy tính (YOLO11n + PP-OCRv5), thử nghiệm độ trễ CPU và demo sản phẩm.

---

## 3. Quy Trình Biên Dịch & Kiểm Thử Slide

### A. Biên Dịch Sang PowerPoint (.pptx)
Tự động ánh xạ nội dung Markdown vào template chuẩn UIT (`template-uit.pptx`):

```bash
# Biên dịch toàn bộ các bộ slide
python scripts/build_thesis.py
```

### B. Kiểm Tra Tràn Chữ & Đè Khối (Bắt buộc sau mỗi lần sửa)
Kiểm tra chiều cao khung chữ và hiện tượng đè khối trong PowerPoint:

```powershell
# Chạy script kiểm tra render slide PowerPoint
powershell -File scripts/check_slides.ps1
```
*Kết quả phải trả về 0 lỗi tràn chữ.*

---

## 4. Danh Mục Tài Liệu Bổ Trợ

> **Trên nhánh `do-an-mon-hoc`:** các tài liệu bảo vệ dưới đây **không có ở nhánh này**
> — chúng nằm trên `main`. Deck duy nhất còn ở đây là `docs/slides/12-slides-mon-hoc.md`.
>
> - Kịch bản Q&A phản biện: `docs/slides/10-defense-qa.md` *(trên `main`)*
> - Kịch bản demo trực tiếp: `docs/slides/10-demo-script.md` *(trên `main`)*
> - Kịch bản nói 24 slide: `docs/slides/10-kich-ban-noi.md` *(trên `main`)*
