# Bố cục poster A0 dọc

**Đề tài:** Xây dựng hệ thống nhận dạng biển số xe Việt Nam ứng dụng Trí tuệ nhân tạo
**Thuộc:** Phase 10 — chuẩn bị bảo vệ · **Ngày lập:** 19/07/2026

---

## 1. Thông số kỹ thuật

| Hạng mục | Giá trị |
|---|---|
| Khổ giấy | **A0 dọc (portrait)** — 841 mm × 1189 mm |
| Độ phân giải thiết kế | 300 DPI khi in ⇒ **9.933 × 14.043 px** (hoặc thiết kế ở kích thước thật bằng mm) |
| Lề an toàn | **50 mm** mọi phía — không đặt chữ ra ngoài vùng an toàn |
| Vùng nội dung | 741 mm × 1089 mm |
| Máng giữa các cột | **20 mm** |
| Khoảng cách đọc mục tiêu | **1,5 m** (chi phối toàn bộ bảng font size ở mục 3) |
| Không gian âm | ≥ **25%** diện tích poster phải là khoảng trắng |

> **Nguyên tắc chi phối toàn bộ thiết kế: người đi ngang phải nắm được ý chính trong 30 giây.**
> Nghĩa là ba thứ — tiêu đề, con số 94,3% / 45,7%, và sơ đồ kiến trúc — phải đọc được **mà không cần dừng lại**. Mọi thứ khác là phần thưởng cho người dừng lại đọc kỹ.

---

## 2. Sơ đồ bố cục tổng thể

```
┌──────────────────────────────────────────────────────────────────────┐
│ ← 50mm lề →                                                          │
│ ┌──────────────────────────────────────────────────────────────────┐ │
│ │  KHỐI 0 — TIÊU ĐỀ                          cao 160 mm (13,5%)    │ │
│ │  Logo trường · Tên đề tài · SV · GVHD · Khoa · 07/2026            │ │
│ └──────────────────────────────────────────────────────────────────┘ │
│ ┌──────────────────────────────────────────────────────────────────┐ │
│ │  KHỐI H — DẢI HOOK (băng ngang toàn chiều rộng)  cao 130 mm      │ │
│ │  94,3%  ▮▮▮▮▮▮▮▮▮▮   vs   45,7%  ▮▮▮▮▮                          │ │
│ │  1 dòng            2 dòng          → chênh 48,6 điểm             │ │
│ └──────────────────────────────────────────────────────────────────┘ │
│ ┌──────────┐  ┌──────────────────────────┐  ┌──────────────────────┐ │
│ │ CỘT TRÁI │  │      CỘT GIỮA            │  │     CỘT PHẢI         │ │
│ │  25%     │  │        40%               │  │       35%            │ │
│ │ 180 mm   │  │       290 mm             │  │      251 mm          │ │
│ │          │  │                          │  │                      │ │
│ │ 1 Đặt    │  │  4 Kiến trúc 5 tầng      │  │  7 Kết quả           │ │
│ │   vấn đề │  │    (SƠ ĐỒ LỚN)           │  │    (bảng, có ô trống)│ │
│ │          │  │                          │  │                      │ │
│ │ 2 Mục    │  │  5 Pipeline AI           │  │  8 Giao diện         │ │
│ │   tiêu   │  │    (sơ đồ luồng)         │  │    (ảnh chụp)        │ │
│ │          │  │                          │  │                      │ │
│ │ 3 Phương │  │  6 XỬ LÝ BIỂN 2 DÒNG     │  │  9 Hạn chế           │ │
│ │   pháp   │  │    (KHỐI ĐẮT NHẤT)       │  │                      │ │
│ │          │  │                          │  │ 10 Kết luận          │ │
│ │          │  │                          │  │                      │ │
│ └──────────┘  └──────────────────────────┘  └──────────────────────┘ │
│ ┌──────────────────────────────────────────────────────────────────┐ │
│ │  KHỐI F — CHÂN TRANG          cao 60 mm                          │ │
│ │  Căn cứ pháp lý · Công nghệ · Tài liệu tham khảo chính · QR       │ │
│ └──────────────────────────────────────────────────────────────────┘ │
│                                                        ← 50mm lề →   │
└──────────────────────────────────────────────────────────────────────┘
```

**Phân bổ chiều cao:**

| Khối | Chiều cao | % |
|---|---:|---:|
| Khối 0 — Tiêu đề | 160 mm | 13,5% |
| Khối H — Dải hook | 130 mm | 11,0% |
| Ba cột nội dung | 739 mm | 62,2% |
| Khối F — Chân trang | 60 mm | 5,0% |
| Lề trên + dưới | 100 mm | 8,4% |

