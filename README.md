# rapid-qwen — RunPod Serverless Worker

Qwen Image Edit Rapid AIO on RunPod Serverless.
Model downloads to network volume on first run and is cached.

## Setup
- Attach a network volume (10GB+ sufficient)
- First cold start downloads the model
- Subsequent starts symlink from volume — fast

## Input
```json
{
  "input": {
    "prompt": "add watercolor style, soft pastel tones",
    "negative_prompt": "",
    "image_url": "https://...",
    "image_url_2": "https://...",
    "image_url_3": "https://...",
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
- image1 required: image_url / image_base64 / image_path
- image2 optional: image_url_2 / image_base64_2 / image_path_2
- image3 optional: image_url_3 / image_base64_3 / image_path_3

## Output
```json
{ "image": "<base64 encoded PNG>" }
```

## Container disk
20GB is enough — model lives on network volume.
