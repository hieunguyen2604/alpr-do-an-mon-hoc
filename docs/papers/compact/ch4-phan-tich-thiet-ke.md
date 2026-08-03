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

### 4.6.1. Tổ chức gói `ai/inference` và ba lớp trừu tượng

Gói gồm mười một mô-đun cùng `__init__.py`, tổng **4.852 dòng**: `types.py`, `interfaces.py`, `config.py`, `exceptions.py`, `plate_rules.py`, `normalizer.py`, `detector.py`, `recognizer.py`, `two_line.py`, `plate_color.py`, `pipeline.py`. Ràng buộc "không import FastAPI" kiểm chứng tự động ở 4.2.3; lý do nền tảng: gói phải chạy được trong Jupyter, script benchmark và Colab.

### 4.6.2. Bộ phát hiện — `YoloPlateDetector`

`YoloPlateDetector` và `PaddleOcrRecognizer` (4.6.3) đều là **adapter mỏng**: không nơi nào ngoài hai mô-đun này chạm vào `Results` của Ultralytics hay máy OCR của PaddleOCR. Cả hai **ghim phiên bản mô hình tường minh** — `name` của detector trả `yolo:{stem}{suffix}`, recognizer ghim `OCR_VERSION = "PP-OCRv5"` — vì một con số benchmark chỉ tái lập được khi nêu đúng bộ trọng số; nâng cấp thư viện không được âm thầm đổi mô hình đứng sau một kết quả đã công bố.

Detector **nạp trọng số ngay trong hàm khởi tạo** để tệp thiếu làm hệ thống thất bại lúc khởi động kèm hướng dẫn khắc phục, thay vì thất bại lúc có yêu cầu đầu tiên. Nó nhận `.pt`/`.onnx`/`.torchscript` **và cả thư mục** OpenVINO — từ chối thư mục sẽ khiến cấu hình nhanh nhất trên CPU Intel không cấu hình được. Mọi hộp bao đều được **kẹp về biên ảnh** và hộp suy biến trả `None` kèm log, nên tầng trên không bao giờ nhận toạ độ nằm ngoài ảnh.

### 4.6.3. Bộ nhận dạng ký tự — `PaddleOcrRecognizer`

**Một phát hiện kỹ thuật phải nêu ở thân bài: backend oneDNN làm sập suy luận trên PP-OCRv5.** Trên đúng nền tảng mục tiêu (`paddlepaddle` 3.3.1, Windows, CPU), chạy mô hình phát hiện văn bản qua oneDNN kết thúc bằng `NotImplementedError: (Unimplemented) ConvertPirAttribute2RuntimeAttribute...` — khiếm khuyết phía thư viện, không phải lỗi cấu hình. Xử lý: hằng số có tài liệu `DEFAULT_ENABLE_MKLDNN: Final[bool] = False`. Đây là **núm hiệu năng, không phải núm độ chính xác** — khi lỗi thượng nguồn được sửa chỉ cần lật giá trị và đo lại. Nó cũng giải thích một phần NFR-P1: **một con đường tăng tốc CPU hiển nhiên đang bị chặn bởi lỗi thư viện chứ không phải chưa được thử.**

### 4.6.4. Mô-đun xử lý biển hai dòng — `two_line.py`

**a) Vì sao bài toán tồn tại.** Bộ nhận dạng hiện đại là CRNN/CTC với giả định **căn chỉnh đơn điệu** giữa cột ảnh và ký tự — chỉ đúng với văn bản một dòng; chồng lên đó, PP-OCR **resize mọi ảnh cắt về chiều cao 48 px** [103]<!-- paddlepaddle_2026_textrecognition -->. Biển xe máy 140 × 190 mm (QCVN 08:2024/BCA [11]<!-- bocongan_2024_qcvn08 -->) có tỷ lệ ≈ 1,36, nên sau khi ép về 48 px mỗi hàng ký tự chỉ còn ~24 px — dưới mức nét chữ còn tách rời. Hệ quả định lượng: trên bộ **RodoSol-ALPR của Brazil**, OpenALPR đạt **94,3% trên biển ô tô một dòng** nhưng chỉ **45,7% trên biển xe máy hai dòng** [7]<!-- laroca_2022_crossdataset -->[88]<!-- laroca_2022_rodosol --> — đồ án trích cặp số này thuần tuý làm dẫn chứng tương đương định lượng, không phải số liệu Việt Nam.

