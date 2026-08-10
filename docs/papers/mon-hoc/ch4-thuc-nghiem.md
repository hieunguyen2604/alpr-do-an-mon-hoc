# CHƯƠNG 4. THỰC NGHIỆM VÀ ĐÁNH GIÁ

## 4.1. Môi trường, dữ liệu và quy ước

**Môi trường.** Toàn bộ số liệu đo trên **một máy trạm duy nhất**: Windows 11 Pro; Intel Core i5-14600K, **14 nhân vật lý / 20 nhân logic**; RAM 31,77 GiB; **không có GPU CUDA**; Python 3.13.12. Mọi suy luận và huấn luyện chạy trên CPU. Đây là **tiền tố ngầm định của mọi con số hiệu năng ở mục 4.5** — so sánh chúng với FPS đo trên GPU là không hợp lệ.

**Giao thức đo.** Trọng số được **đóng băng trước** mọi phép đo; tập kiểm thử **không được chạm vào** trong huấn luyện lẫn khi chọn epoch. Khi đo độ trễ: kích thước lô bằng 1, bỏ 3 lượt khởi động nóng, báo cáo **p50 / p95 / p99 chứ không báo cáo trung bình** — trung bình che mất đuôi phân bố, mà chỉ tiêu lại phát biểu theo p95.

**Hai tập đánh giá, hai mẫu số khác nhau.** Chỉ số của bộ phát hiện đo trên **tập kiểm thử 1.514 ảnh / 1.611 đối tượng**. Chỉ số nhận dạng chỉ đo được trên **tập con có nhãn chuỗi ký tự — 2.801 biển**, vì phần lớn corpus chỉ có nhãn hộp bao. Mẫu số nhỏ này là một hạn chế thật, ghi ở mục 4.7.

**Quy ước viết tắt.** Bốn đại lượng dùng lại nhiều lần:

| Ký hiệu | Nghĩa |
|:--:|---|
| **C** | Đúng ở mức ký tự, tức $1 - \mathrm{CER}$ |
| **S₀** | Đúng **cả chuỗi**, đo trên chuỗi thô — **trước** hậu xử lý |
| **S₁** | Đúng **cả chuỗi**, **sau** hậu xử lý |
| **E** | Đúng đầu-cuối: ảnh vào → chuỗi ra, tính cả sai sót của bước phát hiện |

## 4.2. Kết quả phát hiện vùng biển

### 4.2.1. Chỉ số tổng thể

**Cả bốn chỉ tiêu của bộ phát hiện đều đạt mục tiêu**, đo bằng công cụ đánh giá chuẩn của thư viện tại ngưỡng tin cậy 0,25.

**Bảng 4.1.** Kết quả phát hiện trên tập kiểm thử 1.514 ảnh

| Chỉ số | Ngưỡng tối thiểu | Mục tiêu | Đo được | |
|---|:--:|:--:|---:|:--:|
| mAP@0,5 | 0,85 | 0,90 | **0,9829** | ✅ |
| mAP@0,5:0,95 | 0,55 | 0,65 | **0,7834** | ✅ |
| Precision | 0,88 | 0,92 | **0,9837** | ✅ |
| Recall | 0,85 | 0,90 | **0,9714** | ✅ |
| F1 | — | — | **0,9775** | — |

Ba lưu ý khi đọc bảng này. **Một,** bài toán chỉ có **một lớp**, nên giá trị mAP cao là bình thường và **không phải bằng chứng về độ khó đã vượt qua**; mAP một lớp không so trực tiếp được với mAP nhiều lớp trên các bộ dữ liệu tổng quát. **Hai,** chỉ số thực sự quyết định ở đây là **mAP@0,5:0,95**, vì độ khít của hộp bao ảnh hưởng trực tiếp đến chất lượng vùng cắt đưa sang khối xử lý ảnh. **Ba,** chỉ số tổng thể **che giấu phân bố** — hai mục sau tách nó ra.

### 4.2.2. Tách theo bố cục biển

