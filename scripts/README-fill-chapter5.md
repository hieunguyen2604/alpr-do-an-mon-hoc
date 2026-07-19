# `fill_chapter5.py` — chạy đo và xuất số cho Chương 5

Script điều phối toàn bộ phép đo của Chương 5 (*Thực nghiệm và đánh giá*) rồi xuất kết
quả theo **đúng mã bảng và đúng cấu trúc cột** của `docs/papers/ch5-thuc-nghiem.md`.

Script **không cài đặt lại phép đo nào**. Nó gọi các module đã có trong `ai/evaluation/`,
đọc lại tệp JSON mà chúng sinh ra, và ép dữ liệu về đúng hình dạng bảng của chương.
Mục đích: việc điền số vào chương là **thao tác cơ học**, không phải thao tác diễn giải.

---

## 1. Điều kiện tiên quyết

| Việc cần làm trước | Vì sao |
|---|---|
| ✅ Lượt huấn luyện `runs/final-640-v3/` đã kết thúc đủ 20 epoch | Đã sinh trọng số chính thức |
| ✅ `models/best.pt` đã có (sao từ `runs/final-640-v3/weights/best.pt`) | Đây là trọng số chính thức mà mọi bảng của chương tham chiếu |
| Dùng venv `backend/.venv` | Venv này có đủ cả phụ thuộc AI lẫn backend |

`models/best.pt` **đã tồn tại**, nên script chạy trực tiếp trên trọng số chính thức và các bảng
của chương lấy đúng số của `best.pt`. (Cơ chế lùi về `baseline-416-v1.pt` khi thiếu `best.pt`
vẫn còn trong script như một phương án an toàn, nhưng hiện không kích hoạt.)

---

## 2. Cách chạy

```bash
# Xem sẽ đo những gì, không chạy gì cả — luôn chạy lệnh này trước
backend/.venv/Scripts/python.exe scripts/fill_chapter5.py --dry-run

# Chạy thử nhanh (giới hạn mẫu, bỏ chịu tải và soak) — khoảng 5-10 phút
backend/.venv/Scripts/python.exe scripts/fill_chapter5.py --skip-slow

# Chạy đầy đủ để lấy số công bố — khoảng 1-2 giờ trên CPU
backend/.venv/Scripts/python.exe scripts/fill_chapter5.py
```

> ⚠ **Không chạy lệnh đầy đủ trong lúc đang huấn luyện.** Mọi con số độ trễ sẽ bị lượt
> huấn luyện tranh CPU làm sai lệch, và người đọc báo cáo không có cách nào biết điều đó
> từ chính con số. Đợi huấn luyện xong rồi mới đo hiệu năng.

### Các đối số

| Đối số | Mặc định | Ý nghĩa |
|---|---|---|
| `--weights` | `models/best.pt`, lùi về `models/baseline-416-v1.pt` | Trọng số cần đánh giá |
| `--data` | `datasets/processed/yolo_v3/data.yaml` | Bộ mô tả dataset của Ultralytics |
| `--split` | `test` | `test` hoặc `val`. Dùng `val` chỉ để thử; số công bố phải đo trên `test` |
| `--imgsz` | `640` | Kích thước ảnh suy luận. Với baseline phải đặt `416` |
| `--conf` | `0.25` | Ngưỡng confidence khi đo chỉ số tại điểm vận hành |
| `--skip-slow` | tắt | Bỏ qua chịu tải + soak 300 s, giới hạn số mẫu của các phép còn lại |
| `--out-json` | `docs/reports/05-results.json` | Tệp JSON kết quả |
| `--out-md` | `docs/reports/05-tables.md` | Đoạn Markdown chứa các bảng đã điền số |
| `--run-dir` | `runs/final-640-v3` | Thư mục lượt huấn luyện, để đọc `results.csv` cho bảng T5.4b |
| `--dry-run` | tắt | Chỉ in ra sẽ đo những gì, không chạy phép đo nào |

---

## 3. Đầu ra

### 3.1. `docs/reports/05-results.json`

Cấu trúc phẳng, **khoá cấp một là mã bảng**:

```json
{
  "_meta": { "cpu_ten": "...", "so_nhan_vat_ly": 14, "torch": "...", "..." : "..." },
  "T5.5a": { "map50": 0.9967, "map5095": 0.8448, "so_anh_tap_test": 1514, "..." : "..." },
  "T5.7c": { "trang_thai": "chua do", "ly_do": "khong tim thay ban xuat ONNX/OpenVINO ..." }
}
```

