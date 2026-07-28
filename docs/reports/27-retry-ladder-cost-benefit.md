# Bậc thang thử-lại: giá thật, lợi ích thật, và một phép đo đã đo nhầm pipeline (2026-07-28)

> Báo cáo này **thay thế** [26-remeasure-after-fixes.md](26-remeasure-after-fixes.md).
> Bản 26 đúng về số đo nhưng **sai về quy kết nguyên nhân** — lý do vì sao được
> giải thích ở mục 3, và bản thân sai lầm đó là một phần kết quả.

## 1. Xuất phát: một câu hỏi tưởng đơn giản

Câu hỏi ban đầu chỉ là "có cần fine-tune bộ nhận dạng không". Để trả lời cần
biết hệ thống đang đứng ở đâu, mà bộ số OCR trong quyển thì đo ngày 20/07 —
trước bốn đợt sửa. Nên phải đo lại. Việc đo lại kéo ra ba tầng vấn đề, mỗi
tầng chỉ lộ ra khi kiểm chứng tầng trước.

## 2. Tầng 1 — số liệu cũ đã lạc hậu

| Chỉ tiêu | Sàn | 20/07 | 28/07 | Kết luận |
|---|---|---|---|---|
| **A4** — chính xác ký tự (1 − CER) | 0,92 | 0,8848 | **0,9454** | ❌ → ✅ đạt ngưỡng |
| A5 — chuỗi đúng *trước* hậu xử lý | 0,80 | 0,6098 | 0,6373 | ❌ |
| **A6** — chuỗi đúng *sau* hậu xử lý | 0,85 | 0,6730 | **0,7512** | ❌ (còn 9,9 điểm) |
| A7 — đầu-cuối | 0,82 | 0,5295 | 0,5552 | ❌ (xem mục 6) |

Tách theo bố cục, biển một dòng **không xê dịch ở bất kỳ chỉ số nào**
(0,9489 → 0,9489), toàn bộ mức tăng nằm ở biển hai dòng (0,6030 → ~0,70).
Đó là kiểm chứng cho hợp đồng chống thoái lui: mọi bậc cứu chữa chỉ chạy
**sau khi** đọc hỏng và chỉ nhận chuỗi mới nếu chuỗi đó **hợp lệ**.

## 3. Tầng 2 — công tắc bóc tách không tới được công cụ đo nào

Để quy đóng góp cho từng thay đổi, phải tắt được từng bậc. Lượt bóc tách đầu
tiên cho ba cấu hình chênh nhau **đúng bằng nhiễu**, suýt dẫn tới kết luận
"bậc thang không tốn gì".

Nguyên nhân: `ai/evaluation/benchmark_system.py` dựng
`InferenceConfig(model_path=..., device=...)` **trực tiếp**, không qua
`from_env()`. Mọi trường còn lại bị ghim về mặc định, nên
`ALPR_RECTIFY_ENABLED` và `ALPR_SR_RETRY_ENABLED` **bị bỏ qua hoàn toàn** —
ba lượt đó là ba lần chạy y hệt nhau. Cùng lỗi ở `ocr_accuracy.py` và
`benchmark_ocr.py`.

Trớ trêu: tài liệu của chính hai công tắc ấy viết *"switch tồn tại để Phase 7
bóc tách và quy đóng góp"* — mà Phase 7 dùng đúng ba module này. Công tắc
được tạo ra cho một mục đích rồi không nối vào đúng chỗ ấy.

**Đã sửa** cả ba module (`from_env()` rồi mới ghi đè phần thuộc về công cụ),
và ghi trạng thái công tắc vào tệp kết quả để không bảng số nào còn mồ côi
cấu hình sinh ra nó.

## 4. Tầng 3 — phép đo chạy trên một pipeline ngắn hơn bản giao hàng

Sau khi sửa, phép đo đóng góp *độ chính xác* của siêu phân giải cho ra
**0,0000 ở mọi chỉ số, cùng đúng 2.083 biển đúng**. Con số quá tròn để tin.

