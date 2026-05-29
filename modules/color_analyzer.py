"""
color_analyzer.py

수정 이력:
- HSV 단위 OpenCV 기준 통일 (H=0~179). 이전 colorsys(0~360) 혼용으로 warm/cool 계산 오류 있었음
- 무채색(S<12%) 픽셀을 warm/cool 비율 계산에서 제외
- KMeans 해상도 150→200 상향
"""

import cv2
import numpy as np
from sklearn.cluster import KMeans
from typing import List, Dict, Any


COLOR_MOOD_MAP: Dict[str, List[str]] = {
    "black":        ["grief", "darkness", "weight"],
    "dark":         ["heavy", "mysterious", "melancholic"],
    "gray":         ["quiet", "calm", "distant"],
    "white":        ["pure", "open", "spacious"],
    "red":          ["passionate", "intense", "urgent"],
    "orange":       ["warm", "lively", "energetic"],
    "amber":        ["warm", "earthy", "grounded"],
    "golden":       ["warm", "earthy", "grounded"],
    "yellow":       ["bright", "hopeful", "cheerful"],
    "olive":        ["natural", "restful", "grounded"],
    "green":        ["peaceful", "natural", "restful"],
    "cyan":         ["calm", "distant", "cool"],
    "blue":         ["sad", "lonely", "contemplative"],
    "purple":       ["mysterious", "spiritual", "dignified"],
    "magenta":      ["emotional", "intense", "vibrant"],
    "brown":        ["earthy", "heavy", "grounded"],
    "dark brown":   ["melancholic", "heavy", "grounded"],
    "ochre":        ["earthy", "grounded", "quiet"],
}

MOOD_KO: Dict[str, str] = {
    "grief": "슬픔", "darkness": "어둠", "weight": "무거움",
    "heavy": "무거움", "mysterious": "신비로움", "melancholic": "우울감",
    "quiet": "고요함", "calm": "차분함", "distant": "거리감",
    "pure": "순수함", "open": "개방감", "spacious": "넓음",
    "passionate": "열정", "intense": "강렬함", "urgent": "긴박감",
    "warm": "따뜻함", "lively": "활기참", "energetic": "에너지",
    "earthy": "대지감", "grounded": "안착감",
    "bright": "밝음", "hopeful": "희망", "cheerful": "명랑함",
    "natural": "자연스러움", "restful": "안정감",
    "peaceful": "평화로움",
    "cool": "서늘함",
    "sad": "슬픔", "lonely": "고독", "contemplative": "사색적",
    "spiritual": "영적", "dignified": "위엄",
    "emotional": "감정적", "vibrant": "생동감",
    "subdued": "억제됨", "restrained": "절제됨",
    "expressive": "표현적",
}


def _hsv_to_color_name(h: int, s: int, v: int) -> str:
    """OpenCV HSV (H: 0~179, S: 0~255, V: 0~255) 기준 색 이름 반환."""
    s_n = s / 255.0
    v_n = v / 255.0

    if v_n < 0.12:
        return "black"
    if v_n > 0.90 and s_n < 0.08:
        return "white"
    if s_n < 0.12:
        if v_n < 0.35:   return "dark gray"
        elif v_n < 0.65: return "gray"
        else:            return "light gray"

    # 갈색/황토/황금 계열: 클림트·렘브란트 작품 대응 (일반 orange로 묶이지 않게 분리)
    if 8 <= h <= 30 and s_n >= 0.25:
        if v_n < 0.35:              return "dark brown"
        elif v_n < 0.52 and s_n < 0.60: return "brown"
        elif v_n < 0.65 and s_n < 0.70: return "ochre"
        elif s_n >= 0.60:           return "golden brown"
        else:                       return "amber"

    if h <= 8 or h >= 170:   base = "red"
    elif h < 14:              base = "orange"
    elif h < 22:              base = "amber" if (s_n > 0.55 and v_n > 0.55) else "golden brown"
    elif h < 32:              base = "yellow" if (v_n > 0.60 and s_n > 0.40) else "olive"
    elif h < 80:              base = "green"
    elif h < 100:             base = "cyan"
    elif h < 130:             base = "blue"
    elif h < 150:             base = "purple"
    else:                     base = "magenta"

    if v_n < 0.30:            return f"dark {base}"
    elif v_n > 0.80 and s_n < 0.30: return f"light {base}"
    elif s_n < 0.25:          return f"muted {base}"
    return base


