# Thư mục mô hình

## Tình trạng hiện tại

> ✅ **MÔ HÌNH CHÍNH THỨC `best.pt` ĐÃ CÓ VÀ ĐANG CHẠY.** `best.pt` (YOLO11n, 2.590.035 tham số, `imgsz=640`, split v3, 20 epoch) đã huấn luyện xong và là mô hình hệ thống đang nạp. `GET /health` trả về **`model_loaded: true`**, trường `engine` là `yolo:best.pt+paddleocr-PP-OCRv5-mobile`.
>
> `StubPipeline` **đã bị đưa ra khỏi đường chạy chính**. Phương án lùi khi thiếu trọng số hiện là `UnavailablePipeline` — nó **ném lỗi** thay vì bịa ra biển số. Stub chỉ chạy khi đặt tường minh `ALPR_USE_STUB=true`.
>
> Kết quả detection thật của `best.pt` trên tập test v3 (1.514 ảnh): **mAP@0.5 = 0,9829 · mAP@0.5:0.95 = 0,7834 · Precision = 0,9837 · Recall = 0,9714** — đều đạt chỉ tiêu. Nguồn: 05-tables.md §T5.5a *(nhánh `main`)*.
>
> ⚠️ **`baseline-416-v1.pt` giờ là mô hình ĐỐI CHỨNG**, không phải mô hình đưa vào quyển đồ án — nó có hai khiếm khuyết đã biết, đọc mục ngay dưới.

| Đường dẫn | Là gì | Dùng để làm gì |
|---|---|---|
| `pretrained/yolo11n-coco.pt` | YOLO11n gốc của Ultralytics, huấn luyện trên COCO (80 lớp) | **Điểm khởi đầu transfer learning** |
| `best.pt` | ✅ **Mô hình chính thức** — YOLO11n, `imgsz=640`, split v3 đã khử trùng lặp ở ngưỡng 10, 20 epoch | **Model hệ thống đang chạy và là nguồn mọi số liệu công bố** |
| `best.onnx` | Bản xuất ONNX Runtime của `best.pt` | Đo được **24,48 ms** (1,35× so PyTorch), mAP không giảm |
| `best_openvino_model/` | Bản xuất OpenVINO IR của `best.pt` | **Nhanh nhất trên máy này: 21,12 ms (1,57×)**, mAP không giảm. Bật bằng `ALPR_MODEL_PATH` |
| `baseline-416-v1.pt` | ⚠️ **Baseline đối chứng** — 40 epoch, `imgsz=416`, split v1 | **Chỉ để đối chứng.** **Có hai khiếm khuyết đã biết** — đọc mục dưới |
| `baseline-416-v1.results.csv` | Log chỉ số theo từng epoch của lượt baseline | Nguồn số liệu cho biểu đồ huấn luyện của baseline |

**Cấu hình mặc định trỏ tới `best.pt`:**

```
ALPR_MODEL_PATH=models/best.pt
```

`build_pipeline` nạp `best.pt`, `/health` báo `model_loaded: true` và `engine` chứa `yolo:best.pt`. Nếu muốn chạy đối chứng trên baseline thì trỏ tường minh `ALPR_MODEL_PATH=models/baseline-416-v1.pt`.

---

## ⚠️ `baseline-416-v1.pt` — hai khiếm khuyết phải nêu khi báo cáo

Kết quả huấn luyện (epoch tốt nhất = 38 / 40, tổng 156 phút trên CPU):

| Chỉ số | Giá trị |
|---|---:|
| mAP@0.5 | 0,9933 |
| mAP@0.5:0.95 | 0,8597 |
| Precision | 0,9822 |
| Recall | 0,9810 |

Nhìn qua thì vượt xa chỉ tiêu NFR-A1 (≥ 0,90) và NFR-A2 (≥ 0,65). **Nhưng không được báo cáo là "đạt"**, vì hai lý do độc lập nhau:

**1. `imgsz` = 416, trong khi chỉ tiêu đặt ở 640.** Không so sánh trực tiếp được. Chi tiết: 03-training-setup.md §9.1 *(nhánh `main`)*.

**2. Tập test có rò rỉ thật.** Đo ở ngưỡng phash 10 — dải mà bộ chia tách *không* bảo vệ — tìm thấy **619 cặp ảnh gần trùng giữa train và test** trên bộ v1. Kiểm tra bằng mắt: cùng một chiếc xe, cùng chuỗi biển số, xuất hiện ở cả hai split. Nghĩa là mAP 0,9933 **lạc quan hơn hiệu năng thật**.

> Kết quả 0 cặp ở ngưỡng 5 mà bản trước từng dùng làm bằng chứng là **lập luận vòng tròn**: pipeline gom nhóm ở ngưỡng 5 rồi đo lại cũng ở ngưỡng 5. Chi tiết phân tích: 07-testing-report.md §6 *(nhánh `main`)*.

**Vì vậy `baseline-416-v1.pt` chỉ dùng để hệ thống chạy được và để đối chứng.** Nó **không phải** mô hình đưa vào quyển đồ án.

---

## Đọc kỹ: `yolo11n-coco.pt` KHÔNG phát hiện được biển số

Đây là điểm rất dễ hiểu nhầm. File này có **80 lớp của COCO** — `person`, `bicycle`, `car`, `motorcycle`, `bus`, `truck`… — và **không có lớp nào là biển số xe**. Đã kiểm chứng bằng cách nạp thật:

```python
from ultralytics import YOLO
m = YOLO("models/pretrained/yolo11n-coco.pt")
len(m.names)                                    # 80
[v for v in m.names.values() if "plate" in v]   # []  -> không có
```

