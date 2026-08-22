# Khung slide và kịch bản bảo vệ đồ án tốt nghiệp (38 Slide)

**Đề tài:** Xây dựng hệ thống nhận dạng biển số xe Việt Nam ứng dụng Trí tuệ nhân tạo  
**Thuộc:** Phase 10 — chuẩn bị bảo vệ  
**Thời lượng trình bày chính:** 15 phút (S1–S31) + Phần Hỏi đáp Q&A (S32–S38)

---

## Cách dùng tài liệu này

Mỗi slide gồm bốn phần:

| Phần | Vai trò |
|---|---|
| **Nội dung trên slide** | Gạch đầu dòng ngắn — đây là thứ *chiếu lên*, không phải thứ *nói ra*. |
| **Hình / Bảng** | Tài nguyên minh hoạ trên slide. |
| **Speaker notes** | Kịch bản lời nói gợi ý (30–60 giây/slide). Không đọc lại slide. |
| **Thời lượng** | Ngân sách thời gian (giây). Tổng 31 slide chính = 900 giây (15 phút). |

### Ngân sách thời gian (31 Slide chính)

| Khối | Slide | Thời lượng |
|---|---|---:|
| Khối 1: Tổng quan & Đặc thù bài toán | S1–S8 | 240 s |
| Khối 2: Kiến trúc & Giải pháp AI | S9–S13 | 210 s |
| Khối 3: Dữ liệu & Hệ thống | S14–S17 | 150 s |
| Khối 4: Kết quả thực nghiệm & Đánh giá | S18–S26 | 210 s |
| Khối 5: Demo, Hạn chế & Kết luận | S27–S31 | 90 s |
| **Tổng 31 Slide chính** | | **900 s = 15 phút** |
| Khối Backup: Q&A phản biện | S32–S38 | Chiếu khi hỏi đáp |

---

# PHẦN A — TỔNG QUAN & ĐẶC THÙ BÀI TOÁN

## S1 — Bìa

**Nội dung trên slide**
- Tên đề tài: **Xây dựng hệ thống nhận dạng biển số xe bằng Trí tuệ nhân tạo**
- Sinh viên thực hiện: Phạm Công Thành — 25410013 · Nguyễn Minh Hiếu — 25410007
- Giảng viên hướng dẫn: ThS. Cáp Phạm Đình Thăng
- Trường Đại học Công nghệ Thông tin, ĐHQG-HCM

**Speaker notes** *(20 s)*
> Em xin kính chào Thầy/Cô trong Hội đồng. Em là Nguyễn Minh Hiếu, cùng bạn Phạm Công Thành xin đại diện nhóm trình bày đồ án tốt nghiệp: "Xây dựng hệ thống nhận dạng biển số xe bằng Trí tuệ nhân tạo" dưới sự hướng dẫn của ThS. Cáp Phạm Đình Thăng.

---

## S2 — Nội dung trình bày

**Nội dung trên slide**
1. **Tổng quan đề tài**
2. **Cơ sở lý thuyết**
3. **Phân tích và thiết kế hệ thống**
4. **Kết quả thực nghiệm**
5. **Kết luận và hướng phát triển**

**Speaker notes** *(15 s)*
> Nội dung báo cáo hôm nay gồm 5 phần chính: Từ Đặt vấn đề, Cơ sở lý thuyết, Phân tích thiết kế hệ thống 5 tầng, Kết quả thực nghiệm đo đạc thực tế, cho đến Kết luận và Hướng phát triển.

---

## S3 — Vì sao đề tài này

**Nội dung trên slide**
- **~77 triệu xe máy** — **85–90%** lưu lượng đường bộ Việt Nam
- Cùng hệ thống, cùng phép đo: **chênh 48,6 điểm** *(số liệu RodoSol Brazil)*
- Biểu đồ khoảng cách 1 dòng vs 2 dòng

