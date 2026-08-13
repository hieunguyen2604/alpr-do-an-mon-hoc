# Bộ câu hỏi phản biện và câu trả lời — Bảo vệ đồ án tốt nghiệp

**Đề tài:** Xây dựng hệ thống nhận dạng biển số xe Việt Nam ứng dụng Trí tuệ nhân tạo
**Thuộc:** Phase 10 — chuẩn bị bảo vệ · **Ngày lập:** 19/07/2026

---

## Cách dùng tài liệu này

Mỗi câu gồm ba phần:

| Phần | Vai trò |
|---|---|
| **Trả lời ngắn** | 2–4 câu, nói được trong ~30 giây. Đây là thứ phải thuộc. |
| **Nếu bị hỏi sâu** | Số liệu và lập luận dự phòng. Chỉ dùng khi hội đồng hỏi tiếp. |
| **Cảnh báo** | Chỗ dễ trả lời hỏng, hoặc cách thừa nhận trung thực một điểm yếu. |

### Ba nguyên tắc trả lời

1. **Không bịa số.** Nếu chưa đo thì nói "chưa đo được, và đây là lý do". Hội đồng chấp nhận một khoảng trống được thừa nhận; không chấp nhận một con số bịa bị bắt tại chỗ.
2. **Mọi con số hiệu năng phải kèm phần cứng.** Công bố FPS mà không kèm cấu hình là lỗi phương pháp luận.
3. **Thừa nhận rồi chuyển hướng, không thừa nhận rồi im lặng.** Công thức: *"Đúng, chỗ này em chưa làm được vì [lý do kỹ thuật cụ thể]. Cái em làm được thay vào đó là [bằng chứng đo được]."*

### Bảng trạng thái thật — thuộc lòng bảng này

| Hạng mục | Trạng thái | Bằng chứng |
|---|---|---|
| Phase 0, 1 | ✅ Xong, chốt mốc M0, M1 | 7 tài liệu nghiên cứu, SRS 34 yêu cầu chức năng |
| Bộ dữ liệu detection (v3) | ✅ 15.133 ảnh / 6 nguồn, đã chia 10.592 / 3.027 / 1.514, khử trùng lặp ngưỡng 10 | `datasets/processed/yolo_v3/split_manifest.csv` |
| Huấn luyện detector | ✅ **Xong** — `models/best.pt` (YOLO11n, imgsz 640, split v3, 20 epoch) | `runs/final-640-v3/results.csv` |
| Kết quả detection (test v3) | ✅ mAP50 **0,983** / mAP50-95 **0,783** / P **0,984** / R **0,971** — đạt cả bốn | `05-tables.md §T5.5a` |
| Backend FastAPI | ✅ Chạy được — **10 endpoint** phản hồi đúng qua HTTP thật, Alembic migrate xong | `detection_history` 18 cột, `detection_job` 11 cột |
| Frontend React | ✅ Chạy được — typecheck sạch, lint sạch, build thành công, 10 endpoint kiểm chứng | **3 trang**: Nhận dạng ảnh *(trang chủ)* · Nhận dạng video · Lịch sử |
| Phạm vi giao diện | ⚠️ Thu gọn **2 lần** ngày 2026-07-20 — gỡ trang Webcam, rồi gỡ trang Tổng quan | MoSCoW nay: **21 Must · 6 Should · 3 Could · 4 Won't** (FR-3.1, FR-3.4, **FR-4.1**, FR-4.2). Xem **E4b, E4c** |
| Module OCR + tách 2 dòng + regex | ✅ Đã viết, 104 unit test | `ai/inference/`, `tests/` |
| Độ chính xác OCR (2.801 biển) | ⚠️ **Đã đo — KHÔNG đạt** (A4 0,873 / A5 0,610 / A6 0,656; biển 2 dòng yếu) | `05-tables.md §T5.6` |
| Docker | ⚠️ Có Dockerfile + compose, `docker compose config` hợp lệ, **chưa build thật** | `deployment/docker/` |
| Kiểm thử hiệu năng / chịu tải | ❌ Chưa làm (Phase 7) | — |

---

## A. Về bài toán và đóng góp

### A1. Đóng góp thực sự của em là gì? Cái này ghép thư viện có sẵn thôi mà?

**Trả lời ngắn.**
Thầy/cô nói đúng ở chỗ em không phát minh kiến trúc mạng mới — YOLO11 và PaddleOCR đều là công cụ có sẵn. Đóng góp của em nằm ở **tầng giữa**: bộ luật hậu xử lý theo vị trí ký tự xây từ Thông tư 79/2024/TT-BCA, cơ chế tách biển 2 dòng, và quan trọng nhất là **thiết kế phép đo để chứng minh chúng có tác dụng**. Em lưu cả `raw_ocr_text` lẫn `plate_number` trong cơ sở dữ liệu, nên hiệu số giữa độ chính xác trước và sau chuẩn hoá là một con số đo được, không phải một lời khẳng định.

**Nếu bị hỏi sâu.**
Bốn đóng góp cụ thể, mỗi cái đều kiểm chứng được:

| # | Đóng góp | Bằng chứng |
|---|---|---|
| 1 | **Bộ luật sửa lỗi OCR theo vị trí** — ép về chữ số ở vị trí số, ép về chữ cái ở vị trí seri, có vùng cấm sửa | `ai/inference/plate_rules.py`, 29 test trong `test_normalizer.py` |
| 2 | **Đo định lượng được đóng góp của hậu xử lý** — schema lưu cả chuỗi thô lẫn chuỗi đã chuẩn hoá (NFR-A5 vs A6) | `detection_history.raw_ocr_text` |
| 3 | **Đánh giá tách riêng biển 1 dòng / 2 dòng** thay vì một con số trung bình che mất điểm yếu | `evaluate.py` in bảng NFR-A8, tập test có 300 ảnh biển 2 dòng |
| 4 | **Hệ thống hoàn chỉnh chạy được** — 5 tầng, 10 endpoint, giao diện 3 trang, chạy không cần GPU | Backend + frontend đã kiểm chứng bằng HTTP thật |

**Cảnh báo.** Đừng trả lời "em tự train model nên đó là đóng góp". Fine-tune một model có sẵn trên một dataset có sẵn là công việc kỹ thuật chuẩn, không phải đóng góp học thuật. Đóng góp thật là **phép đo** và **bộ luật theo văn bản pháp lý**.

---

### A2. Đã có nhiều hệ thống ALPR rồi, em làm thêm để làm gì?

**Trả lời ngắn.**
Vì các hệ thống có sẵn hỏng đúng ở chỗ Việt Nam cần nhất. Trong nghiên cứu của Laroca và cộng sự (VISAPP 2022) trên bộ **RodoSol-ALPR của Brazil**, OpenALPR đạt 94,3% trên ô tô biển 1 dòng nhưng chỉ 45,7% trên xe máy biển 2 dòng — chênh 48,6 điểm trên cùng một hệ thống, cùng một tập kiểm thử cân bằng. Đây là số liệu Brazil, em dẫn như một *analogue định lượng* chứ không phải đo trên biển số Việt Nam; nhưng cơ chế gây lỗi là bố cục hai dòng nên hoàn toàn áp dụng được. Ở Việt Nam xe máy không phải trường hợp biên mà là trường hợp phổ biến nhất, nên một hệ thống nhập khẩu sẽ hỏng trên phần lớn phương tiện.

**Nếu bị hỏi sâu.**
- Nguồn con số: Laroca et al., VISAPP 2022 (arXiv 2201.00267).
- Nguyên nhân gốc không phải "model kém" mà là **giới hạn kiến trúc**: CRNN/CTC giả định alignment đơn điệu trên **một** dòng. Đưa ảnh 2 dòng vào thì mô hình không có cách nào biểu diễn đúng.
- Ngoài ra là phần **định dạng và pháp lý**: mã tỉnh, seri, quy tắc phân cách của biển Việt Nam nằm trong Thông tư 79/2024/TT-BCA và QCVN 08:2024/BCA — không hệ thống nước ngoài nào mã hoá những quy tắc này.

---

### A3. Vì sao không dùng model nước ngoài có sẵn?

**Trả lời ngắn.**
Em có dùng — YOLO11 pretrain trên COCO và PaddleOCR pretrain đều là model nước ngoài, và em dùng chúng làm nền. Cái em không dùng được là các **model ALPR đóng gói sẵn** vì chúng được huấn luyện trên định dạng biển của nước khác. Ví dụ ứng dụng biển số của chính PaddleOCR fine-tune trên CCPD — biển Trung Quốc 1 dòng, khác hoàn toàn biển xe máy Việt Nam.

**Nếu bị hỏi sâu.**
- Chứng cứ transfer learning vẫn có giá trị: COCO không có lớp "biển số", nhưng đặc trưng tầng thấp (cạnh, góc, hình chữ nhật tương phản cao) chuyển giao rất tốt. Em đã thiết kế thí nghiệm ablation E-A vs E-B (fine-tune vs train từ đầu, chỉ khác đúng một dòng cấu hình `pretrained_weights`) để **đo** giá trị đó chứ không khẳng định suông.
- Với OCR: PaddleOCR pretrained chạy trên CCPD cho exact-match 0,00% do sinh thêm một ký tự thừa; chỉ cần một bước hậu xử lý bỏ ký tự đó là lên 90,97%. Đây chính là bằng chứng rằng **lớp hậu xử lý là bắt buộc**, không phải trang trí.

---

### A4. Kết quả của em so với state-of-the-art thế nào?

**Trả lời ngắn.**
Thẳng thắn: đồ án của em **không tạo ra state-of-the-art và không đặt mục tiêu đó**. Các công trình SOTA huấn luyện trên hàng chục nghìn đến hàng trăm nghìn ảnh với GPU cụm; em có 4.578 ảnh và một máy CPU. Mục tiêu của em là một hệ thống hoàn chỉnh, đo được, trung thực về giới hạn của nó.

**Nếu bị hỏi sâu.**
- Mốc tham chiếu em dùng để tự đối chiếu là ba nghiên cứu YOLO11 cho ALPR (JAIC 2025, J-Cosine 2025, ETASR 2025) với mAP50 từ 0,906 đến 0,995. Chỉ tiêu em đặt (NFR-A1 ≥ 0,90) nằm trong dải đó.
- Nhưng phải nói rõ: **những con số này không so sánh trực tiếp được** vì khác dataset, khác phân chia train/test, khác định nghĩa lớp. So mAP giữa hai dataset khác nhau là một phép so sánh vô nghĩa.
- Cái em có thể so sánh công bằng là **so với chính em**: E-A vs E-B đo giá trị của pretrain; trước/sau hậu xử lý đo giá trị của bộ luật regex. So sánh nội bộ trên cùng một phân chia dữ liệu mới là so sánh có ý nghĩa.

**Cảnh báo.** Nếu ai đó gợi ý "vậy là kết quả của em kém hơn SOTA à?" — đừng phòng thủ. Trả lời: *"Em không đo trên cùng dataset nên không kết luận được ai hơn ai. Điều em kết luận được là hệ thống đạt các chỉ tiêu phi chức năng em tự đặt ra trước khi làm."*

---

### A5. Vì sao đề tài này xứng đáng là một đồ án tốt nghiệp?

**Trả lời ngắn.**
Vì nó đi trọn một vòng đời phần mềm có yếu tố AI: từ khảo sát văn bản pháp lý gốc, khảo sát công nghệ có trích dẫn, đặc tả 34 yêu cầu chức năng và các chỉ tiêu phi chức năng đo được, thiết kế kiến trúc 5 tầng, đến cài đặt và kiểm thử. Phần AI là một khối trong đó, không phải toàn bộ.

**Nếu bị hỏi sâu.**
- Riêng khối tài liệu nghiên cứu Phase 1 có 232 mục tham khảo, 211 được trích dẫn thật trong văn bản, có bản đồ ánh xạ BibTeX ↔ vị trí trích dẫn (`docs/reports/01-citation-map.md`).
- Em đã chạy một vòng phản biện tự động trên tài liệu Phase 1 và **sửa 25 lỗi**, trong đó 3 lỗi mức nghiêm trọng — chi tiết ở câu G2 và G4.

---

### A6. Phạm vi đồ án đến đâu? Cái gì em cố ý không làm?

**Trả lời ngắn.**
Em cố ý loại ba nhóm: nhận dạng loại xe / màu xe, tích hợp barrier hoặc phần cứng cổng, và xác thực người dùng. Giả định triển khai là hệ thống chạy nội bộ (A-04), nên mô hình đe doạ ở mức hạn chế.

**Nếu bị hỏi sâu.**
- Biển quân đội (bắt đầu bằng 2 chữ cái) nằm ngoài phạm vi — nhưng em **nhận biết để loại trừ** bằng `RE_MILITARY` và đánh dấu `is_valid_format = False` chứ không cố validate. Nhận biết-để-loại-trừ là xử lý đúng; cố validate một định dạng không nghiên cứu kỹ mới là sai.
- Màu nền biển mã hoá loại phương tiện (trắng / vàng / xanh / đỏ) — em đã khảo sát và ghi nhận, nhưng không đưa vào Phase 4 vì nó là một bài toán phân loại riêng.

---

### A7. Ai là người dùng của hệ thống này? Bài toán có thật không?

**Trả lời ngắn.**
Người dùng mục tiêu là bãi giữ xe, cổng ra vào cơ quan, và người vận hành cần tra cứu lịch sử ra vào. Đó là lý do hệ thống có ba chế độ đầu vào — ảnh, video, và khung hình thời gian thực qua API — cộng một trang lịch sử có bộ lọc. Phần số liệu tổng hợp phục vụ qua `GET /api/statistics`; màn hình hiển thị sẵn cho nó đã được gỡ khỏi giao diện ngày 2026-07-20 (xem câu E4c).

**Nếu bị hỏi sâu.**
Điểm cần trung thực: bộ dữ liệu em có **không phải** ảnh camera giao thông toàn cảnh. 90,8% ảnh chỉ chứa một biển số, và heatmap vị trí cho thấy biển tập trung mạnh ở giữa khung — dấu hiệu ảnh đã được cắt hoặc chụp có chủ đích lấy xe làm trung tâm. Nghĩa là mô hình **chưa được kiểm chứng ở chế độ đa đối tượng**; toàn bộ dataset chỉ có 9 ảnh chứa từ 5 biển trở lên.

---

### A8. Nếu đây là sản phẩm thương mại, nó thiếu gì để bán được?

