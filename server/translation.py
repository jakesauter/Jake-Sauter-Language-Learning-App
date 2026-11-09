"""Translation providers and a per-language-pair router.

A provider is "ollama:<model>" or "google". router.json maps "source>target" (or "*>target",
"source>*", "*>*") to a provider and is written by bench_translation.py from measured quality and
speed. Google is used only when its key file exists; the key never leaves this machine.
"""

import html
import json
import re
import os
import time

import httpx

OLLAMA_URL = os.environ.get("POLYLANG_OLLAMA", "http://127.0.0.1:11434")
ROUTER_FILE = os.environ.get("POLYLANG_ROUTER", os.path.join(os.path.dirname(__file__), "router.json"))
GOOGLE_KEY_FILE = os.environ.get("POLYLANG_GOOGLE_KEY_FILE", "/run/secrets/google_translate_key")
FALLBACK_PROVIDER = os.environ.get("POLYLANG_LLM", "ollama:qwen3.5:4b")

LANGUAGE_NAMES = {
    "en": "English", "yue": "Cantonese", "tsn": "Taishanese", "zh": "Mandarin Chinese", "es": "Spanish",
    "fr": "French", "de": "German", "pt": "Portuguese", "fa": "Persian", "ar": "Arabic", "he": "Hebrew",
    "tr": "Turkish", "ja": "Japanese", "ko": "Korean",
}
GOOGLE_LANGUAGE_CODES = {"yue": "yue", "tsn": "yue", "zh": "zh-CN"}


def normalise_code(language):
    language = (language or "").lower()
    return "zh" if language == "cmn" else language


def google_key():
    try:
        with open(GOOGLE_KEY_FILE) as key_file:
            return key_file.read().strip() or None
    except OSError:
        return None


def choose_provider(source, target):
    source, target = normalise_code(source), normalise_code(target)
    try:
        with open(ROUTER_FILE) as router_file:
            routes = json.load(router_file)
    except (OSError, ValueError):
        routes = {}
    for route_key in (f"{source}>{target}", f"*>{target}", f"{source}>*", "*>*"):
        provider = routes.get(route_key)
        if provider and (provider != "google" or google_key()):
            return provider
    return FALLBACK_PROVIDER


def build_prompt(text, source, target, earlier_lines=(), heard_versions=()):
    source_name = LANGUAGE_NAMES.get(normalise_code(source), "the source language")
    target_name = LANGUAGE_NAMES.get(normalise_code(target), target)
    taishanese_note = ""
    if normalise_code(source) == "tsn":
        taishanese_note = (" The speaker may be using Taishanese (Toisanese), a Yue language related to Cantonese;"
                           " the text was transcribed with Cantonese characters.")
    context = ""
    if earlier_lines:
        context = ("This is a live family dinner conversation transcribed by speech recognition, so expect small "
                   "mistakes. What was said just before, for context only (do not translate it):\n"
                   + "\n".join(f"- {line}" for line in earlier_lines[-4:]) + "\n\n")
    versions = [version for version in dict.fromkeys(heard_versions) if version and version != text]
    if versions:
        text = (text + "\n\n(Speech recognition was unsure. It also heard: " + " / ".join(versions[:3])
                + ". Use all versions together to work out the most likely meaning, and translate that.)")
    return (context + f"You are a professional {source_name} to {target_name} translator. Convey the meaning and nuance"
            f" of the original while using natural {target_name}.{taishanese_note} Produce only the {target_name}"
            f" translation, with no explanations, notes or quotation marks. The text comes from speech recognition"
            f" and may be garbled. If it does not form a meaningful sentence, do not invent one: reply exactly"
            f" \"(unclear)\", or \"(unclear: <the few words you can make out>)\" if a few words are clear."
            f" Translate the following {source_name} text into {target_name}:\n\n{text}")


async def stream_translation(text, source, target, provider=None, earlier_lines=(), heard_versions=()):
    """Yield pieces of the translation as the model produces them."""
    provider = provider or choose_provider(source, target)
    if provider == "google":
        yield await translate_with_google(text, source, target)
        return
    model_name = provider.split(":", 1)[1] if provider.startswith("ollama:") else provider
    request_body = {
        "model": model_name, "stream": True, "think": False, "keep_alive": "4h",
        "options": {"temperature": 0.1, "num_ctx": 2048},
        "messages": [{"role": "user", "content": build_prompt(text, source, target, earlier_lines, heard_versions)}],
    }
    async with httpx.AsyncClient(timeout=httpx.Timeout(120, connect=5)) as client:
        async with client.stream("POST", OLLAMA_URL + "/api/chat", json=request_body) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line:
                    continue
                message = json.loads(line)
                piece = message.get("message", {}).get("content", "")
                if piece:
                    yield piece
                if message.get("done"):
                    break


