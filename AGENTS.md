# Agent Guidelines: ALPR Project (ĐATN & ĐAMH)

Tài liệu này định hình cách làm việc của Agent khi tương tác với codebase, tài liệu và slide của đề tài **Nhận dạng biển số xe Việt Nam**.

---

## 🎯 1. Nguyên Tắc Cốt Lõi: Chống Lan Man & Tránh Overthinking

- **Bám sát sự thật (Fact-based):** Mọi số liệu kỹ thuật phải trích từ file đo thật trong `docs/reports/*.json`. Tuyệt đối không bịa số liệu.
- **Ranh giới đề tài (Scope):** Tôn trọng ranh giới ngoài phạm vi (không tracking, không barie, không multi-GPU, không microservices). Tập trung 100% vào **nhận diện biển 1 dòng & 2 dòng chạy tối ưu trên CPU**.
- **Không viết dông dài (Zero-fluff):** Đi thẳng vào kết quả và giải pháp. Bỏ qua các đoạn lý thuyết giáo khoa chung chung không phục vụ trực tiếp cho mô hình.
- **Hạng mục chưa hoàn thành (Unfinished Work):** Mọi tính năng, thử nghiệm dở dang hoặc chưa hoàn thành **tuyệt đối không đưa vào thân bài / nội dung chính** của báo cáo và slide. Phải chuyển trọn vẹn sang phần **Hạn chế** và **Hướng phát triển**.
- **Căn cứ pháp lý đúng:** Sử dụng **TT 79/2024**, **TT 13/2025**, **TT 51/2025** (34 tỉnh thành), **QCVN 08:2024**. Tuyệt đối không dùng TT 24/2023.

---

## 🏗️ 2. Bất Biến Kiến Trúc (Architecture Invariants)

1. **Tầng AI Engine (`ai/`):** Phải là **Python thuần 100%** (chỉ dùng PyTorch, OpenCV, NumPy, PaddleOCR). Cấm tuyệt đối import FastAPI, Pydantic, SQLAlchemy hoặc các thư viện web vào `ai/` để đảm bảo mô hình chạy độc lập ở CLI và unit test.
2. **Tầng Backend (`backend/`):** Đóng vai trò Service / API Gateway, chịu trách nhiệm validate dữ liệu bằng Pydantic, lưu trữ CSDL SQLite/PostgreSQL và gọi sang AI Engine.

---

## 📊 3. Quy Chuẩn Trực Quan Hóa (Data & Workflow Visualization Rules)

1. **Mọi so sánh BẮT BUỘC dùng BẢNG (Comparison $\rightarrow$ Table):**
   - So sánh giữa các mô hình (YOLO11 vs YOLOv8/Faster R-CNN), các engine OCR (PP-OCRv5 vs EasyOCR vs Tesseract), hoặc so sánh trước/sau can thiệp $\rightarrow$ **tuyệt đối không viết văn xuôi dài dòng**, phải kẻ bảng có cột đối chứng rõ ràng (Tiêu chí, Phương án A, Phương án B, Đánh đổi/Kết quả).
2. **Mọi luồng xử lý BẮT BUỘC dùng SƠ ĐỒ / DẢI HÌNH ẢNH (Pipeline & Workflow $\rightarrow$ Diagram/Strip):**
   - Kiến trúc hệ thống, chuỗi xử lý AI (Preprocess $\rightarrow$ YOLO $\rightarrow$ Crop $\rightarrow$ OCR $\rightarrow$ Normalizer), luồng xử lý 2 dòng $\rightarrow$ phải thể hiện bằng **sơ đồ khối hoặc dải ảnh minh họa đầu vào/đầu ra từng bước** (`fig-pipeline-strip.png`).
3. **Phân bố & Xu hướng BẮT BUỘC dùng BIỂU ĐỒ (Distribution/Trends $\rightarrow$ Chart):**
   - Biểu đồ phân bố độ trễ (Latency distribution), đường cong huấn luyện Loss/mAP, ma trận nhầm lẫn Confusion Matrix $\rightarrow$ dùng biểu đồ ảnh trực quan, không mô tả chay bằng lời.
4. **Bóc tách đóng góp (Ablation Study):**
   - Bắt buộc dùng bảng với 2 cột: **Mức cải thiện (+Δ metric)** và **Chi phí tính toán (+ms trễ)**.
5. **Phân tích ca lỗi (Error Analysis):**
   - Bắt buộc có **ảnh cắt thực tế** kèm bảng đối chiếu: *Chuỗi nhãn thật (Ground Truth)* vs *Chuỗi nhận dạng được (Predicted)* vs *Nguyên nhân gốc*.

---

## 📚 4. Quy Tắc Soạn Thảo Tài Liệu, Slide & Trích Dẫn