**Trả lời ngắn.**
Thiếu bốn thứ, theo thứ tự ưu tiên: xác thực và phân quyền người dùng, chuyển SQLite sang PostgreSQL, kiểm thử chịu tải thật, và một giấy phép dữ liệu rõ ràng. Em biết chính xác từng thứ và biết cách khắc phục — chi tiết ở câu E6.

---

## B. Về dữ liệu

### B1. Dữ liệu lấy ở đâu? Có bản quyền không?

**Trả lời ngắn.**
Bộ chính là `hoanglvuit/Vietnam_License_Plate_Segment_Datasets` trên HuggingFace, 4.578 ảnh, tải công khai không cần token. Em phải nói thẳng một rủi ro còn treo: **trang nguồn không ghi rõ giấy phép**. Trường `license` trong cấu hình của em hiện ghi là "cần kiểm tra trước khi dùng cho mục đích xuất bản" — đây là điều em ghi nhận chứ không giấu.

**Nếu bị hỏi sâu.**
- Bộ chính đã chốt ở Phase 1 là VNLP (~37.300 ảnh) nhưng **tải không được** — kho `fict-labs/vnlp` trả HTTP 401, đã chuyển sang chế độ gated. Đó là lý do quy mô thực tế chỉ còn 12,3% so với kế hoạch.
- Bộ v3 cuối cùng gồm **15.133 ảnh / 6 nguồn** (hợp nhất từ 7 bộ Roboflow + HuggingFace); **2 bộ có nhãn ký tự** riêng đã cho phép đo độ chính xác OCR (2.801 biển có nhãn chuỗi).
- Mỗi ảnh trong tập cuối truy ngược được về file gốc và bộ gốc qua `merge_manifest.csv` (tiêu chí chất lượng Q7). Không truy vết được thì không trích dẫn giấy phép được.

**Cảnh báo.** Không nói "dữ liệu công khai nên dùng thoải mái". Công khai ≠ được phép tái phân phối. Cách nói đúng: *"Đây là rủi ro em đã ghi nhận từ Phase 1 và chưa giải quyết xong. Trước khi công bố phải liên hệ tác giả hoặc thay bằng nguồn có giấy phép tường minh."*

---

### B2. Bao nhiêu ảnh? Có đủ không?

**Trả lời ngắn.**
Hiện có 4.578 ảnh với 5.200 box, chia 3.203 / 917 / 458 theo tỷ lệ 70/20/10. So với kế hoạch ban đầu 37.300 ảnh thì đây chỉ là 12,3%. Với bài toán phát hiện một lớp thì lượng này đủ để hội tụ — kết quả huấn luyện đang chạy xác nhận điều đó. Nhưng nó **không đủ** để mô hình tổng quát hoá sang các bối cảnh chưa gặp.

**Nếu bị hỏi sâu.**
- Bộ dữ liệu không đồng nhất mà là ghép của **5 tiểu tập**, mỗi tiểu tập gần như thuần một loại biển: `greenpack` 100% biển 2 dòng, `carlong` 99,4% biển 1 dòng. Cấu trúc này gợi ý mỗi tiểu tập thu từ một buổi / một bối cảnh riêng, tức là các ảnh **không độc lập với nhau** như giả định thống kê thông thường.
- Tỷ lệ biển 2 dòng: 3.559 / 5.200 box = 68,44% theo nhãn thật. Vượt xa ngưỡng tối thiểu 30% em đặt ra, nên biển 2 dòng không bị coi là ngoại lệ hiếm.
- Đang mở rộng lên ~21.000 ảnh từ 8 bộ Roboflow. Khi gộp, phép đo trùng lặp **chéo bộ** mới thực sự có ý nghĩa — hiện tại nó bằng 0 chỉ vì có đúng một bộ.

---

### B3. Làm sao đảm bảo không rò rỉ dữ liệu giữa train và test?

**Trả lời ngắn.**
Em không chia theo ảnh mà chia theo **nhóm ảnh gần trùng**. Trước khi chia, em chạy perceptual hash 64-bit, ngưỡng Hamming 5, tìm được 193 cặp trùng gom thành 144 nhóm. Mỗi nhóm là một đơn vị chia không thể tách. Sau khi chia xong, script đọc lại kết quả cuối cùng và kiểm tra lại độc lập — phát hiện vi phạm thì **trả mã lỗi và không ghi gì cả**.

**Nếu bị hỏi sâu — đây là chỗ có một phát hiện đáng kể.**

Em phân tích 193 cặp trùng theo vị trí trong **bản chia train/val gốc của chính tác giả bộ dữ liệu**:

| Cặp nằm ở | Số cặp | Tỷ lệ |
|---|---|---|
| train ↔ train | 111 | 57,5% |
| **train ↔ val** | **73** | **37,8%** |
| val ↔ val | 9 | 4,7% |

**73 cặp ảnh trùng lặp nằm vắt qua ranh giới train/val của tác giả**, trong đó có những cặp hash giống hệt nhau (Hamming = 0), ví dụ `train/Tgmt_0002.png` ≡ `val/Tgmt_0711.png`. Bất kỳ ai dùng thẳng bản chia sẵn đều đang đo trên một tập validation đã ô nhiễm. Đây chính là căn cứ để em **vứt bỏ hoàn toàn bản chia gốc (3.433/1.145)** và chia lại từ đầu.

- Thuật toán dedup là **chính xác, không xấp xỉ**: multi-index hashing cắt hash thành 6 dải, theo nguyên lý chuồng bồ câu hai hash lệch ≤ 5 bit bắt buộc trùng khít ít nhất một dải. Không bỏ sót cặp nào. Gom nhóm bằng union-find nên đảm bảo tính bắc cầu.
- Kiểm chứng nhất quán: 4.253 đơn vị lẻ + 144 nhóm = 4.397 đơn vị, khớp chính xác.

**Cảnh báo.** Đây là câu **mạnh nhất** của phần dữ liệu. Nếu hội đồng hỏi về rò rỉ, hãy kể phát hiện 73 cặp — nó chứng minh bước dedup không phải thủ tục hình thức mà bắt được một lỗi thật trong chính bộ dữ liệu đang dùng.

---

### B4. Nhãn có đúng không? Ai kiểm tra?

**Trả lời ngắn.**
Nhãn do tác giả bộ dữ liệu gán, em **không gán lại thủ công** — cần nói thẳng điều đó. Cái em làm là chạy một bộ kiểm tra tự động trên toàn bộ 4.578 ảnh: nhãn tồn tại, parse được, toạ độ trong [0,1], diện tích > 0, không vượt khung, và ảnh **giải mã đầy đủ bằng OpenCV**. Kết quả: 0 lỗi mức error, 477 cảnh báo box nhỏ.

**Nếu bị hỏi sâu.**
- Chi tiết đáng nêu về phép kiểm tra ảnh: em giải mã đầy đủ chứ không chỉ đọc header. Một file PNG bị cụt vẫn có header hợp lệ; nếu chỉ đọc header thì lỗi sẽ nổ ra giữa lúc huấn luyện chứ không phải ở bước kiểm tra.
- 477 box nhỏ (9,17%) em **giữ lại**, không loại. Loại chúng đi sẽ tạo lỗi tệ hơn: ảnh vẫn còn biển số nhưng nhãn đã bị xoá, tức là dạy mô hình rằng biển số nhỏ không phải biển số — dạy sai chủ động, tệ hơn hẳn dạy một mục tiêu khó.
- Có một phép kiểm tra chéo nhãn đáng kể: bộ này có **cả hai** thông tin — nhãn số dòng thật (từ hai lớp gốc BSD/BSV) và tỷ lệ khung hình. Em đối chiếu heuristic "AR ≥ 2,5 ⇒ 1 dòng" với nhãn thật: độ chính xác 97,33% (5.061/5.200). Đây là cơ hội hiếm để **đo trực tiếp** độ tin cậy của một heuristic thay vì giả định nó đúng.

---

### B5. Vì sao không tự chụp dữ liệu?

**Trả lời ngắn.**
Ba lý do. Thứ nhất, chụp và gán nhãn 4.500 ảnh thủ công vượt quá ngân sách thời gian của một đồ án — riêng gán nhãn đã là hàng chục giờ. Thứ hai, ảnh tự chụp sẽ chỉ phản ánh một địa điểm và một loại camera, tổng quát hoá còn kém hơn dữ liệu công khai. Thứ ba, chụp biển số xe người khác rồi công bố có vấn đề về dữ liệu cá nhân.

**Nếu bị hỏi sâu.**
Nếu hội đồng hỏi "vậy làm sao biết hệ thống chạy được trên ảnh thật?" — trả lời trung thực: em có demo trực tiếp trên máy tại buổi bảo vệ với ảnh chụp thật, nhưng đó là **kiểm chứng định tính, không phải phép đo**. Một bộ test tự chụp có nhãn là việc còn thiếu và em ghi nhận nó ở phần Hạn chế.

---

### B6. Dữ liệu có cân bằng không? Có bị thiên lệch chỗ nào?

**Trả lời ngắn.**
Cân bằng theo trục quan trọng nhất — tỷ lệ biển 2 dòng lệch nhau tối đa **0,06 điểm phần trăm** giữa train / val / test (65,56% / 65,54% / 65,50%). Nhưng thiên lệch theo trục khác thì có, và em ghi nhận rõ.

**Nếu bị hỏi sâu — ba thiên lệch đã đo được:**

| Thiên lệch | Số liệu | Hệ quả |
|---|---|---|
| Ảnh gần như chỉ có một biển | 90,8% ảnh có đúng 1 box; chỉ 9 ảnh có ≥ 5 box | Ngưỡng NMS và `max_det` không được hiệu chỉnh trên dữ liệu đại diện |
| Biển tập trung giữa khung | Heatmap nóng nhất ở x ≈ 0,46–0,50; y ≈ 0,50–0,58 | Mô hình có thể học prior vị trí ngầm; biển ở rìa khung dễ bị bỏ sót |
| Box cực nhỏ tập trung ở biển xe máy | p05 diện tích: 0,244% (2 dòng) so với 1,002% (1 dòng) — nhỏ hơn 4 lần | Cộng dồn với rủi ro biển 2 dòng |

Em đã đưa `translate = 0,1` và `perspective = 0,0005` vào augmentation chính vì thiên lệch vị trí thứ hai.

---

### B7. Tại sao lại chia 70/20/10 mà không phải 80/20?

**Trả lời ngắn.**
Vì em cần **ba** tập chứ không phải hai. Tập val tham gia vào việc chọn checkpoint `best.pt` theo fitness từng epoch, nên báo cáo con số trên val là báo cáo một ước lượng lạc quan có thiên lệch. Mọi chỉ số công bố đều đo trên tập **test** chưa từng tham gia bất kỳ quyết định nào.

**Nếu bị hỏi sâu.**
- Tỷ lệ đạt được: 0,6997 / 0,2003 / 0,1000 — sát chỉ tiêu vì thuật toán gán theo **mức thiếu hụt tương đối so với chỉ tiêu**, không cắt danh sách theo vị trí. Nếu cắt theo vị trí thì các đơn vị kích thước khác nhau (1–5 ảnh) sẽ làm lệch tỷ lệ, và tập test 10% dễ bị tập train 70% nuốt hết.
- `--split` của `evaluate.py` mặc định là `test` đúng vì lý do này.

---

### B8. Có dùng dữ liệu tổng hợp (synthetic) không?

**Trả lời ngắn.**
Không. Toàn bộ 4.578 ảnh là ảnh thật. Script tăng cường dữ liệu ngoại tuyến (`augment.py`) đã viết xong và chạy được nhưng **chưa chạy** — kiểm chứng được: thư mục train có 3.203 file, 0 file mang hậu tố `_aug`. Augmentation trong đồ án này chỉ có loại trực tuyến do Ultralytics thực hiện trong lúc huấn luyện.

---

## C. Về mô hình và huấn luyện

### C1. Vì sao chọn YOLO11 mà không phải YOLOv8 / v9 / v10?

**Trả lời ngắn.**
Em loại bằng hai bước. Bước một: máy triển khai không có GPU, nên tiêu chí bắt buộc là **có số liệu tốc độ CPU chính thức**. YOLOv9, v10, v12, v13 đều không có, nên bị loại vì không có căn cứ để đánh giá — không phải vì chúng kém. Bước hai: YOLO11n vượt YOLOv8n đồng thời ở **cả hai chiều** — mAP 39,5 so với 37,3 và tốc độ CPU 56,1 ms so với 80,4 ms. Không có lý do kỹ thuật nào để chọn v8.

**Nếu bị hỏi sâu.**
- Hai cơ chế kiến trúc khớp trực tiếp bài toán: **C2PSA** cải thiện phát hiện vật thể nhỏ (biển số là vật thể nhỏ), **anchor-free head** xử lý tốt tỷ lệ khung hình dẹt của biển 1 dòng.
- Có ba nghiên cứu ALPR độc lập dùng YOLO11 với mAP50 từ 0,906 đến 0,995 — nền tảng thực nghiệm dày nhất trong nhóm ứng viên.
- **YOLO26n trên giấy tờ tốt hơn** YOLO11n ở cả ba chỉ số (mAP 40,9 vs 39,5; CPU 38,9 ms vs 56,1 ms; 2,4 M vs 2,6 M tham số). Em vẫn không chọn vì nó phát hành 09/2025, **chưa có tiền lệ ALPR nào** để đối chiếu, và tài liệu của chính nhà phát hành có mâu thuẫn nội tại (tuyên bố "nhanh hơn 43%" không tái lập được từ bảng benchmark của họ, ra ~30,7%). Khuyến nghị của em là huấn luyện song song làm đối chứng — hạ tầng hiện chưa hỗ trợ và đây là khoảng trống em ghi nhận.

**Cảnh báo.** Nếu hội đồng hỏi "sao không dùng cái mới nhất?" — trả lời: *"Chọn một mô hình chưa có tiền lệ trên đúng bài toán làm phương án duy nhất là rủi ro không cần thiết với một đồ án. Cách đúng là chạy nó song song làm đối chứng, và em ghi nhận đó là việc chưa làm."*

---

### C2. Vì sao chọn biến thể nano mà không phải s / m / l?

**Trả lời ngắn.**
Vì ràng buộc triển khai: toàn bộ suy luận chạy trên CPU, chỉ tiêu độ trễ là ≤ 800 ms p95 cho một ảnh và ≥ 5 FPS cho webcam. Mô hình lớn hơn sẽ phá chỉ tiêu đó. Em không cố định lựa chọn này — có sẵn cấu hình leo thang `yolo11s_escalation.yaml`, khác cấu hình chính **đúng một chiều** là `model_variant`.

