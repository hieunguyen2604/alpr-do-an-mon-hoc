# CHƯƠNG 3. KHẢO SÁT CÔNG NGHỆ VÀ LỰA CHỌN MÔ HÌNH

## 3.1. Phương pháp khảo sát và tiêu chí lựa chọn

Chương này trình bày luận cứ cho từng lựa chọn công nghệ của đồ án. Mỗi lựa chọn được trình bày theo cùng một khuôn: các phương án đã xét, tiêu chí đánh giá, kết luận, và **đánh đổi phải chấp nhận**. Nguyên tắc xuyên suốt là theo dữ liệu chứ không hợp thức hoá một lựa chọn có sẵn: khi bằng chứng không đủ để phân định, mục này nói rõ là không đủ, thay vì tạo ra vẻ chắc chắn giả tạo.

### 3.1.1. Bốn ràng buộc chi phối mọi lựa chọn

Không lựa chọn nào trong chương này được cân nhắc trên một bảng cân bằng trung lập. Bốn ràng buộc dưới đây đã thu hẹp không gian phương án **trước khi** việc so sánh bắt đầu, nên phải nêu trước để người đọc hiểu vì sao một số ứng viên mạnh lại bị loại sớm.

| # | Ràng buộc | Hệ quả trực tiếp lên việc chọn |
|:--:|---|---|
| 1 | **Suy luận trên CPU, không có GPU CUDA** (CON-02, xem mục 5.1.2) | Mọi phương án không công bố số liệu tốc độ CPU đều **không có căn cứ để đánh giá**; các mô hình hàng trăm triệu tham số bị loại từ đầu |
| 2 | **Biển số Việt Nam có biển hai dòng** | Engine nào giả định văn bản một dòng đều gãy ở đây; đây là tiêu chí phân loại chứ không phải điểm cộng |
| 3 | **Phải đóng gói và bàn giao được** | Giấy phép, dung lượng mô hình và số lượng phụ thuộc là tiêu chí thật, không phải chi tiết phụ |
| 4 | **Ngân sách thời gian CPU hữu hạn** | Một số phép so sánh đã được thiết kế nhưng **không chạy được**; mục 3.1.2 nói rõ là những phép nào |

### 3.1.2. Ranh giới giữa cái đã đo và cái mới chỉ khảo sát tài liệu

Đây là mục quan trọng nhất của chương, và nó được đặt ngay đầu chương một cách có chủ ý.

Một chương mang tên *"khảo sát và lựa chọn"* rất dễ tạo ấn tượng rằng mọi lựa chọn đều đã qua thực nghiệm. Với đồ án này thì **không**. Có phép so sánh đồ án tự chạy trên chính máy và chính dữ liệu của mình; có phép so sánh chỉ dựa vào số liệu do nhà phát hành công bố; và có phép so sánh **chưa bao giờ chạy được**. Ba mức bằng chứng ấy không tương đương nhau, nên chúng được phân biệt tường minh:

**Bảng 3.1.** Mức bằng chứng của từng phép so sánh trong chương

| Phép so sánh | Mức bằng chứng | Trình bày ở |
|---|---|:---:|
| PP-OCRv5_mobile ↔ PP-OCRv6_medium | ✅ **Tự đo** — 200 vùng cắt biển số của đồ án, cùng máy, cùng thứ tự ảnh | 3.3.2 |
| Bộ nhận dạng gốc ↔ bản tinh chỉnh | ✅ **Tự đo** — 2.801 biển có nhãn chuỗi, bốn cấu hình | 5.4 |
| YOLO11n ↔ YOLOv8n và năm thế hệ YOLO khác | 📄 **Khảo sát tài liệu** — dựa trên bảng benchmark chính thức của nhà phát hành, đồ án **không tự chạy lại** | 3.2 |
| PaddleOCR ↔ EasyOCR ↔ Tesseract | ❌ **Chưa đo lần nào** — chỉ đối chiếu kiến trúc, dung lượng và thông số công bố | 3.3.1 |
| PyTorch ↔ ONNX Runtime ↔ OpenVINO | ❌ **Chưa đo** — chọn theo benchmark của bên thứ ba; bảng {{T6.6c}} còn để trống | 3.4 · 6.6.3 |
| Độ phân giải 416 ↔ 640 | ⚠️ **Có số đo nhưng không quy kết được** — ba biến đổi đồng thời và ngược chiều nhau | 3.6 |

Hai dòng ❌ là hai khoản nợ thực sự của đồ án, và chúng được ghi nhận nhất quán ở mục 6.9.2 cùng Chương 7 chứ không chỉ ở đây. Ý nghĩa của chúng khác nhau:

- **Benchmark engine OCR chưa chạy** ⇒ phát biểu được phép nói là *"PaddleOCR được chọn vì nhẹ hơn, có lộ trình tăng tốc và có bằng chứng tinh chỉnh"*, **không** được phép nói *"PaddleOCR chính xác hơn EasyOCR"*. Trên thực tế, các so sánh công khai mà đồ án kiểm chứng được lại nghiêng về EasyOCR (mục 3.3.1).
- **So sánh runtime chưa chạy** ⇒ quyết định chọn ONNX Runtime đứng vững chủ yếu nhờ **lý do vận hành** (một runtime duy nhất cho cả hai mô hình, tránh xung đột hai framework học sâu), chứ không nhờ số liệu tốc độ tự đo.

Cách trình bày này khiến chương ngắn hơn và nhiều dấu ❌ hơn một chương "khảo sát" thông thường. Đó là chủ đích: một bảng so sánh đầy đủ nhưng có ô chưa từng được đo sẽ dẫn người đọc tới kết luận sai, và một hội đồng truy tới nguồn sẽ phát hiện ra. Nói trước thì mất một dòng; để người khác phát hiện thì mất cả độ tin cậy của những con số **đã** đo thật.

## 3.2. Mô hình phát hiện: YOLO11

