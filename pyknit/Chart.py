# Copyright (C) 2021 Terri Oda
# SPDX-License-Identifier: GPL-2.0-or-later

# !python
"""
pyKnit: a set of tools for knitters to do math, create charts, customise
patterns and more

pyKnit.Chart: chart and pattern parsing functions
"""

import base64
import os.path
import re
from typing import Dict, List, Optional
from xml.sax.saxutils import escape as _xml_escape

from PIL import Image, ImageDraw, ImageFont


class Stitch:
    """A class to represent a stitch. Optionally, a preferred legend can be passed in."""

    def __init__(
        self,
        instruction: str,
        symbol: str,
        width: int,
        category: str = "",
        direction: str = "neutral",
        consumes: int = 1,
        produces: int = 1,
    ):
        self.instruction = instruction
        self.symbol = symbol
        self.width = width
        self.category = category
        self.direction = direction
        self.consumes = consumes
        self.produces = produces

    def __repr__(self):
        return f"'{self.symbol}'"

    def __str__(self):
        return f"{self.instruction}"

    def __eq__(self, other):
        if isinstance(other, Stitch):
            return self.__dict__ == other.__dict__
        return False


Legend = Dict[str, Stitch]
PatternRow = List[Stitch]
Pattern = List[PatternRow]

# chart cell size in pixels, shared by plot_chart and render_chart_svg
cell_height = 50
cell_width = 50

symbol_dir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "symbols",
)

