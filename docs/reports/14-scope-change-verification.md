# 14 — Báo cáo kiểm chứng tài liệu sau khi thu gọn phạm vi giao diện

**Ngày:** 2026-07-20
**Bối cảnh:** gỡ trang Webcam khỏi giao diện web (5 trang → 4 trang) và đồng bộ lại số liệu kiểm thử trong toàn bộ tài liệu.
**Phạm vi rà soát:** tài liệu Markdown (`README.md`, `docs/00-requirements/`, `docs/reports/`, `docs/papers/ch*.md`, `docs/manuals/`) và các tệp phái sinh (`docs/papers/thesis-full.docx`, `docs/slides/slides.pptx`).

---

## 1. Tóm tắt

**Còn 2 lỗi mức critical CHƯA sửa**, cả hai nằm trong tệp trình chiếu `docs/slides/slides.pptx`: slide S16 vẫn ghi giao diện có "5 trang" kèm dòng `/webcam`, và speaker notes vẫn đọc "Giao diện gồm năm trang… Ba trang nhận dạng…" đồng thời chỉ định dùng ảnh `docs/screenshots/webcam.png` (tệp đã bị xoá). Nếu đọc nguyên văn khi bảo vệ thì đây là khẳng định sai trước hội đồng.

Đã sửa xong 10 tệp Markdown: đồng bộ số liệu bộ test lạc hậu (862 thu thập / 861 đạt → **882 thu thập / 881 đạt / 1 xfail / 0 fail**) ở `README.md`, `docs/00-requirements/non-functional-requirements.md`, `docs/00-requirements/timeline.md`, `docs/reports/07-testing-report.md`, `docs/reports/11-definition-of-done.md`, `docs/papers/ch1-mo-dau.md`, `ch4-cai-dat.md`, `ch5-thuc-nghiem.md`, `ch6-ket-luan.md`, `docs/manuals/technical-manual.md`; đồng thời tách bạch hai mốc đo độ bao phủ (87,7% đo 2026-07-20 theo `docs/reports/13-refactor-result.json` và 88,1% đo ở Phase 7 theo `docs/reports/07-testing-report.md`) thay vì trộn lẫn thành một con số.

Phần chưa sửa đều là **tệp phái sinh sinh tự động** (`slides.pptx`, `thesis-full.docx`) — nguồn Markdown của chúng đã đúng, chỉ thiếu bước dựng lại; cộng thêm 1 lỗi mức major trong `docs/slides/README.md` phải sửa tay.

---

## 2. Các thay đổi đã áp dụng

### 2.1 Nhóm tài liệu yêu cầu / báo cáo / README

