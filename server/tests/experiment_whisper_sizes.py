"""Whisper turbo (used live) vs large-v3 on 100 dinner Chinese pieces; phase 'transcribe' then 'judge'."""
import glob, json, random, sys, urllib.request
import numpy as np
import speech_engines, live_session
from faster_whisper import WhisperModel

STORE = "/mnt/storage/polylang-data/experiments/whisper_sizes.json"

def judge(text):
    prompt = ("Rate from 1 to 5 how much this speech-recognition output reads like real, meaningful spoken Cantonese "
              "(5 = clear natural sentence, 1 = gibberish or random characters). Reply with only the number.\n\n" + (text or "(empty)"))
    body = json.dumps({"model": "qwen2.5:7b", "stream": False, "options": {"temperature": 0, "num_ctx": 2048},
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    reply = json.load(urllib.request.urlopen(urllib.request.Request("http://127.0.0.1:11434/api/chat", body, {"Content-Type": "application/json"}), timeout=120))
    digits = [c for c in reply["message"]["content"] if c.isdigit()]
    return int(digits[0]) if digits else 1

if sys.argv[1] == "transcribe":
    sensevoice = speech_engines.get_engine("sensevoice")
    models = {"turbo": WhisperModel("mobiuslabsgmbh/faster-whisper-large-v3-turbo", device="cuda", compute_type="int8_float16"),
              "large-v3": WhisperModel("large-v3", device="cuda", compute_type="int8_float16")}
    pieces = []
    for path in sorted(glob.glob("/mnt/storage/polylang-data/people/*/conversations/*/recordings/*.wav")):
        audio = speech_engines.decode_audio_file(path)
        for start, end in live_session.pieces_for_language_detection(audio):
            piece = speech_engines.clean_audio(audio[start:end])
            if speech_engines.run_sensevoice(sensevoice, piece, "")[2] in ("yue", "zh"):
                pieces.append(piece)
    random.seed(11)
    rows = [{name: speech_engines.to_common_script(speech_engines.run_whisper(model, piece, "yue", with_words=False)[0], "yue")
             for name, model in models.items()} for piece in random.sample(pieces, 100)]
    json.dump(rows, open(STORE, "w"), ensure_ascii=False)
    print("transcribed", len(rows))
else:
    rows = json.load(open(STORE))
    for name in ("turbo", "large-v3"):
        scores = [judge(row[name]) for row in rows]
        print(f"{name:9s} mean {np.mean(scores):.2f}  clear (5): {scores.count(5)}  gibberish (1): {scores.count(1)}")
