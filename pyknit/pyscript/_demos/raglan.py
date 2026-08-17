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

from pyknit import raglan_increases, sleeve_decreases
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

ALLOWED_INCREASES = {4, 8, 12, 16, 20, 24}
ALLOWED_FREQUENCIES = ("every_round", "every_other_round")


def _num(x):
    """Format a float compactly (80.0 -> '80', 7.0769 -> '7.08')."""
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
    """Round an integer up/down to the nearest even number."""
    n = int(round(n))
    return n if n % 2 == 0 else n + 1


def _freq_phrase(freq):
    return "every round" if freq == "every_round" else "every other round"


def _section(heading, intro=None, steps=None, rows=None, table=None):
    section = {"heading": heading}
    if intro:
        section["intro"] = intro
    if steps:
        section["steps"] = steps
    if rows:
        section["rows"] = rows
    if table:
        section["table"] = table
    return section


def compute(inputs):
    """Build the complete sweater plan as a dict, reusing pyknit math."""
    st = _pos(inputs, "stitches_per_inch", "stitch gauge")
    rg = _pos(inputs, "rows_per_inch", "row gauge")
    neck_circ = _pos(inputs, "neck_circumference", "neck circumference")
    bust_circ = _pos(inputs, "bust_circumference", "bust circumference")
    ease = float(inputs.get("ease") or 0)
    if ease < -4 or ease > 10:
        raise ValueError("ease must be between -4 and 10 inches")
    underarm_w = _pos(inputs, "underarm_width", "underarm width")
    upper_arm = _pos(inputs, "upper_arm_circumference", "upper arm circumference")
    wrist_circ = _pos(inputs, "wrist_circumference", "wrist circumference")
    body_len = _pos(inputs, "body_length", "body length")
    sleeve_len = _pos(inputs, "sleeve_length", "sleeve length")
    inc = int(inputs.get("increases_per_round", 8))
    freq = str(inputs.get("increase_frequency", "every_other_round"))

    if inc not in ALLOWED_INCREASES:
        raise ValueError(
            "increases per round must be one of "
            + ", ".join(str(n) for n in sorted(ALLOWED_INCREASES))
        )
    if freq not in ALLOWED_FREQUENCIES:
        raise ValueError(
            "increase frequency must be 'every round' or 'every other round'"
        )
    if neck_circ >= bust_circ:
        raise ValueError(
            "neck circumference must be smaller than the bust circumference "
            "(the raglan widens from the neck down)"
        )
    if upper_arm >= bust_circ:
        raise ValueError(
            "upper arm circumference must be smaller than the bust circumference"
        )
    if wrist_circ >= upper_arm:
        raise ValueError(
            "wrist circumference must be smaller than the upper arm "
            "for a tapering sleeve"
        )

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
    arm = _even(swatch.measurement_to_stitches(upper_arm))
    armpit = max(2, _even(swatch.measurement_to_stitches(underarm_w)))
    wrist = _even(swatch.measurement_to_stitches(wrist_circ))

    if min(neck, bust, arm) < 4:
        raise ValueError("the neck/bust/arm measurements are too small for a sweater")
    if wrist >= arm:
        raise ValueError(
            "the wrist rounds up to the upper-arm count, leaving no room for "
            "sleeve shaping; use a smaller wrist measurement or add negative ease"
        )

    # Raglan arithmetic mirrors pyknit.raglan_increases:
    # working = live stitches at the underarm (body + sleeves)
    #         = bust + 2*arm - 4*armpit  (armpit counted twice)
    working = bust + 2 * arm - 4 * armpit
    needed = working - neck
    if needed <= 0:
        raise ValueError(
            "the finished bust/arm stitches must be larger than the neck cast-on; "
            "check your measurements"
        )
    inc_rounds = needed // inc
    pre = needed % inc
    if inc_rounds < 1:
        raise ValueError(
            "not enough stitches between the neck and underarm to schedule "
            "raglan increases; increase the increases per round or the "
            "difference between neck and bust"
        )
    calc_neck = neck + pre

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
        raise ValueError(
            "The measurements produce a raglan that cannot be distributed "
            "evenly. " + str(exc)
        )

    match_marker = re.search(r"Marker setup:\s*(.*)", raglan)
    marker = match_marker.group(1).strip() if match_marker else ""
    match_incrow = re.search(r"Increase row:\s*(.*?)Marker setup:", raglan)
    inc_row_str = match_incrow.group(1).strip() if match_incrow else ""

    # The per-section starting counts (identical math to raglan_increases).
    body_start = bust / 2 - 2 * inc_rounds - armpit
    front_start = math.ceil(body_start)
    back_start = math.floor(body_start)
    sleeve_start = arm - armpit - 2 * inc_rounds

    seg = inc // 4  # stitches added to each of the 4 sections per increase round
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
            f"body length ({_num(body_len)} in) is too short for a "
            f"{HEM_IN:g} in hem; add length or shorten the hem"
        )
    body_stock_rounds = body_total_rounds - hem_rounds
    sleeve_total_rounds = round(sleeve_len * rg)
    if sleeve_total_rounds <= cuff_rounds:
        raise ValueError(
            f"sleeve length ({_num(sleeve_len)} in) is too short to include "
            f"a {CUFF_IN:g} in cuff"
        )
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

    # Build the per-round transition schedule.
    display_rounds = raglan_total_rounds
    table_rows = []
    text_rows = []
    total = calc_neck
    fr, ba, sl = front_start, back_start, sleeve_start
    for r in range(1, display_rounds + 1):
        if freq == "every_round" or r % 2 == 1:
            total += inc
            fr += seg
            ba += seg
            sl += seg
            action = "increase"
        else:
            action = "plain"
        table_rows.append([r, action, total, fr, ba, sl])
        text_rows.append(
            f"Round {r}: {action} -> {total} sts total "
            f"(front {fr}, back {ba}, sleeve {sl} each)"
        )

    # Warnings for geometry that is usable but worth a second look.
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

    sections = [
        _math_section(locals()),
        _measurements_section(locals()),
        _cast_on_section(inc_row_str, calc_neck, neck, collar_rounds, rg),
        _marker_section(marker, front_start, back_start, sleeve_start,
                        calc_neck, inc, seg, freq),
        _increase_schedule_section(
            inc_rounds, freq, inc, seg, working, front_final, back_final,
            sleeve_final, pre, table_rows, text_rows,
        ),
        _separation_section(front_final, back_final, sleeve_final, armpit, bust, arm),
        _body_section(body_stock_rounds, rg, body_len),
        _hem_section(hem_rounds, rg, body_len),
        _sleeve_section(sleeve_final, armpit, arm, sleeve_shaping_rounds, rg,
                        sleeve_sched, wrist, sleeve_len),
        _cuff_section(cuff_rounds, rg, sleeve_len),
    ]

    assumptions = [
        "This is a seamless, top-down raglan knit in the round: cast on at the "
        "neck, increase along four seams, then split for the body and sleeves.",
        f"There are four raglan seams with {inc} increases per increase round "
        f"({seg} to each section), so the stitch counts stay balanced.",
        f"Positive ease of {_num(ease)} in at the bust; the sleeve is knit at "
        "the measured upper-arm circumference (measure with a little room).",
        f"The collar is about {COLLAR_IN:g} in of ribbing, and the hem and "
        f"cuffs about {HEM_IN:g} in each.",
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
        "svg": _sweater_svg(neck, front_final, back_final, sleeve_final,
                            armpit, bust, depth_in),
        "meta": {
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
            "freq": freq,
            "display_rounds": display_rounds,
            "marker": marker,
        },
    }


