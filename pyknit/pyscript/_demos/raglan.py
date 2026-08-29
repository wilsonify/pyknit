"""Raglan Sweater demo: a complete top-down raglan sweater planner.

Turns a gauge plus simple body measurements (neck, bust, ease, upper arm,
wrist, underarm, body and sleeve lengths) into a full, actionable knitting
plan: cast-on, raglan marker setup, an increase schedule with per-round
stitch transitions, sleeve separation, body, hem, sleeve shaping and cuff.

All the heavy lifting is delegated to existing pyknit calculations:

* :func:`pyknit.raglan_increases` for the neck increase row + marker setup
* :func:`pyknit.increase_evenly` (via raglan_increases) for neck rounding
* :func:`pyknit.sleeve_decreases` for the sleeve taper schedule
* :func:`pyknit.GaugeSwatch.GaugeSwatch` for measurement <-> stitch math

The module only assembles those results into a plan and renders it.
"""

import html
import math
import re

from pyknit import _calculate_spacing, raglan_increases, sleeve_decreases
from pyknit.GaugeSwatch import GaugeSwatch

DEFAULT_INPUTS = {
    # gauge
    "stitches_per_inch": 5,
    "rows_per_inch": 6.5,
    # body measurements (inches)
    "neck_circumference": 14,
    "bust_circumference": 34,
    "ease": 2,
    "underarm_width": 2,
    # sleeve measurements (inches)
    "upper_arm_circumference": 12,
    "upper_arm_ease": 1,
    "wrist_circumference": 7.5,
    # lengths (inches)
    "body_length": 13,
    "sleeve_length": 17,
    # construction preferences
    "increases_per_round": 8,
    "increase_frequency": "every_other_round",
}

TITLE = "Raglan Sweater"

# standard edging depths (inches) used throughout the plan
COLLAR_IN = 1.0
HEM_IN = 1.5
CUFF_IN = 1.5
# the transitions table stops at this many rows on screen; the exported
# pattern always contains the complete schedule
MAX_TABLE_ROWS = 60

# Repeated instruction fragments
_K_ALL = "k all"
_K2_P2_RIB = "k2 p2 across"
_CO_FMT = "co %d"
_SVG_CLOSE = "</svg>"

ALLOWED_INCREASES = {4, 8, 12, 16, 20, 24}
ALLOWED_FREQUENCIES = ("every_round", "every_other_round")


def _num(x):
    "Format a float compactly (80.0 -> '80', 7.0769 -> '7.08')." ""
    if isinstance(x, int):
        return str(x)
    x = round(x, 2)
    return ("%.2f" % x).rstrip("0").rstrip(".")


def _pos(inputs, key, label):
    raw = inputs.get(key)
    try:
        value = float(raw)
    except (TypeError, ValueError):
        raise ValueError(f"{label} must be a number")
    if value <= 0:
        raise ValueError(f"{label} must be positive")
    return value


def _even(n):
    "Round an integer up/down to the nearest even number." ""
    n = int(round(n))
    return n if n % 2 == 0 else n + 1


def _freq_phrase(freq):
    return "every round" if freq == "every_round" else "every other round"


def _sleeve_generate_schedule(rows, num_dec):
    """Evenly-spaced decrease positions for a sleeve taper (after mode).

    Uses the same :func:`pyknit._calculate_spacing` core as
    ``pyknit.sleeve_decreases`` so the Planner's display and the Knit
    Simulator's executable rows stay identical.  Returns 0-indexed row
    numbers where decrease rows occur; plain rows fill the gaps so
    ``len(schedule) + plain == rows``.
    """
    if num_dec <= 0:
        return []
    padding = rows - num_dec
    if padding < 0:
        return list(range(num_dec))
    plan = _calculate_spacing(padding, num_dec, "after")
    schedule = []
    pos = 0
    for interval, groups in plan:
        for _ in range(groups):
            schedule.append(pos)
            pos += 1 + interval
    return schedule


def _sleeve_row(idx, current, dec_set, schedule, arm, wrist, per_row, remainder):
    if idx not in dec_set:
        return "Plain", current, f"Knit plain ({current} sts)"
    dec_idx = len([r for r in schedule if r <= idx])
    if dec_idx == len(schedule) and remainder:
        return "Decrease", wrist, (f"Decrease row: k2tog at each side plus {remainder} extra k2tog -> {wrist} sts")
    after = arm - dec_idx * per_row
    if after < wrist:
        after = wrist
    instruction = f"Decrease row: k2tog at each side of underarm marker ({per_row} sts removed) -> {after} sts"
    return "Decrease", after, instruction


def _sleeve_detail(arm, wrist, shaping_rounds):
    """Build a knittable sleeve decrease schedule from measured inputs.

    Returns a dict with the exact fields the knitter needs plus the
    full row-by-row plan (``rows``) that preserves ``shaping_rounds``.
    """
    total_dec = arm - wrist
    per_row = 2
    num_dec = total_dec // per_row
    remainder = total_dec % per_row
    schedule = _sleeve_generate_schedule(shaping_rounds, num_dec)
    decrease_numbers = [r + 1 for r in schedule]
    spacing = (shaping_rounds - num_dec) / max(num_dec, 1) if num_dec else 0
    # Full row-by-row plan: one entry per knitted round
    dec_set = set(schedule)
    rows = []
    current = arm
    for idx in range(shaping_rounds):
        before = current
        kind, after, instruction = _sleeve_row(idx, current, dec_set, schedule, arm, wrist, per_row, remainder)
        current = after
        rows.append(
            {
                "round": idx + 1,
                "kind": kind,
                "before": before,
                "after": after,
                "transition": f"{before} -> {after}",
                "instruction": instruction,
            }
        )
    if rows and rows[-1]["after"] != wrist:
        rows[-1]["after"] = wrist
        rows[-1]["transition"] = f"{rows[-1]['before']} -> {wrist}"
    return {
        "starting": arm,
        "ending": wrist,
        "total_rows": shaping_rounds,
        "num_dec_rounds": num_dec,
        "per_row": per_row,
        "remainder": remainder,
        "spacing": spacing,
        "schedule": schedule,
        "decrease_numbers": decrease_numbers,
        "rows": rows,
    }


def _section(heading, intro=None, steps=None, rows=None, table=None, collapsible=False):
    section = {"heading": heading}
    if intro:
        section["intro"] = intro
    if steps:
        section["steps"] = steps
    if rows:
        section["rows"] = rows
    if table:
        section["table"] = table
    if collapsible:
        section["collapsible"] = True
    return section


def _validate_inputs(params: dict) -> None:
    """Validate all raglan parameters in one place."""
    ease = params["ease"]
    upper_arm_ease = params["upper_arm_ease"]
    inc = params["inc"]
    freq = params["freq"]
    neck_circ = params["neck_circ"]
    bust_circ = params["bust_circ"]
    upper_arm_eased = params["upper_arm_eased"]
    wrist_circ = params["wrist_circ"]
    neck = params["neck"]
    bust = params["bust"]
    arm = params["arm"]
    wrist = params["wrist"]
    needed = params["needed"]
    inc_rounds = params["inc_rounds"]
    front_start = params["front_start"]
    back_start = params["back_start"]
    sleeve_start = params["sleeve_start"]
    checks = [
        (ease < -4 or ease > 10, "ease must be between -4 and 10 inches"),
        (upper_arm_ease < -2 or upper_arm_ease > 6, "upper arm ease must be between -2 and 6 inches"),
        (
            inc not in ALLOWED_INCREASES,
            "increases per round must be one of " + ", ".join(str(n) for n in sorted(ALLOWED_INCREASES)),
        ),
        (freq not in ALLOWED_FREQUENCIES, "increase frequency must be 'every round' or 'every other round'"),
        (
            neck_circ >= bust_circ,
            "neck circumference must be smaller than the bust circumference (the raglan widens from the neck down)",
        ),
        (upper_arm_eased >= bust_circ, "upper arm circumference + ease must be smaller than the bust circumference"),
        (
            wrist_circ >= upper_arm_eased,
            "wrist circumference must be smaller than the upper arm (with ease) for a tapering sleeve",
        ),
        (min(neck, bust, arm) < 4, "the neck/bust/arm measurements are too small for a sweater"),
        (
            wrist >= arm,
            "the wrist rounds up to the upper-arm count, leaving no room for "
            "sleeve shaping; use a smaller wrist measurement or add negative ease",
        ),
        (
            needed <= 0,
            "the finished bust/arm stitches must be larger than the neck cast-on; check your measurements",
        ),
        (
            inc_rounds < 1,
            "not enough stitches between the neck and underarm to schedule "
            "raglan increases; increase the increases per round or the "
            "difference between neck and bust",
        ),
    ]
    for bad, msg in checks:
        if bad:
            raise ValueError(msg)
    if min(front_start, back_start, sleeve_start) < 1:
        worst = min(front_start, back_start, sleeve_start)
        raise ValueError(
            f"The neck cast-on ({neck} sts) is too small for the bust and "
            f"arm measurements: the smallest raglan section would start at "
            f"{worst} stitches. Increase the neck circumference (a wider "
            "neckline), widen the underarm cast-on, or reduce ease/bust so "
            "the increases can distribute evenly."
        )


