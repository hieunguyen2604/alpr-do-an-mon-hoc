import os
import sys
import zipfile
import shutil
from PIL import Image, ImageDraw
import win32com.client

sys.stdout.reconfigure(encoding='utf-8')

def main():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    src_pptx = os.path.join(base_dir, "nop", "ALPR_Slides_Revised_19slides_schoolframe_v2.backup.pptx")
    target_pptx = os.path.join(base_dir, "nop", "ALPR_Slides_Revised_19slides_schoolframe_v2.pptx")
    figures_dir = os.path.join(base_dir, "docs", "slides", "figures")
    scratch_dir = os.path.join(base_dir, "scratch")
    os.makedirs(scratch_dir, exist_ok=True)
    
    # -------------------------------------------------------------
    # 1. Clean background master image (image-1002-1.png)
    # -------------------------------------------------------------
    layout_img_path = os.path.join(scratch_dir, "layout_image.png")
    clean_bg_path = os.path.join(scratch_dir, "clean_bg.png")
    
    with zipfile.ZipFile(src_pptx, 'r') as z:
        with open(layout_img_path, 'wb') as f:
            f.write(z.read('ppt/media/image-1002-1.png'))
                
    im = Image.open(layout_img_path).convert('RGBA')
    w, h = im.size
    draw = ImageDraw.Draw(im)
    # Fill bottom-left blue stack and circle with pure white
    draw.rectangle([0, int(h * 0.60), int(w * 0.055), h], fill=(255, 255, 255, 255))
    im.save(clean_bg_path)
    print("1. Clean background master image created successfully.")

    # -------------------------------------------------------------
    # 2. Patch zip images in target presentation
    # -------------------------------------------------------------
    replacements = {
        'ppt/media/image-1002-1.png': clean_bg_path,
        'ppt/media/image-8-1.png': os.path.join(figures_dir, 'fig-pipeline-strip-ngang.png'),
        'ppt/media/image-13-1.png': os.path.join(figures_dir, 'fig-ch4-layout.png'),
        'ppt/media/image-14-1.png': os.path.join(figures_dir, 'fig-ch4-loi.png'),
        'ppt/media/image-16-1.png': os.path.join(figures_dir, 'fig-slide-latency-amdahl.png'),
    }

    temp_zip = os.path.join(scratch_dir, "patched_deck.pptx")
    with zipfile.ZipFile(src_pptx, 'r') as zin:
        with zipfile.ZipFile(temp_zip, 'w', compression=zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                if item.filename in replacements:
                    rep_path = replacements[item.filename]
                    with open(rep_path, 'rb') as f:
                        zout.writestr(item.filename, f.read())
                else:
                    zout.writestr(item, zin.read(item.filename))
    
    shutil.copyfile(temp_zip, target_pptx)
    print("2. Zip patched and copied to target PPTX.")

    # -------------------------------------------------------------
    # 3. Use PowerPoint COM to edit shapes, typography, and positions
    # -------------------------------------------------------------
    ppt = win32com.client.Dispatch('PowerPoint.Application')
    pres = ppt.Presentations.Open(target_pptx, False, False, False)
    print(f"3. Opened presentation in PowerPoint COM. Slides: {pres.Slides.Count}")

    # Color definitions for COM (RGB integer: B*65536 + G*256 + R)
    RGB_NAVY  = 145*65536 + 75*256 + 0    # #004b91
    RGB_BLUE  = 199*65536 + 132*256 + 2   # #0284c7
    RGB_DARK  = 59*65536  + 41*256 + 30   # #1e293b
    RGB_MUTED = 139*65536 + 116*256 + 100 # #64748b
    RGB_GREEN = 105*65536 + 150*256 + 5   # #059669
    RGB_AMBER = 19*65536  + 138*256 + 217 # #d97706
    RGB_RED   = 38*65536  + 38*256 + 220  # #dc2626
    RGB_WHITE = 255*65536 + 255*256 + 255

    for s_idx in range(1, pres.Slides.Count + 1):
        s = pres.Slides(s_idx)
        
        # ---------------------------------------------------------
        # SLIDE 1: Bìa
        # ---------------------------------------------------------
        if s_idx == 1:
            to_del_s1 = ["Oval", "Text 3_Sep", "Shape 5", "Text 6"]
            for shp_idx in range(s.Shapes.Count, 0, -1):
                shp = s.Shapes(shp_idx)
                if any(k in shp.Name for k in to_del_s1):
                    shp.Delete()
                elif shp.HasTextFrame:
                    txt = shp.TextFrame.TextRange.Text.strip()
                    if "nhận diệnbiển" in txt:
                        shp.TextFrame.TextRange.Text = txt.replace("nhận diệnbiển", "nhận diện biển")

            shp_map = {shp.Name: shp for shp in s.Shapes}
            if "Text 3" in shp_map:
                txt3_left = shp_map["Text 3"]
                txt3_left.Top = 305
                txt3_left.Left = 190
                txt3_left.Width = 285
                txt3_left.Height = 46
                txt3_left.TextFrame.TextRange.ParagraphFormat.Alignment = 1
                txt3_left.TextFrame.TextRange.Text = "Phạm Nguyễn Thế Châu – 25410004\nNguyễn Minh Hiếu – 25410007"
                txt3_left.TextFrame.TextRange.Font.Name = "Segoe UI"
                txt3_left.TextFrame.TextRange.Font.Size = 13
                txt3_left.TextFrame.TextRange.Font.Bold = False
                txt3_left.TextFrame.TextRange.Font.Color.RGB = RGB_DARK

            if "Text 3_Right" not in shp_map:
                txt3_right = s.Shapes.AddTextbox(1, 495, 305, 285, 46)
                txt3_right.Name = "Text 3_Right"
            else:
                txt3_right = shp_map["Text 3_Right"]
            txt3_right.Top = 305
            txt3_right.Left = 495
            txt3_right.Width = 285
            txt3_right.Height = 46
            txt3_right.TextFrame.TextRange.ParagraphFormat.Alignment = 1
            txt3_right.TextFrame.TextRange.Text = "Nguyễn Công Hậu – 25410006\nPhạm Công Thành – 25410013"
            txt3_right.TextFrame.TextRange.Font.Name = "Segoe UI"
            txt3_right.TextFrame.TextRange.Font.Size = 13
            txt3_right.TextFrame.TextRange.Font.Bold = False
            txt3_right.TextFrame.TextRange.Font.Color.RGB = RGB_DARK

            if "Text 4" in shp_map:
                shp_map["Text 4"].Top = 365
                shp_map["Text 4"].Left = 200
                shp_map["Text 4"].Width = 560
                shp_map["Text 4"].Height = 25
                shp_map["Text 4"].TextFrame.TextRange.ParagraphFormat.Alignment = 2
                shp_map["Text 4"].TextFrame.TextRange.Font.Name = "Segoe UI"
                shp_map["Text 4"].TextFrame.TextRange.Font.Size = 13
                shp_map["Text 4"].TextFrame.TextRange.Font.Bold = False
                shp_map["Text 4"].TextFrame.TextRange.Font.Color.RGB = RGB_GRAY

            if "Text 7" in shp_map:
                shp_map["Text 7"].Top = 445
                shp_map["Text 7"].Left = 374.4
                shp_map["Text 7"].Width = 208.8
                shp_map["Text 7"].Height = 18.0

        # ---------------------------------------------------------
        # SLIDE 2: Nội dung
        # ---------------------------------------------------------
        elif s_idx == 2:
            for shp in s.Shapes:
                if shp.HasTextFrame:
                    txt = shp.TextFrame.TextRange.Text.strip()
                    if "tập trung vào đóng góp" in txt:
                        shp.TextFrame.TextRange.Text = "4 phần chính · Tập trung vào các phương pháp xử lý ảnh và quy chuẩn thực nghiệm"
                    elif txt == "Bài toán & mục tiêu" or "Mục tiêu nghiên cứu" in txt:
                        shp.TextFrame.TextRange.Text = "Bối cảnh & Mục tiêu nghiên cứu"
                    elif txt == "Phương pháp đề xuất":
                        shp.TextFrame.TextRange.Text = "Phương pháp đề xuất (Pipeline & Xử lý ảnh thích ứng)"
                    elif txt == "Kết quả thực nghiệm":
                        shp.TextFrame.TextRange.Text = "Kết quả thực nghiệm & Bóc tách đóng góp (Ablation)"
                    elif txt == "Kết luận & hướng phát triển":
                        shp.TextFrame.TextRange.Text = "Kết luận & Định hướng phát triển tương lai"

        # ---------------------------------------------------------
        # SLIDE 3: Bối cảnh & Thách thức bài toán
        # ---------------------------------------------------------
        elif s_idx == 3:
            # Delete old question container shapes if present
            to_del = ["Shape 5", "Text 6", "Text 7"]
            for i in range(s.Shapes.Count, 0, -1):
                if s.Shapes(i).Name in to_del:
                    s.Shapes(i).Delete()

            shp_names = [shp.Name for shp in s.Shapes]
            if "Text 5" not in shp_names:
                new_txt = s.Shapes.AddTextbox(1, 65, 380, 830, 55)
                new_txt.Name = "Text 5"

            shp_map = {shp.Name: shp for shp in s.Shapes}
            if "Text 0" in shp_map:
                shp_map["Text 0"].TextFrame.TextRange.Text = "Bối cảnh & Thách thức bài toán"
                shp_map["Text 0"].TextFrame.TextRange.Font.Name = "Segoe UI"
                shp_map["Text 0"].TextFrame.TextRange.Font.Size = 25
                shp_map["Text 0"].TextFrame.TextRange.Font.Bold = True
                shp_map["Text 0"].TextFrame.TextRange.Font.Color.RGB = RGB_NAVY
            if "Text 1" in shp_map:
                shp_map["Text 1"].TextFrame.TextRange.Text = "Đặc thù nhận diện biển số xe máy tại Việt Nam & Giới hạn của các mô hình hiện hành"
                shp_map["Text 1"].TextFrame.TextRange.Font.Name = "Segoe UI"
                shp_map["Text 1"].TextFrame.TextRange.Font.Size = 11.5
                shp_map["Text 1"].TextFrame.TextRange.Font.Bold = False
                shp_map["Text 1"].TextFrame.TextRange.Font.Color.RGB = RGB_GRAY

            s3_bullets = [
                (
                    "Text 2",
                    125,
                    "• Áp đảo về lưu lượng (Thực tế): Hơn 77 triệu xe máy (chiếm 85–90% phương tiện) → Biển số 2 dòng là đối tượng phục vụ cốt lõi tại Việt Nam, không phải ngoại lệ.",
                    "• Áp đảo về lưu lượng (Thực tế):"
                ),
                (
                    "Text 3",
                    210,
                    "• Thách thức hình học (Vật lý): Kích thước nhỏ (190 × 140 mm, AR = 1,357), ký tự bị ép 2 tầng → Thuộc nhóm đối tượng nhỏ (small objects) khó phát hiện và phân đoạn.",
                    "• Thách thức hình học (Vật lý):"
                ),
                (
                    "Text 4",
                    295,
                    "• Điều kiện ghi hình khắc nghiệt (Môi trường): Chịu chói lóa phản quang (retroreflection), góc chụp nghiêng, ngược sáng, biển số cong vênh và bám bụi bẩn.",
                    "• Điều kiện ghi hình khắc nghiệt (Môi trường):"
                ),
                (
                    "Text 5",
                    380,
                    "• Xung đột kiến trúc (Mô hình): Các bộ OCR phổ biến (CRNN/CTC) giả định văn bản 1 dòng ngang → Độ chính xác sụt giảm mạnh trên bố cục 2 dòng do gộp nhầm đặc trưng.",
                    "• Xung đột kiến trúc (Mô hình):"
                )
            ]

            for s_name, top_pos, text_content, pfx_str in s3_bullets:
                if s_name in shp_map:
                    shp = shp_map[s_name]
                    shp.Top = top_pos
                    shp.Left = 65
                    shp.Width = 830
                    shp.Height = 55
                    shp.TextFrame.VerticalAnchor = 1
                    shp.TextFrame.WordWrap = -1
                    shp.TextFrame.TextRange.Text = text_content
                    shp.TextFrame.TextRange.Font.Name = "Segoe UI"
                    shp.TextFrame.TextRange.Font.Size = 14.5
                    shp.TextFrame.TextRange.Font.Bold = False
                    shp.TextFrame.TextRange.Font.Color.RGB = RGB_DARK
                    p_len = len(pfx_str)
                    shp.TextFrame.TextRange.Characters(1, p_len).Font.Bold = True
                    shp.TextFrame.TextRange.Characters(1, p_len).Font.Color.RGB = RGB_BLUE

        # ---------------------------------------------------------
        # SLIDE 4: Mục tiêu & chỉ tiêu
        # ---------------------------------------------------------
        elif s_idx == 4:
            for shp in s.Shapes:
                if shp.HasTextFrame:
                    txt = shp.TextFrame.TextRange.Text.strip()
                    if txt == "Mục tiêu & chỉ tiêu":
                        shp.TextFrame.TextRange.Text = "Mục tiêu & Chỉ tiêu kỹ thuật"
                    elif "Hệ thống đầu cuối" in txt:
                        shp.TextFrame.TextRange.Text = "Hệ thống đầu cuối, suy luận hoàn toàn trên CPU, hỗ trợ chuẩn xác cả biển 1 dòng và 2 dòng"
                    elif txt == "mAP@0.5":
                        shp.TextFrame.TextRange.Text = "Độ chính xác phát hiện (mAP@0.5)"
                    elif txt == "Full-string sau hậu xử lý":
                        shp.TextFrame.TextRange.Text = "Độ chính xác toàn chuỗi (Full-sequence Accuracy)"
                    elif "Đúng mức ký tự" in txt:
                        shp.TextFrame.TextRange.Text = "Độ chính xác mức ký tự (1 − CER)"
                    elif "Latency p95" in txt:
                        shp.TextFrame.TextRange.Text = "Độ trễ suy luận p95 trên CPU (1 luồng)"
                    elif "Thiết kế ưu tiên" in txt:
                        shp.TextFrame.TextRange.Text = "Mục tiêu then chốt: Đảm bảo độ chính xác toàn chuỗi cao với độ trễ thực tế tối ưu trên CPU"

        # ---------------------------------------------------------
        # SLIDE 5: Pipeline
        # ---------------------------------------------------------
        elif s_idx == 5:
            for shp in s.Shapes:
                if shp.HasTextFrame:
                    txt = shp.TextFrame.TextRange.Text.strip()
                    if "Đóng góp chính nằm ở" in txt:
                        shp.TextFrame.TextRange.Text = "Đóng góp cốt lõi nằm ở hai khối: Xử lý ảnh thích ứng và Hậu xử lý tri thức chuyên miền"
                    elif "Deskew · Split" in txt:
                        shp.TextFrame.TextRange.Text = "Deskew · Tách–ghép dòng · CLAHE · Lọc song phương"
                    elif "PP-OCRv5 mobile" in txt:
                        shp.TextFrame.TextRange.Text = "PP-OCRv5 Mobile (Thuần CPU)"
                    elif "Luật biển số VN" in txt:
                        shp.TextFrame.TextRange.Text = "Kiểm tra 34 tỉnh · Mặt nạ vị trí · Ma trận hoán vị"
                    elif "Chuỗi chuẩn hóa" in txt:
                        shp.TextFrame.TextRange.Text = "Chuỗi biển số chuẩn hóa + Màu sắc & Loại xe"
                    elif "Không thay đổi mô hình OCR" in txt:
                        shp.TextFrame.TextRange.Text = "Không sửa đổi cấu trúc OCR → Tái cấu trúc hình học ảnh để tương thích tối ưu với OCR sẵn có"

        # ---------------------------------------------------------
        # SLIDE 6: Khử trùng lặp
        # ---------------------------------------------------------
        elif s_idx == 6:
            for shp in s.Shapes:
                if shp.HasTextFrame:
                    txt = shp.TextFrame.TextRange.Text.strip()
                    if "khử trùng lặp trước khi đo" in txt.lower():
                        shp.TextFrame.TextRange.Text = "Bộ dữ liệu: Khử trùng lặp trước khi đánh giá"
                    elif "Tránh “đo trí nhớ”" in txt:
                        shp.TextFrame.TextRange.Text = "Triệt tiêu rò rỉ dữ liệu (Data Leakage) khi các bộ dữ liệu công khai fork chéo lẫn nhau"
                    elif "Gộp từ 7 bộ công khai" in txt:
                        shp.TextFrame.TextRange.Text = "Gộp từ 7 bộ dữ liệu ALPR công khai"
                    elif "ảnh trùng bị loại" in txt:
                        shp.TextFrame.TextRange.Text = "ảnh trùng bị loại bằng pHash DCT 64-bit (Hamming ≤ 6)"
                    elif "15.133 ảnh còn lại" in txt:
                        shp.TextFrame.TextRange.Text = "15.133 ảnh độc lập (10.592 Train / 3.027 Val / 1.514 Test)"

        # ---------------------------------------------------------
        # SLIDE 7: CRNN Collapse
        # ---------------------------------------------------------
        elif s_idx == 7:
            for shp in s.Shapes:
                if shp.Name == "Shape 2":
                    shp.Left = 50.4
                    shp.Top = 115
                    shp.Width = 356.4
                    shp.Height = 300
                elif shp.HasTextFrame:
                    txt = shp.TextFrame.TextRange.Text.strip()
                    if "Vấn đề cốt lõi là hình học" in txt:
                        shp.TextFrame.TextRange.Text = "Hình học đầu vào vi phạm giả định thứ tự thời gian đơn điệu của hàm mất mát CTC Loss"
                    elif "Xung đột đặc trưng" in txt or txt == "Biển 2 dòng":
                        shp.Top = 125
                        shp.Left = 70
                        shp.Width = 320
                        shp.Height = 24
                        shp.TextFrame.VerticalAnchor = 1
                        shp.TextFrame.TextRange.Text = "Xung đột đặc trưng 2 dòng"
                        shp.TextFrame.TextRange.Font.Name = "Segoe UI"
                        shp.TextFrame.TextRange.Font.Size = 13.5
                        shp.TextFrame.TextRange.Font.Bold = True
                        shp.TextFrame.TextRange.Font.Color.RGB = RGB_RED
                    elif "H → 1 trong feature map" in txt or "Tầng CNN hạ chiều cao" in txt:
                        shp.Top = 155
                        shp.Left = 70
                        shp.Width = 320
                        shp.Height = 150
                        shp.TextFrame.VerticalAnchor = 1
                        shp.TextFrame.TextRange.Text = "• Tầng CNN hạ chiều cao H → 1 để tạo chuỗi 1D\n• Hai hàng ký tự bị ép chung cột đặc trưng t\n• Phá vỡ giả định đơn điệu của CTC Loss\n• OCR đọc nhảy dòng, nuốt chữ hoặc sinh rác"
                        shp.TextFrame.TextRange.Font.Name = "Segoe UI"
                        shp.TextFrame.TextRange.Font.Size = 11.5
                        shp.TextFrame.TextRange.Font.Color.RGB = RGB_DARK
                    elif "Giải pháp:" in txt:
                        shp.Top = 325
                        shp.Left = 70
                        shp.Width = 320
                        shp.Height = 65
                        shp.TextFrame.VerticalAnchor = 1
                        shp.TextFrame.TextRange.Text = "Giải pháp: Biến đổi hình học đưa về 1 dòng ngang chuẩn hóa trước khi đưa vào OCR"
                        shp.TextFrame.TextRange.Font.Name = "Segoe UI"
                        shp.TextFrame.TextRange.Font.Size = 11.5
                        shp.TextFrame.TextRange.Font.Bold = True
                        shp.TextFrame.TextRange.Font.Color.RGB = RGB_NAVY

        # ---------------------------------------------------------
        # SLIDE 8: Chuẩn hóa biển 2 dòng
        # ---------------------------------------------------------
        elif s_idx == 8:
            for shp in s.Shapes:
                if shp.HasTextFrame:
                    txt = shp.TextFrame.TextRange.Text.strip()
                    if "Từ heuristic hình học" in txt:
                        shp.TextFrame.TextRange.Text = "Chuỗi 5 phép biến đổi hình học giúp chuẩn hóa biển 2 dòng thành 1 dòng chất lượng cao"
                    elif txt == "Phân loại 1 / 2 dòng":
                        shp.TextFrame.TextRange.Text = "Phân loại 1 / 2 dòng"
                    elif txt == "Aspect ratio":
                        shp.TextFrame.TextRange.Text = "Ngưỡng AR = 2,50 (khoảng cách rộng giữa 1,36 và 4,73)"
                    elif txt == "Deskew":
                        shp.TextFrame.TextRange.Text = "Nắn phẳng Affine"
                    elif txt == "minAreaRect":
                        shp.TextFrame.TextRange.Text = "Tìm góc xoay tối ưu bằng cv2.minAreaRect"
                    elif txt == "Tách hai dòng":
                        shp.TextFrame.TextRange.Text = "Tách hai dòng ổn định"
                    elif "tỉ lệ cắt khảo sát" in txt:
                        shp.TextFrame.TextRange.Text = "Cắt cố định 5/12 trên & 1/3 dưới, loại ốc vít tim biển"
                    elif txt == "Ghép ngang":
                        shp.TextFrame.TextRange.Text = "Ghép ngang nối tiếp"
                    elif "top + bottom" in txt:
                        shp.TextFrame.TextRange.Text = "Dòng trên + dòng dưới → Chuỗi 1 dòng duy nhất"
                    elif "CLAHE" in txt:
                        shp.Width = 200
                        shp.TextFrame.TextRange.Text = "CLAHE & Lọc song phương"
                    elif "tăng tương phản" in txt.lower():
                        shp.Left = 305
                        shp.Width = 160
                        shp.TextFrame.TextRange.Text = "Tăng tương phản cục bộ, khử nhiễu mà bảo toàn nét chữ"

        # ---------------------------------------------------------
        # SLIDE 9: Hậu xử lý theo vị trí
        # ---------------------------------------------------------
        elif s_idx == 9:
            for shp in s.Shapes:
                if shp.HasTextFrame:
                    txt = shp.TextFrame.TextRange.Text.strip()
                    if "Không dùng luật “phẳng”" in txt:
                        shp.TextFrame.TextRange.Text = "Khai thác quy chuẩn Việt Nam (TT 79/2024 & TT 51/2025) theo từng vị trí ký tự trong chuỗi"
                    elif txt == "Mã tỉnh":
                        shp.TextFrame.TextRange.Text = "1. Danh mục 34 Mã địa phương"
                    elif "Chỉ giữ mã tỉnh hợp lệ" in txt:
                        shp.TextFrame.TextRange.Text = "Rà soát theo 34 tỉnh/thành hợp lệ (TT 51/2025); loại bỏ hoàn toàn các mã giả lập không tồn tại"
                    elif txt == "Mặt nạ vị trí":
                        shp.TextFrame.TextRange.Text = "2. Mặt nạ cú pháp định dạng"
                    elif "Xác định vị trí số / chữ" in txt:
                        shp.TextFrame.TextRange.Text = "Ràng buộc nghiêm ngặt vị trí số và chữ theo quy chuẩn DD-L DDD.DD hoặc DD-L? DDD.DD"
                    elif txt == "Tập seri":
                        shp.TextFrame.TextRange.Text = "3. Tập ký tự seri theo loại xe"
                    elif "Luật khác nhau theo loại biển" in txt:
                        shp.TextFrame.TextRange.Text = "Xe con không chứa ký tự 'R'; xe máy phân biệt rõ 'G' và 'R' ở từng vị trí seri"
                    elif txt == "Confusion map":
                        shp.TextFrame.TextRange.Text = "4. Ma trận hoán vị bất đối xứng"
                    elif "Sửa nhầm lẫn theo chiều hợp lý" in txt:
                        shp.TextFrame.TextRange.Text = "Sửa lỗi OCR có định hướng: 'O','D' → '0' khi ở vị trí số; '0' → 'D' khi ở vị trí chữ"
                    elif "Ví dụ:" in txt:
                        shp.TextFrame.TextRange.Text = "Ví dụ thực tế: Tại vị trí số, 'O' được sửa thành '0'; nhưng tại vị trí chữ, '0' được sửa thành 'D' chứ không sửa thành 'O' để bảo toàn tính hợp lệ."

        # ---------------------------------------------------------
        # SLIDE 10: Màu nền HSV
        # ---------------------------------------------------------
        elif s_idx == 10:
            for shp in s.Shapes:
                if shp.HasTextFrame:
                    txt = shp.TextFrame.TextRange.Text.strip()
                    if "Tách sắc độ H khỏi độ sáng V" in txt:
                        shp.TextFrame.TextRange.Text = "Tách sắc độ H khỏi độ sáng V để phân loại bền vững dưới bóng râm và chói lóa"
                    elif "độ chính xác tổng thể" in txt:
                        shp.TextFrame.TextRange.Text = "Độ chính xác phân loại tổng thể (1.565 mẫu)"
                    elif "Nhận diện màu nền" in txt:
                        shp.TextFrame.TextRange.Text = "Nhận diện 4 nhóm màu chuẩn:\nTrắng (97,4%) · Vàng (98,6%) · Xanh (96,8%) · Đỏ"

        # ---------------------------------------------------------
        # SLIDE 11: Nắn nghiêng Deskew
        # ---------------------------------------------------------
        elif s_idx == 11:
            for shp in s.Shapes:
                if shp.HasTextFrame:
                    txt = shp.TextFrame.TextRange.Text.strip()
                    if "Chỉ kích hoạt khi cần" in txt:
                        shp.TextFrame.TextRange.Text = "Chiến lược Fallback Ladder: Chỉ kích hoạt khi cần để tăng độ chính xác mà không làm chậm p50"
                    elif "biển được cứu thêm" in txt:
                        shp.TextFrame.TextRange.Text = "Biển số nghiêng được cứu thành công"
                    elif "Chi phí +277 ms" in txt:
                        shp.TextFrame.TextRange.Text = "Chi phí +277 ms (dồn vào đuôi p95)\np50 giữ nguyên 405 ms (+0 ms) cho phần lớn mẫu dễ"

        # ---------------------------------------------------------
        # SLIDE 12: Kết quả đo được (SỬA LỖI ĐẠ T / CHƯA ĐẠ T)
        # ---------------------------------------------------------
        elif s_idx == 12:
            for shp in s.Shapes:
                if shp.HasTextFrame:
                    txt = shp.TextFrame.TextRange.Text.strip()
                    if "Detection và latency đạt mục tiêu" in txt:
                        shp.TextFrame.TextRange.Text = "Phát hiện và độ trễ đạt xuất sắc mục tiêu; độ chính xác toàn chuỗi phản ánh trung thực bài toán"
                    elif "0,90" in txt and ("ĐẠ" in txt or "ĐẠT" in txt):
                        shp.TextFrame.TextRange.Text = "ĐẠT mục tiêu 0,90"
                        shp.TextFrame.TextRange.Font.Name = "Segoe UI"
                        shp.TextFrame.TextRange.Font.Bold = True
                        shp.TextFrame.TextRange.Font.Size = 10
                        shp.TextFrame.TextRange.Font.Color.RGB = RGB_GREEN
                    elif txt in ["ĐẠ T", "ĐẠT"]:
                        shp.TextFrame.TextRange.Text = "ĐẠT"
                        shp.TextFrame.TextRange.Font.Name = "Segoe UI"
                        shp.TextFrame.TextRange.Font.Bold = True
                        shp.TextFrame.TextRange.Font.Size = 10
                        shp.TextFrame.TextRange.Font.Color.RGB = RGB_GREEN
                    elif "0,85" in txt and ("CHƯA" in txt or "ĐẠ" in txt):
                        shp.TextFrame.TextRange.Text = "CHƯA ĐẠT ngưỡng 0,85"
                        shp.TextFrame.TextRange.Font.Name = "Segoe UI"
                        shp.TextFrame.TextRange.Font.Bold = True
                        shp.TextFrame.TextRange.Font.Size = 10
                        shp.TextFrame.TextRange.Font.Color.RGB = RGB_RED
                    elif "800" in txt and ("ĐẠ" in txt or "ĐẠT" in txt):
                        shp.TextFrame.TextRange.Text = "ĐẠT mục tiêu ≤ 800 ms"
                        shp.TextFrame.TextRange.Font.Name = "Segoe UI"
                        shp.TextFrame.TextRange.Font.Bold = True
                        shp.TextFrame.TextRange.Font.Size = 10
                        shp.TextFrame.TextRange.Font.Color.RGB = RGB_GREEN
                    elif txt == "mAP@0.5":
                        shp.TextFrame.TextRange.Text = "mAP@0.5 (Phát hiện)"
                    elif txt == "Full-string sau xử lý":
                        shp.TextFrame.TextRange.Text = "Độ chính xác toàn chuỗi"
                    elif txt == "Precision / Recall":
                        shp.TextFrame.TextRange.Text = "Precision / Recall"
                    elif txt == "Latency p95 / CPU":
                        shp.TextFrame.TextRange.Text = "Độ trễ p95 trên CPU"
                    elif "Điểm nghẽn còn lại" in txt:
                        shp.TextFrame.TextRange.Text = "Nhận định khách quan: Hệ thống tối ưu xuất sắc trên CPU; khoảng cách độ chính xác tập trung ở biển hai dòng."

        # ---------------------------------------------------------
        # SLIDE 13: Khoảng cách biển 2 dòng
        # ---------------------------------------------------------
        elif s_idx == 13:
            for shp in s.Shapes:
                if shp.HasTextFrame:
                    txt = shp.TextFrame.TextRange.Text.strip()
                    if "Mức ký tự gần nhau" in txt:
                        shp.TextFrame.TextRange.Text = "Độ chính xác mức ký tự gần bằng nhau, nhưng sai số tích lũy trên chuỗi phân hóa rất lớn"
                    elif "Main bottleneck" in txt:
                        shp.TextFrame.TextRange.Text = "Điểm nghẽn cốt lõi: Biển hai dòng"
                        shp.TextFrame.TextRange.Font.Name = "Segoe UI"
                        shp.TextFrame.TextRange.Font.Bold = True
                        shp.TextFrame.TextRange.Font.Size = 11
                        shp.Left = 85
                        shp.Width = 295
                elif shp.Type == 13: # Picture
                    shp.Left = 440
                    shp.Top = 105
                    shp.Width = 475
                    shp.Height = 345
                elif shp.Name == "Shape 7":
                    shp.Left = 80
                    shp.Width = 305

        # ---------------------------------------------------------
        # SLIDE 14: Lỗi thực tế (Xóa badges che phủ ảnh)
        # ---------------------------------------------------------
        elif s_idx == 14:
            # Delete overlapping badges so plate captions are completely clear
            for shp_idx in range(s.Shapes.Count, 0, -1):
                shp = s.Shapes(shp_idx)
                if shp.Name in ["Shape 2", "Shape 4"] or (shp.HasTextFrame and ("sửa đúng nhờ hậu xử lý" in shp.TextFrame.TextRange.Text or "vẫn sai" in shp.TextFrame.TextRange.Text)):
                    shp.Delete()
            
            for shp in s.Shapes:
                if shp.Type == 13: # Picture
                    shp.Left = 70
                    shp.Top = 100
                    shp.Width = 820
                    shp.Height = 360
                elif shp.HasTextFrame:
                    txt = shp.TextFrame.TextRange.Text.strip()
                    if "Hậu xử lý sửa được nhiều lỗi OCR" in txt:
                        shp.TextFrame.TextRange.Text = "Hậu xử lý cứu được nhiều ca OCR thô; các ca còn sai tập trung ở dòng trên của biển hai dòng"

        # ---------------------------------------------------------
        # SLIDE 15: Bóc tách đóng góp (Ablation - 3 đóng góp chính)
        # ---------------------------------------------------------
        elif s_idx == 15:
            # Xóa bỏ card 4 (Siêu phân giải) và 2 nhãn nhóm cũ
            names_to_delete = ["Text 2", "Text 11", "Shape 16", "Text 17", "Text 18", "Text 19"]
            for i in range(s.Shapes.Count, 0, -1):
                shp = s.Shapes(i)
                if shp.Name in names_to_delete:
                    shp.Delete()

            shape_map = {shp.Name: shp for shp in s.Shapes}

            # Phụ đề
            if "Text 1" in shape_map:
                shape_map["Text 1"].TextFrame.TextRange.Text = "Đánh giá độc lập mức độ cải thiện của từng phương pháp xử lý ảnh và hậu xử lý trên tập đo"

            # Card 1: Tách - ghép dòng
            if "Shape 3" in shape_map:
                shape_map["Shape 3"].Left = 50
                shape_map["Shape 3"].Top = 130
                shape_map["Shape 3"].Width = 260
                shape_map["Shape 3"].Height = 195
            if "Text 4" in shape_map:
                t = shape_map["Text 4"]
                t.Left = 55; t.Top = 150; t.Width = 250; t.Height = 45
                t.TextFrame.TextRange.Text = "+34,92 pp"
                t.TextFrame.TextRange.Font.Name = "Segoe UI"
                t.TextFrame.TextRange.Font.Size = 30
                t.TextFrame.TextRange.Font.Bold = True
                t.TextFrame.TextRange.Font.Color.RGB = RGB_BLUE
                t.TextFrame.TextRange.ParagraphFormat.Alignment = 2
            if "Text 5" in shape_map:
                t = shape_map["Text 5"]
                t.Left = 55; t.Top = 210; t.Width = 250; t.Height = 35
                t.TextFrame.TextRange.Text = "Tách–ghép dòng (Split-Merge)"
                t.TextFrame.TextRange.Font.Name = "Segoe UI"
                t.TextFrame.TextRange.Font.Size = 13
                t.TextFrame.TextRange.Font.Bold = True
                t.TextFrame.TextRange.Font.Color.RGB = RGB_DARK
                t.TextFrame.TextRange.ParagraphFormat.Alignment = 2
            if "Text 6" in shape_map:
                t = shape_map["Text 6"]
                t.Left = 55; t.Top = 265; t.Width = 250; t.Height = 30
                t.TextFrame.TextRange.Text = "Đột phá hình học biển 2 dòng"
                t.TextFrame.TextRange.Font.Name = "Segoe UI"
                t.TextFrame.TextRange.Font.Size = 11
                t.TextFrame.TextRange.Font.Bold = True
                t.TextFrame.TextRange.Font.Color.RGB = RGB_BLUE
                t.TextFrame.TextRange.ParagraphFormat.Alignment = 2

            # Card 2: Hậu xử lý
            if "Shape 7" in shape_map:
                shape_map["Shape 7"].Left = 350
                shape_map["Shape 7"].Top = 130
                shape_map["Shape 7"].Width = 260
                shape_map["Shape 7"].Height = 195
            if "Text 8" in shape_map:
                t = shape_map["Text 8"]
                t.Left = 355; t.Top = 150; t.Width = 250; t.Height = 45
                t.TextFrame.TextRange.Text = "+13,28 pp"
                t.TextFrame.TextRange.Font.Name = "Segoe UI"
                t.TextFrame.TextRange.Font.Size = 30
                t.TextFrame.TextRange.Font.Bold = True
                t.TextFrame.TextRange.Font.Color.RGB = RGB_GREEN
                t.TextFrame.TextRange.ParagraphFormat.Alignment = 2
            if "Text 9" in shape_map:
                t = shape_map["Text 9"]
                t.Left = 355; t.Top = 210; t.Width = 250; t.Height = 35
                t.TextFrame.TextRange.Text = "Hậu xử lý tri thức chuyên miền"
                t.TextFrame.TextRange.Font.Name = "Segoe UI"
                t.TextFrame.TextRange.Font.Size = 13
                t.TextFrame.TextRange.Font.Bold = True
                t.TextFrame.TextRange.Font.Color.RGB = RGB_DARK
                t.TextFrame.TextRange.ParagraphFormat.Alignment = 2
            if "Text 10" in shape_map:
                t = shape_map["Text 10"]
                t.Left = 355; t.Top = 265; t.Width = 250; t.Height = 30
                t.TextFrame.TextRange.Text = "0 ca sửa sai (An toàn 100%)"
                t.TextFrame.TextRange.Font.Name = "Segoe UI"
                t.TextFrame.TextRange.Font.Size = 11
                t.TextFrame.TextRange.Font.Bold = True
                t.TextFrame.TextRange.Font.Color.RGB = RGB_GREEN
                t.TextFrame.TextRange.ParagraphFormat.Alignment = 2

            # Card 3: Nắn phẳng Deskew
            if "Shape 12" in shape_map:
                shape_map["Shape 12"].Left = 650
                shape_map["Shape 12"].Top = 130
                shape_map["Shape 12"].Width = 260
                shape_map["Shape 12"].Height = 195
            if "Text 13" in shape_map:
                t = shape_map["Text 13"]
                t.Left = 655; t.Top = 150; t.Width = 250; t.Height = 45
                t.TextFrame.TextRange.Text = "+34 biển"
                t.TextFrame.TextRange.Font.Name = "Segoe UI"
                t.TextFrame.TextRange.Font.Size = 30
                t.TextFrame.TextRange.Font.Bold = True
                t.TextFrame.TextRange.Font.Color.RGB = RGB_AMBER
                t.TextFrame.TextRange.ParagraphFormat.Alignment = 2
            if "Text 14" in shape_map:
                t = shape_map["Text 14"]
                t.Left = 655; t.Top = 210; t.Width = 250; t.Height = 35
                t.TextFrame.TextRange.Text = "Nắn phẳng Affine Deskew"
                t.TextFrame.TextRange.Font.Name = "Segoe UI"
                t.TextFrame.TextRange.Font.Size = 13
                t.TextFrame.TextRange.Font.Bold = True
                t.TextFrame.TextRange.Font.Color.RGB = RGB_DARK
                t.TextFrame.TextRange.ParagraphFormat.Alignment = 2
            if "Text 15" in shape_map:
                t = shape_map["Text 15"]
                t.Left = 655; t.Top = 265; t.Width = 250; t.Height = 30
                t.TextFrame.TextRange.Text = "Cứu biển nghiêng phức tạp"
                t.TextFrame.TextRange.Font.Name = "Segoe UI"
                t.TextFrame.TextRange.Font.Size = 11
                t.TextFrame.TextRange.Font.Bold = True
                t.TextFrame.TextRange.Font.Color.RGB = RGB_AMBER
                t.TextFrame.TextRange.ParagraphFormat.Alignment = 2

            # Kết luận đáy slide
            if "Text 20" in shape_map:
                t = shape_map["Text 20"]
                t.Left = 60; t.Top = 365; t.Width = 840; t.Height = 55
                t.TextFrame.TextRange.Text = "Kết luận: Tách–ghép dòng là cải tiến mang tính quyết định nhất (+34,92 pp);\nHậu xử lý và Deskew tiếp tục nâng cao độ chính xác và độ an toàn của toàn hệ thống."
                t.TextFrame.TextRange.Font.Name = "Segoe UI"
                t.TextFrame.TextRange.Font.Size = 13.5
                t.TextFrame.TextRange.Font.Bold = True
                t.TextFrame.TextRange.Font.Color.RGB = RGB_NAVY
                t.TextFrame.TextRange.ParagraphFormat.Alignment = 2

        # ---------------------------------------------------------
        # SLIDE 16: Latency breakdown & Amdahl
        # ---------------------------------------------------------
        elif s_idx == 16:
            for shp in s.Shapes:
                if shp.HasTextFrame:
                    txt = shp.TextFrame.TextRange.Text.strip()
                    if txt == "Latency breakdown":
                        shp.TextFrame.TextRange.Text = "Phân bổ thời gian thực thi (Latency breakdown)"
                    elif "Điểm nghẽn hiện tại là OCR" in txt:
                        shp.TextFrame.TextRange.Text = "Điểm nghẽn thời gian nằm ở tầng OCR (60,8%), xử lý ảnh chỉ chiếm 1,2% ngân sách"
                    elif "PaddleOCR chiếm phần lớn" in txt:
                        shp.TextFrame.TextRange.Text = "PP-OCRv5 chiếm 60,8% (89,16 ms)\nYOLO11n chiếm 38,0% (55,66 ms)"
                    elif "≈ 0 ms trong đường chạy chính" in txt:
                        shp.TextFrame.TextRange.Text = "Xử lý ảnh: 1,78 ms (1,2%)\nHậu xử lý: ~0,03 ms (0,0%)"
                    elif "Hướng tối ưu: ONNX" in txt:
                        shp.TextFrame.TextRange.Text = "Định luật Amdahl: Tăng tốc OCR (ONNX / OpenVINO / INT8) là then chốt"
                elif shp.Type == 13: # Picture
                    shp.Left = 430
                    shp.Top = 115
                    shp.Width = 490
                    shp.Height = 330

        # ---------------------------------------------------------
        # SLIDE 17: Demo
        # ---------------------------------------------------------
        elif s_idx == 17:
            for shp in s.Shapes:
                if shp.HasTextFrame:
                    txt = shp.TextFrame.TextRange.Text.strip()
                    if "Một lệnh Docker Compose" in txt:
                        shp.TextFrame.TextRange.Text = "Khởi chạy một lệnh duy nhất · Giao diện Web trực quan · Đầy đủ API và lịch sử nhận dạng"
                    elif "Hiển thị chuỗi thô & chuỗi sau xử lý" in txt:
                        shp.TextFrame.TextRange.Text = "• Nhận dạng ảnh tĩnh, luồng video và webcam trực tiếp\n• Đối chiếu chuỗi OCR thô và chuỗi chuẩn hóa theo luật\n• Nhận dạng màu sắc biển (HSV) và loại phương tiện\n• Bảng theo dõi lịch sử và độ trễ suy luận từng bước"
                    elif "39 ảnh demo có expected.json" in txt:
                        shp.TextFrame.TextRange.Text = "Kiểm thử tự động trên 39 mẫu kiểm chuẩn có nhãn expected.json"
                elif shp.Type == 13: # Picture
                    shp.Left = 405
                    shp.Top = 110
                    shp.Width = 475
                    shp.Height = 340

        # ---------------------------------------------------------
        # SLIDE 18: Hướng phát triển
        # ---------------------------------------------------------
        elif s_idx == 18:
            for shp in s.Shapes:
                if shp.HasTextFrame:
                    txt = shp.TextFrame.TextRange.Text.strip()
                    if "Tập trung vào điểm nghẽn còn lại" in txt:
                        shp.TextFrame.TextRange.Text = "Tập trung giải quyết điểm nghẽn còn lại: Mô hình nhận dạng chuyên biệt và biển hai dòng"
                    elif "Huấn luyện recognizer chuyên biệt" in txt:
                        shp.TextFrame.TextRange.Text = "Huấn luyện Recognizer chuyên biệt cho biển số VN: Hỗ trợ nhận diện trực tiếp biển 2 dòng"
                    elif "Mở rộng confusion map" in txt:
                        shp.TextFrame.TextRange.Text = "Tự động hóa ma trận hoán vị: Khai thác lỗi từ ma trận nhầm lẫn trên tập dữ liệu lớn"
                    elif "Khử rò rỉ theo chuỗi" in txt:
                        shp.TextFrame.TextRange.Text = "Khử rò rỉ dữ liệu theo chuỗi ký tự: Kết hợp pHash hình ảnh với khoảng cách Levenshtein"
                    elif "Bổ sung dữ liệu biển vàng" in txt:
                        shp.TextFrame.TextRange.Text = "Mở rộng tập dữ liệu đa dạng: Bổ sung biển vàng dịch vụ, biển quân sự đỏ trong điều kiện ban đêm"
                    elif "Tăng tốc bằng ONNX" in txt:
                        shp.TextFrame.TextRange.Text = "Tối ưu hóa và lượng tử hóa mô hình: Tăng tốc bằng ONNX Runtime, OpenVINO và INT8 trên CPU"

        # ---------------------------------------------------------
        # SLIDE 19: Kết luận
        # ---------------------------------------------------------
        elif s_idx == 19:
            for shp in s.Shapes:
                if shp.HasTextFrame:
                    txt = shp.TextFrame.TextRange.Text.strip()
                    if "Xử lý ảnh đúng chỗ có thể" in txt:
                        shp.TextFrame.TextRange.Text = "Tối ưu hình học ảnh và hậu xử lý tri thức đem lại bước nhảy vọt mà không làm tăng tải mô hình"
                    elif "Split & merge" in txt:
                        shp.TextFrame.TextRange.Text = "Tách–ghép dòng (Split-Merge)"
                    elif "Post-processing" in txt:
                        shp.TextFrame.TextRange.Text = "Hậu xử lý tri thức chuyên miền"
                    elif "p95 trên CPU" in txt:
                        shp.TextFrame.TextRange.Text = "Độ trễ p95 trên CPU (1 luồng)"
                    elif "Điểm nghẽn còn lại" in txt:
                        shp.TextFrame.TextRange.Text = "Điểm nghẽn độ chính xác còn lại: Biển 2 dòng (72,34%) → Đã định vị rõ giải pháp trong hướng phát triển."
                    elif "Cảm ơn & Q&A" in txt:
                        shp.TextFrame.TextRange.Text = "Xin trân trọng cảm ơn Quý Thầy Cô & Hội đồng! · Q&A"
                        shp.TextFrame.TextRange.Font.Name = "Segoe UI"
                        shp.TextFrame.TextRange.Font.Bold = True
                        shp.TextFrame.TextRange.Font.Color.RGB = RGB_NAVY

        # ---------------------------------------------------------
        # GLOBAL SLIDE NUMBER CLEANUP (Slides 2 to 19)
        # ---------------------------------------------------------
        if s_idx >= 2:
            for shp in s.Shapes:
                if "Oval" in shp.Name:
                    shp.Left = 6
                    shp.Top = 512
                    shp.Width = 24
                    shp.Height = 24
                    shp.Line.ForeColor.RGB = RGB_BLUE
                    shp.Line.Weight = 1
                    shp.Fill.Solid()
                    shp.Fill.ForeColor.RGB = RGB_WHITE
                    if shp.HasTextFrame:
                        tr = shp.TextFrame.TextRange
                        tr.Text = str(s_idx)
                        tr.Font.Name = "Segoe UI"
                        tr.Font.Size = 9
                        tr.Font.Bold = True
                        tr.Font.Color.RGB = RGB_NAVY

    pres.Save()
    print("4. Successfully saved presentation via PowerPoint COM!")

    # -------------------------------------------------------------
    # 5. Export all 19 slides to PNG for visual verification
    # -------------------------------------------------------------
    export_dir = os.path.join(scratch_dir, "final_slides")
    os.makedirs(export_dir, exist_ok=True)
    for i in range(1, pres.Slides.Count + 1):
        out_png = os.path.join(export_dir, f"slide_{i:02d}.png")
        pres.Slides(i).Export(out_png, "PNG", 1920, 1080)
    print(f"5. Exported all {pres.Slides.Count} slides to {export_dir}")

    pres.Close()
    ppt.Quit()
    print("ALL DONE!")

if __name__ == "__main__":
    main()
