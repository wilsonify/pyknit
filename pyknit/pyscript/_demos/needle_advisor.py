"""Needle Advisor demo: recommend needle size, type, and cable length.

A deterministic, explainable needle-selection tool.  Returns a starting
recommendation, explains the reasoning, and reminds users to swatch.
"""

DEFAULT_INPUTS = {
    "yarn_weight": "worsted",
    "target_gauge": 18,
    "project_type": "scarf",
    "fabric_density": "balanced",
    "construction": "flat",
}

TITLE = "Needle Advisor"
CABLE_32_40 = "32-40 in (80-100 cm)"
OUTPUT_BOX = "<div class='output-box'>"

YARN_WEIGHTS = {
    "lace": {
        "label": "Lace",
        "typical_gauge": (32, 34),
        "typical_needle_mm": (1.5, 2.25),
        "typical_needle_us": (0, 1),
    },
    "fingering": {
        "label": "Fingering",
        "typical_gauge": (27, 32),
        "typical_needle_mm": (2.0, 3.25),
        "typical_needle_us": (0, 3),
    },
    "sport": {
        "label": "Sport",
        "typical_gauge": (23, 26),
        "typical_needle_mm": (3.25, 3.75),
        "typical_needle_us": (3, 5),
    },
    "dk": {
        "label": "DK",
        "typical_gauge": (21, 24),
        "typical_needle_mm": (3.75, 4.5),
        "typical_needle_us": (5, 7),
    },
    "worsted": {
        "label": "Worsted",
        "typical_gauge": (18, 20),
        "typical_needle_mm": (4.5, 5.0),
        "typical_needle_us": (7, 8),
    },
    "aran": {
        "label": "Aran",
        "typical_gauge": (16, 18),
        "typical_needle_mm": (5.0, 5.5),
        "typical_needle_us": (8, 9),
    },
    "bulky": {
        "label": "Bulky",
        "typical_gauge": (14, 17),
        "typical_needle_mm": (5.5, 8.0),
        "typical_needle_us": (9, 11),
    },
    "super_bulky": {
        "label": "Super Bulky",
        "typical_gauge": (9, 12),
        "typical_needle_mm": (8.0, 12.0),
        "typical_needle_us": (11, 17),
    },
}

DENSITY_LEVELS = {
    "loose": {"label": "Loose / open fabric", "adjustment": -0.25},
    "balanced": {"label": "Balanced (standard)", "adjustment": 0},
    "dense": {"label": "Dense / tight fabric", "adjustment": 0.25},
    "very_dense": {"label": "Very dense (armor-like)", "adjustment": 0.5},
}

CONSTRUCTION_TYPES = {
    "flat": {
        "label": "Flat (back and forth)",
        "needle_type": "straight or circular",
        "can_magic_loop": False,
    },
    "round_seamless": {
        "label": "In the round (seamless)",
        "needle_type": "circular or DPNs",
        "can_magic_loop": True,
    },
    "round_dpns": {
        "label": "In the round (DPNs)",
        "needle_type": "double-pointed needles",
        "can_magic_loop": False,
    },
    "small_circumference": {
        "label": "Small circumference (socks, sleeves)",
        "needle_type": "DPNs or magic loop",
        "can_magic_loop": True,
    },
}

PROJECT_TYPES = {
    "scarf": {"label": "Scarf / Cowl", "default_construction": "flat"},
    "hat": {"label": "Hat / Beanie", "default_construction": "round_seamless"},
    "sock": {"label": "Socks", "default_construction": "small_circumference"},
    "sweater": {
        "label": "Sweater (top-down)",
        "default_construction": "round_seamless",
    },
    "shawl": {"label": "Shawl", "default_construction": "flat"},
    "blanket": {"label": "Blanket", "default_construction": "flat"},
    "mittens": {"label": "Mittens", "default_construction": "round_dpns"},
    "baby": {"label": "Baby garment", "default_construction": "round_seamless"},
}

NEEDLE_SIZES_MM = [
    1.5,
    1.75,
    2.0,
    2.25,
    2.5,
    2.75,
    3.0,
    3.25,
    3.5,
    3.75,
    4.0,
    4.5,
    5.0,
    5.5,
    6.0,
    6.5,
    7.0,
    7.5,
    8.0,
    9.0,
    10.0,
    12.0,
    15.0,
    20.0,
]

MM_TO_US = {
    1.5: "0",
    1.75: "00",
    2.0: "0",
    2.25: "1",
    2.5: "1.5",
    2.75: "2",
    3.0: "2.5",
    3.25: "3",
    3.5: "4",
    3.75: "5",
    4.0: "6",
    4.5: "7",
    5.0: "8",
    5.5: "9",
    6.0: "10",
    6.5: "10.5",
    7.0: "10.75",
    7.5: "11",
    8.0: "11",
    9.0: "13",
    10.0: "15",
    12.0: "17",
    15.0: "19",
    20.0: "35",
}


