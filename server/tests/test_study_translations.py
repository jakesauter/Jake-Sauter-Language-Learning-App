"""English lines shown in the language being learned: the pronoun clean-up and the cached saved-conversation endpoint."""
import asyncio
import importlib
import sys

import pytest
from fastapi.testclient import TestClient

import translation

ALLOWED_ORIGIN = "https://jakesauter.github.io"


def test_mandarin_pronouns_become_spoken_cantonese():
    assert translation.spoken_cantonese_pronouns("她只要一條手杖") == "佢只要一條手杖"
    assert translation.spoken_cantonese_pronouns("他們去咗邊") == "佢哋去咗邊"
    assert translation.spoken_cantonese_pronouns("我們走啦，你們呢") == "我哋走啦，你哋呢"
    assert translation.spoken_cantonese_pronouns("其他人都嚟") == "其他人都嚟"  # "other" is left alone


def test_taishanese_learners_get_cantonese(monkeypatch):
    asked = []

    async def translator(text, source, target, provider, earlier_lines=(), options=None):
        asked.append((source, target))
        return "她買咗"

    monkeypatch.setattr(translation, "translate_with_translation_model", translator)
    monkeypatch.setattr(translation, "choose_provider", lambda source, target: "ollama:hy-mt1.5:1.8b")
    result = asyncio.run(translation.to_study_language("She bought it", "tsn"))
    assert asked == [("en", "yue")]
    assert result == {"text": "佢買咗", "language": "yue"}


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
        yield test_client, server


def test_saved_conversation_english_lines_are_translated_once(client, monkeypatch):
    test_client, server = client
    calls = []

    async def fake_study(text, language):
        calls.append(text)
        return {"text": "譯：" + text, "language": "yue"}

    monkeypatch.setattr(server.translation, "to_study_language", fake_study)
    headers = {"Origin": ALLOWED_ORIGIN, "X-Polylang-Device": "device-study-test"}
    conversation = test_client.post("/conversations", json={"title": "Dinner", "languages": ["yue", "en"]}, headers=headers).json()
    url = f"/conversations/{conversation['id']}/study"
    first = test_client.post(url, json={"language": "tsn", "texts": ["Hello", "Hello", "Should I buy it?"]}, headers=headers).json()
    assert first == {"language": "yue", "translations": {"Hello": "譯：Hello", "Should I buy it?": "譯：Should I buy it?"}}
    again = test_client.post(url, json={"language": "yue", "texts": ["Hello"]}, headers=headers).json()
    assert again["translations"] == {"Hello": "譯：Hello"}
    assert calls == ["Hello", "Should I buy it?"]  # the second request came from the cache


def test_study_needs_an_existing_conversation(client):
    test_client, _ = client
    response = test_client.post("/conversations/nope/study", json={"language": "yue", "texts": ["Hi"]},
                                headers={"Origin": ALLOWED_ORIGIN, "X-Polylang-Device": "device-study-test"})
    assert response.status_code == 404
