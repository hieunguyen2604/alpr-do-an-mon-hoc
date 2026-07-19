# Huấn luyện mô hình phát hiện biển số (YOLO11)

Tài liệu này mô tả **hạ tầng huấn luyện** của Phase 3: cách chạy, ý nghĩa từng tham số,
cách đọc kết quả và cách xử lý khi phiên Colab bị ngắt.

> **Tình trạng hiện tại:** hạ tầng đã sẵn sàng và đã được chạy thử end-to-end trên một
> dataset tổng hợp nhỏ. **Chưa huấn luyện thật** — bước đó chờ dataset Phase 2 hoàn tất.

---

## 1. Tổng quan kiến trúc

```
ai/training/
├── config.py                       # TrainingConfig: nguồn chân lý duy nhất cho siêu tham số
├── configs/
│   ├── yolo11n_baseline.yaml       # huấn luyện từ đầu — mốc so sánh
│   ├── yolo11n_finetune.yaml       # tinh chỉnh từ COCO — CẤU HÌNH CHÍNH
│   └── yolo11s_escalation.yaml     # phương án leo thang nếu nano không đạt mAP
├── train.py                        # điểm vào huấn luyện
├── export.py                       # xuất ONNX / OpenVINO / TorchScript
└── README.md                       # tài liệu này

ai/evaluation/
├── evaluate.py                     # mAP/P/R/F1, PR, ma trận nhầm lẫn, TÁCH 1 dòng/2 dòng
└── benchmark_cpu.py                # đo tốc độ PyTorch vs ONNX vs OpenVINO trên máy này

notebooks/train_colab.ipynb         # trình thực thi trên Colab GPU (không chứa logic)
```

**Nguyên tắc bất di bất dịch:** notebook chỉ *gọi* các script trên. Không có logic huấn luyện
nào nằm trong một ô notebook. Nhờ vậy kết quả chạy trên Colab và chạy cục bộ là như nhau, và
mọi thay đổi tham số đều nằm trong Git chứ không trôi mất theo một phiên trình duyệt.

---

## 2. Chạy nhanh

### 2.1. Trên Colab GPU (khuyến nghị)

Mở `notebooks/train_colab.ipynb`, bật GPU trong `Runtime → Change runtime type`,
rồi chạy lần lượt các ô từ 1 đến 10. Hướng dẫn chi tiết nằm ngay trong ô 1 của notebook.

### 2.2. Dưới máy cục bộ (CPU — rất chậm)

```bash
# Kiểm tra cấu hình mà không huấn luyện
D:/DATN/.venv-ai/Scripts/python.exe -m ai.training.train \
    --config yolo11n_finetune.yaml --print-config

# Chạy thử đường ống (vài phút, kết quả vô nghĩa nhưng chứng minh mọi thứ chạy được)
D:/DATN/.venv-ai/Scripts/python.exe -m ai.training.train \
    --config yolo11n_finetune.yaml \
    --device cpu --epochs 1 --fraction 0.01 --batch 2 --name smoke_test
```

> ⚠️ **Không huấn luyện thật trên CPU.** Máy này (Intel Core i5-14600K, 14 nhân vật lý,
> không có GPU CUDA) sẽ mất nhiều giờ cho **một** epoch trên ~37.000 ảnh. Script sẽ in cảnh
> báo `CANH BAO: dang huan luyen tren CPU, se rat cham.` khi phát hiện tình huống này.
> CPU chỉ dùng để *suy luận* và *đo tốc độ*, đúng như quyết định kiến trúc AD-06.

Lệnh phải chạy từ thư mục gốc `D:/DATN` (hoặc đặt `PYTHONPATH=D:/DATN`) để `python -m ai...`
tìm được gói.

---

## 3. Ba tệp cấu hình và cách chọn

