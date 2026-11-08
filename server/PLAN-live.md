# Polylang × T730: containerized live server — plan (10 rounds)

Goal: the GitHub Pages app offloads heavy work to the T730 (RTX 2070, wired gigabit) over Tailscale:
live transcription + translation while recording, live sentence translation/breakdown, best-quality
translation per language (local models or Google, chosen by measurement), all served from a locked-down
Apptainer container.

Facts gathered before planning (2026-11-08):
- Server today: stdlib `http.server` in repo `.venv`, systemd user unit, `tailscale serve` → 127.0.0.1:8000.
- Known bugs: `language` field reaches a filesystem path (traversal); `engines` field unbounded (GPU DoS).
- App live captions = phone Web Speech API (no Taishanese, weak Cantonese).
- Google: app → Cloudflare worker (`polylang-translate…workers.dev`), **en→X only**; worker's key is **invalid**.
- Ollama: translategemma:4b, aya-expanse:8b, qwen3.5:4b/9b, qwen2.5:7b available.
- VRAM: 8 GB; 3 ASR engines ≈ 4.6–4.8 GB resident.
- Apptainer 1.5.5 .deb available; Ubuntu restricts unprivileged userns (needs Apptainer's AppArmor profile).

---

## Round 1: baseline
1. Fix the two server bugs. 2. Containerize with Apptainer. 3. Rewrite server to support WebSockets.
4. Live streaming transcription + translation. 5. Translation benchmark → per-language router. 6. App UI.

## Round 2: critique (VRAM budget)
Live mode needs ASR + translation LLM resident together, and 8 GB doesn't hold 3 big ASR engines + a 7B LLM.
- Measure each resident model. Candidate layout: SenseVoice (~1 GB, partials + finals) + BuzzASR (yue finals)
  + Whisper (others) + one translation LLM ≤ ~3.5 GB.
- If over budget: Whisper large-v3 → large-v3-turbo; translation LLM → the 4B that wins the benchmark.
- Ollama: `OLLAMA_MAX_LOADED_MODELS=1`, long `keep_alive` for the router's model so it stays warm.
- Ming TTS stays offline (pre-render), never co-resident with live mode.

## Round 3: latency design
- Partials: re-run SenseVoice (~50 ms per call) on the growing utterance every ~700 ms (window capped at 20 s).
- Finals: endpoint on ~600 ms silence (Silero VAD on rolling buffer) → full ensemble + merge on that utterance.
- Translation streamed token-by-token from Ollama to the phone.
- Targets: partial < 1 s after speech; final + translation < 2.5 s after the sentence ends. Measure, don't assume.

## Round 4: capturing audio on an iPhone
- MediaRecorder chunks on iOS are fragmented MP4 (not independently decodable) → stream raw PCM instead:
  AudioWorklet → downsample to 16 kHz mono Int16 → WebSocket binary frames (~32 KB/s, trivial over Tailscale).
- Keep the existing MediaRecorder recording as the saved file (unchanged behaviour).
- AudioContext starts on the Start tap (iOS rule); request a screen wake lock; reconnect with backoff;
  buffer up to 10 s of audio while reconnecting; fall back to phone captions if the T730 is unreachable.

## Round 5: protocol and security
- `WS /live`: client → `{"type":"start", lang, engines?}` then binary PCM; server → `partial`, `final`
  (merged text, spans, hyps, agree, t0/t1), `translation` (streamed deltas + done), `error`, `stats`.
- Origin checked on the WebSocket handshake too (blocks cross-site WebSocket hijacking).
- Limits: 64 KB max frame, 2 h max session, one live session at a time (GPU), idle timeout 60 s,
  HTTP upload cap 50 MB, per-client request rate limit, bounded work queue (503 when full).
- Input validation with pydantic: language whitelist, engines whitelist (deduplicated), no input-derived paths.
- Saved data: server-chosen filenames only, realpath check inside DATA_DIR.

## Round 6: container specifics (Apptainer)
- `polylang.def`: `docker://nvidia/cuda:12.8.1-cudnn-runtime-ubuntu24.04`; Python venv at /opt/venv with
  pinned versions (torch cu128, faster-whisper, ctranslate2, av<16, funasr, opencc, fastapi, uvicorn, pydantic).
- Code baked into /app at build (bind-mounted read-only only during development).
- Run: `apptainer run --nv --containall --cleanenv --no-home --writable-tmpfs`
  binds: `~/models:/models:ro`, `~/.cache/huggingface:/hf:ro` (HF_HUB_OFFLINE=1), `/mnt/storage/polylang-data:/data`,
  secrets file read-only. No docker socket, no home, NO_NEW_PRIVS (no sudo).
- Ollama stays a host service reached at 127.0.0.1:11434 (shared network namespace).
- systemd user unit runs the .sif; the old venv unit kept (disabled) for rollback.

## Round 7: translation quality, decided by data
- Test set: Polylang's own phrases (yue / cmn / tsn / es / fr / de with English meanings) — real app content.
- Directions: yue→en, zh→en, en→yue, en→zh, es/fr/de→en, en→es/fr/de.
- Candidates: translategemma:4b, aya-expanse:8b, qwen3.5:4b, qwen3.5:9b, qwen2.5:7b, Google (when a key exists).
- Metrics: chrF++ against the app's references + COMET-22 if it fits, plus latency per sentence.
- Router: per direction, best quality within the live latency budget; offline/batch can use a slower winner.

## Round 8: Google
- The worker key is invalid, and the worker only does en→X. Rather than redeploying the worker for live use,
  the T730 calls Google directly with its own restricted key (file mounted read-only into the container,
  never sent to the phone). Router works without it; Google joins the benchmark as soon as a key is provided.
- Worker fix (new key via `wrangler secret put`) is a separate user step for when the T730 is off.

## Round 9: app UX (page.html is the real source; record.js is stale)
- Record → "Live on my home computer" (default when a home address is set; phone captions otherwise).
- Live view: grey partial line, then final lines with tap-to-switch alternatives, word gloss, streamed English.
- Lines saved into the recording (`src:"live"`) so the transcript persists with the audio.
- "Speak a sentence" quick tool: hold to talk → transcript + translation + word-by-word breakdown.
- New strings in all 7 UI packs; works offline/static exactly as before when no home computer is set.

## Round 10: verification and rollout
- Unit tests: merge, validation, path safety. Container smoke test: GPU visible, models load, no $HOME access,
  sudo blocked, docker socket absent.
- Security tests: traversal, oversized frames, bad-origin HTTP and WebSocket, engine-list abuse, flood (stays up, 429/503).
- End to end: Playwright + fake mic → live WebSocket through the Tailscale URL → partials, finals, translation rendered.
- Measure partial/final/translation latency; gpuwatch dashboard during a live session.
- Commit on a branch; **no push** without the user's go-ahead. Update server README and memory.

---

## Execution order
A. Patch the current server's two bugs (it is live now).
B. Install Apptainer; verify userns/AppArmor; GPU container smoke test.
C. New FastAPI server (HTTP compat + `/live` WebSocket + limits), developed against the container.
D. Build final image, switch systemd unit, run security tests.
E. Translation benchmark → router.
F. App UI (live mode + quick sentence tool).
G. End-to-end + load + latency tests; docs; commit locally.

## Round 11 (user additions): Rust gateway + readable code everywhere
- `gateway/` (Rust, axum): the only listener on 127.0.0.1:8000 (behind `tailscale serve`). Owns origin checks,
  CORS, per-user rate limits, body caps while streaming, input validation, WebSocket proxy with frame limits,
  one live session at a time. Forwards to the Python inference server over a Unix socket.
- Python inference server listens only on `/run/polylang/inference.sock` (bound into both containers),
  so nothing on the network, including the tailnet, can reach it except through the gateway.
- Both run in Apptainer containers with the same lockdown flags; the gateway container needs no GPU and
  only the socket directory.
- Style for the whole repo: snake_case, descriptive names, short comments only where intent isn't obvious.
  New code follows it immediately; existing code gets a refactor phase:
  server Python → build scripts (source/*.py) → page.html JavaScript (largest; done with browser tests
  before and after so behaviour is unchanged).

## Execution order (revised)
A. ✅ Patch live server bugs.  B. ✅ Apptainer installed + isolation verified.
C. Inference server (FastAPI over Unix socket) in readable style; base image (deps) + app image (code).
D. Rust gateway + its container; systemd units for both; security tests through the gateway.
E. Translation benchmark → router.  F. App live UI.  G. End-to-end, load, latency tests.
H. Readability refactor of existing code (Python build scripts, then page.html JS) with before/after tests.
I. Docs, memory, local commit (no push without approval).
