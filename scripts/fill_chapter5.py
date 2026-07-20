"""Chay toan bo phep do cua Chuong 5 va xuat so lieu theo dung ma bang.

Script nay KHONG cai dat lai bat ky phep do nao. No dieu phoi cac module da co
trong ``ai/evaluation/`` (evaluate, ocr_accuracy, benchmark_system,
benchmark_cpu, stress_test, error_analysis), doc lai cac tep JSON ma chung sinh
ra, roi ep du lieu ve **dung cau truc cot cua tung bang trong**
``docs/papers/ch5-thuc-nghiem.md``.

Ba nguyen tac bat buoc (khong duoc vi pham trong bat ky nhanh ma nao):

1. **Khong bao gio bia so.** Mot phep do that bai se ghi
   ``{"trang_thai": "chua do", "ly_do": ...}`` vao JSON va ``—`` vao Markdown.
   Khong dien ``0``, khong dien ``null`` im lang, khong lam sap ca script.
2. **Moi con so hieu nang di kem cau hinh phan cung.** Khoi ``_meta`` cua tep
   JSON ghi CPU, so nhan, RAM, he dieu hanh, phien ban Python/torch/ultralytics,
   duong dan trong so, ten bo du lieu, so anh tap test va thoi diem do. Doan
   Markdown lap lai khoi nay ngay dau tep.
3. **Moi bang ghi ro mau so.** So anh / so doi tuong / so bien co nhan chuoi cua
   tung phep do luon duoc ghi ra, khong duoc giau.

Cach chay (dung venv day du ca AI lan backend)::

    backend/.venv/Scripts/python.exe scripts/fill_chapter5.py --dry-run
    backend/.venv/Scripts/python.exe scripts/fill_chapter5.py --skip-slow
    backend/.venv/Scripts/python.exe scripts/fill_chapter5.py

Xem them ``scripts/README-fill-chapter5.md``.
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import platform
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

LOGGER = logging.getLogger("fill_chapter5")

# --------------------------------------------------------------------------- #
# Hang so
# --------------------------------------------------------------------------- #

#: Gia tri danh dau mot o chua do duoc. Dung mot hang so thay vi chuoi roi de
#: khong noi nao trong script vo tinh viet sai chinh ta va lam o do bi doc nham
#: thanh mot gia tri hop le.
NOT_MEASURED: str = "chua do"

#: Ky hieu dien vao o Markdown khi khong co so.
EM_DASH: str = "—"

DEFAULT_WEIGHTS = PROJECT_ROOT / "models" / "best.pt"
FALLBACK_WEIGHTS = PROJECT_ROOT / "models" / "baseline-416-v1.pt"
DEFAULT_DATA_YAML = PROJECT_ROOT / "datasets" / "processed" / "yolo_v3" / "data.yaml"
DEFAULT_OUT_JSON = PROJECT_ROOT / "docs" / "reports" / "05-results.json"
DEFAULT_OUT_MD = PROJECT_ROOT / "docs" / "reports" / "05-tables.md"

#: Noi cac tep trung gian cua mot luot chay --skip-slow di vao. Luot chay thu do
#: tren rat it mau, nen neu no ghi de len hinh va bao cao cong bo thi cac tep do
#: se im lang tro thanh so lieu rac ma khong ai biet. Vi vay che do chay thu bi
#: cach ly hoan toan sang thu muc rieng.
SMOKE_DIR = PROJECT_ROOT / "docs" / "reports" / "05-smoke"

#: Cac vi tri co the chua nhan chuoi bien so, thu theo thu tu uu tien.
LABEL_CANDIDATES: tuple[Path, ...] = (
    PROJECT_ROOT / "datasets" / "annotations" / "plate_labels.csv",
    PROJECT_ROOT / "datasets" / "annotations" / "plate_text_labels.csv",
)

#: Cac dai kich thuoc hop gioi han cua bang T5.5c, theo ti le dien tich box /
#: dien tich anh. Bien duoi bao gom, bien tren khong bao gom.
SIZE_BANDS: tuple[tuple[str, float, float], ...] = (
    ("rat_nho_duoi_0.5%", 0.0, 0.005),
    ("nho_0.5_den_1%", 0.005, 0.01),
    ("trung_binh_1_den_5%", 0.01, 0.05),
    ("lon_5_den_15%", 0.05, 0.15),
    ("rat_lon_tren_15%", 0.15, float("inf")),
)

SIZE_BAND_LABELS_VI: dict[str, str] = {
    "rat_nho_duoi_0.5%": "**Rất nhỏ** — dưới 0,5%",
    "nho_0.5_den_1%": "**Nhỏ** — 0,5% đến 1%",
    "trung_binh_1_den_5%": "**Trung bình** — 1% đến 5%",
    "lon_5_den_15%": "**Lớn** — 5% đến 15%",
    "rat_lon_tren_15%": "**Rất lớn** — trên 15%",
}

#: Cac nguong Hamming dung kiem chung ro ri o bang T5.3b. Bat buoc phai co ca
#: nguong LON HON nguong gop trung lap (10), vi chi nhung nguong do moi mang
#: thong tin moi — do o dung nguong gop la kiem tra lai chinh dinh nghia.
LEAK_THRESHOLDS: tuple[int, ...] = (0, 5, 10, 12, 15, 20)

#: Nguong Hamming da dung de khu trung lap khi dung bo du lieu v3.
DEDUP_THRESHOLD_V3: int = 10

#: Cot dien giai cua bang T5.3b — day la van ban bien tap lay nguyen tu Chuong 5,
#: KHONG phai gia tri do duoc.
LEAK_THRESHOLD_NOTE: dict[int, str] = {
    0: "Có",
    5: "Không với v1, v2 (bằng ngưỡng gộp của chúng)",
    10: "**Không với v3** — bằng ngưỡng gộp",
    12: "**Có**",
    15: "**Có**",
    20: "Có, nhưng ngưỡng đã lỏng tới mức nhiều cặp là dương tính giả",
}

#: So cap ro ri da do truoc do tren v1 va v2, tai nguong 10. Day la so DA CO,
#: khong phai so script nay do lai — hai bo du lieu do khong con duoc danh gia.
V1_V2_LEAK_PAIRS: dict[str, int] = {"v1": 619, "v2": 2699}

#: So anh moi split duoc bam khi chay --skip-slow. Bam toan bo 10.592 anh train
#: mat rat lau tren CPU dang ban, ma muc dich cua luot chay thu chi la chung minh
#: duong day chay duoc.
LEAK_SMOKE_CAP: int = 300

#: Nguong lech (diem phan tram) de goi mot nguon du lieu la lech bat can xung
#: giua cac split. Lay tu tieu chi doc bang o muc 5.3.4 cua Chuong 5.
SOURCE_SKEW_LIMIT_POINTS: float = 10.0

#: Uoc luong ngan sach do tre lap o Phase 0, mili-giay. Nguon:
#: docs/00-requirements/non-functional-requirements.md muc 1. Dua vao day de
#: bang T5.7b co cot doi chieu; day KHONG phai so do.
PHASE0_BUDGET_MS: dict[str, tuple[str, float]] = {
    "decode_ms": ("Giải mã ảnh + tiền xử lý", 50.0),
    "detect_ms": ("Suy luận YOLO11n @ 640px (CPU)", 150.0),
    "crop_ms": ("Cắt + tiền xử lý vùng biển số", 30.0),
    "ocr_ms": ("**PaddleOCR (mỗi biển)**", 120.0),
    "normalize_ms": ("Hậu xử lý regex + kiểm tra hợp lệ", 5.0),
    # Buoc nay CO trong ban ngan sach Phase 0 nhung KHONG co doi ung trong so do
    # cua benchmark_system (module do do pipeline suy luan thuan, khong di qua
    # tang API). Giu dong lai de tong uoc luong van la 405 ms dung nhu Chuong 5,
    # va o "do that" cua no se hien "—" chu khong bi lang le bo khoi bang.
    "db_ms": ("Ghi CSDL + lưu ảnh", 50.0),
}

#: Nguong chi tieu cua tung ma NFR: (nguong toi thieu, muc tieu, chieu tot).
#: ``chieu`` = "cao" nghia la gia tri cang cao cang tot.
NFR_TARGETS: dict[str, tuple[float, float, str, str]] = {
    "NFR-A1": (0.85, 0.90, "cao", "mAP@0.5 của bộ phát hiện"),
    "NFR-A2": (0.55, 0.65, "cao", "mAP@0.5:0.95 của bộ phát hiện"),
    "NFR-A3p": (0.88, 0.92, "cao", "Precision phát hiện"),
    "NFR-A3r": (0.85, 0.90, "cao", "Recall phát hiện"),
    "NFR-A4": (0.92, 0.95, "cao", "Độ chính xác OCR mức ký tự (1 − CER)"),
    "NFR-A5": (0.80, 0.85, "cao", "Chuỗi đầy đủ trước hậu xử lý"),
    "NFR-A6": (0.85, 0.90, "cao", "Chuỗi đầy đủ sau hậu xử lý"),
    "NFR-A7": (0.82, 0.88, "cao", "Độ chính xác E2E toàn trình"),
    "NFR-P1": (1500.0, 800.0, "thap", "Độ trễ E2E một ảnh, p95 (ms)"),
    "NFR-P4": (30.0, 15.0, "thap", "Thời gian nạp mô hình (s)"),
    "NFR-P5": (100.0, 50.0, "thap", "Overhead API, p95 (ms)"),
    "NFR-P6": (1000.0, 500.0, "thap", "Truy vấn 10.000 bản ghi, p95 (ms)"),
    "NFR-P7a": (4.0, 2.0, "thap", "RSS pipeline (GB)"),
    "NFR-P7b": (4.0, 2.0, "thap", "RSS máy chủ backend (GB)"),
    "NFR-R4": (0.99, 0.99, "cao", "Tỉ lệ thành công soak 300 s"),
    "NFR-SC1": (5, 5, "cao", "Số yêu cầu đồng thời xử lý ổn định"),
}


# --------------------------------------------------------------------------- #
# Ket qua
# --------------------------------------------------------------------------- #
class ResultStore:
    """Bo tich luy ket qua theo ma bang.

    Moi ma bang (``T5.5a``, ``T5.7b``, ...) la mot khoa cap mot cua JSON dau ra.
    Lop nay ton tai de mot phep do that bai khong bao gio co the ghi im lang mot
    gia tri rong vao bang: duong ghi duy nhat khi that bai la :meth:`skip`, va
    duong do bat buoc phai kem ly do.
    """

    def __init__(self) -> None:
        """Khoi tao kho rong."""
        self.data: dict[str, Any] = {}

    def put(self, code: str, payload: dict[str, Any]) -> None:
        """Ghi ket qua do duoc cho mot ma bang.

        Args:
            code: Ma bang, vi du ``"T5.5a"``.
            payload: Cac khoa so lieu cua bang.
        """
        self.data[code] = payload
        LOGGER.info("[%s] da ghi %d truong so lieu", code, len(payload))

    def skip(self, code: str, reason: str) -> None:
        """Danh dau mot ma bang la chua do duoc, kem ly do.

        Args:
            code: Ma bang.
            reason: Ly do cu the, du de nguoi doc biet phai lam gi de do duoc.
        """
        self.data[code] = {"trang_thai": NOT_MEASURED, "ly_do": reason}
        LOGGER.warning("[%s] CHUA DO — %s", code, reason)

    def get(self, code: str) -> dict[str, Any]:
        """Lay payload cua mot ma bang.

        Args:
            code: Ma bang.

        Returns:
            Payload, hoac mot payload ``chua do`` neu ma bang chua ton tai.
        """
        return self.data.get(code, {"trang_thai": NOT_MEASURED, "ly_do": "chua chay"})

    def measured(self, code: str) -> bool:
        """Cho biet mot ma bang co so that hay khong.

        Args:
            code: Ma bang.

        Returns:
            ``True`` neu ma bang co so liet, ``False`` neu chua do duoc.
        """
        return self.get(code).get("trang_thai") != NOT_MEASURED

    def value(self, code: str, key: str) -> Any:
        """Lay mot truong so lieu, tra ``None`` khi khong co.

        Args:
            code: Ma bang.
            key: Ten truong.

        Returns:
            Gia tri, hoac ``None``.
        """
        payload = self.get(code)
        if payload.get("trang_thai") == NOT_MEASURED:
            return None
        return payload.get(key)


# --------------------------------------------------------------------------- #
# Tien ich dinh dang
# --------------------------------------------------------------------------- #
def vn(value: Any, digits: int = 4) -> str:
    """Dinh dang mot so theo quy uoc tieng Viet (dau phay thap phan).

    Args:
        value: Gia tri can dinh dang. ``None`` cho ra ``—``.
        digits: So chu so thap phan.

    Returns:
        Chuoi da dinh dang, hoac ``—`` khi khong co gia tri.
    """
    if value is None or value == "" or isinstance(value, str):
        return EM_DASH if value is None or value == "" else str(value)
    if isinstance(value, bool):
        return "có" if value else "không"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return EM_DASH
    text = f"{number:,.{digits}f}"
    # en-US -> vi-VN: dau phan cach nghin va dau thap phan doi cho nhau.
    return text.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def vni(value: Any) -> str:
    """Dinh dang mot so nguyen theo quy uoc tieng Viet.

    Args:
        value: Gia tri nguyen. ``None`` cho ra ``—``.

    Returns:
        Chuoi da dinh dang.
    """
    if value is None:
        return EM_DASH
    try:
        return f"{int(value):,}".replace(",", ".")
    except (TypeError, ValueError):
        return EM_DASH


def verdict(code: str, measured: Any) -> str:
    """Doi chieu mot so do voi nguong NFR va tra ky hieu ket qua.

    Args:
        code: Ma NFR trong :data:`NFR_TARGETS`.
        measured: Gia tri do duoc, hoac ``None``.

    Returns:
        ``"✅ đạt"`` / ``"🟡 đạt ngưỡng tối thiểu"`` / ``"❌ không đạt"`` /
        ``"⬜ chưa đo"``.
    """
    if measured is None or code not in NFR_TARGETS:
        return "⬜ chưa đo"
    floor, target, direction, _ = NFR_TARGETS[code]
    try:
        number = float(measured)
    except (TypeError, ValueError):
        return "⬜ chưa đo"
    if direction == "cao":
        if number >= target:
            return "✅ đạt"
        if number >= floor:
            return "🟡 đạt ngưỡng tối thiểu"
        return "❌ không đạt"
    if number <= target:
        return "✅ đạt"
    if number <= floor:
        return "🟡 đạt ngưỡng tối thiểu"
    return "❌ không đạt"


def reports_dir(args: argparse.Namespace) -> Path:
    """Thu muc nhan cac tep trung gian cua luot chay hien tai.

    Mot luot ``--skip-slow`` do tren rat it mau nen ket qua cua no **khong duoc
    phep** ghi de len bao cao va hinh ve dung de cong bo. Ham nay tach hai che do
    ra hai thu muc khac nhau.

    Args:
        args: Doi so dong lenh.

    Returns:
        Duong dan thu muc, da duoc tao neu chua ton tai.
    """
    destination = SMOKE_DIR if args.skip_slow else PROJECT_ROOT / "docs" / "reports"
    destination.mkdir(parents=True, exist_ok=True)
    return destination


def read_json(path: Path) -> dict[str, Any]:
    """Doc mot tep JSON UTF-8.

    Args:
        path: Duong dan tep.

    Returns:
        Noi dung da giai ma.

    Raises:
        FileNotFoundError: Neu tep khong ton tai.
        ValueError: Neu tep khong phai JSON hop le.
    """
    if not path.exists():
        raise FileNotFoundError(f"khong tim thay tep ket qua {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"{path} khong phai JSON hop le: {error}") from error


# --------------------------------------------------------------------------- #
# _meta — cau hinh do
# --------------------------------------------------------------------------- #
def collect_meta(args: argparse.Namespace, weights: Path, num_test_images: int | None) -> dict[str, Any]:
    """Thu thap toan bo ngu canh do de gan vao ket qua.

    Nguyen tac 1 cua Chuong 5 doi hoi moi con so hieu nang phai cong bo kem cau
    hinh phan cung. Khoi nay la cho duy nhat luu ngu canh do, va no duoc ghi vao
    ca JSON lan Markdown de mot bang bi copy roi khoi ngu canh van truy nguoc
    duoc.

    Args:
        args: Doi so dong lenh da phan tich.
        weights: Duong dan trong so thuc su dung.
        num_test_images: So anh cua split duoc danh gia, ``None`` neu chua biet.

    Returns:
        Khoi ``_meta``.
    """
    meta: dict[str, Any] = {
        "thoi_diem_do": datetime.now().isoformat(timespec="seconds"),
        "he_dieu_hanh": f"{platform.system()} {platform.release()} ({platform.version()})",
        "cpu_ten": platform.processor() or "khong xac dinh",
        "so_nhan_logic": None,
        "so_nhan_vat_ly": None,
        "ram_tong_gb": None,
        "python": platform.python_version(),
        "venv": sys.prefix,
        "torch": None,
        "ultralytics": None,
        "paddleocr": None,
        "device": "cpu",
        "duong_dan_model": str(weights),
        "model_ton_tai": weights.exists(),
        "dataset_yaml": str(Path(args.data)),
        "split": args.split,
        "so_anh_split": num_test_images,
        "skip_slow": bool(args.skip_slow),
        "ghi_chu": (
            "Moi so lieu hieu nang trong tep nay chi co nghia khi doc kem khoi "
            "_meta nay. Kich thuoc lo = 1, bo 3 luot khoi dong nong dau tien."
        ),
    }

    try:
        from ai.evaluation.benchmark_system import describe_hardware

        info = describe_hardware(sample_seconds=1.0)
        meta.update(
            {
                "cpu_ten": info.cpu_name,
                "so_nhan_vat_ly": info.physical_cores,
                "so_nhan_logic": info.logical_cores,
                "ram_tong_gb": info.ram_total_gb,
                "he_dieu_hanh": info.platform,
                "python": info.python_version,
                "torch": info.torch_version,
                "torch_threads": info.torch_threads,
                "tien_trinh_canh_tranh": info.competing_processes,
            }
        )
    except Exception as error:  # noqa: BLE001 - moi truong, khong duoc lam sap
        LOGGER.warning("Khong lay duoc thong tin phan cung chi tiet: %s", error)
        import os

        meta["so_nhan_logic"] = os.cpu_count()

    for name in ("torch", "ultralytics", "paddleocr", "onnxruntime", "openvino", "numpy"):
        meta.setdefault("phien_ban_thu_vien", {})
        try:
            from importlib.metadata import version

            meta["phien_ban_thu_vien"][name] = version(name)
        except Exception:  # noqa: BLE001
            meta["phien_ban_thu_vien"][name] = NOT_MEASURED
    if meta.get("torch") is None:
        meta["torch"] = meta["phien_ban_thu_vien"].get("torch")
    meta["ultralytics"] = meta["phien_ban_thu_vien"].get("ultralytics")
    meta["paddleocr"] = meta["phien_ban_thu_vien"].get("paddleocr")
    return meta


# --------------------------------------------------------------------------- #
# Phep do 1 — detection tong the va tach theo layout (T5.5a, T5.5b)
# --------------------------------------------------------------------------- #
def measure_detection(args: argparse.Namespace, weights: Path, store: ResultStore) -> None:
    """Danh gia bo phat hien tren tap test, tong the va tach theo layout.

    Goi lai ``ai.evaluation.evaluate`` nguyen ven — script nay khong tu tinh mAP
    de tranh co hai cai dat metric khac nhau trong cung mot quyen do an.

    Args:
        args: Doi so dong lenh.
        weights: Trong so can danh gia.
        store: Kho ket qua.
    """
    LOGGER.info("=== [1/7] Danh gia detection tren tap %s ===", args.split)
    try:
        from ai.evaluation import evaluate as eval_mod
    except ImportError as error:
        store.skip("T5.5a", f"khong import duoc ai.evaluation.evaluate: {error}")
        store.skip("T5.5b", f"khong import duoc ai.evaluation.evaluate: {error}")
        return

    name = f"ch5-{weights.stem}-{args.split}"
    out_dir = reports_dir(args)
    report_path = out_dir / f"03-evaluation-{name}.json"
    argv = [
        "--weights", str(weights),
        "--data", str(args.data),
        "--split", args.split,
        "--imgsz", str(args.imgsz),
        "--device", "cpu",
        "--ar-threshold", "2.5",
        "--name", name,
        "--output-dir", str(out_dir),
    ]
    if args.skip_slow:
        argv += ["--max-images", "200", "--speed-samples", "50", "--skip-ultralytics-val"]

    try:
        code = eval_mod.main(argv)
    except Exception as error:  # noqa: BLE001
        store.skip("T5.5a", f"ai.evaluation.evaluate nem ngoai le: {error!r}")
        store.skip("T5.5b", f"ai.evaluation.evaluate nem ngoai le: {error!r}")
        return
    if code != 0:
        store.skip("T5.5a", f"ai.evaluation.evaluate tra ma loi {code}")
        store.skip("T5.5b", f"ai.evaluation.evaluate tra ma loi {code}")
        return

    try:
        report = read_json(report_path)
    except (FileNotFoundError, ValueError) as error:
        store.skip("T5.5a", str(error))
        store.skip("T5.5b", str(error))
        return

    # Ultralytics la nguon so co tham quyen hon cho mAP; bo doi sanh noi bo cua
    # evaluate.py dung de tach nhom. Neu bo qua buoc Ultralytics thi lay so noi bo
    # va ghi ro nguon trong truong `nguon_chi_so`.
    reference = report.get("metrics_reference_ultralytics") or {}
    overall = report.get("metrics_overall") or {}
    source = "ultralytics_val" if reference else "bo_doi_sanh_noi_bo_evaluate.py"
    metrics = reference or overall

    dataset = report.get("dataset", {})
    store.put(
        "T5.5a",
        {
            "map50": metrics.get("mAP@0.5"),
            "map5095": metrics.get("mAP@0.5:0.95"),
            "precision": metrics.get("precision"),
            "recall": metrics.get("recall"),
            "f1": metrics.get("f1"),
            "conf_toi_uu_theo_f1": args.conf,
            "conf_ghi_chu": (
                "evaluate.py bao cao chi so tai nguong conf co dinh; duong cong F1 "
                "theo nguong nam trong hinh 05-detection-f1-curve.png. Nguong toi uu "
                "phai doc tu hinh do, khong suy tu bang nay."
            ),
            "so_anh_tap_test": dataset.get("num_images"),
            "so_doi_tuong_nhan_that": dataset.get("num_ground_truth_boxes"),
            "nguon_chi_so": source,
            "chi_so_bo_doi_sanh_noi_bo": {
                "map50": overall.get("mAP@0.5"),
                "map5095": overall.get("mAP@0.5:0.95"),
                "precision": overall.get("precision"),
                "recall": overall.get("recall"),
                "f1": overall.get("f1"),
            },
            "tep_nguon": str(report_path),
            "hinh": report.get("plots", {}),
        },
    )

    by_layout = report.get("metrics_by_line_count") or {}
    single = by_layout.get("single_line") or {}
    two = by_layout.get("two_line") or {}
    if not single or not two:
        store.skip("T5.5b", "bao cao khong co metrics_by_line_count cho ca hai layout")
        return

    label_stats = dataset.get("label_stats", {})
    grouped_by_ar = label_stats.get("grouped_by_aspect_ratio", 0)
    total_boxes = dataset.get("num_ground_truth_boxes") or 0
    heuristic_share = (grouped_by_ar / total_boxes) if total_boxes else None

    def gap(key: str) -> float | None:
        """Chenh lech mot dong tru hai dong, tinh bang diem phan tram."""
        a, b = single.get(key), two.get(key)
        if a is None or b is None:
            return None
        return round((a - b) * 100, 2)

    store.put(
        "T5.5b",
        {
            "mot_dong": {
                "so_doi_tuong": single.get("num_ground_truth"),
                "map50": single.get("mAP@0.5"),
                "map5095": single.get("mAP@0.5:0.95"),
                "precision": single.get("precision"),
                "recall": single.get("recall"),
                "f1": single.get("f1"),
            },
            "hai_dong": {
                "so_doi_tuong": two.get("num_ground_truth"),
                "map50": two.get("mAP@0.5"),
                "map5095": two.get("mAP@0.5:0.95"),
                "precision": two.get("precision"),
                "recall": two.get("recall"),
                "f1": two.get("f1"),
            },
            "chenh_lech_diem_pt": {
                "map50": gap("mAP@0.5"),
                "map5095": gap("mAP@0.5:0.95"),
                "precision": gap("precision"),
                "recall": gap("recall"),
                "f1": gap("f1"),
            },
            "nguong_ty_le_khung_hinh": report.get("settings", {}).get("aspect_ratio_threshold"),
            "ty_le_o_suy_bang_heuristic": (
                None if heuristic_share is None else round(heuristic_share, 4)
            ),
            "canh_bao_heuristic": (
                "Layout duoc suy tu ty le khung hinh 2,5 cho phan lon hop giới han vi "
                "bo du lieu khong khai bao lop layout. Day la UOC LUONG, khong phai "
                "nhan that — moi ket luan ve NFR-A8 phai neu ro dieu nay."
                if (heuristic_share or 0) > 0.5
                else "Phan lon o duoc gan layout tu nhan lop tuong minh."
            ),
            "moc_baseline_416_v1": {
                "map50_mot_dong": 0.9856,
                "map50_hai_dong": 0.9592,
                "chenh_diem_pt": 2.6,
                "ghi_chu": "So cua baseline-416-v1.pt (split v1, imgsz 416) — KHONG duoc "
                "chuyen thanh so cua best.pt.",
            },
        },
    )


# --------------------------------------------------------------------------- #
# Phep do 2 — detection tach theo dai kich thuoc box (T5.5c)
# --------------------------------------------------------------------------- #
def measure_size_bands(args: argparse.Namespace, weights: Path, store: ResultStore) -> None:
    """Tinh mAP tach theo dai dien tich hop gioi han.

    ``ai/evaluation/evaluate.py`` chi phan ra theo layout, chua phan ra theo kich
    thuoc box. Ham nay bo sung phan do do bang cach **tai su dung nguyen cac ham
    nguyen thuy** cua module do (``read_ground_truth``, ``run_predictions``,
    ``evaluate_group``), nen cong thuc mAP van la mot cai dat duy nhat.

    Args:
        args: Doi so dong lenh.
        weights: Trong so can danh gia.
        store: Kho ket qua.
    """
    LOGGER.info("=== [2/7] Detection tach theo dai kich thuoc hop gioi han ===")
    try:
        from PIL import Image

        from ai.evaluation import evaluate as ev
        from ultralytics import YOLO
    except ImportError as error:
        store.skip("T5.5c", f"thieu thu vien: {error}")
        return

    try:
        descriptor = ev.load_dataset_descriptor(Path(args.data))
        images = ev.resolve_split_images(Path(args.data), descriptor, args.split)
    except Exception as error:  # noqa: BLE001
        store.skip("T5.5c", f"khong doc duoc split {args.split}: {error}")
        return

    if args.skip_slow:
        images = images[:200]

    raw_names = descriptor.get("names", {})
    class_names = (
        {int(k): str(v) for k, v in raw_names.items()}
        if isinstance(raw_names, dict)
        else {i: str(n) for i, n in enumerate(raw_names)}
    )

    try:
        ground_truth, _ = ev.read_ground_truth(images, class_names, 2.5)
        model = YOLO(str(weights))
        predictions, _ = ev.run_predictions(
            model, images, args.imgsz, args.conf, 0.45, "cpu", 2.5
        )
    except Exception as error:  # noqa: BLE001
        store.skip("T5.5c", f"khong chay duoc suy luan: {error!r}")
        return

    # Dien tich anh, cache theo duong dan de khong mo lai cung mot tep.
    dims: dict[Path, tuple[int, int]] = {}

    def area_fraction(box: Any) -> float | None:
        """Ty le dien tich box tren dien tich anh."""
        if box.image not in dims:
            try:
                with Image.open(box.image) as handle:
                    dims[box.image] = handle.size
            except Exception:  # noqa: BLE001
                dims[box.image] = (0, 0)
        width, height = dims[box.image]
        if not width or not height:
            return None
        x1, y1, x2, y2 = box.xyxy
        return abs((x2 - x1) * (y2 - y1)) / float(width * height)

    def band_of(fraction: float | None) -> str | None:
        """Ten dai kich thuoc chua mot ty le dien tich."""
        if fraction is None:
            return None
        for band, low, high in SIZE_BANDS:
            if low <= fraction < high:
                return band
        return None

    gt_bands: dict[str, list[Any]] = {band: [] for band, _, _ in SIZE_BANDS}
    unassigned = 0
    for box in ground_truth:
        band = band_of(area_fraction(box))
        if band is None:
            unassigned += 1
            continue
        gt_bands[band].append(box)

    # Moi du doan duoc gan vao dai cua hop nhan that ma no trung nhieu nhat; du
    # doan khong trung gi thi gan theo chinh kich thuoc cua no (day la thong tin
    # duy nhat co cho mot duong tinh gia).
    gt_by_image: dict[Path, list[Any]] = {}
    for box in ground_truth:
        gt_by_image.setdefault(box.image, []).append(box)

    pred_bands: dict[str, list[Any]] = {band: [] for band, _, _ in SIZE_BANDS}
    for prediction in predictions:
        best_iou, best_box = 0.0, None
        for gt in gt_by_image.get(prediction.image, ()):
            score = ev.iou(prediction.xyxy, gt.xyxy)
            if score > best_iou:
                best_iou, best_box = score, gt
        target = best_box if (best_iou >= 0.5 and best_box is not None) else prediction
        band = band_of(area_fraction(target))
        if band is not None:
            pred_bands[band].append(prediction)

    total_gt = len(ground_truth)
    bands_payload: dict[str, Any] = {}
    for band, _, _ in SIZE_BANDS:
        subset = gt_bands[band]
        if not subset:
            bands_payload[band] = {
                "so_doi_tuong": 0,
                "ty_le_trong_tap": 0.0,
                "map50": None,
                "map5095": None,
                "recall": None,
                "canh_bao": "khong co doi tuong nao trong dai nay",
            }
            continue
        metrics = ev.evaluate_group(band, subset, pred_bands[band])
        bands_payload[band] = {
            "so_doi_tuong": metrics.num_ground_truth,
            "ty_le_trong_tap": round(len(subset) / total_gt, 4) if total_gt else None,
            "map50": round(metrics.ap50, 5),
            "map5095": round(metrics.ap50_95, 5),
            "recall": round(metrics.recall, 5),
            "precision": round(metrics.precision, 5),
            "canh_bao": (
                "duoi 30 doi tuong — con so nay KHONG co y nghia thong ke, khong duoc "
                "dua vao so sanh"
                if metrics.num_ground_truth < 30
                else None
            ),
        }

    overall_metrics = ev.evaluate_group("ALL", ground_truth, predictions)
    store.put(
        "T5.5c",
        {
            "dai": bands_payload,
            "toan_tap": {
                "so_doi_tuong": overall_metrics.num_ground_truth,
                "map50": round(overall_metrics.ap50, 5),
                "map5095": round(overall_metrics.ap50_95, 5),
                "recall": round(overall_metrics.recall, 5),
            },
            "so_anh": len(images),
            "so_box_khong_gan_duoc_dai": unassigned,
            "ghi_chu": (
                "Dai duoc tinh tu (w x h) cua hop nhan that chia cho dien tich anh goc. "
                "Chi so cua moi dai tinh bang chinh ham evaluate_group cua "
                "ai/evaluation/evaluate.py nen cong thuc mAP la duy nhat trong do an."
            ),
        },
    )


# --------------------------------------------------------------------------- #
# Phep do 3 — do tre E2E va phan ra ngan sach (T5.7a, T5.7b)
# --------------------------------------------------------------------------- #
def measure_latency(args: argparse.Namespace, weights: Path, store: ResultStore) -> None:
    """Do do tre dau-cuoi va phan ra ngan sach theo tung buoc.

    Args:
        args: Doi so dong lenh.
        weights: Trong so can danh gia.
        store: Kho ket qua.
    """
    LOGGER.info("=== [3/7] Do tre E2E va phan ra ngan sach ===")
    try:
        from ai.evaluation import benchmark_system as bench
    except ImportError as error:
        store.skip("T5.7a", f"khong import duoc benchmark_system: {error}")
        store.skip("T5.7b", f"khong import duoc benchmark_system: {error}")
        return

    images_root = Path(args.data).parent / "images" / args.split
    if not images_root.exists():
        store.skip("T5.7a", f"khong tim thay thu muc anh {images_root}")
        store.skip("T5.7b", f"khong tim thay thu muc anh {images_root}")
        return

    limit = 20 if args.skip_slow else 100
    out_dir = reports_dir(args)
    output = out_dir / f"05-benchmark-system-{weights.stem}.json"
    argv = [
        "--weights", str(weights),
        "--images", str(images_root),
        "--imgsz", str(args.imgsz),
        "--limit", str(limit),
        "--device", "cpu",
        "--output", str(output),
        "--figures-dir", str(out_dir / "figures"),
    ]
    if args.skip_slow:
        argv.append("--skip-onnx")

    try:
        code = bench.main(argv)
        report = read_json(output)
    except Exception as error:  # noqa: BLE001
        store.skip("T5.7a", f"benchmark_system that bai: {error!r}")
        store.skip("T5.7b", f"benchmark_system that bai: {error!r}")
        return
    if code != 0:
        LOGGER.warning("benchmark_system tra ma %d, van doc bao cao neu co", code)

    e2e = report.get("nfr_p1_e2e_latency") or {}
    if not e2e:
        store.skip("T5.7a", "bao cao khong co khoa nfr_p1_e2e_latency")
    else:
        p95 = e2e.get("p95_ms")
        store.put(
            "T5.7a",
            {
                "p50_ms": e2e.get("p50_ms"),
                "p95_ms": p95,
                "p99_ms": e2e.get("p99_ms"),
                "mean_ms": e2e.get("mean_ms"),
                "std_ms": e2e.get("std_ms"),
                "min_ms": e2e.get("min_ms"),
                "max_ms": e2e.get("max_ms"),
                "so_anh_do": e2e.get("samples"),
                "so_bien_trung_binh_moi_anh": report.get("mean_plates_per_image"),
                "boi_so_vuot_nguong_toi_thieu": (
                    None if p95 is None else round(p95 / 1500.0, 2)
                ),
                "boi_so_vuot_muc_tieu": (None if p95 is None else round(p95 / 800.0, 2)),
                "ket_qua_nfr_p1": verdict("NFR-P1", p95),
                # 763,75 ms = client-side warm p95 cua baseline-416-v1 do lai tren
                # may ranh (07-benchmark-p1-resolved.json). Con so cu 5857,19 ms
                # DA BI BAC BO (nhiem tai canh tranh + sai checkpoint + loi crop)
                # — khong duoc dung lai lam moc baseline.
                "moc_baseline_416_v1_p95_ms": 763.75,
                "tep_nguon": str(output),
            },
        )

    budget = report.get("latency_budget") or {}
    median = budget.get("median_ms") or {}
    share = budget.get("share_percent") or {}
    if not median:
        store.skip("T5.7b", "bao cao khong co khoa latency_budget.median_ms")
    else:
        rows: dict[str, Any] = {}
        for key, (label, estimate) in PHASE0_BUDGET_MS.items():
            measured = median.get(key)
            rows[key] = {
                "ten_buoc": label,
                "uoc_luong_phase0_ms": estimate,
                "do_that_ms": measured,
                "chenh_lech_lan": (
                    None if measured is None or not estimate else round(measured / estimate, 2)
                ),
                "phan_tram_tong": share.get(key),
            }
        total_estimate = sum(v[1] for v in PHASE0_BUDGET_MS.values())
        total_measured = budget.get("median_total_ms")
        # Ty so chenh lech phai so cung pham vi: so do khong bao gom buoc ghi CSDL,
        # nen mau so cua ty so cung phai bo buoc do ra. So 405 ms van duoc cong bo
        # nguyen ven o cot uoc luong de doi chieu voi ban ngan sach Phase 0.
        comparable_estimate = sum(
            estimate
            for key, (_, estimate) in PHASE0_BUDGET_MS.items()
            if median.get(key) is not None
        )
        store.put(
            "T5.7b",
            {
                "buoc": rows,
                "tong": {
                    "uoc_luong_phase0_ms": total_estimate,
                    "uoc_luong_cung_pham_vi_ms": comparable_estimate,
                    "do_that_ms": total_measured,
                    "chenh_lech_lan": (
                        None
                        if total_measured is None or not comparable_estimate
                        else round(total_measured / comparable_estimate, 2)
                    ),
                    "phan_tram_tong": 100.0,
                },
                "so_mau": budget.get("samples"),
                "so_bien_trung_binh_moi_anh": budget.get("mean_plates_per_image"),
                "ghi_chu": (
                    "Buoc 'ghi CSDL + luu anh' khong co doi ung trong so do vi "
                    "benchmark_system do pipeline suy luan thuan, khong di qua tang "
                    "API — o 'do that' cua no giu '—'. Cot ty so 'chenh lech (lan)' o "
                    "dong tong vi vay so voi uoc luong CUNG PHAM VI (da tru buoc ghi "
                    "CSDL), khong so voi con so 405 ms tron."
                ),
            },
        )


# --------------------------------------------------------------------------- #
# Phep do 4 — so sanh backend suy luan (T5.7c)
# --------------------------------------------------------------------------- #
def find_exports(weights: Path) -> dict[str, Path]:
    """Tim cac ban xuat ONNX / OpenVINO tuong ung voi mot trong so.

    Args:
        weights: Duong dan tep ``.pt``.

    Returns:
        Anh xa ten backend -> duong dan ban xuat tim duoc.
    """
    found: dict[str, Path] = {}
    onnx_beside = weights.with_suffix(".onnx")
    if onnx_beside.exists():
        found["onnx"] = onnx_beside
    ov_beside = weights.parent / f"{weights.stem}_openvino_model"
    if ov_beside.is_dir():
        found["openvino"] = ov_beside

    exported = PROJECT_ROOT / "models" / "checkpoints" / "exported"
    if exported.is_dir():
        for child in sorted(exported.iterdir()):
            if not child.is_dir():
                continue
            for candidate in child.rglob(f"{weights.stem}*.onnx"):
                found.setdefault("onnx", candidate)
            for candidate in child.glob(f"{weights.stem}*_openvino_model"):
                if candidate.is_dir():
                    found.setdefault("openvino", candidate)
    return found


def measure_backends(args: argparse.Namespace, weights: Path, store: ResultStore) -> None:
    """So sanh do tre bo phat hien giua PyTorch, ONNX Runtime va OpenVINO.

    Args:
        args: Doi so dong lenh.
        weights: Trong so ``.pt`` goc.
        store: Kho ket qua.
    """
    LOGGER.info("=== [4/7] So sanh backend suy luan ===")
    exports = find_exports(weights)
    if not exports:
        store.skip(
            "T5.7c",
            f"khong tim thay ban xuat ONNX/OpenVINO cho {weights.name} (da tim canh "
            f"trong so va trong models/checkpoints/exported/). Xuat truoc bang: "
            f"yolo export model={weights} format=onnx imgsz={args.imgsz}",
        )
        return

    try:
        from ai.evaluation import benchmark_cpu as bench
    except ImportError as error:
        store.skip("T5.7c", f"khong import duoc benchmark_cpu: {error}")
        return

    images_root = Path(args.data).parent / "images" / args.split
    backends = ["pytorch", *sorted(exports)]
    argv = [
        "--weights", str(weights),
        "--images", str(images_root),
        "--backends", *backends,
        "--imgsz", str(args.imgsz),
        "--runs", "10" if args.skip_slow else "50",
        "--warmup", "3" if args.skip_slow else "5",
        "--output-dir", str(reports_dir(args)),
    ]
    try:
        bench.main(argv)
        report = read_json(reports_dir(args) / "03-cpu-benchmark.json")
    except Exception as error:  # noqa: BLE001
        store.skip("T5.7c", f"benchmark_cpu that bai: {error!r}")
        return

    results = report.get("results") or []
    if not results:
        store.skip("T5.7c", "benchmark_cpu khong tra ket qua nao")
        return

    rows: dict[str, Any] = {}
    baseline_p50 = None
    for entry in results:
        backend = entry.get("backend") or entry.get("name") or "?"
        latency = entry.get("latency") or entry
        p50 = latency.get("p50_ms") or latency.get("p50")
        if backend == "pytorch":
            baseline_p50 = p50
        rows[backend] = {
            "p50_ms": p50,
            "p95_ms": latency.get("p95_ms") or latency.get("p95"),
            "tang_toc_so_voi_pytorch": None,
            "map50_sau_khi_xuat": NOT_MEASURED,
            "map50_ly_do": (
                "benchmark_cpu chi do do tre, khong tinh lai mAP cho ban xuat. Muon co "
                "cot nay phai chay: python -m ai.evaluation.evaluate --weights <ban xuat>"
            ),
        }
    for backend, row in rows.items():
        if baseline_p50 and row["p50_ms"]:
            row["tang_toc_so_voi_pytorch"] = round(baseline_p50 / row["p50_ms"], 2)

    # Chan tren cua cai thien E2E theo dinh luat Amdahl: chi phan cua bo phat hien
    # duoc tang toc, nen cai thien tong bi chan boi ty trong cua no.
    detector_share = store.value("T5.7b", "buoc")
    share_pct = None
    if isinstance(detector_share, dict):
        share_pct = (detector_share.get("detect_ms") or {}).get("phan_tram_tong")

    store.put(
        "T5.7c",
        {
            "backend": rows,
            "ty_trong_bo_phat_hien_phan_tram": share_pct,
            "chan_tren_cai_thien_e2e_phan_tram": share_pct,
            "ghi_chu_amdahl": (
                "Cai thien E2E bi chan tren boi chinh ty trong cua bo phat hien trong "
                "tong thoi gian. Ket luan nay khong phu thuoc gia tri cu the cua cot "
                "tang toc."
            ),
            "ban_xuat_da_dung": {k: str(v) for k, v in exports.items()},
            "so_lan_chay_moi_backend": report.get("settings", {}).get("runs"),
            "so_anh": report.get("settings", {}).get("num_images"),
        },
    )


# --------------------------------------------------------------------------- #
# Phep do 5 — OCR (T5.6a...T5.6e) va ma tran nham lan (T5.6d)
# --------------------------------------------------------------------------- #
def find_label_file() -> Path | None:
    """Tim tep nhan chuoi bien so.

    Returns:
        Duong dan tep dau tien tim thay, hoac ``None``.
    """
    for candidate in LABEL_CANDIDATES:
        if candidate.exists():
            return candidate
    annotations = PROJECT_ROOT / "datasets" / "annotations"
    if annotations.is_dir():
        for candidate in sorted(annotations.glob("*.csv")):
            try:
                with candidate.open(encoding="utf-8-sig", newline="") as handle:
                    header = next(csv.reader(handle), [])
            except OSError:
                continue
            if "plate_text" in [c.strip().lower() for c in header]:
                return candidate
    return None


def compute_edit_operations(confusion: dict[str, Any]) -> dict[str, Any]:
    """Dan ra bo ba S / D / I va mau so N tu ma tran nham lan da do.

    Ba loai loi nay goi ra ba nguyen nhan khac nhau (nham ky tu, bo sot ky tu,
    nhieu bi doc thanh ky tu) nen bang T5.6a doi hoi tach bach chung. Cac gia tri
    o day **khong phai uoc luong**: chung la tong truc tiep cua chinh ma tran
    can chinh ma ``ocr_accuracy`` da dem.

    Args:
        confusion: Khoi ``confusion_matrix`` cua bao cao OCR.

    Returns:
        Mapping voi cac khoa ``S``, ``D``, ``I``, ``N``, ``nguon``; rong neu ma
        tran khong co trong bao cao.
    """
    matrix = confusion.get("matrix")
    if not matrix:
        return {}
    substitutions = 0
    aligned = 0
    for row_index, row in enumerate(matrix):
        for col_index, value in enumerate(row):
            aligned += value
            if row_index != col_index:
                substitutions += value
    deletions = sum((confusion.get("deletions") or {}).values())
    insertions = sum((confusion.get("insertions") or {}).values())
    return {
        "S": substitutions,
        "D": deletions,
        "I": insertions,
        "N": aligned + deletions,
        "nguon": (
            "dan ra tu confusion_matrix cua 05-ocr-accuracy.json: S = tong o ngoai "
            "duong cheo, D = tong deletions, I = tong insertions, N = tong ma tran "
            "cong D. Khong phai so uoc luong."
        ),
    }


def rule_table_coverage(review: dict[str, Any]) -> dict[tuple[str, str], str]:
    """Dung tra cuu 'cap ky tu -> bang luat nao phu no'.

    Args:
        review: Khoi ``plate_rules_review`` cua bao cao OCR.

    Returns:
        Anh xa ``(ky_tu_that, ky_tu_doc_thanh")`` -> ten bang luat.
    """
    coverage: dict[tuple[str, str], str] = {}
    for entry in (review.get("confirmed") or []) + (review.get("unobserved") or []):
        rule = str(entry.get("rule", ""))
        if "->" not in rule:
            continue
        source, target = (part.strip() for part in rule.split("->", 1))
        coverage[(source, target)] = str(entry.get("table", "?"))
    return coverage


def measure_ocr(args: argparse.Namespace, weights: Path, store: ResultStore) -> Path | None:
    """Do do chinh xac OCR: NFR-A4, A5, A6, A7 va ma tran nham lan 36x36.

    Args:
        args: Doi so dong lenh.
        weights: Trong so bo phat hien dung cho phep do E2E.
        store: Kho ket qua.

    Returns:
        Duong dan bao cao OCR neu do duoc, ``None`` neu khong.
    """
    LOGGER.info("=== [5/7] Do chinh xac OCR (NFR-A4/A5/A6/A7) ===")
    codes = ("T5.6a", "T5.6b", "T5.6c", "T5.6d", "T5.6e")

    labels = find_label_file()
    if labels is None:
        reason = (
            "khong tim thay tep nhan chuoi bien so trong datasets/annotations/ "
            "(da tim plate_labels.csv, plate_text_labels.csv va moi *.csv co cot "
            "plate_text). Cac chi tieu NFR-A4...A7 vi vay chua do duoc."
        )
        for code in codes:
            store.skip(code, reason)
        return None
    LOGGER.info("Dung tep nhan chuoi: %s", labels)

    try:
        from ai.evaluation import ocr_accuracy as ocr
    except ImportError as error:
        for code in codes:
            store.skip(code, f"khong import duoc ocr_accuracy: {error}")
        return None

    out_dir = reports_dir(args)
    output = out_dir / "05-ocr-accuracy.json"
    argv = [
        "--labels", str(labels),
        "--output", str(output),
        "--detector", str(weights),
        "--detector-imgsz", str(args.imgsz),
        "--figures", str(out_dir / "figures"),
        "--errors-dir", str(out_dir / "05-ocr-errors"),
    ]
    if args.skip_slow:
        argv += ["--limit", "60", "--e2e-limit", "30", "--no-ablation"]

    try:
        code = ocr.main(argv)
    except Exception as error:  # noqa: BLE001
        for name in codes:
            store.skip(name, f"ocr_accuracy nem ngoai le: {error!r}")
        return None
    if code != 0:
        for name in codes:
            store.skip(name, f"ocr_accuracy tra ma loi {code}")
        return None

    try:
        report = read_json(output)
    except (FileNotFoundError, ValueError) as error:
        for name in codes:
            store.skip(name, str(error))
        return None

    by_layout = report.get("by_line_count") or {}
    overall = by_layout.get("overall") or {}
    count = overall.get("count")

    # --- T5.6a: CER muc ky tu -------------------------------------------------
    # S / D / I duoc DAN RA tu ma tran nham lan da do, khong phai uoc luong:
    #   S = tong cac o ngoai duong cheo cua ma tran can chinh
    #   D = tong so lan mot ky tu nhan that khong duoc can chinh (deletions)
    #   I = tong so lan mot ky tu du doan khong co doi ung (insertions)
    #   N = tong so ky tu nhan that = (tong ma tran) + D
    edits = compute_edit_operations(report.get("confusion_matrix") or {})
    store.put(
        "T5.6a",
        {
            "char_accuracy_truoc": overall.get("char_accuracy_pre_norm"),
            "char_accuracy_sau": overall.get("char_accuracy_post_norm"),
            "cer_truoc": overall.get("cer_pre_norm"),
            "cer_sau": overall.get("cer_post_norm"),
            "N_so_ky_tu_nhan_that": edits.get("N", NOT_MEASURED),
            "S_thay_the": edits.get("S", NOT_MEASURED),
            "D_bi_xoa": edits.get("D", NOT_MEASURED),
            "I_chen_thua": edits.get("I", NOT_MEASURED),
            "S_D_I_nguon": edits.get("nguon"),
            "S_D_I_ly_do": (
                None
                if edits
                else "khong doc duoc confusion_matrix trong bao cao OCR, nen S/D/I "
                "khong dan ra duoc. Chay lai ocr_accuracy de co ma tran."
            ),
            "so_ca_theo_loai_loi": overall.get("error_classes"),
            "so_mau": count,
            "ket_qua_nfr_a4": verdict("NFR-A4", overall.get("char_accuracy_post_norm")),
            "tep_nguon": str(output),
        },
    )

    # --- T5.6b: chuoi truoc / sau hau xu ly ----------------------------------
    contribution = report.get("postprocessing_contribution") or {}
    a5 = contribution.get("nfr_a5_exact_before")
    a6 = contribution.get("nfr_a6_exact_after")
    wrong_both = None
    if isinstance(count, int) and count and a6 is not None:
        broke = contribution.get("plates_broken") or 0
        fixed = contribution.get("plates_fixed") or 0
        wrong_both = int(round((1 - a6) * count)) - broke
        wrong_both = max(wrong_both, 0)
    store.put(
        "T5.6b",
        {
            "a5_truoc_hau_xu_ly": a5,
            "a6_sau_hau_xu_ly": a6,
            "muc_cai_thien_diem_pt": contribution.get("gain_points"),
            "so_bien_duoc_sua_dung": contribution.get("plates_fixed"),
            "so_bien_bi_lam_hong": contribution.get("plates_broken"),
            "so_bien_sai_ca_truoc_lan_sau": wrong_both,
            "so_mau": count,
            "ket_qua_nfr_a5": verdict("NFR-A5", a5),
            "ket_qua_nfr_a6": verdict("NFR-A6", a6),
            "nhanh_dien_giai": (
                None
                if contribution.get("gain_points") is None
                else ("A" if contribution["gain_points"] > 0 else "B")
            ),
            "phan_ra_theo_nhom_luat": {
                "trang_thai": NOT_MEASURED,
                "ly_do": (
                    "Chua co co che bat/tat tung nhom luat trong ai/inference/"
                    "plate_rules.py. Muc D.2 cua ch5-thuc-nghiem.md ghi day la hang "
                    "muc can viet ma truoc khi dien duoc."
                ),
            },
        },
    )

    # --- T5.6c: tach theo layout ---------------------------------------------
    one = by_layout.get("one_line") or {}
    two = by_layout.get("two_line") or {}
    if not one.get("count") or not two.get("count"):
        store.skip(
            "T5.6c",
            "tap nhan chuoi khong du ca hai layout (one_line=%s, two_line=%s)"
            % (one.get("count"), two.get("count")),
        )
    else:
        def diff(key: str) -> float | None:
            """Chenh lech mot dong tru hai dong, diem phan tram."""
            a, b = one.get(key), two.get(key)
            return None if a is None or b is None else round((a - b) * 100, 2)

        store.put(
            "T5.6c",
            {
                "mot_dong": {
                    "so_mau": one.get("count"),
                    "char_accuracy": one.get("char_accuracy_post_norm"),
                    "a5": one.get("exact_pre_norm"),
                    "a6": one.get("exact_post_norm"),
                    "gain_points": one.get("postprocessing_gain_points"),
                    "a7": (one.get("e2e") or {}).get("exact"),
                },
                "hai_dong": {
                    "so_mau": two.get("count"),
                    "char_accuracy": two.get("char_accuracy_post_norm"),
                    "a5": two.get("exact_pre_norm"),
                    "a6": two.get("exact_post_norm"),
                    "gain_points": two.get("postprocessing_gain_points"),
                    "a7": (two.get("e2e") or {}).get("exact"),
                },
                "chenh_lech_diem_pt": {
                    "char_accuracy": diff("char_accuracy_post_norm"),
                    "a5": diff("exact_pre_norm"),
                    "a6": diff("exact_post_norm"),
                },
                "moc_tham_chieu": (
                    "Laroca va cong su (VISAPP 2022) bao cao 94,3% (bien mot dong) so "
                    "voi 45,7% (bien hai dong), chenh 48,6 diem, do tren bo du lieu "
                    "RodoSol-ALPR CUA BRAZIL. Day KHONG phai so lieu Viet Nam."
                ),
            },
        )

    # --- T5.6d: ma tran nham lan ky tu 36x36 ---------------------------------
    confusion = report.get("confusion_matrix") or {}
    top = confusion.get("top_confusions") or []
    if not top:
        store.skip("T5.6d", "bao cao khong co confusion_matrix.top_confusions")
    else:
        review = report.get("plate_rules_review") or {}
        coverage = rule_table_coverage(review)
        # Mau so dung cua cot "ti le trong tong so loi thay the" la TONG S cua ca
        # ma tran, khong phai tong cua rieng nhom dan dau — dung tong nhom dan dau
        # se lam moi ty le bi thoi phong.
        edits = compute_edit_operations(report.get("confusion_matrix") or {})
        total_subs = edits.get("S") or None

        rows = []
        for index, item in enumerate(top[:10]):
            truth = item.get("true") or item.get("truth")
            predicted = item.get("predicted") or item.get("pred")
            forward = coverage.get((truth, predicted))
            backward = coverage.get((predicted, truth))
            if forward:
                direction = f"đúng chiều — luật `{truth} → {predicted}` thuộc {forward}"
            elif backward:
                direction = (
                    f"**ngược chiều** — bảng luật chỉ có `{predicted} → {truth}` "
                    f"({backward}); cặp quan sát được đi chiều ngược lại"
                )
            else:
                direction = "chưa có luật nào phủ cặp này"
            rows.append(
                {
                    "hang": index + 1,
                    "ky_tu_that": truth,
                    "doc_thanh": predicted,
                    "so_lan": item.get("count"),
                    "ty_le_trong_tong_thay_the": (
                        None
                        if not total_subs
                        else round(item.get("count", 0) / total_subs, 4)
                    ),
                    "co_trong_bang_luat": bool(forward or backward),
                    "bang_luat": forward or backward,
                    "huong_anh_xa": direction,
                }
            )

        store.put(
            "T5.6d",
            {
                "top_cap_nham": rows,
                "tong_so_thay_the": total_subs,
                "doi_chieu_bang_luat": review,
                "kich_thuoc_ma_tran": (
                    f"{len(confusion.get('charset', ''))}x{len(confusion.get('charset', ''))}"
                    if confusion.get("charset")
                    else NOT_MEASURED
                ),
                "bo_ky_tu": confusion.get("charset"),
                "so_mau": count,
                "hinh": report.get("figures", {}),
            },
        )

    # --- T5.6e: E2E toan trinh ------------------------------------------------
    e2e = overall.get("e2e") or {}
    if not e2e:
        store.skip(
            "T5.6e",
            "khong co khoi e2e trong bao cao — bo phat hien khong duoc truyen vao "
            "hoac khong chay duoc tren tap nhan",
        )
    else:
        a7 = e2e.get("exact")
        detection_rate = e2e.get("detection_rate")
        store.put(
            "T5.6e",
            {
                "a7_e2e": a7,
                "a7_voi_dieu_kien_da_phat_hien": e2e.get("exact_given_detected"),
                "ty_le_bien_bi_bo_sot": (
                    None if detection_rate is None else round(1 - detection_rate, 4)
                ),
                "ty_le_phat_hien_dung_nhung_doc_sai": (
                    None
                    if e2e.get("exact_given_detected") is None
                    else round(1 - e2e["exact_given_detected"], 4)
                ),
                "chenh_lech_a6_tru_a7": (
                    None if a6 is None or a7 is None else round((a6 - a7) * 100, 2)
                ),
                "so_mau": e2e.get("count"),
                "ket_qua_nfr_a7": verdict("NFR-A7", a7),
                "canh_bao_hieu_luc": (report.get("requirements", {}).get("NFR-A7") or {}).get(
                    "validity_reason"
                ),
            },
        )

    return output


# --------------------------------------------------------------------------- #
# Phep do 6 — phan tich loi (T5.10)
# --------------------------------------------------------------------------- #
def adapt_ocr_report_for_error_analysis(ocr_report: Path) -> Path:
    """Doi ten truong cua bao cao ``ocr_accuracy`` sang luoc do ``error_analysis``.

    Hai module ra doi o hai giai doan khac nhau va dat ten truong khac nhau:
    ``ocr_accuracy`` ghi ``truth`` / ``raw_ocr_text`` / ``plate_number``, con
    ``error_analysis`` doc ``ground_truth`` / ``pre_norm_text`` /
    ``post_norm_text``. Neu nap thang, moi truong deu rong va **moi ca deu bi
    phan loai la dung** — tuc bang T5.10 se hien 0 loi mot cach im lang. Ham nay
    tao mot ban sao da doi ten de tranh dung che do that bai do.

    Args:
        ocr_report: Bao cao do ``ai.evaluation.ocr_accuracy`` sinh ra.

    Returns:
        Duong dan ban sao da chuyen doi.

    Raises:
        FileNotFoundError: Neu bao cao khong ton tai.
        ValueError: Neu bao cao khong co danh sach ``samples``.
        OSError: Neu khong ghi duoc ban sao.
    """
    payload = read_json(ocr_report)
    samples = payload.get("samples")
    if not samples:
        raise ValueError(f"{ocr_report} khong co danh sach 'samples'")

    adapted_samples = []
    for sample in samples:
        adapted_samples.append(
            {
                **sample,
                "ground_truth": sample.get("truth", ""),
                "pre_norm_text": sample.get("raw_ocr_text", ""),
                "post_norm_text": sample.get("plate_number", ""),
            }
        )
    destination = ocr_report.with_name(f"{ocr_report.stem}-adapted.json")
    destination.write_text(
        json.dumps(
            {
                "engine": (payload.get("engines") or {}).get("recognizer", "unknown"),
                "generated_at": (payload.get("run") or {}).get("started")
                or payload.get("generated_at", "unknown"),
                "settings": payload.get("corpus", {}),
                "summary": (payload.get("by_line_count") or {}).get("overall", {}),
                "samples": adapted_samples,
            },
            indent=2,
            ensure_ascii=False,
            default=str,
        ),
        encoding="utf-8",
    )
    LOGGER.info("Da chuyen doi bao cao OCR sang luoc do error_analysis: %s", destination)
    return destination


def measure_errors(args: argparse.Namespace, ocr_report: Path | None, store: ResultStore) -> None:
    """Phan loai cac ca sai thanh E1...E6 va dem tan suat.

    Args:
        args: Doi so dong lenh.
        ocr_report: Bao cao OCR do :func:`measure_ocr` sinh ra.
        store: Kho ket qua.
    """
    LOGGER.info("=== [6/7] Phan tich loi (T5.10) ===")
    if ocr_report is None:
        store.skip("T5.10", "khong co bao cao OCR de phan tich (xem ly do o T5.6a)")
        return

    try:
        from ai.evaluation import error_analysis as ea
    except ImportError as error:
        store.skip("T5.10", f"khong import duoc error_analysis: {error}")
        return

    out_dir = reports_dir(args) / "05-ocr-errors"
    try:
        adapted = adapt_ocr_report_for_error_analysis(ocr_report)
    except (FileNotFoundError, ValueError, OSError) as error:
        store.skip("T5.10", f"khong chuyen doi duoc bao cao OCR: {error}")
        return

    argv = ["--report", str(adapted), "--output-dir", str(out_dir), "--no-export"]
    try:
        ea.main(argv)
        payload = read_json(out_dir / "error_analysis.json")
    except Exception as error:  # noqa: BLE001
        store.skip("T5.10", f"error_analysis that bai: {error!r}")
        return

    # Kiem tra cheo: neu error_analysis bao 0 loi trong khi bao cao OCR ghi nhan
    # do chinh xac chuoi duoi 100%, thi phep do da hong (thuong la lech ten truong
    # giua hai module). Bao "0 loi" trong tinh huong do la mot con so SAI, khong
    # phai mot ket qua tot — phai tu choi ghi no.
    a6 = store.value("T5.6b", "a6_sau_hau_xu_ly")
    if not payload.get("total_errors") and a6 is not None and a6 < 1.0:
        store.skip(
            "T5.10",
            f"error_analysis tra ve 0 ca sai trong khi NFR-A6 = {a6} (< 1,0). Hai con "
            f"so nay mau thuan nhau nen ket qua bi tu choi thay vi ghi 0. Nguyen nhan "
            f"kha di: lech ten truong giua ocr_accuracy va error_analysis.",
        )
        return

    by_class = payload.get("by_class") or {}
    by_layout = payload.get("by_line_count") or {}
    total_cases = payload.get("total_cases")
    total_errors = payload.get("total_errors")

    # E1 va E2 la loi cua TANG PHAT HIEN, khong nam trong pham vi cua
    # error_analysis (von phan loai chuoi). Chung duoc lay tu T5.6e khi co.
    missed = store.value("T5.6e", "ty_le_bien_bi_bo_sot")
    e1_cases = (
        None
        if missed is None or not isinstance(store.value("T5.6e", "so_mau"), int)
        else int(round(missed * store.value("T5.6e", "so_mau")))
    )

    rows: dict[str, dict[str, Any]] = {
        "E1": {
            "ten": "Bỏ sót biển",
            "so_ca": e1_cases,
            # E1 do tren luot E2E (mau so rieng), con E3...E6 do tren luot crop.
            # Chia chung mot mau so se cho ra ty le vo nghia, nen cot ty le cua
            # dong nay bi CO Y de trong.
            "mau_so_rieng": store.value("T5.6e", "so_mau"),
            "khong_chia_chung_mau_so": True,
            "ly_do_neu_thieu": (
                None if e1_cases is not None else "phu thuoc T5.6e — chua do duoc"
            ),
        },
        "E2": {
            "ten": "Phát hiện nhầm",
            "so_ca": NOT_MEASURED,
            "ly_do_neu_thieu": (
                "so duong tinh gia nam o T5.5a (false_positives cua bo doi sanh noi "
                "bo), khong cung mau so voi cac loai E3...E6 nen khong duoc gop chung "
                "vao mot cot ty le"
            ),
        },
        "E3": {"ten": "Nhầm ký tự", "so_ca": by_class.get("substitution")},
        "E4": {"ten": "Thiếu ký tự", "so_ca": by_class.get("missing_chars")},
        "E5": {"ten": "Thừa ký tự", "so_ca": by_class.get("extra_chars")},
        "E6": {"ten": "Sai thứ tự", "so_ca": by_class.get("transposition")},
    }
    for key, row in rows.items():
        count = row.get("so_ca")
        if row.get("khong_chia_chung_mau_so"):
            denominator = row.get("mau_so_rieng")
            row["ty_le_tren_mau_so_rieng"] = (
                round(count / denominator, 4)
                if isinstance(count, int) and isinstance(denominator, int) and denominator
                else None
            )
            continue
        if isinstance(count, int) and total_errors:
            row["ty_le_trong_tong_ca_sai"] = round(count / total_errors, 4)
        if isinstance(count, int) and total_cases:
            row["ty_le_trong_toan_tap"] = round(count / total_cases, 4)
        for layout_key, layout_name in (("1_line", "mot_dong"), ("2_line", "hai_dong")):
            source = by_layout.get(layout_key) or {}
            mapping = {
                "E3": "substitution",
                "E4": "missing_chars",
                "E5": "extra_chars",
                "E6": "transposition",
            }
            row[layout_name] = source.get(mapping.get(key)) if key in mapping else None

    store.put(
        "T5.10",
        {
            "loai_loi": rows,
            "cac_loai_khac": {
                "empty_read": by_class.get("empty_read"),
                "mixed": by_class.get("mixed"),
                "ghi_chu": (
                    "Hai loai nay co trong cai dat nhung khong co ma E tuong ung trong "
                    "bang 5.10.1. Phai them dong cho chung hoac gop co giai thich — "
                    "khong duoc bo im lang vi khi do tong se khong bang 100%."
                ),
            },
            "tong_so_ca_sai": total_errors,
            "tong_so_ca_danh_gia": total_cases,
            "ty_le_loi": payload.get("error_rate"),
            "tep_nguon": str(out_dir / "error_analysis.json"),
        },
    )


# --------------------------------------------------------------------------- #
# Phep do 7 — chiu tai, bo nho, do tin cay (T5.7e)
# --------------------------------------------------------------------------- #
def measure_stress(args: argparse.Namespace, weights: Path, store: ResultStore) -> None:
    """Do chiu tai dong thoi va soak.

    Args:
        args: Doi so dong lenh.
        weights: Trong so can do.
        store: Kho ket qua.
    """
    LOGGER.info("=== [7/7] Chiu tai, bo nho, do tin cay ===")
    if args.skip_slow:
        store.skip(
            "T5.7e",
            "bo qua theo --skip-slow. Chay lai khong co co nay de do (khoang 10 phut).",
        )
        return

    try:
        from ai.evaluation import stress_test as stress
    except ImportError as error:
        store.skip("T5.7e", f"khong import duoc stress_test: {error}")
        return

    images_root = Path(args.data).parent / "images" / args.split
    output = reports_dir(args) / "05-stress-test.json"
    argv = [
        "--weights", str(weights),
        "--images", str(images_root),
        "--concurrency", "1", "2", "5", "10",
        "--soak-seconds", "300",
        "--device", "cpu",
        "--output", str(output),
    ]
    try:
        stress.main(argv)
        report = read_json(output)
    except Exception as error:  # noqa: BLE001
        store.skip("T5.7e", f"stress_test that bai: {error!r}")
        return

    concurrency = report.get("concurrency") or {}
    soak = report.get("soak") or {}
    hardware = report.get("hardware") or {}
    store.put(
        "T5.7e",
        {
            "so_yeu_cau_dong_thoi_on_dinh": concurrency.get("max_error_free_concurrency"),
            "dat_nfr_sc1": concurrency.get("meets_nfr_sc1"),
            "soak_so_yeu_cau": soak.get("requests"),
            "soak_ty_le_thanh_cong": soak.get("success_rate"),
            "soak_dat_nfr_r4": soak.get("meets_target"),
            "soak_tang_rss_gb": soak.get("rss_growth_gb"),
            "rss_pipeline_gb": hardware.get("rss_gb"),
            "muc_dong_thoi_da_do": [
                entry.get("concurrency") for entry in (concurrency.get("levels") or [])
            ],
            "moc_da_do_truoc_do": {
                "nfr_p4_nap_model_s": 6.41,
                "nfr_p4b_health_s": 8.36,
                "nfr_p5_api_overhead_p95_ms": 19.01,
                "nfr_p6_truy_van_10000_p95_ms": 18.71,
                "nfr_p7a_rss_pipeline_gb": 0.759,
                "nfr_p7b_rss_server_gb": 0.806,
                "nfr_r4_soak_300s": "100% (185/185)",
                "nguon": "do tren baseline-416-v1.pt, xem docs/reports/07-*.json",
            },
            "tep_nguon": str(output),
        },
    )


# --------------------------------------------------------------------------- #
# Cac bang khong can suy luan: T5.2b, T5.4b
# --------------------------------------------------------------------------- #
def collect_library_versions(store: ResultStore) -> None:
    """Ghi phien ban thu vien tai dung thoi diem do (bang T5.2b).

    Args:
        store: Kho ket qua.
    """
    LOGGER.info("Thu thap phien ban thu vien cho T5.2b")
    packages = (
        "ultralytics", "torch", "torchvision", "paddleocr", "paddlepaddle",
        "onnxruntime", "openvino", "opencv-python", "numpy", "fastapi",
        "uvicorn", "sqlalchemy", "imagehash", "pytest",
    )
    versions: dict[str, Any] = {}
    for name in packages:
        try:
            from importlib.metadata import version

            versions[name] = version(name)
        except Exception:  # noqa: BLE001
            versions[name] = NOT_MEASURED
    store.put(
        "T5.2b",
        {
            "moi_truong": sys.prefix,
            "phien_ban": versions,
            "ghi_chu": (
                "Chi do duoc moi truong dang chay script. Cot con lai cua bang T5.2b "
                "phai lay bang cach chay chinh script nay trong moi truong ao con lai, "
                "hoac chay 'pip freeze' cua moi truong do."
            ),
        },
    )


def collect_training_curve(store: ResultStore, run_dir: Path) -> None:
    """Doc ``results.csv`` cua lượt huan luyen cho bang T5.4b.

    Args:
        store: Kho ket qua.
        run_dir: Thu muc lượt huan luyen Ultralytics.
    """
    LOGGER.info("Doc duong cong huan luyen tu %s", run_dir)
    csv_path = run_dir / "results.csv"
    if not csv_path.exists():
        store.skip("T5.4b", f"khong tim thay {csv_path} — luot huan luyen chua ket thuc?")
        return
    try:
        with csv_path.open(encoding="utf-8", newline="") as handle:
            rows = [{k.strip(): v.strip() for k, v in row.items()} for row in csv.DictReader(handle)]
    except OSError as error:
        store.skip("T5.4b", f"khong doc duoc {csv_path}: {error}")
        return
    if not rows:
        store.skip("T5.4b", f"{csv_path} rong")
        return

    def num(row: dict[str, str], key: str) -> float | None:
        """Doc mot cot so, tra ``None`` khi thieu hoac khong phai so."""
        try:
            return float(row[key])
        except (KeyError, TypeError, ValueError):
            return None

    epochs: dict[str, Any] = {}
    for row in rows:
        index = num(row, "epoch")
        if index is None:
            continue
        epochs[str(int(index))] = {
            "val_box_loss": num(row, "val/box_loss"),
            "val_cls_loss": num(row, "val/cls_loss"),
            "val_dfl_loss": num(row, "val/dfl_loss"),
            "map50": num(row, "metrics/mAP50(B)"),
            "map5095": num(row, "metrics/mAP50-95(B)"),
            "precision": num(row, "metrics/precision(B)"),
            "recall": num(row, "metrics/recall(B)"),
        }

    best_epoch, best_value = None, None
    for index, values in epochs.items():
        value = values.get("map5095")
        if value is not None and (best_value is None or value > best_value):
            best_epoch, best_value = index, value

    store.put(
        "T5.4b",
        {
            "theo_epoch": epochs,
            "so_epoch_da_chay": len(epochs),
            "epoch_tot_nhat_theo_map5095": best_epoch,
            "canh_bao": (
                None
                if len(epochs) >= 20
                else f"moi co {len(epochs)}/20 epoch — luot huan luyen CHUA ket thuc, "
                f"khong duoc cong bo cac dong nay nhu ket qua cuoi cung"
            ),
            "tep_nguon": str(csv_path),
        },
    )


# --------------------------------------------------------------------------- #
# T5.3b — kiem chung ro ri du lieu theo nhieu nguong Hamming
# --------------------------------------------------------------------------- #
def measure_leakage(args: argparse.Namespace, store: ResultStore) -> None:
    """Dem so cap anh gan trung xuyen split train<->test o nhieu nguong Hamming.

    Muc 5.3.3 cua Chuong 5 doi hoi do o **nhieu** nguong chu khong chi o nguong
    da dung de gop trung lap: do o dung nguong gop la kiem tra lai chinh dinh
    nghia cua minh, khong phai kiem chung doc lap. Chi cac nguong **lon hon**
    nguong gop moi mang thong tin moi.

    Phan bam tri giac chi chay **mot lan** roi dem lai o moi nguong tren cung mot
    ma tran khoang cach, thay vi goi ``leak_check`` sau lan — bam la phan dat
    nhat, va chay lai sau lan se cho ra dung cung mot bo bam.

    Args:
        args: Doi so dong lenh.
        store: Kho ket qua.
    """
    LOGGER.info("=== [T5.3b] Kiem chung ro ri du lieu theo %d nguong ===", len(LEAK_THRESHOLDS))
    try:
        import numpy as np

        from ai.evaluation import leak_check as lc
    except ImportError as error:
        store.skip("T5.3b", f"thieu thu vien cho kiem chung ro ri: {error}")
        return

    images_root = Path(args.data).parent / "images"
    if not images_root.is_dir():
        store.skip("T5.3b", f"khong tim thay thu muc anh {images_root}")
        return

    try:
        train_paths = lc.discover_images(images_root / "train")
        test_paths = lc.discover_images(images_root / args.split)
    except Exception as error:  # noqa: BLE001
        store.skip("T5.3b", f"khong liet ke duoc anh: {error!r}")
        return
    if not train_paths or not test_paths:
        store.skip(
            "T5.3b",
            f"split rong: train={len(train_paths)} anh, {args.split}={len(test_paths)} anh",
        )
        return

    warning: str | None = None
    if args.skip_slow:
        train_paths = train_paths[:LEAK_SMOKE_CAP]
        test_paths = test_paths[:LEAK_SMOKE_CAP]
        warning = (
            f"CHAY THU (--skip-slow): chi bam {len(train_paths)} anh train x "
            f"{len(test_paths)} anh {args.split} thay vi toan bo split. So cap dem "
            f"duoc KHONG the so sanh voi con so cua v1/v2 (do tren toan bo split) va "
            f"KHONG duoc dien vao Chuong 5."
        )
        LOGGER.warning(warning)

    try:
        train_hashes = lc.hash_split("train", train_paths)
        test_hashes = lc.hash_split(args.split, test_paths)
        distances = lc.hamming_matrix(train_hashes.bits, test_hashes.bits)
    except Exception as error:  # noqa: BLE001
        store.skip("T5.3b", f"khong bam duoc anh: {error!r}")
        return

    rows: dict[str, Any] = {}
    for threshold in LEAK_THRESHOLDS:
        rows[str(threshold)] = {
            "nguong": threshold,
            "v1_so_cap": V1_V2_LEAK_PAIRS["v1"] if threshold == DEDUP_THRESHOLD_V3 else None,
            "v2_so_cap": V1_V2_LEAK_PAIRS["v2"] if threshold == DEDUP_THRESHOLD_V3 else None,
            "v3_so_cap": int(np.count_nonzero(distances <= threshold)),
            "mang_thong_tin_moi": LEAK_THRESHOLD_NOTE[threshold],
        }

    store.put(
        "T5.3b",
        {
            "theo_nguong": rows,
            "khoang_cach_nho_nhat": int(distances.min()) if distances.size else None,
            "so_anh_train": train_hashes.count,
            "so_anh_split_danh_gia": test_hashes.count,
            "split_danh_gia": args.split,
            "so_cap_da_so_sanh": int(train_hashes.count) * int(test_hashes.count),
            "anh_khong_doc_duoc": {
                "train": train_hashes.unreadable,
                args.split: test_hashes.unreadable,
            },
            "phuong_phap": f"imagehash.phash {train_hashes.bits.shape[1]} bit",
            "nguong_gop_trung_lap_cua_v3": DEDUP_THRESHOLD_V3,
            "canh_bao": warning,
            "ghi_chu": (
                "Cot v1 va v2 chi co so o nguong 10 vi do la con so da do truoc do "
                "tren hai bo du lieu ay; cac o con lai cua hai cot do de trong chu "
                "KHONG duoc suy ra. O v3 tai nguong 10 bang hoac gan 0 la HE QUA DINH "
                "NGHIA (v3 duoc khu trung lap o dung nguong 10), khong phai phat hien "
                "thuc nghiem — chi cac nguong 12, 15, 20 moi mang thong tin moi. Phash "
                "khong bat duoc ro ri o muc ngu nghia (cung mot bien so chup goc khac), "
                "nen ket qua thap KHONG chung minh tap test doc lap."
            ),
        },
    )


# --------------------------------------------------------------------------- #
# T5.3c — phan bo nguon du lieu giua cac split
# --------------------------------------------------------------------------- #
def measure_source_distribution(args: argparse.Namespace, store: ResultStore) -> None:
    """Dem so anh cua tung nguon du lieu trong tung split.

    Neu mot nguon tap trung bat can xung vao mot split thi chi so tren split do
    phan anh dac tinh cua nguon chu khong phan anh nang luc tong quat cua mo
    hinh. So lieu lay tu ``split_manifest.csv`` — ban ghi do chinh script chia
    split sinh ra, nen day la ban ghi **da thuc thi**.

    Args:
        args: Doi so dong lenh.
        store: Kho ket qua.
    """
    LOGGER.info("=== [T5.3c] Phan bo nguon du lieu giua cac split ===")
    manifest = Path(args.data).parent / "split_manifest.csv"
    if not manifest.exists():
        store.skip("T5.3c", f"khong tim thay {manifest}")
        return

    try:
        with manifest.open(encoding="utf-8-sig", newline="") as handle:
            records = list(csv.DictReader(handle))
    except OSError as error:
        store.skip("T5.3c", f"khong doc duoc {manifest}: {error}")
        return
    if not records:
        store.skip("T5.3c", f"{manifest} rong")
        return

    header = {key.strip().lower() for key in (records[0] or {})}
    if not {"split", "source_dataset"} <= header:
        store.skip(
            "T5.3c",
            f"{manifest} thieu cot 'split' hoac 'source_dataset' (co: {sorted(header)})",
        )
        return

    splits = ("train", "val", "test")
    per_source: dict[str, dict[str, int]] = {}
    unknown_split = 0
    for record in records:
        source = (record.get("source_dataset") or "khong xac dinh").strip()
        split = (record.get("split") or "").strip().lower()
        bucket = per_source.setdefault(source, {name: 0 for name in splits})
        if split in bucket:
            bucket[split] += 1
        else:
            unknown_split += 1

    # Mot anh da qua khu trung lap co the mang xuat xu tu NHIEU nguon, va manifest
    # ghi ca tap xuat xu do ngan cach bang '|'. Vi vay so dong cua bang lon hon 6:
    # moi dong la mot TO HOP xuat xu, khong phai mot nguon. Dem rieng cac nguon
    # nguyen to de doi chieu voi con so 6 NGUON NGUYEN TO cua tap v3 o bang T5.3a
    # (luu y: 9 = so bo DA TAI VE, 7 = so bo VAO HOP NHAT detection) — khong gop chung
    # vao bang chinh vi mot anh se bi dem nhieu lan va tong se khong con bang
    # 15.133.
    atomic_sources: dict[str, int] = {}
    for source, counts in per_source.items():
        for part in source.split("|"):
            name = part.strip()
            if name:
                atomic_sources[name] = atomic_sources.get(name, 0) + sum(counts.values())

    grand_total = sum(sum(b.values()) for b in per_source.values())
    totals = {name: sum(b[name] for b in per_source.values()) for name in splits}
    # Ti le tong the cua tung split, dung lam moc de phat hien nguon lech.
    overall_share = {
        name: (totals[name] / grand_total if grand_total else None) for name in splits
    }

    rows: dict[str, Any] = {}
    skewed: list[str] = []
    for source in sorted(per_source, key=lambda s: -sum(per_source[s].values())):
        counts = per_source[source]
        total = sum(counts.values())
        shares = {name: (counts[name] / total if total else None) for name in splits}
        # Tieu chi doc bang o muc 5.3.4: lech qua 10 diem phan tram so voi ti le
        # tong the cua split do thi phai neu ten nguon va ban luan anh huong.
        deviation = None
        if shares["test"] is not None and overall_share["test"] is not None:
            deviation = round((shares["test"] - overall_share["test"]) * 100, 2)
            if abs(deviation) > SOURCE_SKEW_LIMIT_POINTS:
                skewed.append(source)
        rows[source] = {
            "tong_so_anh": total,
            "train": counts["train"],
            "val": counts["val"],
            "test": counts["test"],
            "ty_le_train": None if shares["train"] is None else round(shares["train"], 4),
            "ty_le_val": None if shares["val"] is None else round(shares["val"], 4),
            "ty_le_test": None if shares["test"] is None else round(shares["test"], 4),
            "lech_test_so_voi_tong_the_diem_pt": deviation,
            "canh_bao": (
                "lech quá 10 điểm phần trăm so với tỉ lệ test tổng thể — phải nêu tên "
                "nguồn này và thảo luận ảnh hưởng ở mục 5.3.4"
                if deviation is not None and abs(deviation) > SOURCE_SKEW_LIMIT_POINTS
                else None
            ),
        }

    store.put(
        "T5.3c",
        {
            "theo_nguon": rows,
            "so_to_hop_xuat_xu": len(rows),
            "nguon_nguyen_to": dict(
                sorted(atomic_sources.items(), key=lambda item: -item[1])
            ),
            "so_nguon_nguyen_to": len(atomic_sources),
            "tong": {
                "tong_so_anh": grand_total,
                "train": totals["train"],
                "val": totals["val"],
                "test": totals["test"],
                "ty_le_train": None if not grand_total else round(overall_share["train"], 4),
                "ty_le_val": None if not grand_total else round(overall_share["val"], 4),
                "ty_le_test": None if not grand_total else round(overall_share["test"], 4),
            },
            "nguon_lech_qua_nguong": skewed,
            "so_ban_ghi_khong_ro_split": unknown_split,
            "tep_nguon": str(manifest),
            "ghi_chu": (
                "Moi dong la mot TO HOP xuat xu, khong phai mot nguon: sau khi khu "
                "trung lap, mot anh giu lai co the den tu nhieu nguon cung luc va "
                "manifest ghi ca tap xuat xu ngan cach bang '|'. Do do so dong lon hon "
                "con so 6 nguon nguyen to cua tap v3; khoa 'nguon_nguyen_to' liet ke tung nguon "
                "rieng le, nhung cac so trong do CONG DON QUA 15.133 vi anh da nguon bi "
                "dem nhieu lan — khong duoc dung lam mau so. Ti le cua tung dong tinh "
                "theo mau so la TONG SO ANH CUA CHINH DONG do, khong phai tong toan bo "
                "corpus. Cot lech so sanh ti le test cua dong voi ti le test tong the; "
                f"nguong canh bao {SOURCE_SKEW_LIMIT_POINTS} diem phan tram lay tu tieu "
                "chi doc bang o muc 5.3.4."
            ),
        },
    )


# --------------------------------------------------------------------------- #
# T5.8 va T5.9 — tong hop
# --------------------------------------------------------------------------- #
def build_comparison(store: ResultStore, weights: Path) -> None:
    """Ghep bang T5.8 so sanh baseline voi mo hinh chinh thuc.

    Args:
        store: Kho ket qua.
        weights: Trong so chinh thuc da danh gia.
    """
    baseline = {
        "imgsz": 416,
        "bo_du_lieu": "v1 — 4.578 ảnh, 1 nguồn",
        "nguong_gop_trung_lap": 5,
        "ro_ri_train_test_nguong_10": "619 cặp",
        "so_epoch": 40,
        "tong_thoi_gian_phut": 156,
        "map50": 0.9933,
        "map5095": 0.8597,
        "precision": 0.9822,
        "recall": 0.9810,
        "map50_mot_dong": 0.9856,
        "map50_hai_dong": 0.9592,
        "chenh_layout_diem_pt": 2.6,
        # Client-side warm p95 qua HTTP, may ranh (07-benchmark-p1-resolved.json).
        # Con so cu 5857,19 ms da bi bac bo — khong dung lai.
        "do_tre_p95_ms": 763.75,
    }
    official = {
        "imgsz": 640,
        "bo_du_lieu": "v3 — 15.133 ảnh, 6 nguồn nguyên tố (hợp nhất từ 7 bộ)",
        "nguong_gop_trung_lap": 10,
        "ro_ri_train_test_nguong_10": NOT_MEASURED,
        "so_epoch": store.value("T5.4b", "so_epoch_da_chay"),
        "tong_thoi_gian_phut": NOT_MEASURED,
        "map50": store.value("T5.5a", "map50"),
        "map5095": store.value("T5.5a", "map5095"),
        "precision": store.value("T5.5a", "precision"),
        "recall": store.value("T5.5a", "recall"),
        "map50_mot_dong": (store.value("T5.5b", "mot_dong") or {}).get("map50")
        if isinstance(store.value("T5.5b", "mot_dong"), dict)
        else None,
        "map50_hai_dong": (store.value("T5.5b", "hai_dong") or {}).get("map50")
        if isinstance(store.value("T5.5b", "hai_dong"), dict)
        else None,
        "chenh_layout_diem_pt": (store.value("T5.5b", "chenh_lech_diem_pt") or {}).get("map50")
        if isinstance(store.value("T5.5b", "chenh_lech_diem_pt"), dict)
        else None,
        "do_tre_p95_ms": store.value("T5.7a", "p95_ms"),
    }
    store.put(
        "T5.8",
        {
            "baseline_416_v1": baseline,
            "chinh_thuc": official,
            "trong_so_chinh_thuc": str(weights),
            "canh_bao_quy_ket": (
                "Ba bien thay doi dong thoi (imgsz, bo du lieu + cach chia, so epoch) "
                "va chung tac dong NGUOC CHIEU nhau. Phat bieu duy nhat duoc phep la "
                "mo ta: 'cau hinh A cho X, cau hinh B cho Y'. Khong duoc quy ket "
                "nguyen nhan cho bat ky bien nao."
            ),
        },
    )


def build_nfr_summary(store: ResultStore) -> list[dict[str, Any]]:
    """Dung bang doi chieu NFR (T5.9) tu cac phep do da co.

    Args:
        store: Kho ket qua.

    Returns:
        Danh sach dong cua bang T5.9.
    """
    layout_b = store.value("T5.5b", "chenh_lech_diem_pt")
    layout_gap = layout_b.get("map50") if isinstance(layout_b, dict) else None

    rows: list[dict[str, Any]] = [
        {"ma": "P1", "chi_tieu": "Độ trễ E2E một ảnh, p95 (ms)", "do_duoc": store.value("T5.7a", "p95_ms"), "nfr": "NFR-P1"},
        {"ma": "P2", "chi_tieu": "Tốc độ khung hình webcam (FPS)", "do_duoc": None, "nfr": None,
         "ly_do": "chua co kich ban do webcam — muc D.3 cua ch5-thuc-nghiem.md"},
        {"ma": "P3", "chi_tieu": "Tốc độ xử lý video (× thời gian thực)", "do_duoc": None, "nfr": None,
         "ly_do": "chua co kich ban do video"},
        {"ma": "P4", "chi_tieu": "Thời gian nạp mô hình (s)", "do_duoc": 6.41, "nfr": "NFR-P4",
         "ghi_chu": "do tren baseline-416-v1.pt"},
        {"ma": "P5", "chi_tieu": "Overhead API, p95 (ms)", "do_duoc": 19.01, "nfr": "NFR-P5",
         "ghi_chu": "do tren baseline-416-v1.pt"},
        {"ma": "P6", "chi_tieu": "Truy vấn 10.000 bản ghi, p95 (ms)", "do_duoc": 18.71, "nfr": "NFR-P6",
         "ghi_chu": "do tren baseline-416-v1.pt"},
        {"ma": "P7a", "chi_tieu": "RSS pipeline (GB)", "do_duoc": 0.759, "nfr": "NFR-P7a"},
        {"ma": "P7b", "chi_tieu": "RSS máy chủ backend (GB)", "do_duoc": 0.806, "nfr": "NFR-P7b"},
        {"ma": "A1", "chi_tieu": "mAP@0.5 của bộ phát hiện", "do_duoc": store.value("T5.5a", "map50"), "nfr": "NFR-A1"},
        {"ma": "A2", "chi_tieu": "mAP@0.5:0.95 của bộ phát hiện", "do_duoc": store.value("T5.5a", "map5095"), "nfr": "NFR-A2"},
        {"ma": "A3-P", "chi_tieu": "Precision phát hiện", "do_duoc": store.value("T5.5a", "precision"), "nfr": "NFR-A3p"},
        {"ma": "A3-R", "chi_tieu": "Recall phát hiện", "do_duoc": store.value("T5.5a", "recall"), "nfr": "NFR-A3r"},
        {"ma": "A4", "chi_tieu": "1 − CER (mức ký tự)", "do_duoc": store.value("T5.6a", "char_accuracy_sau"), "nfr": "NFR-A4"},
        {"ma": "A5", "chi_tieu": "Chuỗi đầy đủ trước hậu xử lý", "do_duoc": store.value("T5.6b", "a5_truoc_hau_xu_ly"), "nfr": "NFR-A5"},
        {"ma": "A6", "chi_tieu": "Chuỗi đầy đủ sau hậu xử lý", "do_duoc": store.value("T5.6b", "a6_sau_hau_xu_ly"), "nfr": "NFR-A6"},
        {"ma": "A6−A5", "chi_tieu": "Đóng góp của khối hậu xử lý (điểm %)", "do_duoc": store.value("T5.6b", "muc_cai_thien_diem_pt"), "nfr": None},
        {"ma": "A7", "chi_tieu": "Độ chính xác E2E toàn trình", "do_duoc": store.value("T5.6e", "a7_e2e"), "nfr": "NFR-A7"},
        {"ma": "A8", "chi_tieu": "Chênh lệch layout, detection (điểm %)", "do_duoc": layout_gap, "nfr": None},
        {"ma": "A9", "chi_tieu": "Tách theo điều kiện ảnh", "do_duoc": None, "nfr": None,
         "ly_do": "bo du lieu KHONG co nhan dieu kien anh — day la han che that, khong "
                  "phai 'chua toi luot do'. Khong duoc gan nhan bang suy doan."},
        {"ma": "R4", "chi_tieu": "Tỉ lệ thành công soak 300 s", "do_duoc": store.value("T5.7e", "soak_ty_le_thanh_cong"), "nfr": "NFR-R4"},
        {"ma": "R5", "chi_tieu": "CSDL sống sót qua khởi động lại", "do_duoc": None, "nfr": None,
         "ly_do": "chua chay kich ban khoi dong lai"},
        {"ma": "SC1", "chi_tieu": "Số yêu cầu đồng thời xử lý ổn định", "do_duoc": store.value("T5.7e", "so_yeu_cau_dong_thoi_on_dinh"), "nfr": "NFR-SC1"},
        {"ma": "M2", "chi_tieu": "Độ bao phủ test tầng nghiệp vụ", "do_duoc": 0.881, "nfr": None,
         "ghi_chu": "861/862 test pass, 1 xfail, 0 fail; toan kho 42,0%"},
    ]
    for row in rows:
        code = row.get("nfr")
        row["ket_qua"] = verdict(code, row.get("do_duoc")) if code else (
            "⬜ chưa đo" if row.get("do_duoc") is None else "n/a"
        )
    store.put("T5.9", {"dong": rows})
    return rows


# --------------------------------------------------------------------------- #
# Xuat Markdown
# --------------------------------------------------------------------------- #
def cell(value: Any, digits: int = 4) -> str:
    """Dinh dang mot o bang Markdown.

    Args:
        value: Gia tri, ``None`` hoac chuoi ``chua do``.
        digits: So chu so thap phan.

    Returns:
        Chuoi o, ``—`` khi khong co so.
    """
    if value is None or value == NOT_MEASURED:
        return EM_DASH
    return vn(value, digits)


def render_markdown(store: ResultStore, meta: dict[str, Any]) -> str:
    """Sinh doan Markdown chua cac bang da dien so.

    Cau truc cot cua moi bang bam sat ``docs/papers/ch5-thuc-nghiem.md`` de
    nguoi dung chi viec copy de vao dung cho.

    Args:
        store: Kho ket qua.
        meta: Khoi ngu canh do.

    Returns:
        Noi dung Markdown.
    """
    out: list[str] = []
    add = out.append

    add("# Bảng số liệu Chương 5 — sinh tự động")
    add("")
    add(f"*Sinh lúc {meta['thoi_diem_do']} bằng `scripts/fill_chapter5.py`.*")
    add("")
    add("> **Điều kiện đo — bắt buộc đọc kèm mọi bảng bên dưới.** "
        f"CPU {meta.get('cpu_ten')}, {meta.get('so_nhan_vat_ly') or EM_DASH} nhân vật lý / "
        f"{meta.get('so_nhan_logic') or EM_DASH} nhân logic, RAM "
        f"{cell(meta.get('ram_tong_gb'), 2)} GB, {meta.get('he_dieu_hanh')}, "
        f"Python {meta.get('python')}, torch {meta.get('torch')}, "
        f"ultralytics {meta.get('ultralytics')}, `device=cpu`, kích thước lô = 1. "
        f"Mô hình: `{meta.get('duong_dan_model')}`. Bộ dữ liệu: "
        f"`{meta.get('dataset_yaml')}`, split `{meta.get('split')}`, "
        f"{vni(meta.get('so_anh_split'))} ảnh.")
    add("")
    add("Ô ghi `—` là ô **chưa đo được**; lý do cụ thể nằm ở khoá `ly_do` trong "
        "`docs/reports/05-results.json`. Không được điền 0 vào các ô đó.")
    add("")
    add("---")
    add("")

    # ---------------- T5.2b ----------------
    add("## {{T5.2b}} Phiên bản thư viện")
    add("")
    payload = store.get("T5.2b")
    if store.measured("T5.2b"):
        add(f"*Môi trường đo: `{payload['moi_truong']}`.*")
        add("")
        add("| Gói | Phiên bản đo được |")
        add("|---|:---:|")
        for name, value in payload["phien_ban"].items():
            add(f"| `{name}` | {value if value != NOT_MEASURED else EM_DASH} |")
        add("")
        add(f"> {payload['ghi_chu']}")
    else:
        add(f"*(chưa đo)* — {payload.get('ly_do')}")
    add("")

    # ---------------- T5.3b ----------------
    add("## {{T5.3b}} Số cặp gần trùng xuyên split theo ngưỡng Hamming")
    add("")
    payload = store.get("T5.3b")
    if store.measured("T5.3b"):
        if payload.get("canh_bao"):
            add(f"> ⚠ {payload['canh_bao']}")
            add("")
        add("| Ngưỡng Hamming | v1 — số cặp train↔test | v2 — số cặp train↔test | **v3 — số cặp train↔test** | Ô này có mang thông tin mới không? |")
        add("|:---:|---:|---:|---:|---|")
        for key in sorted(payload["theo_nguong"], key=lambda x: int(x)):
            row = payload["theo_nguong"][key]
            threshold = row["nguong"]
            label = f"**{threshold}**" if threshold == DEDUP_THRESHOLD_V3 else str(threshold)
            if threshold == 0:
                label += " (trùng khít bit-hash)"
            v1 = EM_DASH if row["v1_so_cap"] is None else f"**{vni(row['v1_so_cap'])}**"
            v2 = EM_DASH if row["v2_so_cap"] is None else f"**{vni(row['v2_so_cap'])}**"
            add(f"| {label} | {v1} | {v2} | **{vni(row['v3_so_cap'])}** | {row['mang_thong_tin_moi']} |")
        add("")
        add(f"> Mẫu số: {vni(payload['so_anh_train'])} ảnh train × "
            f"{vni(payload['so_anh_split_danh_gia'])} ảnh `{payload['split_danh_gia']}` = "
            f"{vni(payload['so_cap_da_so_sanh'])} cặp đã so sánh. Phương pháp: "
            f"{payload['phuong_phap']}. Khoảng cách Hamming nhỏ nhất quan sát được: "
            f"**{vni(payload['khoang_cach_nho_nhat'])}**.")
        add(">")
        add(f"> {payload['ghi_chu']}")
    else:
        add(f"*(chưa đo)* — {payload.get('ly_do')}")
    add("")

    # ---------------- T5.3c ----------------
    add("## {{T5.3c}} Phân bố nguồn dữ liệu giữa các split")
    add("")
    payload = store.get("T5.3c")
    if store.measured("T5.3c"):
        add("| Nguồn dữ liệu | Tổng số ảnh | Train (số / %) | Val (số / %) | Test (số / %) | Ghi chú |")
        add("|---|---:|---:|---:|---:|---|")

        def share_cell(count: Any, share: Any) -> str:
            """O dang 'so / phan tram'."""
            if share is None:
                return f"{vni(count)} / {EM_DASH}"
            return f"{vni(count)} / {vn(share * 100, 1)}%"

        for source, row in payload["theo_nguon"].items():
            note = row.get("canh_bao") or EM_DASH
            add(
                f"| `{source}` | {vni(row['tong_so_anh'])} | "
                f"{share_cell(row['train'], row['ty_le_train'])} | "
                f"{share_cell(row['val'], row['ty_le_val'])} | "
                f"{share_cell(row['test'], row['ty_le_test'])} | {note} |"
            )
        total = payload["tong"]
        add(
            f"| **Tổng** | **{vni(total['tong_so_anh'])}** | "
            f"**{share_cell(total['train'], total['ty_le_train'])}** | "
            f"**{share_cell(total['val'], total['ty_le_val'])}** | "
            f"**{share_cell(total['test'], total['ty_le_test'])}** | |"
        )
        add("")
        skewed = payload["nguon_lech_qua_nguong"]
        add(f"> {payload['so_to_hop_xuat_xu']} tổ hợp xuất xứ, dựng từ "
            f"**{payload['so_nguon_nguyen_to']} nguồn nguyên tố**: "
            f"{', '.join(f'`{s}`' for s in payload['nguon_nguyen_to'])}. Nguồn lệch quá "
            f"{vn(SOURCE_SKEW_LIMIT_POINTS, 0)} điểm phần trăm ở tập test: "
            f"{', '.join(f'`{s}`' for s in skewed) if skewed else '**không có**'}. "
            f"Số bản ghi không rõ split: {vni(payload['so_ban_ghi_khong_ro_split'])}.")
        add(">")
        add(f"> {payload['ghi_chu']}")
    else:
        add(f"*(chưa đo)* — {payload.get('ly_do')}")
    add("")

    # ---------------- T5.4b ----------------
    add("## {{T5.4b}} Tiến triển chỉ số trên tập validation theo epoch")
    add("")
    payload = store.get("T5.4b")
    if store.measured("T5.4b"):
        add("| Epoch | `box_loss` (val) | `cls_loss` (val) | `dfl_loss` (val) | mAP@0.5 | mAP@0.5:0.95 | Precision | Recall |")
        add("|:---:|---:|---:|---:|---:|---:|---:|---:|")
        for index in sorted(payload["theo_epoch"], key=lambda x: int(x)):
            row = payload["theo_epoch"][index]
            add(
                f"| {index} | {cell(row['val_box_loss'])} | {cell(row['val_cls_loss'])} | "
                f"{cell(row['val_dfl_loss'])} | **{cell(row['map50'])}** | "
                f"**{cell(row['map5095'])}** | {cell(row['precision'])} | {cell(row['recall'])} |"
            )
        add("")
        add(f"Epoch tốt nhất theo mAP@0.5:0.95 trên val: **{payload['epoch_tot_nhat_theo_map5095'] or EM_DASH}** "
            f"({payload['so_epoch_da_chay']} epoch đã chạy).")
        if payload.get("canh_bao"):
            add("")
            add(f"> ⚠ {payload['canh_bao']}")
    else:
        add(f"*(chưa đo)* — {payload.get('ly_do')}")
    add("")

    # ---------------- T5.5a ----------------
    add("## {{T5.5a}} Kết quả detection tổng thể")
    add("")
    payload = store.get("T5.5a")
    if store.measured("T5.5a"):
        add("| Chỉ số | Mã NFR | Ngưỡng tối thiểu | Mục tiêu | **Đo được** | Kết quả |")
        add("|---|:---:|---:|---:|---:|:---:|")
        add(f"| mAP@0.5 | NFR-A1 | 0,85 | 0,90 | **{cell(payload['map50'])}** | {verdict('NFR-A1', payload['map50'])} |")
        add(f"| mAP@0.5:0.95 | NFR-A2 | 0,55 | 0,65 | **{cell(payload['map5095'])}** | {verdict('NFR-A2', payload['map5095'])} |")
        add(f"| Precision | NFR-A3 | 0,88 | 0,92 | **{cell(payload['precision'])}** | {verdict('NFR-A3p', payload['precision'])} |")
        add(f"| Recall | NFR-A3 | 0,85 | 0,90 | **{cell(payload['recall'])}** | {verdict('NFR-A3r', payload['recall'])} |")
        add(f"| F1 | — | — | — | {cell(payload['f1'])} | n/a |")
        add(f"| Ngưỡng confidence dùng khi đo | — | — | — | {cell(payload['conf_toi_uu_theo_f1'], 2)} | n/a |")
        add(f"| Số ảnh tập test | — | — | — | **{vni(payload['so_anh_tap_test'])}** | n/a |")
        add(f"| Số đối tượng nhãn thật | — | — | — | **{vni(payload['so_doi_tuong_nhan_that'])}** | n/a |")
        add("")
        add(f"> Nguồn chỉ số: `{payload['nguon_chi_so']}`. {payload['conf_ghi_chu']}")
    else:
        add(f"*(chưa đo)* — {payload.get('ly_do')}")
    add("")

    # ---------------- T5.5b ----------------
    add("## {{T5.5b}} Detection tách theo layout (NFR-A8)")
    add("")
    payload = store.get("T5.5b")
    if store.measured("T5.5b"):
        one, two, gap = payload["mot_dong"], payload["hai_dong"], payload["chenh_lech_diem_pt"]
        add("| Chỉ số | Biển **một dòng** | Biển **hai dòng** | Chênh lệch (điểm %) | Mẫu số |")
        add("|---|---:|---:|---:|---:|")
        add(f"| Số đối tượng nhãn thật | {vni(one['so_doi_tuong'])} | {vni(two['so_doi_tuong'])} | n/a | "
            f"{vni((one['so_doi_tuong'] or 0) + (two['so_doi_tuong'] or 0))} |")
        for key, label in (
            ("map50", "mAP@0.5"), ("map5095", "mAP@0.5:0.95"),
            ("precision", "Precision"), ("recall", "Recall"), ("f1", "F1"),
        ):
            add(f"| {label} | {cell(one[key])} | {cell(two[key])} | {cell(gap[key], 2)} | |")
        add("")
        add(f"> Ngưỡng tỉ lệ khung hình: {cell(payload['nguong_ty_le_khung_hinh'], 1)}. "
            f"Tỉ lệ ô được suy bằng heuristic: {cell(payload['ty_le_o_suy_bang_heuristic'])}. "
            f"{payload['canh_bao_heuristic']}")
        add(">")
        moc = payload["moc_baseline_416_v1"]
        add(f"> Mốc baseline (`baseline-416-v1.pt`, split v1, imgsz 416): một dòng "
            f"{vn(moc['map50_mot_dong'])} so với hai dòng {vn(moc['map50_hai_dong'])}, "
            f"chênh {vn(moc['chenh_diem_pt'], 1)} điểm. {moc['ghi_chu']}")
    else:
        add(f"*(chưa đo)* — {payload.get('ly_do')}")
    add("")

    # ---------------- T5.5c ----------------
    add("## {{T5.5c}} Detection tách theo dải kích thước hộp giới hạn")
    add("")
    payload = store.get("T5.5c")
    if store.measured("T5.5c"):
        add("| Dải kích thước (diện tích box / diện tích ảnh) | Số đối tượng | Tỉ lệ trong tập test | mAP@0.5 | mAP@0.5:0.95 | Recall |")
        add("|---|---:|---:|---:|---:|---:|")
        for band, _, _ in SIZE_BANDS:
            row = payload["dai"][band]
            warning = " ⚠" if row.get("canh_bao") else ""
            share = row.get("ty_le_trong_tap")
            add(
                f"| {SIZE_BAND_LABELS_VI[band]} | {vni(row['so_doi_tuong'])}{warning} | "
                f"{EM_DASH if share is None else vn(share * 100, 2) + '%'} | "
                f"{cell(row['map50'])} | {cell(row['map5095'])} | {cell(row['recall'])} |"
            )
        total = payload["toan_tap"]
        add(f"| **Toàn tập test** | **{vni(total['so_doi_tuong'])}** | 100% | "
            f"**{cell(total['map50'])}** | **{cell(total['map5095'])}** | **{cell(total['recall'])}** |")
        add("")
        add(f"> Đo trên {vni(payload['so_anh'])} ảnh. "
            f"Số box không gán được dải: {vni(payload['so_box_khong_gan_duoc_dai'])}. "
            f"Dòng có ⚠ là dòng dưới 30 đối tượng — **không có ý nghĩa thống kê**, "
            f"không được đưa vào so sánh. {payload['ghi_chu']}")
    else:
        add(f"*(chưa đo)* — {payload.get('ly_do')}")
    add("")

    # ---------------- T5.6a ----------------
    add("## {{T5.6a}} Độ chính xác mức ký tự (NFR-A4)")
    add("")
    payload = store.get("T5.6a")
    if store.measured("T5.6a"):
        add("| Chỉ số | Ngưỡng tối thiểu | Mục tiêu | **Đo được (trước hậu xử lý)** | **Đo được (sau hậu xử lý)** | Kết quả |")
        add("|---|---:|---:|---:|---:|:---:|")
        add(f"| 1 − CER (NFR-A4) | 0,92 | 0,95 | {cell(payload['char_accuracy_truoc'])} | "
            f"**{cell(payload['char_accuracy_sau'])}** | {payload['ket_qua_nfr_a4']} |")
        add(f"| CER | ≤ 0,08 | ≤ 0,05 | {cell(payload['cer_truoc'])} | {cell(payload['cer_sau'])} | n/a |")
        for label, key in (
            ("Số ký tự nhãn thật ($N$)", "N_so_ky_tu_nhan_that"),
            ("Số ký tự thay thế ($S$)", "S_thay_the"),
            ("Số ký tự bị xoá ($D$)", "D_bi_xoa"),
            ("Số ký tự chèn thừa ($I$)", "I_chen_thua"),
        ):
            value = payload[key]
            text = EM_DASH if value in (None, NOT_MEASURED) else vni(value)
            add(f"| {label} | — | — | {text} | {text} | n/a |")
        add(f"| **Số biển có nhãn chuỗi (mẫu số)** | — | — | **{vni(payload['so_mau'])}** | **{vni(payload['so_mau'])}** | n/a |")
        add("")
        if payload.get("S_D_I_ly_do"):
            add(f"> ⚠ S/D/I chưa tách được: {payload['S_D_I_ly_do']}")
        elif payload.get("S_D_I_nguon"):
            add(f"> {payload['S_D_I_nguon']} Ba cột $S$/$D$/$I$ đo trên **chuỗi thô "
                f"trước hậu xử lý**, nên chúng giống nhau ở cả hai cột đo được.")
        add("")
        add(f"> Phân bố số ca theo loại lỗi: `{payload.get('so_ca_theo_loai_loi')}`.")
    else:
        add(f"*(chưa đo)* — {payload.get('ly_do')}")
    add("")

    # ---------------- T5.6b ----------------
    add("## {{T5.6b}} Chuỗi đầy đủ trước và sau hậu xử lý (NFR-A5 ↔ A6)")
    add("")
    payload = store.get("T5.6b")
    if store.measured("T5.6b"):
        add("| Chỉ số | Mã NFR | Ngưỡng tối thiểu | Mục tiêu | **Đo được** | Kết quả |")
        add("|---|:---:|---:|---:|---:|:---:|")
        add(f"| Độ chính xác chuỗi **trước** hậu xử lý | NFR-A5 | 0,80 | 0,85 | **{cell(payload['a5_truoc_hau_xu_ly'])}** | {payload['ket_qua_nfr_a5']} |")
        add(f"| Độ chính xác chuỗi **sau** hậu xử lý | NFR-A6 | 0,85 | 0,90 | **{cell(payload['a6_sau_hau_xu_ly'])}** | {payload['ket_qua_nfr_a6']} |")
        add(f"| **Mức cải thiện (A6 − A5), điểm %** | — | — | — | **{cell(payload['muc_cai_thien_diem_pt'], 2)}** | n/a |")
        add(f"| Số biển **được sửa đúng** nhờ hậu xử lý | — | — | — | {vni(payload['so_bien_duoc_sua_dung'])} | n/a |")
        add(f"| Số biển **bị hậu xử lý làm hỏng** | — | — | — | {vni(payload['so_bien_bi_lam_hong'])} | n/a |")
        add(f"| Số biển sai cả trước lẫn sau | — | — | — | {vni(payload['so_bien_sai_ca_truoc_lan_sau'])} | n/a |")
        add(f"| **Số mẫu (biển có nhãn chuỗi)** | — | — | — | **{vni(payload['so_mau'])}** | n/a |")
        add("")
        add(f"> Nhánh diễn giải phải giữ lại ở mục 5.6.2: **nhánh {payload['nhanh_dien_giai'] or '?'}** "
            f"(A nếu hiệu số dương, B nếu bằng 0 hoặc âm).")
        add(">")
        breakdown = payload["phan_ra_theo_nhom_luat"]
        add(f"> Bảng phân rã theo nhóm luật: *(chưa đo)* — {breakdown['ly_do']}")
    else:
        add(f"*(chưa đo)* — {payload.get('ly_do')}")
    add("")

    # ---------------- T5.6c ----------------
    add("## {{T5.6c}} OCR tách theo layout")
    add("")
    payload = store.get("T5.6c")
    if store.measured("T5.6c"):
        one, two, gap = payload["mot_dong"], payload["hai_dong"], payload["chenh_lech_diem_pt"]
        add("| Chỉ số | Biển **một dòng** | Biển **hai dòng** | Chênh lệch (điểm %) |")
        add("|---|---:|---:|---:|")
        add(f"| Số mẫu có nhãn chuỗi | **{vni(one['so_mau'])}** | **{vni(two['so_mau'])}** | n/a |")
        add(f"| 1 − CER (NFR-A4) | {cell(one['char_accuracy'])} | {cell(two['char_accuracy'])} | {cell(gap['char_accuracy'], 2)} |")
        add(f"| Chuỗi đúng **trước** hậu xử lý (A5) | {cell(one['a5'])} | {cell(two['a5'])} | {cell(gap['a5'], 2)} |")
        add(f"| Chuỗi đúng **sau** hậu xử lý (A6) | {cell(one['a6'])} | {cell(two['a6'])} | {cell(gap['a6'], 2)} |")
        add(f"| Mức cải thiện do hậu xử lý (A6 − A5) | {cell(one['gain_points'], 2)} | {cell(two['gain_points'], 2)} | n/a |")
        add(f"| Độ chính xác E2E (A7) | {cell(one['a7'])} | {cell(two['a7'])} | {EM_DASH} |")
        add("")
        add(f"> {payload['moc_tham_chieu']}")
    else:
        add(f"*(chưa đo)* — {payload.get('ly_do')}")
    add("")

    # ---------------- T5.6d ----------------
    add("## {{T5.6d}} Cặp ký tự bị nhầm nhiều nhất")
    add("")
    payload = store.get("T5.6d")
    if store.measured("T5.6d"):
        add("| Hạng | Ký tự thật | Ký tự bị đọc thành | Số lần | Tỉ lệ trong tổng số lỗi thay thế | Bảng luật hiện có phủ cặp này không? | Hướng ánh xạ có đúng không? |")
        add("|:---:|:---:|:---:|---:|---:|:---:|---|")
        for item in payload["top_cap_nham"]:
            covered = item.get("co_trong_bang_luat")
            table = item.get("bang_luat")
            covered_text = f"có (`{table}`)" if covered else "không"
            share = item.get("ty_le_trong_tong_thay_the")
            add(
                f"| {item['hang']} | {item['ky_tu_that'] or EM_DASH} | {item['doc_thanh'] or EM_DASH} | "
                f"{vni(item['so_lan'])} | {EM_DASH if share is None else vn(share * 100, 2) + '%'} | "
                f"{covered_text} | {item.get('huong_anh_xa') or EM_DASH} |"
            )
        add("")
        add(f"> Ma trận `{payload['kich_thuoc_ma_tran']}`, mẫu số "
            f"{vni(payload['so_mau'])} biển có nhãn chuỗi, tổng số lỗi thay thế "
            f"(S) = {vni(payload['tong_so_thay_the'])}. Cột tỉ lệ lấy S làm mẫu số, "
            f"không lấy tổng của riêng nhóm dẫn đầu. Bảng đối chiếu ngược — các cặp "
            f"**có trong bảng luật nhưng không quan sát thấy** — nằm ở khoá "
            f"`doi_chieu_bang_luat.unobserved` trong `05-results.json`.")
    else:
        add(f"*(chưa đo)* — {payload.get('ly_do')}")
    add("")

    # ---------------- T5.6e ----------------
    add("## {{T5.6e}} Độ chính xác E2E toàn trình (NFR-A7)")
    add("")
    payload = store.get("T5.6e")
    if store.measured("T5.6e"):
        add("| Chỉ số | Ngưỡng tối thiểu | Mục tiêu | **Đo được** | Kết quả |")
        add("|---|---:|---:|---:|:---:|")
        add(f"| Độ chính xác E2E (NFR-A7) | 0,82 | 0,88 | **{cell(payload['a7_e2e'])}** | {payload['ket_qua_nfr_a7']} |")
        add(f"| Độ chính xác E2E **với điều kiện đã phát hiện được biển** | — | — | {cell(payload['a7_voi_dieu_kien_da_phat_hien'])} | n/a |")
        add(f"| Tỉ lệ biển **bị bỏ sót** ở tầng phát hiện | — | — | {cell(payload['ty_le_bien_bi_bo_sot'])} | n/a |")
        add(f"| Tỉ lệ biển phát hiện đúng nhưng **đọc sai chuỗi** | — | — | {cell(payload['ty_le_phat_hien_dung_nhung_doc_sai'])} | n/a |")
        add(f"| Chênh lệch A6 − A7 (điểm %) | — | — | {cell(payload['chenh_lech_a6_tru_a7'], 2)} | n/a |")
        add(f"| **Số mẫu** | — | — | **{vni(payload['so_mau'])}** | n/a |")
        if payload.get("canh_bao_hieu_luc"):
            add("")
            add(f"> ⚠ **Cảnh báo hiệu lực:** {payload['canh_bao_hieu_luc']}")
    else:
        add(f"*(chưa đo)* — {payload.get('ly_do')}")
    add("")

    # ---------------- T5.7a ----------------
    add("## {{T5.7a}} Độ trễ đầu-cuối một ảnh (NFR-P1)")
    add("")
    payload = store.get("T5.7a")
    if store.measured("T5.7a"):
        add("| Chỉ số | Ngưỡng tối thiểu | Mục tiêu | **Đo trên `baseline-416-v1.pt`** | **Đo trên mô hình đang đánh giá** | Kết quả |")
        add("|---|---:|---:|---:|---:|:---:|")
        add(f"| Độ trễ E2E p50 (ms) | — | — | {EM_DASH} | {cell(payload['p50_ms'], 2)} | n/a |")
        add(f"| **Độ trễ E2E p95 (ms)** | **≤ 1500** | **≤ 800** | **{vn(payload['moc_baseline_416_v1_p95_ms'], 2)}** | **{cell(payload['p95_ms'], 2)}** | **{payload['ket_qua_nfr_p1']}** |")
        add(f"| Độ trễ E2E p99 (ms) | — | — | {EM_DASH} | {cell(payload['p99_ms'], 2)} | n/a |")
        add(f"| Độ trễ trung bình (ms) | — | — | {EM_DASH} | {cell(payload['mean_ms'], 2)} | n/a |")
        add(f"| Độ lệch chuẩn (ms) | — | — | {EM_DASH} | {cell(payload['std_ms'], 2)} | n/a |")
        add(f"| Số ảnh đo | — | — | 100 | **{vni(payload['so_anh_do'])}** | n/a |")
        add(f"| Bội số vượt ngưỡng tối thiểu | — | — | 0,51× | {cell(payload['boi_so_vuot_nguong_toi_thieu'], 2)}× | n/a |")
        add(f"| Bội số vượt mục tiêu | — | — | 0,95× | {cell(payload['boi_so_vuot_muc_tieu'], 2)}× | n/a |")
        add("")
        add(f"> Số biển trung bình mỗi ảnh: {cell(payload['so_bien_trung_binh_moi_anh'], 2)}. "
            f"Hai cột **không thay thế được cho nhau** — chúng đo hai mô hình ở hai "
            f"độ phân giải khác nhau; cột baseline là **client-side warm p95 qua HTTP, "
            f"máy rảnh** (`07-benchmark-p1-resolved.json`), cột mô hình đang đánh giá là "
            f"in-process. Con số cũ **5.857,19 ms** từng ghi cho baseline **đã bị bác bỏ** "
            f"(nhiễm tải cạnh tranh + sai checkpoint + lỗi crop).")
    else:
        add(f"*(chưa đo)* — {payload.get('ly_do')}")
    add("")

    # ---------------- T5.7b ----------------
    add("## {{T5.7b}} Phân rã ngân sách độ trễ theo từng bước")
    add("")
    payload = store.get("T5.7b")
    if store.measured("T5.7b"):
        add("| Bước xử lý | Ước lượng Phase 0 (ms) | **Đo thật (ms)** | Chênh lệch (lần) | % tổng thời gian |")
        add("|---|---:|---:|---:|---:|")
        for key in PHASE0_BUDGET_MS:
            row = payload["buoc"][key]
            share = row["phan_tram_tong"]
            add(
                f"| {row['ten_buoc']} | {vn(row['uoc_luong_phase0_ms'], 0)} | "
                f"{cell(row['do_that_ms'], 2)} | {cell(row['chenh_lech_lan'], 2)} | "
                f"{EM_DASH if share is None else vn(share, 1) + '%'} |"
            )
        total = payload["tong"]
        add(f"| **Tổng (một biển số)** | **{vn(total['uoc_luong_phase0_ms'], 0)}** | "
            f"**{cell(total['do_that_ms'], 2)}** | **{cell(total['chenh_lech_lan'], 2)}** | **100%** |")
        add("")
        add(f"> Mẫu số: {vni(payload['so_mau'])} ảnh, trung bình "
            f"{cell(payload['so_bien_trung_binh_moi_anh'], 2)} biển mỗi ảnh. "
            f"{payload['ghi_chu']}")
    else:
        add(f"*(chưa đo)* — {payload.get('ly_do')}")
    add("")

    # ---------------- T5.7c ----------------
    add("## {{T5.7c}} So sánh backend suy luận")
    add("")
    payload = store.get("T5.7c")
    if store.measured("T5.7c"):
        add("| Backend | Độ trễ **chỉ bộ phát hiện** p50 (ms) | p95 (ms) | Tăng tốc so với PyTorch | Độ trễ **E2E** p95 (ms) | Cải thiện E2E (%) | mAP@0.5 sau khi xuất |")
        add("|---|---:|---:|---:|---:|---:|---:|")
        for name, row in payload["backend"].items():
            speedup = row.get("tang_toc_so_voi_pytorch")
            add(
                f"| {name} | {cell(row['p50_ms'], 2)} | {cell(row['p95_ms'], 2)} | "
                f"{'1,00×' if name == 'pytorch' else (EM_DASH if speedup is None else vn(speedup, 2) + '×')} | "
                f"{EM_DASH} | {EM_DASH} | {EM_DASH} |"
            )
        add("")
        add(f"> Cột E2E và mAP sau khi xuất **chưa đo**: {payload['backend'].get('pytorch', {}).get('map50_ly_do', '')}")
        add(">")
        add(f"> Tỉ trọng bộ phát hiện trong tổng thời gian: "
            f"{cell(payload['ty_trong_bo_phat_hien_phan_tram'], 1)}%. "
            f"{payload['ghi_chu_amdahl']}")
    else:
        add(f"*(chưa đo)* — {payload.get('ly_do')}")
    add("")

    # ---------------- T5.7d ----------------
    add("## {{T5.7d}} Webcam và xử lý video (NFR-P2, NFR-P3)")
    add("")
    payload = store.get("T5.7d")
    add(f"*(chưa đo)* — {payload.get('ly_do', 'chua chay')}")
    add("")

    # ---------------- T5.7e ----------------
    add("## {{T5.7e}} Chịu tải, bộ nhớ, độ tin cậy")
    add("")
    payload = store.get("T5.7e")
    add("| Chỉ số | Mã NFR | Ngưỡng tối thiểu | Mục tiêu | **Đo được** | Kết quả |")
    add("|---|:---:|---:|---:|---:|:---:|")
    prior = (payload.get("moc_da_do_truoc_do") or {}) if store.measured("T5.7e") else {
        "nfr_p4_nap_model_s": 6.41, "nfr_p4b_health_s": 8.36,
        "nfr_p5_api_overhead_p95_ms": 19.01, "nfr_p6_truy_van_10000_p95_ms": 18.71,
        "nfr_p7a_rss_pipeline_gb": 0.759, "nfr_p7b_rss_server_gb": 0.806,
    }
    add(f"| Thời gian nạp mô hình (giây) | NFR-P4 | ≤ 30 | ≤ 15 | {vn(prior['nfr_p4_nap_model_s'], 2)} *(baseline)* | ✅ đạt |")
    add(f"| Khởi động đến khi `/health` sẵn sàng (giây) | NFR-P4b | ≤ 30 | ≤ 15 | {vn(prior['nfr_p4b_health_s'], 2)} *(baseline)* | ✅ đạt |")
    add(f"| Overhead của API, p95 (ms) | NFR-P5 | ≤ 100 | ≤ 50 | {vn(prior['nfr_p5_api_overhead_p95_ms'], 2)} *(baseline)* | ✅ đạt |")
    add(f"| Truy vấn lịch sử 10.000 bản ghi, p95 (ms) | NFR-P6 | ≤ 1000 | ≤ 500 | {vn(prior['nfr_p6_truy_van_10000_p95_ms'], 2)} *(baseline)* | ✅ đạt |")
    add(f"| RSS pipeline (GB) | NFR-P7a | ≤ 4 | ≤ 2 | {vn(prior['nfr_p7a_rss_pipeline_gb'], 3)} *(baseline)* | ✅ đạt |")
    add(f"| RSS máy chủ backend (GB) | NFR-P7b | ≤ 4 | ≤ 2 | {vn(prior['nfr_p7b_rss_server_gb'], 3)} *(baseline)* | ✅ đạt |")
    if store.measured("T5.7e"):
        add(f"| Số yêu cầu đồng thời xử lý ổn định | NFR-SC1 | ≥ 5 | ≥ 5 | **{vni(payload['so_yeu_cau_dong_thoi_on_dinh'])}** | {verdict('NFR-SC1', payload['so_yeu_cau_dong_thoi_on_dinh'])} |")
        rate = payload.get("soak_ty_le_thanh_cong")
        add(f"| Tỉ lệ thành công soak 300 giây | NFR-R4 | ≥ 99% | ≥ 99% | **{EM_DASH if rate is None else vn(rate * 100, 1) + '%'} ({vni(payload['soak_so_yeu_cau'])} yêu cầu)** | {verdict('NFR-R4', rate)} |")
        add(f"| Tăng RSS sau soak (GB) | — | không có | không có | {cell(payload['soak_tang_rss_gb'], 3)} | n/a |")
        add(f"| Cơ sở dữ liệu sống sót qua khởi động lại | NFR-R5 | 100% | 100% | {EM_DASH} | ⬜ chưa đo |")
        add("")
    else:
        add(f"| Số yêu cầu đồng thời xử lý ổn định | NFR-SC1 | ≥ 5 | ≥ 5 | {EM_DASH} | ⬜ chưa đo |")
        add(f"| Tỉ lệ thành công soak 300 giây | NFR-R4 | ≥ 99% | ≥ 99% | 100% (185/185) *(baseline)* | ✅ đạt |")
        add(f"| Tăng RSS sau soak (GB) | — | không có | không có | {EM_DASH} | ⬜ chưa đo |")
        add(f"| Cơ sở dữ liệu sống sót qua khởi động lại | NFR-R5 | 100% | 100% | {EM_DASH} | ⬜ chưa đo |")
        add("")
        add(f"> ⚠ Phần chịu tải chưa chạy lại cho mô hình này: {payload.get('ly_do', '')}")
        add("")

    # ---------------- T5.8 ----------------
    add("## {{T5.8}} So sánh baseline 416/v1 với mô hình chính thức 640/v3")
    add("")
    payload = store.get("T5.8")
    base, off = payload["baseline_416_v1"], payload["chinh_thuc"]
    add("| Hạng mục | `baseline-416-v1.pt` | Mô hình đang đánh giá | Chênh lệch |")
    add("|---|---:|---:|---:|")
    add(f"| `imgsz` | {base['imgsz']} | **{off['imgsz']}** | +{off['imgsz'] - base['imgsz']} px |")
    add(f"| Bộ dữ liệu | {base['bo_du_lieu']} | **{off['bo_du_lieu']}** | ×3,3 |")
    add(f"| Ngưỡng gộp trùng lặp | {base['nguong_gop_trung_lap']} | **{off['nguong_gop_trung_lap']}** | +5 |")
    add(f"| Số epoch | {base['so_epoch']} | {vni(off['so_epoch'])} | — |")
    add(f"| mAP@0.5 | **{vn(base['map50'])}** *(epoch 38)* | **{cell(off['map50'])}** | {cell(None if off['map50'] is None else (off['map50'] - base['map50']))} |")
    add(f"| mAP@0.5:0.95 | **{vn(base['map5095'])}** *(epoch 38)* | **{cell(off['map5095'])}** | {cell(None if off['map5095'] is None else (off['map5095'] - base['map5095']))} |")
    add(f"| Precision | **{vn(base['precision'])}** | {cell(off['precision'])} | {cell(None if off['precision'] is None else (off['precision'] - base['precision']))} |")
    add(f"| Recall | **{vn(base['recall'])}** | {cell(off['recall'])} | {cell(None if off['recall'] is None else (off['recall'] - base['recall']))} |")
    add(f"| mAP biển một dòng | **{vn(base['map50_mot_dong'])}** | {cell(off['map50_mot_dong'])} | — |")
    add(f"| mAP biển hai dòng | **{vn(base['map50_hai_dong'])}** | {cell(off['map50_hai_dong'])} | — |")
    add(f"| Chênh lệch theo layout (điểm %) | **{vn(base['chenh_layout_diem_pt'], 1)}** | {cell(off['chenh_layout_diem_pt'], 2)} | — |")
    add(f"| Độ trễ E2E p95 (ms) | **{vn(base['do_tre_p95_ms'], 2)}** | {cell(off['do_tre_p95_ms'], 2)} | — |")
    add("")
    add(f"> ⚠ {payload['canh_bao_quy_ket']}")
    add(">")
    add("> Dòng độ trễ: cột baseline là client-side warm p95 qua HTTP trên máy rảnh "
        "(`07-benchmark-p1-resolved.json`); cột mô hình đang đánh giá là in-process (T5.7a). "
        "Con số cũ 5.857,19 ms từng ghi cho baseline đã bị **bác bỏ** "
        "(nhiễm tải cạnh tranh + sai checkpoint + lỗi crop).")
    add("")

    # ---------------- T5.9 ----------------
    add("## {{T5.9}} Đối chiếu chỉ tiêu NFR (phần đo được bằng script này)")
    add("")
    add("| Mã | Chỉ tiêu | Ngưỡng tối thiểu | Mục tiêu | **Đo được** | Kết quả |")
    add("|:---:|---|---:|---:|---:|:---:|")
    for row in store.get("T5.9").get("dong", []):
        code = row.get("nfr")
        floor, target = (NFR_TARGETS[code][0], NFR_TARGETS[code][1]) if code else (None, None)
        value = row.get("do_duoc")
        note = row.get("ghi_chu") or row.get("ly_do") or ""
        suffix = f" *({note})*" if note else ""
        add(
            f"| {row['ma']} | {row['chi_tieu']} | {cell(floor, 2)} | {cell(target, 2)} | "
            f"{cell(value)}{suffix} | {row['ket_qua']} |"
        )
    add("")

    # ---------------- T5.10 ----------------
    add("## {{T5.10}} Tần suất các loại lỗi")
    add("")
    payload = store.get("T5.10")
    if store.measured("T5.10"):
        add("| Mã | Loại lỗi | Số ca | Tỉ lệ trong tổng số ca sai | Tỉ lệ trong toàn tập đánh giá | Biển một dòng | Biển hai dòng |")
        add("|:---:|---|---:|---:|---:|---:|---:|")
        for code, row in payload["loai_loi"].items():
            count = row.get("so_ca")
            count_text = EM_DASH if count is None or count == NOT_MEASURED else vni(count)
            share_err = row.get("ty_le_trong_tong_ca_sai")
            share_all = row.get("ty_le_trong_toan_tap")
            add(
                f"| {code} | {row['ten']} | {count_text} | "
                f"{EM_DASH if share_err is None else vn(share_err * 100, 2) + '%'} | "
                f"{EM_DASH if share_all is None else vn(share_all * 100, 2) + '%'} | "
                f"{vni(row.get('mot_dong')) if row.get('mot_dong') is not None else EM_DASH} | "
                f"{vni(row.get('hai_dong')) if row.get('hai_dong') is not None else EM_DASH} |"
            )
        add(f"| | **Tổng số ca sai** | **{vni(payload['tong_so_ca_sai'])}** | 100% | "
            f"{EM_DASH if not payload['ty_le_loi'] else vn(payload['ty_le_loi'] * 100, 2) + '%'} | — | — |")
        add(f"| | **Tổng số ca đánh giá (mẫu số)** | **{vni(payload['tong_so_ca_danh_gia'])}** | n/a | 100% | — | — |")
        add("")
        other = payload["cac_loai_khac"]
        e1 = payload["loai_loi"]["E1"]
        add(f"> **Mẫu số của E1 khác mẫu số của E3–E6.** E1 lấy từ lượt đo E2E của "
            f"bảng T5.6e ({vni(e1.get('mau_so_rieng'))} mẫu), còn E3–E6 lấy từ lượt "
            f"đo trên vùng cắt ({vni(payload['tong_so_ca_danh_gia'])} mẫu). Hai cột "
            f"tỉ lệ vì vậy **cố ý để trống ở dòng E1** — gộp chung một mẫu số sẽ cho "
            f"ra con số vô nghĩa. Tỉ lệ E1 trên mẫu số riêng của nó: "
            f"{EM_DASH if e1.get('ty_le_tren_mau_so_rieng') is None else vn(e1['ty_le_tren_mau_so_rieng'] * 100, 2) + '%'}.")
        add(">")
        add(f"> E2 (phát hiện nhầm) để `—`: số dương tính giả nằm ở bảng T5.5a và "
            f"cũng không cùng mẫu số với E3–E6.")
        add(">")
        add(f"> Hai loại lỗi ngoài khung E1–E6: `empty_read` = {vni(other['empty_read'])}, "
            f"`mixed` = {vni(other['mixed'])}. {other['ghi_chu']}")
    else:
        add(f"*(chưa đo)* — {payload.get('ly_do')}")
    add("")

    add("---")
    add("")
    add("*Toàn bộ số liệu và lý do của các ô `—` nằm trong `docs/reports/05-results.json`.*")
    add("")
    return "\n".join(out)


# --------------------------------------------------------------------------- #
# Tom tat stdout
# --------------------------------------------------------------------------- #
def print_summary(store: ResultStore, meta: dict[str, Any]) -> None:
    """In bang tom tat NFR ra stdout.

    Args:
        store: Kho ket qua.
        meta: Khoi ngu canh do.
    """
    print()
    print("=" * 88)
    print("TOM TAT DOI CHIEU CHI TIEU NFR")
    print("=" * 88)
    print(
        f"CPU {meta.get('cpu_ten')} | {meta.get('so_nhan_vat_ly')} nhan / "
        f"{meta.get('so_nhan_logic')} luong | device=cpu | {meta.get('he_dieu_hanh')}"
    )
    print(f"Model: {meta.get('duong_dan_model')}")
    print(f"Dataset: {meta.get('dataset_yaml')} | split={meta.get('split')} | "
          f"{meta.get('so_anh_split')} anh")
    print("-" * 88)
    print(f"{'MA':<8}{'CHI TIEU':<44}{'DO DUOC':>16}{'KET QUA':>20}")
    print("-" * 88)
    for row in store.get("T5.9").get("dong", []):
        value = row.get("do_duoc")
        text = "—" if value is None else (f"{float(value):.4f}" if isinstance(value, (int, float)) else str(value))
        print(f"{row['ma']:<8}{row['chi_tieu'][:43]:<44}{text:>16}{row['ket_qua']:>20}")
    print("-" * 88)

    missing = [code for code in sorted(store.data) if code != "_meta" and not store.measured(code)]
    if missing:
        print(f"CAC BANG CHUA DO DUOC ({len(missing)}):")
        for code in missing:
            print(f"  {code:<8} {store.get(code).get('ly_do')}")
    else:
        print("Moi bang deu co so lieu.")
    print("=" * 88)
    print()


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def build_parser() -> argparse.ArgumentParser:
    """Dung bo phan tich doi so dong lenh.

    Returns:
        Parser da cau hinh.
    """
    parser = argparse.ArgumentParser(
        prog="python scripts/fill_chapter5.py",
        description=(
            "Chay toan bo phep do cua Chuong 5 va xuat so lieu theo dung ma bang "
            "cua docs/papers/ch5-thuc-nghiem.md."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Vi du:\n"
            "  python scripts/fill_chapter5.py --dry-run\n"
            "  python scripts/fill_chapter5.py --skip-slow\n"
            "  python scripts/fill_chapter5.py --weights models/best.pt\n"
        ),
    )
    parser.add_argument(
        "--weights",
        default=None,
        help=(
            "Duong dan mo hinh. Mac dinh models/best.pt; neu chua co thi lui ve "
            "models/baseline-416-v1.pt va ghi ro dieu do trong _meta."
        ),
    )
    parser.add_argument("--data", default=str(DEFAULT_DATA_YAML), help="Dataset yaml.")
    parser.add_argument(
        "--split", default="test", choices=("test", "val"), help="Split danh gia."
    )
    parser.add_argument("--imgsz", type=int, default=640, help="Kich thuoc anh suy luan.")
    parser.add_argument("--conf", type=float, default=0.25, help="Nguong confidence.")
    parser.add_argument(
        "--skip-slow",
        action="store_true",
        help="Bo qua cac phep do ton thoi gian (chiu tai, soak) va gioi han so mau.",
    )
    parser.add_argument(
        "--out-json",
        default=None,
        help=(
            "JSON ket qua. Mac dinh docs/reports/05-results.json; voi --skip-slow thi "
            "mac dinh doi sang docs/reports/05-smoke/ de luot chay thu khong ghi de "
            "len bao cao cong bo."
        ),
    )
    parser.add_argument(
        "--out-md",
        default=None,
        help="Doan markdown. Quy tac mac dinh giong --out-json.",
    )
    parser.add_argument(
        "--run-dir",
        default=str(PROJECT_ROOT / "runs" / "final-640-v3"),
        help="Thu muc luot huan luyen (doc results.csv cho bang T5.4b).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Chi in ra se do nhung gi, khong chay phep do nao.",
    )
    return parser


def resolve_weights(requested: str | None) -> tuple[Path, str | None]:
    """Chon trong so se dung, co co che lui ve baseline.

    Args:
        requested: Duong dan nguoi dung yeu cau, hoac ``None``.

    Returns:
        Cap ``(duong_dan, canh_bao)``; ``canh_bao`` khac ``None`` khi da phai lui.
    """
    if requested:
        path = Path(requested)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        return path, None
    if DEFAULT_WEIGHTS.exists():
        return DEFAULT_WEIGHTS, None
    return FALLBACK_WEIGHTS, (
        f"{DEFAULT_WEIGHTS} chua ton tai (luot huan luyen chua xong) nen da lui ve "
        f"{FALLBACK_WEIGHTS.name}. MOI SO TRONG BAO CAO NAY LA SO CUA BASELINE, "
        f"khong duoc dien vao cot 'best.pt' cua Chuong 5."
    )


def resolve_outputs(args: argparse.Namespace) -> tuple[Path, Path]:
    """Chon duong dan hai tep dau ra, co cach ly che do chay thu.

    Mot luot ``--skip-slow`` do tren rat it mau. Neu no ghi de len
    ``docs/reports/05-results.json`` va ``05-tables.md`` — hai tep dung de dien
    so vao Chuong 5 — thi so lieu rac se im lang thay cho so lieu that ma khong
    ai biet. Vi vay khi nguoi dung KHONG chi dinh duong dan tuong minh, che do
    chay thu ghi sang :data:`SMOKE_DIR`.

    Args:
        args: Doi so dong lenh da phan tich.

    Returns:
        Cap ``(out_json, out_md)``.
    """
    directory = SMOKE_DIR if args.skip_slow else PROJECT_ROOT / "docs" / "reports"
    out_json = (
        Path(args.out_json) if args.out_json else directory / DEFAULT_OUT_JSON.name
    )
    out_md = Path(args.out_md) if args.out_md else directory / DEFAULT_OUT_MD.name
    return out_json, out_md


def count_split_images(args: argparse.Namespace) -> int | None:
    """Dem so anh cua split se danh gia.

    Args:
        args: Doi so dong lenh.

    Returns:
        So anh, hoac ``None`` neu khong xac dinh duoc.
    """
    try:
        from ai.evaluation import evaluate as ev

        descriptor = ev.load_dataset_descriptor(Path(args.data))
        return len(ev.resolve_split_images(Path(args.data), descriptor, args.split))
    except Exception as error:  # noqa: BLE001
        LOGGER.warning("Khong dem duoc so anh split: %s", error)
        return None


def main(argv: Sequence[str] | None = None) -> int:
    """Diem vao dong lenh.

    Args:
        argv: Danh sach doi so; mac dinh ``sys.argv[1:]``.

    Returns:
        ``0`` khi chay xong (ke ca khi mot so phep do that bai — do la trang thai
        hop le va da duoc ghi vao bao cao), ``1`` khi khong the ghi dau ra.
    """
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stdout,
    )

    weights, fallback_warning = resolve_weights(args.weights)
    if fallback_warning:
        LOGGER.warning(fallback_warning)

    steps: list[tuple[str, str]] = [
        ("T5.2b", "phien ban thu vien cua moi truong dang chay"),
        ("T5.3b", f"ro ri train<->{args.split} o cac nguong Hamming {LEAK_THRESHOLDS}"),
        ("T5.3c", "phan bo nguon du lieu giua cac split (tu split_manifest.csv)"),
        ("T5.4b", f"duong cong huan luyen tu {args.run_dir}/results.csv"),
        ("T5.5a + T5.5b", f"detection tong the va tach theo layout ({weights.name}, split {args.split})"),
        ("T5.5c", "detection tach theo dai kich thuoc box (5 dai)"),
        ("T5.7a + T5.7b", "do tre E2E p50/p95/p99 va phan ra ngan sach tung buoc"),
        ("T5.7c", "so sanh PyTorch / ONNX / OpenVINO (neu tim thay ban xuat)"),
        ("T5.6a...T5.6e", "OCR: CER, chuoi truoc/sau hau xu ly, layout, ma tran nham lan, E2E"),
        ("T5.10", "phan loai loi E1...E6"),
        ("T5.7e", "chiu tai va soak 300 giay" + (" — SE BI BO QUA (--skip-slow)" if args.skip_slow else "")),
        ("T5.8 + T5.9", "tong hop so sanh va doi chieu NFR"),
    ]

    if args.dry_run:
        print()
        print("DRY RUN — se thuc hien cac phep do sau, khong chay gi:")
        print(f"  trong so      : {weights} (ton tai: {weights.exists()})")
        if fallback_warning:
            print(f"  CANH BAO      : {fallback_warning}")
        print(f"  dataset       : {args.data}")
        print(f"  split         : {args.split} ({count_split_images(args)} anh)")
        print(f"  imgsz         : {args.imgsz}")
        print(f"  nhan chuoi OCR: {find_label_file() or 'KHONG TIM THAY — NFR-A4...A7 se ghi chua do'}")
        print(f"  ban xuat      : {find_exports(weights) or 'KHONG CO — T5.7c se ghi chua do'}")
        print(f"  skip-slow     : {args.skip_slow}")
        dry_json, dry_md = resolve_outputs(args)
        print(f"  out-json      : {dry_json}")
        print(f"  out-md        : {dry_md}")
        if args.skip_slow:
            print("  LUU Y         : --skip-slow ghi vao thu muc chay thu, KHONG ghi de "
                  "len bao cao cong bo")
        print()
        for code, what in steps:
            print(f"  [{code:<14}] {what}")
        print()
        return 0

    store = ResultStore()
    started = time.perf_counter()

    num_images = count_split_images(args)
    meta = collect_meta(args, weights, num_images)
    if fallback_warning:
        meta["canh_bao_trong_so"] = fallback_warning

    if not weights.exists():
        LOGGER.error("Khong tim thay trong so %s — moi phep do phu thuoc no se ghi 'chua do'", weights)

    # Cac buoc doc lap: mot buoc that bai khong duoc chan cac buoc con lai.
    tasks: list[tuple[str, Callable[[], None]]] = [
        ("T5.2b", lambda: collect_library_versions(store)),
        ("T5.3b", lambda: measure_leakage(args, store)),
        ("T5.3c", lambda: measure_source_distribution(args, store)),
        ("T5.4b", lambda: collect_training_curve(store, Path(args.run_dir))),
        ("T5.5a/b", lambda: measure_detection(args, weights, store)),
        ("T5.5c", lambda: measure_size_bands(args, weights, store)),
        ("T5.7a/b", lambda: measure_latency(args, weights, store)),
        ("T5.7c", lambda: measure_backends(args, weights, store)),
    ]
    ocr_report: Path | None = None
    for label, task in tasks:
        try:
            task()
        except Exception as error:  # noqa: BLE001 - mot buoc hong khong duoc lam sap ca script
            LOGGER.exception("Buoc %s that bai ngoai du kien: %s", label, error)

    try:
        ocr_report = measure_ocr(args, weights, store)
    except Exception as error:  # noqa: BLE001
        LOGGER.exception("Buoc OCR that bai ngoai du kien: %s", error)
        for code in ("T5.6a", "T5.6b", "T5.6c", "T5.6d", "T5.6e"):
            if code not in store.data:
                store.skip(code, f"ngoai le khong bat truoc: {error!r}")

    for label, task in (
        ("T5.10", lambda: measure_errors(args, ocr_report, store)),
        ("T5.7e", lambda: measure_stress(args, weights, store)),
    ):
        try:
            task()
        except Exception as error:  # noqa: BLE001
            LOGGER.exception("Buoc %s that bai ngoai du kien: %s", label, error)

    store.skip(
        "T5.7d",
        "chua co kich ban do webcam/video. Muc D.3 cua ch5-thuc-nghiem.md ghi day la "
        "hang muc can viet ma, va khi viet phai kem dinh nghia tuong minh cua "
        "'FPS hieu dung' (khung hinh duoc NHAN DANG moi giay hay khung hinh duoc "
        "HIEN THI moi giay).",
    )
    build_comparison(store, weights)
    build_nfr_summary(store)

    meta["thoi_gian_chay_giay"] = round(time.perf_counter() - started, 1)
    store.data["_meta"] = meta

    out_json, out_md = resolve_outputs(args)
    try:
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(
            json.dumps(store.data, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )
        LOGGER.info("Da ghi JSON: %s", out_json)
        out_md.parent.mkdir(parents=True, exist_ok=True)
        out_md.write_text(render_markdown(store, meta), encoding="utf-8")
        LOGGER.info("Da ghi Markdown: %s", out_md)
    except OSError as error:
        LOGGER.error("Khong ghi duoc dau ra: %s", error)
        return 1

    print_summary(store, meta)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