**Bảng 4.2.** Kết quả phát hiện tách theo biển một dòng và hai dòng

| Chỉ số | Biển **một dòng** | Biển **hai dòng** | Chênh (điểm %) |
|---|---:|---:|---:|
| Số đối tượng *(tổng 1.611)* | 286 | 1.325 | — |
| mAP@0,5 | 0,9884 | 0,9675 | **2,09** |
| mAP@0,5:0,95 | 0,7526 | 0,7649 | −1,23 |
| Recall | 0,9895 | 0,9691 | 2,04 |

Chênh lệch giữa hai bố cục ở tầng phát hiện chỉ **2,09 điểm** — nhỏ. Con số này đáng nhớ, vì mục 4.3.2 sẽ cho thấy cùng phép tách đó ở tầng nhận dạng cho **25,45 điểm**. Kết luận: **bài toán biển hai dòng không nằm ở khâu phát hiện.**

### 4.2.3. Tách theo kích thước đối tượng

Mục này tồn tại vì bộ dữ liệu có **10,91% số hộp bao chiếm dưới 0,5% diện tích ảnh** — vượt ngưỡng chất lượng 10% mà đồ án tự đặt. Đối tượng nhỏ là chế độ thất bại đã ghi nhận rộng rãi của bộ phát hiện một giai đoạn, nên một con số mAP tổng sẽ **giấu chế độ thất bại đó sau giá trị trung bình**.

**Bảng 4.3.** Kết quả phát hiện tách theo dải kích thước hộp bao

| Dải (diện tích hộp / diện tích ảnh) | Số đối tượng | mAP@0,5 | mAP@0,5:0,95 | Recall |
|---|---:|---:|---:|---:|
| **Rất nhỏ** — dưới 0,5% | 262 | **0,8553** | **0,5249** | 0,8740 |
| **Nhỏ** — 0,5% đến 1% | 124 | 0,9755 | 0,7055 | 0,9758 |
| **Trung bình** — 1% đến 5% | 900 | 0,9913 | 0,8005 | 0,9922 |
| **Lớn** — 5% đến 15% | 297 | 0,9966 | 0,8394 | 0,9966 |
| **Rất lớn** — trên 15% | 28 † | 1,0000 | 0,8562 | 1,0000 |

† Dòng này chỉ có 28 đối tượng, dưới ngưỡng 30 nên không có ý nghĩa thống kê và không được dùng để so sánh.

Điểm yếu duy nhất của bộ phát hiện lộ ra ở đây: dải **rất nhỏ** rớt xuống mAP@0,5 = 0,8553 và mAP@0,5:0,95 = 0,5249, tức **hộp bao vừa dễ bỏ sót vừa kém khít**. Với biển số, hộp kém khít kéo theo hậu quả dây chuyền: vùng cắt lệch làm tỉ lệ khung hình đo sai, khiến bước ước lượng số dòng ở mục 3.4.3 phân loại nhầm.

## 4.3. Kết quả nhận dạng ký tự

### 4.3.1. Mức ký tự và đóng góp của khối hậu xử lý

**Bảng 4.4.** Độ chính xác trước và sau hậu xử lý, trên 2.801 biển có nhãn chuỗi

| Chỉ số | Ngưỡng tối thiểu | Mục tiêu | **Trước** | **Sau** | Chênh |
|---|:--:|:--:|---:|---:|---:|
| **C** — đúng mức ký tự | 0,92 | 0,95 | 0,9061 | **0,9454** 🟡 | +3,93 |
| CER | ≤ 0,08 | ≤ 0,05 | 0,0939 | 0,0546 | — |
| **S₀ → S₁** — đúng cả chuỗi | 0,80 → 0,85 | 0,85 → 0,90 | **0,6373** ❌ | **0,7512** ❌ | **+11,39** |
| Số biển **sửa đúng** / **bị làm hỏng** | — | — | — | **319** / **0** | — |
| Phân rã lỗi ký tự $S$ / $D$ / $I$ trên $N$ = 23.855 | — | — | 862 / 1.272 / 107 | — | — |

