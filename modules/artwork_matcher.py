"""
artwork_matcher — CLIP + FAISS 기반 작품 유사도 검색.
인덱스가 없으면 조용히 None 반환 (non-fatal).
"""
import json, io, unicodedata
from pathlib import Path
from typing import Optional

import numpy as np

_INDEX_DIR = Path(__file__).resolve().parent.parent / "backend" / "artwork_index"

_index    = None
_metadata: list[dict] | None = None
_model    = None
_ready    = False
_checked  = False

# 인덱스 빌드 시 폴더명이 잘못 작가명으로 들어간 케이스 필터
_INVALID_ARTISTS = {
    "resized", "images", "_images", "goats", "thumbnails",
    "small", "large", "medium", "original", "backup",
    "__macosx", ".ds_store", "dataset", "data",
}

def _is_valid_artist(name: str) -> bool:
    return name.lower() not in _INVALID_ARTISTS and len(name) > 2


def is_available() -> bool:
    global _checked
    if not _checked:
        _checked = True
    return (
        (_INDEX_DIR / "index.faiss").exists() and
        (_INDEX_DIR / "metadata.json").exists()
    )


def _load():
    global _index, _metadata, _model, _ready
    if _ready:
        return
    if not is_available():
        return

    import faiss
    from sentence_transformers import SentenceTransformer

    print("[ArtworkMatcher] Loading CLIP model…", flush=True)
    _model = SentenceTransformer("clip-ViT-B-32")
    _index = faiss.read_index(str(_INDEX_DIR / "index.faiss"))

    with open(_INDEX_DIR / "metadata.json", encoding="utf-8") as f:
        raw_meta = json.load(f)

    _metadata = []
    for m in raw_meta:
        m2 = dict(m)
        m2["artist"] = unicodedata.normalize("NFC", m.get("artist", ""))
        m2["_valid"] = _is_valid_artist(m2["artist"])
        _metadata.append(m2)

    _ready = True
    print(f"[ArtworkMatcher] Ready — {_index.ntotal} artworks indexed", flush=True)


def top_k_artists(image_bytes: bytes, k: int = 5, min_sim: float = 0.55) -> list[dict]:
    """quick-match 미리보기용 — 느슨한 임계값으로 화가 후보 반환."""
    if not is_available():
        return []
    _load()
    if not _ready:
        return []

    from PIL import Image
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img.thumbnail((224, 224), Image.LANCZOS)
    except Exception:
        return []

    emb  = _model.encode([img], show_progress_bar=False, convert_to_numpy=True)
    norm = np.linalg.norm(emb, axis=1, keepdims=True)
    emb  = emb / np.where(norm == 0, 1, norm)

    # invalid 항목 제거를 감안해 넉넉하게 60개 검색
    D, I = _index.search(emb.astype(np.float32), 60)

    artist_best:  dict[str, float] = {}
    artist_count: dict[str, int]   = {}
    artist_info:  dict[str, dict]  = {}

    for sim, idx in zip(D[0], I[0]):
        if sim < min_sim or idx < 0 or idx >= len(_metadata):
            continue
        meta   = _metadata[idx]
        if not meta.get("_valid", True):
            continue
        artist = meta["artist"]
        if sim > artist_best.get(artist, 0.0):
            artist_best[artist] = float(sim)
        artist_count[artist] = artist_count.get(artist, 0) + 1
        if artist not in artist_info:
            artist_info[artist] = meta

    return [
        {
            "artist":      a,
            "genre":       artist_info[a].get("genre", ""),
            "nationality": artist_info[a].get("nationality", ""),
            "years":       artist_info[a].get("years", ""),
            "confidence":  round(artist_best[a] * 100),
            "vote_count":  artist_count[a],
        }
        for a, _ in sorted(artist_best.items(), key=lambda x: x[1], reverse=True)[:k]
    ]


def match_artwork(image_bytes: bytes, top_k: int = 12, threshold: float = 0.78, vote_min: int = 2) -> Optional[dict]:
    """
    CLIP 인덱스로 업로드 이미지 매칭.
    threshold 이상 + vote_min 이상의 동일 작가 hit이 있어야 반환.
    """
    if not is_available():
        return None
    _load()
    if not _ready:
        return None

    from PIL import Image
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img.thumbnail((224, 224), Image.LANCZOS)
    except Exception:
        return None

    emb  = _model.encode([img], show_progress_bar=False, convert_to_numpy=True)
    norm = np.linalg.norm(emb, axis=1, keepdims=True)
    emb  = emb / np.where(norm == 0, 1, norm)

    D, I    = _index.search(emb.astype(np.float32), top_k)
    scores  = D[0]
    indices = I[0]

    if scores[0] < threshold:
        return None

    # 최고 유사도의 88% 이상인 hit만 투표에 포함
    vote_threshold = threshold * 0.88
    artist_score: dict[str, float] = {}
    artist_count: dict[str, int]   = {}
    artist_info:  dict[str, dict]  = {}

    for sim, idx in zip(scores, indices):
        if sim < vote_threshold or idx < 0 or idx >= len(_metadata):
            continue
        meta   = _metadata[idx]
        if not meta.get("_valid", True):
            continue
        artist = meta["artist"]
        artist_score[artist] = artist_score.get(artist, 0.0) + float(sim)
        artist_count[artist] = artist_count.get(artist, 0)   + 1
        if artist not in artist_info:
            artist_info[artist] = meta

    qualified = {a: s for a, s in artist_score.items() if artist_count[a] >= vote_min}
    if not qualified:
        return None

    best   = max(qualified, key=lambda a: qualified[a])
    info   = artist_info[best]

    return {
        "artist":      info["artist"],
        "genre":       info["genre"],
        "nationality": info["nationality"],
        "years":       info["years"],
        "bio_short":   (info.get("bio") or "")[:200],
        "confidence":  round(float(scores[0]), 3),
        "vote_count":  artist_count[best],
    }
