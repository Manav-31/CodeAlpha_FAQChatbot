import pytest

from app import app


@pytest.fixture
def client():
    return app.test_client()


def test_home_page_has_site_and_chat_widget(client):
    page = client.get("/").get_data(as_text=True)
    assert 'id="chat-panel"' in page
    assert 'id="chat-form"' in page
    assert 'data-ask="How do I apply for admission?"' in page
    assert "What is the fee for B.Tech?" in page  # browse topics data for the widget
    assert "Small talk" not in page
    assert page.index('"Applying"') < page.index('"Eligibility"') < page.index('"Contact"')  # FAQ order, not A-Z


def test_answers_a_question(client):
    resp = client.post("/api/chat", json={"message": "What is the hostel fee?"})
    assert resp.status_code == 200
    reply = resp.get_json()
    assert reply["matched_question"] == "What is the hostel fee?"
    assert reply["score"] > 0.9
    assert set(reply) == {"answer", "matched_question", "category", "score", "suggestions"}


def test_already_asked_questions_are_not_suggested(client):
    asked = ["Is hostel available?", "Where is the college located?"]
    reply = client.post("/api/chat", json={"message": "What is the hostel fee?", "asked": asked}).get_json()
    assert len(reply["suggestions"]) == 3
    assert not set(reply["suggestions"]) & set(asked)


def test_invalid_asked_list_is_ignored(client):
    resp = client.post("/api/chat", json={"message": "What is the hostel fee?", "asked": "not a list"})
    assert resp.status_code == 200


@pytest.mark.parametrize("body, message", [
    ({"message": "   "}, "type a question"),
    ({"message": "a" * 301}, "under 300 characters"),
    ({}, "type a question"),
])
def test_invalid_messages_are_rejected(client, body, message):
    resp = client.post("/api/chat", json=body)
    assert resp.status_code == 400
    assert message in resp.get_json()["error"]