**Khối hậu xử lý đóng góp +11,39 điểm, sửa đúng 319 biển và không làm hỏng biển nào.** Con số "0 biển bị làm hỏng" không phải may mắn mà là hệ quả của nguyên tắc thiết kế ở mục 3.6d: biểu thức chính quy được thử **trước** khi sửa bất cứ thứ gì, nên chuỗi vốn đã hợp lệ không bao giờ bị can thiệp.

Phân rã lỗi ký tự cho một manh mối quan trọng: **số ký tự bị xoá ($D$ = 1.272) lớn hơn số bị thay thế ($S$ = 862)**. Hồ sơ lỗi thiên về *xoá* có cách giải thích tự nhiên là **mất hẳn một dòng** — đúng cơ chế đã dự đoán ở mục 2.4.2.

### 4.3.2. Tách theo bố cục — kết quả quan trọng nhất của chương

**Bảng 4.5.** Độ chính xác nhận dạng tách theo biển một dòng và hai dòng

| Chỉ số | Biển **một dòng** | Biển **hai dòng** | Chênh (điểm %) |
|---|---:|---:|---:|
| Số mẫu *(tổng 2.801)* | **567** | **2.234** | — |
| **C** — đúng mức ký tự | 0,9925 | 0,9344 | 5,81 |
| **S₀** — đúng cả chuỗi, trước hậu xử lý | 0,9418 | 0,5600 | **38,18** |
| **S₁** — đúng cả chuỗi, sau hậu xử lý | **0,9541** | **0,6996** | **25,45** |
| Cải thiện nhờ hậu xử lý | +1,23 | **+13,97** | — |

![](figures/fig-ch4-layout.png)

**Hình 4.1.** Đối chiếu biển một dòng và hai dòng trên ba chỉ số

Chênh lệch mà tầng phát hiện gần như che khuất (2,09 điểm ở Bảng 4.2) **lộ ra ở tầng nhận dạng với biên độ khác hẳn cấp**: 5,81 điểm ở mức ký tự, **25,45 điểm** ở S₁, **38,18 điểm** ở S₀.

Hình 4.1 còn cho thấy một điều mà bảng số không nói ngay: **cột đo mức ký tự gần như không phân biệt được hai bố cục** (0,9925 so với 0,9344), trong khi cột đo cả chuỗi thì cách nhau một trời một vực. Đây chính là quan hệ phi tuyến ở mục 2.4.3: sai một ký tự trong tám là hỏng cả chuỗi, nên một chênh lệch 5,81 điểm ở mức ký tự **khuếch đại thành 25,45 điểm** ở mức chuỗi. Chọn chỉ số nào để báo cáo vì vậy quyết định kết luận trông ra sao — và mức chuỗi mới là mức phản ánh giá trị sử dụng.

Ba kết luận rút ra:

**Biển một dòng về cơ bản đã giải xong** — S₁ = 0,9541, vượt cả mục tiêu 0,90. Toàn bộ việc "nhận dạng không đạt chỉ tiêu" là do **biển hai dòng kéo xuống**, và vì biển hai dòng chiếm **2.234 / 2.801 = 79,8%** tập đánh giá (phản ánh đúng tỉ lệ xe máy rất cao ở Việt Nam), con số tổng bị quần thể khó này chi phối.

**Khối hậu xử lý có ích gấp mười một lần trên biển hai dòng** (+13,97 so với +1,23 điểm). Điều này hợp lý: biển một dòng vốn đã đọc gần đúng nên còn rất ít chỗ để sửa.

**Khoảng cách 25,45 điểm là con số *sau* khi đã áp toàn bộ chuỗi biện pháp xử lý ảnh** ở mục 3.4. Ở lượt đo trước khi có bậc thang thử lại và bước phục hồi dòng trên, S₁ của biển hai dòng là 0,5810 và khoảng cách là **36,79 điểm** — chuỗi biện pháp đã thu hẹp **11,34 điểm**, một dịch chuyển thật nhưng vẫn để lại gần một phần tư khoảng cách. Phần còn lại nằm ở **năng lực nhận dạng của mô hình ký tự**, không ở khâu cắt hay ghép, vì hai khâu đó đã được đo tách bạch ở mục 4.4.

