# CHƯƠNG 4. THIẾT KẾ VÀ CÀI ĐẶT HỆ THỐNG

Trên cơ sở lý thuyết ở Chương 2 và lựa chọn công nghệ ở Chương 3, chương này trình bày thiết kế và hiện thực của hệ thống trong cùng một mạch. Nguyên tắc trình bày: mọi mô tả đều phản ánh đúng mã nguồn thực tế; các chức năng chưa hoàn thiện và các số liệu chưa được đo lường đều được ghi chú rõ ràng. Chương gồm phân tích yêu cầu (4.1), kiến trúc (4.2), môi trường phát triển (4.3), bộ dữ liệu (4.4), huấn luyện mô hình (4.5), tầng AI (4.6), máy chủ và cơ sở dữ liệu (4.7), giao diện (4.8), Docker (4.9) và bảng đối chiếu cài đặt lệch thiết kế (4.10).

Trạng thái bản này: hệ thống chạy ALPRPipeline với mô hình chính thức models/best.pt (`/health` báo `model_loaded: true`, bộ nhận dạng `yolo:best.pt+paddleocr-PP-OCRv5-mobile`, mAP@0.5 = 0,9829); `StubPipeline` đã ra khỏi đường chạy chính. Mọi kết quả thực nghiệm trình bày ở Chương 5.

---

## 4.1. Phân tích yêu cầu

### 4.1.1. Khảo sát nhu cầu và các tác nhân

Nhận dạng biển số là bài toán nền tảng của bãi đỗ tự động, thu phí không dừng, kiểm soát ra vào và giám sát giao thông. Áp mô hình ALPR huấn luyện trên dữ liệu nước ngoài vào Việt Nam gặp bốn trở ngại. **Thứ nhất, biển hai dòng chiếm tỉ trọng lớn** (toàn bộ xe máy và một phần ô tô) trong khi đa số bộ dữ liệu quốc tế giả định biển một dòng; mức suy giảm này đã đo được: trên **bộ RodoSol-ALPR của Brazil**, OpenALPR nhận đúng 3.772/4.000 ô tô biển một dòng (94,3%) nhưng chỉ 1.827/4.000 xe máy biển hai dòng (45,7%), chênh **48,6 điểm phần trăm** [3]<!-- laroca_2022_crossdataset -->[33]<!-- laroca_2022_rodosol -->. **Thứ hai, quy chuẩn biển số có tính pháp lý và cấu trúc chặt**: Thông tư 79/2024/TT-BCA [4]<!-- bocongan_2024_tt79 -->, sửa đổi bởi TT 13/2025 [5]<!-- bocongan_2025_tt13 --> và TT 51/2025 [6]<!-- bocongan_2025_tt51 -->, thông số vật lý theo QCVN 08:2024/BCA [7]<!-- bocongan_2024_qcvn08 --> — cấu trúc chặt vừa là ràng buộc vừa là cơ hội thiết kế cho khối hậu xử lý dựa trên luật. **Thứ ba, điều kiện thu nhận ảnh khắc nghiệt**: che khuất, bụi bẩn, nghiêng, ngược sáng, ban đêm. **Thứ tư, không có phần cứng tăng tốc**: máy thực hiện không có GPU CUDA, mọi suy luận và trình diễn chạy trên CPU (mục 4.1.4a, 4.3.1).

> **Lưu ý phạm vi số liệu.** Cặp 94,3% / 45,7% đo trên **bộ RodoSol-ALPR của Brazil**, **không phải dữ liệu Việt Nam**; nhóm thực hiện chỉ dùng nó làm dẫn chứng định lượng rằng "biển hai dòng khó hơn" là sự kiện đo được, không phải cảm nhận.

Hệ thống có bốn tác nhân: **người vận hành** (đưa ảnh/video, xem kết quả, tra cứu), **người phân tích** (thống kê, lọc, xuất báo cáo), **nhà phát triển** (tích hợp REST API), **hội đồng đánh giá** (quan sát, phản biện). Do hệ thống chạy nội bộ/`localhost` (giả định A-04), đồ án **không xây dựng xác thực và phân quyền**; ba tác nhân đầu là các _vai trò_ trên cùng một giao diện, không phải các _tài khoản_.

### 4.1.2. Sơ đồ use case và ba use case chính

Ba use case chính — nhận dạng từ ảnh (UC-01), từ video (UC-02) và tra cứu lịch sử (UC-05) — đều được đặc tả theo cùng một khuôn: tác nhân, tiền điều kiện, luồng chính, luồng thay thế và hậu điều kiện.

### 4.1.3. Yêu cầu chức năng

Hệ thống có **34 yêu cầu chức năng** chia sáu nhóm, phân mức theo MoSCoW: 20 _Must_, 5 _Should_, 3 _Could_, 6 _Won't_. Sáu yêu cầu mức _Won't_ đến từ ba đợt thu gọn phạm vi: bốn yêu cầu thuần giao diện chuyển mức ngày 20/07/2026, và hai yêu cầu của nhóm video — xuất video đã chú thích cùng huỷ tác vụ đang chạy — chuyển mức ngày 03/08/2026. **Hai yêu cầu mức _Must_ đã bị đưa ra khỏi phạm vi là FR-4.1 và FR-2.5**, nêu rõ ở mục 6.2. Bảng đầy đủ từng mã yêu cầu ở **Phụ lục H.2**.

### 4.1.4. Yêu cầu phi chức năng

Các chỉ tiêu phi chức năng chia bảy nhóm — độ chính xác (NFR-A), hiệu năng (NFR-P), độ tin cậy (NFR-R), khả năng chịu tải (NFR-SC), khả năng bảo trì (NFR-M), bảo mật (NFR-S) và khả dụng (NFR-U) — mỗi chỉ tiêu kèm **ngưỡng tối thiểu, mục tiêu và phương pháp đo**. Hai ràng buộc chi phối toàn bộ nhóm hiệu năng: suy luận **chỉ trên CPU** (CON-02) và ngân sách độ trễ đầu cuối. Bảng đầy đủ ở **Phụ lục H.3**; kết quả đối chiếu từng chỉ tiêu ở mục 5.7.

## 4.2. Kiến trúc hệ thống

### 4.2.1. Nguyên tắc kiến trúc

**Kiến trúc sạch và quy tắc phụ thuộc:** phụ thuộc chỉ hướng vào trong, từ chi tiết dễ thay đổi (framework web, CSDL, giao diện) về quy tắc nghiệp vụ ổn định. Ở bài toán này, thứ ổn định là thuật toán nhận dạng biển số — phát hiện, cắt, đọc, chuẩn hoá theo quy chuẩn Việt Nam; thứ dễ đổi là FastAPI hay Flask, SQLite hay PostgreSQL. Do đó **đường ống AI nằm ở vòng trong cùng**, tầng web phụ thuộc nó chứ không ngược lại. SOLID vận dụng: _trách nhiệm đơn nhất_ — detector chỉ trả bounding box, recognizer chỉ trả chuỗi, normalizer chỉ chuẩn hoá — cho phép đo từng khối riêng; _thay thế Liskov_ — dùng theo nghĩa đen khi hệ thống chạy đường ống giả lập đúng hợp đồng đường ống thật; _đảo ngược phụ thuộc_ — tầng nghiệp vụ phụ thuộc hợp đồng trừu tượng, cài đặt tiêm từ ngoài.

Bốn ràng buộc kiến trúc: (1) **không trộn mã AI với mã API** (NFR-M1) ⇒ đường ống AI là package Python độc lập, không import framework web; (2) **mọi thành phần AI thay thế được** (NFR-M5) ⇒ đều đứng sau lớp trừu tượng; (3) **không hard-code đường dẫn** (NFR-M4) ⇒ mọi đường dẫn qua đối tượng cấu hình đọc từ biến môi trường; (4) **chạy được không cần GPU** (CON-02, NFR-C2) ⇒ thiết bị suy luận là tham số cấu hình, mặc định `cpu` — phát biểu là _cấu hình mặc định_ chứ không phải "chế độ dự phòng", nên đường chạy CPU là đường được kiểm thử thường xuyên nhất.

### 4.2.2. Kiến trúc phân tầng

