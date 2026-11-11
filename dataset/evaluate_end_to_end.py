"""Score whole live setups end to end: Cantonese audio -> recognizer(s) -> translator -> English, against human
English subtitles (chrF++, higher is better). This is the number that matters at the dinner table.

The recognizers' output is read from what evaluate_speech_models.py saved for the "pairs" clips, so trying another
translator or another mix of recognizers needs no graphics card.

    .venv/bin/python dataset/evaluate_end_to_end.py <recognizers> <translator> [most_per_video]

    <recognizers>  saved output names joined by "+", e.g.
                   sensevoice_SenseVoiceSmall__pairs+whisper_large-v3__pairs        (the live setup until now)
                   sensevoice_sensevoice_small_yue__pairs__raw                      (one model alone)
                   Every version goes to the live code (translation.understand_line), so this scores exactly
                   what live mode would show.
    <translator>   understand:<model>  the chat model picks the version, translates and rates clarity
                   hymt:<model>        a translation model gets the version the recognizers agree on most
                   plain:<model>       a plain translation prompt on that same version

    POLYLANG_OLLAMA=http://127.0.0.1:11435 sends the translator to a second Ollama (e.g. one kept off the card).
    POLYLANG_E2E_OUTPUT=<folder> saves (and tables) the results there instead.
"""

import asyncio
import collections
import json
import os
import sys
import time

import sacrebleu

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "server"))
import speech_engines  # noqa: E402
import translation  # noqa: E402
from known_bad_videos import LEAVE_OUT  # noqa: E402

DATASET_FOLDER = "/mnt/storage/datasets/youtube_cc_cantonese"
SPEECH_OUTPUT_FOLDER = os.path.join(DATASET_FOLDER, "speech_eval")
OUTPUT_FOLDER = os.environ.get("POLYLANG_E2E_OUTPUT", os.path.join(DATASET_FOLDER, "end_to_end_eval"))  # a separate folder keeps runs on another translator apart
EARLIER_LINES = int(os.environ.get("POLYLANG_E2E_EARLIER", 4))  # 4 is the amount of context live mode gives


def clip_key(row):
    return row["video"], round(row["start"], 2), round(row["end"], 2)


def load_versions(recognizer_names):
    """{clip: [each recognizer's text, in the order named]} for clips every recognizer has, in time order."""
    heard_by_recognizer = []
    for name in recognizer_names:
        rows = [json.loads(line) for line in open(os.path.join(SPEECH_OUTPUT_FOLDER, name + ".jsonl")) if line.strip()]
        heard_by_recognizer.append({clip_key(row): speech_engines.to_common_script(row["heard"], "yue") for row in rows})
    shared = set.intersection(*(set(heard) for heard in heard_by_recognizer))
    return {clip: [heard[clip] for heard in heard_by_recognizer] for clip in sorted(shared)}


def spread_pairs(versions, most_per_video):
    """Pairs that have recognizer output, evenly spaced within each video so one long video can't dominate."""
    pairs = [json.loads(line) for line in open(os.path.join(DATASET_FOLDER, "translation_pairs.jsonl")) if line.strip()]
    pairs = sorted((pair for pair in pairs if pair["video"] not in LEAVE_OUT and clip_key(pair) in versions),
                   key=lambda pair: (pair["video"], pair["start"]))
    by_video = collections.defaultdict(list)
    for pair in pairs:
        by_video[pair["video"]].append(pair)
    chosen = []
    for video_pairs in by_video.values():
        chosen += video_pairs[:: max(1, len(video_pairs) // most_per_video)][:most_per_video]
    return chosen


async def translate_line(translator, versions, earlier_lines):
    """(what the line is taken to say, its English, whether it was shown as unclear)."""
    kind, _, model = translator.partition(":")
    usable = [version for version in versions if version and not speech_engines.is_repetition_loop(version)]
    if not usable:
        return "", "", True
    if kind in ("understand", "hymt"):
        translation.choose_provider = lambda source, target: "ollama:" + model
        answer = await translation.understand_line(usable, "yue", "en", earlier_lines)
        unclear = answer["english"] == "(unclear)"
        return answer["said"], "" if unclear else answer["english"], unclear
    said, _ = translation.most_agreed_version(usable)
    english = (await translation.translate_text(said, "yue", "en", provider="ollama:" + model))["text"]
    return said, english, False


async def run(recognizers, translator, most_per_video):
    recognizer_names = recognizers.split("+")
    versions = load_versions(recognizer_names)
    pairs = spread_pairs(versions, most_per_video)
    rows, earlier_by_video, started = [], collections.defaultdict(list), time.time()
    for pair in pairs:
        heard = versions[clip_key(pair)]
        earlier = earlier_by_video[pair["video"]][-EARLIER_LINES:]
        said, english = "", ""
        for attempt in range(3):
            try:
                said, english, unclear = await translate_line(translator, heard, earlier)
                break
            except Exception as error:
                print(f"  attempt {attempt + 1} failed: {error}", flush=True)
                await asyncio.sleep(5)
        else:
            unclear = True
        earlier_by_video[pair["video"]].append(said + (f" (meaning: {english})" if english else ""))  # as live mode does
        rows.append({"video": pair["video"], "start": pair["start"], "end": pair["end"], "reference": pair["english"],
                     "english": english, "said": said, "heard": heard, "subtitle": pair["text"], "unclear": unclear})
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    name = recognizers.replace("__pairs", "") + "__" + translator.replace(":", "_").replace("/", "_")
    name += "" if EARLIER_LINES == 4 else f"__earlier{EARLIER_LINES}"
    with open(os.path.join(OUTPUT_FOLDER, name + ".jsonl"), "w") as output:
        for row in rows:
            output.write(json.dumps(row, ensure_ascii=False) + "\n")
    report(name, rows, (time.time() - started) / max(1, len(rows)))


def chrf(rows):
    return sacrebleu.corpus_chrf([row["english"] for row in rows], [[row["reference"] for row in rows]], word_order=2).score


def report(name, rows, seconds_per_line=None):
    by_video = collections.defaultdict(list)
    for row in rows:
        by_video[row["video"]].append(row)
    per_video = " ".join(f"{video[:5]} {chrf(video_rows):.0f}" for video, video_rows in sorted(by_video.items()))
    unclear = sum(row["unclear"] for row in rows)
    speed = f"  {seconds_per_line:.1f}s/line" if seconds_per_line else ""
    print(f"{name}: end-to-end chrF++ {chrf(rows):.1f}  unclear {unclear}/{len(rows)}{speed}\n   per video: {per_video}", flush=True)


def table():
    """Every setup already scored, best first, on the clips they all share (so the numbers compare)."""
    results = {}
    for file_name in sorted(os.listdir(OUTPUT_FOLDER)):
        if file_name.endswith(".jsonl"):
            results[file_name[:-len(".jsonl")]] = [json.loads(line) for line in open(os.path.join(OUTPUT_FOLDER, file_name)) if line.strip()]
    shared = set.intersection(*({clip_key(row) for row in rows} for rows in results.values())) if results else set()
    print(f"{len(shared)} clips scored by every setup")
    scored = sorted(((chrf([row for row in rows if clip_key(row) in shared]), name, rows) for name, rows in results.items()), reverse=True)
    for score, name, rows in scored:
        unclear = sum(row["unclear"] for row in rows if clip_key(row) in shared)
        print(f"  {name:90s} chrF++ {score:5.1f}  unclear {unclear}")


if __name__ == "__main__":
    if sys.argv[1] == "table":
        table()
    else:
        asyncio.run(run(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 40))
