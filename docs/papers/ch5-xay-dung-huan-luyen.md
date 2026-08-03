# CHƯƠNG 5. XÂY DỰNG HỆ THỐNG VÀ HUẤN LUYỆN MÔ HÌNH

Chương 4 trình bày hệ thống *nên* được xây dựng thế nào; chương này trình bày hệ thống *đã* được xây dựng thế nào. Nguyên tắc: **mọi mô tả đều tương ứng với mã nguồn có thật trong kho `d:/DATN`**; chức năng chưa hoàn thiện thì ghi rõ mức độ, số đo chưa có thì để bảng trống với đầy đủ cột và chỉ tới Chương 6. Mục 5.9 đối chiếu thiết kế với hiện thực.

---

## 5.1. Môi trường và công cụ phát triển

### 5.1.1. Cấu hình máy thực hiện

Toàn bộ cài đặt, kiểm thử và đo đạc chạy trên một máy trạm duy nhất (`docs/00-requirements/environment.md`): Windows 11 Pro 10.0.26200; Intel Core i5-14600K (Raptor Lake Refresh), **14 nhân / 20 luồng**; RAM 31,77 GiB; GPU Intel UHD Graphics 770 tích hợp — **không có GPU CUDA**; Python 3.13.12 (dự phòng 3.11); Node.js 18.20.8 qua `nvm-windows`; Docker 29.4.3; 96 GB trống ổ D:. Cấu hình này **mâu thuẫn với mô tả môi trường ban đầu của đồ án** (macOS Apple Silicon, Python 3.12); ghi nhận sai lệch thành văn bản là bước đầu của Phase 0, vì cả ba tham số sai đều ảnh hưởng tới thiết bị huấn luyện, chỉ tiêu hiệu năng và cách viết đường dẫn tệp.

### 5.1.2. Vì sao "không có GPU" là ràng buộc thiết kế chứ không phải hạn chế tạm thời

Ba lý do độc lập: buổi bảo vệ chạy trên máy không GPU nên ràng buộc CPU-only nằm thẳng trong phát biểu NFR-P1; ràng buộc CPU thay đổi *lựa chọn mô hình* chứ không chỉ tốc độ, vì chênh lệch giữa YOLO11n và YOLO11s/m hay giữa OCR mobile và server lên tới hàng trăm mili-giây mỗi ảnh, nên AD-06 kéo theo hai quyết định phái sinh đã cài đặt là `yolo11n` và **PP-OCRv5 mobile**; và huấn luyện YOLO11 trên CPU ước tính 1–3 ngày một lượt nên `ai/training/` phải chạy được cả local lẫn Colab/Kaggle với siêu tham số nằm trong tệp cấu hình — lý do tồn tại của `ai/training/config.py` (586 dòng) như một lớp cấu hình có kiểm tra hợp lệ. Hệ quả đo được: p95 đầu-cuối trên `models/best.pt` (máy rảnh) là **731 ms** (client-side) / **780 ms** (in-process), đạt mục tiêu 800 ms của NFR-P1, với OCR chiếm **~64,3%** và phát hiện **~34,2%**.

### 5.1.3. Ba môi trường ảo Python tách biệt, và lý do bắt buộc phải tách

| Môi trường ảo | Vai trò | NumPy | OpenCV | Gói đặc trưng |
|---|---|---|---|---|
| `.venv-ai/` | Huấn luyện, xuất mô hình | **2.5.4** | `opencv-python` **5.0.0.93** (+ headless) | `torch` 2.13.0+cpu, `torchvision` 0.28.0 |
| `.venv-ocr/` | Thử nghiệm OCR biệt lập | **2.4.5** | `opencv-contrib-python` **4.10.0.84** | `paddlepaddle` 3.3.1, `paddleocr` 3.7.0, `paddlex` |
| `backend/.venv/` | Chạy dịch vụ (backend + suy luận) | **2.4.5** | `opencv-contrib-python` **4.10.0.84** | `torch`, `ultralytics` 8.4.101, `paddleocr` |

`paddleocr` kéo theo `paddlex`, **hạ cấp NumPy từ 2.4.x xuống 2.4.5** và **thay `opencv-python` bằng `opencv-contrib-python` 4.10** — lùi một phiên bản lớn so với OpenCV 5.0 của nhánh huấn luyện; cài chung là **ghi đè hai gói nền tảng của ngăn xếp thị giác máy tính**, và nếu không tách thì mỗi lần cài lại một nhánh âm thầm đổi phiên bản nhánh kia đang chạy — lỗi không làm chương trình sập mà làm **kết quả đo không tái lập được**. Phân tách này phản ánh ở `requirements.txt` (web + CSDL) và `requirements-inference.txt` (ngăn xếp ML), được `Dockerfile.backend` cài theo hai lớp riêng.

### 5.1.4. Bộ công cụ

Python 3.13.12 (local) / 3.12 (Docker); FastAPI + Uvicorn; SQLAlchemy 2.x + Alembic; Pydantic v2 / pydantic-settings; Ultralytics 8.4.101 chạy YOLO11 [16]<!-- jocher_2024_yolo11 -->; PaddlePaddle 3.3.1 / PaddleOCR 3.7.0 cho PP-OCRv5 [17]<!-- cui_2026_ppocrv5 -->; Node.js 18.20.8 (local) / 20 (Docker); Vite + React + TypeScript; pytest + pytest-cov; Docker + Docker Compose 29.4.3. Docker dùng Python 3.12 trong khi local dùng 3.13 là **chủ ý**: container là nơi lấy lại phiên bản mục tiêu và tách môi trường chạy khỏi máy cá nhân — nội dung cụ thể của NFR-C1.

---

## 5.2. Xây dựng bộ dữ liệu

### 5.2.1. Đường ống sáu bước

![](figures/fig-ch5-01.png)

**Hình 5.1.** Đường ống sáu bước xây dựng bộ dữ liệu

Mỗi bước là một script độc lập trong `scripts/dataset/` có CLI riêng và sinh báo cáo JSON/CSV; `run_pipeline.py` chạy cả chuỗi bằng một lệnh, nhưng CLI riêng vẫn cần vì bước khử trùng lặp phải chạy lại nhiều lần với ngưỡng khác nhau (mục 5.2.3). **Kết quả:** **15.133 ảnh** hợp nhất từ **7 bộ công khai** (Roboflow Universe, HuggingFace, Kaggle), còn **6 nguồn nguyên tố** sau khử trùng lặp chéo bộ, sau khi loại **11.978 ảnh (44,2%)** bản sao từ **27.111 ảnh**; tổng **9 bộ được tải về**, 2 bộ nhãn mức ký tự tách riêng cho đánh giá OCR nên không vào hợp nhất detection. Chia 70/20/10 thành **10.592 / 3.027 / 1.514 ảnh**. Bảng dưới **phải trích khi nói về dữ liệu của đồ án**, vì con số tổng che mất việc các bộ đóng góp **rất không đều**:

| # | Bộ (slug) | Nguồn | Giấy phép | Vào gộp | **Còn lại** | Bị loại |
|---|---|---|---|---:|---:|---:|
| 1 | `roboflow_school_fuhih` | Roboflow `school-fuhih/vietnamese-license-plate-tptd0` v1 | **CC BY 4.0** | 8.357 | **6.868** (45,38%) | 17,8% |
| 2 | `hf_vn_plates_segment` | HuggingFace `hoanglvuit/Vietnam_License_Plate_Segment_Datasets` | ⚠️ **chưa xác nhận** | 4.578 | **4.375** (28,91%) | 4,4% |
| 3 | `roboflow_traffic_camera` | Roboflow `traffic-camera/vietnam-license-plate-hayn8` v4 | **CC BY 4.0** | 3.843 | **3.162** (20,89%) | 17,7% |
| 4 | `roboflow_eric_nguyen` | Roboflow `eric-nguyen-knfxn/vietnam-license-plate-curhr` v1 | **CC BY 4.0** | 840 | **353** (2,33%) | 58,0% |
| 5 | `roboflow_demo_tracking` | Roboflow `demo-tracking/license-plate-vietnam-car` v2 | **CC BY 4.0** | 236 | **235** (1,55%) | 0,4% |
| 6 | `roboflow_cuong_ta` | Roboflow `cuong-ta-ulxex/vietnamese-car-license-plate` v1 | Public Domain (người đăng tự khai) | 8.254 | **140** (0,93%) | **98,3%** |
| 7 | `roboflow_tran_ngoc_xuan_tin` | Roboflow `tran-ngoc-xuan-tin-k15-hcm-dpuid/vietnam-license-plate-h8t3n` v1 | **CC BY 4.0** | 1.005 | **0** | **100%** |
| | **Tổng** | | | **27.113** | **15.133** | **44,2%** |

Nguồn: cột "vào gộp" từ `datasets/processed/merged_v2/merge_manifest.csv`; cột "còn lại" đếm trên `datasets/processed/yolo_v3/images/{train,val,test}`. Ba điều bảng nói ra mà con số tổng giấu đi: `school_fuhih` và `hf_vn_plates_segment` chiếm **74,3%** nên đồ án **không đa dạng về nội dung** như con số "6 nguồn" gợi ý; `cuong_ta` mất **98,3%** và `tran_ngoc_xuan_tin` mất **toàn bộ**, bằng chứng trực tiếp rằng các bộ công khai **không độc lập với nhau**; và — hệ quả ngoài ý muốn — `cuong_ta` là bộ **cân bằng nhất** về layout (51,04% hai dòng) còn `school_fuhih` sống sót nhiều nhất lại **lệch nặng nhất** (88,85% hai dòng), nên khử trùng lặp đã **vô tình làm tập dữ liệu lệch layout hơn** trước khi khử (`docs/reports/02-dataset-report.md` mục 7.3). **Giấy phép:** năm bộ CC BY 4.0, một bộ tự khai Public Domain — **không được khẳng định là Public Domain thật** vì ảnh nguồn có dấu hiệu là ảnh báo chí — và một bộ HuggingFace **chưa xác nhận được giấy phép**, phải nêu rõ khi công bố.

Song song, một nhánh riêng tái tạo **4.019 chuỗi biển số** từ hai bộ nhãn mức ký tự, trong đó **2.801 chuỗi (69,69%)** khớp mẫu hợp lệ theo `plate_rules.py` — `roboflow_ocr_plate` đóng góp **2.650**, `roboflow_ocr_conversion` **151**, cả hai CC BY 4.0 — phục vụ đánh giá OCR độc lập với tầng phát hiện.

> **Cảnh báo phạm vi bắt buộc đi kèm mọi số liệu OCR.** Chạy bộ phân loại màu nền lên toàn bộ 2.801 ảnh này cho: **2.736 biển trắng (97,68%)**, 20 vàng (0,71%), 4 xanh (0,14%), **0 đỏ và 0 ngoại giao**. Vì vậy phát biểu đúng là *"1 − CER = 0,9454 trên một tập gồm 97,7% biển trắng"*, **không phải** *"trên biển số Việt Nam"* (`docs/reports/17-plate-type-audit.json`).

Kết quả phụ: tập ký tự quan sát trên toàn bộ 4.019 chuỗi có **đúng 30 ký tự phân biệt**, không chứa `I`, `J`, `O`, `Q`, `W` — **xác nhận độc lập bằng dữ liệu** cho tập `EXCLUDED_LETTERS` vốn suy từ văn bản pháp quy (mục 5.5.6).

### 5.2.2. Khử trùng lặp chéo bộ và con số 44,2%

Các bộ công khai **không độc lập với nhau** (dự án Roboflow fork lẫn nhau, bản Kaggle đóng gói lại bản xuất Roboflow), nên nếu một bức ảnh nằm ở `train` dưới tên bộ này và ở `test` dưới tên bộ khác thì **độ chính xác test đang đo khả năng ghi nhớ**; vì vậy con số tiêu đề của script là số nhóm trùng lặp **chéo bộ**, còn trùng trong cùng bộ chỉ tốn thời gian huấn luyện. Vét cạn 37.000 ảnh là khoảng 690 triệu cặp nên script dùng **multi-index hashing**: cắt mã băm 64 bit thành `threshold + 1` dải, và theo nguyên lý chuồng bồ câu, hai mã khác nhau tối đa `threshold` bit **bắt buộc trùng khớp chính xác** trên ít nhất một dải, nên tập ứng viên **bảo đảm chứa mọi cặp thật** rồi được xác minh chính xác — **thuật toán chính xác chứ không xấp xỉ.** Cần phân biệt **hai phép đo trên hai mẫu số khác nhau**; trích một con số trần mà không nêu mẫu số là gây hiểu nhầm:

| Phép đo | Mẫu số | Ngưỡng Hamming | Ảnh có thể loại | Tỷ lệ | Đã xoá thật? |
|---|---:|---:|---:|---:|---|
| (a) Trên **toàn bộ ảnh của 7 bộ vào hợp nhất detection** | 27.111 | 5 | 11.978 | **44,2%** | **Rồi** (`applied: true`) |
| (b) Trên **corpus đã gộp** `merged_v2` còn lại | 15.133 | 10 | 7.227 | **47,8%** | **Chưa** (`applied: false`) |

Nguồn: (a) `datasets/reports/v2/deduplication_report.json`; (b) `datasets/reports/v3/deduplication_report.json`. Phép đo (b) quét 15.133 ảnh, thấy 19.277 cặp thuộc 1.171 nhóm, trong đó **116 nhóm chéo bộ**; cặp bộ chồng lấn nặng nhất là `hf_vn_plates_segment ↔ roboflow_school_fuhih` với **2.669 cặp**. 47,8% **không mâu thuẫn** với 44,2%: (b) chạy ngưỡng lỏng hơn nên bắt nhiều cặp gần trùng hơn, và **chỉ đo chứ chưa xoá**. Tỷ lệ **11.978 / 27.111 = 44,2%** — **gần một nửa là bản sao** — có hai hệ quả: quy mô thật khác hẳn quy mô danh nghĩa (ca cực đoan nhất là `roboflow_tran_ngoc_xuan_tin` vào với 1.005 ảnh và ra với **0 ảnh — loại 100%**, kiểm chứng độc lập ở mục 6.3.4; đây là lý do **không được cộng dồn `expected_images` của các bộ Roboflow**), và phân bố huấn luyện bị lệch vì 11.978 ảnh dư thừa tập trung ở các bộ được sao chép nhiều nhất. Đầu ra được `split.py` tiêu thụ, và nó giữ **mọi thành viên của một nhóm trùng lặp trong cùng một split** nên ngay cả bản trùng *không* bị xoá cũng không rò rỉ được.

### 5.2.3. Bài học về perceptual hash: nó tóm tắt bố cục khung ảnh, không tóm tắt chiếc xe

Đây là **giới hạn không khắc phục được** bằng công cụ hiện có. Một lần kiểm tra rò rỉ độc lập ở ngưỡng Hamming 10 trên bộ v1 tìm thấy **619 cặp gần trùng giữa `train` và `test`**; phân bố: 0 cặp ở d = 0 và d = 1–5, **619 cặp ở d = 6–10**, 3.016 cặp ở 11–15, 26.135 cặp ở 16–20, 1.437.204 cặp ở d > 20. Kiểm tra bằng mắt dải 6–10 cho thấy **cùng một chiếc xe, cùng chuỗi biển số, ở cả hai split**. Pipeline không bắt được vì bộ chia gom nhóm ở ngưỡng 5 rồi lần kiểm tra đầu cũng đo lại ở ngưỡng 5 và báo "0 cặp rò rỉ" — **lập luận vòng tròn**; rò rỉ thật nằm ở dải 6–10 mà bộ chia **không** bảo vệ. Nâng ngưỡng cũng không giải quyết được, vì perceptual hash rút một bức ảnh thành 64 bit mô tả **cấu trúc tần số thấp của toàn khung hình**, tức bố cục:

> Hai bức ảnh chụp **hai chiếc xe khác nhau** đi qua **cùng một camera** có khoảng cách phash rất nhỏ, bởi vì 90% khung hình — mặt đường, hàng cây, toà nhà, góc nhìn — là hoàn toàn giống nhau. Chiếc xe chỉ chiếm một phần nhỏ diện tích và ảnh hưởng rất ít tới mã băm.

