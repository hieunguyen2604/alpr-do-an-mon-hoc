# Bậc thang thử-lại cho biển nghiêng/méo — cài đặt và đo (2026-07-21)

Xử lý hạn chế **6.3.9** của luận văn (bước rectify chưa từng được cài đặt),
theo đúng hướng **6.4.9** — nhưng kết quả đo bắt buộc phải đổi thiết kế giữa
chừng, và chính chỗ đổi đó là bài học đáng giá nhất của báo cáo này.

## 1. Lần thử thứ nhất: rectify luôn-bật — THẤT BẠI có số liệu

Cài đúng bậc 1+2 của mục 6.4.9: nhị phân hoá → `cv2.minAreaRect` → xoay phẳng
→ cắt lại đúng hình chữ nhật → đo lại số dòng trên ảnh đã nắn. Kiểm chứng hình
học trên ảnh tổng hợp: chuẩn cả hai chiều nghiêng, biển 1 dòng nghiêng ±15–25°
từng bị nhận nhầm 2 dòng (tỷ lệ hộp 2,24) về đúng 1 dòng (4,7).

Nhưng đo trên **tập đúng kỷ luật 6.4.9** — ảnh cắt do chính detector sinh ra
từ 36 khung video demo — thì luôn-bật **thua**: 42 → 40 lần đọc hợp lệ. Hai
lần đọc đang tốt (`76B191873`, `59X139458`) bị hình chữ nhật fit sai trên
crop nhỏ/mờ cắt mất ký tự, thành `C1873`, `55UE39458`. Đúng như luận văn
cảnh báo: *phép đo trên tập chứa dạng lỗi chứng minh được lợi ích; phép đo
này thì chứng minh được tác hại.*

Phát hiện thứ hai, quan trọng hơn: mở crop khung 168 ra xem thì biển
`77-H5 / 4374` **không hề xoay trong mặt phẳng** — nó **ngửa ra sau**
(foreshortening phối cảnh): hai dòng chữ vẫn ngang, chỉ bị nén dọc đến mức tỷ
lệ hộp 3,48 vượt ngưỡng 2,5. Xoay phẳng về nguyên tắc không cứu được ca này;
góc ước lượng là 0° nên bước nắn còn chẳng kích hoạt.

## 2. Thiết kế cuối: bậc thang thử-lại chỉ khi đọc hỏng

Chuyển toàn bộ hình học ra **sau** cổng "lần đọc đầu đã thất bại" — cùng
triết lý với rescue dòng trên đã có: *một lần thử không bao giờ được tốn hơn
những gì nó có thể thắng.*

```
đọc như cũ ──hợp lệ──▶ xong (baseline bất biến theo cấu trúc)
     │ hỏng
     ▼
biến thể 1: rectify xoay phẳng (chỉ khi phép nắn thật sự đổi crop)
biến thể 2: kéo giãn dọc ×2   (chỉ khi tỷ lệ hộp nằm trong dải mơ hồ 2,5–4,2)
     │ mỗi biến thể: đọc lại → chuẩn hoá → rescue dòng trên nếu cần
     ▼
chỉ nhận khi chuỗi mới VALIDATE; không thì giữ nguyên kết quả cũ
```

Chuỗi cứu khung 168 hoạt động đúng như bảng thiết kế: giãn dọc ×2 → tỷ lệ
1,74 → vào đường 2 dòng → đọc được dòng dưới `4374` (chưa hợp lệ) → rescue
dòng trên tại vết cắt 0,55 đọc `77-H5` (conf 0,95) → ghép `77H5-4374` →
hợp lệ.

Cài đặt: `rectify_plate` + `stretch_vertical` trong `ai/inference/two_line.py`;
`should_retry_skewed` + `retry_skewed_variants` trong `ai/inference/pipeline.py`;
cờ `ALPR_RECTIFY_ENABLED` (mặc định bật) để Phase 7 ablate.

## 3. Kết quả đo cuối (36 khung video demo, so cùng dữ liệu)

| Chỉ số | Tắt bậc thang | Bật bậc thang |
|---|---:|---:|
| Lượt nhìn thấy biển | 66 | 66 |
| Lần đọc hợp lệ | 42 | **48 (+6)** |
| Lần đọc bị mất so với baseline | — | **0** (đúng theo cấu trúc) |
| Khung 168 (ca 6.3.9) | rỗng | **`77H5-4374`**, conf 0,785, 2 dòng |