| Tệp | Khởi tạo trọng số | Epoch | Dùng khi nào |
|---|---|---|---|
| `yolo11n_baseline.yaml` | ngẫu nhiên (từ đầu) | 150 | Làm **mốc so sánh** cho luận văn |
| `yolo11n_finetune.yaml` | `yolo11n.pt` (COCO) | 100 | **Cấu hình chính** — sinh ra mô hình đem dùng |
| `yolo11s_escalation.yaml` | `yolo11s.pt` (COCO) | 100 | Chỉ khi nano **không đạt** mục tiêu mAP |

**Quy trình quyết định đúng:**

1. Chạy `yolo11n_finetune.yaml`.
2. Đánh giá bằng `ai/evaluation/evaluate.py`, **bắt buộc xem bảng tách riêng 1 dòng / 2 dòng**.
3. Nếu mAP@0.5 đạt mục tiêu trên **cả hai** loại biển → chốt YOLO11n, dừng.
4. Chỉ khi không đạt → chạy `yolo11s_escalation.yaml`.

> YOLO11s có khoảng gấp 3 tham số và gấp ~3 độ trễ CPU so với YOLO11n. Trên máy không có GPU,
> chi phí đó phải trả ở **mọi** lần suy luận, mãi mãi. Trước khi leo thang, hãy xem nano **hỏng
> ở đâu**: nếu điểm yếu là biển 2 dòng (khả năng cao — rủi ro R-04) thì cân bằng lại dataset
> thường hiệu quả hơn nhiều so với tăng số tham số.

Chạy `yolo11n_baseline.yaml` và `yolo11n_finetune.yaml` trên **cùng một** phân chia dữ liệu:
khoảng cách mAP giữa hai lần chạy **chính là** giá trị đo được của transfer learning — một
bảng số đẹp cho chương thực nghiệm.

---

## 4. Ý nghĩa các tham số quan trọng

Toàn bộ tham số được định nghĩa và kiểm tra hợp lệ trong `ai/training/config.py`
(lớp `TrainingConfig`). Mỗi tệp YAML đều có comment tiếng Anh giải thích tại chỗ.

### 4.1. Lịch huấn luyện

| Tham số | Mặc định | Ý nghĩa |
|---|---|---|
| `imgsz` | 640 | Kích thước ảnh vuông khi huấn luyện. Biển số là **vật thể nhỏ**; giảm giá trị này là thứ đầu tiên làm tụt recall. Giữ nguyên giữa các cấu hình để so sánh công bằng. |
| `epochs` | 100 (finetune) / 150 (baseline) | Số epoch tối đa. Từ đầu cần lịch dài hơn tinh chỉnh. |
| `batch` | 16 | Số ảnh mỗi lô. Đặt `-1` để Ultralytics tự chọn theo VRAM (hữu ích khi Colab cấp GPU khác nhau mỗi phiên). |
| `patience` | 20 | Dừng sớm sau bằng ấy epoch không cải thiện. |

### 4.2. Bộ tối ưu

| Tham số | Mặc định | Ý nghĩa |
|---|---|---|
| `optimizer` | `AdamW` | Dễ tính hơn SGD trên dataset cỡ vừa, ít phải dò learning rate. |
| `lr0` | 0.001 (finetune) | **Cố tình thấp.** LR cao trên trọng số đã pretrain gây *catastrophic forgetting*: đặc trưng COCO hữu ích bị phá trong vài trăm bước đầu, kết quả còn tệ hơn huấn luyện từ đầu. |
| `lrf` | 0.01 | LR cuối = `lr0 × lrf`. |
| `warmup_epochs` | 3 (finetune) / 5 (baseline) | Khởi động tuyến tính. Trọng số ngẫu nhiên sinh gradient lớn và nhiễu nên cần dài hơn. |
| `cos_lr` | `true` khi tinh chỉnh | Suy giảm cosine, mượt hơn ở giai đoạn cuối. |
| `weight_decay` | 0.0005 | Điều chuẩn L2. YOLO11s dùng 0.001 vì nhiều tham số hơn trên cùng lượng dữ liệu. |

