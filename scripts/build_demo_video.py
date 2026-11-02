"""Build a dependency-light three-minute MJPEG demo video.

The video is intentionally self-contained: it uses the synthetic smoke run,
does not record a user's screen or voice, and pairs with demo/demo_script.md
for narration. MJPEG AVI is used so the artifact can be built offline with
Pillow and Python's standard library.
"""

from __future__ import annotations

import io
import struct
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "demo" / "demo_video.avi"
WIDTH, HEIGHT, FPS, DURATION = 640, 360, 1, 180


def font(size: int, bold: bool = False):
    candidates = [
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


TITLE = font(30, True)
SUBTITLE = font(18, True)
BODY = font(15)
SMALL = font(12)


SCENES = [
    (0, "Multilingual Retrieval Fairness", "Three languages. One benchmark. Measured gaps.", "Phase-I implementation demo"),
    (15, "The research question", "Does retrieval quality stay comparable in English, Hindi and Malayalam?", "Recall, MRR, nDCG and answer quality"),
    (30, "Offline smoke fixture", "9 synthetic documents + 9 aligned queries", "Topics: pension, water supply and emergencies"),
    (45, "Data governance", "No real personal data is included", "Source registry records provenance, license and coverage checks"),
    (60, "Pipeline architecture", "Bronze -> Silver -> Gold -> Retrieval -> Evidence", "JSONL storage | partition accounting | run manifest"),
    (75, "Baseline systems", "BM25 | LaBSE* | multilingual-e5-base* | hybrid", "*Optional transformers fall back transparently in smoke mode"),
    (90, "Mitigations", "Translation | hybrid fusion | alignment pilot", "Every mitigation uses the same queries and language splits"),
    (105, "Fairness evidence", "Report each language separately", "Gap = maximum language mean - minimum language mean"),
    (120, "Big-data evidence", "Scale sweep: 9 -> 90 -> 900 rows", "Rows, partitions, storage bytes, elapsed time and throughput"),
    (135, "Responsible-AI guardrails", "Provenance, uncertainty, bilingual review and limitations", "A small measured gap is not a universal fairness claim"),
    (150, "Reproducibility", "One command runs the smoke pipeline", "Notebook, report, model card, data card, Docker and CI included"),
    (165, "Next phase", "Lock public-data licenses and run the full benchmark", "Team: Sujan S M + Swasthik Pamadi"),
]


def scene_at(second: int):
    current = SCENES[0]
    for scene in SCENES:
        if scene[0] <= second:
            current = scene
        else:
            break
    return current


def wrap(draw: ImageDraw.ImageDraw, text: str, max_width: int, face):
    words = text.split()
    lines, line = [], ""
    for word in words:
        candidate = (line + " " + word).strip()
        if draw.textbbox((0, 0), candidate, font=face)[2] <= max_width:
            line = candidate
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def frame(second: int) -> bytes:
    _, title, message, detail = scene_at(second)
    image = Image.new("RGB", (WIDTH, HEIGHT), (15, 23, 42))
    draw = ImageDraw.Draw(image)

    for y in range(HEIGHT):
        shade = int(15 + (y / HEIGHT) * 18)
        draw.line((0, y, WIDTH, y), fill=(shade, shade + 10, shade + 30))

    draw.rectangle((32, 28, WIDTH - 32, HEIGHT - 34), outline=(56, 189, 248), width=2)
    draw.rectangle((52, 56, 588, 60), fill=(249, 115, 22))
    draw.text((52, 78), "BDSRAE / MULTILINGUAL RETRIEVAL FAIRNESS", font=SMALL, fill=(148, 163, 184))
    draw.text((52, 112), title, font=TITLE, fill=(248, 250, 252))

    y = 174
    for line in wrap(draw, message, 520, SUBTITLE):
        draw.text((52, y), line, font=SUBTITLE, fill=(125, 211, 252))
        y += 28
    y += 20
    for line in wrap(draw, detail, 520, BODY):
        draw.text((52, y), line, font=BODY, fill=(226, 232, 240))
        y += 23

    draw.text((52, HEIGHT - 64), f"Demo timeline  {second:03d}s / {DURATION:03d}s", font=SMALL, fill=(148, 163, 184))
    draw.rectangle((52, HEIGHT - 42, 588, HEIGHT - 36), fill=(51, 65, 85))
    progress = int(536 * ((second + 1) / DURATION))
    draw.rectangle((52, HEIGHT - 42, 52 + progress, HEIGHT - 36), fill=(34, 211, 238))

    output = io.BytesIO()
    image.save(output, format="JPEG", quality=82, optimize=True)
    return output.getvalue()


def chunk(tag: bytes, payload: bytes) -> bytes:
    padded = payload + (b"\x00" if len(payload) % 2 else b"")
    return tag + struct.pack("<I", len(payload)) + padded


def list_chunk(payload: bytes) -> bytes:
    return b"LIST" + struct.pack("<I", len(payload) + 4) + payload


def build() -> Path:
    frames = [frame(second) for second in range(DURATION)]
    max_frame = max(map(len, frames))

    avih = struct.pack(
        "<IIIIIIIIII4I",
        1_000_000, 0, 0, 0x10, DURATION, 0, 1, max_frame,
        WIDTH, HEIGHT, 0, 0, 0, 0,
    )
    strh = struct.pack(
        "<4s4sIHHIIIIIIIIhhhh",
        b"vids", b"MJPG", 0, 0, 0, 0, 1, FPS, 0, DURATION,
        max_frame, 0xFFFFFFFF, 0, 0, 0, WIDTH, HEIGHT,
    )
    strf = struct.pack(
        "<IiiHH4sIIiiII",
        40, WIDTH, HEIGHT, 1, 24, b"MJPG", 0, 0, 0, 0, 0, 0,
    )
    hdrl = list_chunk(b"hdrl" + chunk(b"avih", avih) + list_chunk(b"strl" + chunk(b"strh", strh) + chunk(b"strf", strf)))

    movi_payload = bytearray(b"movi")
    index = []
    for data in frames:
        offset = len(movi_payload) - 4
        movi_payload.extend(chunk(b"00dc", data))
        index.append(struct.pack("<4sIII", b"00dc", 0x10, offset, len(data)))
    movi = b"LIST" + struct.pack("<I", len(movi_payload)) + bytes(movi_payload)
    idx1 = chunk(b"idx1", b"".join(index))
    riff_payload = b"AVI " + hdrl + movi + idx1
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_bytes(b"RIFF" + struct.pack("<I", len(riff_payload)) + riff_payload)
    return OUTPUT


if __name__ == "__main__":
    print(build())
