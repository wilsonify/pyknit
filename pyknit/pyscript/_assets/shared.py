"""Shared helpers for the pyKnit browser demos.

This module is loaded twice per demo:

1. In the browser by PyScript:  ``<script type="py" src="../_assets/shared.py">``
2. From the test suite: plain ``import`` in this repository.

Everything that touches the DOM is guarded so the same code runs in both
environments.  All pyknit imports are lazy and feature-detected so older
PyPI releases of pyknit (which may be missing newer functions such as
``render_chart_svg``, ``estimate``, ``Sock`` or ``io``) degrade gracefully
instead of crashing the demo.

The shared module only never imports pyscript at module scope; the DOM is
reached through :func:`_document` at call time.
"""

import importlib
from typing import Any, Dict, List, Optional, Tuple

import base64
import html
import math


# --------------------------------------------------------------------------
# DOM access helpers (safe outside the browser)
# --------------------------------------------------------------------------


def _document():
    """Return the PyScript ``document`` object if available, else None."""
    try:
        from pyscript import document
    except Exception:
        return None
    return document


def _get(selector: str):
    """querySelector wrapper, None outside the browser."""
    doc = _document()
    if doc is None:
        return None
    return doc.querySelector(selector)


def _all(selector: str):
    """querySelectorAll wrapper, empty list outside the browser."""
    doc = _document()
    if doc is None:
        return []
    return doc.querySelectorAll(selector)


def value(element_id: str) -> str:
    el = _get("#" + element_id)
    return el.value if el is not None else ""


def set_value(element_id: str, text: Any) -> None:
    el = _get("#" + element_id)
    if el is not None:
        el.value = str(text)


def set_text(element_id: str, text: Any) -> None:
    el = _get("#" + element_id)
    if el is not None:
        el.textContent = str(text)


def set_html(element_id: str, content: Any) -> None:
    el = _get("#" + element_id)
    if el is not None:
        el.innerHTML = str(content)


def get_number(element_id: str, default: float = 0.0) -> float:
    """Parse a number input, raising ValueError on garbage."""
    raw = value(element_id).strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        raise ValueError(f"'{raw}' is not a valid number")


def get_int(element_id: str, default: int = 0) -> int:
    return int(get_number(element_id, default))


def show_error(element_id: str, message: str) -> None:
    el = _get("#" + element_id)
    if el is not None:
        el.textContent = f"Error: {message}"
        el.style.display = "block"
    else:
        set_html(element_id, f"<div class='error-message'>Error: {message}</div>")


def hide_error(element_id: str) -> None:
    el = _get("#" + element_id)
    if el is not None:
        el.style.display = "none"


def new_html_error(element_id: str, message: str) -> None:
    """Show an error using innerHTML so it is styled by common.css."""
    el = _get("#" + element_id)
    if el is not None:
        el.innerHTML = f"<div class='error-message'>Error: {message}</div>"
        el.style.display = "block"


def set_status(state: str, message: str, detail: str = "") -> None:
    """Drive the shared status banner (loading / ready / error)."""
    banner = _get("#status-banner")
    if banner is not None:
        banner.classList.remove("loading", "ready", "error")
        if state in ("loading", "ready", "error"):
            banner.classList.add(state)
    msg = _get("#status-message")
    if msg is not None:
        msg.textContent = message
    det = _get("#status-detail")
    if det is not None:
        det.textContent = detail


def set_buttons_enabled(enabled: bool) -> None:
    for btn in _all("button"):
        if btn is not None:
            btn.disabled = not enabled


_BOUND_PROXIES = []


def bind_click(button_id: str, handler) -> None:
    """Attach a click listener, guarded for out-of-browser use.

    In the browser the raw Python function cannot be passed straight to
    ``addEventListener``: Pyodide would destroy the borrowed proxy at the end
    of the call, so the listener would silently never fire.  We wrap the
    handler in ``create_proxy`` and keep a reference so it survives for the
    lifetime of the page (see the QA suite for the regression test).
    """
    btn = _get("#" + button_id)
    if btn is None or not hasattr(btn, "addEventListener"):
        return
    callback = handler
    try:
        from pyodide.ffi import create_proxy

        callback = create_proxy(handler)
        _BOUND_PROXIES.append(callback)
    except Exception:
        pass
    btn.addEventListener("click", callback)


