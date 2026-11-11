# Decisions made while you were away — 2026-11-08

Each entry: the question, what I chose, why, and what the alternative would have been. Mark any you'd reverse.

## Before the loop (already in place)

1. **Where does "published" mean?**
   Chose: the private T730 address `https://coderx-legion-t730-28ico.tailf42501.ts.net/app/` (rebuilt after every substantial change). Not pushed to public GitHub Pages.
   Why: pushing makes it public, which you asked me to confirm first; the live features only work on your Tailscale network anyway.
   Alternative: push the branch so jakesauter.github.io also gets the new UI.

2. **Translation model for live mode.**
   Chose: `qwen3.5:4b` instead of `qwen2.5:7b`; Whisper `large-v3-turbo` instead of `large-v3`.
   Why: the 7B spilled 63% onto the CPU next to three speech engines (translations ~4 s, suggestions ~14 s). Now ~0.5 s per translation, ~9 s per suggestion set; 4B quality was comparable on Cantonese test lines (slightly weaker idiom: "go for tea" vs "dim sum").
   Alternative: keep the 7B and drop one speech engine (BuzzASR or Whisper) from the Cantonese route.

3. **Accounts.**
   Chose: optional username/password (scrypt), tokens on the device, guest mode by default, Tailscale login used automatically.
   Alternative: passkeys (Face ID) — nicer, but tied to one web address, so they wouldn't work from both the GitHub site and the T730.

4. **Saved data location.**
   Chose: the container's data volume on the 2 TB drive (`/mnt/storage/polylang-data`), not inside the image.
   Why: the image is read-only and replaced on every rebuild; a volume survives rebuilds and is easy to back up.
   Alternative: an Apptainer overlay image file (one big file, harder to inspect).

5. **Cantonese vs Taishanese labels.**
   Chose: label such lines "Cantonese / Taishanese" when both are possible.
   Why: no existing model can tell them apart by sound; guessing would be wrong half the time.

## During the loop (14:00–18:00)

6. **What to build first in the loop?**
   Chose: (a) a 10-minute real-time soak test to catch slowdowns/leaks before a 2-hour dinner, then (b) a **Recap** button (English summary + 5 phrases worth learning, with pronunciation strips), in the live view and on saved conversations.
   Why: reliability matters most for tonight; Recap helps both catching up mid-dinner and studying afterwards.
   Alternatives considered: speaker labels (who said what) — needs a diarization model and more GPU memory than is free; tap-a-word-to-save-to-phrasebook — deferred, see 7.

7. **Should live/recap phrases save into the existing phrasebook?**
   Chose: not tonight. The phrasebook stores the app's own sentence objects (with per-language token data); turning a transcribed line into one safely needs care, and a broken phrasebook would hurt more than a missing button.
   Alternative: a quick "save" that stores just the text, which you might prefer even if it looks plainer in the phrasebook.

8. **Why the GPU was full (your question).**
   Nothing else was running: the speech server (3 engines) uses ~4 GB and the translation model ~3 GB of the 8 GB card. More VRAM (16–24 GB) is the real fix if you upgrade.

9. **Publishing target (your instruction).** You said: always publish to jakesauter.github.io. Done from now on: every substantial update is built, copied to the repo-root `index.html`, merged to `main` and pushed; the T730 copy is refreshed too.

10. **How compact should word-by-word be?**
    Chose: cards ~30% smaller, then the whole block auto-scales to fit the screen, but never below 65% of that (≈45% of the original size).
    Why: below that the pronunciation lines (ŋɔi³³, ngoy) become unreadably small on a phone; very long sentences scroll a little instead.
    Alternative: wrap long sentences onto several lines — but the connecting lines between languages can't cross a line break when word order differs (e.g. Mandarin vs English).

11. **Memory hooks:** now a collapsible section, closed by default (your instruction).

12. **How does jakesauter.github.io find your T730?**
    Chose: the public page checks the T730's Tailscale address once on load (2.5 s timeout); if it answers (only on your Tailscale devices) the app remembers it and live mode appears.
    Trade-off: the T730's Tailscale hostname is visible in the public page's code. It's already public in certificate-transparency logs and unreachable without your Tailscale login.
    Alternative: keep the hostname out of the code and type the address once in Record → Advanced on each device.
    Note: desktop Chrome now asks "Allow access to devices on your local network?" the first time jakesauter.github.io contacts the T730 — click Allow. iPhone Safari doesn't have this prompt. Verified in Chromium with the permission granted: the home computer is found and the language chips + live option appear.

