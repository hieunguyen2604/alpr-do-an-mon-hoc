# BỘ CÂU HỎI VÀ TRẢ LỜI PHẢN BIỆN (DEFENSE Q&A)
## ĐỒ ÁN MÔN HỌC: XỬ LÝ ẢNH VÀ ỨNG DỤNG

**Đề tài:** Hệ thống nhận dạng biển số xe Việt Nam hỗ trợ biển một dòng và hai dòng chạy trên CPU  
**Tài liệu tham chiếu:** Slide báo cáo môn học (`12-slides-mon-hoc.md`) & Quyển đồ án môn học  
**Cấu hình thực nghiệm:** Intel Core i5-14600K, 14 nhân / 20 luồng, suy luận thuần CPU  

---

## 📊 Bảng tra nhanh số liệu cốt lõi (Cheat Sheet)

| Tiêu chí / Hạng mục | Số liệu đo đạc | Mốc so sánh / Ngưỡng | Ý nghĩa & Đánh giá |
|---|:---:|:---:|---|
| **YOLO11n mAP@0,5** | **0,9829** | $\ge 0,90$ (Sàn: 0,85) | **Đạt** (Đo trên 1.514 ảnh Test v3, 1.611 đối tượng) |
| **YOLO11n mAP@0,5:0,95** | **0,7834** | $\ge 0,65$ (Sàn: 0,55) | **Đạt** (Hộp bao bám rất khít viền biển) |
| **Mức tăng nhờ Tách–ghép ngang (+Δ)** | **+34,92 pp** | $28,81\% \rightarrow 63,73\%$ | **Đột phá** lớn nhất toàn hệ thống (Đo trên 2.801 biển) |
| **Mức tăng nhờ Hậu xử lý vị trí (+Δ)** | **+13,28 pp** | $63,73\% \rightarrow 77,01\%$ | **Sửa đúng 372 biển, 0 ca làm sai lệch** |
| **Độ chính xác biển 1 dòng ($S_1$)** | **95,41%** | Mục tiêu: $\ge 90,0\%$ | **Vượt mục tiêu** (541 / 567 biển đúng hoàn toàn) |
| **Độ chính xác biển 2 dòng ($S_1$)** | **72,34%** | Mục tiêu: $\ge 85,0\%$ | **Chưa đạt** (1.616 / 2.234 biển; điểm nghẽn CRNN) |
| **Độ chính xác chuỗi tổng thể ($S_1$)** | **77,01%** | Mục tiêu: $\ge 90,0\%$ | Bình quân gia quyền (Biển 2 dòng chiếm 79,8% mẫu) |
| **Biển được cứu nhờ nắn phẳng (Deskew)** | **+34 biển** | Pass 1 trượt $\rightarrow$ Pass 2 đúng | Đánh đổi $+276,8\text{ ms}$ ở $p95$, trung vị $p50$ không đổi |
| **Độ trễ đầu cuối CPU ($p95$)** | **509,76 ms** | Mục tiêu: $\le 800\text{ ms}$ | **Đạt** (Sàn tối đa $1.500\text{ ms}$; trung vị $p50 = 150,07\text{ ms}$) |
| **Phân rã thời gian: PaddleOCR** | **60,8%** | $89,16\text{ ms} / 146,63\text{ ms}$ | Điểm nghẽn độ trễ do pipeline OCR tổng quát |
| **Phân rã thời gian: YOLO11n @ 640px** | **38,0%** | $55,66\text{ ms} / 146,63\text{ ms}$ | Suy luận phát hiện vùng biển trên CPU |
| **Phân rã thời gian: Xử lý ảnh & Regex** | **~0,0%** | $\approx 0,03\text{ ms}$ | Chi phí tính toán cực rẻ, tỉ lệ Lợi ích/Chi phí tối ưu |
| **Ngưỡng tỉ lệ khung hình (Aspect Ratio)** | **2,50** | $W/H < 2,5 \rightarrow$ 2 dòng | Dựa trên QCVN 08:2024 và phân tích sai lệch bất đối xứng |
| **Quy mô dữ liệu sạch (Split v3)** | **15.133 ảnh** | Tỉ lệ 70% / 20% / 10% | Khử 44,2% trùng lặp bằng pHash, triệt tiêu rò rỉ Train/Test |

---

## 🔴 PHẦN 1: 12 CÂU HỎI VỀ SỐ LIỆU CHƯA RÕ TRONG SLIDE

