# Thư mục dữ liệu đã xử lý

> ## ⚠️ ĐỌC TRƯỚC: `yolo_v2`, `yolo_v3` **KHÔNG** phải YOLOv2 / YOLOv3
>
> Đây là **tên phiên bản BỘ DỮ LIỆU**, không phải tên kiến trúc mô hình.
>
> * `yolo` trong tên = **định dạng nhãn YOLO** (`class x_center y_center width height`, toạ độ chuẩn hoá) — phân biệt với định dạng COCO JSON hay Pascal VOC XML.
> * `_v2`, `_v3` = **lần dựng bộ dữ liệu thứ 2, thứ 3**.
>
> **Mô hình của đồ án là YOLO11n** — xuyên suốt, không có ngoại lệ. Kiểm chứng được bằng ba cách:
>
> | Cách kiểm | Kết quả |
> |---|---|
> | `runs/*/args.yaml` | `model: yolo11n.pt` |
> | Log huấn luyện | `Vietnamese ALPR -- YOLO11 detector training` |
> | Đếm tham số | **2.590.035** ≈ 2,6 M (YOLO11n) |
>
> Để so sánh: **YOLOv3 có ~61,9 M tham số — gấp 24 lần**. Hai thứ này không thể nhầm với nhau về mặt số liệu.
>
> Căn cứ chọn YOLO11: [docs/reports/01-yolo-comparison.md](../../docs/reports/01-yolo-comparison.md).

---

## Các phiên bản bộ dữ liệu

| Thư mục | Ảnh | Nguồn | Ngưỡng gom | Tình trạng |
|---|---:|---|:---:|---|
| `yolo/` | 4.578 | 1 (HuggingFace) | 5 | ⚠️ Bộ v1 — **có rò rỉ** train↔test (619 cặp ở d≤10) |
| `merged/` | — | — | — | Trung gian của v1, không dùng trực tiếp |
| `merged_v2/` | 15.133 | 6 nguyên tố (7 bộ vào hợp nhất) | 5 | Trung gian của v2 sau khử trùng chéo |
| `yolo_v2/` | 15.133 | 6 nguyên tố (7 bộ vào hợp nhất) | 5 | ⚠️ **Có rò rỉ** (2.699 cặp train↔test ở d≤10) |
| **`yolo_v3/`** | **15.133** | **6 nguyên tố** (7 bộ vào hợp nhất) | **10** | ✅ **Bộ đang dùng** để huấn luyện mô hình chính thức |

> **Ba con số nguồn, ba ngữ cảnh — không được lẫn.** **9 bộ đã tải về** (`datasets/raw/`, khâu thu
> thập) → **7 bộ vào bước hợp nhất detection** (2 bộ nhãn mức ký tự `roboflow_ocr_plate` và
> `roboflow_ocr_conversion` tách riêng phục vụ đánh giá OCR; tổng 27.111 ảnh) → **6 nguồn nguyên tố**
> trong tập cuối. Bộ thứ 7 — `roboflow_tran_ngoc_xuan_tin` (1.005 ảnh) — bị khử trùng lặp chéo bộ
> loại **100% (1.005/1.005)** nên không còn xuất hiện trong `split_manifest.csv`. Chi tiết: mục 5.3.1
> của [`docs/reports/02-dataset-report.md`](../../docs/reports/02-dataset-report.md).

### Vì sao v3 dùng ngưỡng 10 chứ không phải 12

Ban đầu kế hoạch là gom ở ngưỡng 12 cho "an toàn hơn". Kiểm tra bằng mắt 25 cặp ảnh cho thấy giả định đó **sai**.

Corpus này bị thống trị bởi **camera cố định** (barrier bãi xe, camera giao thông). `phash` tóm tắt **bố cục toàn khung ảnh** — bức tường, gờ giảm tốc, góc nhìn — chứ không tóm tắt chiếc xe hay tấm biển. Hệ quả: hai khung hình của **hai xe khác nhau** qua **cùng một camera** lại rất gần nhau về phash.

Bằng chứng trực quan: [`../reports/v3/corpus_samples/flagged_pair.png`](../reports/v3/corpus_samples/flagged_pair.png) — cặp ảnh d=10 từng bị báo cáo nhầm là "cùng một tấm ảnh ở hai bộ dữ liệu", thực tế là **Toyota Land Cruiser `52Y-6490`** và **Toyota Hiace `51F-220.29`**, hai xe khác nhau qua cùng một barrier.

Nâng ngưỡng lên 12 **không bắt thêm trùng lặp thật nào**, mà chỉ nối chuỗi các cạnh giả qua union-find cho đến khi **54,6% corpus dính thành một cụm** — tức gom theo *camera*, không phải chống rò rỉ.

Ngưỡng 10 là giá trị cao nhất còn xác nhận được trùng lặp **thật** bằng mắt: biển `59-L2 237.14`, cùng một xe máy, xuất hiện ở **cả** `hf_vn_plates_segment` lẫn `roboflow_school_fuhih`.

### Giới hạn còn lại — nêu rõ, không giấu

1. **Còn rò rỉ tồn dư mà phash không khử được.** Ví dụ: biển `51F-155.85`, cùng một chiếc Hyundai trắng, vào cùng barrier vào hai ngày khác nhau, hiện nằm ở hai split. phash không phân biệt được ca này với "xe lạ trong cùng khung cảnh" — chỉ gom theo **chuỗi biển số** mới khử được, mà corpus detection này không có nhãn biển số.
2. **Chi phí của ngưỡng 10:** một cụm 4.411 ảnh rơi cả vào `train`, chiếm 41,6% tập train ⇒ **lệch tỉ trọng nguồn** giữa các split (test có 35,3% `traffic_camera` so với 18,0% ở train).
3. **Kiểm chứng dựa trên quan sát mẫu 25 cặp**, không phải kiểm đếm toàn bộ. Không thể khẳng định "đã sạch rò rỉ" bằng phash trên corpus này.

Phân tích đầy đủ: [docs/reports/07-testing-report.md §6](../../docs/reports/07-testing-report.md) · số liệu thô: [`../reports/v3/`](../reports/v3/)

---

## Việc còn nợ

Đổi tên các thư mục sang dạng không gây hiểu nhầm (ví dụ `dataset-v3/`) **sau khi lượt huấn luyện hiện tại kết thúc** — đổi lúc này sẽ làm hỏng lượt train đang chạy vì nó đọc trực tiếp `yolo_v3/data.yaml`.
