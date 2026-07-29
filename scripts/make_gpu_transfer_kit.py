"""Gói mọi thứ cần thiết để fine-tune trên một máy GPU khác, rồi chỉ chép model về.

Vì sao cần gói riêng
--------------------
Máy GPU mượn thường không có kho mã, không có venv của dự án, và không nên có —
chép nguyên kho mã sang chỉ để chạy huấn luyện là mang theo cả backend, frontend
và 180 MB tài liệu cho một việc chỉ cần ba thứ: dữ liệu, trọng số gốc, và một
kịch bản. Bộ này gom đúng ba thứ đó cộng hướng dẫn, chạy độc lập.

Kịch bản trong bộ **không import gì từ kho mã**. Nó tự dựng venv, tự tải
PaddleOCR, và mang theo mọi chốt chặn mà dự án đã học được bằng cách hỏng
thật:

* kiểm ``is_compiled_with_cuda()`` **trước** khi huấn luyện — một lượt chạy
  trên Colab từng chết bằng ``AttributeError`` khó hiểu ở
  ``tools/program.py`` dòng 971 chỉ vì paddle cài nhầm bản CPU;
* stream log ra màn hình **và** ra tệp — cùng lượt chạy đó chỉ hiện đúng một
  con số ``1``, không một dòng lỗi nào, vì ``subprocess.run`` không bắt output;
* kiểm kích thước trọng số tải về — một lần tải hỏng từng trả tệp JSON 117
  byte mang đuôi ``.pdparams``;
* in nghi thức đo bắt buộc khi kết thúc — một lần fine-tune từng cho ra model
  đọc rác 0/7 ảnh demo mà chỉ lộ ra ở bước đo cuối cùng
  (``docs/reports/25-finetune-attempt-failed.md``).

Chạy::

    backend/.venv/Scripts/python scripts/make_gpu_transfer_kit.py

Bộ sinh ra nằm ngoài phạm vi theo dõi của git (~120 MB) — nó là bản chép của
dữ liệu đã có trong kho, không phải nguồn.
"""

from __future__ import annotations

import argparse
import shutil
import sys
import zipfile
from pathlib import Path

# Console Windows mặc định cp1252, không in được dấu tiếng Việt. Thiếu dòng này
# thì chính `--help` tự vỡ bằng UnicodeEncodeError — hỏng ở đúng chỗ người dùng
# tìm đến khi chưa biết dùng script thế nào.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

REPO_ROOT: Path = Path(__file__).resolve().parents[1]
DATA_DIR: Path = REPO_ROOT / "datasets" / "processed" / "rec_finetune"
PRETRAINED: Path = (
    REPO_ROOT / "models" / "pretrained" / "en_PP-OCRv5_mobile_rec_pretrained.pdparams"
)
YOLO_DATA: Path = REPO_ROOT / "datasets" / "processed" / "yolo_v3"
DEFAULT_OUT: Path = REPO_ROOT / "transfer-gpu-finetune"

MIN_WEIGHT_BYTES: int = 10_000_000
"""Dưới ngưỡng này thì tệp trọng số là rác, không phải trọng số."""

_INCOMPRESSIBLE: frozenset[str] = frozenset(
    {".jpg", ".jpeg", ".png", ".webp", ".mp4", ".zip", ".gz"}
)
"""Định dạng đã nén sẵn — nén lại chỉ tốn CPU, không giảm được kích thước."""


# ---------------------------------------------------------------------------
# Nội dung kịch bản huấn luyện đi kèm bộ
# ---------------------------------------------------------------------------

