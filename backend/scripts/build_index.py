#!/usr/bin/env python3
"""
One-time script to build the artwork CLIP+FAISS index.
Supports multiple zip files — place all zips in:  backend/artwork_sources/

Run:  python backend/scripts/build_index.py
      python backend/scripts/build_index.py --clean   (delete images after indexing)

Supported dataset structures (auto-detected):
  1. images/images/Artist_Name/*.jpg  + artists.csv   (Best Artworks of All Time)
  2. GOATs/ARTIST_NAME/*.jpg                          (Greatest Artists Of All Time)
  3. Any folder structure where the parent folder name is the artist
"""
import os, sys, json, zipfile, csv, argparse, shutil
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
from PIL import Image
from tqdm import tqdm

BACKEND_DIR   = PROJECT_ROOT / "backend"
SOURCES_DIR   = BACKEND_DIR  / "artwork_sources"
LEGACY_ZIP    = BACKEND_DIR  / "artwork_source.zip"   # old single-file path
EXTRACT_DIR   = BACKEND_DIR  / "artwork_index" / "_images"
INDEX_DIR     = BACKEND_DIR  / "artwork_index"

BATCH_SIZE = 32


# ── Artist name normalisation ─────────────────────────────────────────────────

def normalise(folder: str) -> str:
    """
    Vincent_van_Gogh  ->  Vincent van Gogh
    FRIDA_KAHLO       ->  Frida Kahlo
    GOATs             ->  (skip)
    """
    name = folder.replace("_", " ").strip()
    if name.upper() == name:          # all-caps dataset (GOATs)
        name = name.title()
    return name


SKIP_FOLDERS = {"goats", "images", "_images", "__macosx", ".ds_store"}


# ── CSV loader ────────────────────────────────────────────────────────────────

