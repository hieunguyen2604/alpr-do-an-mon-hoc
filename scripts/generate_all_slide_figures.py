import os
import cv2
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PIL import Image

plt.rcParams['font.sans-serif'] = ['Segoe UI', 'Arial', 'DejaVu Sans']
plt.rcParams['font.family'] = 'sans-serif'

out_dir = os.path.join(os.path.dirname(__file__), "..", "docs", "slides", "figures")
os.makedirs(out_dir, exist_ok=True)

plate_clean_path = os.path.join(out_dir, "plate_clean.png")

# ==============================================================================
# 1. SLIDE 7: fig-slide-crnn-collapse.png
# ==============================================================================
def gen_fig1():
    print("Generating Figure 1: CRNN/CTC collapse...")
    fig, ax = plt.subplots(figsize=(15, 6.8), dpi=200)
    fig.patch.set_facecolor('#ffffff')
    ax.set_facecolor('#ffffff')
    ax.set_xlim(0, 15)
    ax.set_ylim(0, 6.8)
    ax.axis('off')

    # LEFT BOX: Biển hai dòng
    rect_left = patches.FancyBboxPatch((0.4, 0.4), 6.9, 6.0, boxstyle="round,pad=0.2,rounding_size=0.25",
                                      facecolor='#fff1f2', edgecolor='#fda4af', linewidth=2, zorder=1)
    ax.add_patch(rect_left)

    ax.text(3.85, 6.1, "BIỂN HAI DÒNG — GIẢ ĐỊNH CỦA CTC BỊ VI PHẠM", fontsize=13, fontweight='bold',
            color='#be123c', ha='center', va='center', zorder=4)
    ax.text(3.85, 5.7, "Hạ chiều cao H → 1 ép phẳng 2 hàng ký tự lên cùng một cột đặc trưng",
            fontsize=10.5, color='#9f1239', ha='center', va='center', style='italic', zorder=4)

    # 2-line plate
    img_2line = Image.open(plate_clean_path)
    plate2_border = patches.Rectangle((0.75, 3.4), 2.0, 1.8, facecolor='#ffffff', edgecolor='#cbd5e1', linewidth=1.5, zorder=2)
    ax.add_patch(plate2_border)
    ax.imshow(img_2line, extent=[0.8, 2.7, 3.45, 5.15], zorder=3)
    ax.text(1.75, 3.15, "Vùng cắt 2 dòng\n(83 × 74 px)", fontsize=9.5, ha='center', va='top', color='#334155', fontweight='bold', zorder=4)

    # Arrow 1 -> ConvNet
    arrow1 = patches.FancyArrowPatch((2.9, 4.3), (3.4, 4.3), arrowstyle='->', mutation_scale=18, color='#64748b', linewidth=2, zorder=4)
    ax.add_patch(arrow1)

    # ConvNet block
    conv_box = patches.FancyBboxPatch((3.5, 3.4), 1.6, 1.8, boxstyle="round,pad=0.1,rounding_size=0.15",
                                      facecolor='#e2e8f0', edgecolor='#94a3b8', linewidth=1.5, zorder=2)
    ax.add_patch(conv_box)
    ax.text(4.3, 4.75, "Tầng tích chập", fontsize=10.5, fontweight='bold', color='#1e293b', ha='center', zorder=4)
    ax.text(4.3, 4.35, "CNN Feature Extractor", fontsize=8.5, color='#475569', ha='center', zorder=4)
    ax.text(4.3, 3.95, "Nén không gian 2D", fontsize=9, color='#1e293b', ha='center', zorder=4)
    ax.text(4.3, 3.6, "Hạ chiều cao H → 1", fontsize=10, fontweight='bold', color='#dc2626', ha='center', zorder=4)

    # Arrow 2 -> Feature Vector
    arrow2 = patches.FancyArrowPatch((5.2, 4.3), (5.7, 4.3), arrowstyle='->', mutation_scale=18, color='#64748b', linewidth=2, zorder=4)
    ax.add_patch(arrow2)

    # 1D Feature Vector representation with collision
    for i in range(5):
        is_col = (i == 1)
        col_rect = patches.Rectangle((5.8 + i*0.24, 3.5), 0.20, 1.6, 
                                     facecolor='#fecdd3' if is_col else '#f1f5f9',
                                     edgecolor='#e11d48' if is_col else '#94a3b8', linewidth=1.5 if is_col else 1.0, zorder=2)
        ax.add_patch(col_rect)
        if is_col:
            ax.text(5.9 + i*0.24, 4.7, "5", fontsize=9, fontweight='bold', color='#be123c', ha='center', zorder=4)
            ax.text(5.9 + i*0.24, 4.25, "|", fontsize=10, fontweight='bold', color='#dc2626', ha='center', zorder=4)
            ax.text(5.9 + i*0.24, 3.8, "2", fontsize=9, fontweight='bold', color='#be123c', ha='center', zorder=4)

    ax.text(6.38, 3.15, "Chuỗi vector 1D\n(Xung đột tại cột t₁)", fontsize=9.5, ha='center', va='top', color='#be123c', fontweight='bold', zorder=4)

    # Callout collision
    callout = patches.FancyBboxPatch((0.8, 0.9), 6.1, 1.8, boxstyle="round,pad=0.15,rounding_size=0.2",
                                    facecolor='#ffffff', edgecolor='#f43f5e', linewidth=1.5, zorder=2)
    ax.add_patch(callout)

    ax.text(3.85, 2.35, "HẬU QUẢ XUNG ĐỘT ĐẶC TRƯNG:", fontsize=11, fontweight='bold', color='#be123c', ha='center', zorder=4)
    ax.text(3.85, 1.65, "• Cột thời gian t₁ chứa đồng thời tín hiệu của số '5' (dòng trên) và số '2' (dòng dưới)\n• Giả định căn chỉnh đơn điệu bị phá vỡ hoàn toàn\n• CTC buộc phải chọn ngẫu nhiên -> Đọc lộn xộn, nuốt một dòng, hoặc sinh ký tự rác\n• Độ chính xác cả chuỗi trước xử lý tụt xuống chỉ còn 56,00% (so với 94,18% của biển 1 dòng)",
            fontsize=9, color='#4c0519', ha='center', va='center', zorder=4)

    # RIGHT BOX: Biển một dòng
    rect_right = patches.FancyBboxPatch((7.7, 0.4), 6.9, 6.0, boxstyle="round,pad=0.2,rounding_size=0.25",
                                       facecolor='#ecfdf5', edgecolor='#a7f3d0', linewidth=2, zorder=1)
    ax.add_patch(rect_right)

    ax.text(11.15, 6.1, "BIỂN MỘT DÒNG — CTC HOẠT ĐỘNG CHÍNH XÁC", fontsize=13, fontweight='bold',
            color='#047857', ha='center', va='center', zorder=4)
    ax.text(11.15, 5.7, "Ký tự xếp tuần tự từ trái sang phải, thỏa mãn giả định căn chỉnh đơn điệu",
            fontsize=10.5, color='#065f46', ha='center', va='center', style='italic', zorder=4)

    # 1-line plate
    img_1line = Image.open('docs/reports/figures/28b-err/extra_chars/07_1line_true-51G51008_got-51GG51008.jpg')
    plate1_border = patches.Rectangle((8.0, 3.8), 2.2, 1.0, facecolor='#ffffff', edgecolor='#cbd5e1', linewidth=1.5, zorder=2)
    ax.add_patch(plate1_border)
    ax.imshow(img_1line, extent=[8.05, 10.15, 3.85, 4.75], zorder=3)
    ax.text(9.1, 3.35, "Vùng cắt 1 dòng chuẩn hóa\n(Ký tự xếp thẳng hàng)", fontsize=9.5, ha='center', va='top', color='#334155', fontweight='bold', zorder=4)

    # Arrow 3 -> ConvNet
    arrow3 = patches.FancyArrowPatch((10.3, 4.3), (10.8, 4.3), arrowstyle='->', mutation_scale=18, color='#64748b', linewidth=2, zorder=4)
    ax.add_patch(arrow3)

    # ConvNet block
    conv_box2 = patches.FancyBboxPatch((10.9, 3.4), 1.6, 1.8, boxstyle="round,pad=0.1,rounding_size=0.15",
                                       facecolor='#e2e8f0', edgecolor='#94a3b8', linewidth=1.5, zorder=2)
    ax.add_patch(conv_box2)
    ax.text(11.7, 4.75, "Tầng tích chập", fontsize=10.5, fontweight='bold', color='#1e293b', ha='center', zorder=4)
    ax.text(11.7, 4.35, "CNN Feature Extractor", fontsize=8.5, color='#475569', ha='center', zorder=4)
    ax.text(11.7, 3.95, "Nén không gian 2D", fontsize=9, color='#1e293b', ha='center', zorder=4)
    ax.text(11.7, 3.6, "Hạ chiều cao H → 1", fontsize=10, fontweight='bold', color='#059669', ha='center', zorder=4)

    # Arrow 4 -> Vector 1D
    arrow4 = patches.FancyArrowPatch((12.6, 4.3), (13.0, 4.3), arrowstyle='->', mutation_scale=18, color='#64748b', linewidth=2, zorder=4)
    ax.add_patch(arrow4)

    # 1D Feature Vector representation (monotonic)
    chars = ['5', '1', 'G', '5', '1']
    for i, ch in enumerate(chars):
        col_rect = patches.Rectangle((13.1 + i*0.24, 3.5), 0.20, 1.6, 
                                     facecolor='#dcfce7', edgecolor='#16a34a', linewidth=1.2, zorder=2)
        ax.add_patch(col_rect)
        ax.text(13.2 + i*0.24, 4.25, ch, fontsize=9.5, fontweight='bold', color='#15803d', ha='center', zorder=4)

    ax.text(13.7, 3.15, "Chuỗi vector 1D\n(Ánh xạ 1-1 chuẩn)", fontsize=9.5, ha='center', va='top', color='#047857', fontweight='bold', zorder=4)

    # Callout success
    callout2 = patches.FancyBboxPatch((8.1, 0.9), 6.1, 1.8, boxstyle="round,pad=0.15,rounding_size=0.2",
                                     facecolor='#ffffff', edgecolor='#10b981', linewidth=1.5, zorder=2)
    ax.add_patch(callout2)

    ax.text(11.15, 2.35, "CĂN CHỈNH ĐƠN ĐIỆU (MONOTONIC ALIGNMENT):", fontsize=11, fontweight='bold', color='#047857', ha='center', zorder=4)
    ax.text(11.15, 1.65, "• Mỗi vị trí thời gian tᵢ tương ứng độc lập với duy nhất một lát cắt ký tự\n• Giả định ánh xạ đơn điệu của giải mã CTC được thỏa mãn 100%\n• Biển một dòng đạt độ chính xác chuỗi rất cao: S₁ = 95,41%\n• Định hướng giải pháp: Phải biến biển 2 dòng thành 1 dòng trước khi đưa vào OCR!",
            fontsize=9, color='#064e3b', ha='center', va='center', zorder=4)

    plt.tight_layout()
    p = os.path.join(out_dir, "fig-slide-crnn-collapse.png")
    plt.savefig(p, bbox_inches='tight', dpi=200)
    plt.close()
    print("  -> Saved", p)

