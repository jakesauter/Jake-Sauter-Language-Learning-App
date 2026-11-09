"""Compare Cantonese transcription variants on real saved dinner audio, judged for coherence by the local LLM."""
import glob, json, random, urllib.request
import numpy as np
import scipy.signal
import speech_engines, live_session

def judge(text):
    prompt = ("Rate from 1 to 5 how much this speech-recognition output reads like real, meaningful spoken Cantonese "
              "(5 = clear natural sentence, 1 = gibberish or random characters). Reply with only the number.\n\n" + text)
    body = json.dumps({"model": "qwen2.5:7b", "stream": False, "keep_alive": "4h", "options": {"temperature": 0, "num_ctx": 2048},
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    reply = json.load(urllib.request.urlopen(urllib.request.Request("http://127.0.0.1:11434/api/chat", body, {"Content-Type": "application/json"}), timeout=120))
    digits = [c for c in reply["message"]["content"] if c.isdigit()]
    return int(digits[0]) if digits else 1

def cleaned(audio):
    filtered = scipy.signal.sosfilt(scipy.signal.butter(4, 120, "highpass", fs=16000, output="sos"), audio)
    rms = np.sqrt(np.mean(filtered ** 2)) + 1e-9
    return np.clip(filtered * (0.08 / rms), -1, 1).astype(np.float32)

model = speech_engines.get_engine("sensevoice")
pieces = []
for path in sorted(glob.glob("/mnt/storage/polylang-data/people/*/conversations/*/recordings/*.wav")):
    audio = speech_engines.decode_audio_file(path)
    for start, end in live_session.pieces_for_language_detection(audio):
        piece = audio[start:end]
        if speech_engines.run_sensevoice(model, piece, "")[2] in ("yue", "zh"):
            pieces.append(piece)
random.seed(7)
sample = random.sample(pieces, min(30, len(pieces)))
print(f"Chinese pieces found in dinner audio: {len(pieces)}; judging a random {len(sample)}")
variants = {
    "A current (told Cantonese)": lambda piece: speech_engines.run_sensevoice(model, piece, "yue")[0],
    "B auto language": lambda piece: speech_engines.run_sensevoice(model, piece, "")[0],
    "C cleaned audio + Cantonese": lambda piece: speech_engines.run_sensevoice(model, cleaned(piece), "yue")[0],
}
for name, transcribe in variants.items():
    scores = [judge(speech_engines.to_common_script(transcribe(piece), "yue") or "(empty)") for piece in sample]
    print(f"{name:30s} mean coherence {np.mean(scores):.2f}  (5s: {scores.count(5)}, 1s: {scores.count(1)})")
