# CHƯƠNG 2. CƠ SỞ LÝ THUYẾT

Chương đặt nền lý thuyết và tư liệu cho phần thiết kế. Nguyên tắc xuyên suốt: **mọi con số gắn nguồn tại chỗ, mọi cảnh báo về phạm vi áp dụng giữ nguyên** — lĩnh vực này hay công bố số trên 99% nhưng đo trên tập dữ liệu và giao thức rất khác nhau.

## 2.1. Phạm vi và bố cục cơ sở lý thuyết

Một hệ thống ALPR gồm bốn khối nối tiếp — **phát hiện vùng biển**, **nắn chỉnh và tiền xử lý**, **nhận dạng ký tự**, **hậu xử lý theo quy chuẩn** — và độ chính xác cuối cùng là **tích** của độ chính xác từng khối, nên một khối yếu kéo cả chuỗi xuống. Đồ án đi theo hướng **two-stage** (phát hiện rồi nhận dạng riêng) kết hợp bộ nhận dạng **segmentation-free**; căn cứ của lựa chọn đó trình bày ở Chương 3.

Chương này chỉ giữ phần lý thuyết **ràng buộc trực tiếp một quyết định của hệ thống**: quy chuẩn biển số Việt Nam (2.2) — cơ sở của bộ luật hậu xử lý; kiến trúc YOLO11 và các chỉ số đánh giá khối phát hiện (2.3); kiến trúc CRNN/CTC cùng **điểm gãy của nó trên văn bản nhiều dòng** (2.4) — nền tảng lý thuyết của rủi ro R-04 và của đóng góp kỹ thuật lõi; và khảo sát công trình liên quan cùng sáu khoảng trống nghiên cứu (2.5). Phần bối cảnh lĩnh vực — định nghĩa và ứng dụng ALPR, lịch sử từ xử lý ảnh cổ điển tới học sâu, bảng phân loại các hướng tiếp cận, và các khái niệm nền IoU/NMS — đặt ở **Phụ lục N** để thân bài không phải mang kiến thức đại cương.

## 2.2. Quy chuẩn biển số xe Việt Nam

### 2.2.1. Căn cứ pháp lý hiện hành

**Cảnh báo văn bản hết hiệu lực.** Nhiều tài liệu, kể cả bài báo 2023 – 2024, vẫn viện dẫn **Thông tư 24/2023/TT-BCA** — **đã hết hiệu lực từ 01/01/2025** [12]<!-- bocongan_2023_tt24 -->; đồ án chỉ nhắc như bối cảnh lịch sử.

Bốn văn bản căn cứ: **TT 79/2024/TT-BCA** hiệu lực 01/01/2025, thay TT 24/2023, quy định cấu trúc biển, seri, màu sắc [8]<!-- bocongan_2024_tt79 -->; **TT 13/2025/TT-BCA** sửa đổi TT 79/2024 [9]<!-- bocongan_2025_tt13 -->; **TT 51/2025/TT-BCA** hiệu lực 01/7/2025, **thay toàn bộ Phụ lục mã tỉnh** sau sáp nhập còn 34 tỉnh/thành [10]<!-- bocongan_2025_tt51 -->; **QCVN 08:2024/BCA** kèm TT 81/2024/TT-BCA, hiệu lực 01/01/2025, quy chuẩn quốc gia về kết cấu, kích thước, vật liệu [11]<!-- bocongan_2024_qcvn08 -->. Biển quân đội thuộc TT 169/2021/TT-BQP [15]<!-- boquocphong_2021_tt169 -->, **ngoài phạm vi** TT 79/2024.

TT 79/2024 quy định **nội dung** biển — cơ sở biểu thức chính quy; QCVN 08:2024/BCA quy định **hình thức vật lý** — cơ sở ngưỡng tỷ lệ khung hình; module chuẩn hoá cần cả hai. Khung pháp lý đổi **ba lần trong hai năm** là rủi ro kỹ thuật trực tiếp [19]; hệ quả ở mục 2.2.7.

### 2.2.2. Cấu trúc biển số ô tô và xe máy

**a) Biển số ô tô** trong nước: **8 ký tự chữ–số**, ba thành phần — **mã địa phương** 2 chữ số trong 81 mã hợp lệ thuộc dải 11 – 99 [10], [14]<!-- thuviennhadat_2025_kyhieu34tinh -->; **seri 1 chữ cái** trong 20 chữ với biển trắng và vàng, 11 chữ với biển xanh [13]<!-- bocongan_2024_nhandienbienso -->; **số thứ tự 5 chữ số**, 000.01 – 999.99 [8] — ví dụ `30A-123.45`, `51K-999.99`, `80B-123.45` (Cục CSGT). Trên đường vẫn còn **biển 4 chữ số kiểu cũ** (`29A-1234`); xe đã đăng ký **không bắt buộc đổi biển** [26]<!-- chinhphu_2025_kyhieubienso --> nên biểu thức chính quy phải chấp nhận nhóm thứ tự **4 hoặc 5 chữ số**.

**b) Biển số xe máy** cá nhân: **9 ký tự** — 2 chữ số mã tỉnh, 2 chữ cái seri, 5 chữ số thứ tự (`29-HA 002.33`); quy tắc 2 chữ cái áp dụng từ **15/8/2023**, giữ trong TT 79/2024 [27]<!-- chinhphu_2023_seribiensoxemay -->. Hai kiểu seri cùng lưu hành: **mới** 2 chữ cái (`29-AA 123.45`) và **cũ** 1 chữ + 1 số (`29-B1 123.45`), vẫn hợp pháp [27]. Cách hiểu "biển 1 chữ 1 số chỉ dùng đến hết 2025" là **không chính xác** — điều khoản 31/12/2025 chỉ nói về dùng nốt phôi biển cũ; **biển kiểu cũ còn trên đường hàng chục năm**, biểu thức chính quy phải chấp nhận cả hai.

**c) Một nhập nhằng cấu trúc quan trọng.** Chuỗi 8 ký tự dạng *hai số – một chữ – năm số* khớp **đồng thời** biển ô tô và biển xe máy kiểu cũ sau khi bỏ dấu phân cách — **không thể phân loại phương tiện chỉ bằng chuỗi ký tự**, lý do hệ thống lưu trường số dòng như thuộc tính độc lập (Chương 4).

**d) Seri không còn cho biết loại xe.** Trước 2025 seri mang ngữ nghĩa (`A` xe con, `B` xe khách, `C`, `K` xe tải), **từ 01/01/2025 bị bãi bỏ**, seri cấp tuần tự [28]<!-- otocomvn_2025_seridangky -->; heuristic "seri C suy ra xe tải" **sai về pháp lý**, tín hiệu phân loại duy nhất còn hợp lệ là **màu nền biển** (mục 2.2.5).

### 2.2.3. Mã tỉnh, thành phố

Từ 01/7/2025 cả nước còn **34 tỉnh, thành phố**; ký hiệu sau hợp nhất **bao gồm toàn bộ ký hiệu của các địa phương được hợp nhất** [26], biển cũ không mất giá trị pháp lý. Dải 11 – 99 có **89 số**; theo Phụ lục TT 51/2025 có **81 mã đang dùng** (80 mã địa phương + mã 80 của Cục CSGT) và **8 mã không dùng**: **13, 42, 44, 45, 46, 87, 91, 96** [14]. TP. Hồ Chí Minh 13 mã (41; 50 – 59; 61; 72); Hà Nội 6 mã (29; 30 – 33; 40) [14].

Kiểm tra mã tỉnh loại khoảng 9,0% không gian tìm kiếm ở hai ký tự đầu, và quan trọng hơn: biến lỗi OCR hai vị trí đầu từ **sai âm thầm** thành **sai phát hiện được** — đọc ra `46A-123.45` thì biết ngay mã 46 không tồn tại và hạ cờ hợp lệ. Giả thuyết mã 13 là mã cũ của Hà Bắc **chưa kiểm chứng được nguồn chính thức**, chỉ nêu tham khảo.

