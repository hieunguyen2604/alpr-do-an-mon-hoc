# Nền tảng suy luận CPU và phép đo lại NFR-P2

**Ngày đo:** 2026-08-13 · **Máy:** Intel Core i5-14600K, 14 nhân vật lý / 20 luồng, 31,8 GB RAM, Windows 11, **không GPU**
**Công cụ:** `ai/evaluation/benchmark_cpu.py`, `ai/evaluation/evaluate.py`, `scripts/benchmark_runtime_nfr.py`
**Số liệu thô:** [03-cpu-benchmark.json](03-cpu-benchmark.json) · [03-evaluation-export-openvino.json](03-evaluation-export-openvino.json) · [37-nfr-p2-\*.json](.)

---

## 1. Hai khoản nợ được trả

Báo cáo này đóng hai chỗ mà quyển đồ án tự ghi là **chưa làm**:

| Nợ | Quyển ghi ở đâu | Trạng thái trước hôm nay |
|---|---|---|
| So sánh PyTorch ↔ ONNX Runtime ↔ OpenVINO | mục 5.6.3 | *"Phép so sánh này **chưa được thực hiện**"* — không có số nào |
| NFR-P2 trượt sàn (2,379 FPS) | mục 5.6.4, 5.7 | ❌, quy nguyên nhân cho bậc thang thử-lại |

Kết quả **lật cả hai**, và phần thứ hai lật theo hướng không ai dự đoán.

---

## 2. So sánh ba nền tảng suy luận

50 ảnh thật từ tập kiểm tra, 50 lượt suy luận mỗi nền tảng, 5 lượt làm nóng bị bỏ, `imgsz = 640`, batch = 1.

<!-- {{T38a}} do tre bo phat hien tren ba nen tang suy luan CPU -->

| Nền tảng | Trung bình | p50 | p95 | p99 | FPS | Nhanh hơn PyTorch |
|---|---:|---:|---:|---:|---:|---:|
| PyTorch 2.13 (CPU) | 33,09 ms | 32,37 | 40,54 | 54,42 | 30,2 | 1,00× |
| ONNX Runtime 1.27 | 24,48 ms | 24,01 | 27,18 | 31,75 | 40,9 | **1,35×** |
| **OpenVINO 2026.2** | **21,12 ms** | 20,98 | 23,37 | 25,68 | 47,4 | **1,57×** |

OpenVINO thắng ở **mọi phân vị**, và thắng đậm nhất ở đuôi: p99 giảm từ 54,42 ms xuống 25,68 ms, tức đuôi **hẹp lại 2,1 lần**. Với một hệ thống mà kỷ luật hàng đợi một khe khiến thông lượng bị chi phối bởi những lần chậm nhất, đuôi hẹp còn đáng giá hơn trung bình thấp.

### 2.1. Xuất mô hình có làm giảm độ chính xác không — câu hỏi bắt buộc phải hỏi

Mục 5.6.3 đặt điều kiện: đo tốc độ **phải** đo kèm mAP sau khi xuất, vì tăng tốc kèm suy giảm độ chính xác là **đánh đổi**, không phải khoản lãi. Đo trên toàn bộ 1.514 ảnh tập kiểm tra:

<!-- {{T38b}} do chinh xac truoc va sau khi xuat sang OpenVINO -->

| Đường đo | Chỉ số | PyTorch | OpenVINO | Chênh |
|---|---|---:|---:|---:|
| Validator Ultralytics | mAP@0,5 | 0,9829 | **0,983** | +0,0001 |
| Validator Ultralytics | mAP@0,5:0,95 | 0,7834 | **0,781** | −0,0024 |
| Harness riêng của đồ án | mAP@0,5 | 0,9712 | **0,9718** | +0,0006 |
| Harness riêng của đồ án | mAP@0,5:0,95 | 0,7625 | **0,7745** | +0,0120 |
| Harness riêng | Precision · Recall | 0,9757 · 0,9727 | 0,9739 · 0,9733 | ≈ 0 |

**Kết luận: xuất sang OpenVINO không làm suy giảm độ chính xác.** Bốn phép đo trên hai đường độc lập đều nằm trong khoảng dao động giữa các lượt chạy; không có chỉ số nào giảm quá 0,0024. Vậy **1,57× là khoản lãi thật**, không phải đánh đổi.

