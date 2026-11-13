"""Where do Polylang's sentences and Google Translate disagree most?

Reads the built page (../index.html) and google_ref.json, scores every sentence by how similar the app's
version is to Google's (characters for Chinese, words for the rest), and writes the least similar ones to
../docs/google-check.md for review. Low similarity is not an error by itself: Google is often wrong for
Cantonese, and natural speech differs from Google's literal output. It is a list of places to look.

Usage (from source/): python3 google_compare.py [rows per language]
"""
import difflib
import json
import os
import re
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
SHOW = int(sys.argv[1]) if len(sys.argv) > 1 else 25
NAMES = {"yue": "Cantonese", "cmn": "Mandarin", "es": "Spanish", "fr": "French", "de": "German", "pt": "Portuguese",
         "tr": "Turkish", "he": "Hebrew", "fa": "Persian (written)", "ar": "Arabic (MSA)"}
APP_FIELD = {"fa": "fa_w"}          # Google writes formal Persian, so compare with the written sentence


def phrases():
    html = open(os.path.join(HERE, "..", "index.html"), encoding="utf-8").read()
    start = html.index("const PHRASES = ") + len("const PHRASES = ")
    return json.JSONDecoder().raw_decode(html[start:])[0]


def app_sentence(p, lang):
    value = p.get(APP_FIELD.get(lang, lang))
    if isinstance(value, dict):
        return value.get("t", "")
    if not value:
        return ""
    joiner = "" if lang in ("yue", "cmn") else " "
    return re.sub(r"[（(][^）)]*[）)]", "", joiner.join(t["hz"] for t in value))


def units(text, lang):
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    if lang in ("yue", "cmn"):
        return [c for c in text if "一" <= c <= "鿿"]
    return re.findall(r"\w+", text)


def similarity(a, b, lang):
    return difflib.SequenceMatcher(None, units(a, lang), units(b, lang)).ratio()


def main():
    ref = json.load(open(os.path.join(HERE, "google_ref.json"), encoding="utf-8"))
    out = ["# Polylang vs Google Translate", "",
           "Lowest similarity first. Similarity compares characters (Chinese) or words (other languages);",
           "a low score means *look here*, not *wrong*. Regenerate with `cd source && python3 google_compare.py`.", ""]
    for lang, name in NAMES.items():
        rows = []
        for p in phrases():
            google = ref.get(lang, {}).get(p["en"]) or (p.get("g_" + lang) if lang in ("yue", "cmn") else None)
            mine = app_sentence(p, lang)
            if google and mine:
                rows.append((similarity(mine, google, lang), p["en"], mine, google))
        if not rows:
            continue
        rows.sort()
        mean = sum(r[0] for r in rows) / len(rows)
        out += [f"## {name}", "", f"{len(rows)} sentences compared, average similarity {mean:.2f}.", "",
                "| similarity | English | Polylang | Google |", "|---|---|---|---|"]
        out += [f"| {s:.2f} | {en} | {mine} | {google} |" for s, en, mine, google in rows[:SHOW]]
        out.append("")
        print(f"{name}: {len(rows)} compared, mean {mean:.2f}")
    path = os.path.join(HERE, "..", "docs", "google-check.md")
    open(path, "w", encoding="utf-8").write("\n".join(out) + "\n")
    print("wrote", os.path.relpath(path))


if __name__ == "__main__":
    main()
