"""Stream an AMI meeting through live mode in real time; score live speaker labels (after re-clustering) vs official labels."""
import asyncio, sys
import numpy as np
from scipy.optimize import linear_sum_assignment
sys.path.insert(0, "tests")
import live_stream_client as client

audio_path, rttm_path = sys.argv[1], sys.argv[2]
events = asyncio.run(client.stream(audio_path, "ws://127.0.0.1:8000/live?languages=en&target=en&save=0", "https://coderx-legion-t730-28ico.tailf42501.ts.net"))
finals = {e["id"]: e for e in events if e["type"] == "final"}
first_labels = {line_id: final.get("speaker") for line_id, final in finals.items()}
latest = dict(first_labels)
updates = 0
for event in events:
    if event["type"] == "speakers":
        updates += 1
        latest.update({int(k): v for k, v in event["speakers"].items()})

reference = []
for line in open(rttm_path):
    f = line.split()
    reference.append((float(f[3]), float(f[3]) + float(f[4]), f[7]))

def score(labels):
    pairs = []
    for line_id, final in finals.items():
        if labels.get(line_id) is None:
            continue
        overlaps = {}
        for start, end, speaker in reference:
            overlap = min(end, final["end"]) - max(start, final["start"])
            if overlap > 0:
                overlaps[speaker] = overlaps.get(speaker, 0) + overlap
        if overlaps:
            pairs.append((max(overlaps, key=overlaps.get), labels[line_id]))
    names = sorted({p[0] for p in pairs}); numbers = sorted({p[1] for p in pairs})
    counts = np.zeros((len(names), len(numbers)))
    for name, number in pairs:
        counts[names.index(name), numbers.index(number)] += 1
    rows, cols = linear_sum_assignment(-counts)
    return 1 - counts[rows, cols].sum() / len(pairs), len(numbers), len(pairs)

for name, labels in (("instant labels (old live method)", first_labels), ("after live re-clustering (new)", latest)):
    error, found, lines = score(labels)
    print(f"{name:34s} lines with wrong speaker {error:6.1%}  ({found} speakers found, {lines} lines)")
print(f"re-clustering updates sent: {updates}; errors: {[e['error'] for e in events if e['type']=='error'] or 'none'}")
