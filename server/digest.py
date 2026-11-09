"""Digest a conversation after it ends: the full offline pipeline over all of its recordings.

    clean audio -> pieces -> language -> SenseVoice + Whisper -> LLM fusion
    -> speakers grouped over the whole conversation (Ward) -> translation with surrounding context

Runs automatically when a live session ends, one conversation at a time, and waits while anyone is
recording live so it never slows the live translation. Results go to digest.jsonl next to lines.jsonl.
"""

import asyncio
import datetime
import glob
import json
import os
import time
import wave

import numpy as np

import conversations
import live_session
import speakers
import speech_engines
import translation

CANDIDATE_LANGUAGES = ["yue", "tsn", "zh", "en"]
MOST_SPEAKERS = 6
LINES_PER_EXTRA_SPEAKER = 25

_queue = asyncio.Queue()
_queued = set()


def digest_path(person, conversation_id):
    return os.path.join(conversations.conversation_folder(person, conversation_id), "digest.jsonl")


def set_status(person, conversation_id, status, **details):
    folder = conversations.conversation_folder(person, conversation_id)
    conversation = conversations.details(person, conversation_id)
    conversation["digest"] = {"status": status, "updated": time.time(), **details}
    conversations._write_details(folder, conversation)


def digested_lines(person, conversation_id):
    path = digest_path(person, conversation_id)
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as file:
        return [json.loads(row) for row in file if row.strip()]


def request_digest(person, conversation_id):
    if (person, conversation_id) not in _queued:
        _queued.add((person, conversation_id))
        set_status(person, conversation_id, "waiting")
        _queue.put_nowait((person, conversation_id))


async def digest_worker(live_session_lock):
    while True:
        person, conversation_id = await _queue.get()
        try:
            while live_session_lock.locked():  # never compete with someone recording live
                await asyncio.sleep(5)
            await digest(person, conversation_id)
        except Exception as error:
            print("digest failed:", error)
            set_status(person, conversation_id, "failed", error=str(error)[:200])
        finally:
            _queued.discard((person, conversation_id))


def _recording_start(path):
    with wave.open(path) as wav_file:
        seconds = wav_file.getnframes() / wav_file.getframerate()
    saved_at = datetime.datetime.strptime(os.path.basename(path)[:-4], "%Y-%m-%d_%H%M%S")
    return saved_at.timestamp() - seconds


def _listen(person, conversation_id):
    """GPU part: every piece of every recording, transcribed by each engine, with a voice fingerprint."""
    folder = conversations.conversation_folder(person, conversation_id)
    recordings = sorted(glob.glob(os.path.join(folder, "recordings", "*.wav")))
    candidates = conversations.details(person, conversation_id).get("languages") or CANDIDATE_LANGUAGES
    pieces = []
    for path in recordings:
        audio = speech_engines.decode_audio_file(path)
        started = _recording_start(path)
        for piece_start, piece_end in live_session.pieces_for_language_detection(audio):
            piece = speech_engines.clean_audio(audio[piece_start:piece_end])
            with speech_engines.gpu_lock:
                language, _ = speech_engines.detect_language(piece, candidates)
                versions = {}
                for engine_name in ("sensevoice", "whisper"):
                    result = speech_engines.transcribe_with(engine_name, piece, language)
                    if result and result["text"]:
                        versions[engine_name] = speech_engines.to_common_script(result["text"], language)
            if not versions:
                continue
            seconds = (piece_end - piece_start) / speech_engines.SAMPLE_RATE
            pieces.append({"at": started + piece_start / speech_engines.SAMPLE_RATE, "seconds": round(seconds, 2),
                           "language": language, "hyps": versions,
                           "fingerprint": speakers.voice_fingerprint(piece).tolist() if seconds >= 0.5 else None})
    return pieces


def _group_speakers(pieces):
    from scipy.cluster.hierarchy import fcluster, linkage
    voiced = [index for index, piece in enumerate(pieces) if piece["fingerprint"] and piece["seconds"] >= 1.0]
    if len(voiced) < 4:
        return
    fingerprints = np.array([pieces[index]["fingerprint"] for index in voiced])
    speaker_count = max(1, min(MOST_SPEAKERS, len(voiced) // LINES_PER_EXTRA_SPEAKER + 1))
    groups = fcluster(linkage(fingerprints, method="ward"), t=speaker_count, criterion="maxclust")
    sizes = {group: list(groups).count(group) for group in set(groups)}
    number = {group: rank + 1 for rank, group in enumerate(sorted(sizes, key=lambda group: -sizes[group]))}
    centroids = {group: fingerprints[groups == group].mean(axis=0) for group in sizes}
    for piece in pieces:
        if piece["fingerprint"]:
            closest = max(centroids, key=lambda group: float(np.dot(piece["fingerprint"], centroids[group]) / np.linalg.norm(centroids[group])))
            piece["speaker"] = number[closest]


async def free_gpu_from_translator():
    """Nobody is recording live during a digest, so the translator can leave the GPU while Whisper listens."""
    import httpx
    model = translation.choose_provider("yue", "en").split(":", 1)[-1]
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            await client.post(translation.OLLAMA_URL + "/api/generate", json={"model": model, "keep_alive": 0})
    except Exception as error:
        print("could not unload translator:", error)


async def digest(person, conversation_id):
    set_status(person, conversation_id, "listening")
    await free_gpu_from_translator()
    pieces = await asyncio.get_running_loop().run_in_executor(None, _listen, person, conversation_id)
    _group_speakers(pieces)
    set_status(person, conversation_id, "understanding", total=len(pieces))
    lines = []
    for index, piece in enumerate(pieces):
        versions = list(piece["hyps"].values())
        if piece["language"] != "en" and translation.mostly_latin(piece["hyps"].get("whisper", "")):
            piece["language"] = "en"
        understood = None
        if piece["language"] == "en":
            text = piece["hyps"].get("whisper") or versions[0]
        else:
            earlier = [entry["text"] + (f" (meaning: {entry['en']})" if entry["en"] and entry["en"] != "(unclear)" else "") for entry in lines[-4:]]
            source = "tsn" if piece["language"] == "yue" else piece["language"]
            understood = await translation.understand_line(versions, source, "en", earlier)
            text = speech_engines.fix_cantonese_variants(speech_engines.to_common_script(understood["said"], piece["language"]))
        line = {"text": text, "language": piece["language"], "speaker": piece.get("speaker"), "hyps": piece["hyps"],
                "at": piece["at"], "start": 0, "end": piece["seconds"], "en": "",
                "could_be": ["yue", "tsn"] if piece["language"] == "yue" else [piece["language"]]}
        if understood:
            line["en"], line["clarity"] = understood["english"], understood["clarity"]
        lines.append(line)
        if index % 20 == 0:
            set_status(person, conversation_id, "understanding", done=index, total=len(pieces))
    temporary = digest_path(person, conversation_id) + ".tmp"
    with open(temporary, "w", encoding="utf-8") as file:
        for line in lines:
            file.write(json.dumps(line, ensure_ascii=False) + "\n")
    os.replace(temporary, digest_path(person, conversation_id))
    set_status(person, conversation_id, "done", lines=len(lines),
               speakers=len({line["speaker"] for line in lines if line["speaker"]}))
