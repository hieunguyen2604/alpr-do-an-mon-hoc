# Frontend — Hệ thống nhận dạng biển số xe Việt Nam

Giao diện web của hệ thống ALPR, xây dựng bằng **React 18 + Vite 5 + TypeScript 5 + TailwindCSS 3**.

Đây là phần người dùng nhìn thấy, nên **toàn bộ nhãn nút, tiêu đề và thông báo đều viết bằng tiếng Việt**.
Ngược lại, **mã nguồn — tên biến, tên hàm, comment, docstring — viết hoàn toàn bằng tiếng Anh** theo quy ước của dự án.

---

## 1. Yêu cầu môi trường

| Thành phần | Yêu cầu | Ghi chú |
|---|---|---|
| Node.js | **≥ 18** | Vite 5 dùng API chỉ có từ Node 18. Node 14/16 sẽ **thất bại** ngay ở bước `npm install` |
| npm | ≥ 9 | Đi kèm Node 18+ |
| Backend | đang chạy tại `http://localhost:8000` | Bắt buộc, xem mục 5 |
| Trình duyệt | Chrome / Edge / Firefox bản mới | Không còn yêu cầu `navigator.mediaDevices` — trang Webcam đã gỡ 2026-07-20 |

Ràng buộc phiên bản đã được khai báo trong `package.json`:

```json
"engines": { "node": ">=18" }
```

### Chọn phiên bản Node bằng nvm

Máy phát triển hiện dùng **nvm** để quản lý nhiều phiên bản Node song song.
Phiên bản chốt cho dự án được ghi trong tệp `.nvmrc`:

```
18.20.8
```

Chuyển sang đúng phiên bản trước khi làm bất cứ việc gì khác:

```bash
nvm use 18.20.8
node --version        # phải hiện v18.20.8
```

Nếu chưa cài phiên bản đó:

```bash
nvm install 18.20.8
nvm use 18.20.8
```

> **Node 20 / 22 cũng chạy được.** Dự án đã được kiểm chứng cả trên Node v20.19.6.
> `.nvmrc` ghi phiên bản chốt đã kiểm thử, không phải phiên bản duy nhất được phép.

Nếu chưa có nvm trên Windows, tải **nvm-windows** tại
<https://github.com/coreybutler/nvm-windows/releases>, hoặc cài trực tiếp bản **LTS**
tại <https://nodejs.org/>.

---

## 2. Cài đặt và chạy

### Bước 1 — Cài gói phụ thuộc

```bash
cd frontend
nvm use 18.20.8
npm install
```

### Bước 2 — Cấu hình biến môi trường (tuỳ chọn)

```bash
cp .env.example .env.local
# Windows PowerShell:
Copy-Item .env.example .env.local
```

Bước này **có thể bỏ qua** khi phát triển: giá trị mặc định trong mã nguồn đã đúng
cho trường hợp backend chạy tại `http://localhost:8000`.

### Bước 3 — Chạy môi trường phát triển

```bash
npm run dev
```

Giao diện mở tại <http://localhost:5173>.

> Cổng 5173 được đặt `strictPort: true`. Nếu cổng đã bị chiếm, Vite **báo lỗi và dừng**
> thay vì lặng lẽ nhảy sang cổng khác — để cấu hình proxy ghi trong tài liệu luôn khớp thực tế.

### Bước 4 — Build bản phát hành

```bash
npm run build       # chạy tsc --noEmit rồi build vào dist/
npm run preview     # xem thử bản build tại http://localhost:4173
```

`npm run build` **kiểm tra kiểu trước khi build**. Một lỗi TypeScript sẽ làm hỏng lệnh build,
không lọt ra trình duyệt.

Kết quả build nằm trong `dist/` — chỉ gồm tệp tĩnh (HTML, JS, CSS), có thể phục vụ bằng
Nginx, Caddy hoặc bất kỳ web server tĩnh nào.

### Danh sách script

| Lệnh | Mục đích |
|---|---|
| `npm run dev` | Dev server kèm hot reload tại cổng 5173 |
| `npm run build` | Kiểm tra kiểu rồi build bản phát hành vào `dist/` |
| `npm run preview` | Phục vụ thử thư mục `dist/` như môi trường thật |
| `npm run lint` | Kiểm tra quy chuẩn mã nguồn bằng ESLint (`--max-warnings 0`) |
| `npm run typecheck` | Chỉ kiểm tra kiểu TypeScript, không sinh tệp |

