"""Accounts, per-person conversations, and request guards, tested through the real HTTP API (no GPU needed)."""
import importlib
import secrets
import os
import sys

import pytest
from fastapi.testclient import TestClient

ALLOWED_ORIGIN = "https://jakesauter.github.io"
# Test passwords are generated per run, so no credential-looking literals live in the repository.
TEST_PASSWORD = "t-" + secrets.token_urlsafe(12)
OTHER_PASSWORD = "t-" + secrets.token_urlsafe(12)
WRONG_PASSWORD = "t-" + secrets.token_urlsafe(12)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("POLYLANG_DATA", str(tmp_path))
    monkeypatch.setenv("POLYLANG_PRELOAD", "")
    monkeypatch.setenv("POLYLANG_SITE", str(tmp_path / "no-site"))
    monkeypatch.setenv("POLYLANG_EMAIL_OUTBOX", str(tmp_path / "outbox"))
    for module in ("accounts", "conversations", "email_sender", "inference_server"):
        sys.modules.pop(module, None)
    server = importlib.import_module("inference_server")
    with TestClient(server.app) as test_client:
        yield test_client


def create(client, username, password=None, device_id=""):
    password = password or TEST_PASSWORD
    return client.post("/account/create", json={"username": username, "password": password, "device_id": device_id})


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_create_sign_in_and_wrong_password(client):
    assert create(client, "jake").status_code == 200
    assert create(client, "jake").json()["error"] == "That username is taken."
    assert client.post("/account/sign-in", json={"username": "jake", "password": WRONG_PASSWORD}).status_code == 401
    signed_in = client.post("/account/sign-in", json={"username": "JAKE", "password": TEST_PASSWORD}).json()
    assert client.get("/account", headers=auth(signed_in["token"])).json()["username"] == "jake"


def test_short_password_and_bad_username_rejected(client):
    assert create(client, "ok_name", "short").status_code == 400
    assert create(client, "../../etc").status_code == 400


def test_repeated_wrong_passwords_lock_out(client):
    create(client, "victim")
    for _ in range(8):
        client.post("/account/sign-in", json={"username": "victim", "password": WRONG_PASSWORD})
    locked = client.post("/account/sign-in", json={"username": "victim", "password": TEST_PASSWORD})
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


def last_email(client_tmp_outbox):
    import glob, json
    files = sorted(glob.glob(os.path.join(client_tmp_outbox, "*.json")))
    return json.load(open(files[-1])) if files else None


def outbox_folder():
    return os.environ["POLYLANG_EMAIL_OUTBOX"]


def test_forgot_password_full_flow(client):
    old_token = client.post("/account/create", json={"username": "forgetful", "password": TEST_PASSWORD, "email": "Me@Example.com"}).json()["token"]
    reply = client.post("/account/forgot-password", json={"email": "me@example.com"})
    assert reply.status_code == 200
    email = last_email(outbox_folder())
    assert email["to"] == "me@example.com"
    code = email["subject"].split()[-1]
    assert len(code) == 6 and code.isdigit()
    reset = client.post("/account/reset-password", json={"email": "me@example.com", "code": code, "password": OTHER_PASSWORD})
    assert reset.status_code == 200 and reset.json()["username"] == "forgetful"
    assert client.get("/account", headers=auth(old_token)).json()["signed_in"] is False  # other devices signed out
    assert client.post("/account/sign-in", json={"username": "forgetful", "password": OTHER_PASSWORD}).status_code == 200
    reused = client.post("/account/reset-password", json={"email": "me@example.com", "code": code, "password": WRONG_PASSWORD})
    assert reused.status_code == 400  # codes are single-use


def test_forgot_password_does_not_reveal_accounts(client):
    unknown = client.post("/account/forgot-password", json={"email": "nobody@example.com"})
    client.post("/account/create", json={"username": "someone", "password": TEST_PASSWORD, "email": "someone@example.com"})
    known = client.post("/account/forgot-password", json={"email": "someone@example.com"})
    assert unknown.status_code == known.status_code == 200
    assert unknown.json() == known.json()


def test_reset_code_locks_after_five_wrong_tries(client):
    client.post("/account/create", json={"username": "guessme", "password": TEST_PASSWORD, "email": "guess@example.com"})
    client.post("/account/forgot-password", json={"email": "guess@example.com"})
    real_code = last_email(outbox_folder())["subject"].split()[-1]
    wrong_code = f"{(int(real_code) + 1) % 1000000:06d}"
    for _ in range(5):
        client.post("/account/reset-password", json={"email": "guess@example.com", "code": wrong_code, "password": OTHER_PASSWORD})
    locked = client.post("/account/reset-password", json={"email": "guess@example.com", "code": real_code, "password": OTHER_PASSWORD})
    assert locked.status_code == 400


def test_bad_email_rejected_and_email_can_be_added_later(client):
    assert create(client, "bademail").status_code == 200
    assert client.post("/account/create", json={"username": "x_bad", "password": TEST_PASSWORD, "email": "not-an-email"}).status_code == 400
    token = create(client, "addlater").json()["token"]
    assert client.post("/account/email", json={"email": "later@example.com"}, headers=auth(token)).json()["email"] == "later@example.com"
    assert client.get("/account", headers=auth(token)).json()["email"] == "later@example.com"


def test_trusted_reset_is_off(client):
    create(client, "trusting")
    assert client.post("/account/reset-password-trusted", json={"username": "trusting", "password": OTHER_PASSWORD}).status_code == 400


def test_recovery_code_reset_full_flow(client):
    created = create(client, "careful").json()
    code = created["recovery_code"]
    assert len(code) == 14 and code.count("-") == 2
    reset = client.post("/account/reset-with-recovery-code",
                        json={"username": "careful", "recovery_code": code.lower().replace("-", " "), "password": OTHER_PASSWORD})
    assert reset.status_code == 200
    assert reset.json()["recovery_code"] != code  # a fresh code replaces the used one
    assert client.get("/account", headers=auth(created["token"])).json()["signed_in"] is False
    again = client.post("/account/reset-with-recovery-code", json={"username": "careful", "recovery_code": code, "password": WRONG_PASSWORD})
    assert again.status_code == 400  # used codes stop working
    assert client.post("/account/sign-in", json={"username": "careful", "password": OTHER_PASSWORD}).status_code == 200


def test_recovery_code_guessing_is_limited(client):
    real_code = create(client, "guarded").json()["recovery_code"]
    for _ in range(5):
        client.post("/account/reset-with-recovery-code", json={"username": "guarded", "recovery_code": "AAAA-BBBB-CCCC", "password": OTHER_PASSWORD})
    blocked = client.post("/account/reset-with-recovery-code", json={"username": "guarded", "recovery_code": real_code, "password": OTHER_PASSWORD})
    assert blocked.status_code == 400 and "Too many tries" in blocked.json()["error"]