![](figures/fig-ch4-02.png)

**Hình 4.1.** Kiến trúc phân tầng năm tầng và chiều phụ thuộc

Năm tầng: **1 — Trình bày** (giao diện, chỉ biết hợp đồng HTTP của tầng 2); **2 — API** (định tuyến, kiểm tra hợp lệ, ánh xạ ngoại lệ thành mã HTTP, sinh OpenAPI); **3 — Nghiệp vụ** (điều phối: tạo tác vụ, gọi đường ống, lưu tệp, ghi CSDL, gộp trùng, thống kê); **4 — AI** (phát hiện, nhận dạng, chuẩn hoá — **chỉ biết NumPy, OpenCV và thư viện học sâu**); **5 — Dữ liệu** (CSDL, kho tệp). **Điểm mấu chốt:** khối tầng AI **không có mũi tên nào đi lên**. Sau hai đợt thu gọn 2026-07-20, tầng trình bày còn **ba trang** nhưng **tầng 2–5 không đổi một dòng**: `POST /detect/frame`, `GET /statistics`, `GET /health` vẫn phục vụ và vẫn có kiểm thử tích hợp — phép thử ngoài dự kiến cho nguyên tắc phụ thuộc một chiều.

### 4.2.3. Tách tầng AI khỏi tầng API và cách kiểm chứng ràng buộc

**Ba lợi ích.** _Kiểm thử độc lập_: test chỉ cần nạp mảng NumPy, không phải dựng ứng dụng web. _Tái sử dụng trong script huấn luyện và đánh giá_: nếu logic tiền xử lý nằm lẫn trong hàm HTTP thì script đánh giá phải sao chép, hai bản sẽ lệch nhau, dẫn tới hệ quả nghiêm trọng nhất có thể xảy ra: **con số công bố không phản ánh đúng kết quả thực tế của hệ thống**. Mục 4.6.4g và 4.10 phân tích một trường hợp thuộc loại này. _Thay thế bộ nhận dạng mà không cần sửa mã tầng API_ đã được **kiểm chứng trên thực tế**: trong suốt giai đoạn xây dựng phần mềm và kiểm thử, hệ thống chạy với `StubPipeline`, toàn bộ tầng API, nghiệp vụ, cơ sở dữ liệu và giao diện đã được xây dựng và kiểm chứng **trước khi mô hình được huấn luyện**; khi trọng số đã sẵn sàng, việc chuyển sang `ALPRPipeline` chỉ là thao tác đổi thành phần phụ thuộc được tiêm vào, **không cần sửa đổi** router, service hay schema. Để tránh nhầm lẫn giữa trạng thái mô phỏng và vận hành thực tế, endpoint `/health` sẽ báo `degraded` khi `StubPipeline` còn đang hoạt động.

### 4.2.4. Luồng xử lý của đường ống AI và nhánh biển hai dòng

![](figures/fig-ch4-03.png)

**Hình 4.2.** Luồng xử lý của đường ống AI, các khối tô đỏ là nhánh biển hai dòng

**Nhánh biển hai dòng** là phần khó nhất của đồ án và là rủi ro đã xác định từ khâu lập kế hoạch (R-04). Bộ OCR dựng sẵn giả định văn bản một dòng ngang, nên với biển hai dòng chúng đọc theo thứ tự không xác định, ghép lẫn hoặc bỏ sót một dòng — cơ chế đứng sau chênh lệch 48,6 điểm phần trăm **đo trên bộ RodoSol-ALPR của Brazil** đã dẫn ở 4.1.1 [3]<!-- laroca_2022_crossdataset -->. Giải pháp: **tách vùng biển thành hai nửa, nhận dạng từng nửa, ghép theo thứ tự trên trước dưới sau** — mỗi nửa lúc này là một dòng ngang đúng giả định của bộ OCR (cài đặt ở 4.6.4).

### 4.2.5. Bảng tổng hợp các quyết định kiến trúc

Mỗi quyết định ghi kèm lý do và **đánh đổi phải chấp nhận** — một quyết định trình bày như không có nhược điểm là quyết định chưa cân nhắc đủ.

<!-- {{T4.2}} cac quyet dinh kien truc AD-01 den AD-08 -->

Tám quyết định kiến trúc được ghi thành hồ sơ AD-01 … AD-08, mỗi hồ sơ nêu **bối cảnh, phương án đã cân nhắc, quyết định và hệ quả phải chấp nhận** — dạng ghi chép này khiến một quyết định về sau có thể bị lật lại mà người lật hiểu được vì sao nó từng đúng. Các mục 4.2.1 – 4.2.4 trình bày bốn quyết định có ảnh hưởng rộng nhất.

Ghi chú: AD-03 không đổi sau khi gỡ trang Webcam vì ở ~5 FPS trên CPU, điểm nghẽn là suy luận chứ không phải giao thức. AD-04 cố ý **không** chọn tracking vì phức tạp hơn đáng kể và thêm một họ siêu tham số. AD-05 là quyết định duy nhất **đã thay đổi** so với phác thảo (_"PyTorch trước, ONNX nếu cần"_) — ghi nhận tường minh thay vì lặng lẽ sửa bảng. AD-06 kéo theo hai quyết định phái sinh đã cài đặt: `yolo11n` và **PP-OCRv5 mobile** — ràng buộc CPU thay đổi _lựa chọn mô hình_, không chỉ tốc độ.

---

## 4.3. Môi trường và công cụ phát triển

### 4.3.1. Cấu hình máy thực hiện và hệ quả của ràng buộc CPU

Toàn bộ cài đặt, kiểm thử và đo đạc chạy trên một máy trạm duy nhất: Windows 11 Pro; Intel Core i5-14600K, 14 nhân / 20 luồng; RAM 31,77 GiB; Intel UHD 770 — **không có GPU CUDA**; Python 3.13.12; Node.js 18.20.8; Docker 29.4.3. Cấu hình này **mâu thuẫn với mô tả môi trường ban đầu** (macOS Apple Silicon, Python 3.12); ghi nhận sai lệch thành văn bản là bước đầu của giai đoạn phân tích yêu cầu. Ràng buộc CPU để lại dấu vết cụ thể: NFR-P1 phát biểu thẳng cho CPU; AD-06 kéo theo `yolo11n` và PP-OCRv5 mobile; và vì huấn luyện trên CPU mất 1–3 ngày mỗi lượt, quy trình huấn luyện chạy được cả trên máy cá nhân lẫn nền tảng đám mây, với toàn bộ siêu tham số đặt trong một tệp cấu hình duy nhất. Trước khi bật bậc thử lại, p95 đầu cuối trên `models/best.pt` là **731 ms** (client-side) / **780 ms** (in-process); phép đo này dùng để định lượng đánh đổi. Ở cấu hình giao hàng, p95 chính thức là **1.143,10 ms**, đạt ngưỡng tối thiểu 1.500 ms nhưng chưa đạt mục tiêu 800 ms. Phân rã suy luận thuần cho thấy OCR chiếm **~64,3%**, phát hiện **~34,2%** (đối chiếu NFR-P1 ở 4.10).

### 4.3.2. Ba môi trường ảo Python tách biệt và bộ công cụ

Nhóm thực hiện dùng **ba môi trường ảo tách biệt**: một môi trường cho huấn luyện và xuất mô hình, một môi trường cho thử nghiệm nhận dạng ký tự, và một môi trường cho dịch vụ đang vận hành. Việc tách là bắt buộc vì thư viện nhận dạng ký tự kéo theo một bộ phụ thuộc **hạ cấp NumPy và thay thư viện thị giác máy tính bằng một biến thể lùi một phiên bản lớn** so với nhánh huấn luyện; nếu cài chung thì mỗi lần cài lại một nhánh âm thầm đổi phiên bản nhánh kia — lỗi không làm sập chương trình mà làm **kết quả đo không tái lập được**. Phân tách phản ánh ở `requirements.txt` và `requirements-inference.txt`, được `Dockerfile.backend` cài theo hai lớp riêng (4.9).

