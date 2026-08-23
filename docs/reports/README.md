# Bảng ánh xạ NFR → tệp nguồn chuẩn

> Quy tắc **"Một số liệu — một nguồn"** định nghĩa ở
> [`AGENTS.md` §9.1](../../AGENTS.md). Khi cần con số nào trong bảng dưới, mở
> **đúng tệp** ở cột "Nguồn duy nhất" — không trích từ tệp khác kể cả khi giá
> trị "trông giống". Sửa nguồn → chạy lại checklist đồng bộ (AGENTS.md §9.2).

## Chỉ tiêu đang hiện hành

| NFR | Ý nghĩa | Giá trị hiện hành | Nguồn duy nhất |
|---|---|---|---|
| A1/A2/A3a/b | Detection: P · R · mAP@0.5 · mAP@0.5:0.95 (`best.pt`, split v3) | 0,9837 / 0,9714 / **0,9829** / 0,7834 | [`05-results.json`](05-results.json) → khóa `T5.5a` |
| A4/A5/A6 | OCR mức ký tự · chuỗi trước hậu xử lý · chuỗi sau hậu xử lý (2.801 biển) | 0,9483 / 0,6373 / **0,7701** | [`40-ocr-accuracy-measured-confusion.json`](40-ocr-accuracy-measured-confusion.json) — bảng đọc nhanh ở [`41-measured-confusion-tables.md`](41-measured-confusion-tables.md) |
| Chênh 1 dòng / 2 dòng (A6) | Khoảng cách bố cục | **23,07 điểm** (0,9541 vs 0,7234) | như dòng trên |
| Đóng góp hậu xử lý | A6 − A5 | **+13,28 điểm** (372 biển sửa đúng, 0 hỏng) | như dòng trên |
| A7 | Độ chính xác đầu–cuối | 0,563 *(nhãn máy sinh, không đại diện)* | [`40-ocr-accuracy-measured-confusion.json`](40-ocr-accuracy-measured-confusion.json) |
| P1 | Độ trễ E2E p95 | **1.143,10 ms** 🟡 (median 405,77 ms) | [`27-retry-ladder-cost-benefit.md`](27-retry-ladder-cost-benefit.md) — ⬜ rà thêm tệp JSON thô của lượt đo nếu có |
| P2 | FPS luồng khung hình (tầng API) | **5,257 FPS** ✅ | [`33-runtime-nfr.json`](33-runtime-nfr.json) |
| P3 | Tốc độ video | 0,785× ✅ | [`33-runtime-nfr.json`](33-runtime-nfr.json) |
| R4 | Soak liên tục | 15 phút · 2.028 request · 100% | [`33-runtime-nfr.json`](33-runtime-nfr.json) |
| R5 | CSDL sống qua restart | 0/9.031 bản ghi mất | [`33-runtime-nfr.json`](33-runtime-nfr.json) |
| P4/P4b/P5/P6/P7 | Nạp mô hình · overhead API · truy vấn CSDL · RSS | 8,36 s · 19,01 ms · 18,71 ms · ≤0,81 GB | bộ [`07-*.json`](.) của Phase 7 — ⬜ chốt tệp đơn cho từng chỉ tiêu khi rà tiếp |
| E2E trong Docker | p95 30 ảnh test | 319 ms *(không phải số NFR-P1)* | [`08-deployment-guide.md`](08-deployment-guide.md) §6.1 |
| Kiểm thử | Số test · coverage tầng nghiệp vụ | 1.002/1.002 · 87,7% | lượt chạy pytest 13/08 + [`13-refactor-result.json`](13-refactor-result.json) |
| Dữ liệu v3 | Quy mô · split · khử trùng lặp · rò rỉ tồn dư | 15.133 ảnh (10.592/3.027/1.514); 44,2%; d=12 còn 791 cặp | [`02-dataset-report.md`](02-dataset-report.md) |

## Vòng đo đã NGHỈ HỮU — không trích làm kết quả

| Tệp / con số | Thay thế bằng | Lý do |
|---|---|---|
| `04-ocr-accuracy.json`, `05-ocr-accuracy.json`, `16-*`, `26-*` (OCR) | `40-ocr-accuracy-measured-confusion.json` | đo trước khi sửa `L→4`, `7→Z` trong `plate_rules.py` |
| `gap 25,45` / `A6 = 0,7512` / `A4 = 0,9454` | 23,07 / 0,7701 / 0,9483 | cùng vòng cũ nêu trên |
| P1 = 5.857 ms | 1.143,10 ms | epoch 7 + máy bận ~793% CPU + lỗi crop — bị bác bỏ trong [`07-benchmark-p1-resolved.json`](07-benchmark-p1-resolved.json) |
| P1 = 731,15 / 780,36 ms | 1.143,10 ms | lần đo 20/07, trước khi nối bậc thang thử-lại |
| P2 = 2,379 FPS | 5,257 FPS | máy bận ~560% CPU — bị bác bỏ trong [`38-runtime-backend-and-nfr-p2.md`](38-runtime-backend-and-nfr-p2.md) |
| Soak 185 req/300 s · 3.928 req | 2.028 req/15 phút | các lượt soak trước, đặc tả yêu cầu 60 phút nên mọi phiên bản đều mới là bằng chứng một phần |
| `882 test / 881 đạt` · coverage 88,1% | 1.002/1.002 · 87,7% | lượt chạy cũ |
