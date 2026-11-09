"""High-precision pseudo-labels for downloaded videos without usable subtitles ("noisy student" self-training).

Each speech piece is transcribed by SenseVoice and Whisper large-v3, two very different models. A piece becomes
training data only when it is Cantonese and both models produce nearly the same text (character agreement >= 0.85),
because independent models rarely make the same mistake. Resumable: videos already labeled are skipped.

    ~/Documents/Projects/language-learning-app/.venv/bin/python dataset/pseudo_label.py
"""

import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "server"))
os.environ.setdefault("POLYLANG_MODEL", "large-v3")

import ensemble  # noqa: E402
import live_session  # noqa: E402
import speech_engines  # noqa: E402

DATASET_FOLDER = "/mnt/storage/datasets/youtube_cc_cantonese"
OUTPUT_FILE = os.path.join(DATASET_FOLDER, "pseudo_segments.jsonl")
DONE_FILE = os.path.join(DATASET_FOLDER, "pseudo_done.txt")
SMALLEST_AGREEMENT = 0.85
MOST_PIECES_PER_VIDEO = 150   # spread labels across many speakers instead of a few long videos
FEWEST_CHARACTERS = 4


def labeled_videos():
    return set(open(DONE_FILE).read().split()) if os.path.exists(DONE_FILE) else set()


def videos_with_gold_subtitles():
    path = os.path.join(DATASET_FOLDER, "gold_segments.jsonl")
    return {json.loads(line)["video"] for line in open(path)} if os.path.exists(path) else set()


def label_video(record):
    audio = speech_engines.decode_audio_file(os.path.join(DATASET_FOLDER, "audio", f"{record['id']}.wav"))
    sensevoice, whisper = speech_engines.get_engine("sensevoice"), speech_engines.get_engine("whisper")
    kept, pieces = [], live_session.pieces_for_language_detection(audio)
    if len(pieces) > MOST_PIECES_PER_VIDEO:
        pieces = pieces[:: len(pieces) // MOST_PIECES_PER_VIDEO][:MOST_PIECES_PER_VIDEO]
    for piece_start, piece_end in pieces:
        if (piece_end - piece_start) / 16000 > 28:
            continue
        piece = speech_engines.clean_audio(audio[piece_start:piece_end])
        raw = sensevoice.generate(input=piece, cache={}, language="auto", use_itn=True, batch_size_s=60)
        tags = speech_engines.SENSEVOICE_TAG.findall(raw[0]["text"] if raw else "")
        if "yue" not in tags or "BGM" in tags:
            continue  # Cantonese speech only: not Mandarin, not singing over music
        sensevoice_text = speech_engines.to_common_script(speech_engines.run_sensevoice(sensevoice, piece, "yue")[0], "yue")
        # Greedy decoding is ~3x faster; the two-model agreement filter, not beam search, protects label quality.
        whisper_text = speech_engines.to_common_script(speech_engines.run_whisper(whisper, piece, "yue", beam_size=1, with_words=False)[0], "yue")
        text, _, agreement = ensemble.merge({"sensevoice": sensevoice_text, "whisper": whisper_text}, ["whisper", "sensevoice"], True)
        chinese = [character for character in text if "一" <= character <= "鿿"]
        varied_enough = len(set(chinese)) >= 0.5 * len(chinese)  # drops 媽媽媽 媽, 嚟嚟嚟嚟 and similar loops
        if agreement >= SMALLEST_AGREEMENT and len(chinese) >= FEWEST_CHARACTERS and varied_enough:
            kept.append({"audio": os.path.join(DATASET_FOLDER, "audio", f"{record['id']}.wav"),
                         "start": round(piece_start / 16000, 2), "end": round(piece_end / 16000, 2),
                         "text": whisper_text, "video": record["id"], "split": "train", "agreement": agreement,
                         "license": record.get("license"), "source": "pseudo"})
    return kept, len(pieces)


def main():
    done, gold = labeled_videos(), videos_with_gold_subtitles()
    records = [json.loads(line) for line in open(os.path.join(DATASET_FOLDER, "index.jsonl")) if line.strip()]
    for record in records:
        if record["id"] in done or record["id"] in gold:
            continue
        started = time.time()
        try:
            kept, total = label_video(record)
        except Exception as error:
            print("failed", record["id"], error, flush=True)
            continue
        with open(OUTPUT_FILE, "a") as output:
            for segment in kept:
                output.write(json.dumps(segment, ensure_ascii=False) + "\n")
        with open(DONE_FILE, "a") as done_file:
            done_file.write(record["id"] + "\n")
        seconds_kept = sum(segment["end"] - segment["start"] for segment in kept)
        print(f"[{time.strftime('%H:%M')}] {record['id']}: kept {len(kept)}/{total} pieces ({seconds_kept / 60:.1f} min) "
              f"in {time.time() - started:.0f}s — {record.get('title', '')[:50]}", flush=True)


if __name__ == "__main__":
    while True:  # keep labeling as the crawlers add videos
        main()
        time.sleep(300)
