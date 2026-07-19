# Khung slide bảo vệ đồ án tốt nghiệp

**Đề tài:** Xây dựng hệ thống nhận dạng biển số xe Việt Nam ứng dụng Trí tuệ nhân tạo
**Thuộc:** Phase 10 — chuẩn bị bảo vệ · **Ngày lập:** 19/07/2026
**Thời lượng:** 15 phút trình bày + hỏi đáp · **Số slide:** 21

---

## Cách dùng tài liệu này

Mỗi slide gồm bốn phần:

| Phần | Vai trò |
|---|---|
| **Nội dung trên slide** | Gạch đầu dòng ngắn — đây là thứ *chiếu lên*, không phải thứ *nói ra*. Không viết đoạn văn lên slide. |
| **Hình / Bảng** | Tài nguyên cần chuẩn bị trước. Ghi rõ file nào, còn thiếu thì đánh dấu. |
| **Speaker notes** | Lời nói gợi ý, 30–60 giây. Không đọc lại slide. |
| **Thời lượng** | Ngân sách giây. Tổng phải ≤ 900 giây. |

### Ngân sách thời gian

| Khối | Slide | Thời lượng |
|---|---|---:|
| Mở đầu — vì sao làm | S1–S3 | 110 s |
| Nền tảng — biết gì trước khi làm | S4–S6 | 150 s |
| Thiết kế — làm thế nào | S7–S9 | 135 s |
| Dữ liệu và huấn luyện | S10–S12 | 150 s |
| Đóng góp kỹ thuật lõi | S13–S15 | 165 s |
| Kết quả và hệ thống | S16–S17 | 90 s |
| Kết | S18–S21 | 100 s |
| **Tổng** | | **900 s = 15 phút** |

### Ba nguyên tắc trình bày

1. **Không đọc slide.** Slide là chỗ dựa thị giác; lời nói mang nội dung.
2. **Chỗ nào chưa đo thì nói thẳng là chưa đo; chỗ nào không đạt thì nói thẳng không đạt.** OCR biển 2 dòng (S15) KHÔNG đạt chỉ tiêu — đó là kết quả thật, trình bày trung thực kèm phân tích nguyên nhân, không tô hồng.
3. **Mọi con số hiệu năng đọc kèm phần cứng.** Nói "mAP 0,983" phải kèm "trên tập test v3, imgsz 640, `best.pt`".

---

## Bảng trạng thái dữ liệu của bộ slide

**Đọc bảng này trước khi dựng slide thật.** Slide nào chưa có dữ liệu thì không được điền số phỏng đoán.

| Slide | Trạng thái | Còn thiếu gì | Nguồn số |
|---|---|---|---|
| S1–S11 | ✅ Đủ dữ liệu | — | — |
| **S12 — Kết quả detection** | ✅ **ĐÃ ĐIỀN** | mAP50 0,983 / mAP50-95 0,783 / P 0,984 / R 0,971, tách 1 dòng / 2 dòng | `05-tables.md §T5.5a/b` (`best.pt`, test v3) |
| S13 | ⚠️ Một phần | Ảnh minh hoạ split-then-hstack (chưa render) | Phase 4 — xuất ảnh trung gian từ `two_line.py` |
| **S15 — Đóng góp hậu xử lý** | ✅ **ĐÃ ĐIỀN** | A4–A7, tách layout, A6−A5 = +4,57 điểm | `05-tables.md §T5.6a–e` (2.801 biển) |
| S16 | ✅ Có ảnh | Đã có 5 ảnh trong `docs/screenshots/` | — |
| **S17 — Hiệu năng CPU** | ✅ **ĐÃ ĐIỀN** | p50/p95/p99 độ trễ, phân rã bước | `07-benchmark-p1-resolved.json`, `05-tables.md §T5.7` |
| S18–S21 | ✅ Đủ dữ liệu | — | — |

> **Nguyên tắc trình bày số:** S12/S17 đạt chỉ tiêu — trình bày thẳng. S15 (OCR) **không đạt** — trình bày trung thực kèm phân tích: toàn bộ khoảng cách nằm ở biển 2 dòng, không tô hồng. NFR-P2/P3/A9/R5 **chưa đo** — nói thẳng là chưa đo.

---

# PHẦN A — MỞ ĐẦU

## S1 — Bìa

**Nội dung trên slide**

- Tên đề tài: **Xây dựng hệ thống nhận dạng biển số xe Việt Nam ứng dụng Trí tuệ nhân tạo**
- Sinh viên thực hiện · Mã số sinh viên · Lớp
- Giảng viên hướng dẫn
- Trường / Khoa · Tháng 7 năm 2026

**Hình / Bảng**

- Logo trường (góc trên trái)
- Một ảnh nền mờ: khung hình giao thông có biển số đã được khoanh hộp — lấy từ đầu ra thật của hệ thống, **không** dùng ảnh stock. Nguồn: chạy `/image` rồi chụp vùng kết quả.

**Speaker notes** *(20 s)*

> Em xin kính chào thầy cô trong hội đồng. Em là [tên], sinh viên lớp [lớp]. Hôm nay em xin trình bày đồ án tốt nghiệp: Xây dựng hệ thống nhận dạng biển số xe Việt Nam ứng dụng Trí tuệ nhân tạo, dưới sự hướng dẫn của thầy/cô [tên]. Phần trình bày của em gồm bốn khối: vì sao làm đề tài này, thiết kế hệ thống, hai đóng góp kỹ thuật chính, và trung thực về những gì em chưa làm xong.

---

## S2 — Đặt vấn đề: một con số

**Nội dung trên slide**

- Việt Nam: **~77 triệu xe máy** đăng ký (9/2024), chiếm **85–90%** lưu lượng đường bộ
- Hệ thống ALPR thương mại **OpenALPR**, cùng một tập kiểm thử cân bằng 4.000 + 4.000 ảnh:

| Loại xe | Bố cục biển | Tỉ lệ đọc đúng |
|---|---|---:|
| Ô tô | 1 dòng | **94,3%** |
| Xe máy | **2 dòng** | **45,7%** |
| | **Chênh lệch** | **48,6 điểm** |

- Cùng một hệ thống. Cùng một phép đo. **Chỉ khác bố cục biển.**
- ⚠️ Số đo trên RodoSol-ALPR (Brazil) — dẫn làm *analogue* về độ khó, **không phải số liệu Việt Nam**

**Hình / Bảng**

- Biểu đồ cột **2 cột duy nhất**: 94,3 và 45,7. Cột thứ hai tô đỏ. Không thêm gì khác — hình càng trơ càng mạnh.
- Nguồn ghi nhỏ dưới hình: *Laroca et al., VISAPP 2022 (arXiv 2201.00267)*

**Speaker notes** *(50 s)*

> Em xin bắt đầu bằng một con số. OpenALPR là một hệ thống nhận dạng biển số thương mại đã trưởng thành. Khi được đo trên một tập kiểm thử cân bằng có chủ ý — bốn nghìn ảnh ô tô biển một dòng và bốn nghìn ảnh xe máy biển hai dòng — nó đọc đúng 94,3% với ô tô, nhưng chỉ 45,7% với xe máy. Chênh gần 49 điểm phần trăm, trên cùng một hệ thống, cùng một điều kiện đo, không có biến số nào khác thay đổi ngoài bố cục biển.
>
> Em phải nói rõ ngay: con số này đo trên dữ liệu Brazil, không phải Việt Nam. Em dẫn nó như một *analogue* về độ khó. Nhưng ý nghĩa với Việt Nam thì rất trực tiếp: ở nước ta xe máy chiếm 85 đến 90% lưu lượng. Tức là chỗ mà các hệ thống nhập khẩu hỏng nặng nhất, lại chính là chỗ Việt Nam cần nhất.

---

## S3 — Mục tiêu và phạm vi

**Nội dung trên slide**

**Mục tiêu tổng quát:** hệ thống ALPR hoàn chỉnh cho biển số Việt Nam — hỗ trợ **cả biển 1 dòng và 2 dòng**, suy luận **hoàn toàn trên CPU** (mặc định, không phải chế độ dự phòng)

**Chỉ tiêu đo được — trích 5 chỉ tiêu chính:**

| Mã | Chỉ tiêu | Mục tiêu | Ngưỡng tối thiểu |
|---|---|:--:|:--:|
| NFR-A1 | mAP@0.5 phát hiện | ≥ 0,90 | ≥ 0,85 |
| NFR-A2 | mAP@0.5:0.95 | ≥ 0,65 | ≥ 0,55 |
| NFR-A6 | Chính xác biển **sau** hậu xử lý | ≥ 0,90 | ≥ 0,85 |
| NFR-A7 | **Chính xác E2E toàn trình** | **≥ 0,88** | ≥ 0,82 |
| NFR-P1 | Độ trễ 1 ảnh, p95, CPU | ≤ 800 ms | ≤ 1.200 ms |

**Cố ý ngoài phạm vi:** phân loại loại xe · tracking đa khung · tích hợp barie · xác thực người dùng · huấn luyện OCR từ đầu

**Hình / Bảng**

- Bảng chỉ tiêu như trên
- Dải "trong phạm vi / ngoài phạm vi" hai màu, nằm ngang dưới cùng

**Speaker notes** *(40 s)*

