"""Score any candidate speech model on the same Cantonese clips, and keep what each one heard.

Every model's text for every clip is saved, so models can be compared, combined and fed to the translator later
without running the audio again.

    ~/venvs/asr-next/bin/python dataset/evaluate_speech_models.py qwen3:/mnt/storage/models/hf/Qwen3-ASR-1.7B
    .venv/bin/python dataset/evaluate_speech_models.py sensevoice:FunAudioLLM/SenseVoiceSmall gold 600
    .venv/bin/python dataset/evaluate_speech_models.py whisper:large-v3 pairs

    .venv/bin/python dataset/evaluate_speech_models.py table wsyue        (every model scored so far, side by side)

    <engine>:<model>   qwen3 | firered2 | dolphin | sensevoice | whisper
    test set           gold  = our human-subtitled YouTube test clips (default)
                       pairs = our clips that also have English subtitles
                       wsyue = WenetSpeech-Yue's public test set: everyday Cantonese, transcribed by hand
                               (build it once with dataset/prepare_public_tests.py)
                       table = the same clips under dinner-table conditions: room echo, our real dinner's
                               background noise and a second voice (build with dataset/make_dinner_table_test.py)
                       <name> = one of our own recordings cut by dataset/cut_recording.py (nothing to score
                               against: the lines are saved to be read side by side)
    most_clips         spread evenly across the test set (default 600, everything for pairs)

    Two scores are printed. "strict" counts every different character. "same words" first folds spellings that
    Cantonese writers use interchangeably (喇/啦, 噉/咁, 畀/俾, 返/翻 ...), so it counts wrong words, not spelling taste.

    POLYLANG_EVAL_CONTEXT   background text given to models that accept it (Qwen3 context, Whisper prompt)
    POLYLANG_EVAL_LANGUAGE  the language the models are told to expect (default yue); "auto" lets each model decide,
                            the way a mixed-language dinner needs
    POLYLANG_EVAL_RAW=1     skip the low-cut and volume levelling that live mode applies
"""

import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "server"))
import jiwer  # noqa: E402
import soundfile  # noqa: E402
from opencc import OpenCC  # noqa: E402

import speech_engines  # noqa: E402
from known_bad_videos import NOT_CANTONESE_SPEECH  # noqa: E402

DATASET_FOLDER = "/mnt/storage/datasets/youtube_cc_cantonese"
OUTPUT_FOLDER = os.path.join(DATASET_FOLDER, "speech_eval")
SAMPLE_RATE = 16000
BATCH = 8
CONTEXT = os.environ.get("POLYLANG_EVAL_CONTEXT", "")
LANGUAGE = os.environ.get("POLYLANG_EVAL_LANGUAGE", "yue")
FIRERED_FP16 = bool(os.environ.get("POLYLANG_EVAL_FIRERED_FP16"))
OWN_RECORDINGS_FOLDER = "/mnt/storage/datasets/own_recordings"
# What each model calls a language, as our codes.
LANGUAGE_CODES = {"cantonese": "yue", "yue": "yue", "ct": "yue", "chinese": "zh", "mandarin": "zh", "zh": "zh", "english": "en", "en": "en"}
QWEN_LANGUAGE_NAMES = {"yue": "Cantonese", "zh": "Chinese", "en": "English"}
to_hong_kong = OpenCC("s2hk")


PUBLIC_TESTS = {"wsyue": "/mnt/storage/datasets/public_eval/wsyue_short_test.jsonl",
                "table": "/mnt/storage/datasets/public_eval/wsyue_table_test.jsonl",
                # English (LibriSpeech test-clean, prepare_english_test.py), clean and under dinner-table conditions.
                # Run these with POLYLANG_EVAL_LANGUAGE=en; they are scored by word error rate.
                "english": "/mnt/storage/datasets/public_eval/english_short_test.jsonl",
                "english_table": "/mnt/storage/datasets/public_eval/english_table_test.jsonl"}