**Nếu bị hỏi sâu — và đây là điểm phương pháp luận đáng nêu.**
Có một cái bẫy em ghi thẳng vào comment đầu file cấu hình leo thang: **nếu mô hình yếu ở riêng biển 2 dòng thì tuyệt đối không được leo thang sang YOLO11s**. Điểm yếu ở một *phân nhóm dữ liệu* là vấn đề *dữ liệu*, và thêm tham số vào mô hình không tạo ra dữ liệu. Chỉ leo thang khi mô hình yếu **đều** cả hai loại biển. Em đặt cảnh báo đó ngay tại chỗ người ta sắp mắc lỗi.

---

### C3. ⚠️ mAP của em cao quá — mAP50 0,983. Có bị overfit không? Có bị rò rỉ dữ liệu không?

> **Đây là câu khó nhất trong toàn bộ buổi bảo vệ. Học thuộc câu trả lời này.**

**Trả lời ngắn.**
Em hiểu vì sao câu hỏi này được đặt ra — con số cao phải bị nghi ngờ, đó là phản xạ đúng. Em có ba câu trả lời, theo thứ tự sức nặng. Thứ nhất, con số công bố **0,983** đo trên **tập test v3 đã khử trùng lặp ở ngưỡng phash 10** — chính vì đề phòng rò rỉ mà em không dùng con số baseline cũ 0,9933 (bộ v1 có rò rỉ thật). Thứ hai, em **kiểm chứng rò rỉ bằng phép đo chứ không bằng lời**, và trung thực về giới hạn của phép đo đó. Thứ ba, bài toán detection này **vốn dễ**: một lớp, tương phản cao, kích thước lớn.

**Nếu bị hỏi sâu — bốn lập luận, mỗi cái có số liệu.**

**(1) Con số công bố đo trên mô hình và tập test CÙNG thuộc v3 đã khử trùng lặp.**
- `models/best.pt` huấn luyện trên split v3, đánh giá trên test v3 (1.514 ảnh): mAP50 **0,983**, mAP50-95 **0,783**, P **0,984**, R **0,971**.
- Bộ v3 gom nhóm trùng lặp ở **ngưỡng phash 10**: v2 có 9.126 cặp vắt split ở ngưỡng 10, **v3 có 0**.
- Em **không** lấy baseline (`baseline-416-v1.pt`, train trên v1) đo trên test v3 — vì 289/1.514 ảnh test v3 (19,1%) trùng tên tệp với train+val v1, cho recall = 1,000 giả tạo. Con số công bố **chỉ** từ `runs/final-640-v3`.

**(2) Trung thực về giới hạn phép đo rò rỉ — em không tuyên bố "sạch tuyệt đối".**
- Perceptual hash bắt được ảnh gần trùng bit-hash, nhưng **không** bắt được rò rỉ ở mức ngữ nghĩa: cùng một biển số chụp ở góc khác, cùng một xe ghé cùng barrier hai ngày khác nhau. Ví dụ tồn dư: biển `51F-155.85`.
- Vì vậy em nói: mAP 0,983 **không còn bị rò rỉ tên-tệp thổi phồng** như baseline, nhưng chỉ **test xuyên bộ dữ liệu** mới khép được rủi ro cùng-xe/khác-ngày. Đây là món nợ em ghi nhận, không giấu.
- ⚠️ Một đính chính phương pháp: `phash` cho khoảng cách **luôn chẵn** (mọi hash đều có 32 bit bật), nên "khoảng cách nhỏ nhất = 6" là tất yếu toán học, không phải dấu vết rò rỉ.

**(3) Bài toán detection này vốn dễ — kết luận có căn cứ, không phải lời bào chữa.**

| Yếu tố | Số liệu | Vì sao làm bài toán dễ |
|---|---|---|
| Số lớp | **1** (`license_plate`) | Không có phần phân loại. Đó là lý do em đặt `cls = 0,5` — thấp. |
| Tương phản | Biển là chữ đen trên nền trắng/vàng, viền rõ | Đúng loại đặc trưng mà pretrain COCO chuyển giao tốt nhất |
| Số đối tượng / ảnh | phần lớn ảnh có ít box | Không có bài toán đông đúc, không có NMS phức tạp |
| Transfer learning | Khởi tạo từ trọng số COCO | Hội tụ nhanh là hành vi mong đợi |

**(4) mAP50-95 = 0,783 cho thấy hành vi bình thường, không phải rò rỉ.**

- **Khoảng cách giữa mAP50 (0,983) và mAP50-95 (0,783)** chính là bằng chứng mô hình **tìm ra biển rất tốt nhưng khớp box chưa hoàn hảo** — nếu học thuộc tập test thì chỉ số chặt mAP50-95 cũng phải sát 0,98.
- **Tách theo layout:** biển 1 dòng mAP50 0,988, biển 2 dòng 0,968 — chênh chỉ 2,09 điểm, detection ít nhạy với layout. Đây là dấu hiệu mô hình khái quát hoá, không phải học thuộc một phân nhóm.
- Điểm yếu biển 2 dòng **không** ở detection mà ở **OCR** (xem D1) — em phân biệt rõ hai tầng thay vì gộp một con số trung bình.

**Cảnh báo — ba cách trả lời sai câu này:**
- ❌ *"Em cũng không biết sao cao thế."* — mất hết uy tín.
- ❌ *"Model của em tốt lắm ạ."* — mời hội đồng đào sâu.
- ❌ Nhầm lẫn overfit và rò rỉ. Đây là **hai** cáo buộc khác nhau: overfit = học thuộc train, kém trên val (**không phải trường hợp này** — val đang tốt); rò rỉ = val bị ô nhiễm bởi train (loại trừ bằng dedup). Phải tách hai cái ra khi trả lời.

---

### C4. Vì sao huấn luyện trên CPU mà không dùng GPU?

**Trả lời ngắn.**
Vì máy phát triển **không có GPU CUDA** — CPU Intel Core i5-14600K, đồ hoạ tích hợp Intel UHD 770, không chạy được CUDA và Ultralytics không có backend huấn luyện cho nó. Mô hình chính thức `best.pt` đã huấn luyện xong ở `imgsz=640` trên split v3, 20 epoch. Baseline 416 px trước đó giữ làm mô hình đối chứng.

**Nếu bị hỏi sâu.**
- Mô hình chính thức: `imgsz` **640** (đúng chỉ tiêu), split v3, 20 epoch, cho mAP50 0,983 / mAP50-95 0,783 trên test.
- Baseline đối chứng chạy ở cấu hình hạ (`imgsz` 416, 40 epoch) để khả thi trên CPU — **không** dùng làm số công bố vì sai độ phân giải và bộ v1 có rò rỉ.
- **Hệ quả phải nêu rõ:** cặp 416/v1 ↔ 640/v3 là một khảo sát mô tả, ba biến (imgsz, bộ dữ liệu, số epoch) đổi đồng thời nên **không quy kết nguyên nhân** cho biến nào.
- Nguyên tắc phân vai em đã chốt từ Phase 3: huấn luyện ở đâu có GPU; **đo độ trễ bắt buộc trên máy cục bộ với `--device cpu`**, kể cả khi đang ngồi trên Colab có GPU sẵn — vì con số độ trễ phải mô tả máy triển khai, không phải một chiếc T4 mượn tạm.
- OpenVINO dùng được phần cứng Intel nhưng nó là công cụ **suy luận**, không phải công cụ huấn luyện.

---

### C5. Huấn luyện xong chưa? Kết quả cuối là bao nhiêu?

**Trả lời ngắn.**
**Xong.** Mô hình chính thức `models/best.pt` (YOLO11n, imgsz 640, split v3, 20 epoch) cho **mAP50 0,983, mAP50-95 0,783, precision 0,984, recall 0,971 trên tập test 1.514 ảnh** — đạt cả bốn chỉ tiêu detection. Mọi con số đọc trực tiếp từ `runs/final-640-v3/results.csv` và báo cáo đánh giá, không chép tay.

**Điều em nói thẳng:** detection đạt, nhưng **OCR biển 2 dòng KHÔNG đạt** (xem D1) — đó là nút thắt còn lại và em trình bày trung thực. Cái em có là hạ tầng đo được kiểm chứng: đánh giá trên test chứ không phải val, tách riêng biển 1 dòng / 2 dòng, mọi con số truy ngược được về file YAML sinh ra nó.

---

### C6. Siêu tham số chọn thế nào? Có tune không?

**Trả lời ngắn.**
Trung thực: em **không chạy tìm kiếm siêu tham số tự động** — không có ngân sách tính toán cho việc đó trên CPU. Các giá trị đến từ mặc định Ultralytics, và em chỉ thay đổi những chỗ **có lý do đặc thù bài toán**, mỗi thay đổi ghi rõ lý do trong tài liệu.

**Nếu bị hỏi sâu — bốn thay đổi có chủ đích:**

| Tham số | Mặc định | Của em | Lý do |
|---|---|---|---|
| `box` | 7,5 | **8,0** | Đầu ra của detector được **một mô hình khác** (OCR) tiêu thụ, không phải con người. Hộp lệch vài pixel làm mất một cạnh ký tự ⇒ OCR đọc sai cả biển. |
| `fliplr` | 0,5 | **0,0 — chặn cứng** | Xem câu C8 |
| `hsv_h` | 0,015 | 0,015 (giữ, nhưng **có lý do**) | Màu nền biển ở Việt Nam **mang ngữ nghĩa** (trắng/vàng/xanh/đỏ mã hoá loại phương tiện). Xáo trộn sắc độ mạnh là phá một tín hiệu thật. |
| `lr0` khi fine-tune | — | **0,001 (cố tình thấp)** | LR cao trên trọng số pretrain gây catastrophic forgetting: đặc trưng COCO hữu ích bị phá trong vài trăm bước đầu, kết quả còn **tệ hơn** train từ đầu. |

- `seed = 42` và `deterministic = true` cố định để tái lập. Một con số trong luận văn mà chạy lại không ra được thì không có mấy giá trị bảo vệ.
- `train.py` chụp lại `training_config.yaml` ngay cạnh trọng số, nên mỗi con số truy ngược được về đúng cấu hình sinh ra nó.

---

### C7. Vì sao augmentation lại chọn những phép biến đổi đó?

**Trả lời ngắn.**
Nguyên tắc chung: chỉ dùng phép biến đổi **bảo toàn nhãn** và **mô phỏng điều kiện triển khai thật**. Ví dụ `perspective = 0,0005` vì camera cổng và bãi xe hầu như luôn chụp lệch trục; `erasing = 0,4` vì biển thật hay bị che bởi bùn, giá đỡ, móc kéo; `degrees = 5,0` (nhỏ) vì biển đã gắn trên xe thì gần như luôn nằm ngang.

**Nếu bị hỏi sâu — ba phép em cố tình tắt:**

| Tham số | Giá trị | Lý do tắt |
|---|---|---|
| `fliplr` / `flipud` | 0,0 | Xem C8 |
| `mixup` | 0,0 | Trộn alpha hai ảnh tạo ra chữ trên biển **không đọc được**, không mang tín hiệu phát hiện hữu ích |
| `copy_paste` | 0,0 | Kỹ thuật hướng segmentation, không áp dụng cho detection thuần |

`close_mosaic = 10` — tắt mosaic ở 10 epoch **cuối** để mô hình kết thúc trên ảnh không biến dạng, gần phân phối lúc suy luận thật.

---

### C8. Vì sao tắt lật ngang (`fliplr = 0`) trong augmentation?

**Trả lời ngắn.**
Vì lật ngang một ảnh biển số làm **soi gương các ký tự in trên biển**. Đây không phải một phép biến đổi bảo toàn nhãn — biển lật ngang không phải một góc nhìn khác của cùng vật thể, mà là **một vật thể không tồn tại**. Chữ `A` soi gương không phải chữ `A`; chuỗi `59H1-234.56` soi gương không phải biển số của bất kỳ quốc gia nào.

**Nếu bị hỏi sâu — vì sao chi tiết này đáng đưa vào luận văn:**
1. **`fliplr = 0.5` là mặc định của Ultralytics.** Ai không nghĩ tới sẽ vô tình bật nó, và **một nửa số ảnh huấn luyện** sẽ là biển gương.
2. **Sai lầm này không làm hỏng quá trình huấn luyện.** Loss vẫn giảm, mAP vẫn tăng, đường cong vẫn đẹp. Nó chỉ làm mô hình **kém hơn mức đáng lẽ đạt được** — một lỗi tốn kém và gần như không thể phát hiện nếu chỉ nhìn biểu đồ.
3. **Thiệt hại lan sang khối OCR** nếu chính sách augmentation này được tái dùng cho việc huấn luyện OCR về sau.
4. Vì vậy em **chặn ở tầng mã, không phải tầng quy ước**: `TrainingConfig.__post_init__` ném `ValueError` kèm giải thích nếu ai đó đặt `fliplr` khác 0. Một quy ước ghi trong comment sẽ bị vi phạm sớm muộn; một `ValueError` thì không.

**Cảnh báo.** Đây là một trong những câu **ghi điểm** tốt nhất. Nó cho thấy hiểu bản chất augmentation chứ không chỉ copy cấu hình.

---

### C9. Có cơ chế nào chống lỗi âm thầm trong huấn luyện không?

**Trả lời ngắn.**
Có ba, và cả ba đều chặn loại lỗi tệ nhất: chương trình chạy xong bình thường mà kết quả sai.

**Nếu bị hỏi sâu.**

| # | Lỗi được chặn | Cơ chế |
|---|---|---|
| 1 | Gõ `epoch:` thay vì `epochs:` trong YAML ⇒ huấn luyện với số epoch mặc định | `from_dict()` từ chối khoá lạ, ném `ValueError` kèm danh sách khoá hợp lệ |
| 2 | `resume=True` trên một lần chạy **đã xong** ⇒ Ultralytics âm thầm bắt đầu lần chạy mới với tham số mặc định, tức là **huấn luyện trên COCO**, rồi ghi đè `best.pt` tốt bằng trọng số vô giá trị | `assert_resumable()` đọc chỉ số epoch trong checkpoint và từ chối |
| 3 | Huấn luyện nhầm dataset | Sau khi `model.train()` trả về, đối chiếu tên dataset Ultralytics **thực sự** dùng với dataset được yêu cầu; lệch ⇒ từ chối công bố trọng số |

Thêm một lớp: nếu `models/best.pt` đã tồn tại, file cũ được đổi tên kèm dấu thời gian chứ không bị ghi đè.

