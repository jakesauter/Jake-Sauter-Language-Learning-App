"""Cantonese clip -> English reference pairs, from videos with both human Cantonese and human English subtitles.

Each gold clip (audio + Cantonese text) gets the English subtitle lines that fall inside its time range, so the
translator can be scored on its own (Cantonese text -> English) and end to end (audio -> English).

    ~/venvs/train/bin/python dataset/build_translation_pairs.py
"""

import glob
import json
import os
import re

import webvtt

from build_gold_segments import DATASET_FOLDER, seconds

ENGLISH_FOLDER = os.path.join(DATASET_FOLDER, "subtitles_en")
OUTPUT_FILE = os.path.join(DATASET_FOLDER, "translation_pairs.jsonl")
SMALLEST_OVERLAP = 0.5  # an English line belongs to a clip when at least half of it falls inside the clip


def english_cues(video_id):
    paths = sorted(glob.glob(os.path.join(ENGLISH_FOLDER, f"{video_id}.en*.vtt")))
    if not paths:
        return []
    cues = []
    for cue in webvtt.read(paths[0]):
        text = re.sub(r"<[^>]+>|\[[^\]]*\]|♪", "", cue.text)
        text = re.sub(r"\s+", " ", text).strip()
        if text and seconds(cue.end) > seconds(cue.start):
            cues.append((seconds(cue.start), seconds(cue.end), text))
    return cues


def english_inside(cues, start, end):
    inside = [text for cue_start, cue_end, text in cues
              if min(end, cue_end) - max(start, cue_start) >= SMALLEST_OVERLAP * (cue_end - cue_start)]
    return " ".join(inside)


def main():
    segments = [json.loads(line) for line in open(os.path.join(DATASET_FOLDER, "gold_segments.jsonl")) if line.strip()]
    cues_by_video, pairs = {}, []
    for segment in segments:
        if segment["video"] not in cues_by_video:
            cues_by_video[segment["video"]] = english_cues(segment["video"])
        english = english_inside(cues_by_video[segment["video"]], segment["start"], segment["end"])
        if english:
            pairs.append({**segment, "english": english})
    with open(OUTPUT_FILE, "w") as output:
        for pair in pairs:
            output.write(json.dumps(pair, ensure_ascii=False) + "\n")
    videos = sorted({pair["video"] for pair in pairs})
    print(f"{len(pairs)} pairs from {len(videos)} videos: {videos}")
    for pair in pairs[:: max(1, len(pairs) // 6)][:6]:
        print(f"  {pair['text'][:40]}\n  -> {pair['english'][:80]}")


if __name__ == "__main__":
    main()
