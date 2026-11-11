"""Cut a saved live recording into the same pieces live mode would hear, as a test set with no answers.

There is no transcript to score against: the point is to run every speech model and translator on real
dinner-table audio and read their lines side by side.

    .venv/bin/python dataset/cut_recording.py dinner /mnt/storage/polylang-data/people/<person>/conversations/<id>/recordings/<file>.wav

Writes /mnt/storage/datasets/own_recordings/<name>_test.jsonl, which evaluate_speech_models.py reads as test set <name>.
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "server"))
import live_session  # noqa: E402
import speech_engines  # noqa: E402

OUTPUT_FOLDER = "/mnt/storage/datasets/own_recordings"
SAMPLE_RATE = speech_engines.SAMPLE_RATE


def main(name, recording_path):
    audio = speech_engines.decode_audio_file(recording_path)
    clips = []
    # Live mode closes an utterance after a pause, then splits it again at short pauses to judge each piece's language.
    for utterance_start, utterance_end in live_session.find_speech(audio):
        utterance = audio[utterance_start:utterance_end]
        for piece_start, piece_end in live_session.pieces_for_language_detection(utterance):
            start, end = utterance_start + piece_start, utterance_start + piece_end
            if end - start >= SAMPLE_RATE // 4:
                clips.append({"audio": recording_path, "start": round(start / SAMPLE_RATE, 2), "end": round(end / SAMPLE_RATE, 2),
                              "text": "", "video": name, "split": "test", "source": "recording"})
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    with open(os.path.join(OUTPUT_FOLDER, f"{name}_test.jsonl"), "w") as output:
        for clip in clips:
            output.write(json.dumps(clip, ensure_ascii=False) + "\n")
    speech_minutes = sum(clip["end"] - clip["start"] for clip in clips) / 60
    lengths = sorted(clip["end"] - clip["start"] for clip in clips)
    print(f"{len(clips)} pieces, {speech_minutes:.1f} minutes of speech out of {len(audio) / SAMPLE_RATE / 60:.1f}; "
          f"median piece {lengths[len(lengths) // 2]:.1f}s, longest {lengths[-1]:.1f}s")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
