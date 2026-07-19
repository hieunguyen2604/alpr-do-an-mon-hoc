# Báo cáo 03 — Hạ tầng huấn luyện Phase 3 (bộ phát hiện biển số YOLO11)

> **TÌNH TRẠNG: MÔ HÌNH CHÍNH THỨC `best.pt` ĐÃ HUẤN LUYỆN XONG.**
> Lượt chính thức (YOLO11n, `imgsz=640`, split v3, 20 epoch) đã hoàn tất và cho ra
> `models/best.pt`. Kết quả detection thật trên tập test v3 (1.514 ảnh): **mAP@0.5 = 0,9829 ·
> mAP@0.5:0.95 = 0,7834 · Precision = 0,9837 · Recall = 0,9714** — đều đạt chỉ tiêu NFR-A1/A2/A3.
> Các bảng ở mục 10 **đã điền số đo thật** cho cấu hình chính (E-A). Các thí nghiệm bổ sung
> (E-B ablation, E-C leo thang, E-D độ phân giải) chưa chạy nên vẫn để trống. Xem mục 9 và 10.

**Ngày lập:** 19/07/2026
**Phạm vi:** hạ tầng huấn luyện, đánh giá và xuất mô hình cho khối **detection** (YOLO11).
Khối OCR và hậu xử lý thuộc phase khác, không nằm trong báo cáo này.

---

## Mục lục

