# Hướng dẫn cài đặt

> **Tài liệu này dành cho ai?** Người muốn **cài và chạy** hệ thống trên một máy — máy chấm đồ án, máy hội
> đồng, hay máy cá nhân. Chỉ cần làm theo từ trên xuống, không cần đọc tài liệu nào khác trước.
>
> **Khác gì với Deployment Guide?** Tài liệu này trả lời *"làm sao cài được"*;
> [08-deployment-guide.md](../reports/08-deployment-guide.md) và [deployment/README.md](../../deployment/README.md)
> trả lời *"vận hành thế nào"* (biến môi trường, sao lưu, giới hạn tài nguyên, xử lý sự cố sâu). Người chỉ muốn
> mở hệ thống lên xem thì đọc đúng tài liệu này là đủ.

---

## 1. Yêu cầu hệ thống

| Thành phần | Yêu cầu tối thiểu | Ghi chú |
|---|---|---|
| Hệ điều hành | Windows 10/11, macOS, hoặc Linux | Đã kiểm chứng thực tế trên Windows 11 |
| RAM | 8 GB | Suy luận nạp cả YOLO11n và PP-OCRv5 vào bộ nhớ |
| Ổ đĩa trống | ~6 GB cho cách A (Docker) · ~4 GB cho cách B | Ảnh Docker backend chiếm 4,12 GB |
| GPU | **Không cần** | Toàn bộ suy luận chạy CPU (quyết định AD-06) |
| Mạng | Cần cho lần cài đầu tiên | Tải thư viện và bộ trọng số OCR |

**Chọn một trong hai cách cài.** Cách A ít bước hơn và không đụng tới Python/Node trên máy — nên dùng cho máy
chấm và máy demo. Cách B dành cho người cần sửa mã nguồn.

---

## 2. Cách A — Cài bằng Docker (khuyến nghị)

### Bước A1. Cài Docker Desktop

