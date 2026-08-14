# Kịch bản demo trực tiếp

**Hệ thống nhận dạng biển số xe Việt Nam ứng dụng Trí tuệ nhân tạo**
Tài liệu dùng riêng cho buổi bảo vệ — không nộp cho hội đồng.

---

## 0. Đọc trước tiên — trạng thái thật của hệ thống tại thời điểm demo

Ba sự thật phải nắm chắc trước khi bước vào phòng. Nếu quên, sẽ nói sai trước hội đồng:

| Sự thật | Hệ quả với demo |
|---|---|
| Backend **đang chạy pipeline thật** với `models/best.pt` (mô hình chính thức). `/health` trả về **`model_loaded: true`**, engine `yolo:best.pt+paddleocr-PP-OCRv5-mobile` | Kết quả nhận dạng trên màn hình là **thật**, không phải mô phỏng. Dùng nhánh "`model_loaded: true`" ở mục 2.0. `StubPipeline` đã bị đưa ra khỏi đường chạy chính; phương án lùi hiện là `UnavailablePipeline` (ném lỗi thay vì bịa biển số) |
| Mô hình chính thức **`best.pt` đã huấn luyện xong** (YOLO11n, `imgsz=640`, split v3, 20 epoch): mAP@0.5 = **0,9829** · mAP@0.5:0.95 = **0,7834** · P = **0,9837** · R = **0,9714** — **đạt cả bốn** chỉ tiêu detection, đo trên split v3 sạch rò rỉ tên-tệp | ✅ Được nói "detection đạt chỉ tiêu". Baseline 416/v1 (mAP 0,9933) chỉ là **mô hình đối chứng** — không trích như số chính thức. ⚠️ **OCR biển 2 dòng KHÔNG đạt** — nếu bị hỏi, nói thẳng (A4 0,873 / A6 0,656, toàn bộ khoảng cách ở biển 2 dòng) |
| **NFR-P1 ĐẠT:** độ trễ E2E p95 = **731 ms** client-side / **780 ms** in-process trên `best.pt` (mục tiêu 800 ms) | Máy chạy **trong ngân sách**. Nếu bị hỏi "sao báo cáo đầu ghi 5.857 ms": con số cũ bị nhiễm do tải cạnh tranh + sai checkpoint + lỗi crop; đo lại trên máy rảnh với `best.pt` về 731 ms. Phân rã: OCR 64,3% / detect 34,2% |
| Thư mục `demo/` cần ảnh và video mẫu chuẩn bị trước | Ảnh và video mẫu phải sẵn sàng. Đây là việc phải làm trước, không phải việc kiểm tra lại |

> **Quy tắc số một của buổi demo:** không câu nào được nói vượt quá cái đang chạy trên màn hình.

---

## 1. Chuẩn bị trước buổi bảo vệ

### 1.1. Checklist làm trước — mốc T-1 ngày

- [ ] Chuẩn bị bộ ảnh mẫu vào `demo/` (thư mục hiện đang rỗng) — chi tiết mục 1.4
- [ ] Chạy thử **toàn bộ** kịch bản mục 2 từ đầu đến cuối, đúng thứ tự, ít nhất **2 lần**
- [ ] Ghi màn hình một lượt chạy thành công làm phương án dự phòng (mục 1.7)
- [ ] Kiểm tra pin máy, mang theo sạc và cổng chuyển HDMI/VGA
- [ ] Tắt thông báo hệ thống, tắt Zalo/Messenger, đóng Zoom/Teams/Meet để tránh cửa sổ chen ngang

### 1.2. Khởi động backend

Lệnh lấy đúng từ `README.md` mục 8 — chạy từ thư mục gốc `d:/DATN`:

```bash
backend/.venv/Scripts/python.exe -m uvicorn backend.main:app --port 8000
```

Chờ đến khi log hiện `Application startup complete`. Swagger tại <http://localhost:8000/docs>.

> **Không** thêm cờ `--reload` khi demo. Reload sẽ khởi động lại tiến trình giữa chừng nếu
> có bất kỳ tệp nào bị chạm vào, và việc đó xảy ra đúng lúc đang trình bày thì không cứu được.

### 1.3. Khởi động frontend

```bash
cd frontend
nvm use 18.20.8
npm run dev
```

Giao diện tại <http://localhost:5173>.

> Cổng 5173 đặt `strictPort: true` — nếu cổng bị chiếm, Vite **báo lỗi và dừng hẳn**,
> không tự nhảy cổng khác. Nếu gặp lỗi này: đóng tiến trình Vite cũ rồi chạy lại,
> **đừng** sửa cổng vì proxy `/api` `/files` `/health` đang trỏ theo cấu hình cũ.

### 1.4. Kiểm tra trước — bắt buộc, làm ngay sau khi khởi động

**Bước 1 — gọi `/health`:**

```bash
curl http://localhost:8000/health
```

Trường cần đọc và ý nghĩa:

| Trường | Giá trị mong đợi | Nếu khác thì sao |
|---|---|---|
| `status` | **`"ok"`** — cả CSDL lẫn mô hình đều sẵn sàng | `degraded` **không phải lỗi** — xem `database_connected` và `model_loaded` để biết vế nào hỏng |
| `database_connected` | `true` | `false` ⇒ CSDL chưa migrate. Chạy Alembic trước khi làm gì khác |
| `model_loaded` | **`true`** — trạng thái hiện tại, mô hình chính thức đã nạp | `false` ⇒ `ALPR_MODEL_PATH` đang trỏ vào tệp không tồn tại. Mặc định là `models/best.pt` (**đã có**); kiểm tệp tồn tại rồi khởi động lại. Đây là điều **phải kiểm trước khi vào phòng**, không phải phát hiện giữa lúc demo |
| `engine` | `yolo:best.pt+paddleocr-PP-OCRv5-mobile` | Nếu chuỗi này không có tiền tố `yolo:` thì đường chạy chính **không phải** pipeline thật |
| `version`, `uptime_seconds` | có giá trị | — |