**Phân bổ chiều rộng ba cột** (tổng 741 mm, trừ 2 máng × 20 mm = 701 mm khả dụng):

| Cột | Rộng | % | Vì sao |
|---|---:|---:|---|
| Trái | 180 mm | 25% | Chữ nhiều, hình ít — cột hẹp giúp dòng ngắn, dễ đọc |
| **Giữa** | **290 mm** | **40%** | Chứa **ba sơ đồ** — cần chiều rộng nhất |
| Phải | 251 mm | 35% | Chứa bảng và ảnh chụp màn hình |

---

## 3. Quy định font size — bắt buộc đọc được từ 1,5 m

Quy tắc kinh nghiệm: **chiều cao chữ tính bằng mm ≥ khoảng cách đọc tính bằng m × 5**.
Với 1,5 m ⇒ tối thiểu **7,5 mm** ⇒ khoảng **21 pt**. Bảng dưới đã cộng biên an toàn.

| Cấp | Dùng ở đâu | Cỡ **tối thiểu** | Cỡ **đề xuất** | Đọc được từ |
|---|---|---:|---:|---|
| **T0 — Tên đề tài** | Khối 0 | 90 pt | **110 pt** | 5 m |
| **T1 — Con số hook** | Khối H (94,3% / 45,7%) | 150 pt | **200 pt** | 8 m |
| **T2 — Tiêu đề khối** | "KIẾN TRÚC HỆ THỐNG", … | 48 pt | **56 pt** | 3 m |
| **T3 — Tiêu đề phụ** | Tiêu đề trong khối | 32 pt | **36 pt** | 2 m |
| **T4 — Chữ thân** | Toàn bộ gạch đầu dòng | **28 pt** | **32 pt** | **1,5 m** ✅ |
| **T5 — Chữ trong bảng** | Ô bảng | **24 pt** | 26 pt | 1,5 m |
| **T6 — Nhãn hình / chú thích** | Nhãn trong sơ đồ, caption | **22 pt** | 24 pt | 1,2 m |
| **T7 — Nguồn trích dẫn** | Chân trang, nguồn dưới hình | **18 pt** | 20 pt | 0,8 m |

> ⛔ **Không có chữ nào dưới 18 pt trên poster.** Nội dung nào phải nhỏ hơn 18 pt mới vừa là nội dung **thừa** — cắt đi, đừng thu nhỏ.

**Ràng buộc chữ thân**
- Chiều dài dòng: **45–75 ký tự**. Cột trái 180 mm ở 32 pt ≈ 50 ký tự/dòng — đạt.
- Giãn dòng: **1,4×** cỡ chữ.
- Không viết đoạn văn quá **4 dòng** — quá thì chuyển thành gạch đầu dòng hoặc bảng.
- **Không căn đều hai bên** (justify) — căn trái, để lề phải tự nhiên.

**Font chữ**
- Tiêu đề T0–T2: font sans-serif đậm, có **đủ dấu tiếng Việt** — *Be Vietnam Pro*, *Inter*, hoặc *Montserrat*
- Chữ thân T3–T7: cùng họ font, weight Regular / Medium
- Số liệu trong bảng: dùng **tabular figures** (chữ số cùng bề rộng) để các cột số thẳng hàng
- ⚠️ **Kiểm tra dấu tiếng Việt trước khi in** — nhiều font đẹp hỏng ở dấu nặng, dấu ngã, chữ "ữ", "ượ"

---

## 4. Bảng màu

| Vai trò | Màu | Mã | Dùng ở đâu |
|---|---|---|---|
| Nền chính | Trắng ngà | `#FFFFFF` | Toàn poster |
| Chữ chính | Xanh đen | `#0F172A` | Mọi chữ thân |
| **Nhấn 1 — chủ đạo** | Xanh dương | `#2563EB` | Tiêu đề khối, viền, khối API/Frontend |
| **Nhấn 2 — tầng AI** | Vàng hổ phách | `#D97706` | Khối AI trong sơ đồ (khớp `system-architecture.md`) |
| **Nhấn 3 — cảnh báo / biển 2 dòng** | Đỏ | `#DC2626` | Con số 45,7% · nhánh biển 2 dòng · dấu ❌ |
| Thành công | Xanh lá | `#059669` | Dấu ✅ trong khối Kết luận |
| Nền khối phụ | Xám nhạt | `#F1F5F9` | Nền bảng, nền khối trích dẫn |
| Viền | Xám | `#CBD5E1` | Đường kẻ bảng, viền khối |