TRAIN_SCRIPT = '''#!/usr/bin/env python3
"""Fine-tune PP-OCRv5 mobile rec trên máy có GPU. Chạy ĐỘC LẬP, không cần kho mã.

Đặt tệp này cùng cấp với thư mục ``data/`` và ``pretrained/`` rồi chạy:

    python train_gpu.py --smoke     # thử dây chuyền, vài phút
    python train_gpu.py             # lượt thật

Xong thì chép thư mục ``rec_finetuned/`` về máy chính. Xem README.md.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
PRETRAINED = HERE / "pretrained" / "en_PP-OCRv5_mobile_rec_pretrained.pdparams"
WORK = HERE / "work"
OUTPUT = WORK / "output" / "rec_vn"
EXPORT = HERE / "rec_finetuned"
LOGS = HERE / "logs"

PADDLEOCR_REPO = "https://github.com/PaddlePaddle/PaddleOCR.git"
CONFIG_REL = "configs/rec/PP-OCRv5/multi_language/en_PP-OCRv5_mobile_rec.yaml"

# Bản GPU 3.x CHỈ có trên index của Paddle. Thiếu cờ -i thì pip tìm PyPI và
# dừng ở 2.6.2 — một bản quá cũ cho cấu hình PP-OCRv5.
PADDLE_GPU_INDEX = "https://www.paddlepaddle.org.cn/packages/stable/cu126/"


def run(args, cwd=None, log_name=None):
    """Chạy lệnh, in log ra màn hình VÀ ghi ra tệp."""
    printable = " ".join(str(a) for a in args)
    print(f"\\n$ {printable}", flush=True)

    handle = None
    if log_name:
        LOGS.mkdir(parents=True, exist_ok=True)
        handle = (LOGS / f"{log_name}.log").open("w", encoding="utf-8", errors="replace")

    env = {**os.environ, "PYTHONUNBUFFERED": "1"}
    try:
        proc = subprocess.Popen(
            [str(a) for a in args],
            cwd=str(cwd) if cwd else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            errors="replace",
            env=env,
        )
        for line in proc.stdout:
            line = line.rstrip("\\n")
            print(line, flush=True)
            if handle:
                handle.write(line + "\\n")
        code = proc.wait()
    finally:
        if handle:
            handle.close()

    if code != 0:
        print(f"\\n>> THẤT BẠI — mã thoát {code}", flush=True)
        if log_name:
            print(f">> Log đầy đủ: {LOGS / (log_name + '.log')}", flush=True)
    return code


def venv_python() -> Path:
    """Dựng venv riêng và cài paddle bản GPU."""
    py = WORK / "venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if py.exists():
        return py

    print("=== Dựng venv và cài paddlepaddle-gpu ===")
    WORK.mkdir(parents=True, exist_ok=True)
    run([sys.executable, "-m", "venv", str(WORK / "venv")])
    run([py, "-m", "pip", "install", "-q", "--upgrade", "pip"])
    run([
        py, "-m", "pip", "install", "-q", "--timeout", "300", "--retries", "8",
        "paddlepaddle-gpu==3.3.1", "-i", PADDLE_GPU_INDEX,
    ])
    run([py, "-m", "pip", "install", "-q", "opencv-python", "numpy"])
    return py


def require_cuda(py: Path) -> None:
    """Dừng lại nếu paddle không phải bản CUDA.

    Đây là chốt chặn quan trọng nhất của tệp này. Bản CPU của paddle vẫn cài
    được trên máy có GPU và vẫn chạy bình thường — cho tới khi PaddleOCR hỏi
    tới device id, lúc đó nó vỡ bằng::

        AttributeError: 'ParallelEnv' object has no attribute '_device_id'

    một thông báo không nhắc một chữ nào về GPU, nên người đọc đi tìm lỗi ở
    cấu hình và mất hàng giờ. Hỏi thẳng ngay từ đầu thì rẻ hơn nhiều.
    """
    out = subprocess.run(
        [str(py), "-c",
         "import paddle;from paddle.base import core;"
         "print(paddle.__version__, core.is_compiled_with_cuda())"],
        capture_output=True, text=True,
    )
    print(out.stdout.strip() or out.stderr.strip())
    if "True" not in out.stdout:
        raise SystemExit(
            "\\nDỪNG: paddle đã cài KHÔNG phải bản CUDA.\\n"
            "  • Kiểm tra máy có GPU NVIDIA:  nvidia-smi\\n"
            "  • Xoá venv rồi chạy lại:       rmdir /s work\\\\venv   (Windows)\\n"
            "                                 rm -rf work/venv       (Linux)\\n"
            "Chạy tiếp bằng bản CPU sẽ hỏng ở tools/program.py dòng 971."
        )


def check_data() -> None:
    """Kiểm dữ liệu có mặt và không rỗng."""
    train, val = DATA / "train.txt", DATA / "val.txt"
    if not train.exists() or not val.exists():
        raise SystemExit(f"DỪNG: thiếu train.txt/val.txt trong {DATA}")
    n_train = sum(1 for _ in train.open(encoding="utf-8"))
    n_val = sum(1 for _ in val.open(encoding="utf-8"))
    n_img = len(list((DATA / "images").glob("*.jpg")))
    print(f"Dữ liệu: {n_train} dòng train · {n_val} dòng val · {n_img} ảnh")
    if n_train < 1000 or n_img < 1000:
        raise SystemExit(
            "DỪNG: dữ liệu quá ít, nhiều khả năng chép thiếu. "
            "Mong đợi ~6672 dòng train và ~7243 ảnh."
        )


def check_weights() -> None:
    """Kiểm trọng số gốc là tệp thật, không phải trang lỗi."""
    if not PRETRAINED.exists():
        raise SystemExit(f"DỪNG: thiếu {PRETRAINED}")
    size = PRETRAINED.stat().st_size
    if size < 10_000_000:
        raise SystemExit(
            f"DỪNG: trọng số chỉ {size} byte — không phải tệp trọng số. "
            "Chép lại từ máy chính."
        )
    print(f"Trọng số gốc: {size / 1e6:.1f} MB")


def ensure_paddleocr(py: Path) -> Path:
    """Tải mã nguồn PaddleOCR và cài phụ thuộc."""
    d = WORK / "PaddleOCR"
    if not d.exists():
        run(["git", "clone", "--depth", "1", PADDLEOCR_REPO, str(d)])
        run([py, "-m", "pip", "install", "-q", "-r", str(d / "requirements.txt")])
    cfg = d / CONFIG_REL
    if not cfg.exists():
        raise SystemExit(f"DỪNG: không thấy cấu hình {CONFIG_REL} trong bản vừa tải.")
    return cfg


def main() -> int:
    ap = argparse.ArgumentParser(description="Fine-tune PP-OCRv5 rec trên GPU.")
    ap.add_argument("--epochs", type=int, default=70)
    ap.add_argument("--batch-size", type=int, default=128)
    ap.add_argument("--lr", type=float, default=0.0001)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--smoke", action="store_true",
                    help="1 epoch, batch nhỏ — chứng minh dây chuyền thông.")
    ap.add_argument("--export-only", action="store_true")
    args = ap.parse_args()

    epochs = 1 if args.smoke else args.epochs
    batch = 16 if args.smoke else args.batch_size

    print("=" * 70)
    print("  FINE-TUNE PP-OCRv5 rec — máy GPU")
    print("=" * 70)
    print(f"  Chế độ  : {'THỬ DÂY CHUYỀN' if args.smoke else 'HUẤN LUYỆN THẬT'}")
    print(f"  Epochs  : {epochs} · batch {batch} · lr {args.lr}")
    print("=" * 70)

    py = venv_python()
    require_cuda(py)
    check_data()
    check_weights()
    cfg = ensure_paddleocr(py)
    ocr_dir = WORK / "PaddleOCR"

    common = [
        "Global.use_gpu=true",
        f"Global.character_dict_path={(DATA / 'dict36.txt').as_posix()}",
        "Global.use_space_char=false",
        "Global.max_text_length=10",
        f"Eval.dataset.data_dir={DATA.as_posix()}",
        f"Eval.dataset.label_file_list=[{(DATA / 'val.txt').as_posix()}]",
        f"Eval.loader.batch_size_per_card={batch}",
        f"Eval.loader.num_workers={args.workers}",
    ]

    if not args.export_only:
        opts = [
            *common,
            f"Global.epoch_num={epochs}",
            "Global.save_epoch_step=1",
            "Global.eval_batch_step=[0,200]",
            "Global.print_batch_step=20",
            f"Global.save_model_dir={OUTPUT.as_posix()}",
            f"Optimizer.lr.learning_rate={args.lr}",
            "Optimizer.lr.warmup_epoch=1",
            f"Train.dataset.data_dir={DATA.as_posix()}",
            f"Train.dataset.label_file_list=[{(DATA / 'train.txt').as_posix()}]",
            f"Train.sampler.first_bs={batch}",
            f"Train.loader.batch_size_per_card={batch}",
            f"Train.loader.num_workers={args.workers}",
        ]
        latest = OUTPUT / "latest.pdparams"
        if latest.exists():
            print(f">> Nối tiếp checkpoint: {latest}")
            opts.insert(0, f"Global.checkpoints={(OUTPUT / 'latest').as_posix()}")
        else:
            opts.insert(0,
                f"Global.pretrained_model={PRETRAINED.as_posix()[:-len('.pdparams')]}")

        if run([py, "tools/train.py", "-c", str(cfg), "-o", *opts],
               cwd=ocr_dir, log_name="train") != 0:
            return 1

    if args.smoke:
        print("\\nDây chuyền thông. Chạy lượt thật:  python train_gpu.py")
        return 0

    best = OUTPUT / "best_accuracy"
    if not best.with_suffix(".pdparams").exists():
        print("\\nKhông có best_accuracy — chưa đủ bước để chấm điểm.")
        return 1

    print("\\n=== ĐÁNH GIÁ ===")
    run([py, "tools/eval.py", "-c", str(cfg), "-o", *common,
         f"Global.checkpoints={best.as_posix()}"], cwd=ocr_dir, log_name="eval")

    print("\\n=== XUẤT MODEL ===")
    EXPORT.mkdir(parents=True, exist_ok=True)
    run([py, "tools/export_model.py", "-c", str(cfg), "-o", *common,
         f"Global.checkpoints={best.as_posix()}",
         f"Global.save_inference_dir={EXPORT.as_posix()}"],
        cwd=ocr_dir, log_name="export")
    shutil.copy2(DATA / "dict36.txt", EXPORT / "dict36.txt")

    print("\\n" + "=" * 70)
    print("  XONG. Chép về máy chính ĐÚNG HAI THỨ:")
    print("=" * 70)
    print(f"  1. thư mục  rec_finetuned/     ({EXPORT})")
    print("  2. thư mục  logs/              (để đối chiếu khi cần)")
    print()
    print("  KHÔNG cần chép work/ — đó là venv và checkpoint, hàng GB.")
    print()
    print("  Model này CHƯA ĐƯỢC BẬT cho tới khi qua nghi thức đo.")
    print("  Xem README.md mục 4.")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


YOLO_SCRIPT = '''#!/usr/bin/env python3
"""Huấn luyện lại bộ phát hiện YOLO11n trên GPU. Chạy ĐỘC LẬP, không cần kho mã.

Đặt tệp này cùng cấp với thư mục ``yolo/`` rồi chạy:

    python train_yolo.py --smoke    # 2 epoch, chứng minh dây chuyền thông
    python train_yolo.py            # lượt thật

Vì sao huấn luyện lại
---------------------
Bộ trọng số hiện hành ``best.pt`` được huấn luyện **trên CPU** hết 10,1 giờ,
20 epoch. Đường cong của lượt đó:

    epoch  1   mAP50 0,9684   mAP50-95 0,6526
    epoch 10   mAP50 0,9808   mAP50-95 0,7248
    epoch 12   mAP50 0,9854   mAP50-95 0,7219   <- dinh mAP50
    epoch 20   mAP50 0,9830   mAP50-95 0,7688   <- van con nhich

``mAP50`` đã bão hoà từ khoảng epoch 10, nên **không kỳ vọng nó tăng**.
``mAP50-95`` thì vẫn đang lên khi lượt cũ dừng — đó là chỗ duy nhất còn dư
địa, và cũng là chỉ số đo **độ khít của khung bao**. Khung khít hơn cho vùng
cắt sạch hơn, mà vùng cắt là đầu vào của bộ đọc chữ.

Lượt này chạy **100 epoch với early stopping** thay vì 20, vì trên GPU mỗi
epoch chỉ vài chục giây thay vì 30 phút. Giữ nguyên ``yolo11n``: đổi sang
model lớn hơn sẽ phá vỡ lập luận trung tâm của đồ án là suy luận chạy được
trên CPU.

Kết quả CHỈ được thay thế ``best.pt`` sau khi đo lại và chứng minh không thua
bộ hiện hành. Xem README.md.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
YOLO_DIR = HERE / "yolo"
WORK = HERE / "work-yolo"
EXPORT = HERE / "yolo_retrained"

# Bộ số của lượt huấn luyện hiện hành, để so ngay tại chỗ.
BASELINE = {"mAP50": 0.9829, "mAP50-95": 0.7834, "P": 0.9837, "R": 0.9714}


def sh(args, cwd=None):
    """Chạy lệnh, hiện log ngay."""
    print("\\n$ " + " ".join(str(a) for a in args), flush=True)
    return subprocess.run([str(a) for a in args], cwd=str(cwd) if cwd else None).returncode


def venv_python() -> Path:
    """Dựng venv và cài ultralytics + torch bản CUDA."""
    py = WORK / "venv" / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    if py.exists():
        return py
    print("=== Dựng venv và cài ultralytics ===")
    WORK.mkdir(parents=True, exist_ok=True)
    sh([sys.executable, "-m", "venv", str(WORK / "venv")])
    sh([py, "-m", "pip", "install", "-q", "--upgrade", "pip"])
    # torch bản CUDA phải lấy từ index riêng của PyTorch. Cài ultralytics trước
    # sẽ kéo về torch bản CPU, và lượt "huấn luyện GPU" lặng lẽ chạy trên CPU.
    sh([py, "-m", "pip", "install", "-q", "torch", "torchvision",
        "--index-url", "https://download.pytorch.org/whl/cu124"])
    sh([py, "-m", "pip", "install", "-q", "ultralytics==8.4.101"])
    return py


def require_cuda(py: Path) -> None:
    """Dừng nếu torch không thấy GPU.

    Cùng một cái bẫy như phía paddle: torch bản CPU cài được trên máy có GPU và
    vẫn chạy, chỉ là chậm gấp hàng chục lần. Ultralytics khi đó âm thầm lùi về
    CPU và người dùng đợi 10 giờ mà tưởng đang chạy GPU.
    """
    out = subprocess.run(
        [str(py), "-c",
         "import torch;print(torch.__version__, torch.cuda.is_available(),"
         "torch.cuda.get_device_name(0) if torch.cuda.is_available() else '')"],
        capture_output=True, text=True,
    )
    print(out.stdout.strip() or out.stderr.strip())
    if "True" not in out.stdout:
        raise SystemExit(
            "\\nDỪNG: torch KHÔNG thấy GPU.\\n"
            "  • Kiểm tra:      nvidia-smi\\n"
            "  • Xoá venv rồi chạy lại để cài lại torch bản CUDA.\\n"
            "Chạy tiếp sẽ rơi về CPU và mất hàng giờ mà không ai báo."
        )


def write_data_yaml() -> Path:
    """Viết lại data.yaml với đường dẫn của MÁY NÀY.

    Tệp gốc trong kho mã ghi đường dẫn tuyệt đối kiểu ``D:/DATN/...``. Chép
    nguyên sang máy khác thì Ultralytics đi tìm một thư mục không tồn tại, và
    thông báo lỗi của nó không nói rõ nguyên nhân là đường dẫn.
    """
    path = YOLO_DIR / "data.yaml"
    path.write_text(
        "# Sinh lai boi train_yolo.py cho may nay.\\n"
        f"path: {YOLO_DIR.as_posix()}\\n"
        "train: images/train\\n"
        "val: images/val\\n"
        "test: images/test\\n"
        "\\n"
        "nc: 1\\n"
        "names:\\n"
        "  0: license_plate\\n",
        encoding="utf-8",
    )
    return path


def count_split(name: str) -> int:
    """Đếm ảnh trong một phân tách."""
    d = YOLO_DIR / "images" / name
    return sum(1 for _ in d.glob("*")) if d.is_dir() else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Huấn luyện lại YOLO11n trên GPU.")
    ap.add_argument("--epochs", type=int, default=100)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--patience", type=int, default=25)
    ap.add_argument("--smoke", action="store_true", help="2 epoch, chứng minh dây chuyền.")
    args = ap.parse_args()

    epochs = 2 if args.smoke else args.epochs

    n_train, n_val, n_test = count_split("train"), count_split("val"), count_split("test")
    print("=" * 70)
    print("  HUẤN LUYỆN LẠI YOLO11n — máy GPU")
    print("=" * 70)
    print(f"  Dữ liệu : {n_train} train · {n_val} val · {n_test} test")
    print(f"  Cấu hình: {epochs} epoch · batch {args.batch} · imgsz {args.imgsz}"
          f" · patience {args.patience}")
    print(f"  Mốc phải vượt: mAP50 {BASELINE['mAP50']} · mAP50-95 {BASELINE['mAP50-95']}")
    print("=" * 70)

    if n_train < 1000:
        raise SystemExit(f"DỪNG: chỉ thấy {n_train} ảnh train — chép thiếu dữ liệu.")

    py = venv_python()
    require_cuda(py)
    data_yaml = write_data_yaml()

    # Giữ nguyên seed và deterministic của lượt cũ để so sánh có nghĩa.
    # AMP bật: lượt cũ tắt vì chạy CPU, trên GPU nó nhanh hơn nhiều và không
    # làm giảm mAP với mô hình cỡ nano.
    code = sh([
        py, "-m", "ultralytics", "cfg=", "task=detect", "mode=train",
        "model=yolo11n.pt", f"data={data_yaml.as_posix()}",
        f"epochs={epochs}", f"batch={args.batch}", f"imgsz={args.imgsz}",
        f"patience={args.patience}",
        "seed=42", "deterministic=True", "amp=True", "workers=8",
        f"project={(WORK / 'runs').as_posix()}", "name=gpu-retrain", "exist_ok=True",
    ])
    if code != 0:
        # Ultralytics đổi cách gọi CLI giữa các bản; thử đường Python API.
        print("\\n>> Thử lại bằng Python API...")
        script = WORK / "_train.py"
        script.write_text(
            "from ultralytics import YOLO\\n"
            "m = YOLO('yolo11n.pt')\\n"
            f"m.train(data=r'{data_yaml.as_posix()}', epochs={epochs},"
            f" batch={args.batch}, imgsz={args.imgsz}, patience={args.patience},"
            f" seed=42, deterministic=True, amp=True, workers=8,"
            f" project=r'{(WORK / 'runs').as_posix()}', name='gpu-retrain', exist_ok=True)\\n",
            encoding="utf-8",
        )
        code = sh([py, str(script)])
        if code != 0:
            return code

    weights = WORK / "runs" / "gpu-retrain" / "weights" / "best.pt"
    if not weights.exists():
        print(f"Không thấy trọng số tại {weights}")
        return 1

    print("\\n=== ĐÁNH GIÁ trên tập TEST ===")
    ev = WORK / "_eval.py"
    ev.write_text(
        "from ultralytics import YOLO\\n"
        f"m = YOLO(r'{weights.as_posix()}')\\n"
        f"r = m.val(data=r'{data_yaml.as_posix()}', split='test', imgsz={args.imgsz})\\n"
        "print('KET QUA TEST')\\n"
        "print('  mAP50   :', round(float(r.box.map50), 4))\\n"
        "print('  mAP50-95:', round(float(r.box.map), 4))\\n"
        "print('  P       :', round(float(r.box.mp), 4))\\n"
        "print('  R       :', round(float(r.box.mr), 4))\\n",
        encoding="utf-8",
    )
    sh([py, str(ev)])

    EXPORT.mkdir(parents=True, exist_ok=True)
    for name in ("best.pt", "last.pt"):
        src = weights.parent / name
        if src.exists():
            shutil.copy2(src, EXPORT / name)
    results = weights.parent.parent / "results.csv"
    if results.exists():
        shutil.copy2(results, EXPORT / "results.csv")
    args_yaml = weights.parent.parent / "args.yaml"
    if args_yaml.exists():
        shutil.copy2(args_yaml, EXPORT / "args.yaml")

    print("\\n" + "=" * 70)
    print("  XONG. Chép về máy chính thư mục:  yolo_retrained/")
    print("=" * 70)
    print("  Trong đó best.pt là ứng viên, results.csv là đường cong,")
    print("  args.yaml là bằng chứng lượt này chạy trên GPU.")
    print()
    print("  CHƯA thay thế models/best.pt cho tới khi đo lại và chứng minh")
    print(f"  không thua mốc hiện hành: mAP50 {BASELINE['mAP50']}"
          f" · mAP50-95 {BASELINE['mAP50-95']}")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


README = """# Bộ fine-tune trên máy GPU

