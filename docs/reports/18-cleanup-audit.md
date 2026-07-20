# 18 — Rà soát dọn dẹp kho mã

**Ngày đo:** 2026-07-20
**Phạm vi:** toàn kho `D:\DATN` (trừ `.venv/`, `node_modules/`, `.git/`)
**Trạng thái:** chỉ rà soát và báo cáo. **Không tệp nào bị xóa, sửa hay di chuyển trong đợt này.**

---

## 1. Kết luận mở đầu — dọn được rất ít, và phải nói thẳng

**Tổng dung lượng thu hồi được thật sự: 5.805 byte (~5,7 KB), trên tổng kho 5,0 GB — tức 0,0001%.**

Trong đó chỉ có **một tệp nguyên vẹn** bị xóa (`frontend/src/utils/format.ts`, 336 B). Ba hạng mục
còn lại là **khối mã nằm bên trong những tệp phải giữ nguyên**, nên phải sửa phẫu thuật chứ không
được `rm`.

Nói cho rõ ràng: **đợt dọn dẹp này không giải phóng dung lượng đáng kể nào.** Giá trị của nó nằm ở
chỗ gỡ bỏ mã chết (giảm nhiễu khi đọc mã, tránh việc người sau tưởng hàm còn dùng), **không** phải ở
chỗ tiết kiệm đĩa. Nếu mục tiêu là lấy lại dung lượng thì báo cáo này trả lời: **không có gì để lấy.**

### 1.1. CẢNH BÁO — số liệu `du -sh` trên từng thư mục con LÀ SAI

`datasets/processed/` chứa **hardlink**: cùng một khối dữ liệu trên đĩa được nhiều thư mục cùng trỏ
tới. Số đo thực tế:

| Phép đo | Kết quả |
|---|---:|
| `du -sh datasets/processed` (thực chiếm đĩa) | **1,7 GB** |
| `du -slh datasets/processed` (đếm hardlink nhiều lần) | **6,6 GB** |
| Tổng kích thước biểu kiến của 109.125 tệp | **6.479 MB** |
| `du -sh` từng thư mục **đo riêng lẻ** — `merged` 979M, `merged_v2` 1,6G, `yolo` 979M, `yolo_v2` 1,6G, `yolo_v3` 1,6G | cộng lại ≈ **5,7 GB** |

Bằng chứng hardlink là trực tiếp, không suy đoán — `stat` trên ảnh mẫu ở ba thư mục khác nhau đều
cho `nlink=3`:

```
merged_v2/images/roboflow_school_fuhih_000021.jpg   inode=281474978846153  nlink=3
yolo_v2/images/test/roboflow_cuong_ta_000076.jpg    inode=281474978866413  nlink=3
yolo_v3/images/test/roboflow_cuong_ta_000014.jpg    inode=281474978866350  nlink=3
```

**Hệ quả cụ thể:** nếu xóa cả bốn thư mục `merged`, `merged_v2`, `yolo`, `yolo_v2` — mà `du` riêng lẻ
báo là ~5 GB — thì dung lượng **thật sự** thu hồi được là:

```
1.718.504 KB (toàn bộ processed)  −  1.607.188 KB (yolo_v3 đo một mình)  =  111.316 KB  ≈  108 MB
```

Tức **dự báo 5 GB nhưng thực nhận 108 MB — sai lệch 46 lần.** Kiểm chứng chéo: trong bốn thư mục đó
chỉ có 39.431 tệp mang `nlink=1` (thật sự chỉ tồn tại ở đó), tổng nội dung 13,51 MB; phần chênh lên
108 MB là do tệp nhãn `.txt` nhỏ bị làm tròn lên block 4 KB.

