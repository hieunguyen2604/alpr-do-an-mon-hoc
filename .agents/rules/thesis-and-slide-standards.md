# Quy Chuẩn Soạn Thảo Tài Liệu & Thiết Kế Slide

Tài liệu này quy định các tiêu chuẩn kỹ thuật khi chỉnh sửa các tệp tài liệu trong `docs/papers/` và slide trong `docs/slides/`.

---

## 1. Quy Chuẩn Trực Quan Hóa (Data & Workflow Visualization)

1. **Mọi so sánh BẮT BUỘC dùng BẢNG (Comparison $\rightarrow$ Table):**
   - So sánh giữa các mô hình (YOLO11 vs YOLOv8/Faster R-CNN), các engine OCR (PP-OCRv5 vs EasyOCR vs Tesseract), hoặc so sánh trước/sau can thiệp $\rightarrow$ **tuyệt đối không viết văn xuôi dài dòng**, phải kẻ bảng có cột đối chứng rõ ràng (Tiêu chí, Phương án A, Phương án B, Đánh đổi/Kết quả).
2. **Mọi luồng xử lý BẮT BUỘC dùng SƠ ĐỒ / DẢI HÌNH ẢNH (Pipeline & Workflow $\rightarrow$ Diagram/Strip):**
   - Kiến trúc hệ thống, chuỗi xử lý AI (Preprocess $\rightarrow$ YOLO $\rightarrow$ Crop $\rightarrow$ OCR $\rightarrow$ Normalizer), luồng xử lý 2 dòng $\rightarrow$ phải thể hiện bằng **sơ đồ khối hoặc dải ảnh minh họa đầu vào/đầu ra từng bước** (`fig-pipeline-strip.png`).
3. **Phân bố & Xu hướng BẮT BUỘC dùng BIỂU ĐỒ (Distribution/Trends $\rightarrow$ Chart):**
   - Biểu đồ phân bố độ trễ (Latency distribution), đường cong huấn luyện Loss/mAP, ma trận nhầm lẫn Confusion Matrix $\rightarrow$ dùng biểu đồ ảnh trực quan, không mô tả chay bằng lời.
4. **Bóc tách đóng góp (Ablation Study):**
   - Bắt buộc dùng bảng với 2 cột: **Mức cải thiện (+Δ metric)** và **Chi phí tính toán (+ms trễ)**.
5. **Không mục nào chỉ toàn chữ khi nó đang mô tả một CẤU TRÚC:**
   - Mục mô tả **kiến trúc, phân tầng, giao diện lớp, luồng xử lý, lược đồ CSDL,
     hay quan hệ giữa các thành phần** thì bắt buộc kèm **một sơ đồ hoặc một bảng**.
     Người đọc không dựng được hình trong đầu từ ba đoạn văn.
   - **Tiêu đề hứa gì thì phải có cái đó.** Mục tên chứa *"sơ đồ"*, *"lược đồ"*,
     *"kiến trúc"*, *"luồng"* mà không có hình hoặc bảng là lỗi — đã từng có mục
     tên *"Sơ đồ use case và ba use case chính"* nhưng bên trong không một sơ đồ nào.
   - **Mật độ tối thiểu cho chương kết quả:** trung bình **dưới 60 dòng cho mỗi
     hình hoặc bảng**. Chương thực nghiệm từng dài 423 dòng mà chỉ có đúng một
     hình, và hình đó là sơ đồ giao thức chứ không phải số liệu.

6. **Chuyển văn xuôi sang bảng là THAY, không phải THÊM:**
   - Sau khi dựng bảng, **xoá đoạn văn xuôi mà nó thay thế**. Lỗi này đã mắc
     **hai lần** trong cùng một đợt: §4.7.1 và §4.2.1 đều nói cùng một chuyện
     hai lần — một lần bằng văn xuôi, một lần bằng bảng ngay dưới.
   - **Trước khi xoá, đối chiếu bảng có giữ đủ ý không.** Lần đầu ở §4.7.1 bảng
     còn *nghèo hơn* văn xuôi: nó bỏ mất quy tắc giao dịch, phần ánh xạ cây
     ngoại lệ sang mã HTTP, và NFR-S4. Xoá văn xuôi lúc đó là mất nội dung thật.
   - Cách bắt: đoạn văn xuôi ngay trước một bảng mà chứa `(1)`, `Thứ nhất`,
     hoặc `Ba/Bốn/Tám …` **và dài trên 60 từ** là dấu hiệu lặp.

7. **Chú thích phải mô tả đúng hình ĐƯỢC VẼ RA, không phải hình đã hình dung:**
   - Trước khi nhúng, **mở ảnh ra nhìn**. Ba lỗi từng lọt qua vì chỉ đọc chữ:
     chú thích ghi *"mũi tên rỗng"* trong khi hình vẽ mũi tên đặc; ghi *"mũi tên
     thể hiện tác nhân khởi tạo"* trong khi hình vẽ đường nối không đầu; và một
     nhãn đè lên viền khung.
   - Đây là loại lỗi **không công cụ nào bắt được**: `check_thesis_refs.py` xác
     nhận tệp ảnh tồn tại, Pandoc dựng ra PDF bình thường, chỉ có người nhìn mới
     thấy chữ và hình nói hai chuyện khác nhau.

