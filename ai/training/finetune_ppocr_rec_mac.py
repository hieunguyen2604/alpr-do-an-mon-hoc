#!/usr/bin/env python3
"""Fine-tune PP-OCRv5 mobile rec trên máy Mac Apple Silicon (M1/M2/M3).

Vì sao cần một tệp riêng thay vì dùng ``finetune_ppocr_rec.py``
---------------------------------------------------------------
Bản chung dò thiết bị bằng ``paddle.device.is_compiled_with_cuda()`` rồi chia
hai nhánh GPU/CPU. Trên Mac nhánh đó luôn cho CPU — đúng, nhưng nó bỏ sót ba
việc mà chỉ Apple Silicon mới cần, và cả ba đều làm hỏng lượt chạy chứ không
chỉ làm chậm:

1. **Xung đột OpenMP.** ``libomp`` của Homebrew và ``libiomp5`` đi kèm paddle
   cùng nạp vào một tiến trình. Trên macOS điều đó làm tiến trình chết giữa
   chừng, thường ở lần gọi toán tử đầu tiên. Dự án đã gặp đúng lỗi này ở tầng
   suy luận và vá bằng ``KMP_DUPLICATE_LIB_OK`` (xem
   ``ai/inference/recognizer.py``); huấn luyện cần đúng biến đó, đặt TRƯỚC khi
   paddle được nạp.

2. **Nhân hiệu năng và nhân tiết kiệm điện.** M3 Pro có hai loại nhân với tốc
   độ rất khác nhau. Để OpenMP trải việc lên đủ 11–12 nhân thì mỗi bước phải
   chờ nhóm nhân chậm, và tổng thời gian *xấu hơn* so với chỉ dùng nhóm nhân
   hiệu năng. Script hỏi ``sysctl`` số nhân hiệu năng thật rồi ghim
   ``OMP_NUM_THREADS`` theo đó.

3. **Không có Metal.** Kiểm chứng trực tiếp trên paddle 3.3.1: gói không có
   ``is_compiled_with_mps``, và danh sách backend chỉ gồm CUDA, ROCm, XPU,
   IPU. **Không tồn tại đường chạy GPU nào trên Mac.** Mọi hứa hẹn "dùng GPU
   Apple" đều sai với phiên bản này, nên script nói thẳng thay vì để người
   dùng chờ một thứ không đến.

Điều PHẢI biết trước khi chạy
-----------------------------
Huấn luyện chạy **CPU thuần**, và trên bộ dữ liệu này mất khoảng **1,5–2,5 giờ
cho mỗi epoch**. Mặc định 12 epoch ⇒ **cỡ một ngày đêm**. Vì vậy:

* chạy ``--smoke`` trước — vài chục vòng lặp, đủ chứng minh cả dây chuyền
  thông suốt, mất vài phút. Đừng bao giờ bỏ qua bước này rồi để máy chạy qua
  đêm và sáng ra phát hiện hỏng ở vòng lặp đầu;
* lượt thật nên chạy trong ``tmux``/``screen`` hoặc bật ``caffeinate`` để máy
  không ngủ.

Nếu có Colab GPU thì dùng ``finetune_ppocr_rec_colab.ipynb`` — nhanh hơn hàng
chục lần. Tệp này dành cho trường hợp không có GPU nào khác.

Cách dùng::

    python3 ai/training/finetune_ppocr_rec_mac.py --smoke     # thử dây chuyền
    python3 ai/training/finetune_ppocr_rec_mac.py             # lượt thật
    python3 ai/training/finetune_ppocr_rec_mac.py --export-only

Xong rồi vẫn CHƯA được bật model mới: nghi thức đo bắt buộc nằm ở
``ai/training/README-rec-finetune.md`` mục 3. Lý do nghi thức đó tồn tại nằm ở
``docs/reports/25-finetune-attempt-failed.md`` — một lần fine-tune từng cho ra
model đọc rác 0/7 mà không ai biết cho tới bước đo cuối.
"""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

