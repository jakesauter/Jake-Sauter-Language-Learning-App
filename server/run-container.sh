#!/bin/bash
# Run the Polylang inference server in a locked-down Apptainer container.
#   --containall --no-home --cleanenv : no host home folder, /tmp, environment or IPC
#   --writable-tmpfs                  : scratch space in RAM, thrown away on exit
#   Apptainer always sets NO_NEW_PRIVS, so sudo and setuid programs cannot work inside.
# Mounts: AI models and the Hugging Face cache read-only, the data folder read-write,
# the built website read-only, and the Google key read-only if it exists.
set -euo pipefail
cd "$(dirname "$0")"
google_key_file=/home/coderx/.config/polylang/google_translate_key
mounts=(
    --bind /home/coderx/models:/models:ro
    --bind /home/coderx/.cache/huggingface:/hf:ro
    --bind /mnt/storage/polylang-data:/data
    --bind /mnt/storage/polylang-site:/site:ro
)
[ -f "$google_key_file" ] && mounts+=(--bind "$google_key_file":/run/secrets/google_translate_key:ro)
[ "${POLYLANG_DEV:-0}" = 1 ] && mounts+=(--bind "$PWD":/app:ro)   # run the working copy without rebuilding
exec apptainer run --nv --containall --no-home --cleanenv --writable-tmpfs "${mounts[@]}" \
    --env POLYLANG_ORIGINS="${POLYLANG_ORIGINS:-https://jakesauter.github.io,https://coderx-legion-t730-28ico.tailf42501.ts.net}" \
    --env POLYLANG_PORT="${POLYLANG_PORT:-8000}" \
    --env POLYLANG_MODEL="${POLYLANG_MODEL:-mobiuslabsgmbh/faster-whisper-large-v3-turbo}" \
    container/polylang.sif
