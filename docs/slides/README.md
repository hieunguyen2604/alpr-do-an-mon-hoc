# Slide bảo vệ và poster — hướng dẫn dựng

**Thuộc:** Phase 10 — chuẩn bị bảo vệ · **Ngày lập:** 19/07/2026

Thư mục này chứa **khung nội dung**, không chứa file slide đã dựng. Tài liệu này hướng dẫn chuyển khung đó thành slide thật.

---

## 1. Các file trong Phase 10

| File | Nội dung | Trạng thái |
|---|---|:--:|
| [`10-slides-outline.md`](10-slides-outline.md) | Khung 21 slide + speaker notes + ngân sách thời gian 15 phút | ✅ Xong |
| [`10-defense-qa.md`](10-defense-qa.md) | 40+ câu hỏi phản biện, câu trả lời, cảnh báo trả lời sai | ✅ Xong |
| [`../poster/10-poster-layout.md`](../poster/10-poster-layout.md) | Bố cục poster A0 dọc — 12 khối, bảng font size, bảng màu | ✅ Xong |
| `10-slides.md` hoặc `.pptx` | **File slide thật** | ⬜ Chưa dựng |
| [`10-demo-script.md`](10-demo-script.md) | Kịch bản demo trực tiếp | ✅ Xong |
| `../poster/poster-A0.pdf` | **File poster thật** | ⬜ Chưa dựng |

---

## 2. Chọn công cụ dựng slide

### Phương án A — Marp *(khuyến nghị)*

**Marp** dựng slide từ Markdown. Vì outline đã là Markdown nên chuyển đổi gần như chỉ là thêm dấu phân trang.

**Ưu điểm**
- Nội dung nằm trong Git, diff được, không phải file nhị phân
- Speaker notes viết thẳng bằng comment HTML `<!-- -->`
- Xuất PDF, HTML, PPTX bằng một lệnh
- **Render được mermaid** — dùng thẳng sơ đồ trong `system-architecture.md`, không phải vẽ lại

**Nhược điểm**
- Bố cục phức tạp (hai cột, ảnh đặt tự do) phải viết CSS
- Sửa vặt lúc gấp chậm hơn kéo thả

**Cài và chạy**

```bash
npm install -g @marp-team/marp-cli

# Xem trực tiếp, tự cập nhật khi sửa file
marp --preview docs/slides/10-slides.md

# Xuất PDF (bản dự phòng bắt buộc mang theo)
marp docs/slides/10-slides.md --pdf --allow-local-files

# Xuất PPTX nếu hội đồng yêu cầu định dạng PowerPoint
marp docs/slides/10-slides.md --pptx --allow-local-files
```

**Khung front-matter đề xuất** — đặt ở đầu `10-slides.md`:

```yaml
---
marp: true
theme: default
paginate: true
size: 16:9
lang: vi
style: |
  section {
    font-family: 'Be Vietnam Pro', 'Inter', sans-serif;
    font-size: 26px;
    padding: 50px 60px;
  }
  h1 { color: #2563EB; font-size: 44px; }
  h2 { color: #0F172A; font-size: 34px; }
  strong { color: #DC2626; }
  table { font-size: 22px; }
  .warn {
    background: #FEF2F2;
    border-left: 6px solid #DC2626;
    padding: 12px 18px;
  }
  .ai-layer { background: #FEF3C7; border: 2px solid #D97706; }
---
```

**Cấu trúc một slide trong Marp**

```markdown
---

## S13 — Xử lý biển 2 dòng

- CRNN/CTC giả định alignment đơn điệu trên **một** dòng
- PaddleOCR resize về cao cố định **48 px** → biển xe máy AR 1,36 ⇒ mỗi dòng còn ~24 px

![w:800](../images/split-hstack.svg)

<!--
Speaker notes: chép nguyên phần SPEAKER NOTES của S13 trong 10-slides-outline.md vào đây.
Marp đưa nội dung comment này vào phần notes khi xuất PPTX.
-->
```

### Phương án B — PowerPoint / Google Slides

Chọn phương án này nếu cần bố cục phức tạp, hiệu ứng chuyển, hoặc hội đồng yêu cầu nộp `.pptx`.

