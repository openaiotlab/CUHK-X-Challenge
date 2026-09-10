#!/usr/bin/env python3
"""Render a standalone MP4 of the CUHK-X Explorer's hero "spectral sweep".

The Explorer (https://openaiotlab.github.io/CUHK-X/explorer/) shows one
synchronized moment through three sensors at once — depth, infrared and
thermal — split by draggable dividers. A web page can be dragged; a video
cannot, so this reproduces the panel in its default state: thirds, the same
palette, tags and timecode, with the HUD chrome drawn around it.

Source clips come from the Explorer's own published manifest, so the video
always tracks whatever trial the site currently features.

    python scripts/make_sweep_video.py            # -> assets/spectral-sweep.mp4
    python scripts/make_sweep_video.py --width 960

Requires: ffmpeg on PATH, Pillow.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT_MP4 = ROOT / "assets" / "spectral-sweep.mp4"
OUT_POSTER = ROOT / "assets" / "spectral-sweep.jpg"
CACHE = Path(tempfile.gettempdir()) / "cuhkx-sweep-cache"

EXPLORER = "https://openaiotlab.github.io/CUHK-X/explorer/"
FONT_CSS = ("https://fonts.googleapis.com/css"
            "?family=Chakra+Petch:600|IBM+Plex+Mono:400,500")

# ---- palette, lifted from the Explorer's style.css --------------------------
BG = (5, 8, 12)             # --bg
PANEL_TOP = (13, 22, 34)    # --panel2
PANEL_BOT = (10, 17, 25)    # --panel
LINE = (22, 34, 47)         # --line
TEXT = (214, 227, 238)      # --text
DIM = (95, 118, 137)        # --dim
FAINT = (56, 73, 90)        # --faint
DEPTH = (46, 230, 200)      # --depth
IR = (255, 106, 60)         # --ir
THERMAL = (255, 194, 61)    # --thermal
BAD = (255, 93, 93)         # --bad
TAG_INK = (4, 9, 12)

FPS = 25
SPLITS = (1 / 3, 2 / 3)     # the panel's default divider positions


# --------------------------------------------------------------- small utils
def fetch(url: str, dest: Path) -> Path:
    """Download `url` to `dest` once, then reuse it."""
    if dest.exists() and dest.stat().st_size:
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"  fetching {url.rsplit('/', 1)[-1]}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/4.0"})
    with urllib.request.urlopen(req) as r, dest.open("wb") as f:
        f.write(r.read())
    return dest


def fonts() -> dict[str, Path]:
    """Grab the Explorer's two Google fonts as TTFs (the v1 CSS endpoint
    serves truetype to old user agents; css2 only offers woff2)."""
    css = fetch(FONT_CSS, CACHE / "fonts.css").read_text()
    urls = re.findall(r"https://\S+?\.ttf", css)
    faces = {}
    for name, url in zip(("disp", "mono", "mono_med"), urls):
        faces[name] = fetch(url, CACHE / f"{name}.ttf")
    return faces


def tracked(draw, xy, text, font, fill, tracking=0.0, anchor="l"):
    """Draw text with CSS-style letter-spacing. anchor: l | c | r."""
    width = sum(draw.textlength(c, font=font) + tracking for c in text) - tracking
    x, y = xy
    x -= width if anchor == "r" else width / 2 if anchor == "c" else 0
    for c in text:
        draw.text((x, y), c, font=font, fill=fill)
        x += draw.textlength(c, font=font) + tracking
    return width


def cap_center(font, cy: float) -> float:
    """Draw-y that centres a line's cap height on `cy`."""
    top, bottom = font.getbbox("H")[1], font.getbbox("H")[3]
    return cy - (top + bottom) / 2


