import json
import logging
import re
from pathlib import Path

import pytest

from backend.analysis import (
    PROMPT_TOKEN_BUDGET,
    SHORTENED_MARK,
    build_model_payload,
    estimate_tokens,
    system_prompt,
    user_message,
)
from backend.app import app, get_model_client
from backend.ollama_client import ModelCallError
from backend.schemas import (
    CATEGORIES,
    MODEL_TEXT_LIMIT,
    PRIORITIES,
    RECENT_ACTIVITY_LIMIT,
    STATUSES,
    TicketRequest,
)

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
    assert "resource is unspecified" in system
    assert "Ticket status" in system
    assert "at most 3 followUps" in system
    assert "Do not promise a resolution time" in system
    assert "approved or granted" in system
    assert "unspecified" in user
    assert "ticket status" in user.lower()
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
        ("context_limit", "exceeds its context window"),
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


def test_capped_xai_response_is_an_error_without_partial_fields(client, monkeypatch):
    monkeypatch.setenv("TINYDESK_AI_PROVIDER", "xai")
    monkeypatch.delenv("XAI_REASONING_EFFORT", raising=False)
    monkeypatch.delenv("XAI_MAX_COMPLETION_TOKENS", raising=False)
    fake = FakeModel([ModelCallError("output_capped", "LengthFinish", 200)])
    use_model(fake)
    response = client.post("/api/analyze-ticket", json=ticket(description=SECRET))
    body = response.json()
    assert response.status_code == 200
    assert body["available"] is False
    assert body["message"] == (
        "The xAI response was cut off before the analysis finished. "
        "TinyDesk did not show a partial result."
    )
    assert "summary" not in body
    assert "suggestedCategory" not in body
    assert "followUps" not in body
    assert "draft" not in body
    assert SECRET not in response.text


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


def test_context_limit_failure_keeps_the_configured_model(client, monkeypatch):
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)
    fake = FakeModel([ModelCallError("context_limit", "ResponseError", 400)])
    use_model(fake)
    response = client.post("/api/analyze-ticket", json=ticket(description=SECRET))
    body = response.json()
    assert response.status_code == 200
    assert body["available"] is False
    assert "context window" in body["message"]
    assert "unexpected response" not in body["message"]
    assert "switch models" in body["message"]
    assert SECRET not in response.text
    assert len(fake.calls) == 1
    assert fake.calls[0]["model"] == "qwen3:4b-instruct-2507-q4_K_M"


def test_configured_model_is_used(client, monkeypatch):
    monkeypatch.setenv("OLLAMA_MODEL", "custom-model")
    monkeypatch.setenv("OLLAMA_TIMEOUT_SECONDS", "33")
    fake = FakeModel([json.dumps(VALID_MODEL)])
    use_model(fake)
    client.post("/api/analyze-ticket", json=ticket())
    assert fake.calls[0]["model"] == "custom-model"
    assert fake.calls[0]["timeout"] == 33


def test_assistant_metadata_names_local_ollama_without_secrets(client, monkeypatch):
    monkeypatch.delenv("TINYDESK_AI_PROVIDER", raising=False)
    monkeypatch.setenv("XAI_API_KEY", "test-key")
    response = client.get("/api/assistant")
    assert response.status_code == 200
    assert response.json() == {
        "provider": "ollama",
        "placement": "local",
        "product": "Ollama",
        "sendsTicketToProvider": False,
    }
    assert "test-key" not in response.text
    assert "Authorization" not in response.text


def test_assistant_metadata_names_cloud_xai_without_secrets(client, monkeypatch):
    monkeypatch.setenv("TINYDESK_AI_PROVIDER", "xai")
    monkeypatch.setenv("XAI_API_KEY", "test-key")
    monkeypatch.setenv("XAI_MODEL", "grok-4.7")
    response = client.get("/api/assistant")
    body = response.json()
    assert body == {
        "provider": "xai",
        "placement": "cloud",
        "product": "xAI Grok",
        "sendsTicketToProvider": True,
    }
    assert set(body) == {"provider", "placement", "product", "sendsTicketToProvider"}
    assert "test-key" not in response.text
    assert "grok-4.7" not in response.text


def test_unrecognized_provider_is_not_described_as_local(client, monkeypatch):
    monkeypatch.setenv("TINYDESK_AI_PROVIDER", "other")
    body = client.get("/api/assistant").json()
    assert body["provider"] == "unrecognized"
    assert body["placement"] == "unknown"
    assert body["product"] == ""
    assert body["sendsTicketToProvider"] is False
    assert "other" not in json.dumps(body)


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
    assert 'id="assist-provider"' in index.text
    assert "local model on this computer" not in index.text
    assert "Prepared sample" not in index.text
    app_js = client.get("/js/app.js")
    assert app_js.status_code == 200
    assert "Local Ollama" in app_js.text
    assert "Cloud xAI Grok" in app_js.text
    assert "sends this ticket's information to xAI" in app_js.text

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