**Bước 2 — mở <http://localhost:5173>**, ứng dụng vào thẳng trang **Nhận dạng ảnh** (trang chủ).
Kiểm ba mục sidebar hiện đủ: Nhận dạng ảnh · Nhận dạng video · Lịch sử.

> ⚠️ **Đổi so với bản trước.** Trang **Tổng quan** đã gỡ khỏi giao diện, nên **thẻ
> Trạng thái hệ thống không còn hiển thị trên màn hình**. Từ nay `curl /health` ở Bước 1 là chỗ
> **duy nhất** đọc được `model_loaded`. Mặt tốt: không còn nguy cơ một cảnh báo mô phỏng tự bật lên
> giữa lúc trình bày. Mặt phải trả giá: quên chạy Bước 1 thì vào phòng mới biết mô hình chưa nạp —
> **Bước 1 nay là bắt buộc tuyệt đối, không phải bước kiểm tra cho yên tâm.**

**Bước 3 — đảm bảo CSDL đã có sẵn vài bản ghi.** Trang **Lịch sử** rỗng thì mở ra chỉ thấy trạng thái
rỗng, và Bước 3 của kịch bản (đếm 1 lượt / 3 biển qua `GET /api/statistics`) không có nền để so sánh.
Chạy trước 5–10 ảnh để bảng lịch sử và các bộ đếm có dữ liệu.

### 1.5. Ảnh mẫu cần chuẩn bị — bốn loại, đặt trong `demo/`

Đặt tên có số thứ tự để mở đúng thứ tự kịch bản, không phải dò tìm giữa lúc trình bày:

| Tệp | Loại | Vai trò trong kịch bản |
|---|---|---|
| `01-bien-1-dong.jpg` | Ô tô, biển 1 dòng, chụp thẳng, rõ nét | Ca dễ — mở màn chắc thắng |
| `02-bien-2-dong.jpg` | Xe máy, biển 2 dòng, rõ nét | **Ca khó** — điểm nhấn kỹ thuật số một |
| `03-nhieu-bien.jpg` | Một ảnh chứa **3 biển số** trở lên | Chứng minh quy tắc đếm 1 lượt ≠ 3 lượt |
| `04-khong-co-bien.jpg` | Ảnh phong cảnh / vật thể, **không** có biển số nào | Chứng minh trạng thái rỗng ≠ trạng thái lỗi |
| `05-video-ngan.mp4` | Video **10–15 giây**, ≤ 20 MB | Xem mục 1.6 về thời lượng |

**Quy tắc chọn ảnh:** mỗi tệp trên phải **đã được chạy thử ít nhất một lần** và đã biết kết quả
ra sao. Ảnh chưa thử bao giờ thì không đưa vào `demo/`.

Nếu có một ảnh mà mô hình đọc sai theo kiểu **thú vị** (ví dụ nhầm `O`↔`0` rồi được hậu xử lý
sửa lại đúng), **giữ lại làm ảnh số 06** — đó là minh chứng sống cho mục 3.1, đáng giá hơn
một ảnh chạy hoàn hảo.

### 1.6. Video mẫu — chọn ngắn, đây là chỗ dễ cháy giờ nhất

Suy luận chạy **trên CPU**. Theo `06-ui-documentation.md`, video **60 giây cần khoảng
200 giây** xử lý. Một video 1 phút sẽ ngốn hết thời gian demo.

- Chọn video **10–15 giây** ⇒ khoảng **35–50 giây** xử lý. Vẫn dài, nhưng lấp được bằng lời.
- **Chạy sẵn một tác vụ video trước khi vào phòng.** Tác vụ đã hoàn thành vẫn tra cứu được
  đầy đủ ở trang Video và trang Lịch sử. Nếu cháy giờ, chuyển sang xem kết quả tác vụ cũ.
- Nhớ: nút **Huỷ tác vụ** hiện diện nhưng **bị vô hiệu hoá** (FR-2.6 mới đạt một phần).
  Đã lỡ bấm chạy video dài thì không dừng được — đây chính là lý do phải chọn video ngắn.

### 1.7. Chế độ thời gian thực qua API *(tuỳ chọn — chỉ demo nếu còn giờ)*

> **Thay đổi phạm vi:** trang Webcam đã được **gỡ khỏi giao diện web**; chế độ thời
> gian thực chỉ còn ở **tầng API** (`POST /api/detect/frame`). Không còn bước xin quyền camera,
> không còn ứng dụng nào tranh chiếm thiết bị — đây là một nguồn sự cố demo đã biến mất.

- [ ] Mở sẵn **một cửa sổ terminal** cạnh trình duyệt, đã `cd` về thư mục gốc dự án.
      ⚠️ **Nay là việc bắt buộc, không còn tuỳ chọn** — Bước 3 (bắt buộc) cũng gọi `curl` vào
      `GET /api/statistics` sau khi trang Tổng quan bị gỡ
- [ ] Chạy thử **trước** lệnh ở Bước 5 ít nhất một lần để chắc chắn `curl` có trên máy và
      đường dẫn ảnh mẫu đúng
- [ ] Nếu không muốn dùng terminal: mở **Swagger** tại <http://localhost:8000/docs>, mục
      `POST /api/detect/frame`, bấm *Try it out* rồi chọn tệp — trực quan hơn khi chiếu
- [ ] Ghi nhớ để trả lời nếu bị hỏi về chu kỳ gửi khung: trên CPU mỗi khung mất ~300–400 ms,
      nên client thời gian thực phải gửi ở chu kỳ **700 ms hoặc 1 giây** và dùng hàng đợi một khe
      (bỏ khung khi khe còn bận). Hạ chu kỳ xuống 400 ms **không** làm nhanh hơn, chỉ làm
      số khung bị bỏ tăng vọt.

### 1.8. Phương án OFFLINE — giả định phòng bảo vệ không có mạng

