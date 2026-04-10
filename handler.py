import runpod
import os
import websocket
import base64
import json
import uuid
import logging
import urllib.request
import subprocess
import binascii
import time
import shutil

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SERVER_ADDRESS = os.getenv('SERVER_ADDRESS', '127.0.0.1')
CLIENT_ID      = str(uuid.uuid4())
COMFY_URL      = f"http://{SERVER_ADDRESS}:8188"
WS_URL         = f"ws://{SERVER_ADDRESS}:8188/ws?clientId={CLIENT_ID}"
COMFY_INPUT    = "/ComfyUI/input"
COMFY_OUTPUT   = "/ComfyUI/output"

def wait_for_comfyui(timeout=600):
    logger.info("Waiting for ComfyUI (may take longer on first run while models download)...")
    start = time.time()
    while time.time() - start < timeout:
        try:
            urllib.request.urlopen(f"{COMFY_URL}/", timeout=3)
            logger.info("ComfyUI ready")
            return
        except:
            time.sleep(3)
    raise Exception("ComfyUI did not start in time")

def to_multiple_of_16(v):
    return max(16, int(round(float(v) / 16.0) * 16))

def save_base64(b64_data, out_path):
    clean    = b64_data.split(',')[1] if ',' in b64_data else b64_data
    clean    = clean.replace('\n','').replace('\r','').replace(' ','')
    unpadded = clean.rstrip('=')
    padded   = unpadded + '=' * ((4 - len(unpadded) % 4) % 4)
    try:
        with open(out_path, 'wb') as f:
            f.write(base64.b64decode(padded))
        return out_path
    except (binascii.Error, ValueError) as e:
        raise Exception(f"Base64 decode failed: {e}")

def download_url(url, out_path):
    result = subprocess.run(
        ['wget', '-O', out_path, '--no-verbose',
         '--user-agent', 'Mozilla/5.0 (compatible)', url],
        capture_output=True, text=True, timeout=120
    )
    if result.returncode != 0:
        raise Exception(f"Download failed: {result.stderr}")
    return out_path

def resolve_image(inp, key_path, key_url, key_b64, task_id, filename):
    os.makedirs(COMFY_INPUT, exist_ok=True)
    out = os.path.join(COMFY_INPUT, f"{task_id}_{filename}")
    if key_path in inp:
        shutil.copy(inp[key_path], out)
        return os.path.basename(out)
    elif key_url in inp:
        download_url(inp[key_url], out)
        return os.path.basename(out)
    elif key_b64 in inp:
        save_base64(inp[key_b64], out)
        return os.path.basename(out)
    return None

def queue_prompt(prompt):
    data = json.dumps({"prompt": prompt, "client_id": CLIENT_ID}).encode()
    req  = urllib.request.Request(f"{COMFY_URL}/prompt", data=data)
    return json.loads(urllib.request.urlopen(req).read())

def get_history(prompt_id):
    with urllib.request.urlopen(f"{COMFY_URL}/history/{prompt_id}") as r:
        return json.loads(r.read())

def run_workflow(ws, prompt):
    prompt_id = queue_prompt(prompt)['prompt_id']
    while True:
        msg = ws.recv()
        if isinstance(msg, str):
            data = json.loads(msg)
            if data.get('type') == 'executing':
                node = data['data'].get('node')
                pid  = data['data'].get('prompt_id')
                if node is None and pid == prompt_id:
                    break

    history = get_history(prompt_id)[prompt_id]
    for node_id, node_output in history['outputs'].items():
        if 'images' in node_output:
            for img in node_output['images']:
                img_path = os.path.join(COMFY_OUTPUT, img['filename'])
                if os.path.exists(img_path):
                    with open(img_path, 'rb') as f:
                        return base64.b64encode(f.read()).decode('utf-8')
    return None

def load_workflow(path):
    with open(path) as f:
        return json.load(f)

