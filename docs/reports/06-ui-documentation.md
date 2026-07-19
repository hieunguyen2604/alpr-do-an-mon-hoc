# Tài liệu giao diện người dùng

**Hệ thống nhận dạng biển số xe Việt Nam (ALPR)**
Phần giao diện web — React 18 + Vite 5 + TypeScript 5 (strict) + TailwindCSS 3

---

## 1. Mục tiêu và nguyên tắc thiết kế

### 1.1. Mục tiêu

Giao diện là **cửa duy nhất** người dùng cuối tiếp cận hệ thống. Mọi năng lực của pipeline
AI — phát hiện bằng YOLO11, đọc ký tự bằng PaddleOCR, hậu xử lý theo chuẩn biển số Việt Nam,
gộp trùng, lưu trữ — chỉ có giá trị nếu người dùng **thấy được** và **tin được**.

Ba mục tiêu cụ thể:

1. **Trình diễn được toàn bộ luồng nghiệp vụ** — ba nguồn đầu vào (ảnh, video, webcam),
   tra cứu lịch sử và thống kê tổng hợp, trên một ứng dụng duy nhất.
2. **Trung thực về số liệu** — con số hiển thị phải nói đúng điều nó đo. Đây là yêu cầu
   nghiêm ngặt hơn thường lệ vì các số này đi thẳng vào chương Đánh giá của quyển đồ án.
3. **Không giấu sự thật kỹ thuật** — hệ thống chạy suy luận trên CPU, chậm hơn GPU nhiều lần.
   Giao diện nói rõ điều đó thay vì để người dùng đoán tại sao phải chờ.

### 1.2. Nguyên tắc thiết kế

| Nguyên tắc | Cách hiện thực |
|---|---|
| **Bốn trạng thái, không thiếu trạng thái nào** | Mỗi vùng dữ liệu đều xử lý đủ *loading / empty / error / success*. Riêng "empty" còn được tách nhỏ theo nguyên nhân (chưa gửi gì / đã xử lý nhưng không thấy biển số / không khớp bộ lọc) vì cách thoát khỏi mỗi trạng thái là khác nhau |
| **Kết quả rỗng không phải lỗi** | Ảnh xử lý xong mà không có biển số ⇒ HTTP 200 ⇒ hiện *trạng thái rỗng*, không hiện lỗi đỏ. Báo lỗi ở đây sẽ đẩy người dùng đi sửa một hệ thống đang chạy đúng |
| **Lỗi nói tiếng người** | Toàn bộ lỗi đi qua một bộ chuẩn hoá trong `services/api.ts`, ra thành `ApiError` với `message` tiếng Việt sẵn sàng hiển thị. Stack trace, traceback, mã lỗi kỹ thuật **không bao giờ** lên màn hình (NFR-U3, FR-6.3) |
| **Thao tác chậm phải có phản hồi** | Upload có thanh tiến độ thật (theo byte), suy luận có spinner + câu giải thích, tác vụ video có phần trăm, làm mới có trạng thái quay (NFR-U2) |
| **Trạng thái quan trọng nằm trên URL** | Bộ lọc, sắp xếp và số trang của Lịch sử được đồng bộ vào query string. Tải lại trang không mất bộ lọc; một kết quả tra cứu có thể gửi cho người khác bằng đường link |
| **Một quy ước đặt tên duy nhất** | Kiểu dữ liệu ở frontend dùng `snake_case` **y hệt JSON của API**. Không có lớp chuyển đổi. Backend đổi schema ⇒ TypeScript báo lỗi lúc biên dịch, thay vì trường lặng lẽ thành `undefined` lúc chạy |
| **Không hard-code hostname** | Origin backend đọc từ `VITE_API_URL`; mặc định rỗng ⇒ đi qua proxy same-origin. Triển khai là việc cấu hình, không phải build lại |

### 1.3. Ngôn ngữ

* **Văn bản người dùng nhìn thấy**: tiếng Việt, kể cả thông báo lỗi và nhãn cột.
* **Mã nguồn** (tên biến, tên hàm, comment, docstring): tiếng Anh.

Tách bạch như vậy để người đọc mã và người dùng sản phẩm không phải chia sẻ chung một vốn từ.

---

## 2. Sơ đồ điều hướng

Ứng dụng gồm **5 trang** nằm trong một khung chung (`Layout`) có sidebar cố định.
Mọi đường dẫn không khớp đều chuyển hướng về Tổng quan, không để người dùng rơi vào ngõ cụt.

```mermaid
graph TD
    Layout["Khung ứng dụng (Layout)<br/>Sidebar 5 mục + header"]

    Layout --> D["/ — Tổng quan<br/>(Dashboard)"]
    Layout --> I["/image — Nhận dạng ảnh"]
    Layout --> V["/video — Nhận dạng video"]
    Layout --> W["/webcam — Webcam"]
    Layout --> H["/history — Lịch sử"]

    NF["Mọi đường dẫn khác"] -.->|"chuyển hướng"| D

    D -->|"Nhận dạng ảnh đầu tiên<br/>(trạng thái rỗng)"| I
    D -->|"Xem tất cả<br/>(danh sách gần đây)"| H

    I -->|"kết quả được lưu"| H
    V -->|"kết quả được lưu"| H
    W -->|"kết quả được lưu"| H

    H -->|"trạng thái rỗng"| I

    classDef page fill:#eff6ff,stroke:#2563eb,color:#1e3a5f
    classDef shell fill:#f1f5f9,stroke:#64748b,color:#1e293b
    classDef ghost fill:#fff,stroke:#cbd5e1,color:#64748b,stroke-dasharray: 4 3
    class D,I,V,W,H page
    class Layout shell
    class NF ghost
```

**Quan hệ giữa các trang:**

* Ba trang nhận dạng (ảnh / video / webcam) là **nguồn sinh dữ liệu**. Kết quả của cả ba
  đều chảy về cùng một bảng `detection_history`, nên trang Lịch sử là **đích chung**.
* Tổng quan là **cửa sổ đọc**: không tạo dữ liệu, chỉ tổng hợp. Vì vậy trạng thái rỗng
  của nó dẫn thẳng sang trang Nhận dạng ảnh — đường ngắn nhất để có dữ liệu đầu tiên.
* Lịch sử và Tổng quan **không phụ thuộc lẫn nhau**: mỗi trang tự gọi API của mình,
  hỏng một trang không kéo đổ trang kia.

---

