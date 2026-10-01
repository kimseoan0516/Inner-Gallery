"""
Inner Gallery – FastAPI backend
Run: uvicorn backend.main:app --reload
"""
import sys, os, re, json, base64, datetime, unicodedata, requests
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

import cv2
import numpy as np
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Any, Optional

from modules.color_analyzer       import analyze_colors
from modules.composition_analyzer import analyze_composition
from modules.person_analyzer      import analyze_person
from modules.saliency_analyzer    import create_saliency_overlay, get_attention_center
from modules.emotion_scorer       import calculate_emotion_scores, scores_to_ko, EMOTION_KO
from modules.llm_generator        import generate_interpretation, analyze_artwork_vision, recommend_similar, generate_sketch_reflection, generate_docent_reply, generate_artwork_era, detect_web_artwork
from modules.quality_checker      import check_image_quality
from modules.artwork_matcher      import match_artwork, top_k_artists, is_available as matcher_available
from modules.era_lookup           import lookup_artwork
from backend.database             import init_db, get_journal, get_journal_entry, get_journal_thumbs, save_journal_entry, delete_journal_entry, update_journal_note, update_journal_sketch, update_journal_exhibition, get_random_quote
from backend.auth                 import router as auth_router, get_current_user

app = FastAPI(title="Inner Gallery API")
app.include_router(auth_router)
init_db()   # ensure all tables exist on startup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _j(obj):
    if isinstance(obj, np.integer): return int(obj)
    if isinstance(obj, np.floating): return float(obj)
    if isinstance(obj, np.ndarray): return obj.tolist()
    if isinstance(obj, dict):  return {k: _j(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)): return [_j(i) for i in obj]
    return obj


def _encode(img: np.ndarray, w: int, h: int, q: int = 85) -> str:
    oh, ow = img.shape[:2]
    if max(oh, ow) > max(w, h):
        s = max(w, h) / max(oh, ow)
        img = cv2.resize(img, (int(ow * s), int(oh * s)))
    _, buf = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, q])
    return base64.b64encode(buf.tobytes()).decode('ascii')


# ── 🔍 OCR 힌트 신뢰도 평가기 ──────────────────────────────────────────────────
def evaluate_ocr_hint(ocr_info: dict) -> dict:
    """
    Gemini OCR 결과에서 작품명/작가명 힌트를 추출하고 신뢰도를 평가합니다.

    Returns:
        {
            "hint_title":  str,          # 승격된 제목 힌트 (없으면 "")
            "hint_artist": str,          # 승격된 작가 힌트 (없으면 "")
            "ocr_confidence": str,       # "strong" | "partial" | "rejected"
            "ocr_source": str,           # 판단 이유 설명
        }
    """
    if not ocr_info:
        return {"hint_title": "", "hint_artist": "", "ocr_confidence": "rejected", "ocr_source": "OCR 데이터 없음"}

    raw_title  = (ocr_info.get("title",  "") or "").strip()
    raw_artist = (ocr_info.get("artist", "") or "").strip()
    raw_text   = (ocr_info.get("raw_text", "") or "").strip()

    # ── 거부 조건 1: 너무 긴 문자열은 설명문 가능성이 높음
    MAX_TITLE_LEN  = 80
    MAX_ARTIST_LEN = 50
    if len(raw_title) > MAX_TITLE_LEN:
        return {"hint_title": "", "hint_artist": "", "ocr_confidence": "rejected",
                "ocr_source": f"제목 문자열이 너무 길어 설명문으로 판단 ({len(raw_title)}자)"}
    if len(raw_artist) > MAX_ARTIST_LEN:
        raw_artist = ""   # 작가명만 차단하고 제목은 유지

    # ── 거부 조건 2: 설명문 패턴 감지 (동사·조사·마침표 포함)
    desc_patterns = [
        "이 작품", "그림은", "화가는", "제작된", "그려진", "소장",
        "미술관", "박물관", "전시", "컬렉션", "작품입니다", "입니다.",
        "합니다.", "있습니다", "was painted", "oil on canvas",
        "born in", "is a painting", "dated",
    ]
    combined = (raw_title + " " + raw_artist + " " + raw_text).lower()
    if any(p.lower() in combined for p in desc_patterns):
        return {"hint_title": "", "hint_artist": "", "ocr_confidence": "rejected",
                "ocr_source": "설명문 패턴 감지로 힌트 승격 거부"}

    # ── 거부 조건 3: OCR 결과가 전혀 없는 경우
    if not raw_title and not raw_artist:
        return {"hint_title": "", "hint_artist": "", "ocr_confidence": "rejected",
                "ocr_source": "제목·작가명 모두 미검출"}

    # ── 신뢰도 등급 판단
    #   strong: 제목+작가 둘 다 있음 → confirmed 수준으로 바로 승격
    #   partial: 둘 중 하나만 있음 → 가중치 힌트로만 사용
    has_title  = bool(raw_title)
    has_artist = bool(raw_artist)

    if has_title and has_artist:
        confidence  = "strong"
        source_note = f"라벨 OCR: 제목 '{raw_title}' + 작가명 '{raw_artist}' 동시 검출"
    elif has_title:
        confidence  = "partial"
        source_note = f"라벨 OCR: 제목 '{raw_title}' 단독 검출 (작가명 미확인)"
    else:
        confidence  = "partial"
        source_note = f"라벨 OCR: 작가명 '{raw_artist}' 단독 검출 (제목 미확인)"

    return {
        "hint_title":      raw_title,
        "hint_artist":     raw_artist,
        "ocr_confidence":  confidence,
        "ocr_source":      source_note,
    }


# ── 🎨 작품 유형 자동 감지 ───────────────────────────────────────────────────────
def auto_detect_artwork_type(vision_candidates: list, figure: dict, web_info: dict) -> str:
    """
    Gemini Vision recognition 결과, figure 분석, 웹 결과를 종합해
    artwork_type을 자동 판단합니다.

    Returns: "인물" | "풍경" | "추상" | "정물" | "건축" | "자동"
    """
    # 추상화 사조 키워드
    abstract_movements = [
        "abstract", "cubism", "expressionism", "surrealism",
        "fauvism", "minimalism", "abstract expressionism",
        "추상", "큐비즘", "초현실", "미니멀", "액션 페인팅", "데 스테일",
    ]
    # 풍경화 키워드
    landscape_keywords = [
        "landscape", "seascape", "countryside", "skyscape", "nature",
        "풍경", "바다", "산", "들판", "자연", "하늘",
    ]
    # 정물화 키워드
    still_life_keywords = [
        "still life", "vanitas", "flowers", "fruit", "vase",
        "정물", "꽃", "과일", "꽃다발",
    ]
    # 인물화 키워드
    portrait_keywords = [
        "portrait", "figure", "person", "woman", "man", "girl", "boy",
        "인물", "초상", "인상",
    ]
    # 건축/도시 키워드
    architecture_keywords = [
        "architecture", "cityscape", "building", "cathedral", "interior",
        "건축", "도시", "성당", "건물",
    ]

    # 모든 텍스트 소스 합치기
    text_sources = []
    for c in vision_candidates:
        text_sources.append((c.get("title", "") + " " + c.get("movement", "")).lower())
    web_guess = (web_info.get("best_guess", "") or "").lower()
    web_entities = " ".join([e.get("name", "").lower() for e in web_info.get("entities", [])])
    text_sources.append(web_guess)
    text_sources.append(web_entities)
    combined_text = " ".join(text_sources)

    # 인물 존재 여부 (Gemini Vision figure)
    has_person_gemini = figure.get("has_person", False) if figure else False

    # 점수 집계
    scores = {"추상": 0, "풍경": 0, "정물": 0, "인물": 0, "건축": 0}
    for kw in abstract_movements:
        if kw in combined_text: scores["추상"] += 2
    for kw in landscape_keywords:
        if kw in combined_text: scores["풍경"] += 1
    for kw in still_life_keywords:
        if kw in combined_text: scores["정물"] += 1
    for kw in portrait_keywords:
        if kw in combined_text: scores["인물"] += 1
    for kw in architecture_keywords:
        if kw in combined_text: scores["건축"] += 1

    # Gemini figure 판단이 있으면 인물 가중치
    if has_person_gemini:
        scores["인물"] += 2

    best_type = max(scores, key=scores.get)
    best_score = scores[best_type]

    # 점수 0이면 자동(미판단)
    if best_score == 0:
        return "자동"

    print(f"[ArtworkType AutoDetect] scores={scores} → detected='{best_type}'", flush=True)
    return best_type


