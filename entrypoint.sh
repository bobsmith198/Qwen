#!/bin/bash
set -e

echo "Starting ComfyUI on port 8188..."
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