async def translate_text(text, source, target, provider=None):
    started_at = time.time()
    provider = provider or choose_provider(source, target)
    pieces = [piece async for piece in stream_translation(text, source, target, provider)]
    return {"text": "".join(pieces).strip(), "provider": provider,
            "ms": round((time.time() - started_at) * 1000)}


async def translate_with_google(text, source, target):
    key = google_key()
    if not key:
        raise RuntimeError("no Google key configured")
    request_body = {"q": text, "target": GOOGLE_LANGUAGE_CODES.get(normalise_code(target), normalise_code(target)),
                    "format": "text"}
    if source:
        request_body["source"] = GOOGLE_LANGUAGE_CODES.get(normalise_code(source), normalise_code(source))
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post("https://translation.googleapis.com/language/translate/v2",
                                     params={"key": key}, json=request_body)
    payload = response.json()
    if response.status_code != 200:
        raise RuntimeError((payload.get("error") or {}).get("message", f"Google error {response.status_code}"))
    return html.unescape(payload["data"]["translations"][0]["translatedText"])


async def fuse_transcripts(versions, language):
    """Several recognizers' versions of one clip -> the single most likely sentence (best on real dinner audio)."""
    versions = [version for version in dict.fromkeys(versions) if version]
    if len(versions) < 2:
        return versions[0] if versions else ""
    language_name = LANGUAGE_NAMES.get(normalise_code(language), "the spoken language")
    prompt = (f"Several speech recognizers transcribed the same short clip of spoken {language_name} at a noisy family dinner. "
              "Write the single most likely thing that was actually said, in the same language and script. "
              "Keep any English words that were mixed in. Reply with only that sentence.\n\n"
              + "\n".join(f"{index + 1}. {text}" for index, text in enumerate(versions)))
    request_body = {"model": choose_provider(language, "en").split(":", 1)[-1], "stream": False, "think": False, "keep_alive": "4h",
                    "options": {"temperature": 0.0, "num_ctx": 2048}, "messages": [{"role": "user", "content": prompt}]}
    if request_body["model"] == "google":
        request_body["model"] = FALLBACK_PROVIDER.split(":", 1)[-1]
    async with httpx.AsyncClient(timeout=httpx.Timeout(60, connect=5)) as client:
        response = await client.post(OLLAMA_URL + "/api/chat", json=request_body)
    response.raise_for_status()
    fused = response.json()["message"]["content"].strip().strip('"“”')
    return fused if 0 < len(fused) <= 3 * max(len(version) for version in versions) else versions[0]


SUGGESTION_LANGUAGE_NAMES = {"yue": "Cantonese", "tsn": "Cantonese", "zh": "Mandarin Chinese"}


def suggestion_style(creativity):
    if creativity < 0.34:
        return "Keep them safe and polite: standard, well-known phrases a guest would use."
    if creativity < 0.67:
        return "Make them friendly and natural, mixing polite phrases with simple follow-up questions."
    return ("Make them warm and personal: curious follow-up questions about what was just said, compliments with "
            "specifics, or gentle light humor, while staying respectful to elders.")


async def suggest_replies(conversation_lines, language, creativity=0.4):
    """Short, natural things the learner could say next, with English meanings."""
    reply_language = SUGGESTION_LANGUAGE_NAMES.get(language, LANGUAGE_NAMES.get(language, "the same language"))
    transcript = "\n".join(
        f"- {line['text']}" + (f"  (English: {line['en']})" if line.get("en") else "") for line in conversation_lines[-20:])
    prompt = (
        "You are helping an English speaker who is a beginner in Cantonese join a warm family dinner conversation "
        "with their partner's family, who speak Taishanese and Cantonese. Here is the most recent conversation, "
        "transcribed by speech recognition (it may contain mistakes):\n"
        f"{transcript}\n\n"
        f"Suggest 3 short, polite, natural things the learner could say next in {reply_language}, each under 12 words, "
        "easy for a beginner to pronounce, relevant to what was just said (questions, compliments about the food, "
        f"thanks, or showing interest). {suggestion_style(creativity)} Reply only with JSON: "
        '{"suggestions": [{"say": "<written in Chinese characters>", "en": "<English meaning>", '
        '"why": "<one short phrase on when to use it>"}]}')
    request_body = {"model": choose_provider(language, "en").split(":", 1)[-1], "stream": False, "think": False,
                    "format": "json", "keep_alive": "4h",
                    # Same context size as translations: Ollama reloads the model whenever it changes.
                    "options": {"temperature": round(0.2 + 0.7 * creativity, 2), "num_ctx": 2048},
                    "messages": [{"role": "user", "content": prompt}]}
    if request_body["model"] == "google":
        request_body["model"] = FALLBACK_PROVIDER.split(":", 1)[-1]
    started_at = time.time()
    async with httpx.AsyncClient(timeout=httpx.Timeout(90, connect=5)) as client:
        response = await client.post(OLLAMA_URL + "/api/chat", json=request_body)
    response.raise_for_status()
    suggestions = json.loads(response.json()["message"]["content"]).get("suggestions", [])[:4]
    import speech_engines  # same script as the transcripts (traditional characters for Cantonese)
    cleaned = [{"say": speech_engines.to_common_script(str(item.get("say", ""))[:80], language), "en": str(item.get("en", ""))[:160], "why": str(item.get("why", ""))[:120]}
               for item in suggestions if isinstance(item, dict) and item.get("say")]
    return {"suggestions": cleaned, "ms": round((time.time() - started_at) * 1000)}


