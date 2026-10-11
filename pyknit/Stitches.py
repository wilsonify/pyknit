"""Offline helpers that generate the PNG stitch symbols shipped in ``pyknit/symbols/``.

These are developer utilities for regenerating symbol artwork, not runtime
chart rendering: both write image files to caller-provided ``fname`` paths
(plus a suffix) and return the paths written.
"""

import os

from PIL import Image, ImageDraw


def box(fname, cell_width, cell_height, stitch_width):
    """Generate a plain box symbol, writing ``fname + ".png"``."""
    if not fname:
        raise ValueError("fname must be a non-empty output path")
    chart_image = Image.new("RGB", (cell_width * stitch_width, cell_height), "#ffffff")
    draw = ImageDraw.Draw(chart_image)
    draw.rectangle(((0, 0), (cell_width * stitch_width - 1, cell_height - 1)), fill="white", outline="black")

    out = fname + ".png"
    parent = os.path.dirname(out)
    if parent:
        os.makedirs(parent, exist_ok=True)
    chart_image.save(out)
    return out


def cable(fname, cell_width, cell_height, front_sts, back_sts, purl=False):
    stitch_width = front_sts + back_sts
    chart_image = Image.new("RGB", (cell_width * stitch_width, cell_height), "#ffffff")

    # draw some gridlines
    draw = ImageDraw.Draw(chart_image)
    # Border
    draw.rectangle(
        ((0, 0), (stitch_width * cell_width, cell_height)),
        fill="white",
        outline="black",
    )
    # Back stitches
    back_fill = "black" if purl else "white"
    draw.polygon(
        (
            (0, 0),
            (back_sts * cell_width, 0),
            (stitch_width * cell_width, cell_height),
            (front_sts * cell_width, cell_height),
        ),
        fill=back_fill,
        outline="black",
    )
    draw.polygon(
        (
            (back_sts * cell_width, 0),
            (stitch_width * cell_width, 0),
            (front_sts * cell_width, cell_height),
            (0, cell_height),
        ),
        fill="white",
        outline="black",
    )

    if not fname:
        raise ValueError("fname must be a non-empty output path")
    right = fname + "R.png"
    left = fname + "L.png"
    parent = os.path.dirname(right)
    if parent:
        os.makedirs(parent, exist_ok=True)
    chart_image.save(right)
    flipped = chart_image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    flipped.save(left)
    return [right, left]


def main():
    cable("symbols/cable", 50, 50, 2, 2)


if __name__ == "__main__":
    main()
