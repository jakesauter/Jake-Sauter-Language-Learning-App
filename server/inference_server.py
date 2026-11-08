"""Polylang inference server: speech recognition, translation and live sessions on the GPU.

Listens only on a Unix socket. The Rust gateway (gateway/) is the single public entry point and
handles origins, CORS, rate limits and size caps; this server still validates its own inputs.

    GET  /health
    POST /transcribe   multipart: file, language, lang, translate (1/0), engines
    POST /translate    JSON {text, source, target}
    WS   /live         ?lang=yue&target=en, then binary 16 kHz mono Int16 PCM, text {"type":"stop"}
"""

import asyncio
import json
import os
import re
import tempfile
import threading
import time

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import accounts
import conversations
import email_sender
import ensemble
import live_session
import speech_engines
import translation

DATA_FOLDER = os.environ.get("POLYLANG_DATA", "/data")
SITE_FOLDER = os.environ.get("POLYLANG_SITE", "/site")
ALLOWED_ORIGINS = {origin.strip() for origin in os.environ.get("POLYLANG_ORIGINS", "https://jakesauter.github.io").split(",") if origin.strip()}
LANGUAGE_CODE = re.compile(r"(?:[a-z]{2,3})?")
MOST_WAITING_GPU_JOBS = 4

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
waiting_gpu_jobs = 0
live_session_lock = asyncio.Lock()


def origin_allowed(origin):
    return origin in ALLOWED_ORIGINS or re.fullmatch(r"http://(localhost|127\.0\.0\.1)(:\d+)?", origin or "") is not None


@app.middleware("http")
async def browser_origin_guard(request: Request, call_next):
    """Second line of defence behind the gateway: only Polylang's own pages may call from a browser."""
    origin = request.headers.get("origin")
    cors_headers = {}
    if origin and origin_allowed(origin):
        cors_headers = {"Access-Control-Allow-Origin": origin, "Vary": "Origin",
                        "Access-Control-Allow-Methods": "GET, POST, OPTIONS", "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Polylang-Device",
                        "Access-Control-Allow-Private-Network": "true", "Access-Control-Max-Age": "600"}
    if request.method == "OPTIONS":
        return Response(status_code=204 if cors_headers else 403, headers=cors_headers)
    if request.method != "GET" and origin is not None and not cors_headers:
        return JSONResponse({"error": "origin not allowed"}, 403)
    response = await call_next(request)
    response.headers.update(cors_headers)
    return response


def valid_engine_names(requested):
    names = [name for name in dict.fromkeys((requested or "").split(",")) if name in speech_engines.KNOWN_ENGINES]
    return names or None


async def queued_gpu_job(function, *arguments):
    global waiting_gpu_jobs
    if waiting_gpu_jobs >= MOST_WAITING_GPU_JOBS:
        raise OverflowError("GPU queue full")
    waiting_gpu_jobs += 1
    try:
        return await live_session.run_on_gpu(function, *arguments)
    finally:
        waiting_gpu_jobs -= 1


def data_folder_for(language):
    language_folder = language if re.fullmatch(r"[a-z]{2,3}", language or "") else "unknown"
    folder = os.path.join(DATA_FOLDER, language_folder, time.strftime("%Y-%m-%d"))
    if not os.path.realpath(folder).startswith(os.path.realpath(DATA_FOLDER) + os.sep):
        raise ValueError("refusing to write outside the data folder")
    os.makedirs(folder, exist_ok=True)
    return folder


def save_upload(audio_bytes, result):
    try:
        file_stem = os.path.join(data_folder_for(result.get("language")), time.strftime("%H%M%S") + "-upload")
        with open(file_stem + ".audio", "wb") as audio_file:
            audio_file.write(audio_bytes)
        with open(file_stem + ".json", "w", encoding="utf-8") as transcript_file:
            json.dump(result, transcript_file, ensure_ascii=False, indent=1)
    except (OSError, ValueError) as error:
        print("could not save upload:", error)


