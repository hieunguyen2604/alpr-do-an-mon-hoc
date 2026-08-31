# CHƯƠNG 2. CƠ SỞ LÝ THUYẾT

Chương này chỉ trình bày phần lý thuyết **ràng buộc trực tiếp một quyết định cài đặt** ở Chương 3. Thứ tự trình bày đi từ đối tượng (quy chuẩn biển số và hệ quả hình học của nó), qua các phép xử lý ảnh được sử dụng, rồi tới hai mô hình học sâu mà đồ án dùng như công cụ.

## 2.1. Quy chuẩn biển số xe Việt Nam và hệ quả hình học

### 2.1.1. Cấu trúc chuỗi ký tự

Biển số ô tô trong nước gồm **8 ký tự**, ba thành phần: **mã địa phương** 2 chữ số, **seri** 1 chữ cái, **số thứ tự** 5 chữ số — ví dụ `30A-123.45` [3]. Trên đường vẫn còn biển 4 chữ số kiểu cũ (`29A-1234`) và xe đã đăng ký không bắt buộc đổi biển, nên biểu thức chính quy phải chấp nhận nhóm thứ tự **4 hoặc 5 chữ số**. Biển xe mô tô có **9 ký tự**, seri hai ký tự.

**Mã địa phương hữu hạn và có lỗ hổng.** Dải 11–99 có 89 giá trị, nhưng chỉ **81 mã đang được sử dụng**; tám mã **13, 42, 44, 45, 46, 87, 91, 96** không được gán [7]. Kiểm tra mã tỉnh vì vậy biến lỗi đọc ở hai vị trí đầu từ **sai âm thầm** thành **sai phát hiện được**: đọc ra `46A-123.45` thì biết ngay mã 46 không tồn tại.

**Tập ký tự seri phụ thuộc vị trí.** Đây là chi tiết dễ trình bày sai nhất. Biển trắng và vàng dùng seri thuộc tập **20 chữ cái** [6]; đối chiếu 26 chữ Latin thì vắng `I J O Q R W`. Nhưng suy diễn *"26 − 20 = 6 chữ bị loại trừ"* là **sai**: danh sách 20 chữ chỉ áp dụng cho **chữ cái thứ nhất**; ở **vị trí thứ hai** của seri xe máy là một tập khác — **có `R`, không có `G`**. Hợp hai vị trí, tập chữ không bao giờ xuất hiện trên biển Việt Nam chỉ gồm **5 chữ: `I`, `J`, `O`, `Q`, `W`**.

**Bảng 2.1.** Tổng hợp các tập ký tự seri

| Tập | Số lượng | Nội dung |
|---|:--:|---|
| Chữ cái thứ nhất của seri | 20 | A B C D E F **G** H K L M N P S T U V X Y Z |
| Chữ cái thứ hai của seri xe máy | 20 | A B C D E F H K L M N P **R** S T U V X Y Z |
| Seri biển nền xanh | 11 | A B C D E F G H K L M |
| **Bị loại trừ khỏi toàn hệ thống** | **5** | **I, J, O, Q, W** |

Hệ quả cài đặt: **nếu huấn luyện lại bộ nhận dạng thì phải dùng đủ 36 ký tự** rồi mới ràng buộc ở tầng hậu xử lý. *(Bản giao hàng dùng model gốc PP-OCRv5, charset còn rộng hơn 36; ràng buộc hợp lệ vẫn đặt ở tầng hậu xử lý.)* Một mô hình huấn luyện trên charset 20 chữ cái sẽ **không bao giờ dự đoán được `R`**, gây sai sót có hệ thống trên mọi biển xe máy mang ký tự này — loại sai sót mà hậu xử lý không cứu được vì thông tin đã bị loại ngay ở tầng mô hình.

### 2.1.2. Kích thước vật lý và tỉ lệ khung hình

Đây là cơ sở hình học quan trọng nhất của đồ án, vì nó cho phép **phân biệt biển một dòng với biển hai dòng bằng một đại lượng đo trực tiếp từ ảnh**, không cần huấn luyện thêm mô hình nào.

**Bảng 2.2.** Kích thước và tỉ lệ khung hình các loại biển số [5]

| Loại biển | Kích thước (dài × cao) | Tỉ lệ khung hình | Số dòng |
|---|---|:--:|:--:|
| Ô tô — biển **dài** | 520 × 110 mm | **4,727** | 1 dòng |
| Ô tô — biển **ngắn** | 330 × 165 mm | **2,000** | 2 dòng |
| Xe mô tô, xe gắn máy | 190 × 140 mm | **1,357** | 2 dòng |

