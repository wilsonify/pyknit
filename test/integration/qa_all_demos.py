"""Parallel real-browser QA across every pyKnit demo.

Each worker process owns one headless Chromium and runs the generic checks
from ``qa_demos`` (boot -> ready -> buttons enabled -> default click ->
output changes -> invalid input -> console/page errors clean) over its chunk
of demos, including the demo-specific extras (knit-simulator controls and
the sock/raglan -> simulator cross-demo navigation).

Run from the repo root::

    python test/integration/qa_all_demos.py

Tunables via environment:

    PYQ_BASE      demo server URL            (default http://127.0.0.1:8000)
    PYQ_WORKERS   parallel browser workers   (default 4)

Exit code 0 = all demos passed; 1 = at least one failure.
"""

import os
import sys
from multiprocessing import get_context

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = os.environ.get("PYQ_BASE", "http://127.0.0.1:8000")
WORKERS = int(os.environ.get("PYQ_WORKERS", "4"))

import qa_demos  # noqa: E402  (same directory; local import)


def _estimate_cost(spec):
    """Heuristic cost weight for a demo (higher = slower).

    The extras (simulate-nav, knit-simulator) add navigation, polling, and
    multi-click sequences that dominate wall-clock time.  Sorting demos by
    this weight before dispatching lets the longest-processing-time-first
    (LPT) scheduler keep all workers busy.
    """
    weight = 1
    extra = spec.get("extra")
    if extra == "simulate-nav":
        sim = spec.get("sim", {})
        # More steps and longer instructions = more polling time.
        weight = 3 + sim.get("min_steps", 0) // 20
    elif extra == "knit-simulator":
        weight = 5
    if len(spec.get("buttons", [])) > 1:
        weight += 1
    return weight


def _worker_run_one(spec):
    """Run a single demo and return its QAReport.

    Each call opens its own browser, runs the demo, and closes the browser.
    Used with ``pool.imap_unordered`` for dynamic load balancing.
    """
    import traceback  # noqa: F401

    import qa_demos as qd

    qd.BASE = os.environ.get("PYQ_BASE", "http://127.0.0.1:8000")

    from playwright.sync_api import sync_playwright

    name = spec["dir"]
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            report = qd.run_demo(browser, spec)
        except Exception:
            tb = traceback.format_exc().splitlines()[-6:]
            report = qd.QAReport(name)
            report.fail("crash during QA", "; ".join(tb))
        browser.close()
    return report


def _flag_if_present(items, headline, limit):
    if not items:
        return False
    print(headline % len(items))
    for item in items[:limit]:
        print("        - " + item)
    return True


def _print_report(r):
    status = "PASS" if r.passed else "FAIL"
    print(f"\n[{status}] {r.name}  (loaded in {r.load_ms} ms)")
    for n in r.notes:
        print("     note: " + n)
    for f in r.failures:
        print("     FAIL: " + f)
    ok = r.passed
    if _flag_if_present(r.console_errors, "     boot console errors: %d", 5):
        ok = False
    if _flag_if_present(r.page_errors, "     page errors (%d):", 5):
        ok = False
    _flag_if_present(
        [c[:160] for c in r.interaction_console],
        "     interaction console messages (expected tracebacks): %d",
        3,
    )
    if _flag_if_present(r.failed_requests, "     failed requests (%d):", 8):
        ok = False
    return ok


def main():
    specs = qa_demos.DEMOS
    # Sort heaviest-first so LPT scheduling balances the load:
    # the slowest demos start first and fast ones fill the gaps.
    specs_sorted = sorted(specs, key=lambda s: _estimate_cost(s), reverse=True)
    print(f"QA {len(specs)} demos across {WORKERS} parallel browser workers " f"(BASE={BASE}, dynamic scheduling)")
    ctx = get_context("spawn")
    with ctx.Pool(WORKERS) as pool:
        reports = list(pool.imap_unordered(_worker_run_one, specs_sorted))

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p2:
        b2 = p2.chromium.launch(headless=True)
        try:
            idx_problems = qa_demos.check_index(b2)
        finally:
            b2.close()

    print("\n" + "=" * 70)
    print("QA SUMMARY")
    print("=" * 70)
    if idx_problems:
        print("\n[index.html] PROBLEMS")
        for p_ in idx_problems:
            print("     FAIL: " + p_)
    else:
        print("\n[index.html] PASS  (all demo links resolve)")

    passed_all = not idx_problems
    for r in reports:
        passed_all = _print_report(r) and passed_all
    print("\n" + "=" * 70)
    print("ALL PASS" if passed_all else "SOME DEMOS FAILED")
    print("=" * 70)
    sys.exit(0 if passed_all else 1)


if __name__ == "__main__":
    main()