**Bộ công cụ:** FastAPI + Uvicorn; SQLAlchemy 2.x + Alembic; Pydantic v2; Ultralytics 8.4.101 chạy YOLO11 [10]<!-- jocher_2024_yolo11 -->; PaddleOCR 3.7.0 cho PP-OCRv5 [11]<!-- cui_2026_ppocrv5 -->; Vite + React + TypeScript; pytest + pytest-cov; Docker Compose. Docker dùng Python 3.12 trong khi local dùng 3.13 là **chủ ý**: container là nơi lấy lại phiên bản mục tiêu (NFR-C1).

---

## 4.4. Xây dựng bộ dữ liệu

### 4.4.1. Đường ống sáu bước và thành phần bộ dữ liệu

![](figures/fig-ch5-01.png)

**Hình 4.3.** Đường ống sáu bước xây dựng bộ dữ liệu

Mỗi bước là một kịch bản độc lập có giao diện dòng lệnh riêng và sinh báo cáo dạng dữ liệu có cấu trúc; một kịch bản điều phối chạy toàn chuỗi bằng một lệnh. **Kết quả:** **15.133 ảnh** hợp nhất từ **7 bộ công khai** (Roboflow, HuggingFace, Kaggle), còn **6 nguồn nguyên tố** sau khi loại **11.978 ảnh (44,2%)** bản sao từ **27.111 ảnh**; tổng 9 bộ tải về, 2 bộ nhãn mức ký tự tách riêng cho đánh giá OCR. Chia 70/20/10 thành **10.592 / 3.027 / 1.514 ảnh**. Bảng dưới **phải trích khi nói về dữ liệu của đồ án**; nguồn và giấy phép từng bộ ở **Phụ lục C.1**.

<!-- {{T4.4}} dong gop cua tung bo du lieu truoc va sau khu trung lap -->

**Bảng 4.1.** Đóng góp của từng bộ dữ liệu trước và sau khử trùng lặp

| #   | Bộ (slug)                   |    Vào gộp |        **Còn lại** |   Bị loại |
| --- | --------------------------- | ---------: | -----------------: | --------: |
| 1   | roboflow_school_fuhih       |      8.357 | **6.868** (45,38%) |     17,8% |
| 2   | hf_vn_plates_segment        |      4.578 | **4.375** (28,91%) |      4,4% |
| 3   | roboflow_traffic_camera     |      3.843 | **3.162** (20,89%) |     17,7% |
| 4   | roboflow_eric_nguyen        |        840 |    **353** (2,33%) |     58,0% |
| 5   | roboflow_demo_tracking      |        236 |    **235** (1,55%) |      0,4% |
| 6   | roboflow_cuong_ta           |      8.254 |    **140** (0,93%) | **98,3%** |
| 7   | roboflow_tran_ngoc_xuan_tin |      1.005 |              **0** |  **100%** |
|     | **Tổng**                    | **27.113** |         **15.133** | **44,2%** |

> **Ghi chú về phạm vi của mọi số liệu OCR.** Phân loại màu nền trên 2.801 ảnh cho: **2.736 biển trắng (97,68%)**, 20 vàng, 4 xanh, **0 đỏ, 0 ngoại giao**. Phát biểu đúng là _"1 − CER = 0,9454 trên một tập gồm 97,7% biển trắng"_, **không phải** _"trên biển số Việt Nam"_.

### 4.4.2. Khử trùng lặp chéo bộ và con số 44,2%

Các bộ công khai fork lẫn nhau, nên một ảnh nằm ở `train` dưới tên bộ này và `test` dưới tên bộ khác thì **độ chính xác test đang đo khả năng ghi nhớ**; con số tiêu đề vì vậy là số nhóm trùng **chéo bộ**. Vét cạn ~690 triệu cặp là bất khả thi nên script dùng **multi-index hashing**: cắt mã băm 64 bit thành `threshold + 1` dải — theo nguyên lý chuồng bồ câu, hai mã khác nhau tối đa `threshold` bit bắt buộc trùng khớp trên ít nhất một dải — nên tập ứng viên chứa mọi cặp thật rồi được xác minh chính xác: **thuật toán chính xác, không xấp xỉ**.

Có **hai phép đo trên hai mẫu số khác nhau**, trích một con số trần không nêu mẫu số là gây hiểu nhầm: **(a)** trên 7 bộ vào hợp nhất — mẫu số 27.111, ngưỡng Hamming 5, loại **11.978 = 44,2%**, **đã xoá thật**; **(b)** trên ngữ liệu còn lại — mẫu số 15.133, ngưỡng 10, chỉ ra **47,8% có thể loại** nhưng **chưa xoá**. 47,8% không mâu thuẫn 44,2%: ngưỡng lỏng hơn, và chỉ đo chứ chưa xoá. Hai hệ quả của tỷ lệ 44,2%: quy mô thật khác hẳn danh nghĩa (trường hợp cực đoan: một bộ vào hợp nhất với 1.005 ảnh và ra với **0** ảnh — lý do **không được cộng dồn số ảnh công bố của từng bộ**), và phân bố huấn luyện lệch vì bản sao tập trung ở các bộ được chép nhiều nhất. Bước chia tập giữ **mọi thành viên của một nhóm trùng lặp trong cùng một tập con** nên bản trùng không bị xoá cũng không rò rỉ được.

### 4.4.3. Giới hạn của perceptual hash: nó tóm tắt bố cục khung ảnh, không tóm tắt chiếc xe

Đây là **giới hạn không khắc phục được** bằng công cụ hiện có. Một lần kiểm tra độc lập ở ngưỡng Hamming 10 trên bộ v1 tìm thấy **619 cặp gần trùng giữa `train` và `test`**, toàn bộ ở dải d = 6–10; kiểm bằng mắt cho thấy **cùng một chiếc xe, cùng chuỗi biển số, ở cả hai phép chia tập**. Đường ống không bắt được vì bộ chia gom nhóm ở ngưỡng 5 rồi lần kiểm đầu cũng đo lại ở ngưỡng 5 và báo "0 cặp" — **lập luận vòng tròn**. Nâng ngưỡng cũng không giải quyết: phash rút ảnh thành 64 bit mô tả **cấu trúc tần số thấp của toàn khung**, nên hai xe khác nhau qua cùng một camera có khoảng cách phash rất nhỏ vì 90% khung hình giống hệt. Đánh đổi không thoát được: ngưỡng thấp bỏ sót cặp cùng xe khác ngày; ngưỡng cao gộp nhầm hàng nghìn ảnh xe khác nhau cùng camera. Bộ v3 chia lại với gom nhóm ngưỡng cao hơn và kiểm độc lập ở ngưỡng 10, nhưng nhóm thực hiện ghi nhận: **vẫn còn rò rỉ tồn dư không khử được bằng phash** — khắc phục đòi hỏi so khớp mức chuỗi biển số hoặc đặc trưng phương tiện. Hệ quả: baseline-416-v1.pt đạt mAP@0.5 = 0,9933 trên bộ v1 nhưng con số đó **không được báo cáo là "đạt"** vì tập test có rò rỉ đã đo được (4.10).

---

## 4.5. Huấn luyện mô hình

### 4.5.1. Siêu tham số và chi phí huấn luyện bộ phát hiện

Cấu hình lượt huấn luyện chính thức được trích từ tệp tham số do thư viện tự sinh — bản ghi _đã thực thi_ chứ không phải _dự định_; bảng đầy đủ ở **Phụ lục B.1**. Các giá trị chịu lực: mô hình khởi đầu YOLO11n tiền huấn luyện trên COCO (**2.590.035** tham số, biến thể nhỏ nhất do ràng buộc CPU); độ phân giải đầu vào **640** đúng theo NFR-A1 và NFR-A2; **20** epoch với kích thước lô 8; thuật toán tối ưu AdamW, tốc độ học ban đầu 0,001 theo lịch cosine; thiết bị CPU; hạt giống ngẫu nhiên cố định ở 42 kèm chế độ tất định. Riêng phép tăng cường lật ngang được **tắt hoàn toàn**, lệch có chủ ý so với giá trị mặc định: lật ngang sinh ra ký tự đối xứng gương, một phân bố không bao giờ xuất hiện trong thực tế. Vì giới hạn thời gian CPU chỉ chạy được **một lượt huấn luyện duy nhất**, không có nhiều seed để ước lượng phương sai; cố định seed ít nhất bảo đảm lượt này tái lập được — mọi chỉ số là kết quả **một lần chạy**, không có khoảng tin cậy (hạn chế ghi ở 5.9.3). **Chi phí:** mô hình đối chứng 40 epoch ở độ phân giải 416 trên bộ dữ liệu phiên bản 1 tiêu tốn **156 phút**; mô hình chính thức 20 epoch ở độ phân giải 640 trên bộ dữ liệu phiên bản 3 tiêu tốn **30,2 phút mỗi epoch, tổng 36.181 giây tương đương 10,05 giờ** trên CPU, số liệu lấy từ nhật ký huấn luyện do thư viện tự ghi. Ba yếu tố cùng thay đổi (số ảnh ×3,3, diện tích ×2,37, epoch giảm nửa) khiến so sánh ở mục 3.6 **không quy kết được nguyên nhân cho từng biến**.

