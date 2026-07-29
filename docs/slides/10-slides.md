---
title: "Xây dựng hệ thống nhận dạng biển số xe bằng Trí tuệ nhân tạo"
subtitle: "Đồ án tốt nghiệp đại học · Trường Đại học Công nghệ Thông tin, ĐHQG-HCM"
author:
  - "Phạm Công Thành — 25410013 · Nguyễn Minh Hiếu — 25410007"
  - "GVHD: ThS. Cáp Phạm Đình Thăng"
date: "Tháng 9 năm 2026"
---

<!--
BỘ SLIDE TRÌNH CHIẾU — cố ý ngắn.

Đây là thứ CHIẾU LÊN MÀN HÌNH. Lời nói, số liệu chi tiết, bảng đầy đủ và kịch
bản trả lời phản biện nằm ở `10-slides-outline.md` và `10-defense-qa.md`.
Không chuyển nội dung từ hai file đó sang đây: một slide đọc được trong 5 giây
thì hội đồng nghe người nói; một slide đầy chữ thì hội đồng đọc slide.

HAI QUY ƯỚC BẮT BUỘC KHI SỬA FILE NÀY

1. **Chỉ dùng `##`.** Mỗi `##` là một slide. Cấp này ghim bằng
   `--slide-level=2` trong `scripts/build_thesis.py`, không suy ra từ nội dung.

   Bộ này từng có 7 slide phân đoạn (`#`) cho 7 nhóm chủ đề. Đã bỏ: trong một
   bài 15 phút chúng chiếm 7 slide mà không truyền tải gì, và người nghe vốn
   đã biết đang ở đâu nhờ slide NỘI DUNG ở đầu. Đừng thêm lại.

2. **Bảng hoặc hình phải là khối CUỐI CÙNG của slide, và chỉ được có MỘT.**
   Pandoc cắt sang slide mới ở mọi thứ đứng sau một bảng hoặc một hình, và một
   slide chỉ có một ô nội dung — đặt cả bảng lẫn hình thì cái thứ hai rơi sang
   slide mới. Mọi câu dẫn và mọi kết luận phải nằm TRÊN khối đó.

3. Hình sinh bằng `scripts/make_slide_figures.py`, dựng từ chính mã suy luận
   và ảnh demo của dự án — để một tấm hình không thể mô tả thứ hệ thống không
   làm. Biểu đồ đo đạc thì lấy thẳng từ `docs/reports/figures/`.

Mọi con số lấy từ lượt đo 28/07/2026 (`docs/reports/05-results.json`).
-->

## NỘI DUNG

1. **Tổng quan đề tài**
2. **Cơ sở lý thuyết**
3. **Phân tích và thiết kế hệ thống**
4. **Kết quả thực nghiệm**
5. **Kết luận và hướng phát triển**

## Vì sao đề tài này

**~77 triệu xe máy** — **85–90%** lưu lượng đường bộ Việt Nam

Cùng hệ thống, cùng phép đo: **chênh 48,6 điểm**, chỉ khác bố cục

*Số liệu Brazil, không phải Việt Nam*

![](figures/fig-gap.png)

## Mục tiêu

- Hệ thống ALPR **hoàn chỉnh**: AI · API · giao diện · CSDL · Docker
- Xử lý **cả biển 1 dòng và 2 dòng**
- Suy luận **hoàn toàn trên CPU** — mặc định, không phải dự phòng
- Chỉ tiêu chốt **trước** khi làm, mỗi chỉ tiêu hai mức

**Ngoài phạm vi:** phân loại loại xe · tracking · barie · huấn luyện OCR từ đầu

## Chọn hướng tiếp cận

**Chọn hai giai đoạn:** YOLO11n phát hiện vùng biển → PaddleOCR đọc ký tự

| Thế hệ | Điểm gãy |
|---|---|
| Cổ điển *(Sobel, contour)* | Vỡ khi đổi ánh sáng, góc chụp |
| **Hai giai đoạn** | Giả định 1 dòng nằm trong hàm mất mát |
| Một giai đoạn *(YOLO đọc ký tự)* | Cần nhãn ký tự — Việt Nam gần như không có |
| End-to-end *(Transformer)* | Đói dữ liệu, nặng, không hợp CPU |

## Đặc thù biển số Việt Nam

Bố cục tách bạch theo **tỉ lệ khung hình** *(QCVN 08:2024/BCA)*

