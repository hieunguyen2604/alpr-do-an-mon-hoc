# Đánh giá trực tiếp bộ demo qua API đang chạy (2026-07-21)

**Cách đo:** bắn toàn bộ 16 ảnh `demo/images/` và `demo/demo-video.mp4` vào
`http://localhost:5173/api/...` — đi qua nginx của container frontend, đúng
đường mọi cú bấm trên giao diện đi — rồi đối chiếu với `demo/images/expected.json`.
Stack đo là bản Docker (`docker compose up`), suy luận CPU.

## 1. Phát hiện quan trọng nhất: hai nhãn ground truth SAI

Lần đo đầu cho 13/16 đúng chuỗi, trong đó `2dong-3.png` và `nhieu-bien-1.png`
bị đánh "sai loại xe" (hệ thống nói xe máy, kỳ vọng nói ô tô). Phóng to ảnh
gốc để phân xử thì **hệ thống đúng, file kỳ vọng sai**: biển in rõ
`51-P5 / 4578` và `56-P2 / 3135` — seri hai ký tự `P5`/`P2` của xe máy cũ.
Prior "2 dòng ⇒ xe máy" (đo 450/452 trên corpus có nhãn) một lần nữa được
xác nhận.

Đây là bài học phương pháp luận đáng ghi cho bảo vệ: **khi hệ thống lệch với
nhãn, đừng vội sửa hệ thống — hãy kiểm tra nhãn trước.** `expected.json` từ đó
được đổi ngữ nghĩa từ "kết quả đo tại thời điểm tạo" sang **ground truth do
người xác minh bằng mắt** (xem `demo/README.md`), sửa thêm 2 ca hệ thống đã
tốt lên từ sau khi file được tạo (`51A-1987` đọc đủ 2 dòng; taxonomy
`blue_car`).

## 2. Kết quả ảnh sau khi sửa ground truth

| Chỉ số | Kết quả |
|---|---|
| Đúng chuỗi biển + đủ 5 trường (display/kind/color/valid/lines) | **14/16** |
| Thời gian xử lý trung bình mỗi ảnh (server, CPU) | **0,45 s** (min 0,14 — max 1,41) |
| Phủ loại biển | 1 dòng, 2 dòng, nhiều biển, vàng, xanh (×2), đỏ quân đội, ngoại giao (×2), ảnh không biển — đều cho kết quả đúng kỳ vọng |

2/16 chưa đạt là `nhieu-bien-2.png` và `nhieu-bien-3.png`: các biển xe máy
2 dòng nhỏ/xa bị đọc sai một phần ký tự (`59XB→59YR`, `76B1→73G3`,
`59F2-277.93` chỉ đọc được dòng dưới). Đây chính là hạn chế trung tâm đã mô tả
ở mục 6.3 luận văn — ground truth giữ nguyên sự thật, không "chấm cho đẹp";
từng ca sai được chú thích ngay trong `expected.json` (trường `note`).

## 3. Video: hai lỗi thật, đã sửa và đo lại

Video demo 14 s (171 khung, lấy mẫu 35) chạy trọn luồng upload → 202 → poll →
completed trong ~18,5 s. Lần đo đầu lộ hai lỗi ở tầng lưu lịch sử
(`backend/services/detection_service.py`):

1. **12/27 bản ghi là rác** — box không đọc được chữ vẫn thành bản ghi (key
   theo lưới toạ độ 32 px nên xe di chuyển đẻ hàng loạt), mảnh OCR cụt
   (`S`, `BEK`, `187`, `27793`) mỗi mảnh một dòng. Đây là nguồn sinh ~2.000
   dòng "Không đọc được" đang làm xấu trang Lịch sử.
2. **Biến thể OCR không được gộp** — cùng một xe ra `51P51578` *và*
   `51P54578` (hai bản ghi), `76B41873`/`76B191873`/`76S111873` (ba bản ghi).

**Cách sửa** (kèm 16 unit test mới, tổng bộ test 951 → xanh):

- *Chặn từ gốc:* box không có chữ không vào lịch sử video; chuỗi **chưa phân
  loại được** ngắn hơn 7 ký tự (độ dài tối thiểu của một biển dân sự đầy đủ)
  bị bỏ. Chuỗi đã phân loại thì giữ bất kể độ dài/hợp lệ — biển quân đội
  `KV-6938` là một *phát hiện*, không phải rác.
- *Gộp biến thể:* hai chuỗi lệch nhau **≤ 1 phép sửa** và xuất hiện cách nhau
  **≤ 2 giây** được gộp làm một; bản thắng chọn theo (hợp lệ trước → số khung
  hình "bỏ phiếu" → độ tin cậy). Không dùng độ tin cậy đơn thuần vì đã đo được
  ca bản **sai** tự tin hơn bản đúng (0,919 so với 0,913) trong khi bản đúng
  thắng phiếu khung hình.
- Khoảng cách 2 phép sửa (`76B1…`/`76S1…`) **cố ý không gộp**: hai biển thật
  liên số cũng có thể lệch 1–2 ký tự, ngưỡng nới rộng đổi rủi ro gộp nhầm hai
  xe thật lấy việc dọn nốt vài dòng — không đáng.

**Sau sửa, đo lại cùng video:** 27 → **13 bản ghi**, 13/13 có chuỗi hợp lệ,
0 rác; `51P54578` (đúng) thắng `51P51578` (sai) nhờ đa số khung hình. Nhóm
`76…` còn 3 dòng như thiết kế chấp nhận.

## 4. Ghi chú không phải lỗi

`output_url = null` cho video job là **chủ đích có tài liệu** (render video
chú thích trên CPU nhân ~3 lần thời gian job; giao diện thay bằng overlay
trực tiếp khi phát). Câu trả lời phản biện: năng lực xem-kết-quả-trên-video
vẫn có, chỉ chuyển từ server-render sang client-overlay.

## 5. Tệp liên quan

- Sửa lọc/gộp: `backend/services/detection_service.py`
  (`_merge_frame_results`, `_collapse_variants`, `_within_one_edit`)
- Test mới: `tests/backend/test_video_merge.py` (16 test)
- Ground truth: `demo/images/expected.json` + `demo/README.md`
- Mô tả API cập nhật: `POST /api/detect/video` (Swagger)
