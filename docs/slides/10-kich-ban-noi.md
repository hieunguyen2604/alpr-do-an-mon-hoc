# KỊCH BẢN NÓI — BẢO VỆ 15 PHÚT

**24 slide · trung bình 36 giây mỗi slide · dồn thời lượng vào phần kết quả và đóng góp.**

Cột *giây* là ngân sách, không phải mục tiêu. Tổng cộng **14 phút 45 giây**, chừa 15 giây trôi.
Ba slide dài nhất — 15, 16, 17 — là ba slide mang toàn bộ giá trị học thuật của đồ án; nếu bị
trễ giờ, cắt slide 13 và 21 trước, **không cắt 16 và 17**.

Mọi con số dưới đây đã đối chiếu với quyển. Chỗ nào hội đồng có thể vặn, đã ghi kèm câu
phòng thủ trong khung *"nếu bị hỏi"*.

---

## Phần 1 — Tổng quan (slide 1–7, 3 phút 05 giây)

### Slide 1. Tiêu đề · 10 giây

> Em xin trình bày đồ án **"Xây dựng hệ thống nhận dạng biển số xe bằng trí tuệ nhân tạo"**.
> Nhóm thực hiện gồm Phạm Công Thành và Nguyễn Minh Hiếu, dưới sự hướng dẫn của
> ThS. Cáp Phạm Đình Thăng.

### Slide 2. Nội dung · 10 giây

> Bài trình bày gồm năm phần: tổng quan, cơ sở lý thuyết, thiết kế hệ thống, thực nghiệm và
> kết luận.

### Slide 3. Vì sao đề tài này · 40 giây

> Việt Nam có khoảng **77 triệu xe máy**, chiếm **85 đến 90%** lưu lượng đường bộ. Khác với
> nhiều nước, biển số xe máy Việt Nam là **biển hai dòng** — và đây là điểm khó chính của bài
> toán.
>
> Mức độ khó ấy đã được đo. Trên bộ dữ liệu RodoSol của Brazil, **cùng một hệ thống**
> OpenALPR, độ chính xác giảm từ **94,3%** xuống **45,7%** khi chuyển từ biển một dòng sang
> biển hai dòng. Hai nhóm ảnh chỉ khác nhau ở bố cục biển, nên chênh lệch **48,6 điểm** này
> quy được cho đúng một nguyên nhân.

> ⚠ **Nếu bị hỏi:** *"Sao lại dẫn số liệu Brazil?"* → Vì Brazil cũng có tỉ lệ xe máy cao, và
> đây là bộ dữ liệu công khai hiếm hoi **cân bằng có chủ ý** 4.000 ảnh mỗi loại bố cục. Em
> dẫn nó như một *analogue* định lượng, **không phải** số liệu Việt Nam — số liệu Việt Nam do
> nhóm tự đo, ở Chương 5.

### Slide 4. Đặc thù biển số Việt Nam · 35 giây

> Biển số Việt Nam có ba ràng buộc mà dữ liệu nước ngoài không dạy được.
>
> **Một**, mã tỉnh chỉ có **81 giá trị hợp lệ** trong dải 11 đến 99 — tám mã chưa từng cấp.
> **Hai**, tập ký tự sê-ri **phụ thuộc vị trí**: vị trí thứ nhất có `G` nhưng không có `R`,
> còn vị trí thứ hai của biển xe máy thì ngược lại. **Ba**, hệ thống có cả biển một dòng và
> hai dòng, phân biệt được bằng tỉ lệ khung hình.
>
> Chính ràng buộc thứ hai là lý do một hệ thống dùng danh sách ký tự phẳng sẽ **sai có hệ
> thống** trên toàn bộ lớp biển xe máy mang chữ `R`.

### Slide 5. Chọn hướng tiếp cận · 35 giây

> Nhóm chọn kiến trúc **hai giai đoạn**: YOLO11 phát hiện vùng biển, PaddleOCR đọc ký tự.
>
> Không chọn mô hình đầu-cuối vì hai lý do: dữ liệu có nhãn chuỗi hạn chế, và yêu cầu suy
> luận **hoàn toàn trên CPU**. Kiến trúc hai giai đoạn còn cho một lợi thế cho việc đánh giá:
> đo được **từng khối riêng**, nên định vị được điểm nghẽn.

### Slide 6. Chọn mô hình · 30 giây

> Sau khảo sát, nhóm chọn **YOLO11n** cho bước phát hiện và **PP-OCRv5 mobile** cho bước nhận
> dạng. Đây là phương án cân bằng giữa tốc độ, kích thước mô hình và độ chính xác trên CPU —
> mô hình nhận dạng chỉ **4,5 MB**.

