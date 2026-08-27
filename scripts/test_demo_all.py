"""Script test toàn bộ tệp hình ảnh và video trong thư mục demo/ qua ALPR API."""

import json
import os
import time
from pathlib import Path

import requests

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8001/api")
REPO_ROOT = Path(__file__).resolve().parents[1]
DEMO_DIR = REPO_ROOT / "demo"
ANH_HOP_LE = (".jpg", ".jpeg", ".png", ".webp")
VIDEO_HOP_LE = (".mp4", ".avi", ".mov", ".mkv")


def test_images(img_dir: Path, expected_file: Path | None = None):
    print("\n=======================================================")
    print(f"TEST HÌNH ẢNH TRONG: {img_dir.relative_to(REPO_ROOT)}")
    print("=======================================================")

    expected_map = {}
    if expected_file and expected_file.exists():
        with open(expected_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                for item in data:
                    expected_map[item["file"]] = item.get("plates", [])
            elif isinstance(data, dict):
                for k, v in data.items():
                    expected_map[k] = v

    image_files = sorted(
        f for f in img_dir.iterdir() if f.suffix.lower() in ANH_HOP_LE
    )

    total_imgs = len(image_files)
    total_detected_plates = 0
    total_time = 0.0

    print(
        f"{'STT':<4} {'File':<28} {'Thời gian':<10} {'Số biển':<8} "
        f"{'Chi tiết biển số (Nhận dạng | Kỳ vọng)'}"
    )
    print("-" * 90)

    for idx, img_path in enumerate(image_files, 1):
        rel_path = img_path.name
        start_t = time.perf_counter()

        try:
            with open(img_path, "rb") as f:
                res = requests.post(f"{BASE_URL}/detect/image", files={"file": f}, timeout=60)
            elapsed = time.perf_counter() - start_t
            total_time += elapsed

            if res.status_code != 200:
                print(f"{idx:<4} {rel_path:<28} {elapsed:<9.2f}s ERROR ({res.status_code})")
                continue

            resp_json = res.json()
            plates = resp_json.get("results", [])
            total_detected_plates += len(plates)

            pred_strings = [p.get("plate_display") or p.get("plate_number") or "?" for p in plates]
            pred_text = ", ".join(pred_strings) if pred_strings else "(Không tìm thấy)"

            exp_items = expected_map.get(rel_path, [])
            exp_strings = []
            for item in exp_items:
                if isinstance(item, dict):
                    exp_strings.append(item.get("display") or item.get("plate") or "(null)")
            exp_text = f" [Kỳ vọng: {', '.join(exp_strings)}]" if exp_strings else ""

            print(
                f"{idx:<4} {rel_path:<28} {elapsed:<9.2f}s "
                f"{len(plates):<8} {pred_text}{exp_text}"
            )

        except Exception as err:
            print(f"{idx:<4} {rel_path:<28} EXCEPTION: {err}")

    avg_time = total_time / total_imgs if total_imgs > 0 else 0
    print("-" * 90)
    print(
        f"Tổng kết {img_dir.name}: {total_imgs} ảnh | "
        f"{total_detected_plates} biển phát hiện | TB {avg_time:.3f}s/ảnh"
    )


def test_videos(video_dir: Path | None = None):
    target_dir = video_dir or (DEMO_DIR / "videos")
    if not target_dir.exists():
        target_dir = DEMO_DIR

    print("\n=======================================================")
    print(f"TEST VIDEO TRONG: {target_dir.relative_to(REPO_ROOT)}")
    print("=======================================================")

    video_files = sorted(
        f for f in target_dir.iterdir() if f.suffix.lower() in VIDEO_HOP_LE
    )

    for idx, vid_path in enumerate(video_files, 1):
        print(
            f"\n[{idx}/{len(video_files)}] Đang gửi video: {vid_path.name} "
            f"({vid_path.stat().st_size / 1e6:.1f} MB)..."
        )
        start_t = time.perf_counter()

        try:
            with open(vid_path, "rb") as f:
                res = requests.post(f"{BASE_URL}/detect/video", files={"file": f}, timeout=300)
            elapsed = time.perf_counter() - start_t

            if res.status_code not in [200, 202]:
                print(f"  --> Lỗi HTTP {res.status_code}: {res.text[:200]}")
                continue

            resp_json = res.json()
            job_id = resp_json.get("job_id") or resp_json.get("id")
            status = resp_json.get("status")
            print(
                f"  --> Đã khởi tạo Video Job: ID={job_id}, Status={status} "
                f"(Thời gian gửi: {elapsed:.2f}s)"
            )

            # Polling kết quả job
            poll_count = 0
            while poll_count < 60:
                time.sleep(2)
                poll_count += 1
                try:
                    poll_res = requests.get(f"{BASE_URL}/jobs/{job_id}", timeout=10)
                except requests.RequestException:
                    continue

                if poll_res.status_code == 200:
                    job_data = poll_res.json()
                    job_status = job_data.get("status")
                    progress = job_data.get("progress", 0.0)
                    print(
                        f"      Polling ({poll_count*2}s): status={job_status}, "
                        f"progress={progress*100:.1f}%",
                        end="\r",
                    )

                    if job_status == "completed":
                        total_vid_time = job_data.get("processing_time", 0.0)
                        processed_frames = job_data.get("processed_frames", 0)
                        total_frames = job_data.get("total_frames", 0)

                        # Job KHONG mang theo danh sach bien — no chi dem
                        # (`detection_count`). Muon tung bien thi hoi lich su,
                        # loc theo job.
                        results = []
                        try:
                            page_no = 1
                            while page_no <= 20:
                                hist = requests.get(
                                    f"{BASE_URL}/history",
                                    params={
                                        "job_id": job_id,
                                        "page": page_no,
                                        "page_size": 100,
                                    },
                                    timeout=30,
                                )
                                if hist.status_code != 200:
                                    print(f"\n  (API lich su tra HTTP {hist.status_code})")
                                    break
                                body = hist.json()
                                results.extend(body.get("items", []))
                                if not body.get("has_next"):
                                    break
                                page_no += 1
                        except requests.RequestException as hist_err:
                            print(f"\n  (khong lay duoc lich su cua job: {hist_err})")

                        unique_plates = sorted(list(set(
                            r.get("plate_display") or r.get("plate_number")
                            for r in results
                            if r.get("plate_display") or r.get("plate_number")
                        )))

                        print(f"\n  [HOÀN TẤT VIDEO] {vid_path.name}:")
                        print(f"    - Tổng thời gian xử lý  : {total_vid_time:.2f}s")
                        print(f"    - Số frame đã quét      : {processed_frames}/{total_frames}")
                        print(
                            f"    - Số biển phát hiện     : {len(results)} "
                            f"bản ghi ({len(unique_plates)} biển duy nhất)"
                        )
                        con_nua = "..." if len(unique_plates) > 10 else ""
                        print(
                            f"    - Các biển số duy nhất  : "
                            f"{', '.join(unique_plates[:10])}{con_nua}"
                        )
                        break
                    elif job_status == "failed":
                        print(
                            f"\n  [THẤT BẠI] Job {job_id} bị lỗi: "
                            f"{job_data.get('error_message')}"
                        )
                        break

        except Exception as err:
            print(f"  --> Ném ngoại lệ khi test video: {err}")


if __name__ == "__main__":
    expected_file = DEMO_DIR / "expected.json"
    if (DEMO_DIR / "1-line").exists():
        test_images(DEMO_DIR / "1-line", expected_file)
    if (DEMO_DIR / "2-line").exists():
        test_images(DEMO_DIR / "2-line", expected_file)
    if (DEMO_DIR / "multi-plate").exists():
        test_images(DEMO_DIR / "multi-plate", expected_file)
    test_videos(DEMO_DIR / "videos")
