# CHƯƠNG 2. CƠ SỞ LÝ THUYẾT

Chương đặt nền lý thuyết và tư liệu cho phần thiết kế. Nguyên tắc xuyên suốt: **mọi con số gắn nguồn tại chỗ, mọi cảnh báo về phạm vi áp dụng giữ nguyên** — lĩnh vực này hay công bố số trên 99% nhưng đo trên tập dữ liệu và giao thức rất khác nhau.

## 2.1. Phạm vi và bố cục cơ sở lý thuyết

Một hệ thống ALPR gồm bốn khối nối tiếp — **phát hiện vùng biển**, **nắn chỉnh và tiền xử lý**, **nhận dạng ký tự**, **hậu xử lý theo quy chuẩn** — và độ chính xác cuối cùng là **tích** của độ chính xác từng khối, nên một khối yếu kéo cả chuỗi xuống. Đồ án đi theo hướng **two-stage** (phát hiện rồi nhận dạng riêng) kết hợp bộ nhận dạng **segmentation-free**; căn cứ của lựa chọn đó trình bày ở Chương 3.

Chương chỉ giữ phần lý thuyết **ràng buộc trực tiếp một quyết định của hệ thống**: quy chuẩn biển số Việt Nam (2.2), kiến trúc YOLO11 và các chỉ số đánh giá khối phát hiện (2.3), kiến trúc CRNN/CTC cùng **giới hạn của nó trên văn bản nhiều dòng** (2.4), và khảo sát công trình liên quan cùng sáu khoảng trống nghiên cứu (2.5).

## 2.2. Quy chuẩn biển số xe Việt Nam

Quy chuẩn biển số Việt Nam — bốn văn bản căn cứ, cấu trúc chuỗi ký tự và bảng mã tỉnh — đã trình bày ở **mục 1.1.3(b)**; danh sách 81 mã đang dùng ở **Phụ lục I**. Mục này chỉ khai triển ba đặc điểm mà thiết kế hệ thống dựa trực tiếp vào: tập ký tự sê-ri phụ thuộc vị trí, màu nền, và tỉ lệ khung hình.

### 2.2.1. Tập ký tự seri và các chữ cái bị loại trừ

Biển trắng và vàng chữ đen dùng seri gồm **một trong 20 chữ cái** [7], nhưng danh sách ấy **chỉ áp dụng cho vị trí thứ nhất**: vị trí thứ hai của seri xe máy dùng một tập khác — **có `R`, không có `G`**. Hợp cả hai vị trí, tập chữ cái không bao giờ xuất hiện trên biển số Việt Nam chỉ gồm **5 chữ `I`, `J`, `O`, `Q`, `W`**. Đây là căn cứ cho ràng buộc hậu xử lý **theo vị trí** ở mục 4.6.5; bảng đầy đủ các tập ký tự seri ở **Phụ lục V**.

### 2.2.2. Màu nền và ý nghĩa

Năm tổ hợp màu nền phân biệt đối tượng sử dụng (bảng đầy đủ ở **Phụ lục V**): trắng/đen phổ biến nhất, **vàng/đen là tín hiệu phân loại xe kinh doanh vận tải duy nhất còn hợp lệ**, xanh/trắng cho cơ quan nhà nước với seri chỉ 11 chữ cái, trắng/đỏ cho ngoại giao, đỏ/trắng cho quân đội — loại cuối **ngoài phạm vi** TT 79/2024, thuộc TT 169/2021/TT-BQP [8]. Xe năng lượng sạch **không có biển riêng**, nên không phát hiện được xe điện qua màu biển.

### 2.2.3. Kích thước vật lý và tỷ lệ khung hình

Cơ sở định lượng phân biệt biển một dòng với hai dòng — quyết định với rủi ro R-04 (mục 2.4.3). Ô tô được cấp **02** biển: 01 ngắn (**2 dòng**), 01 dài (**1 dòng**); xe mô tô, xe gắn máy, rơ moóc được cấp **01** biển **2 dòng** — **một ô tô mang cùng chuỗi ký tự trên hai biển hình dạng hoàn toàn khác nhau**.

