FROM runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04

WORKDIR /

RUN apt-get update && apt-get install -y \
    git wget ffmpeg libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# ComfyUI
RUN git clone https://github.com/comfyanonymous/ComfyUI.git /ComfyUI
WORKDIR /ComfyUI
RUN pip install -r requirements.txt

# Custom nodes — Qwen image edit node
WORKDIR /ComfyUI/custom_nodes
RUN git clone https://github.com/kijai/ComfyUI-QwenImageEditNode.git && \
    pip install -r ComfyUI-QwenImageEditNode/requirements.txt || true

# Fallback — try alternate repo name if above fails
RUN if [ ! -d "ComfyUI-QwenImageEditNode" ]; then \
    git clone https://github.com/kijai/ComfyUI-WanVideoWrapper.git && \
    pip install -r ComfyUI-WanVideoWrapper/requirements.txt; \
    fi

# RunPod + websocket
RUN pip install runpod websocket-client huggingface_hub

# Download Qwen Rapid AIO model
RUN mkdir -p /ComfyUI/models/checkpoints/Qwen
RUN huggingface-cli download \
    Phr00t/Qwen-Image-Edit-Rapid-AIO \
    Qwen-Rapid-AIO-v1.safetensors \
    --local-dir /ComfyUI/models/checkpoints/Qwen \
    --local-dir-use-symlinks False

COPY handler.py /handler.py
COPY workflow.json /workflow.json
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

WORKDIR /
CMD ["/entrypoint.sh"]
