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
    sock_plan = inputs.get("sock_plan")
    if sock_plan is not None:
        return _compute_from_sock(sock_plan, inputs)

    raw = inputs.get("instructions", "")
    rows = _parse(raw)
    if not rows:
        raise ValueError("No valid instructions. Use: co, k, p, yo, k2tog, ssk, bo")

    warnings = _validate(raw)
    stitches = []
    steps = []
    row_no = 0
    cast_on = 0

    for row in rows:
        first_name, first_count = row["ops"][0]
        if first_name == "co":
            n = int(first_count)
            if not cast_on:
                cast_on = n
            stitches = list(range(1, n + 1))
            steps.append(_make_cast_on_step(n, stitches))
            continue

        row_no += 1
        width = len(stitches)
        _check_row_width(row_no, row, width, warnings)
        expanded = _expand(row["ops"], width, row["repeat"])
        new_stitches, row_ops, increases, decreases = _apply_row(expanded, stitches)
        stitches = new_stitches
        steps.append(_make_row_step(row_no, width, stitches, expanded, row, row_ops, increases, decreases))

    total = len(steps)
    row_steps = max(total - 1, 1)
    for i, step in enumerate(steps):
        step["progress"] = round(i / row_steps, 4) if total > 1 else 0.0

    speed = inputs.get("speed", "normal")
    speed_ms = SPEED_PRESETS.get(speed, 400)

    result = {
        "steps": steps,
        "total_steps": total,
        "total_rows": row_no,
        "cast_on": cast_on,
        "final_stitches": list(stitches),
        "speed_ms": speed_ms,
        "warnings": warnings,
        "garment": "sweater",
        "sock_summary": None,
        "pattern": [r["line"] for r in rows],
    }

    plan = inputs.get("plan")
    if plan is not None:
        _attach_plan(result, plan)
    return result


def _make_cast_on_step(n: int, stitches: list) -> dict:
    return {
        "op": f"cast on {n}",
        "kind": "cast_on",
        "row": 0,
        "before": 0,
        "n": n,
        "worked": 0,
        "stitches": list(stitches),
        "row_ops": [],
        "increases": 0,
        "decreases": 0,
        "progress": 0.0,
    }


def _check_row_width(row_no: int, row: dict, width: int, warnings: list) -> None:
    if not row["repeat"]:
        wanted = sum(width if count == "all" else max(int(count), 0) for _, count in row["ops"])
        if wanted > width:
            warnings.append(
                f"Row {row_no} ({row['line'].strip()}) tries to work {wanted} "
                f"stitches but only {width} are on the needle; the extra "
                "stitches were left unworked."
            )


def _make_row_step(row_no, width, stitches, expanded, row, row_ops, increases, decreases):
    return {
        "op": _row_label(expanded, row["repeat"], width),
        "kind": "bind_off" if 4 in row_ops else "row",
        "row": row_no,
        "before": width,
        "n": len(stitches),
        "worked": len(expanded),
        "stitches": list(stitches),
        "row_ops": row_ops,
        "increases": increases,
        "decreases": decreases,
        "progress": 0.0,
    }

    speed = inputs.get("speed", "normal")
    speed_ms = SPEED_PRESETS.get(speed, 400)

    result = {
        "steps": steps,
        "total_steps": total,
        "total_rows": row_no,
        "cast_on": cast_on,
        "final_stitches": list(stitches),
        "speed_ms": speed_ms,
        "warnings": warnings,
        "garment": "sweater",
        "sock_summary": None,
        "pattern": [r["line"] for r in rows],
    }

    plan = inputs.get("plan")
    if plan is not None:
        # A present-but-invalid plan must raise, never silently fall back.
        _attach_plan(result, plan)
    return result


def _attach_plan(result, plan):
    """Attach canonical garment sections from a Planner plan to the steps.

    The plan is the single source of truth for the garment structure: every
    section boundary is an index into the (non-comment) instruction lines,
    which map 1:1 onto simulation steps.  If the plan does not match the
    steps that were actually executed it raises instead of producing a
    misleading garment.
    """
    if not isinstance(plan, dict) or not plan.get("instructions"):
        raise ValueError("The sweater plan is missing its instructions.")
    sections = _validate_sections(plan.get("sections"), result["total_steps"])
    steps = result["steps"]
    for i, step in enumerate(steps):
        sec = _section_at(sections, i)
        step["section"] = sec["id"]
        step["section_label"] = sec["label"]
        step["sec_row"] = i - sec["start"] + 1
        step["sec_rows"] = sec["end"] - sec["start"]
        step["op_short"] = _short_op(step, sec["id"])
    result["sections"] = sections
    result["garment"] = str(plan.get("garment") or "raglan")
    counts = plan.get("counts")
    if isinstance(counts, dict):
        result["counts"] = dict(counts)
    return result


def _validate_sections(sections, total):
    """Validate a plan's section list against the executed step count."""
    if not isinstance(sections, list) or not sections:
        raise ValueError("The sweater plan has no garment sections.")
    cleaned = []
    prev_end = 0
    for sec in sections:
        try:
            sid = str(sec["id"])
            label = str(sec.get("label") or sid)
            start = int(sec["start"])
            end = int(sec["end"])
        except (KeyError, TypeError, ValueError):
            raise ValueError("The sweater plan contains an invalid section.")
        if start < 0 or end <= start or start != prev_end:
            raise ValueError("The sweater plan's sections do not line up.")
        cleaned.append({"id": sid, "label": label, "start": start, "end": end})
        prev_end = end
    if prev_end != total:
        raise ValueError("The sweater plan's sections do not match the simulation " "(%d steps)." % total)
    return cleaned


