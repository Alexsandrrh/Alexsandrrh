#!/usr/bin/env python3
"""Render contribution JSON as an accessible animated calendar SVG."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
from pathlib import Path


CELL, GAP, STEP = 12, 3, 15
PAD, LABEL_WIDTH, TOP_LABEL, TITLE_HEIGHT = 22, 30, 20, 30
PALETTE = ("#182334", "#173f3a", "#167052", "#1fa774", "#54e6a1")
BG, BG_TOP, FRAME = "#0b1018", "#111a27", "#263b55"
TEXT, MUTED, ACCENT, GOLD = "#d5e2f2", "#8291a5", "#63d8ff", "#f4c95d"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, nargs="?", default=Path("data/contributions.json"))
    parser.add_argument("output", type=Path, nargs="?", default=Path("contrib-heatmap.svg"))
    return parser.parse_args()


def level(count: int) -> int:
    if count == 0:
        return 0
    if count <= 2:
        return 1
    if count <= 5:
        return 2
    if count <= 9:
        return 3
    return 4


def grid(days: list[dict[str, object]]) -> list[list[dict[str, object] | None]]:
    first = dt.date.fromisoformat(str(days[0]["date"]))
    lead = (first.weekday() + 1) % 7
    cells: list[dict[str, object] | None] = [None] * lead + days
    cells.extend([None] * ((7 - len(cells) % 7) % 7))
    return [cells[index : index + 7] for index in range(0, len(cells), 7)]


def render(data: dict[str, object]) -> str:
    columns = grid(data["days"])
    art_width, art_height = len(columns) * STEP, 7 * STEP
    width = PAD * 2 + LABEL_WIDTH + art_width
    stats_height = 88
    height = TITLE_HEIGHT + TOP_LABEL + art_height + stats_height + PAD
    grid_left, grid_top = PAD + LABEL_WIDTH, TITLE_HEIGHT + TOP_LABEL
    username = html.escape(str(data["username"]))

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc" font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace">',
        f'<title id="title">{username} GitHub contribution calendar</title>',
        f'<desc id="desc">{data["total_contributions"]} public contributions in the displayed year.</desc>',
        '<style>.cell{opacity:0;animation:reveal .42s cubic-bezier(.2,.8,.2,1) both}@keyframes reveal{from{opacity:0;transform:translateY(-6px)}to{opacity:1;transform:translateY(0)}}@media(prefers-reduced-motion:reduce){.cell{opacity:1;animation:none}}</style>',
        f'<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop stop-color="{BG_TOP}"/><stop offset="1" stop-color="{BG}"/></linearGradient></defs>',
        f'<rect width="{width}" height="{height}" rx="12" fill="url(#bg)"/>',
        f'<rect x=".5" y=".5" width="{width-1}" height="{height-1}" rx="12" fill="none" stroke="{FRAME}"/>',
        f'<line x1="0" y1="{TITLE_HEIGHT}" x2="{width}" y2="{TITLE_HEIGHT}" stroke="{FRAME}"/>',
    ]
    for index, color in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        parts.append(f'<circle cx="{PAD + index * 16}" cy="15" r="5" fill="{color}"/>')
    parts.append(
        f'<text x="{width / 2}" y="19" fill="{MUTED}" font-size="12" text-anchor="middle">alexsandrrh@github:~/contributions --graph</text>'
    )

    seen_months: set[tuple[int, int]] = set()
    for column_index, column in enumerate(columns):
        real_cells = [cell for cell in column if cell]
        if real_cells:
            date = dt.date.fromisoformat(str(real_cells[0]["date"]))
            key = (date.year, date.month)
            if key not in seen_months and date.day <= 7:
                seen_months.add(key)
                parts.append(
                    f'<text x="{grid_left + column_index * STEP}" y="44" fill="{MUTED}" font-size="10">{date.strftime("%b")}</text>'
                )
    for row, label in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        parts.append(
            f'<text x="{PAD}" y="{grid_top + row * STEP + 9}" fill="{MUTED}" font-size="9">{label}</text>'
        )

    for column_index, column in enumerate(columns):
        for row_index, day in enumerate(column):
            if day is None:
                continue
            count = int(day["count"])
            delay = column_index * 0.018 + row_index * 0.04
            label = html.escape(f'{day["date"]}: {count} contribution' + ("s" if count != 1 else ""))
            parts.append(
                f'<rect class="cell" x="{grid_left + column_index * STEP}" y="{grid_top + row_index * STEP}" width="{CELL}" height="{CELL}" rx="2.5" fill="{PALETTE[level(count)]}" style="animation-delay:{delay:.3f}s"><title>{label}</title></rect>'
            )

    legend_y = grid_top + art_height + 7
    legend_x = width - PAD - 112
    parts.append(f'<text x="{legend_x}" y="{legend_y + 9}" fill="{MUTED}" font-size="10" text-anchor="end">Less</text>')
    x = legend_x + 8
    for color in PALETTE:
        parts.append(f'<rect x="{x}" y="{legend_y}" width="11" height="11" rx="2" fill="{color}"/>')
        x += 14
    parts.append(f'<text x="{x + 3}" y="{legend_y + 9}" fill="{MUTED}" font-size="10">More</text>')

    separator = legend_y + 27
    parts.append(f'<line x1="0" y1="{separator}" x2="{width}" y2="{separator}" stroke="{FRAME}"/>')
    current = data["current_streak"]["length"]
    longest = data["longest_streak"]["length"]
    best = data["best_day"]
    parts.extend(
        [
            f'<text x="{PAD}" y="{separator + 24}" fill="{TEXT}" font-size="13"><tspan fill="{ACCENT}" font-weight="700">{data["total_contributions"]}</tspan><tspan fill="{MUTED}"> contributions in the last year</tspan></text>',
            f'<text x="{width - PAD}" y="{separator + 24}" fill="{MUTED}" font-size="11" text-anchor="end">{data["range"]["start"]} → {data["range"]["end"]}</text>',
            f'<text x="{PAD}" y="{separator + 48}" fill="{MUTED}" font-size="12">current <tspan fill="{ACCENT}" font-weight="700">{current} days</tspan> · longest <tspan fill="{ACCENT}" font-weight="700">{longest} days</tspan></text>',
            f'<text x="{width - PAD}" y="{separator + 48}" fill="{MUTED}" font-size="11" text-anchor="end">best day <tspan fill="{GOLD}" font-weight="700">{best["count"]}</tspan> on {best["date"]}</text>',
            "</svg>",
        ]
    )
    return "".join(parts)


def main() -> None:
    args = parse_args()
    data = json.loads(args.input.read_text(encoding="utf-8"))
    args.output.write_text(render(data), encoding="utf-8")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()

