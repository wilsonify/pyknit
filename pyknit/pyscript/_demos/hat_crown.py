"""Hat Crown demo: explicit crown shaping math and round plan.

The crown is modeled as a dome, not a flat cone: the gap between decrease
rounds shortens as the crown narrows, so the stitch count falls gently at
the brim edge (every 3rd round), settles into the classic every-other-round
rhythm through the middle, and accelerates (every round) as the crown rounds
over the top to the drawstring cinch.  Every decrease round removes exactly
``repeats`` stitches (one k2tog per marker), so the markers never move and
each repeat is easy to verify while knitting.

Also produces the executable Knit Simulator pattern (``sim_plan``) so the
hat crown can be handed to the Knit Simulator, exactly like the sock and
raglan planners.
"""

DEFAULT_INPUTS = {"repeats": 8, "stitches": 80}

TITLE = "Hat Crown Planner"

_PHASE_LABELS = {
    "curve": "Curve in",
    "steady": "Steady",
    "top": "Round over",
}


def to_html(result):
    """Render crown plan with explicit strategy, math, round-by-round table
    and two crown-shape visualizations (top-down rings + side profile)."""
    strategy_rows = "".join(f"<li>{_esc(item)}</li>" for item in result["strategy"])
    assumption_rows = "".join(f"<li>{_esc(item)}</li>" for item in result["assumptions"])

    round_rows = "".join(
        "<tr>"
        f"<td class='mono'>{row['round']}</td>"
        f"<td>{_esc(row['phase_label'])}</td>"
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
        ".hat-pill .label{display:block;font-size:0.78rem;color:#6b6572;text-transform:uppercase;letter-spacing:0.04em;}"  # noqa: E501
        ".hat-pill .value{font-size:1rem;font-weight:700;color:#2b2333;}"
        ".hat-layout{display:grid;grid-template-columns:1fr;gap:0.8rem;}"
        ".hat-note{margin:0.5rem 0 0;padding-left:1.1rem;}"
        ".hat-note li{margin:0.2rem 0;}"
        ".hat-rounds{width:100%;border-collapse:collapse;font-size:0.95rem;}"
        ".hat-rounds th,.hat-rounds td{border:1px solid #e5e1dc;padding:0.5rem 0.55rem;text-align:left;vertical-align:top;}"  # noqa: E501
        ".hat-rounds th{background:#f3ecf7;color:#5a2a75;font-weight:700;}"
        ".hat-shapes{display:grid;grid-template-columns:1fr 1fr;gap:0.8rem;align-items:start;}"
        ".hat-shapes svg{width:100%;height:auto;background:#fbf7ff;border:1px solid #e3d5f2;border-radius:8px;}"
        ".hat-shape-note{margin:0.5rem 0 0;font-size:0.92rem;color:#4a4452;}"
        "</style>"
        "<div class='output-box'><h3>Crown shape</h3>"
        f"<div class='hat-shapes'>{result['svg']}{result['svg_profile']}</div>"
        f"<p class='hat-shape-note'>{_esc(result['shape_note'])}</p></div>"
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
        f"<span class='value'>{result['stitches']} / {result['repeats']} = {result['stitches_per_repeat']} per repeat</span></div>"  # noqa: E501
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
        "<thead><tr><th>Round</th><th>Phase</th><th>Type</th><th>Stitches</th><th>Instruction</th></tr></thead>"
        f"<tbody>{round_rows}</tbody></table></div>"
    )