13. **Wording (your instruction).** No hardware names in the app: "Live translate", "Saved conversations", "Connecting…", "Transcribe this recording". The only technical word left is "Tailscale" in the connection-error message, because that is the one thing you would need to check.

14. **Stability test result (9.5 minutes of continuous mixed Cantonese/English, real time).**
    105 lines, 0 errors, no slowdown: a line appears ~1.65 s after the speaker stops (same in the first and last minutes), translation starts ~0.27 s later. Language detection: English 1.0, Cantonese 0.98–0.999. Server memory grew ~0.4 GB over the run (the machine has 30 GB), GPU memory stayed flat at ~7 GB.

15. **Feature freeze before dinner?**
    Chose: from ~3 PM, no new server features — only bug fixes and small, low-risk app text/layout changes — plus a final health check (~5:30 PM) that the server is up, models are loaded and the GPU is free.
    Why: every server change means a restart and a little risk; tonight the app working matters more than one more feature. I also stopped spending your usage on large changes you can't review.
    Alternative: keep adding features (tap-to-save phrases, speaker labels) until 6 PM.

16. **Accounts with email + forgot password (your request).**
    Built: optional email at sign-up (or added later on the Account page); "Forgot password?" emails a 6-digit code (15 minutes, single-use, 5 wrong tries, max 5 requests per hour per email and per device). Resetting signs out every other device. The reply is identical whether or not an account uses that email, so the form can't be used to discover accounts.
    A test caught a real bug while building this: a wrong code's "try used up" was being rolled back, which would have allowed unlimited guessing. Fixed and covered by a test.
    **Needs you:** email can't be sent until a mail account is connected. Easiest: a Gmail app password (Google Account → Security → 2-Step Verification → App passwords), saved as `~/.config/polylang/email.json`:
    `{"host": "smtp.gmail.com", "port": 587, "username": "you@gmail.com", "password": "<16-char app password>", "from": "Polylang <you@gmail.com>"}`
    then restart the server (`systemctl --user restart polylang-home`). Alternative: a transactional service (Resend/Postmark) — better deliverability, needs an API key and a domain.
    Decision: I didn't use your Gmail through my own email tools, because the server must send codes by itself at any hour, without me.

17. **Forgot password without email (your instruction: "just trust the user").**
    Built: "Forgot password?" asks for the username and a new password, resets it, signs out the account's other devices, and signs you in. Limited to 10 resets per hour per username and per device.
    Risk you accepted: anyone who can reach the server can reset any account by knowing its username. Today only devices on your Tailscale network can reach it, so that means you and people you invite.
    It's one switch (`POLYLANG_TRUSTED_RESET`, on by default). When email (Gmail app password) or recovery codes are set up, turn it off and the email-code flow (already built and tested) takes over.

18. **Recovery codes replace trusted reset (your instruction: keep it secure).**
    Built: a one-time recovery code (e.g. K7QF-2M9X-HT4P, ~60 bits) shown once at sign-up, or at the next sign-in for accounts made earlier. "Forgot password?" = username + recovery code + new password. Each code works once and is replaced after a reset; "Get a new recovery code" on the Account page. 5 wrong tries per hour per username and per device. Trusted reset is now OFF.
    Codes avoid 0/O and 1/I so they can be copied by hand; spaces, dashes and lower case are accepted when typed back.
    Email reset stays built but off until you add the Gmail app password (reminder set for 9 PM).

19. **Bug you hit at 5:28 PM: only one language on your iPhone.** My fault. The language chips were only shown after the app had reached the T730, and the app gave up after 2.5 seconds, once, at page load — too short for a phone's first Tailscale connection. I had only verified it in a desktop test browser and should have said so. Fixed: the chips now always replace the single dropdown (default Taishanese, Cantonese, Mandarin, English), the app keeps trying to reach the T730 for 12 seconds each time Recordings opens, and Advanced shows the last connection check so failures can be diagnosed from a screenshot.