Một lỗi âm thầm nữa đã bị chặn ở tầng dữ liệu: nhãn trong `processed/yolo/` phải là YOLO **5 trường thuần** (đã kiểm chứng cả 5.200 dòng). Lý do — bộ nạp Ultralytics coi mọi trường sau class id là toạ độ polygon; gặp ký tự `-` (chỗ giữ chỗ cho `plate_text` rỗng) nó ném lỗi rồi **bỏ luôn ảnh đó vì "corrupt"**, chỉ in cảnh báo và huấn luyện tiếp trên phần còn lại — mà phần còn lại có thể là **rỗng**. Cả 4.578 ảnh có thể biến mất trong khi log vẫn trông bình thường.

---

### C10. Nếu mô hình không đạt chỉ tiêu thì em làm gì?

**Trả lời ngắn.**
Em có sơ đồ quyết định lập từ Phase 3, và điểm mấu chốt là **chẩn đoán trước, leo thang sau**. Nếu yếu đều cả hai loại biển ⇒ leo thang sang YOLO11s. Nếu chỉ yếu ở biển 2 dòng ⇒ **cân bằng lại dataset**, tuyệt đối không tăng dung lượng mô hình.

**Nếu bị hỏi sâu.**
`evaluate.py` tự động cảnh báo nếu khoảng cách AP giữa biển 1 dòng và 2 dòng vượt **10 điểm**, kèm khuyến nghị cân bằng dataset. Cảnh báo được đặt ngay tại chỗ người ta sắp chẩn đoán sai bệnh.

Nguyên tắc thí nghiệm: **mỗi thí nghiệm chỉ khác thí nghiệm gốc ở một chiều.** Đó là lý do `yolo11s_escalation.yaml` giữ nguyên xi augmentation, `imgsz`, `epochs`, `patience`, `seed`. Nếu đổi đồng thời dung lượng mô hình và chính sách augmentation thì chênh lệch mAP không quy được cho nguyên nhân nào — thí nghiệm chứng minh con số không.

---

## D. Về OCR và biển 2 dòng

### D1. ⚠️ Vì sao chọn PaddleOCR? Đã so sánh với EasyOCR / Tesseract chưa?

> **Câu này có một cái bẫy: em **chưa** tự benchmark ba engine. Phải trả lời trung thực.**

**Trả lời ngắn.**
Em chọn PaddleOCR làm **baseline**, không phải làm kết luận. Em phải nói thẳng: **không tồn tại benchmark công khai nào so sánh PaddleOCR / EasyOCR / Tesseract trên riêng ảnh biển số xe máy Việt Nam 2 dòng** — em đã tìm và ghi nhận đây là một khoảng trống nghiên cứu. Căn cứ chọn của em là ràng buộc triển khai chứ không phải độ chính xác: PaddleOCR nặng ~21 MB so với ~200 MB của EasyOCR, và độ trễ CPU công bố nằm trong ngân sách.

**Nếu bị hỏi sâu — và đây là chỗ trung thực ăn điểm.**

Trong quá trình phản biện tài liệu Phase 1, em **tự bác bỏ hai bằng chứng** mình từng dùng để biện minh cho PaddleOCR:

| Khẳng định từng dùng | Sự thật |
|---|---|
| ❌ "YOLOv8n + **PaddleOCR** đạt 99% độ chính xác OCR, cải thiện 4,16%" | Bài gốc dùng **EasyOCR**, không phải PaddleOCR. 99% là tỷ lệ **phát hiện**, không phải OCR (OCR thật là 98%). Không có con số 4,16% nào trong bài. |
| ❌ "Hệ thống ANPR dùng **PaddleOCR** đạt 97%/95% trên 1000 ảnh" | Thực tế là **99%/98% trên 270 ảnh**, cũng với **EasyOCR**. Cả ba thành phần đều sai. |

Nghĩa là hai số liệu từng được dùng để chứng minh "PaddleOCR tốt cho biển số" thì nguồn gốc lại chứng minh cho **EasyOCR**.

**So sánh kiểm chứng được duy nhất mà em tìm thấy lại nghiêng về EasyOCR**: CER 0,09 (EasyOCR) so với 0,10 (PaddleOCR) — nhưng đo trên ảnh tài liệu chạy GPU, chênh 0,01, nên không có ý nghĩa quyết định. Và IEEE ICCCNT 2024 (Reddy & Shruthi) so đúng ba engine này kết luận EasyOCR được ưa chuộng về độ chính xác — nhưng toàn văn nằm sau paywall nên em không lấy được bảng số liệu.

Bốn điều PaddleOCR **thua**, em ghi rõ:
- **Không có whitelist ký tự lúc suy luận** — Tesseract có `tessedit_char_whitelist`, EasyOCR có `allowlist`. PaddleOCR muốn đổi charset phải fine-tune. Em bù bằng lớp regex hậu xử lý.
- CER nhỉnh hơn EasyOCR.
- Khó cài hơn — PaddlePaddle là framework riêng, thêm ~500 MB–1 GB dependency.
- Bằng chứng fine-tune tốt (90,97% → 94,54%) là trên **biển Trung Quốc 1 dòng**.

**Cảnh báo — cách trả lời đúng khi bị dồn.**
Nếu hội đồng nói *"vậy đáng ra em nên dùng EasyOCR"* — **đừng cãi**. Trả lời: *"Đó là một kết luận hợp lý và em đã ghi nó vào phần khuyến nghị. Kiến trúc của em đặt bộ nhận dạng sau một interface trừu tượng (NFR-M5) chính vì lý do này — thay engine không phải sửa mã tầng API. Việc còn thiếu là em tự chạy benchmark ba engine trên tập biển số Việt Nam có nhãn, và đó là việc đầu tiên em làm nếu tiếp tục."*

Tuyệt đối **không** trích hai số liệu đã bị bác bỏ ở trên. Nếu hội đồng mở bài Nature ra đọc, đây là lỗi bị bắt ngay lập tức.

---

### D2. Biển 2 dòng xử lý thế nào?

**Trả lời ngắn.**
Kỹ thuật **split-then-hstack**: nhận biết biển 2 dòng, cắt thành nửa trên và nửa dưới có chồng lấn nhẹ, resize hai nửa về cùng chiều cao rồi ghép **ngang** thành một dải dài một dòng, sau đó gọi bộ nhận dạng đúng một lần. Nghĩa là em biến một bài toán mà kiến trúc CRNN không giải được thành một bài toán mà nó giải được.

**Nếu bị hỏi sâu — vì sao phải làm vậy chứ không đưa thẳng vào OCR.**
- **Nguyên nhân gốc là kiến trúc, không phải chất lượng model.** CRNN/CTC giả định alignment đơn điệu trên **một** dòng. Đó là giả định nằm trong hàm mất mát, không sửa được bằng dữ liệu.
- **Bằng chứng cụ thể trong PaddleOCR:** module recognition resize ảnh về chiều cao cố định **48 px** (`rec_image_shape = 3 × 48 × 320`). Crop biển xe máy có tỷ lệ khung hình ~1,36, nên khi ép về cao 48 px thì **mỗi dòng chỉ còn khoảng 24 px**. Đó là mức mà ký tự bắt đầu mất chi tiết.
- Ghép ngang giải quyết cả hai: mỗi dòng được dùng trọn 48 px chiều cao, và chuỗi trở thành đơn điệu một chiều.
- **Bắt buộc rectify trước khi tách** — nếu biển nghiêng thì đường cắt ngang sẽ cắt qua ký tự.
- Có lợi ích phụ đo được: repo Việt Nam `LeNguyenGiaBao/license_plates_recognition` ghi nhận thời gian OCR giảm từ 0,25 s xuống 0,05–0,1 s trên CPU i5-8250 khi tự cắt sẵn từng dòng (bỏ qua được bước DB detection).
- Cài đặt: `ai/inference/two_line.py`, 26 unit test trong `tests/test_two_line.py`.

---

### D3. Làm sao biết một biển là 1 dòng hay 2 dòng?

**Trả lời ngắn.**
Ba nguồn theo thứ tự ưu tiên: nhãn số dòng thật nếu có, tên lớp mang thông tin bố cục, và cuối cùng mới đến suy đoán theo **tỷ lệ khung hình với ngưỡng 2,5**. Ngưỡng 2,5 suy ra từ QCVN 08:2024/BCA và — điều em thấy thú vị — được **dữ liệu thực nghiệm xác nhận độc lập**.

**Nếu bị hỏi sâu.**

Kích thước danh nghĩa theo QCVN 08:2024/BCA:

| Loại biển | Kích thước | Tỷ lệ | Số dòng |
|---|---|---|---|
| Ô tô biển dài | 520 × 110 mm | 4,727 | 1 dòng |
| Ô tô biển ngắn | 330 × 165 mm | 2,000 | 2 dòng |
| Mô tô, xe máy | 190 × 140 mm | 1,357 | 2 dòng |

Hai nhóm tách nhau rất rõ (2,000 so với 4,727) nên ngưỡng 2,5 ổn định.

**Xác nhận thực nghiệm:** biểu đồ phân bố AR của 5.200 box cho **phân bố lưỡng đỉnh rõ** — một đỉnh nhọn quanh AR ≈ 1,1–1,3 và một cụm rộng quanh AR ≈ 3,0–4,0, giữa hai cụm là **vùng trũng gần bằng 0 ở khoảng 2,2–2,6**. Ngưỡng 2,5 rơi đúng đáy vùng trũng đó.

**Và em đo được độ chính xác của chính heuristic này** — bộ dữ liệu có cả nhãn thật lẫn AR nên đối chiếu trực tiếp được:

| | Đoán 1 dòng | Đoán 2 dòng |
|---|---|---|
| **Thật 1 dòng** (1.641) | 1.509 ✓ | 132 ✗ |
| **Thật 2 dòng** (3.559) | 7 ✗ | 3.552 ✓ |

Độ chính xác **97,33%**, nhưng **lệch một chiều theo tỷ lệ 19:1** — 132 lỗi ở hướng "1 dòng bị đoán nhầm thành 2 dòng", chỉ 7 lỗi ở hướng ngược lại. Nguyên nhân: box bao quanh polygon luôn có đệm, và với biển dài mảnh thì đệm theo chiều cao chiếm tỷ lệ lớn hơn nhiều ⇒ AR bị kéo xuống. Cộng thêm phối cảnh và biển móp/cong, cả ba nguyên nhân đều đẩy AR về phía 1.

Một chi tiết phương pháp luận: ngưỡng 2,5 dùng trong `evaluate.py` **cố ý trùng** với ngưỡng của tầng suy luận. Nếu đánh giá theo một quy tắc khác với hệ thống triển khai thì độ chính xác báo cáo không mô tả hệ thống thật — nó mô tả một hệ thống giả định.

---

### D4. Vì sao không huấn luyện OCR riêng cho biển số Việt Nam?

**Trả lời ngắn.**
Vì **không có dữ liệu**. Bộ dữ liệu chính của em chỉ có nhãn vùng biển, **không có một nhãn chuỗi biển số nào** — kiểm chứng bằng số: `plate_text.annotated_boxes = 0`, `character_frequency = {}`. Không có nhãn chuỗi thì không huấn luyện được OCR, và cũng không đo được độ chính xác OCR.

**Nếu bị hỏi sâu.**
- Đây là **khoảng trống lớn nhất của đồ án** và em ghi nó ngay trong báo cáo dữ liệu chứ không giấu.
- Đang xử lý bằng cách gộp thêm 8 bộ Roboflow, trong đó **2 bộ có nhãn ký tự**. Khi có nhãn chuỗi, hai việc mở khoá cùng lúc: đo được NFR-A5/A6 (trước và sau hậu xử lý), và có căn cứ để cân nhắc fine-tune.
- Bằng chứng rằng fine-tune sẽ có tác dụng: ứng dụng biển số của chính PaddleOCR cho thấy fine-tune nâng recognition từ 90,97% lên 94,54% và detection Hmean từ 76,12% lên 99,00% — nhưng trên biển Trung Quốc 1 dòng.
- Nếu fine-tune, **charset phải là đủ A–Z + 0–9 (36 ký tự)** — lý do ở câu D6.

---

### D5. Bộ luật regex của em dựa trên văn bản nào?

**Trả lời ngắn.**
Thông tư 79/2024/TT-BCA (hiệu lực 01/01/2025), sửa đổi bởi Thông tư 13/2025 và Thông tư 51/2025, cộng với QCVN 08:2024/BCA ban hành kèm Thông tư 81/2024 cho phần kích thước vật lý. Em **không** dùng Thông tư 24/2023/TT-BCA vì văn bản đó đã hết hiệu lực — chi tiết ở câu G2.

**Nếu bị hỏi sâu.**
- **Thông tư 51/2025 thay toàn bộ Phụ lục mã tỉnh** sau sáp nhập đơn vị hành chính, còn 34 tỉnh/thành. Bảng mã tỉnh của em lấy theo bản này, không phải bản cũ 63 tỉnh.
- Nguyên tắc thiết kế bộ luật: **sửa lỗi theo VỊ TRÍ, không sửa lỗi toàn cục.** Ví dụ ký tự `0`/`O`: ở vị trí mã tỉnh (2 ký tự đầu) phải là chữ số ⇒ ép `O → 0`; ở vị trí seri phải là chữ cái ⇒ ép `0 → O`. Một bảng thay thế toàn cục sẽ làm hỏng một trong hai vị trí.
- Có **vùng cấm sửa** tường minh — những vị trí mà cả chữ và số đều hợp lệ thì tuyệt đối không đụng vào, vì sửa liều ở đó tạo lỗi mới thay vì sửa lỗi cũ.
- Cài đặt: `ai/inference/plate_rules.py` + `normalizer.py`, 29 unit test.

---

### D6. ⚠️ Charset OCR của em gồm những ký tự nào?

> **Câu này chứa một mệnh đề phổ biến nhưng SAI. Nếu em trả lời theo mệnh đề đó là hỏng.**

**Trả lời ngắn.**
**Đủ A–Z và 0–9, tức 36 ký tự.** Em cố ý không thu hẹp charset ở tầng mô hình, mà đặt ràng buộc hợp lệ ở tầng hậu xử lý — nơi có thể sửa được và ghi log được.

**Nếu bị hỏi sâu — vì sao đây là quyết định quan trọng.**

Mệnh đề phổ biến là *"biển số Việt Nam chỉ dùng 20 chữ cái, 6 chữ I J O Q R W không bao giờ xuất hiện"*. Con số 6 này là **suy diễn số học** (26 − 20 = 6) và **không chính xác**.

Theo Thông tư 79/2024, danh sách chữ cái ở **vị trí thứ hai** của seri xe mô tô là:

```
A B C D E F H K L M N P R S T U V X Y Z
```