> Mục tiêu của em là một hệ thống hoàn chỉnh chứ không phải một notebook demo: có mô hình tự huấn luyện, backend, giao diện, cơ sở dữ liệu và tài liệu. Hai ràng buộc em tuyên bố ngay từ đầu: phải xử lý được cả biển một dòng lẫn hai dòng, và phải chạy được hoàn toàn trên CPU — vì máy triển khai không có GPU.
>
> Điều em muốn nhấn ở slide này là các chỉ tiêu đều **đo được bằng số** và được chốt **trước khi** bắt tay làm, mỗi chỉ tiêu có hai mức: mục tiêu và ngưỡng tối thiểu. Và em cũng ghi rõ những gì cố ý không làm — danh sách ngoài phạm vi này là ranh giới cứng, nó bảo vệ đồ án khỏi phình phạm vi.

---

# PHẦN B — NỀN TẢNG

## S4 — Tổng quan các hướng tiếp cận

**Nội dung trên slide**

| Thế hệ | Cách làm | Điểm gãy |
|---|---|---|
| Cổ điển | Sobel / morphology / contour + template matching | Vỡ khi ánh sáng, góc chụp đổi |
| Hai giai đoạn | CNN phát hiện → CRNN/CTC đọc chuỗi | **Giả định 1 dòng nằm trong hàm mất mát** |
| Một giai đoạn | YOLO phát hiện trực tiếp ký tự | Cần nhãn ký tự — thứ Việt Nam gần như không có công khai |
| End-to-end | Transformer / attention đọc thẳng | Đói dữ liệu, nặng, không hợp CPU |

→ **Lựa chọn:** hai giai đoạn — **YOLO11n** phát hiện vùng biển + **PaddleOCR** đọc ký tự + **khối hậu xử lý theo luật Việt Nam**

- Lý do: chỉ cần nhãn vùng biển (có sẵn), thay được từng khối, chạy được trên CPU

**Hình / Bảng**

- Sơ đồ 4 nhánh, nhánh "hai giai đoạn" tô đậm và có mũi tên dẫn xuống lựa chọn

**Speaker notes** *(45 s)*

> Em khảo sát bốn thế hệ tiếp cận. Hướng cổ điển dùng xử lý ảnh thuần, vỡ ngay khi điều kiện chụp đổi. Hướng end-to-end bằng transformer thì mạnh nhưng đói dữ liệu và quá nặng cho CPU. Hướng một giai đoạn — dùng YOLO phát hiện thẳng từng ký tự — về nguyên tắc rất gọn, nhưng nó đòi nhãn ở mức ký tự, mà dữ liệu biển số Việt Nam công khai gần như không có nhãn đó.
>
> Em chọn kiến trúc hai giai đoạn: YOLO11 tìm vùng biển, PaddleOCR đọc ký tự, rồi một khối hậu xử lý riêng áp luật biển số Việt Nam. Ba lý do: nó chỉ cần loại nhãn em thực sự có, từng khối thay thế được độc lập, và nó vừa ngân sách CPU. Em cũng ghi nhận sẵn điểm yếu của hướng này — CRNN giả định văn bản nằm trên một dòng — và đó chính là vấn đề em xử lý ở slide 13.

---

## S5 — Đặc thù biển số Việt Nam

**Nội dung trên slide**

**Ba đặc thù không có ở bộ quy tắc nước ngoài nào:**

1. **Bố cục tách bạch theo tỉ lệ khung hình** (QCVN 08:2024/BCA)

| Loại biển | Kích thước | Tỉ lệ | Số dòng |
|---|---|:--:|:--:|
| Ô tô biển dài | 110 × 520 mm | **4,727** | 1 dòng |
| Ô tô biển ngắn | 165 × 330 mm | **2,000** | 2 dòng |
| Xe mô tô | 140 × 190 mm | **1,357** | 2 dòng |

→ Khoảng trống **(2,000 ; 4,727)** không có loại biển nào rơi vào ⇒ cơ sở hình học để phân loại số dòng

2. **Tập ký tự seri phụ thuộc VỊ TRÍ** — vị trí 1 có `G` không có `R`; vị trí 2 của xe máy có `R` không có `G`
3. **Mã địa phương là tập hữu hạn có lỗ hổng** — 89 giá trị trong dải 11–99, chỉ **81 mã dùng thật**; 8 mã (13, 42, 44, 45, 46, 87, 91, 96) chưa gán cho địa phương nào

- Màu nền mã hoá loại phương tiện: trắng / vàng / xanh / đỏ → lý do **không** xáo trộn mạnh sắc độ khi augmentation

**Hình / Bảng**

- Ảnh 3 biển thật cạnh nhau, cùng tỉ lệ pixel, có ghi AR đo được dưới mỗi ảnh
- Bảng kích thước như trên

**Speaker notes** *(50 s)*

> Ba đặc thù của biển số Việt Nam có hệ quả kỹ thuật trực tiếp.
>
> Thứ nhất, theo quy chuẩn QCVN 08 năm 2024, ba loại biển có tỉ lệ khung hình lần lượt là 4,73 — 2,00 — và 1,36. Không có loại biển nào rơi vào khoảng giữa 2 và 4,73. Khoảng trống rộng đó cho em một cơ sở hình học đáng tin để phân loại một dòng hay hai dòng, và em sẽ quay lại nó ở slide 13.
>
> Thứ hai — và đây là chỗ em suýt sai — tập chữ cái seri **phụ thuộc vị trí**, không phải một danh sách phẳng.
>
> Thứ ba, mã tỉnh không phải hai chữ số bất kỳ. Dải 11 đến 99 có 89 giá trị nhưng chỉ 81 mã đang dùng. Một biểu thức chính quy viết `\d{2}` sẽ cho qua 8 chuỗi không bao giờ tồn tại.

---

## S6 — Căn cứ pháp lý: một phát hiện

**Nội dung trên slide**

> Đề bài dẫn **Thông tư 24/2023/TT-BCA** làm căn cứ pháp lý.
> Đối chiếu nguồn gốc ở Phase 1: văn bản này **đã hết hiệu lực từ 01/01/2025**.

**Chuỗi văn bản hiện hành đang dùng:**

| Văn bản | Hiệu lực | Nội dung với đồ án |
|---|---|---|
| ~~TT 24/2023/TT-BCA~~ | ❌ hết hiệu lực 01/01/2025 | Văn bản đề bài dẫn |
| **TT 79/2024/TT-BCA** | 01/01/2025 | Cấu trúc biển, seri, màu sắc |
| TT 13/2025/TT-BCA | 2025 | Sửa đổi TT 79/2024 |
| **TT 51/2025/TT-BCA** | 01/7/2025 | **Thay toàn bộ phụ lục mã tỉnh** — còn 34 tỉnh/thành sau sáp nhập |
| TT 81/2024 → **QCVN 08:2024/BCA** | 01/01/2025 | Kích thước vật lý |

**Hệ quả thiết kế — điểm quan trọng nhất của slide này:**

- Pháp lý **thay đổi được** ⇒ tri thức pháp lý phải nằm **tách khỏi mô hình**
- Toàn bộ luật Việt Nam gom vào **một file**: `ai/inference/plate_rules.py`
- TT 51/2025 đổi phụ lục mã tỉnh giữa lúc làm đồ án → chỉ sửa **một bảng hằng số**, không huấn luyện lại gì

**Hình / Bảng**

- Trục thời gian ngang: 2023 → 2024 → 2025, có dấu ✗ đỏ trên TT 24/2023 tại mốc 01/01/2025
- Mũi tên từ trục thời gian trỏ vào một khối chữ nhật duy nhất ghi `plate_rules.py`

**Speaker notes** *(55 s)*

> Slide này em muốn kể một chuyện xảy ra trong lúc làm. Đề bài dẫn Thông tư 24 năm 2023 làm căn cứ pháp lý. Khi em đối chiếu nguồn pháp lý gốc ở giai đoạn nghiên cứu, em phát hiện văn bản đó đã hết hiệu lực từ đầu năm 2025. Em đã chuyển toàn bộ căn cứ sang Thông tư 79 năm 2024, cùng hai thông tư sửa đổi và quy chuẩn QCVN 08.
>
> Em không nêu chuyện này để nói đề bài sai. Em nêu vì nó buộc em phải trả lời một câu hỏi thiết kế: nếu văn bản pháp lý thay đổi được, thì tri thức pháp lý không được phép nằm bên trong mô hình. Và điều đó đã xảy ra lần nữa: Thông tư 51 năm 2025 thay toàn bộ phụ lục mã tỉnh sau sáp nhập, còn 34 tỉnh thành. Vì em đã gom toàn bộ luật vào đúng một file, em chỉ phải sửa một bảng hằng số — không phải huấn luyện lại bất cứ thứ gì.

---

# PHẦN C — THIẾT KẾ

## S7 — Kiến trúc hệ thống

**Nội dung trên slide**

**5 tầng:**

| Tầng | Công nghệ | Vai trò |
|---|---|---|
| L1 — Trình bày | React 18 + Vite + TypeScript strict + Tailwind | 5 trang |
| L2 — API | FastAPI + Swagger | 10 endpoint |
| L3 — Nghiệp vụ | Detection / Video / History / Statistics / Storage Service | Điều phối |
| **L4 — AI** | **Python thuần — cấm import FastAPI** | YOLO11 + PaddleOCR + Normalizer |
| L5 — Dữ liệu | SQLite + SQLAlchemy + Alembic + kho tệp | `detection_history` 18 cột · `detection_job` 11 cột |