**b) Ước lượng số dòng bằng tỷ lệ khung.** `estimate_line_count` dùng `DEFAULT_TWO_LINE_AR_THRESHOLD = 2.3`: `line_count = 2 if aspect_ratio < threshold else 1`. **Đây là heuristic do đồ án đề xuất, không phải quy tắc pháp lý** — quy chuẩn chỉ cung cấp kích thước vật lý (4,727 / 2,000 / 1,357); 2,5 chọn **lệch về phía hai dòng** vì đường xử lý hai dòng suy giảm êm khi gặp đầu vào một dòng, chiều ngược lại thì không. Hạn chế ghi trong mã: dải 2,5–3,0 là vùng xám thật vì biển một dòng chụp nghiêng gắt có tỷ lệ hộp bao tụt vào đó; định lượng tần suất thuộc Chương 5.

**c) Cắt trên/dưới có chồng lấn.** `split_two_line` dùng `UPPER_HALF_END_RATIO = 5/12`, `LOWER_HALF_START_RATIO = 1/3` — hai nửa **chồng lấn 1/12 chiều cao biển**, chủ ý do bất đối xứng chi phí: cắt cụt chân/đỉnh chữ phá huỷ thông tin **vĩnh viễn**, còn lọt vài điểm ảnh hàng bên cạnh thì bộ nhận dạng bỏ qua như nền. Hàm ép hai nửa không rỗng và cảnh báo nếu tham số làm mất chồng lấn.

**d) Ghép ngang bằng `np.hstack`.** Chiều cao chung `max(upper.h, lower.h, MIN_MERGE_HEIGHT)` với `MIN_MERGE_HEIGHT = 48` — bằng đúng chiều cao đầu vào cố định của PP-OCR. Nửa trên đặt bên trái nên thứ tự đọc bảo toàn, và sau khi ghép, **một hàng ký tự duy nhất nhận trọn ngân sách 48 px** thay vì hai hàng chia nhau; `_match_channels` nâng cả hai nửa về BGR khi số kênh lệch.

**e) Tiền xử lý ảnh biển — `preprocess_plate`.** Ba bước, **mỗi bước bật/tắt độc lập** để ablation được: chuyển xám (ký tự không mang thông tin màu); CLAHE (`clipLimit=2.0`, ô 8×8) vì biển phản quang tạo mảng chói cục bộ mà cân bằng toàn cục không xử lý được [95]<!-- sutikno_2025_clahe -->; khử nhiễu `bilateralFilter(5, 50, 50)` vì lọc song phương **bảo toàn biên** — làm mờ Gauss đủ mạnh sẽ bo tròn đầu nét, thứ phân biệt `8` với `B`. Kết quả luôn là BGR ba kênh; recognizer truyền `upscale_to_height = 64` vì ảnh biển ra khỏi detector thường chỉ cao 20–40 px.

**f) Bước cứu dòng trên — một giả thuyết hợp lý bị chính dữ liệu bác bỏ.** Mục có giá trị phương pháp luận cao nhất của khối: quan sát chế độ hỏng — đề xuất giả thuyết *nghe rất hợp lý* — **đo và bác bỏ** — và chính phép bác bỏ dẫn tới thiết kế đúng. Ảnh biển `29E-015.66` trả về `015.66`: sau khi ghép, bộ phát hiện văn bản chỉ tìm thấy **một** vùng chữ và bỏ hẳn cụm `29E`. Giả thuyết đầu tiên — bỏ phép ghép, đọc riêng từng nửa rồi nối chuỗi — được **đo** trên 200 biển hai dòng có nhãn và **sụp đổ**: 64,5% xuống **3,5%**, thắng ở **0/200** ảnh (số liệu đầy đủ ở 5.5.6). Nguyên nhân nằm đúng ở chi tiết đã biện minh ở (c): hai nửa cắt **chồng lấn** đi vào OCR riêng rẽ thì dải chồng lấn **bị đọc hai lần**, sinh ký tự rác nối giữa chuỗi. Kết luận đảo ngược cách hiểu về phép ghép: trên dải liền mạch, vùng lặp nằm giữa hai cụm chữ và **bị bộ phát hiện văn bản gạt đi** — hai ảnh rời thì không có ngữ cảnh để gạt.

