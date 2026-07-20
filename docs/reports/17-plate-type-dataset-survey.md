# Khảo sát nguồn dữ liệu bổ sung theo LOẠI BIỂN SỐ (vàng / xanh / đỏ / ngoại giao)

**Ngày:** 2026-07-20
**Phạm vi:** chỉ tìm và thẩm định nguồn công khai (Roboflow Universe, Kaggle). **Chưa tải file nào về máy.**

---

## 1. Vấn đề cần giải quyết

Chạy bộ phân loại màu nền lên toàn bộ 2.801 ảnh biển số Việt Nam có nhãn ký tự hiện có của dự án, kết quả đo được:

| Loại biển | Số ảnh | Tỷ lệ |
|---|---:|---:|
| Trắng (dân sự) | 2.736 | 97,7 % |
| Vàng (kinh doanh vận tải) | 20 | 0,7 % |
| Xanh (cơ quan Nhà nước) | 4 | 0,1 % |
| Đỏ (Quân đội) | 0 | 0 % |
| NG / QT (ngoại giao) | 0 | 0 % |

Hệ quả: **không thể công bố độ chính xác theo loại biển.** Với biển vàng (n=20) và biển xanh (n=4), mọi con số độ chính xác đều không có ý nghĩa thống kê; với biển đỏ và biển ngoại giao thì đơn giản là **không đánh giá được**, vì tập kiểm thử không chứa mẫu nào.

**Kết luận ngắn:** đã tìm được nguồn công khai lấp được **cả 4 loại biển thiếu**, nhưng ở mức độ rất chênh lệch — biển vàng được lấp dồi dào (thêm ~694 ảnh), biển xanh và biển đỏ chỉ đủ để báo cáo định tính (vài chục ảnh gốc), biển ngoại giao gần như không lấp được (~18 ảnh gốc). **Biển chuyên dùng (LD, DA, RM, HC, KT, CD, T) thì không tìm được nguồn nào.**

---

## 2. Các bộ dữ liệu DÙNG ĐƯỢC (xếp theo mức bù đắp loại biển hiếm)

Thứ tự dưới đây ưu tiên bộ lấp được loại biển đang có **0 ảnh** (đỏ, ngoại giao), sau đó tới bộ lấp được khối lượng lớn nhất.

| # | Tên bộ | Nguồn | Số ảnh | Loại biển bù được | Giấy phép | Lệnh tải |
|---|---|---|---:|---|---|---|
| 1 | **Vietnamese Car License Plate** (Cuong Ta) | Roboflow `cuong-ta-ulxex/vietnamese-car-license-plate/1` | 8.255 ảnh / 8.446 hộp nhãn (1 lớp `plate`) | **Đỏ Quân đội: 541 file (~114 ảnh gốc)** — đã xác nhận bằng mắt (UH 55-12, TH-64-72, CP-23-19, TM-27-01, HH-52-42). **NG ngoại giao: 88 file (~18 ảnh gốc)** — đã xác nhận bằng mắt (41-291-NG-01, 80-NG-631-34, 51-NG-166-33). Trắng dân sự (ô tô + xe máy). **KHÔNG có vàng, KHÔNG có xanh** (đo: 80/80 ảnh mẫu ngẫu nhiên đều nền trắng). | "Public Domain" — **người đăng tự khai**, không phải giấy phép ảnh gốc (thấy watermark báo chí "VTC News" trên ảnh nhóm quandoi/ngoaigiao) | `rf.workspace('cuong-ta-ulxex').project('vietnamese-car-license-plate').version(1).download('yolov11', location='D:/DATN/datasets/raw/cuongta-vn-plate')` — link export đã kiểm chứng sống, ~205 MB |
| 2 | **license-plate-color** (nguyenluanAI) | Roboflow `nguyenluanai/license-plate-color/4` | 2.107 ảnh biển **đã crop sẵn** (train 1.505 / valid 423 / test 179) | **Vàng: 694 ảnh** (gấp 35 lần số hiện có) — xác nhận bằng mắt 12/12 mẫu và bằng đo saturation (hue 44°, sat 0,521). **Xanh: 63 ảnh** — xác nhận 12/12 mẫu (hue 213°, sat 0,505). Trắng 808 (nhãn độ tin cậy thấp). **KHÔNG có đỏ, KHÔNG có NG.** | **CC BY 4.0** (rõ ràng nhất trong tất cả ứng viên) — **bắt buộc ghi công** workspace `nguyenluanAI` | `rf.workspace('nguyenluanai').project('license-plate-color').version(4).download('yolov11', location='D:/DATN/datasets/raw/roboflow-license-plate-color')` — **phải dùng version(4)**, version(3) chỉ có 862 ảnh |
| 3 | **vietnamese license plate** (school) | Roboflow `school-fuhih/vietnamese-license-plate-tptd0/1` | 8.397 ảnh (version 1: 8.357), 1 lớp tên `0` | Đỏ Quân đội ~111 ảnh gốc (~555 file kể cả augment), NG ngoại giao ~16 ảnh gốc (~80 file). **Gần như trùng nội dung hiếm với bộ #1** — chỉ nên dùng để đối chiếu/bổ sung sau khi khử trùng lặp. Không có vàng, không có xanh. | CC BY 4.0 (xác nhận qua API) | `rf.workspace('school-fuhih').project('vietnamese-license-plate-tptd0').version(1).download('yolov11')` |
| 4 | **plate-color** (hungnc) | Roboflow `hungnc/plate-color-osqas` | 2.141 ảnh (White 808 / Yellow 694 / Blue 639) | Cùng nguồn ảnh với bộ #2. Con số "Blue 639" là **ảo**: chỉ ứng với 63 tên file duy nhất và 46 biển số duy nhất, phần dư là bản augment (có ảnh bị lật 180°). **Không thêm giá trị so với bộ #2.** | CC BY 4.0 (qua API) | **KHÔNG tải được bằng SDK** — project không publish version nào (`versions: []`, thử /1…/15 đều 404). Chỉ tải được thủ công qua `POST api.roboflow.com/hungnc/plate-color-osqas/search` rồi `GET source.roboflow.com/<ws>/<image_id>/original.jpg` |
| 5 | **vietnamese-license-plate** (annguyen) | Roboflow `annguyen/vietnamese-license-plate-nugsi/8` | 1.815 ảnh cấp project (version 8: 1.618), 1 lớp `license-plate` | **Không có nhãn màu/loại biển nào.** Chỉ là ảnh biển VN thô, giấy phép thoáng. Không giải quyết vấn đề đang đo. | MIT | `rf.workspace('annguyen').project('vietnamese-license-plate-nugsi').version(8).download('yolov11')` |

