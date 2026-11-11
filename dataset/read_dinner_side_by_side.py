"""Our real dinner recording has no transcript, so the models are judged by reading: for each piece, what every
recognizer heard (and which language it thought it was), next to what live mode showed that night.

    .venv/bin/python dataset/read_dinner_side_by_side.py dinner [translator] > /mnt/storage/datasets/own_recordings/dinner_side_by_side.md

With a translator (e.g. hymt:hy-mt1.5:1.8b), the version the Cantonese recognizers agree on is translated the way
the new live path would. The output is private family conversation: keep it on this machine.
"""

import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "server"))
import speech_engines  # noqa: E402
import translation  # noqa: E402
from evaluate_speech_models import OUTPUT_FOLDER  # noqa: E402

# What live mode showed that night (lines.jsonl of the saved conversation), given as POLYLANG_LIVE_LINES.
LIVE_LINES = os.environ.get("POLYLANG_LIVE_LINES", "")
CANTONESE_RECOGNIZERS = ["firered2_FireRedASR2-AED", "qwen3_Qwen3-ASR-1.7B", "sensevoice_sensevoice_small_yue"]  # first one breaks ties


def saved(which, name):
    path = os.path.join(OUTPUT_FOLDER, f"{name}__{which}.jsonl")
    if not os.path.exists(path):
        return {}
    return {round(row["start"], 2): row for row in (json.loads(line) for line in open(path) if line.strip())}


def live_line_near(live_lines, start, end):
    """The line live mode showed that overlaps this piece most (live times are seconds into the recording)."""
    best, best_overlap = None, 0.0
    for line in live_lines:
        overlap = min(end, line.get("end", 0)) - max(start, line.get("start", 0))
        if overlap > best_overlap:
            best, best_overlap = line, overlap
    return best


async def main(which, translator=None):
    names = sorted({file_name[:-len(f"__{which}.jsonl")] for file_name in os.listdir(OUTPUT_FOLDER)
                    if file_name.endswith(f"__{which}.jsonl")}
                   | {file_name[:-len(f"__{which}__auto.jsonl")] + " (own language guess)" for file_name in os.listdir(OUTPUT_FOLDER)
                      if file_name.endswith(f"__{which}__auto.jsonl")})
    outputs = {name: saved(which + ("__auto" if name.endswith("(own language guess)") else ""), name.replace(" (own language guess)", ""))
               for name in names}
    live_lines = [json.loads(line) for line in open(LIVE_LINES) if line.strip()] if os.path.exists(LIVE_LINES) else []
    starts = sorted(set.union(*(set(rows) for rows in outputs.values())))
    earlier = []
    print(f"# {which}: {len(starts)} pieces, {len(names)} recognizer runs\n")
    for start in starts:
        any_row = next(rows[start] for rows in outputs.values() if start in rows)
        print(f"## {start:.1f}–{any_row['end']:.1f} s")
        live = live_line_near(live_lines, start, any_row["end"])
        if live:
            print(f"- **live that night**: {live.get('text', '')} → _{live.get('en', '')}_")
        for name in names:
            row = outputs[name].get(start)
            if row:
                print(f"- {name} [{row.get('language', '')}]: {speech_engines.to_common_script(row['heard'], 'yue')}")
        if translator:
            versions = [speech_engines.to_common_script(outputs[name][start]["heard"], "yue")
                        for name in CANTONESE_RECOGNIZERS if start in outputs.get(name, {})]
            versions = [version for version in versions if version and not speech_engines.is_repetition_loop(version)]
            if versions:
                kind, _, model = translator.partition(":")
                translation.choose_provider = lambda source, target: "ollama:" + model
                answer = await translation.understand_line(versions, "yue", "en", earlier[-4:])
                earlier.append(answer["said"])
                print(f"- **new path** (clarity {answer['clarity']}): {answer['said']} → _{answer['english']}_")
        print()


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None))
