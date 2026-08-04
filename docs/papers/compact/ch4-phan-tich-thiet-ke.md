# CHƯƠNG 4. THIẾT KẾ VÀ CÀI ĐẶT HỆ THỐNG

Trên cơ sở lý thuyết ở Chương 2 và lựa chọn công nghệ ở Chương 3, chương này trình bày thiết kế và hiện thực của hệ thống trong cùng một mạch. Nguyên tắc: mọi mô tả tương ứng với mã nguồn có thật; chức năng chưa hoàn thiện ghi rõ mức độ; số đo chưa có thì nói thẳng là chưa có. Chương gồm phân tích yêu cầu (4.1), kiến trúc (4.2), môi trường phát triển (4.3), bộ dữ liệu (4.4), huấn luyện mô hình (4.5), tầng AI (4.6), backend và CSDL (4.7), giao diện (4.8), Docker (4.9) và bảng đối chiếu cài đặt lệch thiết kế (4.10).

Trạng thái bản này: hệ thống chạy `ALPRPipeline` với mô hình chính thức `models/best.pt` (`/health` báo `model_loaded: true`, engine `yolo:best.pt+paddleocr-PP-OCRv5-mobile`, mAP@0.5 = 0,9829); `StubPipeline` đã ra khỏi đường chạy chính. Mọi kết quả thực nghiệm trình bày ở Chương 5.

---

## 4.1. Phân tích yêu cầu

### 4.1.1. Khảo sát nhu cầu và các tác nhân

Nhận dạng biển số là bài toán nền tảng của bãi đỗ tự động, thu phí không dừng, kiểm soát ra vào và giám sát giao thông. Áp mô hình ALPR huấn luyện trên dữ liệu nước ngoài vào Việt Nam gặp bốn trở ngại. **Thứ nhất, biển hai dòng chiếm tỉ trọng lớn** (toàn bộ xe máy và một phần ô tô) trong khi đa số bộ dữ liệu quốc tế giả định biển một dòng; điểm gãy này đã đo được: trên **bộ RodoSol-ALPR của Brazil**, OpenALPR nhận đúng 3.772/4.000 ô tô biển một dòng (94,3%) nhưng chỉ 1.827/4.000 xe máy biển hai dòng (45,7%), chênh **48,6 điểm phần trăm** [7]<!-- laroca_2022_crossdataset -->[88]<!-- laroca_2022_rodosol -->. **Thứ hai, quy chuẩn biển số có tính pháp lý và cấu trúc chặt**: Thông tư 79/2024/TT-BCA [8]<!-- bocongan_2024_tt79 -->, sửa đổi bởi TT 13/2025 [9]<!-- bocongan_2025_tt13 --> và TT 51/2025 [10]<!-- bocongan_2025_tt51 -->, thông số vật lý theo QCVN 08:2024/BCA [11]<!-- bocongan_2024_qcvn08 --> — cấu trúc chặt vừa là ràng buộc vừa là cơ hội thiết kế cho khối hậu xử lý dựa trên luật. **Thứ ba, điều kiện thu nhận ảnh khắc nghiệt**: che khuất, bụi bẩn, nghiêng, ngược sáng, ban đêm. **Thứ tư, không có phần cứng tăng tốc**: máy thực hiện không có GPU CUDA, mọi suy luận và trình diễn chạy trên CPU (mục 4.1.4a, 4.3.1).

> **Lưu ý phạm vi số liệu.** Cặp 94,3% / 45,7% đo trên **bộ RodoSol-ALPR của Brazil**, **không phải dữ liệu Việt Nam**; đồ án chỉ dùng nó làm dẫn chứng định lượng rằng "biển hai dòng khó hơn" là sự kiện đo được, không phải cảm nhận.

Hệ thống có bốn tác nhân: **người vận hành** (đưa ảnh/video, xem kết quả, tra cứu), **người phân tích** (thống kê, lọc, xuất báo cáo), **nhà phát triển** (tích hợp REST API), **hội đồng đánh giá** (quan sát, phản biện). Do hệ thống chạy nội bộ/`localhost` (giả định A-04), đồ án **không xây dựng xác thực và phân quyền**; ba tác nhân đầu là các *vai trò* trên cùng một giao diện, không phải các *tài khoản*.

### 4.1.2. Sơ đồ use case và ba use case chính

Ba use case chính — nhận dạng từ ảnh (UC-01), từ video (UC-02) và tra cứu lịch sử (UC-05) — đều được đặc tả theo cùng một khuôn: tác nhân, tiền điều kiện, luồng chính, luồng thay thế và hậu điều kiện.

### 4.1.3. Yêu cầu chức năng

Hệ thống có **34 yêu cầu chức năng** chia sáu nhóm, phân mức theo MoSCoW: 21 *Must*, 6 *Should*, 3 *Could*, 4 *Won't*. Bốn yêu cầu mức *Won't* đều là yêu cầu thuần giao diện và đều chuyển mức trong hai đợt thu gọn phạm vi ngày 20/07/2026 — trong đó **FR-4.1 là yêu cầu mức *Must* duy nhất bị đưa ra khỏi phạm vi**, ghi ở mục 6.2. Bảng đầy đủ từng mã yêu cầu ở **Phụ lục H.2**.

### 4.1.4. Yêu cầu phi chức năng

Các chỉ tiêu phi chức năng chia bảy nhóm — độ chính xác (NFR-A), hiệu năng (NFR-P), độ tin cậy (NFR-R), khả năng chịu tải (NFR-SC), khả năng bảo trì (NFR-M), bảo mật (NFR-S) và khả dụng (NFR-U) — mỗi chỉ tiêu kèm **ngưỡng tối thiểu, mục tiêu và phương pháp đo**. Hai ràng buộc chi phối toàn bộ nhóm hiệu năng: suy luận **chỉ trên CPU** (CON-02) và ngân sách độ trễ đầu-cuối. Bảng đầy đủ ở **Phụ lục H.3**; kết quả đối chiếu từng chỉ tiêu ở mục 5.7.

## 4.2. Kiến trúc hệ thống

### 4.2.1. Nguyên tắc kiến trúc

**Kiến trúc sạch và quy tắc phụ thuộc:** phụ thuộc chỉ hướng vào trong, từ chi tiết dễ thay đổi (framework web, CSDL, giao diện) về quy tắc nghiệp vụ ổn định. Ở bài toán này, thứ ổn định là thuật toán nhận dạng biển số — phát hiện, cắt, đọc, chuẩn hoá theo quy chuẩn Việt Nam; thứ dễ đổi là FastAPI hay Flask, SQLite hay PostgreSQL. Do đó **pipeline AI nằm ở vòng trong cùng**, tầng web phụ thuộc nó chứ không ngược lại. SOLID vận dụng: *trách nhiệm đơn nhất* — detector chỉ trả bounding box, recognizer chỉ trả chuỗi, normalizer chỉ chuẩn hoá — cho phép đo từng khối riêng; *thay thế Liskov* — dùng theo nghĩa đen khi hệ thống chạy pipeline giả lập đúng hợp đồng pipeline thật; *đảo ngược phụ thuộc* — tầng nghiệp vụ phụ thuộc hợp đồng trừu tượng, cài đặt tiêm từ ngoài.

Bốn ràng buộc kiến trúc: (1) **không trộn mã AI với mã API** (NFR-M1) ⇒ pipeline AI là package Python độc lập, không import framework web; (2) **mọi thành phần AI thay thế được** (NFR-M5) ⇒ đều đứng sau lớp trừu tượng; (3) **không hard-code đường dẫn** (NFR-M4) ⇒ mọi đường dẫn qua đối tượng cấu hình đọc từ biến môi trường; (4) **chạy được không cần GPU** (CON-02, NFR-C2) ⇒ thiết bị suy luận là tham số cấu hình, mặc định `cpu` — phát biểu là *cấu hình mặc định* chứ không phải "chế độ dự phòng", nên đường chạy CPU là đường được kiểm thử thường xuyên nhất.

### 4.2.2. Kiến trúc phân tầng

![](figures/fig-ch4-02.png)

**Hình 4.1.** Kiến trúc phân tầng năm tầng và chiều phụ thuộc

