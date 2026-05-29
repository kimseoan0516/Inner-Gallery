"""
emotion_scorer.py

수정 이력:
- 밝은 파란색(수련·아몬드나무 등) → loneliness 오분류 버그 수정
  (밝음+차가운 색 = 고독이 아닌 개방감·평온)
- 여백 넓음+주체 작음 → 무조건 고독 처리 제거
  (반드시 어둡거나 무채색이어야 고독감 부여)
"""

from typing import Dict, Any, Optional

EMOTION_KO = {
    "calmness":   "안정감",
    "loneliness": "고독감",
    "tension":    "긴장감",
    "warmth":     "따뜻함",
    "sadness":    "슬픔",
    "energy":     "생동감",
}

# expression_ko → 감정 보정값 (confidence 가중치 0.35~1.0 배율 적용)
_EXPRESSION_MAP: Dict[str, Dict[str, float]] = {
    "슬픔":   {"sadness": 0.20, "loneliness": 0.10, "energy": -0.10},
    "고통":   {"sadness": 0.22, "tension": 0.15, "energy": -0.12},
    "절망":   {"sadness": 0.24, "loneliness": 0.12, "energy": -0.15},
    "우울":   {"sadness": 0.20, "loneliness": 0.12, "calmness": -0.08},
    "그리움": {"sadness": 0.12, "loneliness": 0.15, "warmth": 0.05},
    "고독":   {"loneliness": 0.20, "sadness": 0.10},
    "공포":   {"tension": 0.20, "sadness": 0.12, "energy": -0.08},
    "분노":   {"tension": 0.22, "energy": 0.10, "calmness": -0.12},
    "긴장감": {"tension": 0.18, "sadness": 0.08},
    "긴장":   {"tension": 0.18, "sadness": 0.08},
    "불안":   {"tension": 0.15, "sadness": 0.10, "calmness": -0.08},
    "무표정": {"calmness": 0.08},
    "평온":   {"calmness": 0.18, "sadness": -0.08, "tension": -0.08},
    "기쁨":   {"energy": 0.20, "warmth": 0.15, "sadness": -0.12},
    "희망":   {"energy": 0.15, "warmth": 0.10, "sadness": -0.08},
    "경이로움": {"energy": 0.12, "tension": 0.08},
    "경이":   {"energy": 0.12, "tension": 0.08},
    "사색":   {"calmness": 0.12, "loneliness": 0.08},
    "결의":   {"energy": 0.15, "tension": 0.08, "sadness": -0.08},
}

_CONFIDENCE_WEIGHT = {"high": 1.0, "medium": 0.6, "low": 0.35}


