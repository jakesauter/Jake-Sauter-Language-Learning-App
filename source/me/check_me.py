"""Check me/*.txt (added languages) against the phrase list before building.

Usage (from source/): python3 me/check_me.py [built index.html] [me files...]
Reports: unknown sentence numbers or English, missing lines, refs outside the
English chunks, tokens without a transliteration where one is expected, full
sentences without " || ", and English chunks that no token points at (warning).
"""
import glob
import json
import re
import sys

built = sys.argv[1] if len(sys.argv) > 1 else "../index.html"
files = sys.argv[2:] or sorted(glob.glob("me/*.txt"))
html = open(built, encoding="utf-8").read()
start = html.index("const PHRASES = ") + len("const PHRASES = ")
phrases, _ = json.JSONDecoder().raw_decode(html[start:])

TOKEN_LINES, FULL_LINES = ("pt", "fa", "la", "he", "tr"), ("fw", "eg", "ms")
NEEDS_TRANSLIT = ("fa", "la", "he")
errors = warnings = 0


def problem(kind, where, text):
    global errors, warnings
    if kind == "error":
        errors += 1
    else:
        warnings += 1
    print(f"{kind.upper():7} {where}: {text}")


for path in files:
    blocks, current = [], None
    for number, line in enumerate(open(path, encoding="utf-8"), 1):
        line = line.rstrip("\n")
        if line.startswith("= "):
            current = {"head": line[2:], "at": f"{path}:{number}", "lines": {}}
            blocks.append(current)
        elif current is not None and line[2:4] == ": ":
            current["lines"][line[:2]] = line[4:]
    for block in blocks:
        key, _, english = block["head"].partition(" ")
        where = block["at"]
        if not key.isdigit() or int(key) >= len(phrases) or phrases[int(key)]["en"] != english.strip():
            problem("error", where, f"sentence {block['head']!r} doesn't match the phrase list")
            continue
        chunks = len(phrases[int(key)]["gloss"])
        for tag in TOKEN_LINES + FULL_LINES:
            if tag not in block["lines"]:
                problem("error", where, f"missing {tag}: line")
        for tag in FULL_LINES:
            if tag in block["lines"] and " || " not in block["lines"][tag]:
                problem("error", where, f"{tag}: needs 'sentence || transliteration'")
        for tag in TOKEN_LINES:
            if tag not in block["lines"]:
                continue
            covered = set()
            for token in block["lines"][tag].split(" ; "):
                word, slash, refs = token.rpartition("/")
                if not slash or not word.strip():
                    problem("error", where, f"{tag}: token {token!r} has no /refs")
                    continue
                if tag in NEEDS_TRANSLIT and not re.search(r"\{[^}]+\}$", word.strip()):
                    problem("error", where, f"{tag}: token {word!r} has no {{transliteration}}")
                if refs.strip() == "-":
                    continue
                for ref in refs.split(","):
                    if not ref.strip().isdigit() or not 0 <= int(ref) < chunks:
                        problem("error", where, f"{tag}: ref {ref!r} is outside 0..{chunks - 1}")
                    else:
                        covered.add(int(ref))
            missing = sorted(set(range(chunks)) - covered)
            if missing:
                problem("warning", where, f"{tag}: no token points at English chunk(s) {missing}")

print(f"{len(files)} file(s): {errors} error(s), {warnings} warning(s)")
sys.exit(1 if errors else 0)