Bằng chứng lưu tại **`datasets/reports/v3/corpus_samples/flagged_pair.png`**. Đánh đổi không thoát ra được: ngưỡng thấp (≤ 5) bỏ sót cặp cùng xe chụp khác ngày; ngưỡng cao (≥ 10) bắt thêm cặp cùng xe nhưng **gộp nhầm hàng nghìn ảnh xe khác nhau cùng camera vào một nhóm**, tức đánh đổi rò rỉ lấy sự nghèo nàn của dữ liệu. Bộ v3 được chia lại với gom nhóm ở ngưỡng cao hơn và kiểm tra rò rỉ độc lập ở ngưỡng 10, nhưng đồ án ghi nhận thẳng thắn rằng **vẫn còn rò rỉ tồn dư không khử được bằng phash** — trường hợp cùng một chiếc xe quay lại cùng một camera vào ngày khác; phân biệt nó với "hai xe khác nhau, cùng camera" đòi hỏi so khớp ở mức **chuỗi biển số** hoặc **đặc trưng phương tiện**, một cơ chế khác hẳn. Hệ quả: `baseline-416-v1.pt` đạt mAP@0.5 = 0,9933 trên bộ v1 nhưng con số đó **không được báo cáo là "đạt"** vì tập test của nó có rò rỉ đã đo được (mục 5.9).

---

## 5.3. Huấn luyện bộ phát hiện biển số

### 5.3.1. Siêu tham số

Bảng dưới trích từ `runs/final-640-v3/args.yaml` — tệp Ultralytics tự sinh khi bắt đầu lượt huấn luyện, nên là bản ghi *đã thực thi*, không phải *dự định*.

<!-- {{T5.3a}} sieu tham so huan luyen mo hinh chinh thuc — DA CO SO, khong can dien -->

**Bảng 5.1.** Siêu tham số huấn luyện mô hình chính thức

| Nhóm | Tham số và giá trị |
|---|---|
| Mô hình | `model` = `yolo11n.pt` (khởi tạo từ trọng số tiền huấn luyện COCO); **2.590.035** tham số — biến thể nano, do ràng buộc CPU |
| Dữ liệu | `data` = `datasets/processed/yolo_v3/data.yaml` (split v3); `imgsz` = **640** (đúng độ phân giải NFR-A1/A2 đặt chỉ tiêu); `fraction` = 1.0 |
| Lịch huấn luyện | `epochs` = **20**; `patience` = 20 (dừng sớm không kích hoạt); `batch` = 8 (giới hạn bởi RAM và tốc độ CPU); `close_mosaic` = 10 |
| Tối ưu hoá | `optimizer` = AdamW; `lr0` = 0.001; `lrf` = 0.01; `cos_lr` = `true`; `momentum` = 0.937; `weight_decay` = 0.0005; `warmup_epochs` = 3.0 |
| Trọng số hàm mất mát | `box` / `cls` / `dfl` = 8.0 / 0.5 / 1.5 |
| Tăng cường dữ liệu | `hsv_h`/`hsv_s`/`hsv_v` = 0.015 / 0.7 / 0.4; `degrees` = 5.0; `translate`/`scale`/`shear` = 0.1 / 0.5 / 2.0; `perspective` = 0.0005; `fliplr`/`flipud` = **0.0 / 0.0**; `mosaic`/`mixup`/`cutmix` = 1.0 / 0.0 / 0.0; `erasing` = 0.4; `auto_augment` = `randaugment` |
| Thực thi | `device` = **`cpu`**; `workers` = 2; `amp` = `false`; `seed` / `deterministic` = 42 / `true` |

**`fliplr = 0.0`** lệch có chủ ý so với mặc định `0.5` của Ultralytics: lật ngang tạo ảnh mà ký tự bị gương hoá — phân bố **không bao giờ xuất hiện trong thực tế**. **`seed = 42`, `deterministic = true`:** chỉ chạy được **một lượt huấn luyện duy nhất** (giới hạn thời gian CPU, mục 6.2.3) nên không có nhiều lượt để ước lượng phương sai giữa các seed; cố định seed ít nhất đảm bảo lượt này **tái lập được**, và mọi chỉ số trong chương là kết quả của **một lần chạy**, không có khoảng tin cậy — hạn chế ghi nhận ở mục 6.9.3.

### 5.3.2. Đường cong huấn luyện

Ba hình dưới sinh từ `runs/final-640-v3/results.csv` sau khi huấn luyện kết thúc.

*Hình 5.1.* Đường cong hàm mất mát theo epoch — `box_loss`, `cls_loss`, `dfl_loss`, tách riêng train và val. `docs/reports/figures/05-train-loss-curves.png` *(chưa sinh)*

*Hình 5.2.* Tiến triển mAP@0.5 và mAP@0.5:0.95 trên tập validation. `docs/reports/figures/05-train-map-curves.png` *(chưa sinh)*

*Hình 5.3.* Tiến triển precision và recall trên tập validation. `docs/reports/figures/05-train-pr-curves.png` *(chưa sinh)*

**Điểm cần đọc từ ba hình** (viết sau khi có hình, không đoán trước): khoảng cách `train_loss` – `val_loss` có mở rộng dần không, dấu hiệu quá khớp; đường mAP đã bão hoà hay còn dốc lên tại epoch 20 — nếu còn dốc thì phải ghi rõ **20 epoch là giới hạn ngân sách tính toán chứ không phải điểm hội tụ**; và bước nhảy tại epoch 10 khi `close_mosaic` kích hoạt.

### 5.3.3. Tiến triển mAP theo mốc epoch

<!-- {{T5.3b}} tien trien chi so tren tap validation theo epoch -->

**Bảng 5.2.** Tiến triển chỉ số trên tập validation theo mốc epoch

| Epoch | `box_loss` (val) | `cls_loss` (val) | `dfl_loss` (val) | mAP@0.5 | mAP@0.5:0.95 | Precision | Recall |
|:---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1,1705 | 0,6858 | 1,1513 | **0,9684** | **0,6526** | 0,9552 | 0,9410 |
| 2 | 1,1861 | 0,5554 | 1,1307 | **0,9726** | **0,6653** | 0,9700 | 0,9450 |
| 3 | 1,1647 | 0,5651 | 1,1098 | **0,9723** | **0,6770** | 0,9731 | 0,9449 |
| 5 | 1,1074 | 0,4977 | 1,0863 | **0,9754** | **0,6950** | 0,9765 | 0,9525 |
| 10 | 1,0548 | 0,4168 | 1,0686 | **0,9808** | **0,7248** | 0,9850 | 0,9584 |
| 15 | 0,9420 | 0,3619 | 1,0205 | **0,9824** | **0,7609** | 0,9846 | 0,9686 |
| 20 | 0,9204 | 0,3331 | 1,0105 | **0,9830** | **0,7688** | 0,9846 | 0,9697 |
| **Epoch tốt nhất (= 20)** | **0,9204** | **0,3331** | **1,0105** | **0,9830** | **0,7688** | **0,9846** | **0,9697** |

> Số liệu từ `runs/final-640-v3/results.csv` (20 epoch đã chạy đủ). **mAP@0.5 gần bão hoà rất sớm** (≈0,97 ngay từ epoch 1, chỉ nhích lên 0,983 ở epoch 20) trong khi **mAP@0.5:0.95 vẫn tăng đều** từ 0,653 lên 0,769 — mô thức điển hình khi *định vị đối tượng* là dễ còn *khớp box chính xác* mới khó. mAP@0.5:0.95 vẫn còn dốc lên tới epoch 20 (0,7605 ở epoch 18 → 0,7688 ở epoch 20) nên **phải phát biểu rõ rằng 20 epoch là giới hạn ngân sách tính toán chứ không phải điểm hội tụ**. `val/cls_loss` giảm đơn điệu (0,686 → 0,333) không tách khỏi xu hướng, tức chưa thấy dấu hiệu quá khớp rõ rệt.
>
> **Việc chọn epoch tốt nhất chỉ dựa trên tập validation.** Epoch 20 có mAP@0.5:0.95 trên val cao nhất và cũng là epoch cuối; tập test không được dùng cho bất kỳ quyết định nào trong mục này.

### 5.3.4. Chi phí huấn luyện

Baseline `baseline-416-v1.pt`: 40 epoch, `imgsz` 416, bộ v1 (4.578 ảnh), **tổng 156 phút**, CPU. Mô hình chính thức `best.pt`: 20 epoch, `imgsz` 640, bộ v3 (15.133 ảnh), **≈ 35,6 phút/epoch**, **tổng ≈ 712 phút (≈ 11,9 giờ)**, CPU. Chênh lệch là hệ quả của ba yếu tố cùng thay đổi — số ảnh tăng 3,3 lần, diện tích ảnh tăng khoảng 2,37 lần (640²/416²), số epoch giảm một nửa — cũng chính là ba biến đồng thời khiến so sánh ở mục 3.6 **không quy kết được nguyên nhân cho từng biến riêng lẻ**.

---

## 5.4. Tinh chỉnh bộ nhận dạng ký tự

PP-OCRv5 mobile được huấn luyện trên chữ cảnh tổng quát; mục này trả lời bằng số câu hỏi fine-tune nó trên đúng miền dữ liệu thì được gì, trên **cùng 2.801 biển có nhãn chuỗi**, cùng bộ phát hiện, cùng mọi công tắc. **Cấu hình:** 30 epoch trên 6.672 mẫu (2.801 ảnh gốc, mỗi ảnh thêm hai biến thể tăng cường: nén nhỏ và làm nhoè/nghiêng), kiểm định 571 mẫu sạch, bộ ký tự đủ 36 (`0-9A-Z`), khởi đầu từ `en_PP-OCRv5_mobile_rec_pretrained`; kết thúc train acc **0,9449**, val acc **0,8809**, `norm_edit_dis` 0,9823.

<!-- {{T5.4}} so sanh fine-tune va model goc -->

**Bảng 5.3.** So sánh bộ nhận dạng gốc và bản tinh chỉnh trên cùng ngữ liệu

| Cấu hình | A5 (chuỗi thô) | A6 (sau hậu xử lý) | Đúng định dạng | ms/ảnh |
|---|---:|---:|---:|---:|
| **Model gốc, det + rec** — *bản giao hàng* | 0,6373 | **0,7512** | 0,9443 | 328,8 |
| Model fine-tune, det + rec | 0,5998 | 0,6762 | 0,9018 | — |
| Model gốc, chỉ rec | 0,6776 | 0,7508 | 0,9568 | 35,7 |
| Model fine-tune, chỉ rec | **0,8618** | **0,8758** | **0,9886** | 38,5 |

Nguồn: `docs/reports/28-ocr-accuracy-finetuned.json` và `docs/reports/29-reconly-ablation.json`. **Phải đọc theo hàng chứ không theo cột.** Hàng 2 so hàng 1: ở đúng chế độ hệ thống đang chạy, fine-tune **kém hơn 7,50 điểm** — dừng ở đây thì kết luận là "fine-tune thất bại". Hàng 4 so hàng 1: bỏ bước phát hiện chữ, fine-tune **hơn 12,46 điểm** và đạt ngưỡng tối thiểu NFR-A6 (0,85) mà bản giao hàng không đạt — kết luận ngược hẳn. **Nguyên nhân mâu thuẫn là hai chế độ đo khác nhau, không phải model:** PaddleOCR đánh giá nhánh nhận dạng bằng cách đưa **nguyên ảnh** biển, còn đường ống triển khai cắt ảnh thành nhiều mảnh rồi đọc từng mảnh, mà model fine-tune chỉ được dạy đọc cả biển một lần nên chưa từng thấy mảnh vụn. Đo trên **chính những tệp ảnh nó đã huấn luyện trên đó** (300 ảnh trong tập huấn luyện): chế độ chỉ nhận dạng — như lúc huấn luyện — model gốc 0,2933, fine-tune **0,8233**; chế độ phát hiện + nhận dạng — như lúc chạy thật — fine-tune tụt về **0,2667**. Mẫu lỗi khớp giả thuyết đọc-từng-mảnh: `51U74598` ra `598`, `59X132817` ra `32817` — cụt đầu.

**Vì vậy con số val acc 0,8809 không sai, nhưng nó đo một chế độ hệ thống không dùng** — thuộc cùng họ với ba lần trước trong đồ án (mục 6.9.3): một phép đo trả về con số đẹp vì nó không chạm được vào chỗ hỏng. **Quyết định: không đem fine-tune đi giao, và cũng không bật chế độ chỉ-rec** (lý do ở mục 6.6.6 — ngữ liệu 2.801 mẫu toàn ảnh **đã cắt sẵn** nên không có thẩm quyền quyết định giữa hai chế độ; đo lại trên ảnh toàn cảnh thì thứ tự đảo ngược). Model, công tắc `ALPR_OCR_REC_MODEL_DIR` và toàn bộ đường ray huấn luyện **giữ nguyên trong kho mã**, sẵn sàng cho lượt đo có tập nhãn ảnh hiện trường.

---

## 5.5. Cài đặt tầng AI

### 5.5.1. Tổ chức gói `ai/inference` và ràng buộc "không import FastAPI"

Gói gồm mười một mô-đun cùng `__init__.py` (80 dòng), tổng **4.852 dòng**: `types.py` 302 (`BoundingBox`, `PlateDetection`, `PlateRecognition`, `DetectionResult`, `PipelineResult`), `interfaces.py` 169, `config.py` 281 (`InferenceConfig`), `exceptions.py` 71 (cây `ALPRError`), `plate_rules.py` 683, `normalizer.py` 419, `detector.py` 597, `recognizer.py` 648, `two_line.py` 500, `plate_color.py` 247, `pipeline.py` 855.

**Ràng buộc kiến trúc trung tâm (NFR-M1): không tệp nào trong `ai/` được `import fastapi`, `pydantic`, `pydantic_settings` hay `starlette`**; riêng `ai/inference/` cấm thêm `sqlalchemy` và `backend`. Lý do: gói suy luận phải chạy được trong Jupyter, script benchmark và Colab — nơi không có máy chủ web lẫn CSDL. **Ràng buộc được kiểm chứng tự động chứ không bằng rà soát mã**, qua `tests/test_architecture.py` (340 dòng) với hai kiểm tra bổ sung nhau: quét văn bản mã nguồn bằng regex chỉ khớp **câu lệnh import viết thường** chứ không khớp tên sản phẩm viết hoa trong tài liệu — nếu không, cách duy nhất để test đi qua là ngừng viết tài liệu về ràng buộc; và quan sát `sys.modules` trong **tiến trình Python hoàn toàn mới** sinh bằng `subprocess.run`, vì quét văn bản không thấy được import **bắc cầu** còn kiểm tra ngay trong bộ test lại vô giá trị do các test tích hợp đã nạp FastAPI từ trước. Ba điều kiện phái sinh cũng được ghim: mỗi mô-đun phải import được **độc lập**; `ALPRPipeline` phải khởi tạo được từ ba đối tượng giả mà **không nạp `ultralytics`, `paddleocr` hay `torch`**; và `ai/evaluation/` được import `backend`/`sqlalchemy` nhưng **chỉ ở phạm vi hàm**. NFR-M4 (**không đường dẫn tuyệt đối viết cứng**) kiểm cùng cách: quét chuỗi dạng `"C:\..."` / `"/home/..."` và khẳng định hai mô-đun cấu hình đều dẫn xuất gốc dự án từ `Path(__file__).resolve().parents[...]`.

### 5.5.2. Ba lớp trừu tượng

![](figures/fig-ch5-02.png)

**Hình 5.2.** Ba lớp trừu tượng của tầng AI và quan hệ giữa chúng

**`BaseDetector`** trả lời đúng một câu hỏi — *biển số nằm ở đâu?* Hợp đồng `detect(image) -> list[PlateDetection]` quy định ba điều kiện: đã lọc theo ngưỡng tin cậy và NMS; mọi hộp bao đã **kẹp về trong biên ảnh** để cắt được ngay; và **danh sách rỗng là kết quả bình thường**, không bao giờ là lỗi. **`BaseRecognizer`** nhận *ảnh biển đã cắt*, và quan trọng nhất là điều nó **không** làm — sửa lỗi ký tự và kiểm tra định dạng không thuộc trách nhiệm của nó, chính việc tách đó làm đóng góp của hậu xử lý trở nên **đo được** qua hiệu số giữa `raw_ocr_text` và `plate_number`. **`BaseNormalizer`** trả cặp `(normalized_text, is_valid_format)`, và kết quả không hợp lệ vẫn phải được **trả về** chứ không loại bỏ, vì loại bỏ sẽ xoá đúng những thất bại mà chương đánh giá cần đếm. Cả hai lớp đầu có `warmup()` mặc định rỗng để chuyển chi phí nạp trọng số và biên dịch trễ ra khỏi yêu cầu đầu tiên của người dùng — phục vụ NFR-P1.

