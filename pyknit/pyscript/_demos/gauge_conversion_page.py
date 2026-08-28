"""Gauge conversion browser page wiring.

This module contains the Python runtime logic for demos/gauge-conversion/demo.html
so the HTML can stay free of inline Python.  It exposes two compute paths:

* ``compute_calc`` — convert a measurement between gauges
* ``compute_chart`` — parse a pattern and render it as a chart

Both are wrapped in a ``DEMO`` dict so ``shared.bootstrap_demo`` can be used
for the chart section, while the gauge-calc section is wired separately.
"""

from pyknit.pyscript._assets import shared

READY = False
BOOT_ERROR = None
parse_chart = None
GaugeSwatch = None
convert_stitch_measure = None

latest_calc_result = None
latest_chart_result = None


# --------------------------------------------------------------------------
# Gauge conversion compute
# --------------------------------------------------------------------------


def compute_calc(inputs):
    """Convert a measurement between two gauges."""
    pattern_st = float(inputs.get("pattern-stitch-count", 27.5))
    pattern_meas = float(inputs.get("pattern-stitch-measure", 10))
    my_st = float(inputs.get("my-stitch-count", 23.5))
    my_meas = float(inputs.get("my-stitch-measure", 10))
    measurement = float(inputs.get("measurement", 42))

    if measurement <= 0:
        raise ValueError("Measurement must be positive (greater than 0)")
    if pattern_st <= 0 or pattern_meas <= 0 or my_st <= 0 or my_meas <= 0:
        raise ValueError("Gauge values must be positive")

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
    return {
        "measurement": measurement,
        "pattern_st": pattern_st,
        "pattern_meas": pattern_meas,
        "my_st": my_st,
        "my_meas": my_meas,
        "result": result,
    }


def calc_to_html(result):
    return (
        f"<div class='success-message'>"
        f"<strong>{result['measurement']:g} in</strong> at the pattern gauge "
        f"({result['pattern_st']} stitches / {result['pattern_meas']} in) "
        f"becomes <strong>{result['result']:.2f} in</strong> at your gauge "
        f"({result['my_st']} stitches / {result['my_meas']} in)."
        f"</div>"
    )


def calc_to_text(result):
    """Human-readable export text for the gauge conversion."""
    return (
        f"{result['measurement']:g} in at the pattern gauge "
        f"({result['pattern_st']} stitches / {result['pattern_meas']} in) "
        f"becomes {result['result']:.2f} in at your gauge "
        f"({result['my_st']} stitches / {result['my_meas']} in)."
    )


# --------------------------------------------------------------------------
# Chart rendering compute (uses shared module — no duplicate code)
# --------------------------------------------------------------------------

CHART_DEFAULT_INPUTS = {
    "pattern": "k2 yo k2tog yo k1\np1 k2 yo k2tog p2",
}


def compute_chart(inputs):
    """Parse the pattern and render it as a chart via shared helpers."""
    pattern_text = inputs.get("pattern", "")
    if not pattern_text.strip():
        raise ValueError("Pattern cannot be empty")
    pattern = shared.parse_chart(pattern_text)
    if not any(pattern):
        raise ValueError("Pattern produced no stitches - check the instructions")
    return {"pattern": pattern}


def chart_to_html(result):
    svg = shared.chart_svg(result["pattern"])
    _backends = shared.available_backends()
    if svg:
        return f"<div class='info-message'>Rendered with SVG backend.</div>" f"<div class='output-box'>{svg}</div>"
    text = shared.pattern_to_text(result["pattern"])
    return (
        f"<div class='info-message'>Rendered with text backend.</div>"
        f"<div class='output-box'><pre>{text}</pre></div>"
    )


# --------------------------------------------------------------------------
# Runtime bootstrap
# --------------------------------------------------------------------------


def _bootstrap_runtime():
    global READY, BOOT_ERROR, parse_chart, GaugeSwatch, convert_stitch_measure

    try:
        print("Attempting to import pyknit...")
        import pyknit  # noqa: F401
        from pyknit.Chart import parse_chart as _parse_chart
        from pyknit import GaugeSwatch as _GaugeSwatch
        from pyknit import convert_stitch_measure as _convert_stitch_measure

        parse_chart = _parse_chart
        GaugeSwatch = _GaugeSwatch
        convert_stitch_measure = _convert_stitch_measure
        READY = True
        shared.set_status("ready", "pyknit loaded", "Edit inputs, then click the button.")
        shared.set_buttons_enabled(True)
        print("pyknit imported successfully")
    except Exception as exc:
        READY = False
        BOOT_ERROR = str(exc)
        shared.set_status("error", f"Failed to load pyknit: {exc}")
        shared.set_buttons_enabled(False)
        print(f"ERROR: Failed to load pyknit: {exc}")


def _handle_calc(event=None):
    global latest_calc_result
    if not READY:
        shared.show_error("calc-error", "pyknit is not loaded")
        return
    shared.hide_error("calc-error")
    try:
        inputs = {
            "pattern-stitch-count": shared.value("pattern-stitch-count"),
            "pattern-stitch-measure": shared.value("pattern-stitch-measure"),
            "my-stitch-count": shared.value("my-stitch-count"),
            "my-stitch-measure": shared.value("my-stitch-measure"),
            "measurement": shared.value("measurement"),
        }
        result = compute_calc(inputs)
        latest_calc_result = result
        shared.set_html("calc-output", calc_to_html(result))
        shared.hide_error("calc-error")
        return result
    except ValueError as exc:
        shared.show_error("calc-error", f"Invalid input: {exc}")
        shared.set_html("calc-output", "")
    except Exception as exc:
        shared.show_error("calc-error", str(exc))
        shared.set_html("calc-output", "")
    return None


def _handle_chart(event=None):
    global latest_chart_result
    if not READY:
        shared.show_error("chart-error", "pyknit is not loaded")
        return
    shared.hide_error("chart-error")
    try:
        inputs = {"pattern": shared.value("pattern-input")}
        result = compute_chart(inputs)
        latest_chart_result = result
        shared.set_html("chart-output", chart_to_html(result))
        shared.hide_error("chart-error")
        return result
    except ValueError as exc:
        shared.show_error("chart-error", f"Parse error: {exc}")
        shared.set_html("chart-output", "")
    except Exception as exc:
        shared.show_error("chart-error", str(exc))
        shared.set_html("chart-output", "")
    return None


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

    shared.bind_click("run-calc", _handle_calc)
    shared.bind_click("run-chart", _handle_chart)
    shared.bind_export_pattern(
        "export-calc",
        lambda: (calc_to_text(latest_calc_result) if latest_calc_result else ""),
        title="gauge-conversion",
    )
    shared.bind_export_pattern(
        "export-chart",
        lambda: (shared.export_pattern_text(latest_chart_result) if latest_chart_result else ""),
        title="gauge-conversion-chart",
    )

    _enable_fields()

    if READY:
        print("Running default calculations...")
        _handle_calc()
        _handle_chart()


bootstrap_page()