Truy ra: `ocr_accuracy.py` **chưa bao giờ gọi** `retry_skewed_variants`. Cả
nhánh crop lẫn nhánh E2E đều tự chép lại các bước của pipeline —
`recognize` → `normalize_detailed` → `rescue_two_line_upper` — và dừng ở đó.
Nghĩa là **A4/A5/A6/A7 xưa nay mô tả một hệ thống ngắn hơn bản người dùng
chạy**.

Đây không phải sơ suất ngẫu nhiên mà là hệ quả cấu trúc: **harness đo dựng
lại đường xử lý thay vì gọi nó**, nên mỗi bậc mới thêm vào pipeline đều mặc
định rơi ra ngoài phép đo. Bằng chứng: chú thích ngay trong mã ghi rằng
**đúng kiểu trôi này từng xảy ra** với bước rescue, và người viết lúc đó đã
nối rescue vào — nhưng bậc thang thêm sau (21/07) thì không ai nối.

**Đã sửa**: nối bậc thang vào cả hai nhánh, đúng vị trí và đúng điều kiện như
`ALPRPipeline._process_one`, kèm phân loại màu để cổng chặn biển quân đội
hoạt động y như sản xuất. Thêm trường `retried_skewed` và khối
`recovery_contribution` để mỗi bậc có số biển cứu được của riêng nó.

## 5. Giá và lợi ích, đo trên cùng dữ liệu

Độ chính xác trên 2.801 mẫu; độ trễ trên 100 ảnh hiện trường của test v3,
máy rảnh:

| Cấu hình | A4 | A6 | Biển cứu được | p95 | p99 |
|---|---|---|---|---|---|
| Tắt hẳn bậc thang | 0,9416 | 0,7437 | 0 | **866 ms** | 1.101 ms |
| Nắn hình / giãn dọc | **0,9454** | **0,7512** | **34** | 1.110 ms | 1.349 ms |
| Thêm siêu phân giải | 0,9454 | 0,7512 | 34 | **1.429 ms** | **2.730 ms** |

Đọc bảng này theo hai chiều:

- **Nắn hình / giãn dọc**: mua 34 biển (+0,75 điểm A6, +0,38 điểm A4) với giá
  +244 ms p95. Giữ.
- **Siêu phân giải**: mua **0** với giá **+319 ms p95 và +1.381 ms p99**, và
  một mình nó đẩy NFR-P1 vượt sàn 1.500 ms. Tắt mặc định.

Bậc thang gần như miễn phí ở trường hợp thường (p50 +3,7%) và rất đắt ở đuôi
(p99 +148%) — đúng bản chất của một cơ chế chỉ chạy khi đọc hỏng.

### 5.1 Số 0 của siêu phân giải là số 0 *cấu trúc*, không phải bằng chứng vô dụng

Phải nói rõ điều này, nếu không bảng trên bị đọc sai. Cổng SR chỉ mở cho crop
có cạnh dài ≤ `RETRY_SR_MAX_SIDE` = 200 px. Đo trên 120 mẫu lấy ngẫu nhiên
của ngữ liệu, cạnh dài sau nắn tỉ lệ: **nhỏ nhất 565 px, trung vị 868 px** —
**0/120 ảnh lọt cổng**. Ngữ liệu này **không thể kích hoạt** bậc SR, nên nó
không thể đo được bậc SR.

Suy ra hai điều. Một, cả 34 biển bậc thang cứu được đều là công của nắn
hình/giãn dọc. Hai, quyết định tắt SR **không** dựa trên "đã đo và thấy vô
dụng" mà trên: *chi phí đã đo được và lớn, lợi ích chưa ai đo được trên bất
kỳ tập đại diện nào, trong khi NFR-P1 là yêu cầu mức Must*. Bằng chứng duy
nhất cho SR vẫn là **1 ca demo tự chọn trong 4 ca thử** ([báo cáo 24](24-sr-retry.md)).

Đo SR cho tử tế đòi một tập **crop nhỏ do bộ phát hiện sinh ra, có nhãn
chuỗi** — đồ án không có. Đó là việc bỏ ngỏ, đã ghi rõ, không phải việc lờ đi.

Mã, test, công tắc và báo cáo của SR **giữ nguyên**; bật lại bằng
`ALPR_SR_RETRY_ENABLED=true`.

## 6. A7 và điều phải nói thẳng khi bảo vệ

