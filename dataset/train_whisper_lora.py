"""Fine-tune Whisper large-v3 for dinner-table Cantonese with LoRA, on an 8 GB GPU.

Recipe (standard for low-resource Whisper adaptation):
  - 8-bit base weights + LoRA adapters on the attention projections, gradient checkpointing
  - far-field augmentation: synthetic room reverb, real dinner background noise, distance-like gain
  - the same light audio conditioning used at inference (low-cut + leveling), so train matches live

    ~/venvs/train/bin/python dataset/train_whisper_lora.py --steps 2000 --output /mnt/storage/models/whisper-yue-lora
    ~/venvs/train/bin/python dataset/train_whisper_lora.py --evaluate-only [--adapter PATH]
"""

import argparse
import glob
import json
import os
import random
import time

import numpy as np
import scipy.signal
import soundfile
import torch

DATASET_FOLDER = "/mnt/storage/datasets/youtube_cc_cantonese"
NOISE_BANK_FILE = os.path.join(DATASET_FOLDER, "dinner_noise_bank.npy")
BASE_MODEL = "openai/whisper-large-v3"
SAMPLE_RATE = 16000


# ---------- data ----------

def load_segments(split):
    segments = []
    for name in ("gold_segments.jsonl", "pseudo_segments.jsonl"):
        path = os.path.join(DATASET_FOLDER, name)
        if os.path.exists(path):
            segments += [json.loads(line) for line in open(path) if line.strip()]
    test_videos = {segment["video"] for segment in segments if segment["split"] == "test"}
    chosen = [segment for segment in segments if segment["split"] == split and 0.5 < segment["end"] - segment["start"] <= 28]
    if split == "train":
        chosen = [segment for segment in chosen if segment["video"] not in test_videos]  # never train on a test video
    return chosen


def read_clip(segment):
    start, end = int(segment["start"] * SAMPLE_RATE), int(segment["end"] * SAMPLE_RATE)
    audio, _ = soundfile.read(segment["audio"], start=start, stop=end, dtype="float32")
    return audio


def build_noise_bank():
    """Non-speech stretches of the real dinner recordings: clatter, room tone, background chatter."""
    if os.path.exists(NOISE_BANK_FILE):
        return np.load(NOISE_BANK_FILE, allow_pickle=True)
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "server"))
    from faster_whisper.vad import VadOptions, get_speech_timestamps
    chunks = []
    for path in glob.glob("/mnt/storage/polylang-data/people/*/conversations/*/recordings/*.wav"):
        audio, _ = soundfile.read(path, dtype="float32")
        speech = get_speech_timestamps(audio, VadOptions(min_silence_duration_ms=300, speech_pad_ms=100))
        previous_end = 0
        for region in speech + [{"start": len(audio), "end": len(audio)}]:
            if region["start"] - previous_end > SAMPLE_RATE:
                chunks.append(audio[previous_end:region["start"]])
            previous_end = region["end"]
    bank = np.array(chunks, dtype=object)
    np.save(NOISE_BANK_FILE, bank, allow_pickle=True)
    print(f"noise bank: {len(chunks)} chunks, {sum(len(c) for c in chunks) / SAMPLE_RATE / 60:.1f} min of real dinner background")
    return bank


def synthetic_room_response(reverb_seconds):
    length = int(reverb_seconds * SAMPLE_RATE)
    decay = np.exp(-6.9 * np.arange(length) / length)  # 60 dB decay over the reverb time
    response = np.random.randn(length) * decay
    response[0] = 1.0
    return response / np.sqrt(np.sum(response ** 2))


def far_field(audio, noise_bank):
    """Make a clean clip sound like a phone in the middle of a dinner table."""
    if random.random() < 0.5:
        audio = scipy.signal.fftconvolve(audio, synthetic_room_response(random.uniform(0.2, 0.7)))[: len(audio)]
    if len(noise_bank) and random.random() < 0.8:
        noise = noise_bank[random.randrange(len(noise_bank))]
        noise = np.tile(noise, int(np.ceil(len(audio) / len(noise))) + 1)
        offset = random.randrange(max(1, len(noise) - len(audio)))
        noise = noise[offset: offset + len(audio)]
        speech_power, noise_power = np.mean(audio ** 2) + 1e-9, np.mean(noise ** 2) + 1e-9
        audio = audio + noise * np.sqrt(speech_power / (noise_power * 10 ** (random.uniform(5, 25) / 10)))
    return (audio * 10 ** (random.uniform(-12, 6) / 20)).astype(np.float32)


def condition(audio):
    """Same as speech_engines.clean_audio at inference: 120 Hz low-cut, then level to a fixed loudness."""
    low_cut = scipy.signal.butter(4, 120, "highpass", fs=SAMPLE_RATE, output="sos")
    filtered = scipy.signal.sosfilt(low_cut, audio)
    return np.clip(filtered * (0.08 / (np.sqrt(np.mean(filtered ** 2)) + 1e-9)), -1, 1).astype(np.float32)


# ---------- model ----------

