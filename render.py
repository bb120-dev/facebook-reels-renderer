
import asyncio
import math
import os
import subprocess
from pathlib import Path

import edge_tts
from PIL import Image, ImageDraw, ImageFont, features

# ==========================================
# CONFIGURATION
# ==========================================

WIDTH = 1080
HEIGHT = 1920
FPS = 25

VOICE = "ar-SA-HamedNeural"
VOICE_RATE = "-10%"


def find_arabic_font():
    candidates = [
        "/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf",
        "/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]

    for path in candidates:
        if os.path.isfile(path):
            print(f"Using Arabic font: {path}")
            return path

    raise FileNotFoundError(
        "No Arabic font found. Install fonts-noto-core."
    )


FONT_PATH = find_arabic_font()


OUTPUT_FILE = "test-reel.mp4"

SCENES = [
    {
        "title": "الذكاء الاصطناعي",
        "subtitle": "تقنية تغيّر العالم",
        "speech": (
            "هل تعلم أن الذكاء الاصطناعي "
            "أصبح جزءاً من حياتنا اليومية؟"
        ),
        "image": "images/scene1.jpg",
    },
    {
        "title": "فهم الصور",
        "subtitle": "تحليل المعلومات",
        "speech": (
            "فهو يساعدنا على فهم الصور، "
            "وتحليل المعلومات، واكتشاف الأنماط."
        ),
        "image": "images/scene2.jpg",
    },
    {
        "title": "مستقبل التكنولوجيا",
        "subtitle": "ابتكارات بلا حدود",
        "speech": (
            "ومع تطور هذه التقنية، "
            "تظهر أمامنا فرص جديدة كل يوم."
        ),
        "image": "images/scene3.jpg",
    },
]


# ==========================================
# SYSTEM UTILITIES
# ==========================================

def run(command):
    subprocess.run(command, check=True)


def check_environment():
    if not features.check("raqm"):
        raise RuntimeError(
            "Pillow does not support libraqm. "
            "Arabic text rendering is unavailable."
        )

    if not Path(FONT_PATH).is_file():
        raise FileNotFoundError(
            f"Arabic font not found: {FONT_PATH}"
        )

    for scene in SCENES:
        if not Path(scene["image"]).is_file():
            raise FileNotFoundError(
                f"Scene image missing: {scene['image']}"
            )

    print("Environment validation passed.")


def get_font(size):
    return ImageFont.truetype(FONT_PATH, size)


def audio_duration(filename):
    output = subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            filename,
        ],
        text=True,
    )

    return float(output.strip())


# ==========================================
# ARABIC TEXT RENDERING
# ==========================================

def draw_arabic(
    draw,
    text,
    center_x,
    center_y,
    size,
    color,
    max_width=940,
):
    current_size = size

    while current_size >= 24:
        current_font = get_font(current_size)

        bounds = draw.textbbox(
            (0, 0),
            text,
            font=current_font,
            direction="rtl",
            language="ar",
        )

        text_width = bounds[2] - bounds[0]

        if text_width <= max_width:
            break

        current_size -= 2

    draw.text(
        (center_x, center_y),
        text,
        font=current_font,
        fill=color,
        anchor="mm",
        direction="rtl",
        language="ar",
        stroke_width=2,
        stroke_fill=(5, 12, 24),
    )


# ==========================================
# IMAGE PROCESSING
# ==========================================

def resize_cover(image, target_width, target_height):
    source_width, source_height = image.size

    scale = max(
        target_width / source_width,
        target_height / source_height,
    )

    new_width = math.ceil(source_width * scale)
    new_height = math.ceil(source_height * scale)

    return image.resize(
        (new_width, new_height),
        Image.Resampling.LANCZOS,
    )


def make_background(source_image, progress):
    # Gentle zoom from 1.00 to 1.08
    zoom = 1.0 + 0.08 * progress

    target_width = math.ceil(WIDTH * zoom)
    target_height = math.ceil(HEIGHT * zoom)

    resized = resize_cover(
        source_image,
        target_width,
        target_height,
    )

    left = (resized.width - WIDTH) // 2
    top = (resized.height - HEIGHT) // 2

    return resized.crop(
        (
            left,
            top,
            left + WIDTH,
            top + HEIGHT,
        )
    )


def add_dark_overlay(image):
    overlay = Image.new(
        "RGBA",
        (WIDTH, HEIGHT),
        (0, 0, 0, 0),
    )

    pixels = ImageDraw.Draw(overlay)

    for y in range(HEIGHT):
        ratio = y / HEIGHT

        # Darken top and bottom for text readability
        darkness = (
            145 if ratio < 0.28
            else 85 if ratio < 0.65
            else 165
        )

        pixels.line(
            (0, y, WIDTH, y),
            fill=(2, 8, 22, darkness),
        )

    return Image.alpha_composite(
        image.convert("RGBA"),
        overlay,
    ).convert("RGB")