# Đặt TRƯỚC mọi import có thể kéo theo paddle/OpenMP. Đặt sau thì thư viện đã
# nạp xong và biến không còn tác dụng — đây là lý do dòng này nằm lẻ ở đây chứ
# không nằm trong hàm.
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

# macOS mặc định UTF-8 nên phần này không cần cho đường chạy chính. Nó cần cho
# đúng cái ngược lại: cổng chặn nền tảng ở dưới in một thông báo tiếng Việt cho
# người chạy trên Windows, mà console Windows mặc định là cp1252 — không sửa thì
# lời nhắc "máy này không phải Mac" tự vỡ bằng UnicodeEncodeError, tức nó hỏng
# đúng trên nền tảng duy nhất nó phục vụ.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

PADDLE_VERSION = "3.3.1"
"""Bản paddle dùng chung với phần còn lại của dự án.

Đã kiểm trên PyPI: 3.3.1 có wheel ``macosx_11_0_arm64`` cho cp310 đến cp313,
nên Apple Silicon cài được đúng bản mà Windows và Docker đang dùng. Trên Mac
gói tên là ``paddlepaddle`` — biến thể ``-gpu`` không tồn tại cho macOS.
"""

PRETRAINED_URL = (
    "https://paddle-model-ecology.bj.bcebos.com/paddlex/"
    "official_pretrained_model/en_PP-OCRv5_mobile_rec_pretrained.pdparams"
)

PADDLEOCR_REPO = "https://github.com/PaddlePaddle/PaddleOCR.git"

CONFIG_RELATIVE = Path(
    "configs/rec/PP-OCRv5/multi_language/en_PP-OCRv5_mobile_rec.yaml"
)


# ---------------------------------------------------------------------------
# Môi trường
# ---------------------------------------------------------------------------


def find_repo_root() -> Path:
    """Tìm gốc kho mã bằng mốc ``CLAUDE.md``.

    Returns:
        Đường dẫn gốc kho mã.
    """
    here = Path(__file__).resolve().parent
    for candidate in (here, *here.parents):
        if (candidate / "CLAUDE.md").exists() and (candidate / "ai" / "inference").is_dir():
            return candidate
    return Path(__file__).resolve().parents[2]


def is_apple_silicon() -> bool:
    """Máy này có phải Mac chạy chip Apple không."""
    return sys.platform == "darwin" and platform.machine() == "arm64"


