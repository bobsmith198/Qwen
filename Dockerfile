FROM runpod/pytorch:2.6.0-py3.11-cuda12.8.1-cudnn-devel-ubuntu22.04

WORKDIR /

RUN apt-get update && apt-get install -y \
    git wget ffmpeg libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Fix typing_extensions conflict before installing anything else
RUN pip install --upgrade typing_extensions sqlalchemy

# ComfyUI
RUN git clone https://github.com/comfyanonymous/ComfyUI.git /ComfyUI
WORKDIR /ComfyUI
RUN pip install -r requirements.txt

# Custom nodes — WanVideoWrapper contains QwenImageEdit nodes
WORKDIR /ComfyUI/custom_nodes
RUN git clone https://github.com/kijai/ComfyUI-WanVideoWrapper.git && \
    pip install -r ComfyUI-WanVideoWrapper/requirements.txt

# RunPod + websocket
RUN pip install runpod websocket-client

# Create dirs
RUN mkdir -p /ComfyUI/models/checkpoints/Qwen && \
    mkdir -p /ComfyUI/input && \
    mkdir -p /ComfyUI/output

# Download model at build time — avoids runtime timeout issues
RUN wget -q --show-progress \
    "https://huggingface.co/Phr00t/Qwen-Image-Edit-Rapid-AIO/resolve/main/v23/Qwen-Rapid-AIO-NSFW-v23.safetensors" \
    -O /ComfyUI/models/checkpoints/Qwen/Qwen-Rapid-AIO-NSFW-v23.safetensors

COPY handler.py /handler.py
COPY workflow.json /workflow.json
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

WORKDIR /
CMD ["/entrypoint.sh"]