---

## 3. Cấu trúc thư mục

```
frontend/
├── index.html                  # Điểm vào HTML của Vite
├── package.json                # Gói phụ thuộc và script
├── vite.config.ts              # Proxy /api /files /health, cổng 5173, alias @
├── tsconfig.json               # TypeScript: strict + noUncheckedIndexedAccess
├── tsconfig.node.json          # Cấu hình riêng cho tệp chạy trên Node (vite.config.ts)
├── tailwind.config.js          # Bảng màu, token giao diện
├── postcss.config.js           # Tailwind + autoprefixer
├── .eslintrc.cjs               # Quy tắc ESLint
├── .nvmrc                      # Phiên bản Node chốt cho dự án
├── .env.example                # Mẫu biến môi trường
├── dist/                       # Kết quả build (không commit)
│
└── src/
    ├── main.tsx                # Gắn React vào DOM, cài router
    ├── App.tsx                 # Bảng định tuyến 3 trang: / (ảnh), /video,
    │                           # /history; đường dẫn lạ → về /
    ├── index.css               # Directive Tailwind + biến màu + lớp tiện ích chung
    ├── vite-env.d.ts           # Khai báo kiểu cho import.meta.env
    │
    ├── types/
    │   └── index.ts            # Interface khớp schema Pydantic của backend (snake_case).
    │                           # Statistics / StatisticsQuery / HealthStatus /
    │                           # InputTypeBreakdown được GIỮ LẠI có chủ đích: chúng là
    │                           # bản sao hợp đồng của GET /api/statistics và GET /health —
    │                           # hai endpoint vẫn phục vụ dù trang Dashboard đã gỡ
    │                           # (lý do ghi ngay trong tệp)
    │
    ├── services/
    │   └── api.ts              # Client axios: baseURL, timeout, X-Request-ID,
    │                           # chuẩn hoá lỗi sang thông báo tiếng Việt,
    │                           # và các hàm gọi endpoint. Đã xoá theo hai lần thu gọn
    │                           # phạm vi 2026-07-20: detectFrame (cùng trang Webcam),
    │                           # getStatistics và getHealth (cùng trang Tổng quan).
    │                           # Ba endpoint backend tương ứng vẫn tồn tại
    │
    ├── hooks/
    │   ├── useDebounce.ts      # Hoãn phát request khi người dùng đang gõ
    │   └── useJobPolling.ts    # Hỏi tiến độ tác vụ video, tự dừng ở trạng thái cuối
    │
    ├── lib/
    │   ├── constants.ts        # Nhãn tiếng Việt, giới hạn tệp, ngưỡng độ tin cậy
    │   ├── format.ts           # Định dạng số, phần trăm, ngày giờ theo chuẩn Việt Nam
    │   └── cn.ts               # Ghép chuỗi class có điều kiện
    │
    ├── utils/
    │   └── format.ts           # Re-export tương thích, đã @deprecated → dùng @/lib/format
    │
    ├── components/
    │   ├── Layout.tsx          # Sidebar 3 mục (ảnh → video → lịch sử), header,
    │   │                       # vùng nội dung
    │   ├── StateViews.tsx      # PageSection, LoadingState, InlineError dùng chung
    │   ├── ui/                 # 15 thành phần nền: Button, Card, Table, Modal,
    │   │                       # Pagination, ConfidenceBar, PlateChip, EmptyState,
    │   │                       # ErrorState, Skeleton, ProgressBar, FileDropzone…
    │   ├── detection/
    │   │   ├── image/          # Dropzone, overlay bounding box, thẻ kết quả, tải tệp
    │   │   └── video/          # Dropzone, bảng tiến độ tác vụ, bảng kết quả
    │   │                       # (thư mục webcam/ đã xoá 2026-07-20 cùng trang Webcam)
    │   └── history/            # Bộ lọc, bảng, modal chi tiết, hộp thoại xoá,
    │                           # useHistoryQuery (lưu trạng thái lọc lên URL)
    │                           # (thư mục dashboard/ đã xoá 2026-07-20
    │                           #  cùng trang Tổng quan)
    │
    └── pages/
        ├── ImageDetection.tsx  # Tải ảnh và nhận dạng — TRANG CHỦ (/)
        ├── VideoDetection.tsx  # Tải video, theo dõi tiến độ nền (/video)
        └── History.tsx         # Tra cứu, lọc, phân trang, xem chi tiết, xoá, xuất CSV (/history)
```

