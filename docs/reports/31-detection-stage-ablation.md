# Bước phát hiện chữ của PaddleOCR: giữ hay bỏ

**Ngày:** 2026-08-02
**Kết luận:** **GIỮ.** Công tắc `ALPR_OCR_SKIP_DETECTION` được cài đặt và giữ lại, **mặc định tắt**.
**Dữ liệu:** [29-reconly-ablation.json](29-reconly-ablation.json), [31-demo-ab-reconly.json](31-demo-ab-reconly.json)

---

## 1. Vì sao lại đặt câu hỏi này

Model fine-tune đo trên ngữ liệu 2.801 mẫu **kém hơn** model gốc ở mọi chỉ số
(A6 0,6762 so với 0,7512). Truy nguyên bằng cách đọc thẳng những tệp ảnh model đã huấn luyện trên
đó thì lộ ra một chênh lệch:

| Chế độ | Model fine-tune đọc đúng (300 ảnh train) |
|---|---:|
| Chỉ nhánh nhận dạng (rec) | **0,8233** |
| Cả phát hiện + nhận dạng (det → rec) | **0,2667** |

PaddleOCR huấn luyện và đánh giá nhánh rec bằng cách đưa **nguyên ảnh**; đường ống triển khai thì
chạy det trước, cắt ảnh thành **nhiều mảnh** rồi mới đưa từng mảnh cho rec. Model fine-tune chưa
từng thấy mảnh vụn nào. Mẫu lỗi khớp chính xác: `51U74598 → 598`, `59X132817 → 32817`.

Con số val 0,8809 mà PaddleOCR báo trong lúc huấn luyện **không sai** — nó đo rec-only, và rec-only
thật sự đạt 0,8567 trên tập val. Nó chỉ đo một chế độ mà hệ thống không dùng.

---

## 2. Đo trên ngữ liệu 2.801 mẫu — bỏ det có vẻ thắng lớn

| Cấu hình | A5 | A6 | ms/ảnh |
|---|---:|---:|---:|
| Gốc, det + rec | 0,6373 | 0,7512 | 328,8 |
| Gốc, chỉ rec | 0,6776 | 0,7508 | 35,7 |
| Fine-tune, det + rec | 0,5998 | 0,6762 | — |
| **Fine-tune, chỉ rec** | **0,8618** | **0,8758** | 38,5 |

Đọc theo bảng này thì kết luận quá rõ: bỏ det, model gốc **không mất gì** (0,7512 so với 0,7508),
model fine-tune **lãi 12,46 điểm**, và nhanh hơn ~290 ms mỗi ảnh. NFR-A6 lật từ trượt sang đạt.

**Kết luận đó sai.**

---

## 3. Vì sao bảng trên không đủ thẩm quyền kết luận

**Mọi ảnh trong ngữ liệu 2.801 mẫu đều là ảnh đã cắt sẵn do Roboflow xuất ra.** Crop khít quanh
biển số thì bộ dò chữ không còn gì để khoanh — nên cột "chỉ rec" đọc ra như thể det là thừa.

Nhưng crop mà hệ thống thật sự phải đọc là **do YOLO sinh ra từ ảnh toàn cảnh**, và chúng lỏng hơn
nhiều: dính cản xe, kính chắn gió, nền đường.

Đo lại trên bộ demo — thứ duy nhất trong đồ án chạy ảnh toàn cảnh qua detector thật (22 biển):

| Cấu hình | Số biển đọc đúng |
|---|---:|
| **Gốc, det + rec** | **17 / 22** |
| Gốc, chỉ rec | 13 / 22 |
| Fine-tune, det + rec | 14 / 22 |
| Fine-tune, chỉ rec | 15 / 22 |

**Thứ tự đảo ngược.** Trên crop lỏng, bước det làm đúng việc của nó: khoanh lại vùng chữ bên trong
crop. Bỏ nó đi thì rec đọc luôn cả phần nền xung quanh thành ký tự — `TCA7A22104`, `5KB274184` trên
`nhieu-bien-2.png`.

---

## 4. Thứ đứng vững ở cả hai bảng

Rec-only **giúp** model fine-tune (+12,46 điểm trên ngữ liệu, +1 biển trên demo) và **hại** model
gốc (−4 biển trên demo). Hiệu ứng này thật và có cơ chế rõ ràng: model huấn luyện trên ảnh nguyên
biển chưa bao giờ nhìn thấy mảnh vụn.

Nhưng 22 biển là mẫu quá nhỏ để đổi thứ đem giao — một biển đã là 4,5 điểm.

---

## 5. Quyết định

| | |
|---|---|
| Mặc định | `ocr_skip_detection = False` — **giữ nguyên hành vi đang giao** |
| Công tắc | `ALPR_OCR_SKIP_DETECTION=1` để bật khi đối chứng |
| Ghim bằng test | `tests/test_config.py::test_text_detection_stays_in_the_pipeline_by_default` |
| Điều kiện để bật thật | Cần một tập **ảnh toàn cảnh có nhãn chuỗi biển số** — đồ án hiện **không có** |

Đây cũng chính là điều kiện đã được ghi trong ghi chú tính đại diện của NFR-A7: không bộ dữ liệu nào
của đồ án có đồng thời ảnh toàn cảnh và chuỗi biển số. Cùng một lỗ hổng dữ liệu chặn cả hai câu hỏi.

---

## 6. Bài học phương pháp — lần thứ tư cùng một họ lỗi

| Lần | Con số đẹp | Thứ nó không nhìn thấy |
|---|---|---|
| Siêu phân giải | "0 biển cải thiện" | Cổng chỉ mở cho crop < 200 px, 0/120 mẫu lọt |
| Harness đo | A4–A7 ổn định | Chưa từng gọi bậc thang thử-lại |
| Fine-tune | val acc 0,8809 | Val đo rec-only, hệ thống chạy det+rec |
| **Lần này** | **A6 0,8758** | **Ngữ liệu toàn ảnh cắt sẵn, không phải crop từ detector** |

Ba lần đầu là lỗi đã mắc rồi mới phát hiện. Lần thứ tư suýt nữa thì đem giao — chỉ tránh được vì
bộ demo được chạy lại trước khi đổi mặc định. **Quy tắc rút ra: không đổi cấu hình mặc định dựa trên
một phép đo mà đầu vào của nó khác đầu vào thật.**