# ==============================================================================
# 2. SLIDE 10: fig-slide-split-vs-projection.png
# ==============================================================================
def gen_fig2():
    print("Generating Figure 2: Split vs Projection...")
    fig, ax = plt.subplots(figsize=(15, 6.8), dpi=200)
    fig.patch.set_facecolor('#ffffff')
    ax.set_facecolor('#ffffff')
    ax.set_xlim(0, 15)
    ax.set_ylim(0, 6.8)
    ax.axis('off')

    # LEFT PANEL: Vì sao phép chiếu ngang thất bại
    rect_left = patches.FancyBboxPatch((0.4, 0.4), 6.9, 6.0, boxstyle="round,pad=0.2,rounding_size=0.25",
                                      facecolor='#fff1f2', edgecolor='#fda4af', linewidth=2, zorder=1)
    ax.add_patch(rect_left)

    ax.text(3.85, 6.1, "RỦI RO CỦA PHÉP CHIẾU NGANG (PROJECTION)", fontsize=13, fontweight='bold',
            color='#be123c', ha='center', va='center', zorder=4)
    ax.text(3.85, 5.7, "Mộc Công an dập nổi và ốc vít gắn biển tạo đỉnh xám giả nối liền hai dòng, làm triệt tiêu điểm cắt rỗng",
            fontsize=9.5, color='#9f1239', ha='center', va='center', style='italic', zorder=4)

    # Real plate with central bolt
    img_plate = Image.open(plate_clean_path)
    ax.imshow(img_plate, extent=[0.8, 3.2, 2.7, 5.1], zorder=3)
    
    # Highlight bolt in plate center
    bolt_circle = patches.Circle((2.0, 4.35), 0.18, edgecolor='#ef4444', facecolor='none', linewidth=2.5, linestyle='--', zorder=5)
    ax.add_patch(bolt_circle)
    ax.text(2.0, 2.55, "Biển xe máy có mộc dập nổi / ốc vít ở tim biển\n(Vùng nối liền 2 dòng)", fontsize=8.5, ha='center', va='top', color='#334155', fontweight='bold', zorder=4)

    # Plot Projection Profile
    ax_prof = patches.Rectangle((3.6, 2.7), 3.3, 2.4, facecolor='#ffffff', edgecolor='#cbd5e1', linewidth=1.5, zorder=2)
    ax.add_patch(ax_prof)

    y_vals = np.linspace(2.7, 5.1, 100)
    p1 = np.exp(-((y_vals - 4.5)/0.25)**2) * 1.8
    p2 = np.exp(-((y_vals - 3.4)/0.3)**2) * 2.2
    bolt_p = np.exp(-((y_vals - 3.95)/0.15)**2) * 1.2
    prof = p1 + p2 + bolt_p + 0.2
    
    ax.plot(3.8 + prof * 0.9, y_vals, color='#be123c', linewidth=2, zorder=4)
    ax.fill_betweenx(y_vals, 3.8, 3.8 + prof * 0.9, color='#fecdd3', alpha=0.5, zorder=3)

    ax.text(6.8, 4.5, "← Dòng 1 (59-K1)", fontsize=8.5, color='#1e293b', va='center', zorder=5)
    ax.text(6.8, 3.4, "← Dòng 2 (201.73)", fontsize=8.5, color='#1e293b', va='center', zorder=5)
    
    ax.annotate("ĐỈNH GIẢ TẠI ỐC VÍT / MỘC DẬP\n(Không có khoảng trắng)", xy=(3.8 + 1.4*0.9, 3.95), xytext=(4.3, 4.0),
                arrowprops=dict(arrowstyle="->", color='#dc2626', lw=1.5),
                fontsize=7.5, fontweight='bold', color='#dc2626', zorder=6)

    # Callout text below
    callout1 = patches.FancyBboxPatch((0.8, 0.75), 6.1, 1.4, boxstyle="round,pad=0.1,rounding_size=0.15",
                                     facecolor='#ffffff', edgecolor='#fda4af', linewidth=1.5, zorder=2)
    ax.add_patch(callout1)
    ax.text(3.85, 1.45, "HẠN CHẾ CỐ HỮU CỦA CHIẾU NGANG:", fontsize=10, fontweight='bold', color='#be123c', ha='center', zorder=4)
    ax.text(3.85, 1.05, "• Ốc vít / mộc Công an ở tâm biển tạo cầu nối xám liên tục giữa 2 dòng ký tự\n• Biển cong vênh, bám bùn hoặc bóng đổ làm mất hoàn toàn thung lũng phân cách\n• Đòi hỏi quét ngưỡng động phức tạp, dễ cắt phạm nét chữ hoặc vỡ đường ống",
            fontsize=8.5, color='#4c0519', ha='center', va='center', zorder=4)

    # RIGHT PANEL: Cắt cố định 5/12 & 1/3
    rect_right = patches.FancyBboxPatch((7.7, 0.4), 6.9, 6.0, boxstyle="round,pad=0.2,rounding_size=0.25",
                                       facecolor='#ecfdf5', edgecolor='#a7f3d0', linewidth=2, zorder=1)
    ax.add_patch(rect_right)

    ax.text(11.15, 6.1, "GIẢI PHÁP ĐỀ XUẤT: CẮT CỐ ĐỊNH (5/12 & 1/3) + ĐỆM 1/12", fontsize=12, fontweight='bold',
            color='#047857', ha='center', va='center', zorder=4)
    ax.text(11.15, 5.7, "Quy chuẩn QCVN 08:2024/BCA định hình hình học O(1), tự động hóa ổn định tuyệt đối",
            fontsize=10, color='#065f46', ha='center', va='center', style='italic', zorder=4)

    ax.imshow(img_plate, extent=[8.0, 10.4, 2.7, 5.1], zorder=3)
    
    overlap_band = patches.Rectangle((8.0, 4.1), 2.4, 0.2, facecolor='#fef08a', edgecolor='#eab308',
                                     alpha=0.6, linewidth=1.5, linestyle='--', zorder=4)
    ax.add_patch(overlap_band)

    ax.plot([7.8, 10.6], [4.1, 4.1], color='#dc2626', linewidth=2, linestyle='-', zorder=5)
    ax.plot([7.8, 10.6], [4.3, 4.3], color='#2563eb', linewidth=2, linestyle='-', zorder=5)

    ax.text(10.7, 4.7, "Nửa trên: [0 → 5/12·H]\n(Bảo toàn chân chữ 59-K1)", fontsize=8.5, color='#991b1b', va='center', fontweight='bold', zorder=4)
    ax.text(10.7, 4.2, "Dải chồng lấn 1/12·H\n(Vùng đệm an toàn)", fontsize=8.5, color='#854d0e', va='center', fontweight='bold', zorder=4)
    ax.text(10.7, 3.3, "Nửa dưới: [1/3·H → H]\n(Bảo toàn đỉnh số 201.73)", fontsize=8.5, color='#1e40af', va='center', fontweight='bold', zorder=4)

    crop_top = img_plate.crop((0, 0, img_plate.width, int(img_plate.height * 5/12)))
    crop_bot = img_plate.crop((0, int(img_plate.height * 1/3), img_plate.width, img_plate.height))
    
    ax.imshow(crop_top, extent=[12.5, 14.3, 4.3, 5.0], zorder=3)
    ax.imshow(crop_bot, extent=[12.5, 14.3, 3.1, 4.1], zorder=3)
    ax.text(13.4, 5.1, "Nửa trên đã tách", fontsize=8, color='#991b1b', ha='center', zorder=4)
    ax.text(13.4, 2.9, "Nửa dưới đã tách", fontsize=8, color='#1e40af', ha='center', zorder=4)

    callout2 = patches.FancyBboxPatch((8.1, 0.75), 6.1, 1.4, boxstyle="round,pad=0.1,rounding_size=0.15",
                                     facecolor='#ffffff', edgecolor='#a7f3d0', linewidth=1.5, zorder=2)
    ax.add_patch(callout2)
    ax.text(11.15, 1.45, "ƯU ĐIỂM VƯỢT TRỘI CỦA CẮT CỐ ĐỊNH:", fontsize=10, fontweight='bold', color='#047857', ha='center', zorder=4)
    ax.text(11.15, 1.05, "• Độ phức tạp O(1): Thực thi gần như tức thì (~0,00 ms), không tốn chu kỳ tính toán\n• Căn cứ pháp lý QCVN 08:2024: Tỉ lệ kích thước ký tự và lề biển đã chuẩn hóa toàn quốc\n• Vùng đệm 1/12 triệt tiêu 100% rủi ro mất nét chân/đầu; nét thừa lọt sang được OCR coi là nền",
            fontsize=8.5, color='#064e3b', ha='center', va='center', zorder=4)

    plt.tight_layout()
    p = os.path.join(out_dir, "fig-slide-split-vs-projection.png")
    plt.savefig(p, bbox_inches='tight', dpi=200)
    plt.close()
    print("  -> Saved", p)