@app.get("/health")
async def health():
    return {"ok": True, "model": speech_engines.WHISPER_MODEL, "device": speech_engines.DEVICE,
            "llm": translation.choose_provider("yue", "en"), "routes": ensemble.ENGINES_BY_LANGUAGE,
            "loaded": speech_engines.loaded_engine_names(), "unavailable": speech_engines.failed_engines(),
            "google": bool(translation.google_key()), "live": True}


@app.post("/transcribe")
async def transcribe(request: Request):
    try:
        form = await request.form(max_files=1, max_fields=10)
    except Exception:
        return JSONResponse({"error": "bad upload"}, 400)
    upload = form.get("file")
    if upload is None or not hasattr(upload, "read"):
        return JSONResponse({"error": "no file"}, 400)
    language = "tsn" if form.get("lang") == "tsn" else str(form.get("language", ""))
    if not LANGUAGE_CODE.fullmatch(language):
        return JSONResponse({"error": "bad language code"}, 400)
    audio_bytes = await upload.read()
    with tempfile.NamedTemporaryFile(suffix=".audio", delete=False) as temporary_file:
        temporary_file.write(audio_bytes)
        audio_path = temporary_file.name
    started_at = time.time()
    try:
        result = await queued_gpu_job(ensemble.transcribe_file, audio_path, language,
                                      valid_engine_names(str(form.get("engines", ""))))
    except OverflowError:
        return JSONResponse({"error": "busy, try again shortly"}, 503)
    except Exception as error:
        return JSONResponse({"error": f"transcription failed: {type(error).__name__}"}, 500)
    finally:
        os.unlink(audio_path)
    if form.get("translate") == "1":
        for segment in result["segments"]:
            try:
                segment["en"] = (await translation.translate_text(segment["text"], result["language"], "en"))["text"]
            except Exception as error:
                segment["en_error"] = str(error)
    result.update(seconds=round(time.time() - started_at, 1), model=speech_engines.WHISPER_MODEL)
    save_upload(audio_bytes, result)
    return result


class TranslationRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    source: str = Field(default="", pattern=r"^(?:[a-z]{2,3})?$")
    target: str = Field(default="en", pattern=r"^[a-z]{2,3}$")


@app.post("/translate")
async def translate(request: TranslationRequest):
    try:
        return await translation.translate_text(request.text, request.source, request.target)
    except Exception as error:
        return JSONResponse({"error": f"translation failed: {error}"}, 502)


class Credentials(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=1, max_length=200)
    device_id: str = Field(default="", max_length=64)
    email: str = Field(default="", max_length=320)


def client_key(request):
    return request.headers.get("tailscale-user-login") or request.headers.get("x-forwarded-for") or "local"


async def finish_sign_in(request, credentials, create):
    loop = asyncio.get_running_loop()
    try:
        if create:
            signed_in = await loop.run_in_executor(None, accounts.create_account, credentials.username, credentials.password, credentials.email)
        else:
            signed_in = await loop.run_in_executor(None, accounts.sign_in, credentials.username, credentials.password, client_key(request))
    except accounts.AccountError as error:
        return JSONResponse({"error": str(error)}, 400 if create else 401)
    account = accounts.account_for_token(signed_in["token"])
    guest = conversations.person_from({k: v for k, v in request.headers.items() if k != "authorization"}, credentials.device_id)
    moved = conversations.move_everything(guest, f"account:{account['id']}")
    return {**signed_in, "moved_conversations": moved}


@app.post("/account/create")
async def create_account(request: Request, credentials: Credentials):
    return await finish_sign_in(request, credentials, create=True)


@app.post("/account/sign-in")
async def sign_in(request: Request, credentials: Credentials):
    return await finish_sign_in(request, credentials, create=False)


@app.post("/account/sign-out")
async def sign_out(request: Request):
    accounts.sign_out(accounts.bearer_token(request.headers))
    return {"ok": True}


@app.get("/account")
async def current_account(request: Request):
    account = accounts.account_for_token(accounts.bearer_token(request.headers))
    return {"signed_in": bool(account), "username": account["username"] if account else None,
            "email": account["email"] if account else None, "email_ready": email_sender.can_send(),
            "reset_mode": "trusted" if accounts.TRUSTED_RESET else ("email" if email_sender.can_send() else "none"),
            "tailscale_login": request.headers.get("tailscale-user-login")}