**Các phương án đã xét.** Bảy thế hệ YOLO thuộc phạm vi cân nhắc, giới hạn từ YOLOv8 trở về sau vì đây là mốc chuyển sang kiến trúc anchor-free có ý nghĩa trực tiếp với bài toán biển số (mục 2.4.2): YOLOv8 [27], YOLOv9 [32], YOLOv10 [24], YOLO11 [28], YOLOv12 [33], YOLOv13 [34] và YOLO26 [25]. Họ two-stage (Faster R-CNN, Mask R-CNN) bị loại từ đầu vì chi phí tính toán không tương thích với ràng buộc CPU (mục 2.4.2).

**Tiêu chí đánh giá**, xếp theo mức độ chi phối:

1. **Có số liệu tốc độ CPU chính thức hay không.** Đây là ràng buộc chi phối vì đồ án triển khai trên máy không có GPU.
2. Mức độ phù hợp của cơ chế kiến trúc với đặc thù bài toán (đối tượng nhỏ, tỷ lệ khung hình dẹt).
3. Mật độ bằng chứng thực nghiệm trên đúng bài toán biển số.
4. Độ trưởng thành của hệ sinh thái và tình trạng giấy phép.

**Quá trình loại trừ.** Khảo sát các bảng benchmark chính thức phát hiện một điều then chốt: **chỉ các bản phát hành từ Ultralytics công bố tốc độ CPU**. YOLOv9 không công bố bất kỳ cột tốc độ nào; YOLOv10, YOLOv12 và YOLOv13 chỉ công bố tốc độ GPU. Bốn phiên bản này do đó bị loại vì **không có căn cứ để đánh giá** trên đúng chiều ràng buộc của đồ án; YOLOv13 còn có rủi ro bổ sung là kho mã nguồn không được tích hợp chính thức vào thư viện Ultralytics [34].

Còn lại ba ứng viên. YOLOv8 bị loại vì YOLO11n **vượt trội đồng thời ở cả hai chiều**: mAP@0.5:0.95 đạt 39,5 so với 37,3 (hơn 2,2 điểm) và tốc độ CPU với định dạng ONNX là **56,1 ± 0,8 ms so với 80,4 ms** — nhanh hơn khoảng 30% [28], [31]. Đây là phép so sánh CPU hợp lệ duy nhất có sẵn, vì cả hai đều đo bằng cùng quy trình xuất mô hình [91]<!-- ultralytics_2026_detecttask -->.

**Kết luận: chọn YOLO11, biến thể n (nano), với năm lý do.**

1. **Là phiên bản duy nhất trong nhóm gần đây có số liệu tốc độ CPU chính thức**, cho phép lập luận có căn cứ khi bảo vệ thay vì suy đoán.
2. **Có cơ chế kiến trúc phù hợp trực tiếp với bài toán:** khối C2PSA được khẳng định cải thiện phát hiện đối tượng nhỏ và xử lý che khuất phức tạp [31]; đầu dự đoán anchor-free giải quyết vấn đề tỷ lệ khung hình nằm ngoài phân bố COCO (mục 2.4.2).
3. **Có bằng chứng thực nghiệm dày nhất trên đúng bài toán biển số:** ít nhất ba nghiên cứu độc lập dùng YOLO11 cho ALPR với mAP@0.5 từ 0,906 đến 0,995 [36], [37], [92]<!-- sutikno_2025_clahe -->. Một nghiên cứu so sánh trực tiếp YOLOv8n, YOLOv9t, YOLOv10n và YOLO11n trên cùng một tập dữ liệu biển số với siêu tham số đồng nhất cũng kết luận YOLO11n tối ưu nhất [93]<!-- sciencedirect_2026_omanplates --> — tuy nhiên nguồn này **chưa kiểm chứng được toàn văn** do bị chặn truy cập, nên chỉ dùng làm trích dẫn phụ, không làm căn cứ chính.
4. **Hệ sinh thái trưởng thành:** tích hợp chính thức trong thư viện `ultralytics`, hỗ trợ hơn 20 định dạng xuất mô hình [94]<!-- ultralytics_2026_export --> và có chế độ benchmark tự động trên CPU [95]<!-- ultralytics_2026_benchmark -->.
5. **Giấy phép hợp lệ:** AGPL-3.0 được nhà phát hành khẳng định miễn phí cho nghiên cứu học thuật và bài tập đại học, với điều kiện công bố mã nguồn [96]<!-- ultralytics_2026_license -->.

**Chọn biến thể nano vì bài toán chỉ có một lớp.** Năng lực biểu diễn cần cho 80 lớp của COCO là dư thừa cho một lớp duy nhất. Số kênh đầu ra của nhánh phân loại giảm từ 80 xuống 1, làm nhẹ đầu dự đoán và giảm chi phí bước NMS. Bằng chứng ủng hộ: một nghiên cứu đạt mAP 99,3% với biến thể YOLOv8-s trên ba benchmark quốc tế ở tốc độ trên 30 FPS, hướng tới đúng kịch bản thiết bị hạn chế tài nguyên [97]<!-- etasr_2025_optimizedyolov8 -->. Biến thể s được giữ làm phương án leo thang nếu nano không đạt chỉ tiêu.

**Đánh đổi phải chấp nhận.**

- **Giấy phép AGPL-3.0 kéo theo nghĩa vụ copyleft.** Nghĩa vụ này bao gồm công bố toàn bộ mã nguồn tương ứng, các sửa đổi, tệp cấu hình và cả **trọng số mô hình**; và điều khoản mạng của AGPL-3.0 khiến không thể tránh nghĩa vụ này bằng cách chỉ cung cấp dịch vụ qua API [96]. Với một đồ án tốt nghiệp công bố mã nguồn công khai, đây là điều kiện chấp nhận được; nhưng nếu hệ thống được thương mại hoá sau này thì phải mua giấy phép doanh nghiệp. Không có phương án nào trong nhóm ứng viên tránh được nghĩa vụ copyleft.
- **Luận cứ về cải thiện đối tượng nhỏ chỉ ở mức định tính**, vì nhà phát hành không công bố chỉ số AP_small tách riêng (mục 2.4.3). Đồ án phải tự đo để chuyển luận cứ này sang định lượng.
- **Bỏ qua YOLO26 dù nó vượt trội trên giấy tờ.** YOLO26n có mAP@0.5:0.95 đạt 40,9 (hơn 1,4 điểm so với YOLO11n) và tốc độ CPU 38,9 ± 0,7 ms (nhanh hơn khoảng 30%), đồng thời thiết kế bỏ DFL giúp việc xuất và lượng tử hoá dễ hơn [25]. Lý do vẫn không chọn làm mặc định: YOLO26 phát hành tháng 09/2025 và **chưa có tiền lệ nào trên bài toán biển số** để đối chiếu, nên chọn nó làm phương án duy nhất là rủi ro không cần thiết cho một đồ án có thời hạn. Cách xử lý dự kiến: huấn luyện YOLO26n **song song làm đối chứng** trên cùng tập dữ liệu và cùng siêu tham số; nếu nó cho kết quả tốt hơn và ổn định khi xuất mô hình thì chuyển sang và ghi nhận đây là đóng góp mới. **Lượt đối chứng này cuối cùng đã không chạy được** vì toàn bộ ngân sách CPU dồn cho lượt huấn luyện `best.pt` chính thức; hạng mục được ghi nhận là chưa đo ở mục 6.9.2 và chuyển thành hướng phát triển.

