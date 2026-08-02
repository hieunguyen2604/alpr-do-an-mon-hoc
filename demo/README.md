# Ảnh demo

Thư mục này có ba lớp tài nguyên:

1. **Bộ lõi** `images/` (16 ảnh) + `demo-video.mp4` — dùng trong kịch bản
   bảo vệ, có ground truth đầy đủ trong `expected.json`.
2. **Bộ mở rộng** `images-extra/` (23 ảnh, đủ các loại biển: vàng, xanh, đỏ
   quân đội, ngoại giao, rơ moóc, xe buýt/tải, cảnh phố) — xem
   [images-extra/README.md](images-extra/README.md).
3. **Hai video test sinh thêm** `demo-video-cac-loai-bien.mp4` (đủ loại biển)
   và `demo-video-giao-thong.mp4` (cảnh phố + đoạn nghiêng chủ đích).
   Tất cả tái tạo được bằng `python scripts/make_demo_media.py`.

## Nhóm 1 — chọn tự động từ tập test (hf_vn_plates), seed 42

| Tệp | Loại | Số biển | Aspect ratio | Nguồn |
|---|---|---:|---:|---|
| `1dong-1.png` | 1dong | 1 | 3.34 | `hf_vn_plates_segment_000255.png` |
| `1dong-2.png` | 1dong | 1 | 3.17 | `hf_vn_plates_segment_000061.png` |
| `1dong-3.png` | 1dong | 1 | 3.88 | `hf_vn_plates_segment_000629.png` |
| `2dong-1.png` | 2dong | 1 | 1.14 | `hf_vn_plates_segment_002089.png` |
| `2dong-2.png` | 2dong | 1 | 1.15 | `hf_vn_plates_segment_001996.png` |
| `2dong-3.png` | 2dong | 1 | 1.16 | `hf_vn_plates_segment_001494.png` |
| `nhieu-bien-1.png` | nhieu-bien | 3 | 1.36 | `hf_vn_plates_segment_002680.png` |
| `nhieu-bien-2.png` | nhieu-bien | 4 | 1.61 | `hf_vn_plates_segment_000790.png` |
| `nhieu-bien-3.png` | nhieu-bien | 3 | 1.59 | `hf_vn_plates_segment_002635.png` |
| `khong-co-bien-so.jpg` | không biển | 0 | — | ca âm tính (negative case) |

## Nhóm 2 — bổ sung phủ đủ loại biển (thêm 2026-07-20, commit `d336b07`)

Nguồn: các bộ công khai đã thẩm định trong
[docs/reports/17-plate-type-dataset-survey.md](../docs/reports/17-plate-type-dataset-survey.md)
(giấy phép do người đăng tự khai — xem cảnh báo trong khảo sát).

| Tệp | Loại biển | Số biển |
|---|---|---:|
| `bien-vang-kinh-doanh.jpg` | vàng (xe kinh doanh) | 1 |
| `bien-xanh-nha-nuoc.jpg` | xanh (cơ quan nhà nước), số 4 chữ số | 1 |
| `bien-xanh-nha-nuoc-2.jpg` | xanh (cơ quan nhà nước), 2 dòng | 1 |
| `bien-do-quan-doi.jpg` | đỏ (quân đội) — ca nhận-để-loại-trừ | 1 |
| `bien-ngoai-giao-ng.jpg` | ngoại giao NG | 1 |
| `bien-ngoai-giao-51ng.jpg` | ngoại giao dạng không chuẩn | 1 |

## `expected.json` — ground truth do người xác minh

Mỗi phần tử ghi **những gì thật sự in trên biển**, xác minh bằng mắt trên ảnh
phóng to (2026-07-21). Đây là **ground truth, không phải kết quả hệ thống**:

- Bản đầu tiên (commit `d336b07`) ghi *kết quả đo được của hệ thống tại thời
  điểm đó*; bản hiện tại đã đổi ngữ nghĩa sang ground truth sau khi rà từng
  ảnh, sửa 2 nhãn sai (`2dong-3`, `nhieu-bien-1[0]` là xe máy seri P5/P2,
  không phải ô tô) và bổ sung các biển đọc thiếu.
- Trường `note` ghi lý do sửa và các ca hệ thống hiện còn đọc sai — đó là
  hạn chế OCR biển 2 dòng đã mô tả trong Chương 6 luận văn, không giấu.
- Biển mờ/che khuất đến mức người cũng không đọc được thì ghi `plate: ""`.

### Vòng xác minh thứ hai — 2026-08-02, sửa 5 nhãn trong `images-extra/results.json`

Năm biển bị ghi sai **cả cách nhóm chữ số lẫn loại xe**: chúng là biển 2 dòng
của ô tô / xe tải nhưng bị gán `motorcycle_old`, kéo theo chuỗi hiển thị sai.

| Ảnh | Biển vật lý ghi | Nhãn cũ | Đã sửa |
|---|---|---|---|
| `xe-tai.jpg` | `67C` / `108.15` | `67C1-0815` | `67C-108.15` |
| `vang-61C15282.jpg` | `61C` / `152.82` | `61C1-5282` | `61C-152.82` |
| `canh-nhieu-bien-2.png` | `51C` / `920.87` | `51C9-2087` | `51C-920.87` |
| `canh-nhieu-bien-2.png` | `51H` / `609.69` | `51H6-0969` | `51H-609.69` |
| `canh-nhieu-bien-3.png` | `51H` / `145.73` | `51H1-4573` | `51H-145.73` |

**Bằng chứng là dấu chấm in trên chính tấm biển.** Biển Việt Nam chỉ in dấu
chấm trước hai chữ số cuối khi số đăng ký có **5 chữ số**, và chỉ cách đọc ô tô
mới có số 5 chữ số. Thấy `108.15` trên biển là biết sê-ri dừng ở `C`.

**Hai nhãn KHÔNG sửa, vì ở đó nhãn mới đúng còn hệ thống sai:** `60F16272`
(biển ghi `60-F1` / `6272`) và `77H54374` (ghi `77-H5` / `4374`) — không dấu
chấm, số 4 chữ số, sê-ri hai ký tự. Hai ca này dẫn tới việc thêm cột
`upper_char_count` (xem Nhật ký quyết định trong `CLAUDE.md`, 02/08/2026).

Sau vòng này bộ demo đạt **46/49 biển đúng hoàn toàn**, **0 ca lệch cách nhóm
hiển thị**; 3 ca còn lại là lỗi OCR thật trên ảnh nhiều biển, không phải lỗi
trình bày.

Đối chiếu tự động: script eval trong quá trình phát triển bắn từng ảnh vào
`POST /api/detect/image` rồi so `plate/display/kind/color/valid/lines` với
file này.
