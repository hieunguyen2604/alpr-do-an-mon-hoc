# Bộ script xử lý dữ liệu — Phase 2

Toàn bộ mã nguồn chuẩn bị dữ liệu cho hệ thống nhận dạng biển số xe Việt Nam:
tải về → kiểm tra nhãn → khử trùng lặp → gộp → chia tập → tăng cường → thống kê.

> **Ngôn ngữ:** mã nguồn và comment bằng tiếng Anh, tài liệu bằng tiếng Việt.
> **Môi trường:** dùng venv `d:/DATN/backend/.venv` (Python 3.13, chạy CPU).

---

## 1. Cài đặt và chuẩn bị

```powershell
cd d:\DATN
.\backend\.venv\Scripts\Activate.ps1
python scripts\dataset\run_pipeline.py --help
```

Các thư viện bắt buộc đã có sẵn trong venv: `pyyaml`, `requests`, `pillow`,
`imagehash`, `opencv-python`, `albumentations`, `matplotlib`, `tqdm`.

Hai thư viện **tuỳ chọn**, chỉ cần khi tải dataset từ nguồn tương ứng:

```powershell
pip install huggingface_hub   # cần cho bộ VNLP
pip install kaggle            # cần cho các bộ trên Kaggle
```

Thiếu chúng thì script **không sập** — nó in hướng dẫn tải thủ công rồi bỏ qua bộ đó.

---

## 2. Thứ tự chạy

```
download  →  [convert_segments]  →  verify  →  dedup  →  merge  →  split  →  [augment]  →  stats
```

Bước `convert_segments` chỉ cần khi bộ dữ liệu tải về dùng nhãn **phân vùng
(polygon)** thay vì hộp — xem mục 4.2.

Chạy tất cả bằng một lệnh:

```powershell
python scripts\dataset\run_pipeline.py --stratify
```

Xem trước kế hoạch mà không chạy gì:

```powershell
python scripts\dataset\run_pipeline.py --dry-run
```

Chạy lại vài bước:

```powershell
python scripts\dataset\run_pipeline.py --steps merge split stats --stratify
```

**Lưu ý:** các bước luôn chạy theo đúng thứ tự chuẩn ở trên, bất kể bạn liệt kê
theo thứ tự nào trong `--steps`. Bước `augment` **không** nằm trong mặc định vì
nó nhân dung lượng đĩa lên nhiều lần — phải yêu cầu rõ ràng.

### Vì sao thứ tự này

| Bước | Phụ thuộc vào | Lý do đứng ở vị trí đó |
|---|---|---|
| `download` | — | Mọi bước sau đều cần dữ liệu thô |
| `verify` | download | Bắt lỗi nhãn khi còn truy được về bộ gốc |
| `dedup` | download | Chạy trên `raw/` để báo cáo theo đường dẫn gốc |
| `merge` | download | Thống nhất không gian lớp và đặt tên duy nhất |
| `split` | merge + dedup | Cần kết quả dedup để chống rò rỉ dữ liệu |
| `augment` | split | Chỉ tác động lên tập train |
| `stats` | split | Thống kê trên bộ dữ liệu cuối cùng |

---

## 3. Cấu trúc thư mục sinh ra

```
datasets/
  raw/<tên_bộ>/            # dữ liệu tải về, giữ nguyên
  processed/
    merged/                # đã gộp, đổi tên <bộ>_<số thứ tự>
      images/  labels/  merge_manifest.csv
    yolo/                  # đã chia tập — đây là thứ đưa cho Ultralytics
      images/{train,val,test}/
      labels/{train,val,test}/
      data.yaml
      split_manifest.csv
  statistics/              # biểu đồ PNG + statistics.json
  reports/                 # báo cáo JSON/CSV của từng bước
```

Đường dẫn gốc có thể đổi bằng `--datasets-dir` hoặc biến môi trường
`DATN_DATASETS_DIR`. Không có đường dẫn nào bị hard-code.

---

## 4. Từng script

Mọi script đều có `--help`, `--log-level`, `--datasets-dir`.

### 4.1 `download.py` — tải dataset

```powershell
python scripts\dataset\download.py --dry-run          # xem sẽ tải gì
python scripts\dataset\download.py --datasets vnlp    # chỉ tải VNLP
python scripts\dataset\download.py --all --force      # tải lại tất cả
```

Đọc danh mục nguồn từ `scripts/dataset/configs/datasets.yaml` (nếu tồn tại
`configs/datasets.yaml` ở gốc dự án thì file đó được ưu tiên). Mỗi mục khai báo:
tên, URL, loại nguồn, định dạng nhãn, giấy phép, có cần credential không.

