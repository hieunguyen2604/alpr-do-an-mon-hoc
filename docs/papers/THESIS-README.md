# Hướng dẫn biên soạn quyển đồ án tốt nghiệp

**Đề tài:** Xây dựng hệ thống nhận dạng biển số xe Việt Nam ứng dụng Trí tuệ nhân tạo

| Mục | Nội dung |
|---|---|
| Thư mục | `docs/papers/` |
| Giai đoạn | Phase 9 — Documentation |
| Ngày lập | 2026-07-19 |
| Đối tượng đọc | Người viết tiếp quyển đồ án ở các phiên làm việc sau |

Tài liệu này trả lời bốn câu hỏi: **quyển đồ án nằm ở đâu**, **đánh số thế nào**, **trích dẫn thế nào**, và **ghép thành một tệp ra sao**. Đọc tài liệu này trước khi viết bất kỳ chương nào.

---

## 1. Cấu trúc thư mục

```
docs/papers/
├── THESIS-README.md          ← tài liệu này — quy ước biên soạn
├── 00-thesis-outline.md      ← đề cương chi tiết toàn quyển (đến cấp 3)
├── 01-front-matter.md        ← bìa, cam đoan, cảm ơn, mục lục, danh mục, abstract
├── 02-chuong-1-mo-dau.md                     ← chưa tạo
├── 03-chuong-2-tong-quan-co-so-ly-thuyet.md  ← chưa tạo
├── 04-chuong-3-phan-tich-thiet-ke.md         ← chưa tạo
├── 05-chuong-4-cai-dat.md                    ← chưa tạo (chờ huấn luyện mô hình)
├── 06-chuong-5-thuc-nghiem-danh-gia.md       ← chưa tạo (chờ huấn luyện mô hình)
├── 07-chuong-6-ket-luan.md                   ← chưa tạo (chờ Chương 5)
├── 08-tai-lieu-tham-khao.md                  ← chưa tạo (sinh từ references.bib)
├── 09-phu-luc.md                             ← chưa tạo
└── build/                    ← đầu ra khi ghép — KHÔNG sửa tay, KHÔNG commit
    └── thesis-full.md
```

**Quy tắc đặt tên tệp:** `<số thứ tự 2 chữ số>-<slug không dấu, gạch nối>.md`. Số thứ tự quyết định thứ tự ghép, nên **không được đổi** sau khi đã đặt. Nếu cần chèn tệp vào giữa, dùng hậu tố chữ (`04a-…`) thay vì đánh số lại toàn bộ.

### Các thư mục liên quan

| Thư mục | Vai trò |
|---|---|
| `docs/00-requirements/` | Nguồn cho Chương 1 và Chương 3 |
| `docs/architecture/` | Nguồn cho Chương 3 |
| `docs/reports/` | Nguồn cho Chương 2 (6 báo cáo Phase 1) |
| `docs/references.bib` | 232 entry BibTeX — nguồn duy nhất của phần Tài liệu tham khảo |
| `docs/slides/`, `docs/poster/` | Phase 10 — **không** thuộc quyển đồ án |

---

## 2. Trạng thái từng chương

| Tệp | Chương | Trạng thái | Điều kiện chặn |
|---|---|---|---|
| `01-front-matter.md` | Phần đầu quyển | 🟢 **Xong phần làm được** — danh mục từ viết tắt và hai abstract hoàn chỉnh; bìa/cam đoan/cảm ơn là mẫu chờ điền; mục lục và danh mục hình/bảng là placeholder | — |
| `02-…` | 1. Mở đầu | 🟡 **Viết được ngay** | — |
| `03-…` | 2. Tổng quan và cơ sở lý thuyết | 🟡 **Viết được ngay** | — |
| `04-…` | 3. Phân tích và thiết kế hệ thống | 🟡 **Viết được ngay** | — |
| `05-…` | 4. Cài đặt hệ thống | 🟢 **ĐÃ VIẾT** (`ch4-cai-dat.md`) | — |
| `06-…` | 5. Thực nghiệm và đánh giá | 🟢 **ĐÃ VIẾT** (`ch5-thuc-nghiem.md`) | Số liệu đã đầy đủ (`05-tables.md`) |
| `07-…` | 6. Kết luận và hướng phát triển | 🟢 **ĐÃ VIẾT** (`ch6-ket-luan.md`) | — |
| `08-…` | Tài liệu tham khảo | ⚪ Sinh khi ghép | Toàn bộ chương |
| `09-…` | Phụ lục | 🟡 Một phần viết được ngay (A, B, C, D) | Phụ lục E chờ Chương 5 |

