"""Accounts, per-person conversations, and request guards, tested through the real HTTP API (no GPU needed)."""
import importlib
import os
import sys

import pytest
from fastapi.testclient import TestClient

ALLOWED_ORIGIN = "https://jakesauter.github.io"


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("POLYLANG_DATA", str(tmp_path))
    monkeypatch.setenv("POLYLANG_PRELOAD", "")
    monkeypatch.setenv("POLYLANG_SITE", str(tmp_path / "no-site"))
    for module in ("accounts", "conversations", "inference_server"):
        sys.modules.pop(module, None)
    server = importlib.import_module("inference_server")
    with TestClient(server.app) as test_client:
        yield test_client


def create(client, username, password="correct horse battery", device_id=""):
    return client.post("/account/create", json={"username": username, "password": password, "device_id": device_id})


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_create_sign_in_and_wrong_password(client):
    assert create(client, "jake").status_code == 200
    assert create(client, "jake").json()["error"] == "That username is taken."
    assert client.post("/account/sign-in", json={"username": "jake", "password": "nope nope"}).status_code == 401
    signed_in = client.post("/account/sign-in", json={"username": "JAKE", "password": "correct horse battery"}).json()
    assert client.get("/account", headers=auth(signed_in["token"])).json()["username"] == "jake"


def test_short_password_and_bad_username_rejected(client):
    assert create(client, "ok_name", "short").status_code == 400
    assert create(client, "../../etc").status_code == 400


def test_repeated_wrong_passwords_lock_out(client):
    create(client, "victim")
    for _ in range(8):
        client.post("/account/sign-in", json={"username": "victim", "password": "wrong guess"})
    locked = client.post("/account/sign-in", json={"username": "victim", "password": "correct horse battery"})
    assert locked.status_code == 401 and "Too many tries" in locked.json()["error"]


def test_conversations_are_private_per_account(client):
    alice = create(client, "alice").json()["token"]
    bob = create(client, "bob").json()["token"]
    conversation = client.post("/conversations", json={"title": "Dinner"}, headers=auth(alice)).json()
    assert [c["title"] for c in client.get("/conversations", headers=auth(alice)).json()["conversations"]] == ["Dinner"]
    assert client.get("/conversations", headers=auth(bob)).json()["conversations"] == []
    assert client.get(f"/conversations/{conversation['id']}", headers=auth(bob)).status_code == 404


def test_guest_conversations_move_into_new_account(client):
    device = {"X-Polylang-Device": "device-0123456789abcdef"}
    client.post("/conversations", json={"title": "Before signing up"}, headers=device)
    signed_up = create(client, "newperson", device_id="device-0123456789abcdef").json()
    assert signed_up["moved_conversations"] == 1
    titles = [c["title"] for c in client.get("/conversations", headers=auth(signed_up["token"])).json()["conversations"]]
    assert titles == ["Before signing up"]


def test_signed_out_token_stops_working(client):
    token = create(client, "leaving").json()["token"]
    client.post("/account/sign-out", headers=auth(token))
    assert client.get("/account", headers=auth(token)).json()["signed_in"] is False


def test_conversation_id_cannot_escape_data_folder(client):
    for bad_id in ("..%2F..%2Fetc", "....////", "a" * 64):
        assert client.get(f"/conversations/{bad_id}").status_code in (404, 400)


def test_other_websites_cannot_post(client):
    blocked = client.post("/conversations", json={"title": "x"}, headers={"Origin": "https://evil.example.com"})
    assert blocked.status_code == 403
    allowed = client.post("/conversations", json={"title": "x"}, headers={"Origin": ALLOWED_ORIGIN})
    assert allowed.status_code == 200 and allowed.headers["access-control-allow-origin"] == ALLOWED_ORIGIN


def test_live_ticket_is_single_use(client):
    import accounts
    token = create(client, "ticketuser").json()["token"]
    ticket = client.post("/live/ticket", headers=auth(token)).json()["ticket"]
    assert accounts.redeem_live_ticket(ticket).startswith("account:")
    assert accounts.redeem_live_ticket(ticket) is None
