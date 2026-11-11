# Live dinner translation: what the field already knows, and what we measured

Question: is live translation bad because of the audio handling, the speech recognition, or a translator that is too
small for an 8 GB card? This note collects the published work (mostly from Chinese labs, since the speech is
Cantonese, Taishanese and Mandarin) and our own measurements on the same questions.

## Short answer

1. **Speech recognition was the weakest link, and the fix already exists.** Whisper large-v3 makes about twice
   the errors of the Cantonese models from Chinese labs (Xiaohongshu's FireRedASR2, Alibaba's Qwen3-ASR,
   Northwestern Polytechnical University's SenseVoice-small-Yue), and under dinner noise almost three times as
   many as FireRedASR2, which is now the live recognizer.
2. **The translator is not too small.** A dedicated 1.8B translation model (Tencent HY-MT1.5) matches or beats the
   7–9B general chat models on Cantonese, and our 7B chat model was not the bottleneck either.
3. **The "understand this line" step was hurting.** On clearly spoken, correctly transcribed YouTube lines, our
   live step hid the translation as "(unclear)" for 35% of them. Asking one chat model to repair the text,
   translate and grade its own confidence in one go loses more than it gains.
4. **Heavy audio clean-up does not help.** This matches the published finding that speech enhancement makes
   recognizers worse. Even our light clean-up (low-cut filter plus volume levelling) is slightly worse than raw
   audio for the newer models under dinner-table noise.
5. **Combining recognizers helps a little, and their agreement is a good trust signal.** When two good models
   agree exactly, the line is almost always right (2% character error). When they disagree a lot, it is often
   wrong (21%). That is a better "how sure are we" signal than asking the translator.
6. **Punctuation matters to the translator.** Recognizers that write no punctuation hand the translator one long
   run-on line. Putting punctuation back (FireRedPunc, about 20 ms per line) is worth about as much as the switch
   between the two best recognizers. End to end, the new live setup scores 35.4 against 32.1 for the old one, hides
   1 line instead of 25, and answers in well under a second instead of many seconds.

## Speech recognition for Cantonese and Chinese dialects

| Work | Lab | What matters for us |
|---|---|---|
| [WenetSpeech-Yue](https://arxiv.org/abs/2509.03959) | NPU ASLP (Xi'an) + partners | 21,800 h Cantonese corpus; released SenseVoice-small-Yue, Whisper-medium-Yue, U2++ Conformer; WSYue-eval test set (which we use) |
| [Qwen3-ASR](https://arxiv.org/abs/2601.21337) | Alibaba Qwen | 0.6B / 1.7B, 52 languages and 22 dialects, built-in language ID, context prompts; open weights |
| [FireRedASR2S](https://arxiv.org/abs/2603.10420) | Xiaohongshu (FireRed) | AED and LLM variants, strong Mandarin and dialects |
| [Dolphin-CN-Dialect](https://arxiv.org/abs/2605.08961) | Dataocean AI + Tsinghua | 0.1B / 0.4B, streaming, hotwords. Writes Cantonese as standard written Chinese, so it is not useful for dinner talk (we tested it) |
| [ChinaVoices Challenge 2026](https://arxiv.org/abs/2609.03471) | NPU ASLP et al. | 16 dialects with about 3 h each. All top 3 teams fine-tuned **FireRedASR2-AED** (11.1–11.8% CER vs the 18.1% Qwen3-ASR LoRA baseline) using speed perturbation, noise, short-utterance concatenation, auxiliary CTC, staged unfreezing, voice-conversion augmentation. This is the recipe to follow for Taishanese, which has little data |
| [Fun-ASR](https://arxiv.org/abs/2509.12508) | Alibaba Tongyi | LLM-based ASR, industrial; context biasing |
| [CantoASR](https://arxiv.org/abs/2511.04139) | — | Cantonese ASR with LLM error correction |
| [WenetSpeech-Wu](https://arxiv.org/abs/2601.11027), [TaigiSpeech](https://arxiv.org/abs/2603.21478), [T-SANDHI](https://arxiv.org/abs/2609.18194) | various | Nearest neighbours to Taishanese work (Wu, Taiwanese Hokkien). Nothing published on Taishanese itself |

## Audio handling

* Speech enhancement and denoising before recognition *raise* error rates for modern recognizers:
  [2201.06685](https://arxiv.org/abs/2201.06685), [2512.17562](https://arxiv.org/abs/2512.17562),
  [2603.04710](https://arxiv.org/abs/2603.04710). The models were trained on noisy audio and denoisers leave
  artefacts they have never seen.
* Our measurement (dinner-table test, below) agrees: raw audio beats our light clean-up for SenseVoice-small-Yue.

## Translation

| Work | Lab | What matters for us |
|---|---|---|
| [HY-MT1.5](https://arxiv.org/abs/2512.24092) | Tencent Hunyuan | Dedicated 1.8B and 7B translation models, 33 languages incl. Cantonese; the 1.8B runs on a processor at under 1 s per line |
| [TranslateGemma](https://arxiv.org/abs/2601.09012) | Google | 4B/12B translation-tuned Gemma |
| ["Hearing to Translate"](https://arxiv.org/abs/2512.16378) | — | Cascades (recognizer → text translator) still beat end-to-end speech translation models in most conditions |
| [Yue-Benchmark](https://github.com/jiangjyjy/Yue-Benchmark) (NAACL 2025), [HKCanto-Eval](https://arxiv.org/abs/2503.12440), [CantoNLU](https://arxiv.org/abs/2510.20670), [CantonMT](https://arxiv.org/abs/2405.08172) | HK / mainland universities | Cantonese text benchmarks; colloquial Cantonese → English is still under-studied |
| [MCE](https://arxiv.org/abs/2310.17953) | — | Cantonese–English code-switching, which our dinners are full of |

## Combining recognizers and correcting with a language model

* [HyPoradise](https://arxiv.org/abs/2309.15701), [GenTranslate](https://arxiv.org/abs/2402.06894),
  [PY-GEC](https://arxiv.org/abs/2409.13262), [PERL](https://arxiv.org/abs/2412.03230), DualHyp (ACL 2026 Findings):
  an LLM given several hypotheses can fix errors, but gains are small unless it is trained for the task, and an
  untrained LLM tends to rewrite correct text. This is what we saw with "understand this line".
* Simple voting (ROVER-style) is cheap and safe; the agreement level doubles as a confidence score.

## Streaming (live) translation

* [CUNI IWSLT 2026](https://arxiv.org/abs/2606.03948) and [AlignAtt4LLM](https://arxiv.org/abs/2606.03967):
  AlignAtt policy for deciding when a partial result is stable enough to show.
* [X-Translator](https://arxiv.org/abs/2607.17544) (github.com/zhaoyx239/X-Translator): cascaded streaming
  recognizer → translator with "incremental segment commitment", which is our live design.
* [Samsung streaming SpeechLLM](https://arxiv.org/abs/2605.14766), [Hikari](https://arxiv.org/abs/2603.11578):
  end-to-end streaming, but no Chinese or no released weights.

## Our measurements

Speech recognition, character error rate (lower is better). "Same words" folds spellings Cantonese writers use
interchangeably (啦/喇, 係/系 …); "strict" does not.

* **wsyue**: 600 clean public clips, hand-transcribed (WSYue-eval, 49 min).
* **table**: the same 600 clips under dinner-table conditions: room echo (0.3–0.7 s), real background noise taken
  from the gaps in our own dinner recording at the levels measured there (speech 5–15 dB above the room), and a
  second voice under half of them.
* **gold**: 480 clips from Cantonese YouTube videos with human subtitles (156 min).

| Recognizer (lab) | wsyue | table | gold | English, table (WER) |
|---|---|---|---|---|
| **FireRedASR2-AED** (Xiaohongshu), half precision | **5.4%** | **11.2%** | 8.7% | 6.7% |
| Qwen3-ASR-1.7B (Alibaba) | 5.7% | 13.8% | **8.3%** | 3.6% |
| SenseVoice-small-Yue (NPU ASLP) | 5.4% | 14.7% (raw audio) | 9.5% | 26.3% |
| SenseVoice small (Alibaba; the old live default) | 6.5% | 19.2% (raw audio) | 9.2% | 9.6% |
| Qwen3-ASR-0.6B (Alibaba) | 6.9% | 18.7% | 9.3% | — |
| Whisper large-v3 (OpenAI; the old live partner) | 13.5% | 31.7% | 13.0% | 5.6% |

Character error rates are "same words"; English is word error rate on 400 LibriSpeech clips under the same
dinner-table conditions (clean: Whisper 3.2%). FireRed in half precision is as accurate as in full precision and
4x faster on this card (22x real time).

**End to end** (Cantonese audio → recognizer → translator → English), chrF++ against human English subtitles on
222 lines from 7 YouTube videos. This is the number that matters at the table.

| Setup | chrF++ | Hidden as "(unclear)" | Seconds per line |
|---|---|---|---|
| Old live: SenseVoice + Whisper, then "understand this line" (qwen2.5:7b) | 32.1 | 25 | 20.6 (processor) |
| SenseVoice + Whisper → HY-MT1.5 1.8B | 32.7 | 1 | 3.0 (processor) |
| FireRed → HY-MT1.5 1.8B | 34.7 | 4 | 0.4 (card) |
| FireRed → qwen2.5:7b / aya-expanse:8b, plain translation | 34.3 / 34.4 | 3 | 3.9 / 4.8 |
| FireRed + SenseVoice-small-Yue check → HY-MT1.5 1.8B | 34.8 | 3 | 0.3 (card) |
| **FireRed + punctuation + SenseVoice-small-Yue check → HY-MT1.5 1.8B (new live setup)** | **35.4** | 1 | 0.3 (card) |
| Qwen3-ASR-1.7B → HY-MT1.5 1.8B | 36.2 | 1 | 0.4 (card) |
| Qwen3-ASR-1.7B with its punctuation removed → HY-MT1.5 1.8B | 35.0 | 1 | 0.4 (card) |

Most of Qwen3-ASR's lead is its punctuation (it hears sentence ends in the voice). FireRed writes none, so live
mode now adds it with FireRedPunc, a small model from the same FireRed release that runs on the processor in
about 20 ms. Qwen3-ASR itself is worse under dinner noise and cannot share the server's software, so it stays out.

Translation, chrF++ (higher is better).

* **tatoeba**: 400 everyday sentences with English written by people.
* **youtube**: 163 spoken lines with human English subtitles.

| Translator | Size | tatoeba | youtube | Seconds per line (processor) |
|---|---|---|---|---|
| HY-MT1.5 (Tencent) | 1.8B | 49.7 | 35.8 | 0.8 |
| HY-MT1.5 (Tencent) | 7B | — | 36.5 | 21 |
| aya-expanse (Cohere), plain prompt | 8B | **53.1** | 36.4 | 1.0–12.8 |
| qwen2.5 (Alibaba), plain prompt | 7B | 48.3 | 36.3 | 0.5–1.1 |
| TranslateGemma (Google) | 4B | 49.5 | 34.6 | 0.4–7.7 |
| qwen3.5 (Alibaba), "understand this line" | 9B | 51.2 | — | 3.3 |
| qwen2.5 (Alibaba), "understand this line" (old live) | 7B | 45.2 | 25.7 | 1.7–3.0 |

The 7–9B models are at most a point or two better than the 1.8B translation model on our lines, and on the full
end-to-end test they are no better (34.3–34.4 vs 34.7). The 1.8B model fits on the card next to the recognizers
(6.8 GB of 8 in all) and answers in about 0.15 s there, so it is the live translator.
