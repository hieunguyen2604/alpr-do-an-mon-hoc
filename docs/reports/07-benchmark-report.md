# Báo cáo Phase 7 — Benchmark hiệu năng

**Ngày đo:** 19/07/2026 · **Cập nhật:** 20/07/2026 (đo lại NFR-P1 trên mô hình chính thức `models/best.pt`, giải quyết mâu thuẫn 5.857 ms ↔ ~780 ms)

> ### ✅ ĐỌC TRƯỚC: số liệu NFR-P1 chính thức đã được xác minh trên `models/best.pt`
>
> Toàn bộ số độ trễ ở các mục 3, 4, 5, 5bis dưới đây đo trên **checkpoint giữa
> chừng** `best-cpu-epoch7.pt` hoặc `baseline-416-v1.pt`, giữ lại để ghi lịch sử
> phép đo. **Số công bố cho NFR-P1 giờ đo trên mô hình chính thức `models/best.pt`**
> (YOLO11n, `imgsz=640`, split v3, 20 epoch). Nguồn xác minh:
> [`07-benchmark-p1-resolved.json`](07-benchmark-p1-resolved.json) và
> [`05-tables.md §T5.7`](05-tables.md).
>
> | | Bản đầu (epoch 7, máy bận) | **Chính thức (`best.pt`, máy rảnh)** |
> |---|---:|---:|
> | **NFR-P1** p95 (client-side qua HTTP) | 5.857,19 ms ❌ | **731,15 ms** ✅ |
> | **NFR-P1** p95 (in-process, T5.7a) | — | **780,36 ms** ✅ |
> | OCR mỗi biển | 1.322,40 ms | **112,55 ms** |
> | Tỷ trọng OCR / phát hiện | 93,3% / 6,5% | **64,3% / 34,2%** |
>
> **Vì sao con số cũ 5.857 ms sai:** (1) đo khi một tiến trình huấn luyện chiếm
> ~793% CPU song song — p95 rơi đúng vùng mẫu bị nhiễm; (2) đo trên checkpoint
> epoch 7 chứ không phải `best.pt`; (3) lỗi crop quá lớn khiến PaddleOCR đọc trên
> ảnh crop ~1322 ms/ảnh, thổi phồng tỷ trọng OCR lên 93,3%. Đo lại trên máy rảnh
> với `best.pt`, oneDNN đã tắt (`enable_mkldnn=false`) và pipeline warmup ngay lúc
> khởi động (cold-start p95 chỉ 176 ms): p95 chỉ còn ~731–780 ms. Giả thuyết
> "oneDNN/cold-start" và "baseline vốn chậm" **đều bị bác bỏ** (baseline đo
> client-side ra 763,75 ms, gần y hệt best.pt).
>
> Các mục 4.1–4.4, 5, 9.2, 9.3 và bảng ở 5bis được **giữ nguyên văn** để ghi lịch
> sử; **không trích dẫn số của chúng**. Số dùng được: bảng tóm tắt mục 2 (đã cập nhật).

**Kết quả một dòng (chính thức):** **NFR-P1 ĐẠT** — p95 = 731,15 ms client-side /
780,36 ms in-process, dưới mục tiêu 800 ms và ngưỡng tối thiểu 1.500 ms. Detection
trên `best.pt` đạt cả bốn chỉ tiêu (mAP@0.5 0,9829 / mAP@0.5:0.95 0,7834 / P 0,9837
/ R 0,9714). NFR-P2 (FPS webcam) và NFR-P3 (video) **chưa đo** trên `best.pt` — ghi
nhận là món nợ, không phải "không áp dụng".

---

## 1. Cấu hình phần cứng đã đo

> **Quy tắc bắt buộc của đồ án** (NFR mục 0): *"công bố một con số FPS mà không
> kèm cấu hình phần cứng là lỗi phương pháp luận"*. Bảng dưới đây do
> `platform` + `psutil` sinh tự động tại thời điểm đo và được nhúng vào **mọi**
> tệp kết quả JSON, không phải chép tay vào báo cáo về sau.

| Hạng mục | Giá trị đo được |
|---|---|
| **CPU** | **Intel(R) Core(TM) i5-14600K** |
| **Số nhân vật lý** | **14** |
| **Số luồng logic** | **20** |
| **RAM** | **31,77 GiB** (≈ 34,1 GB thập phân) |
| **Hệ điều hành** | **Windows 11** (Pro, bản dựng 26200) |
| **Python** | **3.13.12** |
| **PyTorch** | **2.13.0+cpu** — bản CPU, **không có CUDA** |
| Số luồng PyTorch | 14 |
| Backend suy luận | PyTorch (mặc định) và ONNX Runtime (mục 5) |
| Kích thước ảnh vào | **640 px** |
| GPU | **không dùng** — quyết định kiến trúc AD-06, toàn bộ demo bảo vệ chạy CPU |
| Trọng số (số công bố NFR-P1) | **`models/best.pt`** (YOLO11n, 2.590.035 tham số, `imgsz=640`, split v3) |
| Trọng số (các mục lịch sử 3–5bis) | `models/checkpoints/best-cpu-epoch7.pt` / `baseline-416-v1.pt` — **chỉ để đối chiếu** |

### 1.1. ⚠️ Máy đo KHÔNG rảnh — điều kiện quan trọng nhất để đọc mọi con số dưới đây

`psutil` ghi nhận tại thời điểm bắt đầu đo:

| Chỉ số | Giá trị |
|---|---|
| **CPU nền đã bận** | **45,3%** |
| Tiến trình cạnh tranh #1 | `.venv-ai/…/python -m ai.training.train --config yolo11n_finetune.yaml` — **~793% CPU** (≈ 8 nhân) |
| Tiến trình cạnh tranh #2 | `System` — 29% |

Trong đợt đo CSDL còn có thêm hai tiến trình nữa: bộ chịu tải (946% CPU) và
chính pytest (97%).

**Hệ quả, nói thẳng:** mọi con số **độ trễ** trong báo cáo này là **bi quan** —
trên máy rảnh chúng sẽ tốt hơn. Điều này **không** cứu được NFR-P1 (mục 4.4
chứng minh bằng số), nhưng nó có nghĩa là **mức độ** trượt không tin cậy được.
Mục 3.3 định lượng chính xác ảnh hưởng này bằng dữ liệu thô.

---

## 2. Tóm tắt kết quả

| Mã | Chỉ tiêu | Mục tiêu | Ngưỡng tối thiểu | **Đo được** | Kết quả | Biên |
|---|---|---|---|---:|:---:|---|
| ~~**NFR-P1**~~ *(lịch sử — epoch 7, máy bận, có lỗi crop)* | Độ trễ E2E một ảnh (p95) | ≤ 800 ms | ≤ 1.500 ms | ~~**5.857,19 ms**~~ | ~~❌~~ | *phép đo đã bị bác bỏ* |
| **NFR-P1** *(`best.pt`, client-side qua HTTP)* | Độ trễ E2E một ảnh (p95) | ≤ 800 ms | ≤ 1.500 ms | **731,15 ms** | **✅** | **dư 68,85 ms** — 100 mẫu, máy rảnh |
| **NFR-P1** *(`best.pt`, in-process, T5.7a)* | Độ trễ E2E một ảnh (p95) | ≤ 800 ms | ≤ 1.500 ms | **780,36 ms** | **✅** | dư 19,64 ms — 100 mẫu |
| NFR-P2 | FPS chế độ webcam | ≥ 5 FPS | ≥ 3 FPS | **—** *(chưa đo trên `best.pt`)* | ⬜ | chưa có bộ đo webcam |
| NFR-P3 | Tốc độ xử lý video | ≥ 0,3× | ≥ 0,15× | **—** *(chưa đo trên `best.pt`)* | ⬜ | chưa có bộ đo video |
| NFR-P4 | Nạp mô hình (trong tiến trình) | ≤ 15 s | ≤ 30 s | **6,41 s** *(baseline)* | ✅ | dư 57% |
| NFR-P4b | Server đến `/health` sẵn sàng | ≤ 15 s | ≤ 30 s | **8,36 s** *(baseline)* | ✅ | dư 44% |
| NFR-P5 | Overhead API (p95) | ≤ 50 ms | ≤ 100 ms | **19,01 ms** *(baseline)* | ✅ | **nhanh 2,6×** |
| NFR-P6 | Truy vấn lịch sử 10.000 bản ghi (p95 xấu nhất) | ≤ 500 ms | ≤ 1.000 ms | **18,71 ms** | ✅ | **nhanh 26,7×** |
| NFR-P7a | RSS pipeline (đỉnh) | ≤ 2 GB | ≤ 4 GB | **0,759 GB** | ✅ | dùng 38% hạn mức |
| NFR-P7b | RSS server uvicorn dưới tải | ≤ 2 GB | ≤ 4 GB | **0,806 GB** | ✅ | dùng 40% hạn mức |
| **NFR-R5** | CSDL sống qua khởi động lại | 100% | — | **—** *(chưa chạy kịch bản khởi động lại)* | ⬜ | |
| NFR-SC1 | Đồng thời cao nhất không lỗi | ≥ 5 | — | **10** | ✅ | gấp 2× |
| NFR-R4 | Tỉ lệ thành công soak 300 s | ≥ 99% | — | **100%** (soak, 1.684 request) | ✅ | |
| NFR-A1 | mAP@0.5 | ≥ 0,90 | ≥ 0,85 | **0,9829** | ✅ | trên `best.pt`, split v3 |
| NFR-A2 | mAP@0.5:0.95 | ≥ 0,65 | ≥ 0,55 | **0,7834** | ✅ | trên `best.pt`, split v3 |
| NFR-A3a | Precision | ≥ 0,92 | ≥ 0,88 | **0,9837** | ✅ | trên `best.pt`, split v3 |
| NFR-A3b | Recall | ≥ 0,90 | ≥ 0,85 | **0,9714** | ✅ | trên `best.pt`, split v3 |