Danh sách này **có R** và **không có G** — khác với danh sách 20 chữ ở vị trí thứ nhất. Tập loại trừ chắc chắn chỉ gồm **5 chữ: I, J, O, Q, W**.

Ngoài ra chữ R còn xuất hiện trong ký hiệu seri đặc biệt: `R` và `RM` dành cho rơ moóc, sơ mi rơ moóc.

**Hậu quả nếu tin nhầm:** xây charset OCR 20 chữ ⇒ mô hình **không bao giờ dự đoán được ký tự R** ⇒ sai hệ thống trên cả một lớp biển xe máy. Và đây là loại lỗi **hậu xử lý không cứu được**, vì thông tin đã mất ngay ở tầng mô hình.

Ba mức xử lý em khuyến nghị:
1. Charset nhận dạng dùng đủ 36 ký tự, để mô hình tự do dự đoán;
2. Ràng buộc hợp lệ áp ở tầng hậu xử lý bằng regex;
3. Nếu bắt buộc thu hẹp, dùng **21 chữ cái** = 20 ∪ {R}: `[A-HK-NPR-VXYZ]`.

**Trung thực về giới hạn kiểm chứng:** em **chưa đối chiếu được toàn văn Điều 34 Thông tư 79/2024** — bản PDF chính thức trên `datafiles.chinhphu.vn` là bản scan không có lớp text, còn `thuvienphapluat.vn` chặn truy cập tự động (HTTP 403). Vì vậy hai danh sách chữ cái em coi là **giả thuyết có căn cứ, chưa chốt**. Nhưng quyết định kỹ thuật thì không phụ thuộc vào việc chốt được hay không: charset 36 ký tự an toàn trong mọi trường hợp.

**Cảnh báo.** Nếu ai đó trong hội đồng khẳng định "6 chữ bị loại", **đừng phản bác thẳng thừng**. Nói: *"Em cũng ghi nhận con số 6 lúc đầu, nhưng khi đối chiếu danh sách chữ cái vị trí thứ hai của seri xe máy thì thấy có R. Vì rủi ro nghiêng hẳn về một phía — thiếu R thì mất cả một lớp biển, còn thừa R thì hậu xử lý lọc được — nên em chọn phương án an toàn là charset đủ."*

---

### D7. Nếu định dạng biển số thay đổi thì sao?

**Trả lời ngắn.**
Hệ thống chịu được, vì em tách kiến trúc theo đúng nguyên tắc này: **mô hình không mã hoá định dạng, chỉ hậu xử lý mới mã hoá**. Detector chỉ tìm hình chữ nhật; OCR chỉ đọc 36 ký tự; toàn bộ tri thức về định dạng Việt Nam nằm trong `plate_rules.py`. Đổi định dạng thì sửa một file luật, không phải huấn luyện lại mô hình.

**Nếu bị hỏi sâu.**
Đây không phải giả thuyết — nó **đã xảy ra trong lúc em làm đồ án**: Thông tư 51/2025 thay toàn bộ phụ lục mã tỉnh sau sáp nhập, còn 34 tỉnh/thành. Em chỉ phải cập nhật bảng mã tỉnh, không phải chạm vào mô hình.

Còn một nhánh dự phòng nữa: biển không khớp định dạng vẫn được **lưu lại**, chỉ bị đánh dấu `is_valid_format = False`. Không im lặng vứt bỏ dữ liệu — vì chính những trường hợp này là nguồn phân tích lỗi quý giá.

---

### D8. Có xử lý được biển bẩn, mờ, nghiêng, ban đêm không?

**Trả lời ngắn.**
Về augmentation thì có chuẩn bị: `hsv_v = 0,4` cho ảnh đêm và ngược sáng, `perspective` cho ảnh lệch trục, `erasing = 0,4` cho biển bị che bởi bùn và giá đỡ. Nhưng em phải nói thẳng: **chưa đo được** độ chính xác theo từng điều kiện ảnh, vì bộ dữ liệu không có nhãn điều kiện.

**Cảnh báo.** Đây là NFR-A9 và em đã đặt nó là "báo cáo **nếu** dữ liệu có nhãn phù hợp" ngay từ Phase 0 — tức là em biết trước ràng buộc này, không phải phát hiện muộn. Nói rõ điều đó.

---

## E. Về kiến trúc và cài đặt

### E1. Vì sao tách tầng AI khỏi tầng API? Có cần thiết không?

**Trả lời ngắn.**
Cần, và em có thể kiểm chứng bằng một lệnh. Tầng `ai/inference/` là Python thuần, **cấm import FastAPI hoặc Pydantic** — kiểm tra bằng `grep -r "fastapi\|pydantic" ai/inference/`, phải ra rỗng. Ba lợi ích cụ thể: kiểm thử được độc lập (104 unit test cho tầng AI chạy mà không cần dựng server), tái dùng được trong script huấn luyện và đánh giá, và thay được engine OCR mà không sửa mã tầng API.

**Nếu bị hỏi sâu.**
- Trong sơ đồ kiến trúc, khối Tầng AI **không có mũi tên nào đi lên**. Nó không biết gì về HTTP, về cơ sở dữ liệu, hay về việc ai gọi nó.
- Ràng buộc này chính là thứ giúp em trả lời câu D1 một cách tự tin: nếu benchmark cho thấy EasyOCR tốt hơn thì thay `PlateRecognizer` là xong, không đụng tới backend.
- Cái giá phải trả: thêm một lớp gián tiếp, và phải định nghĩa kiểu dữ liệu trung gian riêng (`ai/inference/types.py`) thay vì dùng thẳng Pydantic model.

---

### E2. Vì sao dùng SQLite mà không PostgreSQL?

**Trả lời ngắn.**
Vì mục tiêu triển khai là một lệnh `docker compose up`, và SQLite không cần một dịch vụ riêng. Nhưng em phải nêu rõ **hạn chế đã biết**: SQLite chỉ cho phép **một tiến trình ghi tại một thời điểm**. Với quy mô đồ án thì chấp nhận được; nếu triển khai thật với nhiều người dùng ghi đồng thời thì phải chuyển sang PostgreSQL.

**Nếu bị hỏi sâu.**
- Hạn chế này em ghi vào tài liệu yêu cầu phi chức năng từ Phase 0, kèm nguyên văn dòng "đây là câu hỏi phản biện rất dễ gặp". Không phải phát hiện muộn.
- Chi phí chuyển đổi thấp vì em dùng SQLAlchemy ORM và Alembic migration — đổi connection string là chính, cộng kiểm tra vài chỗ dùng cú pháp riêng của SQLite.
- Ảnh và video **không** lưu dưới dạng BLOB mà lưu file trên đĩa, chỉ giữ đường dẫn trong cơ sở dữ liệu (quyết định AD-07). Tránh phình cơ sở dữ liệu, và cũng làm việc chuyển sang PostgreSQL dễ hơn.
- Chỉ tiêu NFR-SC2 đặt ở ≥ 100.000 bản ghi mà không suy giảm hiệu năng — nhưng **chưa kiểm chứng**, thuộc Phase 7.

---

### E3. Hệ thống chịu được bao nhiêu người dùng đồng thời?

**Trả lời ngắn.**
**Đã đo — NFR-SC1 đạt.** Chỉ tiêu ≥ 5 yêu cầu đồng thời; đo được **10** yêu cầu đồng thời không lỗi (0 lỗi ở mọi mức 1/2/5/10). Soak 300 giây: 100% thành công (1.684 request), không rò rỉ bộ nhớ.

**Nếu bị hỏi sâu.**
- **Nút thắt là suy luận CPU, không phải tầng web.** Một ảnh mất ~180 ms suy luận thuần (detect 60 ms + OCR 112 ms/biển). Với CPU 14 nhân, số yêu cầu song song bị chặn bởi số luồng dành cho suy luận — thêm worker uvicorn không giúp gì, chỉ tranh nhau cùng nhân CPU.
- **Hệ thống xuống cấp nhã nhặn**: ở mức đồng thời 10, độ trễ tăng tuyến tính nhưng **0 lỗi** — không timeout, không HTTP 5xx.
- **Video được thiết kế để không chặn**: xử lý bất đồng bộ, trả `202 Accepted` kèm `job_id` ngay. Bắt buộc bởi NFR-SC3.

**Số liệu thời gian thực.** NFR-P2 = **5,257 FPS** (sàn 3, mục tiêu 5) và NFR-P3 = **0,785×** thời gian thực, đo trên `best.pt` qua HTTP thật ngày 13/08. Dưới tải cạnh tranh nặng, xấu nhất đo được là 4,057 FPS — vẫn trên sàn. Nếu bị hỏi vì sao khác con số 2,379 từng ghi: xem mục 5.6.4, phép đo cũ chạy khi máy đang tải nặng và harness đã tự dán nhãn *bi quan*.

---

### E4. Vì sao chế độ thời gian thực dùng HTTP mà không WebSocket?

**Trả lời ngắn.**
Vì WebSocket không giải quyết được nút thắt thật. Với chỉ tiêu ~5 FPS trên CPU, **thời gian suy luận mới là nút thắt** — khoảng 300–400 ms mỗi khung hình, so với vài mili-giây overhead của HTTP. WebSocket sẽ thêm quản lý trạng thái kết nối, logic kết nối lại và độ phức tạp khi debug mà không cải thiện được điều gì.

**Nếu bị hỏi sâu.**
- Đây là quyết định AD-03, có ghi rõ đánh đổi: nếu cần FPS cao hơn thì phải chuyển WebSocket.
- Em ghi luôn điều kiện thay đổi quyết định: *nếu Phase 7 đo được và chứng minh HTTP là nút cổ chai thì sẽ xem xét lại*. Và bản thân phép đo đó là một nội dung tốt cho chương Đánh giá.
- Điểm phương pháp luận đáng nêu: một quyết định kiến trúc nên đi kèm **điều kiện để đảo ngược nó**, chứ không chỉ đi kèm lý do chọn.

---

### E4b. Vì sao giao diện không còn trang Webcam? Có phải làm không được?

**Trả lời ngắn.**
Không. Đây là **quyết định thu gọn phạm vi giao diện** ngày 2026-07-20, không phải một chức năng thất bại. Trang Webcam đã từng được cài đặt đầy đủ và chạy được; em gỡ nó khỏi giao diện để phần demo gọn lại quanh nghiệp vụ chính. **Năng lực thời gian thực vẫn còn nguyên ở tầng API**: endpoint `POST /api/detect/frame` không thay đổi một dòng nào, vẫn có kiểm thử tự động và vẫn nằm trong kế hoạch đo NFR-P2.

**Nếu bị hỏi sâu.**
- **Về yêu cầu:** trong sáu nhóm yêu cầu chức năng, nhóm FR-3 có 5 yêu cầu. Hai yêu cầu **thuần giao diện** — FR-3.1 (xin quyền và hiển thị luồng camera) và FR-3.4 (vẽ chồng bounding box lên khung hình trực tiếp) — chuyển mức ưu tiên từ *Must* sang *Won't* cho bản này. Ba yêu cầu còn lại — FR-3.2 (nhận và xử lý từng khung), FR-3.3 (nhận dạng trên khung trực tiếp), FR-3.5 (lưu lịch sử phiên có gộp trùng theo `job_id`) — **vẫn là Must và vẫn được đáp ứng**, chỉ là kiểm chứng ở mức API thay vì qua giao diện.
- **Về khả năng khôi phục:** toàn bộ mã giao diện đã gỡ — trang `WebcamDetection`, thư mục `components/detection/webcam/`, hook `useFrameCaptureLoop` và hàm gọi `detectFrame` — **còn nguyên trong lịch sử git**. Khôi phục là thao tác phục hồi, không phải xây mới. Em ghi nó ở phần Hướng phát triển.
- **Nếu hội đồng muốn xem chạy thật:** em demo được ngay bằng một lệnh gọi API (Bước 6 của kịch bản demo) hoặc qua Swagger tại `localhost:8000/docs`.
- **Điểm đáng nêu về kiến trúc:** việc gỡ được một trang giao diện mà **không đụng một dòng nào** ở tầng API, tầng nghiệp vụ hay tầng AI chính là bằng chứng thực tế cho nguyên tắc tách tầng mà em trình bày ở Chương 4.

**Cảnh báo.** Đừng nói "em bỏ vì không kịp làm" — sai sự thật, vì trang đã từng chạy được. Cũng đừng nói lảng như thể hệ thống chưa bao giờ có phần này. Nói đúng: **đã làm, đã chạy được, chủ động thu gọn khỏi giao diện, năng lực giữ ở API.**

---

### E4c. ⚠️ Vì sao đồ án bỏ hẳn một yêu cầu mức *Must* (FR-4.1 — Dashboard)?

> **Đây là câu hỏi khó nhất trong nhóm E, và nó có thể được đặt ra ngay khi hội đồng đối chiếu
> bảng yêu cầu chức năng với giao diện đang chiếu. Chuẩn bị để nói TRƯỚC, đừng đợi bị hỏi.**

**Trả lời ngắn.**
Em xác nhận: ngày 2026-07-20 em gỡ trang **Tổng quan (Dashboard)** khỏi giao diện, và điều đó đưa **FR-4.1 từ *Must* xuống *Won't*** — **lần đầu tiên** trong đồ án một yêu cầu mức bắt buộc bị đưa ra khỏi phạm vi (FR-4.2 mức *Should* cũng chuyển sang *Won't* theo). Đây là **quyết định thu gọn phạm vi demo do em chủ động đưa ra**, không phải một chức năng làm không được: trang đã được cài đặt đầy đủ, đã chạy thật, và toàn bộ mã của nó — `pages/Dashboard.tsx`, thư mục `components/dashboard/` (10 tệp), hook `useApi.ts` — **còn nguyên trong lịch sử git**.

**Nếu bị hỏi sâu — bốn điều, theo thứ tự.**

**(1) Năng lực số liệu KHÔNG mất, chỉ mất màn hình hiển thị.**
Endpoint `GET /api/statistics` và `GET /health` **vẫn phục vụ, không đổi một dòng nào**, và vẫn có kiểm thử tích hợp trong bộ test (`tests/integration/test_api_statistics.py`, `test_api_health.py`). Hội đồng muốn xem số liệu tổng hợp thì em gọi API tại chỗ — đó chính là Bước 3 trong kịch bản demo, một lời gọi `curl` hoặc một lần bấm *Try it out* trên Swagger.