def _build_raglan_tables(rounds, freq, inc, seg, calc_neck, front_start, back_start, sleeve_start):
    table_rows = []
    text_rows = []
    total = calc_neck
    fr, ba, sl = front_start, back_start, sleeve_start
    for r in range(1, rounds + 1):
        if freq == "every_round" or r % 2 == 1:
            total += inc
            fr += seg
            ba += seg
            sl += seg
            action = "increase"
        else:
            action = "plain"
        table_rows.append([r, action, total, fr, ba, sl])
        text_rows.append(f"Round {r}: {action} -> {total} sts total (front {fr}, back {ba}, sleeve {sl} each)")
    return table_rows, text_rows


def _build_warnings(depth_in, sleeve_shaping_rounds, arm, wrist):
    warnings = []
    if depth_in < 4:
        warnings.append(
            f"The raglan depth is only {_num(depth_in)} in (neck to underarm), "
            "which gives a high underarm. Add ease or increase the increases "
            "per round if you want a roomier fit."
        )
    if depth_in > 11:
        warnings.append(
            f"The raglan depth is {_num(depth_in)} in (neck to underarm), which "
            "is quite deep; the sleeves may be harder to move in. Consider "
            "increasing the increases per round."
        )
    dec_rows = (arm - wrist) // 2
    if dec_rows > 0:
        avg_gap = sleeve_shaping_rounds / dec_rows
        if avg_gap < 2:
            warnings.append(
                f"The sleeve decreases are scheduled about {_num(avg_gap)} "
                "rounds apart, which is a steep taper; a roomier wrist or a "
                "shorter sleeve length will shape more gently."
            )
    return warnings


def compute(inputs):
    "Build the complete sweater plan as a dict, reusing pyknit math." ""
    st = _pos(inputs, "stitches_per_inch", "stitch gauge")
    rg = _pos(inputs, "rows_per_inch", "row gauge")
    neck_circ = _pos(inputs, "neck_circumference", "neck circumference")
    bust_circ = _pos(inputs, "bust_circumference", "bust circumference")
    ease = float(inputs.get("ease") or 0)
    underarm_w = _pos(inputs, "underarm_width", "underarm width")
    upper_arm = _pos(inputs, "upper_arm_circumference", "upper arm circumference")
    upper_arm_ease = float(inputs.get("upper_arm_ease") or 0)
    upper_arm_eased = upper_arm + upper_arm_ease
    wrist_circ = _pos(inputs, "wrist_circumference", "wrist circumference")
    body_len = _pos(inputs, "body_length", "body length")
    sleeve_len = _pos(inputs, "sleeve_length", "sleeve length")
    inc = int(inputs.get("increases_per_round", 8))
    freq = str(inputs.get("increase_frequency", "every_other_round"))

    # Gauge <-> measurement math goes through GaugeSwatch.
    swatch = GaugeSwatch(
        stitch_count=st,
        stitch_measure=1.0,
        row_count=rg,
        row_measure=1.0,
        units="in",
    )
    neck = _even(swatch.measurement_to_stitches(neck_circ))
    bust = _even(swatch.measurement_to_stitches(bust_circ + ease))
    arm = _even(swatch.measurement_to_stitches(upper_arm_eased))
    armpit = max(2, _even(swatch.measurement_to_stitches(underarm_w)))
    wrist = _even(swatch.measurement_to_stitches(wrist_circ))

    # Raglan arithmetic mirrors pyknit.raglan_increases:
    # working = live stitches at the underarm (body + sleeves)
    #         = bust + 2*arm - 4*armpit  (armpit counted twice)
    working = bust + 2 * arm - 4 * armpit
    needed = working - neck
    inc_rounds = needed // inc
    pre = needed % inc
    calc_neck = neck + pre

    # The per-section starting counts (identical math to raglan_increases):
    # each increase round adds inc/4 stitches to each of the four sections,
    # so back out that growth to get the marker counts.
    seg = inc // 4  # stitches added to each section per increase round
    body_start = bust / 2 - inc_rounds * seg - armpit
    front_start = math.ceil(body_start)
    back_start = math.floor(body_start)
    sleeve_start = arm - armpit - inc_rounds * seg

    _validate_inputs({
        "ease": ease,
        "upper_arm_ease": upper_arm_ease,
        "inc": inc,
        "freq": freq,
        "neck_circ": neck_circ,
        "bust_circ": bust_circ,
        "upper_arm_eased": upper_arm_eased,
        "wrist_circ": wrist_circ,
        "neck": neck,
        "bust": bust,
        "arm": arm,
        "wrist": wrist,
        "needed": needed,
        "inc_rounds": inc_rounds,
        "front_start": front_start,
        "back_start": back_start,
        "sleeve_start": sleeve_start,
    })

    try:
        raglan = raglan_increases(
            neck,
            arm_stitches=arm,
            bust_stitches=bust,
            neck_to_bust_rows=inc_rounds,
            increase_per_increase_row=inc,
            armpit_stitches=armpit,
        )
    except ValueError as exc:
        raise ValueError("The measurements produce a raglan that cannot be distributed evenly. " + str(exc))

    match_marker = re.search(r"Marker setup:\s*(.*)", raglan)
    marker = match_marker.group(1).strip() if match_marker else ""
    match_incrow = re.search(r"Increase row:\s*([^M]*)Marker setup:", raglan)
    inc_row_str = match_incrow.group(1).strip() if match_incrow else ""

    raglan_total_rounds = inc_rounds if freq == "every_round" else 2 * inc_rounds
    depth_in = raglan_total_rounds / rg

    front_final = front_start + inc_rounds * seg
    back_final = back_start + inc_rounds * seg
    sleeve_final = sleeve_start + inc_rounds * seg

    # Lengths from the row gauge.
    collar_rounds = max(4, round(COLLAR_IN * rg))
    hem_rounds = max(4, round(HEM_IN * rg))
    cuff_rounds = max(4, round(CUFF_IN * rg))
    body_total_rounds = round(body_len * rg)
    if body_total_rounds <= hem_rounds:
        raise ValueError(
            f"body length ({_num(body_len)} in) is too short for a {HEM_IN:g} in hem; add length or shorten the hem"
        )
    body_stock_rounds = body_total_rounds - hem_rounds
    sleeve_total_rounds = round(sleeve_len * rg)
    if sleeve_total_rounds <= cuff_rounds:
        raise ValueError(f"sleeve length ({_num(sleeve_len)} in) is too short to include a {CUFF_IN:g} in cuff")
    sleeve_shaping_rounds = sleeve_total_rounds - cuff_rounds

    try:
        sleeve_sched = sleeve_decreases(
            sleeve_shaping_rounds,
            starting_count=arm,
            ending_count=wrist,
            decrease_per_row=2,
        )
    except ValueError as exc:
        raise ValueError("Cannot shape the sleeve to the wrist: " + str(exc))

    # Detailed sleeve decrease schedule that preserves the total row count
    # and distributes decreases evenly (used for the Planner display and the
    # Knit Simulator's per-row instructions).
    sleeve_detail = _sleeve_detail(arm, wrist, sleeve_shaping_rounds)

    # Build the per-round transition schedule.
    display_rounds = raglan_total_rounds
    table_rows, text_rows = _build_raglan_tables(
        raglan_total_rounds,
        freq,
        inc,
        seg,
        calc_neck,
        front_start,
        back_start,
        sleeve_start,
    )

    # Warnings for geometry that is usable but worth a second look.
    warnings = _build_warnings(depth_in, sleeve_shaping_rounds, arm, wrist)

    sections = [
        _math_section(locals()),
        _measurements_section(locals()),
        _cast_on_section(inc_row_str, calc_neck, neck, collar_rounds, rg),
        _marker_section(marker, front_start, back_start, sleeve_start, calc_neck, inc, seg, freq),
        _increase_schedule_section(
            inc_rounds,
            freq,
            inc,
            seg,
            working,
            front_final,
            back_final,
            sleeve_final,
            pre,
            table_rows,
            text_rows,
        ),
        _separation_section(front_final, back_final, sleeve_final, armpit, bust, arm),
        _body_section(body_stock_rounds, rg, body_len),
        _hem_section(hem_rounds, rg, body_len),
        _sleeve_section(
            sleeve_final,
            armpit,
            arm,
            sleeve_shaping_rounds,
            rg,
            sleeve_sched,
            wrist,
            sleeve_len,
            sleeve_detail,
        ),
        _cuff_section(cuff_rounds, rg, sleeve_len),
    ]

    assumptions = [
        "This is a seamless, top-down raglan knit in the round: cast on at the "
        "neck, increase along four seams, then split for the body and sleeves.",
        f"There are four raglan seams with {inc} increases per increase round "
        f"({seg} to each section), so the stitch counts stay balanced.",
        f"Positive ease of {_num(ease)} in at the bust; the sleeve is knit at "
        f"the measured upper arm circumference plus {_num(upper_arm_ease)} in "
        "of ease.",
        f"The collar is about {COLLAR_IN:g} in of ribbing, and the hem and cuffs about {HEM_IN:g} in each.",
        "Underarm cast-on stitches are shared: they join the front and back "
        "for the body and are picked up again for each sleeve.",
        f"The raglan increases are worked {_freq_phrase(freq)}, giving about "
        f"{_num(depth_in)} in from the neck to the underarm.",
        "Stitches come from your stitch gauge, rounds from your row gauge, "
        "both measured on a blocked stockinette swatch.",
    ]

    return {
        "plan": {
            "sections": sections,
            "assumptions": assumptions,
            "warnings": warnings,
        },
        "result": raglan,
        "svg": _sweater_svg(neck, front_final, back_final, sleeve_final, armpit, bust, depth_in),
        "_estimator_data": {
            "stitch_count": (round(bust * body_total_rounds) + round(arm * sleeve_total_rounds * 2)),
            "project_type": "sweater",
            "source": "raglan_planner",
        },
        "meta": (
            _meta := {
                "neck": neck,
                "bust": bust,
                "arm": arm,
                "armpit": armpit,
                "wrist": wrist,
                "working": working,
                "inc": inc,
                "seg": seg,
                "pre": pre,
                "calc_neck": calc_neck,
                "inc_rounds": inc_rounds,
                "raglan_total_rounds": raglan_total_rounds,
                "depth_in": depth_in,
                "front_start": front_start,
                "back_start": back_start,
                "sleeve_start": sleeve_start,
                "front_final": front_final,
                "back_final": back_final,
                "sleeve_final": sleeve_final,
                "collar_rounds": collar_rounds,
                "body_stock_rounds": body_stock_rounds,
                "hem_rounds": hem_rounds,
                "cuff_rounds": cuff_rounds,
                "sleeve_shaping_rounds": sleeve_shaping_rounds,
                "sleeve_sched": sleeve_sched,
                "sleeve_detail": sleeve_detail,
                "freq": freq,
                "display_rounds": display_rounds,
                "marker": marker,
                "rg": rg,
                "st": st,
                "body_len": body_len,
                "sleeve_len": sleeve_len,
            }
        ),
        "sim_instructions": (_sim_txt := _sim_instructions(_meta))[0],
        "sim_plan": {
            "source": "raglan_planner",
            "garment": "raglan",
            "instructions": _sim_txt[0],
            "sections": _sim_txt[1],
            "counts": {
                "neck": _meta["neck"],
                "calc_neck": _meta["calc_neck"],
                "working": _meta["working"],
                "bust": _meta["bust"],
                "arm": _meta["arm"],
                "armpit": _meta["armpit"],
                "wrist": _meta["wrist"],
                "collar_rounds": _meta["collar_rounds"],
                "raglan_total_rounds": _meta["raglan_total_rounds"],
                "body_stock_rounds": _meta["body_stock_rounds"],
                "hem_rounds": _meta["hem_rounds"],
                "sleeve_shaping_rounds": _meta["sleeve_shaping_rounds"],
                "cuff_rounds": _meta["cuff_rounds"],
            },
        },
    }