# ---------------------------------------------------------------------------
# Plan section builders
# ---------------------------------------------------------------------------


def _math_section(v):
    """Section 0: the visible math behind every derived number."""
    rows = [
        f"Gauge: {_num(v['st'])} sts/in x {_num(v['rg'])} rows/in (blocked)",
        f"Neck cast-on: {_num(v['neck_circ'])} in x {_num(v['st'])} = "
        f"{round(v['neck_circ'] * v['st'])} -> {v['neck']} (rounded even)",
        f"Bust: ({_num(v['bust_circ'])} + {_num(v['ease'])} in ease) x "
        f"{_num(v['st'])} = {round((v['bust_circ'] + v['ease']) * v['st'])} "
        f"-> {v['bust']} sts in the round",
        f"Upper arm: {_num(v['upper_arm'])} in x {_num(v['st'])} = "
        f"{round(v['upper_arm'] * v['st'])} -> {v['arm']} sts",
        f"Underarm cast-on (each side): {_num(v['underarm_w'])} in x "
        f"{_num(v['st'])} = {round(v['underarm_w'] * v['st'])} -> {v['armpit']} sts",
        f"Wrist: {_num(v['wrist_circ'])} in x {_num(v['st'])} = "
        f"{round(v['wrist_circ'] * v['st'])} -> {v['wrist']} sts",
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
        ("Bust + ease", f"{_num(v['bust_circ'] + v['ease'])} in "
                        f"({_num(v['bust_circ'])} + {_num(v['ease'])} ease)"),
        ("Bust stitches (body in the round)", f"{v['bust']} sts"),
        ("Underarm cast-on", f"{v['armpit']} sts each side"),
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
        f"Work {collar_rounds} rounds of k2, p2 ribbing for the collar "
        f"(about {_num(collar_rounds / rg)} in).",
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


def _marker_section(marker, front_start, back_start, sleeve_start, calc_neck,
                    inc, seg, freq):
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


def _increase_schedule_section(inc_rounds, freq, inc, seg, working,
                               front_final, back_final, sleeve_final, pre,
                               table_rows, text_rows):
    shown = table_rows[:MAX_TABLE_ROWS]
    intro = (
        f"Work {inc_rounds} increase rounds, {_freq_phrase(freq)}, adding "
        f"{inc} stitches per increase round ({seg} to each section). This "
        "table shows the stitch count after every round so you can check "
        "your progress."
    )
    if len(table_rows) > MAX_TABLE_ROWS:
        intro += (
            f" The first {MAX_TABLE_ROWS} rounds are shown; the exported "
            "pattern contains the complete schedule."
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
        steps.append(
            f"The {pre}-stitch neck increase round from section 2 is already "
            "included in these counts."
        )
    return _section(
        "4. Raglan increase schedule with stitch transitions",
        intro=intro,
        steps=steps,
        table={"columns": ["Round", "Action", "Total", "Front", "Back", "Sleeve"],
               "rows": shown},
        rows=text_rows,
    )


def _freq_step(freq):
    if freq == "every_round":
        return "Increase every round until the underarm."
    return "Increase on every odd round, and knit a plain round in between " \
           "(increases every other round)."


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
            f"Work {hem_rounds} rounds of k2, p2 ribbing (about "
            f"{_num(hem_rounds / rg)} in).",
            "Bind off loosely in pattern (a stretchy bind-off such as Jeny's "
            "surprisingly stretchy bind-off keeps the hem from pulling in).",
            f"The body measures about {_num(body_len)} in from the underarm "
            "to the hem.",
        ],
    )


