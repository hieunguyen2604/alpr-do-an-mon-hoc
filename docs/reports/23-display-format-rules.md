# Bộ quy tắc định dạng hiển thị biển số theo loại xe (2026-07-24)

**Nguồn sự thật duy nhất.** Chuỗi lưu trữ chuẩn là *không có dấu phân cách*
(`51H60969`); dấu gạch và dấu chấm chỉ được chèn lại ở tầng hiển thị, bởi
đúng một hàm — `VietnamesePlateNormalizer.format_for_display` — và theo đúng
bảng dưới đây. **Badge loại xe và cách nhóm số phải cùng đến từ một quyết
định phân loại** (`KindDecision`): từ 24/07/2026 pipeline truyền thẳng `kind`
đã chốt vào hàm format, chấm dứt tình trạng badge nói "ô tô" mà chuỗi lại
nhóm kiểu xe máy.

## 1. Bảng quy tắc theo loại

| Loại (`plate_kind`) | Cấu trúc chuỗi | Quy tắc nhóm hiển thị | Ví dụ |
|---|---|---|---|
| `car` / `blue_car` (số 5 chữ số) | `TT` + `S` + `NNNNN` | `TTS-NNN.NN` | `51H60969` → **51H-609.69** |
| `car` / `blue_car` (số 4 chữ số) | `TT` + `S` + `NNNN` | `TTS-NNNN` (không dấu chấm) | `51A1987` → **51A-1987** |
| `motorcycle_old` / `blue_motorcycle` (số 5) | `TT` + `SD` + `NNNNN` | `TTSD-NNN.NN` | `59X406909` → **59X4-069.09** |
| `motorcycle_old` (số 4) | `TT` + `SD` + `NNNN` | `TTSD-NNNN` | `51P54578` → **51P5-4578** |
| `motorcycle_new` | `TT` + `SS` + `NNNNN` | `TTSS-NNN.NN` | `59XB20430` → **59XB-204.30** |
| `special` (LD, DA, R, T…) | `TT` + `CODE` + `N…` | `TTCODE-N[NN.NN]` | `61R02309` → **61R-023.09** |
| `diplomatic` | `TT` + `CCC` + `NG/QT/CV/NN` + `NN` | `TT-CCC-CODE-NN` | `80346NG68` → **80-346-NG-68** |
| `military` | `UU[S]` + `N…` | `UU-NNNN` | `KV6938` → **KV-6938** |
| `unknown` | — | **giữ nguyên chuỗi, không tô vẽ** | `27793` → 27793 |

`TT` = mã tỉnh (81 giá trị hợp lệ) · `S` = chữ seri (tập L20) · `D` = chữ số
seri 1–9 · quy ước dấu chấm: **chỉ số 5 chữ số mới có dấu chấm trước 2 chữ số
cuối**, đúng như in trên biển vật lý (QCVN 08:2024/BCA).

## 2. Quy tắc phân xử ca mơ hồ 8 ký tự (car ↔ motorcycle_old)

Chuỗi 8 ký tự dạng `51H60969` đọc được cả hai cách: ô tô `51H`+`60969` hay xe
máy cũ `51H6`+`0969`. Thứ tự bằng chứng, mạnh trước yếu sau:

1. **`line_count = 1`** → chắc chắn **ô tô** (xe máy không có biển 1 dòng).
2. **Chuỗi OCR thô chứa nhóm `DDD.DD`** (ví dụ `609.69`) → chắc chắn **ô tô**:
   biển vật lý chỉ in dấu chấm cho số 5 chữ số, mà chỉ cách đọc ô tô mới có
   số 5 chữ số. Đây là quy tắc thêm 24/07/2026, sửa đúng ca thực địa
   `51H/609.69` (đuôi SUV) và `51C/920.87` (xe tải, nền vàng) bị dán nhầm
   badge "Xe máy". Chấp nhận cả dấu phẩy (`609,69`) vì OCR phân giải thấp
   đọc lẫn hai ký tự này.
3. **`line_count = 2` và không có dấu chấm** → ưu tiên **xe máy** theo prior
   đã đo (450/452 biển 2 dòng mơ hồ trong corpus là xe máy — số 4 chữ số
   của chúng không bao giờ in dấu chấm nên không đụng quy tắc 2), giữ cờ
   `is_ambiguous` vì đây là suy đoán, không phải chứng minh.

## 3. Nhãn tiếng Việt trên giao diện (frontend `plateClass.ts`)

Badge loại xe ghép từ `plate_kind` + `plate_color`; ví dụ `car` + nền vàng →
"Ô tô kinh doanh vận tải", `motorcycle_*` + vàng → "Xe máy kinh doanh vận
tải", `blue_car` → "Xe cơ quan nhà nước", `military` → "Xe quân đội" (kèm
cảnh báo ngoài phạm vi dân sự). Vì badge và nhóm số cùng nguồn `kind`, sửa
phân loại là badge và chuỗi cùng đổi — không bao giờ lệch nhau nữa.

## 4. Điểm neo cài đặt và kiểm thử

- Quy tắc nhóm: `ai/inference/normalizer.py::format_for_display` (tham số
  `kind` mới — nhóm theo loại đã chốt, tự suy chỉ khi không được cung cấp).
- Bằng chứng dấu chấm: `ai/inference/normalizer.py::_FIVE_DIGIT_DOT_GROUP_RE`
  + `detect_plate_kind(raw_text=…)`.
- Pipeline truyền `kind`: `ai/inference/pipeline.py::_format_for_display`
  và ba điểm gọi (đọc chính, rescue, retry).
- Test ghim: `tests/test_normalizer.py` (các test `printed_dot…`,
  `format_for_display_follows_the_established_kind`, bảng
  `test_format_for_display`).
