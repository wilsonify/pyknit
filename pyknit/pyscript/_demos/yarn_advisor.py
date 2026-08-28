"""Yarn Advisor demo: recommend yarn weight, fiber, and characteristics.

A deterministic, explainable yarn-selection tool.  Returns recommendations,
ranges, tradeoffs, and warnings — never a single "perfect" answer.
"""

import math

DEFAULT_INPUTS = {
    "project_type": "scarf",
    "target_gauge": "dk",
    "fabric_drape": "balanced",
    "warmth": "medium",
    "fiber_pref": "any",
    "intended_use": "everyday",
}

TITLE = "Yarn Advisor"

PROJECT_TYPES = {
    "scarf": {"label": "Scarf / Cowl", "needs_drape": True, "needs_structure": False},
    "hat": {"label": "Hat / Beanie", "needs_drape": False, "needs_structure": True},
    "sock": {"label": "Socks", "needs_drape": False, "needs_structure": True},
    "sweater": {"label": "Sweater", "needs_drape": True, "needs_structure": True},
    "shawl": {"label": "Shawl / Wrap", "needs_drape": True, "needs_structure": False},
    "blanket": {"label": "Blanket", "needs_drape": True, "needs_structure": False},
    "mittens": {
        "label": "Mittens / Gloves",
        "needs_drape": False,
        "needs_structure": True,
    },
    "baby": {"label": "Baby garment", "needs_drape": True, "needs_structure": False},
}

GAUGE_CATEGORIES = {
    "lace": {"label": "Lace (30+ sts/in)", "sts_per_in": 32, "weight": "lace"},
    "fingering": {
        "label": "Fingering (27-32 sts/in)",
        "sts_per_in": 28,
        "weight": "fingering",
    },
    "sport": {"label": "Sport (23-26 sts/in)", "sts_per_in": 24, "weight": "sport"},
    "dk": {"label": "DK (21-24 sts/in)", "sts_per_in": 22, "weight": "dk"},
    "worsted": {
        "label": "Worsted (18-20 sts/in)",
        "sts_per_in": 19,
        "weight": "worsted",
    },
    "aran": {"label": "Aran (16-18 sts/in)", "sts_per_in": 17, "weight": "aran"},
    "bulky": {"label": "Bulky (14-17 sts/in)", "sts_per_in": 15, "weight": "bulky"},
    "super_bulky": {
        "label": "Super Bulky (9-12 sts/in)",
        "sts_per_in": 10,
        "weight": "super bulky",
    },
}

DRAPE_LEVELS = {
    "very_drapey": {"label": "Very drapey (flowing)", "drape_score": 0.9},
    "drapey": {"label": "Drapey (soft drape)", "drape_score": 0.7},
    "balanced": {"label": "Balanced", "drape_score": 0.5},
    "structured": {"label": "Structured (firm)", "drape_score": 0.3},
    "very_structured": {"label": "Very structured (stiff)", "drape_score": 0.1},
}

WARMTH_LEVELS = {
    "warmest": {"label": "Warmest", "warmth_score": 1.0},
    "warm": {"label": "Warm", "warmth_score": 0.75},
    "medium": {"label": "Medium", "warmth_score": 0.5},
    "light": {"label": "Light", "warmth_score": 0.25},
    "cool": {"label": "Cool / breathabe", "warmth_score": 0.1},
}

FIBER_TYPES = {
    "merino": {
        "label": "Merino Wool",
        "warmth": 0.8,
        "drape": 0.6,
        "elasticity": 0.8,
        "washable": True,
        "breathable": True,
        "durability": 0.7,
    },
    "wool": {
        "label": "Non-superwash Wool",
        "warmth": 0.85,
        "drape": 0.5,
        "elasticity": 0.7,
        "washable": False,
        "breathable": True,
        "durability": 0.8,
    },
    "alpaca": {
        "label": "Alpaca",
        "warmth": 0.95,
        "drape": 0.8,
        "elasticity": 0.3,
        "washable": False,
        "breathable": True,
        "durability": 0.6,
    },
    "cotton": {
        "label": "Cotton",
        "warmth": 0.1,
        "drape": 0.4,
        "elasticity": 0.1,
        "washable": True,
        "breathable": True,
        "durability": 0.9,
    },
    "silk": {
        "label": "Silk blend",
        "warmth": 0.3,
        "drape": 0.9,
        "elasticity": 0.2,
        "washable": False,
        "breathable": True,
        "durability": 0.7,
    },
    "acrylic": {
        "label": "Acrylic",
        "warmth": 0.5,
        "drape": 0.5,
        "elasticity": 0.5,
        "washable": True,
        "breathable": False,
        "durability": 0.8,
    },
    "linen": {
        "label": "Linen",
        "warmth": 0.05,
        "drape": 0.3,
        "elasticity": 0.05,
        "washable": True,
        "breathable": True,
        "durability": 0.95,
    },
    "blends": {
        "label": "Wool blends",
        "warmth": 0.65,
        "drape": 0.55,
        "elasticity": 0.6,
        "washable": True,
        "breathable": True,
        "durability": 0.75,
    },
    "any": {
        "label": "No preference",
        "warmth": 0.5,
        "drape": 0.5,
        "elasticity": 0.5,
        "washable": True,
        "breathable": True,
        "durability": 0.7,
    },
}