Đây không phải tình huống hiếm. Chuẩn bị như thể **chắc chắn** mất mạng:

| Hạng mục | Việc phải làm trước |
|---|---|
| **Gói phụ thuộc** | `npm install` và cài đặt Python **đã xong từ trước**. Tuyệt đối không để `npm install` chạy trong phòng |
| **Trọng số mô hình** | `models/best.pt` **nằm sẵn trên đĩa**. Không tải từ Colab/Drive tại chỗ |
| **Model PaddleOCR** | PaddleOCR tải model về cache lần chạy đầu. **Chạy thử ít nhất một lần khi còn mạng** để cache sẵn, nếu không lần gọi đầu tiên sẽ treo dài rồi lỗi |
| **`yolo11n.pt`** | Đã có sẵn ở thư mục gốc — kiểm tra lại nó còn đó |
| **Ảnh và video mẫu** | Nằm trong `demo/` **trên máy**, không phải trên Drive/Zalo |
| **Toàn hệ thống** | `localhost:8000` và `localhost:5173` chạy hoàn toàn nội bộ, **không cần mạng** — đây là ưu thế, nên nói ra nếu hội đồng hỏi về triển khai |
| **Kiểm chứng** | **Tắt Wi-Fi và chạy thử trọn kịch bản một lần.** Đây là bước duy nhất chứng minh phương án offline có thật |
| **Tài liệu và slide** | Bản PDF nằm trên máy + một USB dự phòng. Không mở từ Google Drive |
| **Video ghi màn hình dự phòng** | Tệp MP4 trên máy, đã kiểm tra mở được bằng trình phát cục bộ |

---

## 2. Kịch bản demo 5–7 phút

**Tổng bắt buộc: 320 giây = 5 phút 20 giây.**
**Tổng kể cả bước tuỳ chọn: 360 giây = 6 phút 00 giây.**

> **Đổi so với bản trước.** Bước mở màn "Tổng quan (Dashboard)" **45 giây đã bị xoá**
> cùng với trang Tổng quan. Các bước còn lại được **đánh số lại liên tục**, ngân sách giảm từ
> 365 s xuống **320 s**. Ý "khoe số liệu tổng hợp" không mất — nó chuyển vào Bước 3 dưới dạng
> một lời gọi `GET /api/statistics`.

Ngân sách này là **tổng cộng đúng bằng thời lượng ghi ở tiêu đề từng bước bên dưới** — bảng sau
liệt kê lại để kiểm tra chéo được, sửa thời lượng bước nào thì phải sửa lại bảng này:

| Bước | Nội dung | Thời lượng |
|:-:|---|---:|
| 2.0 | Câu mở đầu về `model_loaded` | 10 s |
| 1 | Nhận dạng ảnh biển 1 dòng | 60 s |
| 2 | Nhận dạng ảnh biển 2 dòng — **điểm nhấn chính** | 75 s |
| 3 | Ảnh nhiều biển số + `GET /api/statistics` | 50 s |
| 4 | Video | 60 s |
| 6 | Lịch sử và tra cứu | 50 s |
| 2.8 | Câu kết | 15 s |
| | **Tổng bắt buộc** (10+60+75+50+60+50+15) | **320 s = 5 ph 20 gi** |
| *5* | *Thời gian thực qua API* — **tuỳ chọn**, chạy sau Bước 4 | *40 s* |
| | **Tổng kể cả tuỳ chọn** (320 + 40) | **360 s = 6 ph 00 gi** |

Cột thời lượng là ngân sách, không phải mục tiêu — chậm hơn 20 giây
ở một bước thì bỏ hẳn Bước 5 (thời gian thực qua API, vốn là bước tuỳ chọn), đừng cắt bước biển 2 dòng.
Bỏ Bước 5 là còn đúng 5 phút 20 giây, vẫn nằm trong khung 5–7 phút.

### 2.0. Câu mở đầu — 10 giây, bắt buộc nói

Chọn **đúng một** trong hai câu, tuỳ giá trị `model_loaded` đọc được ở mục 1.4. **Trạng thái hiện tại là `true`**, nên nhánh dưới đây là nhánh sẽ dùng; nhánh `false` giữ lại làm phương án dự phòng nếu cấu hình sai lúc khởi động.

> **Nếu `model_loaded: true` — nhánh hiện hành:**
> "Em xin phép demo hệ thống đang chạy trực tiếp trên máy này. Mô hình phát hiện là mô hình
> chính thức nhóm em **tự huấn luyện** — `best.pt`, ở độ phân giải 640 trên bộ dữ liệu đã khử
> trùng lặp, đạt cả bốn chỉ tiêu phát hiện: mAP 0,983, precision 0,984, recall 0,971. Toàn bộ
> suy luận chạy trên CPU vì máy phát triển không có GPU, độ trễ một ảnh khoảng 730–780 mili-giây,
> nằm trong ngân sách 800. Em cũng xin nói thẳng một hạn chế: **OCR đọc biển hai dòng chưa đạt
> chỉ tiêu** — biển một dòng rất tốt nhưng biển xe máy hai dòng kéo độ chính xác chuỗi xuống, và
> em sẽ trình bày trung thực phần đó."

> **Nếu `model_loaded: false` — chỉ dùng khi cấu hình sai lúc khởi động:**
> "Trước khi bắt đầu, em xin nói rõ: `ALPR_MODEL_PATH` đang trỏ sai nên backend chưa nạp được
> trọng số và đang chạy phương án lùi. Endpoint `/health` báo trung thực `model_loaded: false`
> và em đọc được điều đó bằng `curl /health` trước khi vào phòng — từ khi trang Tổng quan bị gỡ,
> giao diện **không còn hiển thị trạng thái này**, nên em phải nói ra chứ hội đồng không tự thấy. Mô hình chính thức
> `best.pt` đã có sẵn trên đĩa; phần em demo về **luồng nghiệp vụ và hợp đồng API đều chạy thật**."