def sanitize_visual_data(color, comp, person, figure, artwork_type, is_abstract=False):
    safe_facts = []
    blocked_facts = []

    # ── 1. 색채 팩트 (정밀화) ─────────────────────────────────────────────────
    brightness     = color.get("average_brightness", 0.5)
    saturation     = color.get("average_saturation", 0.5)
    contrast       = color.get("contrast_level", 0.5)
    warm_ratio     = color.get("warm_color_ratio", 0.0)
    cool_ratio     = color.get("cool_color_ratio", 0.0)
    dark_area      = color.get("dark_area_ratio", 0.0)
    bright_area    = color.get("bright_area_ratio", 0.0)
    bright_pos     = color.get("bright_area_position", "")
    brightness_lbl = color.get("brightness_label", "중간 밝기")
    saturation_lbl = color.get("saturation_label", "중간 채도")
    contrast_lbl   = color.get("contrast_label", "보통 대비")
    dominant_colors = color.get("dominant_colors", [])

    # 색채 온도감 기술
    if warm_ratio > 0.55:
        temp_desc = f"따뜻한 황토·적갈색 계열 주도 ({warm_ratio:.0%})"
    elif warm_ratio > 0.40:
        temp_desc = f"온기 있는 색조 비중이 높음 ({warm_ratio:.0%})"
    elif cool_ratio > 0.45:
        temp_desc = f"차가운 청색·청회색 계열 주도 ({cool_ratio:.0%})"
    elif cool_ratio > 0.30:
        temp_desc = f"서늘한 색조 일부 포함 ({cool_ratio:.0%})"
    else:
        temp_desc = f"따뜻한 색조 {warm_ratio:.0%} / 차가운 색조 {cool_ratio:.0%}"
    safe_facts.append(f"색채 온도감: {temp_desc}")

    # 명도·채도·대비 기술
    brightness_desc = (
        "전반적으로 매우 어두운 명도" if brightness < 0.25 else
        "전반적으로 어두운 명도" if brightness < 0.40 else
        "중간 명도" if brightness < 0.60 else
        "밝고 환한 명도" if brightness < 0.75 else
        "매우 밝은 고명도"
    )
    saturation_desc = (
        "무채색에 가까운 극저채도" if saturation < 0.15 else
        "절제된 저채도" if saturation < 0.30 else
        "중간 채도" if saturation < 0.55 else
        "선명하고 강렬한 고채도"
    )
    contrast_desc = (
        "매우 부드러운 저대비" if contrast < 0.25 else
        "부드러운 대비" if contrast < 0.40 else
        "보통 대비" if contrast < 0.60 else
        "강한 명암 대비" if contrast < 0.75 else
        "극강한 명암 대비"
    )
    safe_facts.append(f"명도: {brightness_desc} / 채도: {saturation_desc} / 대비: {contrast_desc}")

    # 주조색 (30% 이상인 것만 명시)
    top_colors = [c for c in dominant_colors[:3] if isinstance(c, dict) and c.get("percentage", 0) >= 0.30]
    if top_colors:
        color_names = "·".join(c.get("name", "") for c in top_colors if c.get("name"))
        if color_names:
            safe_facts.append(f"주조색 (30% 이상 비중): {color_names}")

    # 밝은 영역 위치 (존재 시)
    if bright_area > 0.15 and bright_pos:
        safe_facts.append(f"밝은 영역: 화면 {bright_pos}에 집중 ({bright_area:.0%})")
    if dark_area > 0.35:
        safe_facts.append(f"어두운 영역 비중이 높음 ({dark_area:.0%})")

    # ── 2. 구도 팩트 (정밀화) ─────────────────────────────────────────────────
    pos       = comp.get("main_subject_position", "중앙")
    neg_space = comp.get("negative_space_ratio", 0.5)
    sym       = comp.get("symmetry_score", 0.5)
    subj_size = comp.get("subject_size_ratio", 0.3)
    orient    = comp.get("dominant_orientation", "")

    # 여백 해석
    if neg_space > 0.65:
        space_desc = f"매우 넓은 여백 ({neg_space:.0%}) — 고적감·확장감 유발 가능"
    elif neg_space > 0.45:
        space_desc = f"여백 비중이 높음 ({neg_space:.0%}) — 호흡감 있는 구성"
    elif neg_space > 0.25:
        space_desc = f"적당한 여백 ({neg_space:.0%})"
    else:
        space_desc = f"밀도 높은 구성 ({neg_space:.0%} 여백 — 꽉 찬 화면)"

    # 균형감 해석
    if sym > 0.75:
        sym_desc = "매우 균형 잡힌 대칭 구도"
    elif sym > 0.55:
        sym_desc = "안정적인 균형 구도"
    elif sym > 0.35:
        sym_desc = "약간 비대칭적인 구도"
    else:
        sym_desc = "역동적인 비대칭 구도"

    # 주제 크기 해석
    if subj_size > 0.6:
        size_desc = "주요 피사체가 화면을 크게 채움 (압도적 존재감)"
    elif subj_size > 0.35:
        size_desc = "주요 피사체가 화면에 적당히 채워짐"
    else:
        size_desc = "주요 피사체가 작게 배치되어 배경·공간이 강조됨"

    safe_facts.append(f"구도: 화면 {pos} 부근 배치, {space_desc}, {sym_desc}")
    safe_facts.append(f"피사체 규모: {size_desc}")
    if orient:
        safe_facts.append(f"화면 방향 특성: {orient}")

    # ── 3. 인물 팩트 (High-risk — 엄격 제어) ────────────────────────────────────
    gemini_has_person = figure.get("has_person", False) if figure else False

    if is_abstract or artwork_type in ("풍경", "추상", "정물", "건축") or not gemini_has_person:
        human_detected = False
        face_visible   = False
        pose           = None
        posture        = None
        gaze           = None
        expression     = None
        blocked_facts.extend(["인물 존재 여부", "인물의 자세", "인물의 표정", "시선 방향", "인물의 감정 상태"])
    else:
        human_detected = True
        face_visible   = bool(figure.get("face_visible", False))
        expr_conf      = figure.get("expression_confidence", "low").lower()
        gemini_pose    = figure.get("posture_ko", "")
        opencv_pose    = person.get("pose", "")

        # 자세: medium 이상만 허용
        if expr_conf in ("high", "medium") and (gemini_pose or opencv_pose):
            pose    = gemini_pose or opencv_pose
            posture = figure.get("impression_ko", "") or ", ".join(person.get("emotional_posture_ko", []))
            safe_facts.append(f"인물 자세 및 구도적 특징: {pose}" + (f" — {posture}" if posture else ""))
        else:
            pose    = None
            posture = None
            blocked_facts.append("인물의 자세 (신뢰도 미달로 판독 차단)")

        # 표정·시선: high만 허용
        if expr_conf == "high":
            expression = figure.get("expression_ko", "")
            gaze       = figure.get("gaze", "")
            face_dir   = figure.get("face_direction", "")
            if expression:
                safe_facts.append(f"인물 표정: {expression} (판독 신뢰도 높음)")
            if gaze:
                safe_facts.append(f"인물 시선 방향: {gaze}")
            if face_dir:
                safe_facts.append(f"얼굴 방향: {face_dir}")
        else:
            expression = None
            gaze       = None
            blocked_facts.extend([
                "인물의 표정 (신뢰도 미달로 판독 차단)",
                "인물의 시선 방향 (신뢰도 미달로 판독 차단)"
            ])

    return {
        "human_detected":         human_detected,
        "face_visible":           face_visible,
        "pose":                   pose,
        "posture":                posture,
        "gaze":                   gaze,
        "expression":             expression,
        "safe_visual_facts":      safe_facts,
        "blocked_uncertain_facts": blocked_facts,
    }


def _build_payload(info, color, comp, person, figure, scores, att_x, att_y, candidates=None, identification_status="unknown", artwork_type="자동", is_abstract=False, user_provided_name=False):
    sanitized = sanitize_visual_data(color, comp, person, figure, artwork_type, is_abstract)
    return {
        "artwork_info": {k: info.get(k) for k in ("title", "artist", "year", "medium")},
        "candidates": candidates or [],
        "identification_status": identification_status,
        "user_provided_name": user_provided_name,
        "visual_analysis": {
            "dominant_colors": [c["name"] for c in color["dominant_colors"]],
            "brightness":  color["brightness_label"],
            "saturation":  color["saturation_label"],
            "contrast":    color["contrast_label"],
            "warm_ratio":  round(float(color["warm_color_ratio"]), 2),
            "cool_ratio":  round(float(color["cool_color_ratio"]), 2),
            "dark_area_ratio":    round(float(color.get("dark_area_ratio", 0)), 2),
            "bright_area_ratio":  round(float(color.get("bright_area_ratio", 0)), 2),
            "bright_area_position": color.get("bright_area_position", "—"),
            "color_moods": color["color_moods_ko"],
            "composition": {
                "position":       comp.get("main_subject_position"),
                "subject_size":   round(float(comp.get("subject_size_ratio", 0)), 2),
                "negative_space": round(float(comp.get("negative_space_ratio", 0)), 2),
                "symmetry":       round(float(comp.get("symmetry_score", 0)), 2),
                "orientation":    comp.get("dominant_orientation"),
            },
            "human": {
                "detected": sanitized["human_detected"],
                "face":     sanitized["face_visible"],
                "pose":     sanitized["pose"],
                "posture":  sanitized["posture"],
                "gaze":     sanitized["gaze"],
                "expression": sanitized["expression"],
            },
            "attention": f"{att_y} {att_x}",
            "safe_visual_facts": sanitized["safe_visual_facts"],
            "blocked_uncertain_facts": sanitized["blocked_uncertain_facts"],
        },
        "mood_scores": {EMOTION_KO[k]: round(float(v), 2) for k, v in scores.items()},
    }


def _make_evidence(color, comp, person, scores):
    ev = []
    for key, score in sorted(scores.items(), key=lambda x: -x[1])[:4]:
        if score < 0.45:
            continue
        reasons = []
        if key == "sadness":
            if color["average_brightness"] < 0.4:  reasons.append("어두운 밝기")
            if color["average_saturation"] < 0.3:  reasons.append("낮은 채도")
            if person.get("pose") in ("웅크림", "쭈그림"): reasons.append("웅크린 자세")
        elif key == "loneliness":
            if comp.get("negative_space_ratio", 0) > 0.55:
                reasons.append(f"넓은 여백 {comp['negative_space_ratio']*100:.0f}%")
        elif key == "warmth":
            if color["warm_color_ratio"] > 0.45:
                reasons.append(f"따뜻한 색 {color['warm_color_ratio']*100:.0f}%")
        elif key == "tension":
            if color.get("contrast_level", 0) > 0.55: reasons.append("강한 대비")
        elif key == "calmness":
            if color["average_saturation"] < 0.3: reasons.append("절제된 채도")
            if comp.get("symmetry_score", 0) > 0.6: reasons.append("균형 구도")
        elif key == "energy":
            if color["warm_color_ratio"] > 0.5: reasons.append("활기찬 색상")
        if not reasons: reasons = ["전반적 시각 요소"]
        ev.append({"emotion": EMOTION_KO[key], "score": round(float(score), 2), "reasons": reasons})
    return ev


def _parse_essay(text: str) -> dict:
    if not text or not text.strip():
        return {"title": "", "body": [], "questions": [], "comfort": ""}
    out = {"title": "", "body": [], "questions": [], "comfort": ""}
    section = "body"
    for raw in text.strip().splitlines():
        line = raw.strip()
        if not line: continue
        if line.startswith("[") and line.endswith("]"):
            inner = line[1:-1]
            if "질문" in inner:   section = "questions"
            elif "위로" in inner: section = "comfort"
            elif section == "body" and not out["title"]: out["title"] = inner
        elif section == "questions" and line.startswith("- "):
            out["questions"].append(line[2:])
        elif section == "comfort": out["comfort"] = line
        elif section == "body":    out["body"].append(line)
    # Fallback: if no body was parsed (unexpected LLM format), use full text
    if not out["body"]:
        paragraphs = [p.strip() for p in text.strip().split("\n\n") if p.strip()]
        out["body"] = paragraphs if paragraphs else [text.strip()]
    return out


def _load(path: str) -> list:
    if not os.path.exists(path): return []
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _dump(records: list, path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def order_points(pts: np.ndarray) -> np.ndarray:
    """
    Sorts 4 coordinates in order: [top-left, top-right, bottom-right, bottom-left].
    """
    pts = pts.reshape(4, 2)
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]       # Top-left
    rect[2] = pts[np.argmax(s)]       # Bottom-right
    diff = pts[:, 1] - pts[:, 0]
    rect[1] = pts[np.argmin(diff)]     # Top-right
    rect[3] = pts[np.argmax(diff)]     # Bottom-left
    return rect


# Roboflow Universe 공개 그림 탐지 모델 (class: "art"). 다른 모델로 바꾸려면 ROBOFLOW_MODEL 환경변수 지정.
_ROBOFLOW_MODEL = os.environ.get("ROBOFLOW_MODEL", "paintings-gpghp/1")
_ROBOFLOW_MIN_CONF = 0.70   # 이미 잘린 그림 사진에선 0.5대 신뢰도로 일부만 잡는 경우가 있어 높게 설정