### 5.5.3. Cài đặt bộ phát hiện — `YoloPlateDetector`

Adapter mỏng trên Ultralytics, giữ Ultralytics ở vị trí *chi tiết cài đặt*: không nơi nào ngoài mô-đun này chạm vào `Results`, tensor PyTorch hay chỉ số lớp. **Import trễ** (`from ultralytics import YOLO` nằm trong `_load_yolo_model`) cho unit test kiểm tra logic chuyển đổi mà không cần ngăn xếp ML; ngược lại **trọng số nạp ngay trong hàm khởi tạo** để tệp thiếu hoặc hỏng làm hệ thống **thất bại lúc khởi động**, kèm đường dẫn đã thử và hướng dẫn khắc phục. Bốn chi tiết: `SUPPORTED_WEIGHT_SUFFIXES = (".pt", ".onnx", ".torchscript")` cộng khả năng nhận **thư mục** OpenVINO (định dạng duy nhất lưu theo thư mục, nên `_verify_weights_exist` kiểm tệp `.xml`), vì từ chối thư mục sẽ khiến cấu hình nhanh nhất trên CPU Intel không cấu hình được qua `ALPR_MODEL_PATH`; `_resolve_plate_class_ids` giữ tất cả khi mô hình không công bố bảng tên lớp hoặc chỉ có **một lớp** (trường hợp của đồ án), còn mô hình **nhiều lớp** chỉ giữ lớp khớp `PLATE_CLASS_ALIASES` (`license_plate`, `licence_plate`, `plate`, `license-plate`, `bien_so`) nên checkpoint COCO 80 lớp luôn trả danh sách rỗng — đúng, không phải lỗi; `_build_clamped_bbox` kẹp về `[0, width]` × `[0, height]`, hoán đổi nếu `x2 < x1` và trả `None` kèm log nếu hộp suy biến, cho phép hợp đồng `BaseDetector` hứa mọi hộp đều cắt được ngay; và `name` trả `f"yolo:{stem}{suffix}"` (ví dụ `yolo:best.pt`) vì một con số benchmark chỉ tái lập được nếu nêu tên đúng bộ trọng số sinh ra nó.

### 5.5.4. Cài đặt bộ nhận dạng ký tự — `PaddleOcrRecognizer`

Ba đặc điểm cấu trúc: **khởi tạo trễ và tái sử dụng** vì máy OCR rất đắt để dựng; **ghim phiên bản** `OCR_VERSION = "PP-OCRv5"` truyền tường minh, vì nâng cấp `paddleocr` không được phép âm thầm đổi mô hình đứng sau một con số benchmark đã công bố; **tắt tiền xử lý mức tài liệu** (`use_doc_orientation_classify`, `use_doc_unwarping`, `use_textline_orientation` = `False`) vì đầu vào đã là vùng biển đã cắt.

**Phát hiện kỹ thuật: backend oneDNN làm sập suy luận trên PP-OCRv5.** Trên đúng nền tảng mục tiêu — `paddlepaddle` **3.3.1**, Windows, CPU — chạy mô hình phát hiện văn bản của PP-OCRv5 qua oneDNN **kết thúc bằng ngoại lệ** `NotImplementedError: (Unimplemented) ConvertPirAttribute2RuntimeAttribute not support [pir::ArrayAttribute<pir::DoubleAttribute>]`, vì bộ thực thi PIR không dịch được một thuộc tính của đồ thị sang dạng nhân oneDNN yêu cầu — khiếm khuyết phía thư viện, không phải lỗi cấu hình của đồ án. Cách xử lý là hằng số có tài liệu `DEFAULT_ENABLE_MKLDNN: Final[bool] = False`. Đây là **núm điều chỉnh hiệu năng, không phải núm điều chỉnh độ chính xác** — khi lỗi thượng nguồn được sửa thì chỉ cần lật giá trị và đo lại; nó cũng giải thích một phần kết quả NFR-P1, vì một con đường tăng tốc CPU hiển nhiên đang bị chặn bởi lỗi thư viện chứ không phải chưa được thử.

**Lọc mảnh văn bản theo hình học.** CLAHE khuếch đại mọi biến thiên trong vùng ảnh, nên ở vùng gần đồng nhất nhiễu cảm biến được khuếch đại có thể đủ kết cấu để bộ phát hiện văn bản kích hoạt: trên một ảnh biển tổng hợp, hiện tượng này sinh một mảnh cao 10 điểm ảnh đọc thành `"cYanmaGaYGntaYellowb"` với độ tin cậy **0,84**, cạnh hai hàng ký tự thật cao 125 và 87 điểm ảnh. **Ngưỡng tin cậy không tách được hai trường hợp này** — 0,84 hoàn toàn bình thường — mà thứ tách được là **hình học**, vì sau phép cắt–ghép mọi hàng ký tự hợp lệ đều chiếm phần lớn chiều cao dải ảnh; luật là `MIN_FRAGMENT_HEIGHT_RATIO: Final[float] = 0.35` đo **so với mảnh cao nhất** nên không phụ thuộc khung cắt chặt hay lỏng, và `_drop_short_fragments` **trả nguyên đầu vào nếu không mảnh nào báo được hình học**. **Tổng hợp độ tin cậy** dùng **trung bình có trọng số theo độ dài mảnh**, vì trung bình cộng cho phép một mảnh một ký tự ở 0,99 che lấp một mảnh bảy ký tự ở 0,40 trong khi chính mảnh dài mới mang danh tính biển số.

### 5.5.5. Mô-đun xử lý biển hai dòng — `two_line.py`

**a) Vì sao bài toán tồn tại.** Bộ nhận dạng hiện đại là CRNN/CTC với giả định **căn chỉnh đơn điệu** giữa cột ảnh và ký tự đầu ra — chỉ đúng khi văn bản một dòng; chồng lên đó, PP-OCR **resize mọi ảnh cắt về chiều cao cố định 48 điểm ảnh** [103]<!-- paddlepaddle_2026_textrecognition -->. Theo QCVN 08:2024/BCA [11]<!-- bocongan_2024_qcvn08 -->, biển xe máy 140 × 190 mm cho tỷ lệ khung ≈ **1,36**, nên sau khi ép về 48 px thì mỗi hàng ký tự chỉ còn khoảng **24 px** — dưới mức nét chữ còn tách rời được. Hệ quả định lượng đã được công bố: trên bộ **RodoSol-ALPR của Brazil**, OpenALPR đạt **94,3% trên biển ô tô một dòng** nhưng chỉ **45,7% trên biển xe máy hai dòng** [7]<!-- laroca_2022_crossdataset -->[88]<!-- laroca_2022_rodosol -->.

> **Cảnh báo về phạm vi áp dụng.** Cặp số 94,3% / 45,7% được đo trên **bộ dữ liệu RodoSol-ALPR của Brazil**, **không phải dữ liệu Việt Nam** và **không phải một benchmark chung của OpenALPR**. Đồ án trích dẫn nó thuần tuý như một *dẫn chứng tương đương định lượng* cho độ khó tương đối của bố cục hai dòng so với một dòng: nó chứng minh "biển hai dòng khó hơn" là sự kiện đo được, không phải cảm nhận.

**b) Ước lượng số dòng bằng tỷ lệ khung.** `estimate_line_count` dùng `DEFAULT_TWO_LINE_AR_THRESHOLD: Final[float] = 2.5` với `line_count = 2 if aspect_ratio < threshold else 1`. **Đây là heuristic do đồ án đề xuất, không phải quy tắc pháp lý.** Thứ quy chuẩn *có* cung cấp là kích thước vật lý: ô tô biển dài 110 × 520 mm → 4,727 (1 dòng), ô tô biển ngắn 165 × 330 mm → 2,000 (2 dòng), xe máy 140 × 190 mm → 1,357 (2 dòng); không loại nào rơi vào khoảng trống rộng 2,727 giữa 2,000 và 4,727, và 2,5 chọn **lệch về phía hai dòng** vì đường xử lý hai dòng suy giảm êm khi gặp đầu vào một dòng còn chiều ngược lại thì không. Hạn chế đã ghi trong mã: dải 2,5–3,0 là **vùng xám thật sự** vì biển một dòng chụp góc nghiêng gắt có tỷ lệ *hộp bao* tụt vào đó; đo trên ảnh đã nắn phối cảnh hoặc trên `cv2.minAreaRect` sẽ đáng tin cậy hơn, và định lượng tần suất ảnh hưởng thuộc Chương 6.

**c) Cắt trên/dưới có chồng lấn.** `split_two_line` dùng `UPPER_HALF_END_RATIO = 5.0/12.0` (0,4167) và `LOWER_HALF_START_RATIO = 1.0/3.0` (0,3333), nên **hai nửa chồng lấn một dải bằng 1/12 chiều cao biển**. Chồng lấn là chủ ý, do bất đối xứng chi phí sai lầm: **cắt cụt chân chữ hàng trên hoặc đỉnh chữ hàng dưới** phá huỷ thông tin **vĩnh viễn**, còn **để lọt vài điểm ảnh hàng bên cạnh** thì bộ nhận dạng **bỏ qua** như nền. Hàm ép hai nửa không rỗng (`upper_end = max(upper_end, 1)`, `lower_start = min(lower_start, height - 1)`) và ghi log cảnh báo nếu tham số dẫn tới **mất chồng lấn**.

**d) Ghép ngang bằng `np.hstack`.** Chiều cao chung là `max(upper.h, lower.h, MIN_MERGE_HEIGHT)` với `MIN_MERGE_HEIGHT: Final[int] = 48` — **không phải tuỳ chọn**, vì nó bằng đúng chiều cao đầu vào cố định của PP-OCR và một dải thấp hơn buộc máy OCR tự phóng to một ảnh đã suy giảm. Nửa trên đặt bên trái nên **thứ tự đọc được bảo toàn**, và sau khi ghép thì **một hàng ký tự duy nhất nhận trọn ngân sách 48 px** thay vì hai hàng chia nhau. `_match_channels` nâng cả hai nửa về BGR khi số kênh lệch, vì `np.hstack` từ chối mảng có số chiều đuôi khác nhau.

**e) Tiền xử lý ảnh biển — `preprocess_plate`.** Ba bước nhẹ, **mỗi bước bật/tắt độc lập** để đánh giá có thể ablation từng bước: *chuyển ảnh xám* (`COLOR_BGR2GRAY`) vì ký tự biển số không mang thông tin màu; *CLAHE* (`clipLimit=2.0, tileGridSize=(8,8)`) vì biển là kim loại phản quang với ký tự dập nổi 1,7 mm theo QCVN 08:2024/BCA nên đèn pha tạo mảng chói trên một phần biển mà cân bằng biểu đồ **toàn cục** không xử lý được, còn thích nghi theo ô thì được [95]<!-- sutikno_2025_clahe -->; và *khử nhiễu* (`bilateralFilter(d=5, sigmaColor=50, sigmaSpace=50)`) vì lọc song phương **bảo toàn biên có chủ ý**, trong khi làm mờ Gauss đủ mạnh để khử nhiễu cũng bo tròn đầu nét — thứ phân biệt `8` với `B`. Kết quả **luôn là mảng BGR ba kênh**; recognizer truyền `upscale_to_height = _MIN_OCR_HEIGHT = 64` vì ảnh biển ra khỏi bộ phát hiện thường chỉ cao 20–40 px.

**f) Bước cứu dòng trên — một giả thuyết hợp lý bị chính dữ liệu bác bỏ.** Mục có giá trị phương pháp luận cao nhất của chương, vì nó ghi trọn một chu trình: quan sát chế độ hỏng — đề xuất giả thuyết *nghe rất hợp lý* — **đo và bác bỏ** — và chính phép bác bỏ dẫn tới thiết kế đúng. Ảnh biển vàng `29E-015.66` trả về `015.66` kèm cờ *sai định dạng*; hai giai đoạn đầu **không hề sai** (cắt đúng vùng biển, phân loại đúng là hai dòng), điểm gãy nằm ở giai đoạn ghép vì sau khi hai nửa xếp cạnh nhau và đưa vào OCR **một lần**, bộ phát hiện văn bản chỉ tìm thấy **một** vùng chữ và bỏ hẳn cụm `29E` — **khớp với hồ sơ lỗi đã đo** ở Chương 6, nơi lỗi *thiếu ký tự* chiếm ưu thế so với lỗi *nhầm ký tự* trên biển hai dòng. Giả thuyết đầu tiên — bỏ phép ghép, đọc riêng từng nửa rồi nối chuỗi — đủ hợp lý để không bác bỏ được bằng lập luận suông, nên nó được **đo** trên 200 biển hai dòng có nhãn chuỗi (`docs/reports/15-two-line-ab.json`):

| Chiến lược | Đọc đúng | Độ chính xác chuỗi | Đọc rỗng | Thời gian trung bình |
|---|---:|---:|---:|---:|
| **A** — ghép rồi OCR một lần (thiết kế hiện tại) | 129 / 200 | **64,5%** | 2 | 340,11 ms |
| **B** — OCR từng nửa rồi nối chuỗi (giả thuyết) | 7 / 200 | **3,5%** | 9 | 391,35 ms |

Chênh **−61,0 điểm phần trăm**: A thắng ở 122 ảnh, B thắng ở **0 ảnh** — một sự sụp đổ, không phải khác biệt trong sai số lấy mẫu. Nguyên nhân nằm ở đúng chi tiết đã biện minh ở mục (c): khi hai nửa **cắt chồng lấn có chủ ý** đi vào OCR riêng rẽ, dải chồng lấn 1/12 chiều cao **bị đọc hai lần** và sinh ký tự rác nối vào giữa chuỗi — `84G122593` được A đọc thành `84-G1225.93` (chuẩn hoá về đúng `84G122593`) còn B đọc thành `84-G124E009.01225.93`; cùng dạng: `36B557557` → `36-85JU2FUJ575.57`, `29B125662` → `29.JDI256.62`. Kết luận **đảo ngược cách hiểu ban đầu về vai trò của phép ghép**: nó còn **trao cho bộ phát hiện văn bản cơ hội loại bỏ vùng chồng lấn**, vì trên dải liền mạch vùng lặp nằm giữa hai cụm chữ và bị gạt đi, còn trên hai ảnh rời thì không có ngữ cảnh nào để gạt. Bản sửa vì thế **giữ nguyên** chiến lược A và chỉ thêm một bước phục hồi hẹp:

```python
def should_rescue_two_line(recognition: PlateRecognition) -> bool:
    return (recognition.line_count == 2
            and not recognition.is_valid_format
            and bool(recognition.raw_text))
```

Khi và chỉ khi ba điều kiện cùng đúng, hệ thống mới tốn thêm **một** lần gọi OCR trên riêng nửa trên, ghép `upper + raw` rồi chuẩn hoá lại; kết quả mới **chỉ được chấp nhận nếu qua kiểm tra định dạng**, mọi trường hợp khác kể cả khi bước cứu ném ngoại lệ đều trả nguyên kết quả cũ. **Tính chất "không thể làm tệ đi" là tính chất cấu trúc, không phải kết quả thực nghiệm may mắn:** cổng chỉ mở khi kết quả **đã hỏng sẵn**, nên tập biển bị ảnh hưởng và tập biển đang đúng là **hai tập rời nhau**; số đo dưới đây là *kiểm chứng*, không phải *căn cứ*:

| Mẫu (nguồn) | Trước | Sau | Cứu được | Làm hỏng | Tần suất kích hoạt | Thời gian trung bình |
|---|---:|---:|---:|---:|---:|---:|
| 700 mẫu, seed 7 (`15-two-line-fallback-700.json`) | 60,14% | **62,00%** | 13 | **0** | 148/700 = 21,14% | 362,41 → 383,52 ms |
| 200 mẫu, seed khác (`15-two-line-fallback.json`) | 64,5% | **65,0%** | 1 | **0** | 36/200 = 18,0% | 346,70 → 361,97 ms |