Ba giá trị này để lại một **khoảng trống rộng 2,727 đơn vị** giữa 2,000 và 4,727 mà không loại biển nào rơi vào. Khoảng trống đó là căn cứ để đặt ngưỡng phân loại bố cục ở mục 3.4.3.

Cần lưu ý mốc hiệu lực: bộ số liệu trên **chỉ đúng từ 01/01/2025**. Tiêu chuẩn trước đó quy định biển ô tô ngắn 200 × 280 mm và biển dài 110 × 470 mm, và nhiều tài liệu thứ cấp vẫn dùng bộ số cũ.

Một hệ quả nữa: ô tô được cấp **hai** biển mang cùng chuỗi ký tự nhưng **hình dạng hoàn toàn khác nhau** (một dài một ngắn), trong khi xe mô tô chỉ có một biển hai dòng. Do đó số dòng bằng một *chứng minh* biển thuộc ô tô, còn số dòng bằng hai *không chứng minh gì* — cả ô tô lẫn xe máy đều có thể.

### 2.1.3. Màu nền và giới hạn của thông tin ký tự

**Bảng 2.3.** Màu nền biển số và đối tượng áp dụng [6]

| Màu nền / màu chữ | Đối tượng | Ghi chú |
|---|---|---|
| Trắng / đen | Cá nhân, tổ chức trong nước, xe không kinh doanh vận tải | Phổ biến nhất |
| Vàng / đen | Xe **kinh doanh vận tải** | Cùng cấu trúc ký tự với biển trắng |
| Xanh dương / trắng | Cơ quan Đảng, Nhà nước, công an | Seri chỉ dùng 11 chữ cái |
| Trắng / **đỏ** | Xe ngoại giao, tổ chức quốc tế | Cấu trúc chuỗi khác hẳn |

Bảng này chỉ ra một giới hạn về nguyên tắc: biển vàng của xe kinh doanh vận tải mang **đúng cùng cấu trúc ký tự** với biển trắng của xe cá nhân, nên **không biểu thức chính quy nào phân biệt được**. Ngược lại, biển ngoại giao có nền trắng giống biển cá nhân nên riêng màu nền cũng không đủ. Chỉ **cặp thuộc tính gồm chuỗi ký tự và màu nền** mới định danh được loại phương tiện — lý do đồ án xây dựng thêm một bộ phân loại màu trong không gian HSV (mục 3.5).

## 2.2. Các phép xử lý ảnh sử dụng trong đồ án

### 2.2.1. Chuyển thang xám

Ký tự trên biển số không mang thông tin phân biệt trong kênh màu: chữ đen trên nền trắng, đen trên nền vàng, trắng trên nền xanh — trong mọi trường hợp thông tin nằm ở **độ chói**, không ở sắc độ. Chuyển sang thang xám theo trọng số cảm thụ

$$Y = 0{,}299R + 0{,}587G + 0{,}114B$$

<div align="right">(2.1)</div>

giảm ba kênh còn một, tức giảm hai phần ba khối lượng tính toán cho mọi bước phía sau mà không mất thông tin dùng được. Cần lưu ý: bước này chạy trên **nhánh nhận dạng ký tự**; nhánh phân loại màu nền (mục 3.5) làm việc trên ảnh màu gốc, vì đó chính là thông tin nó cần.

### 2.2.2. Cân bằng lược đồ xám thích nghi có giới hạn tương phản (CLAHE)

Bề mặt biển số Việt Nam **phản quang theo tiêu chuẩn**, nên dưới đèn pha hoặc nắng gắt nó tạo ra các **mảng chói cục bộ**: một phần biển bị bão hoà trắng trong khi phần còn lại vẫn tối. Cân bằng lược đồ xám toàn cục không xử lý được tình huống này, vì nó áp một hàm biến đổi duy nhất cho toàn ảnh — làm sáng vùng tối thì đồng thời đẩy vùng chói bão hoà thêm.

**Cân bằng lược đồ xám thích nghi (AHE)** chia ảnh thành các ô nhỏ và cân bằng riêng từng ô, nên vùng chói và vùng tối được xử lý bằng hai hàm biến đổi khác nhau. Nhược điểm của nó là **khuếch đại nhiễu** ở những ô gần đồng nhất: khi lược đồ tập trung vào vài mức xám, hàm phân phối tích luỹ dựng đứng và một chênh lệch một mức xám bị kéo giãn thành chênh lệch lớn.