> `ROBOFLOW_API_KEY` đã có sẵn trong `D:/DATN/.env`. Mọi lệnh trên nên đọc khóa từ biến môi trường, **không hardcode khóa vào script**.

### 2.1 Rủi ro bắt buộc xử lý trước khi đưa vào đánh giá

Áp dụng cho bộ #1 và #3:

1. **Rò rỉ train/test.** Các bản tăng cường (`rotate`, `boder`, `brightness`, `crop`) được nạp như ảnh nguồn độc lập và bị chia lẫn giữa train/valid/test (ví dụ `quandoi104` xuất hiện ở cả test lẫn train; `ngoaigiao2` ở cả train lẫn valid). **Phải gom lại theo tên ảnh gốc rồi tự chia lại split.** Nếu giữ nguyên split có sẵn, dự án lặp lại đúng loại lỗi đánh giá đã từng phải sửa.
2. **Số ảnh gốc thật rất nhỏ.** Biển đỏ ~114, biển NG ~18. Đủ để có tập TEST đánh giá được (thứ dự án đang có bằng 0), **không đủ** để huấn luyện bộ phân loại loại biển cho NG.
3. **Trùng lặp tên file** (ví dụ `quandoi1.jpg` xuất hiện 2 lần) — phải khử trùng lặp.
4. **Lệch miền.** Khối lớn nhất của bộ #1 (~5.485 ảnh `CarLongPlateGen`, `NNNN_NNNNN_b`) là ảnh camera cổng bãi xe, trong khi nhóm quandoi/ngoaigiao là ảnh báo chí ngoài đường. Trộn thẳng vào tập đánh giá sẽ làm lệch kết quả.
5. **Bộ #3 không có nhãn ký tự** — muốn đưa vào đánh giá OCR phải tự gõ nhãn tay.

Áp dụng cho bộ #2:

6. **Lớp `bien_unknown` = 542 ảnh (25,7% bộ)** là ảnh chụp đêm/IR bị lỗi cân bằng trắng, ám tím (median hue 269°, sat 0,194) — đây là lý do annotator không gán được màu. Không dùng được nhãn màu cho 1/4 bộ.
7. **Lớp `bien_trang` (808) đáng ngờ**: mean saturation chỉ 0,147, 14/30 ảnh mẫu gần như ảnh xám — ảnh xám của biển vàng cũng trông ra trắng. May là dự án đang thừa biển trắng nên không cần lớp này.
8. **Ảnh bị resize "Stretch to 640×640"** ⇒ tỷ lệ khung hình biển bị biến dạng. Với biển số (khung hình rất dẹt) đây là biến dạng lớn; nên lấy ảnh gốc từ `source.roboflow.com` nếu cần tỷ lệ thật, và ghi rõ trong báo cáo thực nghiệm.
9. **Biển xanh chỉ 63 ảnh và lệch nặng về 86A (Bình Thuận)** — đủ để báo cáo "có đánh giá", không đủ để kết luận thống kê.

