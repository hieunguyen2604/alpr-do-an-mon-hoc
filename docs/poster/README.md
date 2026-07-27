# Poster A0

| Tệp | Vai trò |
|---|---|
| `10-poster-layout.md` | Đặc tả gốc: khổ, thang cỡ chữ T0–T7, bảng màu, nội dung từng khối |
| `poster.html` | Bản dựng thật, mọi kích thước bằng mm để khớp khổ in |
| `poster.pdf` | **Bản gửi nhà in** — đúng 841 × 1189 mm (A0 dọc) |
| `poster.png` | Ảnh xem trước, dùng để soát nhanh không cần trình đọc PDF |

## Kết xuất lại

```bash
cd frontend && node scripts/build_poster.mjs
```

Script chạy Chromium (Playwright) trên `poster.html`, xuất PDF khổ A0 và PNG
xem trước, đồng thời **cảnh báo mọi ảnh không tải được** — trên poster khổ lớn
một ô ảnh trống rất dễ lọt qua mắt.

## Những chỗ đã lệch khỏi đặc tả, và lý do

- **Lề 40 mm** thay vì 50 mm, **cỡ chữ hạ một nấc** (tên đề tài 90 pt, chữ thân
  28 pt): đúng bằng *ngưỡng tối thiểu* của đặc tả, để toàn bộ nội dung vừa
  **một** trang A0. Không có chữ nào dưới 20 pt.
- **Khối Giao diện chỉ còn một ảnh lớn** (trang Nhận dạng ảnh) thay vì ba ảnh:
  hai ảnh nhỏ đẩy cột phải vượt khổ, và ảnh trang chủ là ảnh duy nhất cho thấy
  kết quả AI thật.

## Việc còn lại trước khi in

1. **Chụp lại ảnh giao diện** (`cd frontend && npm run screenshots`) — ảnh hiện
   tại chụp trước 24/07/2026, khi trang ảnh còn nút *Nhận dạng*. Chụp xong chạy
   lại `build_poster.mjs`.
2. **Thay chữ `UIT` trong huy hiệu bằng logo trường thật** (sửa `.crest` trong
   `poster.html`).
3. In thử **A4 thu nhỏ** và soi ở khoảng cách tương đương 1,5 m trước khi in A0.
