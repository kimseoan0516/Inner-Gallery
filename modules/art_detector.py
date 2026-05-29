import cv2
import numpy as np
from typing import Tuple, Optional


def order_points(pts: np.ndarray) -> np.ndarray:
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect


def four_point_transform(image: np.ndarray, pts: np.ndarray) -> np.ndarray:
    rect = order_points(pts)
    (tl, tr, br, bl) = rect

    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    maxWidth = max(int(widthA), int(widthB))

    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    maxHeight = max(int(heightA), int(heightB))

    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]
    ], dtype="float32")

    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))
    return warped


def detect_and_crop_artwork(image: np.ndarray) -> Tuple[np.ndarray, bool]:
    """
    Detect painting/artwork region in the photo and apply perspective correction.
    Returns (cropped_image, was_detected).
    """
    orig = image.copy()
    h, w = image.shape[:2]

    scale = 1.0
    if max(h, w) > 1200:
        scale = 1200 / max(h, w)
        proc = cv2.resize(image, (int(w * scale), int(h * scale)))
    else:
        proc = image.copy()

    ph, pw = proc.shape[:2]
    gray = cv2.cvtColor(proc, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Try multiple edge thresholds to find the painting rectangle
    for low, high in [(30, 100), (50, 150), (80, 200)]:
        edges = cv2.Canny(blurred, low, high)
        edges = cv2.dilate(edges, np.ones((3, 3), np.uint8), iterations=2)

        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)

        for contour in contours[:8]:
            area = cv2.contourArea(contour)
            if area < 0.08 * ph * pw or area > 0.97 * ph * pw:
                continue

            peri = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.02 * peri, True)

            if len(approx) == 4:
                pts = approx.reshape(4, 2).astype(np.float32) / scale
                warped = four_point_transform(orig, pts)
                ch, cw = warped.shape[:2]
                if cw > 80 and ch > 80:
                    return warped, True

    # No clear quadrilateral — return original
    return orig, False
