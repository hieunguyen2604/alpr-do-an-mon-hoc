# CHƯƠNG 4. THỰC NGHIỆM VÀ ĐÁNH GIÁ

## 4.1. Môi trường, dữ liệu và quy ước

**Môi trường.** Mọi số liệu **hiệu năng** ở mục 4.5 đo trên một máy trạm duy nhất, **Intel Core i5-14600K (14 nhân / 20 luồng), không có GPU CUDA**; toàn bộ suy luận và huấn luyện chạy trên CPU. Cần nêu số nhân chứ không chỉ nêu "trên CPU", vì độ trễ tỉ lệ trực tiếp với nó và hệ thống đặt cứng số luồng tính toán. Ngược lại, số liệu **độ chính xác** không phụ thuộc phần cứng: cùng mô hình và cùng dữ liệu thì máy nào cũng cho kết quả đó. Phiên bản hệ điều hành, thư viện và Python ghi ở Phụ lục A.

**Giao thức đo.** Trọng số được **đóng băng trước** mọi phép đo; tập kiểm thử **không được chạm vào** trong huấn luyện lẫn khi chọn epoch. Khi đo độ trễ: kích thước lô bằng 1, bỏ 3 lượt khởi động nóng, báo cáo **p50 / p95 / p99 chứ không báo cáo trung bình** — trung bình che mất đuôi phân bố, mà chỉ tiêu lại phát biểu theo p95.

**Hai tập đánh giá, hai mẫu số khác nhau.** Chỉ số của bộ phát hiện đo trên **tập kiểm thử 1.514 ảnh / 1.611 đối tượng**. Chỉ số nhận dạng chỉ đo được trên **tập con có nhãn chuỗi ký tự — 2.801 biển**, vì phần lớn ngữ liệu chỉ có nhãn hộp bao. Mẫu số nhỏ này là một hạn chế thật, ghi ở mục 4.7.

**Quy ước viết tắt.** Ba đại lượng dùng lại nhiều lần. *(Lưu ý: các mã **E1–E6** ở mục 4.6 là **mã loại lỗi**, không liên quan tới ba ký hiệu này.)*

| Ký hiệu | Nghĩa |
|:--:|---|
| **C** | Đúng ở mức ký tự, tức $1 - \mathrm{CER}$ |
| **S₀** | Đúng **cả chuỗi**, đo trên chuỗi thô — **trước** hậu xử lý |
| **S₁** | Đúng **cả chuỗi**, **sau** hậu xử lý |

## 4.2. Kết quả phát hiện vùng biển

### 4.2.1. Chỉ số tổng thể

**Cả bốn chỉ tiêu của bộ phát hiện đều đạt mục tiêu**, đo bằng công cụ đánh giá chuẩn của thư viện tại ngưỡng tin cậy 0,25 (Bảng 4.1).