**Speaker notes** *(40 s)*
> Tại Việt Nam, xe máy chiếm từ 85 đến 90% lưu lượng giao thông với hơn 77 triệu xe. Tuy nhiên, các hệ thống ALPR thương mại hiện nay gặp một điểm gãy lớn: khi đo trên cùng một hệ thống và điều kiện, độ chính xác đọc biển 1 dòng ô tô đạt 94,3%, nhưng biển 2 dòng xe máy sụt xuống 45,7% — lệch tới 48,6 điểm. Đồ án này tập trung giải quyết nút thắt biển 2 dòng tại Việt Nam.

---

## S4 — Căn cứ pháp lý: một phát hiện

**Nội dung trên slide**
- TT 24/2023/TT-BCA đã hết hiệu lực từ 01/01/2025
- **TT 79/2024/TT-BCA** — Cấu trúc biển, seri, màu sắc
- **TT 51/2025/TT-BCA** — Thay phụ lục mã tỉnh (34 tỉnh/thành mới)
- **QCVN 08:2024/BCA** — Kích thước và tỉ lệ khung hình

**Speaker notes** *(35 s)*
> Một điểm quan trọng là căn cứ pháp lý. Đề bài ban đầu dẫn Thông tư 24/2023, nhưng văn bản này đã hết hiệu lực từ đầu năm 2025. Hệ thống của nhóm được xây dựng chuẩn xác theo 3 văn bản đang có hiệu lực mới nhất: Thông tư 79/2024, Thông tư 51/2025 (phụ lục 34 tỉnh thành) và Quy chuẩn QCVN 08:2024 của Bộ Công an.

---

## S5 — Đặc thù biển số Việt Nam

**Nội dung trên slide**
- Bố cục tách bạch theo **tỉ lệ khung hình** *(QCVN 08:2024/BCA)*
- Tỉ lệ đo thật lệch khỏi chuẩn nhưng vẫn đúng phía ngưỡng **2,5**
- Hình ảnh minh hoạ phân loại 1 dòng vs 2 dòng

**Speaker notes** *(30 s)*
> Dựa trên QCVN 08:2024, biển số Việt Nam phân loại rõ ràng qua tỉ lệ khung hình (Aspect Ratio): biển 1 dòng có tỉ lệ chiều dài/chiều cao lớn hơn 2,5; trong khi biển 2 dòng vuông có tỉ lệ dưới 2,5. Ranh giới này giúp hệ thống phân loại bố cục chính xác ngay từ bước phát hiện.

---

## S6 — Chọn hướng tiếp cận

**Nội dung trên slide**
- Chọn hai giai đoạn: YOLO11n phát hiện vùng biển $\rightarrow$ PaddleOCR đọc ký tự
- Bảng so sánh 4 thế hệ (Cổ điển vs 2-stage vs 1-stage vs End-to-End Transformer)

**Speaker notes** *(40 s)*
> Về phương pháp, nhóm chọn kiến trúc Hai giai đoạn (2-Stage): YOLO11n phát hiện vùng biển và PaddleOCR đọc ký tự. Phương pháp cổ điển dễ vỡ khi đổi ánh sáng; phương pháp 1-stage thiếu dữ liệu nhãn ký tự Việt Nam; còn End-to-End Transformer quá nặng và đói dữ liệu, không phù hợp suy luận trên CPU.

---

## S7 — Lựa chọn mô hình: YOLO11n & PP-OCRv5 mobile

**Nội dung trên slide**
- Đánh đổi tối ưu cho mục tiêu **suy luận trên CPU** — nhẹ, nhanh, chính xác
- Bảng so sánh chi tiết YOLO11n (2,6M params) & PP-OCRv5 mobile (4,5 MB)

**Speaker notes** *(45 s)*
> Để hệ thống chạy hoàn toàn trên CPU không cần GPU CUDA: Nhóm chọn **YOLO11n** (2,6M tham số) cho tầng phát hiện vì mAP50 cao hơn YOLOv8n nhưng nhẹ hơn và trễ chỉ ~35ms; và chọn **PP-OCRv5 mobile** (4,5 MB) cho tầng OCR vì Tesseract/EasyOCR quá chậm trên CPU (2-3s/ảnh), còn bản PP-OCR Server thì nặng tới 100MB.

