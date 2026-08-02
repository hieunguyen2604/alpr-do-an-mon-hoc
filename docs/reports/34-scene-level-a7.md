# NFR-A7 đo trên ảnh toàn cảnh — gỡ nhãn "không đại diện"

**Ngày:** 2026-08-02
**Nhãn:** `datasets/annotations/scene_labels.csv` — **608 khung biển** (tầng đồng thuận đếm hết)
**Nguồn ảnh:** `datasets/processed/yolo_v3/images/test` — 1.514 ảnh toàn cảnh, 1.606 khung biển

---

## 1. Vấn đề mà báo cáo này giải quyết

Con số NFR-A7 công bố trước đây (**0,5552**) mang nhãn **"KHÔNG ĐẠI DIỆN"**, và
nhãn đó là đúng: phép đo đưa **ảnh biển đã cắt sẵn** vào bộ phát hiện vốn được
huấn luyện trên ảnh giao thông đầy đủ. Một tấm ảnh mà biển chiếm gần hết khung là
**ngoài phân bố** của bộ phát hiện, nên 335/2.801 ca hỏng ngay ở bước phát hiện —
không phải vì OCR đọc sai.

Cùng lỗ hổng dữ liệu ấy còn chặn một câu hỏi thứ hai: có nên bỏ bước phát hiện chữ
của PaddleOCR hay không ([31](31-detection-stage-ablation.md)). Cả hai đều cần một
thứ mà đồ án không có: **ảnh toàn cảnh có nhãn chuỗi biển số**.

## 2. Cách lấy nhãn, và vì sao nó không phải lập luận vòng tròn

Lấy **đồng thuận của chính các cấu hình đang so sánh** làm nhãn là sai về nguyên
tắc: mọi cấu hình sẽ tự động đúng trên mọi mẫu đồng thuận, kể cả khi tất cả cùng
đọc sai, và phép đo mất hết sức phân định. Nhãn ở đây được đọc **độc lập với cả
bốn cấu hình**, nên dùng làm mốc được.

**Hạn chế phải nói kèm:** nhãn do một mô hình ngôn ngữ-thị giác đọc, không phải do
người. Nó độc lập với PaddleOCR nên không vòng tròn, nhưng vẫn có thể sai theo
những cách riêng của nó. 64 khung đọc được một phần mà không chắc từng ký tự được
**để trống** thay vì đoán — một nhãn sai hại hơn một nhãn thiếu.

## 3. Lấy mẫu phân tầng, và vì sao bắt buộc phải phân tầng

Trong 1.606 khung, **1.232 (76,7%) là bất đồng** — tức tập bất đồng gồm hầu hết
các ca khó. Dùng riêng nó để công bố độ chính xác tuyệt đối sẽ ra con số **bi quan
sai lệch**. Vì vậy gán nhãn cả hai tầng rồi ước lượng:

$$A7 = \frac{p_{\text{đồng thuận}} \times 374 + p_{\text{bất đồng}} \times 1.232}{1.606}$$

| Tầng | Kích thước | Đã gán nhãn | Tỷ lệ |
|---|---:|---:|---:|
| Đồng thuận | 374 | **372** | **99,5%** |
| Bất đồng | 1.232 | 236 | 19,2% |
| **Tổng** | **1.606** | **608** | 37,9% |

Tầng đồng thuận gần như **đã đếm hết** chứ không còn là mẫu, nên sai số của ước
lượng chỉ còn đến từ tầng bất đồng.

## 4. Kết quả

<!-- {{T34}} NFR-A7 do tren anh toan canh, uoc luong phan tang -->

| Cấu hình | Tầng đồng thuận<br>*(n = 372)* | Tầng bất đồng<br>*(n = 236)* | **A7 phân tầng** | KTC 95% |
|---|---:|---:|---:|:---:|
| **Gốc + det+rec** — *bản giao hàng* | 96,8% | 44,1% | **56,3%** | [52,0 ; 60,7] |
| Gốc + chỉ rec | 96,8% | 19,9% | 37,8% | [34,3 ; 41,3] |
| Fine-tune + det+rec | 96,8% | 30,9% | 46,3% | [42,2 ; 50,3] |
| Fine-tune + chỉ rec | **94,1%** | 44,5% | 56,0% | [51,7 ; 60,4] |

Khoảng tin cậy tính theo công thức phân tầng có hệ số hiệu chỉnh quần thể hữu hạn;
tầng đồng thuận đóng góp gần như bằng không vào phương sai vì đã đếm hết.

