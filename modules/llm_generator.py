import json
import time
import os
import datetime
from typing import Dict, Any

import google.generativeai as genai

# Google Cloud Service Account 자동 감지 (GOOGLE_APPLICATION_CREDENTIALS 없을 때 fallback)
_key_name = "gen-lang-client-0314786043-47efd63839d9.json"
if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
    _possible_paths = [
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend", _key_name),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), _key_name),
        os.path.join(os.path.dirname(__file__), "backend", _key_name),
        os.path.join(os.path.abspath(os.path.dirname(__file__)), _key_name),
    ]
    for _path in _possible_paths:
        if os.path.exists(_path):
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.abspath(_path)
            break

try:
    from google.cloud import vision
    GOOGLE_VISION_AVAILABLE = True
except ImportError:
    GOOGLE_VISION_AVAILABLE = False

_BASE_RULES = """

[핵심 해설 철학 — 반드시 따를 것]:
이 해설의 목적은 미술사 지식 전달이 아니다.
"이 작품이 지금 이 사람의 마음에 어떤 방식으로 닿을 수 있는가"를 설명하는 것이 목적이다.

글의 흐름은 반드시 이 3단계를 따른다:
  1단계 [시각 분석]: 색채·구도·인물 자세·여백·빛의 방향 등 그림 속 요소를 묘사한다.
  2단계 [정서적 작용]: 그 요소가 보는 사람의 마음에 어떤 느낌, 완화감, 쉼, 자극, 거리두기, 응시의 시간을 줄 수 있는지 설명한다.
  3단계 [자기 회고]: 감상자가 자신의 상황에 이 그림을 적용해볼 수 있도록 연결해준다.

[시각 정보 사용 및 환각 방지 엄격 규칙 — 매우 중요]:
1. 오직 제공된 `safe_visual_facts` 리스트에 기재된 정보만을 사실로 간주하여 해설하십시오.
2. `blocked_uncertain_facts`에 열거된 항목이나, `visual_analysis.human` 객체 내에서 `None` 또는 `null`로 지정된 항목(예: pose, gaze, expression이 null인 경우)은 분석 신뢰도가 매우 낮아 판독에서 제외된 상태입니다. 이 비어있는 정보들을 결코 임의로 상상하여 묘사하지 마십시오.
3. 인물 자세/표정의 임의 추측 및 묘사 절대 금지:
   - 인물 자세(`pose`가 null)를 알 수 없는데 "고개를 숙인", "웅크린", "등을 돌린", "무너진 자세", "절망하여 주저앉은" 등으로 인체를 추측 및 단정하여 묘사하지 마십시오.
   - 표정(`expression`이 null)을 알 수 없는데 "슬픈 눈빛", "쓸쓸한 무표정", "체념한 얼굴", "입가에 띤 미소" 등으로 인물의 얼굴/표정을 묘사하지 마십시오.
   - 시선(`gaze`가 null)을 알 수 없는데 "시선을 회피하는", "먼 곳을 응시하는" 등으로 묘사하지 마십시오.
4. 그림 속 인물의 감정 단정 금지:
   - 인물의 정서를 단정하는 표현("인물이 슬픔에 잠겨 있습니다", "인물이 외로워 보입니다")을 철저히 배제하십시오.
   - 대신 오직 감상자가 그 구도와 공간을 통해 느껴볼 수 있는 가능성("감상자에게 고요한 쓸쓸함처럼 느껴질 수 있습니다", "거리감이 생기는 듯한 느낌을 줄 수 있습니다")으로만 감상자 경험 위주로 돌려 말하십시오.

[문체 및 엄격 금지 규칙]:
1. 감상자의 현재 감정 상태를 인위적으로 추측하여 단정하는 문장을 결코 쓰지 마십시오.
   - 금지(단정): "당신은 지금 지쳐 있습니다", "외로움을 느끼고 계시는군요", "이 그림은 당신의 상처를 알아봅니다."
   - 권장(조건형): "유난히 지쳐 마음을 조용히 내려놓고 싶은 날이라면", "가만히 혼자 서 있고 싶었던 기억이 마음 한구석에 있다면", "요즘 마음이 복잡한 시간이 길어졌다면" 처럼 부드러운 조건형으로 유도해야 합니다.
2. 의료·치료적 또는 효과 단정적 표현의 완전한 배제:
   - "아트 테라피"는 의학적 치료가 아닌 "정서적 감상 경험"입니다.
   - "치료", "진단", "회복", "완화", "개선", "효과", "효능"이라는 의학적 뉘앙스의 단어를 직접적/단정적으로 사용하는 것을 엄격히 금지합니다.
   - 반드시 "그렇게 느껴볼 수 있습니다", "잠시 바라보는 데 잔잔한 도움이 될 수 있습니다"와 같이 부드러운 정서적 가능성으로만 한정하여 기술하십시오.
3. [한 줄 위로] 작법의 고도화 (보편적이고 식상한 위로 금지):
   - "오늘도 당신은 괜찮습니다", "충분히 잘하고 있습니다", "소중한 사람입니다"와 같이 기계적이고 뻔하며 오글거리는 일반적 위로의 반복을 절대 금지합니다.
   - `[한 줄 위로]` 문장은 반드시 **작품의 구체적인 시각 요소 하나(예: 푸른 여백, 노란 불빛, 흔들리는 잎사귀 등)를 직접 인용하면서 감상자의 정서와 정교하게 연결**해야 합니다.
   - 예: "이 그림의 깊고 푸른 여백처럼, 분주했던 오늘의 마음에도 잠시 숨을 비워둘 자리가 고요히 머물 수 있기를 바랍니다."

[문체 규칙]:
- 사용자의 일상 고민에서 시작하는 문장을 적어도 한 번 포함하되, 매번 같은 표현을 반복하지 않는다.
  mood_scores에서 가장 높은 감정을 참고해 그에 맞는 도입 문장을 쓴다.
  예) loneliness 높음 → "혼자 있는 시간이 길어질수록, 아무렇지 않은 풍경도 조금 멀게 느껴질 때가 있습니다."
      tension 높음 → "해야 할 일이 많을수록 마음은 앞으로만 달리려 하고, 몸은 오히려 더 굳어질 때가 있습니다."
      sadness 높음 → "뜻대로 되지 않는 날이 쌓이면, 그냥 아무것도 하기 싫어지는 순간이 옵니다."
- 작품 속 시각 요소를 단순 묘사로 끝내지 않는다. 반드시 "그래서 마음에 어떤 방향의 감각을 줄 수 있는지"로 연결한다.
- 정서적 기대효과는 단정하지 않고 가능성으로 부드럽게 제안한다.
  권장 표현: "줄 수 있습니다", "느껴볼 수 있습니다", "마음을 놓아볼 수 있게 합니다",
             "잠시 멈춰 서는 감각을 줄 수 있습니다", "감정을 천천히 바라보게 할 수 있습니다",
             "긴장을 조금 내려놓는 데 도움이 될 수 있습니다"
- 감상자가 그림 속 인물이나 공간에 자신을 투사할 수 있도록 쓴다.
  예: "저 인물의 자세가 지금 당신의 어깨와 닮아 있을지도 모릅니다."
- 마지막 본문 문단은 그림을 어떻게 감상하면 좋을지 작은 행동 제안으로 마무리한다.
  예: "오늘은 이 그림에서 가장 먼저 눈이 머무는 한 곳만 천천히 바라보세요."
- [한 줄 위로]는 행동 제안이 아니라 작품의 분위기와 연결된 짧은 정서적 문장으로 작성한다.
- "~입니다" 단정체보다 "~처럼 느껴질 수 있습니다", "~일지도 모릅니다"를 우선 사용한다.
- 출력은 한국어로 작성한다.

[색채 기술 정확성 규칙 — 매우 중요]:
- dominant_colors의 색상명은 알고리즘 근사값이다. 그대로 번역해 단정하지 말 것.
- average_brightness, warm_color_ratio, cool_color_ratio, saturation 수치를 우선 참고한다.
  예: warm_color_ratio 높음 → "따뜻한 토색 계열", "황토빛 온기"
      cool_color_ratio 높음 → "차가운 청회색 계열"
      brightness 낮음 → "전반적으로 어두운 색조"
- 특정 색 이름은 dominant_colors 상위 1~2위이고 percentage 30% 이상일 때만 명시한다.
- color_moods는 감성 분위기 참고용이다. 직접 나열하지 말고 서술에 자연스럽게 녹인다.

[작품 식별 가이드라인]:
0. user_provided_name이 true이면 사용자가 직접 입력하거나 후보에서 선택한 확정 작품명·화가명이다.
   이 정보를 해설의 첫 문단부터 자연스럽게 사용하고, 이후 문단에서도 작품명·화가명을 반복적으로 인용하여 감상의 중심 축으로 삼아라.
   별도의 DB 맥락 정보가 없더라도 작품명·화가명 자체를 감상의 출발점으로 삼아 해설을 구성하라.
1. identification_status가 'confirmed', 'ocr_confirmed', 'web_confirmed' 또는 'internal_match'이면 작품명·화가를 자연스럽게 인용하고 그 작품의 시대적·개인적 맥락을 정서적 작용과 연결한다.
2. identification_status가 'partial'이면 "이 작품은 ~를 떠올리게 합니다"처럼 추정 표현을 쓴다. 단정 금지.
3. identification_status가 'unknown'이면 작품명·화가를 억지로 지어내지 않는다.
   첫 문장을 반드시 다음 문구로 시작하며, 어떠한 미술사적 생애나 지식도 언급해서는 안 됩니다:
   "정확한 작품명이나 화가 정보가 확인되지 않았기 때문에, 이번 감상은 그림 안에서 직접 보이는 색채와 구도만을 바탕으로 바라보겠습니다."
   그리고 시각 요소만으로 3단계 흐름을 완성한다.

출력 형식 (반드시 지킬 것):
[작품의 첫인상 제목]

본문

[나에게 던지는 질문]
- 질문 1
- 질문 2
- 질문 3
(단, short 모드에서는 질문을 2개만 작성한다)

[한 줄 위로]
위로 문장"""

MODE_PROMPTS = {
    "healing": f"""너는 감상자의 마음을 차분히 돌아보게 돕는 아트 테라피형 감상 안내자(정서 회고 중심)다.
감상자의 현재 마음을 마음대로 단정하거나 의학적 치료 효과를 장담하지 않고, 색채와 여백이 불러오는 감각을 따라 자기 감정을 차분히 돌아보도록 유도하라. 화가 지식이나 역사 설명은 원칙적으로 최소화(10% 이하)합니다.
색채, 구도, 여백, 화면의 밀도와 리듬이 감상자에게 어떤 정서적 감각을 줄 수 있는지 부드럽게 연결하여 설명한다. 인물의 자세·표정·시선은 확실히 식별된 경우에만 조심스럽게 언급하고 절대로 추측하지 않는다.
본문은 5~7문단으로 작성한다.
[우선순위 비율 가이드라인]:
- 감정/회고 및 마음 연결: 60%
- 시각 요소 묘사 및 매칭: 30%
- 미술사 지식 및 배경: 10% 이하{_BASE_RULES}""",

    "docent": f"""너는 지식과 역사를 통해 감상을 풍부하게 하는 미술관 도슨트다.
작품의 시대적 배경, 화가의 삶, 제작 맥락, 작품 속 상징을 60% 비율로 가장 비중 있게 전달하며, 미술사적 지식을 들려주어 감상자가 그림을 더 깊이 바라보도록 돕는 역할을 한다.
정서적 위로나 자기 회고를 과도하게 강조하는 문장을 지양한다. 작품의 시대적 배경, 화가의 삶, 제작 맥락, 상징을 중심으로 설명하되, 직접적인 위로와 자기 회고는 마지막 문단과 [한 줄 위로]에 집중하여 나긋하게 서술하라.
- ❌ 지양(오글거리는 위로): "이 그림은 지금 외로운 당신의 상처를 어루만집니다."
- ⭕ 권장(깊어지는 감상 유도): "이 화가의 숨겨진 절박했던 배경을 알고 나면, 화면의 고요함이 이전과는 조금 다르게 느껴질지도 모릅니다."
- ⭕ 권장(관점의 전환): "화가가 지나온 모진 시간을 함께 떠올려 본다면, 이 어두운 색조 역시 단순한 우울이 아니라 묵묵히 버텨낸 시간의 흔적처럼 보입니다."
본문은 5~7문단으로 구성하며, 다음의 흐름을 지킨다:
1. 작품 혹은 화가와 관련된 시대적/전기적 비하인드 스토리 (60% 비중)
2. 그 배경이 작품의 시각적 요소(색채, 구도, 선)에 남긴 특징적인 흔적 묘사 (20% 비중)
3. 그 흔적과 이야기를 통해 감상자 마음에 조용히 일어나는 정서적 작용 연결 (20% 비중, 마음 연결은 전체적으로 짧고 은은하게만 사용)
4. 마지막 1문단: 감상자가 자신의 오늘 하루와 연결하여 성찰해 볼 수 있는 차분한 도슨트의 닫는 멘트
5. 나에게 던지는 질문 3개 및 작품 시각 연계형 한 줄 위로
[우선순위 비율 가이드라인]:
- 이야기 및 역사적 배경: 60%
- 시각 요소 묘사: 20%
- 정서 작용 및 마음 연결: 20% (직접 위로는 마지막에 집중하되, 은은한 정서 연결은 조화롭게 허용){_BASE_RULES}""",

    "analysis": f"""너는 객관적 시각 분석과 정서 작용을 연결하는 미술 감상 분석 전문가다.
작가 생애나 시대 배경은 핵심 재료로 삼지 않으며, 필요한 경우에도 한 문장 이내로 제한한다. 오직 작품을 처음 대면하는 사람도 눈으로 즉각 식별 가능한 기하학적 시각 요소(65%)를 선별하여 정밀하게 분석한다.
색채, 구도, 시선 이동, 공간감, 형태/질감의 5대 축을 기준으로 삼되, 작품에서 실제로 두드러지는 2~4개 요소를 선별해 유기적으로 분석하며 모든 축을 기계적으로 나열하여 서술하지 않는다. 분석하는 시각 요소마다 "그래서 감상자의 마음에 어떤 정서가 발생하는가"를 바로 이어서 부드럽게 기술한다.
본문은 5~7문단으로 작성한다.
[필수 시각 분석 항목]:
- 색채: 명도, 채도, 온도감, 대비의 조화
- 구도: 중심/비중심 배치, 대칭/비대칭 균형, 구체적인 여백의 쓰임
- 시선 이동: 관람자의 안구가 화면 내에서 이동하는 물리적 시선 흐름
- 공간감: 캔버스 내부에서 느껴지는 깊이, 시각적 압박감, 심리적 거리감
- 형태: 붓터치와 선의 방향성, 형태의 유기적 반복, 질감과 흐름
[우선순위 비율 가이드라인]:
- 순수 시각 요소 정밀 분석: 65%
- 정서적 감각 작용 연결: 30%
- 작가 생애 및 역사적 사실: 5% 이하{_BASE_RULES}""",

    "short": f"""너는 가장 눈에 띄는 요소 하나로 빠르게 마음을 여는 짧은 감상 안내자다.
기계적 공감이나 미사여구를 배제하고, 그림 전체에서 가장 지배적으로 드러나는 시각 요소 단 하나만 선정하여 짧고 선명하게 분석(50%)한다. 여러 요소를 길게 나열하는 것을 배제한다.
선택한 하나의 요소가 감상자에게 어떤 분위기나 정서적 여운을 남길 수 있는지(30%) 간결하고 품격 있게 전달한다.
[분량 및 양식 제약]:
- 본문 분량: 본문 3문단, 약 350~500자 범위 내외로 구성하여 밀도 높게 작성한다.
- 질문 개수: [나에게 던지는 질문]은 반드시 딱 2개만 작성한다.
- 한 줄 위로: [한 줄 위로] 문장은 작품의 한 요소를 담아 깔끔하게 1줄로만 끝맺는다.
[우선순위 비율 가이드라인]:
- 단 하나의 핵심 시각 요소 집중: 50%
- 정서적 작용 및 일상 교감: 30%
- 질문 및 시각 연계 위로: 20%{_BASE_RULES}""",
}

DEPTH_INSTRUCTIONS = {
    "short": "전체 내용을 30초 안에 읽을 수 있는 분량(200~300자)으로 요약한다. 핵심만 담되 도슨트의 따뜻한 말투를 유지한다.",
    "medium": "3분 정도 집중해 읽을 수 있는 분량(600~900자)으로 작성한다. 중요한 정보를 빠짐없이 담되 에세이처럼 흐름이 있어야 한다.",
    "expert": "전문가 수준의 깊이 있는 글(1200자 이상)로 작성한다. 세부 역사 사실, 미술사적 맥락, 작품 속 상징 등을 풍부하게 담는다.",
}

_SOURCE_NOTE = """
[출처 안내]
이 해설은 Google Gemini AI가 일반적으로 알려진 미술사 지식을 바탕으로 생성한 내용입니다.
더 정확한 정보는 아래를 참고하세요:
• 위키피디아 (wikipedia.org) — 화가 생애, 작품 목록
• 구글 아트 앤 컬처 (artsandculture.google.com) — 고해상도 작품, 미술관 정보
• 국립중앙박물관 (museum.go.kr) — 국내 소장 서양화 정보
• 메트로폴리탄 미술관 (metmuseum.org) — 서양 고전 미술
• 루브르 박물관 (louvre.fr) — 프랑스·유럽 미술
"""


_MODELS = ["gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-2.5-flash"]


def _get_model(api_key: str, system: str, model_name: str = _MODELS[0]) -> genai.GenerativeModel:
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(model_name=model_name, system_instruction=system)


def _generate_with_retry(model_fn, prompt: str, api_key: str, system: str) -> str:
    """Try each model in order, retrying once on 429."""
    for model_name in _MODELS:
        model = model_fn(api_key, system, model_name)
        try:
            return model.generate_content(prompt).text
        except Exception as e:
            msg = str(e)
            if "429" in msg or "ResourceExhausted" in msg:
                # Extract retry delay if present, wait up to 30s then try next model
                delay = 30
                try:
                    import re
                    m = re.search(r'retry.*?(\d+)', msg)
                    if m:
                        delay = min(int(m.group(1)) + 2, 30)
                except Exception:
                    pass
                print(f"[LLM] {model_name} rate-limited, waiting {delay}s …")
                time.sleep(delay)
                try:
                    return model.generate_content(prompt).text
                except Exception:
                    print(f"[LLM] {model_name} still failing, trying next model …")
                    continue
            raise
    raise RuntimeError("모든 Gemini 모델이 할당량을 초과했습니다. 잠시 후 다시 시도해주세요.")


def _normalize_vision(r: dict) -> dict:
    recognition = r.get("recognition", [])
    if not isinstance(recognition, list):
        recognition = []
    ocr = r.get("ocr", {})
    if not isinstance(ocr, dict):
        ocr = {}
    figure = r.get("figure", {})
    if not isinstance(figure, dict):
        figure = {}
    return {
        "recognition": recognition[:3],
        "ocr": {
            "title":    ocr.get("title",    ""),
            "artist":   ocr.get("artist",   ""),
            "year":     ocr.get("year",     ""),
            "raw_text": ocr.get("raw_text", ""),
        },
        "figure": {
            "has_person":           bool(figure.get("has_person", False)),
            "face_direction":       figure.get("face_direction",       ""),
            "face_visible":         bool(figure.get("face_visible",    False)),
            "gaze":                 figure.get("gaze",                 ""),
            "expression_ko":        figure.get("expression_ko",        ""),
            "expression_confidence": figure.get("expression_confidence", "low"),
            "posture_ko":           figure.get("posture_ko",           ""),
            "impression_ko":        figure.get("impression_ko",        ""),
        },
    }

# 신뢰 도메인: 이 기관 URL에서 매칭된 결과만 작품 확정 근거로 활용
TRUSTED_DOMAINS = {
    "metmuseum.org", "moma.org", "nga.gov", "tate.org.uk",
    "rijksmuseum.nl", "vangoghmuseum.nl", "getty.edu",
    "artic.edu", "wikipedia.org", "wikimedia.org"
}

_CACHE_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend", "data", "web_detection_cache.json")

