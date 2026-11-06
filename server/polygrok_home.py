"""Polygrok home transcriber.

Runs on your own computer, so there is no cloud bill. Phones reach it privately over Tailscale.

    POST /transcribe   multipart: file, language (yue, zh, es, fr, de, en or blank), translate (1/0)
    GET  /health

Every upload and its transcript is saved under DATA_DIR. Those files are the start
of a Taishanese speech dataset that you can correct and fine-tune on later.
"""

import json
import os
import tempfile
import threading
import time
import urllib.request
from email.parser import BytesParser
from email.policy import default as email_policy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


MODEL = os.environ.get("POLYGROK_MODEL", "large-v3")
DEVICE = os.environ.get("POLYGROK_DEVICE", "cuda")
COMPUTE = os.environ.get("POLYGROK_COMPUTE", "int8_float16")
PORT = int(os.environ.get("POLYGROK_PORT", "8000"))
DATA_DIR = os.environ.get("POLYGROK_DATA", os.path.expanduser("~/polygrok-data"))
OLLAMA = os.environ.get("POLYGROK_OLLAMA", "http://127.0.0.1:11434")
LLM = os.environ.get("POLYGROK_LLM", "qwen2.5:7b")
MAX_MB = int(os.environ.get("POLYGROK_MAX_MB", "200"))

ORIGINS = [o.strip() for o in os.environ.get(
    "POLYGROK_ORIGINS",
    "https://jakesauter.github.io",
).split(",") if o.strip()]

ORIGIN_SUFFIXES = (".claudeusercontent.com", ".claude.ai")


_model = None
_gpu = threading.Lock()


def model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        _model = WhisperModel(MODEL, device=DEVICE, compute_type=COMPUTE)
    return _model


def transcribe(path, language):
    segs, info = model().transcribe(
        path,
        language=language or None,
        vad_filter=True,
        beam_size=5,
        condition_on_previous_text=False,
    )
    out = [{"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()} for s in segs]
    return out, info.language


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


def save(raw, name, result):
    day = time.strftime("%Y-%m-%d")
    d = os.path.join(DATA_DIR, day)
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
        ok = origin in ORIGINS or origin.endswith(ORIGIN_SUFFIXES) or origin.startswith("http://localhost")
        if ok:
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
            return self.reply(200, {"ok": True, "model": MODEL, "device": DEVICE, "llm": LLM})
        self.reply(404, {"error": "not found"})

    def do_POST(self):
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

        language = fields.get("language", "")
        suffix = os.path.splitext(name)[1] or ".m4a"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(raw)
            path = tmp.name
        try:
            t0 = time.time()
            with _gpu:
                segments, detected = transcribe(path, language)
                if fields.get("translate") == "1":
                    segments = translate(segments, detected)
            result = {"language": detected, "segments": segments, "seconds": round(time.time() - t0, 1), "model": MODEL}
            save(raw, name, result)
            self.reply(200, result)
        except Exception as e:
            self.reply(500, {"error": str(e)})
        finally:
            os.unlink(path)


if __name__ == "__main__":
    print(f"Polygrok home transcriber on :{PORT}  model={MODEL} device={DEVICE}  data={DATA_DIR}")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
