"""One short English meaning per Chinese character (traditional + simplified) from CC-CEDICT, for the
"Where the words come from" panel. Only characters the app can show are kept."""
import re

SKIP = re.compile(r"^(surname|variant of|old variant|archaic variant|erhua variant|Japanese variant|abbr\. for|CL:|see |used in|\((Cant\.|old|literary|dialect|loanword|coll\.|Tw|archaic|math\.|chemistry|physics|music|Buddhism)\)|radical in Chinese|Kangxi radical|component in|\(onom\.\)|\(phonetic\)|\(sound\))", re.I)


def clean(s):
    s = re.sub(r"\[[^\]]*\]", "", s)              # pinyin refs
    s = re.sub(r"\|", "", s)
    s = re.sub(r"\((CL|also pr|loanword|coll|Tw|old|lit|fig)[^)]*\)", "", s)
    s = re.sub(r"\balso pr\..*$", "", s)
    s = re.sub(r"^\((bound form|Tw|coll\.|fig\.|lit\.|formal|literary|old|archaic)\)\s*", "", s)
    s = re.sub(r"\s+", " ", s).strip(" ;,")
    return s


def char_meanings(path, wanted):
    best = {}
    for line in open(path, encoding = "utf-8"):
        if line.startswith("#"):
            continue
        m = re.match(r"(\S+) (\S+) \[([^\]]+)\] /(.*)/", line)
        if not m:
            continue
        trad, simp, pin, senses = m.groups()
        if len(trad) != 1 or not (trad in wanted or simp in wanted):
            continue
        proper = pin[:1].isupper()
        good = [clean(x) for x in senses.split("/") if not SKIP.match(x.strip())]
        good = [g if len(g) <= 40 else re.sub(r"\s*\(.*", "", g) for g in good if g]
        good = [g if len(g) <= 40 else g[:40].rsplit(" ", 1)[0] for g in good if g]
        good = sorted(good, key = lambda g: not g.startswith("(Cantonese)"))
        good = [g.replace("(Cantonese) ", "") for g in good]
        if not good:
            continue
        bits = []
        for g in good:
            for b in g.split(";"):
                b = re.sub(r"^\((of sth|of sb|of a person|bound form)\)\s*", "", b.strip()).strip()
                b2 = re.sub(r"\s*\([^)]*\)", "", b).strip()
                b = b2 or b
                if b and not re.match(r"^(classifier|opposite|measure word|-)", b) and b not in bits:
                    bits.append(b)
        if not bits:
            continue
        text = bits[0] if len(bits) == 1 or len(bits[0]) + len(bits[1]) > 28 else bits[0] + "; " + bits[1]
        rank = (proper, )                             # common-noun readings beat names
        for c in {trad, simp}:
            if c in wanted and (c not in best or rank < best[c][0]):
                best[c] = (rank, text)
    return {c: t for c, (r, t) in best.items()}


# Cantonese everyday characters whose CC-CEDICT first sense is a Mandarin or literary one.
OVERRIDE = {"啦": "(soft ending: so, then)", "呀": "(soft ending)", "喇": "(change-of-state ending)", "没": "not; not have", "沒": "not; not have", "了": "done; finished", "吗": "(question ending)", "嗎": "(question ending)", "么": "(word ending)", "麼": "(word ending)", "係": "is; to be", "咗": "(marks a finished action)", "嘅": "'s; of", "喺": "at; in", "冇": "not have", "嚟": "come",
            "睇": "look; watch", "啱": "right; just", "咩": "what", "乜": "what", "嘢": "thing; stuff", "噉": "like this; so",
            "咁": "so; such", "哋": "(plural marker)", "佢": "he; she; it", "唔": "not", "嗰": "that", "呢": "this", "邊": "which; side"}


def build_table(path, text):
    wanted = set(re.findall(r"[㐀-鿿]", text))
    out = char_meanings(path, wanted)
    out.update({c: v for c, v in OVERRIDE.items() if c in wanted})
    return out
