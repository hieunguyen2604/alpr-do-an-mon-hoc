# Bộ ảnh test mở rộng — 23 ảnh, đủ các loại biển

Sinh bằng `python scripts/make_demo_media.py` (chọn lọc tự động, seed 42) từ
các nguồn **đã có sẵn trên máy và đã thẩm định giấy phép** trong
[17-plate-type-dataset-survey.md](../../docs/reports/17-plate-type-dataset-survey.md).
Không tải gì mới từ mạng: clip/ảnh trôi nổi không xác minh được giấy phép và
không có ground truth, còn bộ này tái tạo được từ script.

Khác với `demo/images/` (bộ lõi 16 ảnh có `expected.json` là ground truth đầy
đủ 6 trường), thư mục này là **bộ test mở rộng**: ground truth ghi ở bảng dưới
(từ tên file gốc hoặc đọc bằng mắt), kết quả hệ thống lưu ở `results.json`
(đo 2026-07-21 qua `POST /api/detect/image` trên stack Docker).

## Nguồn và ground truth

| Nhóm | Tệp | Ground truth | Nguồn / giấy phép |
|---|---|---|---|
| Vàng kinh doanh | `vang-79E00392` `vang-50F01690` `vang-61C15282` | 79E-003.92 · 50F-016.90 · 61C-152.82 (chuỗi nằm trong tên file gốc) | Roboflow plate-color, CC BY 4.0 |
| Xanh nhà nước | `xanh-86A00519` `xanh-80A04285` `xanh-85A00190` | 86A-005.19 · 80A-042.85 · 85A-001.90 | Roboflow plate-color, CC BY 4.0 |
| Xanh (Commons) | `xanh-nha-nuoc-commons` | 50A-004.24 | Wikimedia Commons |
| Đỏ quân đội | `quan-doi-commons` | KP-49-99 | Wikimedia Commons |
| Ngoại giao | `ngoai-giao-commons-1` `ngoai-giao-cd` `ngoai-giao-ng-651-01` | 41-606-NG-10 · 41-456-NG-01 · NG-651-01 | Wikimedia Commons |
| Rơ moóc (seri R) | `ro-mooc` | 61R-023.09 | Wikimedia Commons |
| Xe buýt / xe tải | `xe-buyt` `xe-tai` | 51B-098.65 · 67C-108.15 (đều biển 2 dòng nền trắng) | Wikimedia Commons |
| Ô tô (crop) | `o-to-72A07604` | 72A-076.04 | Wikimedia Commons |
| Cảnh phố 1 biển | `canh-mot-bien-1..3` | (2) 79A-187.68 · (3) 67-H1 480.66; (1) tối, người đọc khó | tập test yolo_v3 — split giữ riêng, chưa từng vào train |
| Cảnh phố nhiều biển | `canh-nhieu-bien-1..5` | nhiều biển/cảnh, xem ảnh | tập test yolo_v3 |

## Kết quả hệ thống đáng chú ý (2026-07-21, chi tiết ở `results.json`)

- **Đúng hoàn toàn:** 4/4 biển xanh (kind `blue_car`), `72A-076.04`,
  `41-606-NG-10` (diplomatic), `61R-023.09` ra đúng kind **special** — bằng
  chứng sống cho quyết định charset 36 ký tự (seri `R` hợp lệ).
- **Giới hạn đã biết, lộ đúng:** biển đỏ template và NG-651-01 (ảnh
  scan/template) **không được detector phát hiện** — khớp khoảng trống dữ
  liệu huấn luyện ghi ở khảo sát 17; `xe-tai`/`vang-61C15282` (biển ô tô
  2 dòng 8 ký tự) rơi vào prior xe máy — ca mơ hồ đã mô tả trong luận văn;
  `vang-79E00392` đọc nhầm E→B.
- Trong `canh-nhieu-bien-3` có một vùng **nền đỏ** được phát hiện nhưng không
  đọc được — và **không** bị bậc thang thử-lại bịa thành biển dân sự: cổng
  chặn nền đỏ hoạt động.

## Hai video test sinh kèm

| Video | Nội dung | Kết quả đo |
|---|---|---|
| `demo-video-cac-loai-bien.mp4` (25s) | 10 ảnh loại biển, zoom chậm + vài đoạn nghiêng 3–4° | 11 bản ghi: quân đội `KP4999` phát hiện được ở video (ảnh tĩnh thì không) và **giữ đúng invalid**; xe buýt đọc đủ `51B09865`; 2 biến thể sai từ đoạn nghiêng |
| `demo-video-giao-thong.mp4` (20s) | 8 cảnh phố thật, có 2 đoạn nghiêng 5–6° | 29 bản ghi; các đoạn nghiêng làm OCR sinh **biến thể sai-nhưng-hợp-lệ cách nhau ≥2 phép sửa** (ví dụ `48L52201` → 7 dị bản), vượt ngưỡng gộp bảo thủ ≤1 — đây là **stress test có chủ đích**, minh hoạ trực quan cho giới hạn ghi ở `docs/reports/21-skew-retry.md` |
