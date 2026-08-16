---
name: thesis-doc-writer
description: Hướng dẫn chuyên sâu và quy chuẩn soạn thảo tài liệu học thuật, báo cáo đồ án tốt nghiệp (ĐATN), đồ án môn học (ĐAMH), chuẩn trích dẫn tài liệu tham khảo, văn phong học thuật tiếng Việt và quy trình biên dịch Pandoc (DOCX/PDF). Kích hoạt skill này khi người dùng yêu cầu viết, sửa, định dạng hoặc kiểm tra tài liệu báo cáo kỹ thuật và luận văn.
---

# Kỹ Năng Soạn Thảo Tài Liệu & Báo Cáo Học Thuật (Thesis Doc Writer)

Skill này quy định chuẩn mực, văn phong, cấu trúc và quy trình viết tài liệu báo cáo kỹ thuật, luận văn Đồ án Tốt nghiệp (ĐATN) và Báo cáo Đồ án Môn học (ĐAMH) cho dự án.

---

## 1. Nguyên Tắc Văn Phong Học Thuật

1. **Ngôi xưng và tính khách quan:**
   - Tuyệt đối **không** dùng ngôi thứ nhất thân mật (*tôi, mình, em*).
   - Dùng chủ ngữ trung tính: **"Nhóm thực hiện"**, **"Đề tài này"**, **"Hệ thống"** hoặc dùng thể bị động (*"Mô hình được huấn luyện...", "Kết quả được đo đạc..."*).
2. **Số liệu và dữ kiện:**
   - Mọi số liệu kỹ thuật (mAP, độ trễ ms, RAM, FPS) phải lấy từ các file kết quả đo thực tế trong `docs/reports/*.json`, không tự bịa hoặc ước lượng.
   - Căn cứ pháp lý phải viện dẫn chính xác văn bản đang có hiệu lực:
     - **Thông tư 79/2024/TT-BCA** (Cấu trúc biển, seri, màu sắc).
     - **Thông tư 51/2025/TT-BCA** (Danh mục 34 mã tỉnh thành mới).
     - **QCVN 08:2024/BCA** (Kích thước và tỉ lệ biển số).
3. **Cấu trúc đoạn văn:**
   - Mỗi đoạn văn tập trung vào 1 luận điểm duy nhất.
   - Tránh câu cảm thán, ngôn từ quảng cáo hoặc khẳng định tuyệt đối thiếu chứng cứ (*"hoàn hảo nhất"*, *"tốt nhất"*).
4. **Quy tắc hạng mục chưa hoàn thành (Unfinished Work):**
   - Mọi tính năng, mô hình hoặc thử nghiệm chưa hoàn thành hoặc kết quả chưa đạt $\rightarrow$ **tuyệt đối không đưa vào thân bài / nội dung chính**.
   - Bắt buộc phải đưa trọn vẹn vào phần **Hạn chế** và **Hướng phát triển** ở Chương Kết luận. Thân bài chỉ viết những gì đã làm thật và có dữ liệu đo đạc thực tế.

---

## 2. Cấu Trúc Tài Liệu Chuẩn

### A. Đồ Án Tốt Nghiệp (Quyển 5-6 Chương)
- **Chương 1: Tổng quan và Đặt vấn đề** (Bối cảnh ALPR tại VN, thực trạng biển 2 dòng, mục tiêu & phạm vi).
- **Chương 2: Cơ sở Lý thuyết & Căn cứ Pháp lý** (Thị giác máy tính, YOLO11, OCR, quy chuẩn biển số VN).
- **Chương 3: Phân tích & Thiết kế Hệ thống** (Kiến trúc 5 tầng Clean Architecture, AI Engine Python thuần, thiết kế API & CSDL).
- **Chương 4: Thực nghiệm & Đánh giá** (Tập dữ liệu, quy trình huấn luyện, benchmark phát hiện & nhận dạng, đo đạc độ trễ CPU, kiểm thử tải NFR).
- **Chương 5: Kết luận & Hướng phát triển** (Các đóng góp chính, hạn chế còn lại, lộ trình mở rộng Edge AI / camera RTSP).
- **Tài liệu tham khảo & Phụ lục** (Mã tỉnh thành, ma trận nhầm lẫn, cấu hình Docker).

### B. Đồ Án Môn Học (Xử lý ảnh và ứng dụng - 40–50 trang)
- Bám sát yêu cầu môn học: Đặt vấn đề $\rightarrow$ Cơ sở lý thuyết xử lý ảnh $\rightarrow$ Thiết kế pipeline $\rightarrow$ Thực nghiệm & demo $\rightarrow$ Kết luận.

---

## 3. Quy Ước Định Dạng & Tham Chiếu (Pandoc Markdown)

1. **Tiêu đề phân cấp:**
   - `#` : Tên Chương (Heading 1)
   - `##` : Mục cấp 1 (Heading 2)
   - `###` : Mục cấp 2 (Heading 3)
   - `####` : Mục cấp 3 (Heading 4)
2. **Hình ảnh & Sơ đồ:**
   - Mọi hình ảnh phải đặt trong `docs/papers/figures/` hoặc `docs/slides/figures/`.
   - Cú pháp chuẩn có chú thích: `![Mô tả hình](figures/fig-ten-hinh.png){#fig:ten-hinh}`.
   - Sơ đồ kỹ thuật ưu tiên render từ mã nguồn hoặc Mermaid script (`scripts/render_mermaid.py`).
3. **Bảng biểu:**
   - Định dạng bảng Markdown chuẩn có căn lề rõ ràng (`|:---|:---:|---:|`).
   - Có tiêu đề bảng và nhãn tham chiếu: `Table: Bảng so sánh hiệu năng {#tbl:so-sanh}`.
4. **Trích dẫn khoa học:**
   - Đặt khóa trích dẫn dạng `[@author2024]` tương ứng với file BibTeX hoặc danh mục tài liệu tham khảo.

---

## 4. Công Cụ & Script Kiểm Tra

Trước khi bàn giao hoặc build tài liệu, luôn chạy các công cụ kiểm tra tự động:

```bash
# 1. Kiểm tra toàn bộ tham chiếu chéo (Cross-references) và đường dẫn ảnh
python scripts/check_thesis_refs.py

# 2. Biên dịch toàn bộ tài liệu sang DOCX và PDF
python scripts/build_thesis.py
```
