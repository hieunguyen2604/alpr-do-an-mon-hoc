# Thay bảng ánh xạ nhầm lẫn bằng bảng trích từ ma trận đo được

**Ngày đo:** 2026-08-14 · **Ngữ liệu:** 2.801 biển có nhãn chuỗi (567 một dòng, 2.234 hai dòng)
**Số liệu thô:** [40-ocr-accuracy-measured-confusion.json](40-ocr-accuracy-measured-confusion.json) · nền so sánh [27-ocr-accuracy-with-ladder.json](27-ocr-accuracy-with-ladder.json)

---

## 1. Khoản nợ được trả

Bảng `TO_DIGIT` / `TO_LETTER` trong `ai/inference/plate_rules.py` mang sẵn một
lời hứa viết ngay trong docstring:

> *"Phase 7 thay bảng này bằng bảng trích từ ma trận nhầm lẫn 36×36 đo được, chỉ
> giữ những cặp vượt ngưỡng thống kê."*

Ma trận đó **đã có sẵn** trong `27-ocr-accuracy-with-ladder.json` từ 28/07,
nhưng chưa ai dùng nó để sửa bảng.

## 2. Ngưỡng, và vì sao phải có ngưỡng

Lấy argmax của ma trận sẽ cho **23 mục** `TO_DIGIT` — nhưng phần lớn dựa trên
**1–3 lần xuất hiện**. Đó là nhiễu, không phải tín hiệu. Ngưỡng áp dụng:

> Chỉ đổi một mục khi ứng viên đo được xuất hiện **≥ 10 lần** _và_ **≥ 2 lần**
> ứng viên đứng nhì. Mỏng hơn thì giữ nguyên phỏng đoán theo hình dạng.

<!-- {{T41}} doi chieu bang suy tu hinh dang voi bang do duoc -->

| Đọc ra | Ở vị trí | Bảng cũ | Đo được | Bằng chứng | Quyết định |
|---|---|:--:|:--:|---|---|
| `L` | số | `1` | **`4`** | 4:53 · 1:1 | **Đổi** |
| `7` | chữ | `T` | **`Z`** | Z:32 · T:0 | **Đổi** |
| `1` | chữ | `L` | `L` | L:90 · U:38 | Xác nhận |
| `0` | chữ | `D` | `D` | D:34 · U:5 | Xác nhận |
| `8` | chữ | `B` | `B` | B:19 · E:1 | Xác nhận |
| `4` | chữ | `A` | `A` | A:12 · H:3 | Xác nhận |
| `5` | chữ | `S` | F:9 · S:6 | winner 9 < 10, tỉ lệ 1,5× | Giữ — quá mỏng |
| `O` · `C` · `U` · `S` · `R` | số | — | 3–8 lần | dưới ngưỡng | Giữ |

**Mục `L` đáng kể nhất.** Trực giác hình dạng ghép đúng *cặp* nhưng **sai
chiều**: khi một vị trí bắt buộc là số mà bộ nhận dạng đọc ra `L`, sự thật là
`4` **53 lần** và là `1` **đúng một lần**. Bảng cũ đang sửa ngược.

## 3. Kết quả — đo lại toàn bộ 2.801 biển

<!-- {{T41b}} anh huong cua bang do duoc len A4-A6 -->

| Chỉ số | Trước | Sau | Chênh |
|---|---:|---:|---:|
| **A4** — đúng mức ký tự | 0,9454 | **0,9483** | **+0,29 điểm** |
| **A5** — đúng cả chuỗi, *trước* hậu xử lý | 0,6373 | 0,6373 | **0,0000** |
| **A6** — đúng cả chuỗi, *sau* hậu xử lý | 0,7512 | **0,7701** | **+1,89 điểm** |
| Biển **hai dòng** | 0,6996 | **0,7234** | **+2,38 điểm** |
| Biển một dòng | 0,9541 | 0,9541 | 0,0000 |
| Hậu xử lý **sửa đúng** | 319 biển | **372 biển** | **+53** |
| Hậu xử lý **làm hỏng** | **0** | **0** | **0** |
| Đóng góp hậu xử lý | +11,39 điểm | **+13,28 điểm** | +1,89 |