# --------------------------------------------------------------------------
# pyknit feature detection
# --------------------------------------------------------------------------


def _pyknit_module(name: str):
    """Import a pyknit submodule, returning None when it is unavailable."""
    try:
        return importlib.import_module(name)
    except Exception:
        return None


def _render_chart_svg_exists() -> bool:
    try:
        from pyknit.Chart import render_chart_svg  # noqa: F401
    except Exception:
        return False
    return True


def parse_chart(text: str, legend=None):
    """parse_chart with the default legend, feature-safe."""
    from pyknit.Chart import parse_chart as _parse, stitch_legend

    if legend is None:
        legend = stitch_legend
    return _parse(text, legend)


def pattern_to_text(pattern) -> str:
    """Text grid using pyknit.browser when present, else a local fallback."""
    try:
        from pyknit.browser import pattern_to_text as _ptt

        return _ptt(pattern)
    except Exception:
        lines = []
        for row in pattern:
            codes = []
            for stitch in row:
                symbol = getattr(stitch, "symbol", "?")
                codes.append(symbol if len(symbol) == 1 else "X")
            lines.append("".join(codes))
        return "\n".join(lines)


def available_backends() -> List[str]:
    try:
        from pyknit.browser import available_backends as _ab

        return _ab()
    except Exception:
        return ["svg", "text"]


def chart_svg(
    pattern, lr_direction: str = "lr", tb_direction: str = "tb"
) -> str:
    """Return an inline SVG document for a parsed pattern, with a text-grid
    fallback rendered as an SVG <text> blob when the pyknit renderer is
    missing (old PyPI releases)."""
    if _render_chart_svg_exists():
        try:
            from pyknit.Chart import render_chart_svg

            return render_chart_svg(pattern, lr_direction, tb_direction)
        except Exception as exc:
            note = f"<!-- SVG backend failed ({exc}); using text fallback -->"
            return note + _text_as_svg(pattern)
    return _text_as_svg(pattern)


def render_html(
    pattern, lr_direction: str = "lr", tb_direction: str = "tb"
) -> Tuple[str, List[str]]:
    """Render a pattern to HTML (SVG preferred, PNG bytes base64 as a
    fallback), returned with the list of backends actually used."""
    backends = available_backends()
    svg = chart_svg(pattern, lr_direction, tb_direction)
    if svg:
        return f"<textarea class='mono' rows='10'>{html.escape(svg)}</textarea><svg-hint></svg-hint>", backends
    return _text_as_html(pattern), backends


def _text_as_svg(pattern) -> str:
    rows = pattern_to_text(pattern).split("\n")
    max_len = max((len(row) for row in rows), default=0)
    cell = 18
    width = 40 + max_len * cell
    height = 30 + len(rows) * 22
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        '<rect x="1" y="1" width="{}" height="{}" fill="white" stroke="#999"/>'.format(
            width - 2, height - 2
        ),
        f'<text x="{width//2}" y="16" text-anchor="middle" font-size="12" fill="#7b3fa0">'
        "text fallback (SVG backend unavailable)</text>",
    ]
    for i, row in enumerate(rows):
        parts.append(
            f'<text x="20" y="{34 + i * 22}" font-family="monospace" '
            f'font-size="14">{html.escape(row)}</text>'
        )
    parts.append("</svg>")
    return "\n".join(parts)


def _text_as_html(pattern) -> str:
    return (
        f"<pre class='mono'>{html.escape(pattern_to_text(pattern))}</pre>"
    )


def svg_to_data_uri(png_bytes: bytes) -> str:
    return "data:image/png;base64," + base64.b64encode(png_bytes).decode("ascii")