| Tệp | Nội dung sửa | Lý do |
|---|---|---|
| `docs/reports/07-testing-report.md` | Header dòng 5: "861/862 pass, 1 xfail, 0 fail" → "882 test thu thập / 881 đạt, 1 xfail, 0 fail"; thêm ghi chú ngày cập nhật trỏ tới `13-refactor-result.json` | 862/861 là lần chạy 19/07/2026, đã lạc hậu |
| `docs/reports/07-testing-report.md` | Mục 3.1: bảng 862→882, 861→881; thêm khối "Mốc số liệu" nêu lệnh chạy `backend/.venv/Scripts/python.exe -m pytest -q` từ gốc kho `D:/DATN`, ngày 20/07/2026, nguồn `13-refactor-result.json`; thời gian chạy 15,93 giây (`pytest -q`), chú thích lần chạy Phase 7 có `--cov` mất 36,70 giây | Bảo toàn cả hai số đo thật theo đúng mốc và lệnh, không trộn lẫn |
| `docs/reports/07-testing-report.md` | Mục 3.2: `test_recognizer.py` 23→24; thêm dòng `tests/test_ocr_accuracy.py` = 19 (unit); tổng 862→882; phân bố "668 unit (77,5%) / 176 integration (20,4%) / 18 kiến trúc (2,1%)" → "688 unit (78,0%) / 176 integration (20,0%) / 18 kiến trúc (2,0%)" | Đo lại bằng `pytest --collect-only -q`: 17 tệp cộng đúng 882; sửa tổng mà không sửa thành phần thì bảng tự mâu thuẫn |
| `docs/reports/07-testing-report.md` | Mục 3.3: giữ bảng 88,1% (2.900 stmt) nhưng thêm khối "Hai mốc đo, không được trộn lẫn" — 88,1% đo Phase 7 ngày 19/07/2026; 87,7% (2.931 stmt, 317 miss) đo lại 20/07/2026 theo `13-refactor-result.json`; NFR-M2 đạt ở cả hai mốc | Ghi rõ mốc và nguồn, không hợp nhất hai con số bao phủ |
| `docs/reports/07-testing-report.md` | Bảng đối chiếu NFR (dòng NFR-M2): ghi cả 88,1% (Phase 7) và 87,7% (đo lại 20/07/2026) | Như trên |
| `docs/reports/07-testing-report.md` | Mục 10 Kết luận: "861/862 test pass, 0 fail, 88,1% bao phủ" → "881/882 test pass, 1 xfail, 0 fail" kèm hai mốc bao phủ có nguồn | Đồng bộ với sự thật và quy tắc ghi nguồn |
| `docs/00-requirements/non-functional-requirements.md` | Dòng 160 (NFR-M2): sửa cặp số test và tách hai mốc bao phủ 87,7% / 88,1% kèm nguồn | Sửa số test lạc hậu, ghi rõ nguồn |
| `docs/00-requirements/timeline.md` | Dòng 138 (Phase 7): "861/862 test pass, bao phủ 88,1%" → "882 thu thập / 881 đạt / 1 xfail, 0 fail; bao phủ 87,7% (20/07/2026, `13-refactor-result.json`; Phase 7 trước đó 88,1%)" | Như trên |
| `README.md` | Dòng 73 (bảng tiến độ Phase 7), dòng 90 (mục Kiểm thử, bổ sung lệnh chạy thật), dòng 168 (bảng tài liệu) | Sửa số test lạc hậu, ghi kèm mốc đo cho bao phủ |
| `docs/reports/11-definition-of-done.md` | Mục 10 và 11: bổ sung số có nguồn — 688 unit + 18 kiến trúc, 176 tích hợp, tổng 882 thu thập / 881 đạt / 1 xfail / 0 fail (`13-refactor-result.json`, 20/07/2026) | Trước đó phần bằng chứng không có số nào để đối chiếu |
| `docs/reports/11-definition-of-done.md` | Mục 12: "07-testing-report.md (1062)" → "(1.046 dòng)" | Đo bằng `wc -l`; con số 1062 không khớp kể cả trước khi sửa |

### 2.2 Nhóm luận văn và sổ tay kỹ thuật