**CLAHE** [11] khắc phục bằng cách **cắt ngọn lược đồ** tại một hệ số giới hạn rồi **phân phối lại** phần bị cắt đều cho mọi mức xám, trước khi tính hàm phân phối tích luỹ. Việc cắt ngọn đặt trần cho độ dốc của hàm biến đổi, tức đặt trần cho mức khuếch đại nhiễu.

Đồ án dùng hệ số giới hạn **2,0** trên lưới ô **8 × 8**. Kỹ thuật này đã được ghi nhận hiệu quả trong chính bài toán ALPR [10].

### 2.2.3. Lọc song phương thay cho làm mờ Gauss

Ảnh biển số do bộ phát hiện cắt ra thường nhoè và nhiễu, nên cần một bước khử nhiễu. Làm mờ Gauss

$$G(x, y) = \frac{1}{2\pi\sigma^{2}} \exp\!\left(-\frac{x^{2} + y^{2}}{2\sigma^{2}}\right)$$

<div align="right">(2.2)</div>

lấy trung bình có trọng số theo **khoảng cách không gian**, nên nó không phân biệt được điểm ảnh nhiễu với điểm ảnh nằm trên một biên thật — kết quả là biên bị làm mờ cùng với nhiễu.

**Lọc song phương** [12] nhân thêm một nhân trọng số theo **chênh lệch cường độ**:

$$I'(\mathbf{p}) = \frac{1}{W_{\mathbf{p}}} \sum_{\mathbf{q} \in S} G_{\sigma_{s}}\!\left(\lVert \mathbf{p} - \mathbf{q} \rVert\right) \, G_{\sigma_{r}}\!\left(\lvert I(\mathbf{p}) - I(\mathbf{q}) \rvert\right) I(\mathbf{q})$$

<div align="right">(2.3)</div>

Điểm ảnh lân cận có cường độ khác xa điểm trung tâm — tức nằm bên kia một biên — nhận trọng số gần bằng không, nên **biên được bảo toàn** trong khi nhiễu bên trong vùng đồng nhất vẫn bị san phẳng.

Lý do chọn lọc song phương ở đây rất cụ thể: các cặp ký tự đồng hình như `8` và `B`, `0` và `D` chỉ phân biệt được nhờ **một nét biên duy nhất**. Một bước khử nhiễu làm mờ biên sẽ trực tiếp tạo ra chính loại lỗi mà toàn bộ khối hậu xử lý ở mục 2.1.1 sinh ra để sửa.

### 2.2.4. Phóng đại và nội suy

Vùng biển do bộ phát hiện cắt ra thường chỉ cao **20–40 điểm ảnh**, trong khi mô-đun nhận dạng chuẩn hoá mọi ảnh đầu vào về chiều cao cố định **48 điểm ảnh**. Nếu đưa thẳng ảnh 20 điểm ảnh vào, mô-đun sẽ tự phóng đại bằng phép nội suy mặc định của nó. Đồ án chủ động phóng đại về **64 điểm ảnh** trước, để bước nội suy nằm trong tầm kiểm soát và diễn ra **trước** các bước tăng cường tương phản thay vì sau.

Thứ tự này quan trọng: phóng đại rồi mới áp CLAHE thì CLAHE làm việc trên lưới ô có đủ điểm ảnh để lược đồ mang ý nghĩa thống kê; làm ngược lại thì lưới 8 × 8 trên một ảnh cao 20 điểm ảnh cho mỗi ô chưa tới 3 hàng điểm ảnh.

### 2.2.5. Không gian màu HSV cho phân tích màu nền

Phân loại màu nền trong không gian RGB rất kém ổn định, vì ba kênh RGB **cùng thay đổi** khi độ sáng thay đổi: một biển vàng trong bóng râm và cùng biển đó dưới nắng cho hai bộ ba RGB rất khác nhau. Không gian **HSV** tách riêng **sắc độ (H)** khỏi **độ bão hoà (S)** và **độ sáng (V)**, nên sắc độ của biển vàng gần như không đổi theo điều kiện chiếu sáng — chỉ V thay đổi.

Đồ án vì vậy phân loại màu bằng cách thống kê tỉ lệ điểm ảnh rơi vào từng dải sắc độ và chọn dải chiếm ưu thế (chi tiết cài đặt ở mục 3.5).

### 2.2.6. Băm tri giác cho khử trùng lặp bộ dữ liệu

Bộ dữ liệu của đồ án hợp nhất từ nhiều nguồn công khai, mà các nguồn này **fork lẫn nhau**. Nếu một ảnh nằm ở tập huấn luyện dưới tên bộ này và ở tập kiểm thử dưới tên bộ khác thì **độ chính xác đo được đang đo khả năng ghi nhớ**, không phải khả năng tổng quát hoá.