def _load_web_cache() -> dict:
    try:
        if os.path.exists(_CACHE_FILE):
            with open(_CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def _save_web_cache(cache_data: dict):
    try:
        os.makedirs(os.path.dirname(_CACHE_FILE), exist_ok=True)
        with open(_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Cache Save Error] {e}", flush=True)

def detect_web_artwork(img_bytes: bytes) -> dict:
    """
    Google Cloud Vision Web Detection API Helper.
    Enforces persistent cache and scores trusted museum/educational domains.
    """
    import hashlib
    img_hash = hashlib.md5(img_bytes).hexdigest()
    
    # 1) 캐시 조회 (Cache Hit Check)
    cache = _load_web_cache()
    if img_hash in cache:
        print(f"[WebDetection Cache Hit] Using cached web info for image hash: {img_hash}", flush=True)
        return cache[img_hash]

    if not GOOGLE_VISION_AVAILABLE or not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        return {"best_guess": "", "entities": [], "matching_pages": [], "has_trusted_domain": False}

    try:
        client = vision.ImageAnnotatorClient()
        image = vision.Image(content=img_bytes)
        response = client.web_detection(image=image)
        web_detection = response.web_detection
        if not web_detection:
            return {"best_guess": "", "entities": [], "matching_pages": [], "has_trusted_domain": False}
        
        # 2) Best Guess 추출
        best_guess = ""
        if web_detection.best_guess_labels:
            best_guess = web_detection.best_guess_labels[0].label
            
        # 3) Web Entities 추출
        entities = []
        for entity in web_detection.web_entities:
            if entity.description and entity.score > 0.4:
                entities.append({
                    "name": entity.description,
                    "score": round(entity.score * 100, 1)
                })
                
        # 4) Matching Pages 및 신뢰 도메인 가중치 부여
        matching_pages = []
        has_trusted_domain = False
        
        if web_detection.pages_with_matching_images:
            for page in web_detection.pages_with_matching_images:
                url = page.url
                if url:
                    # 도메인 추출
                    domain = ""
                    if "://" in url:
                        domain = url.split("://")[1].split("/")[0]
                    else:
                        domain = url.split("/")[0]
                    domain = domain.lower()
                    
                    # sub-domain 포함 여부 체크
                    for td in TRUSTED_DOMAINS:
                        if td in domain:
                            has_trusted_domain = True
                            if td not in matching_pages:
                                matching_pages.append(td)
                            break
                            
        result = {
            "best_guess": best_guess,
            "entities": entities[:8],
            "matching_pages": matching_pages,
            "has_trusted_domain": has_trusted_domain,
            "created_at": str(datetime.date.today())
        }
        
        # 5) 캐시 저장
        cache[img_hash] = result
        _save_web_cache(cache)
        print(f"[WebDetection Cache Saved] API called successfully and cached for hash: {img_hash}", flush=True)
        return result
    except Exception as e:
        print(f"[Google Cloud Vision Web Detection Error] {e}", flush=True)
        return {"best_guess": "", "entities": [], "matching_pages": [], "has_trusted_domain": False}


_EMPTY_VISION = {
    "recognition": [],
    "ocr":    {"title": "", "artist": "", "year": "", "raw_text": ""},
    "figure": {"has_person": False, "face_direction": "", "face_visible": False,
               "gaze": "", "expression_ko": "", "expression_confidence": "low",
               "posture_ko": "", "impression_ko": ""},
}


def analyze_artwork_vision(img_bytes: bytes, api_key: str, original_img_bytes: bytes = None) -> dict:
    """Single Gemini Vision call: recognition + OCR + face/expression."""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")

    # Google Web Detection 결과를 Gemini 프롬프트에 RAG 방식으로 주입
    web_info = detect_web_artwork(img_bytes)
    web_context = ""
    if web_info.get("best_guess") or web_info.get("entities"):
        entities_str = ", ".join([f"{e['name']}(유사도:{e['score']}%)" for e in web_info['entities']])
        web_context = (
            "\n\n[Google Cloud Vision Web Detection 실시간 검색 참고 정보]\n"
            f"- 이미지 최유사 웹 예측 명칭(Best Guess): {web_info['best_guess']}\n"
            f"- 구글 이미지 인덱스 기반 연관 위키백과/웹 엔티티: {entities_str}\n"
            "규칙:\n"
            "- 위 실시간 검색 정보에 나온 작품명, 화가명이 실제 업로드된 명화와 완벽히 매치된다면, "
            "이 정보들의 한국어 번역 및 영문 철자를 최우선순위(1순위)로 'recognition' 목록에 채워 넣으세요."
        )

    prompt = (
        "이 이미지를 분석해주세요. JSON 객체만 반환하고 다른 텍스트는 절대 포함하지 마세요.\n\n"
        "형식:\n"
        '{\n'
        '  "recognition": [{"title":"작품명","artist":"화가명","year":"연도","movement":"미술사조","museum":"소장처","confidence":85,"reason":"추정 근거 한 문장"}],\n'
        '  "ocr": {"title":"","artist":"","year":"","raw_text":""},\n'
        '  "figure": {\n'
        '    "has_person": false,\n'
        '    "face_direction": "",\n'
        '    "face_visible": false,\n'
        '    "gaze": "",\n'
        '    "expression_ko": "",\n'
        '    "expression_confidence": "",\n'
        '    "posture_ko": "",\n'
        '    "impression_ko": ""\n'
        '  }\n'
        '}\n\n'
        "규칙:\n"
        "- recognition: 최대 3개, 유사도 높은 순. confidence 0-100 정수. 인식 불가하면 []\n"
        "- ocr: 이미지 속 텍스트(화판·액자 글씨 등) 추출. 없으면 빈 문자열\n"
        "- figure: 인물이 있을 때만 채움. has_person false면 나머지 빈 문자열\n"
        "- face_direction: 정면/측면/3/4측면/후면/불명확 중 하나\n"
        "- face_visible: 정면뿐 아니라 측면·3/4 얼굴도 true로 처리. 완전히 뒤돌아 있거나 가려진 경우만 false\n"
        "- expression_ko: 얼굴이 일부라도 보이면 표정을 판독해 기입. 예: 슬픔·고통·평온·기쁨·분노·공포·우울·그리움·무표정·긴장감·희망·절망·경이로움\n"
        "  측면·3/4 얼굴도 눈꼬리·입꼬리·눈썹 형태로 표정 추정 가능. face_visible이 false여도 자세·분위기로 추정 가능하면 기입\n"
        "- expression_confidence: high(얼굴이 선명히 보임) / medium(측면·흐릿함) / low(후면·추정만 가능)\n"
        "- impression_ko: 인물 전체 분위기 한 문장"
        + web_context
    )

    if original_img_bytes:
        prompt += (
            "\n\n[Multi-Image Analysis Guideline]\n"
            "- 두 장의 이미지가 전달되었습니다: 첫 번째 이미지는 크롭된 깔끔한 작품 영역이고, 두 번째 이미지는 원본 벽면/방 환경 사진입니다.\n"
            "- 첫 번째 고화질 크롭 이미지에서 표정, 구도, 채색 등 미술적 디테일을 집중 분석하고,\n"
            "- 두 번째 이미지에서 실제 가구, 벽면 대비 작품의 배치 스케일과 공간적 분위기를 읽어내어 분석에 활용해 주세요."
        )

    for attempt in range(2):
        try:
            inputs = []
            inputs.append({"mime_type": "image/jpeg", "data": img_bytes})
            if original_img_bytes:
                inputs.append({"mime_type": "image/jpeg", "data": original_img_bytes})
            inputs.append(prompt)

            response = model.generate_content(inputs)
            text = response.text.strip()
            if "```" in text:
                for chunk in text.split("```"):
                    chunk = chunk.strip().lstrip("json").strip()
                    if not chunk:
                        continue
                    try:
                        r = json.loads(chunk)
                        if isinstance(r, dict):
                            return _normalize_vision(r)
                    except Exception:
                        continue
            else:
                r = json.loads(text)
                if isinstance(r, dict):
                    return _normalize_vision(r)
        except Exception as e:
            if "429" in str(e) and attempt == 0:
                print("[LLM] vision rate-limited, waiting 30s …")
                time.sleep(30)
                continue
            print(f"[LLM] vision error: {e}")
            break
    return _EMPTY_VISION


def recommend_similar(artwork_info: Dict[str, Any], visual_data: Dict[str, Any], api_key: str) -> list:
    """Return up to 4 similar classic artworks."""
    system = _DOCENT_STYLE
    model = _get_model(api_key, system)

    artist = artwork_info.get("artist", "")
    title  = artwork_info.get("title",  "")
    colors = visual_data.get("dominant_colors", [])
    moods  = visual_data.get("color_moods",     [])

    color_str = "·".join(
        c if isinstance(c, str) else c.get("name", "") for c in colors[:4]
    ) if colors else "다양한 색감"
    mood_str = "·".join(moods[:4]) if moods else "감성적"
    base = f"작품: {title} / 화가: {artist}" if title else f"색감: {color_str}"

    prompt = (
        f"다음 조건에 맞는 고전 명화를 4점 추천해주세요.\n{base}\n"
        f"색감: {color_str} / 분위기: {mood_str}\n\n"
        "JSON 배열만 반환하세요 (다른 텍스트 없이):\n"
        '[{"title":"작품명","artist":"화가명","year":"연도","reason":"유사 이유 한 문장"}]\n\n'
        "반드시 실제로 존재하는 유명 고전 명화만 추천하세요."
    )
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        if "```" in text:
            for chunk in text.split("```"):
                chunk = chunk.strip().lstrip("json").strip()
                if not chunk:
                    continue
                try:
                    r = json.loads(chunk)
                    if isinstance(r, list):
                        return r[:4]
                except Exception:
                    continue
        else:
            r = json.loads(text)
            if isinstance(r, list):
                return r[:4]
    except Exception as e:
        print(f"[LLM] recommend_similar error: {e}")
    return []


_ARTWORK_TYPE_HINTS = {
    "인물":     "이 작품은 인물화다. 인물의 위치·자세·표정·시선·행동과 배경의 구도·색감·명암을 함께 분석한다.",
    "풍경":     "이 작품은 풍경화다. 인물을 억지로 찾지 않는다. 공간 배치, 빛의 방향, 색채의 흐름, 수평선, 시선 이동, 여백을 중심으로 분석한다.",
    "추상":     "이 작품은 추상화다. 구체적인 대상이나 장면을 억지로 해석하지 않는다. 색의 대비, 형태의 반복, 선의 방향, 질감, 화면의 밀도, 리듬감, 여백을 중심으로 분석한다.",
    "정물":     "이 작품은 정물화다. 사물의 배치, 빛과 그림자, 질감, 색감, 공간감, 화면 구성을 중심으로 분석한다.",
    "건축":     "이 작품은 건축·도시 장면의 작품이다. 공간감, 원근법, 구조물 배치, 빛과 그림자, 분위기를 중심으로 분석한다.",
    "모르겠어요": "작품의 시각적 특성을 전반적으로 살펴보며 분석한다.",
    "자동":     "",
}

_FOCUS_HINTS = {
    "전체":    "",
    "색감":    "특히 색채 — 색의 선택, 대비, 채도, 온도감, 감정적 연상 — 을 중심으로 깊이 있게 다루어라.",
    "구도":    "특히 구도 — 피사체 배치, 여백, 균형, 시선 이동 — 를 중심으로 깊이 있게 다루어라.",
    "분위기":  "특히 작품 전체의 분위기와 감성적 인상을 중심으로 깊이 있게 다루어라.",
    "인물/장면": "특히 인물이나 장면의 구체적 묘사 — 행동, 표정, 이야기 — 를 중심으로 깊이 있게 다루어라.",
    "내 감정": "감상자의 감정 회고와 연결되도록 — 이 작품이 감상자의 마음에 어떤 울림을 주는지 — 를 중심으로 깊이 있게 다루어라.",
}


def generate_sketch_reflection(
    sketch_bytes: bytes,
    palette: list,
    keywords: list,
    guide_q: str,
    api_key: str,
    mode: str = "short",
) -> str:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        "gemini-2.0-flash",
        system_instruction=(
            "너는 미술 감상 보조 AI다. 사용자가 명화 감상 후 그린 마음 스케치를 함께 읽어주는 회고 안내자다.\n"
            "규칙:\n"
            "- 감정을 진단하거나 심리 상태를 단정하지 않는다. '당신은 우울합니다', '불안 상태입니다' 같은 표현 절대 금지.\n"
            "- 색, 선의 방향과 강약, 여백, 형태의 반복을 묘사하고, 어떤 분위기를 만들 수 있는지 부드럽게 이야기한다.\n"
            "- '~처럼 느껴질 수 있어요', '~한 인상을 줍니다', '~일지도 모릅니다' 같은 표현을 사용한다.\n"
            "- 관람객 옆에서 조용히 속삭이듯 따뜻하게 쓴다.\n"
            "- 한국어로만 답변한다."
        ),
    )

    palette_str = "·".join(
        c.get("name", "") if isinstance(c, dict) else str(c)
        for c in palette[:5] if c
    ) or "다양한 색"
    keyword_str = "·".join(str(k) for k in keywords[:5]) if keywords else "없음"

    if mode == "short":
        instruction = "2~3문장으로 짧고 따뜻하게 전체적인 느낌을 이야기해주세요."
    else:
        instruction = (
            "다음 네 항목 순서로 써주세요. 각 항목은 대괄호 제목 한 줄 + 설명:\n"
            "[사용된 색]\n[선의 느낌]\n[원작과의 연결]\n[회고 문장]"
        )

    prompt = (
        f"다음은 사용자가 명화 감상 후 그린 마음 스케치입니다.\n\n"
        f"원작 팔레트: {palette_str}\n"
        f"감정 키워드: {keyword_str}\n"
        f"감상 가이드 질문: {guide_q or '없음'}\n\n"
        f"{instruction}"
    )

    for attempt in range(2):
        try:
            resp = model.generate_content([
                {"mime_type": "image/jpeg", "data": sketch_bytes},
                prompt,
            ])
            return resp.text.strip()
        except ValueError:
            return "마음 스케치를 자세히 살펴보기 어렵습니다. 하지만 당신만의 색깔과 선이 담긴 멋진 스케치네요. 어떤 마음으로 선을 그었는지 스스로 되돌아보는 것도 좋은 감상이 될 거예요."
        except Exception as e:
            if ("429" in str(e) or "ResourceExhausted" in str(e)) and attempt == 0:
                time.sleep(20)
                continue
            raise
    return ""


def generate_docent_reply(artwork_info: Dict[str, Any], message: str, api_key: str) -> str:
    system = (
        "너는 미술관 도슨트다. 작품 감상을 돕는 친절하고 지적인 가이드.\n"
        "규칙: 심리 진단·치료 언급 절대 금지. 작품의 색채·구도·역사·분위기에 집중.\n"
        "짧고 따뜻하게 2~4문장으로 답변. 한국어로만 답변."
    )
    ctx    = json.dumps(artwork_info, ensure_ascii=False)
    prompt = f"작품 정보: {ctx}\n\n감상자 질문: {message}"
    return _generate_with_retry(_get_model, prompt, api_key, system)


def _build_color_summary(analysis_data: Dict[str, Any]) -> str:
    """Build a human-readable color summary for the LLM, more accurate than raw color names."""
    color = analysis_data.get("color", {})
    brightness = color.get("average_brightness", 0.5)
    saturation = color.get("average_saturation", 0.5)
    warm_ratio = color.get("warm_color_ratio", 0.3)
    cool_ratio = color.get("cool_color_ratio", 0.3)
    contrast = color.get("contrast_level", 0.5)

    parts = []
    if brightness < 0.35:
        parts.append("전반적으로 어둡고 낮은 명도")
    elif brightness > 0.65:
        parts.append("전반적으로 밝고 높은 명도")
    else:
        parts.append("중간 명도")

    if warm_ratio > 0.55:
        parts.append("따뜻한 황토·적갈색 계열이 주를 이룸")
    elif warm_ratio > 0.40:
        parts.append("온기 있는 색조가 상당 부분 포함")
    elif cool_ratio > 0.45:
        parts.append("차가운 청색·청회색 계열이 주를 이룸")
    elif cool_ratio > 0.30:
        parts.append("서늘한 색조가 일부 포함")

    if saturation < 0.2:
        parts.append("채도 낮음(무채색에 가까움)")
    elif saturation > 0.55:
        parts.append("채도 높음(선명하고 강렬한 색)")

    if contrast > 0.6:
        parts.append("명암 대비 강함")
    elif contrast < 0.3:
        parts.append("명암 대비 부드러움")

    dominant = color.get("dominant_colors", [])
    top_colors = [c for c in dominant[:3] if isinstance(c, dict) and c.get("percentage", 0) >= 0.30]
    if top_colors:
        names = "·".join(c.get("name", "") for c in top_colors)
        parts.append(f"상위 주조색(30% 이상): {names}")

    return " / ".join(parts) if parts else "색채 정보 없음"


def check_unsupported_visual_claims(text: str, payload: dict) -> list[str]:
    violations = []
    visual = payload.get("visual_analysis", {})
    human = visual.get("human", {})
    
    # 1. If human detected is False, but text mentions a person in detail
    if not human.get("detected", False):
        person_keywords = ["그림 속 인물", "인물의 자세", "그의 어깨", "그녀의", "그의 표정", "웅크린", "고개를 숙"]
        for p in person_keywords:
            if p in text:
                violations.append(f"인물이 검출되지 않았으나 인물 관련 묘사 감지: '{p}'")
                break
                
    # 2. If pose is None, check for risky pose keywords
    if human.get("detected", False) and not human.get("pose"):
        risky_poses = [
            "고개를 숙", "웅크려", "웅크린", "주저앉", "무너진 자세", "등을 돌", 
            "구부정한", "구부린", "자세로 앉"
        ]
        for p in risky_poses:
            if p in text:
                violations.append(f"자세 판독값이 제공되지 않았으나 자세 관련 단정 감지: '{p}'")
                break
                
    # 3. If expression is None, check for expression keywords
    if human.get("detected", False) and not human.get("expression"):
        risky_expressions = [
            "슬픈 표정", "체념한 얼굴", "체념한 듯", "쓸쓸한 얼굴", "쓸쓸한 무표정", 
            "기쁜 표정", "표정을 짓", "미소를 짓"
        ]
        for p in risky_expressions:
            if p in text:
                violations.append(f"표정 판독값이 제공되지 않았으나 표정 관련 단정 감지: '{p}'")
                break
                
    # 4. If gaze is None, check for gaze keywords
    if human.get("detected", False) and not human.get("gaze"):
        risky_gazes = [
            "먼 곳을 응", "시선을 피", "어딘가를 바라", "눈빛으로"
        ]
        for p in risky_gazes:
            if p in text:
                violations.append(f"시선 판독값이 제공되지 않았으나 시선 관련 단정 감지: '{p}'")
                break
                
    return violations


def generate_interpretation(analysis_data: Dict[str, Any], api_key: str,
                             mode: str = "healing",
                             artwork_type: str = "자동",
                             analysis_focus: str = "전체",
                             artwork_description: str = "") -> str:
    system = MODE_PROMPTS.get(mode, MODE_PROMPTS["healing"])
    extra_parts = [_ARTWORK_TYPE_HINTS.get(artwork_type, ""), _FOCUS_HINTS.get(analysis_focus, "")]
    extra = "\n".join(p for p in extra_parts if p)
    if extra:
        system = extra + "\n\n" + system
    analysis_json = json.dumps(analysis_data, ensure_ascii=False, indent=2)
    color_summary = _build_color_summary(analysis_data)
    desc_block = (
        f"\n[작품 배경 정보]\n{artwork_description.strip()}\n"
        "위 배경 정보를 감상 해설에 자연스럽게 녹여주세요. 사실 나열이 아니라 감상자가 이 작품을 더 깊이 느낄 수 있도록 이야기처럼 풀어주세요.\n"
    ) if artwork_description.strip() else ""
    user_name_prefix = ""
    if analysis_data.get("user_provided_name"):
        artwork_info = analysis_data.get("artwork_info", {})
        _title  = artwork_info.get("title",  "")
        _artist = artwork_info.get("artist", "")
        if _title or _artist:
            user_name_prefix = (
                f"[사용자 직접 확인 작품 — 해설 전반에 반드시 활용]\n"
                f"작품명: {_title or '미정'}  /  화가: {_artist or '미정'}\n"
                "위 작품명과 화가명은 사용자가 직접 입력하거나 후보에서 선택한 확정 정보입니다. "
                "해설 첫 문단부터 이 작품명을 자연스럽게 언급하고, 이후 문단에서도 반복적으로 인용하여 감상의 중심 축으로 삼으세요.\n\n"
            )
    prompt = (
        user_name_prefix +
        "다음은 그림에 대한 시각 분석 결과입니다. "
        "이 결과를 바탕으로 감성적인 미술 감상 해설을 작성해주세요.\n\n"
        f"[색채 요약 — 이 수치 기반으로 색채를 기술하세요]\n{color_summary}\n\n"
        f"[전체 분석 JSON]\n{analysis_json}{desc_block}"
    )
    
    # 1st attempt
    essay = _generate_with_retry(_get_model, prompt, api_key, system)
    
    # Validator
    violations = check_unsupported_visual_claims(essay, analysis_data)
    if violations:
        correction_system = (
            system + "\n\n"
            "[🚨 보안 보정 긴급 지시사항]\n"
            "이전 생성된 감상문에서 이미지 판독 결과와 어긋나는 잘못된 사실 혹은 임의의 추측 묘사가 발견되었습니다.\n"
            f"검출된 위반 사항: {', '.join(violations)}\n\n"
            "반드시 아래의 수칙을 즉시 적용하여 해설을 전면 재작성하십시오:\n"
            "- 판독 결과(safe_visual_facts)에 표기되지 않은 구체적 인체 묘사(예: 고개를 숙이거나, 웅크렸거나, 슬픈 표정 등)를 완전히 삭제하십시오.\n"
            "- 절대로 임의로 인물의 자세나 표정을 마음대로 단정하여 서술을 지어내지 마십시오.\n"
            "- 제공된 순수 색채와 구도 사실만을 100% 사용하여 차분하고 감성적인 해설을 작성하십시오."
        )
        print(f"[PostValidator] Unsupported claims detected: {violations}. Retrying generation...", flush=True)
        essay = _generate_with_retry(_get_model, prompt, api_key, correction_system)
        
    return essay


