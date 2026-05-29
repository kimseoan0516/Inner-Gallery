import cv2
import numpy as np


def check_image_quality(img: np.ndarray, bbox: dict = None, original_size: int = None) -> dict:
    """
    분석 전 이미지 품질 평가 (blur / darkness / glare / artwork size).
    오분석 방지 및 불필요한 API 호출 차단 용도.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img_h, img_w = img.shape[:2]
    total_pixels = img_h * img_w

    # 흐림: Laplacian 분산 < 75 = 흐림, > 100 = 선명
    blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    is_blurry  = blur_score < 75.0

    brightness = float(gray.mean()) / 255.0
    is_dark    = brightness < 0.12

    # 반사광: 전체 밝기가 낮아도 국소 반사 blob이 CLIP/OCR 인식을 망침
    glare_mask  = (gray > 248).astype(np.uint8)
    glare_ratio = float(np.sum(glare_mask)) / total_pixels

    num_labels, _, stats, _ = cv2.connectedComponentsWithStats(glare_mask)
    has_glare_spot      = False
    max_glare_blob_ratio = 0.0
    for i in range(1, num_labels):
        blob_ratio = stats[i, cv2.CC_STAT_AREA] / total_pixels
        if blob_ratio > max_glare_blob_ratio:
            max_glare_blob_ratio = blob_ratio
        if blob_ratio > 0.015:  # 이미지 면적의 1.5% 이상인 반사 blob
            has_glare_spot = True

    is_glare = (brightness > 0.88) or (glare_ratio > 0.08) or has_glare_spot

    # 작품 크기: Roboflow bbox 기준 15% 미만이면 너무 멀리서 촬영
    artwork_area_ratio = 1.0
    is_too_small       = False
    if bbox:
        bw, bh = bbox.get("width", 1.0), bbox.get("height", 1.0)
        if bw <= 1.0 and bh <= 1.0:
            artwork_area_ratio = bw * bh
        else:
            ref = original_size if original_size else total_pixels
            artwork_area_ratio = (bw * bh) / ref
        is_too_small = artwork_area_ratio < 0.15

    warnings = []
    if is_blurry:    warnings.append("이미지가 흔들렸거나 흐릿합니다. 초점을 맞추고 선명하게 촬영해 주세요.")
    if is_dark:      warnings.append("사진이 너무 어둡습니다. 조명을 켜거나 밝은 곳에서 촬영해 주세요.")
    if is_glare:     warnings.append("작품 표면에 빛 반사나 눈부심이 심합니다. 촬영 각도를 살짝 비틀어 다시 촬영해 주세요.")
    if is_too_small: warnings.append("그림이 너무 멀리 보입니다. 조금 더 앞으로 다가가서 크게 촬영해 주세요.")

    return {
        "blur_score":          round(blur_score, 1),
        "brightness":          round(brightness, 2),
        "glare_ratio":         round(glare_ratio, 3),
        "max_glare_blob_ratio": round(max_glare_blob_ratio, 3),
        "artwork_area_ratio":  round(artwork_area_ratio, 3),
        "is_blurry":           is_blurry,
        "is_dark":             is_dark,
        "is_glare":            is_glare,
        "is_too_small":        is_too_small,
        "quality_ok":          not (is_blurry or is_dark or is_glare or is_too_small),
        "warnings":            warnings,
    }