**Bảng 4.1.**[]{#tbl-4-1} Kết quả phát hiện trên tập kiểm thử 1.514 ảnh

| Chỉ số | Ngưỡng tối thiểu | Mục tiêu | Đo được | |
|---|:--:|:--:|---:|:--:|
| mAP@0,5 | 0,85 | 0,90 | **0,9829** | **Đạt** |
| mAP@0,5:0,95 | 0,55 | 0,65 | **0,7834** | **Đạt** |
| Precision | 0,88 | 0,92 | **0,9837** | **Đạt** |
| Recall | 0,85 | 0,90 | **0,9714** | **Đạt** |
| F1 | — | — | **0,9775** | — |

Ba lưu ý khi đọc bảng này. **Một,** bài toán chỉ có **một lớp**, nên giá trị mAP cao là bình thường và **không phải bằng chứng về độ khó đã vượt qua**; mAP một lớp không so trực tiếp được với mAP nhiều lớp trên các bộ dữ liệu tổng quát. **Hai,** chỉ số thực sự quyết định ở đây là **mAP@0,5:0,95**, vì độ khít của hộp bao ảnh hưởng trực tiếp đến chất lượng vùng cắt đưa sang khối xử lý ảnh. **Ba,** chỉ số tổng thể **che giấu phân bố** — hai mục sau tách nó ra.

### 4.2.2. Tách theo bố cục biển

**Bảng 4.2.**[]{#tbl-4-2} Kết quả phát hiện tách theo biển một dòng và hai dòng

| Chỉ số | Biển **một dòng** | Biển **hai dòng** | Chênh (điểm %) |
|---|---:|---:|---:|
| Số đối tượng *(tổng 1.611)* | 286 | 1.325 | — |
| mAP@0,5 | 0,9884 | 0,9675 | **2,09** |
| mAP@0,5:0,95 | 0,7526 | 0,7649 | −1,23 |
| Recall | 0,9895 | 0,9691 | 2,04 |

Bảng 4.2 cho thấy chênh lệch giữa hai bố cục ở tầng phát hiện chỉ **2,09 điểm** — nhỏ. Con số này đáng nhớ, vì mục 4.3.2 sẽ cho thấy cùng phép tách đó ở tầng nhận dạng cho **23,07 điểm**. Kết luận: **bài toán biển hai dòng không nằm ở khâu phát hiện.**

### 4.2.3. Tách theo kích thước đối tượng

Mục này tồn tại vì toàn bộ bộ dữ liệu có **10,91% số hộp bao chiếm dưới 0,5% diện tích ảnh** — vượt ngưỡng chất lượng 10% mà đồ án tự đặt; riêng trên tập kiểm thử tỉ lệ này là 16,3% (262/1.611). Đối tượng nhỏ là chế độ thất bại đã ghi nhận rộng rãi của bộ phát hiện một giai đoạn, nên một con số mAP tổng sẽ **giấu chế độ thất bại đó sau giá trị trung bình** (Bảng 4.3).

**Bảng 4.3.**[]{#tbl-4-3} Kết quả phát hiện tách theo dải kích thước hộp bao

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

**Bảng 4.4.**[]{#tbl-4-4} Độ chính xác trước và sau hậu xử lý, trên 2.801 biển có nhãn chuỗi

| Chỉ số | Ngưỡng tối thiểu | Mục tiêu | **Trước** | **Sau** | Chênh |
|---|:--:|:--:|---:|---:|---:|
| **C** — đúng mức ký tự | 0,92 | 0,95 | 0,9061 | **0,9483** (Cận ngưỡng) | +4,22 |
| CER | ≤ 0,08 | ≤ 0,05 | 0,0939 | 0,0517 | — |
| **S₀ → S₁** — đúng cả chuỗi | 0,80 → 0,85 | 0,85 → 0,90 | **0,6373** (Chưa đạt) | **0,7701** (Chưa đạt) | **+13,28** |
| Số biển **sửa đúng** / **bị làm sai lệch** | — | — | — | **372** / **0** | — |
| Phân rã lỗi ký tự $S$ / $D$ / $I$ trên $N$ = 23.855 | — | — | 862 / 1.272 / 107 | — | — |

**Khối hậu xử lý đóng góp +13,28 điểm, sửa đúng 372 biển và không làm sai lệch biển nào** (Bảng 4.4). Con số "0 biển bị làm sai lệch" không phải may mắn mà là hệ quả của nguyên tắc thiết kế ở mục 3.6d: biểu thức chính quy được thử **trước** khi sửa bất cứ thứ gì, nên chuỗi vốn đã hợp lệ không bao giờ bị can thiệp.

Phân rã lỗi ký tự cho một manh mối quan trọng: **số ký tự bị xoá ($D$ = 1.272) lớn hơn số bị thay thế ($S$ = 862)**. Hồ sơ lỗi thiên về *xoá* có cách giải thích tự nhiên là **mất hẳn một dòng** — đúng cơ chế đã dự đoán ở mục 2.4.2 (Bảng 4.5).

### 4.3.2. Tách theo bố cục — kết quả quan trọng nhất của chương

**Bảng 4.5.**[]{#tbl-4-5} Độ chính xác nhận dạng tách theo biển một dòng và hai dòng

| Chỉ số | Biển **một dòng** | Biển **hai dòng** | Chênh (điểm %) |
|---|---:|---:|---:|
| Số mẫu *(tổng 2.801)* | **567** | **2.234** | — |
| **C** — đúng mức ký tự | 0,9925 | 0,9380 | 5,45 |
| **S₀** — đúng cả chuỗi, trước hậu xử lý | 0,9418 | 0,5600 | **38,18** |
| **S₁** — đúng cả chuỗi, sau hậu xử lý | **0,9541** | **0,7234** | **23,07** |
| Cải thiện nhờ hậu xử lý | +1,23 | **+16,34** | — |

![](figures/fig-ch4-layout.png)

**Hình 4.1.**[]{#fig-4-1} Đối chiếu biển một dòng và hai dòng trên ba chỉ số

Hình 4.1 cho thấy quan hệ phi tuyến ở mục 2.4.3 bằng số thật: cột đo mức ký tự gần như không phân biệt hai bố cục (0,9925 so với 0,9380), nhưng sai một ký tự trong tám là hỏng cả chuỗi, nên chênh lệch 5,45 điểm ở mức ký tự **khuếch đại thành 23,07 điểm** ở mức chuỗi. Ba kết luận rút ra:

1. **Điểm nghẽn nằm ở biển hai dòng.** Biển một dòng đạt S₁ = 0,9541, vượt cả mục tiêu 0,90; biển hai dòng chiếm 79,8% tập đánh giá nên kéo con số tổng xuống.
2. **Hậu xử lý hiệu quả hơn hẳn trên biển hai dòng** — +16,34 so với +1,23 điểm; biển một dòng vốn đã đọc gần đúng nên còn ít chỗ để sửa.
3. **Tách-ghép đã thu hẹp đáng kể khoảng cách nhưng chưa xoá được** — từ 36,79 xuống 23,07 điểm; phần còn lại nằm ở năng lực mô hình ký tự, vì khâu cắt-ghép đã được đo tách bạch ở mục 4.4.

### 4.3.3. Ma trận nhầm lẫn ký tự và mức chính xác của bảng luật

Mục 3.6c đã nêu một giới hạn: bảng ánh xạ nhầm lẫn ban đầu **suy từ hình dạng ký tự chứ không từ đo đạc**. Mục này kiểm chứng nó bằng ma trận nhầm lẫn 36 × 36 đo được, và kết quả đã được dùng để **sửa lại chính bảng đó** (Bảng 4.6).

**Bảng 4.6.**[]{#tbl-4-6} Mười cặp ký tự bị nhầm nhiều nhất, đối chiếu bảng luật hiện hành

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

Kết quả này là một **phát hiện âm có giá trị**: bảng luật suy từ hình dạng chỉ phủ **2 trong 10** cặp nhầm phổ biến nhất, tuy cả hai đều đúng chiều. Tám cặp không được phủ, trong đó bốn cặp `E → F`, `4 → L`, `U → 1`, `Z → 7` là những cặp mà trực giác hình dạng không gợi ra, nhưng thực tế lại rất phổ biến trên ảnh phân giải thấp.

Phép thay thế **đã được thực hiện ngay trong vòng này** cho hai cặp có đủ bằng chứng: mục `L → 1` tại vị trí chữ số đổi thành `L → 4` (hạng 3, 53 lần) và mục cho `7` tại vị trí chữ cái đổi thành `7 → Z` (hạng 6, 32 lần), nhận dạng chính xác thêm **53 biển đọc đúng và 0 biển hỏng** — đây chính là cấu hình triển khai sinh ra S₁ = 0,7701, và bảng ánh xạ phủ **4 trong 10** cặp. Sáu cặp còn lại không sửa được bằng cơ chế này: năm cặp cùng kiểu (`E → F`, `X → Y`, `B → R`, `2 → 7`, `9 → 0`) không bao giờ kích hoạt mặt nạ vị trí vì ký tự đọc ra vẫn đúng kiểu; cặp `U → 1` xung đột với `L → 1` phổ biến hơn (90 so với 38 lần) nên giữ chiều thắng. Xử lý chúng cần một cơ chế khác và ngữ liệu lớn hơn (hướng phát triển số 2, mục 5.3). Đây là ví dụ điển hình cho việc đo đạc thay thế trực giác.

Hiện tượng chữ số 4 bị nhận diện thành chữ cái L chiếm tần suất cao (53 ca, đứng hạng 3 trong tổng số lỗi thay thế, Bảng 4.6) là một phát hiện thị giác đặc thù của bài toán ALPR trên ảnh độ phân giải thấp. Theo chuẩn font chữ dập nổi của biển số Việt Nam, nét gạch ngang của số 4 có độ dày nhỏ hơn nét sổ dọc. Dưới điều kiện chụp xa, bám bụi hoặc bị ánh sáng tán xạ làm giảm tương phản cục bộ, nét gạch ngang này dễ bị mờ nhòe hoặc đứt đoạn sau bước nhị phân hóa nội bộ của OCR. Khi đó, cấu trúc còn lại chỉ gồm một nét sổ đứng và một đoạn chân ngang bên phải, khiến mô hình trích xuất đặc trưng hiểu nhầm thành chữ L viết hoa.

### 4.3.4. So sánh ba bộ nhận dạng trên cùng một tầng bao quanh

Câu hỏi: chọn PaddleOCR có đúng không, khi một số tài liệu công khai lại nghiêng về EasyOCR?

**Thiết kế thí nghiệm.** Cả ba bộ nhận dạng chạy trong **đúng một tầng bao quanh** — toàn bộ chuỗi bước xử lý ảnh bọc quanh bộ nhận dạng, đúng như cấu hình triển khai — trên **cùng một mảng 2.801 vùng biển đã chuẩn bị xong**; khác biệt duy nhất còn lại là bộ nhận dạng. So sánh ba bộ nhận dạng với ba tầng bao quanh khác nhau là đo tầng bao quanh chứ không đo bộ nhận dạng (Bảng 4.7).

**Bảng 4.7.**[]{#tbl-4-7} So sánh ba bộ nhận dạng trên 2.801 biển số Việt Nam

| Bộ nhận dạng | Tắt bước tách-ghép | Có tách-ghép | + hậu xử lý | Riêng biển 2 dòng |
|---|---:|---:|---:|---:|
| **PaddleOCR** | 28,81% | **63,73%** | **68,87%** | **62,3%** |
| EasyOCR | 6,53% | 10,35% | 14,28% | 10,7% |
| Tesseract | 9,57% | 9,60% | 10,28% | **0,1%** |

**PaddleOCR cao hơn hẳn trong phép đo này** — 68,87%, hơn EasyOCR 54,59 điểm và hơn Tesseract 58,59 điểm; khoảng cách quá lớn để quy cho nhiễu, nhưng kết luận chỉ áp cho cấu hình đánh giá nêu ở đoạn *Thiết kế thí nghiệm* trên.

**Tesseract không đọc được biển hai dòng**: **0,1% trên 2.234 mẫu**, kể cả sau khi đã ghép thành một dòng, trong khi đọc được 50,4% biển một dòng. Đã kiểm bằng mắt để loại khả năng lỗi công cụ — nó **có** đọc ra chữ nhưng luôn xuất hiện ký tự nhiễu / ký tự giả mạo, và 700/2.801 lần trả chuỗi rỗng.

**Kết quả ngoài dự đoán nhất — bước tách-ghép KHÔNG độc lập bộ nhận dạng:**

| Bộ nhận dạng | Mức tăng nhờ tách-ghép |
|---|---:|
| PaddleOCR | **+34,92 điểm** |
| EasyOCR | +3,82 điểm |
| Tesseract | **+0,03 điểm** |

Nếu cả ba cùng tăng mạnh, đóng góp kỹ thuật ở mục 3.4.5 sẽ là một kỹ thuật độc lập bộ nhận dạng — một khẳng định mạnh hơn nhiều. **Dữ liệu không cho phép nói thế.** Phát biểu đúng là: tách rồi ghép ngang là **điều kiện cần** để đọc biển hai dòng — nó biến bài toán đa dòng thành bài toán một dòng — nhưng **không đủ**; bộ nhận dạng vẫn phải đủ mạnh để tận dụng dải ảnh đã ghép.

Ngược lại, **bộ luật hậu xử lý giúp cả ba** (+5,14 · +3,93 · +0,68 điểm), nên riêng nó **là** một đóng góp độc lập bộ nhận dạng.

## 4.4. Bóc tách đóng góp của từng bước xử lý ảnh

Mục này là lý do các bước ở mục 3.4 được thiết kế bật tắt độc lập.

### 4.4.1. Ghép rồi đọc một lần, so với đọc riêng từng nửa

Thí nghiệm A/B trên **200 biển hai dòng** với hạt giống ngẫu nhiên cố định cho kết quả ở Bảng 4.8.

**Bảng 4.8.**[]{#tbl-4-8} Hai chiến lược đọc biển hai dòng

| Phương án | Đúng | Chuỗi rỗng | Thời gian |
|---|---:|---:|---:|
| **A — ghép ngang rồi đọc một lần** *(đang dùng)* | **129/200 = 64,50%** | 2 | 340,11 ms |
| B — đọc riêng từng nửa rồi nối chuỗi | **7/200 = 3,50%** | 9 | 391,35 ms |

**B kém A 61,00 điểm phần trăm và còn tốn thêm 51,24 ms**; trong 200 ca, 122 ca A thắng B và **0 ca B thắng A**. Kết quả bác bỏ dứt khoát giả thuyết "đọc riêng từng dòng thì chính xác hơn" và cho thấy chiến lược ghép ngang là **cần thiết** đối với biển hai dòng — cơ chế gây lỗi của phương án B đã phân tích ở mục 3.4.7.

### 4.4.2. Cơ chế thử lại đa tầng: Đánh đổi chi phí tính toán khi nhận dạng thêm 34 biển

Cơ chế thử lại đa tầng với hiệu chỉnh góc nghiêng và giãn dọc ở mục 3.4.6 cải thiện thêm **34 biển đọc đúng**. Cái giá đo được:

**Bảng 4.9.**[]{#tbl-4-9} Ảnh hưởng của cơ chế thử lại đa tầng lên độ trễ

| Chỉ số | Tắt cơ chế thử lại | Bật cơ chế thử lại *(cấu hình triển khai)* | Chênh |
|---|---:|---:|---:|
| p50 | 414,67 ms | 405,77 ms | **−8,90** |
| p95 | 866,3 ms | 1.143,10 ms | +276,80 |
| p99 | — | 1.420,07 ms | — |

Điểm đáng chú ý: **trung vị thậm chí giảm nhẹ.** Vì cơ chế thử lại chỉ chạy **sau khi lần đọc đầu thất bại**, nó không chạm vào trường hợp thường; toàn bộ chi phí dồn vào **đuôi phân bố**. Ở cấu hình đo của thí nghiệm này — **trước** đợt tối ưu tầng suy luận ở mục 4.5.2 — 95% ảnh xong dưới 1,15 giây và một nửa xong dưới 0,41 giây; p50 mô tả trải nghiệm điển hình còn p95 mô tả trường hợp xấu.

Đây là một **thoái lui có chủ ý và đã định lượng**: đổi 277 ms ở p95 lấy 34 biển đọc thêm.

### 4.4.3. Siêu phân giải: Đánh giá thực nghiệm bậc FSRCNN

Bậc thứ ba của cơ chế thử lại là **siêu phân giải** bằng mạng FSRCNN [15], dành cho vùng biển quá nhỏ. Kết quả đo ở **lượt bóc tách sớm** — một lượt đo riêng, trước lượt đo ở Bảng 4.9 và trên nền máy khác, nên số tuyệt đối không cộng trừ chéo được với Bảng 4.9:

| | Chi phí (lượt bóc tách sớm) | Lợi ích |
|---|---:|---:|
| Hiệu chỉnh góc nghiêng + giãn dọc | +244 ms p95 | **+34 biển** |
| **Siêu phân giải** | **+319 ms p95, +1.381 ms p99** | **0 biển** |

Ở lượt đó, bật cả ba bậc đẩy p95 lên **1.514,26 ms**, tức **vượt cả ngưỡng tối thiểu 1.500 ms**; bậc siêu phân giải vì vậy bị **tắt mặc định** và không có mặt trong cấu hình triển khai — Bảng 4.9 và mục 4.5.2 đều đo cấu hình đã tắt bậc này. Chi phí của hiệu chỉnh góc nghiêng + giãn dọc đo lại ở lượt Bảng 4.9 là +276,80 ms, hai lượt cho cùng kết luận.

**Nhưng số 0 đó phải đọc cho đúng, và đây là điểm phương pháp luận đáng nêu.** Cổng vào bậc siêu phân giải chỉ mở cho vùng cắt **nhỏ hơn 200 điểm ảnh**, và trong ngữ liệu đo **0 trên 120 mẫu lọt qua cổng đó**. Cần làm rõ sự khác biệt giữa hai con số thống kê: mẫu số 120 ảnh được đề cập ở đây là tập con các mẫu biển số được đưa vào kịch bản kiểm thử hiệu năng chuyên sâu của đường ống OCR; trong khi con số 262 đối tượng thuộc dải 'Rất nhỏ' tại Bảng 4.3 được thống kê trên toàn bộ tập kiểm thử tổng thể của mô hình phát hiện YOLO11n (nơi hộp bao chiếm dưới 0,5% diện tích khung ảnh 640x640). Trên tập con 120 mẫu thực nghiệm OCR, không có ảnh nào có chiều cao vùng cắt dưới ngưỡng 200 điểm ảnh, dẫn đến việc cổng kích hoạt FSRCNN không được mở trong lượt đo này. Nói cách khác, quyết định tắt dựa trên **"chi phí đã đo, lợi ích chưa ai đo được"** — không phải trên "đã đo và thấy vô dụng". Mã và công tắc vì vậy được **giữ nguyên**, để đo lại khi có ngữ liệu chứa biển thật sự nhỏ.

Phân biệt này quan trọng: một số 0 do *thiếu điều kiện quan sát* khác hẳn một số 0 do *đã quan sát và thấy bằng không*.

## 4.5. Hiệu năng

### 4.5.1. Phân rã ngân sách độ trễ

**Bảng 4.10.**[]{#tbl-4-10} Phân rã thời gian xử lý một biển số

| Bước | Đo được (ms) | % tổng |
|---|---:|---:|
| Giải mã ảnh và tiền xử lý | 1,78 | 1,2% |
| **Suy luận YOLO11n @ 640px** | **55,66** | **38,0%** |
| Cắt và tiền xử lý vùng biển | ~0,00 | 0,0% |
| **PaddleOCR (mỗi biển)** | **89,16** | **60,8%** |
| Hậu xử lý và kiểm tra hợp lệ | 0,03 | 0,0% |
| **Tổng suy luận thuần** | **146,63** | **100%** |

Ba nhận xét từ Bảng 4.10. **Một, điểm nghẽn là khối nhận dạng ký tự** (60,8%) chứ không phải bộ phát hiện (38,0%). Nguyên nhân: PaddleOCR là một **đường ống nhiều giai đoạn** — phát hiện văn bản, phân loại hướng, rồi mới nhận dạng — thiết kế cho ảnh tài liệu tổng quát, nên hệ thống trả chi phí cho những năng lực mà một vùng biển đã cắt sẵn không cần.

**Hai, toàn bộ khối xử lý ảnh của đồ án gần như miễn phí**: bước cắt và tiền xử lý vùng biển đo được xấp xỉ 0 ms, hậu xử lý 0,03 ms. Đóng góp +13,28 điểm ở mục 4.3.1 vì vậy đến với chi phí tính toán không đáng kể — một tỉ lệ lợi ích trên chi phí rất hiếm.

**Ba, chiến lược tối ưu suy ra trực tiếp từ bảng này.** Theo định luật Amdahl, tăng tốc bộ phát hiện gấp 2–3 lần chỉ kéo tổng xuống khoảng 15–23%; muốn giảm mạnh hơn thì khối nhận dạng (60,8%) mới là mục tiêu.

### 4.5.2. Độ trễ đầu cuối và các chỉ tiêu tài nguyên

Độ trễ một ảnh ở cấu hình triển khai: **p50 = 150,07 ms · p95 = 509,76 ms · p99 = 1.124,13 ms** — đo sau đợt tối ưu tầng suy luận (bật `torch.inference_mode()`, ghim số luồng cho torch và OpenCV, truyền `cpu_threads` xuống bộ nhận dạng). Bảng 4.9 ở trên đo **trước** đợt ấy, nên hai bộ số không được ghép chung: bảng ấy trả lời riêng câu hỏi cơ chế thử lại đa tầng đắt bao nhiêu. Chỉ tiêu p95 phát biểu ở mức ≤ 1.500 ms (tối thiểu) và ≤ 800 ms (mục tiêu), nên kết luận chính thức là **đạt cả mục tiêu**, với biên 290 ms. Con số này thay cho lượt đo trước tối ưu ở Bảng 4.9 (p95 = 1.143,10 ms), khi chỉ tiêu mới chỉ đạt ngưỡng tối thiểu.

Mọi chỉ tiêu **ngoài đường xử lý ảnh** đều đạt với biên rộng: nạp mô hình 6,41 s (ngưỡng 30 s); bộ nhớ thường trú 0,806 GB (ngưỡng 4 GB); truy vấn 10.000 bản ghi lịch sử 18,71 ms; chạy liên tục 15 phút với **100% thành công trên 5.337 yêu cầu**, **0 lỗi** — **không rò rỉ**.

### 4.5.3. Độ chính xác bộ phân loại màu nền

**Bảng 4.11.**[]{#tbl-4-11} Độ chính xác phân loại màu nền trên tập ngoài dữ liệu hiệu chỉnh

| Lớp nhãn người gán | Số ảnh | Đúng | Độ chính xác |
|---|---:|---:|---:|
| Biển vàng | 694 | 684 | **98,56%** |
| Biển trắng | 808 | 787 | **97,40%** |
| Biển xanh | 63 | 61 | **96,83%** |
| **Tổng** | **1.565** | **1.532** | **97,89%** |

Bảng 4.11 đo trên 1.565 ảnh ngoài dữ liệu hiệu chỉnh. Ba giới hạn phải nêu kèm. **Một,** 542 ảnh đã bị loại khỏi phép đo — toàn bộ lớp không xác định, cùng các ảnh chụp ban đêm hoặc hồng ngoại mà chính người gán nhãn cũng không xác định được màu. **Hai,** dạng lỗi chủ đạo là **biển trắng bị phân loại thành biển xanh** — 21 trong 33 ca sai — do một số điểm ảnh ám lạnh vượt ngưỡng bão hoà. **Ba,** bộ dữ liệu không chứa biển đỏ và biển ngoại giao nên hai nhánh này chưa có số liệu — ghi thành **hạn chế số 5** ở mục 5.2.

## 4.6. Phân tích lỗi

**Bảng 4.12.**[]{#tbl-4-12} Tần suất từng loại lỗi trên 2.801 mẫu, cấu hình triển khai


| Mã | Loại lỗi | Số ca | Tỉ lệ trong ca sai | Một dòng | Hai dòng |
|:---:|---|---:|---:|---:|---:|
| E1 | Nhầm ký tự _(thay thế)_ | 392 | 60,87% | 17 | 375 |
| E2 | Thiếu ký tự | 76 | 11,80% | 0 | 76 |
| E3 | Thừa ký tự | 20 | 3,11% | 5 | 15 |
| E4 | Sai thứ tự | 0 | 0,00% | 0 | 0 |
| E5 | Trả chuỗi rỗng | 10 | 1,55% | 0 | 10 |
| E6 | Hỗn hợp nhiều loại | 146 | 22,67% | 4 | 142 |
| | **Tổng ca sai** | **644** | **100%** | **26** | **618** |

> Không có lớp *bỏ sót biển* hay *phát hiện nhầm* vì cả 2.801 mẫu là **vùng biển đã cắt sẵn**, nên bước phát hiện không chạy; hai loại lỗi ấy được đo riêng ở tầng bộ phát hiện.

Bảng 4.12 khép lại mạch lập luận của chương. **Nhầm ký tự chiếm gần hai phần ba số ca sai, và 375 trên 392 ca thuộc biển hai dòng** — cùng một kết luận đã rút ra ở mục 4.3.2, nay xác nhận từ một góc đo khác.

**Sai thứ tự bằng 0** là bằng chứng trực tiếp cho thấy thiết kế ghép ngang ở mục 3.4.5 hoạt động đúng: nếu phép ghép đặt nhầm thứ tự hai nửa, hoặc nếu CTC vẫn đọc lộn xộn giữa hai dòng, loại lỗi này phải xuất hiện. Nó không xuất hiện một lần nào.

**Thiếu ký tự tập trung tuyệt đối ở biển hai dòng** (76/76), khớp với hồ sơ lỗi thiên về xoá ở mục 4.3.1 và với chế độ hỏng "mất hẳn dòng trên" mà mục 3.4.7 xử lý.

![](figures/fig-ch4-loi.png)

**Hình 4.2.**[]{#fig-4-2} Sáu vùng biển thật: ba ca khối hậu xử lý sửa được, ba ca vẫn sai

Hình 4.2 đặt các con số của Bảng 4.12 lên ảnh thật. Hàng trên là hai cơ chế sửa: mặt nạ vị trí của mục 3.6b (`2947872 → 29A7872`, `52126661 → 52L26661`) và bước phục hồi dòng trên của mục 3.4.7 (`5203 → 78N25203`). Hàng dưới là ba ca vẫn sai — cả ba đều là biển hai dòng và đều **hỏng ở dòng trên** (`30A → 37L`, `31F` mất hẳn, `52Z → 52T`): dòng trên trộn chữ và số ở đúng vị trí mà mặt nạ cho phép cả hai, nên hậu xử lý không có ràng buộc nào để bám vào. Đây là lý do hướng phát triển số 1 ở mục 5.3 nhắm vào bộ nhận dạng chứ không nhắm vào bộ luật.

Cần lưu ý về ảnh: ngữ liệu nhãn xuất mọi vùng cắt về khung vuông 640 × 640, **phá tỉ lệ khung hình gốc**. Hình trên đã khôi phục tỉ lệ bằng đúng hàm mà công cụ đo dùng trước khi chạy nhận dạng. Bước khôi phục này không phải chi tiết trình bày: bỏ nó đi thì S₁ rơi từ 0,7701 xuống **0,4988**, vì mọi vùng cắt vuông đều bị phân loại thành hai dòng.

## 4.7. Các yếu tố ảnh hưởng tới tính hợp lệ của kết quả

Nguyên tắc: nêu mối đe doạ, đánh giá mức nghiêm trọng, và nói rõ đã làm gì để giảm thiểu — **kể cả khi biện pháp là "không có"** (Bảng 4.13).

**Bảng 4.13.**[]{#tbl-4-13} Sáu yếu tố ảnh hưởng tới tính hợp lệ

| # | Yếu tố | Mức | Biện pháp đã áp dụng |
|:--:|---|:--:|---|
| 1 | **Rò rỉ dữ liệu tồn dư không khử được bằng băm tri giác** (mục 3.2.3) | Cao | Nâng ngưỡng gộp 5 → 10 và đo ở nhiều ngưỡng cao hơn. Vẫn còn 791 cặp ở ngưỡng 12; rò rỉ *ngữ nghĩa* **không ngưỡng nào phát hiện được** ⇒ mọi chỉ số ở mục 4.2 phải coi là **cận trên lạc quan** |
| 2 | **Tập kiểm thử không xuyên bộ dữ liệu** | Cao | **Không có.** Cách đúng là giữ lại một nguồn hoàn toàn không dùng để huấn luyện; chưa thực hiện |
| 3 | **Mẫu số nhỏ cho chỉ số nhận dạng** — 2.801 trên 15.133 ảnh có nhãn chuỗi | Cao | Công bố mẫu số ở mọi bảng; không rút kết luận từ chênh lệch nhỏ |
| 4 | **Bộ dữ liệu lệch nặng về biển trắng** — 97,68% mẫu | Cao | Nêu rõ: kết luận về độ chính xác nhận dạng **chỉ áp cho biển trắng** |
| 5 | Đo trên **một cấu hình phần cứng duy nhất** | Trung bình | Công bố cấu hình đầy đủ ở mục 4.1; **không ngoại suy** sang CPU hay hệ điều hành khác |
| 6 | **Một lượt huấn luyện duy nhất**, không ước lượng được phương sai | Trung bình | Cố định hạt giống để tái lập; không phát biểu so sánh dựa trên chênh lệch nhỏ |