Hai dạng payload, và chỉ có hai:

* **đo được** — các khoá số liệu của bảng đó;
* **chưa đo** — `{"trang_thai": "chua do", "ly_do": "<lý do cụ thể>"}`.

Không bao giờ có dạng thứ ba. Không có `0` giả, không có `null` im lặng.

Khối `_meta` gồm: tên CPU, số nhân vật lý / logic, RAM, hệ điều hành, phiên bản
Python / torch / ultralytics / paddleocr, đường dẫn trọng số, dataset, split, số ảnh của
split, thời điểm đo và thời gian chạy.

### 3.2. `docs/reports/05-tables.md`

Các bảng đã điền số, mỗi bảng có tiêu đề ghi rõ mã bảng (`## {{T5.5a}} ...`), cấu trúc cột
khớp với `ch5-thuc-nghiem.md`. Đầu tệp có khối điều kiện đo để một bảng bị copy rời khỏi
ngữ cảnh vẫn truy ngược được phần cứng đã dùng.

### 3.3. Tệp trung gian và hình vẽ

| Chế độ | Nơi ghi tệp trung gian và hình |
|---|---|
| Chạy đầy đủ | `docs/reports/` và `docs/reports/figures/` |
| `--skip-slow` | `docs/reports/05-smoke/` — **cách ly hoàn toàn** |

Lượt `--skip-slow` đo trên rất ít mẫu. Nếu để nó ghi đè lên báo cáo và hình vẽ dùng để
công bố thì các tệp đó lặng lẽ trở thành số liệu rác mà không ai biết. Vì vậy chế độ chạy
thử bị tách sang thư mục riêng, và thư mục đó có thể xoá bất cứ lúc nào.

### 3.4. stdout

Bảng tóm tắt đối chiếu chỉ tiêu NFR (đạt / đạt ngưỡng tối thiểu / không đạt / chưa đo),
theo sau là danh sách các mã bảng chưa đo được **kèm lý do từng cái**.

---

## 4. Bảng nào lấy số từ đâu

| Mã bảng | Nguồn | Ghi chú |
|:---:|---|---|
| `T5.2b` | `importlib.metadata` của venv đang chạy | Chỉ đo được **một** môi trường mỗi lần chạy |
| `T5.4b` | `<run-dir>/results.csv` | Cảnh báo nếu chưa đủ 20 epoch |
| `T5.5a`, `T5.5b` | `ai.evaluation.evaluate` | mAP ưu tiên lấy từ lượt Ultralytics val |
| `T5.5c` | primitive của `evaluate.py`, gom theo dải diện tích | Dải dưới 30 đối tượng bị đánh dấu ⚠ |
| `T5.6a`…`T5.6e` | `ai.evaluation.ocr_accuracy` | Cần tệp nhãn chuỗi trong `datasets/annotations/` |
| `T5.7a`, `T5.7b` | `ai.evaluation.benchmark_system` | |
| `T5.7c` | `ai.evaluation.benchmark_cpu` | Cần bản xuất ONNX/OpenVINO của **đúng** trọng số này |
| `T5.7e` | `ai.evaluation.stress_test` | Bị bỏ khi có `--skip-slow` |
| `T5.10` | `ai.evaluation.error_analysis` | Qua một bước chuyển đổi lược đồ, xem mục 6 |
| `T5.8`, `T5.9` | ghép từ các bảng trên | Không chạy phép đo mới |

Ba bảng script này **cố ý không đo**, vì chúng chưa có mã và việc bịa ra một cách đo
tạm bợ sẽ tạo ra con số trông chặt chẽ nhưng đo một đại lượng không xác định:

* `T5.7d` — webcam và video: chưa có kịch bản đo, và khi viết **phải kèm định nghĩa
  tường minh** của "FPS hiệu dụng" (khung hình được *nhận dạng* mỗi giây, hay khung hình
  được *hiển thị* mỗi giây — hai định nghĩa cho hai con số rất khác nhau).
* Bảng phân rã đóng góp **theo từng nhóm luật** của `T5.6b`: cần cơ chế bật/tắt từng
  nhóm luật trong `ai/inference/plate_rules.py`.