USE_CASES = {
    "everyday": {
        "label": "Everyday wear",
        "durability_need": 0.7,
        "washable_need": 0.6,
    },
    "gift": {"label": "Gift", "durability_need": 0.5, "washable_need": 0.5},
    "luxury": {
        "label": "Luxury / heirloom",
        "durability_need": 0.3,
        "washable_need": 0.2,
    },
    "baby": {"label": "Baby / child", "durability_need": 0.8, "washable_need": 0.9},
    "outdoor": {
        "label": "Outdoor / active",
        "durability_need": 0.9,
        "washable_need": 0.7,
    },
    "home": {"label": "Home decor", "durability_need": 0.6, "washable_need": 0.5},
}


def compute(inputs):
    project_key = inputs.get("project_type", "scarf")
    gauge_key = inputs.get("target_gauge", "dk")
    drape_key = inputs.get("fabric_drape", "balanced")
    warmth_key = inputs.get("warmth", "medium")
    fiber_key = inputs.get("fiber_pref", "any")
    use_key = inputs.get("intended_use", "everyday")

    if project_key not in PROJECT_TYPES:
        raise ValueError(f"Unknown project type: {project_key}")
    if gauge_key not in GAUGE_CATEGORIES:
        raise ValueError(f"Unknown gauge category: {gauge_key}")
    if drape_key not in DRAPE_LEVELS:
        raise ValueError(f"Unknown drape level: {drape_key}")
    if warmth_key not in WARMTH_LEVELS:
        raise ValueError(f"Unknown warmth level: {warmth_key}")
    if fiber_key not in FIBER_TYPES:
        raise ValueError(f"Unknown fiber preference: {fiber_key}")
    if use_key not in USE_CASES:
        raise ValueError(f"Unknown intended use: {use_key}")

    project = PROJECT_TYPES[project_key]
    gauge = GAUGE_CATEGORIES[gauge_key]
    drape = DRAPE_LEVELS[drape_key]
    warmth_pref = WARMTH_LEVELS[warmth_key]
    fiber_pref = FIBER_TYPES[fiber_key]
    use_case = USE_CASES[use_key]

    recommendations = _score_fibers(project, drape, warmth_pref, fiber_pref, use_case)

    warnings = _check_conflicts(project, gauge, drape, warmth_pref, fiber_pref)

    best = recommendations[0] if recommendations else None
    alternatives = recommendations[1:4] if len(recommendations) > 1 else []

    assumptions = [
        f"Project: {project['label']}.",
        f"Target gauge: {gauge['label']}.",
        f"Fabric: {drape['label']}.",
        f"Warmth: {warmth_pref['label']}.",
        f"Use: {use_case['label']}.",
    ]
    if fiber_key != "any":
        assumptions.append(f"Fiber preference: {fiber_pref['label']}.")

    yarn_weight = gauge["weight"]

    return {
        "project_type": project_key,
        "project_label": project["label"],
        "yarn_weight": yarn_weight,
        "yarn_weight_label": gauge["label"],
        "best_fiber": best["fiber"] if best else None,
        "best_fiber_label": best["label"] if best else None,
        "best_score": best["score"] if best else 0,
        "best_confidence": best["confidence"] if best else "low",
        "recommendations": [
            {
                "fiber": r["fiber"],
                "label": r["label"],
                "score": r["score"],
                "reasons": r["reasons"],
                "tradeoffs": r["tradeoffs"],
                "confidence": r["confidence"],
            }
            for r in recommendations
        ],
        "alternatives": [{"label": a["label"], "score": a["score"], "reasons": a["reasons"]} for a in alternatives],
        "warnings": warnings,
        "assumptions": assumptions,
        "drape_score": drape["drape_score"],
        "warmth_score": warmth_pref["warmth_score"],
    }


