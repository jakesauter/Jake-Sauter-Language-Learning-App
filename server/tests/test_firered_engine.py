"""FireRed is handed audio as 16-bit sample values, and its answer comes back as plain text."""
import numpy as np

import speech_engines


class FakeFireRed:
    def transcribe(self, names, audios):
        self.seen = audios
        return [{"uttid": names[0], "text": " 食咗飯未 "}]


def test_firered_gets_16_bit_samples_and_returns_plain_text():
    model = FakeFireRed()
    audio = np.array([0.0, 0.5, -1.0], dtype=np.float32)
    text, words, detected_language = speech_engines.run_firered(model, audio)
    sample_rate, samples = model.seen[0]
    assert sample_rate == 16000 and samples.tolist() == [0.0, 16384.0, -32768.0]
    assert (text, words, detected_language) == ("食咗飯未", [], None)


def test_english_from_firered_gets_capitals():
    assert speech_engines.tidy_english("i think i'm late, is it okay") == "I think I'm late, is it okay"
    assert speech_engines.tidy_english("hi there") == "Hi there"  # the "i" inside a word is left alone


def test_punctuation_keeps_spaces_around_english(monkeypatch):
    class FakePunctuation:
        def process(self, texts):
            return [{"punc_text": "跟住係call，但係call冇中文字。"}]
    monkeypatch.setattr(speech_engines, "get_engine", lambda name: FakePunctuation())
    assert speech_engines.add_punctuation("跟住係 call但係 call冇中文字") == "跟住係 call，但係 call 冇中文字。"


def test_no_punctuation_model_leaves_text_alone(monkeypatch):
    monkeypatch.setattr(speech_engines, "get_engine", lambda name: None)
    assert speech_engines.add_punctuation("你好") == "你好"


def test_an_unclear_language_does_not_load_whisper(monkeypatch):
    loaded = []
    monkeypatch.setattr(speech_engines, "get_engine", lambda name: loaded.append(name) or object())
    monkeypatch.setattr(speech_engines, "run_sensevoice", lambda model, audio, language: ("", [], None))
    monkeypatch.setattr(speech_engines, "_loaded_engines", {})
    assert speech_engines.detect_language(np.zeros(16000, dtype=np.float32), ["yue", "tsn", "en"]) == ("yue", 0.5)
    assert "whisper" not in loaded
