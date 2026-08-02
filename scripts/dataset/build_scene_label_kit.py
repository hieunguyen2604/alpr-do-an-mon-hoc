"""Dựng bộ công cụ gán nhãn chuỗi biển số cho ẢNH TOÀN CẢNH.

Vì sao cần
----------
Mọi con số OCR của đồ án hiện đo trên ảnh **đã cắt sẵn**. Hai câu hỏi quan
trọng đều bị chặn bởi cùng một lỗ hổng đó:

1. **NFR-A7** hiện được đo bằng cách đưa ảnh crop vào bộ phát hiện, nên payload
   của nó tự đánh dấu ``KHONG DAI DIEN``: bộ phát hiện được huấn luyện trên ảnh
   giao thông đầy đủ, đưa cho nó một tấm ảnh mà biển chiếm gần hết khung là
   **ngoài phân bố**.
2. **Có nên bỏ bước phát hiện chữ của PaddleOCR hay không** --
   ``ALPR_OCR_SKIP_DETECTION``. Trên ngữ liệu ảnh cắt sẵn, bỏ nó thắng 12,46
   điểm; trên bộ demo chạy ảnh toàn cảnh, bỏ nó **thua 4 biển**. Xem
   ``docs/reports/31-detection-stage-ablation.md``.

Cả hai chỉ trả lời được bằng một tập ảnh toàn cảnh **có nhãn chuỗi biển số**.
Script này dựng nguyên liệu để tạo ra tập đó với ít công tay nhất.

Thiết kế
--------
Chạy **nguyên đường ống thật** (``ALPRPipeline.process``) cho từng cấu hình,
không chép lại các bước. Đây là ràng buộc bắt buộc: đồ án đã ba lần công bố số
liệu sai vì công cụ đo tự liệt kê lại các bước của pipeline rồi trôi khỏi bản
giao. Bộ phát hiện được **dựng một lần và dùng chung**, nên mọi cấu hình nhìn
thấy đúng cùng một tập khung biển.

Đầu ra chia hai loại, và đây là chỗ tiết kiệm công:

* **Các cấu hình đọc GIỐNG nhau** -- điền sẵn chuỗi đó, người gán chỉ xác nhận.
  Chúng không phân biệt được cấu hình nào hơn (mọi cấu hình cùng đúng hoặc cùng
  sai), nên chúng chỉ cần thiết cho con số A7 tuyệt đối.
* **Các cấu hình đọc KHÁC nhau** -- để trống, bắt buộc gõ tay. Đây chính là tập
  quyết định cuộc so sánh, nên nó được xếp lên đầu phiếu.

CẢNH BÁO -- KHÔNG được lấy chuỗi đồng thuận làm nhãn rồi đem chấm chính các mô
hình đã sinh ra nó. Đó là lập luận vòng tròn: mọi mô hình sẽ tự động đúng trên
mọi mẫu đồng thuận, kể cả khi tất cả cùng đọc sai. Ô điền sẵn là **gợi ý gõ**,
người gán vẫn phải nhìn ảnh và xác nhận từng dòng.

Cách chạy
---------
.. code-block:: bash

    backend/.venv/Scripts/python scripts/dataset/build_scene_label_kit.py --limit 0

Mở ``datasets/annotations/scene_review/review.html``, gán nhãn, bấm *Tải CSV*.
"""

from __future__ import annotations

import argparse
import html
import json
import logging
import sys
from dataclasses import replace
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from ai.inference.config import InferenceConfig  # noqa: E402
from ai.inference.detector import YoloPlateDetector  # noqa: E402
from ai.inference.normalizer import VietnamesePlateNormalizer  # noqa: E402
from ai.inference.pipeline import ALPRPipeline  # noqa: E402
from ai.inference.recognizer import PaddleOcrRecognizer  # noqa: E402

_LOGGER = logging.getLogger("build_scene_label_kit")

SCENES = ROOT / "datasets" / "processed" / "yolo_v3" / "images" / "test"
OUT_DIR = ROOT / "datasets" / "annotations" / "scene_review"
CROP_DIR = OUT_DIR / "crops"
REPORT = ROOT / "docs" / "reports" / "32-scene-candidates.json"
FINE = ROOT / "models" / "rec_finetuned"

CONFIGS: dict[str, dict] = {
    "goc_det": {"rec_dir": None, "skip": False},
    "goc_rec": {"rec_dir": None, "skip": True},
    "ft_det": {"rec_dir": FINE, "skip": False},
    "ft_rec": {"rec_dir": FINE, "skip": True},
}