So khớp theo mã băm mật mã (MD5, SHA) không dùng được, vì chỉ cần nén lại ảnh ở chất lượng khác là mã băm đổi hoàn toàn. Cần một hàm băm mà **ảnh giống nhau về mặt thị giác cho mã băm gần nhau**.

**Băm tri giác dựa trên biến đổi cosine rời rạc (pHash)** [15] hoạt động theo bốn bước: đưa ảnh về thang xám và kích thước 32 × 32; áp biến đổi cosine rời rạc hai chiều; **giữ lại khối 8 × 8 ở góc trên trái**, tức các hệ số **tần số thấp** mô tả cấu trúc tổng thể và loại bỏ chi tiết tần số cao; so từng hệ số với trung vị của khối để sinh **64 bit**. Khoảng cách giữa hai ảnh là **khoảng cách Hamming** giữa hai mã băm.

Việc giữ lại tần số thấp chính là điều khiến pHash bền vững trước nén, đổi kích thước và thay đổi độ sáng nhẹ — và cũng chính là **giới hạn của nó**, phân tích ở mục 3.2.3.

## 2.3. Phát hiện vùng biển số

### 2.3.1. Kiến trúc một giai đoạn và ý nghĩa của anchor-free

Họ hai giai đoạn (Faster R-CNN) sinh vùng đề xuất rồi phân loại từng đề xuất, cho độ chính xác cao nhưng độ trễ lớn; họ **một giai đoạn** (YOLO, SSD) hồi quy trực tiếp trong một lần lan truyền xuôi. Ràng buộc CPU của đồ án loại họ hai giai đoạn ngay từ đầu.

![](figures/fig-ch2-05.png)

**Hình 2.1.** Kiến trúc tổng quát backbone – neck – head của YOLO11 *(theo [8])*

Từ YOLOv8, họ YOLO chuyển sang **đầu dự đoán anchor-free**, và điều này có ý nghĩa riêng với bài toán biển số. Cách tiếp cận anchor-based hồi quy theo một tập hộp mẫu được thiết kế theo phân bố của bộ dữ liệu COCO; biển số **nằm ngoài phân bố đó** — một dòng khoảng 4,7:1, hai dòng khoảng 1,4:1, hai chế độ tỉ lệ cách xa nhau. Anchor-free hồi quy **trực tiếp khoảng cách từ tâm tới bốn cạnh**, nên xử lý được cả hai chế độ bằng một cơ chế duy nhất [8].

### 2.3.2. Chỉ số đánh giá

Với $TP$ dự đoán đúng, $FP$ dự đoán sai và $FN$ đối tượng bỏ sót:

$$\mathrm{Precision} = \frac{TP}{TP + FP}, \qquad \mathrm{Recall} = \frac{TP}{TP + FN}$$

<div align="right">(2.4)</div>

Với ALPR, **recall quan trọng hơn precision**: một biển bị bỏ sót là mất vĩnh viễn, trong khi một vùng báo nhầm sẽ bị khối hậu xử lý loại vì chuỗi không khớp cú pháp.

**AP** là diện tích dưới đường cong Precision–Recall; **mAP** là trung bình AP trên các lớp — bài toán này chỉ có một lớp nên mAP trùng AP. Hai biến thể **không được so sánh chéo với nhau**: `mAP@0,5` tính tại một ngưỡng IoU cố định 0,5, còn `mAP@0,5:0,95` lấy trung bình trên mười ngưỡng từ 0,50 đến 0,95. Vì `mAP@0,5` là số hạng lớn nhất trong mười số hạng của phép trung bình, trên cùng một mô hình và cùng một tập dữ liệu ta **luôn có** `mAP@0,5:0,95` ≤ `mAP@0,5`.

Khoảng cách giữa hai chỉ số này với biển số thường rất lớn, do hộp bao dẹt khiến một sai lệch nhỏ theo chiều cao làm IoU tụt nhanh. Đây là lý do đồ án lấy `mAP@0,5` làm chỉ tiêu chính nhưng vẫn báo cáo `mAP@0,5:0,95`: chỉ số thứ hai mới phản ánh **độ khít của vùng cắt** đưa sang bước nhận dạng.

## 2.4. Nhận dạng ký tự và điểm suy giảm trên văn bản hai dòng

### 2.4.1. Kiến trúc CRNN và hàm mất mát CTC

**CRNN** [14] gồm ba tầng: tầng tích chập trích đặc trưng và — điểm mấu chốt — **hạ chiều cao bản đồ đặc trưng về 1**, biến ảnh thành một **chuỗi vector theo chiều rộng**; tầng hồi quy mô hình hoá ngữ cảnh; tầng phiên mã giải chuỗi đó thành văn bản.