## 3. Mô tả từng màn hình

### 3.1. Tổng quan (`/`)

![Màn hình Tổng quan](../screenshots/dashboard.png)

**Chức năng:** trả lời trong một màn hình ba câu hỏi — hệ thống đã xử lý bao nhiêu,
chất lượng ra sao, và hiện có đang khoẻ không (FR-4.1, FR-4.2, FR-6.1).

**Thành phần:**

| Vùng | Nội dung | Nguồn dữ liệu |
|---|---|---|
| Bốn thẻ chỉ số | Lượt nhận dạng · Biển số phát hiện · Độ tin cậy trung bình · Thời gian xử lý trung bình | `GET /api/statistics` |
| Trạng thái hệ thống | Kết nối CSDL, tình trạng nạp mô hình AI, kèm cảnh báo khi đang chạy chế độ mô phỏng | `GET /health` |
| Hoạt động theo ngày | Biểu đồ đường 7 ngày, **hai chuỗi**: lượt nhận dạng (xanh dương) và biển số phát hiện (xanh lá). Có nút chuyển Biểu đồ ⇄ Bảng | `statistics.daily_counts` |
| Phân bố theo nguồn | Biểu đồ cột nhóm theo Ảnh / Video / Webcam, cũng hai chuỗi `job_count` và `detection_count` | `statistics.by_input_type` |
| Nhận dạng gần đây | 5 bản ghi mới nhất theo `detected_time` | `GET /api/history?page_size=5` |

**Luồng thao tác:** trang tự nạp khi mở. Nút **Làm mới** gọi lại cả ba request cùng lúc.

**Bốn trạng thái:**

* *Loading* — khung xương (skeleton) dựng **đúng bố cục thật**, nên khi dữ liệu về không có
  phần tử nào nhảy chỗ. Chỉ lần nạp đầu tiên hiện skeleton; lần làm mới giữ nguyên số cũ
  trên màn hình để trang không nhấp nháy.
* *Empty* — chỉ khi `total_jobs == 0` **và** `total_detections == 0`. Kiểm tra cả hai là có chủ ý:
  người đã tải lên vài ảnh không có biển số nào vẫn *đã dùng* hệ thống, nói với họ rằng
  "chưa có dữ liệu" là sai.
* *Error* — ba request **không** gộp thành một khối tất-cả-hoặc-không. `/health` hỏng
  không được xoá trắng số thống kê đã về đủ. Chỉ khi request thống kê — chủ đề của trang — hỏng
  thì mới hiện lỗi toàn trang.
* *Success* — như ảnh chụp.

### 3.2. Nhận dạng ảnh (`/image`)

![Màn hình Nhận dạng ảnh](../screenshots/image-detection.png)

**Chức năng:** tải lên một ảnh, xem vị trí và nội dung mọi biển số trong đó
(FR-1.1, FR-1.2, FR-1.7, FR-4.7).

**Bố cục hai cột:** cột trái là tải lên và ảnh đã đánh dấu, cột phải là danh sách kết quả.

**Thành phần:**

* **Khung kéo–thả** — chấp nhận JPG, PNG, WebP, BMP, tối đa 10 MB. Kiểm tra ở trình duyệt
  chỉ để **tiết kiệm cho người dùng một lần upload vô ích**; backend vẫn kiểm tra magic bytes
  và từ chối bằng 415 nếu tệp giả đuôi (FR-1.2, NFR-S1).
* **Ảnh đã đánh dấu** — bounding box vẽ chồng lên ảnh, toạ độ quy đổi theo tỉ lệ nên
  đúng ở mọi kích thước hiển thị. Rê chuột lên một khung sẽ làm nổi bật thẻ kết quả tương ứng
  và ngược lại — liên kết hai chiều giữa hình và danh sách.
* **Thẻ kết quả** cho từng biển số: ảnh biển số đã cắt, biển số sau chuẩn hoá, **chuỗi OCR thô**
  (khi khác kết quả cuối), độ tin cậy phát hiện và độ tin cậy OCR **tách riêng**, số dòng của biển,
  cờ hợp lệ theo định dạng Việt Nam.
* **Tải về** — nút xuất ảnh có vẽ sẵn bounding box (vẽ bằng canvas ở phía trình duyệt),
  và nút tải riêng từng ảnh biển số đã cắt (FR-4.7).

**Luồng thao tác (3 thao tác click, NFR-U1):** chọn ảnh → bấm **Nhận dạng** → xem kết quả.

**Bốn trạng thái:**

* *Loading* — thanh tiến độ upload **theo byte thật**, sau đó chuyển sang trạng thái chờ
  không xác định kèm câu "Mô hình chạy trên CPU nên bước này có thể mất vài giây".
  Nói trước để sự chậm trở thành thông tin, không thành nghi ngờ.
* *Empty (chưa gửi)* — "Chưa có kết quả", hướng dẫn thao tác tiếp theo.
* *Empty (đã xử lý, không có biển số)* — đây là **kết quả**, không phải lỗi. Hiện gợi ý cụ thể:
  chụp gần hơn, rõ nét hơn, biển ít bị che.
* *Error* — thông báo tiếng Việt + nút Thử lại + mã `request_id` để đối chiếu log máy chủ.
  Mã này thay cho việc phơi bày chi tiết nội bộ.
* *Success* — như mô tả trên.

Việc huỷ giữa chừng (chọn tệp khác, xoá form, rời trang) sẽ **abort** request đang bay và
**không** bị báo là lỗi — huỷ là ý người dùng.

### 3.3. Nhận dạng video (`/video`)

![Màn hình Nhận dạng video](../screenshots/video-detection.png)

**Chức năng:** tải video lên, xử lý ở chế độ nền, theo dõi tiến độ, xem kết quả đã gộp trùng
(FR-2.1, FR-2.6, FR-2.5).

**Thành phần:**

* **Khung kéo–thả video** — MP4, MOV, AVI, MKV, tối đa 200 MB. Ngay dưới khung có ghi chú
  ước lượng thời gian: *"video 60 giây có thể mất khoảng 3–4 phút"*.
* **Bảng tiến độ tác vụ** — trạng thái (Đang chờ / Đang xử lý / Hoàn thành / Thất bại / Đã huỷ),
  phần trăm, số khung đã xử lý trên tổng số khung, nút **Làm mới** để hỏi ngay một lần.