### 4.3.3. Ma trận nhầm lẫn ký tự và mức chính xác của bảng luật

Mục 3.6c đã nêu một giới hạn: bảng ánh xạ nhầm lẫn **suy từ hình dạng ký tự chứ không từ đo đạc**. Mục này kiểm chứng nó bằng ma trận nhầm lẫn 36 × 36 đo được.

**Bảng 4.6.** Mười cặp ký tự bị nhầm nhiều nhất, đối chiếu bảng luật hiện hành

| Hạng | Nhầm | Số lần | Tỉ lệ trong tổng lỗi thay thế | Bảng luật có phủ? |
|:---:|:---:|---:|---:|---|
| 1 | L → 1 | 90 | 10,44% | **có — đúng chiều** |
| 2 | E → F | 73 | 8,47% | không |
| 3 | 4 → L | 53 | 6,15% | không |
| 4 | U → 1 | 38 | 4,41% | không |
| 5 | D → 0 | 34 | 3,94% | **có — đúng chiều** |
| 6 | Z → 7 | 32 | 3,71% | không |
| 7 | 2 → 7 | 26 | 3,02% | không |
| 8 | X → Y | 21 | 2,44% | không |
| 9 | B → R | 20 | 2,32% | không |
| 10 | 9 → 0 | 19 | 2,20% | không |

Kết quả này là một **phát hiện âm có giá trị**: bảng luật suy từ hình dạng chỉ phủ **2 trong 10** cặp nhầm phổ biến nhất, tuy cả hai đều đúng chiều. Bảy cặp không được phủ — `E → F`, `4 → L`, `U → 1`, `Z → 7` — đều là những cặp mà trực giác hình dạng không gợi ra, nhưng thực tế lại rất phổ biến trên ảnh phân giải thấp.

Hướng cải thiện rõ ràng: **thay bảng suy đoán bằng bảng trích trực tiếp từ ma trận nhầm lẫn đo được**. Đây là ví dụ điển hình cho việc đo đạc thay thế trực giác.

### 4.3.4. So sánh ba engine nhận dạng trên cùng một tầng bao quanh

Câu hỏi: chọn PaddleOCR có đúng không, khi tài liệu công khai thực tế nghiêng về EasyOCR?

**Thiết kế thí nghiệm.** Cả ba engine chạy trong **đúng một tầng bao quanh** — sao đúng chuỗi bước xử lý ảnh của bản giao hàng — trên **cùng một mảng ảnh đã chuẩn bị xong**; khác biệt duy nhất còn lại là engine. Điều này quan trọng, vì bốn lượt chạy đầu đều cho số vô nghĩa và mỗi lượt hỏng lộ ra một điều kiện bắt buộc. Bài học chung: **phần lớn năng lực đọc biển số không nằm trong engine mà ở tầng xử lý ảnh bao quanh nó** — so sánh ba engine với ba tầng bao quanh khác nhau là đo tầng bao quanh chứ không đo engine.

**Bảng 4.7.** So sánh ba engine trên 2.801 biển số Việt Nam

| Engine | Tắt bước tách-ghép | Có tách-ghép | + hậu xử lý | Riêng biển 2 dòng |
|---|---:|---:|---:|---:|
| **PaddleOCR** | 28,81% | **63,73%** | **68,87%** | **62,3%** |
| EasyOCR | 6,53% | 10,35% | 14,28% | 10,7% |
| Tesseract | 9,57% | 9,60% | 10,28% | **0,1%** |

**PaddleOCR thắng dứt khoát** — 68,87%, hơn EasyOCR 54,59 điểm và hơn Tesseract 58,59 điểm, khoảng cách quá lớn để quy cho nhiễu.

