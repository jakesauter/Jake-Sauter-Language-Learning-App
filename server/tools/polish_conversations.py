"""Re-process a day's recordings with the full offline pipeline into one new "polished" conversation.

    phase "listen":      clean audio -> pieces -> language -> SenseVoice + Whisper large-v3 -> voice fingerprints
    phase "understand":  speaker clustering over the whole day -> LLM fusion -> translation with context -> save

Run the phases in separate processes so the speech models and the 7B model never share the GPU.
"""

import datetime
import glob
import json
import os
import sys
import wave

import numpy as np

import conversations
import live_session
import speakers
import speech_engines

PERSON = sys.argv[3] if len(sys.argv) > 3 else "jakesauter@github"
DAY = sys.argv[2] if len(sys.argv) > 2 else datetime.date.today().isoformat()
WORK_FILE = f"/data/experiments/polish-{DAY}.json"
CANDIDATE_LANGUAGES = ["yue", "tsn", "zh", "en"]
EXPECTED_SPEAKERS = int(os.environ.get("POLYLANG_EXPECTED_SPEAKERS", "6"))


def recordings_for_day():
    folder = conversations.person_folder(PERSON)
    paths = glob.glob(os.path.join(folder, "conversations", "*", "recordings", f"{DAY}_*.wav"))
    return sorted(paths, key=os.path.basename)


def recording_start_time(path):
    with wave.open(path) as wav_file:
        seconds = wav_file.getnframes() / wav_file.getframerate()
    saved_at = datetime.datetime.strptime(os.path.basename(path)[:-4], "%Y-%m-%d_%H%M%S")
    return saved_at.timestamp() - seconds


def listen():
    from faster_whisper import WhisperModel
    sensevoice = speech_engines.get_engine("sensevoice")
    whisper = WhisperModel("large-v3", device="cuda", compute_type="int8_float16")
    pieces = []
    for path in recordings_for_day():
        audio = speech_engines.decode_audio_file(path)
        recording_started = recording_start_time(path)
        for piece_start, piece_end in live_session.pieces_for_language_detection(audio):
            piece = speech_engines.clean_audio(audio[piece_start:piece_end])
            language, _ = speech_engines.detect_language(piece, CANDIDATE_LANGUAGES)
            versions = {
                "sensevoice": speech_engines.to_common_script(speech_engines.run_sensevoice(sensevoice, piece, language)[0], language),
                "whisper": speech_engines.to_common_script(speech_engines.run_whisper(whisper, piece, language, with_words=False)[0], language),
            }
            if not any(versions.values()):
                continue
            pieces.append({
                "at": recording_started + piece_start / speech_engines.SAMPLE_RATE,
                "seconds": round((piece_end - piece_start) / speech_engines.SAMPLE_RATE, 2),
                "language": language, "hyps": versions,
                "fingerprint": speakers.voice_fingerprint(piece).tolist() if (piece_end - piece_start) > 0.5 * speech_engines.SAMPLE_RATE else None,
            })
        print(f"listened: {os.path.basename(path)} -> {len(pieces)} pieces so far", flush=True)
    os.makedirs(os.path.dirname(WORK_FILE), exist_ok=True)
    json.dump(pieces, open(WORK_FILE, "w"), ensure_ascii=False)


def cluster_speakers(pieces):
    """Average-linkage clustering of every voice fingerprint from the whole day; Speaker 1 talks the most."""
    from scipy.cluster.hierarchy import fcluster, linkage
    with_voice = [index for index, piece in enumerate(pieces) if piece["fingerprint"] and piece["seconds"] >= 1.0]
    if len(with_voice) < 2:
        return
    fingerprints = np.array([pieces[index]["fingerprint"] for index in with_voice])
    # Ward, not average linkage: through one phone mic voices separate weakly (median similarity 0.44 on
    # 2026-11-08), and average linkage chained nearly everything into one group. Ward with ~6 groups split
    # tonight's dinner into voices with clearly different language habits (92% English ... 88% Cantonese).
    groups = fcluster(linkage(fingerprints, method="ward"), t=EXPECTED_SPEAKERS, criterion="maxclust")
    by_size = [group for group, _ in sorted(((group, list(groups).count(group)) for group in set(groups)), key=lambda item: -item[1])]
    number_for_group = {group: rank + 1 for rank, group in enumerate(by_size)}
    centroids = {group: fingerprints[groups == group].mean(axis=0) for group in set(groups)}
    for index, group in zip(with_voice, groups):
        pieces[index]["speaker"] = number_for_group[group]
    for piece in pieces:  # short pieces join the closest voice
        if "speaker" not in piece and piece["fingerprint"]:
            closest = max(centroids, key=lambda group: float(np.dot(piece["fingerprint"], centroids[group])))
            piece["speaker"] = number_for_group[closest]


def understand():
    import asyncio
    import translation
    pieces = json.load(open(WORK_FILE))
    cluster_speakers(pieces)

    async def run():
        lines = []
        for piece in pieces:
            versions = [text for text in piece["hyps"].values() if text]
            if piece["language"] == "en":
                text = piece["hyps"].get("whisper") or versions[0]
            else:
                text = speech_engines.to_common_script(await translation.fuse_transcripts(versions, piece["language"]), piece["language"])
            line = {"text": text, "language": piece["language"], "speaker": piece.get("speaker"), "hyps": piece["hyps"],
                    "at": piece["at"], "start": 0, "end": piece["seconds"], "en": "",
                    "could_be": ["yue", "tsn"] if piece["language"] == "yue" else [piece["language"]]}
            if piece["language"] != "en":
                earlier = [entry["text"] + (f" (meaning: {entry['en']})" if entry["en"] else "") for entry in lines[-4:]]
                source = "tsn" if piece["language"] == "yue" else piece["language"]
                line["en"] = (await translation.translate_text(text, source, "en")) ["text"] if not earlier else \
                    "".join([chunk async for chunk in translation.stream_translation(text, source, "en", None, earlier)]).strip()
            lines.append(line)
            if len(lines) % 25 == 0:
                print(f"understood {len(lines)}/{len(pieces)}", flush=True)
        return lines

    lines = asyncio.run(run())
    conversation = conversations.create(PERSON, f"Dinner {DAY} (polished)", CANDIDATE_LANGUAGES)
    for line in lines:
        conversations.append_line(PERSON, conversation["id"], line)
    languages = {code: sum(line["language"] == code for line in lines) for code in {line["language"] for line in lines}}
    print(f"saved '{conversation['title']}' with {len(lines)} lines; languages {languages}; speakers {len({l['speaker'] for l in lines if l['speaker']})}")


if __name__ == "__main__":
    {"listen": listen, "understand": understand}[sys.argv[1]]()
