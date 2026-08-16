# Quy Tắc Bám Sát Thực Tế, Chống Lan Man & Tránh Overthinking

Tài liệu này là quy chuẩn bắt buộc cho mọi hoạt động tạo mã nguồn, chỉnh sửa tài liệu và soạn thảo slide trong dự án ALPR.

---

## 1. Nguyên Tắc "Zero-Fluff" (Chống Viết Lan Man)

1. **Đi thẳng vào trọng tâm (Get to the point):**
   - Trả lời trực diện câu hỏi, nêu giải pháp trước, giải thích lý do sau.
   - Tuyệt đối không sao chép lại toàn bộ lý thuyết sách giáo khoa đại cương (như lịch sử AI từ 1950, phép toán tích chập cơ bản dài dòng). Chỉ giải thích **cơ chế áp dụng trực tiếp** vào hệ thống (tại sao chọn YOLO11n, tại sao dùng PP-OCRv5 Mobile, tại sao cần ngưỡng Aspect Ratio 2.5).
2. **Số liệu dựa trên sự thật (Fact-based only):**
   - Mọi con số (mAP, độ trễ ms, RAM, FPS, số lượng ảnh, số lượng mẫu lỗi) **bắt buộc** phải trích xuất từ các file đo đạc thực tế trong `docs/reports/*.json`.
   - Tuyệt đối **không tự bịa số**, không ước lượng cảm tính (*"khoảng vài chục ms"*, *"rất chính xác"*).
3. **Câu từ súc tích:**
   - Mỗi câu mang một thông tin rõ ràng. Cắt bỏ các từ đệm sáo rỗng (*"như chúng ta đã biết"*, *"vô cùng vượt trội"*, *"tuyệt đối tối ưu"*).
   - Trong slide: Tối đa 3–5 bullet/slide, 5–10 từ/bullet. Không viết nguyên cả đoạn văn lên slide chiếu.

---

## 2. Nguyên Tắc "Anti-Overthinking" (Tránh Phức Tạp Hóa Vấn Đề)

1. **Tôn trọng ranh giới phạm vi đề tài (Scope Boundaries):**
   - Đề tài tập trung giải quyết: **Nhận dạng biển số xe Việt Nam (1 dòng & 2 dòng) suy luận tối ưu trên CPU**.
   - Các hạng mục **ngoài phạm vi** đã chốt:
     - ❌ Không làm Tracking xe nhiều camera / Barie tự động.
     - ❌ Không làm Phân loại dòng xe / Hãng xe.
     - ❌ Không tự huấn luyện OCR từ đầu (chỉ fine-tune hoặc dùng pre-trained PP-OCRv5 + Normalizer rule).
     - ❌ Không dựng hệ thống microservices phân tán phức tạp khi Clean Architecture 5 tầng nguyên khối dạng module hóa đã đủ đáp ứng NFR.
   - Khi được hỏi về các tính năng ngoài phạm vi $\rightarrow$ Nêu rõ đó là ranh giới ngoài phạm vi và chuyển sang **Hướng phát triển**, không tự ý vẽ thêm kiến trúc dở dang.
2. **Ưu tiên giải pháp đơn giản, hiệu quả và đo đạc được:**
   - Đạt tiêu chí kỹ thuật với tài nguyên tối thiểu (CPU, RAM thấp, không cần card GPU rời).
   - Không đưa vào các công nghệ thừa thãi nếu không có số liệu chứng minh nó cải thiện độ chính xác hoặc độ trễ.
3. **Quy tắc hạng mục chưa hoàn thành (Unfinished Work Rule):**
   - Mọi tính năng, mô hình thử nghiệm hoặc ý tưởng **chưa hoàn thành / dở dang / chưa đo đạc đầy đủ** $\rightarrow$ **TUYỆT ĐỐI KHÔNG** đưa vào thân bài, các chương phân tích thiết kế hoặc nội dung slide chính.
   - Toàn bộ các hạng mục này **bắt buộc phải chuyển trọn vẹn sang mục "Hạn chế" và "Hướng phát triển"**.
   - Báo cáo và slide chính chỉ trình bày những gì **đã làm thật, đã chạy thật, đã đo đạc thật và có số liệu kiểm chứng**.

---

## 3. Bất Biến Kiến Trúc (Architecture Invariants)

1. **AI Engine (`ai/`):** Phải là **Python thuần 100%**. Cấm import FastAPI, Pydantic, SQLAlchemy hoặc các web dependencies vào thư mục `ai/`. Đảm bảo AI Engine có thể chạy độc lập qua CLI/test mà không cần dựng web server.
2. **Backend Gateway (`backend/`):** Đảm nhiệm vai trò Service Layer, chịu trách nhiệm validate dữ liệu Pydantic, kết nối CSDL và chuyển tiếp yêu cầu đến AI Engine.

---

## 4. Căn Cứ Pháp Lý Bắt Buộc

Mọi tài liệu, thuật toán và phân tích liên quan đến biển số Việt Nam phải tuân thủ đúng 3 văn bản:
1. **Thông tư 79/2024/TT-BCA** (Quy định cấu trúc biển số, seri, màu sắc).
2. **Thông tư 13/2025/TT-BCA** (Sửa đổi, bổ sung TT 79/2024).
3. **Thông tư 51/2025/TT-BCA** (Quy định danh mục 34 mã tỉnh thành mới sau sáp nhập).
4. **QCVN 08:2024/BCA** (Quy chuẩn kỹ thuật kích thước và tỉ lệ biển số xe).

> ⚠️ **Cấm tuyệt đối:** Không viện dẫn **Thông tư 24/2023/TT-BCA** vì đã hết hiệu lực từ ngày 01/01/2025.