Bản sửa vì vậy **giữ nguyên chiến lược ghép**, chỉ thêm một bước phục hồi hẹp qua vị từ `should_rescue_two_line(recognition)`: chỉ `True` khi đồng thời `line_count == 2`, `not is_valid_format`, và `raw_text` khác rỗng — khi đó tốn thêm **một** lần OCR trên riêng nửa trên, ghép `upper + raw`, chuẩn hoá lại; kết quả mới **chỉ được nhận nếu qua kiểm tra định dạng**, mọi trường hợp khác trả nguyên kết quả cũ. **Tính chất "không thể làm tệ đi" là tính chất cấu trúc:** cổng chỉ mở khi kết quả **đã hỏng sẵn**, nên tập bị ảnh hưởng và tập đang đúng là hai tập rời nhau — hai phép đo A/B ở 5.5.6 vì vậy là *kiểm chứng*, không phải *căn cứ*. Mức cải thiện **khiêm tốn** (+1,86 và +0,50 điểm trên hai mẫu độc lập, 0 ca bị làm hỏng), không trình bày như đột phá: nó vá một điểm mù cụ thể với chi phí ~15–21 ms mỗi biển hai dòng, không đụng tới nút thắt chính.

**g) Một lỗi phương pháp đo, quan trọng hơn chính bản vá.** `ai/evaluation/ocr_accuracy.py` — nơi sinh các con số NFR-A4–A7 công bố ở Chương 5 — **không đi qua `ALPRPipeline`** mà gọi thẳng recognizer và normalizer, nên mọi logic ở tầng điều phối **vô hình với các con số công bố**. Cách sửa: **tách bước cứu thành hai hàm tự do cấp mô-đun** (`should_rescue_two_line`, `rescue_two_line_upper`) để cả pipeline lẫn bộ đo cùng gọi. Bài học vượt ra ngoài biển hai dòng — **một bộ đo đi tắt qua tầng điều phối sẽ đo một hệ thống khác với hệ thống được giao** — và biện pháp này về sau **vẫn không đủ**: cùng loại lỗi tái diễn lần thứ ba, phân tích ở mục 5.5.6.


### 4.6.5. Bộ luật hậu xử lý — đóng góp kỹ thuật chính

Bộ phát hiện và bộ nhận dạng đều là mô hình có sẵn; khối hậu xử lý thì không. `plate_rules.py` tuân ba quy tắc: **thuần khiết** (không I/O, không trạng thái toàn cục khả biến); **regex sinh từ tập hợp, không viết tay** — mẫu không thể trôi khỏi bảng nó mã hoá; **lớp ký tự là hằng có tên**.

**a) `PROVINCE_CODES` — 81 mã tỉnh** đang dùng theo phụ lục TT 51/2025/TT-BCA [10]<!-- bocongan_2025_tt51 --> (80 mã địa phương + mã 80), song song `UNUSED_PROVINCE_CODES` gồm **8 mã không bao giờ được cấp**: `13, 42, 44, 45, 46, 87, 91, 96`. Giá trị so với `\d{2}`: nó **bác bỏ** `13A-123.45`; giữ tường minh tập không dùng cho phép test khẳng định hai tập phủ đúng dải `11`–`99`. Sáp nhập hành chính 2025 không làm mất hiệu lực biển đã cấp — mối quan tâm của tầng báo cáo, không phải của định dạng.

**b) Các lớp ký tự sê-ri.** Bốn hằng: `L20` (chữ sê-ri ô tô; chữ **thứ nhất** sê-ri xe máy), `L20B` (chữ **thứ hai** sê-ri xe máy), `L11` (sê-ri biển xanh), `L21` (20 chữ chuẩn **cộng** `R`). **`L20` và `L20B` là ảnh gương của nhau ở đúng hai ký tự** (`L20` có `G` không `R`, `L20B` có `R` không `G`): `29-AR 123.45` hợp lệ còn `29-AG 123.45` thì không. `L21` tồn tại vì một mô hình charset "20 chữ" **không bao giờ dự đoán ra `R`** nên sai **có hệ thống** trên mọi biển xe máy mang `R` ở sê-ri thứ hai — loại sai không hậu xử lý nào cứu được vì thông tin đã huỷ ở tầng mô hình. Cùng logic: `OCR_SAFE_CHARSET` = 31 ký tự, `OCR_TRAINING_CHARSET` = 36; huấn luyện trên 36 rồi ràng buộc về 31 là chủ ý — mô hình **được phép** dự đoán ký tự bất hợp pháp tạo sai lầm *quan sát được, sửa được*, mô hình *không thể về mặt kiến trúc* dự đoán nó tạo sai lầm vô hình. `EXCLUDED_LETTERS = {I, J, O, Q, W}` — 5 chữ bị loại toàn quốc; chính việc loại `I`, `O`, `Q` làm sửa lỗi OCR khả thi. (Ghi chú hiệu chỉnh: con số "6 chữ bị loại" từng gồm cả `R` đã được sửa.)