### 2.2.4. Tập ký tự seri và các chữ cái bị loại trừ

Mục dễ bị trình bày sai nhất của chương. Biển trắng và vàng chữ đen dùng seri **một trong 20 chữ cái** [13]; đối chiếu 26 chữ Latin thì vắng `I J O Q R W` — nhưng **suy diễn "26 − 20 = 6 chữ bị loại trừ" là SAI**: danh sách 20 chữ **chỉ áp dụng cho chữ cái thứ nhất**; ở **vị trí thứ hai** của seri xe máy là tập khác — **có R, không có G**. Hợp hai vị trí, tập chữ không bao giờ xuất hiện trên biển Việt Nam chỉ gồm **5 chữ: I, J, O, Q, W**; chữ R còn ở ký hiệu đặc biệt `R`, `RM` của rơ moóc [29]<!-- khobiensodep_2025_kyhieudacbiet -->.

**Bảng 2.1.** Tổng hợp các tập ký tự seri

| Tập | Số lượng | Nội dung |
|---|:--:|---|
| Chữ cái thứ nhất của seri | 20 | A B C D E F **G** H K L M N P S T U V X Y Z |
| Chữ cái thứ hai của seri xe máy | 20 | A B C D E F H K L M N P **R** S T U V X Y Z |
| Seri biển nền xanh | 11 | A B C D E F G H K L M |
| **Bị loại trừ khỏi toàn hệ thống** | **5** | **I, J, O, Q, W** |
| Tập ký tự an toàn tối thiểu cho OCR | 21 | 20 chữ ở vị trí thứ nhất, hợp thêm R |

**c) Hệ quả thứ nhất — ràng buộc theo vị trí, không phải tập phẳng.** Xe mô tô biển xanh dùng 1 trong 11 chữ cái kết hợp 1 chữ số **1 – 9**, không có số 0 [13]. G hợp lệ ở vị trí thứ nhất nhưng không ở vị trí thứ hai, R ngược lại; bộ luật dùng danh sách phẳng sẽ **vừa bỏ sót lỗi vừa sửa nhầm ký tự đúng** — điểm đồ án xử lý khác các mô tả hiện có (Chương 1). Ký tự nhóm I, J, O, Q, W ở vị trí chữ cái chắc chắn là lỗi; ánh xạ có cơ sở hình dạng: `O → 0`, `I → 1`, `Q → 0`; `J`, `W` không có ứng viên hiển nhiên nên chỉ **hạ cờ hợp lệ**. Chữ R **không** thuộc nhóm này và **tuyệt đối không được ánh xạ đi**.

**d) Hệ quả thứ hai — tập ký tự huấn luyện OCR.** Huấn luyện theo "20 chữ cái" thì mô hình **không bao giờ dự đoán được chữ R**, sai hệ thống trên mọi biển xe máy có R ở vị trí thứ hai; mất mát ở **tầng mô hình**, hậu xử lý không cứu được.

> **Khuyến nghị áp dụng cho đồ án.** Huấn luyện tập ký tự **đầy đủ A–Z và 0–9, tức 36 ký tự**, áp ràng buộc hợp lệ ở **tầng hậu xử lý**. Nếu buộc phải thu hẹp, dùng **21 chữ cái** (20 chữ hợp thêm R), tuyệt đối không dùng 20.

**e) Hạn chế kiểm chứng cần giữ nguyên khi trình bày.** Hai danh sách chữ cái ở Bảng 2.1 **chưa được đối chiếu với toàn văn Điều 34 TT 79/2024/TT-BCA**: bản PDF chính thức là bản quét không có lớp văn bản, cổng tra cứu pháp luật chặn truy cập tự động. Kết luận về chữ R dựa trên nguồn thứ cấp, cần xác nhận lại khi tiếp cận được toàn văn. Ghi rõ hạn chế này là bắt buộc và không được lược bỏ khi rút gọn văn bản.

**f) Các ký hiệu seri đặc biệt** [29]: `CD`, `MK`, `MĐ` (xe máy chuyên dùng, máy kéo, xe máy điện); `R`, `RM` (rơ moóc); `HC`; `KT`, `LD`, `DA`; `T`, `TĐ`. Hai bẫy: **chữ R xuất hiện ở đây** dù ngoài tập 20 chữ, củng cố khuyến nghị (d); `TĐ`, `MĐ` chứa `Đ` — ngoài Latin ASCII — nên OCR gần như chắc chắn trả `D`, module chuẩn hoá phải chấp nhận cả hai dạng.

### 2.2.5. Màu nền và ý nghĩa

**Bảng 2.2.** Màu nền biển số và đối tượng áp dụng [13]

| Màu nền / màu chữ | Đối tượng | Ghi chú cho ALPR |
|---|---|---|
| Trắng / đen | Tổ chức, cá nhân trong nước, xe **không** kinh doanh vận tải | Phổ biến nhất |
| Vàng / đen | Xe **kinh doanh vận tải** | Tín hiệu phân loại **duy nhất còn hợp lệ** |
| Xanh dương / trắng | Cơ quan Đảng, Nhà nước, công an | Seri chỉ dùng 11 chữ cái |
| Trắng / **đỏ** | Xe ngoại giao (`NG`) và tổ chức quốc tế (`QT`) | Cấu trúc chuỗi khác hẳn [30]<!-- vietnamnet_2023_biensongoaigiao --> |
| Đỏ / trắng | Xe quân đội và doanh nghiệp quân đội | **Ngoài phạm vi** TT 79/2024, thuộc TT 169/2021/TT-BQP [15] |

QCVN 08:2024/BCA chỉ quy định **4 tổ hợp màu**, **không có nền đỏ** [11] — biển quân đội do Bộ Quốc phòng quản lý riêng [15]. **Xe điện không có biển riêng**: xe năng lượng sạch **không được cấp biển xanh lá**, dùng biển thường kèm biểu tượng [31]<!-- conganlangson_2024_tt79 --> — không phát hiện được xe điện qua màu biển. Màu nền là tín hiệu phân loại duy nhất còn hợp lệ [32]<!-- thuvienphapluat_2025_mausacseri -->; nhưng module chuẩn hoá làm việc trên chuỗi ký tự, phân loại theo màu ngoài phạm vi của nó.

### 2.2.6. Kích thước vật lý và tỷ lệ khung hình

Cơ sở định lượng phân biệt biển một dòng với hai dòng — then chốt với rủi ro R-04 (mục 2.4.3). Ô tô được cấp **02** biển: 01 ngắn (**2 dòng**), 01 dài (**1 dòng**); xe mô tô, xe gắn máy, rơ moóc được cấp **01** biển **2 dòng** [32] — **một ô tô mang cùng chuỗi ký tự trên hai biển hình dạng hoàn toàn khác nhau**.

**Bảng 2.3.** Kích thước và tỷ lệ khung hình của các loại biển số [11]

| Loại biển | Kích thước (dài × cao) | Tỷ lệ khung hình | Số dòng |
|---|---|:--:|:--:|
| Ô tô — biển **dài** | **520 × 110 mm** | **4,727** | **1 dòng** |
| Ô tô — biển **ngắn** | **330 × 165 mm** | **2,000** | **2 dòng** |
| **Xe mô tô, xe gắn máy** | **190 × 140 mm** | **1,357** | **2 dòng** |