| Tham số | Ý nghĩa |
|---|---|
| `--config FILE` | Dùng file danh mục khác |
| `--datasets NAME...` | Chỉ tải các bộ được nêu (ghi đè cờ `enabled: false`) |
| `--all` | Tải mọi mục kể cả mục đang tắt |
| `--dry-run` | In kế hoạch rồi thoát, không đụng vào mạng |
| `--force` | Tải lại dù đã có bản cache hợp lệ |
| `--timeout GIÂY` | Thời gian chờ mỗi request (mặc định 60) |

**Hành vi quan trọng:**

- **Thiếu credential → bỏ qua kèm hướng dẫn cụ thể**, không sập. Ví dụ thiếu
  `KAGGLE_KEY` thì script in đúng các bước lấy token.
- **Resume**: file đã tải và khớp `sha256` thì bỏ qua. Chưa khai `sha256` thì
  script in ra giá trị thật để bạn dán vào file cấu hình.
- Tải qua file tạm `.part`, chỉ đổi tên khi hoàn tất → lần chạy sau không bao giờ
  nhầm file tải dở thành file hoàn chỉnh.
- Từ chối giải nén file chứa đường dẫn thoát ra ngoài thư mục đích.
- **Tự nạp `.env`**: khi khởi động, script đọc `<gốc dự án>/.env` và nạp các biến
  chưa có trong môi trường. Biến đã đặt sẵn trong shell luôn thắng. Giá trị
  không bao giờ được ghi ra log — chỉ in tên biến.

#### `source_type: roboflow` — tải hai bước

Roboflow không phục vụ file zip từ một URL cố định. Trường `url` trong danh mục
phải trỏ tới **API endpoint**, không phải link zip:

```
https://api.roboflow.com/{workspace}/{project}/{version}/yolov11?api_key=${ROBOFLOW_API_KEY}
```

Script làm hai bước:

1. `GET` endpoint trên → JSON chứa `export.link` (link zip đã ký, hết hạn nhanh).
   Nếu Roboflow đang sinh bản export, JSON chỉ có `progress`; script chờ và hỏi lại.
2. Tải zip từ `export.link`, kiểm tra checksum rồi giải nén.

Nếu project không cung cấp định dạng đang yêu cầu, script thử lần lượt
`yolov11 → yolov9 → yolov8 → yolov5pytorch`. Định dạng thực tế đã dùng được ghi
vào `datasets/raw/<tên>/_roboflow_export.json` (file này **không** chứa API key).

Lần chạy lại: nếu file zip đã có sẵn thì script bỏ qua cả hai bước, không tốn
lượt gọi API.

Đặt credential trong PowerShell (hoặc ghi vào `.env`):

```powershell
$env:ROBOFLOW_API_KEY = "..."
$env:KAGGLE_USERNAME  = "..."
$env:KAGGLE_KEY       = "..."
$env:HF_TOKEN         = "..."
```

> **Cảnh báo:** đừng cộng dồn `expected_images` của các bộ để suy ra tổng số ảnh.
> Các bộ Roboflow trùng lặp nhau rất nhiều; con số thật chỉ có sau `deduplicate.py`.

### 4.2 `convert_segments.py` — polygon → hộp giới hạn

```powershell
python scripts\dataset\convert_segments.py `
    --input-dir datasets\raw\hf_vn_plates_segment --line-count-map 0=1,1=2
