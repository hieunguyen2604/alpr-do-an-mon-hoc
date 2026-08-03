# CHƯƠNG 4. PHÂN TÍCH VÀ THIẾT KẾ HỆ THỐNG

Trên cơ sở lý thuyết ở Chương 2, chương này phân tích yêu cầu (4.1), thiết lập kiến trúc (4.2), thiết kế chi tiết các thành phần (4.3), thiết kế cơ sở dữ liệu (4.4) và thiết kế giao diện (4.5).

Chương mô tả **thiết kế đã được cài đặt**: tầng API, tầng nghiệp vụ, tầng dữ liệu và lược đồ CSDL đã tồn tại dưới dạng mã chạy được, kiểm chứng bằng lời gọi HTTP thực tế. Phần lớn nội dung được viết khi hệ thống còn chạy pipeline giả lập (`StubPipeline`); tính đến bản cập nhật này hệ thống đã chuyển sang `ALPRPipeline` với mô hình chính thức `models/best.pt` (`/health` báo `model_loaded: true`, engine `yolo:best.pt+paddleocr-PP-OCRv5-mobile`, mAP@0.5 = 0,9829), stub đã ra khỏi đường chạy chính. Điều đó không đổi cách trình bày: chương này nói về *thiết kế* và *khả năng kiểm chứng của thiết kế*, mọi số liệu thực nghiệm nằm ở Chương 6.

---

## 4.1. Phân tích yêu cầu

### 4.1.1. Khảo sát nhu cầu và các tác nhân

Nhận dạng biển số là bài toán nền tảng của bãi đỗ xe tự động, thu phí không dừng, kiểm soát ra vào và giám sát giao thông: biển số là định danh phương tiện duy nhất quan sát được từ xa mà không cần thiết bị gắn trên xe. Áp dụng trực tiếp mô hình ALPR huấn luyện trên dữ liệu nước ngoài vào bối cảnh Việt Nam gặp bốn trở ngại.

**Thứ nhất, biển hai dòng chiếm tỉ trọng lớn** — toàn bộ xe mô tô, xe gắn máy và một phần ô tô — trong khi đa số bộ dữ liệu và mô hình quốc tế giả định biển một dòng. Đây là điểm gãy đã đo được: trên **bộ dữ liệu RodoSol-ALPR của Brazil** (số mẫu một dòng và hai dòng cân bằng nhau), OpenALPR nhận đúng 3.772/4.000 ô tô biển một dòng (94,3%) nhưng chỉ 1.827/4.000 xe máy biển hai dòng (45,7%), chênh **48,6 điểm phần trăm** [7]<!-- laroca_2022_crossdataset -->[88]<!-- laroca_2022_rodosol -->.

> **Lưu ý về phạm vi áp dụng của số liệu.** Cặp số 94,3% / 45,7% được đo trên **bộ RodoSol-ALPR của Brazil**, **không phải dữ liệu Việt Nam**. Đồ án dùng nó như một dẫn chứng tương đương (analogue) về độ khó tương đối của bố cục hai dòng so với một dòng, tuyệt đối không trình bày như số liệu của biển số Việt Nam. Giá trị của nó là chứng minh "biển hai dòng khó hơn" là một sự kiện định lượng chứ không phải một cảm nhận.

**Thứ hai, quy chuẩn biển số mang tính pháp lý và có cấu trúc chặt**: Thông tư 79/2024/TT-BCA (ký 15/11/2024, hiệu lực 01/01/2025) [8]<!-- bocongan_2024_tt79 -->, sửa đổi bởi Thông tư 13/2025/TT-BCA [9]<!-- bocongan_2025_tt13 --> và Thông tư 51/2025/TT-BCA [10]<!-- bocongan_2025_tt51 -->, thông số vật lý theo QCVN 08:2024/BCA [11]<!-- bocongan_2024_qcvn08 -->. Cấu trúc chặt vừa là ràng buộc vừa là **cơ hội thiết kế**: tập ký hiệu hợp lệ ở từng vị trí là hữu hạn và biết trước nên có thể xây khối hậu xử lý dựa trên luật. **Thứ ba, điều kiện thu nhận ảnh khắc nghiệt**: che khuất do mật độ xe máy cao, biển bụi bẩn hoặc cong vênh, góc nghiêng, ngược sáng, ảnh ban đêm. **Thứ tư, không có phần cứng tăng tốc**: máy thực hiện không có GPU CUDA, toàn bộ suy luận và phần trình diễn khi bảo vệ chạy trên CPU (mục 4.1.4).

Hệ thống có bốn tác nhân, ba trong đó tương tác trực tiếp: **người vận hành** (đưa ảnh/video qua giao diện, xem kết quả, tra cứu lịch sử; trình độ cơ bản, hằng ngày — luồng thời gian thực chuyển sang dùng qua API từ 2026-07-20, xem 4.1.3b), **người phân tích** (xem thống kê, lọc và tìm kiếm lịch sử, xuất tệp báo cáo; trung bình, hằng tuần), **nhà phát triển** (tích hợp qua REST API và tài liệu OpenAPI; cao, khi tích hợp), và **hội đồng đánh giá** (quan sát trình diễn, phản biện). Do hệ thống chạy trong mạng nội bộ hoặc `localhost` (giả định A-04), đồ án **không xây dựng xác thực và phân quyền**: việc đó tốn công sức đáng kể mà không đóng góp cho giá trị học thuật. Ba tác nhân đầu vì vậy là các *vai trò sử dụng* trên cùng một giao diện, không phải các *tài khoản* khác nhau.

### 4.1.2. Sơ đồ use case tổng quát và đặc tả các use case chính

#### a) Sơ đồ use case

![](figures/fig-ch4-01.png)

**Hình 4.1.** Sơ đồ use case tổng quát của hệ thống

Ba quan hệ đáng giải thích. **UC-02 «include» UC-09**: video là tác vụ nền bất đồng bộ nên bắt buộc kéo theo theo dõi tiến độ. **UC-08 «include» UC-01, UC-02**: REST API không phải chức năng song song mà là *một lối vào khác* cho cùng nghiệp vụ — giao diện web cũng gọi chính các endpoint đó. **UC-04 «extend» UC-06**: xuất kết quả là mở rộng tuỳ chọn của tra cứu lịch sử. UC-03 gắn với **nhà phát triển** thay vì người vận hành vì từ 2026-07-20 chức năng này chỉ còn lối vào qua `POST /api/detect/frame`, sau khi trang Webcam bị gỡ khỏi giao diện web.

#### b) Đặc tả use case UC-01 — Nhận dạng biển số từ ảnh

UC-01 *Nhận dạng biển số từ ảnh tĩnh*, tác nhân chính là người vận hành, mức **bắt buộc (Must)**. Tiền điều kiện: hệ thống đang chạy, mô hình đã nạp (`/health` báo sẵn sàng). Hậu điều kiện thành công: kết quả hiển thị trên giao diện, một bản ghi tác vụ và không hoặc nhiều bản ghi biển số được lưu, ảnh gốc và ảnh biển số đã cắt tồn tại trên đĩa.

**Luồng chính.** Người dùng chọn tệp ảnh (JPEG, PNG, WebP hoặc BMP); máy chủ kiểm tra hợp lệ bằng **magic bytes** (không tin phần mở rộng) và hạn mức kích thước, tạo `DetectionJob` loại `image`, lưu tệp gốc bằng tên sinh từ UUID, gọi pipeline AI (giải mã, phát hiện các vùng biển số, cắt từng vùng, nhận dạng ký tự, chuẩn hoá và kiểm tra hợp lệ theo định dạng Việt Nam), lưu ảnh biển đã cắt, ghi mỗi biển thành một bản ghi `DetectionHistory` gắn với tác vụ, rồi trả về toạ độ bounding box, chuỗi biển số, độ tin cậy phát hiện, độ tin cậy OCR và thời gian xử lý.

**Ngoại lệ.** A1 — tệp không đúng định dạng ảnh (ví dụ tệp thực thi đổi đuôi `.jpg`): HTTP 400 kèm thông báo tiếng Việt, tiến trình **không** sập. A2 — vượt hạn mức: HTTP 413. A3 — ảnh hợp lệ nhưng không chứa biển số: HTTP **200** với danh sách rỗng, đây là kết quả hợp lệ chứ không phải lỗi. A4 — phát hiện được biển nhưng OCR không đọc ra ký tự: bản ghi **vẫn được lưu** với `plate_number` rỗng (lý do ở 4.4.3(e)). A5 — chuỗi không khớp định dạng Việt Nam nào: lưu với cờ `is_valid_format = false`, không vứt bỏ. A6 — lỗi nội bộ: HTTP 500 với thông báo thân thiện, chi tiết kỹ thuật chỉ ghi log, **không** hiện stack trace. A3 và A4 phân biệt một thiết kế nghiêm túc với một bản demo: "không có biển số trong ảnh" là một *câu trả lời* chứ không phải *sự cố*, còn âm thầm loại bỏ các trường hợp đọc không ra sẽ làm sai lệch chính các số liệu đánh giá mà Chương 6 cần đến.

#### c) Đặc tả use case UC-02 — Nhận dạng biển số từ video

UC-02, tác nhân chính là người vận hành; hậu điều kiện thành công là tác vụ ở trạng thái `completed`, các biển số đã gộp trùng được lưu, video kết quả có gắn nhãn tải về được. Người dùng chọn tệp video (MP4, AVI, MOV hoặc MKV) trong hạn mức; hệ thống lưu tệp, tạo `DetectionJob` trạng thái `pending` và **trả ngay HTTP 202 kèm `job_id`**, không giữ kết nối chờ. Tác vụ nền chuyển sang `processing`, trích khung theo bước nhảy cấu hình được và cập nhật tiến độ sau mỗi khung; kết quả cùng một biển số trên nhiều khung được **gộp trùng**, chỉ giữ lần đọc có độ tin cậy cao nhất. Duyệt hết khung, hệ thống kết xuất video có vẽ bounding box và nhãn, ghi kết quả vào CSDL, chuyển sang `completed`; giao diện hỏi tiến độ định kỳ qua `job_id` và dừng khi tác vụ kết thúc.

**Vì sao phải bất đồng bộ.** Theo phân rã ngân sách độ trễ (4.1.4), một khung mất khoảng 400 ms trên CPU. Video 60 giây ở 30 khung/giây, ngay cả khi chỉ lấy mẫu 1/5 số khung, vẫn phải xử lý 360 khung ≈ 145 giây — vượt xa timeout mặc định của hầu hết proxy và trình duyệt. Xử lý đồng bộ vì thế **không phải một lựa chọn kém mà là một lựa chọn không khả thi**.

#### d) Đặc tả use case UC-03 — Nhận dạng thời gian thực qua webcam

> ⚠️ **Thay đổi phạm vi 2026-07-20:** trang Webcam đã được **gỡ khỏi giao diện web** theo quyết định thu gọn phạm vi demo. Use case này vì vậy được hiện thực và kiểm chứng **ở tầng API** (`POST /api/detect/frame`); tác nhân chính trở thành một *client thời gian thực* bất kỳ gọi API — trang webcam trước đây của giao diện chính là một client như vậy. Các bước thuần giao diện (FR-3.1, FR-3.4) chuyển mức ưu tiên **M → W**.

Tiền điều kiện: client có nguồn thu hình và mã hoá được khung thành JPEG / PNG, máy chủ nạp được trọng số. Hậu điều kiện: các biển quan sát được trong phiên đã lưu có gộp trùng, toàn bộ phiên là **một** bản ghi tác vụ. Client theo chu kỳ cấu hình được chụp một khung và gửi lên máy chủ; lời gọi đầu tiên không kèm định danh phiên nên máy chủ tạo tác vụ mới và trả `job_id`, các lời gọi sau gửi kèm `job_id` đó nên toàn bộ khung của một phiên quy về cùng một tác vụ. Nếu `job_id` không tồn tại hoặc thuộc phiên đã kết thúc, hệ thống **âm thầm mở phiên mới** thay vì báo lỗi, để việc tải lại trang giữa chừng không làm hỏng luồng chụp.

**Ràng buộc riêng.** Vì không có GPU, bắt buộc bỏ bớt khung (frame skipping) kết hợp hàng đợi một khe ở phía client: khung mới bị bỏ qua nếu còn khung đang chờ kết quả. Nếu không, tốc độ chụp (khoảng 30 khung/giây) vượt xa tốc độ xử lý (khoảng 3–5 khung/giây), hàng đợi phình vô hạn và độ trễ hiển thị tăng tuyến tính — hệ thống trông như "chạy được" trong 10 giây đầu rồi tụt hậu ngày càng xa.

### 4.1.3. Yêu cầu chức năng

