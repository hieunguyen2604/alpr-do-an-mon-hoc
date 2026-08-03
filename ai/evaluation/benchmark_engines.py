"""So sánh PaddleOCR, EasyOCR và Tesseract trên cùng ảnh biển số Việt Nam.

Vì sao phép đo này tồn tại
--------------------------
Khảo sát Phase 1 kết luận **không tồn tại benchmark công khai nào so sánh các
engine OCR trên riêng ảnh biển số xe máy Việt Nam hai dòng**, và hai số liệu
thường được viện dẫn để chứng minh ưu thế của PaddleOCR đã bị bác bỏ khi truy
ngược nguồn — cả hai đến từ một bài dùng **EasyOCR**. Quyển đồ án vì vậy ghi
phép so sánh này là *"chưa đo lần nào"* suốt một thời gian dài. Đây là công cụ
lấp khoản nợ đó.

Nguyên tắc công bằng: **chỉ thay engine, giữ nguyên mọi thứ khác**
-------------------------------------------------------------------
Cách làm ngây thơ — gọi thẳng ``PaddleOCR.predict``, ``easyocr.readtext`` và
``pytesseract.image_to_string`` rồi so kết quả — đã được thử và **cho số vô
nghĩa**: cả ba đọc hỏng gần hết. Lý do: phần lớn năng lực đọc biển số của hệ
thống không nằm trong engine mà nằm ở **tầng bao quanh** engine — ước lượng số
dòng theo tỷ lệ khung, tách-rồi-ghép-ngang cho biển hai dòng, nâng tương phản
CLAHE, khử nhiễu, chuẩn hoá chiều cao về 64 px.

So sánh ba engine với ba tầng bao quanh khác nhau thì đo tầng bao quanh chứ
không đo engine. Vì vậy công cụ này dựng **đúng một tầng bao quanh** — sao đúng
chuỗi bước của :meth:`ai.inference.recognizer.PaddleOcrRecognizer.recognize` —
rồi cho cả ba engine chạy trên **cùng một mảng NumPy đã chuẩn bị xong**. Khác
biệt duy nhất còn lại là engine.

Đây cũng là điều NFR-M5 khẳng định: thay module nhận dạng không đụng tới phần
còn lại của hệ thống. Phép đo này là bằng chứng thực nghiệm cho khẳng định đó.

Ba nhánh
--------
=============  ==============================================================
Nhánh          Đo cái gì
=============  ==============================================================
``nosplit``    Tắt tách-rồi-ghép-ngang. Engine nhìn thẳng biển hai dòng.
``raw``        Bật tách-rồi-ghép-ngang, lấy chuỗi thô. **So sánh engine.**
``post``       Thêm bộ luật hậu xử lý theo vị trí, áp như nhau cho cả ba.
=============  ==============================================================

Chênh lệch ``raw`` − ``nosplit`` **trên từng engine** trả lời câu hỏi có giá trị
khoa học nhất: tách-rồi-ghép-ngang phụ thuộc engine, hay nó giúp mọi engine? Nếu
cả ba cùng tăng thì đóng góp kỹ thuật của đồ án độc lập với engine — một khẳng
định mạnh hơn hẳn *"nó giúp cấu hình của chúng tôi"*.

Hai điều phép đo này KHÔNG trả lời
-----------------------------------
1. Nó đo trên **vùng biển đã cắt sẵn**. Báo cáo 31 cho thấy thứ tự xếp hạng có
   thể **đảo ngược** khi chuyển sang ảnh toàn cảnh qua bộ phát hiện thật.
2. Nó **không** kết luận engine nào tốt hơn nói chung — chỉ kết luận engine nào
   đọc biển số Việt Nam tốt hơn *bên trong tầng bao quanh của đồ án*.

Chạy::

    backend/.venv/Scripts/python -m ai.evaluation.benchmark_engines --limit 200
    backend/.venv/Scripts/python -m ai.evaluation.benchmark_engines   # toan bo
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import statistics as st
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import cv2
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai.evaluation.ocr_accuracy import restore_aspect_ratio  # noqa: E402
from ai.inference.normalizer import VietnamesePlateNormalizer  # noqa: E402
from ai.inference.plate_rules import clean_text  # noqa: E402
from ai.inference.recognizer import _drop_short_fragments  # noqa: E402
from ai.inference.two_line import (  # noqa: E402
    estimate_line_count,
    merge_two_line,
    preprocess_plate,
    split_two_line,
)

for _l in (sys.stdout, sys.stderr):
    if hasattr(_l, "reconfigure"):
        _l.reconfigure(encoding="utf-8", errors="replace")

NHAN = PROJECT_ROOT / "datasets" / "annotations" / "plate_labels.csv"
KET_QUA = PROJECT_ROOT / "docs" / "reports" / "36-engine-benchmark.json"

# Giong het PaddleOcrRecognizer: chuan hoa chieu cao ve 64 px truoc khi doc.
CHIEU_CAO_OCR = 64
NGUONG_HAI_DONG = 2.5
CHU_SO = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
_NORM = VietnamesePlateNormalizer()

NHANH: dict[str, bool] = {"nosplit": False, "raw": True, "post": True}


@dataclass(slots=True)
class Mau:
    duong_dan: Path
    chuoi_dung: str
    so_dong: int


@dataclass
class KetQua:
    """Kết quả tích luỹ của một engine trên một nhánh."""

    engine: str
    nhanh: str
    dung: int = 0
    tong: int = 0
    dung_1: int = 0
    tong_1: int = 0
    dung_2: int = 0
    tong_2: int = 0
    tong_cer: float = 0.0
    ms: list[float] = field(default_factory=list)
    rong: int = 0
    sai: list[dict[str, str]] = field(default_factory=list)

    def ghi(self, truth: str, pred: str, so_dong: int, ms: float) -> None:
        self.tong += 1
        self.ms.append(ms)
        khop = pred == truth
        self.dung += khop
        self.rong += not pred
        if so_dong == 1:
            self.tong_1 += 1
            self.dung_1 += khop
        else:
            self.tong_2 += 1
            self.dung_2 += khop
        self.tong_cer += _levenshtein(truth, pred) / max(len(truth), 1)
        if not khop and len(self.sai) < 20:
            self.sai.append({"dung": truth, "doc_ra": pred})

    def tom_tat(self) -> dict[str, Any]:
        ms = sorted(self.ms)

        def pct(f: float) -> float:
            return round(ms[min(int(len(ms) * f), len(ms) - 1)], 2) if ms else 0.0

        def ty_le(a: int, b: int) -> float | None:
            return round(a / b, 4) if b else None

        return {
            "engine": self.engine,
            "nhanh": self.nhanh,
            "mau": self.tong,
            "dung_chuoi": self.dung,
            "do_chinh_xac": ty_le(self.dung, self.tong),
            "mot_dong": {"mau": self.tong_1, "dung": self.dung_1,
                         "do_chinh_xac": ty_le(self.dung_1, self.tong_1)},
            "hai_dong": {"mau": self.tong_2, "dung": self.dung_2,
                         "do_chinh_xac": ty_le(self.dung_2, self.tong_2)},
            "chenh_lech_layout_diem": (
                round((self.dung_1 / self.tong_1 - self.dung_2 / self.tong_2) * 100, 2)
                if self.tong_1 and self.tong_2 else None),
            "cer": round(self.tong_cer / self.tong, 4) if self.tong else None,
            "chuoi_rong": self.rong,
            "ms": {"trung_vi": pct(0.5), "p95": pct(0.95), "p99": pct(0.99),
                   "trung_binh": round(st.fmean(ms), 2) if ms else 0.0},
            "vi_du_sai": self.sai[:10],
        }


def _levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a or not b:
        return max(len(a), len(b))
    truoc = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        hien = [i]
        for j, cb in enumerate(b, 1):
            hien.append(min(truoc[j] + 1, hien[j - 1] + 1, truoc[j - 1] + (ca != cb)))
        truoc = hien
    return truoc[-1]


# --------------------------------------------------------------------------
# Tang bao quanh DUNG CHUNG — sao dung chuoi buoc cua PaddleOcrRecognizer
# --------------------------------------------------------------------------

def chuan_bi(anh: np.ndarray, tach_hai_dong: bool) -> np.ndarray:
    """Chuẩn bị ảnh y hệt bộ nhận dạng của hệ thống, trước khi engine nhìn thấy.

    Args:
        anh: Vùng biển đã cắt, BGR, đã khôi phục tỷ lệ khung hình.
        tach_hai_dong: Có áp bước tách-rồi-ghép-ngang không. Tắt để đo bước này
            đóng góp bao nhiêu cho *từng* engine.
    """
    vao = anh
    if tach_hai_dong and estimate_line_count(anh, NGUONG_HAI_DONG) == 2:
        tren, duoi = split_two_line(vao)
        vao = merge_two_line(tren, duoi)
    return preprocess_plate(
        vao,
        upscale_to_height=CHIEU_CAO_OCR,
        downscale_to_height=CHIEU_CAO_OCR,
    )


# --------------------------------------------------------------------------
# Ba engine — moi ham nhan anh DA CHUAN BI, tra [(trai, cao, chu)]
#
# Tra ve HINH HOC chu khong chi chu, vi buoc loc manh vun phia sau can no. Buoc
# loc do (`_drop_short_fragments`) la mot heuristic hinh hoc TONG QUAT — bo manh
# thap hon nhieu so voi manh cao nhat — chu khong phai thu rieng cua PaddleOCR.
# Bo phep loc nay di thi PaddleOCR tu 65% tut xuong 40% chi vi cac manh rac
# "JJ", "JJR" o mep dai ghep (da do). Ap no cho ca ba engine moi la cong bang.
# --------------------------------------------------------------------------


def _loc_va_sap(manh: list[tuple[float, float, str]]) -> list[str]:
    """Bỏ mảnh vụn theo chiều cao rồi sắp trái-sang-phải, y hệt hệ thống."""
    day_du = [(trai, cao, chu, 0.0) for trai, cao, chu in manh]
    giu = _drop_short_fragments(day_du)
    giu.sort(key=lambda m: m[0])
    return [chu for _, _, chu, _ in giu]

def dung_paddle() -> Callable[[np.ndarray], list[str]]:
    from paddleocr import PaddleOCR

    # Phai truyen CA HAI ten model. Chi truyen mot thi PaddleOCR 3.7 bo qua
    # lang/ocr_version cho cai con lai va am tham nap PP-OCRv6_medium — mot the
    # he model KHAC HAN. Bay nay da duoc ghi o ai/inference/recognizer.py, va
    # lan chay thu dau tien cua chinh tep nay da vap dung vao no.
    #
    # enable_mkldnn=False: backend oneDNN lam SAP suy luan tren
    # PP-OCRv5_mobile_det (NotImplementedError trong
    # ConvertPirAttribute2RuntimeAttribute). Ban giao hang tat no vi dung ly do
    # nay (muc 5.5.4), nen phep do phai chay dung cau hinh do.
    engine = PaddleOCR(
        text_detection_model_name="PP-OCRv5_mobile_det",
        text_recognition_model_name="en_PP-OCRv5_mobile_rec",
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
        enable_mkldnn=False,
    )

    def doc(anh: np.ndarray) -> list[tuple[float, float, str]]:
        try:
            kq = engine.predict(anh)
        except Exception:  # noqa: BLE001 — mot anh hong khong duoc dung ca luot do
            return []
        if not kq:
            return []
        r = kq[0]
        texts = [str(x) for x in (r.get("rec_texts") or [])]
        hop = r.get("rec_polys")
        if hop is None:
            hop = r.get("dt_polys")
        ra: list[tuple[float, float, str]] = []
        for i, chu in enumerate(texts):
            if not chu:
                continue
            if hop is not None and i < len(hop):
                pts = np.asarray(hop[i], dtype=float)
                ra.append((float(pts[:, 0].min()),
                           float(pts[:, 1].max() - pts[:, 1].min()), chu))
            else:
                ra.append((float(i), 0.0, chu))
        return ra

    return doc


def dung_easyocr() -> Callable[[np.ndarray], list[str]]:
    import easyocr

    engine = easyocr.Reader(["en"], gpu=False, verbose=False)

    def doc(anh: np.ndarray) -> list[tuple[float, float, str]]:
        try:
            kq = engine.readtext(anh, detail=1, paragraph=False)
        except Exception:  # noqa: BLE001
            return []
        ra: list[tuple[float, float, str]] = []
        for hop, chu, _score in kq:
            if not chu:
                continue
            ys = [p[1] for p in hop]
            ra.append((float(min(p[0] for p in hop)),
                       float(max(ys) - min(ys)), str(chu)))
        return ra

    return doc


def dung_tesseract() -> Callable[[np.ndarray], list[str]]:
    import pytesseract

    duong_dan = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
    if duong_dan.is_file():
        pytesseract.pytesseract.tesseract_cmd = str(duong_dan)

    # psm 7 = "mot dong van ban duy nhat". Sau khi da ghep ngang thi day la gia
    # thiet DUNG, khong phai gia thiet uu ai Tesseract.
    #
    # Whitelist la nang luc GOC cua Tesseract ma hai engine kia khong co (muc
    # 3.3.1). Bo no di "cho cong bang" chinh la lam sai — no dim Tesseract
    # xuong duoi muc that cua no.
    cau_hinh = f"--oem 3 --psm 7 -c tessedit_char_whitelist={CHU_SO}"

    def doc(anh: np.ndarray) -> list[tuple[float, float, str]]:
        # image_to_data thay vi image_to_string: can hop bao cua tung manh de
        # ap DUNG bo loc hinh hoc ma hai engine kia cung chiu.
        try:
            d = pytesseract.image_to_data(anh, config=cau_hinh,
                                          output_type=pytesseract.Output.DICT)
        except Exception:  # noqa: BLE001
            return []
        ra: list[tuple[float, float, str]] = []
        for i, chu in enumerate(d.get("text", [])):
            chu = (chu or "").strip()
            if chu:
                ra.append((float(d["left"][i]), float(d["height"][i]), chu))
        return ra

    return doc


ENGINES: dict[str, Callable[[], Callable[[np.ndarray], list[tuple[float, float, str]]]]] = {
    "paddleocr": dung_paddle,
    "easyocr": dung_easyocr,
    "tesseract": dung_tesseract,
}


def doc_nhan(gioi_han: int = 0) -> list[Mau]:
    if not NHAN.is_file():
        raise SystemExit(f"Khong thay tep nhan: {NHAN}")
    ra: list[Mau] = []
    with NHAN.open(encoding="utf-8-sig", newline="") as fh:
        for hang in csv.DictReader(fh):
            try:
                so_dong = int((hang.get("line_count") or "0").strip())
            except ValueError:
                continue
            chuoi = clean_text((hang.get("plate_text") or "").strip())
            p = Path((hang.get("image_path") or "").strip())
            if not chuoi or so_dong not in (1, 2) or not p.is_file():
                continue
            ra.append(Mau(p, chuoi, so_dong))
    if gioi_han and gioi_han < len(ra):
        # Cung seed voi ocr_accuracy.py: mot lan chay thu khong duoc thien ve
        # bo du lieu nao tinh co dung dau danh sach.
        random.Random(20260719).shuffle(ra)
        ra = ra[:gioi_han]
    return ra


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--limit", type=int, default=0, help="so mau (0 = toan bo)")
    ap.add_argument("--engines", nargs="+", default=list(ENGINES), choices=list(ENGINES))
    ap.add_argument("--nhanh", nargs="+", default=list(NHANH), choices=list(NHANH))
    ap.add_argument("--out", type=Path, default=KET_QUA)
    args = ap.parse_args()

    mau = doc_nhan(args.limit)
    n1 = sum(1 for m in mau if m.so_dong == 1)
    print(f"Ngữ liệu: {len(mau)} biển ({n1} một dòng, {len(mau) - n1} hai dòng)")
    print(f"Engine  : {', '.join(args.engines)}")
    print(f"Nhánh   : {', '.join(args.nhanh)}\n")

    # `restore_aspect_ratio` KHONG phai tien xu ly rieng cua do an — no khoi
    # phuc mot thu bo du lieu da pha: anh Roboflow xuat o khung vuong nen ty le
    # khung hinh that cua bien so bi bop meo. Bo buoc nay thi CA BA engine deu
    # doc ra gan nhu 0% (da do thu).
    print("Nạp ảnh…", end=" ", flush=True)
    goc: list[np.ndarray | None] = []
    for m in mau:
        a = cv2.imread(str(m.duong_dan))
        goc.append(None if a is None else restore_aspect_ratio(a, m.so_dong))
    hong = sum(1 for a in goc if a is None)
    print(f"xong ({hong} ảnh hỏng)")

    # Chuan bi TRUOC cho ca hai che do: bao dam ba engine nhan dung cung mot
    # mang NumPy, chu khong chi "cung quy trinh".
    print("Chuẩn bị ảnh…", end=" ", flush=True)
    da_chuan_bi: dict[bool, list[np.ndarray | None]] = {
        tach: [None if a is None else chuan_bi(a, tach) for a in goc]
        for tach in {NHANH[n] for n in args.nhanh}
    }
    print("xong\n")

    ket: list[dict[str, Any]] = []
    for ten in args.engines:
        print(f"── {ten} ──", flush=True)
        t0 = time.perf_counter()
        doc = ENGINES[ten]()
        print(f"   nạp engine: {time.perf_counter() - t0:.1f}s", flush=True)
        for a in next(iter(da_chuan_bi.values()))[:3]:  # lam nong
            if a is not None:
                doc(a)
        for nhanh in args.nhanh:
            kq = KetQua(ten, nhanh)
            anh_vao = da_chuan_bi[NHANH[nhanh]]
            for i, (m, a) in enumerate(zip(mau, anh_vao, strict=True)):
                if a is None:
                    continue
                t = time.perf_counter()
                manh = _loc_va_sap(doc(a))
                ms = (time.perf_counter() - t) * 1000
                tho = clean_text("".join(manh))
                pred = (_NORM.normalize_detailed(tho, line_count=m.so_dong).text
                        if nhanh == "post" else tho)
                kq.ghi(m.chuoi_dung, pred, m.so_dong, ms)
                if (i + 1) % 500 == 0:
                    print(f"   {nhanh}: {i + 1}/{len(mau)} — đúng "
                          f"{kq.dung / kq.tong * 100:.1f}%", flush=True)
            s = kq.tom_tat()
            ket.append(s)
            print(f"   {nhanh:<8} → {s['do_chinh_xac'] * 100:5.2f}%   "
                  f"(1 dòng {(s['mot_dong']['do_chinh_xac'] or 0) * 100:5.1f}% · "
                  f"2 dòng {(s['hai_dong']['do_chinh_xac'] or 0) * 100:5.1f}%)   "
                  f"trung vị {s['ms']['trung_vi']:.0f} ms", flush=True)
        print(flush=True)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({
        "ngu_lieu": {"tep": "datasets/annotations/plate_labels.csv", "mau": len(mau),
                     "mot_dong": n1, "hai_dong": len(mau) - n1, "anh_hong": hong},
        "ket_qua": ket,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Đã ghi {args.out}")


if __name__ == "__main__":
    main()