> **Sửa lại số liệu đầu vào.** Bản tóm tắt giao việc ghi `processed` = 1.559 MB, riêng `yolo_v3` =
> 1.518 MB, `nlink=5`, và xóa bốn bản kia giải phóng 41 MB. Đo lại ngày 2026-07-20 cho kết quả khác:
> `processed` = 1,7 GB, `yolo_v3` = 1,6 GB, `nlink=3`, giải phóng **108 MB**. Kết luận định tính
> (hardlink làm `du` từng thư mục thành vô nghĩa) thì **không đổi** và vẫn đúng; nhưng con số tuyệt
> đối thì phải dùng bản đo lại này. Nguyên nhân sai lệch có thể do `du` tính công phần dữ liệu dùng
> chung cho thư mục nào nó duyệt trước, nên thứ tự duyệt khác nhau sẽ cho kết quả khác nhau.

**Và dù có 108 MB thì cũng không được xóa** — xem mục 3.1: cả bốn thư mục đều đang được tham chiếu.

---

## 2. Bảng XÓA ĐƯỢC

Sắp theo dung lượng giảm dần. Tất cả đã qua thẩm định đối kháng (đã chủ động đi tìm lý do để **giữ**
và không tìm được).

| # | Đường dẫn / phạm vi | Dung lượng | Lý do | Rủi ro |
|---|---|---:|---|:---:|
| 1 | `frontend/src/components/StateViews.tsx` — **chỉ** khối `EmptyState` + `ErrorState`, dòng **40–134** (kèm dọn 3 import) | **2.883 B** | Trùng tên với `components/ui/EmptyState.tsx` và `ui/ErrorState.tsx`. Mọi call site đều lấy bản từ `@/components/ui`, không ai lấy bản ở đây. | trung bình |
| 2 | `scripts/dataset/_common.py` — hàm `read_image_sizes()` dòng **327–355**, mục `__all__` dòng **50**, **và** hàm private `_progress()` dòng **482–501** | **1.803 B** | Hàm công khai duy nhất trong kho không có bất kỳ call site nào. Nằm trong `__all__` nên ruff/pyflakes không báo F401 — đó là lý do nó tồn tại lâu mà không bị phát hiện. | thấp |
| 3 | `frontend/src/components/ui/Skeleton.tsx` — **chỉ** `SkeletonTextProps` + `SkeletonText`, dòng **55–85**; kèm sửa `ui/index.ts` dòng **47** và xóa dòng **51** | **783 B** | Export chết bên trong một tệp còn sống. `Skeleton` (5 usage) và `SkeletonTable` (2 usage) vẫn dùng; riêng `SkeletonText` 0 call site. | thấp |
| 4 | `frontend/src/utils/format.ts` — **xóa cả tệp** | **336 B** | Tệp re-export tương thích, tự đánh dấu `@deprecated`, chỉ chứa một dòng `export * from '@/lib/format'`. Cả 13 call site đều import thẳng `@/lib/format`. | thấp |
| | **Tổng** | **5.805 B** | | |

### 2.1. Bằng chứng từng mục

**Mục 1 — `EmptyState` / `ErrorState` trong `StateViews.tsx`**
- `grep -rn "StateViews"` toàn kho → đúng **2 hit**: `pages/ImageDetection.tsx:36` (chỉ import
  `InlineError, LoadingState, PageSection`) và `frontend/README.md:168`.
- README dòng 168 vốn đã mô tả tệp này là "`PageSection`, `LoadingState`, `InlineError` dùng chung" —
  **tài liệu vốn đã không coi `EmptyState`/`ErrorState` thuộc tệp này**, nên xóa đi làm README chính
  xác hơn chứ không lạc hậu đi.
- Mọi call site lấy từ `@/components/ui`: `ImageDetection.tsx:37`, `VideoDetection.tsx:25`,
  `History.tsx:31-32`, `VideoResultPanel.tsx:16-17`.
- Ba export còn lại **đang sống thật**: `LoadingState` (`ImageDetection.tsx:344`), `InlineError`
  (`:336`), `PageSection` (`:274, 289, 292, 321, 326, 400`) → **tuyệt đối không xóa cả tệp**.

