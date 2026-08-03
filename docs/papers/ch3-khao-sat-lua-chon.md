# CHƯƠNG 3. KHẢO SÁT CÔNG NGHỆ VÀ LỰA CHỌN MÔ HÌNH

## 3.1. Phương pháp khảo sát và tiêu chí lựa chọn

Mỗi lựa chọn dưới đây trình bày theo cùng một khuôn: phương án đã xét, tiêu chí, kết luận, **đánh đổi phải chấp nhận**. Khi bằng chứng không đủ phân định, mục này nói rõ là không đủ.

### 3.1.1. Bốn ràng buộc chi phối mọi lựa chọn

Bốn ràng buộc sau thu hẹp không gian phương án **trước khi** việc so sánh bắt đầu, nên giải thích vì sao một số ứng viên mạnh bị loại sớm.

| # | Ràng buộc | Hệ quả trực tiếp lên việc chọn |
|:--:|---|---|
| 1 | **Suy luận trên CPU, không có GPU CUDA** (CON-02, xem mục 4.3.1) | Mọi phương án không công bố số liệu tốc độ CPU đều **không có căn cứ để đánh giá**; các mô hình hàng trăm triệu tham số bị loại từ đầu |
| 2 | **Biển số Việt Nam có biển hai dòng** | Engine nào giả định văn bản một dòng đều gãy ở đây; đây là tiêu chí phân loại chứ không phải điểm cộng |
| 3 | **Phải đóng gói và bàn giao được** | Giấy phép, dung lượng mô hình và số lượng phụ thuộc là tiêu chí thật, không phải chi tiết phụ |
| 4 | **Ngân sách thời gian CPU hữu hạn** | Một số phép so sánh đã được thiết kế nhưng **không chạy được**; mục 3.1.2 nói rõ là những phép nào |

### 3.1.2. Ranh giới giữa cái đã đo và cái mới chỉ khảo sát tài liệu

Một chương mang tên *"khảo sát và lựa chọn"* dễ gây ấn tượng rằng mọi lựa chọn đều đã qua thực nghiệm; với đồ án này thì **không**: có phép đồ án tự chạy trên chính máy và dữ liệu của mình, có phép chỉ dựa vào số liệu nhà phát hành công bố, và có phép **chưa bao giờ chạy được**.

**Bảng 3.1.** Mức bằng chứng của từng phép so sánh trong chương

| Phép so sánh | Mức bằng chứng | Trình bày ở |
|---|---|:---:|
| PP-OCRv5_mobile ↔ PP-OCRv6_medium | ✅ **Tự đo** — 200 vùng cắt biển số của đồ án, cùng máy, cùng thứ tự ảnh | 3.3.2 |
| Bộ nhận dạng gốc ↔ bản tinh chỉnh | ✅ **Tự đo** — 2.801 biển có nhãn chuỗi, bốn cấu hình | 5.4 |
| YOLO11n ↔ YOLOv8n và năm thế hệ YOLO khác | 📄 **Khảo sát tài liệu** — dựa trên bảng benchmark chính thức của nhà phát hành, đồ án **không tự chạy lại** | 3.2 |
| PaddleOCR ↔ EasyOCR ↔ Tesseract | ✅ **Tự đo 03/08/2026** — 2.801 biển có nhãn chuỗi, ba nhánh, cùng tầng bao quanh | 3.3.3 |
| PyTorch ↔ ONNX Runtime ↔ OpenVINO | ❌ **Chưa đo** — chọn theo benchmark của bên thứ ba; Bảng 6.20 còn để trống | 3.4 · 5.6.3 |
| Độ phân giải 416 ↔ 640 | ⚠️ **Có số đo nhưng không quy kết được** — ba biến đổi đồng thời và ngược chiều nhau | 3.6 |

Dòng ❌ còn lại là khoản nợ thực sự, ghi nhận nhất quán ở mục 5.9.2 và Chương 6:

- **So sánh runtime chưa chạy** ⇒ chọn ONNX Runtime đứng vững nhờ **lý do vận hành** (một runtime duy nhất cho cả hai mô hình, tránh xung đột hai framework học sâu), không nhờ số liệu tốc độ tự đo.

## 3.2. Mô hình phát hiện: YOLO11

**Các phương án đã xét.** Bảy thế hệ YOLO từ YOLOv8 trở về sau — mốc chuyển sang anchor-free, có ý nghĩa trực tiếp với bài toán biển số (mục 2.5.2): YOLOv8 [49], YOLOv9 [53], YOLOv10 [46], YOLO11 [16], YOLOv12 [54], YOLOv13 [55], YOLO26 [47]. Họ two-stage (Faster R-CNN, Mask R-CNN) loại từ đầu vì chi phí tính toán không hợp ràng buộc CPU.

**Tiêu chí**, theo mức chi phối: (1) có số liệu tốc độ CPU chính thức hay không; (2) kiến trúc hợp đối tượng nhỏ và tỷ lệ khung hình dẹt; (3) mật độ bằng chứng thực nghiệm trên bài toán biển số; (4) hệ sinh thái và giấy phép.

**Quá trình loại trừ.** **Chỉ các bản phát hành từ Ultralytics công bố tốc độ CPU**: YOLOv9 không công bố cột tốc độ nào, YOLOv10/YOLOv12/YOLOv13 chỉ công bố tốc độ GPU — bốn phiên bản này bị loại vì **không có căn cứ để đánh giá** trên đúng chiều ràng buộc của đồ án; YOLOv13 còn có rủi ro kho mã nguồn không được tích hợp chính thức vào Ultralytics [55]. YOLOv8 bị loại vì YOLO11n **vượt trội đồng thời cả hai chiều**: mAP@0.5:0.95 đạt 39,5 so với 37,3 (hơn 2,2 điểm) và tốc độ CPU định dạng ONNX **56,1 ± 0,8 ms so với 80,4 ms**, nhanh hơn khoảng 30% [16], [52] — phép so sánh CPU hợp lệ duy nhất có sẵn, vì cả hai đo bằng cùng quy trình xuất mô hình [94]<!-- ultralytics_2026_detecttask -->.