**Ba quy tắc màu**
1. **Đỏ chỉ dùng cho một ý duy nhất: biển 2 dòng và các hạn chế.** Dùng đỏ cho thứ khác sẽ làm loãng thông điệp chính.
2. **Màu tầng AI (vàng hổ phách) phải giống hệt màu trong sơ đồ kiến trúc gốc** — người xem poster rồi xem slide phải nhận ra cùng một khối.
3. Kiểm tra tương phản đạt **WCAG AA** (≥ 4,5:1) và **in thử đen trắng** — nếu đen trắng vẫn phân biệt được thì thiết kế đủ khoẻ.

---

# 5. Đặc tả từng khối

## KHỐI 0 — Tiêu đề

**Vị trí:** trên cùng, băng toàn chiều rộng · **Kích thước:** 741 × 160 mm

**Nội dung**

| Dòng | Nội dung | Cỡ |
|---|---|---|
| 1 | Tên trường · Khoa (chữ nhỏ, trên cùng) | T3 — 36 pt |
| 2 | **XÂY DỰNG HỆ THỐNG NHẬN DẠNG BIỂN SỐ XE VIỆT NAM ỨNG DỤNG TRÍ TUỆ NHÂN TẠO** | **T0 — 110 pt** |
| 3 | Sinh viên: [tên] — MSSV [số] — Lớp [lớp] · GVHD: [tên] | T3 — 36 pt |
| 4 | Tháng 7 năm 2026 | T7 — 20 pt |

**Hình:** logo trường góc trên **trái**, cao 90 mm. Nếu có logo khoa thì đặt góc trên **phải**, cùng chiều cao.

**Ghi chú thiết kế:** dải nền màu `#2563EB` với chữ trắng, hoặc nền trắng với thanh màu dày 12 mm dưới đáy khối. Chọn một, đừng làm cả hai.

---

## KHỐI H — Dải hook

**Vị trí:** ngay dưới tiêu đề, băng toàn chiều rộng · **Kích thước:** 741 × 130 mm

> **Đây là khối quyết định poster có được dừng lại xem hay không. Đầu tư nhiều nhất vào khối này.**

**Nội dung**

```
        94,3%                              45,7%
   ████████████████                   ███████
    Ô tô — biển 1 dòng             Xe máy — biển 2 dòng

              → CHÊNH LỆCH 48,6 ĐIỂM PHẦN TRĂM ←
        Cùng một hệ thống ALPR. Cùng một phép đo.
   Ở Việt Nam, xe máy chiếm 85–90% lưu lượng đường bộ.
```

**Hình:** hai cột đơn giản, cột trái xanh `#2563EB`, cột phải **đỏ** `#DC2626`. Chiều cao cột đúng tỉ lệ với giá trị. **Không** thêm lưới, trục, hay chú giải — hình càng trơ càng mạnh.

**Cỡ chữ:** con số ở **T1 = 200 pt** · nhãn dưới cột T3 = 36 pt · dòng "chênh lệch" T2 = 56 pt

**Chú thích bắt buộc** (T7 — 20 pt, đặt góc phải dưới khối):
> *Nguồn: Laroca và cộng sự, VISAPP 2022 — OpenALPR trên RodoSol-ALPR (Brazil), tập cân bằng 4.000 + 4.000 ảnh. Dẫn làm analogue về độ khó của biển hai dòng, **không phải số liệu Việt Nam**.*

⚠️ Không lược bỏ chú thích này để tiết kiệm chỗ. Trình bày số liệu Brazil như số liệu Việt Nam là một lỗi phương pháp luận nghiêm trọng.

---

## CỘT TRÁI (180 mm) — Vì sao và làm gì

### Khối 1 — Đặt vấn đề *(cao ~200 mm)*

**Tiêu đề khối:** `ĐẶT VẤN ĐỀ` (T2)

**Nội dung** (T4 — 32 pt, gạch đầu dòng, tối đa 5 dòng)
- ~77 triệu xe máy · **85–90%** lưu lượng đường bộ Việt Nam
- Hệ thống ALPR nhập khẩu **hỏng đúng chỗ Việt Nam cần nhất** (xem dải trên)
- Ba đặc thù không có ở bộ quy tắc nước ngoài nào:
  - Bố cục tách bạch theo tỉ lệ khung hình
  - **Tập ký tự seri phụ thuộc VỊ TRÍ**
  - Mã tỉnh là tập hữu hạn có lỗ hổng — 89 giá trị, **81 mã dùng thật**

**Hình:** 3 ảnh biển số cắt từ tập dữ liệu thật, xếp dọc (ô tô dài / ô tô ngắn / xe máy), mỗi ảnh cao ~28 mm, có nhãn tỉ lệ khung hình bên cạnh: **4,727 · 2,000 · 1,357**.