stitch_legend = {  # Default legend. Incomplete for now.
    "k": Stitch(
        instruction="knit",
        symbol=" ",
        width=1,
        category="knit",
    ),
    "kfb": Stitch(
        instruction="knit front and back",
        symbol="V",
        width=1,
        category="increase",
        consumes=1,
        produces=2,
    ),
    "k2tog": Stitch(
        instruction="knit two together",
        symbol="/",
        width=1,
        category="decrease",
        direction="right",
        consumes=2,
        produces=1,
    ),
    "yo": Stitch(
        instruction="yarn over",
        symbol="O",
        width=1,
        category="yarn-over",
        consumes=0,
        produces=1,
    ),
    "p": Stitch(
        instruction="purl",
        symbol=".",
        width=1,
        category="purl",
    ),
    "ssk": Stitch(
        instruction="slip slip knit",  # left-leaning decrease
        symbol="\\",
        width=1,
        category="decrease",
        direction="left",
        consumes=2,
        produces=1,
    ),
    "C1-1L": Stitch(
        instruction="sl 1st onto cn, with cn in front, k1, k1 from cn",
        symbol=os.path.join(symbol_dir, "C1-1L.png"),
        width=2,
        category="cable",
        direction="left",
        consumes=2,
        produces=2,
    ),
    "C1-1R": Stitch(
        instruction="sl 1st onto cn, with cn in back, k1, k1 from cn",
        symbol=os.path.join(symbol_dir, "C1-1R.png"),
        width=2,
        category="cable",
        direction="right",
        consumes=2,
        produces=2,
    ),
    "C1-1PL": Stitch(
        instruction="sl 1st onto cn, with cn in front, p1, k1 from cn",
        symbol=os.path.join(symbol_dir, "C1-1PL.png"),
        width=2,
        category="cable",
        direction="left",
        consumes=2,
        produces=2,
    ),
    "C1-1PR": Stitch(
        instruction="sl 1st onto cn, with cn in back, p1, k1 from cn",
        symbol=os.path.join(symbol_dir, "C1-1PR.png"),
        width=2,
        category="cable",
        direction="right",
        consumes=2,
        produces=2,
    ),
    "C2-1L": Stitch(
        instruction="sl 2st onto cn, with cn in front, k1, k2 from cn",
        symbol=os.path.join(symbol_dir, "C2-1L.png"),
        width=3,
        category="cable",
        direction="left",
        consumes=3,
        produces=3,
    ),
    "C2-1R": Stitch(
        instruction="sl 2st onto cn, with cn in back, k1, k2 from cn",
        symbol=os.path.join(symbol_dir, "C2-1R.png"),
        width=3,
        category="cable",
        direction="right",
        consumes=3,
        produces=3,
    ),
    "C2-1PL": Stitch(
        instruction="sl 2st onto cn, with cn in front, p1, k2 from cn",
        symbol=os.path.join(symbol_dir, "C2-1PL.png"),
        width=3,
        category="cable",
        direction="left",
        consumes=3,
        produces=3,
    ),
    "C2-1PR": Stitch(
        instruction="sl 2st onto cn, with cn in back, p1, k2 from cn",
        symbol=os.path.join(symbol_dir, "C2-1PR.png"),
        width=3,
        category="cable",
        direction="right",
        consumes=3,
        produces=3,
    ),
    "C2-2L": Stitch(
        instruction="sl 2st onto cn, with cn in front, k2, k2 from cn",
        symbol=os.path.join(symbol_dir, "C2-2L.png"),
        width=4,
        category="cable",
        direction="left",
        consumes=4,
        produces=4,
    ),
    "C2-2R": Stitch(
        instruction="sl 2st onto cn, with cn in back, k2, k2 from cn",
        symbol=os.path.join(symbol_dir, "C2-2R.png"),
        width=4,
        category="cable",
        direction="right",
        consumes=4,
        produces=4,
    ),
    "C2-2PL": Stitch(
        instruction="sl 2st onto cn, with cn in front, p2, k2 from cn",
        symbol=os.path.join(symbol_dir, "C2-2PL.png"),
        width=4,
        category="cable",
        direction="left",
        consumes=4,
        produces=4,
    ),
    "C2-2PR": Stitch(
        instruction="sl 2st onto cn, with cn in back, p2, k2 from cn",
        symbol=os.path.join(symbol_dir, "C2-2PR.png"),
        width=4,
        category="cable",
        direction="right",
        consumes=4,
        produces=4,
    ),
    "C3-3L": Stitch(
        instruction="sl 3st onto cn, with cn in front, k3, k3 from cn",
        symbol=os.path.join(symbol_dir, "C3-3L.png"),
        width=6,
        category="cable",
        direction="left",
        consumes=6,
        produces=6,
    ),
    "C3-3R": Stitch(
        instruction="sl 3st onto cn, with cn in back, k3, k3 from cn",
        symbol=os.path.join(symbol_dir, "C3-3R.png"),
        width=6,
        category="cable",
        direction="right",
        consumes=6,
        produces=6,
    ),
    "C3-3PL": Stitch(
        instruction="sl 3st onto cn, with cn in front, p3, k3 from cn",
        symbol=os.path.join(symbol_dir, "C3-3PL.png"),
        width=6,
        category="cable",
        direction="left",
        consumes=6,
        produces=6,
    ),
    "C3-3PR": Stitch(
        instruction="sl 3st onto cn, with cn in back, p3, k3 from cn",
        symbol=os.path.join(symbol_dir, "C3-3PR.png"),
        width=6,
        category="cable",
        direction="right",
        consumes=6,
        produces=6,
    ),
    "C4-4L": Stitch(
        instruction="sl 4st onto cn, with cn in front, k4, k4 from cn",
        symbol=os.path.join(symbol_dir, "C4-4L.png"),
        width=8,
        category="cable",
        direction="left",
        consumes=8,
        produces=8,
    ),
    "C4-4R": Stitch(
        instruction="sl 4st onto cn, with cn in back, k4, k4 from cn",
        symbol=os.path.join(symbol_dir, "C4-4R.png"),
        width=8,
        category="cable",
        direction="right",
        consumes=8,
        produces=8,
    ),
    "C4-4PL": Stitch(
        instruction="sl 4st onto cn, with cn in front, p4, k4 from cn",
        symbol=os.path.join(symbol_dir, "C4-4PL.png"),
        width=8,
        category="cable",
        direction="left",
        consumes=8,
        produces=8,
    ),
    "C4-4PR": Stitch(
        instruction="sl 4st onto cn, with cn in back, p4, k4 from cn",
        symbol=os.path.join(symbol_dir, "C4-4PR.png"),
        width=8,
        category="cable",
        direction="right",
        consumes=8,
        produces=8,
    ),
}