def _score_fibers(project, drape, warmth_pref, fiber_pref, use_case):
    pref_key = fiber_pref.get("label", "").split()[0].lower() if fiber_pref else ""
    scores = []
    for key, fiber in FIBER_TYPES.items():
        if key == "any":
            continue
        score = 0.0
        reasons = []
        tradeoffs = []

        drape_match = 1.0 - abs(fiber["drape"] - drape["drape_score"])
        score += drape_match * 30
        if drape_match > 0.8:
            reasons.append("good drape match")
        elif drape_match < 0.4:
            tradeoffs.append("drape may differ from desired")

        warmth_match = 1.0 - abs(fiber["warmth"] - warmth_pref["warmth_score"])
        score += warmth_match * 25
        if warmth_match > 0.8:
            reasons.append("warmth matches preference")
        elif warmth_match < 0.4:
            tradeoffs.append("warmth level differs from preference")

        durability_match = fiber["durability"] * use_case["durability_need"]
        score += durability_match * 20
        if durability_match > 0.6:
            reasons.append("durable enough for intended use")

        washable_match = (
            1.0
            if (fiber["washable"] and use_case["washable_need"] > 0.5)
            else (0.5 if not fiber["washable"] and use_case["washable_need"] < 0.3 else 0.0)
        )
        score += washable_match * 15
        if washable_match > 0.8:
            reasons.append("easy care for this use")
        elif washable_match < 0.1:
            tradeoffs.append("hand-wash only")

        if pref_key and key.startswith(pref_key):
            score += 15
            reasons.append("matches your fiber preference")

        confidence = "high" if len(reasons) >= 3 else "medium" if len(reasons) >= 2 else "low"

        scores.append(
            {
                "fiber": key,
                "label": fiber["label"],
                "score": round(score, 1),
                "reasons": reasons,
                "tradeoffs": tradeoffs,
                "confidence": confidence,
            }
        )

    scores.sort(key=lambda x: x["score"], reverse=True)
    return scores


def _check_conflicts(project, gauge, drape, warmth_pref, fiber_pref):
    warnings = []
    if project["needs_structure"] and drape["drape_score"] > 0.7:
        warnings.append(
            f"{project['label']} usually benefits from more structure. " "A very drapey fabric may lose shape."
        )
    if project["needs_drape"] and drape["drape_score"] < 0.3:
        warnings.append(
            f"{project['label']} usually looks best with some drape. " "A very stiff fabric may not drape well."
        )
    if gauge["sts_per_in"] > 24 and warmth_pref["warmth_score"] > 0.7:
        warnings.append(
            "Fine gauge with maximum warmth is unusual. Consider a thicker "
            "yarn with a looser gauge for better insulation."
        )
    if gauge["sts_per_in"] < 14 and drape["drape_score"] > 0.7:
        warnings.append(
            "Bulky yarn with very drapey fabric may be heavy and sag. " "Consider a lighter yarn or more structure."
        )
    return warnings


def to_html(result):
    parts = []

    if result["best_fiber"]:
        parts.append(
            f"<div class='stat-row'>"
            f"<span class='stat-pill'>Best match: <em>{_esc(result['best_fiber_label'])}</em></span>"
            f"<span class='stat-pill'>Yarn weight: <em>{_esc(result['yarn_weight_label'])}</em></span>"
            f"<span class='stat-pill'>Confidence: <em>{result['best_confidence']}</em></span>"
            f"</div>"
        )

    if result.get("recommendations"):
        parts.append("<h3>Recommendations</h3>")
        for i, rec in enumerate(result["recommendations"]):
            rank = "Best" if i == 0 else f"Alternative {i}"
            badge = "best" if i == 0 else "alt"
            reasons_html = (
                "".join(f"<li>{_esc(r)}</li>" for r in rec["reasons"]) if rec["reasons"] else "<li>general fit</li>"
            )
            tradeoffs_html = "".join(f"<li>{_esc(t)}</li>" for t in rec["tradeoffs"]) if rec["tradeoffs"] else ""
            parts.append(
                f"<div class='plan-section'>"
                f"<h4>{rank}: {_esc(rec['label'])} "
                f"<span class='stat-pill' style='font-size:0.75rem'>{rec['score']:.0f}/100</span></h4>"
                f"<p style='font-size:0.88rem;color:#555'>Why this fiber:</p>"
                f"<ul style='padding-left:1.3rem;font-size:0.9rem'>{reasons_html}</ul>"
            )
            if tradeoffs_html:
                parts.append(
                    f"<p style='font-size:0.88rem;color:#555;margin-top:0.5rem'>Tradeoffs:</p>"
                    f"<ul style='padding-left:1.3rem;font-size:0.9rem;color:#666'>{tradeoffs_html}</ul>"
                )
            parts.append("</div>")

    if result.get("warnings"):
        items = "".join(f"<li>{_esc(w)}</li>" for w in result["warnings"])
        parts.append("<div class='warning-box'><strong>Worth a second look</strong>" f"<ul>{items}</ul></div>")

    parts.append("<div class='output-box'>")
    parts.append("<h3>Assumptions</h3>")
    parts.append("<ul style='padding-left:1.3rem'>")
    for a in result.get("assumptions", []):
        parts.append(f"<li>{_esc(a)}</li>")
    parts.append("</ul></div>")

    parts.append(
        "<p class='field-hint'>This tool gives recommendations, not rules. "
        "Every yarn and knitter is different — swatch to confirm.</p>"
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