```

Một số bộ biển số Việt Nam phát hành nhãn **phân vùng**: mỗi dòng là
`class x1 y1 x2 y2 ... xn yn`. Toàn bộ pipeline còn lại — và YOLO11 detection —
cần `class x_center y_center width height`.

> **Vì sao phải chuyển tường minh.** Dòng polygon có ít nhất 7 trường, nên bộ
> đọc detection vẫn parse trót lọt: nó lấy `x1 y1 x2 y2` làm `x y w h`. Không có
> gì sập, verify gần như vẫn qua, và mô hình được huấn luyện trên hộp **vô
> nghĩa về mặt hình học**. Đây là kiểu lỗi im lặng, chỉ lộ ra sau khi đã tốn cả
> buổi huấn luyện.

Bản gốc được **chuyển sang `labels_polygon/`, không bao giờ bị xoá** — chạy lại
lần hai đọc từ đó nên thao tác này idempotent.

| Tham số | Ý nghĩa |
|---|---|
| `--input-dir` | Thư mục gốc bộ dữ liệu, chứa `labels/` |
| `--output-dir` | Ghi ra nơi khác thay vì chuyển đổi tại chỗ |
| `--line-count-map` | Ánh xạ class id gốc sang số dòng thật, ví dụ `0=1,1=2` |
| `--report` | Ghi tóm tắt JSON |

**`--line-count-map` quan trọng hơn vẻ ngoài của nó.** Bộ nào tách lớp `BSD`
(biển dài, 1 dòng) và `BSV` (biển vuông, 2 dòng) là đang mã hoá sẵn **số dòng
thật**. Không khai báo ánh xạ thì thông tin đó bị vứt đi, và `split.py
--stratify` cùng `statistics.py` phải quay lại **đoán** bằng tỷ lệ khung hình —
một heuristic mà phối cảnh và box gán lỏng thường xuyên phá vỡ. Khai báo ánh xạ
là thay phép đoán bằng sự thật, đúng ở trục khó nhất của bài toán.

### 4.3 `verify_annotations.py` — kiểm tra chất lượng nhãn

```powershell
python scripts\dataset\verify_annotations.py --input-dir datasets\raw\vnlp
python scripts\dataset\verify_annotations.py --strict
```

| Kiểm tra | Mức | Vì sao |
|---|---|---|
| File nhãn tồn tại | lỗi | Thiếu nhãn → YOLO coi ảnh là nền, dạy mô hình rằng biển số không phải biển số |
| Nhãn parse được | lỗi | Dòng hỏng làm training chết giữa chừng |
| Toạ độ trong `[0,1]` | lỗi | Lỗi phổ biến nhất: quên chuẩn hoá, để nguyên toạ độ pixel |
| Diện tích box > 0 | lỗi | Box rỗng gây NaN loss |
| Box không vượt khung | lỗi | Box bị cắt làm lệch mục tiêu |
| Ảnh đọc được bằng OpenCV | lỗi | Ultralytics đọc bằng OpenCV |
| Box ≥ 0,5% diện tích ảnh | cảnh báo | Biển nhỏ hơn mức này gần như không học được ở đầu vào 640px |
| Box trùng nhau | cảnh báo | Thường do gán nhãn hai lần |

Script **giải mã ảnh đầy đủ bằng OpenCV**, không chỉ đọc header. Ảnh JPEG bị cụt
vẫn có header hợp lệ; nếu chỉ đọc header thì lỗi sẽ nổ ra giữa lúc training.

Tham số: `--min-box-area` (mặc định 0.005), `--allow-missing-labels`,
`--strict` (có lỗi thì trả về mã 1), `--max-issues`.

**Đầu ra:** `reports/annotation_verification.json` và `reports/annotation_issues.csv`.

### 4.4 `deduplicate.py` — khử trùng lặp

```powershell
python scripts\dataset\deduplicate.py --input-dir datasets\raw
python scripts\dataset\deduplicate.py --threshold 3 --workers 8
python scripts\dataset\deduplicate.py --apply        # xoá thật
```

Dùng perceptual hash (`imagehash.phash`, 64 bit), so sánh bằng khoảng cách
Hamming. **Mặc định chỉ báo cáo, không xoá gì.**

| Tham số | Ý nghĩa |
|---|---|
| `--threshold N` | Khoảng cách Hamming tối đa coi là trùng (mặc định 5). 0 = hash giống hệt |
| `--dataset-from` | `top-dir` cho `raw/<tên>/...`; `filename-prefix` cho tên đã gộp |
| `--priority BỘ...` | Thứ tự ưu tiên giữ lại. Mặc định `vnlp` — giữ bộ có nhãn ký tự |
| `--keep-strategy` | `priority` (mặc định) chỉ xét thứ tự bộ; `quality` giữ bản **nhiều box nhất → độ phân giải cao nhất**, chỉ dùng `--priority` để phá hoà |
| `--workers N` | Số luồng băm ảnh |
| `--apply` | Xoá thật ảnh thừa **và** file nhãn tương ứng |

**Điểm quan trọng nhất — trùng lặp CHÉO GIỮA CÁC BỘ.** Đây là con số script in
đậm nhất, vì nó quyết định kết quả đánh giá có đáng tin không. Trùng trong cùng
một bộ chỉ tốn thời gian huấn luyện; trùng chéo giữa hai bộ khiến cùng một tấm
ảnh rơi vào `train` dưới tên bộ này và `test` dưới tên bộ kia — lúc đó độ chính
xác báo cáo chỉ đang đo khả năng học thuộc.

**Thuật toán:** so sánh vét cạn 37.000 ảnh là ~690 triệu cặp, Python không chạy
nổi. Script dùng *multi-index hashing*: cắt hash 64 bit thành `threshold + 1`
dải; hai hash lệch nhau tối đa `threshold` bit thì theo nguyên lý chuồng bồ câu
bắt buộc phải trùng khít ít nhất một dải. Đây là thuật toán **chính xác**, không
phải xấp xỉ — không bỏ sót cặp trùng nào. Các cặp sau đó được gộp thành nhóm
bằng union-find (nếu A trùng B và B trùng C thì cả ba phải cùng một nhóm).

**Đầu ra:**
- `reports/duplicate_pairs.csv` — ảnh nào trùng ảnh nào, thuộc bộ nào, khoảng cách
- `reports/duplicate_groups.csv` — từng nhóm, ảnh nào được giữ / bị xoá
- `reports/duplicate_groups.json` — **file `split.py` đọc để chống rò rỉ**
- `reports/deduplication_report.json` — tổng hợp

#### Kiểm chứng rò rỉ SAU khi chia — dùng lại chính script này

Không cần script riêng. Thư mục đã chia có dạng `images/{train,val,test}/...`,
nên `--dataset-from top-dir` sẽ coi **tên tập** là "tên bộ". Khi đó dòng
*CROSS-DATASET* trong báo cáo chính là **số cặp gần trùng nằm ở hai tập khác
nhau** — con số phải bằng 0:

```powershell
python scripts\dataset\deduplicate.py `
    --input-dir datasets\processed\yolo_v2\images `
    --output-dir datasets\reports\v2\leakage_yolo_v2 `
    --dataset-from top-dir --threshold 5
```

