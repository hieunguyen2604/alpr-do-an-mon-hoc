# Lần fine-tune đầu tiên thất bại — nguyên nhân và cách chặn tái diễn (2026-07-28)

Kết quả âm, ghi lại đầy đủ vì nó là bằng chứng cho một sai lầm phương pháp
đáng nhớ hơn cả một lần thành công.

## 1. Đo được gì

Model fine-tune (`models/rec_finetuned/`) đọc qua pipeline đầy đủ, so trực
tiếp với model gốc trên cùng ảnh:

| Ảnh | Biển thật | Model gốc | Model fine-tune |
|---|---|---|---|
| 1dong-1.png | 51G31691 | ✅ 51G31691 | ❌ `54Z47252V` |
| 2dong-1.png | 59K120173 | ✅ 59K120173 | ❌ `542A5PA52V5242A5A2V` |
| 2dong-2.png | 59K122599 | ✅ 59K122599 | ❌ `542A5A52752427A5PA` |
| 2dong-3.png | 51P54578 | ✅ 51P54578 | ❌ `542424242A5A275…` |
| bien-vang-kinh-doanh.jpg | 29E01566 | ✅ 29E01566 | ❌ `55ZV4542V` |
| bien-xanh-nha-nuoc-2.jpg | 65A00450 | ✅ 65A00450 | ❌ `5525422A275424202A5PA5V` |
| nhieu-bien-3.png | 77H54374 | ✅ 77H54374 | ❌ `534275PA5V` |

**0/7 so với 7/7.** Không phải "kém hơn một chút" mà là **rác hoàn toàn** —
chuỗi lặp vô nghĩa gồm vài ký tự `5`, `4`, `2`, `A`, `V`, đúng dáng của một
model học từ nhãn không liên quan gì tới ảnh.

## 2. Nguyên nhân: tập huấn luyện sai nhãn, sinh ra một cách im lặng

Bản `scripts/dataset/build_rec_finetune_set.py` dùng để sinh dữ liệu có một
cơ chế "ảnh thay thế": khi không mở được ảnh gốc, nó đi tìm trong
`docs/reports/` một ảnh **có tên chứa chuỗi biển số** rồi dùng tạm.

Điều kiện kích hoạt luôn đúng trên máy không phải máy phát triển:
`datasets/raw/**` nằm trong `.gitignore`, nên **clone kho mã về là không có
ảnh gốc**. Hệ quả dây chuyền:

1. Mọi ảnh gốc đều mở không được ⇒ cơ chế thay thế chạy cho mọi dòng.
2. Ảnh được ghép với nhãn của **một biển khác** ⇒ tập huấn luyện sai nhãn.
3. Model học đúng thứ nó được dạy: ánh xạ ảnh → chuỗi ngẫu nhiên.
4. Sai lầm chỉ lộ ra ở **bước đo cuối cùng**, sau khi đã tốn công train.

Không có bước nào trong chuỗi này báo lỗi. Đó mới là vấn đề thật.

## 3. Đã chặn thế nào

- **Gỡ bỏ hoàn toàn cơ chế ảnh thay thế**, để lại một khối chú thích ghi rõ
  chuyện đã xảy ra và cấm khôi phục.
- **Đếm riêng số ảnh nguồn thiếu** và **dừng hẳn** khi vượt 5% tổng số dòng,
  kèm thông báo chỉ đúng nguyên nhân (`datasets/raw` nằm trong gitignore) và
  chỗ tra cách tải lại.
- Chạy lại trên máy có ảnh gốc: **6.672 train / 571 val, thiếu 0** — đúng
  như trước, tức bản vá không làm hỏng đường chạy đúng.

## 4. Model hỏng có ảnh hưởng hệ thống không

**Không, và giờ nó đã bị gỡ khỏi kho mã.**

`ALPR_OCR_REC_MODEL_DIR` mặc định rỗng ở cả `docker-compose.yml`,
`backend/core/config.py` và `.env`, nên hệ thống chưa từng nạp model hỏng —
nó luôn chạy model gốc.

Ngày 28/07/2026, `models/rec_finetuned/` (4 tệp, 7,5 MB) được **xoá khỏi kho
mã**. Giữ lại một model đọc ra chuỗi rác chỉ tạo rủi ro: ai đó bật cờ lên vì
tưởng đã có model tốt. Đường dẫn `models/rec_finetuned/` vẫn là **đích xuất**
của lần train sau — script, notebook và README đều trỏ tới đó, nên chỉ cần
train đạt là thư mục xuất hiện trở lại đúng chỗ.

Vẫn giữ `models/pretrained/en_PP-OCRv5_mobile_rec_pretrained.pdparams`
(70 MB): đó là **trọng số gốc của PaddleOCR**, không phải sản phẩm của lần
train hỏng, và là nguyên liệu đầu vào cho mọi lần fine-tune về sau.

## 5. Bài học

Cùng một họ với bài học ở [21](21-skew-retry.md) và
[22](22-rescue-confidence-floor.md), nhưng ở tầng dữ liệu:

> **Thiếu dữ liệu phải dừng lại và nói rõ, không được im lặng thay bằng thứ
> gần đúng.** Một `fallback` viết với ý tốt đã biến "không chạy được" — một
> thất bại rẻ, phát hiện trong 5 giây — thành "chạy ra kết quả sai" — một
> thất bại đắt, phát hiện sau hàng giờ GPU và chỉ nhờ có bước đo đối chứng.

Và hệ quả trực tiếp cho quy trình: **luôn so model mới với model cũ trên
cùng dữ liệu trước khi bật**. Nghi thức đo trong
`ai/training/README-rec-finetune.md` đã bắt buộc điều này từ đầu, và đây là
lần nó chứng minh giá trị.

## 6. Muốn thử lại thì cần gì

1. Chạy sinh dữ liệu **trên máy có `datasets/raw/`** (hoặc chép thư mục đó
   sang máy train) — script giờ sẽ dừng nếu thiếu.
2. Kiểm tra vài mẫu bằng mắt: mở `datasets/processed/rec_finetune/images/`
   và đối chiếu với nhãn trong `train.txt`.
3. Train, rồi **chạy lại chính phép so ở mục 1** trước khi bật cờ.
