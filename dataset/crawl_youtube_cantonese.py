"""Build a Cantonese/Taishanese speech dataset from Creative Commons YouTube videos.

    1. search YouTube with the Creative Commons filter for many Cantonese topics
    2. read each video's metadata: confirm the CC license, look for human-written Chinese subtitles
    3. download audio as 16 kHz mono WAV, plus human subtitles when they exist

Every video's license is recorded in index.jsonl, so a commercially safe Creative Commons subset can be separated later.
    search mode:   python dataset/crawl_youtube_cantonese.py search [videos_per_query]     (Creative Commons only)
    sources mode:  python dataset/crawl_youtube_cantonese.py sources dataset/sources.txt  (channels/playlists, any license)
"""

import json
import os
import subprocess
import sys
import time
import urllib.parse

DATASET_FOLDER = "/mnt/storage/datasets/youtube_cc_cantonese"
INDEX_FILE = os.path.join(DATASET_FOLDER, "index.jsonl")
YT_DLP = os.path.expanduser("~/venvs/tools/bin/yt-dlp")
CREATIVE_COMMONS_FILTER = "EgIwAQ%3D%3D"
SHORTEST_SECONDS, LONGEST_SECONDS = 60, 2 * 3600
CHINESE_SUBTITLE_CODES = ("yue", "yue-HK", "zh-HK", "zh-Hant", "zh-TW", "zh", "zh-Hans", "zh-CN")

SEARCH_TOPICS = [
    "廣東話", "粵語", "廣東話 教學", "學廣東話", "粵語 故事", "廣東話 故事", "香港 生活 vlog 廣東話",
    "廣東話 煮食", "粵語 煮餸", "屋企 飯局 廣東話", "廣東話 訪問", "粵語 講座", "廣東話 新聞", "粵語 podcast",
    "廣東話 對話", "香港人 傾偈", "粵語 童話", "廣東話 兒歌", "粵語 電台", "廣東話 旅行", "廣東話 遊戲 實況",
    "台山話", "台山话", "四邑話", "Taishanese", "Toisanese", "Hoisanese", "Toishan", "開平話", "恩平話",
    "Cantonese conversation", "learn Cantonese", "Cantonese podcast", "Cantonese vlog", "Cantonese cooking",
]


def run_yt_dlp(arguments, timeout=300):
    command = [YT_DLP, "--js-runtimes", "node", "--sleep-requests", "1", *arguments]
    result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
    return result.stdout


def search(topic, videos_per_query):
    url = ("https://www.youtube.com/results?search_query=" + urllib.parse.quote(topic) + "&sp=" + CREATIVE_COMMONS_FILTER)
    output = run_yt_dlp(["--flat-playlist", "--playlist-end", str(videos_per_query), "--print", "%(id)s", url])
    return [line.strip() for line in output.splitlines() if len(line.strip()) == 11]


def metadata(video_id):
    output = run_yt_dlp(["--skip-download", "-J", f"https://www.youtube.com/watch?v={video_id}"], timeout=120)
    return json.loads(output) if output.strip() else None


def human_chinese_subtitles(info):
    subtitles = info.get("subtitles") or {}
    return [code for code in subtitles if code in CHINESE_SUBTITLE_CODES or code.startswith(("yue", "zh"))]


def download(video_id, subtitle_codes):
    arguments = ["-q", "-f", "bestaudio", "-x", "--audio-format", "wav", "--postprocessor-args", "ffmpeg:-ac 1 -ar 16000",
                 "-o", os.path.join(DATASET_FOLDER, "audio", "%(id)s.%(ext)s")]
    if subtitle_codes:
        arguments += ["--write-subs", "--sub-langs", ",".join(subtitle_codes), "--sub-format", "vtt",
                      "-o", "subtitle:" + os.path.join(DATASET_FOLDER, "subtitles", "%(id)s.%(ext)s")]
    run_yt_dlp(arguments + [f"https://www.youtube.com/watch?v={video_id}"], timeout=1800)
    return os.path.exists(os.path.join(DATASET_FOLDER, "audio", f"{video_id}.wav"))


def list_videos(url, most_videos=500):
    if ("/@" in url or "/channel/" in url) and not url.rstrip("/").endswith(("/videos", "/streams")):
        url = url.rstrip("/") + "/videos"
    output = run_yt_dlp(["--flat-playlist", "--playlist-end", str(most_videos), "--print", "%(id)s", url], timeout=600)
    return [line.strip() for line in output.splitlines() if len(line.strip()) == 11]


def process_video(video_id, source_label, creative_commons_only):
    info = metadata(video_id)
    if not info:
        return
    if creative_commons_only and "Creative Commons" not in (info.get("license") or ""):
        return
    duration = info.get("duration") or 0
    if not SHORTEST_SECONDS // 2 <= duration <= LONGEST_SECONDS:
        return
    subtitle_codes = human_chinese_subtitles(info)
    if not download(video_id, subtitle_codes):
        return
    record = {"id": video_id, "title": info.get("title"), "channel": info.get("channel"),
              "channel_url": info.get("channel_url"), "license": info.get("license") or "standard YouTube license",
              "duration": duration, "language": info.get("language"), "human_subtitles": subtitle_codes,
              "query": source_label, "url": f"https://www.youtube.com/watch?v={video_id}", "downloaded_at": time.time()}
    with open(INDEX_FILE, "a") as index:
        index.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"  + {video_id} {duration // 60:3d} min subs={subtitle_codes or '-'} {info.get('title', '')[:60]}", flush=True)