---

## S8 — Mục tiêu và phạm vi

**Nội dung trên slide**
- Hệ thống ALPR hoàn chỉnh: AI · API · Giao diện · CSDL · Docker
- Xử lý cả biển 1 dòng và 2 dòng trên CPU
- Ngoài phạm vi: tracking, barie, phân loại loại xe, huấn luyện OCR từ đầu

**Speaker notes** *(30 s)*
> Mục tiêu đề tài là xây dựng một hệ thống ALPR production-like hoàn chỉnh 5 tầng chạy mặc định trên CPU. Nhóm cũng xác định rõ ranh giới ngoài phạm vi (như tracking hay barie) để tập trung tối đa vào độ chính xác và hiệu năng cốt lõi.

---

# PHẦN B — PHÂN TÍCH & THIẾT KẾ HỆ THỐNG

## S9 — Kiến trúc 5 tầng

**Nội dung trên slide**
- Sơ đồ Kiến trúc 5 tầng Clean Architecture
- Tầng AI là Python thuần — cấm import FastAPI hoặc Pydantic

**Speaker notes** *(40 s)*
> Hệ thống thiết kế theo Clean Architecture 5 tầng độc lập. Đặc biệt, tầng AI Engine được viết bằng Python thuần, hoàn toàn không phụ thuộc vào tầng Web/FastAPI, giúp mô hình AI có thể tái sử dụng hoặc kiểm thử độc lập mà không cần dựng server.

---

## S10 — Pipeline AI

**Nội dung trên slide**
- Sơ đồ Pipeline AI toàn trình
- Nhánh đỏ là đóng góp kỹ thuật lõi
- Không thấy biển $\Rightarrow$ trả rỗng, HTTP 200

**Speaker notes** *(45 s)*
> Luồng xử lý AI đi từ Ảnh vào $\rightarrow$ YOLO11n phát hiện $\rightarrow$ Phân loại tỉ lệ khung hình. Nếu là biển 2 dòng, nhánh màu đỏ (đóng góp lõi của nhóm) sẽ kích hoạt thuật toán tách dòng `split-then-hstack`, sau đó đưa qua PaddleOCR, Bộ luật hậu xử lý theo vị trí và Bậc thang cứu chữa.

---

## S11 — Xử lý biển 2 dòng

**Nội dung trên slide**
- Thuật toán `split-then-hstack`
- Giả định một dòng nằm trong hàm mất mát CRNN/CTC — thêm dữ liệu không sửa được
- Sơ đồ minh hoạ cắt đôi dòng trên/dưới và ghép ngang

**Speaker notes** *(45 s)*
> Lý do biển 2 dòng bị đọc sai ở các hệ thống gốc là do hàm mất mát CRNN/CTC ngầm giả định văn bản nằm trên 1 dòng đơn. Nhóm giải quyết bằng thuật toán `split-then-hstack`: cắt đôi biển 2 dòng thành 2 dòng riêng biệt rồi ghép ngang thành 1 dải duy nhất cao 64px trước khi đưa vào bộ đọc OCR.

---

## S12 — Bộ luật hậu xử lý theo vị trí

**Nội dung trên slide**
- Sửa theo **VỊ TRÍ**, không sửa toàn cục — đóng góp kỹ thuật riêng
- Sơ đồ quy tắc vị trí tỉnh (2 số đầu), seri (chữ cái), và dãy số cuối

**Speaker notes** *(40 s)*
> Bộ luật hậu xử lý áp dụng quy tắc định dạng theo đúng vị trí pháp lý Việt Nam: 2 vị trí đầu bắt buộc là mã tỉnh (chỉ sửa số nhầm thành chữ, ví dụ `B` $\rightarrow$ `8`), vị trí seri bắt buộc là chữ cái, và các vị trí cuối là chữ số. Việc sửa theo vị trí giúp tăng +13,28 điểm mà không làm hỏng biển đang đúng.

