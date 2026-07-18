#!/usr/bin/env python3
"""Render a prepared portrait as a self-typing, monochrome ASCII SVG."""

from __future__ import annotations

import argparse
import html
from pathlib import Path

from PIL import Image, ImageEnhance


COLS, ROWS = 100, 53
CELL_W, CELL_H = 8, 15
PAD, TITLE_H, STATUS_H = 20, 30, 30
RAMP = " .`:-=+*cs#%@"
BG, BG_TOP, FRAME = "#0b1018", "#111a27", "#263b55"
TEXT, MUTED, ACCENT = "#d5e2f2", "#8291a5", "#63d8ff"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    return parser.parse_args()


def ascii_rows(source: Path) -> list[str]:
    image = Image.open(source).convert("L")
    image = ImageEnhance.Contrast(image).enhance(1.08)
    image = image.resize((COLS, ROWS), Image.Resampling.LANCZOS)
    pixels = image.load()
    result: list[str] = []
    for row in range(ROWS):
        chars: list[str] = []
        for col in range(COLS):
            luminance = (pixels[col, row] / 255.0) ** 1.15
            if luminance >= 0.82:
                chars.append(" ")
            else:
                index = round((1.0 - luminance) * (len(RAMP) - 1))
                chars.append(RAMP[max(0, min(index, len(RAMP) - 1))])
        result.append("".join(chars))
    return result


def render(rows: list[str]) -> str:
    art_width, art_height = COLS * CELL_W, ROWS * CELL_H
    width = art_width + PAD * 2
    height = TITLE_H + art_height + STATUS_H + PAD
    art_top = TITLE_H + 6
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc" font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace">',
        '<title id="title">Aleksandr Sadov as animated ASCII art</title>',
        '<desc id="desc">A monochrome portrait prints from top to bottom like terminal output.</desc>',
        '<style>@media(prefers-reduced-motion:reduce){animate,animateTransform,set{display:none!important}.cursor{display:none}}</style>',
        f'<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop stop-color="{BG_TOP}"/><stop offset="1" stop-color="{BG}"/></linearGradient></defs>',
        f'<rect width="{width}" height="{height}" rx="12" fill="url(#bg)"/>',
        f'<rect x=".5" y=".5" width="{width-1}" height="{height-1}" rx="12" fill="none" stroke="{FRAME}"/>',
        f'<line x1="0" y1="{TITLE_H}" x2="{width}" y2="{TITLE_H}" stroke="{FRAME}"/>',
    ]
    for index, color in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        parts.append(f'<circle cx="{PAD + index * 16}" cy="15" r="5" fill="{color}"/>')
    parts.append(
        f'<text x="{width / 2}" y="19" fill="{MUTED}" font-size="12" text-anchor="middle">alexsandrrh@github:~$ ./portrait.sh</text>'
    )

    for index, line in enumerate(rows):
        baseline = art_top + index * CELL_H + CELL_H * 0.75
        top = art_top + index * CELL_H
        delay = index * 0.09
        clip_id = f"row-{index}"
        parts.append(
            f'<clipPath id="{clip_id}"><rect x="{PAD}" y="{top:.1f}" width="{art_width}" height="{CELL_H}">'
            f'<animate attributeName="width" from="0" to="{art_width}" begin="{delay:.2f}s" dur=".09s" fill="freeze"/></rect></clipPath>'
        )
        parts.append(
            f'<text xml:space="preserve" x="{PAD}" y="{baseline:.1f}" fill="{TEXT}" font-size="{CELL_H * 0.86:.1f}" textLength="{art_width}" lengthAdjust="spacing" clip-path="url(#{clip_id})">{html.escape(line)}</text>'
        )
        parts.append(
            f'<rect class="cursor" x="{PAD}" y="{top + 1:.1f}" width="{CELL_W}" height="{CELL_H - 2}" fill="{ACCENT}" opacity="0">'
            f'<animate attributeName="x" from="{PAD}" to="{PAD + art_width}" begin="{delay:.2f}s" dur=".09s" fill="freeze"/>'
            f'<set attributeName="opacity" to=".8" begin="{delay:.2f}s"/><set attributeName="opacity" to="0" begin="{delay + .09:.2f}s"/></rect>'
        )

    separator = TITLE_H + art_height + 7
    status_y = separator + 20
    parts.extend(
        [
            f'<line x1="0" y1="{separator}" x2="{width}" y2="{separator}" stroke="{FRAME}"/>',
            f'<text x="{PAD}" y="{status_y}" fill="{MUTED}" font-size="13">alexsandrrh@github:~$ whoami <tspan fill="{TEXT}">Aleksandr Sadov</tspan></text>',
            f'<rect x="{PAD + 276}" y="{status_y - 12}" width="8" height="14" fill="{ACCENT}"><animate attributeName="opacity" values="1;1;0;0" keyTimes="0;.5;.51;1" dur="1s" repeatCount="indefinite"/></rect>',
            "</svg>",
        ]
    )
    return "".join(parts)


def main() -> None:
    args = parse_args()
    args.output.write_text(render(ascii_rows(args.input)), encoding="utf-8")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()

