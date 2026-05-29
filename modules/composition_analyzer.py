import cv2
import numpy as np
from typing import Dict, Any, Optional, Tuple


def analyze_composition(image: np.ndarray) -> Dict[str, Any]:
    """Analyze spatial composition: subject position, negative space, symmetry, orientation."""
    h, w = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    subject_bbox = _find_main_subject(gray, h, w)
    result: Dict[str, Any] = {}

    if subject_bbox is not None:
        x, y, bw, bh = subject_bbox
        cx = (x + bw / 2) / w
        cy = (y + bh / 2) / h

        pos_x = "왼쪽" if cx < 0.35 else ("오른쪽" if cx > 0.65 else "중앙")
        pos_y = "상단" if cy < 0.35 else ("하단" if cy > 0.65 else "중간")

        size_ratio     = (bw * bh) / (w * h)
        negative_space = 1.0 - size_ratio

        # 3분할 법칙: 1/3 또는 2/3 라인에서 ±12% 이내
        thirds_x = abs(cx - 1/3) < 0.12 or abs(cx - 2/3) < 0.12
        thirds_y = abs(cy - 1/3) < 0.12 or abs(cy - 2/3) < 0.12

        result.update({
            "main_subject_detected":    True,
            "main_subject_position":    f"{pos_y} {pos_x}",
            "subject_center_normalized": (float(cx), float(cy)),
            "subject_size_ratio":       float(size_ratio),
            "negative_space_ratio":     float(negative_space),
            "rule_of_thirds":           bool(thirds_x or thirds_y),
        })
    else:
        result.update({
            "main_subject_detected": False,
            "main_subject_position": "미감지",
            "subject_size_ratio":    0.5,
            "negative_space_ratio":  0.5,
            "rule_of_thirds":        False,
        })

    result["symmetry_score"]       = float(_analyze_symmetry(gray))
    result["dominant_orientation"] = _dominant_orientation(gray)
    return result


def _find_main_subject(gray: np.ndarray, h: int, w: int) -> Optional[Tuple[int, int, int, int]]:
    """대비 기반 주목 영역 탐지 (가우시안 차이로 국소 대비가 높은 영역 추출)."""
    blurred = cv2.GaussianBlur(gray, (51, 51), 0)
    diff    = cv2.absdiff(gray, blurred)
    _, thresh = cv2.threshold(diff, 18, 255, cv2.THRESH_BINARY)

    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, np.ones((20, 20), np.uint8))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN,  np.ones((8,  8),  np.uint8))

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    largest = max(contours, key=cv2.contourArea)
    if cv2.contourArea(largest) < 0.015 * h * w:  # 전체 면적의 1.5% 미만은 노이즈로 무시
        return None

    return cv2.boundingRect(largest)


def _analyze_symmetry(gray: np.ndarray) -> float:
    h, w = gray.shape
    left  = gray[:, :w // 2].astype(float)
    right = cv2.flip(gray[:, w // 2: w // 2 * 2], 1).astype(float)
    if left.shape != right.shape:
        return 0.5
    diff = np.abs(left - right)
    return max(0.0, min(1.0, 1.0 - diff.mean() / 128.0))


def _dominant_orientation(gray: np.ndarray) -> str:
    horiz = np.abs(cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)).sum()
    vert  = np.abs(cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)).sum()
    if horiz > vert * 1.3:   return "수평"
    elif vert > horiz * 1.3: return "수직"
    return "균형"
