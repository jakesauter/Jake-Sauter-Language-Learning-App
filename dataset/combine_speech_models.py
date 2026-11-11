"""What are several speech models worth together? Uses the outputs evaluate_speech_models.py already saved, so it
needs no graphics card.

    .venv/bin/python dataset/combine_speech_models.py wsyue qwen3_Qwen3-ASR-1.7B sensevoice_sensevoice_small_yue whisper_large-v3

Prints each model alone, then three ways of combining them (the first model named breaks ties):

    closest to the others   per clip, keep the version that differs least from the other versions (needs no reference)
    character vote          line the versions up character by character and keep what most of them wrote
    best possible pick      per clip, keep whichever version is closest to the reference: the ceiling for any picker

and how much the models' agreement says about whether a line can be trusted.
"""

import collections
import difflib
import json
import os
import sys

import jiwer
from rapidfuzz.distance import Levenshtein

from evaluate_speech_models import OUTPUT_FOLDER, comparable, same_words


def saved_rows(model_name, which):
    path = os.path.join(OUTPUT_FOLDER, f"{model_name}__{which}.jsonl")
    rows = [json.loads(line) for line in open(path) if line.strip()]
    return {(row["video"], row["start"], row["end"]): row for row in rows}


def closest_to_the_others(versions):
    """The version with the smallest total distance to the rest. With two versions this is always the first."""
    def distance_to_the_rest(version):
        return sum(Levenshtein.normalized_distance(version, other) for other in versions)
    return min(versions, key=distance_to_the_rest)


def character_vote(versions):
    """Line every version up against the first one and keep, at each position, the character most versions wrote."""
    first = versions[0]
    votes_at = [collections.Counter({character: 1}) for character in first]
    votes_between = [collections.Counter() for _ in range(len(first) + 1)]  # text the others put before position i
    for other in versions[1:]:
        for step, first_from, first_to, other_from, other_to in difflib.SequenceMatcher(None, first, other, autojunk=False).get_opcodes():
            shared = min(first_to - first_from, other_to - other_from) if step in ("equal", "replace") else 0
            for offset in range(shared):
                votes_at[first_from + offset][other[other_from + offset]] += 1
            for position in range(first_from + shared, first_to):
                votes_at[position][""] += 1  # this version has nothing here
            if other_to - other_from > shared:
                votes_between[first_from + shared][other[other_from + shared: other_to]] += 1
    voted = []
    for position in range(len(first) + 1):
        if votes_between[position]:
            extra_text, extra_votes = votes_between[position].most_common(1)[0]
            if extra_votes > len(versions) / 2:
                voted.append(extra_text)
        if position < len(first):
            voted.append(max(votes_at[position].items(), key=lambda vote: (vote[1], vote[0] == first[position]))[0])
    return "".join(voted)


def error_rates(references, heard):
    strict = jiwer.cer([comparable(text) for text in references], [comparable(text) or " " for text in heard])
    lenient = jiwer.cer([same_words(text) for text in references], [same_words(text) or " " for text in heard])
    return strict, lenient


def main(which, model_names):
    rows_by_model = [saved_rows(model_name, which) for model_name in model_names]
    clips = [clip for clip in rows_by_model[0] if all(clip in rows for rows in rows_by_model)
             and comparable(rows_by_model[0][clip]["reference"])]
    references = [rows_by_model[0][clip]["reference"] for clip in clips]
    versions_by_clip = [[same_words(rows[clip]["heard"]) for rows in rows_by_model] for clip in clips]

    def show(label, heard):
        strict, lenient = error_rates(references, heard)
        print(f"  {label:44s} {lenient:>10.1%} {strict:>7.1%}")

    print(f"{which}: {len(clips)} clips\n  {'':44s} {'same words':>10s} {'strict':>7s}")
    for model_name, rows in zip(model_names, rows_by_model):
        show(model_name, [rows[clip]["heard"] for clip in clips])
    show("closest to the others", [closest_to_the_others(versions) for versions in versions_by_clip])
    show("character vote", [character_vote(versions) for versions in versions_by_clip])
    show("best possible pick", [min(versions, key=lambda version: Levenshtein.distance(version, same_words(reference)))
                                for versions, reference in zip(versions_by_clip, references)])

    # Does agreement between the first two models tell us which lines to trust?
    print("  when the first two models...")
    for label, wanted in (("agree exactly", lambda distance: distance == 0), ("differ a little (under 20%)", lambda distance: 0 < distance < 0.2),
                          ("differ a lot", lambda distance: distance >= 0.2)):
        chosen = [index for index, versions in enumerate(versions_by_clip)
                  if wanted(Levenshtein.normalized_distance(versions[0], versions[1]))]
        if chosen:
            _, lenient = error_rates([references[index] for index in chosen], [versions_by_clip[index][0] for index in chosen])
            print(f"    {label:30s} {len(chosen) / len(clips):>5.0%} of clips, first model's error there {lenient:.1%}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