Dữ liệu thô: [21-skew-retry-ab.json](21-skew-retry-ab.json).

**Ghi trung thực về 6 lần đọc mới:** 3 lần là `77H54374` — đúng với biển thật
(khung 155/160/168). 3 lần còn lại (`31L16147`, `53L1547`, `59F27793`) là đọc
sai/thiếu của các biển rất mờ ở xa trong cùng cảnh — chuỗi hợp lệ về định dạng
nhưng không khớp biển thật. Đây là lớp lỗi OCR-trên-crop-mờ sẵn có của hệ
thống (không có bậc thang thì các khung đó trả về **không gì cả**), nhưng phải
nêu rõ: bậc thang đổi *một phần* "không đọc được" lấy "đọc được nhưng có thể
sai" — với video, lớp gộp biến thể + bỏ phiếu đa số ở tầng lưu lịch sử là
tấm lưới đỡ cho đánh đổi này.

## 3b. Sự cố thực địa ngay sau triển khai — và hai cổng chặn bổ sung

Ngay sau khi triển khai, người thực hiện tải một ảnh biển quân đội
(`KV-69-38`, nền đỏ) và hệ thống trả về **`14D7-069.38`, xe máy, hợp lệ** —
đúng lớp lỗi *tự tin-mà-sai* tệ nhất mà commit `d336b07` từng sửa, sống lại
qua cửa sau.

Cơ chế: biển quân đội được **đọc đúng** nhưng *cố ý* mang cờ `invalid`
(nhận-để-loại-trừ khỏi hệ thống dân sự). Cổng thử-lại phiên bản đầu chỉ nhìn
`not is_valid_format`, nên coi lần đọc thành công đó là thất bại → đọc lại
trên biến thể giãn dọc → OCR nhoè `KV` thành `14D7` → chuỗi ghép
`14D706938` khớp mẫu xe máy cũ → được nhận vì "validate". Cổng chống-sửa-biển-
quân-đội trong normalizer không cứu được, vì chuỗi *mới* không còn hình dạng
quân đội để nó nhận ra.

Sửa bằng hai cổng, đều có test ghim:

1. **Cổng loại biển:** chỉ thử lại khi lần đọc đầu *không phân loại được*
   (`kind` rỗng/unknown). Một chuỗi đã được xếp vào bất kỳ họ biển nào —
   kể cả quân đội — là một *phát hiện* phải giữ, không phải thất bại để sửa.
2. **Cổng màu nền (phòng thủ chiều sâu):** crop nền **đỏ** không bao giờ được
   thử lại, bất kể ký tự nói gì — che nốt trường hợp lần đọc đầu mờ đến mức
   không nhận ra hình dạng quân đội nhưng màu vẫn nói thật.

Đo lại sau vá: 16 ảnh demo giữ nguyên 14/16 (`bien-do-quan-doi.jpg` trả đúng
`KV-6938` / quân đội / đỏ / invalid), video vẫn cứu được `77H54374` (17 bản
ghi). Bộ test 985.

Bài học ghi vào luận văn: **"không hợp lệ" không đồng nghĩa "đọc hỏng"** —
trong hệ thống này cờ `invalid` mang *hai* nghĩa (đọc thất bại ↔ nhận diện
thành công một biển ngoài phạm vi dân sự), và mọi cổng quyết định dựa trên cờ
đó buộc phải phân biệt được hai nghĩa ấy.

## 4. Còn lại gì

- **Nắn phối cảnh 4 điểm** (bậc 3 của 6.4.9) vẫn chưa cài — bậc thang hiện
  cứu ca ngửa-ra-sau bằng giãn dọc thô, đủ cho ca đã đo nhưng không phải
  nghiệm tổng quát.
- Đóng góp trên **toàn tập nhãn** chưa đo (tập đó gần chính diện, dự kiến
  "không đổi" — đúng thiết kế cổng thất bại); số A4–A7 công bố không bị
  ảnh hưởng vì baseline bất biến.

## 5. Tệp liên quan

- `ai/inference/two_line.py` — `rectify_plate`, `stretch_vertical` (+ 11 test)
- `ai/inference/pipeline.py` — `should_retry_skewed`, `retry_skewed_variants` (+ 7 test)
- `ai/inference/config.py`, `docker-compose.yml` — cờ `ALPR_RECTIFY_ENABLED`
- Luận văn: mục 6.3.9 (bổ sung đoạn cập nhật), 6.4.9 (chuyển trạng thái đã thực hiện)