**Đã kiểm chứng bằng chạy thật:** 10 endpoint phản hồi đúng qua HTTP · Alembic migrate xong · frontend typecheck sạch, lint sạch, build thành công, 10 endpoint khớp kiểu TypeScript từng trường

**Hình / Bảng**

- **Sơ đồ kiến trúc 5 tầng** — render từ mermaid trong `docs/architecture/system-architecture.md` mục 2. Tầng AI (L4) tô **vàng**, và phải thấy rõ **không có mũi tên nào đi lên từ L4**.

**Speaker notes** *(45 s)*

> Hệ thống chia làm năm tầng. Tầng trình bày là React với TypeScript ở chế độ strict. Tầng API là FastAPI, mười endpoint. Tầng nghiệp vụ gồm năm service. Tầng dữ liệu là SQLite qua SQLAlchemy với Alembic migration.
>
> Khối màu vàng ở giữa là tầng AI, và nó là điểm em muốn nhấn ở slide sau.
>
> Về trạng thái: cả backend lẫn frontend đều đã chạy và được kiểm chứng bằng gọi HTTP thật, không phải chỉ biên dịch được. Mười endpoint phản hồi đúng, migration chạy xong, và frontend khớp kiểu dữ liệu với API tới từng trường.

---

## S8 — Nguyên tắc: tách tầng AI khỏi tầng API

**Nội dung trên slide**

**Ràng buộc:** `ai/inference/` là Python thuần — **cấm import FastAPI hoặc Pydantic**

```bash
# Phép kiểm chứng — phải ra rỗng
grep -r "fastapi\|pydantic" ai/inference/
```

Trong sơ đồ kiến trúc: **khối AI không có mũi tên nào đi lên**. Nó không biết gì về HTTP, về CSDL, hay về ai gọi nó.

**Ba lợi ích cụ thể — không phải lý thuyết:**

| Lợi ích | Bằng chứng |
|---|---|
| Kiểm thử độc lập | **104 unit test** tầng AI chạy không cần dựng server |
| Tái dùng | Cùng một pipeline dùng trong script huấn luyện, đánh giá và API |
| **Thay được engine** | Nếu benchmark cho thấy EasyOCR tốt hơn → thay `PlateRecognizer`, **không đụng backend** |

**Cái giá phải trả:** thêm một lớp gián tiếp, phải định nghĩa kiểu trung gian riêng (`ai/inference/types.py`) thay vì dùng thẳng Pydantic model

**Hình / Bảng**

- Sơ đồ đơn giản hoá: 3 hộp xếp dọc (API → Service → **AI**), mũi tên **chỉ đi xuống**. Vẽ thêm một mũi tên đi lên bị gạch chéo đỏ.

**Speaker notes** *(45 s)*

> Nguyên tắc kiến trúc quan trọng nhất của em là tầng AI không được biết gì về tầng web. Cụ thể: thư mục `ai/inference` là Python thuần, cấm import FastAPI hay Pydantic. Đây không phải một quy ước ghi trong tài liệu rồi quên — nó kiểm chứng được bằng đúng một lệnh grep, phải ra rỗng.
>
> Vì sao đáng công như vậy? Ba lý do đo được. Một, một trăm lẻ bốn unit test của tầng AI chạy mà không cần dựng server. Hai, cùng một pipeline đó được dùng lại trong script huấn luyện và script đánh giá. Ba — và đây là lý do thật — nếu sau này em benchmark ra rằng EasyOCR đọc tốt hơn PaddleOCR, em thay đúng một lớp, không phải sửa dòng nào ở backend.
>
> Cái giá là thêm một lớp gián tiếp và phải tự định nghĩa kiểu dữ liệu trung gian. Em thấy đó là cái giá đáng trả.

---

## S9 — Pipeline AI

**Nội dung trên slide**

```
Ảnh / Khung hình
   → Tiền xử lý
   → YOLO11n phát hiện biển  ──── không thấy biển → trả rỗng, HTTP 200 (KHÔNG phải lỗi)
   → Cắt vùng biển
   → Phân loại số dòng (ngưỡng AR = 2,5)
        ├─ 1 dòng → PaddleOCR
        └─ 2 dòng → RECTIFY → tách trên/dưới → ghép ngang → PaddleOCR
   → Chuẩn hoá + sửa lỗi theo VỊ TRÍ (plate_rules.py)
   → Kiểm tra hợp lệ định dạng VN
        ├─ hợp lệ  → lưu
        └─ không   → lưu + đánh dấu is_valid_format = False (KHÔNG vứt bỏ)
   → Ghi CSDL: LƯU CẢ raw_ocr_text LẪN plate_number
```

**Hai quyết định đáng chú ý ở slide này:**
- Kết quả rỗng ⇒ **HTTP 200**, không phải lỗi — hệ thống đang chạy đúng
- Biển không khớp định dạng ⇒ **vẫn lưu**, chỉ đánh dấu — đây là nguồn phân tích lỗi cho chương Đánh giá

**Hình / Bảng**

- **Sơ đồ luồng** — render từ mermaid `system-architecture.md` mục 3. Nhánh 2 dòng tô **đỏ**.

**Speaker notes** *(45 s)*

> Đây là luồng xử lý. Ảnh vào, YOLO11 tìm vùng biển, cắt ra, rồi phân nhánh theo số dòng: biển một dòng đưa thẳng vào OCR, biển hai dòng đi qua nhánh màu đỏ mà em sẽ nói kỹ ở slide 13. Kết quả OCR đi qua khối chuẩn hoá theo luật Việt Nam rồi mới ghi cơ sở dữ liệu.
>
> Hai quyết định nhỏ nhưng em muốn nêu. Thứ nhất: ảnh xử lý xong mà không có biển số thì trả HTTP 200 với danh sách rỗng, không trả lỗi — vì hệ thống đang chạy đúng, báo lỗi ở đây sẽ đẩy người dùng đi sửa một thứ không hỏng. Thứ hai: biển đọc ra không khớp định dạng Việt Nam thì vẫn được lưu, chỉ bị đánh dấu cờ. Em không im lặng vứt dữ liệu — chính những ca đó là nguyên liệu phân tích lỗi.
>
> Và ở bước ghi cơ sở dữ liệu, em lưu **cả hai** chuỗi: chuỗi OCR thô và chuỗi sau chuẩn hoá. Slide 15 sẽ giải thích vì sao.

---

# PHẦN D — DỮ LIỆU VÀ HUẤN LUYỆN

## S10 — Bộ dữ liệu

**Nội dung trên slide**

**Quy mô hiện tại:** 4.578 ảnh · 5.200 box · 1 lớp `license_plate`

| Tập | Ảnh | Tỉ lệ | Tỉ lệ biển 2 dòng |
|---|---:|---:|---:|
| Train | 3.203 | 69,97% | 65,56% |
| Val | 917 | 20,03% | 65,54% |
| Test | 458 | 10,00% | 65,50% |

→ Lệch tỉ lệ 2 dòng giữa 3 tập tối đa **0,06 điểm phần trăm** (phân tầng, seed 42)

**Chống rò rỉ — và một phát hiện:**
- Perceptual hash 64-bit, ngưỡng Hamming ≤ 5, multi-index hashing **chính xác** (không bỏ sót cặp nào) → **193 cặp / 144 nhóm**
- Chia theo **nhóm**, không theo ảnh · sau khi chia đọc lại kết quả kiểm tra độc lập, vi phạm ⇒ trả mã lỗi
- 🔴 **73 / 193 cặp trùng nằm vắt qua ranh giới train↔val của chính bản chia gốc tác giả** ⇒ em **vứt bỏ bản chia gốc**, chia lại từ đầu

**Trạng thái và rủi ro — nói thẳng:**
- 🔄 Đang mở rộng lên **~21.000 ảnh** từ 8 bộ Roboflow, trong đó **2 bộ có nhãn ký tự**
- ⚠️ Bộ chính (HuggingFace) **không ghi rõ giấy phép** — rủi ro pháp lý còn treo, đã ghi nhận
- ⚠️ Bộ VNLP 37.300 ảnh chốt ở Phase 1 **tải không được** (HTTP 401, chuyển gated) ⇒ quy mô thực chỉ còn **12,3%** kế hoạch

**Hình / Bảng**

- Bảng chia tập như trên
- Biểu đồ phân bố tỉ lệ khung hình (AR) của 5.200 box — **phải thấy rõ hai đỉnh và vùng trũng ở 2,2–2,6**. Nguồn: `datasets/statistics/`. Dùng lại ở S13.

**Speaker notes** *(55 s)*