| Tệp | Nội dung sửa | Lý do |
|---|---|---|
| `docs/papers/ch1-mo-dau.md` | Mục 1.6.2 (dòng 326): "88,1% ở tầng nghiệp vụ (42,0% toàn kho), với 861 test đạt / 1 xfail" → "87,7% tầng nghiệp vụ (đo 2026-07-20, `13-refactor-result.json`; Phase 7 trước đó 88,1% theo `07-testing-report.md`; 42,0% toàn kho), với 882 test thu thập / 881 đạt / 1 xfail / 0 thất bại" | Số test lạc hậu; bao phủ giữ cả hai mốc kèm nguồn |
| `docs/papers/ch4-cai-dat.md` | Mục 4.8 (dòng 1311): bao phủ tầng nghiệp vụ 88,1% → 87,7% (đo 2026-07-20, `13-refactor-result.json`), vẫn giữ 88,1% + 42,0% kèm nguồn `07-testing-report.md` | Ghi rõ nguồn và mốc, không trộn lẫn |
| `docs/papers/ch4-cai-dat.md` | Mục 4.8 (dòng 1313, khung "Ghi chú về số lượng test"): viết lại toàn bộ — 882 thu thập / 881 pass / 1 xfail / 0 fail / 0 skip / 0 error / 17 cảnh báo, nêu rõ lệnh chạy và ngày 2026-07-20; nói rõ cặp 862/861 là lần chạy cũ đã bị thay; giữ ghi chú về con số 199 lạc hậu | Đây là khung ghi chú chuyên về số lượng test nên phải khớp tuyệt đối, đồng thời không xoá dấu vết số cũ |
| `docs/papers/ch5-thuc-nghiem.md` | Bảng tổng hợp NFR (dòng 856): M2 88,1% → 87,7% (2026-07-20) | Đồng bộ với số đo mới nhất, ghi mốc ngay trong ô |
| `docs/papers/ch5-thuc-nghiem.md` | Mục 5.9.2 (bảng kết quả kiểm thử): 862→882, 861→881, thêm dòng "Số test skip = 0"; tách bao phủ thành 3 dòng (87,7% đo 2026-07-20; 88,1% đo Phase 7; 42,0% toàn kho Phase 7); thêm khung "Nguồn và mốc đo"; sửa câu kế tiếp thành "Chênh lệch giữa 88,1% và 42,0% (cùng một mốc đo Phase 7)" | Đây là bảng số liệu kiểm thử chính của luận văn, phải khớp 882/881/1 và nêu rõ nguồn + mốc |
| `docs/papers/ch5-thuc-nghiem.md` | Mục 5.9.2: bổ sung tên đầy đủ và nguyên nhân của test xfail duy nhất — `tests/integration/test_api_detection.py::TestErrorBodies::test_a_failed_image_detection_records_the_failed_job` (`_fail_job` gọi `db.rollback()` trước khi ghi, `_create_job` mới chỉ `flush`) | Đoạn văn yêu cầu "phải được nêu tên và giải thích khi công bố" nhưng lại không nêu tên; thông tin lấy từ `xfail_reason` trong `13-refactor-result.json` |
| `docs/papers/ch5-thuc-nghiem.md` | Kết luận chương (dòng 980): "88,1%, 861/862 test pass" → "87,7% (đo 2026-07-20), 881/882 test pass" | Đồng bộ với bảng 5.9.2 |
| `docs/papers/ch6-ket-luan.md` | Bảng tổng kết phase (dòng 24): Phase 7 → 882/881/1 xfail/0 fail/0 skip kèm ngày và tệp nguồn; bao phủ 87,7% và 88,1% đều dẫn nguồn | Số test lạc hậu; bao phủ cần ghi rõ nguồn và mốc |
| `docs/papers/ch6-ket-luan.md` | Bảng đối chiếu NFR (dòng 57): "88,1% (861/862 pass)" → "87,7% đo 2026-07-20 (881/882 pass, 1 xfail); trước đó Phase 7 đo 88,1%" | Như trên |
| `docs/manuals/technical-manual.md` | Cây thư mục (dòng 168): chú thích "862 test được thu thập" → "882 test được thu thập" | Số test lạc hậu |
| `docs/manuals/technical-manual.md` | Mục 11.4: bảng bao phủ đổi thành 3 dòng có cột "Mốc đo và nguồn" (87,7% → `13-refactor-result.json`; 88,1% Phase 7 → `07-testing-report.md`; 42,0% toàn kho Phase 7); thêm khung cảnh báo "Hai con số bao phủ, hai mốc đo"; viết lại đoạn số liệu kiểm thử với lệnh chạy thật và ngày | Đây là mục định nghĩa chuẩn cách trích số liệu kiểm thử của toàn dự án |
| `docs/manuals/technical-manual.md` | Bảng trạng thái kiểm chứng (dòng 1301): 862/861 → 882 thu thập; 881 pass, 1 xfail, 0 fail, 0 skip, 17 cảnh báo (chạy 2026-07-20); bao phủ tách hai mốc có nguồn | Đồng bộ với mục 11.4 |