# ---------------------------------------------------------------------------
# Plan section builders
# ---------------------------------------------------------------------------


def _math_section(v):
    "Section 0: the visible math behind every derived number." ""

    def derived(raw, final, suffix):
        raw = int(round(raw))
        arrow = f" -> {final}" if final != raw else ""
        return f"{raw}{arrow}{suffix}"

    rows = [
        f"Gauge: {_num(v['st'])} sts/in x {_num(v['rg'])} rows/in (blocked)",
        f"Neck cast-on: {_num(v['neck_circ'])} in x {_num(v['st'])} = "
        f"{derived(v['neck_circ'] * v['st'], v['neck'], '')}",
        f"Bust: ({_num(v['bust_circ'])} + {_num(v['ease'])} in ease) x "
        f"{_num(v['st'])} = {derived((v['bust_circ'] + v['ease']) * v['st'], v['bust'], ' sts in the round')}",
        f"Upper arm: ({_num(v['upper_arm'])} + {_num(v['upper_arm_ease'])} in ease) x "
        f"{_num(v['st'])} = {derived(v['upper_arm_eased'] * v['st'], v['arm'], ' sts')}",
        f"Underarm cast-on (each side): {_num(v['underarm_w'])} in x "
        f"{_num(v['st'])} = {derived(v['underarm_w'] * v['st'], v['armpit'], ' sts')}",
        f"Wrist: {_num(v['wrist_circ'])} in x {_num(v['st'])} = "
        f"{derived(v['wrist_circ'] * v['st'], v['wrist'], ' sts')}",
        f"Raglan increases: {v['needed']} stitches between neck and underarm, "
        f"{v['inc']} per increase round -> {v['inc_rounds']} increase rounds "
        f"({_freq_phrase(v['freq'])}, {v['raglan_total_rounds']} rounds, about "
        f"{_num(v['depth_in'])} in deep)",
        f"Body: {_num(v['body_len'])} in x {_num(v['rg'])} rows/in = "
        f"{v['body_total_rounds']} rounds, minus {v['hem_rounds']} rounds of "
        f"ribbing = {v['body_stock_rounds']} stockinette rounds",
        f"Sleeve: {_num(v['sleeve_len'])} in x {_num(v['rg'])} rows/in = "
        f"{v['sleeve_total_rounds']} rounds, minus {v['cuff_rounds']} rounds "
        f"of ribbing = {v['sleeve_shaping_rounds']} shaping rounds",
    ]
    if v["pre"]:
        rows.insert(
            -1,
            f"Neck increase row: add {v['pre']} stitches before the raglan "
            f"starts, bringing the cast-on to {v['calc_neck']} stitches",
        )
    return _section(
        "0. The math behind these numbers",
        intro="Every number in this plan is derived from your gauge and "
        "measurements. The formulas are shown so you can see the reasoning "
        "and adjust if needed.",
        rows=rows,
    )


def _measurements_section(v):
    table = [
        ("Item", "Value"),
        ("Gauge", f"{_num(v['st'])} sts x {_num(v['rg'])} rows per inch"),
        ("Neck circumference", f"{_num(v['neck_circ'])} in"),
        (
            "Bust + ease",
            f"{_num(v['bust_circ'] + v['ease'])} in ({_num(v['bust_circ'])} + {_num(v['ease'])} ease)",
        ),
        ("Bust stitches (body in the round)", f"{v['bust']} sts"),
        ("Underarm cast-on", f"{v['armpit']} sts each side"),
        (
            "Upper arm + ease",
            f"{_num(v['upper_arm_eased'])} in ({_num(v['upper_arm'])} + {_num(v['upper_arm_ease'])} ease)",
        ),
        ("Upper arm (sleeve in the round)", f"{v['arm']} sts"),
        ("Wrist", f"{v['wrist']} sts"),
        ("Raglan depth (neck to underarm)", f"{_num(v['depth_in'])} in"),
        ("Body length (underarm to hem)", f"{_num(v['body_len'])} in"),
        ("Sleeve length (underarm to cuff)", f"{_num(v['sleeve_len'])} in"),
    ]
    return _section(
        "1. Gauge and finished measurements",
        intro="The finished garment, as computed from your inputs.",
        table={"columns": table[0], "rows": table[1:]},
        rows=[f"{label}: {value}" for label, value in table[1:]],
    )