1. **Văn phong học thuật:** Khách quan, trung tính, dùng **"Nhóm thực hiện"**, **"Đề tài này"** hoặc thể bị động (tuyệt đối không dùng *tôi, em, chúng tôi*).
2. **Định dạng số liệu (Metric Formatting):**
   - *Trong Slide & Báo cáo tiếng Việt:* Dùng **dấu phẩy `,`** cho số thập phân (VD: `0,9829`, `48,6%`, `168,41 ms`).
   - *Trong Code Python & JSON:* Dùng dấu chấm `.` chuẩn kỹ thuật (VD: `0.9829`).
3. **Độ tin cậy trích dẫn (Citation Credibility):**
   - Mọi trích dẫn phải lấy từ nguồn khoa học uy tín (VISAPP, IEEE, Springer, arXiv tác giả gốc: Laroca 2021/2022, PaddlePaddle Team 2025, Ultralytics 2024).
   - Tuyệt đối không trích dẫn blog cá nhân không kiểm chứng hoặc tài liệu không rõ tác giả.
4. **Quy tắc Slide Pandoc:**
   - Cấp `##` cho mỗi slide (`--slide-level=2`).
   - Bảng hoặc Hình là khối **CUỐI CÙNG** của slide, chỉ có tối đa **1 bảng HOẶC 1 hình** mỗi slide.
   - Câu dẫn trên bảng/hình tối đa 3 dòng text để tránh đè khối trong PowerPoint.

---

## 💻 5. Quy Tắc Dự Phòng Demo Thực Chiến (Live Demo Fallback)

1. **Thư mục ảnh test ngoại tuyến (Offline Test Samples):** Chuẩn bị sẵn thư mục ảnh mẫu trên máy cục bộ gồm đủ các tình huống: biển 1 dòng dễ, biển 2 dòng chuẩn, biển nghiêng/mờ và biển có trường hợp lỗi đã phân tích.
2. **Video demo dự phòng (Fallback Video):** Luôn chuẩn bị sẵn 1 video ngắn (khoảng 60s) ghi lại thao tác chạy thực tế trên máy để phát ngay khi webcam, camera hoặc mạng hội trường gặp sự cố kết nối.

---

## 🛡️ 6. Nguyên Tắc Phản Biện Q&A (Defense Response Principle)

Khi trả lời câu hỏi phản biện của Hội đồng:
1. **Thừa nhận thẳng thắn:** Không vòng vo ngụy biện khi thầy cô chỉ ra điểm chưa hoàn hảo.
2. **Đưa số liệu đo thật:** Dùng số liệu đo đạc khách quan để chứng minh (*"Đúng là biển 2 dòng còn thấp, nhóm đã đo đạc độc lập và ghi nhận khoảng cách 25,4 điểm so với biển 1 dòng..."*).
3. **Chốt bằng Hướng phát triển:** Chuyển ngay sang giải pháp trong tương lai (*"Nhóm đã định vị nguyên nhân là do kiến trúc dòng đơn của CRNN và đã đưa hướng fine-tune riêng vào lộ trình phát triển..."*).

---

## 🔬 7. Bảo Toàn Tính Hợp Lệ Của Số Liệu

Đây là nhóm quy tắc đồ án trả giá nhiều nhất, tách riêng ra
[`.agents/rules/measurement-validity.md`](.agents/rules/measurement-validity.md).
Sáu điều cốt lõi:

1. **Công cụ đo phải đi qua đúng đường mã bản giao hàng đi** — lỗi này đã lặp
   **bốn lần**. Mọi mặc định của công cụ đo phải đọc từ cùng nguồn cấu hình với
   máy chủ thật, không gán cứng.
2. **Lượt đo có cảnh báo tải cạnh tranh thì bỏ, chạy lại trên máy rảnh.**
3. **Lật một kết luận thì phải có phép đối chứng**, không chỉ một lần đo mới.
   Nguyên nhân không xác định được thì ghi đúng là không xác định được.
4. **So sánh chỉ có nghĩa khi hai vế cùng đường đo** — cùng ngữ liệu, cấu hình,
   phiên bản mã.
5. **Đổi hằng số cũng phải đo lại**, và chỉ ra trước một **chỉ số phải đứng yên**
   làm chứng cho tính hợp lệ của phép so.
6. **Sửa nguồn → dựng lại → mới kiểm.** Kiểm trước khi dựng là kiểm nhầm bản cũ.

---

## 🔒 8. Kiểm Soát Chất Lượng & Bảo Mật (Quality Gate & Privacy)