---

## 3. Lỗi đã được xác minh nhưng CHƯA sửa

Sắp xếp theo mức độ nghiêm trọng. Cả ba lỗi đều đã được kiểm chứng độc lập (đọc lại tệp / giải nén tệp nén / đối chiếu mã nguồn), không bác bỏ được.

| # | Mức | Tệp / vị trí | Nội dung sai | Đề xuất sửa cụ thể |
|---|:--:|---|---|---|
| 1 | **critical** | `docs/slides/slides.pptx`, slide 37 (S16 — Giao diện hệ thống) | Ghi "5 trang trong một khung ứng dụng chung:" kèm bảng 5 dòng, trong đó có `/webcam — Thời gian thực` và `/ — Tổng quan` là trang chủ. Thực tế: 4 trang, `/` là Nhận dạng ảnh, không còn route `/webcam` (`frontend/src/App.tsx`) | **Không vá tay XML.** Chạy `backend/.venv/Scripts/python.exe scripts/build_thesis.py` từ gốc kho `D:/DATN` (Pandoc đã có sẵn tại `tools/pandoc-3.10/pandoc.exe`). Nguồn `docs/slides/10-slides-outline.md:635-645` ĐÃ đúng ("4 trang…", bảng `/` · `/video` · `/history` · `/dashboard`, ghi chú "Chế độ thời gian thực (webcam) giữ ở tầng API — `POST /api/detect/frame`… trang Webcam đã gỡ khỏi giao diện 2026-07-20"), chỉ thiếu bước dựng lại. Kiểm chứng sau khi dựng: giải nén rồi `grep -il webcam ppt/slides/*.xml` — slide37/slide38 phải không còn trúng |
| 2 | **critical** | `docs/slides/slides.pptx`, slide 38 (speaker notes S16) | Câu đọc khi bảo vệ: "Giao diện gồm năm trang: tổng quan, nhận dạng ảnh, nhận dạng video, webcam và lịch sử. Ba trang nhận dạng là nguồn sinh dữ liệu…"; đồng thời chỉ định dùng ảnh `webcam.png` — tệp đã bị xoá, `docs/screenshots/` chỉ còn 4 ảnh | Sửa cùng lúc với #1 bằng một lần chạy `scripts/build_thesis.py`. Nội dung đúng đã có trong outline (`10-slides-outline.md:667`): "Giao diện gồm bốn trang: nhận dạng ảnh (trang chủ), nhận dạng video, lịch sử và tổng quan. Hai trang nhận dạng là nguồn sinh dữ liệu… Chế độ thời gian thực qua webcam vẫn còn ở tầng API — endpoint `POST /api/detect/frame` — chỉ là em đã gỡ trang giao diện tương ứng để thu gọn phần demo." Mục Hình/Bảng phải còn 4 ảnh và "(2 ảnh nhỏ xếp hàng dưới)". **Lưu ý:** các chỗ nhắc "webcam" ở slide42/43/44 (NFR-P2/P3) nói về chỉ tiêu ở tầng API, hợp lệ, KHÔNG được xoá |
| 3 | **major** | `docs/papers/thesis-full.docx` (bản Word nộp kèm) | 4 chỗ còn mô tả frontend hiện có 5 trang gồm `WebcamDetection`: "gồm 5 trang và khoảng 50 mô-đun .tsx/.ts", "pages/ 5 trang: Dashboard, ImageDetection, VideoDetection, WebcamDetection, History", "tầng frontend (5 trang, khoảng 50 mô-đun…)" + bao phủ 88,1% không nêu mốc, "phủ năm màn hình (Dashboard, Nhận dạng ảnh, Video, Webcam, Lịch sử)." (mất mệnh đề "tại thời điểm chốt phase"). Bản .docx còn tự mâu thuẫn: một đoạn khác (từ `ch3`) đã nói màn hình Webcam "đã được gỡ khỏi giao diện" | **Không sửa tay .docx.** Chạy `scripts/build_thesis.py` — script ghép `01-front-matter.md` + `ch1..ch6` rồi gọi Pandoc xuất `thesis-full.docx`. Các chương gốc đã đúng (`ch4-cai-dat.md:936-937` ghi "pages/ 4 trang…", `:1311` ghi "4 trang sau thu gọn phạm vi 2026-07-20, 60 mô-đun" + bao phủ 87,7% có nguồn; `ch6-ket-luan.md:23` có mệnh đề "tại thời điểm chốt phase"). Kiểm chứng sau khi dựng: trong `word/document.xml` kỳ vọng "5 trang" = 0 lần, "WebcamDetection" = 1 lần (ghi chú lịch sử ở mục 4.4.1), "năm màn hình" = 2 lần (đều có mệnh đề giới hạn thời gian) |
| 4 | **major** | `docs/slides/README.md:168` và `:193` (kéo theo `:192`) | Dòng 168: "\| 14 \| Ảnh chụp 5 trang giao diện \| S16, poster Khối 8 \| ✅ Đã có ở `docs/screenshots/` \| ✅ \|" — sai số lượng (4 trang, 4 ảnh) và sai trạng thái. Dòng 193: "5 ảnh trong `docs/screenshots/`", trạng thái ✅ Xong. Mâu thuẫn với chính các tệp cùng thư mục (`10-slides-outline.md:51,656,661-663` và `10-defense-qa.md:925,927` đều ghi ⚠️ "phải chụp lại 4 ảnh này trước khi nộp") | Sửa tay 3 dòng: (a) dòng 168 → "Ảnh chụp **4** trang giao diện … Có sẵn 4 tệp (`image-detection` · `video-detection` · `history` · `dashboard`) nhưng chụp khi sidebar còn 5 mục — **phải chụp lại trước khi nộp**", trạng thái ⚠️; (b) dòng 193 → "⚠️ Cần chụp lại \| 4 ảnh trong `docs/screenshots/`, chụp trước 20/7 khi sidebar còn 5 mục và trang chủ còn là Tổng quan"; (c) dòng 192 → "Hình minh hoạ \| ⬜ 0/14 \| 13 hình vẽ/render cần làm + 4 ảnh chụp giao diện cần chụp lại". Không đụng vào các số đo thực nghiệm ở dòng 195–197 |

