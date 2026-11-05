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

order = ["Greetings", "Getting to know you", "Family", "Visiting", "Meals", "Small Talk", "Plans", "Around the House", "Road Trip", "Travel", "Weather", "Work", "School", "Hobbies", "Swimming", "Running & Biking", "Shopping", "Pets", "Health", "Helping Out", "Learning", "Holidays", "Goodbyes"]
data.sort(key = lambda p: order.index(p["cat"]))

for p in data:
    n = len(p["gloss"])
    for lang in ("yue", "cmn", "tsn"):
        for tok in p[lang]:
            assert all(0 <= r < n for r in tok["refs"]), (p["en"], lang, tok)

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
page = page.replace("__WORDS__", open("words.json", encoding = "utf-8").read().replace("</", "<\\/"))

open(sys.argv[1], "w", encoding = "utf-8").write(page)

print("phrases:", len(data), "bytes:", len(page.encode()))