# Spellings Cantonese writers use interchangeably. Folding them keeps a model from being marked wrong for writing
# 啦 where the subtitler wrote 喇.
SAME_WORD_SPELLINGS = str.maketrans({
    "喇": "啦", "嘞": "啦", "嚹": "啦", "噉": "咁", "畀": "俾", "翻": "返", "嗮": "晒", "哂": "晒", "曬": "晒", "噶": "㗎",
    "嘎": "㗎", "咧": "呢", "啊": "呀", "吖": "呀", "枱": "台", "檯": "台", "麪": "麵", "裏": "裡", "㖞": "喎", "噃": "喎",
    "咯": "囉", "囖": "囉", "衹": "只", "祇": "只", "系": "係", "繫": "係", "着": "著", "峯": "峰", "羣": "群", "牀": "床",
    "爲": "為", "啓": "啟", "綫": "線",
})


def comparable(text):
    return "".join(character for character in to_hong_kong.convert(text) if character.isalnum()).lower()


def same_words(text):
    return comparable(text.translate(SAME_WORD_SPELLINGS)).translate(SAME_WORD_SPELLINGS)


def test_clips(which, most_clips):
    own_recording = os.path.join(OWN_RECORDINGS_FOLDER, f"{which}_test.jsonl")
    if which in PUBLIC_TESTS:
        clips = [json.loads(line) for line in open(PUBLIC_TESTS[which]) if line.strip()]
    elif os.path.exists(own_recording):
        clips = [json.loads(line) for line in open(own_recording) if line.strip()]
    elif which == "pairs":
        clips = [json.loads(line) for line in open(os.path.join(DATASET_FOLDER, "translation_pairs.jsonl")) if line.strip()]
    else:
        clips = [json.loads(line) for line in open(os.path.join(DATASET_FOLDER, "gold_segments.jsonl"))]
        clips = [clip for clip in clips if clip["split"] == "test"]
    clips = [clip for clip in clips if 0.5 < clip["end"] - clip["start"] <= 28 and clip["video"] not in NOT_CANTONESE_SPEECH]
    if most_clips:
        clips = clips[:: max(1, len(clips) // most_clips)][:most_clips]
    return clips


def clip_audio(clip):
    audio, _ = soundfile.read(clip["audio"], start=int(clip["start"] * SAMPLE_RATE), stop=int(clip["end"] * SAMPLE_RATE), dtype="float32")
    return audio if os.environ.get("POLYLANG_EVAL_RAW") else speech_engines.clean_audio(audio)


# ---------- engines: each returns a function (list of audio arrays) -> list of (text, language it heard) ----------

def load_qwen3(model_path):
    import torch
    from qwen_asr import Qwen3ASRModel
    model = Qwen3ASRModel.from_pretrained(model_path, dtype=torch.float16, device_map="cuda:0",
                                          max_inference_batch_size=BATCH, max_new_tokens=256)

    def transcribe(audios):
        results = model.transcribe(audio=[(audio, SAMPLE_RATE) for audio in audios], context=[CONTEXT] * len(audios),
                                   language=[QWEN_LANGUAGE_NAMES.get(LANGUAGE)] * len(audios))
        return [(result.text, result.language or "") for result in results]
    return transcribe


def load_firered2(model_path):
    sys.path.insert(0, os.environ.get("FIRERED_CODE", "/mnt/storage/models/hf/FireRedASR2S"))
    import tempfile
    import types
    try:
        import torchaudio  # noqa: F401
    except ImportError:  # only used for word timings, which are not asked for here
        import transformers  # noqa: F401  (let it see there is no torchaudio before the stand-in exists)
        sys.modules["torchaudio"] = types.ModuleType("torchaudio")
    from fireredasr2s.fireredasr2 import FireRedAsr2, FireRedAsr2Config
    if FIRERED_FP16:
        # FireRed picks bfloat16 whenever torch says it can, but older cards only emulate it (slowly).
        import torch
        torch.cuda.is_bf16_supported = lambda *args, **kwargs: False
    config = FireRedAsr2Config(use_gpu=True, use_half=True, beam_size=3, nbest=1, decode_max_len=0,
                               softmax_smoothing=1.25, aed_length_penalty=0.6, eos_penalty=1.0, return_timestamp=False)
    model = FireRedAsr2.from_pretrained("aed", model_path, config)
    folder = tempfile.mkdtemp()

    def transcribe(audios):
        names, paths = [], []
        for index, audio in enumerate(audios):
            path = os.path.join(folder, f"clip{index}.wav")
            soundfile.write(path, audio, SAMPLE_RATE, subtype="PCM_16")
            names.append(f"clip{index}")
            paths.append(path)
        by_name = {result["uttid"]: result["text"] for result in model.transcribe(names, paths)}
        return [(by_name.get(name, ""), "") for name in names]
    return transcribe


def load_dolphin(model_folder):
    """Dataocean AI and Tsinghua's small dialect model. The folder holds one <model name>.pt file."""
    sys.path.insert(0, os.environ.get("DOLPHIN_CODE", "/mnt/storage/models/hf/Dolphin-code"))
    import dolphin
    model_name = next(name[:-len(".pt")] for name in os.listdir(model_folder) if name.endswith(".pt"))
    import torch
    model = dolphin.load_model(model_name, model_folder, device="cuda" if torch.cuda.is_available() else "cpu")
    # This model files Cantonese under Chinese with a Guangdong region (and writes it as standard written Chinese).
    language_symbol, region_symbol = {"yue": ("zh", "GUANGDONG"), "zh": ("zh", "CN")}.get(LANGUAGE, (None, None))

    def transcribe(audios):
        heard = []
        for audio in audios:
            result = dolphin.transcribe(model, torch.from_numpy(audio).unsqueeze(0), lang_sym=language_symbol,
                                        region_sym=region_symbol)
            heard.append((result.text_nospecial, f"{result.language}-{result.region}"))
        return heard
    return transcribe


def load_sensevoice(model_path):
    from funasr import AutoModel
    is_local = os.path.isdir(model_path)
    model = AutoModel(model=model_path, device="cuda:0", disable_update=True, **({} if is_local else {"hub": "hf"}))

    def transcribe(audios):
        texts = []
        for audio in audios:
            raw = model.generate(input=audio, cache={}, language=LANGUAGE, use_itn=True, batch_size_s=60)
            raw_text = raw[0]["text"] if raw else ""
            heard_as = next((tag for tag in speech_engines.SENSEVOICE_TAG.findall(raw_text) if tag in LANGUAGE_CODES), "")
            texts.append((speech_engines.EMOJI.sub("", speech_engines.SENSEVOICE_TAG.sub("", raw_text)).strip(), heard_as))
        return texts
    return transcribe


def load_whisper(model_path):
    from faster_whisper import WhisperModel
    model = WhisperModel(model_path, device="cuda", compute_type="int8_float16")

    def transcribe(audios):
        heard = [speech_engines.run_whisper(model, audio, "" if LANGUAGE == "auto" else LANGUAGE, with_words=False,
                                            prompt=CONTEXT or None) for audio in audios]
        return [(text, language or "") for text, _, language in heard]
    return transcribe


LOADERS = {"qwen3": load_qwen3, "firered2": load_firered2, "dolphin": load_dolphin, "sensevoice": load_sensevoice,
           "whisper": load_whisper}


def main(engine_and_model, which="gold", most_clips=None):
    engine, _, model_path = engine_and_model.partition(":")
    clips = test_clips(which, most_clips or (None if which == "pairs" else 600))
    transcribe = LOADERS[engine](model_path)
    rows, started = [], time.time()
    for batch_start in range(0, len(clips), BATCH):
        batch = clips[batch_start: batch_start + BATCH]
        heard = transcribe([clip_audio(clip) for clip in batch])
        for clip, (text, heard_as) in zip(batch, heard):
            language = LANGUAGE_CODES.get(heard_as.lower(), "") if LANGUAGE == "auto" else LANGUAGE
            rows.append({"video": clip["video"], "start": clip["start"], "end": clip["end"], "reference": clip["text"],
                         "heard": speech_engines.to_common_script(text, language), "language": language})
    seconds = time.time() - started
    name = f"{engine}_{os.path.basename(model_path.rstrip('/'))}__{which}" + ("__context" if CONTEXT else "") + \
           ("__raw" if os.environ.get("POLYLANG_EVAL_RAW") else "") + ("__fp16" if FIRERED_FP16 and engine == "firered2" else "") + \
           ("" if LANGUAGE == "yue" else "__" + LANGUAGE)
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    with open(os.path.join(OUTPUT_FOLDER, name + ".jsonl"), "w") as output:
        for row in rows:
            output.write(json.dumps(row, ensure_ascii=False) + "\n")
    strict, lenient, scored = scores(rows)
    audio_seconds = sum(clip["end"] - clip["start"] for clip in clips)
    speed = f"({seconds:.0f}s for {audio_seconds / 60:.0f} min of audio, {audio_seconds / seconds:.0f}x real time)"
    if not scored:  # one of our own recordings: nothing to score against
        heard_languages = {code: sum(row["language"] == code for row in rows) for code in sorted({row["language"] for row in rows})}
        print(f"{name}: no CER (no transcript), {len(rows)} pieces heard as {heard_languages}  {speed}", flush=True)
        for row in rows[:: max(1, len(rows) // 8)][:8]:
            print(f"   got [{row['language']}] {row['heard'][:60]}", flush=True)
        return
    measure = "WER" if scored[0]["video"].startswith("librispeech-") else "CER"
    print(f"{name}: {measure} {strict:.1%} strict, {lenient:.1%} same words, on {len(scored)} clips  {speed}", flush=True)
    for row in scored[:: max(1, len(scored) // 5)][:5]:
        print(f"   ref {comparable(row['reference'])[:40]}\n   got {comparable(row['heard'])[:40]}", flush=True)


def english_words(text):
    return " ".join(re.sub(r"[^a-z0-9']+", " ", text.lower()).split())


def scores(rows):
    """(strict error, error after folding interchangeable spellings, the rows that were scored).
    English is scored by words (both numbers are then the word error rate)."""
    scored = [row for row in rows if comparable(row["reference"]) and row["video"] not in NOT_CANTONESE_SPEECH]
    if not scored:
        return 0.0, 0.0, scored
    if all(row["video"].startswith("librispeech-") for row in scored):
        word_error = jiwer.wer([english_words(row["reference"]) for row in scored], [english_words(row["heard"]) or "-" for row in scored])
        return word_error, word_error, scored
    strict = jiwer.cer([comparable(row["reference"]) for row in scored], [comparable(row["heard"]) or " " for row in scored])
    lenient = jiwer.cer([same_words(row["reference"]) for row in scored], [same_words(row["heard"]) or " " for row in scored])
    return strict, lenient, scored


def table(which):
    """Every model already run on a test set, best first, with the score on each video for our own clips."""
    results = []
    for file_name in sorted(os.listdir(OUTPUT_FOLDER)):
        if not file_name.endswith(".jsonl") or not (f"__{which}__" in file_name or file_name.endswith(f"__{which}.jsonl")):
            continue
        rows = [json.loads(line) for line in open(os.path.join(OUTPUT_FOLDER, file_name)) if line.strip()]
        strict, lenient, scored = scores(rows)
        by_video = {}
        for row in scored:
            by_video.setdefault(row["video"], []).append(row)
        per_video = {video: scores(video_rows)[1] for video, video_rows in by_video.items()} if len(by_video) <= 12 else {}
        results.append((lenient, strict, len(scored), file_name[:-len(".jsonl")], per_video))
    print(f"{'model':58s} {'same words':>10s} {'strict':>7s} {'clips':>6s}")
    for lenient, strict, clip_count, name, per_video in sorted(results):
        print(f"{name:58s} {lenient:>10.1%} {strict:>7.1%} {clip_count:>6d}  "
              + " ".join(f"{video[:5]} {score:.0%}" for video, score in sorted(per_video.items())))


if __name__ == "__main__":
    if sys.argv[1] == "table":
        table(sys.argv[2] if len(sys.argv) > 2 else "gold")
        sys.exit()
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "gold", int(sys.argv[3]) if len(sys.argv) > 3 else None)
