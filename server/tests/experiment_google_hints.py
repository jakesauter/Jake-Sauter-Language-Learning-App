"""Dinner lines: understanding with vs without Google Translate hints (trust levels + examples)."""
import asyncio, json, os, sys
import translation
translation.GOOGLE_KEY_FILE = os.path.expanduser("~/.config/polylang/google_translate_key")
lines = [line for line in json.load(open(sys.argv[1]))["digest_lines"] if line["language"] != "en"][:80]

async def run(with_hints):
    os.environ["POLYLANG_GOOGLE_HINTS"] = "1" if with_hints else "0"
    out = []
    for line in lines:
        versions = list(dict.fromkeys(v for v in line.get("hyps", {}).values() if v)) or [line["text"]]
        out.append(await translation.understand_line(versions, "tsn"))
    return out

without, with_hints = asyncio.run(run(False)), asyncio.run(run(True))
level = lambda r: "unclear" if r["unclear"] else ("rough" if r["clarity"] == 3 else "clear")
for name, results in (("without Google hints", without), ("with Google hints", with_hints)):
    counts = {k: sum(level(r) == k for r in results) for k in ("clear", "rough", "unclear")}
    print(f"{name:22s} {counts}")
print("\nexamples (without -> with):")
for line, a, b in list(zip(lines, without, with_hints))[10:24]:
    print(f"  {' / '.join(list(dict.fromkeys(line['hyps'].values()))[:2])[:44]:44s}\n      {level(a):7s} {a['english'][:55]}\n      {level(b):7s} {b['english'][:55]}")