def handler(job):
    inp     = job.get('input', {})
    task_id = str(uuid.uuid4())[:8]
    logger.info(f"Job input keys: {list(inp.keys())}")

    # Resolve input images
    image1 = resolve_image(inp,
        'image_path',   'image_url',   'image_base64',
        task_id, 'image1.jpg')
    image2 = resolve_image(inp,
        'image_path_2', 'image_url_2', 'image_base64_2',
        task_id, 'image2.jpg')
    image3 = resolve_image(inp,
        'image_path_3', 'image_url_3', 'image_base64_3',
        task_id, 'image3.jpg')

    if not image1:
        return {'error': 'At least one input image required'}

    image_count = sum(1 for x in [image1, image2, image3] if x)
    logger.info(f"Images provided: {image_count}")

    prompt = load_workflow('/workflow.json')

    width     = to_multiple_of_16(inp.get('width',  1024))
    height    = to_multiple_of_16(inp.get('height', 1024))
    steps     = int(inp.get('steps',     4))
    seed      = int(inp.get('seed',     42))
    cfg       = float(inp.get('cfg',   1.0))
    sampler   = inp.get('sampler',   'sa_solver')
    scheduler = inp.get('scheduler', 'beta')
    pos_prompt = inp.get('prompt', '')
    neg_prompt = inp.get('negative_prompt', '')

    # Node 1 — CheckpointLoaderSimple
    prompt['1']['widgets_values'] = ['Qwen/Qwen-Rapid-AIO-v1.safetensors']

    # Node 9 — EmptyLatentImage (output size)
    prompt['9']['widgets_values'] = [width, height, 1]

    # Node 2 — KSampler
    # [seed, control_after_gen, steps, cfg, sampler, scheduler, denoise]
    prompt['2']['widgets_values'] = [seed, 'fixed', steps, cfg, sampler, scheduler, 1]

    # Node 3 — TextEncodeQwenImageEditPlus (positive)
    prompt['3']['widgets_values'] = [pos_prompt]

    # Node 4 — TextEncodeQwenImageEditPlus (negative)
    prompt['4']['widgets_values'] = [neg_prompt]

    # Node 7 — LoadImage (image1, always required)
    prompt['7']['widgets_values'] = [image1, 'image']

    # Node 8 — LoadImage (image2, optional)
    if image2:
        prompt['8']['widgets_values'] = [image2, 'image']
    else:
        # Disconnect node 8 from node 3 by nulling link 18
        for i in prompt['3'].get('inputs', []):
            if i.get('name') == 'image2':
                i['link'] = None
        if '8' in prompt:
            del prompt['8']

    # image3 — add dynamic LoadImage node if provided
    if image3:
        max_id     = str(max(int(k) for k in prompt.keys()) + 1)
        new_link   = 50
        prompt[max_id] = {
            "inputs": [],
            "outputs": [{"name": "IMAGE", "type": "IMAGE",
                         "links": [new_link], "slot_index": 0}],
            "class_type": "LoadImage",
            "widgets_values": [image3, "image"]
        }
        for i in prompt['3'].get('inputs', []):
            if i.get('name') == 'image3':
                i['link'] = new_link
                break
        logger.info(f"image3 wired via node {max_id}")

    # Connect WebSocket
    ws = websocket.WebSocket()
    for attempt in range(10):
        try:
            ws.connect(WS_URL)
            logger.info(f"WebSocket connected (attempt {attempt+1})")
            break
        except Exception as e:
            logger.warning(f"WS connect failed ({attempt+1}/10): {e}")
            if attempt == 9:
                raise
            time.sleep(3)

    try:
        image_b64 = run_workflow(ws, prompt)
    finally:
        ws.close()
        for fname in [image1, image2, image3]:
            if fname:
                fp = os.path.join(COMFY_INPUT, fname)
                if os.path.exists(fp):
                    os.remove(fp)

    if image_b64:
        return {'image': image_b64}
    return {'error': 'No image output found'}

wait_for_comfyui()
runpod.serverless.start({'handler': handler})
