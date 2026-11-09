"""Speech recognition engines: loading, running, and normalising their output to one script."""

import os
import re
import threading
import time

SAMPLE_RATE = 16000

WHISPER_MODEL = os.environ.get("POLYLANG_MODEL", "large-v3")
BUZZASR_MODEL_PATH = os.environ.get("POLYLANG_BUZZ", os.path.expanduser("~/models/buzzasr-cantonese-ct2"))
SENSEVOICE_MODEL = os.environ.get("POLYLANG_SENSEVOICE", "FunAudioLLM/SenseVoiceSmall")
DEVICE = os.environ.get("POLYLANG_DEVICE", "cuda")
COMPUTE_TYPE = os.environ.get("POLYLANG_COMPUTE", "int8_float16")

KNOWN_ENGINES = ("whisper", "buzzasr", "sensevoice")
SENSEVOICE_LANGUAGES = {"yue", "tsn", "zh", "en", "ja", "ko"}
CHINESE_LANGUAGES = {"yue", "tsn", "zh"}

# One GPU job at a time, shared by uploads and live sessions.
gpu_lock = threading.Lock()

_loaded_engines = {}
_failed_engines = {}
_loading_lock = threading.Lock()


def _load_whisper(model_name_or_path):
    from faster_whisper import WhisperModel
    return WhisperModel(model_name_or_path, device=DEVICE, compute_type=COMPUTE_TYPE)


def _load_sensevoice():
    from funasr import AutoModel
    device = "cuda:0" if DEVICE == "cuda" else "cpu"
    return AutoModel(model=SENSEVOICE_MODEL, hub="hf", device=device, disable_update=True)


def get_engine(engine_name):
    """Load an engine on first use; returns None if it can't load (the others still run)."""
    with _loading_lock:
        if engine_name in _failed_engines:
            return None
        if engine_name not in _loaded_engines:
            loaders = {
                "whisper": lambda: _load_whisper(WHISPER_MODEL),
                "buzzasr": lambda: _load_whisper(BUZZASR_MODEL_PATH),
                "sensevoice": _load_sensevoice,
            }
            started_at = time.time()
            try:
                _loaded_engines[engine_name] = loaders[engine_name]()
                print(f"loaded {engine_name} in {time.time() - started_at:.1f}s")
            except Exception as error:
                print(f"engine {engine_name} unavailable: {error}")
                _failed_engines[engine_name] = str(error)
                return None
        return _loaded_engines[engine_name]


def loaded_engine_names():
    return sorted(_loaded_engines)


def failed_engines():
    return dict(_failed_engines)


def whisper_language_code(language):
    # Taishanese has no model of its own; Cantonese is its closest relative.
    return "yue" if language in ("yue", "tsn") else (language or None)


def run_whisper(model, audio, language, beam_size=5, with_words=True):
    segments, info = model.transcribe(
        audio, language=whisper_language_code(language), beam_size=beam_size, vad_filter=False,
        condition_on_previous_text=False, word_timestamps=with_words)
    segments = list(segments)
    words = [
        {"word": word.word, "start": round(word.start, 2), "end": round(word.end, 2),
         "probability": round(word.probability, 3)}
        for segment in segments for word in (segment.words or [])
    ]
    text = "".join(segment.text for segment in segments).strip()
    return text, words, info.language


SENSEVOICE_TAG = re.compile(r"<\|([^|]*)\|>")
EMOJI = re.compile(r"[\U0001F300-\U0001FAFF☀-➿]")


def run_sensevoice(model, audio, language):
    language_hint = whisper_language_code(language) if language in SENSEVOICE_LANGUAGES else "auto"
    results = model.generate(input=audio, cache={}, language=language_hint, use_itn=True, batch_size_s=60)
    raw_text = results[0]["text"] if results else ""
    tags = SENSEVOICE_TAG.findall(raw_text)
    detected_language = next((tag for tag in tags if tag in ("zh", "yue", "en", "ja", "ko")), None)
    try:
        from funasr.utils.postprocess_utils import rich_transcription_postprocess
        text = rich_transcription_postprocess(raw_text)
    except Exception:
        text = SENSEVOICE_TAG.sub("", raw_text)
    # SenseVoice appends emotion/event emoji; they aren't speech.
    return EMOJI.sub("", text).strip(), [], detected_language


