"""Hat Crown demo: explicit crown shaping math and round plan."""

DEFAULT_INPUTS = {"repeats": 8, "stitches": 80}

TITLE = "Hat Crown Planner"


def to_html(result):
    """Render crown plan with explicit strategy, math, and round-by-round table."""
    strategy_rows = "".join(f"<li>{_esc(item)}</li>" for item in result["strategy"])
    assumption_rows = "".join(f"<li>{_esc(item)}</li>" for item in result["assumptions"])

    round_rows = "".join(
        "<tr>"
        f"<td class='mono'>{row['round']}</td>"
        f"<td>{_esc(row['kind'])}</td>"
        f"<td class='mono'>{_esc(row['transition']).replace('-&gt;', '&rarr;')}</td>"
        f"<td>{_esc(row['instruction'])}</td>"
        "</tr>"
        for row in result["plan"]
    )

    return (
        "<style>"
        ".hat-summary{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));"
        "gap:0.7rem;margin:0.7rem 0;}"
        ".hat-pill{border:1px solid #ddd8d4;border-radius:6px;padding:0.55rem 0.7rem;background:#fdfcfa;}"
        ".hat-pill .label{display:block;font-size:0.78rem;color:#6b6572;text-transform:uppercase;letter-spacing:0.04em;}"
        ".hat-pill .value{font-size:1rem;font-weight:700;color:#2b2333;}"
        ".hat-layout{display:grid;grid-template-columns:1fr;gap:0.8rem;}"
        ".hat-note{margin:0.5rem 0 0;padding-left:1.1rem;}"
        ".hat-note li{margin:0.2rem 0;}"
        ".hat-rounds{width:100%;border-collapse:collapse;font-size:0.95rem;}"
        ".hat-rounds th,.hat-rounds td{border:1px solid #e5e1dc;padding:0.5rem 0.55rem;text-align:left;vertical-align:top;}"
        ".hat-rounds th{background:#f3ecf7;color:#5a2a75;font-weight:700;}"
        "</style>"
        f"<div class='output-box'>{result['svg']}</div>"
        "<div class='button-row'><button class='btn-secondary send-to-estimator' "
        "data-type='hat'>"
        "Send to Yarn Estimator &rarr;</button></div>"
        "<div class='output-box hat-layout'>"
        "<h3>Crown shaping strategy</h3>"
        "<div class='hat-summary'>"
        "<div class='hat-pill'><span class='label'>Cast-on</span>"
        f"<span class='value'>{result['stitches']} stitches</span></div>"
        "<div class='hat-pill'><span class='label'>Repeats</span>"
        f"<span class='value'>{result['repeats']} decrease repeats</span></div>"
        "<div class='hat-pill'><span class='label'>Math</span>"
        f"<span class='value'>{result['stitches']} / {result['repeats']} = {result['stitches_per_repeat']} per repeat</span></div>"
        "<div class='hat-pill'><span class='label'>Decrease step</span>"
        f"<span class='value'>- {result['repeats']} stitches per decrease round</span></div>"
        "</div>"
        f"<p><strong>Formula:</strong> stitches after each decrease round = before - {result['repeats']}.</p>"
        "<p><strong>Strategy:</strong></p>"
        f"<ul class='hat-note'>{strategy_rows}</ul>"
        "<p><strong>Assumptions:</strong></p>"
        f"<ul class='hat-note'>{assumption_rows}</ul>"
        "</div>"
        "<div class='output-box'>"
        "<h3>Round-by-round instructions</h3>"
        "<table class='hat-rounds'>"
        "<thead><tr><th>Round</th><th>Type</th><th>Stitches</th><th>Instruction</th></tr></thead>"
        f"<tbody>{round_rows}</tbody></table></div>"
    )