**Kết luận: chọn YOLO11 biến thể n (nano)**, với năm lý do: là phiên bản gần đây **duy nhất có số liệu tốc độ CPU chính thức**; khối C2PSA được khẳng định cải thiện phát hiện đối tượng nhỏ và xử lý che khuất phức tạp [52], đầu anchor-free giải quyết tỷ lệ khung hình ngoài phân bố COCO (mục 2.5.2); **bằng chứng thực nghiệm dày nhất trên bài toán biển số** — ít nhất ba nghiên cứu độc lập dùng YOLO11 cho ALPR đạt mAP@0.5 từ 0,906 đến 0,995 [57], [58], [95]<!-- sutikno_2025_clahe -->; hệ sinh thái trưởng thành (tích hợp chính thức trong `ultralytics`, hơn 20 định dạng xuất [96]<!-- ultralytics_2026_export -->, benchmark tự động trên CPU [97]<!-- ultralytics_2026_benchmark -->); giấy phép AGPL-3.0 miễn phí cho nghiên cứu học thuật với điều kiện công bố mã nguồn [98]<!-- ultralytics_2026_license -->. Một nghiên cứu so sánh trực tiếp YOLOv8n, YOLOv9t, YOLOv10n và YOLO11n trên cùng tập biển số với siêu tham số đồng nhất cũng kết luận YOLO11n tối ưu nhất [99]<!-- sciencedirect_2026_omanplates -->, nhưng nguồn này **chưa kiểm chứng được toàn văn** do bị chặn truy cập nên chỉ dùng làm trích dẫn phụ.

**Chọn nano vì bài toán chỉ có một lớp:** số kênh đầu ra nhánh phân loại giảm từ 80 xuống 1, làm nhẹ đầu dự đoán và giảm chi phí NMS; một nghiên cứu đạt mAP 99,3% với YOLOv8-s trên ba benchmark quốc tế ở tốc độ trên 30 FPS, đúng kịch bản thiết bị hạn chế tài nguyên [100]<!-- etasr_2025_optimizedyolov8 -->. Biến thể s giữ làm phương án leo thang nếu nano không đạt chỉ tiêu.

**Đánh đổi phải chấp nhận.**

- **AGPL-3.0 kéo theo nghĩa vụ copyleft:** công bố toàn bộ mã nguồn tương ứng, sửa đổi, tệp cấu hình và cả **trọng số mô hình**; điều khoản mạng khiến không né được bằng cách chỉ cung cấp dịch vụ qua API [98]. Đồ án công bố mã nguồn công khai nên chấp nhận được, nhưng thương mại hoá sau này phải mua giấy phép doanh nghiệp; không ứng viên nào tránh được copyleft.
- **Luận cứ về cải thiện đối tượng nhỏ chỉ ở mức định tính**, vì nhà phát hành không công bố AP_small tách riêng (mục 2.5.3); đồ án phải tự đo để chuyển sang định lượng.
- **Bỏ qua YOLO26 dù trội trên giấy tờ:** mAP@0.5:0.95 đạt 40,9 (hơn 1,4 điểm so với YOLO11n), tốc độ CPU 38,9 ± 0,7 ms (nhanh hơn khoảng 30%), bỏ DFL giúp xuất và lượng tử hoá dễ hơn [47] — nhưng phát hành tháng 09/2025 và **chưa có tiền lệ nào trên bài toán biển số**, nên chọn làm phương án duy nhất là rủi ro không cần thiết. Dự kiến huấn luyện YOLO26n **song song làm đối chứng** trên cùng dữ liệu và siêu tham số; **lượt đối chứng này cuối cùng đã không chạy được** vì toàn bộ ngân sách CPU dồn cho lượt huấn luyện `best.pt` — ghi nhận là chưa đo ở mục 5.9.2 và chuyển thành hướng phát triển.

## 3.3. Engine nhận dạng ký tự

Đây là lựa chọn đồ án trình bày **trung thực nhất về mức độ chắc chắn**: chọn *họ engine* theo khảo sát tài liệu (3.3.1), rồi chọn *bậc mô hình* trong họ ấy theo phép đo tự chạy (3.3.2).

### 3.3.1. PaddleOCR, EasyOCR, Tesseract — khảo sát tài liệu

**Các phương án đã xét:** tám engine — PaddleOCR, EasyOCR, Tesseract, TrOCR, docTR, MMOCR, fast-plate-ocr và RapidOCR/OnnxTR.

**Bảng 3.2.** So sánh các engine OCR ứng viên

| Tiêu chí | **PaddleOCR** (PP-OCRv5 mobile) | **EasyOCR** | **Tesseract** |
|---|---|---|---|
| Kiến trúc | 2 giai đoạn: DB và SVTR-LCNet/CTC [17] | 2 giai đoạn: CRAFT và CRNN/CTC [60] | LSTM theo dòng [101]<!-- tesseract_2026_releasenotes --> |
| Kích thước mô hình | **4,7 MB det + 16 MB rec ≈ 21 MB** [102]<!-- paddlepaddle_2026_textdetection -->, [103]<!-- paddlepaddle_2026_textrecognition --> | Khoảng 200 MB | Khoảng 30 MB mô hình |
| Thời gian CPU | det 57,77 ms + rec 21,20 ms [102], [103] | Cần đo ở giai đoạn thực nghiệm | Nhanh nhất trong nhóm |
| Giấy phép | Apache 2.0 | Apache 2.0 | Apache 2.0 |
| Hỗ trợ nhiều dòng | Tự nhiên — mỗi dòng một hộp, **cần tự sắp xếp** | Tự nhiên — CRAFT tách vùng | Về lý thuyết có, thực tế kém [104]<!-- rosebrock_2021_psm --> |
| Giới hạn tập ký tự khi suy luận | **Không có** — phải tinh chỉnh [105]<!-- paddleocr_2022_discussion7515 --> | Có, tham số native [106]<!-- jaided_2025_easyocrdocs --> | **Tốt nhất** [107]<!-- rosebrock_2021_whitelist --> |
| Độ khó triển khai trên Windows + CPU | Trung bình — framework riêng | **Dễ nhất** — chỉ cần PyTorch | Cần cài binary hệ thống |

