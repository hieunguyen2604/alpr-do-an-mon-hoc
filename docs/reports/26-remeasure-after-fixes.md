# Đo lại A4–A7 sau bốn đợt sửa 21–28/07/2026

> ## ⚠ BẢN NÀY ĐÃ BỊ THAY THẾ — đọc [27-retry-ladder-cost-benefit.md](27-retry-ladder-cost-benefit.md)
>
> Giữ lại vì hai lý do, không phải vì còn dùng được.
>
> **Sai ở đâu.** Bản này quy mức tăng A6 (0,6730 → 0,7437) cho cả bốn đợt sửa
> 21–28/07, trong đó có bậc thang thử-lại (21/07) và siêu phân giải (24/07).
> Vài giờ sau khi viết, phát hiện `ai/evaluation/ocr_accuracy.py` **chưa bao
> giờ gọi** `retry_skewed_variants` — cả hai đợt ấy **không nằm trong đường
> đo** lúc đó. Mức tăng thật đến từ các bản sửa đọc biển hai dòng và
> normalizer; bậc thang đóng góp thêm 0,7437 → **0,7512**, và chỉ hiện ra sau
> khi harness được sửa.
>
> **Vì sao vẫn giữ.** Số trong bản này là số đo thật của một cấu hình thật
> (hệ thống **không** chạy bậc thang), nên nó là cột giữa của bảng chi phí–lợi
> ích ở [27](27-retry-ladder-cost-benefit.md) mục 5. Và một quy kết sai đã
> công bố thì sửa công khai, không xoá lặng lẽ.

## 1. Vì sao phải đo lại

Bộ số OCR đang trích trong quyển đồ án sinh ngày **20/07/2026**
([16-ocr-accuracy-rescued.json](16-ocr-accuracy-rescued.json)). Sau mốc đó có
bốn thay đổi nhắm thẳng vào lỗi đọc:

| Ngày | Commit | Nội dung | Báo cáo |
|---|---|---|---|
| 21/07 | `4978a87` | Bậc thang thử-lại cho biển nghiêng/méo | [21](21-skew-retry.md) |
| 24/07 | `8b4f9d3` | Dấu chấm in phân xử ô tô/xe máy | [23](23-display-format-rules.md) |
| 24/07 | `2169cba` | Siêu phân giải cứu crop nhỏ, rescue lai hai nửa | [24](24-sr-retry.md) |
| 28/07 | `d49018c` | Ba lỗi trong bản kéo về (`UnboundLocalError`, đường dẫn cứng, test bám môi trường) | — |

Công bố một con số đo **trước** chính các bản sửa của mình là lỗi phương pháp
luận, không phải chuyện nhỏ về cập nhật tài liệu. Nó khiến người đọc đánh giá
một hệ thống không còn tồn tại.

Lần đo này giữ **nguyên mọi biến khác**: cùng máy (i5-14600K, 20 luồng), cùng
trọng số `models/best.pt`, cùng `--detector-imgsz 640`, cùng bộ nhãn 2.801 mẫu
(567 biển một dòng, 2.234 biển hai dòng). Chỉ mã nguồn suy luận là khác.

## 2. Kết quả

| Chỉ tiêu | Sàn | 20/07 | 28/07 | Chênh (điểm %) | Kết luận |
|---|---|---|---|---|---|
| **A4** — chính xác ký tự (1 − CER) | 0,92 | 0,8848 | **0,9416** | **+5,68** | ❌ → ✅ **đạt ngưỡng tối thiểu** |
| A5 — chuỗi đúng *trước* hậu xử lý | 0,80 | 0,6098 | 0,6373 | +2,75 | ❌ |
| **A6** — chuỗi đúng *sau* hậu xử lý | 0,85 | 0,6730 | **0,7437** | **+7,07** | ❌ (còn cách 10,6 điểm) |
| A7 — đầu-cuối | 0,82 | 0,5295 | 0,5498 | +2,03 | ❌ (xem mục 5) |

**A4 lật trạng thái.** Đây là lần đầu một chỉ tiêu trong nhóm A chuyển từ
"không đạt" sang đạt, và nó xảy ra **không tốn một giây GPU nào** — hoàn toàn
nhờ hình học và bậc thang thử-lại ở tầng suy luận.

Chỉ số phụ cùng hướng:

| | 20/07 | 28/07 |
|---|---|---|
| Tỉ lệ chuỗi đúng quy cách | 0,8429 | **0,9322** |
| Số biển hậu xử lý sửa được | 177 | **298** |
| Đóng góp của hậu xử lý (A6 − A5) | 6,32 điểm | **10,64 điểm** |
| Độ tin cậy OCR trung bình | 0,9576 | **0,9657** |

## 3. Bằng chứng không thoái lui

Tách theo bố cục biển:

| Chỉ số | Biển **một dòng** (n = 567) | Biển **hai dòng** (n = 2.234) |
|---|---|---|
| Chính xác ký tự | 0,9903 → **0,9903** (±0) | 0,8601 → **0,9302** (+7,01) |
| Chuỗi đúng (A6) | 0,9489 → **0,9489** (±0) | 0,6030 → **0,6916** (+8,86) |
| Đúng quy cách | 0,9859 → **0,9859** (±0) | 0,8066 → **0,9185** (+11,19) |
| Đọc rỗng | 0,0018 → **0,0018** (±0) | 0,0045 → **0,0045** (±0) |
| E2E | 0,6843 → **0,6843** (±0) | 0,4902 → **0,5157** (+2,55) |