def pill(draw, xy, text, font, bg, tracking, pad):
    """A solid label chip — the Explorer's modality tags."""
    px, py = pad
    h = font.getbbox("H")[3] - font.getbbox("H")[1]
    w = sum(draw.textlength(c, font=font) + tracking for c in text) - tracking
    x, y = xy
    draw.rectangle([x, y, x + w + 2 * px, y + h + 2 * py], fill=bg)
    tracked(draw, (x + px, y + py - font.getbbox("H")[1]), text, font,
            TAG_INK, tracking)


# ------------------------------------------------------------ source clips
def hero_clips() -> tuple[list[Path], str]:
    """Resolve the featured trial from the Explorer manifest and cache it."""
    m = json.loads(fetch(EXPLORER + "data/manifest.json",
                         CACHE / "manifest.json").read_text())
    sets = m["hauSets"]
    st = next((s for s in sets if s["id"] == m["hero"]["set"]), sets[0])
    tr = next((t for t in st["trials"] if t["trial"] == m["hero"]["trial"]),
              st["trials"][0])
    paths = [fetch(EXPLORER + "data/" + tr["clips"][k],
                   CACHE / "clips" / st["id"] / f"t{tr['trial']}" / f"{k}.mp4")
             for k in ("depth", "ir", "thermal")]
    meta = (f"SYNC ×3 · {st['user'].upper()} · "
            f"S{st['scene']}E{st['env']} · {tr['pace'].upper()}")
    return paths, meta


# ---------------------------------------------------------------- the frame
class Layout:
    """Panel geometry, scaled from the Explorer's rem-based sizing."""

    def __init__(self, width: int):
        self.margin = round(width * 0.0219) // 2 * 2
        self.stage_w = width - 2 * self.margin
        self.stage_w -= self.stage_w % 3          # exact thirds
        self.stage_h = round(self.stage_w * 3 / 4) // 2 * 2
        self.k = self.stage_w / 560               # vs. the panel's size on the page
        self.head_h = round(34 * self.k) // 2 * 2
        self.hint_h = round(28 * self.k) // 2 * 2
        self.w = self.stage_w + 2 * self.margin
        self.h = self.head_h + self.stage_h + self.hint_h + 2 * self.margin
        self.stage_x = self.margin
        self.stage_y = self.margin + self.head_h
        self.inset = round(9.6 * self.k)          # the panel's 0.6rem inset

    def px(self, rem: float) -> int:
        return max(1, round(rem * 16 * self.k))