Năm tầng: **1 — Trình bày** (giao diện, chỉ biết hợp đồng HTTP của tầng 2); **2 — API** (định tuyến, kiểm tra hợp lệ, ánh xạ ngoại lệ thành mã HTTP, sinh OpenAPI); **3 — Nghiệp vụ** (điều phối: tạo tác vụ, gọi pipeline, lưu tệp, ghi CSDL, gộp trùng, thống kê); **4 — AI** (phát hiện, nhận dạng, chuẩn hoá — **chỉ biết NumPy, OpenCV và thư viện học sâu**); **5 — Dữ liệu** (CSDL, kho tệp). **Điểm mấu chốt:** khối tầng AI **không có mũi tên nào đi lên**. Sau hai đợt thu gọn 2026-07-20, tầng trình bày còn **ba trang** nhưng **tầng 2–5 không đổi một dòng**: `POST /detect/frame`, `GET /statistics`, `GET /health` vẫn phục vụ và vẫn có kiểm thử tích hợp — phép thử ngoài dự kiến cho nguyên tắc phụ thuộc một chiều.

### 4.2.3. Tách tầng AI khỏi tầng API và cách kiểm chứng ràng buộc

**Ba lợi ích.** *Kiểm thử độc lập*: test chỉ cần nạp mảng NumPy, không phải dựng ứng dụng web. *Tái sử dụng trong script huấn luyện và đánh giá*: nếu logic tiền xử lý nằm lẫn trong hàm HTTP thì script đánh giá phải sao chép, hai bản sẽ lệch nhau — dẫn tới tình huống tệ nhất: **con số công bố không phải con số hệ thống thực sự tạo ra** (đúng loại sự cố đã xảy ra thật, mục 4.6.4g và 4.10). *Thay engine không sửa tầng API* — **đã kiểm chứng trên thực tế**: suốt Phase 5–7 hệ thống chạy `StubPipeline`, toàn bộ tầng API, nghiệp vụ, CSDL, giao diện được xây và kiểm chứng **trước khi mô hình được huấn luyện**; khi trọng số sẵn sàng, chuyển sang `ALPRPipeline` chỉ là đổi thành phần được tiêm, **không sửa dòng nào** ở router, service, schema. Để trạng thái mô phỏng không bị nhầm với vận hành thật, `/health` báo `degraded` chừng nào stub còn được dùng.

### 4.2.4. Luồng xử lý của pipeline AI và nhánh biển hai dòng

![](figures/fig-ch4-03.png)

**Hình 4.2.** Luồng xử lý của pipeline AI, các khối tô đỏ là nhánh biển hai dòng

**Nhánh biển hai dòng** là phần khó nhất của đồ án và là rủi ro đã xác định từ khâu lập kế hoạch (R-04). Bộ OCR dựng sẵn giả định văn bản một dòng ngang, nên với biển hai dòng chúng đọc theo thứ tự không xác định, ghép lẫn hoặc bỏ sót một dòng — cơ chế đứng sau chênh lệch 48,6 điểm phần trăm **đo trên bộ RodoSol-ALPR của Brazil** đã dẫn ở 4.1.1 [7]<!-- laroca_2022_crossdataset -->. Giải pháp: **tách vùng biển thành hai nửa, nhận dạng từng nửa, ghép theo thứ tự trên trước dưới sau** — mỗi nửa lúc này là một dòng ngang đúng giả định của bộ OCR (cài đặt ở 4.6.4).

### 4.2.5. Bảng tổng hợp các quyết định kiến trúc

Mỗi quyết định ghi kèm lý do và **đánh đổi phải chấp nhận** — một quyết định trình bày như không có nhược điểm là quyết định chưa cân nhắc đủ.

<!-- {{T4.2}} cac quyet dinh kien truc AD-01 den AD-08 -->

Tám quyết định kiến trúc được ghi thành hồ sơ AD-01 … AD-08, mỗi hồ sơ nêu **bối cảnh, phương án đã cân nhắc, quyết định và hệ quả phải chấp nhận** — dạng ghi chép này khiến một quyết định về sau có thể bị lật lại mà người lật hiểu được vì sao nó từng đúng. Các mục 4.2.1 – 4.2.4 trình bày bốn quyết định có ảnh hưởng rộng nhất.

Ghi chú: AD-03 không đổi sau khi gỡ trang Webcam vì ở ~5 FPS trên CPU, nút thắt là suy luận chứ không phải giao thức. AD-04 cố ý **không** chọn tracking vì phức tạp hơn đáng kể và thêm một họ siêu tham số. AD-05 là quyết định duy nhất **đã thay đổi** so với phác thảo (*"PyTorch trước, ONNX nếu cần"*) — ghi nhận tường minh thay vì lặng lẽ sửa bảng. AD-06 kéo theo hai quyết định phái sinh đã cài đặt: `yolo11n` và **PP-OCRv5 mobile** — ràng buộc CPU thay đổi *lựa chọn mô hình*, không chỉ tốc độ.

---

## 4.3. Môi trường và công cụ phát triển

### 4.3.1. Cấu hình máy thực hiện và hệ quả của ràng buộc CPU

Toàn bộ cài đặt, kiểm thử, đo đạc chạy trên một máy trạm duy nhất (`docs/00-requirements/environment.md`): Windows 11 Pro; Intel Core i5-14600K, 14 nhân / 20 luồng; RAM 31,77 GiB; Intel UHD 770 — **không có GPU CUDA**; Python 3.13.12; Node.js 18.20.8; Docker 29.4.3. Cấu hình này **mâu thuẫn với mô tả môi trường ban đầu** (macOS Apple Silicon, Python 3.12); ghi nhận sai lệch thành văn bản là bước đầu của Phase 0. Ràng buộc CPU để lại dấu vết cụ thể: NFR-P1 phát biểu thẳng cho CPU; AD-06 kéo theo `yolo11n` và PP-OCRv5 mobile; và vì huấn luyện trên CPU mất 1–3 ngày/lượt, `ai/training/` chạy được cả local lẫn Colab/Kaggle với siêu tham số trong tệp cấu hình (`ai/training/config.py`, 586 dòng). Hệ quả đo được: p95 đầu-cuối trên `models/best.pt` (máy rảnh) là **731 ms** (client-side) / **780 ms** (in-process), OCR chiếm **~64,3%**, phát hiện **~34,2%** (đối chiếu NFR-P1 ở 4.10).

### 4.3.2. Ba môi trường ảo Python tách biệt và bộ công cụ

Đồ án dùng **ba môi trường ảo tách biệt**: `.venv-ai/` (huấn luyện, xuất mô hình — NumPy 2.3.3, OpenCV 5.0, torch 2.13.0+cpu), `.venv-ocr/` (thử nghiệm OCR — paddlepaddle 3.3.1, paddleocr 3.7.0), `backend/.venv/` (dịch vụ — torch, ultralytics 8.4.101, paddleocr). Bắt buộc tách vì `paddleocr` kéo theo `paddlex`, **hạ cấp NumPy và thay `opencv-python` bằng `opencv-contrib-python` 4.10** — lùi một phiên bản lớn so với OpenCV 5.0 của nhánh huấn luyện; cài chung thì mỗi lần cài lại một nhánh âm thầm đổi phiên bản nhánh kia — lỗi không làm sập chương trình mà làm **kết quả đo không tái lập được**. Phân tách phản ánh ở `requirements.txt` và `requirements-inference.txt`, được `Dockerfile.backend` cài theo hai lớp riêng (4.9).

**Bộ công cụ:** FastAPI + Uvicorn; SQLAlchemy 2.x + Alembic; Pydantic v2; Ultralytics 8.4.101 chạy YOLO11 [16]<!-- jocher_2024_yolo11 -->; PaddleOCR 3.7.0 cho PP-OCRv5 [17]<!-- cui_2026_ppocrv5 -->; Vite + React + TypeScript; pytest + pytest-cov; Docker Compose. Docker dùng Python 3.12 trong khi local dùng 3.13 là **chủ ý**: container là nơi lấy lại phiên bản mục tiêu (NFR-C1).

---

## 4.4. Xây dựng bộ dữ liệu

### 4.4.1. Đường ống sáu bước và thành phần bộ dữ liệu

![](figures/fig-ch5-01.png)

**Hình 4.3.** Đường ống sáu bước xây dựng bộ dữ liệu