Ba tỷ lệ khung hình tách rõ hai bố cục [6]: ô tô biển **dài** 520 × 110 mm → **4,727** (một dòng); ô tô biển **ngắn** 330 × 165 mm → **2,000** và xe máy 190 × 140 mm → **1,357** (hai dòng). Không biển nào rơi vào khoảng mở **(2,000 ; 4,727)** — đó là cơ sở hình học của bộ phân loại số dòng. Bộ số này **chỉ đúng từ 01/01/2025**; tiêu chuẩn trước đó quy định kích thước khác, nên mọi trích dẫn kích thước biển số bắt buộc kèm mốc hiệu lực. Bảng chi tiết ở **Phụ lục V**.

### 2.2.4. Ý nghĩa đối với thiết kế hệ thống nhận dạng

Bảy dữ kiện kéo theo bảy quyết định thiết kế: **81 mã tỉnh trong dải 89 số** biến lỗi OCR hai ký tự đầu thành sai phát hiện được; **tập seri khác theo vị trí** buộc ràng buộc **theo vị trí** và tập huấn luyện OCR đủ 36 ký tự; **hai kiểu seri xe máy, nhóm thứ tự 4 hoặc 5 chữ số** buộc biểu thức chính quy đa nhánh; **chuỗi 8 ký tự khớp hai loại biển** nên phải lưu số dòng độc lập; **seri không còn cho biết loại xe** nên cấm heuristic suy loại phương tiện; **khoảng trống tỷ lệ khung hình 2,727** là cơ sở ngưỡng phân loại bố cục; **khung pháp lý đổi ba lần trong hai năm** buộc hậu xử lý tách rời mô hình để cập nhật độc lập.

## 2.3. Cơ sở lý thuyết về phát hiện đối tượng

### 2.3.1. Kiến trúc YOLO: nguyên lý one-stage và anchor-free

Ràng buộc CPU loại họ **two-stage** (Faster R-CNN — sinh vùng đề xuất rồi phân loại từng đề xuất) ngay từ đầu; đồ án dùng họ **one-stage**, hồi quy trực tiếp trong một lần lan truyền xuôi. Một nghiên cứu ALPR trên 50.000 ảnh và 10.000 video clip kết luận nhóm YOLO vượt trội Faster R-CNN và SSD cả về độ chính xác lẫn thời gian suy luận [12]<!-- scirep_2025_advanceddl --> (Hình 2.1).

![](figures/fig-ch2-05.png)