20. **Speaker labels and language detection (your request at dinner).** SenseVoice now decides the language of each piece (Whisper called noisy Cantonese "English"); pieces are cut at quarter-second pauses, minimum 1.5 s. Speakers come from CAM++ voice fingerprints (CPU) with a running average per voice; threshold 0.5 (0.55 found 7 voices in 100 s of real dinner audio — likely over-splitting; 0.35–0.45 merged everyone). Adjustable with POLYLANG_SAME_SPEAKER.

21. **Cantonese/Taishanese quality at dinner.** Real dinner lines showed the problem was transcription, not translation: Whisper produced invented romanization/English ("PEN TOHWA AM LAO"), BuzzASR sometimes looped (嚟嚟嚟…). Chose: Cantonese/Taishanese now use SenseVoice (lead) + BuzzASR only; when they disagree, the translator gets every version and works out the most likely meaning. Likely root cause remains Taishanese, which no model knows; tonight’s saved audio is the start of the dataset to fix that.

22. **Improving recognition from tonight’s data (your request).** No labels exist, so I used the local 7B model as a coherence judge (1–5) on 30 random Chinese pieces out of 319 from the saved dinner audio. Current 3.90 (3 gibberish), letting SenseVoice auto-detect 3.60, cleaned audio (120 Hz low-cut + volume leveling) 4.10 with 0 gibberish. Adopted cleaned audio for every piece. Script: server/tests/experiment_cantonese_variants.py — re-run it as more audio is saved. A sample of 30 is small; the direction is consistent but not proof.

23. **Engine choice from 100 real dinner pieces.** LLM fusion 4.45, SenseVoice 4.21, Whisper large-v3 4.13, BuzzASR 3.76 (10 gibberish). Chose: Cantonese/Taishanese = SenseVoice + Whisper, fused by the 7B model into one transcript when they differ; BuzzASR dropped. Caveat: the judge rates fluency, not correctness, and is the same kind of model as the fuser, so a fluent-but-wrong fusion would still score well. Ground truth (a few corrected lines from a Cantonese speaker) would settle it.

24. **Polished dinner (409 lines) and speaker grouping.** Re-processed all 23 recordings offline with Whisper large-v3 + SenseVoice + LLM fusion + translation with context. First speaker grouping (live threshold) gave 48 speakers; average-linkage with max 8 collapsed to 1 (voices separate weakly through one phone mic: median similarity 0.44). Chose Ward clustering with 6 speakers: the groups differ clearly by language (two ~90% English, two ~85% Cantonese, two mixed), which is a good sign they are real voices. Not verified against who actually spoke.

25. **Automatic digest + live engine fixes (evening).** Measured on 100 dinner pieces: Whisper turbo (my afternoon VRAM-saving switch) scored 2.81 with 33 gibberish lines vs large-v3 4.14 with 5 — the turbo switch was a main cause of the bad live output at dinner. Live now uses large-v3. That first ran out of GPU memory under load; fixed by reserving 1.5 GB in Ollama (OLLAMA_GPU_OVERHEAD; translator ~24% on CPU, ~0.5 s per line) and reloading an engine automatically after any GPU error. Every finished recording is now digested automatically in the background (waits while anyone records live); the app shows the digested version with a toggle back to "as heard live".

26. **Trust levels on translations (loop, after dinner).** Asking the translator to say "(unclear)" only flagged 2 of 151 real dinner lines; asking for an explicit clarity score flagged 26 (17%), all genuinely garbled. Chose three tiers: clarity 4–5 shown normally, 3 shown greyed with "≈", 1–2 shown as "(unclear)" while the original characters and pronunciation strip stay visible. Translations that leak Chinese count as unclear. Cost: translations arrive whole (~1.1–1.4 s) instead of streaming. Known issue: the judge is a little strict (a clear sentence scored 3).

27. **Research-driven preprocessing (arXiv).** Recent studies show speech enhancement/denoising *raises* Whisper error rates (arXiv 2512.17562, 2603.04710), so no neural denoiser; light conditioning (low-cut + leveling) stays because it measured better on our audio. Found and fixed real aliasing: the phone downsampled 48→16 kHz by dropping samples with no filter, letting 9–17 kHz noise fold into speech at full level. Now a 63-tap Blackman windowed-sinc low-pass (flat to 6.5 kHz, -52 dB at 9 kHz, < -80 dB above 10.5 kHz). Frequency/pitch shifting is a training-time augmentation, not an inference step, so not used.

