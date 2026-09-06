# Thư mục dữ liệu Demo

Thư mục này được tổ chức thành các nhóm dữ liệu phân loại rõ ràng phục vụ chạy thử nghiệm và bảo vệ đề tài:

## 📁 Cấu trúc thư mục

```text
demo/
├── 1-line/          # 14 ảnh biển số 1 dòng (ô tô, xe tải, rơ-moóc, biển dài)
├── 2-line/          # 16 ảnh biển số 2 dòng (xe máy, ô tô vuông, biển quân sự, ngoại giao)
├── multi-plate/     # 9 ảnh bối cảnh nhiều xe / không có biển số
├── videos/          # 3 video giao thông thực tế
└── expected.json    # Bản ghi kết quả hệ thống trên 39 ảnh (mốc đối chiếu)
```

---

## 1. `demo/1-line/` — Biển số 1 dòng (14 ảnh)
Gồm các tình huống biển 1 dòng ô tô cá nhân, biển vàng kinh doanh, xe tải, xe buýt, rơ-moóc, biển ngoại giao dạng dài:
- `1dong-1.png` (`51G-316.91`), `1dong-2.png` (`51F-630.34`), `1dong-3.png` (`51G-513.32`)
- `bien-vang-kinh-doanh.jpg` (`29E-015.66`)
- `bien-ngoai-giao-ng.jpg` (`80-346-NG-68`), `ngoai-giao-commons-1.jpg` (`41-606-NG-10`)
- `o-to-72A07604.jpg` (`72A-076.04`), `canh-mot-bien-2.png` (`79A-187.68`)
- `ro-mooc.jpg` (`61R-023.09`), `xe-buyt.jpg` (`51B-0986`), `xe-tai.jpg` (`67C-108.15`)
- `xanh-85A00190.jpg` (`85A-001.90`), `xanh-86A00519.jpg` (`86A-005.19`), `xanh-nha-nuoc-commons.jpg` (`50A-004.24`)

---

## 2. `demo/2-line/` — Biển số 2 dòng (16 ảnh)
Gồm các tình huống biển 2 dòng xe máy, ô tô biển vuông, biển đỏ quân đội, biển xanh 2 dòng:
- `2dong-1.png` (`59K1-201.73`), `2dong-2.png` (`59K1-225.99`), `2dong-3.png` (`51P5-4578`)
- `bien-do-quan-doi.jpg` (`KV-6938`), `quan-doi-commons.jpg`
- `bien-xanh-nha-nuoc.jpg` (`51A-1987`), `bien-xanh-nha-nuoc-2.jpg` (`65A-004.50`), `xanh-80A04285.jpg` (`80A-042.85`)
- `bien-ngoai-giao-51ng.jpg` (`51NG16633`), `ngoai-giao-cd.jpg` (`NC01`), `ngoai-giao-ng-651-01.png`
- `canh-mot-bien-1.jpg` (`52Z2-0513`), `canh-mot-bien-3.png` (`51A-8066`)
- `vang-50F01690.jpg` (`50F-016.90`), `vang-61C15282.jpg` (`61C-152.82`), `vang-79E00392.jpg` (`79B-003.92`)

---

## 3. `demo/multi-plate/` — Bối cảnh nhiều biển & Không có biển (9 ảnh)
- `nhieu-bien-1.png`, `nhieu-bien-2.png`, `nhieu-bien-3.png`
- `canh-nhieu-bien-1.jpg` $\rightarrow$ `canh-nhieu-bien-5.png`
- `khong-co-bien-so.jpg` (Ca âm tính)

---

## 4. `demo/videos/` — Video kiểm thử (3 tệp)
- `demo-video.mp4` (1.5 MB): Video mẫu tiêu chuẩn.
- `demo-video-cac-loai-bien.mp4` (3.2 MB): Video chứa đa dạng các loại biển số.
- `demo-video-giao-thong.mp4` (3.0 MB): Video bối cảnh đường phố lưu lượng cao.

---

## 5. Chạy kiểm thử tự động

Chạy 39 ảnh qua **đúng đường ống của phiên bản bàn giao** rồi đối chiếu với `expected.json`:

```bash
backend/.venv/Scripts/python scripts/demo_test.py
```

Không cần chạy máy chủ — script tự nạp mô hình (mất khoảng 5 giây) rồi chạy
khoảng 470 ms mỗi ảnh. Nó in số ảnh khớp theo từng nhóm và **chỉ rõ trường nào
lệch** ở những ảnh không khớp.

`expected.json` là **bản ghi đầu ra của hệ thống**, không phải nhãn do người gán:
nó chứa cả mảnh rác mà bộ phát hiện bắt nhầm (`'MI'`, `'HN'`) và các ô trống ở
biển không đọc được. Vì vậy "khớp" ở đây nghĩa là *hệ thống vẫn hành xử như lúc
ghi nhận*, không phải *đọc đúng biển*. Muốn ghi lại mốc theo lượt chạy hiện tại:

```bash
backend/.venv/Scripts/python scripts/demo_test.py --ghi-lai
```