### 4.5.2. Tiến triển của quá trình huấn luyện

![](figures/fig-train-curves.png)

**Hình 4.4.** Đường cong huấn luyện theo epoch — ba hàm mất mát và bốn chỉ số trên tập kiểm định

Ba hàm mất mát giảm đơn điệu và **không có dấu hiệu quá khớp**: mất mát hộp bao 1,252 → 0,809, mất mát phân lớp 0,833 → 0,313, mất mát phân phối 1,154 → 0,987; đường validation bám sát đường train suốt 20 epoch. Chỉ số trên tập validation đi lên rồi bão hoà sớm: mAP@0,5 đạt **0,9684 ngay ở epoch 1** và chỉ nhích lên **0,9830** ở epoch 20, trong khi mAP@0,5:0,95 — chỉ số nhạy với độ khít của hộp — tăng đáng kể hơn, **0,6526 → 0,7688**.

<!-- {{T4.5a}} tien trien chi so tren tap validation theo epoch -->

**Bảng 4.2.** Tiến triển chỉ số trên tập validation theo mốc epoch

|           Epoch           | Mất mát hộp bao | Mất mát phân lớp | Mất mát phân phối |    mAP@0.5 | mAP@0.5:0.95 |  Precision |     Recall |
| :-----------------------: | --------------: | ---------------: | ----------------: | ---------: | -----------: | ---------: | ---------: |
|             1             |          1,1705 |           0,6858 |            1,1513 | **0,9684** |   **0,6526** |     0,9552 |     0,9410 |
|             2             |          1,1861 |           0,5554 |            1,1307 | **0,9726** |   **0,6653** |     0,9700 |     0,9450 |
|             3             |          1,1647 |           0,5651 |            1,1098 | **0,9723** |   **0,6770** |     0,9731 |     0,9449 |
|             5             |          1,1074 |           0,4977 |            1,0863 | **0,9754** |   **0,6950** |     0,9765 |     0,9525 |
|            10             |          1,0548 |           0,4168 |            1,0686 | **0,9808** |   **0,7248** |     0,9850 |     0,9584 |
|            15             |          0,9420 |           0,3619 |            1,0205 | **0,9824** |   **0,7609** |     0,9846 |     0,9686 |
|            20             |          0,9204 |           0,3331 |            1,0105 | **0,9830** |   **0,7688** |     0,9846 |     0,9697 |
| **Epoch tốt nhất (= 20)** |      **0,9204** |       **0,3331** |        **1,0105** | **0,9830** |   **0,7688** | **0,9846** | **0,9697** |

### 4.5.3. Tinh chỉnh bộ nhận dạng ký tự và lý do không đưa vào bản bàn giao

PP-OCRv5 mobile huấn luyện trên chữ cảnh tổng quát; mục này trả lời bằng số câu hỏi fine-tune trên đúng miền dữ liệu thì được gì. **Cấu hình:** 30 epoch trên 6.672 mẫu (2.801 ảnh gốc + hai biến thể tăng cường mỗi ảnh), kiểm định 571 mẫu, charset đủ 36, khởi đầu từ `en_PP-OCRv5_mobile_rec_pretrained`; kết thúc train acc **0,9449**, val acc **0,8809**.

<!-- {{T4.5b}} so sanh fine-tune va model goc -->

**Bảng 4.3.** So sánh bộ nhận dạng gốc và bản tinh chỉnh trên cùng ngữ liệu

| Cấu hình                                   | A5 (chuỗi thô) | A6 (sau hậu xử lý) | Đúng định dạng | ms/ảnh |
| ------------------------------------------ | -------------: | -----------------: | -------------: | -----: |
| **Model gốc, det + rec** — _bản bàn giao_ |         0,6373 |         **0,7512** |         0,9443 |  328,8 |
| Model fine-tune, det + rec                 |         0,5998 |             0,6762 |         0,9018 |      — |
| Model gốc, chỉ rec                         |         0,6776 |             0,7508 |         0,9568 |   35,7 |
| Model fine-tune, chỉ rec                   |     **0,8618** |         **0,8758** |     **0,9886** |   38,5 |

## 4.6. Tầng AI — thiết kế và cài đặt

### 4.6.1. Tổ chức gói suy luận và ba lớp trừu tượng

Tầng AI là một gói Python độc lập, không phụ thuộc bất kỳ thành phần nào của tầng API; ràng buộc được kiểm chứng tự động (mục 4.2.3) để gói vận hành được trong môi trường notebook, kịch bản đo đạc và nền tảng huấn luyện đám mây.

Kiến trúc dựa trên ba lớp trừu tượng có hợp đồng thống nhất. Lớp phát hiện trả về danh sách vùng biển đã lọc ngưỡng và khử chồng lấn, trong đó danh sách rỗng là kết quả hợp lệ chứ không phải trạng thái lỗi. Lớp nhận dạng trả về chuỗi thô kèm độ tin cậy; việc sửa lỗi ký tự và kiểm tra hợp lệ không thuộc trách nhiệm của lớp này, và chính sự tách biệt đó cho phép định lượng đóng góp của khối hậu xử lý (mục 5.5.2). Lớp chuẩn hoá trả về cả chuỗi không hợp lệ, vì loại bỏ chúng sẽ làm mất đúng các trường hợp mà chương đánh giá cần thống kê. Hợp đồng chung là trả kết quả rỗng thay vì ném ngoại lệ, nhất quán với NFR-R2: không tìm thấy đối tượng và lỗi hệ thống là hai trạng thái khác nhau.

### 4.6.2. Bộ phát hiện

Bộ phát hiện là lớp thích ứng mỏng bao quanh thư viện Ultralytics: không thành phần nào ngoài lớp này tiếp xúc với cấu trúc dữ liệu nội bộ của thư viện. Phiên bản mô hình được ghim tường minh trong định danh mà lớp công bố, để mọi kết quả đo truy được về đúng bộ trọng số và việc nâng cấp thư viện không thay đổi ngầm mô hình đứng sau một kết quả đã công bố. Trọng số nạp ngay khi khởi tạo, nên lỗi thiếu tệp bộc lộ lúc khởi động thay vì lúc phục vụ yêu cầu đầu tiên. Lớp chấp nhận cả tệp trọng số đơn lẻ lẫn thư mục mô hình đã tối ưu cho CPU, do giới hạn ở một dạng sẽ loại bỏ cấu hình suy luận nhanh nhất trên phần cứng mục tiêu. Mọi hộp bao được kẹp về biên ảnh và hộp suy biến bị loại, nên tầng trên không nhận toạ độ ngoài khung.

### 4.6.3. Bộ nhận dạng ký tự

Bộ nhận dạng tuân theo cùng mô hình lớp thích ứng và cũng ghim phiên bản mô hình tường minh. Các mảnh văn bản được lọc theo tiêu chí hình học thay vì ngưỡng tin cậy, do bước nâng tương phản có thể sinh mảnh nhiễu được đọc thành chuỗi vô nghĩa ở độ tin cậy cao; độ tin cậy của cả chuỗi tổng hợp bằng trung bình có trọng số theo độ dài mảnh, vì trung bình cộng cho phép một mảnh một ký tự che lấp mảnh dài mang danh tính thực của biển số.