Tỉ lệ **đo thật** lệch khỏi chuẩn nhưng vẫn đúng phía ngưỡng — nên ngưỡng
đặt ở **2,5**, giữa vùng trống

![](figures/fig-layouts.png)

## Căn cứ pháp lý: một phát hiện

> Đề bài dẫn **TT 24/2023/TT-BCA** — văn bản này **đã hết hiệu lực từ 01/01/2025**

- **TT 79/2024/TT-BCA** — cấu trúc biển, seri, màu sắc
- **TT 51/2025/TT-BCA** — thay phụ lục mã tỉnh, còn **34 tỉnh/thành**
- **QCVN 08:2024/BCA** — kích thước và tỉ lệ

⇒ Bộ luật xây trên văn bản **đang có hiệu lực**

## Kiến trúc 5 tầng

Tầng AI là **Python thuần** — cấm import FastAPI hoặc Pydantic. Nó không có
mũi tên nào đi lên, nên thay engine OCR **không đụng một dòng mã API**

| Tầng | Công nghệ |
|---|---|
| L1 — Trình bày | React + TypeScript + Tailwind · 3 trang |
| L2 — API | FastAPI + Swagger · 10 endpoint |
| L3 — Nghiệp vụ | Detection / Video / History / Storage |
| **L4 — AI** | **Python thuần** — YOLO11 + PaddleOCR + Normalizer |
| L5 — Dữ liệu | SQLite + SQLAlchemy + Alembic |

## Cơ sở dữ liệu — một cột làm nên đóng góp

Lưu **cả hai** chuỗi trên **cùng một bản ghi** — không có `raw_ocr_text` thì
**không đo được** đóng góp của hậu xử lý

| Cột | Nội dung |
|---|---|
| `raw_ocr_text` | Chuỗi **thô** do PaddleOCR trả về |
| `plate_number` | Chuỗi **sau** bộ luật hậu xử lý |
| `is_valid_format` | Hợp quy cách Việt Nam hay không |

## Pipeline AI

Không thấy biển ⇒ trả rỗng, **HTTP 200** — không phải lỗi

```
Ảnh → YOLO11n phát hiện → cắt vùng biển
    → phân loại số dòng (ngưỡng tỉ lệ 2,5)
        ├─ 1 dòng → PaddleOCR
        └─ 2 dòng → nắn hình → tách → ghép ngang → PaddleOCR
    → chuẩn hoá + sửa lỗi theo VỊ TRÍ → kiểm tra hợp lệ
    → lưu CẢ chuỗi thô LẪN chuỗi đã sửa
```

## Bộ dữ liệu

- **15.133 ảnh · 15.977 khung biển** · 6 nguồn · 1 lớp
- Chia **10.592 / 3.027 / 1.514** *(phân tầng theo bố cục biển)*

**Chống rò rỉ giữa các tập**

- Băm tri giác, chia theo **nhóm** chứ không theo ảnh
- Rò rỉ vắt qua các tập: **9.126 cặp → 0**
- Phần tồn dư **được công bố**, không giấu

## Huấn luyện

**Chọn YOLO11n — loại bằng hai bước**

1. Máy triển khai không GPU ⇒ bắt buộc có **số liệu tốc độ CPU chính thức**
2. YOLO11n vượt YOLOv8n **đồng thời cả hai chiều**: mAP 39,5 vs 37,3 · CPU 56,1 ms vs 80,4 ms

- Huấn luyện **và** suy luận đều **trên CPU** — 10,1 giờ, không dùng GPU nào
- `imgsz 640` · 20 epoch · seed cố định · `deterministic`

## Kết quả phát hiện — đạt cả 4 chỉ tiêu

**Chênh giữa hai bố cục chỉ 2,09 điểm** ⇒ điểm yếu nằm ở tầng đọc chữ, không phải tầng phát hiện

| Nhóm | N | P | R | mAP50 | mAP50-95 |
|---|---:|---:|---:|---:|---:|
| Biển 1 dòng | 286 | 0,986 | 0,990 | **0,988** | 0,753 |
| Biển 2 dòng | 1.325 | 0,973 | 0,969 | **0,968** | 0,765 |
| **TẤT CẢ** | **1.611** | **0,984** | **0,971** | **0,983** | **0,783** |
| *Chỉ tiêu* | | *≥0,92* | *≥0,90* | *≥0,90* | *≥0,65* |

## Xử lý biển 2 dòng