**(2) Phần Lịch sử — nơi chứa 6 trong 8 yêu cầu của nhóm FR-4 — không đổi.**
FR-4.3 đến FR-4.8 (phân trang, tìm kiếm khớp một phần, lọc đa tiêu chí, xem chi tiết, tải về, sắp xếp) đều thuộc trang Lịch sử và **giữ nguyên mức ưu tiên, giữ nguyên tình trạng đáp ứng**. Cái mất là hai yêu cầu *trình bày* số liệu, không phải năng lực tra cứu.

**(3) Đánh đổi đo được, không phải cảm tính.**
Gỡ trang kéo theo gỡ thư viện biểu đồ `recharts`: gói tải về của giao diện giảm từ **~730 KB xuống 328,8 KB — giảm 55%**. Với một hệ thống mà ràng buộc chi phối là chạy trên máy không GPU và mạng nội bộ, đó là một đánh đổi có lợi đo được.

**(4) Bảng MoSCoW sau thay đổi — em nói thẳng con số.**
34 yêu cầu chức năng: **21 Must · 6 Should · 3 Could · 4 Won't**. Bốn yêu cầu *Won't* là FR-3.1, FR-3.4 (gỡ trang Webcam) và FR-4.1, FR-4.2 (gỡ trang Tổng quan) — cả bốn đều **thuần giao diện**, không có yêu cầu nào ở tầng xử lý hay tầng dữ liệu bị bỏ.

**Nếu hội đồng hỏi "vậy đồ án có còn đạt không, khi thiếu một Must?"**
Trả lời: *"Theo đúng định nghĩa MoSCoW mà em chốt ở Phase 0 thì một Must bị thiếu là một khiếm khuyết, và em không né điều đó. Cái em xin trình bày là bản chất của khiếm khuyết này: nó nằm ở tầng trình bày, năng lực bên dưới còn nguyên và kiểm chứng được ngay tại đây, và việc khôi phục là một thao tác phục hồi từ git chứ không phải xây mới. Nếu hội đồng yêu cầu, em khôi phục lại trang trước ngày nộp."*

**Cảnh báo — bốn cách trả lời SAI:**

| ❌ Cách nói sai | Vì sao hỏng |
|---|---|
| *"Dashboard không cần thiết ạ"* | Nói tránh, và **tự mâu thuẫn**: chính em đặt nó là *Must* ở Phase 0. Hạ giá một yêu cầu sau khi bỏ nó là sửa tiêu chuẩn cho vừa kết quả — hội đồng nhìn ra ngay. |
| *"Em không kịp làm"* | **Sai sự thật.** Trang đã chạy được, còn trong lịch sử git. Nói sai một chi tiết kiểm chứng được sẽ khiến mọi khẳng định khác bị nghi ngờ. |
| *"Số liệu vẫn có trong CSDL mà"* (rồi dừng) | Đúng nhưng **né trọng tâm**. Câu hỏi là về *yêu cầu bị bỏ*, không phải về nơi cất dữ liệu. Phải nói rõ đây là khiếm khuyết có thật, rồi mới nói phạm vi của nó. |
| Im lặng không nhắc, đợi hội đồng phát hiện | Tệ nhất. Một khiếm khuyết **tự khai** là một quyết định phạm vi; cũng khiếm khuyết đó **bị bắt** là một chỗ giấu giếm. |

**Cách nói đúng, một câu:** *"Em chủ động gỡ trang Tổng quan để thu gọn phạm vi demo. Hệ quả là FR-4.1 — một yêu cầu mức Must — chuyển sang Won't, và em nêu thẳng chứ không giấu. Trang đã từng chạy thật và còn trong lịch sử git; endpoint thống kê vẫn phục vụ và vẫn có kiểm thử; đổi lại gói tải về giảm 55%."*

---

### E5. Vì sao không làm xác thực người dùng?

**Trả lời ngắn.**
Vì em đặt giả định triển khai là hệ thống chạy **nội bộ** (giả định A-04), nên mô hình đe doạ ở mức hạn chế và xác thực nằm ngoài phạm vi đã chốt ở Phase 0. Đây là lựa chọn phạm vi có ý thức chứ không phải bỏ sót.

**Nếu bị hỏi sâu — những gì em vẫn làm dù không có xác thực:**

| Yêu cầu | Cơ chế |
|---|---|
| NFR-S1 | Kiểm tra file tải lên bằng **magic bytes**, không tin phần mở rộng |
| NFR-S2 | Chống path traversal — tên file sinh lại bằng **UUID**, không dùng tên gốc |
| NFR-S3 | Giới hạn kích thước file, thực thi ở tầng server, vượt hạn mức ⇒ HTTP 413 |
| NFR-S4 | CORS chỉ cho phép origin đã khai báo, **không dùng `*`** |
| NFR-S6 | Truy vấn cơ sở dữ liệu luôn tham số hoá qua ORM, không nối chuỗi SQL |

Nếu triển khai ra ngoài mạng nội bộ thì xác thực là việc bắt buộc đầu tiên — xem câu E6.

---

### E6. Nếu deploy thật thì cần sửa gì?

**Trả lời ngắn.**
Sáu việc, theo thứ tự ưu tiên: thêm xác thực và phân quyền, chuyển SQLite sang PostgreSQL, chạy kiểm thử chịu tải thật, xuất mô hình sang ONNX Runtime để giảm độ trễ, làm rõ giấy phép dữ liệu, và thêm giám sát hiệu năng.

**Nếu bị hỏi sâu.**

| # | Việc | Vì sao ở vị trí đó |
|---|---|---|
| 1 | Xác thực + phân quyền | Không có thì bất kỳ ai truy cập được mạng đều xem được toàn bộ lịch sử biển số — đây là dữ liệu có thể truy vết cá nhân |
| 2 | SQLite → PostgreSQL | Một tiến trình ghi tại một thời điểm là giới hạn cứng |
| 3 | Chuyển bộ phát hiện sang OpenVINO | Đã đo: nhanh **1,57×**, mAP không giảm, đầu cuối +20% FPS — chỉ còn là quyết định bật |
| 4 | Trần thời gian cho bậc thang thử-lại | Đường cắt đuôi độ trễ NFR-P1 mà không mất 34 biển đã mua được |
| 5 | Giấy phép dữ liệu | Bộ dữ liệu hiện không ghi rõ giấy phép |
| 6 | Giám sát | Cần biết mô hình xuống cấp khi phân phối dữ liệu thật lệch khỏi tập huấn luyện |

---

### E7. Docker đã chạy được chưa?

**Trả lời ngắn.**
Chưa build thật. Em có Dockerfile cho cả backend và frontend, có `docker-compose.yml`, có cấu hình nginx, và `docker compose config` xác nhận cấu hình hợp lệ. Nhưng **chưa chạy `docker build` lần nào**, nên em không thể khẳng định `docker compose up` chạy được.

**Cảnh báo.** Đây là điểm yếu thật, đừng tô hồng. Cách thừa nhận: *"Cấu hình hợp lệ về cú pháp nhưng chưa kiểm chứng bằng build thật. Em không dám nói nó chạy được. Bù lại, cả backend lẫn frontend đều đã chạy và kiểm chứng bằng HTTP thật ở môi trường phát triển — 10 endpoint phản hồi đúng, frontend build thành công."*

Nếu hội đồng hỏi "vì sao chưa build?" — trả lời trung thực: ưu tiên còn lại dồn vào việc hoàn thành huấn luyện và tích hợp OCR, vì đó là phần lõi. Docker là phần đóng gói, làm sau được.

---

### E8. Vì sao cơ sở dữ liệu của em khác đặc tả ban đầu?

**Trả lời ngắn.**
Vì đặc tả gốc có một thiếu sót làm sai thống kê. Schema gốc không có trường nhóm, nên **một ảnh chứa 3 biển số sẽ thành 3 bản ghi rời rạc** và `GET /api/statistics` sẽ đếm thành "3 lượt nhận dạng" thay vì "1 ảnh có 3 biển số". Em bổ sung `source_job_id` và bảng `DetectionJob`, và đã kiểm chứng bằng test: 1 ảnh 3 biển đếm ra **1 lượt**, không phải 3.

**Nếu bị hỏi sâu — sáu trường bổ sung, mỗi trường một lý do:**

| Trường | Lý do |
|---|---|
| `raw_ocr_text` | Lưu chuỗi OCR **trước** khi sửa regex. Không có trường này thì **không đo được** đóng góp của hậu xử lý (NFR-A5 vs A6) — mất luôn một đóng góp học thuật định lượng |
| `ocr_confidence` | Trường `confidence` gốc nhập nhằng giữa độ tin cậy phát hiện và độ tin cậy OCR. Tách ra mới phân tích lỗi được |
| `bbox_x/y/w/h` | Vẽ lại bounding box khi xem chi tiết mà không phải chạy lại mô hình |
| `is_valid_format` | Đánh dấu biển không khớp định dạng thay vì vứt bỏ |
| `plate_line_count` | Báo cáo độ chính xác tách theo biển 1 dòng / 2 dòng (NFR-A8) |
| `source_job_id` | Nhóm nhiều biển số về một lượt tải lên |

Kết quả: `detection_history` 18 cột, `detection_job` 11 cột, Alembic migrate xong và kiểm chứng bằng HTTP thật.

**Trường `raw_ocr_text` là trường em muốn nhấn mạnh nhất** — nó là thứ biến "chúng em có thêm bước sửa lỗi regex" thành một con số đo được.

---

## F. Về đánh giá và đo lường

### F1. Các chỉ số em dùng là gì? Công thức thế nào?

**Trả lời ngắn.**
Cho tầng phát hiện: Precision, Recall, F1, mAP@0.5 và mAP@0.5:0.95. Cho tầng nhận dạng: CER ở mức ký tự và exact-match ở mức chuỗi biển. Cho toàn trình: độ chính xác đầu-cuối, tức ảnh vào ra đúng chuỗi biển.

**Nếu bị hỏi sâu.**

| Chỉ số | Công thức | Ý nghĩa ở bài toán này |
|---|---|---|
| Precision | TP / (TP + FP) | Trong những biển mô hình báo, bao nhiêu là biển thật |
| Recall | TP / (TP + FN) | Trong những biển có thật, mô hình tìm ra bao nhiêu |
| F1 | 2PR / (P + R) | Dùng để **chọn ngưỡng confidence vận hành** |
| AP | Diện tích dưới đường cong Precision–Recall | Tổng hợp P và R trên mọi ngưỡng |
| mAP | Trung bình AP trên các lớp | Ở đây chỉ 1 lớp nên mAP = AP |
| CER | Khoảng cách Levenshtein / độ dài chuỗi thật | Sai bao nhiêu ký tự |

Một điểm phương pháp luận: em **luôn báo cáo P/R kèm ngưỡng confidence**, và ngưỡng đó chọn bằng cách dò theo F1. Báo cáo một cặp P/R mà không nói ngưỡng là báo cáo một con số vô nghĩa, vì có thể chọn ngưỡng để làm đẹp bất kỳ vế nào.

---

### F2. mAP@0.5 và mAP@0.5:0.95 khác nhau chỗ nào?

**Trả lời ngắn.**
mAP@0.5 tính AP ở một ngưỡng IoU duy nhất là 0,50 — nó hỏi *"có tìm ra biển không"*. mAP@0.5:0.95 lấy trung bình AP trên 10 ngưỡng IoU từ 0,50 đến 0,95 bước 0,05 — nó hỏi *"hộp có **bám sát** biển không"*. Chỉ số thứ hai chặt hơn nhiều.

**Nếu bị hỏi sâu — và đây là chỗ đáng nói vì nó đặc thù bài toán này.**

Với hệ thống của em, **câu hỏi thứ hai mới là câu hỏi thật**. Lý do: đầu ra của detector không đến tay người mà đến tay **một mô hình khác** — bộ OCR. Hộp lệch vài pixel làm mất một cạnh ký tự, và OCR đọc sai cả biển. Trong một bài toán phát hiện thông thường, hộp lệch nhẹ vẫn "đúng"; ở đây nó hỏng cả pipeline.

Đó chính là lý do em nâng trọng số `box` từ 7,5 lên **8,0** — một thay đổi nhỏ nhưng có lý do đặc thù dự án, và mAP@0.5:0.95 chính là chỉ số đo hiệu quả của thay đổi đó.

Số liệu thật minh hoạ khoảng cách: trên tập test v3, mAP50 = 0,983 nhưng mAP50-95 chỉ = 0,783. Chênh 0,200 — tức mô hình tìm ra biển rất tốt nhưng khớp box còn chỗ cải thiện.

---

### F3. ⚠️ Tốc độ xử lý bao nhiêu? Đo trên máy gì?

> **Bắt buộc nhắc phần cứng. Công bố FPS mà không kèm cấu hình là lỗi phương pháp luận.**

**Trả lời ngắn.**
**NFR-P1 đạt.** Độ trễ đầu-cuối một ảnh, đo trên `models/best.pt`, máy rảnh: **p95 = 731 ms** (client-side qua HTTP) và **780 ms** (in-process) — dưới mục tiêu 800 ms. Phần cứng: Intel Core i5-14600K, 14 nhân / 20 luồng, không GPU, torch CPU, imgsz 640, một ảnh mỗi lần gọi.

**Nếu bị hỏi "sao báo cáo đầu ghi 5.857 ms?" — đây là câu chuyện phương pháp luận đáng kể.**

Con số cũ 5.857 ms **sai**, và em đã truy ra ba nguyên nhân cộng dồn:
1. **Nhiễm do tải cạnh tranh:** đo khi một tiến trình huấn luyện chiếm ~793% CPU song song — p95 rơi đúng vùng mẫu bị nhiễm.
2. **Sai mô hình:** đo trên checkpoint epoch 7, không phải `best.pt`.
3. **Lỗi crop:** ảnh crop quá lớn khiến PaddleOCR chạy cả khối text-detection, đẩy OCR lên ~1322 ms/ảnh.

Đo lại trên máy rảnh với mô hình đúng: p95 về 731 ms. Giả thuyết "oneDNN/cold-start" bị bác bỏ (`enable_mkldnn=false`, cold-start p95 chỉ 176 ms vì pipeline warmup lúc khởi động). Giả thuyết "baseline vốn chậm" cũng bị bác bỏ (baseline đo client-side ra 763,75 ms, gần y hệt best.pt).

**Phân rã độ trễ đúng trên `best.pt` (T5.7b):**

| Bước | Đo thật | % tổng |
|---|---:|---:|
| Giải mã ảnh | 2,65 ms | 1,5% |
| YOLO11n @640 | 59,83 ms | **34,2%** |
| PaddleOCR (mỗi biển) | 112,55 ms | **64,3%** |
| Chuẩn hoá regex | 0,03 ms | 0,0% |