Nói câu này **trước**, chủ động. Để hội đồng tự phát hiện thì mọi thứ nói sau đó đều mất trọng lượng.

### Bước 1 — Nhận dạng ảnh biển 1 dòng · 60 giây

| Thao tác | Mở `localhost:5173` — ứng dụng vào thẳng trang **Nhận dạng ảnh** (trang chủ) → kéo thả `demo/01-bien-1-dong.jpg` — nhận dạng tự chạy ngay khi ảnh vào |
|---|---|
| **Lời thoại (lúc chờ)** | "Mở ứng dụng là vào thẳng màn hình nhận dạng ảnh — nghiệp vụ chính đặt ngay trang chủ, không có màn hình trung gian. Ảnh đang được tải lên — thanh tiến độ này đo theo **byte thật**, không phải hoạt ảnh giả. Sau khi tải xong, giao diện chuyển sang trạng thái chờ và nói rõ rằng mô hình chạy trên CPU nên có thể mất vài giây. Đây là chủ ý thiết kế: nói trước lý do chậm để người dùng không nghi ngờ hệ thống treo." |
| **Lời thoại (khi có kết quả)** | "Kết quả gồm ảnh có vẽ khung bao và thẻ chi tiết. Xin lưu ý **hai độ tin cậy được tách riêng**: một của bước phát hiện YOLO, một của bước đọc ký tự OCR. Gộp trung bình hai số này thì khi chất lượng kém sẽ không biết bước nào đang kém — mà đó chính là phân tích cần cho chương Đánh giá." |
| **Kỳ vọng thấy** | Bounding box đúng vị trí · thẻ kết quả có: ảnh biển đã cắt, biển số chuẩn hoá, độ tin cậy phát hiện, độ tin cậy OCR, số dòng = **1**, cờ hợp lệ định dạng VN |
| **Nếu chuỗi thô khác chuỗi cuối** | **Dừng lại và chỉ vào nó** — xem mục 3.1, đây là điểm nhấn giá trị nhất |

### Bước 2 — Nhận dạng ảnh biển 2 dòng · 75 giây · **ĐIỂM NHẤN CHÍNH**

| Thao tác | Cùng trang → chọn `demo/02-bien-2-dong.jpg` → **Nhận dạng** |
|---|---|
| **Lời thoại (trước khi bấm)** | "Ảnh tiếp theo là biển xe máy **hai dòng**. Đây là ca khó nhất, và mức khó đã được đo: trong nghiên cứu của Laroca năm 2022 trên bộ dữ liệu Brazil, OpenALPR đạt **94,3%** trên ô tô biển một dòng nhưng chỉ **45,7%** trên xe máy biển hai dòng — chênh **48,6 điểm** trên cùng một hệ thống. Đó là số liệu Brazil, em dẫn như một mốc tham chiếu, nhưng cơ chế gây lỗi là bố cục hai dòng nên hoàn toàn áp dụng cho biển Việt Nam." |<br>⚠️ **Bắt buộc nói rõ "bộ dữ liệu Brazil"** khi trích cặp số này. Nếu rút gọn thành "OpenALPR đạt 94,3%" và hội đồng tra nguồn, sẽ thành trích dẫn sai. |
| **Lời thoại (giải thích nguyên nhân gốc)** | "Nguyên nhân không nằm ở chất lượng ảnh mà ở **kiến trúc**: CRNN/CTC giả định alignment đơn điệu trên **một** dòng văn bản. Thêm nữa, module nhận dạng của PP-OCR resize ảnh về chiều cao cố định **48 px** — crop biển xe máy có tỉ lệ khoảng 1,36 nên mỗi dòng bị nén còn khoảng **24 px**. Giải pháp của em là **tách dòng rồi ghép ngang** (split-then-hstack): cắt biển thành hai dòng, ghép lại thành một dòng dài, rồi mới đưa vào OCR — đưa bài toán về đúng giả định mà kiến trúc kỳ vọng." |
| **Kỳ vọng thấy** | Biển hai dòng đọc ra **một chuỗi liền mạch** · trường **số dòng = 2** · biển số đúng định dạng |
| **Nhắc** | Đây là bước đáng dành thời gian nhất. Nếu bị cắt giờ, bỏ Bước 5 (thời gian thực qua API) chứ **không bỏ bước này**. |

### Bước 3 — Ảnh nhiều biển số + `GET /api/statistics` · 50 giây

> **Thay cho bước Tổng quan cũ.** Trang Tổng quan đã gỡ khỏi giao diện, nên hai bộ đếm
> không còn màn hình để chiếu. Chúng vẫn phục vụ nguyên vẹn ở tầng API — bước này đọc thẳng từ đó.

| Thao tác | Chọn `demo/03-nhieu-bien.jpg` → **Nhận dạng** → sau khi có kết quả, chuyển sang terminal gọi `GET /api/statistics` |
|---|---|
| **Lời thoại** | "Ảnh này có **ba** biển số, hệ thống phát hiện đủ cả ba. Điểm em muốn nhấn nằm ở phần thống kê: schema CSDL trong đề bài gốc **thiếu trường nhóm** — một ảnh nhiều biển sẽ bị đếm thành nhiều lượt và làm sai toàn bộ phần thống kê. Em đã bổ sung trường `source_job_id` và bảng `DetectionJob`. Kết quả: ảnh này làm `total_detections` **tăng 3** nhưng `total_jobs` **chỉ tăng 1**. Em xin nói thẳng: màn hình Tổng quan đã được gỡ khỏi giao diện ngày 20 tháng 7 để thu gọn phạm vi demo, nhưng endpoint thống kê **vẫn phục vụ và vẫn có kiểm thử tích hợp** — em đọc thẳng từ API để hội đồng thấy con số thật." |
| **Lệnh** | Xem khối lệnh bên dưới. Có thể thay bằng Swagger `localhost:8000/docs` → `GET /api/statistics` → *Try it out* nếu muốn trực quan hơn. |
| **Kỳ vọng thấy** | 3 bounding box · 3 thẻ kết quả · trong JSON trả về: `total_detections` **+3**, `total_jobs` **+1** so với lần gọi trước |
| **Nhắc** | **Gọi `GET /api/statistics` một lần TRƯỚC khi chạy ảnh này và ghi lại hai con số.** Không có số trước thì không chứng minh được số sau. |