Đây là bằng chứng bắt buộc cho chương Đánh giá: nếu số này khác 0 thì mAP báo
cáo đang đo khả năng học thuộc, không phải khả năng khái quát.

### 4.5 `merge.py` — gộp các bộ

```powershell
python scripts\dataset\merge.py
python scripts\dataset\merge.py --datasets vnlp --link
python scripts\dataset\merge.py --accept-classes 0 2 --include-extras
```

Gộp mọi bộ trong `raw/` về một cấu trúc thống nhất trong `processed/merged/`.

| Tham số | Ý nghĩa |
|---|---|
| `--datasets NAME...` | Chỉ gộp các bộ được nêu |
| `--keep-class-ids` | Giữ nguyên class id gốc thay vì đưa hết về 0 |
| `--accept-classes ID...` | Chỉ giữ box có class id gốc nằm trong danh sách |
| `--accept-classes-for BỘ=ID[,ID]` | Bộ lọc lớp **riêng cho từng bộ**, đè lên `--accept-classes` |
| `--exclude-list FILE` | File danh sách ảnh cần bỏ, mỗi dòng một đường dẫn — dùng để loại ảnh mà `verify_annotations.py` báo lỗi |
| `--include-unlabeled` | Nhận cả ảnh không có nhãn, coi là ảnh nền |
| `--link` | Dùng hard link thay vì copy, tiết kiệm dung lượng |
| `--include-extras` | Ghi thêm `plate_text` và `line_count` vào file nhãn |

Ba việc merge phải giải quyết:

1. **Đụng tên file.** Hầu hết bộ nào cũng đánh số `0001.jpg`. Copy chung một thư
   mục là ghi đè lẫn nhau mà không báo gì. Nên mọi file được đổi tên
   `<bộ>_<số thứ tự 6 chữ số>` — duy nhất, và vẫn đọc được bộ gốc từ tên file.
2. **Không gian class id.** Bộ này class 0 là biển số, bộ kia class 0 là ô tô.
   Mặc định mọi box được đưa về class `0 = license_plate` (bài toán một lớp).
3. **Truy vết.** `merge_manifest.csv` ghi file mới ← file gốc ← thuộc bộ nào.
   Không có nó thì không trích dẫn được giấy phép trong báo cáo.

Thứ tự xử lý cố định → chạy lại cho ra tên file giống hệt.

#### ⚠️ Vì sao cần `--accept-classes-for` chứ không phải `--accept-classes`

`--accept-classes` áp cho **mọi** bộ, và điều đó sai khi cùng một class id mang
nghĩa khác nhau giữa các bộ. Trong nhóm detection hiện tại:

- `roboflow_eric_nguyen` có `0=license-plate`, `1=vehicle` → phải **bỏ** lớp 1.
- `hf_vn_plates_segment` có `0=BSD` (biển dài, 1 dòng), `1=BSV` (biển vuông,
  2 dòng) → **cả hai đều là biển số**, phải giữ.

Dùng `--accept-classes 0` cho cả hai sẽ **xoá sạch 3.559 box biển 2 dòng** của
bộ `hf` — đúng tập con khó nhất và giá trị nhất của bài toán — mà log vẫn báo
merge thành công. Lệnh đúng:

```powershell
python scripts\dataset\merge.py --accept-classes-for roboflow_eric_nguyen=0
```

Script **từ chối chạy** nếu tên bộ trong `--accept-classes-for` không nằm trong
danh sách bộ đang gộp, nên gõ sai tên sẽ lộ ra ngay thay vì bị bỏ qua im lặng.

### 4.6 `split.py` — chia train/val/test

```powershell
python scripts\dataset\split.py --stratify
python scripts\dataset\split.py --ratios 0.8 0.1 0.1 --seed 1337
```