> **⚠️ Cảnh báo về mốc hiệu lực của bộ số liệu kích thước.** Bộ số liệu trên **chỉ đúng từ 01/01/2025**; tiêu chuẩn trước đó quy định biển ô tô ngắn **200 × 280 mm**, biển dài **110 × 470 mm**, và rất nhiều tài liệu thứ cấp — kể cả bài báo năm 2023 — vẫn dùng bộ số cũ. Mọi trích dẫn kích thước biển số **bắt buộc ghi kèm mốc hiệu lực**; nếu không, người phản biện đối chiếu văn bản hiện hành sẽ kết luận là sai.

**Không loại biển nào rơi vào khoảng (2,000 ; 4,727)** — khoảng trống rộng 2,727 đơn vị. Đồ án đề xuất: **AR < 2,5** → **2 dòng**; **AR > 3,0** → **1 dòng**; **2,5 ≤ AR ≤ 3,0** — **vùng nghi ngờ**, thử cả hai nhánh, chọn kết quả tin cậy cao hơn.

> **Hai lưu ý bắt buộc. Thứ nhất, đây là đề xuất của đồ án, KHÔNG phải quy định pháp luật:** ba giá trị 1,357 / 2,000 / 4,727 trích được từ QCVN 08:2024/BCA, nhưng ngưỡng 2,5 và 3,0 là **suy luận thiết kế của tác giả**, phải kiểm chứng thực nghiệm; gán bộ ngưỡng cho văn bản pháp luật là lỗi trích dẫn. **Thứ hai:** phải đo tỷ lệ khung hình trên ảnh **đã nắn chỉnh phối cảnh** hoặc hộp bao xoay tối thiểu, **không** đo trên hộp bao thẳng trục — biển một dòng nghiêng 30° có tỷ lệ hộp thẳng trục tụt dưới 3,0 và bị phân loại nhầm.

**d) Bố cục biển hai dòng.** Ô tô biển ngắn: `30A` / `123.45`; xe máy kiểu mới: `29-AA` / `123.45`; xe máy kiểu cũ: `29-B1` / `123.45`, dòng dưới 4 – 5 chữ số.

**e) Dấu phân cách.** Các nguồn mô tả vị trí dấu gạch ngang không nhất quán, không tra cứu được nguyên văn quy cách in của QCVN 08:2024/BCA; đồ án chọn quyết định an toàn: **module chuẩn hoá loại bỏ toàn bộ ký tự phân cách rồi kiểm tra hợp lệ trên chuỗi chữ–số thuần**.

**f) Hai thông số vật lý khác.** Biển hợp kim nhôm, phản quang, chữ dập nổi cao **(1,7 ± 0,1) mm** [11]; chữ dập nổi tạo bóng và loá theo góc chiếu — nguyên nhân lỗi `B` đọc thành `3`; bù lại font và vật liệu chuẩn hoá toàn quốc là yếu tố tốt cho OCR.

### 2.2.7. Ý nghĩa đối với thiết kế hệ thống nhận dạng

Bảy dữ kiện kéo theo bảy quyết định thiết kế: **81 mã tỉnh trong dải 89 số** biến lỗi OCR hai ký tự đầu thành sai phát hiện được; **tập seri khác theo vị trí** buộc ràng buộc **theo vị trí** và tập huấn luyện OCR đủ 36 ký tự; **hai kiểu seri xe máy, nhóm thứ tự 4 hoặc 5 chữ số** buộc biểu thức chính quy đa nhánh; **chuỗi 8 ký tự khớp hai loại biển** nên phải lưu số dòng độc lập; **seri không còn cho biết loại xe** nên cấm heuristic suy loại phương tiện; **khoảng trống tỷ lệ khung hình 2,727** là cơ sở ngưỡng phân loại bố cục; **khung pháp lý đổi ba lần trong hai năm** buộc hậu xử lý tách rời mô hình để cập nhật độc lập [19].

Về mức đóng góp: luận điểm dự kiến ban đầu — "loại trừ 6 chữ I J O Q R W" — là **sai**, và việc sửa làm **yếu đi** đóng góp theo tiêu chí thu hẹp không gian tìm kiếm; đổi lại phần giá trị chuyển sang ràng buộc **phụ thuộc vị trí trong chuỗi**: danh sách phẳng sẽ sai hệ thống trên toàn bộ lớp biển xe máy có R ở vị trí thứ hai — lỗi mà bộ luật của đồ án ngăn được. Đóng góp là **đúng đắn về pháp lý và cấu trúc**, không phải cải thiện lớn về không gian tìm kiếm.

## 2.3. Cơ sở lý thuyết về phát hiện đối tượng

### 2.3.1. Kiến trúc YOLO: nguyên lý one-stage và anchor-free

**Họ two-stage** (Faster R-CNN) sinh vùng đề xuất rồi phân loại từng đề xuất — độ trễ cao; **họ one-stage** (YOLO, SSD, RetinaNet) hồi quy trực tiếp trong một lần lan truyền xuôi — thời gian thực. Ràng buộc CPU loại họ two-stage từ đầu; một nghiên cứu ALPR trên 50.000 ảnh và 10.000 video clip kết luận nhóm YOLO (v5–v10) vượt trội Faster R-CNN và SSD cả độ chính xác lẫn thời gian suy luận [48]<!-- scirep_2025_advanceddl -->.

![](figures/fig-ch2-05.png)

**Hình 2.1.** Kiến trúc tổng quát backbone – neck – head của YOLO11 *(theo [49], [16])*

Ba phần: **backbone** trích đặc trưng, kết thúc bằng SPPF gộp đa tỷ lệ; **neck** hợp nhất đặc trưng nhiều tầng; **head** sinh dự đoán — từ YOLOv8 dùng **anchor-free split head** [49]<!-- jocher_2023_yolov8 -->. Anchor-free có ý nghĩa riêng với biển số: anchor-based hồi quy theo tập hộp mẫu thiết kế theo phân bố COCO — biển số nằm ngoài phân bố đó (một dòng ≈ 4,7:1, hai dòng ≈ 1,4:1); anchor-free hồi quy **trực tiếp khoảng cách tâm đến bốn cạnh**, xử lý cả hai chế độ tỷ lệ bằng một cơ chế [16]<!-- jocher_2024_yolo11 -->.

### 2.3.2. YOLO11: các cải tiến kiến trúc

Bài tổng quan độc lập xác định ba thành phần chính của YOLO11: **C3k2**, **SPPF**, **C2PSA** [50]<!-- khanam_2024_yolov11overview -->; phần dưới đối chiếu trực tiếp mã nguồn Ultralytics [51]<!-- ultralytics_2026_blockpy -->. **a) C3k2 — là C2f có thể hoán đổi khối con:** `C3k2` **kế thừa trực tiếp từ `C2f`** của YOLOv8; khác biệt duy nhất là một cờ — tắt thì **giống hệt C2f**, bật thì dùng khối `C3k` tuỳ chỉnh kích thước nhân [51]. YOLO11 giảm tham số mà giữ độ chính xác vì không đổi triết lý CSP, chỉ cấu hình linh hoạt hơn. **b) C2PSA — thành phần YOLOv8 hoàn toàn không có**, khác biệt kiến trúc thực sự; đặt **ngay sau SPPF** để attention tái phân bổ trọng số theo vị trí không gian. Ultralytics khẳng định cơ chế này cải thiện phát hiện **đối tượng nhỏ** và **che khuất phức tạp** so với YOLOv8 [52]<!-- ultralytics_2025_yolo11vsyolov8 -->.

> **Lưu ý về mức độ chứng minh.** Phát biểu về đối tượng nhỏ là **định tính**: Ultralytics không công bố AP_small/AP_medium/AP_large theo chuẩn COCO cho từng biến thể, nên không thể chứng minh định lượng YOLO11 hơn YOLOv8 bao nhiêu trên đối tượng nhỏ [16]. Đồ án phải **tự đo trên dữ liệu của mình**; kết quả ở Chương 5.