Mỗi bước là một script độc lập trong `scripts/dataset/` có CLI riêng, sinh báo cáo JSON/CSV; `run_pipeline.py` chạy cả chuỗi một lệnh. **Kết quả:** **15.133 ảnh** hợp nhất từ **7 bộ công khai** (Roboflow, HuggingFace, Kaggle), còn **6 nguồn nguyên tố** sau khi loại **11.978 ảnh (44,2%)** bản sao từ **27.111 ảnh**; tổng 9 bộ tải về, 2 bộ nhãn mức ký tự tách riêng cho đánh giá OCR. Chia 70/20/10 thành **10.592 / 3.027 / 1.514 ảnh**. Bảng dưới **phải trích khi nói về dữ liệu của đồ án**; nguồn và giấy phép từng bộ ở **Phụ lục C.1**.

<!-- {{T4.4}} dong gop cua tung bo du lieu truoc va sau khu trung lap -->

**Bảng 4.1.** Đóng góp của từng bộ dữ liệu trước và sau khử trùng lặp

| # | Bộ (slug) | Vào gộp | **Còn lại** | Bị loại |
|---|---|---:|---:|---:|
| 1 | `roboflow_school_fuhih` | 8.357 | **6.868** (45,38%) | 17,8% |
| 2 | `hf_vn_plates_segment` | 4.578 | **4.375** (28,91%) | 4,4% |
| 3 | `roboflow_traffic_camera` | 3.843 | **3.162** (20,89%) | 17,7% |
| 4 | `roboflow_eric_nguyen` | 840 | **353** (2,33%) | 58,0% |
| 5 | `roboflow_demo_tracking` | 236 | **235** (1,55%) | 0,4% |
| 6 | `roboflow_cuong_ta` | 8.254 | **140** (0,93%) | **98,3%** |
| 7 | `roboflow_tran_ngoc_xuan_tin` | 1.005 | **0** | **100%** |
| | **Tổng** | **27.113** | **15.133** | **44,2%** |



> **Cảnh báo phạm vi bắt buộc kèm mọi số liệu OCR.** Phân loại màu nền trên 2.801 ảnh cho: **2.736 biển trắng (97,68%)**, 20 vàng, 4 xanh, **0 đỏ, 0 ngoại giao**. Phát biểu đúng là *"1 − CER = 0,9454 trên một tập gồm 97,7% biển trắng"*, **không phải** *"trên biển số Việt Nam"* (`docs/reports/17-plate-type-audit.json`).

### 4.4.2. Khử trùng lặp chéo bộ và con số 44,2%

Các bộ công khai fork lẫn nhau, nên một ảnh nằm ở `train` dưới tên bộ này và `test` dưới tên bộ khác thì **độ chính xác test đang đo khả năng ghi nhớ**; con số tiêu đề vì vậy là số nhóm trùng **chéo bộ**. Vét cạn ~690 triệu cặp là bất khả thi nên script dùng **multi-index hashing**: cắt mã băm 64 bit thành `threshold + 1` dải — theo nguyên lý chuồng bồ câu, hai mã khác nhau tối đa `threshold` bit bắt buộc trùng khớp trên ít nhất một dải — nên tập ứng viên chứa mọi cặp thật rồi được xác minh chính xác: **thuật toán chính xác, không xấp xỉ**.

Có **hai phép đo trên hai mẫu số khác nhau**, trích một con số trần không nêu mẫu số là gây hiểu nhầm: **(a)** trên 7 bộ vào hợp nhất — mẫu số 27.111, ngưỡng Hamming 5, loại **11.978 = 44,2%**, **đã xoá thật**; **(b)** trên corpus còn lại — mẫu số 15.133, ngưỡng 10, chỉ ra **47,8% có thể loại** nhưng **chưa xoá**. 47,8% không mâu thuẫn 44,2%: ngưỡng lỏng hơn, và chỉ đo chứ chưa xoá. Hai hệ quả của tỷ lệ 44,2%: quy mô thật khác hẳn danh nghĩa (ca cực đoan `tran_ngoc_xuan_tin` vào 1.005 ra **0** — lý do **không được cộng dồn `expected_images`** của các bộ Roboflow), và phân bố huấn luyện lệch vì bản sao tập trung ở các bộ được chép nhiều nhất. `split.py` giữ **mọi thành viên của một nhóm trùng trong cùng split** nên bản trùng không bị xoá cũng không rò rỉ được.

### 4.4.3. Giới hạn của perceptual hash: nó tóm tắt bố cục khung ảnh, không tóm tắt chiếc xe

Đây là **giới hạn không khắc phục được** bằng công cụ hiện có. Một lần kiểm tra độc lập ở ngưỡng Hamming 10 trên bộ v1 tìm thấy **619 cặp gần trùng giữa `train` và `test`**, toàn bộ ở dải d = 6–10; kiểm bằng mắt cho thấy **cùng một chiếc xe, cùng chuỗi biển số, ở cả hai split**. Pipeline không bắt được vì bộ chia gom nhóm ở ngưỡng 5 rồi lần kiểm đầu cũng đo lại ở ngưỡng 5 và báo "0 cặp" — **lập luận vòng tròn**. Nâng ngưỡng cũng không giải quyết: phash rút ảnh thành 64 bit mô tả **cấu trúc tần số thấp của toàn khung**, nên hai xe khác nhau qua cùng một camera có khoảng cách phash rất nhỏ vì 90% khung hình giống hệt. Đánh đổi không thoát được: ngưỡng thấp bỏ sót cặp cùng xe khác ngày; ngưỡng cao gộp nhầm hàng nghìn ảnh xe khác nhau cùng camera. Bộ v3 chia lại với gom nhóm ngưỡng cao hơn và kiểm độc lập ở ngưỡng 10, nhưng đồ án ghi nhận thẳng thắn: **vẫn còn rò rỉ tồn dư không khử được bằng phash** — khắc phục đòi hỏi so khớp mức chuỗi biển số hoặc đặc trưng phương tiện. Hệ quả: `baseline-416-v1.pt` đạt mAP@0.5 = 0,9933 trên bộ v1 nhưng con số đó **không được báo cáo là "đạt"** vì tập test có rò rỉ đã đo được (4.10).

---

## 4.5. Huấn luyện mô hình

### 4.5.1. Siêu tham số và chi phí huấn luyện bộ phát hiện

Cấu hình lượt chính thức trích từ `runs/final-640-v3/args.yaml` — tệp Ultralytics tự sinh, là bản ghi *đã thực thi* chứ không phải *dự định*; bảng đầy đủ ở **Phụ lục B.1**. Giá trị chịu lực: `model` = `yolo11n.pt` (tiền huấn luyện COCO, **2.590.035** tham số — biến thể nano do ràng buộc CPU); `imgsz` = **640** (đúng độ phân giải NFR-A1/A2); `epochs` = **20**, `batch` = 8; `optimizer` = AdamW, `lr0` = 0.001, `cos_lr`; `close_mosaic` = 10; `device` = `cpu`; `seed` / `deterministic` = 42 / `true`. **`fliplr = 0.0`** lệch có chủ ý so với mặc định 0.5: lật ngang tạo ký tự gương hoá — phân bố không bao giờ có trong thực tế. Vì giới hạn thời gian CPU chỉ chạy được **một lượt huấn luyện duy nhất**, không có nhiều seed để ước lượng phương sai; cố định seed ít nhất bảo đảm lượt này tái lập được — mọi chỉ số là kết quả **một lần chạy**, không có khoảng tin cậy (hạn chế ghi ở 5.9.3). **Chi phí:** baseline `baseline-416-v1.pt` 40 epoch, `imgsz` 416, bộ v1 — **156 phút**; `best.pt` 20 epoch, `imgsz` 640, bộ v3 — **30,2 phút/epoch, tổng 36.181 giây (10,05 giờ)** trên CPU, số lấy từ cột `time` của `results.csv`. Ba yếu tố cùng thay đổi (số ảnh ×3,3, diện tích ×2,37, epoch giảm nửa) khiến so sánh ở mục 3.6 **không quy kết được nguyên nhân cho từng biến**.

### 4.5.2. Tiến triển của quá trình huấn luyện

![](figures/fig-train-curves.png)

**Hình 4.4.** Đường cong huấn luyện theo epoch — ba hàm mất mát và bốn chỉ số trên tập validation *(nguồn: `runs/final-640-v3/results.csv`)*