Nó nằm ở đây **chỉ để làm trọng số khởi tạo** khi fine-tune sang bài toán 1 lớp (`license_plate`). Nạp nó rồi kỳ vọng ra bounding box biển số là sai.

Đây cũng là lý do file được đặt ở `pretrained/` chứ không phải `interim/`: tên `interim` gợi ý "model tạm đang dùng được", trong khi thực tế nó **chưa dùng được cho bài toán này**.

---

## Nguồn gốc mô hình — quyết định đã chốt

*(Mục này ghi lại một quyết định đã thực hiện xong, giữ lại vì nó là căn cứ phải nêu trong quyển đồ án.)*

Kế hoạch ban đầu có cân nhắc việc tải một mô hình phát hiện biển số đã huấn luyện sẵn từ HuggingFace/GitHub để Phase 4–7 có cái chạy thật. **Phương án đó đã bị loại**, vì hai lý do:

1. **Rủi ro bảo mật.** Tệp `.pt` của PyTorch là **pickle**. Nạp một file `.pt` tải từ kho bất kỳ trên Internet đồng nghĩa với **thực thi mã tuỳ ý** trên máy — không phải chỉ đọc dữ liệu.
2. **Ràng buộc học thuật.** Mọi số liệu công bố phải đo trên mô hình do đồ án tự huấn luyện (xem mục cuối trang này).

**Quyết định đã chọn và đã thực hiện: tự huấn luyện.** `baseline-416-v1.pt` là kết quả của lượt huấn luyện đầu tiên trên bộ dữ liệu của đồ án; `best.pt` là lượt chính thức (đã hoàn tất, đang chạy). Không có trọng số bên thứ ba nào nằm trên đường chạy chính ngoài `pretrained/yolo11n-coco.pt` — và file đó chỉ dùng làm điểm khởi tạo transfer learning, không tự phát hiện được biển số.

---

## Tối ưu hiệu năng — bản xuất nào đáng dùng

Kho có hai bản xuất, **cả hai sinh từ `best.pt`**: `best.onnx` và `best_openvino_model/`.
Sáu bản xuất cũ dưới `checkpoints/exported/` sinh từ checkpoint giữa chừng của lượt
baseline **đã bị xoá** — mọi số đo trên chúng đã bị bác bỏ.

Đo ngày 13/08/2026 trên 50 ảnh thật: PyTorch **33,09 ms** · ONNX Runtime **24,48 ms**
(1,35×) · OpenVINO **21,12 ms** (1,57×), và mAP **không suy giảm** sau khi xuất.
Bản giao hàng **vẫn giữ `best.pt`** vì NFR-P1 và NFR-P2 đều đạt mà không cần đổi;
muốn bật thì đổi `ALPR_MODEL_PATH`. Chi tiết: báo cáo 38 *(nhánh `main`)*.

Đo lại phân rã độ trễ trên `best.pt` (nguồn: 05-tables.md §T5.7b *(nhánh `main`)*): **PaddleOCR chiếm ~64,3% tổng độ trễ (~112,55 ms/biển)**, detector YOLO11n chiếm **~34,2% (~59,83 ms)**. Độ trễ E2E p95 đo được là **780,36 ms in-process** và **731,15 ms client-side qua HTTP** (07-benchmark-p1-resolved.json *(nhánh `main`)*) — **đạt mục tiêu NFR-P1 (≤ 800 ms)** và thoả cả ngưỡng tối thiểu 1.500 ms.

> Con số cũ "PaddleOCR chiếm 93,3%, p95 = 5.857,19 ms" **đã bị bác bỏ**: nó đo trên checkpoint `best-cpu-epoch7.pt` (không phải `best.pt`) trong khi một tiến trình huấn luyện chiếm ~793% CPU song song, cộng thêm lỗi crop khiến OCR đọc trên ảnh crop quá lớn (~1322 ms/ảnh). Đo lại trên `best.pt` với máy rảnh: p95 chỉ còn ~731–780 ms. Vì OCR (64,3%) không còn áp đảo tuyệt đối, tối ưu detector (34,2%) giờ mới có ý nghĩa thực sự.

---

## Lượt huấn luyện chính thức — ĐÃ HOÀN TẤT

1. ✅ `best.pt` đã nằm ở `models/best.pt`
2. ✅ Cấu hình mặc định `ALPR_MODEL_PATH=models/best.pt`
3. ✅ `GET /health` báo `model_loaded: true`, `engine` chứa `yolo:best.pt`
4. ✅ Đã chạy `ai/evaluation/evaluate.py`, số liệu detection nằm ở 05-tables.md §T5.5a *(nhánh `main`)*
5. ✅ Số liệu hiệu năng (P1, breakdown) đã đo lại trên `best.pt` — xem 05-tables.md §T5.7 *(nhánh `main`)* và 07-benchmark-p1-resolved.json *(nhánh `main`)*. Các NFR hiệu năng khác (P4–P7, R4, SC1) vẫn ghi số đo trên baseline và được đánh dấu rõ *(baseline)* trong bảng.

---

## ⚠️ Quy tắc bắt buộc khi viết quyển đồ án

**Mọi số liệu công bố trong quyển đồ án phải đo trên mô hình do đồ án tự huấn luyện.**

Tuyệt đối không được báo cáo số của mô hình tải sẵn — dù là `yolo11n-coco.pt` hay bất kỳ model bên thứ ba nào — như thể là kết quả của đồ án. Nếu có dùng model bên ngoài để so sánh đối chứng, phải ghi rõ nguồn, giấy phép và nêu tách bạch khỏi kết quả của đồ án.
