"""Gauge conversion browser page wiring.

This module contains the Python runtime logic for demos/gauge-conversion/demo.html
so the HTML can stay free of inline Python.
"""

import base64
import sys

from pyknit.pyscript._assets import shared

READY = False
BOOT_ERROR = None
parse_chart = None
GaugeSwatch = None
convert_stitch_measure = None


def pattern_to_text(pattern):
    """Convert parsed chart rows into a compact text grid."""
    if not pattern:
        return ""
    lines = []
    for row in pattern:
        line = "".join(str(cell) for cell in row)
        lines.append(line)
    return "\n".join(lines)


def available_backends():
    """Return available rendering backends in preference order."""
    backends = ["text"]

    try:
        from PIL import Image  # noqa: F401

        backends.append("pillow")
    except Exception:
        pass

    try:
        import xml.etree.ElementTree as ET  # noqa: F401

        backends.insert(0, "svg")
    except Exception:
        pass

    return backends


def _symbol_for_cell(cell):
    """Return a concise visible symbol for a chart cell."""
    symbol = getattr(cell, "symbol", None)
    if symbol is None:
        symbol = str(cell)
    symbol = str(symbol)
    # knit is blank in pyknit's legend; draw a visible placeholder.
    if symbol.strip() == "":
        return "\u2022"
    return symbol


def _class_for_cell(cell):
    category = str(getattr(cell, "category", "other") or "other")
    safe = category.replace("_", "-").replace(" ", "-").lower()
    return "stitch-" + safe


def render_pattern(pattern):
    """Render pattern with SVG preferred, then PNG, then plain text."""
    if not pattern:
        return ("text", pattern_to_text([]))

    try:
        import xml.etree.ElementTree as ET  # noqa: F401

        cell_width = 20
        cell_height = 20

        rows = len(pattern)
        if rows == 0:
            return ("text", "")

        cols = max((len(row) for row in pattern), default=0)
        if cols == 0:
            return ("text", "")

        width = cols * cell_width + 20
        height = rows * cell_height + 20

        svg_lines = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" style="border: 1px solid #ccc;">',
            '<style>'
            '.stitch-label { font-family: monospace; font-size: 14px; text-anchor: middle; dominant-baseline: central; }'
            '.stitch-knit { fill: #1f2937; }'
            '.stitch-purl { fill: #1f2937; }'
            '.stitch-decrease { fill: #c62828; font-weight: 700; }'
            '.stitch-yarn-over { fill: #1565c0; font-weight: 700; }'
            '.stitch-increase { fill: #2e7d32; font-weight: 700; }'
            '.stitch-other { fill: #374151; }'
            'rect { stroke: #c7ced6; stroke-width: 1; fill: #ffffff; }'
            '</style>',
        ]

        for y, row in enumerate(pattern):
            for x, cell in enumerate(row):
                rect_x = 10 + x * cell_width
                rect_y = 10 + y * cell_height
                svg_lines.append(
                    f'<rect x="{rect_x}" y="{rect_y}" width="{cell_width}" height="{cell_height}" />'
                )
                cell_str = (
                    _symbol_for_cell(cell)
                    .replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                )
                cls = _class_for_cell(cell)
                svg_lines.append(
                    f'<text class="stitch-label {cls}" x="{rect_x + cell_width // 2}" y="{rect_y + cell_height // 2}">{cell_str}</text>'
                )

        svg_lines.append("</svg>")
        svg_content = "\n".join(svg_lines)
        print(f"SVG generated: {len(svg_content)} bytes", file=sys.stderr)
        return ("svg", svg_content)
    except Exception as exc:
        print(f"SVG rendering failed: {exc}", file=sys.stderr)

    try:
        from PIL import Image, ImageDraw

        cell_size = 20
        rows = len(pattern)
        cols = max((len(row) for row in pattern), default=0)

        width = cols * cell_size + 20
        height = rows * cell_size + 20

        img = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(img)

        for y, row in enumerate(pattern):
            for x, cell in enumerate(row):
                x_pos = 10 + x * cell_size
                y_pos = 10 + y * cell_size
                draw.rectangle(
                    [x_pos, y_pos, x_pos + cell_size, y_pos + cell_size],
                    outline="#cccccc",
                )
                draw.text((x_pos + 5, y_pos + 2), _symbol_for_cell(cell), fill="black")

        import io

        png_buffer = io.BytesIO()
        img.save(png_buffer, format="PNG")
        png_bytes = png_buffer.getvalue()
        print(f"PNG generated: {len(png_bytes)} bytes", file=sys.stderr)
        return ("png", png_bytes)
    except Exception as exc:
        print(f"Pillow rendering failed: {exc}", file=sys.stderr)

    print("Using text rendering fallback", file=sys.stderr)
    text = pattern_to_text(pattern)
    print(f"Text generated: {len(text)} chars", file=sys.stderr)
    return ("text", text)


def _out(element_id, html_content, display="block"):
    element = shared._get("#" + element_id)
    if element is not None:
        element.innerHTML = html_content
        if display:
            element.style.display = display