Cần lưu ý một giới hạn kỹ thuật ảnh hưởng trực tiếp đến hiệu năng: trên nền tảng mục tiêu, thư viện nhận dạng không cho phép kích hoạt thư viện tăng tốc oneDNN do khiếm khuyết phía thư viện, nên thư viện này bị vô hiệu hoá bằng một hằng số cấu hình có tài liệu kèm theo. Đây là tham số hiệu năng chứ không phải tham số độ chính xác, và giải thích một phần kết quả NFR-P1 ở mục 5.6: một hướng tăng tốc suy luận CPU thông dụng hiện không khả dụng vì lý do nằm ngoài phạm vi kiểm soát của đồ án.

### 4.6.4. Mô-đun xử lý biển hai dòng

**a) Cơ sở của bài toán.** Bộ nhận dạng dựa trên kiến trúc CRNN kết hợp hàm mất mát CTC, vốn giả định căn chỉnh đơn điệu giữa cột ảnh và chuỗi ký tự — giả định chỉ đúng với văn bản một dòng. Chồng lên đó, mô-đun nhận dạng chuẩn hoá mọi ảnh về chiều cao cố định 48 điểm ảnh [34]<!-- paddlepaddle_2026_textrecognition -->. Biển xe máy Việt Nam 140 × 190 mm theo QCVN 08:2024/BCA [7]<!-- bocongan_2024_qcvn08 --> có tỉ lệ khung hình xấp xỉ 1,36; sau chuẩn hoá, mỗi hàng ký tự chỉ còn khoảng 24 điểm ảnh, thấp hơn ngưỡng mà nét chữ còn tách rời. Mức nghiêm trọng đã được định lượng: trên bộ RodoSol-ALPR của Brazil, OpenALPR đạt 94,3% trên biển ô tô một dòng nhưng chỉ 45,7% trên biển xe máy hai dòng [3]<!-- laroca_2022_crossdataset -->[33]<!-- laroca_2022_rodosol -->. Cần lưu ý cặp số liệu này đo trên dữ liệu Brazil, chỉ được trích như dẫn chứng tương đương về định lượng chứ không phải số liệu Việt Nam.

**b) Ước lượng số dòng.** Số dòng suy từ tỉ lệ chiều rộng trên chiều cao của vùng biển, ngưỡng phân loại 2,5: tỉ lệ nhỏ hơn ngưỡng được xếp vào nhóm hai dòng. Đây là đề xuất của đồ án, không phải quy định pháp lý — quy chuẩn chỉ cung cấp ba tỉ lệ vật lý 4,727, 2,000 và 1,357. Ngưỡng được chọn lệch về phía hai dòng vì đường xử lý hai dòng suy giảm êm khi gặp đầu vào một dòng, chiều ngược lại thì không. Dải 2,5–3,0 vẫn là vùng bất định do biển một dòng chụp nghiêng lớn có thể cho tỉ lệ rơi vào khoảng này; định lượng tần suất thuộc Chương 5.

**c) Phân tách hai nửa có chồng lấn.** Vùng biển được cắt thành hai nửa theo chiều dọc, nửa trên kết thúc tại 5/12 chiều cao và nửa dưới bắt đầu tại 1/3, tạo vùng chồng lấn bằng 1/12 chiều cao biển. Thiết kế xuất phát từ tính bất đối xứng của chi phí sai sót: cắt cụt chân hoặc đỉnh ký tự phá huỷ thông tin không phục hồi được, trong khi lọt vài hàng điểm ảnh của nửa còn lại chỉ được xử lý như nền.

**d) Ghép ngang.** Hai nửa được ghép theo chiều ngang bằng phép `hstack`, chiều cao chung lấy bằng giá trị lớn nhất trong ba đại lượng: chiều cao nửa trên, chiều cao nửa dưới và 48 điểm ảnh — đúng bằng chiều cao đầu vào cố định của mô-đun nhận dạng. Nửa trên đặt bên trái để bảo toàn thứ tự đọc. Sau khi ghép, một hàng ký tự duy nhất nhận trọn ngân sách 48 điểm ảnh thay vì hai hàng chia nhau, vô hiệu hoá đúng nguyên nhân đã phân tích ở mục a.

**e) Tiền xử lý ảnh biển.** Ba bước độc lập, mỗi bước bật tắt riêng để phục vụ thí nghiệm bóc tách đóng góp: chuyển thang xám, do ký tự không mang thông tin phân biệt trong kênh màu; cân bằng lược đồ xám thích nghi có giới hạn tương phản (CLAHE, hệ số 2,0 trên ô 8 × 8), vì bề mặt phản quang tạo mảng chói cục bộ mà cân bằng toàn cục không xử lý được [35]<!-- sutikno_2025_clahe -->; và khử nhiễu bằng lọc song phương thay cho làm mờ Gauss, vì lọc song phương bảo toàn biên — yếu tố quyết định để phân biệt các cặp ký tự đồng hình như `8` và `B`. Ảnh biển do bộ phát hiện sinh ra thường chỉ cao 20–40 điểm ảnh nên được phóng đại về 64 điểm ảnh trước khi đọc.

**f) Bước phục hồi dòng trên.** Chế độ hỏng quan sát được: chuỗi `29E-015.66` chỉ đọc được thành `015.66` do sau khi ghép, bộ phát hiện văn bản chỉ xác định một vùng chữ và bỏ qua cụm mã tỉnh cùng ký tự sê-ri. Giả thuyết ban đầu — loại bỏ phép ghép, đọc riêng từng nửa rồi nối chuỗi — được kiểm chứng trên 200 biển hai dòng có nhãn và bị bác bỏ dứt khoát: độ chính xác giảm từ 64,5% xuống 3,5%, không thắng ở trường hợp nào (mục 5.5.6). Nguyên nhân nằm ở chính vùng chồng lấn tại mục c: khi hai nửa được đọc riêng, dải chồng lấn bị nhận dạng hai lần và sinh ký tự thừa giữa chuỗi. Kết quả đảo ngược cách hiểu ban đầu — trên dải liền mạch, vùng lặp nằm giữa hai cụm ký tự và bị bộ phát hiện văn bản loại bỏ, điều không xảy ra khi hai ảnh được xử lý tách biệt.

Thiết kế cuối cùng vì vậy giữ nguyên chiến lược ghép, chỉ bổ sung một bước phục hồi có điều kiện chặt: chỉ kích hoạt khi đồng thời vùng biển được phân loại hai dòng, chuỗi sau chuẩn hoá không hợp lệ, và chuỗi thô khác rỗng. Khi đó hệ thống nhận dạng thêm một lượt trên riêng nửa trên, ghép với chuỗi thô rồi chuẩn hoá lại; kết quả mới chỉ được chấp nhận nếu vượt kiểm tra định dạng. Tính chất không làm suy giảm kết quả mang bản chất cấu trúc: cổng chỉ mở khi kết quả đã không hợp lệ, nên tập bị can thiệp và tập đang đúng là hai tập rời nhau. Mức cải thiện đo được là +1,86 và +0,50 điểm phần trăm trên hai mẫu độc lập, 0 trường hợp bị làm hỏng, chi phí khoảng 15–21 ms mỗi biển hai dòng — khắc phục một chế độ hỏng cụ thể chứ không tác động tới điểm nghẽn chính.

**g) Một giới hạn về phương pháp đo.** Kịch bản sinh các chỉ số NFR-A4 đến NFR-A7 ban đầu gọi trực tiếp bộ nhận dạng và bộ chuẩn hoá thay vì đi qua tầng điều phối, khiến logic đặt tại tầng điều phối không được phản ánh trong số liệu công bố. Biện pháp khắc phục là tách bước phục hồi thành hàm độc lập cấp mô-đun để cả đường chạy sản phẩm lẫn công cụ đo cùng gọi một cài đặt. Bài học vượt ra ngoài phạm vi biển hai dòng: một công cụ đo đi tắt qua tầng điều phối sẽ đo một hệ thống khác với hệ thống được bàn giao. Cần lưu ý biện pháp này về sau vẫn chưa đủ — cùng loại sai lệch đã tái diễn, phân tích tại mục 5.5.6.

### 4.6.5. Bộ luật hậu xử lý theo vị trí