> Bộ dữ liệu hiện có 4.578 ảnh với 5.200 hộp nhãn, chia 70-20-10 và phân tầng theo số dòng biển — lệch tối đa 0,06 điểm phần trăm giữa ba tập.
>
> Phần em muốn nhấn là chống rò rỉ. Em không chia theo ảnh mà chia theo nhóm ảnh gần trùng: chạy perceptual hash 64 bit trên toàn bộ, ngưỡng Hamming 5, tìm được 193 cặp gom thành 144 nhóm, mỗi nhóm là một đơn vị không tách được. Sau khi chia xong, script đọc lại kết quả cuối và kiểm tra lại độc lập.
>
> Và bước này bắt được một lỗi thật: 73 trong 193 cặp trùng nằm vắt qua ranh giới train và val của chính bản chia mà tác giả bộ dữ liệu cung cấp sẵn — có những cặp giống hệt nhau, Hamming bằng 0. Ai dùng thẳng bản chia đó đều đang đo trên một tập validation đã ô nhiễm. Đó là căn cứ để em vứt bỏ bản chia gốc và chia lại từ đầu.
>
> Hai điều em phải nói thẳng: bộ chính không ghi rõ giấy phép, và bộ 37.300 ảnh em chốt ban đầu tải không được nên quy mô thực chỉ còn 12,3% kế hoạch. Em đang mở rộng lên khoảng 21.000 ảnh, trong đó hai bộ có nhãn ký tự.

---

## S11 — Huấn luyện: cấu hình và lý do

**Nội dung trên slide**

**Chọn YOLO11n — loại bằng hai bước:**
1. Máy triển khai không GPU ⇒ bắt buộc có **số liệu tốc độ CPU chính thức** → YOLOv9/v10/v12/v13 bị loại vì thiếu căn cứ, không phải vì kém
2. YOLO11n vượt YOLOv8n **đồng thời cả hai chiều**: mAP 39,5 vs 37,3 · CPU 56,1 ms vs 80,4 ms

**Cấu hình lần chạy CPU** (đã hạ để khả thi): `imgsz 416` (chuẩn: 640) · `batch 8` · `40 epoch` · AdamW `lr0 0,001` · `workers 2` · `amp` tắt · `seed 42` · `deterministic`

**Bốn thay đổi có chủ đích so với mặc định Ultralytics:**

| Tham số | Mặc định | Của em | Lý do |
|---|:--:|:--:|---|
| `box` | 7,5 | **8,0** | Đầu ra detector do **một mô hình khác** (OCR) tiêu thụ — hộp lệch vài pixel làm mất cạnh ký tự |
| `fliplr` | 0,5 | **0,0 — chặn cứng bằng `ValueError`** | Lật ngang biển = **soi gương ký tự** = vật thể không tồn tại |
| `hsv_h` | 0,015 | giữ, **có lý do** | Màu nền biển **mang ngữ nghĩa** (loại phương tiện) |
| `lr0` | — | **0,001 cố tình thấp** | LR cao trên trọng số pretrain ⇒ catastrophic forgetting |

**Vì sao CPU:** máy phát triển Intel Core i5-14600K (14 nhân / 20 luồng), đồ hoạ tích hợp UHD 770 — **không có CUDA**. Đo thực: **~230 s/epoch** ⇒ 40 epoch ≈ 2,5 giờ.

**Hình / Bảng**

- Bảng bốn thay đổi như trên
- Ảnh minh hoạ nhỏ: một biển số và ảnh soi gương của nó, có dấu ✗ đỏ (minh hoạ `fliplr`)

**Speaker notes** *(50 s)*

> Em chọn YOLO11 biến thể nano bằng hai bước loại. Bước một: vì máy triển khai không có GPU nên tiêu chí bắt buộc là mô hình phải có số liệu tốc độ CPU chính thức. YOLOv9, v10, v12, v13 đều không có nên bị loại — vì thiếu căn cứ đánh giá, không phải vì chúng kém. Bước hai: YOLO11n vượt YOLOv8n đồng thời cả về độ chính xác lẫn tốc độ CPU, nên không có lý do chọn v8.
>
> Về siêu tham số, em phải trung thực: em không chạy tìm kiếm tự động, không có ngân sách tính toán cho việc đó trên CPU. Em lấy mặc định Ultralytics và chỉ đổi những chỗ có lý do đặc thù bài toán.
>
> Em xin nói một chỗ: `fliplr`. Mặc định của Ultralytics là 0,5, tức một nửa số ảnh huấn luyện bị lật ngang. Nhưng lật ngang một biển số là soi gương các ký tự trên đó — chữ A soi gương không phải chữ A. Đó không phải một góc nhìn khác của cùng vật thể, mà là một vật thể không tồn tại. Nguy hiểm ở chỗ sai lầm này **không** làm hỏng quá trình huấn luyện: loss vẫn giảm, đường cong vẫn đẹp, chỉ là mô hình kém hơn mức đáng lẽ đạt được. Vì vậy em chặn nó ở tầng mã bằng một `ValueError`, chứ không ghi vào comment — một quy ước trong comment sớm muộn cũng bị vi phạm.

---

## S12 — Kết quả detection ✅ ĐÃ CÓ SỐ CÔNG BỐ

> **Đo trên `models/best.pt` (YOLO11n, imgsz 640, split v3), tập TEST 1.514 ảnh.**

**Nội dung trên slide**

**Trạng thái: mô hình chính thức `best.pt` đã huấn luyện xong (20 epoch, epoch tốt nhất = 20)**

**Bảng công bố — đo trên tập TEST v3 (1.514 ảnh), tách theo layout:**

| Nhóm | N đối tượng | P | R | F1 | mAP50 | mAP50-95 |
|---|---:|---:|---:|---:|---:|---:|
| Biển 1 dòng | 286 | 0,986 | 0,990 | 0,988 | **0,988** | 0,753 |
| Biển 2 dòng | 1.325 | 0,973 | 0,969 | 0,971 | **0,968** | 0,765 |
| **TẤT CẢ** | **1.611** | **0,984** | **0,971** | **0,977** | **0,983** | **0,783** |
| *Chỉ tiêu (NFR-A1/A2/A3)* | | *≥0,92* | *≥0,90* | | *≥0,90* | *≥0,65* |

**Bốn chỉ tiêu detection đều ĐẠT.** Chênh layout (A8) chỉ **2,09 điểm** mAP50 ⇒ **detection ít nhạy với layout**.

**Ba điều đọc được:**
- ✅ **Cả bốn chỉ tiêu NFR-A1/A2/A3 đều vượt mục tiêu** trên tập test độc lập, đo ở đúng imgsz 640.
- ✅ Đo trên **split v3 đã khử trùng lặp ở ngưỡng 10** ⇒ mAP không còn bị rò rỉ tên-tệp thổi phồng như baseline v1 (0,9933).
- ⚠️ Điểm yếu biển 2 dòng **KHÔNG** nằm ở detection (chênh 2,09 điểm) mà ở tầng **OCR** — xem S14/S15.

**Hình / Bảng**

- Bảng test đầy đủ số, tách 1 dòng / 2 dòng
- Đường cong mAP theo epoch từ `runs/final-640-v3/results.csv`; PR-curve `ch5-best-test_pr_curve.png`

**Speaker notes** *(50 s)*

> Đây là kết quả detection của mô hình chính thức `best.pt`, đo trên tập test 1.514 ảnh của bộ v3. Bốn chỉ tiêu — mAP50 0,983, mAP50-95 0,783, precision 0,984, recall 0,971 — đều vượt mục tiêu.
>
> Em tách riêng biển một dòng và hai dòng vì đó là rủi ro lớn nhất của đề tài. Ở tầng phát hiện, chênh lệch giữa hai loại chỉ 2,09 điểm mAP50 — nghĩa là bộ phát hiện làm việc tốt với cả hai. Điểm yếu biển hai dòng nằm ở tầng OCR, không phải ở đây, và em sẽ trình bày thẳng ở slide sau.
>
> Con số này đo trên split v3 đã khử trùng lặp ở ngưỡng phash 10. Baseline cũ đạt mAP 0,9933 nhưng con số đó lạc quan vì bộ v1 có rò rỉ train-test; con số 0,983 ở đây trung thực hơn. Nếu thầy cô nghi ngờ rò rỉ, em xin trình bày kỹ phần chống rò rỉ ở phần hỏi đáp.

---

# PHẦN E — ĐÓNG GÓP KỸ THUẬT LÕI

## S13 — Xử lý biển 2 dòng

> **Slide kỹ thuật đắt nhất của bài. Dành nhiều thời gian nhất ở đây.**

**Nội dung trên slide**

**Vấn đề — nguyên nhân gốc là KIẾN TRÚC, không phải chất lượng model:**
- CRNN/CTC giả định **alignment đơn điệu trên MỘT dòng** — giả định này nằm trong **hàm mất mát**, không sửa được bằng thêm dữ liệu
- Bằng chứng cụ thể trong PaddleOCR: module recognition resize về **chiều cao cố định 48 px** (`rec_image_shape = 3×48×320`). Crop biển xe máy có AR ≈ **1,36** ⇒ ép về cao 48 px thì **mỗi dòng chỉ còn ~24 px** — mức ký tự bắt đầu mất chi tiết

**Giải pháp — split-then-hstack:**

```
[ 59-H1 ]          RECTIFY (bắt buộc trước)
[ 234.56 ]   ───▶  tách trên/dưới (chồng lấn nhẹ)
  AR 1,36          resize 2 nửa về cùng chiều cao
                   ghép NGANG  ─▶  [ 59-H1 | 234.56 ]  ─▶ OCR gọi 1 LẦN
                                        AR ~5,4
```