```bash
# Gọi TRƯỚC khi nhận dạng ảnh 03 — ghi lại total_jobs và total_detections
curl http://localhost:8000/api/statistics

# Gọi LẠI sau khi nhận dạng xong — so hai lần
curl http://localhost:8000/api/statistics
```

> **Lưu ý về đường dẫn.** Tiền tố API đọc từ `ALPR_API_PREFIX`, **mặc định `/api`** (xem
> `backend/.env.example`), nên đường dẫn đầy đủ là `/api/statistics`. Endpoint nhận thêm tham số
> tuỳ chọn `days` cho chuỗi số liệu theo ngày; đặc tả đầy đủ xem tài liệu API
> (`docs/manuals/api-documentation.md`) hoặc Swagger đang chạy.

### Bước 4 — Video · 60 giây

| Thao tác | Sidebar → **Nhận dạng video** → chọn `demo/05-video-ngan.mp4` → **Bắt đầu xử lý** |
|---|---|
| **Lời thoại (lúc chờ)** | "Video được xử lý ở **chế độ nền**: API trả về `202` kèm mã tác vụ ngay lập tức, giao diện hỏi tiến độ định kỳ. Không làm vậy thì một video 60 giây cần khoảng 200 giây trên CPU sẽ **chắc chắn** vượt timeout HTTP, và người dùng thấy lỗi mạng cho một tác vụ thực ra vẫn đang chạy tốt." |
| **Lời thoại (về gộp trùng)** | "Ghi chú dưới bảng kết quả giải thích cơ chế **gộp trùng**: một xe xuất hiện trong hàng chục khung hình chỉ được tính **một** bản ghi. Thiếu ghi chú này, người dùng đọc con số thấp và tưởng hệ thống bỏ sót." |
| **Kỳ vọng thấy** | Thanh tiến độ % + số khung đã xử lý / tổng khung · trạng thái chuyển Đang xử lý → Hoàn thành · bảng biển số đã gộp trùng |
| **Nếu quá 60 giây** | Nói: *"Tác vụ này còn chạy, em xin chuyển sang một tác vụ đã hoàn thành từ trước để hội đồng thấy kết quả"* → mở tác vụ đã chạy sẵn ở mục 1.6 |

### Bước 5 — Thời gian thực qua API · 40 giây · **TUỲ CHỌN, bỏ trước nếu thiếu giờ**

> Trang Webcam đã được gỡ khỏi giao diện web để thu gọn phạm vi demo. Năng lực
> thời gian thực **vẫn còn nguyên ở tầng API** và bước này trình diễn đúng điều đó.

| Thao tác | Chuyển sang cửa sổ terminal đã mở sẵn (mục 1.7) và gửi một khung hình vào endpoint thời gian thực |
|---|---|
| **Lệnh** | Xem khối lệnh bên dưới. Có thể thay bằng Swagger `localhost:8000/docs` → `POST /api/detect/frame` → *Try it out* nếu muốn trực quan hơn. |
| **Lời thoại** | "Nguồn thứ ba là chế độ thời gian thực. Em đã gỡ trang webcam khỏi giao diện để thu gọn phần demo, nhưng năng lực thì vẫn nguyên: endpoint `POST /api/detect/frame` nhận **từng khung hình một** và trả kết quả kèm mã phiên `job_id`. Lời gọi đầu tiên không gửi `job_id`, máy chủ cấp mới; mọi khung sau gửi kèm mã đó, nhờ vậy **cả phiên chỉ tính là một lượt** thay vì mấy chục lượt. Client thời gian thực chỉ cần gửi lặp lại lệnh này theo chu kỳ khoảng 700 mili-giây, kèm quy tắc **một khe**: khung mới đến lúc khe còn bận thì bỏ, không xếp hàng — vì nếu xếp hàng, tốc độ vào lớn hơn tốc độ ra thì độ trễ cộng dồn vô hạn." |
| **Kỳ vọng thấy** | JSON trả về gồm `job_id`, `input_type: "webcam"`, mảng `results` với biển số, hai độ tin cậy, `bbox` và `plate_line_count` |
| **Nếu bị hỏi vì sao gỡ trang** | Trả lời ngắn theo Q&A mục **E4b** của `10-defense-qa.md`, đừng sa đà |

```bash
# Khung đầu tiên của phiên — KHÔNG gửi job_id, máy chủ sẽ cấp mới
curl -X POST http://localhost:8000/api/detect/frame \
  -F "file=@demo/01-bien-1-dong.jpg"

# Các khung tiếp theo — gửi lại job_id nhận được ở lần gọi đầu
curl -X POST http://localhost:8000/api/detect/frame \
  -F "file=@demo/02-bien-2-dong.jpg" \
  -F "job_id=<dán job_id từ phản hồi trước>"
```

> **Lưu ý về đường dẫn.** Tiền tố API đọc từ biến môi trường `ALPR_API_PREFIX`, **mặc định `/api`**
> (xem `backend/.env.example`), nên đường dẫn đầy đủ là `/api/detect/frame`. Nếu đã đổi tiền tố
> trong `.env` thì sửa lệnh cho khớp. Đặc tả tham số đầy đủ xem tài liệu API
> (`docs/manuals/api-documentation.md`) hoặc Swagger đang chạy.

### Bước 6 — Lịch sử và tra cứu · 50 giây