## 3.3. Engine nhận dạng ký tự

Đây là lựa chọn mà đồ án trình bày **trung thực nhất về mức độ chắc chắn**, vì bằng chứng hiện có không đủ để phân định dứt khoát. Mục này tách làm hai phần theo đúng ranh giới bằng chứng đã nêu ở Bảng 3.1: chọn *họ engine* dựa trên khảo sát tài liệu (3.3.1), rồi chọn *bậc mô hình* trong họ đã chọn dựa trên phép đo tự chạy (3.3.2).

### 3.3.1. PaddleOCR, EasyOCR, Tesseract — khảo sát tài liệu

**Các phương án đã xét.** Tám engine được khảo sát: PaddleOCR, EasyOCR, Tesseract, TrOCR, docTR, MMOCR, fast-plate-ocr và RapidOCR/OnnxTR. Bảng 3.2 tóm tắt các đặc tính quyết định.

**Bảng 3.2.** So sánh các engine OCR ứng viên

| Tiêu chí | **PaddleOCR** (PP-OCRv5 mobile) | **EasyOCR** | **Tesseract** | **TrOCR** |
|---|---|---|---|---|
| Kiến trúc | 2 giai đoạn: DB và SVTR-LCNet/CTC [40] | 2 giai đoạn: CRAFT và CRNN/CTC [39] | LSTM theo dòng [98]<!-- tesseract_2026_releasenotes --> | Encoder-decoder BEiT và RoBERTa [49] |
| Kích thước mô hình | **4,7 MB det + 16 MB rec ≈ 21 MB** [99]<!-- paddlepaddle_2026_textdetection -->, [100]<!-- paddlepaddle_2026_textrecognition --> | Khoảng 200 MB | Khoảng 30 MB mô hình | 334 – 558 triệu tham số [49] |
| Thời gian CPU | det 57,77 ms + rec 21,20 ms [99], [100] | Cần đo ở giai đoạn thực nghiệm | Nhanh nhất trong nhóm | Không đo — đã loại |
| Giấy phép | Apache 2.0 | Apache 2.0 | Apache 2.0 | MIT |
| Hỗ trợ nhiều dòng | Tự nhiên — mỗi dòng một hộp, **cần tự sắp xếp** | Tự nhiên — CRAFT tách vùng | Về lý thuyết có, thực tế kém [101]<!-- rosebrock_2021_psm --> | **Ảo giác trên đa dòng** [50] |
| Giới hạn tập ký tự khi suy luận | **Không có** — phải tinh chỉnh [102]<!-- paddleocr_2022_discussion7515 --> | Có, tham số native [103]<!-- jaided_2025_easyocrdocs --> | **Tốt nhất** [104]<!-- rosebrock_2021_whitelist --> | Không — dùng tokenizer subword |
| Độ khó triển khai trên Windows + CPU | Trung bình — framework riêng | **Dễ nhất** — chỉ cần PyTorch | Cần cài binary hệ thống | Dễ cài nhưng tải 1,3 – 2,2 GB |

*Ghi chú bắt buộc về cột thời gian CPU: các con số của PaddleOCR đo trên Intel Xeon Gold 6271C, chế độ FP32, trên tập đánh giá nội bộ đa ngôn ngữ gồm ảnh tài liệu — **không phải ảnh biển số**.*

Bốn engine bị loại sớm với lý do rõ ràng: **TrOCR** vì ảo giác trên văn bản đa dòng, quá nặng cho CPU và biến dạng tỷ lệ khung hình (mục 2.5.3g); **MMOCR** vì chuỗi phụ thuộc bốn tầng, rủi ro cài đặt cao nhất trên Windows không GPU [105]<!-- openmmlab_2023_mmocrrepo -->; **fast-plate-ocr** vì không có mô hình cho biển số Việt Nam và kiến trúc khe cố định không xử lý được biển hai dòng nếu chưa huấn luyện lại [106]<!-- kandratavicius_2026_fastplateocr -->; **docTR** vì tối ưu cho trang tài liệu chứ không cho ảnh crop nhỏ [107]<!-- mindee_2026_doctrmodels -->.

**Bằng chứng thực sự đứng vững cho PaddleOCR.** Trong quá trình khảo sát, hai số liệu thường được viện dẫn để chứng minh "PaddleOCR tốt cho biển số" đã **bị bác bỏ khi truy ngược về nguồn gốc**: cả hai đều đến từ một bài báo dùng **EasyOCR**, không phải PaddleOCR [108]<!-- scirep_2024_yolov8ocr -->. Việc trích dẫn nhầm này đã được loại bỏ hoàn toàn. Sau khi loại, những bằng chứng còn đứng vững là:

1. **Nhẹ nhất trong nhóm khả dụng:** khoảng 21 MB so với khoảng 200 MB của EasyOCR — yếu tố quyết định với ràng buộc bộ nhớ của đồ án.
2. **Thời gian CPU khả thi**, và trên giấy có lộ trình nâng cấp: PP-OCRv6 bản Tiny chỉ 1,5 triệu tham số và đạt 0,20 giây mỗi ảnh trên CPU, nhanh hơn PP-OCRv5 mobile khoảng 3,9 lần [109]<!-- paddlepaddle_2026_ppocrv6 -->. **Lộ trình này về sau không lấy được** — xem mục 3.3.2.
3. **Ràng buộc siêu nhẹ là chủ đích thiết kế xuyên suốt của dòng PP-OCR** chứ không phải kết quả ngẫu nhiên của một bản phát hành [110]<!-- du_2020_ppocr -->, [111]<!-- du_2021_ppocrv2 --> — đúng thứ mà ràng buộc CPU của đồ án cần.
4. **Có bằng chứng tinh chỉnh trên biển số cho kết quả tốt:** recognition tăng từ 90,97% lên 94,54%, detection Hmean tăng từ 76,12% lên 99,00% [48] — tuy nhiên đây là **biển số Trung Quốc một dòng**.
5. **Kiến trúc hai giai đoạn trả mỗi dòng một hộp** — đúng thứ cần cho biển hai dòng.
6. **Giấy phép Apache 2.0**, không ràng buộc copyleft.

**Những gì PaddleOCR thua.** Không có cơ chế giới hạn tập ký tự khi suy luận, phải tinh chỉnh mới có được [102]; khó cài hơn EasyOCR vì kéo theo một framework học sâu thứ hai bên cạnh PyTorch; và kém xa các mô hình chuyên biệt cho biển số như LPTR-AFLNet vốn đạt 99,37% riêng trên biển hai dòng với chỉ 2,7 triệu tham số [72] — nhưng mô hình đó không có gói cài đặt sẵn, không có bản cho biển số Việt Nam và không công bố số liệu CPU.

> ### 🎯 Kết luận trung thực — điểm quan trọng nhất của Chương 3
>
> **PaddleOCR là lựa chọn hợp lý, nhưng KHÔNG phải lựa chọn đã được chứng minh là tốt nhất cho bài toán này.** Ba điểm phải nói rõ:
>
> 1. **Bằng chứng trực tiếp ủng hộ PaddleOCR trên ảnh biển số yếu hơn ta tưởng.** Hai số liệu mạnh nhất từng được viện dẫn đã bị bác bỏ. Các so sánh engine-với-engine trên ảnh biển số mà khảo sát kiểm chứng được lại **nghiêng về EasyOCR** [112]<!-- reddy_2024_yolov8ocr -->. **Không tồn tại số liệu công khai nào cho thấy PaddleOCR vượt EasyOCR trên ảnh biển số.**
> 2. **Lý do giữ PaddleOCR là lý do kỹ thuật và vận hành, không phải lý do độ chính xác:** nhẹ hơn EasyOCR gần 10 lần, có lộ trình tăng tốc rõ ràng, có bằng chứng tinh chỉnh, và mạnh trên ảnh xoay.
> 3. **Không engine nào giải sẵn bài toán hai dòng.** Như đã chứng minh ở mục 2.5.3, việc chọn engine **không quyết định** thành bại của rủi ro R-04 — module tách và ghép dòng mới quyết định.
>
> Cách xử lý đúng về mặt học thuật: **giữ PaddleOCR làm baseline** vì các lý do kỹ thuật ở điểm 2, nhưng coi **quyết định cuối cùng là kết luận của giai đoạn thực nghiệm**, dựa trên benchmark tự chạy trên chính tập dữ liệu biển số Việt Nam. **EasyOCR phải được coi là ứng viên ngang hàng, không phải phương án dự phòng hình thức.** Tesseract được giữ làm mốc so sánh dưới.
>
> Cách làm này vừa trung thực nhất, vừa biến điểm yếu "chưa chứng minh được" thành đóng góp khoa học "đồ án là bên đầu tiên đo" — đúng khoảng trống số 4 ở Bảng 2.23. **Cần ghi nhận trung thực rằng benchmark này cuối cùng đã không chạy được** trong khuôn khổ đồ án: PaddleOCR PP-OCRv5_mobile được giữ làm engine duy nhất vì các lý do kỹ thuật ở điểm 2 ở trên, **không phải vì đã chứng minh được nó chính xác hơn EasyOCR**. Hạng mục được ghi nhận là chưa đo ở mục 6.9.2 và chuyển thành hướng phát triển.

**Ma trận thí nghiệm dự kiến** gồm bốn trục: engine (PaddleOCR chưa tinh chỉnh, PaddleOCR đã tinh chỉnh, EasyOCR, Tesseract); phương án xử lý biển hai dòng (đưa thẳng, sắp xếp hộp theo toạ độ dọc, tách rồi ghép ngang, tách rồi gọi OCR hai lần); có hoặc không nắn chỉnh phối cảnh; và runtime suy luận. Chỉ số chính là **độ chính xác mức chuỗi tách riêng cho biển một dòng và biển hai dòng**, kèm độ trễ ở các phân vị p50, p95, p99 đo trên chính máy của đồ án.

### 3.3.2. PP-OCRv5 mobile so với PP-OCRv6 — đo trên máy đồ án

Mục 3.3.1 chọn **họ** engine. Mục này chọn **bậc mô hình** bên trong họ đã chọn, và khác mục trên ở một điểm quyết định: câu trả lời ở đây dựa trên số liệu đồ án **tự đo**, không phải trên tài liệu. Số liệu đầy đủ và quy trình đo ở `docs/reports/35-ppocrv6-evaluation.md`.

**a) Chỉ một bậc của v6 là lấy được.** Quét toàn bộ gói `paddleocr 3.7.0` đã cài chỉ tìm thấy ba định danh v6: `PP-OCRv6`, `PP-OCRv6_medium_det` và `PP-OCRv6_medium_rec`. **Không có bản Tiny, không có bản Small.**

