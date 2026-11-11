"""The live path for a dedicated translation model: pick the version the recognizers agree on, rate clarity by
their agreement, and never call a real sentence "(unclear)" just because the recognizers differed."""
import asyncio

import translation


def test_the_version_most_recognizers_wrote_wins():
    said, distance = translation.most_agreed_version(["你食咗飯未呀", "你食咗飯未呀", "你食咗飯味呀"])
    assert said == "你食咗飯未呀" and distance == 0.0


def test_ties_go_to_the_first_recognizer():
    said, distance = translation.most_agreed_version(["你好嗎", "你號碼"])
    assert said == "你好嗎" and distance > 0.5


def test_punctuation_does_not_count_as_disagreement():
    _, distance = translation.most_agreed_version(["好呀，食飯啦。", "好呀食飯啦"])
    assert distance == 0.0


def test_clarity_follows_agreement():
    assert translation.clarity_from_agreement(0.0) == 5
    assert translation.clarity_from_agreement(0.1) == 4
    assert translation.clarity_from_agreement(0.6) == 3
    assert translation.clarity_from_agreement(None) == 4


def fake_translator(english):
    async def translate(text, source, target, provider, earlier_lines=(), options=None):
        translate.seen = (text, list(earlier_lines))
        return english
    return translate


def test_disagreeing_recognizers_still_get_a_translation(monkeypatch):
    translator = fake_translator("How are you?")
    monkeypatch.setattr(translation, "translate_with_translation_model", translator)
    monkeypatch.setattr(translation, "choose_provider", lambda source, target: "ollama:hy-mt1.5:1.8b")
    result = asyncio.run(translation.understand_line(["你好嗎", "你號碼"], "yue", "en", ["食飯啦 (meaning: Let's eat)"]))
    assert result == {"said": "你好嗎", "english": "How are you?", "clarity": 3, "unclear": False}
    assert translator.seen == ("你好嗎", [])  # earlier lines are not given to the translation model


def test_earlier_lines_go_in_as_plain_text_when_switched_on(monkeypatch):
    translator = fake_translator("How are you?")
    monkeypatch.setattr(translation, "translate_with_translation_model", translator)
    monkeypatch.setattr(translation, "choose_provider", lambda source, target: "ollama:hy-mt1.5:1.8b")
    monkeypatch.setattr(translation, "TRANSLATION_MODEL_CONTEXT_LINES", 4)
    asyncio.run(translation.understand_line(["你好嗎"], "yue", "en", ["食飯啦 (meaning: Let's eat)"]))
    assert translator.seen == ("你好嗎", ["食飯啦"])


def test_a_translation_that_is_still_chinese_is_unclear(monkeypatch):
    monkeypatch.setattr(translation, "translate_with_translation_model", fake_translator("鞋的韵母是 ai"))
    monkeypatch.setattr(translation, "choose_provider", lambda source, target: "ollama:hy-mt1.5:1.8b")
    result = asyncio.run(translation.understand_line(["鞋嘅韻母係 ai"], "yue", "en"))
    assert result["unclear"] and result["english"] == "(unclear)"


def test_a_translation_may_quote_a_character(monkeypatch):
    english = "The rhyme of the character “夏” is “a”."
    monkeypatch.setattr(translation, "translate_with_translation_model", fake_translator(english))
    monkeypatch.setattr(translation, "choose_provider", lambda source, target: "ollama:hy-mt1.5:1.8b")
    result = asyncio.run(translation.understand_line(["夏字嘅韻母係 a"], "yue", "en"))
    assert not result["unclear"] and result["english"] == english


def test_writing_jobs_never_go_to_the_translation_model(tmp_path, monkeypatch):
    router = tmp_path / "router.json"
    monkeypatch.setattr(translation, "ROUTER_FILE", str(router))
    router.write_text('{"*>*": "ollama:hy-mt1.5:1.8b", "chat": "ollama:qwen2.5:7b"}')
    assert translation.chat_model() == "qwen2.5:7b"
    router.write_text('{"*>*": "ollama:hy-mt1.5:1.8b"}')
    assert translation.chat_model() == translation.FALLBACK_PROVIDER.split(":", 1)[-1]
    router.write_text('{"*>*": "ollama:qwen2.5:7b"}')
    assert translation.chat_model() == "qwen2.5:7b"