---

### Khối 2 — Mục tiêu và chỉ tiêu *(cao ~230 mm)*

**Tiêu đề khối:** `MỤC TIÊU` (T2)

**Nội dung**
- Hệ thống ALPR **hoàn chỉnh** cho biển số Việt Nam
- Hỗ trợ **cả biển 1 dòng và 2 dòng**
- Suy luận **hoàn toàn trên CPU** — mặc định, không phải chế độ dự phòng

**Bảng chỉ tiêu** (T5 — 24 pt, 4 dòng, không nhiều hơn)

| Mã | Chỉ tiêu | Ngưỡng |
|---|---|:--:|
| A1 | mAP@0.5 phát hiện | ≥ 0,90 |
| A6 | Chính xác biển sau hậu xử lý | ≥ 0,90 |
| **A7** | **Chính xác E2E toàn trình** | **≥ 0,88** |
| P1 | Độ trễ 1 ảnh, p95, CPU | ≤ 800 ms |

**Ghi chú nhỏ dưới bảng** (T7): *Chỉ tiêu chốt trước khi bắt đầu cài đặt, không điều chỉnh theo kết quả.*

---

### Khối 3 — Phương pháp *(cao ~280 mm)*

**Tiêu đề khối:** `PHƯƠNG PHÁP` (T2)

**Nội dung**
- Kiến trúc **hai giai đoạn**: YOLO11n phát hiện → PaddleOCR đọc → **luật hậu xử lý Việt Nam**
- Vì sao YOLO11n: yêu cầu bắt buộc là **có số liệu tốc độ CPU chính thức**; và nó vượt YOLOv8n **cả hai chiều** (mAP 39,5 vs 37,3 · CPU 56,1 ms vs 80,4 ms)
- **Căn cứ pháp lý hiện hành** — không dùng văn bản hết hiệu lực:

> ⚠️ Đề bài dẫn **TT 24/2023/TT-BCA**. Đối chiếu nguồn gốc: văn bản này **đã hết hiệu lực từ 01/01/2025**.
> Toàn bộ luật của hệ thống xây trên **TT 79/2024/TT-BCA** (sửa bởi TT 13/2025 và TT 51/2025) + **QCVN 08:2024/BCA**.

- Hệ quả thiết kế: **tri thức pháp lý tách khỏi mô hình**, gom vào một file `plate_rules.py`. TT 51/2025 đổi phụ lục mã tỉnh giữa lúc làm ⇒ chỉ sửa **một bảng hằng số**.

**Hình:** khối trích dẫn nền xám `#F1F5F9` có viền trái dày 6 mm màu đỏ, chứa đoạn cảnh báo về TT 24/2023.

---

## CỘT GIỮA (290 mm) — Hệ thống hoạt động thế nào

### Khối 4 — Kiến trúc hệ thống *(cao ~260 mm)*

**Tiêu đề khối:** `KIẾN TRÚC HỆ THỐNG` (T2)

**Hình — SƠ ĐỒ LỚN, chiếm ~200 mm chiều cao:**
- **Nguồn:** render sơ đồ mermaid ở `docs/architecture/system-architecture.md` mục 2 ra **SVG** (không dùng PNG — poster in 300 DPI cần vector)
- 5 tầng xếp dọc: Trình bày (React) → API (FastAPI) → Nghiệp vụ → **AI (vàng hổ phách)** → Dữ liệu (SQLite)
- ⚠️ **Bắt buộc thấy rõ: khối AI không có mũi tên nào đi lên**
- Nhãn trong sơ đồ tối thiểu **T6 = 22 pt** — nếu sơ đồ gốc chữ nhỏ hơn thì phải chỉnh lại, không phóng to ảnh bitmap

**Nội dung chữ** (T4, đặt bên phải hoặc dưới sơ đồ, tối đa 3 dòng)
- Tầng AI là **Python thuần — cấm import FastAPI/Pydantic**, kiểm chứng bằng một lệnh `grep`
- Lợi ích đo được: **104 unit test** chạy không cần dựng server · thay engine OCR không đụng backend
- ✅ Đã kiểm chứng bằng chạy thật: **10 endpoint** phản hồi đúng qua HTTP · frontend build thành công, **10 endpoint** khớp kiểu TypeScript từng trường

---

### Khối 5 — Pipeline AI *(cao ~200 mm)*

**Tiêu đề khối:** `PIPELINE XỬ LÝ` (T2)