*Ghi chú bắt buộc về cột thời gian CPU: các con số của PaddleOCR đo trên Intel Xeon Gold 6271C, chế độ FP32, trên tập đánh giá nội bộ đa ngôn ngữ gồm ảnh tài liệu — **không phải ảnh biển số**.*

Bốn engine bị loại sớm nên không vào bảng: **TrOCR** (kiến trúc encoder-decoder BEiT và RoBERTa, giấy phép MIT) vì **ảo giác trên văn bản đa dòng** [69], quá nặng cho CPU — 334 – 558 triệu tham số [68], gói tải 1,3 – 2,2 GB — và biến dạng tỷ lệ khung hình (mục 2.6.3g); **MMOCR** vì chuỗi phụ thuộc bốn tầng, rủi ro cài đặt cao nhất trên Windows không GPU [108]<!-- openmmlab_2023_mmocrrepo -->; **fast-plate-ocr** vì không có mô hình cho biển số Việt Nam và kiến trúc khe cố định không xử lý được biển hai dòng nếu chưa huấn luyện lại [109]<!-- kandratavicius_2026_fastplateocr -->; **docTR** vì tối ưu cho trang tài liệu chứ không cho ảnh crop nhỏ [110]<!-- mindee_2026_doctrmodels -->.

**Bằng chứng thực sự đứng vững cho PaddleOCR.** Hai số liệu thường được viện dẫn để chứng minh "PaddleOCR tốt cho biển số" đã **bị bác bỏ khi truy ngược nguồn gốc**: cả hai đến từ một bài báo dùng **EasyOCR**, không phải PaddleOCR [111]<!-- scirep_2024_yolov8ocr -->. Còn đứng vững: **nhẹ nhất nhóm khả dụng** — khoảng 21 MB so với khoảng 200 MB của EasyOCR; **thời gian CPU khả thi** và trên giấy có lộ trình nâng cấp — PP-OCRv6 bản Tiny chỉ 1,5 triệu tham số, 0,20 giây mỗi ảnh trên CPU, nhanh hơn PP-OCRv5 mobile khoảng 3,9 lần [112]<!-- paddlepaddle_2026_ppocrv6 -->, nhưng **lộ trình này về sau không lấy được** (mục 3.3.2); **ràng buộc siêu nhẹ là chủ đích thiết kế xuyên suốt của dòng PP-OCR** [113]<!-- du_2020_ppocr -->, [114]<!-- du_2021_ppocrv2 -->; **có bằng chứng tinh chỉnh trên biển số cho kết quả tốt** — recognition từ 90,97% lên 94,54%, detection Hmean từ 76,12% lên 99,00% [67], tuy nhiên đây là **biển số Trung Quốc một dòng**; **kiến trúc hai giai đoạn trả mỗi dòng một hộp**; **giấy phép Apache 2.0**, không copyleft.

**Những gì PaddleOCR thua.** Không có cơ chế giới hạn tập ký tự khi suy luận, phải tinh chỉnh mới có [105]; khó cài hơn EasyOCR vì kéo theo framework học sâu thứ hai bên cạnh PyTorch; kém xa mô hình chuyên biệt như LPTR-AFLNet vốn đạt 99,37% riêng trên biển hai dòng với chỉ 2,7 triệu tham số [75] — nhưng mô hình đó không có gói cài đặt sẵn, không có bản cho biển số Việt Nam và không công bố số liệu CPU.

> ### 🎯 Kết luận trung thực — điểm quan trọng nhất của Chương 3
>
> **PaddleOCR là lựa chọn hợp lý, nhưng KHÔNG phải lựa chọn đã được chứng minh là tốt nhất cho bài toán này.** Ba điểm phải nói rõ:
>
> 1. **Tài liệu công khai không ủng hộ PaddleOCR:** hai số liệu mạnh nhất từng được viện dẫn đã bị bác bỏ, và các so sánh engine-với-engine trên ảnh biển số mà khảo sát kiểm chứng được lại **nghiêng về EasyOCR** [115]<!-- reddy_2024_yolov8ocr -->. Đây là tình trạng bằng chứng **tại thời điểm chọn công nghệ**; mục 3.3.3 trình bày phép đo mà đồ án tự chạy về sau, và nó nói ngược lại.
> 2. **Lý do giữ PaddleOCR là lý do kỹ thuật và vận hành, không phải độ chính xác:** nhẹ hơn EasyOCR gần 10 lần, có lộ trình tăng tốc, có bằng chứng tinh chỉnh, mạnh trên ảnh xoay.
> 3. **Không engine nào giải sẵn bài toán hai dòng.** Như đã chứng minh ở mục 2.6.3, việc chọn engine **không quyết định** thành bại của rủi ro R-04 — module tách và ghép dòng mới quyết định.
>
> Cách xử lý đúng ở thời điểm đó: giữ PaddleOCR làm baseline vì lý do ở điểm 2, coi **EasyOCR là ứng viên ngang hàng, không phải phương án dự phòng hình thức** (Tesseract làm mốc so sánh dưới), và **để một benchmark tự chạy trên chính tập biển số Việt Nam quyết định**. Benchmark đó **đã chạy ngày 03/08/2026** — kết quả ở mục 3.3.3.