**Mục 2 — `read_image_sizes()`**
- `grep -rn "read_image_sizes"` toàn kho → đúng **2 hit**, cả hai đều tự tham chiếu trong chính tệp
  định nghĩa: `_common.py:50` (mục `__all__`) và `:327` (dòng `def`). 0 call site.
- **Đã loại trừ đường thoát quan trọng nhất:** `grep -rn "^from .* import \*" --include="*.py"` toàn
  kho → **0 kết quả**. Không module nào dùng `import *`, nên tư cách thành viên `__all__` không thể
  làm hàm này tiếp cận được mà không để lại hit tên.
- `git log -S "read_image_sizes"` → **đúng 1 commit** (`19ace79`, commit khởi tạo) ⇒ hàm được thêm vào
  đã chết sẵn, **không phải** từng có caller rồi bị gỡ. Khác hẳn `models/baseline-416-v1.pt` (giữ có
  chủ đích): không có mục nào trong Project Decisions Log, không comment, không TODO.
- Chuỗi `tqdm` riêng của hàm — `"Reading image sizes"` — chỉ có 1 hit tại `_common.py:346`, chưa bao
  giờ xuất hiện trong `logs/` hay `docs/reports/*.json` ⇒ hàm chưa từng được thực thi.
- `docs/manuals/technical-manual.md:869` là chỗ **duy nhất** liệt kê bề mặt công khai của
  `_common.py`, và nó liệt kê `DatasetPaths, resolve_dataset_paths, bootstrap_project_path,
  configure_logging, write_json` — **không có** `read_image_sizes`.
- Ba chỗ đọc kích thước ảnh (`merge.py:383`, `split.py:265`, `statistics.py:123`) đều xen kẽ công việc
  khác cho từng ảnh, nên **về mặt cấu trúc** không thể dùng hàm batch này.

**Mục 3 — `SkeletonText`**
- `grep -rni "skeletontext"` toàn kho → đúng **6 hit**, tất cả là nơi định nghĩa
  (`Skeleton.tsx:55, 56, 71, 74`) và nơi re-export (`ui/index.ts:47, 51`). 0 call site. Các cách viết
  khác (`skeleton-text`, `Skeleton.Text`) → 0 hit. Không có `import * as` từ `components/ui`.
- `docs/`: `grep -i "skeleton"` ra 5 chỗ (`ch4-cai-dat.md:965`, `thesis-full.md:4309`,
  `06-ui-documentation.md:210` và `:568`, `frontend/README.md:171`) — **tất cả** nhắc component/tệp
  `Skeleton`, **không chỗ nào** nhắc `SkeletonText`. Bất biến "15 component nguyên thủy" đếm theo
  **tệp**; `Skeleton.tsx` vẫn còn nên con số 15 **không đổi**.
- `frontend/dist` **không chứa** chuỗi `SkeletonText` ⇒ đã bị tree-shake, xóa giải phóng **0 byte
  bundle**; mọi con số build trong `ch4-cai-dat.md` giữ nguyên.

**Mục 4 — `utils/format.ts`**
- `grep -rn "utils/format"` trong `frontend/src` → **0 kết quả**. Toàn kho → chỉ 1 hit là
  `frontend/README.md:162` (dòng mô tả cây thư mục, không phải mã nguồn).
- Cả 13 import đều dạng `from '@/lib/format'` (`DetectionSummary.tsx:15`, `ImageUploadPanel.tsx:20`,
  `ConfidenceBar.tsx:11`, `Pagination.tsx:9`, `ProgressBar.tsx:9`, `PlateChip.tsx:13`,
  `FileDropzone.tsx:17`, `History.tsx:36`, …). Không có import tương đối `../utils/format`.
- Nội dung tệp tự ghi: `@deprecated Import from @/lib/format instead.`
- `git log -- frontend/src/utils/format.ts` → 1 commit `19ace79` ⇒ sinh ra đã deprecated sẵn cùng
  `lib/format.ts`, không phải di sản của một đợt di chuyển có người tiêu thụ bên ngoài.