stitch_legend_japanese = {  # Legend for Japanese Symbols. Only a portion of available symbols provided.
    "NA": Stitch(
        instruction="no stitch",
        symbol=os.path.join(symbol_dir, "japanese", "no-stitch.png"),
        width=1,
        category="other",
    ),
    "k": Stitch(
        instruction="knit",
        symbol=os.path.join(symbol_dir, "japanese", "box.png"),
        width=1,
        category="knit",
    ),
    "ktbl": Stitch(
        instruction="knit through the back loop",
        symbol=os.path.join(symbol_dir, "japanese", "ktbl.png"),
        width=1,
        category="knit",
    ),
    "k2tog": Stitch(
        instruction="knit two together",
        symbol=os.path.join(symbol_dir, "japanese", "k2tog.png"),
        width=1,
        category="decrease",
        direction="right",
        consumes=2,
        produces=1,
    ),
    "k3tog": Stitch(
        instruction="knit three together",
        symbol=os.path.join(symbol_dir, "japanese", "k3tog.png"),
        width=1,
        category="decrease",
        direction="right",
        consumes=3,
        produces=1,
    ),
    "k4tog": Stitch(
        instruction="knit four together",
        symbol=os.path.join(symbol_dir, "japanese", "k4tog.png"),
        width=1,
        category="decrease",
        direction="right",
        consumes=4,
        produces=1,
    ),
    "yo": Stitch(
        instruction="yarn over",
        symbol=os.path.join(symbol_dir, "japanese", "yarn_over.png"),
        width=1,
        category="yarn-over",
        consumes=0,
        produces=1,
    ),
    "p": Stitch(
        instruction="purl",
        symbol=os.path.join(symbol_dir, "japanese", "purl.png"),
        width=1,
        category="purl",
    ),
    "ptbl": Stitch(
        instruction="purl through the back loop",
        symbol=os.path.join(symbol_dir, "japanese", "ptbl.png"),
        width=1,
        category="purl",
    ),
    "p2tog": Stitch(
        instruction="purl two together",
        symbol=os.path.join(symbol_dir, "japanese", "p2tog.png"),
        width=1,
        category="decrease",
        direction="right",
        consumes=2,
        produces=1,
    ),
    "ssk": Stitch(
        instruction="[slip 1 kwise] twice, return both back to LN, k2togtbl",
        symbol=os.path.join(symbol_dir, "japanese", "ssk.png"),
        width=1,  # left leaning decrease
        category="decrease",
        direction="left",
        consumes=2,
        produces=1,
    ),
    "skp": Stitch(
        instruction="slip knit pass over (same as ssk)",
        symbol=os.path.join(symbol_dir, "japanese", "ssk.png"),
        width=1,  # left leaning decrease
        category="decrease",
        direction="left",
        consumes=2,
        produces=1,
    ),
    "ssp": Stitch(
        instruction="[slip 1 kwise] twice, slip 2 stitches back to LN, then p2togtbl",
        symbol=os.path.join(symbol_dir, "japanese", "ssp.png"),
        width=1,
        category="decrease",
        direction="left",
        consumes=2,
        produces=1,
    ),
    "sk2togp": Stitch(
        instruction="slip 1 kwise, k2tog, psso",
        symbol=os.path.join(symbol_dir, "japanese", "sk2togp.png"),
        width=1,
        category="decrease",
        direction="left",
        consumes=3,
        produces=1,
    ),
    "sl2kp2": Stitch(
        instruction="sl 2 sts together kwise, k1, psso",
        symbol=os.path.join(symbol_dir, "japanese", "sl2kp2.png"),
        width=1,
        category="decrease",
        direction="left",
        consumes=3,
        produces=1,
    ),
    "s3kp3": Stitch(
        instruction="[slip 1 kwise] 3 times, k1, psso",
        symbol=os.path.join(symbol_dir, "japanese", "sl3kp3.png"),
        width=1,
        category="decrease",
        direction="left",
        consumes=4,
        produces=1,
    ),
    "C1-1L": Stitch(
        instruction=(
            "With RN, go behind first st and k second st without removing; "
            "k first st, slip both off LN"
        ),
        symbol=os.path.join(symbol_dir, "japanese", "C1-1L.png"),
        width=2,
        category="cable",
        direction="left",
        consumes=2,
        produces=2,
    ),
    "C1-1R": Stitch(
        instruction=(
            "with RN, go in front of first st and k second st without "
            "removing; k first st, slip both off LN"
        ),
        symbol=os.path.join(symbol_dir, "japanese", "C1-1R.png"),
        width=2,
        category="cable",
        direction="right",
        consumes=2,
        produces=2,
    ),
    "C1-1PL": Stitch(
        instruction=(
            "With RN, go behind first st and p second st without removing; "
            "k first st, slip both off LN"
        ),
        symbol=os.path.join(symbol_dir, "japanese", "C1-1PL.png"),
        width=2,
        category="cable",
        direction="left",
        consumes=2,
        produces=2,
    ),
    "C1-1PR": Stitch(
        instruction=(
            "With RN, go in front of first st and k second st without "
            "removing, p first st, slip both off LN"
        ),
        symbol=os.path.join(symbol_dir, "japanese", "C1-1PR.png"),
        width=2,
        category="cable",
        direction="right",
        consumes=2,
        produces=2,
    ),
    "C4L": Stitch(
        instruction="Place 1 st on CN, hold to front, k3; k1 from CN",
        symbol=os.path.join(symbol_dir, "japanese", "C4L.png"),
        width=4,
        category="cable",
        direction="left",
        consumes=4,
        produces=4,
    ),
    "C4R": Stitch(
        instruction="Place 3 sts on CN, hold to back, k1; k3 from CN",
        symbol=os.path.join(symbol_dir, "japanese", "C4R.png"),
        width=4,
        category="cable",
        direction="right",
        consumes=4,
        produces=4,
    ),
}