1. [Mục tiêu Phase 3 và chỉ tiêu cần đạt](#1-mục-tiêu-phase-3-và-chỉ-tiêu-cần-đạt)
2. [Lựa chọn mô hình và căn cứ](#2-lựa-chọn-mô-hình-và-căn-cứ)
3. [Chiến lược huấn luyện — vì sao Colab GPU chứ không phải máy cục bộ](#3-chiến-lược-huấn-luyện--vì-sao-colab-gpu-chứ-không-phải-máy-cục-bộ)
4. [Cấu hình siêu tham số](#4-cấu-hình-siêu-tham-số)
5. [Kế hoạch thí nghiệm](#5-kế-hoạch-thí-nghiệm)
6. [Quy trình đánh giá](#6-quy-trình-đánh-giá)
7. [Kế hoạch đo tốc độ CPU](#7-kế-hoạch-đo-tốc-độ-cpu)
8. [Hướng dẫn chạy](#8-hướng-dẫn-chạy)
9. [Tình trạng hiện tại](#9-tình-trạng-hiện-tại)
10. [Bảng chờ điền kết quả](#10-bảng-chờ-điền-kết-quả)
11. [Rủi ro và cách đối phó](#11-rủi-ro-và-cách-đối-phó)

---

## 1. Mục tiêu Phase 3 và chỉ tiêu cần đạt

### 1.1. Mục tiêu

Phase 3 sản xuất **một tệp trọng số duy nhất** — `models/best.pt` — là bộ phát hiện biển số
mà toàn bộ hệ thống phía sau tiêu thụ, kèm theo bằng chứng định lượng rằng tệp đó đạt các
chỉ tiêu phi chức năng đã cam kết. Cụ thể gồm bốn sản phẩm bàn giao:

| # | Sản phẩm | Vị trí |
|---|---|---|
| S1 | Trọng số đã huấn luyện | `models/best.pt` |
| S2 | Báo cáo đánh giá JSON + biểu đồ PNG | `docs/reports/03-evaluation-*.json`, `docs/reports/figures/` |
| S3 | Mô hình đã xuất cho suy luận CPU | `models/best.onnx`, `models/best_openvino_model/`, `models/best.torchscript` |
| S4 | Số đo tốc độ CPU trên **chính máy này** | `docs/reports/03-benchmark-cpu-*.json` |

### 1.2. Chỉ tiêu cần đạt

Nguồn: [`docs/00-requirements/non-functional-requirements.md`](../00-requirements/non-functional-requirements.md),
mục 2 (NFR-A). Đo trên **tập test độc lập**, không phải tập validation.

| Mã | Chỉ số | Mục tiêu | Ngưỡng tối thiểu chấp nhận | Ghi chú đo |
|---|---|---|---|---|
| **NFR-A1** | mAP@0.5 của bộ phát hiện | **≥ 0,90** | ≥ 0,85 | Trên tập test độc lập |
| **NFR-A2** | mAP@0.5:0.95 của bộ phát hiện | **≥ 0,65** | ≥ 0,55 | Chỉ tiêu chặt hơn, phản ánh chất lượng khớp box |
| **NFR-A3** | Precision / Recall | **≥ 0,92 / ≥ 0,90** | ≥ 0,88 / ≥ 0,85 | Tại ngưỡng confidence tối ưu theo F1 |
| **NFR-A8** | Độ chính xác **tách riêng biển 1 dòng / 2 dòng** | Không đặt ngưỡng riêng, nhưng **bắt buộc báo cáo** | — | Biển 2 dòng dự kiến khó hơn rõ rệt |
| **NFR-A9** | Độ chính xác theo điều kiện ảnh | Báo cáo nếu dữ liệu có nhãn phù hợp | — | Ngày / đêm / nghiêng / mờ |

**Vì sao NFR-A2 khó hơn NFR-A1 nhiều hơn vẻ ngoài của nó.** mAP@0.5 chỉ hỏi "có tìm ra biển
không"; mAP@0.5:0.95 lấy trung bình trên 10 ngưỡng IoU từ 0,50 đến 0,95, tức là hỏi "hộp có
**bám sát** biển không". Với dự án này, câu hỏi thứ hai mới là câu hỏi thật: đầu ra của detector
không đến tay người mà đến tay **một mô hình khác** (OCR). Hộp lệch vài pixel làm mất một cạnh ký
tự và OCR đọc sai cả biển. Đó chính là lý do trọng số `box` được nâng lên 8,0 (mục 4.4).

**Vì sao NFR-A3 nhấn mạnh "tại ngưỡng confidence tối ưu theo F1".** Precision và recall là hai
đại lượng đánh đổi lẫn nhau theo ngưỡng confidence; báo cáo một cặp P/R mà không nói ngưỡng nào
là báo cáo một con số vô nghĩa vì có thể chọn ngưỡng để làm đẹp bất kỳ vế nào. `evaluate.py` dò
ngưỡng theo F1 và ghi lại ngưỡng đó trong báo cáo JSON.

---

## 2. Lựa chọn mô hình và căn cứ

Quyết định đã chốt ở Phase 1. Báo cáo này **không lập luận lại**, chỉ ghi nhận kết luận và trỏ
tới nguồn: [`docs/reports/01-yolo-comparison.md`](01-yolo-comparison.md), mục 9.

| Vai trò | Mô hình | Cấu hình | Căn cứ |
|---|---|---|---|
| **Chính (shipping)** | **YOLO11n** | `yolo11n_finetune.yaml` | 01-yolo-comparison.md mục 9.2 |
| Mốc so sánh (ablation) | YOLO11n từ đầu | `yolo11n_baseline.yaml` | Đo giá trị của transfer learning |
| **Leo thang** | YOLO11s | `yolo11s_escalation.yaml` | 01-yolo-comparison.md mục 9.2 — chỉ dùng khi nano không đạt |

Tóm tắt căn cứ chọn YOLO11n, ở mức đủ để đọc báo cáo này mà không phải mở tệp kia:

1. Là phiên bản **duy nhất** trong nhóm v9–v13 có **số liệu tốc độ CPU chính thức** — điều kiện
   bắt buộc với một hệ thống triển khai trên máy không có GPU.
2. Có cơ chế kiến trúc khớp trực tiếp với bài toán: **C2PSA** cải thiện phát hiện vật thể nhỏ,
   **anchor-free head** xử lý tốt tỷ lệ khung hình dẹt của biển số.
3. Có **bằng chứng thực nghiệm dày nhất trên đúng bài toán ALPR** — ba nghiên cứu độc lập.

Ngoài ra Phase 1 khuyến nghị huấn luyện **YOLO26n song song làm đối chứng** (01-yolo-comparison.md
mục 9.3). Hạ tầng hiện tại **chưa hỗ trợ sẵn** biến thể này: `TrainingConfig.SUPPORTED_MODEL_VARIANTS`
mới liệt kê `yolo11n/s/m/l/x`. Đây là một khoảng trống đã biết, ghi ở mục 9.3.

---

## 3. Chiến lược huấn luyện — vì sao Colab GPU chứ không phải máy cục bộ

### 3.1. Sự thật phần cứng

Máy phát triển của đồ án:

| Thành phần | Giá trị thực tế |
|---|---|
| CPU | Intel Core i5-14600K (14 nhân vật lý / 20 luồng) |
| GPU | **Intel UHD Graphics 770** (đồ họa tích hợp) |
| **GPU CUDA** | **KHÔNG CÓ** |
| Hệ điều hành | Windows 11 |
| Python | 3.13 |

Nguồn: [`docs/00-requirements/environment.md`](../00-requirements/environment.md) mục 3.1.
`CLAUDE.md` ban đầu mô tả môi trường là macOS Apple Silicon M3 Pro với Python 3.12; khảo sát
thực tế cho thấy **cả hai đều sai** và sai lệch đó được ghi nhận chính thức trong tài liệu môi
trường vì nó ảnh hưởng trực tiếp đến quyết định trong mục này.

### 3.2. Hệ quả: máy cục bộ không thể huấn luyện

Huấn luyện một bộ phát hiện là bài toán bị chi phối bởi **backward pass** trên hàng chục nghìn
ảnh, lặp lại hàng trăm lần. Không có CUDA thì:

* PyTorch chạy toàn bộ forward + backward trên CPU, không có kernel nào được tăng tốc.
* **AMP (mixed precision) vô hiệu** — đây là một tính năng của GPU. `train.py` chủ động tắt
  `amp` khi thiết bị là `cpu` để tránh cảnh báo gây nhiễu và một lần tải kiểm tra AMP vô ích.
* Intel UHD 770 **không phải** phương án thay thế: nó không chạy được CUDA, và đường ống
  huấn luyện của Ultralytics không có backend cho nó. OpenVINO — thứ *có* dùng được phần cứng
  Intel — là công cụ **suy luận**, không phải công cụ huấn luyện.

Ước lượng quy mô vấn đề: tập dữ liệu VNLP có ~37.300 ảnh. Một epoch tức là ~37.300 lượt
forward + backward ở độ phân giải 640. Trên CPU, **một** epoch có thể mất nhiều giờ; lịch huấn
luyện là **100 epoch** (fine-tune) hoặc **150 epoch** (từ đầu). Con số đó không nằm trong phạm
vi khả thi của một đồ án.

> Đây là ước lượng bậc độ lớn dùng để ra quyết định, **không phải số đo**. Không có phép đo
> thời gian một epoch trên CPU nào được thực hiện, và cũng không cần thực hiện: kết luận
> không thay đổi dù sai số gấp vài lần.

### 3.3. Kết luận chiến lược: phân vai rõ ràng giữa hai máy

| Việc | Chạy ở đâu | Lý do |
|---|---|---|
| **Huấn luyện** | **Google Colab (GPU T4)** | Là nơi duy nhất có GPU CUDA |
| Đánh giá độ chính xác | Colab hoặc cục bộ | mAP/P/R **không phụ thuộc thiết bị** |
| **Đo độ trễ** | **Bắt buộc máy cục bộ, `--device cpu`** | Số liệu phải mô tả đúng máy triển khai |
| Xuất ONNX / OpenVINO | Nơi nào cũng được | Export chạy trên CPU (`device="cpu"` cố định trong `export.py`) |

Quyết định này khớp với **AD-06** trong [`docs/architecture/system-architecture.md`](../architecture/system-architecture.md):
thiết bị suy luận cấu hình được, **mặc định `cpu`**.

Chú ý điểm tinh tế ở dòng "Đánh giá độ chính xác": ô 8 của notebook Colab cố ý truyền
`--device cpu` **ngay cả khi đang chạy trên Colab có GPU**. Lý do nằm trong comment của chính ô
đó: độ chính xác giống nhau trên hai thiết bị, nhưng **phần trăm vị độ trễ** trong báo cáo phải
mô tả máy triển khai chứ không phải một chiếc T4 mượn tạm.

### 3.4. Nguyên tắc bất di bất dịch: notebook không chứa logic

`notebooks/train_colab.ipynb` **chỉ là trình thực thi**. Mọi logic huấn luyện nằm trong
`ai/training/*.py` và `ai/evaluation/*.py`. Notebook chỉ gọi script bằng `!python -m ...`.

Ba lợi ích, và đây là lý do đáng bảo vệ trước hội đồng chứ không phải sở thích cá nhân:

1. **Kết quả trên Colab và cục bộ là như nhau** — cùng một mã, cùng một `TrainingConfig`.
2. **Mọi thay đổi tham số nằm trong Git**, không trôi mất theo một phiên trình duyệt bị thu hồi.
3. **Tái lập được**: một con số trong luận văn truy ngược được về đúng tệp YAML sinh ra nó,
   nhờ `train.py` chụp lại `training_config.yaml` ngay cạnh trọng số.

---

## 4. Cấu hình siêu tham số

Nguồn chân lý duy nhất: lớp `TrainingConfig` trong [`ai/training/config.py`](../../ai/training/config.py).
Ba tệp YAML trong `ai/training/configs/` là ba **thực thể** của lớp đó. Mọi giá trị đều được
kiểm tra hợp lệ **trước khi nạp một ảnh nào** — thất bại sớm rẻ hơn nhiều so với phát hiện một
siêu tham số sai sau ba giờ chạy trên Colab.

### 4.0. Bảng đầy đủ ba cấu hình

| Nhóm | Tham số | `yolo11n_baseline` | `yolo11n_finetune` ★ | `yolo11s_escalation` |
|---|---|---|---|---|
| **Mô hình** | `model_variant` | yolo11n | yolo11n | yolo11s |
| | `pretrained_weights` | `""` (ngẫu nhiên) | `yolo11n.pt` | `yolo11s.pt` |
| **Dữ liệu** | `data` | `datasets/processed/data.yaml` | *nt* | *nt* |
| **Lịch** | `imgsz` | 640 | 640 | 640 |
| | `epochs` | 150 | 100 | 100 |
| | `batch` | 16 | 16 | 8 |
| | `patience` | 30 | 20 | 20 |
| **Tối ưu** | `optimizer` | AdamW | AdamW | AdamW |
| | `lr0` | 0,002 | 0,001 | 0,0008 |
| | `lrf` | 0,01 | 0,01 | 0,01 |
| | `momentum` | 0,937 | 0,937 | 0,937 |
| | `weight_decay` | 0,0005 | 0,0005 | 0,001 |
| | `warmup_epochs` | 5,0 | 3,0 | 3,0 |
| | `warmup_momentum` | 0,8 | 0,8 | 0,8 |
| | `warmup_bias_lr` | 0,1 | 0,1 | 0,1 |
| | `cos_lr` | false | **true** | **true** |
| **Mất mát** | `box` | **8,0** | **8,0** | **8,0** |
| | `cls` | 0,5 | 0,5 | 0,5 |
| | `dfl` | 1,5 | 1,5 | 1,5 |
| **Augmentation** | `hsv_h` | 0,015 | 0,015 | 0,015 |
| | `hsv_s` | 0,7 | 0,7 | 0,7 |
| | `hsv_v` | 0,4 | 0,4 | 0,4 |
| | `degrees` | 5,0 | 5,0 | 5,0 |
| | `translate` | 0,1 | 0,1 | 0,1 |
| | `scale` | 0,5 | 0,5 | 0,5 |
| | `shear` | 2,0 | 2,0 | 2,0 |
| | `perspective` | 0,0005 | 0,0005 | 0,0005 |
| | **`fliplr`** | **0,0 — bắt buộc** | **0,0 — bắt buộc** | **0,0 — bắt buộc** |
| | **`flipud`** | **0,0 — bắt buộc** | **0,0 — bắt buộc** | **0,0 — bắt buộc** |
| | `copy_paste` | 0,0 | 0,0 | 0,0 |
| | `erasing` | 0,4 | 0,4 | 0,4 |
| | `mosaic` | 1,0 | 1,0 | 1,0 |
| | `close_mosaic` | 15 | 10 | 10 |
| | `mixup` | 0,0 | 0,0 | 0,0 |
| **Vận hành** | `device` | auto | auto | auto |
| | `workers` | 8 | 8 | 4 |
| | `seed` | **42** | **42** | **42** |
| | `deterministic` | true | true | true |
| | `save_period` | **10** | **10** | **10** |
| | `val` / `plots` | true / true | true / true | true / true |
| | `cache` | false | false | false |
| | `amp` | true (bỏ qua trên CPU) | *nt* | *nt* |
| | `fraction` | 1,0 | 1,0 | 1,0 |

★ = cấu hình chính, sinh ra mô hình đem dùng.

### 4.1. Nhóm mô hình — dòng khác biệt duy nhất giữa baseline và finetune

`pretrained_weights` là **dòng duy nhất** phân biệt `yolo11n_baseline.yaml` với
`yolo11n_finetune.yaml`. Chuỗi rỗng → dựng kiến trúc từ `yolo11n.yaml` với trọng số ngẫu nhiên;
`yolo11n.pt` → tinh chỉnh từ trọng số đã pretrain trên COCO.

COCO **không có** lớp "biển số". Nhưng đặc trưng tầng thấp — cạnh, góc, hình chữ nhật tương phản
cao — chuyển giao rất tốt, và đó đúng là thứ một bộ phát hiện biển số cần.

Vì hai cấu hình chỉ khác nhau một dòng và chạy trên **cùng một phân chia dữ liệu**, khoảng cách
mAP giữa chúng **chính là** giá trị đo được của transfer learning. Đây là một ablation sạch,
không phải một phép so sánh mơ hồ.

### 4.2. Nhóm lịch huấn luyện

| Tham số | Ý nghĩa và lý do chọn |
|---|---|
| `imgsz = 640` | Biển số là **vật thể nhỏ**. Giảm giá trị này là thứ **đầu tiên** làm tụt recall. Giữ **cố định 640 ở cả ba cấu hình** để mọi so sánh đều công bằng. `TrainingConfig` bắt buộc bội số của 32. |
| `epochs` | 150 khi huấn luyện từ đầu, 100 khi tinh chỉnh. Trọng số ngẫu nhiên cần lịch dài hơn để hội tụ; trọng số pretrain hội tụ nhanh hơn nhiều. |
| `batch` | 16 vừa với T4 ở 640 px cho nano. YOLO11s giảm còn 8 vì activation lớn hơn đáng kể và T4 có thể OOM ở batch 16. Đặt `-1` để Ultralytics AutoBatch tự chọn theo VRAM — hữu ích vì Colab cấp GPU khác nhau mỗi phiên. |
| `patience` | Dừng sớm sau bằng ấy epoch không cải thiện fitness. Baseline rộng tay hơn (30) vì huấn luyện từ đầu hay đi ngang rồi cải thiện trở lại; fine-tune chặt hơn (20) vì đã 20 epoch không tiến bộ thì chỉ còn quá khớp. |

### 4.3. Nhóm bộ tối ưu

| Tham số | Ý nghĩa và lý do chọn |
|---|---|
| `optimizer = AdamW` | Dễ tính hơn SGD trên dataset cỡ vừa (~37k ảnh) và ít phải dò learning rate — phù hợp với ngân sách GPU hữu hạn của một đồ án. |
| `lr0` | **Cố tình thấp khi tinh chỉnh (0,001).** LR cao trên trọng số pretrain gây **catastrophic forgetting**: đặc trưng COCO hữu ích bị phá trong vài trăm bước đầu và kết quả còn **tệ hơn** huấn luyện từ đầu. Baseline dùng 0,002 vì không có cấu trúc nào cần bảo tồn. YOLO11s dùng 0,0008, giảm theo batch (batch nhỏ → gradient nhiễu hơn → bước nhỏ hơn giữ cập nhật hiệu dụng tương đương). |
| `lrf = 0,01` | LR cuối = `lr0 × lrf`. Fine-tune kết thúc ở 1e-5. |
| `warmup_epochs` | 5 cho baseline, 3 cho fine-tune. Trọng số ngẫu nhiên sinh gradient lớn và nhiễu ở những bước đầu nên cần khởi động dài hơn. |
| `cos_lr` | `true` khi tinh chỉnh: suy giảm cosine có đuôi mượt hơn lịch tuyến tính và giúp vài điểm mAP cuối. `false` ở baseline để giữ baseline gần cấu hình tham chiếu nhất. |
| `weight_decay` | 0,0005 chuẩn; YOLO11s nâng lên 0,001 vì **nhiều tham số hơn trên cùng lượng dữ liệu** nghĩa là nhiều chỗ để quá khớp hơn. |

### 4.4. Nhóm trọng số hàm mất mát

| Tham số | Giá trị | Lý do |
|---|---|---|
| `box` | **8,0** (mặc định Ultralytics: 7,5) | Nâng lên vì lý do **đặc thù dự án**: đầu ra của detector được **một mô hình khác** tiêu thụ chứ không phải con người. Hộp lệch → ảnh cắt xấu → OCR đọc sai. Chất lượng định vị ở đây quan trọng hơn trong một bài toán phát hiện thông thường, và nó cũng chính là thứ NFR-A2 đo. |
| `cls` | 0,5 | Thấp — detector có rất ít lớp, phân loại là phần dễ của bài toán này. |
| `dfl` | 1,5 | Giữ mặc định. Không có căn cứ để chỉnh. |

### 4.5. Nhóm augmentation — `fliplr = 0.0` và vì sao nó là điểm kỹ thuật đáng nêu

> ### ⚠️ `fliplr = 0.0` — chặn cứng ở tầng cấu hình
>
> Lật ngang ảnh làm **soi gương các ký tự in trên biển số**.
>
> Đây không phải một phép biến đổi bảo toàn nhãn. Một biển số bị lật ngang **không phải** một
> góc nhìn khác của cùng vật thể — nó là **một vật thể không tồn tại**. Chữ `A` soi gương không
> phải chữ `A`; chuỗi `59H1-234.56` soi gương không phải một biển số Việt Nam hợp lệ, cũng
> không phải biển số của bất kỳ quốc gia nào.

Vì sao chi tiết này đáng nêu trong luận văn, chứ không chỉ là một dòng cấu hình:

1. **`fliplr = 0.5` là mặc định của Ultralytics.** Ai không nghĩ tới sẽ vô tình bật nó, và
   **một nửa số ảnh huấn luyện** sẽ là biển gương. Đây là lỗi mặc định-im-lặng, đúng loại lỗi
   dễ mắc nhất.
2. **Sai lầm này không làm hỏng quá trình huấn luyện.** Loss vẫn giảm, mAP vẫn tăng, đường cong
   vẫn đẹp. Nó chỉ làm mô hình **kém hơn mức đáng lẽ đạt được** — một sai lầm tốn kém và gần
   như không thể phát hiện nếu chỉ nhìn biểu đồ.
3. **Thiệt hại lan sang khối OCR.** Nếu chính sách augmentation này được tái sử dụng cho việc
   huấn luyện OCR ở phase sau, mô hình OCR sẽ được dạy đọc các ký tự gương. Đó là phá hoại
   trực tiếp tín hiệu mà cả hệ thống dựa vào.
4. **Vì vậy quy tắc được chặn ở tầng mã, không phải tầng quy ước.** `TrainingConfig.__post_init__`
   **ném `ValueError`** với thông điệp giải thích lý do nếu ai đó đặt `fliplr` khác 0:

   ```
   fliplr must be 0.0: horizontal flipping mirrors the characters printed on
   the plate and corrupts the training signal (got 0.5)
   ```

   Một quy ước ghi trong comment sẽ bị vi phạm sớm muộn; một `ValueError` thì không.

`flipud` cũng bị chặn cứng ở 0,0, nhưng vì lý do nhẹ hơn: biển lộn ngược đơn giản là không xuất
hiện trong bài toán triển khai.

Các tham số augmentation còn lại, và lý do từng giá trị:

| Tham số | Giá trị | Lý do |
|---|---|---|
| `hsv_h` | 0,015 (rất nhỏ) | **Màu nền biển ở Việt Nam mang ngữ nghĩa**: trắng / vàng / xanh / đỏ mã hóa loại phương tiện. Xáo trộn sắc độ là phá một tín hiệu thật, không phải tạo bất biến. |
| `hsv_s` | 0,7 | Nhiễu độ bão hòa rộng tay — an toàn, không đụng đến thông tin phân loại theo sắc độ. |
| `hsv_v` | 0,4 | Nhiễu độ sáng rộng tay: ảnh ban đêm, chói đèn pha, biển ngược sáng — đều là điều kiện thật ở cổng/bãi xe. |
| `degrees` | 5,0 | Xoay **nhỏ**. Biển thật gần như luôn nằm ngang trên xe đã gắn; xoay lớn dạy mô hình những tư thế không tồn tại và lãng phí dung lượng mô hình. |
| `translate` | 0,1 | Tịnh tiến vừa phải. |
| `scale` | 0,5 | Nhiễu tỷ lệ — biển xuất hiện ở nhiều khoảng cách camera khác nhau. |
| `shear` | 2,0 | Cắt nghiêng nhẹ. |
| `perspective` | 0,0005 | Biến dạng phối cảnh nhẹ. Camera cổng và bãi xe **hầu như luôn** chụp lệch trục — đây là augmentation mô phỏng đúng điều kiện triển khai. |
| `erasing` | 0,4 | Xóa ngẫu nhiên — biển thật hay bị che bởi bùn, giá đỡ biển, móc kéo. |
| `mosaic` | 1,0 | Augmentation **hiệu quả nhất cho vật thể nhỏ**, ghép 4 ảnh thành một. |
| `close_mosaic` | 10–15 | Tắt mosaic ở bằng ấy epoch **cuối** để mô hình kết thúc trên ảnh không biến dạng, gần phân phối suy luận thật. |
| `mixup` | 0,0 | Trộn alpha hai ảnh tạo ra chữ trên biển **không đọc được** và không mang tín hiệu phát hiện hữu ích. |
| `copy_paste` | 0,0 | Hướng segmentation; không áp dụng cho bài toán detection thuần. |

### 4.6. Nhóm vận hành và tái lập

| Tham số | Giá trị | Lý do |
|---|---|---|
| `seed` | **42** | Cố định để **tái lập được**. Một con số trong luận văn mà chạy lại không ra được thì không có mấy giá trị bảo vệ. |
| `deterministic` | `true` | Ép nhân tất định. Chậm hơn một chút — đổi lấy khả năng tái lập, một cái giá đáng trả. |
| `save_period` | **10** | Lưu checkpoint đánh số mỗi 10 epoch. **Không phải tùy chọn trang trí**: Colab thu hồi phiên không báo trước; xem mục 11. `train.py` cảnh báo nếu ai đặt giá trị ≤ 0. |
| `device` | `auto` | `auto` → CUDA nếu có → MPS → CPU, phân giải trong `resolve_device()`. Khi kết quả là `cpu`, script in một **banner cảnh báo lớn** kèm hướng dẫn chuyển sang Colab. |
| `workers` | 8 (nano) / 4 (yolo11s) | Tiến trình nạp dữ liệu. YOLO11s dùng batch 8 nên GPU là nút cổ chai; thêm worker chỉ tăng áp lực bộ nhớ trên VM Colab. Trên Windows nên để vừa phải vì mỗi worker phải nạp lại module. |
| `project` / `name` | `runs` / tên cấu hình | Thư mục kết quả là `<project>/<name>`. Trên Colab **bắt buộc** trỏ `--project` vào Google Drive. |
| `cache` | `false` | Không cache ảnh vào RAM/đĩa. Có thể bật `"ram"` nếu VM Colab dư bộ nhớ, đổi lấy epoch nhanh hơn. |

### 4.7. Ba cơ chế an toàn được cài trong hạ tầng

Ba lỗi dưới đây đều thuộc loại **thất bại im lặng** — chương trình chạy xong bình thường mà kết
quả sai. Chúng được chặn ở tầng mã:

1. **Khóa từ lạ trong YAML bị từ chối.** Gõ `epoch:` thay vì `epochs:` sẽ **không** bị bỏ qua
   âm thầm rồi huấn luyện với số epoch mặc định — `from_dict()` ném `ValueError` kèm danh sách
   khóa hợp lệ.
2. **Resume một lần chạy đã hoàn tất bị chặn.** Ultralytics có hành vi nguy hiểm: gọi
   `train(resume=True)` trên checkpoint của một lần chạy **đã xong** thì nó **không báo lỗi** —
   nó âm thầm bỏ yêu cầu resume và bắt đầu một lần chạy hoàn toàn mới **với tham số mặc định**,
   tức là huấn luyện trên **COCO** chứ không phải biển số. Lần chạy đó trông bình thường, kết
   thúc bình thường, rồi **ghi đè `best.pt` tốt bằng trọng số vô giá trị**.
   `assert_resumable()` đọc chỉ số epoch trong checkpoint và từ chối, kèm hướng dẫn xử lý.
3. **Đối chiếu dataset sau khi huấn luyện.** Sau khi `model.train()` trả về, `run_training()`
   so tên dataset mà Ultralytics **thực sự** đã dùng với dataset được yêu cầu, và **từ chối
   công bố** trọng số nếu lệch.

Thêm một lớp nữa khi công bố: nếu `models/best.pt` đã tồn tại, tệp cũ được **đổi tên kèm dấu
thời gian** chứ không bị ghi đè.

---

## 5. Kế hoạch thí nghiệm

### 5.1. Sơ đồ quyết định

```
        ┌─────────────────────────────────────────┐
        │ E-A: yolo11n_finetune.yaml  (CHÍNH)     │
        │      100 epoch, imgsz 640, batch 16     │
        └────────────────────┬────────────────────┘
                             │
                    evaluate.py --split test
                             │
            ┌────────────────┴─────────────────┐
            │                                  │
   NFR-A1/A2/A3 ĐẠT                   KHÔNG ĐẠT
   trên CẢ HAI loại biển                       │
            │                                  │
            ▼                    ┌─────────────┴──────────────┐
   ┌─────────────────┐           │ Hỏng ở ĐÂU?                │
   │ CHỐT YOLO11n    │           └─────┬────────────────┬─────┘
   │ Chạy E-B để có  │                 │                │
   │ số ablation     │        biển 2 dòng yếu    yếu ĐỀU cả hai
   └─────────────────┘                 │                │
                                       ▼                ▼
                          ┌────────────────────┐  ┌──────────────┐
                          │ CÂN BẰNG DATASET   │  │ E-C:         │
                          │ (không leo thang!) │  │ yolo11s      │
                          └────────────────────┘  └──────────────┘
```

### 5.2. Danh sách thí nghiệm

| Mã | Cấu hình | Mục đích | Điều kiện chạy |
|---|---|---|---|
| **E-A** | `yolo11n_finetune.yaml` | **Sinh mô hình đem dùng.** Chạy đầu tiên, luôn luôn. | Bắt buộc |
| **E-B** | `yolo11n_baseline.yaml` | Ablation transfer learning. Cùng phân chia dữ liệu với E-A → **khoảng cách mAP chính là giá trị đo được của pretrain COCO**. | Bắt buộc (nội dung chương thực nghiệm) |
| **E-C** | `yolo11s_escalation.yaml` | Leo thang dung lượng mô hình. Khác E-A **đúng một chiều**: `model_variant`. | **Chỉ khi E-A không đạt và yếu đều cả hai loại biển** |
| **E-D** | E-A với `--imgsz 480` và `--imgsz 800` | Đo đường cong đánh đổi độ phân giải ↔ mAP ↔ độ trễ CPU. Lấp khoảng trống E3 của Phase 1. | Tùy chọn, nếu còn ngân sách GPU |
| **E-E** | YOLO26n đối chứng | Khuyến nghị Phase 1 mục 9.3. **Hạ tầng hiện chưa hỗ trợ** — xem mục 9.3. | Chưa khả thi |

### 5.3. Nguyên tắc phương pháp

**Mỗi thí nghiệm chỉ được khác thí nghiệm gốc ở một chiều.** Đây là lý do `yolo11s_escalation.yaml`
giữ **nguyên xi** chính sách augmentation, `imgsz`, `epochs`, `patience` và `seed` của cấu hình
nano. Nếu đổi đồng thời dung lượng mô hình và chính sách augmentation thì chênh lệch mAP thu được
không quy được cho nguyên nhân nào — thí nghiệm chứng minh con số không.

Hai ngoại lệ có chủ ý ở E-C, đều là **hệ quả kỹ thuật bắt buộc** chứ không phải lựa chọn tự do:
`batch` giảm 16 → 8 (tránh OOM trên T4) và `lr0` giảm theo batch để giữ bước cập nhật hiệu dụng
tương đương. Cả hai phải được **nêu rõ** khi báo cáo so sánh E-A với E-C.

**Cùng một phân chia dữ liệu cho mọi thí nghiệm.** `seed = 42` và cùng `data.yaml`.

### 5.4. Cách so sánh kết quả

| So sánh | Trả lời câu hỏi | Đọc bảng nào |
|---|---|---|
| E-A vs E-B | Transfer learning từ COCO đáng giá bao nhiêu điểm mAP? | Bảng 10.1 |
| E-A vs E-C | Tăng gấp ~3 tham số đổi được bao nhiêu mAP, và **trả giá bao nhiêu ms** trên CPU? | Bảng 10.1 + 10.3 |
| E-A tách 1 dòng / 2 dòng | Mô hình có dùng được cho **xe máy** không? | Bảng 10.2 |
| E-D các mức imgsz | Có giảm được `imgsz` để nhanh hơn mà không mất recall? | Bảng 10.4 |

> Cảnh báo trước một cái bẫy: nếu E-A không đạt vì **biển 2 dòng yếu**, đừng leo thang sang
> YOLO11s. Đó là chẩn đoán sai bệnh. Điểm yếu ở một **phân nhóm dữ liệu** là vấn đề **dữ liệu**,
> và thêm tham số vào mô hình không tạo ra dữ liệu. Cân bằng lại dataset trước. Comment ở đầu
> `yolo11s_escalation.yaml` nói đúng điều này, ngay tại chỗ người ta sắp mắc lỗi.

---

## 6. Quy trình đánh giá

Công cụ: [`ai/evaluation/evaluate.py`](../../ai/evaluation/evaluate.py).

### 6.1. Nguyên tắc đo

* **Đo trên tập `test`, không phải `val`.** Tập val đã tham gia chọn `best.pt` (fitness theo
  epoch), nên báo cáo con số val là báo cáo một ước lượng lạc quan có thiên lệch. Mặc định của
  `--split` là `test` đúng vì lý do này.
* **Ultralytics validator là tham chiếu.** Script chạy pass validation chính thức của Ultralytics
  để lấy mAP, đồng thời có bộ so khớp riêng để tính bảng tách nhóm — hai nguồn kiểm chứng chéo
  nhau.
* **Độ trễ đo với `--device cpu`** kể cả khi chạy trên Colab.

### 6.2. Các chỉ số báo cáo

| Chỉ số | Ứng với NFR | Ghi chú |
|---|---|---|
| mAP@0.5 | NFR-A1 | Chỉ tiêu chính |
| mAP@0.5:0.95 | NFR-A2 | Báo cáo kèm; phản ánh chất lượng khớp box |
| Precision / Recall | NFR-A3 | **Kèm ngưỡng confidence tối ưu theo F1** |
| F1 | — | Dùng để chọn điểm vận hành |
| TP / FP / FN | — | Con số thô, để kiểm tra chéo |
| Đường cong PR, ma trận nhầm lẫn | — | `docs/reports/figures/*.png` |
| Độ trễ p50 / p95 / p99 | NFR-P (phase khác) | Đo trên ảnh thật, `--speed-samples` |

### 6.3. Đánh giá tách riêng biển 1 dòng / 2 dòng (NFR-A8) — phần quan trọng nhất

**Đây là con số cần nhìn trước tiên, không phải mAP tổng.**

Lý do: biển 2 dòng là **rủi ro kỹ thuật lớn nhất** của toàn dự án (**R-04**). Trên bộ
**RodoSol-ALPR của Brazil** ([Laroca et al., VISAPP 2022](https://arxiv.org/abs/2201.00267)),
OpenALPR đạt **94,3%** trên biển ô tô 1 dòng nhưng chỉ **45,7%** trên biển xe máy 2 dòng —
*số liệu Brazil, dẫn như analogue định lượng, không phải đo trên biển số Việt Nam*. Một con số mAP tổng
**che giấu đúng thất bại đó**: mô hình có thể trông khỏe mạnh trong khi vô dụng với một nửa số
phương tiện lưu thông ở Việt Nam. Xe máy không phải trường hợp biên ở Việt Nam — nó là **trường
hợp phổ biến nhất**.

Định dạng bảng mà `evaluate.py` in ra:

```
GROUP            N_GT     TP     FP     FN        P        R       F1    mAP50  mAP50-95
single_line      ...
two_line         ...
ALL              ...
NFR-A8 gap (single-line AP@0.5 minus two-line AP@0.5): +0.xxxx
```

Nếu khoảng cách vượt **10 điểm AP**, script cảnh báo và khuyến nghị **cân bằng lại dataset**
trước khi nghĩ tới việc dùng mô hình lớn hơn.

### 6.4. Cách phân nhóm 1 dòng / 2 dòng

Theo thứ tự ưu tiên (script tự chọn nguồn tốt nhất hiện có):

1. **Cột `line_count`** (cột thứ 6) trong tệp nhãn, nếu có — nguồn đáng tin nhất.
2. **Tên lớp mang thông tin bố cục**: `plate_1line` / `plate_2line` và các biến thể phổ biến.
3. **Suy đoán theo tỷ lệ khung hình**, dựa trên **QCVN 08:2024/BCA**:

| Loại biển | Kích thước | Tỷ lệ khung hình | Số dòng |
|---|---|---|---|
| Ô tô, biển dài | 520 × 110 mm | **4,727** | **1 dòng** |
| Ô tô, biển ngắn | 330 × 165 mm | **2,000** | **2 dòng** |
| Mô tô, xe máy | 190 × 140 mm | **1,357** | **2 dòng** |

Hai nhóm tách nhau rất rõ (**2,000** so với **4,727**), nên ngưỡng **2,5** phân loại ổn định
ngay cả khi hộp dự đoán không hoàn hảo.

> Ngưỡng 2,5 **cố ý trùng** với `InferenceConfig.two_line_aspect_ratio_threshold` của tầng suy
> luận. Nếu đánh giá phân loại biển theo một quy tắc khác với hệ thống triển khai thì độ chính
> xác báo cáo **không mô tả hệ thống thật** — nó mô tả một hệ thống giả định.

Nếu **toàn bộ** hộp phải phân nhóm bằng suy đoán tỷ lệ (nghĩa là nhãn không mang thông tin bố
cục), script cảnh báo, và **bản báo cáo kết quả phải nói rõ điều đó** — vì khi ấy bảng NFR-A8
mang một tầng bất định nữa.

### 6.5. Đầu ra

| Loại | Vị trí |
|---|---|
| Báo cáo JSON | `docs/reports/03-evaluation-*.json` |
| Biểu đồ PNG | `docs/reports/figures/` |

---

## 7. Kế hoạch đo tốc độ CPU

Công cụ: [`ai/evaluation/benchmark_cpu.py`](../../ai/evaluation/benchmark_cpu.py).

### 7.1. Nguyên tắc bắt buộc

> **Luận văn chỉ được trích số CPU do chính script này đo trên chính máy này.**
>
> Phase 1 đã ghi nhận cảnh báo rõ ràng: benchmark CPU công bố của Ultralytics được đo trên
> **Amazon EC2 P4d**, không đại diện cho máy của đồ án. Con số "**ONNX nhanh hơn PyTorch ~3,7 lần**"
> trong tài liệu Phase 1 là **số tham khảo từ nguồn ngoài** và **phải được thay** bằng số đo thật.

### 7.2. Phương pháp đo

Bốn quyết định phương pháp, mỗi cái tránh một lỗi đo cụ thể:

1. **Cùng ảnh, cùng thứ tự, cho mọi backend** — nếu không thì đang so nội dung ảnh chứ không
   phải backend.
2. **Bỏ pha warm-up khỏi thống kê** (`--warmup 5`). Lần suy luận đầu của bất kỳ backend nào cũng
   phải trả chi phí một lần cho việc dựng graph và cấp phát bộ nhớ. Gộp nó vào là báo cáo sai
   độ trễ trạng thái ổn định.
3. **Một ảnh mỗi lần gọi**, đúng cách API phục vụ một lượt tải ảnh lên — không phải batch.
4. **Báo cáo phần trăm vị, không chỉ trung bình.** Đuôi p95/p99 mới là thứ người dùng cảm nhận,
   và đuôi của suy luận CPU thì dài.

Script ghi kèm tên CPU, số nhân vật lý/luận lý, RAM và số luồng PyTorch, để số liệu còn diễn
giải được sau một năm.

### 7.3. Các backend so sánh

| Backend | Vai trò | Gói cần cài |
|---|---|---|
| **PyTorch** (eager) | Mốc chuẩn, hệ số 1,00× | có sẵn |
| **ONNX Runtime** | Ứng viên chính cho triển khai CPU | `onnx onnxruntime onnxslim` |
| **OpenVINO** | Tối ưu cho phần cứng Intel (máy này là Intel) | `openvino` |
| TorchScript | Đối chứng, không cần runtime ngoài | có sẵn |

### 7.4. Ghi chú về FP16 và imgsz

* **Không dùng `--half` cho mục tiêu CPU.** FP16 là tối ưu hóa của GPU; trên CPU nó thường bị
  bỏ qua hoặc phải giả lập, và có thể **chậm hơn** FP32. `export.py` in cảnh báo nếu bị yêu cầu.
* Đo ở **`imgsz = 640`**, đúng độ phân giải huấn luyện và triển khai. Đo ở độ phân giải khác rồi
  báo cáo là số của hệ thống là sai lệch.

### 7.5. Số liệu đã có: chỉ là kiểm chứng hạ tầng, KHÔNG dùng được

Tệp [`ai/training/README.md`](../../ai/training/README.md) mục 9 có ghi một bảng số đo từ lần
chạy thử hạ tầng trước đây, trên **Intel Core i5-14600K (14 nhân / 20 luồng)**:

| Backend | Trung bình | p50 | p95 | Tăng tốc |
|---|---|---|---|---|
| PyTorch | 14,53 ms | 13,70 ms | 17,79 ms | 1,00× |
| ONNX Runtime | 6,18 ms | 6,05 ms | 6,59 ms | 2,35× |
| OpenVINO | 10,67 ms | 9,93 ms | 14,06 ms | 1,36× |

> **Bảng này KHÔNG được đưa vào luận văn.** Ba lý do, mỗi lý do đủ để loại:
> 1. Đo trên một **mô hình tổng hợp chưa huấn luyện thật**, không phải `models/best.pt`.
> 2. Đo ở **`imgsz = 320`**, không phải 640 của hệ thống thật.
> 3. **Không kiểm chứng lại được từ kho mã hiện tại**: thư mục `runs/`, `logs/` và tệp JSON kết
>    quả benchmark **không tồn tại** trên đĩa ở thời điểm lập báo cáo này. Chỉ còn lại con số
>    chép trong README.
>
> Nó chỉ chứng minh **đường ống export + benchmark chạy được**. Phải đo lại toàn bộ với mô hình
> thật, `imgsz = 640` và ảnh test thật.
>
> Một quan sát **định tính** từ bảng trên vẫn đáng lưu ý và cần kiểm chứng lại: **OpenVINO không
> thắng ONNX Runtime** dù đây là CPU Intel. Phase 1 đã cảnh báo "OpenVINO không phải luôn thắng";
> quan sát này khớp với cảnh báo đó. Đừng chọn định dạng triển khai theo giả định.

---

## 8. Hướng dẫn chạy

### 8.1. Trên Google Colab GPU — đường đi chính

Notebook: [`notebooks/train_colab.ipynb`](../../notebooks/train_colab.ipynb). Chạy tuần tự
10 ô. Bảng dưới tóm tắt; hướng dẫn chi tiết nằm ngay trong ô 1 của notebook.

| Ô | Việc | Điểm cần chú ý |
|---|---|---|
| **1** | Hướng dẫn (markdown) | **Trước hết: `Runtime` → `Change runtime type` → `Hardware accelerator` = **GPU** (T4 là đủ)** |
| **2** | Kiểm tra GPU | Chạy `nvidia-smi` và `torch.cuda.is_available()`. **Ném `RuntimeError` nếu không có GPU** — cố ý báo lỗi to thay vì để một lần chạy CPU nhiều giờ khởi động âm thầm |
| **3** | Gắn Google Drive | **Không phải tùy chọn.** Đặt `DRIVE_ROOT = /content/drive/MyDrive/DATN`, tạo `runs/`, `datasets/`, `models/`, `logs/` |
| **4** | Đưa mã nguồn lên VM | `SOURCE_MODE = "clone"` (git clone — khuyến nghị, gắn lần chạy với một commit xác định) hoặc `"drive"` (chép từ thư mục đã tải lên Drive) |
| **5** | Cài phụ thuộc | `pip install ultralytics==8.4.101` + `onnx onnxruntime onnxslim openvino`. **Cố ý KHÔNG dùng `ai/requirements.txt`** — tệp đó ghim bản torch **CPU-only** cho máy Windows và cài nó sẽ hạ cấp torch của Colab thành bản không có CUDA |
| **6** | Giải nén dataset về **đĩa cục bộ của VM** | Đọc dataset **từ đĩa VM, không đọc thẳng từ Drive**: I/O của Drive chậm và bị giới hạn tần suất; một epoch stream từng ảnh qua Drive có thể lâu hơn cả forward+backward |
| **7** | **Huấn luyện** | Đặt `CONFIG` và `RESUME`. Truyền `--project` **trỏ thẳng vào Drive** |
| **8** | Đánh giá | `--device cpu` (cố ý), `--split test`, in bảng tách 1 dòng / 2 dòng |
| **9** | Xuất mô hình | `--format all --imgsz 640`; mỗi định dạng được **nạp lại và chạy thử** trước khi báo thành công |
| **10** | Lưu sản phẩm | Chép JSON + PNG + trọng số về Drive, và mở tải xuống trực tiếp `best.pt` |

Nội dung ô 7 (huấn luyện):

```python
CONFIG = "yolo11n_finetune.yaml"   # hoặc yolo11n_baseline.yaml / yolo11s_escalation.yaml
RESUME = False                     # đặt True để chạy tiếp một lần chạy bị ngắt

resume_flag = "--resume" if RESUME else ""

!python -m ai.training.train \
    --config {CONFIG} \
    --device auto \
    --project "{DRIVE_RUNS}" \
    --models-dir "{DRIVE_MODELS}" \
    --log-dir "{DRIVE_LOGS}" \
    {resume_flag}
```

### 8.2. Dưới máy cục bộ

**Chỉ dùng để kiểm tra cấu hình và chạy thử đường ống. Không huấn luyện thật trên CPU.**

Mọi lệnh phải chạy từ thư mục gốc `D:/DATN` (hoặc đặt `PYTHONPATH=D:/DATN`) để `python -m ai...`
tìm được gói.

```bash
# 1. In cấu hình hiệu lực rồi thoát — không huấn luyện. Cách rẻ nhất để kiểm tra YAML.
D:/DATN/.venv-ai/Scripts/python.exe -m ai.training.train \
    --config yolo11n_finetune.yaml --print-config

# 2. Chạy thử đường ống: vài phút, kết quả VÔ NGHĨA nhưng chứng minh mọi thứ chạy được.
D:/DATN/.venv-ai/Scripts/python.exe -m ai.training.train \
    --config yolo11n_finetune.yaml \
    --device cpu --epochs 1 --fraction 0.01 --batch 2 --name smoke_test
```

Khi phát hiện thiết bị là CPU, `train.py` in banner:

```
CANH BAO: dang huan luyen tren CPU, se rat cham.
  - Khong tim thay GPU CUDA. Mot epoch tren ~37.000 anh co the mat nhieu gio.
  - Khuyen nghi: chay tren Google Colab GPU bang notebooks/train_colab.ipynb.
```

Đánh giá, xuất và đo tốc độ — **các bước này thì chạy cục bộ mới đúng**:

```bash
# Đánh giá trên tập test, có tách riêng biển 1 dòng / 2 dòng (NFR-A8)
python -m ai.evaluation.evaluate \
    --weights models/best.pt --split test --device cpu --speed-samples 200

# Xuất sang các định dạng chạy CPU (mỗi định dạng được nạp lại và chạy thử)
python -m ai.training.export --weights models/best.pt --format all --imgsz 640

# Đo tốc độ thật trên CHÍNH máy này — số liệu duy nhất được trích vào luận văn
python -m ai.evaluation.benchmark_cpu \
    --weights models/best.pt \
    --images datasets/processed/test/images \
    --imgsz 640 --runs 50 --warmup 5
```

### 8.3. Tham số dòng lệnh chính

`train.py`:

```
--config           (bắt buộc) tệp YAML; chỉ cần tên tệp là tìm trong ai/training/configs/
--resume [PATH]    huấn luyện tiếp; không có PATH thì tự tìm last.pt mới nhất
--device           auto | cpu | 0 | 0,1 | mps
--epochs / --batch / --imgsz / --workers / --fraction    ghi đè tương ứng
--data             ghi đè đường dẫn data.yaml
--name / --project ghi đè thư mục kết quả
--models-dir       nơi công bố best.pt (mặc định: D:/DATN/models)
--log-dir          nơi ghi tệp log (mặc định: D:/DATN/logs/training)
--print-config     in cấu hình hiệu lực rồi thoát, không huấn luyện
--quiet            log mức INFO thay vì DEBUG
```

Mọi giá trị ghi đè đều được **kiểm tra lại** qua `TrainingConfig`, nên tham số sai bị từ chối
ngay lập tức chứ không đợi đến giữa lần chạy.

`evaluate.py`: `--weights --data --split --imgsz --conf --iou --batch --device --ar-threshold
--speed-samples --max-images --output-dir --name --no-plots --skip-ultralytics-val`

`benchmark_cpu.py`: `--weights --images --backends --imgsz --runs --warmup --max-images
--threads --output-dir --no-save`

`export.py`: `--weights --format --imgsz --half --dynamic --no-simplify --opset --batch --no-verify`

### 8.4. Sản phẩm sau một lần chạy

Thư mục `<project>/<name>/`:

| Tệp | Nội dung |
|---|---|
| `weights/best.pt` | Trọng số tốt nhất theo fitness trên tập val — **sản phẩm bàn giao** |
| `weights/last.pt` | Trọng số epoch cuối — dùng để `--resume` |
| `weights/epoch*.pt` | Checkpoint định kỳ theo `save_period` |
| `results.csv` / `results.png` | Loss và mAP theo từng epoch |
| `confusion_matrix.png`, `PR_curve.png`, `F1_curve.png` | Biểu đồ chẩn đoán |
| `labels.jpg` | Phân bố nhãn — kiểm tra nhanh dataset có lệch không |
| `args.yaml` | Tham số Ultralytics đã dùng |
| `training_config.yaml` | **Bản chụp `TrainingConfig`**, nạp lại được bằng `from_yaml()` |

`best.pt` được tự động chép về `models/best.pt` — đúng đường dẫn mà tầng suy luận nạp mặc định
(`ALPR_MODEL_PATH`).

---

## 9. Tình trạng hiện tại

### 9.1. Trạng thái huấn luyện — cập nhật 2026-07-20

> ## ✅ MÔ HÌNH CHÍNH THỨC `best.pt` ĐÃ HUẤN LUYỆN XONG
>
> Mục này đã được viết lại. Bản trước ghi "đang huấn luyện baseline" và nay **không còn đúng**:
> lượt baseline đã xong (cho `baseline-416-v1.pt`, nay là mô hình đối chứng) **và** lượt chính
> thức `imgsz=640` trên split v3 cũng đã xong (cho `models/best.pt`).

**Lượt chính thức đã hoàn tất — `runs/final-640-v3/`:**

| Tham số | Giá trị | Ghi chú |
|---|---|---|
| Cấu hình | `yolo11n_finetune.yaml` | Transfer từ trọng số COCO |
| Thiết bị | **CPU** | Máy không có GPU CUDA |
| **`imgsz`** | **640** | Đúng độ phân giải chỉ tiêu NFR đặt ra |
| `epochs` | 20 | Epoch tốt nhất theo mAP@0.5:0.95 = epoch 20 |
| Dữ liệu | `datasets/processed/yolo_v3/` — 10.592 train / 3.027 val / 1.514 test | Bộ v3, 15.133 ảnh, khử trùng lặp ở ngưỡng 10 |
| Tham số mô hình | 2.590.035 | YOLO11n |

**Lượt baseline đối chứng — `runs/cpu-finetune-416/`:**

| Tham số | Giá trị | Ghi chú |
|---|---|---|
| **`imgsz`** | **416** | ⚠️ Chỉ dùng đối chứng — xem cảnh báo bên dưới |
| `epochs` | 40 (epoch tốt nhất 38) | ~230 giây/epoch ⇒ tổng ~156 phút |
| Dữ liệu | Bộ v1, 4.578 ảnh | Có rò rỉ train↔test đã biết |

---

> ### ⛔ SAI LỆCH PHƯƠNG PHÁP LUẬN CẦN GHI NHẬN: `imgsz` = 416, không phải 640
>
> Toàn bộ chỉ tiêu **NFR-A1** (mAP@0.5 ≥ 0,90) và **NFR-A2** (mAP@0.5:0.95 ≥ 0,65) trong
> [non-functional-requirements.md](../00-requirements/non-functional-requirements.md) được đặt
> trên giả định `imgsz = 640` — đó là kích thước chuẩn mà mọi bảng benchmark của Ultralytics
> trích dẫn ở [01-yolo-comparison.md](01-yolo-comparison.md) sử dụng. Chính tài liệu này ở
> mục 1 cũng liệt kê "giảm `imgsz` xuống 480" như một **phương án giảm tải khi không đạt chỉ tiêu**,
> tức mặc định là 640.
>
> Lần chạy hiện tại dùng **416** để rút ngắn thời gian trên CPU. Hệ quả:
>
> * **Kết quả của lần chạy này KHÔNG so sánh trực tiếp được với NFR-A1/NFR-A2.**
>   Không được viết "đạt chỉ tiêu mAP@0.5 ≥ 0,90" dựa trên lần chạy 416px.
> * Ảnh nhỏ hơn ⇒ biển số ở xa chiếm ít pixel hơn ⇒ **thường bất lợi** cho recall trên
>   vật thể nhỏ. Bộ dữ liệu này có **477 box dưới 0,5% diện tích ảnh** (9,17%), là nhóm
>   chịu ảnh hưởng nặng nhất.
>
> **Cách xử lý đã chọn — không giấu, biến thành khảo sát có ích (ĐÃ THỰC HIỆN XONG):**
>
> 1. ✅ Lần chạy 416px chạy hết 40 epoch, giữ làm **baseline / mốc đối chứng** (`baseline-416-v1.pt`).
> 2. ✅ Mô hình **đưa vào quyển đồ án** đã được huấn luyện ở **`imgsz = 640`** trên bộ dữ liệu
>    v3 (đã khử trùng lặp ở ngưỡng 10), cho `models/best.pt` — so được với chỉ tiêu đã công bố.
> 3. Cặp 416/v1 ↔ 640/v3 trở thành một **khảo sát ảnh hưởng của độ phân giải + bộ dữ liệu** — xem
>    bảng so sánh ở [05-tables.md §T5.8](05-tables.md). ⚠️ Lưu ý: ba biến (imgsz, bộ dữ liệu/cách
>    chia, số epoch) đổi đồng thời và tác động ngược chiều nhau, nên chỉ được **mô tả** chứ không
>    quy kết nguyên nhân cho bất kỳ biến nào.
>
> Mọi bảng kết quả **bắt buộc ghi rõ `imgsz`** ở tiêu đề cột hoặc chú thích. Công bố mAP mà
> không kèm `imgsz` là lỗi phương pháp luận cùng loại với công bố FPS mà không kèm cấu hình CPU.

---

**Vì sao huấn luyện cục bộ:** để toàn hệ thống có một mô hình **thật** mà kiểm thử. Nếu tiếp tục
chạy `StubPipeline`, mọi số liệu sẽ là số của mã giả lập, không đo được gì. **Mục đích này đã
đạt:** hệ thống nạp `models/best.pt` (`/health` báo `model_loaded: true`, engine
`yolo:best.pt+paddleocr-PP-OCRv5-mobile`), và `StubPipeline` đã bị đưa ra khỏi đường chạy chính —
thay bằng `UnavailablePipeline`.

**Đã có đầy đủ:** `models/best.pt` (mô hình chính thức — lượt `imgsz=640` trên split v3, 20 epoch,
epoch tốt nhất = 20), kết quả đánh giá trên tập test v3 (mAP@0.5 = 0,9829 / mAP@0.5:0.95 = 0,7834),
và kết luận NFR-A1/A2/A3 (đạt) và NFR-A8 (chênh layout 2,09 điểm) — xem mục 10.

### 9.2. Những gì ĐÃ có

| Hạng mục | Vị trí | Tình trạng |
|---|---|---|
| Lớp cấu hình có kiểm tra hợp lệ | `ai/training/config.py` | ✅ Có |
| Ba tệp cấu hình YAML | `ai/training/configs/*.yaml` | ✅ Có |
| Script huấn luyện có log, resume, chốt an toàn | `ai/training/train.py` | ✅ Có |
| Script xuất ONNX/OpenVINO/TorchScript có tự kiểm chứng | `ai/training/export.py` | ✅ Có |
| Script đánh giá có tách nhóm 1 dòng / 2 dòng | `ai/evaluation/evaluate.py` | ✅ Có |
| Script đo tốc độ CPU đa backend | `ai/evaluation/benchmark_cpu.py` | ✅ Có |
| Notebook Colab 10 ô | `notebooks/train_colab.ipynb` | ✅ Có |
| Tài liệu vận hành hạ tầng | `ai/training/README.md` | ✅ Có |
| Dataset v1 đã xử lý | `datasets/processed/yolo/data.yaml` | ✅ Có — 4.578 ảnh |
| Dataset v3 (đã khử trùng lặp) | `datasets/processed/yolo_v3/` | ✅ Có — 15.133 ảnh, 6 nguồn nguyên tố, khử trùng lặp ở ngưỡng 10 |
| Trọng số COCO để transfer | `models/pretrained/yolo11n-coco.pt` | ✅ Có — **80 lớp COCO, KHÔNG phát hiện biển số** |
| Checkpoint giữa chừng | `models/checkpoints/best-cpu-epoch7.pt` | ✅ Có — checkpoint baseline, chỉ để đối chiếu |
| Nhật ký huấn luyện | `runs/final-640-v3/`, `runs/cpu-finetune-416/`, `logs/training/` | ✅ Có — `results.csv` cập nhật theo epoch |
| **Trọng số chính thức** | `models/best.pt` | ✅ **Đã có** — YOLO11n, `imgsz=640`, split v3, 20 epoch |
| **Kết quả đánh giá tập test** | `docs/reports/03-evaluation-ch5-best-test.json`, `docs/reports/05-tables.md` | ✅ **Đã có** — mAP@0.5 = 0,9829, mAP@0.5:0.95 = 0,7834 |
| **Số đo tốc độ CPU với mô hình thật** | `docs/reports/05-benchmark-system-best.json`, `07-benchmark-p1-resolved.json` | ✅ Đã đo — p95 E2E 780,36 ms (in-process) / 731,15 ms (client-side) |

### 9.3. Các khoảng trống đã biết

| # | Khoảng trống | Ảnh hưởng | Cách xử lý |
|---|---|---|---|
| G1 | ✅ **Đã xử lý — Dataset Phase 2 xong.** Khi tài liệu này viết lần đầu, `datasets/processed/data.yaml` chưa tồn tại. | Nay đã có bộ v2 (`datasets/processed/yolo_v2/`, 15.133 ảnh) và bộ v3 đã làm sạch rò rỉ. ⚠️ **`yolo_v2`/`yolo_v3` là *phiên bản bộ dữ liệu*, không phải YOLOv2/YOLOv3** — mô hình dùng là YOLO11n (2.590.035 tham số). Xem `datasets/processed/README.md`. | — |
| G2 | **Chưa hỗ trợ YOLO26n.** `SUPPORTED_MODEL_VARIANTS` mới có `yolo11n/s/m/l/x`. | Khuyến nghị đối chứng ở 01-yolo-comparison.md mục 9.3 **chưa thực hiện được**. | Thêm `yolo26n` vào danh sách biến thể và tạo `yolo26n_control.yaml`; ngoài ra không cần đổi gì vì Ultralytics dùng chung API |
| G3 | ✅ **Đã xử lý — `models/README.md` đã có.** Khi tài liệu này viết lần đầu, thư mục `models/` chỉ có `.gitkeep` và trọng số COCO nằm trong `models/interim/`. | Người đọc dễ nhầm mô hình tạm với mô hình thật. | Đã viết `models/README.md`. Thư mục `interim/` **đã bị bỏ**, đổi thành **`models/pretrained/`** (`models/pretrained/yolo11n-coco.pt`) — chính vì tên `interim` gợi ý sai rằng đó là "mô hình tạm đang dùng được", trong khi trọng số COCO **không phát hiện được biển số** |
| G4 | **Số benchmark CPU trong `ai/training/README.md` không kiểm chứng lại được.** | Không còn tệp JSON hay `runs/` để đối chiếu. | Không trích vào luận văn; đo lại sau khi có mô hình thật (mục 7.5) |
| G5 | **Chưa kiểm tra wheel `onnxruntime`/`openvino` cho Python 3.13 trên Windows 11.** | Rủi ro phải hạ về Python 3.11/3.12 để export. Phase 1 đã nêu. | Kiểm tra khi chạy `export.py` lần đầu; đã có Python 3.11 làm phương án lùi |

---

## 10. Bảng kết quả

> **Cấu hình chính (E-A) ĐÃ điền số đo thật** từ `models/best.pt` trên tập test v3.
> Các thí nghiệm bổ sung (E-B, E-C, E-D) chưa chạy — ô `—` nghĩa là **chưa đo**, không phải bằng 0.
> Nguồn số: [`docs/reports/05-tables.md`](05-tables.md) và `05-results.json`.

### 10.1. Bảng 1 — Kết quả huấn luyện tổng thể

| Thí nghiệm | Cấu hình | Biến thể | imgsz / split | Epoch chạy | mAP@0.5 | mAP@0.5:0.95 | Precision | Recall | F1 | Ngưỡng conf | Đạt NFR-A1? | Đạt NFR-A2? | Đạt NFR-A3? |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **E-A** (chính thức) | `yolo11n_finetune.yaml` | YOLO11n | 640 / v3 | 20 | **0,9829** | **0,7834** | **0,9837** | **0,9714** | 0,9775 | 0,25 | ✅ | ✅ | ✅ |
| **E-B** | `yolo11n_baseline.yaml` | YOLO11n | — | — | — | — | — | — | — | — | — | — | — |
| **E-C** | `yolo11s_escalation.yaml` | YOLO11s | — | — | — | — | — | — | — | — | — | — | — |
| *baseline (đối chứng)* | `yolo11n_finetune.yaml` | YOLO11n | 416 / v1 | 40 | 0,9933 | 0,8597 | 0,9822 | 0,9810 | — | — | ⚠️ *(416, rò rỉ)* | ⚠️ | ⚠️ |

**Chỉ tiêu tham chiếu:** NFR-A1 ≥ 0,90 · NFR-A2 ≥ 0,65 · NFR-A3 P ≥ 0,92 / R ≥ 0,90.

**Giá trị đo được của transfer learning** = mAP@0.5 của E-A − mAP@0.5 của E-B = **—** *(E-B chưa chạy)*

> ⚠️ Dòng baseline chỉ để đối chứng, **không** được báo cáo là "đạt": đo ở `imgsz=416` (không so
> trực tiếp với chỉ tiêu đặt ở 640) và trên bộ v1 có rò rỉ train↔test đã biết (619 cặp ở ngưỡng
> phash 10), nên mAP 0,9933 **lạc quan hơn hiệu năng thật**. Mô hình `best.pt` train trên split v3
> đã khử trùng lặp ở ngưỡng 10, không còn hiện tượng rò rỉ thổi phồng như baseline.

### 10.2. Bảng 2 — Tách riêng biển 1 dòng / 2 dòng (NFR-A8)

Cho **E-A** (`best.pt`, tập test v3). Nguồn: `ultralytics_val` tách theo layout, [05-tables.md §T5.5b](05-tables.md).

| Nhóm | N_GT | Precision | Recall | F1 | mAP@0.5 | mAP@0.5:0.95 |
|---|---|---|---|---|---|---|
| `single_line` (biển 1 dòng) | 286 | 0,9861 | 0,9895 | 0,9878 | 0,9884 | 0,7526 |
| `two_line` (biển 2 dòng) | 1.325 | 0,9735 | 0,9691 | 0,9713 | 0,9675 | 0,7649 |
| **ALL** | 1.611 | 0,9837 | 0,9714 | 0,9775 | 0,9829 | 0,7834 |

**Khoảng cách NFR-A8** (mAP@0.5 của 1 dòng − mAP@0.5 của 2 dòng) = **+2,09 điểm** *(dưới 10 điểm → không cần cân bằng lại dataset ở tầng detection)*

> Ở **tầng phát hiện**, detection ít nhạy với layout: chênh chỉ 2,09 điểm mAP@0.5. Điểm yếu biển 2
> dòng bộc lộ ở **tầng OCR** chứ không phải detection — xem [04-ocr-report.md] và T5.6c.

**Nguồn phân nhóm đã dùng:** ☑ suy đoán theo tỷ lệ khung hình (ngưỡng 2,5) — bộ dữ liệu không
khai báo lớp layout nên 100% ô suy bằng heuristic; đây là **ước lượng**, mọi kết luận NFR-A8 phải nêu rõ.

### 10.3. Bảng 3 — Tốc độ suy luận trên CPU máy cục bộ

Máy đo: **Intel Core i5-14600K**, Windows 11, Python 3.13, **không có GPU CUDA**.
Điều kiện: `imgsz = 640`, batch = 1, ảnh test thật, đã bỏ warm-up.

| Backend | Định dạng tệp | Kích thước (MB) | Trung bình (ms) | p50 (ms) | p95 (ms) | p99 (ms) | Tăng tốc so với PyTorch |
|---|---|---|---|---|---|---|---|
| PyTorch (eager) | `.pt` | — | — | — | — | — | 1,00× |
| ONNX Runtime | `.onnx` | — | — | — | — | — | — |
| OpenVINO | `_openvino_model/` | — | — | — | — | — | — |
| TorchScript | `.torchscript` | — | — | — | — | — | — |

**Định dạng chọn để triển khai:** — *(điền sau khi đo)*

### 10.4. Bảng 4 — Ảnh hưởng của `imgsz` (thí nghiệm E-D, tùy chọn)

| `imgsz` | mAP@0.5 | mAP@0.5:0.95 | Recall | Độ trễ CPU p50 (ms) | Nhận xét về chất lượng ảnh cắt cho OCR |
|---|---|---|---|---|---|
| 480 | — | — | — | — | — |
| **640** (chuẩn) | — | — | — | — | — |
| 800 | — | — | — | — | — |

### 10.5. Bảng 5 — Kết luận chốt mô hình

| Câu hỏi | Trả lời |
|---|---|
| Mô hình chốt để triển khai | **`models/best.pt`** — YOLO11n, `imgsz=640`, split v3, 20 epoch |
| Định dạng chốt để triển khai | `.pt` (PyTorch eager) — NFR-P1 đã đạt mà không cần export detector |
| Đạt đủ NFR-A1, A2, A3? | **Có** (mAP@0.5 0,9829 / mAP@0.5:0.95 0,7834 / P 0,9837 / R 0,9714) ở **tầng detection** |
| Có phải leo thang lên YOLO11s không? | **Không** — YOLO11n đã đạt chỉ tiêu detection |
| Biển 2 dòng có đạt mức dùng được không? | **Detection: có** (chênh 2,09 điểm). **OCR: chưa** — char_acc biển 2 dòng 0,846 so với 0,990 biển 1 dòng (T5.6c) |
| Ngày huấn luyện | Đo lúc 2026-07-20 |
| Commit sinh ra mô hình | *(xem `runs/final-640-v3/args.yaml`)* |

---

## 11. Rủi ro và cách đối phó

### 11.1. R-C1 — Colab ngắt phiên giữa chừng

**Mức độ: chắc chắn xảy ra, không phải "có thể".** Colab thu hồi máy ảo không báo trước, và khi
VM biến mất thì **toàn bộ đĩa cục bộ biến mất theo**.

**Chuẩn bị — làm từ đầu, không phải sau khi đã mất:**

| Biện pháp | Cài ở đâu |
|---|---|
| Gắn Google Drive | Ô 3 của notebook |
| `--project` trỏ **thẳng vào Drive** → mọi checkpoint nằm ngoài VM | Ô 7 của notebook |
| `--log-dir` trỏ vào Drive → log sống sót để chẩn đoán | Ô 7 của notebook |
| `save_period: 10` → checkpoint đánh số mỗi 10 epoch | Cả ba tệp YAML |
| `last.pt` được ghi **mỗi epoch** | Hành vi mặc định Ultralytics |
| Ghi log ra **cả stdout và tệp** | `configure_logging()` trong `train.py` |

**Khôi phục:**

1. Mở lại notebook, chạy lại các ô 2 → 3 → 4 → 5 → 6.
2. Ở ô 7 đặt `RESUME = True`, chạy lại.
3. `train.py` tự tìm `last.pt` mới nhất của lần chạy đó và tiếp tục **đúng từ epoch đang dở**.

Hoặc bằng dòng lệnh:

```bash
python -m ai.training.train --config yolo11n_finetune.yaml --resume
python -m ai.training.train --config yolo11n_finetune.yaml \
    --resume /content/drive/MyDrive/DATN/runs/yolo11n_finetune/weights/last.pt
```

> **Bẫy đã được chặn:** resume một lần chạy **đã hoàn tất** khiến Ultralytics âm thầm khởi động
> một lần chạy mới trên **COCO** rồi ghi đè `best.pt` tốt bằng trọng số vô giá trị.
> `assert_resumable()` từ chối trường hợp này kèm hướng dẫn — xem mục 4.7.
> Muốn huấn luyện **lâu hơn** một lần chạy đã xong thì **không dùng `--resume`**; hãy tăng
> `epochs` trong cấu hình và chạy một lần mới với `--name` khác.

### 11.2. R-C2 — Hết hạn mức GPU của Colab

Tài khoản Colab miễn phí có hạn mức GPU **không công bố và thay đổi theo tải hệ thống**. Hết hạn
mức thì phiên bị hạ xuống CPU hoặc bị từ chối cấp GPU.

| Cách đối phó | Ghi chú |
|---|---|
| **Chia nhỏ lịch huấn luyện** | Chạy 30–40 epoch mỗi phiên rồi `--resume` ở phiên sau. Checkpoint trên Drive làm việc này thành chuyện thường ngày. |
| **Ưu tiên đúng thứ tự** | Chạy **E-A trước** (cấu hình sinh mô hình đem dùng). E-B (ablation) và E-C (leo thang) là nội dung *bổ sung* cho luận văn — nếu hết hạn mức thì mất chúng còn chấp nhận được, mất E-A thì không. |
| **Cân nhắc Colab Pro** | Nếu ngân sách cho phép; hạn mức cao hơn và ưu tiên cấp GPU tốt hơn. |
| **Ô 2 chặn phiên CPU** | Notebook **ném lỗi** thay vì để một lần chạy CPU nhiều giờ khởi động âm thầm — đây chính là biện pháp phòng khi Colab lặng lẽ cấp máy không GPU. |
| **Giảm quy mô chạy thử** | Dùng `--fraction` để thử nghiệm nhanh trước khi tiêu hạn mức cho lần chạy đầy đủ. |

### 11.3. R-C3 — GPU được cấp thay đổi giữa các phiên

Colab có thể cấp T4, hoặc L4, hoặc thứ khác. Batch size vừa với máy này có thể OOM trên máy kia.

* Đặt `batch: -1` để Ultralytics **AutoBatch** tự chọn theo VRAM thực tế.
* Hoặc giảm tay: 16 → 8 → 4.
* `train.py` bắt lỗi và trả về thông điệp nêu rõ ba nguyên nhân thường gặp, trong đó có OOM.
* **Cảnh báo phương pháp:** nếu đổi `batch` giữa các lần chạy thì các lần chạy đó **không còn so
  sánh trực tiếp được** với nhau. Phải ghi rõ khi báo cáo.

### 11.4. R-04 — Biển 2 dòng (rủi ro lớn nhất của dự án)

Không phải rủi ro hạ tầng, nhưng là rủi ro mà hạ tầng có nhiệm vụ **phát hiện sớm**.

| Biện pháp | Đã cài ở đâu |
|---|---|
| Bắt buộc báo cáo tách nhóm | `evaluate.py`, luôn in bảng NFR-A8 |
| Cảnh báo tự động khi khoảng cách > 10 điểm AP | `evaluate.py` |
| Khuyến nghị đúng hướng xử lý (cân bằng dataset, **không** leo thang mô hình) | Comment đầu tệp `yolo11s_escalation.yaml` |
| Ngưỡng phân nhóm trùng với tầng suy luận | `DEFAULT_AR_THRESHOLD = 2.5` = `InferenceConfig.two_line_aspect_ratio_threshold` |

### 11.5. R-C4 — Rủi ro vận hành khác

| Hiện tượng | Nguyên nhân và cách xử lý |
|---|---|
| `Dataset descriptor not found` | Chưa chạy đường ống dataset Phase 2, hoặc `data.yaml` sai đường dẫn. Truyền `--data` trỏ đúng tệp. |
| `fliplr must be 0.0` | Có người sửa YAML đặt `fliplr` khác 0. Đây là chặn **cố ý** — xem mục 4.5. |
| `Unknown configuration key(s)` | Gõ sai tên tham số trong YAML (ví dụ `epoch` thay vì `epochs`). Cố tình không bỏ qua âm thầm. |
| `close_mosaic cannot exceed epochs` | `close_mosaic` lớn hơn `epochs` thì mosaic không bao giờ bật. Khi ghi đè `--epochs` nhỏ, script tự kẹp lại và ghi cảnh báo. |
| Huấn luyện rất chậm, có banner cảnh báo CPU | Đang chạy trên CPU. Chuyển sang Colab GPU — mục 8.1. |
| Xuất ONNX/OpenVINO báo thiếu gói | `pip install onnx onnxruntime onnxslim openvino`. Một định dạng lỗi **không** làm hỏng các định dạng còn lại — `export.py` xử lý từng định dạng độc lập. |
| Cài `ai/requirements.txt` trên Colab làm mất CUDA | Tệp đó ghim torch **CPU-only** cho máy Windows. Ô 5 của notebook cố ý không dùng nó. |
| Epoch chậm bất thường trên Colab dù có GPU | Nhiều khả năng đang đọc dataset **thẳng từ Drive**. Ô 6 giải nén về đĩa VM đúng vì lý do này. |

---

## 12. Tài liệu liên quan

* [`docs/reports/01-yolo-comparison.md`](01-yolo-comparison.md) — căn cứ chọn YOLO11n (mục 2)
* [`docs/reports/01-dataset-survey.md`](01-dataset-survey.md) — khảo sát dataset, VNLP
* [`docs/reports/01-vn-plate-standards.md`](01-vn-plate-standards.md) — QCVN 08:2024/BCA
* [`docs/00-requirements/non-functional-requirements.md`](../00-requirements/non-functional-requirements.md) — NFR-A1…A9
* [`docs/00-requirements/environment.md`](../00-requirements/environment.md) — phần cứng thật, không có GPU CUDA
* [`docs/architecture/system-architecture.md`](../architecture/system-architecture.md) — AD-06 (thiết bị mặc định `cpu`)
* [`ai/training/README.md`](../../ai/training/README.md) — tài liệu vận hành chi tiết của hạ tầng

---

*Báo cáo lập ngày 19/07/2026, cập nhật 20/07/2026. **Mô hình chính thức `best.pt` đã huấn luyện
xong** (YOLO11n, `imgsz=640`, split v3, 20 epoch); bảng E-A ở mục 10 đã điền số đo thật từ tập
test v3. Các thí nghiệm bổ sung (E-B, E-C, E-D) chưa chạy, ô để trống có chủ ý.*