| Tham số | Ý nghĩa |
|---|---|
| `--ratios TRAIN VAL TEST` | Tỷ lệ chia (mặc định 0.7 0.2 0.1), tự chuẩn hoá về tổng 1 |
| `--stratify` | Cân bằng tỷ lệ biển 1 dòng / 2 dòng giữa các tập |
| `--seed N` | Hạt giống ngẫu nhiên (mặc định 42) — cùng seed cho kết quả y hệt |
| `--duplicate-groups FILE` | Đường dẫn `duplicate_groups.json` |
| `--allow-no-groups` | Cho phép chạy khi chưa có kết quả dedup (mất bảo vệ rò rỉ) |
| `--link` | Hard link thay vì copy |
| `--keep-extras` | Giữ `plate_text`/`line_count` trong nhãn đã chia — **mặc định TẮT**, xem cảnh báo dưới |

#### ⚠️ Vì sao `processed/yolo/` phải là YOLO 5 trường thuần

`merge.py --include-extras` ghi thêm `plate_text` và `line_count` vào cuối mỗi
dòng nhãn. Đó là **phần mở rộng riêng của dự án này**, và Ultralytics **không
đọc được nó**: bộ nạp của Ultralytics coi mọi trường sau class id là toạ độ
polygon, gặp ký tự `-` (chỗ giữ chỗ cho `plate_text` rỗng) thì ném
`could not convert string to float: '-'` rồi **bỏ luôn tấm ảnh đó vì "corrupt"**.

Nguy hiểm ở chỗ nó **không sập**. Ultralytics chỉ in cảnh báo rồi huấn luyện
tiếp trên phần còn lại — mà phần còn lại có thể là **rỗng**. Cả bộ 4.578 ảnh có
thể biến mất trong khi log vẫn trông bình thường.

Vì vậy `split.py` **mặc định gỡ bỏ extras** khi ghi vào `processed/yolo/`: đây
là thư mục dành cho Ultralytics, nó buộc phải huấn luyện được ngay.
`processed/merged/` vẫn **giữ nguyên** extras, nên số dòng thật không mất — đó
là nơi `split.py --stratify` đọc để phân tầng, và là nơi chạy `statistics.py`
nếu muốn thống kê theo nhãn thật:

```powershell
# Bộ dữ liệu huấn luyện (đã gỡ extras, Ultralytics đọc được)
python scripts\dataset\statistics.py

# Thống kê theo số dòng THẬT (đọc từ merged, còn extras)
python scripts\dataset\statistics.py --input-dir datasets\processed\merged `
    --output-dir datasets\statistics\merged_ground_truth --no-charts
