"""
proper_eval.py
Full-pipeline artwork recognition evaluation.

Dataset : backend/data/imagedata/images/images  (same Kaggle source as FAISS index)
Metric  : Artist-level Top-1 accuracy  (in-distribution)
Pipeline: CLIP+FAISS + Gemini Vision + Google Web Detection + OCR
          Roboflow crop activated if ROBOFLOW_API_KEY is set.

NOTE: Test images are drawn from the same dataset used to build the FAISS index
      (in-distribution evaluation). This measures retrieval performance under
      real pipeline conditions, not zero-shot generalisation to unseen artworks.
"""

import os
import random
import asyncio
import json
import sys
import time
from io import BytesIO
from datetime import datetime

import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, r"C:\Users\Home\OneDrive\Desktop\Inner Gallery\backend")

# ── Monkey-patch: skip Gemini calls (credits depleted) ────────────────────────
# Only CLIP+FAISS + Google Web Detection + OCR are active.
import modules.llm_generator as _llm

def _stub_essay(*args, **kwargs):
    return '{"title":"[eval]","body":[],"questions":[],"comfort":""}'

def _stub_similar(*args, **kwargs):
    return []

def _stub_vision(*args, **kwargs):
    return _llm._EMPTY_VISION

_llm.generate_interpretation = _stub_essay
_llm.recommend_similar       = _stub_similar
_llm.analyze_artwork_vision  = _stub_vision

import backend.main as _main_mod
_main_mod.generate_interpretation = _stub_essay
_main_mod.recommend_similar       = _stub_similar
_main_mod.analyze_artwork_vision  = _stub_vision  # patch the name bound at import

from main import analyze

IMAGE_DIR   = r"C:\Users\Home\OneDrive\Desktop\Inner Gallery\backend\data\imagedata\images\images"
NUM_SAMPLES = 100
TIMEOUT_SEC = 90        # Gemini + Web Detection 포함 충분한 여유
RANDOM_SEED = 42        # 재현 가능한 샘플링
RESULT_FILE = "proper_eval_results.txt"
DETAIL_FILE = "proper_eval_details.json"


def get_random_images(n: int, seed: int) -> list:
    random.seed(seed)
    artists = [
        a for a in os.listdir(IMAGE_DIR)
        if os.path.isdir(os.path.join(IMAGE_DIR, a))
    ]
    seen, images = set(), []
    attempts = 0
    while len(images) < n and attempts < n * 10:
        attempts += 1
        artist    = random.choice(artists)
        artist_dir = os.path.join(IMAGE_DIR, artist)
        files = [
            f for f in os.listdir(artist_dir)
            if f.lower().endswith((".jpg", ".jpeg", ".png"))
        ]
        if not files:
            continue
        file = random.choice(files)
        key  = os.path.join(artist, file)
        if key in seen:
            continue
        seen.add(key)
        images.append({
            "path":        os.path.join(artist_dir, file),
            "true_artist": artist.replace("_", " "),
        })
    return images


class MockUploadFile:
    def __init__(self, filename: str, content: bytes):
        self.filename = filename
        self._content = content

    async def read(self):
        return self._content


def is_correct(true_artist: str, pred_artist: str) -> bool:
    t = true_artist.lower().replace(" ", "")
    p = pred_artist.lower().replace(" ", "")
    return len(p) > 1 and (t in p or p in t)


