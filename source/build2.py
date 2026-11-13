import json
import sys

from phrases import PHRASES
from tsn import TSN
from parse_batch import parse


def tokens(rows, sure = False):

    out = []

    for r in rows:
        t = {"hz": r[0], "rom": r[1], "refs": list(r[2])}
        if sure:
            t["sure"] = r[3] if len(r) > 3 else True
        out.append(t)

    return out


lines = lambda f: [l.strip() for l in open(f, encoding = "utf-8") if l.strip()]

data = []

for p, t, g in zip(PHRASES, TSN, lines("google_yue.txt")):

    data.append({
        "cat": p["cat"], "en": p["en"], "gloss": p["gloss"],
        "yue": tokens(p["yue"]), "cmn": tokens(p["cmn"]), "tsn": tokens(t["tsn"], sure = True),
        "tip": p["tip"], "tsn_tip": t["tip"], "g_yue": g,
    })

for e, gy, gc in zip(parse("batch2.txt"), lines("google2_yue.txt"), lines("google2_cmn.txt")):

    e["g_yue"], e["g_cmn"] = gy, gc
    data.append(e)

en3 = lines("batches/batch3_en.txt")
gy3 = dict(zip(en3, lines("batches/batch3_yue.txt")))
gc3 = dict(zip(en3, lines("batches/batch3_cmn.txt")))

for part in "abcd":
    for e in parse(f"batches/batch3{part}.txt"):
        e["g_yue"], e["g_cmn"] = gy3[e["en"]], gc3[e["en"]]
        data.append(e)

data += parse("batches/batch4a.txt")

from parse_batch import eu_tokens

EU = {}
for part in "abc":
    cur = None
    for line in open(f"eu/{part}.txt", encoding = "utf-8"):
        line = line.rstrip("\n")
        if line.startswith("#"):
            cur = int(line[1:]); EU[cur] = {}
        elif line[:3] in ("s: ", "f: ", "d: "):
            EU[cur][{"s": "es", "f": "fr", "d": "de"}[line[0]]] = eu_tokens(line[3:])

assert len(data) == 329 and sorted(EU) == list(range(329)), (len(data), len(EU))
for i, p in enumerate(data):
    p.update(EU[i])

data += parse("batches/jokes.txt")
data += parse("batches/daily.txt")

en6 = lines("batches/batch6_en.txt")
gy6 = dict(zip(en6, lines("batches/batch6_yue.txt")))
gc6 = dict(zip(en6, lines("batches/batch6_cmn.txt")))
for e in json.load(open("batches/batch6_cards.json", encoding = "utf-8")):
    e["g_yue"], e["g_cmn"] = gy6[e["en"]], gc6[e["en"]]
    data.append(e)

en5 = lines("batches/batch5_en.txt")
gy5 = dict(zip(en5, lines("batches/batch5_yue.txt")))
gc5 = dict(zip(en5, lines("batches/batch5_cmn.txt")))
for part in "ab":
    for e in parse(f"batches/batch5{part}.txt"):
        e["g_yue"], e["g_cmn"] = gy5[e["en"]], gc5[e["en"]]
        data.append(e)

order = ["Start Here", "Talking About the Day", "Quick Patterns", "Greetings", "Getting to know you", "Family", "Visiting", "Meals", "Small Talk", "Plans", "Around the House", "Cooking Together", "Family Events", "Road Trip", "Travel", "Weather", "Work", "School", "Hobbies", "Swimming", "Running & Biking", "Shopping", "Pets", "Health", "Helping Out", "Learning", "Holidays", "Feelings", "Joking Around", "Goodbyes"]
data.sort(key = lambda p: order.index(p["cat"]))

for p in data:
    n = len(p["gloss"])
    for lang in ("yue", "cmn", "tsn", "es", "fr", "de"):
        assert p.get(lang), (p["en"], lang)
        for tok in p[lang]:
            assert all(0 <= r < n for r in tok["refs"]), (p["en"], lang, tok)

import glob, re as _re

def me_tokens(line):
    out = []
    for part in line.split(" ; "):
        w, refs = part.rsplit("/", 1)
        m = _re.match(r"^(.*?)\{(.*)\}$", w.strip())
        hz, rom = (m.group(1).strip(), m.group(2).strip()) if m else (w.strip(), "")
        refs = refs.strip()
        out.append({"hz": hz, "rom": rom, "refs": [] if refs == "-" else [int(r) for r in refs.split(",")]})
    return out

ME_TOK = {"fa": "fa", "la": "apc", "he": "he", "tr": "tr", "pt": "pt"}
ME_FULL = {"fw": "fa_w", "eg": "arz", "ms": "ar"}
by_en = {p["en"]: p for p in data}
miss = []
for f in sorted(glob.glob("me/*.txt")):
    cur = None
    for line in open(f, encoding = "utf-8"):
        line = line.rstrip("\n")
        if line.startswith("= "):
            k, _, en = line[2:].partition(" ")
            cur = data[int(k)] if k.isdigit() and int(k) < len(data) and data[int(k)]["en"] == en.strip() else None
            if cur is None: miss.append(line[2:])
        elif cur is not None and line[:4].rstrip(": ") in ME_TOK and line[2:4] == ": ":
            toks = me_tokens(line[4:])
            n = len(cur["gloss"])
            toks = [dict(t, refs = [r for r in t["refs"] if 0 <= r < n]) for t in toks]
            cur[ME_TOK[line[:2]]] = toks
        elif cur is not None and line[:2] in ME_FULL and line[2:4] == ": ":
            t, _, r = line[4:].partition(" || ")
            cur[ME_FULL[line[:2]]] = {"t": t.strip(), "r": r.strip()}
if miss: print("me: unmatched", len(miss), miss[:3])
print("me coverage:", {k: sum(1 for p in data if p.get(k)) for k in ["pt", "fa", "fa_w", "apc", "arz", "ar", "he", "tr"]})

from romanize import annotate, sentence_rom

for p in data:
    p["tip"] = annotate(p.get("tip", ""), p, "yue")
    p["tsn_tip"] = annotate(p.get("tsn_tip", ""), p, "tsn")
    if p.get("g_yue"):
        p["g_yue_rom"] = sentence_rom(p["g_yue"], "yue")
    if p.get("g_cmn"):
        p["g_cmn_rom"] = sentence_rom(p["g_cmn"], "cmn")

page = open("page.html", encoding = "utf-8").read()

from romanize import tag_standalone
g0 = page.index("  const GRAMMAR = {")
g1 = page.index("  const MEASURES = new Set")
page = page[:g0] + tag_standalone(page[g0:g1]) + page[g1:]
page = page.replace("__PHRASES__", json.dumps(data, ensure_ascii = False))
lex = json.load(open("words.json", encoding = "utf-8"))
for f in ("eu/core_eu.txt", "eu/topic_eu.txt"):
    for line in open(f, encoding = "utf-8"):
        en, es, fr, de = line.rstrip("\n").split("|")
        e = lex.setdefault(en.lower(), {})
        e.setdefault("s", es); e.setdefault("f", fr); e.setdefault("d", de)
# The word list goes after the app's script, as data the app reads when first needed (see lex_data in page.html).
words_json = json.dumps(lex, ensure_ascii = False, separators = (",", ":")).replace("</", "<\\/")
page = page.rstrip("\n") + '\n<script type="application/json" id="polylang-words">' + words_json + '</script>\n'


open(sys.argv[1], "w", encoding = "utf-8").write(page)

print("phrases:", len(data), "bytes:", len(page.encode()))