def test_local_config_file_is_not_served(client):
    from backend.app import request_targets_local_config

    assert request_targets_local_config("/.env")
    assert request_targets_local_config("/.env/")
    assert request_targets_local_config("/css/../.env")
    assert request_targets_local_config("/js/../.env")
    assert request_targets_local_config("/%2eenv")
    assert request_targets_local_config("/css/%2e%2e/.env")
    assert not request_targets_local_config("/")
    assert not request_targets_local_config("/css/styles.css")
    assert not request_targets_local_config("/js/app.js")

    for path in ("/.env", "/.env/", "/css/../.env", "/js/../.env", "/%2eenv"):
        response = client.get(path)
        assert response.status_code == 404
        assert "XAI_API_KEY" not in response.text
        assert response.json() == {"detail": "Not Found"}


def sent_payload(fake):
    user = fake.calls[0]["messages"][1]["content"]
    return json.loads(user.split("\n\n", 1)[1]), user


def test_more_than_30_activity_entries_stay_analyzable(client):
    activity = [
        {"kind": "internal", "body": f"history-{index}", "at": "2026-10-01T00:00:00.000Z"}
        for index in range(31)
    ]
    fake = FakeModel([json.dumps(VALID_MODEL)])
    use_model(fake)
    response = client.post("/api/analyze-ticket", json=ticket(activity=activity))
    assert response.status_code == 200
    assert response.json()["available"] is True
    data, user = sent_payload(fake)
    assert data["omittedEarlierActivityCount"] == 31 - RECENT_ACTIVITY_LIMIT
    assert [item["body"] for item in data["activity"]] == [
        f"history-{index}" for index in range(31 - RECENT_ACTIVITY_LIMIT, 31)
    ]
    assert "history-0" not in user
    assert "history-30" in user


def test_activity_note_longer_than_4000_characters_is_shortened(client):
    body = "A" * (MODEL_TEXT_LIMIT + 1)
    fake = FakeModel([json.dumps(VALID_MODEL)])
    use_model(fake)
    response = client.post(
        "/api/analyze-ticket",
        json=ticket(
            activity=[{"kind": "internal", "body": body, "at": "2026-10-01T00:00:00.000Z"}]
        ),
    )
    assert response.status_code == 200
    assert response.json()["available"] is True
    data, user = sent_payload(fake)
    sent_body = data["activity"][0]["body"]
    assert sent_body.endswith(SHORTENED_MARK)
    assert len(sent_body) <= MODEL_TEXT_LIMIT
    assert body not in user
    assert sent_body[:20] == body[:20]


def test_prefixed_resolution_activity_keeps_the_resolution_note(client):
    note = "R" * MODEL_TEXT_LIMIT
    prefix = "Status changed from In Progress to Resolved. Resolution: "
    body = prefix + note
    assert len(note) == MODEL_TEXT_LIMIT
    assert len(body) > MODEL_TEXT_LIMIT
    fake = FakeModel([json.dumps(VALID_MODEL)])
    use_model(fake)
    response = client.post(
        "/api/analyze-ticket",
        json=ticket(
            status="Resolved",
            resolutionNote=note,
            activity=[
                {"kind": "status", "body": body, "at": "2026-10-01T00:00:00.000Z"}
            ],
        ),
    )
    assert response.status_code == 200
    assert response.json()["available"] is True
    data, user = sent_payload(fake)
    sent_body = data["activity"][0]["body"]
    sent_note = data["currentFields"]["resolutionNote"]
    assert sent_note.startswith(note[:20])
    assert sent_note.endswith(SHORTENED_MARK)
    assert sent_note != note
    assert sent_body.startswith(prefix)
    assert sent_body.endswith(SHORTENED_MARK)
    assert len(sent_body) <= MODEL_TEXT_LIMIT
    assert body not in user
    assert note not in user
    assert sent_note in user
    assert estimate_tokens(system_prompt() + "\n" + user) <= PROMPT_TOKEN_BUDGET