| Thao tác | Sidebar → **Lịch sử** → gõ vài ký tự biển số vào ô tìm → bấm tiêu đề cột **Độ tin cậy** → mở **modal chi tiết** một dòng |
|---|---|
| **Lời thoại** | "Kết quả của cả ba nguồn — ảnh, video và khung hình thời gian thực gửi qua API — đều chảy về cùng một bảng lịch sử. Tìm kiếm khớp một phần, có thể kết hợp lọc theo nguồn, khoảng thời gian và ngưỡng tin cậy. Xin lưu ý: **mọi bộ lọc đều được ghi lên URL**, nên tải lại trang không mất bộ lọc và một kết quả tra cứu có thể dán vào báo cáo dưới dạng đường link tái lập được." |
| **Lời thoại (modal)** | "Modal chi tiết cho thấy đầy đủ: ảnh gốc, ảnh biển đã cắt, hai độ tin cậy tách riêng, **chuỗi OCR thô** đặt cạnh biển số sau chuẩn hoá, số dòng, toạ độ vùng biển, và mã lần tải lên `source_job_id` — chính là trường cho phép đếm đúng ảnh nhiều biển ở bước ban nãy." |
| **Kỳ vọng thấy** | Bảng lọc đúng · URL đổi theo bộ lọc · modal đầy đủ metadata |
| **Kết** | Bấm **Xuất CSV** (1 giây) và nói: *"Toàn bộ dữ liệu xuất được ra CSV có áp đúng bộ lọc hiện hành, phục vụ cho phần đánh giá."* |

### 2.8. Câu kết — 15 giây

> "Đó là toàn bộ luồng nghiệp vụ: ba nguồn đầu vào, một đường lưu trữ, một trang tra cứu.
> Em xin nói rõ hai chỗ đã **chủ động thu gọn** trong ngày 20 tháng 7: trang Webcam và trang Tổng
> quan đều đã gỡ khỏi giao diện; năng lực tương ứng vẫn còn ở tầng API và vẫn có kiểm thử. Riêng
> việc gỡ trang Tổng quan đưa FR-4.1 — một yêu cầu mức **bắt buộc** — ra khỏi phạm vi bản này, em
> nêu thẳng chứ không để hội đồng tự phát hiện.
> Em cũng xin nói rõ phần **chưa đạt và chưa đo**: OCR biển hai dòng chưa đạt chỉ tiêu — đây là kết
> quả thật, toàn bộ khoảng cách nằm ở biển xe máy; và một số chế độ như FPS webcam, xử lý video
> thì em chưa đo. Phần phát hiện và độ trễ đầu-cuối thì đã đạt. Em xin nhận câu hỏi của hội đồng."

---

## 3. Điểm nhấn cần làm nổi bật

Bốn điểm dưới đây là thứ phân biệt một hệ thống **được hiểu** với một hệ thống **được ghép lại**.
Nếu chỉ kịp nói bốn điều trong cả buổi, thì nói bốn điều này.

### 3.1. Hiện **cả** `raw_ocr_text` và `plate_number` khi hai chuỗi khác nhau

**Thao tác:** khi thấy thẻ kết quả có hai dòng chuỗi khác nhau, **dừng lại và chỉ tay vào**.

> "Dòng trên là chuỗi OCR **thô**, dòng dưới là kết quả **sau hậu xử lý**. Ví dụ `90C76040`
> thành `90C-76040` là chuẩn hoá dấu gạch; `51A-I234O` thành `51A-12340` là sửa nhầm `I`↔`1`
> và `O`↔`0`. Việc lưu song song hai chuỗi không phải để trang trí — nó cho phép **đo định lượng
> đóng góp riêng của bước hậu xử lý**, bằng hiệu số giữa độ chính xác trước và sau chuẩn hoá.
> Nếu giao diện chỉ hiện kết quả cuối, dữ liệu vẫn nằm trong CSDL nhưng không ai nhìn thấy —
> và một số liệu không quan sát được thì không đưa vào phần Đánh giá được."

Bổ sung nếu có thời gian: hiển thị song song còn giúp **phát hiện hậu xử lý sửa sai** — nếu
regex biến một chuỗi đúng thành chuỗi sai, chỉ nhìn cả hai mới thấy.

### 3.2. Ảnh 3 biển số = **1 lượt**, không phải 3

> "Đây là chỗ dễ sai nhất trong toàn bộ phần thống kê, và nó nguy hiểm vì **trông vẫn hợp lý**.
> Gộp hai khái niệm lại thì mọi tỉ lệ tính từ đó — biển trên lượt, thời gian trên lượt — đều
> vô nghĩa mà không có dấu hiệu báo động nào. Nặng nhất là chế độ thời gian thực: một phiên 30 giây gửi
> hàng chục khung hình vào `POST /api/detect/frame`; nếu mỗi khung mở một job mới thì một phiên biến
> thành ~40 lượt tải lên và nuốt chửng toàn bộ thống kê. Vì vậy cả phiên dùng chung **một** `job_id`."

### 3.3. `/health` báo **trung thực** `model_loaded`

> "Endpoint `/health` không trả về `ok` một cách vô điều kiện. Nó thăm dò riêng CSDL và riêng
> pipeline; chỉ khi **cả hai** đều sẵn sàng thì `status` mới là `ok`, ngược lại là `degraded`.
> Khi trọng số không nạp được, `model_loaded` là `false` — và quan trọng hơn, hệ thống
> **không rơi về pipeline giả lập**: phương án lùi là `UnavailablePipeline`,
> nó **ném lỗi** thay vì trả về một biển số bịa ra trông rất thuyết phục. Em chọn để hệ thống
> **tự tố cáo** trạng thái của nó thay vì trang trí một dấu tích xanh."

Đây là điểm mạnh **kể cả khi** `model_loaded: false`. Một hệ thống trung thực về giới hạn của
mình đáng tin hơn một hệ thống luôn báo xanh. Nếu hội đồng hỏi về `StubPipeline`: nó **vẫn còn
trong mã nguồn** nhưng chỉ chạy khi đặt tường minh `ALPR_USE_STUB=true`, và `build_pipeline`
ghi một dòng log mức `WARNING` nói rõ mọi kết quả trả về đều là bịa.