**Hàm mất mát CTC** [13] giải bài toán: biết chuỗi nhãn đúng nhưng **không biết mỗi ký tự nằm ở cột đặc trưng nào**. CTC thêm ký hiệu trống $\varepsilon$, định nghĩa ánh xạ $\mathcal{B}$ gộp ký tự lặp rồi xoá $\varepsilon$ — ví dụ $\mathcal{B}(\texttt{3}\varepsilon\texttt{00}\varepsilon\texttt{A}) = \texttt{30A}$ — và tính xác suất chuỗi nhãn $\mathbf{l}$ bằng tổng xác suất **mọi** đường đi thô ánh xạ về nó:

$$p(\mathbf{l} \mid \mathbf{x}) = \sum_{\boldsymbol{\pi} \in \mathcal{B}^{-1}(\mathbf{l})} \prod_{t=1}^{T} y^{t}_{\pi_{t}}$$

<div align="right">(2.5)</div>

Ưu điểm quyết định: **không cần nhãn vị trí từng ký tự**, lý do CTC là mặc định của hầu hết bộ nhận dạng ký tự mã nguồn mở.

![](figures/fig-ch2-crnn-ctc.png)

**Hình 2.2.** Kiến trúc CRNN và cách CTC gộp chuỗi thô. Điểm mấu chốt nằm ở
tầng tích chập: nó hạ **chiều cao về 1**, biến bản đồ đặc trưng hai chiều thành
một chuỗi vector — nhờ đó bài toán đọc ảnh trở thành bài toán đọc chuỗi.

### 2.4.2. Vì sao CTC gãy trên biển hai dòng

![](figures/fig-ch2-07.png)

**Hình 2.3.** Cơ chế sụp đổ của CTC trên ảnh văn bản hai dòng

Phép hạ chiều cao về 1 ở mục 2.4.1 **giả định toàn bộ văn bản nằm trên một dòng ngang**. Với ảnh hai dòng, mọi ký tự của dòng trên và dòng dưới bị **chiếu chồng lên nhau** vào cùng một cột đặc trưng, và giả định căn chỉnh đơn điệu giữa cột ảnh và chuỗi ký tự — nền tảng của CTC — không còn đúng. Hệ quả quan sát được là mô hình đọc theo thứ tự không xác định, ghép lẫn hai dòng, hoặc bỏ sót hẳn một dòng.

Vấn đề còn bị khuếch đại bởi một ràng buộc kích thước. Mô-đun nhận dạng chuẩn hoá mọi ảnh về chiều cao **48 điểm ảnh**. Biển xe mô tô có tỉ lệ khung hình khoảng 1,36, nên sau chuẩn hoá **mỗi hàng ký tự chỉ còn khoảng 24 điểm ảnh** — thấp hơn ngưỡng mà nét chữ còn tách rời được.

Hai quan sát này dẫn thẳng tới giải pháp xử lý ảnh ở mục 3.4: nếu vấn đề là *ảnh có hai dòng*, thì **biến nó thành ảnh một dòng trước khi đưa vào mô hình** — và làm sao cho hàng ký tự duy nhất đó nhận trọn ngân sách 48 điểm ảnh thay vì phải chia đôi.

### 2.4.3. Chỉ số CER và độ chính xác mức chuỗi

**CER** dựa trên khoảng cách Levenshtein, với $S$ ký tự thay thế, $D$ bị xoá, $I$ chèn thừa và $N$ tổng ký tự nhãn thật:

$$\mathrm{CER} = \frac{S + D + I}{N}$$

<div align="right">(2.6)</div>

CER **có thể vượt 1** khi chuỗi dự đoán dài hơn nhãn thật rất nhiều — đúng tình huống CTC gặp ảnh hai dòng.

**Độ chính xác mức chuỗi** đếm số biển có **toàn bộ** chuỗi khớp chính xác. Đây là chỉ số phản ánh đúng giá trị sử dụng, và quan hệ của nó với CER **bất lợi một cách không tuyến tính**: với biển 8 ký tự, nếu xác suất đọc đúng mỗi ký tự là $p$ thì xác suất đúng cả chuỗi là $p^{8}$. Với $p = 0{,}99$ con số này chỉ còn khoảng $0{,}923$; với $p = 0{,}95$ nó tụt xuống khoảng $0{,}663$. Đây là lý do một bộ nhận dạng có CER rất tốt trên văn bản tài liệu vẫn có thể thất bại trên biển số.