> ⚠ **Nếu bị hỏi:** *"Vì sao không dùng bản lớn hơn?"* → Nhóm **đã đo**: PP-OCRv6 medium đọc
> đúng hơn 5,5 điểm nhưng **chậm gấp 16,8 lần**, đẩy độ trễ p95 vượt ngưỡng tối đa 1.500 ms.

### Slide 7. Mục tiêu đề tài · 25 giây

> Mục tiêu của nhóm: xây dựng hệ thống ALPR **hoàn chỉnh**, hỗ trợ cả hai loại bố cục biển,
> suy luận **hoàn toàn trên CPU**, và đạt các chỉ tiêu độ chính xác cùng hiệu năng đã đặt ra
> **từ giai đoạn phân tích yêu cầu** — chứ không phải đặt sau khi có kết quả.

---

## Phần 2 — Thiết kế hệ thống (slide 8–13, 3 phút 45 giây)

### Slide 8. Kiến trúc hệ thống · 35 giây

> Hệ thống gồm **năm tầng**: giao diện, API, nghiệp vụ, AI và dữ liệu, với luồng phụ thuộc
> một chiều nghiêm ngặt.
>
> Điểm đáng nói là **tầng AI tách hoàn toàn khỏi FastAPI** — mã đường ống AI không import
> framework web, và ràng buộc này được **kiểm chứng tự động** trong bộ kiểm thử. Nhờ đó kịch
> bản đo đạc dùng lại **đúng mã của bản giao hàng** thay vì sao chép.

### Slide 9. Pipeline AI · 35 giây

> Đường ống gồm năm bước: phát hiện biển, cắt vùng biển, xử lý theo bố cục một dòng hay hai
> dòng, nhận dạng ký tự, và hậu xử lý theo quy chuẩn.
>
> Hai khối tô đỏ — **xử lý biển hai dòng** và **hậu xử lý theo vị trí** — là hai đóng góp kỹ
> thuật chính của đồ án. Đây là hai khối **không có sẵn trong bất kỳ thư viện nào**.

### Slide 10. Xử lý biển hai dòng · 45 giây

> Bộ nhận dạng dựa trên kiến trúc CRNN với hàm mất mát CTC, vốn **giả định văn bản một dòng**:
> tầng tích chập hạ chiều cao về 1, biến ảnh thành một chuỗi theo chiều ngang. Ảnh hai dòng
> vi phạm giả định đó, nên hai dòng bị chồng vào cùng một cột đặc trưng.
>
> Giải pháp của nhóm: **tách hai nửa có chồng lấn, ghép ngang thành một dải, rồi mới đọc một
> lần**. Cách này chuyển bài toán đa dòng về bài toán một dòng mà mô hình vốn xử lý được.

> ⚠ **Nếu bị hỏi:** *"Sao không đọc riêng từng dòng rồi nối?"* → Nhóm **đã đo A/B** trên 200
> biển: ghép ngang đạt **64,5%**, đọc riêng chỉ **3,5%**, thắng ở **0 trên 200** trường hợp.
> Nguyên nhân: vùng chồng lấn bị đọc **hai lần** khi tách riêng.

### Slide 11. Hậu xử lý theo vị trí · 45 giây

> Đây là đóng góp kỹ thuật thứ nhất. Thay vì sửa lỗi trên toàn chuỗi bằng một danh sách ký tự
> phẳng, hệ thống sửa **theo từng vị trí**: hai ký tự đầu phải thuộc 81 mã tỉnh; ký tự sê-ri
> phải thuộc đúng tập của vị trí đó; các vị trí còn lại phải là chữ số.
>
> Điểm đáng nói nhất là bảng ánh xạ nhầm lẫn **không đối xứng**: `O` sửa thành `0` ở vị trí
> chữ số là hợp lý, nhưng `0` sửa thành `O` thì **không bao giờ**, vì `O` không thuộc tập
> sê-ri hợp lệ.

### Slide 12. Bộ dữ liệu · 40 giây

> Nhóm hợp nhất **bảy bộ dữ liệu công khai**, còn **15.133 ảnh** sau khi làm sạch. Quá trình
> khử trùng lặp loại **44,2%** số ảnh — con số này tự nó là một phát hiện: các bộ Roboflow tái
> sử dụng ảnh của nhau rất nặng, có bộ bị loại **100%**.
>
> Dữ liệu chia train, validation và test theo tỉ lệ 70-20-10, và phép chia **có kiểm soát rò
> rỉ** giữa các tập.