# Chart and pattern parsing functions

def parse_row(row: str, legend: Dict[str, Stitch] = stitch_legend) -> List[Stitch]:
    # legend=None allows a mutable parameter here - important for japanese legend option
    # I don't think a set is the right return type, order is important here
    """Parse a written set of knitting instructions and print an array of
    stitches using a legend.  This is a stand in for eventually printing a
    chart.

    >>> parse_row("k4 p4")
    [' ', ' ', ' ', ' ', '.', '.', '.', '.']
    """

    if legend is None:
        legend = stitch_legend
    stitch_array = []
    for section in row.split(" "):

        patterns = [
            r"(C\d-\dP?[F|B|L|R])([0-9]*)",  # cables
            r"([A-Za-z]+[0-9]+[A-Za-z]+)([0-9]*)",  # things like k2tog or m1l
            r"([A-Za-z]+)([0-9]*)",  # things like p4
        ]
        matched_stitch = False
        for pat in patterns:
            result = re.match(pat, section)
            if result and not matched_stitch:
                # only match one pattern per stitch so k2tog doesn't
                # get parsed as k2
                matched_stitch = True
                stitch = result.group(1)
                # set the number or if no number, assume you repeat once
                number = int(result.group(2)) if result.group(2) else 1
                for i in range(0, number):
                    stitch_array.append(legend[stitch])

    return stitch_array