Biển một dòng **không xê dịch ở bất kỳ chỉ số nào**. Đó không phải may mắn mà
là tính chất thiết kế đã đặt ra từ [báo cáo 21](21-skew-retry.md): bậc thang
thử-lại chỉ chạy **sau khi** lần đọc đầu thất bại, và chỉ nhận chuỗi mới nếu
chuỗi đó **hợp lệ** — nên về mặt cấu trúc nó không thể làm hỏng một kết quả
đang đúng. Bảng trên là kiểm chứng thực nghiệm của tính chất đó trên 2.801 mẫu.

Cùng một ý ở khối hậu xử lý: `postprocessing_broke = 0` ở **cả hai** bố cục —
298 biển được sửa, không biển nào bị phá.

## 4. Phân loại lỗi: một con số tăng lên mà không phải thoái lui

| Loại lỗi | 20/07 | 28/07 | Chênh |
|---|---|---|---|
| Đúng | 1.885 | **2.083** | **+198** |
| Thừa ký tự | 95 | **19** | −76 |
| Thiếu ký tự | 134 | **89** | −45 |
| Hỗn hợp | 277 | **157** | −120 |
| **Thay ký tự** | 399 | **442** | **+43** |
| Đọc rỗng | 11 | 11 | 0 |

Số ca *thay ký tự* **tăng 43**. Đọc thoáng thì tưởng thoái lui, nhưng không:
tổng số đọc đúng tăng 198, và ba loại lỗi cấu trúc (thừa / thiếu / hỗn hợp)
giảm tổng cộng 241 ca. Đây là **hiện tượng phân loại lại**, đúng như dự đoán
của các bản sửa hình học: một biển méo trước kia cho ra chuỗi sai độ dài (rơi
vào *hỗn hợp* hoặc *thiếu ký tự*); sau khi nắn hình và siêu phân giải, nó cho
ra chuỗi **đúng độ dài nhưng sai một ký tự** ⇒ chuyển sang nhóm *thay ký tự*.

Nói cách khác, phần lỗi còn lại đã dịch từ "đọc hỏng cả chuỗi" sang "đọc gần
đúng, sai một ký tự". Đó là loại lỗi mà fine-tune bộ nhận dạng nhắm tới, còn
hình học thì đã hết dư địa.

## 5. A7 và một điều phải nói thẳng khi bảo vệ

| | 20/07 | 28/07 |
|---|---|---|
| Tỉ lệ phát hiện được | 0,8804 | **0,8804** (y hệt) |
| Số ảnh bộ phát hiện bỏ sót | 335 | **335** (y hệt) |
| Đúng **trong số đã phát hiện** | 0,6014 | **0,6245** (+2,31) |

Hai dòng đầu **không đổi một đơn vị nào** vì trọng số phát hiện không đụng
tới. Suy ra toàn bộ mức tăng của A7 đến từ khối nhận dạng — con số +2,31 điểm
ở dòng thứ ba mới là mức cải thiện thật của phép đo E2E, còn +2,03 điểm ở A7
là con số đó bị pha loãng bởi 335 ca bộ phát hiện không bao giờ có cơ hội đọc.

Và bản thân **A7 = 0,5498 không đại diện cho hệ thống thật**. Phép đo đưa
**ảnh biển đã cắt sẵn** vào bộ phát hiện vốn huấn luyện trên ảnh giao thông
toàn cảnh — tức ngoài phân bố huấn luyện của nó. Chính vì thế 335/2.801 ảnh
bị bỏ sót ngay ở bước đầu. Bằng chứng đối chứng: cùng bộ trọng số đó đạt
**mAP@0.5 = 0,9829** trên tập test v3 gồm 1.514 ảnh hiện trường.

Nguyên nhân gốc là **không bộ dữ liệu nào trong đồ án có đồng thời ảnh toàn
cảnh và chuỗi biển số**. Đo A7 đúng cách đòi hỏi gán nhãn chuỗi cho một phân
tách test của `yolo_v2` — việc chưa làm. Cho tới lúc đó, A7 phải được trình
bày đúng bản chất: **cận dưới bi quan**, không phải hiệu năng thực tế.

## 6. Hệ quả cho quyết định fine-tune

Khoảng cách A6 tới sàn thu từ **17,7 điểm xuống 10,6 điểm** mà không cần huấn
luyện. Phần còn lại tập trung ở biển hai dòng (0,6916) và chủ yếu là lỗi thay
một ký tự — đúng mục tiêu của việc fine-tune bộ nhận dạng.

Kết luận: fine-tune **không bắt buộc để hoàn thành đồ án** (xem
[25](25-finetune-attempt-failed.md) về lần thử thất bại và các rào chắn đã
dựng), nhưng là hướng cải thiện duy nhất còn dư địa rõ ràng nếu có GPU. Nếu
làm, phải chạy lại đúng phép đo này để so, và phải đồng bộ lại toàn bộ bảng số
chương 5, poster và tóm tắt.

## 7. Tái lập

```bash
backend/.venv/Scripts/python.exe -m ai.evaluation.ocr_accuracy \
  --labels datasets/annotations/plate_text_labels_vn.csv \
  --detector models/best.pt --detector-imgsz 640 \
  --output docs/reports/26-ocr-accuracy-post-fixes.json
```

Thời gian chạy: **56,2 phút** trên CPU i5-14600K, máy rảnh. Kết quả đầy đủ
kèm ma trận nhầm lẫn và các ca lỗi xuất ra nằm trong
[26-ocr-accuracy-post-fixes.json](26-ocr-accuracy-post-fixes.json); bản
20/07 giữ nguyên tại [16-ocr-accuracy-rescued.json](16-ocr-accuracy-rescued.json)
để đối chiếu.

Bảng chính thức của chương 5 ([05-tables.md](05-tables.md)) và
[05-results.json](05-results.json) được sinh lại bằng
`scripts/fill_chapter5.py` trong cùng ngày, nên số trong quyển lấy từ một
phiên đo nhất quán chứ không ghép từ hai lần chạy.
