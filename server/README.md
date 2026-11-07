# Polyling home transcriber

This runs speech-to-text and translation on your own computer, so there's no cloud bill. Your phone reaches it privately over Tailscale.

- **Speech to text:** [faster-whisper](https://github.com/SYSTRAN/faster-whisper) running Whisper large-v3. It handles Cantonese (`yue`), Mandarin, Spanish, French, German and English.
- **Translation (optional):** a local LLM through [Ollama](https://ollama.com). The default is `qwen2.5:7b`, which is strong at Chinese.
- **Your data:** every upload and its transcript is saved to `POLYLING_DATA`, so put that on the 2 TB drive. No model knows Taishanese yet, and these files are the start of a dataset to fine-tune one.

Sized for an RTX 2070 (8 GB): Whisper large-v3 in `int8_float16` uses about 3 GB, and a 7B model at Q4 uses about 5 GB. Jobs run one at a time.

## 1. Set up (Windows + WSL2)

Install the NVIDIA driver on Windows. Then, in an Ubuntu (WSL2) terminal:

    sudo apt update && sudo apt install -y python3-venv ffmpeg
    python3 -m venv ~/pg && source ~/pg/bin/activate
    pip install faster-whisper nvidia-cublas-cu12 "nvidia-cudnn-cu12==9.*"
    export LD_LIBRARY_PATH=$(python3 -c 'import os, nvidia.cublas.lib, nvidia.cudnn.lib; print(os.path.dirname(nvidia.cublas.lib.__file__) + ":" + os.path.dirname(nvidia.cudnn.lib.__file__))')

Optional translation:

    curl -fsSL https://ollama.com/install.sh | sh
    ollama pull qwen2.5:7b

## 2. Run

    export POLYLING_DATA=/mnt/d/polyling-data      # the 2 TB drive
    python3 polyling_home.py

The first run downloads the Whisper model, about 3 GB. Check that it's up at `http://localhost:8000/health`.

Settings, all optional:

| Variable | Default | |
|---|---|---|
| `POLYLING_MODEL` | `large-v3` | `medium` is faster with less VRAM |
| `POLYLING_COMPUTE` | `int8_float16` | `float16` is slightly more accurate |
| `POLYLING_LLM` | `qwen2.5:7b` | any Ollama model |
| `POLYLING_ORIGINS` | `https://jakesauter.github.io` | add the new address after a repo rename |
| `POLYLING_MAX_MB` | `200` | largest upload accepted |

The server listens on 127.0.0.1 only. Nothing on your home network or the internet can reach it directly.

## 3. Reach it from your phone (Tailscale, free for personal use)

1. Install Tailscale on the PC (Windows) and on your iPhone, and sign in to both with the same account.
2. In the Tailscale admin console, under DNS, turn on MagicDNS and HTTPS certificates.
3. On the PC, run: `tailscale serve --bg 8000`
4. It prints an address like `https://legion.your-tailnet.ts.net`. In Polyling, open Record › Home computer, paste that address, and tap Test.

Tailscale Serve provides a real HTTPS certificate. That matters because the app is served over HTTPS, and browsers block it from calling a plain `http://` address. Only devices signed in to your tailnet can connect.

## Cost guardrails

This setup has no metered cloud services, so the only cost is electricity. If you add a cloud fallback later, give it its own project with a hard budget cap and per-day request limits. Have the app call your server, never the cloud API directly, so a key can't leak from the phone.