> **Một cái bẫy đã suýt mắc.** Nhìn thoạt tiên, harness riêng cho OpenVINO 0,9718 so với **0,9829** mà quyển công bố, và kết luận vội sẽ là *"xuất mô hình làm mất 1,1 điểm mAP"*. Sai: 0,9829 đến từ **validator Ultralytics**, còn 0,9718 đến từ **harness riêng**. Hai đường đo khác nhau thì chênh nhau là chuyện bình thường. Chỉ khi chạy lại **chính bản PyTorch qua chính harness riêng** (0,9712) mới thấy OpenVINO thực ra **nhỉnh hơn**. Bài học: so sánh chỉ có nghĩa khi hai vế đi qua cùng một đường đo.

---

## 3. Đo lại NFR-P2 — và một con số cũ không tái lập được

### 3.1. Sáu lần đo

Cùng mã nguồn, cùng cấu hình, cùng bộ ảnh phát lại, cùng harness.

<!-- {{T38c}} sau lan do NFR-P2 trong cac dieu kien may khac nhau -->

| Điều kiện | FPS hiệu dụng | p50 | p95 | Trung bình | Khung đạt | Kết luận |
|---|---:|---:|---:|---:|---:|:--:|
| **02/08 — máy tải nặng** | **2,379** | 180,05 | **1.247,70** | 401,22 | 144 | ❌ trượt sàn |
| Máy rảnh, lần 1 | **5,257** | 164,08 | 204,52 | 175,64 | 316 | ✅ vượt mục tiêu |
| Máy rảnh, lần 2 | **5,213** | 165,13 | 199,33 | 177,62 | 313 | ✅ vượt mục tiêu |
| Ép tải 6 lõi | 4,367 | 201,76 | 238,97 | 210,96 | 262 | 🟡 trên sàn |
| Ép tải 12 lõi | 4,057 | 215,69 | 268,40 | 228,88 | 244 | 🟡 trên sàn |
| **OpenVINO, máy rảnh** | **6,310** | 129,60 | 148,50 | 144,34 | 379 | ✅ vượt mục tiêu |

### 3.2. Mã nguồn không đổi — đã kiểm chứng, không phải phỏng đoán

`git diff 47ba05e HEAD -- ai/` (47ba05e là commit tại thời điểm đo cũ) trả về **đúng một tệp thêm mới**: `benchmark_engines.py`, một công cụ đo. Toàn bộ đường suy luận `ai/inference/` **giống hệt từng byte**. Hai công tắc bậc thang cũng giống hệt: `rectify_enabled = True`, `sr_retry_enabled = False` ở cả hai thời điểm. Thư mục ảnh phát lại không đổi từ 19/07, và harness chọn ảnh **theo thứ tự sắp xếp cố định** nên hai lần chạy nhận cùng một dãy ảnh.

Vậy chênh lệch 2,379 → 5,2 **không đến từ hệ thống**.

### 3.3. Giả thuyết đầu tiên — và thí nghiệm bác bỏ nó

Log của lần đo cũ cho thấy máy lúc đó đang cõng khoảng **560% CPU** của tiến trình khác: Explorer 120%, VS Code 159%, Visual Studio 68%, Claude 37%, `System` 136%, `svchost` 40%. Chính harness đã in cảnh báo *"Competing CPU load present — every timing below is PESSIMISTIC"*.

Giả thuyết hiển nhiên: **tải cạnh tranh làm chậm phép đo**. Để kiểm chứng thay vì tin, dựng tải tổng hợp bằng 6 rồi 12 tiến trình chiếm trọn lõi (`cpu_load.py`) và đo lại.

**Thí nghiệm bác bỏ giả thuyết.** Tải cạnh tranh nâng **cả phân bố** một cách khiêm tốn và đều tay:

| | p50 | p95 | Tỉ lệ p95/p50 |
|---|---:|---:|---:|
| Máy rảnh | 164,08 | 204,52 | 1,25 |
| Ép tải 6 lõi | 201,76 (+23%) | 238,97 (+17%) | 1,18 |
| Ép tải 12 lõi | 215,69 (+31%) | 268,40 (+31%) | 1,24 |
| **02/08** | **180,05 (+10%)** | **1.247,70 (+510%)** | **6,93** |

Lần đo 02/08 có **trung vị gần như của một máy rảnh** (180 ms, còn thấp hơn cả lần ép tải 6 lõi) nhưng **đuôi gấp 6,9 lần trung vị**. Ép tải tới 12 lõi cũng chỉ đẩy tỉ lệ này lên 1,24. Chữ ký hai trường hợp **khác hẳn nhau**: tải cạnh tranh làm *mọi* khung chậm đi một chút, còn thứ xảy ra hôm 02/08 làm *đa số* khung vẫn nhanh nhưng *một phần* khung chậm thảm hại.

### 3.4. Điều rút ra được, và điều không rút ra được

**Rút ra được:**

