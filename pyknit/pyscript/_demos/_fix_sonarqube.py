"""Shawl Shapes demo: generate written instructions for four shawl shapes.

Uses ``pyknit.shawl_shapes.generate_shawl`` for the instructions and draws
a simple silhouette of the chosen shape.
"""

DEFAULT_INPUTS = {
    "shape": "crescent",
    "width": 24,
    "length": 30,
    "stitch_count": 16,
    "stitch_measure": 4,
    "row_count": 20,
    "row_measure": 4,
}

TITLE = "Shawl Shapes"


def to_html(result):
    # Render the shape silhouette plus the instruction list and assumptions.
    steps = "".join(f"<tr><td class='mono'>{_esc(step)}</td></tr>" for step in result["instructions"])
    est = result.get("_estimator_data", {})
    assumptions = result.get("assumptions", [])
    assumption_html = ""
    if assumptions:
        items = "".join(f"<li>{_esc(a)}</li>" for a in assumptions)
        assumption_html = (
            "<section class='plan-section'>"
            "<h4>How this shawl is constructed</h4>"
            f"<ul class='plan-assumptions'>{items}</ul>"
            "</section>"
        )
    return (
        f"<div class='output-box'>{result['svg']}</div>"
        "<div class='button-row'><button class='btn-secondary send-to-estimator' "
        f"data-stitches='{est.get('stitch_count', 0)}' "
        f"data-type='{est.get('project_type', 'custom')}'>"
        "Send to Yarn Estimator &rarr;</button></div>"
        f"{assumption_html}"
        "<h3>Instructions</h3>"
        f"<div class='output-box'><table class='instructions'><tbody>{steps}</tbody></table></div>"
    )


def _esc(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def compute(inputs):
    "Return instructions + an SVG silhouette for the requested shape."
    from pyknit import shawl_shapes
    from pyknit.GaugeSwatch import GaugeSwatch

    shape = inputs.get("shape", "crescent")
    if shape not in shawl_shapes.SUPPORTED_SHAPES:
        raise ValueError("shape must be one of " + ", ".join(shawl_shapes.SUPPORTED_SHAPES))

    width = float(inputs["width"])
    length = float(inputs["length"])
    mm = _measure(inputs)
    gauge = GaugeSwatch(
        stitch_count=mm["stitch_count"],
        stitch_measure=mm["stitch_measure"],
        row_count=mm["row_count"],
        row_measure=mm["row_measure"],
        units="in",
    )
    if width <= 0 or length <= 0:
        raise ValueError("width and length must be positive")

    instructions = shawl_shapes.generate_shawl(shape, width, length, gauge)
    est_stitches = gauge.measurement_to_stitches(width) * gauge.measurement_to_rows(length)
    if shape in ("triangle", "crescent"):
        est_stitches = est_stitches // 2
    return {
        "shape": shape,
        "width": width,
        "length": length,
        "instructions": instructions,
        "svg": _shape_svg(shape),
        "assumptions": _build_assumptions(shape, width, length, gauge),
        "_estimator_data": {
            "stitch_count": est_stitches,
            "project_type": (f"shawl_{shape}" if shape in ("triangle", "crescent", "rectangle") else "custom"),
            "source": "shawl_shapes_planner",
        },
    }


def _measure(inputs):
    for key in ("stitch_count", "stitch_measure", "row_count", "row_measure"):
        if float(inputs[key]) <= 0:
            raise ValueError("gauge values must be positive")
    return {key: float(inputs[key]) for key in inputs if key.startswith(("stitch_", "row_"))}


def _build_assumptions(shape, width, length, gauge):
    sps = gauge.measurement_to_stitches(width)
    rps = gauge.measurement_to_rows(length)
    assumptions = [
        f"Gauge: {gauge.stitch_count} stitches per {gauge.stitch_measure} "
        f"({sps:.1f} stitches/in) x {gauge.row_count} rows per "
        f"{gauge.row_measure} ({rps:.1f} rows/in).",
    ]
    if shape == "crescent":
        assumptions.append(
            "Crescent shawls are worked top-down with short rows to create "
            "the curved shape, then worked straight to the edge."
        )
    elif shape == "triangle":
        assumptions.append(
            "Triangle shawls are worked top-down from the centre back "
            "with increases along the centre and both edges."
        )
    elif shape == "square":
        assumptions.append(
            "Square shawls are worked from the centre outward, with increases at four corners each round."
        )
    elif shape == "rectangle":
        assumptions.append(
            "Rectangle shawls are worked flat from one end to the other "
            "(or from the centre outward), with no shaping."
        )
    return assumptions


def _shape_svg(shape):
    "Simple SVG silhouette per shape type."
    size = 320
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">']
    stroke = 'fill="#e8dcf2" stroke="#7b3fa0" stroke-width="2"'
    if shape == "square":
        parts.append(f'<rect x="40" y="40" width="240" height="240" {stroke}/>')
    elif shape == "rectangle":
        parts.append(f'<rect x="40" y="120" width="240" height="120" {stroke}/>')
    elif shape == "triangle":
        parts.append(f'<polygon points="160,30 60,290 260,290" {stroke}/>')
    elif shape == "crescent":
        parts.append(f'<path d="M 40 250 C 40 100 160 60 280 180 C 200 230 90 250 40 250 Z" {stroke}/>')
    parts.append(f'<text x="160" y="{size - 12}" text-anchor="middle" font-size="13" fill="#5a2a75">{shape}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


DEMO = {
    "TITLE": TITLE,
    "DEFAULT_INPUTS": DEFAULT_INPUTS,
    "compute": compute,
    "to_html": to_html,
}