**Bảng 2.4.** So sánh khác biệt kiến trúc giữa các phiên bản YOLO gần đây

| Phiên bản | Khối backbone | Cơ chế attention | Đầu dự đoán | NMS | Điểm mới đáng chú ý nhất |
|---|---|---|---|:--:|---|
| YOLOv8 [49] | C2f | Không có | Anchor-free, tách nhánh | Có | Chuyển sang anchor-free |
| YOLOv9 [53]<!-- wang_2024_yolov9 --> | GELAN | Không có | Anchor-free | Có | PGI chống mất mát thông tin |
| YOLOv10 [46] | Rank-guided blocks | Partial self-attention | Hai đầu song song | **Không** | Consistent dual assignments |
| **YOLO11** [16] | **C3k2** (kế thừa C2f) | **C2PSA** sau SPPF | Anchor-free, tách nhánh | Có | C2PSA cải thiện đối tượng nhỏ |
| YOLOv12 [54]<!-- tian_2025_yolov12 --> / YOLOv13 [55]<!-- lei_2025_yolov13 --> | R-ELAN / DS-C3k2 | Area Attention / HyperACE (hypergraph) | Anchor-free | Có | Attention làm trung tâm; tương quan bậc cao, FullPAD |
| YOLO26 [47] | Kế thừa dòng Ultralytics | Kế thừa dòng Ultralytics | **Bỏ DFL** | **Không** (mặc định) | Bỏ DFL, dễ xuất và lượng tử hoá |

Luận cứ chọn YOLO11 trình bày đầy đủ ở mục 3.2.

### 2.3.3. Các chỉ số đánh giá khối phát hiện

**a) Precision, Recall và F1.** Với $TP$ dự đoán đúng, $FP$ dự đoán sai, $FN$ đối tượng bỏ sót:

$$\mathrm{Precision} = \frac{TP}{TP + FP}, \qquad \mathrm{Recall} = \frac{TP}{TP + FN}, \qquad F_1 = \frac{2 \cdot \mathrm{Precision} \cdot \mathrm{Recall}}{\mathrm{Precision} + \mathrm{Recall}}$$

<div align="right">(2.2)</div>

Với ALPR, **recall của detection quan trọng hơn precision**: biển bỏ sót là mất vĩnh viễn, vùng báo nhầm bị hậu xử lý loại vì chuỗi không khớp cú pháp.

**b) AP và mAP.** AP là diện tích dưới đường cong Precision–Recall; mAP là trung bình AP trên $N$ lớp — đồ án có $N = 1$ nên mAP trùng AP:

$$\mathrm{AP} = \int_0^1 p(r)\, \mathrm{d}r, \qquad \mathrm{mAP} = \frac{1}{N}\sum_{i=1}^{N} \mathrm{AP}_i$$

<div align="right">(2.3)</div>

**c) mAP@0.5 và mAP@0.5:0.95 — hai chỉ số khác nhau, không được so sánh chéo.** **mAP@0.5** tính tại **một ngưỡng IoU cố định 0,5**; **mAP@0.5:0.95** lấy **trung bình trên 10 ngưỡng** từ 0,5 đến 0,95 bước 0,05:

$$\mathrm{mAP@0.5\!:\!0.95} = \frac{1}{10}\sum_{t \in \{0{,}50;\, 0{,}55;\, \ldots;\, 0{,}95\}} \mathrm{mAP@}t$$

<div align="right">(2.4)</div>

> **Trên cùng một mô hình và cùng một tập dữ liệu, mAP@0.5:0.95 LUÔN nhỏ hơn hoặc bằng mAP@0.5** — vì mAP@0.5 là một trong mười số hạng của phép trung bình ở (2.4), và là số hạng lớn nhất.

Khoảng cách giữa hai chỉ số với biển số thường rất lớn do hộp bao dẹt, ba minh chứng: **87,2%** so với **46,5%** trên biển Ấn Độ [56]<!-- batra_2022_yolov5 -->; **0,906** so với **0,631** ở một nghiên cứu YOLOv11 [57]<!-- jaic_2025_yolov11alpr -->; **99,5%** so với **80,7%** trên biển xe máy Indonesia [58]<!-- jcosine_2025_yolo11plate -->. Cả ba xác nhận: **biển số dễ phát hiện nhưng khó khớp hộp bao chính xác**.

> **⚠️ Cảnh báo phương pháp luận bắt buộc giữ nguyên.** Một cách trình bày phổ biến và **sai** là đặt mAP@0.5 của một nghiên cứu ALPR (khoảng 0,90 – 0,99) cạnh mAP@0.5:0.95 trên COCO của cùng lớp mô hình (khoảng 0,395 ở phân khúc nano [16]) rồi kết luận "bài toán biển số dễ hơn bài toán COCO". Đây là **so sánh giữa hai chỉ số có định nghĩa khác nhau**, và theo hệ quả toán học nêu trên, chênh lệch giữa chúng **không mang bất kỳ thông tin nào** về độ khó tương đối. Phép đối chiếu hợp lệ duy nhất là mAP@0.5 với mAP@0.5, hoặc mAP@0.5:0.95 với mAP@0.5:0.95, **và trên cùng một tập dữ liệu**; ngay cả khi cùng định nghĩa nhưng khác tập dữ liệu, so sánh cũng chỉ để cảm nhận độ khó chứ không làm luận cứ cho quyết định kỹ thuật. Lỗi này đã được phát hiện và sửa trong quá trình khảo sát tài liệu của đồ án, nêu tường minh ở đây vì hội đồng phản biện phát hiện rất nhanh.

**d) Chỉ tiêu của đồ án.** Vì mục tiêu detection là cắt vùng crop đủ tốt để OCR đọc, đồ án dùng **mAP@0.5 làm chỉ tiêu chính**, **mAP@0.5:0.95 vẫn báo cáo** nhưng không đặt ngưỡng chấp nhận; giá trị ở Chương 5. **e) mIoU.** Một số công trình dùng IoU trung bình toàn tập — nhóm Học viện Kỹ thuật Quân sự báo cáo mIoU 95,01% trên biển Việt Nam [59]<!-- lqdtu_2021_vietnameselpr --> — chỉ số khác mAP, không so sánh chéo được.

## 2.4. Cơ sở lý thuyết về nhận dạng ký tự

### 2.4.1. Bài toán OCR và đặc thù khi áp dụng cho biển số

**OCR** (*Optical Character Recognition*) chuyển văn bản trong ảnh thành chuỗi, thường gồm **text detection** khoanh vùng rồi **text recognition** đọc từng vùng. Sai lầm phổ biến: lấy thẳng bảng xếp hạng OCR phổ thông làm căn cứ chọn engine cho ALPR.

**Bảng 2.5.** So sánh OCR văn bản tài liệu và OCR biển số xe

| Chiều so sánh | OCR văn bản tài liệu | OCR biển số xe |
|---|---|---|
| Nguồn ảnh | Ảnh quét hoặc chụp tài liệu, gần chính diện | Ảnh cảnh ngoài trời, phối cảnh nghiêng, chói sáng, nhoè do chuyển động |
| Độ dài chuỗi và tập ký tự | Hàng trăm đến hàng nghìn ký tự; tập lớn, mở, kèm dấu | 7 – 9 ký tự; tập đóng — **chỉ A–Z và 0–9** |
| Bố cục | Nhiều dòng, đa cột, ngắt dòng tuỳ ý | Cố định: 1 hoặc 2 dòng theo quy chuẩn nhà nước |
| Ràng buộc cú pháp và vai trò hậu xử lý | Gần như không có; hậu xử lý phụ trợ | Rất chặt, kiểm tra được bằng biểu thức chính quy; hậu xử lý **bắt buộc**, là lớp sửa lỗi chính |
| Tiêu chí đánh giá | CER / WER — chấp nhận sai lẻ tẻ | **Khớp chuỗi tuyệt đối** — sai 1 ký tự là hỏng cả bản ghi |
| Giá trị của thông tin ngôn ngữ | Cao — mô hình ngôn ngữ sửa lỗi hiệu quả | **Thấp** — không có từ vựng để dựa vào |

