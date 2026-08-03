# CHƯƠNG 3. KHẢO SÁT CÔNG NGHỆ VÀ LỰA CHỌN MÔ HÌNH

## 3.1. Phương pháp khảo sát và tiêu chí lựa chọn

Mỗi lựa chọn trình bày theo cùng một khuôn: phương án đã xét, tiêu chí, kết luận, **đánh đổi phải chấp nhận**. Khi bằng chứng không đủ phân định, mục này nói rõ là không đủ.

### 3.1.1. Bốn ràng buộc chi phối mọi lựa chọn

Bốn ràng buộc sau thu hẹp không gian phương án **trước khi** so sánh — vì sao một số ứng viên mạnh bị loại sớm.

| # | Ràng buộc | Hệ quả trực tiếp lên việc chọn |
|:--:|---|---|
| 1 | **Suy luận trên CPU, không có GPU CUDA** (CON-02, mục 4.3.1) | Phương án không công bố tốc độ CPU đều **không có căn cứ để đánh giá**; mô hình hàng trăm triệu tham số loại từ đầu |
| 2 | **Biển số Việt Nam có biển hai dòng** | Engine giả định văn bản một dòng gãy ở đây; tiêu chí phân loại, không phải điểm cộng |
| 3 | **Phải đóng gói và bàn giao được** | Giấy phép, dung lượng mô hình, số phụ thuộc là tiêu chí thật |
| 4 | **Ngân sách thời gian CPU hữu hạn** | Một số phép so sánh đã thiết kế nhưng **không chạy được**; mục 3.1.2 nói rõ là những phép nào |

### 3.1.2. Ranh giới giữa cái đã đo và cái mới chỉ khảo sát tài liệu

Không phải mọi lựa chọn đều qua thực nghiệm: có phép đồ án tự chạy trên chính máy và dữ liệu của mình, có phép chỉ dựa số liệu nhà phát hành, và có phép **chưa bao giờ chạy được**.

**Bảng 3.1.** Mức bằng chứng của từng phép so sánh trong chương

| Phép so sánh | Mức bằng chứng | Trình bày ở |
|---|---|:---:|
| PP-OCRv5_mobile ↔ PP-OCRv6_medium | ✅ **Tự đo** — 200 vùng cắt biển số, cùng máy, cùng thứ tự ảnh | 3.3.2 |
| Bộ nhận dạng gốc ↔ bản tinh chỉnh | ✅ **Tự đo** — 2.801 biển có nhãn chuỗi, bốn cấu hình | 5.4 |
| YOLO11n ↔ YOLOv8n và năm thế hệ YOLO khác | 📄 **Khảo sát tài liệu** — theo benchmark chính thức của nhà phát hành, đồ án **không tự chạy lại** | 3.2 |
| PaddleOCR ↔ EasyOCR ↔ Tesseract | ✅ **Tự đo 03/08/2026** — 2.801 biển có nhãn chuỗi, ba nhánh, cùng tầng bao quanh | 3.3.3 |
| PyTorch ↔ ONNX Runtime ↔ OpenVINO | ❌ **Chưa đo** — chọn theo benchmark bên thứ ba, chưa có số tự đo | 3.4 · 5.6.3 |
| Độ phân giải 416 ↔ 640 | ⚠️ **Có số đo nhưng không quy kết được** — ba biến đổi đồng thời và ngược chiều nhau | 3.6 |

Dòng ❌ còn lại là khoản nợ thực sự, ghi nhận nhất quán ở mục 5.9.2 và Chương 6:

- **So sánh runtime chưa chạy** ⇒ chọn ONNX Runtime đứng vững nhờ **lý do vận hành** (một runtime duy nhất cho cả hai mô hình, tránh xung đột hai framework học sâu), không nhờ số liệu tốc độ tự đo.

## 3.2. Mô hình phát hiện: YOLO11

**Các phương án đã xét.** Bảy thế hệ YOLO từ YOLOv8 trở về sau — mốc chuyển sang anchor-free, có ý nghĩa trực tiếp với bài toán biển số (mục 2.3.1): YOLOv8 [49], YOLOv9 [53], YOLOv10 [46], YOLO11 [16], YOLOv12 [54], YOLOv13 [55], YOLO26 [47]. Họ two-stage (Faster R-CNN, Mask R-CNN) loại từ đầu vì chi phí tính toán không hợp ràng buộc CPU.

