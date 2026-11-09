"""Turn human-written subtitles into training segments: audio clip + spoken-Cantonese text.

Written-Chinese subtitles (書面語) differ from what is spoken and would teach the model to translate rather than
transcribe, so a video is kept only if its subtitles use enough colloquial Cantonese particles.
Output: /mnt/storage/datasets/youtube_cc_cantonese/gold_segments.jsonl  (split by video into train/test)
"""

import glob
import hashlib
import json
import os
import re

import webvtt
from opencc import OpenCC

DATASET_FOLDER = "/mnt/storage/datasets/youtube_cc_cantonese"
OUTPUT_FILE = os.path.join(DATASET_FOLDER, "gold_segments.jsonl")
SUBTITLE_PREFERENCE = ("yue-HK", "yue", "zh-HK", "zh-Hant", "zh-TW", "zh", "zh-Hans", "zh-CN")
COLLOQUIAL_PARTICLES = set("嘅咗唔係哋佢嚟啲冇嘢喺噉嗰咩乜嘛囉㗎吖啱咁睇")
SHORTEST_COLLOQUIAL_SHARE = 0.03
LONGEST_SEGMENT_SECONDS = 25.0
to_hong_kong_script = OpenCC("s2hk")


def best_subtitle_file(video_id):
    for code in SUBTITLE_PREFERENCE:
        path = os.path.join(DATASET_FOLDER, "subtitles", f"{video_id}.{code}.vtt")
        if os.path.exists(path):
            return path, code
    others = sorted(glob.glob(os.path.join(DATASET_FOLDER, "subtitles", f"{video_id}.*.vtt")))
    return (others[0], others[0].split(".")[-2]) if others else (None, None)


def clean_text(text):
    text = re.sub(r"<[^>]+>|\[[^\]]*\]|\([^)]*\)|♪|♫|^-\s*", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return to_hong_kong_script.convert(text)


def seconds(timestamp):
    hours, minutes, rest = timestamp.split(":")
    return int(hours) * 3600 + int(minutes) * 60 + float(rest)


def colloquial_share(texts):
    characters = [character for text in texts for character in text if "一" <= character <= "鿿"]
    return sum(character in COLLOQUIAL_PARTICLES for character in characters) / max(1, len(characters)), len(characters)


def split_for(video_id):
    return "test" if int(hashlib.sha1(video_id.encode()).hexdigest(), 16) % 10 == 0 else "train"


def main():
    records = [json.loads(line) for line in open(os.path.join(DATASET_FOLDER, "index.jsonl")) if line.strip()]
    kept_videos, segments = 0, []
    for record in records:
        if not record.get("human_subtitles"):
            continue
        path, code = best_subtitle_file(record["id"])
        audio = os.path.join(DATASET_FOLDER, "audio", f"{record['id']}.wav")
        if not path or not os.path.exists(audio):
            continue
        cues = [(seconds(cue.start), seconds(cue.end), clean_text(cue.text)) for cue in webvtt.read(path)]
        cues = [cue for cue in cues if cue[2] and cue[1] > cue[0]]
        share, chinese_characters = colloquial_share([cue[2] for cue in cues])
        if chinese_characters < 50 or share < SHORTEST_COLLOQUIAL_SHARE:
            print(f"  skip {record['id']} ({code}): colloquial share {share:.1%}, {chinese_characters} chars — written Chinese or too short")
            continue
        kept_videos += 1
        current = None
        for start, end, text in cues:
            if current and end - current["start"] <= LONGEST_SEGMENT_SECONDS and start - current["end"] < 1.5:
                current["end"], current["text"] = end, current["text"] + text
            else:
                if current:
                    segments.append(current)
                current = {"audio": audio, "start": start, "end": end, "text": text, "video": record["id"],
                           "split": split_for(record["id"]), "license": record.get("license"), "subtitle": code}
        if current:
            segments.append(current)
    with open(OUTPUT_FILE, "w") as output:
        for segment in segments:
            output.write(json.dumps(segment, ensure_ascii=False) + "\n")
    hours = {split: sum(s["end"] - s["start"] for s in segments if s["split"] == split) / 3600 for split in ("train", "test")}
    print(f"kept {kept_videos} videos -> {len(segments)} segments; train {hours['train']:.2f} h, test {hours['test']:.2f} h")


if __name__ == "__main__":
    main()