### 3.4. Biển 2 dòng đọc được

Đã trình bày ở Bước 3. Nhắc lại một lần trong phần kết: đây là **48,6 điểm chênh lệch** mà
hầu hết pipeline thông dụng bỏ ngỏ, và biển 2 dòng chiếm phần lớn xe máy tại Việt Nam.

---

## 4. Phương án dự phòng

| Sự cố | Xử lý ngay |
|---|---|
| **Backend không khởi động** | Đọc dòng lỗi cuối cùng. (1) Cổng 8000 bị chiếm ⇒ đóng tiến trình cũ, chạy lại. (2) `database_connected: false` ⇒ CSDL chưa migrate, chạy Alembic. (3) Lỗi nạp mô hình ⇒ **vẫn chạy được** với `StubPipeline`, nói rõ và demo tiếp phần luồng nghiệp vụ. **Trần thời gian: 60 giây.** Quá 60 giây thì chuyển sang video ghi màn hình và nói: *"Để không mất thời gian của hội đồng, em xin trình bày qua bản ghi màn hình đã chạy trước, phần mã nguồn em sẵn sàng mở ra khi hội đồng cần."* |
| **Lệnh `curl /api/statistics` ở Bước 3 lỗi** | Bước 3 là **bắt buộc**, không bỏ được — nhưng đổi được đường vào. Mở **Swagger** `localhost:8000/docs` → `GET /api/statistics` → *Try it out*. Nếu Swagger cũng không mở được: chuyển sang trang **Lịch sử**, đếm bằng mắt ba bản ghi vừa sinh và nói: *"Ba biển này mang cùng một `source_job_id` — hội đồng xem trong modal chi tiết; đó chính là trường khiến chúng được tính là một lượt."* **Trần: 20 giây.** |
| **Lệnh `curl` ở Bước 5 lỗi** | Bỏ qua **ngay**, đừng gõ lại. Bước 5 là tuỳ chọn. Nói: *"Em xin phép bỏ qua phần này — chế độ thời gian thực dùng chung đúng pipeline với nhận dạng ảnh mà em vừa demo, khác biệt chỉ ở chỗ khung hình được gửi lặp lại theo chu kỳ và cả phiên gộp về một `job_id`."* Rồi chuyển sang Lịch sử. **Trần: 15 giây.** Nếu vẫn muốn trình diễn: mở Swagger `localhost:8000/docs` → `POST /api/detect/frame`. |
| **Model đọc SAI biển số ngay trước mặt hội đồng** | **Bình tĩnh, không thử lại, không xin lỗi rối rít.** Biến nó thành nội dung: *"Đây là một ca sai và em xin phân tích luôn. Hệ thống đang đọc `<X>` thay vì `<Y>` — sai ở ký tự `<Z>`. Nhìn vào hai chuỗi hiển thị song song, em biết được lỗi nằm ở **bước OCR** hay ở **bước hậu xử lý** — đó chính là lý do em lưu cả chuỗi thô. Nguyên nhân có thể là <góc chụp / mờ / thiếu sáng / biển 2 dòng bị nén>. Hướng cải thiện đã xác định: bộ dữ liệu đang mở rộng từ 4.578 lên khoảng 21.000 ảnh, và huấn luyện hiện mới đến epoch 5 trên 40."* Một sinh viên **giải thích được** cái sai của mình gây ấn tượng tốt hơn một sinh viên có kết quả đẹp mà không hiểu vì sao đẹp. |
| **Mất mạng** | Không ảnh hưởng — toàn hệ thống chạy trên `localhost`. Nói luôn ra: *"Hệ thống chạy hoàn toàn nội bộ, không phụ thuộc dịch vụ đám mây nào."* Biến sự cố thành điểm cộng về triển khai. **Điều kiện:** phải đã kiểm chứng offline theo mục 1.8. |
| **Máy chậm, xử lý lâu** | **Đừng im lặng nhìn spinner.** Lấp bằng nội dung có ích: *"Trong lúc chờ, em xin nói rõ về hiệu năng: máy phát triển không có GPU CUDA, toàn bộ suy luận chạy trên CPU, mỗi khung mất khoảng 300–400 ms. Con số này không so sánh trực tiếp được với các hệ thống công bố trên GPU, và em ghi rõ điều đó trong phần Đánh giá."* Sự chậm đã được **giải thích trước** thì không còn là sự cố. Nếu quá 90 giây: huỷ, chuyển sang kết quả đã chạy sẵn. |
| **Ảnh chuẩn bị sẵn bị mất** | Ba lớp dự phòng, theo thứ tự: (1) bản sao trên **USB**; (2) vài ảnh biển số lưu sẵn trong **thư viện ảnh của điện thoại** — chụp lại màn hình điện thoại hoặc gửi ảnh sang máy rồi tải lên như bình thường; (3) trang **Lịch sử** vẫn còn toàn bộ kết quả đã chạy trước, mở modal chi tiết ra vẫn thấy đủ ảnh gốc, ảnh cắt và metadata. **Lớp 3 luôn có sẵn** miễn là CSDL không bị xoá. |
| **Frontend trắng trang / lỗi 5173** | Vite đặt `strictPort` nên cổng bị chiếm sẽ dừng hẳn. Đóng tiến trình Vite cũ, chạy lại `npm run dev`. Nếu không được: demo trực tiếp trên **Swagger** tại `localhost:8000/docs` — vẫn chứng minh được API chạy thật, chỉ kém trực quan. |
| **Kết quả rỗng (ảnh không có biển số)** | Đây **không phải sự cố**, mà là hành vi đúng: *"Backend trả về HTTP 200 với danh sách rỗng, giao diện hiện trạng thái rỗng kèm gợi ý chụp lại, **không** hiện lỗi đỏ. Báo lỗi ở đây sẽ đẩy người dùng đi sửa một hệ thống đang chạy đúng."* |