def calculate_emotion_scores(
    color: Dict[str, Any],
    composition: Dict[str, Any],
    person: Dict[str, Any],
    figure: Optional[Dict[str, Any]] = None,
) -> Dict[str, float]:
    scores = {k: 0.5 for k in EMOTION_KO}

    brightness = color.get("average_brightness", 0.5)
    saturation = color.get("average_saturation", 0.5)
    warm_ratio = color.get("warm_color_ratio", 0.3)
    cool_ratio = color.get("cool_color_ratio", 0.3)
    contrast   = color.get("contrast_level", 0.5)

    neg_space  = composition.get("negative_space_ratio", 0.5)
    size_ratio = composition.get("subject_size_ratio", 0.3)
    position   = composition.get("main_subject_position", "")
    symmetry   = composition.get("symmetry_score", 0.5)

    # 1. 명도
    if brightness < 0.30:
        scores["sadness"]  += 0.25; scores["tension"] += 0.08
        scores["energy"]   -= 0.20; scores["warmth"]  -= 0.08
    elif brightness < 0.42:
        scores["sadness"]  += 0.12; scores["energy"]  -= 0.10
    elif brightness > 0.72:
        scores["energy"]   += 0.20; scores["calmness"] += 0.08; scores["sadness"] -= 0.15
    elif brightness > 0.55:
        scores["energy"]   += 0.08; scores["sadness"]  -= 0.06

    # 2. 채도
    if saturation < 0.15:
        scores["calmness"] += 0.15; scores["sadness"] += 0.12; scores["energy"] -= 0.12
    elif saturation < 0.28:
        scores["calmness"] += 0.08; scores["sadness"] += 0.06
    elif saturation > 0.62:
        scores["energy"]   += 0.18; scores["tension"] += 0.08
    elif saturation > 0.45:
        scores["energy"]   += 0.08

    # 3. 색 온도 — 밝기와 반드시 조합 평가 (밝은 파란색 ≠ 고독)
    if warm_ratio > 0.45:
        scores["warmth"]     += 0.22; scores["energy"]    += 0.08; scores["sadness"]   -= 0.10
    elif warm_ratio > 0.28:
        scores["warmth"]     += 0.10

    if cool_ratio > 0.40:
        if brightness < 0.40:
            # 어둡고 차가움 → 고독·슬픔
            scores["loneliness"] += 0.20; scores["sadness"] += 0.12; scores["warmth"] -= 0.12
        elif brightness > 0.55:
            # 밝고 차가움 → 차분·평온 (파란 하늘, 수련 등)
            scores["calmness"]   += 0.15; scores["energy"] += 0.05
        else:
            scores["loneliness"] += 0.08; scores["calmness"] += 0.05
    elif cool_ratio > 0.22 and brightness < 0.42:
        scores["loneliness"] += 0.06

    # 4. 명암 대비
    if contrast > 0.65:
        scores["tension"]  += 0.18; scores["energy"]   += 0.06
    elif contrast > 0.50:
        scores["tension"]  += 0.08
    elif contrast < 0.25:
        scores["calmness"] += 0.10; scores["tension"]  -= 0.08

    # 5. 구도 — 여백+작은 주체가 고독인지는 어두움·무채색 여부로 결정
    is_dark_and_desaturated = brightness < 0.42 and saturation < 0.30
    is_bright_and_open      = brightness > 0.55 and neg_space > 0.50

    if neg_space > 0.60 and size_ratio < 0.30:
        if is_dark_and_desaturated:
            scores["loneliness"] += 0.24; scores["sadness"] += 0.10
        elif is_bright_and_open:
            # 밝고 넓은 여백 → 개방감 (아몬드나무, 동양화 여백미 등)
            scores["calmness"]   += 0.12; scores["energy"]     += 0.05
            scores["loneliness"] -= 0.08
        else:
            scores["loneliness"] += 0.10; scores["sadness"] += 0.04
    elif neg_space > 0.45 and size_ratio < 0.20:
        if is_dark_and_desaturated: scores["loneliness"] += 0.12
        elif is_bright_and_open:    scores["calmness"]   += 0.08

    if "하단" in str(position):
        scores["sadness"] += 0.10 if brightness < 0.45 else 0.04
        if brightness < 0.45: scores["calmness"] -= 0.05

    if symmetry > 0.65:
        scores["calmness"] += 0.12; scores["tension"] -= 0.06
    elif symmetry > 0.50:
        scores["calmness"] += 0.05
    elif symmetry < 0.30:
        scores["tension"]  += 0.08; scores["energy"]  += 0.05

    # 6. 인물 자세 (OpenCV)
    if person.get("human_detected"):
        posture = person.get("emotional_posture", [])
        pose    = person.get("pose", "")
        if "withdrawn" in posture or "self-protective" in posture:
            scores["loneliness"] += 0.18; scores["sadness"] += 0.14
        if "isolated" in posture:
            scores["loneliness"] += 0.18
        if pose in ("웅크림", "쭈그림"):
            scores["sadness"]    += 0.14; scores["tension"] += 0.08
        if "resilient" in posture or "upright" in posture:
            scores["energy"]     += 0.14; scores["sadness"] -= 0.08

    # 7. Gemini Vision 표정 (confidence 가중치 적용)
    if figure and figure.get("has_person"):
        expression = figure.get("expression_ko", "")
        weight     = _CONFIDENCE_WEIGHT.get(figure.get("expression_confidence", "low"), 0.35)
        for keyword, deltas in _EXPRESSION_MAP.items():
            if keyword in expression:
                for emotion, delta in deltas.items():
                    scores[emotion] += delta * weight
                break

    # 8. 복합 시그니처 보정
    if brightness > 0.60 and warm_ratio > 0.35 and saturation > 0.30:
        # 밝고+따뜻하고+채도 있음 → 생동감 (해바라기·아몬드나무 등)
        scores["energy"] += 0.08; scores["warmth"] += 0.06; scores["sadness"] -= 0.06

    if brightness < 0.35 and saturation < 0.25 and contrast > 0.50:
        # 매우 어둡고+무채색+강한 대비 → 내면 깊이 (렘브란트 계열)
        scores["sadness"]  += 0.10; scores["tension"]  += 0.06
        scores["calmness"] += 0.05  # 어둠 속 고요함

    if brightness > 0.55 and cool_ratio > 0.30 and neg_space > 0.40:
        # 밝고+차가운+넓은 여백 → 인상주의 풍경, 고독감 억제
        scores["calmness"]   += 0.10; scores["loneliness"] -= 0.05

    return {k: max(0.0, min(1.0, v)) for k, v in scores.items()}


def scores_to_ko(scores: Dict[str, float]) -> Dict[str, float]:
    return {EMOTION_KO[k]: v for k, v in scores.items()}