# ==============================================================================
# 3. SLIDE 12: fig-slide-hsv-eval.png
# ==============================================================================
def gen_fig3():
    print("Generating Figure 3: HSV Color Classification...")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6.8), dpi=200, gridspec_kw={'width_ratios': [1, 1.2]})
    fig.patch.set_facecolor('#ffffff')

    ax1.set_facecolor('#ffffff')
    ax1.set_xlim(0, 10)
    ax1.set_ylim(0, 10)
    ax1.axis('off')

    bg_left = patches.FancyBboxPatch((0.2, 0.2), 9.6, 9.6, boxstyle="round,pad=0.2,rounding_size=0.3",
                                    facecolor='#f8fafc', edgecolor='#cbd5e1', linewidth=1.8, zorder=1)
    ax1.add_patch(bg_left)

    ax1.text(5.0, 9.2, "NGUYÊN LÝ KHÔNG GIAN MÀU HSV", fontsize=13, fontweight='bold', color='#1e293b', ha='center', zorder=3)
    ax1.text(5.0, 8.7, "Phân tách sắc độ khỏi độ sáng để chống chịu ánh sáng tự nhiên", fontsize=9.5, color='#475569', ha='center', style='italic', zorder=3)

    # Draw HSV Color Wheel / Disk
    theta = np.linspace(0, 2*np.pi, 200)
    r = np.linspace(0.2, 1.8, 50)
    T, R = np.meshgrid(theta, r)
    X = R * np.cos(T) + 5.0
    Y = R * np.sin(T) + 5.8
    H = T / (2*np.pi)
    S = R / 1.8
    V = np.ones_like(H) * 0.95
    import matplotlib.colors as mcolors
    HSV = np.stack([H, S, V], axis=-1)
    RGB = mcolors.hsv_to_rgb(HSV)
    ax1.pcolormesh(X, Y, RGB[:, :, 0], color=RGB.reshape(-1, 3), shading='auto', zorder=2)

    ax1.annotate("Trục Sắc độ H\n(Quay tròn 0° - 360°)\nNhận biết: Vàng, Trắng, Xanh", xy=(6.6, 6.6), xytext=(7.3, 7.3),
                 arrowprops=dict(arrowstyle="->", color='#0f172a', lw=1.5),
                 fontsize=8.5, fontweight='bold', color='#0f172a', zorder=4)

    ax1.annotate("Trục Bão hòa S\n(Tâm → Rìa)\nPhân biệt Trắng (S thấp)\n& Biển màu (S cao)", xy=(5.0, 5.8), xytext=(1.2, 6.8),
                 arrowprops=dict(arrowstyle="->", color='#0f172a', lw=1.5),
                 fontsize=8.5, fontweight='bold', color='#0f172a', zorder=4)

    ax1.arrow(1.0, 4.0, 0, 2.5, head_width=0.2, head_length=0.3, fc='#64748b', ec='#64748b', zorder=4)
    ax1.text(0.7, 5.2, "Độ sáng V (Độc lập)", fontsize=8.5, color='#334155', rotation=90, va='center', fontweight='bold', zorder=4)

    card = patches.FancyBboxPatch((0.6, 0.6), 8.8, 2.8, boxstyle="round,pad=0.15,rounding_size=0.2",
                                 facecolor='#ffffff', edgecolor='#e2e8f0', linewidth=1.5, zorder=2)
    ax1.add_patch(card)
    ax1.text(5.0, 3.0, "BA KỸ THUẬT XỬ LÝ ẢNH MÀU CỐT LÕI:", fontsize=10, fontweight='bold', color='#1e293b', ha='center', zorder=3)
    ax1.text(5.0, 1.8, "1. Tách biệt H và V: Nhận diện màu chuẩn xác dưới nắng gắt hoặc bóng râm\n2. Vùng đệm thu biên 18%: Cắt bỏ rìa viền nhằm triệt tiêu màu sơn vỏ xe\n3. Ngưỡng tin cậy 30%: Dải màu chiếm đa số từ 30% trở lên mới phân loại, tránh gán nhãn thiếu căn cứ",
             fontsize=8.5, color='#334155', ha='center', va='center', zorder=3)

    # RIGHT PANEL: Biểu đồ cột đánh giá độc lập
    ax2.set_facecolor('#ffffff')
    bg_right = patches.FancyBboxPatch((0.02, 0.02), 0.96, 0.96, boxstyle="round,pad=0.02,rounding_size=0.03",
                                     facecolor='#f8fafc', edgecolor='#cbd5e1', linewidth=1.8, zorder=1, transform=ax2.transAxes)
    ax2.add_patch(bg_right)

    categories = ['Biển vàng\n(Xe dịch vụ)', 'Biển trắng\n(Xe dân sự)', 'Biển xanh\n(Cơ quan)', 'TỔNG THỂ\n(Toàn tập đo)']
    accuracies = [98.56, 97.40, 96.83, 97.89]
    samples = ['684 / 694 mẫu', '787 / 808 mẫu', '61 / 63 mẫu', '1.532 / 1.565 mẫu']
    bar_colors = ['#f59e0b', '#64748b', '#2563eb', '#059669']

    x = np.arange(len(categories))
    width = 0.55

    bars = ax2.bar(x, accuracies, width, color=bar_colors, edgecolor='#0f172a', linewidth=1.2, zorder=3)
    ax2.set_ylim(80, 104)
    ax2.set_ylabel('Độ chính xác phân loại (%)', fontsize=11, fontweight='bold', color='#1e293b')
    ax2.set_title('KẾT QUẢ ĐÁNH GIÁ ĐỘC LẬP (n = 1.565 mẫu thử nghiệm)', fontsize=13, fontweight='bold', color='#1e293b', pad=20)
    ax2.set_xticks(x)
    ax2.set_xticklabels(categories, fontsize=10, fontweight='semibold', color='#1e293b')
    ax2.grid(axis='y', linestyle='--', alpha=0.5, zorder=1)

    for bar, acc, samp in zip(bars, accuracies, samples):
        yval = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2.0, yval + 1.0, f"{acc:.2f}%", ha='center', va='bottom',
                 fontsize=11, fontweight='bold', color='#0f172a', zorder=4)
        ax2.text(bar.get_x() + bar.get_width()/2.0, yval - 4.5, samp, ha='center', va='center',
                 fontsize=8.5, fontweight='semibold', color='#ffffff' if bar.get_facecolor()[0] < 0.8 else '#0f172a', zorder=4)

    ax2.axhline(95, color='#94a3b8', linestyle=':', linewidth=1.5, zorder=2)
    ax2.text(3.4, 95.3, 'Mục tiêu: 95%', fontsize=8.5, color='#64748b', style='italic', zorder=4)

    plt.tight_layout()
    p = os.path.join(out_dir, "fig-slide-hsv-eval.png")
    plt.savefig(p, bbox_inches='tight', dpi=200)
    plt.close()
    print("  -> Saved", p)