Đây chính là điểm quyết định, chứ không phải một chi tiết đóng gói. Bậc hấp dẫn với một hệ thống chạy CPU là **Tiny** — bài báo ghi 0,20 giây mỗi ảnh, nhanh hơn PP-OCRv5 mobile (0,78 giây) khoảng 3,9 lần. Đó cũng đúng là "lộ trình nâng cấp trên giấy" từng được viện dẫn ở mục 3.3.1 làm một trong sáu lý do giữ PaddleOCR. Bậc duy nhất tải được lại là **Medium**, bậc mà chính bài báo ấy ghi 1,40 giây mỗi ảnh — tức **chậm hơn** v5 mobile khoảng 1,8 lần. Lộ trình nâng cấp vì vậy **không lấy được**, và điều đó phải được ghi nhận thay vì để nguyên như một lợi thế còn hiệu lực.

**b) Phải tự đo, vì số của bài báo không trả lời đúng câu hỏi.** Bài báo đo trên Intel Xeon 8350C **có OpenVINO** và đo trên **văn bản tài liệu**, không phải trên biển số. Cả phần cứng lẫn miền dữ liệu đều lệch khỏi điều kiện của đồ án.

Cách đo: 200 vùng cắt biển số nguyên ảnh lấy từ tập kiểm định (`val.txt`, không tăng cường, không mảnh vụn), chạy **chỉ nhánh nhận dạng** để cô lập đúng biến đang so sánh. Cùng máy, cùng ảnh, cùng thứ tự.

**Bảng 3.3.** PP-OCRv6_medium_rec so với PP-OCRv5_mobile_rec, đo trên 200 vùng cắt biển số của đồ án

| Mô hình | Đúng chuỗi | Trung vị | p95 |
|---|---:|---:|---:|
| **PP-OCRv5_mobile_rec** — *đang dùng* | 134/200 = **67,0%** | **23,0 ms** | 31,9 ms |
| PP-OCRv6_medium_rec | 145/200 = **72,5%** | 386,9 ms | 429,0 ms |

**v6 Medium chính xác hơn 5,5 điểm và chậm hơn 16,8 lần.** Chiều của kết quả khớp bài báo — v6 Medium *đúng là* chính xác hơn — nhưng biên độ chi phí trên máy này lớn hơn nhiều so với tỷ lệ 1,8 lần mà bài báo ghi, vì bài đo có OpenVINO còn đồ án chạy PaddlePaddle thuần.

**c) Vì sao 5,5 điểm ấy vẫn không đủ.** Hệ thống đã căng về độ trễ ở **cả hai đầu**: NFR-P1 đạt sàn sát nút (p95 1.143 ms, sàn 1.500 ms) và NFR-P2 thì **đã trượt** (2,379 FPS, sàn 3). Bước OCR trong đường ống chiếm 108,28 ms mỗi biển ({{T6.6b}}), trong đó nhánh nhận dạng chỉ khoảng 23 ms — phần còn lại là bước phát hiện chữ. Thay v5 bằng v6 Medium cộng thêm khoảng **364 ms mỗi biển**.

> ⚠️ **Đây là phép chiếu, không phải phép đo.** Cộng 364 ms vào p95 hiện hành cho khoảng **1.507 ms**, tức **vượt sàn 1.500 ms** và đẩy NFR-P1 từ 🟡 xuống ❌. Con số này suy ra từ độ trễ nhánh nhận dạng đo cô lập, **chưa chạy lại toàn đường ống** — muốn công bố phải đo thật. Nhưng ngay cả với sai số rộng, hướng của kết luận không đổi: NFR-P2 vốn đã trượt sàn thì chắc chắn trượt sâu hơn.

**d) Kết luận: giữ PP-OCRv5_mobile_rec.** Đây **không phải** kết luận "v6 kém hơn" — nó chính xác hơn thật, và 5,5 điểm ấy là **dư địa đã định lượng** chứ không phải một cơ hội bị bỏ lỡ. Đây là kết luận về **ràng buộc phần cứng của đồ án**: hệ thống chạy CPU thuần (ràng buộc số 1 ở mục 3.1.1), và bậc v6 phù hợp với ràng buộc đó — Tiny — **không có trong gói**.

Hai điều kiện đảo được quyết định này, và cả hai đều **đo được**: PaddleOCR phát hành bậc Tiny vào gói pip (bậc này được ghi là nhanh hơn v5 mobile 3,9 lần, tức cải thiện *cả* độ chính xác *lẫn* độ trễ, không phải đánh đổi); hoặc xuất được v6 Medium sang ONNX/OpenVINO với mức tăng tốc trên 8 lần, khi đó 386 ms về khoảng 45 ms và bài toán đổi hẳn. Cả hai đã nằm trong hướng phát triển ở Chương 7.

> **Lưu ý bắt buộc khi trích bài PP-OCRv6.** Cặp *"+5,1 / +4,6 điểm"* mà bài v6 công bố được tính trên **baseline của chính nó** (v5_server 78,1% / 81,6%), không phải trên baseline trong tài liệu PaddleX (86,38% / 83,8%). Ghép hai nguồn sẽ **đảo chiều kết luận**. Trích thì phải trích kèm baseline gốc.

## 3.4. Runtime suy luận trên CPU: ONNX Runtime

**Các phương án đã xét:** chạy trực tiếp tệp trọng số PyTorch, ONNX Runtime, và OpenVINO.

**Tiêu chí:** tốc độ trên CPU, mức độ đa nền tảng, độ nặng của phụ thuộc khi đóng gói, và khả năng cùng tồn tại với các framework khác.

**Bằng chứng định lượng.** Benchmark chính thức trên CPU laptop Intel Core i7-13700H, chế độ FP32, kích thước ảnh 640, cho thấy **ONNX Runtime nhanh gấp khoảng 3,73 lần so với chạy trực tiếp PyTorch ở phân khúc nano: 104,61 ms giảm còn 28,02 ms** [113]<!-- ultralytics_2026_openvinoexport -->. Lợi ích này lớn nhất đúng ở phân khúc mà đồ án sử dụng và thu hẹp dần khi mô hình lớn lên.

> **Cảnh báo trích dẫn bắt buộc.** Chỉ được dùng **phần số liệu tốc độ** của bảng benchmark này. Các con số mAP đi kèm trong bảng gốc được đo trên tập `coco8` chỉ gồm **8 ảnh**, nên **vô nghĩa về mặt thống kê** và không được trích dẫn dưới bất kỳ hình thức nào.