def _sleeve_section(sleeve_final, armpit, arm, sleeve_shaping_rounds, rg,
                    sleeve_sched, wrist, sleeve_len):
    return _section(
        "8. Sleeve instructions and shaping",
        intro="Work each sleeve the same way.",
        steps=[
            f"Pick up and knit {arm} stitches for the sleeve: the "
            f"{sleeve_final} held stitches plus {armpit} stitches along the "
            "underarm cast-on. Place a marker at the underarm seam.",
            f"Knit the sleeve in the round, working the shaping schedule "
            f"below to taper from {arm} to {wrist} stitches over "
            f"{sleeve_shaping_rounds} rounds (about "
            f"{_num(sleeve_shaping_rounds / rg)} in).",
            f"Sleeve shaping: {sleeve_sched}",
            "Each decrease row removes 2 stitches (k2tog at each side of the "
            "underarm seam).",
            f"Try the sweater on and adjust the sleeve length before "
            f"starting the cuff (target {_num(sleeve_len)} in from the "
            "underarm).",
        ],
    )


def _cuff_section(cuff_rounds, rg, sleeve_len):
    return _section(
        "9. Cuff and finishing",
        intro="Finish with a ribbed cuff, then tidy up.",
        steps=[
            f"Work {cuff_rounds} rounds of k2, p2 ribbing for the cuff "
            f"(about {_num(cuff_rounds / rg)} in).",
            "Bind off loosely in pattern.",
            f"Repeat for the second sleeve. Each sleeve measures about "
            f"{_num(sleeve_len)} in from the underarm to the cuff.",
            "Weave in ends and block. Because this sweater is knitted "
            "top-down, you can adjust body and sleeve length at any point by "
            "knitting more rounds before the ribbing.",
        ],
    )


