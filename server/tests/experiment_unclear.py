"""How often does the translator now admit "(unclear)" on real dinner lines, and what does it keep?"""
import asyncio, json, sys
import translation

lines = [line for line in json.load(open(sys.argv[1]))["digest_lines"] if line["language"] != "en"]

async def run():
    results = []
    for index, line in enumerate(lines):
        earlier = [entry["text"] for entry in lines[max(0, index - 4):index]]
        english = "".join([piece async for piece in translation.stream_translation(line["text"], "tsn", "en", None, earlier)]).strip()
        results.append((line["text"], line["en"], english))
    return results

results = asyncio.run(run())
unclear = [r for r in results if r[2].lower().startswith("(unclear")]
print(f"{len(unclear)} of {len(results)} Cantonese lines now marked unclear ({100*len(unclear)//len(results)}%)\n")
print("examples now marked unclear (old translation -> new):")
for text, old, new in unclear[:8]:
    print(f"  {text[:40]:40s} | {old[:45]:45s} -> {new[:40]}")
print("\nexamples still translated:")
for text, old, new in [r for r in results if not r[2].lower().startswith("(unclear")][:10]:
    print(f"  {text[:40]:40s} -> {new[:60]}")