def _cast_on_section(inc_row_str, calc_neck, neck, collar_rounds, rg):
    steps = [
        f"Cast on {neck} stitches using a stretchy cast-on (long-tail or "
        "German twisted) and join in the round, taking care not to twist. "
        "Place a marker for the start of the round (centre back).",
        f"Work {collar_rounds} rounds of k2, p2 ribbing for the collar (about {_num(collar_rounds / rg)} in).",
    ]
    if inc_row_str:
        steps.append(
            f"Work the neck increase round now: {inc_row_str}. This brings "
            f"the cast-on to {calc_neck} stitches so the raglan increases "
            "divide evenly between the four sections."
        )
    return _section(
        "2. Cast on and neck setup",
        intro="Start at the neckline and work downwards.",
        steps=steps,
    )


def _marker_section(marker, front_start, back_start, sleeve_start, calc_neck, inc, seg, freq):
    return _section(
        "3. Raglan marker setup",
        intro="Four seams divide the sweater into front, back and two "
        "sleeves. Place a marker on each side of every seam.",
        steps=[
            marker,
            f"You begin with {front_start} front, {back_start} back and "
            f"{sleeve_start} stitches on each sleeve ({calc_neck} stitches "
            "total).",
            f"Each increase round adds {seg} stitches to each of the four "
            f"sections ({inc} total). Knit to 1 stitch before the next "
            "marker, M1R, slip marker, knit 1, M1L, then continue to the "
            "next marker and repeat for all four seams.",
        ],
    )


def _increase_schedule_section(
    inc_rounds,
    freq,
    inc,
    seg,
    working,
    front_final,
    back_final,
    sleeve_final,
    pre,
    table_rows,
    text_rows,
):
    intro = (
        f"Work {inc_rounds} increase rounds, {_freq_phrase(freq)}, adding "
        f"{inc} stitches per increase round ({seg} to each section)."
    )
    steps = [
        f"Increase round: knit to 1 stitch before the marker, M1R, slip "
        f"marker, knit 1, M1L, knit to the next marker, and repeat for all "
        f"four seams ({inc} stitches added).",
        _freq_step(freq),
        f"After {inc_rounds} increase rounds you are at the underarm: "
        f"{working} stitches total ({front_final} front, {back_final} back, "
        f"{sleeve_final} on each sleeve).",
    ]
    if pre:
        steps.append(f"The {pre}-stitch neck increase round from section 2 is already included in these counts.")
    return _section(
        "4. Raglan increase schedule with stitch transitions",
        intro=intro,
        steps=steps,
        table={
            "columns": ["Round", "Action", "Total", "Front", "Back", "Sleeve"],
            "rows": table_rows,
        },
        rows=text_rows,
        collapsible=True,
    )


def _freq_step(freq):
    if freq == "every_round":
        return "Increase every round until the underarm."
    return "Increase on every odd round, and knit a plain round in between (increases every other round)."


def _separation_section(front_final, back_final, sleeve_final, armpit, bust, arm):
    return _section(
        "5. Sleeve separation and underarm cast-on",
        intro="Divide the work into the body and the two sleeves.",
        steps=[
            f"Knit across the {front_final} front stitches, then place the "
            f"next {sleeve_final} sleeve stitches on a holder or waste yarn.",
            f"Cast on {armpit} stitches for the underarm (a provisional or "
            "backward-loop cast-on works well) and place a marker.",
            f"Knit across the {back_final} back stitches and place the "
            f"second sleeve's {sleeve_final} stitches on a holder.",
            f"Cast on {armpit} more underarm stitches and place a marker "
            "for the new start of the round (left underarm).",
            f"You now have {bust} stitches on the needles for the body, and "
            f"{sleeve_final} stitches resting for each sleeve ({arm} once "
            "the underarm stitches are picked up).",
        ],
    )


def _body_section(body_stock_rounds, rg, body_len):
    return _section(
        "6. Body instructions",
        intro="Knit the body in the round, all stitches on the needles.",
        steps=[
            f"Knit every round in stockinette for {body_stock_rounds} rounds "
            f"from the underarm (about {_num(body_stock_rounds / rg)} in).",
            "Optional waist shaping: work a decrease round about 2 in below "
            "the underarm (k2tog around, e.g. 8-12 stitches) and an increase "
            "round again lower down, spacing them evenly around the body.",
            f"Stop at {body_len:g} in from the underarm, measured flat.",
        ],
    )


def _hem_section(hem_rounds, rg, body_len):
    return _section(
        "7. Hem instructions",
        intro="A ribbed hem keeps the bottom edge from rolling.",
        steps=[
            f"Work {hem_rounds} rounds of k2, p2 ribbing (about {_num(hem_rounds / rg)} in).",
            "Bind off loosely in pattern (a stretchy bind-off such as Jeny's "
            "surprisingly stretchy bind-off keeps the hem from pulling in).",
            f"The body measures about {_num(body_len)} in from the underarm to the hem.",
        ],
    )