_DOCENT_STYLE = """
너는 미술관 도슨트다. 차분하고 따뜻하며 지적인 말투로 설명한다.
백과사전처럼 딱딱하지 않고, 관람객 옆에서 조용히 속삭이듯 이야기한다.
역사적 사실은 일반적으로 알려진 내용에 한정하며, 불확실한 내용은 
"알려져 있습니다", "전해집니다", "추정됩니다"와 같이 표현한다.
출력은 한국어로 작성한다.
"""

def generate_artist_story(artwork_info: Dict[str, Any], api_key: str,
                           depth: str = "medium") -> tuple[str, str]:
    """화가의 삶 해설 생성. Returns (content, source_note)."""
    system = _DOCENT_STYLE + f"\n{DEPTH_INSTRUCTIONS[depth]}"
    model = _get_model(api_key, system)

    artist = artwork_info.get("artist", "이 작품의 화가")
    title  = artwork_info.get("title",  "이 작품")
    year   = artwork_info.get("year",   "")

    prompt = f"""
화가: {artist}
작품: {title} ({year})

위 화가의 삶과 예술 세계를 설명해주세요.
포함할 내용:
1. 생애 개요 (출생·사망, 주요 활동 시기)
2. 작품 세계와 화풍의 특징
3. 대표작 2~3점 언급
4. 이 작품 '{title}'이 화가의 생애 어느 시점에 그려졌는지, 
   그 시기 화가의 삶과 이 작품의 연결고리

도슨트처럼 따뜻하게 이야기해주세요.
"""
    response = model.generate_content(prompt)
    return response.text, _SOURCE_NOTE


def generate_era_context(artwork_info: Dict[str, Any], api_key: str,
                          depth: str = "medium") -> tuple[str, str]:
    """시대적 배경 해설 생성. Returns (content, source_note)."""
    system = _DOCENT_STYLE + f"\n{DEPTH_INSTRUCTIONS[depth]}"
    model = _get_model(api_key, system)

    artist = artwork_info.get("artist", "이 화가")
    title  = artwork_info.get("title",  "이 작품")
    year   = artwork_info.get("year",   "제작 시기")

    prompt = f"""
작품: {title}
화가: {artist}
제작 연도: {year}

위 작품이 탄생한 시대적 배경을 설명해주세요.
포함할 내용:
1. 제작 당시의 시대적 상황 (정치·사회·문화)
2. 당시 유럽 미술계의 분위기와 주류 사조
3. 이 작품이 속한 미술 사조 (인상주의, 바로크, 낭만주의 등)와 그 특징
4. 시대적 맥락이 이 작품에 어떤 영향을 미쳤는지

도슨트처럼 차분하고 따뜻하게 이야기해주세요.
"""
    response = model.generate_content(prompt)
    return response.text, _SOURCE_NOTE


def generate_hidden_story(artwork_info: Dict[str, Any],
                           visual_data: Dict[str, Any],
                           api_key: str,
                           depth: str = "medium") -> tuple[str, str]:
    """작품 속 숨은 이야기 해설 생성. Returns (content, source_note)."""
    system = _DOCENT_STYLE + f"\n{DEPTH_INSTRUCTIONS[depth]}"
    model = _get_model(api_key, system)

    artist  = artwork_info.get("artist", "화가")
    title   = artwork_info.get("title",  "이 작품")
    colors  = visual_data.get("dominant_colors", [])
    comp    = visual_data.get("composition", {})
    person  = visual_data.get("human", {})

    color_str = "·".join(colors[:4]) if colors else "다양한 색채"
    pose_str  = person.get("posture", "") or person.get("pose", "")

    prompt = f"""
작품: {title}
화가: {artist}
분석된 색채: {color_str}
구도 특징: 주요 피사체 위치 {comp.get('position','중앙')}, 
           여백 비율 {comp.get('negative_space', 0.3):.0%}
인물 자세: {pose_str or '해당 없음'}

위 정보를 바탕으로 작품 속 숨은 이야기를 설명해주세요.
포함할 내용:
1. 작품에 사용된 색채의 상징적 의미
2. 구도와 배치에 담긴 의도
3. 인물이 있다면 표정·자세·시선이 전달하는 메시지
4. 배경 속 숨겨진 요소나 상징 (알려진 것에 한정)
5. 이 작품을 처음 본 당시 관람객들의 반응 (알려진 내용)

마치 그림 앞에 서서 속삭이듯 설명해주세요.
"""
    response = model.generate_content(prompt)
    return response.text, _SOURCE_NOTE


def generate_similar_artworks(artwork_info: Dict[str, Any],
                               visual_data: Dict[str, Any],
                               api_key: str,
                               depth: str = "medium") -> tuple[str, str]:
    """비슷한 명화 추천 생성. Returns (content, source_note)."""
    system = _DOCENT_STYLE + f"\n{DEPTH_INSTRUCTIONS[depth]}"
    model = _get_model(api_key, system)

    artist = artwork_info.get("artist", "화가")
    title  = artwork_info.get("title",  "이 작품")
    colors = visual_data.get("dominant_colors", [])
    moods  = visual_data.get("color_moods", [])

    color_str = "·".join(colors[:4]) if colors else "다양한 색감"
    mood_str  = "·".join(moods[:4])  if moods  else "감성적"

    prompt = f"""
작품: {title}
화가: {artist}
색감 특징: {color_str}
분위기: {mood_str}

위 작품과 비슷한 고전 명화 3~5점을 추천해주세요.
각 추천 작품마다:
1. 작품명 (화가, 제작연도)
2. 이 작품과 어떤 점이 비슷한지 (색감/분위기/주제/사조)
3. 이 작품을 좋아하는 사람이 왜 이 추천작도 좋아할지

반드시 실제로 존재하는 유명한 고전 명화만 추천하세요.
불확실한 경우 추천하지 마세요.
도슨트처럼 따뜻하고 흥미롭게 소개해주세요.
"""
    response = model.generate_content(prompt)
    return response.text, _SOURCE_NOTE