def crop_painting_roboflow(img_bytes: bytes, api_key: str) -> tuple:
    """
    전시장 사진에서 그림 영역을 Roboflow 객체 탐지로 찾아 잘라낸다 (+ 기울어짐 보정).
    반환: (cropped_image_bytes, best_pred) / 그림을 못 찾았거나 자를 필요가 없으면 (None, None)
    """
    arr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        return None, None
    img_h, img_w = img.shape[:2]

    # 전송량·지연을 줄이기 위해 긴 변 1280px로 축소해서 탐지 (좌표는 원본 비율로 환산)
    scale = min(1.0, 1280 / max(img_h, img_w))
    small = cv2.resize(img, (int(img_w * scale), int(img_h * scale))) if scale < 1.0 else img
    base64_str = base64.b64encode(cv2.imencode('.jpg', small, [cv2.IMWRITE_JPEG_QUALITY, 90])[1].tobytes()).decode('ascii')

    try:
        response = requests.post(
            f"https://serverless.roboflow.com/{_ROBOFLOW_MODEL}",
            params={"api_key": api_key, "confidence": int(_ROBOFLOW_MIN_CONF * 100)},
            data=base64_str,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=8,
        )
        response.raise_for_status()
        predictions = response.json().get("predictions", [])
    except Exception as e:
        print(f"[Roboflow API Error] Request failed: {e}", flush=True)
        return None, None

    predictions = [p for p in predictions if p.get("confidence", 0.0) >= _ROBOFLOW_MIN_CONF
                   and None not in (p.get("x"), p.get("y"), p.get("width"), p.get("height"))]
    if not predictions:
        print(f"[Roboflow Crop] No painting detected with confidence >= {_ROBOFLOW_MIN_CONF:.0%}", flush=True)
        return None, None

    # 여러 점이 잡히면 사용자가 겨냥한(화면 중앙에 가까운) 그림 우선, 그다음 신뢰도
    sw, sh = small.shape[1], small.shape[0]
    def _center_dist(p):
        return ((p["x"] / sw - 0.5) ** 2 + (p["y"] / sh - 0.5) ** 2) ** 0.5
    best_pred = min(predictions, key=lambda p: (_center_dist(p) - p["confidence"] * 0.2))

    cx_px, cy_px = best_pred["x"] / scale, best_pred["y"] / scale
    w_px,  h_px  = best_pred["width"] / scale, best_pred["height"] / scale
    # quality_checker는 bbox를 원본 픽셀 기준으로 사용
    best_pred = {**best_pred, "x": cx_px, "y": cy_px, "width": w_px, "height": h_px}

    # 박스가 이미 화면 대부분이면 자를 필요 없음 (이미 그림만 찍힌 사진)
    if (w_px * h_px) / (img_w * img_h) > 0.85:
        print("[Roboflow Crop] Painting already fills the frame — skip crop", flush=True)
        return None, best_pred

    # Add 8% padding/margin to avoid cutting off borders of the painting
    pad_w = w_px * 0.08
    pad_h = h_px * 0.08

    x1 = max(0, int(cx_px - w_px / 2 - pad_w))
    y1 = max(0, int(cy_px - h_px / 2 - pad_h))
    x2 = min(img_w, int(cx_px + w_px / 2 + pad_w))
    y2 = min(img_h, int(cy_px + h_px / 2 + pad_h))

    if (x2 - x1) < 10 or (y2 - y1) < 10:
        print(f"[Roboflow Crop] Cropped region too small: {x2-x1}x{y2-y1}", flush=True)
        return None, None

    cropped_img = img[y1:y2, x1:x2]

    # ── OpenCV Perspective Warping (Straighten skewed painting) ─────────────────
    try:
        # 1. Prepare ROI for contour analysis
        roi_gray = cv2.cvtColor(cropped_img, cv2.COLOR_BGR2GRAY)
        roi_blur = cv2.GaussianBlur(roi_gray, (5, 5), 0)
        
        # 2. Dynamic Canny Edge Detection
        v = np.median(roi_blur)
        lower = int(max(0, (1.0 - 0.33) * v))
        upper = int(min(255, (1.0 + 0.33) * v))
        edged = cv2.Canny(roi_blur, lower, upper)
        
        # 3. Find contours inside the padded ROI
        contours, _ = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]
        
        quad_contour = None
        roi_area = cropped_img.shape[0] * cropped_img.shape[1]
        
        for c in contours:
            area = cv2.contourArea(c)
            # Quadrilateral must cover at least 15% of the ROI to ignore noise
            if area < (roi_area * 0.15):
                continue
                
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.025 * peri, True)
            
            # Must be a convex quadrilateral (exactly 4 points)
            if len(approx) == 4 and cv2.isContourConvex(approx):
                quad_contour = approx
                break
                
        if quad_contour is not None:
            # Reshape coordinates to (4, 2)
            roi_corners = quad_contour.reshape(4, 2).astype("float32")
            
            # Sort corners in [top-left, top-right, bottom-right, bottom-left] order
            ordered_roi_corners = order_points(roi_corners)
            
            # Translate coordinates back to original global image space
            global_corners = ordered_roi_corners.copy()
            global_corners[:, 0] += x1
            global_corners[:, 1] += y1
            
            # Target dimensions derived from Roboflow predicted size
            target_w = int(w_px)
            target_h = int(h_px)
            
            # Flat target destination points
            dst_corners = np.array([
                [0, 0],
                [target_w - 1, 0],
                [target_w - 1, target_h - 1],
                [0, target_h - 1]
            ], dtype="float32")
            
            # 4. Generate perspective homography matrix and warp the original image
            M = cv2.getPerspectiveTransform(global_corners, dst_corners)
            warped_img = cv2.warpPerspective(img, M, (target_w, target_h))
            
            # Confirm validity of warped result
            if warped_img is not None and warped_img.shape[0] >= 10 and warped_img.shape[1] >= 10:
                print(f"[Perspective Warp] Successfully flattened skewed painting frame ({target_w}x{target_h})", flush=True)
                _, buf = cv2.imencode('.jpg', warped_img, [cv2.IMWRITE_JPEG_QUALITY, 95])
                return buf.tobytes(), best_pred
                
        print("[Perspective Warp Warning] Quadrilateral not detected or invalid, falling back to standard padded crop", flush=True)
    except Exception as warp_err:
        print(f"[Perspective Warp Error] Warp failed: {warp_err}, falling back to standard crop", flush=True)

    # Standard fallback crop
    _, buf = cv2.imencode('.jpg', cropped_img, [cv2.IMWRITE_JPEG_QUALITY, 95])
    return buf.tobytes(), best_pred


_API_KEY = os.environ.get("GEMINI_API_KEY", "")


# ── 작가명 비교 / 식별 헬퍼 ──────────────────────────────────────────────────────

def _norm_name(s: str) -> str:
    """악센트·구두점 제거 + 소문자 (Dürer == Durer, Pierre-Auguste == pierre auguste)."""
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return " ".join(re.sub(r"[^\w\s]", " ", s.lower()).split())


def _artist_aliases(name: str) -> set:
    """영문명 + 한국어명(_ARTIST_KO)을 정규화한 별칭 집합."""
    out = {_norm_name(name)}
    n = _norm_name(name)
    for en, ko in _ARTIST_KO.items():
        en_n, ko_n = _norm_name(en), _norm_name(ko)
        if n and (n == en_n or n == ko_n or n in en_n or en_n in n):
            out.update({en_n, ko_n})
    out.discard("")
    return out


def _same_artist(a: str, b: str) -> bool:
    """두 작가명이 같은 인물인지 (영/한, 전체/성만 표기 차이 허용)."""
    if not a or not b:
        return False
    for x in _artist_aliases(a):
        for y in _artist_aliases(b):
            if x == y or x in y or y in x:
                return True
            # 성(last name) 등 4글자 이상 토큰 공유
            if any(len(t) >= 4 for t in set(x.split()) & set(y.split())):
                return True
    return False


def _text_overlap(a: str, b: str) -> bool:
    """제목 비교용 포함 관계 (짧은 일반어 오매칭 방지 위해 4글자 이상만)."""
    a, b = _norm_name(a), _norm_name(b)
    if len(a) < 4 or len(b) < 4:
        return False
    return a in b or b in a


def _db_description(info: dict, db_entry: dict) -> str:
    return f"""
[작품 배경 정보 - DB에서 직접 조회된 신뢰 사실]
- 작품명: {info['title']}
- 화가명: {info['artist']}
- 제작 시기: {db_entry.get('creation_period', '')}
- 미술 사조: {db_entry.get('art_movement', '')}
- 시대적 배경: {db_entry.get('historical_context', '')}
- 화가의 생애 맥락: {db_entry.get('artist_context', '')}
- 구도 및 시각적 상징: {db_entry.get('visual_connection', '')}
"""


def _resolve_info(title: str, artist: str, cand: dict | None, fallback_medium: str, ui_message: str):
    """DB 조회 후 info dict 구성. 반환: (info, db_entry)"""
    db_entry = lookup_artwork(title=title, artist=artist) if (title or artist) else None
    # lookup_artwork는 제목만으로도 매칭하므로 ("자화상" 등) 다른 작가의 작품이 걸릴 수 있음 → 작가 불일치면 폐기
    if db_entry and artist and not _same_artist(db_entry.get("artist", ""), artist):
        print(f"[DB Lookup] '{title}' 매칭 결과 작가 불일치({db_entry.get('artist')} ≠ {artist}) → 무시", flush=True)
        db_entry = None
    cand = cand or {}
    info = {
        "title":  (db_entry.get("title")  if db_entry else None) or title,
        "artist": (db_entry.get("artist") if db_entry else None) or artist,
        "year":   (db_entry.get("year")   if db_entry else None) or cand.get("year", ""),
        "medium": (db_entry.get("art_movement") if db_entry else None) or cand.get("movement", "") or fallback_medium,
        "ui_message": ui_message,
    }
    return info, db_entry


def _match_with_fallback(crop_bytes: bytes, original_bytes: bytes):
    """CLIP 매칭: 크롭 이미지 우선, 신뢰도 낮으면 원본으로 재시도."""
    try:
        m = match_artwork(crop_bytes)
        if original_bytes is not crop_bytes and (not m or m.get("confidence", 0) < 0.80):
            m2 = match_artwork(original_bytes)
            if m2 and m2.get("confidence", 0) > (m.get("confidence", 0) if m else 0):
                m = m2
        return m
    except Exception as e:
        print(f"[CLIP Match] failed (non-fatal): {e}", flush=True)
        return None


def _web_with_fallback(crop_bytes: bytes, original_bytes: bytes) -> dict:
    """Google Web Detection: 크롭 결과에 best_guess가 없으면 원본으로 재시도."""
    empty = {"best_guess": "", "entities": [], "matching_pages": [], "has_trusted_domain": False}
    try:
        w = detect_web_artwork(crop_bytes) or empty
        if not w.get("best_guess") and original_bytes is not crop_bytes:
            w2 = detect_web_artwork(original_bytes)
            if w2 and w2.get("best_guess"):
                w = w2
        return w
    except Exception as e:
        print(f"[WebDetection] failed (non-fatal): {e}", flush=True)
        return empty