> **Bốn chỉ tiêu độ chính xác giờ đo trên mô hình chính thức `models/best.pt`**,
> huấn luyện trên **split v3 đã khử trùng lặp ở ngưỡng 10**. Khác với bản đầu (đo
> trên checkpoint epoch 7 và bộ v1 có 619 cặp rò rỉ train↔test), số này **không
> còn caveat "checkpoint giữa chừng" hay "rò rỉ thổi phồng"** — mAP không còn bị
> phóng đại như baseline. Nguồn: [05-tables.md §T5.5a](05-tables.md).

**Chưa đo được:** NFR-P2 (FPS webcam), NFR-P3 (tốc độ video), NFR-A9 (điều kiện
ảnh), NFR-R5 (CSDL sau khởi động lại). Ghi nhận là **món nợ**, không phải "không
áp dụng".

---

## 3. Độ trễ đầu-cuối (NFR-P1)

> ## ⛔ TOÀN BỘ MỤC 3 LÀ SỐ ĐO CŨ ĐÃ BỊ BÁC BỎ — GIỮ LẠI LÀM TƯ LIỆU LỊCH SỬ
>
> Các con số trong mục này (p95 ≈ 5.857 ms, "không ảnh nào đạt 800 ms") **KHÔNG phải kết
> quả cuối cùng** và **không được trích vào quyển đồ án như hiện trạng**. Chúng đo trên
> `baseline-416-v1` / checkpoint epoch 7, **trong khi một tiến trình huấn luyện chiếm ~793% CPU
> song song**, cộng với một lỗi crop khiến PaddleOCR đọc trên ảnh quá lớn (~1.322 ms/ảnh).
>
> **Kết quả đúng, đo lại trên `models/best.pt` khi máy rảnh: NFR-P1 p95 = 731,15 ms
> (client-side) / 780,36 ms (in-process) — ĐẠT mục tiêu 800 ms.** Phân rã đúng: OCR 64,3% /
> phát hiện 34,2% (không phải "93,3% OCR" như phân tích cũ). Nguồn thẩm quyền:
> [`07-benchmark-p1-resolved.json`](07-benchmark-p1-resolved.json).
>
> Mục 3 được giữ nguyên vì quá trình phát hiện và bác bỏ con số nhiễu này bản thân nó là một
> nội dung phương pháp luận đáng ghi — nhưng đọc nó với điều kiện tiên quyết ở trên.

**Nguồn:** `07-benchmark-system.json`. **Cỡ mẫu: 100 ảnh** lấy từ
`datasets/processed/yolo/images/test`, chạy trong tiến trình (không qua HTTP,
không ghi CSDL). Trung bình **1,46 biển số/ảnh**. *(Số đo cũ — xem banner trên.)*

### 3.1. Bảng phân vị

| Phân vị | Giá trị | So với mục tiêu 800 ms | So với ngưỡng 1.500 ms |
|---|---:|---:|---:|
| min | **1.169,80 ms** | 1,46× | 0,78× |
| **p50** | **1.508,79 ms** | 1,89× | **1,01×** |
| trung bình | 2.391,75 ms | 2,99× | 1,59× |
| **p95** | **5.857,19 ms** | **7,32×** | **3,90×** |
| p99 | 10.802,80 ms | 13,50× | 7,20× |
| max | 10.922,96 ms | 13,65× | 7,28× |
| độ lệch chuẩn | 1.953,2 ms | | |

**Kết luận NFR-P1: TRƯỢT cả mục tiêu (800 ms) lẫn ngưỡng tối thiểu (1.500 ms).**

### 3.2. Phân bố — hình dạng nói lên nhiều hơn con số p95

| Ngưỡng | Số ảnh vượt | Tỉ lệ |
|---|---:|---:|
| > 800 ms (mục tiêu NFR-P1) | **100 / 100** | **100%** |
| > 1.500 ms (ngưỡng tối thiểu) | 50 / 100 | **50%** |
| > 2.000 ms | 37 / 100 | 37% |
| > 3.000 ms | 19 / 100 | 19% |
| > 5.000 ms | 8 / 100 | 8% |

**Không một ảnh nào trong 100 ảnh đạt mục tiêu 800 ms.** Ảnh nhanh nhất
(1.169,80 ms) vẫn chậm hơn mục tiêu 46%. Đây là điểm quan trọng: NFR-P1 không
trượt vì một vài trường hợp ngoại lệ kéo đuôi phân bố — **nó trượt ở toàn bộ
phân bố**. Không có cách chỉnh nào ở phần đuôi cứu được chỉ tiêu này.

Phân bố có **đuôi phải rất dài**: p50 = 1.509 ms nhưng p99 = 10.803 ms, gấp
**7,2 lần**. Độ lệch chuẩn (1.953 ms) lớn hơn cả trung vị. Mục 3.3 giải thích
đuôi này đến từ đâu.

**Biểu đồ:** `figures/07-latency-distribution.png`.

### 3.3. Đuôi phân bố đến từ đâu — bằng chứng trong chính dữ liệu thô

Tách 100 mẫu theo thứ tự đo (mảng `e2e_raw_latencies_ms` giữ nguyên thứ tự thời
gian):

| Nhóm mẫu | Trung bình | p50 | max |
|---|---:|---:|---:|
| **80 mẫu đầu** | **1.802,0 ms** | 1.452,3 ms | 4.381,4 ms |
| **20 mẫu cuối** | **4.750,7 ms** | 3.674,1 ms | **10.923,0 ms** |
| Tỉ lệ | **2,64×** | 2,53× | 2,49× |

**Toàn bộ 8 mẫu vượt 5.000 ms đều nằm trong nhóm 20 mẫu cuối.** Trước mẫu thứ
81, độ trễ cao nhất từng ghi nhận là 4.381 ms; sau đó xuất hiện liên tiếp
9.359 / 8.959 / 10.803 / 10.923 / 7.767 ms.

**Diễn giải:** đây không phải thuộc tính của ảnh (thứ tự ảnh là ngẫu nhiên so
với độ khó), mà là **sự tranh chấp tài nguyên tăng dần** — tiến trình huấn
luyện song song chiếm ~8 nhân, cộng thêm khả năng CPU bị giảm xung do nhiệt sau
vài phút chạy full-load. Con số p95 = 5.857 ms rơi **đúng vào vùng bị nhiễm**.

**Ước lượng công bằng hơn cho máy rảnh:** dùng 80 mẫu đầu, **p95 ≈ 3.283 ms**.

**Nhưng kết luận không đổi:** 3.283 ms vẫn **gấp 4,1× mục tiêu** và **gấp 2,2×
ngưỡng tối thiểu**. Ngay cả trên máy hoàn toàn rảnh, NFR-P1 vẫn trượt. Nhiễu do
máy bận **làm con số xấu đi, không tạo ra kết luận**.

---

## 4. Phân rã ngân sách độ trễ — đối chiếu ƯỚC LƯỢNG với ĐO THẬT

Đây là phần có giá trị học thuật nhất của báo cáo. `non-functional-requirements.md`
mục 1 đưa ra một bảng ngân sách **ước lượng trước khi có bất kỳ phép đo nào**,
kèm ghi chú *"sẽ hiệu chỉnh sau Phase 3–4"*. Dưới đây là lần hiệu chỉnh đó.

**Nguồn số đo:** `07-benchmark-system.json → latency_budget`, **40 mẫu**, trung
bình **1,27 biển số/ảnh**, lấy trung vị của từng bước.

> ⛔ **CÁC MỤC 4.1–4.4 LÀ SỐ ĐO CŨ ĐÃ BỊ BÁC BỎ — giữ làm tư liệu lịch sử,
> KHÔNG trích dẫn.** Chúng đo trên checkpoint epoch 7, khi máy bận và hệ thống
> còn lỗi crop khiến PaddleOCR đọc ảnh quá lớn (~1.322 ms/ảnh) — vì vậy con số
> "OCR chiếm 93,3%" là tạo tác của lỗi đó. Phân rã **đúng** trên `models/best.pt`:
> **OCR 64,3% (112,55 ms/biển) / phát hiện 34,2% (59,83 ms)**, và NFR-P1 **ĐẠT**
> (p95 731,15 ms client-side / 780,36 ms in-process, mục tiêu 800 ms). Xem đính
> chính ở **mục 4.5** và nguồn thẩm quyền
> [`07-benchmark-p1-resolved.json`](07-benchmark-p1-resolved.json).

### 4.1. Bảng đối chiếu

| Bước | **Ước lượng** (Phase 0) | **Đo thật** (trung vị) | Chênh lệch | % thời gian thật |
|---|---:|---:|---|---:|
| Giải mã ảnh + tiền xử lý | ~50 ms | **2,54 ms** | **nhanh hơn 19,7×** | 0,2% |
| Suy luận YOLO11n @640 (CPU) | ~150 ms | **92,56 ms** | **nhanh hơn 1,6×** | 6,5% |
| Cắt + tiền xử lý vùng biển | ~30 ms | **0,00 ms** | dưới độ phân giải đồng hồ | 0,0% |
| **PaddleOCR** (tổng cho ảnh) | **~120 ms** ×1,27 = ~152 ms | **1.322,40 ms** | **CHẬM HƠN 8,7×** | **93,3%** |
| Hậu xử lý regex + kiểm hợp lệ | < 5 ms | **0,04 ms** | nhanh hơn 125× | 0,0% |
| Ghi CSDL + lưu ảnh | ~50 ms | *(không nằm trong phép đo này)* | — | — |
| **Tổng pipeline (không CSDL)** | **~355 ms** | **1.417,54 ms** | **chậm hơn 4,0×** | 100% |
| **Tổng có CSDL** | **~405 ms** | *(xem mục 6 và 7)* | | |

