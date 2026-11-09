"""High-precision pseudo-labels for downloaded videos without usable subtitles ("noisy student" self-training).

Each speech piece is transcribed by SenseVoice and Whisper large-v3, two very different models. A piece becomes
training data only when it is Cantonese and both models produce nearly the same text (character agreement >= 0.85),
because independent models rarely make the same mistake. Resumable: videos already labeled are skipped.

    .venv/bin/python dataset/pseudo_label.py          (keeps going as the crawlers add videos)
    .venv/bin/python dataset/pseudo_label.py --once   (stops when every video is labeled)
"""

import json
import os
import queue
import sys
import threading
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


WHISPER_BATCH = 8


def sensevoice_cantonese(sensevoice, piece):
    """SenseVoice's text for a piece when it hears Cantonese speech (not Mandarin, not singing over music), else None."""
    raw = sensevoice.generate(input=piece, cache={}, language="auto", use_itn=True, batch_size_s=60)
    raw_text = raw[0]["text"] if raw else ""
    tags = speech_engines.SENSEVOICE_TAG.findall(raw_text)
    if "yue" not in tags or "BGM" in tags:
        return None
    text = speech_engines.EMOJI.sub("", speech_engines.SENSEVOICE_TAG.sub("", raw_text)).strip()
    return speech_engines.to_common_script(text, "yue")


def whisper_greedy_batch(whisper, pieces):
    """Greedy Whisper on several pieces at once (one encoder pass per batch), with Whisper's reference silence and loop rules."""
    import zlib
    import ctranslate2
    import numpy as np
    from faster_whisper.tokenizer import Tokenizer
    tokenizer = Tokenizer(whisper.hf_tokenizer, whisper.model.is_multilingual, task="transcribe", language="yue")
    features = []
    for piece in pieces:
        mel = whisper.feature_extractor(piece)[:, :3000]
        features.append(np.pad(mel, ((0, 0), (0, 3000 - mel.shape[1]))))
    encoded = whisper.model.encode(ctranslate2.StorageView.from_array(np.stack(features).astype(np.float32)))
    prompt = list(tokenizer.sot_sequence) + [tokenizer.no_timestamps]
    results = whisper.model.generate(encoded, [prompt] * len(pieces), beam_size=1, max_length=448,
                                     return_scores=True, return_no_speech_prob=True)
    texts = []
    for result in results:
        tokens = [token for token in result.sequences_ids[0] if token < tokenizer.eot]
        text = tokenizer.decode(tokens).strip()
        average_log_probability = result.scores[0]
        compression = len(text.encode()) / max(1, len(zlib.compress(text.encode())))
        silence = result.no_speech_prob > 0.6 and average_log_probability < -1.0
        texts.append("" if silence or compression > 2.4 else text)
    return texts


def cantonese_candidates(record):
    """Speech pieces of a video that SenseVoice hears as Cantonese, with SenseVoice's text."""
    audio = speech_engines.decode_audio_file(os.path.join(DATASET_FOLDER, "audio", f"{record['id']}.wav"))
    sensevoice = speech_engines.get_engine("sensevoice")
    pieces = live_session.pieces_for_language_detection(audio)
    if len(pieces) > MOST_PIECES_PER_VIDEO:
        pieces = pieces[:: len(pieces) // MOST_PIECES_PER_VIDEO][:MOST_PIECES_PER_VIDEO]
    candidates = []
    for piece_start, piece_end in pieces:
        if (piece_end - piece_start) / 16000 > 28:
            continue
        piece = speech_engines.clean_audio(audio[piece_start:piece_end])
        sensevoice_text = sensevoice_cantonese(sensevoice, piece)
        if sensevoice_text:
            candidates.append((piece_start, piece_end, piece, sensevoice_text))
    return candidates, len(pieces)


def agreed_segments(record, candidates):
    """Candidates where greedy Whisper writes nearly the same text as SenseVoice."""
    whisper = speech_engines.get_engine("whisper")
    kept = []
    for batch_start in range(0, len(candidates), WHISPER_BATCH):
        batch = candidates[batch_start: batch_start + WHISPER_BATCH]
        # Greedy is much faster than beam search; the two-model agreement filter is what protects label quality.
        whisper_texts = whisper_greedy_batch(whisper, [candidate[2] for candidate in batch])
        for (piece_start, piece_end, _, sensevoice_text), whisper_text in zip(batch, whisper_texts):
            whisper_text = speech_engines.to_common_script(whisper_text, "yue")
            if not whisper_text or speech_engines.is_repetition_loop(whisper_text):
                continue
            text, _, agreement = ensemble.merge({"sensevoice": sensevoice_text, "whisper": whisper_text}, ["whisper", "sensevoice"], True)
            chinese = [character for character in text if "\u4e00" <= character <= "\u9fff"]
            varied_enough = len(set(chinese)) >= 0.5 * len(chinese)  # drops 媽媽媽 媽, 嚟嚟嚟嚟 and similar loops
            if agreement >= SMALLEST_AGREEMENT and len(chinese) >= FEWEST_CHARACTERS and varied_enough:
                kept.append({"audio": os.path.join(DATASET_FOLDER, "audio", f"{record['id']}.wav"),
                             "start": round(piece_start / 16000, 2), "end": round(piece_end / 16000, 2),
                             "text": whisper_text, "video": record["id"], "split": "train", "agreement": agreement,
                             "license": record.get("license"), "source": "pseudo"})
    return kept


def label_video(record):
    candidates, total = cantonese_candidates(record)
    return agreed_segments(record, candidates), total


def save_video(record, kept, total, started):
    with open(OUTPUT_FILE, "a") as output:
        output.write("".join(json.dumps(segment, ensure_ascii=False) + "\n" for segment in kept))
    with open(DONE_FILE, "a") as done_file:
        done_file.write(record["id"] + "\n")
    seconds_kept = sum(segment["end"] - segment["start"] for segment in kept)
    print(f"[{time.strftime('%H:%M')}] {record['id']}: kept {len(kept)}/{total} pieces ({seconds_kept / 60:.1f} min) "
          f"in {time.time() - started:.0f}s — {record.get('title', '')[:50]}", flush=True)


def main():
    """Label every video not labeled yet. SenseVoice works one video ahead of Whisper, so both models stay busy,
    sharing one copy of each model on the GPU."""
    done, gold = labeled_videos(), videos_with_gold_subtitles()
    records = [json.loads(line) for line in open(os.path.join(DATASET_FOLDER, "index.jsonl")) if line.strip()]
    records = [record for record in records if record["id"] not in done and record["id"] not in gold]
    speech_engines.get_engine("sensevoice"), speech_engines.get_engine("whisper")
    handoff = queue.Queue(maxsize=2)

    def find_candidates():
        for record in records:
            started = time.time()
            try:
                handoff.put((record, *cantonese_candidates(record), started))
            except Exception as error:
                print("failed (SenseVoice)", record["id"], error, flush=True)
        handoff.put(None)

    threading.Thread(target=find_candidates, daemon=True).start()
    while (item := handoff.get()) is not None:
        record, candidates, total, started = item
        try:
            save_video(record, agreed_segments(record, candidates), total, started)
        except Exception as error:
            print("failed (Whisper)", record["id"], error, flush=True)
    return len(records)


if __name__ == "__main__":
    # pseudo_label.py [--once]   (without --once it keeps labeling as the crawlers add videos)
    while True:
        main()
        if "--once" in sys.argv:
            break
        time.sleep(300)