### Vì sao hai chương cuối chưa viết được

Hệ thống chạy **pipeline thật**: `ALPRPipeline` với mô hình chính thức `models/best.pt`, `/health` báo `model_loaded: true`, engine `yolo:best.pt+paddleocr-PP-OCRv5-mobile`.

Trước đó (Phase 5–7) hệ thống chạy **`StubPipeline`** — một cài đặt giả lập tuân đúng giao diện trừu tượng của tầng AI, cho phép phát triển và kiểm thử backend, cơ sở dữ liệu và giao diện trước khi có mô hình thật. Stub **đã bị đưa ra khỏi đường chạy chính**; nó chỉ chạy khi đặt tường minh `ALPR_USE_STUB=true`, còn phương án lùi khi thiếu trọng số là `UnavailablePipeline` (ném lỗi thay vì bịa kết quả).

Chương 5 và 6 đã viết được vì số liệu thực nghiệm đã đầy đủ: `models/best.pt` (`imgsz=640`, split v3) đã huấn luyện xong — detection đạt cả bốn chỉ tiêu (mAP@0.5 0,9829), NFR-P1 đạt (731/780 ms), và NFR-A4/A5/A6/A7 đã đo (OCR biển hai dòng không đạt — kết quả thật).

> **Ranh giới không được vượt qua.** Không một con số nào do `StubPipeline` sinh ra được phép xuất hiện trong Chương 5, trong hai bản abstract, hay trong slide bảo vệ dưới danh nghĩa kết quả thực nghiệm. Số của `baseline-416-v1.pt` (mô hình đối chứng) được phép nêu **nhưng phải kèm cả hai khiếm khuyết ngay trong câu** (imgsz=416; split v1 có rò rỉ), và không được trình bày như kết quả đạt chỉ tiêu — số công bố lấy từ `models/best.pt`.

Trạng thái đã xác minh của phần đã làm được: backend FastAPI **chạy được thật** — **10 endpoint** phản hồi đúng qua HTTP (10 thao tác trên 9 đường dẫn; `/docs`, `/redoc`, `/openapi.json` do FastAPI tự sinh, không tính vào 10), Alembic migrate thành công, Swagger UI render được. Nhờ vậy Chương 3 mô tả một thiết kế **đã được kiểm chứng bằng cài đặt**, không phải thiết kế trên giấy.

---

## 3. Quy ước đánh số

### 3.1. Đánh số mục

Dùng đánh số phân cấp kiểu `1.`, `1.1.`, `1.1.1.` — tối đa **ba cấp** trong thân bài. Cấp 4 trở đi dùng danh sách gạch đầu dòng hoặc chữ cái `a)`, `b)`, không đánh số tiếp.

Ánh xạ sang tiêu đề Markdown:

| Cấp | Markdown | Ví dụ |
|---|---|---|
| Chương | `# CHƯƠNG n. TÊN CHƯƠNG` | `# CHƯƠNG 2. TỔNG QUAN VÀ CƠ SỞ LÝ THUYẾT` |
| Cấp 2 | `## n.m. Tên mục` | `## 2.6. Quy chuẩn biển số xe Việt Nam` |
| Cấp 3 | `### n.m.k. Tên mục` | `### 2.6.5. Tập ký tự seri hợp lệ` |

**Mỗi tệp chương chỉ có đúng một tiêu đề cấp `#`.** Đây là điều kiện để công cụ sinh mục lục tự động hoạt động và để việc ghép tệp không tạo ra cấu trúc lệch.