**c) `POSITION_MASKS` và ký tự đại diện `?` ở chỉ số 3** — chi tiết cài đặt quan trọng nhất của khối. Ba mặt nạ: `car_5 = "DDLDDDDD"`, `car_4 = "DDLDDDD"`, `motorcycle_9 = "DDL?DDDDD"`; `MASK_BY_LENGTH` ánh xạ độ dài 7/8/9. `D` = bắt buộc chữ số, `L` = bắt buộc chữ cái, `?` = **đại diện, tuyệt đối không ép kiểu**. Hai kiểu biển xe máy cùng 9 ký tự khác nhau ở đúng vị trí này — kiểu mới sê-ri hai chữ (`29AA12345`), kiểu cũ sê-ri chữ + số (`29B112345`, vẫn lưu hành) — nếu tách thành `DDLLDDDDD` và `DDLDDDDDD` thì ép kiểu tại chỉ số 3 là bắt buộc, và kết quả kiểm chứng bằng chạy thật: **một trong hai kiểu bị phá huỷ** (`29AA12345` → `29A412345`, hoặc `29B112345` → `29BL12345`), trong khi `DDL?DDDDD` trả lại đúng cả hai. Chỉ số 3 của chuỗi 9 ký tự là **vị trí duy nhất trong toàn hệ thống biển số Việt Nam mà cả chữ lẫn số đều hợp lệ**; nhánh `?` viết tường minh trong `apply_position_rules` chứ không rơi vào `else`. Chuỗi 8 ký tự không cần mặt nạ thay thế vì cả hai cách đọc áp cùng `DDLDDDDD`.

**d) Hai bảng ánh xạ nhầm lẫn và tính không đối xứng.** `TO_DIGIT` 12 mục (`O→0`, `Q→0`, `D→0`, `I→1`, `J→1`, `L→1`, `Z→2`, `A→4`, `S→5`, `G→6`, `T→7`, `B→8`), `TO_LETTER` 9 mục (`0→D`, `1→L`, `2→Z`, `3→B`, `4→A`, `5→S`, `6→G`, `7→T`, `8→B`); áp riêng tại vị trí `D` và `L`. **Ánh xạ không đối xứng, và đó là phát hiện trung tâm:** `O → 0` đúng, nhưng `0 → O` **không bao giờ đúng** vì `O` không phải chữ sê-ri hợp lệ — với cả `O` và `Q` bị loại, `D` là ứng viên đồng hình duy nhất còn lại, nên chiều đúng là `0 → D` tại vị trí chữ; chữ `R` **tuyệt đối không được ánh xạ đi** vì hợp lệ ở vị trí thứ hai sê-ri xe máy (2.2.4). Quy tắc an toàn: **ký tự không có mục trong bảng thì giữ nguyên**. **Ghi nhận trung thực về nguồn gốc:** hai bảng suy từ lập luận hình dạng ký tự, **không phải từ đo đạc**; vài cặp — đáng chú ý `L → 1` — là phỏng đoán yếu; thay bằng bảng trích từ ma trận nhầm lẫn 36×36 đo được thuộc Chương 5, và trình bày bảng hiện tại như **giả thuyết cần kiểm chứng** vừa trung thực vừa mạnh hơn về học thuật.

**e) Thuật toán chuẩn hoá.** `VietnamesePlateNormalizer.normalize_detailed` thực hiện luồng sau:

![](figures/fig-ch5-03.png)

**Hình 4.5.** Thuật toán chuẩn hoá chuỗi biển số theo bộ luật ràng buộc vị trí

Ba nguyên tắc chịu lực: **thử regex *trước* khi sửa** (chuỗi đã hợp lệ thì mọi chỉnh sửa chỉ có thể làm hỏng); **không bao giờ vứt bỏ** — chuỗi không sửa được vẫn trả về với `is_valid_format=False` và được lưu; **giữ chuỗi thô** vào `raw_ocr_text`. Kết quả là `NormalizationOutcome` bất biến mang chuỗi thô, chuỗi cuối, cờ hợp lệ, kết quả phân loại và **danh sách bộ ba `(chỉ số, trước, sau)` cho từng ký tự đã sửa** — dấu vết kiểm toán mà chương đánh giá dựa vào.