_STATIC_ERA_DATA = {
    # ════════════════════════════════════════════════════════════════════
    # Vincent van Gogh
    # ════════════════════════════════════════════════════════════════════
    "The Starry Night": {
        "creation_period": "1889년 6월, 반 고흐가 생레미드프로방스 정신병원에 자발적으로 입원하던 시기에 제작되었습니다.",
        "art_movement": "후기 인상주의",
        "historical_context": "19세기 후반 유럽은 산업혁명의 여파로 급격한 사회 변화를 겪고 있었습니다. 프랑스를 중심으로 개인의 감정과 내면 세계를 표현하는 후기 인상주의가 부상했고, 반 고흐·고갱·세잔 등이 각자의 화풍을 발전시키던 시기였습니다.",
        "artist_context": "반 고흐는 1889년 자발적으로 생레미 정신병원에 입원해 치료를 받으면서도 왕성한 창작 활동을 이어갔습니다. 별이 빛나는 밤은 병원 창문 너머 바라본 밤하늘을 상상력으로 재구성한 작품으로, 그의 내면 소용돌이와 자연에 대한 경외심이 담겨 있습니다.",
        "visual_connection": "소용돌이치는 붓터치와 강렬한 파란색·황금색 대비는 반 고흐가 당시 겪은 내면의 격동을 시각화합니다. 두꺼운 임파스토 기법과 주관적 색채 사용이 후기 인상주의의 특징을 잘 보여줍니다.",
    },
    "Sunflowers": {
        "creation_period": "1888년, 반 고흐가 남프랑스 아를(Arles)에 머물며 두 차례에 걸쳐 연작으로 제작했습니다.",
        "art_movement": "후기 인상주의",
        "historical_context": "19세기 후반 아를의 강렬한 햇빛과 색채는 반 고흐에게 큰 영감을 주었습니다. 이 시기 그는 폴 고갱과 함께 예술가 공동체를 꿈꾸며 황색의 집(Yellow House)에 머물고 있었습니다.",
        "artist_context": "반 고흐는 고갱을 아를로 초대하기 위해 그의 방을 해바라기로 장식하려 했습니다. 그에게 해바라기는 태양·감사·희망을 상징했으며, 연작 제작에 강렬한 열정을 쏟았습니다.",
        "visual_connection": "두껍게 쌓인 물감과 황금빛 계열의 풍부한 색조는 남프랑스의 강렬한 햇빛과 반 고흐의 열정적인 내면을 동시에 표현합니다.",
    },
    "Almond Blossom": {
        "creation_period": "1890년 2월, 반 고흐가 생레미 정신병원에서 갓 태어난 조카 빌럼을 위해 제작했습니다.",
        "art_movement": "후기 인상주의",
        "historical_context": "19세기 말 유럽에는 일본 우키요에 판화의 영향이 확산되고 있었습니다. 반 고흐는 일본 미술에 깊이 매료되어 있었으며, 아몬드 나무는 일본화의 벚꽃 모티프에서 영감을 받았습니다.",
        "artist_context": "반 고흐의 동생 테오가 아들을 낳자, 반 고흐는 기쁜 마음으로 조카 빌럼에게 이 작품을 선물했습니다. 그에게 아몬드 꽃은 새 생명과 봄의 희망을 상징했습니다.",
        "visual_connection": "파란 하늘을 배경으로 뻗은 흰 꽃 가지는 일본 우키요에의 구도에서 영향을 받은 것으로, 생명의 시작과 순수함을 시각적으로 구현합니다.",
    },
    "Water Lilies": {
        "creation_period": "1896년부터 1926년까지, 모네가 지베르니 정원 수련 연못을 주제로 약 250여 점의 연작을 제작했습니다.",
        "art_movement": "인상주의",
        "historical_context": "19세기 말~20세기 초 프랑스는 벨 에포크(Belle Époque) 시대로, 예술과 문화가 융성했습니다. 인상주의는 이미 주류 예술 운동으로 자리잡았고, 모네는 빛의 순간적 변화를 포착하는 데 평생을 헌신했습니다.",
        "artist_context": "모네는 말년에 백내장으로 시력이 점차 나빠지면서도 지베르니 수련 연작에 몰두했습니다. 색채 인식이 변화하면서 후기 수련 작품들은 점점 추상적인 성격을 띠게 되었습니다.",
        "visual_connection": "수면 위에 반영되는 하늘과 수련의 색채는 고정된 형태 없이 빛과 색으로만 표현되어, 인상주의의 핵심인 순간적 빛의 포착을 완벽히 구현합니다.",
    },
    "The Kiss": {
        "creation_period": "1907~1908년, 구스타프 클림트의 황금 시기(Golden Phase)를 대표하는 작품입니다.",
        "art_movement": "상징주의 / 아르누보",
        "historical_context": "20세기 초 빈은 합스부르크 제국의 수도로 화려한 문화의 중심지였습니다. 분리파(Secession) 운동이 활발했고, 전통적 아카데미즘에서 벗어나 새로운 예술을 추구하는 움직임이 강했습니다.",
        "artist_context": "클림트는 빈 분리파의 창립 멤버로, 황금빛 장식과 관능적 표현을 결합한 독특한 화풍으로 유명했습니다. 비잔틴 모자이크와 일본 우키요에에서 영향을 받아 화려한 금박 기법을 발전시켰습니다.",
        "visual_connection": "금박과 기하학적 문양으로 뒤덮인 두 연인의 모습은 세기말 빈의 화려함을 반영합니다. 배경과 인물의 경계가 흐릿해지는 구성은 현실과 꿈의 경계를 허무는 상징주의적 특성을 보여줍니다.",
    },
    "The Scream": {
        "creation_period": "1893년 제작. 뭉크는 같은 주제로 회화·파스텔·판화 등 여러 버전을 남겼습니다.",
        "art_movement": "표현주의",
        "historical_context": "19세기 말 유럽은 산업화와 도시화로 인한 불안과 소외감이 팽배했습니다. 니체의 철학과 프로이트의 정신분석학이 대두되며 인간 내면과 무의식에 대한 관심이 높아지던 시기였습니다.",
        "artist_context": "뭉크는 어린 시절 어머니와 누나를 잃는 불행한 경험을 했습니다. 그는 실제로 산책 중 하늘이 핏빛으로 물드는 것을 보고 극심한 불안을 느꼈다는 기록을 남겼으며, 이 경험이 절규 탄생의 계기가 되었습니다.",
        "visual_connection": "굴곡진 선과 비틀린 형태, 강렬한 붉은 하늘은 내면의 공포와 실존적 불안을 시각화합니다. 자연의 물결치는 곡선이 인물의 절규와 하나가 되어 표현주의의 감정 외화(外化)를 구현합니다.",
    },
    "Mona Lisa": {
        "creation_period": "1503~1519년경, 레오나르도 다 빈치가 피렌체에서 시작해 프랑스에서 완성했습니다.",
        "art_movement": "르네상스",
        "historical_context": "15~16세기 이탈리아 르네상스는 인문주의와 고전 문화 부흥을 중심으로 예술·과학·철학이 융합되던 시기였습니다. 피렌체는 메디치 가문의 후원 아래 유럽 예술의 중심지로 번성했습니다.",
        "artist_context": "다 빈치는 화가뿐 아니라 과학자·발명가·해부학자였습니다. 그는 스푸마토(sfumato) 기법을 개발해 윤곽선 없이 색조의 미묘한 변화로 형태를 표현했으며, 모나리자는 이 기법의 정점으로 꼽힙니다.",
        "visual_connection": "스푸마토 기법으로 처리된 신비로운 미소와 배경의 안개 낀 풍경은 르네상스의 이상인 자연의 과학적 관찰과 인간 내면 표현을 동시에 구현합니다.",
    },
    "Girl with a Pearl Earring": {
        "creation_period": "1665년경, 요하네스 페르메이르가 네덜란드 델프트에서 제작한 것으로 추정됩니다.",
        "art_movement": "바로크 / 네덜란드 황금시대",
        "historical_context": "17세기 네덜란드는 해상 무역으로 번성한 황금시대를 맞이했습니다. 부유한 상인 계층의 등장으로 예술 시장이 확대되었고, 일상생활을 사실적으로 묘사하는 장르화가 발달했습니다.",
        "artist_context": "페르메이르는 빛을 다루는 탁월한 능력으로 유명했습니다. 그는 평생 델프트를 거의 벗어나지 않으며 소규모의 정밀한 작품을 제작했고, 생전에는 그다지 유명하지 않았습니다.",
        "visual_connection": "어두운 배경에서 빛을 받아 빛나는 진주 귀걸이와 소녀의 피부는 페르메이르 특유의 빛 표현 기법을 보여줍니다. 강렬한 시선과 반쯤 열린 입술은 신비로운 분위기를 자아냅니다.",
    },
    "The Birth of Venus": {
        "creation_period": "1484~1486년경, 산드로 보티첼리가 피렌체에서 제작했습니다.",
        "art_movement": "초기 르네상스",
        "historical_context": "15세기 피렌체는 메디치 가문의 후원 아래 인문주의와 신플라톤주의가 꽃핀 르네상스의 중심지였습니다. 고대 그리스·로마 신화에 대한 관심이 되살아나며 신화적 주제의 회화가 발달했습니다.",
        "artist_context": "보티첼리는 메디치 가문의 총애를 받은 화가로, 신화와 알레고리를 주제로 한 대형 작품을 다수 제작했습니다. 그의 우아한 선과 섬세한 색채는 초기 르네상스의 이상적 아름다움을 구현했습니다.",
        "visual_connection": "조개껍질 위에 서 있는 비너스의 우아한 자세와 바람에 흩날리는 머리칼은 고대 그리스 조각의 영향과 르네상스 이상미의 결합을 보여줍니다.",
    },
    "Guernica": {
        "creation_period": "1937년, 스페인 내전 중 게르니카 폭격 사건에 항의하여 파블로 피카소가 제작했습니다.",
        "art_movement": "큐비즘 / 표현주의",
        "historical_context": "1937년 스페인 내전 중 나치 독일 공군이 바스크 지방 소도시 게르니카를 무차별 폭격해 수백 명의 민간인이 사망했습니다. 이 사건은 전 세계에 충격을 주었으며 반파시즘 운동의 상징이 되었습니다.",
        "artist_context": "피카소는 당시 파리 만국박람회 스페인관 벽화를 의뢰받은 상태였습니다. 게르니카 폭격 소식을 듣고 기존 계획을 바꿔 이 작품을 단 한 달 만에 완성했습니다.",
        "visual_connection": "흑백의 무채색 팔레트는 전쟁의 참혹함과 죽음을 상징하며, 뒤틀리고 분열된 형태들은 큐비즘 기법으로 공포와 혼란을 극대화합니다.",
    },
    "The Last Supper": {
        "creation_period": "1495~1498년, 레오나르도 다 빈치가 밀라노 산타마리아 델레 그라치에 성당 식당 벽에 그린 벽화입니다.",
        "art_movement": "르네상스",
        "historical_context": "15세기 말 밀라노는 스포르차 공작 가문의 통치 하에 있었으며, 다 빈치는 루도비코 스포르차의 궁정 화가로 활동했습니다. 이탈리아는 프랑스의 침략 위협을 받고 있었습니다.",
        "artist_context": "다 빈치는 이 작품에서 예수가 '너희 중 하나가 나를 배신할 것이다'라고 말하는 순간을 포착했습니다. 각 사도의 표정과 몸짓을 통해 충격·부정·슬픔 등 다양한 감정을 사실적으로 표현했습니다.",
        "visual_connection": "완벽한 원근법 구성과 예수를 중심으로 한 사도들의 배치는 르네상스의 조화·균형 미학을 보여주며, 건축적 배경이 시선을 자연스럽게 예수에게 집중시킵니다.",
    },
    "Impression, Sunrise": {
        "creation_period": "1872년, 클로드 모네가 프랑스 르아브르 항구의 일출을 빠르게 포착해 제작했습니다.",
        "art_movement": "인상주의 (이 작품이 운동의 이름이 되었습니다)",
        "historical_context": "1870년대 프랑스는 보불전쟁(1870~71) 패배 후 재건 중이었습니다. 전통적 아카데미 회화에 반발한 화가들이 자연의 빛과 순간적 인상을 포착하는 새로운 기법을 실험하고 있었습니다.",
        "artist_context": "1874년 이 작품이 전시될 때 비평가 루이 르루아가 '인상'이라는 제목을 비웃으며 '인상주의자들'이라 조롱했고, 이 단어가 운동의 이름으로 굳어졌습니다.",
        "visual_connection": "안개 낀 항구의 주황빛 태양과 물 위의 반영은 단 몇 번의 붓터치로 표현되어, 인상주의의 핵심인 순간의 빛과 분위기 포착을 완벽하게 보여줍니다.",
    },
    "Starry Night Over the Rhône": {
        "creation_period": "1888년 9월, 반 고흐가 프랑스 아를에 머물던 시기에 론 강변에서 직접 바라보며 제작했습니다.",
        "art_movement": "후기 인상주의",
        "historical_context": "19세기 후반 아를은 반 고흐에게 색채와 빛의 영감을 준 곳이었습니다. 그는 이 시기 고갱과 함께 예술가 공동체를 꿈꾸며 황색의 집에서 생활했습니다.",
        "artist_context": "반 고흐는 밤 풍경을 그리기 위해 실제로 밤에 야외에 나가 그림을 그렸습니다. 그는 밤이 낮보다 더 풍부한 색채를 지닌다고 믿었으며, 론 강의 별빛을 사랑했습니다.",
        "visual_connection": "강 위에 반영된 가스등의 노란빛과 파란 밤하늘의 별빛 대비는 반 고흐 특유의 보색 대비 기법을 보여주며, 굵고 역동적인 붓터치가 밤의 생동감을 표현합니다.",
    },
    "Bedroom in Arles": {
        "creation_period": "1888년 10월, 반 고흐가 아를의 황색의 집에서 자신의 침실을 그린 작품으로 세 가지 버전이 존재합니다.",
        "art_movement": "후기 인상주의",
        "historical_context": "19세기 말 반 고흐는 남프랑스 아를에서 예술가 공동체를 꿈꾸며 황색의 집을 임대해 살았습니다. 고갱의 방문을 앞두고 집을 꾸미던 시기였습니다.",
        "artist_context": "반 고흐는 이 작품을 '휴식'을 표현한 그림으로 설명했습니다. 강렬한 색채를 사용했지만, 의도적으로 단순하고 편안한 공간을 연출하려 했습니다.",
        "visual_connection": "원근법이 의도적으로 왜곡된 실내 공간과 평면적인 색채 표현은 일본 우키요에의 영향을 보여줍니다. 보색 대비와 두꺼운 윤곽선이 반 고흐의 개성적인 화풍을 드러냅니다.",
    },
    "Café Terrace at Night": {
        "creation_period": "1888년 9월, 반 고흐가 아를의 포럼 광장의 카페를 밤에 직접 야외에서 그린 작품입니다.",
        "art_movement": "후기 인상주의",
        "historical_context": "19세기 후반 아를의 카페는 시민들의 사교 공간이었습니다. 가스등이 도시 곳곳에 설치되던 시기로, 인공 조명이 만들어내는 밤의 풍경이 새로운 회화적 주제로 주목받았습니다.",
        "artist_context": "반 고흐는 검은색을 쓰지 않고도 밤을 표현할 수 있다고 믿었습니다. 이 작품은 그가 밤 야외에서 직접 캔버스에 그린 최초의 작품 중 하나로 알려져 있습니다.",
        "visual_connection": "가스등의 따뜻한 황금빛과 푸른 밤하늘의 별빛이 강렬한 보색 대비를 이루며, 카페의 온기와 밤의 서늘함을 동시에 표현합니다.",
    },
    "Irises": {
        "creation_period": "1889년 5월, 반 고흐가 생레미 정신병원 정원에서 제작한 작품입니다.",
        "art_movement": "후기 인상주의",
        "historical_context": "19세기 말 유럽에서는 일본 우키요에 판화에 대한 관심이 높았습니다. 반 고흐도 일본화에 깊은 영향을 받았으며, 붓꽃은 일본 미술에서 즐겨 다루는 소재였습니다.",
        "artist_context": "반 고흐는 생레미 입원 초기 병원 정원을 거닐며 마음의 안정을 찾으려 했습니다. 붓꽃 연작은 이 시기의 비교적 차분하고 세밀한 관찰을 반영합니다.",
        "visual_connection": "생생한 파란 붓꽃과 주황빛 흙의 보색 대비, 물결치는 꽃잎의 유기적 형태는 생명력과 활기를 전달하며 일본 판화의 평면적 구성에서 영향받은 요소를 보여줍니다.",
    },
    "The Potato Eaters": {
        "creation_period": "1885년 4월, 반 고흐가 네덜란드 뉘넨에서 농민 가족을 주제로 제작한 초기 대표작입니다.",
        "art_movement": "사실주의 / 초기 후기 인상주의",
        "historical_context": "19세기 후반 네덜란드 농촌에서는 산업화의 영향으로 빈민 농가의 생활이 더욱 어려워지고 있었습니다. 밀레·쿠르베 등 사실주의 화가들의 영향으로 노동자 계층의 삶을 그리는 예술이 주목받았습니다.",
        "artist_context": "반 고흐는 당시 목사로 활동하며 빈민 광부·농민들과 생활한 경험이 있었습니다. 그는 농민의 거친 손과 삶의 진실함을 미화 없이 솔직하게 표현하려 했습니다.",
        "visual_connection": "어두운 갈색과 황토색 위주의 팔레트는 흙과 가난의 이미지를 강조하며, 투박한 인물 묘사와 거친 붓터치는 농민 삶의 고단함을 직접적으로 전달합니다.",
    },
    "Wheat Field with Crows": {
        "creation_period": "1890년 7월, 반 고흐가 세상을 떠나기 직전 오베르쉬르우아즈에서 제작한 마지막 작품 중 하나입니다.",
        "art_movement": "후기 인상주의",
        "historical_context": "1890년 반 고흐는 생레미 요양원에서 퇴원해 파리 근교 오베르쉬르우아즈로 이사했습니다. 그는 정신과 의사 가셰 박사의 보살핌을 받으며 마지막 생애를 보냈습니다.",
        "artist_context": "반 고흐는 오베르에서 70일 동안 70여 점의 그림을 남길 만큼 왕성하게 활동했습니다. 이 작품은 광활한 밀밭과 검은 까마귀들이 보여주는 불안한 분위기로 그의 내면 상태를 반영한다는 해석이 많습니다.",
        "visual_connection": "폭풍 전야 같은 암울한 하늘, 세 갈래로 갈라지는 밀밭 길, 흩날리는 까마귀 떼는 불안과 종말에 대한 암시로 읽히며, 거친 임파스토 기법이 감정의 격렬함을 더합니다.",
    },
    "Self-Portrait with Bandaged Ear": {
        "creation_period": "1889년 1월, 반 고흐가 고갱과의 격렬한 다툼 끝에 스스로 귀를 자른 사건 이후 제작한 작품입니다.",
        "art_movement": "후기 인상주의",
        "historical_context": "1888년 12월 고갱과의 갈등이 극에 달한 반 고흐는 자신의 왼쪽 귀 일부를 잘라내는 사건을 일으켰습니다. 이 사건은 그의 정신적 위기와 예술적 열정의 비극적 충돌을 상징합니다.",
        "artist_context": "반 고흐는 이 사건 직후 고요하고 담담한 자화상을 두 점 그렸습니다. 붕대를 감고 파이프를 문 채 화면을 바라보는 그의 시선에는 내면의 상처와 평정심이 공존합니다.",
        "visual_connection": "흰 붕대와 털모자의 대비, 배경의 일본 판화와 화가용 캔버스는 그의 정체성을 압축적으로 표현합니다. 차분한 구성이지만 붓터치에는 여전한 긴장감이 담겨 있습니다.",
    },
    # ════════════════════════════════════════════════════════════════════
    # Claude Monet
    # ════════════════════════════════════════════════════════════════════
    "Woman with a Parasol": {
        "creation_period": "1875년, 클로드 모네가 아내 카미유와 아들 장을 모델로 제작한 인상주의 걸작입니다.",
        "art_movement": "인상주의",
        "historical_context": "19세기 후반 프랑스에서는 인상주의 화가들이 야외에서 자연 빛의 변화를 포착하는 '외광파(Plein Air)' 기법을 실험하고 있었습니다.",
        "artist_context": "모네는 빛과 바람, 움직임의 순간을 포착하는 데 탁월했습니다. 이 작품은 하늘 아래 파라솔을 든 여인과 아이의 순간적인 모습을 생동감 있게 담아냈습니다.",
        "visual_connection": "바람에 흔들리는 풀과 옷자락, 역광으로 빛나는 파라솔의 반투명함은 인상주의 특유의 빠른 붓터치로 표현되어 바람과 빛의 순간을 생생하게 전달합니다.",
    },
    "Haystacks": {
        "creation_period": "1890~1891년, 모네가 지베르니 인근 들판의 건초더미를 다양한 계절과 시간대에 그린 25점의 연작입니다.",
        "art_movement": "인상주의",
        "historical_context": "19세기 말 프랑스 농촌에서는 여전히 전통적인 농업 방식이 이어지고 있었습니다. 모네는 동일한 대상이 빛과 시간에 따라 얼마나 다르게 보이는지를 연구했습니다.",
        "artist_context": "건초더미 연작은 모네가 본격적으로 '연작 회화' 방식을 도입한 시리즈입니다. 그는 같은 장소에 여러 캔버스를 두고 빛이 바뀔 때마다 다른 캔버스로 옮겨 그리는 방식으로 제작했습니다.",
        "visual_connection": "여름 아침 황금빛에서 겨울 눈 속까지 각기 다른 색채로 표현된 건초더미들은 빛이 형태보다 중요하다는 인상주의의 핵심 철학을 직접 실증합니다.",
    },
    "The Japanese Footbridge": {
        "creation_period": "1899~1900년, 모네가 지베르니의 일본식 정원 다리를 주제로 제작한 연작입니다.",
        "art_movement": "인상주의",
        "historical_context": "19세기 말 유럽에는 일본 문화에 대한 관심이 높았으며, '자포니즘(Japonisme)'이 예술계에 큰 영향을 미쳤습니다. 모네도 일본 판화를 수집하며 일본식 정원을 직접 설계했습니다.",
        "artist_context": "모네는 지베르니에 수련 연못과 일본식 아치 다리를 조성했습니다. 이 정원은 그의 말년 작품들의 핵심 소재가 되었으며, 다리 연작은 수련 연작으로 이어지는 전환점이었습니다.",
        "visual_connection": "초록빛 아치 다리와 수면의 반영, 늘어진 수양버들이 어우러진 구성은 자연과 인공의 조화를 보여주며 일본 정원의 선(禪)적 미학과 인상주의의 빛 표현이 융합됩니다.",
    },
    # ════════════════════════════════════════════════════════════════════
    # Gustav Klimt
    # ════════════════════════════════════════════════════════════════════
    "Portrait of Adele Bloch-Bauer I": {
        "creation_period": "1907년, 클림트의 황금 시기를 대표하는 초상화로 '오스트리아의 모나리자'라고 불립니다.",
        "art_movement": "상징주의 / 아르누보 / 빈 분리파",
        "historical_context": "20세기 초 빈은 합스부르크 제국의 문화 수도로 유대인 상류층이 예술 후원의 중심에 있었습니다. 아델레 블로흐-바우어는 빈의 저명한 사교계 인사로 클림트의 주요 후원자였습니다.",
        "artist_context": "클림트는 이 작품을 완성하는 데 4년이 걸렸으며, 수백 장의 스케치를 남겼습니다. 황금빛 장식과 기하학적 문양으로 뒤덮인 이 초상화는 2006년 비공개 거래로 당시 최고가인 1억 3,500만 달러에 거래되었습니다.",
        "visual_connection": "금박으로 뒤덮인 의상과 배경에서 아델레의 얼굴과 손만이 자연스러운 피부색으로 표현되어, 인물이 황금빛 장식 속에서 부유하는 듯한 신비로운 효과를 만들어냅니다.",
    },
    "The Tree of Life": {
        "creation_period": "1909년, 클림트가 브뤼셀 스토클레 저택 식당을 위해 제작한 모자이크 벽화 디자인입니다.",
        "art_movement": "상징주의 / 아르누보 / 빈 분리파",
        "historical_context": "20세기 초 유럽의 아르누보 운동은 건축·인테리어·회화 등 모든 예술 분야에서 자연적 형태와 장식성을 강조했습니다. 클림트는 총체예술(Gesamtkunstwerk) 개념 아래 건축과 회화를 통합하려 했습니다.",
        "artist_context": "클림트는 나무를 생명·죽음·부활의 순환을 상징하는 모티프로 사용했습니다. 소용돌이치는 나뭇가지 아래 수많은 장식적 요소들은 이집트·비잔틴·일본 미술에서 가져온 이미지들입니다.",
        "visual_connection": "황금빛 소용돌이 가지와 화려한 장식 문양으로 가득 찬 생명나무는 우주적 생명력을 상징하며, 클림트 특유의 평면적 금박 기법이 작품 전체에 신화적 분위기를 부여합니다.",
    },
    # ════════════════════════════════════════════════════════════════════
    # Edvard Munch
    # ════════════════════════════════════════════════════════════════════
    "Madonna": {
        "creation_period": "1894~1895년, 뭉크가 성스러움과 관능성을 결합한 상징적 여성상을 그린 작품입니다.",
        "art_movement": "상징주의 / 표현주의",
        "historical_context": "19세기 말 유럽에서는 여성성에 대한 양가적 시선이 팽배했습니다. '팜므 파탈(femme fatale)'과 성녀(Madonna)라는 이분법적 여성 이미지가 예술과 문학에서 자주 다뤄졌습니다.",
        "artist_context": "뭉크는 사랑과 성(性)을 죽음과 연결 지어 보았습니다. 이 작품에서 눈을 감은 여인의 엑스터시적 표정과 주변의 정자·태아 형상은 사랑과 생명과 죽음의 순환을 상징합니다.",
        "visual_connection": "붉은 후광과 검은 배경, 관능적인 인체 표현은 성스러움과 육체성의 충돌을 강조합니다. 물결치는 머리카락과 굴곡진 선은 뭉크의 상징주의적 표현 언어를 잘 보여줍니다.",
    },
    # ════════════════════════════════════════════════════════════════════
    # Johannes Vermeer
    # ════════════════════════════════════════════════════════════════════
    "The Milkmaid": {
        "creation_period": "1657~1658년경, 요하네스 페르메이르가 델프트에서 제작한 장르화입니다.",
        "art_movement": "바로크 / 네덜란드 황금시대",
        "historical_context": "17세기 네덜란드 황금시대에는 해상 무역으로 번성한 시민 계층이 일상생활을 담은 장르화를 즐겨 수집했습니다. 가정 내 하인과 노동자를 주제로 한 그림이 인기를 끌었습니다.",
        "artist_context": "페르메이르는 빛이 실내로 스며드는 방식을 정밀하게 관찰하고 표현하는 데 뛰어났습니다. 빛이 우유를 따르는 여인의 모습을 조용히 비추는 장면은 일상의 노동을 숭고한 순간으로 격상시킵니다.",
        "visual_connection": "창문 왼쪽에서 들어오는 자연광이 인물과 빵, 우유 항아리를 섬세하게 조명합니다. 두꺼운 빛의 질감과 차분한 색채는 페르메이르 특유의 정밀한 관찰력을 드러냅니다.",
    },
    "Woman Reading a Letter": {
        "creation_period": "1663년경, 페르메이르가 편지를 읽는 여인의 사적인 순간을 포착한 작품입니다.",
        "art_movement": "바로크 / 네덜란드 황금시대",
        "historical_context": "17세기 네덜란드에서는 해상 무역이 활발해 가족과 멀리 떨어진 선원·상인들의 편지가 가정에서 중요한 의미를 가졌습니다. 편지를 읽는 행위는 회화에서 서사와 감정을 담는 장치로 자주 활용되었습니다.",
        "artist_context": "페르메이르는 인물을 관찰자처럼 바라보며, 그 사적인 순간에 침묵과 집중의 분위기를 담아내는 데 탁월했습니다. 임신한 듯한 여인이 어떤 소식을 읽는지는 관람자의 상상에 맡겨집니다.",
        "visual_connection": "창문을 통해 들어오는 빛이 여인의 얼굴과 흰 벽에 부드럽게 반사되며, 파란 드레스와 황토색 테이블이 따뜻한 색 대비를 이룹니다. 고요한 구성이 깊은 사색의 분위기를 자아냅니다.",
    },
    # ════════════════════════════════════════════════════════════════════
    # Leonardo da Vinci
    # ════════════════════════════════════════════════════════════════════
    "Lady with an Ermine": {
        "creation_period": "1489~1490년경, 레오나르도 다 빈치가 밀라노에서 루도비코 스포르차의 정부 체칠리아 갈레라니를 그린 초상화입니다.",
        "art_movement": "르네상스",
        "historical_context": "15세기 말 밀라노는 스포르차 가문의 통치 하에 있었습니다. 다 빈치는 1482년부터 밀라노 궁정 화가로 활동했으며, 이 초상화는 궁정의 화려한 문화적 풍토를 반영합니다.",
        "artist_context": "다 빈치는 인물의 심리적 상태를 몸짓과 표정으로 표현하는 데 탁월했습니다. 그림 속 족제비(ermine)는 순결과 고귀함의 상징으로, 모델의 이름 갈레라니가 그리스어로 족제비를 뜻한다는 설도 있습니다.",
        "visual_connection": "3/4 측면 구도와 손으로 족제비를 안은 자연스러운 자세는 당시 경직된 초상화 관습에서 벗어난 혁신적인 구성입니다. 스푸마토 기법의 부드러운 명암이 생동감 있는 인물 표현을 완성합니다.",
    },
    # ════════════════════════════════════════════════════════════════════
    # Sandro Botticelli
    # ════════════════════════════════════════════════════════════════════
    "Primavera": {
        "creation_period": "1477~1482년경, 산드로 보티첼리가 메디치 가문을 위해 제작한 알레고리 회화입니다.",
        "art_movement": "초기 르네상스",
        "historical_context": "15세기 피렌체는 로렌초 데 메디치의 통치 하에 인문주의와 신플라톤주의가 꽃피웠습니다. 고대 그리스·로마 신화와 철학을 재해석하는 것이 지식인 사이에서 유행했습니다.",
        "artist_context": "보티첼리는 메디치 가문의 총애를 받으며 철학자 피치노의 신플라톤주의 사상에 영향을 받았습니다. 이 작품은 '봄'이라는 제목처럼 생명·사랑·풍요를 신화적 우의로 표현합니다.",
        "visual_connection": "우아하게 흐르는 인물들의 자세와 정교하게 묘사된 꽃과 나무들은 선과 장식성을 강조하는 보티첼리의 고유 화풍을 보여줍니다. 황금빛 오렌지 숲이 신화적 분위기를 고조시킵니다.",
    },
    # ════════════════════════════════════════════════════════════════════
    # Raphael
    # ════════════════════════════════════════════════════════════════════
    "The School of Athens": {
        "creation_period": "1509~1511년, 라파엘로가 바티칸 교황 집무실(스탄체) 벽에 프레스코로 제작했습니다.",
        "art_movement": "전성기 르네상스",
        "historical_context": "16세기 초 교황 율리우스 2세는 바티칸을 예술과 학문의 중심지로 만들기 위해 미켈란젤로·라파엘로 등 최고의 예술가들을 고용했습니다. 이 시기는 이탈리아 르네상스의 절정이었습니다.",
        "artist_context": "라파엘로는 고대 그리스 철학자들을 한 자리에 모아 인류 지성의 이상을 표현했습니다. 가운데 플라톤(다 빈치의 얼굴)과 아리스토텔레스가 논쟁하는 구도가 핵심입니다.",
        "visual_connection": "완벽한 원근법과 웅장한 건축 배경, 각 철학자의 개성 있는 포즈와 표정은 르네상스의 이상인 인간 이성의 위대함을 시각적으로 구현합니다.",
    },
    # ════════════════════════════════════════════════════════════════════
    # Michelangelo
    # ════════════════════════════════════════════════════════════════════
    "The Creation of Adam": {
        "creation_period": "1508~1512년, 미켈란젤로가 바티칸 시스티나 성당 천장화의 일부로 제작한 프레스코입니다.",
        "art_movement": "전성기 르네상스",
        "historical_context": "16세기 초 교황 율리우스 2세의 의뢰로 미켈란젤로는 시스티나 성당 천장화를 완성했습니다. 4년에 걸친 이 작업은 인류 미술사의 가장 위대한 업적 중 하나로 꼽힙니다.",
        "artist_context": "미켈란젤로는 조각가로 더 유명했지만 이 천장화로 회화에서도 정점을 이뤘습니다. 그는 신의 손과 인간의 손이 맞닿으려는 순간을 통해 신성과 인간성의 만남을 표현했습니다.",
        "visual_connection": "근육질의 이상적인 인체와 신의 손과 아담의 손 사이의 아직 닿지 않은 간격이 이 작품의 핵심입니다. 인체를 통한 신성의 표현은 르네상스 인문주의 사상을 완벽하게 시각화합니다.",
    },
    # ════════════════════════════════════════════════════════════════════
    # Rembrandt
    # ════════════════════════════════════════════════════════════════════
    "The Night Watch": {
        "creation_period": "1642년, 렘브란트가 암스테르담 시민 경비대의 의뢰로 제작한 대형 집단 초상화입니다.",
        "art_movement": "바로크 / 네덜란드 황금시대",
        "historical_context": "17세기 네덜란드 황금시대에는 번성한 상인 계층이 집단 초상화를 즐겨 의뢰했습니다. 시민 경비대는 암스테르담 도시 방어의 핵심 조직이었으며, 구성원들은 초상화를 통해 사회적 지위를 과시했습니다.",
        "artist_context": "렘브란트는 정적인 집단 초상화 전통을 깨고 역동적인 순간을 포착했습니다. 강렬한 빛과 어둠의 대비(키아로스쿠로)로 구성원들이 행진을 시작하는 순간의 생동감을 표현했습니다.",
        "visual_connection": "어두운 배경에서 밝게 조명된 인물들의 대비, 역동적인 구성과 움직임의 표현은 렘브란트의 빛 처리 기법인 '렘브란트 조명'의 정수를 보여줍니다.",
    },
    "The Anatomy Lesson of Dr. Nicolaes Tulp": {
        "creation_period": "1632년, 렘브란트가 26세에 암스테르담에서 제작한 첫 번째 대형 집단 초상화입니다.",
        "art_movement": "바로크 / 네덜란드 황금시대",
        "historical_context": "17세기 네덜란드에서는 과학혁명의 영향으로 인체 해부학에 대한 관심이 높았습니다. 의사들은 공개 해부를 통해 의학 지식을 공유했으며, 이러한 행사는 교육적·사회적 이벤트로 여겨졌습니다.",
        "artist_context": "렘브란트는 이 작품으로 암스테르담에서 화가로서의 명성을 확립했습니다. 당시 26세의 젊은 나이에 복잡한 집단 구성을 능숙하게 처리하며 탁월한 재능을 드러냈습니다.",
        "visual_connection": "해부 장면 주변에 집중된 인물들의 시선과 렘브란트 특유의 강렬한 명암 대비가 의학적 순간의 극적 긴장감을 효과적으로 전달합니다.",
    },
    # ════════════════════════════════════════════════════════════════════
    # Caravaggio
    # ════════════════════════════════════════════════════════════════════
    "Judith Beheading Holofernes": {
        "creation_period": "1598~1599년경, 카라바조가 구약성경 유디트서의 장면을 극적으로 묘사한 작품입니다.",
        "art_movement": "바로크",
        "historical_context": "16세기 말 이탈리아 가톨릭 교회는 종교개혁에 대응하는 반종교개혁 운동을 펼쳤습니다. 극적이고 감동적인 종교 미술이 장려되었으며, 카라바조의 사실적이고 극적인 화풍은 이 시대적 요구에 부응했습니다.",
        "artist_context": "카라바조는 미화 없이 인물을 사실적으로 묘사하고 강렬한 빛과 어둠의 대비를 사용하는 혁신적인 화풍으로 당시 예술계에 큰 충격을 주었습니다.",
        "visual_connection": "강렬한 키아로스쿠로 기법으로 어두운 배경에서 유디트의 하얀 피부와 피 흘리는 홀로페르네스가 강렬하게 부각됩니다. 유디트의 냉정한 표정과 잘린 목의 생생한 묘사가 극적 긴장감을 극대화합니다.",
    },
    "The Calling of Saint Matthew": {
        "creation_period": "1599~1600년, 카라바조가 로마 산 루이지 데이 프란체시 성당을 위해 제작한 제단화입니다.",
        "art_movement": "바로크",
        "historical_context": "17세기 초 로마는 반종교개혁의 중심지로 웅장한 성당과 종교 미술이 활발히 제작되었습니다. 카라바조는 신화적 장면이 아닌 성경을 일상적 현실처럼 표현하는 새로운 접근법을 보여줬습니다.",
        "artist_context": "카라바조는 세리(세금 징수원) 마태오를 부르는 장면을 당시 로마의 선술집처럼 그렸습니다. 예수의 부름을 받는 순간 마태오가 자신을 가리키는 손짓의 모호함이 작품의 핵심입니다.",
        "visual_connection": "어두운 실내로 스며드는 한 줄기 빛이 인물들을 드라마틱하게 조명합니다. 일상적 공간에서의 신성한 사건이라는 카라바조 특유의 접근이 종교화에 새로운 현실감을 부여합니다.",
    },
    # ════════════════════════════════════════════════════════════════════
    # Diego Velázquez
    # ════════════════════════════════════════════════════════════════════
    "Las Meninas": {
        "creation_period": "1656년, 디에고 벨라스케스가 스페인 마드리드 왕실에서 제작한 대형 궁정화입니다.",
        "art_movement": "바로크",
        "historical_context": "17세기 스페인은 합스부르크 왕가의 통치 하에 있었으며, 벨라스케스는 필리페 4세의 궁정 화가로 활동했습니다. 스페인 왕실은 당시 유럽 최강국으로 화려한 궁정 문화를 자랑했습니다.",
        "artist_context": "벨라스케스는 이 작품에서 왕녀 마르가리타와 시녀들, 난쟁이, 그리고 자신을 함께 그려 왕실 일상을 묘사했습니다. 배경 거울에 비친 왕과 왕비의 모습은 작품의 시점 문제를 복잡하게 만드는 수수께끼입니다.",
        "visual_connection": "화가 자신을 포함한 복잡한 구성, 거울 속 반영, 빛의 섬세한 처리는 당시로선 혁신적인 메타회화적 기법을 보여줍니다. 벨라스케스의 자유로운 붓터치는 인상주의를 200년 앞선 것으로 평가됩니다.",
    },
    # ════════════════════════════════════════════════════════════════════
    # Francisco Goya
    # ════════════════════════════════════════════════════════════════════
    "Saturn Devouring His Son": {
        "creation_period": "1820~1823년, 고야가 귀머거리의 집(Quinta del Sordo) 식당 벽에 직접 그린 '검은 그림' 연작 중 하나입니다.",
        "art_movement": "낭만주의 / 표현주의 전조",
        "historical_context": "19세기 초 스페인은 나폴레옹 침략과 이후의 정치적 혼란으로 극심한 고통을 겪었습니다. 고야는 이 시기에 청력을 잃고, 전쟁의 공포와 인간의 폭력성에 대한 환멸을 강렬한 그림으로 표현했습니다.",
        "artist_context": "고야는 이 벽화들을 공개 전시용이 아닌 자신만을 위해 그렸습니다. 로마 신화에서 권력에 집착한 사투르누스가 자식을 잡아먹는 장면은 고야의 인간 본성에 대한 비관적 시선을 집약합니다.",
        "visual_connection": "어두운 배경과 거친 붓터치, 공포에 사로잡힌 사투르누스의 크게 뜬 눈은 극단적인 감정적 강도를 전달합니다. 표현주의와 현대 미술을 예고하는 원초적 에너지가 느껴집니다.",
    },
    "The Third of May 1808": {
        "creation_period": "1814년, 고야가 나폴레옹 군대의 스페인 점령에 저항한 민중을 기리기 위해 제작했습니다.",
        "art_movement": "낭만주의",
        "historical_context": "1808년 5월 2~3일 마드리드에서 스페인 시민들이 나폴레옹 군대에 맞서 봉기했다가 무자비하게 진압되었습니다. 이 사건은 이베리아 반도 전쟁의 시작을 알리는 역사적 전환점이었습니다.",
        "artist_context": "고야는 스페인을 점령했던 나폴레옹 군대가 물러난 후, 반도전쟁의 참상을 기록하기 위해 이 작품을 그렸습니다. 민간인 학살을 고발하는 이 그림은 이후 전쟁 반대 미술의 원형이 되었습니다.",
        "visual_connection": "처형 직전 두 팔을 벌린 흰 셔츠 남자와 총구를 겨누는 익명의 군인들의 대비는 희생자의 인간성과 학살자의 비인간성을 극명하게 대조시킵니다.",
    },
    # ════════════════════════════════════════════════════════════════════
    # Eugène Delacroix
    # ════════════════════════════════════════════════════════════════════
    "Liberty Leading the People": {
        "creation_period": "1830년, 들라크루아가 프랑스 7월 혁명을 주제로 제작한 역사화입니다.",
        "art_movement": "낭만주의",
        "historical_context": "1830년 프랑스에서는 샤를 10세의 전제 정치에 맞선 7월 혁명이 일어났습니다. 시민들이 3일간의 봉기 끝에 왕정을 무너뜨린 이 사건은 자유·평등·박애의 혁명 이념을 재확인했습니다.",
        "artist_context": "들라크루아 자신은 혁명에 직접 참가하지 않았지만, 혁명 직후 이 작품을 그려 자유의 이념을 알레고리로 표현했습니다. 자유의 여신 마리안느는 이후 프랑스 공화국의 상징이 되었습니다.",
        "visual_connection": "삼색기를 든 반나체의 자유의 여신과 그 주변에 모인 다양한 계층의 인물들, 역동적인 구성과 강렬한 색채는 낭만주의의 감정적 에너지와 역사적 메시지를 완벽히 결합합니다.",
    },
    # ════════════════════════════════════════════════════════════════════
    # Pierre-Auguste Renoir
    # ════════════════════════════════════════════════════════════════════
    "Dance at Le Moulin de la Galette": {
        "creation_period": "1876년, 르누아르가 파리 몽마르트르의 야외 무도회장을 그린 인상주의 걸작입니다.",
        "art_movement": "인상주의",
        "historical_context": "19세기 후반 파리는 벨 에포크의 시작으로 번성하는 도시 문화를 꽃피웠습니다. 노동자·시민 계층이 주말에 야외 무도회를 즐기는 문화가 성행했으며, 르누아르는 이러한 시민의 삶을 즐겨 그렸습니다.",
        "artist_context": "르누아르는 몽마르트르의 다양한 사람들을 모델로 삼아 이 대형 작품을 제작했습니다. 그는 오전부터 저녁까지 현장에 나가 빛의 변화를 직접 관찰하며 작업했습니다.",
        "visual_connection": "나뭇잎 사이로 내리쬐는 얼룩진 햇빛이 군중 위에 흩뿌려지는 표현, 밝고 생동감 있는 색채와 분위기 있는 구성은 인상주의 특유의 빛과 움직임 표현의 정점을 보여줍니다.",
    },
    "Luncheon of the Boating Party": {
        "creation_period": "1880~1881년, 르누아르가 파리 근교 샤투의 레스토랑 야외 테라스에서 친구들과의 점심을 그린 작품입니다.",
        "art_movement": "인상주의",
        "historical_context": "19세기 말 파리 시민들은 철도의 발달로 교외 레저 활동을 즐길 수 있게 되었습니다. 센 강변의 보트 놀이와 야외 식사는 부르주아 계층의 전형적인 여가 활동이 되었습니다.",
        "artist_context": "르누아르는 자신의 친구들을 모델로 이 작품을 제작했습니다. 나중에 그의 아내가 되는 알린 샤리고(강아지를 안은 여인)도 등장합니다. 이 작품은 르누아르의 가장 야심찬 구성 중 하나입니다.",
        "visual_connection": "빛과 그늘의 변화 속에서 포도주·과일·인물이 어우러진 풍성한 구성은 19세기 말 파리 시민의 삶의 풍요로움과 즐거움을 생생하게 포착합니다.",
    },
    # ════════════════════════════════════════════════════════════════════
    # Edgar Degas
    # ════════════════════════════════════════════════════════════════════
    "The Dance Class": {
        "creation_period": "1874년, 에드가 드가가 파리 오페라 발레단의 연습 장면을 그린 작품입니다.",
        "art_movement": "인상주의",
        "historical_context": "19세기 후반 파리 오페라는 유럽 최고 수준의 발레 공연을 선보였습니다. 발레리나들은 대부분 하층 계급 출신으로 엄격한 훈련을 받았으며, 드가는 이들의 일상을 사실적으로 기록했습니다.",
        "artist_context": "드가는 발레 연습 장면을 약 1,500점에 달하는 다양한 작품으로 남겼습니다. 그는 발레의 화려한 무대 이면에 있는 고된 훈련과 일상의 모습을 즐겨 포착했습니다.",
        "visual_connection": "비대칭적이고 스냅 사진처럼 보이는 구성, 연습 중 다양한 포즈의 무용수들은 일본 우키요에와 사진의 영향을 받은 드가의 현대적 시각을 보여줍니다.",
    },
    "L'Absinthe": {
        "creation_period": "1876년, 에드가 드가가 파리 카페의 쓸쓸한 두 인물을 그린 작품입니다.",
        "art_movement": "인상주의 / 사실주의",
        "historical_context": "19세기 후반 파리에서 압생트는 보헤미안 예술가와 노동 계층 사이에서 인기 있는 값싼 술이었습니다. 과음으로 인한 사회적 문제가 대두되었으며, 이후 1914년 프랑스에서 금지되었습니다.",
        "artist_context": "드가는 여배우 엘렌 앙드레와 화가 마르슬랭 데부탱을 모델로 삼아 이 작품을 제작했습니다. 도시 소외와 고독을 주제로 한 이 작품은 당시 파리 서민 생활의 어두운 면을 솔직하게 드러냅니다.",
        "visual_connection": "대각선으로 기울어진 테이블, 멍하니 앉은 두 인물의 시선이 서로 엇갈린 구성은 도시의 고독과 소외를 강렬하게 표현합니다. 비대칭적인 구도는 당시 사진의 영향을 보여줍니다.",
    },
    # ════════════════════════════════════════════════════════════════════
    # Édouard Manet
    # ════════════════════════════════════════════════════════════════════
    "Olympia": {
        "creation_period": "1863년 제작, 1865년 살롱전 출품. 마네가 티치아노의 '우르비노의 비너스'를 현대적으로 재해석한 작품입니다.",
        "art_movement": "사실주의 / 인상주의 전조",
        "historical_context": "19세기 중반 파리 살롱전에서 나체 여성 그림은 신화나 역사 주제일 때만 허용되었습니다. 마네는 이 금기를 깨고 실존하는 파리 매춘부를 직접적으로 묘사해 큰 논란을 일으켰습니다.",
        "artist_context": "마네는 이 작품에서 모델의 시선을 관람자에게 직접 향하게 함으로써 전통적인 수동적 나체화 관습을 전복시켰습니다. 이 도전적인 자세와 시선은 당시 미술계에 충격을 주었습니다.",
        "visual_connection": "평면적인 색채 처리와 대담한 윤곽선, 모델의 직접적인 시선은 전통 회화의 환상성을 파괴하고 현실을 직시하게 만드는 마네의 혁신적 기법을 보여줍니다.",
    },
    "Le Déjeuner sur l'herbe": {
        "creation_period": "1862~1863년, 마네가 파리 근교 숲에서 벌어지는 충격적인 소풍 장면을 그린 작품입니다.",
        "art_movement": "사실주의 / 인상주의 전조",
        "historical_context": "1863년 파리 살롱전에서 낙선한 작품들이 나폴레옹 3세의 결정으로 '낙선전(Salon des Refusés)'에 전시되었습니다. 이 전시는 이후 인상주의의 탄생을 이끄는 역사적 계기가 되었습니다.",
        "artist_context": "마네는 르네상스 거장 라파엘로의 '파리스의 심판'에서 구도를 빌려왔지만, 신화적 맥락을 배제하고 현대 파리 시민을 등장시켜 당시 관람자들에게 큰 충격을 주었습니다.",
        "visual_connection": "옷을 입은 두 남성과 나체 여성의 병치, 밝은 빛 아래 평면적으로 처리된 인물들은 전통적인 원근법과 회화적 관습을 의도적으로 해체하는 마네의 도전적인 시각을 보여줍니다.",
    },
    # ════════════════════════════════════════════════════════════════════
    # Georges Seurat
    # ════════════════════════════════════════════════════════════════════
    "A Sunday on La Grande Jatte": {
        "creation_period": "1884~1886년, 조르주 쇠라가 파리 그랑드 자트 섬의 주말 나들이 장면을 점묘법으로 그린 작품입니다.",
        "art_movement": "신인상주의 / 점묘주의",
        "historical_context": "19세기 후반 파리 시민들은 철도 덕분에 도심 근교에서 여가를 즐길 수 있게 되었습니다. 쇠라는 당시 발전하던 광학·색채 이론을 적용해 과학적 인상주의를 시도했습니다.",
        "artist_context": "쇠라는 이 작품을 완성하는 데 2년이 걸렸으며, 현장에서 수십 장의 습작을 그린 후 아틀리에에서 점묘법(pointillism)으로 마무리했습니다. 이 기법은 '분할주의'라고도 불립니다.",
        "visual_connection": "무수히 많은 순수 색채의 점들이 관람자의 눈 속에서 혼합되어 빛을 표현하는 점묘법은 인상주의의 빛 포착을 과학적으로 체계화한 것입니다. 기하학적 구성이 독특한 정적인 분위기를 만들어냅니다.",
    },
    # ════════════════════════════════════════════════════════════════════
    # Paul Cézanne
    # ════════════════════════════════════════════════════════════════════
    "The Card Players": {
        "creation_period": "1890~1895년, 폴 세잔이 프로방스 농민들의 카드 게임 장면을 그린 연작(5점)입니다.",
        "art_movement": "후기 인상주의",
        "historical_context": "19세기 말 남프랑스 프로방스에서는 전통적인 농촌 생활이 이어졌습니다. 세잔은 인상주의의 즉흥성에서 벗어나 형태의 구조적 견고함을 회복하려 했습니다.",
        "artist_context": "세잔은 이 작품에서 인물들의 집중된 표정과 견고한 형체를 통해 '자연을 원통·구·원뿔로 다룬다'는 자신의 예술 철학을 실천했습니다. 이 접근법은 이후 큐비즘에 직접적인 영향을 미쳤습니다.",
        "visual_connection": "단순화된 형태, 무거운 윤곽선, 기하학적 구성은 세잔이 인상주의의 빛과 분위기 대신 견고한 구조와 공간감을 추구했음을 보여줍니다.",
    },
    "Mont Sainte-Victoire": {
        "creation_period": "1885~1906년, 세잔이 고향 프로방스의 생트-빅투아르 산을 주제로 그린 60여 점의 연작입니다.",
        "art_movement": "후기 인상주의",
        "historical_context": "19세기 말 세잔은 파리의 인상주의 화가들과 거리를 두고 고향 엑상프로방스에 은거하며 자신만의 화풍을 완성해 나갔습니다.",
        "artist_context": "세잔은 같은 산을 수십 번 반복해 그리며 자연의 본질적인 구조를 포착하려 했습니다. 각도·계절·거리를 달리하며 공간과 형태, 색채의 관계를 깊이 탐구했습니다.",
        "visual_connection": "산의 굳건한 형태와 전경의 나무·들판이 만들어내는 수평적 구조, 넓은 색면의 단순한 붓터치는 세잔 특유의 '감각의 실현'을 향한 끊임없는 탐구를 보여줍니다.",
    },
    # ════════════════════════════════════════════════════════════════════
    # Paul Gauguin
    # ════════════════════════════════════════════════════════════════════
    "Where Do We Come From? What Are We? Where Are We Going?": {
        "creation_period": "1897~1898년, 폴 고갱이 타히티에서 자살을 결심하기 전 최후의 걸작으로 제작한 대형 작품입니다.",
        "art_movement": "후기 인상주의 / 상징주의",
        "historical_context": "19세기 말 유럽의 식민지 확장으로 태평양 섬들이 '미개'한 낙원으로 낭만화되었습니다. 고갱은 이 원시적 낙원에서 서구 문명의 타락을 피하고 진정한 예술을 추구하려 했습니다.",
        "artist_context": "고갱은 빚과 질병, 딸의 죽음으로 절망해 자살을 결심하고 이 작품을 제작했습니다. 인간의 탄생에서 죽음까지의 여정을 파노라마처럼 펼친 이 대형 작품은 그의 철학적 유언장이었습니다.",
        "visual_connection": "생생한 열대의 색채와 원시적 형태, 상징적인 인물 배치는 서구 문명과 원시 자연에 대한 고갱의 이원론적 사유를 시각화합니다.",
    },
    # ════════════════════════════════════════════════════════════════════
    # Caspar David Friedrich
    # ════════════════════════════════════════════════════════════════════
    "Wanderer above the Sea of Fog": {
        "creation_period": "1818년경, 카스파르 다비드 프리드리히가 낭만주의 정신을 집약한 대표작입니다.",
        "art_movement": "낭만주의",
        "historical_context": "19세기 초 유럽에서는 계몽주의에 대한 반발로 자연의 숭고함과 인간의 감정을 중시하는 낭만주의가 부상했습니다. 독일에서는 자연철학(Naturphilosophie)이 예술에 깊은 영향을 미쳤습니다.",
        "artist_context": "프리드리히는 광대한 자연 앞에 서 있는 '뒷모습의 인물(Rückenfigur)'을 즐겨 사용했습니다. 이 기법은 관람자가 인물에 자신을 동일시하며 무한한 자연과 마주하는 경험을 유도합니다.",
        "visual_connection": "안개 속 산봉우리를 내려다보는 검은 코트의 인물은 자연의 숭고함 앞에 선 인간의 고독과 탐구 정신을 상징합니다. 극적인 명암과 원경의 깊이감이 낭만주의적 경외감을 불러일으킵니다.",
    },
    # ════════════════════════════════════════════════════════════════════
    # J.M.W. Turner
    # ════════════════════════════════════════════════════════════════════
    "The Fighting Temeraire": {
        "creation_period": "1839년, 조지프 말로드 윌리엄 터너가 증기선에 끌려가는 낡은 전함 테메레르 호를 그린 작품입니다.",
        "art_movement": "낭만주의",
        "historical_context": "19세기 중반 영국은 산업혁명의 한복판에 있었습니다. 증기선이 범선을 대체하는 시대적 전환은 영국 해군의 황금기 종말을 상징했습니다. 테메레르 호는 트라팔가르 해전(1805) 영국 승리의 공신이었습니다.",
        "artist_context": "터너는 이 작품에서 석양 빛 속에 사라져가는 옛 시대의 영광을 시적으로 포착했습니다. 작품은 영국 국민에게 큰 감동을 주어 '영국인이 가장 사랑하는 그림'으로 여러 차례 선정되었습니다.",
        "visual_connection": "황금빛과 주황빛으로 타오르는 석양과 그 속에 유령처럼 희게 빛나는 전함, 검은 연기를 내뿜는 증기 예인선의 대비는 낡은 시대와 새 시대의 교체를 시적으로 담아냅니다.",
    },
    # ════════════════════════════════════════════════════════════════════
    # Salvador Dalí
    # ════════════════════════════════════════════════════════════════════
    "The Persistence of Memory": {
        "creation_period": "1931년, 살바도르 달리가 카탈루냐 포르트 리가트 해변을 배경으로 제작한 초현실주의 걸작입니다.",
        "art_movement": "초현실주의",
        "historical_context": "1920~30년대 유럽에서는 제1차 세계대전 이후의 허무와 프로이트의 정신분석학에 영향을 받아 꿈과 무의식을 예술로 표현하는 초현실주의가 등장했습니다.",
        "artist_context": "달리는 '편집증적 비판 방법'을 사용해 반의식 상태에서 보이는 이미지를 극사실적 기법으로 표현했습니다. 녹아내리는 시계들은 아인슈타인의 상대성 이론에 대한 달리의 응답이라는 해석도 있습니다.",
        "visual_connection": "포르트 리가트 해변의 사실적 풍경에 녹아 처진 시계들이 놓인 초현실적 장면은 극사실주의 기법으로 표현되어, 꿈의 논리를 현실처럼 믿게 만드는 초현실주의 핵심 전략을 구현합니다.",
    },
    # ════════════════════════════════════════════════════════════════════
    # René Magritte
    # ════════════════════════════════════════════════════════════════════
    "The Son of Man": {
        "creation_period": "1964년, 르네 마그리트가 자화상으로 제작한 초현실주의 회화입니다.",
        "art_movement": "초현실주의",
        "historical_context": "20세기 중반 초현실주의는 제2차 세계대전을 거치며 존재와 정체성, 실재와 허구의 경계에 대한 철학적 탐구를 계속했습니다.",
        "artist_context": "마그리트는 이 자화상에서 사과로 얼굴을 가려 정체성의 불가해성을 표현했습니다. 그는 '보이는 것이 다른 무언가를 숨긴다'는 신비를 회화 언어로 탐구했습니다.",
        "visual_connection": "정장을 입은 신사의 얼굴을 가리는 초록 사과, 낮과 밤이 뒤섞인 배경은 일상적 대상들의 낯선 병치를 통해 시각적 인식과 현실의 본질에 의문을 제기합니다.",
    },
    "The Treachery of Images": {
        "creation_period": "1929년, 마그리트가 이미지와 언어의 관계를 탐구한 개념적 작품입니다.",
        "art_movement": "초현실주의",
        "historical_context": "1920년대 초현실주의는 단순한 시각적 충격을 넘어 언어와 이미지, 현실과 재현의 관계에 대한 철학적 질문을 던지기 시작했습니다.",
        "artist_context": "마그리트는 파이프 그림 아래에 '이것은 파이프가 아니다'라는 글귀를 써서 이미지(재현)와 사물(실재) 사이의 근본적 차이를 지적했습니다. 이 작품은 이후 기호학과 미디어 이론에 큰 영향을 미쳤습니다.",
        "visual_connection": "극사실적으로 그려진 파이프와 그것을 부정하는 텍스트의 모순이 핵심입니다. 이미지가 곧 사물이라는 시각적 환상을 언어로 해체하는 이 전략은 마그리트 예술의 중심 방법론입니다.",
    },
    # ════════════════════════════════════════════════════════════════════
    # Pablo Picasso
    # ════════════════════════════════════════════════════════════════════
    "Les Demoiselles d'Avignon": {
        "creation_period": "1907년, 파블로 피카소가 바르셀로나의 홍등가를 모티프로 제작한 큐비즘의 시작을 알린 작품입니다.",
        "art_movement": "큐비즘 전조 / 원시주의",
        "historical_context": "20세기 초 유럽 식민지 확장과 세계 박람회를 통해 아프리카·오세아니아 미술이 유럽에 소개되었습니다. 이른바 '원시 미술'은 피카소·마티스 등 전위 예술가들에게 큰 충격과 영감을 주었습니다.",
        "artist_context": "피카소는 이 작품을 약 1년간의 준비 끝에 완성했습니다. 세잔의 기하학적 접근법과 아프리카 마스크에서 영감을 받아, 여러 시점을 동시에 표현하는 혁신적인 양식을 실험했습니다.",
        "visual_connection": "다시점으로 표현된 평면적 인체, 아프리카 마스크를 연상시키는 오른쪽 인물들의 얼굴은 전통적인 원근법과 인체 묘사 방식을 철저히 해체해 큐비즘 탄생의 직접적 계기가 되었습니다.",
    },
    # ════════════════════════════════════════════════════════════════════
    # Henri Matisse
    # ════════════════════════════════════════════════════════════════════
    "The Dance": {
        "creation_period": "1909~1910년, 앙리 마티스가 러시아 미술 수집가 세르게이 슈킨의 의뢰로 제작한 대형 벽화입니다.",
        "art_movement": "야수주의 / 모더니즘",
        "historical_context": "20세기 초 파리는 전위 예술의 중심지였습니다. 마티스는 색채를 감정 표현의 도구로 사용하는 야수주의를 이끌었으며, 이 작품은 그의 원시적 에너지와 리듬 표현의 정점입니다.",
        "artist_context": "마티스는 이 작품에서 춤추는 다섯 인물의 원형 구성을 통해 생명력과 집단적 리듬감을 표현했습니다. 단순화된 형태와 강렬한 원색 사용이 마티스 미학의 핵심을 보여줍니다.",
        "visual_connection": "녹색 언덕과 파란 하늘을 배경으로 붉은 인체가 원을 그리며 춤추는 구성은 단 세 가지 색으로 생명의 원초적 기쁨을 강렬하게 전달합니다.",
    },
    # ════════════════════════════════════════════════════════════════════
    # Andy Warhol
    # ════════════════════════════════════════════════════════════════════
    "Marilyn Diptych": {
        "creation_period": "1962년, 앤디 워홀이 마릴린 먼로 사망 직후 그녀의 홍보 사진을 실크스크린으로 반복해 제작한 작품입니다.",
        "art_movement": "팝 아트",
        "historical_context": "1960년대 미국에서는 대중 매체·광고·소비 문화가 폭발적으로 성장했습니다. 팝 아트는 이러한 대중 이미지들을 고급 예술의 영역으로 가져오며 '예술이란 무엇인가'에 의문을 제기했습니다.",
        "artist_context": "워홀은 마릴린 먼로가 사망한 직후 이 작품을 제작해 유명 인사의 아이콘화와 죽음, 대중 매체의 관계를 탐구했습니다. 50번 반복되는 이미지 중 왼쪽은 화려한 색채, 오른쪽은 흑백으로 삶과 죽음을 대비시킵니다.",
        "visual_connection": "실크스크린의 기계적 반복과 선명한 원색의 인공적 색채는 대중 매체가 유명 인사를 상품화·아이콘화하는 과정을 직접적으로 시각화합니다.",
    },
    "Campbell's Soup Cans": {
        "creation_period": "1962년, 앤디 워홀이 캠벨 수프의 32가지 종류를 각각 하나씩 묘사한 32점 연작입니다.",
        "art_movement": "팝 아트",
        "historical_context": "1960년대 미국 소비 사회에서 대량 생산 상품은 일상을 지배했습니다. 워홀은 슈퍼마켓 상품을 예술 작품으로 격상시킴으로써 예술과 상업, 고급 문화와 대중 문화의 경계를 해체했습니다.",
        "artist_context": "32점은 토마토·페퍼팟·크림 오브 셀러리 등 당시 캠벨이 판매하던 수프 맛 전 종류를 하나씩 담은 것입니다. 워홀은 어릴 때부터 매일 캠벨 수프를 먹었다고 밝혔으며, 평범한 일상품을 반복해 그림으로써 무엇이 예술이고 무엇이 아닌지에 대한 근본적인 질문을 던졌습니다.",
        "visual_connection": "슈퍼마켓 진열대처럼 나란히 배치된 32개의 동일한 수프 캔들은 대량 생산과 균일화된 소비 문화를 그대로 전시함으로써 예술적 독창성의 개념 자체를 도전합니다.",
    },
    # ════════════════════════════════════════════════════════════════════
    # Frida Kahlo
    # ════════════════════════════════════════════════════════════════════
    "The Two Fridas": {
        "creation_period": "1939년, 프리다 칼로가 디에고 리베라와 이혼하던 시기에 제작한 대형 자화상입니다.",
        "art_movement": "초현실주의 / 민속 미술",
        "historical_context": "20세기 초 멕시코는 독립 후 민족 정체성을 재건하는 과정에서 전통 민속 예술이 재평가되었습니다. 프리다는 멕시코 원주민 복식과 유럽적 정체성 사이에서 자신의 혼혈 정체성을 탐구했습니다.",
        "artist_context": "프리다는 디에고와의 이혼 직후 이 작품을 그렸습니다. 두 명의 프리다는 멕시코 정체성의 프리다(하트가 온전한)와 유럽 정체성의 프리다(하트가 찢긴)를 상징하며, 두 심장이 혈관으로 연결되어 있습니다.",
        "visual_connection": "두 자아의 심장을 잇는 혈관, 한 손에 든 가위와 실은 분리와 연결, 상처와 치유를 동시에 상징합니다. 폭풍 치는 하늘 배경은 내면의 격동을 외적 환경으로 표현합니다.",
    },
    "Self-Portrait with Thorn Necklace and Hummingbird": {
        "creation_period": "1940년, 프리다 칼로가 디에고 리베라와 이혼한 후 제작한 자화상입니다.",
        "art_movement": "초현실주의 / 멕시코 민속 미술",
        "historical_context": "20세기 중반 멕시코는 민족주의 운동과 함께 전통 테우아나 문화가 재조명되었습니다. 초현실주의 화가들도 멕시코를 방문해 이 원시적 예술에 매료되었습니다.",
        "artist_context": "프리다는 평생 30번 이상의 수술을 받는 극심한 신체적 고통을 겪었습니다. 이 자화상에서 가시 목걸이와 검은 고양이, 원숭이 등 상징 요소들은 그녀의 고통과 저항 의지를 복합적으로 표현합니다.",
        "visual_connection": "가시가 목을 파고드는 목걸이와 날아오르려는 벌새, 죽음을 상징하는 검은 고양이의 병치는 고통과 자유를 향한 갈망의 이중성을 강렬하게 전달합니다.",
    },
    # ════════════════════════════════════════════════════════════════════
    # Jan van Eyck
    # ════════════════════════════════════════════════════════════════════
    "Arnolfini Portrait": {
        "creation_period": "1434년, 얀 반 에이크가 플랑드르 상인 조반니 아르놀피니 부부를 그린 이중 초상화입니다.",
        "art_movement": "북방 르네상스 / 플랑드르 회화",
        "historical_context": "15세기 플랑드르(현재 벨기에)는 북해 무역의 중심지로 번성했습니다. 부유한 상인 계층이 등장하면서 초상화와 종교화 주문이 활발해졌습니다.",
        "artist_context": "반 에이크는 유화 기법을 발전시켜 섬세한 빛의 표현과 질감 묘사를 가능하게 했습니다. 배경 볼록 거울에 반사된 방의 전경, 서명 '얀 반 에이크가 여기 있었다'는 독특한 요소로 유명합니다.",
        "visual_connection": "유화 특유의 빛나는 질감으로 표현된 황동 샹들리에, 모피 코트, 오렌지들의 정밀한 묘사는 북방 르네상스 특유의 자연주의적 세밀화를 보여줍니다. 볼록 거울의 반영은 그림 속 공간을 확장하는 혁신적 장치입니다.",
    },
    # ════════════════════════════════════════════════════════════════════
    # Pieter Bruegel the Elder
    # ════════════════════════════════════════════════════════════════════
    "Hunters in the Snow": {
        "creation_period": "1565년, 피터르 브뤼헐이 플랑드르의 계절 연작 중 하나로 제작한 겨울 풍경화입니다.",
        "art_movement": "북방 르네상스 / 플랑드르 회화",
        "historical_context": "16세기 플랑드르에서는 계절의 변화를 담은 달력화 전통이 있었습니다. 브뤼헐은 이 전통을 따르면서도 농민들의 삶을 대규모 풍경 속에 자연스럽게 배치했습니다.",
        "artist_context": "브뤼헐은 농민 생활을 즐겨 그려 '농민 브뤼헐'이라는 별명을 얻었습니다. 그는 넓은 파노라마 구도 속에 농민들의 일상을 생동감 있게 포착했습니다.",
        "visual_connection": "눈 덮인 언덕 위의 사냥꾼들에서 멀리 얼어붙은 연못의 스케이트 타는 이들까지, 대각선 구도로 깊이감 있게 펼쳐지는 겨울 풍경은 공간감과 생동감이 뛰어난 북방 르네상스 풍경화의 걸작입니다.",
    },
    # ════════════════════════════════════════════════════════════════════
    # Marc Chagall
    # ════════════════════════════════════════════════════════════════════
    "I and the Village": {
        "creation_period": "1911년, 마르크 샤갈이 파리에서 제작한 초기 대표작으로 고향 비테프스크의 기억을 담은 작품입니다.",
        "art_movement": "큐비즘 / 초현실주의 / 표현주의",
        "historical_context": "20세기 초 파리는 세계 각지의 예술가들이 모이는 국제적 예술 중심지였습니다. 샤갈은 러시아계 유대인 이민자로, 파리의 전위 예술과 자신의 민속적·신화적 전통을 결합했습니다.",
        "artist_context": "샤갈은 파리에서 몽마르트르 아틀리에에 머물며 큐비즘과 야수주의를 접했지만, 자신만의 환상적이고 서정적인 화풍을 발전시켰습니다. 이 작품은 고향과 현재, 꿈과 현실을 자유롭게 결합합니다.",
        "visual_connection": "염소와 사람의 얼굴이 원으로 연결되고, 거꾸로 서 있는 여인과 마을 풍경이 중첩되는 환상적 구성은 유대 민속 전통과 큐비즘적 다시점을 결합한 샤갈 특유의 '마법 현실주의'를 보여줍니다.",
    },
    # ════════════════════════════════════════════════════════════════════
    # Piet Mondrian
    # ════════════════════════════════════════════════════════════════════
    "Composition with Red, Blue and Yellow": {
        "creation_period": "1930년, 피트 몬드리안이 데 스테일(De Stijl) 운동의 원리를 완성한 추상 회화입니다.",
        "art_movement": "추상주의 / 신조형주의 / 데 스테일",
        "historical_context": "20세기 초 유럽에서는 제1차 세계대전의 혼란을 극복하기 위해 순수한 조화와 균형을 추구하는 예술 운동들이 등장했습니다. 데 스테일은 최소한의 요소로 우주적 질서를 표현하려 했습니다.",
        "artist_context": "몬드리안은 신지학(Theosophy)의 영향을 받아 수평선(여성 원리)과 수직선(남성 원리)의 조화가 우주적 균형을 나타낸다고 믿었습니다. 삼원색과 흑백만을 사용해 순수한 조형적 관계를 탐구했습니다.",
        "visual_connection": "검은 격자선으로 구분된 빨강·파랑·노랑 색면과 흰 여백은 최소한의 요소로 최대한의 균형을 실현합니다. 이 단순한 구성은 이후 디자인·패션·건축에 광범위한 영향을 미쳤습니다.",
    },
    # ════════════════════════════════════════════════════════════════════
    # Edward Hopper
    # ════════════════════════════════════════════════════════════════════
    "Nighthawks": {
        "creation_period": "1942년, 에드워드 호퍼가 뉴욕 그리니치빌리지의 심야 식당을 배경으로 그린 미국 현대 미술의 아이콘입니다.",
        "art_movement": "사실주의 / 미국 모더니즘",
        "historical_context": "1940년대 미국은 제2차 세계대전 중이었습니다. 전쟁과 도시화로 개인의 고독과 소외가 심화되었고, 호퍼는 미국 도시 생활의 이면에 깔린 고독을 회화로 포착했습니다.",
        "artist_context": "호퍼는 미국 도시 생활의 고독을 탁월하게 표현하는 화가였습니다. 그는 실제 뉴욕의 특정 식당을 모델로 삼지 않고 여러 장소를 종합한 상상의 공간을 만들었다고 밝혔습니다.",
        "visual_connection": "어두운 도시 밤거리를 배경으로 유리 너머 형광등 빛에 비추어지는 인물들은 물리적으로 함께 있으면서도 심리적으로 고립된 현대 도시인의 소외를 시각화합니다.",
    },
    # ════════════════════════════════════════════════════════════════════
    # Jackson Pollock
    # ════════════════════════════════════════════════════════════════════
    "No. 31": {
        "creation_period": "1950년, 잭슨 폴록이 드립 페인팅(drip painting) 기법으로 제작한 액션 페인팅의 대표작입니다.",
        "art_movement": "추상 표현주의 / 액션 페인팅",
        "historical_context": "제2차 세계대전 이후 미국 뉴욕이 세계 현대 미술의 중심지로 부상했습니다. 추상 표현주의는 전후 미국의 자유와 개인주의를 표방하며 유럽 중심의 미술 질서를 바꾸었습니다.",
        "artist_context": "폴록은 캔버스를 바닥에 놓고 주위를 걸어다니며 물감을 떨어뜨리고 뿌리는 드립 페인팅을 개발했습니다. 그는 이 과정에서 무의식과 우연성이 회화에 직접 개입한다고 믿었습니다.",
        "visual_connection": "온 화면을 덮는 균질한 물감 망은 기존의 구도 개념을 해체하고, 신체 전체의 움직임으로 만들어진 에너지와 리듬을 캔버스에 그대로 새깁니다.",
    },
    # ════════════════════════════════════════════════════════════════════
    # Additional famous works
    # ════════════════════════════════════════════════════════════════════
    "The Ambassadors": {
        "creation_period": "1533년, 한스 홀바인이 영국 주재 프랑스 대사들을 그린 이중 초상화입니다.",
        "art_movement": "북방 르네상스",
        "historical_context": "16세기 영국은 헨리 8세의 종교 개혁으로 가톨릭과 갈등을 빚고 있었습니다. 그림 속 두 인물은 이 혼란스러운 시기에 외교 임무를 띠고 영국을 방문한 프랑스 귀족들입니다.",
        "artist_context": "홀바인은 대기 원근법과 섬세한 직물·물건 묘사로 유명한 북방 르네상스의 거장입니다. 이 작품 하단에 그려진 왜곡된 해골(아나모르피즘)은 허영과 죽음을 상기시키는 장치입니다.",
        "visual_connection": "두 인물 사이에 배치된 지구의·악기·책 등의 정교한 묘사와 바닥의 왜곡된 해골은 지식의 허영과 삶의 덧없음에 대한 메멘토 모리(memento mori) 메시지를 담고 있습니다.",
    },
    "Girl with a Red Hat": {
        "creation_period": "1665~1666년경, 요하네스 페르메이르가 제작한 소형 트로니(tronie, 인물 습작) 작품입니다.",
        "art_movement": "바로크 / 네덜란드 황금시대",
        "historical_context": "17세기 네덜란드에서는 초상화 외에 특정 인물의 유형이나 표정을 연구하는 '트로니' 장르가 발달했습니다. 렘브란트와 페르메이르 모두 이 장르의 뛰어난 작품을 남겼습니다.",
        "artist_context": "페르메이르의 작품 중 가장 소형이며, 패널(나무판)에 그려진 드문 작품입니다. 빨간 모자와 파란 가운, 진주 귀걸이를 한 여인의 생동감 있는 표현이 특징입니다.",
        "visual_connection": "어두운 배경에서 빨간 모자가 밝게 빛나며 인물을 부각시킵니다. 카메라 옵스쿠라를 연상시키는 피사계 심도 표현과 진주의 빛 처리는 페르메이르 특유의 빛 연구를 보여줍니다.",
    },
    "Ophelia": {
        "creation_period": "1851~1852년, 존 에버렛 밀레이가 셰익스피어 '햄릿'의 오필리아가 물에 잠기는 장면을 그린 작품입니다.",
        "art_movement": "라파엘 전파",
        "historical_context": "19세기 중반 영국에서는 산업화에 반발해 중세와 르네상스 이전의 순수한 자연 묘사를 추구하는 라파엘 전파(Pre-Raphaelites) 운동이 등장했습니다.",
        "artist_context": "밀레이는 모델 엘리자베스 시달을 4개월 동안 겨울철 냉수 욕조에서 포즈를 취하게 했습니다. 배경의 식물들은 현장에서 각각의 상징적 의미를 갖도록 세심하게 선택된 실제 식물입니다.",
        "visual_connection": "물 위에 떠 있는 오필리아의 하얀 드레스와 주변을 둘러싼 정교하게 묘사된 꽃들은 삶과 죽음의 경계에 놓인 비극적 아름다움을 완벽하게 포착합니다.",
    },
    "Whistler's Mother": {
        "creation_period": "1871년, 제임스 애벗 맥닐 휘슬러가 어머니 안나 휘슬러의 초상을 그린 작품입니다.",
        "art_movement": "유미주의(Aestheticism) / 모더니즘 전조",
        "historical_context": "19세기 후반 영국과 미국에서는 '예술을 위한 예술(l'art pour l'art)' 원칙을 내세우는 유미주의 운동이 등장했습니다. 휘슬러는 이 운동의 핵심 인물이었습니다.",
        "artist_context": "휘슬러는 이 작품의 정식 제목을 '회색과 검정색의 배치 1번'이라 지었습니다. 그는 색채와 형태의 순수한 조화를 강조했으며, 감상적인 해석보다 형식적 구성을 우선시했습니다.",
        "visual_connection": "검정·회색·흰색의 제한된 팔레트로 이루어진 엄격한 구성은 회화를 색채의 교향악으로 보는 휘슬러의 '음악적 회화' 개념을 실현합니다.",
    },
}

