# Benchmark PaddleOCR ↔ EasyOCR ↔ Tesseract trên ảnh biển số Việt Nam

**Ngày đo:** 2026-08-03 · **Công cụ:** `ai/evaluation/benchmark_engines.py`
**Số liệu thô:** [36-engine-benchmark.json](36-engine-benchmark.json)

**Lấp khoản nợ:** khoảng trống nghiên cứu số 4 (Bảng 2.23) — *"không tồn tại
benchmark công khai nào so sánh các engine OCR trên riêng ảnh biển số xe máy
Việt Nam hai dòng"*. Trước ngày này, quyển đồ án ghi phép so sánh này là **chưa
đo lần nào** ở mục 3.1.2 và mục 6.9.2.

---

## 1. Vì sao phép đo này khó làm đúng, và bốn lần chạy hỏng

Cách làm ngây thơ — gọi thẳng ba engine rồi so kết quả — **cho số vô nghĩa**.
Bốn lần chạy thử đầu tiên đều sai, và mỗi lần sai chỉ ra một điều kiện mà một
benchmark công bằng bắt buộc phải thoả:

| Lần | Triệu chứng | Nguyên nhân thật |
|:--:|---|---|
| 1 | PaddleOCR nạp **PP-OCRv6_medium** thay vì v5_mobile | `PaddleOCR(lang="en")` ở bản 3.7 không còn cho v5. Phải truyền **cả hai** tên model; truyền một cái thì gói bỏ qua `lang` cho cái còn lại |
| 2 | Sập với `NotImplementedError` | Backend oneDNN làm hỏng suy luận trên `PP-OCRv5_mobile_det` — đúng lỗi mục 5.5.4 đã ghi. Bản giao hàng tắt nó |
| 3 | **Cả ba engine đọc ra ~0%** | Ảnh Roboflow xuất ở khung vuông nên tỷ lệ khung hình thật của biển bị bóp méo. Thiếu `restore_aspect_ratio` thì không engine nào đọc được |
| 4 | PaddleOCR 40% thay vì 65% | Thiếu bộ lọc mảnh vụn theo chiều cao — engine đọc ra `59P200263`**`JJ`**, thừa mảnh rác ở mép dải ghép |

**Bài học chung của cả bốn lần: phần lớn năng lực đọc biển số của hệ thống không
nằm trong engine.** Nó nằm ở tầng bao quanh — ước lượng số dòng theo tỷ lệ khung,
tách-rồi-ghép-ngang, CLAHE, khử nhiễu, chuẩn hoá chiều cao 64 px, lọc mảnh vụn.
So sánh ba engine với ba tầng bao quanh khác nhau là **đo tầng bao quanh chứ
không đo engine**.

## 2. Thiết kế: chỉ thay engine, giữ nguyên mọi thứ khác

Công cụ dựng **đúng một tầng bao quanh**, sao đúng chuỗi bước của
`PaddleOcrRecognizer.recognize`, rồi cho cả ba engine chạy trên **cùng một mảng
NumPy đã chuẩn bị xong**. Khác biệt duy nhất còn lại là engine.

Đây cũng là bằng chứng thực nghiệm cho NFR-M5 — *thay module nhận dạng không
đụng tới phần còn lại của hệ thống* — chứ không chỉ là một phép so sánh.

**Một chỗ cố ý không cào bằng.** Tesseract chạy kèm whitelist `A-Z0-9`, hai
engine kia chạy cấu hình mặc định. Giới hạn tập ký tự khi suy luận là **năng lực
gốc** của Tesseract mà PaddleOCR và EasyOCR không có (mục 3.3.1). Cắt bỏ nó "cho
công bằng" chính là làm sai — nó dìm Tesseract xuống dưới mức thật của nó.

**Kiểm chứng harness.** PaddleOCR ở nhánh `raw` đo được **63,73%**, khớp **chính
xác** con số NFR-A5 = 0,6373 mà quyển đã công bố từ trước bằng một đường đo hoàn
toàn khác (`ai/evaluation/ocr_accuracy.py`). Hai đường đo độc lập cho cùng một
con số tới bốn chữ số — harness tái lập đúng bản giao hàng.

## 3. Ngữ liệu

**2.801 biển số Việt Nam có nhãn chuỗi** — 567 biển một dòng, 2.234 biển hai
dòng. Đúng ngữ liệu mà mọi con số A4–A7 trong quyển dựa vào
(`datasets/annotations/plate_labels.csv`). 0 ảnh hỏng.

## 4. Kết quả

<!-- {{T36}} so sanh ba engine OCR tren 2.801 bien so Viet Nam -->

| Engine | Nhánh | Toàn bộ | Biển 1 dòng | Biển 2 dòng | Chênh layout | CER | Chuỗi rỗng | p50 | p95 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **PaddleOCR** | tắt split | 28,81% | 94,2% | 12,2% | 82,0 | 0,588 | 6 | 295 ms | 348 ms |
| **PaddleOCR** | có split | **63,73%** | 94,2% | 56,0% | 38,2 | 0,094 | 11 | 405 ms | 606 ms |
| **PaddleOCR** | + hậu xử lý | **68,87%** | **94,9%** | **62,3%** | 32,6 | **0,089** | 11 | 402 ms | 624 ms |
| EasyOCR | tắt split | 6,53% | 15,3% | 4,3% | 11,1 | 0,647 | 4 | 84 ms | 181 ms |
| EasyOCR | có split | 10,35% | 15,3% | 9,1% | 6,3 | 0,282 | 1 | 248 ms | 351 ms |
| EasyOCR | + hậu xử lý | 14,28% | 28,6% | 10,7% | 17,9 | 0,269 | 1 | 249 ms | 338 ms |
| Tesseract | tắt split | 9,57% | 47,3% | **0,0%** | 47,3 | 0,777 | 960 | 101 ms | 112 ms |
| Tesseract | có split | 9,60% | 47,3% | **0,0%** | 47,2 | 0,565 | 700 | 108 ms | 122 ms |
| Tesseract | + hậu xử lý | 10,28% | 50,4% | **0,1%** | 50,4 | 0,567 | 700 | 106 ms | 120 ms |