**Tiêu chí**, theo mức chi phối: (1) có số liệu tốc độ CPU chính thức; (2) kiến trúc hợp đối tượng nhỏ và tỷ lệ khung hình dẹt; (3) mật độ bằng chứng thực nghiệm trên bài toán biển số; (4) hệ sinh thái và giấy phép.

**Quá trình loại trừ.** **Chỉ các bản phát hành từ Ultralytics công bố tốc độ CPU**: YOLOv9 không công bố cột tốc độ nào, YOLOv10/YOLOv12/YOLOv13 chỉ công bố tốc độ GPU — bốn phiên bản bị loại vì **không có căn cứ để đánh giá** trên đúng chiều ràng buộc; YOLOv13 còn rủi ro kho mã không được tích hợp chính thức vào Ultralytics [55]. YOLOv8 bị loại vì YOLO11n **vượt trội cả hai chiều**: mAP@0.5:0.95 đạt 39,5 so với 37,3 và tốc độ CPU định dạng ONNX **56,1 ± 0,8 ms so với 80,4 ms**, nhanh hơn khoảng 30% [16], [52] — hai số đo cùng quy trình xuất mô hình nên so sánh được [94]<!-- ultralytics_2026_detecttask -->.

**Kết luận: chọn YOLO11 biến thể n (nano)**, với năm lý do: phiên bản gần đây **duy nhất có số liệu tốc độ CPU chính thức**; khối C2PSA được khẳng định cải thiện phát hiện đối tượng nhỏ và xử lý che khuất [52], đầu anchor-free giải quyết tỷ lệ khung hình ngoài phân bố COCO (mục 2.3.1); **bằng chứng thực nghiệm dày nhất trên bài toán biển số** — ít nhất ba nghiên cứu độc lập dùng YOLO11 cho ALPR đạt mAP@0.5 từ 0,906 đến 0,995 [57], [58], [95]<!-- sutikno_2025_clahe -->; hệ sinh thái trưởng thành — tích hợp chính thức trong `ultralytics`, hơn 20 định dạng xuất [96]<!-- ultralytics_2026_export -->, benchmark tự động trên CPU [97]<!-- ultralytics_2026_benchmark -->; giấy phép AGPL-3.0 miễn phí cho nghiên cứu học thuật [98]<!-- ultralytics_2026_license -->. Một nghiên cứu so sánh trực tiếp bốn bản nano trên cùng tập biển số cũng kết luận YOLO11n tối ưu [99]<!-- sciencedirect_2026_omanplates -->, nhưng **chưa kiểm chứng được toàn văn** nên chỉ là trích dẫn phụ.

**Chọn nano vì bài toán chỉ có một lớp:** số kênh đầu ra nhánh phân loại giảm từ 80 xuống 1, nhẹ đầu dự đoán và giảm chi phí NMS; kết quả mAP 99,3% của YOLOv8-s trên ba benchmark quốc tế ở trên 30 FPS củng cố hướng này [100]<!-- etasr_2025_optimizedyolov8 -->. Biến thể s giữ làm phương án leo thang.

**Đánh đổi phải chấp nhận.**

- **AGPL-3.0 kéo theo nghĩa vụ copyleft:** công bố mã nguồn tương ứng, tệp cấu hình và cả **trọng số mô hình**; điều khoản mạng khiến không né được qua API [98]. Đồ án công bố mã công khai nên chấp nhận được — thương mại hoá phải mua giấy phép; không ứng viên nào tránh được copyleft.
- **Luận cứ cải thiện đối tượng nhỏ chỉ ở mức định tính**, vì nhà phát hành không công bố AP_small tách riêng (mục 2.3.2); đồ án phải tự đo.
- **Bỏ qua YOLO26 dù trội trên giấy tờ:** mAP@0.5:0.95 đạt 40,9 (hơn 1,4 điểm), tốc độ CPU 38,9 ± 0,7 ms (nhanh hơn khoảng 30%), bỏ DFL dễ xuất và lượng tử hoá [47] — nhưng phát hành 09/2025, **chưa có tiền lệ trên bài toán biển số**, nên chọn làm phương án duy nhất là rủi ro không cần thiết. Dự kiến huấn luyện YOLO26n **song song làm đối chứng**; **lượt đối chứng này cuối cùng đã không chạy được** vì toàn bộ ngân sách CPU dồn cho lượt huấn luyện `best.pt` — ghi nhận là chưa đo ở mục 5.9.2 và chuyển thành hướng phát triển.