---

## S13 — Bậc thang cứu chữa khi đọc hỏng

**Nội dung trên slide**
- Chỉ chạy **sau khi đọc hỏng**, chỉ nhận chuỗi **hợp lệ** $\Rightarrow$ không làm hỏng kết quả đúng
- Cứu dòng trên: **209 biển** · Nắn hình chống méo: **34 biển**

**Speaker notes** *(40 s)*
> Khi chuỗi đọc ra không hợp lệ, cơ chế Bậc thang cứu chữa (Rescue Ladder) sẽ tự động kích hoạt: thử cứu riêng dòng trên của biển 2 dòng hoặc nắn góc nghiêng/giãn dọc. Cơ chế này đã cứu thành công 209 biển 2 dòng bị mất nét dòng trên và 34 biển nghiêng méo.

---

# PHẦN C — DỮ LIỆU & HỆ THỐNG

## S14 — Bộ dữ liệu

**Nội dung trên slide**
- **15.133 ảnh · 15.977 khung** (chia 10.592 / 3.027 / 1.514)
- Hợp nhất 7 bộ công khai, loại 44,2% bản sao
- **Giảm rò rỉ theo pHash:** gom nhóm ảnh gần trùng ở ngưỡng Hamming 10; kiểm tra lại cùng ngưỡng cho 0 cặp Train–Test

**Speaker notes** *(40 s)*
> Tập dữ liệu gồm hơn 15.000 ảnh từ 7 nguồn công khai. Nhóm gom nhóm ảnh gần trùng bằng Perceptual Hashing ở ngưỡng Hamming 10 trước khi chia tập; phép kiểm tra rò rỉ chạy đúng tại chính ngưỡng đó nên cho 0 cặp Train–Test — kết quả này tất yếu theo cấu tạo, nhóm nói rõ điều đó thay vì lấy làm bằng chứng độc lập. Kiểm ngoài vùng bảo vệ (khoảng cách Hamming 12) còn 791 cặp vắt qua ranh giới train–test; món nợ khép kín duy nhất là đánh giá xuyên bộ dữ liệu.

---

## S15 — Huấn luyện

**Nội dung trên slide**
- **YOLO11n**, `imgsz 640`, 20 epoch, seed cố định
- Huấn luyện và suy luận đều trên CPU (hết 10,1 giờ)
- Biểu đồ đường cong huấn luyện hội tụ

**Speaker notes** *(35 s)*
> Mô hình YOLO11n được huấn luyện với `imgsz 640`, 20 epoch hoàn toàn trên CPU trong 10,1 giờ. Các đường cong loss (box, cls, dfl) hội tụ mượt mà và mAP50 đạt đỉnh ổn định từ epoch thứ 15.

---

## S16 — Cơ sở dữ liệu — một cột làm nên đóng góp

**Nội dung trên slide**
- Lưu cả hai chuỗi `raw_ocr_text` và `plate_number` trên cùng một bản ghi
- Bảng cấu trúc bảng `detections` trong CSDL SQLite

**Speaker notes** *(35 s)*
> CSDL SQLite được thiết kế lưu song song cả `raw_ocr_text` (chuỗi thô từ OCR) và `plate_number` (chuỗi sau hậu xử lý). Việc lưu cả 2 cột này cho phép hệ thống đo đạc chính xác đóng góp thực tế của bộ luật hậu xử lý trên dữ liệu lịch sử.

---

## S17 — Giao diện

**Nội dung trên slide**
- Giao diện Web React/TypeScript đáp ứng đủ **4 trạng thái**: Chờ · Rỗng · Lỗi · Thành công
- Hình ảnh màn hình ứng dụng thực tế

**Speaker notes** *(30 s)*
> Giao diện người dùng được xây dựng bằng React và TypeScript, đảm bảo xử lý minh bạch đủ 4 trạng thái giao diện, cho phép tải ảnh, xử lý video bất đồng bộ và tra cứu lịch sử nhận dạng.

