# CHƯƠNG 4. THIẾT KẾ VÀ CÀI ĐẶT HỆ THỐNG

Trên cơ sở lý thuyết ở Chương 2 và lựa chọn công nghệ ở Chương 3, chương này trình bày thiết kế và hiện thực của hệ thống trong cùng một mạch. Nguyên tắc trình bày: mọi mô tả đều phản ánh đúng mã nguồn thực tế; các chức năng chưa hoàn thiện và các số liệu chưa được đo lường đều được ghi chú rõ ràng. Chương gồm phân tích yêu cầu (4.1), kiến trúc (4.2), môi trường phát triển (4.3), bộ dữ liệu (4.4), huấn luyện mô hình (4.5), tầng AI (4.6), máy chủ và cơ sở dữ liệu (4.7), giao diện (4.8) và Docker (4.9).

Trạng thái bản này: hệ thống chạy ALPRPipeline với mô hình chính thức models/best.pt (`/health` báo `model_loaded: true`, bộ nhận dạng `yolo:best.pt+paddleocr-PP-OCRv5-mobile`, mAP@0.5 = 0,9829); `StubPipeline` đã ra khỏi đường chạy chính. Mọi kết quả thực nghiệm trình bày ở Chương 5.

---

## 4.1. Phân tích yêu cầu

### 4.1.1. Sơ đồ use case và ba use case chính

Ba use case chính — nhận dạng từ ảnh (UC-01), từ video (UC-02) và tra cứu lịch sử (UC-05) — đều được đặc tả theo cùng một khuôn: tác nhân, tiền điều kiện, luồng chính, luồng thay thế và hậu điều kiện (Hình 4.1).

![](figures/fig-ch4-usecase.png)

**Hình 4.1.** Sơ đồ use case — hai tác nhân và bốn use case.

### 4.1.2. Yêu cầu chức năng

Hệ thống có **34 yêu cầu chức năng** chia sáu nhóm, phân mức theo MoSCoW: 22 _Must_, 5 _Should_, 3 _Could_, 4 _Won't_. Sáu yêu cầu mức _Won't_ đến từ ba đợt thu gọn phạm vi: bốn yêu cầu thuần giao diện chuyển mức ở đợt thu gọn giao diện, và hai yêu cầu của nhóm video — xuất video đã chú thích cùng huỷ tác vụ đang chạy — chuyển mức ở đợt thu gọn nhóm video. Bốn yêu cầu mức _Must_ từng chuyển sang _Won't_, nhưng **hai trong số đó đã quay lại**: FR-3.1 và FR-3.4 được cài đặt lại cùng chế độ quét trực tiếp (4.8.1). **Còn lại hai yêu cầu _Must_ nằm ngoài phạm vi: FR-4.1 và FR-2.5** — FR-4.1 chỉ mất màn hình hiển thị (thống kê vẫn phục vụ ở tầng API và vẫn có kiểm thử), riêng **FR-2.5 mất chính năng lực**. Nêu rõ ở mục 6.2. Bảng đầy đủ từng mã yêu cầu ở **Phụ lục H.2**.

### 4.1.3. Yêu cầu phi chức năng

Các chỉ tiêu phi chức năng chia bảy nhóm — độ chính xác (NFR-A), hiệu năng (NFR-P), độ tin cậy (NFR-R), khả năng chịu tải (NFR-SC), khả năng bảo trì (NFR-M), bảo mật (NFR-S) và khả dụng (NFR-U) — mỗi chỉ tiêu kèm **ngưỡng tối thiểu, mục tiêu và phương pháp đo**. Hai ràng buộc chi phối toàn bộ nhóm hiệu năng: suy luận **chỉ trên CPU** (CON-02) và ngân sách độ trễ đầu cuối. Bảng đầy đủ ở **Phụ lục H.3**; kết quả đối chiếu từng chỉ tiêu ở mục 5.7.

## 4.2. Kiến trúc hệ thống

### 4.2.1. Nguyên tắc kiến trúc

**Kiến trúc sạch và quy tắc phụ thuộc:** phụ thuộc chỉ hướng vào trong, từ chi tiết dễ thay đổi (framework web, CSDL, giao diện) về quy tắc nghiệp vụ ổn định. Ở bài toán này thứ ổn định là thuật toán nhận dạng biển số, thứ dễ đổi là FastAPI hay Flask, SQLite hay PostgreSQL — nên **đường ống AI nằm ở vòng trong cùng**, tầng web phụ thuộc nó chứ không ngược lại. Nguyên tắc **trách nhiệm đơn nhất** được vận dụng trực tiếp để đo được từng khối riêng: bộ phát hiện chỉ trả hộp bao, bộ nhận dạng chỉ trả chuỗi, bộ chuẩn hoá chỉ chuẩn hoá (Bảng 4.1).

<!-- {{T4.1a}} bon rang buoc kien truc va cach kiem chung -->

**Bảng 4.1.** Bốn ràng buộc kiến trúc và cách kiểm chứng từng ràng buộc

| # | Ràng buộc | Mã chỉ tiêu | Cách hiện thực | Kiểm chứng bằng gì |
|:--:|---|:--:|---|---|
| 1 | Không trộn mã AI với mã API | NFR-M1 | `ai/` là gói Python độc lập, không import framework web | Kiểm thử tự động quét `sys.modules` lúc chạy |
| 2 | Mọi thành phần AI thay thế được | NFR-M5 | Ba lớp trừu tượng, đường ống chỉ giữ tham chiếu tới lớp cha (Hình 4.6) | Đổi bộ nhận dạng không phải sửa nơi khác |
| 3 | Không gán cứng đường dẫn | NFR-M4 | Mọi đường dẫn qua đối tượng cấu hình đọc từ biến môi trường | Đổi `ALPR_MODEL_PATH` là đổi được mô hình |
| 4 | Chạy được không cần GPU | CON-02 · NFR-C2 | Thiết bị suy luận là tham số, **mặc định `cpu`** | Toàn bộ số liệu Chương 5 đo trên CPU |

Ràng buộc thứ tư phát biểu là **cấu hình mặc định**, không phải "chế độ dự
phòng" — nên đường chạy CPU là đường được kiểm thử thường xuyên nhất, chứ không
phải nhánh ít ai đụng tới.

### 4.2.2. Kiến trúc phân tầng

![](figures/fig-ch4-02.png)

**Hình 4.2.** Kiến trúc phân tầng năm tầng và chiều phụ thuộc

Năm tầng: **1 — Trình bày** (giao diện, chỉ biết hợp đồng HTTP của tầng 2); **2 — API** (định tuyến, kiểm tra hợp lệ, ánh xạ ngoại lệ thành mã HTTP, sinh OpenAPI); **3 — Nghiệp vụ** (điều phối: tạo tác vụ, gọi đường ống, lưu tệp, ghi CSDL, gộp trùng, thống kê); **4 — AI** (phát hiện, nhận dạng, chuẩn hoá — **chỉ biết NumPy, OpenCV và thư viện học sâu**); **5 — Dữ liệu** (CSDL, kho tệp). **Điều quan trọng:** khối tầng AI **không có mũi tên nào đi lên**. Sau hai đợt thu gọn, tầng trình bày còn **ba trang** nhưng **tầng 2–5 không đổi một dòng**: `POST /detect/frame`, `GET /statistics`, `GET /health` vẫn phục vụ và vẫn có kiểm thử tích hợp — phép thử ngoài dự kiến cho nguyên tắc phụ thuộc một chiều.

