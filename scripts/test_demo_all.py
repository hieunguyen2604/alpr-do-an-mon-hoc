"""Script test toàn bộ tệp hình ảnh và video trong thư mục demo/ qua ALPR API."""

import json
import time
import requests
from pathlib import Path

BASE_URL = "http://localhost:8000/api"
REPO_ROOT = Path(__file__).resolve().parents[1]
DEMO_DIR = REPO_ROOT / "demo"


def test_images(img_dir: Path, expected_file: Path | None = None):
    print(f"\n=======================================================")
    print(f"TEST HÌNH ẢNH TRONG: {img_dir.relative_to(REPO_ROOT)}")
    print(f"=======================================================")

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

    image_files = sorted([f for f in img_dir.iterdir() if f.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]])
    
    total_imgs = len(image_files)
    total_detected_plates = 0
    total_time = 0.0

    print(f"{'STT':<4} {'File':<28} {'Thời gian':<10} {'Số biển':<8} {'Chi tiết biển số (Nhận dạng | Kỳ vọng)'}")
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

            print(f"{idx:<4} {rel_path:<28} {elapsed:<9.2f}s {len(plates):<8} {pred_text}{exp_text}")

        except Exception as err:
            print(f"{idx:<4} {rel_path:<28} EXCEPTION: {err}")

    avg_time = total_time / total_imgs if total_imgs > 0 else 0
    print("-" * 90)
    print(f"Tổng kết {img_dir.name}: {total_imgs} ảnh | {total_detected_plates} biển phát hiện | TB {avg_time:.3f}s/ảnh")


def test_videos():
    print(f"\n=======================================================")
    print(f"TEST VIDEO TRONG: demo/")
    print(f"=======================================================")

    video_files = sorted([f for f in DEMO_DIR.iterdir() if f.suffix.lower() in [".mp4", ".avi", ".mov", ".mkv"]])

    for idx, vid_path in enumerate(video_files, 1):
        print(f"\n[{idx}/{len(video_files)}] Đang gửi video: {vid_path.name} ({vid_path.stat().st_size / 1e6:.1f} MB)...")
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
            print(f"  --> Đã khởi tạo Video Job: ID={job_id}, Status={status} (Thời gian gửi: {elapsed:.2f}s)")



            # Polling kết quả job
            poll_count = 0
            while poll_count < 60:
                time.sleep(2)
                poll_count += 1
                job_res = requests.get(f"{BASE_URL}/jobs/{job_id}", timeout=10)
                if job_res.status_code == 200:
                    job_data = job_res.json()
                    job_status = job_data.get("status")
                    progress = job_data.get("progress_percent", 0)
                    print(f"      Polling ({poll_count * 2}s): status={job_status}, progress={progress:.1f}%", end="\r")

                    if job_status == "completed":
                        total_vid_time = time.perf_counter() - start_t
                        results = job_data.get("results", [])
                        total_frames = job_data.get("total_frames", 0)
                        processed_frames = job_data.get("processed_frames", 0)
                        
                        unique_plates = sorted(list(set(
                            r.get("plate_display") or r.get("plate_number") 
                            for r in results 
                            if r.get("plate_display") or r.get("plate_number")
                        )))

                        print(f"\n  [HOÀN TẤT VIDEO] {vid_path.name}:")
                        print(f"    - Tổng thời gian xử lý  : {total_vid_time:.2f}s")
                        print(f"    - Số frame đã quét      : {processed_frames}/{total_frames}")
                        print(f"    - Số biển phát hiện     : {len(results)} bản ghi ({len(unique_plates)} biển duy nhất)")
                        print(f"    - Các biển số duy nhất  : {', '.join(unique_plates[:10])}{'...' if len(unique_plates) > 10 else ''}")
                        break
                    elif job_status == "failed":
                        print(f"\n  [THẤT BẠI] Job {job_id} bị lỗi: {job_data.get('error_message')}")
                        break

        except Exception as err:
            print(f"  --> Ném ngoại lệ khi test video: {err}")


if __name__ == "__main__":
    test_images(DEMO_DIR / "images", DEMO_DIR / "images" / "expected.json")
    test_images(DEMO_DIR / "images-extra", DEMO_DIR / "images-extra" / "results.json")
    test_videos()