Gói này chứa **đủ mọi thứ** để fine-tune bộ nhận dạng ký tự trên một máy có
GPU NVIDIA. Không cần kho mã của đồ án, không cần cài gì trước.

## 0. Vì sao cần chạy trên GPU

Lượt chạy trên CPU trước đó dừng ở **epoch 5**. Đường cong thật, đọc từ các
tệp `.states` của từng epoch:

| Epoch | Bước | `acc` | `norm_edit_dis` |
|---|---|---|---|
| 1 | 146 | 0,0000 | — |
| 2 | 292 | 0,0000 | 0,3681 |
| 3 | 438 | 0,0000 | 0,5706 |
| 4 | 584 | 0,0000 | 0,5706 |
| **5** | 600 | **0,1660** | **0,8114** |

`acc` nằm im ở **0 suốt bốn epoch** rồi mới bật lên ở epoch 5. Đó là hình dạng
kinh điển của bài toán đọc chuỗi: `norm_edit_dis` đo ở **mức ký tự** nên leo
đều ngay từ đầu, còn `acc` đòi **mọi ký tự trong chuỗi 8–9 ký tự đều đúng**
nên nó bám sát 0 cho tới khi độ chính xác ký tự vượt một ngưỡng, rồi mới vọt.

Nghĩa là lượt CPU dừng **đúng vào lúc mô hình vừa bắt đầu học được**. Kết quả
kém là vì **thiếu epoch**, không phải vì fine-tune sai hướng.

