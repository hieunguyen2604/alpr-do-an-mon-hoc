# Bảng số liệu Chương 5 — sinh tự động

*Sinh lúc 2026-07-19T20:15:41 bằng `scripts/fill_chapter5.py`.*

> **Điều kiện đo — bắt buộc đọc kèm mọi bảng bên dưới.** CPU Intel(R) Core(TM) i5-14600K, 14 nhân vật lý / 20 nhân logic, RAM 31,77 GB, Windows 11, Python 3.13.12, torch 2.13.0+cpu, ultralytics 8.4.101, `device=cpu`, kích thước lô = 1. Mô hình: `D:\DATN\models\baseline-416-v1.pt`. Bộ dữ liệu: `datasets\processed\yolo_v3\data.yaml`, split `test`, 1.514 ảnh.

Ô ghi `—` là ô **chưa đo được**; lý do cụ thể nằm ở khoá `ly_do` trong `docs/reports/05-results.json`. Không được điền 0 vào các ô đó.

---

## {{T5.2b}} Phiên bản thư viện

*Môi trường đo: `D:\DATN\backend\.venv`.*

| Gói | Phiên bản đo được |
|---|:---:|
| `ultralytics` | 8.4.101 |
| `torch` | 2.13.0+cpu |
| `torchvision` | 0.28.0+cpu |
| `paddleocr` | 3.7.0 |
| `paddlepaddle` | 3.3.1 |
| `onnxruntime` | 1.27.0 |
| `openvino` | 2026.2.1 |
| `opencv-python` | 4.10.0.84 |
| `numpy` | 2.3.5 |
| `fastapi` | 0.139.2 |
| `uvicorn` | 0.51.0 |
| `sqlalchemy` | 2.0.51 |
| `imagehash` | 4.3.2 |
| `pytest` | 9.1.1 |

> Chi do duoc moi truong dang chay script. Cot con lai cua bang T5.2b phai lay bang cach chay chinh script nay trong moi truong ao con lai, hoac chay 'pip freeze' cua moi truong do.

## {{T5.3b}} Số cặp gần trùng xuyên split theo ngưỡng Hamming

> ⚠ CHAY THU (--skip-slow): chi bam 300 anh train x 300 anh test thay vi toan bo split. So cap dem duoc KHONG the so sanh voi con so cua v1/v2 (do tren toan bo split) va KHONG duoc dien vao Chuong 5.

| Ngưỡng Hamming | v1 — số cặp train↔test | v2 — số cặp train↔test | **v3 — số cặp train↔test** | Ô này có mang thông tin mới không? |
|:---:|---:|---:|---:|---|
| 0 (trùng khít bit-hash) | — | — | **0** | Có |
| 5 | — | — | **0** | Không với v1, v2 (bằng ngưỡng gộp của chúng) |
| **10** | **619** | **2.699** | **0** | **Không với v3** — bằng ngưỡng gộp |
| 12 | — | — | **7** | **Có** |
| 15 | — | — | **27** | **Có** |
| 20 | — | — | **693** | Có, nhưng ngưỡng đã lỏng tới mức nhiều cặp là dương tính giả |

> Mẫu số: 300 ảnh train × 300 ảnh `test` = 90.000 cặp đã so sánh. Phương pháp: imagehash.phash 64 bit. Khoảng cách Hamming nhỏ nhất quan sát được: **12**.
>
> Cot v1 va v2 chi co so o nguong 10 vi do la con so da do truoc do tren hai bo du lieu ay; cac o con lai cua hai cot do de trong chu KHONG duoc suy ra. O v3 tai nguong 10 bang hoac gan 0 la HE QUA DINH NGHIA (v3 duoc khu trung lap o dung nguong 10), khong phai phat hien thuc nghiem — chi cac nguong 12, 15, 20 moi mang thong tin moi. Phash khong bat duoc ro ri o muc ngu nghia (cung mot bien so chup goc khac), nen ket qua thap KHONG chung minh tap test doc lap.

## {{T5.3c}} Phân bố nguồn dữ liệu giữa các split