### 4.3. Trọng số hàm mất mát

| Tham số | Mặc định | Ý nghĩa |
|---|---|---|
| `box` | **8.0** | Nâng lên so với mặc định 7.5 của Ultralytics. Lý do đặc thù của dự án: đầu ra của detector được **một mô hình khác** (OCR) tiêu thụ, không phải con người. Hộp lệch → ảnh cắt xấu → OCR đọc sai. Chất lượng định vị quan trọng hơn bài toán phát hiện thông thường. |
| `cls` | 0.5 | Thấp — detector có rất ít lớp, phân loại là phần dễ. |
| `dfl` | 1.5 | Mặc định. |

### 4.4. Tăng cường dữ liệu (augmentation)

| Tham số | Mặc định | Ý nghĩa |
|---|---|---|
| `fliplr` | **0.0 — BẮT BUỘC** | Lật ngang làm **soi gương các ký tự in trên biển**. Đó không phải một phép quay của biển thật mà là một vật thể *không tồn tại*. Mô hình sẽ học biển gương và mọi chính sách augmentation tái sử dụng cho OCR sẽ bị hỏng theo. `TrainingConfig` **ném `ValueError`** nếu giá trị khác 0. |
| `flipud` | **0.0 — BẮT BUỘC** | Biển lộn ngược không xuất hiện trong bài toán triển khai. Cũng bị chặn cứng. |
| `hsv_h` | 0.015 | Nhiễu sắc độ **rất nhỏ**. Màu nền biển ở Việt Nam **mang ngữ nghĩa** (trắng / vàng / xanh / đỏ mã hóa loại phương tiện). Xáo trộn sắc độ là phá một tín hiệu thật. |
| `hsv_v` | 0.4 | Nhiễu độ sáng rộng tay: ảnh ban đêm, chói đèn pha, biển ngược sáng. |
| `degrees` | 5.0 | Xoay nhỏ. Biển thật gần như luôn nằm ngang trên xe; xoay lớn dạy mô hình những tư thế không tồn tại. |
| `perspective` | 0.0005 | Biến dạng phối cảnh nhẹ — camera cổng/bãi xe hầu như luôn chụp lệch trục. |
| `erasing` | 0.4 | Xóa ngẫu nhiên — biển hay bị che bởi bùn, giá đỡ, móc kéo. |
| `mosaic` | 1.0 | Augmentation hiệu quả nhất cho vật thể nhỏ. |
| `close_mosaic` | 10–15 | Tắt mosaic ở bằng ấy epoch cuối để mô hình kết thúc trên ảnh không biến dạng. |
| `mixup` | 0.0 | Trộn hai ảnh tạo ra chữ trên biển **không đọc được** và không mang tín hiệu phát hiện hữu ích. |

### 4.5. Vận hành và tái lập

| Tham số | Mặc định | Ý nghĩa |
|---|---|---|
| `seed` | **42** | Cố định để **tái lập được**. Một con số trong luận văn mà không chạy lại ra được thì không có mấy giá trị. |
| `deterministic` | `true` | Ép nhân tất định. Chậm hơn một chút, đổi lấy khả năng tái lập. |
| `save_period` | **10** | Lưu checkpoint đánh số mỗi 10 epoch. **Không phải tùy chọn trang trí** — Colab thu hồi phiên không báo trước. |
| `device` | `auto` | `auto` → CUDA nếu có, rồi MPS, cuối cùng CPU. |
| `workers` | 8 | Tiến trình nạp dữ liệu. Trên Windows nên để vừa phải. |
| `project` / `name` | `runs` / tên cấu hình | Thư mục kết quả là `<project>/<name>`. Trên Colab hãy trỏ `--project` vào Google Drive. |

---

## 5. Tham số dòng lệnh của `train.py`

