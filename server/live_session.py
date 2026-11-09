"""Live transcription and translation for one WebSocket connection.

The phone streams raw 16 kHz mono Int16 PCM, so no audio decoder ever touches untrusted bytes.
Every ~300 ms of new audio, voice-activity detection runs on the open utterance:
  - while someone is talking, a fast engine re-transcribes it about every 700 ms   -> "partial"
  - after ~600 ms of silence (or 20 s of speech) the utterance is closed, the full
    engine ensemble runs on it                                                    -> "final"
  - the translation then streams back piece by piece                              -> "translation"
"""

import asyncio
import json
import os
import re
import time
import wave

import numpy as np

import conversations
import ensemble
import speakers
import speech_engines
import translation
from speech_engines import SAMPLE_RATE

SECONDS_BETWEEN_VAD_CHECKS = 0.3
SECONDS_BETWEEN_PARTIALS = 0.7
SILENCE_THAT_ENDS_UTTERANCE = 0.6   # default; each session can tune it between the two limits below
SHORTEST_ENDING_SILENCE, LONGEST_ENDING_SILENCE = 0.3, 1.5
LONGEST_UTTERANCE_SECONDS = 20.0
LONGEST_SESSION_SECONDS = 2 * 3600
LARGEST_FRAME_BYTES = 64 * 1024


def run_on_gpu(function, *arguments):
    """Run blocking GPU work in a worker thread, one job at a time across the whole server."""
    def with_gpu_lock():
        with speech_engines.gpu_lock:
            return function(*arguments)
    return asyncio.get_running_loop().run_in_executor(None, with_gpu_lock)


SHORTEST_DETECTION_PIECE_SECONDS = 1.5


def pieces_for_language_detection(audio):
    """Cut at pauses of a quarter second, then join neighbours until each piece is long enough to judge its language."""
    regions = speech_engines.speech_regions(audio, min_silence_ms=250, max_speech_seconds=12, padding_ms=80, min_speech_ms=200)
    if not regions:
        return [(0, len(audio))]
    pieces = []
    for region_start, region_end in regions:
        if pieces and (pieces[-1][1] - pieces[-1][0]) / SAMPLE_RATE < SHORTEST_DETECTION_PIECE_SECONDS:
            pieces[-1] = (pieces[-1][0], region_end)
        else:
            pieces.append((region_start, region_end))
    if len(pieces) > 1 and (pieces[-1][1] - pieces[-1][0]) / SAMPLE_RATE < 1.0:
        last_start, last_end = pieces.pop()
        pieces[-1] = (pieces[-1][0], last_end)
    return pieces


def find_speech(audio, ending_silence=SILENCE_THAT_ENDS_UTTERANCE):
    return speech_engines.speech_regions(
        audio, min_silence_ms=int(ending_silence * 800), max_speech_seconds=30,
        padding_ms=100, min_speech_ms=150)