Con số cũ "OCR chiếm 93,3%" là tạo tác của lỗi crop. Trên `best.pt`, OCR chiếm **64,3%** — vẫn tốn nhất nhưng không còn áp đảo, nên tối ưu bộ phát hiện (34,2%) giờ mới có ý nghĩa.

**Bài học phương pháp luận đáng nêu:** một phép đo lấy trên hệ thống **đang có lỗi chưa biết** trông y hệt một phép đo hợp lệ — vẫn có cỡ mẫu, phân vị, biểu đồ. Thứ duy nhất phát hiện ra là **đo lại sau khi sửa lỗi** và thấy con số OCR dịch hơn 10 lần. Mọi con số hiệu năng em công bố kèm tên CPU, số luồng, imgsz và cỡ mẫu.

---

### F4. Làm sao biết bước hậu xử lý có tác dụng?

**Trả lời ngắn.**
Bằng cách lưu **cả hai** chuỗi vào cơ sở dữ liệu: `raw_ocr_text` là chuỗi OCR thô, `plate_number` là chuỗi sau chuẩn hoá. Chạy trên tập test có nhãn chuỗi, tính exact-match trên cả hai cột, và **hiệu số chính là đóng góp định lượng của khối hậu xử lý**. Đó là NFR-A5 so với NFR-A6 trong đặc tả của em.

**Nếu bị hỏi sâu.**
- Chỉ tiêu đặt: A5 (trước) ≥ 0,85, A6 (sau) ≥ 0,90 — tức kỳ vọng hậu xử lý đóng góp khoảng 5 điểm.
- **Đã đo (2.801 biển):** A5 = 0,6373, A6 = 0,7512 ⇒ **hiệu số +11,39 điểm** — **319 biển được sửa đúng, 0 biển bị làm hỏng** ở mức chuỗi. Đóng góp của hậu xử lý là dương và loss-free, đúng như thiết kế; nhưng cả A5 và A6 **đều dưới ngưỡng** vì biển 2 dòng kéo xuống (xem D1).
- Vì sao thiết kế này đáng nêu: nó biến một khẳng định định tính ("chúng em có thêm bước sửa lỗi") thành một con số kiểm chứng được. Em cũng trung thực về giới hạn: ở **mức ký tự**, bảng ánh xạ có hai luật sai đích (`L→1` phải là `L→4`, `7→T` phải là `7→Z`) làm lỗi bị dời chỗ chứ không bị xoá — chỉ lộ ra khi so ma trận nhầm lẫn trước/sau.

---

### F5. Vì sao báo cáo tách riêng biển 1 dòng và 2 dòng?

**Trả lời ngắn.**
Vì một con số mAP tổng **che giấu đúng thất bại cần nhìn**. Trên bộ RodoSol-ALPR (Brazil), OpenALPR đạt 94,3% trên biển 1 dòng và 45,7% trên biển 2 dòng — nếu chỉ báo cáo trung bình thì hệ thống trông khoẻ mạnh trong khi vô dụng với phần lớn phương tiện lưu thông ở Việt Nam. Đây là con số em nhìn **trước tiên**, không phải mAP tổng.

**Nếu bị hỏi sâu.**
- Tập nhãn OCR của em có **2.234 biển 2 dòng** trên tổng 2.801 (79,8%) — dư sức để con số tách nhóm có ý nghĩa thống kê. Kết quả thật: biển 1 dòng đạt A6 0,949 (vượt mục tiêu), biển 2 dòng chỉ 0,581 — chênh 36,8 điểm. Đúng thất bại mà một con số trung bình sẽ che giấu.
- `evaluate.py` in bảng `single_line / two_line / ALL` với N_GT, TP, FP, FN, P, R, F1, mAP50, mAP50-95, cộng một dòng khoảng cách AP giữa hai nhóm.
- Nếu khoảng cách vượt 10 điểm AP, script cảnh báo và khuyến nghị cân bằng dataset trước khi nghĩ tới mô hình lớn hơn.
- Ngưỡng phân nhóm 2,5 **cố ý trùng** với ngưỡng của tầng suy luận, để phép đánh giá mô tả đúng hệ thống thật.

---

### F6. Đánh giá trên tập nào? Vì sao không phải tập validation?

**Trả lời ngắn.**
Trên tập **test**, 458 ảnh. Tập val đã tham gia chọn checkpoint `best.pt` theo fitness từng epoch, nên báo cáo con số val là báo cáo một ước lượng lạc quan có thiên lệch. `--split` của script đánh giá mặc định là `test` đúng vì lý do này.

**Nếu bị hỏi sâu.**
Có một lớp kiểm chứng chéo: script chạy pass validation chính thức của Ultralytics để lấy mAP, đồng thời có bộ so khớp riêng của em để tính bảng tách nhóm. Hai nguồn kiểm chứng lẫn nhau — nếu chúng lệch nhau nhiều thì có lỗi ở một trong hai.

---

## G. Câu hỏi bẫy / câu hỏi khó

### G1. Em có dùng AI để viết code không?

**Trả lời ngắn.**
Có. Em dùng trợ lý AI trong quá trình làm, và em nghĩ giấu điều đó vừa không trung thực vừa không cần thiết. Điều quan trọng là em **hiểu và kiểm chứng được** từng quyết định trong hệ thống — thầy/cô có thể hỏi bất kỳ dòng cấu hình nào và em giải thích được vì sao nó có giá trị đó.

**Nếu bị hỏi sâu.**
- Cách em kiểm soát: mọi con số trong tài liệu đều đọc trực tiếp từ file do pipeline sinh ra, không có con số nào ước lượng bằng tay. Báo cáo dữ liệu có hẳn một bảng ánh xạ "số liệu ↔ file nguồn" ở đầu tài liệu.
- Em đã chạy một vòng phản biện có chủ đích trên tài liệu Phase 1 và **tìm ra 25 lỗi trong chính tài liệu của mình**, trong đó 3 lỗi nghiêm trọng (xem G4). Việc chủ động đi tìm lỗi trong sản phẩm của mình là bằng chứng em không tin mù quáng vào đầu ra.
- Trợ lý AI mạnh ở việc viết mã lặp lại và soạn tài liệu; nó **không** giúp được ở những chỗ khó nhất của đồ án: phát hiện Thông tư 24/2023 hết hiệu lực, phát hiện mệnh đề chữ R sai, phát hiện 73 cặp rò rỉ trong bản chia gốc. Những cái đó đến từ việc đối chiếu nguồn gốc và chạy phép đo.

**Cảnh báo.** Đừng chối. Nếu bị hỏi tiếp *"vậy phần nào là của em?"* — trả lời: *"Toàn bộ quyết định thiết kế và mọi phép kiểm chứng. Em có thể giải thích vì sao `fliplr` phải bằng 0, vì sao ngưỡng aspect ratio là 2,5, vì sao charset phải đủ 36 ký tự — và mỗi cái đều có bằng chứng đằng sau."* Rồi mời hội đồng hỏi bất kỳ chi tiết nào.

---

### G2. Nếu thay đổi Thông tư thì hệ thống còn đúng không?

> **Đây là câu ghi điểm mạnh nhất trong nhóm G. Chuẩn bị kỹ.**

**Trả lời ngắn.**
Chuyện đó **đã xảy ra ngay trong đề bài của em**. Đề bài dẫn Thông tư 24/2023/TT-BCA làm căn cứ pháp lý, nhưng khi em đối chiếu nguồn gốc ở Phase 1 thì phát hiện văn bản đó **đã hết hiệu lực từ 01/01/2025**. Em đã chuyển toàn bộ căn cứ sang Thông tư 79/2024/TT-BCA.

**Nếu bị hỏi sâu.**

Chuỗi văn bản hiện hành em đang dùng:

| Văn bản | Ngày | Hiệu lực | Nội dung với đồ án |
|---|---|---|---|
| ~~TT 24/2023/TT-BCA~~ | 01/7/2023 | ❌ **hết hiệu lực 01/01/2025** | Văn bản đề bài dẫn |
| **TT 79/2024/TT-BCA** | 15/11/2024 | 01/01/2025 | Cấu trúc biển, seri, màu sắc, ký hiệu |
| TT 13/2025/TT-BCA | 28/02/2025 | — | Sửa đổi TT 79/2024 |
| **TT 51/2025/TT-BCA** | 30/6/2025 | 01/7/2025 | **Thay toàn bộ Phụ lục mã tỉnh** sau sáp nhập, còn 34 tỉnh/thành |
| TT 81/2024/TT-BCA | — | 01/01/2025 | Ban hành kèm **QCVN 08:2024/BCA** — kích thước vật lý |

**Và đây chính là câu trả lời cho câu hỏi.** Em đã thiết kế kiến trúc để chịu được thay đổi này:
- Mô hình **không** mã hoá định dạng — detector chỉ tìm hình chữ nhật, OCR chỉ đọc 36 ký tự.
- Toàn bộ tri thức pháp lý nằm trong **một tầng duy nhất**: `ai/inference/plate_rules.py`.
- Khi TT 51/2025 thay phụ lục mã tỉnh, em chỉ cập nhật một bảng hằng số. Không huấn luyện lại gì cả.

**Cảnh báo.** Cách kể quan trọng hơn nội dung. Đừng nói theo kiểu "đề bài sai". Nói: *"Em phát hiện điều này khi đối chiếu nguồn pháp lý gốc, và em nghĩ nó có ích cho đồ án — nó buộc em phải thiết kế sao cho tri thức pháp lý tách khỏi mô hình."* Biến một phát hiện có thể gây khó xử thành một luận điểm thiết kế.

---

### G3. Phần nào trong đồ án này em thấy chưa hài lòng nhất?

**Trả lời ngắn.**
Việc **OCR biển 2 dòng không đạt chỉ tiêu** — đo được A4 0,873 / A5 0,610 / A6 0,656, đều dưới ngưỡng. Đây là con số quan trọng nhất với người dùng, và em trình bày trung thực chứ không tô hồng. Toàn bộ khoảng cách nằm ở biển 2 dòng (xe máy, 79,8% tập nhãn): biển 1 dòng vượt cả ba mục tiêu, biển 2 dòng kéo tổng xuống.

**Nếu bị hỏi sâu.**
- Nguyên nhân gốc là **kiến trúc OCR dòng đơn** (CRNN/CTC) đọc kém biển 2 dòng dù đã tách-rồi-ghép; đây là rủi ro R-04 em nêu từ đầu và nó bộc lộ đúng bằng số liệu Việt Nam thật.
- Em đang xử lý bằng 2 bộ Roboflow có nhãn ký tự trong đợt mở rộng lên ~21.000 ảnh.
- Điều em vẫn giữ được: **hạ tầng đo đã sẵn sàng**. Schema có `raw_ocr_text` tách khỏi `plate_number`, có `ocr_confidence` tách khỏi `confidence` phát hiện, có `plate_line_count`. Ngày có nhãn là đo được ngay, không phải sửa gì.

**Cảnh báo.** Nếu hội đồng đã hỏi câu này thì họ **đang cho em cơ hội tự nói ra điểm yếu**. Trả lời thẳng và cụ thể sẽ tốt hơn nhiều so với chọn một điểm yếu vô hại kiểu "giao diện chưa đẹp lắm ạ". Chọn điểm yếu thật, rồi cho thấy em hiểu nguyên nhân và có hướng xử lý.

---

### G4. Em có tự tìm ra lỗi nào trong công việc của mình không?

**Trả lời ngắn.**
Có. Em chạy một vòng phản biện có chủ đích trên tài liệu Phase 1 và tìm ra **25 lỗi**, trong đó **3 lỗi nghiêm trọng**. Em nghĩ chuyện này đáng kể hơn phần nào so với việc không có lỗi nào — vì có lỗi mà tìm ra được thì hơn có lỗi mà không biết.

**Nếu bị hỏi sâu — ba lỗi nghiêm trọng:**

| # | Lỗi | Hậu quả nếu không phát hiện |
|---|---|---|
| 1 | **Số liệu kích thước biển số dùng tiêu chuẩn cũ và trích sai nguồn** | Toàn bộ ngưỡng phân loại 1 dòng / 2 dòng suy ra từ số liệu sai |
| 2 | **Mệnh đề "6 chữ I J O Q R W không bao giờ xuất hiện" là sai** — chữ R hợp lệ ở vị trí thứ hai của seri xe máy | Charset OCR 20 chữ ⇒ mô hình không bao giờ đoán được R ⇒ sai hệ thống trên cả một lớp biển xe máy, và **hậu xử lý không cứu được** |
| 3 | **7 trích dẫn về 7 gói phần mềm khác nhau đều trỏ về cùng một URL** | Dấu hiệu bịa trích dẫn — nếu hội đồng mở link ra kiểm tra thì phá hỏng uy tín của cả chương lựa chọn công nghệ |

Cộng thêm một phát hiện nữa cùng loại: hai số liệu em từng dùng để biện minh cho PaddleOCR hoá ra đến từ một bài dùng **EasyOCR** — chi tiết ở câu D1.

**Cảnh báo.** Đây là câu **ghi điểm**, không phải câu phòng thủ. Nó cho thấy em có kỷ luật kiểm chứng. Nhưng đừng kể lể quá dài — nêu 3 lỗi, giải thích lỗi thứ 2 kỹ nhất vì nó có hậu quả kỹ thuật rõ ràng nhất.

---

### G5. Nếu làm lại từ đầu em sẽ làm khác gì?

**Trả lời ngắn.**
Ba việc. Một, **chốt nguồn dữ liệu có nhãn chuỗi biển số trước tiên** — em mất nhiều thời gian vào hạ tầng detection rồi mới phát hiện nhánh OCR không có dữ liệu để đo. Hai, **kiểm chứng bộ dữ liệu tải được thật trước khi lập kế hoạch dựa trên nó** — bộ VNLP 37.300 ảnh em chốt ở Phase 1 hoá ra trả HTTP 401. Ba, **tự chạy benchmark ba engine OCR sớm** thay vì chọn theo tài liệu.

**Nếu bị hỏi sâu.**
- Bài học chung của cả ba: em lập kế hoạch dựa trên **tài liệu công bố** thay vì dựa trên **thứ đã kiểm chứng được trên máy mình**. Bộ dữ liệu công bố 37.300 ảnh nhưng tải về được 0. Bảng benchmark công bố nhưng đo trên EC2 P4d, không phải máy em. Bài báo công bố PaddleOCR tốt nhưng thực tế bài đó dùng EasyOCR.
- Nguyên tắc em rút ra và đã áp dụng cho phần còn lại: **một con số chỉ được dùng nếu tái lập được từ kho mã hiện tại**. Đó là lý do em loại bảng benchmark CPU cũ dù nó nằm sẵn trong README.

