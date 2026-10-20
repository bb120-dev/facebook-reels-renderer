
import asyncio
import math
import os
import random
import subprocess

import edge_tts
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

WIDTH = 720
HEIGHT = 1280
FPS = 25

VOICE = "ar-SA-HamedNeural"
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

SCENES = [
    {
        "title": "الذكاء الاصطناعي",
        "subtitle": "تقنية تغيّر العالم",
        "speech": "هل تعلم أن الذكاء الاصطناعي أصبح جزءاً من حياتنا اليومية؟",
        "kind": "brain",
    },
    {
        "title": "فهم الصور",
        "subtitle": "تحليل المعلومات",
        "speech": "فهو يساعدنا على فهم الصور، وتحليل المعلومات، واكتشاف الأنماط.",
        "kind": "vision",
    },
    {
        "title": "مستقبل التكنولوجيا",
        "subtitle": "ابتكارات بلا حدود",
        "speech": "ومع تطور هذه التقنية، تظهر أمامنا فرص جديدة كل يوم.",
        "kind": "future",
    },
]


def run(command):
    subprocess.run(command, check=True)


def arabic(text):
    return get_display(arabic_reshaper.reshape(text))


def font(size):
    return ImageFont.truetype(FONT_PATH, size)


def centered(draw, text, y, size, fill):
    draw.text(
        (WIDTH // 2, y),
        arabic(text),
        font=font(size),
        fill=fill,
        anchor="mm",
        stroke_width=1,
        stroke_fill=(5, 12, 30),
    )


def background(draw, frame, scene_index):
    for y in range(HEIGHT):
        r = int(7 + y / HEIGHT * 9)
        g = int(18 + y / HEIGHT * 18)
        b = int(42 + y / HEIGHT * 28)
        draw.line((0, y, WIDTH, y), fill=(r, g, b))

    shift = int(frame * 0.7) % 80

    for x in range(-80, WIDTH + 80, 80):
        draw.line(
            (x + shift, 0, x + shift, HEIGHT),
            fill=(17, 48, 78),
            width=1,
        )

    for y in range(0, HEIGHT, 80):
        draw.line(
            (0, y, WIDTH, y),
            fill=(17, 48, 78),
            width=1,
        )


def brain_scene(draw, frame):
    cx, cy = WIDTH // 2, 550
    pulse = 1 + 0.06 * math.sin(frame / 8)

    points = []

    for i in range(14):
        angle = 2 * math.pi * i / 14
        radius = (175 if i % 2 == 0 else 110) * pulse
        x = cx + math.cos(angle) * radius
        y = cy + math.sin(angle) * radius
        points.append((x, y))

    for i, a in enumerate(points):
        for j, b in enumerate(points):
            if j > i and (j - i) % 3 == 0:
                draw.line((a, b), fill=(22, 110, 165), width=2)

    for i, (x, y) in enumerate(points):
        radius = 8 + 3 * math.sin(frame / 10 + i)
        draw.ellipse(
            (x - radius, y - radius, x + radius, y + radius),
            fill=(40, 220, 255),
        )

    draw.ellipse(
        (cx - 55, cy - 55, cx + 55, cy + 55),
        fill=(15, 75, 125),
        outline=(75, 235, 255),
        width=5,
    )


def vision_scene(draw, frame):
    cx, cy = WIDTH // 2, 560
    size = 220
    offset = int(25 * math.sin(frame / 12))

    draw.rounded_rectangle(
        (cx - size, cy - size, cx + size, cy + size),
        radius=35,
        outline=(55, 210, 255),
        width=7,
    )

    draw.ellipse(
        (cx - 155, cy - 85, cx + 155, cy + 85),
        outline=(100, 240, 255),
        width=8,
    )

    draw.ellipse(
        (cx - 55, cy - 55, cx + 55, cy + 55),
        fill=(40, 170, 225),
    )

    draw.line(
        (cx - 200, cy + offset, cx + 200, cy + offset),
        fill=(80, 255, 170),
        width=6,
    )


def future_scene(draw, frame):
    cx, cy = WIDTH // 2, 570

    for i in range(6):
        radius = 55 + i * 43
        angle = frame / 35 + i * 0.7

        color = (
            25 + i * 8,
            min(255, 115 + i * 20),
            245,
        )

        draw.arc(
            (
                cx - radius,
                cy - radius,
                cx + radius,
                cy + radius,
            ),
            start=math.degrees(angle) % 360,
            end=(math.degrees(angle) + 220) % 360,
            fill=color,
            width=7,
        )

    draw.ellipse(
        (cx - 45, cy - 45, cx + 45, cy + 45),
        fill=(45, 215, 245),
    )


def make_frame(scene, scene_index, frame):
    image = Image.new("RGB", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(image)

    background(draw, frame, scene_index)

    centered(
        draw,
        "TECH CARTOON",
        105,
        30,
        (100, 210, 255),
    )

    centered(
        draw,
        scene["title"],
        260,
        48,
        (255, 255, 255),
    )

    if scene["kind"] == "brain":
        brain_scene(draw, frame)
    elif scene["kind"] == "vision":
        vision_scene(draw, frame)
    else:
        future_scene(draw, frame)

    centered(
        draw,
        scene["subtitle"],
        960,
        37,
        (100, 245, 220),
    )

    centered(
        draw,
        "تابعنا للمزيد",
        1120,
        27,
        (220, 230, 245),
    )

    return image


async def generate_audio():
    for index, scene in enumerate(SCENES):
        filename = f"audio_{index}.mp3"

        communicate = edge_tts.Communicate(
            text=scene["speech"],
            voice=VOICE,
            rate="-10%",
        )

        await communicate.save(filename)


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


def render_scene(index, scene):
    audio = f"audio_{index}.mp3"
    duration = audio_duration(audio)
    frames = math.ceil(duration * FPS)

    output = f"scene_{index}.mp4"

    process = subprocess.Popen(
        [
            "ffmpeg",
            "-y",
            "-f",
            "rawvideo",
            "-vcodec",
            "rawvideo",
            "-s",
            f"{WIDTH}x{HEIGHT}",
            "-pix_fmt",
            "rgb24",
            "-r",
            str(FPS),
            "-i",
            "-",
            "-i",
            audio,
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-crf",
            "25",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-af",
            "apad",
            "-t",
            str(frames / FPS),
            "-movflags",
            "+faststart",
            output,
        ],
        stdin=subprocess.PIPE,
    )

    try:
        for frame in range(frames):
            image = make_frame(scene, index, frame)
            process.stdin.write(image.tobytes())
    finally:
        process.stdin.close()

    if process.wait() != 0:
        raise RuntimeError(f"FFmpeg failed for scene {index}")

    print(f"Scene {index + 1} rendered: {duration:.2f}s")


def combine_scenes():
    with open("scenes.txt", "w", encoding="utf-8") as file:
        for index in range(len(SCENES)):
            file.write(f"file 'scene_{index}.mp4'\n")

    run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            "scenes.txt",
            "-c",
            "copy",
            "-movflags",
            "+faststart",
            "test-reel.mp4",
        ]
    )


def main():
    asyncio.run(generate_audio())

    for index, scene in enumerate(SCENES):
        render_scene(index, scene)

    combine_scenes()

    if not os.path.isfile("test-reel.mp4"):
        raise RuntimeError("Final video was not created")

    print("Final Reel created successfully.")


if __name__ == "__main__":
    main()