1. **NFR-P2 đạt.** Hai lần đo độc lập trên máy rảnh cho 5,257 và 5,213 FPS — vượt cả **mục tiêu** 5 FPS, không chỉ sàn 3.
2. **Kết quả bền dưới tải.** Ngay cả khi 12 trên 20 luồng bị tiến trình khác chiếm trọn, hệ thống vẫn giữ 4,057 FPS — **trên sàn 35%**. Đây mới là con số nên dùng khi nói về biên an toàn.
3. **Con số 2,379 không tái lập được** ở bất kỳ điều kiện nào trong sáu lần đo.
4. **Quy kết nguyên nhân trong quyển là chưa chứng minh được.** Mục 5.6.4 gán đuôi 1.247,70 ms cho bậc thang thử-lại. Nhưng log máy chủ lần đó cho thấy bậc thang chỉ nổ **6 lần trên 144 khung**; với giá trị chậm nhất đo được là 1.484,91 ms, 6 lần nổ chỉ giải thích được khoảng **52 ms** trong khoảng chênh 225 ms của giá trị trung bình. Bậc thang góp phần, nhưng không phải nguyên nhân chính.

**Không rút ra được:** *chính xác* cái gì đã tạo ra đuôi hôm 02/08. Ứng viên còn lại là các nguồn tranh chấp **không phải CPU thuần** mà tải tổng hợp ở đây không mô phỏng — `System` 136% là thời gian nhân, thường đi kèm quét đĩa của Windows Defender, và lần chạy đó có một bản dựng Visual Studio đang ghi đĩa. Đường suy luận có ghi ảnh và ghi cơ sở dữ liệu nên nhạy với tranh chấp đĩa. **Đây là suy đoán có cơ sở, không phải kết luận đã đo** — và được ghi ra đúng như vậy.

### 3.5. Bài học về quy trình

Đây là lần **thứ tư** trong đồ án một con số công bố mô tả trạng thái không còn đúng. Ba lần trước là do mã đổi mà số không đo lại. Lần này khác về bản chất: **mã không đổi, phép đo mới là thứ sai** — nó đo lẫn trạng thái nền của máy vào kết quả.

Điều đáng nói là harness **đã cảnh báo đúng ngay lúc đó**, in rõ danh sách tiến trình đang chiếm CPU và dán nhãn PESSIMISTIC lên toàn bộ số liệu. Cảnh báo được in ra nhưng không được đọc. Biện pháp phòng ngừa vì vậy không phải là thêm cảnh báo, mà là: **một lần đo có cảnh báo tải cạnh tranh thì không được phép trở thành số liệu công bố** cho tới khi chạy lại trên máy rảnh.

---

## 4. Có nên chuyển bản giao hàng sang OpenVINO không

**Không, chưa.** Bằng chứng ủng hộ rất mạnh — nhanh hơn 1,57× ở tầng bộ phát hiện, +20% FPS đầu-cuối (5,257 → 6,310), độ chính xác giữ nguyên. Nhưng đổi mô hình mặc định sẽ làm **mọi con số độ trễ trong Chương 5 lệch khỏi bản giao hàng**, và đồ án này đã ba lần trả giá cho việc đo lại nửa vời. NFR-P2 **đã đạt** với PyTorch (5,257 FPS) nên không cần đổi để qua chỉ tiêu.

Vì vậy: giữ `models/best.pt` làm mặc định, giữ nguyên cả `best.onnx` lẫn `best_openvino_model/` trong kho, và hạ mục *"đóng gói ONNX hoặc OpenVINO"* ở phần hướng phát triển từ **đề xuất** xuống **đã đo, sẵn sàng bật** — đổi một dòng cấu hình `ALPR_MODEL_PATH` là dùng được, vì tầng nạp mô hình đã hỗ trợ sẵn thư mục OpenVINO.

---

## 5. Cách chạy lại

```bash
python -m ai.training.export --weights models/best.pt --format all
python -m ai.evaluation.benchmark_cpu --weights models/best.pt \
    --images datasets/processed/yolo_v3/images/test --backends pytorch onnx openvino
python -m ai.evaluation.evaluate --weights models/best_openvino_model \
    --data datasets/processed/yolo_v3/data.yaml --split test
python scripts/benchmark_runtime_nfr.py --skip-soak --skip-restart
```

**Điều kiện bắt buộc khi chạy lại `benchmark_runtime_nfr.py`:** đóng IDE, trình duyệt và mọi bản dựng đang chạy. Nếu đầu ra có dòng `Competing CPU load present` thì **bỏ kết quả và chạy lại** — đó chính là cái bẫy mục 3.5 mô tả.