* **Bảng kết quả** — danh sách biển số của tác vụ, đọc từ `GET /api/history?job_id=…`
  chứ không từ đối tượng tác vụ (đối tượng này chỉ mang số đếm). Nhờ vậy trang video và trang
  Lịch sử **không thể mâu thuẫn** về những gì một tác vụ đã tạo ra.
* **Tải video kết quả** — khi `output_url` có giá trị (FR-2.5).
* **Ghi chú gộp trùng** — luôn hiển thị dưới danh sách, giải thích rằng một xe xuất hiện
  trong hàng chục khung chỉ tính **một** bản ghi. Thiếu ghi chú này, người dùng đọc con số
  thấp và tưởng hệ thống bỏ sót (FR-2.4).

**Luồng thao tác:** chọn video → **Bắt đầu xử lý** → API trả `202 { job_id }` → giao diện
hỏi `GET /api/jobs/{job_id}` định kỳ cho tới khi trạng thái kết thúc → tự nạp danh sách biển số.

Trang giữ **`job_id`** làm nguồn sự thật chứ không giữ đối tượng tác vụ, vì hook
`useJobPolling` đã sở hữu đối tượng đó; giữ hai bản sao sẽ khiến chúng lệch nhau giữa các lần hỏi.
Việc hỏi tiến độ **tự dừng** khi trạng thái đã kết thúc — không dừng thì một tác vụ đã xong
vẫn bị hỏi mãi chừng nào tab còn mở.

**Bốn trạng thái:** *loading* (thanh upload rồi thanh tiến độ tác vụ) · *empty* ("Chưa có tác vụ nào")
· *error* (tách riêng lỗi tải lên, lỗi hỏi tiến độ, lỗi nạp danh sách kết quả — ba nguyên nhân khác nhau
nên ba nút thử lại khác nhau) · *success*.

### 3.4. Webcam (`/webcam`)

![Màn hình Webcam](../screenshots/webcam.png)

**Chức năng:** nhận dạng thời gian thực từ camera của máy người dùng (FR-3.1 → FR-3.5).

**Bố cục hai cột:** trái là camera và số đo, phải là danh sách biển số của phiên.

**Thành phần:**

* **Điều khiển camera** — nút Bật/Tắt, chọn thiết bị (khi máy có nhiều camera),
  chọn chu kỳ gửi khung hình: 400 ms / 700 ms / 1 giây / 2 giây (FR-3.2).
* **Khung hình trực tiếp** — bounding box và nhãn biển số vẽ chồng lên hình đang phát (FR-3.4).
* **Bảng đo hiệu năng** — tốc độ thực tế (FPS đo trong 5 giây gần nhất), thời gian xử lý phía
  máy chủ, trọn vòng gửi–nhận, số khung đã gửi và **số khung bị bỏ qua**.
* **Bảng biển số trong phiên** — mỗi biển số **một dòng** kèm số lần xuất hiện. Biển phát hiện
  được nhưng OCR không đọc nổi được **đếm gộp**, không liệt kê từng dòng (FR-3.5).

**Luồng thao tác:** bấm **Bật camera** → trình duyệt hỏi quyền → hình hiện lên → vòng lặp
tự động chụp và gửi khung hình → kết quả cập nhật liên tục → bấm **Tắt** để giải phóng camera.

**Bốn trạng thái:** *loading* (spinner phủ lên khung trong lúc mở camera) · *empty*
("Camera đang tắt" / "Chưa nhận được biển số nào") · *error* (hai loại lỗi tách biệt, xem dưới)
· *success*.

**Hai loại lỗi được tách riêng có chủ ý:**

1. **Lỗi camera** — không cấp quyền, không có thiết bị, thiết bị bị chiếm. Hiện panel riêng
   gồm *chuyện gì đã xảy ra* **và** *cách khắc phục cụ thể cho đúng nguyên nhân đó*. Nói
   "không truy cập được camera" mà không nói phải cấp quyền, cắm thiết bị hay đóng Zoom
   là để người dùng tay không.
2. **Lỗi máy chủ** — camera vẫn tốt, chỉ là khung hình bị từ chối. Hình **vẫn giữ trên màn hình**,
   lỗi hiện dạng dải thông báo. Sau **5 lỗi liên tiếp**, vòng lặp **tự tạm dừng** và hiện một
   thông báo kèm nút *Tiếp tục* — thay vì đập vào backend đã chết mỗi 700 ms và nháy cùng
   một lỗi vô tận.

### 3.5. Lịch sử (`/history`)

![Màn hình Lịch sử](../screenshots/history.png)

**Chức năng:** tra cứu, lọc, sắp xếp, xem chi tiết, xoá và xuất dữ liệu đã lưu
(FR-4.3 → FR-4.8, FR-5.1, FR-5.2).

**Thành phần:**

* **Thanh bộ lọc** — tìm theo biển số (khớp một phần, tự tìm sau khi ngừng gõ), lọc theo
  loại đầu vào, khoảng thời gian (từ ngày / đến ngày), ngưỡng độ tin cậy tối thiểu (thanh trượt
  0–100%). Kèm nút **Xoá bộ lọc** và **Xuất CSV**.
* **Bảng kết quả** — ảnh biển số đã cắt, biển số (kèm **chuỗi OCR thô** ngay bên dưới khi khác),
  thanh độ tin cậy, loại đầu vào, thời điểm, thời gian xử lý, nút xoá. Tiêu đề cột
  **Độ tin cậy** và **Thời điểm** bấm được để đảo thứ tự (FR-4.8).
* **Phân trang** — chọn 10 / 20 / 50 / 100 dòng mỗi trang; 100 là trần backend chấp nhận.
* **Modal chi tiết** — ảnh gốc, ảnh biển số đã cắt, hai độ tin cậy tách riêng, biển số sau
  chuẩn hoá, chuỗi OCR thô, số dòng của biển, thời gian xử lý, thời điểm nhận dạng, thời điểm lưu,
  toạ độ vùng chứa biển (pixel), và mã lần tải lên `source_job_id` (FR-4.6).
* **Hộp thoại xác nhận xoá** — nêu rõ rằng ảnh liên quan trên máy chủ cũng bị xoá (FR-5.1).

**Luồng thao tác:** mọi thay đổi bộ lọc đều **ghi lên URL**, URL đổi thì danh sách tự nạp lại.
Nhờ đó tải lại trang không mất bộ lọc và có thể chia sẻ kết quả tra cứu bằng đường link.