> **Hai thay đổi phạm vi trong ngày 2026-07-20.** Giao diện được thu gọn hai lần liên tiếp,
> nay còn **3 trang**. Mã của cả hai trang đã gỡ **còn trong lịch sử git**.
>
> | # | Trang đã gỡ | Đã xoá khỏi cây thư mục | Năng lực còn lại ở backend |
> |---|---|---|---|
> | 1 | **Webcam** | `pages/WebcamDetection.tsx`, `components/detection/webcam/`, hàm `detectFrame` | `POST /api/detect/frame` vẫn phục vụ, vẫn có kiểm thử |
> | 2 | **Tổng quan (Dashboard)** | `pages/Dashboard.tsx`, cả thư mục `components/dashboard/`, `hooks/useApi.ts`, hàm `getStatistics` và `getHealth`, gói npm `recharts` | `GET /api/statistics` và `GET /health` vẫn phục vụ, vẫn có kiểm thử |
>
> Bảng định tuyến hiện hành (`src/App.tsx`):
>
> | Route | Trang |
> |---|---|
> | `/` (index) | `ImageDetection` — trang chủ |
> | `/video` | `VideoDetection` |
> | `/history` | `History` |
> | `*` | chuyển hướng về `/` |
>
> Gỡ `recharts` cùng trang Tổng quan làm **gói tải về giảm từ ~730 KB xuống 328,8 KB
> (giảm 55%)** — đo ngày **2026-07-20**; build thành công trong 2,14 s, `tsc --noEmit` 0 lỗi,
> ESLint sạch.

### Vai trò từng tầng

| Tầng | Trách nhiệm | Không được làm |
|---|---|---|
| `pages/` | Ghép thành phần, giữ trạng thái của trang, xử lý đủ 4 trạng thái loading / empty / error / success | Gọi `axios` trực tiếp |
| `components/` | Hiển thị. Nhận dữ liệu qua props, báo sự kiện ra ngoài | Tự gọi API |
| `hooks/` | Vòng đời bất đồng bộ dùng lại được | Chứa markup |
| `services/api.ts` | Điểm **duy nhất** chạm tới HTTP | Ném lỗi thô ra giao diện |
| `types/` | Bản sao kiểu của schema backend | Đổi tên trường sang camelCase |

> **Quy ước tên trường.** Toàn bộ interface dùng `snake_case` **giống hệt JSON mà API trả về**.
> Không có lớp chuyển đổi sang camelCase. Lý do: khi backend đổi schema, TypeScript báo lỗi
> **lúc biên dịch**; còn nếu có lớp chuyển đổi, trường bị đổi tên sẽ âm thầm thành `undefined`
> lúc chạy — kiểu lỗi khó truy vết hơn nhiều.

---

## 4. Biến môi trường

Chỉ biến có tiền tố `VITE_` mới được đưa vào bundle trình duyệt. Đây là các biến **build-time**:
đổi giá trị thì phải khởi động lại dev server hoặc build lại.

| Biến | Mặc định | Ý nghĩa |
|---|---|---|
| `VITE_API_URL` | rỗng | **Origin** của backend. Để rỗng ⇒ mọi request là same-origin tương đối và đi qua proxy của Vite |
| `VITE_API_BASE_URL` | rỗng | Tên cũ, vẫn được đọc để tương thích. `VITE_API_URL` được ưu tiên nếu cả hai cùng có |
| `VITE_API_TIMEOUT_MS` | `60000` | Thời gian chờ tối đa cho một request (ms). Suy luận chạy trên CPU nên **không đặt quá thấp** |

Cách xử lý trong `src/services/api.ts`:

* Giá trị được cắt bỏ dấu `/` thừa ở cuối, và **cắt luôn hậu tố `/api`** nếu có.
  Lý do: biến này khai báo *origin*, còn tiền tố `/api` được ghép riêng — vì `GET /health`
  cố ý **nằm ngoài** tiền tố đó. Nhờ vậy đặt `VITE_API_URL=http://host:8000/api` vẫn chạy đúng.
