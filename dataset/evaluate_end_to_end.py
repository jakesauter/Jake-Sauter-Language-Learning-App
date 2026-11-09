"""Score the live pipeline end to end: Cantonese audio -> both speech engines -> "understand this line" -> English,
against human English subtitles (chrF++, higher is better). This is the number that matters at the dinner table.

    POLYLANG_MODEL=large-v3 .venv/bin/python dataset/evaluate_end_to_end.py qwen2.5:7b [most_per_video]
"""

import asyncio
import collections
import json
import os
import sys
import time

import sacrebleu
import soundfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "server"))
os.environ.setdefault("POLYLANG_MODEL", "large-v3")
import ensemble  # noqa: E402
import speech_engines  # noqa: E402
import translation  # noqa: E402

DATASET_FOLDER = "/mnt/storage/datasets/youtube_cc_cantonese"
PAIRS_FILE = os.path.join(DATASET_FOLDER, "translation_pairs.jsonl")
OUTPUT_FOLDER = os.path.join(DATASET_FOLDER, "end_to_end_eval")


def spread_pairs(most_per_video):
    pairs = [json.loads(line) for line in open(PAIRS_FILE) if line.strip()]
    by_video = collections.defaultdict(list)
    for pair in pairs:
        by_video[pair["video"]].append(pair)
    chosen = []
    for video_pairs in by_video.values():  # evenly spaced, so one long video can't dominate
        chosen += video_pairs[:: max(1, len(video_pairs) // most_per_video)][:most_per_video]
    return chosen


async def run(translator_model, most_per_video):
    translation.choose_provider = lambda source, target: "ollama:" + translator_model
    pairs = spread_pairs(most_per_video)
    rows, earlier_by_video, started = [], collections.defaultdict(list), time.time()
    for pair in pairs:
        audio, _ = soundfile.read(pair["audio"], start=int(pair["start"] * 16000), stop=int(pair["end"] * 16000), dtype="float32")
        result = ensemble.transcribe_audio(speech_engines.clean_audio(audio), "yue", ["sensevoice", "whisper"], 0.0, False)
        hyps = result["segments"][0]["hyps"] if result["segments"] else {}
        versions = [text for text in hyps.values() if text and not speech_engines.is_repetition_loop(text)]
        earlier = earlier_by_video[pair["video"]][-4:]
        answer = await translation.understand_line(versions, "yue", "en", earlier) if versions else {"said": "", "english": "(unclear)"}
        english = "" if answer["english"] == "(unclear)" else answer["english"]
        earlier_by_video[pair["video"]].append(answer["said"] + (f" (meaning: {english})" if english else ""))
        rows.append({"video": pair["video"], "reference": pair["english"], "english": english, "said": answer["said"],
                     "hyps": hyps, "subtitle": pair["text"], "unclear": not english})
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    name = f"{os.path.basename(os.environ['POLYLANG_MODEL'].rstrip('/'))}__{translator_model.replace(':', '_')}"
    with open(os.path.join(OUTPUT_FOLDER, name + ".jsonl"), "w") as output:
        for row in rows:
            output.write(json.dumps(row, ensure_ascii=False) + "\n")
    by_video = collections.defaultdict(list)
    for row in rows:
        by_video[row["video"]].append(row)
    chrf = lambda chosen: sacrebleu.corpus_chrf([r["english"] for r in chosen], [[r["reference"] for r in chosen]], word_order=2).score
    per_video = {video: round(chrf(video_rows), 1) for video, video_rows in by_video.items()}
    unclear = sum(row["unclear"] for row in rows)
    print(f"{name}: end-to-end chrF++ {chrf(rows):.1f}  unclear {unclear}/{len(rows)}  per video {per_video}  "
          f"({(time.time() - started) / len(rows):.1f}s per clip)", flush=True)


if __name__ == "__main__":
    asyncio.run(run(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 60))