**Hình — sơ đồ luồng ngang, ~150 mm chiều cao:**
- **Nguồn:** mermaid ở `system-architecture.md` mục 3, render SVG
- Nhánh biển 2 dòng tô **đỏ** `#DC2626` và dày hơn các nhánh khác — dẫn mắt sang Khối 6 ngay bên dưới

```
Ảnh → YOLO11n → Cắt → [Mấy dòng?] ─┬─ 1 dòng ─→ OCR ─┐
                                    └─ 2 dòng ─→ TÁCH+GHÉP ─→ OCR ─┘
   → Chuẩn hoá theo LUẬT VN → Lưu CẢ raw_ocr_text LẪN plate_number
```

**Nội dung chữ** (T4, 2 dòng)
- Không thấy biển ⇒ **HTTP 200** + kết quả rỗng, **không phải lỗi**
- Biển không khớp định dạng ⇒ **vẫn lưu**, chỉ đánh dấu `is_valid_format = False`

---

### Khối 6 — Xử lý biển 2 dòng ⭐ *(cao ~279 mm — khối lớn nhất poster)*

**Tiêu đề khối:** `XỬ LÝ BIỂN HAI DÒNG` (T2, có viền đỏ quanh cả khối để nổi bật)

> **Đây là khối đắt nhất về mặt kỹ thuật — cho nó nhiều diện tích nhất.**

**Nội dung — chia 3 phần:**

**(a) Vấn đề** (T4)
- Nguyên nhân gốc là **KIẾN TRÚC**, không phải chất lượng model
- CRNN/CTC giả định **alignment đơn điệu trên MỘT dòng** — nó nằm trong **hàm mất mát**, không sửa được bằng thêm dữ liệu
- Bằng chứng: PaddleOCR resize về **cao cố định 48 px**. Crop biển xe máy AR ≈ **1,36** ⇒ **mỗi dòng chỉ còn ~24 px**

**(b) Giải pháp — HÌNH QUAN TRỌNG NHẤT POSTER** *(cao ~110 mm)*

> 🔴 **CẦN CHUẨN BỊ — hiện chưa có.** Ảnh minh hoạ 4 bước **split-then-hstack** trên một crop biển xe máy **thật**, xuất từ ảnh trung gian của `ai/inference/two_line.py`:
>
> `[crop gốc, AR 1,36]` → `[đã rectify]` → `[2 nửa tách rời]` → `[dải ghép ngang, AR ~5,4]`
>
> Bốn khung xếp ngang, nối bằng mũi tên, mỗi khung có nhãn T6 phía dưới. Đây là hình người xem nhớ lâu nhất — đầu tư làm cho đẹp.

- Mỗi dòng dùng **trọn 48 px** thay vì 24 px
- Chuỗi trở lại **đơn điệu một chiều** — đúng giả định CRNN
- OCR gọi **một lần** trên dải đã ghép
- ⚠️ Bắt buộc **rectify trước khi tách** — biển nghiêng thì đường cắt sẽ cắt qua ký tự

**(c) Nhận biết mấy dòng — ngưỡng có hai căn cứ độc lập** (T4 + hình nhỏ)
- Từ **QCVN 08:2024**: khoảng trống (2,000 ; 4,727) không có loại biển nào rơi vào
- Từ **dữ liệu**: phân bố AR của 15.977 khung **lưỡng đỉnh**, vùng trũng ở 2,2–2,6 ⇒ ngưỡng **2,5** rơi đúng đáy

**Hình nhỏ** *(~60 mm)*: biểu đồ phân bố AR, có đường đứng đỏ tại 2,5. Nguồn: `datasets/statistics/`.

**Bảng — đo được độ chính xác của chính heuristic** (T5)

| | Đoán 1 dòng | Đoán 2 dòng |
|---|---:|---:|
| **Thật 1 dòng** (1.641) | 1.509 ✓ | 132 ✗ |
| **Thật 2 dòng** (3.559) | 7 ✗ | 3.552 ✓ |

→ **97,33%** trên 5.200 khung của `hf_vn_plates_segment` — bộ **duy nhất** trong 9 bộ có nhãn số dòng thật, nên đây là chỗ duy nhất đo trực tiếp được
→ lệch **một chiều 19:1** · nguyên nhân: box bao polygon có đệm, biển dài mảnh thì đệm chiều cao chiếm tỉ lệ lớn hơn

---

## CỘT PHẢI (251 mm) — Kết quả và ranh giới

### Khối 7 — Kết quả *(cao ~250 mm)*

**Tiêu đề khối:** `KẾT QUẢ` (T2)