| Nguồn dữ liệu | Tổng số ảnh | Train (số / %) | Val (số / %) | Test (số / %) | Ghi chú |
|---|---:|---:|---:|---:|---|
| `hf_vn_plates_segment|roboflow_cuong_ta|roboflow_eric_nguyen|roboflow_school_fuhih|roboflow_traffic_camera` | 4.411 | 4.411 / 100,0% | 0 / 0,0% | 0 / 0,0% | — |
| `roboflow_school_fuhih` | 3.599 | 2.275 / 63,2% | 938 / 26,1% | 386 / 10,7% | — |
| `hf_vn_plates_segment` | 2.820 | 1.933 / 68,5% | 574 / 20,3% | 313 / 11,1% | — |
| `roboflow_traffic_camera` | 2.582 | 1.368 / 53,0% | 689 / 26,7% | 525 / 20,3% | lech quá 10 điểm phần trăm so với tỉ lệ test tổng thể — phải nêu tên nguồn này và thảo luận ảnh hưởng ở mục 5.3.4 |
| `hf_vn_plates_segment|roboflow_school_fuhih` | 634 | 78 / 12,3% | 527 / 83,1% | 29 / 4,6% | — |
| `roboflow_eric_nguyen` | 351 | 228 / 65,0% | 77 / 21,9% | 46 / 13,1% | — |
| `roboflow_school_fuhih|roboflow_traffic_camera` | 250 | 4 / 1,6% | 72 / 28,8% | 174 / 69,6% | lech quá 10 điểm phần trăm so với tỉ lệ test tổng thể — phải nêu tên nguồn này và thảo luận ảnh hưởng ở mục 5.3.4 |
| `roboflow_demo_tracking` | 210 | 139 / 66,2% | 51 / 24,3% | 20 / 9,5% | — |
| `roboflow_cuong_ta` | 136 | 88 / 64,7% | 33 / 24,3% | 15 / 11,0% | — |
| `roboflow_demo_tracking|roboflow_traffic_camera` | 57 | 32 / 56,1% | 22 / 38,6% | 3 / 5,3% | — |
| `hf_vn_plates_segment|roboflow_traffic_camera` | 50 | 29 / 58,0% | 18 / 36,0% | 3 / 6,0% | — |
| `hf_vn_plates_segment|roboflow_school_fuhih|roboflow_traffic_camera` | 20 | 0 / 0,0% | 20 / 100,0% | 0 / 0,0% | — |
| `hf_vn_plates_segment|roboflow_demo_tracking|roboflow_traffic_camera` | 4 | 0 / 0,0% | 4 / 100,0% | 0 / 0,0% | — |
| `roboflow_cuong_ta|roboflow_school_fuhih` | 4 | 2 / 50,0% | 2 / 50,0% | 0 / 0,0% | — |
| `hf_vn_plates_segment|roboflow_eric_nguyen|roboflow_school_fuhih` | 3 | 3 / 100,0% | 0 / 0,0% | 0 / 0,0% | — |
| `roboflow_demo_tracking|roboflow_school_fuhih` | 2 | 2 / 100,0% | 0 / 0,0% | 0 / 0,0% | — |
| **Tổng** | **15.133** | **10.592 / 70,0%** | **3.027 / 20,0%** | **1.514 / 10,0%** | |

> 16 tổ hợp xuất xứ, dựng từ **6 nguồn nguyên tố**: `roboflow_school_fuhih`, `hf_vn_plates_segment`, `roboflow_traffic_camera`, `roboflow_eric_nguyen`, `roboflow_cuong_ta`, `roboflow_demo_tracking`. Nguồn lệch quá 10 điểm phần trăm ở tập test: `roboflow_traffic_camera`, `roboflow_school_fuhih|roboflow_traffic_camera`. Số bản ghi không rõ split: 0.
>
> Moi dong la mot TO HOP xuat xu, khong phai mot nguon: sau khi khu trung lap, mot anh giu lai co the den tu nhieu nguon cung luc va manifest ghi ca tap xuat xu ngan cach bang '|'. Do do so dong lon hon con so 6 nguon nguyen to cua tap v3; khoa 'nguon_nguyen_to' liet ke tung nguon rieng le, nhung cac so trong do CONG DON QUA 15.133 vi anh da nguon bi dem nhieu lan — khong duoc dung lam mau so. Ti le cua tung dong tinh theo mau so la TONG SO ANH CUA CHINH DONG do, khong phai tong toan bo corpus. Cot lech so sanh ti le test cua dong voi ti le test tong the; nguong canh bao 10.0 diem phan tram lay tu tieu chi doc bang o muc 5.3.4.