### 2.2. Bốn cái bẫy bắt buộc phải tránh khi thực hiện

Đây **không phải** bốn thao tác `rm`. Ba trong bốn mục là sửa phẫu thuật, và mỗi mục có một bẫy:

1. **Hàm anh em `read_image_size` (SỐ ÍT, dòng 294) ĐANG SỐNG** — được import và gọi tại
   `merge.py:54,383`, `split.py:67,265`, `statistics.py:69,123`. Hai tên chỉ khác nhau **một ký tự
   `s`**. Tuyệt đối không đụng vào bản số ít.
2. **Phải xóa kèm `_progress()`** — hàm private này có **đúng một caller trong toàn kho là chính
   `read_image_sizes`** (`_common.py:346`). Xóa `read_image_sizes` mà giữ `_progress` sẽ để lại một
   hàm chết thứ hai, và vì nó là private nên ruff **cũng không báo**. *(Đã kiểm tra: `Iterable` vẫn
   dùng ở dòng 263 và `Sequence` vẫn dùng ở dòng 385, 424 — nên import ở dòng 39 **không** bị mồ côi.)*
3. **`StateViews.tsx` phải dọn 3 import, nếu không HỎNG BUILD** — `tsconfig.json` bật
   `noUnusedLocals: true` và `npm run lint` chạy `--max-warnings 0`. Sau khi xóa dòng 40–134, ba thứ
   này thành mã chết: `Inbox` (chỉ dùng ở dòng 64), `RefreshCw` (chỉ dòng 128), và cả câu
   `import type { LucideIcon }` (chỉ dòng 47). **Giữ lại** `AlertCircle` (còn dùng ở 159), `Loader2`
   (34), `ReactNode` (181, 183). Ngoài ra phải sửa header tệp dòng 1–7 và JSDoc dòng 147
   (`{@link ErrorState}` sẽ trỏ tới một symbol không còn tồn tại).
4. **`ui/index.ts` là barrel của cả thư viện UI** — một lỗi gõ nhầm ở đây làm vỡ toàn bộ bề mặt
   import. Dòng 47 phải **bỏ riêng chữ `SkeletonText`** mà giữ `Skeleton` và `SkeletonTable`; dòng 51
   (`SkeletonTextProps`) xóa cả dòng.

Thêm: xóa `utils/format.ts` thì phải xóa **cả hai dòng 162–163** của `frontend/README.md` (kể cả mục
`utils/`), vì đó là tệp duy nhất trong thư mục đó — nếu không tài liệu sẽ mô tả một thư mục không còn
tồn tại, trái quy tắc "tài liệu phải tiến hóa cùng mã nguồn" của chính dự án.

---

## 3. Bảng PHẢI GIỮ — dù trông như thừa

**Bảng này quan trọng ngang bảng 2.** Nó là thứ ngăn lần dọn dẹp sau xóa nhầm. Mọi mục dưới đây đều
có 0 hoặc gần 0 usage trong mã nguồn — tức là **mọi công cụ dò mã chết đều sẽ đề xuất xóa chúng**.