Ba hàm mất mát giảm đơn điệu và **không có dấu hiệu quá khớp**: `box_loss` 1,252 → 0,809, `cls_loss` 0,833 → 0,313, `dfl_loss` 1,154 → 0,987; đường validation bám sát đường train suốt 20 epoch. Chỉ số trên tập validation đi lên rồi bão hoà sớm: mAP@0,5 đạt **0,9684 ngay ở epoch 1** và chỉ nhích lên **0,9830** ở epoch 20, trong khi mAP@0,5:0,95 — chỉ số nhạy với độ khít của hộp — tăng đáng kể hơn, **0,6526 → 0,7688**.

<!-- {{T4.5a}} tien trien chi so tren tap validation theo epoch -->

**Bảng 4.2.** Tiến triển chỉ số trên tập validation theo mốc epoch

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

### 4.5.3. Tinh chỉnh bộ nhận dạng ký tự và lý do không đưa vào bản giao hàng

PP-OCRv5 mobile huấn luyện trên chữ cảnh tổng quát; mục này trả lời bằng số câu hỏi fine-tune trên đúng miền dữ liệu thì được gì. **Cấu hình:** 30 epoch trên 6.672 mẫu (2.801 ảnh gốc + hai biến thể tăng cường mỗi ảnh), kiểm định 571 mẫu, charset đủ 36, khởi đầu từ `en_PP-OCRv5_mobile_rec_pretrained`; kết thúc train acc **0,9449**, val acc **0,8809**.

<!-- {{T4.5b}} so sanh fine-tune va model goc -->

**Bảng 4.3.** So sánh bộ nhận dạng gốc và bản tinh chỉnh trên cùng ngữ liệu

| Cấu hình | A5 (chuỗi thô) | A6 (sau hậu xử lý) | Đúng định dạng | ms/ảnh |
|---|---:|---:|---:|---:|
| **Model gốc, det + rec** — *bản giao hàng* | 0,6373 | **0,7512** | 0,9443 | 328,8 |
| Model fine-tune, det + rec | 0,5998 | 0,6762 | 0,9018 | — |
| Model gốc, chỉ rec | 0,6776 | 0,7508 | 0,9568 | 35,7 |
| Model fine-tune, chỉ rec | **0,8618** | **0,8758** | **0,9886** | 38,5 |

## 4.6. Tầng AI — thiết kế và cài đặt

### 4.6.1. Tổ chức gói suy luận và ba lớp trừu tượng

Tầng AI là một gói Python độc lập, không phụ thuộc bất kỳ thành phần nào của tầng API; ràng buộc được kiểm chứng tự động (mục 4.2.3) để gói vận hành được trong môi trường notebook, kịch bản đo đạc và nền tảng huấn luyện đám mây.

Kiến trúc dựa trên ba lớp trừu tượng có hợp đồng thống nhất. Lớp phát hiện trả về danh sách vùng biển đã lọc ngưỡng và khử chồng lấn, trong đó danh sách rỗng là kết quả hợp lệ chứ không phải trạng thái lỗi. Lớp nhận dạng trả về chuỗi thô kèm độ tin cậy; việc sửa lỗi ký tự và kiểm tra hợp lệ không thuộc trách nhiệm của lớp này, và chính sự tách biệt đó cho phép định lượng đóng góp của khối hậu xử lý (mục 5.5.2). Lớp chuẩn hoá trả về cả chuỗi không hợp lệ, vì loại bỏ chúng sẽ làm mất đúng các trường hợp mà chương đánh giá cần thống kê. Hợp đồng chung là trả kết quả rỗng thay vì ném ngoại lệ, nhất quán với NFR-R2: không tìm thấy đối tượng và lỗi hệ thống là hai trạng thái khác nhau.

### 4.6.2. Bộ phát hiện

Bộ phát hiện là lớp thích ứng mỏng bao quanh thư viện Ultralytics: không thành phần nào ngoài lớp này tiếp xúc với cấu trúc dữ liệu nội bộ của thư viện. Phiên bản mô hình được ghim tường minh trong định danh mà lớp công bố, để mọi kết quả đo truy được về đúng bộ trọng số và việc nâng cấp thư viện không thay đổi ngầm mô hình đứng sau một kết quả đã công bố. Trọng số nạp ngay khi khởi tạo, nên lỗi thiếu tệp bộc lộ lúc khởi động thay vì lúc phục vụ yêu cầu đầu tiên. Lớp chấp nhận cả tệp trọng số đơn lẻ lẫn thư mục mô hình đã tối ưu cho CPU, do giới hạn ở một dạng sẽ loại bỏ cấu hình suy luận nhanh nhất trên phần cứng mục tiêu. Mọi hộp bao được kẹp về biên ảnh và hộp suy biến bị loại, nên tầng trên không nhận toạ độ ngoài khung.

### 4.6.3. Bộ nhận dạng ký tự

Bộ nhận dạng tuân theo cùng mô hình lớp thích ứng và cũng ghim phiên bản mô hình tường minh. Các mảnh văn bản được lọc theo tiêu chí hình học thay vì ngưỡng tin cậy, do bước nâng tương phản có thể sinh mảnh nhiễu được đọc thành chuỗi vô nghĩa ở độ tin cậy cao; độ tin cậy của cả chuỗi tổng hợp bằng trung bình có trọng số theo độ dài mảnh, vì trung bình cộng cho phép một mảnh một ký tự che lấp mảnh dài mang danh tính thực của biển số.

Cần lưu ý một giới hạn kỹ thuật ảnh hưởng trực tiếp đến hiệu năng: trên nền tảng mục tiêu, thư viện nhận dạng không cho phép kích hoạt backend tăng tốc oneDNN do khiếm khuyết phía thư viện, nên backend này bị vô hiệu hoá bằng một hằng số cấu hình có tài liệu kèm theo. Đây là tham số hiệu năng chứ không phải tham số độ chính xác, và giải thích một phần kết quả NFR-P1 ở mục 5.6: một hướng tăng tốc suy luận CPU thông dụng hiện không khả dụng vì lý do nằm ngoài phạm vi kiểm soát của đồ án.

### 4.6.4. Mô-đun xử lý biển hai dòng

**a) Cơ sở của bài toán.** Bộ nhận dạng dựa trên kiến trúc CRNN kết hợp hàm mất mát CTC, vốn giả định căn chỉnh đơn điệu giữa cột ảnh và chuỗi ký tự — giả định chỉ đúng với văn bản một dòng. Chồng lên đó, mô-đun nhận dạng chuẩn hoá mọi ảnh về chiều cao cố định 48 điểm ảnh [103]<!-- paddlepaddle_2026_textrecognition -->. Biển xe máy Việt Nam 140 × 190 mm theo QCVN 08:2024/BCA [11]<!-- bocongan_2024_qcvn08 --> có tỉ lệ khung hình xấp xỉ 1,36; sau chuẩn hoá, mỗi hàng ký tự chỉ còn khoảng 24 điểm ảnh, thấp hơn ngưỡng mà nét chữ còn tách rời. Mức nghiêm trọng đã được định lượng: trên bộ RodoSol-ALPR của Brazil, OpenALPR đạt 94,3% trên biển ô tô một dòng nhưng chỉ 45,7% trên biển xe máy hai dòng [7]<!-- laroca_2022_crossdataset -->[88]<!-- laroca_2022_rodosol -->. Cần lưu ý cặp số liệu này đo trên dữ liệu Brazil, chỉ được trích như dẫn chứng tương đương về định lượng chứ không phải số liệu Việt Nam.

**b) Ước lượng số dòng.** Số dòng suy từ tỉ lệ chiều rộng trên chiều cao của vùng biển, ngưỡng phân loại 2,5: tỉ lệ nhỏ hơn ngưỡng được xếp vào nhóm hai dòng. Đây là đề xuất của đồ án, không phải quy định pháp lý — quy chuẩn chỉ cung cấp ba tỉ lệ vật lý 4,727, 2,000 và 1,357. Ngưỡng được chọn lệch về phía hai dòng vì đường xử lý hai dòng suy giảm êm khi gặp đầu vào một dòng, chiều ngược lại thì không. Dải 2,5–3,0 vẫn là vùng bất định do biển một dòng chụp nghiêng lớn có thể cho tỉ lệ rơi vào khoảng này; định lượng tần suất thuộc Chương 5.

