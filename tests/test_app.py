import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import app


def test_home_page():
    client = app.test_client()
    response = client.get("/")
    assert response.status_code == 200
    assert b"FAQ Support Chatbot" in response.data


def test_chat_endpoint():
    client = app.test_client()
    response = client.post("/chat", json={"message": "How do I apply for admission?"})
    assert response.status_code == 200
    data = response.get_json()
    assert data["answer"]
    assert "confidence" in data
    assert data["matched_question"]


def test_invalid_request():
    client = app.test_client()
    response = client.post("/chat", json={"message": ""})
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_non_json_request():
    client = app.test_client()
    response = client.post("/chat", data="hello", content_type="text/plain")
    assert response.status_code == 400


def test_too_long_message():
    client = app.test_client()
    response = client.post("/chat", json={"message": "x" * 501})
    assert response.status_code == 400


def test_health():
    client = app.test_client()
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"
