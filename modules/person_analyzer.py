import cv2
import numpy as np
from typing import Dict, Any, Optional, Tuple


def analyze_person(image: np.ndarray) -> Dict[str, Any]:
    """
    명화 속 인물 감지 및 정서적 자세 분류.
    HOG 우선, 실패 시 피부색 기반 fallback.
    """
    h, w = image.shape[:2]

    bbox, people_count = _hog_detect(image, h, w)
    if bbox is None:
        bbox = _skin_detect(image, h, w)
        if bbox is not None:
            people_count = 1

    if bbox is None:
        return {
            "human_detected": False, "face_visible": False,
            "pose": "미감지", "body_orientation": "미감지",
            "body_height_position": "미감지", "size_ratio": 0.0,
            "emotional_posture": [], "emotional_posture_ko": [],
        }

    return _build_result(image, bbox, h, w, people_count)


def _hog_detect(image: np.ndarray, h: int, w: int) -> Tuple[Optional[Tuple], int]:
    scale = min(1.0, 640 / max(h, w))
    small = cv2.resize(image, (int(w * scale), int(h * scale)))
    hog   = cv2.HOGDescriptor()
    hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
    detections, weights = hog.detectMultiScale(small, winStride=(8, 8), padding=(4, 4), scale=1.05)
    if len(detections) == 0:
        return None, 0
    best = int(np.argmax(weights))
    x, y, bw, bh = detections[best]
    return (int(x / scale), int(y / scale), int(bw / scale), int(bh / scale)), len(detections)


def _skin_detect(image: np.ndarray, h: int, w: int) -> Optional[Tuple]:
    # 명화의 납작하고 변형된 인물 형태 대응을 위해 피부색 범위를 넓게 설정
    ycrcb = cv2.cvtColor(image, cv2.COLOR_BGR2YCrCb)
    mask  = cv2.inRange(ycrcb, np.array([0, 125, 70], dtype=np.uint8),
                                np.array([255, 195, 145], dtype=np.uint8))
    mask  = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((12, 12), np.uint8))

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    largest = max(contours, key=cv2.contourArea)
    if cv2.contourArea(largest) < 0.008 * h * w:
        return None
    return cv2.boundingRect(largest)


POSTURE_KO = {
    "withdrawn": "웅크림", "self-protective": "자기보호", "vulnerable": "취약함",
    "exhausted": "탈진", "surrendered": "내려놓음", "resting": "휴식",
    "upright": "꼿꼿함", "resilient": "회복력", "present": "현재에 있음",
    "contemplative": "사색적", "waiting": "기다림", "settled": "안정됨",
    "concealed": "은폐", "isolated": "고립",
}


def _build_result(image: np.ndarray, bbox: Tuple, img_h: int, img_w: int, people_count: int = 1) -> Dict[str, Any]:
    x, y, bw, bh = bbox
    aspect     = bh / max(bw, 1)
    cy         = (y + bh / 2) / img_h
    size_ratio = (bw * bh) / (img_w * img_h)
    height_pos = "하단" if cy > 0.62 else ("상단" if cy < 0.38 else "중간")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    ).detectMultiScale(gray, 1.1, 4, minSize=(20, 20))
    face_visible = len(faces) > 0

    if people_count >= 2:
        pose        = "다양한 군상의 역동적 얽힘" if people_count >= 3 else "어우러진 이중주 구도"
        orientation = "다각도 입체 흐름"
        posture_en  = ["resilient", "present", "contemplative", "waiting"]
        posture_ko  = [POSTURE_KO.get(p, p) for p in posture_en]
        if people_count >= 3:
            posture_en.append("solidarity")
            posture_ko.extend(["역동적 연대", "군중의 비장함", "다채로운 상호작용"])
        else:
            posture_ko.extend(["정서적 교감", "조화로운 이중주"])
        return {
            "human_detected": True, "face_visible": bool(face_visible),
            "pose": pose, "body_orientation": orientation,
            "body_height_position": height_pos, "size_ratio": float(size_ratio),
            "emotional_posture": posture_en, "emotional_posture_ko": posture_ko,
        }

    # aspect ratio(height/width)와 화면 내 위치로 자세 판정
    if aspect >= 1.85:
        pose, orientation = ("우뚝 서있음", "수직") if size_ratio > 0.14 else ("서있음", "수직")
    elif aspect < 0.62:
        pose, orientation = "편안히 누움", "수평"
    elif aspect < 0.95:
        pose, orientation = ("웅크려 앉음", "아래방향") if cy > 0.54 else ("기대어 앉음", "경사방향")
    elif aspect < 1.48:
        if cy > 0.58:       pose, orientation = "무릎 꿇은 자세", "아래방향"
        elif face_visible:  pose, orientation = "단정히 앉음", "수직"
        else:               pose, orientation = "사색하듯 숙임", "아래방향"
    else:
        pose, orientation = "차분한 자세", "수직"

    posture_en: list = []
    if pose in ("웅크려 앉음", "사색하듯 숙임", "무릎 꿇은 자세") and height_pos == "하단":
        posture_en.extend(["withdrawn", "self-protective", "vulnerable"])
    elif pose == "편안히 누움":
        posture_en.extend(["exhausted", "surrendered", "resting"])
    elif pose in ("우뚝 서있음", "서있음") and cy < 0.5:
        posture_en.extend(["upright", "resilient", "present"])
    elif pose in ("단정히 앉음", "기대어 앉음", "차분한 자세"):
        posture_en.extend(["contemplative", "waiting", "settled"])

    if not face_visible:    posture_en.append("concealed")
    if size_ratio < 0.12:   posture_en.append("isolated")
    if not posture_en:      posture_en = ["neutral"]

    return {
        "human_detected": True, "face_visible": bool(face_visible),
        "pose": pose, "body_orientation": orientation,
        "body_height_position": height_pos, "size_ratio": float(size_ratio),
        "emotional_posture": posture_en,
        "emotional_posture_ko": [POSTURE_KO.get(p, p) for p in posture_en],
    }