Danh sách mục chính thức nằm ở `00-thesis-outline.md`. **Sửa đề cương trước, viết chương sau** — không tự thêm mục mới trực tiếp vào tệp chương, vì mục lục sẽ lệch với đề cương.

### 3.2. Đánh số hình và bảng

| Loại | Định dạng | Vị trí chú thích |
|---|---|---|
| Hình | `Hình <chương>.<thứ tự>` — ví dụ `Hình 3.2` | **Dưới** hình, căn giữa |
| Bảng | `Bảng <chương>.<thứ tự>` — ví dụ `Bảng 2.5` | **Trên** bảng |
| Công thức | `(<chương>.<thứ tự>)` căn phải — ví dụ `(2.7)` | — |

Thứ tự đếm lại từ 1 ở mỗi chương. Hình và bảng **phải được nhắc tới trong thân bài** trước khi xuất hiện (*"…như trình bày ở Hình 3.2"*). Hình hoặc bảng không được nhắc tới ở đâu thì hoặc là thừa, hoặc là thân bài đang thiếu một đoạn.

Hình hoặc bảng lấy/phỏng theo nguồn khác **bắt buộc** ghi nguồn trong chú thích kèm ký hiệu `[n]`.

### 3.3. Sơ đồ và bảng biểu

- **Sơ đồ:** dùng `mermaid` (`graph`, `flowchart`, `sequenceDiagram`, `erDiagram`, `gantt`). Các báo cáo Phase 0–1 đã có sẵn nhiều sơ đồ mermaid dùng lại được — xem `ARCH` §2–6, `SCOPE` §4, `FR` §1.
- **Bảng:** dùng bảng Markdown chuẩn. Bảng quá rộng thì tách cột hoặc chuyển xuống Phụ lục, **không** thu nhỏ chữ.

### 3.4. Quy ước ngôn ngữ và số

| Hạng mục | Quy ước | Ví dụ |
|---|---|---|
| Văn phong | Tiếng Việt học thuật, ngôi kể khách quan | *"Đồ án xây dựng…"*, không dùng *"em/chúng em"* |
| Dấu thập phân | **Dấu phẩy** trong thân bài tiếng Việt | `94,3%`, `0,90` |
| Dấu thập phân | **Dấu chấm** trong mã nguồn, tên tệp, abstract tiếng Anh | `conf=0.25`, `94.3%` |
| Thuật ngữ chuyên ngành | Giữ nguyên tiếng Anh khi đó là cách dùng thông thường | *bounding box*, *pipeline*, *dataset*, *confidence*, *mAP*, *backbone* |
| Từ viết tắt | Lần đầu viết đầy đủ kèm viết tắt trong ngoặc; các lần sau chỉ dùng viết tắt | *"nhận dạng biển số xe tự động (ALPR)"* |
| Mã nguồn, docstring, Swagger | **Tiếng Anh** (ràng buộc CON-05) | — |

---

## 4. Quy ước trích dẫn

### 4.1. Định dạng bắt buộc

Mọi số liệu, mọi mệnh đề lấy từ nguồn khác **phải có trích dẫn**, gồm **hai phần đi liền nhau**:

```markdown
...hệ thống OpenALPR đạt 94,3% trên biển một dòng [1]<!-- laroca_2022_crossdataset -->
```

| Phần | Vai trò |
|---|---|
| `[n]` | Số hiệu trỏ tới mục Tài liệu tham khảo — **tạm thời**, đánh lại toàn quyển khi ghép |
| `<!-- khoa_bibtex -->` | Khoá tra trong `docs/references.bib` — **thông tin gốc, luôn đúng, không bao giờ đổi** |

> **Vì sao cần cả hai.** Số `[n]` phụ thuộc thứ tự xuất hiện trong quyển hoàn chỉnh, mà quyển thì đang viết dở và viết không theo thứ tự chương. Nếu chỉ ghi `[n]`, mọi con số sẽ sai ngay khi chèn thêm một trích dẫn ở chương trước. Khoá BibTeX trong comment HTML là **neo bất biến** — script ghép dựa vào nó để đánh lại số. Comment HTML không hiển thị khi render, nên không ảnh hưởng bản đọc.

