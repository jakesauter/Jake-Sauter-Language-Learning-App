"""Translation providers and a per-language-pair router.

A provider is "ollama:<model>" or "google". router.json maps "source>target" (or "*>target",
"source>*", "*>*") to a provider and is written by bench_translation.py from measured quality and
speed. Google is used only when its key file exists; the key never leaves this machine.
"""

import html
import json
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


def build_prompt(text, source, target):
    source_name = LANGUAGE_NAMES.get(normalise_code(source), "the source language")
    target_name = LANGUAGE_NAMES.get(normalise_code(target), target)
    taishanese_note = ""
    if normalise_code(source) == "tsn":
        taishanese_note = (" The speaker may be using Taishanese (Toisanese), a Yue language related to Cantonese;"
                           " the text was transcribed with Cantonese characters.")
    return (f"You are a professional {source_name} to {target_name} translator. Convey the meaning and nuance"
            f" of the original while using natural {target_name}.{taishanese_note} Produce only the {target_name}"
            f" translation, with no explanations, notes or quotation marks. Translate the following"
            f" {source_name} text into {target_name}:\n\n{text}")


async def stream_translation(text, source, target, provider=None):
    """Yield pieces of the translation as the model produces them."""
    provider = provider or choose_provider(source, target)
    if provider == "google":
        yield await translate_with_google(text, source, target)
        return
    model_name = provider.split(":", 1)[1] if provider.startswith("ollama:") else provider
    request_body = {
        "model": model_name, "stream": True, "think": False, "keep_alive": "4h",
        "options": {"temperature": 0.1, "num_ctx": 2048},
        "messages": [{"role": "user", "content": build_prompt(text, source, target)}],
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
