# PHỤ LỤC

## Phụ lục I. Mã vùng biển số

**Bảng I.1.** 81 mã vùng biển số đang sử dụng, dải 11–99

| 11 | 12 | 14 | 15 | 16 | 17 | 18 | 19 | 20 |
|---|---|---|---|---|---|---|---|---|
| 21 | 22 | 23 | 24 | 25 | 26 | 27 | 28 | 29 |
| 30 | 31 | 32 | 33 | 34 | 35 | 36 | 37 | 38 |
| 39 | 40 | 41 | 43 | 47 | 48 | 49 | 50 | 51 |
| 52 | 53 | 54 | 55 | 56 | 57 | 58 | 59 | 60 |
| 61 | 62 | 63 | 64 | 65 | 66 | 67 | 68 | 69 |
| 70 | 71 | 72 | 73 | 74 | 75 | 76 | 77 | 78 |
| 79 | 80 | 81 | 82 | 83 | 84 | 85 | 86 | 88 |
| 89 | 90 | 92 | 93 | 94 | 95 | 97 | 98 | 99 |

Dải 11–99 có 89 số; **8 mã chưa cấp**: `13`, `42`, `44`, `45`, `46`, `87`, `91`, `96`. Từ 01/7/2025 cả nước còn **34 tỉnh, thành phố**, và ký hiệu sau hợp nhất **giữ toàn bộ ký hiệu của các địa phương được hợp nhất** — nên số mã vẫn nhiều hơn số tỉnh. Danh sách này là nguồn sinh ra nhóm bắt mã tỉnh trong biểu thức kiểm tra hợp lệ (mục 4.6.5), nên nó không thể lệch khỏi mã đang chạy.

---

## Phụ lục II. Ghi công giấy phép bộ dữ liệu

Bộ dữ liệu hợp nhất từ bảy nguồn công khai. **Năm bộ phát hành theo giấy phép CC BY 4.0**, giấy phép này **bắt buộc ghi công tác giả**: Roboflow `school-fuhih/vietnamese-license-plate-tptd0`, `traffic-camera/vietnam-license-plate-hayn8`, `eric-nguyen-knfxn/vietnam-license-plate-curhr`, `demo-tracking/license-plate-vietnam-car`, và `tran-ngoc-xuan-tin-k15-hcm-dpuid/vietnam-license-plate-h8t3n`. Bộ `cuong-ta-ulxex/vietnamese-car-license-plate` được người đăng tự khai Public Domain — đồ án **không khẳng định** điều đó vì ảnh nguồn có dấu hiệu là ảnh báo chí. Bộ `hoanglvuit/Vietnam_License_Plate_Segment_Datasets` trên HuggingFace **chưa xác nhận được giấy phép** và đóng góp 28,91% ngữ liệu; đây là rủi ro pháp lý được nêu ở mục 6.2 chứ không phải chi tiết bỏ qua được.

---

## Phụ lục III. Nơi tra cứu phần chi tiết

Các bảng tra cứu dưới đây không lặp lại trong quyển vì chúng đã nằm trong thân bài hoặc trong bộ tài liệu đi kèm.

| Nội dung | Nơi tra cứu |
|---|---|
| Siêu tham số huấn luyện đầy đủ | Mục 4.5.1; nguyên văn tại `runs/final-640-v3/args.yaml` |
| Quy mô và tổ chức mã nguồn | Mục 4.2.2 |
| Kết quả kiểm thử theo nhóm | Mục 5.7; chi tiết tại `docs/reports/07-testing-report.md` |
| Danh sách endpoint và cấu hình triển khai | Mục 4.7.4 và 4.9; OpenAPI tự sinh tại `/docs` |
| Đặc tả 34 yêu cầu chức năng và chỉ tiêu phi chức năng | `docs/00-requirements/` |
| Chỉ mục báo cáo đo dạng JSON chống lưng từng con số | `docs/reports/README.md` |
| Hướng dẫn cài đặt và vận hành | `docs/manuals/installation-guide.md` |