8. **Sơ đồ nên sinh từ mã nguồn, đừng vẽ tay:**
   - Ưu tiên đọc tên lớp, tên phương thức, tên cột trực tiếp từ mã hoặc từ lược
     đồ thật (ví dụ `scripts/make_ch4_diagrams.py` đọc `ai/inference/interfaces.py`;
     bảng lược đồ CSDL lấy từ `PRAGMA table_info`). Sơ đồ vẽ tay sẽ trôi khỏi mã
     mà không ai biết.
   - Máy này **không cài `mermaid-cli`**. Dùng `matplotlib` cho sơ đồ và biểu đồ
     mới; đừng thêm một hệ thị giác thứ hai vào quyển chỉ để vẽ một hình.

9. **Phân tích ca lỗi (Error Analysis):**
   - Bắt buộc có **ảnh cắt thực tế** kèm bảng đối chiếu: *Chuỗi nhãn thật (Ground Truth)* vs *Chuỗi nhận dạng được (Predicted)* vs *Nguyên nhân gốc*.

---

## 2. Quy Chuẩn Tài Liệu Báo Cáo & Trích Dẫn (Thesis & Citations)

1. **Văn phong học thuật:**
   - Sử dụng đại từ trung tính: **"Nhóm thực hiện"**, **"Đề tài này"**, **"Hệ thống"** hoặc thể bị động (*"Mô hình được huấn luyện...", "Thuật toán xử lý..."*).
   - Tuyệt đối không dùng *tôi, mình, em, chúng em*.
2. **Định dạng số liệu học thuật (Metric Formatting):**
   - Dùng **dấu phẩy `,`** cho số thập phân trong tiếng Việt (VD: `0,9829`, `48,6%`, `168,41 ms`).
   - Dấu chấm `.` chỉ dùng trong code Python, JSON hoặc câu lệnh kỹ thuật.
3. **Độ tin cậy trích dẫn (Citation Credibility):**
   - Chỉ trích dẫn từ nguồn học thuật được thẩm định (VISAPP, IEEE, Springer, arXiv tác giả gốc: Laroca, PaddleTeam, Ultralytics) và văn bản pháp lý chính thức (**TT 79/2024**, **TT 51/2025**, **QCVN 08:2024**).
   - Cấm trích dẫn blog cá nhân không kiểm chứng.
4. **Khai báo và định dạng:**
   - Mỗi chương bắt đầu bằng `#` (Heading 1).
   - **Bảng:** một dòng neo máy đọc `<!-- {{TN.M}} mô tả ngắn -->`, rồi chú thích `**Bảng N.M.** Tên bảng` ngay trên bảng.
   - **Hình:** `![](figures/ten-hinh.png)` rồi chú thích `**Hình N.M.** Mô tả` ngay dưới.
   - Không dùng cú pháp `Table: … {#tbl:}` hay `{#fig:}` của pandoc-crossref: kho hiện dùng 50 chú thích `**Bảng N.M.**` và 11 chú thích `**Hình N.M.**`, trộn hai hệ sẽ làm hỏng đánh số và danh mục.
5. **Hạng mục chưa hoàn thành:**
   - Tuyệt đối không đưa vào **Chương 4** (Thiết kế và cài đặt) hoặc **Chương 5** (Thực nghiệm và đánh giá).
   - Phải đưa trọn vẹn vào **Chương 6** — mục 6.2 Hạn chế và mục 6.3 Hướng phát triển.
6. **Kiểm tra chéo (Cross-references):**
   - Sau khi sửa tài liệu, luôn chạy: `python scripts/check_thesis_refs.py` (phải đạt 0 tham chiếu chết và 0 đường dẫn ảnh hỏng).

---

## 3. Quy Chuẩn Bất Di Bất Dịch Khi Soạn Slide (`docs/slides/*.md`)

1. **Cấu trúc Slide:**
   - Cố định phân cấp slide bằng `##` (`--slide-level=2`).
   - Mỗi slide chỉ truyền tải **1 ý chính**.
2. **Quy tắc Bảng & Hình ảnh:**
   - **Bảng hoặc Hình ảnh BẮT BUỘC là khối cuối cùng của slide.**
   - Mỗi slide **chỉ được có tối đa 1 bảng HOẶC 1 hình ảnh**. Không để cả hai trên cùng một slide (Pandoc sẽ tự cắt thành slide rác).
   - Mọi câu dẫn giải thích phải nằm **phía trên** bảng/hình.
3. **Quy tắc chống tràn chữ (Overflow & Overlap):**
   - Câu dẫn trên bảng/hình tối đa **3 dòng** text khi render. Nếu dài hơn, PowerPoint sẽ vẽ chữ đè lên bảng bên dưới.
4. **Kiểm tra định dạng Slide:**
   - Sau khi sửa file slide, phải chạy: `powershell -File scripts/check_slides.ps1` (đạt 0 lỗi tràn chữ).

---

## 4. Quy Tắc Dự Phòng Demo Thực Chiến (Live Demo Fallback)

1. **Chuẩn bị sẵn thư mục ảnh test ngoại tuyến:** Không phụ thuộc mạng Internet hay camera trực tiếp khi trình diễn trước Hội đồng.
2. **Video demo dự phòng (Fallback Video):** Video quay sẵn luồng nhận diện (60s) sẵn sàng kích hoạt nếu xảy ra sự cố phần cứng tại phòng bảo vệ.

---

## 5. Nguyên Tắc Trả Lời Phản Biện Q&A (Defense Response Principle)

1. **Thừa nhận thẳng thắn:** Không ngụy biện khi được hỏi về các điểm hạn chế.
2. **Chứng minh bằng số liệu đo thật:** Dẫn xuất số liệu từ `docs/reports/*.json`.
3. **Chốt bằng Hướng phát triển:** Chuyển sang giải pháp kỹ thuật cụ thể đã vạch ra trong lộ trình.