def transcribe_with(engine_name, audio, language):
    model = get_engine(engine_name)
    if model is None:
        return None
    started_at = time.time()
    try:
        if engine_name == "sensevoice":
            text, words, detected_language = run_sensevoice(model, audio, language)
        else:
            text, words, detected_language = run_whisper(model, audio, language)
    except RuntimeError as error:
        if "CUDA" in str(error) or "cuda" in str(error):
            # A GPU error can leave the model unusable; drop it so the next request reloads it fresh.
            with _loading_lock:
                _loaded_engines.pop(engine_name, None)
            import gc
            gc.collect()
        raise
    return {"text": text, "words": words, "detected_language": detected_language,
            "seconds": round(time.time() - started_at, 2)}


def quick_transcript(audio, language, candidate_languages=()):
    """Fast, lower-accuracy transcript for live partial results."""
    if len(candidate_languages) > 1 and set(candidate_languages) <= SENSEVOICE_LANGUAGES:
        model = get_engine("sensevoice")
        if model is not None:
            text, _, detected = run_sensevoice(model, audio, "")
            return to_common_script(text, "yue" if detected in ("yue", "zh") and "zh" not in candidate_languages else (detected or ""))
    if language in SENSEVOICE_LANGUAGES:
        model = get_engine("sensevoice")
        if model is not None:
            return to_common_script(run_sensevoice(model, audio, language)[0], language)
    model = get_engine("whisper")
    text, _, _ = run_whisper(model, audio, language, beam_size=1, with_words=False)
    return text


_script_converters = {}


def _converter(configuration):
    if configuration not in _script_converters:
        try:
            from opencc import OpenCC
            _script_converters[configuration] = OpenCC(configuration)
        except Exception:
            _script_converters[configuration] = None
    return _script_converters[configuration]


REPEATED_UNIT = re.compile(r"(.{1,3}?)(?:[\s,，、。.!！?？]*\1){4,}")
REPEATED_WORD = re.compile(r"\b(\w+)\b(?:[\s,.!?]+\1\b){3,}", re.IGNORECASE)


def is_repetition_loop(text):
    """Whisper's well-known failure on laughter and noise: 唔唔唔唔唔, 啱啱啱啱, 啵 啵 啵 啵, just just just just.
    Short genuine repeats like 多謝多謝多謝 or 好呀好呀 are kept."""
    letters = [character for character in text if character.isalnum()]
    if len(letters) >= 9 and len(set(letters)) / len(letters) < 0.3:
        return True
    looped = sum(len(match.group(0)) for match in REPEATED_UNIT.finditer(text))
    if len(letters) >= 8 and looped / max(1, len(text)) > 0.5:
        return True
    return bool(REPEATED_WORD.search(text))


# Common Cantonese typing variants that change the meaning a translator sees (哂 "smile" vs 晒 "all/completely").
CANTONESE_VARIANT_FIXES = {"多謝哂": "多謝晒", "唔該哂": "唔該晒", "食哂": "食晒", "做哂": "做晒", "冇哂": "冇晒", "曬": "晒"}


def fix_cantonese_variants(text):
    for variant, standard in CANTONESE_VARIANT_FIXES.items():
        text = text.replace(variant, standard)
    return text


def to_common_script(text, language):
    """Put every engine's output in the same script so alignment compares like with like."""
    if not text:
        return text
    if language in ("yue", "tsn"):
        converter = _converter("s2hk")
    elif language == "zh":
        converter = _converter("t2s")
    else:
        converter = None
    return converter.convert(text) if converter else text


# Languages no model tells apart by sound share a family; the family's speech code is what engines hear.
SPEECH_FAMILY = {"yue": "yue", "tsn": "yue", "zh": "zh", "cmn": "zh"}