def load_model(adapter=None, for_training=False):
    from peft import LoraConfig, PeftModel, get_peft_model, prepare_model_for_kbit_training
    from transformers import BitsAndBytesConfig, WhisperForConditionalGeneration, WhisperProcessor
    processor = WhisperProcessor.from_pretrained(BASE_MODEL, language="cantonese", task="transcribe")
    model = WhisperForConditionalGeneration.from_pretrained(
        BASE_MODEL, quantization_config=BitsAndBytesConfig(load_in_8bit=True), device_map={"": 0})
    model.config.forced_decoder_ids = None
    model.generation_config.language, model.generation_config.task = "cantonese", "transcribe"
    if adapter:
        model = PeftModel.from_pretrained(model, adapter, is_trainable=for_training)
    elif for_training:
        model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)
        model = get_peft_model(model, LoraConfig(r=32, lora_alpha=64, lora_dropout=0.05,
                                                 target_modules=["q_proj", "k_proj", "v_proj", "out_proj"]))
    if for_training:
        model.config.use_cache = False
        model.print_trainable_parameters()
    return processor, model


def character_error_rate(references, hypotheses):
    import jiwer
    from opencc import OpenCC
    to_hong_kong = OpenCC("s2hk")
    keep = lambda text: "".join(c for c in to_hong_kong.convert(text) if c.isalnum()).lower()
    pairs = [(keep(r), keep(h)) for r, h in zip(references, hypotheses) if keep(r)]
    return jiwer.cer([p[0] for p in pairs], [p[1] for p in pairs])


@torch.no_grad()
def evaluate(processor, model, segments, label):
    model.eval()
    references, hypotheses = [], []
    for start in range(0, len(segments), 8):
        batch = segments[start:start + 8]
        clips = [condition(read_clip(segment)) for segment in batch]
        features = processor.feature_extractor(clips, sampling_rate=SAMPLE_RATE, return_tensors="pt").input_features
        with torch.autocast("cuda", dtype=torch.float16):
            generated = model.generate(input_features=features.to("cuda", torch.float16), language="cantonese",
                                       task="transcribe", num_beams=1, max_new_tokens=200)
        hypotheses += processor.batch_decode(generated, skip_special_tokens=True)
        references += [segment["text"] for segment in batch]
    score = character_error_rate(references, hypotheses)
    print(f"[{label}] CER {score:.1%} on {len(references)} held-out clips", flush=True)
    for reference, hypothesis in list(zip(references, hypotheses))[:5]:
        print(f"    ref {reference[:40]}\n    got {hypothesis[:40]}")
    return score


# ---------- training ----------

def train(arguments):
    processor, model = load_model(arguments.adapter, for_training=True)
    noise_bank = build_noise_bank()
    train_segments, test_segments = load_segments("train"), load_segments("test")
    print(f"train {len(train_segments)} clips ({sum(s['end'] - s['start'] for s in train_segments) / 3600:.2f} h), "
          f"test {len(test_segments)} clips", flush=True)
    optimizer = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=arguments.learning_rate)
    scheduler = torch.optim.lr_scheduler.OneCycleLR(optimizer, max_lr=arguments.learning_rate, total_steps=arguments.steps, pct_start=0.05)
    tokenizer = processor.tokenizer
    tokenizer.set_prefix_tokens(language="cantonese", task="transcribe")
    model.train()
    started, running_loss = time.time(), []
    for step in range(1, arguments.steps + 1):
        for _ in range(arguments.accumulate):
            batch = random.sample(train_segments, min(arguments.batch, len(train_segments)))
            clips = [condition(far_field(read_clip(s), noise_bank) if random.random() < 0.6 else read_clip(s)) for s in batch]
            features = processor.feature_extractor(clips, sampling_rate=SAMPLE_RATE, return_tensors="pt").input_features
            labels = tokenizer([s["text"] for s in batch], return_tensors="pt", padding=True).input_ids
            labels = labels.masked_fill(labels == tokenizer.pad_token_id, -100)
            if (labels[:, 0] == model.config.decoder_start_token_id).all():
                labels = labels[:, 1:]
            with torch.autocast("cuda", dtype=torch.float16):
                loss = model(input_features=features.to("cuda", torch.float16), labels=labels.to("cuda")).loss / arguments.accumulate
            loss.backward()
            running_loss.append(loss.item() * arguments.accumulate)
        torch.nn.utils.clip_grad_norm_([p for p in model.parameters() if p.requires_grad], 1.0)
        optimizer.step(); scheduler.step(); optimizer.zero_grad(set_to_none=True)
        if step % 25 == 0:
            rate = (time.time() - started) / step
            print(f"step {step}/{arguments.steps} loss {np.mean(running_loss[-100:]):.3f} lr {scheduler.get_last_lr()[0]:.2e} "
                  f"({rate:.1f}s/step, ~{rate * (arguments.steps - step) / 60:.0f} min left)", flush=True)
        if step % arguments.save_every == 0 or step == arguments.steps:
            model.save_pretrained(arguments.output)
            if test_segments:
                evaluate(processor, model, test_segments[:200], f"step {step}")
                model.train()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--steps", type=int, default=2000)
    parser.add_argument("--batch", type=int, default=2)
    parser.add_argument("--accumulate", type=int, default=8)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--save-every", type=int, default=500)
    parser.add_argument("--output", default="/mnt/storage/models/whisper-yue-lora")
    parser.add_argument("--adapter", default=None)
    parser.add_argument("--evaluate-only", action="store_true")
    arguments = parser.parse_args()
    if arguments.evaluate_only:
        processor, model = load_model(arguments.adapter)
        evaluate(processor, model, load_segments("test")[:300], "adapter " + str(arguments.adapter) if arguments.adapter else "base large-v3")
    else:
        train(arguments)