**Bốn trạng thái:** *loading* (skeleton lần đầu; các lần sau giữ bảng cũ, chỉ làm mờ nhẹ)
· *empty* (**hai kiểu khác nhau** — "không khớp bộ lọc" kèm nút xoá bộ lọc, và "chưa có dữ liệu"
kèm lối đi sang trang nhận dạng ảnh) · *error* · *success*.

Hai chi tiết kỹ thuật ảnh hưởng trực tiếp tới thứ người dùng nhìn thấy:

* Request cũ bị **abort** khi có request mới, kèm một bộ đếm tăng dần đảm bảo **chỉ phản hồi
  mới nhất được ghi vào state**. Không có cơ chế này, gõ nhanh hai ký tự có thể khiến phản hồi
  đến muộn của bộ lọc cũ ghi đè lên kết quả đúng.
* Xoá dòng **cuối cùng** của một trang sẽ lùi về trang trước, thay vì nạp lại một trang không
  còn tồn tại và hiện bảng trống.

---

## 4. Sơ đồ tuần tự — luồng nhận dạng ảnh

Nhìn từ góc nhìn người dùng, từ lúc chọn tệp tới lúc thấy kết quả.

```mermaid
sequenceDiagram
    autonumber
    actor U as Người dùng
    participant UI as Giao diện<br/>trang Nhận dạng ảnh
    participant API as Client API<br/>services/api.ts
    participant BE as Backend FastAPI

    U->>UI: Kéo thả / chọn tệp ảnh
    UI->>UI: Kiểm tra định dạng và dung lượng ≤ 10 MB
    alt Tệp không hợp lệ
        UI-->>U: Thông báo tiếng Việt ngay tại khung kéo thả<br/>(không tốn một lần tải lên)
    else Tệp hợp lệ
        UI-->>U: Hiện ảnh xem trước + bật nút "Nhận dạng"
    end

    U->>UI: Bấm "Nhận dạng"
    UI->>UI: Xoá kết quả cũ, đặt trạng thái loading
    UI->>API: detectImage(file, onProgress, signal)
    API->>BE: POST /api/detect/image (multipart)<br/>header X-Request-ID

    loop Trong lúc tải lên
        BE-->>API: sự kiện tiến độ theo byte
        API-->>UI: onProgress(phần trăm)
        UI-->>U: Thanh tiến độ tải lên (NFR-U2)
    end

    Note over UI,U: Tải lên xong → chuyển sang trạng thái chờ không xác định<br/>kèm câu "Mô hình chạy trên CPU nên có thể mất vài giây"

    BE->>BE: YOLO11 phát hiện vùng biển số (FR-1.3)
    BE->>BE: Cắt vùng, PaddleOCR đọc ký tự (FR-1.4)
    BE->>BE: Hậu xử lý regex + kiểm tra định dạng VN (FR-1.5)
    BE->>BE: Lưu CSDL + ảnh gốc + ảnh biển đã cắt (FR-1.6)

    alt Thành công, có biển số
        BE-->>API: 200 { results[], image_url, plate_count, ... }
        API-->>UI: DetectionResponse
        UI-->>U: Ảnh có bounding box + thẻ kết quả từng biển số<br/>(biển chuẩn hoá, OCR thô, 2 độ tin cậy) — FR-1.7
    else Thành công, không có biển số nào
        BE-->>API: 200 { results: [], plate_count: 0 }
        API-->>UI: DetectionResponse rỗng
        UI-->>U: Trạng thái RỖNG kèm gợi ý chụp lại<br/>(không phải trạng thái lỗi)
    else Thất bại
        BE-->>API: 4xx / 5xx
        API->>API: Chuẩn hoá thành ApiError<br/>message tiếng Việt, giữ request_id
        API-->>UI: throw ApiError
        UI-->>U: Thông báo thân thiện + nút "Thử lại" + mã tra cứu<br/>(không lộ stack trace — NFR-U3, FR-6.3)
    end

    opt Người dùng muốn giữ kết quả
        U->>UI: "Tải ảnh kết quả" / "Tải ảnh biển số"
        UI-->>U: Tệp ảnh về máy (FR-4.7)
    end

    opt Người dùng huỷ giữa chừng
        U->>UI: Chọn tệp khác / xoá form / rời trang
        UI->>API: abort()
        Note over UI: Huỷ là ý người dùng ⇒ KHÔNG báo lỗi
    end
```

---

## 5. Bảng đối chiếu yêu cầu chức năng → màn hình

Danh sách yêu cầu lấy từ `docs/00-requirements/functional-requirements.md`.
Cột **Mức** giữ nguyên phân loại MoSCoW của tài liệu gốc (M = Must, S = Should, C = Could).

### FR-1 — Nhận dạng từ ảnh

| Mã | Yêu cầu (rút gọn) | Mức | Màn hình đáp ứng | Trạng thái |
|---|---|---|---|---|
| FR-1.1 | Tải lên ảnh JPG/JPEG/PNG/BMP | M | Nhận dạng ảnh — khung kéo–thả (thêm cả WebP) | ✅ |
| FR-1.2 | Kiểm tra định dạng, ≤ 10 MB, ảnh giải mã được | M | Nhận dạng ảnh — kiểm tra ở trình duyệt + hiển thị lỗi 415/413 từ backend | ✅ |
| FR-1.3 | Phát hiện **tất cả** vùng biển số | M | Nhận dạng ảnh — overlay bounding box, `plate_count` | ✅ (hiển thị) |
| FR-1.4 | Cắt vùng và nhận dạng ký tự | M | Nhận dạng ảnh — ảnh biển đã cắt + `ocr_confidence` trên mỗi thẻ | ✅ (hiển thị) |
| FR-1.5 | Hậu xử lý, lưu **cả** chuỗi thô và chuỗi đã sửa | M | Nhận dạng ảnh + Lịch sử — hiện song song `raw_ocr_text` và `plate_number` | ✅ |
| FR-1.6 | Lưu CSDL kèm ảnh gốc và ảnh cắt | M | Lịch sử — bản ghi và hai ảnh xem được trong modal chi tiết | ✅ (hiển thị) |
| FR-1.7 | Hiện ảnh có bounding box, biển số, độ tin cậy, thời gian xử lý, không tải lại trang | M | Nhận dạng ảnh — cột kết quả | ✅ |

### FR-2 — Nhận dạng từ video