## {{T5.4b}} Tiến triển chỉ số trên tập validation theo epoch

| Epoch | `box_loss` (val) | `cls_loss` (val) | `dfl_loss` (val) | mAP@0.5 | mAP@0.5:0.95 | Precision | Recall |
|:---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1,1705 | 0,6858 | 1,1513 | **0,9684** | **0,6526** | 0,9552 | 0,9410 |
| 2 | 1,1861 | 0,5554 | 1,1307 | **0,9726** | **0,6653** | 0,9700 | 0,9450 |
| 3 | 1,1647 | 0,5651 | 1,1098 | **0,9723** | **0,6770** | 0,9731 | 0,9449 |
| 4 | 1,0362 | 0,5156 | 1,0670 | **0,9740** | **0,7120** | 0,9782 | 0,9462 |
| 5 | 1,1074 | 0,4977 | 1,0863 | **0,9754** | **0,6950** | 0,9765 | 0,9525 |

Epoch tốt nhất theo mAP@0.5:0.95 trên val: **4** (5 epoch đã chạy).

> ⚠ moi co 5/20 epoch — luot huan luyen CHUA ket thuc, khong duoc cong bo cac dong nay nhu ket qua cuoi cung

## {{T5.5a}} Kết quả detection tổng thể

| Chỉ số | Mã NFR | Ngưỡng tối thiểu | Mục tiêu | **Đo được** | Kết quả |
|---|:---:|---:|---:|---:|:---:|
| mAP@0.5 | NFR-A1 | 0,85 | 0,90 | **0,9967** | ✅ đạt |
| mAP@0.5:0.95 | NFR-A2 | 0,55 | 0,65 | **0,8448** | ✅ đạt |
| Precision | NFR-A3 | 0,88 | 0,92 | **0,9538** | ✅ đạt |
| Recall | NFR-A3 | 0,85 | 0,90 | **1,0000** | ✅ đạt |
| F1 | — | — | — | 0,9764 | n/a |
| Ngưỡng confidence dùng khi đo | — | — | — | 0,25 | n/a |
| Số ảnh tập test | — | — | — | **200** | n/a |
| Số đối tượng nhãn thật | — | — | — | **248** | n/a |

> Nguồn chỉ số: `bo_doi_sanh_noi_bo_evaluate.py`. evaluate.py bao cao chi so tai nguong conf co dinh; duong cong F1 theo nguong nam trong hinh 05-detection-f1-curve.png. Nguong toi uu phai doc tu hinh do, khong suy tu bang nay.

## {{T5.5b}} Detection tách theo layout (NFR-A8)

| Chỉ số | Biển **một dòng** | Biển **hai dòng** | Chênh lệch (điểm %) | Mẫu số |
|---|---:|---:|---:|---:|
| Số đối tượng nhãn thật | 45 | 203 | n/a | 248 |
| mAP@0.5 | 0,9966 | 0,9976 | -0,10 | |
| mAP@0.5:0.95 | 0,7822 | 0,8588 | -7,66 | |
| Precision | 0,9783 | 0,9486 | 2,97 | |
| Recall | 1,0000 | 1,0000 | 0,00 | |
| F1 | 0,9890 | 0,9736 | 1,54 | |

> Ngưỡng tỉ lệ khung hình: 2,5. Tỉ lệ ô được suy bằng heuristic: 1,0000. Layout duoc suy tu ty le khung hinh 2,5 cho phan lon hop giới han vi bo du lieu khong khai bao lop layout. Day la UOC LUONG, khong phai nhan that — moi ket luan ve NFR-A8 phai neu ro dieu nay.
>
> Mốc baseline (`baseline-416-v1.pt`, split v1, imgsz 416): một dòng 0,9856 so với hai dòng 0,9592, chênh 2,6 điểm. So cua baseline-416-v1.pt (split v1, imgsz 416) — KHONG duoc chuyen thanh so cua best.pt.

## {{T5.5c}} Detection tách theo dải kích thước hộp giới hạn