---

# PHẦN D — KẾT QUẢ THỰC NGHIỆM & ĐÁNH GIÁ

## S18 — Kết quả phát hiện — đạt cả 4 chỉ tiêu

**Nội dung trên slide**
- **mAP50 đạt 0,983** · **mAP50-95 đạt 0,783** (Đạt cả 4/4 chỉ tiêu)
- Bảng kết quả chi tiết tách theo biển 1 dòng và 2 dòng

**Speaker notes** *(45 s)*
> Ở tầng phát hiện, YOLO11n đạt kết quả xuất sắc: mAP50 đạt 0,983 (vượt mục tiêu 0,90) và mAP50-95 đạt 0,783. Đáng chú ý, độ chính xác phát hiện giữa biển 1 dòng (0,988) và 2 dòng (0,968) chỉ chênh 2 điểm, chứng tỏ tầng phát hiện không phải là nút thắt.

---

## S19 — Kết quả OCR

**Nội dung trên slide**
- Đúng từng ký tự: **0,9483** (🟡 Đạt ngưỡng tối thiểu)
- Đúng cả chuỗi sau hậu xử lý: **0,7701** (❌ Chưa đạt mục tiêu 0,85)
- Toàn bộ khoảng cách nằm ở biển 2 dòng: 0,7234 so với 0,9541 của biển 1 dòng

**Speaker notes** *(50 s)*
> Ở tầng nhận dạng OCR, nhóm công khai trung thực: Độ chính xác đúng từng ký tự đạt 94,83%, nhưng đúng cả chuỗi chỉ đạt 77,01% — chưa đạt mục tiêu 0,85. Phân tích sâu cho thấy toàn bộ khoảng cách này dồn vào biển 2 dòng xe máy (chỉ đạt 72,34%), trong khi biển 1 dòng ô tô đạt tới 95,41%.

---

## S20 — Khoảng cách nằm trọn ở biển 2 dòng

**Nội dung trên slide**
- Biểu đồ so sánh độ chính xác tách theo bố cục biển 1 dòng vs 2 dòng
- Cùng một hệ thống, cùng một phép đo

**Speaker notes** *(35 s)*
> Biểu đồ này thể hiện rõ bản chất bài toán: Trên cùng một hệ thống và phép đo, biển 1 dòng đạt 95,41% nhưng biển 2 dòng sụt xuống 72,34%. Việc tách bạch con số này giúp định vị chính xác điểm gãy nằm ở bộ đọc dòng đơn của PaddleOCR khi xử lý biển 2 dòng.

---

## S21 — Đóng góp của hậu xử lý — đo được bằng số

**Nội dung trên slide**
- Sửa đúng **372 biển**, làm hỏng **0 biển**
- Biểu đồ minh hoạ mức tăng độ chính xác trước và sau hậu xử lý

**Speaker notes** *(40 s)*
> Nhờ lưu vết cột `raw_ocr_text`, nhóm đo được đóng góp thực tế của Bộ luật hậu xử lý theo vị trí: sửa đúng 372 biển số từ sai thành đúng và không làm hỏng bất kỳ biển nào đang đúng, đưa độ chính xác từ 63,73% lên 77,01%.

---

## S22 — Ba can thiệp, một kết luận

**Nội dung trên slide**
- Thu hẹp khoảng cách 2 dòng từ **48,6 điểm** *(Laroca 2022)* xuống **23,07 điểm**
- Bảng thu hoạch từ 3 can thiệp kỹ thuật (+13,28 pt, rescue 209 biển, nắn hình 34 biển)

**Speaker notes** *(45 s)*
> Ba can thiệp bên ngoài mô hình nhận dạng đã giúp nâng độ chính xác từ 63,73% lên 77,01%, thu hẹp khoảng cách bố cục từ 48,6 điểm xuống 23,07 điểm. Dư địa xử lý bên ngoài đã mỏng đi rõ rệt, các lỗi còn lại do ký tự mờ chưa từng được OCR đọc ra.

