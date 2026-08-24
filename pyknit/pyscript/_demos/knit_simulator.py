"""Knit Simulator demo: visualize knitting step by step as a wearable garment.

The pipeline is deliberately simple and honest:

    pattern (instructions text)
      -> rows / operations (one step per knitted row)
      -> garment progress (0..1 per step, driven by rows completed)
      -> SVG garment rendering (JS side of the demo page)

Each instruction line becomes one step.  Rows never invent operations:
``k2 p2 across`` expands to the exact sequence of knit/purl stitches across
the current stitch count, and the stitch count only changes when an
instruction explicitly changes it (yo, k2tog, ssk, bo).
"""

import json

DEFAULT_INPUTS = {
    "instructions": "co 10\nk2 p2 across\nk2 p2 across\nk all",
}

TITLE = "Knit Simulator"

SPEED_PRESETS = {
    "slow": 800,
    "normal": 400,
    "fast": 150,
}

# Per-unit-operation semantics: how many stitches each op consumes from the
# left needle and produces onto the right needle, plus the row texture code
# the JS renderer uses (0 knit, 1 purl, 2 increase, 3 decrease, 4 bind off).
_OPS = {
    "knit": {"consume": 1, "produce": 1, "code": 0, "short": "k"},
    "purl": {"consume": 1, "produce": 1, "code": 1, "short": "p"},
    "yo": {"consume": 0, "produce": 1, "code": 2, "short": "yo"},
    "k2tog": {"consume": 2, "produce": 1, "code": 3, "short": "k2tog"},
    "ssk": {"consume": 2, "produce": 1, "code": 3, "short": "ssk"},
    "bo": {"consume": 1, "produce": 0, "code": 4, "short": "bo"},
}

_OP_NAMES = {
    "k": "knit",
    "knit": "knit",
    "p": "purl",
    "purl": "purl",
    "yo": "yo",
    "k2tog": "k2tog",
    "ssk": "ssk",
    "bo": "bo",
    "bind": "bo",
    "bindoff": "bo",
    "bind_off": "bo",
    "co": "co",
    "cast": "co",
    "caston": "co",
    "cast_on": "co",
}


def compute(inputs):
    raw = inputs.get("instructions", "")
    rows = _parse(raw)
    if not rows:
        raise ValueError("No valid instructions. Use: co, k, p, yo, k2tog, ssk, bo")

    warnings = _validate(raw)

    stitches = []  # stitch ids currently on the needle
    steps = []
    row_no = 0
    cast_on = 0

    for row in rows:
        first_name, first_count = row["ops"][0]
        if first_name == "co":
            n = int(first_count)
            cast_on = n
            stitches = list(range(1, n + 1))
            steps.append(
                {
                    "op": f"cast on {n}",
                    "kind": "cast_on",
                    "row": 0,
                    "n": n,
                    "worked": 0,
                    "stitches": list(stitches),
                    "row_ops": [],
                    "increases": 0,
                    "decreases": 0,
                    "progress": 0.0,
                }
            )
            continue

        row_no += 1
        width = len(stitches)
        expanded = _expand(row["ops"], width, row["repeat"])
        new_stitches, row_ops, increases, decreases = _apply_row(expanded, stitches)
        stitches = new_stitches

        steps.append(
            {
                "op": _row_label(expanded, row["repeat"], width),
                "kind": "bind_off" if 4 in row_ops else "row",
                "row": row_no,
                "n": len(stitches),
                "worked": len(expanded),
                "stitches": list(stitches),
                "row_ops": row_ops,
                "increases": increases,
                "decreases": decreases,
                "progress": 0.0,
            }
        )

    total = len(steps)
    row_steps = max(total - 1, 1)
    for i, step in enumerate(steps):
        step["progress"] = round(i / row_steps, 4) if total > 1 else 0.0

    speed = inputs.get("speed", "normal")
    speed_ms = SPEED_PRESETS.get(speed, 400)

    return {
        "steps": steps,
        "total_steps": total,
        "total_rows": row_no,
        "cast_on": cast_on,
        "final_stitches": list(stitches),
        "speed_ms": speed_ms,
        "warnings": warnings,
        "pattern": [r["line"] for r in rows],
    }


# --------------------------------------------------------------------------
# Parsing
# --------------------------------------------------------------------------


def _op_name(token):
    """Strip trailing digits so 'k2' -> 'k' but 'k2tog' stays 'k2tog'."""
    return token.rstrip("0123456789")


def _trailing_count(token, name):
    suffix = token[len(name):]
    return int(suffix) if suffix.isdigit() else None


def _parse(raw):
    """Parse instruction text into a list of row dicts.

    Each row dict has ``ops`` (list of (op_name, count) pairs), ``repeat``
    (bool: whether the row repeats across the stitch count), and ``line``
    (the original text, for display).
    """
    rows = []
    for line in raw.strip().split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        tokens = line.lower().split()
        if not tokens:
            continue

        repeat = False
        if tokens[0] == "*":
            repeat = True
            tokens = tokens[1:]
        if tokens and tokens[-1] in ("across", "rep", "repeat"):
            repeat = True
            tokens = tokens[:-1]
        if not tokens:
            continue

        ops = []
        i = 0
        while i < len(tokens):
            tok = tokens[i]
            name = _op_name(tok)
            canonical = _OP_NAMES.get(name)
            if canonical is None:
                i += 1
                continue

            count = _trailing_count(tok, name)
            j = i + 1
            if count is None:
                # support "cast on 10", "bind off 5", "k all", "k 10"
                if canonical in ("co", "bo") and j < len(tokens) and tokens[j] in ("on", "off"):
                    j += 1
                if j < len(tokens) and tokens[j] == "all":
                    count = "all"
                    j += 1
                elif j < len(tokens) and tokens[j].isdigit():
                    count = int(tokens[j])
                    j += 1
                else:
                    count = 1
            i = j
            ops.append((canonical, count))

        if ops:
            rows.append({"ops": ops, "repeat": repeat, "line": line})
    return rows