### 4.2.3. Tách tầng AI khỏi tầng API và cách kiểm chứng ràng buộc

Tầng AI là một gói Python độc lập, giao tiếp với tầng API **chỉ qua giao diện trừu tượng**; ràng buộc *mã đường ống AI không import FastAPI* (NFR-M1) được kiểm chứng tự động trong bộ kiểm thử. Tách như vậy cho ba lợi ích: kiểm thử tầng AI chỉ cần nạp mảng ảnh chứ không phải dựng ứng dụng web; kịch bản huấn luyện và đo đạc **dùng lại đúng mã của bản giao hàng** thay vì sao chép — bản sao lệch nhau chính là nguyên nhân của loại sự cố nghiêm trọng nhất, **con số công bố không mô tả hệ thống được bàn giao** (5.5.6); và thay bộ nhận dạng chỉ là đổi thành phần được tiêm vào, không sửa router hay lược đồ (NFR-M5) (Hình 4.3).

### 4.2.4. Luồng xử lý của đường ống AI và nhánh biển hai dòng

![](figures/fig-ch4-03.png)

**Hình 4.3.** Luồng xử lý của đường ống AI, các khối tô đỏ là nhánh biển hai dòng

**Nhánh biển hai dòng** là phần khó nhất của đồ án và là rủi ro đã xác định từ khâu lập kế hoạch (R-04). Bộ OCR dựng sẵn giả định văn bản một dòng ngang, nên với biển hai dòng chúng đọc theo thứ tự không xác định, ghép lẫn hoặc bỏ sót một dòng — cơ chế đứng sau chênh lệch 48,6 điểm phần trăm **đo trên bộ RodoSol-ALPR của Brazil** đã dẫn ở 4.1.1 [2]<!-- laroca_2022_crossdataset -->. Giải pháp: **tách vùng biển thành hai nửa, nhận dạng từng nửa, ghép theo thứ tự trên trước dưới sau** — mỗi nửa lúc này là một dòng ngang đúng giả định của bộ OCR (cài đặt ở 4.6.4).

### 4.2.5. Bảng tổng hợp các quyết định kiến trúc

Mỗi quyết định ghi kèm lý do và **đánh đổi phải chấp nhận** — một quyết định trình bày như không có nhược điểm là quyết định chưa cân nhắc đủ (Bảng 4.2).

<!-- {{T4.2}} cac quyet dinh kien truc AD-01 den AD-08 -->

**Bảng 4.2.** Tám quyết định kiến trúc — mỗi dòng kèm đánh đổi phải chấp nhận

| Mã | Quyết định | Lựa chọn | Đánh đổi phải chấp nhận |
|:--:|---|---|---|
| AD-01 | Tách tầng AI khỏi tầng API | Gói Python độc lập | Thêm một lớp gián tiếp |
| AD-02 | Xử lý video | Bất đồng bộ, trả `job_id` ngay | Giao diện phải hỏi tiến độ định kỳ |
| AD-03 | Nhận dạng thời gian thực | Client gửi từng khung qua HTTP | Muốn FPS cao hơn phải chuyển WebSocket |
| AD-04 | Gộp trùng biển số | Theo chuỗi ký tự + cửa sổ thời gian | Kém chính xác khi hai xe cùng biển đi gần nhau |
| AD-05 | Nền tảng suy luận | PyTorch trước, ONNX/OpenVINO nếu cần | Có thể phải làm lại bước xuất mô hình |
| AD-06 | Thiết bị | Cấu hình được, mặc định `cpu` | — |
| AD-07 | Lưu trữ ảnh | Tệp trên đĩa, chỉ lưu đường dẫn trong CSDL | Phải giữ đồng bộ giữa tệp và bản ghi |
| AD-08 | Đặt tên tệp | UUID, không dùng tên gốc | Cần lưu tên gốc riêng nếu muốn hiển thị |

Tám quyết định kiến trúc được ghi thành hồ sơ AD-01 … AD-08, mỗi hồ sơ nêu **bối cảnh, phương án đã cân nhắc, quyết định và hệ quả phải chấp nhận** — dạng ghi chép này khiến một quyết định về sau có thể bị lật lại mà người lật hiểu được vì sao nó từng đúng. Các mục 4.2.1 – 4.2.4 trình bày bốn quyết định có ảnh hưởng rộng nhất.

Ghi chú: AD-03 không đổi sau khi gỡ trang Webcam vì ở ~5 FPS trên CPU, điểm nghẽn là suy luận chứ không phải giao thức. AD-04 cố ý **không** chọn tracking vì phức tạp hơn đáng kể và thêm một họ siêu tham số. AD-05 là quyết định duy nhất **đã thay đổi** so với phác thảo (_"PyTorch trước, ONNX nếu cần"_) — ghi nhận tường minh thay vì lặng lẽ sửa bảng. AD-06 kéo theo hai quyết định phái sinh đã cài đặt: `yolo11n` và **PP-OCRv5 mobile** — ràng buộc CPU thay đổi _lựa chọn mô hình_, không chỉ tốc độ.

---

## 4.3. Môi trường và công cụ phát triển

### 4.3.1. Cấu hình máy thực hiện và hệ quả của ràng buộc CPU

Toàn bộ cài đặt, kiểm thử và đo đạc chạy trên một máy trạm duy nhất: Windows 11 Pro; Intel Core i5-14600K, 14 nhân / 20 luồng; RAM 31,77 GiB; Intel UHD 770 — **không có GPU CUDA**; Python 3.13.12; Node.js 18.20.8; Docker 29.4.3. Cấu hình này **mâu thuẫn với mô tả môi trường ban đầu** (macOS Apple Silicon, Python 3.12), và ghi nhận sai lệch thành văn bản là bước đầu của giai đoạn phân tích yêu cầu.

Ràng buộc CPU để lại dấu vết cụ thể: NFR-P1 phát biểu thẳng cho CPU; AD-06 kéo theo `yolo11n` và PP-OCRv5 mobile; và vì huấn luyện trên CPU mất 1–3 ngày mỗi lượt, quy trình huấn luyện chạy được cả trên máy cá nhân lẫn nền tảng đám mây với toàn bộ siêu tham số trong một tệp cấu hình duy nhất. Ở cấu hình giao hàng, p95 đầu cuối là **509,76 ms**, đạt cả ngưỡng tối thiểu 1.500 ms lẫn mục tiêu 800 ms; phân rã suy luận thuần cho thấy OCR chiếm **60,8%**, phát hiện **38,0%** (đối chiếu NFR-P1 ở 5.6.1) (Hình 4.4).

## 4.4. Xây dựng bộ dữ liệu

### 4.4.1. Đường ống sáu bước và thành phần bộ dữ liệu

![](figures/fig-ch5-01.png)

**Hình 4.4.** Đường ống sáu bước xây dựng bộ dữ liệu