| Dải kích thước (diện tích box / diện tích ảnh) | Số đối tượng | Tỉ lệ trong tập test | mAP@0.5 | mAP@0.5:0.95 | Recall |
|---|---:|---:|---:|---:|---:|
| **Rất nhỏ** — dưới 0,5% | 37 | 14,92% | 0,9241 | 0,7306 | 1,0000 |
| **Nhỏ** — 0,5% đến 1% | 24 ⚠ | 9,68% | 1,0000 | 0,8116 | 1,0000 |
| **Trung bình** — 1% đến 5% | 133 | 53,63% | 1,0000 | 0,8542 | 1,0000 |
| **Lớn** — 5% đến 15% | 52 | 20,97% | 1,0000 | 0,8879 | 1,0000 |
| **Rất lớn** — trên 15% | 2 ⚠ | 0,81% | 1,0000 | 0,7500 | 1,0000 |
| **Toàn tập test** | **248** | 100% | **0,9967** | **0,8448** | **1,0000** |

> Đo trên 200 ảnh. Số box không gán được dải: 0. Dòng có ⚠ là dòng dưới 30 đối tượng — **không có ý nghĩa thống kê**, không được đưa vào so sánh. Dai duoc tinh tu (w x h) cua hop nhan that chia cho dien tich anh goc. Chi so cua moi dai tinh bang chinh ham evaluate_group cua ai/evaluation/evaluate.py nen cong thuc mAP la duy nhat trong do an.

## {{T5.6a}} Độ chính xác mức ký tự (NFR-A4)

| Chỉ số | Ngưỡng tối thiểu | Mục tiêu | **Đo được (trước hậu xử lý)** | **Đo được (sau hậu xử lý)** | Kết quả |
|---|---:|---:|---:|---:|:---:|
| 1 − CER (NFR-A4) | 0,92 | 0,95 | 0,8829 | **0,8829** | ❌ không đạt |
| CER | ≤ 0,08 | ≤ 0,05 | 0,1171 | 0,1171 | n/a |
| Số ký tự nhãn thật ($N$) | — | — | 521 | 521 | n/a |
| Số ký tự thay thế ($S$) | — | — | 15 | 15 | n/a |
| Số ký tự bị xoá ($D$) | — | — | 29 | 29 | n/a |
| Số ký tự chèn thừa ($I$) | — | — | 17 | 17 | n/a |
| **Số biển có nhãn chuỗi (mẫu số)** | — | — | **60** | **60** | n/a |

> dan ra tu confusion_matrix cua 05-ocr-accuracy.json: S = tong o ngoai duong cheo, D = tong deletions, I = tong insertions, N = tong ma tran cong D. Khong phai so uoc luong. Ba cột $S$/$D$/$I$ đo trên **chuỗi thô trước hậu xử lý**, nên chúng giống nhau ở cả hai cột đo được.

> Phân bố số ca theo loại lỗi: `{'correct': 39, 'empty_read': 0, 'substitution': 8, 'missing_chars': 4, 'extra_chars': 2, 'transposition': 0, 'mixed': 7}`.

## {{T5.6b}} Chuỗi đầy đủ trước và sau hậu xử lý (NFR-A5 ↔ A6)

| Chỉ số | Mã NFR | Ngưỡng tối thiểu | Mục tiêu | **Đo được** | Kết quả |
|---|:---:|---:|---:|---:|:---:|
| Độ chính xác chuỗi **trước** hậu xử lý | NFR-A5 | 0,80 | 0,85 | **0,6167** | ❌ không đạt |
| Độ chính xác chuỗi **sau** hậu xử lý | NFR-A6 | 0,85 | 0,90 | **0,6500** | ❌ không đạt |
| **Mức cải thiện (A6 − A5), điểm %** | — | — | — | **3,33** | n/a |
| Số biển **được sửa đúng** nhờ hậu xử lý | — | — | — | 2 | n/a |
| Số biển **bị hậu xử lý làm hỏng** | — | — | — | 0 | n/a |
| Số biển sai cả trước lẫn sau | — | — | — | 21 | n/a |
| **Số mẫu (biển có nhãn chuỗi)** | — | — | — | **60** | n/a |

> Nhánh diễn giải phải giữ lại ở mục 5.6.2: **nhánh A** (A nếu hiệu số dương, B nếu bằng 0 hoặc âm).
>
> Bảng phân rã theo nhóm luật: *(chưa đo)* — Chua co co che bat/tat tung nhom luat trong ai/inference/plate_rules.py. Muc D.2 cua ch5-thuc-nghiem.md ghi day la hang muc can viet ma truoc khi dien duoc.

## {{T5.6c}} OCR tách theo layout