class EmailChange(BaseModel):
    email: str = Field(default="", max_length=320)


@app.post("/account/email")
async def change_email(request: Request, body: EmailChange):
    account = accounts.account_for_token(accounts.bearer_token(request.headers))
    if not account:
        return JSONResponse({"error": "Sign in first."}, 401)
    try:
        return {"email": accounts.set_email(account["id"], body.email)}
    except accounts.AccountError as error:
        return JSONResponse({"error": str(error)}, 400)


class ResetRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)


class ResetFinish(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")
    password: str = Field(min_length=1, max_length=200)


RESET_SENT = "If an account uses that email, a 6-digit code is on its way. It works for 15 minutes."


@app.post("/account/forgot-password")
async def forgot_password(request: Request, body: ResetRequest):
    if not email_sender.can_send():
        return JSONResponse({"error": "Password reset by email isn't set up yet."}, 503)
    found = accounts.start_password_reset(body.email, client_key(request))
    if found:
        address, code = found
        body_text = (f"Your Polylang password reset code is {code}\n\nIt works for 15 minutes. "
                     "If you didn't ask for this, you can ignore this email; your password hasn't changed.")
        try:
            await asyncio.get_running_loop().run_in_executor(None, email_sender.send, address, f"Polylang code: {code}", body_text)
        except Exception as error:
            print("reset email failed:", error)
    return {"message": RESET_SENT}


class TrustedReset(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=1, max_length=200)


@app.post("/account/reset-password-trusted")
async def reset_password_trusted(request: Request, body: TrustedReset):
    try:
        return await asyncio.get_running_loop().run_in_executor(
            None, accounts.trusted_password_reset, body.username, body.password, client_key(request))
    except accounts.AccountError as error:
        return JSONResponse({"error": str(error)}, 400)


@app.post("/account/reset-password")
async def reset_password(body: ResetFinish):
    try:
        return await asyncio.get_running_loop().run_in_executor(
            None, accounts.finish_password_reset, body.email, body.code, body.password)
    except accounts.AccountError as error:
        return JSONResponse({"error": str(error)}, 400)


@app.post("/live/ticket")
async def live_ticket(request: Request):
    return {"ticket": accounts.issue_live_ticket(conversations.person_from(request.headers))}


class NewConversation(BaseModel):
    title: str = Field(default="", max_length=120)
    languages: list[str] = Field(default_factory=list, max_length=6)


class ConversationTitle(BaseModel):
    title: str = Field(min_length=1, max_length=120)


@app.get("/conversations")
async def list_conversations(request: Request):
    return {"conversations": conversations.list_for(conversations.person_from(request.headers))}


@app.post("/conversations")
async def create_conversation(request: Request, body: NewConversation):
    languages = [code for code in body.languages if re.fullmatch(r"[a-z]{2,3}", code)]
    return conversations.create(conversations.person_from(request.headers), body.title, languages)


@app.get("/conversations/{conversation_id}")
async def get_conversation(request: Request, conversation_id: str):
    person = conversations.person_from(request.headers)
    if not conversations.exists(person, conversation_id):
        return JSONResponse({"error": "conversation not found"}, 404)
    return {**conversations.details(person, conversation_id), "lines": conversations.lines(person, conversation_id)}


@app.post("/conversations/{conversation_id}/title")
async def rename_conversation(request: Request, conversation_id: str, body: ConversationTitle):
    person = conversations.person_from(request.headers)
    if not conversations.exists(person, conversation_id):
        return JSONResponse({"error": "conversation not found"}, 404)
    return conversations.rename(person, conversation_id, body.title)


class ConversationLine(BaseModel):
    text: str = Field(max_length=500)
    en: str = Field(default="", max_length=800)


class SuggestionRequest(BaseModel):
    lines: list[ConversationLine] = Field(min_length=1, max_length=30)
    language: str = Field(default="yue", pattern=r"^[a-z]{2,3}$")
    creativity: float = Field(default=0.4, ge=0.0, le=1.0)


@app.post("/suggest")
async def suggest(request: SuggestionRequest):
    try:
        return await translation.suggest_replies([line.model_dump() for line in request.lines], request.language, request.creativity)
    except Exception as error:
        return JSONResponse({"error": f"suggestions failed: {error}"}, 502)


class RecapRequest(BaseModel):
    lines: list[ConversationLine] = Field(min_length=1, max_length=200)
    language: str = Field(default="yue", pattern=r"^[a-z]{2,3}$")


@app.post("/recap")
async def recap(request: RecapRequest):
    try:
        return await translation.recap_conversation([line.model_dump() for line in request.lines], request.language)
    except Exception as error:
        return JSONResponse({"error": f"recap failed: {error}"}, 502)


@app.websocket("/live")
async def live(websocket: WebSocket):
    origin = websocket.headers.get("origin")
    if origin is not None and not origin_allowed(origin):
        await websocket.close(code=1008)
        return
    requested_languages = websocket.query_params.get("languages") or websocket.query_params.get("lang", "")
    candidate_languages = list(dict.fromkeys(code for code in requested_languages.split(",") if code))[:6] or [""]
    language = candidate_languages[0]
    target_language = websocket.query_params.get("target", "en")
    if not all(LANGUAGE_CODE.fullmatch(code) for code in candidate_languages) or not LANGUAGE_CODE.fullmatch(target_language):
        await websocket.close(code=1008)
        return
    if live_session_lock.locked():
        await websocket.accept()
        await websocket.send_json({"type": "error", "error": "another live session is running on this computer"})
        await websocket.close(code=1013)
        return
    async with live_session_lock:
        await websocket.accept()
        engine_names = valid_engine_names(websocket.query_params.get("engines", ""))
        person = accounts.redeem_live_ticket(websocket.query_params.get("ticket")) or \
            conversations.person_from(websocket.headers, websocket.query_params.get("device", ""))
        conversation_id = websocket.query_params.get("conversation", "")
        if not conversations.exists(person, conversation_id):
            conversation_id = conversations.create(person, "", candidate_languages)["id"]
        session = live_session.LiveSession(websocket, candidate_languages, target_language, engine_names,
                                           websocket.query_params.get("save", "1") == "1", DATA_FOLDER,
                                           person, conversation_id)
        utterance_worker = asyncio.create_task(session.process_closed_utterances())
        await websocket.send_json({
            "type": "ready", "lang": language, "languages": candidate_languages, "target": target_language,
            "conversation": conversation_id,
            "provider": translation.choose_provider(language, target_language),
            "engines": engine_names or ensemble.ENGINES_BY_LANGUAGE.get(language, ensemble.DEFAULT_ENGINES)})
        try:
            while True:
                message = await asyncio.wait_for(websocket.receive(), timeout=60)
                if message["type"] == "websocket.disconnect":
                    break
                if message.get("bytes") is not None:
                    await session.receive_audio(message["bytes"])
                elif message.get("text"):
                    control = json.loads(message["text"])
                    if control.get("type") == "stop":
                        break
                    if control.get("type") == "settings":
                        session.apply_settings(control)
        except (WebSocketDisconnect, asyncio.TimeoutError, TimeoutError, ValueError):
            pass
        finally:
            await session.close()
            await utterance_worker
            await asyncio.get_running_loop().run_in_executor(None, session.save_recording)
            try:
                await websocket.send_json({"type": "end", "lines": len(session.finished_lines)})
                await websocket.close()
            except Exception:
                pass


@app.get("/")
async def to_app():
    return RedirectResponse("/app/")


if os.path.isdir(SITE_FOLDER):
    app.mount("/app", StaticFiles(directory=SITE_FOLDER, html=True), name="app")


@app.on_event("startup")
async def preload_engines():
    engine_names = [name for name in os.environ.get("POLYLANG_PRELOAD", "buzzasr,sensevoice,whisper").split(",") if name]
    threading.Thread(target=lambda: [speech_engines.get_engine(name) for name in engine_names], daemon=True).start()