### Nên chạy bao nhiêu epoch

**Đặt 60–80.** Lý do không phải cảm tính:

* `acc` mới rời 0 ở epoch 5, tức 5 epoch còn chưa qua giai đoạn khởi động;
* `norm_edit_dis` ở 0,81 nghĩa là vẫn còn ~19% ký tự sai — còn xa mới bão hoà;
* để thắng được model gốc thì cần với tới vùng **0,75** ở thang A6, một quãng
  rất dài so với 0,166.

**Đặt cao không có rủi ro.** `Global.save_epoch_step=1` cộng cơ chế
`best_accuracy` nghĩa là PaddleOCR **tự giữ lại checkpoint tốt nhất**; chạy
thừa epoch chỉ tốn thời gian GPU, không bao giờ làm xấu kết quả cuối. Ngược
lại, đặt thiếu thì mất hẳn phần chưa học tới.

Cách đọc lúc chạy: theo dõi dòng `cur metric, acc:`. Khi `acc` **không nhích
lên trong khoảng 10 epoch liên tiếp** thì coi như đã bão hoà, dừng được.

Trên GPU mỗi epoch chỉ khoảng một đến hai phút, nên 60–80 epoch mất cỡ **một
đến hai giờ** — so với hàng ngày trời trên CPU.

## 1. Yêu cầu máy GPU