# --------------------------------------------------------------------------
# Small helpers used by several demos
# --------------------------------------------------------------------------


def stitch_counts_report(pattern) -> List[Tuple[str, int]]:
    """Summarise a parsed pattern with the GaugeSwatch accounting functions
    (feature-safe: falls back to plain counts)."""
    try:
        from pyknit.GaugeSwatch import (
            chart_width,
            stitch_operations,
            stitches_consumed,
            stitches_produced,
        )
    except Exception:
        return [
            ("rows", len(pattern)),
            ("stitches", sum(len(row) for row in pattern)),
        ]
    report = [
        ("rows", len(pattern)),
        ("stitches", sum(stitch_operations(row) for row in pattern)),
        ("consumed", sum(stitches_consumed(row) for row in pattern)),
        ("produced", sum(stitches_produced(row) for row in pattern)),
        ("chart width", max((chart_width(row) for row in pattern), default=0)),
    ]
    return report


def gauge(
    stitch_count: float,
    stitch_measure: float,
    row_count: float,
    row_measure: float,
    units: str = "in",
):
    """Build a GaugeSwatch, feature-safe."""
    from pyknit.GaugeSwatch import GaugeSwatch

    return GaugeSwatch(
        stitch_count=stitch_count,
        stitch_measure=stitch_measure,
        row_count=row_count,
        row_measure=row_measure,
        units=units,
    )


def humanize_hours(total_hours: float) -> str:
    """Format an hour figure as 'X hours Y minutes'."""
    hours = math.floor(total_hours)
    minutes = round((total_hours - hours) * 60)
    if minutes == 60:
        hours += 1
        minutes = 0
    parts = []
    if hours:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    return " ".join(parts) if parts else "under a minute"


# --------------------------------------------------------------------------
# page wiring used by every demo
# --------------------------------------------------------------------------


def collect_inputs(defaults: Dict[str, Any]) -> Dict[str, Any]:
    """Read every input/textarea/select into a dict of strings, falling back
    to ``defaults`` when a field is empty or missing."""
    out: Dict[str, Any] = {}
    for key, default in defaults.items():
        raw = value(key)
        out[key] = raw if raw not in (None, "") else default
    return out


def wire_demo(module: Optional[Any] = None) -> Any:
    """Return the demo page's :func:`run` handler.

    The demo module (``DEFAULT_INPUTS``, ``compute``, optional ``to_html``,
    optional ``TITLE``) may be passed explicitly, or provided as globals by
    a ``<script type="py" src="../_demos/foo.py">`` block — PyScript executes
    ``src`` scripts into the shared global namespace, so the conventional
    names are picked up automatically when ``module`` is ``None``.
    """
    import traceback

    if module is None:
        module = globals()

    def run(event=None):
        try:
            inputs = collect_inputs(module["DEFAULT_INPUTS"])
            result = module["compute"](inputs)
        except Exception as exc:
            set_status("error", f"Error: {exc}", "")
            show_error("demo-error", str(exc))
            traceback.print_exc()
            return
        hide_error("demo-error")
        to_html = module.get("to_html")
        if to_html is not None:
            set_html("demo-output", to_html(result))
        else:
            set_html("demo-output", _default_result_html(result))
        set_status(
            "ready",
            f"✔ {module.get('TITLE', 'Demo')} computed successfully",
            "",
        )

    return run


def _default_result_html(result: Any) -> str:
    """Fallback pretty-print for modules without a custom ``to_html``."""
    if isinstance(result, dict):
        rows = []
        for key, value in result.items():
            if key in ("svg", "pattern"):
                continue
            rows.append(
                f"<tr><th>{key}</th><td class='mono'>{html.escape(str(value))}</td></tr>"
            )
        return "<table class='instructions'><tbody>" + "".join(
            f"<tr><th>{r[0]}</th><td class='mono'>{r[1]}</td></tr>" for r in rows
        ) + "</tbody></table>"
    return f"<pre class='mono'>{html.escape(str(result))}</pre>"