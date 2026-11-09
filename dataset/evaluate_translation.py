"""Score translators on Cantonese -> English pairs with human references (chrF++, higher is better).

The Cantonese input is the human subtitle, so this measures translation alone, not speech recognition.
Each line gets the four lines before it as context, the same as live mode.

    .venv/bin/python dataset/evaluate_translation.py google understand:qwen2.5:7b plain:aya-expanse:8b

    google              Google Translate
    understand:<model>  the live "understand this line" step (picks/repairs the heard text, translates, rates clarity)
    plain:<model>       a plain translation prompt
"""

import asyncio
import collections
import json
import os
import sys
import time

import sacrebleu

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "server"))
os.environ.setdefault("POLYLANG_GOOGLE_KEY_FILE", os.path.expanduser("~/.config/polylang/google_translate_key"))
import translation  # noqa: E402

DATASET_FOLDER = "/mnt/storage/datasets/youtube_cc_cantonese"
PAIRS_FILE = os.path.join(DATASET_FOLDER, "translation_pairs.jsonl")
OUTPUT_FOLDER = os.path.join(DATASET_FOLDER, "translation_eval")


async def translate_one(translator, text, earlier_lines):
    kind, _, model = translator.partition(":")
    if kind == "google":
        return await translation.translate_with_google(text, "yue", "en")
    translation.choose_provider = lambda source, target: "ollama:" + model
    if kind == "understand":
        answer = await translation.understand_line([text], "yue", "en", earlier_lines)
        return answer["english"]
    result = await translation.translate_text(text, "yue", "en", provider="ollama:" + model)
    return result["text"]


async def run(translator, pairs):
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    outputs, started = [], time.time()
    for index, pair in enumerate(pairs):
        earlier = [earlier_pair["text"] for earlier_pair in pairs[max(0, index - 4): index] if earlier_pair["video"] == pair["video"]]
        english = ""
        for attempt in range(5):  # Google rate-limits bursts; wait and retry
            try:
                english = await translate_one(translator, pair["text"], earlier)
                break
            except Exception as error:
                print(f"  {translator} attempt {attempt + 1} failed on {index}: {error}", flush=True)
                await asyncio.sleep(2 ** attempt * 5)
        outputs.append({"video": pair["video"], "cantonese": pair["text"], "reference": pair["english"], "english": english})
    with open(os.path.join(OUTPUT_FOLDER, translator.replace(":", "_").replace("/", "_") + ".jsonl"), "w") as output:
        for row in outputs:
            output.write(json.dumps(row, ensure_ascii=False) + "\n")
    seconds_per_line = (time.time() - started) / max(1, len(pairs))
    by_video = collections.defaultdict(list)
    for row in outputs:
        by_video[row["video"]].append(row)
    overall = sacrebleu.corpus_chrf([row["english"] for row in outputs], [[row["reference"] for row in outputs]], word_order=2).score
    per_video = {video: round(sacrebleu.corpus_chrf([r["english"] for r in rows], [[r["reference"] for r in rows]], word_order=2).score, 1)
                 for video, rows in by_video.items()}
    unclear = sum(row["english"] == "(unclear)" for row in outputs)
    print(f"{translator}: chrF++ {overall:.1f}  per video {per_video}  unclear {unclear}/{len(outputs)}  {seconds_per_line:.2f}s/line", flush=True)


def main(translators):
    pairs = [json.loads(line) for line in open(PAIRS_FILE) if line.strip()]
    pairs = [pair for pair in pairs if pair.get("chinese_is_spoken", True)]  # Cantonese text, not written-Chinese subtitles
    for translator in translators:
        asyncio.run(run(translator, pairs))


if __name__ == "__main__":
    main(sys.argv[1:])
