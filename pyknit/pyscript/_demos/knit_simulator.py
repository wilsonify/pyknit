"""Knit Simulator demo: visualize knitting step by step.

Accepts simple instructions and produces a step-by-step log that the
JavaScript player renders as SVG stitch loops on a needle.
"""

import json

DEFAULT_INPUTS = {
    "instructions": "co 10\n* k2 p2 across\nk all",
}

TITLE = "Knit Simulator"

SPEED_PRESETS = {
    "slow": 800,
    "normal": 400,
    "fast": 150,
}


def compute(inputs):
    raw = inputs.get("instructions", "")
    steps = _parse(raw)
    if not steps:
        raise ValueError("No valid instructions. Use: co, k, p, k2tog, ssk, yo, bo")

    stitches = []
    row_type = None
    log = []

    for step in steps:
        op = step["op"]
        count = step.get("count", 1)

        if op == "co":
            stitches = list(range(1, count + 1))
            log.append({"op": "cast on", "n": len(stitches), "stitches": list(stitches)})

        elif op == "knit":
            row_type = "knit"
            log.append({"op": "knit", "n": len(stitches), "stitches": list(stitches)})

        elif op == "purl":
            row_type = "purl"
            log.append({"op": "purl", "n": len(stitches), "stitches": list(stitches)})

        elif op == "yo":
            stitches.append(0)
            log.append({"op": "yarn over", "n": len(stitches), "stitches": list(stitches)})

        elif op == "k2tog":
            if len(stitches) >= 2:
                stitches = stitches[:-2] + [stitches[-1]]
            log.append({"op": "k2tog", "n": len(stitches), "stitches": list(stitches)})

        elif op == "ssk":
            if len(stitches) >= 2:
                stitches = stitches[2:] + [stitches[0]]
            log.append({"op": "ssk", "n": len(stitches), "stitches": list(stitches)})

        elif op == "bo":
            n_bo = min(count, len(stitches))
            stitches = stitches[n_bo:]
            log.append({"op": "bind off", "n": len(stitches), "stitches": list(stitches)})

    if not log:
        raise ValueError("No steps produced. Check your instructions.")

    warnings = _validate(raw)
    speed = inputs.get("speed", "normal")
    speed_ms = SPEED_PRESETS.get(speed, 400)

    return {
        "steps": log,
        "total_steps": len(log),
        "final_stitches": list(stitches),
        "speed_ms": speed_ms,
        "warnings": warnings,
    }


def _parse(raw):
    ops = []
    for line in raw.strip().split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.lower().split()
        if not parts:
            continue
        repeat = parts[0] == "*"
        if repeat:
            parts = parts[1:]
            if not parts:
                continue
        op = parts[0]
        count = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 1
        if op in ("co", "cast", "caston"):
            ops.append({"op": "co", "count": count})
        elif op in ("knit", "k"):
            ops.append({"op": "knit", "count": count, "repeat": repeat})
        elif op in ("purl", "p"):
            ops.append({"op": "purl", "count": count, "repeat": repeat})
        elif op == "yo":
            ops.append({"op": "yo"})
        elif op == "k2tog":
            ops.append({"op": "k2tog"})
        elif op == "ssk":
            ops.append({"op": "ssk"})
        elif op in ("bo", "bindoff", "bind off"):
            ops.append({"op": "bo", "count": count})
    return ops


def _validate(raw):
    warnings = []
    lines = [l.strip() for l in raw.strip().split("\n") if l.strip() and not l.strip().startswith("#")]
    if not lines:
        return ["No instructions provided."]
    first = lines[0].lower().split()
    if not first or first[0] not in ("co", "cast", "caston"):
        warnings.append("Instructions should start with a cast-on (co 20).")
    return warnings


def to_html(result):
    parts = []
    parts.append(
        "<div class='stat-row'>"
        f"<span class='stat-pill'>Steps: <em>{result['total_steps']}</em></span>"
        f"<span class='stat-pill'>Stitches: <em>{len(result['final_stitches'])}</em></span>"
        "</div>"
    )
    if result.get("warnings"):
        items = "".join(f"<li>{_esc(w)}</li>" for w in result["warnings"])
        parts.append(f"<div class='warning-box'><strong>Heads up</strong><ul>{items}</ul></div>")
    parts.append("<p class='field-hint'>Use the simulation controls above to play through each step.</p>")
    return "\n".join(parts)


def _esc(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


DEMO = {
    "TITLE": TITLE,
    "DEFAULT_INPUTS": DEFAULT_INPUTS,
    "compute": compute,
    "to_html": to_html,
}