def parse_chart(chart_instructions: str, legend=None) -> Pattern:
    """Parse multi-line knitting instructions into a chart.

    Each line is parsed with :func:`parse_row`.

    >>> parse_chart("k4\\np4")
    [[' ', ' ', ' ', ' '], ['.', '.', '.', '.']]
    """
    if legend is None:
        legend = stitch_legend
    return [parse_row(row, legend) for row in chart_instructions.split("\n")]


def print_row(stitch_array: PatternRow) -> Image:
    """Print a chart from a stitch array"""
    # Set up the image
    cell_height = 50
    cell_width = 50
    chart_image = Image.new(
        "RGB",
        ((cell_width + 1) * sum(st.width for st in stitch_array), cell_height),
        (255, 255, 255),
    )

    # draw some gridlines
    draw = ImageDraw.Draw(chart_image)

    # draw symbol for each cell
    fnt = ImageFont.truetype("Times.ttf", 40)
    position = 0
    for i, stitch in enumerate(stitch_array):
        # for i in range(1, len(stitch_array)):
        position = sum(st.width for st in stitch_array[: i + 1]) * (cell_width + 1)
        draw.line((position, 0) + (position, cell_height), fill=128)

        draw.text(
            (position - (stitch.width * cell_width) / 2, cell_height / 2),
            stitch.symbol,
            font=fnt,
            fill=(255, 255, 255, 255),
            align="center",
            anchor="mm",
        )
    return chart_image


def instruction_to_plot_order(
        input_array: Pattern, vertical_order: str = "bt", horizontal_order: str = "rl"
) -> Pattern:
    """Reorder a pattern for plotting, bottom-to-top and right-to-left by default.

    >>> instruction_to_plot_order(parse_chart("k4\\np4"))
    [['.', '.', '.', '.'], [' ', ' ', ' ', ' ']]
    """
    # input_array = [list(row) for row in pattern.lstrip().rstrip().split("\n")]
    vertical_ordered = (
        list(reversed(input_array)) if vertical_order == "bt" else input_array
    )
    return_array = [
        list(reversed(row)) if horizontal_order == "rl" else row
        for row in vertical_ordered
    ]
    return return_array