Mỗi bước là một kịch bản độc lập có giao diện dòng lệnh riêng và sinh báo cáo dạng dữ liệu có cấu trúc; một kịch bản điều phối chạy toàn chuỗi bằng một lệnh. **Kết quả:** **15.133 ảnh** hợp nhất từ **7 bộ công khai** (Roboflow, HuggingFace, Kaggle), còn **6 nguồn nguyên tố** sau khi loại **11.978 ảnh (44,2%)** bản sao từ **27.111 ảnh**; tổng 9 bộ tải về, 2 bộ nhãn mức ký tự tách riêng cho đánh giá OCR. Chia 70/20/10 thành **10.592 / 3.027 / 1.514 ảnh**. Bảng dưới **phải trích khi nói về dữ liệu của đồ án**; nguồn và giấy phép từng bộ ở **Phụ lục C.1** (Bảng 4.3).

<!-- {{T4.4}} dong gop cua tung bo du lieu truoc va sau khu trung lap -->

**Bảng 4.3.** Đóng góp của từng bộ dữ liệu trước và sau khử trùng lặp

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

> **Ghi chú về phạm vi của mọi số liệu OCR.** Phân loại màu nền trên 2.801 ảnh cho: **2.736 biển trắng (97,68%)**, 20 vàng, 4 xanh, **0 đỏ, 0 ngoại giao**. Phát biểu đúng là _"1 − CER = 0,9483 trên một tập gồm 97,7% biển trắng"_, **không phải** _"trên biển số Việt Nam"_.

> **Giới hạn của phép khử trùng lặp.** Băm tri giác rút ảnh thành 64 bit mô tả cấu trúc tần số thấp của *toàn khung*, nên hai xe khác nhau qua cùng một camera vẫn cho khoảng cách rất nhỏ: ngưỡng thấp bỏ sót cặp cùng xe khác ngày, ngưỡng cao gộp nhầm hàng nghìn ảnh khác xe. Vì vậy **vẫn còn rò rỉ tồn dư**, ghi thành hạn chế số 3 ở mục 6.2 và đo lại ở 5.3.1.

## 4.5. Huấn luyện mô hình

### 4.5.1. Siêu tham số và chi phí huấn luyện bộ phát hiện

Cấu hình lượt huấn luyện chính thức trích từ tệp tham số do thư viện tự sinh — bản ghi *đã thực thi* chứ không phải *dự định*. Các giá trị chịu lực: YOLO11n tiền huấn luyện COCO (**2.590.035** tham số, biến thể nhỏ nhất do ràng buộc CPU), độ phân giải **640** theo NFR-A1/A2, **20 epoch** lô 8, AdamW với tốc độ học 0,001 theo lịch cosine, thiết bị CPU, hạt giống cố định 42 kèm chế độ tất định. Phép lật ngang **tắt hoàn toàn** — lệch có chủ ý so với mặc định, vì nó sinh ký tự đối xứng gương, một phân bố không bao giờ xuất hiện thật.

Giới hạn thời gian CPU chỉ cho phép **một lượt huấn luyện duy nhất**, nên không có nhiều hạt giống để ước lượng phương sai; cố định hạt giống ít nhất bảo đảm lượt này tái lập được, và mọi chỉ số phải đọc là **kết quả một lần chạy, không có khoảng tin cậy** (5.9.1). **Chi phí:** mô hình đối chứng 40 epoch @416 trên bộ v1 mất **156 phút**; mô hình chính thức 20 epoch @640 trên bộ v3 mất **30,2 phút mỗi epoch, tổng 10,05 giờ** trên CPU. Ba yếu tố cùng đổi (số ảnh ×3,3, diện tích ×2,37, epoch giảm nửa) nên so sánh ở mục 3.6 **không quy kết được nguyên nhân cho từng biến** (Hình 4.5).

### 4.5.2. Tiến triển của quá trình huấn luyện

![](figures/fig-train-curves.png)

**Hình 4.5.** Đường cong huấn luyện theo epoch — ba hàm mất mát và bốn chỉ số trên tập kiểm định

Ba hàm mất mát giảm đơn điệu và **không có dấu hiệu quá khớp**: mất mát hộp bao 1,252 → 0,809, mất mát phân lớp 0,833 → 0,313, mất mát phân phối 1,154 → 0,987; đường validation bám sát đường train suốt 20 epoch. Chỉ số trên tập validation đi lên rồi bão hoà sớm: mAP@0.5 đạt **0,9684 ngay ở epoch 1** và chỉ nhích lên **0,9830** ở epoch 20, trong khi mAP@0.5:0.95 — chỉ số nhạy với độ khít của hộp — tăng đáng kể hơn, **0,6526 → 0,7688** (Bảng 4.4).

<!-- {{T4.5a}} tien trien chi so tren tap validation theo epoch -->

**Bảng 4.4.** Tiến triển chỉ số trên tập validation theo mốc epoch

| Epoch | Mất mát hộp bao | Mất mát phân lớp | mAP@0.5 | mAP@0.5:0.95 | Precision | Recall |
| :---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 1,1705 | 0,6858 | **0,9684** | **0,6526** | 0,9552 | 0,9410 |
| 5 | 1,1074 | 0,4977 | **0,9754** | **0,6950** | 0,9765 | 0,9525 |
| 10 | 1,0548 | 0,4168 | **0,9808** | **0,7248** | 0,9850 | 0,9584 |
| **20** _(tốt nhất)_ | **0,9204** | **0,3331** | **0,9830** | **0,7688** | **0,9846** | **0,9697** |

## 4.6. Tầng AI — thiết kế và cài đặt

### 4.6.1. Tổ chức gói suy luận và ba lớp trừu tượng

Kiến trúc tầng AI dựa trên **ba lớp trừu tượng** có hợp đồng thống nhất. Lớp **phát hiện** trả danh sách vùng biển đã lọc ngưỡng và khử chồng lấn — danh sách rỗng là kết quả hợp lệ, không phải lỗi. Lớp **nhận dạng** trả chuỗi thô kèm độ tin cậy; sửa lỗi ký tự không thuộc trách nhiệm của nó, và chính sự tách biệt đó cho phép định lượng đóng góp của khối hậu xử lý (5.5.2). Lớp **chuẩn hoá** trả về cả chuỗi không hợp lệ, vì loại bỏ chúng sẽ làm mất đúng những trường hợp chương đánh giá cần thống kê. Hợp đồng chung: **trả kết quả rỗng thay vì ném ngoại lệ** — không tìm thấy đối tượng và lỗi hệ thống là hai trạng thái khác nhau (NFR-R2).

![](figures/fig-ch4-interfaces.png)

**Hình 4.6.** Ba lớp trừu tượng và cài đặt tương ứng — bằng chứng cài đặt cho NFR-M5.

### 4.6.2. Bộ phát hiện

Bộ phát hiện là **lớp thích ứng mỏng** bao quanh thư viện Ultralytics: không thành phần nào ngoài lớp này tiếp xúc với cấu trúc dữ liệu nội bộ của thư viện. Phiên bản mô hình được **ghim tường minh** để mọi kết quả đo truy được về đúng bộ trọng số, và nâng cấp thư viện không đổi ngầm mô hình đứng sau một số liệu đã công bố. Trọng số nạp ngay khi khởi tạo nên lỗi thiếu tệp bộc lộ lúc khởi động; mọi hộp bao được kẹp về biên ảnh và hộp suy biến bị loại.

### 4.6.3. Bộ nhận dạng ký tự

