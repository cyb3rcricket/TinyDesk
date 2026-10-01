import json
import logging
import re
from pathlib import Path

import pytest

from backend.app import app, get_model_client
from backend.ollama_client import ModelCallError
from backend.schemas import CATEGORIES, PRIORITIES, STATUSES

ROOT = Path(__file__).resolve().parents[1]
SECRET = "SECRET_TICKET_BODY_9f3a"

VALID_MODEL = {
    "summary": "The VPN client stops while contacting the gateway.",
    "suggestedCategory": "Network",
    "followUps": ["What exact error text appears after contacting gateway?"],
    "draft": "Hello Mara,\n\nI am looking at the VPN connection.\n\nAshmere Press IT",
}


class FakeModel:
    def __init__(self, results):
        self.results = list(results)
        self.calls = []

    def complete(self, *, model, messages, schema, timeout):
        self.calls.append(
            {"model": model, "messages": messages, "schema": schema, "timeout": timeout}
        )
        item = self.results.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def ticket(**overrides):
    payload = {
        "id": "TD-2401",
        "subject": "Home VPN will not connect",
        "description": "The VPN client stops at contacting gateway.",
        "requester": "Mara Ellison",
        "department": "Editorial",
        "category": "Network",
        "priority": "High",
        "status": "In Progress",
        "resolutionNote": "",
        "activity": [
            {"kind": "opened", "body": "Ticket created.", "at": "2026-09-28T14:12:00.000Z"},
            {
                "kind": "internal",
                "body": "Checked the VPN profile.",
                "at": "2026-09-28T15:05:00.000Z",
            },
        ],
    }
    payload.update(overrides)
    return payload


def use_model(fake):
    app.dependency_overrides[get_model_client] = lambda: fake


def test_valid_model_output_keeps_the_frontend_contract(client):
    fake = FakeModel([json.dumps(VALID_MODEL)])
    use_model(fake)
    response = client.post("/api/analyze-ticket", json=ticket(category="Other"))
    body = response.json()
    assert response.status_code == 200
    assert body == {
        "available": True,
        "summary": VALID_MODEL["summary"],
        "suggestedCategory": "Network",
        "followUps": VALID_MODEL["followUps"],
        "draft": VALID_MODEL["draft"],
    }
    assert "message" not in body
    assert fake.calls[0]["schema"]["properties"]["suggestedCategory"]["enum"] == list(CATEGORIES)
    assert fake.calls[0]["messages"][0]["role"] == "system"
    assert fake.calls[0]["messages"][1]["role"] == "user"
    assert len(fake.calls[0]["messages"]) == 2


def test_prompt_sends_current_fields_activity_and_rules(client):
    fake = FakeModel([json.dumps(VALID_MODEL)])
    use_model(fake)
    client.post("/api/analyze-ticket", json=ticket())
    system = fake.calls[0]["messages"][0]["content"]
    user = fake.calls[0]["messages"][1]["content"]
    assert "untrusted" in system.lower()
    assert "Do not invent company policies" in system
    assert "Never claim the issue has been fixed" in system
    for category in CATEGORIES:
        assert category in system
    data = json.loads(user.split("\n\n", 1)[1])
    assert data["subject"] == "Home VPN will not connect"
    assert data["description"] == "The VPN client stops at contacting gateway."
    assert data["currentFields"]["category"] == "Network"
    assert data["currentFields"]["priority"] == "High"
    assert data["currentFields"]["status"] == "In Progress"
    assert data["activity"][1]["body"] == "Checked the VPN profile."
    assert data["omittedEarlierActivityCount"] == 0
    assert "Home VPN will not connect" not in system


def test_only_recent_activity_is_sent(client):
    fake = FakeModel([json.dumps(VALID_MODEL)])
    use_model(fake)
    activity = [
        {"kind": "internal", "body": f"note-{index}", "at": "2026-10-01T00:00:00.000Z"}
        for index in range(12)
    ]
    client.post("/api/analyze-ticket", json=ticket(activity=activity))
    user = fake.calls[0]["messages"][1]["content"]
    data = json.loads(user.split("\n\n", 1)[1])
    assert data["omittedEarlierActivityCount"] == 2
    assert [item["body"] for item in data["activity"]] == [f"note-{index}" for index in range(2, 12)]
    assert "note-0" not in user
    assert "note-11" in user


def test_requests_do_not_share_ticket_text(client):
    fake = FakeModel([json.dumps(VALID_MODEL), json.dumps(VALID_MODEL)])
    use_model(fake)
    client.post("/api/analyze-ticket", json=ticket(subject="SUBJECT_ALPHA_UNIQUE"))
    client.post("/api/analyze-ticket", json=ticket(id="TD-2402", subject="SUBJECT_BETA_UNIQUE"))
    first = fake.calls[0]["messages"][1]["content"]
    second = fake.calls[1]["messages"][1]["content"]
    assert "SUBJECT_ALPHA_UNIQUE" in first
    assert "SUBJECT_ALPHA_UNIQUE" not in second
    assert "SUBJECT_BETA_UNIQUE" in second
    assert len(fake.calls[1]["messages"]) == 2


def test_disallowed_category_is_rejected(client):
    payload = dict(VALID_MODEL)
    payload["suggestedCategory"] = "Printing"
    fake = FakeModel([json.dumps(payload)])
    use_model(fake)
    response = client.post("/api/analyze-ticket", json=ticket(description=SECRET))
    body = response.json()
    assert response.status_code == 200
    assert body["available"] is False
    assert "could not use" in body["message"]
    assert "summary" not in body
    assert "Printing" not in response.text
    assert SECRET not in response.text


