# NFR-A7 đo trên ảnh toàn cảnh — gỡ nhãn "không đại diện"

**Ngày:** 2026-08-02
**Nhãn:** `datasets/annotations/scene_labels.csv` — 385 khung biển
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

| Tầng | Kích thước | Đã gán nhãn |
|---|---:|---:|
| Đồng thuận | 374 | 149 |
| Bất đồng | 1.232 | 236 |
| **Tổng** | **1.606** | **385** |

## 4. Kết quả

<!-- {{T34}} NFR-A7 do tren anh toan canh, uoc luong phan tang -->

| Cấu hình | Tầng đồng thuận | Tầng bất đồng | **A7 phân tầng** |
|---|---:|---:|---:|
| **Gốc + det+rec** — *bản giao hàng* | 97,3% | 44,1% | **56,5%** |
| Gốc + chỉ rec | 97,3% | 19,9% | 37,9% |
| Fine-tune + det+rec | 97,3% | 30,9% | 46,4% |
| Fine-tune + chỉ rec | **93,3%** | 44,5% | 55,9% |

**Bản giao hàng thắng**, và khoảng cách với ứng viên gần nhất là 0,6 điểm.

**Một chi tiết mới lộ ra ở cột đầu:** fine-tune + chỉ rec là cấu hình duy nhất
**kém đi ở tầng dễ** — 93,3% so với 97,3% của ba cấu hình còn lại. Nó thắng ở ca
khó nhưng đánh mất ca dễ, và trên một tập thật thì ca dễ chiếm phần lớn.

### 4.1. Hành vi im lặng — khác biệt lớn nhất, và không nằm ở độ chính xác

Trong 385 khung có **22 khung mà người đọc cũng không đọc nổi**: biển mờ, bị che,
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
sẵn) và phép đo mới (56,5% trên 1.606 khung từ ảnh toàn cảnh) cho hai con số gần
nhau, nhưng chúng đo **hai thứ khác nhau trên hai ngữ liệu khác nhau**. Sự trùng
hợp không biến phép đo cũ thành đại diện — nó chỉ có nghĩa là hai nguồn sai lệch
khác nhau tình cờ triệt tiêu nhau.

Bài học giữ nguyên: **nhãn "không đại diện" là đúng khi nó được dán**, và cách duy
nhất để gỡ là đo lại trên đúng loại đầu vào.

## 6. Phát hiện ngoài dự kiến — tập này CÓ biển hiếm

Ngữ liệu nhãn ký tự 2.801 mẫu có **0 biển đỏ và 0 biển ngoại giao**. Trong 385
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

- [ ] Người thực hiện rà 64 khung để trống và 385 nhãn đã có
- [ ] Cập nhật ch5 mục 5.6.5 và bảng T5.9: gỡ nhãn "không đại diện" của NFR-A7
- [ ] Gán nhãn thêm tầng đồng thuận (còn 225/374 chưa gán) để thu hẹp khoảng tin cậy