| Đường dẫn | Dung lượng | AI/CÁI GÌ đang tham chiếu tới nó |
|---|---:|---|
| `datasets/processed/yolo/` (v1) | ~979 MB biểu kiến | **Là giá trị mặc định của tham số CLI** trong 3 script đánh giá đang sống: `ai/evaluation/benchmark_system.py:479`, `leak_check.py:359`, `stress_test.py:323` (`--images datasets/processed/yolo/images/test`). Còn là **phản chứng rò rỉ dữ liệu** trong luận văn: `datasets/processed/README.md:27` ghi "⚠️ Bộ v1 — **có rò rỉ** train↔test (619 cặp ở d≤10)"; `docs/reports/02-dataset-report.md:13` ghi rõ "Tập v1 **vẫn còn nguyên trên đĩa**". |
| `datasets/processed/yolo_v2/` | ~1,6 GB biểu kiến | Phản chứng rò rỉ thứ hai: `README.md:29` — "⚠️ **Có rò rỉ** (2.699 cặp train↔test ở d≤10)". Là **một cột trong bảng so sánh v1/v2/v3** của luận văn: `docs/papers/ch5-thuc-nghiem.md:146` và `thesis-full.md:4830`. `02-dataset-report.md:26` trỏ `processed/yolo_v2/split_manifest.csv`. |
| `datasets/processed/merged_v2/` | ~1,6 GB biểu kiến | Là **corpus được nêu đích danh** trong `datasets/reports/v3/grouping_threshold_sweep.json:2` (`"corpus": "datasets/processed/merged_v2/images"`) — tệp chứng minh cho quyết định chọn ngưỡng gom 10. `02-dataset-report.md:25, 221, 663`. |
| `datasets/processed/merged/` | ~979 MB biểu kiến | Là **đích mặc định** của `scripts/dataset/merge.py:483`. `02-dataset-report.md:655` dùng nó làm **bằng chứng kiểm chứng** và trích nguyên một dòng nhãn: "kiểm chứng ở `processed/merged/labels/`: `0 0.409230 0.599669 0.220442 0.093567 - 1`". `scripts/dataset/README.md:296, 372`. |
| `models/best-640-v3-ep20.pt` | **5.447.834 B (5,4 MB)** | **Trùng từng byte với `models/best.pt`** (cùng SHA-256 `9caa59ad…`) và là **hai bản sao thật** (`nlink=1`, inode khác nhau) — tức xóa **thật sự** thu hồi 5,4 MB, nhiều hơn toàn bộ bảng 2 cộng lại **937 lần**. **Vẫn phải giữ:** nó được liệt kê đích danh là **deliverable** trong `docs/reports/11-definition-of-done.md:32`. `best.pt` là con trỏ "bản đang dùng", tên có phiên bản là bản lưu vết nguồn gốc. |
| `frontend/src/components/ui/StatCard.tsx` | 2.811 B | Mồ côi thật sau khi gỡ trang Tổng quan, nhưng **được 8+ chỗ tài liệu trích dẫn**, xóa làm sai **hai bất biến đếm cùng lúc** — xem mục 3.2. |
| `frontend/src/lib/constants.ts` — `DEFAULT_TREND_DAYS` và 6 hằng phụ | ~1,5 KB | Bản sao hợp đồng (wire-contract mirror) **giữ có chủ đích** — xem mục 3.3. |
| `frontend/src/lib/constants.ts` — `TERMINAL_JOB_STATUSES` | — | Bẫy: 0 usage **ngoài** tệp, nhưng được dùng ở **dòng 61** (`isTerminalStatus`) ngay trong chính tệp. Grep phạm vi ngoài sẽ báo nhầm là chết. |
| `htmlcov/` | 6,5 MB | Sinh lại được bằng một lệnh, đã nằm trong `.gitignore:19`, **0 tệp được git theo dõi** — nhưng **được tài liệu trỏ tới như một artefact**: `docs/reports/07-testing-report.md:231` và `:1045` ("Báo cáo bao phủ dạng HTML"), `docs/manuals/technical-manual.md:1004`. Xóa thì đường dẫn trong tài liệu 404 cho tới khi chạy lại pytest có `--cov`. Đây là **thu hồi được nhưng không phải "thừa"**. |

### 3.2. `StatCard.tsx` — mục đáng chú ý nhất trong bảng này

Đây là trường hợp nguy hiểm nhất trong toàn bộ đợt rà soát, vì **không có công cụ tự động nào phát
hiện được thiệt hại**: bộ 912 test là pytest thuần Python, frontend không có tệp test nào, và
`eslint --max-warnings 0` cũng không báo vì component được export qua barrel. Xóa nó **không làm gãy
bất cứ thứ gì máy kiểm tra được** — thiệt hại chỉ hiện ra ở tầng tài liệu, và chỉ bị phát hiện khi
hội đồng đối chiếu.

Nó phá **hai bất biến đếm** đang đúng chính xác:

1. **"15 component nguyên thủy"** — `frontend/src/components/ui/` hiện có **đúng 15 tệp `.tsx`**
   (Badge, Button, Card, ConfidenceBar, EmptyState, ErrorState, FileDropzone, Modal, Pagination,
   PlateChip, ProgressBar, Skeleton, Spinner, **StatCard**, Table). Xóa ⇒ còn 14, làm sai
   `ch4-cai-dat.md:965`, `thesis-full.md:4293, 4309, 4661`, `technical-manual.md:187`,
   `frontend/README.md:169`.
2. **"48 mô-đun nguồn `.ts/.tsx`"** — `technical-manual.md:108` ghi số liệu **đo thực** ngày
   20/07/2026. Đếm lại: 49 tệp `.ts/.tsx` trong `frontend/src`, trừ `vite-env.d.ts` (tệp khai báo) =
   **đúng 48**. Xóa ⇒ 47, làm sai thêm `technical-manual.md:179`, `ch4-cai-dat.md:934` và `:1331`,
   `00-thesis-outline.md:395`.

Câu bị sai **hai lần cùng lúc** là `ch4-cai-dat.md:1331` — đúng đoạn số liệu dùng để bảo vệ: *"tầng
frontend (3 trang sau hai đợt thu gọn phạm vi ngày 2026-07-20, **48 mô-đun**, **15 component** nguyên
thủy dùng chung)"*. Hai bản đã dựng (`docs/papers/thesis-full.docx` 324.985 B và
`docs/slides/slides.pptx` 115.599 B) đã chứa khẳng định này.

Ngoài con số, nó còn là hiện thân mã nguồn cuối cùng của một quyết định thiết kế được bảo vệ:
`06-ui-documentation.md:473-480` chốt rằng `total_jobs` và `total_detections` phải hiển thị thành hai
thẻ riêng biệt; `docs/slides/10-demo-script.md:234` biến đúng điểm này thành điểm nhấn bảo vệ. Chính
docstring của `StatCard.tsx` mã hóa cái bẫy đó: *"A tile labelled 'Số ảnh đã xử lý' must therefore
read `total_jobs`. Filling it from `total_detections` inflates the figure… and produces a number
plausible enough to survive review."*

**Cân nhắc lợi/hại:** tiết kiệm 2,8 KB, đổi lại 8 chỗ không nhất quán trong luận văn, sổ tay kỹ
thuật, README frontend và đề cương — kể cả 2 tệp nhị phân đã dựng. Nếu vẫn muốn xóa thì **phải sửa
đồng thời cả 8 chỗ** rồi chạy lại `scripts/build_thesis.py` để sinh lại `.docx` và `.pptx`.

### 3.3. `DEFAULT_TREND_DAYS` và các hằng trong `constants.ts`

Không phải tàn dư ngẫu nhiên mà là **một nửa của bản sao hợp đồng được giữ có chủ đích** — cùng mô
hình với `models/baseline-416-v1.pt` (0 usage, giữ cố ý).

- Người tiêu thụ duy nhất là `frontend/src/pages/Dashboard.tsx`, bị xóa ở commit `270a314`
  (2026-07-20, "Thu gọn giao diện web còn 3 trang").
- **Chính commit đó đã để lại cảnh báo bằng văn bản** tại `frontend/src/types/index.ts:400`: *"No
  consumer in this application since 2026-07-20… It is kept because the endpoint it mirrors is still
  served and still tested… **Do not 'clean it up'** without also checking
  `backend/api/routes/statistics.py`."*
- `DEFAULT_TREND_DAYS = 7` khớp `backend/services/statistics_service.py:60`
  (`DEFAULT_TREND_DAYS: Final[int] = 7`). `docs/papers/ch6-ket-luan.md:222` lập luận dựa đúng vào
  điểm này: *"phần mất đi là màn hình hiển thị, không phải năng lực hệ thống"*.