def _esc(text):
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def compute(inputs):
    """Return explicit crown shaping math and table-ready round rows."""
    repeats = int(inputs["repeats"])
    stitches = int(inputs["stitches"])

    _validate_inputs(repeats, stitches)

    stitches_per_repeat = stitches // repeats
    plan = _build_plan(repeats, stitches, stitches_per_repeat)

    transitions = [row["after"] for row in plan if row["kind"] == "Decrease"]
    rounds = [row["instruction"] for row in plan]

    strategy = [
        "Place markers for evenly spaced decrease repeats.",
        "On each decrease round, work one k2tog in each repeat section.",
        "Work one plain knit round between decrease rounds.",
        "Stop when one more decrease round would leave zero stitches; then cinch the crown closed.",
    ]
    assumptions = [
        "Cast-on stitches must divide evenly by decrease repeats.",
        "Each repeat starts with at least 2 stitches so one decrease fits in each repeat.",
        "This planner models classic paired rounds: decrease round, then knit-even round.",
    ]

    return {
        "repeats": repeats,
        "stitches": stitches,
        "stitches_per_repeat": stitches_per_repeat,
        "plan": plan,
        "rounds": rounds,
        "strategy": strategy,
        "assumptions": assumptions,
        "svg": _crown_svg(repeats, [stitches] + transitions),
        "_estimator_data": {
            "project_type": "hat",
            "source": "hat_crown_planner",
        },
    }


def _validate_inputs(repeats, stitches):
    if repeats <= 0 or stitches <= 0:
        raise ValueError("repeats and stitches must be positive integers")
    if stitches % repeats != 0:
        raise ValueError(
            "cast-on stitches must divide evenly by decrease repeats "
            f"({stitches} is not divisible by {repeats})"
        )
    if stitches < repeats * 2:
        raise ValueError(
            "cast-on stitches are too small for this strategy: "
            "need at least 2 stitches per repeat before decreases"
        )


def _build_plan(repeats, stitches, stitches_per_repeat):
    plan = []
    round_no = 1
    current = stitches
    per_repeat = stitches_per_repeat

    while current - repeats > 0:
        before = current
        after = before - repeats

        if per_repeat > 2:
            decrease_instruction = (
                f"*K{per_repeat - 2}, k2tog* around ({repeats} repeats)"
            )
        else:
            decrease_instruction = f"*K2tog* around ({repeats} repeats)"

        plan.append(
            {
                "round": round_no,
                "kind": "Decrease",
                "before": before,
                "after": after,
                "transition": f"{before} -> {after}",
                "instruction": decrease_instruction,
            }
        )
        round_no += 1

        if after > repeats:
            plan.append(
                {
                    "round": round_no,
                    "kind": "Knit even",
                    "before": after,
                    "after": after,
                    "transition": f"{after} -> {after}",
                    "instruction": "Knit 1 round even (no decreases)",
                }
            )
            round_no += 1

        current = after
        per_repeat -= 1

    plan.append(
        {
            "round": round_no,
            "kind": "Finish",
            "before": current,
            "after": current,
            "transition": f"{current} -> {current}",
            "instruction": (
                "Cut yarn, leave a tail, thread through remaining stitches, and pull closed"
            ),
        }
    )
    return plan


def _crown_svg(repeats, counts):
    """Top-down crown SVG: wedge lines + concentric stitch-count rings."""
    import math

    size = 320
    cx = cy = size / 2
    outer = size / 2 - 20

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 {size} {size}">'
    ]
    if counts:
        max_count = max(counts)
        for count in counts:
            radius = outer * (count / max_count)
            parts.append(
                f'<circle cx="{cx}" cy="{cy}" r="{radius:.1f}" '
                f'fill="none" stroke="#c9a7e0" stroke-width="1" '
                f'stroke-dasharray="4 3" opacity="0.8"/>'
            )

    for i in range(repeats):
        angle = 2 * math.pi * i / repeats
        x2 = cx + outer * math.cos(angle)
        y2 = cy + outer * math.sin(angle)
        parts.append(
            f'<line x1="{cx}" y1="{cy}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="#7b3fa0" stroke-width="2"/>'
        )
        parts.append(f'<circle cx="{x2:.1f}" cy="{y2:.1f}" r="4" fill="#7b3fa0"/>')
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="6" fill="#7b3fa0"/>')
    parts.append(
        f'<text x="{cx}" y="{size - 10}" text-anchor="middle" font-size="13" '
        'fill="#5a2a75">top-down crown stitch levels: '
        + (' -> '.join(str(c) for c in counts))
        + "</text>"
    )
    parts.append("</svg>")
    return "\n".join(parts)


DEMO = {
    "TITLE": TITLE,
    "DEFAULT_INPUTS": DEFAULT_INPUTS,
    "compute": compute,
    "to_html": to_html,
}
