"""Who is speaking: online speaker diarization with CAM++ voice fingerprints.

Each piece of speech gets a 192-number voice fingerprint (CAM++, runs on the CPU). A piece joins the most
similar known voice when the cosine similarity is high enough; otherwise it starts a new speaker. Each
speaker's fingerprint is the running average of their pieces, so it gets sturdier as the dinner goes on.
"""

import os

import numpy as np

CAMPPLUS_MODEL = os.environ.get("POLYLANG_CAMPPLUS", "/models/campplus.onnx")
SAME_SPEAKER_SIMILARITY = float(os.environ.get("POLYLANG_SAME_SPEAKER", "0.5"))
SHORTEST_PIECE_FOR_NEW_SPEAKER = 1.2   # seconds; shorter pieces can only join an existing voice
MOST_SPEAKERS = 12

_session = None


def _model():
    global _session
    if _session is None:
        import onnxruntime
        options = onnxruntime.SessionOptions()
        options.intra_op_num_threads = 2
        _session = onnxruntime.InferenceSession(CAMPPLUS_MODEL, sess_options=options, providers=["CPUExecutionProvider"])
    return _session


def voice_fingerprint(audio, sample_rate=16000):
    import torch
    import torchaudio.compliance.kaldi as kaldi
    waveform = torch.from_numpy(np.asarray(audio, dtype=np.float32)).unsqueeze(0)
    features = kaldi.fbank(waveform, num_mel_bins=80, dither=0, sample_frequency=sample_rate)
    features = features - features.mean(dim=0, keepdim=True)
    session = _model()
    embedding = session.run(None, {session.get_inputs()[0].name: features.unsqueeze(0).numpy()})[0][0]
    return embedding / (np.linalg.norm(embedding) + 1e-9)


class SpeakerTracker:
    def __init__(self):
        self.fingerprints = []   # running-average fingerprint per speaker
        self.piece_counts = []

    def identify(self, audio, sample_rate=16000):
        """Returns (speaker number starting at 1, similarity) or (None, 0) if too short to tell."""
        seconds = len(audio) / sample_rate
        if seconds < 0.5:
            return None, 0.0
        fingerprint = voice_fingerprint(audio, sample_rate)
        if self.fingerprints:
            similarities = [float(fingerprint @ known) for known in self.fingerprints]
            best = int(np.argmax(similarities))
            if similarities[best] >= SAME_SPEAKER_SIMILARITY or seconds < SHORTEST_PIECE_FOR_NEW_SPEAKER or len(self.fingerprints) >= MOST_SPEAKERS:
                count = self.piece_counts[best]
                updated = (self.fingerprints[best] * count + fingerprint) / (count + 1)
                self.fingerprints[best] = updated / (np.linalg.norm(updated) + 1e-9)
                self.piece_counts[best] += 1
                return best + 1, round(similarities[best], 3)
        if seconds < SHORTEST_PIECE_FOR_NEW_SPEAKER:
            return None, 0.0
        self.fingerprints.append(fingerprint)
        self.piece_counts.append(1)
        return len(self.fingerprints), 1.0