## 3.3. Engine nhận dạng ký tự

Đây là lựa chọn trình bày **trung thực nhất về mức độ chắc chắn**: chọn *họ engine* theo khảo sát tài liệu (3.3.1), rồi chọn *bậc mô hình* theo phép đo tự chạy (3.3.2).

### 3.3.1. PaddleOCR, EasyOCR, Tesseract — khảo sát tài liệu

**Các phương án đã xét:** tám engine — PaddleOCR, EasyOCR, Tesseract, TrOCR, docTR, MMOCR, fast-plate-ocr và RapidOCR/OnnxTR.

Bảng so sánh tám tiêu chí giữa ba ứng viên hàng đầu — kiến trúc, kích thước mô hình, tốc độ CPU, giấy phép, khả năng xử lý nhiều dòng, khả năng giới hạn tập ký tự, độ khó triển khai — ở **Phụ lục M.2**.

Bốn engine loại sớm nên không vào bảng: **TrOCR** — **ảo giác trên văn bản đa dòng** [69], quá nặng cho CPU (334 – 558 triệu tham số [68]), biến dạng tỷ lệ khung hình (mục 2.4.3g); **MMOCR** — chuỗi phụ thuộc bốn tầng, rủi ro cài đặt cao nhất trên Windows không GPU [108]<!-- openmmlab_2023_mmocrrepo -->; **fast-plate-ocr** — không có mô hình cho biển Việt Nam, kiến trúc khe cố định không xử lý được biển hai dòng nếu chưa huấn luyện lại [109]<!-- kandratavicius_2026_fastplateocr -->; **docTR** — tối ưu cho trang tài liệu, không cho ảnh crop nhỏ [110]<!-- mindee_2026_doctrmodels -->.

**Bằng chứng thực sự đứng vững cho PaddleOCR.** Hai số liệu thường được viện dẫn để chứng minh "PaddleOCR tốt cho biển số" đã **bị bác bỏ khi truy ngược nguồn gốc**: cả hai đến từ một bài báo dùng **EasyOCR**, không phải PaddleOCR [111]<!-- scirep_2024_yolov8ocr -->. Còn đứng vững: **nhẹ nhất nhóm khả dụng** — khoảng 21 MB so với khoảng 200 MB của EasyOCR; **thời gian CPU khả thi**, trên giấy có lộ trình nâng cấp — PP-OCRv6 Tiny nhanh hơn v5 mobile khoảng 3,9 lần trên CPU [112]<!-- paddlepaddle_2026_ppocrv6 -->, nhưng **lộ trình này về sau không lấy được** (mục 3.3.2); ràng buộc siêu nhẹ là chủ đích thiết kế xuyên suốt dòng PP-OCR [113]<!-- du_2020_ppocr -->, [114]<!-- du_2021_ppocrv2 -->; có bằng chứng tinh chỉnh trên biển số cho kết quả tốt [67] — tuy nhiên là **biển số Trung Quốc một dòng**; kiến trúc hai giai đoạn trả mỗi dòng một hộp; giấy phép Apache 2.0, không copyleft.

**Những gì PaddleOCR thua.** Không giới hạn được tập ký tự khi suy luận, phải tinh chỉnh mới có [105]; khó cài hơn EasyOCR vì kéo theo framework học sâu thứ hai; kém xa mô hình chuyên biệt LPTR-AFLNet — 99,37% riêng trên biển hai dòng với 2,7 triệu tham số [75] — nhưng mô hình đó không có gói cài sẵn, không có bản cho biển Việt Nam, không công bố số liệu CPU.