```
--config           (bắt buộc) tệp YAML; chỉ cần tên tệp là tìm trong ai/training/configs/
--resume [PATH]    huấn luyện tiếp; không có PATH thì tự tìm last.pt mới nhất
--device           auto | cpu | 0 | 0,1 | mps
--epochs           ghi đè số epoch
--batch            ghi đè kích thước lô
--imgsz            ghi đè kích thước ảnh (bội số của 32)
--workers          ghi đè số tiến trình nạp dữ liệu
--data             ghi đè đường dẫn data.yaml
--name / --project ghi đè thư mục kết quả
--fraction         ghi đè tỷ lệ tập huấn luyện được dùng
--models-dir       nơi công bố best.pt (mặc định: D:/DATN/models)
--log-dir          nơi ghi tệp log (mặc định: D:/DATN/logs/training)
--print-config     in cấu hình hiệu lực rồi thoát, không huấn luyện
--quiet            log mức INFO thay vì DEBUG
```

Mọi giá trị ghi đè đều được **kiểm tra lại** qua `TrainingConfig`, nên tham số sai bị từ chối
ngay lập tức chứ không đợi đến giữa lần chạy.

---

## 6. Khi Colab ngắt phiên

Đây là chuyện **bình thường**, hạ tầng đã tính trước.

**Chuẩn bị (làm từ đầu, không phải sau khi mất):**

* Ô 3 của notebook gắn Google Drive.
* Ô 7 truyền `--project` trỏ **thẳng vào Drive** → mọi checkpoint nằm ngoài máy ảo.
* `save_period: 10` giữ checkpoint đánh số; `last.pt` được ghi **mỗi epoch**.

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

### ⚠️ Chốt an toàn quan trọng khi resume

Ultralytics có một hành vi **nguy hiểm và im lặng**: nếu bạn gọi `train(resume=True)` trên một
checkpoint mà lần chạy của nó **đã hoàn tất**, nó **không báo lỗi** — nó âm thầm bỏ yêu cầu
resume và bắt đầu một lần chạy **hoàn toàn mới với tham số mặc định**, tức là huấn luyện trên
**COCO** chứ không phải biển số của bạn. Lần chạy đó trông rất bình thường, kết thúc bình
thường, rồi **ghi đè** `best.pt` tốt của bạn bằng trọng số vô giá trị.

Lỗi này đã được phát hiện khi chạy thử hạ tầng và `train.py` nay chặn nó: hàm `assert_resumable()`
đọc chỉ số epoch trong checkpoint và **từ chối** resume một lần chạy đã hoàn tất, kèm hướng dẫn
xử lý. Ngoài ra sau khi huấn luyện còn một lớp kiểm tra nữa, đối chiếu dataset mà Ultralytics
thực sự đã dùng với dataset được yêu cầu.

Nếu bạn muốn huấn luyện **lâu hơn** một lần chạy đã xong thì không dùng `--resume`, mà hãy tăng
`epochs` trong cấu hình và chạy một lần mới với `--name` khác.

Thêm một lớp bảo vệ nữa: khi công bố `best.pt`, nếu đã tồn tại tệp cũ thì tệp cũ được **đổi tên
kèm dấu thời gian** chứ không bị ghi đè — mất một mô hình đã huấn luyện tốt vì một lần chạy tệ
hơn là sai lầm đắt và rất khó nhận ra.

---

## 7. Đọc kết quả

Sau khi chạy xong, thư mục `<project>/<name>/` chứa:

| Tệp | Nội dung |
|---|---|
| `weights/best.pt` | Trọng số tốt nhất (theo fitness trên tập val) — **sản phẩm bàn giao** |
| `weights/last.pt` | Trọng số epoch cuối — dùng để `--resume` |
| `weights/epoch*.pt` | Checkpoint định kỳ theo `save_period` |
| `results.csv` / `results.png` | Loss và mAP theo từng epoch |
| `confusion_matrix.png` | Ma trận nhầm lẫn do Ultralytics sinh |
| `PR_curve.png`, `F1_curve.png` | Đường cong precision-recall và F1 |
| `labels.jpg` | Phân bố nhãn — kiểm tra nhanh dataset có lệch không |
| `args.yaml` | Tham số Ultralytics đã dùng |
| `training_config.yaml` | **Bản chụp `TrainingConfig`**, nạp lại được bằng `from_yaml()` |