- Mỗi dòng được dùng **trọn 48 px** chiều cao thay vì 24 px
- Chuỗi trở lại **đơn điệu một chiều** — đúng giả định CRNN
- ⚠️ **Bắt buộc rectify trước khi tách** — biển nghiêng thì đường cắt ngang sẽ cắt qua ký tự

**Nhận biết 1 dòng / 2 dòng — 3 nguồn theo thứ tự ưu tiên:** nhãn thật → tên lớp → suy đoán theo **AR, ngưỡng 2,5**

Ngưỡng 2,5 có **hai** căn cứ độc lập:
- Từ QCVN 08:2024: khoảng trống (2,000 ; 4,727)
- **Từ dữ liệu:** phân bố AR của 5.200 box **lưỡng đỉnh rõ**, vùng trũng ở 2,2–2,6 → ngưỡng 2,5 rơi đúng đáy

**Và em đo được độ chính xác của chính heuristic đó** (bộ dữ liệu có cả nhãn thật lẫn AR):

| | Đoán 1 dòng | Đoán 2 dòng |
|---|---:|---:|
| **Thật 1 dòng** (1.641) | 1.509 ✓ | 132 ✗ |
| **Thật 2 dòng** (3.559) | 7 ✗ | 3.552 ✓ |

→ **97,33%** (5.061/5.200), lệch **một chiều tỉ lệ 19:1**. Nguyên nhân: box bao polygon luôn có đệm, biển dài mảnh thì đệm theo chiều cao chiếm tỉ lệ lớn hơn ⇒ AR bị kéo xuống.

- Cài đặt: `ai/inference/two_line.py` · **26 unit test**

**Hình / Bảng**

- 🔴 **CẦN LÀM:** ảnh minh hoạ 3 bước split-then-hstack trên một crop biển xe máy thật — ảnh gốc → 2 nửa → dải ghép ngang. Xuất từ ảnh trung gian của `two_line.py`. **Đây là hình quan trọng nhất của cả bộ slide.**
- Biểu đồ phân bố AR (dùng lại từ S10), vẽ đường thẳng đứng tại 2,5 vào đúng đáy vùng trũng
- Ma trận nhầm lẫn 2×2 như trên

**Speaker notes** *(70 s — slide dài nhất, có chủ đích)*

> Đây là phần kỹ thuật lõi của đồ án.
>
> Trước hết, vì sao biển hai dòng khó. Nguyên nhân **không phải** model kém, mà là giới hạn kiến trúc. Kiến trúc CRNN với hàm mất mát CTC giả định rằng văn bản chạy đơn điệu trên **một** dòng — giả định đó nằm ngay trong hàm mất mát, nên không thể sửa bằng cách thêm dữ liệu.
>
> Em có một bằng chứng cụ thể hơn trong chính PaddleOCR: module nhận dạng của nó resize mọi ảnh về chiều cao cố định 48 pixel. Mà crop biển xe máy có tỉ lệ khung hình khoảng 1,36 — gần vuông. Ép một ảnh gần vuông về cao 48 pixel thì mỗi dòng chỉ còn khoảng 24 pixel. Đó là mức ký tự bắt đầu mất chi tiết.
>
> Giải pháp của em là split-then-hstack. Nắn thẳng biển trước, cắt thành nửa trên và nửa dưới có chồng lấn nhẹ, resize hai nửa về cùng chiều cao, rồi ghép **ngang** thành một dải dài, và gọi OCR đúng một lần. Việc này giải quyết cả hai vấn đề cùng lúc: mỗi dòng được dùng trọn 48 pixel thay vì 24, và chuỗi trở lại đơn điệu một chiều — đúng giả định mà CRNN cần. Nói ngắn gọn, em biến một bài toán mà kiến trúc không giải được thành một bài toán mà nó giải được.
>
> Một lưu ý: bắt buộc nắn thẳng **trước** khi tách, vì nếu biển nghiêng thì đường cắt ngang sẽ cắt qua giữa ký tự.
>
> Còn việc nhận biết một dòng hay hai dòng: ngưỡng tỉ lệ khung hình 2,5 có hai căn cứ độc lập — suy từ quy chuẩn QCVN, và được chính dữ liệu xác nhận: phân bố tỉ lệ khung hình của 5.200 hộp cho hai đỉnh rõ rệt với một vùng trũng ở khoảng 2,2 đến 2,6, và ngưỡng 2,5 rơi đúng đáy vùng trũng đó.
>
> Và vì bộ dữ liệu này có cả nhãn số dòng thật lẫn tỉ lệ khung hình, em **đo được** độ chính xác của chính heuristic: 97,33%. Nhưng lỗi lệch một chiều theo tỉ lệ 19 trên 1 — 132 lỗi ở hướng biển một dòng bị đoán nhầm thành hai dòng, chỉ 7 lỗi ở hướng ngược lại. Nguyên nhân là hộp bao quanh polygon luôn có đệm, mà với biển dài mảnh thì phần đệm theo chiều cao chiếm tỉ lệ lớn hơn nhiều, kéo tỉ lệ khung hình xuống.

---

## S14 — Bộ luật hậu xử lý theo vị trí

**Nội dung trên slide**

**Nguyên tắc:** sửa lỗi theo **VỊ TRÍ**, không sửa lỗi toàn cục

| Vị trí trong chuỗi | Ràng buộc | Luật sửa |
|---|---|---|
| 2 ký tự đầu — mã tỉnh | Phải là **chữ số**, thuộc **81 mã hợp lệ** | ép `O → 0`, `I → 1`, `S → 5` |
| Vị trí seri | Phải là **chữ cái** | ép `0 → O`, `1 → I`, `5 → S` |
| Phần số đăng ký | Phải là **chữ số** | ép về chữ số |
| **Vùng cấm sửa** | Nơi cả chữ và số đều hợp lệ | **tuyệt đối không đụng vào** |

→ Một bảng thay thế **toàn cục** sẽ làm hỏng một trong hai vị trí — cùng ký tự `O`/`0` cần luật **ngược nhau** ở hai chỗ

**Charset OCR: đủ 36 ký tự A–Z + 0–9 — và đây là một quyết định có lý do**

> ❌ Mệnh đề phổ biến: *"biển số VN chỉ dùng 20 chữ cái, 6 chữ I J O Q R W không bao giờ xuất hiện"* — **SAI**
> Chữ **R hợp lệ** ở vị trí chữ cái thứ hai của seri xe máy. Tập loại trừ đúng chỉ gồm **5 chữ: I J O Q W**.
> **Hậu quả nếu tin nhầm:** charset 20 chữ ⇒ mô hình **không bao giờ đoán được R** ⇒ sai hệ thống trên cả một lớp biển xe máy — và **hậu xử lý KHÔNG cứu được**, vì thông tin đã mất ngay ở tầng mô hình.

- Ràng buộc hợp lệ đặt ở **tầng hậu xử lý** — nơi sửa được và ghi log được, không đặt ở tầng mô hình
- Cài đặt: `ai/inference/plate_rules.py` + `normalizer.py` · **29 unit test**

**Hình / Bảng**

- Sơ đồ một chuỗi biển số mẫu `59-H1 234.56`, mỗi vị trí tô màu theo loại ràng buộc (số / chữ / cấm sửa)
- Hộp cảnh báo về chữ `R`, làm nổi bật

**Speaker notes** *(55 s)*

> Khối hậu xử lý xây theo một nguyên tắc: sửa lỗi theo **vị trí**, không sửa toàn cục. Ví dụ rõ nhất là cặp chữ O và số 0. Ở hai ký tự đầu — mã tỉnh — bắt buộc là chữ số, nên gặp chữ O phải ép về số 0. Nhưng ở vị trí seri thì bắt buộc là chữ cái, nên gặp số 0 phải ép ngược lại thành chữ O. Cùng một cặp ký tự, luật ngược nhau. Một bảng thay thế toàn cục chắc chắn làm hỏng một trong hai chỗ. Ngoài ra em có vùng cấm sửa tường minh: chỗ nào cả chữ và số đều hợp lệ thì tuyệt đối không đụng vào, vì sửa liều ở đó tạo lỗi mới thay vì sửa lỗi cũ.
>
> Phần thứ hai em muốn nêu là charset. Có một mệnh đề rất phổ biến rằng biển số Việt Nam chỉ dùng 20 chữ cái và sáu chữ I, J, O, Q, R, W không bao giờ xuất hiện. Con số 6 đó là suy diễn số học 26 trừ 20, và nó **sai**. Khi em đối chiếu danh sách chữ cái ở **vị trí thứ hai** của seri xe mô tô thì thấy có chữ R. Tập loại trừ chắc chắn chỉ gồm 5 chữ.
>
> Hậu quả nếu tin nhầm rất nặng: xây charset OCR 20 chữ thì mô hình **không bao giờ** dự đoán được ký tự R, tức là sai hệ thống trên cả một lớp biển xe máy. Và đây là loại lỗi hậu xử lý không cứu được, vì thông tin đã mất ngay ở tầng mô hình. Vì vậy em dùng đủ 36 ký tự ở tầng mô hình, và đặt ràng buộc hợp lệ ở tầng hậu xử lý — nơi sửa được và ghi log được.

---

## S15 — Đo định lượng đóng góp của hậu xử lý ✅ ĐÃ CÓ SỐ (OCR KHÔNG ĐẠT — trình bày trung thực)

> **Đã đo trên 2.801 biển có nhãn chuỗi. A4/A5/A6/A7 không đạt — kết quả thật.**