### 2.2 Lợi ích ngoài dự kiến

Bộ #2 (và #4): **tên file chứa sẵn chuỗi biển số ground-truth** — ví dụ `crop_caunamprc555_76B01322_05-02-2024_13-11-32_640.jpg`. Parse được 900 biển từ mẫu 1.107 bản ghi, 897/900 có mã tỉnh VN hợp lệ (51 TP.HCM 205, 86 Bình Thuận 170, 79 Khánh Hòa 84, 85 Ninh Thuận 77…). Nghĩa là **694 ảnh biển vàng có sẵn nhãn ký tự miễn phí**, dùng ngay được làm tập đánh giá OCR biển vàng — không chỉ đánh giá màu. Vẫn nên soát lại bằng mắt trước khi công bố số liệu.

---

## 3. Các bộ đã xét nhưng LOẠI BỎ

| Bộ | Lý do loại |
|---|---|
| `intoo/plate-type-classification` | **Không phải biển VN — biển IRAN.** Nhãn `taxi/gov/police/simple` nghe rất đúng nhu cầu, nhưng ảnh thật là nền xanh lá, dải xanh dương "I.R. IRAN", chữ Ba Tư. Đã xác minh bằng ảnh. |
| `annas-workspace-ko9ow/military-license-plates` | **Không phải biển VN — biển quân sự Ukraine/Nga.** Nền xanh lá, "KB 0004", ký tự Kirin. Đã xác minh bằng ảnh. |
| `alibi/ir-license-plate-oke2v` (6.384 ảnh) | Không phải biển VN — IRAN. Tên lớp là chữ cái Ba Tư (alef, ain, ein, fe, gaf…), có lớp `diplomat` gây hiểu nhầm. |
| `eazy-pass-2/khmer-plate-number-ggehz` (2.743 ảnh) | Không phải biển VN — CAMPUCHIA. Lớp theo tỉnh Khmer (phnom_penh, battambang, kampot…). |
| `openaiclip/plate-types-dgw88` (4.461 ảnh) | Không phải biển VN — MỸ. Lớp là 51 bang. |
| `pattarawadees-workspace/car-license-plate-color-ai` (318 ảnh), `muthitas-workspace/car-license-plate-color` (157 ảnh) | Không phải biển VN — THÁI LAN. Ngoài ra quá nhỏ. |
| `anpr-tsug0/license-plate-eq813` | Không phải biển VN — ẤN ĐỘ (nhãn là biển thật dạng AP16TE6971, GJ01BY5066). |
| Toàn bộ Kaggle | **Không tồn tại bộ biển số VN nào có nhãn loại biển hoặc nhãn màu.** Không bộ nào tự mô tả là chứa biển vàng/xanh/đỏ/ngoại giao. |

**Ghi chú phương pháp — đây là bước quan trọng nhất:** hai bộ đầu bảng trên (`plate-type-classification`, `military-license-plates`) có tên lớp trùng khớp hoàn hảo với nhu cầu của dự án. Nếu chỉ tin tên lớp mà không mở ảnh xem, dự án đã nhập hai bộ nước ngoài vào tập đánh giá — đúng loại lỗi đã từng mắc và phải tách ra.

**Hạn chế của quá trình thẩm định:** trang `universe.roboflow.com` bị Cloudflare chặn hoàn toàn (HTTP 403 với cả WebFetch lẫn curl có User-Agent trình duyệt). Mọi metadata và giấy phép trong báo cáo này lấy từ **API chính thức `api.roboflow.com`** có xác thực, **không phải từ trang hiển thị cho người dùng**. Giấy phép do đó chưa được đối chiếu chéo với trang công khai.

---

## 4. Những gì KHÔNG tìm được

| Loại biển | Tình trạng |
|---|---|
| **Biển vàng** (kinh doanh vận tải) | ✅ Đã lấp — 694 ảnh, có nhãn màu + nhãn ký tự. |
| **Biển xanh** (cơ quan Nhà nước) | ⚠️ Lấp một phần — chỉ 63 ảnh, lệch về 1 tỉnh. Đủ báo cáo định tính, **không đủ công bố số liệu thống kê**. |
| **Biển đỏ** (Quân đội) | ⚠️ Lấp một phần — ~114 ảnh gốc, đều là ảnh báo chí toàn cảnh xe, biển nhỏ trong khung hình, crop ra độ phân giải thấp. Không có nhãn ký tự. |
| **Biển NG / QT** (ngoại giao) | ❌ Gần như không lấp được — chỉ ~18 ảnh gốc. **Không có bộ nào chuyên về biển ngoại giao VN.** |
| **Biển chuyên dùng (LD, DA, RM, HC, KT, CD, T)** | ❌ **Không tìm được nguồn nào.** Không project VN nào gán nhãn theo seri. Dấu vết duy nhất: trong 900 biển parse được từ bộ #2 có 13 biển seri LD và 1 biển KT — nhãn màu của chúng còn mâu thuẫn (6 unknown / 3 vàng / 4 trắng). Không dùng để đánh giá được. |