> ⚠ **Nếu bị hỏi:** *"Còn rò rỉ không?"* → Còn, và quyển ghi thẳng: ở ngưỡng Hamming 12 vẫn
> còn **791 cặp**. Băm tri giác không phát hiện được rò rỉ *ngữ nghĩa* — cùng một xe chụp
> khác góc. Vì vậy mọi chỉ số phát hiện phải đọc như **cận trên lạc quan**.

### Slide 13. Huấn luyện · 25 giây

> Mô hình YOLO11n huấn luyện ở độ phân giải **640**, **20 epoch**, **hoàn toàn trên CPU**,
> tổng thời gian **khoảng 10 giờ**. Đường cong huấn luyện không có dấu hiệu quá khớp, và chỉ
> số trên tập kiểm định bão hoà sớm.

---

## Phần 3 — Kết quả thực nghiệm (slide 14–22, 6 phút 35 giây)

### Slide 14. Kết quả phát hiện · 45 giây

> Bộ phát hiện đạt **mAP@0.5 bằng 0,9829**, precision **0,9837**, recall **0,9714** — **đạt
> toàn bộ bốn chỉ tiêu** đã đặt ra, với biên rộng.
>
> Một lưu ý về cách đọc con số này: bài toán chỉ có **một lớp**, nên mAP một lớp **không so
> trực tiếp được** với mAP nhiều lớp trên COCO. Giá trị cao ở đây là bình thường, không phải
> bằng chứng về độ khó đã vượt qua.

### Slide 15. Kết quả OCR · 60 giây

> Khối nhận dạng đạt **1 trừ CER bằng 94,83%** ở mức ký tự. Nhưng ở mức **chuỗi đầy đủ** —
> tức đọc đúng **toàn bộ** biển — chỉ đạt **77,01%** sau hậu xử lý.
>
> Con số này **chưa đạt cả ngưỡng tối thiểu 85%**, chứ chưa nói mục tiêu 90%. Nhóm ghi nhận
> đây là **nút thắt chính** của hệ thống hiện nay.
>
> Khoảng cách giữa hai con số ấy có lý do toán học: với biển tám ký tự, nếu xác suất đọc đúng
> mỗi ký tự là *p* thì xác suất đúng cả chuỗi là *p* mũ 8. Sai một ký tự là hỏng cả bản ghi.

### Slide 16. So sánh biển một dòng và hai dòng · 60 giây

> **Đây là kết quả quan trọng nhất của đồ án.**
>
> Biển một dòng đạt **95,41%**. Biển hai dòng chỉ **72,34%**. Chênh lệch **23,07 điểm phần
> trăm** — trong khi biển hai dòng chiếm **79,8%** tập đánh giá.
>
> Con số này định vị chính xác điểm nghẽn. Ở **tầng phát hiện**, chênh lệch giữa hai bố cục
> chỉ **2,09 điểm**; ở **tầng nhận dạng** là **23,07 điểm**. Nghĩa là rủi ro nằm **trọn** ở
> khối đọc ký tự, không ở khối phát hiện.

### Slide 17. Đóng góp của hậu xử lý · 60 giây

> Đây là đóng góp định lượng rõ nhất của đề tài.
>
> Độ chính xác chuỗi tăng từ **63,73%** lên **77,01%** — **cộng 13,28 điểm phần trăm**, sửa
> đúng **372 biển số**, và **không làm hỏng trường hợp nào**.
>
> Con số "không làm hỏng trường hợp nào" **không phải may mắn**, mà là **tính chất cấu trúc**
> của thiết kế: khối hậu xử lý chỉ can thiệp khi chuỗi đã **không hợp lệ**, nên tập bị can
> thiệp và tập đang đúng là hai tập **rời nhau**.
>
> Đo được con số này là nhờ một quyết định ở tầng dữ liệu: hệ thống **lưu song song** chuỗi
> OCR thô và chuỗi đã sửa.

### Slide 18. Ba can thiệp thực nghiệm · 40 giây

> Ngoài hậu xử lý, nhóm thực hiện thêm hai can thiệp: **phục hồi dòng trên** khi chuỗi mất
> cụm mã tỉnh, và **nắn hình chống méo** cho biển chụp nghiêng.
>
> Cả ba đều được **đo tách bạch**, và cả ba đều thoả cùng một ràng buộc: chỉ kích hoạt khi kết
> quả đã hỏng, nên **không làm hỏng thêm** trường hợp nào đang đúng.

### Slide 19. Hiệu năng trên CPU · 45 giây