**Tesseract không đọc được biển hai dòng**: **0,1% trên 2.234 mẫu**, kể cả sau khi đã ghép thành một dòng, trong khi đọc được 50,4% biển một dòng. Đã kiểm bằng mắt để loại khả năng lỗi công cụ — nó **có** đọc ra chữ nhưng luôn kèm ký tự rác, và 700/2.801 lần trả chuỗi rỗng.

**Kết quả bất ngờ nhất — bước tách-ghép KHÔNG độc lập engine:**

| Engine | Mức tăng nhờ tách-ghép |
|---|---:|
| PaddleOCR | **+34,92 điểm** |
| EasyOCR | +3,82 điểm |
| Tesseract | **+0,03 điểm** |

Nếu cả ba cùng tăng mạnh, đóng góp kỹ thuật ở mục 3.4.5 sẽ là một kỹ thuật độc lập engine — một khẳng định mạnh hơn nhiều. **Dữ liệu không cho phép nói thế.** Phát biểu đúng là: tách-rồi-ghép-ngang là **điều kiện cần** để đọc biển hai dòng — nó biến bài toán đa dòng thành bài toán một dòng — nhưng **không đủ**; engine vẫn phải đủ mạnh để tận dụng dải ảnh đã ghép.

Ngược lại, **bộ luật hậu xử lý giúp cả ba** (+5,14 · +3,93 · +0,68 điểm), nên riêng nó **là** một đóng góp độc lập engine.

## 4.4. Bóc tách đóng góp của từng bước xử lý ảnh

Mục này là lý do các bước ở mục 3.4 được thiết kế bật tắt độc lập.

### 4.4.1. Ghép rồi đọc một lần, so với đọc riêng từng nửa

Thí nghiệm A/B trên **200 biển hai dòng** với hạt giống ngẫu nhiên cố định:

**Bảng 4.8.** Hai chiến lược đọc biển hai dòng

| Phương án | Đúng | Chuỗi rỗng | Thời gian |
|---|---:|---:|---:|
| **A — ghép ngang rồi đọc một lần** *(đang dùng)* | **129/200 = 64,50%** | 2 | 340,11 ms |
| B — đọc riêng từng nửa rồi nối chuỗi | **7/200 = 3,50%** | 9 | 391,35 ms |

**B kém A 61,00 điểm phần trăm và còn đắt hơn 51,24 ms.** Trong 200 ca, **122 ca A thắng B và 0 ca B thắng A** — giả thuyết "đọc riêng từng dòng thì chính xác hơn" bị **bác bỏ dứt khoát**.

Nguyên nhân đọc được ngay trong dữ liệu, và nó chính là hệ quả của vùng chồng lấn ở mục 3.4.4: khi hai nửa được đọc riêng, dải chồng lấn bị nhận dạng **hai lần** và ký tự bị nhân đôi — `84G122593` đọc ra thành `84-G124E009.01225.93`. Trên dải liền mạch đã ghép, vùng lặp nằm **giữa** hai cụm ký tự và bị bộ phát hiện văn bản loại bỏ như mảnh nhiễu.

Đây là một **kết quả âm có giá trị**: nó chứng minh lựa chọn kiến trúc ở mục 3.4.5 không tuỳ tiện, và nó cho thấy vùng chồng lấn — vốn thiết kế chỉ để tránh cắt cụt ký tự — còn có một tác dụng thứ hai mà thiết kế ban đầu không lường trước.

### 4.4.2. Bậc thang thử lại: cái giá của 34 biển đọc thêm

Bậc thang nắn hình và giãn dọc ở mục 3.4.6 mua thêm **34 biển đọc đúng**. Cái giá đo được:

**Bảng 4.9.** Ảnh hưởng của bậc thang thử lại lên độ trễ

| Chỉ số | Tắt bậc thang | Bật bậc thang *(bản giao hàng)* | Chênh |
|---|---:|---:|---:|
| p50 | 414,67 ms | **405,77 ms** | **−8,90** |
| p95 | 866,3 ms | **1.143,10 ms** | +276,80 |
| p99 | — | 1.420,07 ms | — |