Đã quét 30 từ khóa (tiếng Anh + tiếng Việt không dấu: `vietnam license plate`, `bien so xe`, `bien so vang`, `bien so xanh`, `bien so do`, `bien so quan doi`, `bien so ngoai giao`, `vietnam military plate`, `phan loai mau bien so xe`, `diplomatic license plate`, `taxi license plate vietnam`…), mỗi từ khóa tối đa 3 trang, thu được **286 project duy nhất** trên Roboflow. Kaggle quét qua REST API không cần xác thực.

**Lý do hợp lý cho việc thiếu:** biển đỏ và biển NG cực hiếm trên đường, và việc chụp/công khai biển quân đội VN là vấn đề nhạy cảm. **Không nên kỳ vọng tìm được nguồn công khai tốt hơn.**

---

## 5. Đề xuất

### 5.1 Thứ tự tải

1. **Tải trước: `nguyenluanai/license-plate-color` version 4.** Giấy phép rõ ràng nhất (CC BY 4.0), tải được ngay bằng SDK, mức cải thiện lớn nhất và chắc chắn nhất: biển vàng 20 → 714 ảnh, biển xanh 4 → 67 ảnh, kèm nhãn ký tự miễn phí trong tên file. Đây là bộ duy nhất biến biển vàng từ "không đánh giá được" thành "đánh giá được có ý nghĩa".
2. **Tải thứ hai: `cuong-ta-ulxex/vietnamese-car-license-plate` version 1**, nhưng **chỉ trích 541 file `quandoi` + 88 file `ngoaigiao`**, sau khi gom bản augment về ảnh gốc và khử trùng lặp. Bỏ phần còn lại (lệch miền camera bãi xe). Phải ghi trong luận văn: *"giấy phép do người đăng tự khai là Public Domain; ảnh nguồn có dấu hiệu là ảnh báo chí"* — **không được khẳng định là Public Domain thật.**
3. **Chỉ tải nếu cần đối chiếu: `school-fuhih/...`** — nội dung hiếm gần như trùng bộ #2, và không có nhãn ký tự.
4. **Bỏ qua:** `hungnc/plate-color-osqas` (cùng nguồn ảnh với bộ #1, không tải được bằng SDK, con số Blue bị thổi phồng bởi augmentation), `annguyen/...` (không có nhãn loại biển).

### 5.2 Phương án cho loại biển vẫn thiếu

| Thiếu | Phương án |
|---|---|
| Biển xanh (n≈67 sau khi bổ sung) | Báo cáo độ chính xác kèm **ghi rõ n và khoảng tin cậy**, xếp vào mục "kết quả sơ bộ". Không đưa vào bảng kết quả chính như một con số ngang hàng với biển trắng. |
| Biển đỏ (n≈114 ảnh gốc, ảnh báo chí) | Dùng làm **tập kiểm thử định tính**: báo cáo "phát hiện được / không phát hiện được" và tỷ lệ đọc đúng trên n nhỏ, kèm cảnh báo về độ phân giải. Không dùng để huấn luyện. |
| Biển NG/QT (n≈18) | **Không đủ để đánh giá.** Phương án: (a) tự thu thập bổ sung ảnh biển NG công khai; (b) sinh ảnh tổng hợp theo đúng quy cách QCVN 08:2024/BCA để kiểm tra khả năng của bộ hậu xử lý regex — nhưng phải nêu rõ là dữ liệu tổng hợp; (c) **chấp nhận ghi vào mục Hạn chế của luận văn** rằng hệ thống chưa được đánh giá trên biển ngoại giao. |
| Biển chuyên dùng LD/DA/RM/HC/KT/CD/T | **Không có nguồn.** Ghi vào mục Hạn chế. Có thể kiểm tra riêng phần **validator/regex** bằng chuỗi biển tổng hợp đúng quy cách (không cần ảnh) để chứng minh tầng hậu xử lý không loại nhầm các seri này. |

### 5.3 Nguyên tắc bắt buộc khi nhập dữ liệu mới

- Tự chia lại split theo **ảnh gốc**, không theo file, để tránh rò rỉ do bản augment.
- Khử trùng lặp theo tên file và theo chuỗi biển số.
- Giữ nguồn gốc từng ảnh trong metadata (`source_dataset`) để có thể báo cáo kết quả tách theo miền dữ liệu.
- Ghi công CC BY 4.0 cho `nguyenluanAI` và `school-fuhih` trong báo cáo dataset và luận văn.
