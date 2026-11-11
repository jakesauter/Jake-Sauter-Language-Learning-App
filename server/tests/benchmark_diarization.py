"""Speaker confusion on AMI far-field meetings (official labels), for the current method vs field-standard NME-SC."""
import sys, time
import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.cluster.hierarchy import fcluster, linkage
import speech_engines, live_session, speakers, speaker_clustering

FRAME = 0.01

def reference_frames(rttm_path, total_frames):
    names, frames = {}, [set() for _ in range(total_frames)]
    for line in open(rttm_path):
        fields = line.split()
        start, duration, speaker = float(fields[3]), float(fields[4]), fields[7]
        index = names.setdefault(speaker, len(names))
        for frame in range(int(start / FRAME), min(total_frames, int((start + duration) / FRAME))):
            frames[frame].add(index)
    return frames, len(names)

def confusion(reference, hypothesis):
    """Share of single-speaker frames (that the system labeled) given to the wrong speaker, after best mapping."""
    pairs = [(next(iter(ref)), hyp) for ref, hyp in zip(reference, hypothesis) if len(ref) == 1 and hyp >= 0]
    if not pairs:
        return 1.0, 0.0
    ref_count, hyp_count = max(p[0] for p in pairs) + 1, max(p[1] for p in pairs) + 1
    counts = np.zeros((ref_count, hyp_count))
    for ref, hyp in pairs:
        counts[ref, hyp] += 1
    rows, cols = linear_sum_assignment(-counts)
    single = sum(1 for ref in reference if len(ref) == 1)
    return 1 - counts[rows, cols].sum() / len(pairs), len(pairs) / single

for meeting in sys.argv[1:]:
    audio = speech_engines.decode_audio_file(f"/mnt/storage/benchmarks/ami/{meeting}.wav")
    total_frames = int(len(audio) / 16000 / FRAME)
    reference, true_speakers = reference_frames(f"/mnt/storage/benchmarks/ami/{meeting}.rttm", total_frames)
    pieces = live_session.pieces_for_language_detection(audio)
    print(f"\n{meeting}: {len(audio)/16000/60:.1f} min, {true_speakers} speakers, {len(pieces)} speech pieces", flush=True)

    # A: current — one fingerprint per piece, Ward with the digest's speaker-count rule
    started = time.time()
    voiced = [(s, e) for s, e in pieces if e - s >= 16000]
    fingerprints = np.array([speakers.voice_fingerprint(audio[s:e]) for s, e in voiced])
    guess = max(1, min(6, len(voiced) // 25 + 1))
    labels = fcluster(linkage(fingerprints, method="ward"), t=guess, criterion="maxclust") - 1
    hypothesis = np.full(total_frames, -1)
    for (s, e), label in zip(voiced, labels):
        hypothesis[int(s / 16000 / FRAME):int(e / 16000 / FRAME)] = label
    error, coverage = confusion(reference, hypothesis)
    print(f"  A current (piece + Ward, guessed {guess})      speaker confusion {error:6.1%}  (covers {coverage:.0%} of single-speaker speech, {time.time()-started:.0f}s)", flush=True)

    # B/C: sliding windows + NME-SC (auto count) / oracle count
    started = time.time()
    windows, window_fps = speaker_clustering.window_fingerprints(audio, pieces)
    raw = speaker_clustering.nme_spectral_clustering(window_fps)
    folded = speaker_clustering.fold_small_clusters(raw, window_fps)
    variants = {"B windows + NME-SC (auto count)": raw, "D B + fold tiny clusters": folded,
                "E D + smoothing (shipped)": speaker_clustering.smooth_labels(folded, windows)}
    for name, labels in variants.items():
        votes = np.zeros((total_frames, labels.max() + 1))
        for (s, e), label in zip(windows, labels):
            votes[int(s / 16000 / FRAME):int(e / 16000 / FRAME), label] += 1
        hypothesis = np.where(votes.sum(axis=1) > 0, votes.argmax(axis=1), -1)
        error, coverage = confusion(reference, hypothesis)
        print(f"  {name:42s} speaker confusion {error:6.1%}  (found {labels.max()+1} speakers, covers {coverage:.0%}, {time.time()-started:.0f}s)", flush=True)