async def main():
    images = get_random_images(NUM_SAMPLES, RANDOM_SEED)

    active_apis = {
        "Gemini Vision": "OFF (credits depleted, stubbed)",
        "Roboflow":      "ON" if os.environ.get("ROBOFLOW_API_KEY") else "OFF",
        "GCV WebDetect": "ON" if os.environ.get("GOOGLE_CLOUD_VISION_KEY") else "OFF (cache only)",
    }
    api_str = " | ".join(f"{k}={v}" for k, v in active_apis.items())

    print(f"[proper_eval] {len(images)} samples  seed={RANDOM_SEED}  timeout={TIMEOUT_SEC}s")
    print(f"APIs: {api_str}")
    print("=" * 65, flush=True)

    results   = []
    start_all = time.time()

    for i, img_info in enumerate(images):
        safe_artist = img_info['true_artist'].encode('ascii', 'replace').decode('ascii')
        label = f"[{i+1:03d}/{len(images)}] {safe_artist}"
        print(f"{label:<55}", end="", flush=True)
        t0 = time.time()

        try:
            with open(img_info["path"], "rb") as f:
                content = f.read()

            result = await asyncio.wait_for(
                analyze(
                    image=MockUploadFile(os.path.basename(img_info["path"]), content),
                    mode="standard",
                    hint_title=None,
                    hint_artist=None,
                    artwork_type="회화",
                    analysis_focus="전체",
                    artwork_description="",
                    user_identity_provided=False,
                ),
                timeout=TIMEOUT_SEC,
            )

            pred_artist = (result.get("info", {}).get("artist") or "").strip()
            pred_title  = (result.get("info", {}).get("title")  or "").strip()
            status      = result.get("identification_status", "unknown")
            correct     = is_correct(img_info["true_artist"], pred_artist)
            elapsed     = round(time.time() - t0, 1)

            mark = "O" if correct else "X"
            print(f"{mark} [{status}]  pred='{pred_artist}'  ({elapsed}s)", flush=True)

            results.append({
                "idx":         i + 1,
                "true_artist": img_info["true_artist"],
                "pred_artist": pred_artist,
                "pred_title":  pred_title,
                "status":      status,
                "correct":     correct,
                "elapsed":     elapsed,
            })

        except asyncio.TimeoutError:
            print(f"TIMEOUT ({TIMEOUT_SEC}s)", flush=True)
            results.append({
                "idx": i + 1, "true_artist": img_info["true_artist"],
                "pred_artist": "", "pred_title": "",
                "status": "timeout", "correct": False,
                "elapsed": TIMEOUT_SEC,
            })

        except Exception as e:
            err = str(e).encode("ascii", "ignore").decode()[:80]
            print(f"ERROR: {err}", flush=True)
            results.append({
                "idx": i + 1, "true_artist": img_info["true_artist"],
                "pred_artist": "", "pred_title": "",
                "status": "error", "correct": False,
                "elapsed": round(time.time() - t0, 1),
            })

    # ── Statistics ─────────────────────────────────────────────────────────────
    wall_min  = (time.time() - start_all) / 60
    valid     = [r for r in results if r["status"] not in ("error", "timeout")]
    errors    = [r for r in results if r["status"] == "error"]
    timeouts  = [r for r in results if r["status"] == "timeout"]

    by_status = {}
    for r in valid:
        by_status.setdefault(r["status"], []).append(r)

    def acc_str(subset):
        if not subset:
            return "0/0 (—)"
        n_correct = sum(1 for r in subset if r["correct"])
        return f"{n_correct}/{len(subset)} ({100 * n_correct / len(subset):.1f}%)"

    lines = [
        "=" * 65,
        f"Full Pipeline Evaluation  —  {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"Samples : {len(results)}  |  Valid: {len(valid)}  |  "
        f"Errors: {len(errors)}  |  Timeouts: {len(timeouts)}",
        f"APIs    : {api_str}",
        f"Wall time: {wall_min:.1f} min  |  Avg/image: {wall_min*60/len(results):.1f}s",
        "=" * 65,
        "",
        "── Top-1 Artist Accuracy (valid samples only) ──",
        f"  전체          : {acc_str(valid)}",
        "",
        "── 판정 상태별 분포 및 정확도 ──",
    ]
    for status, items in sorted(by_status.items()):
        lines.append(f"  {status:<22}: {acc_str(items)}")

    lines += [
        "",
        "── 오답 케이스 ──",
    ]
    wrong = [r for r in valid if not r["correct"]]
    if wrong:
        for r in wrong:
            lines.append(
                f"  [{r['status']}]  true={r['true_artist']:<28}  pred={r['pred_artist']}"
            )
    else:
        lines.append("  (없음 — 전부 정답)")

    output = "\n".join(lines)
    print("\n" + output, flush=True)

    with open(RESULT_FILE, "w", encoding="utf-8") as f:
        f.write(output)
    with open(DETAIL_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n결과 저장: {RESULT_FILE} / {DETAIL_FILE}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
