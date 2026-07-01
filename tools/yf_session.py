"""yfinance용 공용 세션.

Yahoo Finance가 기본 requests 세션의 TLS 지문을 봇으로 감지해 클라우드/공유 IP에서
"Too Many Requests. Rate limited." 오류를 자주 반환하는 문제가 있어, curl_cffi로
실제 브라우저의 TLS 지문을 흉내낸 세션을 사용한다.
"""

from curl_cffi import requests as cffi_requests

_session = None


def get_session():
    global _session
    if _session is None:
        _session = cffi_requests.Session(impersonate="chrome")
    return _session