Bộ nhận dạng tuân theo cùng mô hình lớp thích ứng và cũng ghim phiên bản mô hình tường minh. Các mảnh văn bản được lọc theo tiêu chí hình học thay vì ngưỡng tin cậy, do bước nâng tương phản có thể sinh mảnh nhiễu được đọc thành chuỗi vô nghĩa ở độ tin cậy cao; độ tin cậy của cả chuỗi tổng hợp bằng trung bình có trọng số theo độ dài mảnh, vì trung bình cộng cho phép một mảnh một ký tự che lấp mảnh dài mang danh tính thực của biển số.

Một giới hạn kỹ thuật ngoài tầm kiểm soát của đồ án: trên nền tảng mục tiêu, thư viện nhận dạng không kích hoạt được thư viện tăng tốc oneDNN do khiếm khuyết phía thư viện, nên nó bị vô hiệu hoá bằng cấu hình. Đây là tham số **hiệu năng**, không phải độ chính xác, và giải thích một phần kết quả NFR-P1 ở mục 5.6.

### 4.6.4. Mô-đun xử lý biển hai dòng

**a) Cơ sở của bài toán.** Bộ nhận dạng dựa trên kiến trúc CRNN kết hợp hàm mất mát CTC, vốn giả định đầu vào là **một chuỗi ký tự theo chiều ngang** (2.4.2). Ảnh biển hai dòng vi phạm giả định đó, và mức suy giảm đã được đo trong tài liệu (1.1.3) — đây là rủi ro R-04, mức Cao/Cao, vì ở Việt Nam biển hai dòng là dạng phổ biến chứ không phải ngoại lệ.

**b) Ước lượng số dòng.** Số dòng suy từ tỉ lệ chiều rộng trên chiều cao của vùng biển, ngưỡng phân loại 2,5: tỉ lệ nhỏ hơn ngưỡng được xếp vào nhóm hai dòng. Đây là đề xuất của đồ án, không phải quy định pháp lý — quy chuẩn chỉ cung cấp ba tỉ lệ vật lý 4,727, 2,000 và 1,357. Ngưỡng được chọn lệch về phía hai dòng vì đường xử lý hai dòng suy giảm êm khi gặp đầu vào một dòng, chiều ngược lại thì không. Dải 2,5–3,0 vẫn là vùng bất định do biển một dòng chụp nghiêng lớn có thể cho tỉ lệ rơi vào khoảng này; định lượng tần suất thuộc Chương 5.

**c) Phân tách hai nửa có chồng lấn.** Vùng biển được cắt thành hai nửa theo chiều dọc, nửa trên kết thúc tại 5/12 chiều cao và nửa dưới bắt đầu tại 1/3, tạo vùng chồng lấn bằng 1/12 chiều cao biển. Thiết kế xuất phát từ tính bất đối xứng của chi phí sai sót: cắt cụt chân hoặc đỉnh ký tự phá huỷ thông tin không phục hồi được, trong khi lọt vài hàng điểm ảnh của nửa còn lại chỉ được xử lý như nền.

**d) Ghép ngang.** Hai nửa được ghép theo chiều ngang bằng phép `hstack`, chiều cao chung lấy bằng giá trị lớn nhất trong ba đại lượng: chiều cao nửa trên, chiều cao nửa dưới và 48 điểm ảnh — đúng bằng chiều cao đầu vào cố định của mô-đun nhận dạng. Nửa trên đặt bên trái để bảo toàn thứ tự đọc. Sau khi ghép, một hàng ký tự duy nhất nhận trọn ngân sách 48 điểm ảnh thay vì hai hàng chia nhau, vô hiệu hoá đúng nguyên nhân đã phân tích ở mục a.

**e) Tiền xử lý ảnh biển.** Ba bước độc lập, mỗi bước bật tắt riêng để phục vụ thí nghiệm bóc tách đóng góp. **Chuyển thang xám** vì ký tự không mang thông tin phân biệt trong kênh màu. **CLAHE** hệ số 2,0 trên ô 8 × 8, vì bề mặt phản quang tạo mảng chói cục bộ mà cân bằng toàn cục không xử lý được [22]<!-- sutikno_2025_clahe -->. **Lọc song phương** thay cho làm mờ Gauss, vì nó bảo toàn biên — yếu tố quyết định để phân biệt các cặp đồng hình như `8` và `B`. Ảnh biển do bộ phát hiện sinh ra thường chỉ cao 20–40 điểm ảnh nên được phóng về 64 trước khi đọc.

**f) Bước phục hồi dòng trên.** Chế độ hỏng quan sát được: `29E-015.66` chỉ đọc ra `015.66` — sau khi ghép, bộ phát hiện văn bản bỏ qua cụm mã tỉnh và ký tự sê-ri. Giả thuyết thay thế *(bỏ phép ghép, đọc riêng từng nửa rồi nối chuỗi)* đã kiểm chứng trên 200 biển hai dòng có nhãn và **bị bác bỏ: 64,5% xuống 3,5%** (5.5.6); nguyên nhân là dải chồng lấn ở mục c bị nhận dạng hai lần khi đọc riêng.

Thiết kế cuối cùng vì vậy giữ nguyên chiến lược ghép và chỉ thêm một bước phục hồi có cổng chặt: **chỉ kích hoạt khi đồng thời** vùng biển được phân loại hai dòng, chuỗi sau chuẩn hoá không hợp lệ, và chuỗi thô khác rỗng. Khi đó hệ thống đọc thêm một lượt trên riêng nửa trên, ghép với chuỗi thô rồi chuẩn hoá lại; kết quả mới chỉ được nhận nếu vượt kiểm tra định dạng. **Tính không làm hỏng mang bản chất cấu trúc** — cổng chỉ mở khi kết quả đã không hợp lệ, nên tập bị can thiệp và tập đang đúng là hai tập rời nhau. Đo được **+1,86 và +0,50 điểm** trên hai mẫu độc lập, **0 trường hợp bị làm hỏng**, chi phí 15–21 ms mỗi biển hai dòng.

**g) Một giới hạn về phương pháp đo.** Kịch bản sinh NFR-A4…A7 ban đầu gọi thẳng bộ nhận dạng thay vì đi qua tầng điều phối, nên logic đặt tại tầng ấy không được phản ánh trong số công bố. Khắc phục bằng cách tách bước phục hồi thành hàm cấp mô-đun để cả đường chạy sản phẩm lẫn công cụ đo cùng gọi một cài đặt. Bài học vượt ra ngoài phạm vi biển hai dòng: **một công cụ đo đi tắt qua tầng điều phối sẽ đo một hệ thống khác với hệ thống được bàn giao** (5.5.6).

### 4.6.5. Bộ luật hậu xử lý theo vị trí

Bộ phát hiện dùng kiến trúc có sẵn nhưng **trọng số do nhóm tự huấn luyện trên dữ liệu Việt Nam** (4.5); bộ nhận dạng dùng mô hình tiền huấn luyện nguyên bản. Khối hậu xử lý là thành phần nhóm tự thiết kế toàn bộ. Khối tuân ba nguyên tắc: thuần khiết về mặt hàm số, không vào/ra và không giữ trạng thái toàn cục khả biến; biểu thức chính quy sinh tự động từ các tập ký tự thay vì viết tay, loại trừ khả năng mẫu lệch khỏi bảng dữ liệu mà nó mã hoá; mọi lớp ký tự là hằng số có tên.