def crawl_sources(sources_file):
    seen = already_indexed()
    for url in [line.strip() for line in open(sources_file) if line.strip() and not line.startswith("#")]:
        found = list_videos(url)
        print(f"[{time.strftime('%H:%M')}] {url}: {len(found)} videos", flush=True)
        for video_id in found:
            if video_id in seen:
                continue
            seen.add(video_id)
            try:
                process_video(video_id, url, creative_commons_only=False)
            except Exception as error:
                print("  failed:", video_id, error, flush=True)


def already_indexed():
    if not os.path.exists(INDEX_FILE):
        return set()
    with open(INDEX_FILE) as index:
        return {json.loads(line)["id"] for line in index if line.strip()}


def main():
    videos_per_query = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    os.makedirs(os.path.join(DATASET_FOLDER, "audio"), exist_ok=True)
    os.makedirs(os.path.join(DATASET_FOLDER, "subtitles"), exist_ok=True)
    seen = already_indexed()
    for topic in SEARCH_TOPICS:
        found = search(topic, videos_per_query)
        print(f"[{time.strftime('%H:%M')}] '{topic}': {len(found)} results", flush=True)
        for video_id in found:
            if video_id in seen:
                continue
            seen.add(video_id)
            try:
                info = metadata(video_id)
            except Exception as error:
                print("  metadata failed:", video_id, error, flush=True)
                continue
            if not info or "Creative Commons" not in (info.get("license") or ""):
                continue
            duration = info.get("duration") or 0
            if not SHORTEST_SECONDS <= duration <= LONGEST_SECONDS:
                continue
            subtitle_codes = human_chinese_subtitles(info)
            try:
                downloaded = download(video_id, subtitle_codes)
            except Exception as error:
                print("  download failed:", video_id, error, flush=True)
                continue
            if not downloaded:
                continue
            record = {"id": video_id, "title": info.get("title"), "channel": info.get("channel"),
                      "channel_url": info.get("channel_url"), "license": info.get("license"), "duration": duration,
                      "language": info.get("language"), "human_subtitles": subtitle_codes, "query": topic,
                      "url": f"https://www.youtube.com/watch?v={video_id}", "downloaded_at": time.time()}
            with open(INDEX_FILE, "a") as index:
                index.write(json.dumps(record, ensure_ascii=False) + "\n")
            print(f"  + {video_id} {duration // 60:3d} min subs={subtitle_codes or '-'} {info.get('title', '')[:60]}", flush=True)


SUBTITLED_FILTER = "EgIoAQ%3D%3D"  # YouTube search filter: videos with subtitles/CC
SUBTITLED_TOPICS = ["廣東話 字幕", "粵語 字幕", "廣東話 中文字幕", "香港 訪問 字幕", "粵語 對白", "廣東話 vlog 字幕",
                    "Cantonese with Chinese subtitles", "Cantonese subtitles Jyutping", "粵語 煮食 字幕", "廣東話 講故事 字幕",
                    "香港 街訪", "廣東話 podcast 字幕", "粵語 新聞 字幕", "台山話 字幕"]


def crawl_subtitled(videos_per_query):
    """Any license, but only videos that come with human-written Chinese subtitles (gold test data)."""
    seen = already_indexed()
    for topic in SUBTITLED_TOPICS:
        url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote(topic) + "&sp=" + SUBTITLED_FILTER
        output = run_yt_dlp(["--flat-playlist", "--playlist-end", str(videos_per_query), "--print", "%(id)s", url])
        found = [line.strip() for line in output.splitlines() if len(line.strip()) == 11]
        print(f"[{time.strftime('%H:%M')}] subtitled '{topic}': {len(found)} results", flush=True)
        for video_id in found:
            if video_id in seen:
                continue
            seen.add(video_id)
            try:
                info = metadata(video_id)
                if info and human_chinese_subtitles(info):
                    process_video(video_id, "subtitled:" + topic, creative_commons_only=False)
            except Exception as error:
                print("  failed:", video_id, error, flush=True)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "subtitled":
        crawl_subtitled(int(sys.argv[2]) if len(sys.argv) > 2 else 80)
        sys.exit()
    if len(sys.argv) > 2 and sys.argv[1] == "sources":
        os.makedirs(os.path.join(DATASET_FOLDER, "audio"), exist_ok=True)
        os.makedirs(os.path.join(DATASET_FOLDER, "subtitles"), exist_ok=True)
        crawl_sources(sys.argv[2])
    else:
        if len(sys.argv) > 1 and sys.argv[1] == "search":
            sys.argv.pop(1)
        main()