def compute(inputs):
    yarn_key = inputs.get("yarn_weight", "worsted")
    target_gauge = _pos_float(inputs, "target_gauge", "target gauge")
    project_key = inputs.get("project_type", "scarf")
    density_key = inputs.get("fabric_density", "balanced")
    construction_key = inputs.get("construction", "flat")

    if yarn_key not in YARN_WEIGHTS:
        raise ValueError(f"Unknown yarn weight: {yarn_key}")
    if project_key not in PROJECT_TYPES:
        raise ValueError(f"Unknown project type: {project_key}")
    if density_key not in DENSITY_LEVELS:
        raise ValueError(f"Unknown fabric density: {density_key}")
    if construction_key not in CONSTRUCTION_TYPES:
        raise ValueError(f"Unknown construction type: {construction_key}")

    yarn = YARN_WEIGHTS[yarn_key]
    density = DENSITY_LEVELS[density_key]
    construction = CONSTRUCTION_TYPES[construction_key]
    project = PROJECT_TYPES[project_key]

    gauge_low, gauge_high = yarn["typical_gauge"]
    in_range = gauge_low <= target_gauge <= gauge_high
    if in_range:
        gauge_position = (target_gauge - gauge_low) / max(1, gauge_high - gauge_low)
    else:
        gauge_position = 0.5

    needle_mm_low, needle_mm_high = yarn["typical_needle_mm"]
    needle_span = needle_mm_high - needle_mm_low
    base_mm = needle_mm_low + gauge_position * needle_span

    adjusted_mm = base_mm + density["adjustment"]
    adjusted_mm = max(1.5, min(20.0, adjusted_mm))

    recommended_mm = _nearest_needle(adjusted_mm)
    recommended_us = MM_TO_US.get(recommended_mm, "?")

    size_range_mm = [
        _nearest_needle(max(1.5, recommended_mm - 0.5)),
        _nearest_needle(min(20.0, recommended_mm + 0.5)),
    ]
    size_range_us = [MM_TO_US.get(s, "?") for s in size_range_mm]

    warnings = []
    if not in_range:
        if target_gauge < gauge_low:
            warnings.append(
                f"Your gauge ({target_gauge} sts/in) is finer than typical for "
                f"{yarn['label']} yarn ({gauge_low}-{gauge_high} sts/in). "
                "You may need a much smaller needle than usual."
            )
        else:
            warnings.append(
                f"Your gauge ({target_gauge} sts/in) is looser than typical for "
                f"{yarn['label']} yarn ({gauge_low}-{gauge_high} sts/in). "
                "You may need a much larger needle than usual."
            )

    if construction_key == "small_circumference":
        warnings.append("For socks and small items, use DPNs or magic loop. Fixed circulars may be too long.")

    cable_length = _recommend_cable_length(construction_key, project_key)

    assumptions = [
        f"Yarn weight: {yarn['label']}.",
        f"Typical gauge: {gauge_low}-{gauge_high} sts/in.",
        f"Your target gauge: {target_gauge} sts/in.",
        f"Fabric: {density['label']}.",
        f"Construction: {construction['label']}.",
        "This is a starting point. Always swatch to confirm your needle size.",
    ]

    needle_types = _needle_type_recommendation(construction_key)

    return {
        "yarn_weight": yarn_key,
        "yarn_weight_label": yarn["label"],
        "recommended_mm": recommended_mm,
        "recommended_us": recommended_us,
        "range_mm": size_range_mm,
        "range_us": size_range_us,
        "needle_types": needle_types,
        "cable_length": cable_length,
        "target_gauge": target_gauge,
        "typical_gauge": f"{gauge_low}-{gauge_high}",
        "in_range": in_range,
        "density_adjustment": density["adjustment"],
        "construction_label": construction["label"],
        "project_label": project["label"],
        "warnings": warnings,
        "assumptions": assumptions,
    }


def _pos_float(inputs, key, label):
    raw = inputs.get(key)
    if raw is None or str(raw).strip() == "":
        raise ValueError(f"{label} is required")
    try:
        val = float(raw)
    except (TypeError, ValueError):
        raise ValueError(f"{label} must be a number")
    if val <= 0:
        raise ValueError(f"{label} must be positive")
    return val


def _nearest_needle(target_mm):
    closest = NEEDLE_SIZES_MM[0]
    for size in NEEDLE_SIZES_MM:
        if abs(size - target_mm) < abs(closest - target_mm):
            closest = size
    return closest


def _recommend_cable_length(construction_key, project_key):
    if construction_key == "flat":
        return {
            "label": CABLE_32_40,
            "note": "Long enough for flat pieces; can also use straight needles.",
        }
    if construction_key == "round_dpns":
        return {
            "label": "N/A (DPNs)",
            "note": "Use a set of 4-5 double-pointed needles.",
        }
    if project_key == "hat":
        return {
            "label": "16 in (40 cm)",
            "note": "Short circular for hat circumference.",
        }
    if project_key == "sock":
        return {
            "label": "32 in (80 cm) for magic loop, or DPNs",
            "note": "Use 9-inch circular for the body if preferred.",
        }
    if project_key == "sweater":
        return {
            "label": CABLE_32_40,
            "note": "Long enough for body circumference; use 24 in for sleeves.",
        }
    if project_key == "shawl":
        return {
            "label": CABLE_32_40,
            "note": "Long circular for body; switch to straights if preferred.",
        }
    return {
        "label": "24-32 in (60-80 cm)",
        "note": "A versatile length for most circular projects.",
    }


