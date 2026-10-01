"""
IP 기반 호출 제한 — 공개 URL에서 AI 엔드포인트(Gemini·Vision·Roboflow 비용 발생)가 무제한 호출되는 것 방지.
단일 프로세스(HF Space 1 컨테이너) 기준 메모리 슬라이딩 윈도우.

    @app.post("/api/analyze", dependencies=[Depends(limit("analyze", 20, 600))])
"""
import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request

_lock = threading.Lock()
_hits: dict[tuple[str, str], deque] = defaultdict(deque)


def client_ip(request: Request) -> str:
    # HF Spaces는 프록시 뒤에서 동작 → X-Forwarded-For의 첫 번째(원 클라이언트) 주소 사용
    fwd = request.headers.get("x-forwarded-for", "")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def limit(bucket: str, max_calls: int, window_sec: int):
    """window_sec 동안 IP당 max_calls회까지 허용하는 FastAPI 의존성."""
    def _dep(request: Request):
        now = time.monotonic()
        key = (bucket, client_ip(request))
        with _lock:
            q = _hits[key]
            while q and now - q[0] > window_sec:
                q.popleft()
            if len(q) >= max_calls:
                retry = int(window_sec - (now - q[0])) + 1
                raise HTTPException(
                    429,
                    f"요청이 너무 많아요. {max(1, retry // 60) if retry >= 60 else retry}{'분' if retry >= 60 else '초'} 후에 다시 시도해 주세요.",
                    headers={"Retry-After": str(retry)},
                )
            q.append(now)
            # 오래된 키 정리 (메모리 누수 방지)
            if len(_hits) > 5000:
                for k in [k for k, v in _hits.items() if not v or now - v[-1] > 3600]:
                    _hits.pop(k, None)
    return _dep
