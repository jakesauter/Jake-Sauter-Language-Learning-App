"""Turn a YouTube or Instagram link into a saved conversation to study.

    link -> audio only (yt-dlp, YouTube and Instagram only, short videos only)
         -> the uploader's own subtitles in that language if there are any, otherwise speech recognition
         -> English for every line -> a conversation with the video's title, lines timed like the video

Jobs run one at a time in the background; the page polls GET /video/{job_id} for progress.
"""

import asyncio
import glob
import os
import re
import secrets
import shutil
import tempfile
import time
import urllib.parse

import conversations
import ensemble
import live_session
import translation

ALLOWED_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com", "youtu.be",
                 "instagram.com", "www.instagram.com"}
ALLOWED_EXTRACTORS = [r"youtube$", r"instagram$"]
LONGEST_VIDEO_SECONDS = 15 * 60
LARGEST_DOWNLOAD_BYTES = 80 * 1024 * 1024
MOST_LINES = 300
JOBS_KEPT_SECONDS = 6 * 3600

# Subtitle tracks that count as "this language", best first.
SUBTITLE_LANGUAGES = {
    "yue": ["yue", "yue-HK", "zh-HK"], "tsn": ["yue", "zh-HK"], "zh": ["zh-Hans", "zh-CN", "zh", "zh-Hant", "zh-TW"],
    "en": ["en", "en-US", "en-GB"], "es": ["es"], "fr": ["fr"], "de": ["de"], "ja": ["ja"], "ko": ["ko"],
}

jobs = {}
import_lock = asyncio.Lock()


def checked_link(link):
    """The link if it is an https YouTube or Instagram page, else ValueError. Keeps the server from fetching anything else."""
    link = (link or "").strip()
    parts = urllib.parse.urlsplit(link)
    if parts.scheme not in ("https", "http") or (parts.hostname or "").lower() not in ALLOWED_HOSTS or parts.port or parts.username:
        raise ValueError("Only YouTube and Instagram links work here.")
    return urllib.parse.urlunsplit(("https", parts.hostname.lower(), parts.path, parts.query, ""))


def start(person, link, language):
    link = checked_link(link)
    forget_old_jobs()
    if sum(job["person"] == person and job["status"] not in ("done", "failed") for job in jobs.values()) >= 2:
        raise ValueError("Two videos are already on the way. Try again when one is done.")
    job_id = secrets.token_urlsafe(9)
    jobs[job_id] = {"id": job_id, "person": person, "link": link, "language": language, "status": "waiting",
                    "done": 0, "total": 0, "conversation_id": "", "error": "", "title": "", "started": time.time()}
    asyncio.get_running_loop().create_task(run(job_id))
    return public(jobs[job_id])


def public(job):
    return {key: job[key] for key in ("id", "status", "done", "total", "conversation_id", "error", "title")}


def job_for(person, job_id):
    job = jobs.get(job_id)
    return public(job) if job and job["person"] == person else None


def forget_old_jobs():
    for job_id in [job_id for job_id, job in jobs.items() if time.time() - job["started"] > JOBS_KEPT_SECONDS]:
        jobs.pop(job_id, None)


async def run(job_id):
    job = jobs[job_id]
    folder = tempfile.mkdtemp(prefix="video-")
    try:
        async with import_lock:
            job["status"] = "downloading"
            audio_path, info, subtitle_path = await asyncio.get_running_loop().run_in_executor(
                None, download, job["link"], job["language"], folder)
            job["title"] = video_title(info)
            if subtitle_path:
                job["status"] = "reading subtitles"
                lines = subtitle_lines(subtitle_path)
            else:
                job["status"] = "listening"
                result = await live_session.run_on_gpu(ensemble.transcribe_file, audio_path, job["language"])
                lines = [piece for segment in result["segments"] if segment.get("text", "").strip()
                         for piece in sentences_of(segment)]
            lines = lines[:MOST_LINES]
            if not lines:
                raise ValueError("No speech found in this video.")
            job["status"], job["total"] = "translating", len(lines)
            written = "yue" if job["language"] == "tsn" else job["language"]
            for number, line in enumerate(lines):
                line["language"] = job["language"]
                if job["language"] != "en":
                    earlier_lines = [earlier["text"] + (f" (meaning: {earlier['en']})" if earlier.get("en") else "")
                                     for earlier in lines[max(0, number - 4):number]]
                    try:
                        pieces = [piece async for piece in translation.stream_translation(line["text"], written, "en", None, earlier_lines)]
                        line["en"] = "".join(pieces).strip()
                    except Exception as error:
                        print("video line translation failed:", error)
                job["done"] += 1
            conversation = save(job, info, lines)
            job["conversation_id"], job["status"] = conversation["id"], "done"
    except Exception as error:
        job["status"], job["error"] = "failed", friendly_error(error)
        print("video import failed:", type(error).__name__, error)
    finally:
        shutil.rmtree(folder, ignore_errors=True)


SENTENCE_END = re.compile(r"(?<=[。？！?!])\s*")
COMMA = re.compile(r"(?<=[，,])\s*")
LONGEST_LINE_CHARACTERS = 24