Cột "làm hỏng" bằng **0 ở cả hai mẫu** trên tổng 900 biển hai dòng, đúng như tính chất cấu trúc dự đoán. Mức cải thiện **khiêm tốn** (+1,86 và +0,5 điểm) và không được trình bày như bước đột phá: nó vá một điểm mù cụ thể, không đụng tới nút thắt chính là chất lượng mô hình nhận dạng trên biển hai dòng. Chi phí độ trễ khoảng **15–21 ms trung bình mỗi biển hai dòng**, vì lần gọi thêm chỉ chạy trên khoảng một phần năm số ảnh và chỉ trên ảnh vốn đã hỏng.

**g) Một lỗi phương pháp đo, quan trọng hơn chính bản vá.** Script `ai/evaluation/ocr_accuracy.py` — nơi sinh các con số NFR-A4, A5, A6, A7 công bố ở Chương 6 — **không đi qua `ALPRPipeline`** mà gọi thẳng bộ nhận dạng và bộ chuẩn hoá, nên **mọi logic đặt ở tầng điều phối đều vô hình đối với các con số công bố**: nếu bước cứu được cài như một phương thức riêng của pipeline — cách viết tự nhiên nhất — thì chương thực nghiệm sẽ đo một đường mã mà sản phẩm thật không chạy và **báo thấp hơn** năng lực thực của hệ thống đang giao. Cách sửa là **tách bước cứu thành hai hàm tự do dùng chung** (`should_rescue_two_line`, `rescue_two_line_upper`) ở cấp mô-đun để cả pipeline lẫn bộ đo cùng gọi, kèm lý do ghi thẳng vào docstring: *"Were the rescue a method, the published NFR-A5/A6/A7 figures would measure a code path that production does not use."* Bài học vượt ra ngoài phạm vi biển hai dòng: **một bộ đo đi tắt qua tầng điều phối sẽ đo một hệ thống khác với hệ thống được giao** — khoảng cách đó không gây lỗi, không sinh cảnh báo, chỉ lộ ra khi có người đối chiếu hai đường mã.

### 5.5.6. Cài đặt bộ luật hậu xử lý — đóng góp kỹ thuật chính

Bộ phát hiện và bộ nhận dạng đều là mô hình có sẵn; khối hậu xử lý thì không. `plate_rules.py` tuân thủ ba quy tắc ghi trong tài liệu mô-đun: **thuần khiết** (không I/O, log, import khung hay trạng thái toàn cục khả biến); **regex sinh từ tập hợp, không viết tay** nên mẫu không thể trôi khỏi bảng nó mã hoá; **lớp ký tự là hằng có tên**.

**a) `PROVINCE_CODES` — 81 mã tỉnh** đang dùng theo phụ lục Thông tư 51/2025/TT-BCA [10]<!-- bocongan_2025_tt51 --> (80 mã địa phương cộng mã 80 của Cục Cảnh sát giao thông), song song với `UNUSED_PROVINCE_CODES` gồm **8 mã không bao giờ được cấp**: `13, 42, 44, 45, 46, 87, 91, 96`. Giá trị so với `\d{2}` là cụ thể và đo được: nó **bác bỏ** `13A-123.45` vì mã `13` chưa từng được cấp; giữ tường minh cả tập không dùng cho phép một test khẳng định `PROVINCE_CODES | UNUSED_PROVINCE_CODES` phủ đúng dải `11`–`99`. Ghi chú trong mã: sáp nhập đơn vị hành chính năm 2025 **không làm mất hiệu lực biển số đã cấp**, nên một mã có thể trỏ tới tỉnh không còn tồn tại — mối quan tâm của tầng báo cáo, không phải của định dạng.

**b) Các lớp ký tự sê-ri.**

| Hằng | Tập ký tự | Vị trí áp dụng |
|---|---|---|
| `L20` | `A B C D E F G H K L M N P S T U V X Y Z` | Chữ sê-ri biển ô tô; chữ **thứ nhất** của sê-ri biển xe máy |
| `L20B` | `A B C D E F H K L M N P R S T U V X Y Z` | Chữ **thứ hai** của sê-ri biển xe máy |
| `L11` | `A`–`H`, `K`, `L`, `M` | Sê-ri biển xanh (cơ quan nhà nước) |
| `L21` | 20 chữ chuẩn **cộng** `R` | Tập ký tự an toàn cho bộ nhận dạng |

**`L20` và `L20B` là ảnh gương của nhau ở đúng hai ký tự** (`L20` có `G` không có `R`, `L20B` có `R` không có `G`), bất đối xứng thật và có hệ quả: `29-AR 123.45` hợp lệ còn `29-AG 123.45` thì không. `L21` tồn tại vì **một mô hình có tập ký tự dựng từ "20 chữ cái" không bao giờ dự đoán ra `R`** nên sẽ sai **có hệ thống** trên mọi biển xe máy mang `R` ở sê-ri thứ hai — loại sai không hậu xử lý nào sửa được vì thông tin đã bị huỷ ở tầng mô hình. Cùng logic dẫn tới tách đôi tập ký tự: `OCR_SAFE_CHARSET` = chữ số + 21 chữ hợp pháp (**31 ký tự**), `OCR_TRAINING_CHARSET` = chữ số + `A..Z` (**36 ký tự**); huấn luyện trên 36 rồi ràng buộc về 31 là chủ ý, vì một mô hình **được phép** dự đoán ký tự bất hợp pháp tạo ra sai lầm **quan sát được, ghi log được, sửa được**, còn mô hình **không thể về mặt kiến trúc** dự đoán một ký tự tạo ra sai lầm vô hình. `EXCLUDED_LETTERS = {I, J, O, Q, W}` gồm 5 chữ bị loại trên toàn quốc, và chính việc loại `I`, `O`, `Q` làm việc sửa lỗi OCR khả thi. (Ghi chú hiệu chỉnh: con số "6 chữ bị loại" từng bao gồm `R` đã được sửa — `R` vẫn hợp lệ ở sê-ri thứ hai của xe máy và trong mã `RM`/`R`.)

**c) `POSITION_MASKS` và ký tự đại diện `?` ở chỉ số 3** — chi tiết cài đặt quan trọng nhất của khối hậu xử lý.

```python
POSITION_MASKS: Final[dict[str, str]] = {
    "car_5": "DDLDDDDD", "car_4": "DDLDDDD", "motorcycle_9": "DDL?DDDDD",
}
MASK_BY_LENGTH = {7: car_4, 8: car_5, 9: motorcycle_9}
```

`D` = **bắt buộc chữ số**, `L` = **bắt buộc chữ cái**, `?` = **ký tự đại diện, tuyệt đối không ép kiểu**; mặt nạ chọn **thuần tuý theo độ dài chuỗi đã làm sạch**. Hai kiểu biển xe máy cùng 9 ký tự nhưng khác nhau ở đúng vị trí này — kiểu mới cấp từ 15/08/2023 có sê-ri hai chữ cái (`29AA12345`), kiểu cũ trước 15/08/2023 (**vẫn còn hiệu lực lưu hành**) có sê-ri chữ + số (`29B112345`) — nên nếu tách thành `DDLLDDDDD` và `DDLDDDDDD` thì ép kiểu tại chỉ số 3 là bắt buộc, và hệ quả đã kiểm chứng bằng chạy thật là **một trong hai kiểu bị phá huỷ**:

```
29AA12345 + 'DDLDDDDDD' -> 29A412345   phá kiểu mới
29B112345 + 'DDLLDDDDD' -> 29BL12345   phá kiểu cũ
29AA12345 + 'DDL?DDDDD' -> 29AA12345   đúng
29B112345 + 'DDL?DDDDD' -> 29B112345   đúng
```

Chỉ số 3 của chuỗi 9 ký tự là **vị trí duy nhất trong toàn bộ hệ thống biển số Việt Nam mà cả chữ cái lẫn chữ số đều hợp lệ**, và chính *mặt nạ* — không phải tài liệu chú thích — mới quyết định hành vi của hàm; nhánh `?` vì vậy viết tường minh trong `apply_position_rules` chứ không để rơi vào `else`. Chuỗi 8 ký tự (nhập nhằng ô tô / xe máy kiểu cũ) **không cần mặt nạ thay thế** vì cả hai cách đọc áp cùng ràng buộc `DDLDDDDD`, chỉ khác cách diễn giải nhóm.

**d) Hai bảng ánh xạ nhầm lẫn và tính không đối xứng của chúng.**

```python
TO_DIGIT = {"O":"0","Q":"0","D":"0","I":"1","J":"1","L":"1",
            "Z":"2","A":"4","S":"5","G":"6","T":"7","B":"8"}
TO_LETTER = {"0":"D","1":"L","2":"Z","3":"B","4":"A","5":"S","6":"G","7":"T","8":"B"}
```

`TO_DIGIT` chỉ áp tại vị trí `D`, `TO_LETTER` chỉ tại vị trí `L`. **Ánh xạ không đối xứng, và đó chính là phát hiện trung tâm:** `O -> 0` đúng, nhưng `0 -> O` **không bao giờ đúng** vì `O` không phải chữ sê-ri hợp lệ; với cả `O` và `Q` đều bị loại, `D` là ứng viên đồng hình duy nhất còn lại, nên chiều đúng là `O -> 0` tại vị trí chữ số và `0 -> D` tại vị trí chữ cái — **tri thức miền thay thế cho dữ liệu**. Quy tắc an toàn thứ hai: **ký tự không có mục trong bảng thì giữ nguyên** — `3OB12E45` thành `30B12E45`, **không** thành `30B12?45`. **Cần ghi nhận trung thực về nguồn gốc hai bảng:** chúng suy từ lập luận hình dạng ký tự, **không phải từ đo đạc**, và vài cặp — đáng chú ý `L -> 1` — là phỏng đoán yếu; việc thay chúng bằng bảng trích từ **ma trận nhầm lẫn 36×36 đo được ở mức ký tự** thuộc Chương 6, và trình bày bảng hiện tại như một **giả thuyết cần kiểm chứng** vừa trung thực hơn vừa mạnh hơn về mặt học thuật.

**e) Thuật toán chuẩn hoá.** `VietnamesePlateNormalizer.normalize_detailed` thực hiện luồng sau:

![](figures/fig-ch5-03.png)

**Hình 5.3.** Thuật toán chuẩn hoá chuỗi biển số theo bộ luật ràng buộc vị trí

Ba nguyên tắc chịu lực: **thử regex *trước* khi sửa** vì chuỗi đã hợp lệ thì mọi chỉnh sửa chỉ có thể làm hỏng nó; **không bao giờ vứt bỏ** — chuỗi không sửa được vẫn trả về với `is_valid_format=False` và được lưu vào CSDL; **giữ chuỗi thô** vào `raw_ocr_text`, vì so sánh thô với đã chuẩn hoá là **cách duy nhất** đo được đóng góp của khối này. Kết quả là `NormalizationOutcome` bất biến mang chuỗi thô, chuỗi đã làm sạch, chuỗi cuối, cờ hợp lệ, kết quả phân loại và **danh sách bộ ba `(chỉ số, trước, sau)` cho từng ký tự đã sửa** — dấu vết kiểm toán mà chương đánh giá dựa vào.

**f) Xử lý nhập nhằng bằng số dòng.** Ô tô / xe máy kiểu cũ ở chuỗi 8 ký tự (`29B11234`) giải quyết được **một phần**; mã đặc biệt / xe máy kiểu mới ở chuỗi 9 ký tự (`29LD12345`) thì **không**. `line_count == 1` **chứng minh** chuỗi là biển ô tô vì xe máy luôn hai dòng, còn `line_count == 2` **không chứng minh gì cả** vì biển ô tô ngắn cũng hai dòng nên **cờ `is_ambiguous` vẫn được giữ** — khẳng định ngược lại là bịa ra thông tin mà đầu vào không chứa; `KindDecision` do đó trả *một tập ứng viên* kèm cờ. Thứ tự trong `PATTERNS_BY_KIND`: `DIPLOMATIC` đầu vì hình dạng không thể nhầm; `SPECIAL` trước các mẫu xe máy vì danh sách mã đặc biệt là đóng và hiếm; `MILITARY` cuối vì nó là trường hợp **nhận-ra-để-loại-trừ** — khớp `RE_MILITARY` nhưng **không** thuộc `CIVIL_KINDS` nên không bao giờ được báo là biển dân sự hợp lệ.

### 5.5.7. Ghép thành `ALPRPipeline` bằng tiêm phụ thuộc

`ALPRPipeline` là **đối tượng tổ hợp**: không giữ mô hình, không tự suy luận, chỉ sắp thứ tự giai đoạn, cắt ảnh ở giữa, **đo thời gian từng giai đoạn** và **cô lập lỗi ở mức từng biển số**. Ba giai đoạn được truyền vào hàm khởi tạo; `build_default_pipeline()` là tiện ích bọc quanh lớp mà lớp không biết đến, với ba lớp cụ thể import **bên trong thân hàm** — điều cho phép unit test dựng pipeline từ ba đối tượng giả mà không cần thời gian chạy ML. `stage_times` luôn đủ năm khoá cố định `STAGE_NAMES = ("detect", "crop", "ocr", "normalize", "total")`, làm một giai đoạn không chạy báo `0.0` thay vì vắng mặt; đây là thứ cho phép phân rã độ trễ (trên `best.pt`: OCR ~64,3%, detect ~34,2%) — không có phân rã thì con số tổng chỉ nói hệ thống chậm, không nói phải tối ưu chỗ nào — và cũng chính nó giúp phát hiện con số cũ "93,3%" là tạo tác của một lần đo trên hệ thống có lỗi crop.

**Chính sách thất bại có phân tầng**, khác nhau là chủ ý: ảnh không có biển số trả `PipelineResult` rỗng; OCR hỏng trên **một** biển thì biển đó trả `recognition=None` còn các biển khác vẫn xử lý; bộ phát hiện hỏng thì ném `DetectionError`; chuẩn hoá hỏng thì giữ nguyên `PlateRecognition` thô và ghi log `exception`. Bắt cả `Exception` chung ở tầng OCR là chủ ý vì một máy OCR bên thứ ba có thể ném bất cứ thứ gì. **Cắt ảnh kẹp lại lần hai** dù `BaseDetector` đã hứa, vì cắt ảnh là **nơi duy nhất** mà sai lệch một đơn vị tạo ra mảng rỗng âm thầm thay vì một lỗi; ảnh cắt trả về là **bản sao** chứ không phải khung nhìn, vì một view sẽ ghim toàn bộ khung hình video trong bộ nhớ. Cuối cùng, `normalize_detailed(raw, line_count=...)` không thuộc giao diện `BaseNormalizer` nên pipeline dùng `getattr` để **dò** nó và lùi về `normalize(raw_source)` nếu không có.

### 5.5.8. Nhận dạng họ biển và màu nền — `plate_color.py` và phép hợp nhất hai nguồn bằng chứng

**a) Vấn đề đã quan sát: thông tin được tính ra rồi bị vứt đi.** Ảnh biển đỏ quân đội `KV6938` được OCR đọc **đúng** ở độ tin cậy 0,999, nhưng giao diện hiển thị **"Sai định dạng biển số"** — sai về phát biểu chứ không sai về tính toán, vì biển quân đội **là** biển hợp lệ, chỉ nằm ngoài hệ đăng ký dân sự nên khớp `RE_MILITARY` mà không thuộc `CIVIL_KINDS` (mục 5.5.6f). Hai thông tin **được tính ra rồi bị vứt bỏ** trước khi tới CSDL: **họ biển** do `normalize_detailed` phân loại vào một trong chín giá trị `PlateKind` (`car`, `motorcycle_new`, `motorcycle_old`, `blue_car`, `blue_motorcycle`, `special`, `diplomatic`, `military`, `unknown` — tám họ cộng một giá trị "không xác định"), và **chuỗi hiển thị** do `format_for_display` dựng lại dấu phân cách như trên biển vật lý (`29E01566` → `29E-015.66`, `80001NG01` → `80-001-NG-01`). Bản sửa gồm hai phần: **giữ lại** những gì đã tính (mục d và 5.6.2), và **bổ sung một nguồn bằng chứng mà chuỗi ký tự về nguyên tắc không thể mang** — màu nền.

**b) Vì sao màu là nguồn bằng chứng *bổ trợ*, không phải thừa.** Hai nguồn **bù trừ nhau**: mỗi nguồn thấy đúng thứ nguồn kia mù.

| Loại xe | Màu nền | Họ biển suy từ chuỗi |
|---|---|---|
| Ô tô cá nhân | trắng | `car` |
| Ô tô kinh doanh vận tải | **vàng** | `car` — **trùng hệt** |
| Xe cơ quan nhà nước | xanh | `blue_car` |
| Xe quân đội | đỏ | `military` |
| Xe ngoại giao | **trắng** — trùng hệt | `diplomatic` |