@app.post("/api/analyze")
def analyze(
    image:          UploadFile = File(...),
    original_image: Optional[UploadFile] = File(None),
    mode:           str = Form("healing"),
    hint_title:     str = Form(""),
    hint_artist:    str = Form(""),
    user_identity_provided: bool = Form(False),
    artwork_type:        str = Form("자동"),
    analysis_focus:      str = Form("전체"),
    artwork_description: str = Form(""),
    # 프론트가 /api/crop-artwork(Roboflow)로 이미 자른 경우: 재호출 없이 그 bbox(JSON) 사용
    crop_bbox:           str = Form(""),
):
    raw = image.file.read()
    img = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(400, "이미지를 읽을 수 없습니다")
    if not _API_KEY:
        raise HTTPException(500, "GEMINI_API_KEY가 설정되지 않았습니다. 프로젝트 루트의 .env 파일을 확인하세요.")

    # 프론트에서 이미 작품 영역을 잘라 보낸 경우, 자르기 전 원본 사진을 함께 받음
    # (Roboflow 탐지 + Gemini 공간 맥락 + 매칭 fallback 용). 없으면 업로드 이미지가 곧 원본.
    original_raw = raw
    original_img = img
    if original_image is not None:
        ob = original_image.file.read()
        oi = cv2.imdecode(np.frombuffer(ob, np.uint8), cv2.IMREAD_COLOR) if ob else None
        if oi is not None:
            original_raw, original_img = ob, oi
    original_size = original_img.shape[0] * original_img.shape[1]

    # ── Roboflow Painting Border Detection & Crop ──────────────────────────────
    # 벽·바닥이 함께 찍힌 원본 사진에서 탐지 (이미 잘린 이미지에선 일부만 잡는 경우가 있음).
    # 실패하면 프론트에서 자른 이미지(없으면 원본)를 그대로 사용.
    best_pred = None
    if crop_bbox:
        try:
            best_pred = json.loads(crop_bbox)
        except Exception:
            best_pred = None
    roboflow_key = os.environ.get("ROBOFLOW_API_KEY")
    if roboflow_key and not crop_bbox:
        try:
            cropped_bytes, pred = crop_painting_roboflow(original_raw, roboflow_key)
            best_pred = pred
            if cropped_bytes is not None:
                temp_img = cv2.imdecode(np.frombuffer(cropped_bytes, np.uint8), cv2.IMREAD_COLOR)
                if temp_img is not None:
                    raw, img = cropped_bytes, temp_img
                    print("[Roboflow Crop] Successfully cropped painting border (with 8% padding)", flush=True)
                else:
                    print("[Roboflow Crop Warning] Cropped image could not be decoded, falling back to original", flush=True)
        except Exception as e:
            print(f"[Roboflow Crop Warning] Fallback to original image due to error: {e}", flush=True)

    try:
        _, buf = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 85])
        crop_jpg = buf.tobytes()

        # ── 외부 호출(CLIP·Google Web)을 로컬 CV 분석과 병렬 실행 ─────────────────
        with ThreadPoolExecutor(max_workers=2) as ex:
            # 사용자가 화가를 직접 알려준 경우 CLIP 자동 매칭 불필요
            f_match = ex.submit(_match_with_fallback, raw, original_raw) if not hint_artist else None
            f_web   = ex.submit(_web_with_fallback, crop_jpg, original_raw)

            quality = check_image_quality(img, best_pred, original_size=original_size)
            color   = analyze_colors(img, 5)
            comp    = analyze_composition(img)
            # 사용자가 명시한 유형이 인물 제외인 경우 analyze_person 스킵
            # (자동 감지는 Vision 호출 이후 결정되므로, 이 시점에서는 사용자 입력 기준)
            _skip_person_initial = artwork_type in ("풍경", "추상", "정물", "건축")
            person  = (
                {"human_detected": False, "face_visible": False, "pose": "미감지",
                 "body_orientation": "미감지", "body_height_position": "미감지",
                 "size_ratio": 0.0, "emotional_posture": [], "emotional_posture_ko": []}
                if _skip_person_initial else analyze_person(img)
            )
            sal     = create_saliency_overlay(img)
            att_x, att_y = get_attention_center(img)

            db_match = f_match.result() if f_match else None
            web_info = f_web.result()

        # Vision call before emotion scoring so figure expression feeds into scores
        vision   = analyze_artwork_vision(
            crop_jpg, _API_KEY,
            original_raw if original_raw is not raw else None,
            web_info=web_info,
        )
        candidates = vision["recognition"]
        ocr_info   = vision["ocr"]
        figure     = vision["figure"]

        scores  = calculate_emotion_scores(color, comp, person, figure)
        evidence = _make_evidence(color, comp, person, scores)

        db_confidence = (db_match.get("confidence", 0) * 100) if db_match else 0

        # ── 🏷️ OCR → 힌트 자동 주입 ────────────────────────────────────────────
        # 사용자가 수동으로 힌트를 제공하지 않은 경우에만 OCR 힌트를 평가·주입
        ocr_hint = evaluate_ocr_hint(ocr_info)
        ocr_auto_injected = False
        if not hint_title and not hint_artist and ocr_hint["ocr_confidence"] == "strong":
            # 강한 힌트(제목+작가 둘 다 검출)는 주입. 다른 소스와 일치하면 로그에 교차검증 표시.
            ocr_title, ocr_artist = ocr_hint["hint_title"], ocr_hint["hint_artist"]
            google_texts = [web_info.get("best_guess", "")] + [e["name"] for e in web_info.get("entities", [])]
            cross_ok = (
                any(_text_overlap(ocr_title, c.get("title", "")) or _same_artist(ocr_artist, c.get("artist", "")) for c in candidates)
                or any(_text_overlap(ocr_title, g) or _same_artist(ocr_artist, g) for g in google_texts)
            )
            hint_title, hint_artist = ocr_title, ocr_artist
            ocr_auto_injected = True
            print(f"[OCR AutoHint] STRONG{'+CROSS_VALIDATED' if cross_ok else ' (no cross-validation)'} → hint_title='{hint_title}', hint_artist='{hint_artist}'", flush=True)
        elif ocr_hint["ocr_confidence"] == "partial":
            # 부분 힌트: 제목 또는 작가 하나만 → 아래 자율 판단의 보조 근거로만 사용
            print(f"[OCR AutoHint] PARTIAL → 보조 힌트만 기록 (title='{ocr_hint['hint_title']}', artist='{ocr_hint['hint_artist']}')", flush=True)

        print(f"[OCR Evaluation] confidence={ocr_hint['ocr_confidence']}, source='{ocr_hint['ocr_source']}'", flush=True)

        # ── 🎨 작품 유형 자동 감지 (사용자가 '자동'을 선택한 경우만) ────────────────────
        if artwork_type == "자동":
            detected_type = auto_detect_artwork_type(candidates, figure, web_info)
            if detected_type != "자동":
                artwork_type = detected_type
                print(f"[ArtworkType] 자동 감지 결과: '{artwork_type}'", flush=True)

        # ── 📐 하이브리드 크로스 발리데이션 최종 판단 ──────────────────────────────
        # 원칙: 제목과 작가는 반드시 "같은 후보"에서 가져온다.
        #       (CLIP 인덱스는 작가 단위라 제목이 없음 → 제목은 CLIP 작가와 일치하는 Gemini 후보에서만)
        identification_status = "unknown"
        info: dict = {"title": "", "artist": "", "year": "", "medium": "", "ui_message": ""}
        db_entry = None
        chosen_cand = None

        if hint_title or hint_artist:
            # 1) 수동 힌트 또는 OCR 자동 주입 힌트
            if ocr_auto_injected:
                identification_status = "ocr_confirmed"
                ui_msg = f"라벨 OCR로 자동 확인된 작품 정보입니다. ({ocr_hint['ocr_source']})"
            else:
                identification_status = "confirmed"
                ui_msg = "사용자가 직접 선택해 확정된 검증 명화 정보입니다."
            info, db_entry = _resolve_info(hint_title, hint_artist, None, "", ui_msg)
        else:
            # 2) 자율 판단
            clip_artist  = db_match["artist"] if db_match else ""
            # 다른 작가 그림도 0.85~0.91까지 나오는 경우가 있어 90% 이상만 강일치로 인정
            clip_strong  = bool(db_match) and db_confidence >= 90
            clip_cand    = next((c for c in candidates if _same_artist(c.get("artist", ""), clip_artist)), None) if clip_artist else None
            top          = candidates[0] if candidates else None

            google_guess    = web_info.get("best_guess", "")
            google_entities = [e["name"] for e in web_info.get("entities", [])]
            google_texts    = [g for g in [google_guess] + google_entities if g]
            has_trusted     = web_info.get("has_trusted_domain", False)
            matching_pages  = web_info.get("matching_pages", [])

            def _cand_backed_by_google(c) -> bool:
                if not c:
                    return False
                return any(_text_overlap(c.get("title", ""), g) or _same_artist(c.get("artist", ""), g) for g in google_texts)

            ocr_p_title  = ocr_hint["hint_title"]  if ocr_hint["ocr_confidence"] == "partial" else ""
            ocr_p_artist = ocr_hint["hint_artist"] if ocr_hint["ocr_confidence"] == "partial" else ""

            def _cand_backed_by_ocr(c) -> bool:
                if not c or not (ocr_p_title or ocr_p_artist):
                    return False
                return _text_overlap(ocr_p_title, c.get("title", "")) or _same_artist(ocr_p_artist, c.get("artist", ""))

            # 규칙 1: confirmed — CLIP 작가 강일치 + 같은 작가의 Gemini 후보 + (Google 신뢰도메인 or OCR) 지지
            if clip_strong and clip_cand and (
                (has_trusted and (_cand_backed_by_google(clip_cand) or any(_same_artist(clip_artist, g) for g in google_texts)))
                or _cand_backed_by_ocr(clip_cand)
            ):
                identification_status = "confirmed"
                chosen_cand = clip_cand
                src = f"신뢰도 높은 기관 웹 매칭({', '.join(matching_pages)})" if has_trusted else "작품 라벨 OCR"
                info, db_entry = _resolve_info(
                    clip_cand.get("title", ""), clip_cand.get("artist") or clip_artist, clip_cand, db_match.get("genre", ""),
                    f"작품 정보가 확인되었어요. 내부 데이터셋과 {src} 결과가 같은 작품을 가리킵니다.",
                )

            # 규칙 2: web_confirmed — Gemini 후보가 Google 신뢰도메인 결과 또는 OCR로 뒷받침됨
            elif (has_trusted and _cand_backed_by_google(top)) or _cand_backed_by_ocr(top):
                identification_status = "web_confirmed"
                chosen_cand = top
                src = ', '.join(matching_pages) if has_trusted and matching_pages else "작품 라벨 OCR"
                info, db_entry = _resolve_info(
                    top.get("title", ""), top.get("artist", ""), top, "",
                    f"웹 교차 검증을 통해 작품 정보가 식별되었습니다. (출처: {src})",
                )

            # 규칙 3: internal_match — CLIP 작가 강일치 (제목은 같은 작가 후보가 있을 때만)
            elif clip_strong:
                identification_status = "internal_match"
                chosen_cand = clip_cand
                if clip_cand:
                    ui_msg = f"내부 미술관 데이터셋 매칭을 기반으로 가장 일치하는 작품입니다. (화풍 유사도: {round(db_confidence, 1)}%)"
                    title_choice = clip_cand.get("title", "")
                else:
                    ui_msg = f"{_ARTIST_KO.get(clip_artist, clip_artist)}의 화풍과 가장 유사합니다. 정확한 작품명은 확인하지 못했어요. (화풍 유사도: {round(db_confidence, 1)}%)"
                    title_choice = ""
                info, db_entry = _resolve_info(title_choice, clip_artist, clip_cand, db_match.get("genre", ""), ui_msg)

            # 규칙 4: unknown
            else:
                info = {"title": "", "artist": "", "year": "", "medium": "",
                        "ui_message": "정확한 작품명을 확인하기 어렵습니다. 색채와 구도를 중심으로 감상해볼게요."}

        if db_entry:
            artwork_description = _db_description(info, db_entry)

        # Check abstract art
        is_abstract = artwork_type == "추상"
        if db_entry:
            abstract_keywords = ["추상", "abstract", "데 스테일", "신조형주의", "미니멀리즘", "minimalism", "올오버 구도", "액션 페인팅"]
            fields = [db_entry.get(k, "").lower() for k in ("art_movement", "visual_connection", "creation_period")]
            if any(k in f for k in abstract_keywords for f in fields):
                is_abstract = True

        # LLM에는 최종 판정과 같은 작가의 후보만 전달 (다른 작가 후보가 섞여 해설이 흔들리는 것 방지)
        if identification_status == "unknown":
            payload_candidates = []
        elif info.get("artist"):
            payload_candidates = [c for c in candidates if _same_artist(c.get("artist", ""), info["artist"])]
        else:
            payload_candidates = [chosen_cand] if chosen_cand else []
        user_provided_name = bool((hint_title or hint_artist) and not ocr_auto_injected)

        payload = _build_payload(info, color, comp, person, figure, scores, att_x, att_y, candidates=payload_candidates, identification_status=identification_status, artwork_type=artwork_type, is_abstract=is_abstract, user_provided_name=user_provided_name)

        visual_for_similar = {
            "dominant_colors": [c.get("name", "") for c in color["dominant_colors"]],
            "color_moods":     color.get("color_moods_ko", []),
        }
        # 해설 생성과 유사 작품 추천은 서로 독립 → 병렬 실행
        with ThreadPoolExecutor(max_workers=2) as ex:
            f_essay   = ex.submit(generate_interpretation, payload, _API_KEY, mode, artwork_type, analysis_focus, artwork_description)
            f_similar = ex.submit(recommend_similar, info, visual_for_similar, _API_KEY)
            essay   = _parse_essay(f_essay.result())
            similar = f_similar.result()
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"분석 중 오류: {type(e).__name__}: {e}")

    dom_colors = [
        {"rgb": [int(c["rgb"][0]), int(c["rgb"][1]), int(c["rgb"][2])],
         "name": c.get("name", ""),
         "percentage": float(c.get("percentage", 0.2))}
        for c in color["dominant_colors"]
    ]

    return {
        "artwork_image":  _encode(img, 800, 800, 85),
        "saliency_image": _encode(sal, 800, 800, 85),
        "thumbnail":      _encode(img, 480, 360, 75),
        "detected": False,
        "quality":    quality,
        "candidates": candidates,
        "identification_status": identification_status,
        "ocr_info":   ocr_info,
        "figure":     figure,
        "similar":    similar,
        "db_match":   db_match,
        "info": {k: (info.get(k) or "") for k in ("title", "artist", "year", "medium", "ui_message")},
        "color": {
            "dominant_colors":    dom_colors,
            "warm_color_ratio":   float(color["warm_color_ratio"]),
            "cool_color_ratio":   float(color["cool_color_ratio"]),
            "average_brightness": float(color["average_brightness"]),
            "brightness_label":   color["brightness_label"],
            "average_saturation": float(color["average_saturation"]),
            "saturation_label":   color["saturation_label"],
            "contrast_level":     float(color.get("contrast_level", 0.5)),
            "contrast_label":     color["contrast_label"],
            "color_moods_ko":     color["color_moods_ko"],
        },
        "comp":     _j(comp),
        "person":   _j(person),
        "scores":   {EMOTION_KO[k]: round(float(v), 2) for k, v in scores.items()},
        "evidence": evidence,
        "essay":    essay,
    }