**(a) Bộ dữ liệu** (T4)
- **15.133 ảnh / 15.977 khung** · chia 10.592 / 3.027 / 1.514 (70/20/10, phân tầng, seed 42)
- Lệch tỉ lệ biển 2 dòng giữa 3 tập tối đa **0,06 điểm phần trăm**
- Chống rò rỉ: perceptual hash 64-bit, chia theo **nhóm** không theo ảnh
- 🔴 **Phát hiện: 73 cặp ảnh trùng vắt qua ranh giới train↔val của bản chia gốc tác giả** ⇒ vứt bỏ bản chia gốc, chia lại từ đầu

**(b) Kết quả detection — ✅ ĐÃ ĐO** (T5)

> Đo trên `models/best.pt` (imgsz 640, split v3), tập TEST v3 (1.514 ảnh). Đạt cả bốn chỉ tiêu.

| Đo trên tập TEST v3 | P | R | mAP50 | mAP50-95 |
|---|:--:|:--:|:--:|:--:|
| Biển 1 dòng (286) | 0,986 | 0,990 | 0,988 | 0,753 |
| Biển 2 dòng (1.325) | 0,973 | 0,969 | 0,968 | 0,765 |
| **TẤT CẢ (1.611)** | **0,984** | **0,971** | **0,983** | **0,783** |
| *Ngưỡng chỉ tiêu* | *≥0,92* | *≥0,90* | *≥0,90* | *≥0,65* |

> ✅ Chênh layout chỉ **2,09 điểm** mAP50 — detection ít nhạy với layout. Điểm yếu biển 2 dòng nằm ở tầng OCR.

**(c) Hiệu năng — ✅ NFR-P1 ĐẠT** (T5)

> Độ trễ E2E p95 trên `best.pt`, máy rảnh: **731 ms** (client-side) / **780 ms** (in-process), dưới mục tiêu 800 ms.
> Phân rã: OCR **64,3%** (112,55 ms/biển) · detect **34,2%** (59,83 ms). Con số cũ 5.857 ms đã bị bác bỏ (nhiễm tải + sai checkpoint + lỗi crop).
> Phần cứng: Intel Core i5-14600K, 14 nhân / 20 luồng, **không có GPU CUDA**.

**Hình:** biểu đồ cột xếp chồng ngang minh hoạ ngân sách 405 ms, có vạch đứt ở 800 ms.

---

### Khối 8 — Giao diện hệ thống *(cao ~230 mm)*

**Tiêu đề khối:** `GIAO DIỆN HỆ THỐNG` (T2)

**Hình — ảnh chụp màn hình thật, đã có sẵn trong `docs/screenshots/`:**

| Vị trí | File | Kích thước |
|---|---|---|
| Trên, lớn | `image-detection.png` — **quan trọng nhất**, hiện kết quả AI thật với bounding box | rộng 251 mm, cao ~140 mm |
| Dưới trái | `video-detection.png` | ~120 × 70 mm |
| Dưới phải | `history.png` | ~120 × 70 mm |

*(`docs/screenshots/` còn **3 tệp dùng được**: `image-detection.png` · `video-detection.png` · `history.png` — đúng ba trang của giao diện hiện hành, poster dùng cả ba. `dashboard.png` **không còn dùng**: trang Tổng quan đã gỡ khỏi giao diện 2026-07-20.)*

⚠️ **Chụp lại ảnh trước khi in.** Cả 3 ảnh hiện có chụp khi sidebar còn **5 mục** và trang chủ còn là **Tổng quan**. Giao diện nay chỉ còn **3 trang**, trang chủ là **Nhận dạng ảnh** và **không còn trang Tổng quan** — poster in ảnh cũ sẽ mâu thuẫn với dòng "3 trang" ngay bên dưới.

**Nội dung chữ** (T4, 2 dòng)
- **3 trang**: Nhận dạng ảnh *(trang chủ)* · Video (bất đồng bộ, `job_id`) · Lịch sử — cộng chế độ thời gian thực và số liệu tổng hợp giữ ở tầng API (`POST /api/detect/frame`, `GET /api/statistics`)
- Mọi vùng dữ liệu xử lý đủ **4 trạng thái**: loading / empty / error / success

⚠️ **Ảnh chụp phải ở độ phân giải gốc.** Ảnh 1920 px phóng lên 251 mm ở 300 DPI sẽ vỡ. Nếu cần, chụp lại màn hình ở chế độ độ phân giải cao hoặc chụp từng vùng rồi ghép.

---

### Khối 9 — Hạn chế *(cao ~140 mm)*

**Tiêu đề khối:** `HẠN CHẾ` (T2)

> **Không lược bỏ khối này để lấy chỗ cho kết quả.** Một poster có mục hạn chế trung thực đáng tin hơn một poster toàn kết quả đẹp.