Điểm đáng chú ý: **trung vị thậm chí giảm nhẹ.** Vì bậc thang chỉ chạy **sau khi lần đọc đầu thất bại**, nó không chạm vào trường hợp thường; toàn bộ chi phí dồn vào **đuôi phân bố**. Với một hệ thống mà 95% ảnh xong dưới 1,15 giây và một nửa xong dưới 0,41 giây, p50 mô tả trải nghiệm điển hình còn p95 mô tả trường hợp xấu.

Đây là một **thoái lui có chủ ý và đã định lượng**: đổi 277 ms ở p95 lấy 34 biển đọc thêm.

### 4.4.3. Siêu phân giải: một số 0 và cách đọc nó cho đúng

Bậc thứ ba của thang thử lại là **siêu phân giải** bằng mạng FSRCNN [16], dành cho vùng biển quá nhỏ. Kết quả đo:

| | Chi phí | Lợi ích |
|---|---:|---:|
| Nắn hình + giãn dọc | +244 ms p95 | **+34 biển** |
| **Siêu phân giải** | **+319 ms p95, +1.381 ms p99** | **0 biển** |

Một mình bậc siêu phân giải đẩy p95 lên **1.514,26 ms**, tức **vượt cả ngưỡng tối thiểu 1.500 ms**. Nó đã bị **tắt mặc định**, đưa p95 về 1.143,10 ms.

**Nhưng số 0 đó phải đọc cho đúng, và đây là điểm phương pháp luận đáng nêu.** Cổng vào bậc siêu phân giải chỉ mở cho vùng cắt **nhỏ hơn 200 điểm ảnh**, và trong ngữ liệu đo **0 trên 120 mẫu lọt qua cổng đó**. Nói cách khác, quyết định tắt dựa trên **"chi phí đã đo, lợi ích chưa ai đo được"** — không phải trên "đã đo và thấy vô dụng". Mã và công tắc vì vậy được **giữ nguyên**, để đo lại khi có ngữ liệu chứa biển thật sự nhỏ.

Phân biệt này quan trọng: một số 0 do *thiếu điều kiện quan sát* khác hẳn một số 0 do *đã quan sát và thấy bằng không*.

## 4.5. Hiệu năng

### 4.5.1. Phân rã ngân sách độ trễ

**Bảng 4.10.** Phân rã thời gian xử lý một biển số

| Bước | Đo được (ms) | % tổng |
|---|---:|---:|
| Giải mã ảnh và tiền xử lý | 2,83 | 1,7% |
| **Suy luận YOLO11n @ 640px** | **57,27** | **34,0%** |
| Cắt và tiền xử lý vùng biển | ~0,00 | 0,0% |
| **PaddleOCR (mỗi biển)** | **108,28** | **64,3%** |
| Hậu xử lý và kiểm tra hợp lệ | 0,03 | 0,0% |
| **Tổng suy luận thuần** | **168,41** | **100%** |

Ba nhận xét. **Một, nút thắt là khối nhận dạng ký tự** (64,3%) chứ không phải bộ phát hiện (34,0%). Nguyên nhân: PaddleOCR là một **đường ống nhiều giai đoạn** — phát hiện văn bản, phân loại hướng, rồi mới nhận dạng — thiết kế cho ảnh tài liệu tổng quát, nên hệ thống trả chi phí cho những năng lực mà một vùng biển đã cắt sẵn không cần.

**Hai, toàn bộ khối xử lý ảnh của đồ án gần như miễn phí**: bước cắt và tiền xử lý vùng biển đo được xấp xỉ 0 ms, hậu xử lý 0,03 ms. Đóng góp +11,39 điểm ở mục 4.3.1 vì vậy đến với chi phí tính toán không đáng kể — một tỉ lệ lợi ích trên chi phí rất hiếm.

**Ba, chiến lược tối ưu suy ra trực tiếp từ bảng này.** Theo định luật Amdahl, tăng tốc bộ phát hiện gấp 2–3 lần chỉ kéo tổng xuống khoảng 15–23%; muốn giảm mạnh hơn thì khối nhận dạng (64,3%) mới là mục tiêu.

