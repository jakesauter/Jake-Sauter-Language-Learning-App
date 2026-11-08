"""Regression tests for the multi-engine consensus merge (expected values verified by hand on 2026-11-08)."""
import ensemble
import speech_engines


def merge_normalised(hypotheses_by_engine, engine_order, language):
    normalised = {engine: speech_engines.to_common_script(text, language) for engine, text in hypotheses_by_engine.items()}
    return ensemble.merge(normalised, engine_order, language in speech_engines.CHINESE_LANGUAGES)


def test_cantonese_majority_beats_written_chinese():
    text, spans, agreement = merge_normalised(
        {"buzzasr": "我哋今日去飲茶。", "sensevoice": "我哋今日去饮茶", "whisper": "我們今日去飲茶。"},
        ["buzzasr", "sensevoice", "whisper"], "yue")
    assert text == "我哋今日去飲茶。"
    assert agreement == 0.857
    disputed = [span for span in spans if "alts" in span]
    assert len(disputed) == 1
    assert disputed[0]["alts"][0] == {"text": "哋", "engines": ["buzzasr", "sensevoice"]}
    assert disputed[0]["alts"][1] == {"text": "們", "engines": ["whisper"]}


def test_three_way_split_falls_back_to_priority():
    text, spans, agreement = merge_normalised(
        {"buzzasr": "佢係我阿媽", "sensevoice": "佢系我阿妈啊", "whisper": "他是我媽媽"},
        ["buzzasr", "sensevoice", "whisper"], "yue")
    assert text == "佢係我阿媽"
    assert agreement == 0.333
    assert spans[0]["alts"][0]["engines"] == ["buzzasr"]


def test_spanish_missing_word_and_punctuation_spacing():
    text, spans, agreement = merge_normalised(
        {"whisper": "Mañana vamos a la playa con mis amigos.", "sensevoice": "mañana vamos a playa con mis amigos"},
        ["whisper", "sensevoice"], "")
    assert text == "Mañana vamos a la playa con mis amigos."
    assert agreement == 0.875
    assert spans[-1]["text"] == "playa con mis amigos."


def test_inverted_question_mark_is_not_a_word():
    text, spans, agreement = merge_normalised(
        {"whisper": "¿Dónde está el baño? Gracias.", "sensevoice": "donde esta el bano gracias"},
        ["whisper", "sensevoice"], "")
    assert text == "¿Dónde está el baño? Gracias."
    assert agreement == 0.4  # 2 of 5 words agree; "¿" is not counted as a word


def test_mandarin_insertion_lowers_agreement():
    text, spans, agreement = merge_normalised(
        {"whisper": "我们明天去北京。", "sensevoice": "我们明天要去北京"}, ["whisper", "sensevoice"], "zh")
    assert text == "我们明天去北京。"
    assert agreement == 0.875


def test_single_engine_passes_through():
    text, spans, agreement = merge_normalised({"whisper": "你好", "sensevoice": ""}, ["whisper", "sensevoice"], "zh")
    assert (text, agreement) == ("你好", 1.0)


def test_cantonese_with_english_words_keeps_them():
    text, spans, agreement = ensemble.merge(
        {"sensevoice": "我好like呢個menu，好正！", "whisper": "我好鍾意呢個菜單，好正！"}, ["sensevoice", "whisper"], True)
    assert text == "我好 like 呢個 menu，好正！"


def test_english_word_case_differences_count_as_agreement():
    text, spans, agreement = ensemble.merge(
        {"sensevoice": "今晚個steak好好食", "buzzasr": "今晚個steak好好食", "whisper": "今晚個 Steak 好好食"},
        ["sensevoice", "buzzasr", "whisper"], True)
    assert (text, agreement) == ("今晚個 steak 好好食", 1.0)