### 1. Các chỉ tiêu 0,90 / 0,85 / 0,92 / 800 ms lấy cơ sở từ đâu?
* **mAP@0,5 $\ge$ 0,90 (Bộ phát hiện):** Tham chiếu từ dải kết quả công bố của các công trình ALPR dùng YOLO thế hệ mới gần đây (*JAIC 2025, J-Cosine 2025, ETASR 2025* đạt từ 0,906 đến 0,995). Do bài toán là phát hiện 1 lớp đối tượng có độ tương phản cao, 0,90 là mức chuẩn mực phải đạt (sàn tối thiểu 0,85).
* **Đúng cả chuỗi thô $\ge$ 0,85 (Trước hậu xử lý):** Mốc chặn kỳ vọng đối với mô hình OCR (PP-OCRv5) khi chưa có tri thức miền Việt Nam, nhằm tạo mốc đối chứng đo định lượng mức tăng do khối hậu xử lý đem lại.
* **Đúng mức ký tự $(1 - \text{CER}) \ge$ 0,92 (Tối thiểu):** Biển số Việt Nam dài 8–9 ký tự. Xác suất chuỗi đúng tỉ lệ thuận với lũy thừa mức ký tự ($P \approx p^n$). Nếu $p < 0,92$ thì $0,90^8 \approx 0,43$ (hơn 50% chuỗi đọc ra bị sai). Ngưỡng $p \ge 0,92$ (mục tiêu 0,95) là điều kiện toán học tối thiểu để chuỗi thô giữ lại đủ ký tự đúng làm mỏ neo cho bộ luật sửa lỗi.
* **Độ trễ một ảnh p95 $\le$ 800 ms (trên CPU):** Được tính từ **phân rã ngân sách phần cứng CPU-only** (không có GPU):
  $$\text{Giải mã/Tiền xử lý (50 ms)} + \text{YOLO11n (150 ms)} + \text{Tiền xử lý cắt (30 ms)} + \text{PaddleOCR (120 ms)} + \text{Ghi DB (50 ms)} \approx 405\text{ ms}$$
  Ngân sách 800 ms (sàn tối đa 1.500 ms) để lại **hệ số an toàn gần $2\times$** để dự phòng biến động tải CPU và ảnh có nhiều biển số.

---

### 2. 15.133 ảnh sau khi khử trùng lặp được chia Train / Validation / Test như thế nào?
* **Làm sạch dữ liệu:** Từ 27.111 ảnh thu thập từ 7 bộ dữ liệu công khai, thuật toán băm tri giác pHash 64-bit + băm đa chỉ mục ở ngưỡng Hamming 10 đã loại bỏ $11.978$ ảnh trùng lặp ($44,2\%$), còn lại **15.133 ảnh**.
* **Phân chia tỉ lệ 70 / 20 / 10:**
  * **Train:** 10.592 ảnh (70%)
  * **Validation:** 3.027 ảnh (20%)
  * **Test:** 1.514 ảnh (10%)
* **Cơ chế chống rò rỉ (Leakage Prevention):** Không chia ngẫu nhiên từng ảnh (gây rò rỉ 9.126 cặp gần trùng giữa Train và Test ở bản v2 cũ). Hệ thống gom các ảnh gần trùng ở ngưỡng 10 thành các **nhóm liên thông (connected components)** và chia **theo cả cụm**. Mọi ảnh trong cùng một cụm bắt buộc nằm trọn trong cùng một tập con. Kết quả: ở bản v3, số cặp rò rỉ xuyên tập ở ngưỡng 10 đã giảm triệt để về **0 cặp**.

---

### 3. mAP@0.5 = 0,9829 được đo trên tập nào và bao nhiêu ảnh?
* **Tập đo:** Đo trên **tập Test v3 độc lập** gồm **1.514 ảnh** (chứa **1.611 đối tượng biển số**, gồm 286 biển 1 dòng và 1.325 biển 2 dòng).
* **Mô hình & Thiết lập:** Mô hình bàn giao `best.pt` (YOLO11n, input 640 px, train 20 epoch trên split v3) tại ngưỡng tin cậy tiêu chuẩn $\text{conf} = 0,25$, $\text{IoU} = 0,5$.
* **Chỉ số đi kèm:** $\text{mAP@0,5} = \mathbf{0,9829}$; $\text{mAP@0,5:0,95} = \mathbf{0,7834}$; $\text{Precision} = \mathbf{0,9837}$; $\text{Recall} = \mathbf{0,9714}$.
* **Điểm nhấn bảo vệ:** mAP@0,5 cao là do bài toán 1 lớp tương phản cao. Chỉ số thực sự phản ánh chất lượng là **mAP@0,5:0,95 đạt 0,7834** (vượt xa mục tiêu 0,65), chứng minh hộp bao bám rất khít viền biển số thật.