- GPU NVIDIA có CUDA (kiểm bằng `nvidia-smi`)
- Python **3.10 – 3.13**
- `git` trên PATH
- ~15 GB trống (venv, mã nguồn PaddleOCR, checkpoint)

## 2. Chạy

```bash
# Bước 1 — LUÔN chạy trước, mất vài phút, chứng minh cả dây chuyền thông
python train_gpu.py --smoke

# Bước 2 — lượt thật
python train_gpu.py
```

Kịch bản tự dựng venv, tự cài `paddlepaddle-gpu`, tự tải mã nguồn PaddleOCR.

Muốn đổi tham số:

```bash
python train_gpu.py --epochs 80 --batch-size 256
```

> **Đừng bỏ qua `--smoke`.** Nó tồn tại vì một lượt chạy trước đây hỏng ngay ở
> vòng lặp đầu tiên nhưng chỉ hiện đúng một con số `1` — không một dòng lỗi
> nào — và chuyện đó chỉ phát hiện sau khi đã chờ rất lâu.

## 3. Chép gì về máy chính

Sau khi xong, **chỉ chép hai thư mục**:

| Thư mục | Chép về đâu | Dung lượng |
|---|---|---|
| `rec_finetuned/` | `models/rec_finetuned/` trong kho mã | ~8 MB |
| `logs/` | bất kỳ đâu, để đối chiếu | vài MB |