**Nội dung** (T4, dùng ký hiệu ❌ / ⚠️ nhất quán)
- ❌ **OCR biển 2 dòng KHÔNG đạt** — A4 0,873 / A5 0,610 / A6 0,656; toàn bộ khoảng cách ở biển xe máy (2 dòng char_acc 0,846 vs 0,990 biển 1 dòng)
- ⚠️ NFR-A7 (E2E) = 0,5227 — đo trên ảnh crop (ngoài phân bố detector), là cận dưới bi quan
- ⬜ NFR-P2/P3 (webcam/video), A9, R5 **chưa đo**
- ⚠️ Chưa có tập test **xuyên bộ dữ liệu** ⇒ mAP lạc quan hơn khi triển khai
- ⚠️ Giấy phép một phần bộ dữ liệu **chưa rõ**
- ⚠️ Không có GPU CUDA — toàn bộ suy luận chạy CPU
- ⚠️ **FR-4.1 (Must) + FR-4.2 (Should) đưa ra khỏi phạm vi** — trang Tổng quan gỡ khỏi giao diện 2026-07-20 để thu gọn demo; `GET /api/statistics` **vẫn phục vụ và vẫn có kiểm thử**

---

### Khối 10 — Kết luận *(cao ~119 mm)*

**Tiêu đề khối:** `KẾT LUẬN` (T2)

**Nội dung — hai cột nhỏ song song** (T4)

| ✅ Đã làm được | ❌ Không tuyên bố |
|---|---|
| Hệ thống 5 tầng chạy được, kiểm chứng bằng HTTP thật | Không tạo state-of-the-art, và không đặt mục tiêu đó |
| Quy trình dữ liệu chống rò rỉ — bắt được **73 cặp** lỗi thật | Chưa phải sản phẩm triển khai được |
| Split-then-hstack + luật hậu xử lý theo vị trí, **104 unit test** | Chưa có con số OCR đầu–cuối |

**Bốn đóng góp** (T5, ô nền xanh nhạt)
1. Bộ luật sửa lỗi OCR **theo vị trí**, xây từ TT 79/2024
2. **Thiết kế phép đo** đóng góp của hậu xử lý — lưu `raw_ocr_text` **và** `plate_number` trên cùng bản ghi
3. Đánh giá **tách riêng** biển 1 dòng / 2 dòng, không che bằng số trung bình
4. Hệ thống hoàn chỉnh **chạy không cần GPU**

**Câu chốt** (T3, in đậm, căn giữa, đóng khung):
> **Charset OCR dùng đủ 36 ký tự A–Z + 0–9. Tập loại trừ đúng chỉ gồm 5 chữ I J O Q W — chữ R HỢP LỆ ở seri xe máy.**
> *Charset 20 chữ ⇒ mô hình không bao giờ đoán được R ⇒ sai hệ thống trên cả một lớp biển, và hậu xử lý không cứu được.*

---

## KHỐI F — Chân trang

**Vị trí:** dưới cùng, băng toàn chiều rộng · **Kích thước:** 741 × 60 mm · **Nền:** xám `#F1F5F9`

**Nội dung — ba vùng chia đều** (T7 — 20 pt)

| Vùng trái | Vùng giữa | Vùng phải |
|---|---|---|
| **Căn cứ pháp lý:** TT 79/2024/TT-BCA (sửa bởi TT 13/2025, TT 51/2025) · QCVN 08:2024/BCA | **Công nghệ:** YOLO11n · PaddleOCR · FastAPI · React + TypeScript · SQLite · Docker | **Tham khảo chính:** Laroca et al., VISAPP 2022 · Ultralytics YOLO11 · PaddleOCR |

**Góc phải dưới cùng:** mã QR (cạnh 40 mm) trỏ tới repo hoặc bản PDF quyển đồ án, kèm nhãn nhỏ "Mã nguồn & tài liệu".

---

## 6. Danh sách hình cần chuẩn bị