def _needle_type_recommendation(construction_key):
    types = []
    if construction_key == "flat":
        types.append(
            {
                "type": "Straight needles",
                "when": "Simple flat pieces like scarves and blankets.",
            }
        )
        types.append(
            {
                "type": "Circular needles (32+ in)",
                "when": "Flat pieces wider than straight needles allow; easier on wrists.",
            }
        )
    elif construction_key == "round_seamless":
        types.append(
            {
                "type": "Circular needles",
                "when": "Primary choice for seamless in-the-round knitting.",
            }
        )
        types.append({"type": "DPNs", "when": "For small sections (hat crown decreases)."})
    elif construction_key == "round_dpns":
        types.append(
            {
                "type": "Double-pointed needles",
                "when": "Required for small circumferences like mittens and sock toes.",
            }
        )
        types.append(
            {
                "type": "Magic loop",
                "when": "Alternative to DPNs if you prefer a single circular needle.",
            }
        )
    elif construction_key == "small_circumference":
        types.append(
            {
                "type": "DPNs",
                "when": "Traditional choice for socks, sleeves, and mittens.",
            }
        )
        types.append(
            {
                "type": "Magic loop",
                "when": "Use one long circular needle for everything.",
            }
        )
        types.append(
            {
                "type": "9-inch circular",
                "when": "For the foot of socks if you dislike DPNs/magic loop.",
            }
        )
    return types


def to_html(result):
    parts = []

    parts.append(
        f"<div class='stat-row'>"
        f"<span class='stat-pill'>Needle: <em>{result['recommended_mm']} mm (US {result['recommended_us']})</em></span>"
        f"<span class='stat-pill'>Range: <em>{result['range_mm'][0]}-{result['range_mm'][1]} mm</em></span>"
        f"<span class='stat-pill'>Construction: <em>{_esc(result['construction_label'])}</em></span>"
        f"</div>"
    )

    parts.append(OUTPUT_BOX)
    parts.append("<h3>Starting needle size</h3>")
    parts.append("<p style='font-size:1.1rem;font-weight:600;color:#5a2a75'>")
    parts.append(f"{result['recommended_mm']} mm &mdash; US {result['recommended_us']}")
    parts.append("</p>")
    parts.append("<p style='font-size:0.9rem;color:#666'>")
    parts.append(f"Your target gauge ({result['target_gauge']} sts/in) is ")
    if result["in_range"]:
        parts.append(
            f"within the typical range ({result['typical_gauge']} sts/in) for {result['yarn_weight_label']} yarn."
        )
    else:
        parts.append(
            f"outside the typical range ({result['typical_gauge']} sts/in) for {result['yarn_weight_label']} yarn."
        )
    parts.append("</p>")
    parts.append("</div>")

    if result.get("needle_types"):
        parts.append(OUTPUT_BOX)
        parts.append("<h3>Needle types to consider</h3>")
        parts.append("<table class='instructions'><tbody>")
        for nt in result["needle_types"]:
            parts.append(f"<tr><th>{_esc(nt['type'])}</th><td>{_esc(nt['when'])}</td></tr>")
        parts.append("</tbody></table></div>")

    if result.get("cable_length"):
        cl = result["cable_length"]
        parts.append(OUTPUT_BOX)
        parts.append("<h3>Cable length</h3>")
        parts.append(f"<p style='font-weight:600'>{_esc(cl['label'])}</p>")
        parts.append(f"<p style='font-size:0.9rem;color:#666'>{_esc(cl['note'])}</p>")
        parts.append("</div>")

    if result.get("warnings"):
        items = "".join(f"<li>{_esc(w)}</li>" for w in result["warnings"])
        parts.append("<div class='warning-box'><strong>Heads up</strong>" f"<ul>{items}</ul></div>")

    parts.append(OUTPUT_BOX)
    parts.append("<h3>Assumptions</h3>")
    parts.append("<ul style='padding-left:1.3rem'>")
    for a in result.get("assumptions", []):
        parts.append(f"<li>{_esc(a)}</li>")
    parts.append("</ul></div>")

    parts.append(
        "<p class='field-hint'>This is a starting recommendation. "
        "Your gauge swatch determines the final needle size — "
        "go up a size for looser fabric, down for tighter.</p>"
    )

    return "\n".join(parts)


def _esc(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


DEMO = {
    "TITLE": TITLE,
    "DEFAULT_INPUTS": DEFAULT_INPUTS,
    "compute": compute,
    "to_html": to_html,
}