| Chỉ số | Biển **một dòng** | Biển **hai dòng** | Chênh lệch (điểm %) |
|---|---:|---:|---:|
| Số mẫu có nhãn chuỗi | **10** | **50** | n/a |
| 1 − CER (NFR-A4) | 1,0000 | 0,8614 | 13,86 |
| Chuỗi đúng **trước** hậu xử lý (A5) | 1,0000 | 0,5400 | 46,00 |
| Chuỗi đúng **sau** hậu xử lý (A6) | 1,0000 | 0,5800 | 42,00 |
| Mức cải thiện do hậu xử lý (A6 − A5) | 0,00 | 4,00 | n/a |
| Độ chính xác E2E (A7) | 0,0000 | 0,0000 | — |

> Laroca va cong su (VISAPP 2022) bao cao 94,3% (bien mot dong) so voi 45,7% (bien hai dong), chenh 48,6 diem, do tren bo du lieu RodoSol-ALPR CUA BRAZIL. Day KHONG phai so lieu Viet Nam.

## {{T5.6d}} Cặp ký tự bị nhầm nhiều nhất

| Hạng | Ký tự thật | Ký tự bị đọc thành | Số lần | Tỉ lệ trong tổng số lỗi thay thế | Bảng luật hiện có phủ cặp này không? | Hướng ánh xạ có đúng không? |
|:---:|:---:|:---:|---:|---:|:---:|---|
| 1 | E | F | 2 | 13,33% | không | chưa có luật nào phủ cặp này |
| 2 | U | 1 | 2 | 13,33% | không | chưa có luật nào phủ cặp này |
| 3 | 0 | U | 1 | 6,67% | không | chưa có luật nào phủ cặp này |
| 4 | 1 | 8 | 1 | 6,67% | không | chưa có luật nào phủ cặp này |
| 5 | 4 | L | 1 | 6,67% | không | chưa có luật nào phủ cặp này |
| 6 | 5 | 8 | 1 | 6,67% | không | chưa có luật nào phủ cặp này |
| 7 | 5 | 9 | 1 | 6,67% | không | chưa có luật nào phủ cặp này |
| 8 | 6 | 5 | 1 | 6,67% | không | chưa có luật nào phủ cặp này |
| 9 | A | 4 | 1 | 6,67% | có (`TO_DIGIT`) | đúng chiều — luật `A → 4` thuộc TO_DIGIT |
| 10 | H | M | 1 | 6,67% | không | chưa có luật nào phủ cặp này |

> Ma trận `36x36`, mẫu số 60 biển có nhãn chuỗi, tổng số lỗi thay thế (S) = 15. Cột tỉ lệ lấy S làm mẫu số, không lấy tổng của riêng nhóm dẫn đầu. Bảng đối chiếu ngược — các cặp **có trong bảng luật nhưng không quan sát thấy** — nằm ở khoá `doi_chieu_bang_luat.unobserved` trong `05-results.json`.

## {{T5.6e}} Độ chính xác E2E toàn trình (NFR-A7)

| Chỉ số | Ngưỡng tối thiểu | Mục tiêu | **Đo được** | Kết quả |
|---|---:|---:|---:|:---:|
| Độ chính xác E2E (NFR-A7) | 0,82 | 0,88 | **0,0000** | ❌ không đạt |
| Độ chính xác E2E **với điều kiện đã phát hiện được biển** | — | — | 0,0000 | n/a |
| Tỉ lệ biển **bị bỏ sót** ở tầng phát hiện | — | — | 0,5667 | n/a |
| Tỉ lệ biển phát hiện đúng nhưng **đọc sai chuỗi** | — | — | 1,0000 | n/a |
| Chênh lệch A6 − A7 (điểm %) | — | — | 65,00 | n/a |
| **Số mẫu** | — | — | **30** | n/a |

> ⚠ **Cảnh báo hiệu lực:** Con so nay do tren anh CROP bien so, khong phai anh hien truong, vi khong bo du lieu nao trong do an co dong thoi anh toan canh va chuoi bien so. Bo detect duoc huan luyen tren anh giao thong day du nen mot tam anh chi co bien so chiem gan het khung la NGOAI PHAN BO: phan lon that bai la do detect khong bat duoc box, khong phai do OCR doc sai (xem e2e.exact_given_detected va e2e.missed_by_detector). Phase 7 do duoc mAP50 = 0,9935 cho bo detect tren anh hien truong that. De do NFR-A7 dung cach can gan nhan chuoi bien so cho mot phan bo test cua yolo_v2 -- viec nay CHUA lam.

