#!/usr/bin/env python3
"""Build Aleksandr's animated neofetch-style profile card."""

from __future__ import annotations

import argparse
import html
from pathlib import Path


WIDTH, HEIGHT = 480, 376
BG, BG_TOP, FRAME = "#0b1018", "#111a27", "#263b55"
TEXT, MUTED = "#d5e2f2", "#8291a5"
KEY, SECTION, GREEN, ACCENT = "#f4a261", "#63d8ff", "#62d98b", "#b48cff"

ROWS = [
    ("host", ""),
    ("kv", "Role", "Senior Product Engineer"),
    ("kv", "Experience", "6+ years in product engineering"),
    ("kv", "Focus", "Frontend systems · AI agents"),
    ("gap", ""),
    ("section", "Stack"),
    ("kv", "Frontend", "React · TypeScript · Next.js"),
    ("kv", "Data / UI", "TanStack · Tailwind CSS"),
    ("kv", "Runtime", "Node.js · Bun"),
    ("kv", "Backend", "NestJS · REST APIs"),
    ("kv", "AI", "LangChain · LangGraph"),
    ("gap", ""),
    ("section", "How I build"),
    ("bullet", "Product-minded engineering"),
    ("bullet", "Scalable frontend architecture"),
    ("bullet", "Typed contracts · reusable UI"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    return parser.parse_args()


def reveal(content: str, index: int) -> str:
    delay = 0.12 + index * 0.055
    return (
        f'<g opacity="1">{content}'
        f'<animate attributeName="opacity" from="0" to="1" begin="{delay:.2f}s" dur=".35s" fill="freeze"/>'
        f'<animateTransform attributeName="transform" type="translate" from="0 5" to="0 0" begin="{delay:.2f}s" dur=".35s" fill="freeze"/>'
        "</g>"
    )


def render() -> str:
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-labelledby="title desc" font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace">',
        '<title id="title">Aleksandr Sadov profile card</title>',
        '<desc id="desc">A terminal-style summary of Aleksandr’s role, experience, stack, and engineering approach.</desc>',
        '<style>@media(prefers-reduced-motion:reduce){animate,animateTransform{display:none!important}}</style>',
        f'<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop stop-color="{BG_TOP}"/><stop offset="1" stop-color="{BG}"/></linearGradient></defs>',
        f'<rect width="{WIDTH}" height="{HEIGHT}" rx="12" fill="url(#bg)"/>',
        f'<rect x=".5" y=".5" width="{WIDTH-1}" height="{HEIGHT-1}" rx="12" fill="none" stroke="{FRAME}"/>',
        f'<line x1="0" y1="30" x2="{WIDTH}" y2="30" stroke="{FRAME}"/>',
    ]
    for index, color in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        parts.append(f'<circle cx="{20 + index * 16}" cy="15" r="5" fill="{color}"/>')
    parts.append(
        f'<text x="{WIDTH / 2}" y="19" fill="{MUTED}" font-size="12" text-anchor="middle">alexsandrrh@github:~$ neofetch</text>'
    )

    y, visible_index = 58.0, 0
    for kind, *values in ROWS:
        if kind == "gap":
            y += 8
            continue
        if kind == "host":
            inner = (
                f'<text x="20" y="{y}" font-size="14" font-weight="700"><tspan fill="{GREEN}">alexsandrrh</tspan><tspan fill="{MUTED}">@</tspan><tspan fill="{ACCENT}">github</tspan></text>'
                f'<line x1="172" y1="{y - 4}" x2="460" y2="{y - 4}" stroke="{FRAME}"/>'
            )
        elif kind == "section":
            label = html.escape(values[0])
            inner = (
                f'<text x="20" y="{y}" fill="{SECTION}" font-size="12" font-weight="700">— {label}</text>'
                f'<line x1="{40 + len(label) * 8}" y1="{y - 4}" x2="460" y2="{y - 4}" stroke="{FRAME}"/>'
            )
        elif kind == "kv":
            key, value = map(html.escape, values)
            inner = (
                f'<text x="20" y="{y}" fill="{KEY}" font-size="11.7" font-weight="700">{key}</text>'
                f'<text x="112" y="{y}" fill="{TEXT}" font-size="11.7">{value}</text>'
            )
        else:
            value = html.escape(values[0])
            inner = (
                f'<circle cx="23" cy="{y - 4}" r="2.5" fill="{GREEN}"/>'
                f'<text x="34" y="{y}" fill="{TEXT}" font-size="11.7">{value}</text>'
            )
        parts.append(reveal(inner, visible_index))
        visible_index += 1
        y += 19.5
    parts.append("</svg>")
    return "".join(parts)


def main() -> None:
    args = parse_args()
    args.output.write_text(render(), encoding="utf-8")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