> ### 🎯 Kết luận trung thực — điểm quan trọng nhất của Chương 3
>
> **PaddleOCR là lựa chọn hợp lý, nhưng KHÔNG phải lựa chọn đã được chứng minh là tốt nhất cho bài toán này.** Ba điểm phải nói rõ:
>
> 1. **Tài liệu công khai không ủng hộ PaddleOCR:** hai số liệu mạnh nhất từng được viện dẫn đã bị bác bỏ, và các so sánh engine-với-engine trên ảnh biển số kiểm chứng được lại **nghiêng về EasyOCR** [115]<!-- reddy_2024_yolov8ocr -->. Đây là tình trạng **tại thời điểm chọn công nghệ**; phép đo tự chạy về sau (mục 3.3.3) nói ngược lại.
> 2. **Lý do giữ PaddleOCR là lý do kỹ thuật và vận hành, không phải độ chính xác:** nhẹ hơn EasyOCR gần 10 lần, có lộ trình tăng tốc, có bằng chứng tinh chỉnh, mạnh trên ảnh xoay.
> 3. **Không engine nào giải sẵn bài toán hai dòng.** Như đã chứng minh ở mục 2.4.3, chọn engine **không quyết định** thành bại của rủi ro R-04 — module tách và ghép dòng mới quyết định.
>
> Cách xử lý đúng ở thời điểm đó: giữ PaddleOCR làm baseline vì điểm 2, coi **EasyOCR là ứng viên ngang hàng, không phải phương án dự phòng hình thức** (Tesseract làm mốc dưới), và **để một benchmark tự chạy trên chính tập biển số Việt Nam quyết định** — benchmark đó **đã chạy ngày 03/08/2026**, kết quả ở mục 3.3.3.

**Ma trận thí nghiệm** gồm bốn trục: engine, cách xử lý biển hai dòng, có hoặc không nắn chỉnh phối cảnh, và runtime. Ba trục đầu đã chạy (mục 3.3.3); trục runtime chưa (mục 5.6.3).

### 3.3.2. PP-OCRv5 mobile so với PP-OCRv6 — đo trên máy đồ án

Mục này chọn **bậc mô hình** bên trong họ đã chọn, dựa trên số liệu **tự đo**. Quy trình đầy đủ ở `docs/reports/35-ppocrv6-evaluation.md`.

**a) Chỉ một bậc của v6 là lấy được.** Quét gói `paddleocr 3.7.0` chỉ thấy `PP-OCRv6` và cặp `PP-OCRv6_medium_det/rec` — **không có bản Tiny, không có bản Small.** Bậc hấp dẫn với hệ thống CPU là **Tiny** (0,20 giây mỗi ảnh, chính là "lộ trình trên giấy" ở mục 3.3.1); bậc duy nhất tải được là **Medium**, bậc mà chính bài báo ghi 1,40 giây mỗi ảnh — **chậm hơn** v5 mobile (0,78 giây) khoảng 1,8 lần. Lộ trình nâng cấp vì vậy **không lấy được**.

**b) Phải tự đo:** bài báo đo trên Xeon 8350C **có OpenVINO**, trên **văn bản tài liệu** — lệch cả phần cứng lẫn miền dữ liệu. Cách đo: 200 vùng cắt biển số từ tập kiểm định (`val.txt`, không tăng cường, không mảnh vụn), chạy **chỉ nhánh nhận dạng** để cô lập biến so sánh; cùng máy, cùng ảnh, cùng thứ tự.

**Bảng 3.2.** PP-OCRv6_medium_rec so với PP-OCRv5_mobile_rec, đo trên 200 vùng cắt biển số của đồ án

| Mô hình | Đúng chuỗi | Trung vị | p95 |
|---|---:|---:|---:|
| **PP-OCRv5_mobile_rec** — *đang dùng* | 134/200 = **67,0%** | **23,0 ms** | 31,9 ms |
| PP-OCRv6_medium_rec | 145/200 = **72,5%** | 386,9 ms | 429,0 ms |

**v6 Medium chính xác hơn 5,5 điểm và chậm hơn 16,8 lần.** Chiều kết quả khớp bài báo; biên độ chi phí lớn hơn nhiều tỷ lệ 1,8 lần bài báo ghi, vì bài đo có OpenVINO còn đồ án chạy PaddlePaddle thuần.

**c) Vì sao 5,5 điểm ấy vẫn không đủ.** Hệ thống đã căng độ trễ ở **cả hai đầu**: NFR-P1 đạt sàn sát nút (p95 1.143 ms, sàn 1.500 ms), NFR-P2 **đã trượt** (2,379 FPS, sàn 3). Bước OCR chiếm 108,28 ms mỗi biển (Bảng 6.19), nhánh nhận dạng chỉ khoảng 23 ms. Thay v5 bằng v6 Medium cộng thêm khoảng **364 ms mỗi biển**.

> ⚠️ **Đây là phép chiếu, không phải phép đo.** Cộng 364 ms vào p95 hiện hành cho khoảng **1.507 ms**, tức **vượt sàn 1.500 ms** và đẩy NFR-P1 từ 🟡 xuống ❌. Con số này suy ra từ độ trễ nhánh nhận dạng đo cô lập, **chưa chạy lại toàn đường ống** — muốn công bố phải đo thật. Nhưng ngay cả với sai số rộng, hướng của kết luận không đổi: NFR-P2 vốn đã trượt sàn thì chắc chắn trượt sâu hơn.

