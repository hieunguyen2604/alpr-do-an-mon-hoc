# Công cụ gán nhãn biển số cho tập test

Thư mục này chứa hai script phục vụ việc **gán nhãn tay chuỗi biển số** cho tập
test, tạo ra ground truth để đo độ chính xác OCR.

## 1. Tại sao cần bước này

Bộ dữ liệu đã gộp chỉ có **bounding box** — nó cho biết biển số *nằm ở đâu*,
không cho biết biển số *đọc là gì*. Như vậy là đủ để huấn luyện và đánh giá bộ
phát hiện (detector), nhưng hoàn toàn không đủ để đánh giá OCR.

Hệ quả rất cụ thể: nếu không có nhãn chuỗi thì các chỉ tiêu **NFR-A4 đến NFR-A7**
không phải là "đo được kém", mà là **không đo được**. Không có con số nào để đưa
vào chương đánh giá.

Cách khắc phục đã thống nhất: gán nhãn tay vài trăm ảnh trong tập test. Hai
script dưới đây tồn tại để việc đó nhanh và ít sai nhất có thể.

## 2. Chạy như thế nào

Hai script này chạy bằng **`backend/.venv`**.

### Bước 1 — Cắt ảnh biển số

```powershell
.\backend\.venv\Scripts\python.exe scripts\labeling\extract_plates.py
```

Script đọc `datasets/processed/yolo/images/test` cùng nhãn tương ứng trong
`labels/test`, cắt từng vùng biển số theo **box ground-truth**, phóng to lên
chiều cao 200px cho dễ đọc, rồi ghi vào:

- `datasets/annotations/plates_to_label/` — các ảnh đã cắt
- `datasets/annotations/plates_to_label/manifest.csv` — bảng truy nguyên

Tên file cắt có dạng `<tên_ảnh_gốc>__box<N>.jpg`, nên luôn truy ngược được về
ảnh gốc và về đúng dòng nhãn thứ mấy.

Kết quả thực tế đã chạy: **458 ảnh test → 512 ảnh biển số** (một số ảnh chứa
nhiều hơn một biển). Ước lượng theo tỉ lệ khung: 153 biển 1 dòng, 359 biển 2 dòng.

Chạy lại lần nữa sẽ **dùng lại** các ảnh đã cắt, không cắt lại từ đầu (trừ khi
thêm cờ `--overwrite`).

Vài tuỳ chọn hay dùng:

| Cờ | Ý nghĩa |
| --- | --- |
| `--split val` | Cắt từ split khác (mặc định `test`) |
| `--target-height 260` | Phóng to hơn nữa nếu ảnh mờ khó đọc |
| `--padding-ratio 0.08` | Chừa lề rộng hơn quanh biển (mặc định 0.04) |
| `--overwrite` | Cắt và ghi đè lại toàn bộ |

### Bước 2 — Mở công cụ gán nhãn

```powershell
.\backend\.venv\Scripts\python.exe scripts\labeling\label_tool.py
```

Script mở một máy chủ HTTP nhỏ ở `http://127.0.0.1:8765/` và tự bật trình duyệt.
Máy chủ dùng thư viện chuẩn `http.server`, **không dùng FastAPI**, để không kéo
thêm phụ thuộc và không dính vào ràng buộc kiến trúc NFR-M1.

Nếu cổng 8765 đã bận: `--port 9000`. Nếu không muốn tự mở trình duyệt:
`--no-browser`.

Nhãn được ghi vào `datasets/annotations/plate_labels.csv`.

## 3. Phím tắt

Con trỏ luôn nằm sẵn trong ô nhập, không cần chạm chuột.

| Phím | Tác dụng |
| --- | --- |
| `Enter` | Lưu và sang ảnh kế tiếp |
| `Ctrl` + `Enter` | Bỏ qua — ảnh không đọc được |
| `Alt` + `←` | Quay lại ảnh trước (để sửa) |
| `Alt` + `→` | Sang ảnh sau mà không lưu |
| `Alt` + `1` | Chọn biển 1 dòng |
| `Alt` + `2` | Chọn biển 2 dòng |

## 4. Quy ước gõ nhãn