def _sleeve_section(
    sleeve_final,
    armpit,
    arm,
    sleeve_shaping_rounds,
    rg,
    sleeve_sched,
    wrist,
    sleeve_len,
    sleeve_detail=None,
):
    dd = sleeve_detail or {}
    # Fallback when called from older tests
    if not dd and arm and wrist and sleeve_shaping_rounds:
        try:
            dd = _sleeve_detail(arm, wrist, sleeve_shaping_rounds)
        except Exception:
            dd = {}
    starting = dd.get("starting", arm)
    ending = dd.get("ending", wrist)
    total_rows = dd.get("total_rows", sleeve_shaping_rounds)
    num_dec = dd.get("num_dec_rounds", (arm - wrist) // 2 if arm and wrist else 0)
    per_row = dd.get("per_row", 2)
    spacing = dd.get("spacing", 0)
    dec_numbers = dd.get("decrease_numbers", [])
    rows = dd.get("rows", [])

    dec_list = ", ".join(str(n) for n in dec_numbers) if dec_numbers else "—"
    # Build a collapsible row-by-row table: one row per knitted round
    table = None
    export_rows = []
    if rows:
        table_rows = []
        for r in rows:
            table_rows.append([r["round"], r["kind"], r["transition"], r["instruction"]])
            export_rows.append(f"Row {r['round']}: {r['kind']} {r['transition']} — {r['instruction']}")
        table = {
            "columns": ["Row", "Type", "Stitches", "Instruction"],
            "rows": table_rows,
        }

    steps = [
        f"Pick up and knit {arm} stitches for the sleeve: the "
        f"{sleeve_final} held stitches plus {armpit} stitches along the "
        "underarm cast-on. Place a marker at the underarm seam.",
        f"Starting stitches: {starting} sts at the upper arm (after picking up underarm stitches).",
        f"Ending stitches: {ending} sts at the wrist (before the cuff).",
        f"Total shaping rows: {total_rows} rounds (about {_num(total_rows / rg)} in).",
        f"Number of decrease rounds: {num_dec}.",
        f"Stitches removed per decrease round: {per_row} sts (k2tog at each side of the underarm marker).",
        f"Actual row numbers where decreases occur: {dec_list} (1-indexed, ~{_num(spacing)} rows between decreases).",
        f"Classic taper string: {sleeve_sched}",
        f"Try the sweater on and adjust the sleeve length before "
        f"starting the cuff (target {_num(sleeve_len)} in from the "
        "underarm).",
    ]
    section = _section(
        "8. Sleeve instructions and shaping",
        intro="Work each sleeve the same way. The table below is a complete, row-by-row plan you can knit directly.",
        steps=steps,
        table=table,
        rows=export_rows,
        collapsible=True,
    )
    # Keep the detail dict available for tests that inspect the section
    section["sleeve_detail"] = dd
    return section


def _cuff_section(cuff_rounds, rg, sleeve_len):
    return _section(
        "9. Cuff and finishing",
        intro="Finish with a ribbed cuff, then tidy up.",
        steps=[
            f"Work {cuff_rounds} rounds of k2, p2 ribbing for the cuff (about {_num(cuff_rounds / rg)} in).",
            "Bind off loosely in pattern.",
            f"Repeat for the second sleeve. Each sleeve measures about "
            f"{_num(sleeve_len)} in from the underarm to the cuff.",
            "Weave in ends and block. Because this sweater is knitted "
            "top-down, you can adjust body and sleeve length at any point by "
            "knitting more rounds before the ribbing.",
        ],
    )


def _increase_row(width, n):
    """One row that adds exactly ``n`` stitches (yo = +1 each, like M1R/M1L),
    distributed evenly across ``width`` stitches: (72, 4) -> 'k18 yo k18 yo
    k18 yo k18 yo'.  The row works the full width and produces width + n."""
    if n <= 0:
        return _K_ALL
    base, extra = divmod(width, n)
    return " ".join("k%d yo" % (base + (1 if i < extra else 0)) for i in range(n))


def _decrease_row(width, n=2):
    """One row that removes exactly ``n`` stitches (``n`` k2togs), e.g.
    (60, 2) -> 'k28 k2tog k2tog k28': consumes 60, produces 58."""
    if n <= 0:
        return _K_ALL
    knits = width - 2 * n
    a = knits // 2
    b = knits - a
    ops = (["k%d" % a] if a else []) + ["k2tog"] * n + (["k%d" % b] if b else [])
    return " ".join(ops)


def _sleeve_schedule_rows(m):
    """Per-row schedule for one sleeve: list of ('dec'|'plain', width).

    Uses the exact same spacing math as ``pyknit.sleeve_decreases`` (plain
    rows padded after each decrease row), so the taper matches the plan the
    Planner displays: from ``arm`` down to ``wrist`` over
    ``sleeve_shaping_rounds`` rows, removing 2 stitches per decrease row."""
    total_dec = m["arm"] - m["wrist"]
    num_dec = total_dec // 2
    padding = m["sleeve_shaping_rounds"] - num_dec
    plan = _calculate_spacing(padding, num_dec, "after")
    rows = []
    w = m["arm"]
    for interval, groups in plan:
        for _ in range(groups):
            rows.append(("dec", w))
            w -= 2
            for _ in range(interval):
                rows.append(("plain", w))
    return rows


def _sim_sleeve_lines(m):
    out = []
    for sleeve_no in (1, 2):
        out.append(
            "# sleeve %d: %d sts on the needle (%d held + %d underarm pickup)"
            % (sleeve_no, m["arm"], m["arm"] - m["armpit"], m["armpit"])
        )
        out.append(_CO_FMT % m["arm"])
        for kind, wd in _sleeve_schedule_rows(m):
            out.append(_decrease_row(wd) if kind == "dec" else _K_ALL)
        out.append("# cuff: %d rounds of k2, p2 ribbing" % m["cuff_rounds"])
        for _ in range(m["cuff_rounds"]):
            out.append(_K2_P2_RIB)
        out.append("bo all")
    return out


def _sim_instructions(m):
    """Generate the executable knitting instructions for the Knit Simulator.

    Every line comes straight from the computed plan: the neck cast-on, the
    collar rounds, the neck increase (``pre``), the raglan increase schedule
    (``inc`` per increase round, plain rounds interleaved per ``freq``), the
    sleeve separation (the body continues at the plan's real ``bust`` count
    while the sleeves rest on holders), the body length in rounds, the hem,
    and each sleeve's pickup count, decrease schedule and cuff.  The
    simulator's ops map 1:1 onto the plan's real actions (yo = one +1
    increase like M1R/M1L; k2tog = one -1 sleeve decrease), so the
    simulator never invents operations.

    One structural caveat of a linear, single-needle engine: a seamless
    top-down raglan splits the yoke into body + sleeves, but a linear row
    stream cannot hold stitches aside.  The instructions therefore
    represent the separation as its own cast-on at the bust count (a
    comment says the sleeve stitches rest on holders), so every executed
    stitch count from the separation onwards matches the Planner's real
    numbers — body and hem at ``bust``, each sleeve from ``arm`` down to
    ``wrist``.

    Returns ``(text, sections)`` where ``sections`` is the canonical garment
    structure the Planner knows (neck, yoke, body, hem, left sleeve, left
    cuff, right sleeve, right cuff) with start/end indices into the
    *non-comment* instruction lines — exactly the indices the simulation
    steps will have, because every non-comment instruction line becomes
    precisely one step.
    """
    lines = [
        "# Raglan sweater · generated by the Raglan Sweater Planner",
        "# Top-down, in the round: collar, raglan yoke, body, then the sleeves.",
        _CO_FMT % m["neck"],
    ]
    for _ in range(m["collar_rounds"]):
        lines.append(_K2_P2_RIB)
    if m["pre"]:
        lines.append("# neck increase round: +%d evenly (%d -> %d)" % (m["pre"], m["neck"], m["calc_neck"]))
        lines.append(_increase_row(m["neck"], m["pre"]))
    freq_phrase = "every round" if m["freq"] == "every_round" else "every other round"
    lines.append(
        "# raglan yoke: +%d per increase round, %s (%d -> %d)" % (m["inc"], freq_phrase, m["calc_neck"], m["working"])
    )
    w = m["calc_neck"]
    for r in range(1, m["raglan_total_rounds"] + 1):
        if m["freq"] == "every_round" or r % 2 == 1:
            lines.append(_increase_row(w, m["inc"]))
            w += m["inc"]
        else:
            lines.append(_K_ALL)
    # Sleeve separation: the real pattern puts the sleeve stitches on holders
    # and continues the body on the bust count.  A linear engine cannot hold
    # stitches aside, so the body is represented by its own cast-on at the
    # plan's real body count — the comment keeps that honest, and every
    # executed stitch count from here on matches the Planner's numbers.
    lines.append("# sleeve separation: the %d-st sleeves go on holders; the body" % m["arm"])
    lines.append("# continues on the %d body stitches (front + back + underarm cast-on)" % m["bust"])
    lines.append(_CO_FMT % m["bust"])
    lines.append("# body: %d rounds of stockinette" % m["body_stock_rounds"])
    for _ in range(m["body_stock_rounds"]):
        lines.append(_K_ALL)
    lines.append("# hem: %d rounds of k2, p2 ribbing" % m["hem_rounds"])
    for _ in range(m["hem_rounds"]):
        lines.append(_K2_P2_RIB)
    lines.append("bo all")
    lines.extend(_sim_sleeve_lines(m))

    # Canonical garment sections.  Boundaries are non-comment line indices,
    # which map 1:1 onto simulation steps.  The neck increase round shapes
    # the neckline, so it stays in the Neckline section; the yoke is exactly
    # the raglan increase schedule; the body begins with the sleeve
    # separation (its own cast-on at the bust count); the hem, each sleeve
    # and each cuff are their own phase so the cuffs and bind-offs are
    # visible in the progress view.
    neckline_end = 1 + m["collar_rounds"] + (1 if m["pre"] else 0)
    yoke_end = neckline_end + m["raglan_total_rounds"]
    body_end = yoke_end + 1 + m["body_stock_rounds"]  # + separation co
    hem_end = body_end + m["hem_rounds"] + 1  # + bo all
    sleeve_len = 1 + m["sleeve_shaping_rounds"]  # co + shaping
    cuff_len = m["cuff_rounds"] + 1  # cuff + bo all
    s1_end = hem_end + sleeve_len
    c1_end = s1_end + cuff_len
    s2_end = c1_end + sleeve_len
    total_end = s2_end + cuff_len
    sections = [
        {"id": "neckline", "label": "Neck", "start": 0, "end": neckline_end},
        {"id": "yoke", "label": "Yoke", "start": neckline_end, "end": yoke_end},
        {"id": "body", "label": "Body", "start": yoke_end, "end": body_end},
        {"id": "hem", "label": "Hem & bind-off", "start": body_end, "end": hem_end},
        {"id": "left_sleeve", "label": "Left sleeve", "start": hem_end, "end": s1_end},
        {
            "id": "left_cuff",
            "label": "Left cuff & bind-off",
            "start": s1_end,
            "end": c1_end,
        },
        {"id": "right_sleeve", "label": "Right sleeve", "start": c1_end, "end": s2_end},
        {
            "id": "right_cuff",
            "label": "Right cuff & bind-off",
            "start": s2_end,
            "end": total_end,
        },
    ]
    return "\n".join(lines) + "\n", sections


# ---------------------------------------------------------------------------
# SVG schematic
# ---------------------------------------------------------------------------


def _sweater_svg(neck, front_final, back_final, sleeve_final, armpit, bust, depth_in):
    """Top-down flat schematic: T-shaped sweater with neck, raglan seams,
    body, sleeves, underarm, hem, cuffs, and a stitch proportion bar."""
    vw = 480
    vh = 440

    body_w = 140
    body_top = 130
    body_h = 155

    sleeve_w = 90
    sleeve_h = 100

    neck_w = 50
    neck_h = 30

    cx = vw // 2

    # Proportion bar dimensions
    bar_y = body_top + body_h + 50
    bar_h = 24
    bar_margin = 40
    bar_w = vw - 2 * bar_margin

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{vw}" '
        f'height="{vh}" viewBox="0 0 {vw} {vh}" '
        'font-family="system-ui, -apple-system, sans-serif">',
        "<defs>",
        "<style>",
        ".sleeve { fill: #c8e6f5; stroke: #2980b9; stroke-width: 2; }",
        ".body { fill: #d5f5e3; stroke: #27ae60; stroke-width: 2; }",
        ".neck { fill: #f5f5f5; stroke: #7f8c8d; stroke-width: 2; }",
        ".raglan { stroke: #e74c3c; stroke-width: 2.5; stroke-dasharray: 6,3; fill: none; }",
        ".rib { fill: none; stroke: #8e44ad; stroke-width: 1.5; }",
        ".label { font-size: 11px; fill: #2c3e50; }",
        ".sublabel { font-size: 10px; fill: #7f8c8d; }",
        ".title { font-size: 13px; fill: #2c3e50; font-weight: bold; }",
        ".bar-label { font-size: 10px; fill: white; font-weight: bold; }",
        ".bar-legend { font-size: 10px; fill: #555; }",
        "</style>",
        '<marker id="arrow" viewBox="0 0 10 10" refX="5" refY="5" '
        'markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
        '<path d="M 0 0 L 10 5 L 0 10 z" fill="#7f8c8d"/>'
        "</marker>",
        "</defs>",
    ]

    # --- Right sleeve ---
    sx = cx + body_w // 2
    sy = body_top + 15
    sleeve_pts = f"{sx},{sy} {sx + sleeve_w},{sy + 10} {sx + sleeve_w},{sy + sleeve_h - 10} {sx},{sy + sleeve_h}"
    parts.append(f'<polygon points="{sleeve_pts}" class="sleeve"/>')

    # Cuff (ribbing at sleeve end)
    cuff_x = sx + sleeve_w - 12
    for i in range(4):
        cy = sy + 20 + i * ((sleeve_h - 40) / 3)
        parts.append(f'<line x1="{cuff_x}" y1="{cy:.1f}" ' f'x2="{sx + sleeve_w}" y2="{cy:.1f}" class="rib"/>')

    # --- Left sleeve (mirrored) ---
    lx = cx - body_w // 2
    ly = body_top + 15
    left_pts = f"{lx},{ly} {lx - sleeve_w},{ly + 10} {lx - sleeve_w},{ly + sleeve_h - 10} {lx},{ly + sleeve_h}"
    parts.append(f'<polygon points="{left_pts}" class="sleeve"/>')

    # Left cuff
    lcuff_x = lx - sleeve_w + 12
    for i in range(4):
        cy = ly + 20 + i * ((sleeve_h - 40) / 3)
        parts.append(f'<line x1="{lcuff_x}" y1="{cy:.1f}" ' f'x2="{lx - sleeve_w}" y2="{cy:.1f}" class="rib"/>')

    # --- Body ---
    parts.append(f'<rect x="{cx - body_w // 2}" y="{body_top}" ' f'width="{body_w}" height="{body_h}" class="body"/>')

    # Hem (ribbing at bottom)
    hem_y = body_top + body_h - 14
    for i in range(4):
        hx = cx - body_w // 2 + 10 + i * ((body_w - 20) / 3)
        parts.append(f'<line x1="{hx:.1f}" y1="{hem_y}" ' f'x2="{hx:.1f}" y2="{body_top + body_h}" class="rib"/>')

    # --- Raglan lines (4 diagonal seams from neck to underarms) ---
    neck_left = cx - neck_w // 2
    neck_right = cx + neck_w // 2
    neck_bottom = body_top + neck_h
    ur_x = cx + body_w // 2
    ur_y = body_top + 15
    ul_x = cx - body_w // 2
    ul_y = body_top + 15

    parts.append(f'<line x1="{neck_right}" y1="{body_top}" ' f'x2="{ur_x}" y2="{ur_y}" class="raglan"/>')
    parts.append(f'<line x1="{neck_left}" y1="{body_top}" ' f'x2="{ul_x}" y2="{ul_y}" class="raglan"/>')
    parts.append(f'<line x1="{neck_right}" y1="{neck_bottom}" ' f'x2="{ur_x}" y2="{ur_y + sleeve_h}" class="raglan"/>')
    parts.append(f'<line x1="{neck_left}" y1="{neck_bottom}" ' f'x2="{ul_x}" y2="{ul_y + sleeve_h}" class="raglan"/>')

    # --- Neck opening (ellipse) ---
    parts.append(
        f'<ellipse cx="{cx}" cy="{body_top + neck_h // 2}" ' f'rx="{neck_w // 2}" ry="{neck_h // 2}" class="neck"/>'
    )

    # --- Labels ---
    # Neck label (above)
    parts.append(f'<text x="{cx}" y="{body_top - 30}" text-anchor="middle" ' f'class="title">Neck: {neck} sts</text>')
    parts.append(
        f'<text x="{cx}" y="{body_top - 17}" text-anchor="middle" '
        f'class="sublabel">cast on and join in the round</text>'
    )

    # Raglan line labels (at midpoints of the four seams)
    mid_r = ((neck_right + ur_x) / 2, (body_top + ur_y) / 2)
    parts.append(f'<text x="{mid_r[0] + 8}" y="{mid_r[1] - 4}" ' f'class="sublabel" text-anchor="start">raglan</text>')
    mid_l = ((neck_left + ul_x) / 2, (body_top + ul_y) / 2)
    parts.append(f'<text x="{mid_l[0] - 8}" y="{mid_l[1] - 4}" ' f'class="sublabel" text-anchor="end">raglan</text>')

    # Front label (center of body)
    parts.append(
        f'<text x="{cx}" y="{body_top + body_h // 2 - 8}" '
        f'text-anchor="middle" class="label">'
        f"Front: {front_final} sts</text>"
    )
    parts.append(
        f'<text x="{cx}" y="{body_top + body_h // 2 + 8}" '
        f'text-anchor="middle" class="label">'
        f"Back: {back_final} sts</text>"
    )

    # Sleeve labels (center of each sleeve polygon)
    r_sleeve_cx = sx + sleeve_w * 0.45
    r_sleeve_cy = sy + sleeve_h * 0.5
    parts.append(
        f'<text x="{r_sleeve_cx:.0f}" y="{r_sleeve_cy:.0f}" '
        f'text-anchor="middle" class="label">'
        f"Sleeve: {sleeve_final} sts</text>"
    )
    l_sleeve_cx = lx - sleeve_w * 0.45
    l_sleeve_cy = ly + sleeve_h * 0.5
    parts.append(
        f'<text x="{l_sleeve_cx:.0f}" y="{l_sleeve_cy:.0f}" '
        f'text-anchor="middle" class="label">'
        f"Sleeve: {sleeve_final} sts</text>"
    )

    # Underarm cast-on labels
    parts.append(
        f'<text x="{ur_x + 8}" y="{ur_y + sleeve_h + 16}" '
        f'class="sublabel" text-anchor="start">'
        f"underarm +{armpit}</text>"
    )
    parts.append(
        f'<text x="{ul_x - 8}" y="{ul_y + sleeve_h + 16}" '
        f'class="sublabel" text-anchor="end">'
        f"underarm +{armpit}</text>"
    )

    # Body in the round label (below body, above proportion bar)
    parts.append(
        f'<text x="{cx}" y="{body_top + body_h + 18}" '
        f'text-anchor="middle" class="label">'
        f"Body: {bust} sts in the round</text>"
    )
    parts.append(
        f'<text x="{cx}" y="{body_top + body_h + 32}" '
        f'text-anchor="middle" class="sublabel">'
        f"~{_num(depth_in)} in neck to underarm</text>"
    )

    # Raglan depth annotation (right side, vertical line)
    ann_x = cx + body_w // 2 + 20
    parts.append(
        f'<line x1="{ann_x}" y1="{body_top}" x2="{ann_x}" y2="{ur_y}" '
        f'stroke="#7f8c8d" stroke-width="1" marker-start="url(#arrow)" '
        f'marker-end="url(#arrow)"/>'
    )
    parts.append(
        f'<text x="{ann_x + 6}" y="{(body_top + ur_y) / 2 + 4}" '
        f'class="sublabel" text-anchor="start">'
        f'{_num(depth_in)}" raglan</text>'
    )

    # --- Stitch proportion bar ---
    total = front_final + back_final + 2 * sleeve_final
    if total > 0:
        # Color segments: sleeve L (blue), back (orange), front (teal), sleeve R (blue)
        segments = [
            (sleeve_final, "#3498db", f"Sleeve {sleeve_final}"),
            (back_final, "#e67e22", f"Back {back_final}"),
            (front_final, "#1abc9c", f"Front {front_final}"),
            (sleeve_final, "#3498db", f"Sleeve {sleeve_final}"),
        ]
        x = bar_margin
        for count, color, label in segments:
            seg_w = max(2, bar_w * count / total)
            parts.append(
                f'<rect x="{x:.1f}" y="{bar_y}" width="{seg_w:.1f}" ' f'height="{bar_h}" fill="{color}" rx="3"/>'
            )
            # Label inside bar if wide enough, else above
            text_x = x + seg_w / 2
            if seg_w > 30:
                parts.append(
                    f'<text x="{text_x:.1f}" y="{bar_y + bar_h / 2 + 3.5}" '
                    f'text-anchor="middle" class="bar-label">{label}</text>'
                )
            else:
                parts.append(
                    f'<text x="{text_x:.1f}" y="{bar_y - 4}" ' f'text-anchor="middle" class="bar-legend">{label}</text>'
                )
            x += seg_w

        # Bar border
        parts.append(
            f'<rect x="{bar_margin}" y="{bar_y}" width="{bar_w}" '
            f'height="{bar_h}" fill="none" stroke="#ccc" stroke-width="1" rx="3"/>'
        )

        # Total label below bar
        parts.append(
            f'<text x="{cx}" y="{bar_y + bar_h + 16}" '
            f'text-anchor="middle" class="sublabel">'
            f"total at underarm: {total} sts ({front_final}+{back_final}+{sleeve_final}+{sleeve_final})"
            f"</text>"
        )

    parts.append(_SVG_CLOSE)
    return "\n".join(parts)