28. **GitGuardian alert (commit 2931be2).** Investigated: it flagged made-up test credentials in server/tests (e.g. password "a new password" against a throwaway test database), not a real secret. The Google key was never committed (0 matches in all history; it lives only in ~/.config/polylang/, mode 600). Tests now generate random passwords at runtime so no credential-looking literals remain. Action for you: mark the GitGuardian incident as a false positive / test credential.

29. **Google hints: tried, turned off.** With Google Translate hints the model called more lines clear (75 vs 68 of 80) but that included junk like "Hit your bell Hit your bell" and "Hee hee hee" — Google always returns fluent English, which made the model more confident about nonsense. Off by default (POLYLANG_GOOGLE_HINTS=1 to enable). Key stored for later use as a translation provider/benchmark reference.

30. **Repetition-loop filter.** Whisper hallucinates loops on laughter/noise (唔唔唔唔, 啱啱啱啱, 啵 啵 啵). Looping versions are dropped; if every engine looped, no line is shown. Calibrated so genuine repeats (多謝多謝多謝, 要小心 要小心 要小心, No no no) are kept; covered by tests.

31. **Evaluation and data split for fine-tuning (overnight).** Baseline measured two ways on held-out human-subtitled Cantonese: 8-bit greedy decoding 39.6% CER, but with the live settings (CTranslate2, beam 5, same audio conditioning) 25.1% — beam search already fixes most Mandarin drift (我哋 vs 我們). The live-settings number is the one to beat. Gold grew to 17 videos / 5.5 h via the subtitled-video crawler, so gold is now split by video (~50/50 by hours: 2.7 h train, 2.8 h test) instead of test-only; pseudo-labels (SenseVoice/Whisper agreement >= 0.85, Cantonese-only, no music, no loops) add to training. A fine-tuned model replaces live only if it beats the live-settings baseline on the same test set.

32. **Overnight dataset.** 487 Cantonese videos / 123.8 h downloaded with yt-dlp (your channels + playlists + search), license recorded per video (243 CC videos / 39.6 h usable commercially). Gold = 17 videos with human spoken-Cantonese subtitles (5.5 h). Taishanese: the 1964 DLI Toishan course audio (13 zips, ~17 h) was recovered from the Internet Archive (original host is dead); the textbook OCR is in github.com/gnezas/taishanese-g2p; audio and text are not yet aligned (that project reports naive alignment fails). Note: the DLI course dialect may differ from your family speech.

33. **Taishanese data use.** The DLI textbook OCR is too noisy (vertical text broken into single characters) for a reliable audio-text alignment tonight, so the first use of the 17 h of DLI audio is a Taishanese-vs-Cantonese detector on Whisper encoder features — it needs no transcripts and fixes the "Cantonese / Taishanese" label. Era confound handled by overlapping recording conditions (tape-like Cantonese, room-noise DLI) and an honest test on modern Taishanese YouTube (Hoisan Sauce, InspirLang, Kaiping lessons) never used for training. Licensing: DLI audio/text public domain (do not sell the course itself); the taishanese-g2p lexicon has GPL/AGPL parts — research use only unless rebuilt from Wiktionary/OpenCC.

34. **Cooling (your question at 5:20 AM).** CPU fine (package 77 °C under load, limit 86). GPU had been hitting 87–89 °C with the stock fan at ~55%. Installed a custom GPU fan curve via NVML as a root service (gpu-fan-curve.service; 40°C→30%, 55→45, 65→65, 72→80, 78→95, 82+→100%; stopping it restores automatic control). Motherboard fans are on an ITE IT8613E chip with no mainline Linux driver; a community DKMS driver exists (Secure Boot is off), but not installed: the CPU is not hot and Lenovo firmware may override it anyway.
    Update: you asked for more aggressive cooling twice; curve is now 30°C→50%, 45→70, 55→90, 60+→100%. First test with the earlier curve already held a 177 W burst at 56–68 °C (was 87–89 °C).