Nguyên nhân gốc là **kiến trúc**: CRNN/CTC giả định căn chỉnh **trên một dòng**
— giả định nằm trong **hàm mất mát**, thêm dữ liệu không sửa được

![](figures/fig-two-line.png)

## Bộ luật hậu xử lý theo vị trí

Sửa theo **VỊ TRÍ**, không sửa toàn cục — cùng ký tự `O`/`0` nhưng hai vị trí cần hai luật ngược nhau

| Vị trí | Ràng buộc | Luật sửa |
|---|---|---|
| 2 ký tự đầu — mã tỉnh | Chữ số, thuộc 81 mã hợp lệ | `O→0` `I→1` `S→5` |
| Vị trí seri | Chữ cái | `0→O` `1→I` `5→S` |
| Số đăng ký | Chữ số | ép về chữ số |
| **Vùng cấm sửa** | Cả chữ và số đều hợp lệ | **không đụng vào** |

## Kết quả OCR — nói thẳng phần chưa đạt

Toàn bộ khoảng cách nằm ở **biển 2 dòng**: 0,6996 so với **0,9541** của biển 1 dòng

| Chỉ tiêu | Đo được | Ngưỡng | |
|---|---:|---:|:--:|
| A4 — chính xác ký tự | **0,9454** | 0,92 | 🟡 |
| A5 — chuỗi trước hậu xử lý | 0,6373 | 0,80 | ❌ |
| A6 — chuỗi sau hậu xử lý | **0,7512** | 0,85 | ❌ |
| A7 — đầu-cuối | 0,5552 | 0,82 | ❌ |

## Khoảng cách nằm trọn ở biển 2 dòng

Cùng một hệ thống, cùng một phép đo — tách theo bố cục biển

![](../reports/figures/04-ocr-accuracy-by-line-count.png)

## Đóng góp của hậu xử lý — đo được bằng số

CSDL lưu **cả hai** chuỗi trên cùng một bản ghi ⇒ đo được hiệu số

Dồn gần trọn vào biển 2 dòng: **+13,97 điểm** *(1 dòng chỉ +1,23)*

| Chỉ số | Đo được |
|---|---:|
| A5 — chuỗi đúng **trước** hậu xử lý | 0,6373 |
| A6 — chuỗi đúng **sau** hậu xử lý | **0,7512** |
| **Đóng góp** | **+11,39 điểm** |
| Số biển sửa đúng / làm hỏng | **319 / 0** |

## Bậc thang cứu chữa khi đọc hỏng

Chỉ chạy **sau khi đọc hỏng**, chỉ nhận chuỗi **hợp lệ**

⇒ không thể làm hỏng kết quả đang đúng

| Bậc | Cứu được |
|---|---:|
| Cứu dòng trên của biển 2 dòng | **209 biển** |
| Nắn hình / giãn dọc chống méo | **34 biển** |

## Giao diện

Mọi vùng dữ liệu xử lý đủ **4 trạng thái**: chờ · rỗng · lỗi · thành công

![](../screenshots/image-detection.png)

## Demo trực tiếp

Ba tình huống, chạy trên máy thật — **không phải video quay sẵn**

| Bước | Cho thấy điều gì |
|---|---|
| Ảnh ô tô — biển 1 dòng | Đường đi cơ bản, đọc đúng, dưới 1 giây |
| Ảnh xe máy — biển 2 dòng | Chính chỗ khó nhất, split-then-hstack chạy thật |
| Video + Lịch sử | Xử lý bất đồng bộ, tra cứu lại kết quả |

## Kiểm thử và triển khai

- **999 kiểm thử tự động** đạt · bao phủ tầng nghiệp vụ **87,7%**
- Kiểm thử **đơn vị · tích hợp · độ chính xác AI · hiệu năng · chịu tải**
- Tầng AI có bộ test **chạy không cần dựng server**
- `docker compose up` — **một lệnh**, đã dựng và xác minh chạy được
- Soak 300 giây: **1.684 yêu cầu, không rò rỉ bộ nhớ**

## Hiệu năng trên CPU

**i5-14600K · 20 luồng · KHÔNG có GPU CUDA**

Vượt mục tiêu p95 là **đánh đổi có chủ ý**: tắt bậc thang thì p95 về **866 ms**, mất 34 biển

| Chỉ số | Đo được | Ngưỡng |
|---|---:|---|
| Độ trễ p50 | **406 ms** | — |
| Độ trễ p95 | **1.143 ms** | sàn 1.500 ms · mục tiêu 800 ms |
| Yêu cầu đồng thời | **10** | ≥ 5 |