Tải tại [docker.com](https://www.docker.com/products/docker-desktop/), cài rồi **mở Docker Desktop lên** và
chờ tới khi biểu tượng cá voi báo *Running*. Kiểm tra:

```bash
docker --version
```

### Bước A2. Lấy mã nguồn và vào thư mục dự án

```bash
git clone <đường-dẫn-repo> DATN
cd DATN
```

*(Nếu nhận bản nén thì giải nén rồi `cd` vào thư mục đó.)*

### Bước A3. Kiểm tra mô hình đã có

Tệp **`models/best.pt`** (khoảng 5,4 MB) phải tồn tại — đây là bộ trọng số phát hiện biển số đã huấn luyện.
Không có tệp này thì hệ thống khởi động được nhưng `/health` sẽ báo `model_loaded: false` và mọi yêu cầu nhận
dạng đều bị từ chối.

```bash
ls models/best.pt
```

### Bước A4. Chạy hệ thống

```bash
docker compose up -d --build
```

Lần đầu mất **10–20 phút** (build ảnh, tải thư viện). Những lần sau chỉ vài giây.

### Bước A5. Kiểm tra đã chạy

Mở trình duyệt:

- Giao diện: **http://localhost:5173**
- Tài liệu API (Swagger): **http://localhost:5173/docs**

Hoặc kiểm tra bằng dòng lệnh — kết quả phải có `"status":"ok"` và `"model_loaded":true`:

```bash
curl http://localhost:8000/health
```

> **Backend cần khoảng 8 giây để nạp mô hình** sau khi container khởi động (đo thực tế: 8,36 giây trên Intel
> i5-14600K). Trong mấy giây đó giao diện có thể báo chưa sẵn sàng — chờ rồi tải lại trang.

### Dừng hệ thống

```bash
docker compose down          # dừng, GIỮ lại dữ liệu
docker compose down -v       # dừng và XOÁ cả cơ sở dữ liệu — cân nhắc kỹ
```

---

## 3. Cách B — Chạy trực tiếp (dành cho người phát triển)

### Bước B1. Cài Python 3.13 (hoặc 3.12) và Node.js ≥ 18

```bash
python --version    # cần 3.12 trở lên
node --version      # cần v18 trở lên; dự án dùng v20.19.6
```

> Node **v14 không chạy được** với Vite 5 — đây là lỗi đã gặp thật. Nếu máy có nhiều bản Node, dùng `nvm` để
> chuyển sang v20 trước khi làm tiếp.

### Bước B2. Tạo môi trường Python và cài thư viện

```bash
python -m venv backend/.venv
backend/.venv/Scripts/pip install -r backend/requirements.txt            # Windows
backend/.venv/Scripts/pip install -r backend/requirements-inference.txt
```

*(macOS/Linux thay `Scripts` bằng `bin`.)*

### Bước B3. Chạy backend

```bash
backend/.venv/Scripts/python.exe -m uvicorn backend.main:app --port 8000
```

Để nguyên cửa sổ này — đóng là hệ thống tắt. Swagger: http://localhost:8000/docs

### Bước B4. Chạy giao diện (cửa sổ dòng lệnh thứ hai)

```bash
cd frontend
npm install      # chỉ lần đầu, vài phút
npm run dev
```

Giao diện: http://localhost:5173

---

## 4. Kiểm tra sau khi cài — 60 giây

1. Mở http://localhost:5173 — vào thẳng trang **Nhận dạng ảnh**.
2. Kéo thả một ảnh trong `demo/images/` (ví dụ `1dong-1.png`) vào khung tải lên.
   **Nhận dạng chạy ngay khi ảnh được chọn**, không cần bấm nút nào.
3. Kết quả mong đợi với `1dong-1.png`: biển **51G-316.91**, nhãn *Ô tô*, nền trắng, *Đúng định dạng biển số*.
4. Mở trang **Lịch sử** — bản ghi vừa tạo phải xuất hiện ở đầu danh sách.

Làm được cả 4 bước nghĩa là cài đặt thành công.

---

## 5. Sự cố thường gặp khi cài

| Hiện tượng | Nguyên nhân thường gặp | Cách xử lý |
|---|---|---|
| `docker compose` báo cổng 5173 hoặc 8000 đã bị chiếm | Một tiến trình khác đang dùng cổng | Đóng tiến trình đó, hoặc đổi cổng: `ALPR_FRONTEND_PORT=5174 docker compose up -d` |
| `/health` trả `model_loaded: false` | Thiếu `models/best.pt` | Xem bước A3; kiểm tra tệp có nằm đúng thư mục `models/` không |
| Giao diện mở được nhưng nhận dạng luôn báo lỗi | Backend chưa nạp xong mô hình, hoặc container backend chết | `docker compose logs backend --tail 50` để xem lý do thật |
| `npm run dev` báo lỗi cú pháp lạ (cách B) | Node quá cũ (v14) | Chuyển sang Node ≥ 18 |
| Lần đầu chạy rất chậm | Đang tải bộ trọng số OCR (một lần duy nhất) | Chờ; các lần sau dùng bản đã lưu trong cache |

Sự cố sâu hơn (giới hạn bộ nhớ, xung đột thư viện `cv2`, sao lưu và khôi phục dữ liệu) nằm ở
[deployment/README.md](../../deployment/README.md) mục 10.

---

## 6. Gỡ cài đặt

```bash
docker compose down -v                 # xoá container và cả dữ liệu
docker rmi alpr-backend alpr-frontend  # xoá ảnh Docker
```

Cách B: chỉ cần xoá thư mục dự án và thư mục `backend/.venv`.

---

## 7. Tài liệu liên quan

| Cần gì | Đọc |
|---|---|
| Cách sử dụng từng chức năng | [user-manual.md](user-manual.md) |
| Vận hành, biến môi trường, sao lưu | [deployment/README.md](../../deployment/README.md) · [08-deployment-guide.md](../reports/08-deployment-guide.md) |
| Kiến trúc và chi tiết kỹ thuật | [technical-manual.md](technical-manual.md) |
| Danh sách API | [api-documentation.md](api-documentation.md) |
