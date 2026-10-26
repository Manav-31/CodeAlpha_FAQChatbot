import pytest

from app import app


@pytest.fixture
def client():
    return app.test_client()


def test_home_page_shows_chat_and_topics(client):
    page = client.get("/").get_data(as_text=True)
    assert 'id="chat-form"' in page
    assert "Browse questions" in page
    assert "What is the fee for B.Tech?" in page
    assert "Small talk" not in page


def test_answers_a_question(client):
    resp = client.post("/api/chat", json={"message": "What is the hostel fee?"})
    assert resp.status_code == 200
    reply = resp.get_json()
    assert reply["matched_question"] == "What is the hostel fee?"
    assert reply["score"] > 0.9
    assert set(reply) == {"answer", "matched_question", "category", "score", "suggestions"}


@pytest.mark.parametrize("body, message", [
    ({"message": "   "}, "type a question"),
    ({"message": "a" * 301}, "under 300 characters"),
    ({}, "type a question"),
])
def test_invalid_messages_are_rejected(client, body, message):
    resp = client.post("/api/chat", json=body)
    assert resp.status_code == 400
    assert message in resp.get_json()["error"]