Quy về **mỗi biển số**: ước lượng 120 ms/biển, đo được **1.322,40 / 1,27 ≈
1.041 ms/biển** — **chậm hơn 8,7 lần**.

**Biểu đồ:** `figures/07-latency-budget.png`.

### 4.2. Phân tích: vì sao ước lượng ban đầu sai, và sai theo hướng nào

**Bốn trên năm bước được ước lượng QUÁ BI QUAN** — tổng cộng ước lượng 235 ms
cho các bước không-OCR, đo thật chỉ **95,14 ms**, tức là ngân sách thừa gấp 2,5
lần. Nguyên nhân của từng cái:

| Bước | Vì sao ước lượng sai | Bài học |
|---|---|---|
| Giải mã ảnh (50 → 2,54 ms) | Ước lượng theo trực giác "đọc tệp thì tốn thời gian". Thực tế `cv2.imdecode` là mã C đã tối ưu SIMD; ảnh test lại nhỏ | Đừng ước lượng chi phí I/O bằng trực giác khi thư viện là mã native |
| YOLO11n @640 (150 → 92,56 ms) | Ước lượng lấy từ các bài báo đo trên CPU **di động**. Máy này là i5-14600K 14 nhân, PyTorch dùng 14 luồng | Ước lượng lấy từ tài liệu phải quy đổi theo phần cứng |
| Cắt vùng biển (30 → 0,00 ms) | Bị hình dung thành "một bước xử lý ảnh". Thực tế nó chỉ là **cắt lát mảng NumPy** — không sao chép dữ liệu, không có phép tính | **Sai lầm điển hình:** gán ngân sách cho một thao tác không hề tồn tại về mặt tính toán |
| Regex (< 5 → 0,04 ms) | Ước lượng bảo thủ và đúng về mặt bậc độ lớn | Không vấn đề gì |

**Một trên năm bước sai theo hướng chí mạng — và nó nuốt trọn cả ngân sách:**

**PaddleOCR: ước lượng 120 ms/biển, thực tế ~1.041 ms/biển.** Ba nguyên nhân,
xếp theo mức đóng góp:

1. **Con số 120 ms lấy từ tài liệu công bố của engine, gần như chắc chắn đo trên
   GPU hoặc trên biến thể *mobile*.** Cấu hình đang dùng là biến thể mặc định
   (server) chạy **CPU thuần**. Đây là đúng loại lỗi mà mục 0 của chính tài liệu
   NFR cảnh báo — trích số hiệu năng mà không quy đổi phần cứng — nhưng lại mắc
   phải ngay trong bảng ngân sách của tài liệu đó.
2. **PaddleOCR mặc định chạy cả khối *detection* văn bản trước khi *recognition*.**
   Với đầu vào đã là một vùng biển số đã cắt sẵn, bước dò tìm văn bản gần như
   thừa, nhưng vẫn tốn thời gian.
3. **Biển 2 dòng phải qua xử lý tách dòng** (`two_line.py`), làm tăng số lần gọi
   nhận dạng trên mỗi biển. Tập test có **70,1% biển 2 dòng**, nên đây không
   phải trường hợp hiếm mà là **trường hợp phổ biến**.

### 4.3. Hệ quả kiến trúc — luật Amdahl áp lên chính dự án này

> ⛔ **MỤC 4.3 ĐÃ BỊ BÁC BỎ — giữ nguyên văn làm tư liệu lịch sử, KHÔNG trích dẫn.**
> Tỷ trọng thật trên `models/best.pt` là **OCR 64,3% / phát hiện 34,2%** (T5.7b),
> không phải 93,3% / 6,5%. Con số 93,3% dưới đây đo trên checkpoint epoch 7 khi
> hệ thống còn lỗi crop khiến PaddleOCR đọc ảnh quá lớn (~1.322 ms/ảnh). Xem
> đính chính ở **mục 4.5** và **mục 5bis.3**, nguồn thẩm quyền
> [`07-benchmark-p1-resolved.json`](07-benchmark-p1-resolved.json).

Với OCR chiếm **93,3%** thời gian, mọi tối ưu ở bốn bước còn lại đều **vô nghĩa
về mặt số học**:

> Kể cả nếu giải mã ảnh, phát hiện, cắt và hậu xử lý đều trở nên **tức thời
> (0 ms)**, tổng thời gian chỉ giảm từ 1.417,54 ms xuống 1.322,40 ms — **cải
> thiện 6,7%**. Vẫn trượt cả hai ngưỡng của NFR-P1.

Điều này **đảo ngược thứ tự ưu tiên giảm tải** ghi trong `non-functional-requirements.md`:

| Thứ tự trong đặc tả gốc | Đánh giá sau khi đo | Mức cải thiện thực tế đạt được |
|---|---|---|
| **(1)** Xuất mô hình sang ONNX/OpenVINO | ❌ **Nhắm sai đối tượng** — chỉ tăng tốc bộ phát hiện, tức 6,5% ngân sách | **≈ 0,9%** (tính ở mục 5) |
| **(2)** Giảm `imgsz` xuống 480 | ❌ **Nhắm sai đối tượng** — cũng chỉ chạm vào bộ phát hiện, và còn làm giảm mAP | < 3% |
| **(3)** Dùng PaddleOCR **mobile** thay vì server | ✅ **ĐÂY MỚI LÀ VIỆC PHẢI LÀM ĐẦU TIÊN** | có thể vài trăm phần trăm |

**Đề xuất sửa đặc tả:** đảo thứ tự ưu tiên thành **(1) OCR mobile, (2) bỏ khối
text-detection của PaddleOCR khi đầu vào đã là crop, (3) ONNX/OpenVINO cho cả
**bộ nhận dạng**, không chỉ bộ phát hiện.** Đây là một kết luận **rút ra từ số
đo**, chứ không phải từ suy đoán — và nó chỉ có được nhờ phân rã ngân sách theo
từng bước thay vì chỉ đo tổng.

### 4.4. Cần cải thiện bao nhiêu để đạt chỉ tiêu

| Mục tiêu | Tổng cho phép | OCR được phép chiếm (giữ nguyên 95,14 ms cho các bước khác) | Mức tăng tốc OCR cần thiết |
|---|---:|---:|---:|
| Ngưỡng tối thiểu 1.500 ms (p95) | 1.500 ms | ~1.405 ms | **≥ 4,2×** (vì p95 đo được lúc đó là 5.857 ms — con số đã bị bác bỏ) |
| Mục tiêu 800 ms (p95) | 800 ms | ~705 ms | **≥ 8,3×** |

Trên máy rảnh (dùng p95 = 3.283 ms từ mục 3.3), mức cần thiết giảm còn **≥ 2,3×**
để đạt ngưỡng tối thiểu và **≥ 4,4×** để đạt mục tiêu. Mức tăng tốc 2–3× khi
chuyển từ biến thể server sang mobile là hoàn toàn khả thi — nghĩa là **ngưỡng
tối thiểu 1.500 ms vẫn nằm trong tầm với, còn mục tiêu 800 ms thì rất khó** nếu
không thay đổi kiến trúc OCR.

### 4.5. ⚠️ BẢNG NGÂN SÁCH ĐÃ HIỆU CHỈNH LẠI LẦN HAI — bảng ở mục 4.1 đã lỗi thời

Bảng 4.1 được dựng từ **40 mẫu** trên checkpoint epoch 7, **trước** khi sửa lỗi
crop quá lớn khiến PaddleOCR đọc rỗng. Nó cho OCR = 1.322,40 ms và kết luận
OCR chiếm 93,3%. **Con số đó đo một hệ thống đang có lỗi.**

Dưới đây là đối chiếu **ba cột**: ước lượng Phase 0, đo lần đầu (mục 4.1), và đo
lại trên cấu hình đang giao. Nguồn cột thứ ba:
`05-benchmark-system-baseline-416-v1.json → latency_budget` (20 mẫu, 1,00
biển/ảnh — **tệp này là sản phẩm của lượt chạy khói và đã bị xoá cùng thư mục
`05-smoke/`**; các con số của nó được giữ nguyên trong bảng dưới làm tư liệu) và
`07-benchmark-data-v2.json → pipeline_stage_breakdown` (**4.209**
lần chạy — cỡ mẫu đáng tin nhất trong cả báo cáo, tệp còn tồn tại). Phân rã
**chính thức** trên `models/best.pt` là T5.7b
(`05-benchmark-system-best.json`): OCR 64,3% / detect 34,2%.

| Bước | **Ước lượng Phase 0** | **Đo lần 1** (epoch 7, có lỗi) | **Đo lần 2** (`baseline-416-v1`, đã sửa) | Ước lượng có đúng không? |
|---|---:|---:|---:|---|
| Giải mã ảnh + tiền xử lý | ~50 ms | 2,54 ms | **2,55 ms** | ❌ **quá bi quan 19,6×** |
| Suy luận YOLO11n @640 (CPU) | ~150 ms | 92,56 ms | **92,73 ms** *(86,71 ms trên 4.209 mẫu)* | ⚠️ quá bi quan **1,6×** |
| Cắt + tiền xử lý vùng biển | ~30 ms | 0,00 ms | **0,00 ms** | ❌ **bước này không tồn tại về mặt tính toán** |
| **PaddleOCR** | ~120 ms/biển | **1.322,40 ms** ⚠️ | **119,72 ms** *(124,67 ms trên 4.209 mẫu)* | ✅ **ĐÚNG — sai số 0,2%** |
| Hậu xử lý regex + kiểm hợp lệ | < 5 ms | 0,04 ms | **0,03 ms** | ⚠️ bảo thủ, đúng bậc độ lớn |
| **Tổng pipeline (không CSDL)** | **~355 ms** | **1.417,54 ms** | **215,03 ms** | ✅ **quá bi quan 1,65×** |

