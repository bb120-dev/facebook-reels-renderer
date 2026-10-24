"""Generate scene images with Cloudflare Workers AI.

Requires CF_ACCOUNT_ID and CF_API_TOKEN environment variables.
Usage: python image_generator.py --prompts-file scene_prompts.json
"""
import argparse
import base64
import io
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from PIL import Image, ImageOps

MODEL = '@cf/black-forest-labs/flux-1-schnell'
ENDPOINT = 'https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/' + MODEL
DEFAULT_PROMPTS = [
    'A cinematic futuristic city at dusk, wide establishing shot, dramatic lighting, no text or logos',
    'A friendly humanoid robot walking through a futuristic street, cinematic photograph, no text or logos',
    'A close-up of a futuristic robot observing city lights, cinematic photograph, no text or logos',
]

def generate(prompt, account, token, attempts=3):
    payload = json.dumps({'prompt': prompt + ', no captions, no letters, no watermarks', 'steps': 4}).encode('utf-8')
    req = urllib.request.Request(ENDPOINT.format(account=account), data=payload,
        headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'}, method='POST')
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.load(resp)
            if not data.get('success', False):
                raise RuntimeError('Cloudflare API returned unsuccessful response: ' + str(data.get('errors', [])))
            result = data.get('result') or {}
            encoded = result.get('image') if isinstance(result, dict) else None
            if not encoded:
                raise RuntimeError('No result.image returned; verify model response format')
            return base64.b64decode(encoded, validate=True)
        except urllib.error.HTTPError as e:
            body = e.read(1200).decode('utf-8', 'replace')
            print(f'Cloudflare HTTP {e.code}: {body}', file=sys.stderr)
            if e.code not in (429, 500, 502, 503, 504) or attempt == attempts - 1:
                raise
        except (urllib.error.URLError, TimeoutError) as e:
            print(f'Cloudflare transient error: {e}', file=sys.stderr)
            if attempt == attempts - 1:
                raise
        time.sleep(2 ** attempt * 3)
    raise RuntimeError('Image generation failed')

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--prompts-file', default='scene_prompts.json')
    p.add_argument('--output-dir', default='images')
    p.add_argument('--allow-fallback', action='store_true', help='Use existing scene image if generation fails')
    args = p.parse_args()
    account, token = os.getenv('CF_ACCOUNT_ID'), os.getenv('CF_API_TOKEN')
    if not account or not token:
        raise SystemExit('Missing CF_ACCOUNT_ID or CF_API_TOKEN environment variables')
    prompts = DEFAULT_PROMPTS
    prompts_file = Path(args.prompts_file)
    if prompts_file.exists():
        loaded = json.loads(prompts_file.read_text(encoding='utf-8'))
        if isinstance(loaded, dict):
            loaded = loaded.get('prompts')
        if not isinstance(loaded, list) or len(loaded) != 3 or any(not isinstance(x, str) or not x.strip() for x in loaded):
            raise SystemExit('Prompts JSON must contain exactly three non-empty strings')
        prompts = loaded
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    for i, prompt in enumerate(prompts, 1):
        path = output / f'scene{i}.jpg'
        print(f'Generating scene {i}/3...', flush=True)
        try:
            raw = generate(prompt, account, token)
            with Image.open(io.BytesIO(raw)) as im:
                im = ImageOps.exif_transpose(im).convert('RGB')
                # 9:16 canvas without destructive cropping: background fills, foreground stays intact.
                bg = ImageOps.fit(im, (1080, 1920), method=Image.Resampling.LANCZOS)
                from PIL import ImageFilter
                bg = bg.filter(ImageFilter.GaussianBlur(radius=30))
                fg = ImageOps.contain(im, (1080, 1920), method=Image.Resampling.LANCZOS)
                bg.paste(fg, ((1080 - fg.width)//2, (1920 - fg.height)//2))
                bg.save(path, quality=91, optimize=True)
            print(f'Saved {path}', flush=True)
        except Exception as exc:
            if args.allow_fallback and path.is_file() and path.stat().st_size > 0:
                print(f'WARNING: scene {i} failed ({type(exc).__name__}); keeping existing {path}', file=sys.stderr)
            else:
                raise

if __name__ == '__main__':
    main()
