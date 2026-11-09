"""Score each speech engine (and an LLM fusion of all of them) on real dinner audio, judged for coherence by the local LLM."""
import glob, json, random, time, urllib.request
import numpy as np
import speech_engines, live_session
from faster_whisper import WhisperModel

def chat(prompt, temperature=0.0):
    body = json.dumps({"model": "qwen2.5:7b", "stream": False, "keep_alive": "2h", "options": {"temperature": temperature, "num_ctx": 2048},
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    return json.load(urllib.request.urlopen(urllib.request.Request("http://127.0.0.1:11434/api/chat", body, {"Content-Type": "application/json"}), timeout=180))["message"]["content"].strip()

def judge(text):
    reply = chat("Rate from 1 to 5 how much this speech-recognition output reads like real, meaningful spoken Cantonese "
                 "(5 = clear natural sentence, 1 = gibberish or random characters). Reply with only the number.\n\n" + (text or "(empty)"))
    digits = [c for c in reply if c.isdigit()]
    return int(digits[0]) if digits else 1

def fuse(versions):
    listed = "\n".join(f"{index + 1}. {text}" for index, text in enumerate(versions) if text)
    return chat("Several speech recognizers transcribed the same short clip of spoken Cantonese at a noisy family dinner. "
                "Write the single most likely thing that was actually said, in Cantonese written with traditional characters. "
                "Reply with only that sentence.\n\n" + listed)

import sys
VERSIONS_FILE = "/mnt/storage/polylang-data/experiments/engine_versions.json"
if sys.argv[1:] == ["transcribe"]:
    sensevoice = speech_engines.get_engine("sensevoice")
    buzzasr = speech_engines.get_engine("buzzasr")
    whisper_large = WhisperModel("large-v3", device="cuda", compute_type="int8_float16")
    pieces = []
    for path in sorted(glob.glob("/mnt/storage/polylang-data/people/*/conversations/*/recordings/*.wav")):
        audio = speech_engines.decode_audio_file(path)
        for start, end in live_session.pieces_for_language_detection(audio):
            piece = speech_engines.clean_audio(audio[start:end])
            if speech_engines.run_sensevoice(sensevoice, piece, "")[2] in ("yue", "zh"):
                pieces.append(piece)
    random.seed(11)
    sample = random.sample(pieces, min(100, len(pieces)))
    print(f"Chinese pieces in dinner audio: {len(pieces)}; transcribing {len(sample)}", flush=True)
    rows = []
    for piece in sample:
        versions = {
            "SenseVoice": speech_engines.run_sensevoice(sensevoice, piece, "yue")[0],
            "BuzzASR": speech_engines.run_whisper(buzzasr, piece, "yue", with_words=False)[0],
            "Whisper large-v3": speech_engines.run_whisper(whisper_large, piece, "yue", with_words=False)[0],
        }
        rows.append({name: speech_engines.to_common_script(text, "yue") for name, text in versions.items()})
    import os
    os.makedirs(os.path.dirname(VERSIONS_FILE), exist_ok=True)
    json.dump(rows, open(VERSIONS_FILE, "w"), ensure_ascii=False)
else:
    rows = json.load(open(VERSIONS_FILE))
    results = {name: [] for name in ("SenseVoice", "BuzzASR", "Whisper large-v3", "LLM fusion of all three")}
    started = time.time()
    for versions in rows:
        versions["LLM fusion of all three"] = speech_engines.to_common_script(fuse(list(versions.values())), "yue")
        for name, text in versions.items():
            results[name].append(judge(text))
    for name, scores in sorted(results.items(), key=lambda item: -np.mean(item[1])):
        print(f"{name:26s} mean {np.mean(scores):.2f}   clear (5): {scores.count(5):3d}   gibberish (1): {scores.count(1):3d}", flush=True)
    print(f"judging took {time.time() - started:.0f}s", flush=True)