Hai hàng in đậm là toàn bộ lý do mô-đun tồn tại: theo Thông tư 79/2024/TT-BCA, biển vàng xe kinh doanh vận tải mang **đúng cùng bố cục ký tự** với biển trắng xe cá nhân (`29E-015.66` hợp lệ cho cả hai) nên không regex nào phân biệt được vì **khác biệt không nằm trong chuỗi**; ngược lại biển ngoại giao nền trắng như biển cá nhân nên **màu cũng không đủ**. Chỉ *cặp* (chuỗi, màu) mới định danh được loại phương tiện.

**c) Thiết kế `classify_plate_color` — ba quyết định và các ngưỡng.** Hàm chuyển ảnh cắt sang **HSV**, đếm tỷ lệ điểm ảnh theo từng dải màu và chọn dải lớn nhất. *(1) Chỉ lấy mẫu vùng giữa* (`CENTRE_INSET = 0.18`, mỗi cạnh cắt bỏ 18%) vì **khung phát hiện hiếm khi ôm sát biển** nên dải ngoài thường chứa cản xe, kính chắn gió hoặc mặt đường — ca hỏng được ngăn là **một chiếc xe sơn đỏ đứng sau một biển trắng sẽ thắng phiếu bầu màu nếu lấy mẫu cả rìa ảnh**. *(2) Không loại trừ điểm ảnh của ký tự*, dù cách "đúng sách vở" là phân đoạn chữ rồi chỉ đếm nền: ký tự chiếm thiểu số diện tích và ngưỡng đặt theo *tỷ lệ trên vùng lấy mẫu* chứ không đòi *đa số tuyệt đối*, nên thêm bước phân đoạn glyph là đưa vào một khâu mong manh hơn hẳn khâu nó bảo vệ. *(3) Trả `UNKNOWN` thay vì đoán* (`MIN_DOMINANT_FRACTION = 0.30`), ngưỡng đặt theo **chiều sai lầm nào đắt hơn** — gọi sai màu là khẳng định một loại phương tiện không chứng minh được, còn thừa nhận không đọc được màu chỉ là ghi nhận trung thực một giới hạn.

Các ngưỡng còn lại theo dải HSV của OpenCV (H 0–179, S 0–255, V 0–255): `_YELLOW_HUE` 15–42; `_BLUE_HUE` 90–138; `_RED_HUE_LOW` / `_RED_HUE_HIGH` là 0–10 và 165–179 vì đỏ **vắt qua điểm 0** của vòng sắc độ; `_CHROMATIC_MIN_SATURATION` = 70 và `_CHROMATIC_MIN_VALUE` = 45 (dưới hai mức này là xám hoặc bóng tối, sắc độ vô nghĩa — thiếu hai cổng này thì nhiễu trên biển trắng bị **rải đều vào các dải màu**); `_WHITE_MAX_SATURATION` / `_WHITE_MIN_VALUE` = 65 / 105, định nghĩa "trắng" là **sáng và bão hoà thấp**, không dùng sắc độ. `ColorEstimate` mang cả **tỷ lệ từng dải, kể cả dải thua** để phục vụ khả năng kiểm chứng, và hàm **không bao giờ ném ngoại lệ**: ảnh rỗng, một kênh hay quá nhỏ đều trả `UNKNOWN` với độ tin cậy 0.

**d) Hợp nhất chuỗi và màu để phân giải nhập nhằng biển xanh — kèm một ràng buộc an toàn.** Chuỗi `80A12345` cho **bốn ứng viên ngang nhau** (`car`, `motorcycle_old`, `blue_car`, `blue_motorcycle`); normalizer chọn cái phổ biến nhất là `car` — đúng đa số trường hợp và **sai âm thầm với mọi xe cơ quan nhà nước**, vốn mang đúng các ký tự đó trên nền **xanh**. `refine_kind_with_color(outcome, color, line_count)` giải quyết qua bảng `_COLOR_PREFERRED_KINDS = {"blue": ("blue_car", "blue_motorcycle")}`. **Ràng buộc an toàn quan trọng hơn cả tác dụng của hàm:** màu chỉ được **nâng cấp một ứng viên mà chuỗi đã coi là hợp lý** — nếu phán quyết gốc không nằm trong tập ứng viên (`military`, `diplomatic`, `special`) thì hàm trả nguyên phán quyết gốc, nên **màu không thể bịa ra một họ biển mà bộ luật ký tự đã bác bỏ**: **một biển quân đội bị đọc nhầm màu thì vẫn là biển quân đội**. Ràng buộc phụ: khi họ biển ưu tiên có cả biến thể ô tô lẫn xe máy thì chọn theo `line_count`, và nếu `line_count` mâu thuẫn cả hai thì **trả về phán quyết gốc** — số dòng *đo được* từ hình học còn màu *suy ra* từ thống kê điểm ảnh, nên khi bất đồng, bên đo được thắng. Chỉ màu **xanh** nằm trong bảng vì đó là màu duy nhất mà chuỗi bó tay hoàn toàn; vàng không đổi *họ* biển mà chỉ đổi *mục đích sử dụng* của cùng họ `car` nên được lưu như trường độc lập.

**e) Độ chính xác đo được của bộ nhận màu.** Đo trên **`nguyenluanai/license-plate-color` v4** (Roboflow Universe, **CC BY 4.0**) — ảnh biển đã cắt sẵn, **có nhãn màu do người gán**, và **bộ phân loại chưa từng được hiệu chỉnh theo bộ này** (ngưỡng ở mục c đặt từ ảnh cắt do chính bộ phát hiện của đồ án sinh ra), nên đây là phép đo **ngoài dữ liệu hiệu chỉnh**. Kết quả trên 1.565 ảnh dùng được (`docs/reports/19-color-accuracy.json`):

| Lớp nhãn người gán | Số ảnh | Đúng | Độ chính xác |
|---|---:|---:|---:|
| Biển vàng | 694 | 684 | **98,56%** |
| Biển trắng | 808 | 787 | **97,40%** |
| Biển xanh | 63 | 61 | **96,83%** |
| **Tổng** | **1.565** | **1.532** | **97,89%** |

Ba điều phải nói kèm. **542 ảnh đã bị loại khỏi phép tính, và lý do loại phải nêu rõ:** toàn bộ lớp `bien_unknown` — ảnh đêm hoặc hồng ngoại lỗi cân bằng trắng, ám tím, mà **chính người gán nhãn cũng không đọc được màu nền**; việc loại chúng được ghi tường minh trong tệp báo cáo chứ không ẩn đi. **Dạng lỗi chủ đạo đã được định vị:** 21 ảnh biển trắng bị gọi thành xanh, chiếm hai phần ba tổng số 33 ca sai — hệ quả của việc bộ này có mức bão hoà rất thấp ở lớp "trắng", khiến một số điểm ảnh ám lạnh vượt được cổng `_CHROMATIC_MIN_SATURATION`. **Phạm vi phép đo hẹp hơn phạm vi mô-đun:** bộ này **không chứa biển đỏ và không chứa biển ngoại giao**, nên hai nhánh đó **chưa có số đo** — chỉ được kiểm chứng bằng ảnh lẻ và unit test; hạn chế thật, nêu lại ở mục 7.3.

> **Ghi chú phạm vi bắt buộc.** Mọi ảnh trong bộ `license-plate-color` đều bị **kéo méo về khuôn 640×640** trước khi tải lên. Bộ này vì vậy **không dùng được để đánh giá OCR**, vì `estimate_line_count` (mục 5.5.5b) dựa trên tỷ lệ khung hình và phép kéo phá huỷ chính đại lượng đó. Màu nền thì **không** bị phép kéo làm thay đổi, nên câu hỏi về màu là câu hỏi duy nhất mà bộ này trả lời được — và nó chỉ được dùng cho đúng câu hỏi đó.

---

## 5.6. Cài đặt backend

### 5.6.1. Cấu trúc phân tầng và luồng phụ thuộc

Backend gồm 21 mô-đun Python (không kể tám `__init__.py`), trong đó 19 mô-đun ứng dụng và 2 tệp Alembic, tổ chức thành năm tầng với **luồng phụ thuộc một chiều nghiêm ngặt**:

![](figures/fig-ch5-04.png)

**Hình 5.4.** Cấu trúc phân tầng của backend và luồng phụ thuộc một chiều

Ba quy tắc được cài đặt và kiểm chứng. **Router không viết truy vấn** — mọi truy cập dữ liệu qua repository, nên một thay đổi lược đồ có bán kính ảnh hưởng bằng một tệp thay vì bằng số endpoint. **Repository `flush`, không bao giờ `commit`**: lưu một tác vụ cùng sáu biển số là **một** thao tác logic, nên `commit` sau mỗi `create` sẽ để lại ba biển số và một tác vụ tự nhận đã hoàn tất — trạng thái không đoạn mã nào sau đó phát hiện được là hỏng vì từng dòng riêng lẻ đều hợp lệ; `flush` vẫn điền được khoá chính tự tăng và làm **vi phạm ràng buộc nổi lên ngay tại dòng gây ra nó**, còn ranh giới giao dịch thuộc tầng service. **Khoá sắp xếp qua danh sách cho phép tường minh** chứ không qua `getattr(model, name)`, vì khoá đến từ chuỗi truy vấn nên `getattr` biến `?sort_by=metadata` thành lỗi 500 hình dạng `AttributeError` và `?sort_by=job` thành join ngoài ý muốn, còn ánh xạ khiến khoá lạ thành lỗi 400 sạch sẽ; `MAX_PAGE_SIZE = 200` chặn cứng `?page_size=1000000`. Tầng `core/` (cấu hình, log, cây ngoại lệ) được mọi tầng dùng nhưng không phụ thuộc tầng nào.

### 5.6.2. Mô hình dữ liệu và di trú

![](figures/fig-ch5-05.png)

**Hình 5.5.** Mô hình dữ liệu sau ba lần di trú Alembic

Trạng thái kiểm chứng bằng Alembic: `detection_history` có **21 cột** (18 cột ban đầu cộng ba cột do di trú `0002_plate_kind_and_color` bổ sung), `detection_job` có **11 cột**. Bốn trường mang ý nghĩa vượt việc lưu trữ đơn thuần. **`raw_ocr_text` bên cạnh `plate_number`:** chuỗi OCR lưu **hai lần**, vì không có cột thô thì **không có cách nào đo được đóng góp của hậu xử lý**; thuộc tính dẫn xuất `was_corrected` là dạng theo-từng-dòng của phép đo đó. **`ocr_confidence` tách khỏi `confidence`:** hai độ tin cậy **không bao giờ được gộp** — một là mức chắc chắn của *bộ phát hiện* rằng nó đang nhìn vào một biển số, một là mức chắc chắn của *OCR* về các ký tự; tên cột đặt trùng tên thuộc tính trên `PlateDetection`/`PlateRecognition` để tầng lưu trữ **sao chép từng trường** thay vì phiên dịch. **`source_job_id` trên mọi dòng, không cho phép NULL:** không có khoá nhóm thì một ảnh ba xe thành ba dòng không liên hệ và `GET /api/statistics` báo "3 lượt nhận dạng" trong khi câu trả lời trung thực là "1 lượt tải lên chứa 3 biển số". **`plate_line_count`** (`1` hoặc `2`) cho phép báo cáo độ chính xác **tách riêng biển một dòng và hai dòng**; không có nó, con số tổng hợp sẽ che giấu đúng điểm khó nhất của bài toán.

**Quy tắc NULL:** *một lần phát hiện vẫn đáng giữ ngay cả khi OCR không đọc được gì* — hộp bao và độ tin cậy luôn có mặt nên `NOT NULL`, mọi cột dẫn xuất từ OCR cho phép NULL, vì loại bỏ những dòng này sẽ xoá đúng các thất bại mà chương đánh giá cần đếm và làm độ chính xác nhận dạng hoàn hảo *do cách xây dựng*. **Chỉ mục:** 5 chỉ mục, trong đó một chỉ mục **tổ hợp** `(input_type, detected_time)` phục vụ cả bộ lọc lẫn thứ tự của truy vấn mặc định màn hình lịch sử; đo được p95 = **18,71 ms** trên 10.000 bản ghi so với chỉ tiêu NFR-P6 là 500 ms. **Tám ràng buộc CHECK** mức CSDL (5 trên `detection_history`, 3 trên `detection_job`), ví dụ `CHECK (plate_line_count IS NULL OR plate_line_count IN (1, 2))`, `CHECK (ocr_confidence IS NULL OR (ocr_confidence >= 0.0 AND ocr_confidence <= 1.0))`, `CHECK (bbox_w > 0 AND bbox_h > 0)`; kiểu liệt kê lưu dạng văn bản thuần kèm `CHECK` vì SQLite không có enum.

**Ba cột phân loại phương tiện — di trú `0002_plate_kind_and_color`.** Mục 5.5.8a đã nêu: biển quân đội đọc đúng ở độ tin cậy 0,999 được lưu với `is_valid_format = 0` và **không gì khác**, không phân biệt được với biển đọc hỏng, vì lược đồ ban đầu không có chỗ đặt câu trả lời cho *"vì sao chuỗi này không hợp lệ theo hệ dân sự"*. Di trú thêm `plate_kind` (`String(16)`, từ `NormalizationOutcome.decision.kind` sau `refine_kind_with_color`), `plate_color` (`String(16)`, từ `ColorEstimate.color`) và `plate_color_confidence` (`Float`) — lặp lại nguyên tắc đã dùng cho cặp `raw_ocr_text`/`plate_number`: **thông tin đã được tính ra thì phải được ghi lại**. `String(16)` dùng chung hằng `_ENUM_LENGTH`, và giá trị dài nhất cần lưu là `motorcycle_new` — 14 ký tự. **Cả ba cột cho phép NULL, không có giá trị mặc định:** các dòng ghi **trước** khi di trú chạy **thật sự không có giá trị**, nên điền lùi một giá trị đoán sẽ tạo dòng **không phân biệt được với một phép đo thật**; `NULL` nghĩa là *chưa bao giờ đo*, còn `"unknown"` nghĩa là *đã đo và không kết luận được* — **một giá trị vắng mặt phải trông như vắng mặt.** SQLite hỗ trợ `ADD COLUMN` trực tiếp cho cột NULL nên `upgrade()` không cần `batch_alter_table` và **không ràng buộc nào bị mất âm thầm**.

### 5.6.3. Tầng service và cách tiêm pipeline AI

**Hợp đồng pipeline biểu diễn bằng `typing.Protocol`, không phải ABC**: một ABC phải nằm trong `backend` và được `ALPRPipeline` **kế thừa**, tức `ai` phải import từ `backend` — đúng chiều mũi tên NFR-M1 cấm; `Protocol` là cấu trúc nên `ALPRPipeline` thoả mãn nhờ *có đúng các phương thức* (`name`, `is_ready`, `process`) mà không biết tệp này tồn tại, và giao diện giữ **cố ý nhỏ** vì giao diện lớn hơn sẽ trói tầng service vào chính những chi tiết mà tầng AI cần tự do sắp xếp lại. **Điểm tiêm ở `api/deps.py`:** pipeline dựng **một lần** lúc khởi động và gắn vào `app.state` (nạp trọng số tốn vài giây và hàng trăm megabyte nên dựng theo yêu cầu sẽ bắt mọi lần tải lên trả chi phí thuộc về tiến trình), nhờ đó kiểm thử chỉ cần `app.dependency_overrides[get_pipeline] = lambda: FakePipeline()` mà không phải vá khỉ. `DetectionService._run_pipeline` là **điểm dịch ngoại lệ** của NFR-M1: `ALPRError` mang thông điệp tiếng Anh cho lập trình viên và không biết gì về HTTP, để nó thoát ra sẽ rò rỉ văn bản đó hoặc tạo lỗi 500 kèm vết ngăn xếp.