def _esc(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def compute(inputs):
    """Return explicit crown shaping math and table-ready round rows."""
    repeats = int(inputs["repeats"])
    stitches = int(inputs["stitches"])

    _validate_inputs(repeats, stitches)

    stitches_per_repeat = stitches // repeats
    plan = _build_plan(repeats, stitches)

    transitions = [row["after"] for row in plan if row["kind"] == "Decrease"]
    rounds = [row["instruction"] for row in plan]

    strategy = [
        f"Place {repeats} markers, one per repeat ({stitches_per_repeat} stitches between them).",
        f"On each decrease round, work one k2tog in every repeat — {repeats} stitches removed.",
        "Shape the crown as a dome: the gap between decrease rounds shortens as it narrows.",
        "  - Curve in (brim edge): decrease every 3rd round, twice.",
        "  - Steady (middle): decrease every other round.",
        "  - Round over (top): decrease every round to the final stitches.",
        f"Stop when {repeats} stitches remain and cinch the crown closed.",
    ]
    assumptions = [
        "Cast-on stitches must divide evenly by decrease repeats.",
        "Each repeat starts with at least 2 stitches so one decrease fits in each repeat.",
        "This planner models a tapered dome crown rather than a flat cone: the plain-round",
        "gap between decrease rounds shortens (2 -> 1 -> 0) as the crown narrows.",
        "The hat body is not planned here — knit it to your desired length, then work the crown.",
    ]

    sim_text, sim_plan = _sim_plan(repeats, stitches, plan)

    return {
        "repeats": repeats,
        "stitches": stitches,
        "stitches_per_repeat": stitches_per_repeat,
        "plan": plan,
        "rounds": rounds,
        "strategy": strategy,
        "assumptions": assumptions,
        "svg": _crown_svg(repeats, [stitches] + transitions),
        "svg_profile": _crown_profile_svg(stitches, plan),
        "shape_note": _shape_note(repeats, stitches, plan),
        "sim_instructions": sim_text,
        "sim_plan": sim_plan,
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
            "cast-on stitches must divide evenly by decrease repeats " f"({stitches} is not divisible by {repeats})"
        )
    if stitches < repeats * 2:
        raise ValueError(
            "cast-on stitches are too small for this strategy: " "need at least 2 stitches per repeat before decreases"
        )


def _build_plan(repeats, stitches):
    """Tapered dome schedule.

    Every decrease round removes exactly ``repeats`` stitches (one k2tog per
    marker), so the stitch count stays divisible and every repeat verifies
    against the same marker.  The number of plain rounds between decrease
    rounds shortens as the crown narrows:

    - "curve": the first two decrease rounds are worked every 3rd round
      (2 plain rounds between) while the hat is still wide, so the crown
      rises gently from the brim edge — only for hats with >= 6 stitches
      per repeat, where there is enough height to need a gradual start.
    - "steady": decrease every other round (1 plain round between) while
      more than 4x the repeats remain — the classic middle of the crown.
    - "top": decrease every round once the crown is narrow, rounding over
      quickly to the final drawstring cinch.
    """
    plan = []
    round_no = 1
    current = stitches
    per_repeat = stitches // repeats
    dec_index = 0
    gradual = stitches >= 6 * repeats

    while current - repeats > 0:
        before = current
        after = before - repeats

        if per_repeat - 2 > 0:
            instruction = f"*K{per_repeat - 2}, k2tog* around ({repeats} repeats)"
        else:
            instruction = f"*K2tog* around ({repeats} repeats)"

        if after <= repeats:
            phase, gap = "top", 0
        elif gradual and dec_index < 2:
            phase, gap = "curve", 2
        elif after > 4 * repeats:
            phase, gap = "steady", 1
        else:
            phase, gap = "top", 0

        plan.append(
            {
                "round": round_no,
                "kind": "Decrease",
                "phase": phase,
                "phase_label": _PHASE_LABELS[phase],
                "before": before,
                "after": after,
                "transition": f"{before} -> {after}",
                "instruction": instruction,
                "per_repeat_before": per_repeat,
                "per_repeat_after": per_repeat - 1,
            }
        )
        for _ in range(gap):
            round_no += 1
            plan.append(
                {
                    "round": round_no,
                    "kind": "Knit even",
                    "phase": phase,
                    "phase_label": _PHASE_LABELS[phase],
                    "before": after,
                    "after": after,
                    "transition": f"{after} -> {after}",
                    "instruction": "Knit 1 round even (no decreases)",
                    "per_repeat_before": per_repeat - 1,
                    "per_repeat_after": per_repeat - 1,
                }
            )
        round_no += 1
        current = after
        per_repeat -= 1
        dec_index += 1

    plan.append(
        {
            "round": round_no,
            "kind": "Finish",
            "phase": "top",
            "phase_label": _PHASE_LABELS["top"],
            "before": current,
            "after": current,
            "transition": f"{current} -> {current}",
            "instruction": ("Cut yarn, leave a tail, thread through remaining stitches, and pull closed"),
            "per_repeat_before": 1,
            "per_repeat_after": 1,
        }
    )
    return plan


def _shape_note(repeats, stitches, plan):
    """One-paragraph explanation of the dome the schedule produces, using the
    actual plain-round gaps of the computed plan."""
    gaps = []
    i = 0
    while i < len(plan):
        if plan[i]["kind"] == "Decrease":
            j = i + 1
            cnt = 0
            while j < len(plan) and plan[j]["kind"] == "Knit even":
                cnt += 1
                j += 1
            gaps.append(cnt)
            i = j
        else:
            i += 1
    gap_text = ", ".join(str(g) for g in gaps)
    return (
        f"The crown narrows like a dome, not a cone: the number of plain rounds "
        f"between decrease rounds shortens as the crown gets smaller "
        f"({gap_text}, then the drawstring cinch). With {stitches} cast-on "
        f"stitches and {repeats} repeats you hold {stitches // repeats} stitches "
        f"between markers at the start and {repeats} at the finish — every "
        f"decrease round removes exactly {repeats} stitches, so each repeat "
        f"stays easy to verify."
    )


def _crown_svg(repeats, counts):
    """Top-down crown SVG: wedge lines + concentric stitch-count rings."""
    import math

    size = 320
    cx = cy = size / 2
    outer = size / 2 - 20

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" ' f'viewBox="0 0 {size} {size}">']
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
        parts.append(f'<line x1="{cx}" y1="{cy}" x2="{x2:.1f}" y2="{y2:.1f}" ' f'stroke="#7b3fa0" stroke-width="2"/>')
        parts.append(f'<circle cx="{x2:.1f}" cy="{y2:.1f}" r="4" fill="#7b3fa0"/>')
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="6" fill="#7b3fa0"/>')
    parts.append(
        f'<text x="{cx}" y="{size - 10}" text-anchor="middle" font-size="13" '
        'fill="#5a2a75">top-down crown stitch levels: ' + (" -> ".join(str(c) for c in counts)) + "</text>"
    )
    parts.append("</svg>")
    return "\n".join(parts)


def _crown_profile_svg(stitches, plan):
    """Side profile of the crown: width = stitches on the needle, height =
    rounds worked.  Each decrease round steps the profile inward (a dot marks
    the step), and a dashed arc shows a smooth dome for comparison.  The hat
    body is drawn as a plain band below the crown."""
    W, H = 340, 230
    cx = W / 2.0
    top_y = 18.0
    crown_h = 148.0
    brim_y = top_y + crown_h
    body_h = H - brim_y
    hw_max = 106.0
    max_c = max(stitches, max(row["before"] for row in plan))

    def hw(c):
        return hw_max * c / max_c

    # one profile point per plan row (count at the start of the round), from
    # the brim (widest) up to the finish row, then the cinched tip at width 0
    pts = []
    n = len(plan)
    for i, row in enumerate(plan):
        y = brim_y - (i / max(n - 1, 1)) * crown_h
        pts.append((hw(row["before"]), y))
    pts.append((0.0, top_y - 6))

    right = "".join(" L %.1f,%.1f" % (cx + w, y) for w, y in pts)
    left = "".join(" L %.1f,%.1f" % (cx - w, y) for w, y in reversed(pts))
    silhouette = "M %.1f,%.1f%s%s Z" % (cx - pts[0][0], pts[0][1], right, left)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" ' f'viewBox="0 0 {W} {H}">',
        "<defs>",
        '<linearGradient id="hatProfGrad" x1="0" y1="0" x2="0" y2="1">',
        '<stop offset="0" stop-color="#e3d3f0"/>',
        '<stop offset="1" stop-color="#c9a7e0"/>',
        "</linearGradient>",
        "</defs>",
        # hat body (knit to your desired length before the crown)
        f'<rect x="{cx - hw_max:.1f}" y="{brim_y:.1f}" width="{2 * hw_max:.1f}" '
        f'height="{body_h:.1f}" fill="#f2eaf9" stroke="rgba(90,42,117,0.15)"/>',
        f'<text x="{cx}" y="{H - 9}" text-anchor="middle" font-size="9.5" '
        'fill="#6b6572">hat body — knit to your desired length, then work the crown above</text>',
        # smooth dome reference
        f'<path d="M {cx - hw_max:.1f},{brim_y:.1f} A {hw_max:.1f},{crown_h:.1f} 0 0 1 '
        f'{cx + hw_max:.1f},{brim_y:.1f}" fill="none" stroke="#b39bcb" '
        'stroke-width="1.4" stroke-dasharray="5 4" opacity="0.75"/>',
        # crown silhouette
        f'<path d="{silhouette}" fill="url(#hatProfGrad)" '
        'stroke="#7b3fa0" stroke-width="1.6" stroke-linejoin="round"/>',
        # decrease points + stitch-count labels (right edge of the profile)
        '<g fill="#5a2a75">',
    ]
    for i, row in enumerate(plan):
        if row["kind"] != "Decrease":
            continue
        w, y = pts[i]
        parts.append(f'<circle cx="{cx - w:.1f}" cy="{y:.1f}" r="2.6" fill="#7b3fa0"/>')
        parts.append(f'<circle cx="{cx + w:.1f}" cy="{y:.1f}" r="2.6" fill="#7b3fa0"/>')
        parts.append(
            f'<text x="{cx + w + 5:.1f}" y="{y + 3:.1f}" font-size="8" ' f'fill="#5a2a75">{row["after"]}</text>'
        )
    parts.append("</g>")
    parts.append("</svg>")
    return "\n".join(parts)