**Cách làm hiệu quả**
1. Tạo **Slide Master** trước, đặt sẵn màu và cỡ chữ theo mục 4 — đừng chỉnh tay từng slide
2. Tạo 4 layout dùng lại: *Bìa* · *Tiêu đề + gạch đầu dòng* · *Tiêu đề + hình lớn* · *Tiêu đề + bảng*
3. Chép **Nội dung trên slide** từ outline vào phần thân
4. Chép **Speaker notes** vào ô Notes — PowerPoint có sẵn chế độ Presenter View hiện notes trên màn hình phụ
5. Chèn sơ đồ dưới dạng **SVG**, không phải PNG

⚠️ **Kiểm tra font tiếng Việt.** Nếu máy chiếu ở phòng bảo vệ không có font đã dùng, PowerPoint thay font khác và **vỡ bố cục toàn bộ**. Hai cách phòng:
- Nhúng font: *File → Options → Save → Embed fonts in the file*
- **Luôn mang theo bản PDF** — PDF nhúng font, không phụ thuộc máy chiếu

---

## 3. Quy ước màu sắc

Dùng **cùng bảng màu** cho slide và poster. Người xem cả hai phải nhận ra cùng một hệ thống.

| Vai trò | Mã màu | Dùng ở đâu |
|---|---|---|
| Nền | `#FFFFFF` | Nền slide |
| Chữ chính | `#0F172A` | Toàn bộ chữ thân |
| **Nhấn 1 — chủ đạo** | `#2563EB` | Tiêu đề slide, khối API/Frontend, cột "biển 1 dòng" |
| **Nhấn 2 — tầng AI** | `#D97706` (nền `#FEF3C7`) | Khối AI trong sơ đồ kiến trúc |
| **Nhấn 3 — cảnh báo / biển 2 dòng** | `#DC2626` (nền `#FEF2F2`) | Nhánh biển 2 dòng · con số 45,7% · dấu ❌ · khối Hạn chế |
| Thành công | `#059669` | Dấu ✅ trong khối Kết luận |
| Nền khối phụ | `#F1F5F9` | Nền bảng, khối trích dẫn |
| Viền | `#CBD5E1` | Kẻ bảng |

**Ba quy tắc bắt buộc**
1. **Đỏ chỉ mang một nghĩa xuyên suốt: biển 2 dòng và các hạn chế.** Dùng đỏ cho thứ khác làm loãng thông điệp chính.
2. **Vàng hổ phách chỉ dành cho tầng AI** — khớp đúng màu trong sơ đồ mermaid gốc ở `system-architecture.md`.
3. Kiểm tra tương phản **WCAG AA (≥ 4,5:1)**. Phòng bảo vệ thường sáng, máy chiếu làm nhạt màu — màu nhạt trên nền trắng sẽ biến mất.

**Cỡ chữ tối thiểu trên slide** (khoảng cách xem ~4 m trong phòng bảo vệ)

| Cấp | Cỡ tối thiểu | Đề xuất |
|---|---:|---:|
| Tiêu đề slide | 36 pt | 44 pt |
| Chữ thân / gạch đầu dòng | **24 pt** | 28 pt |
| Chữ trong bảng | **20 pt** | 22 pt |
| Chú thích, nguồn | **16 pt** | 18 pt |

⛔ Không có chữ nào dưới **16 pt** trên slide. Bảng nào phải nhỏ hơn 20 pt mới vừa thì bảng đó **có quá nhiều cột** — cắt bớt cột, đừng thu chữ.

---

## 4. File hình cần chuẩn bị

Đặt tất cả trong `docs/images/` (tạo mới), đặt tên theo slide dùng nó.