@app.get("/api/journal")
def journal_get(user=Depends(get_current_user)):
    return get_journal(user["id"])

class ThumbsRequest(BaseModel):
    dates: List[str]

@app.post("/api/journal/thumbs")
def journal_thumbs(req: ThumbsRequest, user=Depends(get_current_user)):
    return get_journal_thumbs(user["id"], req.dates)

@app.get("/api/journal/detail/{date:path}")
def journal_entry_get(date: str, user=Depends(get_current_user)):
    entry = get_journal_entry(user["id"], date)
    if not entry:
        raise HTTPException(404, "기록을 찾을 수 없습니다")
    return entry


class JournalEntry(BaseModel):
    date:             str
    entry_type:       str       = ""        # "sketch" | ""
    reflection:       str       = ""
    artwork_title:    str       = ""
    artwork_artist:   str       = ""
    artwork_year:     str       = ""
    essay_title:      str       = ""
    essay_body:       List[str] = []
    questions:        List[str] = []
    comfort:          str       = ""
    moods:            List[str] = []
    dominant_colors:  List[Any] = []
    thumbnail:        str       = ""
    pre_emotions:     List[str] = []
    post_emotions:    List[str] = []
    mood_color:       str       = ""
    mood_color_name:  str       = ""
    mood_note:        str       = ""
    sketch_image:     str       = ""
    sketch_title:     str       = ""
    sketch_note:      str       = ""
    sketch_guide:      str       = ""
    sketch_reflection: str       = ""
    era_data:         str       = ""
    question_answers: str       = "{}"


@app.post("/api/journal")
def journal_post(entry: JournalEntry, user=Depends(get_current_user)):
    save_journal_entry(user["id"], entry.model_dump())
    return {"ok": True}


class SketchReflectionRequest(BaseModel):
    sketch_image: str
    palette:  List[Any] = []
    keywords: List[str] = []
    guide_q:  str       = ""
    mode:     str       = "short"


@app.post("/api/sketch-reflection")
def sketch_reflection_api(req: SketchReflectionRequest):
    if not _API_KEY:
        raise HTTPException(500, "API 키가 설정되지 않았습니다")
    try:
        img_bytes = base64.b64decode(req.sketch_image)
        text = generate_sketch_reflection(img_bytes, req.palette, req.keywords, req.guide_q, _API_KEY, req.mode)
        return {"reflection": text}
    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(500, f"회고 생성 중 오류: {type(e).__name__}: {e}")


class EssayTextRequest(BaseModel):
    title:  str = ""
    artist: str = ""
    year:   str = ""
    mode:   str = "healing"


@app.post("/api/essay-text")
def essay_text_api(req: EssayTextRequest):
    """Generate an essay from artwork text info only (no image required).
    Used when user manually corrects artwork identification on the Results page."""
    if not _API_KEY:
        raise HTTPException(500, "API 키가 설정되지 않았습니다")
    if not req.title and not req.artist:
        raise HTTPException(400, "작품명 또는 화가명이 필요합니다")
    try:
        payload = {
            "artwork_info": {
                "title":  req.title  or "작품명 미정",
                "artist": req.artist or "화가 미정",
                "year":   req.year   or "",
                "medium": "",
            },
            "candidates": [],
            "identification_status": "confirmed",
            "user_provided_name": True,
            "visual_analysis": {},
            "mood_scores": {},
        }
        essay_raw = generate_interpretation(payload, _API_KEY, req.mode, "자동", "전체", "")
        essay = _parse_essay(essay_raw)
        return {"essay": essay}
    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(500, f"해설 생성 중 오류: {type(e).__name__}: {e}")


@app.delete("/api/journal/{date:path}")
def journal_delete(date: str, user=Depends(get_current_user)):
    delete_journal_entry(user["id"], date)
    return {"ok": True}


class NoteUpdateRequest(BaseModel):
    note: str

@app.patch("/api/journal/{date:path}/note")
def journal_update_note(date: str, req: NoteUpdateRequest, user=Depends(get_current_user)):
    update_journal_note(user["id"], date, req.note)
    return {"ok": True}

class ExhibitionUpdateRequest(BaseModel):
    exhibition: str

@app.patch("/api/journal/{date:path}/exhibition")
def journal_update_exhibition(date: str, req: ExhibitionUpdateRequest, user=Depends(get_current_user)):
    update_journal_exhibition(user["id"], date, req.exhibition)
    return {"ok": True}


class SketchUpdateRequest(BaseModel):
    sketch_image:      str = ""
    sketch_title:      str = ""
    sketch_note:       str = ""
    sketch_guide:      str = ""
    sketch_reflection: str = ""
    mood_color:        str = ""
    mood_color_name:   str = ""
    moods:             list = []

@app.patch("/api/journal/{date:path}/sketch")
def journal_update_sketch(date: str, req: SketchUpdateRequest, user=Depends(get_current_user)):
    update_journal_sketch(user["id"], date, req.dict())
    return {"ok": True}


_daily_cache: dict = {}
_aic_daily_cache: dict = {}

_DAILY_QUESTIONS = [
    "이 작품에서 가장 먼저 눈길이 가는 부분은 어디인가요?",
    "이 색감이 지금 내 기분과 어떻게 맞닿아 있나요?",
    "이 장면 속에 내가 있다면 어떤 감정을 느낄 것 같나요?",
    "작가는 무엇을 말하고 싶었을까요?",
    "이 작품이 떠올리게 하는 기억이나 장소가 있나요?",
    "빛과 그림자가 어디에서 시작되고 어디에서 끝나나요?",
    "이 작품을 한 단어로 표현한다면 무엇인가요?",
    "그림 속 인물 혹은 사물이 지금 어떤 소리를 내고 있을까요?",
    "오늘 하루와 이 작품 사이에 어떤 닮은 점이 있나요?",
    "만약 이 그림 속으로 들어갈 수 있다면, 어디에 서 있을 건가요?",
    "작가가 이 순간을 포착하기 위해 무엇을 내려놓았을까요?",
    "이 그림 앞에서 얼마나 오래 머물 수 있을 것 같나요?",
    "작품의 어느 부분이 가장 조용하게 느껴지나요?",
    "이 작품이 걸린 공간은 어떤 분위기일까요?",
    "그림 속 시간은 몇 시쯤일 것 같나요?",
    "이 작품을 보며 어떤 계절이 떠오르나요?",
    "구도에서 어떤 균형 또는 불균형이 느껴지나요?",
    "이 색 중 지금의 내 감정과 가장 가까운 색은 무엇인가요?",
    "이 장면이 끝나면 무슨 일이 일어날 것 같나요?",
    "작품이 나에게 조용히 건네는 말이 있다면 무엇일까요?",
    "붓터치 혹은 선 하나하나에서 어떤 감각이 느껴지나요?",
    "이 작품을 떠올릴 때 들릴 것 같은 음악이 있나요?",
    "작가는 이 작품을 그리면서 무엇을 느꼈을까요?",
    "지금 이 그림을 선물받는다면 어디에 걸고 싶나요?",
    "이 작품이 내 삶의 어떤 순간과 겹쳐 보이나요?",
    "가장 따뜻한 부분과 가장 차가운 부분은 어디인가요?",
    "이 그림을 처음 본 사람은 어떤 반응을 보였을까요?",
    "화면에서 눈에 보이지 않는 것은 무엇일까요?",
    "이 작품은 나에게 무엇을 허락해주는 것 같나요?",
    "오늘 하루를 이 그림의 제목으로 붙인다면?",
]