**Hình 2.1.**[]{#fig-2-1} Kiến trúc tổng quát backbone – neck – head của YOLO11 *(theo [13], [9])*

Ba phần: **backbone** trích đặc trưng, **neck** hợp nhất đặc trưng nhiều tầng, **head** sinh dự đoán — từ YOLOv8 dùng **anchor-free split head** [13]<!-- jocher_2023_yolov8 -->. Anchor-free có ý nghĩa riêng với biển số: anchor-based hồi quy theo tập hộp mẫu thiết kế theo phân bố COCO, mà biển số nằm ngoài phân bố đó (một dòng ≈ 4,7:1, hai dòng ≈ 1,4:1); anchor-free hồi quy **trực tiếp khoảng cách tâm đến bốn cạnh**, xử lý cả hai chế độ tỷ lệ bằng một cơ chế [9]<!-- jocher_2024_yolo11 -->.

### 2.3.2. YOLO11: các cải tiến kiến trúc

Đồ án **không cải tiến kiến trúc YOLO**, nên phần này chỉ nêu điều cần để đọc kết quả ở Chương 5. Khác biệt kiến trúc thực sự của YOLO11 so với YOLOv8 là khối attention **C2PSA** đặt ngay sau SPPF — thành phần YOLOv8 hoàn toàn không có; khối `C3k2` thì **kế thừa trực tiếp từ `C2f`** của YOLOv8 và trùng khớp với nó khi tắt cờ cấu hình [14]<!-- ultralytics_2026_blockpy -->. Ultralytics cho biết C2PSA cải thiện phát hiện **đối tượng nhỏ** và **che khuất phức tạp** [9]<!-- jocher_2024_yolo11 -->, nhưng đây là phát biểu **định tính**: hãng không công bố AP_small/AP_medium/AP_large theo chuẩn COCO cho từng biến thể, nên đồ án phải **tự đo trên dữ liệu của mình** (Chương 5) (Bảng 2.1).

**Bảng 2.1.**[]{#tbl-2-1} So sánh khác biệt kiến trúc giữa các phiên bản YOLO gần đây

| Phiên bản | Khối backbone | Cơ chế attention | Đầu dự đoán | NMS | Điểm mới chính |
|---|---|---|---|:--:|---|
| YOLOv8 [13] | C2f | Không có | Anchor-free, tách nhánh | Có | Chuyển sang anchor-free |
| YOLOv10 | Rank-guided blocks | Partial self-attention | Hai đầu song song | **Không** | Consistent dual assignments |
| **YOLO11** [9] | **C3k2** (kế thừa C2f) | **C2PSA** sau SPPF | Anchor-free, tách nhánh | Có | C2PSA cải thiện đối tượng nhỏ |
| YOLO26 | Kế thừa dòng Ultralytics | Kế thừa dòng Ultralytics | **Bỏ DFL** | **Không** (mặc định) | Bỏ DFL, dễ xuất và lượng tử hoá |

Bảng chỉ giữ bốn phiên bản có khác biệt kiến trúc đáng kể với bài toán biển số; **danh sách đầy đủ bảy thế hệ đã xét** và luận cứ chọn YOLO11 trình bày ở mục 3.2.

### 2.3.3. Các chỉ số đánh giá khối phát hiện

**a) Precision, Recall và F1.** Với $TP$ dự đoán đúng, $FP$ dự đoán sai, $FN$ đối tượng bỏ sót:

$$\mathrm{Precision} = \frac{TP}{TP + FP}, \qquad \mathrm{Recall} = \frac{TP}{TP + FN}, \qquad F_1 = \frac{2 \cdot \mathrm{Precision} \cdot \mathrm{Recall}}{\mathrm{Precision} + \mathrm{Recall}}$$

<div align="right">(2.2)</div>

Với ALPR, **recall của bước phát hiện quan trọng hơn precision**: biển bỏ sót là mất vĩnh viễn, vùng báo nhầm bị hậu xử lý loại vì chuỗi không khớp cú pháp.

**b) AP và mAP.** AP là diện tích dưới đường cong Precision–Recall; mAP là trung bình AP trên $N$ lớp — đồ án có $N = 1$ nên mAP trùng AP:

$$\mathrm{AP} = \int_0^1 p(r)\, \mathrm{d}r, \qquad \mathrm{mAP} = \frac{1}{N}\sum_{i=1}^{N} \mathrm{AP}_i$$

<div align="right">(2.3)</div>

**c) mAP@0.5 và mAP@0.5:0.95.** mAP@0.5 tính tại **một ngưỡng IoU cố định 0,5**; mAP@0.5:0.95 lấy **trung bình trên 10 ngưỡng** từ 0,5 đến 0,95 bước 0,05, nên trên cùng mô hình và cùng tập dữ liệu **mAP@0.5:0.95 luôn ≤ mAP@0.5**. Khoảng cách giữa hai chỉ số với biển số thường rất lớn do hộp bao dẹt: ba công trình đã công bố cho chênh **18,8 · 27,5 · 40,7 điểm phần trăm** (**Phụ lục V**), cùng xác nhận **biển số dễ phát hiện nhưng khó khớp hộp bao chính xác**. Hai chỉ số này **không so sánh chéo được**, nên đối chiếu mAP@0.5 của một nghiên cứu ALPR với mAP@0.5:0.95 trên COCO không có giá trị làm luận cứ kỹ thuật.

**d) Chỉ tiêu của đồ án.** Vì mục tiêu phát hiện là cắt vùng biển đủ tốt để OCR đọc, đồ án chọn **mAP@0.5 làm chỉ tiêu chính** và vẫn báo cáo mAP@0.5:0.95; giá trị ở Chương 5.