**a) Tập mã tỉnh.** Khối lưu 81 mã tỉnh đang sử dụng theo phụ lục Thông tư 51/2025/TT-BCA [5]<!-- bocongan_2025_tt51 -->, đối chiếu với bảng ký hiệu do Cổng Thông tin điện tử Chính phủ công bố [11]<!-- chinhphu_2025_kyhieu -->, song song tập 8 mã không bao giờ được cấp: 13, 42, 44, 45, 46, 87, 91 và 96. So với biểu thức tổng quát chấp nhận mọi cặp chữ số, ràng buộc này bác bỏ được các chuỗi không tồn tại trên thực tế; lưu tường minh cả tập không sử dụng cho phép kiểm thử khẳng định hai tập phủ đúng dải 11–99.

**b) Các lớp ký tự sê-ri.** Bốn lớp được định nghĩa: tập 20 chữ cái cho sê-ri ô tô và ký tự thứ nhất của sê-ri xe máy; tập 20 chữ cái cho ký tự thứ hai của sê-ri xe máy; tập 11 chữ cái cho biển nền xanh; và tập mở rộng 21 chữ cái. Hai tập đầu là ảnh gương của nhau tại đúng hai ký tự — tập thứ nhất chứa `G` không chứa `R`, tập thứ hai ngược lại — nên `29-AR 123.45` hợp lệ còn `29-AG 123.45` thì không.

Tập mở rộng tồn tại vì một bộ nhận dạng chỉ biết 20 chữ cái **sẽ không bao giờ dự đoán được `R`**, gây sai sót có hệ thống trên mọi biển xe máy mang ký tự này ở vị trí sê-ri thứ hai — loại sai sót hậu xử lý không cứu được vì thông tin đã mất ở tầng mô hình. Nguyên tắc rút ra: **một mô hình được phép dự đoán ký tự bất hợp lệ tạo sai lầm quan sát được và sửa được, còn một mô hình không thể dự đoán ký tự đó về mặt kiến trúc tạo sai lầm không quan sát được.**

> **Nguyên tắc này áp vào đâu, nói cho chính xác.** Nó là quyết định thiết kế cho **lượt tinh chỉnh bộ nhận dạng**, hiện thực hoá bằng tệp `dict36.txt` gồm đủ `0–9` và `A–Z`. Lượt tinh chỉnh ấy **đã chạy và đã đo bốn cấu hình, nhưng không được đưa vào bản giao hàng** vì ở đúng chế độ production nó thua 7,50 điểm (5.5). **Bản giao hàng chạy model gốc PP-OCRv5** — `ocr_rec_model_dir` để trống — và charset của model gốc còn rộng hơn 36 ký tự nhiều. Nguyên tắc vì vậy vẫn đúng, thậm chí đúng hơn: khả năng model đọc ra ký tự ngoài tập hợp lệ càng lớn, nên **ràng buộc về 31 ký tự hợp lệ ở tầng hậu xử lý chính là chỗ bắt chúng**. Hằng số `OCR_TRAINING_CHARSET` giữ trong mã nguồn cùng kiểm thử canh giữ, để lượt tinh chỉnh sau không vô tình thu hẹp lại còn 20 chữ.

Tập bị loại trừ toàn hệ thống gồm năm chữ `I`, `J`, `O`, `Q`, `W`; chính việc loại `I`, `O`, `Q` làm việc sửa lỗi nhận dạng trở nên khả thi.

**c) Mặt nạ vị trí và ký tự đại diện.** Ba mặt nạ tương ứng ba độ dài chuỗi hợp lệ, trong đó `D` bắt buộc chữ số, `L` bắt buộc chữ cái, `?` là ký tự đại diện không áp đặt kiểu:

- chuỗi 8 ký tự (ô tô, sê-ri 5 chữ số): `DDLDDDDD`
- chuỗi 7 ký tự (ô tô, sê-ri 4 chữ số kiểu cũ): `DDLDDDD`
- chuỗi 9 ký tự (xe máy): `DDL?DDDDD`

Ký tự đại diện tại chỉ số 3 của chuỗi 9 ký tự quyết định tính đúng đắn của mặt nạ. Hai kiểu biển xe máy cùng 9 ký tự nhưng khác nhau đúng tại vị trí này: kiểu mới dùng sê-ri hai chữ cái, kiểu cũ dùng một chữ cái kết hợp một chữ số và vẫn lưu hành hợp pháp. Nếu tách thành hai mặt nạ riêng thì việc áp kiểu tại chỉ số 3 trở thành bắt buộc, và kiểm chứng bằng chạy thật cho thấy một trong hai kiểu sẽ bị phá huỷ. Chỉ số 3 của chuỗi 9 ký tự là vị trí duy nhất trong toàn hệ thống biển số Việt Nam mà cả chữ cái lẫn chữ số đều hợp lệ.

**d) Bảng ánh xạ nhầm lẫn và tính không đối xứng.** Hai bảng riêng biệt áp tại vị trí bắt buộc chữ số và vị trí bắt buộc chữ cái, và **phát hiện trung tâm là chúng không đối xứng**: `O → 0` tại vị trí chữ số là hợp lý, nhưng `0 → O` thì không bao giờ, vì `O` không thuộc tập sê-ri hợp lệ. Do cả `O` và `Q` đều bị loại, ứng viên đồng hình duy nhất còn lại ở vị trí chữ cái là `D`, nên chiều đúng là `0 → D`. Ký tự `R` không được ánh xạ trong mọi trường hợp vì nó hợp lệ ở vị trí sê-ri thứ hai của biển xe máy (2.2.1). Nguyên tắc an toàn: ký tự không có mục trong bảng thì giữ nguyên. Hai bảng này **suy từ hình dạng ký tự chứ không từ đo đạc** — thay chúng bằng bảng trích từ ma trận nhầm lẫn đo được thuộc Chương 5.

**e) Thuật toán chuẩn hoá.**

![](figures/fig-ch5-03.png)

Trình tự các bước của thuật toán trình bày ở Hình 4.7.

**Hình 4.7.** Thuật toán chuẩn hoá chuỗi biển số theo bộ luật ràng buộc vị trí

Thuật toán tuân ba nguyên tắc. Biểu thức chính quy được thử trước khi thực hiện bất kỳ chỉnh sửa nào, bởi với chuỗi vốn đã hợp lệ thì mọi can thiệp chỉ có thể làm sai đi. Không chuỗi nào bị loại bỏ: chuỗi không sửa được vẫn trả về kèm cờ không hợp lệ và vẫn được lưu. Chuỗi thô được giữ song song với chuỗi đã sửa. Kết quả là một cấu trúc bất biến chứa chuỗi thô, chuỗi cuối, cờ hợp lệ, kết quả phân loại họ biển và danh sách vị trí ký tự đã chỉnh sửa — dấu vết kiểm toán mà chương đánh giá dựa vào để định lượng đóng góp của khối.