### 4.5.2. Độ trễ đầu-cuối và các chỉ tiêu tài nguyên

Độ trễ một ảnh: **p50 = 405,77 ms · p95 = 1.143,10 ms · p99 = 1.420,07 ms**. Chỉ tiêu p95 phát biểu ở mức ≤ 1.500 ms (tối thiểu) và ≤ 800 ms (mục tiêu), nên kết luận chính thức là **đạt ngưỡng tối thiểu, không đạt mục tiêu** — với nguyên nhân đã định lượng ở mục 4.4.2.

Mọi chỉ tiêu **ngoài đường xử lý ảnh** đều đạt với biên rộng: nạp mô hình 6,41 s (ngưỡng 30 s); bộ nhớ thường trú 0,806 GB (ngưỡng 4 GB); truy vấn 10.000 bản ghi lịch sử 18,71 ms; chạy liên tục 15 phút với **100% thành công trên 2.028 yêu cầu** và bộ nhớ chỉ tăng 0,094 GB — **không rò rỉ**.

### 4.5.3. Độ chính xác bộ phân loại màu nền

**Bảng 4.11.** Độ chính xác phân loại màu nền trên tập ngoài dữ liệu hiệu chỉnh

| Lớp nhãn người gán | Số ảnh | Đúng | Độ chính xác |
|---|---:|---:|---:|
| Biển vàng | 694 | 684 | **98,56%** |
| Biển trắng | 808 | 787 | **97,40%** |
| Biển xanh | 63 | 61 | **96,83%** |
| **Tổng** | **1.565** | **1.532** | **97,89%** |

Ba giới hạn phải nêu kèm. **Một,** 542 ảnh đã bị loại khỏi phép đo — toàn bộ lớp không xác định, cùng các ảnh chụp ban đêm hoặc hồng ngoại mà chính người gán nhãn cũng không xác định được màu. **Hai,** dạng lỗi chủ đạo là **biển trắng bị phân loại thành biển xanh** — 21 trong 33 ca sai — do một số điểm ảnh ám lạnh vượt ngưỡng bão hoà. **Ba,** bộ dữ liệu không chứa biển đỏ và biển ngoại giao nên hai nhánh này chưa có số liệu.

## 4.6. Phân tích lỗi

**Bảng 4.12.** Tần suất từng loại lỗi trên 2.801 mẫu

| Mã | Loại lỗi | Số ca | Tỉ lệ trong tổng ca sai | Một dòng | Hai dòng |
|:---:|---|---:|---:|---:|---:|
| E1 | Bỏ sót biển ở khâu phát hiện | 335 | — | — | — |
| E3 | **Nhầm ký tự** | **445** | **63,85%** | 17 | **428** |
| E4 | Thiếu ký tự | 73 | 10,47% | 0 | 73 |
| E5 | Thừa ký tự | 18 | 2,58% | 5 | 13 |
| E6 | Sai thứ tự | **0** | 0,00% | 0 | 0 |
| | **Tổng ca sai** | **697** | 100% | — | — |

Bảng này khép lại mạch lập luận của chương. **Nhầm ký tự chiếm gần hai phần ba số ca sai, và 428 trên 445 ca thuộc biển hai dòng** — cùng một kết luận đã rút ra ở mục 4.3.2, nay xác nhận từ một góc đo khác.

**Sai thứ tự bằng 0** là bằng chứng trực tiếp cho thấy thiết kế ghép ngang ở mục 3.4.5 hoạt động đúng: nếu phép ghép đặt nhầm thứ tự hai nửa, hoặc nếu CTC vẫn đọc lộn xộn giữa hai dòng, loại lỗi này phải xuất hiện. Nó không xuất hiện một lần nào.

**Thiếu ký tự tập trung tuyệt đối ở biển hai dòng** (73/73), khớp với hồ sơ lỗi thiên về xoá ở mục 4.3.1 và với chế độ hỏng "mất hẳn dòng trên" mà mục 3.4.7 xử lý.