def chrome(L: Layout, meta: str, f: dict) -> tuple[Image.Image, Image.Image, tuple]:
    """Everything that never changes: the panel behind the stage, and the
    dividers / tags / timecode frame that sit on top of it."""
    disp = ImageFont.truetype(str(f["disp"]), L.px(0.78))
    mono = ImageFont.truetype(str(f["mono"]), L.px(0.66))
    mono_tag = ImageFont.truetype(str(f["mono_med"]), L.px(0.6))
    mono_tc = ImageFont.truetype(str(f["mono_med"]), L.px(0.72))
    hint_f = ImageFont.truetype(str(f["mono"]), L.px(0.64))

    base = Image.new("RGB", (L.w, L.h), BG)
    d = ImageDraw.Draw(base)

    # panel: vertical gradient + hairline border
    px0, py0 = L.margin, L.margin
    px1, py1 = L.margin + L.stage_w, L.h - L.margin
    for y in range(py0, py1):
        t = (y - py0) / max(1, py1 - py0)
        d.line([(px0, y), (px1, y)], fill=tuple(
            round(a + (b - a) * t) for a, b in zip(PANEL_TOP, PANEL_BOT)))
    d.rectangle([px0, py0, px1 - 1, py1 - 1], outline=LINE, width=2)
    d.line([(px0, L.stage_y - 1), (px1, L.stage_y - 1)], fill=LINE, width=2)

    # the HUD's clipped corner brackets
    arm, th = round(14 * L.k), max(2, round(2 * L.k))
    d.line([(px0, py0), (px0 + arm, py0)], fill=DEPTH, width=th)
    d.line([(px0, py0), (px0, py0 + arm)], fill=DEPTH, width=th)
    d.line([(px1 - arm, py1 - th), (px1, py1 - th)], fill=DEPTH, width=th)
    d.line([(px1 - th, py1 - arm), (px1 - th, py1)], fill=DEPTH, width=th)

    # header
    pad_x = round(0.9 * 16 * L.k)
    cy = py0 + L.head_h / 2
    tracked(d, (px0 + pad_x, cap_center(disp, cy)), "SPECTRAL SWEEP",
            disp, TEXT, L.px(0.78) * 0.2)
    tracked(d, (px1 - pad_x, cap_center(mono, cy)), meta,
            mono, DIM, L.px(0.66) * 0.12, anchor="r")

    # footer hint
    tracked(d, (px0 + pad_x, cap_center(hint_f, py1 - L.hint_h / 2)),
            "ONE MOMENT, THREE SENSORS · DEPTH, INFRARED AND THERMAL",
            hint_f, FAINT, L.px(0.64) * 0.2)

    # ---- stage overlay (RGBA, drawn over the video) ----
    ov = Image.new("RGBA", (L.stage_w, L.stage_h), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    xs = [round(L.stage_w * s) for s in SPLITS]

    glow = Image.new("RGBA", ov.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for x in xs:
        gd.rectangle([x - th, 0, x + th, L.stage_h], fill=DEPTH + (180,))
    ov.alpha_composite(glow.filter(ImageFilter.GaussianBlur(round(12 * L.k))))
    for x in xs:
        od.rectangle([x - th // 2, 0, x + th // 2, L.stage_h], fill=DEPTH + (255,))

    tag_pad = (round(0.5 * 16 * L.k), round(0.16 * 16 * L.k))
    tag_track = L.px(0.6) * 0.18
    tag_gap = round(12 * L.k)
    pill(od, (L.inset, L.inset), "DEPTH", mono_tag, DEPTH, tag_track, tag_pad)
    pill(od, (xs[0] + tag_gap, L.inset), "INFRARED", mono_tag, IR, tag_track, tag_pad)
    pill(od, (xs[1] + tag_gap, L.inset), "THERMAL", mono_tag, THERMAL, tag_track, tag_pad)

    # timecode frame — the digits are redrawn every frame
    tc_track = L.px(0.72) * 0.14
    tc_pad = (round(0.5 * 16 * L.k), round(0.18 * 16 * L.k))
    tw = sum(od.textlength(c, font=mono_tc) + tc_track for c in "00:00.0") - tc_track
    th_ = mono_tc.getbbox("H")[3] - mono_tc.getbbox("H")[1]
    box = (L.stage_w - L.inset - tw - 2 * tc_pad[0], L.stage_h - L.inset - th_ - 2 * tc_pad[1])
    od.rectangle([box[0], box[1], box[0] + tw + 2 * tc_pad[0], box[1] + th_ + 2 * tc_pad[1]],
                 fill=(4, 10, 12, 184), outline=DEPTH + (90,), width=max(1, round(L.k)))
    tc_org = (L.stage_x + box[0] + tc_pad[0],
              L.stage_y + box[1] + tc_pad[1] - mono_tc.getbbox("H")[1])

    # pulsing record dot, prerendered so only its alpha changes per frame
    r = round(3.5 * L.k)
    pad = r * 4
    dot = Image.new("RGBA", (pad * 2, pad * 2), (0, 0, 0, 0))
    dd = ImageDraw.Draw(dot)
    dd.ellipse([pad - r * 2, pad - r * 2, pad + r * 2, pad + r * 2], fill=BAD + (110,))
    dot = dot.filter(ImageFilter.GaussianBlur(r))
    dd = ImageDraw.Draw(dot)
    dd.ellipse([pad - r, pad - r, pad + r, pad + r], fill=BAD + (255,))
    meta_w = sum(d.textlength(c, font=mono) + L.px(0.66) * 0.12 for c in meta)
    dot_org = (round(px1 - pad_x - meta_w - round(0.45 * 16 * L.k) - pad - r),
               round(cy - pad))

    return base, ov, (mono_tc, tc_track, tc_org, dot, dot_org)


# ------------------------------------------------------------------- render
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--width", type=int, default=1280, help="output width (default 1280)")
    ap.add_argument("--crf", type=int, default=21, help="x264 quality (lower = better)")
    args = ap.parse_args()

    print("resolving the Explorer's featured trial")
    clips, meta = hero_clips()
    f = fonts()

    L = Layout(args.width)
    base, ov, (tc_font, tc_track, tc_org, dot, dot_org) = chrome(L, meta, f)
    print(f"canvas {L.w}×{L.h} · stage {L.stage_w}×{L.stage_h}")

    band = L.stage_w // 3
    common = f"fps={FPS},scale={L.stage_w}:{L.stage_h}:flags=lanczos"
    graph = (
        # the page's own CSS filters, per layer
        f"[0:v]{common},eq=contrast=1.10,hue=h=-8,crop={band}:{L.stage_h}:0:0[d];"
        f"[1:v]{common},eq=contrast=1.06:saturation=1.05,crop={band}:{L.stage_h}:{band}:0[i];"
        f"[2:v]{common},eq=contrast=1.06:saturation=1.05,"
        f"crop={L.stage_w - 2 * band}:{L.stage_h}:{2 * band}:0[t];"
        f"[d][i][t]hstack=inputs=3,format=rgb24[out]"
    )
    src = subprocess.Popen(
        ["ffmpeg", "-v", "error",
         *sum((["-i", str(c)] for c in clips), []),
         "-filter_complex", graph, "-map", "[out]",
         "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        stdout=subprocess.PIPE, bufsize=10 ** 8)

    OUT_MP4.parent.mkdir(parents=True, exist_ok=True)
    enc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y",
         "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{L.w}x{L.h}", "-r", str(FPS), "-i", "-",
         "-an", "-c:v", "libx264", "-preset", "slow", "-crf", str(args.crf),
         "-pix_fmt", "yuv420p", "-profile:v", "high", "-g", str(FPS * 2),
         "-movflags", "+faststart", str(OUT_MP4)],
        stdin=subprocess.PIPE)

    stage_bytes = L.stage_w * L.stage_h * 3
    n = 0
    while True:
        buf = src.stdout.read(stage_bytes)
        if len(buf) < stage_bytes:
            break
        t = n / FPS
        canvas = base.copy()
        canvas.paste(Image.frombytes("RGB", (L.stage_w, L.stage_h), buf),
                     (L.stage_x, L.stage_y))
        canvas.paste(ov, (L.stage_x, L.stage_y), ov)

        d = ImageDraw.Draw(canvas)
        tracked(d, tc_org,
                f"{int(t // 60):02d}:{int(t % 60):02d}.{int(t * 10) % 10}",
                tc_font, DEPTH, tc_track)

        # .rec-dot: @keyframes pulse — 1 -> 0.35 -> 1 over 1.1s
        a = 0.35 + 0.65 * (0.5 + 0.5 * math.cos(2 * math.pi * t / 1.1))
        canvas.paste(dot, dot_org, dot.getchannel("A").point(lambda v: round(v * a)))

        enc.stdin.write(canvas.tobytes())
        n += 1
        if n % 200 == 0:
            print(f"  {n} frames · {t:5.1f}s", flush=True)

    enc.stdin.close()
    src.stdout.close()
    if enc.wait() or src.wait():
        sys.exit("ffmpeg failed")

    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "8", "-i", str(OUT_MP4),
                    "-frames:v", "1", "-q:v", "3", str(OUT_POSTER)], check=True)
    print(f"\n{OUT_MP4.relative_to(ROOT)}  "
          f"{OUT_MP4.stat().st_size / 1024 ** 2:.1f} MB · {n / FPS:.1f}s")
    print(f"{OUT_POSTER.relative_to(ROOT)}  "
          f"{OUT_POSTER.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
