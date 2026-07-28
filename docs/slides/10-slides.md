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

1. `#` = slide phân đoạn · `##` = một slide nội dung. Cấp này được ghim bằng
   `--slide-level=2` trong `scripts/build_thesis.py`, không suy ra từ nội dung.

2. **Bảng phải là khối CUỐI CÙNG của slide.** Pandoc cắt sang slide mới ở mọi
   thứ đứng sau một bảng, nên một dòng ghi chú đặt dưới bảng sẽ lặng lẽ sinh
   thêm một slide mồ côi mang tiêu đề là chính dòng ghi chú đó. Mọi câu dẫn và
   mọi kết luận phải nằm TRÊN bảng.

Mọi con số lấy từ lượt đo 28/07/2026 (`docs/reports/05-results.json`).
-->

# Mở đầu

## Vì sao đề tài này

**~77 triệu xe máy** — **85–90%** lưu lượng đường bộ Việt Nam

Cùng hệ thống, cùng phép đo: **chênh 48,6 điểm**, chỉ khác bố cục

*Số liệu Brazil, không phải Việt Nam*

| Loại xe | Bố cục | Đọc đúng |
|---|---|---:|
| Ô tô | 1 dòng | **94,3%** |
| Xe máy | **2 dòng** | **45,7%** |

## Mục tiêu

- Hệ thống ALPR **hoàn chỉnh**: AI · API · giao diện · CSDL · Docker
- Xử lý **cả biển 1 dòng và 2 dòng**
- Suy luận **hoàn toàn trên CPU** — mặc định, không phải dự phòng
- Chỉ tiêu chốt **trước** khi làm, mỗi chỉ tiêu hai mức

**Ngoài phạm vi:** phân loại loại xe · tracking · barie · huấn luyện OCR từ đầu

# Nền tảng

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

Khoảng **(2,000 ; 4,727)** bỏ trống ⇒ phân loại số dòng bằng hình học

| Loại biển | Tỉ lệ | Số dòng |
|---|:--:|:--:|
| Ô tô biển dài | **4,727** | 1 |
| Ô tô biển ngắn | **2,000** | 2 |
| Xe mô tô | **1,357** | 2 |

## Căn cứ pháp lý: một phát hiện

> Đề bài dẫn **TT 24/2023/TT-BCA** — văn bản này **đã hết hiệu lực từ 01/01/2025**

- **TT 79/2024/TT-BCA** — cấu trúc biển, seri, màu sắc
- **TT 51/2025/TT-BCA** — thay phụ lục mã tỉnh, còn **34 tỉnh/thành**
- **QCVN 08:2024/BCA** — kích thước và tỉ lệ

⇒ Bộ luật xây trên văn bản **đang có hiệu lực**

# Thiết kế

## Kiến trúc 5 tầng

| Tầng | Công nghệ |
|---|---|
| L1 — Trình bày | React + TypeScript + Tailwind · 3 trang |
| L2 — API | FastAPI + Swagger · 10 endpoint |
| L3 — Nghiệp vụ | Detection / Video / History / Storage |
| **L4 — AI** | **Python thuần** — YOLO11 + PaddleOCR + Normalizer |
| L5 — Dữ liệu | SQLite + SQLAlchemy + Alembic |

## Tách tầng AI khỏi tầng API

**Ràng buộc:** `ai/inference/` cấm import FastAPI hoặc Pydantic

- Khối AI **không có mũi tên nào đi lên** — không biết gì về HTTP, CSDL hay ai gọi nó
- Kiểm thử độc lập, không cần dựng server
- Cùng một pipeline dùng cho huấn luyện, đánh giá và phục vụ
- Thay engine OCR **không đụng một dòng mã API**

```bash
grep -r "fastapi\|pydantic" ai/inference/   # phải ra rỗng
```

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

# Dữ liệu và huấn luyện

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

- Huấn luyện trên **GPU đám mây**, triển khai suy luận **trên CPU**
- `imgsz 640` · 20 epoch · seed cố định · `deterministic`

## Kết quả phát hiện — đạt cả 4 chỉ tiêu

**Chênh giữa hai bố cục chỉ 2,09 điểm** ⇒ điểm yếu nằm ở tầng đọc chữ, không phải tầng phát hiện

| Nhóm | N | P | R | mAP50 | mAP50-95 |
|---|---:|---:|---:|---:|---:|
| Biển 1 dòng | 286 | 0,986 | 0,990 | **0,988** | 0,753 |
| Biển 2 dòng | 1.325 | 0,973 | 0,969 | **0,968** | 0,765 |
| **TẤT CẢ** | **1.611** | **0,984** | **0,971** | **0,983** | **0,783** |
| *Chỉ tiêu* | | *≥0,92* | *≥0,90* | *≥0,90* | *≥0,65* |

# Đóng góp kỹ thuật

## Xử lý biển 2 dòng

**Nguyên nhân gốc là kiến trúc, không phải chất lượng mô hình**

- CRNN/CTC giả định căn chỉnh **trên một dòng** — nằm trong **hàm mất mát**
- PaddleOCR ép cao 48 px ⇒ **mỗi dòng chỉ còn ~24 px**

**Giải pháp — split-then-hstack**

- Nắn hình → tách hai nửa chồng lấn → ghép ngang → OCR **một lần**
- Đọc từng nửa: **3,5%** · ghép ngang: **64,5%**

## Bộ luật hậu xử lý theo vị trí

Sửa theo **VỊ TRÍ**, không sửa toàn cục — cùng ký tự `O`/`0` nhưng hai vị trí cần hai luật ngược nhau

| Vị trí | Ràng buộc | Luật sửa |
|---|---|---|
| 2 ký tự đầu — mã tỉnh | Chữ số, thuộc 81 mã hợp lệ | `O→0` `I→1` `S→5` |
| Vị trí seri | Chữ cái | `0→O` `1→I` `5→S` |
| Số đăng ký | Chữ số | ép về chữ số |
| **Vùng cấm sửa** | Cả chữ và số đều hợp lệ | **không đụng vào** |

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

# Kết quả và hệ thống

## Giao diện

Mọi vùng dữ liệu xử lý đủ **4 trạng thái**: chờ · rỗng · lỗi · thành công

| Trang | Chức năng |
|---|---|
| Nhận dạng ảnh *(chủ)* | Chọn ảnh là chạy ngay, khung bao + kết quả hiện cùng lúc |
| Nhận dạng video | Bất đồng bộ — trả `job_id`, hỏi tiến độ, xuất video gắn nhãn |
| Lịch sử | Lọc, sắp xếp, phân trang — **trạng thái nằm trên URL** |

## Hiệu năng trên CPU

**i5-14600K · 20 luồng · KHÔNG có GPU CUDA**

Vượt mục tiêu p95 là **đánh đổi có chủ ý**: tắt bậc thang thì p95 về **866 ms**, mất 34 biển

| Chỉ số | Đo được | Ngưỡng |
|---|---:|---|
| Độ trễ p50 | **406 ms** | — |
| Độ trễ p95 | **1.143 ms** | sàn 1.500 ms · mục tiêu 800 ms |
| Yêu cầu đồng thời | **10** | ≥ 5 |

# Kết luận

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

**Em xin cảm ơn thầy cô đã lắng nghe**

**Em xin sẵn sàng nhận câu hỏi từ hội đồng**