Bốn hệ quả: **tập ký tự đóng là tài sản** — biển Việt Nam chỉ dùng A–Z, 0–9 không dấu nên ưu thế "hỗ trợ tiếng Việt" là **vô nghĩa**, từ điển đa ngôn ngữ còn tăng không gian nhầm lẫn; **ràng buộc cú pháp bù điểm yếu whitelist** qua hậu xử lý theo vị trí (Chương 4); đây là **ảnh cảnh, không phải ảnh tài liệu** — benchmark trên văn bản chỉ tham chiếu xu hướng; **bố cục hai dòng là lớp bài toán riêng** (mục 2.4.3).

### 2.4.2. Kiến trúc CRNN và hàm mất mát CTC

**CRNN** gồm ba tầng: **tầng tích chập** trích đặc trưng và — điểm mấu chốt — downsample chiều cao **về 1**, biến bản đồ đặc trưng thành **chuỗi vector theo chiều rộng**; **tầng hồi quy** (Bi-LSTM) mô hình hoá ngữ cảnh hai chiều; **tầng phiên mã** giải mã thành chuỗi, thường bằng CTC. EasyOCR dùng đúng kiến trúc này (ResNet, Bi-LSTM, CTC) [60]<!-- jaided_2025_easyocrdeepwiki -->; PaddleOCR dùng SVTR-LCNet kết hợp GTC [17]<!-- cui_2026_ppocrv5 -->, vẫn thuộc họ CTC.

**Hàm mất mát CTC** giải vấn đề: biết chuỗi nhãn đúng nhưng **không biết mỗi ký tự nằm ở cột đặc trưng nào**. CTC thêm ký hiệu trống $\varepsilon$, định nghĩa ánh xạ $\mathcal{B}$ gộp ký tự lặp rồi xoá $\varepsilon$ — ví dụ $\mathcal{B}(\texttt{3}\varepsilon\texttt{00}\varepsilon\texttt{A}) = \texttt{30A}$ — và tính xác suất chuỗi nhãn $\mathbf{l}$ bằng tổng xác suất **mọi** đường đi thô $\boldsymbol{\pi}$ ánh xạ về nó:

$$p(\mathbf{l} \mid \mathbf{x}) = \sum_{\boldsymbol{\pi} \in \mathcal{B}^{-1}(\mathbf{l})} \prod_{t=1}^{T} y^{t}_{\pi_t}, \qquad \mathcal{L}_{\mathrm{CTC}} = -\log p(\mathbf{l} \mid \mathbf{x})$$

<div align="right">(2.3)</div>

Tổng ở (2.3) tính hiệu quả bằng quy hoạch động tiến–lùi. Ưu điểm quyết định: **không cần nhãn vị trí từng ký tự** — lý do CTC là mặc định của hầu hết engine OCR mã nguồn mở, và lý do LPRNet đạt 3 ms/biển trên GPU GTX 1080, 1,3 ms trên CPU i7-6700K mà vẫn 95% accuracy trên biển Trung Quốc [40].

### 2.4.3. Vì sao kiến trúc CTC gặp khó với văn bản nhiều dòng

Mục kỹ thuật quan trọng nhất của chương: nền tảng lý thuyết cho rủi ro **R-04** ("khả năng Cao, ảnh hưởng Cao") — ở Việt Nam nơi xe máy áp đảo, biển hai dòng là dạng phổ biến chứ không phải ngoại lệ.

**a) Giả định alignment đơn điệu của CTC.** Ánh xạ $\mathcal{B}$ ở (2.3) hoạt động trên **chuỗi một chiều** theo trục $t$ — chính là **trục chiều rộng ảnh**: CTC giả định ngầm ký tự **tuần tự trái sang phải trên một dòng duy nhất**, đó là bản chất toán học của hàm mất mát chứ không phải tuỳ chọn cấu hình. Ảnh hai dòng vi phạm giả định: chiều cao đã downsample **về 1**, mỗi vector cột chứa **cả hai ký tự chồng nhau theo chiều dọc**, mạng cho ra chuỗi lộn xộn hoặc chỉ đọc một dòng [61]<!-- arxiv_2019_arbitraryshaped -->.

![](figures/fig-ch2-07.png)

**Hình 2.2.** Cơ chế sụp đổ của CTC trên ảnh văn bản hai dòng *(theo [61])*

**b) Bằng chứng cụ thể trong PaddleOCR — `rec_image_shape`.** Module recognition PP-OCRv3/v4/v5 resize mọi ảnh về **chiều cao cố định 48 pixel** (`rec_image_shape = 3 × 48 × 320`) [62]<!-- paddleocr_nd_issue14109 -->. Áp vào biển xe máy tỷ lệ 1,357: đưa thẳng crop 2 dòng thì chiều rộng sau resize chỉ còn $48 \times 1{,}357 \approx$ **65 px**, mỗi dòng **≈ 24 px** cao — **không đọc được**; sau tách dòng và ghép ngang (AR $\approx$ 5,43) chiều rộng $\approx$ **261 px**, mỗi dòng trọn **48 px** — **đọc được**. Kết luận kiến trúc: **không tồn tại cấu hình nào của module recognition PP-OCR giải được bài toán này**; phải giải ở **tầng trên** bằng module tách dòng, hoặc thay hẳn mô hình recognition — lý do mục 3.3 kết luận chọn engine OCR **không quyết định** thành bại của R-04.

**c) Bằng chứng định lượng độc lập.** *Điểm gãy của một hệ thống thương mại trưởng thành:* trên tập kiểm thử cân bằng của **bộ RodoSol-ALPR (Brazil)** — 4.000 ảnh ô tô biển một dòng và 4.000 ảnh xe máy biển hai dòng — OpenALPR nhận đúng **94,3%** ô tô nhưng chỉ **45,7%** xe máy, chênh **48,6 điểm phần trăm** trên cùng hệ thống, cùng tập kiểm thử, không biến số nào khác ngoài bố cục biển [7]<!-- laroca_2022_crossdataset -->; rộng hơn, cả 12 phương pháp và 2 hệ thống thương mại đều **không vượt 70% recognition rate** trên bộ này, có công trình phải **loại bỏ hoàn toàn xe máy** vì không sửa được phương pháp [7].

> **⚠️ Cảnh báo phạm vi áp dụng — bắt buộc giữ nguyên.** Cặp số 94,3% / 45,7% được đo trên bộ **RodoSol-ALPR của Brazil**, **không phải trên dữ liệu Việt Nam**. Nó được dẫn ở đây như một *analogue* định lượng về độ khó vượt trội của biển hai dòng xe máy tại một quốc gia cũng có tỷ lệ xe máy cao. Trích dẫn nhầm cặp số này thành số liệu Việt Nam là lỗi trích dẫn nghiêm trọng.

*Riêng kích thước ảnh đầu vào đã đủ phá huỷ hiệu năng:* trong PatrolVision, cùng mô hình chỉ đổi kích thước ảnh vào — 240×80 cho biển một dòng đạt 83%, hai dòng **chỉ 30%**; 288×200 bao phủ cả hai bố cục cho tổng thể 67% [63]<!-- arxiv_2025_patrolvision -->. *Hiệu quả của tách và ghép:* các cài đặt tham chiếu cho biển hai tầng Trung Quốc đều cắt crop thành hai phần rồi ghép ngang trước khi vào OCR [64]<!-- we0091234_nd_doubleplatesplit -->. **d) Nắn chỉnh trước khi tách:** chiếu ngang tìm điểm trũng và phân ngưỡng theo toạ độ dọc đều **vô hiệu khi biển nghiêng**; nghiên cứu cổ điển đặt hiệu chỉnh contour ngang ở tiền xử lý [35], cài đặt hiện đại nắn phối cảnh bốn điểm trước khi tách [64].

