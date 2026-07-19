# Môi trường phát triển (Development Environment)

**Thuộc:** [SRS.md](SRS.md) — Phase 0
**Phiên bản:** 1.0 · **Ngày khảo sát:** 2026-07-19

---

## 1. Vì sao có tài liệu này

`CLAUDE.md` mô tả môi trường phát triển là **macOS Apple Silicon (M3 Pro)** với **Python 3.12**. Khảo sát thực tế cho thấy **cả hai đều không đúng** với máy đang dùng. Sai lệch này ảnh hưởng trực tiếp đến việc chọn thiết bị huấn luyện, chỉ tiêu hiệu năng và cách viết đường dẫn tệp, nên được ghi nhận chính thức tại đây.

---

## 2. Kết quả khảo sát thực tế

| Hạng mục | `CLAUDE.md` mô tả | Thực tế đo được | Đánh giá |
|---|---|---|---|
| Hệ điều hành | macOS Apple Silicon M3 Pro | **Windows 11 Pro 10.0.26200** | ❌ Khác hoàn toàn |
| Python | 3.12 | **3.13.12** (có sẵn cả 3.11) | ⚠️ Khác, nhưng chấp nhận được |
| GPU | Apple Silicon (hỗ trợ MPS) | **Intel UHD Graphics 770** + Parsec Virtual Display | ❌ **Không có GPU CUDA** |
| Node.js | (không nêu) | **v14.21.3** đang kích hoạt (nvm-windows) | ❌ Quá cũ cho Vite |
| Git | 2.x | 2.52.0.windows.1 | ✅ Đạt |
| Docker | Có | 29.4.3 | ✅ Đạt |
| Dung lượng trống ổ D: | (không nêu) | 96 GB | ✅ Đủ |

---

## 3. Phân tích tác động

### 3.1. Không có GPU CUDA — tác động lớn nhất

**Hệ quả:** không thể huấn luyện YOLO11 tại chỗ trong thời gian chấp nhận được. Ước tính CPU-only cần **1–3 ngày cho một lần huấn luyện**, khiến việc thử nghiệm siêu tham số trở nên bất khả thi.

**Phương án đã chọn:** huấn luyện trên **GPU miễn phí của Google Colab / Kaggle** (T4 hoặc P100), xuất `best.pt` về repo, chạy suy luận local bằng CPU.

**Nguyên tắc bắt buộc kèm theo:**

- Script huấn luyện đặt tại `ai/training/`, phải chạy được **cả local lẫn trên notebook**.
- Notebook chỉ đóng vai trò **trình thực thi**, tuyệt đối không phải nơi chứa logic gốc.
- Siêu tham số nằm trong tệp cấu hình, **không nằm trong ô lệnh của notebook** — để đảm bảo tái lập được và trích dẫn được trong quyển đồ án.
- Lưu checkpoint định kỳ ra Google Drive để phòng Colab ngắt phiên (rủi ro R-05).

### 3.2. Node.js v14 quá cũ

Vite 5+ yêu cầu Node ≥ 18. Máy đã cài sẵn nvm-windows với các phiên bản: `v10.24.1`, `v14.21.3`, `v16.20.2`, **`v18.20.8`**.

**Khắc phục** (thực hiện trước khi bắt đầu Phase 6):

```powershell
nvm use 18.20.8
node --version   # kỳ vọng: v18.20.8
```

> ⚠️ Lệnh này **thay đổi phiên bản Node mặc định toàn hệ thống**, có thể ảnh hưởng đến các dự án khác trên máy. Cần xác nhận trước khi chạy. Nếu muốn phiên bản mới hơn: `nvm install 22 && nvm use 22`.

### 3.3. Python 3.13 thay vì 3.12

Đã kiểm chứng thực tế: `paddlepaddle 3.3.1` **có** wheel `cp313-win_amd64`, nên PaddleOCR chạy được trên Python 3.13.

```
paddlepaddle-3.3.1-cp313-cp313-win_amd64.whl   ✅ khả dụng
```

**Kết luận:** giữ Python 3.13. Nếu về sau phát sinh xung đột phụ thuộc, đã có sẵn Python 3.11 làm phương án lùi.

### 3.4. Windows thay vì macOS

| Vấn đề | Cách xử lý |
|---|---|
| Dấu phân tách đường dẫn (`\` vs `/`) | Bắt buộc dùng `pathlib.Path`, cấm nối chuỗi đường dẫn thủ công |
| Ký tự xuống dòng (CRLF vs LF) | Đã đặt `core.autocrlf=false`, dùng `.gitattributes` |
| Không có MPS | Chọn thiết bị theo cấu hình, mặc định `cpu` |
| Khác biệt môi trường khi triển khai | Docker là tầng chuẩn hoá — đây chính là lý do NFR-C1 tồn tại |

---

## 4. Cấu hình môi trường mục tiêu

### 4.1. Môi trường phát triển local (máy hiện tại)

| Thành phần | Phiên bản | Mục đích |
|---|---|---|
| Windows 11 Pro | 10.0.26200 | Hệ điều hành |
| Python | 3.13.12 | Backend + suy luận AI |
| Node.js | 18.20.8 *(cần kích hoạt)* | Frontend |
| Git | 2.52.0 | Quản lý phiên bản |
| Docker | 29.4.3 | Đóng gói triển khai |
| Thiết bị suy luận | **CPU** | Cưỡng bức bởi phần cứng |

### 4.2. Môi trường huấn luyện (từ xa)

| Thành phần | Cấu hình |
|---|---|
| Nền tảng | Google Colab (ưu tiên) / Kaggle (dự phòng) |
| GPU | NVIDIA T4 16 GB hoặc P100 16 GB |
| Hạn mức | Colab: thay đổi theo thời điểm · Kaggle: 30 giờ GPU/tuần |
| Đầu ra | `best.pt`, `results.csv`, biểu đồ huấn luyện |

### 4.3. Môi trường triển khai (Docker)

| Container | Ảnh nền | Vai trò |
|---|---|---|
| `backend` | `python:3.12-slim` | FastAPI + pipeline AI |
| `frontend` | `node:20-alpine` → `nginx:alpine` | Build rồi phục vụ tĩnh |

> **Lưu ý chủ ý:** container dùng Python **3.12** dù local là 3.13. Docker chính là nơi ta lấy lại đúng phiên bản mà `CLAUDE.md` yêu cầu, đồng thời tách môi trường chạy khỏi máy phát triển. Đây là điểm đáng nêu khi bảo vệ: *môi trường triển khai được kiểm soát, không phụ thuộc máy cá nhân*.

---

## 5. Danh sách kiểm tra trước khi bắt đầu Phase 1

- [ ] Xác nhận việc chuyển Node sang v18.20.8 (ảnh hưởng toàn hệ thống)
- [ ] Tạo môi trường ảo Python (`.venv`)
- [ ] Xác nhận có tài khoản Google/Kaggle để huấn luyện
- [ ] Kiểm tra Docker Desktop khởi động được
- [ ] Tạo `.gitattributes` để cố định quy tắc xuống dòng

---

## 6. Lệnh kiểm chứng môi trường

Chạy các lệnh sau để tự xác minh lại các số liệu trong tài liệu này:

```powershell
python --version
node --version
git --version
docker --version
nvm list
Get-CimInstance Win32_VideoController | Select-Object Name
python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
```

Kỳ vọng: `torch.cuda.is_available()` trả về **`False`** — đúng như phân tích ở mục 3.1.