## 2.4. Cơ sở lý thuyết về nhận dạng ký tự

### 2.4.1. Bài toán OCR và đặc thù khi áp dụng cho biển số

**OCR** (*Optical Character Recognition*) chuyển văn bản trong ảnh thành chuỗi, thường gồm **text detection** khoanh vùng rồi **text recognition** đọc từng vùng. Sai lầm phổ biến: lấy thẳng bảng xếp hạng OCR phổ thông làm căn cứ chọn bộ nhận dạng cho ALPR (Bảng 2.2).

**Bảng 2.2.**[]{#tbl-2-2} So sánh OCR văn bản tài liệu và OCR biển số xe

| Chiều so sánh | OCR văn bản tài liệu | OCR biển số xe |
|---|---|---|
| Nguồn ảnh | Ảnh quét hoặc chụp tài liệu, gần chính diện | Ảnh cảnh ngoài trời, phối cảnh nghiêng, chói sáng, nhoè do chuyển động |
| Độ dài chuỗi và tập ký tự | Hàng trăm đến hàng nghìn ký tự; tập lớn, mở, kèm dấu | 7 – 9 ký tự; tập đóng — **chỉ A–Z và 0–9** |
| Bố cục | Nhiều dòng, đa cột, ngắt dòng tuỳ ý | Cố định: 1 hoặc 2 dòng theo quy chuẩn nhà nước |
| Ràng buộc cú pháp và vai trò hậu xử lý | Gần như không có; hậu xử lý phụ trợ | Rất chặt, kiểm tra được bằng biểu thức chính quy; hậu xử lý **bắt buộc**, là lớp sửa lỗi chính |
| Tiêu chí đánh giá | CER / WER — chấp nhận sai lẻ tẻ | **Khớp chuỗi tuyệt đối** — sai 1 ký tự là hỏng cả bản ghi |
| Giá trị của thông tin ngôn ngữ | Cao — mô hình ngôn ngữ sửa lỗi hiệu quả | **Thấp** — không có từ vựng để dựa vào |

### 2.4.2. Kiến trúc CRNN và hàm mất mát CTC

**CRNN** gồm ba tầng: **tầng tích chập** trích đặc trưng và — điểm quyết định — downsample chiều cao **về 1**, biến bản đồ đặc trưng thành **chuỗi vector theo chiều rộng**; **tầng hồi quy** (Bi-LSTM) mô hình hoá ngữ cảnh hai chiều; **tầng phiên mã** giải mã thành chuỗi, thường bằng CTC. EasyOCR dùng đúng kiến trúc này; PaddleOCR dùng SVTR-LCNet kết hợp GTC [10]<!-- cui_2026_ppocrv5 -->, vẫn thuộc họ CTC.

**Hàm mất mát CTC** giải vấn đề: biết chuỗi nhãn đúng nhưng **không biết mỗi ký tự nằm ở cột đặc trưng nào**. CTC thêm ký hiệu trống $\varepsilon$, định nghĩa ánh xạ $\mathcal{B}$ gộp ký tự lặp rồi xoá $\varepsilon$ — ví dụ $\mathcal{B}(\texttt{3}\varepsilon\texttt{00}\varepsilon\texttt{A}) = \texttt{30A}$ — và tính xác suất chuỗi nhãn $\mathbf{l}$ bằng tổng xác suất **mọi** đường đi thô $\boldsymbol{\pi}$ ánh xạ về nó:

$$p(\mathbf{l} \mid \mathbf{x}) = \sum_{\boldsymbol{\pi} \in \mathcal{B}^{-1}(\mathbf{l})} \prod_{t=1}^{T} y^{t}_{\pi_t}, \qquad \mathcal{L}_{\mathrm{CTC}} = -\log p(\mathbf{l} \mid \mathbf{x})$$

<div align="right">(2.3)</div>

Tổng ở (2.3) tính bằng quy hoạch động tiến–lùi. Ưu điểm quyết định: **không cần nhãn vị trí từng ký tự** — lý do CTC là mặc định của hầu hết bộ nhận dạng mã nguồn mở (Hình 2.2).

![](figures/fig-ch2-crnn-ctc.png)

**Hình 2.2.**[]{#fig-2-2} Kiến trúc CRNN và cách CTC gộp chuỗi thô.

### 2.4.3. Vì sao kiến trúc CTC gặp khó với văn bản nhiều dòng

Nền tảng lý thuyết cho rủi ro **R-04**: ở Việt Nam nơi xe máy áp đảo, biển hai dòng là dạng phổ biến chứ không phải ngoại lệ. CTC giả định đầu vào là **một chuỗi theo chiều rộng**; ảnh hai dòng vi phạm giả định đó — tầng tích chập hạ chiều cao về 1 nên hai dòng bị chồng vào cùng một cột đặc trưng, sinh chuỗi trộn lẫn hoặc mất hẳn một dòng (Hình 2.3).

![](figures/fig-ch2-07.png)

**Hình 2.3.**[]{#fig-2-3} Cơ chế sụp đổ của CTC trên ảnh văn bản hai dòng

Có nhiều cách phân biệt biển một dòng với hai dòng — lấy lớp từ chính bộ phát hiện, cắt đôi theo tỷ lệ hình học, chiếu ngang tìm điểm trũng, phân cụm hộp bao ký tự theo toạ độ dọc, hoặc kiểm tra tính thẳng hàng của ký tự. Phương án được chọn và lý do trình bày ở mục 4.6.4.

### 2.4.4. Chỉ số CER và độ chính xác mức chuỗi

**a) CER** (*Character Error Rate*) dựa trên khoảng cách Levenshtein, với $S$ thay thế, $D$ xoá, $I$ chèn, $N$ tổng ký tự chuỗi thực; độ chính xác mức ký tự là $1 - \mathrm{CER}$:

$$\mathrm{CER} = \frac{S + D + I}{N}$$

<div align="right">(2.4)</div>

CER **có thể vượt 1** khi chuỗi dự đoán dài hơn chuỗi thực rất nhiều — đúng tình huống CTC gặp ảnh hai dòng. **b) WER** tương tự nhưng đơn vị là từ; đồ án không dùng chỉ số này vì biển số không có ranh giới từ. **c) Độ chính xác mức chuỗi** (*plate-level accuracy*, *exact match*) là chỉ số nghiêm ngặt nhất:

$$\mathrm{Acc}_{\text{plate}} = \frac{\#\{\text{biển số có TOÀN BỘ chuỗi ký tự khớp chính xác}\}}{\#\{\text{tổng số biển số trong tập kiểm thử}\}}$$

<div align="right">(2.5)</div>

Quan hệ giữa chỉ số này và CER là **bất lợi phi tuyến**: với biển 8 ký tự, nếu xác suất đọc đúng mỗi ký tự là $p$ thì xác suất đúng cả chuỗi là $p^{8}$ — $p = 0{,}99$ cho ≈ 0,923, còn $p = 0{,}95$ tụt xuống ≈ 0,663. Đó là lý do một bộ nhận dạng có CER rất tốt trên văn bản tài liệu vẫn có thể thất bại trên biển số. **d) End-to-end Recognition Rate** — tỷ lệ biển đọc đúng hoàn toàn trên **toàn bộ đường ống** — là chỉ số duy nhất phản ánh lỗi tích luỹ, chỉ tiêu quan trọng nhất của đồ án; cuộc thi ICPR 2026 về biển độ phân giải thấp dùng chỉ số này làm chính, đội vô địch đạt 82,13% [18]<!-- laroca_2026_icprlrlpr -->. Kèm theo là chỉ số vận hành: **độ trễ** p50, p95, p99 (bắt buộc kèm cấu hình phần cứng), **kích thước mô hình**, **bộ nhớ thường trú**, **số tham số**; giá trị ở Chương 5.

## 2.5. Các công trình liên quan

### 2.5.1. Công trình quốc tế tiêu biểu

