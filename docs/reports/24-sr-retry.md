# Super-resolution cho crop nhỏ trong bậc thang thử-lại (2026-07-24)

Trả lời câu hỏi "tối ưu OCR kiểu gì ít công nhất": trong các hướng ở mục 6.4
luận văn, đây là hướng rẻ nhất còn lại — không huấn luyện, không dữ liệu mới,
chạy CPU — nhắm thẳng **cụm lỗi lớn nhất còn tồn tại**: 6/9 ca đọc sai là
crop < 200 px (đo 24/07). Fine-tune recognizer trên Colab vẫn là cú đấm lớn
(kỳ vọng 2 dòng 0,60 → 0,8+), báo cáo này chỉ là bậc rẻ đi trước.

## 1. Thí nghiệm trước, cài đặt sau

Upscale thường (cubic ×2–4) đã thử từ báo cáo 22: không cứu được gì — nội
suy không tạo ra chi tiết. Thử SR học được (FSRCNN/ESPCN, model 40–92 KB,
MIT, đúng repo mà tài liệu OpenCV `dnn_superres` dẫn) trên 4 crop nhỏ đang
sai, đọc qua đúng chuỗi sản xuất:

| Ca (kích thước) | Baseline | Tốt nhất sau SR | Kết cục |
|---|---|---|---|
| `59F227793` (32×23) | `27793` (mất dòng trên) | FSRCNN — **ĐÚNG trọn** | ✅ |
| `67H148066` (171×120, tối) | `51A8066` | FSRCNN×4 — **ĐÚNG trọn** | ⚠️ xem mục 4 |
| `59XB20430` (51×37) | `59YR…` | `59XR…` — X hồi, B→R còn | ✳️ chưa trọn |
| `51K14116` (25×16) | `BA104` (gắn cờ) | rác, không validate | an toàn |

## 2. Ba chướng ngại thật khi đưa vào sản xuất — và cách xử

**(a) `cv2.dnn_superres` nằm trong gói contrib, và namespace `cv2` đang bị
ba gói giẫm nhau** (đúng hiểm hoạ đã ghi trong deployment guide — venv local
có module `dnn_superres` nhưng RỖNG). Xử: Dockerfile gỡ sạch mọi biến thể
opencv rồi cài `opencv-contrib-python-headless` **cuối cùng** — một chủ sở
hữu duy nhất cho `cv2`, chấm dứt vĩnh viễn trò giẫm namespace; venv local
force-reinstall contrib. Module `ai/inference/superres.py` **tự hạ cấp**
khi môi trường không có contrib: bậc thang mất một biến thể, không bao giờ
mất một lần đọc.

**(b) SR không được phép gây thoái lui.** Đặt SR làm biến thể trong bậc
thang thử-lại (sau rectify/giãn dọc, chỉ crop ≤ 200 px — `RETRY_SR_MAX_SIDE`,
vì crop 600 px+ sai vì lý do khác): chỉ chạy khi lần đọc đầu đã hỏng, chỉ
được nhận khi validate, qua sàn tin cậy fragment. Cờ riêng
`ALPR_SR_RETRY_ENABLED` để ablate độc lập với `ALPR_RECTIFY_ENABLED`.

**(c) Hai nửa đúng của một biển nằm ở hai lần đọc khác nhau.** Trên bản
OpenCV 4.10 của sản xuất, crop `59-F2/277.93`: lần đọc gốc giữ dòng dưới
(`27793`), biến thể SR×4 đọc được dòng trên (`59 F2`, conf 0,849 — qua sàn
0,8) nhưng strip của chính nó lại hỏng (`m93`) — mỗi mảnh một nơi, không
biến thể nào tự đủ. Thêm **rescue lai**: dòng trên từ ảnh biến thể + dòng
dưới từ lần đọc gốc, cùng tiêu chí chấp nhận và cùng sàn tin cậy. Đây là ca
`59F2-277.93` hồi phục trọn vẹn qua pipeline thật.

## 3. Kết quả sau tích hợp

- `59F227793`: **đọc đúng `59F2-277.93`** qua `POST /api/detect/image`
  (trước: `27793` không hợp lệ).
- `51K14116`, `59XB20430`: không đổi — SR không đủ cứu, và quan trọng hơn:
  **không ca nào xấu đi** (mọi biến thể rác bị cổng validate loại).
- Bộ test 993 (+4 test: gating theo kích thước, hạ cấp khi thiếu contrib,
  cấu trúc rescue lai).

## 4. Ghi trung thực

- `67H148066` cứu được trong thí nghiệm **nhưng không cứu được trong sản
  xuất** — vì baseline của nó đọc ra `51A8066`, một chuỗi *hợp lệ-nhưng-sai*:
  bậc thang chỉ chạy khi đọc *hỏng*, mà chính điều đó là hợp đồng chống
  thoái lui. Cứu ca này đòi nghi ngờ cả lần đọc hợp lệ — đánh đổi nguy hiểm
  hơn lợi ích, không làm.
- Kết quả SR **phụ thuộc phiên bản OpenCV** (thí nghiệm 5.0 và sản xuất
  4.10 cho fragment khác nhau ở biên) — lý do phải pin đúng
  `opencv-contrib-python==4.10.0.84` trong image.

  > **Đính chính 28/07/2026:** bản đầu của mục này ghi
  > `opencv-contrib-python-headless`. Sai, và sai theo hướng nguy hiểm: `paddlex`
  > kiểm tra phụ thuộc **theo tên gói pip**, nên bản `-headless` làm nó từ chối
  > khởi tạo và **toàn bộ OCR ngừng hoạt động**, chứ không chỉ mất siêu phân
  > giải. `deployment/docker/Dockerfile.backend` vẫn luôn ghim đúng bản không
  > headless — chỉ dòng văn bản này lệch với bản build thật.
- Cụm crop LỚN đọc sai (`50F01690`, `79E00392`, `51B09865`, 600 px+) là
  bài toán khác (nghi liên quan trần nén 64 px trước OCR) — chưa xử trong
  báo cáo này.
- Con đường nâng cấp thật sự cho toàn cụm 2 dòng vẫn là **fine-tune
  recognizer trên crop biển VN** (Colab GPU, dữ liệu nhãn có sẵn) — mục
  6.4 luận văn.
