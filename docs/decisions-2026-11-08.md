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