**Ma trận thí nghiệm** gồm bốn trục: engine, cách xử lý biển hai dòng, có hoặc không nắn chỉnh phối cảnh, và runtime. Ba trục đầu đã chạy (mục 3.3.3); trục runtime chưa (mục 5.6.3).

### 3.3.2. PP-OCRv5 mobile so với PP-OCRv6 — đo trên máy đồ án

Mục này chọn **bậc mô hình** bên trong họ đã chọn, dựa trên số liệu đồ án **tự đo**. Quy trình đo đầy đủ ở `docs/reports/35-ppocrv6-evaluation.md`.

**a) Chỉ một bậc của v6 là lấy được.** Quét toàn bộ gói `paddleocr 3.7.0` đã cài chỉ tìm thấy ba định danh v6: `PP-OCRv6`, `PP-OCRv6_medium_det` và `PP-OCRv6_medium_rec` — **không có bản Tiny, không có bản Small.** Đây là điểm quyết định chứ không phải chi tiết đóng gói: bậc hấp dẫn với hệ thống chạy CPU là **Tiny**, bậc mà bài báo ghi 0,20 giây mỗi ảnh, nhanh hơn PP-OCRv5 mobile (0,78 giây) khoảng 3,9 lần — cũng đúng là "lộ trình nâng cấp trên giấy" từng viện dẫn ở mục 3.3.1. Bậc duy nhất tải được lại là **Medium**, bậc mà chính bài báo ấy ghi 1,40 giây mỗi ảnh, tức **chậm hơn** v5 mobile khoảng 1,8 lần. Lộ trình nâng cấp vì vậy **không lấy được**.

**b) Phải tự đo, vì số của bài báo không trả lời đúng câu hỏi:** bài báo đo trên Intel Xeon 8350C **có OpenVINO** và trên **văn bản tài liệu**, không phải biển số — cả phần cứng lẫn miền dữ liệu đều lệch khỏi điều kiện của đồ án. Cách đo: 200 vùng cắt biển số nguyên ảnh lấy từ tập kiểm định (`val.txt`, không tăng cường, không mảnh vụn), chạy **chỉ nhánh nhận dạng** để cô lập đúng biến đang so sánh; cùng máy, cùng ảnh, cùng thứ tự.

**Bảng 3.3.** PP-OCRv6_medium_rec so với PP-OCRv5_mobile_rec, đo trên 200 vùng cắt biển số của đồ án

| Mô hình | Đúng chuỗi | Trung vị | p95 |
|---|---:|---:|---:|
| **PP-OCRv5_mobile_rec** — *đang dùng* | 134/200 = **67,0%** | **23,0 ms** | 31,9 ms |
| PP-OCRv6_medium_rec | 145/200 = **72,5%** | 386,9 ms | 429,0 ms |

**v6 Medium chính xác hơn 5,5 điểm và chậm hơn 16,8 lần.** Chiều kết quả khớp bài báo, nhưng biên độ chi phí trên máy này lớn hơn nhiều so với tỷ lệ 1,8 lần bài báo ghi, vì bài đo có OpenVINO còn đồ án chạy PaddlePaddle thuần.

**c) Vì sao 5,5 điểm ấy vẫn không đủ.** Hệ thống đã căng độ trễ ở **cả hai đầu**: NFR-P1 đạt sàn sát nút (p95 1.143 ms, sàn 1.500 ms) và NFR-P2 thì **đã trượt** (2,379 FPS, sàn 3). Bước OCR chiếm 108,28 ms mỗi biển (Bảng 6.19), trong đó nhánh nhận dạng chỉ khoảng 23 ms — phần còn lại là bước phát hiện chữ. Thay v5 bằng v6 Medium cộng thêm khoảng **364 ms mỗi biển**.

> ⚠️ **Đây là phép chiếu, không phải phép đo.** Cộng 364 ms vào p95 hiện hành cho khoảng **1.507 ms**, tức **vượt sàn 1.500 ms** và đẩy NFR-P1 từ 🟡 xuống ❌. Con số này suy ra từ độ trễ nhánh nhận dạng đo cô lập, **chưa chạy lại toàn đường ống** — muốn công bố phải đo thật. Nhưng ngay cả với sai số rộng, hướng của kết luận không đổi: NFR-P2 vốn đã trượt sàn thì chắc chắn trượt sâu hơn.

**d) Kết luận: giữ PP-OCRv5_mobile_rec.** Đây **không phải** kết luận "v6 kém hơn" — 5,5 điểm ấy là **dư địa đã định lượng** — mà là kết luận về **ràng buộc phần cứng**: hệ thống chạy CPU thuần (ràng buộc số 1, mục 3.1.1) và bậc v6 hợp ràng buộc đó, Tiny, **không có trong gói**. Hai điều kiện đảo được quyết định này, cả hai đều **đo được**: PaddleOCR phát hành bậc Tiny vào gói pip (nhanh hơn v5 mobile 3,9 lần, tức cải thiện *cả* độ chính xác *lẫn* độ trễ); hoặc xuất được v6 Medium sang ONNX/OpenVINO với mức tăng tốc trên 8 lần, khi đó 386 ms về khoảng 45 ms. Cả hai nằm trong hướng phát triển ở Chương 6.

> **Lưu ý bắt buộc khi trích bài PP-OCRv6.** Cặp *"+5,1 / +4,6 điểm"* mà bài v6 công bố được tính trên **baseline của chính nó** (v5_server 78,1% / 81,6%), không phải trên baseline trong tài liệu PaddleX (86,38% / 83,8%). Ghép hai nguồn sẽ **đảo chiều kết luận**. Trích thì phải trích kèm baseline gốc.

### 3.3.3. Benchmark ba engine trên 2.801 biển số Việt Nam — đo 03/08/2026