## {{T5.7a}} Độ trễ đầu-cuối một ảnh (NFR-P1)

| Chỉ số | Ngưỡng tối thiểu | Mục tiêu | **Đo trên `baseline-416-v1.pt`** | **Đo trên mô hình đang đánh giá** | Kết quả |
|---|---:|---:|---:|---:|:---:|
| Độ trễ E2E p50 (ms) | — | — | — | 218,63 | n/a |
| **Độ trễ E2E p95 (ms)** | **≤ 1500** | **≤ 800** | **5.857,19** | **284,54** | **✅ đạt** |
| Độ trễ E2E p99 (ms) | — | — | — | 318,15 | n/a |
| Độ trễ trung bình (ms) | — | — | — | 222,66 | n/a |
| Độ lệch chuẩn (ms) | — | — | — | — | n/a |
| Số ảnh đo | — | — | 100 | **20** | n/a |
| Bội số vượt ngưỡng tối thiểu | — | — | 3,90× | 0,19× | n/a |
| Bội số vượt mục tiêu | — | — | 7,32× | 0,36× | n/a |

> Số biển trung bình mỗi ảnh: 1,00. Hai cột **không thay thế được cho nhau** — chúng đo hai mô hình ở hai độ phân giải khác nhau.

## {{T5.7b}} Phân rã ngân sách độ trễ theo từng bước

| Bước xử lý | Ước lượng Phase 0 (ms) | **Đo thật (ms)** | Chênh lệch (lần) | % tổng thời gian |
|---|---:|---:|---:|---:|
| Giải mã ảnh + tiền xử lý | 50 | 2,94 | 0,06 | 1,2% |
| Suy luận YOLO11n @ 640px (CPU) | 150 | 111,90 | 0,75 | 45,3% |
| Cắt + tiền xử lý vùng biển số | 30 | 0,00 | 0,00 | 0,0% |
| **PaddleOCR (mỗi biển)** | 120 | 132,35 | 1,10 | 53,5% |
| Hậu xử lý regex + kiểm tra hợp lệ | 5 | 0,04 | 0,01 | 0,0% |
| Ghi CSDL + lưu ảnh | 50 | — | — | — |
| **Tổng (một biển số)** | **405** | **247,23** | **0,70** | **100%** |

> Mẫu số: 20 ảnh, trung bình 1,00 biển mỗi ảnh. Buoc 'ghi CSDL + luu anh' khong co doi ung trong so do vi benchmark_system do pipeline suy luan thuan, khong di qua tang API — o 'do that' cua no giu '—'. Cot ty so 'chenh lech (lan)' o dong tong vi vay so voi uoc luong CUNG PHAM VI (da tru buoc ghi CSDL), khong so voi con so 405 ms tron.

## {{T5.7c}} So sánh backend suy luận

*(chưa đo)* — khong tim thay ban xuat ONNX/OpenVINO cho baseline-416-v1.pt (da tim canh trong so va trong models/checkpoints/exported/). Xuat truoc bang: yolo export model=D:\DATN\models\baseline-416-v1.pt format=onnx imgsz=640

## {{T5.7d}} Webcam và xử lý video (NFR-P2, NFR-P3)

*(chưa đo)* — chua co kich ban do webcam/video. Muc D.3 cua ch5-thuc-nghiem.md ghi day la hang muc can viet ma, va khi viet phai kem dinh nghia tuong minh cua 'FPS hieu dung' (khung hinh duoc NHAN DANG moi giay hay khung hinh duoc HIEN THI moi giay).

## {{T5.7e}} Chịu tải, bộ nhớ, độ tin cậy