| Mã | Yêu cầu (rút gọn) | Mức | Màn hình đáp ứng | Trạng thái |
|---|---|---|---|---|
| FR-2.1 | Tải lên MP4/AVI/MOV ≤ 200 MB, trả mã tác vụ | M | Nhận dạng video — khung kéo–thả (thêm cả MKV) | ✅ |
| FR-2.2 | Trích khung hình theo bước nhảy cấu hình được | M | — (thuần backend) | ➖ ngoài phạm vi giao diện |
| FR-2.3 | Phát hiện và nhận dạng trên khung đã trích | M | Nhận dạng video — bảng kết quả | ✅ (hiển thị) |
| FR-2.4 | Gộp trùng cùng một biển qua nhiều khung | M | Nhận dạng video — kết quả đã gộp + ghi chú giải thích cách đếm | ✅ (hiển thị + giải thích) |
| FR-2.5 | Xuất video kết quả có vẽ sẵn nhãn | M | Nhận dạng video — nút **Tải video kết quả** khi `output_url` có giá trị | ✅ |
| FR-2.6 | Hiện tiến độ % và **cho phép huỷ** tác vụ | S | Nhận dạng video — bảng tiến độ ✅; nút **Huỷ tác vụ** hiện diện nhưng **bị vô hiệu hoá** | ⚠️ một phần |

### FR-3 — Nhận dạng thời gian thực (Webcam)

| Mã | Yêu cầu (rút gọn) | Mức | Màn hình đáp ứng | Trạng thái |
|---|---|---|---|---|
| FR-3.1 | Xin quyền và hiển thị luồng webcam | M | Webcam — nút Bật camera, khung hình trực tiếp, panel lỗi có gợi ý khắc phục | ✅ |
| FR-3.2 | Gửi khung hình theo chu kỳ cấu hình được | M | Webcam — dropdown 400 ms / 700 ms / 1 s / 2 s | ✅ |
| FR-3.3 | Phát hiện và nhận dạng trên luồng trực tiếp | M | Webcam — `POST /api/detect/frame` | ✅ |
| FR-3.4 | Vẽ bounding box và nhãn chồng lên khung hình | M | Webcam — overlay trên khung camera | ✅ |
| FR-3.5 | Lưu lịch sử phiên webcam, có gộp trùng | M | Webcam — bảng biển số trong phiên (một dòng mỗi biển + số lần xuất hiện); dùng chung một `job_id` cho cả phiên | ✅ |

### FR-4 — Dashboard, lịch sử và tra cứu

| Mã | Yêu cầu (rút gọn) | Mức | Màn hình đáp ứng | Trạng thái |
|---|---|---|---|---|
| FR-4.1 | Chỉ số tổng hợp: tổng lượt, độ tin cậy TB, thời gian xử lý TB, phân bố theo nguồn | M | Tổng quan — 4 thẻ chỉ số + biểu đồ theo nguồn | ✅ |
| FR-4.2 | Biểu đồ số lượt theo thời gian | S | Tổng quan — biểu đồ 7 ngày, có chế độ bảng và trạng thái rỗng riêng | ✅ |
| FR-4.3 | Danh sách lịch sử có phân trang | M | Lịch sử — bảng + phân trang 10/20/50/100 | ✅ |
| FR-4.4 | Tìm theo biển số, khớp một phần | M | Lịch sử — ô tìm kiếm (debounce) | ✅ |
| FR-4.5 | Lọc theo loại đầu vào, khoảng thời gian, ngưỡng tin cậy | M | Lịch sử — thanh bộ lọc, kết hợp được nhiều điều kiện | ✅ |
| FR-4.6 | Xem chi tiết: ảnh gốc, ảnh cắt, toàn bộ metadata | M | Lịch sử — modal chi tiết | ✅ |
| FR-4.7 | Tải về ảnh kết quả hoặc ảnh biển số đã cắt | S | Nhận dạng ảnh — nút tải ảnh đã đánh dấu và tải từng ảnh biển | ✅ |
| FR-4.8 | Sắp xếp theo thời gian / độ tin cậy, tăng–giảm | C | Lịch sử — bấm tiêu đề cột; trạng thái sắp xếp lưu trên URL | ✅ |

### FR-5 — Quản lý dữ liệu

| Mã | Yêu cầu (rút gọn) | Mức | Màn hình đáp ứng | Trạng thái |
|---|---|---|---|---|
| FR-5.1 | Xoá một bản ghi kèm tệp ảnh liên quan | S | Lịch sử — nút xoá trên mỗi dòng + hộp thoại xác nhận nêu rõ ảnh cũng bị xoá | ✅ |
| FR-5.2 | Xuất lịch sử **có áp bộ lọc hiện hành** ra CSV | S | Lịch sử — nút **Xuất CSV**, mang đúng bộ lọc đang áp dụng | ✅ |
| FR-5.3 | Script dọn tệp mồ côi | C | — (script vận hành) | ➖ ngoài phạm vi giao diện |
| FR-5.4 | Xoá nhiều bản ghi theo lựa chọn | C | — | ❌ chưa làm |

### FR-6 — Hệ thống và vận hành (phần liên quan giao diện)

| Mã | Yêu cầu (rút gọn) | Mức | Màn hình đáp ứng | Trạng thái |
|---|---|---|---|---|
| FR-6.1 | Endpoint sức khoẻ báo trạng thái mô hình và CSDL | S | Tổng quan — thẻ **Trạng thái hệ thống** | ✅ (hiển thị) |
| FR-6.2 | Log có cấu trúc cho mọi lượt và mọi lỗi | S | Toàn bộ — mỗi request mang `X-Request-ID`, mã này được hiện lại khi có lỗi | ✅ (phần đóng góp của giao diện) |
| FR-6.3 | Lỗi thân thiện, **không** rò rỉ stack trace | M | Toàn bộ — bộ chuẩn hoá lỗi trong `services/api.ts` | ✅ |
| FR-6.4 | Cấu hình đọc từ biến môi trường, không hard-code | M | Toàn bộ — `VITE_API_URL`, `VITE_API_TIMEOUT_MS` | ✅ |

**Tổng kết:** trong 34 yêu cầu chức năng, **2 nằm ngoài phạm vi giao diện** (FR-2.2 trích khung hình,
FR-5.3 script dọn tệp mồ côi). Trong 32 yêu cầu còn lại: **30 đã đáp ứng đầy đủ**,
**1 đáp ứng một phần** (FR-2.6 — có tiến độ, thiếu chức năng huỷ), **1 chưa làm**
(FR-5.4 — xoá hàng loạt, mức Could).