**Không chép `work/`** — đó là venv, mã nguồn PaddleOCR và checkpoint, hàng GB,
và máy chính không cần.

## 4. Bật model — CHƯA được bật ngay

Chép về rồi vẫn **chưa** bật. Một lần fine-tune trước đây cho ra model đọc rác
**0/7** ảnh demo, và chuyện đó chỉ lộ ra ở bước đo cuối cùng. Nghi thức đo là
bắt buộc:

```bash
# 1. Đo A4-A7 toàn tập, so với bộ số hiện hành
backend/.venv/Scripts/python -m ai.evaluation.ocr_accuracy \\
  --labels datasets/annotations/plate_text_labels_vn.csv \\
  --detector models/best.pt --detector-imgsz 640 \\
  --output docs/reports/28-ocr-accuracy-finetuned.json

# 2. So với bộ số hiện hành: docs/reports/27-ocr-accuracy-with-ladder.json
#    ĐẠT = A6 biển 2 dòng tăng >= 5 điểm VÀ biển 1 dòng KHÔNG giảm
```

Bộ số hiện hành để so:

| Chỉ tiêu | Model gốc |
|---|---|
| A4 — chính xác ký tự | 0,9454 |
| A6 — chuỗi sau hậu xử lý | 0,7512 |
| A6 — riêng biển 1 dòng | **0,9541** |
| A6 — riêng biển 2 dòng | **0,6996** |

Chỉ khi đạt mới bật:

```bash
# Windows
set ALPR_OCR_REC_MODEL_DIR=models\\rec_finetuned
# Linux/macOS
export ALPR_OCR_REC_MODEL_DIR=models/rec_finetuned
```

