#!/usr/bin/env python3
"""
Fine-tune PP-OCRv5 mobile rec trên crop biển số Việt Nam (Chạy trực tiếp trên máy local).

Cách sử dụng:
    python ai/training/finetune_ppocr_rec.py [options]

Ví dụ:
    # Chạy mặc định (tự động phát hiện GPU/CPU, tự sinh dataset nếu chưa có)
    python ai/training/finetune_ppocr_rec.py

    # Tùy chỉnh số epoch và batch size
    python ai/training/finetune_ppocr_rec.py --epochs 30 --batch-size 64

    # Chỉ xuất model đã train (nếu đã có checkpoint best_accuracy)
    python ai/training/finetune_ppocr_rec.py --export-only
"""

import argparse
import os
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

PRETRAINED_URL = (
    "https://paddle-model-ecology.bj.bcebos.com/paddlex/"
    "official_pretrained_model/en_PP-OCRv5_mobile_rec_pretrained.pdparams"
)


def find_repo_root() -> Path:
    """Tìm thư mục gốc của repository."""
    here = Path(__file__).resolve().parent
    for candidate in (here, *here.parents):
        if (candidate / "CLAUDE.md").exists() and (candidate / "ai" / "inference").is_dir():
            return candidate
    # Fallback nếu không tìm thấy CLAUDE.md
    return Path(__file__).resolve().parents[2]


def run_cmd(args, cwd=None):
    """Chạy lệnh subprocess và in ra stdout trực tiếp."""
    cmd_str = " ".join(str(a) for a in args)
    print(f"\n$ {cmd_str}")
    res = subprocess.run([str(a) for a in args], cwd=str(cwd) if cwd else None)
    if res.returncode != 0:
        print(f"[CẢNH BÁO] Lệnh trả về mã lỗi: {res.returncode}")
    return res.returncode


def find_python_310_plus() -> str:
    """Tìm Python >= 3.10 trên hệ thống (vì dự án sử dụng dataclass(slots=True)).

    Chỉ dò theo TÊN lệnh, để ``shutil.which`` tra PATH — không ghi cứng đường
    dẫn tuyệt đối kiểu ``/opt/homebrew/bin/python3.12``: đường dẫn ấy chỉ đúng
    trên một máy, và quy ước NFR-M4 của dự án cấm literal như vậy trong ``ai/``
    (có test kiểm tra). Máy nào để Python ngoài PATH thì chỉ định thẳng qua
    biến môi trường ``ALPR_TRAIN_PYTHON``.
    """
    override = os.environ.get("ALPR_TRAIN_PYTHON", "").strip()
    candidates = [
        *( [override] if override else [] ),
        "python3.12",
        "python3.11",
        "python3.13",
        "python3.10",
        "python3",
    ]
    for cand in candidates:
        p = shutil.which(cand) or (cand if os.path.exists(cand) else None)
        if p:
            try:
                out = subprocess.run([str(p), "-c", "import sys; print(sys.version_info >= (3, 10))"], capture_output=True, text=True)
                if out.stdout.strip() == "True":
                    return str(p)
            except Exception:
                pass
    return sys.executable


def get_venv_python(work_dir: Path) -> Path:
    """Ưu tiên venv trong training-work/venv nếu có, ngược lại tìm Python >= 3.10 để sử dụng."""
    venv_py = work_dir / "venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if venv_py.exists():
        return venv_py

    py_base = find_python_310_plus()
    py_ver = subprocess.run([py_base, "-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"], capture_output=True, text=True).stdout.strip()
    print(f"\n[Thông tin] Sử dụng Python base: {py_base} (v{py_ver})")
    
    # Tạo venv nếu chưa có
    if not venv_py.exists():
        print(f"=== Khởi tạo Virtual Environment tại: {work_dir / 'venv'} ===")
        work_dir.mkdir(parents=True, exist_ok=True)
        run_cmd([py_base, "-m", "venv", work_dir / "venv"])
        if venv_py.exists():
            print("Cài đặt các gói cơ bản vào venv...")
            run_cmd([venv_py, "-m", "pip", "install", "-q", "--upgrade", "pip"])
            run_cmd([venv_py, "-m", "pip", "install", "-q", "opencv-python", "numpy", "pandas", "paddlepaddle==3.3.1"])
            return venv_py

    return Path(py_base)