35. **More pseudo-labels for run 2 (your instruction).** After run 1, the GPU pseudo-labels the ~430 unlabeled videos. To cover more speakers in less time: greedy Whisper (beam 1) for labeling (the two-model agreement filter is what guards label quality) and at most 150 evenly spaced speech pieces per video. Run 2 then trains on gold-train + all pseudo-labels; it replaces live only if it beats the 20.8% live-settings baseline.

36. **Run 1 stopped at step ~225: end-of-text bug.** Whisper pads with its own end-of-text token, and the training script masked labels by token id, so the real end token was masked too. The model was learning never to stop, which explains the 139% greedy CER (runaway repeats). Fixed with the standard attention-mask masking. Run 1 is discarded rather than finished, because every extra step made it worse.

37. **Faster pseudo-labeling.** SenseVoice runs once per piece (its auto-language output gives both the Cantonese check and the text). Only Cantonese candidates go to Whisper, greedy, in batches of 8, with Whisper reference silence/loop rules and the repetition filter. Two workers run in parallel on separate halves of the ~420 remaining videos (~2.7 GB GPU each). Measured ~25 s per video per worker.

38. **Run 2 = fixed recipe, gold-train + all pseudo-labels, 1000 steps.** Then it is converted to CTranslate2 and scored with live settings on the same 600 test clips as the 20.8% baseline. Live only switches if it wins.

39. **Spoken-style filter for pseudo-labels.** A spot check showed some pseudo-labels are written Chinese read aloud (Dream of the Red Chamber readings, sutra chanting). They are correct transcripts, but they pull the model toward written style, which is wrong for dinner talk. Training now drops pseudo-labeled videos below 3% colloquial particles (same rule as the gold set; videos with under 50 characters are kept). This removed ~7% of pseudo minutes in the sample.

40. **Prompt experiment (CPU, 100 test clips).** Testing whether a short colloquial Cantonese prompt (initial_prompt) shifts Whisper to spoken characters. If it helps under live settings, it goes into live mode.