**Tỷ trọng thật của từng bước** (cột đo lần 2, 20 mẫu):

| Bước | Lần 1 | **Lần 2** |
|---|---:|---:|
| Giải mã | 0,2% | **1,2%** |
| **Phát hiện** | 6,5% | **43,1%** |
| **OCR** | **93,3%** | **55,7%** |
| Cắt + hậu xử lý | 0,0% | **0,0%** |

**Bốn kết luận, và kết luận thứ nhất buộc phải rút lại một tuyên bố cũ:**

1. **Ước lượng 120 ms/biển cho PaddleOCR của Phase 0 là ĐÚNG.** Đo lại được
   **119,72 ms** — sai số **0,2%**. Mục 4.2 quy kết con số 120 ms là "lấy từ tài
   liệu đo trên GPU hoặc biến thể mobile, không quy đổi phần cứng". **Quy kết đó
   sai.** Con số 120 ms đúng cho **PP-OCRv5-mobile trên CPU này**, và đó chính là
   engine đang chạy. Cái sai nằm ở **phép đo lần 1**, không nằm ở ước lượng.
2. **Tổng ngân sách ước lượng ~355 ms so với đo thật 215,03 ms** — Phase 0 bi
   quan **1,65×**. Với một bảng ngân sách dựng **trước khi viết một dòng mã nào**,
   sai lệch 1,65× trên tổng là **chính xác một cách bất thường**.
3. **Hai hạng mục ước lượng sai bản chất, không phải sai độ lớn:** "cắt vùng
   biển ~30 ms" — thao tác này chỉ là **cắt lát mảng NumPy**, không sao chép, chi
   phí bằng 0; và "giải mã ảnh ~50 ms" — `cv2.imdecode` là mã C đã tối ưu SIMD.
   Bài học giữ nguyên: **đừng cấp ngân sách cho một thao tác không tồn tại về mặt
   tính toán.**
4. **Bài học phương pháp lớn nhất của cả Phase 7:** bảng ngân sách ở mục 4.1
   không chỉ sai con số — nó dẫn tới một **kết luận kiến trúc sai** (mục 9.3:
   "thứ tự ưu tiên giảm tải trong đặc tả bị sai"). Một phép đo lấy trên hệ thống
   đang có lỗi chưa biết **trông y hệt** một phép đo hợp lệ: nó có cỡ mẫu, có
   phân vị, có biểu đồ. Thứ duy nhất phát hiện ra nó là **đo lại sau khi sửa
   lỗi** và thấy con số dịch 10,6×.

---

## 5. So sánh PyTorch với ONNX Runtime

**Nguồn:** `07-benchmark-system.json → detector_backend_comparison`.
**Đối tượng: chỉ bộ phát hiện.** Bộ nhận dạng (PaddleOCR) chưa được xuất ONNX.

| Chỉ số | **PyTorch** (`.pt`) | **ONNX Runtime** (`.onnx`) | Tăng tốc |
|---|---:|---:|---:|
| Số mẫu | 50 | 50 | |
| Trung bình | 43,33 ms | **32,29 ms** | 1,34× |
| **p50** | 42,39 ms | **29,85 ms** | **1,42×** |
| p95 | 53,60 ms | **50,04 ms** | 1,07× |
| p99 | 64,42 ms | **57,08 ms** | 1,13× |
| min | 30,81 ms | **22,74 ms** | 1,36× |
| max | 64,42 ms | 57,08 ms | 1,13× |
| Thời gian nạp | 0,105 s | **0,000 s** | |

**Biểu đồ:** `figures/07-backend-comparison.png`.

### 5.1. Đọc kết quả này cho đúng

**ONNX nhanh hơn thật — 1,42× ở p50.** Nhưng con số này **thấp hơn kỳ vọng**
"2–3× trên CPU Intel" ghi trong `non-functional-requirements.md`. Hai lý do có
thể: (a) đây là ONNX Runtime thuần, **chưa dùng OpenVINO Execution Provider** —
mà OpenVINO mới là thứ khai thác được AVX-512/AMX của kiến trúc Intel; (b) máy
đang bận nặng làm nhiễu cả hai phía.

**Nhưng điều quan trọng hơn là mức tăng tốc đó có ý nghĩa gì với hệ thống:**

> Bộ phát hiện chiếm **92,56 ms trên tổng 1.417,54 ms = 6,5%**. Tăng tốc 1,42×
> tiết kiệm được **92,56 − 65,18 ≈ 27,4 ms**, tức **1,9% tổng thời gian**. Áp
> lên phép đo backend riêng (42,39 → 29,85 ms) thì con số còn nhỏ hơn: **≈ 12,5 ms,
> bằng 0,9% tổng thời gian.**
>
> **Độ trễ E2E p95 sẽ đi từ 5.857 ms xuống ≈ 5.830 ms.** Vẫn trượt NFR-P1.
> *(Tính trên số đo cũ đã bị bác bỏ — NFR-P1 nay **ĐẠT** với p95 731,15 ms trên
> `best.pt`, máy rảnh; xem khối "ĐỌC TRƯỚC" §0. Bài học Amdahl trong đoạn này
> vẫn đúng về phương pháp, nhưng với hệ số 34,2%/64,3% thật thì tối ưu detector
> không còn "vô dụng" như kết luận dưới đây.)*

Đây là minh hoạ sách giáo khoa của **luật Amdahl**, và cũng là lý do phần này
đáng nằm trong quyển đồ án: **một tối ưu đúng về kỹ thuật vẫn có thể vô dụng nếu
nhắm vào phần không phải nút cổ chai.** Phương án giảm tải xếp hạng (1) trong
đặc tả gốc chính là phương án ít tác dụng nhất trong ba phương án.

**Việc đáng làm:** xuất **PaddleOCR** sang ONNX/OpenVINO. Nếu đạt cùng mức
1,42×, nó tiết kiệm ~390 ms — gấp **14 lần** phần tiết kiệm được từ bộ phát hiện.

---

## 5bis. PyTorch vs ONNX Runtime vs OpenVINO — đo đủ ba backend × ba độ phân giải

**Nguồn:** `07-benchmark-optimized.json`, đo ngày 19/07/2026 lúc 18:07.
**Cấu hình phần cứng:** Intel **i5-14600K**, 14 nhân vật lý / 20 luồng logic,
31,77 GiB RAM, Windows 11, Python 3.13.12, torch **2.13.0+cpu**, 14 luồng torch.
**⚠️ CPU nền 44,2% đã bận**, một tiến trình huấn luyện chiếm **792%** trong suốt
phép đo. **120 ảnh**, 5 ảnh khởi động (warm-up) không tính.

### 5bis.1. Chỉ bộ phát hiện — đây là nơi tối ưu backend thật sự có tác dụng

| Backend | imgsz | Trung bình | **p50** | p95 | p99 | Nạp (s) | **Tăng tốc p50 so với PyTorch@640** |
|---|---:|---:|---:|---:|---:|---:|---:|
| PyTorch | 640 | 44,70 | **44,30** | 56,92 | 65,49 | 0,569 | *(mốc)* 1,00× |
| PyTorch | 480 | 32,87 | 32,09 | 41,94 | 48,08 | 0,106 | 1,38× |
| PyTorch | 416 | 26,38 | 26,07 | 33,92 | 38,18 | 0,071 | 1,70× |
| **ONNX** | 640 | 27,08 | **25,83** | 37,67 | 41,52 | 0,134 | **1,71×** |
| **ONNX** | 480 | 19,73 | 18,40 | 29,17 | 34,13 | 0,063 | 2,41× |
| **ONNX** | **416** | 11,52 | **10,73** | **16,17** | 18,93 | 0,045 | **🏆 4,13×** |
| **OpenVINO** | 640 | 20,19 | **19,76** | **24,97** | 27,60 | 0,889 | **2,24×** |
| **OpenVINO** | 480 | 13,92 | 13,43 | 18,63 | 21,65 | 0,644 | 3,30× |
| **OpenVINO** | 416 | 12,76 | 11,76 | 16,75 | 30,54 | 0,626 | 3,77× |

