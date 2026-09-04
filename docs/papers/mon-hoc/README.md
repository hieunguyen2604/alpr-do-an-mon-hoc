# Bản đồ án môn học — Xử lý ảnh và ứng dụng

Thư mục này chứa **một quyển riêng**, không phải một phiên bản khác của quyển đồ
án tốt nghiệp. Hai quyển dùng chung số liệu đo và chung thư mục `figures/`,
nhưng có bố cục, cao độ trình bày và danh mục tài liệu tham khảo **độc lập**.

Quyển đồ án tốt nghiệp ở `docs/papers/` **không bị thay đổi** khi dựng quyển này.

## Khác gì quyển tốt nghiệp

Số của cột *Tốt nghiệp* đọc từ nhánh `main` (quyển đó không có ở nhánh này).

| | Tốt nghiệp | Môn học |
|---|---:|---:|
| Số chương | 6 | **5** |
| Số trang | 72 | **42** |
| Tài liệu tham khảo | 29 mục | **16 mục** |
| Phụ lục | 9 mục | **3 mục** |

**Trọng tâm dời chỗ.** Quyển tốt nghiệp phải bảo vệ một *đóng góp* trước hội
đồng — vì sao chọn công nghệ này chứ không phải công nghệ kia, kết quả đứng ở
đâu so với công trình đã công bố. Quyển này chỉ cần chứng minh làm chủ **nội
dung môn học**, nên phần bị cắt là bộ máy biện minh chứ không phải phần kỹ
thuật:

- **Cắt hẳn:** chương khảo sát và lựa chọn công nghệ (nén còn Bảng 1.2), mục
  công trình liên quan, mục đối chiếu với công trình đã công bố, mục bàn luận,
  bảng đối chiếu chỉ tiêu phi chức năng, và toàn bộ hệ mã FR/NFR.
- **Dựng dày lên:** các phép xử lý ảnh — CLAHE, lọc song phương, nội suy, HSV,
  băm tri giác dựa trên biến đổi cosine rời rạc — mỗi phép nêu cơ chế và **lý do
  chọn nó thay vì phương án hiển nhiên hơn** (mục 2.2). Toàn bộ khối xử lý ảnh
  vùng biển thành một mục riêng 10 trang (mục 3.4), và một mục riêng bóc tách
  đóng góp đo được của từng bước (mục 4.4).
- **Gộp lại:** backend, cơ sở dữ liệu, giao diện và Docker gộp còn mục 3.7,
  một trang.

**Giữ nguyên không đổi:** mọi con số đo được. Không số liệu nào bị làm tròn lại,
diễn giải lại hay bỏ đi để bản rút gọn trông đẹp hơn.

## Dựng lại

```bash
backend/.venv/Scripts/python.exe scripts/build_thesis.py
```

Thứ tự ghép khai báo ở `ORDER.txt` trong chính thư mục này, không dùng
`CHAPTER_FILENAMES` mặc định — đó là lý do `build_thesis.py` có hàm `read_order`.

Kết xuất PDF (Word điền số trang cho mục lục):

```bash
powershell -File scripts/export_thesis_pdf.ps1
```

Trên nhánh `do-an-mon-hoc`, cả hai lệnh đã đặt bản môn học làm mặc định nên không
cần tham số; chúng tự chép bản thành phẩm sang `nop/` dưới tên `01-do-an-mon-hoc.*`.

## Kiểm tra sau mỗi lần sửa

```bash
backend/.venv/Scripts/python.exe scripts/check_thesis_refs.py
```

Cần lưu ý giới hạn của công cụ này: nó chỉ bắt tham chiếu trỏ tới mục **không
tồn tại**. Một tham chiếu trỏ tới mục **có tồn tại nhưng sai mục** thì nó không
thấy — lỗi đó đã xảy ra thật một lần trong quyển này (mục 3.4.6 từng trỏ sang
4.5.2 thay vì 4.4.2). Cách bắt là đối chiếu số mục với **tiêu đề** của mục đó,
không chỉ đối chiếu sự tồn tại.