**f) Xử lý nhập nhằng bằng số dòng.** Số dòng bằng một chứng minh chuỗi thuộc biển ô tô, do biển xe máy luôn hai dòng; ngược lại, số dòng bằng hai không chứng minh gì vì biển ô tô loại ngắn cũng hai dòng. Trong trường hợp thứ hai, hệ thống giữ cờ nhập nhằng và trả về tập ứng viên thay vì suy đoán kết luận mà dữ liệu đầu vào không chứa. Thứ tự kiểm tra các mẫu sắp xếp theo mức đặc trưng giảm dần, trong đó biển quân đội đặt cuối vì đây là trường hợp nhận dạng nhằm loại trừ: chuỗi khớp mẫu biển quân đội không bao giờ được báo cáo là biển dân sự hợp lệ.

### 4.6.6. Tổ hợp đường ống bằng tiêm phụ thuộc

Đường ống suy luận là đối tượng tổ hợp: nó không sở hữu mô hình mà chỉ điều phối thứ tự giai đoạn, cắt vùng ảnh, đo thời gian từng giai đoạn và cô lập lỗi ở mức từng biển số; do không chứa logic học sâu, đường ống kiểm thử được đầy đủ bằng thành phần giả lập. Thời gian của cả năm giai đoạn luôn được ghi nhận, giai đoạn không thực thi báo giá trị 0 thay vì vắng mặt — cơ sở cho phép phân rã ngân sách độ trễ ở mục 5.6.2, theo đó khối nhận dạng chiếm 64,3% và khối phát hiện 34,0% tổng thời gian suy luận thuần.

Chính sách xử lý lỗi phân tầng theo mức ảnh hưởng: ảnh không chứa biển số trả kết quả rỗng; lỗi nhận dạng trên một biển chỉ vô hiệu hoá biển đó, các biển còn lại vẫn được xử lý; lỗi ở bộ phát hiện làm dừng toàn bộ yêu cầu; lỗi chuẩn hoá giữ nguyên kết quả thô. Thao tác cắt ảnh kẹp toạ độ **thêm một lần nữa** dù lớp phát hiện đã bảo đảm, vì cắt ảnh là nơi duy nhất mà sai lệch một đơn vị tạo mảng rỗng không kèm cảnh báo; ảnh cắt được tạo dưới dạng bản sao thay vì khung nhìn, tránh giữ toàn bộ khung hình gốc trong bộ nhớ khi xử lý video.

### 4.6.7. Nhận dạng họ biển và màu nền

**a) Vì sao cần bằng chứng ngoài chuỗi ký tự.** Hai nguồn bằng chứng bù trừ cho nhau. Theo TT 79/2024, biển **vàng** của xe kinh doanh vận tải mang **đúng cùng cấu trúc ký tự** với biển trắng cá nhân nên không biểu thức chính quy nào phân biệt được; ngược lại biển **ngoại giao** có nền trắng giống biển cá nhân nên riêng màu nền cũng không đủ. Chỉ **cặp** chuỗi ký tự và màu nền mới định danh được loại phương tiện.

**c) Thiết kế bộ phân loại màu.** Bộ phân loại chuyển ảnh sang HSV, thống kê tỉ lệ điểm ảnh theo từng dải màu rồi chọn dải chiếm ưu thế, với ba quyết định đáng nêu. **Chỉ lấy mẫu vùng trung tâm**, biên thu vào 18% mỗi phía, vì khung phát hiện hiếm khi ôm sát mép biển và màu thân xe phía sau có thể lấn át. **Không loại điểm ảnh thuộc ký tự**: ký tự chiếm thiểu số diện tích, và thêm một bước phân đoạn ký tự là đưa vào khâu kém ổn định hơn chính khâu nó bảo vệ. **Trả *không xác định* khi dải ưu thế dưới 30%** — kết luận sai về màu tương đương khẳng định một loại phương tiện không chứng minh được, còn thừa nhận không xác định chỉ là ghi nhận một giới hạn.

**d) Hợp nhất chuỗi ký tự và màu nền.** Với chuỗi như `80A12345`, bốn họ biển đều hợp lệ và bộ chuẩn hoá mặc định chọn họ phổ biến nhất — đúng với đa số nhưng sai ngầm với xe cơ quan nhà nước mang biển nền xanh. Cơ chế hợp nhất cho phép màu nền **nâng cấp một ứng viên mà bộ luật ký tự đã coi là hợp lý**, và ràng buộc an toàn quan trọng hơn chính tác dụng ấy: nếu phán quyết ban đầu không nằm trong tập ứng viên thì giữ nguyên, nên màu nền **không thể tạo ra họ biển mà bộ luật ký tự đã bác bỏ**. Khi họ biển ưu tiên có cả biến thể ô tô và xe máy thì phân định theo số dòng; mâu thuẫn cả hai thì giữ phán quyết ban đầu — đại lượng đo từ hình học ưu tiên hơn đại lượng suy từ thống kê điểm ảnh. Chỉ màu xanh nằm trong bảng ưu tiên vì đó là màu duy nhất chuỗi ký tự hoàn toàn không phân biệt được; màu vàng không đổi họ biển mà chỉ đổi mục đích sử dụng nên lưu thành trường độc lập.

**d) Độ chính xác đo được.** Trên bộ ảnh biển cắt sẵn có nhãn màu do người gán và **chưa từng dùng để hiệu chỉnh**, bộ phân loại đạt **97,89%** trên 1.565 ảnh (vàng 98,56% · trắng 97,40% · xanh 96,83%). Ba giới hạn phải nêu kèm: mẫu **không có biển đỏ và biển ngoại giao** nên hai nhánh đó chưa có số liệu; nhãn gán trên **vùng biển đã cắt sẵn** chứ không phải qua bộ phát hiện thật; và ba lớp **rất lệch nhau về cỡ mẫu**, nên con số tổng nghiêng theo hai lớp lớn.

### 4.6.8. Tối ưu tầng chạy cho suy luận trên CPU

Ba can thiệp dưới đây **không đổi trọng số, không đổi phép tính**, chỉ đổi cách phép tính được lập lịch trên CPU. Vì vậy chúng cải thiện độ trễ mà **không đụng tới bất kỳ chỉ số độ chính xác nào** — điều này đã được kiểm chứng bằng số ở mục 5.6.1.

**Một — tắt ghi sổ đồ thị đạo hàm.** Lệnh dự đoán của bộ phát hiện được bọc trong `torch.inference_mode()`. Ở chế độ mặc định, PyTorch vẫn dựng cấu trúc dữ liệu phục vụ lan truyền ngược cho mọi phép toán, kể cả khi không ai gọi `backward()`. Với suy luận thuần đó là chi phí trả không công. Lệnh gọi được bọc trong `try/except` và lùi về ngữ cảnh rỗng nếu không nhập được `torch`, để tầng AI vẫn chạy khi thiếu thư viện.

**Hai — ghim số luồng thay vì để thư viện tự đoán.** Torch và OpenCV mặc định lấy toàn bộ số nhân sẵn có; tài liệu ONNX Runtime nêu đúng hiện tượng này là nguồn suy giảm hiệu năng phổ biến trên CPU nhiều nhân [24]<!-- onnxruntime_threads -->. Trên máy 14 nhân / 20 luồng, hai thư viện cùng làm vậy trong một tiến trình sẽ **tranh khoá lẫn nhau**, và tổng thời gian tăng chứ không giảm. Số luồng nay được ghim ở `min(8, số_nhân)` cho phép toán trong một toán tử, và `min(4, số_nhân)` cho phép toán giữa các toán tử.

