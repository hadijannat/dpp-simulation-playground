from __future__ import annotations

import threading
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

_sessions: dict[str, requests.Session] = {}
_lock = threading.Lock()


def _build_retry_policy(total_retries: int) -> Retry:
    return Retry(
        total=total_retries,
        connect=total_retries,
        read=total_retries,
        status=total_retries,
        backoff_factor=0.2,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"}),
        raise_on_status=False,
    )


def get_session(name: str = "default", *, total_retries: int = 3) -> requests.Session:
    with _lock:
        if name in _sessions:
            return _sessions[name]

        session = requests.Session()
        adapter = HTTPAdapter(max_retries=_build_retry_policy(total_retries), pool_connections=20, pool_maxsize=100)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        _sessions[name] = session
        return session


def request(
    method: str,
    url: str,
    *,
    session_name: str = "default",
    timeout: float | tuple[float, float] = 8,
    **kwargs: Any,
) -> requests.Response:
    session = get_session(name=session_name)
    return session.request(method=method, url=url, timeout=timeout, **kwargs)