---

## S23 — Hiệu năng trên CPU — Phân rã độ trễ

**Nội dung trên slide**
- Nút thắt nằm ở tầng đọc chữ PaddleOCR (**64,3%**)
- Bảng phân rã suy luận thuần: Detect **59,83 ms** (34,2%), OCR **112,55 ms** (64,3%), còn lại tiền/hậu xử lý ⇒ Tổng **175,24 ms** mỗi biển; E2E p50 = 406 ms

**Speaker notes** *(45 s)*
> Về hiệu năng trên CPU (i5-14600K), phân rã suy luận thuần cho thấy tầng OCR chiếm tới 64,3% thời gian (112,55 ms mỗi biển), trong khi YOLO11n chỉ tốn khoảng 60 ms. Độ trễ đầu-cuối p50 đạt 406 ms. Điều này chỉ ra hướng tối ưu hiệu năng tương lai là xuất mô hình OCR sang ONNX/OpenVINO để cắt đuôi độ trễ.

---

## S24 — Phân bố độ trễ — đuôi mới là chỗ tốn

**Nội dung trên slide**
- Biểu đồ phân bố độ trễ (Latency Distribution Curve)
- Độ trễ p95 = 1.143 ms (đạt ngưỡng sàn 1.500 ms)

**Speaker notes** *(30 s)*
> Phân bố độ trễ cho thấy đa số ảnh hoàn thành dưới 0,5 giây. Đuôi độ trễ p95 rơi vào 1.143 ms là do các ảnh bị đọc hỏng phải chạy qua các bậc thử lại của Rescue Ladder.

---

## S25 — Kiểm thử và triển khai

**Nội dung trên slide**
- **1.002/1.002 kiểm thử tự động** đạt · Bao phủ tầng nghiệp vụ **87,7%**
- Chạy stress test 15 phút: 2.028 requests, **0 lỗi**, 0 rò rỉ bộ nhớ
- `docker compose up` — **một lệnh** đóng gói hoàn chỉnh

**Speaker notes** *(40 s)*
> Hệ thống đạt 1.002 test cases tự động với độ bao phủ tầng nghiệp vụ 87,7%. Chạy thử nghiệm chịu tải 15 phút với 2.028 yêu cầu đạt tỉ lệ thành công 100%, không rò rỉ bộ nhớ, và đóng gói Docker chạy thật chỉ với 1 lệnh.

---

## S26 — Đối chiếu chỉ tiêu — bảng chốt hạ

**Nội dung trên slide**
- Bảng ma trận đối chiếu 7 nhóm chỉ tiêu chính (✅ Đạt mục tiêu · 🟡 Đạt ngưỡng tối thiểu · ❌ Chưa đạt)

**Speaker notes** *(45 s)*
> Bảng tổng kết đối chiếu 7 chỉ tiêu chính: Đạt mục tiêu ở Phát hiện (mAP 0,983), Thời gian thực (5,257 FPS — đo trước khi gỡ trang Webcam khỏi phạm vi), Độ tin cậy (100%) và Phần mềm; Đạt ngưỡng ở Đọc từng ký tự (94,83%) và Độ trễ p95 (1.143ms); Chưa đạt ở Đọc cả chuỗi biển 2 dòng.

---

# PHẦN E — DEMO, HẠN CHẾ & KẾT LUẬN

## S27 — Demo trực tiếp

**Nội dung trên slide**
- Bảng 3 bước demo trực tiếp trên máy thật: Ảnh ô tô 1 dòng $\rightarrow$ Ảnh xe máy 2 dòng $\rightarrow$ Video & Lịch sử

**Speaker notes** *(30 s)*
> Sau đây nhóm xin thực hiện Live Demo trực tiếp 3 tình huống trên hệ thống thật: Nhận dạng ảnh ô tô 1 dòng, ảnh xe máy 2 dòng và luồng xử lý video bất đồng bộ.

---

## S28 — Hạn chế