### 4.2. Cách tra khoá BibTeX

1. Tìm nguồn cần dẫn trong báo cáo Phase 1 tương ứng (chúng dẫn nguồn bằng **URL nội tuyến**).
2. Tra dòng tương ứng trong `docs/reports/01-citation-map.md` để lấy **khoá BibTeX**.
3. Dùng khoá đó trong comment HTML.

**Không sửa sáu báo cáo Phase 1 sang cú pháp `\cite{}`.** Chúng cố ý dùng URL nội tuyến để đọc trực tiếp được trên GitHub; `01-citation-map.md` tồn tại chính là để giữ được **cả hai** dạng.

### 4.3. Ba quy tắc cứng

1. **Không bịa.** Không bịa số liệu, tên bài báo, tên tác giả, năm xuất bản. Chỉ dùng những gì **có trong** tài liệu Phase 0–1 và `references.bib`.
2. **Không dùng nhóm *Further reading*.** 21 entry trong nhóm `% === Further reading (not cited) ===` ở cuối `references.bib` **chưa được trích ở bất kỳ báo cáo nào**. Muốn dùng: đọc và kiểm chứng lại nguồn, chuyển entry lên đúng mục chủ đề trong `.bib`, rồi mới trích. Không `\cite{}` thẳng từ nhóm này.
3. **Giữ nguyên cảnh báo về phạm vi số liệu.** Một số con số kèm cảnh báo bắt buộc, ghi ở §4.4. Rút gọn câu văn làm mất cảnh báo là lỗi trích dẫn nghiêm trọng.

### 4.4. Các số liệu có cảnh báo bắt buộc

| Số liệu | Khoá BibTeX | Cảnh báo không được lược bỏ |
|---|---|---|
| OpenALPR 94,3% (biển 1 dòng) ↔ 45,7% (biển 2 dòng), chênh 48,6 điểm | `laroca_2022_crossdataset` | Đo trên **RodoSol-ALPR (Brazil)**, **KHÔNG phải dữ liệu Việt Nam**. Chỉ dẫn như *analogue* định lượng. Câu văn **phải nêu tên bộ dữ liệu** |
| ONNX Runtime nhanh gấp ~3,73 lần PyTorch trên CPU i7-13700H (104,61 ms → 28,02 ms) | `ultralytics_2026_benchmark` | Chỉ dùng phần **tốc độ**. Con số **mAP đi kèm đo trên coco8 (8 ảnh)** nên **vô nghĩa về mặt thống kê** — không được trích |
| Tập ký tự seri | `bocongan_2024_tt79` | Loại trừ toàn hệ thống là **5 chữ: I, J, O, Q, W** — **không phải 6**. Chữ **R hợp lệ** ở vị trí seri thứ hai của biển xe máy |
| Kích thước biển số | `bocongan_2024_qcvn08` | Theo **QCVN 08:2024/BCA**, không theo tiêu chuẩn cũ |
| Căn cứ pháp lý biển số | `bocongan_2024_tt79`, `bocongan_2025_tt13`, `bocongan_2025_tt51` | **TT 24/2023/TT-BCA đã HẾT HIỆU LỰC từ 01/01/2025** — chỉ nhắc như bối cảnh lịch sử, không dùng làm căn cứ |
| Mọi số liệu hiệu năng của đồ án | — | Bắt buộc kèm: model CPU, số luồng, kích thước ảnh đầu vào, backend suy luận, cỡ mẫu đo |

### 4.5. Sinh phần Tài liệu tham khảo

Khi ghép quyển:

1. Quét toàn bộ tệp chương, thu thập mọi khoá BibTeX trong comment HTML theo thứ tự xuất hiện.
2. Đánh số `[1]`, `[2]`, … theo thứ tự đó.
3. Thay các số `[n]` tạm thời trong thân bài bằng số đã đánh lại.
4. Sinh mục Tài liệu tham khảo từ `references.bib` theo đúng thứ tự, định dạng IEEE.