Mục 3.3.1 kết thúc bằng một khoản nợ: quyết định giữ PaddleOCR dựa trên lý do kỹ thuật, **không** dựa trên bằng chứng độ chính xác, và tài liệu công khai thậm chí nghiêng về EasyOCR. Mục này trả nợ đó. Số liệu đầy đủ ở `docs/reports/36-engine-benchmark.md`.

**a) Vì sao phép đo này khó làm đúng.** Bốn lượt chạy đầu đều cho số vô nghĩa, và mỗi lượt hỏng chỉ ra một điều kiện bắt buộc: PaddleOCR 3.7 âm thầm nạp PP-OCRv6_medium nếu chỉ truyền một tên model; backend oneDNN làm sập suy luận (mục 4.6.3); thiếu bước khôi phục tỷ lệ khung hình thì **cả ba** engine đọc ra ~0%; và thiếu bộ lọc mảnh vụn thì PaddleOCR tụt từ 65% xuống 40% vì mảnh rác ở mép dải ghép.

Bài học chung: **phần lớn năng lực đọc biển số không nằm trong engine** mà nằm ở tầng bao quanh nó. So sánh ba engine với ba tầng bao quanh khác nhau là đo tầng bao quanh chứ không đo engine.

**b) Thiết kế.** Cả ba engine chạy trong **đúng một tầng bao quanh** — sao đúng chuỗi bước của bộ nhận dạng bản giao hàng — trên **cùng một mảng NumPy đã chuẩn bị xong**. Khác biệt duy nhất còn lại là engine. Đây cũng là bằng chứng thực nghiệm cho NFR-M5. Một chỗ cố ý không cào bằng: Tesseract chạy kèm whitelist `A-Z0-9` vì giới hạn tập ký tự là **năng lực gốc** của nó mà hai engine kia không có; cắt bỏ "cho công bằng" mới là làm sai.

*Kiểm chứng harness:* PaddleOCR nhánh có-split đo được **63,73%**, khớp **chính xác** NFR-A5 = 0,6373 mà quyển công bố từ trước bằng một đường đo hoàn toàn khác. Hai đường độc lập, cùng một số tới bốn chữ số.

**Bảng 3.5.** So sánh ba engine OCR trên 2.801 biển số Việt Nam (567 một dòng, 2.234 hai dòng)

| Engine | Nhánh | Toàn bộ | 1 dòng | 2 dòng | CER | Rỗng | p50 |
|---|---|---:|---:|---:|---:|---:|---:|
| **PaddleOCR** | tắt split | 28,81% | 94,2% | 12,2% | 0,588 | 6 | 295 ms |
| **PaddleOCR** | có split | **63,73%** | 94,2% | 56,0% | 0,094 | 11 | 405 ms |
| **PaddleOCR** | + hậu xử lý | **68,87%** | **94,9%** | **62,3%** | **0,089** | 11 | 402 ms |
| EasyOCR | tắt split | 6,53% | 15,3% | 4,3% | 0,647 | 4 | 84 ms |
| EasyOCR | có split | 10,35% | 15,3% | 9,1% | 0,282 | 1 | 248 ms |
| EasyOCR | + hậu xử lý | 14,28% | 28,6% | 10,7% | 0,269 | 1 | 249 ms |
| Tesseract | tắt split | 9,57% | 47,3% | **0,0%** | 0,777 | 960 | 101 ms |
| Tesseract | có split | 9,60% | 47,3% | **0,0%** | 0,565 | 700 | 108 ms |
| Tesseract | + hậu xử lý | 10,28% | 50,4% | **0,1%** | 0,567 | 700 | 106 ms |

**c) PaddleOCR thắng dứt khoát — và điều này bác bỏ tài liệu công khai.** Ở cấu hình bản giao hàng, PaddleOCR đạt **68,87%**, hơn EasyOCR **54,59 điểm** và hơn Tesseract **58,59 điểm**. Khoảng cách quá lớn để quy cho nhiễu. Câu ở mục 3.3.1 — *"không tồn tại số liệu công khai nào cho thấy PaddleOCR vượt EasyOCR trên ảnh biển số"* — **vẫn đúng về tài liệu công khai**, nhưng nay đồ án có số liệu của chính mình trên biển số Việt Nam và nó nói ngược lại. Quyết định giữ PaddleOCR, vốn chỉ dựa trên lý do kỹ thuật, nay **có thêm căn cứ độ chính xác**.

**d) Tách-rồi-ghép-ngang KHÔNG độc lập engine — kết quả bất ngờ nhất.**

| Engine | tắt split → có split | Mức tăng |
|---|---|---:|
| PaddleOCR | 28,81% → 63,73% | **+34,92 điểm** |
| EasyOCR | 6,53% → 10,35% | +3,82 điểm |
| Tesseract | 9,57% → 9,60% | **+0,03 điểm** |

Nếu cả ba cùng tăng mạnh thì đóng góp kỹ thuật của đồ án sẽ độc lập với engine — một khẳng định mạnh. **Dữ liệu không cho phép nói thế.** Phát biểu đúng và dè dặt hơn: tách-rồi-ghép-ngang là điều kiện **cần** để đọc biển hai dòng — nó biến bài toán đa dòng thành bài toán một dòng — nhưng **không đủ**; engine phải đủ mạnh để tận dụng dải ảnh đã ghép.

Ngược lại, **bộ luật hậu xử lý giúp cả ba** (+5,14 · +3,93 · +0,68 điểm). Đóng góp (b) của đồ án vì vậy **là** đóng góp độc lập engine, khác với tách-rồi-ghép-ngang.

