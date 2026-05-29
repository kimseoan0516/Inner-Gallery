"""
Artwork era context lookup from JSON DB.
Search priority: artwork_id → title+artist → title-only → artist-only
"""
import json
import pathlib
import re
from typing import Optional, Dict, Any

_DB_PATH = pathlib.Path(__file__).parent.parent / "backend" / "data" / "artwork_era_db.json"
_db: Optional[Dict] = None


def _load() -> Dict:
    global _db
    if _db is None:
        _db = json.loads(_db_PATH.read_text(encoding="utf-8")) if (_db_PATH := _DB_PATH).exists() else {"artworks": [], "artists": []}
    return _db


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def _normalize(title: str) -> str:
    return re.sub(r"\s+", " ", title.strip().lower())


def lookup_artwork(
    title: str = "",
    artist: str = "",
    artwork_id: str = "",
) -> Optional[Dict[str, Any]]:
    """
    Search order:
    1. artwork_id exact match
    2. title + artist (both normalized)
    3. title only (normalized)
    Returns the DB entry dict or None.
    """
    db = _load()
    artworks = db.get("artworks", [])

    # 1. artwork_id
    if artwork_id:
        for a in artworks:
            if a.get("artwork_id") == artwork_id:
                return a

    title_n  = _normalize(title)
    artist_n = _normalize(artist)

    # 2. title + artist
    if title_n and artist_n:
        for a in artworks:
            if _normalize(a.get("title", "")) == title_n and _normalize(a.get("artist", "")) == artist_n:
                return a
        # alias check
        for a in artworks:
            aliases = [_normalize(x) for x in a.get("title_aliases", [])]
            if title_n in aliases and _normalize(a.get("artist", "")) == artist_n:
                return a

    # 3. title only
    if title_n:
        for a in artworks:
            if _normalize(a.get("title", "")) == title_n:
                return a
        for a in artworks:
            aliases = [_normalize(x) for x in a.get("title_aliases", [])]
            if title_n in aliases:
                return a

    return None


def lookup_artist(artist: str = "") -> Optional[Dict[str, Any]]:
    """Search artists DB by name (normalized) or alias."""
    if not artist:
        return None
    db = _load()
    artist_n = _normalize(artist)
    for a in db.get("artists", []):
        if _normalize(a.get("name", "")) == artist_n:
            return a
        for alias in a.get("name_aliases", []):
            if _normalize(alias) == artist_n:
                return a
    return None


def era_response_from_artwork(entry: Dict, confidence_label: str) -> Dict[str, Any]:
    """Build the API response dict from a verified artwork DB entry."""
    return {
        "confidence_label":   confidence_label,
        "creation_period":    entry.get("creation_period",    ""),
        "art_movement":       entry.get("art_movement",       ""),
        "historical_context": entry.get("historical_context", ""),
        "artist_context":     entry.get("artist_context",     ""),
        "visual_connection":  entry.get("visual_connection",  ""),
        "_source": "verified_db",
    }


def era_response_from_artist(entry: Dict, title: str, confidence_label: str) -> Dict[str, Any]:
    """Build a partial response from an artist DB entry (no artwork-specific data)."""
    return {
        "confidence_label":   confidence_label,
        "creation_period":    "",
        "art_movement":       entry.get("art_movement", ""),
        "historical_context": "",
        "artist_context":     entry.get("artist_context", ""),
        "visual_connection":  "",
        "_source": "artist_db",
    }


def visual_only_response() -> Dict[str, Any]:
    """
    Returned when identification_status == 'unknown'.
    No historical claims — only a note explaining the limitation.
    """
    return {
        "confidence_label":   "정보 없음",
        "creation_period":    "",
        "art_movement":       "",
        "historical_context": "",
        "artist_context":     "",
        "visual_connection":  "",
        "_no_era": True,
        "_source": "none",
    }


def not_in_db_response(title: str, artist: str, confidence_label: str) -> Dict[str, Any]:
    """
    Returned when status is confirmed/partial but artwork is not in the verified DB.
    Signals the frontend to show a 'preparing' message instead of hallucinated content.
    """
    return {
        "confidence_label":   confidence_label,
        "creation_period":    "",
        "art_movement":       "",
        "historical_context": "",
        "artist_context":     "",
        "visual_connection":  "",
        "_not_in_db": True,
        "_title":  title,
        "_artist": artist,
        "_source": "none",
    }