| Chỉ số | Mã NFR | Ngưỡng tối thiểu | Mục tiêu | **Đo được** | Kết quả |
|---|:---:|---:|---:|---:|:---:|
| Thời gian nạp mô hình (giây) | NFR-P4 | ≤ 30 | ≤ 15 | 6,41 *(baseline)* | ✅ đạt |
| Khởi động đến khi `/health` sẵn sàng (giây) | NFR-P4b | ≤ 30 | ≤ 15 | 8,36 *(baseline)* | ✅ đạt |
| Overhead của API, p95 (ms) | NFR-P5 | ≤ 100 | ≤ 50 | 19,01 *(baseline)* | ✅ đạt |
| Truy vấn lịch sử 10.000 bản ghi, p95 (ms) | NFR-P6 | ≤ 1000 | ≤ 500 | 18,71 *(baseline)* | ✅ đạt |
| RSS pipeline (GB) | NFR-P7a | ≤ 4 | ≤ 2 | 0,759 *(baseline)* | ✅ đạt |
| RSS máy chủ backend (GB) | NFR-P7b | ≤ 4 | ≤ 2 | 0,806 *(baseline)* | ✅ đạt |
| Số yêu cầu đồng thời xử lý ổn định | NFR-SC1 | ≥ 5 | ≥ 5 | — | ⬜ chưa đo |
| Tỉ lệ thành công soak 300 giây | NFR-R4 | ≥ 99% | ≥ 99% | 100% (185/185) *(baseline)* | ✅ đạt |
| Tăng RSS sau soak (GB) | — | không có | không có | — | ⬜ chưa đo |
| Cơ sở dữ liệu sống sót qua khởi động lại | NFR-R5 | 100% | 100% | — | ⬜ chưa đo |

> ⚠ Phần chịu tải chưa chạy lại cho mô hình này: bo qua theo --skip-slow. Chay lai khong co co nay de do (khoang 10 phut).

## {{T5.8}} So sánh baseline 416/v1 với mô hình chính thức 640/v3

| Hạng mục | `baseline-416-v1.pt` | Mô hình đang đánh giá | Chênh lệch |
|---|---:|---:|---:|
| `imgsz` | 416 | **640** | +224 px |
| Bộ dữ liệu | v1 — 4.578 ảnh, 1 nguồn | **v3 — 15.133 ảnh, 6 nguồn nguyên tố (hợp nhất từ 7 bộ)** | ×3,3 |
| Ngưỡng gộp trùng lặp | 5 | **10** | +5 |
| Số epoch | 40 | 5 | — |
| mAP@0.5 | **0,9933** *(epoch 38)* | **0,9967** | 0,0034 |
| mAP@0.5:0.95 | **0,8597** *(epoch 38)* | **0,8448** | -0,0149 |
| Precision | **0,9822** | 0,9538 | -0,0283 |
| Recall | **0,9810** | 1,0000 | 0,0190 |
| mAP biển một dòng | **0,9856** | 0,9966 | — |
| mAP biển hai dòng | **0,9592** | 0,9976 | — |
| Chênh lệch theo layout (điểm %) | **2,6** | -0,10 | — |
| Độ trễ E2E p95 (ms) | **5.857,19** | 284,54 | — |

> ⚠ Ba bien thay doi dong thoi (imgsz, bo du lieu + cach chia, so epoch) va chung tac dong NGUOC CHIEU nhau. Phat bieu duy nhat duoc phep la mo ta: 'cau hinh A cho X, cau hinh B cho Y'. Khong duoc quy ket nguyen nhan cho bat ky bien nao.

## {{T5.9}} Đối chiếu chỉ tiêu NFR (phần đo được bằng script này)

