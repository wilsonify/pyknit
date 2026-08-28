# Copyright (C) 2021 Terri Oda
# SPDX-License-Identifier: GPL-2.0-or-later

# !python
"""
pyKnit: a set of tools for knitters to do math, create charts, customise
patterns and more

pyKnit.browser: browser / PyScript helpers with graceful chart-rendering
fallback (Pillow -> SVG -> plain text).  Pillow and Chart are imported lazily
(inside functions) so this module can be imported in bare environments and
degrades at call time rather than import time.
"""

from typing import Any, List, Tuple

Stitch = Any
PatternRow = List[Stitch]
Pattern = List[PatternRow]


def available_backends() -> List[str]:
    """Return the chart rendering backends usable in this environment.

    Deterministic order: "svg" (pyknit.Chart.render_chart_svg) ahead of
    "pillow" (PIL + pyknit.Chart.plot_chart).
    """
    backends: List[str] = []
    if _svg_available():
        backends.append("svg")
    if _pillow_available():
        backends.append("pillow")
    return backends


def render_pattern(pattern: Pattern, legend: Any = None, **kwargs: Any) -> Tuple[str, Any]:
    """Best-effort chart rendering.

    Returns a (format, content) tuple:

    - ("svg", str): an SVG document when pyknit.Chart.render_chart_svg exists;
    - ("png", bytes): PNG bytes produced by pyknit.Chart.plot_chart otherwise;
    - ("text", str): the last-resort pattern_to_text() grid when every
      available backend fails to render.

    Raises RuntimeError only when no backend is available at all.
    """
    backends = available_backends()
    if not backends:
        raise RuntimeError("No chart rendering backend is available " "(need Pillow or pyknit's SVG renderer)")
    output_format = {"svg": "svg", "pillow": "png"}
    for backend in backends:
        try:
            content = _render_with_backend(backend, pattern, legend, kwargs)
        except Exception:
            # This backend failed; try the next one.
            continue
        return (output_format[backend], content)
    # Every available backend failed: degrade to a text grid, never crash.
    return ("text", pattern_to_text(pattern))


def pattern_to_text(pattern: Pattern) -> str:
    """Render a pattern as a plain-text grid of one-character codes.

    Multi-character symbols (e.g. PNG file paths or colour codes) become "X";
    each output line matches the length of its pattern row.
    """
    lines = []
    for row in pattern:
        codes = []
        for stitch in row:
            symbol = getattr(stitch, "symbol", "?")
            codes.append(symbol if len(symbol) == 1 else "X")
        lines.append("".join(codes))
    return "\n".join(lines)


def _render_with_backend(fmt: str, pattern: Pattern, legend: Any, kwargs: Any) -> Any:
    """Render with a single backend, returning its raw content."""
    if fmt == "svg":
        from pyknit.Chart import render_chart_svg

        return render_chart_svg(pattern)
    if fmt == "pillow":
        import io

        from pyknit.Chart import plot_chart

        image = plot_chart(pattern)
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()
    raise ValueError(f"Unknown rendering backend: {fmt}")


def _svg_available() -> bool:
    """True when pyknit.Chart exposes render_chart_svg() on this branch."""
    try:
        from pyknit import Chart
    except Exception:
        return False
    return hasattr(Chart, "render_chart_svg")


def _pillow_available() -> bool:
    import importlib.util

    return importlib.util.find_spec("PIL") is not None