@app.get("/api/daily-artwork-aic")
def daily_artwork_aic():
    """AIC GET + URL-encoded params (공식 권장) 방식으로 날짜 기반 퍼블릭 도메인 작품 추천."""
    today = datetime.date.today()
    cache_key = str(today)
    if cache_key in _aic_daily_cache:
        return _aic_daily_cache[cache_key]

    ordinal = today.toordinal()
    # ES from 오프셋으로 날짜마다 다른 작품 선택 (0~8999 순환)
    es_from = ordinal % 9000

    aic_query = {
        "query": {
            "bool": {
                "must": [
                    {"term": {"is_public_domain": True}},
                    {"exists": {"field": "image_id"}},
                ]
            }
        },
        "from": es_from,
        "size": 10,
    }

    try:
        resp = requests.get(
            "https://api.artic.edu/api/v1/artworks/search",
            params={
                "params": json.dumps(aic_query, separators=(',', ':')),
                "fields": "id,title,artist_display,date_display,medium_display,image_id,description",
            },
            headers={"AIC-User-Agent": "inner-gallery (sakim9018@gmail.com)"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return {"fallback": True, "error": str(e)}

    artworks = data.get("data", [])
    artwork = next((a for a in artworks if a.get("image_id")), None)
    if not artwork:
        return {"fallback": True, "error": "image_id 없음"}

    iiif_base = data.get("config", {}).get("iiif_url", "https://www.artic.edu/iiif/2")
    img_id = artwork["image_id"]

    result = {
        "fallback":      False,
        "id":            artwork.get("id"),
        "title":         artwork.get("title", ""),
        "artist":        artwork.get("artist_display", ""),
        "date":          artwork.get("date_display", ""),
        "medium":        artwork.get("medium_display", ""),
        "description":   artwork.get("description") or "",
        "image_url":     f"{iiif_base}/{img_id}/full/843,/0/default.jpg",
        "thumbnail_url": f"{iiif_base}/{img_id}/full/400,/0/default.jpg",
        "artic_url":     f"https://www.artic.edu/artworks/{artwork.get('id')}",
        "question":      _DAILY_QUESTIONS[ordinal % len(_DAILY_QUESTIONS)],
    }

    _aic_daily_cache.clear()
    _aic_daily_cache[cache_key] = result
    return result


@app.get("/api/daily-artwork")
def daily_artwork():
    today = str(datetime.date.today())
    if today in _daily_cache:
        return _daily_cache[today]
    if not _API_KEY:
        return {"title": "—", "artist": "—", "year": "", "movement": "", "description": "API 키가 필요합니다"}
    from modules import gemini_client as genai
    genai.configure(api_key=_API_KEY)
    model = genai.GenerativeModel("gemini-2.5-flash")
    prompt = (
        f"오늘({today}) 날짜와 계절에 어울리는 서양 고전 명화 한 점을 추천해주세요. "
        "JSON 객체만 반환하고 다른 텍스트는 절대 포함하지 마세요:\n"
        '{"title":"작품명","artist":"화가명","year":"연도","movement":"미술사조","museum":"소장처","description":"감성적인 작품 소개 100자 이내"}'
    )
    try:
        resp = model.generate_content(prompt)
        text = resp.text.strip()
        r = None
        if "```" in text:
            for chunk in text.split("```"):
                chunk = chunk.strip().lstrip("json").strip()
                if chunk:
                    try:
                        r = json.loads(chunk); break
                    except Exception:
                        continue
        else:
            r = json.loads(text)
        if isinstance(r, dict):
            _daily_cache.clear()
            _daily_cache[today] = r
            return r
    except Exception as e:
        pass
    return {"title": "오늘의 명화", "artist": "", "year": "", "movement": "", "description": ""}



_ARTIST_KO = {
    "Vincent van Gogh": "빈센트 반 고흐",
    "Joaquín Sorolla": "호아킨 소로야",
    "Mikhail Vrubel": "미하일 브루벨",
    "Claude Monet": "클로드 모네",
    "Gustav Klimt": "구스타프 클림트",
    "Edvard Munch": "에드바르 뭉크",
    "Leonardo da Vinci": "레오나르도 다 빈치",
    "René Magritte": "르네 마그리트",
    "Salvador Dalí": "살바도르 달리",
    "Pablo Picasso": "파블로 피카소",
    "Henri Matisse": "앙리 마티스",
    "Pierre-Auguste Renoir": "피에르 오귀스트 르누아르",
    "Paul Cézanne": "폴 세잔",
    "Paul Gauguin": "폴 고갱",
    "Edgar Degas": "에드가 드가",
    "Edouard Manet": "에두아르 마네",
    "Rembrandt": "렘브란트",
    "Caravaggio": "카라바조",
    "Sandro Botticelli": "산드로 보티첼리",
    "Michelangelo": "미켈란젤로",
    "Raphael": "라파엘로",
    "Gustave Courbet": "귀스타브 쿠르베",
    "Eugene Delacroix": "외젠 들라크루아",
    "Francisco Goya": "프란시스코 고야",
    "Georges Seurat": "조르주 쇠라",
    "Andy Warhol": "앤디 워홀",
    "Jackson Pollock": "잭슨 폴록",
    "Piet Mondrian": "피트 몬드리안",
    "Frida Kahlo": "프리다 칼로",
    "Diego Rivera": "디에고 리베라",
    "Camille Pissarro": "카미유 피사로",
    "Alfred Sisley": "알프레드 시슬레",
    "Amedeo Modigliani": "아메데오 모딜리아니",
    "Henri Rousseau": "앙리 루소",
    "William Turner": "윌리엄 터너",
    "Diego Velazquez": "디에고 벨라스케스",
    "El Greco": "엘 그레코",
    "Peter Paul Rubens": "페테르 파울 루벤스",
    "Titian": "티치아노",
    "Albrecht Dürer": "알브레히트 뒤러",
    "Jan van Eyck": "얀 반 에이크",
    "Pieter Bruegel": "피터 브뢰헬",
    "Hieronymus Bosch": "히에로니무스 보스",
    "Giotto di Bondone": "조토 디 본도네",
    "Andrei Rublev": "안드레이 루블료프",
    "Kazimir Malevich": "카지미르 말레비치",
    "Vasiliy Kandinskiy": "바실리 칸딘스키",
    "Marc Chagall": "마르크 샤갈",
    "Joan Miro": "호안 미로",
    "Paul Klee": "파울 클레",
}

_FALLBACK_ARTWORKS = {
    "Vincent van Gogh": [
        {"title": "The Starry Night", "titleKo": "별이 빛나는 밤", "year": "1889", "confidence": 92, "reason": "반 고흐 특유의 소용돌이치는 밤하늘과 노란 별빛의 붓터치가 매우 짙게 검출되었습니다."},
        {"title": "Sunflowers", "titleKo": "해바라기", "year": "1888", "confidence": 85, "reason": "역동적이고 따뜻한 황금빛 태양조의 원색 대비가 느껴집니다."},
        {"title": "Café Terrace at Night", "titleKo": "밤의 카페 테라스", "year": "1888", "confidence": 78, "reason": "파란 밤하늘과 등불의 강렬한 보색 대조가 특징적입니다."},
        {"title": "Bedroom in Arles", "titleKo": "아를의 침실", "year": "1888", "confidence": 72, "reason": "안정적인 선 구도와 아늑한 침실 심상이 조화를 이룹니다."},
        {"title": "Starry Night Over the Rhône", "titleKo": "론강의 별이 빛나는 밤", "year": "1888", "confidence": 68, "reason": "강변의 가스등 불빛과 잔잔한 밤물결의 묘사가 유사합니다."}
    ],
    "Claude Monet": [
        {"title": "Water Lilies", "titleKo": "수련", "year": "1916", "confidence": 91, "reason": "지베르니 연못 위로 번지는 은은한 빛과 색채의 몽환성이 감지되었습니다."},
        {"title": "Impression, Sunrise", "titleKo": "인상, 일출", "year": "1872", "confidence": 84, "reason": "아침 안개 사이로 피어오르는 강렬한 붉은빛의 인상이 감지됩니다."},
        {"title": "Woman with a Parasol", "titleKo": "양산을 쓴 여인", "year": "1875", "confidence": 79, "reason": "바람을 머금은 구름과 초원, 양산을 든 여인의 상징적 배치가 강합니다."},
        {"title": "The Japanese Footbridge", "titleKo": "일본식 인도교", "year": "1899", "confidence": 73, "reason": "화창한 지베르니 정원의 연못과 초록 인도교의 시각적 형태가 일치합니다."}
    ],
    "Gustav Klimt": [
        {"title": "The Kiss", "titleKo": "키스", "year": "1908", "confidence": 93, "reason": "아름다운 기하학적 황금 문양과 연인의 몽환적인 포옹이 특징입니다."},
        {"title": "Portrait of Adele Bloch-Bauer I", "titleKo": "아델레 블로흐-바우어의 초상 I", "year": "1907", "confidence": 86, "reason": "정교하게 장식된 황금 텍스처와 인물의 매혹적인 미소가 느껴집니다."},
        {"title": "The Tree of Life", "titleKo": "생명의 나무", "year": "1909", "confidence": 80, "reason": "정교한 나선 무늬 나뭇가지의 기하학적 배치가 유사합니다."}
    ],
    "Edvard Munch": [
        {"title": "The Scream", "titleKo": "절규", "year": "1893", "confidence": 94, "reason": "핏빛 노을 하늘과 굴곡진 인물의 실루엣에서 오는 표현주의 화풍이 짙습니다."},
        {"title": "Madonna", "titleKo": "마돈나", "year": "1894", "confidence": 81, "reason": "뭉크 특유의 매혹적이고 신비한 뉘앙스를 자아내는 인물 구도가 돋보입니다."},
        {"title": "Anxiety", "titleKo": "불안", "year": "1894", "confidence": 76, "reason": "경직된 군상의 표정에서 깊은 우울과 심리적 불안을 전달합니다."}
    ],
    "Leonardo da Vinci": [
        {"title": "Mona Lisa", "titleKo": "모나리자", "year": "1503", "confidence": 95, "reason": "르네상스 시기 스푸마토 기법 특유의 경계선 묘사와 미소가 강렬하게 다가옵니다."},
        {"title": "The Last Supper", "titleKo": "최후의 만찬", "year": "1498", "confidence": 88, "reason": "완벽한 소실점 원근법 구조와 인물 군상의 극적인 드라마가 일치합니다."},
        {"title": "Lady with an Ermine", "titleKo": "담비를 안은 여인", "year": "1489", "confidence": 82, "reason": "우아한 자세의 여인과 품에 안긴 흰 담비의 해부학적 묘사가 유사합니다."}
    ],
}


def _get_fallback_candidates(artist_name: str) -> list:
    if not artist_name:
        return []
    # Try exact or partial lookup in masterpieces dict
    for key, cands in _FALLBACK_ARTWORKS.items():
        if key.lower() in artist_name.lower() or artist_name.lower() in key.lower():
            out = []
            for c in cands:
                item = c.copy()
                item["artist"] = key
                item["artistKo"] = _ARTIST_KO.get(key, key)
                out.append(item)
            return out
    
    # artist is known but specific artwork title is unknown — return empty
    # so the caller uses the artist-only candidate format
    return []


class ArtworkEraRequest(BaseModel):
    title:                 str  = ""
    artist:                str  = ""
    year:                  str  = ""
    identification_status: str  = "unknown"
    visual_context:        dict = {}


# \u2500\u2500 \ud654\uc9c8 \uc0ac\uc804 \uccb4\ud06c \uc5d4\ub4dc\ud3ec\uc778\ud2b8 \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
@app.post("/api/quick-quality")
def quick_quality(image: UploadFile = File(...)):
    """
    \uc774\ubbf8\uc9c0 \uc120\ud0dd \uc990\uc2dc \ud654\uc9c8 \uccb4\ud06c\ub9cc \uc2e4\ud589\ud569\ub2c8\ub2e4 (AI \ud638\ucd9c \uc5c6\uc74c).
    \ubd84\uc11d \uc2dc\uc791 \uc804 \uc0ac\uc6a9\uc790\uc5d0\uac8c \ubc14\ub85c \ud654\uc9c8 \uacbd\uace0\ub97c \ud45c\uc2dc\ud558\uae30 \uc704\ud55c \uc6a9\ub3c4\uc785\ub2c8\ub2e4.
    """
    try:
        raw = image.file.read()
        arr = np.frombuffer(raw, np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is None:
            return {"ok": False, "warnings": ["\uc774\ubbf8\uc9c0\ub97c \uc77d\uc744 \uc218 \uc5c6\uc2b5\ub2c8\ub2e4."]}
        quality = check_image_quality(img, bbox=None, original_size=None)
        return {
            "ok": True,
            "warnings":     quality.get("warnings", []),
            "overall_ok":   quality.get("overall_ok", True),
            "blur_score":   quality.get("blur_score"),
            "glare_ratio":  quality.get("glare_ratio"),
            "dark_ratio":   quality.get("dark_ratio"),
        }
    except Exception as e:
        return {"ok": False, "warnings": [f"\ud654\uc9c8 \ud655\uc778 \uc911 \uc624\ub958: {str(e)}"]}


@app.post("/api/crop-artwork")
def crop_artwork(image: UploadFile = File(...)):
    """촬영/선택 직후 미리보기용: Roboflow로 그림 영역을 잘라(+기울기 보정) 돌려준다.
    bbox는 분석 요청 때 그대로 돌려받아 Roboflow 재호출 없이 화질 판정에 사용."""
    raw = image.file.read()
    key = os.environ.get("ROBOFLOW_API_KEY")
    if not key:
        return {"cropped": False, "image": None, "bbox": None}
    try:
        cropped_bytes, pred = crop_painting_roboflow(raw, key)
    except Exception as e:
        print(f"[CropArtwork] failed: {e}", flush=True)
        return {"cropped": False, "image": None, "bbox": None}
    bbox = {k: float(pred[k]) for k in ("x", "y", "width", "height")} if pred else None
    if cropped_bytes is None:
        return {"cropped": False, "image": None, "bbox": bbox}
    return {"cropped": True, "image": base64.b64encode(cropped_bytes).decode("ascii"), "bbox": bbox}


@app.post("/api/quick-match")
def quick_match(image: UploadFile = File(...), local_only: bool = Form(False)):
    """이미지 업로드 즉시 Top-5 작품 후보 반환 (분석 전 미리보기용).
    local_only=True면 Gemini를 건너뛰고 로컬 CLIP만 사용 (카메라 자동 스캔처럼 반복 호출되는 경우)."""
    raw = image.file.read()

    # 1. Try Gemini API first (only if key exists)
    if _API_KEY and not local_only:
        try:
            from modules import gemini_client as genai
            genai.configure(api_key=_API_KEY)
            model = genai.GenerativeModel("gemini-2.5-flash")

            import PIL.Image, io
            pil_img = PIL.Image.open(io.BytesIO(raw))

            prompt = """이 이미지에 있는 미술 작품을 분석하세요.

가능성 있는 작품을 최대 5개까지 후보로 나열하세요.
각 후보마다 작품명, 화가, 제작연도, 신뢰도(0-100)를 포함하세요.

반드시 아래 JSON 형식으로만 답변하세요. 다른 텍스트 없이:
{
  "candidates": [
    {"title": "작품명(영어)", "titleKo": "작품명(한국어)", "artist": "화가명(영어)", "artistKo": "화가명(한국어)", "year": "연도", "confidence": 85, "reason": "이 작품으로 추정하는 이유 한 줄"},
    ...
  ],
  "is_artwork": true
}

미술 작품이 아닌 경우 is_artwork를 false로 설정하고 candidates는 빈 배열로 반환하세요.
확실하지 않으면 솔직하게 낮은 confidence를 부여하세요."""

            resp = model.generate_content([prompt, pil_img])
            raw_text = resp.text.strip()

            data = None
            if "```" in raw_text:
                for chunk in raw_text.split("```"):
                    chunk = chunk.strip().lstrip("json").strip()
                    if chunk.startswith("{"):
                        try:
                            data = json.loads(chunk); break
                        except Exception:
                            continue
            else:
                try:
                    data = json.loads(raw_text)
                except Exception:
                    pass

            if data and data.get("candidates"):
                return data
        except Exception as api_err:
            # If Gemini fails (e.g. rate limit, quota exceeded, network block), fall back to local CLIP
            print(f"[QuickMatch] Gemini API failed: {api_err}. Falling back to local CLIP FAISS index...", flush=True)

    # 2. Offline Fallback: Local CLIP + FAISS database search
    try:
        # Search wider pool, then filter for reliability
        artist_cands = top_k_artists(raw, k=8, min_sim=0.58)
        # Require ≥2 votes so single-image flukes are excluded
        reliable = [ac for ac in artist_cands if ac.get("vote_count", 0) >= 2]
        # Fall back to all if none pass vote filter
        filtered = reliable if reliable else artist_cands[:3]
        if filtered:
            out = []
            for ac in filtered:
                if len(out) >= 4:   # at most 4 artist candidates
                    break
                artist_name = ac["artist"]
                # 인덱스에 같은 작가가 다른 표기로 들어간 경우("Van Gogh" / "Vincent van Gogh") 중복 제거
                if any(_same_artist(artist_name, o["artist"]) for o in out):
                    continue
                ko = _ARTIST_KO.get(artist_name, "")
                out.append({
                    "title":      "",
                    "titleKo":    "",
                    "artist":     artist_name,
                    "artistKo":   ko or artist_name,
                    "year":       ac.get("years", ""),
                    "genre":      ac.get("genre", ""),
                    "confidence": ac["confidence"],
                    "vote_count": ac.get("vote_count", 0),
                    "reason":     f"CLIP 분석 결과 {ko or artist_name} 화풍과 유사합니다.",
                })
            if out:
                print(f"[QuickMatch] FAISS candidates: {[(o['artist'], o['confidence'], o['vote_count']) for o in out]}", flush=True)
                return {"candidates": out, "is_artwork": True, "source": "local_faiss"}
    except Exception as db_err:
        print(f"[QuickMatch] Local FAISS fallback failed: {db_err}", flush=True)

    return {"candidates": [], "is_artwork": False}



@app.post("/api/artwork-era")
def artwork_era_api(req: ArtworkEraRequest):
    if not _API_KEY:
        return {
            "_error": True,
            "confidence_label": "API 키 없음",
            "creation_period": "", "art_movement": "",
            "historical_context": "",
            "artist_context": "", "visual_connection": "",
        }
    try:
        result = generate_artwork_era(
            req.title, req.artist, req.year,
            req.identification_status, req.visual_context, _API_KEY,
        )
        return result
    except Exception as e:
        import traceback; traceback.print_exc()
        return {
            "_error": True,
            "confidence_label": "오류 발생",
            "creation_period": "", "art_movement": "",
            "historical_context": "",
            "artist_context": "", "visual_connection": "",
        }


class ChatRequest(BaseModel):
    artwork_info: dict
    message: str


@app.post("/api/docent-chat")
def docent_chat(req: ChatRequest):
    if not _API_KEY:
        raise HTTPException(500, "API 키가 설정되지 않았습니다")
    try:
        text = generate_docent_reply(req.artwork_info, req.message, _API_KEY)
        return {"reply": text.strip()}
    except Exception as e:
        raise HTTPException(500, str(e))


# ── 번역 ─────────────────────────────────────────────────────────────────────

class TranslateRequest(BaseModel):
    text: str

@app.post("/api/translate")
def translate_text(req: TranslateRequest):
    """영어 텍스트 → 한국어 번역 (Gemini)."""
    if not req.text.strip():
        return {"translated": ""}
    if not _API_KEY:
        raise HTTPException(500, "GEMINI_API_KEY가 설정되지 않았습니다.")
    from modules import gemini_client as _genai
    _genai.configure(api_key=_API_KEY)
    prompt = (
        "다음 미술 작품 설명 영어 텍스트를 자연스러운 한국어로 번역해주세요. "
        "번역문만 출력하세요 (설명, 주석 없이):\n\n" + req.text
    )
    for model_name in ["gemini-2.5-flash", "gemini-2.5-flash-lite"]:
        try:
            model = _genai.GenerativeModel(model_name)
            resp = model.generate_content(prompt)
            return {"translated": resp.text.strip()}
        except Exception as e:
            err_str = str(e)
            print(f"[translate] {model_name} error: {err_str[:200]}", flush=True)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                continue
            raise HTTPException(500, "번역 중 오류가 발생했습니다.")
    raise HTTPException(429, "번역 서비스가 일시적으로 한도에 도달했습니다. 잠시 후 다시 시도해주세요.")


# ── 이미지 프록시 ──────────────────────────────────────────────────────────────

@app.get("/api/proxy-image")
def proxy_image(url: str):
    import urllib.request
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read()
            content_type = resp.headers.get("Content-Type", "image/jpeg")
        return Response(content=data, media_type=content_type)
    except Exception as e:
        raise HTTPException(400, f"이미지를 가져올 수 없습니다: {str(e)}")


# ── 명언 ─────────────────────────────────────────────────────────────────────

@app.get("/api/demo-result")
def demo_result():
    """별이 빛나는 밤 — 사전 저장된 데모 분석 결과."""
    return {
        "artwork_image": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/ea/Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg/1280px-Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg",
        "saliency_image": "",
        "thumbnail": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/ea/Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg/400px-Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg",
        "info": {
            "title": "The Starry Night",
            "artist": "Vincent van Gogh",
            "year": "",
            "medium": "Oil on canvas",
            "ui_message": ""
        },
        "color": {
            "dominant_colors": [
                {"rgb": [66, 103, 155],  "name": "스틸 블루",         "percentage": 0.24},
                {"rgb": [15,  19,  34],  "name": "딥 네이비",          "percentage": 0.23},
                {"rgb": [35,  62, 111],  "name": "미드나이트 블루",    "percentage": 0.21},
                {"rgb": [110, 132, 159], "name": "슬레이트 블루",      "percentage": 0.20},
                {"rgb": [138, 147, 112], "name": "올리브 세이지",      "percentage": 0.12},
            ],
            "warm_color_ratio": 0.10,
            "cool_color_ratio": 0.78,
            "average_brightness": 0.35,
            "brightness_label": "보통",
            "average_saturation": 0.52,
            "saturation_label": "보통",
            "contrast_level": 0.52,
            "contrast_label": "보통",
            "dark_ratio": 0,
            "color_moods_ko": ["거리감", "무거움", "고독", "차분함", "슬픔", "신비로움"],
        },
        "comp": {
            "main_subject_position": "중간 중앙",
            "dominant_orientation": "균형",
            "negative_space_ratio": 0,
            "symmetry_score": 0.53,
            "composition_analysis": "소용돌이치는 하늘이 화면 전체를 압도하며, 왼쪽 사이프러스 나무가 수직 리듬을 형성하고 아래쪽 마을이 안정감을 부여하는 삼분할 구도입니다.",
            "composition_score": 78,
        },
        "person": {
            "detected_people_count": 0,
            "poses": [],
            "emotional_posture_ko": [],
            "posture_ko": "차분한 자세",
            "bright_position": "",
        },
        "scores": {
            "안정감": 0.60, "고독감": 0.58, "생동감": 0.58,
            "긴장감": 0.50, "따뜻함": 0.50, "슬픔": 0.50,
        },
        "evidence": [
            {"emotion": "안정감", "score": 0.60, "reasons": ["소용돌이치는 구도 속 안정적인 마을 풍경"]},
            {"emotion": "고독감", "score": 0.58, "reasons": ["광활한 밤하늘 아래 홀로 선 사이프러스 나무"]},
            {"emotion": "생동감", "score": 0.58, "reasons": ["역동적인 소용돌이 붓 터치와 밝은 별빛"]},
            {"emotion": "긴장감", "score": 0.50, "reasons": ["격렬한 하늘과 고요한 마을의 강렬한 대비"]},
        ],
        "essay": {
            "title": "밤하늘의 선율, 내면의 잔향",
            "body": [
                "혼자 있는 시간이 길어질수록, 아무렇지 않은 밤하늘마저 때로는 깊은 사색의 풍경으로 다가올 때가 있습니다. 빈센트 반 고흐의 걸작, <별이 빛나는 밤>은 익숙한 이름만큼이나 우리 내면의 밤을 환히 비추는 듯한 특별한 감동을 선사합니다. 이 그림은 깊고 차가운 청색과 짙푸른 색조가 주도하는 가운데(78%), 화면 전체를 꽉 채우는 역동적인 움직임으로, 우리의 복잡한 감정선을 따라 천천히 마음을 돌아보게 합니다.",
                "그림의 대부분을 차지하는 밤하늘은 중간 명도와 채도의 푸른색과 짙은 파란색으로 가득합니다. 물결치듯 소용돌이치는 붓질은 마치 바람의 흐름을 눈으로 보는 듯한 감각을 불러일으킵니다. 격렬하게 휘몰아치는 듯한 이 곡선들은 어쩌면 우리 마음속에 숨겨진 복잡한 생각이나 해소되지 않은 감정들의 움직임을 닮아 있을지도 모릅니다. 이 압도적인 하늘의 존재감은 보는 이에게 장엄함과 동시에 어딘가 모를 신비로운 긴장감을 전해줍니다.",
                "그러나 하늘을 가득 채운 별빛과 달빛은 따스한 노란빛과 황금빛으로 그림에 생명력을 불어넣습니다. 격동하는 푸른빛과 대비되는 이 작은 온기들은, 혼란 속에서도 기어코 빛을 찾아내고야 마는 희망이나 위안처럼 느껴질 수 있습니다. 반 고흐는 병원 생활 중 밤하늘에서 종교적인 위안을 얻었다고 고백했듯이, 이 별빛은 어둡고 고독한 순간에도 찾아오는 내면의 평화와 연결될 수 있습니다.",
                "화면 왼쪽에서 위로 솟아오른 짙은 나무는 마치 불꽃처럼 하늘을 향해 타오르는 듯한 존재감을 드러냅니다. 강렬하게 어둠 속에 솟아오른 이 나무는 우리 마음속 깊이 자리한 어떤 열망이나, 혹은 잠시 내려놓고 싶은 무언가를 상징하는 것처럼 느껴질 수 있습니다. 조용한 마을과 대비되는 이 나무의 강렬한 실루엣은 삶의 경계와 그 너머의 광활한 세계를 동시에 보여주는 듯합니다.",
                "하늘의 격렬함과 대조적으로, 그림 아래의 고요한 마을은 차분하고 평화로운 분위기를 자아냅니다. 가지런한 집들과 교회 첨탑은 흔들림 없는 일상의 풍경을 담아내며, 소용돌이치는 밤하늘 아래에서도 굳건히 자리를 지키고 있습니다. 이 마을의 안정된 구도는 삶의 혼돈 속에서도 우리를 지탱해주는 작은 안식처와 같은 감각을 줄 수 있으며, 바쁘게 움직이는 마음을 잠시 멈추고 고요히 내려놓는 시간을 가질 수 있도록 안내합니다.",
                "<별이 빛나는 밤>은 꽉 찬 화면 구성으로 어느 한 곳도 비워두지 않고 우리의 시선을 그림 안에 머물게 합니다. 이 밀도 높은 화면은 마치 우리 내면의 복잡한 감정들이 서로 얽혀 있는 모습을 보는 듯한 느낌을 줍니다. 시원하고 차가운 색채가 주를 이루지만, 그 안에 피어나는 따뜻한 별빛처럼, 그림은 다양한 감정의 스펙트럼을 동시에 경험하게 하면서 지금 당신의 마음이 어떤 모습인지 찬찬히 들여다볼 수 있도록 돕습니다.",
                "오늘은 이 그림의 소용돌이치는 밤하늘을 따라, 당신 마음속에 잠시 웅크리고 있던 생각의 흐름을 조용히 따라가 보세요. 그리고 그 안에서 반짝이는 작은 빛을 찾아 잠시 눈을 맞춰보는 시간을 가져보세요.",
            ],
            "questions": [
                "이 그림의 소용돌이치는 밤하늘에서 나의 어떤 감정의 움직임이 느껴지나요?",
                "그림 속 고요한 마을처럼, 나의 삶에서 흔들림 없이 나를 지탱해주는 것은 무엇인가요?",
                "격동하는 밤하늘 속 작은 별빛처럼, 나의 가장 어두운 순간에도 빛을 찾아주는 것은 무엇이었나요?",
            ],
            "comfort": "이 그림의 깊고 푸른 소용돌이 속에서 반짝이는 별들처럼, 당신의 복잡한 마음속에도 스스로 빛을 내는 위안의 순간이 고요히 머물러 있기를 바랍니다.",
        },
        "quality": {},
        "candidates": [],
        "identification_status": "confirmed",
        "ocr_info": {},
        "figure": {},
        "similar": [],
    }


@app.get("/api/artist-quote")
def artist_quote():
    """DB에서 랜덤 명언 반환."""
    return get_random_quote()


# ── 전시 정보 ────────────────────────────────────────────────────────────────

def _parse_kcisa_items(data: dict) -> list:
    """kcisa.kr 공통 응답에서 item 배열을 추출 (다양한 응답 구조 대응)."""
    body = data.get("response", {}).get("body", {})
    items = body.get("items", {})
    if not items:
        # 일부 API는 body에 items 없이 data 바로 반환
        items = body.get("data", {})
    if isinstance(items, list):
        return items
    if not items:
        return []
    item_list = items.get("item", items.get("data", []))
    if isinstance(item_list, dict):
        item_list = [item_list]
    return item_list if isinstance(item_list, list) else []


def _is_active_period(period_str: str) -> bool:
    """PERIOD 필드 파싱해 현재 진행 중인지 확인. 날짜 형식이 다양하므로 숫자만 추출해서 비교."""
    if not period_str:
        return True  # 기간 정보 없으면 일단 포함
    import datetime, re
    today = datetime.date.today()
    try:
        parts = period_str.split("~")
        end_str = parts[-1].strip()
        # 숫자만 추출 (예: 2024. 05. 31 -> 20240531)
        digits = re.sub(r'[^0-9]', '', end_str)
        if len(digits) >= 8:
            end_date = datetime.date(int(digits[:4]), int(digits[4:6]), int(digits[6:8]))
            return end_date >= today
        return True
    except Exception:
        return True


def _parse_integ_item(item: dict) -> dict | None:
    """통합 API 아이템 → 공통 포맷 변환 (기간 지난 전시 제외)."""
    if not isinstance(item, dict): return None
    title = str(item.get("TITLE") or "").strip()
    if not title:
        return None
    period = str(item.get("PERIOD") or "")
    if not _is_active_period(period):
        return None
    return {
        "source":    str(item.get("CNTC_INSTT_NM") or "기관").strip(),
        "title":     title,
        "place":     str(item.get("EVENT_SITE") or ""),
        "period":    period,
        "fee":       str(item.get("CHARGE") or ""),
        "thumbnail": str(item.get("IMAGE_OBJECT") or ""),
        "url":       str(item.get("URL") or ""),
        "author":    str(item.get("AUTHOR") or ""),
    }


@app.get("/api/exhibitions")
def get_exhibitions():
    """
    ① 통합 전시정보 API (INTEG_API_KEY) — 27개 기관 통합, 현재 전시 필터링
    ② 국립현대미술관 개별 API (MOCA_API_KEY) — 보조
    ③ 예술의전당 개별 API  (SAC_API_KEY)  — 보조
    키가 하나도 없으면 fallback 반환.
    """
    integ_key = os.getenv("INTEG_API_KEY", "").strip()
    moca_key  = os.getenv("MOCA_API_KEY",  "").strip()
    sac_key   = os.getenv("SAC_API_KEY",   "").strip()

    if not any([integ_key, moca_key, sac_key]):
        return {"items": [], "fallback": True}

    results = []
    seen_titles = set()
    
    def add_result(parsed_item):
        if not parsed_item: return
        title_norm = parsed_item["title"].replace(" ", "").lower()
        if title_norm not in seen_titles:
            seen_titles.add(title_norm)
            results.append(parsed_item)
    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (compatible; InnerGallery/1.0)",
    }

    # ① 통합 전시정보 (27개 기관) — 최우선
    if integ_key:
        try:
            resp = requests.get(
                "https://api.kcisa.kr/openapi/API_CCA_145/request",
                params={"serviceKey": integ_key, "numOfRows": "1000", "pageNo": "1"},
                headers=headers,
                timeout=12,
            )
            resp.raise_for_status()
            raw = resp.json()
            print(f"[exhibitions] INTEG status: {resp.status_code}, keys: {list(raw.keys())}", flush=True)
            for item in _parse_kcisa_items(raw):
                add_result(_parse_integ_item(item))
                if len(results) >= 30:
                    break
        except Exception as e:
            print(f"[exhibitions] INTEG error: {e}", flush=True)

    # ② 국립현대미술관 개별 (보조 — 통합에 없는 경우 대비)
    if moca_key and len(results) < 3:
        try:
            resp = requests.get(
                "https://api.kcisa.kr/openapi/service/rest/moca/docMeta",
                params={"serviceKey": moca_key, "numOfRows": "5", "pageNo": "1"},
                headers=headers,
                timeout=12,
            )
            resp.raise_for_status()
            for item in _parse_kcisa_items(resp.json())[:5]:
                if not isinstance(item, dict): continue
                title = str(item.get("title") or "").strip()
                if not title:
                    continue
                add_result({
                    "source":    "국립현대미술관",
                    "title":     title,
                    "place":     str(item.get("venue") or ""),
                    "period":    str(item.get("eventPeriod") or ""),
                    "fee":       str(item.get("charge") or ""),
                    "thumbnail": "",
                    "url":       "",
                    "author":    str(item.get("creator") or ""),
                })
        except Exception as e:
            print(f"[exhibitions] MOCA error: {e}", flush=True)

    # ③ 예술의전당 개별 (보조)
    if sac_key and len(results) < 3:
        try:
            resp = requests.get(
                "https://api.kcisa.kr/openapi/API_CCA_149/request",
                params={"serviceKey": sac_key, "numOfRows": "5", "pageNo": "1"},
                headers=headers,
                timeout=12,
            )
            resp.raise_for_status()
            for item in _parse_kcisa_items(resp.json())[:5]:
                if not isinstance(item, dict): continue
                title = str(item.get("TITLE") or "").strip()
                if not title:
                    continue
                add_result({
                    "source":    "예술의전당",
                    "title":     title,
                    "place":     str(item.get("EVENT_SITE") or ""),
                    "period":    str(item.get("PERIOD") or ""),
                    "fee":       str(item.get("CHARGE") or ""),
                    "thumbnail": str(item.get("IMAGE_OBJECT") or ""),
                    "url":       str(item.get("URL") or ""),
                    "author":    str(item.get("AUTHOR") or ""),
                })
        except Exception as e:
            print(f"[exhibitions] SAC error: {e}", flush=True)

    return {"items": results[:30], "fallback": len(results) == 0}


# ── 프론트엔드 정적 파일 서빙 (Docker 빌드 후) ──────────────────────────────
_dist = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "dist")
if os.path.exists(_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(_dist, "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend(full_path: str):
        # dist 내 실제 파일(아이콘, manifest 등)이면 그 파일을 직접 반환
        _dist_real = os.path.realpath(_dist)
        candidate = os.path.realpath(os.path.join(_dist, full_path))
        if candidate.startswith(_dist_real + os.sep) and os.path.isfile(candidate):
            return FileResponse(candidate)
        return FileResponse(os.path.join(_dist, "index.html"))