Ba kết luận bổ sung từ cùng nguồn dữ liệu:

- **OpenVINO không phải luôn nhanh hơn.** Trên CPU Intel thế hệ mới, OpenVINO ở chế độ FP32 **chậm hơn PyTorch** ở các biến thể lớn, do PyTorch hiện đại đã tối ưu tốt các thư viện tính toán trên CPU mới [113]. Hệ quả bắt buộc: đồ án phải **tự benchmark trên đúng máy chạy**, không được tin số liệu chung.
- **FP16 hoàn toàn vô ích trên CPU.** Đây là một hiểu nhầm phổ biến cần nêu rõ: trên CPU, OpenVINO chuyển nội bộ toàn bộ giá trị FP16 sang FP32 và thực hiện mọi phép tính ở FP32 [114]<!-- openvino_2025_precisioncontrol -->; số liệu benchmark xác nhận chênh lệch dưới 1% [113]. FP16 chỉ giảm một nửa dung lượng lưu trữ. Kết luận: bỏ qua FP16 trên CPU, đi thẳng từ FP32 sang INT8 nếu cần thêm tốc độ.
- **Lượng tử hoá INT8 là lợi thế thực sự của OpenVINO**, đạt mức tăng tốc 2,3 đến 3,6 lần với mất mát mAP tương đối chỉ 1,73 đến 2,47% [113]. Tuy nhiên với mô hình CNN phải dùng lượng tử hoá **tĩnh** kèm tập hiệu chuẩn, và cần kiểm tra CPU có hỗ trợ tập lệnh phù hợp trước khi đầu tư.

**Kết luận: mặc định dùng ONNX Runtime, coi OpenVINO là phương án tối ưu bổ sung.** Ba lý do:

1. **Nhanh hơn đáng kể** so với chạy trực tiếp tệp PyTorch ở đúng phân khúc mô hình mà đồ án dùng.
2. **Là chuẩn mở, không ràng buộc nhà sản xuất CPU**, và cùng một tệp mô hình phục vụ được cho cả khối detection lẫn khối OCR.
3. **Loại bỏ hoàn toàn rủi ro xung đột giữa hai framework học sâu.** Đồ án dùng PyTorch cho YOLO và PaddlePaddle cho PaddleOCR — hai framework khác nhau cùng tồn tại trong một môi trường Python trên Windows là một nguồn rủi ro thực sự. Nếu **cả hai** mô hình đều chạy bằng ONNX Runtime khi vận hành, rủi ro này biến mất. Đây có thể là lý do quan trọng nhất trong cả mục.

**Đánh đổi phải chấp nhận:** thêm một bước xuất mô hình vào quy trình; phải kiểm chứng tính tương thích của gói cài đặt với Python 3.13 trên Windows; và phải **đặt tường minh số luồng nội bộ** đồng thời với **giới hạn số yêu cầu suy luận đồng thời** ở tầng ứng dụng, vì cả ONNX Runtime lẫn PaddleOCR đều mặc định sinh số luồng bằng hoặc lớn hơn số lõi vật lý, dễ gây tranh chấp tài nguyên khi backend xử lý nhiều yêu cầu song song [115]<!-- onnxruntime_2025_threading -->.

## 3.5. Các lựa chọn công nghệ nền tảng khác

Bảng 3.4 tổng hợp các quyết định còn lại. Phần lớn các lựa chọn này là **ràng buộc của đề bài** chứ không phải lựa chọn tự do; chúng được ghi lại kèm lý do và đánh đổi để phần thiết kế ở Chương 4 có căn cứ tham chiếu.

**Bảng 3.4.** Tổng hợp quyết định công nghệ nền tảng

| # | Hạng mục | Lựa chọn | Lý do chính | Phương án thay thế | Đánh đổi phải chấp nhận |
|:--:|---|---|---|---|---|
| 1 | Web framework backend | **FastAPI** | Tự sinh đặc tả OpenAPI nên tạo sẵn một sản phẩm bàn giao; hỗ trợ sẵn WebSocket và tác vụ nền nên không phát sinh dịch vụ phụ trợ | Django, Flask | Phải hiểu rõ khi nào **không** dùng hàm bất đồng bộ; nguy cơ tranh chấp luồng với luồng suy luận |
| 2 | ORM và migration | **SQLAlchemy 2.0 + Alembic** | Tích hợp sâu hệ thống kiểu tĩnh; lược đồ cơ sở dữ liệu đã thay đổi một lần nên nhu cầu migration là có thật | Tortoise ORM, Peewee | Đường cong học dốc nhất trong nhóm |
| 3 | Cơ sở dữ liệu | **SQLite** | Ghi có thể xếp hàng vì suy luận trên CPU mới là nút cổ chai; không thêm dịch vụ khi đóng gói; nộp kèm được tệp dữ liệu | PostgreSQL, MySQL | **Chỉ một tiến trình ghi tại một thời điểm**; phải chuyển sang PostgreSQL nếu vượt ngưỡng tải |
| 4 | Frontend | **React + TypeScript + Vite + TailwindCSS** | Hệ sinh thái lớn nhất; công cụ build tiền nhiệm đã ngừng bảo trì; kiểu tĩnh nối tiếp chuỗi kiểu từ backend sang client | Vue, Angular, Svelte | Phải tự lắp ghép routing và quản lý trạng thái; tự dựng thành phần giao diện thay vì dùng thư viện có sẵn |
| 5 | Framework học sâu | **PyTorch** | Thư viện Ultralytics khai báo PyTorch là phụ thuộc lõi, nên chọn YOLO11 là chọn PyTorch | TensorFlow | Kéo theo một framework học sâu **thứ hai** (PaddlePaddle) do lựa chọn OCR — rủi ro xung đột được giải bằng quyết định ở mục 3.4 |
| 6 | Đóng gói | **Docker + Compose** | Yêu cầu về khả năng tái lập và khởi động bằng một lệnh | — | Kích thước image là rủi ro do có framework học sâu |

---

## 3.6. Khảo sát ảnh hưởng của độ phân giải và chất lượng split

