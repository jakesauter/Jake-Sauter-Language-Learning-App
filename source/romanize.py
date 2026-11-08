import json
import os
import re

# Dictionary datasets (OpenCC, rime-cantonese, cc-cedict, pinyin-data, jieba,
# stephen-dictionary-data). Defaults to dl/ at the repo root.
DL = os.environ.get("POLYLANG_DL", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "dl"))

HAN = re.compile(r"[㐀-鿿豈-﫿\U00020000-\U0002ffff]+")


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


to_trad = lambda s: convert(s, ST_C, ST_P)
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
for k, v in rime(f"{DL}/rime-cantonese/jyut6ping3.phrase.dict.yaml").items():
    JP_W.setdefault(k, v)
JP_C = {k: v[0] for k, v in rime(f"{DL}/rime-cantonese/jyut6ping3.chars.dict.yaml", chars = True).items()}
JP_C.update({"呀": "aa3", "啦": "laa1", "喇": "laa3", "嘅": "ge3", "咗": "zo2", "㗎": "gaa3", "囉": "lo1", "吖": "aa1", "啫": "ze1", "喎": "wo3", "嘛": "maa3", "咩": "me1", "啲": "di1", "嗰": "go2", "佢": "keoi5", "冇": "mou5", "係": "hai6", "喺": "hai2"})


def segment(s, words, maxlen = 6):

    out, i = [], 0

    while i < len(s):
        for n in range(min(maxlen, len(s) - i), 0, -1):
            w = s[i:i + n]
            if w in words:
                out.append(words[w]); i += n; break
        else:
            return None

    return " ".join(out)


def jyutping(s):

    t = to_trad(s)
    words = dict(JP_C)
    words.update(JP_W)
    return segment(t, words, 5)


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
    i = s.index(v) if v in "ae" else s.rindex(v)
    return s[:i] + TONES[v][t - 1] + s[i + 1:]


PY_W = {}
for line in open(f"{DL}/cc-cedict/cedict_1_0_ts_utf-8_mdbg.txt", encoding = "utf-8"):
    if line.startswith("#"):
        continue
    m = re.match(r"^(\S+) (\S+) \[([^\]]+)\]", line)
    if not m:
        continue
    trad, simp, py = m.groups()
    if re.search(r"[A-Z]", py[:1]):
        continue
    if len(simp) < 2:
        continue
    val = " ".join(mark(x) for x in py.split())
    PY_W.setdefault(simp, val)
    PY_W.setdefault(trad, val)

for line in open(f"{DL}/pinyin-data/pinyin.txt", encoding = "utf-8"):
    m = re.match(r"^U\+([0-9A-F]+):\s*([^\s#]+)", line)
    if m:
        PY_W.setdefault(chr(int(m.group(1), 16)), m.group(2).split(",")[0])

PY_W.update({"吗": "ma", "嗎": "ma", "吧": "ba", "了": "le", "的": "de", "么": "me", "呢": "ne", "啊": "a", "们": "men", "们": "men", "着": "zhe", "过": "guo", "得": "de", "个": "ge", "汤": "tāng", "湯": "tāng", "一些": "yì xiē", "一下": "yí xià", "一点": "yì diǎn", "不是": "bú shì", "不要": "bú yào"})


def pinyin(s):

    return segment(s, PY_W, 6)


def tsn_rom(r):

    r = r.strip().strip("[]").replace("*", "").strip()
    r = re.sub(r"(\d)\((\d)\)", r"\1\2", r)
    r = r.split("/")[0].strip()
    return re.sub(r"\s+", " ", r)


TSN_W = {}
for e in json.load(open(f"{DL}/stephen-dictionary-data/data.json", encoding = "utf-8")):
    t, r = (e.get("taishanese") or "").strip(), tsn_rom(e.get("taishaneseRomanization") or "")
    if not t or not r or not HAN.fullmatch(t) or len(t) != len(r.split()):
        continue
    TSN_W.setdefault(t, r)
    TSN_W.setdefault(to_trad(t), r)