def _section_at(sections, index):
    for sec in sections:
        if sec["start"] <= index < sec["end"]:
            return sec
    return sections[-1]


def _short_op(step, section_id):
    """Concise, honest operation label for the phase line, derived from the
    step's own data and its garment section — never invented."""
    n = step["n"]
    if step["kind"] == "cast_on":
        return "Cast on %d sts" % n
    if step["kind"] == "bind_off":
        return "Bind off %d sts" % step["worked"]
    if step["increases"] > 0:
        if section_id == "yoke":
            return "Raglan increase (+%d)" % step["increases"]
        if section_id == "neckline":
            return "Neck increase (+%d)" % step["increases"]
        return "Increase (+%d)" % step["increases"]
    if step["decreases"] > 0:
        if section_id in ("left_sleeve", "right_sleeve"):
            return "Sleeve decrease (-%d)" % step["decreases"]
        return "Decrease (-%d)" % step["decreases"]
    if 1 in step["row_ops"]:
        return "K2 P2 ribbing"
    return "Knit all"


def _compute_from_sock(plan, inputs):
    """Build simulation steps from a Sock Calculator pattern.

    The pattern is the single source of truth: every simulation step mirrors
    exactly one round of ``plan["rounds"]`` (the cast-on edge included), so
    no operations are invented and the stitch counts stay identical to the
    calculator's.  Missing or invalid data raises a clear error instead of
    silently falling back to something incorrect.
    """
    if not isinstance(plan, dict) or plan.get("source") != "sock_calculator":
        raise ValueError(
            "The Sock Calculator data is missing or invalid. Open the Sock "
            "Calculator, run it, and click 'Simulate sock' again."
        )
    rounds = plan.get("rounds")
    if not isinstance(rounds, list) or not rounds:
        raise ValueError("The Sock Calculator pattern is empty. Re-run the Sock Calculator.")
    cast = plan.get("cast_on_stitches")
    try:
        cast_ok = cast is not None and int(rounds[0]["after"]) == int(cast)
    except (KeyError, TypeError, ValueError):
        cast_ok = False
    if not cast_ok:
        raise ValueError(
            "The Sock Calculator cast-on count is inconsistent with its " "pattern. Re-run the Sock Calculator."
        )

    steps = []
    for i, rnd in enumerate(rounds):
        try:
            before = int(rnd.get("before", rnd["after"]))
            after = int(rnd["after"])
        except (KeyError, TypeError, ValueError):
            raise ValueError("The Sock Calculator pattern contains an invalid round. " "Re-run the Sock Calculator.")
        removed = after - before
        kind = str(rnd.get("kind") or "row")
        steps.append(
            {
                "op": str(rnd.get("label") or "row"),
                "kind": "cast_on" if kind == "cast_on" else "row",
                "row": i,
                "before": before,
                "n": after,
                "worked": max(0, removed),
                "stitches": list(range(1, after + 1)),
                "row_ops": [],
                "texture": str(rnd.get("texture") or "stockinette"),
                "increases": max(0, removed),
                "decreases": max(0, -removed),
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
        "total_rows": total - 1,
        "cast_on": int(cast),
        "final_stitches": list(range(1, steps[-1]["n"] + 1)),
        "speed_ms": speed_ms,
        "warnings": [],
        "garment": "sock",
        "sock_summary": {
            "size": plan.get("size", ""),
            "gauge": plan.get("gauge", ""),
            "cast_on_stitches": int(cast),
            "ankle_stitches": plan.get("ankle_stitches"),
            "total_rounds": plan.get("total_rounds", total - 1),
        },
        "pattern": [],
    }


# --------------------------------------------------------------------------
# Parsing
# --------------------------------------------------------------------------


def _op_name(token):
    """Strip trailing digits so 'k2' -> 'k' but 'k2tog' stays 'k2tog'."""
    return token.rstrip("0123456789")


def _trailing_count(token, name):
    suffix = token[len(name) :]
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

        repeat, tokens = _extract_repeat_flag(tokens)
        ops = _parse_tokens(tokens)
        if ops:
            rows.append({"ops": ops, "repeat": repeat, "line": line})
    return rows


def _extract_repeat_flag(tokens):
    """Strip repeat markers from tokens and return (repeat, cleaned_tokens)."""
    repeat = False
    if tokens[0] == "*":
        repeat = True
        tokens = tokens[1:]
    if tokens and tokens[-1] in ("across", "rep", "repeat"):
        repeat = True
        tokens = tokens[:-1]
    return repeat, tokens


def _parse_tokens(tokens):
    """Parse a list of tokens into operation (name, count) pairs."""
    ops = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        name = _op_name(tok)
        canonical = _OP_NAMES.get(name)
        if canonical is None:
            i += 1
            continue
        count, j = _resolve_count(tok, name, canonical, tokens, i + 1)
        i = j
        ops.append((canonical, count))
    return ops


def _resolve_count(tok, name, canonical, tokens, j):
    """Resolve the count for a token, handling trailing digits and keywords."""
    count = _trailing_count(tok, name)
    if count is not None:
        return count, j
    if canonical in ("co", "bo") and j < len(tokens) and tokens[j] in ("on", "off"):
        j += 1
    if j < len(tokens) and tokens[j] == "all":
        return "all", j + 1
    if j < len(tokens) and tokens[j].isdigit():
        return int(tokens[j]), j + 1
    return 1, j


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
        chunk = stitches[pos : pos + op["consume"]]
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
    lines = [line.strip() for line in raw.strip().split("\n") if line.strip() and not line.strip().startswith("#")]
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
