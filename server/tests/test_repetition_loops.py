"""Whisper's laughter/noise loops are dropped; short genuine repeats are kept."""
import pytest
import speech_engines


@pytest.mark.parametrize("text", ["唔唔唔唔唔唔唔唔唔唔", "咁我哋啱啱啱啱啱啱啱啱啱", "喔 啵 啵 啵 啵 咦 啵 啵 啵",
                                  "嘻嘻嘻嘻嘻嘻嘻嘻嘻嘻", "So we just just just just", "要唔唔唔唔唔唔唔唔唔唔唔唔"])
def test_loops_are_detected(text):
    assert speech_engines.is_repetition_loop(text)


@pytest.mark.parametrize("text", ["你食咗飯未呀", "今晚嗰條魚好好食", "Let me know if you want more fish.", "多謝多謝多謝",
                                  "好呀好呀", "要小心 要小心 要小心", "No no no", "哈哈哈哈"])
def test_real_speech_is_kept(text):
    assert not speech_engines.is_repetition_loop(text)