async def recap_conversation(conversation_lines, language):
    """A short English summary plus the most useful phrases to learn from what was said."""
    transcript = "\n".join(
        f"- {line['text']}" + (f"  (English: {line['en']})" if line.get("en") else "") for line in conversation_lines[-60:])
    prompt = (
        "Below is a family dinner conversation transcribed by speech recognition (it may contain mistakes). "
        "The listener is an English speaker learning Cantonese.\n"
        f"{transcript}\n\n"
        "Reply only with JSON: {\"summary\": \"<3 to 5 short English sentences on what people talked about>\", "
        "\"phrases\": [{\"say\": \"<a short useful phrase that was said, in Chinese characters>\", "
        "\"en\": \"<its English meaning>\"}]} with the 5 phrases most worth learning.")
    request_body = {"model": choose_provider(language, "en").split(":", 1)[-1], "stream": False, "think": False,
                    "format": "json", "keep_alive": "4h", "options": {"temperature": 0.3, "num_ctx": 2048},
                    "messages": [{"role": "user", "content": prompt}]}
    if request_body["model"] == "google":
        request_body["model"] = FALLBACK_PROVIDER.split(":", 1)[-1]
    started_at = time.time()
    async with httpx.AsyncClient(timeout=httpx.Timeout(120, connect=5)) as client:
        response = await client.post(OLLAMA_URL + "/api/chat", json=request_body)
    response.raise_for_status()
    result = json.loads(response.json()["message"]["content"])
    import speech_engines
    phrases = [{"say": speech_engines.to_common_script(str(item.get("say", ""))[:80], language), "en": str(item.get("en", ""))[:160]}
               for item in result.get("phrases", [])[:6] if isinstance(item, dict) and item.get("say")]
    return {"summary": str(result.get("summary", ""))[:1200], "phrases": phrases, "ms": round((time.time() - started_at) * 1000)}


CJK_CHARACTER = re.compile(r"[㐀-鿿]")
CLEAR_ENOUGH = 3  # clarity 1-5; below this the line is shown as "(unclear)"; exactly 3 is shown as rough


def mostly_latin(text):
    """A "Chinese" line that is mostly English words was really English (mixed pieces get mislabeled)."""
    letters = [character for character in text if character.isalpha()]
    return bool(letters) and sum(character.isascii() for character in letters) / len(letters) > 0.6


async def translate_with_clarity(text, source, target="en", earlier_lines=(), heard_versions=()):
    """One call: how clear the transcript is (1-5) and its translation. Garbled lines become "(unclear)"."""
    base = build_prompt(text, source, target, earlier_lines, heard_versions)
    prompt = (base + "\n\nAlso rate how clearly the speech-recognition text forms meaningful speech: 5 = clear, natural "
              "sentence; 4 = understandable with small errors; 3 = partly understandable; 2 = mostly garbled; "
              "1 = gibberish. Short everyday phrases that make sense are 4 or 5. "
              "Reply only with JSON: {\"clarity\": <1-5>, \"english\": \"<translation>\"}")
    provider = choose_provider(source, target)
    model = FALLBACK_PROVIDER.split(":", 1)[-1] if provider == "google" else provider.split(":", 1)[-1]
    request_body = {"model": model, "stream": False, "think": False, "format": "json", "keep_alive": "4h",
                    "options": {"temperature": 0.1, "num_ctx": 2048}, "messages": [{"role": "user", "content": prompt}]}
    async with httpx.AsyncClient(timeout=httpx.Timeout(60, connect=5)) as client:
        response = await client.post(OLLAMA_URL + "/api/chat", json=request_body)
    response.raise_for_status()
    try:
        answer = json.loads(response.json()["message"]["content"])
        clarity = int(answer.get("clarity", 1))
        english = str(answer.get("english", "")).strip()
    except (ValueError, TypeError):
        return {"english": "(unclear)", "clarity": 1, "unclear": True}
    unclear = clarity < CLEAR_ENOUGH or not english or bool(CJK_CHARACTER.search(english)) or english.lower().startswith("(unclear")
    return {"english": "(unclear)" if unclear else english, "clarity": clarity, "unclear": unclear}