41. **Research round (your request: "do a lot of research on arXiv… papers out of China").** Findings, with links, are in docs/research-live-translation-2026-11-09.md. The short version: the recognizer was the weak link, Chinese labs already publish much better Cantonese recognizers (Alibaba Qwen3-ASR; SenseVoice-small-Yue from Northwestern Polytechnical University's WenetSpeech-Yue), and dedicated translation models (Tencent HY-MT1.5) beat general chat models of the same or larger size. Nothing has been published on Taishanese itself; the ChinaVoices 2026 dialect challenge shows the recipe for a dialect with little data (fine-tune FireRedASR2-AED with speed/noise/voice-conversion augmentation).

42. **New test sets.** (a) WSYue-eval Short: 600 public hand-transcribed Cantonese clips. (b) "table": the same clips under dinner-table conditions built from our own recording (room echo 0.3–0.7 s; real room background at the levels measured in the gaps of the 8 Nov dinner, speech 5–15 dB above it; a second voice under half the clips). (c) "dinner": the real 8 Nov recording cut the way live mode cuts it (309 pieces, no transcript; read by eye). (d) Tatoeba yue→en (400 human pairs). The private dinner audio and anything cut from it stay in /mnt/storage, never in git.

43. **Scoring change: "same words".** Strict character error counts 喇 vs 啦, 系 vs 係 and similar interchangeable Cantonese spellings as mistakes. Results are now reported both strict and with those spellings folded together; decisions use the folded number, since a reader sees the same word.

44. **Contaminated test video removed.** aRjfEC3KXJ4 is a Taiwanese food vlog (Mandarin and Hokkien speech) with Cantonese-translated subtitles, so every model "failed" on it. It is now excluded everywhere through one shared list (dataset/known_bad_videos.py).

45. **HY-MT needs its own chat format.** Ollama's automatic template for the 1.8B download is broken (it produced nothing useful); server/ollama/hy-mt.Modelfile writes the real one. The 7B download is a different model family whose own template is correct, so server/ollama/hy-mt-7b.Modelfile only adds Tencent's sampling settings.

46. **The "processor-only" translator server was using the card.** CUDA_VISIBLE_DEVICES="" does not hide the card from Ollama's Vulkan backend, so the second Ollama loaded models onto the card and about half of the speech tests ran out of memory. They are being re-run. A processor-only Ollama now needs CUDA_VISIBLE_DEVICES=-1 GGML_VK_VISIBLE_DEVICES=-1 OLLAMA_VULKAN=0, and the log line "inference compute … library=cpu" confirms it. The translation scores from that round are valid (quality does not depend on where a model runs); only their speeds are card speeds.

47. **Dolphin (Dataocean AI + Tsinghua) ruled out.** It writes Cantonese as standard written Chinese (喺 → 在, 嘅 → 的) with every language/region setting tried, so it cannot show what was actually said at the table.

48. **The live "understand this line" step hides too much.** On 163 clearly spoken YouTube lines with correct Cantonese text, it showed "(unclear)" for 57 (35%) and scored chrF++ 25.7, while a plain translation of the same text by the same model scored 36.3 and Tencent's 1.8B translation model 35.8. Asking one chat model to repair, translate and grade itself in one go loses more than it gains. Chosen: with a dedicated translation model, live mode translates the version the recognizers agree on most, and takes clarity from how much they agree (two good recognizers agreeing exactly → 98% of characters right; differing by more than a fifth → 79%). Disagreement now shows a rough (greyed) translation instead of "(unclear)". "(unclear)" remains only for empty output or a translation that leaks Chinese.

49. **FireRedASR2-AED is the main Cantonese recognizer.** Under dinner-table conditions (600 clips) it makes 11.2% errors (same-words CER) against Qwen3-ASR-1.7B 13.8%, SenseVoice-small-Yue 14.7% (raw) and the old live SenseVoice 19.2%; Whisper large-v3 makes 31.7%. On clean public clips it is 5.3%. On our YouTube clips Qwen3-ASR is slightly better (8.3% vs 8.7%), but dinner noise is where live mode is used. Qwen3-ASR also cannot share the server's container (it needs an older transformers), so it is left out. Combining three recognizers gains little (10.6–10.9% vs 11.2%), so live mode uses FireRed for the text and a second, fast recognizer only as an agreement check.

50. **The second translator round on the processor was stopped early.** The 7B HY-MT scored 36.5 on YouTube lines (1.8B: 35.8) but takes 21 s per line on the processor and does not fit on the card next to the recognizers, so it cannot be live. Qwen3.5-9B's "understand" run timed out on every line on the processor; that step is being retired anyway (48). The 1.8B on the processor takes 1.5–4 s per line, too slow for live, so it stays on the card.

51. **FireRed in float16.** FireRed chooses bfloat16 whenever torch says the card can do it, but this card (2018 generation) only emulates bfloat16. Live mode forces float16 on such cards; a test on the 600 clean and 600 dinner-table clips checks that accuracy is unchanged and measures the speed gain before relying on it. The live copy of the weights is stored in half precision (2.4 GB instead of 4.7 GB) since that is how they run.

52. **FireRed in the container.** Only FireRed's recognizer code is added to the base image, pinned to one commit of FireRedTeam/FireRedASR2S (Apache-2.0), plus the one library it needs that the image lacked (kaldi_native_fbank). The rebuild is pinned to the exact package versions of the previous image (container/constraints.txt), so nothing else changes underneath. The previous image is kept at /mnt/storage/models/base-previous.sif.

53. **English test set.** About half the pieces of the 8 Nov dinner were English, and nothing measured English recognition. Added LibriSpeech test-clean (400 clips, 40 speakers, CC BY 4.0) clean and under the same dinner-table conditions, scored by word error rate, to choose the English recognizer and see whether Whisper (about 1.5 GB on the card) is worth its memory.
    Result: float16 is 4× faster with the same accuracy (clean 5.4% vs 5.3%, dinner table 11.2% vs 11.2%; 22× real time instead of 5×), so a 3-second line takes about 0.14 s.

54. **A translation may quote a Chinese character.** The new path hid 15 of 222 YouTube lines as "(unclear)" because their English quoted a character (a pronunciation lesson: "the rhyme of 夏 is a"). Only a translation that is mostly Chinese is now hidden. The first end-to-end run is repeated under the new rule so all setups compare fairly.

55. **Writing jobs keep a chat model.** The running gist, reply suggestions, recap and version fusing need a general chat model even when lines go to the translation model. router.json's "chat" entry names it (falling back to POLYLANG_LLM), and POLYLANG_CHAT_OLLAMA can point those jobs at a second Ollama.

56. **Engines per language.** Cantonese and Taishanese: FireRed for the text, SenseVoice-small-Yue as the agreement check. Mandarin and English: FireRed, with SenseVoice as the check (SenseVoice also keeps doing language detection and the quick partial lines). Whisper is no longer preloaded (it stays available for Japanese and Korean); FireRed's English is within about one word in a hundred of Whisper's under dinner noise, and leaving Whisper out frees room on the card for the translator. FireRed writes English in lower case, so its English lines get a capital at the start and for "I".

57. **Live test of the new setup (test port, sample recording).** The three recognizers take 4.5 GB of the card; with the 1.8B translator it is 6.8 GB of 8. Lines are recognized in about 0.4–0.7 s (FireRed ~0.4 s, SenseVoice-small-Yue ~0.07 s) and translated in about 0.15 s once the translator is loaded. Two delays found and fixed: (a) the translator's first load took 13 s and held up the first lines, so the server now loads it at start; (b) the running gist asked the card's Ollama for a 7B chat model, which pushed the translator around and delayed a line by 12 s, so writing jobs now go to a second Ollama that runs on the processor only (server/container/ollama-cpu.service, port 11435).

58. **End-to-end results (222 YouTube lines with human English subtitles, chrF++, higher is better).** Old live setup (SenseVoice + Whisper, then "understand this line" with qwen2.5:7b): 32.1, with 25 lines hidden as "(unclear)", 20.6 s per line on the processor. Same recognizers with the 1.8B translation model: 32.7. FireRed alone: 34.7–34.9. FireRed checked by SenseVoice-small-Yue: 34.8. Qwen3-ASR-1.7B alone: 36.1–36.2 (better than every other setup in at least 95% of bootstrap resamples). The 7–8B chat models given FireRed's text as a plain translation job did no better than the 1.8B model (34.3–34.4). The translator gives the same scores on the card and on the processor (36.2 vs 36.1), but takes 0.4 s per line instead of 3.3 s.

59. **Punctuation explains most of Qwen3-ASR's lead, so FireRed's text now gets punctuation.** Qwen3-ASR writes punctuation; FireRed and SenseVoice-small-Yue write none. With Qwen3's punctuation removed its score drops to 35.0, level with FireRed. Adding punctuation to FireRed's text with FireRedPunc (a small BERT model from the same FireRedASR2S release, Apache-2.0) raises FireRed + SenseVoice-small-Yue from 34.8 to 35.4 (better in 91% of resamples). It never changes the words (checked on 1,077 lines), except that it removes spaces around English words, which are put back. It runs on the processor in about 20 ms per line, so it costs no card memory. Qwen3-ASR stays out of live mode: it is worse under dinner-table noise (13.8% vs 11.2% errors), it cannot share the server's container, and its remaining lead (35.4 vs 36.2) is the punctuation it hears in the voice.

60. **The translation model gets no earlier lines.** With the four earlier lines as context the new setup scored 35.4 on the 222 YouTube lines; with none, also 35.4 (with one, 34.5). On the real 8 Nov dinner recording, a garbled line now and then came back as a translation of the lines before it. No gain and a real failure, so the context is off (TRANSLATION_MODEL_CONTEXT_LINES in translation.py turns it back on). The chat-model writing jobs (gist, suggestions, recap) still see the conversation.

61. **Whisper stays off the card.** The live check after the switch showed the translator falling back to the processor (97% processor) after every conversation. Two paths still loaded Whisper (1.5 GB) and filled the card: the language check, when SenseVoice could not name the language of a noisy piece, and the after-conversation "digested" pass, which still used SenseVoice + Whisper. The language check now takes the conversation's first language in that case (FireRed writes English words as English anyway), and the digested pass uses the same recognizers as live mode (FireRed with punctuation, checked by SenseVoice). Only a conversation in Japanese or Korean loads Whisper now. Checked on the real page: lines, suggestions and the digested version all work, and the translator stays fully on the card (6.7 GB of 8 in use).