**c) Phân tách hai nửa có chồng lấn.** Vùng biển được cắt thành hai nửa theo chiều dọc, nửa trên kết thúc tại 5/12 chiều cao và nửa dưới bắt đầu tại 1/3, tạo vùng chồng lấn bằng 1/12 chiều cao biển. Thiết kế xuất phát từ tính bất đối xứng của chi phí sai sót: cắt cụt chân hoặc đỉnh ký tự phá huỷ thông tin không phục hồi được, trong khi lọt vài hàng điểm ảnh của nửa còn lại chỉ được xử lý như nền.

**d) Ghép ngang.** Hai nửa được ghép theo chiều ngang bằng phép `hstack`, chiều cao chung lấy bằng giá trị lớn nhất trong ba đại lượng: chiều cao nửa trên, chiều cao nửa dưới và 48 điểm ảnh — đúng bằng chiều cao đầu vào cố định của mô-đun nhận dạng. Nửa trên đặt bên trái để bảo toàn thứ tự đọc. Sau khi ghép, một hàng ký tự duy nhất nhận trọn ngân sách 48 điểm ảnh thay vì hai hàng chia nhau, vô hiệu hoá đúng nguyên nhân đã phân tích ở mục a.

**e) Tiền xử lý ảnh biển.** Ba bước độc lập, mỗi bước bật tắt riêng để phục vụ thí nghiệm bóc tách đóng góp: chuyển thang xám, do ký tự không mang thông tin phân biệt trong kênh màu; cân bằng lược đồ xám thích nghi có giới hạn tương phản (CLAHE, hệ số 2,0 trên ô 8 × 8), vì bề mặt phản quang tạo mảng chói cục bộ mà cân bằng toàn cục không xử lý được [95]<!-- sutikno_2025_clahe -->; và khử nhiễu bằng lọc song phương thay cho làm mờ Gauss, vì lọc song phương bảo toàn biên — yếu tố quyết định để phân biệt các cặp ký tự đồng hình như `8` và `B`. Ảnh biển do bộ phát hiện sinh ra thường chỉ cao 20–40 điểm ảnh nên được phóng đại về 64 điểm ảnh trước khi đọc.

**f) Bước phục hồi dòng trên.** Chế độ hỏng quan sát được: chuỗi `29E-015.66` chỉ đọc được thành `015.66` do sau khi ghép, bộ phát hiện văn bản chỉ xác định một vùng chữ và bỏ qua cụm mã tỉnh cùng ký tự sê-ri. Giả thuyết ban đầu — loại bỏ phép ghép, đọc riêng từng nửa rồi nối chuỗi — được kiểm chứng trên 200 biển hai dòng có nhãn và bị bác bỏ dứt khoát: độ chính xác giảm từ 64,5% xuống 3,5%, không thắng ở trường hợp nào (mục 5.5.6). Nguyên nhân nằm ở chính vùng chồng lấn tại mục c: khi hai nửa được đọc riêng, dải chồng lấn bị nhận dạng hai lần và sinh ký tự thừa giữa chuỗi. Kết quả đảo ngược cách hiểu ban đầu — trên dải liền mạch, vùng lặp nằm giữa hai cụm ký tự và bị bộ phát hiện văn bản loại bỏ, điều không xảy ra khi hai ảnh được xử lý tách biệt.

Thiết kế cuối cùng vì vậy giữ nguyên chiến lược ghép, chỉ bổ sung một bước phục hồi có điều kiện chặt: chỉ kích hoạt khi đồng thời vùng biển được phân loại hai dòng, chuỗi sau chuẩn hoá không hợp lệ, và chuỗi thô khác rỗng. Khi đó hệ thống nhận dạng thêm một lượt trên riêng nửa trên, ghép với chuỗi thô rồi chuẩn hoá lại; kết quả mới chỉ được chấp nhận nếu vượt kiểm tra định dạng. Tính chất không làm suy giảm kết quả mang bản chất cấu trúc: cổng chỉ mở khi kết quả đã không hợp lệ, nên tập bị can thiệp và tập đang đúng là hai tập rời nhau. Mức cải thiện đo được là +1,86 và +0,50 điểm phần trăm trên hai mẫu độc lập, 0 trường hợp bị làm hỏng, chi phí khoảng 15–21 ms mỗi biển hai dòng — khắc phục một chế độ hỏng cụ thể chứ không tác động tới nút thắt chính.

**g) Một giới hạn về phương pháp đo.** Kịch bản sinh các chỉ số NFR-A4 đến NFR-A7 ban đầu gọi trực tiếp bộ nhận dạng và bộ chuẩn hoá thay vì đi qua tầng điều phối, khiến logic đặt tại tầng điều phối không được phản ánh trong số liệu công bố. Biện pháp khắc phục là tách bước phục hồi thành hàm độc lập cấp mô-đun để cả đường chạy sản phẩm lẫn công cụ đo cùng gọi một cài đặt. Bài học vượt ra ngoài phạm vi biển hai dòng: một công cụ đo đi tắt qua tầng điều phối sẽ đo một hệ thống khác với hệ thống được bàn giao. Cần lưu ý biện pháp này về sau vẫn chưa đủ — cùng loại sai lệch đã tái diễn, phân tích tại mục 5.5.6.

### 4.6.5. Bộ luật hậu xử lý theo vị trí

Bộ phát hiện và bộ nhận dạng đều dùng mô hình có sẵn; khối hậu xử lý là thành phần do đồ án tự thiết kế và là đóng góp kỹ thuật chính. Khối tuân ba nguyên tắc: thuần khiết về mặt hàm số, không vào/ra và không giữ trạng thái toàn cục khả biến; biểu thức chính quy sinh tự động từ các tập ký tự thay vì viết tay, loại trừ khả năng mẫu lệch khỏi bảng dữ liệu mà nó mã hoá; mọi lớp ký tự là hằng số có tên.

**a) Tập mã tỉnh.** Khối lưu 81 mã tỉnh đang sử dụng theo phụ lục Thông tư 51/2025/TT-BCA [10]<!-- bocongan_2025_tt51 -->, song song tập 8 mã không bao giờ được cấp: 13, 42, 44, 45, 46, 87, 91 và 96. So với biểu thức tổng quát chấp nhận mọi cặp chữ số, ràng buộc này bác bỏ được các chuỗi không tồn tại trên thực tế; lưu tường minh cả tập không sử dụng cho phép kiểm thử khẳng định hai tập phủ đúng dải 11–99.

**b) Các lớp ký tự sê-ri.** Bốn lớp được định nghĩa: tập 20 chữ cái cho sê-ri ô tô và ký tự thứ nhất của sê-ri xe máy; tập 20 chữ cái cho ký tự thứ hai của sê-ri xe máy; tập 11 chữ cái cho biển nền xanh; và tập mở rộng 21 chữ cái. Hai tập đầu là ảnh gương của nhau tại đúng hai ký tự — tập thứ nhất chứa `G` không chứa `R`, tập thứ hai ngược lại — nên `29-AR 123.45` hợp lệ còn `29-AG 123.45` thì không.

Tập mở rộng tồn tại vì mô hình huấn luyện trên bộ ký tự chỉ gồm 20 chữ cái sẽ không bao giờ dự đoán được `R`, gây sai sót có hệ thống trên mọi biển xe máy mang ký tự này ở vị trí sê-ri thứ hai — loại sai sót hậu xử lý không khắc phục được vì thông tin đã bị loại ở tầng mô hình. Theo cùng lập luận, mô hình được huấn luyện trên bộ 36 ký tự đầy đủ rồi mới ràng buộc về 31 ký tự hợp lệ ở tầng hậu xử lý: mô hình được phép dự đoán ký tự bất hợp lệ tạo sai lầm quan sát được và sửa được, còn mô hình không thể dự đoán ký tự đó về mặt kiến trúc tạo sai lầm không quan sát được. Tập bị loại trừ toàn hệ thống gồm 5 chữ cái `I`, `J`, `O`, `Q`, `W`; chính việc loại `I`, `O`, `Q` làm việc sửa lỗi nhận dạng trở nên khả thi.