Trước khi commit và push mã nguồn / tài liệu:
1. **Chạy test tự động:** Đảm bảo toàn bộ 530 unit tests AI vượt qua (`pytest tests/test_*.py`).
2. **Kiểm tra tham chiếu — CẢ HAI bản:** `python scripts/check_thesis_refs.py` và `python scripts/check_thesis_refs.py mon-hoc` đều phải đạt **0 tham chiếu chết, 0 đường dẫn ảnh hỏng**. Bản môn học từng thiếu hai hình suốt nhiều ngày vì chỉ bản chính được kiểm.
3. **Sửa slide thì dựng lại rồi mới kiểm:** sau khi sửa `docs/slides/*.md`, chạy `python scripts/build_thesis.py` (kèm `--slides ...` cho bộ tương ứng) **trước**, rồi `powershell -File scripts/check_slides.ps1` (0 lỗi). `check_slides.ps1` kiểm **bản dựng PPTX** — kiểm trước khi dựng là kiểm nhầm bản cũ và từng cho 0 lỗi trong khi thật ra có ba slide tràn.
4. **Bảo mật & Dữ liệu:** Không commit file `.env` chứa bí mật, file nén dataset nặng hoặc dữ liệu nhạy cảm vào Git.

---

## 🔁 9. Đồng Bộ Số Liệu Liên Tệp (Cross-File Sync Rules)

Bổ sung sau đợt kiểm toán 08/2026. Mỗi rule dưới đây gắn với một sự cố đã xảy ra
thật trong dự án — đọc ví dụ để hiểu vì sao rule tồn tại.

1. **Một số liệu — một nguồn (Single Source of Truth):**
   Mỗi chỉ tiêu NFR chỉ được trích từ **đúng một tệp JSON chuẩn**, khai báo trong
   bảng ánh xạ `NFR → tệp nguồn` đặt tại [`docs/reports/README.md`](docs/reports/README.md).
   Cấm trích cùng một chỉ tiêu từ tệp khác, kể cả khi giá trị "trông giống".
   *(Sự cố: số request soak R4 từng bị trích 4 cách — 185 · 1.684 · 3.928 · 2.028 —
   riêng 1.684 không khớp tệp JSON nào; NFR-P3 có ba giá trị 0,746× / 0,754× / 0,785×
   không ai xác định được giá nào chuẩn.)*
2. **Vòng đo mới = đồng bộ lan truyền theo checklist cố định:**
   Khi một vòng đo mới được chấp nhận làm hiện hành, bắt buộc rà theo đúng thứ tự:
   `README.md` → các báo cáo liên quan → Chương 4–6 **cả hai bản quyển** → 3 bộ slide +
   outline + defense-qa → dựng lại PPTX/PDF. Không tự đánh dấu "xong" nếu chưa đi hết.
   *(Sự cố gốc của đợt kiểm toán 08/2026: ba vòng đo kế tiếp sống chung trong tài liệu
   vì không ai có danh sách "phải sửa những gì" sau khi đổi nguồn số.)*
3. **Banner "số đã lỗi thời" có hạn sử dụng:**
   Mọi banner cảnh báo số cũ phải ghi **ngày lập** và **điều kiện gỡ** (VD: "gỡ khi
   `fill_chapter5.py` chạy lại từ nguồn mới"). Khi một vòng đo mới vào, banner của
   đợt *trước* phải được rà lại ngay — **banner chứa số đã bị bác bỏ là lỗi nghiêm
   trọng hơn cả thiếu banner**, vì nó giả danh "hiện tại".
   *(Sự cố: banner của `07-testing-report.md` ghi ô "hiện tại" = P2 ❌ 2,379 FPS —
   chính là con số đã bị bác bỏ trong báo cáo [38].)*
4. **Bộ slide là một đơn vị commit:**
   deck và kịch bản/hình đi kèm phải thay đổi **cùng một commit**. Trên nhánh
   `do-an-mon-hoc` chỉ còn `12-slides-mon-hoc.md` (+ hình từ
   `make_slide_figures.py`); bộ ĐATN (`10-slides.md` + `10-kich-ban-noi.md` +
   `10-defense-qa.md`) nằm trên `main`. Sửa deck mà bỏ kịch bản nói
   là để lại mâu thuẫn ngay trên sân bảo vệ.
   *(Sự cố: outline ghi siêu tham số "SGD, batch 16, lr0 0,01" trong khi Backup 5
   của chính deck đó ghi "AdamW, batch 8, lr0 0,001" — bản ghi đã thực thi.)*
5. **Đợt sửa quyển chỉ tính là XONG khi PDF đã xuất lại:**
   Sau mọi đợt sửa `.md` thuộc quyển: mở docx → Ctrl+A → F9 (cập nhật mục lục) →
   xuất PDF → chạy lại `copy_bundle()` để đồng bộ `nop/`. DOCX mới mà PDF cũ là
   trạng thái dở dang, không phải trạng thái hoàn thành.
   *(Sự cố: hai file PDF trong `nop/` lệch cả một ngày so với md trước khi bị phát hiện.)*
6. **Tag bản nộp là mốc khoá:**
   Sau khi đánh tag bản nộp (VD: `nop-2026-08-23`), mọi commit đụng tới nội dung
   đã nộp phải **kéo tag mới hoặc đánh tag hậu tố** — không để tag "bản nộp" trôi
   dần khỏi nội dung thật của nó. Tag cũ giữ nguyên như bằng chứng lịch sử.
