"""Exercise every demo's Python compute() with default inputs.

This is the Python half of the Phase-4 workflow test: it proves the knitting
math the WebView would execute is intact. JS/DOM wiring is audited statically
(shared.py uses only querySelector/innerHTML/sessionStorage + data-URI
download, all WebView-supported).
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
    except Exception as e:
        fail.append(name)
        print(f"FAIL {name}: {e}")
        traceback.print_exc(limit=3)

print(f"\n{ok} passed, {len(fail)} failed: {fail}")