def taishanese(s):

    return segment(s, TSN_W, 6) or segment(to_simp(s), TSN_W, 6)


ROM_AFTER = re.compile(r"^\s*[\"“]?[a-zɔəɛŋɬüāáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜ]+\d*", re.I)
HAS_TONE = re.compile(r"\d|[āáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜ]")


def has_rom_after(text, end):

    m = ROM_AFTER.match(text[end:])
    return bool(m and HAS_TONE.search(m.group(0)))


def token_map(p, lang):

    m = {}
    toks = p.get(lang) or []
    for t in toks:
        m.setdefault(t["hz"], t["rom"])
    joined = "".join(t["hz"] for t in toks)
    m.setdefault(joined, " ".join(t["rom"] for t in toks))
    return m


def guess(run, p, prefer):

    maps = {l: token_map(p, l) for l in ("yue", "cmn", "tsn")}

    order = {"yue": ["yue", "cmn", "tsn"], "tsn": ["tsn", "yue", "cmn"], "cmn": ["cmn", "yue", "tsn"]}[prefer]
    for l in order:
        if run in maps[l]:
            return maps[l][run], l
        seg = segment(run, maps[l], 6)
        if seg:
            return seg, l

    if prefer == "tsn":
        r = taishanese(run)
        if r:
            return r, "tsn"
    if to_trad(run) != run or prefer == "cmn":
        return pinyin(run), "cmn"
    r = jyutping(run)
    if r:
        return r, "yue"
    return pinyin(run), "cmn"


MARKS = "āáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜ"
SYLT = r"(?:[a-zɔəɛŋɬü]*[" + MARKS + r"][a-zɔəɛŋɬü]*|[a-zɔəɛŋɬü]+[1-6]{1,3})"
AFTER = re.compile(r"\s+(" + SYLT + r"(?:\s+" + SYLT + r")*)(?![\w])", re.I)
STANDALONE = re.compile(r"(?<![\w⟨:])(" + SYLT + r"(?:\s+" + SYLT + r")*)(?![\w⟩])", re.I)


def lang_of(rom):

    if re.search("[" + MARKS + "]", rom):
        return "cmn"
    nums = re.findall(r"\d+", rom)
    if nums and all(len(n) == 1 for n in nums) and not re.search(r"[ɔəɛŋɬ]", rom):
        return "yue"
    return "tsn"


def tag_standalone(text):

    parts = re.split(r"(⟨[^⟩]*⟩)", text)
    out = []
    for part in parts:
        if part.startswith("⟨"):
            out.append(part)
            continue
        out.append(STANDALONE.sub(lambda m: "⟨" + lang_of(m.group(1)) + ":" + m.group(1) + "⟩", part))
    return "".join(out)


def annotate(text, p, prefer):

    text = text or ""
    out, last = [], 0

    for m in HAN.finditer(text):
        out.append(text[last:m.end()])
        last = m.end()
        a = AFTER.match(text, m.end())
        if a:
            words = a.group(1).split()
            take = words[:max(1, len(m.group(0)))]
            rom = " ".join(take)
            out.append(" ⟨" + lang_of(rom) + ":" + rom + "⟩")
            consumed = re.match(r"\s+" + r"\s+".join(re.escape(w) for w in take), text[m.end():])
            last = m.end() + consumed.end()
            continue
        r, l = guess(m.group(0), p, prefer)
        if r:
            out.append(" ⟨" + l + ":" + r + "⟩")

    out.append(text[last:])
    return tag_standalone("".join(out))


def sentence_rom(s, lang):

    runs = HAN.findall(s or "")
    if lang == "yue":
        parts = [jyutping(r) or "" for r in runs]
    else:
        parts = [pinyin(r) or "" for r in runs]
    return " ".join(x for x in parts if x)
