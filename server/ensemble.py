"""Run several speech engines on the same audio and merge their transcripts.

Every engine transcribes the same speech chunks, so their outputs line up by construction. Within a
chunk, transcripts are aligned token by token (characters for Chinese, words otherwise). Where all
engines agree the text is confident; where they disagree, the most-voted reading is shown (ties go to
the engine listed first for the language) and every alternative is kept for the app to offer.
"""

import difflib
import os
import re
import unicodedata

import speech_engines as engines
from speech_engines import CHINESE_LANGUAGES, SAMPLE_RATE

# Engine order is the tie-break priority.
ENGINES_BY_LANGUAGE = {
    "yue": ["buzzasr", "sensevoice", "whisper"],
    "tsn": ["buzzasr", "sensevoice", "whisper"],
    "zh": ["whisper", "sensevoice"],
    "en": ["whisper", "sensevoice"],
    "ja": ["whisper", "sensevoice"],
    "ko": ["whisper", "sensevoice"],
}
DEFAULT_ENGINES = ["whisper"]
for variable, value in os.environ.items():
    if variable.startswith("POLYLANG_ENGINES_"):
        language_code = variable[len("POLYLANG_ENGINES_"):].lower()
        ENGINES_BY_LANGUAGE[language_code] = [name.strip() for name in value.split(",") if name.strip()]

OPENING_PUNCTUATION = "([{“‘¿¡"


# ---------- tokens ----------

def is_punctuation(token):
    return all(unicodedata.category(character)[0] in "PZS" for character in token)


CJK_CHARACTER = "\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\U00020000-\U0002ebef"
TOKEN = re.compile(rf"[{CJK_CHARACTER}]|[^\W_{CJK_CHARACTER}]+(?:['’-][^\W_{CJK_CHARACTER}]+)*|[^\w\s]")


def is_cjk(token):
    return bool(token) and bool(re.fullmatch(rf"[{CJK_CHARACTER}]", token[0]))


def split_tokens(text, is_chinese=None):
    """Chinese characters one by one, words of any other script whole, punctuation separately.

    The same rule serves every language, so a Cantonese line with English words in it aligns correctly.
    """
    return TOKEN.findall(text)


def comparison_key(token):
    """Case-folded and punctuation-free; empty for pure punctuation."""
    return "".join(c for c in token.lower() if unicodedata.category(c)[0] not in "PZS")


def needs_space_between(left_token, right_token):
    if not left_token or not right_token:
        return False
    if left_token[-1] in OPENING_PUNCTUATION:
        return False
    if is_punctuation(right_token[0]) and right_token[0] not in OPENING_PUNCTUATION:
        return False
    if is_cjk(left_token[-1]) and is_cjk(right_token[0]):
        return False
    if is_punctuation(left_token[-1]) and is_cjk(right_token[0]):
        return False  # "，我" — Chinese punctuation needs no space
    return True


def join_tokens(tokens, is_chinese=None):
    text = ""
    for token in tokens:
        text += (" " if needs_space_between(text, token) else "") + token
    return text


def join_pieces(left, right, is_chinese=None):
    return left + (" " if needs_space_between(left, right) else "") + right


# ---------- merging ----------

def merge(transcripts, engine_order, is_chinese):
    """transcripts: {engine: text}. Returns (merged_text, spans, agreement between 0 and 1).

    A span is {"text"} where engines agree, or {"text", "alts": [{"text", "engines"}]} where they don't.
    """
    engines_with_text = [name for name in engine_order if transcripts.get(name)]
    if not engines_with_text:
        return "", [], 0.0
    if len(engines_with_text) == 1:
        only_text = transcripts[engines_with_text[0]]
        return only_text, [{"text": only_text}], 1.0

    base_engine, other_engines = engines_with_text[0], engines_with_text[1:]
    base_tokens = split_tokens(transcripts[base_engine], is_chinese)
    base_word_positions = [index for index, token in enumerate(base_tokens) if comparison_key(token)]
    base_keys = [comparison_key(base_tokens[index]) for index in base_word_positions]
    base_word_count = len(base_word_positions)

    # How each other engine's words line up against the base words (punctuation ignored).
    alignments, other_words = {}, {}
    for engine in other_engines:
        words = [token for token in split_tokens(transcripts[engine], is_chinese) if comparison_key(token)]
        other_words[engine] = words
        matcher = difflib.SequenceMatcher(None, base_keys, [comparison_key(word) for word in words], autojunk=False)
        alignments[engine] = matcher.get_opcodes()

    conflict_regions = _conflict_regions(alignments)

    def text_from_engine(engine, region_start, region_end):
        words = []
        for operation, base_from, base_to, other_from, other_to in alignments[engine]:
            if operation == "equal":
                overlap_from, overlap_to = max(base_from, region_start), min(base_to, region_end)
                if overlap_from < overlap_to:
                    shift = other_from - base_from
                    words += other_words[engine][overlap_from + shift: overlap_to + shift]
            elif operation == "insert":
                if region_start <= base_from <= region_end:
                    words += other_words[engine][other_from:other_to]
            elif base_from >= region_start and base_to <= region_end:
                words += other_words[engine][other_from:other_to]
        return join_tokens(words, is_chinese)

    def base_text(word_from, word_to):
        """Base text for words [word_from, word_to), plus the punctuation that follows it."""
        if word_from >= word_to:
            return "", ""
        first_token = base_word_positions[word_from]
        after_last_token = base_word_positions[word_to - 1] + 1
        next_word_token = base_word_positions[word_to] if word_to < base_word_count else len(base_tokens)
        return (join_tokens(base_tokens[first_token:after_last_token], is_chinese),
                join_tokens(base_tokens[after_last_token:next_word_token], is_chinese))

    priority = {engine: rank for rank, engine in enumerate(engines_with_text)}
    spans = []
    leading_punctuation = join_tokens(base_tokens[:base_word_positions[0]] if base_word_positions else base_tokens, is_chinese)
    if leading_punctuation:
        spans.append({"text": leading_punctuation})
    position, agreed_words, total_weight = 0, 0, 0
    for region_start, region_end in conflict_regions:
        if position < region_start:
            words, punctuation = base_text(position, region_start)
            spans.append({"text": join_pieces(words, punctuation, is_chinese)})
            agreed_words += region_start - position
            total_weight += region_start - position
        words, punctuation = base_text(region_start, region_end)
        readings = {words: [base_engine]}
        for engine in other_engines:
            readings.setdefault(text_from_engine(engine, region_start, region_end), []).append(engine)
        alternatives = sorted(
            ({"text": reading, "engines": voters} for reading, voters in readings.items()),
            key=lambda alternative: (-len(alternative["engines"]), min(priority[e] for e in alternative["engines"])))
        spans.append({"text": join_pieces(alternatives[0]["text"], punctuation, is_chinese), "alts": alternatives})
        total_weight += max(region_end - region_start, 1)
        position = region_end
    if position < base_word_count:
        words, punctuation = base_text(position, base_word_count)
        spans.append({"text": join_pieces(words, punctuation, is_chinese)})
        agreed_words += base_word_count - position
        total_weight += base_word_count - position

    spans = _combine_agreed_neighbours(spans, is_chinese)
    merged_text = ""
    for span in spans:
        if span["text"]:
            merged_text = join_pieces(merged_text, span["text"], is_chinese)
    agreement = round(agreed_words / total_weight, 3) if total_weight else 1.0
    return merged_text.strip(), spans, agreement