def is_gpu_available(python_bin: Path) -> bool:
    """Kiểm tra PaddlePaddle có hỗ trợ GPU/CUDA không."""
    try:
        out = subprocess.run(
            [str(python_bin), "-c", "import paddle; print(paddle.device.is_compiled_with_cuda())"],
            capture_output=True,
            text=True,
        )
        return out.stdout.strip() == "True"
    except Exception:
        return False


def ensure_dataset(root: Path, data_dir: Path, python_bin: Path):
    """Đảm bảo dataset train.txt và val.txt đã sẵn sàng và hợp lệ (không bị rỗng)."""
    train_txt = data_dir / "train.txt"
    val_txt = data_dir / "val.txt"

    def is_valid_dataset() -> bool:
        return train_txt.exists() and train_txt.stat().st_size > 100 and val_txt.exists() and val_txt.stat().st_size > 100

    if not is_valid_dataset():
        print("\n=== 1. Chưa có dataset hợp lệ. Đang tự động sinh dataset từ nhãn... ===")
        # Xóa file rỗng nếu có
        if train_txt.exists() and train_txt.stat().st_size <= 100:
            train_txt.unlink()
        if val_txt.exists() and val_txt.stat().st_size <= 100:
            val_txt.unlink()

        script = root / "scripts" / "dataset" / "build_rec_finetune_set.py"
        if script.exists():
            code = run_cmd([python_bin, script], cwd=root)
            if code != 0 or not is_valid_dataset():
                raise RuntimeError("Sinh dataset thất bại! Vui lòng kiểm tra lại dữ liệu nhãn gốc.")
        else:
            raise FileNotFoundError(f"Không tìm thấy script sinh dataset tại: {script}")


    n_train = sum(1 for _ in train_txt.open(encoding="utf-8"))
    n_val = sum(1 for _ in val_txt.open(encoding="utf-8"))
    dict_file = data_dir / "dict36.txt"
    n_dict = len(dict_file.read_text(encoding="utf-8").split()) if dict_file.exists() else 0
    print(f"[Dataset OK] train: {n_train} dòng | val: {n_val} dòng | dictionary: {n_dict} ký tự")


def ensure_paddleocr(work_dir: Path, python_bin: Path) -> Path:
    """Đảm bảo repository PaddleOCR đã được clone và cài đặt thư viện cần thiết."""
    paddleocr_dir = work_dir / "PaddleOCR"
    if not paddleocr_dir.exists():
        print("\n=== 2. Clone mã nguồn PaddleOCR... ===")
        work_dir.mkdir(parents=True, exist_ok=True)
        run_cmd(["git", "clone", "--depth", "1", "https://github.com/PaddlePaddle/PaddleOCR.git", paddleocr_dir])
        req_file = paddleocr_dir / "requirements.txt"
        if req_file.exists():
            print("Cài đặt requirements cho PaddleOCR...")
            run_cmd([python_bin, "-m", "pip", "install", "-q", "-r", req_file])

    config_path = paddleocr_dir / "configs/rec/PP-OCRv5/multi_language/en_PP-OCRv5_mobile_rec.yaml"
    if not config_path.exists():
        found = list(paddleocr_dir.glob("configs/rec/**/*en_PP-OCRv5_mobile*.y*ml"))
        if found:
            config_path = found[0]
        else:
            raise FileNotFoundError(f"Không tìm thấy file config PP-OCRv5 trong {paddleocr_dir}")

    print(f"[PaddleOCR OK] Config: {config_path}")
    return config_path