**c) Mặt nạ vị trí và ký tự đại diện.** Ba mặt nạ tương ứng ba độ dài chuỗi hợp lệ, trong đó `D` bắt buộc chữ số, `L` bắt buộc chữ cái, `?` là ký tự đại diện không áp đặt kiểu:

- chuỗi 8 ký tự (ô tô, sê-ri 5 chữ số): `DDLDDDDD`
- chuỗi 7 ký tự (ô tô, sê-ri 4 chữ số kiểu cũ): `DDLDDDD`
- chuỗi 9 ký tự (xe máy): `DDL?DDDDD`

Ký tự đại diện tại chỉ số 3 của chuỗi 9 ký tự là chi tiết thiết kế then chốt. Hai kiểu biển xe máy cùng 9 ký tự nhưng khác nhau đúng tại vị trí này: kiểu mới dùng sê-ri hai chữ cái, kiểu cũ dùng một chữ cái kết hợp một chữ số và vẫn lưu hành hợp pháp. Nếu tách thành hai mặt nạ riêng thì việc áp kiểu tại chỉ số 3 trở thành bắt buộc, và kiểm chứng bằng chạy thật cho thấy một trong hai kiểu sẽ bị phá huỷ. Chỉ số 3 của chuỗi 9 ký tự là vị trí duy nhất trong toàn hệ thống biển số Việt Nam mà cả chữ cái lẫn chữ số đều hợp lệ.

**d) Bảng ánh xạ nhầm lẫn và tính không đối xứng.** Hai bảng ánh xạ riêng biệt được áp tại vị trí bắt buộc chữ số và vị trí bắt buộc chữ cái. Phát hiện trung tâm là hai bảng không đối xứng: `O → 0` tại vị trí chữ số là hợp lý, nhưng `0 → O` không bao giờ hợp lý vì `O` không thuộc tập sê-ri hợp lệ. Do cả `O` và `Q` đều bị loại trừ, ứng viên đồng hình duy nhất còn lại tại vị trí chữ cái là `D`, nên chiều đúng là `0 → D`. Ký tự `R` không được ánh xạ trong mọi trường hợp vì hợp lệ tại vị trí sê-ri thứ hai của biển xe máy (mục 2.2.4). Nguyên tắc an toàn: ký tự không có mục trong bảng thì giữ nguyên. Cần lưu ý hai bảng này suy từ lập luận hình dạng ký tự chứ không từ đo đạc, và một số cặp mang tính phỏng đoán; việc thay thế bằng bảng trích từ ma trận nhầm lẫn đo được thuộc Chương 5.

**e) Thuật toán chuẩn hoá.**

![](figures/fig-ch5-03.png)

**Hình 4.5.** Thuật toán chuẩn hoá chuỗi biển số theo bộ luật ràng buộc vị trí

Thuật toán tuân ba nguyên tắc. Biểu thức chính quy được thử trước khi thực hiện bất kỳ chỉnh sửa nào, bởi với chuỗi vốn đã hợp lệ thì mọi can thiệp chỉ có thể làm sai đi. Không chuỗi nào bị loại bỏ: chuỗi không sửa được vẫn trả về kèm cờ không hợp lệ và vẫn được lưu. Chuỗi thô được giữ song song với chuỗi đã sửa. Kết quả là một cấu trúc bất biến chứa chuỗi thô, chuỗi cuối, cờ hợp lệ, kết quả phân loại họ biển và danh sách vị trí ký tự đã chỉnh sửa — dấu vết kiểm toán mà chương đánh giá dựa vào để định lượng đóng góp của khối.

**f) Xử lý nhập nhằng bằng số dòng.** Số dòng bằng một chứng minh chuỗi thuộc biển ô tô, do biển xe máy luôn hai dòng; ngược lại, số dòng bằng hai không chứng minh gì vì biển ô tô loại ngắn cũng hai dòng. Trong trường hợp thứ hai, hệ thống giữ cờ nhập nhằng và trả về tập ứng viên thay vì suy đoán kết luận mà dữ liệu đầu vào không chứa. Thứ tự kiểm tra các mẫu sắp xếp theo mức đặc trưng giảm dần, trong đó biển quân đội đặt cuối vì đây là trường hợp nhận dạng nhằm loại trừ: chuỗi khớp mẫu biển quân đội không bao giờ được báo cáo là biển dân sự hợp lệ.

### 4.6.6. Tổ hợp đường ống bằng tiêm phụ thuộc

Đường ống suy luận là đối tượng tổ hợp: nó không sở hữu mô hình mà chỉ điều phối thứ tự giai đoạn, cắt vùng ảnh, đo thời gian từng giai đoạn và cô lập lỗi ở mức từng biển số; do không chứa logic học sâu, đường ống kiểm thử được đầy đủ bằng thành phần giả lập. Thời gian của cả năm giai đoạn luôn được ghi nhận, giai đoạn không thực thi báo giá trị 0 thay vì vắng mặt — cơ sở cho phép phân rã ngân sách độ trễ ở mục 5.6.2, theo đó khối nhận dạng chiếm 64,3% và khối phát hiện 34,0% tổng thời gian suy luận thuần.

Chính sách xử lý lỗi phân tầng theo mức ảnh hưởng: ảnh không chứa biển số trả kết quả rỗng; lỗi nhận dạng trên một biển chỉ vô hiệu hoá biển đó, các biển còn lại vẫn được xử lý; lỗi ở bộ phát hiện làm dừng toàn bộ yêu cầu; lỗi chuẩn hoá giữ nguyên kết quả thô. Thao tác cắt ảnh kẹp toạ độ lần thứ hai dù lớp phát hiện đã bảo đảm, vì cắt ảnh là nơi duy nhất mà sai lệch một đơn vị tạo mảng rỗng không kèm cảnh báo; ảnh cắt được tạo dưới dạng bản sao thay vì khung nhìn, tránh giữ toàn bộ khung hình gốc trong bộ nhớ khi xử lý video.

### 4.6.7. Nhận dạng họ biển và màu nền

**a) Vấn đề đặt ra.** Hệ thống ban đầu tính ra họ biển và chuỗi hiển thị có dấu phân cách nhưng loại bỏ chúng trước khi ghi vào cơ sở dữ liệu, nên một biển quân đội được nhận dạng chính xác ở độ tin cậy 0,999 vẫn bị hiển thị là sai định dạng — phát biểu không chính xác, do biển quân đội là biển hợp lệ nằm ngoài hệ dân sự (mục 4.6.5f). Hướng khắc phục gồm hai phần: lưu giữ thông tin đã tính (mục 4.7.2), và bổ sung nguồn bằng chứng mà chuỗi ký tự về nguyên tắc không thể mang, đó là màu nền.

**b) Cơ sở của bằng chứng bổ trợ.** Hai nguồn bằng chứng bù trừ cho nhau. Theo Thông tư 79/2024/TT-BCA, biển vàng của xe kinh doanh vận tải mang đúng cùng cấu trúc ký tự với biển trắng của xe cá nhân nên không biểu thức chính quy nào phân biệt được; ngược lại, biển ngoại giao có nền trắng giống biển cá nhân nên riêng màu nền cũng không đủ. Chỉ cặp thuộc tính gồm chuỗi ký tự và màu nền mới định danh được loại phương tiện.

**c) Thiết kế bộ phân loại màu.** Bộ phân loại chuyển ảnh sang không gian HSV, thống kê tỉ lệ điểm ảnh theo từng dải màu và chọn dải chiếm ưu thế, với ba quyết định đáng lưu ý. Chỉ vùng trung tâm được lấy mẫu, biên thu vào 18% mỗi phía, do khung phát hiện hiếm khi ôm sát mép biển và màu thân xe phía sau có thể chiếm ưu thế nếu lấy cả rìa. Điểm ảnh thuộc ký tự không bị loại trừ, vì ký tự chiếm thiểu số diện tích và việc bổ sung một bước phân đoạn ký tự sẽ đưa vào khâu kém ổn định hơn chính khâu nó bảo vệ. Bộ phân loại trả kết quả không xác định khi tỉ lệ dải chiếm ưu thế không đạt 30%: kết luận sai về màu tương đương khẳng định một loại phương tiện không chứng minh được, trong khi thừa nhận không xác định được chỉ là ghi nhận một giới hạn.

