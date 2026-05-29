import cv2
import numpy as np
from typing import Tuple


def create_saliency_overlay(image: np.ndarray) -> np.ndarray:
    """
    Return the original image blended with a saliency heatmap overlay.
    Falls back to contrast-based attention if the contrib saliency module is absent.
    """
    saliency_map = _compute_saliency(image)
    heatmap = cv2.applyColorMap(saliency_map, cv2.COLORMAP_JET)
    return cv2.addWeighted(image, 0.55, heatmap, 0.45, 0)


def get_attention_center(image: np.ndarray) -> Tuple[str, str]:
    """Return (x_desc, y_desc) of the most salient region."""
    h, w = image.shape[:2]
    saliency_map = _compute_saliency(image)

    M = cv2.moments(saliency_map.astype(float))
    if M["m00"] == 0:
        return "중앙", "중간"

    cx = M["m10"] / M["m00"] / w
    cy = M["m01"] / M["m00"] / h

    x_desc = "왼쪽" if cx < 0.35 else ("오른쪽" if cx > 0.65 else "중앙")
    y_desc = "상단" if cy < 0.35 else ("하단" if cy > 0.65 else "중간")
    return x_desc, y_desc


def _compute_saliency(image: np.ndarray) -> np.ndarray:
    try:
        sal = cv2.saliency.StaticSaliencySpectralResidual_create()  # type: ignore[attr-defined]
        ok, smap = sal.computeSaliency(image)
        if ok:
            return (smap * 255).astype(np.uint8)
    except (AttributeError, cv2.error):
        pass
    return _contrast_saliency(image)


def _contrast_saliency(image: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (51, 51), 0)
    diff = cv2.absdiff(gray, blurred)
    return cv2.normalize(diff, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
