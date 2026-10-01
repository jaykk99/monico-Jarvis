"""Real tests for Monico Jarvis: endpoints, skills, validation, errors."""
import os
import tempfile

import pytest
from fastapi.testclient import TestClient

# isolate note storage per test session
_tmp = tempfile.mkdtemp()
os.environ["MONICO_DATA_DIR"] = os.path.join(_tmp, "data")

import main  # noqa: E402

client = TestClient(main.app)


def test_console_serves_html():
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "MONICO JARVIS" in r.text


def test_static_assets():
    assert client.get("/static/style.css").status_code == 200
    assert client.get("/static/app.js").status_code == 200


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_skills_listed():
    r = client.get("/skills")
    names = {s["name"] for s in r.json()["skills"]}
    assert {"time", "date", "calc", "echo", "notes", "status", "help"} <= names


def test_capabilities_honest():
    r = client.get("/capabilities")
    body = r.json()
    assert body["api_keys_required"] is False
    assert body["network_calls"] is False
    assert isinstance(body["not_implemented"], list) and body["not_implemented"]


def test_chat_time():
    r = client.post("/chat", json={"query": "time"})
    body = r.json()
    assert body["ok"] is True and body["skill"] == "time"
    assert ":" in body["response"]


def test_chat_calc():
    r = client.post("/chat", json={"query": "calc (12 + 8) * 3"})
    assert r.json()["response"].endswith("= 60")


def test_chat_calc_rejects_junk():
    r = client.post("/chat", json={"query": "calc __import__('os').system('x')"})
    body = r.json()
    assert body["ok"] is True  # skill handled it, no 500
    assert "Can't compute" in body["response"]


def test_chat_echo():
    r = client.post("/chat", json={"query": "echo hello jarvis"})
    assert r.json()["response"] == "hello jarvis"


def test_chat_notes_roundtrip():
    assert "Noted" in client.post("/chat", json={"query": "note buy milk"}).json()["response"]
    listed = client.post("/chat", json={"query": "notes"}).json()["response"]
    assert "buy milk" in listed
    assert "cleared" in client.post("/chat", json={"query": "note clear"}).json()["response"].lower()


def test_chat_unknown_is_honest_fallback():
    r = client.post("/chat", json={"query": "launch the missiles"})
    body = r.json()
    assert body["ok"] is False
    assert body["skill"] == "fallback"
    assert "help" in body["response"]


def test_chat_query_param_backward_compat():
    r = client.post("/chat", params={"query": "date"})
    assert r.json()["skill"] == "date"


def test_chat_missing_query_400():
    r = client.post("/chat", json={"query": "   "})
    assert r.status_code == 400
    assert "error" in r.json()


def test_chat_oversize_rejected():
    r = client.post("/chat", json={"query": "x" * 2001})
    assert r.status_code == 422


def test_structured_404():
    r = client.get("/nope")
    assert r.status_code == 404
    assert "error" in r.json()