**Ba — truyền số luồng xuống bộ nhận dạng.** PaddleOCR nhận `cpu_threads` từ biến môi trường `OMP_NUM_THREADS`. Trước đó tham số này không được truyền, và trong một số cấu hình OpenBLAS điều đó gây lỗi nghiêm trọng làm sập tiến trình chứ không chỉ chậm.

Kết quả đo ở 5.6.1: p95 giảm từ 1.143,10 xuống **509,76 ms**, trung vị từ 405,77 xuống **150,07 ms**, và phần OCR trong ngân sách độ trễ giảm từ 108,28 xuống **89,16 ms** mỗi biển.

## 4.7. Máy chủ và cơ sở dữ liệu

### 4.7.1. Kiến trúc phân tầng và tầng nghiệp vụ

Máy chủ tổ chức thành **năm tầng với luồng phụ thuộc một chiều nghiêm ngặt** (Hình 4.2). Ba quy tắc giữ cho tầng nghiệp vụ tách biệt khỏi hai tầng kề nó: tầng định tuyến **không chứa truy vấn** (mọi truy cập dữ liệu đi qua tầng kho, nên một thay đổi lược đồ có bán kính ảnh hưởng gói trong một mô-đun); tầng kho **không tự xác nhận giao dịch** (lưu một lượt nhận dạng cùng toàn bộ biển số thuộc lượt đó là **một thao tác logic duy nhất**); và mỗi ngoại lệ mang **hai mô tả** — thông điệp tiếng Việt kèm hành động khắc phục đi vào phản hồi HTTP, mô tả kỹ thuật chỉ đi vào nhật ký, nên vết ngăn xếp không lộ ra người dùng (NFR-S4). Bảng đầy đủ ở **Phụ lục VII**.

Phần lớn sự cố gặp khi cài đặt nằm ở **ranh giới giữa mã nguồn và môi trường thực thi** — nguồn cấu hình, tầng lưu trữ, bảng mã đầu ra — và đều vượt qua được kiểm thử đơn vị; đó là lập luận thực nghiệm cho việc bộ kiểm thử phải có kiểm thử tích hợp chạy trên đường dẫn thật.

### 4.7.2. Hợp nhất các biến thể đọc sai trong chuỗi khung hình video

Một xe đi qua khung hình xuất hiện ở hàng chục khung liên tiếp. Gom kết quả theo chuỗi ký tự là bước đầu tiên và chưa đủ, vì **cùng một biển ở hai khung liền nhau vẫn có thể cho hai chuỗi khác nhau**: khối nhận dạng không tất định ở mức một ký tự. Hệ quả là một video ngắn sinh ra nhiều dòng kết quả cho cùng một chiếc xe.

Tầng nghiệp vụ vì vậy có một lượt hợp nhất thứ hai. Hai chuỗi được coi là cùng một biển vật lý khi thoả **đồng thời**:

| Điều kiện | Ngưỡng | Vì sao cần cả hai |
|---|---|---|
| Gần nhau về chuỗi | khoảng cách Levenshtein $\le 2$ | Chỉ điều kiện này thì hai biển thật sự khác nhau cũng lọt |
| Gần nhau về thời gian | không quá 48 khung | Chỉ điều kiện này thì hai xe khác nhau đi liền nhau cũng lọt |

Riêng ở khoảng cách bằng 2, hai điều kiện trên vẫn chưa đủ chặt, nên mức đó phải qua thêm một **rào ngữ nghĩa dựa trên cấu trúc biển số Việt Nam**: hai chuỗi phải cùng **mã tỉnh hai chữ số**, và **hoặc** cùng chữ cái sê-ri **hoặc** cùng ba chữ số cuối. Rào này khai thác đúng đặc điểm đã phân tích ở 4.6.5 — biển số Việt Nam không phải chuỗi tuỳ ý mà có cấu trúc theo vị trí.

**Bản nào được giữ lại là quyết định về bằng chứng, không phải về thứ tự đến.** Thứ tự ưu tiên: đúng quy chuẩn định dạng trước, rồi **số khung đã bỏ phiếu** cho cách đọc đó, cuối cùng mới tới độ tin cậy của khối nhận dạng. Đặt độ tin cậy xuống cuối là có lý do đo được: ở mức sai khác một ký tự, một lần đọc sai vẫn thường mang điểm tin cậy cao — mục 5.6.5 có ca cụ thể trong đó bản sai đạt 0,994 còn bản đúng 0,996.

### 4.7.3. Thiết kế cơ sở dữ liệu

**a) Lược đồ.** Cơ sở dữ liệu gồm hai bảng có quan hệ một–nhiều: bảng tác vụ ghi nhận mỗi lần sử dụng hệ thống, và bảng lịch sử ghi nhận mỗi biển số được phát hiện. Việc tách thành hai bảng là điều kiện để thống kê đếm đúng, bởi _lượt nhận dạng_ và _biển số phát hiện được_ là hai đại lượng khác nhau: một ảnh chứa ba phương tiện tạo ra một lượt và ba bản ghi. Gộp hai khái niệm sẽ làm số lượt sử dụng bị đánh giá cao hơn thực tế đúng bằng số biển số trung bình trên mỗi ảnh.

Bảng `detection_job` có 11 cột theo dõi trạng thái tác vụ; bảng `detection_history` có 23 cột lưu từng biển số phát hiện được. **Lược đồ đầy đủ ở Phụ lục VII.** Ba cột đáng chú ý vì là hệ quả trực tiếp của các quyết định đã nêu: `raw_ocr_text` cho phép đo đóng góp thuần của khối hậu xử lý (5.5.2); `source_job_id` gom nhiều biển của cùng một lần tải lên về một nhóm, thiếu nó thì thống kê đếm sai; và `upper_char_count` lưu *bằng chứng* để suy ra cách trình bày biển hai dòng lúc đọc, thay vì đoán từ chuỗi phẳng vốn nhập nhằng.

**b) Hai quyết định dữ liệu đáng chú ý.** Chuỗi thô và chuỗi đã chuẩn hoá lưu **song song ở hai cột**: hiệu số độ chính xác giữa chúng chính là NFR-A6 − NFR-A5 ở mục 5.5.2. Và hệ thống lưu **số ký tự dòng trên** của biển hai dòng, vì chuỗi tám ký tự nhóm được theo hai cách đều hợp lệ mà ranh giới hai dòng — thông tin duy nhất phân định được — bị chính bước ghép ngang loại bỏ; giá trị này thu được không tốn thêm chi phí vì bộ nhận dạng vốn trả một mảnh cho mỗi nửa ảnh.

### 4.7.4. Giao diện lập trình

Hệ thống cung cấp giao diện theo phong cách REST với tài liệu đặc tả sinh tự động. Các điểm cuối nghiệp vụ nằm dưới một tiền tố chung, riêng điểm cuối kiểm tra tình trạng đặt ở gốc để hệ thống giám sát và cơ chế kiểm tra sức khoẻ của môi trường container không phụ thuộc vào phiên bản giao diện. Tổng cộng có mười thao tác HTTP trên chín đường dẫn; bảng đặc tả đầy đủ từng điểm cuối được trình bày ở **Phụ lục F.1**.