---

### 4. +34,92 percentage points của Split & Merge được tính từ accuracy trước và sau là bao nhiêu?
* **Trước khi tách–ghép (Tắt Split & Merge):** Để nguyên ảnh 2 dòng đưa vào PaddleOCR $\rightarrow$ Độ chính xác chuỗi chỉ đạt **28,81%** (mô hình CRNN/CTC bị sụp đổ căn chỉnh dòng đơn điệu).
* **Sau khi tách–ghép (Bật Split & Merge):** Cắt đôi theo phương ngang và ghép thành 1 dải ảnh dài $\rightarrow$ Độ chính xác tăng vọt lên **63,73%**.
* **Mức cải thiện:** $63,73\% - 28,81\% = \mathbf{+34,92\text{ điểm phần trăm (pp)}}$ (Đo trên cùng tập 2.801 biển số Việt Nam).

---

### 5. +13,28 pp của Post-processing được tính như thế nào?
* **Trước hậu xử lý ($S_0$):** Chuỗi ký tự thô do PaddleOCR đọc ra đạt **63,73%** (đúng hoàn toàn $1.785 / 2.801$ biển).
* **Sau hậu xử lý ($S_1$):** Sau khi áp dụng bộ luật theo vị trí từ TT 79/2024 (kiểm tra 81 mã tỉnh, mặt nạ vị trí `DDLDDDDD` / `DDL?DDDDD`, bảng ánh xạ nhầm lẫn bất đối xứng) $\rightarrow$ Độ chính xác đạt **77,01%** (đúng hoàn toàn $2.157 / 2.801$ biển).
* **Mức tăng:** $S_1 - S_0 = 77,01\% - 63,73\% = \mathbf{+13,28\text{ điểm phần trăm}}$, tương ứng **sửa đúng thêm 372 biển số** từ sai thành đúng.

---

### 6. "+34 biển được cứu" nghĩa chính xác là gì? Tiêu chí một biển được gọi là "cứu" là gì?
* **Bối cảnh:** Nằm trong **Cơ chế thử lại đa tầng (Fallback Ladder)** ở khâu xử lý ảnh vùng biển.
* **Tiêu chí "được cứu":**
  1. Ở lần đọc đầu (Pass 1 - vùng cắt chữ nhật chuẩn): Chuỗi ký tự trả về **không khớp biểu thức chính quy (Regex)** của TT 79/2024 (do biển bị chụp nghiêng, méo phối cảnh hoặc biến dạng).
  2. Hệ thống mở cổng thử lại (Pass 2): Thực hiện **hiệu chỉnh góc nghiêng (Deskew bằng `minAreaRect`)** kết hợp giãn dọc tỉ lệ rồi cho OCR đọc lại.
  3. Kết quả lần 2: Chuỗi nhận dạng trở nên **khớp chính xác 100% với nhãn thật (Ground Truth)**.
* Thống kê đo đạc độc lập ghi nhận cơ chế này cứu thêm **đúng 34 biển số**. Cơ chế chỉ chạy khi lần 1 thất bại nên trung vị $p50$ không bị ảnh hưởng ($~405\text{ ms}$), chỉ dồn chi phí tính toán vào đuôi $p95$ ($+276,8\text{ ms}$).

---

### 7. 95,41% và 72,34% là metric gì, được tính trên bao nhiêu mẫu?
* **Metric:** **$S_1$ — Độ chính xác toàn chuỗi sau hậu xử lý (Full-string exact match accuracy)**, yêu cầu toàn bộ các ký tự trong biển số phải khớp hoàn toàn 100% với Ground Truth.
* **Số mẫu đánh giá (Bảng 4.5 trong quyển đồ án):**
  * **95,41%:** Đo trên **567 mẫu biển một dòng** ($541 / 567$ biển đúng).
  * **72,34%:** Đo trên **2.234 mẫu biển hai dòng** ($1.616 / 2.234$ biển đúng).
  *(Tổng cộng tập kiểm thử OCR là 2.801 biển có nhãn chuỗi).*

---

### 8. Tại sao full-string tổng thể là 77,01% trong khi biển một dòng 95,41% và hai dòng 72,34%?
* Vì con số tổng thể là **trung bình có trọng số (weighted average)** theo phân bố mẫu thực tế:
  $$\text{Tổng thể} = \frac{567 \times 95,41\% + 2.234 \times 72,34\%}{567 + 2.234} = \frac{541 + 1.616}{2.801} = \frac{2.157}{2.801} \approx \mathbf{77,01\%}$$
