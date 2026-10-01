"""
gemini_client — 지원 종료된 google.generativeai 대신 google.genai SDK를 쓰는 얇은 호환 레이어.
기존 호출부(genai.configure / genai.GenerativeModel(...).generate_content(...).text)를 그대로 유지한다.

    from modules import gemini_client as genai
"""
import threading

from google import genai as _genai
from google.genai import types as _types

_lock    = threading.Lock()
_api_key = ""
_client  = None


def configure(api_key: str):
    global _api_key, _client
    with _lock:
        if api_key and api_key != _api_key:
            _api_key = api_key
            # 호출당 최대 60초 — 응답이 멈춰도 요청이 무한정 붙잡혀 있지 않게
            _client  = _genai.Client(api_key=api_key, http_options=_types.HttpOptions(timeout=60_000))


def _get_client():
    if _client is None:
        raise RuntimeError("Gemini API key가 설정되지 않았습니다 (configure 먼저 호출).")
    return _client


def _to_part(item):
    # 구 SDK 형식 {"mime_type": ..., "data": bytes} → Part
    if isinstance(item, dict) and "data" in item:
        return _types.Part.from_bytes(data=item["data"], mime_type=item.get("mime_type", "image/jpeg"))
    return item  # str, PIL.Image 등은 새 SDK가 그대로 처리


class _Response:
    def __init__(self, raw):
        self._raw = raw

    @property
    def text(self) -> str:
        t = self._raw.text
        if t is None:
            # 구 SDK는 안전 필터 등으로 텍스트가 없으면 ValueError를 던졌음 — 동작 유지
            raise ValueError("Gemini 응답에 텍스트가 없습니다 (차단되었거나 빈 응답).")
        return t


class GenerativeModel:
    def __init__(self, model_name: str, system_instruction: str | None = None):
        self.model_name = model_name
        self._config = _types.GenerateContentConfig(
            system_instruction=system_instruction,
            # 도구 호출을 쓰지 않으므로 자동 함수 호출(AFC) 비활성화
            automatic_function_calling=_types.AutomaticFunctionCallingConfig(disable=True),
        )

    def generate_content(self, contents):
        if isinstance(contents, (list, tuple)):
            contents = [_to_part(c) for c in contents]
        else:
            contents = _to_part(contents)
        raw = _get_client().models.generate_content(
            model=self.model_name, contents=contents, config=self._config,
        )
        return _Response(raw)