Bộ phát hiện và bộ nhận dạng đều dùng mô hình có sẵn; khối hậu xử lý là thành phần do nhóm thực hiện tự thiết kế và là đóng góp kỹ thuật chính. Khối tuân ba nguyên tắc: thuần khiết về mặt hàm số, không vào/ra và không giữ trạng thái toàn cục khả biến; biểu thức chính quy sinh tự động từ các tập ký tự thay vì viết tay, loại trừ khả năng mẫu lệch khỏi bảng dữ liệu mà nó mã hoá; mọi lớp ký tự là hằng số có tên.

**a) Tập mã tỉnh.** Khối lưu 81 mã tỉnh đang sử dụng theo phụ lục Thông tư 51/2025/TT-BCA [6]<!-- bocongan_2025_tt51 -->, song song tập 8 mã không bao giờ được cấp: 13, 42, 44, 45, 46, 87, 91 và 96. So với biểu thức tổng quát chấp nhận mọi cặp chữ số, ràng buộc này bác bỏ được các chuỗi không tồn tại trên thực tế; lưu tường minh cả tập không sử dụng cho phép kiểm thử khẳng định hai tập phủ đúng dải 11–99.

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

Chính sách xử lý lỗi phân tầng theo mức ảnh hưởng: ảnh không chứa biển số trả kết quả rỗng; lỗi nhận dạng trên một biển chỉ vô hiệu hoá biển đó, các biển còn lại vẫn được xử lý; lỗi ở bộ phát hiện làm dừng toàn bộ yêu cầu; lỗi chuẩn hoá giữ nguyên kết quả thô. Thao tác cắt ảnh kẹp toạ độ **thêm một lần nữa** dù lớp phát hiện đã bảo đảm, vì cắt ảnh là nơi duy nhất mà sai lệch một đơn vị tạo mảng rỗng không kèm cảnh báo; ảnh cắt được tạo dưới dạng bản sao thay vì khung nhìn, tránh giữ toàn bộ khung hình gốc trong bộ nhớ khi xử lý video.

### 4.6.7. Nhận dạng họ biển và màu nền

**a) Vấn đề đặt ra.** Hệ thống ban đầu tính ra họ biển và chuỗi hiển thị có dấu phân cách nhưng loại bỏ chúng trước khi ghi vào cơ sở dữ liệu, nên một biển quân đội được nhận dạng chính xác ở độ tin cậy 0,999 vẫn bị hiển thị là sai định dạng — phát biểu không chính xác, do biển quân đội là biển hợp lệ nằm ngoài hệ dân sự (mục 4.6.5f). Hướng khắc phục gồm hai phần: lưu giữ thông tin đã tính (mục 4.7.2), và bổ sung nguồn bằng chứng mà chuỗi ký tự về nguyên tắc không thể mang, đó là màu nền.

**b) Cơ sở của bằng chứng bổ trợ.** Hai nguồn bằng chứng bù trừ cho nhau. Theo Thông tư 79/2024/TT-BCA, biển vàng của xe kinh doanh vận tải mang đúng cùng cấu trúc ký tự với biển trắng của xe cá nhân nên không biểu thức chính quy nào phân biệt được; ngược lại, biển ngoại giao có nền trắng giống biển cá nhân nên riêng màu nền cũng không đủ. Chỉ cặp thuộc tính gồm chuỗi ký tự và màu nền mới định danh được loại phương tiện.

**c) Thiết kế bộ phân loại màu.** Bộ phân loại chuyển ảnh sang không gian HSV, thống kê tỉ lệ điểm ảnh theo từng dải màu và chọn dải chiếm ưu thế, với ba quyết định đáng lưu ý. Chỉ vùng trung tâm được lấy mẫu, biên thu vào 18% mỗi phía, do khung phát hiện hiếm khi ôm sát mép biển và màu thân xe phía sau có thể chiếm ưu thế nếu lấy cả rìa. Điểm ảnh thuộc ký tự không bị loại trừ, vì ký tự chiếm thiểu số diện tích và việc bổ sung một bước phân đoạn ký tự sẽ đưa vào khâu kém ổn định hơn chính khâu nó bảo vệ. Bộ phân loại trả kết quả không xác định khi tỉ lệ dải chiếm ưu thế không đạt 30%: kết luận sai về màu tương đương khẳng định một loại phương tiện không chứng minh được, trong khi thừa nhận không xác định được chỉ là ghi nhận một giới hạn.

**d) Hợp nhất chuỗi ký tự và màu nền.** Với chuỗi như `80A12345`, bốn họ biển đều là ứng viên hợp lệ và bộ chuẩn hoá mặc định chọn họ phổ biến nhất — đúng với đa số nhưng gây sai lệch ngầm đối với xe cơ quan nhà nước mang biển nền xanh. Cơ chế hợp nhất cho phép màu nền nâng cấp một ứng viên mà bộ luật ký tự đã coi là hợp lý. Ràng buộc an toàn quan trọng hơn chính tác dụng của cơ chế: nếu phán quyết ban đầu không nằm trong tập ứng viên thì kết quả giữ nguyên, nên màu nền không thể tạo ra họ biển mà bộ luật ký tự đã bác bỏ. Khi họ biển ưu tiên có cả biến thể ô tô và xe máy, hệ thống phân định theo số dòng; nếu số dòng mâu thuẫn cả hai thì giữ phán quyết ban đầu, theo nguyên tắc đại lượng đo được từ hình học ưu tiên hơn đại lượng suy ra từ thống kê điểm ảnh. Chỉ màu xanh nằm trong bảng ưu tiên vì đây là màu duy nhất chuỗi ký tự hoàn toàn không phân biệt được; màu vàng không đổi họ biển mà chỉ đổi mục đích sử dụng nên được lưu như trường độc lập.

**e) Độ chính xác đo được.** Bộ phân loại được đánh giá trên bộ dữ liệu ảnh biển cắt sẵn có nhãn màu do người gán và chưa từng được hiệu chỉnh theo bộ này — phép đo vì vậy nằm ngoài dữ liệu hiệu chỉnh.

<!-- {{T4.6}} do chinh xac bo nhan mau nen bien so -->

**Bảng 4.4.** Độ chính xác bộ nhận màu nền trên bộ dữ liệu ngoài hiệu chỉnh

| Lớp nhãn người gán |    Số ảnh |      Đúng | Độ chính xác |
| ------------------ | --------: | --------: | -----------: |
| Biển vàng          |       694 |       684 |   **98,56%** |
| Biển trắng         |       808 |       787 |   **97,40%** |
| Biển xanh          |        63 |        61 |   **96,83%** |
| **Tổng**           | **1.565** | **1.532** |   **97,89%** |

Ba giới hạn cần nêu kèm kết quả trên. Thứ nhất, 542 ảnh đã bị loại khỏi phép đo, gồm toàn bộ lớp không xác định và các ảnh chụp ban đêm hoặc hồng ngoại mà chính người gán nhãn cũng không xác định được màu. Thứ hai, dạng lỗi chủ đạo là biển trắng bị phân loại thành biển xanh — 21 trong tổng số 33 trường hợp sai — do một số điểm ảnh ám lạnh vượt ngưỡng bão hoà. Thứ ba, phạm vi phép đo hẹp hơn phạm vi mô-đun: bộ dữ liệu không chứa biển đỏ và biển ngoại giao nên hai nhánh này chưa có số liệu đánh giá.

Cần lưu ý thêm rằng toàn bộ ảnh của bộ dữ liệu này đã bị biến đổi tỉ lệ về khung vuông trước khi công bố, nên bộ không dùng được để đánh giá độ chính xác nhận dạng ký tự — phép biến đổi phá huỷ tỉ lệ khung hình mà thuật toán ước lượng số dòng dựa vào. Màu nền không chịu ảnh hưởng, do đó bộ dữ liệu chỉ được dùng cho đúng câu hỏi về màu sắc.

## 4.7. Máy chủ và cơ sở dữ liệu

### 4.7.1. Kiến trúc phân tầng và tầng nghiệp vụ

Máy chủ được tổ chức thành năm tầng với luồng phụ thuộc một chiều nghiêm ngặt, trong đó tầng lõi được mọi tầng khác sử dụng nhưng không phụ thuộc tầng nào. Ba quy tắc chi phối toàn bộ tầng nghiệp vụ.