_STATIC_ARTIST_ERA = {
    # ════════════════════════════════════════════════════════════════════
    # Post-Impressionism
    # ════════════════════════════════════════════════════════════════════
    "Vincent van Gogh": {
        "creation_period": "주로 1880년대~1890년, 약 10년간의 짧은 화가 생활 동안 900점 이상의 그림을 남겼습니다.",
        "art_movement": "후기 인상주의",
        "historical_context": "19세기 후반 유럽은 인상주의 이후 새로운 예술적 방향을 모색하던 시기였습니다. 반 고흐는 파리에서 인상주의를 접하고, 이후 남프랑스와 생레미에서 자신만의 강렬한 화풍을 완성했습니다.",
        "artist_context": "반 고흐는 목사 아들로 태어나 뒤늦게 화가의 길을 걸었습니다. 극심한 정신적 고통 속에서도 불굴의 창작 의지로 후기 인상주의를 대표하는 화풍을 이뤘으며, 37세에 안타깝게 세상을 떠났습니다.",
        "visual_connection": "굵고 역동적인 붓터치, 보색의 강렬한 대비, 소용돌이치는 선은 반 고흐 작품 전반의 특징으로, 자연과 인물에 대한 강렬한 감정적 공명을 시각화합니다.",
    },
    "Paul Cézanne": {
        "creation_period": "19세기 후반~20세기 초, 인상주의에서 출발해 큐비즘의 토대가 된 독자적 화풍을 완성했습니다.",
        "art_movement": "후기 인상주의",
        "historical_context": "19세기 후반 세잔은 파리 인상주의 그룹과 교류하다가 고향 엑상프로방스로 돌아가 독자적인 회화 탐구를 이어갔습니다. 그의 작업은 피카소·브라크의 큐비즘에 직접적 영향을 주었습니다.",
        "artist_context": "세잔은 '인상주의를 미술관의 예술처럼 견고하고 지속적인 것으로 만들겠다'는 목표를 가졌습니다. 자연을 원통·구·원뿔로 파악하는 그의 구조적 접근법은 20세기 추상 미술의 씨앗이 되었습니다.",
        "visual_connection": "사물의 여러 시점을 동시에 담은 복합 원근법, 짧고 평행한 붓터치로 이루어진 색면들은 형태의 견고함과 공간감을 동시에 표현하는 세잔 특유의 조형 언어를 보여줍니다.",
    },
    "Paul Gauguin": {
        "creation_period": "19세기 후반, 프랑스 인상주의에서 출발해 타히티로 떠나 원시주의적 상징주의 화풍을 완성했습니다.",
        "art_movement": "후기 인상주의 / 상징주의 / 원시주의",
        "historical_context": "19세기 말 유럽 식민지 확장으로 태평양·카리브해 문화가 '원시적 낙원'으로 낭만화되었습니다. 고갱은 서구 문명의 타락에서 벗어나 '순수한' 원시 문화 속에서 진정한 예술을 찾으려 타히티로 이주했습니다.",
        "artist_context": "고갱은 증권 중개인 생활을 청산하고 화가가 되어 브르타뉴·파나마·마르티니크·타히티를 거쳤습니다. 반 고흐와 아를에서 함께 생활하다 극적으로 결별한 것으로도 유명합니다.",
        "visual_connection": "원색의 평면적 색면, 검은 윤곽선, 폴리네시아 신화와 인물을 결합한 상징적 구성은 고갱의 종합주의(Synthetism) 화풍을 대표합니다.",
    },
    "Georges Seurat": {
        "creation_period": "1880년대, 짧은 생애 동안 점묘법(Pointillism)을 개발해 신인상주의를 창시했습니다.",
        "art_movement": "신인상주의 / 점묘주의",
        "historical_context": "19세기 후반 과학적 색채 이론(슈브뢸·루드의 색채 대비 이론)이 발전하면서 이를 회화에 적용하려는 시도가 등장했습니다. 쇠라는 이 이론을 체계화해 '과학적 인상주의'를 실현했습니다.",
        "artist_context": "쇠라는 31세에 디프테리아로 요절했지만, 점묘법으로 이후 추상 미술과 옵 아트에 이르는 색채 과학의 토대를 마련했습니다. 그는 그림 속 색점들이 관람자의 눈에서 혼합된다고 믿었습니다.",
        "visual_connection": "순수한 색채의 점을 규칙적으로 찍어 만드는 화면은 가까이서 보면 추상적 패턴이지만, 멀리서 보면 빛나는 색채의 풍경으로 변모하는 광학적 효과를 만들어냅니다.",
    },
    # ════════════════════════════════════════════════════════════════════
    # Impressionism
    # ════════════════════════════════════════════════════════════════════
    "Claude Monet": {
        "creation_period": "19세기 중반~20세기 초, 약 60년에 걸친 화가 생활로 인상주의를 창시하고 완성했습니다.",
        "art_movement": "인상주의",
        "historical_context": "19세기 후반 프랑스에서 전통적 아카데미 회화에 반발한 화가들이 야외에서 빛의 변화를 포착하는 인상주의 운동을 시작했습니다. 모네의 '인상, 일출'이 이 운동의 이름이 되었습니다.",
        "artist_context": "모네는 평생 빛과 색채의 순간적 변화를 포착하는 데 헌신했습니다. 말년에 지베르니 정원을 직접 가꾸며 수련 연작에 몰두했고, 백내장으로 시력을 잃어가면서도 창작을 멈추지 않았습니다.",
        "visual_connection": "자연의 순간적인 빛과 대기 변화를 포착하기 위해 빠른 붓터치와 밝은 색채를 사용하는 모네의 기법은 인상주의의 핵심 원리를 완벽하게 구현합니다.",
    },
    "Pierre-Auguste Renoir": {
        "creation_period": "19세기 후반~20세기 초, 인상주의 창시 멤버로서 파리 시민의 삶과 기쁨을 밝고 생동감 있게 표현했습니다.",
        "art_movement": "인상주의",
        "historical_context": "19세기 후반 파리는 산업화와 도시화 속에서 새로운 중산층 문화가 꽃피었습니다. 카페·무도회·야외 소풍 등 여가 문화가 발달했고, 르누아르는 이 시대의 활기찬 일상을 즐겨 포착했습니다.",
        "artist_context": "르누아르는 도자기 공방 직공 출신으로 독학으로 화가가 되었습니다. 그는 인간의 행복과 아름다움을 표현하는 것이 예술의 사명이라고 믿었으며, 만년에 관절염으로 손이 굽어도 붓을 손에 묶어 그림을 계속 그렸습니다.",
        "visual_connection": "따뜻한 색채와 부드러운 붓터치로 표현된 인물의 피부 질감, 빛과 그늘이 어우러진 생동감 있는 군중 장면은 르누아르의 낙관적이고 감각적인 예술 세계를 반영합니다.",
    },
    "Edgar Degas": {
        "creation_period": "19세기 후반~20세기 초, 발레·경마·카페 등 현대 도시 생활을 즐겨 그린 인상주의 화가입니다.",
        "art_movement": "인상주의",
        "historical_context": "19세기 후반 파리는 현대적 도시 생활이 꽃피던 시기였습니다. 사진술의 발달이 화가들에게 새로운 시각적 구도와 순간 포착의 가능성을 보여주었습니다.",
        "artist_context": "드가는 부유한 가정 출신으로 르누아르·모네와 달리 야외 작업보다 실내와 인공 조명을 즐겼습니다. 독신으로 살며 발레리나·세탁부·목욕하는 여인 등을 즐겨 그렸으며, 말년에 시력을 잃고 조각에 몰두했습니다.",
        "visual_connection": "사진처럼 비대칭적이고 잘린 구도, 순간적인 움직임의 포착, 파스텔의 섬세한 색채는 드가의 독창적인 현대적 시각을 보여줍니다.",
    },
    "Édouard Manet": {
        "creation_period": "19세기 중반~후반, 전통 회화에서 인상주의로의 가교 역할을 한 혁신적 화가입니다.",
        "art_movement": "사실주의 / 인상주의 전조",
        "historical_context": "19세기 중반 프랑스 살롱전은 예술의 공식 관문이었습니다. 마네는 살롱전에서 인정받기를 원하면서도 전통에 도전하는 작품으로 매번 논란을 일으켰습니다.",
        "artist_context": "마네는 인상주의 그룹의 정신적 지도자였지만 정작 인상주의 전시에는 거의 참가하지 않았습니다. 벨라스케스·고야·할스 등 과거 거장들에 깊은 경의를 표하면서도 현대적 주제로 전통을 뒤집었습니다.",
        "visual_connection": "평면적 색채 처리, 굵은 윤곽선, 대담한 명암 대비는 마네 특유의 화풍으로, 전통적인 원근법과 명암법에서 벗어나 현대 회화의 평면성을 예고했습니다.",
    },
    # ════════════════════════════════════════════════════════════════════
    # Symbolism / Art Nouveau / Vienna Secession
    # ════════════════════════════════════════════════════════════════════
    "Gustav Klimt": {
        "creation_period": "19세기 후반~20세기 초, 빈 분리파를 이끌며 아르누보와 상징주의를 결합한 독창적 화풍을 완성했습니다.",
        "art_movement": "상징주의 / 아르누보 / 빈 분리파",
        "historical_context": "세기말 빈은 합스부르크 제국의 수도로 화려한 문화와 예술의 중심지였습니다. 전통적 아카데미즘에 반발한 클림트는 분리파를 창립해 새로운 미학을 추구했습니다.",
        "artist_context": "클림트는 빈 분리파의 핵심 인물로, 황금빛 장식과 관능적 표현으로 당시 보수적인 빈 사회와 갈등을 겪었습니다. 비잔틴 모자이크와 일본 우키요에에서 영향을 받아 독자적인 장식 양식을 발전시켰습니다.",
        "visual_connection": "금박과 기하학적 문양, 장식적 패턴과 관능적 인체 표현의 결합은 클림트 작품의 핵심으로, 세기말 빈의 화려함과 에로티시즘을 동시에 반영합니다.",
    },
    "Edvard Munch": {
        "creation_period": "19세기 후반~20세기 초, 인간의 불안·사랑·죽음을 주제로 표현주의적 화풍을 개척했습니다.",
        "art_movement": "표현주의 / 상징주의",
        "historical_context": "19세기 말 유럽은 산업화와 도시화로 인한 불안과 소외감이 팽배했습니다. 니체와 프로이트의 영향 속에 인간 내면의 어두운 면을 탐구하는 예술이 주목받았습니다.",
        "artist_context": "뭉크는 어린 시절부터 어머니·누나의 죽음, 자신의 정신적 불안 등 삶의 고통을 직접 겪었습니다. 이러한 경험들은 그의 작품 전반에 걸쳐 불안·공포·죽음의 주제로 강하게 나타납니다.",
        "visual_connection": "굴곡진 선과 강렬한 색채, 비틀린 형태는 뭉크 특유의 표현주의적 기법으로, 내면의 감정을 시각적 형태로 외화(外化)하는 데 탁월합니다.",
    },
    # ════════════════════════════════════════════════════════════════════
    # Renaissance
    # ════════════════════════════════════════════════════════════════════
    "Leonardo da Vinci": {
        "creation_period": "15세기 후반~16세기 초, 르네상스 최고의 천재로 회화·조각·건축·과학·음악 등 모든 분야에 걸쳐 업적을 남겼습니다.",
        "art_movement": "르네상스 / 전성기 르네상스",
        "historical_context": "15~16세기 이탈리아 르네상스는 고대 그리스·로마 문명의 부활과 인문주의를 중심으로 예술·과학·철학이 융합되던 시기였습니다. 다 빈치는 이 시대 정신의 완벽한 구현자였습니다.",
        "artist_context": "다 빈치는 '만능인(Uomo Universale)'의 전형으로, 회화와 동시에 해부학·지질학·수리학·비행술까지 연구했습니다. 그는 스푸마토 기법을 개발해 자연의 빛과 형태를 과학적으로 재현했습니다.",
        "visual_connection": "스푸마토 기법의 부드러운 명암 처리, 과학적 해부학 지식에서 비롯된 정확한 인체 표현, 대기 원근법의 섬세한 적용은 다 빈치 작품의 특징적 요소입니다.",
    },
    "Michelangelo": {
        "creation_period": "15세기 후반~16세기 중반, 조각·회화·건축 모두에서 르네상스의 이상을 완성한 거장입니다.",
        "art_movement": "전성기 르네상스 / 매너리즘",
        "historical_context": "16세기 초 로마는 교황 율리우스 2세와 레오 10세의 후원 아래 예술의 황금기를 맞았습니다. 미켈란젤로는 시스티나 성당 천장화와 성 베드로 대성당 설계 등 교황청의 주요 프로젝트를 도맡았습니다.",
        "artist_context": "미켈란젤로는 자신을 화가가 아닌 조각가로 여겼습니다. 그는 인체에서 신성(神性)을 발견할 수 있다고 믿었으며, 거대한 대리석 조각 '다비드'와 '피에타'는 이 신념의 결정체입니다.",
        "visual_connection": "완벽히 이상화된 근육질 인체, 역동적이고 긴장감 넘치는 포즈, 조각적 입체감을 회화로 구현하는 방식은 미켈란젤로의 예술 전반을 관통하는 특징입니다.",
    },
    "Raphael": {
        "creation_period": "15세기 말~16세기 초, 르네상스 3대 거장 중 가장 조화롭고 우아한 화풍으로 이상적 아름다움을 표현했습니다.",
        "art_movement": "전성기 르네상스",
        "historical_context": "16세기 초 바티칸은 가톨릭 예술의 중심지였습니다. 라파엘로는 다 빈치·미켈란젤로와 함께 교황의 부름을 받아 로마에서 활동하며 르네상스의 정점을 이루었습니다.",
        "artist_context": "라파엘로는 37세에 요절했지만, 온화하고 완벽한 인체 표현과 조화로운 구성으로 후대 화가들의 이상이 되었습니다. 특히 성모 마리아를 우아하고 인간적으로 표현한 수많은 성모화로 유명합니다.",
        "visual_connection": "균형 잡힌 삼각형 구성, 온화하고 이상화된 인물 표현, 차분하고 조화로운 색채는 라파엘로 작품의 전형적 특징으로, 고전적 아름다움의 표준을 제시했습니다.",
    },
    "Sandro Botticelli": {
        "creation_period": "15세기 후반, 메디치 가문의 후원 아래 피렌체에서 초기 르네상스의 우아한 화풍을 완성했습니다.",
        "art_movement": "초기 르네상스",
        "historical_context": "15세기 피렌체는 메디치 가문 통치 하에 신플라톤주의 철학과 인문주의가 꽃피던 이탈리아 르네상스의 심장부였습니다. 고대 신화와 알레고리를 주제로 한 대형 회화가 유행했습니다.",
        "artist_context": "보티첼리는 메디치 가문의 총애를 받으며 철학자 피치노의 신플라톤주의 사상에 깊이 영향 받았습니다. 그러나 말년에 사보나롤라의 종교적 열정에 감화되어 세속적 그림들을 불태웠다는 전설도 있습니다.",
        "visual_connection": "우아하게 흐르는 선율적 윤곽선, 섬세한 인물 표현, 신화적 상징이 가득한 알레고리 구성은 보티첼리 특유의 서정적이고 몽환적인 세계를 만들어냅니다.",
    },
    # ════════════════════════════════════════════════════════════════════
    # Baroque
    # ════════════════════════════════════════════════════════════════════
    "Rembrandt": {
        "creation_period": "17세기, 네덜란드 황금시대 최고의 화가로 자화상·초상화·종교화에서 빛과 어둠의 극적 표현을 완성했습니다.",
        "art_movement": "바로크 / 네덜란드 황금시대",
        "historical_context": "17세기 네덜란드는 해상 무역으로 황금시대를 맞았습니다. 부유한 상인 계층이 예술의 주요 후원자가 되면서 초상화·장르화·풍경화가 크게 발달했습니다.",
        "artist_context": "렘브란트는 생전에 큰 명성을 얻었지만 낭비벽과 미술품 수집 과욕으로 파산을 맞았습니다. 그는 평생 100점 이상의 자화상을 그려 자신의 노화 과정을 솔직하게 기록했습니다.",
        "visual_connection": "'렘브란트 조명'이라 불리는 한쪽에서 비추는 극적인 빛과 어둠의 대비(키아로스쿠로), 따뜻한 황금빛 색조, 자유롭고 표현적인 붓터치는 렘브란트 작품의 핵심입니다.",
    },
    "Johannes Vermeer": {
        "creation_period": "17세기 중반, 델프트에서 활동한 네덜란드 황금시대 화가로 빛을 다루는 탁월한 능력으로 유명합니다.",
        "art_movement": "바로크 / 네덜란드 황금시대",
        "historical_context": "17세기 네덜란드 황금시대에는 일상의 실내 장면을 사실적으로 묘사하는 장르화가 인기를 끌었습니다. 페르메이르는 이 시기 델프트에서 활동했으나 생전에는 그다지 주목받지 못했습니다.",
        "artist_context": "페르메이르는 생전에 약 40~45점의 작품만 남겼으며, 그 중 35점 정도가 현존합니다. 19세기에 재발견될 때까지 비교적 잊혀진 화가였으나, 현재는 렘브란트와 함께 네덜란드 황금시대를 대표하는 거장으로 손꼽힙니다.",
        "visual_connection": "창문을 통해 들어오는 부드러운 자연광, 정밀한 질감 묘사, 고요하고 사색적인 분위기는 페르메이르 작품 전반의 특징으로, 일상의 순간을 영원한 아름다움으로 승화시킵니다.",
    },
    "Caravaggio": {
        "creation_period": "16세기 말~17세기 초, 극적인 키아로스쿠로와 사실주의적 인물 표현으로 바로크 미술의 토대를 마련했습니다.",
        "art_movement": "바로크",
        "historical_context": "16세기 말 이탈리아 가톨릭 교회는 종교개혁에 대응하는 반종교개혁을 펼치며 감동적이고 직접적인 종교 미술을 장려했습니다. 카라바조의 생생한 사실주의는 이 요구에 정확히 부응했습니다.",
        "artist_context": "카라바조는 폭행·살인 등 법적 문제로 도망자 신세를 면치 못하면서도 로마·나폴리·몰타·시칠리아를 옮겨다니며 작품 활동을 이어갔습니다. 38세에 사망할 때까지 불꽃 같은 삶을 살았습니다.",
        "visual_connection": "어두운 배경에서 인물을 강렬하게 조명하는 '스포트라이트' 같은 빛의 효과, 성경 속 인물을 당대 평민처럼 묘사한 극적 사실주의는 카라바조의 혁명적 화풍을 규정합니다.",
    },
    "Diego Velázquez": {
        "creation_period": "17세기, 스페인 펠리페 4세의 궁정 화가로 활동하며 바로크 사실주의의 정점을 이룬 거장입니다.",
        "art_movement": "바로크",
        "historical_context": "17세기 스페인은 합스부르크 왕가의 절대 왕정 하에 있었지만 정치·경제적으로는 쇠퇴기에 접어들었습니다. 반면 예술에서는 황금시대를 맞아 벨라스케스·무리요 등의 걸작이 탄생했습니다.",
        "artist_context": "벨라스케스는 23세에 왕실 화가에 임명된 후 평생 왕실에 봉사했습니다. 루벤스의 방문을 계기로 두 차례 이탈리아를 여행해 거장들의 작품을 연구했으며, 이것이 그의 화풍 발전에 큰 영향을 미쳤습니다.",
        "visual_connection": "대기 중에 녹아드는 듯한 자유로운 붓터치, 회색·갈색 위주의 절제된 팔레트, 복잡한 심리와 사회적 관계를 포착하는 탁월한 구성력은 벨라스케스 특유의 화풍입니다.",
    },
    # ════════════════════════════════════════════════════════════════════
    # Romanticism
    # ════════════════════════════════════════════════════════════════════
    "Francisco Goya": {
        "creation_period": "18세기 후반~19세기 초, 스페인 왕실 화가로 출발해 낭만주의와 현대 미술의 문을 연 거장입니다.",
        "art_movement": "낭만주의 / 표현주의 전조",
        "historical_context": "18세기 말~19세기 초 스페인은 프랑스 혁명의 여파와 나폴레옹의 침략, 종교재판의 폭압 속에서 혼란스러운 시기를 보냈습니다. 고야는 이 시대의 어두운 면을 예리한 시선으로 기록했습니다.",
        "artist_context": "고야는 카를로스 4세의 궁정 화가로 화려한 출세를 했지만, 46세에 청력을 완전히 잃고 나서 작품의 성격이 어둡게 변했습니다. 말년의 '검은 그림' 연작은 인간 본성에 대한 그의 비관적 통찰을 집약합니다.",
        "visual_connection": "초기 밝고 장식적인 태피스트리 밑그림에서 말년의 어둡고 공포스러운 '검은 그림'에 이르기까지 고야의 화풍은 극적으로 변화했으며, 거친 붓터치와 강렬한 감정 표현이 공통된 특징입니다.",
    },
    "Eugène Delacroix": {
        "creation_period": "19세기 전반, 프랑스 낭만주의를 대표하는 화가로 역동적 구성과 강렬한 색채로 감정적 표현을 극대화했습니다.",
        "art_movement": "낭만주의",
        "historical_context": "19세기 전반 프랑스는 나폴레옹 전쟁 이후 정치적 격변기를 겪었습니다. 고전주의 대 낭만주의의 예술적 논쟁이 팽배했으며, 들라크루아는 이성적 고전주의에 맞서 감성과 운동감을 옹호했습니다.",
        "artist_context": "들라크루아는 루벤스·제리코의 영향을 받아 역동적이고 색채가 풍부한 화풍을 발전시켰습니다. 모로코 여행(1832)은 이국적 주제와 강렬한 색채에 대한 그의 관심을 더욱 심화시켰습니다.",
        "visual_connection": "소용돌이치는 구성, 강렬한 원색의 충돌, 격렬한 움직임의 표현은 들라크루아 낭만주의 화풍의 핵심으로, 르누아르·세잔 등 후대 화가들에게 색채 사용의 자유를 열어주었습니다.",
    },
    "J.M.W. Turner": {
        "creation_period": "18세기 말~19세기 중반, 영국 낭만주의 풍경화의 거장으로 빛과 대기의 표현을 극한까지 밀어붙였습니다.",
        "art_movement": "낭만주의 / 인상주의 전조",
        "historical_context": "19세기 영국은 산업혁명의 한복판에 있었습니다. 증기와 속도, 자연의 힘 앞에 선 인간의 취약함은 낭만주의 예술의 핵심 주제가 되었습니다.",
        "artist_context": "터너는 요크셔 이발사의 아들로 태어나 왕립미술원(RA)에서 교육받았습니다. 그는 실제로 폭풍 속에서 배의 돛대에 묶인 채 관찰하며 그림을 그렸다는 일화로도 유명합니다.",
        "visual_connection": "빛과 안개, 연기와 물이 뒤섞이는 소용돌이 속에 형태가 용해되는 표현은 터너의 만년 화풍으로, 인상주의와 추상 표현주의를 50~100년 앞선 혁신으로 평가됩니다.",
    },
    "Caspar David Friedrich": {
        "creation_period": "18세기 말~19세기 전반, 독일 낭만주의를 대표하는 풍경화가로 자연의 숭고함과 인간의 고독을 표현했습니다.",
        "art_movement": "낭만주의",
        "historical_context": "19세기 초 독일에서는 계몽주의에 대한 반발로 자연과 감성을 중시하는 낭만주의가 부상했습니다. 독일 자연철학(Naturphilosophie)은 자연을 신성한 힘의 표현으로 보았습니다.",
        "artist_context": "프리드리히는 개신교 신앙이 깊었으며, 그에게 자연은 신의 현존을 경험하는 장소였습니다. 그는 광대한 자연 앞에 홀로 서 있는 뒷모습 인물(Rückenfigur)을 통해 인간과 무한의 관계를 탐구했습니다.",
        "visual_connection": "광대한 자연을 마주한 작은 인간의 뒷모습, 안개에 잠긴 산과 폐허가 된 건물들, 차갑고 서정적인 색채는 프리드리히 특유의 숭고한 고독감을 만들어냅니다.",
    },
    # ════════════════════════════════════════════════════════════════════
    # Cubism / Fauvism / Modernism
    # ════════════════════════════════════════════════════════════════════
    "Pablo Picasso": {
        "creation_period": "20세기 전반, 큐비즘을 창시하고 청색 시기·장밋빛 시기·신고전주의 등 다양한 화풍을 거치며 현대 미술에 가장 큰 영향을 미쳤습니다.",
        "art_movement": "큐비즘 / 초현실주의 / 현대 미술",
        "historical_context": "20세기 초 파리는 세계 현대 미술의 중심지였습니다. 두 차례의 세계대전과 스페인 내전을 거치며 피카소는 예술을 정치적 발언의 수단으로도 적극 활용했습니다.",
        "artist_context": "피카소는 스페인 말라가 태생으로 파리로 이주해 활동했습니다. 9세에 이미 데생 실력이 정규 교육을 초월할 정도였으며, 91세에 세상을 떠날 때까지 창작을 멈추지 않았습니다.",
        "visual_connection": "여러 시점을 동시에 보여주는 다시점 분해, 기하학적 평면으로의 형태 환원, 시기마다 극적으로 달라지는 화풍은 피카소의 끊임없는 실험 정신을 보여줍니다.",
    },
    "Henri Matisse": {
        "creation_period": "20세기 전반, 야수주의를 이끌며 색채를 감정 표현의 자율적 도구로 해방시킨 거장입니다.",
        "art_movement": "야수주의 / 모더니즘",
        "historical_context": "20세기 초 파리 화단에서는 색채를 대담하게 사용하는 새로운 경향이 나타났습니다. 1905년 살롱전에 이들의 작품이 전시되었을 때, 비평가가 '야수(fauves)들의 우리'라 조롱한 것이 야수주의의 이름이 되었습니다.",
        "artist_context": "마티스는 피카소와 함께 20세기 미술의 양대 산맥으로 꼽힙니다. 두 사람은 서로의 작업을 긴장감 있게 의식하며 발전했습니다. 마티스는 말년에 관절염으로 붓을 들 수 없게 되자 색종이 오리기(커팅 아웃)로 마지막 창작을 이어갔습니다.",
        "visual_connection": "자연주의에서 해방된 순수한 원색의 대담한 사용, 장식적 패턴과 평면적 색면의 조화, 단순화된 형태 속의 풍부한 감각은 마티스 특유의 '삶의 기쁨'을 표현하는 방식입니다.",
    },
    # ════════════════════════════════════════════════════════════════════
    # Surrealism / Expressionism
    # ════════════════════════════════════════════════════════════════════
    "Salvador Dalí": {
        "creation_period": "20세기 전반, 극사실주의 기법으로 꿈과 무의식의 세계를 표현하며 초현실주의의 가장 유명한 예술가가 되었습니다.",
        "art_movement": "초현실주의",
        "historical_context": "1920~30년대 유럽에서는 제1차 세계대전 이후의 허무감과 프로이트 정신분석학의 영향으로 꿈과 무의식을 탐구하는 초현실주의 운동이 등장했습니다.",
        "artist_context": "달리는 카탈루냐 출신으로, 갈라 달리와의 만남 이후 그녀를 평생의 뮤즈이자 매니저로 삼았습니다. 그는 '편집증적 비판 방법'을 통해 이중 이미지와 착시를 체계적으로 활용했습니다.",
        "visual_connection": "포르트 리가트 해변의 사실적인 풍경 묘사 위에 뒤틀리고 녹아내리는 물체들을 극사실적으로 배치하는 방식은 꿈의 논리를 현실보다 더 사실적으로 재현하는 달리의 전략입니다.",
    },
    "René Magritte": {
        "creation_period": "20세기 전반, 일상적 대상들의 낯선 병치와 이미지·언어의 관계를 탐구하며 개념적 초현실주의를 개척했습니다.",
        "art_movement": "초현실주의",
        "historical_context": "20세기 전반 벨기에에서 활동한 마그리트는 파리 초현실주의 그룹과 교류했습니다. 그의 작품은 시각적 충격보다는 철학적 의문을 제기하는 '개념적' 초현실주의로 분류됩니다.",
        "artist_context": "마그리트는 어머니의 익사 사고로 어린 시절에 큰 트라우마를 겪었습니다. 그는 표면적으로는 안정된 브뤼셀 시민의 삶을 살면서도 회화를 통해 현실 인식에 근본적인 의문을 제기했습니다.",
        "visual_connection": "정확하고 사실적으로 그려진 일상 사물들이 불가능하거나 모순된 맥락에 놓이는 방식, 회화와 텍스트의 의도적 충돌은 마그리트 특유의 철학적 유머와 수수께끼를 만들어냅니다.",
    },
    "Frida Kahlo": {
        "creation_period": "20세기 전반, 멕시코 민속 미술과 초현실주의적 상징을 결합해 여성의 신체와 정체성·고통을 주제로 독자적 화풍을 완성했습니다.",
        "art_movement": "초현실주의 / 멕시코 민속 미술 / 나이브 아트",
        "historical_context": "20세기 초 멕시코는 혁명(1910~1920) 이후 민족 정체성 재건 운동인 '멕시카니다드(Mexicanidad)'가 강성했습니다. 프리다는 이 흐름 속에서 테우아나 원주민 복식과 전통 문화를 자신의 정체성으로 강하게 표방했습니다.",
        "artist_context": "프리다는 6세에 소아마비, 18세에 버스 사고로 평생 극심한 신체적 고통을 안고 살았습니다. 35회 이상의 수술을 받으며 침대에 누워 그림을 그렸으며, 디에고 리베라와의 격동적 결혼 생활도 작품의 핵심 주제가 되었습니다.",
        "visual_connection": "자화상의 집중적인 정면 시선, 멕시코 민속화 양식의 세밀하고 장식적인 배경, 신체적·심리적 고통을 직접적으로 시각화하는 상징적 요소들은 프리다 작품의 핵심입니다.",
    },
    # ════════════════════════════════════════════════════════════════════
    # Northern Renaissance / Flemish
    # ════════════════════════════════════════════════════════════════════
    "Jan van Eyck": {
        "creation_period": "15세기 전반, 유화 기법을 발전시켜 북방 르네상스 플랑드르 회화의 기초를 세운 거장입니다.",
        "art_movement": "북방 르네상스 / 플랑드르 회화",
        "historical_context": "15세기 플랑드르(현재 벨기에)는 부르고뉴 공국의 통치 하에 북해 무역으로 번성한 유럽 최대의 경제 중심지 중 하나였습니다. 풍요로운 경제는 섬세한 종교화와 초상화에 대한 수요를 낳았습니다.",
        "artist_context": "반 에이크는 부르고뉴 공작 필리프 선량공의 궁정 화가로 활동했습니다. 유화 기법의 발전(일부에서는 발명)으로 이전에는 불가능했던 섬세한 빛의 표현과 질감 묘사를 가능하게 했습니다.",
        "visual_connection": "유화의 반투명한 중첩 글레이즈 기법으로 표현된 빛나는 보석·직물·금속의 질감, 인물의 피부와 눈의 섬세한 묘사, 상징으로 가득한 공간 구성은 반 에이크 화풍의 특징입니다.",
    },
    "Pieter Bruegel the Elder": {
        "creation_period": "16세기 중반, 플랑드르 농민 생활과 네덜란드 속담을 주제로 한 파노라마적 풍경·풍속화의 거장입니다.",
        "art_movement": "북방 르네상스 / 플랑드르 회화",
        "historical_context": "16세기 플랑드르는 스페인 합스부르크의 통치 하에 종교적 박해와 정치적 갈등을 겪었습니다. 브뤼헐은 이 시대를 농민 생활의 시각으로 기록했습니다.",
        "artist_context": "브뤼헐은 '농민 브뤼헐'이라 불렸지만 실제로는 당시 지식인·인문주의자들과 교류한 교양 있는 화가였습니다. 네덜란드 속담과 민간 전설을 풍자적으로 그려내는 독특한 방식은 그를 16세기 최고의 풍속화가로 만들었습니다.",
        "visual_connection": "높은 시점에서 내려다보는 파노라마 구도, 수십 명의 인물이 각자의 이야기를 가지고 등장하는 복잡한 구성, 따뜻한 자연색과 계절감 있는 묘사는 브뤼헐 작품의 특징입니다.",
    },
    # ════════════════════════════════════════════════════════════════════
    # Abstract / Pop Art / Modern
    # ════════════════════════════════════════════════════════════════════
    "Piet Mondrian": {
        "creation_period": "20세기 전반, 추상 예술의 순수한 원리를 탐구하며 신조형주의(De Stijl)를 창시했습니다.",
        "art_movement": "추상주의 / 신조형주의 / 데 스테일",
        "historical_context": "20세기 초 유럽은 제1차 세계대전의 충격 속에서 새로운 시각 질서를 탐구했습니다. 몬드리안은 혼돈스러운 현실 세계를 초월한 순수한 조형적 원리를 추구했습니다.",
        "artist_context": "몬드리안은 신지학(Theosophy)에 심취해 수평·수직의 균형이 우주적 원리를 표현한다고 믿었습니다. 그는 나무·풍경 등 구상에서 출발해 점점 더 단순화된 격자 추상으로 발전했습니다.",
        "visual_connection": "검은 격자선, 삼원색(빨·파·노), 흰 여백으로만 구성된 작품들은 불필요한 모든 요소를 제거해 순수한 조형 원리만 남긴 결과로, 이후 그래픽 디자인·건축·패션에 광범위한 영향을 미쳤습니다.",
    },
    "Marc Chagall": {
        "creation_period": "20세기 전반~후반, 러시아 유대 문화의 신화와 민속을 파리 전위 미술과 결합해 독자적인 환상적 화풍을 완성했습니다.",
        "art_movement": "초현실주의 / 큐비즘 / 표현주의",
        "historical_context": "20세기 초 러시아계 유대인 예술가들이 파리에 몰려들어 에콜 드 파리(École de Paris)를 형성했습니다. 샤갈은 두 차례의 세계대전과 홀로코스트의 비극을 겪으며 이를 회화로 승화시켰습니다.",
        "artist_context": "샤갈은 벨라루스 비테프스크 출신으로 러시아 혁명 후 문화부 관리로 활동하다 파리로 이주했습니다. 그는 유대 민속 전통과 성경 이야기, 고향의 기억을 평생 작품의 원천으로 삼았습니다.",
        "visual_connection": "중력을 거스르며 하늘을 나는 인물들, 상징적인 동물들, 역동적인 색채와 환상적 공간 구성은 샤갈의 '마법 현실주의'를 특징짓는 요소들입니다.",
    },
    "Andy Warhol": {
        "creation_period": "20세기 중반~후반, 실크스크린 기법으로 대중 매체와 소비 문화의 이미지를 예술로 격상시킨 팝 아트의 대표 작가입니다.",
        "art_movement": "팝 아트",
        "historical_context": "1960년대 미국에서는 TV·잡지·광고 등 대중 매체가 급속히 성장했습니다. 팝 아트는 이러한 대중문화의 이미지를 고급 예술의 언어로 전환해 예술과 상업의 경계를 해체했습니다.",
        "artist_context": "워홀은 뉴욕에서 상업 일러스트레이터로 출발했습니다. '팩토리(The Factory)'라는 스튜디오에서 조수들과 협력해 실크스크린 작품을 대량 생산하며 작품의 유일성·독창성이라는 개념 자체에 의문을 제기했습니다.",
        "visual_connection": "기계적 인쇄물 같은 반복 이미지, 원본에서 변형된 원색의 인공적 색채 사용은 대중 매체가 이미지를 소비하고 순환시키는 방식을 예술 언어로 직접 구현합니다.",
    },
    "Jackson Pollock": {
        "creation_period": "20세기 중반, 드립 페인팅 기법을 개발해 액션 페인팅·추상 표현주의의 핵심 작가가 되었습니다.",
        "art_movement": "추상 표현주의 / 액션 페인팅",
        "historical_context": "제2차 세계대전 이후 미국 뉴욕이 파리를 대신해 세계 현대 미술의 중심지로 부상했습니다. 미국 정부는 추상 표현주의를 자유 민주주의의 상징으로 홍보하며 문화적으로 지원했습니다.",
        "artist_context": "폴록은 알코올 중독과 정신적 불안정으로 힘든 삶을 살았습니다. 정신과 치료 중 무의식적 표현에 관심을 갖게 되었고, 캔버스를 바닥에 두고 온몸으로 물감을 뿌리고 떨어뜨리는 드립 페인팅을 개발했습니다.",
        "visual_connection": "전통적인 붓의 사용을 완전히 벗어나 신체 전체의 움직임으로 만들어진 무수한 물감 궤적들은 화가의 신체 에너지와 무의식적 몸짓을 캔버스에 직접 기록합니다.",
    },
}



