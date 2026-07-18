#!/usr/bin/env python3
"""Isolate and tone a portrait for the ASCII renderer."""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageFilter
from rembg import remove


TARGET_SIZE = (1200, 636)  # same aspect ratio as the 100 x 53 ASCII grid


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="Source portrait")
    parser.add_argument("output", type=Path, help="Prepared grayscale PNG")
    return parser.parse_args()


def prepare(source: Path) -> Image.Image:
    cutout = remove(Image.open(source).convert("RGBA"))
    alpha = cutout.getchannel("A")
    bbox = alpha.getbbox()
    if bbox is None:
        raise ValueError("Background removal produced an empty image")

    subject = cutout.crop(bbox)
    max_width = int(TARGET_SIZE[0] * 0.76)
    max_height = int(TARGET_SIZE[1] * 0.96)
    scale = min(max_width / subject.width, max_height / subject.height)
    subject = subject.resize(
        (max(1, round(subject.width * scale)), max(1, round(subject.height * scale))),
        Image.Resampling.LANCZOS,
    )

    rgba = Image.new("RGBA", TARGET_SIZE, (255, 255, 255, 0))
    x = (TARGET_SIZE[0] - subject.width) // 2
    y = TARGET_SIZE[1] - subject.height
    rgba.alpha_composite(subject, (x, y))

    rgb = np.asarray(rgba.convert("RGB"))
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    gray = cv2.createCLAHE(clipLimit=2.4, tileGridSize=(8, 8)).apply(gray)
    gray = cv2.convertScaleAbs(gray, alpha=1.04, beta=15)

    mask = np.asarray(rgba.getchannel("A").filter(ImageFilter.GaussianBlur(1.0))) / 255.0
    composed = gray.astype(np.float32) * mask + 255.0 * (1.0 - mask)
    return Image.fromarray(np.clip(composed, 0, 255).astype(np.uint8), mode="L")


def main() -> None:
    args = parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    prepare(args.input).save(args.output)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()

