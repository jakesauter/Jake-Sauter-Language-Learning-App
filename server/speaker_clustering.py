"""Field-standard speaker clustering: sliding-window voice fingerprints + auto-tuned spectral clustering.

Spectral clustering with normalized maximum eigengap (NME-SC; Park et al., arXiv 2003.02405): for each candidate
row-pruning level p, keep each fingerprint's p most similar neighbours, build the graph Laplacian, and measure the
largest eigengap. The p with the best gap-to-pruning ratio fixes both the graph and the number of speakers, so
there is no threshold to hand-tune.
"""

import numpy as np
import scipy.cluster.vq
import scipy.linalg

import speakers

WINDOW_SECONDS = 1.5
HOP_SECONDS = 0.75
SAMPLE_RATE = 16000


def sliding_windows(start_sample, end_sample):
    window, hop = int(WINDOW_SECONDS * SAMPLE_RATE), int(HOP_SECONDS * SAMPLE_RATE)
    if end_sample - start_sample <= window:
        return [(start_sample, end_sample)]
    windows = [(position, position + window) for position in range(start_sample, end_sample - window + 1, hop)]
    if windows[-1][1] < end_sample:
        windows.append((end_sample - window, end_sample))
    return windows


def window_fingerprints(audio, speech_regions):
    """Every speech region cut into overlapping 1.5 s windows, each with a voice fingerprint."""
    windows, fingerprints = [], []
    for region_start, region_end in speech_regions:
        if region_end - region_start < int(0.5 * SAMPLE_RATE):
            continue
        for window_start, window_end in sliding_windows(region_start, region_end):
            windows.append((window_start, window_end))
            fingerprints.append(speakers.voice_fingerprint(audio[window_start:window_end]))
    return windows, np.array(fingerprints)


def _laplacian_eigen(affinity):
    degree = np.diag(affinity.sum(axis=1))
    return scipy.linalg.eigh(degree - affinity)


def nme_spectral_clustering(fingerprints, most_speakers=8, fixed_speaker_count=None):
    count = len(fingerprints)
    if count < 3:
        return np.zeros(count, dtype=int)
    similarity = fingerprints @ fingerprints.T
    similarity = (similarity - similarity.min()) / (similarity.max() - similarity.min() + 1e-9)
    np.fill_diagonal(similarity, 1.0)
    order = np.argsort(-similarity, axis=1)
    best = None
    largest_pruning = max(2, count // 4)
    for pruning in range(2, largest_pruning + 1, max(1, largest_pruning // 40)):
        kept = np.zeros_like(similarity)
        rows = np.arange(count)[:, None]
        kept[rows, order[:, :pruning]] = similarity[rows, order[:, :pruning]]
        affinity = 0.5 * (kept + kept.T)
        eigenvalues, _ = _laplacian_eigen(affinity)
        gaps = np.diff(eigenvalues[: most_speakers + 1])
        speaker_count = int(np.argmax(gaps)) + 1
        normalized_gap = gaps.max() / (eigenvalues[-1] + 1e-9)
        ratio = (pruning / count) / (normalized_gap + 1e-9)
        if best is None or ratio < best[0]:
            best = (ratio, pruning, speaker_count, affinity)
    _, _, speaker_count, affinity = best
    if fixed_speaker_count:
        speaker_count = fixed_speaker_count
    _, eigenvectors = _laplacian_eigen(affinity)
    embedding = eigenvectors[:, :speaker_count]
    np.random.seed(0)
    _, labels = scipy.cluster.vq.kmeans2(embedding, speaker_count, minit="++", iter=100)
    return labels


def fold_small_clusters(labels, fingerprints, smallest_share=0.03):
    """Clusters holding under 3% of the speech are usually one voice split off; move them to the nearest real speaker."""
    labels = labels.copy()
    sizes = np.bincount(labels)
    real = [label for label in range(len(sizes)) if sizes[label] >= smallest_share * len(labels)] or [int(np.argmax(sizes))]
    centroids = {label: fingerprints[labels == label].mean(axis=0) for label in real}
    for index, label in enumerate(labels):
        if label not in centroids:
            labels[index] = max(centroids, key=lambda candidate: float(fingerprints[index] @ centroids[candidate]))
    renumber = {label: rank for rank, label in enumerate(sorted(set(labels), key=lambda l: -np.sum(labels == l)))}
    return np.array([renumber[label] for label in labels])


def smooth_labels(labels, windows, neighbours=1):
    """Majority vote with each window's immediate neighbours in the same speech region (no one-window flicker)."""
    smoothed = labels.copy()
    for index in range(len(labels)):
        same_region = [other for other in range(max(0, index - neighbours), min(len(labels), index + neighbours + 1))
                       if windows[other][0] < windows[index][1] + 16000 and windows[index][0] < windows[other][1] + 16000]
        votes = np.bincount(labels[same_region])
        if votes.max() > votes[labels[index]]:
            smoothed[index] = int(np.argmax(votes))
    return smoothed


def diarize(audio, speech_regions, most_speakers=8):
    """Speech regions -> (windows, speaker label per window), field-standard pipeline with cleanup."""
    windows, fingerprints = window_fingerprints(audio, speech_regions)
    if len(windows) < 3:
        return windows, np.zeros(len(windows), dtype=int)
    labels = nme_spectral_clustering(fingerprints, most_speakers=most_speakers)
    labels = fold_small_clusters(labels, fingerprints)
    return windows, smooth_labels(labels, windows)
