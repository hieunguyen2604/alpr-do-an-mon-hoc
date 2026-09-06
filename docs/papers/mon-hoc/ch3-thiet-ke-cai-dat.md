# CHƯƠNG 3. THIẾT KẾ VÀ CÀI ĐẶT

## 3.1. Kiến trúc tổng thể

Toàn bộ luồng xử lý của đường ống nhận dạng trình bày ở Hình 3.1.

![](figures/fig-ch4-03.png)

**Hình 3.1.**[]{#fig-3-1} Luồng xử lý của đường ống nhận dạng; các khối tô đỏ là nhánh biển hai dòng

Đường ống gồm bốn khối nối tiếp, và độ chính xác cuối cùng là **tích** của độ chính xác từng khối — một khối yếu kéo cả chuỗi xuống:

1. **Phát hiện vùng biển** — YOLO11n trên ảnh đầu vào, trả về danh sách hộp bao;
2. **Xử lý ảnh vùng biển** — cắt, phân loại bố cục theo hình học, tách và ghép, rồi phóng đại, tăng cường tương phản và khử nhiễu (mục 3.4);
3. **Nhận dạng ký tự** — PaddleOCR trên dải ảnh một dòng đã chuẩn bị;
4. **Hậu xử lý theo quy chuẩn** — chuẩn hoá chuỗi theo bộ luật ràng buộc vị trí (mục 3.6).

Khối 2 và khối 4 là phần do đồ án tự thiết kế; khối 1 và khối 3 dùng mô hình có sẵn.

Toàn bộ đường ống được đóng gói thành một **gói Python độc lập không phụ thuộc tầng web**. Ràng buộc này không phải hình thức: nó cho phép cùng một mã chạy được trong sổ tay thử nghiệm, trong kịch bản đo đạc và trong dịch vụ đang vận hành. Bài học ngược lại đã xảy ra trong quá trình thực hiện đồ án: một kịch bản đo **chép lại** các bước của đường ống thay vì **gọi** nó, nên mỗi bước mới thêm vào đường ống đều rơi ra ngoài phép đo, và số liệu công bố mô tả một hệ thống ngắn hơn hệ thống thực tế.

Ba lớp trừu tượng có hợp đồng thống nhất: lớp phát hiện trả danh sách vùng biển đã lọc ngưỡng và khử chồng lấn, **danh sách rỗng là kết quả hợp lệ chứ không phải lỗi**; lớp nhận dạng trả chuỗi thô kèm độ tin cậy, **không** tự sửa lỗi ký tự; lớp chuẩn hoá trả về cả chuỗi không hợp lệ kèm cờ đánh dấu. Chính việc lớp nhận dạng không được phép tự sửa lỗi là điều kiện để **đo tách bạch** đóng góp của khối hậu xử lý ở mục 4.3.2.

## 3.2. Xây dựng bộ dữ liệu

### 3.2.1. Đường ống sáu bước

![](figures/fig-ch5-01.png)

**Hình 3.2.**[]{#fig-3-2} Đường ống sáu bước xây dựng bộ dữ liệu

Hình 3.2 tóm tắt sáu bước; mỗi bước là một kịch bản độc lập sinh báo cáo dạng dữ liệu có cấu trúc; một kịch bản điều phối chạy toàn chuỗi bằng một lệnh. Kết quả: **15.133 ảnh** hợp nhất từ **7 bộ công khai**, sau khi loại **11.978 ảnh trùng lặp (44,2%)** từ **27.111 ảnh** ban đầu. Chia theo tỉ lệ 70/20/10 thành **10.592 / 3.027 / 1.514 ảnh** (Bảng 3.1).

**Bảng 3.1.**[]{#tbl-3-1} Đóng góp của từng bộ dữ liệu trước và sau khử trùng lặp

| # | Bộ dữ liệu | Vào hợp nhất | Còn lại | Bị loại |
|:--:|---|---:|---:|---:|
| 1 | roboflow_school_fuhih | 8.357 | **6.868** | 17,8% |
| 2 | hf_vn_plates_segment | 4.578 | **4.375** | 4,4% |
| 3 | roboflow_traffic_camera | 3.843 | **3.162** | 17,7% |
| 4 | roboflow_eric_nguyen | 840 | **353** | 58,0% |
| 5 | roboflow_demo_tracking | 236 | **235** | 0,4% |
| 6 | roboflow_cuong_ta | 8.254 | **140** | **98,3%** |
| 7 | roboflow_tran_ngoc_xuan_tin | 1.005 | **0** | **100%** |
| | **Tổng** † | **27.111** | **15.133** | **44,2%** |

† Cột *Vào hợp nhất* cộng lại được 27.113; bước hợp nhất gạt hai ảnh nằm trong danh sách loại trừ ra trước khi ghi (`skipped_excluded = 2` trong báo cáo hợp nhất), nên tổng thực ghi là 27.111.

### 3.2.2. Khử trùng lặp chéo bộ

Bảng trên là lý do bước này bắt buộc phải có. Một bộ vào hợp nhất với **1.005 ảnh và ra với 0 ảnh** — toàn bộ nội dung của nó đã có sẵn trong các bộ khác. Hệ quả trực tiếp: **không được cộng dồn số ảnh công bố của từng bộ để suy ra quy mô thật**.

Vét cạn mọi cặp trong 27.111 ảnh là khoảng 367 triệu phép so sánh, không khả thi. Kịch bản dùng **băm đa chỉ mục**: cắt mã băm 64 bit thành `ngưỡng + 1` dải. Theo nguyên lý chuồng bồ câu, hai mã băm khác nhau **tối đa** `ngưỡng` bit bắt buộc phải trùng khớp hoàn toàn trên **ít nhất một dải**. Tập ứng viên thu được vì vậy chứa **mọi** cặp thật, rồi được xác minh lại bằng khoảng cách Hamming chính xác — thuật toán là **chính xác, không xấp xỉ**.

Bước chia tập giữ **mọi thành viên của một nhóm trùng lặp trong cùng một tập con**, nên những bản trùng không bị xoá cũng không thể rò rỉ giữa tập huấn luyện và tập kiểm thử.

### 3.2.3. Giới hạn của băm tri giác: nó tóm tắt khung ảnh, không tóm tắt chiếc xe

Đây là **giới hạn không khắc phục được** bằng công cụ hiện có, và đồ án ghi nhận thay vì bỏ qua.

Một lần kiểm tra độc lập ở ngưỡng Hamming 10 trên phiên bản đầu của bộ dữ liệu tìm thấy **619 cặp gần trùng giữa tập huấn luyện và tập kiểm thử**; kiểm bằng mắt cho thấy đó là **cùng một chiếc xe, cùng chuỗi biển số, xuất hiện ở cả hai tập**. Đường ống không bắt được vì bước chia tập gom nhóm ở ngưỡng 5 và lần kiểm tra đầu cũng đo lại ở đúng ngưỡng 5 — một **lập luận vòng tròn**: đo ở ngưỡng đã dùng để gộp thì chỉ chứng minh bước gộp đã chạy đúng đặc tả, không chứng minh thêm điều gì.

Nâng ngưỡng cũng không giải quyết được, và lý do nằm ngay ở cơ chế của pHash trình bày ở mục 2.2.6. Mã băm mô tả **cấu trúc tần số thấp của toàn khung ảnh**, nên hai chiếc xe khác nhau đi qua **cùng một camera** có khoảng cách Hamming rất nhỏ — vì 90% khung hình (mặt đường, vạch kẻ, nền) giống hệt nhau. Đánh đổi vì vậy không thoát được:

- **ngưỡng thấp** bỏ sót các cặp "cùng xe, khác ngày";
- **ngưỡng cao** gộp nhầm hàng nghìn ảnh xe khác nhau chụp cùng một camera.

Số liệu xác nhận: ở ngưỡng 12 còn **791 cặp**, ở ngưỡng 15 là **3.529 cặp**, ở ngưỡng 20 lên **137.506 cặp** — mức mà phần lớn đã là dương tính giả.

**Kết luận trung thực:** đồ án khẳng định được *bước khử trùng lặp ở ngưỡng 10 đã chạy đúng đặc tả*, và **không** khẳng định được *tập kiểm thử độc lập với tập huấn luyện*. Rò rỉ ở mức ngữ nghĩa cần so khớp theo chuỗi biển số hoặc đặc trưng phương tiện mới phát hiện được. Mọi chỉ số ở mục 4.2 vì vậy phải đọc như **cận trên lạc quan**.

## 3.3. Huấn luyện bộ phát hiện

Cấu hình lượt huấn luyện chính thức được trích từ tệp tham số do thư viện tự sinh — bản ghi *đã thực thi* chứ không phải *dự định* (Bảng 3.2).

**Bảng 3.2.**[]{#tbl-3-2} Siêu tham số lượt huấn luyện chính thức

| Tham số | Giá trị | Lý do |
|---|---|---|
| Mô hình khởi đầu | YOLO11n tiền huấn luyện COCO, **2.590.035** tham số | Biến thể nhỏ nhất, do ràng buộc CPU |
| Độ phân giải đầu vào | **640** | Đúng theo chỉ tiêu; cũng là độ phân giải mọi số liệu tốc độ CPU chính thức được đo |
| Số epoch · kích thước lô | **20** · 8 | Ngân sách thời gian CPU |
| Thuật toán tối ưu | AdamW, tốc độ học ban đầu 0,001, lịch cosine | |
| Hạt giống ngẫu nhiên | **42**, kèm chế độ tất định | Chỉ chạy được một lượt nên ít nhất phải tái lập được |
| **Lật ngang** | **Tắt hoàn toàn** | Lệch có chủ ý so với mặc định — xem dưới |

Việc **tắt phép lật ngang** là quyết định xử lý ảnh đáng chú ý nhất trong cấu hình này. Lật ngang là phép tăng cường dữ liệu mặc định và hữu ích trong hầu hết bài toán phát hiện, nhưng ở đây nó sinh ra **ký tự đối xứng gương** — một phân bố không bao giờ xuất hiện trong thực tế. Giữ nó lại là dạy mô hình một bất biến mà bài toán không có.

**Chi phí:** **30,2 phút mỗi epoch**, tổng **36.181 giây tương đương 10,05 giờ** liên tục trên CPU. Chi phí này khiến **tìm kiếm siêu tham số bất khả thi**: đồ án báo cáo *một* cấu hình huấn luyện, không phải kết quả của một quá trình tối ưu, và mọi chỉ số là kết quả **một lần chạy** không có khoảng tin cậy.

## 3.4. Khối xử lý ảnh vùng biển số

Đây là phần trọng tâm của đồ án. Đầu vào là vùng ảnh do bộ phát hiện cắt ra; đầu ra là một **dải ảnh một dòng** đưa sang bộ nhận dạng.

### 3.4.1. Chuỗi bước và nguyên tắc bật tắt độc lập

Mọi bước trong mục này đều **bật tắt được độc lập** qua biến cấu hình — điều kiện để chương 4 **bóc tách đóng góp của từng bước**. Thứ tự trên **luồng xử lý chính**:

> cắt vùng → ước lượng số dòng → *(nếu hai dòng)* tách hai nửa → ghép ngang → phóng đại → thang xám → CLAHE → lọc song phương → nhận dạng

Ước lượng số dòng chạy trên vùng cắt thô (các bước tăng cường phía sau không làm đổi tỉ lệ khung hình); tiền xử lý chạy trên dải ảnh **đã ghép** để CLAHE cân bằng tương phản trên một hàng ký tự liền mạch; còn bước hiệu chỉnh góc nghiêng (Deskew) không nằm trên luồng xử lý chính — nó thuộc cơ chế thử lại đa tầng ở mục 3.4.6.

![](figures/fig-pipeline-strip.png)

**Hình 3.3.**[]{#fig-3-3} Toàn bộ chuỗi xử lý trên một biển thật, ảnh chụp sau từng bước

Hình 3.3 là kết quả chạy **chính các hàm của mô hình đề xuất**: mỗi khung là mảng ảnh thật ở đầu ra của bước tương ứng. Khung 3 và khung 4 cho thấy trực tiếp điều cả mục này mô tả bằng chữ — **tỉ lệ khung hình nhảy từ 1,12 lên 4,42**, hai hàng ký tự cao 30 px thành một hàng duy nhất nhận trọn 50 px. Phần chân hàng trên lọt vào nửa dưới ở khung 3 không phải lỗi cắt mà là vùng chồng lấn của mục 3.4.4.

### 3.4.2. Tiền xử lý

Ba bước độc lập, cơ sở lý thuyết ở mục 2.2:

- **Chuyển thang xám**, vì ký tự không mang thông tin phân biệt trong kênh màu.
- **CLAHE**, hệ số giới hạn **2,0** trên lưới ô **8 × 8**, để xử lý mảng chói cục bộ do bề mặt phản quang.
- **Lọc song phương** thay cho làm mờ Gauss, để khử nhiễu mà không phá biên — yếu tố quyết định phân biệt các cặp ký tự đồng hình.

Vùng biển được **phóng đại về 64 điểm ảnh** chiều cao trước toàn bộ chuỗi trên, vì ảnh do bộ phát hiện sinh ra thường chỉ cao 20–40 điểm ảnh.

### 3.4.3. Ước lượng số dòng bằng tỉ lệ khung hình

Số dòng suy từ tỉ lệ chiều rộng trên chiều cao của vùng biển, **ngưỡng phân loại 2,5**: tỉ lệ nhỏ hơn ngưỡng được xếp vào nhóm hai dòng.

Ngưỡng này là **đề xuất của đồ án, không phải quy định pháp lý**. Quy chuẩn chỉ cung cấp ba tỉ lệ vật lý 4,727 · 2,000 · 1,357 (mục 2.1.2), để lại khoảng trống rộng giữa 2,000 và 4,727. Giá trị 2,5 được đặt **lệch hẳn về phía nhóm hai dòng** thay vì đặt ở giữa khoảng trống, và lý do là **tính bất đối xứng của chi phí sai sót**: đường xử lý hai dòng **suy giảm êm** khi gặp đầu vào một dòng — nó chỉ tách một ảnh vốn đã một dòng thành hai nửa rồi ghép lại, kết quả gần như không đổi — trong khi chiều ngược lại thì không, một biển hai dòng đi thẳng vào bộ nhận dạng sẽ hỏng theo cơ chế ở mục 2.4.2.

Dải 2,5–3,0 vẫn là **vùng bất định**, và nó bất định theo cả hai chiều: một biển một dòng chụp nghiêng lớn có thể cho tỉ lệ rơi xuống khoảng này, còn một biển hai dòng nghiêng thì có tỉ lệ **vọt lên trên** ngưỡng và đi nhầm sang nhánh một dòng.

Luồng xử lý chính **không có cách nào tự phát hiện** mình vừa phân loại nhầm — nó chỉ đo một con số và so với một ngưỡng. Đây chính là lý do cơ chế thử lại đa tầng ở mục 3.4.6 tồn tại: nó không sửa ngưỡng mà **dùng kết quả đọc sai lệch làm tín hiệu** để hiệu chỉnh góc nghiêng rồi phân loại lại.

### 3.4.4. Tách hai nửa có chồng lấn

Vùng biển được cắt thành hai nửa theo chiều dọc, nhưng **hai nửa cố ý chồng lên nhau**: nửa trên kết thúc tại **5/12** chiều cao, nửa dưới bắt đầu tại **1/3**, tạo vùng chồng lấn bằng **1/12** chiều cao biển.

Căn cứ kỹ thuật của hai phân số 5/12 và 1/3 xuất phát trực tiếp từ các tham số kích thước quy định tại QCVN 08:2024/BCA [5]: trên biển số xe mô tô hai dòng, seri đăng ký ở dòng trên có kích thước chữ cái và chữ số tương đương dòng dưới, nhưng khoảng cách từ mép trên biển đến đỉnh ký tự dòng trên thường nhỏ hơn khoảng cách từ đáy số dòng dưới đến mép dưới biển. Phép cắt nửa trên tại 5/12 chiều cao biển đảm bảo thu trọn toàn bộ thân chữ của seri; trong khi nửa dưới bắt đầu tại 1/3 chiều cao biển đảm bảo ôm trọn cụm số thứ tự ngay cả khi biển số bị dập lệch nhẹ. Khoảng cách giao nhau 1/12 chiều cao đóng vai trò như một vùng đệm an toàn: nó triệt tiêu hoàn toàn rủi ro cắt đứt nét chân của chữ dòng trên hoặc cắt mất phần mũ của số dòng dưới.

Thiết kế xuất phát từ tính bất đối xứng của chi phí sai sót, giống mục 3.4.3 nhưng ở một đại lượng khác. Cắt phạm vào nét đáy ký tự dòng trên hoặc đỉnh của ký tự dòng dưới **phá huỷ thông tin không phục hồi được** — một `8` bị cắt chân thành `9` hoặc `0` là lỗi vĩnh viễn. Ngược lại, để lọt vài hàng điểm ảnh của nửa còn lại chỉ tạo ra một dải nhiễu mà bộ nhận dạng xử lý như nền.

Vùng chồng lấn này về sau hoá ra còn có một tác dụng thứ hai mà thiết kế ban đầu không lường trước, phân tích ở mục 3.4.7.

### 3.4.5. Ghép ngang

Hai nửa được ghép theo chiều ngang bằng phép nối mảng `hstack`, **nửa trên đặt bên trái** để bảo toàn thứ tự đọc. Chiều cao chung lấy bằng giá trị lớn nhất trong ba đại lượng: chiều cao nửa trên, chiều cao nửa dưới, và **48 điểm ảnh** — đúng bằng chiều cao đầu vào cố định của mô-đun nhận dạng.

Chi tiết cuối cùng là điểm mấu chốt của toàn bộ thiết kế. Sau khi ghép, ảnh chỉ còn **một hàng ký tự duy nhất**, và hàng đó nhận **trọn ngân sách 48 điểm ảnh** thay vì hai hàng chia nhau mỗi hàng 24 điểm ảnh. Phép biến đổi này vô hiệu hoá **đồng thời cả hai nguyên nhân** đã phân tích ở mục 2.4.2: giả định căn chỉnh đơn điệu của CTC lại đúng, và độ phân giải mỗi hàng ký tự tăng gấp đôi.

Đây là một minh hoạ trực tiếp cho luận điểm của môn học: bài toán không được giải bằng cách thay mô hình mạnh hơn, mà bằng cách **biến đổi ảnh đầu vào cho khớp giả định của mô hình sẵn có**.

### 3.4.6. Hiệu chỉnh góc nghiêng và cơ chế thử lại đa tầng

Biển chụp nghiêng vừa làm ký tự biến dạng phối cảnh, vừa làm **hộp bao nở rộng theo chiều ngang** khiến tỉ lệ khung hình đo được vượt ngưỡng 2,5 của mục 3.4.3: biển hai dòng bị phân loại nhầm thành một dòng, không được tách và trả về chuỗi rỗng — lỗi **đi nhầm nhánh xử lý**, không phải "đọc kém đi". Hai phép hiệu chỉnh được cài để kéo vùng biển về đúng nhánh:

- **Hiệu chỉnh góc nghiêng (Deskew)** — nhị phân hoá bằng Otsu ở cả hai cực, lấy vùng liên thông lớn nhất, khớp một hình chữ nhật xoay, xoay cho cạnh dài nằm ngang rồi **cắt lại sát**; tỉ lệ của phần cắt sát mới là hình dạng thật của biển — đúng đại lượng mà bước phân loại cần.
- **Giãn theo chiều dọc** — cho biển bị nén do chụp chếch từ trên xuống, khi không có góc xoay nào để nắn; giá trị nằm ở việc **định tuyến lại**, không ở chi tiết ảnh nội suy thêm.

Hai phép này tổ chức thành một **cơ chế thử lại đa tầng (Fallback Ladder)**, chỉ kích hoạt sau khi lượt đọc đầu tiên trượt kiểm tra định dạng. Vì cổng chỉ mở khi kết quả đã không hợp lệ, tập bị can thiệp và tập đang đúng là **hai tập rời nhau** — cơ chế thử lại không thể làm sai lệch một biển vốn đã đọc đúng, nên bật mặc định được. Bước hiệu chỉnh góc nghiêng còn ba cổng an toàn tự lùi về "trả nguyên vùng cắt": góc nghiêng dưới 1,5°, góc trên 35°, hoặc vùng liên thông lớn nhất dưới 25% diện tích vùng cắt.

Chi phí và lợi ích đo được trình bày ở mục 4.4.2, kèm một quyết định **tắt** một bậc trong đó.

Cần nhấn mạnh một đánh đổi có chủ đích trong thiết kế: giải thuật hiệu chỉnh góc nghiêng chỉ áp dụng phép xoay phẳng hai chiều (2D affine rotation) dựa trên việc khớp hình chữ nhật có hướng diện tích tối thiểu (minAreaRect) [16]. Hệ thống chủ động không tích hợp các phép biến đổi phối cảnh ba chiều (3D Homography/Perspective Transformation) phức tạp. Lý do trực tiếp là ràng buộc thời gian thực trên CPU: tính toán ma trận phối cảnh và nội suy lại toàn bộ lưới điểm ảnh trên CPU sẽ đẩy độ trễ p95 vượt trần cho phép, trong khi phép xoay phẳng 2D có chi phí tính toán xấp xỉ 0 ms nhưng vẫn giải quyết được đại đa số các trường hợp biển số bị lệch góc chụp phổ biến trong thực tế.

### 3.4.7. Bước phục hồi dòng trên

Chế độ hỏng quan sát được: chuỗi `29E-015.66` chỉ đọc ra `015.66` — sau khi ghép, bộ phát hiện văn bản của PaddleOCR chỉ khoanh được một vùng chữ và bỏ qua nửa bên trái. Giả thuyết tự nhiên — **bỏ hẳn phép ghép, đọc riêng từng nửa rồi nối chuỗi** — được kiểm bằng thí nghiệm A/B trên 200 biển hai dòng và **bị bác bỏ dứt khoát** (mục 4.4.1): khi đọc riêng, dải chồng lấn của mục 3.4.4 bị nhận dạng **hai lần** và sinh ký tự thừa (`84G122593` → `84-G124E009.01225.93`), trong khi trên dải đã ghép nó nằm giữa hai cụm ký tự và bị loại như một mảnh nhiễu.

Thiết kế cuối cùng vì vậy **giữ nguyên chiến lược ghép** và chỉ bổ sung một bước phục hồi có điều kiện chặt: kích hoạt khi đồng thời (a) vùng biển phân loại hai dòng, (b) chuỗi sau chuẩn hoá không hợp lệ, (c) chuỗi thô khác rỗng — hệ thống đọc thêm một lượt trên **riêng nửa trên**, ghép với chuỗi thô rồi chuẩn hoá lại, và chỉ nhận kết quả vượt kiểm tra định dạng.

## 3.5. Phân loại màu nền trong không gian HSV

Mục 2.1.3 đã chỉ ra giới hạn về nguyên tắc: chuỗi ký tự không phân biệt được biển vàng với biển trắng. Bộ phân loại màu cung cấp **nguồn bằng chứng thứ hai**.

Bộ phân loại chuyển vùng biển sang không gian HSV, thống kê tỉ lệ điểm ảnh theo từng dải sắc độ và chọn dải chiếm ưu thế. Ba quyết định thiết kế đáng lưu ý:

**Chỉ lấy mẫu vùng trung tâm, thu biên vào 18% mỗi phía.** Hộp bao do bộ phát hiện sinh ra hiếm khi ôm sát mép biển, nên rìa hộp thường chứa màu thân xe phía sau. Với biển nhỏ, phần rìa đó đủ để chiếm ưu thế và lật kết quả.

**Không loại trừ điểm ảnh thuộc ký tự.** Ký tự chiếm thiểu số diện tích biển, và việc bổ sung một bước phân đoạn ký tự sẽ đưa vào chuỗi xử lý một khâu **kém ổn định hơn chính khâu nó bảo vệ**.

**Trả kết quả *không xác định* khi dải chiếm ưu thế không đạt 30%.** Một kết luận sai về màu tương đương khẳng định một loại phương tiện không chứng minh được; thừa nhận không xác định được chỉ là ghi nhận một giới hạn.

Kết quả hợp nhất giữa hai nguồn bằng chứng tuân một **ràng buộc an toàn**: màu nền chỉ được phép **nâng cấp một ứng viên mà bộ luật ký tự đã coi là hợp lý**, và nếu phán quyết ban đầu không nằm trong tập ứng viên thì kết quả giữ nguyên. Nói cách khác, màu nền không thể tạo ra một họ biển mà bộ luật ký tự đã bác bỏ (Hình 3.4).

## 3.6. Bộ luật hậu xử lý theo vị trí

![](figures/fig-ch5-03.png)

**Hình 3.4.**[]{#fig-3-4} Thuật toán chuẩn hoá chuỗi biển số theo bộ luật ràng buộc vị trí

Khối này là thành phần do đồ án tự thiết kế hoàn toàn. Nó khai thác ba ràng buộc đặc thù đã trình bày ở mục 2.1.1.

**a) Tập mã tỉnh.** Khối lưu **81 mã đang sử dụng**, song song với tập **8 mã không bao giờ được cấp**. Lưu tường minh cả hai tập cho phép kiểm thử khẳng định chúng phủ đúng dải 11–99.

**b) Mặt nạ vị trí.** Ba mặt nạ tương ứng ba độ dài chuỗi hợp lệ, trong đó `D` bắt buộc chữ số, `L` bắt buộc chữ cái, `?` là ký tự đại diện không áp đặt kiểu:

- chuỗi 8 ký tự (ô tô, seri 5 chữ số): `DDLDDDDD`
- chuỗi 7 ký tự (ô tô, seri 4 chữ số kiểu cũ): `DDLDDDD`
- chuỗi 9 ký tự (xe máy): `DDL?DDDDD`

Ký tự đại diện tại **chỉ số 3** của chuỗi 9 ký tự là chi tiết thiết kế then chốt. Hai kiểu biển xe máy cùng 9 ký tự nhưng khác nhau **đúng tại vị trí này**: kiểu mới dùng seri hai chữ cái, kiểu cũ dùng một chữ cái kết hợp một chữ số và vẫn lưu hành hợp pháp. Tách thành hai mặt nạ riêng sẽ buộc phải áp kiểu tại chỉ số 3, và kết quả thực nghiệm thực tế cho thấy khi đó **một trong hai kiểu bị phá huỷ**. Đây là vị trí duy nhất trong toàn hệ thống biển số Việt Nam mà cả chữ cái lẫn chữ số đều hợp lệ.

**c) Bảng ánh xạ nhầm lẫn và tính bất đối xứng.** Hai bảng riêng biệt được áp tại vị trí bắt buộc chữ số và vị trí bắt buộc chữ cái, và phát hiện trung tâm là **hai bảng bất đối xứng**:

- Chữ cái O $\rightarrow$ số 0 (O $\rightarrow$ 0) tại vị trí chữ số là hợp lý;
- Số 0 $\rightarrow$ chữ cái O (0 $\rightarrow$ O) **không bao giờ** hợp lý, vì chữ O không thuộc tập seri hợp lệ.

Do cả chữ cái O và Q đều bị loại trừ, ứng viên đồng hình duy nhất còn lại tại vị trí chữ cái là D, nên chiều đúng là 0 $\rightarrow$ D. Ký tự R **không được ánh xạ trong mọi trường hợp**, vì nó hợp lệ tại vị trí seri thứ hai của biển xe máy. Nguyên tắc an toàn: ký tự không có mục trong bảng thì giữ nguyên.

Cần nêu rõ một giới hạn: hai bảng này **suy từ lập luận hình dạng ký tự chứ không từ đo đạc**, và một số cặp mang tính phỏng đoán. Mục 4.3.3 đối chiếu chúng với ma trận nhầm lẫn đo được.

**d) Thuật toán.** Ba nguyên tắc: **thử biểu thức chính quy trước khi sửa bất cứ thứ gì**, vì với chuỗi vốn đã hợp lệ thì mọi can thiệp chỉ có thể làm sai đi; **không chuỗi nào bị loại bỏ** — chuỗi không sửa được vẫn trả về kèm cờ không hợp lệ; và **chuỗi thô được giữ song song với chuỗi đã sửa**.

Nguyên tắc thứ ba có hệ quả trực tiếp lên cơ sở dữ liệu: hai cột riêng cho chuỗi thô và chuỗi đã chuẩn hoá cùng tồn tại trong lược đồ. Đây là **điều kiện cần để phép đo ở mục 4.3.2 thực hiện được**, và nó phải có mặt từ giai đoạn thiết kế chứ không thể bổ sung về sau.

## 3.7. Ứng dụng trình diễn

Phần này không phải trọng tâm của môn học nên chỉ nêu những quyết định có liên quan tới khối xử lý ảnh (Hình 3.5).

![](figures/fig-ch4-02.png)

**Hình 3.5.**[]{#fig-3-5} Kiến trúc phân tầng và chiều phụ thuộc

Hệ thống gồm **máy chủ FastAPI** phục vụ mười thao tác HTTP trên chín đường dẫn, **cơ sở dữ liệu SQLite** lưu lịch sử nhận dạng, **giao diện web React** bốn trang (nhận dạng ảnh, nhận dạng video, quét webcam trực tiếp, tra cứu lịch sử), và **đóng gói Docker Compose** khởi động toàn bộ bằng một lệnh.

Ba chi tiết đáng ghi nhận:

**Ảnh không chứa biển số trả mã thành công kèm danh sách rỗng**, không phải mã lỗi. Kết quả nhận dạng vẫn tồn tại và là tập rỗng; trả mã lỗi sẽ loại toàn bộ trường hợp âm khỏi thống kê. Đây là cùng một quyết định đã áp ở tầng suy luận (mục 3.1).

**Giao diện hiển thị đồng thời chuỗi thô và chuỗi đã chuẩn hoá khi hai chuỗi khác nhau.** Điều này biến một cột dữ liệu phục vụ nghiên cứu thành **bằng chứng quan sát được ngay trong lúc trình diễn**: người xem thấy trực tiếp khối hậu xử lý vừa sửa gì.

**Yêu cầu xử lý video trả mã *đã tiếp nhận* thay vì mã thành công**, vì một video 60 giây, với bước lấy mẫu 5 khung hình, cần khoảng một đến ba phút xử lý trên CPU tuỳ độ trễ từng khung, và không client nào chờ được.
