# Nhãn chuỗi biển số — ĐỌC TRƯỚC KHI DÙNG

| Tệp | Dòng | Dùng để làm gì |
|---|---:|---|
| `plate_text_labels_vn.csv` | 2.801 | ✅ **Chỉ biển hợp lệ định dạng VN** — dùng cho đánh giá (A4–A6) và huấn luyện OCR |
| `plate_text_labels_foreign.csv` | 1.218 | ⛔ Biển **nước ngoài / không hợp lệ** (Croatia `ZG…`, Ấn Độ `KA…`, ảnh bảng chữ cái mẫu). **Tuyệt đối không đưa vào huấn luyện OCR biển VN** |
| `plate_text_labels.csv` | 4.019 | Tệp gộp gốc, giữ để truy vết. Cột `is_valid_format` là bộ lọc |
| `plate_labels.csv` | 2.801 | Nhãn gán tay/tái tạo dùng cho benchmark |

**Vì sao phải tách:** nguồn `roboflow_ocr_plate` là bộ dữ liệu **quốc tế** — 30,3% nội dung
không phải biển số Việt Nam. Bộ lọc định dạng đã kiểm chứng loại sạch (0 mã tỉnh ngoài 81 mã VN,
0 chuỗi lọt), nhưng tách tệp tường minh để không ai vô tình nạp cả 4.019 dòng vào huấn luyện.