def _expand(ops, width, repeat):
    """Expand row ops into a flat list of unit operations, clamped to the
    current stitch count.  ``across``/``*`` rows tile their sequence until
    the row is full; plain rows work exactly the stitches they name."""
    flat = []
    for name, count in ops:
        if count == "all":
            count = width
        for _ in range(max(int(count), 0)):
            flat.append(name)
    if not flat or width <= 0:
        return []

    out = []
    pos = 0
    if repeat:
        idx = 0
        n_flat = len(flat)
        while pos < width:
            name = flat[idx % n_flat]
            consume = _OPS[name]["consume"]
            if pos + consume > width:
                break
            out.append(name)
            pos += consume
            idx += 1
    else:
        for name in flat:
            consume = _OPS[name]["consume"]
            if pos + consume > width:
                break
            out.append(name)
            pos += consume
    return out


def _apply_row(expanded, stitches):
    """Work one expanded row across the needle.

    Returns ``(new_stitches, row_ops, increases, decreases)`` where
    ``row_ops`` is parallel to the *original* stitch row: 0 knit, 1 purl,
    2 increase, 3 decrease, 4 bind off, -1 not worked.
    """
    new_stitches = []
    row_ops = [-1] * len(stitches)
    next_id = max(stitches, default=0) + 1
    pos = 0
    increases = 0
    decreases = 0
    for name in expanded:
        op = _OPS[name]
        if op["consume"] == 0:
            # increase (yo): adds a new stitch before the current position
            new_stitches.append(next_id)
            next_id += 1
            if pos < len(row_ops):
                row_ops[pos] = 2
            increases += 1
            continue
        if pos + op["consume"] > len(stitches):
            break
        chunk = stitches[pos:pos + op["consume"]]
        pos += op["consume"]
        if op["produce"] == 1:
            # a decrease merges the consumed stitches into one
            new_stitches.append(chunk[-1] if name in ("k2tog", "ssk") else chunk[0])
        for j in range(op["consume"]):
            row_ops[pos - op["consume"] + j] = op["code"]
        if name in ("k2tog", "ssk"):
            decreases += 1
    # stitches that were never worked stay on the needle
    new_stitches.extend(stitches[pos:])
    return new_stitches, row_ops, increases, decreases


def _row_label(expanded, repeat, width):
    """Human label for a worked row, e.g. 'k2 p2 k2 p2 k2 across'."""
    if not expanded:
        return "no stitches worked"
    n = len(expanded)
    uniform = all(name == expanded[0] for name in expanded)
    if uniform and expanded[0] == "bo":
        return f"bind off {n}"
    if uniform and not repeat and n == width:
        friendly = {"knit": "knit all", "purl": "purl all"}
        if expanded[0] in friendly:
            return friendly[expanded[0]]
    parts = []
    cur = expanded[0]
    cnt = 0
    for name in expanded + [None]:
        if name == cur:
            cnt += 1
        else:
            short = _OPS[cur]["short"]
            if len(short) == 1:
                parts.append(short if cnt == 1 else f"{short}{cnt}")
            else:
                parts.extend([short] * cnt)
            cur = name
            cnt = 1
    label = " ".join(parts)
    if repeat:
        label += " across"
    return label


def _validate(raw):
    warnings = []
    lines = [
        l.strip()
        for l in raw.strip().split("\n")
        if l.strip() and not l.strip().startswith("#")
    ]
    if not lines:
        return ["No instructions provided."]
    first = lines[0].lower().split()
    if not first or _op_name(first[0]) not in ("co", "cast", "caston", "cast_on"):
        warnings.append("Instructions should start with a cast-on (co 20).")
    return warnings


def to_html(result):
    parts = []
    parts.append(
        "<div class='stat-row'>"
        f"<span class='stat-pill'>Steps: <em>{result['total_steps']}</em></span>"
        f"<span class='stat-pill'>Rows: <em>{result['total_rows']}</em></span>"
        f"<span class='stat-pill'>Stitches: <em>{len(result['final_stitches'])}</em></span>"
        "</div>"
    )
    if result.get("warnings"):
        items = "".join(f"<li>{_esc(w)}</li>" for w in result["warnings"])
        parts.append(f"<div class='warning-box'><strong>Heads up</strong><ul>{items}</ul></div>")
    parts.append("<p class='field-hint'>Use the simulation controls above to play through each row.</p>")
    return "\n".join(parts)


def _esc(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


DEMO = {
    "TITLE": TITLE,
    "DEFAULT_INPUTS": DEFAULT_INPUTS,
    "compute": compute,
    "to_html": to_html,
}