def _sim_plan(repeats, stitches, plan):
    """Executable Knit Simulator pattern + canonical sections for the crown.

    Every non-comment instruction line becomes exactly one simulation step:
    decrease rounds use the simulator's ``across`` tiling ('k8 k2tog across')
    and plain rounds are 'k all'; the drawstring cinch is represented by
    'bo all' so the simulation ends with an explicit finishing step.  The
    sections follow the schedule phases (Curve in / Steady / Round over) so
    the simulator can show phase progress with the planner's real counts.
    """
    execs = [("curve", f"co {stitches}")]
    for row in plan:
        if row["kind"] == "Finish":
            continue
        if row["kind"] == "Decrease":
            k = row["per_repeat_before"] - 2
            line = f"k{k} k2tog across" if k > 0 else "k2tog across"
        else:
            line = "k all"
        execs.append((row["phase"], line))
    execs.append(("top", "bo all"))

    lines = [
        "# Hat crown · generated by the Hat Crown Planner",
        f"# {stitches} stitches cast on, {repeats} decrease repeats " f"({stitches // repeats} per repeat).",
        "# Tapered dome: 2 plain rounds, then 1, then 0 between decrease rounds.",
        execs[0][1],
    ]
    prev_phase = execs[0][0]
    for phase, line in execs[1:]:
        if phase != prev_phase:
            lines.append(f"# {_PHASE_LABELS[phase]}")
            prev_phase = phase
        lines.append(line)

    # canonical sections: phase runs over the exec (non-comment) lines
    sections = []
    start = 0
    for i in range(1, len(execs)):
        if execs[i][0] != execs[i - 1][0]:
            sections.append(
                {
                    "id": execs[start][0],
                    "label": _PHASE_LABELS[execs[start][0]],
                    "start": start,
                    "end": i,
                }
            )
            start = i
    sections.append(
        {
            "id": execs[start][0],
            "label": _PHASE_LABELS[execs[start][0]],
            "start": start,
            "end": len(execs),
        }
    )

    sim_plan = {
        "source": "hat_planner",
        "garment": "hat",
        "instructions": "\n".join(lines) + "\n",
        "sections": sections,
        "counts": {
            "cast_on": stitches,
            "repeats": repeats,
            "per_repeat": stitches // repeats,
            "final": repeats,
            "rounds": len(plan),
        },
    }
    return sim_plan["instructions"], sim_plan


DEMO = {
    "TITLE": TITLE,
    "DEFAULT_INPUTS": DEFAULT_INPUTS,
    "compute": compute,
    "to_html": to_html,
}