Toàn bộ yêu cầu mức **M (Must)** liên quan giao diện đều đã đáp ứng đầy đủ.

---

## 6. Các quyết định thiết kế đáng chú ý

### 6.1. Hàng đợi một khe ở trang Webcam

**Quyết định:** vòng lặp gửi khung hình chỉ cho phép **đúng một request đang bay**.
Khi bộ đếm thời gian kích hoạt mà khe vẫn bận, khung hình đó bị **bỏ đi**, **không xếp hàng**.
Số khung bị bỏ được hiển thị công khai trên bảng đo, kèm giải thích ngay dưới đó.

**Lý do:** suy luận chạy trên **CPU**, mỗi khung mất khoảng 300–400 ms, tức chừng 5 FPS.
Giả sử dùng cách ngây thơ — bộ đếm 700 ms, mỗi lần kích hoạt thì gửi một khung và chờ:

* Chỉ cần **một** khung mất 900 ms là request thứ hai đã khởi động trước khi khung đầu trả về.
* Từ đó trở đi hàng đợi **chỉ dài thêm**, không bao giờ ngắn lại — vì tốc độ vào (1 khung/700 ms)
  lớn hơn tốc độ ra (1 khung/900 ms).
* Hệ quả: độ trễ **cộng dồn**, bounding box tụt lại xa dần so với hình đang phát, bộ nhớ trình duyệt
  phình lên vì hàng chục blob JPEG đang chờ, và tab **treo** dưới sức nặng các request tồn đọng.

Bỏ khung hình **không mất gì**: khung tiếp theo chỉ cách 700 ms và mang hình **mới hơn**.
Giữ một khung cũ trong hàng đợi để xử lý sau là giữ lại một tấm ảnh **đã lỗi thời**.

Hệ quả thiết kế đi kèm: các mức chu kỳ trong dropdown là **tần suất thử**, không phải thông lượng
đảm bảo. Chọn 400 ms trên máy cần 600 ms mỗi khung **không** cho 2,5 FPS — nó cho đúng tốc độ như cũ,
chỉ thêm nhiều khung bị bỏ. Điều này được ghi rõ trong tài liệu mã nguồn để người bảo trì sau không
"tối ưu" bằng cách hạ chu kỳ xuống.

**Cơ chế bảo vệ đi kèm:** sau 5 lỗi liên tiếp, vòng lặp tự tạm dừng. Không có nó, một backend đã chết
sẽ bị gọi mỗi 700 ms cho tới khi người dùng đóng tab, và cùng một thông báo lỗi nhấp nháy vô tận.

### 6.2. Phân biệt "lượt nhận dạng" và "biển số phát hiện"

**Quyết định:** dashboard hiển thị `total_jobs` và `total_detections` thành **hai thẻ riêng biệt,
đặt cạnh nhau**, mỗi thẻ có nhãn khác nhau, có dòng mô tả, và có tooltip giải thích kèm ví dụ.
Cả hai biểu đồ (theo ngày và theo nguồn) cũng vẽ **hai chuỗi** thay vì một, dùng **cùng một quy ước màu
trên mọi biểu đồ**: xanh dương luôn là lượt, xanh lá luôn là biển số.

| Chỉ số | Nhãn hiển thị | Đơn vị đếm |
|---|---|---|
| `total_jobs` | **Lượt nhận dạng** | Số **tệp / phiên** đã tải lên và xử lý |
| `total_detections` | **Biển số phát hiện** | Số **biển số** đọc được |

Một ảnh chứa 3 biển số = **1 lượt** và **3 biển số**.

**Lý do:** đây là chỗ dễ sai nhất trong toàn bộ phần thống kê, và cái sai này **nguy hiểm vì trông
vẫn hợp lý**. Gọi cả hai là "số lần nhận dạng" thì:

* Người đọc coi hai con số là thay thế được cho nhau.
* Mọi tỉ lệ tính từ đó (biển/lượt, thời gian/lượt) trở nên vô nghĩa mà không có dấu hiệu báo động.
* Một phiên webcam 30 giây có thể tạo hàng chục biển số nhưng vẫn chỉ là **một** lượt — nếu gộp,
  webcam sẽ nuốt chửng thống kê và làm sai lệch so sánh giữa ba nguồn đầu vào.

Chính vì rủi ro này mà quyết định ở mục 6.1 (một `job_id` cho cả phiên webcam) là **bắt buộc**,
không phải tuỳ chọn: gửi mỗi khung hình không kèm `job_id` sẽ mở một job mới cho **từng khung**,
biến một phiên 30 giây thành ~40 lượt tải lên. Không có gì hỏng thấy được — dashboard chỉ lặng lẽ
trở nên sai.

Bảng `by_input_type` cũng tách `job_count` và `detection_count`, và đây là lý do chọn **biểu đồ cột nhóm
thay vì biểu đồ tròn**: biểu đồ tròn chỉ mã hoá được **một** đại lượng, nên sẽ giấu mất đúng cái khác biệt
đáng nói nhất giữa webcam và ảnh tĩnh.

### 6.3. Hiển thị `raw_ocr_text` cạnh `plate_number`

**Quyết định:** khi chuỗi OCR thô **khác** biển số cuối cùng, giao diện hiển thị **cả hai**
kèm ghi chú rằng chuỗi đã qua hậu xử lý. Điều này áp dụng ở **ba nơi**: thẻ kết quả trang ảnh,
dòng trong bảng Lịch sử, và modal chi tiết. Khi hai chuỗi trùng nhau thì không hiện lặp,
tránh làm rối màn hình bằng thông tin không mang tin.

**Lý do:** FR-1.5 yêu cầu lưu song song hai chuỗi, và mục đích của việc lưu song song đó là
**đo được mức đóng góp riêng của bước hậu xử lý regex**. Nếu giao diện chỉ hiện kết quả cuối,
dữ liệu vẫn nằm trong CSDL nhưng **không ai nhìn thấy** — và một số liệu không quan sát được
thì không thể đưa vào phần Đánh giá.

Hiển thị song song cho ba lợi ích cụ thể:

1. **Thấy ngay hậu xử lý làm gì** — `90C76040` → `90C-76040` là chuẩn hoá dấu gạch;
   `51A-I234O` → `51A-12340` là sửa nhầm ký tự O/0 và I/1.