def load_csv(extract_root: Path) -> dict[str, dict]:
    """Find artists.csv anywhere under extract_root; return {lowercase_name: info}."""
    csv_files = list(extract_root.rglob("*.csv"))
    if not csv_files:
        return {}
    with open(csv_files[0], encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        out = {}
        for row in reader:
            name = (row.get("name") or "").strip()
            if not name:
                continue
            bio = (row.get("bio") or "")[:300]
            out[name.lower()] = {
                "name":        name,
                "genre":       (row.get("genre")       or "").strip(),
                "nationality": (row.get("nationality") or "").strip(),
                "years":       (row.get("years")       or "").strip(),
                "bio":         bio,
            }
    print(f"    CSV: {len(out)} artists loaded from {csv_files[0].name}")
    return out


# ── Image file discovery ──────────────────────────────────────────────────────

def find_images(extract_root: Path) -> list[tuple[Path, str]]:
    """
    Walk the extracted directory and return (image_path, artist_folder_name).
    Skips infrastructure folders (images/, GOATs/, etc.).
    """
    results = []
    for jpg in sorted(extract_root.rglob("*.jpg")):
        artist_folder = jpg.parent.name
        if artist_folder.lower() in SKIP_FOLDERS:
            # image stored one level too high — try grandparent
            artist_folder = jpg.parent.parent.name
        if artist_folder.lower() in SKIP_FOLDERS:
            continue
        results.append((jpg, artist_folder))
    return results


# ── Batch embedding flush ─────────────────────────────────────────────────────

def flush(model, imgs, metas, all_embs, all_metas):
    if not imgs:
        return
    embs = model.encode(imgs, batch_size=len(imgs),
                        show_progress_bar=False, convert_to_numpy=True)
    norms = np.linalg.norm(embs, axis=1, keepdims=True)
    embs  = embs / np.where(norms == 0, 1, norms)
    all_embs.extend(embs)
    all_metas.extend(metas)
    imgs.clear()
    metas.clear()


# ── Main ──────────────────────────────────────────────────────────────────────

def collect_zips() -> list[Path]:
    zips = []
    # New: sources directory
    if SOURCES_DIR.exists():
        zips += sorted(SOURCES_DIR.glob("*.zip"))
    # Legacy: single file at backend/artwork_source.zip
    if LEGACY_ZIP.exists() and LEGACY_ZIP not in zips:
        zips.append(LEGACY_ZIP)
    return zips


def build_index(clean_after: bool = False):
    zips = collect_zips()
    if not zips:
        print("No zip files found.")
        print(f"Place zip files in:  {SOURCES_DIR}")
        print(f"  (or the legacy path: {LEGACY_ZIP})")
        sys.exit(1)

    print(f"Found {len(zips)} zip file(s):")
    for z in zips:
        print(f"  {z.name}  ({z.stat().st_size / 1e9:.2f} GB)")

    # ── Extract all zips ───────────────────────────────────────────────────────
    EXTRACT_DIR.mkdir(parents=True, exist_ok=True)

    # Shared CSV data (enriched from any zip that has a CSV)
    csv_data: dict[str, dict] = {}

    for z in zips:
        dest = EXTRACT_DIR / z.stem
        if dest.exists() and any(dest.rglob("*.jpg")):
            print(f"\n[{z.name}] Already extracted — skipping.")
        else:
            print(f"\n[{z.name}] Extracting…")
            dest.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(z, "r") as zf:
                zf.extractall(dest)
            print(f"  Done.")
        csv_data.update(load_csv(dest))

    # ── Collect all images ────────────────────────────────────────────────────
    print("\nScanning for images…")
    all_images: list[tuple[Path, str]] = []
    for z in zips:
        dest = EXTRACT_DIR / z.stem
        found = find_images(dest)
        print(f"  {z.name}: {len(found)} images")
        all_images.extend(found)

    total = len(all_images)
    print(f"Total: {total} images")
    if total == 0:
        print("Error: no .jpg files found. Check zip structure.")
        sys.exit(1)

    # Artist summary
    artist_counts: dict[str, int] = defaultdict(int)
    for _, folder in all_images:
        artist_counts[normalise(folder)] += 1
    print(f"Artists: {len(artist_counts)}  (top 5: {', '.join(list(artist_counts)[:5])}…)")

    # ── Load CLIP model ────────────────────────────────────────────────────────
    print("\nLoading CLIP model (first run downloads ~400 MB)…")
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print("Run:  pip install sentence-transformers faiss-cpu tqdm pillow")
        sys.exit(1)
    model = SentenceTransformer("clip-ViT-B-32")
    print("  Model ready.")

    # ── Embed ─────────────────────────────────────────────────────────────────
    est = max(1, total // 600)
    print(f"\nEmbedding {total} images (~{est}–{est*3} min on CPU)…")

    all_embs:  list[np.ndarray] = []
    all_metas: list[dict]       = []
    batch_imgs:  list[Image.Image] = []
    batch_metas: list[dict]        = []
    failed = 0

    for jpg_path, folder_name in tqdm(all_images, desc="Embedding", unit="img"):
        try:
            img = Image.open(jpg_path).convert("RGB")
            img.thumbnail((224, 224), Image.LANCZOS)
        except Exception:
            failed += 1
            continue

        artist_name = normalise(folder_name)
        # Enrich from CSV if available (match by lowercase name)
        csv_info = csv_data.get(artist_name.lower(), {})

        batch_imgs.append(img)
        batch_metas.append({
            "artist":      csv_info.get("name", artist_name),
            "genre":       csv_info.get("genre",       ""),
            "nationality": csv_info.get("nationality", ""),
            "years":       csv_info.get("years",       ""),
            "bio":         csv_info.get("bio",         ""),
        })

        if len(batch_imgs) >= BATCH_SIZE:
            flush(model, batch_imgs, batch_metas, all_embs, all_metas)

    flush(model, batch_imgs, batch_metas, all_embs, all_metas)

    if failed:
        print(f"  {failed} images skipped (could not open).")

    # ── FAISS index ───────────────────────────────────────────────────────────
    print("Building FAISS index…")
    try:
        import faiss
    except ImportError:
        print("Run:  pip install faiss-cpu")
        sys.exit(1)

    emb_array = np.array(all_embs, dtype=np.float32)
    dim = emb_array.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(emb_array)

    # ── Save ──────────────────────────────────────────────────────────────────
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(INDEX_DIR / "index.faiss"))
    with open(INDEX_DIR / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(all_metas, f, ensure_ascii=False)
    with open(INDEX_DIR / "index_info.json", "w") as f:
        json.dump({"dim": dim, "count": len(all_embs),
                   "model": "clip-ViT-B-32",
                   "sources": [z.name for z in zips],
                   "artists": len(artist_counts)}, f, indent=2)

    size_mb = (INDEX_DIR / "index.faiss").stat().st_size / 1e6
    print(f"\nDone!")
    print(f"  {len(all_embs)} vectors  |  {len(artist_counts)} artists  |  dim={dim}")
    print(f"  index.faiss: {size_mb:.0f} MB")

    if clean_after:
        shutil.rmtree(EXTRACT_DIR)
        print(f"  Cleaned extracted images.")
    else:
        print(f"\nTip: delete {EXTRACT_DIR} to free disk space after confirming the index works.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--clean", action="store_true",
                        help="Delete extracted images after indexing")
    args = parser.parse_args()
    build_index(clean_after=args.clean)
