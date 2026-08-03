# Thẩm định bản đề xuất cải thiện quyển đồ án

**Ngày lập:** 2026-08-03 · **Trạng thái:** đề xuất, **chưa thi hành** — chờ người thực hiện duyệt từng mục
**Đối tượng thẩm định:** bản góp ý gồm 5 điểm cải thiện và một công thức phân bổ 60–80 trang

Mọi kết luận dưới đây **đã kiểm chứng trên kho mã và trên tệp `.docx`/`.pdf` thật**, không suy đoán từ trí nhớ.

---

## 1. Tóm tắt phán quyết

| # | Đề xuất | Phán quyết | Chi phí |
|:--:|---|---|---|
| 1 | Bổ sung biểu đồ huấn luyện vào §4.5.2 | ✅ **Nhận** — dữ liệu và cả biểu đồ đã có sẵn | Thấp |
| 2 | Cập nhật số trang trong Danh mục hình/bảng | ✅ **Nhận, nhưng cách làm phải khác** | Trung bình |
| 3 | Thống nhất mốc thời gian bìa vs benchmark | ❌ **Bác** — không phải lỗi | — |
| 4 | Chuyển E1/E2/E3 xuống Chương 6 | ⚠️ **Nhận một nửa** — tách, không chuyển hẳn | Thấp |
| 5 | Kiểm lỗi font icon khi xuất PDF | ❌ **Bác** — đã kiểm, không có lỗi | — |
| 6 | Phân bổ 60–80 trang cho Chương 1–6 | ⚠️ **Nhận phần lớn, một mục mâu thuẫn** | Cao |

---

## 2. Điểm 1 — Biểu đồ huấn luyện · ✅ NHẬN

**Kiểm chứng.** Quyển hiện thừa nhận thiếu ở ba chỗ:

- `ch4:224` — *"Ba hình đường cong (loss, mAP, precision/recall theo epoch) dự kiến sinh từ `runs/final-640-v3/results.csv` — **cả ba hiện chưa sinh**"*
- `ch5:98` — ba hình chẩn đoán khối phát hiện chưa sinh
- `ch5:448` — bốn hình minh hoạ ca lỗi chưa sinh

**Điều bản góp ý chưa biết: nguyên liệu không những có, mà biểu đồ đã được dựng sẵn.** Thư mục `runs/final-640-v3/` chứa:

```
results.csv                      # dữ liệu thô theo epoch
results.png                      # loss + mAP + precision/recall — Ultralytics tự sinh
BoxPR_curve.png                  # đường cong Precision–Recall
BoxF1_curve.png  BoxP_curve.png  BoxR_curve.png
confusion_matrix.png  confusion_matrix_normalized.png
```

Nghĩa là việc này **không phải "chạy script để tạo biểu đồ"** mà là **chèn ảnh đã có** — rẻ hơn nhiều so với ước lượng trong bản góp ý.

**Việc phải làm:** chèn 3 ảnh vào §4.5.2 (đường cong huấn luyện) và 2 ảnh vào §5.4 (PR + ma trận nhầm lẫn), viết chú thích, xoá ba dòng *"chưa sinh"*. Bốn hình minh hoạ ca lỗi ở `ch5:448` **vẫn phải giữ nhãn "chưa sinh"** vì chúng cần chọn tay từng ca — không có sẵn.

> ⚠️ **Xung đột với mục tiêu số trang.** Năm ảnh thêm vào tốn khoảng **3–4 trang**. Nếu vẫn theo đuổi mốc 60–80 trang thì phải bù lại ở chỗ khác. Đây là đánh đổi có thật, cần quyết định cùng lúc chứ không tách rời.

---

## 3. Điểm 2 — Số trang trong danh mục · ✅ NHẬN, nhưng cách làm phải khác

**Kiểm chứng.** Đúng: **53 ô** trong Danh mục hình vẽ và Danh mục bảng biểu đang mang ký hiệu `—`.

**Chỗ bản góp ý sai về cách khắc phục.** Góp ý viết *"nhớ dùng tính năng cập nhật số trang trong Word"*. Việc đó **không chạy được** với cấu trúc hiện tại:

- Mục lục (E) là **trường TOC thật** của Word → cập nhật được bằng F9.
- Danh mục hình (F) và bảng (G) là **bảng Markdown thường** do `scripts/gen_front_matter_lists.py` sinh ra → Word không biết chúng là danh mục, F9 không đụng tới. Điền tay 53 ô, và **mọi lần dựng lại quyển là mất sạch**.

**Hai phương án thật:**

| | Cách | Ưu | Nhược |
|---|---|---|---|
| A | Đổi F và G thành **trường TOC theo chú thích** (`TOC \c "Hình"`, `TOC \c "Bảng"`) | Word tự điền và tự cập nhật; không bao giờ lệch | Phải gán style *Caption* cho 12 chú thích hình và 41 chú thích bảng khi xuất |
| B | Điền tay sau lần phân trang cuối | Không đổi công cụ | Mất khi dựng lại; dễ quên |