Bất biến phải kiểm tra sau khi ghép: **mọi khoá xuất hiện trong thân bài đều có entry trong `.bib`**, và **mọi entry trong danh mục đều được trích ít nhất một lần**.

---

## 5. Cách ghép thành một tệp

### 5.1. Thứ tự ghép

Theo đúng thứ tự số của tên tệp: `01-front-matter.md` → `02-…` → … → `09-phu-luc.md`. Tệp `00-thesis-outline.md` và `THESIS-README.md` là **tài liệu công cụ, KHÔNG ghép vào quyển**.

### 5.2. Ghép thô

```powershell
# Chạy từ thư mục gốc dự án
New-Item -ItemType Directory -Force docs/papers/build
Get-ChildItem docs/papers/0[1-9]-*.md | Sort-Object Name |
    ForEach-Object { Get-Content $_.FullName -Raw; "`n`n---`n`n" } |
    Out-File -Encoding utf8 docs/papers/build/thesis-full.md
```

Lệnh này chỉ nối tệp. Bốn việc **phải làm sau đó**, chưa tự động hoá:

| # | Việc | Trạng thái |
|:-:|---|---|
| 1 | Đánh lại số `[n]` theo thứ tự xuất hiện | Thủ công hoặc script — xem §4.5 |
| 2 | Sinh mục Tài liệu tham khảo từ `references.bib` | Cần script |
| 3 | Sinh mục lục, danh mục hình, danh mục bảng | Công cụ kết xuất lo (xem §5.3) |
| 4 | Đánh số trang (La Mã cho phần đầu, Ả Rập từ Chương 1) | Công cụ kết xuất lo |

### 5.3. Kết xuất sang PDF / Word

Mục lục, danh mục hình, danh mục bảng và số trang **không sinh được từ Markdown thuần**. Chọn một trong hai đường:

| Đường | Cách làm | Lưu ý |
|---|---|---|
| **Pandoc → PDF** | `pandoc thesis-full.md -o thesis.pdf --toc --toc-depth=3 --number-sections` | Cần bộ chữ hỗ trợ tiếng Việt; sơ đồ mermaid phải xuất ra ảnh trước (`mermaid-cli`) |
| **Pandoc → DOCX, hoàn thiện trong Word** | `pandoc thesis-full.md -o thesis.docx --reference-doc=mau-khoa.docx` | Thực tế hơn nếu khoa yêu cầu nộp bản Word theo mẫu; mục lục và danh mục dùng chức năng có sẵn của Word |

> **Khuyến nghị:** đường **DOCX**. Hầu hết khoa yêu cầu nộp bản Word theo biểu mẫu riêng, và các trang biểu mẫu ở `01-front-matter.md` §B (phiếu giao nhiệm vụ, nhận xét của giảng viên) vốn là tài liệu Word do khoa cấp — không có cách nào sinh chúng từ Markdown. **Xác nhận yêu cầu định dạng của khoa trước khi đầu tư công sức vào một đường.**

### 5.4. Kiểm tra trước khi nộp