```

Trường `line_count_estimate.method` trong `statistics.json` cho biết con số đến
từ đâu: `LABEL` (nhãn thật), `HEURISTIC` (đoán theo tỷ lệ khung hình), hay
`MIXED`.

Chỉ bật `--keep-extras` khi phân tích ngoại tuyến, **tuyệt đối không** cho thư
mục sắp đem đi huấn luyện.

#### Chống rò rỉ dữ liệu — điểm mấu chốt

Chia theo từng ảnh là **sai** với bộ dữ liệu này. Đơn vị chia ở đây là **nhóm**,
không phải ảnh:

1. `deduplicate.py` ghi ra `duplicate_groups.json` — các nhóm ảnh gần giống nhau.
2. Mỗi nhóm là một đơn vị **không thể tách rời**. Ảnh không thuộc nhóm nào là đơn vị lẻ.
3. Chia các **đơn vị**, không chia các ảnh.

Nhóm được giữ nguyên vẹn kể cả khi ảnh trùng chưa bị xoá — nên chỉ cần chạy
`deduplicate.py` ở chế độ báo cáo là đủ để tập chia an toàn.

Vì các đơn vị có kích thước khác nhau, cắt theo tỷ lệ vị trí sẽ lệch. Script gán
mỗi đơn vị vào tập đang **thiếu nhiều nhất so với chỉ tiêu** (tính theo tỷ lệ
phần trăm chỉ tiêu, để tập val/test nhỏ không bị tập train nuốt hết).

Sau khi chia, script **kiểm tra lại từ kết quả cuối cùng** rằng không nhóm nào
nằm ở hai tập khác nhau; phát hiện vi phạm thì trả mã lỗi 1 và không ghi gì.

Nếu chưa có `duplicate_groups.json`, script **từ chối chạy** và báo lỗi rõ ràng —
phải chạy dedup trước, hoặc chấp nhận rủi ro bằng `--allow-no-groups`.

#### Về `--stratify`

Cân bằng tỷ lệ biển 1 dòng / 2 dòng giữa ba tập. Biển 2 dòng của xe máy là điểm
yếu đã biết của bài toán (OpenALPR: 94,3% trên biển ô tô 1 dòng nhưng chỉ 45,7%
trên biển xe máy 2 dòng). Một tập test vô tình thiếu biển 2 dòng sẽ **che mất**
đúng cái lỗi mà việc đánh giá cần đo. Số dòng suy ra từ ngưỡng tỷ lệ khung hình
nên chỉ gần đúng — nhưng cân bằng gần đúng vẫn tốt hơn lệch ngẫu nhiên rất nhiều.

**Đầu ra:** thư mục theo chuẩn Ultralytics + `data.yaml` + `split_manifest.csv`.

### 4.7 `augment.py` — tăng cường dữ liệu

```powershell
python scripts\dataset\augment.py --multiplier 2
python scripts\dataset\augment.py --multiplier 3 --rotate-degrees 8 --seed 7
```

| Tham số | Ý nghĩa |
|---|---|
| `--multiplier N` | Số bản tăng cường cho mỗi ảnh gốc (mặc định 2) |
| `--rotate-degrees ĐỘ` | Góc xoay tối đa (mặc định 10) |
| `--perspective-scale S` | Mức biến dạng phối cảnh (mặc định 0.05) |
| `--min-visibility F` | Phần box phải còn lại thì mới giữ (mặc định 0.35) |
| `--jpeg-quality Q` | Chất lượng JPEG khi ghi (mặc định 95) |
| `--seed N` | Hạt giống — cùng seed cho kết quả y hệt |

#### ⚠️ Vì sao KHÔNG lật ngang — lỗi hay gặp nhất

`HorizontalFlip` có mặt trong gần như mọi công thức augmentation mẫu, và nó
**sai** với bài toán biển số. Biển số **là chữ**. Lật gương tạo ra tấm ảnh mà
không camera nào chụp được: `51F-12345` thành chuỗi ngược không đọc nổi, và các
ký tự ánh xạ nhầm sang nhau — số `2` lật giống số `5`, chữ `E` lật giống số `3`.

Điều khiến lỗi này khó phát hiện: **nó vô hình ở tầng detection.** Mô hình phát
hiện vẫn tìm ra hình chữ nhật giống biển số, mAP vẫn đẹp, nên phép tăng cường
trông có vẻ vô hại. Thiệt hại dồn hết sang tầng OCR — vốn đã được dạy rằng ký tự
lật gương là hợp lệ — và chỉ lộ ra rất muộn, dưới dạng nhầm lẫn ký tự không rõ
nguyên nhân. Lập luận tương tự loại bỏ luôn lật dọc, xoay 90° và transpose.

Các phép biến đổi được dùng đều mô phỏng nhiễu loạn có thật của camera giao thông:
xoay nhẹ ±10° (camera nghiêng, biển gắn lệch), đổi độ sáng/tương phản (thời điểm
trong ngày, đèn pha, bóng râm), motion blur (xe đang chạy — lỗi thực tế phổ biến
nhất), nhiễu Gauss (chụp đêm ISO cao), nén JPEG (mọi luồng CCTV đều bị nén),
biến dạng phối cảnh nhẹ (camera không bao giờ vuông góc với biển).

#### Chỉ tác động lên tập TRAIN

Tăng cường tập val/test làm hỏng việc đánh giá: chỉ số sẽ đo trên ảnh tổng hợp
không còn đại diện cho dữ liệu thật, và bản tăng cường của một ảnh val chính là
bản gần trùng của nó → điểm số bị thổi phồng. Script **từ chối** ghi vào `val`
hay `test`, và **không có cờ nào ghi đè được**.

Box bị biến dạng ra ngoài khung sẽ bị loại; ảnh mất hết box thì bỏ luôn. Ảnh đã
tăng cường (tên chứa `_aug`) không bị tăng cường lại ở lần chạy sau.

### 4.8 `statistics.py` — thống kê và biểu đồ

```powershell
python scripts\dataset\statistics.py
python scripts\dataset\statistics.py --input-dir datasets\processed\merged
python scripts\dataset\statistics.py --no-charts
```

Sinh `statistics.json` và 8 biểu đồ PNG vào `datasets/statistics/`:

| File | Trả lời câu hỏi gì |
|---|---|
| `images_per_split.png` | Chia tập có đúng tỷ lệ không, bộ nguồn nào chiếm ưu thế |
| `boxes_per_image.png` | Một khung hình thường có mấy biển số |
| `box_area.png` | Biển có đủ lớn để học không (đánh dấu ngưỡng 0,5%) |
| `aspect_ratio.png` | **Cân bằng biển 1 dòng / 2 dòng** — biểu đồ quan trọng nhất |
| `image_sizes.png` | Độ phân giải nguồn có phân tán quá không |
| `box_position_heatmap.png` | Biển thường nằm ở đâu trong khung hình |
| `character_frequency.png` | Tần suất ký tự (đỏ = chữ không được phép có trên biển VN) |
| `plate_length.png` | Phân bố độ dài chuỗi biển số |

Hai biểu đồ cuối chỉ có khi nhãn mang `plate_text` (chạy `merge.py --include-extras`).

---

### 4.9 `build_plate_text.py` — dựng lại chuỗi biển số từ nhãn từng ký tự

Script này **đứng ngoài** chuỗi pipeline phát hiện biển (mục 2). Nó chỉ chạy trên
hai bộ có nhãn **hộp cho từng ký tự** thay vì nhãn cho cả biển:

| Bộ | Ảnh | Số lớp | Tên lớp trong `data.yaml` |
|---|---|---|---|
| `roboflow_ocr_plate` | 3 819 | 30 | `'0'`…`'29'` — **mã số, không phải ký tự** |
| `roboflow_ocr_conversion` | 200 | 22 | chính là ký tự (`'0'`…`'9'`, `'A'`…`'X'`) |

Đây là nguồn duy nhất trong đồ án có **chuỗi biển số thật**, tức là thứ cần để đo
được độ chính xác OCR (NFR-A4…A7).

```powershell
python scripts\dataset\build_plate_text.py --verify-samples 20
```

Cách làm: giải mã lớp → ký tự, phân cụm hộp thành **dòng** theo tọa độ `y`
(ngưỡng = 0,6 × chiều cao ký tự trung vị), sắp xếp dòng từ trên xuống và trong
mỗi dòng từ trái sang phải, rồi ghép lại. Số cụm chính là `line_count` — đây là
**nhãn đo được**, không phải suy đoán từ tỷ lệ khung hình như ở mục 5. Chuỗi thu
được đem đối chiếu với văn phạm biển số VN qua `ai/inference/normalizer.py`.

Kết quả ghi ra `datasets/annotations/plate_text_labels.csv`, báo cáo tổng hợp ở
`datasets/reports/plate_text_report.json`, ảnh kiểm chứng ở
`datasets/annotations/verify_samples/` (tiền tố `OK__` / `CHECK__`).

**Bảng mã lớp của `roboflow_ocr_plate`.** `data.yaml` chỉ ghi `'0'`…`'29'` nên
không tự nó cho biết lớp nào là ký tự nào. Bảng mã được khôi phục từ chính một
ảnh nằm trong bộ (`0_jpg.rf.7b00e9…jpg`): ảnh này không phải biển số mà là **bảng
phông chữ** liệt kê glyph kèm mã Unicode, và được gán nhãn đủ cả 30 lớp. Đọc bảng
đó ra hằng số `_OCR_PLATE_CHARSET = "123456789ABCDEFGHKLMNPSTUVXYZ0"` (chỉ số =
giá trị số của tên lớp). Kiểm chứng: dựng lại chính ảnh bảng phông cho đúng chuỗi
`0123456789ABCDEFGHKLMNPSTUVXYZ` theo thứ tự.

> **Tập ký tự của bộ này là 30 = `OCR_SAFE_CHARSET` thiếu chữ `R`** — đúng bằng
> tập `L20` (chữ cái đầu nhóm seri). Bộ này **không thể** dạy mô hình nhận chữ
> `R`, mà `R` lại hợp lệ ở vị trí seri thứ hai của xe máy. Xem mục 6.

**Hai cảnh báo về chất lượng dữ liệu, phát hiện khi chạy:**

1. **904/3 819 ảnh của `roboflow_ocr_plate` không phải biển Việt Nam** (22,5 %):
   nhóm tên `iwt*` là biển Séc (có dải EU xanh chữ `CZ`, dạng `1B9 8681`), nhóm
   `*PlateBaza*` là biển Croatia/Ba Lan (dạng `ZG 567-EF`). Chúng được dựng lại
   **đúng** nhưng không bao giờ khớp văn phạm VN, nên bị gắn cờ
   `non_vietnamese_source_image` chứ không tính là lỗi dựng chuỗi. **Phải loại
   trước khi dùng để huấn luyện hay đánh giá OCR tiếng Việt.**
2. **104 biển thuộc dòng `MĐ`** (xe máy điện) bị gắn cờ
   `electric_series_MD_not_in_phase1_grammar`. Đây là biển VN thật, chữ `Đ` bị
   người gán nhãn ghi thành `D`; văn phạm Phase 1 chưa có mẫu cho dòng này.

---

## 5. Ngưỡng tỷ lệ khung hình và số dòng biển

Theo QCVN 08:2024/BCA:

| Loại biển | Kích thước (mm) | Tỷ lệ | Số dòng |
|---|---|---|---|
| Ô tô, biển dài | 520 × 110 | 4,727 | 1 |
| Ô tô, biển ngắn | 330 × 165 | 2,000 | 2 |
| Xe mô tô | 190 × 140 | 1,357 | 2 |

Ngưỡng phân biệt đặt ở **2,5** (khoảng trống giữa 2,000 và 4,727):
`AR < 2,5` → đoán 2 dòng; `AR ≥ 2,5` → đoán 1 dòng.

> **Đây là HEURISTIC, không phải nhãn thật.** Ba yếu tố phá ngưỡng này: phối cảnh
> (biển chụp chéo bị hẹp lại), box gán lỏng (đệm thừa làm giảm tỷ lệ), và biển
> xe máy bị móp — rất phổ biến trong ảnh giao thông Việt Nam. Chỉ dùng nó để có
> phân bố gần đúng phục vụ chia tập phân tầng và thống kê. Bộ nào có nhãn số
> dòng thật thì luôn ưu tiên nhãn thật.

---

## 6. Tập ký tự

| Hằng số (trong `ai/data/schema.py`) | Nội dung | Dùng ở đâu |
|---|---|---|
| `OCR_TRAINING_CHARSET` | 10 số + **26 chữ A–Z** | **Huấn luyện mô hình** |
| `OCR_SAFE_CHARSET` | 10 số + 21 chữ (20 chữ seri + `R`) | **Chỉ dùng ở hậu xử lý** |
| `EXCLUDED_LETTERS` | `I J O Q W` | Không bao giờ xuất hiện trên biển VN |
| `SERIAL_FIRST_LETTERS` | 20 chữ | Chữ cái đầu của nhóm seri |
| `SERIAL_SECOND_LETTERS_MOTORCYCLE` | có `R`, không có `G` | Chữ seri thứ hai của xe máy |

> **Quan trọng:** khi xây charset cho mô hình phải dùng **A–Z đầy đủ**, rồi mới
> ràng buộc ở tầng hậu xử lý. Nếu thu hẹp charset ngay ở tầng mô hình thì mô hình
> **không thể** phát ra chữ `R` — thông tin mất trước khi hậu xử lý kịp chạy, và
> không cách nào cứu lại. Thu hẹp ở hậu xử lý thì đoán sai vẫn còn sửa được và
> vẫn đo được.

---

## 7. Xử lý sự cố

| Triệu chứng | Nguyên nhân và cách xử lý |
|---|---|
| `download.py` bỏ qua bộ nào đó | Thiếu biến môi trường — đọc hướng dẫn script in ra |
| Roboflow trả về 401/403 | `ROBOFLOW_API_KEY` sai hoặc hết hiệu lực — kiểm tra lại trong `.env` |
| Roboflow trả về 404 | Sai workspace/project/version, hoặc project không có định dạng đang yêu cầu. Script tự thử `yolov9/yolov8/yolov5pytorch` trước khi bỏ cuộc |
| Kaggle trả về 403 | Chưa bấm đồng ý điều khoản trên trang dataset |
| `split.py` báo lỗi "No duplicate group information" | Chưa chạy `deduplicate.py`. Chạy nó trước (chế độ báo cáo là đủ) |
| `merge.py` báo "Nothing was merged" | Nhãn nằm ở vị trí script không tìm tới, hoặc bộ chưa ở định dạng YOLO |
| Ultralytics báo "dataset not found" | Dùng đường dẫn tuyệt đối tới `processed/yolo/data.yaml` |
| Ultralytics báo `ignoring corrupt image/label: could not convert string to float: '-'` | Nhãn còn extras. Chạy lại `split.py` **không** kèm `--keep-extras` — xem mục 4.6 |
| Ultralytics nạp được 0 ảnh nhưng không báo lỗi | Cùng nguyên nhân trên. Luôn kiểm tra số ảnh nạp được trước khi huấn luyện |
| Nhãn có 7 hoặc 9 trường, box trông vô lý | Bộ dữ liệu dùng nhãn polygon. Chạy `convert_segments.py` — xem mục 4.2 |
| Cảnh báo "Only x% two-line plates" | Bộ dữ liệu lệch nặng về biển 1 dòng — cần bổ sung ảnh xe máy |

---

## 8. Chạy thử nhanh không cần tải dataset thật

Mọi script nhận `--datasets-dir`, nên có thể trỏ vào một thư mục bất kỳ có cấu
trúc `raw/<tên_bộ>/`:

```powershell
python scripts\dataset\run_pipeline.py --datasets-dir D:\tmp\thu_nghiem `
    --steps verify dedup merge split stats --stratify
```

---

## 9. Ghi chú thiết kế

- **Không hard-code đường dẫn.** Mọi thư mục suy ra từ `--datasets-dir`, biến môi
  trường `DATN_DATASETS_DIR`, hoặc vị trí file mã nguồn.
- **Thư mục `ai/` không import `fastapi` hay `pydantic`** — `ai/data/schema.py`
  chỉ dùng `dataclass` thuần.
- **Lỗi được báo cáo, không làm sập.** Ảnh hỏng, nhãn sai định dạng, dataset tải
  lỗi đều được ghi nhận rồi bỏ qua. Không thể để một file JPEG hỏng chặn đứng
  lượt xử lý 37.000 ảnh.
- **Tên file `statistics.py` che mất module `statistics` của thư viện chuẩn.**
  Hàm `_shield_stdlib_statistics()` trong `_common.py` nạp module chuẩn theo
  đường dẫn tuyệt đối trước, nên `import statistics` ở bất kỳ đâu vẫn lấy đúng
  thư viện chuẩn. Đừng gỡ hàm này.