# ==============================================================================
# 4. SLIDE 13: fig-slide-deskew-ladder.png
# ==============================================================================
def gen_fig4():
    print("Generating Figure 4: Deskew & Fallback Ladder...")
    fig, ax = plt.subplots(figsize=(15, 6.8), dpi=200)
    fig.patch.set_facecolor('#ffffff')
    ax.set_facecolor('#ffffff')
    ax.set_xlim(0, 15)
    ax.set_ylim(0, 6.8)
    ax.axis('off')

    # Top Banner
    rect_top = patches.FancyBboxPatch((0.4, 2.5), 14.2, 3.9, boxstyle="round,pad=0.2,rounding_size=0.25",
                                     facecolor='#f8fafc', edgecolor='#cbd5e1', linewidth=1.8, zorder=1)
    ax.add_patch(rect_top)

    ax.text(7.5, 6.0, "QUY TRÌNH HIỆU CHỈNH GÓC NGHIÊNG 2D (AFFINE DESKEW)", fontsize=13, fontweight='bold', color='#1e293b', ha='center', zorder=3)
    ax.text(7.5, 5.65, "Kéo tỉ lệ khung hình về đúng hình học chuẩn để đi vào nhánh tách-ghép biển hai dòng", fontsize=10, color='#475569', ha='center', style='italic', zorder=3)

    img_cv = cv2.imread(plate_clean_path)
    h, w = img_cv.shape[:2]

    # Create 1. Skewed plate (rotate by 18 degrees)
    M_skew = cv2.getRotationMatrix2D((w//2, h//2), 18, 0.85)
    img_skew = cv2.warpAffine(img_cv, M_skew, (w, h), borderValue=(235, 235, 235))

    # Create 2. Binary Otsu + Rotated Rect
    gray = cv2.cvtColor(img_skew, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    img_box = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)
    cnts, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if cnts:
        c = max(cnts, key=cv2.contourArea)
        rect = cv2.minAreaRect(c)
        box = cv2.boxPoints(rect)
        box = np.int32(box)
        cv2.drawContours(img_box, [box], 0, (0, 0, 255), 4)

    # Create 3. Deskewed result (perfect horizontal, clean background)
    M_deskew = cv2.getRotationMatrix2D((w//2, h//2), -18, 1.15)
    img_deskew = cv2.warpAffine(img_skew, M_deskew, (w, h), borderValue=(245, 245, 245))

    # Show 3 images side by side
    ax.imshow(cv2.cvtColor(img_skew, cv2.COLOR_BGR2RGB), extent=[0.8, 4.2, 3.2, 5.2], zorder=3)
    ax.text(2.5, 2.9, "1. Ảnh vùng cắt gốc\n(Nghiêng ~18°, AR nhảy lệch)", fontsize=9.5, ha='center', va='top', color='#1e293b', fontweight='bold', zorder=4)

    arrow1 = patches.FancyArrowPatch((4.4, 4.2), (5.3, 4.2), arrowstyle='->', mutation_scale=20, color='#2563eb', linewidth=2.5, zorder=4)
    ax.add_patch(arrow1)

    ax.imshow(cv2.cvtColor(img_box, cv2.COLOR_BGR2RGB), extent=[5.5, 8.9, 3.2, 5.2], zorder=3)
    ax.text(7.2, 2.9, "2. Nhị phân hóa Otsu 2 cực\n& Khớp minAreaRect (hộp đỏ)", fontsize=9.5, ha='center', va='top', color='#1e293b', fontweight='bold', zorder=4)

    arrow2 = patches.FancyArrowPatch((9.1, 4.2), (10.0, 4.2), arrowstyle='->', mutation_scale=20, color='#2563eb', linewidth=2.5, zorder=4)
    ax.add_patch(arrow2)

    ax.imshow(cv2.cvtColor(img_deskew, cv2.COLOR_BGR2RGB), extent=[10.2, 13.6, 3.2, 5.2], zorder=3)
    ax.text(11.9, 2.9, "3. Xoay phẳng theo trục hoành\n(Cắt sát, phục hồi AR = 1,36)", fontsize=9.5, ha='center', va='top', color='#047857', fontweight='bold', zorder=4)

    # Bottom Banner: Đánh đổi kỹ thuật
    rect_bot = patches.FancyBboxPatch((0.4, 0.4), 14.2, 1.9, boxstyle="round,pad=0.2,rounding_size=0.2",
                                     facecolor='#ecfdf5', edgecolor='#a7f3d0', linewidth=1.8, zorder=1)
    ax.add_patch(rect_bot)

    ax.text(7.5, 2.0, "ĐÁNH ĐỔI KỸ THUẬT ĐÃ LƯỢNG HÓA TỪ THỰC NGHIỆM (BẢNG 4.9)", fontsize=11, fontweight='bold', color='#047857', ha='center', zorder=3)
    
    col1_text = "• Cứu thêm +34 biển số đọc đúng hoàn toàn (đóng góp vào mức tăng toàn hệ thống)\n• Cơ chế thử lại đa tầng (Fallback Ladder): Chỉ mở cổng khi lần đọc 1 trượt regex -> Tuyệt đối không can thiệp biển vốn đã đúng"
    col2_text = "• Ba cổng an toàn: Bỏ qua hiệu chỉnh nếu góc dưới 1,5°, trên 35°, hoặc diện tích liên thông dưới 25% bbox\n• Chi phí tính toán: Trung vị p50 giữ nguyên 405 ms (+0 ms); chi phí dồn trọn vào đuôi phân bố p95 (+276,8 ms)"

    ax.text(1.0, 1.4, col1_text, fontsize=9, color='#064e3b', va='top', zorder=4)
    ax.text(8.0, 1.4, col2_text, fontsize=9, color='#064e3b', va='top', zorder=4)

    plt.tight_layout()
    p = os.path.join(out_dir, "fig-slide-deskew-ladder.png")
    plt.savefig(p, bbox_inches='tight', dpi=200)
    plt.close()
    print("  -> Saved", p)

# ==============================================================================
# 5. SLIDE 18: fig-slide-latency-amdahl.png
# ==============================================================================
def gen_fig5():
    print("Generating Figure 5: Latency Donut & Amdahl's Law...")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6.8), dpi=200, gridspec_kw={'width_ratios': [1.1, 1.2]})
    fig.patch.set_facecolor('#ffffff')

    # LEFT PANEL: Donut Chart
    ax1.set_facecolor('#ffffff')
    labels = [
        'PaddleOCR (Nhận dạng ký tự)\n89,16 ms (60,8%) — Điểm nghẽn chính',
        'YOLO11n @ 640px (Phát hiện biển)\n55,66 ms (38,0%)',
        'Tiền xử lý & Giải mã ảnh\n1,78 ms (1,2%)',
        'Xử lý ảnh & Hậu xử lý\n~0,03 ms (0,0%)'
    ]
    sizes = [89.16, 55.66, 1.78, 0.03]
    colors = ['#f43f5e', '#3b82f6', '#94a3b8', '#10b981']
    explode = (0.06, 0, 0, 0)

    wedges, texts, autotexts = ax1.pie(
        sizes, explode=explode, labels=None, autopct=lambda p: f'{p:.1f}%' if p > 5 else '',
        pctdistance=0.72, startangle=140, colors=colors,
        wedgeprops=dict(width=0.45, edgecolor='#ffffff', linewidth=2)
    )

    for at in autotexts:
        at.set_color('#ffffff')
        at.set_fontsize(11.5)
        at.set_fontweight('bold')

    ax1.text(0, 0, "TỔNG ĐỘ TRỄ\n146,63 ms\n(Thuần CPU)", ha='center', va='center',
             fontsize=12, fontweight='bold', color='#1e293b')
    ax1.set_title("PHÂN BỔ THỜI GIAN THỰC THI TRÊN CPU (Bảng 4.10)", fontsize=12, fontweight='bold', color='#1e293b', pad=15)

    ax1.legend(wedges, labels, loc='center', bbox_to_anchor=(0.5, -0.15),
               frameon=False, fontsize=8.5, labelspacing=0.6)

    # RIGHT PANEL: Amdahl & Architecture Insights
    ax2.set_facecolor('#ffffff')
    ax2.axis('off')

    bg_right = patches.FancyBboxPatch((0.02, 0.02), 0.96, 0.96, boxstyle="round,pad=0.02,rounding_size=0.03",
                                     facecolor='#f8fafc', edgecolor='#cbd5e1', linewidth=1.8, zorder=1, transform=ax2.transAxes)
    ax2.add_patch(bg_right)

    ax2.text(0.5, 0.92, "KẾT LUẬN THEN CHỐT TỪ ĐỊNH LUẬT AMDAHL", fontsize=13, fontweight='bold', color='#1e293b', ha='center', transform=ax2.transAxes, zorder=3)
    ax2.text(0.5, 0.86, "Định hướng chiến lược phân bổ nguồn lực tối ưu hóa toàn hệ thống", fontsize=9.5, color='#475569', ha='center', style='italic', transform=ax2.transAxes, zorder=3)

    # Card 1: Image processing efficiency
    card1 = patches.FancyBboxPatch((0.06, 0.48), 0.88, 0.34, boxstyle="round,pad=0.02,rounding_size=0.02",
                                  facecolor='#ffffff', edgecolor='#10b981', linewidth=1.5, zorder=2, transform=ax2.transAxes)
    ax2.add_patch(card1)
    ax2.text(0.10, 0.76, "1. HIỆU QUẢ CHI PHÍ TÍNH TOÁN CỰC CAO (XỬ LÝ ẢNH & HẬU XỬ LÝ)", fontsize=10, fontweight='bold', color='#047857', transform=ax2.transAxes, zorder=3)
    ax2.text(0.10, 0.52, "• Toàn bộ chuỗi xử lý ảnh (CLAHE, lọc song phương, tách-ghép) và bộ luật hậu xử lý\n  mang lại mức tăng khổng lồ: +34,92 điểm (tách-ghép) và +13,28 điểm (hậu xử lý)\n• Tổng thời gian thực thi xấp xỉ bằng không (~0,03 ms, chiếm 0,0% ngân sách CPU)\n-> Tỉ lệ Lợi ích / Chi phí tính toán đạt mức tối ưu tuyệt đối.",
             fontsize=8.5, color='#064e3b', transform=ax2.transAxes, zorder=3)

    # Card 2: Amdahl bottleneck
    card2 = patches.FancyBboxPatch((0.06, 0.08), 0.88, 0.36, boxstyle="round,pad=0.02,rounding_size=0.02",
                                  facecolor='#ffffff', edgecolor='#f43f5e', linewidth=1.5, zorder=2, transform=ax2.transAxes)
    ax2.add_patch(card2)
    ax2.text(0.10, 0.38, "2. HỆ QUẢ ĐỊNH LUẬT AMDAHL & TRỌNG TÂM TỐI ƯU", fontsize=10, fontweight='bold', color='#be123c', transform=ax2.transAxes, zorder=3)
    ax2.text(0.10, 0.12, "• Tăng tốc YOLO11n gấp 2 - 3 lần chỉ giúp giảm tối đa 15% - 20% tổng thời gian hệ thống\n• Điểm nghẽn duy nhất và lớn nhất là PaddleOCR (chiếm 60,8% thời gian = 89,16 ms)\n• Nguyên nhân: PaddleOCR là pipeline đa giai đoạn thiết kế cho trang văn bản lớn\n-> Trọng tâm tối ưu bắt buộc: Lượng tử hóa INT8, xuất mô hình ONNX / OpenVINO\n  và loại bỏ các khối phát hiện văn bản dư thừa.",
             fontsize=8.5, color='#4c0519', transform=ax2.transAxes, zorder=3)

    plt.tight_layout()
    p = os.path.join(out_dir, "fig-slide-latency-amdahl.png")
    plt.savefig(p, bbox_inches='tight', dpi=200)
    plt.close()
    print("  -> Saved", p)

if __name__ == "__main__":
    gen_fig1()
    gen_fig2()
    gen_fig3()
    gen_fig4()
    gen_fig5()
    print("All 5 slide figures successfully polished and generated!")
