"""yfinance용 공용 세션 + 재시도 헬퍼.

Yahoo Finance가 기본 requests 세션의 TLS 지문을 봇으로 감지해 클라우드/공유 IP에서
"Too Many Requests. Rate limited." 오류를 자주 반환하는 문제가 있어, curl_cffi로
실제 브라우저의 TLS 지문을 흉내낸 세션을 사용한다. 그래도 일시적으로 막히는 경우가
있어 짧은 지수 백오프로 재시도한다 (완전한 차단은 재시도로도 해결되지 않는다).
"""

import random
import time

from curl_cffi import requests as cffi_requests

_session = None


def get_session():
    global _session
    if _session is None:
        _session = cffi_requests.Session(impersonate="chrome")
    return _session


def fetch_with_retry(fn, retries: int = 3, base_delay: float = 1.0):
    last_exc = None
    for attempt in range(retries):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            if attempt < retries - 1:
                time.sleep(base_delay * (2**attempt) + random.uniform(0, 0.4))
    raise last_exc