`missed_by_detector` = 335/2.801 và `detection_rate` = 0,8804 **không đổi**
giữa các lượt, vì trọng số phát hiện không đụng tới. Mức cải thiện thật của
nhánh E2E nằm ở `exact_given_detected` (0,6014 → 0,6245), còn con số A7 là
mức đó bị pha loãng bởi 335 ca bộ phát hiện không bao giờ có cơ hội đọc.

Và **A7 không đại diện cho hệ thống thật**: phép đo đưa ảnh biển **đã cắt
sẵn** vào bộ phát hiện vốn huấn luyện trên ảnh giao thông toàn cảnh — ngoài
phân bố huấn luyện của nó. Cùng bộ trọng số đó đạt **mAP@0.5 = 0,9829** trên
1.514 ảnh hiện trường. Nguyên nhân gốc: không bộ dữ liệu nào trong đồ án có
đồng thời ảnh toàn cảnh **và** chuỗi biển số. A7 phải được trình bày đúng bản
chất — **cận dưới bi quan**.

## 7. Vì sao bản 26 quy kết sai

Bản 26 gán mức tăng A6 cho cả bốn đợt sửa 21–28/07, trong đó có bậc thang
(21/07) và SR (24/07). Sai: lúc đo, **cả hai đều không nằm trong đường đo**.
Mức tăng 0,6730 → 0,7437 đến từ các bản sửa đọc biển hai dòng và normalizer;
bậc thang đóng góp thêm 0,7437 → 0,7512 và chỉ hiện ra **sau khi** harness
được sửa ở mục 4.

Bài học cùng họ với [21](21-skew-retry.md), [22](22-rescue-confidence-floor.md)
và [25](25-finetune-attempt-failed.md), nhưng ở tầng phép đo:

> **Một con số quá tròn là một giả thuyết cần kiểm chứng, không phải một kết
> quả.** Ba lượt bóc tách chênh nhau đúng bằng nhiễu, rồi một mức chênh
> 0,0000 trên bốn chữ số thập phân — cả hai lần, con số "đẹp" đều là dấu hiệu
> phép đo không chạm tới thứ nó tưởng đang đo.

## 8. Tái lập

```bash
# Do chinh xac (A4-A7), toan bo 2801 mau
backend/.venv/Scripts/python.exe -m ai.evaluation.ocr_accuracy \
  --labels datasets/annotations/plate_text_labels_vn.csv \
  --detector models/best.pt --detector-imgsz 640 \
  --output docs/reports/27-ocr-accuracy-with-ladder.json

# Do do tre, tung bac mot
backend/.venv/Scripts/python.exe -m ai.evaluation.benchmark_system \
  --weights models/best.pt --images datasets/processed/yolo_v3/images/test \
  --limit 100 --imgsz 640 --skip-onnx
ALPR_SR_RETRY_ENABLED=false  ... # bac giua
ALPR_SR_RETRY_ENABLED=false ALPR_RECTIFY_ENABLED=false ... # tat han
```

Kết quả đầy đủ: [27-ocr-accuracy-with-ladder.json](27-ocr-accuracy-with-ladder.json).
Bản 20/07 giữ tại [16-ocr-accuracy-rescued.json](16-ocr-accuracy-rescued.json),
bản trung gian (harness còn thiếu bậc thang) tại
[26-ocr-accuracy-post-fixes.json](26-ocr-accuracy-post-fixes.json) — giữ cả ba
để chênh lệch ở mục 5 và mục 7 kiểm chứng lại được.

## 9. Việc bỏ ngỏ

1. **Đo siêu phân giải cho tử tế** — cần tập crop nhỏ do bộ phát hiện sinh,
   có nhãn chuỗi. Chưa có.
2. **Gọi thẳng `ALPRPipeline.process` trong harness E2E** thay vì chép lại
   các bước, để lỗi trôi ở mục 4 không thể tái diễn. Bản sửa hiện tại nối
   đúng bậc còn thiếu nhưng **không** trị được nguyên nhân gốc.
3. **Fine-tune bộ nhận dạng** — vẫn là hướng còn dư địa rõ nhất cho biển hai
   dòng, không bắt buộc để hoàn thành đồ án ([25](25-finetune-attempt-failed.md)).