**e) Tesseract không đọc được biển hai dòng.** **0,0% trên 2.234 biển hai dòng**, kể cả sau khi đã ghép thành một dòng, trong khi đọc được 47,3% biển một dòng. Đã kiểm bằng mắt để loại khả năng lỗi công cụ: nó **có** đọc ra chữ nhưng luôn kèm ký tự rác — `59L214999` → `B507B149991` — và 700/2.801 lần trả chuỗi rỗng. Mục 3.3.1 đã dự đoán *"Tesseract vỡ khi crop nhiều dòng"* dựa trên tài liệu; phép đo xác nhận, ở mức nghiêm trọng hơn dự đoán.

> ⚠️ **Hai điều phép đo này không trả lời.** Thứ nhất, nó đo trên **vùng biển đã cắt sẵn**; báo cáo 31 cho thấy thứ tự xếp hạng có thể **đảo ngược** trên ảnh toàn cảnh qua bộ phát hiện thật, nên kết luận chỉ áp cho tầng nhận dạng. Thứ hai, nó **không** kết luận engine nào tốt hơn nói chung — chỉ kết luận engine nào đọc biển số Việt Nam tốt hơn *bên trong tầng bao quanh của đồ án*; một hệ thống thiết kế quanh EasyOCR, với tiền xử lý riêng của nó, có thể cho số khác.

## 3.4. Runtime suy luận trên CPU: ONNX Runtime

**Các phương án đã xét:** chạy trực tiếp tệp trọng số PyTorch, ONNX Runtime, OpenVINO. **Tiêu chí:** tốc độ trên CPU, mức đa nền tảng, độ nặng phụ thuộc khi đóng gói, khả năng cùng tồn tại với framework khác.

**Bằng chứng định lượng.** Benchmark chính thức trên CPU laptop Intel Core i7-13700H, chế độ FP32, kích thước ảnh 640: **ONNX Runtime nhanh gấp khoảng 3,73 lần so với chạy trực tiếp PyTorch ở phân khúc nano — 104,61 ms giảm còn 28,02 ms** [18]<!-- ultralytics_2026_openvinoexport -->. Lợi ích lớn nhất đúng ở phân khúc đồ án dùng và thu hẹp dần khi mô hình lớn lên.

> **Cảnh báo trích dẫn bắt buộc.** Chỉ được dùng **phần số liệu tốc độ** của bảng benchmark này. Các con số mAP đi kèm trong bảng gốc được đo trên tập `coco8` chỉ gồm **8 ảnh**, nên **vô nghĩa về mặt thống kê** và không được trích dẫn dưới bất kỳ hình thức nào.

Ba kết luận bổ sung từ cùng nguồn. **OpenVINO không phải luôn nhanh hơn:** trên CPU Intel thế hệ mới, OpenVINO ở FP32 **chậm hơn PyTorch** ở các biến thể lớn, do PyTorch hiện đại đã tối ưu tốt thư viện tính toán trên CPU mới [18] — hệ quả bắt buộc là phải **tự benchmark trên đúng máy chạy**, không tin số liệu chung. **FP16 hoàn toàn vô ích trên CPU:** OpenVINO chuyển nội bộ toàn bộ giá trị FP16 sang FP32 và tính ở FP32 [116]<!-- openvino_2025_precisioncontrol -->, benchmark xác nhận chênh lệch dưới 1% [18], FP16 chỉ giảm một nửa dung lượng lưu trữ — nên bỏ qua FP16, đi thẳng từ FP32 sang INT8 nếu cần thêm tốc độ. **Lượng tử hoá INT8 là lợi thế thực sự của OpenVINO:** tăng tốc 2,3 đến 3,6 lần với mất mát mAP tương đối chỉ 1,73 đến 2,47% [18]; tuy nhiên với CNN phải dùng lượng tử hoá **tĩnh** kèm tập hiệu chuẩn, và cần kiểm tra CPU có hỗ trợ tập lệnh phù hợp.

**Kết luận: mặc định dùng ONNX Runtime, coi OpenVINO là phương án tối ưu bổ sung.** Ba lý do: nhanh hơn đáng kể so với chạy trực tiếp tệp PyTorch ở đúng phân khúc đồ án dùng; là chuẩn mở không ràng buộc nhà sản xuất CPU, cùng một tệp mô hình phục vụ cả khối detection lẫn khối OCR; và — có thể là lý do quan trọng nhất — **loại bỏ hoàn toàn rủi ro xung đột giữa hai framework học sâu**, vì đồ án dùng PyTorch cho YOLO và PaddlePaddle cho PaddleOCR, còn nếu **cả hai** mô hình đều chạy bằng ONNX Runtime khi vận hành thì rủi ro này biến mất.

**Đánh đổi phải chấp nhận:** thêm một bước xuất mô hình; phải kiểm chứng tương thích của gói cài đặt với Python 3.13 trên Windows; và phải **đặt tường minh số luồng nội bộ** đồng thời với **giới hạn số yêu cầu suy luận đồng thời** ở tầng ứng dụng, vì cả ONNX Runtime lẫn PaddleOCR đều mặc định sinh số luồng bằng hoặc lớn hơn số lõi vật lý, dễ gây tranh chấp tài nguyên [117]<!-- onnxruntime_2025_threading -->.

## 3.5. Các lựa chọn công nghệ nền tảng khác

Phần lớn các quyết định còn lại là **ràng buộc của đề bài** chứ không phải lựa chọn tự do; ghi lại kèm lý do và đánh đổi để Chương 4 có căn cứ tham chiếu.

**Bảng 3.4.** Tổng hợp quyết định công nghệ nền tảng