**d) Hợp nhất chuỗi ký tự và màu nền.** Với chuỗi như `80A12345`, bốn họ biển đều là ứng viên hợp lệ và bộ chuẩn hoá mặc định chọn họ phổ biến nhất — đúng với đa số nhưng sai một cách không quan sát được đối với xe cơ quan nhà nước mang biển nền xanh. Cơ chế hợp nhất cho phép màu nền nâng cấp một ứng viên mà bộ luật ký tự đã coi là hợp lý. Ràng buộc an toàn quan trọng hơn chính tác dụng của cơ chế: nếu phán quyết ban đầu không nằm trong tập ứng viên thì kết quả giữ nguyên, nên màu nền không thể tạo ra họ biển mà bộ luật ký tự đã bác bỏ. Khi họ biển ưu tiên có cả biến thể ô tô và xe máy, hệ thống phân định theo số dòng; nếu số dòng mâu thuẫn cả hai thì giữ phán quyết ban đầu, theo nguyên tắc đại lượng đo được từ hình học ưu tiên hơn đại lượng suy ra từ thống kê điểm ảnh. Chỉ màu xanh nằm trong bảng ưu tiên vì đây là màu duy nhất chuỗi ký tự hoàn toàn không phân biệt được; màu vàng không đổi họ biển mà chỉ đổi mục đích sử dụng nên được lưu như trường độc lập.

**e) Độ chính xác đo được.** Bộ phân loại được đánh giá trên bộ dữ liệu ảnh biển cắt sẵn có nhãn màu do người gán và chưa từng được hiệu chỉnh theo bộ này — phép đo vì vậy nằm ngoài dữ liệu hiệu chỉnh.

<!-- {{T4.6}} do chinh xac bo nhan mau nen bien so -->

**Bảng 4.4.** Độ chính xác bộ nhận màu nền trên bộ dữ liệu ngoài hiệu chỉnh

| Lớp nhãn người gán | Số ảnh | Đúng | Độ chính xác |
|---|---:|---:|---:|
| Biển vàng | 694 | 684 | **98,56%** |
| Biển trắng | 808 | 787 | **97,40%** |
| Biển xanh | 63 | 61 | **96,83%** |
| **Tổng** | **1.565** | **1.532** | **97,89%** |

Ba giới hạn cần nêu kèm kết quả trên. Thứ nhất, 542 ảnh đã bị loại khỏi phép đo, gồm toàn bộ lớp không xác định và các ảnh chụp ban đêm hoặc hồng ngoại mà chính người gán nhãn cũng không xác định được màu. Thứ hai, dạng lỗi chủ đạo là biển trắng bị phân loại thành biển xanh — 21 trong tổng số 33 trường hợp sai — do một số điểm ảnh ám lạnh vượt ngưỡng bão hoà. Thứ ba, phạm vi phép đo hẹp hơn phạm vi mô-đun: bộ dữ liệu không chứa biển đỏ và biển ngoại giao nên hai nhánh này chưa có số liệu đánh giá.

Cần lưu ý thêm rằng toàn bộ ảnh của bộ dữ liệu này đã bị biến đổi tỉ lệ về khung vuông trước khi công bố, nên bộ không dùng được để đánh giá độ chính xác nhận dạng ký tự — phép biến đổi phá huỷ tỉ lệ khung hình mà thuật toán ước lượng số dòng dựa vào. Màu nền không chịu ảnh hưởng, do đó bộ dữ liệu chỉ được dùng cho đúng câu hỏi về màu sắc.

## 4.7. Backend và cơ sở dữ liệu

### 4.7.1. Cấu trúc phân tầng backend và tầng nghiệp vụ

Backend gồm 21 mô-đun Python (19 ứng dụng + 2 Alembic) trong năm tầng với **luồng phụ thuộc một chiều nghiêm ngặt**; `core/` được mọi tầng dùng nhưng không phụ thuộc tầng nào. Ba quy tắc: **router không viết truy vấn** — mọi truy cập qua repository, thay đổi lược đồ có bán kính ảnh hưởng một tệp; **repository `flush`, không bao giờ `commit`** — lưu một tác vụ cùng sáu biển là **một** thao tác logic, `commit` giữa chừng để lại trạng thái hỏng mà từng dòng riêng lẻ đều hợp lệ, ranh giới giao dịch thuộc tầng service; **khoá sắp xếp qua danh sách cho phép tường minh** — `getattr(model, name)` biến `?sort_by=metadata` thành lỗi 500, ánh xạ tường minh biến khoá lạ thành 400 sạch sẽ; `MAX_PAGE_SIZE = 200`.

### 4.7.2. Cơ sở dữ liệu: lược đồ, di trú và các quyết định thiết kế dữ liệu

Cơ sở dữ liệu gồm hai bảng quan hệ một–nhiều: `detection_job` (một lần sử dụng hệ thống) và `detection_history` (mỗi biển số phát hiện được một bản ghi), nối bằng khoá `source_job_id`. Tách hai bảng là điều kiện để thống kê đếm đúng — *lượt nhận dạng* và *biển số phát hiện* là hai đại lượng khác nhau. `detection_history` hiện có **21 cột** sau ba lần di trú Alembic, trong đó hai quyết định đáng chú ý: lưu **song song** `raw_ocr_text` và `plate_number` để đo được đóng góp của khối hậu xử lý, và cột `upper_char_count` để giải nhập nhằng cách nhóm chữ số của biển hai dòng.

### 4.7.3. REST API

API kiểu REST, tự sinh OpenAPI 3.x và Swagger UI. Endpoint nghiệp vụ dưới tiền tố `/api`; health check đặt ở gốc để giám sát và Docker healthcheck không phụ thuộc phiên bản API. Đếm từ `backend/api/routes/` đối chiếu OpenAPI: **10 thao tác HTTP trên 9 đường dẫn** (`/api/history/{detection_id}` mang cả `GET` và `DELETE`); `/docs`, `/redoc`, `/openapi.json` do FastAPI tự sinh, không tính. Bảng đặc tả đầy đủ ở **Phụ lục F.1**. Tóm tắt: `GET /health` (200); `POST /api/detect/image` (200); `POST /api/detect/video` (**202**); `POST /api/detect/frame` (200, kèm `job_id` tuỳ chọn); `GET /api/jobs/{job_id}` (200/404); `GET /api/history` (200, các tham số lọc – sắp xếp – phân trang); `GET /api/history/export` (200 `text/csv`, UTF-8 **có BOM**, không phân trang); `GET /api/history/{detection_id}` (200/404/422); `DELETE /api/history/{detection_id}` (**204**); `GET /api/statistics` (200, tham số `days`). Lỗi chung: 400, 413, 422, 500.

### 4.7.4. `UnavailablePipeline` — một phương án lùi phải thất bại theo cách quan sát được

Giai đoạn chưa có mô hình, hệ thống chạy `StubPipeline` — bịa kết quả có cấu trúc hợp lệ, chính đáng lúc đó để xây API/CSDL/frontend. Vấn đề: **stub từng được cài làm phương án lùi khi không nạp được mô hình** — một triển khai cấu hình sai sẽ trả lời mọi lần tải lên bằng một biển số thuyết phục nhưng hư cấu: chế độ hỏng **trông giống thành công**, loại nguy hiểm nhất trong hệ thống có ghi CSDL. Ba lớp nay phân vai rõ: `ALPRPipeline` — nhận dạng thật, `is_ready = True`, `/health` `ok`; `UnavailablePipeline` — **mặc định khi hỏng**, ném `ALPRError` và **không bịa gì**, `/health` `degraded`; `StubPipeline` — **chỉ chạy khi `ALPR_USE_STUB` đặt tường minh**, `/health` `degraded`. Trọng số thiếu thì **dịch vụ vẫn khởi động** (tiến trình từ chối khởi động không nói được *vì sao*), mỗi yêu cầu trả lỗi sạch sẽ; `build_pipeline` log `WARNING`: *"Every result this process returns is invented."*

### 4.7.5. Xử lý lỗi, log có cấu trúc và `request_id`