def _raglan_growth_svg(
    front_start,
    back_start,
    sleeve_start,
    front_final,
    back_final,
    sleeve_final,
    inc_rounds,
    freq,
):
    "Line chart showing how each raglan section grows from neck to underarm." ""
    vw = 420
    vh = 240
    pad_l, pad_r, pad_t, pad_b = 55, 20, 30, 50
    cw = vw - pad_l - pad_r
    ch = vh - pad_t - pad_b

    total_rounds = inc_rounds if freq == "every_round" else 2 * inc_rounds
    max_sts = max(front_final, back_final, sleeve_final) + 2
    min_sts = min(front_start, back_start, sleeve_start, 0)

    def x(round_num):
        return pad_l + (round_num / max(total_rounds, 1)) * cw

    def y(sts):
        return pad_t + ch - ((sts - min_sts) / max(max_sts - min_sts, 1)) * ch

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{vw}" height="{vh}" '
        f'viewBox="0 0 {vw} {vh}" '
        'font-family="system-ui, -apple-system, sans-serif">',
        "<defs><style>",
        ".chart-label { font-size: 10px; fill: #555; }",
        ".chart-title { font-size: 12px; fill: #2c3e50; font-weight: bold; }",
        ".grid-line { stroke: #eee; stroke-width: 1; }",
        ".inc-marker { stroke: #ddd; stroke-width: 1; stroke-dasharray: 3,3; }",
        "</style></defs>",
    ]

    # Grid lines (horizontal, every 10 stitches)
    step = 20 if max_sts - min_sts > 60 else 10
    v = int(min_sts // step * step)
    while v <= max_sts + step:
        parts.append(f'<line x1="{pad_l}" y1="{y(v):.1f}" x2="{pad_l + cw}" ' f'y2="{y(v):.1f}" class="grid-line"/>')
        parts.append(f'<text x="{pad_l - 6}" y="{y(v) + 3}" text-anchor="end" ' f'class="chart-label">{v}</text>')
        v += step

    # X axis labels
    for r in range(0, total_rounds + 1, max(1, total_rounds // 5)):
        parts.append(
            f'<text x="{x(r):.0f}" y="{vh - pad_b + 16}" text-anchor="middle" ' f'class="chart-label">{r}</text>'
        )
    parts.append(
        f'<text x="{pad_l + cw / 2}" y="{vh - 4}" text-anchor="middle" ' f'class="chart-label">raglan rounds</text>'
    )

    # Data lines (front/back and sleeve)
    series = [
        ([front_start, front_final], "#1abc9c", "front"),
        ([back_start, back_final], "#e67e22", "back"),
        ([sleeve_start, sleeve_final], "#3498db", "sleeve (each)"),
    ]
    for pts, color, label in series:
        x1, y1 = x(0), y(pts[0])
        x2, y2 = x(total_rounds), y(pts[1])
        parts.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" ' f'stroke="{color}" stroke-width="2.5"/>'
        )
        # Start dot
        parts.append(f'<circle cx="{x1:.1f}" cy="{y1:.1f}" r="3" fill="{color}"/>')
        # End dot
        parts.append(f'<circle cx="{x2:.1f}" cy="{y2:.1f}" r="3" fill="{color}"/>')
        # End label
        parts.append(
            f'<text x="{x2 + 5:.1f}" y="{y2 + 3:.1f}" font-size="9" '
            f'fill="{color}" font-weight="bold">{pts[1]}</text>'
        )

    # Legend (top right)
    lx = pad_l + cw - 8
    for i, (_, color, label) in enumerate(reversed(series)):
        ly = pad_t + 6 + i * 14
        parts.append(f'<line x1="{lx - 30}" y1="{ly}" x2="{lx - 16}" y2="{ly}" ' f'stroke="{color}" stroke-width="2"/>')
        parts.append(
            f'<text x="{lx - 13}" y="{ly + 3}" font-size="9" ' f'fill="{color}" text-anchor="start">{label}</text>'
        )

    # Title
    parts.append(
        f'<text x="{pad_l + cw / 2}" y="{pad_t - 10}" text-anchor="middle" '
        f'class="chart-title">Raglan yoke growth ({total_rounds} rounds)</text>'
    )

    parts.append(_SVG_CLOSE)
    return "\n".join(parts)


def _sleeve_taper_svg(arm, wrist, sleeve_shaping_rounds, rg, sleeve_sched):
    "Visual showing the sleeve taper from upper arm to wrist." ""
    vw = 420
    vh = 220
    pad_l, pad_r, pad_t, pad_b = 50, 30, 30, 40
    cw = vw - pad_l - pad_r
    ch = vh - pad_t - pad_b

    total_r = max(sleeve_shaping_rounds, 1)
    max_sts = arm + 4
    min_sts = max(wrist - 4, 0)

    def px(round_num):
        return pad_l + (round_num / total_r) * cw

    def py(sts):
        return pad_t + ch - ((sts - min_sts) / max(max_sts - min_sts, 1)) * ch

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{vw}" height="{vh}" '
        f'viewBox="0 0 {vw} {vh}" '
        'font-family="system-ui, -apple-system, sans-serif">',
        "<defs><style>",
        ".taper-label { font-size: 10px; fill: #555; }",
        ".taper-title { font-size: 12px; fill: #2c3e50; font-weight: bold; }",
        ".taper-grid { stroke: #eee; stroke-width: 1; }",
        ".taper-shade { fill: #3498db; opacity: 0.12; }",
        ".taper-line { stroke: #3498db; stroke-width: 2.5; fill: none; }",
        "</style></defs>",
    ]

    # Grid
    step = 10 if arm - wrist > 30 else 5
    v = int(min_sts // step * step)
    while v <= max_sts + step:
        parts.append(f'<line x1="{pad_l}" y1="{py(v):.1f}" x2="{pad_l + cw}" ' f'y2="{py(v):.1f}" class="taper-grid"/>')
        parts.append(f'<text x="{pad_l - 6}" y="{py(v) + 3}" text-anchor="end" ' f'class="taper-label">{v}</text>')
        v += step

    for r in range(0, total_r + 1, max(1, total_r // 5)):
        parts.append(
            f'<text x="{px(r):.0f}" y="{vh - pad_b + 16}" text-anchor="middle" ' f'class="taper-label">{r}</text>'
        )
    parts.append(
        f'<text x="{pad_l + cw / 2}" y="{vh - 4}" text-anchor="middle" ' f'class="taper-label">shaping rounds</text>'
    )

    # Shaded area under the line
    pts = [(px(0), py(arm))]
    for r in range(total_r + 1):
        # Estimate stitch count at this round
        frac = r / total_r
        est = arm - frac * (arm - wrist)
        pts.append((px(r), py(est)))
    pts.append((px(total_r), py(wrist)))
    pts.append((px(total_r), pad_t + ch))
    pts.append((px(0), pad_t + ch))
    poly = " ".join(f"{px:.1f},{py:.1f}" for px, py in pts)
    parts.append(f'<polygon points="{poly}" class="taper-shade"/>')

    # Main line
    line_pts = [(px(0), py(arm))]
    for r in range(total_r + 1):
        frac = r / total_r
        est = arm - frac * (arm - wrist)
        line_pts.append((px(r), py(est)))
    line_str = " ".join(f"{lx:.1f},{ly:.1f}" for lx, ly in line_pts)
    parts.append(f'<polyline points="{line_str}" class="taper-line"/>')

    # Start/end dots and labels
    parts.append(f'<circle cx="{px(0):.1f}" cy="{py(arm):.1f}" r="4" fill="#3498db"/>')
    parts.append(
        f'<text x="{px(0) + 6:.1f}" y="{py(arm) - 6:.1f}" font-size="11" '
        f'fill="#3498db" font-weight="bold">{arm} sts (arm)</text>'
    )
    parts.append(f'<circle cx="{px(total_r):.1f}" cy="{py(wrist):.1f}" r="4" fill="#e74c3c"/>')
    parts.append(
        f'<text x="{px(total_r) - 6:.1f}" y="{py(wrist) - 6:.1f}" '
        f'text-anchor="end" font-size="11" '
        f'fill="#e74c3c" font-weight="bold">{wrist} sts (wrist)</text>'
    )

    # Title
    parts.append(
        f'<text x="{pad_l + cw / 2}" y="{pad_t - 10}" text-anchor="middle" '
        f'class="taper-title">Sleeve shaping ({sleeve_sched})</text>'
    )

    parts.append(_SVG_CLOSE)
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# HTML rendering
# ---------------------------------------------------------------------------


def _esc(text):
    return html.escape(str(text), quote=False)


def _render_steps(steps):
    parts = ["<ol class='plan-steps'>"]
    for step in steps:
        parts.append(f"<li>{_esc(step)}</li>")
    parts.append("</ol>")
    return "\n".join(parts)


def _render_table(table):
    parts = ["<table class='plan-table'><thead><tr>"]
    for col in table["columns"]:
        parts.append(f"<th>{_esc(col)}</th>")
    parts.append("</tr></thead><tbody>")
    for row in table["rows"]:
        parts.append("<tr>")
        for cell in row:
            parts.append(f"<td>{_esc(cell)}</td>")
        parts.append("</tr>")
    parts.append("</tbody></table>")
    return "\n".join(parts)


def _render_rows(rows):
    parts = ["<ul class='plan-rows'>"]
    for line in rows:
        parts.append(f"<li class='mono'>{_esc(line)}</li>")
    parts.append("</ul>")
    return "\n".join(parts)


def _render_one_section(section):
    parts = [
        '<section class="plan-section">',
        f'<h4>{_esc(section["heading"])}</h4>',
    ]
    if section.get("intro"):
        parts.append(f'<p class="plan-intro">{_esc(section["intro"])}</p>')
    if section.get("steps"):
        parts.append(_render_steps(section["steps"]))
    table = section.get("table")
    if table:
        if section.get("collapsible"):
            shown = table["rows"][:MAX_TABLE_ROWS]
            total = len(table["rows"])
            parts.append("<details class='plan-details'>")
            parts.append(f"<summary>Show round-by-round stitch table ({len(shown)} of {total} rounds)</summary>")
            parts.append(_render_table({"columns": table["columns"], "rows": shown}))
            if total > MAX_TABLE_ROWS:
                parts.append(
                    f"<p class='plan-note'>The first {MAX_TABLE_ROWS} "
                    "rounds are shown; the exported pattern contains the "
                    "complete schedule.</p>"
                )
            parts.append("</details>")
        else:
            parts.append(_render_table(table))
    elif section.get("rows"):
        parts.append(_render_rows(section["rows"]))
    parts.append("</section>")
    return "\n".join(parts)


def _render_sections(sections):
    return "\n".join(_render_one_section(section) for section in sections)


def to_html(result):
    "Render the schematic plus the full guided sweater plan." ""
    plan = result["plan"]
    m = result["meta"]

    # Stat pills: at-a-glance key numbers
    pills = [
        ("Cast on", f"{m['neck']} sts"),
        ("Body", f"{m['bust']} sts"),
        ("Sleeve", f"{m['arm']} sts"),
        ("Raglan", f"~{_num(m['depth_in'])} in"),
        ("Body length", f"{_num(m['body_len'])} in"),
        ("Sleeve length", f"{_num(m['sleeve_len'])} in"),
    ]
    pill_html = "".join(
        f"<div class='raglan-pill'><span class='label'>{label}</span><span class='value'>{value}</span></div>"
        for label, value in pills
    )

    blocks = [
        "<style>"
        ".raglan-pills{display:flex;flex-wrap:wrap;gap:0.5rem;margin:0.6rem 0;}"
        ".raglan-pill{border:1px solid #ddd8d4;border-radius:6px;padding:0.4rem 0.65rem;background:#fdfcfa;flex:1 1 auto;min-width:90px;text-align:center;}"  # noqa: E501
        ".raglan-pill .label{display:block;font-size:0.72rem;color:#6b6572;text-transform:uppercase;letter-spacing:0.04em;}"  # noqa: E501
        ".raglan-pill .value{font-size:0.95rem;font-weight:700;color:#2b2333;}"
        "</style>",
        f"<div class='output-box'>{result['svg']}</div>",
        f"<div class='raglan-pills'>{pill_html}</div>",
    ]

    est = result.get("_estimator_data", {})
    if est.get("stitch_count"):
        blocks.append(
            "<div class='button-row'><button class='btn-secondary send-to-estimator' "
            f"data-stitches='{est['stitch_count']}' data-type='sweater'>"
            "Send to Yarn Estimator &rarr;</button></div>"
        )

    if plan["warnings"]:
        items = "".join(f"<li>{_esc(w)}</li>" for w in plan["warnings"])
        blocks.append(f"<div class='warning-box'><strong>Worth a second look</strong><ul>{items}</ul></div>")

    assumptions = "".join(f"<li>{_esc(a)}</li>" for a in plan["assumptions"])
    blocks.append(
        "<section class='plan-section'>"
        "<h4>How this sweater is built</h4>"
        f"<ul class='plan-assumptions'>{assumptions}</ul>"
        "</section>"
    )

    # Raglan growth chart
    growth_svg = _raglan_growth_svg(
        m["front_start"],
        m["back_start"],
        m["sleeve_start"],
        m["front_final"],
        m["back_final"],
        m["sleeve_final"],
        m["inc_rounds"],
        m["freq"],
        m["seg"],
        m["inc"],
    )
    blocks.append(f"<div class='output-box'>{growth_svg}</div>")

    # Sleeve taper chart
    taper_svg = _sleeve_taper_svg(
        m["arm"],
        m["wrist"],
        m["sleeve_shaping_rounds"],
        m["rg"],
        m["sleeve_sched"],
    )
    blocks.append(f"<div class='output-box'>{taper_svg}</div>")

    blocks.append("<h3 class='plan-title'>Your knitting plan</h3>")
    blocks.append(_render_sections(plan["sections"]))
    return "\n".join(blocks)


DEMO = {
    "TITLE": TITLE,
    "DEFAULT_INPUTS": DEFAULT_INPUTS,
    "compute": compute,
    "to_html": to_html,
}
