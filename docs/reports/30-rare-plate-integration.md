# Thẩm định và tích hợp dữ liệu biển hiếm (vàng / xanh)

**Ngày:** 2026-08-02
**Nguồn:** `nguyenluanai/license-plate-color` v4 — **CC BY 4.0**, bắt buộc ghi công
**Trạng thái:** đã thẩm định xong, đã xuất manifest, **chưa đưa vào huấn luyện**

---

## 1. Phát hiện đầu tiên: bộ dữ liệu đã nằm sẵn trên máy

Khảo sát [17-plate-type-dataset-survey.md](17-plate-type-dataset-survey.md) (20/07) đề xuất tải bộ này
và ghi rõ *"chưa tải file nào về máy"*. Thực tế `datasets/raw/roboflow_plate_color/` **đã có đủ
2.107 ảnh** từ 13/01/2026 — tải về rồi không dùng, và không có mục nào trong tài liệu ghi lại việc đó.

Đây không phải chi tiết vụn vặt: nếu không kiểm tra trước khi tải, dự án đã tải chồng lên
dữ liệu sẵn có và có thể ghi đè mất nó.

---

## 2. Bộ dữ liệu có đúng như khảo sát mô tả không

| Hạng mục | Khảo sát 20/07 dự đoán | Đo thực tế 02/08 | |
|---|---|---|---|
| Phiên bản | phải là v4 | v4, xuất 13/01/2026 | ✅ |
| Tổng ảnh | 2.107 | 2.107 | ✅ |
| Chia tập | 1.505 / 423 / 179 | 1.505 / 423 / 179 | ✅ |
| Giấy phép | CC BY 4.0 | CC BY 4.0 (trong `data.yaml` và `README.dataset.txt`) | ✅ |
| Biển vàng | 694 | 694 | ✅ |
| Biển xanh | 63 | 63 | ✅ |
| `bien_unknown` bỏ đi | 542 (25,7%) | 542 (25,7%) | ✅ |
| Tăng cường dữ liệu | — | **không có** (`No image augmentation techniques were applied`) | ✅ |

Việc không có bản tăng cường là điểm quan trọng: bộ #1 và #3 trong khảo sát đều bị rò rỉ
train/test do bản augment bị chia lẫn giữa các tập. Bộ này không có rủi ro đó.

---

## 3. Nhãn ký tự lấy từ tên tệp

Tên tệp có dạng `crop_<camera>_<BIỂNSỐ>_<ngày>_<giờ>_640_jpg.rf.<hash>.jpg`.

| Bước lọc | Còn lại |
|---|---:|
| Tổng ảnh | 2.107 |
| Parse được chuỗi từ tên tệp | 1.677 |
| Mã tỉnh nằm trong 81 mã hợp lệ | 1.665 |
| **Qua validator của chính đồ án** | **1.661** |

Loại bỏ: 12 ảnh sai mã tỉnh, 4 ảnh sai định dạng. Nhãn **không** được tin ngay — nó phải đi qua
`VietnamesePlateNormalizer` giống hệt mọi nhãn khác của dự án.

### Phần dùng được, tách theo màu

| Lớp | Có nhãn ký tự |
|---|---:|
| `bien_trang` | 555 |
| `bien_unknown` | 535 |
| **`bien_vang`** | **509** |
| **`bien_xanh`** | **62** |

Chỉ hai lớp cuối được lấy — dự án đang **thừa** biển trắng, còn `bien_unknown` là ảnh đêm ám tím
mà chính người gán nhãn cũng không xác định được màu.

---

## 4. Nhãn màu của bộ có đáng tin không

Không tin nhãn của người khác. Chạy bộ phân loại màu của chính đồ án
(`ai/inference/plate_color.py`) lên **toàn bộ** 571 ảnh hiếm:

| Lớp theo nhãn của bộ | n | Bộ phân loại của đồ án đồng ý | Tỷ lệ khớp |
|---|---:|---|---:|
| `bien_vang` | 509 | 501 vàng, 6 trắng, 2 đỏ | **98,43%** |
| `bien_xanh` | 62 | 60 xanh, 2 trắng | **96,77%** |

Hai nguồn độc lập đồng ý ở mức này thì nhãn màu dùng được. Số ảnh lệch (6 + 2 trắng) nhiều khả
năng là ảnh gần như xám — đúng hiện tượng khảo sát đã cảnh báo ở mục 2.1.

---

## 5. Trùng lặp và rò rỉ

| Kiểm tra | Kết quả |
|---|---|
| Biển số duy nhất trong bộ | 1.570 |
| Biển xuất hiện nhiều hơn 1 lần | 74 biển / 165 ảnh — **phải khử trước khi chia tập** |
| Giao với ngữ liệu 2.801 hiện có | **1 biển** (`29H03102`) |

Một biển trùng trên 1.570 là mức không đáng kể, nhưng vẫn phải loại để tập kiểm thử sạch tuyệt đối.

---

## 6. Mức cải thiện

| Loại biển | Trước | Sau | Bội số |
|---|---:|---:|---:|
| Vàng (có nhãn ký tự) | 20 | **529** | **26×** |
| Xanh (có nhãn ký tự) | 4 | **66** | **16×** |
| Tổng ngữ liệu | 2.801 | 3.372 | |
| **Tỷ lệ biển hiếm** | **0,86%** | **17,6%** | **20×** |

Biển vàng chuyển từ *"n=20, mọi con số đều vô nghĩa thống kê"* sang **đánh giá được**.
Biển xanh (n=66) vẫn phải báo cáo kèm khoảng tin cậy và xếp vào mục kết quả sơ bộ.