2. **Phát hiện hậu xử lý sửa sai** — nếu regex biến một chuỗi đúng thành chuỗi sai, chỉ có cách
   nhìn cả hai mới thấy được.
3. **Bằng chứng trực quan cho quyển đồ án** — ảnh chụp màn hình có sẵn cặp thô/đã sửa là minh chứng
   trực tiếp, không cần dựng thêm bảng số liệu.

Cùng tinh thần đó, `confidence` (bước phát hiện YOLO) và `ocr_confidence` (bước đọc ký tự) **luôn
hiển thị tách biệt, không gộp trung bình**. Gộp lại thì khi chất lượng kém sẽ không biết bước nào
đang kém — mà đó chính là phân tích cần cho chương Đánh giá.

### 6.4. Xử lý bất đồng bộ cho video

Trang video **không** chờ phản hồi đồng bộ. API trả `202 { job_id }` ngay, giao diện hỏi tiến độ định kỳ.
Video 60 giây cần khoảng 200 giây trên CPU — chờ đồng bộ **chắc chắn** vượt timeout HTTP,
và người dùng sẽ thấy một lỗi mạng cho một tác vụ thực ra vẫn đang chạy tốt.

Việc hỏi tiến độ **tự dừng** khi tác vụ đạt trạng thái kết thúc (`completed` / `failed` / `cancelled`).

### 6.5. Trạng thái tra cứu nằm trên URL

Bộ lọc, sắp xếp và số trang của Lịch sử được đồng bộ vào query string thay vì giữ trong state cục bộ.
Đổi lại một chút phức tạp, được ba thứ: tải lại trang không mất bộ lọc, nút Back của trình duyệt hoạt động
đúng nghĩa, và một kết quả tra cứu có thể dán vào báo cáo dưới dạng đường link tái lập được.

### 6.6. Lỗi được chuẩn hoá tại một điểm duy nhất

Mọi lỗi HTTP đi qua interceptor trong `services/api.ts` và ra thành một kiểu `ApiError` thống nhất,
với `message` **tiếng Việt sẵn sàng hiển thị**. Thông báo do backend cung cấp luôn được ưu tiên
(backend biết chính xác cái gì hỏng); chỉ khi không có mới dùng bản dự phòng theo mã HTTP.

Mỗi request mang một `X-Request-ID`. Khi lỗi, mã này được hiện cho người dùng trích dẫn — đủ để đối chiếu
ngược với log máy chủ mà **không** phơi bày bất kỳ chi tiết nội bộ nào.

### 6.7. Nút "Huỷ tác vụ" hiện diện nhưng vô hiệu hoá

FR-2.6 yêu cầu chức năng huỷ. Worker phía backend **có** tôn trọng việc huỷ — nó đọc lại trạng thái tác vụ
sau mỗi vài khung và dừng — nhưng **không có route HTTP nào đặt được trạng thái đó**: tài liệu OpenAPI
đang chạy chỉ phơi bày 9 đường dẫn (mang 10 thao tác), không đường nào huỷ tác vụ.

Nút vì vậy được để **hiện diện và vô hiệu hoá**, kèm tooltip "Chức năng đang được phát triển",
thay vì nối vào một endpoint tự bịa. Gọi một endpoint không tồn tại sẽ nhận 404 và để người dùng
**tin rằng tác vụ đã dừng trong khi nó vẫn chạy** — một lời nói dối tệ hơn hẳn một nút xám.

---

## 7. Đánh giá đối chiếu NFR-U1 → NFR-U5

| Mã | Yêu cầu | Cách đáp ứng | Kết luận |
|---|---|---|---|
| **NFR-U1** | Người dùng mới hoàn thành lượt nhận dạng ảnh đầu tiên **≤ 3 click**, không cần đọc tài liệu | (1) bấm *Nhận dạng ảnh* ở sidebar → (2) bấm khung kéo–thả và chọn tệp → (3) bấm *Nhận dạng*. Đúng **3 thao tác**. Dashboard rỗng còn rút ngắn hơn: nút *Nhận dạng ảnh đầu tiên* dẫn thẳng sang trang, còn **2 thao tác**. Mọi khung rỗng đều ghi sẵn việc cần làm tiếp | ✅ Đạt |
| **NFR-U2** | 100% thao tác > 500 ms có phản hồi trực quan | Tải ảnh/video: thanh tiến độ **theo byte thật**. Suy luận: spinner + câu giải thích lý do chậm. Tác vụ video: phần trăm + số khung/tổng khung, cập nhật định kỳ. Webcam: chỉ báo *đang gửi* trên khung hình + bảng đo trực tiếp. Tải danh sách: skeleton lần đầu, làm mờ bảng cũ ở lần sau. Nút *Làm mới* / *Tải lại*: biểu tượng xoay + nhãn *Đang tải…*. Xoá bản ghi: nút chuyển trạng thái đang xử lý. Tải tệp về: nút hiện *Đang xuất…* | ✅ Đạt |
| **NFR-U3** | Lỗi tiếng Việt, nêu nguyên nhân và cách khắc phục, không lộ mã lỗi kỹ thuật | Toàn bộ lỗi đi qua một bộ chuẩn hoá duy nhất. Lỗi camera có panel riêng gồm *nguyên nhân* + *cách sửa cụ thể theo đúng nguyên nhân*. Lỗi bộ lọc rỗng đi kèm nút *Xoá bộ lọc*. Không hiện stack trace, không hiện mã HTTP; thay vào đó là `request_id` để đối chiếu log | ✅ Đạt |
| **NFR-U4** | Dùng được từ 1366×768 trở lên, không vỡ layout | Lưới của các thẻ chỉ số là 2 cột ở 1366px và 4 cột trên màn rộng — **không bao giờ** rớt xuống 1 cột trên ngưỡng tối thiểu. Sidebar cố định từ breakpoint `lg` (1024px) trở lên, dưới ngưỡng đó chuyển thành ngăn kéo có nút đóng. Trang ảnh và webcam dùng lưới 2 cột co giãn `minmax(0, …)` nên nội dung dài không đẩy vỡ khung. Bảng lịch sử cuộn ngang trong khung riêng. Ảnh chụp màn hình trong tài liệu này chụp ở **1440×900** | ✅ Đạt (kiểm tra bằng ảnh chụp thực tế ở 1440×900; **chưa** đo thủ công ở đúng 1366×768) |
| **NFR-U5** | Tương phản màu đạt WCAG AA (≥ 4,5:1) cho chữ chính | Bảng màu định nghĩa tập trung trong `tailwind.config.js` + `index.css` theo cặp nền/chữ (`surface`/`content`, `content-muted`), không rải màu tuỳ tiện trong từng thành phần. Chữ chính dùng tông rất tối trên nền trắng/xám nhạt. Trạng thái (thành công / cảnh báo / lỗi) **không chỉ dùng màu**: luôn kèm biểu tượng và chữ, nên vẫn đọc được khi mù màu | ⚠️ Đạt theo thiết kế, **chưa đo bằng công cụ** (xem mục 8) |

