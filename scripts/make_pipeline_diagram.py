#!/usr/bin/env python3
"""Draw the VibeFinder 2.0 pipeline diagram used on the slide deck.

The picture is generated with Pillow so it can be rebuilt without a browser or
a Mermaid toolchain:

    python scripts/make_pipeline_diagram.py

Output: assets/pipeline.png (2562 x 1250, the aspect ratio the deck expects).
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 2562, 1250
MARGIN = 79
BOX_W, BOX_GAP, BOX_TOP, BOX_H = 288, 65, 327, 166
STEP = BOX_W + BOX_GAP

INK = (18, 35, 46)
MUTED = (107, 124, 136)
RED = (179, 38, 30)
BAR = (244, 246, 247)

FILLS = {
    "neutral": (244, 246, 247),
    "guard": (255, 244, 230),
    "core": (232, 240, 254),
    "out": (230, 244, 234),
}
STROKES = {
    "neutral": None,
    "guard": (217, 130, 43),
    "core": (31, 78, 121),
    "out": (15, 118, 110),
}

FONT_DIR = Path("/usr/share/fonts/google-carlito-fonts")
FONT_FILES = {
    ("regular", False): "Carlito-Regular.ttf",
    ("regular", True): "Carlito-Bold.ttf",
    ("italic", False): "Carlito-Italic.ttf",
    ("italic", True): "Carlito-BoldItalic.ttf",
}

# name, kind, title, detail lines
STAGES = [
    ("request", "neutral", "Request", ["something chill", "for studying"]),
    ("parser", "guard", "Parser", ["rule-based lexicon", "no model involved"]),
    ("retrieve", "core", "Context retriever", ["custom notes", "study · gym · rainy"]),
    ("rank", "core", "Ranker", ["Module 3 scorer", "genre, mood, energy, tempo"]),
    ("explain", "core", "Explainer", ["writes the reason", "stub or Gemini"]),
    ("verify", "guard", "Verifier", ["numbers + names", "vs the song's row"]),
    ("answer", "out", "Answer", ["with an audit line", "support 1.00"]),
]


def font(style: str, bold: bool, size: int) -> ImageFont.FreeTypeFont:
    path = FONT_DIR / FONT_FILES[(style, bold)]
    if not path.exists():
        path = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    return ImageFont.truetype(str(path), size)


def centre(draw: ImageDraw.ImageDraw, text: str, fnt, x: int, y: int, fill) -> None:
    draw.text((x, y), text, font=fnt, fill=fill, anchor="mm")


def dashed(draw: ImageDraw.ImageDraw, a, b, fill, width=3, dash=14, gap=10) -> None:
    (x0, y0), (x1, y1) = a, b
    length = max(abs(x1 - x0), abs(y1 - y0))
    if length == 0:
        return
    ux, uy = (x1 - x0) / length, (y1 - y0) / length
    pos = 0.0
    while pos < length:
        end = min(pos + dash, length)
        draw.line(
            [
                (x0 + ux * pos, y0 + uy * pos),
                (x0 + ux * end, y0 + uy * end),
            ],
            fill=fill,
            width=width,
        )
        pos = end + gap


def box_x(index: int) -> int:
    return MARGIN + index * STEP


def draw_stage(draw: ImageDraw.ImageDraw, index: int, kind: str, title: str, lines) -> None:
    x = box_x(index)
    fill = FILLS[kind]
    stroke = STROKES[kind]
    draw.rounded_rectangle(
        [x, BOX_TOP, x + BOX_W, BOX_TOP + BOX_H],
        radius=14,
        fill=fill,
        outline=stroke,
        width=3,
    )
    cx = x + BOX_W // 2
    centre(draw, title, font("regular", True, 22), cx, BOX_TOP + 52, INK)
    for i, line in enumerate(lines):
        centre(draw, line, font("regular", False, 15), cx, BOX_TOP + 92 + i * 26, INK)


def build() -> Image.Image:
    img = Image.new("RGB", (W, H), "white")
    draw = ImageDraw.Draw(img)

    draw.text(
        (MARGIN, 74),
        "VibeFinder 2.0: every explanation is checked before you see it",
        font=font("regular", True, 34),
        fill=INK,
        anchor="lm",
    )
    draw.text(
        (MARGIN, 126),
        "The song ranking is unchanged. What is new is that the explanation must pass a check "
        "against the song's real information.",
        font=font("regular", False, 20),
        fill=INK,
        anchor="lm",
    )

    # connectors between the stages
    for i in range(len(STAGES) - 1):
        y = BOX_TOP + BOX_H // 2
        draw.line([(box_x(i) + BOX_W, y), (box_x(i + 1), y)], fill=INK, width=3)

    for i, (_, kind, title, lines) in enumerate(STAGES):
        draw_stage(draw, i, kind, title, lines)

    # fact sheet feeding the explainer
    explain_cx = box_x(4) + BOX_W // 2
    draw.line([(explain_cx, BOX_TOP + BOX_H), (explain_cx, 641)], fill=INK, width=3)
    draw.rounded_rectangle([explain_cx - 191, 641, explain_cx + 191, 763], radius=14, fill=BAR)
    centre(draw, "Fact sheet", font("regular", True, 20), explain_cx, 676, INK)
    centre(draw, "title, genre, mood, energy,", font("regular", False, 15), explain_cx, 708, INK)
    centre(draw, "tempo, decade, score", font("regular", False, 15), explain_cx, 734, INK)

    # decline path out of the parser
    parser_cx = box_x(1) + BOX_W // 2
    draw.line([(parser_cx, BOX_TOP + BOX_H), (parser_cx, 687)], fill=RED, width=3)
    centre(draw, "nothing recognised →", font("regular", True, 17), parser_cx, 706, INK)
    centre(draw, "decline, no model call", font("regular", True, 17), parser_cx, 734, INK)

    # retry loop from the verifier back to the explainer
    verify_cx = box_x(5) + BOX_W // 2
    centre(
        draw,
        "below 0.80 support → retry once, stricter prompt",
        font("regular", True, 17),
        (explain_cx + verify_cx) // 2,
        190,
        RED,
    )
    centre(
        draw,
        "a second failure is returned with a caveat, not hidden",
        font("regular", True, 17),
        (explain_cx + verify_cx) // 2,
        222,
        INK,
    )
    dashed(draw, (explain_cx, 254), (verify_cx, 254), RED)
    dashed(draw, (explain_cx, 254), (explain_cx, BOX_TOP), RED)
    dashed(draw, (verify_cx, 254), (verify_cx, BOX_TOP), RED)

    # footer bars
    for x0, x1, headline, detail in (
        (
            MARGIN,
            1204,
            "Every attempt is written to a JSONL trace",
            "parse → retrieve → rank → verify, including the one that failed",
        ),
        (
            1282,
            2485,
            "harness.py: 16 queries × 2 modes",
            "explain-only 5/16 → verified 16/16",
        ),
    ):
        draw.rounded_rectangle([x0, 1079, x1, 1182], radius=14, fill=BAR)
        cx = (x0 + x1) // 2
        centre(draw, headline, font("regular", True, 19), cx, 1112, INK)
        centre(draw, detail, font("regular", False, 16), cx, 1150, INK)

    return img


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "assets" / "pipeline.png",
    )
    args = parser.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    build().save(args.out, "PNG", optimize=True)
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
