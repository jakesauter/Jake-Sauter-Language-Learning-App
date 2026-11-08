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
