"""Train a Taishanese-vs-Cantonese detector from the DLI Toishan course (1964) and Cantonese YouTube.

No speech model tells Taishanese from Cantonese, so live mode labels both "Cantonese / Taishanese". This trains a
small classifier on Whisper large-v3 encoder features (what Whisper's own language detection is built on).

Recording era is a confound (1960s tape vs modern YouTube), so recording conditions are made to overlap
(Cantonese clips sometimes degraded to telephone-band tape with hiss; DLI clips sometimes given modern room noise),
and the honest test is MODERN Taishanese from YouTube, which the classifier never trains on.

    .venv/bin/python dataset/taishanese_detector.py prepare     (CPU: unzip, convert, cut, drop English narration)
    .venv/bin/python dataset/taishanese_detector.py features    (GPU: Whisper encoder features for every clip)
    .venv/bin/python dataset/taishanese_detector.py train       (fit + evaluate, save the classifier)
"""

import glob
import json
import os
import random
import subprocess
import sys
import zipfile

import numpy as np
import scipy.signal

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "server"))
import speech_engines  # noqa: E402

DLI_FOLDER = "/mnt/storage/datasets/taishanese_dli"
CANTONESE_FOLDER = "/mnt/storage/datasets/youtube_cc_cantonese"
MODERN_TAISHANESE_FOLDER = "/mnt/storage/datasets/youtube_taishanese"
WORK_FOLDER = "/mnt/storage/datasets/taishanese_detector"
CLIP_SECONDS = (1.5, 12.0)
SAMPLE_RATE = 16000


# ---------- prepare: clips of Taishanese (DLI), Cantonese (YouTube), modern Taishanese (test) ----------

def unpack_dli():
    audio_folder = os.path.join(DLI_FOLDER, "audio")
    os.makedirs(audio_folder, exist_ok=True)
    for archive in sorted(glob.glob(os.path.join(DLI_FOLDER, "zips", "*.zip"))):
        with zipfile.ZipFile(archive) as zipped:
            for member in zipped.namelist():
                if member.lower().endswith(".mp3"):
                    target = os.path.join(audio_folder, os.path.basename(member)[:-4] + ".wav")
                    if not os.path.exists(target):
                        with zipped.open(member) as source, open(target + ".mp3", "wb") as mp3:
                            mp3.write(source.read())
                        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", target + ".mp3", "-ac", "1", "-ar", "16000", target], check=True)
                        os.remove(target + ".mp3")
    return sorted(glob.glob(os.path.join(audio_folder, "*.wav")))


def cut_clips(path, label, group, sensevoice, keep_language):
    """Speech pieces of a recording whose SenseVoice language tag is in keep_language (drops English narration)."""
    import live_session
    audio = speech_engines.decode_audio_file(path)
    clips = []
    for start, end in live_session.pieces_for_language_detection(audio):
        seconds = (end - start) / SAMPLE_RATE
        if not CLIP_SECONDS[0] <= seconds <= CLIP_SECONDS[1]:
            continue
        raw = sensevoice.generate(input=audio[start:end], cache={}, language="auto", use_itn=False, batch_size_s=60)
        tags = speech_engines.SENSEVOICE_TAG.findall(raw[0]["text"] if raw else "")
        if not set(tags) & keep_language or "BGM" in tags:
            continue
        clips.append({"audio": path, "start": start / SAMPLE_RATE, "end": end / SAMPLE_RATE, "label": label, "group": group})
    return clips


def prepare():
    os.makedirs(WORK_FOLDER, exist_ok=True)
    sensevoice = speech_engines.get_engine("sensevoice")
    chinese = {"yue", "zh"}
    clips = []
    for path in unpack_dli():
        lesson = os.path.basename(path)[:-4]
        clips += cut_clips(path, "taishanese", "dli:" + lesson, sensevoice, chinese)
    print(f"DLI Taishanese clips: {len(clips)}", flush=True)
    cantonese_records = [json.loads(line) for line in open(os.path.join(CANTONESE_FOLDER, "index.jsonl"))]
    random.seed(3)
    random.shuffle(cantonese_records)
    cantonese_clips = []
    taishanese_words = ("台山", "Taishan", "Toisan", "Toishan", "Hoisan", "開平", "恩平", "四邑")
    for record in cantonese_records:
        if any(word in (record.get("title") or "") for word in taishanese_words):
            continue
        path = os.path.join(CANTONESE_FOLDER, "audio", f"{record['id']}.wav")
        if os.path.exists(path) and record["duration"] < 3600:
            cantonese_clips += cut_clips(path, "cantonese", "yt:" + record["id"], sensevoice, {"yue"})[:40]
        if len(cantonese_clips) >= 1.3 * len(clips):
            break
    print(f"Cantonese clips: {len(cantonese_clips)}", flush=True)
    modern = []
    for path in sorted(glob.glob(os.path.join(MODERN_TAISHANESE_FOLDER, "audio", "*.wav"))):
        modern += cut_clips(path, "taishanese", "modern:" + os.path.basename(path)[:-4], sensevoice, chinese)
    print(f"modern Taishanese test clips: {len(modern)}", flush=True)
    with open(os.path.join(WORK_FOLDER, "clips.jsonl"), "w") as output:
        for clip in clips + cantonese_clips + modern:
            output.write(json.dumps(clip) + "\n")


# ---------- features: Whisper encoder, mean-pooled ----------