- `SORT_OPTIONS` chứa 6 nhãn tiếng Việt **chỉ tồn tại ở đây** và được `user-manual.md:444-452` (mục
  8.3 "Sắp xếp") hứa hẹn với người dùng.
- `MAX_IMAGE_BYTES` / `MAX_VIDEO_BYTES` được **chính docstring đầu tệp (dòng 7–9)** gọi tên, đối ứng
  `backend/core/config.py:434` và `:439` (hai thuộc tính này có thật).

> **BẪY GREP cho lần rà soát sau:** `grep` toàn kho `"DEFAULT_TREND_DAYS"` trả về 11 hit ở
> `backend/` và `docs/`, nhưng đó là **một hằng số KHÁC trùng tên** —
> `backend/repositories/detection_repository.py:80` đặt giá trị **14** chứ không phải 7. Đếm hit thô
> sẽ đọc nhầm theo **cả hai chiều**.

---

## 4. Lệnh dọn dẹp

Dán nguyên khối vào Git Bash **tại gốc kho**. Lệnh dùng so khớp chuỗi neo chính xác và **tự hủy giữa
chừng nếu bất kỳ neo nào không khớp** (`--check` chạy trước, không sửa gì) — thà dừng còn hơn làm hỏng
tệp.

```bash
cd /d/DATN && python - <<'PY' && npm --prefix frontend run typecheck && npm --prefix frontend run lint && backend/.venv/Scripts/python.exe -m pytest -q
import sys, pathlib

# (file, old, new) — mọi neo phải khớp ĐÚNG MỘT LẦN, nếu không sẽ hủy toàn bộ.
E = []

# --- Mục 2: read_image_sizes + _progress + __all__ (scripts/dataset/_common.py) ---
c = pathlib.Path("scripts/dataset/_common.py")
E += [(c, '    "read_image_sizes",\n', "")]
E += [(c, 'def read_image_sizes(\n', None)]      # đánh dấu khối, cắt tới trước 'def write_json'
E += [(c, 'def _progress(items: Sequence[Any]', None)]  # cắt tới trước 'def _json_default'

# --- Mục 3: SkeletonText (Skeleton.tsx + ui/index.ts) ---
s = pathlib.Path("frontend/src/components/ui/Skeleton.tsx")
E += [(s, '/** Props of {@link SkeletonText}. */\n', None)]  # cắt tới trước '/** Props of {@link SkeletonTable}'
i = pathlib.Path("frontend/src/components/ui/index.ts")
E += [(i, "export { Skeleton, SkeletonTable, SkeletonText } from './Skeleton';",
          "export { Skeleton, SkeletonTable } from './Skeleton';")]
E += [(i, "  SkeletonTextProps,\n", "")]

# --- Mục 1: EmptyState + ErrorState + 3 import (StateViews.tsx) ---
v = pathlib.Path("frontend/src/components/StateViews.tsx")
E += [(v, "import { AlertCircle, Inbox, Loader2, RefreshCw } from 'lucide-react';\nimport type { LucideIcon } from 'lucide-react';",
          "import { AlertCircle, Loader2 } from 'lucide-react';")]
E += [(v, '/** Props for {@link EmptyState}. */\n', None)]  # cắt tới trước '/** Props for {@link InlineError}'
E += [(v, ' * Reusable loading, empty and error views.\n *\n * Every page has to handle the same three non-happy-path states. Centralising',
          ' * Reusable loading, section and inline-error views.\n *\n * Centralising them')]
E += [(v, 'Used where {@link ErrorState} would be too heavy',
          'Used where a full-page error view would be too heavy')]

# Khối cắt-tới-mốc: (tệp, neo đầu, mốc dừng)
BLOCKS = [
 ("scripts/dataset/_common.py", 'def read_image_sizes(\n', 'def write_json('),
 ("scripts/dataset/_common.py", 'def _progress(items: Sequence[Any]', 'def _json_default('),
 ("frontend/src/components/ui/Skeleton.tsx", '/** Props of {@link SkeletonText}. */\n', '/** Props of {@link SkeletonTable}. */'),
 ("frontend/src/components/StateViews.tsx", '/** Props for {@link EmptyState}. */\n', '/** Props for {@link InlineError}. */'),
]

texts = {}
def load(p):
    p = str(p)
    if p not in texts: texts[p] = pathlib.Path(p).read_text(encoding="utf-8")
    return texts[p]

# 1) Cắt các khối lớn
for path, start, stop in BLOCKS:
    t = load(path)
    a, b = t.find(start), t.find(stop)
    if a < 0 or b < 0 or b <= a:
        sys.exit(f"HUY: khong tim thay khoi {start!r}..{stop!r} trong {path}")
    texts[path] = t[:a] + t[b:]

# 2) Thay/xoa các chuỗi đơn
for path, old, new in E:
    if new is None: continue
    t = load(path)
    if t.count(old) != 1:
        sys.exit(f"HUY: neo xuat hien {t.count(old)} lan (can dung 1) trong {path}: {old[:60]!r}")
    texts[str(path)] = t.replace(old, new)

for p, t in texts.items():
    pathlib.Path(p).write_text(t, encoding="utf-8")
    print("da sua:", p)
PY
rm -f frontend/src/utils/format.ts && rmdir frontend/src/utils 2>/dev/null; \
echo "--- Con lai: tu sua tay 2 cho tai lieu ---"; \
echo "  1. frontend/README.md dong 162-163: xoa ca muc 'utils/' va dong 'format.ts'"; \
echo "  2. frontend/README.md dong 168: doi mo ta StateViews.tsx neu can"
```