* `T5.3b`, `T5.3c`: thuộc về `ai.evaluation.leak_check` và `scripts/dataset/statistics`,
  chạy riêng theo mục B của `ch5-thuc-nghiem.md`.

---

## 5. Quy trình điền vào Chương 5 sau khi có kết quả

1. **Chạy `--dry-run`.** Kiểm tra trọng số, split, tệp nhãn chuỗi và bản xuất đúng như
   mong đợi. Nếu dòng `trong so` vẫn trỏ về `baseline-416-v1.pt` thì dừng lại — huấn
   luyện chưa xong.
2. **Chạy đầy đủ**, không có `--skip-slow`, khi máy không chạy việc gì khác.
3. **Đọc bảng tóm tắt trên stdout trước.** Nếu một mã bảng nằm trong danh sách "chưa đo
   được", đọc lý do và quyết định: khắc phục được thì khắc phục rồi chạy lại; không khắc
   phục được thì ô đó **giữ nguyên `—`** trong chương.
4. **Mở `docs/reports/05-tables.md`**, copy từng bảng vào đúng vị trí đánh dấu
   `<!-- {{T5.x}} ... -->` trong `docs/papers/ch5-thuc-nghiem.md`.
5. **Kiểm tra lại năm điều sau mỗi bảng vừa dán:**
   - Dòng **mẫu số** đã có số chưa (số ảnh / số đối tượng / số biển có nhãn chuỗi)?
   - Ô nào là số của **baseline** thì nhãn cột có ghi rõ chưa?
   - Cặp số **94,3% / 45,7%** nếu xuất hiện, câu văn có ghi **RodoSol-ALPR** và **Brazil**
     ngay trong câu chưa?
   - Mục 5.6.2 đã chọn đúng **một** nhánh A hoặc B theo dấu của hiệu số A6 − A5 chưa?
     (Khoá `T5.6b.nhanh_dien_giai` trong JSON cho biết nhánh nào.)
   - Bảng T5.5c có dải nào bị đánh dấu ⚠ (dưới 30 đối tượng) không? Dải đó **không được
     đưa vào so sánh**.
6. **Viết phần diễn giải** (5.11, 5.12) dựa trên các ô đã điền số thật, theo đúng khung
   lập luận đã cố định sẵn trong chương.
7. **Xoá mục "Hướng dẫn điền số"** ở cuối `ch5-thuc-nghiem.md` trước khi nộp.

---

## 6. Những chỗ script cố tình từ chối cho ra số

Ghi lại ở đây để người bảo trì sau không tưởng là thiếu sót:

* **`T5.10` bị từ chối khi mâu thuẫn với `T5.6b`.** `error_analysis` đọc lược đồ
  `ground_truth` / `pre_norm_text` / `post_norm_text`, còn `ocr_accuracy` ghi
  `truth` / `raw_ocr_text` / `plate_number`. Nếu nạp thẳng, mọi trường đều rỗng và
  **mọi ca bị phân loại là đúng** — bảng sẽ hiện 0 lỗi một cách im lặng. Script chuyển
  đổi lược đồ trước, rồi vẫn kiểm tra chéo: nếu `error_analysis` báo 0 ca sai trong khi
  NFR-A6 dưới 1,0, kết quả bị **từ chối** thay vì ghi 0.
* **Dòng E1 của `T5.10` để trống hai cột tỉ lệ.** E1 đo trên lượt E2E, E3–E6 đo trên lượt
  vùng cắt — hai mẫu số khác nhau. Tỉ lệ trên mẫu số riêng của E1 nằm ở khoá
  `ty_le_tren_mau_so_rieng`.
* **Dòng tổng của `T5.7b` so tỉ số với ước lượng cùng phạm vi.** Số đo không bao gồm bước
  ghi CSDL, nên mẫu số của tỉ số cũng phải trừ bước đó ra. Con số 405 ms vẫn được công bố
  nguyên vẹn ở cột ước lượng.
* **Cột "mAP@0.5 sau khi xuất" của `T5.7c` luôn là `—`.** `benchmark_cpu` chỉ đo độ trễ.
  Muốn có cột này phải chạy `ai.evaluation.evaluate` với `--weights` trỏ vào bản xuất.
* **NFR-A9 ghi "không đo được vì thiếu nhãn", không phải "chưa tới lượt đo".** Bộ dữ liệu
  không có nhãn điều kiện ảnh, và script **không** gán nhãn bằng suy đoán độ sáng.