def old_tape(audio):
    band = scipy.signal.butter(4, [300, 3400], "bandpass", fs=SAMPLE_RATE, output="sos")
    return (scipy.signal.sosfilt(band, audio) + np.random.randn(len(audio)) * 0.003).astype(np.float32)


def modern_room(audio):
    response = np.random.randn(int(0.3 * SAMPLE_RATE)) * np.exp(-6.9 * np.arange(int(0.3 * SAMPLE_RATE)) / (0.3 * SAMPLE_RATE))
    response[0] = 1.0
    reverberant = scipy.signal.fftconvolve(audio, response / np.sqrt(np.sum(response ** 2)))[: len(audio)]
    return (reverberant + np.random.randn(len(audio)) * 0.01 * np.std(audio)).astype(np.float32)


def features():
    import soundfile
    from faster_whisper import WhisperModel
    from faster_whisper.feature_extractor import FeatureExtractor
    import ctranslate2
    model = WhisperModel("large-v3", device="cuda", compute_type="int8_float16")
    extractor = FeatureExtractor(feature_size=128)
    clips = [json.loads(line) for line in open(os.path.join(WORK_FOLDER, "clips.jsonl"))]
    vectors, kept = [], []
    random.seed(5)
    for index, clip in enumerate(clips):
        audio, _ = soundfile.read(clip["audio"], start=int(clip["start"] * SAMPLE_RATE), stop=int(clip["end"] * SAMPLE_RATE), dtype="float32")
        if clip["group"].startswith("yt:") and random.random() < 0.5:
            audio = old_tape(audio)          # Cantonese that sounds like 1960s tape
        if clip["group"].startswith("dli:") and random.random() < 0.5:
            audio = modern_room(audio)       # Taishanese that sounds like a modern room
        audio = speech_engines.clean_audio(audio)
        mel = extractor(audio)[:, :3000]
        mel = np.pad(mel, ((0, 0), (0, 3000 - mel.shape[1])))
        encoded = model.model.encode(ctranslate2.StorageView.from_array(mel[None].astype(np.float32)), to_cpu=True)
        frames = int(len(audio) / SAMPLE_RATE * 50)  # encoder frames are 20 ms
        vectors.append(np.asarray(encoded)[0, : max(1, frames)].mean(axis=0))
        kept.append(clip)
        if index % 500 == 0:
            print(f"features {index}/{len(clips)}", flush=True)
    np.save(os.path.join(WORK_FOLDER, "features.npy"), np.array(vectors, dtype=np.float32))
    with open(os.path.join(WORK_FOLDER, "features_clips.jsonl"), "w") as output:
        for clip in kept:
            output.write(json.dumps(clip) + "\n")


# ---------- train + evaluate ----------

def train():
    import torch
    vectors = np.load(os.path.join(WORK_FOLDER, "features.npy"))
    clips = [json.loads(line) for line in open(os.path.join(WORK_FOLDER, "features_clips.jsonl"))]
    labels = np.array([1 if clip["label"] == "taishanese" else 0 for clip in clips])
    groups = [clip["group"] for clip in clips]
    is_modern = np.array([group.startswith("modern:") for group in groups])
    held_out_groups = {group for group in set(groups) if not group.startswith("modern:") and hash(group) % 5 == 0}
    is_test = np.array([group in held_out_groups for group in groups])
    is_train = ~is_test & ~is_modern
    mean, spread = vectors[is_train].mean(axis=0), vectors[is_train].std(axis=0) + 1e-6
    normalised = torch.tensor((vectors - mean) / spread)
    classifier = torch.nn.Sequential(torch.nn.Linear(vectors.shape[1], 128), torch.nn.ReLU(), torch.nn.Dropout(0.3), torch.nn.Linear(128, 1))
    optimizer = torch.optim.AdamW(classifier.parameters(), lr=1e-3, weight_decay=1e-2)
    targets = torch.tensor(labels, dtype=torch.float32)
    train_rows = torch.tensor(np.flatnonzero(is_train))
    for epoch in range(60):
        classifier.train()
        for batch in train_rows[torch.randperm(len(train_rows))].split(256):
            loss = torch.nn.functional.binary_cross_entropy_with_logits(classifier(normalised[batch]).squeeze(1), targets[batch])
            optimizer.zero_grad(); loss.backward(); optimizer.step()
    classifier.eval()
    with torch.no_grad():
        probability = torch.sigmoid(classifier(normalised).squeeze(1)).numpy()
    for name, rows in (("held-out DLI lessons + Cantonese videos", is_test), ("MODERN Taishanese YouTube (never trained on)", is_modern)):
        if rows.sum():
            correct = ((probability[rows] > 0.5) == labels[rows].astype(bool)).mean()
            per_label = {label: f"{((probability[rows & (labels == value)] > 0.5) == bool(value)).mean():.1%} of {int((rows & (labels == value)).sum())}"
                         for label, value in (("taishanese", 1), ("cantonese", 0)) if (rows & (labels == value)).sum()}
            print(f"{name}: accuracy {correct:.1%}  {per_label}")
    torch.save({"state": classifier.state_dict(), "mean": mean, "spread": spread}, os.path.join(WORK_FOLDER, "taishanese_detector.pt"))


if __name__ == "__main__":
    {"prepare": prepare, "features": features, "train": train}[sys.argv[1]]()
