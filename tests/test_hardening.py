"""Tests for deploy-readiness hardening: config, /ready, security headers,
rate limiting, and skill disabling.

These cover the production surface (Docker/Fly/Render/Railway all probe
/ready and rely on sane defaults), not just the chat router.
"""
import importlib
import os
import tempfile

import pytest
from fastapi.testclient import TestClient

_tmp = tempfile.mkdtemp()
os.environ["MONICO_DATA_DIR"] = os.path.join(_tmp, "data")

import main  # noqa: E402

client = TestClient(main.app)


# ---------------------------------------------------------------- /ready

def test_ready_ok():
    r = client.get("/ready")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ready"
    assert body["skills"] >= 20
    assert body["version"]


def test_ready_unwritable_data_dir_reports_503(monkeypatch):
    import config as config_module
    from dataclasses import replace
    from pathlib import Path

    patched = replace(config_module.settings,
                      data_dir=Path("/proc/definitely-not-writable-xyz"))
    monkeypatch.setattr(main, "settings", patched)
    r = client.get("/ready")
    assert r.status_code == 503
    assert r.json()["status"] == "not-ready"


# ---------------------------------------------------------------- /health extended

def test_health_has_uptime():
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert isinstance(body["uptime_seconds"], int)


# ---------------------------------------------------------------- security headers

def test_security_headers_present():
    r = client.get("/health")
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["X-Frame-Options"] == "DENY"
    assert r.headers["Referrer-Policy"] == "no-referrer"
    assert "X-Request-Id" in r.headers


def test_request_id_unique_per_request():
    a = client.get("/health").headers["X-Request-Id"]
    b = client.get("/health").headers["X-Request-Id"]
    assert a != b


# ---------------------------------------------------------------- rate limiting

def test_rate_limit_429(monkeypatch):
    import config as config_module
    from dataclasses import replace

    monkeypatch.setattr(main, "settings",
                        replace(config_module.settings, rate_limit_per_minute=2))
    main._rate_buckets.clear()
    assert client.post("/chat", json={"query": "time"}).status_code == 200
    assert client.post("/chat", json={"query": "time"}).status_code == 200
    r = client.post("/chat", json={"query": "time"})
    assert r.status_code == 429
    assert "too many requests" in r.json()["error"]["message"]
    main._rate_buckets.clear()


def test_rate_limit_disabled_when_zero(monkeypatch):
    import config as config_module
    from dataclasses import replace

    monkeypatch.setattr(main, "settings",
                        replace(config_module.settings, rate_limit_per_minute=0))
    main._rate_buckets.clear()
    for _ in range(5):
        assert client.post("/chat", json={"query": "time"}).status_code == 200
    main._rate_buckets.clear()


# ---------------------------------------------------------------- config defaults

def test_config_safe_defaults(monkeypatch):
    for key in ("MONICO_PORT", "MONICO_HOST", "MONICO_RATE_LIMIT_PER_MIN",
                "MONICO_LOG_LEVEL", "MONICO_DISABLED_SKILLS"):
        monkeypatch.delenv(key, raising=False)
    import config as config_module

    fresh = importlib.reload(config_module)
    try:
        assert fresh.Settings().port == 8000
        assert fresh.Settings().log_level == "INFO"
        assert fresh.Settings().rate_limit_per_minute == 60
        assert fresh.Settings().disabled_skills == []
    finally:
        importlib.reload(config_module)


def test_config_bad_int_falls_back(monkeypatch):
    monkeypatch.setenv("MONICO_PORT", "notaport")
    import config as config_module

    fresh = importlib.reload(config_module)
    try:
        assert fresh.Settings().port == 8000
    finally:
        importlib.reload(config_module)


# ---------------------------------------------------------------- disabled skills

def test_disabled_skill_falls_back():
    from agent import MonicoAgent

    a = MonicoAgent(disabled=("dice",))
    r = a.respond("dice")
    assert r["ok"] is False and r["skill"] == "fallback"
    # others still work
    assert a.respond("coin")["ok"] is True


def test_disabled_listed_in_capabilities():
    from agent import MonicoAgent

    a = MonicoAgent(disabled=("dice",))
    caps = a.capabilities()
    assert "dice" in caps["disabled"]
    assert "dice" not in caps["implemented"]