# ---------------------------------------------------------------------------
# SVG schematic
# ---------------------------------------------------------------------------


def _sweater_svg(neck, front_final, back_final, sleeve_final, armpit, bust,
                 depth_in):
    """Top-down schematic: neck hole, four seams and the derived numbers."""
    size = 360
    cx = cy = size / 2
    neck_r = max(20, neck / 7)
    bust_r = max(85, bust / 2.1)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" '
        f'height="{size}" viewBox="0 0 {size} {size}" '
        'font-family="system-ui, sans-serif">'
    ]
    parts.append(
        f'<circle cx="{cx}" cy="{cy}" r="{bust_r}" fill="#e8dcf2" '
        'stroke="#7b3fa0" stroke-width="2"/>'
    )
    parts.append(
        f'<circle cx="{cx}" cy="{cy}" r="{neck_r}" fill="white" '
        'stroke="#5a2a75" stroke-width="2"/>'
    )
    for angle in (45, 135, 225, 315):
        rad = math.radians(angle)
        parts.append(
            f'<line x1="{cx + neck_r * math.cos(rad):.1f}" '
            f'y1="{cy + neck_r * math.sin(rad):.1f}" '
            f'x2="{cx + bust_r * math.cos(rad):.1f}" '
            f'y2="{cy + bust_r * math.sin(rad):.1f}" stroke="#4aa3a2" '
            'stroke-width="3"/>'
        )
    labels = [
        (cx, cy - bust_r - 14, f"neck {neck} sts"),
        (cx - bust_r + 2, cy, f"back {back_final}", "end"),
        (cx + bust_r - 2, cy, f"front {front_final}"),
        (cx + 10, cy - neck_r - 16, f"arm {sleeve_final} sts"),
        (cx - bust_r + 6, cy + bust_r - 12, f"underarm +{armpit} each side"),
        (cx, cy + bust_r + 26, f"body {bust} sts in the round · "
                               f"~{_num(depth_in)} in neck to underarm"),
    ]
    for x, y, text, *anchor in labels:
        parts.append(
            f'<text x="{x}" y="{y}" font-size="11" fill="#5a2a75" '
            f'{"text-anchor=\'end\'" if anchor and anchor[0] == "end" else ""}'
            f'>{text}</text>'
        )
    parts.append("</svg>")
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


def _render_sections(sections):
    blocks = []
    for section in sections:
        parts = ['<section class="plan-section">',
                 f'<h4>{_esc(section["heading"])}</h4>']
        if section.get("intro"):
            parts.append(f'<p class="plan-intro">{_esc(section["intro"])}</p>')
        if section.get("steps"):
            parts.append(_render_steps(section["steps"]))
        table = section.get("table")
        if table:
            parts.append(_render_table(table))
        elif section.get("rows"):
            parts.append(_render_rows(section["rows"]))
        parts.append("</section>")
        blocks.append("\n".join(parts))
    return "\n".join(blocks)


def to_html(result):
    """Render the schematic plus the full guided sweater plan."""
    plan = result["plan"]
    blocks = [f"<div class='output-box'>{result['svg']}</div>"]

    if plan["warnings"]:
        items = "".join(f"<li>{_esc(w)}</li>" for w in plan["warnings"])
        blocks.append(
            f"<div class='warning-box'><strong>Worth a second look</strong>"
            f"<ul>{items}</ul></div>"
        )

    assumptions = "".join(
        f"<li>{_esc(a)}</li>" for a in plan["assumptions"]
    )
    blocks.append(
        "<section class='plan-section'>"
        "<h4>How this sweater is built</h4>"
        f"<ul class='plan-assumptions'>{assumptions}</ul>"
        "</section>"
    )
    blocks.append("<h3 class='plan-title'>Your knitting plan</h3>")
    blocks.append(_render_sections(plan["sections"]))
    return "\n".join(blocks)


DEMO = {
    "TITLE": TITLE,
    "DEFAULT_INPUTS": DEFAULT_INPUTS,
    "compute": compute,
    "to_html": to_html,
}