def ensure_pretrained_weights(pretrained_path: Path, work_dir: Path):
    """Đảm bảo weights pretrained đã được tải về."""
    def is_valid_file(p: Path) -> bool:
        return p.exists() and p.stat().st_size > 10_000_000

    if is_valid_file(pretrained_path):
        print(f"[Pretrained OK] {pretrained_path} ({pretrained_path.stat().st_size / 1e6:.1f} MB)")
        return

    pretrained_path.parent.mkdir(parents=True, exist_ok=True)
    alt = work_dir / "pretrained" / pretrained_path.name
    if is_valid_file(alt):
        print(f"Sao chép weights pretrained từ {alt}")
        shutil.copy2(alt, pretrained_path)
    else:
        print("\n=== 3. Tải trọng số gốc (Pretrained Weights) PP-OCRv5 mobile rec... ===")
        urllib.request.urlretrieve(PRETRAINED_URL, pretrained_path)

    if not is_valid_file(pretrained_path):
        raise RuntimeError("Tải trọng số gốc thất bại hoặc file bị hỏng (>10MB). Vui lòng thử lại!")
    print(f"[Pretrained OK] {pretrained_path} ({pretrained_path.stat().st_size / 1e6:.1f} MB)")


def main():
    parser = argparse.ArgumentParser(description="Fine-tune PP-OCRv5 mobile rec trực tiếp trên máy local")
    parser.add_argument("--epochs", type=int, default=None, help="Số lượng epoch huấn luyện (Default: 30 trên GPU, 12 trên CPU)")
    parser.add_argument("--batch-size", type=int, default=None, help="Batch size (Default: 128 trên GPU, 64 trên CPU)")
    parser.add_argument("--workers", type=int, default=None, help="Số lượng data loader workers (Default: 2 trên GPU, 0 trên CPU)")
    parser.add_argument("--lr", type=float, default=0.0001, help="Learning rate (Default: 0.0001)")
    parser.add_argument("--force-cpu", action="store_true", help="Bắt buộc chạy bằng CPU dù máy có GPU")
    parser.add_argument("--export-only", action="store_true", help="Chỉ thực hiện export model (bỏ qua bước train & eval)")
    parser.add_argument("--eval-only", action="store_true", help="Chỉ đánh giá checkpoint best_accuracy")
    args = parser.parse_args()

    root = find_repo_root()
    work_dir = root / "training-work"
    data_dir = root / "datasets" / "processed" / "rec_finetune"
    export_dir = root / "models" / "rec_finetuned"
    pretrained_path = root / "models" / "pretrained" / "en_PP-OCRv5_mobile_rec_pretrained.pdparams"
    output_dir = work_dir / "output" / "rec_vn"

    python_bin = get_venv_python(work_dir)
    use_gpu = False if args.force_cpu else is_gpu_available(python_bin)

    epochs = args.epochs if args.epochs is not None else (30 if use_gpu else 12)
    batch_size = args.batch_size if args.batch_size is not None else (128 if use_gpu else 64)
    workers = args.workers if args.workers is not None else (2 if use_gpu else 0)

    print("=" * 70)
    print("THÔNG TIN CẤU HÌNH HUẤN LUYỆN LOCAL")
    print(f"  Thư mục gốc Repo  : {root}")
    print(f"  Python executable : {python_bin}")
    print(f"  Chế độ tính toán   : {'GPU (CUDA)' if use_gpu else 'CPU (~2 giờ/epoch)'}")
    print(f"  Epochs            : {epochs}")
    print(f"  Batch size        : {batch_size}")
    print(f"  Workers           : {workers}")
    print("=" * 70)

    # 1. Đảm bảo dữ liệu & thư viện
    ensure_dataset(root, data_dir, python_bin)
    config_path = ensure_paddleocr(work_dir, python_bin)
    ensure_pretrained_weights(pretrained_path, work_dir)
    paddleocr_dir = work_dir / "PaddleOCR"

    common_opts = [
        f"Global.use_gpu={str(use_gpu).lower()}",
        f"Global.character_dict_path={(data_dir / 'dict36.txt').as_posix()}",
        "Global.use_space_char=false",
        "Global.max_text_length=10",
        f"Eval.dataset.data_dir={data_dir.as_posix()}",
        f"Eval.dataset.label_file_list=[{(data_dir / 'val.txt').as_posix()}]",
        f"Eval.loader.batch_size_per_card={batch_size}",
        f"Eval.loader.num_workers={workers}",
    ]

    # 2. Huấn luyện (Train)
    if not args.export_only and not args.eval_only:
        print("\n=== 4. BẮT ĐẦU HUẤN LUYỆN (TRAINING) ===")
        output_dir.mkdir(parents=True, exist_ok=True)
        train_opts = [
            *common_opts,
            f"Global.epoch_num={epochs}",
            "Global.save_epoch_step=1",
            "Global.eval_batch_step=[0,10]",
            "Global.print_batch_step=20",
            f"Global.save_model_dir={output_dir.as_posix()}",
            f"Optimizer.lr.learning_rate={args.lr}",
            "Optimizer.lr.warmup_epoch=1",
            f"Train.dataset.data_dir={data_dir.as_posix()}",
            f"Train.dataset.label_file_list=[{(data_dir / 'train.txt').as_posix()}]",
            f"Train.sampler.first_bs={batch_size}",
            f"Train.loader.batch_size_per_card={batch_size}",
            f"Train.loader.num_workers={workers}",
        ]

        latest_ckpt = output_dir / "latest.pdparams"
        if latest_ckpt.exists():
            print(f">> Khôi phục huấn luyện từ Checkpoint cũ: {latest_ckpt}")
            train_opts.insert(0, f"Global.checkpoints={(output_dir / 'latest').as_posix()}")
        else:
            print(">> Huấn luyện từ Trọng số gốc (Pretrained)")
            pretrained_prefix = str(pretrained_path.as_posix())
            if pretrained_prefix.endswith(".pdparams"):
                pretrained_prefix = pretrained_prefix[:-9]
            train_opts.insert(0, f"Global.pretrained_model={pretrained_prefix}")

        run_cmd([python_bin, "tools/train.py", "-c", config_path, "-o", *train_opts], cwd=paddleocr_dir)

    # Nếu chưa có best_accuracy (ví dụ train ít epoch/step), tạo bản sao từ latest
    best_ckpt = output_dir / "best_accuracy"
    if not (output_dir / "best_accuracy.pdparams").exists() and (output_dir / "latest.pdparams").exists():
        print(">> Sao chép latest checkpoint làm best_accuracy...")
        for ext in [".pdparams", ".pdopt", ".states"]:
            src = output_dir / f"latest{ext}"
            dst = output_dir / f"best_accuracy{ext}"
            if src.exists():
                shutil.copy2(src, dst)

    # 3. Đánh giá (Eval)
    if not args.export_only:

        print("\n=== 5. ĐÁNH GIÁ CHECKPOINT TỐT NHẤT (EVALUATION) ===")
        if (output_dir / "best_accuracy.pdparams").exists():
            eval_opts = [
                *common_opts,
                f"Global.checkpoints={best_ckpt.as_posix()}",
            ]
            run_cmd([python_bin, "tools/eval.py", "-c", config_path, "-o", *eval_opts], cwd=paddleocr_dir)
        else:
            print("[CẢNH BÁO] Chưa tìm thấy checkpoint best_accuracy để đánh giá!")

    # 4. Xuất mô hình (Export Inference Model)
    print("\n=== 6. XUẤT MÔ HÌNH INFERENCE (EXPORT) ===")
    if (output_dir / "best_accuracy.pdparams").exists():
        export_opts = [
            f"Global.checkpoints={best_ckpt.as_posix()}",
            f"Global.character_dict_path={(data_dir / 'dict36.txt').as_posix()}",
            "Global.use_space_char=false",
            "Global.max_text_length=10",
            f"Global.save_inference_dir={export_dir.as_posix()}",
        ]
        run_cmd([python_bin, "tools/export_model.py", "-c", config_path, "-o", *export_opts], cwd=paddleocr_dir)

        # Copy bộ từ điển dict36.txt vào thư mục xuất model
        if (data_dir / "dict36.txt").exists():
            shutil.copy2(data_dir / "dict36.txt", export_dir / "dict36.txt")

        print(f"\n[HOÀN TẤT] Mô hình đã được xuất ra thư mục: {export_dir}")




        for f in sorted(export_dir.glob("*")):
            print(f"  - {f.name:<30} {f.stat().st_size / 1e6:8.2f} MB")

        print("\nĐể kích hoạt mô hình fine-tuned này trong hệ thống ALPR:")
        print("  Set biến môi trường: ALPR_OCR_REC_MODEL_DIR=models/rec_finetuned")
    else:
        print("[LỖI] Không thể xuất mô hình vì chưa có checkpoint best_accuracy trong", output_dir)


if __name__ == "__main__":
    main()