def test_invalid_json_is_rejected(client, caplog):
    fake = FakeModel(["this is not json"])
    use_model(fake)
    with caplog.at_level(logging.WARNING, logger="tinydesk.analysis"):
        response = client.post("/api/analyze-ticket", json=ticket(description=SECRET))
    body = response.json()
    assert body["available"] is False
    assert "could not use" in body["message"]
    assert SECRET not in caplog.text
    assert "TD-2401" in caplog.text
    assert "invalid_output" in caplog.text


def test_blank_summary_is_rejected(client):
    payload = dict(VALID_MODEL)
    payload["summary"] = "   "
    fake = FakeModel([json.dumps(payload)])
    use_model(fake)
    response = client.post("/api/analyze-ticket", json=ticket())
    assert response.json()["available"] is False


def test_empty_followups_are_allowed(client):
    payload = dict(VALID_MODEL)
    payload["followUps"] = ["  ", "Which printer name is selected?"]
    fake = FakeModel([json.dumps(payload)])
    use_model(fake)
    response = client.post("/api/analyze-ticket", json=ticket())
    assert response.json()["followUps"] == ["Which printer name is selected?"]


@pytest.mark.parametrize(
    ("reason", "snippet"),
    [
        ("unavailable", "could not reach the local model"),
        ("timeout", "took too long"),
        ("model_missing", "model is not available"),
        ("bad_response", "unexpected response"),
    ],
)
def test_backend_failures_are_visible(client, caplog, reason, snippet):
    fake = FakeModel([ModelCallError(reason, "ConnectError", 404 if reason == "model_missing" else None)])
    use_model(fake)
    with caplog.at_level(logging.WARNING, logger="tinydesk.analysis"):
        response = client.post("/api/analyze-ticket", json=ticket(description=SECRET))
    body = response.json()
    assert response.status_code == 200
    assert body["available"] is False
    assert snippet in body["message"]
    assert SECRET not in response.text
    assert SECRET not in caplog.text
    assert reason in caplog.text


def test_unexpected_model_error_does_not_echo_ticket_text(client, caplog):
    fake = FakeModel([RuntimeError(SECRET)])
    use_model(fake)
    with caplog.at_level(logging.ERROR, logger="tinydesk"):
        response = client.post("/api/analyze-ticket", json=ticket(description=SECRET))
    assert response.json()["available"] is False
    assert "could not be completed" in response.json()["message"]
    assert SECRET not in response.text
    assert SECRET not in caplog.text
    assert "unhandled" in caplog.text


def test_missing_subject_is_a_validation_error(client, caplog):
    with caplog.at_level(logging.WARNING, logger="tinydesk"):
        response = client.post(
            "/api/analyze-ticket",
            json=ticket(subject="   ", description=SECRET),
        )
    body = response.json()
    assert response.status_code == 422
    assert body["available"] is False
    assert "subject" in body["message"]
    assert SECRET not in response.text
    assert SECRET not in caplog.text


def test_unknown_category_is_a_validation_error(client):
    response = client.post("/api/analyze-ticket", json=ticket(category="Printing"))
    assert response.status_code == 422
    assert response.json()["available"] is False
    assert "category" in response.json()["message"]


def test_oversized_description_is_rejected(client):
    response = client.post("/api/analyze-ticket", json=ticket(description="x" * 5001))
    assert response.status_code == 422
    assert "description" in response.json()["message"]


def test_request_over_the_byte_limit_is_rejected(client):
    raw = b'{"description":"' + (b"x" * 200_000) + b'"}'
    response = client.post(
        "/api/analyze-ticket",
        content=raw,
        headers={"content-type": "application/json"},
    )
    assert response.status_code == 413
    assert response.json()["available"] is False
    assert "too large" in response.json()["message"]


def test_get_is_not_allowed(client):
    response = client.get("/api/analyze-ticket")
    assert response.status_code == 405


def test_configured_model_is_used(client, monkeypatch):
    monkeypatch.setenv("OLLAMA_MODEL", "custom-model")
    monkeypatch.setenv("OLLAMA_TIMEOUT_SECONDS", "33")
    fake = FakeModel([json.dumps(VALID_MODEL)])
    use_model(fake)
    client.post("/api/analyze-ticket", json=ticket())
    assert fake.calls[0]["model"] == "custom-model"
    assert fake.calls[0]["timeout"] == 33


def test_categories_match_the_frontend_store():
    text = (ROOT / "js" / "store.js").read_text(encoding="utf-8")

    def grab(name):
        match = re.search(rf"export const {name} = \[(.*?)\];", text, re.DOTALL)
        assert match, name
        return re.findall(r'"([^"]+)"', match.group(1))

    assert grab("CATEGORIES") == list(CATEGORIES)
    assert grab("PRIORITIES") == list(PRIORITIES)
    assert grab("STATUSES") == list(STATUSES)


def test_frontend_is_served_and_backend_files_are_not(client):
    index = client.get("/")
    assert index.status_code == 200
    assert "text/html" in index.headers["content-type"]
    assert "Local AI" in index.text
    assert "Prepared sample" not in index.text

    script = client.get("/js/analysis.js")
    assert script.status_code == 200
    assert "/api/analyze-ticket" in script.text
    assert "SAMPLES" not in script.text

    assert client.get("/css/styles.css").status_code == 200
    assert client.get("/favicon.svg").status_code == 200
    assert client.get("/requirements.txt").status_code == 404
    assert client.get("/backend/app.py").status_code == 404
    assert client.get("/.env").status_code == 404
    assert client.get("/docs").status_code == 404
    assert client.get("/js/../requirements.txt").status_code == 404