**d) Kết luận: giữ PP-OCRv5_mobile_rec.** Đây **không phải** kết luận "v6 kém hơn" — 5,5 điểm ấy là **dư địa đã định lượng** — mà là kết luận về **ràng buộc phần cứng**: bậc v6 hợp ràng buộc CPU thuần (ràng buộc số 1), Tiny, **không có trong gói**. Hai điều kiện đảo được quyết định, đều **đo được**: Tiny được phát hành vào gói pip (cải thiện *cả* độ chính xác *lẫn* độ trễ); hoặc xuất v6 Medium sang ONNX/OpenVINO với mức tăng tốc trên 8 lần (386 ms về khoảng 45 ms). Cả hai nằm trong hướng phát triển ở Chương 6.

> **Lưu ý bắt buộc khi trích bài PP-OCRv6.** Cặp *"+5,1 / +4,6 điểm"* mà bài v6 công bố được tính trên **baseline của chính nó** (v5_server 78,1% / 81,6%), không phải trên baseline trong tài liệu PaddleX (86,38% / 83,8%). Ghép hai nguồn sẽ **đảo chiều kết luận**. Trích thì phải trích kèm baseline gốc.

### 3.3.3. Benchmark ba engine trên 2.801 biển số Việt Nam — đo 03/08/2026

Mục 3.3.1 kết thúc bằng một khoản nợ: giữ PaddleOCR dựa trên lý do kỹ thuật, **không** dựa trên bằng chứng độ chính xác, trong khi tài liệu công khai nghiêng về EasyOCR. Mục này trả nợ đó. Số liệu đầy đủ ở `docs/reports/36-engine-benchmark.md`.

**a) Vì sao phép đo này khó làm đúng.** Bốn lượt chạy đầu đều cho số vô nghĩa; mỗi lượt hỏng lộ ra một điều kiện bắt buộc — truyền tên model tường minh, tắt backend oneDNN (mục 4.6.3), khôi phục tỷ lệ khung hình, lọc mảnh vụn ở mép dải ghép. Bài học chung: **phần lớn năng lực đọc biển số không nằm trong engine** mà ở tầng bao quanh nó. So sánh ba engine với ba tầng bao quanh khác nhau là đo tầng bao quanh chứ không đo engine.

**b) Thiết kế.** Cả ba engine chạy trong **đúng một tầng bao quanh** — sao đúng chuỗi bước của bộ nhận dạng bản giao hàng — trên **cùng một mảng NumPy đã chuẩn bị xong**; khác biệt duy nhất còn lại là engine. Đây cũng là bằng chứng thực nghiệm cho NFR-M5. Một chỗ cố ý không cào bằng: Tesseract chạy kèm whitelist `A-Z0-9`, vì giới hạn tập ký tự là **năng lực gốc** của nó; cắt bỏ "cho công bằng" mới là làm sai.

*Kiểm chứng harness:* nhánh có-split của PaddleOCR đo được **63,73%**, khớp **chính xác** NFR-A5 = 0,6373 công bố từ trước bằng một đường đo hoàn toàn khác — cùng một số tới bốn chữ số.

**Bảng 3.3.** So sánh ba engine OCR trên 2.801 biển số Việt Nam (567 một dòng, 2.234 hai dòng)

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

**c) PaddleOCR thắng dứt khoát — và điều này bác bỏ tài liệu công khai.** Ở cấu hình bản giao hàng, PaddleOCR đạt **68,87%**, hơn EasyOCR **54,59 điểm** và hơn Tesseract **58,59 điểm** — khoảng cách quá lớn để quy cho nhiễu. Kết luận *"tài liệu công khai không cho thấy PaddleOCR vượt EasyOCR trên ảnh biển số"* ở mục 3.3.1 **vẫn đúng về tài liệu công khai**, nhưng nay đồ án có số liệu của chính mình trên biển số Việt Nam và nó nói ngược lại. Quyết định giữ PaddleOCR nay **có thêm căn cứ độ chính xác**.

**d) Tách-rồi-ghép-ngang KHÔNG độc lập engine — kết quả bất ngờ nhất.**