* `VITE_API_TIMEOUT_MS` không đọc được hoặc ≤ 0 ⇒ quay về mặc định `60000`,
  chứ **không** tắt timeout (một request treo vô hạn còn tệ hơn).

Ví dụ khi backend chạy trên máy khác:

```dotenv
# .env.local
VITE_API_URL=http://192.168.1.50:8000
VITE_API_TIMEOUT_MS=90000
```

> Đặt `VITE_API_URL` **không rỗng** sẽ khiến trình duyệt gọi thẳng sang origin đó,
> bỏ qua proxy của Vite. Khi ấy backend phải bật CORS cho `http://localhost:5173`.

---

## 5. Cấu hình proxy sang backend

Khi `VITE_API_URL` để rỗng (mặc định), trình duyệt chỉ nói chuyện với **một origin duy nhất**
là `http://localhost:5173`. Vite chuyển tiếp ba tiền tố đường dẫn sang backend
(khai báo trong `vite.config.ts`):

| Tiền tố | Chuyển tới | Vì sao cần |
|---|---|---|
| `/api` | `http://localhost:8000` | Toàn bộ REST API: nhận dạng, tác vụ, lịch sử. *(Backend còn phục vụ `GET /api/statistics`; từ 2026-07-20 không trang nào của giao diện gọi nó nữa — xem mục 3.)* |
| `/files` | `http://localhost:8000` | Ảnh gốc và ảnh biển số đã cắt. Đây chính là đường dẫn trả về trong `image_path` / `plate_image_path`. **Thiếu mục này thì mọi ảnh kết quả đều hỏng** |
| `/health` | `http://localhost:8000` | Endpoint sức khoẻ nằm ở gốc, không dưới `/api`, nên cần mục riêng. Giữ lại sau khi gỡ trang Tổng quan: không trang nào của giao diện gọi nó nữa, nhưng mục proxy này cho phép kiểm tra backend ngay qua cổng 5173 (`curl http://localhost:5173/health`) — hữu ích khi cần xác định lỗi nằm ở proxy hay ở backend |

```ts
// vite.config.ts (trích)
server: {
  port: 5173,
  strictPort: true,
  proxy: {
    '/api':    { target: 'http://localhost:8000', changeOrigin: true },
    '/files':  { target: 'http://localhost:8000', changeOrigin: true },
    '/health': { target: 'http://localhost:8000', changeOrigin: true },
  },
},
```

Lợi ích của cách này:

1. **Không cần CORS** trong môi trường phát triển.
2. Bản build production đặt sau reverse proxy vẫn dùng **đúng các tiền tố đó**,
   nên mã nguồn không phải phân biệt dev/prod.
3. Không có hostname nào bị hard-code — triển khai là việc **cấu hình**, không phải build lại.

### Đổi cổng backend

Sửa `target` ở cả ba mục trong `vite.config.ts`, rồi khởi động lại `npm run dev`.
Vite **không** nạp lại cấu hình proxy khi đang chạy.

---

## 6. Xử lý sự cố thường gặp

### `npm install` thất bại, log nhắc tới cú pháp lạ hoặc `Unexpected token`

Node quá cũ. Kiểm tra:

```bash
node --version
```

Không phải v18/v20/v22 ⇒ chạy `nvm use 18.20.8` rồi cài lại. Nếu `node_modules` đã lỡ được
tạo bằng Node cũ, xoá sạch trước khi cài lại:

```bash
rm -rf node_modules package-lock.json    # PowerShell: Remove-Item -Recurse -Force node_modules
npm install
```

### Giao diện mở được nhưng mọi trang báo "Không kết nối được máy chủ"

Backend chưa chạy. Kiểm tra bằng chính đường dẫn mà proxy dùng:

```bash
curl http://localhost:8000/health
```

Phải trả về `{"status": ..., "database_connected": ..., "model_loaded": ...}`.
Nếu không có phản hồi, khởi động backend trước rồi bấm **Tải lại** trên giao diện —
không cần khởi động lại dev server.

> Frontend vẫn hiển thị đầy đủ khi backend chưa chạy, chỉ khác là mỗi trang hiện trạng thái lỗi
> kèm nút thử lại. Đây là hành vi đúng, không phải lỗi của frontend.

