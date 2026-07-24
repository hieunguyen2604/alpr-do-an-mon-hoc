# Fine-tune bộ nhận dạng ký tự (PP-OCRv5 mobile rec) trên biển số Việt Nam

Đường ray đầy đủ cho hướng phát triển có kỳ vọng lớn nhất còn lại của luận
văn: nâng độ chính xác chuỗi **biển 2 dòng** từ ~0,60 lên vùng 0,8+ bằng
fine-tune model recognition trên đúng dữ liệu miền. Ba mảnh, hai mảnh đầu đã
chạy được ngay:

## 1. Sinh dataset (local, đã chạy — tái tạo được)

```bash
backend/.venv/Scripts/python scripts/dataset/build_rec_finetune_set.py
```

Đọc `datasets/annotations/plate_labels.csv` (2.801 chuỗi đã kiểm chứng, 80%
biển 2 dòng) và xuất `datasets/processed/rec_finetune/`:

- **6.672 mẫu train** = 2.224 gốc × (1 bản chuẩn + 2 bản augment nhắm đúng
  cụm lỗi đã đo: thu nhỏ 14–30 px rồi phóng lại, và nghiêng ±8° + mờ + nén
  JPEG) · **571 mẫu val sạch** (không augment — val phải đo hiệu năng thật).
- Điểm thiết kế quan trọng nhất: mọi ảnh xuất **sau tiền xử lý production**
  — biển 2 dòng thành strip ghép ngang cao 64 px, y hệt thứ recognizer đang
  đưa vào engine. Kỷ luật 6.4.9: tập huấn luyện phải chứa đúng thứ hệ thống
  gặp, nếu không phép đo nói dối.
- `dict36.txt`: charset 36 ký tự theo quyết định Phase 1 (cấm thu hẹp còn
  20 chữ — chữ `R` hợp lệ ở seri xe máy).

Nén để đưa lên Colab: `cd datasets/processed && zip -r rec_finetune.zip rec_finetune`

## 2. Huấn luyện (Colab GPU)

Mở `ai/training/finetune_ppocr_rec_colab.ipynb` trên Colab (runtime T4),
chạy tuần tự: cài paddle-gpu → mount Drive → tải pretrained
`en_PP-OCRv5_mobile_rec` → train 30 epoch (lr 1e-4, batch 128) → eval →
export inference model → zip về Drive. Các URL/тên config có cell kiểm tra
riêng để dễ chẩn đoán khi upstream đổi.

## 3. Tích hợp và đo lại (local)

Giải nén về `models/rec_finetuned/` rồi bật bằng **một biến môi trường** —
mọi dây nối đã sẵn (`InferenceConfig.ocr_rec_model_dir`, kiểm tra tồn tại
lúc khởi động, fail to thay vì âm thầm dùng model gốc):

```bash
# Docker (.env):
ALPR_OCR_REC_MODEL_DIR=/app/models/rec_finetuned
# Local:
set ALPR_OCR_REC_MODEL_DIR=models/rec_finetuned
```

**Nghi thức đo bắt buộc trước khi công bố bất kỳ con số nào:**

1. `ocr_accuracy.py` toàn tập — so A4–A7 với baseline (`docs/reports/16-*`);
   chỉ tiêu thành công: **A6 biển 2 dòng tăng ≥ 5 điểm, biển 1 dòng không
   giảm**.
2. Bộ hồi quy: 16 ảnh lõi (`demo/images/expected.json`), 13 ca rescue
   (`15-two-line-fallback-700.json`), 3 video demo.
3. Ablation: chạy cả bật lẫn tắt (`ALPR_OCR_REC_MODEL_DIR` có/không) để số
   chênh lệch quy được đúng cho fine-tune, không lẫn với bậc thang thử-lại.
4. Thất bại thì ghi trung thực vào báo cáo và gỡ cờ — model gốc vẫn là
   mặc định cho đến khi có số chứng minh.