class LiveSession:
    def __init__(self, websocket, candidate_languages, target_language="en", engine_names=None, keep_recording=True,
                 data_folder=None, person=None, conversation_id=None):
        self.websocket = websocket
        self.person = person
        self.conversation_id = conversation_id
        self.candidate_languages = list(candidate_languages) or [""]
        self.language = self.candidate_languages[0]
        self.target_language = target_language
        self.engine_names = engine_names
        self.keep_recording = keep_recording
        self.data_folder = data_folder
        self.open_utterance = np.zeros(0, np.float32)
        self.open_utterance_starts_at = 0.0
        self.received_frames = []
        self.samples_since_vad_check = 0
        self.last_partial_at = 0.0
        self.partial_in_progress = False
        self.started_at = time.time()
        self.closed_utterances = asyncio.Queue()
        self.finished_lines = []
        self.line_count = 0
        self.is_closing = False
        self.ending_silence = SILENCE_THAT_ENDS_UTTERANCE
        self.speaker_tracker = speakers.SpeakerTracker()

    def apply_settings(self, settings):
        """Tune the session while it runs, e.g. {"pause_ms": 900}."""
        pause_ms = settings.get("pause_ms")
        if isinstance(pause_ms, (int, float)):
            self.ending_silence = min(LONGEST_ENDING_SILENCE, max(SHORTEST_ENDING_SILENCE, pause_ms / 1000))

    async def send(self, message):
        try:
            await self.websocket.send_text(json.dumps(message, ensure_ascii=False))
        except Exception:
            pass  # the phone went away; the session still finishes and saves

    # ---------- incoming audio ----------

    async def receive_audio(self, frame: bytes):
        if len(frame) > LARGEST_FRAME_BYTES or len(frame) % 2:
            await self.send({"type": "error", "error": "bad audio frame"})
            return
        if time.time() - self.started_at > LONGEST_SESSION_SECONDS:
            raise TimeoutError("session too long")
        samples = np.frombuffer(frame, dtype="<i2")
        self.received_frames.append(samples.copy())
        self.open_utterance = np.concatenate([self.open_utterance, samples.astype(np.float32) / 32768.0])
        self.samples_since_vad_check += len(samples)
        if self.samples_since_vad_check >= SECONDS_BETWEEN_VAD_CHECKS * SAMPLE_RATE:
            self.samples_since_vad_check = 0
            await self.check_for_speech()

    async def check_for_speech(self, end_of_stream=False):
        audio = self.open_utterance
        speech = await asyncio.get_running_loop().run_in_executor(None, find_speech, audio, self.ending_silence)
        if not speech:
            if len(audio) > 3 * SAMPLE_RATE:
                self._drop_audio_before(len(audio) - SAMPLE_RATE)
            return
        speech_start, speech_end = speech[0][0], speech[-1][1]
        trailing_silence = (len(audio) - speech_end) / SAMPLE_RATE
        utterance_length = (len(audio) - speech_start) / SAMPLE_RATE
        if end_of_stream or trailing_silence >= self.ending_silence or utterance_length >= LONGEST_UTTERANCE_SECONDS:
            padding = int(0.15 * SAMPLE_RATE)
            clip_from, clip_to = max(0, speech_start - padding), min(len(audio), speech_end + padding)
            await self.closed_utterances.put(
                (audio[clip_from:clip_to].copy(), self.open_utterance_starts_at + clip_from / SAMPLE_RATE, time.time()))
            self._drop_audio_before(speech_end)
            self.last_partial_at = 0.0
            await self.send({"type": "partial", "text": ""})
        elif time.time() - self.last_partial_at >= SECONDS_BETWEEN_PARTIALS and not self.partial_in_progress:
            self.last_partial_at = time.time()
            self.partial_in_progress = True
            asyncio.create_task(self.send_partial(audio[max(0, speech_start - int(0.1 * SAMPLE_RATE)):].copy()))

    def _drop_audio_before(self, sample_index):
        self.open_utterance = self.open_utterance[sample_index:]
        self.open_utterance_starts_at += sample_index / SAMPLE_RATE

    async def send_partial(self, audio):
        try:
            started_at = time.time()
            text = await run_on_gpu(speech_engines.quick_transcript, audio, self.language, self.candidate_languages)
            await self.send({"type": "partial", "text": text, "ms": round((time.time() - started_at) * 1000)})
        except Exception as error:
            await self.send({"type": "error", "error": f"partial: {error}"})
        finally:
            self.partial_in_progress = False

    # ---------- finished utterances, in order ----------

    async def process_closed_utterances(self):
        while True:
            utterance = await self.closed_utterances.get()
            if utterance is None:
                return
            try:
                await self.finish_utterance(*utterance)
            except Exception as error:
                await self.send({"type": "error", "error": f"final: {error}"})

    def detect_and_transcribe(self, audio, starts_at):
        """Split at short pauses first, so a Cantonese stretch followed by English isn't judged as one language."""
        transcribed_pieces = []
        for piece_start, piece_end in pieces_for_language_detection(audio):
            piece = speech_engines.clean_audio(audio[piece_start:piece_end])
            language, confidence = speech_engines.detect_language(piece, self.candidate_languages)
            result = ensemble.transcribe_audio(piece, language, self.engine_names, starts_at + piece_start / SAMPLE_RATE, False)
            try:
                result["speaker"], result["speaker_similarity"] = self.speaker_tracker.identify(piece)
            except Exception as error:
                result["speaker"], result["speaker_similarity"] = None, 0.0
                print("speaker identification failed:", error)
            transcribed_pieces.append((language, confidence, result))
        return transcribed_pieces

    def translation_source_for(self, language):
        # Cantonese and Taishanese sound alike to every model; tell the translator it may be Taishanese.
        if language == "yue" and "tsn" in self.candidate_languages:
            return "tsn"
        return language

    async def finish_utterance(self, audio, starts_at, closed_at):
        started_at = time.time()
        transcribed_pieces = await run_on_gpu(self.detect_and_transcribe, audio, starts_at)
        for language, confidence, result in transcribed_pieces:
            if result["segments"] and result["segments"][0]["text"]:
                await self.finish_piece(language, confidence, result, started_at, closed_at)

    async def finish_piece(self, language, confidence, result, started_at, closed_at):
        segment = result["segments"][0]
        engine_versions = [text for text in segment.get("hyps", {}).values() if text]
        if language != "en" and translation.mostly_latin(segment["text"]):
            language = "en"
        if language != "en" and len(set(engine_versions)) > 1:
            try:
                fused = await translation.fuse_transcripts(engine_versions, language)
                import speech_engines as engines_for_script
                segment = {**segment, "text": engines_for_script.to_common_script(fused, language), "fused": True,
                           "spans": [{"text": engines_for_script.to_common_script(fused, language)}]}
            except Exception as error:
                print("fusion failed:", error)
        self.line_count += 1
        line_id = self.line_count
        line = {
            "type": "final", "id": line_id, **segment, "engines": result["engines"],
            "language": language, "language_confidence": confidence, "speaker": result.get("speaker"),
            "could_be": [code for code in self.candidate_languages if speech_engines.SPEECH_FAMILY.get(code, code) == speech_engines.SPEECH_FAMILY.get(language, language)],
            "stats": {
                "asr_ms": round((time.time() - started_at) * 1000),
                "engine_ms": {name: round(seconds * 1000) for name, seconds in result["engine_seconds"].items()},
                "since_speech_end_ms": round((time.time() - closed_at + self.ending_silence) * 1000),
            },
        }
        await self.send(line)
        if self.target_language and language != self.target_language:
            line["en"], line["clarity"] = await self.translate_with_clarity(line_id, segment["text"], self.translation_source_for(language))
        self.finished_lines.append(line)
        if self.conversation_id:
            saved_line = {key: line[key] for key in ("text", "en", "clarity", "language", "could_be", "speaker", "spans", "hyps", "agree", "start", "end") if key in line}
            saved_line["at"] = self.started_at + line["start"]
            await asyncio.get_running_loop().run_in_executor(
                None, conversations.append_line, self.person, self.conversation_id, saved_line)

    async def translate_with_clarity(self, line_id, text, source_language):
        started_at = time.time()
        earlier_lines = [line["text"] + (f" (meaning: {line['en']})" if line.get("en") and line["en"] != "(unclear)" else "")
                         for line in self.finished_lines[-4:]]
        try:
            result = await translation.translate_with_clarity(text, source_language, self.target_language, earlier_lines)
        except Exception as error:
            await self.send({"type": "translation", "id": line_id, "done": True, "error": str(error)})
            return "", None
        await self.send({"type": "translation", "id": line_id, "done": True, "text": result["english"], "clarity": result["clarity"],
                         "unclear": result["unclear"], "ms": round((time.time() - started_at) * 1000)})
        return result["english"], result["clarity"]

    async def stream_translation_of(self, line_id, text, source_language, heard_versions=()):
        started_at = time.time()
        first_piece_ms, pieces = None, []
        provider = translation.choose_provider(source_language, self.target_language)
        try:
            earlier_lines = [line["text"] + (f" (meaning: {line['en']})" if line.get("en") else "") for line in self.finished_lines[-4:]]
            async for piece in translation.stream_translation(text, source_language, self.target_language, provider, earlier_lines, heard_versions):
                if first_piece_ms is None:
                    first_piece_ms = round((time.time() - started_at) * 1000)
                pieces.append(piece)
                await self.send({"type": "translation", "id": line_id, "delta": piece})
        except Exception as error:
            await self.send({"type": "translation", "id": line_id, "done": True, "error": str(error)})
            return ""
        translated = "".join(pieces).strip()
        await self.send({"type": "translation", "id": line_id, "done": True, "text": translated, "provider": provider,
                         "first_ms": first_piece_ms, "ms": round((time.time() - started_at) * 1000)})
        return translated

    # ---------- ending ----------

    async def close(self):
        if self.is_closing:
            return
        self.is_closing = True
        if len(self.open_utterance) > SAMPLE_RATE // 4:
            try:
                await self.check_for_speech(end_of_stream=True)
            except Exception:
                pass
        await self.closed_utterances.put(None)

    def save_recording(self):
        if not (self.keep_recording and self.data_folder and self.received_frames):
            return
        if self.conversation_id:
            self._write_wav(conversations.recording_path(self.person, self.conversation_id))
            return
        language_folder = self.language if re.fullmatch(r"[a-z]{2,3}", self.language or "") else "unknown"
        folder = os.path.join(self.data_folder, language_folder, time.strftime("%Y-%m-%d"))
        if not os.path.realpath(folder).startswith(os.path.realpath(self.data_folder) + os.sep):
            return
        os.makedirs(folder, exist_ok=True)
        file_stem = os.path.join(folder, time.strftime("%H%M%S") + "-live")
        self._write_wav(file_stem + ".wav")
        with open(file_stem + ".json", "w", encoding="utf-8") as transcript_file:
            json.dump({"languages": self.candidate_languages, "target": self.target_language, "lines": self.finished_lines},
                      transcript_file, ensure_ascii=False, indent=1)

    def _write_wav(self, path):
        with wave.open(path, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(SAMPLE_RATE)
            wav_file.writeframes(np.concatenate(self.received_frames).tobytes())