## Phân bố độ trễ — đuôi mới là chỗ tốn

Phần lớn ảnh xong dưới nửa giây; đuôi phải là những ảnh phải thử lại nhiều lượt

![](../reports/figures/07-latency-distribution.png)

## Đối chiếu chỉ tiêu — bảng chốt hạ

✅ đạt mục tiêu · 🟡 đạt ngưỡng tối thiểu · ❌ chưa đạt

| Nhóm | Chỉ tiêu | Kết quả |
|---|---|:--:|
| Phát hiện | mAP@0.5 **0,9829** · mAP@0.5:0.95 **0,7834** · P **0,9837** · R **0,9714** | ✅ |
| Đọc ký tự | A4 **0,9454** | 🟡 |
| Đọc chuỗi | A5 **0,6373** · A6 **0,7512** · A7 **0,5552** | ❌ |
| Hiệu năng | p95 **1.143 ms** *(sàn 1.500)* · nạp mô hình **6,4 s** · truy vấn **18,7 ms** | 🟡 |
| Phần mềm | 999 test · bao phủ 87,7% · `docker compose up` | ✅ |

## Hạn chế — nói thẳng

| Hạn chế | Nguyên nhân gốc |
|---|---|
| **OCR biển 2 dòng chưa đạt** — A6 0,6996 so với 0,9541 của biển 1 dòng | Bộ đọc dòng đơn; xe máy chiếm 79,8% tập nhãn |
| **A7 = 0,5552 không đại diện** | Không bộ dữ liệu nào vừa có ảnh toàn cảnh vừa có chuỗi biển ⇒ đo trên ảnh cắt sẵn, ngoài phân bố bộ phát hiện |
| Tập test **không xuyên bộ dữ liệu** | Chỉ đo tổng quát hoá *trong* phân bố ⇒ mAP lạc quan hơn thực tế |
| Một yêu cầu mức **Must** đã đưa ra khỏi phạm vi | Thu gọn cho demo; API thống kê vẫn phục vụ và vẫn có kiểm thử |

## Ba can thiệp, một kết luận

Cả ba **ngoài** mô hình nhận dạng: A6 **0,6098 → 0,7512**

**Dư địa đã cạn** — lỗi còn lại là ký tự *chưa từng đọc ra*

| Can thiệp | Thu được |
|---|---:|
| Bộ luật hậu xử lý theo vị trí | **+11,39 điểm** A6 |
| Cứu dòng trên | 209 biển |
| Nắn hình chống méo | 34 biển |

## Hướng phát triển

**Ngắn hạn** — gỡ đúng nút thắt đã định vị

1. **Fine-tune bộ nhận dạng** trên vùng cắt biển Việt Nam
2. **Gán nhãn chuỗi cho ảnh hiện trường** ⇒ đo được A7 đúng cách

**Trung hạn**

3. Tập test **xuyên bộ dữ liệu** — đo tổng quát hoá ngoài phân bố
4. Xuất ONNX / OpenVINO để hạ độ trễ đuôi

## Kết luận

**Đã làm được**

- Hệ thống **5 tầng chạy thật**, đóng gói Docker một lệnh
- Phát hiện đạt **cả 4 chỉ tiêu**: mAP50 **0,983** · mAP50-95 **0,783**
- Hậu xử lý theo vị trí — **+11,39 điểm**, đo tách bạch
- **999 kiểm thử** đạt · bao phủ tầng nghiệp vụ 87,7%

**Đóng góp học thuật**

- Hai con số 1 dòng / 2 dòng **tách bạch trên cùng một hệ thống**
- Quy trình đo **tự bắt được lỗi của chính nó**

## Cảm ơn

**Em xin cảm ơn thầy cô đã lắng nghe. Em xin sẵn sàng nhận câu hỏi.**

| Tra nhanh | |
|---|---|
| Dữ liệu | 15.133 ảnh · 15.977 khung · 6 nguồn |
| Mô hình | YOLO11n · imgsz 640 · 20 epoch |
| Phát hiện | mAP50 **0,983** · mAP50-95 **0,783** |
| Đọc chuỗi | A4 **0,9454** · A6 **0,7512** · A7 **0,5552** |
| Độ trễ p95 | **1.143 ms** trên CPU *(p50 406 ms)* |