* **Nguyên nhân lệch:** Biển hai dòng (xe máy, ô tô vuông) chiếm tới **79,76%** tổng số mẫu trong tập kiểm thử ($2.234 / 2.801$), trong khi biển một dòng chỉ chiếm **20,24%**. Tỉ trọng áp đảo của biển hai dòng đã kéo con số bình quân sát về mức $72,34\%$.

---

### 9. "0 ca sửa sai" của Post-processing nghĩa chính xác là gì?
* **Ý nghĩa:** Trong toàn bộ 2.801 biển kiểm thử, **không có bất kỳ trường hợp nào mà chuỗi ký tự ban đầu vốn đang đúng (khớp Ground Truth) lại bị bộ luật hậu xử lý sửa thành sai** ($0\text{ degradation cases}$).
* **Cơ chế kỹ thuật đảm bảo (Nguyên tắc Regex-First):**
  1. Nếu chuỗi OCR thô ban đầu đã khớp hoàn toàn với cấu trúc hợp lệ của biển số Việt Nam $\rightarrow$ **thuật toán bỏ qua ngay, tuyệt đối không can thiệp**.
  2. Chỉ khi chuỗi vi phạm cú pháp, bộ luật mới áp dụng ánh xạ an toàn theo vị trí (mặt nạ ký tự).
  Do đó, khối hậu xử lý là một hàm biến đổi **đơn điệu không giảm** về độ chính xác.

---

### 10. Tại sao phân loại biển 1 dòng / 2 dòng bằng aspect ratio? Ngưỡng aspect ratio là bao nhiêu và lấy từ đâu?
* **Tại sao dùng tỉ lệ khung hình (Aspect Ratio - AR):**
  * Tỉ lệ $W/H$ là đặc trưng hình học có chi phí tính toán $O(1)$, tính ngay từ hộp bao YOLO mà **không tốn thêm tài nguyên CPU** để chạy mô hình nơ-ron phân loại.
  * Kích thước vật lý quy định tại QCVN 08:2024/BCA phân tách hai nhóm rất rõ rệt:
    * Ô tô biển dài (1 dòng): $520 \times 110\text{ mm} \rightarrow \text{AR} \approx \mathbf{4,727}$.
    * Ô tô biển vuông (2 dòng): $330 \times 165\text{ mm} \rightarrow \text{AR} = \mathbf{2,000}$.
    * Mô tô / xe máy (2 dòng): $190 \times 140\text{ mm} \rightarrow \text{AR} \approx \mathbf{1,357}$.
* **Ngưỡng AR:** Được chọn là **2,50**.
* **Nguồn gốc:** Đây là **đề xuất kỹ thuật của đề tài dựa trên quan sát thực nghiệm và phân tích chi phí sai lệch bất đối xứng**, không phải số trong luật:
  * Đáy trũng giữa hai phân phối quan sát được trong dữ liệu nằm ở khoảng $2,2$ – $2,6$.
  * Ngưỡng được đặt lệch hẳn về phía 2 dòng ($2,5$ thay vì trung điểm $3,35$) vì: nếu nhận nhầm biển 1 dòng thành 2 dòng, đường ống tách-ghép vẫn xử lý êm (chỉ cắt đôi dải ký tự rồi ghép lại, OCR vẫn đọc được). Ngược lại, nếu nhận nhầm biển 2 dòng thành 1 dòng, ảnh 2 dòng đưa thẳng vào CRNN sẽ khiến nhận dạng sụp đổ hoàn toàn.

---

### 11. 60,8% latency của PaddleOCR được đo như thế nào? 39,2% còn lại nằm ở đâu?
* **Cách đo 60,8% (89,16 ms):** Đo bằng cách cô lập thời gian chạy suy luận OCR trên vùng biển đã cắt trong vòng lặp benchmark nội bộ. PaddleOCR chiếm tỷ trọng lớn nhất vì bản chất nó là đường ống nhiều giai đoạn (Text Detection $\rightarrow$ Direction Classifier $\rightarrow$ Recognition) được thiết kế cho văn bản tài liệu tổng quát.
* **39,2% còn lại phân bổ ở đâu (tổng thời gian suy luận 146,63 ms):**
  * **38,0% (55,66 ms):** Thuộc về **mô hình phát hiện YOLO11n @ 640px** chạy trên CPU.
  * **1,2% (1,78 ms):** Khâu **giải mã ảnh đầu vào và tiền xử lý** (OpenCV decode, resize, chuẩn hóa mảng).
  * **~0,0% (~0,03 ms):** Toàn bộ các bước xử lý ảnh (CLAHE, Bilateral Filter, Tách-Ghép) và khối Hậu xử lý Regex/Bảng luật theo vị trí thực thi cực kỳ nhẹ, chiếm xấp xỉ **0,0% ngân sách CPU**.

