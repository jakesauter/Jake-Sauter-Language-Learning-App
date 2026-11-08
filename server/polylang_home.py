"""Polylang home transcriber.

Runs on your own computer, so there is no cloud bill. Phones reach it privately over Tailscale.

    POST /transcribe   multipart: file, language (yue, zh, es, fr, de, en or blank), translate (1/0),
                       lang (app tag, e.g. tsn), engines (optional comma list to override routing)
                       -> segments[] with merged text, per-engine hyps, disagreement spans, agreement
    GET  /health

Every upload and its transcript is saved under DATA_DIR. Those files are the start
of a Taishanese speech dataset that you can correct and fine-tune on later.
"""

import json
import re
import os
import tempfile
import threading
import time
import urllib.request
from email.parser import BytesParser
from email.policy import default as email_policy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


MODEL = os.environ.get("POLYLANG_MODEL", "large-v3")
DEVICE = os.environ.get("POLYLANG_DEVICE", "cuda")
COMPUTE = os.environ.get("POLYLANG_COMPUTE", "int8_float16")
PORT = int(os.environ.get("POLYLANG_PORT", "8000"))
DATA_DIR = os.environ.get("POLYLANG_DATA", os.path.expanduser("~/polylang-data"))
OLLAMA = os.environ.get("POLYLANG_OLLAMA", "http://127.0.0.1:11434")
LLM = os.environ.get("POLYLANG_LLM", "qwen2.5:7b")
MAX_MB = int(os.environ.get("POLYLANG_MAX_MB", "200"))

ORIGINS = [o.strip() for o in os.environ.get(
    "POLYLANG_ORIGINS",
    "https://jakesauter.github.io",
).split(",") if o.strip()]

# Only these websites may call the server from a browser. Wildcard hosting domains (claude.ai
# artifacts, github.io in general) are deliberately excluded: anyone can publish a page there.
ORIGIN_SUFFIXES = ()


def origin_ok(origin):
    return origin in ORIGINS or origin.endswith(ORIGIN_SUFFIXES) if ORIGIN_SUFFIXES else (
        origin in ORIGINS or re.fullmatch(r"http://(localhost|127\.0\.0\.1)(:\d+)?", origin or "") is not None)


_gpu = threading.Lock()

import ensemble  # noqa: E402  (multi-engine ASR + consensus merge)


def translate(segments, language):
    if not segments:
        return segments
    lines = [s["text"] for s in segments]
    prompt = (
        "You help an English speaker learn their family's language "
        f"(Whisper detected: {language}; it may be Taishanese, Cantonese or Mandarin). "
        "Translate each line into natural English. Return JSON: {\"en\": [one string per line, same order]}.\n\n"
        + json.dumps(lines, ensure_ascii=False)
    )
    body = json.dumps({"model": LLM, "prompt": prompt, "stream": False, "format": "json"}).encode()
    try:
        req = urllib.request.Request(OLLAMA + "/api/generate", body, {"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=300) as r:
            en = json.loads(json.loads(r.read())["response"]).get("en", [])
        for s, e in zip(segments, en):
            s["en"] = str(e)
    except Exception as e:
        print("translation skipped:", e)
    return segments


def save(raw, name, result, language=""):
    day = time.strftime("%Y-%m-%d")
    if not re.fullmatch(r"[a-z]{2,3}(-[A-Za-z]{2,4})?", language or ""):
        language = "unknown"
    d = os.path.join(DATA_DIR, language, day)
    if not os.path.realpath(d).startswith(os.path.realpath(DATA_DIR) + os.sep):
        raise ValueError("refusing to write outside the data folder")
    os.makedirs(d, exist_ok=True)
    stem = time.strftime("%H%M%S") + "-" + os.path.basename(name or "clip")
    with open(os.path.join(d, stem), "wb") as f:
        f.write(raw)
    with open(os.path.join(d, stem + ".json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)


def parse_form(headers, body):
    msg = BytesParser(policy=email_policy).parsebytes(
        b"Content-Type: " + headers["Content-Type"].encode() + b"\r\n\r\n" + body
    )
    fields, files = {}, {}
    for part in msg.iter_parts():
        name = part.get_param("name", header="content-disposition")
        if part.get_filename():
            files[name] = (part.get_filename(), part.get_payload(decode=True))
        else:
            fields[name] = part.get_content().strip()
    return fields, files


class Handler(BaseHTTPRequestHandler):

    def cors(self):
        origin = self.headers.get("Origin", "")
        if origin_ok(origin):
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Allow-Private-Network", "true")

    def reply(self, code, obj):
        data = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.cors()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        self.send_response(204)
        self.cors()
        self.end_headers()

    def do_GET(self):
        if self.path.startswith("/health"):
            return self.reply(200, {"ok": True, "model": MODEL, "device": DEVICE, "llm": LLM,
                                   "routes": ensemble.ROUTES, "loaded": sorted(ensemble._cache),
                                   "unavailable": ensemble._broken})
        self.reply(404, {"error": "not found"})

    def do_POST(self):
        # Browsers always send Origin on cross-site POSTs. A page from any other website could
        # otherwise make the phone upload junk here (CORS only hides the reply), so refuse it.
        origin = self.headers.get("Origin")
        if origin is not None and not origin_ok(origin):
            return self.reply(403, {"error": "origin not allowed"})
        if not self.path.startswith("/transcribe"):
            return self.reply(404, {"error": "not found"})
        n = int(self.headers.get("Content-Length", "0"))
        if n <= 0 or n > MAX_MB * 1024 * 1024:
            return self.reply(413, {"error": "file too large or empty"})
        try:
            fields, files = parse_form(self.headers, self.rfile.read(n))
            name, raw = files["file"]
        except Exception as e:
            return self.reply(400, {"error": f"bad upload: {e}"})

        # "lang" is the app's own tag (tsn, yue, cmn...); "language" the ASR hint. tsn wins so
        # Taishanese clips are labelled as such in the dataset even though they decode as yue.
        language = fields.get("lang") if fields.get("lang") == "tsn" else fields.get("language", "")
        if not re.fullmatch(r"[a-z]{2,3}(-[A-Za-z]{2,4})?|", language or ""):
            return self.reply(400, {"error": "bad language code"})
        engines = [e for e in dict.fromkeys(fields.get("engines", "").split(",")) if e in ("whisper", "buzzasr", "sensevoice")] or None
        suffix = os.path.splitext(name)[1] or ".m4a"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(raw)
            path = tmp.name
        try:
            t0 = time.time()
            with _gpu:
                result = ensemble.run(path, language, engines)
                if fields.get("translate") == "1":
                    result["segments"] = translate(result["segments"], result["language"])
            result.update(seconds=round(time.time() - t0, 1), model=MODEL)
            save(raw, name, result, result["language"])
            self.reply(200, result)
        except Exception as e:
            self.reply(500, {"error": str(e)})
        finally:
            os.unlink(path)


if __name__ == "__main__":
    print(f"Polylang home transcriber on :{PORT}  model={MODEL} device={DEVICE}  data={DATA_DIR}")
    # Load the engines in the background so the first real request isn't a 2-minute cold start.
    pre = [e for e in os.environ.get("POLYLANG_PRELOAD", "buzzasr,sensevoice,whisper").split(",") if e]
    threading.Thread(target=lambda: [ensemble.engine(e) for e in pre], daemon=True).start()
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