**Nội dung trên slide**
- Bảng phân tích 5 hạn chế và nguyên nhân gốc (Biển 2 dòng chưa đạt, số đầu-cuối 0,563 chưa đạt ngưỡng, 97,7% là biển trắng)

**Speaker notes** *(40 s)*
> Nhóm nhìn nhận thẳng thắn các hạn chế: Biển 2 dòng chưa đạt do bộ đọc OCR dòng đơn; chỉ số đầu-cuối đo trên ảnh toàn cảnh chỉ đạt 0,563, chưa đạt ngưỡng 0,82 — và nhãn của phép đo ấy do mô hình sinh chứ không phải người gán, nhóm nêu rõ chỗ đó; và tập dữ liệu chủ yếu là biển trắng, chưa đủ mẫu biển vàng, xanh hay ngoại giao.

---

## S29 — Hướng phát triển

**Nội dung trên slide**
- Ngắn hạn: Fine-tune bộ nhận dạng trên crop biển VN, gán nhãn chuỗi cho ảnh hiện trường
- Trung hạn: Đo tập test xuyên bộ dữ liệu, xuất ONNX/OpenVINO hạ độ trễ

**Speaker notes** *(35 s)*
> Hướng phát triển ngắn hạn là fine-tune bộ nhận dạng trên tập crop chuẩn và gán nhãn hiện trường; trung hạn là chuyển đổi mô hình sang ONNX/OpenVINO để rút ngắn 300ms độ trễ OCR.

---

## S30 — Kết luận

**Nội dung trên slide**
- Đã làm được: Hệ thống 5 tầng chạy thật, Docker 1 lệnh, mAP 0,983, +13,28 pt hậu xử lý
- Đóng góp học thuật: Tách bạch con số 1 dòng/2 dòng, quy trình đo tự phát hiện lỗi

**Speaker notes** *(40 s)*
> Tóm lại, đồ án đã giao hàng một hệ thống 5 tầng hoàn chỉnh chạy Docker. Đóng góp học thuật chính là việc đo đạc và chứng minh tách bạch ranh giới biển 1 dòng vs 2 dòng, cùng quy trình thực nghiệm tự phát hiện hạn chế của chính mình.

---

## S31 — Cảm ơn

**Nội dung trên slide**
- **Em xin cảm ơn Thầy/Cô đã lắng nghe.**
- **Em sẵn sàng nhận câu hỏi.**

**Speaker notes** *(15 s)*
> Em xin chân thành cảm ơn Thầy/Cô trong Hội đồng đã chú ý lắng nghe. Nhóm xin sẵn sàng nhận các câu hỏi phản biện từ Thầy/Cô.

---

# PHẦN F — SLIDE BACKUP KỸ THUẬT (Q&A PHẢN BIỆN)

## S32 — Backup 1 — Kiến trúc mô hình YOLO11

**Nội dung trên slide**
- Bảng chi tiết kiến trúc YOLO11n (C3k2, SPPF, C2PSA Attention, Anchor-free head, 2,6M params)

**Speaker notes (Dùng khi Hội đồng hỏi về kiến trúc YOLO11)**
> YOLO11n cải tiến bộ trích xuất đặc trưng với các block C3k2 và C2PSA tích hợp Attention, giúp bắt nét vùng biển số nghiêng tốt hơn YOLOv8, đồng thời duy trì quy mô cực nhẹ 2,6M params cho suy luận CPU.

---

## S33 — Backup 2 — Kiến trúc mô hình PP-OCRv5

**Nội dung trên slide**
- Bảng chi tiết kiến trúc PP-OCRv5 Mobile (PP-LCNetV3, SVTR-HG Transformer, CTC head, 4,5 MB)

**Speaker notes (Dùng khi Hội đồng hỏi về kiến trúc OCR)**
> PP-OCRv5 Mobile kết hợp backbone PP-LCNetV3 siêu nhẹ trên CPU với block SVTR-HG Gated-Attention Transformer để trích xuất thông tin ngữ cảnh chuỗi văn bản, giải mã qua CTC Head mà không cần nhãn từng vị trí ký tự.

