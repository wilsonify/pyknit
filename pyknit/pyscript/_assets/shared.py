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
_last_result = None


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


def chart_svg(pattern, lr_direction: str = "lr", tb_direction: str = "tb") -> str:
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


def render_html(pattern, lr_direction: str = "lr", tb_direction: str = "tb") -> Tuple[str, List[str]]:
    """Render a pattern to HTML (SVG preferred, PNG bytes base64 as a
    fallback), returned with the list of backends actually used."""
    backends = available_backends()
    svg = chart_svg(pattern, lr_direction, tb_direction)
    if svg:
        return (
            f"<textarea class='mono' rows='10'>{html.escape(svg)}</textarea><svg-hint></svg-hint>",
            backends,
        )
    return _text_as_html(pattern), backends


def _text_as_svg(pattern) -> str:
    rows = pattern_to_text(pattern).split("\n")
    max_len = max((len(row) for row in rows), default=0)
    cell = 18
    width = 40 + max_len * cell
    height = 30 + len(rows) * 22
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        '<rect x="1" y="1" width="{}" height="{}" fill="white" stroke="#999"/>'.format(width - 2, height - 2),
        f'<text x="{width//2}" y="16" text-anchor="middle" font-size="12" fill="#7b3fa0">'
        "text fallback (SVG backend unavailable)</text>",
    ]
    for i, row in enumerate(rows):
        parts.append(
            f'<text x="20" y="{34 + i * 22}" font-family="monospace" ' f'font-size="14">{html.escape(row)}</text>'
        )
    parts.append("</svg>")
    return "\n".join(parts)


def _text_as_html(pattern) -> str:
    return f"<pre class='mono'>{html.escape(pattern_to_text(pattern))}</pre>"


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


def _export_plan_text(plan) -> str:
    """Render a list of step dicts like hat-crown plan rows into text."""
    if not isinstance(plan, list):
        return ""
    lines = []
    for item in plan:
        if not isinstance(item, dict):
            continue
        if "heading" in item:
            heading = str(item.get("heading", "")).strip()
            if heading:
                lines.append(heading.upper())
            intro = str(item.get("intro", "")).strip()
            if intro:
                lines.append(intro)
            steps = item.get("steps")
            if isinstance(steps, list):
                for step in steps:
                    lines.append(f"- {step}".strip())
            rows = item.get("rows")
            if isinstance(rows, list):
                for row in rows:
                    lines.append(f"  {row}".strip())
            continue
        if "instruction" in item:
            instruction = str(item.get("instruction", "")).strip()
            transition = str(item.get("transition", "")).strip()
            round_no = item.get("round")
            if round_no is not None:
                prefix = f"Round {round_no}"
                if instruction:
                    line = f"{prefix}: {instruction}"
                else:
                    line = prefix
                if transition and transition != "->" and transition != "-":
                    line = f"{line} ({transition})"
                lines.append(line)
            else:
                if transition:
                    line = f"{instruction} ({transition})" if instruction else transition
                else:
                    line = instruction
                if line:
                    lines.append(line)
    return "\n".join(line for line in lines if line)


def export_pattern_text(result: Any) -> str:
    """Return a human-readable knitting export for the current demo result."""
    if result is None:
        return ""
    if isinstance(result, str):
        return result.strip()
    if isinstance(result, dict):
        if "plan" in result:
            plan = result["plan"]
            if isinstance(plan, list):
                text = _export_plan_text(plan)
                if text:
                    return text
            if isinstance(plan, dict) and isinstance(plan.get("sections"), list):
                text = _export_plan_text(plan["sections"])
                if text:
                    return text
        for key in ("instructions", "result", "pattern", "text"):
            if key in result:
                value = result[key]
                if isinstance(value, str):
                    if key != "text" and value.strip():
                        return value.strip()
                    if (
                        key == "text"
                        and value.strip()
                        and not any(k in result for k in ("instructions", "result", "pattern"))
                    ):
                        return value.strip()
                if isinstance(value, list):
                    if key == "pattern":
                        try:
                            from pyknit.io import pattern_to_instructions

                            return pattern_to_instructions(value)
                        except Exception:
                            pass
                    text = "\n".join(str(item) for item in value)
                    if text.strip():
                        return text.strip()
        lines = []
        for key, value in result.items():
            if key in {"svg", "html", "pattern", "text"}:
                continue
            text = export_pattern_text(value)
            if text.strip():
                lines.append(f"{key}: {text}")
        if lines:
            return "\n".join(lines)
        return str(result)
    if isinstance(result, (list, tuple)):
        if result and isinstance(result[0], dict):
            text = _export_plan_text(result)
            if text:
                return text
        return "\n".join(str(item) for item in result)
    return str(result)


def _download_text_file(filename: str, text: str) -> bool:
    """Download plain text in-browser; no-op outside the browser."""
    try:
        from js import document
    except Exception:
        return False

    encoded = text.replace("%", "%25").replace("\n", "%0A").replace("\r", "%0D").replace(" ", "%20")
    url = f"data:text/plain;charset=utf-8,{encoded}"

    link = document.createElement("a")
    link.href = url
    link.download = filename
    link.style.display = "none"
    document.body.appendChild(link)
    try:
        link.click()
    finally:
        link.remove()
    return True