- [ ] Không còn chỗ nào để nguyên `«…»`
- [ ] Không còn chỗ nào ghi *"sẽ được trình bày ở Chương 5"* trong khi Chương 5 đã có số liệu
- [ ] Hai bản abstract đã cập nhật số liệu thật (xem `01-front-matter.md` §K)
- [ ] Mọi `[n]` trong thân bài đều có entry tương ứng trong Tài liệu tham khảo
- [ ] Mọi hình và bảng đều được nhắc tới trong thân bài
- [ ] Đánh số hình/bảng liên tục, không nhảy cóc, không trùng
- [ ] Không có số liệu nào do `StubPipeline` sinh ra bị trình bày như kết quả thực nghiệm
- [ ] Mọi số của `baseline-416-v1.pt` đều kèm cả hai khiếm khuyết (`imgsz`=416 thay vì 640; split v1 có rò rỉ train↔test) ngay trong câu, và không được trình bày như kết quả đạt chỉ tiêu
- [ ] Mọi tỷ lệ khử trùng lặp đều ghi rõ **mẫu số**: 44,2% là 11.978/27.111 (toàn bộ ảnh của 7 bộ vào hợp nhất detection, trước khi gộp — không phải cả 9 bộ tải về); 47,8% là 7.227/15.133 (corpus đã gộp `merged_v2`, ngưỡng 10)
- [ ] Mọi số liệu hiệu năng đều kèm cấu hình phần cứng
- [ ] Các cảnh báo ở §4.4 còn nguyên vẹn trong văn bản cuối
- [ ] Mục 1.6 (Cấu trúc quyển đồ án) mô tả khớp nội dung thật của sáu chương

---

## 6. Nguyên tắc viết

Rút từ quy tắc của Phase 0–1, áp dụng nguyên cho quyển đồ án:

1. **Không viết về kết quả chưa có.** Cần số liệu thực nghiệm mà chưa đo được thì ghi *"sẽ được trình bày ở Chương 5"*. Không phỏng đoán, không điền số tạm.
2. **Không tô hồng trạng thái dự án.** Phần nào chưa làm thì ghi rõ chưa làm và lý do. Một quyển đồ án trung thực về giới hạn của nó bảo vệ được; một quyển che giấu thì không.
3. **Mỗi chương mở bằng một đoạn dẫn nhập ngắn và đóng bằng một mục tóm tắt chương.** Người đọc phải biết mình sắp đọc gì và vừa đọc được gì.
4. **Không nghiên cứu lại Phase 0–1.** Sáu báo cáo Phase 1 và bộ tài liệu Phase 0 đã qua vòng kiểm chứng đối kháng (phát hiện và sửa 25 lỗi, trong đó 3 lỗi mức critical). Dùng lại, đừng làm lại.
5. **Nêu cả đánh đổi, không chỉ nêu ưu điểm.** Mọi quyết định công nghệ và thiết kế đều phải kèm phương án bị loại và điều kiện mà phương án đó sẽ trở thành lựa chọn đúng. Đây cũng là cách chuẩn bị tốt nhất cho phần hỏi–đáp khi bảo vệ.
6. **Đồng bộ mã nguồn và tài liệu.** Mỗi lần cài đặt thay đổi thì cập nhật chương tương ứng — rủi ro R-06 trong `project-scope.md`.

---

## 7. Việc tiếp theo

| Thứ tự | Việc | Điều kiện |
|:-:|---|---|
| 1 | Viết **Chương 2** — nhiều nguyên liệu nhất, không phụ thuộc gì | ✅ Làm được ngay |
| 2 | Viết **Chương 3** — backend đã chạy, thiết kế đã kiểm chứng | ✅ Làm được ngay |
| 3 | Viết **Chương 1** — viết sau 2 và 3 để phần đóng góp bám sát nội dung thật | Sau bước 1, 2 |
| 4 | Viết Phụ lục A, B, C, D | ✅ Làm được ngay |
| 5 | Điền thông tin cá nhân vào `01-front-matter.md` §A, C, D | Cần thông tin từ người thực hiện |
| 6 | Xác nhận yêu cầu định dạng và biểu mẫu của khoa | Cần liên hệ khoa |
| 7 | **Huấn luyện mô hình** | ⛔ Chặn Chương 4, 5, 6 |
| 8 | Viết Chương 4 → 5 → 6, cập nhật hai abstract | Sau bước 7 |
| 9 | Ghép quyển, đánh lại trích dẫn, kết xuất | Sau bước 8 |

**Bước 7 là nút thắt duy nhất của cả quyển đồ án.** Bốn hạng mục đầu tiên (Chương 1, 2, 3 và bốn phụ lục) — khoảng 60–70 trang, tức quá nửa số trang thân bài — làm được ngay mà không cần chờ gì.