| # | Hạng mục | Lựa chọn (phương án thay thế) | Lý do chính | Đánh đổi phải chấp nhận |
|:--:|---|---|---|---|
| 1 | Web framework backend | **FastAPI** (Django, Flask) | Tự sinh đặc tả OpenAPI nên tạo sẵn một sản phẩm bàn giao; có sẵn WebSocket và tác vụ nền | Phải biết khi nào **không** dùng hàm bất đồng bộ; nguy cơ tranh chấp luồng với luồng suy luận |
| 2 | ORM và migration | **SQLAlchemy 2.0 + Alembic** (Tortoise ORM, Peewee) | Tích hợp sâu hệ thống kiểu tĩnh; lược đồ đã thay đổi một lần nên nhu cầu migration là có thật | Đường cong học dốc nhất trong nhóm |
| 3 | Cơ sở dữ liệu | **SQLite** (PostgreSQL, MySQL) | Ghi có thể xếp hàng vì suy luận CPU mới là nút cổ chai; không thêm dịch vụ khi đóng gói | **Chỉ một tiến trình ghi tại một thời điểm**; phải chuyển sang PostgreSQL nếu vượt ngưỡng tải |
| 4 | Frontend | **React + TypeScript + Vite + TailwindCSS** (Vue, Angular, Svelte) | Hệ sinh thái lớn nhất; công cụ build tiền nhiệm đã ngừng bảo trì; kiểu tĩnh nối tiếp từ backend sang client | Tự lắp ghép routing, quản lý trạng thái và thành phần giao diện |
| 5 | Framework học sâu | **PyTorch** (TensorFlow) | Ultralytics khai báo PyTorch là phụ thuộc lõi, nên chọn YOLO11 là chọn PyTorch | Kéo theo framework học sâu **thứ hai** (PaddlePaddle) do lựa chọn OCR — giải bằng quyết định ở mục 3.4 |
| 6 | Đóng gói | **Docker + Compose** | Yêu cầu tái lập và khởi động bằng một lệnh | Kích thước image là rủi ro do có framework học sâu |

---

## 3.6. Khảo sát ảnh hưởng của độ phân giải và chất lượng split

Đồ án có hai mô hình đã huấn luyện: `baseline-416-v1.pt` và `best.pt`. So sánh chúng là tự nhiên, nhưng **phải rất thận trọng về phương pháp luận**, vì lý do ngay dưới bảng.

<!-- {{T3.6}} so sanh baseline 416/v1 voi mo hinh chinh thuc 640/v3 -->

**Bảng 3.5.** So sánh `baseline-416-v1.pt` với `best.pt` — ba biến thay đổi đồng thời

| Hạng mục | `baseline-416-v1.pt` | `best.pt` (chính thức) | Chênh lệch |
|---|---:|---:|---:|
| **Cấu hình** | | | |
| `imgsz` | 416 | **640** | +224 px |
| Bộ dữ liệu | v1 — 4.578 ảnh, 1 nguồn | **v3 — 15.133 ảnh, 6 nguồn nguyên tố (hợp nhất từ 7 bộ)** | ×3,3 |
| Ngưỡng gộp trùng lặp | 5 | **10** | +5 |
| Rò rỉ train↔test (ngưỡng 10) | **619 cặp** | **0 cặp** *(hệ quả định nghĩa, xem T5.3b)* | |
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

> ⚠ Ba biến thay đổi đồng thời (imgsz, bộ dữ liệu + cách chia, số epoch) và chúng tác động **ngược chiều** nhau — không được quy kết nguyên nhân cho bất kỳ biến nào (xem 3.6.1). Dòng độ trễ E2E dùng con số **client-side đã xác minh** cho **cả hai** mô hình (763,75 ms và 731,15 ms, máy rảnh, qua HTTP); con số 5.857,19 ms từng ghi cho baseline ở báo cáo Phase 7 đã bị **bác bỏ** vì nhiễm tranh chấp CPU và đo sai checkpoint (mục 5.6.1). Đo cùng phương pháp trên máy rảnh, hai mô hình cho độ trễ gần như y hệt.

### 3.6.1. Vì sao so sánh này không quy kết được nguyên nhân

**So sánh này có ít nhất ba biến cùng thay đổi**, và chúng tác động **ngược chiều nhau**:

| Biến thay đổi | Baseline | Chính thức | Hướng ảnh hưởng dự kiến |
|---|---|---|---|
| Độ phân giải đầu vào | 416 | 640 | Tăng độ phân giải → dự kiến **cải thiện**, nhất là với đối tượng nhỏ |
| Bộ dữ liệu và cách chia | v1, có rò rỉ | v3, ngưỡng gộp chặt hơn | Khử rò rỉ → dự kiến **làm giảm** chỉ số đo được, vì chỉ số cũ bị thổi phồng |
| Số epoch | 40 | 20 | Ít epoch hơn → dự kiến **làm giảm**, nếu chưa hội tụ |

Do đó phát biểu duy nhất được phép là mô tả: *"cấu hình A cho kết quả X, cấu hình B cho kết quả Y, ba biến thay đổi đồng thời nên không tách được đóng góp của từng biến."*

**Kết quả thực tế: `best.pt` cho mAP@0.5:0.95 = 0,7834, thấp hơn baseline 0,8597 đúng 7,63 điểm** (mAP@0.5 cũng thấp hơn 1,04 điểm) — và đây là kết quả *có giá trị* chứ không phải một sự thụt lùi. Baseline được huấn luyện và đánh giá trên split v1, split **có rò rỉ** (619 cặp gần trùng train↔test ở ngưỡng 10), nên mô hình *ghi nhớ* thay vì *tổng quát hoá* và con số 0,8597 **bị thổi phồng**; `best.pt` được đánh giá trên split v3 đã siết khử trùng lặp (0 cặp ở ngưỡng gộp), nên 0,7834 phản ánh năng lực tổng quát hoá **trung thực hơn** dù trị số thấp hơn. Đây là nghịch lý cốt lõi cần trình bày khi bảo vệ: **một con số thấp hơn nhưng đo đúng có giá trị hơn một con số cao hơn nhưng đo trên tập bị rò rỉ.** Không được kết luận mạnh hơn (ví dụ "toàn bộ 7,63 điểm là do khử rò rỉ") vì `imgsz` tăng và số epoch giảm cũng tác động — và nếu kết quả đi chiều ngược lại thì cũng **không** được quy kết riêng cho `imgsz`, vì lượng dữ liệu đã tăng 3,3 lần đồng thời. Ngược lại, tuyệt đối không được trình bày `best.pt` như một mô hình "tệ hơn baseline": ở tầng phát hiện nó vẫn **vượt mọi ngưỡng NFR** (mục 5.4.1).