**Bảng 2.6.** Các phương pháp phân biệt biển một dòng và biển hai dòng

| Phương án | Cơ chế | Ưu điểm và hạn chế |
|---|---|---|
| **PA-1.** Lấy lớp từ chính detector | YOLO xuất thêm một lớp: `0` = một dòng, `1` = hai dòng [64] | Chính xác nhất, chi phí gần 0 khi tự gán nhãn; phải gán nhãn hai lớp từ đầu |
| **PA-2.** Ngưỡng tỷ lệ khung hình | So ngưỡng suy từ quy chuẩn (mục 2.2.6) | Rẻ nhất, không cần huấn luyện; sai khi biển nghiêng nếu đo trên hộp bao thô |
| **PA-3.** Chiếu ngang tìm điểm trũng | Tổng cường độ pixel theo hàng; biển hai dòng có điểm trũng sâu ở giữa [35] | Vị trí cắt thích nghi từng ảnh; điểm trũng biến mất khi biển nghiêng |
| **PA-4.** Phân cụm hộp bao theo toạ độ dọc | Dùng text detection của engine OCR, gom nhóm theo tâm dọc [65]<!-- paddlepaddle_nd_ocrpipeline --> | Tái dùng kết quả sẵn có; phụ thuộc chất lượng text detection trên crop nhỏ |
| **PA-5.** Kiểm tra tính thẳng hàng của ký tự | Nối tâm ký tự trái nhất và phải nhất, đo độ lệch các ký tự còn lại [66]<!-- trungdinh22_nd_helper --> | Trực quan, dễ gỡ lỗi; cần phát hiện từng ký tự, ngưỡng pixel phụ thuộc độ phân giải |

**e) Lựa chọn của đồ án: PA-1 chính, PA-2 dự phòng** — thiết kế ở Chương 4, kết quả đo ở Chương 5. **f) Tinh chỉnh là bắt buộc, không phải tuỳ chọn:** ứng dụng nhận dạng biển số chính thức của PaddleOCR trên CCPD cho thấy tinh chỉnh nâng detection Hmean **76,12% → 99,00%** và recognition **90,97% → 94,54%** [67]<!-- paddlepaddle_nd_plateapp -->.

> **Lưu ý cách đọc số liệu này.** Tài liệu gốc ghi recognition pre-trained 0,00%, nhưng con số đó **không** nghĩa là PaddleOCR không đọc được biển: mô hình pre-trained sinh thêm một ký tự đặc biệt khiến chuỗi trượt tiêu chí khớp tuyệt đối; hậu xử lý loại ký tự đó là đạt 90,97% [67]. Luận điểm đúng là **tinh chỉnh nâng 90,97% → 94,54%**; số liệu đo trên **biển Trung Quốc một dòng**, không chứng minh điều gì về biển hai dòng Việt Nam.

**g) Vì sao không chọn kiến trúc thuần Transformer.** TrOCR resize ảnh thành ô vuông 384×384, chia 576 mảnh, mã hoá BEiT, giải mã RoBERTa [68]<!-- li_2021_trocr -->; bị loại vì ba lý do: huấn luyện cho văn bản **một dòng** nên với ảnh nhiều dòng **có thể sinh ảo giác** [69]<!-- roboflow_2025_trocr -->; quá lớn cho CPU — 334 đến 558 triệu tham số [68], nặng hơn recognition PP-OCRv5 mobile (5 triệu [17]) từ 67 đến 112 lần; và ép ảnh về ô vuông bất lợi cho crop biển vốn rất rộng (AR ≈ 4,73) hoặc gần vuông (AR ≈ 1,36).

### 2.4.4. Chỉ số CER và độ chính xác mức chuỗi

**a) CER** (*Character Error Rate*) dựa trên khoảng cách Levenshtein, với $S$ thay thế, $D$ xoá, $I$ chèn, $N$ tổng ký tự chuỗi thực; độ chính xác mức ký tự là $1 - \mathrm{CER}$:

$$\mathrm{CER} = \frac{S + D + I}{N}$$

<div align="right">(2.4)</div>

CER **có thể vượt 1** khi chuỗi dự đoán dài hơn chuỗi thực rất nhiều — đúng tình huống CTC gặp ảnh hai dòng. **b) WER** tương tự nhưng đơn vị là từ; một công trình biển Việt Nam báo cáo WER 0,014 trên bãi đỗ xe trong nhà [70]<!-- dang_2024_crnn -->. **c) Độ chính xác mức chuỗi** (*plate-level accuracy*, *exact match*) là chỉ số nghiêm ngặt nhất:

$$\mathrm{Acc}_{\text{plate}} = \frac{\#\{\text{biển số có TOÀN BỘ chuỗi ký tự khớp chính xác}\}}{\#\{\text{tổng số biển số trong tập kiểm thử}\}}$$

<div align="right">(2.5)</div>

Sai một ký tự vẫn tính sai hoàn toàn — phản ánh đúng giá trị sử dụng: chuỗi sai hoặc không khớp bản ghi nào, hoặc khớp nhầm sang phương tiện khác. Quan hệ CER – mức chuỗi **không tuyến tính và bất lợi**: biển 8 ký tự với xác suất đúng mỗi ký tự $p$, xác suất đúng cả chuỗi là $p^{8}$ — $p = 0{,}99$ chỉ còn $\approx 0{,}923$, $p = 0{,}95$ tụt xuống $\approx 0{,}663$ — lý do engine có CER rất tốt trên văn bản vẫn thất bại trên biển số. **d) End-to-end Recognition Rate** — tỷ lệ biển đọc đúng hoàn toàn trên **toàn bộ pipeline** — là chỉ số duy nhất phản ánh lỗi tích luỹ, chỉ tiêu quan trọng nhất của đồ án; cuộc thi ICPR 2026 về biển độ phân giải thấp dùng chỉ số này làm chính, đội vô địch đạt 82,13% [71]<!-- laroca_2026_icprlrlpr -->. Kèm theo là chỉ số vận hành: **độ trễ** p50, p95, p99 (bắt buộc kèm cấu hình phần cứng), **kích thước mô hình**, **bộ nhớ thường trú**, **số tham số**; giá trị ở Chương 5.

## 2.5. Các công trình liên quan

### 2.5.1. Công trình quốc tế tiêu biểu


Khảo sát lập danh mục **21 công trình quốc tế tiêu biểu** từ 2018 đến 2026, kèm phương pháp, bộ dữ liệu đánh giá và kết quả công bố của từng công trình; **bảng đầy đủ ở Phụ lục J.1**. Sáu mốc kiến trúc còn lại — số 4, 5, 12, 15, 18, 20 — **không kèm số liệu đối chứng công bố được**: Li–Wang–Shen 2019, mạng thống nhất một lần lan truyền xuôi [39]; Zhang và cộng sự 2020, attention 2D, công bố **CLPD** [41]; Nascimento và cộng sự 2024, **LCDNet** với hàm mất mát **LCOFL**, GAN có bộ phân biệt là OCR [78]<!-- nascimento_2024_lpsr -->; Meyer và cộng sự 2025, **SaLT** giảm phụ thuộc cú pháp [19]; Shabaninia và cộng sự 2025, nhận dạng **không phụ thuộc layout** trên IR-LPR, UFPR-ALPR, AOLP [42]; Gong–Liu 2026, **LP-LLM** trên Qwen3-VL với Character Slot Queries và LoRA [44].

