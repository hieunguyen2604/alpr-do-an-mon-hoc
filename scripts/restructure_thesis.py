"""Tái cấu trúc quyển đồ án từ 6 chương thành 7 chương.

Vì sao
------
Phần *"Lựa chọn công nghệ"* — thứ hội đồng hỏi nhiều nhất — đang là **§2.8, nằm
cuối một chương 1.193 dòng**. Người đọc mục lục không nhìn thấy nó. Cấu trúc mới
đưa nó thành **Chương 3** riêng, và gom phần huấn luyện mô hình (đang nằm rải ở
Chương 5 thực nghiệm) về cùng chỗ với phần cài đặt.

Bảng ánh xạ đầy đủ ở ``docs/papers/00-thesis-outline-v2.md``.

Điểm nguy hiểm nhất
-------------------
Mã bảng **va chạm**: ``T4.x`` cũ phải thành ``T5.x``, nhưng ``T5.x`` cũ cũng đang
tồn tại. Thay thế một pha sẽ ăn chồng lên nhau. Script dùng **thay thế hai pha**
qua ký hiệu tạm ``\\x00…\\x00`` để mọi phép đổi tên xảy ra đồng thời.

Chạy::

    backend/.venv/Scripts/python scripts/restructure_thesis.py           # chay kho
    backend/.venv/Scripts/python scripts/restructure_thesis.py --apply   # ghi that
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

for _l in (sys.stdout, sys.stderr):
    if hasattr(_l, "reconfigure"):
        _l.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
PAPERS = ROOT / "docs" / "papers"

# --------------------------------------------------------------------------
# Cau truc dich
# --------------------------------------------------------------------------

CHUONG_MOI: list[tuple[str, str]] = [
    ("ch1-gioi-thieu.md", "CHƯƠNG 1. GIỚI THIỆU"),
    ("ch2-co-so-ly-thuyet.md", "CHƯƠNG 2. CƠ SỞ LÝ THUYẾT"),
    ("ch3-khao-sat-lua-chon.md", "CHƯƠNG 3. KHẢO SÁT CÔNG NGHỆ VÀ LỰA CHỌN MÔ HÌNH"),
    ("ch4-phan-tich-thiet-ke.md", "CHƯƠNG 4. PHÂN TÍCH VÀ THIẾT KẾ HỆ THỐNG"),
    ("ch5-xay-dung-huan-luyen.md", "CHƯƠNG 5. XÂY DỰNG HỆ THỐNG VÀ HUẤN LUYỆN MÔ HÌNH"),
    ("ch6-thuc-nghiem.md", "CHƯƠNG 6. THỰC NGHIỆM VÀ ĐÁNH GIÁ"),
    ("ch7-ket-luan.md", "CHƯƠNG 7. KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN"),
]

NGUON = {
    1: "ch1-mo-dau.md",
    2: "ch2-tong-quan.md",
    3: "ch3-phan-tich-thiet-ke.md",
    4: "ch4-cai-dat.md",
    5: "ch5-thuc-nghiem.md",
    6: "ch6-ket-luan.md",
}

# (chuong dich, so muc moi, so muc cu, thang cap H3->H2?)
# Thu tu trong danh sach = thu tu xuat hien trong chuong dich.
KE_HOACH: list[tuple[int, str, str, bool]] = [
    # --- Chuong 1: giu nguyen ---
    *[(1, f"1.{i}", f"1.{i}", False) for i in range(1, 9)],
    # --- Chuong 2: bo §2.8, §2.9 -> §2.8 ---
    *[(2, f"2.{i}", f"2.{i}", False) for i in range(1, 8)],
    (2, "2.8", "2.9", False),
    # --- Chuong 3: MOI ---
    (3, "3.2", "2.8.1", True),
    (3, "3.3", "2.8.2", True),
    (3, "3.4", "2.8.3", True),
    (3, "3.5", "2.8.4", True),
    (3, "3.6", "5.8", False),
    # --- Chuong 4 <- ch3 ---
    *[(4, f"4.{i}", f"3.{i}", False) for i in range(1, 7)],
    # --- Chuong 5 <- ch4 + hai khoi chuyen sang ---
    (5, "5.1", "4.1", False),
    (5, "5.2", "4.5", False),
    (5, "5.3", "5.4", False),
    (5, "5.4", "5.6.8", True),
    (5, "5.5", "4.2", False),
    (5, "5.6", "4.3", False),
    (5, "5.7", "4.4", False),
    (5, "5.8", "4.6", False),
    (5, "5.9", "4.7", False),
    (5, "5.10", "4.8", False),
    # --- Chuong 6 <- ch5 con lai ---
    (6, "6.1", "5.1", False),
    (6, "6.2", "5.2", False),
    (6, "6.3", "5.3", False),
    (6, "6.4", "5.5", False),
    (6, "6.5", "5.6", False),
    (6, "6.6", "5.7", False),
    (6, "6.7", "5.9", False),
    (6, "6.8", "5.10", False),
    (6, "6.9", "5.11", False),
    (6, "6.10", "5.12", False),
    # --- Chuong 7 <- ch6 ---
    *[(7, f"7.{i}", f"6.{i}", False) for i in range(1, 6)],
]

# Khoi khong danh so, bam theo chuong dich va dat o cuoi.
KHOI_DUOI: list[tuple[int, int, str]] = [
    (1, 1, "Tóm tắt chương"),
    (6, 5, "Phụ lục kỹ thuật — Ánh xạ số liệu và lệnh tái lập"),
]

# Chuong cu -> chuong moi (dung cho "Chuong N" trong van xuoi).
CHUONG_MAP = {"1": "1", "2": "2", "3": "4", "4": "5", "5": "6", "6": "7"}

# Phan dan nhap dau tep: chuong nguon -> chuong dich.
DAN_NHAP = {1: 1, 2: 2, 3: 4, 4: 5, 5: 6, 6: 7}

# Muc cu nay da len thanh ca mot chuong, nen tham chieu toi no doi ca danh tu.
MUC_SANG_CHUONG = {"2.8": "Chương 3"}

# Chuoi TRONG NHU so muc nhung khong phai so muc. Danh sach nay ton tai vi so
# phien bien thu vien co dung dang `\d.\d.\d`: doi bua se bien
# "paddlepaddle 3.3.1" thanh "paddlepaddle 4.3.1" — mot loi khong ai doc ra khi
# soat ban in. Moi token bi chan o day deu duoc in ra o cuoi lan chay de kiem.
KHONG_PHAI_SO_MUC = {"3.3.1"}

FENCE = re.compile(r"^\s*(```|~~~)")
HEAD = re.compile(r"^(#{1,6})\s+(.*)$")
SO_MUC = re.compile(r"^(\d+(?:\.\d+)+)\.\s*(.*)$")


@dataclass
class Khoi:
    """Một khối nội dung: tiêu đề cộng toàn bộ phần thân tới tiêu đề cùng cấp."""

    cap: int
    so: str
    ten: str
    dong: list[str] = field(default_factory=list)


def tach(path: Path) -> tuple[list[str], list[Khoi], dict[str, Khoi]]:
    """Tách một tệp chương thành phần đầu và danh sách khối **cấp H2**.

    Chỉ cắt ở H2. Mọi H3/H4 nằm nguyên trong phần thân của H2 cha — cần bóc
    riêng thì dùng :func:`tach_h3`. Dòng bắt đầu bằng ``#`` **bên trong khối
    mã** không phải tiêu đề (ch3 có ``# Không được có...``, ch4 có
    ``# ai/evaluation/ocr_accuracy.py``) nên phải theo dõi hàng rào ```` ``` ````.
    """
    dau: list[str] = []
    khoi: list[Khoi] = []
    theo_so: dict[str, Khoi] = {}
    trong_fence = False
    hien: Khoi | None = None

    for ln in path.read_text(encoding="utf-8").splitlines():
        if FENCE.match(ln):
            trong_fence = not trong_fence
        m = None if trong_fence else HEAD.match(ln)
        if m and len(m.group(1)) == 2:
            sm = SO_MUC.match(m.group(2))
            hien = Khoi(2, sm.group(1) if sm else "", sm.group(2) if sm else m.group(2))
            khoi.append(hien)
            if hien.so:
                theo_so[hien.so] = hien
            continue
        (hien.dong if hien is not None else dau).append(ln)
    return dau, khoi, theo_so


def tach_h3(k: Khoi, so_h3: str) -> tuple[Khoi, list[str]]:
    """Bóc một mục con H3 ra khỏi khối H2 cha, trả về (khối con, phần còn lại)."""
    con: list[str] = []
    con_lai: list[str] = []
    dang_lay = False
    trong_fence = False
    ten = ""
    for ln in k.dong:
        if FENCE.match(ln):
            trong_fence = not trong_fence
        m = None if trong_fence else HEAD.match(ln)
        if m and len(m.group(1)) <= 3:
            sm = SO_MUC.match(m.group(2))
            so = sm.group(1) if sm else ""
            if so == so_h3:
                dang_lay = True
                ten = sm.group(2)
                continue
            if dang_lay and len(m.group(1)) <= 3:
                dang_lay = False
        (con if dang_lay else con_lai).append(ln)
    return Khoi(3, so_h3, ten, con), con_lai


def doi_so(dong: list[str], cu: str, moi: str, thang_cap: bool) -> list[str]:
    """Đổi tiền tố số của mọi tiêu đề con, và thăng cấp một bậc nếu cần."""
    ra: list[str] = []
    trong_fence = False
    for ln in dong:
        if FENCE.match(ln):
            trong_fence = not trong_fence
            ra.append(ln)
            continue
        m = HEAD.match(ln) if not trong_fence else None
        if m:
            sm = SO_MUC.match(m.group(2))
            if sm and (sm.group(1) == cu or sm.group(1).startswith(cu + ".")):
                so_moi = moi + sm.group(1)[len(cu):]
                dau = m.group(1)
                if thang_cap and len(dau) > 2:
                    dau = dau[:-1]
                ra.append(f"{dau} {so_moi}. {sm.group(2)}")
                continue
            if thang_cap and len(m.group(1)) > 2:
                ra.append("#" * (len(m.group(1)) - 1) + " " + m.group(2))
                continue
        ra.append(ln)
    return ra


def main() -> None:
    ap = "--apply" in sys.argv
    nguon = {n: tach(PAPERS / f) for n, f in NGUON.items()}

    # ---- gom noi dung theo chuong dich -------------------------------------
    ra: dict[int, list[str]] = {i: [] for i in range(1, 8)}
    muc_map: dict[str, str] = {}
    thieu: list[str] = []

    for dich, moi, cu, thang in KE_HOACH:
        ch_cu = int(cu.split(".")[0])
        _, _, theo_so = nguon[ch_cu]
        if cu.count(".") >= 2:
            # muc H3 — phai boc ra khoi H2 cha, va cha bi cat bot phan da boc
            cha = theo_so.get(cu.rsplit(".", 1)[0])
            if cha is None:
                thieu.append(f"{cu} (khong thay muc cha trong ch{ch_cu})")
                continue
            khoi, con_lai = tach_h3(cha, cu)
            if not khoi.ten:
                thieu.append(f"{cu} (khong thay tieu de con trong ch{ch_cu})")
                continue
            cha.dong = con_lai
        else:
            khoi = theo_so.get(cu)
            if khoi is None:
                thieu.append(f"{cu} (khong tim thay trong ch{ch_cu})")
                continue
        ra[dich].append(f"## {moi}. {khoi.ten}")
        ra[dich].extend(doi_so(khoi.dong, cu, moi, thang))
        muc_map[cu] = moi
        # anh xa cac muc con
        for ln in khoi.dong:
            m = HEAD.match(ln)
            if m:
                sm = SO_MUC.match(m.group(2))
                if sm and sm.group(1).startswith(cu + "."):
                    muc_map[sm.group(1)] = moi + sm.group(1)[len(cu):]

    if thieu:
        print("THIEU KHOI:")
        for t in thieu:
            print("  " + t)
        sys.exit(2)

    # ---- kiem tra khong mat chu --------------------------------------------
    # Moi khoi H2 nguon phai hoac duoc chuyen di, hoac chi con lai phan dan
    # nhap da co cho khac nhan. Bo qua buoc nay la cach de mat nguyen mot muc.
    da_dung = {cu for _, _, cu, _ in KE_HOACH}
    ten_duoi = {t for _, _, t in KHOI_DUOI}
    con_du: list[str] = []
    for n, (dau, khoi, _) in nguon.items():
        if n not in DAN_NHAP and [d for d in dau if d.strip() and not d.startswith("#")]:
            con_du.append(f"ch{n}: có chữ ở đầu tệp không được mang đi")
        for k in khoi:
            if k.so in da_dung or k.ten.strip() in ten_duoi:
                continue
            chu = [d for d in k.dong if d.strip()]
            con_du.append(f"ch{n} §{k.so or '—'} {k.ten[:40]!r}: {len(chu)} dòng chưa có chỗ")
    if con_du:
        print("NỘI DUNG CHƯA CÓ CHỖ ĐI:")
        for c in con_du:
            print("  " + c)
        print()

    # ---- khoi khong danh so o cuoi -----------------------------------------
    for dich, ch_cu, ten in KHOI_DUOI:
        _, khoi, _ = nguon[ch_cu]
        for k in khoi:
            if k.ten.strip() == ten:
                ra[dich].append(f"## {k.ten}")
                ra[dich].extend(k.dong)

    # ---- mang phan dan nhap sang chuong dich -------------------------------
    # Moi chuong mo bang mot doan cau noi ("Chuong N da trinh bay...") — bo di
    # la quyen mat mach.
    for ch_cu, ch_moi in DAN_NHAP.items():
        dau = [d for d in nguon[ch_cu][0] if not d.startswith("# ")]
        while dau and not dau[0].strip():
            dau.pop(0)
        ra[ch_moi] = dau + ra[ch_moi]

    # Doan dan nhap cua §2.8 la hat giong cua §3.1 (se viet tay sau).
    con_28 = [d for d in nguon[2][2]["2.8"].dong if d.strip()]

    # ---- danh so lai bang / hinh theo VI TRI MOI ---------------------------
    # Suy tu vi tri thay vi bang tay: neo va chu thich luon khop chuong chua no.
    neo_map: dict[str, str] = {}
    hinh_map: dict[str, str] = {}
    bang_map: dict[str, str] = {}
    NEO = re.compile(r"\{\{(T\d+(?:\.\d+)?[a-z]?)\}\}")
    CAP_HINH = re.compile(r"\*+(Hình) (\d+\.\d+)\.")
    CAP_BANG = re.compile(r"\*\*(Bảng) (\d+\.\d+)\.?\*\*")

    for i in range(1, 8):
        theo_muc: dict[str, list[str]] = {}
        muc_hien = ""
        dem_hinh = dem_bang = 0
        for ln in ra[i]:
            m = HEAD.match(ln)
            if m and len(m.group(1)) == 2:
                sm = SO_MUC.match(m.group(2))
                muc_hien = sm.group(1) if sm else muc_hien
            for neo in NEO.findall(ln):
                theo_muc.setdefault(muc_hien, []).append(neo)
            for _, so in CAP_HINH.findall(ln):
                dem_hinh += 1
                hinh_map[so] = f"{i}.{dem_hinh}"
            for _, so in CAP_BANG.findall(ln):
                dem_bang += 1
                bang_map[so] = f"{i}.{dem_bang}"
        for muc, ds in theo_muc.items():
            for j, neo in enumerate(ds):
                hau = "" if len(ds) == 1 else chr(ord("a") + j)
                neo_map[neo] = f"T{muc}{hau}"

    # ---- doi so trong van xuoi: MOT luot quet, moi vi tri cham dung mot lan -
    # Mot phan dang tham chieu KHONG co tu dan ("xem 5.8.1", "Theo T5.5a",
    # "han che 6.3.3"). Duoi theo tung gioi tu la tro chuot-duoi-meo, nen dung
    # quy tac chung:
    #   - ma bang "T5.6a" la duy nhat, doi o bat ky dau;
    #   - so muc BA thanh phan ("6.3.3") cung gan nhu duy nhat, vi so lieu tieng
    #     Viet dung dau cham lam dau phan cach hang nghin nen luon co DUNG BA
    #     chu so sau dau cham ("2.801", "15.133") — {1,2} loai het;
    #   - so muc HAI thanh phan van doi hoi tu dan, vi "3.13" / "2.0" / "0.5"
    #     xuat hien that trong van ban (phien ban thu vien, nguong IoU).
    DAN = r"(?i:xem|ở|tại|theo|nêu ở|trình bày ở|hạn chế|đóng góp)\s+"
    QUET = re.compile(
        r"(?P<chuong>\bChương\s+(?P<cs>\d+)\b)"
        r"|(?P<muc>\b[Mm]ục\s+(?P<ms>\d+(?:\.\d+){1,2})\b)"
        r"|(?P<neo>\{\{(?P<ns>T\d+(?:\.\d+)?[a-z]?)\}\})"
        r"|(?P<bangT>\b[Bb]ảng\s+(?P<bts>T\d+(?:\.\d+)?[a-z]?)\b)"
        r"|(?P<hinh>\b(?P<hw>[Hh]ình)\s+(?P<hs>\d+\.\d+)\b)"
        r"|(?P<bang>\b(?P<bw>[Bb]ảng)\s+(?P<bs>\d+\.\d+)\b)"
        # Dang tran — chi doi khi tra duoc trong bang anh xa, nen "tren 2.801
        # bien" hay "o 1.565 anh" khong bi dong vao vi chung khong phai so muc.
        rf"|(?P<tranM>(?<![\w.]){DAN}(?P<tms>\d\.\d{{1,2}})(?![\d.]))"
        # So muc BA thanh phan doi o moi noi — chung xuat hien trong o bang,
        # trong nhan so do mermaid, sau dau phay — doi hoi tu dan se bo sot 81
        # cho. An toan nho hai lop: phai tra duoc trong bang anh xa, va phai
        # khong nam trong KHONG_PHAI_SO_MUC.
        r"|(?P<tran3>(?<![\w.\-])(?P<t3s>\d\.\d{1,2}\.\d{1,2})(?![\d.]))"
        r"|(?P<tranT>(?<![\w.\-])(?P<tts>T\d+(?:\.\d+)?[a-z]?)\b)"
        # Nhanh CUOI CUNG, chi bat nhung gi cac nhanh tren khong nuot: token
        # trong nhu so muc nhung khong co ngu canh tham chieu. Khong doi gi ca,
        # chi ghi lai de nguoi soat. Phai dat o day — soat tren ban DA doi thi
        # khong con phan biet duoc "chua doi" voi "doi roi, trung so cu".
        r"|(?P<soat>(?<![\w.\-])(?P<ss>\d\.\d{1,2}\.\d{1,2})(?![\d.]))"
    )
    can_soat: list[str] = []
    bi_chan: list[str] = []
    dem = {"chuong": 0, "muc": 0, "neo": 0, "bangT": 0, "hinh": 0, "bang": 0,
           "tranM": 0, "tran3": 0, "tranT": 0}
    bo_qua: list[str] = []

    def thay(m: re.Match[str], dong: str) -> str:
        g = m.lastgroup
        if m.group("chuong"):
            moi = CHUONG_MAP.get(m.group("cs"))
            if moi:
                dem["chuong"] += 1
                return f"Chương {moi}"
        elif m.group("muc"):
            # "docs/reports/....md muc 7.3" tro sang tep khac, khong doi.
            if ".md" in dong[: m.start()]:
                return m.group(0)
            if m.group("ms") in MUC_SANG_CHUONG:
                dem["muc"] += 1
                return MUC_SANG_CHUONG[m.group("ms")]
            moi = muc_map.get(m.group("ms"))
            if moi:
                dem["muc"] += 1
                return f"{m.group(0)[:3]} {moi}"  # giu nguyen 'muc' hay 'Muc'
            bo_qua.append(f"mục {m.group('ms')}")
        elif m.group("neo"):
            moi = neo_map.get(m.group("ns"))
            if moi:
                dem["neo"] += 1
                return "{{" + moi + "}}"
        elif m.group("bangT"):
            moi = neo_map.get(m.group("bts"))
            if moi:
                dem["bangT"] += 1
                return m.group(0).replace(m.group("bts"), moi)
        elif m.group("hinh"):
            moi = hinh_map.get(m.group("hs"))
            if moi:
                dem["hinh"] += 1
                return f"{m.group('hw')} {moi}"
        elif m.group("bang"):
            moi = bang_map.get(m.group("bs"))
            if moi:
                dem["bang"] += 1
                return f"{m.group('bw')} {moi}"
        elif m.group("tranM"):
            moi = muc_map.get(m.group("tms"))
            if moi:
                dem["tranM"] += 1
                return m.group(0).replace(m.group("tms"), moi)
        elif m.group("tran3"):
            if m.group("t3s") in KHONG_PHAI_SO_MUC:
                bi_chan.append(f"  {m.group('t3s')}  …{dong[max(0, m.start() - 46):m.end() + 22].strip()}…")
                return m.group(0)
            moi = muc_map.get(m.group("t3s"))
            if moi:
                dem["tran3"] += 1
                return moi
        elif m.group("tranT"):
            moi = neo_map.get(m.group("tts"))
            if moi:
                dem["tranT"] += 1
                return m.group(0).replace(m.group("tts"), moi)
        elif m.group("soat") and m.group("ss") in muc_map:
            if muc_map[m.group("ss")] != m.group("ss"):
                vt = m.start()
                can_soat.append(
                    f"  {m.group('ss')} → {muc_map[m.group('ss')]}?  "
                    f"…{dong[max(0, vt - 48):vt + 24].strip()}…"
                )
        return m.group(0)

    def quet_dong(ln: str) -> str:
        """Quét một dòng, nhưng **không đụng vào phần số của tiêu đề**.

        Tiêu đề đã được :func:`doi_so` đánh số xong. Quét lại chính phần số ấy
        là cơ hội duy nhất tạo va chạm — mục mới ``5.5.3`` trùng đúng mã cũ của
        một mục khác và sẽ bị đổi lần thứ hai. Nhưng phần **chữ** của tiêu đề
        thì vẫn phải quét, vì có tiêu đề nhắc tên chương (§4.7 cũ: *"lệch khỏi
        thiết kế ở Chương 3"*).
        """
        m = HEAD.match(ln)
        if not m:
            return QUET.sub(lambda x: thay(x, ln), ln)
        sm = SO_MUC.match(m.group(2))
        if not sm:
            return ln
        chu = QUET.sub(lambda x, d=sm.group(2): thay(x, d), sm.group(2))
        return f"{m.group(1)} {sm.group(1)}. {chu}"

    for i in range(1, 8):
        ra[i] = [quet_dong(ln) for ln in ra[i]]

    # ---- bao cao -----------------------------------------------------------
    print(f"Ánh xạ mục   : {len(muc_map)} mục, {sum(a != b for a, b in muc_map.items())} đổi số")
    print(f"Neo bảng     : {sum(a != b for a, b in neo_map.items())}/{len(neo_map)} đổi mã")
    print(f"Chú thích    : {sum(a != b for a, b in hinh_map.items())} hình, "
          f"{sum(a != b for a, b in bang_map.items())} bảng đổi số")
    print("Đã thay      : " + ", ".join(f"{k}={v}" for k, v in dem.items()))
    if bi_chan:
        print(f"\n🔒 {len(bi_chan)} chỗ bị chặn vì nằm trong KHÔNG_PHẢI_SỐ_MỤC — "
              f"xác nhận đúng là số phiên bản:")
        for c in bi_chan:
            print(c)
    if can_soat:
        print(f"\n⚠ {len(can_soat)} chỗ trùng dạng số mục nhưng KHÔNG đổi tự động — soát tay:")
        for c in can_soat:
            print(c)
        print()
    if bo_qua:
        print(f"⚠ Không tra được {len(bo_qua)} tham chiếu: {sorted(set(bo_qua))}")
    print(f"§2.8 còn {len(con_28)} dòng dẫn nhập → dùng làm hạt giống §3.1\n")
    for i, (fn, _) in enumerate(CHUONG_MOI, 1):
        print(f"  Chương {i}  {fn:<30} {len(ra[i]):>5} dòng")

    if not ap:
        print("\n(chạy khô — thêm --apply để ghi)")
        return

    # ---- ghi ---------------------------------------------------------------
    for i, (fn, tieu_de) in enumerate(CHUONG_MOI, 1):
        than = [f"# {tieu_de}", ""] + ra[i]
        (PAPERS / fn).write_text("\n".join(than).rstrip() + "\n", encoding="utf-8")
    (PAPERS / "_seed-3.1.md").write_text("\n".join(con_28) + "\n", encoding="utf-8")
    for f in NGUON.values():
        (PAPERS / f).unlink()
    print("\nĐã ghi 7 tệp chương mới, xoá 6 tệp cũ.")


if __name__ == "__main__":
    main()