def _gemini_era_from_artist(artist: str, title: str, api_key: str) -> Dict[str, Any]:
    """Gemini call anchored to artist context — used for partial/artist_only when artist IS in DB."""
    genai.configure(api_key=api_key)
    schema = (
        '{"creation_period":"","art_movement":"...",'
        '"historical_context":"...","artist_context":"...","visual_connection":""}'
    )
    prompt = (
        f"화가: {artist}\n"
        f"추정 작품명: {title or '미상'}\n\n"
        "이 화가의 활동 시기와 미술 사조를 설명하세요. 작품명은 추정이므로 단정하지 마세요.\n"
        "JSON만 반환 (한국어):\n" + schema + "\n"
        "규칙: creation_period·visual_connection은 빈 문자열로 두세요. "
        "historical_context는 화가 활동 당시 시대상 2문장. "
        "artist_context는 화가의 대표 화풍·특징 2문장."
    )
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        raw = model.generate_content(prompt).text.strip()
        if "```" in raw:
            for chunk in raw.split("```"):
                chunk = chunk.strip().lstrip("json").strip()
                if chunk.startswith("{"):
                    return json.loads(chunk)
        return json.loads(raw)
    except Exception as e:
        print(f"[LLM] gemini_era_from_artist error: {e}")
        return {}


