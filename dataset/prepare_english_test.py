"""Build an English test set, because about half of what is said at our dinners is English.

Uses LibriSpeech test-clean (Panayotov et al. 2015, openslr.org/12, CC BY 4.0): read English from 40 speakers,
transcribed by hand. It is cleaner and more formal than dinner talk; make_dinner_table_test.py then adds the
room echo, our real dinner background and a second voice, as it does for the Cantonese set.

    1. download openslr.org/resources/12/test-clean.tar.gz and unpack it into PUBLIC_FOLDER/librispeech
    2. .venv/bin/python dataset/prepare_english_test.py
    3. .venv/bin/python dataset/make_dinner_table_test.py /mnt/storage/datasets/own_recordings/dinner_test.jsonl english
"""

import glob
import json
import os

import soundfile

PUBLIC_FOLDER = "/mnt/storage/datasets/public_eval"
LIBRISPEECH_FOLDER = os.path.join(PUBLIC_FOLDER, "librispeech", "LibriSpeech", "test-clean")
OUTPUT_FILE = os.path.join(PUBLIC_FOLDER, "english_short_test.jsonl")
CLIPS_PER_SPEAKER = 10
SHORTEST_SECONDS, LONGEST_SECONDS = 1.5, 15.0  # dinner lines are short


def main():
    clips = []
    for speaker_folder in sorted(glob.glob(os.path.join(LIBRISPEECH_FOLDER, "*"))):
        speaker_clips = []
        for transcript_file in sorted(glob.glob(os.path.join(speaker_folder, "*", "*.trans.txt"))):
            for line in open(transcript_file):
                utterance, _, text = line.strip().partition(" ")
                chapter_folder = os.path.dirname(transcript_file)
                audio = os.path.join(chapter_folder, utterance + ".flac")
                seconds = soundfile.info(audio).duration
                if SHORTEST_SECONDS <= seconds <= LONGEST_SECONDS:
                    speaker_clips.append({"video": "librispeech-" + os.path.basename(speaker_folder), "audio": audio,
                                          "start": 0.0, "end": round(seconds, 2), "text": text.lower()})
        clips += speaker_clips[:: max(1, len(speaker_clips) // CLIPS_PER_SPEAKER)][:CLIPS_PER_SPEAKER]
    with open(OUTPUT_FILE, "w") as output:
        for clip in clips:
            output.write(json.dumps(clip) + "\n")
    print(f"{len(clips)} English clips, {sum(clip['end'] for clip in clips) / 60:.0f} min, from {len({clip['video'] for clip in clips})} speakers")


if __name__ == "__main__":
    main()