**Ba lưu ý bắt buộc khi đọc danh mục ở Phụ lục J.1. Thứ nhất, không so sánh trực tiếp giữa các dòng** — mỗi công trình đo trên tập và định nghĩa chỉ số khác nhau; nghiêm trọng nhất là dòng 10: **tuyệt đối không rút gọn thành "Tesseract (93%) tốt hơn LPRNet (90%)"** — 93% chỉ trên dữ liệu **tổng hợp** và **sau tiền xử lý**, còn 90% trên biển **thật**. **Thứ hai, mọi con số tốc độ phải kèm phần cứng:** VSNet 149 FPS và YOLOv5-PDLPR 159,8 FPS đều **trên GPU**, 1,3 ms/biển của LPRNet là **trên CPU** — nhanh hơn con số GPU (3 ms) đúng theo bài báo gốc, thường do chi phí khởi tạo, truyền dữ liệu khi lô nhỏ; Batra và cộng sự đo 4,8 ms trên **Nvidia T4** — GPU máy chủ, không phải thiết bị biên. **Thứ ba, VLM đánh đổi tốc độ lấy tổng quát:** VehiclePaliGemma 87,6% nhưng chỉ **7 FPS trên A100-80GB** [43], chậm hơn hai bậc độ lớn so với 149 – 160 FPS của CNN chuyên dụng — lý do đồ án loại hướng này (Phụ lục N.3).

Quan sát tổng hợp: **các con số vượt 99% chủ yếu đạt trên tập dễ, giao thức dễ dãi** — 99,9% trên CCPD-Base nhưng 94,1% trên CCPD-Challenge [73]; giao thức xuyên tập làm trung bình tụt 82,4% → 74,5%, nặng nhất 28,1 điểm [7]; dữ liệu độ phân giải thấp thật: đội vô địch chỉ 82,13% [71]. Bài toán ALPR **chưa được giải quyết xong** như cách nó thường được mô tả.

### 2.5.2. Công trình về biển số Việt Nam

Nghiên cứu ALPR cho biển Việt Nam chủ yếu công bố tại hội nghị, tạp chí khu vực, **không xuất hiện trên các benchmark quốc tế lớn**, phần lớn đánh giá trên tập tự thu thập không công khai — so sánh công bằng gần như bất khả thi.

Khảo sát lập danh mục **mười công trình về biển số Việt Nam** từ 2012 đến 2024, kèm nơi công bố, phương pháp và kết quả — **bảng đầy đủ ở Phụ lục J.3**. Ba đặc điểm chung nổi lên. **Phần lớn công bố tại hội nghị hoặc tạp chí khu vực và đánh giá trên tập tự thu thập không công khai**, nên so sánh công bằng gần như bất khả thi. **Nhiều công trình không công bố số liệu cụ thể** — có bài chỉ ghi "độ chính xác cao", có bài không nêu độ chính xác cuối, có cuộc thi không công bố kết quả xếp hạng. Và **không công trình nào báo cáo tách riêng độ chính xác biển một dòng với biển hai dòng**, dù đó là phân biệt quan trọng nhất với phân bố phương tiện Việt Nam.

Con số cao nhất cho biển Việt Nam là **99,28% mức chuỗi** [59] nhưng **không dùng làm mốc so sánh được**: đo trên tập riêng không công khai, không tái lập được, độ khó không mô tả định lượng nên không so được với 91,3% trên PTITPlates [79]; chưa tồn tại benchmark công khai chuẩn cho biển Việt Nam kiểu UFPR-ALPR hay RodoSol-ALPR của Brazil. Cũng không dùng trực tiếp được mô hình huấn luyện trên dữ liệu nước ngoài: Việt Nam có **77 triệu xe máy (9/2024), 770 xe trên 1.000 dân**, hàng cao nhất thế giới [1]<!-- dantri_2024_77trieuxemay --> — **biển hai dòng gần vuông chiếm đa số tuyệt đối** trong khi CCPD, AOLP, SSIG lấy ô tô làm trung tâm; mật độ cao gây che khuất; biển xe máy đặt thấp dễ dính bùn, bị che, biến dạng. CCPD chỉ có **biển một dòng, ký tự Hán tự, 7 ký tự, không có biển hai dòng**. Giao thức *leave-one-dataset-out* làm trung bình tụt 7,9 điểm, nặng nhất 28,1 điểm, nguyên nhân quy cho khác biệt **font chữ trên biển** [7]; với Việt Nam, dịch chuyển miền còn lớn hơn.

> **Kết luận kiến trúc.** Huấn luyện trước trên dữ liệu quốc tế chỉ nên áp dụng cho khối **detection**. Khối **recognition bắt buộc huấn luyện hoặc tinh chỉnh trên dữ liệu Việt Nam**, hậu xử lý viết riêng theo quy chuẩn ở mục 2.2.

Khoảng tám kho mã nguồn mở về biển Việt Nam đang hoạt động, phần lớn **không công bố số liệu độ chính xác**, nhiều kho không ghi giấy phép; phía thương mại, các con số 98 – 99,9% do nhà cung cấp tự công bố trên định nghĩa "ảnh chuẩn" không thống nhất — **không dùng làm mốc so sánh học thuật**.

### 2.5.3. Các bộ dữ liệu chuẩn trong lĩnh vực


Khảo sát đối chiếu **chín bộ dữ liệu chuẩn** của lĩnh vực theo quy mô, đặc điểm và **giấy phép sử dụng** — cột giấy phép quyết định bộ nào dùng được cho đồ án này; **bảng đầy đủ ở Phụ lục J.2**.

**Ba nhận xét. Thứ nhất, bộ lớn nhất không phải bộ sạch nhất:** Laroca và cộng sự **loại trừ tường minh CCPD** khỏi thí nghiệm tổng quát hoá vì ảnh nén quá mạnh, sai số gán nhãn đỉnh lớn [7] — dùng được CCPD cho huấn luyện trước detection nhưng **không nên** tin toạ độ bốn đỉnh cho nắn chỉnh. **Thứ hai, báo cáo chỉ trên tập con dễ là không đủ:** khoảng cách 5,8 điểm giữa CCPD-Base (99,9%) và CCPD-Challenge (94,1%) [73] cho thấy con số trung bình che giấu điểm gãy — cơ sở cho quyết định **báo cáo tách bạch theo nhóm điều kiện**, đặc biệt tách một dòng và hai dòng. **Thứ ba, dữ liệu biển Việt Nam là điểm nghẽn thực sự:** **không tồn tại bộ dữ liệu biển Việt Nam công khai nào được bình duyệt học thuật**; nguồn hiện có là GitHub cá nhân, Roboflow Universe, Kaggle. Bộ lớn nhất, đủ nhãn nhất là VNLP: **37.300 ảnh** (19.086 một dòng, 18.211 hai dòng), annotation mức ký tự, tách rõ hai loại gần 50/50 — nhưng **không ghi giấy phép**, cần xin xác nhận tác giả trước khi dùng trong công bố [91]<!-- fictlabs_2025_vnlp -->.

Ba đặc điểm chung của dữ liệu Việt Nam: phần lớn chỉ có hộp bao một lớp — chỉ dùng cho detection; rất ít bộ phân biệt tường minh một dòng và hai dòng; **không bộ nào gán nhãn chuỗi biển số đầy đủ** — khoảng trống lớn nhất. Tin tốt: hiệu năng bão hoà quanh **4.750 ảnh thật (99,0% độ chính xác)**, và chỉ cần **300 ảnh thật** kết hợp sinh dữ liệu cùng tăng cường là tương đương 200.000 ảnh thật [92]<!-- arxiv_2018_howmanyplates -->; kho dữ liệu Việt Nam công khai vượt xa ngưỡng cho detection, nút thắt là **nhãn mức ký tự và nhãn chuỗi**. Có công cụ sinh ảnh biển Việt Nam tổng hợp **cả một dòng lẫn hai dòng** [93]<!-- nndam_2024_plategenerator -->.