**Khuyến nghị: phương án A.** Nó biến 53 ô sai-được thành 53 ô không-thể-sai, cùng lối đã dùng cho mục lục.

---

## 4. Điểm 3 — Mốc thời gian · ❌ BÁC

**Bản góp ý nêu:** trang bìa ghi *"Tháng 9 năm 2026"* nhưng benchmark ghi *03/08/2026* → cần thống nhất.

**Đây không phải mâu thuẫn.** Hai con số trả lời hai câu hỏi khác nhau:

- **24/09/2026** — ngày **nộp quyển**, khớp đề cương đã đăng ký (16/07 – 24/09/2026), có ở trang bìa, lời cam đoan và lời cảm ơn.
- **03/08/2026** — ngày **chạy phép đo**.

Một quyển nộp tháng 9 báo cáo phép đo tháng 8 là **đúng và bình thường**. Sửa cho "thống nhất" sẽ tạo ra một lỗi thật: hoặc bìa sai ngày nộp, hoặc phép đo bị ghi lùi ngày — cái sau là gian lận số liệu.

**Không làm gì.** Nếu muốn chặt chẽ hơn, chỉ nên rà **thì của câu**: vài khối *"trạng thái tại thời điểm viết"* nói về bản thảo chứ không về hệ thống — nhưng đó là việc khác, không phải mốc thời gian.

---

## 5. Điểm 4 — E1/E2/E3 · ⚠️ NHẬN MỘT NỬA

**Kiểm chứng.** §3.6.2 (`ch3:236`) hiện có: ba thí nghiệm cô lập biến E1/E2/E3, bảng chi phí ước tính, và câu *"không được thực hiện vì tổng khoảng 33 giờ CPU vượt ngân sách còn lại"*.

**Chỗ bản góp ý đúng.** Ba thí nghiệm chưa chạy đúng là chất liệu của hướng phát triển, và đưa xuống Chương 6 thì Chương 3 gọn hơn.

**Chỗ phải cẩn thận.** §3.6 trình bày phép so sánh 416 ↔ 640 và kết luận **không quy kết được nguyên nhân** vì ba biến đổi đồng thời. §3.6.2 chính là **câu trả lời cho câu hỏi mà §3.6 vừa đặt ra**: *"vậy làm sao để biết biến nào gây ra?"* Bê nguyên nó đi làm §3.6 mất vế sau và trở thành một lời than không có lối ra — yếu hơn hiện tại.

**Khuyến nghị: tách, không chuyển.**

- Giữ ở §3.6.2 **hai câu**: cần một ma trận cô lập biến, chi phí ước tính ~33 giờ CPU, chưa chạy → trỏ §6.4.
- Đưa **bảng E1/E2/E3 đầy đủ** xuống §6.4 thành một hướng phát triển có chi phí định lượng.

Lợi cả hai: Chương 3 vẫn khép được lập luận, Chương 6 có thêm một hướng cụ thể thay vì chung chung.

---

## 6. Điểm 5 — Font icon · ❌ BÁC (đã kiểm)

**Kiểm chứng trên tệp thật.** Bản `.docx` chứa 129 icon: 39 ⚠, 40 ✅, 24 ❌, 15 🟡, 8 ⬜, 2 📄, 1 🎯.

Bản `.pdf` **nhúng đầy đủ hai font cần thiết**:

```
BCDHEE+SegoeUIEmoji
BCEGEE+SegoeUISymbol
```

Nghĩa là icon **đã hiển thị đúng**, không có ô vuông. Không cần làm gì.

**Một rủi ro khác, có thật hơn:** nếu in **đen trắng**, ✅ / ❌ / 🟡 mất phân biệt màu. Điều này **không gây mất nghĩa** vì trong toàn quyển chúng luôn đi kèm chữ (*"✅ đạt"*, *"❌ không đạt"*, *"🟡 chỉ đạt sàn"*) — đã kiểm quy ước ở bảng đối chiếu NFR. Đề nghị: in thử **một trang** bảng NFR trước khi in cả quyển.

---

## 7. Điểm 6 — Phân bổ 60–80 trang

### 7.1. Khoảng cách hiện tại

Ước lượng theo mật độ đo được (~2,9 nghìn ký tự mỗi trang in):

| Chương | Đề xuất | Hiện tại | Chênh |
|---|---:|---:|---:|
| 1. Giới thiệu | 5–7 | ~9 | −2 |
| 2. Cơ sở lý thuyết | 10–15 | ~20 | −5 |
| 3. Khảo sát và lựa chọn | 5–8 | ~10 | −2 |
| **4. Thiết kế và cài đặt** | **15–20** | **~33** | **−13** |
| 5. Thực nghiệm và đánh giá | 15–20 | ~20–28 | −0…−8 |
| **6. Kết luận** | **2–3** | **~10** | **−7** |
| **Tổng thân bài** | **60–80** | **~102** | **−22…−42** |

*(Chương 5 đang trong lượt ép ký tự nên còn dao động.)*

### 7.2. Chỗ bản góp ý đúng, và rất đúng