Đây là phần quan trọng nhất. Nhãn không nhất quán sẽ làm sai lệch mọi con số
tính về sau.

- **Gõ liền, không dấu cách**: `51G49539`, không phải `51 G 495 39`.
- **Không gõ gạch ngang, không gõ dấu chấm**: gõ `51G49539`, không phải
  `51G-495.39`. Giao diện sẽ tự hiển thị lại dạng có dấu phân cách để đối chiếu.
- **Chữ tự động viết hoa**. Cứ gõ thường cũng được.
- Mọi ký tự không phải chữ cái hoặc chữ số **bị loại bỏ ngay khi gõ**. Có gõ
  nhầm gạch ngang cũng không sao.
- **Biển 2 dòng vẫn gõ thành một chuỗi liền**, dòng trên trước, dòng dưới sau:
  biển xe máy có dòng trên `29-H1` và dòng dưới `123.45` thì gõ `29H112345`.
- Biển mờ, khuất, chỉ đọc được một phần → bấm **Ctrl+Enter (Bỏ qua)**. Không đoán
  bừa. Một nhãn đoán sai còn tai hại hơn một ảnh bị bỏ qua: ảnh bỏ qua vẫn được
  ghi lại nên vẫn đếm được, còn nhãn sai thì âm thầm làm sai con số độ chính xác.
- Ô **số dòng** đã được điền sẵn theo ước lượng tỉ lệ khung. Đây chỉ là **phỏng
  đoán** (xem mục 6), nhìn ảnh thấy sai thì sửa bằng `Alt`+`1` / `Alt`+`2`.

### Dấu hiệu hợp lệ bên phải ô nhập

Khung bên phải gọi thẳng bộ chuẩn hoá thật của hệ thống
(`ai/inference/normalizer.py`) — cùng đúng đoạn mã mà pipeline dùng, nên nó
không bao giờ lệch với thứ hệ thống thực sự chấp nhận.

- ✔ **xanh lá** — chuỗi khớp một định dạng biển số Việt Nam hợp lệ, có kèm dạng
  hiển thị (`51G-495.39`) và loại biển (`Ô tô`, `Xe máy (kiểu mới)`…).
- ⚠ **vàng** — chưa khớp định dạng nào. **Vẫn lưu được**. Dấu vàng là lời nhắc
  kiểm tra lại xem có gõ nhầm không, không phải lệnh cấm: biển thật đôi khi cũ,
  hỏng, hoặc thuộc dạng hiếm mà bộ luật chưa phủ.

Lưu ý: dấu ✔ có thể xuất hiện nhờ bộ chuẩn hoá đã **tự sửa** chuỗi bạn gõ (ví dụ
gõ `3OA12345` chữ O, nó hiểu thành `30A12345` số 0). Hãy nhìn chuỗi hiển thị bên
cạnh dấu ✔ để chắc chắn nó khớp đúng thứ trên ảnh. **Nhãn được lưu là đúng chuỗi
bạn gõ**, không phải bản đã sửa — vì ground truth phải là thứ mắt người đọc được.

## 5. Lưu và chạy tiếp

- **Tự động lưu sau mỗi ảnh.** Mỗi câu trả lời được ghi xuống đĩa *trước khi*
  trình duyệt báo lưu thành công. Đóng nhầm trình duyệt hay mất điện thì cùng lắm
  mất đúng ảnh đang xem.
- **Chạy lại thì tiếp tục từ chỗ đang dở**, tự nhảy tới ảnh chưa gán đầu tiên.
  Không phải làm lại từ đầu.
- **Gán lại một ảnh sẽ thay thế dòng cũ**, không tạo dòng trùng. Cứ `Alt`+`←`
  quay lại sửa thoải mái.
- Tệp được ghi kiểu ghi-tạm-rồi-đổi-tên, nên nếu bị ngắt giữa chừng thì tệp cũ
  vẫn còn nguyên vẹn chứ không bị cụt.

Cột trong `datasets/annotations/plate_labels.csv`:

| Cột | Nội dung |
| --- | --- |
| `crop_file` | Tên ảnh đã cắt — khoá nối với `manifest.csv` |
| `source_image` | Tên ảnh gốc trong tập test |
| `plate_text` | Chuỗi biển số, viết hoa, không dấu phân cách. Rỗng nếu bỏ qua |
| `line_count` | `1` hoặc `2` |
| `is_skipped` | `true` nếu ảnh không đọc được |
| `labeled_at` | Thời điểm gán nhãn, ISO-8601 theo giờ UTC |

Ảnh bị bỏ qua **được ghi lại chứ không bị bỏ trống**. "Ảnh này không đọc nổi" là
một phát hiện về chất lượng dữ liệu; xoá nó đi sẽ âm thầm làm nhỏ mẫu số của mọi
con số độ chính xác tính sau này.

## 6. Ước lượng số dòng — đây là phỏng đoán

Cột `estimated_lines` và ô radio điền sẵn dùng ngưỡng tỉ lệ ngang/dọc **2.5**.
Con số này suy ra từ kích thước biển trong QCVN 08:2024/BCA:

| Loại biển | Kích thước (mm) | Tỉ lệ | Số dòng |
| --- | --- | --- | --- |
| Ô tô, biển dài | 520 × 110 | 4,727 | 1 |
| Ô tô, biển ngắn | 330 × 165 | 2,000 | 2 |
| Xe máy | 190 × 140 | 1,357 | 2 |

Khoảng trống giữa 2,000 và 4,727 khá rộng nên ngưỡng 2,5 nằm an toàn ở giữa.

Nhưng **đây là heuristic, không phải quy định pháp lý**. Quy chuẩn chỉ ràng buộc
kích thước tấm biển vật lý; nó không hề bảo đảm rằng cái *box* được vẽ ra giữ
đúng tỉ lệ đó. Góc chụp nghiêng, box cắt chặt hay lỏng, ảnh nhoè — tất cả đều làm
lệch tỉ lệ. Vì vậy giá trị này chỉ là **giá trị điền sẵn để người gán nhãn sửa**,
đúng như cách công cụ đang dùng nó.

Ngưỡng 2,5 khớp với `InferenceConfig.two_line_aspect_ratio_threshold`, để mặc
định lúc gán nhãn và ngưỡng lúc chạy pipeline không nói hai đằng.

## 7. Ước lượng thời gian

Khoảng **1–2 giây mỗi ảnh** khi đã quen tay: nhìn ảnh, gõ 8–9 ký tự, bấm Enter.
Vài chục ảnh đầu sẽ chậm hơn (3–5 giây) trong lúc làm quen.

| Số ảnh | Thời gian ước tính |
| --- | --- |
| 300 ảnh | ~10–15 phút |
| 500 ảnh (toàn bộ 512) | ~15–25 phút |

Nên chia thành 2–3 đợt, mỗi đợt khoảng 10 phút. Gán nhãn liên tục quá lâu thì mắt
mỏi và tỉ lệ gõ nhầm tăng lên — mà nhãn sai thì tai hại hơn nhãn thiếu.

Không bắt buộc phải gán hết 512 ảnh. Mục tiêu đã thống nhất là **300–500 ảnh**;
gán hết bao nhiêu thì dừng ở đó cũng được, phần chưa gán sẽ không có trong CSV và
việc đánh giá chỉ tính trên phần đã có nhãn.

## 8. Xử lý sự cố

| Hiện tượng | Nguyên nhân và cách xử lý |
| --- | --- |
| `Manifest not found` | Chưa chạy `extract_plates.py`. Chạy bước 1 trước |
| `Cannot bind 127.0.0.1:8765` | Cổng đang bận, thường do một bản công cụ khác còn chạy. Dùng `--port 9000` |
| Khung bên phải báo "Không kiểm tra được định dạng" | Không import được `ai.inference.normalizer` (thường do thiếu NumPy trong venv đang dùng). **Vẫn gán nhãn bình thường được**, chỉ mất dấu tích tự động |
| Ảnh hiện ra quá nhỏ / mờ | Chạy lại bước 1 với `--target-height 300 --overwrite` |

Máy chủ chỉ lắng nghe ở địa chỉ loopback `127.0.0.1` và **không có xác thực**, vì
nó không hề lộ ra mạng. Đừng đổi `--host` sang địa chỉ khác nếu chưa thêm cơ chế
xác thực.