| Mã | Chỉ tiêu | Ngưỡng tối thiểu | Mục tiêu | **Đo được** | Kết quả |
|:---:|---|---:|---:|---:|:---:|
| P1 | Độ trễ E2E một ảnh, p95 (ms) | 1.500,00 | 800,00 | 284,5400 | ✅ đạt |
| P2 | Tốc độ khung hình webcam (FPS) | — | — | — *(chua co kich ban do webcam — muc D.3 cua ch5-thuc-nghiem.md)* | ⬜ chưa đo |
| P3 | Tốc độ xử lý video (× thời gian thực) | — | — | — *(chua co kich ban do video)* | ⬜ chưa đo |
| P4 | Thời gian nạp mô hình (s) | 30,00 | 15,00 | 6,4100 *(do tren baseline-416-v1.pt)* | ✅ đạt |
| P5 | Overhead API, p95 (ms) | 100,00 | 50,00 | 19,0100 *(do tren baseline-416-v1.pt)* | ✅ đạt |
| P6 | Truy vấn 10.000 bản ghi, p95 (ms) | 1.000,00 | 500,00 | 18,7100 *(do tren baseline-416-v1.pt)* | ✅ đạt |
| P7a | RSS pipeline (GB) | 4,00 | 2,00 | 0,7590 | ✅ đạt |
| P7b | RSS máy chủ backend (GB) | 4,00 | 2,00 | 0,8060 | ✅ đạt |
| A1 | mAP@0.5 của bộ phát hiện | 0,85 | 0,90 | 0,9967 | ✅ đạt |
| A2 | mAP@0.5:0.95 của bộ phát hiện | 0,55 | 0,65 | 0,8448 | ✅ đạt |
| A3-P | Precision phát hiện | 0,88 | 0,92 | 0,9538 | ✅ đạt |
| A3-R | Recall phát hiện | 0,85 | 0,90 | 1,0000 | ✅ đạt |
| A4 | 1 − CER (mức ký tự) | 0,92 | 0,95 | 0,8829 | ❌ không đạt |
| A5 | Chuỗi đầy đủ trước hậu xử lý | 0,80 | 0,85 | 0,6167 | ❌ không đạt |
| A6 | Chuỗi đầy đủ sau hậu xử lý | 0,85 | 0,90 | 0,6500 | ❌ không đạt |
| A6−A5 | Đóng góp của khối hậu xử lý (điểm %) | — | — | 3,3300 | n/a |
| A7 | Độ chính xác E2E toàn trình | 0,82 | 0,88 | 0,0000 | ❌ không đạt |
| A8 | Chênh lệch layout, detection (điểm %) | — | — | -0,1000 | n/a |
| A9 | Tách theo điều kiện ảnh | — | — | — *(bo du lieu KHONG co nhan dieu kien anh — day la han che that, khong phai 'chua toi luot do'. Khong duoc gan nhan bang suy doan.)* | ⬜ chưa đo |
| R4 | Tỉ lệ thành công soak 300 s | 0,99 | 0,99 | — | ⬜ chưa đo |
| R5 | CSDL sống sót qua khởi động lại | — | — | — *(chua chay kich ban khoi dong lai)* | ⬜ chưa đo |
| SC1 | Số yêu cầu đồng thời xử lý ổn định | 5,00 | 5,00 | — | ⬜ chưa đo |
| M2 | Độ bao phủ test tầng nghiệp vụ | — | — | 0,8810 *(861/862 test pass, 1 xfail, 0 fail; toan kho 42,0%)* | n/a |

## {{T5.10}} Tần suất các loại lỗi

| Mã | Loại lỗi | Số ca | Tỉ lệ trong tổng số ca sai | Tỉ lệ trong toàn tập đánh giá | Biển một dòng | Biển hai dòng |
|:---:|---|---:|---:|---:|---:|---:|
| E1 | Bỏ sót biển | 17 | — | — | — | — |
| E2 | Phát hiện nhầm | — | — | — | — | — |
| E3 | Nhầm ký tự | 8 | 38,10% | 13,33% | 0 | 8 |
| E4 | Thiếu ký tự | 4 | 19,05% | 6,67% | 0 | 4 |
| E5 | Thừa ký tự | 2 | 9,52% | 3,33% | 0 | 2 |
| E6 | Sai thứ tự | 0 | 0,00% | 0,00% | 0 | 0 |
| | **Tổng số ca sai** | **21** | 100% | 35,00% | — | — |
| | **Tổng số ca đánh giá (mẫu số)** | **60** | n/a | 100% | — | — |

> **Mẫu số của E1 khác mẫu số của E3–E6.** E1 lấy từ lượt đo E2E của bảng T5.6e (30 mẫu), còn E3–E6 lấy từ lượt đo trên vùng cắt (60 mẫu). Hai cột tỉ lệ vì vậy **cố ý để trống ở dòng E1** — gộp chung một mẫu số sẽ cho ra con số vô nghĩa. Tỉ lệ E1 trên mẫu số riêng của nó: 56,67%.
>
> E2 (phát hiện nhầm) để `—`: số dương tính giả nằm ở bảng T5.5a và cũng không cùng mẫu số với E3–E6.
>
> Hai loại lỗi ngoài khung E1–E6: `empty_read` = 0, `mixed` = 7. Hai loai nay co trong cai dat nhung khong co ma E tuong ung trong bang 5.10.1. Phai them dong cho chung hoac gop co giai thich — khong duoc bo im lang vi khi do tong se khong bang 100%.

---

*Toàn bộ số liệu và lý do của các ô `—` nằm trong `docs/reports/05-results.json`.*