| Engine | tắt split → có split | Mức tăng |
|---|---|---:|
| PaddleOCR | 28,81% → 63,73% | **+34,92 điểm** |
| EasyOCR | 6,53% → 10,35% | +3,82 điểm |
| Tesseract | 9,57% → 9,60% | **+0,03 điểm** |

Nếu cả ba cùng tăng mạnh, đóng góp kỹ thuật của đồ án sẽ độc lập với engine — một khẳng định mạnh. **Dữ liệu không cho phép nói thế.** Phát biểu đúng: tách-rồi-ghép-ngang là điều kiện **cần** để đọc biển hai dòng — nó biến bài toán đa dòng thành bài toán một dòng — nhưng **không đủ**; engine phải đủ mạnh để tận dụng dải ảnh đã ghép.

Ngược lại, **bộ luật hậu xử lý giúp cả ba** (+5,14 · +3,93 · +0,68 điểm). Đóng góp (b) của đồ án vì vậy **là** đóng góp độc lập engine, khác với tách-rồi-ghép-ngang.

**e) Tesseract không đọc được biển hai dòng.** **0,0% trên 2.234 biển hai dòng**, kể cả sau khi đã ghép thành một dòng, trong khi đọc được 47,3% biển một dòng. Đã kiểm bằng mắt để loại khả năng lỗi công cụ: nó **có** đọc ra chữ nhưng luôn kèm ký tự rác, và 700/2.801 lần trả chuỗi rỗng. Dự đoán *"Tesseract vỡ khi crop nhiều dòng"* ở mục 3.3.1 được xác nhận, ở mức nghiêm trọng hơn.

> ⚠️ **Hai điều phép đo này không trả lời.** Thứ nhất, nó đo trên **vùng biển đã cắt sẵn**; báo cáo 31 cho thấy thứ tự xếp hạng có thể **đảo ngược** trên ảnh toàn cảnh qua bộ phát hiện thật, nên kết luận chỉ áp cho tầng nhận dạng. Thứ hai, nó **không** kết luận engine nào tốt hơn nói chung — chỉ kết luận engine nào đọc biển số Việt Nam tốt hơn *bên trong tầng bao quanh của đồ án*; một hệ thống thiết kế quanh EasyOCR, với tiền xử lý riêng của nó, có thể cho số khác.

## 3.4. Runtime suy luận trên CPU: ONNX Runtime

**Các phương án đã xét:** chạy trực tiếp tệp trọng số PyTorch, ONNX Runtime, OpenVINO. **Tiêu chí:** tốc độ CPU, mức đa nền tảng, độ nặng phụ thuộc khi đóng gói, khả năng cùng tồn tại với framework khác.

**Bằng chứng định lượng.** Benchmark chính thức trên CPU laptop Intel Core i7-13700H, FP32, ảnh 640: **ONNX Runtime nhanh gấp khoảng 3,73 lần chạy trực tiếp PyTorch ở phân khúc nano — 104,61 ms giảm còn 28,02 ms** [18]<!-- ultralytics_2026_openvinoexport -->. Lợi ích lớn nhất đúng ở phân khúc nano và thu hẹp khi mô hình lớn lên.

> **Cảnh báo trích dẫn bắt buộc.** Chỉ được dùng **phần số liệu tốc độ** của bảng benchmark này. Các con số mAP đi kèm được đo trên tập `coco8` chỉ gồm **8 ảnh**, nên **vô nghĩa về mặt thống kê** và không được trích dẫn dưới bất kỳ hình thức nào.

Ba kết luận bổ sung từ cùng nguồn: **OpenVINO không phải luôn nhanh hơn** — trên CPU Intel thế hệ mới, FP32 **chậm hơn PyTorch** ở các biến thể lớn [18], hệ quả là phải **tự benchmark trên đúng máy chạy**; **FP16 vô ích trên CPU** — OpenVINO chuyển nội bộ FP16 sang FP32 [116]<!-- openvino_2025_precisioncontrol -->, benchmark xác nhận chênh dưới 1% [18]; **INT8 mới là lợi thế thực của OpenVINO** — tăng tốc 2,3 đến 3,6 lần, mất mAP tương đối 1,73 đến 2,47% [18], nhưng với CNN phải lượng tử hoá **tĩnh** kèm tập hiệu chuẩn.