---

## S34 — Backup 3 — Phân tích lỗi (Error Analysis)

**Nội dung trên slide**
- Bảng 6 loại lỗi loại trừ lẫn nhau trên 697 ca sai / 2.801 biển (24,88%): Nhầm ký tự E3 chiếm **63,85%**, Thiếu ký tự E4 **10,47%**, Thừa ký tự E5 **2,58%**, Sai thứ tự E6 = 0

**Speaker notes (Dùng khi Hội đồng hỏi về các case nhận dạng sai)**
> Trong 697 ca sai trên 2.801 biển, nhóm phân loại được 6 kiểu lỗi loại trừ lẫn nhau. Chiếm đa số là nhầm ký tự do hình dạng tương đồng (445 ca, 63,85%), kế đến là mất trọn nét một dòng của biển xe máy (73 ca). Riêng sai thứ tự ghép nửa trên/dưới là đúng bằng không — chứng tỏ thuật toán split-then-hstack luôn ghép đúng thứ tự đọc.

---

## S35 — Backup 4 — Bóc tách đóng góp kỹ thuật (Ablation Study)

**Nội dung trên slide**
- Bảng bóc tách đóng góp độc lập: Baseline 0,6373 $\rightarrow$ Pos-rules +13,28 pt $\rightarrow$ Rescue dòng trên 209 biển $\rightarrow$ Nắn góc 34 biển

**Speaker notes (Dùng khi Hội đồng hỏi về Ablation Study / Đóng góp từng phần)**
> Kết quả bóc tách chứng minh: Bộ luật hậu xử lý theo vị trí đóng góp +13,28 điểm; cơ chế Rescue dòng trên cứu 209 biển và nắn hình cứu 34 biển. Thử nghiệm fine-tune OCR trực tiếp bị sụt -7,5 điểm do lệch phân phối với bước dò chữ.

---

## S36 — Backup 5 — Siêu tham số & Biểu đồ huấn luyện

**Nội dung trên slide**
- Bảng siêu tham số (`imgsz 640`, `batch 8`, `epochs 20`, `lr0 0,001`, AdamW) và sự hội tụ của 3 hàm mất mát `box_loss`, `cls_loss`, `dfl_loss`

**Speaker notes (Dùng khi Hội đồng hỏi về siêu tham số & quá trình huấn luyện)**
> YOLO11n được huấn luyện với `imgsz 640`, `batch 8`, `lr0 0,001` dùng AdamW, momentum 0,937. Cả 3 hàm loss `box_loss` (giảm từ 0,642 xuống 0,315), `cls_loss` (0,812 $\rightarrow$ 0,204) và `dfl_loss` (0,911 $\rightarrow$ 0,412) đều hội tụ ổn định.

---

## S37 — Backup 6 — Tài liệu tham khảo chính

**Nội dung trên slide**
- Bảng trích dẫn các công trình tham chiếu chính (Laroca et al. 2021/2022, PP-OCR 2020/2025, Ultralytics YOLO11, TT 79, QCVN 08)

**Speaker notes (Dùng khi Hội đồng hỏi về nguồn trích dẫn)**
> Đây là các tài liệu khoa học và văn bản pháp lý nòng cốt chống đỡ cho các luận điểm trong bài, đầy đủ 232 mục trích dẫn nằm trong file BibTeX của đồ án.

---

## S38 — Backup 7 — Tra nhanh số liệu

**Nội dung trên slide**
- Bảng ma trận tổng hợp tra cứu siêu tốc mọi con số quan trọng của hệ thống (Dataset, Model, mAP50, Accuracy, Latency, Test Cases)

**Speaker notes (Dùng khi Hội đồng hỏi tra cứu lại con số bất kỳ)**
> Đây là bảng tra cứu tổng hợp toàn bộ thông số thực nghiệm của hệ thống để trả lời nhanh bất kỳ con số nào Thầy/Cô muốn làm rõ.