![](figures/fig-ch4-loi.png)

**Hình 4.2.** Sáu vùng biển thật: ba ca khối hậu xử lý sửa được, ba ca vẫn sai

Hình 4.2 cho thấy các con số ở Bảng 4.12 **trông như thế nào trên ảnh thật**. Hàng trên minh hoạ đúng ba cơ chế mà mục 3.6 mô tả: `2947872 → 29A7872` là mặt nạ vị trí ép chữ số thành chữ cái ở vị trí seri; `52126661 → 52L26661` là cùng cơ chế với cặp `1 / L`; còn `5203 → 78N25203` là bước phục hồi dòng trên ở mục 3.4.7 — chuỗi thô mất trọn dòng trên và được đọc lại riêng nửa trên.

Hàng dưới cho thấy phần còn lại khó ở đâu. Cả ba đều là biển hai dòng, và cả ba đều **hỏng ở dòng trên**: `30A → 37L`, `31F` mất hẳn, `52Z → 52T`. Dòng dưới toàn chữ số nên bộ luật vị trí kiểm được; dòng trên trộn chữ và số ở đúng vị trí mà mặt nạ cho phép cả hai, nên hậu xử lý **không có ràng buộc nào để bám vào**. Đây là lý do hướng phát triển số 1 ở mục 5.3 nhắm vào bộ nhận dạng chứ không nhắm vào bộ luật.

Cần lưu ý về ảnh: ngữ liệu nhãn xuất mọi vùng cắt về khung vuông 640 × 640, **phá tỉ lệ khung hình gốc**. Hình trên đã khôi phục tỉ lệ bằng đúng hàm mà công cụ đo dùng trước khi chạy nhận dạng. Bước khôi phục này không phải chi tiết trình bày: bỏ nó đi thì S₁ rơi từ 0,7512 xuống **0,4988**, vì mọi vùng cắt vuông đều bị phân loại thành hai dòng.

## 4.7. Các yếu tố ảnh hưởng tới tính hợp lệ của kết quả

Nguyên tắc: nêu mối đe doạ, đánh giá mức nghiêm trọng, và nói rõ đã làm gì để giảm thiểu — **kể cả khi biện pháp là "không có"**.

**Bảng 4.13.** Sáu yếu tố ảnh hưởng tới tính hợp lệ

| # | Yếu tố | Mức | Biện pháp đã áp dụng |
|:--:|---|:--:|---|
| 1 | **Rò rỉ dữ liệu tồn dư không khử được bằng băm tri giác** (mục 3.2.3) | Cao | Nâng ngưỡng gộp 5 → 10 và đo ở nhiều ngưỡng cao hơn. Vẫn còn 791 cặp ở ngưỡng 12; rò rỉ *ngữ nghĩa* **không ngưỡng nào phát hiện được** ⇒ mọi chỉ số ở mục 4.2 phải coi là **cận trên lạc quan** |
| 2 | **Tập kiểm thử không xuyên bộ dữ liệu** | Cao | **Không có.** Cách đúng là giữ lại một nguồn hoàn toàn không dùng để huấn luyện; chưa thực hiện |
| 3 | **Mẫu số nhỏ cho chỉ số nhận dạng** — 2.801 trên 15.133 ảnh có nhãn chuỗi | Cao | Công bố mẫu số ở mọi bảng; không rút kết luận từ chênh lệch nhỏ |
| 4 | **Bộ dữ liệu lệch nặng về biển trắng** — 97,68% mẫu | Cao | Nêu rõ: kết luận về độ chính xác nhận dạng **chỉ áp cho biển trắng** |
| 5 | Đo trên **một cấu hình phần cứng duy nhất** | Trung bình | Công bố cấu hình đầy đủ ở mục 4.1; **không ngoại suy** sang CPU hay hệ điều hành khác |
| 6 | **Một lượt huấn luyện duy nhất**, không ước lượng được phương sai | Trung bình | Cố định hạt giống để tái lập; không phát biểu so sánh dựa trên chênh lệch nhỏ |