**Ba luồng nghiệp vụ.** `detect_image` đồng bộ, một lần tải lên = một tác vụ, ảnh không có biển số trả **HTTP 200 với danh sách rỗng**. `detect_frame` coi một **phiên** webcam là một tác vụ chứ không phải một tác vụ mỗi khung, và khung hình **không** lưu xuống đĩa. `create_video_job` + `process_video_job` bất đồng bộ, trả `202 Accepted` ngay khi bytes đã xuống đĩa. **Chi tiết luồng video:** lấy mẫu theo `frame_stride` (mặc định 5) vì ở 30 fps một biển hiện diện qua hàng chục khung liên tiếp; **khử trùng lặp trước khi ghi**, khoá là chuỗi đã nhận dạng và giữ lần đọc tin cậy nhất, còn biển OCR không đọc được thì khoá theo vị trí lượng tử hoá về lưới thô `f"unread@{(bbox.x + bbox.width // 2) // 32},{(bbox.y + bbox.height // 2) // 32}"` để một biển đứng yên không đọc được co lại thành một dòng; ghi tiến độ mỗi 10 khung (`_PROGRESS_COMMIT_EVERY = 10`) vì commit mỗi khung biến video hai phút thành hàng nghìn giao dịch cạnh tranh với truy vấn đọc, còn commit chỉ ở cuối để thanh tiến độ đứng yên ở 0 suốt tác vụ; đọc kích thước khung **trước** `capture.release()` vì sau khi giải phóng các thuộc tính này trả 0 trên mọi backend, khiến hệ thống báo video 0×0 và mọi hộp bao frontend co giãn theo đó sụp về không; tiến độ khi không biết tổng số khung trả **0,99** thay vì 1,0 vì báo 1,0 sớm khiến client ngừng hỏi và bỏ lỡ kết quả; và kiểm tra huỷ bằng cách đọc lại từ CSDL (`db.refresh(job, attribute_names=["status"])`) vì lệnh huỷ đến trên phiên khác.

### 5.6.4. `UnavailablePipeline` — quyết định cài đặt đáng chú ý

Giai đoạn trước, khi mô hình chưa huấn luyện, hệ thống chạy `StubPipeline` — pipeline **bịa ra kết quả có cấu trúc hợp lệ**, chính đáng lúc đó vì API, lược đồ, thống kê và frontend đều cần thứ gì đó để trao đổi; stub bảo đảm **hình dạng**, không bảo đảm **sự thật**. Vấn đề nằm ở chỗ khác: **stub được cài như phương án lùi khi không nạp được mô hình**, nghĩa là một triển khai cấu hình sai sẽ trả lời mọi lần tải lên bằng một biển số thuyết phục nhưng hư cấu — chế độ hỏng **trông giống như thành công**, loại nguy hiểm nhất trong hệ thống có ghi dữ liệu vào CSDL.

| Lớp | Khi nào được cài | Hành vi `process()` | `is_ready` | `/health` |
|---|---|---|---|---|
| `ALPRPipeline` | Bình thường: có trọng số, có thư viện | Nhận dạng thật | `True` | `ok` |
| `UnavailablePipeline` | **Mặc định khi hỏng**: thiếu trọng số hoặc dựng giai đoạn ném ngoại lệ | **Ném `ALPRError`, không bịa gì** | `False` | `degraded` |
| `StubPipeline` | **Chỉ khi `ALPR_USE_STUB` được đặt tường minh** | Bịa kết quả xác định theo hash ảnh | `False` | `degraded` |

Hành vi đúng khi trọng số thiếu là **dịch vụ vẫn khởi động**, `/health` báo `model_loaded = false`, mỗi yêu cầu nhận dạng trả lỗi sạch sẽ — vẫn khởi động là chủ ý, vì một tiến trình từ chối khởi động không nói cho người vận hành biết *vì sao*. `StubPipeline` còn trong mã nhưng **ra khỏi đường chạy chính**, và `build_pipeline` ghi log `WARNING` nói rõ *"Every result this process returns is invented."* Trạng thái kiểm chứng: `/health` trả `model_loaded = true` với `engine` là `yolo:...+paddleocr-PP-OCRv5-mobile`.

### 5.6.5. REST API — bảng endpoint thực tế

Đếm từ `backend/api/routes/` và đối chiếu OpenAPI sinh từ chính đối tượng ứng dụng: **10 thao tác HTTP trên 9 đường dẫn** (`/api/history/{detection_id}` mang cả `GET` và `DELETE` nên OpenAPI gom vào một mục `paths`).

| # | Phương thức | Đường dẫn | Mã | Mô tả |
|:-:|---|---|:-:|---|
| 1 | `GET` | `/health` | 200 | Trạng thái sẵn sàng: `status`, `database_connected`, `model_loaded`, `uptime_seconds`, `version` |
| 2 | `POST` | `/api/detect/image` | **200** | Nhận dạng đồng bộ trên ảnh tĩnh |
| 3 | `POST` | `/api/detect/video` | **202** | Xếp hàng video để xử lý nền |
| 4 | `POST` | `/api/detect/frame` | **200** | Nhận dạng một khung hình webcam |
| 5 | `GET` | `/api/jobs/{job_id}` | 200 | Trạng thái và tiến độ của một tác vụ |
| 6 | `GET` | `/api/history` | 200 | Danh sách có tìm kiếm, lọc, sắp xếp, phân trang |
| 7 | `GET` | `/api/history/export` | 200 | Xuất CSV các bản ghi khớp bộ lọc |
| 8 | `GET` | `/api/history/{detection_id}` | 200 | Chi tiết một bản ghi |
| 9 | `DELETE` | `/api/history/{detection_id}` | **204** | Xoá một bản ghi |
| 10 | `GET` | `/api/statistics` | 200 | Số liệu thống kê tổng hợp và chuỗi số liệu theo ngày |

*(10 dòng = 10 thao tác. `/health` nằm ngoài tiền tố `/api`; dưới `/api` có 8 đường dẫn mang 9 thao tác. Cách đếm chi tiết ở `docs/manuals/api-documentation.md` mục 4.2.)*

Ba lựa chọn mã trạng thái đáng giải thích: **`202` cho video** vì một video 60 giây mất khoảng 200 giây trên CPU và không client HTTP nào chờ lâu vậy, nên `202` phát biểu đúng ngữ nghĩa "đã nhận, chưa xong"; **`200` cho ảnh không có biển số** thay vì `404`/`422` vì đó là **kết quả hợp lệ** và trả 4xx sẽ xoá mọi trường hợp âm khỏi thống kê; **`204 No Content` cho xoá**. `/health` ở gốc thay vì dưới `/api`, lý do ghi trong mã: *"một health check di chuyển khi tiền tố API thay đổi thì không phải là một health check tốt"*. Tài liệu OpenAPI sinh tự động tại `/docs`, `/redoc`, `/openapi.json`, nhưng ba đường dẫn này do **FastAPI tự sinh** nên **không tính vào 10 endpoint**. Toàn bộ 10 endpoint đã kiểm chứng bằng lời gọi HTTP thật với kiểu TypeScript khớp từng trường (thực hiện trước hai đợt thu gọn phạm vi giao diện 2026-07-20; hợp đồng cả 10 endpoint không đổi kể từ đó — mục 5.7.2).

### 5.6.6. Xử lý lỗi, log có cấu trúc và `request_id`

**Mỗi ngoại lệ mang hai mô tả cho hai đối tượng độc giả:** `user_message` — **tiếng Việt**, ngắn, có hành động, đi vào thân phản hồi HTTP; `internal_detail` — tiếng Anh, kỹ thuật, **chỉ vào log**. Giữ chúng là hai thuộc tính riêng biệt loại bỏ chế độ hỏng thường gặp, nơi chuỗi kỹ thuật đến tay người dùng vì người viết câu `raise` chỉ có một trường thông điệp. Cây ngoại lệ: `APIError` (gốc, mang `status_code`) với `ValidationError` 400, `NotFoundError` 404, `FileTooLargeError` 413, `UnsupportedMediaTypeError` 415, `ProcessingError` 500. **Bốn bộ xử lý ngoại lệ được đăng ký** — `APIError`, `RequestValidationError`, `StarletteHTTPException` (404/405 do khung sinh) và một bộ **bắt tất cả** cho `Exception`; bộ cuối quan trọng nhất vì không có nó thì ngoại lệ ngoài dự kiến sẽ do bộ xử lý mặc định của máy chủ hiển thị, và ở cấu hình debug điều đó gồm cả vết ngăn xếp (NFR-S4). Thân lỗi dựng bởi `APIError.to_response_dict(request_id)` **từ danh sách khoá an toàn tường minh** nên một trường mới thêm vào ngoại lệ không thể rò rỉ theo mặc định; riêng `RequestValidationError` được viết lại vì thân lỗi gốc của FastAPI liệt kê mọi trường sai kèm vị trí và giá trị vi phạm — tuyệt vời cho lập trình viên, sai với người dùng cuối.

**Log có cấu trúc: mỗi dòng là một đối tượng JSON**, vì log tác vụ video xen kẽ log các lần tải lên đồng thời và văn bản thuần không tách trở lại được; với JSON, `jq 'select(.request_id == "3f2a...")' backend.log` dựng lại toàn bộ câu chuyện của một yêu cầu. **`request_id` đi trong `ContextVar`, không phải tham số hàm**, vì giá trị truyền tay phải xâu qua service, repository và adapter pipeline và mọi hàm quên chuyển tiếp sẽ âm thầm làm đứt vết. Middleware **tôn trọng header `X-Request-ID` đến từ ngoài**, và cả `X-Request-ID` lẫn `X-Process-Time` khai báo trong `expose_headers` của CORS vì nếu không trình duyệt sẽ giấu chúng khỏi frontend. Hàm `safe_extra()` xử lý việc thư viện `logging` **từ chối** một số tên khoá trong `extra=` (`filename`, `module`, `lineno`...) và ném `KeyError` — kiểu hỏng ném **bởi chính lời gọi log**, thay thế đúng thông tin chẩn đoán bằng một ngoại lệ không liên quan, đúng lúc log quan trọng nhất; `safe_extra` **đổi tên** khoá trùng (tiền tố `ctx_`) thay vì bỏ. Log ghi ra `stdout` thay vì tệp vì runtime container sở hữu việc thu thập và luân chuyển log.

### 5.6.7. Ba lỗi thực tế đã gặp và sửa trong quá trình cài đặt

Ba lỗi dưới đây được ghi lại vì cả ba đều **đi qua được kiểm thử đơn vị** — minh hoạ rằng test xanh không phải bằng chứng đầy đủ khi lỗi nằm ở ranh giới giữa mã và môi trường.

**a) pydantic-settings JSON-decode trường list *trước* validator.** Dòng `.env` tự nhiên nhất — `ALPR_CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173` — làm dịch vụ **sập lúc khởi động** với `json.JSONDecodeError`, vì `pydantic-settings` chạy `json.loads` trên giá trị thô của trường `list[str]` **trước** mọi validator. *Vì sao unit test vẫn xanh:* nguồn `init` **không** JSON-decode, nên `Settings(cors_origins="a,b")` **pass** trong khi dịch vụ triển khai với đúng giá trị đó trong `.env` thì **từ chối khởi động** — test và môi trường chạy đi qua hai nhánh mã khác nhau của cùng một thư viện. *Cách sửa:* alias `StringList = Annotated[list[str], NoDecode]` cho ba trường `cors_origins`, `allowed_image_types`, `allowed_video_types`, đưa giá trị thô thẳng tới `_split_list` vốn nhận **cả hai** dạng dấu phẩy và JSON; validator `_reject_wildcard_origin` từ chối `"*"` và danh sách rỗng ngay lúc khởi động.

**b) SQLite âm thầm nuốt `tzinfo`.** Mọi mốc thời gian hiển thị **lệch 7 giờ** trên trình duyệt ở UTC+7, vì SQLite **không có kiểu datetime bản địa** và định dạng chuỗi của SQLAlchemy **đánh rơi phần bù múi giờ**: `2026-07-19 12:00:00+00:00` quay về naive `2026-07-19 12:00:00` — **không lỗi, không cảnh báo**. Hai hệ quả không tự thông báo: `utcnow() - row.created_at` ném `TypeError: can't subtract offset-naive and offset-aware datetimes`, và mốc naive tuần tự hoá sang JSON **không có hậu tố `Z`** nên trình duyệt đọc là giờ **địa phương**. *Vì sao lọt qua rà soát:* một bản ghi tạo lúc 14:30 hiển thị 21:30 vẫn là mốc bình thường, vẫn trong ngày, vẫn đúng thứ tự tương đối — không có gì trông sai, nhưng mọi phân tích thời gian đều vô hiệu. *Cách sửa:* `TypeDecorator` tên `UtcDateTime` (`impl = DateTime(timezone=True)`, `cache_ok = True`) chuẩn hoá về UTC khi ghi và gắn lại UTC khi đọc, đóng khoảng trống ở **mức kiểu**; hàm `utcnow()` phía Python thay `CURRENT_TIMESTAMP` của SQLite vì bản SQLite sinh chuỗi **naive** độ phân giải một giây, quá thô để sắp thứ tự các lần phát hiện từ cùng một video.

**c) Log tiếng Việt làm sập console `cp1252` trên Windows.** Một dòng log tiếng Việt ném `UnicodeEncodeError` **bên trong cỗ máy logging**, vì console Windows mặc định dùng `cp1252` trong khi `JsonFormatter` đặt `ensure_ascii=False` — chủ ý, để log giữ chữ tiếng Việt đọc được. Đây là **sự cố trong lúc đang báo cáo sự cố**: ngoại lệ mã hoá **phá huỷ chính thông tin chẩn đoán** đang được ghi. Container Linux dùng UTF-8 mặc định nên lỗi **chỉ xuất hiện trên Windows** và **sống sót qua toàn bộ quá trình kiểm thử trong Docker** — chạy `docker compose up` thấy mọi thứ hoạt động không hề là bằng chứng rằng lỗi không tồn tại. *Cách sửa:* `_utf8_stdout()` gọi `reconfigure(encoding="utf-8", errors="backslashreplace")` trước khi gắn handler, với `errors="backslashreplace"` là **tuyến phòng thủ thứ hai**, và lời gọi bọc trong `try/except (ValueError, OSError)`.

**Điểm chung:** cả ba nằm ở **ranh giới giữa mã và môi trường** — nguồn cấu hình, tầng lưu trữ, bảng mã luồng đầu ra — và cả ba đi qua được unit test; đây là lập luận cụ thể cho việc bộ kiểm thử phải gồm cả kiểm thử tích hợp chạy trên đường dẫn thật (`.env` thật, CSDL thật, `stdout` thật).

---

## 5.7. Cài đặt frontend

### 5.7.1. Cấu trúc và bộ component dùng chung

Ứng dụng React + TypeScript dựng bằng Vite, gồm **3 trang** và 48 mô-đun `.tsx`/`.ts`: `pages/` (ImageDetection ở trang chủ `/`, VideoDetection `/video`, History `/history`); `components/ui/` 15 component nguyên thuỷ; `components/detection/image/` (BoundingBoxOverlay, DetectionSummary, ImageUploadPanel, PlateResultCard) và `.../video/` (JobProgressPanel, VideoResultPanel, VideoUploadPanel); `components/history/` (HistoryTable, HistoryFilters, HistoryDetailModal, DeleteHistoryDialog, useHistoryQuery); cùng `services/api.ts`, `types/index.ts` (472 dòng), `hooks/` (useDebounce, useJobPolling) và `lib/` (cn, constants, format).

> **Ghi chú thay đổi phạm vi 2026-07-20 — hai đợt liên tiếp trong cùng một ngày.**
>
> **Đợt 1** gỡ `pages/WebcamDetection.tsx`, `components/detection/webcam/` (CameraStage, CameraControls, CaptureMetricsPanel, SessionPlateTable, useCameraStream, useFrameCaptureLoop) và hàm `detectFrame`; ở tầng API, `POST /api/detect/frame` **không đổi** (endpoint, test, benchmark). **Đợt 2** gỡ `pages/Dashboard.tsx`, cả thư mục `components/dashboard/` (10 tệp: 8 component + `chartTheme.ts` + `index.ts`), `hooks/useApi.ts`, hai hàm `getStatistics` và `getHealth`, và gói npm `recharts`; `GET /api/statistics` và `GET /health` **vẫn có kiểm thử tích hợp** ở `tests/integration/test_api_statistics.py` và `test_api_health.py`.
>
> Đợt 1 đồng thời chuyển trang chủ từ Dashboard sang Nhận dạng ảnh. Sau đợt 2, số mô-đun frontend giảm từ 60 xuống **48** (12 tệp bị gỡ), mọi đường dẫn không khớp `Navigate` về `/`, và mã nguồn cả hai trang còn trong lịch sử git. Hệ quả về yêu cầu — FR-3.1/FR-3.4 và **FR-4.1 (mức Must)**/FR-4.2 chuyển sang Won't — phân tích ở mục 4.1.3(a). Các kiểu `Statistics`, `StatisticsQuery`, `HealthStatus`, `InputTypeBreakdown` **giữ lại có chủ đích** vì là bản sao hợp đồng của hai endpoint vẫn đang phục vụ.

