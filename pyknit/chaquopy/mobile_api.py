"""Small Chaquopy bridge for the native pyKnit Android app.

This module is intentionally an adapter, not a second knitting engine. The
existing demo modules remain authoritative for calculations, instruction
creation, and simulation semantics. Kotlin receives JSON-safe dictionaries
and owns only navigation and presentation.
"""

import json

from pyknit.pyscript._demos import (
    hat_crown,
    knit_simulator,
    raglan,
    sleeve_decreases,
    sock_calculator,
    yarn_estimator,
)

_MODULES = {
    "raglan": raglan,
    "hat": hat_crown,
    "sleeve": sleeve_decreases,
    "sock": sock_calculator,
    "yarn": yarn_estimator,
}


def _inputs(name, raw):
    if raw is None:
        raw = "{}"
    values = json.loads(raw) if isinstance(raw, str) else dict(raw)
    if not isinstance(values, dict):
        raise ValueError("Inputs must be a JSON object")
    defaults = dict(_MODULES[name].DEMO["DEFAULT_INPUTS"])
    defaults.update(values)
    return defaults


def _summary(name, result):
    if name == "raglan":
        m = result["meta"]
        return {
            "title": "Raglan Sweater Planner",
            "cast_on": m["neck"],
            "bust": m["bust"],
            "arm": m["arm"],
            "rows": m["raglan_total_rounds"],
            "sections": [s["label"] for s in result["sim_plan"]["sections"]],
            "message": (
                f"Cast on {m['neck']} sts · {m['bust']} body sts · "
                f"{m['raglan_total_rounds']} yoke rounds · sleeves {m['arm']} sts"
            ),
        }
    if name == "hat":
        return {
            "title": "Hat Crown Planner",
            "cast_on": result["stitches"],
            "rows": len(result["plan"]),
            "message": (
                f"{result['stitches']} cast-on sts · {len(result['plan'])} crown rounds · "
                f"{result['repeats']} decrease repeats"
            ),
        }
    if name == "sleeve":
        return {
            "title": "Sleeve Decreases",
            "cast_on": result["starting"],
            "rows": result["rows"],
            "message": (
                f"{result['starting']} → {result['ending']} sts over "
                f"{result['rows']} rows · {result['summary']['number_of_decrease_rows']} "
                "decrease rows"
            ),
        }
    if name == "sock":
        rounds = result["sim"].get("total_rounds", len(result["sim"].get("rounds", [])) - 1)
        return {
            "title": "Sock Calculator",
            "cast_on": result["cast_on_stitches"],
            "rows": rounds,
            "message": (
                f"Cast on {result['cast_on_stitches']} sts · " f"{result['ankle_stitches']} ankle sts · {rounds} rounds"
            ),
        }
    return {
        "title": "Yarn & Time Estimator",
        "message": (
            f"{result['project_stitches']:,} stitches · " f"{result['yards']:.0f} yd · {result['grams']:.0f} g"
        ),
        "yards": result["yards"],
        "grams": result["grams"],
    }


def _sock_sim_plan(result):
    """Adapt the Sock Calculator's existing structured simulation pattern.

    The rounds are already the calculator's canonical output; the text is only
    a readable field value for the native UI. The simulator executes
    ``sock_plan`` and therefore never reparses or recreates sock arithmetic.
    """
    source = result.get("sim")
    if not isinstance(source, dict):
        return None
    rounds = source.get("rounds")
    if not isinstance(rounds, list) or not rounds:
        return None
    return {
        "source": "sock_calculator",
        "garment": "sock",
        "instructions": "\n".join(str(r.get("label", "row")) for r in rounds) + "\n",
        "rounds": rounds,
        "cast_on_stitches": source.get("cast_on_stitches"),
        "ankle_stitches": source.get("ankle_stitches"),
        "size": result.get("cast_on_stitches", ""),
        "gauge": source.get("gauge", ""),
        "total_rounds": source.get("total_rounds"),
    }


def _sim_plan_for(name, result):
    if "sim_plan" in result:
        return result["sim_plan"]
    if name == "sock":
        return _sock_sim_plan(result)
    return None


def _payload(name, result, include_result=True):
    payload = {"demo": name, "summary": _summary(name, result)}
    if include_result:
        payload["result"] = result
    sim_plan = _sim_plan_for(name, result)
    if sim_plan is not None:
        payload["sim_plan"] = sim_plan
    return payload


def _json_result(name, result, include_result=True):
    return json.dumps(_payload(name, result, include_result), ensure_ascii=False)


def planner_result(name, inputs_json="{}"):
    """Calculate a planner using its real module and return JSON for the UI."""
    if name not in _MODULES:
        raise ValueError(f"Unknown planner: {name}")
    result = _MODULES[name].DEMO["compute"](_inputs(name, inputs_json))
    return _json_result(name, result)


def _simulation(instructions, sim_plan=None):
    values = {"instructions": instructions}
    if sim_plan is not None:
        if not isinstance(sim_plan, dict):
            raise ValueError("Simulator plan must be a JSON object")
        # The exact text is the join point. Edited instructions are manual
        # patterns and must not retain stale planner section boundaries.
        if sim_plan.get("instructions") == instructions:
            if sim_plan.get("source") == "sock_calculator":
                values["sock_plan"] = sim_plan
            else:
                values["plan"] = sim_plan
    return knit_simulator.DEMO["compute"](values)


def build_simulation(instructions, sim_plan_json=""):
    """Execute exactly the supplied field text, optionally retaining matching
    canonical Planner sections. Called on Build and every manual edit.
    """
    if not instructions or not instructions.strip():
        raise ValueError("Enter knitting instructions before building")
    plan = json.loads(sim_plan_json) if sim_plan_json else None
    result = _simulation(instructions, plan)
    return json.dumps({"simulation": result}, ensure_ascii=False)


def planner_to_simulator(name, inputs_json="{}"):
    """Calculate a planner then execute its exact generated sim_plan."""
    if name not in ("raglan", "hat", "sock"):
        raise ValueError("Only garment planners can open the Knit Simulator")
    planner = _MODULES[name].DEMO["compute"](_inputs(name, inputs_json))
    plan = _sim_plan_for(name, planner)
    if not isinstance(plan, dict) or not plan.get("instructions"):
        raise ValueError(f"{name} did not produce simulator instructions")
    simulation = _simulation(plan["instructions"], plan)
    return json.dumps(
        {
            "planner": _payload(name, planner),
            "instructions": plan["instructions"],
            "sim_plan": plan,
            "simulation": simulation,
        },
        ensure_ascii=False,
    )