Không đạt thì **ghi lại trung thực và giữ model gốc** — đó là cách dự án đã xử
lý lần thất bại trước, và bản ghi đó có giá trị học thuật riêng.

Chi tiết đầy đủ: `ai/training/README-rec-finetune.md` mục 3.

## 5. Huấn luyện lại YOLO *(chỉ khi gói có thư mục `yolo/`)*

```bash
python train_yolo.py --smoke    # 2 epoch, chứng minh dây chuyền thông
python train_yolo.py            # 100 epoch, early stop ở patience 25
```

### Kỳ vọng đúng mức

Bộ trọng số hiện hành huấn luyện **trên CPU** hết **10,1 giờ** cho 20 epoch.
Đường cong của lượt đó:

| Epoch | mAP50 | mAP50-95 |
|---|---|---|
| 1 | 0,9684 | 0,6526 |
| 10 | 0,9808 | 0,7248 |
| **12** | **0,9854** ← đỉnh | 0,7219 |
| 20 | 0,9830 | **0,7688** ← vẫn còn nhích |

**`mAP50` đã bão hoà từ khoảng epoch 10 — đừng kỳ vọng nó tăng.** Chỗ duy
nhất còn dư địa là `mAP50-95`, chỉ số đo **độ khít của khung bao**. Khung khít
hơn cho vùng cắt sạch hơn, mà vùng cắt là đầu vào của bộ đọc chữ — nên nếu có
lợi ích thì nó đến gián tiếp qua đó.

Giữ nguyên **`yolo11n`**. Đổi sang model lớn hơn sẽ phá vỡ lập luận trung tâm
của đồ án là suy luận chạy được trên CPU.

### Mốc phải vượt

| | Hiện hành |
|---|---|
| mAP50 | **0,9829** |
| mAP50-95 | **0,7834** |
| Precision | 0,9837 |
| Recall | 0,9714 |

Chép về `yolo_retrained/`, rồi **chỉ thay thế `models/best.pt` khi không thua
bộ hiện hành trên cùng tập test**. Thua thì giữ nguyên bộ cũ và ghi lại lượt
thử — kết quả âm cũng là kết quả.

## 6. Nội dung gói

| Thư mục / tệp | Nội dung |
|---|---|
| `train_gpu.py` | Kịch bản huấn luyện, chạy độc lập |
| `data/images/` | 7.243 ảnh vùng cắt biển số, đã tiền xử lý như production |
| `data/train.txt` | 6.672 dòng nhãn huấn luyện |
| `data/val.txt` | 571 dòng nhãn kiểm định, **không augment** |
| `data/dict36.txt` | Bộ 36 ký tự (A–Z, 0–9) |
| `pretrained/` | Trọng số gốc `en_PP-OCRv5_mobile_rec` |

