#!/usr/bin/env python3
"""Render the image assets used by README.md.

  assets/banner.png       dark banner in the site palette, with a faint
                          multimodal "sensor trace" motif behind the wordmark
  assets/organizers/*.jpg square-cropped portraits for the organizer grid

Usage: python scripts/make_readme_assets.py
"""
import math
import random
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
BANNER = ROOT / "assets" / "banner.png"
THUMBS = ROOT / "assets" / "organizers"
THUMB_PX = 240

# Roster shown in the README organizer grid, in display order. Portraits in
# photos/ that are not listed here are not published in the README.
ORGANIZERS = [
    "Zhenyu_Yan", "Hongkai_Chen", "Siyang_Jiang",          # co-chairs
    "Guangyu_Chen", "LieKang_Zeng", "Anlan_Peng", "Xiang_Ji", "Mu_Yuan",
    "Guoliang_Xing",                                       # steering
]

W, H = 2400, 760              # rendered at 2x, displayed ~1200px wide
NAVY = (6, 16, 31)
NAVY_TOP = (9, 22, 40)
CYAN = (56, 189, 248)
TEAL = (45, 212, 191)
TEXT = (226, 234, 245)
TEXT_2 = (143, 170, 200)
TEXT_3 = (77, 107, 138)
# CUHK brand marks, sampled from the CUHK-X lockup. The brand purple only
# reaches 1.8:1 against this navy, so the wordmark uses a tint of the same hue.
CUHK_GOLD = (234, 170, 0)          # #EAAA00
CUHK_PURPLE_TINT = (168, 123, 227)  # tint of #582C83, ~4.7:1 on the banner

FONT = "/System/Library/Fonts/HelveticaNeue.ttc"
IDX = {"bold": 1, "medium": 10, "regular": 0, "light": 7, "thin": 12}


def font(weight: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT, size, index=IDX[weight])


def tracked(draw, xy, runs, f, fill=None, tracking=0, anchor_center=False):
    """Draw text with manual letter-spacing; returns the advance width.

    `runs` is either a string drawn in `fill`, or a list of (text, colour)
    pairs drawn end to end — used to colour the CUHK-X wordmark.
    """
    if isinstance(runs, str):
        runs = [(runs, fill)]
    width = sum(draw.textlength(c, font=f) + tracking
                for text, _ in runs for c in text) - tracking
    x, y = xy
    if anchor_center:
        x -= width / 2
    for text, colour in runs:
        for c in text:
            draw.text((x, y), c, font=f, fill=colour)
            x += draw.textlength(c, font=f) + tracking
    return width