Đồ án có hai mô hình đã huấn luyện: `baseline-416-v1.pt` và `best.pt`. So sánh chúng là điều tự nhiên, nhưng **phải được thực hiện với sự thận trọng phương pháp luận rất cao**, vì lý do trình bày ngay dưới bảng.

<!-- {{T3.6}} so sanh baseline 416/v1 voi mo hinh chinh thuc 640/v3 -->

**Bảng 3.5.** So sánh `baseline-416-v1.pt` với `best.pt` — ba biến thay đổi đồng thời

| Hạng mục | `baseline-416-v1.pt` | `best.pt` (chính thức) | Chênh lệch |
|---|---:|---:|---:|
| **Cấu hình** | | | |
| `imgsz` | 416 | **640** | +224 px |
| Bộ dữ liệu | v1 — 4.578 ảnh, 1 nguồn | **v3 — 15.133 ảnh, 6 nguồn nguyên tố (hợp nhất từ 7 bộ)** | ×3,3 |
| Ngưỡng gộp trùng lặp | 5 | **10** | +5 |
| Rò rỉ train↔test (ngưỡng 10) | **619 cặp** | **0 cặp** *(hệ quả định nghĩa, xem T6.3b)* | |
| Số epoch | 40 | **20** | −20 |
| Tổng thời gian huấn luyện | 156 phút | **≈ 712 phút** | |
| **Kết quả trên tập test tương ứng** | | | |
| mAP@0.5 | **0,9933** *(epoch 38)* | **0,9829** | −0,0104 |
| mAP@0.5:0.95 | **0,8597** *(epoch 38)* | **0,7834** | −0,0763 |
| Precision | **0,9822** | **0,9837** | +0,0015 |
| Recall | **0,9810** | **0,9714** | −0,0096 |
| mAP biển một dòng | **0,9856** | **0,9884** | +0,0028 |
| mAP biển hai dòng | **0,9592** | **0,9675** | +0,0083 |
| Chênh lệch theo layout (điểm %) | **2,6** | **2,09** | −0,51 |
| Độ trễ E2E p95 (ms) | **763,75** *(client-side)* | **1.143,10** *(in-process, có bậc thang thử-lại)* | — |

> ⚠ Ba biến thay đổi đồng thời (imgsz, bộ dữ liệu + cách chia, số epoch) và chúng tác động **ngược chiều** nhau — không được quy kết nguyên nhân cho bất kỳ biến nào (xem 3.6.1). Dòng độ trễ E2E dùng con số **client-side đã xác minh** cho **cả hai** mô hình (763,75 ms và 731,15 ms, máy rảnh, qua HTTP); con số 5.857,19 ms từng ghi cho baseline ở báo cáo Phase 7 đã bị **bác bỏ** vì nhiễm tranh chấp CPU và đo sai checkpoint (mục 6.6.1). Đo cùng phương pháp trên máy rảnh, hai mô hình cho độ trễ gần như y hệt.

### 3.6.1. Vì sao so sánh này không quy kết được nguyên nhân

**Đây là so sánh có ít nhất ba biến cùng thay đổi**, và điều đó phải được nói thẳng chứ không được lướt qua:

| Biến thay đổi | Baseline | Chính thức | Hướng ảnh hưởng dự kiến |
|---|---|---|---|
| Độ phân giải đầu vào | 416 | 640 | Tăng độ phân giải → dự kiến **cải thiện**, nhất là với đối tượng nhỏ |
| Bộ dữ liệu và cách chia | v1, có rò rỉ | v3, ngưỡng gộp chặt hơn | Khử rò rỉ → dự kiến **làm giảm** chỉ số đo được, vì chỉ số cũ bị thổi phồng |
| Số epoch | 40 | 20 | Ít epoch hơn → dự kiến **làm giảm**, nếu chưa hội tụ |

Ba biến này tác động **ngược chiều nhau**. Do đó:

- **Nếu `best.pt` cho mAP *thấp hơn* baseline**, kết luận **không** được viết là "mô hình chính thức kém hơn". Kịch bản nhiều khả năng nhất là: baseline được đo trên một tập test **có rò rỉ**, nên con số 0,9933 của nó **bị thổi phồng** và không phản ánh năng lực tổng quát hoá thật. Khi đó chỉ số thấp hơn của `best.pt` lại là chỉ số **đáng tin cậy hơn**. Đây là một trong những nghịch lý quan trọng nhất cần trình bày được khi bảo vệ: *một con số thấp hơn nhưng đo đúng có giá trị hơn một con số cao hơn nhưng đo sai*.
- **Nếu `best.pt` cho mAP *cao hơn* baseline**, cũng **không** được quy kết cho riêng việc tăng `imgsz`, vì lượng dữ liệu đã tăng 3,3 lần đồng thời.
- **Trong cả hai trường hợp**, phát biểu duy nhất được phép là mô tả: *"cấu hình A cho kết quả X, cấu hình B cho kết quả Y, ba biến thay đổi đồng thời nên không tách được đóng góp của từng biến."*

**Kết quả thực tế rơi vào trường hợp thứ nhất, và đây là một kết quả *có giá trị* chứ không phải một sự thụt lùi.** `best.pt` cho mAP@0.5:0.95 = **0,7834**, thấp hơn baseline **0,8597** đúng **7,63 điểm** (mAP@0.5 cũng thấp hơn 1,04 điểm). Theo đúng khung lập luận đã cố định trước, con số thấp hơn này **không** được đọc là "mô hình chính thức kém hơn". Baseline được huấn luyện và đánh giá trên split v1 — split **có rò rỉ** (619 cặp gần trùng train↔test ở ngưỡng 10), nghĩa là một phần tập test v1 gần trùng với ảnh đã thấy khi huấn luyện; mô hình *ghi nhớ* thay vì *tổng quát hoá*, và con số 0,8597 vì thế **bị thổi phồng**. `best.pt` được đánh giá trên split v3 đã siết khử trùng lặp (0 cặp ở ngưỡng gộp), nên 0,7834 phản ánh năng lực tổng quát hoá **trung thực hơn**, dù trị số thấp hơn. Đây chính là nghịch lý cốt lõi cần trình bày khi bảo vệ: **một con số thấp hơn nhưng đo đúng có giá trị hơn một con số cao hơn nhưng đo trên tập bị rò rỉ.** Không được kết luận mạnh hơn (ví dụ "toàn bộ 7,63 điểm là do khử rò rỉ"), vì `imgsz` tăng và số epoch giảm đồng thời cũng tác động; nhưng cũng tuyệt đối không được trình bày `best.pt` như một mô hình "tệ hơn baseline". Ở tầng phát hiện, `best.pt` vẫn **vượt mọi ngưỡng NFR** (mục 6.4.1) — nên đây là một mô hình đạt yêu cầu, được đo trên một tập đánh giá đáng tin hơn.

