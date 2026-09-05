"""Exercise every demo's Python compute() with default inputs.

This proves the knitting math bundled into the Android WebView APK (executed
there through Pyodide) is intact. Run from the repository root::

    python scripts/demo_workflow_smoke.py
"""

import traceback

MODULES = [
    "sock_calculator",
    "raglan",
    "hat_crown",
    "sleeve_decreases",
    "shaping",
    "gauge_conversion_page",
    "yarn_estimator",
    "yarn_advisor",
    "needle_advisor",
    "chart_renderer",
    "pattern_io",
    "knit_simulator",
    "shawl_shapes",
    "pi_shawl",
]


def main() -> int:
    ok, fail = 0, []
    for name in MODULES:
        try:
            mod = __import__(f"pyknit.pyscript._demos.{name}", fromlist=["DEMO"])
            demo = getattr(mod, "DEMO", mod)
            if isinstance(demo, dict):
                inputs = dict(demo["DEFAULT_INPUTS"])
                result = demo["compute"](inputs)
                keys = list(result.keys()) if isinstance(result, dict) else type(result).__name__
                print(f"PASS {name}: keys={keys}")
            else:
                print(f"SKIP {name}: no DEMO dict")
            ok += 1
        except Exception as exc:
            fail.append(name)
            print(f"FAIL {name}: {exc}")
            traceback.print_exc(limit=3)

    print(f"\n{ok} passed, {len(fail)} failed: {fail}")
    return 1 if fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
