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
    if engine_name == "sensevoice":
        text, words, detected_language = run_sensevoice(model, audio, language)
    else:
        text, words, detected_language = run_whisper(model, audio, language)
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
    total = sum(family_scores.values()) or 1.0
    best_family = max(family_scores, key=family_scores.get)
    members = families[best_family]
    best_code = "yue" if best_family == "yue" and len(members) > 1 else members[0]
    return best_code, round(family_scores[best_family] / total, 3)


def speech_regions(audio, min_silence_ms=500, max_speech_seconds=25, padding_ms=200, min_speech_ms=250):
    from faster_whisper.vad import VadOptions, get_speech_timestamps
    options = VadOptions(min_silence_duration_ms=min_silence_ms, max_speech_duration_s=max_speech_seconds,
                         speech_pad_ms=padding_ms, min_speech_duration_ms=min_speech_ms)
    return [(region["start"], region["end"]) for region in get_speech_timestamps(audio, options)]


def decode_audio_file(path):
    from faster_whisper.audio import decode_audio
    return decode_audio(path, sampling_rate=SAMPLE_RATE)