Laroca và cộng sự (2022) khảo sát khả năng tổng quát hoá của các hệ thống ALPR khi chuyển giữa các bộ dữ liệu khác nhau [2]<!-- laroca_2022_crossdataset -->. Trên bộ **RodoSol-ALPR** của Brazil — thiết kế cân bằng có chủ ý với 4.000 ảnh ô tô biển một dòng và 4.000 ảnh xe máy biển hai dòng — hệ thống thương mại OpenALPR suy giảm **48,6 điểm phần trăm** khi chuyển từ biển một dòng sang biển hai dòng (số liệu cụ thể ở 1.1.3). Vì hai nhóm ảnh chỉ khác nhau ở bố cục biển, kết quả này cho thấy **bố cục hai dòng là một thách thức độc lập với chất lượng bộ phát hiện**. Cũng trong nghiên cứu đó, cả 12 phương pháp và 2 hệ thống thương mại được đánh giá đều không vượt quá 70% tỷ lệ nhận dạng khi đo xuyên bộ dữ liệu.

Cuộc thi **ICPR 2026 về nhận dạng biển số độ phân giải thấp** lấy độ chính xác đầu cuối ở **mức chuỗi** làm chỉ số chính; đội dẫn đầu đạt **82,13%** [18]<!-- laroca_2026_icprlrlpr -->. Con số này cho thấy bài toán vẫn chưa được giải quyết trọn vẹn ngay cả với những phương pháp mạnh nhất, và nó cũng là mốc tham chiếu hợp lý duy nhất cho chỉ số đầu cuối của đồ án (5.8.1).

Về kiến trúc, các nghiên cứu ALPR gần đây phần lớn theo hướng **hai giai đoạn**: một bộ phát hiện đối tượng khoanh vùng biển, rồi một bộ nhận dạng ký tự đọc vùng đã cắt. Batra và cộng sự (2022) dùng YOLOv5 cho biển số Ấn Độ [15]<!-- batra_2022_yolov5 -->, và hai công trình 2025 áp dụng YOLO11 cho cùng bài toán [16]<!-- jaic_2025_yolov11alpr --> [17]<!-- jcosine_2025_yolo11plate -->. Cả ba đều báo cáo mAP của **riêng bước phát hiện**; không công trình nào trong nhóm này bóc tách kết quả nhận dạng theo bố cục biển — khoảng cách giữa mAP@0.5 và mAP@0.5:0.95 mà chúng công bố (18,8 · 27,5 · 40,7 điểm phần trăm, **Phụ lục V**) chỉ nói lên độ khít của hộp bao, không nói gì về khả năng đọc biển hai dòng.

### 2.5.2. Công trình về biển số Việt Nam

Qua khảo sát các công trình và đồ án ALPR cho biển số Việt Nam được công bố công khai, phần lớn nghiên cứu tập trung vào việc cải thiện độ chính xác **phát hiện** biển số hoặc báo cáo kết quả tổng thể của toàn hệ thống. Các công trình thường dùng YOLO kết hợp EasyOCR hoặc PaddleOCR, và công bố mAP, precision, recall hoặc một con số độ chính xác nhận dạng chung. Phần lớn đánh giá trên tập tự thu thập không công khai, nên **so sánh công bằng giữa các công trình gần như bất khả thi**.

Trong tập tài liệu khảo sát được, nhóm thực hiện **chưa tìm thấy công trình công khai nào đồng thời làm ba việc sau**: *(i)* báo cáo tách riêng độ chính xác cho biển một dòng và biển hai dòng trên cùng một hệ thống; *(ii)* đo **định lượng** đóng góp của bước hậu xử lý, tức công bố độ chính xác cả trước lẫn sau bước đó; và *(iii)* công bố benchmark giữa nhiều bộ nhận dạng ký tự trên cùng một tập ảnh biển số Việt Nam.

Bảng 2.3 tóm tắt năm công trình tiêu biểu trong tập khảo sát, chọn theo tiêu chí có công bố phương pháp và số liệu đủ để đối chiếu.