### 3.6.2. Thí nghiệm cô lập biến — đề xuất, chưa thực hiện

Muốn quy kết nguyên nhân cho từng biến, cần một ma trận thí nghiệm cô lập:

| Thí nghiệm | `imgsz` | Bộ dữ liệu | Mục đích | Chi phí ước tính (CPU) | Trạng thái |
|:---:|:---:|:---:|---|---:|:---:|
| E1 | 416 | v3 | Cô lập ảnh hưởng của **độ phân giải** (so với `best.pt`) | ≈ 5 giờ | ⬜ chưa chạy |
| E2 | 640 | v1 | Cô lập ảnh hưởng của **chất lượng bộ dữ liệu** | ≈ 4 giờ | ⬜ chưa chạy |
| E3 | 640 | v3, 40 epoch | Cô lập ảnh hưởng của **số epoch** | ≈ 24 giờ | ⬜ chưa chạy |

Ba thí nghiệm này **không được thực hiện** trong khuôn khổ đồ án, vì tổng chi phí khoảng 33 giờ CPU liên tục vượt quá ngân sách thời gian còn lại; ghi nhận chúng kèm chi phí ước tính trung thực hơn là im lặng về giới hạn của phép so sánh ở mục 3.6, đồng thời là một hướng phát triển cụ thể cho Chương 6.

## 3.7. Kết luận chương

**Bảng 3.6.** Tổng hợp các quyết định công nghệ và căn cứ

| Hạng mục | Quyết định | Căn cứ quyết định | Mức bằng chứng | Đánh đổi đã chấp nhận |
|---|---|---|:---:|---|
| Mô hình phát hiện | **YOLO11n** | Phiên bản gần đây duy nhất có số liệu tốc độ CPU chính thức; khối C2PSA hợp đối tượng nhỏ; bằng chứng ALPR dày nhất | 📄 tài liệu | AGPL-3.0 kéo theo nghĩa vụ copyleft; bỏ qua YOLO26 dù trội hơn trên giấy |
| Họ engine OCR | **PaddleOCR** | Nhẹ hơn EasyOCR gần 10 lần; kiến trúc hai giai đoạn trả mỗi dòng một hộp; Apache 2.0 | ❌ chưa đo | **Không chứng minh được là chính xác hơn EasyOCR** |
| Bậc mô hình OCR | **PP-OCRv5_mobile** | v6 Medium chính xác hơn 5,5 điểm nhưng chậm hơn 16,8 lần; bậc Tiny của v6 không có trong gói | ✅ tự đo | Bỏ lại 5,5 điểm độ chính xác đã định lượng được |
| Tinh chỉnh bộ nhận dạng | **Không dùng ở bản giao hàng** | Ở đúng chế độ hệ thống đang chạy, bản tinh chỉnh kém hơn 7,50 điểm (mục 4.5.3) | ✅ tự đo | Bỏ lại +12,46 điểm chỉ đạt được ở chế độ bỏ bước phát hiện chữ, mà chế độ đó hỏng trên ảnh toàn cảnh |
| Runtime suy luận | **ONNX Runtime** mặc định | Loại bỏ rủi ro xung đột hai framework học sâu trong một môi trường | ❌ chưa đo | Thêm một bước xuất mô hình; lợi ích tốc độ chưa tự kiểm chứng |
| Độ phân giải đầu vào | **640** | Số đo có, nhưng ba biến đổi đồng thời nên không quy kết được (mục 3.6) | ⚠️ không quy kết được | Không tách được đóng góp của riêng độ phân giải |

**Ba điều rút ra từ chương này.**

*Thứ nhất, ràng buộc phần cứng quyết định nhiều hơn chất lượng mô hình.* Ba trong sáu quyết định ở Bảng 3.6 — YOLO11n thay vì YOLO26n, v5 mobile thay vì v6 Medium, ONNX Runtime thay vì PyTorch — đều xoay quanh việc hệ thống phải chạy trên CPU; ở một triển khai có GPU, ít nhất hai trong ba phải xét lại. Đây là ranh giới áp dụng của toàn bộ chương.

*Thứ hai, hai lựa chọn lớn nhất lại là hai lựa chọn ít bằng chứng nhất.* Chọn họ engine OCR và chọn runtime đều mang dấu ❌ — không làm hai quyết định ấy sai, nhưng giới hạn nghiêm ngặt những gì được phát biểu khi bảo vệ: được nói *"chọn PaddleOCR vì nhẹ và vì kiến trúc hợp với biển hai dòng"*, **không** được nói *"PaddleOCR chính xác hơn"*.

*Thứ ba, chỗ đo được lại cho kết quả trái với kỳ vọng.* Cả hai phép so sánh đồ án tự chạy đều **bác bỏ** phương án trông có vẻ tốt hơn: v6 chính xác hơn nhưng không dùng được, và bản tinh chỉnh thắng đậm ở một chế độ nhưng thua ở chế độ thật. Chỉ đọc tài liệu rồi chọn theo con số cao nhất thì cả hai quyết định đều sai — đó là lập luận thực nghiệm cho việc phải tự đo, và là lý do hai dấu ❌ còn lại được ghi nhận thành nợ kỹ thuật ở mục 5.9.2 chứ không được bỏ qua.

---