Bốn quyết định thiết kế đáng ghi nhận. Yêu cầu xử lý video trả về mã trạng thái chấp nhận thay vì mã thành công, do một video 60 giây cần khoảng 200 giây xử lý trên CPU và không client nào chờ được; mã chấp nhận phản ánh đúng ngữ nghĩa "đã tiếp nhận, đang xử lý". Trường hợp ảnh không chứa biển số trả về mã thành công kèm danh sách rỗng thay vì mã lỗi, vì kết quả nhận dạng vẫn tồn tại và là tập rỗng (NFR-R2); trả về mã lỗi sẽ loại toàn bộ trường hợp âm khỏi thống kê. Chức năng tìm kiếm đối chiếu đồng thời chuỗi đã chuẩn hoá và chuỗi thô, để người dùng nhớ dạng nào cũng tra được. Cuối cùng, hai chỉ số thống kê về số lượt và số biển số được trả về tách biệt, kèm mô tả tường minh trong tài liệu đặc tả nhằm ngăn việc gộp nhầm hai đại lượng đã phân tích tại mục 4.7.2a.

## 4.8. Giao diện người dùng

### 4.8.1. Cấu trúc và các màn hình

Giao diện là ứng dụng một trang xây dựng trên React và TypeScript, gồm bốn màn hình: nhận dạng ảnh, nhận dạng video, quét trực tiếp qua webcam và tra cứu lịch sử. Điều hướng được thiết kế phẳng có chủ ý — cả ba màn hình truy cập trực tiếp từ thanh điều hướng — còn chi tiết bản ghi và hộp xác nhận xoá hiển thị dưới dạng hộp thoại chồng lên trang lịch sử để không làm mất ngữ cảnh bộ lọc đang áp dụng.

Toàn bộ giao tiếp với máy chủ tập trung tại một tầng gọi API duy nhất, nơi duy nhất trong giao diện có hiểu biết về thư viện HTTP và mã trạng thái; các thành phần hiển thị chỉ nhận dữ liệu đã có kiểu hoặc đối tượng lỗi đã chuẩn hoá. Không địa chỉ máy chủ nào được viết cứng: gốc địa chỉ đọc từ biến môi trường tại thời điểm biên dịch và mặc định là rỗng, tương ứng cấu hình cùng nguồn gốc.

Hai màn hình sau cùng đáng nói riêng, vì cả hai đều sinh ra từ ràng buộc của tầng dưới. Giao diện có **chế độ quét trực tiếp qua webcam** và **hàng đợi tải lên nhiều ảnh**, cả hai đều sinh ra từ ràng buộc của tầng dưới chứ không phải từ mong muốn thêm tính năng.

**Quét trực tiếp qua webcam.** Trình duyệt lấy khung hình từ camera và gửi từng khung tới `POST /api/detect/frame`. Điểm thiết kế đáng nêu là **vòng lặp một khe**: tại mỗi thời điểm chỉ có đúng một khung đang được gửi đi, và mọi khung camera sinh ra trong lúc chờ đều bị **bỏ thẳng** chứ không xếp hàng. Lý do là một hàng đợi không giới hạn sẽ khiến độ trễ hiển thị tăng dần không giới hạn khi tốc độ camera vượt tốc độ xử lý — người dùng sẽ thấy khung hình cũ dần so với thực tế. Chấp nhận bỏ khung giữ cho kết quả hiển thị luôn thuộc về hiện tại. Phép đo ở 5.6.4 cho thấy tỷ lệ bỏ là đáng kể và **đó là hành vi đúng**: trong 60 giây, camera ảo 30 khung/giây chào 1.801 khung, hệ thống xử lý 338 và bỏ 1.463.

**Hàng đợi tải lên nhiều ảnh.** Người dùng chọn nhiều tệp một lần; giao diện xếp chúng thành một dải xem trước và xử lý tuần tự, hiển thị kết quả ngay khi từng ảnh xong thay vì chờ cả lô. Xử lý tuần tự chứ không song song là quyết định có chủ đích: máy chủ chạy suy luận trên CPU đã ghim số luồng (4.6.8), nên gửi song song chỉ làm các yêu cầu tranh nhau cùng một tài nguyên và kéo dài tổng thời gian.

Cần lưu ý rằng thiết kế ban đầu có năm màn hình. Màn hình tổng quan đã được đưa ra khỏi phạm vi trong hai đợt thu gọn giao diện, kéo theo bốn yêu cầu chức năng chuyển sang mức không thực hiện — trong đó có một yêu cầu ở mức bắt buộc, được nêu rõ tại mục 6.2. Các điểm cuối tương ứng ở phía máy chủ vẫn hoạt động và vẫn có kiểm thử tích hợp; điều bị loại bỏ là hàm gọi phía giao diện, không phải bản thân điểm cuối.

### 4.8.2. Nguyên tắc trải nghiệm người dùng

Mọi thành phần hiển thị dữ liệu cài đặt đủ **bốn trạng thái**: đang tải, có dữ liệu, rỗng và lỗi — thiếu trạng thái rỗng thì màn hình trắng không phân biệt được với lỗi hệ thống. Trạng thái rỗng có ba thông điệp khác nhau, trong đó *ảnh không chứa biển số* là biểu hiện ở tầng giao diện của cùng một quyết định đã áp ở tầng suy luận: **không tìm thấy đối tượng không phải là lỗi**. Thông báo lỗi viết theo cấu trúc hiện tượng – nguyên nhân – khắc phục (NFR-U3). Giao diện hiển thị **đồng thời chuỗi thô và chuỗi đã chuẩn hoá khi hai chuỗi khác nhau**, biến một cột dữ liệu phục vụ nghiên cứu thành bằng chứng quan sát được ngay khi trình diễn.

Riêng client nhận dạng theo khung hình giữ **đúng một yêu cầu đang xử lý** tại mỗi thời điểm: ở tốc độ ~5 khung/giây trên CPU, một vòng lặp gửi theo chu kỳ cố định sẽ khiến hàng đợi tăng không giới hạn, nên khung hình đến trong lúc kênh bận bị **bỏ qua thay vì xếp hàng** — khung kế tiếp luôn cập nhật hơn khung bị bỏ.

## 4.9. Triển khai bằng Docker

Đóng gói phục vụ NFR-C1: môi trường chạy tái lập được, không phụ thuộc máy cá nhân. Ảnh Docker của máy chủ dựng **hai giai đoạn**, chạy dưới người dùng không đặc quyền, **giới hạn tường minh số luồng tính toán** để hai container không cạnh tranh nhân CPU, và đặt thời gian chờ khởi động của cơ chế kiểm tra sức khoẻ đủ dài cho việc nạp trọng số. Ảnh giao diện được dựng rồi phục vụ tĩnh qua máy chủ web nhẹ — ảnh chạy không chứa Node hay mã nguồn. **Trọng số mô hình không nằm trong ảnh Docker** mà gắn từ ngoài, cùng một volume riêng cho bộ đệm mô hình PaddleOCR; thiếu volume này thì mỗi lần dựng lại phải tải vài trăm MB. Bảng biến môi trường ở **Phụ lục VII**. **Trạng thái kiểm chứng:** `docker compose config` hợp lệ; đo hiệu năng trong container thuộc Chương 5.

---