Thứ nhất, tầng định tuyến không chứa truy vấn: mọi truy cập dữ liệu đi qua tầng kho dữ liệu, nhờ đó một thay đổi lược đồ chỉ có bán kính ảnh hưởng trong phạm vi một mô-đun. Thứ hai, tầng kho dữ liệu chỉ đẩy thay đổi xuống phiên làm việc mà không bao giờ tự xác nhận giao dịch: việc lưu một lượt nhận dạng cùng toàn bộ biển số thuộc lượt đó là một thao tác logic duy nhất, và xác nhận giao dịch giữa chừng sẽ để lại trạng thái không nhất quán mà từng bản ghi riêng lẻ vẫn hợp lệ; ranh giới giao dịch vì vậy thuộc về tầng dịch vụ. Thứ ba, khoá sắp xếp trong truy vấn được ánh xạ qua danh sách cho phép tường minh thay vì truy xuất thuộc tính động, bởi cách thứ hai biến một tham số không hợp lệ thành lỗi máy chủ thay vì lỗi yêu cầu.

Về xử lý lỗi, mỗi ngoại lệ mang hai mô tả cho hai đối tượng đọc khác nhau: một thông điệp tiếng Việt ngắn gọn kèm hành động khắc phục, đi vào thân phản hồi HTTP; và một mô tả kỹ thuật chỉ đi vào nhật ký hệ thống. Cây ngoại lệ được ánh xạ trực tiếp sang mã trạng thái HTTP, kèm một bộ xử lý bắt tất cả nhằm bảo đảm ngoại lệ ngoài dự kiến không làm lộ vết ngăn xếp ra phía người dùng (NFR-S4). Nhật ký được ghi theo định dạng có cấu trúc, mỗi bản ghi là một đối tượng dữ liệu kèm định danh yêu cầu truyền ngầm qua ngữ cảnh thực thi; điều này là bắt buộc vì nhật ký của tác vụ video xen kẽ với nhật ký của các yêu cầu đồng thời, và văn bản thuần không cho phép tách lại chuỗi sự kiện của một yêu cầu cụ thể.

Cần lưu ý rằng phần lớn sự cố gặp phải trong quá trình cài đặt nằm ở ranh giới giữa mã nguồn và môi trường thực thi — nguồn cấu hình, tầng lưu trữ và bảng mã đầu ra — và đều vượt qua được kiểm thử đơn vị. Đây là lập luận thực nghiệm cho yêu cầu bộ kiểm thử phải bao gồm kiểm thử tích hợp chạy trên đường dẫn thật, chứ không chỉ kiểm thử đơn vị với thành phần giả lập.

### 4.7.2. Thiết kế cơ sở dữ liệu

**a) Lược đồ.** Cơ sở dữ liệu gồm hai bảng có quan hệ một–nhiều: bảng tác vụ ghi nhận mỗi lần sử dụng hệ thống, và bảng lịch sử ghi nhận mỗi biển số được phát hiện. Việc tách thành hai bảng là điều kiện để thống kê đếm đúng, bởi _lượt nhận dạng_ và _biển số phát hiện được_ là hai đại lượng khác nhau: một ảnh chứa ba phương tiện tạo ra một lượt và ba bản ghi. Gộp hai khái niệm sẽ làm số lượt sử dụng bị đánh giá cao hơn thực tế đúng bằng số biển số trung bình trên mỗi ảnh.

**b) Hai quyết định thiết kế dữ liệu đáng chú ý.** Thứ nhất, chuỗi ký tự thô do bộ nhận dạng trả về và chuỗi đã qua chuẩn hoá được lưu song song trong hai cột riêng biệt. Đây là điều kiện cần để định lượng đóng góp của khối hậu xử lý: hiệu số giữa độ chính xác tính trên hai cột này chính là chỉ số NFR-A6 trừ NFR-A5 báo cáo ở mục 5.5.2. Thứ hai, hệ thống lưu số ký tự thuộc dòng trên của biển hai dòng, nhằm giải quyết một trường hợp nhập nhằng về nguyên tắc: chuỗi tám ký tự của biển hai dòng có thể được nhóm theo hai cách đều hợp lệ, và ranh giới giữa hai dòng — thông tin duy nhất phân định được — bị chính bước ghép ngang loại bỏ. Giá trị này thu được không tốn thêm chi phí tính toán vì bộ nhận dạng trả về một mảnh kết quả cho mỗi nửa ảnh.

### 4.7.3. Giao diện lập trình

Hệ thống cung cấp giao diện theo phong cách REST với tài liệu đặc tả sinh tự động. Các điểm cuối nghiệp vụ nằm dưới một tiền tố chung, riêng điểm cuối kiểm tra tình trạng đặt ở gốc để hệ thống giám sát và cơ chế kiểm tra sức khoẻ của môi trường container không phụ thuộc vào phiên bản giao diện. Tổng cộng có mười thao tác HTTP trên chín đường dẫn; bảng đặc tả đầy đủ từng điểm cuối được trình bày ở **Phụ lục F.1**.

Bốn quyết định thiết kế đáng ghi nhận. Yêu cầu xử lý video trả về mã trạng thái chấp nhận thay vì mã thành công, do một video 60 giây cần khoảng 200 giây xử lý trên CPU và không client nào chờ được; mã chấp nhận phản ánh đúng ngữ nghĩa "đã tiếp nhận, đang xử lý". Trường hợp ảnh không chứa biển số trả về mã thành công kèm danh sách rỗng thay vì mã lỗi, vì kết quả nhận dạng vẫn tồn tại và là tập rỗng (NFR-R2); trả về mã lỗi sẽ loại toàn bộ trường hợp âm khỏi thống kê. Chức năng tìm kiếm đối chiếu đồng thời chuỗi đã chuẩn hoá và chuỗi thô, để người dùng nhớ dạng nào cũng tra được. Cuối cùng, hai chỉ số thống kê về số lượt và số biển số được trả về tách biệt, kèm mô tả tường minh trong tài liệu đặc tả nhằm ngăn việc gộp nhầm hai đại lượng đã phân tích tại mục 4.7.2a.

### 4.7.4. Phương án lùi phải thất bại theo cách quan sát được

Trong giai đoạn chưa có mô hình đã huấn luyện, hệ thống vận hành với một đường ống mô phỏng sinh kết quả có cấu trúc hợp lệ nhưng không phản ánh nội dung ảnh. Cách làm này chính đáng ở thời điểm đó vì cho phép xây dựng và kiểm thử toàn bộ giao diện lập trình, cơ sở dữ liệu và giao diện người dùng trước khi mô hình sẵn sàng.

Vấn đề nảy sinh khi đường ống mô phỏng được đặt làm phương án lùi cho tình huống không nạp được mô hình. Khi đó một triển khai bị cấu hình sai sẽ đáp lại mọi yêu cầu bằng một biển số có định dạng thuyết phục nhưng hoàn toàn hư cấu — chế độ hỏng mang biểu hiện của một hệ thống hoạt động bình thường, và là dạng nguy hiểm nhất đối với hệ thống có ghi dữ liệu vào cơ sở dữ liệu.

Thiết kế hiện tại phân vai rõ ba đường ống. Đường ống thật thực hiện nhận dạng và báo trạng thái bình thường. Đường ống không khả dụng là phương án lùi mặc định: nó ném ngoại lệ và không sinh ra bất kỳ kết quả nào, đồng thời báo trạng thái suy giảm. Đường ống mô phỏng chỉ được kích hoạt khi người vận hành đặt biến môi trường tương ứng một cách tường minh. Khi thiếu trọng số, dịch vụ vẫn khởi động — một tiến trình từ chối khởi động không truyền đạt được nguyên nhân — nhưng mỗi yêu cầu đều trả về lỗi rõ ràng. Nguyên tắc rút ra: một phương án lùi phải thất bại rõ ràng và quan sát được, thay vì thay thế thất bại bằng dữ liệu thiếu cơ sở.

## 4.8. Giao diện người dùng

### 4.8.1. Cấu trúc và các màn hình