def generate_artwork_era(
    title: str,
    artist: str,
    year: str,                      # kept for API compat, not used in new flow
    identification_status: str,
    visual_context: Dict[str, Any], # kept for API compat, not used in new flow
    api_key: str,
) -> Dict[str, Any]:
    """
    작품의 시대와 이야기 섹션 생성.

    Decision tree:
    confirmed  + in DB        → verified DB data (no Gemini hallucination)
    confirmed  + NOT in DB    → _not_in_db sentinel (frontend shows 'preparing' msg)
    partial    + artist in DB → artist DB + Gemini for historical context
    partial    + NOT in DB    → _not_in_db sentinel
    artist_only + artist in DB→ artist DB + Gemini for historical context
    artist_only + NOT in DB   → _not_in_db sentinel
    unknown                   → _no_era sentinel (no historical claims at all)
    """
    from modules.era_lookup import (
        lookup_artwork, lookup_artist,
        era_response_from_artwork, era_response_from_artist,
        visual_only_response, not_in_db_response,
    )

    status_map = {
        "confirmed":   "확인된 작품",
        "partial":     "유사 추정",
        "artist_only": "화가만 확인",
        "unknown":     "정보 없음",
    }
    confidence_label = status_map.get(identification_status, "정보 없음")

    # ── unknown: no historical claims ────────────────────────────────────────
    if identification_status == "unknown":
        return visual_only_response()

    # ── confirmed: must find artwork in verified DB ───────────────────────────
    if identification_status == "confirmed":
        entry = lookup_artwork(title=title, artist=artist)
        if entry:
            return era_response_from_artwork(entry, confidence_label)
        # Not in DB — don't call Gemini with "정확한 배경 써줘"
        return not_in_db_response(title, artist, confidence_label)

    # ── partial / artist_only: anchor to artist DB, supplement with Gemini ───
    artist_entry = lookup_artist(artist)
    if artist_entry:
        base = era_response_from_artist(artist_entry, title, confidence_label)
        # Try to enrich with Gemini (artist context is verified, Gemini adds historical color)
        genai_data = _gemini_era_from_artist(artist, title, api_key)
        if genai_data:
            if genai_data.get("historical_context"):
                base["historical_context"] = genai_data["historical_context"]
            if genai_data.get("art_movement") and not base.get("art_movement"):
                base["art_movement"] = genai_data["art_movement"]
        return base

    # Artist not in DB either
    return not_in_db_response(title, artist, confidence_label)

