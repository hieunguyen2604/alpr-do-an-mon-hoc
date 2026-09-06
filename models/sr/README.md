# Mô hình Super-Resolution cho cơ chế thử lại đa tầng trong OCR

| Tệp | Kiến trúc | Hệ số | Nguồn | Giấy phép |
|---|---|---|---|---|
| `FSRCNN_x3.pb` (40 KB) | FSRCNN (Dong et al., ECCV 2016) | ×3 | github.com/Saafke/FSRCNN_Tensorflow (repo được tài liệu OpenCV dnn_superres dẫn) | MIT |
| `FSRCNN_x4.pb` (41 KB) | FSRCNN | ×4 | như trên | MIT |

Tải ngày 2026-07-24. Dùng bởi `ai/inference/superres.py` để phóng đại crop
biển số nhỏ (<200 px) khi lần đọc đầu thất bại — đo được cứu 2/4 ca crop
nhỏ đang sai (`59F227793` 32×23 px, `67H148066` 171×120 px), chi tiết tại
`docs/reports/24-sr-retry.md`. Cần `cv2.dnn_superres` (gói
opencv-contrib); khi thiếu, hệ thống tự bỏ qua biến thể SR.