**Nội dung trên slide**

**Thiết kế phép đo — đây là đóng góp học thuật, không phải một khẳng định:**

Cơ sở dữ liệu lưu **cả hai** chuỗi trên **cùng một bản ghi**:

| Cột | Nội dung |
|---|---|
| `raw_ocr_text` | Chuỗi OCR **thô**, trước khi sửa regex |
| `plate_number` | Chuỗi **sau** chuẩn hoá |

→ Chạy trên tập test có nhãn chuỗi, tính exact-match trên **cả hai cột**
→ **Hiệu số chính là đóng góp định lượng của khối hậu xử lý**

**Bảng công bố — ĐÃ ĐO (2.801 biển có nhãn chuỗi):**

| Chỉ tiêu | Đo được | Mục tiêu | Ngưỡng tối thiểu | Đạt? |
|---|:--:|:--:|:--:|:--:|
| NFR-A4 — chính xác mức ký tự (1 − CER) | **0,8734** | ≥ 0,95 | ≥ 0,92 | ❌ |
| NFR-A5 — exact-match **trước** hậu xử lý | **0,6098** | ≥ 0,85 | ≥ 0,80 | ❌ |
| NFR-A6 — exact-match **sau** hậu xử lý | **0,6555** | ≥ 0,90 | ≥ 0,85 | ❌ |
| **Hiệu số A6 − A5 = đóng góp hậu xử lý** | **+4,57 điểm** | *kỳ vọng ~5 điểm* | | — |
| NFR-A7 — chính xác E2E toàn trình | **0,5227** | ≥ 0,88 | ≥ 0,82 | ❌ |

**Đóng góp hậu xử lý đo được: +4,57 điểm** — **128 biển được sửa đúng, 0 biển bị làm hỏng** (loss-free ở mức chuỗi). Phép đo biến một khẳng định định tính thành con số.

**Trình bày TRUNG THỰC — A4/A5/A6/A7 KHÔNG đạt, và toàn bộ khoảng cách nằm ở biển 2 dòng:**

| | Biển 1 dòng (567) | Biển 2 dòng (2.234) | Chênh |
|---|:--:|:--:|:--:|
| A4 (char) | **0,990** ✅ | 0,846 | 14,4 đ |
| A5 | **0,942** ✅ | 0,526 | 41,6 đ |
| A6 | **0,949** ✅ | 0,581 | **36,8 đ** |

Biển 1 dòng **vượt cả ba mục tiêu**; biển 2 dòng (xe máy, 79,8% tập nhãn) kéo tổng xuống. Chênh 36,8 điểm **cùng bậc độ lớn** với mốc Laroca RodoSol-ALPR *(Brazil, 48,6 điểm — không phải số VN)*.

**Hình / Bảng**

- Sơ đồ hai nhánh từ một crop biển: nhánh trên → `raw_ocr_text`, nhánh dưới qua khối luật → `plate_number`, hai nhánh cùng đổ vào một bản ghi CSDL, có dấu trừ giữa hai con số
- Bảng A4–A7 và bảng tách 1 dòng / 2 dòng

**Speaker notes** *(55 s)*

> Slide này nói về đóng góp học thuật chính, và em trình bày cả phần đạt lẫn phần không đạt.
>
> Ý tưởng: nói "chúng em có thêm một bước sửa lỗi regex" là khẳng định định tính. Nên em lưu **cả hai** chuỗi trên cùng bản ghi — `raw_ocr_text` thô và `plate_number` sau chuẩn hoá — rồi tính exact-match trên cả hai. Hiệu số chính là đóng góp định lượng của khối hậu xử lý: **+4,57 điểm, 128 biển sửa đúng, 0 biển làm hỏng**.
>
> Nhưng em phải nói thẳng: A4, A5, A6, A7 **đều không đạt chỉ tiêu**. Đây là kết quả thật, em không tô hồng. Điều quan trọng là **toàn bộ khoảng cách nằm ở biển hai dòng**: biển một dòng đạt char-accuracy 0,99 và exact-match sau xử lý 0,95 — vượt cả ba mục tiêu; biển hai dòng chỉ 0,85 và 0,58. Chênh 36,8 điểm.
>
> Vì sao? Biển hai dòng là xe máy, chiếm gần 80% tập nhãn, và OCR dòng đơn không đọc tốt hai dòng dù đã tách-rồi-ghép. Đây là rủi ro R-04 mà em nêu từ đầu, và nó bộc lộ đúng bằng số liệu Việt Nam thật. Con số này cùng bậc độ lớn với mốc Laroca trên bộ RodoSol của Brazil — nhưng em nhấn mạnh đó là số Brazil, không phải số Việt Nam.

---

# PHẦN F — HỆ THỐNG VÀ HIỆU NĂNG

## S16 — Giao diện hệ thống

**Nội dung trên slide**

**5 trang trong một khung ứng dụng chung:**

| Trang | Chức năng |
|---|---|
| `/` — Tổng quan | 4 thẻ chỉ số · trạng thái hệ thống · hoạt động 7 ngày · phân bố theo nguồn · 5 nhận dạng gần nhất |
| `/image` — Nhận dạng ảnh | Upload, vẽ bounding box, hiện biển số + độ tin cậy + thời gian xử lý |
| `/video` — Nhận dạng video | Upload → `202 Accepted` + `job_id` → hỏi tiến độ định kỳ → video có gắn nhãn |
| `/webcam` — Thời gian thực | Gửi từng khung qua HTTP, mục tiêu ~5 FPS |
| `/history` — Lịch sử | Lọc, sắp xếp, phân trang — **trạng thái nằm trên URL**, gửi link được |

**Bốn nguyên tắc giao diện:**
- **Bốn trạng thái đủ ở mọi vùng dữ liệu**: loading / empty / error / success — riêng *empty* tách nhỏ theo nguyên nhân
- **Kết quả rỗng ≠ lỗi**: xử lý xong không thấy biển ⇒ trạng thái rỗng, không phải màn hình đỏ
- **Lỗi nói tiếng người**: không bao giờ để traceback lên màn hình
- **Không lớp chuyển đổi tên trường**: TypeScript dùng `snake_case` y hệt JSON API ⇒ backend đổi schema thì **báo lỗi lúc biên dịch**, không lặng lẽ thành `undefined` lúc chạy

**Hình / Bảng**

- **Ảnh chụp màn hình** — đã có sẵn trong `docs/screenshots/`:
  - `dashboard.png` (ảnh lớn, chiếm ~55% slide)
  - `image-detection.png` (ảnh vừa — quan trọng nhất vì hiện kết quả AI thật)
  - `history.png`, `webcam.png`, `video-detection.png` (3 ảnh nhỏ xếp hàng dưới)

**Speaker notes** *(40 s)*

> Giao diện gồm năm trang: tổng quan, nhận dạng ảnh, nhận dạng video, webcam và lịch sử. Ba trang nhận dạng là nguồn sinh dữ liệu, tất cả đổ về cùng một bảng lịch sử.
>
> Em xin nêu hai chi tiết thiết kế. Thứ nhất, mỗi vùng dữ liệu đều xử lý đủ bốn trạng thái, và riêng trạng thái rỗng em còn tách nhỏ theo nguyên nhân — chưa gửi gì, đã xử lý mà không thấy biển, hay không khớp bộ lọc — vì cách thoát khỏi mỗi trạng thái là khác nhau. Thứ hai, kiểu dữ liệu ở frontend dùng đúng tên trường của JSON API, không có lớp chuyển đổi ở giữa. Nhờ vậy nếu backend đổi schema thì TypeScript báo lỗi ngay lúc biên dịch, thay vì một trường lặng lẽ thành undefined lúc chạy.
>
> Nếu thầy cô muốn, em có thể demo trực tiếp sau phần trình bày.

---

## S17 — Hiệu năng trên CPU ✅ ĐÃ ĐO (NFR-P1 ĐẠT)

> **Đã đo trên `models/best.pt`, máy rảnh: p95 731 ms client / 780 ms in-process.**

**Nội dung trên slide**

**Phần cứng đo (bắt buộc công bố kèm mọi con số):** Intel Core i5-14600K · 14 nhân / 20 luồng · **không có GPU CUDA** · backend suy luận PyTorch · `imgsz` 640 · một ảnh mỗi lần gọi

**Bảng công bố — ĐÃ ĐO trên `models/best.pt`, máy rảnh:**

| Chỉ tiêu | p50 | p95 | p99 | Đạt? | Ngưỡng |
|---|:--:|:--:|:--:|:--:|:--:|
| NFR-P1 — độ trễ 1 ảnh (client-side, HTTP) | 415 ms | **731 ms** | 948 ms | ✅ | p95 ≤ 800 ms |
| NFR-P1 — độ trễ 1 ảnh (in-process) | 419 ms | **780 ms** | 948 ms | ✅ | p95 ≤ 800 ms |
| NFR-SC1 — yêu cầu đồng thời | — | — | — | ✅ (**10**) | ≥ 5 |

**Phân rã độ trễ ĐO THẬT trên `best.pt` (T5.7b) — đối chiếu với ước lượng thiết kế:**