Bộ nguyên thuỷ `ui/` gồm `Badge`, `Button`, `Card`, `ConfidenceBar`, `EmptyState`, `ErrorState`, `FileDropzone`, `Modal`, `Pagination`, `PlateChip`, `ProgressBar`, `Skeleton`, `Spinner`, `StatCard`, `Table`; hai trong số này mã hoá tri thức miền chứ không chỉ hình thức — `PlateChip` dùng phông đơn cách với khoảng cách chữ mở rộng để `0` và `O` phân biệt được bằng mắt, `ConfidenceBar` hiển thị độ tin cậy kèm nhãn ngưỡng thay vì một con số trần. Trạng thái kiểm chứng (đo lại 2026-07-20 sau đợt gỡ thứ hai): `tsc --noEmit` sạch, ESLint sạch, `vite build` thành công trong 2,15 giây với **1.670 mô-đun** — giảm từ 2.381 mô-đun của bản trước; gói tải về giảm từ khoảng **730 KB xuống 328,8 KB (−55%)** phần lớn nhờ gỡ `recharts`, từng chunk là `index` 178,11 KB, `api` 54,92 KB, `History` 30,80 KB, CSS 28,82 KB, `ImageDetection` 16,42 KB, `VideoDetection` 15,33 KB, cùng ba chunk nhỏ dưới 5 KB.

### 5.7.2. Tầng gọi API và ánh xạ kiểu dữ liệu

`services/api.ts` là **nơi duy nhất trong frontend biết về axios hoặc mã trạng thái HTTP**: component nhận về hoặc dữ liệu đã có kiểu, hoặc một promise bị từ chối mang `ApiError` đã chuẩn hoá. **Sáu hàm gọi API** ứng một–một với sáu trong 10 endpoint (`detectImage`, `detectVideo`, `getJob`, `getHistory`, `getHistoryDetail`, `deleteHistory`), cộng hai hàm dựng URL là `exportHistoryUrl` (phủ endpoint thứ bảy `GET /api/history/export`, tải bằng điều hướng trực tiếp chứ không qua axios) và `fileUrl`. **Ba endpoint còn lại không còn hàm gọi phía giao diện**, đều do hai đợt thu gọn 2026-07-20 và đều vẫn hoạt động nguyên vẹn ở backend: `POST /api/detect/frame` (hàm cũ `detectFrame`, đợt 1) nay do client thời gian thực gọi trực tiếp; `GET /api/statistics` (hàm cũ `getStatistics`, đợt 2) nay do script phân tích, kiểm thử tích hợp và client bên ngoài gọi; `GET /health` (hàm cũ `getHealth`, đợt 2) nay do `HEALTHCHECK` của Docker, kiểm thử tích hợp và giám sát vận hành gọi. Số hàm gọi giảm từ tám xuống **sáu**; cần phân biệt rõ **hàm gọi ở tầng giao diện bị xoá**, còn **endpoint thì không**.

**Không hostname nào viết cứng:** origin đọc từ biến môi trường lúc build và **mặc định rỗng**, khiến mọi yêu cầu là cùng-origin — một triển khai được **cấu hình**, không phải **build lại**; `resolveOrigin()` chạy `configured.replace(/\/+$/, '').replace(/\/api$/, '')` vì giá trị cấu hình kết thúc bằng `/api` là đang chỉ *API base* chứ không phải *origin*, và nếu không cắt thì endpoint `/health` — **chủ ý nằm ngoài tiền tố `/api`** — không còn với tới được. **Ánh xạ kiểu:** `types/index.ts` khai báo `DetectionResult`, `DetectionResponse`, `DetectionHistory`, `DetectionJob`, `Statistics`, `StatisticsQuery`, `HealthStatus`, `InputTypeBreakdown`, `ApiErrorResponse` cùng các kiểu hợp `InputType`, `JobStatus`, `PlateLineCount`; riêng `PlateLineCount` khai báo là `1 | 2` chứ không phải `number` nên trình biên dịch bắt ngay tại chỗ mọi phép gán giá trị khác — cách kiểu tĩnh mã hoá lại ràng buộc `CHECK (plate_line_count IN (1,2))` của CSDL ở đầu bên kia đường truyền. Toàn bộ 10 endpoint đã kiểm chứng bằng HTTP thật với kiểu khớp từng trường **trước 2026-07-20**, vẫn còn hiệu lực vì hợp đồng không đổi kể từ đó; ba endpoint nay không có trang gọi tới tiếp tục được kiểm chứng bằng **kiểm thử tích hợp ở backend**.

### 5.7.3. Hàng đợi một khe ở trang webcam (đã gỡ khỏi giao diện 2026-07-20)

> **Ghi chú thay đổi phạm vi:** trang webcam cùng toàn bộ mã mô tả trong mục này đã được **gỡ khỏi frontend** ngày 2026-07-20 theo quyết định thu gọn phạm vi demo; mã nguồn còn trong lịch sử git. Năng lực thời gian thực giữ nguyên ở tầng API (`POST /api/detect/frame`), và kỹ thuật hàng đợi một khe dưới đây trở thành **khuyến nghị bắt buộc cho bất kỳ client nào** gọi endpoint đó (mục 4.1.2d). Mục được giữ lại như mô tả kỹ thuật ở thì quá khứ vì lập luận thiết kế vẫn đúng và cần cho việc tái lập.

Suy luận chạy trên CPU ở khoảng **5 FPS**, nên một bộ đếm giờ ngây thơ kích hoạt mỗi 700 ms và `await` từng phản hồi sẽ, ngay khi một khung mất 900 ms, khởi động yêu cầu thứ hai *trước khi* yêu cầu thứ nhất trở về; từ đó tồn đọng chỉ có tăng và tab cuối cùng đứng hình. **Cách giải quyết: một khe duy nhất** — `useFrameCaptureLoop.ts` giữ đúng một yêu cầu đang bay, và nếu `inFlightRef` đang được đặt thì khung hình bị **bỏ qua** (tăng `framesSkipped`) chứ không xếp hàng, với chú thích trong mã: *"Luật một khe. Bỏ qua là hành vi ĐÚNG, không phải phương án lùi."* Lập luận cốt lõi: **bỏ một khung hình không tốn gì cả** vì khung tiếp theo cách 700 ms và dù sao cũng cập nhật hơn, trong khi xếp hàng thì tốn tất cả. Giải phóng khe đặt trong `finally` là chi tiết chịu lực: nếu đặt trong `try`, một khung lỗi sẽ để `inFlightRef` mắc kẹt ở `true` và **khoá vòng lặp vĩnh viễn**. Hai cơ chế bảo vệ đi kèm: **tự tạm dừng sau 5 lần lỗi liên tiếp** (`MAX_CONSECUTIVE_ERRORS = 5`), không có nó thì một backend đã ngừng hoạt động bị gọi mỗi 700 ms suốt thời gian tab mở; và **`AbortController` huỷ yêu cầu đang bay**, với huỷ chủ động nhận biết qua `controller.signal.aborted` và **không** báo là lỗi.

**Một `job_id` cho cả phiên:** định danh từ phản hồi đầu được giữ trong ref và gửi lại cùng mọi khung sau đó, vì nếu không thì một lần chụp ba mươi giây được ghi nhận là khoảng 40 lượt tải lên thay vì 1 — **không có gì hỏng một cách hữu hình**, bảng điều khiển chỉ âm thầm trở nên sai. **FPS tính trên cửa sổ trượt 5 giây** thay vì từ lúc bắt đầu, để một buổi trình diễn chạy chậm mười giây đầu không kéo con số xuống suốt phiên. Hàm `mergeSessionPlates` được **export riêng** để kiểm thử trực tiếp; khoá khử trùng bỏ mọi ký tự không phải chữ-số và viết hoa phần còn lại nên `"90C-76040"`, `"90c 76040"`, `"90C76040"` gộp một dòng, nhưng đây là **khoá**, không bao giờ là giá trị hiển thị: ký tự **không** được "sửa" ở đây — một `O` do OCR đọc ra vẫn là `O`, vì âm thầm biến nó thành `0` sẽ **che giấu đúng loại sai lầm mà chương đánh giá cần đo**.

### 5.7.4. Hiển thị `raw_ocr_text` cạnh `plate_number` khi hai chuỗi khác nhau

Cột `raw_ocr_text` tồn tại để đo hiệu quả hậu xử lý (mục 5.6.2); frontend đưa phép đo đó lên màn hình. Trong `PlateResultCard.tsx`, cờ `showRawComparison = wasCorrected(result.raw_ocr_text, result.plate_number)` tính ngay khi dựng component, và **chỉ khi** hai chuỗi khác nhau thì hiện một dòng so sánh gồm biểu tượng cây đũa phép, nhãn *"Hậu xử lý đã sửa:"*, chuỗi thô **gạch ngang**, mũi tên `→` và chuỗi đã chuẩn hoá; cùng cơ chế lặp lại ở `HistoryDetailModal.tsx` với điều kiện tường minh hơn (`raw_ocr_text !== null && plate_number !== null && raw_ocr_text !== plate_number`). Nó biến một cột CSDL phục vụ nghiên cứu thành **bằng chứng nhìn thấy được ngay trong lúc trình diễn** — người xem thấy trực tiếp `3OA12345` trở thành `30A12345` trên chính bức ảnh vừa đưa vào — và vì dòng so sánh **chỉ hiện khi có thay đổi**, giao diện không lộn xộn bởi các trường hợp hậu xử lý không can thiệp, vốn là đa số.

### 5.7.5. Phân biệt "lượt nhận dạng" và "biển số phát hiện"

> **Ghi chú thay đổi phạm vi:** phần giao diện mô tả trong mục này thuộc trang Tổng quan (Dashboard) và **đã được gỡ ngày 2026-07-20**. Hai tầng dưới — CSDL và API — **không đổi**, và chính chúng là nơi sự phân biệt này được thi hành. Mục được giữ lại vì lập luận vẫn còn hiệu lực và vì bất kỳ client nào đọc `GET /api/statistics` đều phải hiểu đúng hai trường này.

Điểm dễ hiểu sai nhất của toàn hệ thống, xử lý nhất quán ở cả ba tầng: **CSDL** *(không đổi)* — `detection_job` đếm lượt, `detection_history` đếm biển số, `source_job_id` nối hai bên; **API** *(không đổi)* — `StatisticsResponse` có hai trường tách biệt `total_jobs` và `total_detections`, mô tả OpenAPI cấp cao nhất nêu rõ *"An image containing three vehicles is one job and three detections."*; **giao diện** *(đã gỡ 2026-07-20)* — trang Tổng quan từng hiển thị hai thẻ số liệu riêng kèm `InfoTooltip` tiếng Việt:

> **Lượt nhận dạng** — "Mỗi lần tải lên một ảnh, một video hoặc một phiên webcam được tính là một lượt — bất kể trong đó có bao nhiêu biển số."

> **Biển số phát hiện** — "Đếm theo từng biển số, không phải theo tệp. Một ảnh chứa 3 biển số được tính là 1 lượt nhận dạng nhưng 3 biển số phát hiện."

Nếu gộp hai khái niệm, con số "lượt sử dụng" bị thổi phồng đúng bằng **số biển số trung bình trên mỗi ảnh** — sai lệch không tạo giá trị vô lý mà chỉ tạo một con số lớn hơn sự thật một cách nhất quán, tức loại khó phát hiện nhất. Sau khi trang bị gỡ, gánh nặng giải thích chuyển sang **mô tả trường trong tài liệu OpenAPI**; `StatisticsService` giữ nguyên phân biệt này trong mọi phép tính dẫn xuất, phân rã theo loại đầu vào cũng đếm **cả hai** cho mỗi loại thay vì chọn một.

---

## 5.8. Triển khai bằng Docker

Đóng gói phục vụ NFR-C1: môi trường chạy phải tái lập được và không phụ thuộc máy cá nhân.

### 5.8.1. `Dockerfile.backend` — build hai giai đoạn

![](figures/fig-ch5-06.png)

**Hình 5.6.** Build hai giai đoạn của `Dockerfile.backend`

**(a) Hai tệp requirements cài thành hai lớp riêng** — `requirements.txt` (web + CSDL) trước, `requirements-inference.txt` (ngăn xếp ML nặng) sau — nên thay đổi ở tầng suy luận không làm mất hiệu lực bộ đệm của tầng web và ngược lại; hệ quả trực tiếp của việc tách phụ thuộc ở mục 5.1.3. **(b) Chạy dưới người dùng không đặc quyền:** ảnh tạo `appuser` với UID/GID cấu hình được, `chown` toàn bộ mã và thư mục dữ liệu, chuyển sang người dùng đó trước `CMD`. **(c) Giới hạn số luồng:** `ENV OMP_NUM_THREADS=4` đặt tường minh, vì không có nó thì BLAS/OpenMP dùng toàn bộ số nhân nhìn thấy được, và trên máy 14 nhân điều đó khiến hai container cạnh tranh đến mức cả hai đều chậm hơn. **(d) `HEALTHCHECK` gọi chính `/health`** với `--start-period=60s`, vì nạp trọng số YOLO và các mô hình PP-OCR mất vài chục giây và một `start-period` ngắn sẽ đánh dấu container là hỏng trong lúc nó đang khởi động bình thường. `ALPR_MODEL_PATH=/app/models/best.pt` đặt trong ảnh còn `models/` gắn từ ngoài vào, nên **trọng số không nằm trong ảnh Docker** — một tệp `.pt` vài chục megabyte nhúng trong ảnh sẽ khiến mọi lần build lại phải đẩy lại toàn bộ.

### 5.8.2. `Dockerfile.frontend` — build rồi phục vụ tĩnh

Giai đoạn `builder` dùng `node:20-alpine`, chạy `npm ci` (không phải `npm install` — `ci` cài đúng theo `package-lock.json`, đảm bảo tái lập) rồi `npm run build`; giai đoạn `runtime` dùng `nginx:alpine` và chỉ sao chép `dist/`, nên ảnh runtime **không chứa Node, không chứa `node_modules`, không chứa mã nguồn**. `VITE_API_BASE_URL` truyền vào ở **thời điểm build** dưới dạng `ARG` vì Vite nhúng giá trị các biến `VITE_*` vào bundle lúc biên dịch — hạn chế thực tế cần ghi nhận: khác backend, frontend **không** cấu hình lại được origin API mà không build lại, và mặc định chuỗi rỗng (same-origin) được chọn chính để tránh phải làm điều đó.

### 5.8.3. `docker-compose.yml`

Tệp compose (khoảng 250 dòng, phần lớn là chú thích giải thích) khai báo dịch vụ `backend` (nhãn `alpr-backend:${ALPR_TAG:-latest}`), dịch vụ `frontend` (nhãn `alpr-frontend:${ALPR_TAG:-latest}`), mạng bridge riêng `alpr-net` để frontend gọi backend qua tên dịch vụ, volume `alpr-data` cho dữ liệu bền (CSDL SQLite, ảnh tải lên, ảnh biển đã cắt) và volume `alpr-model-cache` cho bộ đệm mô hình PaddleOCR — volume cuối đáng nêu riêng vì PaddleOCR tải trọng số về thư mục `HOME` ở lần chạy đầu, nên không có nó thì mỗi lần `docker compose down && up` tải lại vài trăm MB và trên mạng chậm hoặc không có mạng thì container đơn giản là không khởi động được. **Trạng thái kiểm chứng:** `docker compose config` chạy hợp lệ; đo hiệu năng trong container so với chạy trực tiếp trên máy chủ thuộc Chương 6.

---

## 5.9. Những chỗ cài đặt lệch khỏi thiết kế ở Chương 4, và lý do

Nguyên tắc: **mọi điểm lệch đều được nêu, kể cả những điểm chưa được giải quyết.**

### 5.9.1. Bảng tổng hợp