| # | File đề xuất | Dùng ở | Nguồn | Trạng thái |
|---|---|---|---|:--:|
| 1 | `hook-openalpr.svg` | S2, poster Khối H | Vẽ mới — 2 cột 94,3% / 45,7% | ⬜ |
| 2 | `plate-types-ar.png` | S5, poster Khối 1 | Cắt 3 biển thật từ dataset, ghi AR | ⬜ |
| 3 | `legal-timeline.svg` | S6 | Vẽ mới — trục thời gian TT 24/2023 → 79/2024 → 51/2025 | ⬜ |
| 4 | **`architecture-5layer.svg`** | S7, poster Khối 4 | Render mermaid `system-architecture.md` §2 | ⬜ |
| 5 | `ai-layer-isolation.svg` | S8 | Vẽ mới — 3 hộp, mũi tên đi lên bị gạch chéo | ⬜ |
| 6 | **`pipeline-flow.svg`** | S9, poster Khối 5 | Render mermaid `system-architecture.md` §3 | ⬜ |
| 7 | `ar-distribution.png` | S10, S13, poster Khối 6 | `datasets/statistics/` — vẽ lại kèm đường ngưỡng 2,5 | ⬜ |
| 8 | `fliplr-mirror.png` | S11 | Một biển + ảnh soi gương, có dấu ✗ | ⬜ |
| 9 | `training-curve.png` | S12 | `runs/cpu-finetune-416/results.csv` — **cập nhật lại sát ngày bảo vệ** | ⬜ |
| 10 | ⭐ **`split-hstack.svg`** | S13, poster Khối 6 | Xuất ảnh trung gian từ `ai/inference/two_line.py` | 🔴 **Ưu tiên cao nhất** |
| 11 | `plate-rules-positions.svg` | S14 | Vẽ mới — chuỗi `59-H1 234.56` tô màu theo loại ràng buộc | ⬜ |
| 12 | `postproc-measure.svg` | S15 | Vẽ mới — 2 nhánh `raw_ocr_text` / `plate_number` | ⬜ |
| 13 | `latency-budget.svg` | S17, poster Khối 7 | Vẽ mới — cột xếp chồng 405 ms, vạch 800 ms | ⬜ |
| 14 | Ảnh chụp **3 trang** giao diện | S16, poster Khối 8 | `docs/screenshots/`: `image-detection.png` · `video-detection.png` · `history.png` | ⚠️ **Chụp lại** |

**Render mermaid ra SVG**

```bash
npm install -g @mermaid-js/mermaid-cli

# Tách khối mermaid từ system-architecture.md ra file .mmd trước, rồi:
mmdc -i architecture.mmd -o docs/images/architecture-5layer.svg -b transparent
```

⚠️ Chữ trong sơ đồ mermaid xuất mặc định khoảng 14 pt — đọc được trên màn hình, **không đọc được trên poster**. Chỉnh `fontSize` trong cấu hình mermaid trước khi render, hoặc sửa trực tiếp trong SVG sau khi xuất.

---

## 5. Trạng thái hạng mục Phase 10

| # | Hạng mục | Trạng thái | Còn thiếu gì |
|---|---|:--:|---|
| 1 | Bộ Q&A phản biện | ✅ Xong | — |
| 2 | Khung slide + speaker notes | ✅ Xong | — |
| 3 | Bố cục poster | ✅ Xong | — |
| 4 | **File slide thật** | ⬜ Chưa dựng | Chọn công cụ, dựng theo outline |
| 5 | **File poster thật** | ⬜ Chưa dựng | Dựng theo layout |
| 6 | Hình minh hoạ | 🔄 0/14 xong · 1 phần | 13 hình cần làm + 3 ảnh chụp cần chụp lại — xem bảng mục 4 |
| 7 | Ảnh chụp giao diện | ⚠️ **Cần chụp lại** | 3 ảnh dùng được trong `docs/screenshots/` (`image-detection` · `video-detection` · `history`). `dashboard.png` **bỏ** — trang Tổng quan đã gỡ 2026-07-20. Cả 3 ảnh chụp lúc sidebar còn 5 mục ⇒ chụp lại trên giao diện **3 trang** hiện hành trước khi nộp |
| 8 | Kịch bản demo trực tiếp | ✅ Xong | `10-demo-script.md` |
| 9 | **Số liệu cho S12** (kết quả detection) | ✅ **Đã có** | `models/best.pt` (YOLO11n, `imgsz=640`, split v3, 20 epoch), test v3 1.514 ảnh: mAP@0.5 = 0,9829 · mAP@0.5:0.95 = 0,7834 · P = 0,9837 · R = 0,9714 |
| 10 | **Số liệu cho S15** (đóng góp hậu xử lý) | ✅ **Đã có** | 2.801 biển: A4 = 0,8734 · A5 = 0,6098 · A6 = 0,6555 (A6 − A5 = +4,57 điểm) — xem `docs/reports/04-ocr-report.md` |
| 11 | **Số liệu cho S17** (hiệu năng CPU) | ✅ **Đã có** | NFR-P1 đạt: p95 = 731,15 ms client-side / 780,36 ms in-process (mục tiêu 800 ms); phân rã OCR 64,3% / detect 34,2% |
| 12 | Tập dượt tính giờ | ⬜ Chưa làm | Chạy thử ≥ 2 lần, bấm giờ |