**Bản giao hàng thắng**, nhưng phải nói cho đúng mức: khoảng cách với ứng viên gần
nhất là **0,3 điểm** và hai khoảng tin cậy **chồng lên nhau gần như hoàn toàn**.
Về mặt thống kê, `gốc + det+rec` và `fine-tune + chỉ rec` **không phân biệt được**
trên tập này. Hai cấu hình còn lại thì thua rõ, nằm ngoài khoảng tin cậy.

Kết luận vì vậy **không phải** "bản giao hàng chính xác hơn", mà là: **không có
bằng chứng để đổi**, và cái giá của việc đổi thì đã đo được ở mục 4.1.

**Một chi tiết lộ ra ở cột đầu:** fine-tune + chỉ rec là cấu hình duy nhất **kém
đi ở tầng dễ** — 94,1% so với 96,8% của ba cấu hình còn lại. Trên 372 khung đã
đếm hết, đó là **10 biển đọc hỏng thêm** ở đúng nhóm mà mọi cấu hình khác đều
đọc được. Nó thắng ở ca khó nhưng đánh mất ca dễ, và đây là lý do lợi thế 12,46
điểm đo trên ngữ liệu ảnh cắt sẵn không sống sót ở đường chạy thật.

### 4.1. Hành vi im lặng — khác biệt lớn nhất, và không nằm ở độ chính xác

Trong 608 khung có **27 khung mà người đọc cũng không đọc nổi**: biển mờ, bị che,
hoặc bộ phát hiện bắt nhầm vào thứ không phải biển số — biển báo *"CẤM XE 2 VÀ 3
BÁNH"*, biển Thái Lan, biển Mỹ, biển trang trí *"RDHE4D"*, và một dấu thời gian
của camera.

| | Trả chuỗi rỗng đúng lúc |
|---|---:|
| Gốc + det+rec · Fine-tune + det+rec | **75%** |
| Gốc + chỉ rec · Fine-tune + chỉ rec | **0%** |

Hai cấu hình chỉ-rec **bịa ra một biển số ở mọi khung, không sót một lần nào**.
Với hệ thống ghi vào cơ sở dữ liệu thì bịa nguy hiểm hơn im lặng, và đây là lý do
độc lập với độ chính xác để giữ bước phát hiện chữ.

## 5. Con số cũ 0,5552 có sai không?

**Không, nhưng nó đúng một cách tình cờ.** Phép đo cũ (0,5552 trên 2.801 ảnh cắt
sẵn) và phép đo mới (56,3% trên 1.606 khung từ ảnh toàn cảnh) cho hai con số gần
nhau, nhưng chúng đo **hai thứ khác nhau trên hai ngữ liệu khác nhau**. Sự trùng
hợp không biến phép đo cũ thành đại diện — nó chỉ có nghĩa là hai nguồn sai lệch
khác nhau tình cờ triệt tiêu nhau.

Bài học giữ nguyên: **nhãn "không đại diện" là đúng khi nó được dán**, và cách duy
nhất để gỡ là đo lại trên đúng loại đầu vào.

## 6. Phát hiện ngoài dự kiến — tập này CÓ biển hiếm

Ngữ liệu nhãn ký tự 2.801 mẫu có **0 biển đỏ và 0 biển ngoại giao**. Trong 608
khung đã gán nhãn ở đây có:

| Loại | Biển |
|---|---|
| Đỏ (quân đội) | `PK-53-46` (×2) · `QC 10-21` · `VT 1A-16` |
| Xanh (nhà nước) | `80A-068.89` |
| Ngoại giao | `41-291-NG-01` |
| Sê-ri LD (liên doanh) | `93LD-001.03` |

Đây là **nguồn biển hiếm đầu tiên của đồ án có nhãn chuỗi**. Số lượng quá nhỏ để
công bố độ chính xác theo loại biển, nhưng đủ để bỏ mệnh đề *"không bộ dữ liệu nào
của đồ án chứa biển đỏ"* — mệnh đề đó chỉ còn đúng cho **ngữ liệu ảnh cắt sẵn**.

## 7. Việc còn lại

- [x] Gán nhãn hết tầng đồng thuận — 372/374, khoảng tin cậy nay chỉ còn phụ
      thuộc tầng bất đồng
- [x] Cập nhật ch5 mục 5.6.5, bảng T5.9 và đặc tả NFR: gỡ nhãn "không đại diện"
- [ ] Người thực hiện rà 608 nhãn, nhất là 64 khung để trống ở tầng bất đồng
- [ ] Gán thêm tầng bất đồng (còn 996/1.232) nếu muốn thu khoảng tin cậy từ
      ±4,4 điểm xuống dưới ±2 — nhưng với mục đích hiện tại (quyết định có đổi
      cấu hình hay không) thì độ chính xác này đã đủ, vì kết luận là "không phân
      biệt được", và thêm mẫu chỉ làm kết luận đó chắc hơn chứ không đổi nó