`best.pt` được tự động chép về `models/best.pt` — đúng đường dẫn mà tầng suy luận nạp mặc định
(`ALPR_MODEL_PATH`).

### Cách đọc `results.png`

* `train/box_loss`, `train/cls_loss`, `train/dfl_loss` phải **giảm đều**. Đi ngang từ sớm →
  learning rate quá thấp; nhảy loạn → quá cao.
* `metrics/mAP50` phải **tăng rồi bão hòa**. Nếu mAP val bắt đầu **giảm** trong khi loss train
  vẫn giảm → **quá khớp**; `patience` sẽ dừng sớm.
* Khoảng cách lớn giữa loss train và val → quá khớp; cân nhắc tăng dữ liệu hoặc `weight_decay`.

---

## 8. Đánh giá và xuất mô hình

```bash
# Đánh giá trên tập test (có tách riêng biển 1 dòng / 2 dòng — NFR-A8)
python -m ai.evaluation.evaluate --weights models/best.pt --split test --device cpu

# Xuất sang các định dạng chạy CPU
python -m ai.training.export --weights models/best.pt --format all --imgsz 640

# Đo tốc độ thật trên máy này
python -m ai.evaluation.benchmark_cpu --weights models/best.pt \
    --images datasets/processed/test/images
```

`evaluate.py` ghi báo cáo JSON vào `docs/reports/` và biểu đồ PNG vào `docs/reports/figures/`.

**Con số cần nhìn trước tiên** không phải mAP tổng, mà là bảng tách theo số dòng:

```
GROUP            N_GT     TP     FP     FN        P        R       F1    mAP50  mAP50-95
single_line      ...
two_line         ...
ALL              ...
NFR-A8 gap (single-line AP@0.5 minus two-line AP@0.5): +0.xxxx
```

Biển 2 dòng là **rủi ro kỹ thuật lớn nhất** của dự án (R-04): trên bộ dữ liệu **RodoSol-ALPR
của Brazil**, OpenALPR đạt 94,3% trên biển ô tô 1 dòng nhưng chỉ 45,7% trên biển xe máy 2 dòng
(Laroca và cộng sự, VISAPP 2022). Đây là **số liệu Brazil, không phải số liệu Việt Nam**, chỉ
được dẫn như một *analogue* định lượng. Một con số mAP tổng che giấu **đúng** thất bại
đó — mô hình có thể trông khỏe mạnh trong khi vô dụng với một nửa số phương tiện ở Việt Nam.
Nếu khoảng cách vượt 10 điểm AP, script sẽ cảnh báo và khuyến nghị **cân bằng lại dataset**
trước khi nghĩ đến việc dùng mô hình lớn hơn.

Cách phân nhóm 1 dòng / 2 dòng, theo thứ tự ưu tiên:

1. Cột `line_count` (cột thứ 6) trong tệp nhãn, nếu có.
2. Tên lớp có mang thông tin bố cục (`plate_1line` / `plate_2line`, …).
3. Nếu không có gì → **tỷ lệ khung hình**, theo QCVN 08:2024/BCA:

   | Loại biển | Kích thước | Tỷ lệ | Số dòng |
   |---|---|---|---|
   | Ô tô, biển dài | 520 × 110 mm | 4,727 | 1 |
   | Ô tô, biển ngắn | 330 × 165 mm | 2,000 | 2 |
   | Mô tô, xe máy | 190 × 140 mm | 1,357 | 2 |

   Hai nhóm tách nhau rõ (2,000 so với 4,727) nên ngưỡng 2,5 phân loại ổn định ngay cả khi hộp
   không hoàn hảo. Ngưỡng này **trùng** với `InferenceConfig.two_line_aspect_ratio_threshold`
   để độ chính xác báo cáo mô tả đúng hệ thống được triển khai.