def _bootstrap_runtime():
    global READY, BOOT_ERROR, parse_chart, GaugeSwatch, convert_stitch_measure

    try:
        print("Attempting to import pyknit...", file=sys.stderr)
        import pyknit  # noqa: F401
        from pyknit.Chart import parse_chart as _parse_chart
        from pyknit import GaugeSwatch as _GaugeSwatch
        from pyknit import convert_stitch_measure as _convert_stitch_measure

        parse_chart = _parse_chart
        GaugeSwatch = _GaugeSwatch
        convert_stitch_measure = _convert_stitch_measure
        READY = True
        shared.set_status("ready", "✓ pyknit loaded successfully!", "Ready to use")
        shared.set_buttons_enabled(True)
        print("pyknit imported successfully", file=sys.stderr)
    except Exception as exc:
        READY = False
        BOOT_ERROR = str(exc)
        shared.set_status("error", f"Failed to load pyknit: {exc}")
        shared.set_buttons_enabled(False)
        print(f"ERROR: Failed to load pyknit: {exc}", file=sys.stderr)


def handle_calculation(event=None):
    if not READY:
        shared.show_error("calc-error", "pyknit is not loaded")
        return

    shared.hide_error("calc-error")

    try:
        pattern_st = float(shared.value("pattern-stitch-count"))
        pattern_meas = float(shared.value("pattern-stitch-measure"))
        my_st = float(shared.value("my-stitch-count"))
        my_meas = float(shared.value("my-stitch-measure"))
        measurement = float(shared.value("measurement"))

        if measurement <= 0:
            shared.show_error("calc-error", "Measurement must be positive (greater than 0)")
            _out("calc-output", "", "none")
            return

        if pattern_st <= 0 or pattern_meas <= 0 or my_st <= 0 or my_meas <= 0:
            shared.show_error("calc-error", "Gauge values must be positive")
            _out("calc-output", "", "none")
            return

        pattern_gauge = GaugeSwatch(
            stitch_count=pattern_st,
            stitch_measure=pattern_meas,
            row_count=40,
            row_measure=4,
            units="in",
        )
        my_gauge = GaugeSwatch(
            stitch_count=my_st,
            stitch_measure=my_meas,
            row_count=33,
            row_measure=4,
            units="in",
        )

        result = convert_stitch_measure(measurement, pattern_gauge, my_gauge)

        html = f"""<div class='success-message'>
          <strong>{measurement:g} in</strong> at the pattern gauge
          ({pattern_st} stitches / {pattern_meas} in)
          becomes <strong>{result:.2f} in</strong> at your gauge
          ({my_st} stitches / {my_meas} in).
        </div>"""
        _out("calc-output", html)
    except ValueError as exc:
        shared.show_error("calc-error", f"Invalid input: {exc}")
        _out("calc-output", "", "none")
    except Exception as exc:
        shared.show_error("calc-error", str(exc))
        _out("calc-output", "", "none")


def handle_chart(event=None):
    if not READY:
        shared.show_error("chart-error", "pyknit is not loaded")
        return

    shared.hide_error("chart-error")

    try:
        pattern_text = shared.value("pattern-input")

        if not pattern_text.strip():
            shared.show_error("chart-error", "Pattern cannot be empty")
            _out("chart-output", "", "none")
            _out("backend-info", "", "none")
            return

        try:
            pattern = parse_chart(pattern_text)
        except Exception as parse_error:
            shared.show_error("chart-error", f"Parse error: {parse_error}")
            _out("chart-output", "", "none")
            _out("backend-info", "", "none")
            return

        try:
            fmt, content = render_pattern(pattern)
        except Exception:
            text_output = pattern_to_text(pattern)
            _out(
                "chart-output",
                f"<div class='info-message'>Rendering with text fallback.</div><pre>{text_output}</pre>",
            )
            backends = ", ".join(available_backends())
            _out("backend-info", f"Available backends: {backends}", "block")
            return

        if fmt == "svg":
            _out("chart-output", f"<div class='info-message'>Rendered with SVG backend.</div>{content}")
        elif fmt == "png":
            data_uri = "data:image/png;base64," + base64.b64encode(content).decode("ascii")
            _out(
                "chart-output",
                f"<div class='info-message'>Rendered with Pillow/PNG backend.</div><img src='{data_uri}' alt='Chart' />",
            )
        elif fmt == "text":
            _out(
                "chart-output",
                f"<div class='info-message'>Rendered with text backend.</div><pre>{content}</pre>",
            )
        else:
            text_output = pattern_to_text(pattern)
            _out("chart-output", f"<pre>{text_output}</pre>")

        backends = ", ".join(available_backends())
        _out("backend-info", f"Available backends: {backends}", "block")

        chart_elem = shared._get("#chart-output")
        if chart_elem is not None:
            chart_elem.style.display = "block"
    except Exception as exc:
        shared.show_error("chart-error", str(exc))
        _out("chart-output", "", "none")
        _out("backend-info", "", "none")


def _enable_fields():
    for field_id in [
        "pattern-stitch-count",
        "pattern-stitch-measure",
        "my-stitch-count",
        "my-stitch-measure",
        "measurement",
        "pattern-input",
    ]:
        field = shared._get("#" + field_id)
        if field is not None:
            field.disabled = False


def bootstrap_page():
    _bootstrap_runtime()

    shared.bind_click("run-calc", handle_calculation)
    shared.bind_click("run-chart", handle_chart)

    _enable_fields()

    if READY:
        print("Running default calculations...", file=sys.stderr)
        handle_calculation()
        handle_chart()


bootstrap_page()