def test_analysis_preparation_does_not_change_the_saved_ticket():
    note = "R" * MODEL_TEXT_LIMIT
    long_note = "L" * (MODEL_TEXT_LIMIT + 50)
    prefix = "Status changed from Waiting on User to Resolved. Resolution: "
    activity = [
        {"kind": "internal", "body": f"history-{index}", "at": "2026-10-01T00:00:00.000Z"}
        for index in range(31)
    ]
    activity.append(
        {
            "kind": "internal",
            "body": long_note,
            "at": "2026-10-01T00:00:01.000Z",
        }
    )
    activity.append(
        {
            "kind": "status",
            "body": prefix + note,
            "at": "2026-10-01T00:00:02.000Z",
        }
    )
    saved = ticket(status="Resolved", resolutionNote=note, activity=activity)
    model = TicketRequest.model_validate(saved)
    before = model.model_dump()
    prepared = build_model_payload(model)
    message = user_message(model)
    assert model.model_dump() == before
    assert model.resolutionNote == note
    assert model.activity[-1].body == prefix + note
    assert model.activity[-2].body == long_note
    assert len(model.activity) == 33
    sent_note = prepared["currentFields"]["resolutionNote"]
    assert sent_note.startswith(note[:20])
    assert sent_note.endswith(SHORTENED_MARK)
    assert prepared["activity"][-1]["body"].startswith(prefix)
    assert prepared["activity"][-1]["body"].endswith(SHORTENED_MARK)
    assert prepared["activity"][-2]["body"].endswith(SHORTENED_MARK)
    assert prepared["omittedEarlierActivityCount"] >= 33 - RECENT_ACTIVITY_LIMIT
    assert prefix + note not in message
    assert note not in message
    assert sent_note in message
    assert estimate_tokens(system_prompt() + "\n" + message) <= PROMPT_TOKEN_BUDGET


def test_ordinary_history_fits_without_shortening():
    sentence = "The VPN client stops at the gateway after the laptop wakes. "
    note = (sentence * 20)[:400]
    description = (sentence * 40)[:1500]
    activity = [
        {"kind": "internal", "body": note, "at": "2026-10-01T00:00:00.000Z"}
        for _ in range(10)
    ]
    model = TicketRequest.model_validate(
        ticket(description=description, activity=activity)
    )
    before = model.model_dump()
    prepared = build_model_payload(model)
    message = user_message(model)
    assert model.model_dump() == before
    assert prepared["description"] == model.description
    assert [item["body"] for item in prepared["activity"]] == [item.body for item in model.activity]
    assert len(prepared["activity"]) == 10
    assert prepared["omittedEarlierActivityCount"] == 0
    assert SHORTENED_MARK not in message.split("\n\n", 1)[1]
    assert estimate_tokens(system_prompt() + "\n" + message) <= PROMPT_TOKEN_BUDGET


def test_token_dense_input_stays_inside_the_combined_budget():
    note = "R" * MODEL_TEXT_LIMIT
    description = "R" * 5000
    prefix = "Status changed from In Progress to Resolved. Resolution: "
    activity = [
        {"kind": "internal", "body": f"history-{index}", "at": "2026-10-01T00:00:00.000Z"}
        for index in range(30)
    ]
    activity.extend(
        {
            "kind": "internal",
            "body": "R" * MODEL_TEXT_LIMIT,
            "at": "2026-10-01T00:01:00.000Z",
        }
        for _ in range(9)
    )
    activity.append(
        {"kind": "status", "body": prefix + note, "at": "2026-10-01T00:02:00.000Z"}
    )
    saved = ticket(
        subject="Token dense ticket",
        description=description,
        status="Resolved",
        resolutionNote=note,
        activity=activity,
    )
    model = TicketRequest.model_validate(saved)
    before = model.model_dump()
    prepared = build_model_payload(model)
    message = user_message(model)
    assert model.model_dump() == before
    assert model.resolutionNote == note
    assert len(model.activity) == len(activity)
    assert prepared["subject"] == "Token dense ticket"
    assert prepared["currentFields"]["status"] == "Resolved"
    assert prepared["currentFields"]["category"] == "Network"
    sent_note = prepared["currentFields"]["resolutionNote"]
    assert sent_note.startswith("RRRR")
    assert sent_note.endswith(SHORTENED_MARK)
    assert description not in message
    assert note not in message
    assert "omittedEarlierActivityCount" in message
    assert prepared["omittedEarlierActivityCount"] >= len(activity) - RECENT_ACTIVITY_LIMIT
    assert estimate_tokens(system_prompt() + "\n" + message) <= PROMPT_TOKEN_BUDGET
    if prepared["activity"]:
        assert prepared["activity"][-1]["body"].startswith(prefix)
        assert prepared["activity"][-1]["body"].endswith(SHORTENED_MARK)