def analyze_colors(image: np.ndarray, n_colors: int = 5) -> Dict[str, Any]:
    """
    주조색 추출 및 감성 색채 지표 계산.
    HSV 계산 전부 OpenCV 기준 (H: 0~179, S: 0~255, V: 0~255).
    """
    small = cv2.resize(image, (200, 200))
    hsv_small = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)

    h_ch = hsv_small[:, :, 0].astype(np.float32)
    s_ch = hsv_small[:, :, 1].astype(np.float32)
    v_ch = hsv_small[:, :, 2].astype(np.float32)

    pixels = small.reshape(-1, 3).astype(np.float32)
    kmeans = KMeans(n_clusters=n_colors, random_state=42, n_init=10, max_iter=300)
    kmeans.fit(pixels)

    centers_bgr = kmeans.cluster_centers_.astype(np.uint8)
    labels = kmeans.labels_
    unique, counts = np.unique(labels, return_counts=True)
    percentages = counts / len(labels)
    sorted_idx = np.argsort(-percentages)

    dominant_colors: List[Dict] = []
    for idx in sorted_idx:
        b, g, r = centers_bgr[idx]
        c_bgr = np.uint8([[[b, g, r]]])
        c_hsv = cv2.cvtColor(c_bgr, cv2.COLOR_BGR2HSV)[0][0]
        ch, cs, cv2_v = int(c_hsv[0]), int(c_hsv[1]), int(c_hsv[2])
        dominant_colors.append({
            "rgb": (int(r), int(g), int(b)),
            "hsv": (ch, cs, cv2_v),
            "name": _hsv_to_color_name(ch, cs, cv2_v),
            "percentage": float(percentages[idx]),
        })

    s_norm = s_ch / 255.0
    v_norm = v_ch / 255.0

    avg_brightness = float(np.mean(v_norm))
    avg_saturation = float(np.mean(s_norm))

    # 무채색 픽셀(S<12%)은 온기/냉기 비율 계산에서 제외
    # 흑백 명암이 지배적인 작품에서 색온도가 잘못 계산되는 것을 방지
    chromatic_mask  = s_norm > 0.12
    chromatic_count = float(np.sum(chromatic_mask))

    if chromatic_count > 0:
        h_flat = h_ch.flatten()
        c_flat = chromatic_mask.flatten()

        # 따뜻한 색: 빨강(0~15, 170~179) + 주황(15~30) + 노랑(30~38)
        warm_hue = (
            ((h_flat >= 0) & (h_flat <= 15)) |
            ((h_flat >= 170) & (h_flat <= 179)) |
            ((h_flat > 15) & (h_flat <= 38))
        )
        warm_ratio = float(np.sum(warm_hue & c_flat) / chromatic_count)

        # 차가운 색: 청록(85~105) + 파랑(105~130) + 남색(130~145)
        cool_hue = (h_flat >= 85) & (h_flat <= 145)
        cool_ratio = float(np.sum(cool_hue & c_flat) / chromatic_count)

        neutral_hue = (h_flat >= 38) & (h_flat < 85)
        neutral_ratio = float(np.sum(neutral_hue & c_flat) / chromatic_count)
    else:
        warm_ratio = cool_ratio = neutral_ratio = 0.0

    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    contrast = min(float(np.std(gray) / 128.0), 1.0)

    brightness_label = (
        "매우 어두움" if avg_brightness < 0.25 else
        "어두움"      if avg_brightness < 0.40 else
        "보통"        if avg_brightness < 0.60 else
        "밝음"        if avg_brightness < 0.78 else
        "매우 밝음"
    )
    saturation_label = (
        "매우 낮음" if avg_saturation < 0.12 else
        "낮음"      if avg_saturation < 0.28 else
        "보통"      if avg_saturation < 0.52 else
        "높음"      if avg_saturation < 0.72 else
        "매우 높음"
    )
    contrast_label = (
        "매우 낮음" if contrast < 0.20 else
        "낮음"      if contrast < 0.35 else
        "보통"      if contrast < 0.55 else
        "높음"      if contrast < 0.75 else
        "매우 높음"
    )

    dark_area_ratio   = float(np.sum(v_norm < 0.30) / v_norm.size)
    bright_area_ratio = float(np.sum(v_norm > 0.70) / v_norm.size)

    bright_mask = v_norm > 0.70
    if bright_mask.sum() > 20:
        rows, cols = np.where(bright_mask)
        cy = float(np.mean(rows) / small.shape[0])
        cx = float(np.mean(cols) / small.shape[1])
        vert  = "상단" if cy < 0.38 else ("하단" if cy > 0.62 else "중간")
        horiz = "왼쪽" if cx < 0.38 else ("오른쪽" if cx > 0.62 else "중앙")
        bright_area_position = f"{vert} {horiz}"
    else:
        bright_area_position = "—"

    color_moods: set = set()
    for ci in dominant_colors[:3]:
        name = ci["name"]
        for key, moods in COLOR_MOOD_MAP.items():
            if key in name:
                color_moods.update(moods[:2])
                break

    if avg_brightness < 0.30:   color_moods.update(["heavy", "quiet"])
    elif avg_brightness > 0.72: color_moods.update(["bright", "open"])

    if avg_saturation < 0.18:   color_moods.update(["subdued", "restrained"])
    elif avg_saturation > 0.60: color_moods.update(["vibrant", "expressive"])

    if cool_ratio > 0.45:       color_moods.update(["calm", "distant"])

    color_moods_ko = [MOOD_KO.get(m, m) for m in list(color_moods)[:6]]

    return {
        "dominant_colors":      dominant_colors,
        "warm_color_ratio":     round(warm_ratio, 3),
        "cool_color_ratio":     round(cool_ratio, 3),
        "neutral_color_ratio":  round(neutral_ratio, 3),
        "average_brightness":   round(avg_brightness, 3),
        "brightness_label":     brightness_label,
        "average_saturation":   round(avg_saturation, 3),
        "saturation_label":     saturation_label,
        "contrast_level":       round(contrast, 3),
        "contrast_label":       contrast_label,
        "dark_area_ratio":      round(dark_area_ratio, 3),
        "bright_area_ratio":    round(bright_area_ratio, 3),
        "bright_area_position": bright_area_position,
        "color_moods":          list(color_moods)[:6],
        "color_moods_ko":       color_moods_ko,
    }