| Bước | Ước lượng | **Đo thật** | % tổng |
|---|---:|---:|---:|
| Giải mã ảnh | ~50 ms | **2,65 ms** | 1,5% |
| YOLO11n @ 640 | ~150 ms | **59,83 ms** | **34,2%** |
| Cắt vùng biển | ~30 ms | **0,00 ms** | 0,0% |
| PaddleOCR (mỗi biển) | ~120 ms | **112,55 ms** | **64,3%** |
| Chuẩn hoá regex | < 5 ms | **0,03 ms** | 0,0% |

> ✅ **NFR-P1 ĐẠT** — p95 731 ms (client-side) / 780 ms (in-process), dưới mục tiêu 800 ms. Con số cũ **5.857 ms bị bác bỏ**: nó đo khi một tiến trình huấn luyện chiếm ~793% CPU song song, trên checkpoint epoch 7 (không phải `best.pt`), và có lỗi crop khiến OCR đọc ~1322 ms/ảnh. Phân rã đúng: **OCR 64,3% / detect 34,2%** — OCR vẫn tốn nhất nhưng **không còn áp đảo**, tối ưu detector giờ mới có ý nghĩa. Nguồn: [07-benchmark-p1-resolved.json](../reports/07-benchmark-p1-resolved.json).

**Vì sao KHÔNG dùng bảng benchmark cũ có sẵn trong kho mã** (ONNX 6,18 ms, nhanh 2,35×) — ba lý do:
1. Đo trên **mô hình tổng hợp cũ**, không phải `models/best.pt`
2. Đo ở **`imgsz = 320`**, không phải 640 của hệ thống thật
3. **Không tái lập được** — file JSON kết quả không còn trên đĩa

**Hình / Bảng**

- Biểu đồ cột xếp chồng ngang: ước lượng vs đo thật, có vạch đứt ở mốc 800 ms
- Bảng chỉ tiêu đã điền số

**Speaker notes** *(50 s)*

> Về hiệu năng: NFR-P1 — độ trễ đầu-cuối một ảnh — em đo được p95 731 mili-giây phía client qua HTTP, và 780 mili-giây in-process, đều dưới mục tiêu 800. **Đạt.**
>
> Em phải kể một câu chuyện phương pháp luận ở đây. Bản báo cáo đầu của em ghi con số 5.857 mili-giây — trượt nặng. Nhưng con số đó sai, và em đã truy ra ba nguyên nhân: nó đo khi một tiến trình huấn luyện đang chiếm gần 8 nhân CPU song song; nó đo trên checkpoint giữa chừng chứ không phải mô hình chính thức; và hệ thống lúc đó có một lỗi cắt ảnh khiến OCR đọc trên ảnh quá lớn, mất 1300 mili-giây một ảnh. Đo lại trên máy rảnh với mô hình đúng, con số về 731.
>
> Phân rã cho thấy OCR chiếm 64%, phát hiện 34%. Bài học: một phép đo lấy trên hệ thống đang có lỗi trông y hệt một phép đo hợp lệ — nó vẫn có cỡ mẫu, có phân vị. Chỉ có đo lại sau khi sửa lỗi mới lộ ra.
>
> Và nguyên tắc em chốt: mọi con số hiệu năng công bố kèm tên CPU, số luồng, kích thước ảnh, cỡ mẫu.

---

# PHẦN G — KẾT

## S18 — Hạn chế

> **Slide trung thực. Liệt kê thật, không tô hồng.**

**Nội dung trên slide**

| # | Hạn chế | Trạng thái | Nguyên nhân gốc |
|---|---|:--:|---|
| 1 | **OCR biển 2 dòng KHÔNG đạt chỉ tiêu** — A4 0,873 / A5 0,610 / A6 0,656 (biển 2 dòng char_acc chỉ 0,846) | ❌ | OCR dòng đơn (CRNN/CTC) đọc kém biển 2 dòng; xe máy chiếm 79,8% tập nhãn |
| 2 | **NFR-A7 (E2E) không đo được có ý nghĩa** = 0,5227 | ⚠️ | Không bộ dữ liệu nào vừa có ảnh toàn cảnh vừa có chuỗi biển ⇒ đo trên crop, ngoài phân bố detector |
| 3 | **NFR-P2/P3 (webcam/video), A9, R5 chưa đo** | ❌ | Chưa có kịch bản đo cho các chế độ này |
| 4 | **Docker chưa build thật** — có Dockerfile + compose, `docker compose config` hợp lệ | ⚠️ | Ưu tiên dồn vào huấn luyện và tích hợp OCR |
| 5 | **Chưa tự benchmark 3 engine OCR** (PaddleOCR / EasyOCR / Tesseract) | ❌ | Không tồn tại benchmark công khai nào trên biển xe máy VN 2 dòng |
| 6 | **Quy mô dữ liệu 12,3% kế hoạch** — 4.578 / 37.300 ảnh | ⚠️ | Bộ VNLP trả HTTP 401, chuyển gated |
| 7 | **Giấy phép bộ dữ liệu chưa rõ** | ⚠️ | Trang nguồn không ghi license |
| 8 | **Chưa kiểm chứng ở chế độ đa đối tượng** | ⚠️ | 90,8% ảnh chỉ có 1 biển; toàn bộ dataset chỉ 9 ảnh có ≥ 5 biển |
| 9 | Không có xác thực người dùng · SQLite 1 tiến trình ghi | ⚠️ | Lựa chọn phạm vi có ý thức (giả định A-04, chạy nội bộ) |

**Ba thiên lệch dữ liệu đã đo được:** ảnh gần như chỉ có 1 biển (90,8%) · biển tập trung giữa khung (heatmap x≈0,46–0,50) · box cực nhỏ tập trung ở biển xe máy (p05 diện tích 0,244% so với 1,002%)

**Hình / Bảng**

- Bảng như trên, cột trạng thái dùng ký hiệu ❌ / ⚠️ nhất quán
- Không thêm hình — slide này để chữ nói

**Speaker notes** *(45 s)*

> Đây là slide em muốn trình bày thẳng.
>
> Hạn chế lớn nhất, và em nói thẳng: **OCR biển hai dòng không đạt chỉ tiêu**. Char-accuracy tổng 0,873, exact-match sau xử lý 0,656 — đều dưới ngưỡng. Toàn bộ khoảng cách nằm ở biển hai dòng: biển một dòng đạt 0,99 và 0,95, vượt mục tiêu; biển hai dòng chỉ 0,85 và 0,58. Vì xe máy chiếm gần 80% tập nhãn nên nó kéo tổng xuống. Đây là kết quả thật, em không tô hồng, và em đã phân tích nguyên nhân: OCR dòng đơn đọc kém hai dòng dù đã tách-rồi-ghép.
>
> Hai, NFR-A7 đo E2E ra 0,52 nhưng con số này không đại diện, vì không bộ dữ liệu nào vừa có ảnh toàn cảnh vừa có chuỗi biển, nên em buộc phải đo trên ảnh crop — ngoài phân bố của detector. Ba, một số chỉ tiêu như FPS webcam, xử lý video, điều kiện ảnh thì em chưa đo. Ngoài ra Docker mới có cấu hình hợp lệ chứ chưa build thật, và giấy phép một phần bộ dữ liệu chưa rõ — em ghi nhận từ đầu.

---

## S19 — Hướng phát triển

**Nội dung trên slide**

**Ngắn hạn — xử lý nút thắt còn lại:**
1. **Cải thiện OCR biển 2 dòng** — nơi chứa toàn bộ 36,8 điểm khoảng cách. Sửa hai luật ánh xạ sai đích (`L→1` phải là `L→4`; `7→T` phải là `7→Z`), xử lý 217 ca mất trọn một dòng và ký tự ma ở đường ghép hstack
2. **Gán nhãn chuỗi cho 300–500 ảnh test v3** ⇒ đo được NFR-A7 đúng cách (không phải trên crop ngoài phân bố)
3. **Tự benchmark 3 engine OCR** trên tập biển số Việt Nam có nhãn
4. **Đo NFR-P2/P3 (webcam/video), A9, R5** — các chế độ còn thiếu

**Trung hạn — nâng chất lượng:**
5. Fine-tune OCR trên biển số Việt Nam (charset **36 ký tự**, không thu hẹp)
6. Huấn luyện **YOLO26n song song làm đối chứng** — trên giấy tờ tốt hơn ở cả 3 chỉ số nhưng chưa có tiền lệ ALPR nào
7. Xuất **ONNX Runtime** để giảm độ trễ — đường tối ưu đầu tiên, trước khi nghĩ tới giảm `imgsz`
8. Tự chụp một bộ test có nhãn ở đúng bối cảnh triển khai (bãi xe, cổng cơ quan)

**Nếu triển khai thật — 6 việc theo thứ tự ưu tiên:**
xác thực + phân quyền → SQLite sang PostgreSQL → kiểm thử chịu tải → ONNX Runtime → làm rõ giấy phép dữ liệu → giám sát suy giảm mô hình

**Hình / Bảng**

- Lộ trình 3 mốc theo trục ngang: ngắn hạn / trung hạn / triển khai thật

**Speaker notes** *(35 s)*

