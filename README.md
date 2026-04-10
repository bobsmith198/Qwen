# rapid-qwen — RunPod Serverless Worker

Qwen Image Edit Rapid AIO on RunPod Serverless.

## Key differences from standard Qwen edit
- Single checkpoint (VAE + CLIP + model merged)
- 4 steps at cfg=1 (much faster)
- sa_solver/beta recommended

## Input
```json
{
  "input": {
    "prompt": "add watercolor style, soft pastel tones",
    "negative_prompt": "",
    "image_url": "https://...",
    "image_url_2": "https://...",
    "seed": 42,
    "cfg": 1.0,
    "width": 1024,
    "height": 1024,
    "steps": 4,
    "sampler": "sa_solver",
    "scheduler": "beta"
  }
}
```

## Images
- image1: required (image_url / image_base64 / image_path)
- image2: optional second reference (image_url_2 / image_base64_2 / image_path_2)
- image3: optional third reference (image_url_3 / image_base64_3 / image_path_3)

## Output
```json
{ "image": "<base64 encoded PNG>" }
```

## Deploy
1. Push to GitHub
2. Create RunPod Serverless endpoint from this repo
3. GPU: 24GB+ recommended (A100, RTX 4090)
4. Container disk: 40GB+