| # | Thiết kế (Chương 4) | Cài đặt thực tế | Loại lệch | Trạng thái |
|:-:|---|---|---|---|
| 1 | `StubPipeline` là phương án lùi khi thiếu mô hình | `UnavailablePipeline` là phương án lùi; stub chỉ chạy khi opt-in tường minh | **Cải tiến so với thiết kế** | Đã giải quyết |
| 2 | Một môi trường ảo Python | **Ba** môi trường ảo tách biệt | Bắt buộc bởi xung đột phụ thuộc | Đã giải quyết |
| 3 | FR-2.6: có nút huỷ tác vụ video | Nút **hiện diện nhưng bị vô hiệu hoá**; không có endpoint huỷ | **Đạt một phần** | ⚠️ Chưa xong |
| 4 | Mô hình chính thức `imgsz=640` trên split sạch | Đã có `models/best.pt` (`imgsz=640`, split v3, mAP@0.5 0,9829) | Đúng thiết kế | ✅ Đã giải quyết |
| 5 | NFR-P1: độ trễ E2E p95 ≤ 800 ms | Đo được **731 ms** (client) / **780 ms** (in-process) trên `best.pt`, máy rảnh | **Đạt chỉ tiêu** | ✅ Đã giải quyết |
| 6 | Video job xuất video đã chú thích (`output_path`) | Chưa cài đặt; chỉ trả về các dòng lịch sử | Hoãn có lý do | ⚠️ Chưa xong |
| 7 | Bật oneDNN để tăng tốc CPU | Buộc phải tắt do lỗi thư viện | Bắt buộc bởi lỗi thượng nguồn | Đã ghi nhận |
| 8 | Khử rò rỉ bằng phash | Còn rò rỉ tồn dư không khử được bằng phash | **Giới hạn phương pháp** | Đã ghi nhận |
| 9 | Bộ đo độ chính xác OCR đo hệ thống đang giao | Bộ đo gọi thẳng recognizer + normalizer, **bỏ qua tầng điều phối** | **Lỗi phương pháp đo** | ✅ Đã phát hiện và sửa |

### 5.9.2. Phân tích từng điểm lệch

**(1)** là điểm lệch duy nhất mà cài đặt **tốt hơn** thiết kế: thiết kế coi stub là lưới an toàn, hiện thực cho thấy đó là lưới an toàn *sai loại* vì nó biến một triển khai hỏng thành một triển khai trông như đang chạy tốt (mục 5.6.4) — bài học: **một phương án lùi phải thất bại theo cách quan sát được**. **(2)** là lệch **bắt buộc bởi ngoại cảnh**: `paddleocr` hạ cấp NumPy và thay `opencv-python` bằng bản cũ hơn một bậc major (mục 5.1.3); chi phí là thiết lập môi trường phức tạp hơn, lợi ích là kết quả đo tái lập được.

**(3) FR-2.6 đạt một phần — nút "Huỷ tác vụ" bị vô hiệu hoá**, điểm lệch cần trình bày thẳng thắn nhất. **Phía backend, cơ chế huỷ đã tồn tại và hoạt động** (vòng lặp video gọi `_is_cancelled(db, job)` mỗi 10 khung, `JobStatus.CANCELLED` hợp lệ trong lược đồ và trong ràng buộc `CHECK`), nhưng **phía HTTP không route nào đặt được trạng thái đó** — OpenAPI đang chạy công bố 9 đường dẫn (10 thao tác) và **không đường dẫn nào huỷ một tác vụ**. Quyết định là **hiển thị nút ở trạng thái vô hiệu hoá** kèm `title="Chức năng đang được phát triển"`, với lý do ghi thành chú thích trong `JobProgressPanel.tsx`: *"The button is therefore present and disabled rather than wired to an invented endpoint, which would 404 and leave the user believing the job had stopped while it kept running."* Việc còn lại nhỏ và đã xác định rõ: thêm route `POST /api/jobs/{job_id}/cancel` và bỏ thuộc tính `disabled`.

**(4) Mô hình chính thức đã hoàn tất.** `models/best.pt` (YOLO11n, `imgsz=640`, split v3, 20 epoch) trên tập test v3 (1.514 ảnh):

| Chỉ số | Giá trị | Chỉ tiêu | Đạt? |
|---|---:|---|---|
| mAP@0.5 | 0,9829 | NFR-A1: ≥ 0,90 | ✅ |
| mAP@0.5:0.95 | 0,7834 | NFR-A2: ≥ 0,65 | ✅ |
| Precision | 0,9837 | NFR-A3: ≥ 0,92 | ✅ |
| Recall | 0,9714 | NFR-A3: ≥ 0,90 | ✅ |

Cả bốn chỉ tiêu detection **đều đạt**, đo trên split v3 đã khử trùng lặp ở ngưỡng phash 10 nên không còn rò rỉ tên-tệp thổi phồng như baseline; `baseline-416-v1.pt` (`imgsz=416`, split v1, mAP@0.5 0,9933) giữ làm **mô hình đối chứng**, không báo cáo là "đạt" vì sai độ phân giải và có rò rỉ (619 cặp d ≤ 10).

**(5) NFR-P1 đạt.** Độ trễ đầu-cuối p95 trên `models/best.pt`, máy rảnh, cấu hình giao hàng: **1.143,10 ms** (in-process) — dưới ngưỡng tối thiểu 1.500 ms nhưng vượt mục tiêu 800 ms; trung vị chỉ **405,77 ms**, chênh lệch giữa hai phân vị là do bậc thang thử-lại vốn chỉ chạy khi lần đọc đầu thất bại (Chương 6, mục 6.5.7 và 6.6.1). Phân rã giai đoạn: **OCR ~64,3% (108,28 ms/biển), detect ~34,0% (57,27 ms)**. Con số cũ **5.857,19 ms** (từng ghi trong bản nháp) **đã bị bác bỏ**: nó đo khi một tiến trình huấn luyện chiếm ~793% CPU song song, trên checkpoint epoch 7 (không phải `best.pt`), và trên hệ thống có lỗi crop khiến PaddleOCR đọc trên ảnh crop quá lớn (~1322 ms/ảnh) — đẩy tỷ trọng OCR lên "93,3%" giả tạo; đo lại trên máy rảnh với mô hình đúng, oneDNN đã tắt (`enable_mkldnn=false`, cold-start p95 chỉ 176 ms), p95 về 731 ms.

**(6) Video job chưa xuất video đã chú thích:** `output_path` tồn tại trong lược đồ và trong `DetectionJobResponse` nhưng chưa được điền, với lý do ghi thành `TODO` có giải thích — vẽ hộp bao lên từng khung đòi hỏi đầu ra theo từng khung của bộ phát hiện thật, mà lúc viết đoạn mã đó hệ thống còn chạy stub, và chú thích các hộp bao **bịa ra** lên một video thật sẽ tạo hiện vật trông thuyết phục nhưng sai sự thật; với pipeline thật, rào cản còn lại là chi phí tính toán chứ không còn là tính đúng đắn. **(7) oneDNN buộc phải tắt** do lỗi `NotImplementedError` trong bộ thực thi PIR của PaddlePaddle 3.3.1 (mục 5.5.4) — lệch **bắt buộc bởi lỗi thượng nguồn**, ghi thành hằng số có tài liệu để lật lại và đo lại khi lỗi được sửa. **(8) Rò rỉ tồn dư không khử được bằng phash:** phash tóm tắt **bố cục khung ảnh** chứ không tóm tắt **chiếc xe** (mục 5.2.3) — **giới hạn phương pháp đã được ghi nhận**, không phải lỗi cài đặt. **(9) Bộ đo OCR từng đi tắt qua tầng điều phối** là điểm lệch **không thuộc về sản phẩm mà thuộc về phép đo sản phẩm**, nguy hiểm hơn tám điểm trên vì nó không làm hệ thống chạy sai mà làm *các con số công bố về hệ thống* mô tả một thứ khác: `ai/evaluation/ocr_accuracy.py` gọi thẳng recognizer và normalizer nên mọi logic ở tầng điều phối vô hình với NFR-A4 đến A7; cách sửa là tách thành hai hàm tự do cấp mô-đun để cả hai đường mã cùng gọi (5.5.5g). Điểm lệch này **đã được sửa** nhưng giữ trong bảng vì bài học của nó áp dụng cho mọi hạng mục đo còn lại.

### 5.9.3. Nhận xét về bản chất của các điểm lệch

Phân loại theo nguyên nhân: **1 điểm** là cải tiến so với thiết kế (#1); **3 điểm** bị ngoại cảnh cưỡng bức — xung đột phụ thuộc, lỗi thư viện, giới hạn công cụ khoa học (#2, #7, #8); **4 điểm** là công việc chưa hoàn thành hoặc chỉ tiêu chưa đạt (#3, #4, #5, #6); **1 điểm** là lỗi ở **phương pháp đo**, không ở sản phẩm (#9). Không điểm nào phát sinh từ sai lầm trong bản thân thiết kế kiến trúc — chỉ dấu tích cực về chất lượng Chương 4; ba điểm lệch do ngoại cảnh lại là bằng chứng gián tiếp cho giá trị thiết kế, vì nhờ `BaseRecognizer` mà vấn đề của PaddleOCR chỉ ảnh hưởng một tệp và nhờ cấu hình tập trung mà tắt oneDNN là một hằng số chứ không phải sửa đổi rải rác. Điểm lệch thứ chín đứng riêng một loại và cần đọc như một cảnh báo chứ không như mục đã đóng: nó nhắc rằng **ranh giới giữa "hệ thống" và "phép đo hệ thống" cũng là một ranh giới kiến trúc**, và ranh giới đó không được test nào ở mục 5.5.1 canh giữ — bộ test kiến trúc kiểm chiều phụ thuộc giữa các gói nhưng không kiểm được rằng bộ đo và sản phẩm chạy *cùng một đường mã*; đây là hạng mục còn thiếu cơ chế bảo vệ tự động, cần nêu khi bảo vệ nếu có câu hỏi về độ tin cậy của các con số ở Chương 6.

---

## 5.10. Kết luận chương

**Về khối lượng và trạng thái.** Hệ thống gồm tầng AI (12 mô-đun, 4.852 dòng trong `ai/inference/` cộng các gói huấn luyện, đánh giá, dữ liệu), tầng backend (21 mô-đun không kể `__init__.py`, 10 endpoint REST, 2 bảng CSDL với 21 và 11 cột), tầng frontend (**3 trang sau hai đợt thu gọn phạm vi ngày 2026-07-20, 48 mô-đun**, 15 component nguyên thuỷ), đường ống dữ liệu 6 bước và cấu hình Docker hai dịch vụ. Trạng thái kiểm chứng bằng chạy thật: backend trả `model_loaded=true` với engine `yolo:...+paddleocr-PP-OCRv5-mobile`, 10/10 ảnh test nhận dạng được biển số với các chuỗi đọc đúng như `51G-495.39`, `51F-734.20`, `47A-065.46`, `51A-897.14` (độ tin cậy OCR 0,94–0,9993); frontend typecheck sạch, lint sạch, build **1.670 mô-đun** trong 2,15 giây với gói tải về **328,8 KB** (giảm 55% so với ~730 KB trước khi gỡ `recharts`), 10 endpoint kiểm chứng qua HTTP thật với kiểu TypeScript khớp từng trường (thực hiện trước hai đợt gỡ trang; ba endpoint nay không có trang gọi tới vẫn được kiểm chứng bằng kiểm thử tích hợp); bộ kiểm thử tự động chạy qua với bao phủ tầng nghiệp vụ **87,7%** ở lần đo mới nhất 2026-07-20 (`docs/reports/13-refactor-result.json`) — NFR-M2 yêu cầu ≥ 70%: **đạt**; lần đo Phase 7 trước đó là 88,1% với bao phủ toàn kho 42,0% (`docs/reports/07-testing-report.md`).

> **Ghi chú về số lượng test.** Con số đã được kiểm chứng bằng cách chạy lại thật (`backend/.venv/Scripts/python.exe -m pytest -q` từ gốc kho, ngày 2026-07-20). Lần chạy mới nhất **thu thập 913 test**; kết quả là **912 pass, 1 `xfail` (lỗi đã biết, có mô tả), 0 fail, 0 skip, 0 error, 17 cảnh báo**. Cần phân biệt hai con số khác nhau: **913 là số test *thu thập*,** còn **912 là số test *pass*** — chênh lệch đúng bằng 1 `xfail`, không phải một test hỏng. Cặp số **882/881** là kết quả của một lần chạy sớm hơn cùng ngày, **trước** khi bổ sung các test cho `plate_color.py`, cho bước cứu dòng trên và cho ba cột CSDL mới; cặp **862/861** xuất hiện trong các bản tài liệu trước nữa là kết quả một lần chạy còn cũ hơn. Cả ba cặp đều là số đo thật ở ba thời điểm khác nhau và **không được trộn lẫn**. Con số **199** từng xuất hiện trong một bản tổng kết trạng thái Phase 4 cũng **không còn đúng**: đó là kết quả một lần chạy *con* chỉ gồm 5 tệp test của tầng AI, không phải toàn kho. Về bao phủ, số mới nhất là **87,7%** tầng nghiệp vụ (2026-07-20); số Phase 7 trước đó là **88,1%** tầng nghiệp vụ và **42,0%** toàn kho — cả hai đều là số đo thật ở hai thời điểm khác nhau, không được trộn lẫn.

**Về đóng góp kỹ thuật.** Năm khối là công trình của đồ án chứ không phải thư viện có sẵn: **`two_line.py`** (cắt-có-chồng-lấn rồi ghép ngang, mục 5.5.5); **bộ luật hậu xử lý `plate_rules.py` + `normalizer.py`** với hai phát hiện trung tâm là ký tự đại diện `?` tại chỉ số 3 và tính không đối xứng của bảng ánh xạ nhầm lẫn (5.5.6c–d); **đường ống khử trùng lặp** băm đa chỉ mục chính xác kèm bài học rằng perceptual hash tóm tắt bố cục khung ảnh chứ không tóm tắt phương tiện (5.2.2–5.2.3); **`plate_color.py` cùng phép hợp nhất chuỗi–màu** với ràng buộc an toàn còn đáng giá hơn cả con số 97,89% (5.5.8); và **bước cứu dòng trên**, đáng ghi nhận vì **đường đi tới nó** — giả thuyết đầu tiên bị chính phép đo bác bỏ — hơn là vì mức cải thiện (5.5.5f).

**Về chất lượng mã nguồn.** NFR-M6 lần đầu được **đo trực tiếp** thay vì tuyên bố: `ruff check .` báo *All checks passed*, `black --check` báo 79 tệp không cần sửa; ghi nhận lần đo đầu tiên ở đây để các lần sau có mốc đối chiếu.

**Về những gì chưa hoàn thành.** Nút huỷ tác vụ video bị vô hiệu hoá khiến FR-2.6 chỉ đạt một phần; video job chưa xuất video đã chú thích; bộ dữ liệu còn rò rỉ tồn dư không khử được bằng công cụ hiện có. Mô hình chính thức `best.pt` đã hoàn tất (detection đạt cả bốn chỉ tiêu) và NFR-P1 đã đạt; nút thắt kỹ thuật còn lại là **độ chính xác OCR biển 2 dòng** (A4/A5/A6 không đạt — trình bày trung thực ở Chương 6). Ghi nhận các hạng mục này kèm phân tích nguyên nhân, thay vì bỏ qua chúng, là một phần của phương pháp làm việc mà chương này chủ trương.

**Về giá trị của kiến trúc đã chọn.** NFR-M1 **được kiểm chứng tự động** nên là ràng buộc không suy thoái theo thời gian; tiêm phụ thuộc cho phép thay `StubPipeline` bằng `UnavailablePipeline` bằng **một thay đổi trong `backend/main.py`**; và cơ chế đo thời gian theo giai đoạn cho phép phân rã độ trễ (OCR 64,3% / detect 34,2% trên `best.pt`) đồng thời giúp phát hiện con số cũ 93,3% là tạo tác của một hệ thống đang có lỗi crop.

Chương 6 sẽ trình bày kết quả đo đạc đầy đủ: hiệu năng mô hình phát hiện trên tập test đã làm sạch, độ chính xác nhận dạng ký tự tách riêng cho biển một dòng và hai dòng (NFR-A4 đến A7), đóng góp định lượng của hậu xử lý đo bằng so sánh `raw_ocr_text` với `plate_number`, tốc độ xử lý webcam và video (NFR-P2, NFR-P3), cùng kết quả các phương án tối ưu độ trễ đang được theo đuổi.
