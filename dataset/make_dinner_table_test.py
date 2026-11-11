"""Turn the clean public test clips into dinner-table conditions, so models are scored where they will be used.

Each hand-transcribed clip gets what our real dinner recording has: the sound of a room (a decaying echo), the
actual background of our dinner (taken from the gaps between speech in a real recording, at the loudness measured
there: speech 7 to 19 dB over the room), and, for half the clips, a second quieter voice talking over it.
The transcript stays the truth, so the error rate still means something.

    .venv/bin/python dataset/make_dinner_table_test.py /mnt/storage/datasets/own_recordings/dinner_test.jsonl [english]

Writes /mnt/storage/datasets/public_eval/wsyue_table_test.jsonl (test set "table" in evaluate_speech_models.py), or
with "english", english_table_test.jsonl from the English clips (test set "english_table").
"""

import json
import os
import sys

import numpy as np
import scipy.signal
import soundfile

PUBLIC_FOLDER = "/mnt/storage/datasets/public_eval"
SAMPLE_RATE = 16000
SPEECH_OVER_ROOM_DB = (5.0, 15.0)        # measured on the real dinner: 7 dB (10th percentile) to 19 dB (90th), median 13
SPEECH_OVER_OTHER_VOICE_DB = (6.0, 12.0)
ECHO_SECONDS = (0.3, 0.7)                # how long the room rings (a living or dining room)


def loudness(audio):
    return float(np.sqrt(np.mean(audio ** 2)) + 1e-9)


def room_background(recording_test_file):
    """The stretches between speech in a real recording, joined into one long background track."""
    pieces = [json.loads(line) for line in open(recording_test_file) if line.strip()]
    audio, _ = soundfile.read(pieces[0]["audio"], dtype="float32")
    gaps, previous_end = [], 0.0
    for piece in pieces:
        if piece["start"] - previous_end > 0.5:
            gaps.append(audio[int((previous_end + 0.15) * SAMPLE_RATE): int((piece["start"] - 0.15) * SAMPLE_RATE)])
        previous_end = piece["end"]
    return np.concatenate(gaps)


def with_room_echo(audio, random):
    """A simple room: the direct sound plus a tail of reflections that dies away."""
    echo_seconds = random.uniform(*ECHO_SECONDS)
    tail_length = int(echo_seconds * SAMPLE_RATE)
    tail = random.standard_normal(tail_length) * np.exp(-6.9 * np.arange(tail_length) / tail_length)  # down 60 dB at the end
    tail[: int(0.003 * SAMPLE_RATE)] = 0
    tail *= 0.7 / np.sqrt(np.sum(tail ** 2))  # reflections carry about half the energy of the direct sound
    impulse = np.concatenate([[1.0], tail])
    return scipy.signal.fftconvolve(audio, impulse)[: len(audio)].astype(np.float32)


def main(recording_test_file, test_name="wsyue"):
    random = np.random.default_rng(2026)
    clean_test = os.path.join(PUBLIC_FOLDER, f"{test_name}_short_test.jsonl")
    output_audio = os.path.join(PUBLIC_FOLDER, f"{test_name}_table")
    output_file = os.path.join(PUBLIC_FOLDER, f"{test_name}_table_test.jsonl")
    clips = [json.loads(line) for line in open(clean_test) if line.strip()]
    background = room_background(recording_test_file)
    os.makedirs(output_audio, exist_ok=True)
    with open(output_file, "w") as output:
        for index, clip in enumerate(clips):
            speech, _ = soundfile.read(clip["audio"], dtype="float32")
            speech = with_room_echo(speech, random)
            speech_level = loudness(speech)
            start = int(random.integers(0, len(background) - len(speech)))
            room = background[start: start + len(speech)]
            room_db = random.uniform(*SPEECH_OVER_ROOM_DB)
            mixed = speech + room * (speech_level / loudness(room)) / 10 ** (room_db / 20)
            other_voice_db = None
            if index % 2:
                other, _ = soundfile.read(clips[int(random.integers(0, len(clips)))]["audio"], dtype="float32")
                other = with_room_echo(np.resize(other, len(speech)), random)
                other_voice_db = random.uniform(*SPEECH_OVER_OTHER_VOICE_DB)
                mixed = mixed + other * (speech_level / loudness(other)) / 10 ** (other_voice_db / 20)
            mixed = (mixed * min(1.0, 0.95 / (np.max(np.abs(mixed)) + 1e-9))).astype(np.float32)
            path = os.path.join(output_audio, os.path.splitext(os.path.basename(clip["audio"]))[0] + ".wav")
            soundfile.write(path, mixed, SAMPLE_RATE, subtype="PCM_16")
            output.write(json.dumps({**clip, "audio": path, "source": f"{test_name} + dinner table", "room_db": round(room_db, 1),
                                     "other_voice_db": other_voice_db and round(other_voice_db, 1)}, ensure_ascii=False) + "\n")
    print(f"{len(clips)} clips with room echo and real dinner background; {len(clips) // 2} also have a second voice")


if __name__ == "__main__":
    main(*sys.argv[1:3])