**Bằng chứng còn hiệu lực tại thời điểm viết báo cáo (kiểm tra lại 2026-07-20):**

- `docs/slides/slides.pptx` sửa lúc 13:56, `docs/slides/10-slides-outline.md` sửa lúc 14:15 → pptx là bản dựng cũ, chưa sinh lại.
- `docs/papers/thesis-full.docx` 13:56 < `thesis-full.md` 14:13 < `ch4-cai-dat.md` 14:14 → cả bản hợp nhất Markdown lẫn .docx đều dựng trước khi các chương được sửa. **Do đó phải dựng lại cả `thesis-full.md`, không chỉ .docx.**
- `docs/screenshots/` hiện có đúng 4 tệp: `dashboard.png`, `history.png`, `image-detection.png`, `video-detection.png`.
- `docs/slides/README.md:168` và `:193` vẫn còn nguyên văn như mô tả.
- `tools/pandoc-3.10/pandoc.exe` tồn tại → không có rào cản kỹ thuật cho bước dựng lại.

---

## 4. Điểm còn nghi ngờ / cần người quyết

| # | Vấn đề | Trạng thái | Cần gì |
|---|---|---|---|
| 1 | `README.md:70` ghi Phase 4 "145 test pass" | **Không tìm được nguồn.** Đây không phải tổng số test của bộ test nên không thuộc diện sửa thành 882. `grep '145'` trong `docs/reports/04-ocr-report.md` không khớp. Đếm thực tế các tệp test liên quan OCR hiện nay: `test_normalizer` 79 + `test_two_line` 28 + `test_recognizer` 24 = 131; cộng thêm `test_plate_rules` 140 = 271 — không tổ hợp nào ra 145. Đã **giữ nguyên**, không tự đặt số mới | Người có ngữ cảnh Phase 4 xác định 145 gồm những tệp nào; nếu không xác định được thì nên bỏ con số này khỏi README thay vì để không nguồn |
| 2 | Bảng bao phủ chi tiết theo module trong `07-testing-report.md` mục 3.3 (stmt/miss/cover từng module, tổng 2.900/305/88,1%) | Vẫn là số của lần đo 19/07/2026, đã đánh dấu rõ mốc thay vì thay bằng số 20/07/2026 | `13-refactor-result.json` chỉ ghi phần trăm từng module, không ghi stmt/miss nên không tái dựng được bảng tương đương. Muốn có bảng theo mốc mới thì phải chạy lại `pytest --cov` và ghi lại toàn bộ bảng |
| 3 | 4 ảnh chụp giao diện hiện có | Chụp khi sidebar còn 5 mục và trang chủ còn là Tổng quan → **không khớp giao diện 4 trang hiện tại** | Chụp lại 4 ảnh trước khi nộp. Đây là việc tách bạch với các lỗi ở mục 3, nhưng nếu không làm thì slide S16 dù dựng lại vẫn minh hoạ sai |
| 4 | `docs/papers/thesis-full.md` (bản hợp nhất Markdown) | Đếm được **0** lần xuất hiện của "phiên bản trước đó có trang thứ năm", "tại thời điểm chốt phase" và "87,7" → được ghép từ trạng thái chương TRƯỚC khi sửa | Xác nhận quy trình: mỗi lần sửa `ch*.md` phải chạy lại `scripts/build_thesis.py`. Cân nhắc thêm một bước kiểm tra CI so sánh `thesis-full.md` với bản ghép mới nhất để chống tái phát |
| 5 | Slide 42/43/44 trong `slides.pptx` cũng trúng `grep webcam` | Đã đánh giá sơ bộ là **hợp lệ** (nói về chỉ tiêu NFR-P2/P3 ở tầng API `POST /api/detect/frame`, không phải trang giao diện) | Sau khi dựng lại, đọc lại 3 slide này một lượt để chắc chắn không có khẳng định nào về TRANG webcam |
| 6 | Dữ liệu đầu vào của báo cáo này bị cắt cụt | Danh sách `unresolved` của đợt sửa nhóm luận văn bị cắt giữa chừng tại chuỗi "ch5-thuc-nghiem.md dòng…" | Có thể còn 1 mục tồn đọng liên quan `ch5-thuc-nghiem.md` chưa được ghi vào báo cáo này. Cần rà lại `ch5-thuc-nghiem.md` một lượt trước khi coi đợt kiểm chứng là đóng |

---

## 5. Việc cần làm tiếp, theo thứ tự

1. Chạy `backend/.venv/Scripts/python.exe scripts/build_thesis.py` từ gốc kho — xử lý dứt điểm lỗi #1, #2 (critical) và #3 (major) trong cùng một lần.
2. Kiểm chứng lại bằng các lệnh grep nêu ở mục 3 (kỳ vọng: `"5 trang"` = 0 trong cả pptx lẫn docx).
3. Sửa tay 3 dòng trong `docs/slides/README.md` (lỗi #4).
4. Chụp lại 4 ảnh giao diện.
5. Quyết định về con số "145 test" ở `README.md:70`.
6. Rà lại `docs/papers/ch5-thuc-nghiem.md` do dữ liệu đầu vào bị cắt cụt (mục 4.6).