def sentences_of(segment):
    """One line per sentence, so a long stretch of speech becomes short lines to study; times shared out by length."""
    text = segment["text"].strip()
    pieces = [piece.strip() for piece in SENTENCE_END.split(text) if piece.strip()]
    pieces = [part for piece in pieces for part in (COMMA.split(piece) if len(piece) > LONGEST_LINE_CHARACTERS else [piece]) if part.strip()]
    start, end = segment.get("start") or 0.0, segment.get("end") or segment.get("start") or 0.0
    if len(pieces) <= 1:
        return [{"text": text, "start": start, "end": end, "agree": segment.get("agree"),
                 "spans": segment.get("spans"), "hyps": segment.get("hyps")}]
    total_length, lines, used = sum(len(piece) for piece in pieces), [], 0
    for piece in pieces:
        piece_start = start + (end - start) * used / total_length
        used += len(piece)
        lines.append({"text": piece, "start": round(piece_start, 2), "end": round(start + (end - start) * used / total_length, 2),
                      "agree": segment.get("agree")})
    return lines


def video_title(info):
    """The video's title; Instagram reels have none ("Video by …"), so use the caption's first line instead."""
    title = (info.get("title") or "").strip()
    if not title or title.lower().startswith("video by"):
        caption = next((row.strip() for row in (info.get("description") or "").splitlines() if row.strip() and not row.strip().startswith("#")), "")
        title = caption or (f"{info.get('uploader')}'s video" if info.get("uploader") else "Video")
    return title[:100]


def friendly_error(error):
    text = str(error)
    if "duration" in text or "too long" in text.lower():
        return f"That video is longer than {LONGEST_VIDEO_SECONDS // 60} minutes."
    if isinstance(error, ValueError):
        return text
    if "login" in text.lower() or "private" in text.lower() or "unavailable" in text.lower():
        return "That video is private, removed or needs a login."
    return "Couldn't get that video. Check the link and try again."


def download(link, language, folder):
    """Audio only, plus the uploader's subtitles in this language if there are any. Returns (audio, info, subtitles)."""
    import yt_dlp

    def not_too_long(info, *, incomplete=False):
        duration = info.get("duration")
        if duration and duration > LONGEST_VIDEO_SECONDS:
            return "video too long (duration)"
        return None

    options = {
        "format": "bestaudio/best[height<=480]/best", "outtmpl": os.path.join(folder, "audio.%(ext)s"),
        "noplaylist": True, "playlist_items": "1", "allowed_extractors": ALLOWED_EXTRACTORS,
        "match_filter": not_too_long, "max_filesize": LARGEST_DOWNLOAD_BYTES, "socket_timeout": 20, "retries": 2,
        "quiet": True, "no_warnings": True, "noprogress": True, "cachedir": False,
        "writesubtitles": True, "writeautomaticsub": False, "subtitlesformat": "vtt",
        "subtitleslangs": SUBTITLE_LANGUAGES.get(language, [language]),
    }
    with yt_dlp.YoutubeDL(options) as downloader:
        info = downloader.extract_info(link, download=True)
    if info.get("_type") == "playlist":
        info = (info.get("entries") or [{}])[0] or {}
    audio_files = [path for path in glob.glob(os.path.join(folder, "audio.*")) if not path.endswith((".vtt", ".part"))]
    if not audio_files:
        raise RuntimeError("download produced no audio (duration filter or size cap)")
    subtitle_files = sorted(glob.glob(os.path.join(folder, "audio.*.vtt")),
                            key=lambda path: subtitle_rank(path, language))
    return audio_files[0], info, (subtitle_files[0] if subtitle_files else None)


def subtitle_rank(path, language):
    wanted = SUBTITLE_LANGUAGES.get(language, [language])
    code = path.rsplit(".", 2)[-2]
    return wanted.index(code) if code in wanted else len(wanted)


VTT_TIME = re.compile(r"(?:(\d+):)?(\d+):(\d+)[.,](\d+)\s+-->\s+(?:(\d+):)?(\d+):(\d+)[.,](\d+)")


def subtitle_lines(path):
    """WebVTT cues as lines, with markup removed and repeated cues (rolling captions) merged."""
    def seconds(hours, minutes, secs, millis):
        return int(hours or 0) * 3600 + int(minutes) * 60 + int(secs) + int(millis) / 1000

    lines, current = [], None
    with open(path, encoding="utf-8", errors="replace") as file:
        for row in file.read().splitlines() + [""]:
            match = VTT_TIME.search(row)
            if match:
                groups = match.groups()
                current = {"start": seconds(*groups[:4]), "end": seconds(*groups[4:]), "text": ""}
            elif current is not None and row.strip():
                text = re.sub(r"<[^>]+>|\{[^}]+\}", "", row).strip()
                current["text"] = (current["text"] + " " + text).strip()
            elif current is not None:
                if current["text"] and not (lines and lines[-1]["text"] == current["text"]):
                    lines.append(current)
                elif current["text"]:
                    lines[-1]["end"] = current["end"]
                current = None
    return lines


def save(job, info, lines):
    person = job["person"]
    title = "▶ " + (job["title"] or "Video")
    conversation = conversations.create(person, title, [job["language"], "en"])
    conversations.set_source(person, conversation["id"], {
        "kind": "video", "link": job["link"], "site": "Instagram" if "instagram" in job["link"] else "YouTube",
        "uploader": (info.get("uploader") or info.get("channel") or "")[:80], "duration": info.get("duration")})
    for line in lines:
        conversations.append_line(person, conversation["id"], {
            **{key: value for key, value in line.items() if value not in (None, "")}, "t": line.get("start") or 0})
    return conversations.details(person, conversation["id"])