### 2.5.4. Khoảng trống nghiên cứu và định vị đề tài

**Bảng 2.7.** Sáu khoảng trống nghiên cứu và cách đồ án lấp

| # | Khoảng trống được xác định từ khảo sát | Cách đồ án lấp |
|:--:|---|---|
| 1 | **Chưa có nghiên cứu Việt Nam nào công bố bảng so sánh tách riêng độ chính xác biển một dòng và biển hai dòng trên cùng một hệ thống** (mục 2.5.2) | Đồ án báo cáo tách bạch hai con số này |
| 2 | **Chưa có nghiên cứu Việt Nam nào mô tả có hệ thống bộ luật hậu xử lý ràng buộc theo VỊ TRÍ trong chuỗi** — các mô tả hiện có dừng ở danh sách phẳng, phần lớn dùng nhầm con số 20 chữ cái cho toàn chuỗi (mục 2.2.4) | Thiết kế hậu xử lý **theo từng vị trí**, **đo tách bạch trước và sau hậu xử lý**; hiệu số là đóng góp định lượng |
| 3 | **Hầu hết công trình trong nước chỉ báo cáo mAP của detection**, không báo cáo end-to-end mức chuỗi (mục 2.5.2) | Báo cáo cả hai, end-to-end là chỉ tiêu quan trọng nhất |
| 4 | **Không tồn tại benchmark công khai nào so sánh các engine OCR trên riêng ảnh biển số xe máy Việt Nam hai dòng** (mục 3.3) | ✅ **Đã lấp 03/08/2026** — đo ba engine trên 2.801 biển, cùng tầng bao quanh: PaddleOCR 68,87% · EasyOCR 14,28% · Tesseract 10,28% (mục 3.3.3) |
| 5 | **Số liệu hiệu năng thường công bố không kèm phần cứng** (mục 2.5.1) | Mọi số liệu hiệu năng kèm: model CPU, số luồng, kích thước ảnh vào, backend suy luận, cỡ mẫu đo |
| 6 | **Hầu hết kho mã nguồn mở Việt Nam không công bố số liệu và không có kiến trúc phần mềm** (mục 2.5.2) | Công bố đầy đủ giao thức đo, tập kiểm thử, toàn bộ chỉ số; bàn giao hệ thống có API, giao diện, cơ sở dữ liệu, kiểm thử, đóng gói |

Sáu khoảng trống đều thuộc loại **kỹ nghệ và báo cáo**, không phải thuật toán: đồ án không đặt mục tiêu vượt các con số trên 99% ở Phụ lục J.1 — trong đó 99,28% của nhóm Học viện Kỹ thuật Quân sự đo trên tập riêng không công khai — và mọi số liệu hiệu năng của đồ án là **số liệu CPU**, không so trực tiếp với FPS đo trên GPU.

> Tuyên bố trung thực đầy đủ về mức đóng góp, cùng bốn điều đồ án **không** tuyên bố, đặt ở **mục 1.6.1 và 1.6.8** (Chương 1) — nơi chính danh để tuyên bố đóng góp.

## 2.6. Kết luận chương

**Thứ nhất, bài toán ALPR chưa được giải quyết xong:** giao thức nghiêm ngặt hơn làm độ chính xác trung bình sụt gần 8 điểm, nặng nhất 28,1 điểm [7]; trên dữ liệu độ phân giải thấp thật, đội vô địch chỉ đạt 82,13% [71]. **Thứ hai, đồ án theo two-stage kết hợp bộ nhận dạng segmentation-free** — hệ quả của ràng buộc thay được bộ OCR mà không huấn luyện lại toàn hệ thống. **Thứ ba, khối phát hiện dùng YOLO11n:** phiên bản duy nhất vừa có số liệu tốc độ CPU chính thức, vừa có cơ chế kiến trúc (C2PSA, đầu anchor-free) phù hợp đối tượng nhỏ và tỷ lệ khung hình dẹt, vừa có bằng chứng thực nghiệm dày trên ALPR; **mAP@0.5 và mAP@0.5:0.95 là hai chỉ số khác nhau, chênh lệch giữa chúng không mang thông tin về độ khó** — đồ án dùng mAP@0.5 làm chỉ tiêu chính, báo cáo mAP@0.5:0.95 kèm theo, không đặt ngưỡng chấp nhận.

**Thứ tư, bài toán biển hai dòng có nền tảng lý thuyết rõ ràng và không thể giải bằng cách đổi engine.** CTC giả định alignment đơn điệu trên **một dòng duy nhất**; module recognition resize về chiều cao 48 pixel nên crop biển xe máy tỷ lệ 1,357 bị nén còn khoảng 65 pixel chiều rộng, mỗi dòng khoảng 24 pixel — không đủ để đọc. Bằng chứng độc lập: OpenALPR đạt 94,3% trên biển một dòng nhưng chỉ 45,7% trên biển hai dòng, chênh 48,6 điểm, đo trên bộ RodoSol-ALPR của Brazil [7]. **Vấn đề phải giải ở tầng trên bằng module tách dòng, không phải bằng cách đổi engine OCR.**

**Thứ năm, quy chuẩn biển số Việt Nam đã đặc tả đủ để cài đặt, với ba điểm đính chính.** Căn cứ hiện hành: TT 79/2024/TT-BCA sửa đổi bởi TT 13/2025 và TT 51/2025, cùng QCVN 08:2024/BCA — TT 24/2023 đã hết hiệu lực từ 01/01/2025. 81 mã tỉnh đang dùng, 8 mã không dùng. Quan trọng nhất: **tập chữ cái bị loại trừ chỉ gồm 5 chữ I, J, O, Q, W chứ không phải 6; chữ R hợp lệ ở vị trí thứ hai của seri xe máy** — hậu xử lý phải ràng buộc **theo từng vị trí trong chuỗi**, tập ký tự huấn luyện OCR đủ 36 ký tự. Ba tỷ lệ khung hình (1,357 / 2,000 / 4,727) tạo khoảng trống 2,727 đơn vị — cơ sở ngưỡng phân loại bố cục đồ án đề xuất.

**Thứ sáu, sáu khoảng trống nghiên cứu đã được xác định** (Bảng 2.7), cả sáu có cách lấp cụ thể. Khoảng trống số 4 — *không tồn tại benchmark công khai nào so sánh các engine OCR trên riêng ảnh biển số Việt Nam* — **đã được lấp bằng phép đo của chính đồ án**: ba engine chạy trên 2.801 biển với **cùng một tầng bao quanh**, chỉ khác engine, cho PaddleOCR **68,87%**, EasyOCR 14,28%, Tesseract 10,28% (mục 3.3.3). Nhờ đó, PaddleOCR được giữ **vì có bằng chứng đo được trên đúng miền dữ liệu**, không còn là một baseline để ngỏ như bản khảo sát ban đầu ghi nhận. Kèm theo là tuyên bố trung thực về giới hạn: đồ án không đặt mục tiêu kết quả tốt nhất lĩnh vực, không đề xuất kiến trúc mạng mới, không giải các thách thức mở như biển độ phân giải rất thấp hay tổng quát hoá xuyên tập dữ liệu.

Ba nguyên tắc phương pháp áp dụng nguyên vẹn cho phần thực nghiệm: **mọi số liệu hiệu năng kèm cấu hình phần cứng và cỡ mẫu đo**; **báo cáo tách bạch theo bố cục biển và điều kiện ảnh**; **không so sánh chéo giữa các chỉ số khác định nghĩa hoặc khác tập dữ liệu**. Chương tiếp theo chuyển sang lựa chọn công nghệ, rồi tới thiết kế hệ thống.