**Bảng 2.3.**[]{#tbl-2-3} Tóm tắt một số công trình ALPR cho biển số Việt Nam được khảo sát

| Công trình | Năm | Khối phát hiện | Khối nhận dạng | Chỉ số báo cáo | Hạn chế đối với câu hỏi của đồ án |
| --- | :--: | --- | --- | --- | --- |
| Nguyen Quoc và cộng sự, MAPR [25]<!-- mta_2021_mapr --> | 2021 | Key-point detection | Encoder–decoder *segmentation-free* | Chuỗi **99,28%**, ký tự 99,7%; mIoU 95,01% | Tập dữ liệu riêng không công khai; không tách theo bố cục biển |
| Tran-Anh và cộng sự [26]<!-- tran_2023_multiangle --> | 2023 | Multi-angle view model | CnOCR | **F1 91,3%** trên PTITPlates (500 ảnh) | Không đo đóng góp của khối hậu xử lý |
| Le và cộng sự, FDSE [27]<!-- le_2023_fdse --> | 2023 | YOLOv8 | YOLOv8 | **mAP 93%** | Chỉ báo cáo chỉ số phát hiện, không có chỉ số đầu cuối |
| Tran và Bui, MIWAI [28]<!-- tran_2024_miwai --> | 2024 | SSD, backbone MobileNetV2 | YOLOv8-nano | **95,68%**; 0,478 s/ảnh trên Raspberry Pi 4 | Không benchmark giữa nhiều bộ nhận dạng |
| Đặng Thị Dung và cộng sự, TNU [29]<!-- dang_2024_tnu --> | 2024 | YOLOv8 · YOLO-NAS | *(không có)* | YOLO-NAS-S accuracy **83,92%**, F1 0,9125 | Chỉ so sánh bộ phát hiện; không đọc chuỗi |
| **Đồ án này** | **2026** | **YOLO11n** | **PaddleOCR PP-OCRv5 mobile** | **A6 = 77,01%**, **A7 = 56,3%**, tách theo bố cục biển | Độ chính xác trên biển hai dòng còn hạn chế (72,34%) |

Bảng cho thấy ba đặc điểm chung. **Một, chỉ số báo cáo không đồng nhất** — mIoU, mAP, F1, accuracy và độ chính xác mức chuỗi xuất hiện lẫn lộn, nên các con số trong cột cuối **không so sánh trực tiếp được với nhau**. **Hai, hai trong năm công trình chỉ báo cáo chỉ số của khối phát hiện**, không công bố kết quả đọc chuỗi đầu cuối. **Ba, không công trình nào tách riêng kết quả cho biển một dòng và biển hai dòng**, dù bốn trong năm công trình làm việc với ảnh xe máy — vốn luôn mang biển hai dòng.

Kết quả cao nhất được công bố cho biển số Việt Nam là **99,28% mức chuỗi** [25]. **Con số này không đối chiếu trực tiếp được với kết quả của đồ án**, và lý do là về nguyên tắc chứ không phải về mức độ: công trình ấy đo trên **bộ dữ liệu riêng không công khai** nên không ai tái lập hay đối chứng được, và **không công bố phân bố độ khó** của tập ấy — tỉ lệ biển hai dòng, điều kiện chụp, dải kích thước biển đều không được mô tả định lượng. Hai tập dữ liệu có phân bố độ khó khác nhau thì hai con số độ chính xác **không cùng thang đo**, nên đặt 99,28% cạnh bất kỳ con số nào của đồ án đều là so sánh không hợp lệ. Phép so sánh hợp lệ đòi hai hệ thống chạy trên **cùng một tập kiểm tra**, điều kiện mà bộ dữ liệu không công khai loại trừ ngay từ đầu.

> **Phạm vi của nhận định trên.** Nó chỉ áp dụng cho tập tài liệu nhóm thực hiện khảo sát được tại thời điểm thực hiện đề tài, chủ yếu là các nguồn công khai truy cập được bằng tiếng Việt và tiếng Anh. Đây là **phát biểu về phạm vi khảo sát**, không phải khẳng định rằng những công trình như vậy không tồn tại.

### 2.5.3. Các bộ dữ liệu chuẩn trong lĩnh vực

Khảo sát đối chiếu các bộ dữ liệu chuẩn của lĩnh vực theo quy mô, đặc điểm và **giấy phép sử dụng** — cột giấy phép quyết định bộ nào dùng được cho đồ án này. Hai bộ được nhắc tới nhiều nhất là **RodoSol-ALPR** (Brazil, có nhãn bố cục một dòng · hai dòng) [2]<!-- laroca_2022_crossdataset --> và tập của **ICPR 2026 LR-LPR** (ảnh độ phân giải thấp, có nhãn chuỗi) [18]<!-- laroca_2026_icprlrlpr -->; cả hai đều **không chứa biển số Việt Nam**, nên không dùng trực tiếp được. Bộ dữ liệu mà đồ án hợp nhất cùng giấy phép từng nguồn trình bày ở mục 4.4.1 và **Phụ lục II**.

### 2.5.4. Khoảng trống nghiên cứu và định vị đề tài

Từ khảo sát trên, đồ án xác định sáu hướng đóng góp, mỗi hướng nhắm vào một khoảng trống cụ thể (Bảng 2.4).

**Bảng 2.4.**[]{#tbl-2-4} Sáu khoảng trống nghiên cứu và cách nhóm thực hiện lấp

| # | Đóng góp của đồ án | Khoảng trống mà nó lấp |
|:--:| --- | --- |
| 1 | **Báo cáo tách riêng độ chính xác cho biển một dòng và biển hai dòng** trên cùng một hệ thống, ở cả tầng phát hiện lẫn tầng nhận dạng, và biến việc này thành nghĩa vụ bắt buộc qua chỉ tiêu NFR-A8 | Năm công trình trong Bảng 2.3 đều báo cáo một chỉ số chung, không tách theo bố cục biển (2.5.2) |
| 2 | **Thiết kế bộ luật hậu xử lý ràng buộc theo VỊ TRÍ trong chuỗi**, và **đo tách bạch độ chính xác trước và sau bước đó** để hiệu số trở thành một đại lượng định lượng | Các mô tả khảo sát được dừng ở danh sách ký tự phẳng, phần lớn dùng nhầm con số 20 chữ cái cho toàn chuỗi (2.2.4) |
| 3 | **Công bố chỉ số đầu cuối ở mức chuỗi** bên cạnh mAP của bước phát hiện, và nêu rõ chênh lệch giữa hai đại lượng | Trong phạm vi khảo sát, phần lớn công trình trong nước chỉ báo cáo mAP của bước phát hiện (2.5.2) |
| 4 | **Xây dựng benchmark ba bộ nhận dạng ký tự trên 2.801 biển số Việt Nam** trong cùng một tầng bao quanh: PaddleOCR 68,87% · EasyOCR 14,28% · Tesseract 10,28% (3.3.3) | Trong tập khảo sát, không công trình nào công bố benchmark giữa nhiều bộ nhận dạng trên riêng ảnh biển số Việt Nam (3.3) |
| 5 | **Mọi số liệu hiệu năng công bố kèm cấu hình phần cứng**: model CPU, số luồng, kích thước ảnh vào, nền tảng suy luận, cỡ mẫu đo | Trong phạm vi khảo sát, số liệu hiệu năng thường công bố không kèm phần cứng nên không tái lập được (2.5.1) |
| 6 | **Bàn giao hệ thống có kiến trúc phần mềm, kiểm thử và giao thức đo công khai** — mọi số liệu sinh lại được bằng một lệnh | Trong phạm vi các kho mã nguồn mở được khảo sát, đa số không công bố đầy đủ giao thức đo hoặc kiến trúc hệ thống (2.5.2) |

Sáu đóng góp đều thuộc loại **kỹ nghệ và báo cáo**, không phải thuật toán; tuyên bố đóng góp đầy đủ đặt ở mục 1.5.

> Tuyên bố trung thực đầy đủ về mức đóng góp, cùng bốn điều đồ án **không** tuyên bố, đặt ở **mục 1.5.1 và 1.5.2** (Chương 1) — nơi chính danh để tuyên bố đóng góp.