---

## 7. Ba điều kiện phải nói kèm mọi số liệu sinh từ bộ này

1. **Một miền dữ liệu duy nhất.** Toàn bộ là ảnh crop từ camera cổng bãi xe
   (`crop_caunamprc554`, `crop_caunamprc555`…), **biển 1 dòng, ô tô**. Không có xe máy, không có
   ảnh hiện trường. Kết quả trên bộ này **không** suy rộng ra biển vàng nói chung.
2. **Ảnh bị resize *stretch* về 640×640** ⇒ tỷ lệ khung hình bị phá, giống hệt hai bộ Roboflow
   sẵn có. Đường ống đã có `restore_aspect_ratio` xử lý, nhưng phải ghi rõ trong luận văn.
3. **Bắt buộc ghi công CC BY 4.0** cho workspace `nguyenluanAI` trong báo cáo dataset và luận văn.

---

## 8. Đã gộp — 02/08/2026

Chạy bằng [`scripts/dataset/merge_rare_plates.py`](../../scripts/dataset/merge_rare_plates.py),
đầu ra `datasets/annotations/plate_labels_merged.csv`.

| Bước | Kết quả |
|---|---|
| Khử trùng lặp trong bộ mới | bỏ **50**, còn 521 |
| Khử giao với ngữ liệu cũ | **0** — xem ghi chú dưới |
| Chia lại theo **biển số** | 413 train / 108 valid (seed 42, tỷ lệ khớp ngữ liệu gốc) |
| **Ngữ liệu sau khi gộp** | **3.322 dòng** — 2.637 train / 679 valid |
| **Tỷ lệ biển hiếm** | **0,86% → 15,7%** (476 vàng + 45 xanh) |

> **Vì sao 0 biển giao mà khảo sát mục 5 lại ghi 1?** Khảo sát quét **toàn bộ**
> 1.570 biển của bộ màu và tìm thấy `29H03102` trùng ngữ liệu cũ. Nhưng tệp
> xuất ra chỉ gồm biển **vàng và xanh**, còn `29H03102` là biển **trắng** — nó
> chưa bao giờ lọt vào. Hai con số cùng đúng, khác phạm vi.

### 8.1. Hai chỗ phải sửa trong bộ sinh dữ liệu trước khi fine-tune lại

Gộp dữ liệu **một mình là không đủ**. Lượt fine-tune 02/08 thất bại vì chênh lệch
giữa lúc huấn luyện và lúc chạy, không phải vì thiếu dữ liệu — lặp lại y nguyên
quy trình cũ với dữ liệu nhiều hơn sẽ cho ra đúng thất bại cũ.

**(a) Thiếu bước nắn tỉ lệ.** `build_rec_finetune_set.py` đọc ảnh thẳng từ đĩa,
trong khi đường ống thật gọi `restore_aspect_ratio` trước khi đọc. Hai bộ Roboflow
đều xuất crop lên khung **vuông**, nên model được dạy một hình dạng mà production
không bao giờ đưa cho nó. Đã sửa.

**(b) Model chưa từng thấy mảnh vụn.** Đây là nguyên nhân gốc của lượt trước:
PaddleOCR đánh giá bằng **nguyên ảnh**, còn hệ thống chạy **det trước rồi rec**,
tức đưa cho model từng mảnh. Nay bộ sinh phát thêm **hai nửa của biển 2 dòng làm
mẫu riêng**, mỗi nửa mang nhãn của chính nó.

Chỉ phát khi điểm cắt **không nhập nhằng** — biển 9 ký tự (4+5) và 7 ký tự (3+4).
Biển 8 ký tự bị bỏ qua vì `67C10815` có thể là `67C`+`10815` hoặc `67C1`+`0815`,
cả hai đều hợp lệ; đoán ở đây là đúng cách mà lượt fine-tune **đầu tiên** đã hỏng
(nhãn sai sinh ra âm thầm).

### 8.2. Tập huấn luyện mới

| | train | val |
|---|---:|---:|
| Nguyên ảnh biển (`base`) | 2.637 | 679 |
| Tăng cường (`tiny`, `deg`) | 5.274 | — |
| **Nửa trên / nửa dưới** (`up`, `low`) | **2.364** | **632** |
| **Tổng** | **10.275** | **1.311** |

**Điểm quan trọng nhất nằm ở cột val.** Lần trước tập kiểm định chỉ có nguyên ảnh,
nên val acc 0,8809 đo một chế độ hệ thống **không dùng** — và vì thế không nhìn
thấy được cái hỏng. Nay val có **632 mẫu mảnh vụn**, tức phép đo lúc huấn luyện đã
chạm được vào chính chế độ mà production chạy.

### 8.3. Còn lại

- [ ] Fine-tune lại (người thực hiện chạy)
- [ ] Đo lại A4–A7 bằng `ai/evaluation/ocr_accuracy.py` và **đối chiếu với bộ demo
      ảnh toàn cảnh** trước khi kết luận — bài học của mục 5 trong
      [31-detection-stage-ablation.md](31-detection-stage-ablation.md)
- [ ] Cập nhật mục 6.3.8 của [ch6-ket-luan.md](../papers/ch6-ket-luan.md): câu
      *"97,68% mẫu thuộc một lớp duy nhất"* chỉ còn đúng cho ngữ liệu **trước** khi gộp
- [ ] Biển đỏ và ngoại giao **vẫn bằng 0** — không nguồn công khai nào lấp được,
      giữ nguyên trong mục Hạn chế
