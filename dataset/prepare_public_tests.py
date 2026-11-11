"""Build a test set from WenetSpeech-Yue's public benchmark (everyday Cantonese from many speakers, transcribed by hand).

Our own YouTube test clips come from six videos and their subtitles are loose, so they can't tell good models from
great ones. This set can: 600 clips from hundreds of speakers, each checked by several human annotators.

It also builds a translation test from the Tatoeba Challenge (University of Helsinki): short everyday Cantonese
sentences with English written by people, the closest public match to dinner-table talk.

    1. download ASLP-lab/WSYue-ASR-eval from Hugging Face and unpack Short/wav.tar.gz into PUBLIC_FOLDER/wsyue_short
    2. save github.com/Helsinki-NLP/Tatoeba-Challenge data/test/eng-zho/test.txt as PUBLIC_FOLDER/tatoeba/eng-zho.txt
    3. ~/venvs/asr-next/bin/python dataset/prepare_public_tests.py
"""

import json
import os
import random

import soundfile

PUBLIC_FOLDER = "/mnt/storage/datasets/public_eval"
TRANSCRIPTS = os.path.join(PUBLIC_FOLDER, "WSYue-ASR-eval", "Short", "content.txt")
AUDIO_FOLDER = os.path.join(PUBLIC_FOLDER, "wsyue_short", "wav_")
OUTPUT_FILE = os.path.join(PUBLIC_FOLDER, "wsyue_short_test.jsonl")
CLIPS_WANTED = 600
SHORTEST_SECONDS, FEWEST_CHARACTERS = 1.0, 4
AGE_GROUPS = {"青年（18~35）": "18-35", "中年（36~59）": "36-59", "老年（60岁及以上）": "60+", "少年（0~17）": "0-17"}
EMOTIONS = {"中性": "neutral", "高兴": "happy", "生气": "angry", "伤心": "sad", "害怕": "afraid", "厌恶": "disgusted", "惊讶": "surprised"}
GENDERS = {"男": "male", "女": "female"}


TATOEBA_FILE = os.path.join(PUBLIC_FOLDER, "tatoeba", "eng-zho.txt")
TATOEBA_OUTPUT = os.path.join(PUBLIC_FOLDER, "tatoeba_yue_en.jsonl")
SENTENCES_WANTED = 400


def build_translation_test():
    """Cantonese sentences (either script) with their English, one row per Cantonese sentence."""
    english_by_cantonese = {}
    for line in open(TATOEBA_FILE, encoding="utf-8"):
        fields = line.rstrip("\n").split("\t")
        if len(fields) == 4 and fields[1].startswith("yue"):
            english_by_cantonese.setdefault(fields[3], []).append(fields[2])
    sentences = sorted(english_by_cantonese)
    random.Random(2026).shuffle(sentences)
    with open(TATOEBA_OUTPUT, "w", encoding="utf-8") as output:
        for sentence in sentences[:SENTENCES_WANTED]:
            output.write(json.dumps({"video": "tatoeba", "text": sentence, "english": english_by_cantonese[sentence][0],
                                     "other_english": english_by_cantonese[sentence][1:], "chinese_is_spoken": True},
                                    ensure_ascii=False) + "\n")
    print(f"{min(SENTENCES_WANTED, len(sentences))} of {len(sentences)} Cantonese sentences with English")
    for sentence in sentences[:8]:
        print(f"  {sentence}  ->  {english_by_cantonese[sentence][0]}")


def main():
    build_translation_test()
    clips = []
    for line in open(TRANSCRIPTS, encoding="utf-8"):
        name, age, emotion, gender, text = line.rstrip("\n").split("\t")
        path = os.path.join(AUDIO_FOLDER, name)
        if not os.path.exists(path):
            continue
        details = soundfile.info(path)
        seconds = details.frames / details.samplerate
        chinese_characters = sum("一" <= character <= "鿿" for character in text)
        if details.samplerate != 16000 or seconds < SHORTEST_SECONDS or chinese_characters < FEWEST_CHARACTERS:
            continue
        clips.append({"audio": path, "start": 0.0, "end": round(seconds, 2), "text": text, "video": name[:-len(".wav")],
                      "age": AGE_GROUPS.get(age, age), "emotion": EMOTIONS.get(emotion, emotion),
                      "gender": GENDERS.get(gender, gender), "split": "test", "source": "wsyue"})
    random.Random(2026).shuffle(clips)  # the same clips every time, in an order with no pattern
    with open(OUTPUT_FILE, "w", encoding="utf-8") as output:
        for clip in clips[:CLIPS_WANTED]:
            output.write(json.dumps(clip, ensure_ascii=False) + "\n")
    chosen = clips[:CLIPS_WANTED]
    print(f"{len(chosen)} clips of {len(clips)} usable, {sum(clip['end'] for clip in chosen) / 60:.0f} minutes")
    for field in ("age", "gender", "emotion"):
        counts = {}
        for clip in chosen:
            counts[clip[field]] = counts.get(clip[field], 0) + 1
        print(f"  {field}: {counts}")
    for clip in chosen[:8]:
        print(f"  {clip['end']:.1f}s  {clip['text']}")


if __name__ == "__main__":
    main()