Nếu **toàn bộ** hộp bị phân nhóm bằng suy đoán tỷ lệ, script sẽ cảnh báo — và bản báo cáo phải
nói rõ điều đó.

---

## 9. Số liệu tốc độ CPU

`benchmark_cpu.py` in kèm tên CPU, số nhân vật lý/luận lý, RAM và số luồng PyTorch.

> **Bắt buộc:** luận văn chỉ được trích số CPU do **chính script này đo trên máy này**.
> Phase 1 đã cảnh báo không được trích số CPU của người khác. Con số ~3,7 lần trong báo cáo
> Phase 1 là số **tham khảo từ nguồn ngoài**, phải thay bằng số đo thật.

Kết quả chạy thử hạ tầng (mô hình tổng hợp, `imgsz=320`, batch = 1,
Intel Core i5-14600K — 14 nhân vật lý / 20 luồng):

| Backend | Trung bình | p50 | p95 | Tăng tốc |
|---|---|---|---|---|
| PyTorch | 14,53 ms | 13,70 ms | 17,79 ms | 1,00× |
| ONNX Runtime | 6,18 ms | 6,05 ms | 6,59 ms | **2,35×** |
| OpenVINO | 10,67 ms | 9,93 ms | 14,06 ms | 1,36× |

> Đây **chỉ là số kiểm chứng hạ tầng**, không phải kết quả dùng được: mô hình chưa huấn luyện
> thật và `imgsz=320` thay vì 640. Phải đo lại với mô hình thật, `imgsz=640` và ảnh test thật
> rồi mới đưa vào luận văn.

---

## 10. Xử lý sự cố

| Hiện tượng | Nguyên nhân và cách xử lý |
|---|---|
| `Dataset descriptor not found` | Chưa chạy đường ống dataset Phase 2, hoặc `data.yaml` sai đường dẫn. Truyền `--data` trỏ đúng tệp. |
| `fliplr must be 0.0` | Có người sửa YAML đặt `fliplr` khác 0. Đây là chặn **cố ý** — xem mục 4.4. |
| `Unknown configuration key(s)` | Gõ sai tên tham số trong YAML (ví dụ `epoch` thay vì `epochs`). Cố tình không bỏ qua âm thầm. |
| CUDA out of memory | Giảm `batch` (16 → 8 → 4), hoặc đặt `batch: -1` để Ultralytics tự chọn. |
| `close_mosaic cannot exceed epochs` | `close_mosaic` lớn hơn `epochs` thì mosaic không bao giờ bật. Khi ghi đè `--epochs` nhỏ, script tự kẹp lại và ghi cảnh báo. |
| Huấn luyện rất chậm, có cảnh báo CPU | Đang chạy trên CPU. Chuyển sang Colab GPU — xem mục 2.1. |
| Resume không tiếp tục mà chạy lại từ đầu | Xem mục 6 — lần chạy đó đã hoàn tất; `train.py` sẽ chặn và hướng dẫn. |
| Xuất ONNX/OpenVINO báo thiếu gói | `pip install onnx onnxruntime onnxslim openvino`. Ultralytics thường tự cài khi cần. |

---

## 11. Tài liệu liên quan

* [`docs/reports/01-yolo-comparison.md`](../../docs/reports/01-yolo-comparison.md) — căn cứ chọn YOLO11n
* [`docs/reports/01-dataset-survey.md`](../../docs/reports/01-dataset-survey.md) — khảo sát dataset
* [`docs/reports/01-vn-plate-standards.md`](../../docs/reports/01-vn-plate-standards.md) — QCVN 08:2024/BCA
* [`docs/00-requirements/environment.md`](../../docs/00-requirements/environment.md) — môi trường và quyết định AD-06
* [`ai/inference/README.md`](../inference/README.md) — tầng suy luận tiêu thụ `models/best.pt`