**Kết luận: mặc định dùng ONNX Runtime, coi OpenVINO là phương án tối ưu bổ sung.** Ba lý do: nhanh hơn đáng kể ở đúng phân khúc; chuẩn mở, cùng một tệp mô hình phục vụ cả detection lẫn OCR; và — quan trọng nhất — **loại bỏ rủi ro xung đột giữa hai framework học sâu** (PyTorch cho YOLO, PaddlePaddle cho PaddleOCR): khi **cả hai** mô hình đều chạy bằng ONNX Runtime lúc vận hành, rủi ro này biến mất.

**Đánh đổi phải chấp nhận:** thêm một bước xuất mô hình; phải kiểm chứng tương thích gói với Python 3.13 trên Windows; và phải **đặt tường minh số luồng nội bộ** cùng **giới hạn số yêu cầu suy luận đồng thời**, vì cả ONNX Runtime lẫn PaddleOCR đều mặc định sinh số luồng bằng hoặc lớn hơn số lõi vật lý, dễ tranh chấp tài nguyên [117]<!-- onnxruntime_2025_threading -->.

## 3.5. Các lựa chọn công nghệ nền tảng khác

Phần lớn quyết định còn lại là **ràng buộc của đề bài**; ghi lại kèm lý do và đánh đổi để Chương 4 tham chiếu.

**Bảng 3.4.** Tổng hợp quyết định công nghệ nền tảng

| # | Hạng mục | Lựa chọn (phương án thay thế) | Lý do chính | Đánh đổi phải chấp nhận |
|:--:|---|---|---|---|
| 1 | Web framework backend | **FastAPI** (Django, Flask) | Tự sinh đặc tả OpenAPI — tạo sẵn một sản phẩm bàn giao; có sẵn WebSocket và tác vụ nền | Phải biết khi nào **không** dùng hàm bất đồng bộ; nguy cơ tranh chấp với luồng suy luận |
| 2 | ORM và migration | **SQLAlchemy 2.0 + Alembic** (Tortoise ORM, Peewee) | Tích hợp sâu kiểu tĩnh; lược đồ đã thay đổi nên nhu cầu migration là có thật | Đường cong học dốc nhất trong nhóm |
| 3 | Cơ sở dữ liệu | **SQLite** (PostgreSQL, MySQL) | Ghi có thể xếp hàng vì suy luận CPU mới là nút cổ chai; không thêm dịch vụ khi đóng gói | **Chỉ một tiến trình ghi tại một thời điểm**; vượt ngưỡng tải phải chuyển PostgreSQL |
| 4 | Frontend | **React + TypeScript + Vite + TailwindCSS** (Vue, Angular, Svelte) | Hệ sinh thái lớn nhất; công cụ build tiền nhiệm ngừng bảo trì; kiểu tĩnh nối tiếp từ backend | Tự lắp ghép routing, quản lý trạng thái, thành phần giao diện |
| 5 | Framework học sâu | **PyTorch** (TensorFlow) | Ultralytics khai báo PyTorch là phụ thuộc lõi — chọn YOLO11 là chọn PyTorch | Kéo theo framework học sâu **thứ hai** (PaddlePaddle) do lựa chọn OCR — giải bằng mục 3.4 |
| 6 | Đóng gói | **Docker + Compose** | Yêu cầu tái lập và khởi động bằng một lệnh | Kích thước image là rủi ro do có framework học sâu |

---

## 3.6. Độ phân giải đầu vào: 640 thay vì 416

Đồ án có sẵn hai mô hình để đối chiếu — `baseline-416-v1.pt` và `best.pt` — nhưng **phép so sánh giữa chúng không quy kết được nguyên nhân**: giữa hai lượt huấn luyện có **ba biến thay đổi đồng thời và ngược chiều nhau** (độ phân giải 416 → 640, bộ dữ liệu v1 → v3 đã khử rò rỉ, số epoch), nên chênh lệch chỉ số **không gán được cho riêng biến nào**. Điều này phải nói rõ vì bản nháp trước từng trình bày `best.pt` như mô hình "tệ hơn baseline", trong khi ở tầng phát hiện nó **vượt mọi ngưỡng NFR** (mục 5.4.1).

Lựa chọn **640** vì vậy đứng trên căn cứ khác: đó là độ phân giải mà chỉ tiêu NFR-A1/A2 đặt ra và là độ phân giải mọi số liệu tốc độ CPU chính thức của Ultralytics được đo. Muốn quy kết nguyên nhân cần một ma trận thí nghiệm cô lập từng biến (E1 – E3), ước tính **≈ 33 giờ CPU** — vượt ngân sách còn lại, ghi nhận là **chưa thực hiện** ở mục 5.9.2. Bảng đối chiếu hai mô hình và đặc tả ma trận E1 – E3 ở **Phụ lục M.3**.