---

### G6. Em mất bao lâu để làm?

**Trả lời ngắn.**
Đồ án chia theo 10 giai đoạn, và hiện em đang ở giai đoạn cuối với hai việc còn chạy: huấn luyện và tích hợp OCR. Phần chiếm thời gian nhiều nhất ngoài dự kiến là **khảo sát nguồn pháp lý và kiểm chứng trích dẫn** — vì phát hiện văn bản căn cứ hết hiệu lực buộc em phải làm lại toàn bộ phần đó.

**Nếu bị hỏi sâu.**
- Phần tốn thời gian thứ hai ngoài dự kiến: xây pipeline dữ liệu tái lập được. Nhìn qua thì chỉ là "tải về rồi chia", nhưng bước chuyển polygon → bounding box và bước chống rò rỉ mới là chỗ mất công — và cũng là chỗ bắt được lỗi thật.
- Phần nhanh hơn dự kiến: backend và frontend, vì kiến trúc 5 tầng đã chốt rõ từ Phase 0 nên lúc cài đặt gần như không phải quay lại sửa thiết kế.

---

### G7. Nếu bây giờ em phải demo trực tiếp mà hệ thống lỗi thì sao?

**Trả lời ngắn.**
Em có ảnh chụp màn hình **cả 3 trang** giao diện trong `docs/screenshots/` (`image-detection` · `video-detection` · `history`), và có thể trình bày kết quả từ file `results.csv` sinh ra tự động. Nhưng nếu demo lỗi thì em sẽ nói thẳng nó lỗi ở đâu — em quen với hệ thống đủ để chẩn đoán tại chỗ.

**Cảnh báo.** Chuẩn bị trước: mở sẵn backend và frontend **trước khi vào phòng**, có sẵn 2–3 ảnh test đã biết chắc chạy được, và có sẵn tab Swagger. Đừng để lần chạy đầu tiên của buổi bảo vệ là lần khởi động server.

⚠️ **Chụp lại 3 ảnh này trước khi nộp.** Bản đang có chụp lúc sidebar còn **5 mục** và trang chủ còn là **Tổng quan**. Nếu phải dùng ảnh cũ làm phương án dự phòng mà hội đồng để ý thấy khác giao diện đang mô tả, hãy nói thẳng: *"Ảnh này chụp trước khi em thu gọn giao diện ngày 20/7, hiện giao diện còn 3 trang — nhận dạng ảnh, nhận dạng video và lịch sử."*

---

### G8. Đây có phải là hệ thống thật sự dùng được không, hay chỉ là bài tập?

**Trả lời ngắn.**
Nó là một hệ thống chạy được nhưng **chưa phải sản phẩm triển khai được**. Chạy được: backend 10 endpoint đã kiểm chứng bằng HTTP thật, frontend build thành công và gọi được cả 10 endpoint, cơ sở dữ liệu migrate xong. Chưa triển khai được: chưa có xác thực, chưa kiểm thử chịu tải, Docker chưa build thật, và giấy phép dữ liệu chưa rõ.

**Cảnh báo.** Đây là câu hỏi thử độ trung thực. Trả lời "dùng được ngay ạ" là hỏng. Trả lời "chỉ là bài tập thôi ạ" là tự hạ thấp. Câu trả lời đúng nằm ở giữa và phải **cụ thể về ranh giới**.

---

## Ba câu dễ trả lời sai nhất

> Đọc lại mục này ngay trước khi vào phòng.

---

### 🥇 Câu 1 — "mAP 0,983 cao thế, có rò rỉ dữ liệu không?" (C3)

**Vì sao dễ hỏng.** Đây là câu duy nhất mà một câu trả lời sai làm **mất hết uy tín của toàn bộ phần thực nghiệm**. Nếu hội đồng tin rằng có rò rỉ, thì mọi con số khác em trình bày đều trở nên vô nghĩa.

**Ba cái bẫy cụ thể:**

| Bẫy | Vì sao sai |
|---|---|
| Nói *"em cũng không rõ vì sao cao thế"* | Thừa nhận không kiểm soát được kết quả của chính mình |
| Nói *"model của em tốt lắm ạ"* | Không có nội dung, và mời hội đồng đào sâu |
| **Nhầm overfit với rò rỉ** | Đây là **hai cáo buộc khác nhau**. Overfit = học thuộc train, kém trên val. Rò rỉ = val bị ô nhiễm bởi train. Trả lời nhầm cái nọ sang cái kia lộ ra rằng em không phân biệt được hai khái niệm cơ bản. |

**Bốn thứ phải nói, theo đúng thứ tự:**
1. Con số công bố **0,983** đo trên **test v3 đã khử trùng lặp ở ngưỡng phash 10** (v2 có 9.126 cặp vắt split, v3 có 0), bằng mô hình `best.pt` train đúng trên chính split v3.
2. Em **không** lấy baseline (train trên v1) đo trên test v3 — vì 289/1.514 ảnh (19,1%) trùng tên tệp; và em **vứt bỏ bản chia gốc của tác giả** vì phát hiện rò rỉ.
3. **Trung thực về giới hạn:** phash không bắt được rò rỉ ngữ nghĩa (cùng xe/khác ngày), nên em nói "không còn bị rò rỉ tên-tệp thổi phồng" chứ không nói "sạch tuyệt đối"; test xuyên bộ dữ liệu là món nợ còn lại.
4. Bài toán detection này vốn dễ: **1 lớp**, đối tượng tương phản cao. Tách layout: 1 dòng 0,988 vs 2 dòng 0,968 — chênh chỉ 2,09 điểm, dấu hiệu khái quát hoá chứ không học thuộc.

**Câu chốt:** *"mAP50-95 chỉ 0,783 — chênh 0,20 so với mAP50. Nếu mô hình học thuộc tập test thì chỉ số chặt này cũng phải sát 0,98 — nó không. Và điểm yếu thật của hệ thống nằm ở OCR biển 2 dòng, em không giấu bằng một con số trung bình."*

---

### 🥈 Câu 2 — "Vì sao chọn PaddleOCR? Đã so sánh chưa?" (D1)

**Vì sao dễ hỏng.** Vì có sẵn hai câu trả lời nghe rất thuyết phục mà **cả hai đều dựa trên số liệu đã bị bác bỏ**. Nếu em trích chúng và hội đồng mở bài gốc ra đọc, đó là lỗi trích dẫn sai nguồn — loại lỗi nặng nhất trong một đồ án.

**Hai câu tuyệt đối không được nói:**
- ❌ *"Có nghiên cứu cho thấy YOLOv8 + PaddleOCR đạt 99%, cải thiện 4,16%"* — bài đó dùng **EasyOCR**; 99% là tỷ lệ **phát hiện** chứ không phải OCR; **không có con số 4,16% nào** trong bài.
- ❌ *"Hệ thống ANPR dùng PaddleOCR đạt 97%/95% trên 1000 ảnh"* — thực tế **99%/98% trên 270 ảnh**, cũng bằng **EasyOCR**. Cả ba thành phần đều sai.

**Cái bẫy thứ hai, tinh vi hơn:** cố bảo vệ PaddleOCR đến cùng. Sự thật là **so sánh kiểm chứng được duy nhất lại nghiêng về EasyOCR** (CER 0,09 so với 0,10), và IEEE ICCCNT 2024 cũng kết luận EasyOCR được ưa chuộng về độ chính xác. Cãi lại điều đó là tự đưa mình vào thế không thắng được.

**Ba thứ phải nói:**
1. PaddleOCR là **baseline**, không phải kết luận. Căn cứ chọn là **ràng buộc triển khai** (21 MB so với 200 MB), không phải độ chính xác.
2. **Không tồn tại benchmark công khai nào** so sánh ba engine trên riêng ảnh biển số xe máy Việt Nam 2 dòng — em đã tìm và ghi nhận đây là khoảng trống nghiên cứu.
3. Kiến trúc đặt bộ nhận dạng sau **interface trừu tượng** (NFR-M5) chính vì lý do này. Thay engine không phải sửa mã tầng API.

**Câu chốt khi bị dồn:** *"Nếu benchmark cho thấy EasyOCR tốt hơn thì em thay, và kiến trúc đã được thiết kế để việc thay đó chỉ tốn một file. Việc còn thiếu là em tự chạy benchmark — đó là việc đầu tiên em làm nếu tiếp tục."*

---

### 🥉 Câu 3 — "Tốc độ xử lý bao nhiêu?" (F3)

> ✅ **NFR-P1 ĐẠT.** Độ trễ E2E một ảnh trên `models/best.pt`, máy rảnh: **p95 = 731 ms** (client-side qua HTTP) / **780 ms** (in-process) — dưới mục tiêu 800 ms. Cấu hình: Intel i5-14600K, 14 nhân / 20 luồng, CPU-only, imgsz 640, một ảnh/lần, 100 mẫu. Nguồn: [07-benchmark-p1-resolved.json](../reports/07-benchmark-p1-resolved.json).

**Vì sao dễ hỏng.** Vì câu chuyện đúng ở đây là một câu chuyện phương pháp luận, và dễ trả lời hụt. Bản báo cáo đầu ghi **5.857 ms** (trượt) — nếu em nhắc con số đó mà không giải thích thì tự bắn vào chân.

**Con số cũ 5.857 ms sai vì ba nguyên nhân cộng dồn:**
1. **Nhiễm do tải cạnh tranh:** đo khi một tiến trình huấn luyện chiếm ~793% CPU song song.
2. **Sai mô hình:** checkpoint epoch 7, không phải `best.pt`.
3. **Lỗi crop:** ảnh crop quá lớn khiến PaddleOCR đọc ~1322 ms/ảnh, thổi phồng tỷ trọng OCR lên "93,3%".

Đo lại trên máy rảnh với mô hình đúng: p95 731 ms. Phân rã đúng (T5.7b): **OCR 64,3% (112,55 ms/biển) / detect 34,2% (59,83 ms)**.

**Cái bẫy: công bố con số mà không kèm cấu hình phần cứng.** Mọi con số hiệu năng phải kèm: **model CPU, số luồng, kích thước ảnh, backend, cỡ mẫu**.

**Bài học phương pháp luận đáng nêu:** một phép đo lấy trên hệ thống đang có lỗi chưa biết trông y hệt một phép đo hợp lệ — vẫn có cỡ mẫu, phân vị. Thứ duy nhất phát hiện ra là đo lại sau khi sửa lỗi.

**Câu chốt:** *"NFR-P1 đạt — p95 731 mili-giây. Bản báo cáo đầu ghi 5.857 nhưng con số đó là tạo tác của tải cạnh tranh, sai checkpoint và một lỗi crop; đo lại trên máy rảnh với mô hình chính thức thì về 731. Bài học của em là: một phép đo trên hệ thống có lỗi trông y hệt một phép đo đúng."*

---

## Phụ lục — Bảng số liệu tra nhanh

Để trả lời không phải lật tài liệu.

| Hạng mục | Số liệu |
|---|---|
| Ảnh (v3) | **15.133** · 6 nguồn nguyên tố (hợp nhất từ 7 bộ) |
| Chia tập (v3) | train **10.592** · val **3.027** · test **1.514** (khử trùng lặp ngưỡng 10) |
| Rò rỉ vắt split ở ngưỡng 10 | v2 = 9.126 cặp → **v3 = 0 cặp** |
| Dedup | phash 64-bit; ngưỡng chẵn (mọi hash 32 bit bật) |
| Mô hình chính thức | **`best.pt`** — YOLO11n, imgsz **640**, split v3, 20 epoch, box 8,0, fliplr 0, seed 42 |
| Detection (test v3, 1.514 ảnh) | mAP50 **0,983** · mAP50-95 **0,783** · P **0,984** · R **0,971** — đạt cả bốn |
| Detection tách layout | 1 dòng mAP50 0,988 · 2 dòng 0,968 · chênh **2,09 điểm** |
| OCR (2.801 biển) | A4 **0,945** đạt sàn · A5 **0,637** · A6 **0,751** — A5/A6 chưa đạt; A6−A5 = **+11,39 điểm** |
| OCR tách layout | 1 dòng A6 0,949 (đạt) · 2 dòng A6 0,581 · chênh **36,8 điểm** |
| NFR-P1 độ trễ E2E p95 | **731 ms** client / **780 ms** in-process (đạt, mục tiêu 800 ms) |
| Phân rã độ trễ | OCR **64,3%** (112,55 ms/biển) · detect **34,2%** (59,83 ms) |
| Đồng thời (SC1) | **10** yêu cầu, 0 lỗi · soak 300 s 100% |
| Phần cứng | Intel Core i5-14600K, 14 nhân / 20 luồng, **không có GPU CUDA** |
| Chỉ tiêu chính | mAP50 ≥ 0,90 · mAP50-95 ≥ 0,65 · E2E OCR ≥ 0,88 · p95 ≤ 800 ms |
| Biển 1/2 dòng — OpenALPR trên **RodoSol-ALPR (Brazil)** | 94,3% so với **45,7%** (chênh 48,6 điểm) · Laroca VISAPP 2022, `laroca_2022_crossdataset` · **số liệu Brazil, KHÔNG phải VN** |
| Ngưỡng AR phân loại | **2,5** — đáy vùng trũng quan sát được ở 2,2–2,6 |
| AR danh nghĩa QCVN 08:2024 | ô tô dài 4,727 · ô tô ngắn 2,000 · mô tô 1,357 |
| Charset OCR | **36 ký tự** A–Z + 0–9; tập loại trừ chắc chắn chỉ **5 chữ I J O Q W** |
| Căn cứ pháp lý | TT 79/2024 (sửa bởi TT 13/2025, TT 51/2025) + QCVN 08:2024/BCA |
| Cơ sở dữ liệu | `detection_history` 18 cột · `detection_job` 11 cột |
| Giao diện | **3 trang** — `/` Nhận dạng ảnh *(trang chủ)* · `/video` · `/history`; gói tải về **328,8 KB** (−55% sau khi gỡ `recharts`) |
| MoSCoW (34 FR) | **21 Must · 6 Should · 3 Could · 4 Won't** — Won't = FR-3.1, FR-3.4, **FR-4.1 (Must cũ)**, FR-4.2 |
| Unit test tầng AI | 104 (detector 30 · normalizer 29 · two_line 26 · recognizer 19) |
| Tài liệu tham khảo | 232 entry, 211 được trích dẫn |
| Lỗi tự phát hiện ở Phase 1 | **25 lỗi**, trong đó **3 nghiêm trọng** |