> Phân rã thời gian suy luận cho thấy **OCR chiếm 60,8%**, còn tầng phát hiện chiếm **38,0%**.
>
> Kết quả này quan trọng vì nó **đảo ngược chiến lược tối ưu**: điểm nghẽn không nằm ở mô hình
> phát hiện như dự đoán ban đầu, mà ở khối đọc ký tự — và PaddleOCR đắt vì nó là đường ống
> nhiều giai đoạn thiết kế cho ảnh tài liệu tổng quát, trong khi vùng biển đã cắt không cần
> năng lực đó.

### Slide 20. Phân bố độ trễ · 25 giây

> Độ trễ **p95 đạt khoảng 510 mili-giây**, **vượt mục tiêu 800 mili-giây**. Trung vị chỉ 150
> mili-giây. Hệ thống đáp ứng yêu cầu chạy thời gian thực trên CPU.

### Slide 21. Kiểm thử và triển khai · 30 giây

> Hệ thống đạt **1004 trên 1004** kiểm thử tự động, bao phủ tầng nghiệp vụ **87,7%**, triển
> khai bằng **một lệnh Docker**, và chạy liên tục **5.337 yêu cầu không lỗi**.

### Slide 22. Tổng hợp chỉ tiêu · 30 giây

> Tổng hợp lại: **mọi chỉ tiêu phát hiện đều đạt**, **mọi chỉ tiêu hiệu năng đều đạt**, còn
> **chỉ tiêu độ chính xác chuỗi và đầu cuối thì chưa đạt**.
>
> Nhóm trình bày đầy đủ cả phần đạt lẫn phần không đạt, kèm nguyên nhân đã định vị được.

---

## Phần 4 — Kết luận (slide 23–24, 1 phút 20 giây)

### Slide 23. Hạn chế và hướng phát triển · 45 giây

> Ba hạn chế chính. **Một**, OCR trên biển hai dòng còn thấp. **Hai**, nhãn cho ảnh hiện
> trường do mô hình sinh chứ không phải người gán, nên chỉ số đầu cuối **56,3%** phải đọc kèm
> hạn chế này. **Ba**, chưa đánh giá xuyên bộ dữ liệu.
>
> Ba hướng tương ứng: huấn luyện lại bộ nhận dạng riêng cho biển số Việt Nam, xây dựng bộ nhãn
> do người gán, và dựng tập test xuyên bộ để đo tổng quát hoá.

### Slide 24. Kết luận · 35 giây

> Đồ án xây dựng thành công một hệ thống ALPR hoàn chỉnh **chạy trên CPU**, đạt độ chính xác
> phát hiện cao — **mAP@0.5 bằng 98,29%**.
>
> Đồ án **định lượng được đóng góp của khối hậu xử lý**: cộng **13,28 điểm**, sửa đúng 372
> biển, không làm hỏng biển nào.
>
> Và đồ án **chỉ ra rõ nút thắt hiện nay**: nhận dạng ký tự trên biển hai dòng.
>
> Em xin hết phần trình bày. Kính mời Hội đồng đặt câu hỏi.

---

## Ba câu hỏi gần như chắc chắn bị hỏi

| Câu hỏi | Trả lời gọn |
|---|---|
| **Vì sao A6 = 77,01% mà A7 chỉ 56,3%?** | Hai con số **không cùng mẫu**: A6 đo trên vùng biển cắt sẵn theo nhãn thật, A7 đo trên khung do chính bộ phát hiện tìm ra. Ba nguồn chênh lệch, xếp theo mức đóng góp: khối đọc trên biển hai dòng *(lớn nhất)*, chất lượng vùng cắt, và bỏ sót của bộ phát hiện *(nhỏ nhất — chỉ ~2,9%, vì recall 0,9714)*. |
| **Vì sao công trình MAPR 2021 đạt 99,28% còn đồ án 77,01%?** | Công trình ấy đo trên **bộ dữ liệu riêng không công khai** và **không công bố phân bố độ khó**. Hai tập có độ khó khác nhau thì hai con số **không cùng thang đo**. Phép so sánh hợp lệ đòi hai hệ thống chạy trên **cùng một tập kiểm tra**. |
| **Phần AI tự làm là gì, nếu OCR dùng model gốc?** | Bộ phát hiện **tự huấn luyện** trên dữ liệu Việt Nam. Đóng góp nằm ở **tầng hậu xử lý và tầng xử lý bố cục**, không ở tầng mô hình — và đó là lựa chọn **có căn cứ**: lượt tinh chỉnh bộ nhận dạng đã chạy, đã đo bốn cấu hình, và **thua model gốc 7,50 điểm** ở đúng chế độ vận hành. |