### Ảnh kết quả và ảnh biển số hiện ô trống / biểu tượng ảnh vỡ

Mục proxy `/files` bị thiếu hoặc sai `target` trong `vite.config.ts`.
Kiểm tra nhanh bằng cách mở thẳng một đường dẫn ảnh trong tab mới:
`http://localhost:5173/files/...` — nếu 404 mà `http://localhost:8000/files/...` lại 200
thì chắc chắn là lỗi proxy.

### `Port 5173 is already in use`

Cổng đang bị một tiến trình khác chiếm (thường là một `npm run dev` cũ chưa tắt).

```powershell
netstat -ano | findstr :5173
taskkill /PID <pid> /F
```

Không nên đổi cổng: `strictPort: true` cố ý báo lỗi để cấu hình proxy trong tài liệu
luôn khớp thực tế.

### Video xử lý mãi không xong

Bình thường. Suy luận chạy trên CPU: video 60 giây cần khoảng 200 giây.
Trang video **không** chờ đồng bộ mà nhận `job_id` rồi hỏi tiến độ định kỳ,
nên có thể rời trang và quay lại sau. Nếu thanh tiến độ đứng yên quá lâu, bấm
**Làm mới** trong bảng tiến độ để hỏi ngay một lần.

### Bảng lịch sử trống dù vừa nhận dạng xong

Kiểm tra bộ lọc: khi có bộ lọc đang áp dụng, trang hiện thông báo
*"Không có bản ghi nào khớp bộ lọc"* kèm nút **Xoá bộ lọc**. Trạng thái này khác hẳn
*"Chưa có dữ liệu nhận dạng"* (hệ thống chạy đúng nhưng chưa có dữ liệu nào).

Lưu ý bộ lọc được lưu trên URL, nên tải lại trang **không** xoá bộ lọc.

### CSV xuất ra mở bằng Excel bị lỗi dấu tiếng Việt

Không nên xảy ra: backend xuất UTF-8 **có BOM** đúng cho Excel. Nếu vẫn lỗi,
nhiều khả năng tệp đã bị mở bằng công cụ khác rồi lưu đè mất BOM.

### `npm run build` báo lỗi kiểu nhưng `npm run dev` vẫn chạy

Đúng như thiết kế. Vite dev server chỉ **biên dịch bỏ kiểu** (transpile-only), còn
`npm run build` chạy `tsc --noEmit` trước. Chạy `npm run typecheck` trong lúc phát triển
để phát hiện sớm.

---

## 7. Ghi chú về trạng thái hiện tại

* **Cả 3 trang đã nối vào API thật** và đã được xác minh chạy với backend tại
  `http://localhost:8000`. `npm run typecheck` sạch, `npm run lint` sạch, `npm run build`
  thành công trong 2,14 s. (Trang Webcam và trang Tổng quan đều đã gỡ 2026-07-20
  theo hai thay đổi phạm vi — xem ghi chú ở mục 3.)
* Kích thước gói tải về sau khi gỡ trang Tổng quan: **328,8 KB** (trước đó ~730 KB —
  giảm 55%, chủ yếu nhờ bỏ thư viện biểu đồ `recharts`). Đo ngày **2026-07-20**.
* Backend chạy **mô hình thật** (`models/best.pt` — YOLO11n + PaddleOCR, cấu hình qua
  `ALPR_MODEL_PATH`). Nếu không nạp được mô hình, backend dùng `UnavailablePipeline`
  — trả lỗi rõ ràng thay vì kết quả giả lập, nên người dùng vẫn thấy ngay là hệ thống
  không sẵn sàng. Trạng thái `model_loaded` vẫn đọc được qua `GET /health`; từ 2026-07-20
  **không còn màn hình nào hiển thị nó** (thẻ cảnh báo cũ nằm ở trang Tổng quan đã gỡ).
* Nút **Huỷ tác vụ** ở trang video đang **bị vô hiệu hoá** vì API chưa có endpoint huỷ
  (xem mục Hạn chế trong `docs/reports/06-ui-documentation.md`).

Tài liệu giao diện đầy đủ — sơ đồ điều hướng, mô tả từng màn hình, bảng đối chiếu yêu cầu
chức năng — nằm ở [`docs/reports/06-ui-documentation.md`](../docs/reports/06-ui-documentation.md).
