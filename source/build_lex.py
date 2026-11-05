import json
import math
import re
import sys
from collections import defaultdict

DL = sys.argv[1]
OUT = sys.argv[2]


def load_opencc(name):

    m = {}

    for line in open(f"{DL}/OpenCC/data/dictionary/{name}", encoding = "utf-8"):
        if line.startswith("#") or "\t" not in line:
            continue
        k, v = line.rstrip("\n").split("\t")
        m[k] = v.split(" ")[0]

    return m


ST_C, ST_P = load_opencc("STCharacters.txt"), load_opencc("STPhrases.txt")
TS_C, TS_P = load_opencc("TSCharacters.txt"), load_opencc("TSPhrases.txt")


def convert(s, chars, phrases):

    out, i = [], 0

    while i < len(s):
        for n in range(min(6, len(s) - i), 1, -1):
            if s[i:i + n] in phrases:
                out.append(phrases[s[i:i + n]]); i += n; break
        else:
            out.append(chars.get(s[i], s[i])); i += 1

    return "".join(out)


KEEP = set("吃")
to_trad = lambda s: "".join(c if c in KEEP else convert(c, ST_C, ST_P) for c in s) if len(s) == 1 else "".join((c if c in KEEP else t) for c, t in zip(s, convert(s, ST_C, ST_P))) if len(convert(s, ST_C, ST_P)) == len(s) else convert(s, ST_C, ST_P)
to_simp = lambda s: convert(s, TS_C, TS_P)


def rime(path, chars = False):

    m, body = {}, False

    for line in open(path, encoding = "utf-8"):
        if line.startswith("..."):
            body = True; continue
        if not body or line.startswith("#") or "\t" not in line:
            continue
        parts = line.rstrip("\n").split("\t")
        if len(parts) < 2:
            continue
        w, jp = parts[0], parts[1]
        if chars:
            wt = float(parts[2].rstrip("%")) if len(parts) > 2 and parts[2].endswith("%") else 100.0
            if w not in m or wt > m[w][1]:
                m[w] = (jp, wt)
        elif w not in m:
            m[w] = jp

    return m


JP_W = rime(f"{DL}/rime-cantonese/jyut6ping3.words.dict.yaml")
JP_W.update({k: v for k, v in rime(f"{DL}/rime-cantonese/jyut6ping3.phrase.dict.yaml").items() if k not in JP_W})
JP_C = {k: v[0] for k, v in rime(f"{DL}/rime-cantonese/jyut6ping3.chars.dict.yaml", chars = True).items()}


def jyutping(trad):

    out, i = [], 0

    while i < len(trad):
        for n in range(min(5, len(trad) - i), 1, -1):
            if trad[i:i + n] in JP_W:
                out.append(JP_W[trad[i:i + n]]); i += n; break
        else:
            c = trad[i]
            if c not in JP_C:
                return None
            out.append(JP_C[c]); i += 1

    return " ".join(out)


TONES = {"a": "āáǎàa", "e": "ēéěèe", "i": "īíǐìi", "o": "ōóǒòo", "u": "ūúǔùu", "ü": "ǖǘǚǜü"}


def mark(syl):

    syl = syl.lower().replace("u:", "ü").replace("v", "ü")
    m = re.match(r"^([a-zü]+)([1-5])$", syl)
    if not m:
        return syl
    s, t = m.group(1), int(m.group(2))
    if t == 5:
        return s
    if "a" in s: v = "a"
    elif "e" in s: v = "e"
    elif "ou" in s: v = "o"
    else:
        vs = [c for c in s if c in TONES]
        if not vs:
            return s
        v = vs[-1]
    i = s.rindex(v) if v != "a" and v != "e" else s.index(v)
    return s[:i] + TONES[v][t - 1] + s[i + 1:]


pinyin = lambda p: " ".join(mark(x) for x in p.split())


FREQ = {}
for line in open(f"{DL}/jieba/jieba/dict.txt", encoding = "utf-8"):
    parts = line.split(" ")
    if len(parts) >= 2:
        FREQ[parts[0]] = int(parts[1])