**Đối chiếu với kỳ vọng ghi trong `non-functional-requirements.md` mục 1** ("ONNX
Runtime hoặc OpenVINO — thường nhanh gấp 2–3× trên CPU Intel") **và với số liệu
Ultralytics mà Phase 1 tìm được** (ONNX nhanh gấp **~3,73×** PyTorch trên
i7-13700H: 104,61 ms → 28,02 ms):

| Nguồn | Kỳ vọng | **Đo được trên máy này** | Phán quyết |
|---|---|---|---|
| Đặc tả NFR mục 1 | 2–3× | **2,24× (OpenVINO@640)**, **4,13× (ONNX@416)** | ✅ **Kỳ vọng đúng, thậm chí bảo thủ** |
| Ultralytics / Phase 1 | ~3,73× (ONNX, i7-13700H) | **3,77×** (OpenVINO@416), **4,13×** (ONNX@416) | ✅ **Trùng khớp đáng kể** |

> **Đây là một kiểm chứng độc lập thành công.** Con số Phase 1 trích từ tài liệu
> Ultralytics được đo trên **máy khác** (i7-13700H, CPU di động); máy đồ án là
> i5-14600K (CPU để bàn, cùng thế hệ Raptor Lake). Mức tăng tốc **3,7–4,1×** đo
> được ở đây tái lập con số công bố **trong biên độ vài phần trăm** — và đạt được
> **trong lúc máy đang bận 44%**. Rất hiếm khi một con số trích từ tài liệu ngoài
> lại tái lập tốt đến vậy trên phần cứng khác; nó đáng được ghi nhận.

**Một chi tiết ngược trực giác đáng nêu:** OpenVINO **nạp mô hình chậm nhất**
(0,63–0,89 s so với 0,045–0,134 s của ONNX) nhưng **suy luận nhanh nhất** ở 640.
Với dịch vụ chạy dài, chi phí nạp trả một lần, nên đánh đổi này là hoàn toàn có
lợi. Với một script chạy một phát rồi thoát thì ngược lại.

### 5bis.2. Toàn trình (E2E) — và đây là chỗ câu chuyện đảo chiều

Cùng 120 ảnh đó, nhưng đo **cả pipeline** (giải mã → phát hiện → cắt → OCR →
chuẩn hoá):

| Cấu hình | p50 E2E | **p95 E2E** | Trung bình | **detect (trung vị)** | **ocr (trung vị)** | Biển/ảnh | NFR-P1 ≤ 800 ms? |
|---|---:|---:|---:|---:|---:|---:|:---:|
| PyTorch @640 | 265,81 | 742,26 | 342,09 | 103,41 | 148,37 | 1,48 | ✅ *(sát mép)* |
| ONNX @640 | 249,18 | **773,32** | 352,86 | **24,37** | **218,39** | 1,37 | ✅ *(sát mép)* |
| OpenVINO @640 | 154,51 | 667,73 | 249,73 | 20,97 | 128,61 | 1,37 | ✅ |
| OpenVINO @480 | 152,07 | 655,88 | 240,22 | 14,63 | 132,74 | 1,32 | ✅ |
| **OpenVINO @416** | **150,89** | **🏆 631,48** | 244,82 | **12,72** | 134,99 | 1,32 | ✅ **tốt nhất** |

**Ba điều phải rút ra, và điều thứ hai là quan trọng nhất:**

1. **Mọi cấu hình đều đạt NFR-P1 ở p95** trên checkpoint epoch 7 — kể cả PyTorch
   thuần @640 (742 ms). So với **5.857 ms** đo ở mục 3, đây là chênh lệch **7,9
   lần** trên **cùng một checkpoint, cùng một tập ảnh**. Phần lớn khác biệt đến
   từ việc **sửa lỗi crop quá lớn khiến PaddleOCR đọc rỗng** (mục 8 của
   [04-ocr-report.md](04-ocr-report.md)) — không phải từ việc đổi backend.
2. **Tăng tốc bộ phát hiện 3,77× chỉ đổi được 15% ở p95 E2E** (742,26 → 631,48
   ms). Đây chính là **luật Amdahl**, đo được chứ không suy đoán — và nó xác nhận
   nguyên văn lập luận ở mục 4.3, chỉ với **hệ số nhỏ hơn nhiều** so với con số
   93,3% mà mục 4 dùng.
3. **ONNX@640 tệ hơn PyTorch@640 ở E2E (773 vs 742 ms) dù bộ phát hiện của nó
   nhanh hơn 4,2×.** Nghịch lý này được giải thích ở mục 5bis.4.

### 5bis.3. Nút thắt nằm ở đâu — và nó **DI CHUYỂN** giữa các cấu hình

Đây là phát hiện đảo ngược kết luận của mục 4 và của bản báo cáo trước.
**Nguồn:** `07-benchmark-data-v2.json → pipeline_stage_breakdown`, lấy trung vị
của **mọi** bản ghi log `Pipeline run finished` mà server phát ra.

| Cấu hình | Số lần chạy lấy mẫu | **detect (ms)** | **ocr (ms)** | Tổng (ms) | **% detect** | **% OCR** |
|---|---:|---:|---:|---:|---:|---:|
| **PyTorch `baseline-416-v1` @640** *(cấu hình đang giao)* | **4.209** | **86,71** | **124,67** | 212,77 | **40,8%** | **58,6%** |
| ONNX @640 | 149 | 51,08 | 446,24 | 507,92 | 10,1% | 87,9% |
| OpenVINO @640 | 311 | 23,27 | 166,45 | 191,02 | 12,2% | 87,1% |
| OpenVINO @480 | 297 | 15,29 | 171,31 | 188,08 | 8,1% | 91,1% |

> #### ⚠️ Đính chính chính thức đối với mục 4.3 và 5.1
>
> Mục 4 kết luận **"OCR chiếm 93,3%, nên tối ưu bộ phát hiện là nhắm sai đối
> tượng"**, và xếp phương án ONNX/OpenVINO là **"❌ nhắm sai đối tượng"**.
>
> **Kết luận đó SAI đối với cấu hình đang giao, và số đo mới bác bỏ nó.**
>
> Trên `baseline-416-v1.pt` chạy PyTorch @640, tỷ lệ thật là **detect 86,71 ms
> (40,8%)** so với **OCR 124,67 ms (58,6%)** — trên **4.209** lần chạy, cỡ mẫu
> lớn hơn 105 lần so với 40 mẫu của mục 4. Bộ phát hiện là **một khoản chi phí
> lớn**, không phải 6,5% như mục 4 tính.
>
> **Vậy phương án giảm tải xếp hạng (1) trong đặc tả — ONNX/OpenVINO — nhắm ĐÚNG
> đối tượng, và nó đã hoạt động:** OpenVINO cắt bộ phát hiện từ 86,71 ms xuống
> **23,27 ms**, đúng **3,7×**, khớp con số Ultralytics mà Phase 1 tìm được.
> **Thứ tự ưu tiên trong đặc tả gốc KHÔNG sai như mục 9.3 đã tuyên bố.**
>
> **Vì sao mục 4 tính sai:** nó lấy số từ một lần chạy dùng checkpoint epoch 7 và
> **trước** khi sửa lỗi crop quá lớn. Trong lần đó OCR phồng lên 1.322 ms/ảnh —
> gấp **10,6 lần** con số 124,67 ms đo lại được. Tỷ lệ 93,3% là **đúng về số học
> đối với dữ liệu của chính nó**, nhưng dữ liệu đó phản ánh một con **lỗi**, chứ
> không phản ánh chi phí thật của PaddleOCR. Bài học phương pháp: **đừng rút ra
> kết luận kiến trúc từ một phép đo lấy trên hệ thống đang có lỗi chưa biết.**

**Nhưng OCR vẫn thắng ở các cấu hình đã tối ưu.** Sau khi OpenVINO hạ bộ phát
hiện xuống 23 ms, OCR chiếm **87,1%** — nên với các bước tối ưu *tiếp theo*, kết
luận của mục 4 lại trở nên đúng. Nói chính xác: **nút thắt di chuyển.** Câu
"OCR là nút thắt" đúng **sau khi** đã tối ưu bộ phát hiện, và sai **trước đó**.

### 5bis.4. Nghịch lý ONNX — bộ phát hiện nhanh nhất, hệ thống chậm nhất

| Cấu hình | detect (ms) | **ocr (ms)** | FPS webcam hiệu dụng |
|---|---:|---:|---:|
| PyTorch baseline @640 | 86,71 | **124,67** | **4,076** |
| **ONNX @640** | **51,08** | **446,24** ⚠️ | **1,874** ⚠️ |
| OpenVINO @640 | 23,27 | 166,45 | **4,570** 🏆 |

**Khối OCR của ONNX phồng lên gấp 3,6× (124,67 → 446,24 ms) trong khi không có
gì chạm vào nó.** Giải thích: ONNX Runtime và PaddleOCR **mỗi bên tự dựng một
thread pool riêng** trên một máy vốn đã bị đăng ký thừa (một tiến trình huấn
luyện đang chiếm ~8 trên 20 luồng logic). Hai runtime **tranh chấp** nhau chứ
không phối hợp.

**Phải nói thẳng về giới hạn của kết luận này:** đây **cũng là hiệu ứng của môi
trường đo** chứ không thuần tuý là tính chất của ONNX. Cần đo lại trên **máy
rảnh** và **ghim số luồng** (`OMP_NUM_THREADS`, `ort.SessionOptions`) trước khi
kết luận ONNX kém hơn OpenVINO cho bài toán này. Trên bằng chứng **hiện có**,
khuyến nghị là **OpenVINO**.

### 5bis.5. Ba phương án giảm tải của đặc tả — đối chiếu từng phương án

`non-functional-requirements.md` mục 1 quy định: *"Chỉ hạ chỉ tiêu SAU KHI đã thử
hết ba phương án này."* **Cả ba đã thử.**

| # | Phương án trong đặc tả | Kỳ vọng | **Kết quả đo được** | Phán quyết |
|:-:|---|---|---|---|
| **1** | Xuất sang ONNX Runtime hoặc OpenVINO | nhanh 2–3× trên CPU Intel | **Bộ phát hiện: đúng như hứa** — OpenVINO 3,7× (86,71 → 23,27 ms). **E2E: chỉ 12%** (4,076 → 4,570 FPS), vì bộ phát hiện chỉ là 41% ngân sách ⇒ Amdahl chặn trần ở ~1,7× | ✅ **Đã dùng, có tác dụng, nhưng không đủ một mình** |
| **2** | Giảm `imgsz` xuống 480 | — | Bộ phát hiện 23,3 → 15,3 ms **đúng như dự kiến**. Nhưng E2E **không cải thiện** (4,570 → 4,346 FPS, nằm trong nhiễu): tiết kiệm 8 ms là vô hình bên cạnh khối OCR ~170 ms | ⚠️ **Có tác dụng nhưng đã cạn** |
| **3** | Dùng PaddleOCR **mobile** thay vì server | — | **VỐN ĐÃ ĐANG DÙNG TỪ TRƯỚC.** Log server ghi engine là `paddleocr-PP-OCRv5-mobile(det=PP-OCRv5_mobile_det)` | ⛔ **Đã tiêu từ trước, không còn gì để lấy** |

**Kết luận về việc có được hạ chỉ tiêu hay không:**

- **NFR-P1: KHÔNG cần hạ.** Đã đạt (272,42 ms trên `baseline-416-v1`; 631,48 ms
  trên OpenVINO@416) so với mục tiêu 800 ms.
- **NFR-P2: đạt ngưỡng tối thiểu 3 FPS, KHÔNG đạt mục tiêu 5 FPS.** Tốt nhất đo
  được **4,57 FPS** (OpenVINO@640). Cả ba phương án đã cạn. **Nhưng vẫn CHƯA
  được phép hạ chỉ tiêu**, vì hai lý do đo lường:
  1. Mọi con số đo trong lúc một tiến trình huấn luyện chiếm **~790% CPU** ⇒ mọi
     con số là **sàn**, không phải trần.
  2. Khối OCR — thứ **không** phương án nào chạm vào — **trôi 34%** giữa các lần
     chạy dưới tải đó (124,67 → 166,45 ms). **Mức trôi này lớn hơn toàn bộ khoảng
     cách còn lại tới chỉ tiêu.** Giữ OCR ở mốc 124,67 ms thì pipeline OpenVINO
     tổng ~148 ms ⇒ **≈ 6,7 FPS**, tức **ĐẠT**. *(Đây là phép tính số học, KHÔNG
     phải phép đo — ghi lại chỉ để lập luận rằng mục tiêu 5 FPS không phải bất
     khả thi trên máy rảnh.)*

  **Phải đo lại trên máy rảnh trước khi tuyên bố NFR-P2 trượt hoặc hạ chỉ tiêu.**

---

## 6. Kết quả chịu tải

**Nguồn:** `07-stress-load.json`. Chạy qua HTTP thật vào tiến trình uvicorn sống.

### 6.1. Thông lượng theo mức đồng thời

| Mức đồng thời | Số request | Thành công | **Lỗi** | Thời gian (s) | **Thông lượng (req/s)** | p50 (ms) | p95 (ms) | p99 (ms) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **1** | 20 | 20 | **0** | 32,32 | 0,619 | 1.414,51 | 2.500,39 | 3.521,19 |
| **2** | 20 | 20 | **0** | 30,75 | **0,650** | 2.709,44 | 5.148,87 | 5.998,26 |
| **5** | 20 | 20 | **0** | 32,16 | 0,622 | 7.199,99 | 11.706,15 | 11.780,42 |
| **10** | 20 | 20 | **0** | 33,80 | 0,592 | 14.921,35 | 19.069,76 | 19.092,01 |

| Kết luận | Giá trị |
|---|---|
| **Thông lượng đỉnh** | **0,650 req/s tại mức đồng thời 2** |
| **Mức đồng thời cao nhất không lỗi** | **10** |
| Chỉ tiêu NFR-SC1 | ≥ 5 ⇒ **ĐẠT** (gấp 2×) |
| Tỉ lệ lỗi ở mọi mức | **0,0%** |

**Biểu đồ:** `figures/07-concurrency.png`.

### 6.2. Phân tích: hệ thống bão hoà ngay ở mức đồng thời 2

Đây là dạng đường cong **bão hoà CPU thuần túy** và nó rất sạch:

- **Thông lượng gần như phẳng** từ mức 1 đến mức 10: 0,619 → 0,650 → 0,622 →
  0,592 req/s. Dao động chỉ ±5%.
- **Độ trễ tăng gần tuyến tính** với số request đồng thời: p50 đi 1.415 →
  2.709 → 7.200 → 14.921 ms. Từ mức 1 sang mức 10, độ trễ tăng **10,5 lần**
  trong khi thông lượng **giảm 4%**.

Đây chính là hành vi của một hệ thống mà **mọi request đều bị chặn ở CPU**:
thêm request đồng thời **không** tạo thêm công suất, chỉ **xếp hàng** — đúng
định luật Little. Suy luận CPU không có phần chờ I/O để chồng lấn.

**Hai hệ quả vận hành:**

1. **Tăng số worker uvicorn sẽ không giúp gì**, có khi còn hại, vì các worker
   sẽ tranh nhau đúng những nhân CPU đó. Cách duy nhất tăng thông lượng là làm
   **một request nhanh hơn** — tức lại quay về nút cổ chai OCR ở mục 4.
2. **Không có lỗi nào ở mức đồng thời 10 là kết quả tốt và đáng ghi nhận**: hệ
   thống **xuống cấp một cách nhã nhặn** (chậm dần) thay vì đổ vỡ (timeout,
   HTTP 5xx). Đó là đúng hành vi mong muốn.

**Lưu ý về diễn giải:** con số 0,65 req/s bị nén xuống bởi tiến trình huấn luyện
đang chiếm ~8/14 nhân. Trên máy rảnh, thông lượng chắc chắn cao hơn, nhưng
**hình dạng đường cong bão hoà sẽ không đổi** — chỉ dịch lên.

### 6.3. Chạy liên tục (soak) — NFR-R4

| Chỉ số | Giá trị |
|---|---|
| Thời lượng | **300 giây (5 phút)** |
| Mức đồng thời | 2 |
| Tổng request | **185** |
| Thành công / Thất bại | **185 / 0** |
| **Tỉ lệ thành công** | **100%** (chỉ tiêu ≥ 99%) ✅ |
| Thông lượng | 0,617 req/s |
| p50 / p95 / p99 | 2.712,50 / 6.099,06 / 6.351,99 ms |
| min / max | 1.970,58 / 6.414,90 ms |
| **RSS lúc bắt đầu** | **0,880 GB** |
| **RSS lúc kết thúc** | **0,875 GB** |
| **Mức tăng RSS** | **−0,005 GB (GIẢM 5 MB)** |

**Hai điểm đáng chú ý:**

1. **Không có dấu hiệu rò rỉ bộ nhớ.** Sau 185 lượt suy luận liên tiếp, RSS
   **giảm** 5 MB. Bộ nhớ dao động quanh mức ổn định, không tích luỹ.
2. **Độ trễ ổn định hơn hẳn phép đo đơn lẻ**: p99 chỉ 6.352 ms so với 10.803 ms
   ở mục 3.1, và max chỉ 6.415 ms. Điều này **củng cố phân tích ở mục 3.3** —
   các đỉnh 10 giây kia là nhiễu ngoại cảnh, không phải hành vi cố hữu.

**Hạn chế:** đặc tả NFR-R4 quy định **1 giờ**; phép đo này chỉ chạy **5 phút**.
Kết quả 100% là thật nhưng **chưa đủ để kết luận NFR-R4 đạt theo đúng đặc tả**.

---

## 7. Truy vấn cơ sở dữ liệu với 10.000 bản ghi (NFR-P6)

**Nguồn:** `07-stress-db.json`. **10.000 bản ghi**, mỗi kịch bản lặp **10 lần**.

| Kịch bản | Số dòng khớp | Số dòng trả về | p50 (ms) | **p95 (ms)** | max (ms) | Kết quả |
|---|---:|---:|---:|---:|---:|:---:|
| Trang 1, không lọc | 10.000 | 20 | 0,83 | 3,91 | 3,91 | ✅ |
| Trang 50, không lọc | 10.000 | 20 | 0,74 | **0,87** | 0,87 | ✅ |
| **Trang sâu (trang 400)** | 10.000 | 20 | 1,09 | 1,69 | 1,69 | ✅ |
| Lọc theo `input_type` | 3.338 | 20 | 1,20 | 4,09 | 4,09 | ✅ |
| Lọc theo khoảng thời gian | 4.320 | 20 | 1,38 | 4,16 | 4,16 | ✅ |
| Lọc theo độ tin cậy | 2.713 | 20 | 2,11 | 5,27 | 5,27 | ✅ |
| **Lọc chuỗi con biển số (`LIKE`)** | 67 | 20 | 15,90 | **18,71** | 18,71 | ✅ |
| Kết hợp nhiều bộ lọc | 1.140 | 20 | 1,46 | 3,67 | 3,67 | ✅ |

| Kết luận | Giá trị |
|---|---|
| **p95 xấu nhất trên mọi kịch bản** | **18,71 ms** |
| Chỉ tiêu NFR-P6 | ≤ 500 ms |
| **Kết quả** | ✅ **ĐẠT — nhanh hơn chỉ tiêu 26,7 lần** |

### 7.1. Phân tích

**Kịch bản chậm nhất chậm hơn 10–20 lần các kịch bản khác, và lý do rất rõ.**
Lọc chuỗi con biển số (`LIKE '%...%'`) mất **15,90 ms** ở p50 trong khi các
kịch bản khác đều dưới 2,2 ms. Nguyên nhân: `LIKE` với ký tự đại diện **ở đầu
chuỗi** không dùng được chỉ mục B-tree, buộc SQLite **quét toàn bảng 10.000
dòng**. Bằng chứng khẳng định: đây là kịch bản trả về **ít dòng khớp nhất**
(67), tức là chậm **bất chấp** kết quả nhỏ — dấu hiệu kinh điển của quét bảng.

**Phân trang sâu không tốn thêm chi phí.** Trang 400 (1,09 ms) thậm chí nhanh
hơn trang 1 (0,83 ms p50 / 3,91 ms p95). Với `OFFSET` lớn thường có hiện tượng
suy giảm; ở quy mô 10.000 dòng thì chưa xuất hiện.

**Đánh giá thực tế:** với biên **26,7 lần**, tầng CSDL **không phải mối lo** ở
quy mô này. Kể cả khi dữ liệu tăng 10 lần (100.000 bản ghi) và kịch bản `LIKE`
suy giảm tuyến tính lên ~187 ms, chỉ tiêu vẫn đạt. Nếu cần, cách xử lý đã rõ:
thêm chỉ mục FTS cho trường biển số.

---

## 8. Overhead của tầng API (NFR-P5) và thời gian khởi động (NFR-P4)

**Nguồn:** `07-api-overhead.json`. **27 request** qua HTTP thật; mỗi request so
sánh **thời gian đồng hồ phía client** với **thời gian pipeline do server tự báo**.

### 8.1. NFR-P5 — Overhead API

| Chỉ số | Đồng hồ client (ms) | Pipeline tự báo (ms) | **Overhead (ms)** |
|---|---:|---:|---:|
| Trung bình | 1.903,66 | 1.887,84 | **15,82** |
| p50 | 1.474,99 | 1.457,51 | **15,43** |
| **p95** | 3.701,23 | 3.682,83 | **19,01** |
| p99 | 3.767,45 | 3.748,74 | 20,08 |
| min | 736,66 | 721,54 | 10,63 |
| max | 3.767,45 | 3.748,74 | 20,08 |

| Kết luận | Giá trị |
|---|---|
| **Overhead p95** | **19,01 ms** |
| Chỉ tiêu NFR-P5 | ≤ 50 ms |
| **Kết quả** | ✅ **ĐẠT — nhanh hơn chỉ tiêu 2,6 lần** |
| Số request thất bại | **0 / 27** |

**Phân tích.** Overhead **rất ổn định**: dải từ 10,63 ms đến 20,08 ms, chênh
lệch giữa min và max chưa tới 10 ms, **bất kể** thời gian pipeline dao động từ
722 ms đến 3.749 ms. Đây là dấu hiệu của một tầng API có chi phí **hằng số** —
nhận tệp, kiểm magic bytes, tuần tự hoá JSON, ghi CSDL — không phụ thuộc khối
lượng công việc AI.

**Con số này cũng nói lên một điều khác:** 19,01 ms overhead so với 1.457 ms
thời gian pipeline nghĩa là tầng API chỉ chiếm **1,3%** tổng thời gian. Mọi nỗ
lực tối ưu backend đều không đáng, vì lý do y hệt như ở mục 5.

### 8.2. NFR-P4 — Thời gian khởi động

| Phép đo | Giá trị | Chỉ tiêu | Kết quả |
|---|---:|---|:---:|
| Nạp trọng số (trong tiến trình) | **0,66 s** | | |
| Chạy warm-up | **5,74 s** | | |
| **Tổng — pipeline sẵn sàng** | **6,41 s** | ≤ 15 s | ✅ |
| **Khởi động server → `/health` báo sẵn sàng** | **8,36 s** | ≤ 15 s | ✅ |

Nội dung `/health` tại thời điểm đo:

```json
{"status": "ok", "app_name": "Vietnamese ALPR API", "version": "0.1.0",
 "database_connected": true, "model_loaded": true, "uptime_seconds": 7.59}
```

**Phân tích.** **Nạp trọng số chỉ chiếm 0,66 s trong tổng 6,41 s — 10%.** 5,74 s
còn lại là **warm-up**, tức các lần suy luận đầu tiên để PyTorch và PaddleOCR
cấp phát bộ đệm và biên dịch kernel. Điều này khớp với quan sát ở
[07-testing-report.md](07-testing-report.md) mục 5.4: lần suy luận đầu tiên của
bộ phát hiện mất **1.240 ms** trong khi p99 chỉ 74,78 ms.

**Warm-up là lựa chọn thiết kế đúng và nên bảo vệ:** trả trước 5,74 s một lần
lúc khởi động để **không** người dùng nào phải trả giá đó ở request đầu tiên.
2 giây chênh lệch giữa 6,41 s (trong tiến trình) và 8,36 s (qua server) là chi
phí khởi tạo của uvicorn, kết nối CSDL và đăng ký route.

### 8.3. NFR-P7 — Bộ nhớ thường trú

| Phép đo | Giá trị | Chỉ tiêu | Kết quả |
|---|---:|---|:---:|
| RSS trước khi nạp mô hình | 0,196 GB | | |
| RSS sau khi nạp mô hình | 0,729 GB | | |
| **RSS đỉnh (pipeline trong tiến trình)** | **0,759 GB** | ≤ 2 GB | ✅ |
| **RSS server uvicorn dưới tải** | **0,806 GB** | ≤ 2 GB | ✅ |
| RSS trong soak (đầu → cuối) | 0,880 → 0,875 GB | | ✅ không rò rỉ |

**Nạp mô hình tốn 0,533 GB** (0,196 → 0,729). Server dùng nhiều hơn pipeline
thuần **77 MB** — chi phí của uvicorn, SQLAlchemy và các bộ đệm request. Mức
tiêu thụ cao nhất ghi nhận được là **0,880 GB, tức 44% hạn mức 2 GB**. Chỉ tiêu
này đạt với biên rộng và không có rủi ro.

> Để tham chiếu: đo trong container Docker (`cpus: 4`, `OMP_NUM_THREADS=4`) cho
> **719 MiB** — cùng bậc độ lớn, xác nhận con số này không phụ thuộc cách đóng gói.

---

## 9. Kết luận

### 9.1. Chỉ tiêu đạt — và biên an toàn

| Chỉ tiêu | Đo được | Chỉ tiêu | Biên |
|---|---:|---:|---|
| **NFR-P6** truy vấn CSDL | 18,71 ms | 500 ms | **nhanh hơn 26,7×** |
| **NFR-P5** overhead API | 19,01 ms | 50 ms | **nhanh hơn 2,6×** |
| **NFR-P4** khởi động | 8,36 s | 15 s | dư 44% |
| **NFR-P7** bộ nhớ | 0,880 GB | 2 GB | dùng 44% |
| **NFR-SC1** đồng thời | 10 | 5 | gấp 2× |
| **NFR-R4** thành công liên tục | 100% | 99% | 0 lỗi/185 |

**Nhận định chung: toàn bộ tầng hạ tầng — API, CSDL, bộ nhớ, độ ổn định — đều
đạt chỉ tiêu với biên rộng, phần lớn là rất rộng.** Không có chỉ tiêu nào trong
nhóm này ở trạng thái sát ngưỡng. Hệ thống cũng **xuống cấp nhã nhặn** dưới tải
(chậm dần, không đổ vỡ) và **không rò rỉ bộ nhớ**.

### 9.2. Chỉ tiêu KHÔNG đạt — và vì sao

**NFR-P1 — độ trễ E2E p95: 5.857 ms so với mục tiêu 800 ms (gấp 7,32×) và
ngưỡng tối thiểu 1.500 ms (gấp 3,90×).**

Chuỗi nguyên nhân, mỗi bước đều có số đo hậu thuẫn:

1. **PaddleOCR chiếm 93,3% thời gian** — 1.322,40 ms trong tổng 1.417,54 ms
   (mục 4.1).
2. **Đo trên mỗi biển số, OCR chậm hơn ước lượng 8,7 lần** — 1.041 ms so với
   ngân sách 120 ms (mục 4.1).
3. **Ước lượng 120 ms lấy từ tài liệu engine, gần như chắc chắn đo trên GPU
   hoặc biến thể mobile**, rồi được dùng cho biến thể server chạy CPU thuần
   (mục 4.2).
4. **70,1% biển trong tập test là biển 2 dòng**, phải qua xử lý tách dòng làm
   tăng số lần gọi nhận dạng (mục 4.2).
5. **Bốn bước còn lại đều NHANH HƠN ước lượng** — tổng cộng 95,14 ms so với
   ngân sách 235 ms. Vấn đề nằm **hoàn toàn** ở một bước duy nhất (mục 4.2).
6. **Máy đo bị chiếm ~8/14 nhân bởi một tiến trình huấn luyện song song**, làm
   xấu thêm con số. Loại bỏ ảnh hưởng này, p95 ước còn ~3.283 ms — **vẫn trượt
   cả hai ngưỡng** (mục 3.3).

**Kết luận về NFR-P1: trượt thật, không phải tạo tác của phép đo.** Không một
ảnh nào trong 100 ảnh đạt mục tiêu 800 ms; ảnh nhanh nhất vẫn chậm hơn 46%.

> ### 🔴 MỤC 9.2 ĐÃ BỊ BÁC BỎ — SỐ CHÍNH THỨC ĐO TRÊN `best.pt`
>
> Toàn bộ mục 9.2 ở trên **không còn đúng**. Giữ lại nguyên văn vì lịch sử phép
> đo là một phần của báo cáo, nhưng **không được trích dẫn**. Số công bố:
>
> | | Mục 9.2 tuyên bố | Chính thức (`best.pt`, máy rảnh) |
> |---|---:|---:|
> | NFR-P1 p95 | **5.857 ms** ❌ | **731,15 ms** ✅ client-side · **780,36 ms** ✅ in-process |
> | OCR mỗi biển | **1.322,40 ms** | **112,55 ms** (**11,7×** thấp hơn) |
> | Tỷ trọng OCR | ~~**93,3%**~~ | **64,3%** (T5.7b) |
> | Tỷ trọng phát hiện | **6,5%** | **34,2%** (T5.7b) |
>
> **Câu "trượt thật, không phải tạo tác của phép đo" là sai — nó ĐÚNG LÀ tạo tác
> của phép đo.** Ba nguyên nhân và hai giả thuyết bị bác bỏ đã trình bày ở **khối
> "ĐỌC TRƯỚC" đầu báo cáo (§0)**; không lặp lại ở đây.
>
> Đồng thời, quy kết ở bước 3 của mục 9.2 — *"ước lượng 120 ms lấy từ tài liệu
> đo trên GPU"* — cũng sai: **120 ms là con số đúng** cho PP-OCRv5-mobile trên
> CPU này (đo lại 112,55 ms/biển trên `best.pt`).

### 9.3. ~~Kết luận có giá trị nhất: thứ tự ưu tiên giảm tải trong đặc tả bị sai~~ — ĐÃ RÚT LẠI

`non-functional-requirements.md` xếp hạng ba phương án giảm tải là **(1) ONNX/
OpenVINO, (2) giảm `imgsz`, (3) PaddleOCR mobile**, và yêu cầu *"chỉ hạ chỉ tiêu
sau khi đã thử hết ba phương án"*. Số đo cho thấy thứ tự này **ngược**:

| Phương án | Chạm vào bao nhiêu % ngân sách | Cải thiện E2E ước tính | Xếp hạng đúng |
|---|---:|---:|---:|
| ONNX cho **bộ phát hiện** (đã đo: 1,42×) | ~~6,5%~~ → **34,2%** thật | nhỏ | **2** |
| Giảm `imgsz` xuống 480 | ~~6,5%~~ | < 3%, kèm mất mAP | **3** |
| **PaddleOCR mobile / bỏ khối text-detection / ONNX cho bộ nhận dạng** | ~~93,3%~~ → **64,3%** thật (OCR) | **có thể vài trăm %** | **1** |

Phương án được đặt ưu tiên **cao nhất** trong đặc tả hoá ra là phương án **ít
tác dụng nhất trong ba phương án** — nó đã được thực hiện, đã đo được, và cải
thiện đúng **0,9%**. Đây là minh hoạ trực tiếp của **luật Amdahl** và là lý do
việc **phân rã ngân sách theo từng bước** — thay vì chỉ đo tổng thời gian — là
một đóng góp phương pháp luận thật, chứ không phải công việc trang trí.

**Đề xuất chính thức:** ~~sửa `non-functional-requirements.md` mục 1 theo thứ tự
mới~~ — **RÚT LẠI. KHÔNG sửa đặc tả.**

> #### Vì sao rút lại — và vì sao đây mới là kết luận có giá trị nhất
>
> Bảng ngay trên ban đầu dựa vào tỷ lệ "phát hiện 6,5% / OCR ~93%", vốn lấy từ
> phép đo hỏng ở mục 4.1. Tỷ lệ thật trên mô hình chính thức `best.pt` là **phát
> hiện 34,2% / OCR 64,3%** (T5.7b, đo trên `best.pt`).
>
> **Thứ tự ưu tiên trong đặc tả gốc là ĐÚNG.** Phương án (1) — xuất ONNX/OpenVINO
> — nhắm đúng vào một khoản chi phí chiếm 41% ngân sách, và khi thực hiện thì
> **đúng như hứa**: OpenVINO cắt bộ phát hiện từ 86,71 ms xuống 23,27 ms, tức
> **3,7×**, khớp con số Ultralytics mà Phase 1 tìm được cho lớp CPU này
> (~3,73× trên i7-13700H).
>
> **Kết luận có giá trị nhất của Phase 7 vì vậy KHÔNG phải "đặc tả sai", mà là
> một bài học phương pháp luận đắt hơn:**
>
> > Một phép đo lấy trên hệ thống **đang có lỗi chưa biết** trông y hệt một phép
> > đo hợp lệ — vẫn có cỡ mẫu, phân vị, biểu đồ, phân rã theo bước. Nó đã suýt
> > khiến đồ án **sửa một bản đặc tả vốn đúng**, dựa trên một lập luận Amdahl
> > hoàn toàn chặt chẽ về mặt số học nhưng chạy trên đầu vào sai. Thứ duy nhất
> > phát hiện ra là **đo lại sau khi sửa lỗi** và thấy con số OCR dịch **10,6×**.
>
> **Luật Amdahl vẫn được minh hoạ, chỉ là với hệ số khác:** tăng tốc bộ phát hiện
> 3,7× chỉ đổi được **15%** ở p95 E2E (742,26 → 631,48 ms) và **12%** FPS webcam
> (4,076 → 4,570). Bài học Amdahl **đứng vững**; con số dùng để minh hoạ nó thì
> phải thay.

### 9.4. Việc còn phải làm

| # | Việc | Vì sao | Trạng thái |
|:-:|---|---|---|
| **1** | ~~Chuyển sang **PaddleOCR mobile**~~ | — | ⛔ **Không áp dụng** — vốn đã dùng `PP-OCRv5-mobile` từ trước; NFR-P1 nay đã đạt |
| **2** | Đo lại toàn bộ trên **máy rảnh**, sau khi lượt huấn luyện kết thúc | Loại bỏ nhiễu đã định lượng ở mục 3.3. **Cấp thiết hơn trước**: khối OCR trôi **34%** dưới tải, lớn hơn toàn bộ khoảng cách còn lại của NFR-P2 | **Chưa làm** |
| **3** | Đo **NFR-P2 (FPS webcam)** và **NFR-P3 (tốc độ video)** | Hai chế độ đầu vào chưa có số | ✅ **ĐÃ LÀM** — P2 = **4,076 FPS** (tốt nhất 4,57), P3 = **0,754×** |
| **4** | Chạy soak **1 giờ** thay vì 5 phút | Đặc tả NFR-R4 quy định 1 giờ | ⚠️ **Một phần** — đã chạy **15 phút / 3.928 request / 0 lỗi**, vẫn chưa đủ 60 phút |
| **5** | Xuất **bộ nhận dạng** (PaddleOCR) sang ONNX/OpenVINO | Sau khi bộ phát hiện đã xuống 23 ms, OCR chiếm **87%** — giờ nó **mới thật sự** là nút thắt | **Chưa làm** — nhưng ưu tiên đã **tăng** |
| **6** | Đo lại NFR-A1/A2/A3 trên `models/best.pt` và trên split đã sửa rò rỉ | Số cũ (epoch 7, v1 có rò rỉ) không dùng để công bố được | ✅ **ĐÃ LÀM** — `best.pt` (split v3, 640) cho mAP@0.5 **0,9829** / mAP@0.5:0.95 **0,7834** / P **0,9837** / R **0,9714**, đều đạt. Nguồn: [05-tables.md §T5.5a](05-tables.md) |
| **7** | **MỚI** — ghim số luồng (`OMP_NUM_THREADS`, `ort.SessionOptions`) rồi đo lại ONNX | ONNX@640 chậm hơn PyTorch ở E2E dù bộ phát hiện nhanh hơn 4,2×, do tranh chấp thread pool với PaddleOCR (mục 5bis.4) | **Chưa làm** |
| **8** | **MỚI** — sửa xung đột `.env` | `backend/.env` **ghi đè** `.env` gốc: `pydantic-settings` đọc theo thứ tự `(.env, backend/.env)` và **tệp sau thắng**, nên đường dẫn OpenVINO khai trong `.env` gốc **chưa bao giờ có hiệu lực** | **Chưa làm** |

---

## 10. Tệp dữ liệu gốc và biểu đồ

| Tệp | Nội dung |
|---|---|
| `docs/reports/07-benchmark-data.json` | Tệp hợp nhất — mọi con số trong báo cáo này |
| `docs/reports/07-benchmark-system.json` | ⚠️ **Phép đo đã bị bác bỏ** — độ trễ E2E lần 1 (100 mẫu, epoch 7, có lỗi crop), phân rã ngân sách sai |
| **`docs/reports/07-benchmark-optimized.json`** | **3 backend × 3 độ phân giải** (120 ảnh) — nguồn của mục 5bis.1 và 5bis.2 |
| **`docs/reports/07-benchmark-data-v2.json`** | **NFR-P2 / P3 / R4 / R5**, so sánh backend E2E, phân rã theo bước trên **4.209** lần chạy — nguồn của mục 5bis.3–5bis.5 |
| **`docs/reports/05-benchmark-system-best.json`** | **NFR-P1 chính thức** trên `models/best.pt`: p95 in-process 780,36 ms (T5.7a), phân rã bước T5.7b |
| **`docs/reports/07-benchmark-p1-resolved.json`** | **Xác minh NFR-P1 client-side qua HTTP trên `best.pt`: p95 = 731,15 ms** — giải quyết mâu thuẫn 5.857 ↔ 780 ms |
| ~~`docs/reports/05-benchmark-system-baseline-416-v1.json`~~ | NFR-P1 trên `baseline-416-v1.pt` (đối chứng), tập test v3 — chỉ để so sánh. **Tệp đã bị xoá** cùng thư mục khói `05-smoke/`; số client-side đã xác minh của baseline (763,75 ms p95) nằm trong `07-benchmark-p1-resolved.json` |
| `docs/reports/07-benchmark-data-v2.server.log` | Log uvicorn của đợt đo bổ sung (10,2 MB) |
| `docs/reports/07-stress-load.json` | Chịu tải theo mức đồng thời và soak 300 s |
| `docs/reports/07-stress-db.json` | 8 kịch bản truy vấn trên 10.000 bản ghi |
| `docs/reports/07-api-overhead.json` | Overhead API, khởi động, RSS server |
| `docs/reports/07-api-overhead.server.log` | Log uvicorn của đợt đo overhead |

| Biểu đồ | Nội dung |
|---|---|
| `figures/07-latency-distribution.png` | Phân bố độ trễ E2E, 100 mẫu |
| `figures/07-latency-budget.png` | Phân rã ngân sách theo từng bước |
| `figures/07-backend-comparison.png` | PyTorch với ONNX Runtime |
| `figures/07-concurrency.png` | Thông lượng và độ trễ theo mức đồng thời |
| `figures/07-detection-test_latency.png` | Độ trễ riêng của bộ phát hiện |
| `figures/07-leak-distance-distribution.png` | Phân bố khoảng cách Hamming giữa các split |
