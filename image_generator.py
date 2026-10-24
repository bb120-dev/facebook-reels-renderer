import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from PIL import Image, ImageFilter

MODEL = "@cf/black-forest-labs/flux-1-schnell"


def load_prompts():
    path = Path(os.environ.get("REEL_CONTENT_FILE", "reel_content.json"))
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        scenes = data.get("scenes", [])
        if len(scenes) != 3:
            raise ValueError("Expected exactly three scenes")
        return [scene["image_prompt"] for scene in scenes]
    path = Path("scene_prompts.json")
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        return data["prompts"] if isinstance(data, dict) else data
    raise FileNotFoundError("Missing reel_content.json or scene_prompts.json")


def generate(prompt):
    account = os.environ["CF_ACCOUNT_ID"]
    token = os.environ["CF_API_TOKEN"]
    url = f"https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/{MODEL}"
    payload = json.dumps({"prompt": prompt + ", no words, no watermark", "steps": 4}).encode()
    req = urllib.request.Request(url, data=payload, headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}, method="POST")
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                obj = json.load(response)
            if not obj.get("success", False):
                raise RuntimeError(str(obj.get("errors", "Cloudflare error")))
            return base64.b64decode(obj["result"]["image"])
        except urllib.error.HTTPError as exc:
            if exc.code not in (429, 500, 502, 503, 504) or attempt == 2:
                raise RuntimeError(f"Cloudflare HTTP {exc.code}: {exc.read()[:300]}") from exc
            time.sleep(5 * (attempt + 1))
    raise RuntimeError("Image generation failed")


def portrait_image(raw, target):
    import io
    with Image.open(io.BytesIO(raw)) as img:
        img = img.convert("RGB")
        background = img.copy()
        background.thumbnail((1080, 1920))
        canvas = img.resize((1080, 1920), Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(35))
        foreground = img.copy()
        foreground.thumbnail((1080, 1920), Image.Resampling.LANCZOS)
        canvas.paste(foreground, ((1080 - foreground.width)//2, (1920 - foreground.height)//2))
        canvas.save(target, "JPEG", quality=90)


def main():
    prompts = load_prompts()
    if len(prompts) != 3 or not all(isinstance(p, str) and p.strip() for p in prompts):
        raise ValueError("Need three nonempty image prompts")
    Path("images").mkdir(exist_ok=True)
    for i, prompt in enumerate(prompts, 1):
        target = Path(f"images/scene{i}.jpg")
        print(f"Generating image {i}/3", flush=True)
        portrait_image(generate(prompt), target)
        print(f"Saved {target}", flush=True)


if __name__ == "__main__":
    main()
