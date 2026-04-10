#!/bin/bash
set -e

VOL="/runpod-volume"
MODELS_DIR="$VOL/models"
mkdir -p "$MODELS_DIR"

# ── Qwen Rapid AIO model ───────────────────────────────────────
QWEN_DEST="/ComfyUI/models/checkpoints/Qwen/Qwen-Rapid-AIO-v1.safetensors"
QWEN_CACHE="$MODELS_DIR/Qwen-Rapid-AIO-v1.safetensors"

if [ ! -f "$QWEN_CACHE" ]; then
    echo "Downloading Qwen Rapid AIO model (first run only)..."
    wget -q --show-progress \
        "https://huggingface.co/Phr00t/Qwen-Image-Edit-Rapid-AIO/resolve/main/Qwen-Rapid-AIO-v1.safetensors" \
        -O "$QWEN_CACHE"
    echo "Qwen model downloaded."
else
    echo "Qwen model found in cache."
fi
ln -sf "$QWEN_CACHE" "$QWEN_DEST"

echo "Starting ComfyUI..."
cd /ComfyUI
python main.py \
    --listen 127.0.0.1 \
    --port 8188 \
    --disable-auto-launch \
    --gpu-only \
    --lowvram \
    &

echo "Starting RunPod handler..."
cd /
python -u handler.py