**A5 đứng yên tới bốn chữ số là kiểm chứng quan trọng nhất của bảng này.** A5 đo
*trước* hậu xử lý; nếu nó nhúc nhích thì phép so sánh đã hỏng vì đầu vào khác
nhau. Nó bất động ⇒ bộ nhận dạng nhận đúng cùng ảnh, cùng chuỗi thô, và toàn bộ
chênh lệch quy được cho **hai hằng số vừa đổi**.

Hai mục đổi mua **53 biển đọc đúng, làm hỏng 0 biển** — toàn bộ nằm ở biển hai
dòng, đúng điểm nghẽn của đồ án.

---

## 4. Một hồi quy giả suýt được công bố

Lượt chạy đầu cho **A7 = 0,2588** so với 0,5552 — thoạt nhìn là sụp đổ. Nhưng
bảng ánh xạ ký tự **không thể** chạm tới bộ phát hiện, mà `detection_rate` lại
rơi 0,8804 → 0,6109. Truy ra: `--detector-imgsz` **mặc định 416** trong khi mô
hình huấn luyện ở 640 và bản giao hàng chạy 640.

Đây là **lỗi thứ ba cùng họ** phát hiện trong ngày — *công cụ đo không khớp bản
giao hàng*, sau `benchmark_system.py` và `stress_test.py` cùng trỏ vào một
checkpoint đã bị bác bỏ. Đã sửa: mặc định nay đọc `InferenceConfig.from_env()`.

## 5. Nhưng A7 vẫn không tái lập được, và đó là kết luận về *phép đo*

Chạy lại ở đúng 640 cho **A7 = 0,0000**, `detection_rate` 0,3592 — *tệ hơn* cả
lượt 416. Không phải hệ thống hỏng:

**Đường ống giao hàng chạy trên ảnh toàn cảnh thật đạt 17/22 biển** — đúng con
số quyển công bố. Mọi ảnh một biển đều đọc đúng, gồm cả biển đỏ quân đội, hai
biển ngoại giao, biển vàng kinh doanh và hai biển xanh nhà nước.

Vấn đề nằm ở **thiết kế của nhánh e2e**: nó nạp ảnh **vuông 640×640 đã bóp méo
tỷ lệ** vào một bộ phát hiện huấn luyện trên ảnh giao thông toàn cảnh. Chính
harness đã dán nhãn `KHÔNG ĐẠI DIỆN` cho con số này từ trước. Trên đầu vào ngoài
phân bố, một thay đổi nhỏ ở tầng suy luận đủ để lật hoàn toàn kết quả — và giữa
28/07 với 14/08 tầng đó **có** thay đổi (`upper_char_count`, chặn chế độ chỉ-rec).

**Kết luận: con số A7 = 0,5552 công bố ngày 28/07 không tái lập được bằng mã hôm
nay, và cách đọc đúng không phải "hệ thống tệ đi" mà là "phép đo này không đo cái
nó tưởng đang đo".** Số liệu đại diện cho năng lực đầu-cuối là **17/22 trên ảnh
toàn cảnh**; muốn có A7 đúng nghĩa thì phải gán nhãn chuỗi cho một phân bố test
ảnh hiện trường — hướng phát triển số 3, mục 6.3.

---

## 6. Cách chạy lại

```bash
python -m ai.evaluation.ocr_accuracy --output docs/reports/40-ocr-accuracy-measured-confusion.json
```

`--detector-imgsz` nay mặc định lấy từ `InferenceConfig.from_env()`. **Đừng
truyền tay giá trị khác trừ khi đang cố ý đo một cấu hình khác bản giao hàng** —
và nếu có thì phải ghi rõ trong báo cáo, vì đó chính là cái bẫy mục 4 mô tả.