---

## 8. Hạn chế hiện tại và hướng cải thiện

### 8.1. Hạn chế về chức năng

| # | Hạn chế | Ảnh hưởng | Hướng xử lý |
|---|---|---|---|
| 1 | **Không huỷ được tác vụ video** (FR-2.6, mức S). API không có endpoint huỷ; nút hiện diện nhưng vô hiệu hoá | Người dùng lỡ tải nhầm video 200 MB phải chờ hết | Backend bổ sung `POST /api/jobs/{id}/cancel`; giao diện chỉ cần bỏ `disabled` và nối hàm — phần còn lại đã sẵn sàng |
| 2 | **Không xoá được nhiều bản ghi cùng lúc** (FR-5.4, mức C) | Dọn dữ liệu thử nghiệm phải xoá từng dòng | Thêm cột checkbox + gọi `DELETE` tuần tự, hoặc backend bổ sung endpoint xoá theo lô |
| 3 | **Xuất chỉ có CSV, chưa có JSON** (FR-5.2 nêu "CSV hoặc JSON") | Nhỏ — CSV đã đáp ứng yêu cầu chấp nhận (mở được bằng Excel, UTF-8 có BOM) | Thêm tuỳ chọn định dạng khi backend hỗ trợ |
| 4 | **Trang video chưa xem trước video kết quả ngay trong giao diện** — chỉ có nút tải về | Người dùng phải tải xuống mới xem được nhãn đã vẽ | Nhúng thẻ `<video>` trỏ tới `output_url` |
| 5 | **Danh sách kết quả một tác vụ video giới hạn 100 dòng** (trần `MAX_PAGE_SIZE` của backend) | Video sinh > 100 biển số khác nhau sẽ bị cắt bớt ở trang này | Đã có lối thoát: toàn bộ dữ liệu vẫn tra cứu được ở trang Lịch sử bằng bộ lọc. Có thể thêm phân trang cho bảng này |

### 8.2. Hạn chế về kiểm chứng

| # | Hạn chế | Hướng xử lý |
|---|---|---|
| 6 | ✅ **Đã giải quyết.** Khi tài liệu này được viết lần đầu, backend còn chạy `StubPipeline` nên biển số hiển thị là giả lập. **Hiện backend đã nạp mô hình thật** (`models/baseline-416-v1.pt`, `/health` → `model_loaded: true`) và `StubPipeline` đã bị đưa ra khỏi đường chạy chính. Đúng như dự đoán, hợp đồng API không đổi ⇒ **frontend không phải sửa dòng nào** | Còn lại: chụp lại bộ ảnh minh hoạ với kết quả nhận dạng thật (xem hạn chế 10) |
| 7 | **NFR-U5 chưa được đo bằng công cụ.** Tương phản màu đạt theo thiết kế nhưng chưa chạy axe DevTools hay Lighthouse để có số liệu tỉ lệ tương phản cụ thể | Chạy Lighthouse Accessibility + axe DevTools trên cả 5 trang, ghi lại tỉ lệ đo được cho từng cặp màu chính |
| 8 | **NFR-U4 chưa kiểm tra ở đúng 1366×768.** Ảnh chụp minh hoạ ở 1440×900; bố cục đã tính cho ngưỡng 1366 nhưng chưa có bằng chứng chụp màn hình ở đúng độ phân giải đó | Chụp lại bộ ảnh ở 1366×768 và bổ sung vào `docs/screenshots/` |
| 9 | **Chưa có kiểm thử tự động cho giao diện.** `playwright` đã nằm trong devDependencies và đã dùng để chụp ảnh màn hình, nhưng chưa có bộ test hồi quy | Viết test E2E cho luồng chính: tải ảnh → thấy kết quả; lọc lịch sử → đúng số dòng; xoá → biến mất |
| 10 | **Ảnh chụp màn hình hiện chỉ ở trạng thái rỗng/ban đầu** với các trang Ảnh, Video và Webcam. Chưa có ảnh minh hoạ trạng thái *success* của ba trang này | Chụp bổ sung sau khi có mô hình thật và dữ liệu mẫu đủ đại diện |

### 8.3. Hướng cải thiện thêm

1. **Tự động làm mới dashboard** — hiện phải bấm *Làm mới* thủ công. Có thể làm mới định kỳ,
   nhưng cần thận trọng: cập nhật ngầm khi người dùng đang đọc số sẽ gây khó chịu hơn là hữu ích.
2. **Chế độ tối** — bảng màu đã tập trung ở một chỗ nên chi phí thêm không lớn.
3. **Xem trước theo lô** — hiện mỗi lần chỉ xử lý một ảnh. Tải lên nhiều ảnh cùng lúc sẽ hữu ích
   khi cần dựng nhanh dữ liệu đánh giá.
4. **Điều hướng bằng bàn phím cho bảng lịch sử** — modal và nút đã hỗ trợ, nhưng chưa có phím tắt
   di chuyển giữa các dòng.
5. **Ghim so sánh** — chọn hai bản ghi để so sánh cạnh nhau chuỗi thô và chuỗi đã hậu xử lý,
   phục vụ trực tiếp cho phần đánh giá đóng góp của bước regex.

---

## 9. Tài liệu liên quan

| Tài liệu | Nội dung |
|---|---|
| `frontend/README.md` | Cài đặt, chạy, cấu trúc thư mục, biến môi trường, proxy, xử lý sự cố |
| `docs/00-requirements/functional-requirements.md` | Danh sách yêu cầu chức năng FR-1 → FR-6 |
| `docs/00-requirements/non-functional-requirements.md` | Yêu cầu phi chức năng, gồm NFR-U1 → NFR-U5 |
| `docs/architecture/system-architecture.md` | Kiến trúc tổng thể và các quyết định AD-xx |
| `docs/screenshots/` | Ảnh chụp màn hình dùng trong tài liệu này |