## 5. Bốn kết luận

### 5.1. PaddleOCR thắng dứt khoát — và điều này BÁC BỎ một câu trong quyển

Ở cấu hình bản giao hàng, PaddleOCR đạt **68,87%**, hơn EasyOCR **54,59 điểm**
và hơn Tesseract **58,59 điểm**. Khoảng cách này quá lớn để quy cho nhiễu.

Trước phép đo này, mục 3.3.1 ghi: *"không tồn tại số liệu công khai nào cho thấy
PaddleOCR vượt EasyOCR trên ảnh biển số"*, và *"các so sánh engine-với-engine
trên ảnh biển số mà khảo sát kiểm chứng được lại **nghiêng về EasyOCR**"*. Câu
đó **vẫn đúng về tài liệu công khai**, nhưng nay đồ án có số liệu **của chính
mình** trên **biển số Việt Nam**, và nó nói ngược lại.

Đây là lý do phép đo tồn tại: một khoảng trống được lấp bằng số, không bằng
suy đoán.

### 5.2. Tách-rồi-ghép-ngang KHÔNG phải kỹ thuật độc lập engine

Đây là kết quả bất ngờ nhất, và nó buộc phải phát biểu dè dặt hơn dự kiến:

| Engine | tắt split → có split | Mức tăng |
|---|---|---:|
| PaddleOCR | 28,81% → 63,73% | **+34,92 điểm** |
| EasyOCR | 6,53% → 10,35% | +3,82 điểm |
| Tesseract | 9,57% → 9,60% | **+0,03 điểm** |

Nếu cả ba cùng tăng mạnh thì đóng góp kỹ thuật của đồ án sẽ độc lập với engine —
một khẳng định mạnh. **Dữ liệu không cho phép nói thế.** Bước tách-rồi-ghép-ngang
mua được gần 35 điểm cho PaddleOCR, gần như không mua được gì cho Tesseract.

Phát biểu đúng: *tách-rồi-ghép-ngang là điều kiện **cần** để đọc biển hai dòng —
nó biến bài toán đa dòng thành bài toán một dòng — nhưng **không đủ**. Engine
phải đủ mạnh để tận dụng dải ảnh đã ghép.*

### 5.3. Tesseract không đọc được biển hai dòng — đúng như dự đoán, nhưng tuyệt đối hơn

**0,0% trên 2.234 biển hai dòng**, kể cả sau khi đã ghép thành một dòng. Trong
khi đó nó đọc được **47,3%** biển một dòng — tức engine hoạt động bình thường,
chỉ là hỏng hoàn toàn ở đúng loại biển chiếm 80% ngữ liệu.

Đã kiểm bằng mắt để loại khả năng lỗi công cụ: nó **có** đọc ra chữ, nhưng luôn
kèm ký tự rác — `59L214999` → `B507B149991`, `60F141516` → `P6NF741516` — và
700/2.801 lần trả chuỗi rỗng. Đây là kết quả thật.

Mục 3.3.1 đã dự đoán *"Tesseract vỡ khi crop nhiều dòng"* dựa trên tài liệu.
Phép đo xác nhận, và cho thấy mức độ nghiêm trọng hơn dự đoán.

### 5.4. Bộ luật hậu xử lý giúp **mọi** engine — đây mới là phần độc lập engine

| Engine | có split → + hậu xử lý | Mức tăng |
|---|---|---:|
| PaddleOCR | 63,73% → 68,87% | +5,14 điểm |
| EasyOCR | 10,35% → 14,28% | +3,93 điểm |
| Tesseract | 9,60% → 10,28% | +0,68 điểm |

Cả ba đều tăng. Bộ luật hậu xử lý ràng buộc theo vị trí — đóng góp (b) của đồ án
— vì vậy **là** một đóng góp độc lập engine, khác với tách-rồi-ghép-ngang.

Lưu ý mức tăng ở đây (+5,14) nhỏ hơn con số +11,39 công bố ở mục 6.5.2. Hai con
số đo hai thứ khác nhau: +11,39 đo trên đường ống đầy đủ **có bước cứu dòng trên
và bậc thang thử-lại**; +5,14 đo ở tầng nhận dạng thuần, không có hai bước đó.

## 6. Hai điều phép đo này KHÔNG trả lời

1. **Đo trên vùng biển đã cắt sẵn, không phải ảnh toàn cảnh.** Báo cáo
   [31](31-detection-stage-ablation.md) đã cho thấy thứ tự xếp hạng **đảo ngược**
   khi chuyển sang ảnh toàn cảnh qua bộ phát hiện thật. Kết luận ở đây chỉ áp
   cho tầng nhận dạng.
2. **Không kết luận engine nào tốt hơn nói chung.** Chỉ kết luận engine nào đọc
   biển số Việt Nam tốt hơn *bên trong tầng bao quanh của đồ án*. Một hệ thống
   thiết kế quanh EasyOCR — với tiền xử lý riêng của nó — có thể cho số khác.

## 7. Tái lập

```bash
backend/.venv/Scripts/python -m ai.evaluation.benchmark_engines
```

Khoảng 100 phút trên CPU của máy đo (xem mục 6.2.1). Thêm `--limit N` để chạy
mẫu nhỏ; hạt giống trộn cố định (20260719) nên mẫu nhỏ không thiên về bộ dữ liệu
nào tình cờ đứng đầu danh sách.
