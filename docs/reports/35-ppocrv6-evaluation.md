# PP-OCRv6 — vì sao đồ án vẫn dùng v5 mobile

**Ngày:** 2026-08-02
**Trả lời câu hỏi bỏ ngỏ tại** [01-ocr-comparison.md](01-ocr-comparison.md) mục 2.1:
*"chưa xác định được PP-OCRv6 đã có sẵn trong gói `paddleocr 3.7.0` hay chưa và
tải model ở đâu"*

---

## 1. Có sẵn không — có, nhưng chỉ một bậc

Quét toàn bộ gói `paddleocr 3.7.0` đã cài tìm thấy **đúng ba** định danh v6:

```
PP-OCRv6
PP-OCRv6_medium_det
PP-OCRv6_medium_rec
```

**Không có bản Tiny, không có bản Small.** Đây là điểm quyết định, vì bậc hấp
dẫn cho một hệ thống chạy CPU chính là **Tiny** — bài báo ghi 0,20 s/ảnh, nhanh
hơn PP-OCRv5_mobile (0,78 s) **3,9 lần**. Bậc duy nhất tải được lại là **Medium**,
bậc mà chính bài báo ghi **1,40 s/ảnh**, tức *chậm hơn* v5_mobile 1,8 lần.

## 2. Đo trên máy thật, trên biển số thật

Số của bài báo đo trên **Intel Xeon 8350C + OpenVINO** và trên **văn bản tài
liệu**, không phải trên biển số. Vì vậy phải tự đo.

**Cách đo:** 200 vùng cắt biển số nguyên ảnh từ tập kiểm định (`val.txt`, không
augment, không mảnh vụn), chạy **chỉ nhánh nhận dạng** để cô lập đúng biến đang
so sánh. Cùng máy, cùng ảnh, cùng thứ tự.

<!-- {{T35}} PP-OCRv6_medium_rec so voi PP-OCRv5_mobile_rec -->

| Mô hình | Đúng chuỗi | Trung vị | p95 |
|---|---:|---:|---:|
| **PP-OCRv5_mobile_rec** — *đang dùng* | 134/200 = **67,0%** | **23,0 ms** | 31,9 ms |
| PP-OCRv6_medium_rec | 145/200 = **72,5%** | **386,9 ms** | 429,0 ms |

**v6 Medium chính xác hơn 5,5 điểm và chậm hơn 16,8 lần.**

Chiều của kết quả khớp bài báo — v6 Medium *đúng là* chính xác hơn — nhưng biên
độ chi phí trên máy này lớn hơn nhiều so với tỷ lệ 1,8 lần mà bài báo ghi, vì
bài đo có OpenVINO còn đồ án chạy PaddlePaddle thuần.

## 3. Vì sao 5,5 điểm ấy vẫn không đủ

Hệ thống hiện đã **căng về độ trễ ở cả hai đầu**:

| | Hiện tại | Ngưỡng |
|---|---:|---|
| NFR-P1 độ trễ p95 | 1.143 ms | 🟡 sàn 1.500 · mục tiêu 800 |
| NFR-P2 FPS webcam | 2,379 | ❌ sàn 3 |

Bước OCR trong đường ống chiếm **108,28 ms/biển** (T5.7b), trong đó nhánh nhận
dạng chỉ khoảng **23 ms** — phần còn lại là bước phát hiện chữ. Thay v5 bằng v6
Medium cộng thêm khoảng **364 ms mỗi biển**.

> **Đây là phép chiếu, không phải phép đo.** Cộng 364 ms vào p95 hiện hành cho
> **≈ 1.507 ms**, tức **vượt sàn 1.500 ms** và đẩy NFR-P1 từ 🟡 xuống ❌. Con số
> này suy ra từ độ trễ nhánh nhận dạng đo cô lập, chưa chạy lại toàn đường ống —
> muốn công bố phải đo thật. Nhưng ngay cả với sai số rộng, hướng của kết luận
> không đổi: **NFR-P2 vốn đã trượt sàn thì chắc chắn trượt sâu hơn.**

## 4. Quyết định

**Giữ PP-OCRv5_mobile_rec.** Đổi sang v6 Medium là mua 5,5 điểm chính xác bằng
cách phá vỡ một chỉ tiêu đang đạt sàn và làm tệ thêm một chỉ tiêu đang trượt.

Đây **không phải** kết luận "v6 kém hơn" — nó chính xác hơn thật. Đây là kết luận
về **ràng buộc phần cứng của đồ án**: hệ thống chạy CPU thuần, và bậc v6 phù hợp
với ràng buộc đó (Tiny) **không có trong gói**.

## 5. Điều kiện để xét lại

| Điều kiện | Vì sao đủ để đảo quyết định |
|---|---|
| **PaddleOCR phát hành PP-OCRv6_tiny** vào gói pip | Bậc này được ghi là nhanh hơn v5_mobile 3,9 lần — nếu đúng thì nó cải thiện *cả* độ chính xác *lẫn* độ trễ, không phải đánh đổi |
| **Xuất v6 Medium sang ONNX / OpenVINO** | Khảo sát ghi mức tăng tốc 3–21% với PP-OCRv4_mobile và tối đa 8,6 lần ở một cấu hình khác. Nếu đạt trên 8 lần thì 386 ms về khoảng 45 ms và bài toán đổi hẳn |
| **Triển khai có GPU** | Toàn bộ lập luận này dựa trên ràng buộc CPU-only (CON-02) |

Hai điều kiện đầu đều **đo được**, và cả hai đều nằm trong hướng phát triển đã ghi
ở ch6. Cho tới lúc đó, con số 5,5 điểm là **dư địa đã định lượng**, không phải
một cơ hội bị bỏ lỡ.

## 6. Một lưu ý khi trích bài PP-OCRv6 vào quyển

Cảnh báo ở [01-ocr-comparison.md](01-ocr-comparison.md) mục 2.1 vẫn nguyên hiệu
lực: cặp *"+5,1 / +4,6 điểm"* của bài v6 tính trên **baseline của chính nó**
(v5_server 78,1% / 81,6%), không phải baseline trong tài liệu PaddleX (86,38% /
83,8%). Ghép hai nguồn sẽ **đảo chiều kết luận**. Trích thì phải trích kèm
baseline gốc.