Giao diện là ứng dụng một trang xây dựng trên React và TypeScript, gồm ba màn hình: nhận dạng ảnh, nhận dạng video và tra cứu lịch sử. Điều hướng được thiết kế phẳng có chủ ý — cả ba màn hình truy cập trực tiếp từ thanh điều hướng — còn chi tiết bản ghi và hộp xác nhận xoá hiển thị dưới dạng hộp thoại chồng lên trang lịch sử để không làm mất ngữ cảnh bộ lọc đang áp dụng.

Toàn bộ giao tiếp với máy chủ tập trung tại một tầng gọi API duy nhất, nơi duy nhất trong giao diện có hiểu biết về thư viện HTTP và mã trạng thái; các thành phần hiển thị chỉ nhận dữ liệu đã có kiểu hoặc đối tượng lỗi đã chuẩn hoá. Không địa chỉ máy chủ nào được viết cứng: gốc địa chỉ đọc từ biến môi trường tại thời điểm biên dịch và mặc định là rỗng, tương ứng cấu hình cùng nguồn gốc.

Cần lưu ý rằng thiết kế ban đầu có năm màn hình. Màn hình nhận dạng thời gian thực và màn hình tổng quan đã được đưa ra khỏi phạm vi trong hai đợt thu gọn ngày 20/07/2026, kéo theo bốn yêu cầu chức năng chuyển sang mức không thực hiện — trong đó có một yêu cầu ở mức bắt buộc, được nêu rõ tại mục 6.2. Các điểm cuối tương ứng ở phía máy chủ vẫn hoạt động và vẫn có kiểm thử tích hợp; điều bị loại bỏ là hàm gọi phía giao diện, không phải bản thân điểm cuối.

### 4.8.2. Nguyên tắc trải nghiệm người dùng

Mọi thành phần hiển thị dữ liệu đều cài đặt đủ bốn trạng thái: đang tải, có dữ liệu, rỗng và lỗi. Thiếu trạng thái đang tải khiến giao diện có biểu hiện như bị treo và người dùng thao tác lại, làm tăng tải không cần thiết; thiếu trạng thái rỗng khiến màn hình trắng không phân biệt được với lỗi hệ thống. Trạng thái rỗng xuất hiện với ba ý nghĩa cần ba thông điệp khác nhau: chưa có lượt nhận dạng nào, bộ lọc không khớp bản ghi nào, và ảnh không chứa biển số. Ý nghĩa thứ ba là biểu hiện ở tầng giao diện của cùng một quyết định đã áp dụng tại tầng giao diện lập trình và tầng suy luận: không tìm thấy đối tượng không phải là lỗi.

Thông báo lỗi được viết bằng tiếng Việt theo cấu trúc ba phần — hiện tượng, nguyên nhân và hành động khắc phục (NFR-U3) — trong khi chi tiết kỹ thuật được chuyển hướng vào nhật ký phía máy chủ thay vì bị loại bỏ. Giao diện hiển thị đồng thời chuỗi thô và chuỗi đã chuẩn hoá khi hai chuỗi khác nhau, qua đó biến một cột dữ liệu phục vụ nghiên cứu thành bằng chứng quan sát được ngay trong quá trình trình diễn; do chỉ hiển thị khi có thay đổi, giao diện không bị rối bởi phần lớn trường hợp mà khối hậu xử lý không can thiệp.

Một nguyên tắc thiết kế đáng ghi nhận thuộc về client nhận dạng thời gian thực. Do tốc độ suy luận trên CPU chỉ đạt khoảng 5 khung hình mỗi giây, một vòng lặp gửi yêu cầu theo chu kỳ cố định sẽ khởi tạo yêu cầu mới trước khi yêu cầu trước đó hoàn tất, khiến hàng đợi tăng không giới hạn. Giải pháp là duy trì đúng một yêu cầu đang xử lý tại mỗi thời điểm; khung hình đến trong lúc kênh bận sẽ bị bỏ qua thay vì xếp hàng, do khung hình kế tiếp luôn cập nhật hơn khung hình bị bỏ. Màn hình tương ứng đã được đưa ra khỏi phạm vi, nhưng nguyên tắc này vẫn là khuyến nghị bắt buộc cho mọi client sử dụng điểm cuối nhận dạng theo khung hình.

## 4.9. Triển khai bằng Docker

Đóng gói phục vụ NFR-C1: môi trường chạy tái lập được, không phụ thuộc máy cá nhân. Ảnh Docker của máy chủ được dựng hai giai đoạn, cài **hai tệp khai báo phụ thuộc thành hai lớp riêng** để thay đổi một tầng không làm mất bộ đệm tầng kia (hệ quả trực tiếp của mục 4.3.2), chạy dưới người dùng không đặc quyền, giới hạn tường minh số luồng tính toán để hai container không cạnh tranh nhân CPU đến mức cùng chậm, và đặt thời gian chờ khởi động của cơ chế kiểm tra sức khoẻ đủ dài cho việc nạp trọng số. Ảnh Docker của giao diện được dựng rồi phục vụ tĩnh qua máy chủ web nhẹ — ảnh chạy không chứa Node hay mã nguồn. **Trọng số mô hình không nằm trong ảnh Docker** mà gắn từ ngoài, cùng một volume riêng cho bộ đệm mô hình PaddleOCR — không có volume này thì mỗi lần `down && up` phải tải lại vài trăm MB và không có mạng thì container không khởi động được. Bảng biến môi trường ở **Phụ lục F.2**. **Trạng thái kiểm chứng:** `docker compose config` hợp lệ; đo hiệu năng trong container thuộc Chương 5.

---

## 4.10. Những chỗ cài đặt lệch khỏi thiết kế, và lý do

Nguyên tắc: **mọi điểm lệch đều được nêu, kể cả những điểm chưa được giải quyết.**

<!-- {{T4.10a}} tong hop cac diem lech giua thiet ke va cai dat -->

**Bảng 4.5.** Tổng hợp chín điểm lệch giữa thiết kế và cài đặt

|  #  | Thiết kế                                          | Cài đặt thực tế                                                             | Loại lệch                       | Trạng thái             |
| :-: | ------------------------------------------------- | --------------------------------------------------------------------------- | ------------------------------- | ---------------------- |
|  1  | `StubPipeline` là phương án lùi khi thiếu mô hình | `UnavailablePipeline` là phương án lùi; stub chỉ chạy khi opt-in tường minh | **Cải tiến so với thiết kế**    | Đã giải quyết          |
|  2  | Một môi trường ảo Python                          | **Ba** môi trường ảo tách biệt                                              | Bắt buộc bởi xung đột phụ thuộc | Đã giải quyết          |
|  3  | FR-2.6: có nút huỷ tác vụ video                   | Đưa ra khỏi phạm vi 03/08/2026; nút đã gỡ khỏi giao diện                    | **Thu hẹp phạm vi**             | ➖ Không áp dụng       |
|  4  | Mô hình chính thức imgsz=640 trên phép chia tập sạch      | Đã có models/best.pt (imgsz=640, phép chia tập v3, mAP@0.5 0,9829)                  | Đúng thiết kế                   | ✅ Đã giải quyết       |
|  5  | NFR-P1: độ trễ E2E p95 ≤ 800 ms                   | Đo được **1.143,10 ms** — dưới sàn 1.500 ms nhưng vượt mục tiêu 800 ms      | 🟡 **Chỉ đạt sàn**              | 🟡 Chưa đạt mục tiêu   |
|  6  | FR-2.5: tác vụ video xuất video đã chú thích      | Đưa ra khỏi phạm vi 03/08/2026                                              | **Thu hẹp phạm vi**             | ➖ Không áp dụng       |
|  7  | Bật oneDNN để tăng tốc CPU                        | Buộc phải tắt do lỗi thư viện                                               | Bắt buộc bởi lỗi thượng nguồn   | Đã ghi nhận            |
|  8  | Khử rò rỉ bằng phash                              | Còn rò rỉ tồn dư không khử được bằng phash                                  | **Giới hạn phương pháp**        | Đã ghi nhận            |
|  9  | Bộ đo độ chính xác OCR đo hệ thống đang giao      | Bộ đo gọi thẳng recognizer + normalizer, **bỏ qua tầng điều phối**          | **Lỗi phương pháp đo**          | ✅ Đã phát hiện và sửa |
