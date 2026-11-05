import json
import sys


def tokens(line, tsn):

    out = []

    for part in line.split(" ; "):
        hz, rom, refs = [x.strip() for x in part.split("/")]
        sure = not refs.endswith("?")
        refs = refs.rstrip("?")
        t = {"hz": hz, "rom": rom, "refs": [] if refs == "-" else [int(r) for r in refs.split(",")]}
        if tsn:
            t["sure"] = sure
        out.append(t)

    return out


def parse(path):

    entries = []
    cur = None

    for raw in open(path, encoding = "utf-8"):
        line = raw.rstrip("\n")
        if line.startswith("@ "):
            cat, en = [x.strip() for x in line[2:].split("|")]
            cur = {"cat": cat, "en": en}
            entries.append(cur)
        elif line.startswith("g: "):
            cur["gloss"] = [x.strip() for x in line[3:].split(" / ")]
        elif line.startswith("y: "):
            cur["yue"] = tokens(line[3:], False)
        elif line.startswith("m: "):
            cur["cmn"] = tokens(line[3:], False)
        elif line.startswith("t: "):
            cur["tsn"] = tokens(line[3:], True)
        elif line.startswith("n: "):
            cur["tip"] = line[3:].strip()
        elif line.startswith("nt: "):
            cur["tsn_tip"] = line[4:].strip()

    return entries


if __name__ == "__main__":

    es = parse(sys.argv[1])
    bad = 0

    for e in es:
        n = len(e["gloss"])
        for lang in ("yue", "cmn", "tsn"):
            for t in e[lang]:
                if any(r >= n for r in t["refs"]):
                    print("BAD REF", e["en"], lang, t); bad += 1
                if lang == "yue" and len(t["hz"]) != len(t["rom"].split()):
                    print("YUE SYL", e["en"], t)
        for k in range(n):
            if not any(k in t["refs"] for t in e["yue"]):
                print("gloss unmapped in yue:", e["en"], e["gloss"][k])

    print(len(es), "entries,", bad, "bad refs")