BAD = re.compile(r"\b(surname|variant of|old variant|archaic|literary|classical|abbr|dialect|Tw|taiwan|used in|see |CL:|place name|old name|bound form|onom|honorific|euphemism|slang|vulgar|buddhism|chemistry)\b", re.I)


def clean_sense(s):

    s = re.sub(r"\([^)]*\)", " ", s)
    s = re.sub(r"\b(sb|sth|sb's|one's|oneself)\b", " ", s)
    s = s.lower().strip()
    s = re.sub(r"^(to|a|an|the) ", "", s)
    s = re.sub(r"[^a-z' -]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


CEDICT = defaultdict(list)

for line in open(f"{DL}/cc-cedict/cedict_1_0_ts_utf-8_mdbg.txt", encoding = "utf-8"):
    if line.startswith("#"):
        continue
    m = re.match(r"^(\S+) (\S+) \[([^\]]+)\] /(.*)/\s*$", line)
    if not m:
        continue
    trad, simp, py, defs = m.groups()
    if re.search(r"[A-Za-z0-9]", simp):
        continue
    f = FREQ.get(simp, 0)
    if f < 300:
        continue
    for pos, sense in enumerate(defs.split("/")):
        if BAD.search(sense):
            continue
        for piece in sense.split(";"):
            key = clean_sense(piece)
            if not key or len(key.split()) > 2 or len(key) < 2:
                continue
            score = math.log(f + 1) - pos * 0.7 - (0.5 if len(simp) > 3 else 0)
            CEDICT[key].append((score, trad, simp, py))


TSN_BY_YUE, TSN_BY_CMN, TSN_EN = {}, {}, defaultdict(list)


def tsn_rom(r):

    r = r.strip().strip("[]").replace("*", "").strip()
    r = re.sub(r"(\d)\((\d)\)", r"\1\2", r)
    r = r.split("/")[0].strip()
    return re.sub(r"\s+", " ", r)


for e in json.load(open(f"{DL}/stephen-dictionary-data/data.json", encoding = "utf-8")):
    t, r = (e.get("taishanese") or "").strip(), tsn_rom(e.get("taishaneseRomanization") or "")
    if not t or not r or re.search(r"[()*/?！？。，、a-zA-Z]", t):
        continue
    if len(t) != len(r.split()):
        continue
    entry = (to_trad(t), r)
    for y in re.split(r"[,，/、]", e.get("cantonese") or ""):
        y = y.strip()
        if y and not re.search(r"[()（）]", y):
            TSN_BY_YUE.setdefault(y, entry)
    for c in re.split(r"[,，/、]", e.get("mandarin") or ""):
        c = c.strip()
        if c and not re.search(r"[()（）]", c):
            TSN_BY_CMN.setdefault(c, entry)


def tsn_for(yue_trad, cmn_simp):

    y = to_simp(yue_trad)
    return TSN_BY_YUE.get(y) or TSN_BY_CMN.get(cmn_simp) or TSN_BY_YUE.get(cmn_simp)


LEX = {}

for line in open("core_words.txt", encoding = "utf-8"):
    line = line.strip()
    if not line:
        continue
    en, y, jp, c, py = line.split("|")
    t = tsn_for(y, c)
    LEX[en] = {"y": [y, jp, 1], "m": [c, pinyin(py)], "t": [t[0], t[1]] if t else None}


for key, cands in CEDICT.items():
    if key in LEX:
        continue
    cands.sort(key = lambda x: -x[0])
    score, trad, simp, py = cands[0]
    t = tsn_for(trad, simp)
    jp = jyutping(trad)
    if not jp:
        continue
    LEX[key] = {"y": [trad, jp, 0], "m": [simp, pinyin(py)], "t": [t[0], t[1]] if t else None}


json.dump(LEX, open(OUT, "w", encoding = "utf-8"), ensure_ascii = False, separators = (",", ":"))

print("keys:", len(LEX), "with tsn:", sum(1 for v in LEX.values() if v["t"]))
for k in ["eat", "beach", "grandma", "airport", "cook", "beautiful", "sunscreen", "hungry", "phone", "dog", "ice cream", "birthday", "computer", "dinner", "movie"]:
    print(k, LEX.get(k))