---

## 5. Những điều TUYỆT ĐỐI không làm

1. **Không demo bằng ảnh chưa thử bao giờ.** Kể cả khi hội đồng đưa ảnh và mời thử — vẫn thử,
   nhưng phải nói trước: *"Đây là ảnh em chưa chạy bao giờ, kết quả có thể không như ảnh mẫu."*
   Nói trước một câu thì kết quả xấu là **dữ liệu**; không nói thì nó là **thất bại**.

2. **Không hứa "để em thử lại" quá 2 lần.** Lần một chấp nhận được, lần hai là giới hạn.
   Lần ba, hội đồng đã ngừng nghe. Đến giới hạn thì chuyển phương án dự phòng ngay.

3. **Không nói "bình thường nó chạy được".** Câu này không chứng minh được gì và nghe như biện hộ.
   Thay bằng phát biểu kiểm chứng được: *"Trên máy này, cấu hình này, em đã chạy thành công
   trước buổi bảo vệ; em xin phân tích nguyên nhân của lần chạy này."*

4. **Không nói vượt quá cái đang chạy trên màn hình.** Không tô hồng OCR: khi bị hỏi độ chính
   xác chuỗi, nói đúng số thật (A6 = 0,656, biển hai dòng không đạt) chứ không né. mAP detection
   0,983 là số công bố hợp lệ trên `best.pt`/test v3 — được đọc thẳng, kèm ghi rõ split và imgsz.

5. **Không im lặng khi máy đang xử lý.** Mỗi giây im lặng làm sự chậm trở nên đáng nghi.
   Luôn có sẵn nội dung để nói khi chờ.

6. **Không mở terminal đầy log lỗi lên màn chiếu.** Nếu buộc phải nhìn log, thu nhỏ cửa sổ
   hoặc chuyển màn hình, xử lý xong mới chiếu lại.

7. **Không sửa mã nguồn trực tiếp trong lúc bảo vệ.** Không bao giờ. Kể cả khi biết chắc chỉ
   sai một dòng.

8. **Không đổ lỗi cho máy, cho mạng, cho thư viện.** Nêu nguyên nhân kỹ thuật là phân tích;
   đổ lỗi là thái độ.

---

## 6. Kịch bản rút gọn 2 phút

Dùng khi hội đồng cắt thời gian. Chỉ giữ ba bước — mỗi bước tương ứng **một** luận điểm.
Bỏ hết phần còn lại không tiếc.

| # | Bước | Thời lượng | Chỉ nói đúng một ý |
|:-:|---|:-:|---|
| 0 | Câu mở đầu về `model_loaded` | 10 s | Trung thực về trạng thái mô hình (mục 2.0) |
| 1 | **Ảnh biển 2 dòng** | 45 s | "Đây là ca khó nhất — Laroca và cộng sự (VISAPP 2022) đo trên bộ **RodoSol-ALPR của Brazil** thấy chênh **48,6 điểm** giữa biển 1 dòng (94,3%) và biển 2 dòng (45,7%). Đó là số của Brazil, không phải Việt Nam, nhưng nó cho thấy độ khó của biển 2 dòng. Em xử lý bằng tách dòng rồi ghép ngang." |
| 2 | **Ảnh 3 biển số** + `curl /api/statistics` | 40 s | "Ba biển, nhưng thống kê tính **1 lượt** và **3 biển số**. Đây là lỗi thiết kế em phát hiện trong schema gốc và đã sửa bằng `source_job_id`." |
| 3 | **Lịch sử — mở modal chi tiết** | 25 s | "Lưu **cả** chuỗi OCR thô lẫn biển số đã chuẩn hoá — nhờ đó **đo được** đóng góp của bước hậu xử lý." |
| | **Tổng** (10+45+40+25) | **120 s = 2 ph** | |

**Chuẩn bị cho bản rút gọn:** mở sẵn **hai tab trình duyệt** trước khi vào phòng — `/` (Nhận dạng ảnh,
trang chủ) và `/history` (Lịch sử) — cộng **một cửa sổ terminal** đã `cd` về thư mục gốc để gọi
`curl http://localhost:8000/api/statistics` ở Bước 2. Không còn tab `/dashboard`: trang Tổng quan
đã gỡ khỏi giao diện.

**Nếu bị cắt còn 1 phút:** giữ **Bước 1** (biển 2 dòng). Đó là đóng góp kỹ thuật khó thay thế nhất.

---

## 7. Việc phải làm trước khi tài liệu này dùng được

Tài liệu viết theo hệ thống **hiện tại** (mô hình chính thức `best.pt` đã có). Việc phải hoàn tất trước buổi bảo vệ:

1. **Chuẩn bị bộ tệp trong `demo/`** — bảo đảm có ảnh và video mẫu. Đây là điều kiện cần của toàn bộ mục 2.
2. **Xác nhận `/health` báo `model_loaded: true` và `engine` chứa `yolo:best.pt`** vào **sáng ngày bảo vệ**.
3. **Chạy thử trọn kịch bản trong trạng thái tắt Wi-Fi**, ít nhất một lần.

---

## 8. Tài liệu liên quan

| Tài liệu | Dùng để |
|---|---|
| `docs/slides/10-defense-qa.md` | Câu hỏi và trả lời dự kiến của hội đồng |
| `docs/reports/06-ui-documentation.md` | Chi tiết các màn hình, 4 trạng thái, các quyết định thiết kế |
| `docs/manuals/api-documentation.md` | Đặc tả `POST /api/detect/frame` và toàn bộ endpoint |
| `README.md` mục 8 | Lệnh khởi động gốc |
| `frontend/README.md` | Lệnh frontend, cấu hình cổng và proxy, xử lý sự cố |
| `docs/reports/01-ocr-comparison.md` | Số liệu OpenALPR và phân tích biển 2 dòng |
| `docs/architecture/system-architecture.md` | Sơ đồ ER, `DetectionJob`, `source_job_id` |