> Hướng phát triển của em chia ba mốc.
>
> Ngắn hạn là mở khoá những thứ đang bị chặn: hoàn thành huấn luyện, gộp xong hai bộ dữ liệu có nhãn ký tự — riêng việc này mở khoá bốn chỉ tiêu cùng lúc — và tự chạy benchmark ba engine OCR. Đó là việc đầu tiên em làm nếu tiếp tục đề tài.
>
> Trung hạn là fine-tune OCR trên biển số Việt Nam, huấn luyện YOLO26 song song làm đối chứng, và xuất sang ONNX Runtime để giảm độ trễ.
>
> Còn nếu triển khai thật thì việc số một là xác thực và phân quyền — vì lịch sử biển số là dữ liệu có thể truy vết cá nhân, không có xác thực thì bất kỳ ai vào được mạng đều xem được toàn bộ.

---

## S20 — Kết luận

**Nội dung trên slide**

**Đã làm được:**
- ✅ Hệ thống **5 tầng chạy được** — backend 10 endpoint kiểm chứng bằng HTTP thật; frontend typecheck / lint sạch, build thành công, 10 endpoint khớp kiểu từng trường
- ✅ Bộ dữ liệu **15.133 ảnh (v3, 6 nguồn)** có **quy trình chống rò rỉ kiểm chứng được** — khử trùng lặp ở ngưỡng 10, v2→v3 giảm rò rỉ vắt split từ 9.126 xuống 0 cặp
- ✅ Mô hình chính thức `best.pt` **huấn luyện xong**: detection mAP50 **0,983** / mAP50-95 **0,783** trên tập test v3, đạt cả bốn chỉ tiêu; NFR-P1 **đạt** (p95 731/780 ms)
- ✅ Module tách biển 2 dòng + bộ luật hậu xử lý theo vị trí — **104 unit test** tầng AI

**Bốn đóng góp — mỗi cái kiểm chứng được:**

| # | Đóng góp | Bằng chứng |
|---|---|---|
| 1 | Bộ luật sửa lỗi OCR **theo vị trí**, xây từ TT 79/2024 | `plate_rules.py` · 29 test |
| 2 | **Thiết kế phép đo** đóng góp của hậu xử lý (`raw_ocr_text` vs `plate_number`) | Schema CSDL 18 cột |
| 3 | Đánh giá **tách riêng** biển 1 dòng / 2 dòng, không che bằng số trung bình | `evaluate.py` bảng NFR-A8 |
| 4 | Hệ thống hoàn chỉnh **chạy không cần GPU** | 5 tầng · 10 endpoint · 5 trang |

**Ba điều đồ án này KHÔNG tuyên bố:**
- ❌ Không tạo ra state-of-the-art, và **không đặt mục tiêu đó**
- ❌ Không phải sản phẩm triển khai được — thiếu xác thực, chưa kiểm thử tải đầy đủ
- ❌ **OCR biển 2 dòng chưa đạt chỉ tiêu** — trình bày trung thực, không tô hồng

**Hình / Bảng**

- Hai cột song song: cột trái ✅ đã làm, cột phải ❌ không tuyên bố. Cân bằng thị giác giữa hai cột là chủ ý.

**Speaker notes** *(35 s)*

> Tóm lại. Em đã xây được một hệ thống năm tầng chạy được và kiểm chứng được bằng gọi HTTP thật, một bộ dữ liệu có quy trình chống rò rỉ mà chính bước đó bắt được lỗi thật trong bản chia gốc, một mô hình phát hiện đạt cả bốn chỉ tiêu, và hai module kỹ thuật lõi là tách biển hai dòng và bộ luật hậu xử lý theo vị trí.
>
> Đóng góp của em không nằm ở việc phát minh kiến trúc mạng — YOLO và PaddleOCR đều là công cụ có sẵn. Đóng góp nằm ở tầng giữa: bộ luật xây từ văn bản pháp lý hiện hành, cơ chế xử lý biển hai dòng, và quan trọng nhất là **thiết kế phép đo để chứng minh chúng có tác dụng** thay vì chỉ khẳng định — đo được +4,57 điểm đóng góp của hậu xử lý.
>
> Và em muốn kết bằng ba điều đồ án này **không** tuyên bố: nó không tạo ra state-of-the-art và không đặt mục tiêu đó; nó chưa phải sản phẩm triển khai được; và **OCR biển hai dòng chưa đạt chỉ tiêu** — em trình bày thẳng kết quả đó kèm phân tích nguyên nhân. Em nghĩ nói rõ ranh giới cũng quan trọng như nói kết quả.

---

## S21 — Cảm ơn / Hỏi đáp

**Nội dung trên slide**

- **Em xin cảm ơn thầy cô đã lắng nghe**
- Lời cảm ơn giảng viên hướng dẫn
- **Em xin sẵn sàng nhận câu hỏi từ hội đồng**
- Góc dưới: bảng số liệu tra nhanh cỡ nhỏ (để tự tra khi trả lời, không phải để hội đồng đọc):

| | |
|---|---|
| Ảnh (v3) | 15.133 · 6 nguồn |
| Chia tập | 10.592 / 3.027 / 1.514 |
| Mô hình | `best.pt` YOLO11n · imgsz 640 · split v3 · 20 epoch |
| Detection (test v3) | mAP50 0,983 · mAP50-95 0,783 · P 0,984 · R 0,971 |
| OCR (2.801 biển) | A4 0,873 · A5 0,610 · A6 0,656 (KHÔNG đạt; 2 dòng yếu) |
| NFR-P1 p95 | 731 ms client / 780 ms in-process (đạt) |
| Charset | 36 ký tự · loại trừ đúng 5 chữ |
| Unit test tầng AI | 104 |

**Hình / Bảng**

- Nền tối giản, chữ lớn
- Không dùng hình động

**Speaker notes** *(20 s)*

> Phần trình bày của em đến đây là hết. Em xin chân thành cảm ơn thầy/cô [tên] đã hướng dẫn em trong suốt quá trình làm đồ án, và cảm ơn hội đồng đã lắng nghe. Em xin sẵn sàng nhận câu hỏi ạ.

---

## Checklist trước khi vào phòng

**Về nội dung slide**
- [ ] S12, S15, S17 — cập nhật số mới nhất nếu huấn luyện / đo đã có kết quả; nếu chưa thì **giữ nguyên ô trống**, đừng xoá bảng
- [ ] S13 — đã render ảnh minh hoạ split-then-hstack chưa (hình quan trọng nhất, hiện **còn thiếu**)
- [ ] Mọi con số trên slide đọc lại từ file nguồn, không chép tay
- [ ] Slide S2 ghi rõ cảnh báo phạm vi áp dụng "số liệu Brazil, không phải Việt Nam"

**Về kỹ thuật**
- [ ] Backend và frontend **đã khởi động trước khi vào phòng** — đừng để lần chạy đầu của buổi bảo vệ là lần khởi động server
- [ ] 2–3 ảnh test đã biết chắc chạy được, để sẵn trên desktop
- [ ] Tab Swagger mở sẵn
- [ ] File slide xuất **PDF dự phòng** — không phụ thuộc máy chiếu hiểu được định dạng gốc
- [ ] Ảnh nhúng hết vào file, không link ngoài

**Về trả lời**
- [ ] Đọc lại `docs/slides/10-defense-qa.md`, đặc biệt mục "Ba câu dễ trả lời sai nhất": mAP 0,983 có rò rỉ không (C3) · vì sao OCR biển 2 dòng không đạt (D1) · tốc độ bao nhiêu, sao con số cũ 5.857 ms (F3)
- [ ] Thuộc bảng số liệu tra nhanh ở S21
- [ ] Nhớ nguyên tắc: **chưa đo thì nói chưa đo**

---

## Bản đồ slide ↔ câu hỏi phản biện

Dùng khi hội đồng hỏi giữa lúc trình bày — biết ngay câu trả lời nằm ở đâu trong `10-defense-qa.md`.

| Slide | Câu hỏi có thể bị hỏi ngay | Mục trong Q&A |
|---|---|---|
| S2 | "Số liệu Brazil thì liên quan gì tới VN?" | A2 |
| S3 | "Phạm vi đến đâu? Cái gì cố ý không làm?" | A6 |
| S4 | "Sao không dùng end-to-end / model nước ngoài?" | A3 |
| S6 | "Thông tư thay đổi thì hệ thống còn đúng không?" | **G2** |
| S7, S8 | "Tách tầng AI có cần thiết không?" · "Sao dùng SQLite?" | E1, E2, E8 |
| S10 | "Dữ liệu ở đâu, có bản quyền không?" · "Chống rò rỉ thế nào?" | B1, **B3** |
| S11 | "Sao chọn YOLO11 / nano?" · "Sao train trên CPU?" | C1, C2, C4 |
| **S12** | ⚠️ **"mAP 0,983 cao quá, có rò rỉ không?"** | **C3 — câu khó nhất** |
| S13 | "Biển 2 dòng xử lý thế nào?" · "Sao biết mấy dòng?" | D2, D3 |
| S14 | "Charset gồm những ký tự nào?" | **D6** |
| S15 | "Làm sao biết hậu xử lý có tác dụng?" · "Sao chọn PaddleOCR?" | F4, **D1** |
| **S17** | ⚠️ **"Tốc độ bao nhiêu? Đo trên máy gì?"** | **F3** |
| S18 | "Docker chạy được chưa?" · "Chịu được bao nhiêu người dùng?" | E7, E3, G3 |
| S20 | "Đóng góp thực sự là gì? Ghép thư viện thôi mà?" | **A1**, G4 |