### Ba slide còn ô trống — quy tắc xử lý

**S12, S15, S17 để bảng trống là có chủ đích.**

| Slide | Chờ gì | Nếu đến ngày bảo vệ vẫn chưa có |
|---|---|---|
| **S12** — kết quả detection trên test | Phase 3 — huấn luyện xong 40 epoch | Giữ bảng test trống, trình bày bảng val kèm **hai cảnh báo**: đây là val không phải test, và đo ở 416 px không phải 640 px |
| **S15** — đóng góp hậu xử lý | Phase 4 + 7 — cần nhãn chuỗi biển số | Giữ bảng trống, trình bày **thiết kế phép đo** — đó mới là đóng góp học thuật, con số chỉ là kết quả của nó |
| **S17** — hiệu năng CPU | Phase 7 — kiểm thử hiệu năng | Giữ bảng trống, trình bày **ngân sách độ trễ ~405 ms** và nói rõ đó là ước lượng, không phải số đo |

> **Không được điền số phỏng đoán vào ba bảng này.** Bảng trống có đủ tên cột, đơn vị và ngưỡng chỉ tiêu nói rằng *phép đo đã thiết kế xong, chỉ chờ số*. Bảng bị xoá đi nói rằng *không nghĩ tới*. Bảng điền số bịa thì bị bắt tại chỗ và mất toàn bộ uy tín phần thực nghiệm.
>
> Nguyên tắc chung của cả đồ án: **một con số chỉ được dùng nếu tái lập được từ kho mã hiện tại.**

---

## 6. Thứ tự làm — đề xuất

1. **Render 2 sơ đồ mermaid ra SVG** (#4, #6 bảng mục 4) — dùng lại cho cả slide và poster, làm một lần dùng hai chỗ
2. 🔴 **Làm ảnh `split-hstack.svg`** — hình quan trọng nhất, xuất từ `two_line.py`
3. Dựng **file slide** theo outline, để trống 3 bảng chưa có số
4. **Tập dượt bấm giờ** — nếu quá 15 phút thì cắt slide, đừng nói nhanh hơn
5. Dựng **poster**, dùng lại hình đã có
6. Viết **kịch bản demo** `10-demo-script.md`
7. Sát ngày bảo vệ: **cập nhật S12 nếu train đã xong**, cập nhật `training-curve.png`
8. Đọc lại `10-defense-qa.md`, đặc biệt mục *"Ba câu dễ trả lời sai nhất"*

---

## 7. Checklist ngày bảo vệ

**Mang theo**
- [ ] Slide bản **PDF** trong USB — không phụ thuộc máy chiếu hiểu định dạng gốc
- [ ] Slide bản gốc (`.md` / `.pptx`) dự phòng
- [ ] Poster đã in, có ống đựng
- [ ] Bản in `10-defense-qa.md` mục *Phụ lục — Bảng số liệu tra nhanh*

**Chuẩn bị máy — làm TRƯỚC khi vào phòng**
- [ ] Backend đã khởi động và trả `/health` đúng
- [ ] Frontend đã khởi động, mở sẵn trang `/` (Nhận dạng ảnh — trang chủ)
- [ ] Tab Swagger mở sẵn
- [ ] 2–3 ảnh test **đã biết chắc chạy được**, để sẵn trên desktop
- [ ] Tắt thông báo hệ thống, tắt chế độ ngủ màn hình

> ⚠️ **Đừng để lần chạy đầu tiên của buổi bảo vệ là lần khởi động server.**

**Nội dung — kiểm lần cuối**
- [ ] S2 còn nguyên cảnh báo *"số liệu Brazil, không phải Việt Nam"*
- [ ] S12/S15/S17 — ô trống ghi `—`, không có số phỏng đoán
- [ ] Mọi con số trên slide đọc lại từ file nguồn, không chép tay
- [ ] Ảnh nhúng hết vào file, không link ngoài
- [ ] **S16 mô tả đúng 3 trang** (Nhận dạng ảnh · Nhận dạng video · Lịch sử) và ảnh chụp đã chụp lại
      trên giao diện hiện hành — không còn `dashboard.png`, không còn dòng "4 trang"
