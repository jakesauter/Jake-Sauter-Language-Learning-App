"""Character error rate on the gold test set, using the same engine and settings as live mode (CTranslate2, beam 5).

    .venv/bin/python dataset/evaluate_ct2.py large-v3                          (stock model)
    .venv/bin/python dataset/evaluate_ct2.py /mnt/storage/models/whisper-yue-ct2  (fine-tuned, converted)
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "server"))
import jiwer  # noqa: E402
import soundfile  # noqa: E402
from faster_whisper import WhisperModel  # noqa: E402
from opencc import OpenCC  # noqa: E402

import speech_engines  # noqa: E402

DATASET_FOLDER = "/mnt/storage/datasets/youtube_cc_cantonese"
to_hong_kong = OpenCC("s2hk")


def comparable(text):
    return "".join(character for character in to_hong_kong.convert(text) if character.isalnum()).lower()


def main(model_path):
    segments = [json.loads(line) for line in open(os.path.join(DATASET_FOLDER, "gold_segments.jsonl"))]
    segments = [segment for segment in segments if segment["split"] == "test" and 0.5 < segment["end"] - segment["start"] <= 28]
    model = WhisperModel(model_path, device="cuda", compute_type="int8_float16")
    references, hypotheses, started = [], [], time.time()
    for segment in segments:
        audio, _ = soundfile.read(segment["audio"], start=int(segment["start"] * 16000), stop=int(segment["end"] * 16000), dtype="float32")
        text, _, _ = speech_engines.run_whisper(model, speech_engines.clean_audio(audio), "yue", with_words=False)
        if comparable(segment["text"]):
            references.append(comparable(segment["text"]))
            hypotheses.append(comparable(text))
    score = jiwer.cer(references, hypotheses)
    print(f"{model_path}: CER {score:.1%} on {len(references)} gold clips ({time.time() - started:.0f}s)")
    for reference, hypothesis in list(zip(references, hypotheses))[:4]:
        print(f"   ref {reference[:36]}\n   got {hypothesis[:36]}")


if __name__ == "__main__":
    main(sys.argv[1])