**f) Xử lý nhập nhằng bằng số dòng.** `line_count == 1` **chứng minh** chuỗi là biển ô tô (xe máy luôn hai dòng), còn `line_count == 2` **không chứng minh gì** vì biển ô tô ngắn cũng hai dòng — cờ `is_ambiguous` được giữ, `KindDecision` trả *tập ứng viên* kèm cờ thay vì bịa thông tin đầu vào không chứa. Thứ tự `PATTERNS_BY_KIND`: `DIPLOMATIC` đầu (hình dạng không thể nhầm); `SPECIAL` trước các mẫu xe máy (danh sách mã đóng và hiếm); `MILITARY` cuối vì là trường hợp **nhận-ra-để-loại-trừ** — khớp `RE_MILITARY` nhưng không thuộc `CIVIL_KINDS` nên không bao giờ được báo là biển dân sự hợp lệ.

### 4.6.6. Ghép thành `ALPRPipeline` bằng tiêm phụ thuộc

`ALPRPipeline` là **đối tượng tổ hợp**: không giữ mô hình, chỉ sắp thứ tự giai đoạn, cắt ảnh, **đo thời gian từng giai đoạn** và **cô lập lỗi mức từng biển** — không chứa logic học sâu nên kiểm thử được bằng thành phần giả lập; `build_default_pipeline()` import ba lớp cụ thể **trong thân hàm**. `stage_times` luôn đủ năm khoá `("detect", "crop", "ocr", "normalize", "total")` — giai đoạn không chạy báo `0.0` thay vì vắng mặt; đây là thứ cho phép phân rã độ trễ (trên `best.pt`: OCR ~64,3%, detect ~34,2%) và cũng chính nó giúp phát hiện con số cũ "93,3%" là tạo tác của một lần đo trên hệ thống có lỗi crop. **Chính sách thất bại phân tầng:** ảnh không biển trả kết quả rỗng; OCR hỏng trên một biển thì biển đó `recognition=None`, biển khác vẫn xử lý; detector hỏng ném `DetectionError`; chuẩn hoá hỏng giữ nguyên kết quả thô và log. Cắt ảnh **kẹp lại lần hai** dù `BaseDetector` đã hứa — cắt là nơi duy nhất sai một đơn vị tạo mảng rỗng âm thầm; ảnh cắt là **bản sao**, không phải view, vì view sẽ ghim cả khung video trong bộ nhớ. `normalize_detailed(raw, line_count=...)` không thuộc `BaseNormalizer` nên pipeline dò bằng `getattr` và lùi về `normalize(raw)` nếu không có.

### 4.6.7. Nhận dạng họ biển và màu nền — `plate_color.py`

**a) Vấn đề đã quan sát: thông tin được tính ra rồi bị vứt đi.** Ảnh biển đỏ quân đội `KV6938` được OCR đọc **đúng** ở độ tin cậy 0,999 nhưng giao diện hiển thị "Sai định dạng biển số" — sai về phát biểu chứ không sai về tính toán: biển quân đội là biển hợp lệ nằm ngoài hệ dân sự (4.6.5f). Hai thông tin bị vứt trước khi tới CSDL: **họ biển** (`PlateKind`, chín giá trị từ `car` tới `military`/`unknown`) và **chuỗi hiển thị** do `format_for_display` dựng lại dấu phân cách (`29E01566` → `29E-015.66`). Bản sửa: **giữ lại** những gì đã tính (mục d, 4.7.2), và bổ sung nguồn bằng chứng mà chuỗi ký tự về nguyên tắc không thể mang — màu nền.

<!-- {{T4.6}} do chinh xac bo nhan mau nen bien so -->

**Bảng 4.4.** Độ chính xác bộ nhận màu nền trên bộ dữ liệu ngoài hiệu chỉnh

| Lớp nhãn người gán | Số ảnh | Đúng | Độ chính xác |
|---|---:|---:|---:|
| Biển vàng | 694 | 684 | **98,56%** |
| Biển trắng | 808 | 787 | **97,40%** |
| Biển xanh | 63 | 61 | **96,83%** |
| **Tổng** | **1.565** | **1.532** | **97,89%** |

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

