#!/bin/bash
set -e

# ── Start ComfyUI ─────────────────────────────────────────────
echo "Starting ComfyUI..."
cd /ComfyUI
python main.py \
    --listen 127.0.0.1 \
    --port 8188 \
    --disable-auto-launch \
    --gpu-only \
    &

echo "Starting RunPod handler..."
cd /
python -u handler.py