Mỗi ngoại lệ mang **hai mô tả cho hai độc giả**: `user_message` tiếng Việt ngắn gọn có hành động, đi vào thân HTTP; `internal_detail` tiếng Anh kỹ thuật, chỉ đi vào log. Cây ngoại lệ `APIError` ánh xạ thẳng sang mã HTTP (400/404/413/415/500), và **bốn bộ xử lý được đăng ký** — trong đó một bộ *bắt tất cả* cho `Exception`, không có nó thì ngoại lệ ngoài dự kiến ở cấu hình debug sẽ hiển thị cả stack trace (NFR-S4). Log ghi **mỗi dòng một đối tượng JSON** kèm `request_id` truyền ngầm qua `ContextVar` — log video xen kẽ log tải lên đồng thời, văn bản thuần không tách lại được.

### 4.7.6. Ba lỗi thực tế đã gặp và sửa trong quá trình cài đặt

Ba lỗi đáng ghi nhận đã gặp khi cài đặt: pydantic-settings JSON-decode trường danh sách **trước** validator khiến dịch vụ sập lúc khởi động; SQLite âm thầm nuốt `tzinfo` khiến mọi phân tích theo thời gian sai lệch mà không gì trông sai; và log tiếng Việt làm sập console `cp1252` trên Windows — sự cố xảy ra *bên trong* cỗ máy logging, đúng lúc log quan trọng nhất. **Cả ba đều đi qua được kiểm thử đơn vị**, vì cả ba nằm ở ranh giới mã–môi trường (nguồn cấu hình, tầng lưu trữ, bảng mã đầu ra) — lập luận cụ thể cho việc bộ kiểm thử phải gồm kiểm thử tích hợp chạy trên đường dẫn thật.

## 4.8. Giao diện người dùng

### 4.8.1. Cấu trúc, điều hướng và các màn hình

Giao diện là SPA React + TypeScript dựng bằng Vite, gồm **3 trang** và 48 mô-đun `.tsx`/`.ts`: `pages/` (ImageDetection ở trang chủ `/`, VideoDetection `/video`, History `/history`); `components/ui/` 15 component nguyên thuỷ; các nhóm component detection/history; `services/api.ts`, `types/index.ts`, `hooks/`, `lib/`. Điều hướng cố ý **phẳng**: ba màn hình truy cập trực tiếp từ thanh điều hướng; chi tiết bản ghi và xác nhận xoá là hộp thoại chồng lên trang lịch sử để không mất ngữ cảnh bộ lọc.

### 4.8.2. Tầng gọi API và ánh xạ kiểu dữ liệu

`services/api.ts` là **nơi duy nhất frontend biết về axios hoặc mã HTTP**: component nhận dữ liệu đã có kiểu hoặc `ApiError` chuẩn hoá. Sáu hàm gọi API ứng một–một với sáu endpoint, cộng hai hàm dựng URL. **Ba endpoint còn lại không còn hàm gọi phía giao diện** nhưng **vẫn hoạt động ở backend** — cần phân biệt *hàm gọi bị xoá* với *endpoint thì không*. Không hostname nào viết cứng: origin đọc từ biến môi trường lúc build, mặc định rỗng (cùng-origin).

### 4.8.3. Nguyên tắc trải nghiệm người dùng

**Bốn trạng thái bắt buộc của mọi thành phần hiển thị dữ liệu:** *đang tải* (thiếu thì giao diện trông như treo, người dùng bấm lại tạo thêm tải); *có dữ liệu*; *rỗng* (thiếu thì màn hình trắng không phân biệt được với lỗi); *lỗi* (tiếng Việt, nêu nguyên nhân và cách khắc phục, có thử lại). Trạng thái rỗng xuất hiện với **ba nghĩa cần ba thông điệp**: chưa có lượt nhận dạng nào; bộ lọc không khớp; ảnh không chứa biển số — nghĩa thứ ba là biểu hiện giao diện của cùng quyết định ở tầng API (200 danh sách rỗng) và tầng pipeline: **không tìm thấy không phải là lỗi**.

### 4.8.4. Hàng đợi một khe ở client thời gian thực (trang webcam đã gỡ 2026-07-20)

Trang webcam đã gỡ khỏi frontend, nhưng lập luận thiết kế của nó vẫn đúng và trở thành **khuyến nghị bắt buộc cho bất kỳ client nào** gọi `POST /api/detect/frame`. Suy luận CPU chỉ ~5 FPS, nên một bộ đếm giờ ngây thơ sẽ khởi động yêu cầu thứ hai trước khi yêu cầu thứ nhất trở về — tồn đọng chỉ tăng và tab đứng hình. Giải pháp là **giữ đúng một yêu cầu đang bay**; khung tới trong lúc khe bận thì bị **bỏ qua chứ không xếp hàng**: bỏ một khung không tốn gì vì khung sau cập nhật hơn, xếp hàng thì tốn tất cả.

## 4.9. Triển khai bằng Docker

Đóng gói phục vụ NFR-C1: môi trường chạy tái lập được, không phụ thuộc máy cá nhân. `Dockerfile.backend` build hai giai đoạn, cài **hai tệp requirements thành hai lớp riêng** để thay đổi một tầng không mất bộ đệm tầng kia (hệ quả trực tiếp của 4.3.2), chạy dưới người dùng không đặc quyền, đặt `OMP_NUM_THREADS` tường minh để hai container không cạnh tranh nhân CPU đến mức cùng chậm, và `HEALTHCHECK` có `start-period` đủ dài cho việc nạp trọng số. `Dockerfile.frontend` build rồi phục vụ tĩnh bằng `nginx:alpine` — ảnh chạy không chứa Node hay mã nguồn. **Trọng số mô hình không nằm trong ảnh Docker** mà gắn từ ngoài, cùng một volume riêng cho bộ đệm mô hình PaddleOCR — không có volume này thì mỗi lần `down && up` phải tải lại vài trăm MB và không có mạng thì container không khởi động được. Bảng biến môi trường ở **Phụ lục F.2**. **Trạng thái kiểm chứng:** `docker compose config` hợp lệ; đo hiệu năng trong container thuộc Chương 5.

---

## 4.10. Những chỗ cài đặt lệch khỏi thiết kế, và lý do

Nguyên tắc: **mọi điểm lệch đều được nêu, kể cả những điểm chưa được giải quyết.**

<!-- {{T4.10a}} tong hop cac diem lech giua thiet ke va cai dat -->

**Bảng 4.5.** Tổng hợp chín điểm lệch giữa thiết kế và cài đặt

| # | Thiết kế | Cài đặt thực tế | Loại lệch | Trạng thái |
|:-:|---|---|---|---|
| 1 | `StubPipeline` là phương án lùi khi thiếu mô hình | `UnavailablePipeline` là phương án lùi; stub chỉ chạy khi opt-in tường minh | **Cải tiến so với thiết kế** | Đã giải quyết |
| 2 | Một môi trường ảo Python | **Ba** môi trường ảo tách biệt | Bắt buộc bởi xung đột phụ thuộc | Đã giải quyết |
| 3 | FR-2.6: có nút huỷ tác vụ video | Nút **hiện diện nhưng bị vô hiệu hoá**; không có endpoint huỷ | **Đạt một phần** | ⚠️ Chưa xong |
| 4 | Mô hình chính thức `imgsz=640` trên split sạch | Đã có `models/best.pt` (`imgsz=640`, split v3, mAP@0.5 0,9829) | Đúng thiết kế | ✅ Đã giải quyết |
| 5 | NFR-P1: độ trễ E2E p95 ≤ 800 ms | Đo được **1.143,10 ms** — dưới sàn 1.500 ms nhưng vượt mục tiêu 800 ms | 🟡 **Chỉ đạt sàn** | ⚠️ Chưa đạt mục tiêu |
| 6 | Video job xuất video đã chú thích (`output_path`) | Chưa cài đặt; chỉ trả về các dòng lịch sử | Hoãn có lý do | ⚠️ Chưa xong |
| 7 | Bật oneDNN để tăng tốc CPU | Buộc phải tắt do lỗi thư viện | Bắt buộc bởi lỗi thượng nguồn | Đã ghi nhận |
| 8 | Khử rò rỉ bằng phash | Còn rò rỉ tồn dư không khử được bằng phash | **Giới hạn phương pháp** | Đã ghi nhận |
| 9 | Bộ đo độ chính xác OCR đo hệ thống đang giao | Bộ đo gọi thẳng recognizer + normalizer, **bỏ qua tầng điều phối** | **Lỗi phương pháp đo** | ✅ Đã phát hiện và sửa |