| # | Hình | Vị trí | Nguồn | Trạng thái |
|---|---|---|---|:--:|
| 1 | Biểu đồ 2 cột 94,3% / 45,7% | Khối H | Vẽ mới (số từ Laroca 2022) | ⬜ Cần vẽ |
| 2 | 3 ảnh biển thật + nhãn AR | Khối 1 | Cắt từ tập dữ liệu | ⬜ Cần cắt |
| 3 | **Sơ đồ kiến trúc 5 tầng (SVG)** | Khối 4 | Render mermaid từ `system-architecture.md` §2 | ⬜ Cần render |
| 4 | **Sơ đồ pipeline AI (SVG)** | Khối 5 | Render mermaid từ `system-architecture.md` §3 | ⬜ Cần render |
| 5 | ⭐ **Minh hoạ split-then-hstack 4 bước** | Khối 6 | Xuất ảnh trung gian từ `ai/inference/two_line.py` | 🔴 **Còn thiếu — ưu tiên cao nhất** |
| 6 | Biểu đồ phân bố AR + đường ngưỡng 2,5 | Khối 6 | `datasets/statistics/` | ⬜ Cần vẽ lại cho poster |
| 7 | Biểu đồ ngân sách độ trễ 405 ms | Khối 7 | Vẽ mới | ⬜ Cần vẽ |
| 8 | `image-detection.png` | Khối 8 | `docs/screenshots/` | ⚠️ Có — **chụp lại** (ảnh cũ: sidebar 5 mục) |
| 9 | `video-detection.png` | Khối 8 | `docs/screenshots/` | ⚠️ Có — **chụp lại** (ảnh cũ: sidebar 5 mục) |
| 10 | `history.png` | Khối 8 | `docs/screenshots/` | ⚠️ Có — **chụp lại** (ảnh cũ: sidebar 5 mục) |
| 11 | Logo trường (+ logo khoa) | Khối 0 | Xin từ khoa | ⬜ Cần lấy |
| 12 | Mã QR repo / PDF | Khối F | Sinh sau khi chốt link | ⬜ Cần sinh |

**Yêu cầu chung cho hình**
- Sơ đồ → **SVG hoặc PDF vector**. Bitmap phóng to sẽ vỡ ở 300 DPI.
- Ảnh chụp màn hình → độ phân giải gốc, **tối thiểu 2× kích thước in**.
- Biểu đồ tự vẽ → chữ tối thiểu **T6 = 22 pt** ở kích thước in cuối cùng, không phải kích thước lúc thiết kế.
- Mọi hình có số liệu → ghi **nguồn** ngay dưới hình (T7).

---

## 7. Kiểm tra trước khi in

**Kiểm tra 30 giây** — nhờ một người **chưa biết gì về đồ án** đứng cách 1,5 m trong đúng 30 giây, rồi hỏi ba câu:
1. Đề tài này về cái gì?
2. Vấn đề khó nhất là gì?
3. Hệ thống gồm những khối nào?

Nếu họ trả lời được cả ba ⇒ bố cục đạt. Không trả lời được câu nào ⇒ khối tương ứng cần phóng to hoặc rút gọn chữ.

**Checklist kỹ thuật**
- [ ] Không có chữ nào dưới **18 pt**
- [ ] Không có chữ nào lọt ra ngoài lề an toàn 50 mm
- [ ] Mọi sơ đồ là **vector**, mọi ảnh chụp ≥ 2× kích thước in
- [ ] **Ảnh chụp màn hình ở Khối 8 đã chụp lại** trên giao diện **3 trang** hiện hành (sidebar 3 mục, trang chủ là Nhận dạng ảnh, không còn Tổng quan) — không dùng bản cũ chụp lúc sidebar còn 5 mục, không dùng `dashboard.png`
- [ ] **Dấu tiếng Việt hiển thị đúng** ở mọi cỡ chữ — kiểm riêng các chữ "ữ", "ượ", "ỹ", "ặ"
- [ ] In thử **A3 đen trắng** — vẫn phân biệt được các khối?
- [ ] In thử **A4 màu** — kiểm màu có lệch so với màn hình không
- [ ] Chú thích nguồn số liệu Brazil ở Khối H **còn nguyên**, chưa bị cắt để lấy chỗ
- [ ] Ba bảng có ô trống (Khối 7) — ô ghi `—`, **không** ghi số phỏng đoán
- [ ] Xuất **PDF/X-1a**, nhúng hết font, không dùng font hệ thống
- [ ] Không gian âm ≥ 25% — nếu thấy chật thì **cắt nội dung**, đừng thu nhỏ chữ

**Ba lỗi phổ biến nhất cần tránh**
1. **Nhồi chữ.** Poster không phải quyển đồ án thu nhỏ. Chỗ nào phải thu chữ xuống dưới 24 pt mới vừa là chỗ có nội dung thừa.
2. **Sơ đồ chữ quá nhỏ.** Sơ đồ mermaid xuất mặc định có chữ khoảng 14 pt — đọc được trên màn hình, không đọc được trên poster. Phải chỉnh trước khi render.
3. **Bỏ mục Hạn chế.** Cám dỗ lớn khi hết chỗ. Nhưng một poster toàn kết quả đẹp mà không có ranh giới sẽ bị hỏi đúng vào chỗ đó.