def _conflict_regions(alignments):
    """Union of every engine's disagreeing ranges on the base words; touching ranges are merged."""
    ranges = sorted((base_from, base_to)
                    for opcodes in alignments.values()
                    for operation, base_from, base_to, _, _ in opcodes if operation != "equal")
    regions = []
    for range_start, range_end in ranges:
        if regions and range_start <= regions[-1][1]:
            regions[-1][1] = max(regions[-1][1], range_end)
        else:
            regions.append([range_start, range_end])
    return regions


def _combine_agreed_neighbours(spans, is_chinese):
    combined = []
    for span in spans:
        if combined and "alts" not in span and "alts" not in combined[-1]:
            combined[-1]["text"] = join_pieces(combined[-1]["text"], span["text"], is_chinese)
        else:
            combined.append(span)
    return combined


# ---------- running ----------

def transcribe_file(path, language, engine_names=None):
    return transcribe_audio(engines.decode_audio_file(path), language, engine_names)


def transcribe_audio(audio, language, engine_names=None, time_offset=0.0, split_on_silence=True):
    """Transcribe float32 16 kHz mono audio with every engine for the language and merge the results."""
    language = (language or "").lower()
    engine_order = engine_names or ENGINES_BY_LANGUAGE.get(language, DEFAULT_ENGINES)
    seconds_per_engine = {name: 0.0 for name in engine_order}
    detected_language = None
    segments = []
    if split_on_silence:
        regions = engines.speech_regions(audio)
        if not regions and len(audio) > SAMPLE_RATE // 4:
            regions = [(0, len(audio))]
    else:
        regions = [(0, len(audio))]

    for region_start, region_end in regions:
        chunk = audio[region_start:region_end]
        chunk_start_seconds = region_start / SAMPLE_RATE + time_offset
        transcripts, words_by_engine = {}, {}
        for engine_name in engine_order:
            result = engines.transcribe_with(engine_name, chunk, language)
            if result is None:
                continue
            seconds_per_engine[engine_name] += result["seconds"]
            detected_language = detected_language or result["detected_language"]
            script_language = language or (result["detected_language"] if result["detected_language"] in CHINESE_LANGUAGES else "")
            transcripts[engine_name] = engines.to_common_script(result["text"], script_language)
            words_by_engine[engine_name] = [
                {**word, "start": round(word["start"] + chunk_start_seconds, 2), "end": round(word["end"] + chunk_start_seconds, 2)}
                for word in result["words"]]
        if not any(transcripts.values()):
            continue
        is_chinese = language in CHINESE_LANGUAGES or (not language and detected_language in CHINESE_LANGUAGES)
        merged_text, spans, agreement = merge(transcripts, [name for name in engine_order if name in transcripts], is_chinese)
        segments.append({
            "start": round(chunk_start_seconds, 2),
            "end": round(region_end / SAMPLE_RATE + time_offset, 2),
            "text": merged_text, "spans": spans, "agree": agreement, "hyps": transcripts,
            "words": next((words_by_engine[name] for name in engine_order if words_by_engine.get(name)), []),
        })

    failed = engines.failed_engines()
    used_engines = [name for name in engine_order if name not in failed]
    return {"language": language or detected_language or "", "segments": segments, "engines": used_engines,
            "engine_seconds": {name: round(seconds, 2) for name, seconds in seconds_per_engine.items() if name in used_engines},
            "unavailable": {name: error for name, error in failed.items() if name in engine_order}}
