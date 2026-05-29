import re
import cv2
import numpy as np
from typing import Dict, Optional


def extract_artwork_info(image: np.ndarray) -> Dict[str, Optional[str]]:
    """
    Try to extract artwork metadata from text found in the image (e.g. museum captions).
    Returns best-effort fields; None for fields that could not be extracted.
    """
    result: Dict[str, Optional[str]] = {
        "title": None,
        "artist": None,
        "year": None,
        "medium": None,
        "museum": None,
        "raw_text": None,
    }

    # Focus on bottom 25% where captions typically appear
    h = image.shape[0]
    caption_region = image[int(h * 0.75):, :]

    full_text = _run_ocr(caption_region)
    if not full_text:
        full_text = _run_ocr(image)  # try full image as fallback
    if not full_text:
        return result

    result["raw_text"] = full_text.strip()

    year_m = re.search(r"\b(1[4-9]\d{2}|20[0-2]\d)\b", full_text)
    if year_m:
        result["year"] = year_m.group()

    medium_kw = [
        "oil on canvas", "watercolor", "tempera", "acrylic", "oil", "pastel", "ink",
        "캔버스에 유채", "수채화", "템페라", "유채", "수채",
    ]
    for kw in medium_kw:
        if kw.lower() in full_text.lower():
            result["medium"] = kw
            break

    museum_kw = [
        "museum", "gallery", "louvre", "uffizi", "moma", "tate", "metropolitan",
        "박물관", "미술관", "갤러리",
    ]
    for kw in museum_kw:
        if kw.lower() in full_text.lower():
            idx = full_text.lower().find(kw.lower())
            result["museum"] = full_text[max(0, idx - 10): idx + len(kw) + 20].strip()
            break

    lines = [l.strip() for l in full_text.splitlines() if l.strip()]
    if lines:
        result["title"] = lines[0][:120]

    return result


def _run_ocr(image: np.ndarray) -> str:
    try:
        import easyocr  # optional heavy dependency
        reader = easyocr.Reader(["ko", "en"], gpu=False, verbose=False)
        texts = reader.readtext(image, detail=0)
        return " ".join(texts)
    except ImportError:
        pass
    except Exception:
        pass

    # Fallback: try Tesseract if available
    try:
        import pytesseract
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return pytesseract.image_to_string(gray, lang="kor+eng")
    except Exception:
        pass

    return ""