def detect_language(audio, candidate_languages):
    """Most likely language among the candidates, with its probability.

    Returns a code from candidate_languages, or "yue" when Cantonese and Taishanese are both possible,
    because nothing can tell those two apart by sound yet.
    """
    candidates = [code for code in dict.fromkeys(candidate_languages) if code]
    if len(candidates) <= 1:
        return (candidates[0] if candidates else ""), 1.0
    # SenseVoice first: trained on Cantonese, Mandarin and English (and mixes of them). Whisper's detector
    # calls noisy Cantonese "English" too often, so it is only used for languages SenseVoice doesn't know.
    families = {}
    for code in candidates:
        families.setdefault(SPEECH_FAMILY.get(code, code), []).append(code)
    sensevoice = get_engine("sensevoice")
    if sensevoice is not None and set(families) & {"yue", "zh", "en", "ja", "ko"}:
        heard_as = run_sensevoice(sensevoice, audio, "")[2]
        if heard_as == "zh" and "zh" not in families and "yue" in families:
            heard_as = "yue"
        if heard_as == "yue" and "yue" not in families and "zh" in families:
            heard_as = "zh"
        if heard_as in families:
            members = families[heard_as]
            return ("yue" if heard_as == "yue" and len(members) > 1 else members[0]), 0.9
    model = get_engine("whisper")
    if model is None:
        return candidates[0], 0.0
    _, _, all_probabilities = model.detect_language(audio=audio[: 30 * SAMPLE_RATE], vad_filter=False)
    probability_by_code = dict(all_probabilities)
    families = {}
    for code in candidates:
        families.setdefault(SPEECH_FAMILY.get(code, code), []).append(code)
    if "yue" in families and "zh" not in families:
        # Whisper often hears Cantonese as Mandarin; when Mandarin isn't an option, count it as Cantonese.
        probability_by_code["yue"] = probability_by_code.get("yue", 0) + probability_by_code.get("zh", 0)
    family_scores = {family: probability_by_code.get(family, 0.0) for family in families}
    if "yue" in families and "zh" in families:
        # Whisper labels Cantonese as Mandarin far too often; it decides "Chinese or not",
        # and SenseVoice (trained on both) decides which Chinese.
        chinese_score = family_scores["yue"] + family_scores["zh"]
        sensevoice = get_engine("sensevoice")
        heard_as = run_sensevoice(sensevoice, audio, "")[2] if sensevoice is not None else "yue"
        family_scores["yue"], family_scores["zh"] = (chinese_score, 0.0) if heard_as != "zh" else (0.0, chinese_score)
    total = sum(family_scores.values()) or 1.0
    best_family = max(family_scores, key=family_scores.get)
    members = families[best_family]
    best_code = "yue" if best_family == "yue" and len(members) > 1 else members[0]
    return best_code, round(family_scores[best_family] / total, 3)


def clean_audio(audio):
    """Low-cut filter (table and room rumble) and level the volume, so far-away voices are as loud as near ones.

    On tonight's dinner recordings this raised transcript coherence from 3.9 to 4.1 out of 5 and removed the
    gibberish lines (tests/experiment_cantonese_variants.py).
    """
    import numpy as np
    import scipy.signal
    low_cut = scipy.signal.butter(4, 120, "highpass", fs=SAMPLE_RATE, output="sos")
    filtered = scipy.signal.sosfilt(low_cut, audio)
    loudness = np.sqrt(np.mean(filtered ** 2)) + 1e-9
    return np.clip(filtered * (0.08 / loudness), -1, 1).astype(np.float32)


def speech_regions(audio, min_silence_ms=500, max_speech_seconds=25, padding_ms=200, min_speech_ms=250):
    from faster_whisper.vad import VadOptions, get_speech_timestamps
    options = VadOptions(min_silence_duration_ms=min_silence_ms, max_speech_duration_s=max_speech_seconds,
                         speech_pad_ms=padding_ms, min_speech_duration_ms=min_speech_ms)
    return [(region["start"], region["end"]) for region in get_speech_timestamps(audio, options)]


def decode_audio_file(path):
    from faster_whisper.audio import decode_audio
    return decode_audio(path, sampling_rate=SAMPLE_RATE)