def plot_chart(
        stitch_array: Pattern, lr_direction: str = "lr", tb_direction: str = "tb"
) -> Image:
    """Print a chart from a stitch array"""

    # Set up the image
    cell_height = 50
    cell_width = 50

    num_rows = len(stitch_array) if type(stitch_array[0] == list) else 1
    if num_rows <= 0:
        raise ValueError("There must be at least one row in the pattern")
    elif num_rows == 1:
        stitch_array = [
            stitch_array
        ]  # put a single row into a containing list to make the 2D loop work

    longest_row_len = max([sum(st.width for st in row) for row in stitch_array])

    print(f"{num_rows} rows, {longest_row_len} sts wide at max")
    pattern_to_plot = instruction_to_plot_order(
        stitch_array, tb_direction, lr_direction
    )

    # Set up canvas with room for all stitches plus numbers
    chart_image = Image.new(
        "RGB",
        (cell_width * (longest_row_len + 1), cell_height * (num_rows + 1)),
        (255, 255, 255),
    )

    # draw some gridlines
    draw = ImageDraw.Draw(chart_image)

    # draw symbol for each cell
    fnt = ImageFont.truetype("Inkfree.ttf", 35)
    color_st_pattern = r"#[0-9a-fA-F]{6}"

    for st_y, row in enumerate(pattern_to_plot):
        cur_y = (st_y + (1 if tb_direction == "tb" else 0)) * cell_height
        cur_x = 0 if lr_direction == "rl" else cell_width
        for st_x, stitch in enumerate(row):
            # for i in range(1, len(stitch_array)):
            stitch_coloured = re.match(color_st_pattern, stitch.symbol)
            stitch_graphic = stitch.symbol.endswith(".png")

            if (
                    stitch_graphic
            ):  # this is really ugly, fix path to symbols as part of the symbol name?
                with Image.open(stitch.symbol) as sym:
                    chart_image.paste(sym, (cur_x, cur_y))

            else:
                stitch_color = stitch.symbol if stitch_coloured else "white"
                draw.rectangle(
                    (
                        (cur_x, cur_y),
                        (cur_x + stitch.width * cell_width, cur_y + cell_height),
                    ),
                    fill=stitch_color,
                    outline="black",
                )
                if not stitch_coloured:
                    draw.text(
                        (
                            cur_x + (stitch.width * cell_width) / 2,
                            cur_y + cell_height / 2,
                        ),
                        stitch.symbol,
                        font=fnt,
                        fill="blue",
                        align="center",
                        anchor="mm",
                    )
            cur_x += stitch.width * cell_width
    # Row and column numbers
    row_x = (
        3 * cell_width // 2
        if lr_direction == "lr"
        else chart_image.width - 3 * cell_width // 2
    )
    row_y = (
        cell_height // 2
        if tb_direction == "tb"
        else chart_image.height - cell_height // 2
    )
    for i in range(1, longest_row_len + 1):
        draw.text(
            (row_x, row_y),
            str(i),
            fill="black",
            font=fnt,
            align="center",
            anchor="mm",
        )
        row_x = row_x + cell_width * (1 if lr_direction == "lr" else -1)

    col_x = (
        cell_width // 2 if lr_direction == "lr" else chart_image.width - cell_width // 2
    )
    col_y = (
        3 * cell_height // 2
        if tb_direction == "tb"
        else chart_image.height - 3 * cell_height // 2
    )
    for j in range(1, num_rows + 1):
        draw.text(
            (col_x, col_y),
            str(j),
            fill="black",
            font=fnt,
            align="center",
            anchor="mm",
        )
        col_y = col_y + cell_height * (1 if tb_direction == "tb" else -1)

    return chart_image


def _symbol_to_data_uri(symbol: str) -> Optional[str]:
    """Return *symbol* as a base64 data URI, or None if the file is unreadable."""
    mime_by_extension = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
    }
    try:
        with open(symbol, "rb") as image_file:
            payload = base64.b64encode(image_file.read()).decode("ascii")
    except (IOError, OSError):
        return None
    mime = mime_by_extension.get(
        os.path.splitext(symbol)[1].lower(), "image/png"
    )
    return f"data:{mime};base64,{payload}"