Đồ án đặc tả **34 yêu cầu chức năng** trong **6 nhóm**, mỗi yêu cầu có mã định danh, mức ưu tiên MoSCoW (Must, Should, Could, Won't) và **một tiêu chí chấp nhận kiểm chứng được bằng một phép thử cụ thể** — một yêu cầu không kèm cách kiểm chứng thì không thể tuyên bố là đã hoàn thành hay chưa.

#### a) Phân bố yêu cầu theo nhóm và mức ưu tiên

**Bảng 4.1.** Phân bố 34 yêu cầu chức năng theo nhóm và mức ưu tiên MoSCoW

| Nhóm | Mã | Phạm vi chức năng | Must | Should | Could | Won't | **Tổng** |
|---|---|---|:---:|:---:|:---:|:---:|:---:|
| FR-1 | FR-1.1 → 1.7 | Nhận dạng từ ảnh tĩnh | 7 | 0 | 0 | 0 | **7** |
| FR-2 | FR-2.1 → 2.6 | Nhận dạng từ video | 5 | 1 | 0 | 0 | **6** |
| FR-3 | FR-3.1 → 3.5 | Nhận dạng thời gian thực (tầng API) | 3 | 0 | 0 | 2 | **5** |
| FR-4 | FR-4.1 → 4.8 | Thống kê, lịch sử và tra cứu | 4 | 1 | 1 | 2 | **8** |
| FR-5 | FR-5.1 → 5.4 | Quản lý dữ liệu | 0 | 2 | 2 | 0 | **4** |
| FR-6 | FR-6.1 → 6.4 | Hệ thống và vận hành | 2 | 2 | 0 | 0 | **4** |
| | | **Tổng cộng** | **21** | **6** | **3** | **4** | **34** |

> ### Bốn yêu cầu mức Won't và hai đợt thu gọn phạm vi ngày 2026-07-20
>
> Cả bốn yêu cầu mức Won't đều **thuần giao diện** và đều chuyển mức trong cùng một ngày qua hai đợt: đợt 1 gỡ trang Webcam (`/webcam`) khiến FR-3.1 và FR-3.4 chuyển **M → W** (năng lực còn lại: `POST /api/detect/frame`, phiên gộp trùng theo `job_id`); đợt 2 gỡ trang Tổng quan / Dashboard (`/dashboard`) khiến **FR-4.1 chuyển M → W** và FR-4.2 chuyển **S → W** (năng lực còn lại: `GET /api/statistics`, chuỗi số liệu theo ngày nằm trong cùng đáp ứng, và `GET /health`).
>
> **Phải nói thẳng: FR-4.1 là yêu cầu mức *Must* đầu tiên — và duy nhất — bị đưa ra khỏi phạm vi trong toàn bộ đồ án.** Trước đó mọi thay đổi phạm vi chỉ đụng tới yêu cầu mức Should trở xuống hoặc tới phần hiển thị của một năng lực vẫn còn nguyên. Bảng đếm ở trên vì vậy giảm từ 22/7/3/2 xuống **21/6/3/4**, và mục 7.3 của Chương 7 ghi nhận đây là một **hạn chế thật** chứ không phải một dòng ghi chú hành chính. Điều **không** thay đổi: cả hai đợt chỉ gỡ **màn hình hiển thị**, không gỡ **năng lực hệ thống** — các endpoint vẫn phục vụ, vẫn nằm trong tài liệu OpenAPI, vẫn có kiểm thử tích hợp (`tests/integration/test_api_statistics.py`, `test_api_health.py`), mã giao diện của cả hai trang còn nguyên trong lịch sử git. Đánh đổi đo được của đợt 2: gỡ thư viện biểu đồ `recharts` cùng trang Tổng quan làm gói tải về của giao diện giảm từ ~730 KB xuống **328,8 KB** (−55%).

#### b) Nội dung cốt lõi của từng nhóm

**FR-1 — Nhận dạng từ ảnh (7 yêu cầu, toàn bộ Must).** Tiếp nhận tệp, kiểm tra hợp lệ, phát hiện *tất cả* vùng biển số, cắt và nhận dạng từng vùng, hậu xử lý chuỗi, lưu kết quả cùng ảnh liên quan, hiển thị có vẽ bounding box — thiếu bất kỳ bước nào thì hệ thống không còn là một hệ thống ALPR. FR-1.5 quy định lưu **cả chuỗi OCR thô lẫn chuỗi đã sửa** (chuỗi thô `51A-I234O` chuẩn hoá thành `51A-12340`, cả hai đều được ghi lại): điều kiện cần để đo đóng góp riêng của khối hậu xử lý ở Chương 6 (lập luận ở 4.4.3(b)).

**FR-2 — Nhận dạng từ video (5 Must, 1 Should).** Bổ sung ba năng lực FR-1 không có: trích khung theo bước nhảy cấu hình được, **gộp trùng** kết quả cùng một biển trên nhiều khung, kết xuất video có gắn nhãn; yêu cầu Should duy nhất là hiển thị tiến độ phần trăm và cho huỷ tác vụ. Không có gộp trùng (FR-2.4), một video 30 giây sinh hàng nghìn bản ghi mô tả cùng vài chiếc xe, làm hỏng toàn bộ thống kê nhóm FR-4 và biến bảng lịch sử thành vô dụng.

**FR-3 — Thời gian thực (3 Must, 2 Won't).** Ban đầu là 5 yêu cầu Must: xin quyền và hiển thị luồng webcam, gửi khung theo chu kỳ cấu hình được, nhận dạng trên luồng trực tiếp, vẽ chồng bounding box, lưu lịch sử phiên có gộp trùng. Theo quyết định 2026-07-20, hai yêu cầu thuần giao diện FR-3.1 và FR-3.4 chuyển **M → W**; FR-3.2, FR-3.3, FR-3.5 vẫn Must và được kiểm chứng **ở tầng API** qua `POST /api/detect/frame`. Ràng buộc hiệu năng của nhóm gắn với việc không có GPU, cụ thể hoá thành NFR-P2.

**FR-4 — Thống kê, lịch sử và tra cứu (4 Must, 1 Should, 1 Could, 2 Won't).** Nhóm đông nhất và chịu tác động nặng nhất: chỉ số tổng hợp trên màn hình Tổng quan (tổng lượt sử dụng, độ tin cậy trung bình, thời gian xử lý trung bình, phân bố theo loại đầu vào — FR-4.1), biểu đồ số lượt theo thời gian (FR-4.2), danh sách lịch sử phân trang, tìm kiếm biển số khớp một phần, lọc theo loại đầu vào / khoảng thời gian / ngưỡng độ tin cậy, xem chi tiết bản ghi, tải ảnh kết quả, sắp xếp theo cột. Đợt thu gọn thứ hai ngày 2026-07-20 gỡ trang Tổng quan: **FR-4.1 chuyển M → W**, **FR-4.2 chuyển S → W**. Đây là lần đầu một yêu cầu mức Must bị đưa ra khỏi phạm vi, không phải một chi tiết kỹ thuật nhỏ: một chỉ tiêu từng được xếp loại "thiếu ⇒ đồ án không đạt" nay không còn được đáp ứng ở tầng giao diện. Nhưng phạm vi mất đi là phạm vi **hiển thị**, không phải **năng lực**: phép tính vẫn nằm trong `StatisticsService` (4.3.2), vẫn phơi ra qua `GET /api/statistics` với đầy đủ chỉ số và chuỗi số liệu theo ngày mà FR-4.1 và FR-4.2 yêu cầu, vẫn có trong OpenAPI và vẫn có kiểm thử tích hợp; thiết kế API ở 4.3.3 **giữ nguyên không sửa một dòng nào** — bằng chứng thực tế cho nguyên tắc tách tầng ở 4.2. Sáu yêu cầu **FR-4.3 đến FR-4.8** (màn hình Lịch sử) **không đổi mức và không đổi nội dung**.

**FR-5 — Quản lý dữ liệu (2 Should, 2 Could).** Xoá bản ghi kèm xoá tệp ảnh (không để lại tệp mồ côi), xuất lịch sử đã lọc ra CSV hoặc JSON, script dọn tệp không còn bản ghi tham chiếu, xoá hàng loạt. Tiêu chí chấp nhận có một chi tiết thực dụng: CSV phải mã hoá UTF-8 **có BOM**, nếu không Excel hiển thị sai toàn bộ ký tự tiếng Việt.

**FR-6 — Hệ thống và vận hành (2 Must, 2 Should).** Endpoint kiểm tra sức khoẻ báo trạng thái nạp mô hình và kết nối CSDL; log có cấu trúc cho mọi lượt nhận dạng và mọi lỗi; thông báo lỗi thân thiện không rò rỉ stack trace; toàn bộ cấu hình đọc từ biến môi trường hoặc tệp cấu hình thay vì hard-code.

#### c) Ma trận truy vết

Mỗi nhóm được truy vết tới giai đoạn cài đặt và hình thức kiểm chứng: FR-1 (Phase 3, 4, 5, 6) — unit test và integration test; FR-2 (Phase 5, 6) — integration test và performance test; FR-3 (Phase 5, tầng API; phần giao diện đã gỡ 2026-07-20) — performance test; FR-4 (Phase 5, 6; FR-4.1/4.2 chỉ còn ở tầng API) — integration test `test_api_statistics.py`, `test_api_health.py` cùng UI test cho FR-4.3 → 4.8; FR-5 (Phase 5, 6) — unit test; FR-6 (Phase 5, 8) — smoke test và stress test. Kết quả thực hiện được báo cáo ở Chương 6.

### 4.1.4. Yêu cầu phi chức năng

Yêu cầu phi chức năng gồm bảy nhóm: hiệu năng (NFR-P), độ chính xác (NFR-A), độ tin cậy (NFR-R), khả năng sử dụng (NFR-U), khả năng bảo trì (NFR-M), bảo mật (NFR-S), tương thích và triển khai (NFR-C), cùng khả năng mở rộng (NFR-SC).

#### a) Nguyên tắc nền tảng: mọi chỉ tiêu hiệu năng đều là chỉ tiêu CPU

> **Toàn bộ chỉ tiêu hiệu năng của đồ án là chỉ tiêu đo trên CPU.**

Máy thực hiện chạy Windows 11 với Python 3.13, **không có GPU CUDA** — phần đồ hoạ là Intel UHD Graphics 770 tích hợp, không hỗ trợ CUDA và không được PyTorch dùng để tăng tốc suy luận. Huấn luyện thực hiện trên GPU miễn phí của Google Colab hoặc Kaggle, nhưng **suy luận và toàn bộ phần trình diễn khi bảo vệ chạy trên CPU của máy cá nhân**.

Đây là **ràng buộc thiết kế** — điều kiện biên mà mọi phương án kỹ thuật phải được đánh giá dưới nó — chứ không phải một hạn chế tạm thời, vì bốn lý do. **Thứ nhất**, nó cố định trong toàn bộ vòng đời đồ án và tại chính thời điểm quan trọng nhất là buổi bảo vệ trên máy cá nhân: một thiết kế chỉ đạt chỉ tiêu khi có GPU là một thiết kế không bao giờ được chứng minh là đạt. **Thứ hai**, nó thay đổi bậc độ lớn của độ trễ chứ không phải vài phần trăm — ở mốc 20 ms mỗi khung hình, xử lý video đồng bộ trong một lời gọi HTTP là hợp lý và webcam xử lý được mọi khung; ở mốc thực tế 400 ms cả hai đều bất khả thi, nên **ràng buộc CPU trực tiếp sinh ra hai quyết định kiến trúc**: video chạy nền bất đồng bộ có theo dõi tiến độ (AD-02) và webcam bỏ khung với hàng đợi một khe. **Thứ ba**, nó chi phối lựa chọn biến thể mô hình phát hiện (n/s/m), biến thể OCR (mobile hay server), kích thước ảnh đầu vào và đặc biệt là **backend suy luận**: benchmark chính thức trên CPU Intel Core i7-13700H cho thấy YOLOv8n chạy qua ONNX Runtime nhanh hơn khoảng **3,73 lần** so với PyTorch thuần (104,61 ms giảm còn 28,02 ms) [18]<!-- ultralytics_2026_openvinoexport -->, lợi ích lớn nhất đúng ở phân khúc mô hình nhỏ đồ án dùng — có GPU thì việc xuất ONNX/OpenVINO và tinh chỉnh số luồng [117]<!-- onnxruntime_2025_threading --> chỉ là tối ưu thứ yếu, không có GPU thì nó thành một phương án chính đáng ngay từ khâu thiết kế. **Thứ tư**, nó buộc phương pháp luận công bố số liệu chặt hơn: văn liệu ALPR thường công bố độ trễ đo trên GPU dòng RTX hoặc V100 với vài chục mili-giây, nên một con số FPS không kèm cấu hình phần cứng là vô nghĩa; đồ án đặt quy tắc bắt buộc — **mọi số liệu hiệu năng công bố phải kèm model CPU, số luồng, kích thước ảnh đầu vào, backend suy luận (PyTorch / ONNX / OpenVINO) và cỡ mẫu đo** — ghi thành ràng buộc chính thức CON-06. Hệ quả: các chỉ tiêu độ trễ dưới đây trông "rộng rãi" hơn văn liệu quốc tế; đó không phải sự dễ dãi mà là sự trung thực về điều kiện đo.

> **Cảnh báo về cách trích dẫn con số này.** Bảng benchmark nguồn có kèm cột mAP, nhưng cột đó được đo trên tập `coco8` chỉ gồm **8 ảnh**, nên không có ý nghĩa thống kê. Đồ án chỉ sử dụng cột thời gian suy luận của bảng và cố ý lược bỏ cột độ chính xác.

#### b) NFR-P — Hiệu năng

**Bảng 4.2.** Chỉ tiêu phi chức năng nhóm hiệu năng (NFR-P)

| Mã | Chỉ tiêu | Mục tiêu | Ngưỡng tối thiểu | Phương pháp đo |
|---|---|---|---|---|
| **NFR-P1** | Độ trễ toàn trình một ảnh (p95) | ≤ 800 ms | ≤ 1500 ms | 100 ảnh test, báo cáo p50/p95/p99 |
| **NFR-P2** | Tốc độ khung hình thời gian thực (webcam — đo ở tầng API) | ≥ 5 FPS hiệu dụng | ≥ 3 FPS | Đo liên tục trong 60 giây |
| **NFR-P3** | Tốc độ xử lý video | ≥ 0,3× thời gian thực | ≥ 0,15× | Video 60 giây xử lý trong ≤ 200 giây |
| **NFR-P4** | Thời gian nạp mô hình khi khởi động | ≤ 15 giây | ≤ 30 giây | Từ lúc khởi động đến khi `/health` báo sẵn sàng |
| **NFR-P5** | Overhead của tầng API (không tính suy luận) | ≤ 50 ms | ≤ 100 ms | Hiệu giữa tổng thời gian request và thời gian pipeline |
| **NFR-P6** | Thời gian truy vấn lịch sử (10.000 bản ghi) | ≤ 500 ms | ≤ 1000 ms | Có áp phân trang và bộ lọc |
| **NFR-P7** | Bộ nhớ thường trú của backend | ≤ 2 GB | ≤ 4 GB | Theo dõi RSS khi chạy tải liên tục |

NFR-P1 xuất phát từ một **phân rã ngân sách độ trễ**: giải mã ảnh và tiền xử lý ~50 ms; suy luận mô hình phát hiện @ 640 px trên CPU ~150 ms; cắt và tiền xử lý vùng biển ~30 ms; nhận dạng ký tự mỗi biển ~120 ms; hậu xử lý regex và kiểm tra hợp lệ < 5 ms; ghi CSDL và lưu ảnh ~50 ms — **tổng cho ảnh chứa một biển số ~405 ms**. Ngân sách 800 ms để lại khoảng hai lần dự phòng cho ảnh nhiều biển (mỗi biển thêm khoảng 150 ms) và cho biến động tải. Các con số này là **ước lượng thiết kế, không phải kết quả đo**; số đo thực tế ở Chương 6.

Ngân sách trên lập cho **runtime suy luận mặc định đã chốt ở mục 3.4 là ONNX Runtime**, không phải cho việc chạy trực tiếp trọng số PyTorch — điểm đã đổi so với quyết định sơ bộ AD-05 (*"PyTorch trước, ONNX/OpenVINO nếu cần"*): ONNX Runtime nhanh gấp khoảng 3,73 lần ở đúng phân khúc đồ án dùng, và việc cho **cả bộ phát hiện lẫn bộ OCR chạy trên một runtime duy nhất** loại bỏ rủi ro xung đột giữa hai framework học sâu trong cùng môi trường Python. Nếu đo thực tế vượt ngưỡng, thứ tự giảm tải đã định trước: (1) lượng tử hoá INT8 bằng OpenVINO kèm tập hiệu chuẩn; (2) giảm kích thước ảnh đầu vào xuống 480 px; (3) chuyển sang biến thể OCR nhẹ hơn — chỉ hạ chỉ tiêu **sau khi** đã thử hết ba phương án, để tránh hạ chuẩn cho tiện.

#### c) NFR-A — Độ chính xác

**Bảng 4.3.** Chỉ tiêu phi chức năng nhóm độ chính xác (NFR-A)

| Mã | Chỉ tiêu | Mục tiêu | Ngưỡng tối thiểu |
|---|---|---|---|
| **NFR-A1** | mAP@0.5 của bộ phát hiện | ≥ 0,90 | ≥ 0,85 |
| **NFR-A2** | mAP@0.5:0.95 của bộ phát hiện | ≥ 0,65 | ≥ 0,55 |
| **NFR-A3** | Precision / Recall phát hiện | ≥ 0,92 / ≥ 0,90 | ≥ 0,88 / ≥ 0,85 |
| **NFR-A4** | Độ chính xác OCR mức ký tự (1 − CER) | ≥ 0,95 | ≥ 0,92 |
| **NFR-A5** | Độ chính xác biển đầy đủ **trước** hậu xử lý | ≥ 0,85 | ≥ 0,80 |
| **NFR-A6** | Độ chính xác biển đầy đủ **sau** hậu xử lý | ≥ 0,90 | ≥ 0,85 |
| **NFR-A7** | Độ chính xác toàn trình (ảnh vào → biển đúng) | ≥ 0,88 | ≥ 0,82 |

Cặp NFR-A5 và NFR-A6 được đặt **tách bạch** có chủ đích: hiệu số giữa chúng chính là đóng góp định lượng của khối hậu xử lý — đại lượng đo được và bảo vệ được, thay vì chỉ phát biểu định tính rằng "hệ thống có thêm bước sửa lỗi bằng regex". Đo được hiệu số này phụ thuộc hoàn toàn vào một quyết định ở tầng dữ liệu (lưu cả chuỗi thô lẫn chuỗi đã sửa, 4.4.3(b)) — ví dụ điển hình cho thấy một chỉ tiêu đánh giá học thuật ràng buộc ngược lên lược đồ CSDL. Hai yêu cầu phân tích bổ sung: **NFR-A8** — báo cáo độ chính xác **tách riêng biển một dòng và biển hai dòng**, căn cứ là số liệu 94,3% / 45,7% **đo trên bộ RodoSol-ALPR (Brazil)** đã dẫn ở 4.1.1, vì một con số tổng thể duy nhất sẽ **che giấu** đúng điểm gãy cần phân tích; **NFR-A9** — báo cáo theo điều kiện ảnh (ban ngày, ban đêm, nghiêng, mờ) nếu bộ dữ liệu có nhãn phù hợp.

#### d) Các nhóm yêu cầu phi chức năng còn lại

**NFR-R — Độ tin cậy.** Không sập khi gặp đầu vào hỏng, sai định dạng hoặc độc hại (mục tiêu 100% lỗi đều bị bắt và xử lý); ảnh không có biển số trả kết quả rỗng hợp lệ với HTTP 200; tác vụ video thất bại giữa chừng không để lại bản ghi hoặc tệp rác; tỉ lệ thành công khi chạy liên tục một giờ ≥ 99%; CSDL sống sót qua khởi động lại mà không mất dữ liệu.

**NFR-U — Khả năng sử dụng.** Người dùng mới hoàn thành lượt nhận dạng ảnh đầu tiên trong không quá ba thao tác nhấp chuột và không cần đọc tài liệu; mọi thao tác trên 500 ms phải có phản hồi trực quan; thông báo lỗi bằng tiếng Việt nêu rõ nguyên nhân và cách khắc phục, không hiển thị mã lỗi kỹ thuật; giao diện dùng được từ độ phân giải 1366×768 trở lên; tương phản chữ chính đạt WCAG AA (≥ 4,5:1).

**NFR-M — Khả năng bảo trì.** Nhóm ảnh hưởng lớn nhất tới kiến trúc: mã AI tách biệt hoàn toàn khỏi mã API (NFR-M1); bao phủ test tầng nghiệp vụ ≥ 70% (NFR-M2); mọi hàm public có type hint và docstring (NFR-M3); không hard-code đường dẫn (NFR-M4); thay được bộ OCR khác mà không sửa mã tầng API (NFR-M5); mã tuân thủ định dạng và lint tự động (NFR-M6). NFR-M1 và NFR-M5 **là yêu cầu kiến trúc, không phải nguyện vọng** — chúng là lý do tồn tại của tầng AI độc lập ở mục 4.2.

**NFR-S — Bảo mật.** Mô hình đe doạ ở mức hạn chế do hệ thống chạy nội bộ, nhưng vẫn yêu cầu: kiểm tra tệp tải lên bằng magic bytes; chống path traversal bằng cách sinh lại tên tệp từ UUID; giới hạn kích thước tệp ở phía máy chủ; CORS chỉ cho phép origin đã khai báo, không dùng ký tự đại diện; không ghi dữ liệu nhạy cảm vào log; truy vấn CSDL luôn tham số hoá qua ORM.

**NFR-C — Tương thích và triển khai.** Chạy trên Windows, Linux và macOS qua Docker với một lệnh duy nhất; hoạt động **không cần GPU** và đây là *chế độ mặc định* chứ không phải chế độ dự phòng; hỗ trợ Chrome, Edge, Firefox bản mới; cài từ đầu trên máy sạch theo README trong không quá 15 phút. **NFR-SC — Khả năng mở rộng.** Ổn định với ít nhất 5 yêu cầu đồng thời; hiệu năng không suy giảm ở quy mô 100.000 bản ghi; tác vụ video chạy nền không chặn các yêu cầu khác.

> **Giới hạn đã biết cần công bố.** SQLite chỉ cho phép **một tiến trình ghi tại một thời điểm**. Với quy mô đồ án, giới hạn này chấp nhận được và không ảnh hưởng tới việc đạt các chỉ tiêu trên. Tuy nhiên nó phải được nêu rõ trong phần Hạn chế của đồ án, kèm hướng khắc phục (chuyển sang PostgreSQL) nếu triển khai thực tế. Việc chủ động nêu ra một giới hạn kèm phương án xử lý là cách trình bày trung thực hơn và cũng vững vàng hơn khi phản biện so với việc để nó bị phát hiện.

---

## 4.2. Kiến trúc hệ thống

### 4.2.1. Nguyên tắc kiến trúc

**Kiến trúc sạch và quy tắc phụ thuộc.** Phụ thuộc chỉ được hướng vào trong, từ các chi tiết kỹ thuật dễ thay đổi (framework web, CSDL, giao diện) về phía các quy tắc nghiệp vụ ổn định; thành phần vòng trong **không được biết gì** về thành phần vòng ngoài. Ở bài toán này, thứ ổn định là thuật toán nhận dạng biển số — phát hiện vùng, cắt, đọc ký tự, chuẩn hoá theo quy chuẩn Việt Nam — vì nó là bản chất đề tài và tồn tại độc lập với việc kết quả được trả qua HTTP, ghi vào tệp hay in ra màn hình; thứ dễ thay đổi là việc dùng FastAPI hay Flask, SQLite hay PostgreSQL, React hay Vue. Do đó **pipeline AI phải nằm ở vòng trong cùng**, tầng web phụ thuộc vào nó chứ không ngược lại.

**Các nguyên lý SOLID được vận dụng.** *Trách nhiệm đơn nhất*: bộ phát hiện chỉ trả bounding box, bộ nhận dạng chỉ chuyển ảnh biển số thành chuỗi, bộ chuẩn hoá chỉ biến chuỗi thô thành chuỗi hợp quy chuẩn — phân tách này cho phép **đo hiệu năng và độ chính xác của từng khối riêng biệt**, điều kiện cần để chương đánh giá nói được lỗi nằm ở khâu phát hiện hay khâu đọc ký tự. *Thay thế Liskov*: mọi cài đặt bộ phát hiện phải thay thế được cho nhau mà không làm hỏng pipeline — được dùng theo nghĩa đen khi hệ thống chạy bằng pipeline giả lập tuân thủ đúng hợp đồng của pipeline thật. *Đảo ngược phụ thuộc*: tầng nghiệp vụ phụ thuộc vào một *hợp đồng trừu tượng* chứ không vào lớp pipeline cụ thể, cài đặt được tiêm từ bên ngoài.

**Bảng 4.4.** Bốn ràng buộc kiến trúc và hệ quả trực tiếp

| # | Ràng buộc | Nguồn gốc | Hệ quả kiến trúc trực tiếp |
|---|---|---|---|
| **1** | **Không trộn mã AI với mã API** | NFR-M1 | Pipeline AI là một package Python độc lập, **không import bất cứ thành phần nào của framework web** |
| **2** | **Mọi thành phần AI phải thay thế được** | NFR-M5 | Bộ phát hiện, bộ nhận dạng và bộ chuẩn hoá đều đứng sau lớp trừu tượng |
| **3** | **Không hard-code đường dẫn** | NFR-M4 | Mọi đường dẫn đi qua một đối tượng cấu hình tập trung, đọc từ biến môi trường |
| **4** | **Chạy được không cần GPU** | CON-02, NFR-C2 | Thiết bị suy luận là tham số cấu hình, giá trị mặc định là `cpu` |

Ràng buộc thứ tư đáng lưu ý ở cách phát biểu: nó **không** nói "hệ thống có chế độ dự phòng chạy CPU khi không tìm thấy GPU" — cách nói đó ngầm coi CPU là trường hợp suy biến — mà nói CPU là *cấu hình mặc định*, GPU nếu có chỉ là một giá trị khác của cùng tham số. Khác biệt này dẫn tới khác biệt thật trong mã nguồn: đường chạy trên CPU là đường được kiểm thử thường xuyên nhất, không phải một nhánh hiếm khi chạy tới.

### 4.2.2. Kiến trúc phân tầng

![](figures/fig-ch4-02.png)

**Hình 4.2.** Kiến trúc phân tầng năm tầng và chiều phụ thuộc

**Bảng 4.5.** Trách nhiệm của từng tầng trong kiến trúc phân tầng

| Tầng | Trách nhiệm | Được phép biết về |
|---|---|---|
| **1 — Trình bày** | Thu nhận thao tác người dùng, gọi API, hiển thị kết quả, quản lý trạng thái giao diện | Hợp đồng HTTP của tầng 2 |
| **2 — API** | Định tuyến, kiểm tra hợp lệ đầu vào, xác thực kiểu dữ liệu, ánh xạ ngoại lệ thành mã trạng thái HTTP, sinh tài liệu OpenAPI | Tầng 3 |
| **3 — Nghiệp vụ** | Điều phối các bước nghiệp vụ: tạo tác vụ, gọi pipeline, lưu tệp, ghi CSDL, gộp trùng, tổng hợp thống kê | Tầng 4 và tầng 5 |
| **4 — AI** | Phát hiện, nhận dạng, chuẩn hoá biển số | **Chỉ NumPy, OpenCV và các thư viện học sâu** |
| **5 — Dữ liệu** | Truy vấn và ghi CSDL, đọc ghi kho tệp | Lược đồ CSDL và hệ thống tệp |

Sau hai đợt thu gọn phạm vi ngày 2026-07-20, tầng trình bày còn **ba trang** (đã gỡ trang Webcam và trang Tổng quan), nhưng **tầng 2 đến tầng 5 không đổi một dòng nào**: `POST /detect/frame`, `GET /statistics`, `GET /health` vẫn ở tầng 2, `StatisticsService` vẫn ở tầng 3, cả ba endpoint vẫn có kiểm thử tích hợp và nay phục vụ client gọi API. Đây là phép thử ngoài dự kiến cho nguyên tắc phụ thuộc một chiều. **Điểm mấu chốt của sơ đồ:** khối tầng AI **không có mũi tên nào đi lên** — nó không biết gì về HTTP, về CSDL, hay về việc thành phần nào đang gọi nó.

### 4.2.3. Nguyên tắc tách tầng AI khỏi tầng API

> **Không một tệp mã nguồn nào trong package `ai/inference/` được phép import FastAPI, Pydantic, SQLAlchemy hay bất kỳ thành phần nào của tầng web và tầng dữ liệu.** Chiều ngược lại được phép và là bắt buộc: tầng nghiệp vụ import các kiểu dữ liệu và lớp trừu tượng từ tầng AI.

**Ba lợi ích.** *Kiểm thử độc lập*: một bài kiểm thử chỉ cần nạp một mảng NumPy và so sánh đầu ra, không phải dựng ứng dụng web và yêu cầu HTTP giả lập — hạ tầng vốn không liên quan tới câu hỏi cần trả lời nhưng lại là nơi phát sinh lỗi. *Tái sử dụng trong script huấn luyện và đánh giá*: script huấn luyện trên Colab và script đánh giá cục bộ là chương trình dòng lệnh, không phải ứng dụng web; nếu logic tiền xử lý, cắt vùng và chuẩn hoá chuỗi nằm lẫn trong hàm xử lý HTTP thì script đánh giá phải sao chép lại, và hai bản sao sẽ lệch nhau, dẫn tới tình huống tệ nhất có thể xảy ra với một đồ án — **con số công bố trong báo cáo đánh giá không phải con số mà hệ thống thực sự tạo ra**. *Thay engine không sửa tầng API*: chọn kích thước mô hình, biến thể OCR hay có xuất ONNX hay không chỉ là thay một cài đặt lớp con sau lớp trừu tượng.

Lợi ích này **đã được kiểm chứng trên thực tế**: suốt Phase 5–7 hệ thống chạy với `StubPipeline`, nhờ đó toàn bộ tầng API, tầng nghiệp vụ, lược đồ CSDL và giao diện đã được xây dựng và kiểm chứng bằng lời gọi HTTP **trước khi mô hình được huấn luyện**; khi trọng số sẵn sàng, việc chuyển sang `ALPRPipeline` chỉ là đổi thành phần được tiêm vào tầng nghiệp vụ, **không sửa một dòng nào** ở router, service hay schema. Không có ràng buộc tách tầng thì thứ tự công việc bắt buộc phải là "huấn luyện xong mới xây được phần mềm", dồn toàn bộ rủi ro vào cuối lịch trình. Để trạng thái mô phỏng không bị nhầm với vận hành thật, `/health` báo `degraded` chừng nào pipeline giả lập còn được dùng: một hệ thống trả kết quả bịa mà báo "khoẻ mạnh" là một hệ thống nói dối.

**Kiểm chứng ràng buộc bằng công cụ.** Một ràng buộc chỉ nằm trong tài liệu là ràng buộc sẽ bị vi phạm — cách nhanh nhất để thêm một trường vào kết quả trả về luôn là import thẳng một lớp Pydantic vào module AI, việc không gây lỗi ngay và chỉ bộc lộ nhiều tuần sau khi script đánh giá không chạy được nữa. Đồ án vì vậy đặt **hai lớp kiểm chứng tự động**. Lớp thứ nhất là kiểm tra tĩnh bằng grep, điều kiện đạt là **không có kết quả nào**:

```bash
grep -rnE "^\s*(import|from)\s+(fastapi|pydantic|starlette|sqlalchemy|backend)" ai/inference/
```

Phép này cực rẻ và gắn được vào hook trước khi commit, nhưng chỉ thấy các import tường minh ở đầu tệp. Lớp thứ hai bịt lỗ hổng đó: khởi động một tiến trình Python sạch, import *chỉ* package AI, rồi soi `sys.modules` — nếu tầng AI thật sự độc lập thì danh sách module đã nạp không được chứa module nào thuộc `fastapi`, `starlette`, `pydantic`, `sqlalchemy` hay `backend`; ngược lại tiến trình in danh sách vi phạm và thoát với mã lỗi. Phép động mạnh hơn ở ba điểm: bắt được import muộn trong thân hàm khi hàm đó chạy lúc khởi tạo; bắt được **import bắc cầu** khi module AI kéo theo một module tưởng vô hại nhưng module đó kéo theo cả tầng web; và nó đo *thực tế đã nạp gì vào bộ nhớ* thay vì *mã trông như thế nào*. Cả hai đều rẻ nên đồ án chạy cả hai (grep ở mọi lần commit, kiểm tra động như một bài test), kết quả thực thi báo cáo ở Chương 6; phép động còn đo gián tiếp **thời gian nạp và dung lượng bộ nhớ** của riêng tầng AI, liên quan trực tiếp tới NFR-P4 và NFR-P7.

### 4.2.4. Luồng xử lý của pipeline AI

![](figures/fig-ch4-03.png)

**Hình 4.3.** Luồng xử lý của pipeline AI, các khối tô đỏ là nhánh biển hai dòng

**Nhánh xử lý biển hai dòng.** Các khối tô đỏ là phần khó nhất của đồ án và là rủi ro kỹ thuật đã xác định từ khâu lập kế hoạch (R-04). Các bộ OCR dựng sẵn được huấn luyện quanh giả định văn bản nằm trên một dòng ngang, nên với biển hai dòng chúng đọc theo thứ tự không xác định, ghép lẫn ký tự của hai dòng hoặc bỏ sót một dòng — cho ra chuỗi lộn xộn mà không luật hậu xử lý nào cứu được; đây chính là cơ chế đứng sau chênh lệch 48,6 điểm phần trăm đã dẫn ở 4.1.1 [7]<!-- laroca_2022_crossdataset -->. Giải pháp: **tách vùng biển thành hai nửa trên và dưới, nhận dạng từng nửa độc lập, rồi ghép kết quả theo thứ tự trên trước dưới sau** — mỗi nửa lúc này là một dòng văn bản ngang thông thường, đúng giả định mà bộ OCR được thiết kế cho.

**Phân loại số dòng.** Theo kết luận ở mục 2.6.3(e), hệ thống dùng **hai cơ chế xếp chồng**. *Cơ chế chính*: lấy lớp trực tiếp từ bộ phát hiện, vốn được huấn luyện hai lớp (`0` = một dòng, `1` = hai dòng) — chính xác nhất vì mô hình "nhìn" được nội dung bên trong biển chứ không chỉ hình dạng hộp bao, chi phí suy luận tăng gần bằng không; cái giá là dữ liệu huấn luyện phải gán nhãn hai lớp ngay từ đầu. *Cơ chế dự phòng*: ngưỡng tỉ lệ khung, dùng khi bộ phát hiện chưa có nhãn hai lớp hoặc độ tin cậy phân lớp thấp, căn cứ kích thước vật lý chuẩn tại QCVN 08:2024/BCA [11]<!-- bocongan_2024_qcvn08 --> — ô tô biển dài 520 × 110 mm cho tỉ lệ 4,727 (một dòng), ô tô biển ngắn 330 × 165 mm cho 2,000 (hai dòng), xe mô tô và xe gắn máy 190 × 140 mm cho 1,357 (hai dòng). Ba giá trị tách biệt rõ rệt, không loại biển nào rơi vào khoảng mở (2,000 ; 4,727), nên bộ ngưỡng ở Bảng 2.11 của Chương 2 (AR < 2,5 là hai dòng; AR > 3,0 là một dòng; khoảng giữa là vùng nghi ngờ, thử cả hai nhánh) đủ dùng làm lớp dự phòng. Căn cứ vào quy chuẩn pháp lý thay vì một ngưỡng chọn theo cảm tính khiến ngưỡng giải thích được và bảo vệ được.

> **Điều kiện áp dụng bắt buộc của cơ chế dự phòng.** Như đã cảnh báo ở mục 2.2.6(c), tỉ lệ khung phải được đo trên ảnh **đã nắn chỉnh phối cảnh** hoặc trên **hộp bao xoay tối thiểu**, tuyệt đối không đo trên hộp bao thẳng trục thô do bộ phát hiện trả về: một biển một dòng chụp nghiêng có hộp bao thẳng trục với tỉ lệ tụt xuống dưới 3,0 và sẽ bị phân loại nhầm thành biển hai dòng. Đây cũng là lý do khối hiệu chỉnh hình học được đặt **trước** bước xác định số dòng. Ngoài ra, ba giá trị 4,727 / 2,000 / 1,357 là tỉ lệ **danh định của biển vật lý**, trong khi thứ đo được là tỉ lệ của vùng ảnh sau phép chiếu phối cảnh — hai đại lượng chỉ trùng nhau khi biển gần chính diện.

Thuật toán tách chi tiết — cắt cứng theo tỉ lệ chiều cao, hay dựa trên phân tích hình chiếu ngang của ảnh nhị phân — sẽ được xác định và so sánh bằng thực nghiệm, kết quả ở Chương 6.

**Nhánh giữ lại kết quả không hợp lệ.** Khối `WARN` thể hiện quyết định: biển không khớp định dạng Việt Nam nào **vẫn được lưu**, chỉ bị đánh cờ `is_valid_format = false`. Loại bỏ chúng vừa khiến hệ thống im lặng vứt bỏ dữ liệu, vừa tiêu huỷ đúng những trường hợp giá trị nhất cho phân tích lỗi: một biển đọc ra `51A-1234X` trong khi vị trí cuối chỉ được phép là chữ số cho biết chính xác bộ OCR đang nhầm ở đâu.

**Thiết kế sẵn sàng cho việc đo lường.** **Chuỗi OCR thô được giữ lại như một sản phẩm đầu ra riêng biệt**, song song với chuỗi đã chuẩn hoá, chứ không bị khối chuẩn hoá ghi đè — biểu hiện ở tầng pipeline của cùng một quyết định xuất hiện lại ở tầng CSDL (4.4.3b) và ở tầng chỉ tiêu đánh giá (NFR-A5 so với NFR-A6).

### 4.2.5. Bảng tổng hợp các quyết định kiến trúc

Mỗi quyết định được ghi kèm lý do và **đánh đổi phải chấp nhận** — chủ ý, vì một quyết định được trình bày như thể không có nhược điểm là một quyết định chưa được cân nhắc đủ.

**Bảng 4.6.** Các quyết định kiến trúc AD-01 … AD-08

| Mã | Quyết định về | Lựa chọn | Lý do | Đánh đổi phải chấp nhận |
|---|---|---|---|---|
| **AD-01** | Quan hệ giữa tầng AI và tầng API | Tầng AI là package Python độc lập | NFR-M1; kiểm thử độc lập, tái dùng được trong script huấn luyện và đánh giá (mục 4.2.3) | Thêm một lớp gián tiếp giữa hai tầng |
| **AD-02** | Xử lý video | **Bất đồng bộ, trả `job_id` ngay** | Thời gian xử lý vượt xa timeout HTTP (NFR-SC3); xem mục 4.1.2(c) | Giao diện phải hỏi tiến độ định kỳ; cần quản lý vòng đời tác vụ |
| **AD-03** | Thời gian thực (webcam) | Client gửi từng khung qua HTTP (`POST /detect/frame`) | Đơn giản, dễ gỡ lỗi, đủ cho mức ~5 FPS | Cần tốc độ khung hình cao hơn thì phải chuyển sang WebSocket |
| **AD-04** | Gộp trùng biển số | Theo chuỗi ký tự kết hợp cửa sổ thời gian | Đơn giản hơn nhiều so với bám vết đối tượng, đủ dùng cho FR-2.4 | Kém chính xác nếu hai xe cùng biển số trong một video — thực tế không xảy ra |
| **AD-05** | Runtime suy luận | **ONNX Runtime làm mặc định**, OpenVINO là tối ưu bổ sung | Nhanh hơn PyTorch khoảng 3,73 lần ở phân khúc nano; một runtime duy nhất cho cả hai mô hình loại bỏ xung đột framework (mục 3.4) | Thêm bước xuất mô hình; phải đặt tường minh số luồng nội bộ |
| **AD-06** | Thiết bị suy luận | Cấu hình được, mặc định `cpu` | CON-02 — máy phát triển không có GPU CUDA | — |
| **AD-07** | Lưu trữ ảnh và video | Tệp trên đĩa, CSDL chỉ giữ đường dẫn | Tránh phình tệp SQLite do BLOB (mục 4.3.2c) | Phải giữ đồng bộ giữa tệp và bản ghi (FR-5.1, FR-5.3) |
| **AD-08** | Đặt tên tệp | Sinh từ UUID, không dùng tên gốc | NFR-S2 — chống path traversal | Phải lưu tên gốc ở một trường riêng nếu muốn hiển thị lại |

Về **AD-03**: sau khi trang Webcam bị gỡ (2026-07-20), "client" là bất kỳ chương trình nào gọi API; quyết định không đổi vì ở mức ~5 FPS trên CPU, nút thắt là thời gian suy luận từng khung chứ không phải overhead giao thức. Về **AD-05**: đây là quyết định duy nhất đã **thay đổi** so với bản phác thảo ban đầu (*"PyTorch trước, ONNX/OpenVINO nếu cần"*); ghi nhận tường minh thay đổi này thay vì lặng lẽ sửa bảng là một phần của yêu cầu truy vết quyết định thiết kế.

---

## 4.3. Thiết kế chi tiết

### 4.3.1. Thiết kế module tầng AI

![](figures/fig-ch4-04.png)

**Hình 4.4.** Sơ đồ lớp của tầng AI — ba lớp trừu tượng và các kiểu dữ liệu bất biến

Tầng AI tổ chức quanh ba lớp trừu tượng cùng một tập kiểu dữ liệu bất biến truyền giữa các giai đoạn. `BaseDetector.detect(image) → list[PlateDetection]` trả danh sách vùng biển số kèm độ tin cậy; ảnh không có biển số trả danh sách rỗng, **không** ném ngoại lệ. `BaseRecognizer.recognize(plate_image) → PlateRecognition` trả chuỗi đọc được kèm độ tin cậy; không đọc được ký tự nào thì trả chuỗi rỗng, **không** ném ngoại lệ. `BaseNormalizer.normalize(raw_text) → tuple[str, bool]` trả cặp (chuỗi đã chuẩn hoá, cờ hợp lệ). Hợp đồng "trả rỗng chứ không ném ngoại lệ" nhất quán với NFR-R2: **không tìm thấy** và **lỗi** là hai chuyện khác nhau, trộn chúng ở tầng thấp buộc mọi tầng trên phải xử lý ngoại lệ cho một tình huống bình thường. Hai lớp đầu còn có `warmup()` với cài đặt mặc định rỗng, vì lần suy luận đầu tiên sau khi nạp mô hình chậm hơn đáng kể do cấp phát bộ nhớ và biên dịch nhân tính toán: không làm nóng trước thì lượt nhận dạng đầu của người dùng chậm bất thường và phép đo độ trễ đầu tiên trong benchmark bị nhiễu.

Các kiểu dữ liệu được khai báo **bất biến** (`frozen dataclass`) ở những chỗ có thể, vì chúng đi qua nhiều tầng và được ghi vào CSDL nên một tầng trung gian vô tình sửa giá trị sẽ khiến việc truy vết rất khó; riêng `DetectionResult` và `PipelineResult` không bất biến vì `DetectionResult` chứa mảng ảnh vùng biển số — đối tượng nặng cần giải phóng sau khi lưu xuống đĩa. `BoundingBox` lưu toạ độ dạng `(x, y, width, height)` để khớp trực tiếp bốn cột `bbox_x`, `bbox_y`, `bbox_w`, `bbox_h`, đồng thời cung cấp thuộc tính dẫn xuất `aspect_ratio` phục vụ phân loại số dòng ở 4.2.4. Tên thuộc tính của `PlateDetection` và `PlateRecognition` được đặt **trùng khớp có chủ đích** với tên cột CSDL, nhờ vậy tầng lưu trữ chỉ sao chép trường-sang-trường: một lớp biên dịch trung gian sẽ là thêm một chỗ để `confidence` và `ocr_confidence` bị hoán đổi — đúng loại lỗi mà việc tách chúng thành hai cột được thiết kế để ngăn (4.4.3a). Lớp điều phối `ALPRPipeline` nhận ba thành phần qua hàm khởi tạo và chỉ điều phối, **không chứa logic học sâu nào**, nên kiểm thử được hoàn toàn bằng thành phần giả lập.

### 4.3.2. Thiết kế tầng nghiệp vụ

Tầng nghiệp vụ gồm bốn service: `DetectionService` điều phối toàn bộ nghiệp vụ nhận dạng (tạo tác vụ, gọi pipeline, lưu ảnh, ghi bản ghi, xử lý video nền, gộp trùng, quản lý vòng đời tác vụ); `HistoryService` truy vấn lịch sử có lọc, sắp xếp, phân trang, lấy chi tiết, xoá bản ghi kèm tệp và xuất dữ liệu; `StatisticsService` tổng hợp chỉ số và chuỗi số liệu theo ngày cho `GET /api/statistics`; `StorageService` lưu, đọc, xoá tệp, sinh tên tệp an toàn từ UUID và ánh xạ đường dẫn nội bộ sang URL công khai.

#### a) Hợp đồng pipeline được khai báo bằng giao thức cấu trúc

`DetectionService` phụ thuộc vào một **giao thức** (`typing.Protocol`) khai báo ba thành viên — `name`, `is_ready`, `process(image) → PipelineResult` — chứ không vào lớp `ALPRPipeline` cụ thể. Chọn giao thức cấu trúc thay vì lớp cơ sở trừu tượng là có chủ ý: lớp cơ sở trừu tượng đòi hỏi cài đặt phải **kế thừa**, tức package AI phải import một lớp do tầng nghiệp vụ định nghĩa — đúng phụ thuộc ngược chiều mà ràng buộc số 1 cấm; còn một lớp thoả mãn giao thức cấu trúc chỉ bằng cách *có đúng các thành viên đó*, nên mũi tên phụ thuộc vẫn đi một chiều. Giao thức được thoả mãn bởi ba cài đặt: `ALPRPipeline` (đường chạy chính), `UnavailablePipeline` (phương án lùi khi thiếu trọng số — ném lỗi thay vì bịa kết quả) và `StubPipeline` (chỉ chạy khi đặt tường minh `ALPR_USE_STUB=true`). Việc chuyển từ stub sang pipeline thật đã diễn ra **mà không sửa dòng nào trong tầng nghiệp vụ**.

#### b) Xử lý video nền và gộp trùng

![](figures/fig-ch4-05.png)

**Hình 4.5.** Sơ đồ trạng thái của tác vụ xử lý video nền

Trạng thái `pending` được giữ tách biệt với `processing` có chủ đích: vì lời gọi tải video trả về ngay, có một khoảng thời gian tác vụ đã được ghi nhận nhưng tác vụ nền chưa kịp tiếp nhận — gộp hai trạng thái thì không phân biệt được một tác vụ *đang xếp hàng* với một tác vụ *đã treo*. Gộp trùng (FR-2.4) hoạt động theo chuỗi ký tự biển số kết hợp cửa sổ thời gian, giữ lần đọc có độ tin cậy cao nhất. Phương án thay thế là bám vết đối tượng qua các khung hình; đồ án cố ý **không** chọn và ghi rõ trong phạm vi, vì tracking phức tạp hơn đáng kể và thêm một họ siêu tham số cần tinh chỉnh, trong khi nhược điểm đã biết của gộp theo chuỗi ký tự — hai xe khác nhau mang cùng biển số trong một video — không xảy ra trong thực tế.

#### c) Kho tệp tách khỏi cơ sở dữ liệu

`StorageService` lưu ảnh và video **trên hệ thống tệp**, CSDL chỉ giữ đường dẫn. Lưu nhị phân dưới dạng BLOB sẽ khiến tệp SQLite phình rất nhanh (mỗi ảnh vài trăm KB, mỗi video hàng chục MB), làm chậm mọi truy vấn kể cả truy vấn không đụng tới ảnh và khiến việc sao lưu nặng nề. Cái giá phải trả là hai nguồn dữ liệu phải giữ đồng bộ: xoá bản ghi phải xoá tệp (FR-5.1) và cần script dọn tệp mồ côi (FR-5.3). Tên tệp sinh từ UUID thay vì tên gốc do người dùng cung cấp là biện pháp đáp ứng NFR-S2, vì tên tệp do người dùng kiểm soát là véc-tơ path traversal kinh điển và một tên chứa `../` có thể khiến hệ thống ghi đè tệp ngoài thư mục lưu trữ.

### 4.3.3. Thiết kế REST API

API theo phong cách REST, tự sinh tài liệu OpenAPI 3.x và Swagger UI. Endpoint nghiệp vụ nằm dưới tiền tố `/api` cấu hình được; riêng endpoint kiểm tra sức khoẻ đặt ở gốc để công cụ giám sát và Docker healthcheck truy cập không phụ thuộc phiên bản API.

**Bảng 4.7.** Đặc tả các endpoint REST API

| # | Phương thức | Đường dẫn | Đầu vào | Đầu ra | Mã trạng thái |
|:--:|---|---|---|---|---|
| 1 | `POST` | `/api/detect/image` | `file` — ảnh JPEG / PNG / WebP / BMP | Danh sách kết quả: bounding box, `plate_number`, `raw_ocr_text`, `confidence`, `ocr_confidence`, `is_valid_format`, `plate_line_count`, thời gian xử lý, `job_id` | **200** OK · 400 sai định dạng · 413 vượt kích thước · 422 thiếu tham số · 500 lỗi nội bộ |
| 2 | `POST` | `/api/detect/video` | `file` — video MP4 / AVI / MOV / MKV | `job_id`, `status`, `progress`, `created_at` | **202** Accepted · 400 · 413 · 422 · 500 |
| 3 | `POST` | `/api/detect/frame` | `file` — khung hình JPEG / PNG; `job_id` (tuỳ chọn, định danh phiên webcam) | Như endpoint 1, kèm `job_id` của phiên | **200** OK · 400 · 413 · 422 · 500 |
| 4 | `GET` | `/api/jobs/{job_id}` | `job_id` | `status`, `progress`, `total_frames`, `processed_frames`, `output_url`, `error_message` | **200** OK · 404 không tồn tại |
| 5 | `GET` | `/api/history` | `search`, `input_type`, `is_valid_format`, `date_from`, `date_to`, `min_confidence`, `job_id`, `sort_by`, `order`, `page`, `page_size` | `items`, `total`, `page`, `page_size`, `total_pages` | **200** OK · 422 tham số không hợp lệ |
| 6 | `GET` | `/api/history/{detection_id}` | `detection_id` (số nguyên ≥ 1) | Toàn bộ metadata của một bản ghi kèm URL ảnh gốc và ảnh biển số | **200** OK · 404 · 422 |
| 7 | `GET` | `/api/history/export` | Các tham số lọc như endpoint 5 — **không** phân trang | Luồng tệp CSV, UTF-8 **có BOM** (để Excel đọc đúng tiếng Việt) | **200** OK (`text/csv`) · 400 · 422 · 500 |
| 8 | `DELETE` | `/api/history/{detection_id}` | `detection_id` | Không có nội dung | **204** No Content · 404 · 422 |
| 9 | `GET` | `/api/statistics` | `days` (độ dài cửa sổ chuỗi thời gian) | Tổng số tác vụ, tổng số biển số, độ tin cậy trung bình, thời gian xử lý trung bình, phân bố theo loại đầu vào, chuỗi số liệu theo ngày | **200** OK · 422 |
| 10 | `GET` | `/health` | Không | Trạng thái tổng thể (`healthy` / `degraded` / `unhealthy`), trạng thái pipeline, trạng thái CSDL, tên pipeline đang dùng | **200** OK |

**Các quyết định thiết kế API.** *Mã 202 cho video*: `200` nghĩa là "đã xử lý xong", `202` nghĩa là "đã tiếp nhận, việc xử lý sẽ diễn ra sau" — với hàng trăm giây xử lý trên CPU, `202` đúng ngữ nghĩa và là cơ sở để client biết cần hỏi tiến độ. *Mã 200 với danh sách rỗng*: ảnh không chứa biển số trả `200` chứ không phải `404`, vì tài nguyên — kết quả nhận dạng của ảnh này — tồn tại và có giá trị là tập rỗng (NFR-R2). *Mã 204 cho xoá*: không có gì có ý nghĩa để trả về sau khi xoá. *Tìm kiếm khớp cả hai trường chuỗi*: `search` khớp đồng thời `plate_number` (đã chuẩn hoá) và `raw_ocr_text` (thô), vì nếu hậu xử lý đã sửa chuỗi thì người dùng nhớ chuỗi nào cũng phải tìm ra được bản ghi. *Chuỗi thời gian trả cả ngày không có dữ liệu*: ngày không phát sinh hoạt động vẫn trả giá trị không, vì bỏ qua thì biểu đồ sẽ **âm thầm nối liền các khoảng trống**, khiến một tuần không hoạt động trông giống một tuần hoạt động đều. *Trạng thái `degraded`*: hệ thống chạy được và CSDL kết nối tốt nhưng pipeline chưa nạp được trọng số thật (thiếu tệp mô hình, hoặc chạy `ALPR_USE_STUB=true`) nên kết quả không có giá trị thực — báo `healthy` khi đó sẽ gây hiểu lầm nghiêm trọng; hiện `/health` trả `healthy` vì mô hình chính thức đã nạp thành công.

**Trạng thái cài đặt.** Toàn bộ 10 endpoint **đã được cài đặt và xác minh bằng lời gọi HTTP thực tế**: hệ thống khởi động được, migration CSDL chạy xong, Swagger render đầy đủ, mỗi endpoint phản hồi đúng mã trạng thái mong đợi cho cả trường hợp thành công lẫn lỗi. Hệ thống hiện **vận hành pipeline nhận dạng thật** (`model_loaded: true`, engine `yolo:best.pt+paddleocr-PP-OCRv5-mobile`); `StubPipeline` đã ra khỏi đường chạy chính, phương án lùi là `UnavailablePipeline` — lớp này **ném lỗi thay vì sinh biển số giả**. Cần nói rõ phạm vi: việc xác minh này chứng minh **hợp đồng của API** hoạt động đúng, **không** chứng minh chất lượng nhận dạng. Mô hình đang chạy là `models/best.pt` (YOLO11n, `imgsz=640`, split v3); mô hình đối chứng `models/baseline-416-v1.pt` **không nằm trên đường chạy chính** và số liệu của nó không được dùng làm kết quả đánh giá, do hai khiếm khuyết đã biết (`imgsz=416` trong khi chỉ tiêu đặt ở 640; split v1 có rò rỉ train↔test khiến chỉ số bị thổi phồng). Đánh giá chất lượng nhận dạng thuộc **Chương 6**.

### 4.3.4. Các sơ đồ tuần tự

![](figures/fig-ch4-06.png)

**Hình 4.6.** Sơ đồ tuần tự — nhận dạng biển số từ ảnh tĩnh

**Nhận dạng từ ảnh (sơ đồ trên).** Điểm cần chú ý ở bước ghi CSDL: N bản ghi biển số đều mang cùng một `source_job_id`; lý do và hậu quả của việc thiếu trường này được phân tích tại mục 4.4.3(c).

![](figures/fig-ch4-07.png)

**Hình 4.7.** Sơ đồ tuần tự — nhận dạng video bất đồng bộ

**Nhận dạng video bất đồng bộ (sơ đồ trên).** Vòng lặp hỏi tiến độ ở phía giao diện chạy độc lập với vòng lặp xử lý ở tác vụ nền, hai bên chỉ giao tiếp gián tiếp qua bản ghi tác vụ trong CSDL. Việc kiểm tra cờ huỷ đặt bên trong vòng lặp xử lý để yêu cầu huỷ có hiệu lực trong vòng vài khung hình thay vì phải chờ hết video.

![](figures/fig-ch4-08.png)

**Hình 4.8.** Sơ đồ tuần tự — nhận dạng thời gian thực qua tầng API

**Nhận dạng thời gian thực qua webcam (sơ đồ trên).** Từ 2026-07-20 trang Webcam đã gỡ khỏi giao diện web — trang đó trước đây chính là client trong sơ đồ — nên sơ đồ nay mô tả **hợp đồng tương tác cho một client bất kỳ** gọi `POST /api/detect/frame`; phía máy chủ giữ nguyên. Ba chi tiết: **hàng đợi một khe nằm ở phía client** chứ không phải phía máy chủ, vì việc bỏ khung nên xảy ra trước khi khung được truyền qua mạng, và đây là ràng buộc client phải tự tuân thủ; `job_id` do máy chủ sinh ở lời gọi đầu tiên và được client ghi nhớ, nhờ đó toàn bộ phiên là một tác vụ duy nhất; gộp trùng diễn ra trong phạm vi phiên, nên giữ một biển số trước ống kính mười giây tạo ra một bản ghi chứ không phải hàng chục.

---

## 4.4. Thiết kế cơ sở dữ liệu

### 4.4.1. Sơ đồ thực thể — liên kết

![](figures/fig-ch4-09.png)

**Hình 4.9.** Sơ đồ thực thể — liên kết của cơ sở dữ liệu

Mô hình gồm hai thực thể quan hệ một–nhiều: **một lần sử dụng hệ thống** (một ảnh tải lên, một video, hoặc một phiên webcam) là một bản ghi `DetectionJob`; **mỗi biển số tìm thấy trong lần đó** là một bản ghi `DetectionHistory`. Số bản ghi con có thể bằng không (ảnh không có biển số nào), bằng một, hoặc nhiều. Lược đồ mở rộng đáng kể so với bản phác thảo ban đầu chỉ gồm 9 trường trong một bảng duy nhất; toàn bộ mở rộng đã được rà soát và phê duyệt, mục 4.4.3 lập luận cho những mở rộng đáng chú ý.

### 4.4.2. Mô tả chi tiết các bảng

#### a) Bảng `detection_job`

**Bảng 4.8.** Đặc tả trường của bảng `detection_job`

| Trường | Kiểu | Ràng buộc | Mô tả |
|---|---|---|---|
| `id` | `VARCHAR(36)` | PK | Định danh dạng UUID |
| `input_type` | `VARCHAR(16)` | NOT NULL, CHECK ∈ {image, video, webcam} | Loại đầu vào đã sinh ra tác vụ |
| `status` | `VARCHAR(16)` | NOT NULL, CHECK ∈ 5 giá trị trạng thái | Trạng thái vòng đời hiện tại |
| `progress` | `FLOAT` | NOT NULL, CHECK 0 ≤ x ≤ 1 | Tỉ lệ hoàn thành, dùng cho thanh tiến độ |
| `source_path`, `output_path` | `VARCHAR(512)` | NULL | Nơi lưu tệp đầu vào; nơi lưu ảnh hoặc video kết quả có gắn nhãn |
| `error_message` | `TEXT` | NULL | Nguyên nhân kỹ thuật khi thất bại; **chỉ dùng phía máy chủ**, không trả nguyên văn cho người dùng |
| `total_frames` / `processed_frames` | `INTEGER` | NULL / NOT NULL, mặc định 0 | Tổng số khung của video (`NULL` khi không áp dụng hoặc chưa biết); số khung đã xử lý |
| `created_at`, `completed_at` | `DATETIME` (UTC) | NOT NULL / NULL | Thời điểm tiếp nhận; thời điểm đạt trạng thái kết thúc |

Khoá chính là UUID chứ không phải số nguyên tự tăng vì định danh này được trả cho client và dùng trong tên tệp sinh ra: một số thứ tự đoán được sẽ cho phép một người dùng liệt kê tác vụ của người khác bằng cách thử các số liền kề. `error_message` không bao giờ trả nguyên văn vì nó có thể chứa đường dẫn hệ thống tệp, tên thư viện và thông tin phiên bản — vừa vi phạm FR-6.3 vừa là một dạng rò rỉ thông tin. Bảng có bốn chỉ mục (theo `input_type`, `status`, `created_at`) phục vụ truy vấn thống kê và danh sách hoạt động gần đây.

#### b) Bảng `detection_history`

**Bảng 4.9.** Đặc tả trường của bảng `detection_history`

| Trường | Kiểu | Ràng buộc | Mô tả |
|---|---|---|---|
| `id` | `INTEGER` | PK, tự tăng | Định danh bản ghi |
| `plate_number` | `VARCHAR(32)` | **NULL** | Chuỗi biển số **sau** chuẩn hoá, ví dụ `51F-12345` |
| `raw_ocr_text` | `VARCHAR(32)` | **NULL** | Chuỗi OCR **trước** chuẩn hoá, nguyên văn từ bộ nhận dạng |
| `confidence` | `FLOAT` | **NOT NULL**, CHECK 0 ≤ x ≤ 1 | Độ tin cậy của bộ **phát hiện** |
| `ocr_confidence` | `FLOAT` | **NULL**, CHECK NULL hoặc 0 ≤ x ≤ 1 | Độ tin cậy của bộ **nhận dạng ký tự** |
| `input_type` | `VARCHAR(16)` | NOT NULL, CHECK | Khử chuẩn hoá từ tác vụ cha, để lọc lịch sử không cần phép nối bảng |
| `image_path`, `plate_image_path` | `VARCHAR(512)` | NULL | Ảnh nguồn (hoặc khung hình đã trích với video); ảnh vùng biển số đã cắt |
| `bbox_x`, `bbox_y`, `bbox_w`, `bbox_h` | `INTEGER` | **NOT NULL**; `bbox_w`, `bbox_h` CHECK > 0 | Toạ độ góc trên trái theo pixel ảnh gốc và kích thước bounding box |
| `is_valid_format` | `BOOLEAN` | NOT NULL, mặc định `false` | Chuỗi đã chuẩn hoá có khớp một định dạng biển số Việt Nam hay không |
| `plate_line_count` | `INTEGER` | **NULL**, CHECK NULL hoặc ∈ {1, 2} | Số dòng của biển số |
| `processing_time` | `FLOAT` | NOT NULL, mặc định 0 | Thời gian xử lý riêng biển số này, tính bằng giây |
| `detected_time`, `created_at` | `DATETIME` (UTC) | NOT NULL | Thời điểm phát hiện; thời điểm ghi bản ghi |
| `source_job_id` | `VARCHAR(36)` | **NOT NULL**, FK → `detection_job.id`, ON DELETE CASCADE | Tác vụ đã sinh ra biển số này |

Bảng có năm chỉ mục, trong đó chỉ mục kết hợp `(input_type, detected_time)` phục vụ truy vấn mặc định của màn hình lịch sử — "mới nhất trước, có thể lọc theo loại đầu vào" — bằng một cấu trúc duy nhất đáp ứng đồng thời cả điều kiện lọc lẫn thứ tự sắp xếp; đây là yếu tố quyết định để NFR-P6 còn giữ được ở quy mô hàng trăm nghìn bản ghi.

**Xử lý múi giờ.** Mọi cột thời gian lưu ở UTC qua một kiểu tuỳ biến, vì SQLite không có kiểu thời gian gốc: giá trị lưu dưới dạng chuỗi định dạng, và định dạng đó **làm mất phần chênh lệch múi giờ** — `2026-07-19 12:00:00+00:00` ghi vào sẽ đọc ra thành `2026-07-19 12:00:00`, không báo lỗi, không cảnh báo. Hậu quả có hai mặt và đều không tự bộc lộ: phép trừ hai mốc thời gian sẽ ném ngoại lệ ở một thời điểm nào đó trong tương lai; và khi tuần tự hoá sang JSON, mốc không có hậu tố múi giờ sẽ được trình duyệt hiểu là **giờ địa phương** — trên máy múi giờ UTC+7, mọi mốc thời gian trong bảng lịch sử hiển thị lệch bảy giờ, đủ hợp lý để không ai để ý và đủ sai để làm hỏng mọi phân tích theo thời gian.

### 4.4.3. Các quyết định thiết kế dữ liệu đáng chú ý

Năm quyết định dưới đây đều xuất phát từ một yêu cầu đo lường hoặc một tình huống sai lệch cụ thể, và nếu bỏ qua thì hậu quả là **một con số sai mà không có gì báo hiệu**.

#### a) Vì sao tách `confidence` và `ocr_confidence` thành hai cột

Hệ thống ALPR hai giai đoạn tạo ra **hai đại lượng khác nhau về bản chất**: độ tin cậy phát hiện trả lời *"vùng ảnh này có phải biển số không?"*, độ tin cậy nhận dạng trả lời *"chuỗi ký tự đọc được từ vùng này có đúng không?"*. Bản phác thảo ban đầu chỉ có một cột `confidence`; gộp như vậy buộc phải chọn một trong hai hoặc ghép bằng công thức tuỳ tiện, và cả ba lựa chọn đều dẫn tới cùng kết cục: **không phân tích lỗi được nữa**. Bốn tổ hợp cho bốn chẩn đoán: cao–cao là lý tưởng; **cao–thấp** là định vị đúng nhưng đọc kém (biển mờ, nghiêng, hoặc hai dòng) ⇒ cải thiện tiền xử lý vùng cắt hoặc thuật toán tách dòng; **thấp–cao** là bộ phát hiện thiếu tự tin nhưng vùng cắt vẫn đọc được ⇒ cân nhắc hạ ngưỡng, huấn luyện thêm; **thấp–thấp** có thể là dương tính giả ⇒ kiểm tra chất lượng nhãn, tăng cường dữ liệu âm. Bảng chẩn đoán này **chỉ tồn tại khi hai đại lượng được lưu tách biệt**. Một lý do phụ: bộ lọc `min_confidence` của endpoint lịch sử lọc theo độ tin cậy **phát hiện** ("chỉ hiện những vùng chắc chắn là biển số") — với một cột gộp thì ngữ nghĩa bộ lọc không thể phát biểu rõ ràng.

#### b) Vì sao lưu cả `raw_ocr_text` lẫn `plate_number`

Đây là quyết định có giá trị học thuật cao nhất trong lược đồ. Khối hậu xử lý sửa các nhầm lẫn ký tự kinh điển dựa trên cấu trúc biển số Việt Nam rồi kiểm tra hợp lệ — ví dụ chuỗi thô `51A-I234O` được sửa thành `51A-12340` vì vị trí thứ tư trở đi chỉ được phép là chữ số. Các ánh xạ này là **một chiều và phụ thuộc vị trí**, không phải cặp hoán đổi hai chiều — như đã lập luận ở mục 1.6.3: với cặp `O` và `0`, ánh xạ đúng là `O → 0` tại vị trí chữ số và `0 → D` tại vị trí chữ cái, còn `0 → O` **không bao giờ hợp lệ** vì `O` không thuộc tập chữ cái sê-ri của biển số Việt Nam; chữ `R` **tuyệt đối không được ánh xạ đi** vì nó hợp lệ ở vị trí chữ cái thứ hai của sê-ri biển xe mô tô (mục 2.2.4). Trình bày các cặp này bằng ký hiệu hai chiều là một cách viết tắt sai, dẫn thẳng tới một cài đặt sai.

Câu hỏi tất yếu từ hội đồng là **khối hậu xử lý đó đóng góp bao nhiêu?** Nếu chỉ lưu chuỗi đã sửa, câu trả lời duy nhất là định tính — "chúng em có thêm bước sửa lỗi bằng regex" — không kiểm chứng được. Khi lưu cả hai chuỗi, câu trả lời thành định lượng: tỉ lệ `raw_ocr_text` khớp tuyệt đối nhãn đúng chính là **NFR-A5**, tỉ lệ `plate_number` khớp tuyệt đối nhãn đúng chính là **NFR-A6**, và **hiệu số giữa hai tỉ lệ là đóng góp định lượng của khối hậu xử lý**. Phép đo còn tách được các can thiệp thành **sửa đúng** (chuỗi thô sai, chuỗi sửa đúng) và **sửa hỏng** (chuỗi thô đúng, chuỗi sửa sai) — loại thứ hai đáng quan tâm vì một luật quá mạnh tay có thể sửa hỏng chuỗi vốn đã đúng, hiện tượng bị che khuất hoàn toàn nếu chỉ nhìn con số độ chính xác tổng thể. Chi phí là vài chục byte mỗi bản ghi; nếu chỉ lưu chuỗi đã sửa thì bằng chứng bị **xoá âm thầm ngay tại thời điểm ghi dữ liệu**, không cách nào khôi phục ngoài việc chạy lại toàn bộ thực nghiệm.

#### c) Vì sao cần `source_job_id`

Giả định A-02 đã ghi nhận: **một ảnh có thể chứa nhiều biển số** — với mật độ xe máy ở Việt Nam, đây là trường hợp thông thường chứ không phải ngoại lệ. Lược đồ ban đầu là một bảng lịch sử phẳng không có khoá nhóm, nên sai lệch phát sinh ngay ở thống kê (FR-4.1): chỉ số "tổng số lượt nhận dạng" đo **mức độ sử dụng hệ thống**, nhưng không có khoá nhóm thì cách duy nhất để tính là đếm số dòng bảng lịch sử — **một ảnh ba biển số bị đếm thành ba lượt sử dụng**. Với ảnh giao thông trung bình chứa 2–3 biển số, chỉ số bị nhân lên 2–3 lần; với video còn nặng hơn vì một video có thể sinh hàng chục biển số sau khi gộp trùng. Nguy hiểm nhất là lỗi này **không tự bộc lộ**: không ngoại lệ, không log, không giá trị vô lý — đáp ứng của `GET /api/statistics` vẫn mang những con số trông hợp lý, chỉ có điều chúng sai theo hướng có lợi cho ấn tượng ban đầu. Lập luận này **không mất hiệu lực** khi trang Tổng quan bị gỡ ngày 2026-07-20: phép tính vẫn ở `StatisticsService` và vẫn phục vụ qua API, nên khoá nhóm sai vẫn cho con số sai — chỉ là sai trong JSON thay vì sai trên màn hình.

Với `source_job_id`, ba câu hỏi thống kê tách bạch: số lần hệ thống được sử dụng đếm bằng bản ghi `detection_job`; số biển số đã đọc đếm bằng bản ghi `detection_history`; trung bình mỗi lần dùng đọc được mấy biển là tỉ số giữa hai con số — với lược đồ ban đầu cả ba cho cùng một câu trả lời và câu trả lời đó chỉ đúng cho một trong ba. Khoá nhóm còn phục vụ bộ lọc `job_id` của endpoint lịch sử và ràng buộc khoá ngoại với xoá lan truyền. Cột đặt là **bắt buộc** vì một bản ghi không thuộc tác vụ nào sẽ vô hình với thống kê tính theo tác vụ nhưng vẫn xuất hiện trong bảng lịch sử — đặt bắt buộc chuyển mâu thuẫn tiềm ẩn đó thành một lỗi ồn ào ngay lúc chèn dữ liệu.

#### d) Vì sao `plate_line_count` là trường bắt buộc về mặt nghiệp vụ

**Vai trò thứ nhất: báo cáo độ chính xác tách theo bố cục.** NFR-A8 yêu cầu báo cáo riêng cho biển một dòng và hai dòng, căn cứ là số liệu 94,3% so với 45,7% **đo trên bộ RodoSol-ALPR (Brazil)** đã dẫn ở 4.1.1 [7]<!-- laroca_2022_crossdataset -->. Nếu tập kiểm thử có 70% biển một dòng và mô hình đạt 95% trên nhóm đó nhưng chỉ 50% trên nhóm hai dòng, con số tổng thể là 81,5% — trông chấp nhận được nhưng che lấp hoàn toàn việc hệ thống hoạt động rất kém trên nhóm phương tiện chiếm đa số ở Việt Nam.

**Vai trò thứ hai: khử nhập nhằng trong chính khối hậu xử lý.** Chuỗi tám ký tự `29B11234` sau khi bỏ dấu gạch nối có thể phân giải thành `29` + `B` + `11234` (mã tỉnh, **một** chữ cái sê-ri, **năm** chữ số) ⇒ biển ô tô một dòng, hiển thị `29B-112.34`; hoặc thành `29` + `B1` + `1234` (mã tỉnh, sê-ri **một chữ cái kèm một chữ số**, **bốn** chữ số) ⇒ biển xe máy kiểu cũ hai dòng, hiển thị `29-B1 1234`. Chỉ nhìn chuỗi ký tự thì **không có cách nào phân biệt hai trường hợp** — đây chính là nhập nhằng cấu trúc đã nêu ở mục 2.2.2(c): dạng *hai chữ số – một chữ cái – năm chữ số* khớp **đồng thời** cả biển ô tô lẫn biển xe máy kiểu cũ (sê-ri gồm một chữ cái kèm một chữ số, cấp trước 15/8/2023 và vẫn lưu hành hợp pháp), trong khi cách chèn dấu phân cách lại khác nhau. Ràng buộc về tập chữ cái sê-ri **không** gỡ được nhập nhằng này: theo mục 2.2.4, hai tập 20 chữ cái là ràng buộc **theo vị trí trong sê-ri** — chữ ở **vị trí thứ nhất** thuộc tập có `G` và không có `R`, chữ ở **vị trí thứ hai của sê-ri biển xe mô tô** thuộc tập có `R` và không có `G` — mà cả hai cách phân giải trên đều đặt `B` ở vị trí thứ nhất. Thông tin số dòng đến từ nguồn khác hẳn: **hình học của bounding box**, cụ thể là tỉ lệ khung đối chiếu kích thước chuẩn theo QCVN 08:2024/BCA [11]<!-- bocongan_2024_qcvn08 --> (4,727 cho biển ô tô một dòng; 2,000 cho biển ô tô hai dòng; 1,357 cho biển xe máy) — thông tin mà bộ OCR không có và không thể suy ra từ chuỗi nó xuất ra. Vì vậy `plate_line_count` là **đầu vào cần thiết để khối hậu xử lý chọn đúng luật kiểm tra và đúng cách định dạng chuỗi kết quả**. Cột cho phép giá trị rỗng vì lý do ở mục (e), nhưng ràng buộc kiểm tra bảo đảm giá trị chỉ được là 1 hoặc 2; về nghiệp vụ, mọi bản ghi có kết quả OCR đều phải có giá trị này.

#### e) Vì sao các cột liên quan tới OCR đều cho phép giá trị rỗng

Bốn cột `plate_number`, `raw_ocr_text`, `ocr_confidence`, `plate_line_count` cho phép giá trị rỗng, trong khi bốn cột toạ độ bounding box và cột `confidence` của bộ phát hiện **bắt buộc phải có giá trị**. Sự bất đối xứng này tuân theo một quy tắc duy nhất:

> **Một biển số phát hiện được vẫn đáng lưu, kể cả khi bộ OCR không đọc ra ký tự nào.**

Đầu ra của bộ phát hiện luôn tồn tại với mọi bản ghi, vì chính sự tồn tại của bản ghi bắt nguồn từ việc bộ phát hiện đã tìm thấy một vùng; ngược lại, mọi cột dẫn xuất từ OCR đều có thể vắng mặt, vì một biển **được định vị nhưng không đọc được** là kết quả có thật và xảy ra thường xuyên: biển ở xa nên độ phân giải vùng cắt quá thấp, biển bụi bẩn hoặc bị che một phần, ảnh ngược sáng, biển nghiêng quá mức làm hỏng bước hiệu chỉnh hình học, ảnh ban đêm nhiễu nặng.

**Vì sao vứt bỏ các bản ghi này là sai.** Độ chính xác nhận dạng là tỉ lệ giữa số biển đọc đúng và tổng số biển cần đọc; nếu các trường hợp không đọc được bị loại khỏi CSDL thì chúng cũng biến mất khỏi mẫu số, và hệ thống chỉ được đánh giá trên **chính những trường hợp nó đã xử lý thành công** — một dạng thiên lệch chọn mẫu (selection bias) làm chỉ số **đẹp lên một cách giả tạo**. Ví dụ số cụ thể: bộ phát hiện tìm thấy 100 biển số, bộ OCR đọc ra chuỗi cho 80 biển trong đó 76 chuỗi đúng, 20 biển còn lại không đọc ra ký tự nào. Giữ mọi bản ghi cho 76 / 100 = **76,0%**, phản ánh đúng năng lực toàn trình; vứt bỏ cho 76 / 80 = **95,0%**, sai lệch 19 điểm phần trăm. Con số 95% không sai về số học — nó đúng cho một câu hỏi khác (*"khi bộ OCR đọc được, nó đọc đúng bao nhiêu phần trăm?"*) — nhưng câu hỏi thực sự là xác suất hệ thống trả về biển số đúng khi đưa một ảnh vào, và câu trả lời 76% chỉ tính được nếu 20 trường hợp thất bại vẫn nằm trong CSDL. Lỗi này đặc biệt nguy hiểm vì nó **thiên vị theo một chiều duy nhất và luôn theo hướng có lợi**, nên ít có khả năng bị nghi ngờ và soát lại. Kết hợp với việc tách hai cột độ tin cậy (mục a), các bản ghi có `confidence` cao nhưng `plate_number` rỗng còn tạo thành tập mẫu giá trị nhất để phân tích lỗi ở Chương 6: những vùng mà bộ phát hiện chắc chắn là biển số nhưng bộ OCR bó tay.

---

## 4.5. Thiết kế giao diện người dùng

### 4.5.1. Sơ đồ điều hướng

![](figures/fig-ch4-10.png)

**Hình 4.10.** Sơ đồ điều hướng giữa ba màn hình của giao diện

Giao diện là ứng dụng một trang (SPA) với **ba màn hình** chính chia sẻ chung một khung bố cục gồm thanh điều hướng và vùng nội dung. Cấu trúc điều hướng cố ý giữ **phẳng**: ba màn hình đều truy cập trực tiếp từ thanh điều hướng; chi tiết một bản ghi và xác nhận xoá là hộp thoại chồng lên trang lịch sử thay vì trang riêng, để người dùng không mất ngữ cảnh danh sách và bộ lọc đang áp dụng. Mọi đường dẫn không khớp đều chuyển hướng về trang chủ (Nhận dạng ảnh) thay vì hiển thị trang lỗi.

> **Ghi chú thay đổi phạm vi 2026-07-20 — hai đợt liên tiếp trong cùng một ngày.** Thiết kế ban đầu có **năm màn hình** và Dashboard là trang chủ. Đợt thứ nhất gỡ màn hình Webcam (`/webcam`) và chuyển trang chủ sang **Nhận dạng ảnh**; đợt thứ hai gỡ tiếp màn hình **Tổng quan / Dashboard** (`/dashboard`). Cả hai đợt đều nhằm thu gọn phạm vi demo và đều **không** gỡ năng lực nào ở tầng dưới: `POST /api/detect/frame`, `GET /api/statistics` và `GET /health` vẫn phục vụ và vẫn có kiểm thử tích hợp. Hệ quả: FR-3.1/FR-3.4 chuyển M → W ở đợt 1, **FR-4.1 chuyển M → W** và FR-4.2 chuyển S → W ở đợt 2 — xem khung ghi chú ở mục 4.1.3(a) về việc đây là yêu cầu mức Must đầu tiên bị đưa ra khỏi phạm vi. Mã giao diện của cả hai màn hình còn nguyên trong lịch sử git.

### 4.5.2. Mô tả các màn hình chính

**Màn hình Tổng quan / Dashboard (đã gỡ khỏi giao diện 2026-07-20).** Thiết kế ban đầu đặt màn hình này tại `/dashboard` gồm hàng thẻ chỉ số tổng hợp (tổng lượt sử dụng đếm theo tác vụ, tổng số biển đã đọc đếm theo bản ghi lịch sử, độ tin cậy trung bình, thời gian xử lý trung bình — FR-4.1), biểu đồ xu hướng theo ngày (FR-4.2), biểu đồ phân bố theo loại đầu vào, danh sách hoạt động gần đây và thẻ trạng thái hệ thống. Màn hình đã bị gỡ cùng đợt với việc chuyển **FR-4.1 từ Must sang Won't** và FR-4.2 từ Should sang Won't (mục 4.1.3a); số liệu vẫn truy vấn được qua `GET /api/statistics` và `GET /health`, hai endpoint vẫn có kiểm thử tích hợp. Hai lập luận thiết kế của nó vẫn còn hiệu lực vì chúng ràng buộc chính đáp ứng của API: **hai con số "lượt sử dụng" và "số biển đã đọc" phải tính từ hai bảng khác nhau** đúng theo 4.4.3(c); và **trạng thái `degraded` phải hiển thị rõ** để pipeline mô phỏng không bị nhầm với vận hành thật, ràng buộc nay nằm ở trường `status` của `GET /health`.

**Màn hình nhận dạng ảnh** là trang chủ (`/`), phản ánh vai trò nghiệp vụ trung tâm của luồng nhận dạng ảnh. Bố cục hai cột: cột trái là khu vực tải ảnh hỗ trợ kéo–thả kèm ảnh xem trước; cột phải hiển thị ảnh đã vẽ bounding box, danh sách thẻ kết quả và phần tóm tắt gồm số biển phát hiện được, số biển đọc được và thời gian xử lý. Mỗi thẻ hiển thị chuỗi biển số đã chuẩn hoá ở kích thước lớn, chuỗi OCR thô nhỏ hơn khi hai chuỗi khác nhau, hai thanh độ tin cậy riêng cho phát hiện và OCR, nhãn số dòng và cờ hợp lệ định dạng. Hiển thị **cả hai chuỗi** khi chúng khác nhau cho phép quan sát trực tiếp khối hậu xử lý đã can thiệp gì, và khi bảo vệ đây là bằng chứng trực quan cho đóng góp kỹ thuật ở mục 4.4.3(b).

**Màn hình nhận dạng video** gồm ba giai đoạn nối tiếp đúng bản chất bất đồng bộ: khu vực tải tệp; bảng tiến độ với thanh phần trăm, số khung đã xử lý trên tổng số khung, trạng thái tác vụ và nút huỷ; bảng kết quả với video đã gắn nhãn, danh sách biển số đã gộp trùng và liên kết tải về.

**Màn hình webcam (đã gỡ khỏi giao diện 2026-07-20)** gồm khu vực hiển thị camera với lớp phủ bounding box thời gian thực, cụm điều khiển bật/tắt camera và chọn thiết bị, bảng số liệu phiên (tốc độ khung hình hiệu dụng, số khung đã gửi, số khung bị bỏ, độ trễ trung bình) và bảng biển số đã phát hiện trong phiên. Bảng số liệu phiên có vai trò kép: với người dùng, nó cho biết hệ thống chạy nhanh chậm ra sao; với người thực hiện đồ án, nó là công cụ đo tại chỗ cho NFR-P2 — việc số khung bị bỏ được hiển thị công khai giúp phân biệt "hệ thống xử lý được 5 khung mỗi giây" với "camera chụp 30 khung mỗi giây nhưng 25 khung bị bỏ". Sau khi màn hình bị gỡ, năng lực thời gian thực giữ nguyên ở tầng API (`POST /api/detect/frame`, mục 4.3.3) và phép đo NFR-P2 chuyển sang kịch bản gọi API trực tiếp.

**Màn hình lịch sử** gồm bảng dữ liệu có phân trang và sắp xếp theo cột, thanh bộ lọc (tìm kiếm, loại đầu vào, khoảng thời gian, ngưỡng độ tin cậy, trạng thái hợp lệ định dạng), nút xuất dữ liệu, hộp thoại chi tiết và hộp thoại xác nhận xoá. Hộp thoại chi tiết hiển thị đầy đủ metadata: ảnh gốc có vẽ bounding box, ảnh biển số đã cắt, cả hai chuỗi thô và đã chuẩn hoá, cả hai độ tin cậy, số dòng, thời gian xử lý và định danh tác vụ nguồn — việc vẽ lại bounding box mà không cần chạy lại mô hình là nhờ bốn cột toạ độ lưu trong CSDL.

### 4.5.3. Nguyên tắc trải nghiệm người dùng

**Bốn trạng thái bắt buộc của mọi thành phần hiển thị dữ liệu**, không ngoại lệ. (1) *Đang tải* — chỉ báo trực quan cho mọi thao tác trên 500 ms; bỏ qua thì giao diện trông như treo, người dùng bấm lại nhiều lần và tạo thêm tải cho một hệ thống vốn đã chậm vì chạy CPU. (2) *Có dữ liệu* — nội dung thực tế. (3) *Rỗng* — thông báo giải thích vì sao chưa có gì kèm gợi ý hành động; bỏ qua thì màn hình trắng không phân biệt được với lỗi kỹ thuật. (4) *Lỗi* — thông báo tiếng Việt nêu nguyên nhân và cách khắc phục kèm khả năng thử lại; bỏ qua thì người dùng bế tắc.

Trạng thái rỗng thường bị bỏ sót nhất và ở hệ thống này nó xuất hiện với ba ý nghĩa khác nhau, cần ba thông điệp khác nhau: bảng lịch sử khi chưa có lượt nhận dạng nào ("chưa có dữ liệu, hãy thử nhận dạng một ảnh"), bảng lịch sử khi bộ lọc không khớp bản ghi nào ("không có bản ghi nào khớp bộ lọc, hãy nới lỏng điều kiện"), và kết quả nhận dạng khi ảnh không chứa biển số ("không phát hiện được biển số trong ảnh này"). *(Trường hợp thứ nhất trước 2026-07-20 xuất hiện trên màn hình Tổng quan; sau khi màn hình này được gỡ, nó biểu hiện ở bảng lịch sử rỗng.)* Trường hợp thứ ba là biểu hiện ở tầng giao diện của cùng quyết định đã xuất hiện ở tầng API (mã 200 với danh sách rỗng) và ở tầng pipeline (trả kết quả rỗng, không ném ngoại lệ) — ba tầng nhất quán về ngữ nghĩa: **không tìm thấy không phải là lỗi**.

**Thông báo lỗi tiếng Việt thân thiện.** NFR-U3 quy định thông báo phải bằng tiếng Việt, nêu rõ nguyên nhân và cách khắc phục, không hiển thị mã lỗi kỹ thuật; FR-6.3 bổ sung rằng stack trace tuyệt đối không được rò rỉ ra giao diện. Nguyên tắc soạn gồm ba phần — **chuyện gì đã xảy ra**, **vì sao**, **người dùng có thể làm gì** — và một thông báo thiếu phần thứ ba là một thông báo bỏ mặc người dùng. Năm tình huống điển hình được soạn lại thay cho thông báo kém tương ứng: `400 Bad Request` → "Tệp bạn chọn không phải là ảnh hợp lệ. Hệ thống chỉ nhận các định dạng JPG, PNG, WebP và BMP. Vui lòng chọn tệp khác."; `413 Payload Too Large` → "Ảnh vượt quá dung lượng cho phép. Vui lòng chọn ảnh nhỏ hơn hoặc giảm kích thước ảnh trước khi tải lên."; "Lỗi: không có kết quả" → "Không tìm thấy biển số nào trong ảnh này. Hãy thử ảnh chụp gần hơn hoặc rõ nét hơn."; `NetworkError: Failed to fetch` → "Không kết nối được tới máy chủ. Vui lòng kiểm tra máy chủ đã khởi động chưa, sau đó bấm Thử lại."; toàn bộ stack trace Python → "Đã xảy ra lỗi trong quá trình xử lý. Vui lòng thử lại. Nếu lỗi tiếp diễn, hãy liên hệ quản trị viên." Nguyên tắc vận hành đi kèm: **chi tiết kỹ thuật không bị vứt bỏ mà được chuyển hướng** — loại ngoại lệ, stack trace và định danh yêu cầu được ghi vào log có cấu trúc ở phía máy chủ theo FR-6.2.

**Các nguyên tắc khác.** Theo NFR-U1, người dùng mới phải hoàn thành lượt nhận dạng ảnh đầu tiên trong không quá ba thao tác nhấp chuột và không cần đọc tài liệu — điều này định hình bố cục: khu vực tải ảnh ở vị trí trung tâm, hỗ trợ kéo–thả, không có bước cấu hình bắt buộc nào. Toàn bộ chữ chính đạt tương phản tối thiểu 4,5:1 theo WCAG AA (NFR-U5), và độ tin cậy được biểu diễn bằng thanh trực quan kèm giá trị số chứ không chỉ bằng màu. Giao diện hoạt động đúng từ độ phân giải 1366×768 trở lên (NFR-U4) — độ phân giải phổ biến của máy chiếu trong phòng bảo vệ.

**Trạng thái cài đặt.** Phần giao diện **đã hoàn thành**: cấu trúc điều hướng, khung bố cục và toàn bộ thành phần của **ba màn hình hiện hành** đã cài đặt, bản build production chạy sạch. Hai màn hình Webcam và Tổng quan từng được cài đặt đầy đủ và đã gỡ ngày 2026-07-20; ba endpoint tương ứng (`POST /api/detect/frame`, `GET /api/statistics`, `GET /health`) nay phục vụ client API. Chi tiết cài đặt và ảnh chụp màn hình ở **Chương 5**; các hạng mục còn dở (đáng chú ý là nút huỷ tác vụ video) được ghi nhận ở mục 5.9.

---

## 4.6. Kết luận chương

Về **phân tích yêu cầu**, đồ án xác định ba tác nhân tương tác trực tiếp và chín use case, đặc tả 34 yêu cầu chức năng trong 6 nhóm (**21 bắt buộc, 6 nên có, 3 có thì tốt, 4 không triển khai ở bản này**), mỗi yêu cầu kèm một tiêu chí chấp nhận kiểm chứng được. Bốn yêu cầu mức Won't đều thuần giao diện và đều chuyển mức trong hai đợt thu gọn phạm vi ngày 2026-07-20 — FR-3.1/FR-3.4 khi gỡ trang Webcam, FR-4.1/FR-4.2 khi gỡ trang Tổng quan — trong đó **FR-4.1 là yêu cầu mức Must đầu tiên bị đưa ra khỏi phạm vi**, được ghi thẳng ở mục 4.1.3(a) và đánh giá là hạn chế thật ở Chương 7; cả bốn đều mất màn hình hiển thị chứ không mất năng lực. Yêu cầu phi chức năng đặt ở dạng chỉ tiêu định lượng, với điểm cần nhấn mạnh là **mọi chỉ tiêu hiệu năng đều là chỉ tiêu đo trên CPU**: việc không có GPU là ràng buộc thiết kế nghiêm túc chứ không phải hạn chế tạm thời, vì nó cố định trong toàn bộ vòng đời đồ án, thay đổi độ trễ theo bậc độ lớn chứ không theo tỉ lệ phần trăm, chi phối lựa chọn thành phần ở mọi tầng, và trực tiếp sinh ra hai quyết định kiến trúc — video bất đồng bộ và bỏ khung có kiểm soát ở chế độ webcam.

Về **kiến trúc**, hệ thống gồm năm tầng theo nguyên tắc phụ thuộc một chiều, và quyết định quan trọng nhất là **tách hoàn toàn tầng AI khỏi tầng API**: package nhận dạng không import bất kỳ thành phần nào của framework web. Ba lợi ích — kiểm thử độc lập, tái sử dụng trong script huấn luyện và đánh giá, thay engine mà không sửa tầng API — đã dùng trong thực tế: nhờ nó, toàn bộ phần mềm đã được xây dựng và chạy được với pipeline mô phỏng trước khi mô hình được huấn luyện. Ràng buộc được kiểm chứng bằng hai công cụ bổ trợ: kiểm tra tĩnh các câu lệnh import và kiểm tra động danh sách module đã nạp lúc chạy — phép thứ hai bắt được cả import muộn lẫn import bắc cầu mà phép thứ nhất bỏ sót.

Về **thiết kế chi tiết**, chương đặc tả tầng AI với ba lớp trừu tượng và tập kiểu dữ liệu bất biến, bốn service của tầng nghiệp vụ, mười endpoint REST kèm đầy đủ đầu vào, đầu ra, mã trạng thái, cùng ba sơ đồ tuần tự. Về **cơ sở dữ liệu**, mô hình gồm hai bảng quan hệ một–nhiều; năm quyết định thiết kế dữ liệu đều bảo vệ **tính đúng đắn của các số liệu sẽ công bố ở chương đánh giá**: tách hai cột độ tin cậy để phân tích lỗi được; lưu cả chuỗi OCR thô lẫn chuỗi đã sửa để đo được đóng góp định lượng của khối hậu xử lý; thêm khoá nhóm tác vụ để thống kê sử dụng không bị thổi phồng theo số biển số trên mỗi ảnh; lưu số dòng của biển vì chuỗi ký tự tự nó nhập nhằng giữa biển ô tô và biển xe máy; cho phép các cột OCR rỗng để những trường hợp đọc không ra vẫn nằm trong mẫu số khi tính độ chính xác. Mỗi quyết định, nếu bỏ qua, đều dẫn tới một con số sai mà **không có gì báo hiệu**. Về **giao diện**, chương trình bày sơ đồ điều hướng phẳng gồm **ba màn hình** (sau hai đợt thu gọn phạm vi ngày 2026-07-20) và hai nguyên tắc trải nghiệm bắt buộc: bốn trạng thái phải xử lý cho mọi thành phần hiển thị dữ liệu, và quy tắc soạn thông báo lỗi tiếng Việt gồm ba phần nguyên nhân — giải thích — hướng khắc phục.

Cần nói rõ giới hạn của chương: nội dung ở đây là **thiết kế và trạng thái cài đặt của thiết kế**, không phải kết quả thực nghiệm. Hệ thống **đã chạy pipeline nhận dạng thật với mô hình chính thức** `models/best.pt`, còn mô hình đối chứng `models/baseline-416-v1.pt` không dùng làm kết quả đánh giá được (sai độ phân giải và split có rò rỉ). Toàn bộ số liệu về độ chính xác của mô hình, độ trễ thực đo trên CPU, mức đóng góp thực tế của khối hậu xử lý và độ chính xác tách theo số dòng biển số **được trình bày ở Chương 6**. Chương tiếp theo trình bày quá trình cài đặt hệ thống trên cơ sở thiết kế đã xác lập ở đây.