---
## 3.7. Kết luận chương

**Bảng 3.5.** Tổng hợp các quyết định công nghệ và căn cứ

| Hạng mục | Quyết định | Căn cứ quyết định | Mức bằng chứng | Đánh đổi đã chấp nhận |
|---|---|---|:---:|---|
| Mô hình phát hiện | **YOLO11n** | Phiên bản gần đây duy nhất có số liệu tốc độ CPU chính thức; C2PSA hợp đối tượng nhỏ; bằng chứng ALPR dày nhất | 📄 tài liệu | AGPL-3.0 kéo theo copyleft; bỏ qua YOLO26 dù trội hơn trên giấy |
| Họ engine OCR | **PaddleOCR** | Benchmark tự chạy trên 2.801 biển Việt Nam: **68,87%** so với EasyOCR 14,28% và Tesseract 10,28% (mục 3.3.3); nhẹ hơn EasyOCR gần 10 lần; Apache 2.0 | ✅ tự đo | Kết luận chỉ áp cho **vùng biển đã cắt sẵn**; trên ảnh toàn cảnh thứ tự có thể đảo |
| Bậc mô hình OCR | **PP-OCRv5_mobile** | v6 Medium chính xác hơn 5,5 điểm nhưng chậm hơn 16,8 lần; bậc Tiny của v6 không có trong gói | ✅ tự đo | Bỏ lại 5,5 điểm độ chính xác đã định lượng được |
| Tinh chỉnh bộ nhận dạng | **Không dùng ở bản giao hàng** | Ở đúng chế độ hệ thống đang chạy, bản tinh chỉnh kém hơn 7,50 điểm (mục 4.5.3) | ✅ tự đo | Bỏ lại +12,46 điểm chỉ đạt được ở chế độ bỏ bước phát hiện chữ, mà chế độ đó hỏng trên ảnh toàn cảnh |
| Runtime suy luận | **ONNX Runtime** mặc định | Loại bỏ rủi ro xung đột hai framework học sâu trong một môi trường | ❌ chưa đo | Thêm một bước xuất mô hình; lợi ích tốc độ chưa tự kiểm chứng |
| Độ phân giải đầu vào | **640** | Số đo có, nhưng ba biến đổi đồng thời nên không quy kết được (mục 3.6) | ⚠️ không quy kết được | Không tách được đóng góp của riêng độ phân giải |

**Ba điều rút ra từ chương này.**

*Thứ nhất, ràng buộc phần cứng quyết định nhiều hơn chất lượng mô hình.* Ba trong sáu quyết định ở Bảng 3.5 — YOLO11n thay vì YOLO26n, v5 mobile thay vì v6 Medium, ONNX Runtime thay vì PyTorch — đều xoay quanh ràng buộc CPU; ở triển khai có GPU, ít nhất hai trong ba phải xét lại. Đây là ranh giới áp dụng của toàn bộ chương.

*Thứ hai, khoản nợ bằng chứng lớn nhất đã được trả, khoản còn lại thì chưa.* Lựa chọn họ engine OCR từng mang dấu ❌ suốt phần lớn thời gian làm đồ án — được nói *"chọn PaddleOCR vì nhẹ"* nhưng **không** được nói *"PaddleOCR chính xác hơn"*. Benchmark ba engine ngày 03/08/2026 đã lật dấu đó sang ✅ và cho phép phát biểu mạnh hơn, kèm đúng một giới hạn: phép đo chạy trên vùng biển đã cắt sẵn. Lựa chọn **runtime** thì vẫn mang dấu ❌ và vẫn là nợ kỹ thuật ghi ở mục 5.9.2.

*Thứ ba, chỗ đo được lại cho kết quả trái với kỳ vọng.* Cả hai phép so sánh đồ án tự chạy đều **bác bỏ** phương án trông có vẻ tốt hơn: v6 chính xác hơn nhưng không dùng được, bản tinh chỉnh thắng đậm ở một chế độ nhưng thua ở chế độ thật. Chỉ đọc tài liệu rồi chọn theo con số cao nhất thì cả hai quyết định đều sai — lập luận thực nghiệm cho việc phải tự đo, và lý do hai dấu ❌ được ghi thành nợ kỹ thuật ở mục 5.9.2.

---
