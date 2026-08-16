# Quy Tắc Bảo Toàn Tính Hợp Lệ Của Số Liệu

Hai bộ quy tắc kia nói về **cách trình bày**. Bộ này nói về thứ khác và khó hơn:
làm sao để con số đưa vào quyển **đúng là con số của hệ thống đang giao**.

Sáu quy tắc dưới đây không phải lý thuyết. Mỗi quy tắc là một lần đồ án này đã
công bố sai và phải sửa. Ghi ra để không lặp lần nữa.

---

## 1. Công cụ đo phải đi qua đúng đường mã mà bản giao hàng đi

**Đây là lỗi nghiêm trọng nhất và đã lặp bốn lần.** Công cụ đo được viết riêng,
tự dựng lại các bước xử lý thay vì gọi đúng hàm mà hệ thống thật gọi. Hai bên
trôi xa nhau mà không ai thấy: công cụ vẫn chạy trơn tru, vẫn in ra số đẹp, chỉ
có điều nó đang đo **một hệ thống khác**.

Bốn lần đã xảy ra:

| Lần | Triệu chứng | Hậu quả |
|:--:|---|---|
| 1 | `ocr_accuracy.py` chép lại các bước nên **chưa bao giờ gọi** bậc thang thử-lại | Mọi số A4–A7 công bố trong một tuần mô tả một đường ống **ngắn hơn** bản giao hàng |
| 2 | Ba công cụ dựng `InferenceConfig` trực tiếp thay vì `from_env()` | Hai công tắc sinh ra để bóc tách **không tới được** chính công cụ cần chúng |
| 3 | `benchmark_system.py` · `stress_test.py` mặc định trỏ một checkpoint **đã bị bác bỏ** | Ai chạy lại mà không truyền `--weights` sẽ đo nhầm mô hình, không một cảnh báo |
| 4 | `--detector-imgsz` mặc định `416` trong khi bản giao hàng chạy `640` | Suýt công bố một **hồi quy giả** |

**Quy tắc:**

- Công cụ đo **gọi đúng hàm** của đường ống, không chép lại các bước.
- **Mọi mặc định** của công cụ đo đọc từ cùng nguồn cấu hình với máy chủ thật
  (`InferenceConfig.from_env()`), không gán cứng.
- Đổi một mặc định của công cụ đo là **đổi kết quả**. Phải ghi vào commit.

## 2. Một lần đo có cảnh báo tải cạnh tranh không được thành số liệu công bố

Con số NFR-P2 = 2,379 FPS sống **mười một ngày** trong quyển, dù chính harness
đã in `Competing CPU load present -- every timing below is PESSIMISTIC` ngay
lúc đo, kèm danh sách tiến trình đang chiếm CPU.

Cảnh báo được in ra nhưng không được đọc.

**Quy tắc:** thấy cảnh báo tải cạnh tranh thì **bỏ kết quả và chạy lại trên máy
rảnh**. Không có ngoại lệ "chắc cũng không ảnh hưởng mấy".

## 3. Lật một kết luận thì phải có phép đối chứng, không chỉ một lần đo mới

Khi con số cũ không tái lập được, giả thuyết đầu tiên nghe hợp lý đến mấy cũng
phải **kiểm bằng thí nghiệm**, không được tin.

Đã xảy ra: giả thuyết *"2,379 FPS thấp vì máy đang tải nặng"* nghe rất thuyết
phục. Dựng tải tổng hợp 6 rồi 12 lõi để kiểm — và **thí nghiệm bác bỏ chính giả
thuyết đó**: tải cạnh tranh nâng cả phân bố đều tay (p95/p50 quanh 1,2), còn
lần đo cũ có trung vị gần như máy rảnh nhưng đuôi gấp 6,93 lần. Hai chữ ký khác
hẳn nhau.

Nếu tin ngay lần đo mới, quyển đã ghi sai nguyên nhân.

**Quy tắc:** nguyên nhân **không xác định được** thì ghi đúng là không xác định
được. Đừng chọn lời giải thích nghe xuôi tai nhất.

## 4. So sánh chỉ có nghĩa khi hai vế đi qua cùng một đường đo

Suýt kết luận *"xuất sang OpenVINO làm mất 1,1 điểm mAP"* vì so **0,9718** của
harness riêng với **0,9829** của validator Ultralytics — hai đường đo khác
nhau. Chạy lại chính bản PyTorch qua chính harness riêng cho **0,9712**, tức
OpenVINO thực ra **nhỉnh hơn**.

**Quy tắc:** trước khi so hai con số, kiểm chúng có cùng: đường đo · ngữ liệu ·
cấu hình · phiên bản mã. Thiếu một điều là phép so hỏng.

## 5. Đổi hằng số cũng phải đo lại, và cần một chỉ số bất động làm chứng

Thay hai mục trong bảng ánh xạ nhầm lẫn là thay **hằng số**, nghe như không cần
đo lại. Nhưng phải đo, và điều quan trọng nhất của lượt đo đó **không phải** con
số tăng lên:

> **A5 đứng yên tới bốn chữ số (0,6373).**

A5 đo *trước* hậu xử lý. Nếu nó nhúc nhích thì phép so đã hỏng vì đầu vào khác
nhau. Nó bất động chứng minh toàn bộ chênh lệch quy được cho **đúng hai hằng số
vừa đổi**, không phải cho thứ gì khác.

**Quy tắc:** mỗi lần đo lại, chỉ ra trước **một chỉ số phải đứng yên**. Nó bất
động thì kết quả đáng tin; nó nhúc nhích thì phép đo có biến khác chưa kiểm soát.

## 6. Sửa nguồn xong phải dựng lại rồi mới kiểm

`check_slides.ps1` kiểm **bản dựng PPTX**, không kiểm `.md`. Sau khi kéo về một
commit sửa nội dung slide, lượt kiểm chạy ngay lập tức báo **0 lỗi** — vì nó
đang kiểm bản dựng cũ. Dựng lại từ nguồn mới thì lộ ra **ba lỗi tràn chữ**,
trong đó một slide đè nhau 89 pt.

**Quy tắc:** thứ tự bắt buộc là **sửa → dựng lại → kiểm**. Kiểm trước khi dựng
là kiểm nhầm bản cũ, và tệ hơn không kiểm vì nó cho cảm giác an toàn giả.

---

## Áp dụng: danh sách kiểm trước khi đưa một con số vào quyển

1. Công cụ đo có gọi đúng đường mã của bản giao hàng không?
2. Mọi mặc định của nó có đọc từ cấu hình thật không?
3. Lượt đo có cảnh báo tải cạnh tranh không?
4. Nếu con số này thay thế một con số cũ — đã có phép đối chứng chưa?
5. Nếu là phép so — hai vế có cùng đường đo, ngữ liệu, cấu hình, phiên bản mã?
6. Có chỉ số nào phải đứng yên không, và nó có đứng yên thật không?
7. Đã dựng lại trước khi kiểm chưa?
