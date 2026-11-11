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

from build_gold_segments import DATASET_FOLDER, best_subtitle_file, clean_text, colloquial_share, seconds
from known_bad_videos import LEAVE_OUT

ENGLISH_FOLDER = os.path.join(DATASET_FOLDER, "subtitles_en")
OUTPUT_FILE = os.path.join(DATASET_FOLDER, "translation_pairs.jsonl")
SMALLEST_OVERLAP = 0.5  # an English line belongs to a clip when at least half of it falls inside the clip
CHUNK_SECONDS = (3.0, 10.0)


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


def subtitle_chunks(video_id):
    """Clips cut from a video's human Chinese subtitles (for videos that are not in the gold set): consecutive
    cues merged into sentence-sized chunks."""
    path, _ = best_subtitle_file(video_id)
    if not path:
        return []
    cues = [(seconds(cue.start), seconds(cue.end), clean_text(cue.text)) for cue in webvtt.read(path)]
    chunks, current = [], None
    for start, end, text in cues:
        if not text:
            continue
        if current and (start - current["end"] > 0.6 or current["end"] - current["start"] >= CHUNK_SECONDS[0]
                        or end - current["start"] > CHUNK_SECONDS[1]):
            chunks.append(current)
            current = None
        if current:
            current["end"], current["text"] = end, current["text"] + " " + text
        else:
            current = {"video": video_id, "audio": os.path.join(DATASET_FOLDER, "audio", f"{video_id}.wav"),
                       "start": start, "end": end, "text": text, "split": "test", "source": "subtitles"}
    return chunks + ([current] if current else [])


def main():
    segments = [json.loads(line) for line in open(os.path.join(DATASET_FOLDER, "gold_segments.jsonl")) if line.strip()]
    gold_videos = {segment["video"] for segment in segments}
    for path in sorted(glob.glob(os.path.join(ENGLISH_FOLDER, "*.vtt"))):
        video_id = os.path.basename(path).split(".")[0]
        if video_id not in gold_videos and video_id not in LEAVE_OUT:
            segments += subtitle_chunks(video_id)
    segments = [segment for segment in segments if segment["video"] not in LEAVE_OUT]
    cues_by_video, pairs = {}, []
    for segment in segments:
        if segment["video"] not in cues_by_video:
            cues_by_video[segment["video"]] = english_cues(segment["video"])
        english = english_inside(cues_by_video[segment["video"]], segment["start"], segment["end"])
        if english:
            pairs.append({**segment, "english": english})
    # Some videos' Chinese subtitles are written Chinese (a translation of the speech, not a transcript): those pairs
    # are only good for audio -> English tests, not for Cantonese text -> English.
    spoken_videos = {video for video in {pair["video"] for pair in pairs}
                     if colloquial_share([pair["text"] for pair in pairs if pair["video"] == video])[0] >= 0.03}
    for pair in pairs:
        pair["chinese_is_spoken"] = pair["video"] in spoken_videos
    with open(OUTPUT_FILE, "w") as output:
        for pair in pairs:
            output.write(json.dumps(pair, ensure_ascii=False) + "\n")
    videos = sorted({pair["video"] for pair in pairs})
    print(f"{len(pairs)} pairs from {len(videos)} videos")
    for video in videos:
        texts = [pair["text"] for pair in pairs if pair["video"] == video]
        print(f"  {video}: {len(texts)} pairs, colloquial share {colloquial_share(texts)[0]:.1%}")
    for pair in pairs[:: max(1, len(pairs) // 6)][:6]:
        print(f"  {pair['text'][:40]}\n  -> {pair['english'][:80]}")


if __name__ == "__main__":
    main()