def background() -> Image.Image:
    """Near-black navy field with two soft off-centre glows."""
    img = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(img)
    for y in range(H):                       # vertical gradient
        t = (y / H) ** 1.4
        d.line([(0, y), (W, y)], fill=tuple(
            round(a + (b - a) * (1 - t)) for a, b in zip(NAVY, NAVY_TOP)))

    glow = Image.new("RGB", (W, H), (0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([W * 0.58, -H * 0.75, W * 1.25, H * 0.85], fill=(8, 32, 52))
    gd.ellipse([-W * 0.18, H * 0.45, W * 0.30, H * 1.7], fill=(4, 22, 27))
    return _add(img, glow.filter(ImageFilter.GaussianBlur(230)))


def _add(a: Image.Image, b: Image.Image) -> Image.Image:
    return ImageChops.add(a, b)


def traces(img: Image.Image) -> Image.Image:
    """Six faint waveforms — one per challenge modality — fading at the edges."""
    layer = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(layer)
    rng = random.Random(11)
    specs = [
        # (baseline y, amplitude, frequency, jitter, colour, width)
        (0.13, 26, 3.1, 0.0, CYAN, 3),      # depth   — smooth
        (0.27, 15, 9.0, 0.55, TEAL, 3),     # imu     — noisy
        (0.42, 34, 1.7, 0.0, CYAN, 3),      # mmwave  — slow sweep
        (0.60, 12, 14.0, 0.35, TEAL, 3),    # skeleton
        (0.76, 22, 4.6, 0.15, CYAN, 3),     # thermal
        (0.90, 18, 7.2, 0.45, TEAL, 3),     # infrared
    ]
    for base, amp, freq, jit, colour, lw in specs:
        pts = []
        phase = rng.uniform(0, math.tau)
        for x in range(0, W + 8, 8):
            u = x / W
            y = base * H + math.sin(u * math.tau * freq + phase) * amp
            y += math.sin(u * math.tau * freq * 2.7 + phase * 1.9) * amp * 0.35
            if jit:
                y += rng.uniform(-1, 1) * amp * jit
            pts.append((x, y))
        d.line(pts, fill=colour, width=lw, joint="curve")

    # fade the traces out towards both edges and behind the wordmark
    mask = Image.new("L", (W, H), 0)
    md = ImageDraw.Draw(mask)
    for x in range(W):
        u = x / W
        edge = min(1.0, u / 0.16, (1 - u) / 0.16)
        md.line([(x, 0), (x, H)], fill=int(48 * edge))
    md.ellipse([W * 0.10, H * 0.16, W * 0.90, H * 0.84], fill=10)
    mask = mask.filter(ImageFilter.GaussianBlur(60))
    return Image.composite(_add(img, layer), img, mask)


def banner() -> None:
    img = traces(background())
    d = ImageDraw.Draw(img)
    cx = W / 2

    # eyebrow
    tracked(d, (cx, 150), "CUHK · AIoT LAB    ×    UbiComp 2026 · SHANGHAI",
            font("medium", 34), CYAN, tracking=7.5, anchor_center=True)

    # wordmark — CUHK-X in the brand purple/gold, CHALLENGE in plain white
    tracked(d, (cx, 232), [("CUHK-", CUHK_PURPLE_TINT),
                           ("X", CUHK_GOLD),
                           (" CHALLENGE", TEXT)],
            font("bold", 152), tracking=2, anchor_center=True)

    # subtitle
    tracked(d, (cx, 424), "Multimodal Human Activity Challenge",
            font("light", 62), TEXT_2, tracking=0.5, anchor_center=True)
    tracked(d, (cx, 506), "no RGB · depth, IMU, mmWave, skeleton, thermal, infrared",
            font("regular", 38), TEXT_3, tracking=1.2, anchor_center=True)

    # rule
    d.line([(cx - 460, 604), (cx + 460, 604)], fill=(20, 58, 92), width=2)

    # stat row
    tracked(d, (cx, 646),
            "2 TRACKS      40 ACTIONS      64,267 SAMPLES      $20,000 PRIZE POOL",
            font("medium", 34), TEXT_2, tracking=6, anchor_center=True)

    BANNER.parent.mkdir(parents=True, exist_ok=True)
    img.save(BANNER, optimize=True)
    print(f"wrote {BANNER.relative_to(ROOT)}  ({BANNER.stat().st_size / 1024:.0f} KB)")


def organizer_thumbs() -> None:
    """Centre-crop each portrait to a square so the README grid stays even."""
    THUMBS.mkdir(parents=True, exist_ok=True)
    for stem in ORGANIZERS:
        src = ROOT / "photos" / f"{stem}.jpg"
        im = Image.open(src).convert("RGB")
        w, h = im.size
        side = min(w, h)
        # bias the crop upwards — faces sit above centre in a portrait
        top = max(0, int((h - side) * 0.32))
        im = im.crop(((w - side) // 2, top, (w - side) // 2 + side, top + side))
        im = im.resize((THUMB_PX, THUMB_PX), Image.LANCZOS)
        im.save(THUMBS / src.name, quality=88, optimize=True)
    print(f"wrote {len(ORGANIZERS)} portraits to {THUMBS.relative_to(ROOT)}/")


def main() -> None:
    banner()
    organizer_thumbs()


if __name__ == "__main__":
    main()