### 3.6.2. Thí nghiệm cô lập biến — đề xuất, chưa thực hiện

Muốn quy kết nguyên nhân cho từng biến, cần một ma trận thí nghiệm cô lập:

| Thí nghiệm | `imgsz` | Bộ dữ liệu | Mục đích | Chi phí ước tính (CPU) | Trạng thái |
|:---:|:---:|:---:|---|---:|:---:|
| E1 | 416 | v3 | Cô lập ảnh hưởng của **độ phân giải** (so với `best.pt`) | ≈ 5 giờ | ⬜ chưa chạy |
| E2 | 640 | v1 | Cô lập ảnh hưởng của **chất lượng bộ dữ liệu** | ≈ 4 giờ | ⬜ chưa chạy |
| E3 | 640 | v3, 40 epoch | Cô lập ảnh hưởng của **số epoch** | ≈ 24 giờ | ⬜ chưa chạy |

Ba thí nghiệm này **không được thực hiện** trong khuôn khổ đồ án, vì tổng chi phí khoảng 33 giờ CPU liên tục vượt quá ngân sách thời gian còn lại. Việc ghi nhận chúng ở đây — kèm chi phí ước tính và lý do không chạy — trung thực hơn là im lặng về giới hạn của phép so sánh ở mục 3.6, và đồng thời cung cấp một hướng phát triển cụ thể, có thể thực hiện được cho Chương 7.

## 3.7. Kết luận chương

**Bảng 3.6.** Tổng hợp các quyết định công nghệ và căn cứ

| Hạng mục | Quyết định | Căn cứ quyết định | Mức bằng chứng | Đánh đổi đã chấp nhận |
|---|---|---|:---:|---|
| Mô hình phát hiện | **YOLO11n** | Phiên bản gần đây duy nhất có số liệu tốc độ CPU chính thức; khối C2PSA hợp với đối tượng nhỏ; bằng chứng ALPR dày nhất | 📄 tài liệu | Giấy phép AGPL-3.0 kéo theo nghĩa vụ copyleft; bỏ qua YOLO26 dù trội hơn trên giấy |
| Họ engine OCR | **PaddleOCR** | Nhẹ hơn EasyOCR gần 10 lần; kiến trúc hai giai đoạn trả mỗi dòng một hộp; Apache 2.0 | ❌ chưa đo | **Không chứng minh được là chính xác hơn EasyOCR** |
| Bậc mô hình OCR | **PP-OCRv5_mobile** | v6 Medium chính xác hơn 5,5 điểm nhưng chậm hơn 16,8 lần; bậc Tiny của v6 không có trong gói | ✅ tự đo | Bỏ lại 5,5 điểm độ chính xác đã định lượng được |
| Tinh chỉnh bộ nhận dạng | **Không dùng ở bản giao hàng** | Ở đúng chế độ hệ thống đang chạy, bản tinh chỉnh kém hơn 7,50 điểm (mục 5.4) | ✅ tự đo | Bỏ lại +12,46 điểm chỉ đạt được ở chế độ bỏ bước phát hiện chữ, mà chế độ đó hỏng trên ảnh toàn cảnh |
| Runtime suy luận | **ONNX Runtime** mặc định | Loại bỏ rủi ro xung đột hai framework học sâu trong một môi trường | ❌ chưa đo | Thêm một bước xuất mô hình; lợi ích tốc độ chưa tự kiểm chứng |
| Độ phân giải đầu vào | **640** | Số đo có, nhưng ba biến đổi đồng thời nên không quy kết được (mục 3.6) | ⚠️ không quy kết được | Không tách được đóng góp của riêng độ phân giải |

**Ba điều rút ra từ chương này.**

*Thứ nhất, ràng buộc phần cứng quyết định nhiều hơn chất lượng mô hình.* Ba trong sáu quyết định ở Bảng 3.6 — YOLO11n thay vì YOLO26n, v5 mobile thay vì v6 Medium, ONNX Runtime thay vì PyTorch — đều xoay quanh việc hệ thống phải chạy trên CPU. Ở một triển khai có GPU, ít nhất hai trong ba quyết định ấy phải xét lại. Đây là ranh giới áp dụng của toàn bộ chương, không phải một ghi chú phụ.

*Thứ hai, hai lựa chọn lớn nhất lại là hai lựa chọn ít bằng chứng nhất.* Việc chọn họ engine OCR và chọn runtime đều mang dấu ❌. Điều này không làm hai quyết định ấy sai — lý do vận hành đứng sau chúng là lý do thật — nhưng nó giới hạn nghiêm ngặt những gì được phép phát biểu về chúng khi bảo vệ. Cụ thể: được nói *"chọn PaddleOCR vì nhẹ và vì kiến trúc hợp với biển hai dòng"*, **không** được nói *"PaddleOCR chính xác hơn"*.

*Thứ ba, chỗ đo được lại cho kết quả trái với kỳ vọng.* Cả hai phép so sánh đồ án tự chạy đều **bác bỏ** phương án trông có vẻ tốt hơn: v6 chính xác hơn nhưng không dùng được, và bản tinh chỉnh thắng đậm ở một chế độ nhưng thua ở chế độ thật. Nếu chỉ đọc tài liệu rồi chọn theo con số cao nhất, cả hai quyết định đều sẽ sai. Đó là lập luận thực nghiệm cho chính việc phải tự đo — và là lý do hai dấu ❌ còn lại được ghi nhận thành nợ kỹ thuật ở mục 6.9.2 chứ không được bỏ qua.

---
