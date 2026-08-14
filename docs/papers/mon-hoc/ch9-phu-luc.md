# PHỤ LỤC

## Phụ lục A. Cấu hình và siêu tham số

### A.1. Môi trường thực thi

Chỉ cần khi muốn tái lập **số đo hiệu năng**; số đo độ chính xác không phụ thuộc những giá trị này.

| Hạng mục | Giá trị |
|---|---|
| Hệ điều hành | Windows 11 Pro 10.0.26200 |
| CPU · RAM | Intel Core i5-14600K, 14 nhân / 20 luồng · 31,77 GiB |
| GPU | **Không có GPU CUDA** |
| Python | 3.13.12 |
| Thư viện chính | `ultralytics` 8.4.101 · `torch` 2.13.0+cpu · `paddleocr` 3.7.0 · `paddlepaddle` 3.3.1 · `opencv-python` 4.10.0.84 · `numpy` 2.4.5 |

Phiên bản thư viện trích từ **môi trường đang chạy tại thời điểm đo**, không lấy từ tệp khai báo phụ thuộc — tệp khai báo ghi *ràng buộc phiên bản*, không ghi *phiên bản đã cài*. Riêng phiên bản OpenCV đáng ghi vì quy ước góc của `minAreaRect` từng đổi giữa các phiên bản lớn, và bước nắn hình ở mục 3.4.6 phải xử lý riêng chuyện đó.

### A.2. Siêu tham số huấn luyện bộ phát hiện

Bảng dưới trích từ tệp tham số do thư viện Ultralytics tự sinh sau lượt huấn luyện chính thức — bản ghi **đã thực thi**, không phải cấu hình dự định.

| Tham số | Giá trị |
|---|---|
| `model` | `yolo11n.pt` (tiền huấn luyện COCO, 2.590.035 tham số) |
| `imgsz` | 640 |
| `epochs` · `batch` | 20 · 8 |
| `optimizer` | AdamW |
| `lr0` · `lrf` · `cos_lr` | 0,001 · 0,01 · bật |
| `momentum` · `weight_decay` | 0,937 · 0,0005 |
| `device` | `cpu` |
| `seed` · `deterministic` | 42 · bật |
| `fliplr` | **0,0** — tắt hoàn toàn (xem mục 3.3) |
| `flipud` | 0,0 |
| `hsv_h` · `hsv_s` · `hsv_v` | 0,015 · 0,7 · 0,4 |
| `translate` · `scale` | 0,1 · 0,5 |
| `mosaic` | 1,0 |
| **Thời gian huấn luyện** | **30,2 phút/epoch · tổng 36.181 s ≈ 10,05 giờ** |

### A.3. Tham số của khối xử lý ảnh

| Tham số | Giá trị | Mục |
|---|---|:--:|
| Chiều cao phóng đại vùng biển | 64 điểm ảnh | 3.4.2 |
| CLAHE — hệ số giới hạn · lưới ô | 2,0 · 8 × 8 | 3.4.2 |
| Ngưỡng tỉ lệ khung hình phân loại số dòng | 2,5 | 3.4.3 |
| Điểm kết thúc nửa trên · bắt đầu nửa dưới | 5/12 · 1/3 chiều cao | 3.4.4 |
| Chiều cao tối thiểu sau ghép ngang | 48 điểm ảnh | 3.4.5 |
| Bộ phân loại màu — thu biên · ngưỡng chiếm ưu thế | 18% mỗi phía · 30% | 3.5 |
| Ngưỡng Hamming khử trùng lặp | 10 | 3.2.2 |

## Phụ lục B. Hướng dẫn cài đặt và chạy

### B.1. Chạy bằng Docker (khuyến nghị)

Yêu cầu duy nhất là Docker Desktop. Từ thư mục gốc dự án:

```
cp deployment/.env.example .env
docker compose up -d --build
```

Sau khi hai container báo trạng thái khoẻ mạnh:

- Giao diện web: <http://localhost:5173>
- Tài liệu API tự sinh: <http://localhost:5173/docs>

Dừng hệ thống bằng `docker compose down`. **Không thêm cờ `-v`** trừ khi thực sự muốn xoá dữ liệu, vì cờ đó xoá luôn volume chứa cơ sở dữ liệu lịch sử.

Trọng số mô hình **không nằm trong ảnh Docker** mà được gắn từ ngoài dưới dạng chỉ đọc, nên tệp `models/best.pt` phải có mặt trước khi khởi động.

### B.2. Chạy trực tiếp trên máy, không dùng Docker

Cần Python 3.12 trở lên và Node.js 18 trở lên. Đồ án dùng **một môi trường ảo duy nhất**; bản đầu từng tách làm ba vì: bộ phụ thuộc của thư viện nhận dạng ký tự hạ cấp NumPy và thay thư viện thị giác máy tính bằng một biến thể lùi một phiên bản lớn so với nhánh huấn luyện. Cài chung thì mỗi lần cài lại một nhánh sẽ âm thầm đổi phiên bản nhánh kia — lỗi không làm sập chương trình mà làm **kết quả đo không tái lập được**.

```
python -m venv backend/.venv
backend/.venv/Scripts/pip install -r backend/requirements.txt
backend/.venv/Scripts/pip install -r backend/requirements-inference.txt
backend/.venv/Scripts/python -m uvicorn backend.main:app --port 8000
```

Giao diện chạy riêng:

```
cd frontend
npm install
npm run dev
```

### B.3. Chạy lại các phép đo của Chương 4

```
backend/.venv/Scripts/python ai/evaluation/ocr_accuracy.py
backend/.venv/Scripts/python ai/evaluation/benchmark_system.py
backend/.venv/Scripts/python ai/evaluation/benchmark_engines.py
```

Ba công cụ này đọc cấu hình từ biến môi trường thay vì tự dựng cấu hình riêng, nên các công tắc bật tắt từng bước xử lý ảnh ở mục 3.4.1 có hiệu lực với chúng. Đây là điều kiện để **bóc tách đóng góp của từng bước** ở mục 4.4; một công cụ đo tự dựng cấu hình riêng sẽ đo một hệ thống khác với hệ thống được bàn giao.

### B.4. Dựng lại quyển báo cáo

```
backend/.venv/Scripts/python scripts/build_thesis.py --src docs/papers/mon-hoc
powershell -File scripts/export_thesis_pdf.ps1 -Nguon docs/papers/mon-hoc/thesis-full.docx -Dich docs/papers/mon-hoc/thesis-full.pdf
```

Lệnh đầu ghép năm chương thành một tệp Markdown rồi kết xuất `.docx`; thứ tự ghép khai báo ở `ORDER.txt` trong chính thư mục đó. Lệnh hai dùng Word để kết xuất PDF và điền số trang cho mục lục.
