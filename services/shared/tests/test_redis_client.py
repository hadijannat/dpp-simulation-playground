from services.shared import redis_client


REDIS_ENV_VARS = (
    "REDIS_PROTOCOL",
    "REDIS_SOCKET_TIMEOUT_SECONDS",
    "REDIS_SOCKET_CONNECT_TIMEOUT_SECONDS",
    "REDIS_SOCKET_KEEPALIVE",
    "REDIS_MAX_CONNECTIONS",
    "REDIS_RETRY_ON_TIMEOUT",
)


def test_get_redis_applies_redis_8_safe_defaults(monkeypatch):
    for name in REDIS_ENV_VARS:
        monkeypatch.delenv(name, raising=False)

    captured: dict[str, object] = {}
    expected_client = object()

    def fake_from_url(url: str, **kwargs: object) -> object:
        captured["url"] = url
        captured["kwargs"] = kwargs
        return expected_client

    monkeypatch.setattr(redis_client.redis, "from_url", fake_from_url)

    client = redis_client.get_redis("redis://cache:6379/0")

    assert client is expected_client
    assert captured == {
        "url": "redis://cache:6379/0",
        "kwargs": {
            "protocol": 2,
            "socket_timeout": 10.0,
            "socket_connect_timeout": 5.0,
            "socket_keepalive": True,
            "max_connections": 100,
            "retry_on_timeout": False,
        },
    }


def test_redis_connection_kwargs_use_env_overrides(monkeypatch):
    monkeypatch.setenv("REDIS_PROTOCOL", "3")
    monkeypatch.setenv("REDIS_SOCKET_TIMEOUT_SECONDS", "30")
    monkeypatch.setenv("REDIS_SOCKET_CONNECT_TIMEOUT_SECONDS", "7.5")
    monkeypatch.setenv("REDIS_SOCKET_KEEPALIVE", "false")
    monkeypatch.setenv("REDIS_MAX_CONNECTIONS", "25")
    monkeypatch.setenv("REDIS_RETRY_ON_TIMEOUT", "true")

    assert redis_client.redis_connection_kwargs() == {
        "protocol": 3,
        "socket_timeout": 30.0,
        "socket_connect_timeout": 7.5,
        "socket_keepalive": False,
        "max_connections": 25,
        "retry_on_timeout": True,
    }
