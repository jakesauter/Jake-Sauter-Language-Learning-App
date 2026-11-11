"""Score translators on Cantonese -> English pairs with human references (chrF++, higher is better).

The Cantonese input is the human subtitle, so this measures translation alone, not speech recognition.
Each line gets the four lines before it as context, the same as live mode.

    .venv/bin/python dataset/evaluate_translation.py google understand:qwen2.5:7b plain:aya-expanse:8b
    .venv/bin/python dataset/evaluate_translation.py tatoeba hymt:hy-mt1.5:1.8b understand:qwen2.5:7b

    Start with "tatoeba" to use the public test (400 short everyday Cantonese sentences with English written by
    people, built by prepare_public_tests.py) instead of our YouTube subtitle pairs.
    POLYLANG_EVAL_ON_PROCESSOR=1 keeps the model off the graphics card (for when it is busy).

    google              Google Translate
    understand:<model>  the live "understand this line" step (picks/repairs the heard text, translates, rates clarity)
    plain:<model>       a plain translation prompt
    hymt:<model>        a dedicated translation model with its own fixed instruction (Tencent HY-MT), no context
    hymt-context:<model>  the same, given the earlier lines
    hymt-steady:<model>   the same with context, always picking the most likely word (no randomness)
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
from known_bad_videos import LEAVE_OUT  # noqa: E402

DATASET_FOLDER = "/mnt/storage/datasets/youtube_cc_cantonese"
PAIRS_FILE = os.path.join(DATASET_FOLDER, "translation_pairs.jsonl")
OUTPUT_FOLDER = os.path.join(DATASET_FOLDER, "translation_eval")
TATOEBA_FILE = "/mnt/storage/datasets/public_eval/tatoeba_yue_en.jsonl"
ON_PROCESSOR = {"num_gpu": 0} if os.environ.get("POLYLANG_EVAL_ON_PROCESSOR") else {}


async def translate_one(translator, text, earlier_lines):
    kind, _, model = translator.partition(":")
    if kind == "google":
        return await translation.translate_with_google(text, "yue", "en")
    if kind.startswith("hymt"):
        return await translation.translate_with_translation_model(
            text, "yue", "en", model, earlier_lines if kind != "hymt" else (),
            {**({"temperature": 0.0} if kind == "hymt-steady" else {}), **ON_PROCESSOR})
    translation.choose_provider = lambda source, target: "ollama:" + model
    if kind == "understand":
        answer = await translation.understand_line([text], "yue", "en", earlier_lines)
        return answer["english"]
    result = await translation.translate_text(text, "yue", "en", provider="ollama:" + model)
    return result["text"]


async def run(translator, pairs, test_name):
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    outputs, started = [], time.time()
    for index, pair in enumerate(pairs):
        # Tatoeba sentences are unrelated to each other, so they get no earlier lines.
        earlier = [earlier_pair["text"] for earlier_pair in pairs[max(0, index - 4): index]
                   if earlier_pair["video"] == pair["video"] and test_name != "tatoeba"]
        english = ""
        for attempt in range(5):  # Google rate-limits bursts; wait and retry
            try:
                english = await translate_one(translator, pair["text"], earlier)
                break
            except Exception as error:
                print(f"  {translator} attempt {attempt + 1} failed on {index}: {error}", flush=True)
                await asyncio.sleep(2 ** attempt * 5)
        outputs.append({"video": pair["video"], "cantonese": pair["text"], "reference": pair["english"], "english": english})
    file_name = ("" if test_name == "youtube" else test_name + "__") + translator.replace(":", "_").replace("/", "_") + ".jsonl"
    with open(os.path.join(OUTPUT_FOLDER, file_name), "w") as output:
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
    print(f"{test_name} {translator}: chrF++ {overall:.1f}  per video {per_video}  unclear {unclear}/{len(outputs)}  {seconds_per_line:.2f}s/line", flush=True)


def main(translators):
    test_name = "youtube"
    if translators[0] in ("tatoeba", "youtube"):
        test_name, translators = translators[0], translators[1:]
    pairs = [json.loads(line) for line in open(TATOEBA_FILE if test_name == "tatoeba" else PAIRS_FILE) if line.strip()]
    # Only pairs whose Chinese side is Cantonese as spoken (not written-Chinese subtitles), from videos we trust.
    pairs = [pair for pair in pairs if pair.get("chinese_is_spoken", True) and pair["video"] not in LEAVE_OUT]
    for translator in translators:
        asyncio.run(run(translator, pairs, test_name))


if __name__ == "__main__":
    main(sys.argv[1:])
