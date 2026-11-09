"""Clarity-scored translation on real dinner lines: how many are flagged, and do the kept ones make sense?"""
import asyncio, json, sys
import translation
lines = [line for line in json.load(open(sys.argv[1]))["digest_lines"] if line["language"] != "en"]
async def run():
    out = []
    for index, line in enumerate(lines):
        earlier = [entry["text"] for entry in lines[max(0, index - 4):index]]
        out.append((line["text"], await translation.translate_with_clarity(line["text"], "tsn", "en", earlier)))
    return out
results = asyncio.run(run())
flagged = [r for r in results if r[1]["unclear"]]
print(f"{len(flagged)} of {len(results)} lines marked unclear ({100*len(flagged)//len(results)}%); clarity counts:",
      {score: sum(r[1]["clarity"] == score for r in results) for score in range(1, 6)})
print("\nmarked unclear:")
for text, result in flagged[:8]:
    print(f"  [{result['clarity']}] {text[:50]}")
print("\nkept (translated):")
for text, result in [r for r in results if not r[1]["unclear"]][:12]:
    print(f"  [{result['clarity']}] {text[:36]:36s} -> {result['english'][:60]}")