def render_chart_svg(
    stitch_array: Pattern, lr_direction: str = "lr", tb_direction: str = "tb"
) -> str:
    """Render a chart as an SVG string.

    Produces the same layout as :func:`plot_chart` (spec 03) using only the
    standard library so charts render where Pillow is unavailable. A single
    :class:`PatternRow` is normalized into a one-row pattern, and the returned
    string is a standalone SVG document with the same canvas dimensions as
    ``plot_chart``.

    >>> from xml.etree.ElementTree import fromstring
    >>> svg = render_chart_svg(parse_chart("k p"))
    >>> svg.startswith("<?xml")
    True
    >>> root = fromstring(svg)
    >>> root.tag
    '{http://www.w3.org/2000/svg}svg'
    >>> root.attrib["width"]
    '150'
    >>> root.attrib["height"]
    '100'
    """
    num_rows = len(stitch_array)
    if num_rows <= 0:
        raise ValueError("There must be at least one row in the pattern")
    if isinstance(stitch_array[0], Stitch):
        # a single row arrives as a flat list of Stitches; wrap it so the
        # 2D loop below always iterates over rows
        stitch_array = [stitch_array]
        num_rows = 1

    longest_row_len = max(sum(st.width for st in row) for row in stitch_array)

    pattern_to_plot = instruction_to_plot_order(
        stitch_array, tb_direction, lr_direction
    )

    canvas_width = cell_width * (longest_row_len + 1)
    canvas_height = cell_height * (num_rows + 1)

    color_st_pattern = re.compile(r"#[0-9a-fA-F]{6}")
    elements = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{canvas_width}" height="{canvas_height}" '
        f'viewBox="0 0 {canvas_width} {canvas_height}">',
    ]

    # Numbers live in a leading stripe (top or bottom for rows, left or right
    # for columns), so the data area is inset by one cell there.
    top = 0 if tb_direction == "bt" else cell_height
    left = 0 if lr_direction == "rl" else cell_width
    bottom = top + cell_height * num_rows
    right = left + cell_width * longest_row_len

    for x in range(left, right + 1, cell_width):
        elements.append(
            f'<line x1="{x}" y1="{top}" x2="{x}" y2="{bottom}" '
            f'stroke="black" stroke-width="1"/>'
        )
    for y in range(top, bottom + 1, cell_height):
        elements.append(
            f'<line x1="{left}" y1="{y}" x2="{right}" y2="{y}" '
            f'stroke="black" stroke-width="1"/>'
        )

    for row_index, row in enumerate(pattern_to_plot):
        cur_y = (row_index + (1 if tb_direction == "tb" else 0)) * cell_height
        cur_x = 0 if lr_direction == "rl" else cell_width
        for stitch in row:
            span = stitch.width * cell_width
            center_x = cur_x + span / 2
            center_y = cur_y + cell_height / 2
            if stitch.symbol.endswith(".png"):
                data_uri = _symbol_to_data_uri(stitch.symbol)
                if data_uri is not None:
                    elements.append(
                        f'<image href="{data_uri}" x="{cur_x}" y="{cur_y}" '
                        f'width="{span}" height="{cell_height}"/>'
                    )
                else:
                    label = os.path.basename(stitch.symbol)
                    elements.append(
                        f'<text x="{center_x}" y="{center_y}" '
                        f'text-anchor="middle" dominant-baseline="central" '
                        f'font-size="14">{_xml_escape(label)}</text>'
                    )
            else:
                colored = color_st_pattern.match(stitch.symbol)
                fill = stitch.symbol if colored else "white"
                elements.append(
                    f'<rect x="{cur_x}" y="{cur_y}" width="{span}" '
                    f'height="{cell_height}" fill="{fill}" stroke="black"/>'
                )
                if not colored:
                    elements.append(
                        f'<text x="{center_x}" y="{center_y}" '
                        f'text-anchor="middle" dominant-baseline="central" '
                        f'font-size="20" fill="blue">'
                        f'{_xml_escape(stitch.symbol)}</text>'
                    )
            cur_x += span

    row_x = (
        3 * cell_width // 2
        if lr_direction == "lr"
        else canvas_width - 3 * cell_width // 2
    )
    row_y = (
        cell_height // 2
        if tb_direction == "tb"
        else canvas_height - cell_height // 2
    )
    for column_number in range(1, longest_row_len + 1):
        elements.append(
            f'<text x="{row_x}" y="{row_y}" text-anchor="middle" '
            f'dominant-baseline="central" font-size="14">'
            f'{column_number}</text>'
        )
        row_x += cell_width * (1 if lr_direction == "lr" else -1)

    column_x = (
        cell_width // 2
        if lr_direction == "lr"
        else canvas_width - cell_width // 2
    )
    column_y = (
        3 * cell_height // 2
        if tb_direction == "tb"
        else canvas_height - 3 * cell_height // 2
    )
    for pattern_row_number in range(1, num_rows + 1):
        elements.append(
            f'<text x="{column_x}" y="{column_y}" text-anchor="middle" '
            f'dominant-baseline="central" font-size="14">'
            f'{pattern_row_number}</text>'
        )
        column_y += cell_height * (1 if tb_direction == "tb" else -1)

    elements.append("</svg>")
    return "\n".join(elements)
