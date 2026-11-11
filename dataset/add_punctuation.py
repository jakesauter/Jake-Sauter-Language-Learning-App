"""FireRed and SenseVoice write no punctuation, Qwen3-ASR does, and Qwen3's text translates better. Is that the
punctuation? This writes punctuated (or unpunctuated) copies of saved recognizer output so evaluate_end_to_end.py
can score them like any other recognizer.

    ~/venvs/asr-next/bin/python dataset/add_punctuation.py add   firered2_FireRedASR2-AED__pairs__raw
    ~/venvs/asr-next/bin/python dataset/add_punctuation.py strip qwen3_Qwen3-ASR-1.7B__pairs__raw

"add" uses FireRedPunc (a small BERT model from the FireRedASR2S release) and saves <name>__punc.jsonl;
"strip" removes punctuation and saves <name>__nopunc.jsonl.
"""

import json
import os
import re
import sys

SPEECH_OUTPUT_FOLDER = "/mnt/storage/datasets/youtube_cc_cantonese/speech_eval"
PUNCTUATION_MODEL = os.environ.get("POLYLANG_PUNC", "/mnt/storage/models/hf/FireRedPunc")
FIRERED_CODE = "/mnt/storage/models/hf/FireRedASR2S/fireredasr2s"  # import fireredpunc alone, not the whole system
PUNCTUATION = re.compile(r"[，。？！、,.?!；;：:「」“”\"']")
BATCH_SIZE = 32


def load_punctuation_model():
    import torch
    sys.path.insert(0, FIRERED_CODE)
    from fireredpunc.punc import FireRedPunc, FireRedPuncConfig
    return FireRedPunc.from_pretrained(PUNCTUATION_MODEL, FireRedPuncConfig(use_gpu=torch.cuda.is_available()))


def punctuate(model, texts):
    """The same texts with punctuation added; empty texts stay empty."""
    punctuated = list(texts)
    to_do = [index for index, text in enumerate(texts) if text.strip()]
    for batch_start in range(0, len(to_do), BATCH_SIZE):
        batch = to_do[batch_start: batch_start + BATCH_SIZE]
        for index, result in zip(batch, model.process([texts[index] for index in batch])):
            punctuated[index] = result["punc_text"]
    return punctuated


def main(action, name):
    rows = [json.loads(line) for line in open(os.path.join(SPEECH_OUTPUT_FOLDER, name + ".jsonl")) if line.strip()]
    if action == "add":
        heard = punctuate(load_punctuation_model(), [row["heard"] for row in rows])
    else:
        heard = [PUNCTUATION.sub("", row["heard"]) for row in rows]
    suffix = "__punc" if action == "add" else "__nopunc"
    with open(os.path.join(SPEECH_OUTPUT_FOLDER, name + suffix + ".jsonl"), "w") as output:
        for row, text in zip(rows, heard):
            output.write(json.dumps({**row, "heard": text}, ensure_ascii=False) + "\n")
    for row, text in list(zip(rows, heard))[200:203]:
        print(row["heard"], "->", text)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