def bind_export_pattern(
    button_id: str,
    result_getter,
    filename_prefix: str = "pyknit-pattern",
    title: Optional[str] = None,
) -> None:
    """Attach an export button that downloads the current demo result as text."""
    btn = _get("#" + button_id)
    if btn is None:
        return

    def handler(_event=None):
        result = result_getter() if callable(result_getter) else result_getter
        text = export_pattern_text(result)
        if not text.strip():
            set_status("ready", "Nothing to export yet", "Generate a result first.")
            return
        safe = (title or filename_prefix).lower()
        safe = "".join(ch if ch.isalnum() or ch in ("-", "_") else "-" for ch in safe)
        filename = f"{safe or 'pyknit-pattern'}.txt"
        if not _download_text_file(filename, text):
            set_status(
                "ready",
                "Export is ready",
                "This browser does not support file downloads.",
            )

    callback = handler
    try:
        from pyodide.ffi import create_proxy

        callback = create_proxy(handler)
        _BOUND_PROXIES.append(callback)
    except Exception:
        pass
    btn.addEventListener("click", callback)


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


def _normalize_demo(module: Any) -> Dict[str, Any]:
    """Return a canonical demo mapping.

    Supported inputs:
    - a DEMO dict
    - a module/object exposing ``DEMO``
    - a globals dict with ``DEFAULT_INPUTS`` and ``compute``
    """
    if module is None:
        module = globals()
    if isinstance(module, dict):
        if "compute" in module and "DEFAULT_INPUTS" in module:
            return module
        if "DEMO" in module and isinstance(module["DEMO"], dict):
            return module["DEMO"]
    demo = getattr(module, "DEMO", None)
    if isinstance(demo, dict):
        return demo
    if hasattr(module, "compute") and hasattr(module, "DEFAULT_INPUTS"):
        return {
            "TITLE": getattr(module, "TITLE", "Demo"),
            "DEFAULT_INPUTS": getattr(module, "DEFAULT_INPUTS"),
            "compute": getattr(module, "compute"),
            "to_html": getattr(module, "to_html", None),
        }
    raise TypeError("demo module must expose DEMO or compute/default inputs")


def _log_unexpected_error() -> None:
    import traceback

    traceback.print_exc()


def wire_demo(module: Optional[Any] = None) -> Any:
    """Return the demo page's :func:`run` handler.

    The demo module (``DEFAULT_INPUTS``, ``compute``, optional ``to_html``,
    optional ``TITLE``) may be passed explicitly, or provided as globals by
    a ``<script type="py" src="../_demos/foo.py">`` block — PyScript executes
    ``src`` scripts into the shared global namespace, so the conventional
    names are picked up automatically when ``module`` is ``None``.
    """
    demo = _normalize_demo(module)

    def run(event=None):
        try:
            inputs = collect_inputs(demo["DEFAULT_INPUTS"])
            result = demo["compute"](inputs)
        except Exception as exc:
            if isinstance(exc, ValueError):
                set_status("ready", "Please check your inputs", str(exc))
            else:
                set_status("error", "Unexpected demo error", str(exc))
                _log_unexpected_error()
            show_error("demo-error", str(exc))
            return
        hide_error("demo-error")
        to_html = demo.get("to_html")
        if to_html is not None:
            set_html("demo-output", to_html(result))
        else:
            set_html("demo-output", _default_result_html(result))
        set_status(
            "ready",
            f"✔ {demo.get('TITLE', 'Demo')} updated",
            "Adjust inputs and run again.",
        )
        return result

    return run


def bootstrap_demo(
    module: Optional[Any] = None,
    button_id: str = "run",
    action_label: str = "Run",
    auto_run: bool = True,
    export_button_id: Optional[str] = None,
) -> Any:
    """Wire a standard demo page and optionally run default inputs once."""
    set_status(
        "loading",
        "Loading pyknit runtime...",
        "First load can take 30-60 seconds while packages initialize.",
    )
    demo = _normalize_demo(module)
    latest_result = None

    def run(event=None):
        nonlocal latest_result
        global _last_result
        try:
            inputs = collect_inputs(demo["DEFAULT_INPUTS"])
            result = demo["compute"](inputs)
            latest_result = result
            _last_result = result
        except Exception as exc:
            if isinstance(exc, ValueError):
                set_status("ready", "Please check your inputs", str(exc))
            else:
                set_status("error", "Unexpected demo error", str(exc))
                _log_unexpected_error()
            show_error("demo-error", str(exc))
            return
        hide_error("demo-error")
        to_html = demo.get("to_html")
        if to_html is not None:
            set_html("demo-output", to_html(result))
        else:
            set_html("demo-output", _default_result_html(result))
        set_status(
            "ready",
            f"✔ {demo.get('TITLE', 'Demo')} updated",
            "Adjust inputs and run again.",
        )
        return result

    bind_click(button_id, run)
    if export_button_id:
        bind_export_pattern(
            export_button_id,
            lambda: latest_result,
            filename_prefix=(demo.get("TITLE", "pyknit") or "pyknit").lower().replace(" ", "-"),
            title=demo.get("TITLE", "pyknit"),
        )
    set_status(
        "ready",
        "✔ pyknit loaded",
        f"Edit inputs, then click '{action_label}'.",
    )
    if auto_run:
        run()
    return run


def _default_result_html(result: Any) -> str:
    """Fallback pretty-print for modules without a custom ``to_html``."""
    if isinstance(result, dict):
        rows = []
        for key, value in result.items():
            if key in ("svg", "pattern"):
                continue
            rows.append(f"<tr><th>{key}</th><td class='mono'>{html.escape(str(value))}</td></tr>")
        return "<table class='instructions'><tbody>" + "".join(rows) + "</tbody></table>"
    return f"<pre class='mono'>{html.escape(str(result))}</pre>"