Ảnh trong `data/images/` đã qua **đúng bước tiền xử lý mà hệ thống thật dùng**
— biển 2 dòng đã tách và ghép ngang thành dải cao 64 px. Đó là chủ ý: tập
huấn luyện phải chứa đúng thứ bộ nhận dạng gặp khi chạy thật, nếu không phép
đo sẽ nói dối.
"""


def _zip_subset(
    out_dir: Path,
    archive: Path,
    include_top: set[str] | None = None,
    exclude_top: set[str] | None = None,
) -> None:
    """Nén một phần của bộ thành một tệp .zip.

    Args:
        out_dir: Thư mục bộ.
        archive: Tệp .zip cần tạo.
        include_top: Nếu có, chỉ lấy các mục cấp một nằm trong tập này.
        exclude_top: Nếu có, bỏ các mục cấp một nằm trong tập này.
    """
    print(f"  nén -> {archive.name} ...")
    stored = deflated = 0
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for path in sorted(out_dir.rglob("*")):
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            top = path.relative_to(out_dir).parts[0]
            if include_top is not None and top not in include_top:
                continue
            if exclude_top is not None and top in exclude_top:
                continue
            # Ảnh JPEG/PNG đã nén sẵn. Đo thử trên 200 ảnh của bộ này: deflate
            # cho ra đúng 100% kích thước gốc — không lợi một byte nào, chỉ tốn
            # CPU trên 37.000 tệp. Lưu nguyên thì bước nén thành thuần I/O.
            if path.suffix.lower() in _INCOMPRESSIBLE:
                zf.write(path, path.relative_to(out_dir.parent),
                         compress_type=zipfile.ZIP_STORED)
                stored += 1
            else:
                zf.write(path, path.relative_to(out_dir.parent))
                deflated += 1
    size = archive.stat().st_size / 1048576
    print(f"[ok] {archive.name}  ({size:.0f} MB · {stored} lưu nguyên, {deflated} nén)")


def build(out_dir: Path, make_zip: bool, with_yolo: bool = False) -> int:
    """Dựng bộ chuyển giao.

    Args:
        out_dir: Thư mục đích.
        make_zip: Có nén thành một tệp .zip không.
        with_yolo: Có kèm bộ dữ liệu YOLO để huấn luyện lại bộ phát hiện không.

    Returns:
        Mã thoát tiến trình.
    """
    if not (DATA_DIR / "train.txt").exists():
        print(
            f"[lỗi] chưa có tập fine-tune tại {DATA_DIR}\n"
            "      Sinh trước bằng:\n"
            "      backend/.venv/Scripts/python scripts/dataset/build_rec_finetune_set.py",
            file=sys.stderr,
        )
        return 2

    if not PRETRAINED.exists() or PRETRAINED.stat().st_size < MIN_WEIGHT_BYTES:
        print(f"[lỗi] thiếu hoặc hỏng trọng số gốc: {PRETRAINED}", file=sys.stderr)
        return 2

    # Dọn NỘI DUNG thay vì xoá chính thư mục. Trên Windows, một thư mục đang là
    # thư mục làm việc của bất kỳ tiến trình nào — kể cả một shell đang mở —
    # không xoá được, và ``rmtree`` khi đó xoá sạch bên trong rồi mới ném lỗi ở
    # bước cuối. Hệ quả là bộ cũ bị phá mà bộ mới chưa dựng: tệ hơn cả không
    # làm gì. Xoá từng mục con thì bước dựng lại luôn chạy được.
    out_dir.mkdir(parents=True, exist_ok=True)
    for child in out_dir.iterdir():
        if child.is_dir():
            shutil.rmtree(child, ignore_errors=True)
        else:
            child.unlink(missing_ok=True)

    print(f"Dựng bộ tại {out_dir}")

    # Dữ liệu. Chép chứ không tạo symlink: bộ này để bỏ vào USB hoặc nén gửi đi,
    # mà symlink thì không sống sót qua cả hai đường đó.
    print("  chép dữ liệu huấn luyện...")
    shutil.copytree(DATA_DIR, out_dir / "data")

    print("  chép trọng số gốc...")
    (out_dir / "pretrained").mkdir()
    shutil.copy2(PRETRAINED, out_dir / "pretrained" / PRETRAINED.name)

    (out_dir / "train_gpu.py").write_text(TRAIN_SCRIPT, encoding="utf-8", newline="\n")
    (out_dir / "README.md").write_text(README, encoding="utf-8", newline="\n")

    if with_yolo:
        if not (YOLO_DATA / "images" / "train").is_dir():
            print(f"[lỗi] không thấy bộ dữ liệu YOLO tại {YOLO_DATA}", file=sys.stderr)
            return 2
        print("  chép dữ liệu YOLO (1,6 GB — mất vài phút)...")
        # Bỏ data.yaml của kho mã: nó ghi đường dẫn tuyệt đối D:/DATN/... nên
        # sang máy khác là trỏ vào hư không. train_yolo.py tự sinh lại tệp này
        # theo đường dẫn của máy đích.
        shutil.copytree(
            YOLO_DATA,
            out_dir / "yolo",
            ignore=shutil.ignore_patterns("data.yaml", "*.cache"),
        )
        (out_dir / "train_yolo.py").write_text(
            YOLO_SCRIPT, encoding="utf-8", newline="\n"
        )

    total = sum(f.stat().st_size for f in out_dir.rglob("*") if f.is_file())
    n_files = sum(1 for f in out_dir.rglob("*") if f.is_file())
    print(f"[ok] {n_files} tệp · {total / 1048576:.0f} MB")

    if make_zip:
        # Nén thành HAI tệp thay vì một, khi bộ có cả phần YOLO. Lý do thực
        # dụng: phần OCR chỉ ~120 MB và đó là phần có kỳ vọng cải thiện thật,
        # còn phần YOLO là 1,5 GB cho một lượt mà mAP50 đã bão hoà. Gộp làm một
        # buộc người dùng phải tải lên và tải về cả 1,6 GB chỉ để chạy phần
        # nhỏ. Tách ra thì phần cần trước đi trước.
        if with_yolo:
            _zip_subset(out_dir, out_dir.parent / f"{out_dir.name}-ocr.zip",
                        exclude_top={"yolo", "train_yolo.py"})
            _zip_subset(out_dir, out_dir.parent / f"{out_dir.name}-yolo.zip",
                        include_top={"yolo", "train_yolo.py", "README.md"})
        else:
            _zip_subset(out_dir, out_dir.with_suffix(".zip"))

    print()
    print("Gửi thư mục (hoặc tệp .zip) sang máy GPU, rồi ở đó chạy:")
    print("    python train_gpu.py --smoke")
    print("    python train_gpu.py")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Điểm vào.

    Args:
        argv: Tham số dòng lệnh.

    Returns:
        Mã thoát tiến trình.
    """
    parser = argparse.ArgumentParser(
        prog="make_gpu_transfer_kit.py",
        description="Gói dữ liệu + trọng số + kịch bản để fine-tune trên máy GPU khác.",
    )
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--zip", action="store_true", help="Nén thành một tệp .zip.")
    parser.add_argument(
        "--with-yolo",
        action="store_true",
        help="Kèm cả bộ dữ liệu YOLO (1,6 GB) để huấn luyện lại bộ phát hiện.",
    )
    args = parser.parse_args(argv)

    out = Path(args.out)
    if not out.is_absolute():
        out = REPO_ROOT / out
    return build(out, args.zip, args.with_yolo)


if __name__ == "__main__":
    raise SystemExit(main())
