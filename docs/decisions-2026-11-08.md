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