async def conversation_gist(recent_lines):
    """One or two plain sentences on what people are talking about right now, from the trustworthy lines."""
    usable = [line for line in recent_lines if line.get("text") and line.get("en") != "(unclear)" and (line.get("clarity") or 4) >= 3]
    if len(usable) < 2:
        return ""
    transcript = "\n".join(
        (f"Speaker {line['speaker']}: " if line.get("speaker") else "- ") + line["text"]
        + (f"  (English: {line['en']})" if line.get("en") else "") for line in usable[-20:])
    prompt = ("These are the most recent lines of a family dinner conversation in Cantonese, Taishanese and English, "
              "transcribed by speech recognition (some mistakes). In one or two short, plain English sentences, say what "
              "people are talking about right now, for someone at the table who doesn't speak Cantonese. Only state what "
              "the lines support; don't guess. Reply with only those sentences.\n\n" + transcript)
    model = FALLBACK_PROVIDER.split(":", 1)[-1] if choose_provider("yue", "en") == "google" else choose_provider("yue", "en").split(":", 1)[-1]
    request_body = {"model": model, "stream": False, "think": False, "keep_alive": "4h",
                    "options": {"temperature": 0.2, "num_ctx": 2048}, "messages": [{"role": "user", "content": prompt}]}
    async with httpx.AsyncClient(timeout=httpx.Timeout(60, connect=5)) as client:
        response = await client.post(OLLAMA_URL + "/api/chat", json=request_body)
    response.raise_for_status()
    return response.json()["message"]["content"].strip()[:400]


async def understand_line(heard_versions, source, target="en", earlier_lines=()):
    """One call per line: which version was really said, its translation, and how clear it is.

    Speech engines often split on sound-alikes (你好嗎 vs 你號碼); seeing every version side by side lets the
    model choose the one that makes sense instead of judging a single wrong guess.
    """
    versions = [version for version in dict.fromkeys(heard_versions) if version]
    if not versions:
        return {"said": "", "english": "", "clarity": 1, "unclear": True}
    source_name = LANGUAGE_NAMES.get(normalise_code(source), "the spoken language")
    target_name = LANGUAGE_NAMES.get(normalise_code(target), target)
    taishanese_note = (" It may be Taishanese (Toisanese), a Yue language close to Cantonese, written with Cantonese characters."
                       if normalise_code(source) == "tsn" else "")
    context = ""
    if earlier_lines:
        context = ("What was said just before, for context only:\n" + "\n".join(f"- {line}" for line in earlier_lines[-4:]) + "\n\n")
    listed = "\n".join(f"{index + 1}. {version}" for index, version in enumerate(versions))
    prompt = (context + f"At a family dinner, someone said one short thing in {source_name}.{taishanese_note} "
              f"Speech recognizers heard these versions (they often confuse words that sound alike):\n{listed}\n\n"
              "Decide what was most likely actually said: pick the version that forms a natural, meaningful sentence, "
              "or combine them if each got part of it right. Keep English words that were mixed in. Do not invent content.\n"
              f"Then translate it into natural {target_name}, and rate clarity: 5 = clear natural sentence, "
              "4 = understandable with small errors, 3 = partly understandable, 2 = mostly garbled, 1 = gibberish. "
              "Short everyday phrases that make sense are 4 or 5.\n"
              f'Reply only with JSON: {{"said": "<what was said, in Chinese characters>", "english": "<{target_name} translation>", "clarity": <1-5>}}')
    provider = choose_provider(source, target)
    model = FALLBACK_PROVIDER.split(":", 1)[-1] if provider == "google" else provider.split(":", 1)[-1]
    request_body = {"model": model, "stream": False, "think": False, "format": "json", "keep_alive": "4h",
                    "options": {"temperature": 0.1, "num_ctx": 2048}, "messages": [{"role": "user", "content": prompt}]}
    async with httpx.AsyncClient(timeout=httpx.Timeout(60, connect=5)) as client:
        response = await client.post(OLLAMA_URL + "/api/chat", json=request_body)
    response.raise_for_status()
    try:
        answer = json.loads(response.json()["message"]["content"])
        said = str(answer.get("said") or versions[0]).strip()
        english = str(answer.get("english", "")).strip()
        clarity = int(answer.get("clarity", 1))
    except (ValueError, TypeError):
        return {"said": versions[0], "english": "(unclear)", "clarity": 1, "unclear": True}
    if len(said) > 3 * max(len(version) for version in versions):
        said = versions[0]  # the model wrote far more than anyone heard: don't trust it
    unclear = clarity < CLEAR_ENOUGH or not english or bool(CJK_CHARACTER.search(english))
    return {"said": said, "english": "(unclear)" if unclear else english, "clarity": clarity, "unclear": unclear}