---

### 12. 39 ảnh demo có expected.json có nằm trong dataset đánh giá hay không?
* **KHÔNG.** 39 ảnh trong thư mục `demo/` là tập mẫu độc lập, **hoàn toàn không nằm trong tập Test 1.514 ảnh hay tập 2.801 biển OCR đánh giá**.
* **Đặc điểm:** Được chọn lọc thủ công từ nhiều nguồn thực tế (Wikimedia Commons, ảnh đường phố, xe tải, xe buýt, xe quân đội, ngoại giao, biển vàng và cả ảnh âm tính không có biển số).
* **Mục đích của bộ dữ liệu này:**
  1. Làm **dữ liệu dự phòng chiếu thực tế (Live Demo Fallback)** khi mạng hội trường hoặc camera gặp sự cố.
  2. Làm bộ **kiểm thử hồi quy tự động (Regression Smoke Test)** bằng kịch bản `python scripts/demo_test.py` trước khi báo cáo để đảm bảo mã nguồn không bị lỗi runtime.
  3. Tệp `expected.json` là bản ghi chụp lại hành vi đầu ra thực tế của hệ thống bàn giao (chứa cả các mảnh rác bị bắt nhầm hoặc ô trống), dùng để kiểm chứng tính toàn vẹn của mã nguồn chứ không phải nhãn Ground Truth để tính toán độ chính xác của đề tài.

---

## 🟡 PHẦN 2: CÁC CÂU HỎI KỸ THUẬT & PHẢN BIỆN MỞ RỘNG

### 13. Em ghép các thư viện có sẵn, vậy đóng góp thực sự của đề tài là gì?
* **Trả lời:** Đóng góp nằm ở **tầng giữa (Xử lý ảnh & Hậu xử lý)** giúp kết nối 2 mô hình học sâu chạy tối ưu trên CPU:
  * Biến đổi ảnh đầu vào khớp giả định mô hình (Tách-ghép mang lại mức tăng **+34,92 điểm**).
  * Bộ luật hậu xử lý theo vị trí mã hóa TT 79/2024 mang lại mức tăng **+13,28 điểm** (sửa đúng 372 biển, 0 ca sửa sai).
  * Thiết kế hệ thống đo đạc độc lập để định lượng giá trị của từng khâu can thiệp.

### 14. Tại sao dùng CLAHE và Lọc song phương (Bilateral) thay vì cân bằng sáng thông thường và Gaussian Blur?
* **Trả lời:**
  * **CLAHE:** Cân bằng sáng cục bộ và giới hạn độ dốc tương phản (Clip Limit = 2,0), không bị khuếch đại nhiễu trắng ở các vùng biển bị chói đèn pha/lóa sáng như HE thông thường.
  * **Lọc song phương:** Kết hợp trọng số không gian và trọng số cường độ sáng, làm mịn bề mặt biển bám bụi nhưng **bảo toàn sắc nét viền cạnh của ký tự** (Gaussian làm nhòe luôn nét chữ).

### 15. Phân loại màu biển (Trắng, Vàng, Xanh, Đỏ) bằng HSV thế nào khi biển bị bám bẩn hoặc chói sáng?
* **Trả lời:**
  * **Không gian HSV:** Tách biệt kênh màu sắc ($H$) khỏi kênh độ sáng ($V$) $\rightarrow$ màu sắc ổn định khi xe đi dưới bóng râm hoặc nắng gắt.
  * **Mặt nạ loại trừ nét chữ:** Chỉ lấy mẫu màu tại các pixel nền, loại bỏ các pixel thuộc biên nét chữ (tương phản cao) để tránh sai lệch màu trung bình.

### 16. Nếu tiếp tục phát triển đề tài, em sẽ ưu tiên cải tiến điểm nào đầu tiên?
* **Trả lời:**
  * **Huấn luyện mô hình OCR chuyên biệt cho biển 2 dòng:** Theo định luật Amdahl, OCR chiếm tới **60,8%** thời gian và là nguồn gây ra **23,07 điểm thâm hụt** trên biển 2 dòng.
  * **Lượng tử hóa INT8 / OpenVINO:** Tối ưu hóa tập lệnh vector AVX trên CPU Intel, kéo độ trễ $p95$ xuống dưới 200 ms.
