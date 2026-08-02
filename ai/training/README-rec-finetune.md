# Fine-tune bộ nhận dạng ký tự (PP-OCRv5 mobile rec) trên biển số Việt Nam

> ## ⛔ Trạng thái 02/08/2026 — ĐÃ DỪNG, và hai script đã bị gỡ khỏi kho
>
> **Bản giao hàng dùng model gốc, không dùng bản tinh chỉnh** —
> `ocr_rec_model_dir` mặc định `None`. Đồ án đã chạy **một lượt fine-tune hoàn
> chỉnh** (`models/rec_finetuned/`) và đo đủ bốn cấu hình ở mục 5.4: ở đúng chế
> độ production (det + rec) bản tinh chỉnh **thua 7,50 điểm**; nó chỉ thắng
> +12,46 điểm ở chế độ bỏ bước phát hiện chữ, mà chế độ đó đã bị bác trên ảnh
> toàn cảnh ([31-detection-stage-ablation.md](../../docs/reports/31-detection-stage-ablation.md)).
> Lượt fine-tune trên ngữ liệu đã gộp 521 biển hiếm **quyết định không chạy** —
> lý do đầy đủ ở [30-rare-plate-integration.md](../../docs/reports/30-rare-plate-integration.md)
> mục 8.3.
>
> **Hai script `finetune_ppocr_rec.py` và `finetune_ppocr_rec_mac.py` đã gỡ khỏi
> kho** ở đợt dọn dẹp cùng ngày; lấy lại từ lịch sử git nếu cần
> (`git show f14df03:ai/training/finetune_ppocr_rec.py`). Notebook Colab
> `finetune_ppocr_rec_colab.ipynb` **vẫn còn** và là đường chạy được duy nhất
> hiện tại.
>
> Tài liệu dưới đây giữ nguyên làm mô tả quy trình cho ai muốn chạy lại. Các
> lệnh gọi hai script đã gỡ sẽ **không chạy** cho tới khi khôi phục chúng.

Đường ray đầy đủ cho hướng phát triển có kỳ vọng lớn nhất còn lại của luận
văn: nâng độ chính xác chuỗi **biển 2 dòng** từ ~0,60 lên vùng 0,8+ bằng
fine-tune model recognition trên đúng dữ liệu miền. Ba mảnh, hai mảnh đầu đã
chạy được ngay:

## 0. Trọng số gốc — KHÔNG nằm trong kho mã

Tệp `models/pretrained/en_PP-OCRv5_mobile_rec_pretrained.pdparams` (68 MB) đã
**bỏ theo dõi git từ 02/08/2026**: nó là tệp công khai tải được, không phải sản
phẩm của đồ án, và một mình nó chiếm hơn một phần ba dung lượng kho mã.

Cả `finetune_ppocr_rec.py` lẫn notebook Colab đều **tự tải khi thiếu**, nên
thường không phải làm gì. Nếu cần lấy tay:

```bash
curl -L -o models/pretrained/en_PP-OCRv5_mobile_rec_pretrained.pdparams \
  https://paddleocr.bj.bcebos.com/PP-OCRv5/multilingual/official_pretrained_model/en_PP-OCRv5_mobile_rec_pretrained.pdparams
```

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

## 2b. Huấn luyện trên máy Mac Apple Silicon (không có GPU nào khác)

```bash
python3 ai/training/finetune_ppocr_rec_mac.py --smoke   # thử dây chuyền, vài phút
caffeinate -i python3 ai/training/finetune_ppocr_rec_mac.py
```

Chỉ dùng khi **không có Colab GPU** — trên Mac huấn luyện chạy **CPU thuần**,
khoảng **1,5–2,5 giờ mỗi epoch**, tức mặc định 12 epoch mất cỡ một ngày đêm.

Ba điều chỉ Apple Silicon mới cần, và cả ba đều làm hỏng lượt chạy chứ không
chỉ làm chậm — nên script này tách riêng khỏi `finetune_ppocr_rec.py`:

| Vấn đề | Xử lý |
|---|---|
| `libomp` của Homebrew và `libiomp5` của paddle cùng nạp ⇒ tiến trình chết giữa chừng | Đặt `KMP_DUPLICATE_LIB_OK` **trước** khi paddle được nạp |
| Nhân hiệu năng lẫn nhân tiết kiệm điện ⇒ mỗi rào đồng bộ phải chờ nhóm chậm | Hỏi `sysctl hw.perflevel0.logicalcpu`, ghim `OMP_NUM_THREADS` theo số nhân hiệu năng |
| `DataLoader` nhiều tiến trình dùng `fork` ⇒ treo im lặng trên macOS | `num_workers=0` ở cả train lẫn eval |

> **Không có Metal.** Kiểm trực tiếp trên paddle 3.3.1: gói không có
> `is_compiled_with_mps`, backend chỉ gồm CUDA / ROCm / XPU / IPU. Không tồn
> tại đường chạy GPU nào trên Mac. Bù lại, `paddlepaddle==3.3.1` **có** wheel
> `macosx_11_0_arm64` cho cp310–cp313 (kiểm trên PyPI), nên Mac cài đúng bản
> mà Windows và Docker đang dùng — gói tên `paddlepaddle`, không phải `-gpu`.

Luôn chạy `--smoke` trước. Nó chứng minh cả dây chuyền thông trong vài phút,
thay vì để máy chạy qua đêm rồi sáng ra phát hiện hỏng ở vòng lặp đầu tiên.

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