def performance_cores() -> int:
    """Số nhân HIỆU NĂNG của chip, không tính nhân tiết kiệm điện.

    Apple Silicon trộn hai loại nhân trong cùng một con số ``os.cpu_count()``.
    Giao việc OpenMP cho cả hai loại khiến mỗi rào đồng bộ phải chờ nhóm chậm,
    nên tổng thời gian xấu đi. ``hw.perflevel0`` là nhóm nhân hiệu năng.

    Returns:
        Số nhân hiệu năng; lùi về một nửa tổng số nhân khi không hỏi được.
    """
    sysctl = shutil.which("sysctl")
    if sysctl:
        try:
            out = subprocess.run(
                [sysctl, "-n", "hw.perflevel0.logicalcpu"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            value = int(out.stdout.strip())
            if value > 0:
                return value
        except (ValueError, OSError, subprocess.SubprocessError):
            pass
    return max(1, (os.cpu_count() or 4) // 2)


def run(args: list, cwd: Path | None = None, log_path: Path | None = None) -> int:
    """Chạy lệnh, in log ra màn hình VÀ ghi ra tệp.

    Ghi song song ra tệp vì lượt huấn luyện kéo dài hàng giờ: cửa sổ terminal
    có thể bị đóng, cuộn mất, hoặc phiên ssh đứt, mà log là thứ duy nhất cho
    biết lượt chạy đã tới đâu và hỏng ở đâu.

    Args:
        args: Lệnh và tham số.
        cwd: Thư mục làm việc của tiến trình con.
        log_path: Nơi ghi log; ``None`` thì chỉ in ra màn hình.

    Returns:
        Mã thoát của tiến trình con. 0 là thành công.
    """
    printable = " ".join(str(a) for a in args)
    print(f"\n$ {printable}", flush=True)

    # PYTHONUNBUFFERED: thiếu nó thì tiến trình con thấy đầu ra là ống chứ
    # không phải terminal nên gom đệm theo khối, và tiến độ huấn luyện nhìn
    # như bị treo hàng phút.
    env = {**os.environ, "PYTHONUNBUFFERED": "1"}

    handle = None
    if log_path is not None:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handle = log_path.open("w", encoding="utf-8", errors="replace")

    try:
        process = subprocess.Popen(
            [str(a) for a in args],
            cwd=str(cwd) if cwd else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            errors="replace",
            env=env,
        )
        assert process.stdout is not None
        for line in process.stdout:
            line = line.rstrip("\n")
            print(line, flush=True)
            if handle:
                handle.write(line + "\n")
        code = process.wait()
    finally:
        if handle:
            handle.close()

    if code != 0:
        print(f"\n>> LỆNH THẤT BẠI — mã thoát {code}", flush=True)
        if log_path:
            print(f">> Log đầy đủ: {log_path}", flush=True)
    return code


# ---------------------------------------------------------------------------
# Chuẩn bị
# ---------------------------------------------------------------------------


def ensure_venv(work_dir: Path) -> Path:
    """Tạo venv riêng cho huấn luyện và cài paddle bản arm64.

    Venv riêng thay vì dùng ``backend/.venv``: huấn luyện kéo theo cả cây phụ
    thuộc của PaddleOCR, và trộn nó vào môi trường đang phục vụ hệ thống thật
    là cách nhanh nhất để làm hỏng một thứ đang chạy tốt.

    Args:
        work_dir: Thư mục làm việc của huấn luyện.

    Returns:
        Đường dẫn trình thông dịch trong venv.
    """
    venv_python = work_dir / "venv" / "bin" / "python"
    if venv_python.exists():
        return venv_python

    print(f"=== Tạo venv tại {work_dir / 'venv'} ===")
    work_dir.mkdir(parents=True, exist_ok=True)
    run([sys.executable, "-m", "venv", str(work_dir / "venv")])
    run([venv_python, "-m", "pip", "install", "-q", "--upgrade", "pip"])
    run([
        venv_python, "-m", "pip", "install", "-q",
        f"paddlepaddle=={PADDLE_VERSION}",
        "opencv-python", "numpy",
    ])
    return venv_python


def check_paddle(python_bin: Path) -> None:
    """Xác nhận paddle nạp được và nói rõ nó chạy trên gì.

    In ra sự thật thay vì hứa hẹn: nếu người dùng kỳ vọng GPU Apple thì đây là
    chỗ họ biết là không có, trước khi bỏ ra một ngày chờ đợi.

    Args:
        python_bin: Trình thông dịch của venv.

    Raises:
        SystemExit: Khi paddle không nạp được.
    """
    probe = (
        "import paddle;"
        "from paddle.base import core;"
        "print('paddle', paddle.__version__);"
        "print('CUDA', core.is_compiled_with_cuda());"
        "print('MPS', hasattr(paddle.device, 'is_compiled_with_mps'))"
    )
    out = subprocess.run(
        [str(python_bin), "-c", probe], capture_output=True, text=True
    )
    if out.returncode != 0:
        print(out.stdout)
        print(out.stderr)
        raise SystemExit(
            "Không nạp được paddle. Nếu thấy lỗi OpenMP (OMP: Error #15) thì "
            "biến KMP_DUPLICATE_LIB_OK chưa tới được tiến trình con — kiểm tra "
            "lại xem có shell nào ghi đè biến môi trường không."
        )
    print(out.stdout.strip())


def ensure_dataset(root: Path, data_dir: Path, python_bin: Path) -> None:
    """Bảo đảm tập fine-tune đã có, sinh lại nếu chưa.

    KHÔNG tự bịa dữ liệu khi thiếu ảnh gốc. Kịch bản sinh dữ liệu có chốt chặn
    cứng cho đúng chuyện đó — lần fine-tune đầu của dự án hỏng vì một cơ chế
    "ảnh thay thế" ghép nhãn của biển này với ảnh của biển khác, và sai lầm chỉ
    lộ ra sau hàng giờ huấn luyện (``docs/reports/25-finetune-attempt-failed.md``).

    Args:
        root: Gốc kho mã.
        data_dir: Thư mục tập fine-tune.
        python_bin: Trình thông dịch dùng để chạy kịch bản sinh dữ liệu.

    Raises:
        SystemExit: Khi không sinh được tập dữ liệu.
    """
    train_txt = data_dir / "train.txt"
    val_txt = data_dir / "val.txt"
    if train_txt.exists() and val_txt.exists() and train_txt.stat().st_size > 100:
        print(f"Dữ liệu: {sum(1 for _ in train_txt.open(encoding='utf-8'))} dòng train, "
              f"{sum(1 for _ in val_txt.open(encoding='utf-8'))} dòng val")
        return

    print("=== Chưa có tập fine-tune — sinh lại từ nhãn ===")
    builder = root / "scripts" / "dataset" / "build_rec_finetune_set.py"
    if run([python_bin, str(builder)], cwd=root) != 0:
        raise SystemExit(
            "Sinh tập fine-tune thất bại. Nguyên nhân hay gặp nhất: thiếu ảnh "
            "gốc trong datasets/raw (thư mục này nằm trong .gitignore nên KHÔNG "
            "có sẵn sau khi clone). Xem docs/reports/02-dataset-report.md."
        )


def ensure_paddleocr(work_dir: Path, python_bin: Path) -> Path:
    """Clone PaddleOCR và cài phụ thuộc của nó.

    Args:
        work_dir: Thư mục làm việc.
        python_bin: Trình thông dịch của venv.

    Returns:
        Đường dẫn tệp cấu hình huấn luyện.

    Raises:
        SystemExit: Khi không tìm thấy tệp cấu hình sau khi clone.
    """
    paddleocr_dir = work_dir / "PaddleOCR"
    if not paddleocr_dir.exists():
        run(["git", "clone", "--depth", "1", PADDLEOCR_REPO, str(paddleocr_dir)])
        run([
            python_bin, "-m", "pip", "install", "-q",
            "-r", str(paddleocr_dir / "requirements.txt"),
        ])

    config = paddleocr_dir / CONFIG_RELATIVE
    if not config.exists():
        raise SystemExit(
            f"Không thấy cấu hình {CONFIG_RELATIVE} trong bản PaddleOCR vừa "
            "clone. Upstream có thể đã đổi cấu trúc thư mục — mở kho PaddleOCR "
            "tìm cấu hình en_PP-OCRv5_mobile_rec rồi sửa CONFIG_RELATIVE."
        )
    return config


def ensure_pretrained(path: Path) -> None:
    """Tải trọng số gốc nếu chưa có, và kiểm tra kích thước.

    Kiểm kích thước vì một lần tải hỏng từng trả về tệp JSON 117 byte mang tên
    ``.pdparams``; huấn luyện khi đó chết với lỗi giải mã khó lần ra.

    Args:
        path: Nơi lưu trọng số gốc.

    Raises:
        SystemExit: Khi tải về không phải một tệp trọng số hợp lệ.
    """
    if path.exists() and path.stat().st_size > 10_000_000:
        print(f"Trọng số gốc: {path.stat().st_size / 1e6:.1f} MB (OK)")
        return

    print("=== Tải trọng số gốc en_PP-OCRv5_mobile_rec ===")
    path.parent.mkdir(parents=True, exist_ok=True)
    curl = shutil.which("curl")
    if curl is None:
        raise SystemExit("Không tìm thấy curl trên PATH.")
    run([curl, "-L", "--fail", "-o", str(path), PRETRAINED_URL])

    size = path.stat().st_size if path.exists() else 0
    if size < 10_000_000:
        raise SystemExit(
            f"Tệp tải về chỉ {size} byte — không phải trọng số. Nhiều khả năng "
            "URL đã đổi và máy chủ trả về một trang lỗi. Kiểm tra PRETRAINED_URL."
        )
    print(f"Đã tải: {size / 1e6:.1f} MB")


# ---------------------------------------------------------------------------
# Chạy
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Dựng bộ phân tích tham số dòng lệnh.

    Returns:
        Bộ phân tích đã cấu hình.
    """
    parser = argparse.ArgumentParser(
        prog="finetune_ppocr_rec_mac.py",
        description="Fine-tune PP-OCRv5 rec trên Mac Apple Silicon (CPU).",
    )
    parser.add_argument("--epochs", type=int, default=12)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--lr", type=float, default=0.0001)
    parser.add_argument(
        "--threads",
        type=int,
        default=None,
        help="Số luồng OpenMP. Mặc định = số nhân hiệu năng của chip.",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Chạy vài chục vòng lặp để chứng minh dây chuyền thông, vài phút.",
    )
    parser.add_argument("--export-only", action="store_true")
    parser.add_argument(
        "--allow-non-apple",
        action="store_true",
        help="Bỏ qua kiểm tra Apple Silicon (chỉ dùng để thử kịch bản).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Điểm vào.

    Args:
        argv: Tham số dòng lệnh; mặc định lấy ``sys.argv[1:]``.

    Returns:
        Mã thoát tiến trình.
    """
    args = build_parser().parse_args(argv)

    if not is_apple_silicon() and not args.allow_non_apple:
        print(
            f"Máy này là {sys.platform}/{platform.machine()}, không phải Mac "
            "Apple Silicon.\n"
            "  • Windows/Linux có GPU  -> ai/training/finetune_ppocr_rec.py\n"
            "  • Không có GPU          -> ai/training/finetune_ppocr_rec_colab.ipynb\n"
            "  • Vẫn muốn chạy tệp này -> thêm --allow-non-apple"
        )
        return 2

    root = find_repo_root()
    work_dir = root / "training-work"
    data_dir = root / "datasets" / "processed" / "rec_finetune"
    output_dir = work_dir / "output" / "rec_vn"
    export_dir = root / "models" / "rec_finetuned"
    pretrained = root / "models" / "pretrained" / "en_PP-OCRv5_mobile_rec_pretrained.pdparams"
    log_dir = work_dir / "logs"

    threads = args.threads or performance_cores()
    os.environ["OMP_NUM_THREADS"] = str(threads)

    epochs = 1 if args.smoke else args.epochs
    batch_size = 8 if args.smoke else args.batch_size

    print("=" * 70)
    print("  FINE-TUNE PP-OCRv5 rec — Mac Apple Silicon")
    print("=" * 70)
    print(f"  Chip              : {platform.machine()} · {os.cpu_count()} nhân "
          f"({threads} nhân hiệu năng)")
    print("  Thiết bị tính toán: CPU — paddle không có backend Metal/MPS")
    print(f"  Chế độ            : {'THỬ DÂY CHUYỀN (smoke)' if args.smoke else 'HUẤN LUYỆN THẬT'}")
    print(f"  Epochs / batch    : {epochs} / {batch_size}")
    if not args.smoke:
        print(f"  Thời gian dự kiến : ~{epochs * 2} giờ. Chạy trong tmux/screen,")
        print( "                      hoặc bật caffeinate để máy không ngủ.")
    print("=" * 70)

    python_bin = ensure_venv(work_dir)
    check_paddle(python_bin)
    ensure_dataset(root, data_dir, python_bin)
    config = ensure_paddleocr(work_dir, python_bin)
    ensure_pretrained(pretrained)
    paddleocr_dir = work_dir / "PaddleOCR"

    common = [
        "Global.use_gpu=false",
        f"Global.character_dict_path={(data_dir / 'dict36.txt').as_posix()}",
        "Global.use_space_char=false",
        "Global.max_text_length=10",
        f"Eval.dataset.data_dir={data_dir.as_posix()}",
        f"Eval.dataset.label_file_list=[{(data_dir / 'val.txt').as_posix()}]",
        f"Eval.loader.batch_size_per_card={batch_size}",
        # 0 worker trên macOS. DataLoader nhiều tiến trình dùng fork, mà fork
        # một tiến trình đã nạp thư viện toán học của Apple hay treo — và treo
        # thì không có thông báo lỗi nào, chỉ là chờ mãi không xong.
        "Eval.loader.num_workers=0",
    ]

    if not args.export_only:
        train_opts = [
            *common,
            f"Global.epoch_num={epochs}",
            "Global.save_epoch_step=1",
            "Global.eval_batch_step=[0,200]",
            "Global.print_batch_step=10",
            f"Global.save_model_dir={output_dir.as_posix()}",
            f"Optimizer.lr.learning_rate={args.lr}",
            "Optimizer.lr.warmup_epoch=1",
            f"Train.dataset.data_dir={data_dir.as_posix()}",
            f"Train.dataset.label_file_list=[{(data_dir / 'train.txt').as_posix()}]",
            f"Train.sampler.first_bs={batch_size}",
            f"Train.loader.batch_size_per_card={batch_size}",
            "Train.loader.num_workers=0",
        ]

        latest = output_dir / "latest.pdparams"
        if latest.exists():
            print(f">> Nối tiếp checkpoint cũ: {latest}")
            print(">> Muốn bắt đầu lại từ đầu thì xoá thư mục", output_dir)
            train_opts.insert(0, f"Global.checkpoints={(output_dir / 'latest').as_posix()}")
        else:
            prefix = pretrained.as_posix()[: -len(".pdparams")]
            train_opts.insert(0, f"Global.pretrained_model={prefix}")

        code = run(
            [python_bin, "tools/train.py", "-c", str(config), "-o", *train_opts],
            cwd=paddleocr_dir,
            log_path=log_dir / "train-mac.log",
        )
        if code != 0:
            return code

    if args.smoke:
        print("\n" + "=" * 70)
        print("  Dây chuyền thông. Giờ chạy lượt thật:")
        print("    caffeinate -i python3 ai/training/finetune_ppocr_rec_mac.py")
        print("=" * 70)
        return 0

    best = output_dir / "best_accuracy"
    if not best.with_suffix(".pdparams").exists():
        print("\nKhông có best_accuracy — chưa đủ bước để chấm điểm. Dừng ở đây.")
        return 1

    print("\n=== ĐÁNH GIÁ trên tập val sạch ===")
    run(
        [python_bin, "tools/eval.py", "-c", str(config), "-o",
         *common, f"Global.checkpoints={best.as_posix()}"],
        cwd=paddleocr_dir,
        log_path=log_dir / "eval-mac.log",
    )

    print("\n=== XUẤT model suy luận ===")
    export_dir.mkdir(parents=True, exist_ok=True)
    run(
        [python_bin, "tools/export_model.py", "-c", str(config), "-o",
         *common, f"Global.checkpoints={best.as_posix()}",
         f"Global.save_inference_dir={export_dir.as_posix()}"],
        cwd=paddleocr_dir,
        log_path=log_dir / "export-mac.log",
    )
    shutil.copy2(data_dir / "dict36.txt", export_dir / "dict36.txt")

    print("\n" + "=" * 70)
    print("  Model đã xuất, nhưng CHƯA ĐƯỢC BẬT.")
    print("=" * 70)
    print("  Một lần fine-tune trước đây cho ra model đọc rác 0/7 ảnh demo, và")
    print("  chuyện đó chỉ lộ ra ở bước đo cuối cùng. Vì vậy nghi thức đo là")
    print("  bắt buộc, không phải khuyến nghị:")
    print()
    print("    1. Đo A4–A7 toàn tập, so với bộ số hiện hành")
    print("       Đạt = A6 biển 2 dòng tăng ≥ 5 điểm, biển 1 dòng KHÔNG giảm")
    print("    2. Chạy bộ hồi quy demo/images/expected.json")
    print("    3. Đo cả khi bật lẫn khi tắt, để quy đúng công cho fine-tune")
    print()
    print("  Chi tiết  : ai/training/README-rec-finetune.md muc 3")
    print("  Vì sao có : docs/reports/25-finetune-attempt-failed.md")
    print()
    print(f"  Bật bằng  : export ALPR_OCR_REC_MODEL_DIR={export_dir.as_posix()}")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
