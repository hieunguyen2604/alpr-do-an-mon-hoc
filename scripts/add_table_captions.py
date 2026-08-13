"""Thêm chú thích nhìn thấy được cho các bảng có neo ở Chương 5 và Chương 6.

Vấn đề
------
Quyển dùng **hai quy ước bảng song song**. Chương 2–4 đặt chú thích nhìn thấy
được (``**Bảng 2.9.** …``). Chương 5–6 — nơi đặt toàn bộ số liệu thực nghiệm —
chỉ có **neo máy đọc** (``<!-- {{T6.5b}} … -->``), vốn là chú thích HTML nên
**không hiện ra khi in**.

Hệ quả: 26 bảng số liệu quan trọng nhất của đồ án không có tên, và *"Danh mục
bảng biểu"* ở đầu quyển không thể sinh ra được — nó đang là một placeholder liệt
kê những bảng không tồn tại.

Cách xử lý
----------
Giữ nguyên neo (phụ lục ánh xạ số liệu tra theo nó), **thêm** một dòng chú thích
đánh số tuần tự trong chương ngay dưới neo. Người đọc thấy *"Bảng 6.10"*; công
cụ vẫn tra được ``{{T6.5b}}``.

Chạy một lần::

    backend/.venv/Scripts/python scripts/add_table_captions.py --apply
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

for _l in (sys.stdout, sys.stderr):
    if hasattr(_l, "reconfigure"):
        _l.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
PAPERS = ROOT / "docs" / "papers"

# neo -> chu thich. Thu tu trong dict = thu tu danh so trong chuong.
CHU_THICH: dict[str, dict[str, str]] = {
    "ch5-xay-dung-huan-luyen.md": {
        "T5.3a": "Siêu tham số huấn luyện mô hình chính thức",
        "T5.3b": "Tiến triển chỉ số trên tập validation theo mốc epoch",
        "T5.4": "So sánh bộ nhận dạng gốc và bản tinh chỉnh trên cùng ngữ liệu",
    },
    "ch6-thuc-nghiem.md": {
        "T6.2a": "Cấu hình phần cứng và hệ thống của máy thực nghiệm",
        "T6.2b": "Phiên bản thư viện tại thời điểm đo",
        "T6.3a": "So sánh ba phiên bản bộ dữ liệu",
        "T6.3b": "Số cặp ảnh gần trùng xuyên split theo ngưỡng Hamming",
        "T6.3c": "Phân bố nguồn dữ liệu giữa các split của phiên bản v3",
        "T6.4a": "Kết quả phát hiện tổng thể trên tập test v3",
        "T6.4b": "Kết quả phát hiện tách theo biển một dòng và hai dòng (NFR-A8)",
        "T6.4c": "Kết quả phát hiện tách theo dải kích thước hộp giới hạn",
        "T6.5a": "Độ chính xác mức ký tự (NFR-A4)",
        "T6.5b": "Độ chính xác chuỗi đầy đủ trước và sau hậu xử lý",
        "T6.5c": "Độ chính xác nhận dạng tách theo biển một dòng và hai dòng",
        "T6.5d": "Các cặp ký tự bị nhầm nhiều nhất, đối chiếu bảng luật hiện hành",
        "T6.5e": "Độ chính xác đầu-cuối toàn trình (NFR-A7)",
        "T6.5f": "So sánh A/B hai chiến lược đọc biển hai dòng",
        "T6.5g": "So sánh A/B bước cứu dòng trên trên hai mẫu độc lập",
        "T6.5h": "Trước và sau bước cứu dòng trên, đo trên toàn tập có nhãn chuỗi",
        "T6.5i": "Chi phí và lợi ích của từng bậc trong bậc thang thử-lại",
        "T6.6a": "Độ trễ đầu-cuối một ảnh, đối chiếu NFR-P1",
        "T6.6b": "Phân rã ngân sách độ trễ theo từng bước",
        "T6.6c": "So sánh backend suy luận cho bộ phát hiện",
        "T6.6d": "Hiệu năng chế độ webcam và xử lý video",
        "T6.6e": "Chịu tải, bộ nhớ và độ tin cậy",
        "T6.6f": "Bỏ bước phát hiện chữ — hai ngữ liệu, hai kết luận ngược nhau",
        "T6.7": "Đối chiếu toàn bộ chỉ tiêu phi chức năng",
        "T6.8": "Tần suất từng loại lỗi",
    },
}

NEO = re.compile(r"^<!--\s*\{\{(T[\d.]+[a-z]?)\}\}")
HEADER_BANG = re.compile(r"^\|.*\|\s*$")

# Chuong 1, 4, 7 khong dung neo, nen phai neo theo DONG CHU dung ngay truoc bang.
# Chi danh so nhung bang nguoi doc thuc su tra cuu — cac luoi noi tuyen kieu
# "| Muc | Noi dung |" trong dac ta use case thi khong.
THEO_MOC: dict[str, list[tuple[str, str]]] = {
    "ch1-gioi-thieu.md": [
        ("**(a) Nhóm chỉ tiêu độ chính xác**", "Nhóm chỉ tiêu độ chính xác"),
        ("**(b) Nhóm chỉ tiêu hiệu năng", "Nhóm chỉ tiêu hiệu năng trên CPU"),
        ("### 1.3.2. Phạm vi trong nghiên cứu", "Phạm vi trong nghiên cứu"),
        ("> **Vì sao mục này quan trọng hơn vẻ ngoài của nó.**",
         "Các hạng mục nằm ngoài phạm vi và lý do loại trừ"),
        ("Đề tài được thực hiện theo quy trình **12 giai đoạn",
         "Mười hai giai đoạn thực hiện, công sức và điều kiện thông qua"),
    ],
    "ch4-phan-tich-thiet-ke.md": [
        ("#### a) Phân bố yêu cầu theo nhóm và mức ưu tiên",
         "Phân bố 34 yêu cầu chức năng theo nhóm và mức ưu tiên MoSCoW"),
        ("#### b) NFR-P — Hiệu năng", "Chỉ tiêu phi chức năng nhóm hiệu năng (NFR-P)"),
        ("#### c) NFR-A — Độ chính xác", "Chỉ tiêu phi chức năng nhóm độ chính xác (NFR-A)"),
        ("Các nguyên tắc trên được cụ thể hoá thành bốn ràng buộc",
         "Bốn ràng buộc kiến trúc và hệ quả trực tiếp"),
        ("**Trách nhiệm của từng tầng:**",
         "Trách nhiệm của từng tầng trong kiến trúc phân tầng"),
        ("Toàn bộ các quyết định kiến trúc của hệ thống được ghi lại",
         "Các quyết định kiến trúc AD-01 … AD-08"),
        ("#### a) Bảng đặc tả endpoint", "Đặc tả các endpoint REST API"),
        ("#### a) Bảng `detection_job`", "Đặc tả trường của bảng `detection_job`"),
        ("#### b) Bảng `detection_history`", "Đặc tả trường của bảng `detection_history`"),
    ],
    "ch7-ket-luan.md": [
        ("Bảng dưới đây đặt cạnh nhau **chỉ tiêu đã cam kết ở Phase 0**",
         "Đối chiếu chỉ tiêu cam kết ở Phase 0 với số đo trên `best.pt`"),
    ],
}


def theo_moc(path: Path, moc: list[tuple[str, str]], ap: bool) -> None:
    """Chèn chú thích ngay trên bảng đầu tiên xuất hiện sau mỗi dòng mốc."""
    dong = path.read_text(encoding="utf-8").splitlines()
    chuong = path.name[2]
    for i, (mo, ten) in enumerate(moc, 1):
        vt = next((k for k, ln in enumerate(dong) if ln.startswith(mo)), None)
        if vt is None:
            print(f"  ⚠ {path.name}: không thấy mốc {mo[:44]!r}")
            continue
        # bang dau tien sau moc: dong '|' ma dong ke tiep la '|---|'
        b = next((k for k in range(vt + 1, min(vt + 40, len(dong) - 1))
                  if dong[k].startswith("|")
                  and re.match(r"^\|[\s:|-]+\|\s*$", dong[k + 1])), None)
        if b is None:
            print(f"  ⚠ {path.name}: không thấy bảng sau mốc {mo[:44]!r}")
            continue
        dong[b:b] = [f"**Bảng {chuong}.{i}.** {ten}", ""]
    print(f"{path.name:<28} thêm {len(moc)} chú thích theo mốc")
    if ap:
        path.write_text("\n".join(dong) + "\n", encoding="utf-8")


def main() -> None:
    ap = "--apply" in sys.argv
    if "--moc" in sys.argv:
        for ten, moc in THEO_MOC.items():
            theo_moc(PAPERS / ten, moc, ap)
        if not ap:
            print("\n(chạy khô — thêm --apply để ghi)")
        return
    for ten, bang in CHU_THICH.items():
        path = PAPERS / ten
        dong = path.read_text(encoding="utf-8").splitlines()
        chuong = ten[2]
        thu_tu = {neo: i for i, neo in enumerate(bang, 1)}
        ra: list[str] = []
        thay = 0
        for ln in dong:
            ra.append(ln)
            m = NEO.match(ln)
            if not m:
                continue
            neo = m.group(1)
            if neo not in bang:
                print(f"  ⚠ {ten}: neo {neo} chưa có chú thích")
                continue
            ra.append("")
            ra.append(f"**Bảng {chuong}.{thu_tu[neo]}.** {bang[neo]}")
            thay += 1
        print(f"{ten:<28} thêm {thay}/{len(bang)} chú thích")
        if ap:
            path.write_text("\n".join(ra) + "\n", encoding="utf-8")
    if not ap:
        print("\n(chạy khô — thêm --apply để ghi)")


if __name__ == "__main__":
    main()