# ==========================================
# FRAME COMPOSITION
# ==========================================

def create_frame(scene, source_image, frame, total_frames):
    progress = (
        frame / max(total_frames - 1, 1)
    )

    image = make_background(
        source_image,
        progress,
    )

    image = add_dark_overlay(image)

    draw = ImageDraw.Draw(image)

    # Top brand label
    draw.text(
        (WIDTH // 2, 115),
        "TECH CARTOON",
        font=get_font(40),
        fill=(115, 225, 255),
        anchor="mm",
    )

    # Main Arabic title
    draw_arabic(
        draw,
        scene["title"],
        WIDTH // 2,
        330,
        86,
        (255, 255, 255),
    )

    # Decorative separator
    draw.rounded_rectangle(
        (
            WIDTH // 2 - 110,
            430,
            WIDTH // 2 + 110,
            438,
        ),
        radius=4,
        fill=(45, 220, 255),
    )

    # Subtitle
    draw_arabic(
        draw,
        scene["subtitle"],
        WIDTH // 2,
        1500,
        65,
        (120, 255, 225),
    )

    # Call to action
    draw_arabic(
        draw,
        "تابعنا للمزيد",
        WIDTH // 2,
        1700,
        45,
        (255, 255, 255),
    )

    return image


# ==========================================
# ARABIC NARRATION
# ==========================================

async def generate_audio():
    for index, scene in enumerate(SCENES):
        output = f"audio_{index}.mp3"

        print(
            f"Generating Arabic narration "
            f"{index + 1}/{len(SCENES)}"
        )

        communicate = edge_tts.Communicate(
            text=scene["speech"],
            voice=VOICE,
            rate=VOICE_RATE,
        )

        await communicate.save(output)

        if not Path(output).is_file():
            raise RuntimeError(
                f"Audio generation failed: {output}"
            )

        if Path(output).stat().st_size == 0:
            raise RuntimeError(
                f"Generated audio is empty: {output}"
            )


# ==========================================
# VIDEO RENDERING
# ==========================================

def render_scene(index, scene):
    audio_file = f"audio_{index}.mp3"
    video_file = f"scene_{index}.mp4"

    duration = audio_duration(audio_file)

    total_frames = max(
        1,
        math.ceil(duration * FPS),
    )

    print(
        f"Rendering scene {index + 1}: "
        f"{duration:.2f} seconds"
    )

    with Image.open(scene["image"]) as image:
        source_image = image.convert("RGB")

    process = subprocess.Popen(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "-s",
            f"{WIDTH}x{HEIGHT}",
            "-r",
            str(FPS),
            "-i",
            "-",
            "-i",
            audio_file,
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-crf",
            "23",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-af",
            "apad",
            "-t",
            str(total_frames / FPS),
            "-movflags",
            "+faststart",
            video_file,
        ],
        stdin=subprocess.PIPE,
    )

    try:
        for frame_number in range(total_frames):
            frame_image = create_frame(
                scene,
                source_image,
                frame_number,
                total_frames,
            )

            process.stdin.write(
                frame_image.tobytes()
            )

    except BrokenPipeError as error:
        raise RuntimeError(
            "FFmpeg stopped before rendering finished"
        ) from error

    finally:
        if process.stdin:
            process.stdin.close()

    return_code = process.wait()

    if return_code != 0:
        raise RuntimeError(
            f"Scene rendering failed: {index + 1}"
        )

    print(
        f"Scene {index + 1} completed."
    )


# ==========================================
# FINAL VIDEO ASSEMBLY
# ==========================================

def combine_scenes():
    playlist = Path("scenes.txt")

    with playlist.open(
        "w",
        encoding="utf-8",
    ) as file:
        for index in range(len(SCENES)):
            file.write(
                f"file 'scene_{index}.mp4'\n"
            )

    run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(playlist),
            "-c",
            "copy",
            "-movflags",
            "+faststart",
            OUTPUT_FILE,
        ]
    )

    output = Path(OUTPUT_FILE)

    if not output.is_file():
        raise RuntimeError(
            "Final Reel was not created"
        )

    if output.stat().st_size == 0:
        raise RuntimeError(
            "Final Reel is empty"
        )

    print(
        f"Final Reel created: {OUTPUT_FILE}"
    )


# ==========================================
# MAIN
# ==========================================

def main():
    check_environment()

    asyncio.run(generate_audio())

    for index, scene in enumerate(SCENES):
        render_scene(index, scene)

    combine_scenes()

    print("SUCCESS: Arabic Reel is ready.")


if __name__ == "__main__":
    main()