**Chương 4 phải cắt tiếp — đây là mục lớn nhất và có căn cứ nhất.** 33 trang cho thiết kế + cài đặt là quá nhiều với một quyển 60–80 trang, và nguyên tắc mà bản góp ý nêu là chuẩn: *"những gì cốt lõi nhất giữ ở thân bài, các chi tiết cài đặt thô đẩy ra ngoài."* Phần đẩy được, không mất mát:

- cấu hình `args.yaml` đầy đủ → Phụ lục B *(đã có, chỉ cần trỏ)*
- log lỗi và JSON thô → Phụ lục
- các đoạn mã dài mô tả cách cài đặt thông thường → Phụ lục A

**Phụ lục không giới hạn trang cũng đúng** và hiện đang bị dùng thiếu: Phụ lục A–F mới có **8 trang**, quá mỏng so với vai trò "nơi chứa chi tiết".

### 7.3. Chỗ bản góp ý mâu thuẫn với chỉ đạo vừa đưa ra

> **Chương 6: 2–3 trang.**

Con số này **không dung hoà được** với yêu cầu bạn đưa cách đây ít phút: *"đã làm rồi nhưng chưa tốt thì bỏ vô hạn chế và hướng phát triển."*

Chương 6 hiện có **10 hạn chế** và **10 hướng phát triển**, mỗi mục kèm mức nghiêm trọng và số liệu chứng minh. Nếu ép xuống 2–3 trang thì mỗi mục còn khoảng **hai dòng** — tức biến phần trung thực nhất của quyển thành một danh sách gạch đầu dòng không có bằng chứng. Và nếu tiếp tục dồn các mục "đã làm nhưng chưa tốt" từ thân bài xuống đây theo đúng chỉ đạo, Chương 6 **phải dày lên**, không thể mỏng đi.

**Khuyến nghị: Chương 6 giữ 8–10 trang**, và bù phần chênh bằng cách cắt sâu hơn ở Chương 4. Với một đồ án mà **đóng góp lớn nhất là quy trình đánh giá trung thực** (§6.2.6), chương thừa nhận hạn chế là chương không nên ép.

### 7.4. Phân bổ đề nghị thay thế

| Chương | Đề xuất gốc | Đề nghị của báo cáo này | Lý do lệch |
|---|---:|---:|---|
| 1. Giới thiệu | 5–7 | **6–7** | đồng ý |
| 2. Cơ sở lý thuyết | 10–15 | **13–15** | có phần quy chuẩn pháp lý Việt Nam không lược được |
| 3. Khảo sát và lựa chọn | 5–8 | **8–9** | vừa nhận thêm benchmark 3 engine — phần đóng góp mới |
| 4. Thiết kế và cài đặt | 15–20 | **16–18** | đồng ý, cắt sâu |
| 5. Thực nghiệm và đánh giá | 15–20 | **18–20** | phần trọng tâm |
| 6. Kết luận | 2–3 | **8–10** | ⚠️ **lệch có chủ ý** — xem 7.3 |
| **Tổng** | **60–80** | **69–79** | vẫn nằm trong khoảng đề xuất |

Tổng vẫn đạt mốc 60–80; chỉ khác cách chia.

---

## 8. Thứ tự thi hành đề nghị

Nếu được duyệt, làm theo thứ tự này để mỗi bước kiểm được và không phải làm lại:

1. **Đợi lượt ép ký tự đang chạy kết thúc** — Chương 5 chưa xong, làm chồng lên sẽ hỏng.
2. **Chèn 5 biểu đồ có sẵn** (điểm 1), xoá ba dòng *"chưa sinh"* tương ứng. *(+3–4 trang)*
3. **Tách E1/E2/E3** (điểm 4): hai câu ở §3.6.2, bảng đầy đủ xuống §6.4.
4. **Cắt Chương 4 xuống 16–18 trang**, đẩy chi tiết cài đặt sang Phụ lục A và B.
5. **Đổi Danh mục hình/bảng sang trường TOC** (điểm 2, phương án A).
6. Dựng lại, đo trang, chạy `check_thesis_refs.py`, in thử một trang đen trắng.

**Không làm:** điểm 3 (mốc thời gian) và điểm 5 (font icon) — cả hai đã kiểm là không có lỗi.

---

## 9. Việc chưa quyết, cần ý kiến

1. **Chương 6 giữ 8–10 trang hay ép xuống 2–3?** Báo cáo này khuyến nghị giữ, vì mâu thuẫn với chỉ đạo về hạn chế và hướng phát triển.
2. **Bốn hình minh hoạ ca lỗi** (`ch5:448`) có sinh không? Cần chọn tay 4 ca từ tập lỗi, khoảng 1–2 giờ, thêm ~2 trang. Không sinh thì giữ nhãn *"chưa sinh"* — trung thực nhưng để lại một khoảng trống thấy được.
3. **Phụ lục nở tới đâu?** Hiện 8 trang. Đẩy chi tiết Chương 4 xuống sẽ thành 20–25 trang. Cần xác nhận quy chế của khoa có tính phụ lục vào giới hạn không.