**Sau khi chạy, ba lệnh kiểm tra ở cuối chuỗi `&&` phải cùng xanh:**
`npm run typecheck` (exit 0), `npm run lint` (exit 0), và `pytest -q` → **912 passed, 1 xfail** (con số
này không được thay đổi — `scripts/` không nằm trong `source` của `.coveragerc`, và `pytest.ini` đặt
`testpaths = tests`, nên không hạng mục nào ở bảng 2 chạm tới bộ test).

**Nếu script in ra `HUY:`** thì không tệp nào bị ghi (mọi thay đổi chỉ được ghi ở bước cuối) — nghĩa
là số dòng đã trôi so với bản rà soát này; hãy rà lại thủ công thay vì sửa neo cho khớp.

---

## 5. Những hướng đã kiểm tra và KHÔNG tìm thấy gì

Ghi lại để lần sau không phải làm lại:

- Kho **không có thư mục `.github/`** — không có CI tham chiếu tệp nào.
- `pyproject.toml`, `pytest.ini`, `.coveragerc`, `docker-compose.yml`, `Dockerfile*`, `alembic.ini`,
  `frontend/package.json`, `vite.config.ts`, `tsconfig*.json`: không tham chiếu hạng mục nào ở bảng 2.
- `docs/reports/11-definition-of-done.md`: không hạng mục nào ở bảng 2 là deliverable
  (0 hit cho `_common`, `read_image`, `scripts/dataset`, `utils`, `format`, `skeleton`).
- Frontend **không có tệp test nào** (`*.test.*` / `*.spec.*` → rỗng); `06-ui-documentation.md:594`
  ghi nhận playwright mới chỉ dùng để chụp ảnh màn hình, chưa có kiểm thử hồi quy giao diện. Đây là
  lý do bảng 3 phải tồn tại: **không có lưới an toàn tự động nào cho tầng giao diện.**
- Không có Storybook, không có `import * as` từ `components/ui`, không có gọi động qua
  `getattr`/tra cứu theo tên chuỗi trong `scripts/dataset/`.
- `.gitignore` đã phủ `__pycache__/`, `.pytest_cache/`, `.coverage`, `htmlcov/`, `frontend/dist/` —
  0 tệp trong số đó được git theo dõi, nên chúng **không làm phình kho git**; xóa chỉ tác động đĩa
  cục bộ và chúng sinh lại được.