def build_pipeline(detector: YoloPlateDetector, rec_dir: Path | None, skip: bool) -> ALPRPipeline:
    """Đường ống thật, chỉ đổi hai công tắc, dùng chung một bộ phát hiện."""
    config = replace(
        InferenceConfig.from_env(), ocr_rec_model_dir=rec_dir, ocr_skip_detection=skip
    )
    return ALPRPipeline(
        detector=detector,
        recognizer=PaddleOcrRecognizer(config),
        normalizer=VietnamesePlateNormalizer(),
        config=config,
    )


def key_of(bbox) -> str:
    """Khoá ổn định cho một khung biển, để ghép kết quả giữa các cấu hình."""
    return f"{int(bbox.x)}_{int(bbox.y)}_{int(bbox.width)}_{int(bbox.height)}"


def main() -> None:
    parser = argparse.ArgumentParser(prog="build_scene_label_kit")
    parser.add_argument("--scenes", default=str(SCENES))
    parser.add_argument("--limit", type=int, default=0, help="0 = mọi ảnh")
    parser.add_argument(
        "--resample",
        type=int,
        default=0,
        help=(
            "Dựng lại phiếu gán nhãn từ kết quả đã có, lấy N khung BẤT ĐỒNG "
            "ngẫu nhiên (seed cố định). Không chạy lại mô hình nào. Dùng khi "
            "toàn bộ tập bất đồng quá lớn để gõ tay hết."
        ),
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    if args.resample:
        resample_sheet(args.resample)
        return

    # Đường ống ghi ba dòng cho MỖI khung biển của MỖI cấu hình. Với 1.514 ảnh
    # và 4 cấu hình đó là hàng chục nghìn dòng, đủ để chi phối thời gian chạy.
    logging.getLogger("ai").setLevel(logging.WARNING)
    CROP_DIR.mkdir(parents=True, exist_ok=True)

    scene_dir = Path(args.scenes)
    images = sorted(p for p in scene_dir.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png"})
    if args.limit:
        images = images[: args.limit]
    _LOGGER.info("Ảnh toàn cảnh: %d", len(images))

    base = InferenceConfig.from_env()
    detector = YoloPlateDetector(base)
    pipelines = {name: build_pipeline(detector, **spec) for name, spec in CONFIGS.items()}

    records: dict[str, dict] = {}

    for index, path in enumerate(images, 1):
        image = cv2.imread(str(path))
        if image is None:
            continue

        for name, pipeline in pipelines.items():
            result = pipeline.process(image)
            for plate in result.results:
                bbox_key = f"{path.stem}#{key_of(plate.detection.bbox)}"
                record = records.setdefault(
                    bbox_key,
                    {
                        "scene": path.name,
                        "bbox": [
                            int(plate.detection.bbox.x),
                            int(plate.detection.bbox.y),
                            int(plate.detection.bbox.width),
                            int(plate.detection.bbox.height),
                        ],
                        "color": plate.plate_color,
                        "reads": {},
                        "crop": "",
                    },
                )
                record["reads"][name] = (
                    plate.recognition.text if plate.recognition is not None else ""
                )
                if not record["crop"] and plate.plate_image is not None:
                    crop_name = f"{bbox_key.replace('#', '__')}.png"
                    cv2.imwrite(str(CROP_DIR / crop_name), plate.plate_image)
                    record["crop"] = crop_name

        if index % 25 == 0:
            _LOGGER.info("  %d/%d ảnh, %d khung biển", index, len(images), len(records))

    rows = []
    for bbox_key, record in records.items():
        reads = [record["reads"].get(name, "") for name in CONFIGS]
        distinct = {r for r in reads if r}
        record["key"] = bbox_key
        record["agree"] = len(distinct) == 1 and len(reads) == len(CONFIGS)
        record["suggestion"] = next(iter(distinct)) if record["agree"] else ""
        rows.append(record)

    # Bất đồng lên đầu: đó là phần bắt buộc gõ tay và là phần quyết định.
    rows.sort(key=lambda r: (r["agree"], r["scene"]))
    disagree = sum(1 for r in rows if not r["agree"])

    REPORT.write_text(
        json.dumps(
            {
                "scenes": len(images),
                "plates": len(rows),
                "disagreements": disagree,
                "configs": {k: {"rec_dir": str(v["rec_dir"] or ""), "skip_detection": v["skip"]}
                            for k, v in CONFIGS.items()},
                "rows": rows,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    write_review_sheet(rows)

    _LOGGER.info("Khung biển: %d | bất đồng: %d (%.1f%%)",
                 len(rows), disagree, disagree / max(1, len(rows)) * 100)
    _LOGGER.info("Phiếu gán nhãn: %s", OUT_DIR / "review.html")


def resample_sheet(count: int) -> None:
    """Dựng lại phiếu từ ``32-scene-candidates.json``, chỉ lấy N khung bất đồng.

    Toàn bộ 1.232 khung bất đồng là khoảng ba giờ gõ tay. Một mẫu ngẫu nhiên
    300 khung cho sai số khoảng ±5 điểm phần trăm — đủ để phân định cấu hình
    nào thắng, ở một phần tư công sức. Seed cố định để mẫu tái lập được.

    Args:
        count: Số khung bất đồng lấy vào phiếu.
    """
    import random

    payload = json.loads(REPORT.read_text(encoding="utf-8"))
    disagree = [r for r in payload["rows"] if not r["agree"]]
    rng = random.Random(42)
    sample = rng.sample(disagree, min(count, len(disagree)))
    sample.sort(key=lambda r: r["scene"])

    write_review_sheet(sample)
    (OUT_DIR / "sample_keys.json").write_text(
        json.dumps([r["key"] for r in sample], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    _LOGGER.info(
        "Phiếu rút gọn: %d/%d khung bất đồng (seed 42) -> %s",
        len(sample), len(disagree), OUT_DIR / "review.html",
    )


def write_review_sheet(rows: list[dict]) -> None:
    """Phiếu gán nhãn mở bằng trình duyệt, tự tải CSV khi bấm nút."""
    blocks = []
    for i, r in enumerate(rows):
        reads = " · ".join(
            f"<b>{html.escape(k)}</b>: {html.escape(v) or '—'}" for k, v in r["reads"].items()
        )
        flag = "" if r["agree"] else ' <span class="warn">BẤT ĐỒNG — phải gõ tay</span>'
        blocks.append(
            f'<div class="row{"" if r["agree"] else " dis"}">'
            f'<img src="crops/{html.escape(r["crop"])}" alt="">'
            f'<div class="meta"><div class="scene">{html.escape(r["scene"])}{flag}</div>'
            f'<div class="reads">{reads}</div>'
            f'<input data-key="{html.escape(r["key"])}" value="{html.escape(r["suggestion"])}" '
            f'placeholder="gõ chuỗi biển số đúng"></div></div>'
        )

    OUT_DIR.joinpath("review.html").write_text(
        f"""<!doctype html><meta charset="utf-8"><title>Gán nhãn biển số ảnh toàn cảnh</title>
<style>
body{{font:15px system-ui;margin:24px;max-width:1000px}}
.row{{display:flex;gap:16px;align-items:center;padding:10px;border-bottom:1px solid #ddd}}
.row.dis{{background:#fff6f6}}
img{{height:64px;image-rendering:pixelated;border:1px solid #bbb}}
.meta{{flex:1}} .scene{{font-size:12px;color:#666}}
.reads{{font-size:12px;color:#333;margin:3px 0}}
.warn{{color:#c00;font-weight:600}}
input{{width:260px;padding:6px;font-size:15px;font-family:ui-monospace,monospace}}
button{{position:sticky;top:0;padding:10px 18px;font-size:15px}}
</style>
<h1>Gán nhãn chuỗi biển số — ảnh toàn cảnh</h1>
<p>Dòng nền đỏ là chỗ các cấu hình đọc khác nhau: <b>bắt buộc nhìn ảnh và gõ tay</b>.
Dòng còn lại đã điền sẵn chuỗi mà mọi cấu hình cùng đọc ra — vẫn phải <b>nhìn ảnh xác nhận</b>,
đừng bấm qua, vì tất cả có thể cùng đọc sai.</p>
<button onclick="dl()">Tải CSV</button>
{"".join(blocks)}
<script>
function dl(){{
  let out = "key,plate_text\\n";
  document.querySelectorAll("input[data-key]").forEach(i => {{
    if (i.value.trim()) out += i.dataset.key + "," + i.value.trim().toUpperCase() + "\\n";
  }});
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([out], {{type:"text/csv"}}));
  a.download = "scene_labels.csv"; a.click();
}}
</script>""",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
