# Sàn độ tin cậy cho fragment dòng trên của rescue (2026-07-21)

## Lỗi thực địa

Người thực hiện chỉ ra trang Lịch sử hiển thị các bản ghi sai từ ảnh
`nhieu-bien-2.png`: nổi bật nhất là **`81B-9458`** — một biển *không tồn tại*,
trình bày như biển ô tô hợp lệ, trong khi crop kèm theo ai nhìn cũng đọc được
là `59-X1 / 394.58`.

## Chẩn đoán — đo trực tiếp trên crop lỗi

Chuỗi sự kiện: crop chỉ **34×26 px** → OCR strip chỉ đọc được dòng dưới
`394.58` (không hợp lệ) → bước rescue dòng trên đọc nửa trên ra fragment
**`81` với độ tin cậy 0,709** → ghép `81` + `39458` → bộ sửa vị trí bẻ ký tự
thứ ba thành chữ (`3`→`B`) → **`81B-9458` khớp mẫu ô tô, hợp lệ**. Tiêu chí
chấp nhận của rescue ("chuỗi ghép validate được") hoá ra **quá yếu trên crop
dưới 40 px**: bộ sửa vị trí đủ mạnh để bẻ một fragment đọc nhoè thành biển
đúng ngữ pháp.

Đo phân bố độ tin cậy fragment trên mọi ca có hồ sơ:

| Fragment | Đúng/Sai | Conf |
|---|---|---:|
| `USteo` (crop 25×16) | sai | 0,436 |
| `81` (crop 34×26) | sai | 0,709 |
| `59.51` (vết cắt 0,417 của ca đúng) | sai | 0,740 |
| `59-S1` (ca rescue yếu nhất trong 13 ca hồ sơ) | **đúng** | 0,862 |
| `77-H5` (nghiêng, đã giãn) | **đúng** | 0,953 |
| `77-H5` (chính diện) | **đúng** | 0,975 |
| `29E` | **đúng** | 0,995–0,998 |

Hai quần thể **tách nhau bằng khoảng trống 0,740 → 0,862**.

## Sửa

Thêm sàn `RESCUE_MIN_UPPER_CONFIDENCE = 0.8` — fragment dưới sàn bị bỏ,
bậc thang thử vết cắt tiếp theo. Bản nháp đầu đặt 0,9 và bị chính bộ hồi quy
bác: nó làm mất ca `59-S1` (0,862) mà không thêm an toàn nào; 0,8 chẻ giữa
khoảng trống, hai phía đều còn biên ~0,06.

## Kiểm chứng

- **Hồi quy 13 ca rescue** trong [15-two-line-fallback-700.json](15-two-line-fallback-700.json):
  **13/13 giữ được** với sàn 0,8 (bản nháp 0,9: 12/13).
- Hai ca lắp ghép sai bị chặn, và qua pipeline đầy đủ còn được **thưởng
  thêm**: khi fragment nhoè bị sàn loại bỏ, lần đọc vẫn "thất bại" nên **bậc
  thang thử-lại nắn hình** (báo cáo 21) được quyền chạy — và biến thể nắn
  hình đọc đúng. Kết quả cuối qua `POST /api/detect/image`:
  `59-X1 / 394.58` → **`59X1-394.58` ĐÚNG** (trước đây `81B-9458` sai),
  `76-B1 / 418.73` → **`76B1-418.73` ĐÚNG** (trước đây `73G3-418.73` sai).
  Hai tầng sửa lỗi độc lập hoá ra ghép nối: sàn tin cậy chặn đáp án sai
  *chiếm chỗ*, nhường lượt cho biến thể hình học tìm đáp án đúng.
- `BA-104` (crop 25×16) vẫn còn: đó là **đọc thẳng** khớp mẫu quân đội, không
  qua rescue — được gắn cờ cảnh báo/không hợp lệ trên giao diện, đúng nguyên
  tắc nhận-để-loại-trừ, không bị trình bày như biển dân sự.
- Hai bản ghi sai còn lại người dùng chỉ ra (`73G3-418.73`, `59YR-204.30`)
  là **đọc thẳng sai trên crop 31–51 px** — đã thử upscale ×2/×3/×4 trước khi
  tách dòng: không đổi (chỉ ×4 sửa được X nhưng hỏng B). Không còn nút vặn
  rẻ; thuộc hạn chế OCR crop nhỏ đã ghi ở Chương 6, hướng xử lý thật là
  super-resolution hoặc fine-tune recognizer (ngoài phạm vi hiện tại).
- Bộ test: **986 pass** (+1 test ghim fragment 0,7 bị loại).

## Bài học (bổ sung cho bài học ở báo cáo 21)

"Validate được" là điều kiện **cần**, không phải điều kiện **đủ** — với một
bộ sửa vị trí đủ mạnh, chuỗi rác cũng có thể được uốn thành biển đúng ngữ
pháp. Mọi bước *lắp ghép* chuỗi từ nhiều lần đọc phải mang theo bằng chứng
độ tin cậy của từng mảnh, không chỉ tính hợp lệ của tổng thể.
