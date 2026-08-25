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
from multiprocessing import Pool

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = os.environ.get("PYQ_BASE", "http://127.0.0.1:8000")
WORKERS = int(os.environ.get("PYQ_WORKERS", "4"))

import qa_demos  # noqa: E402  (same directory; local import)


def _chunked(items, n):
    return [items[i::n] for i in range(n)]


def worker(specs):
    """Run one browser over a chunk of demo specs (one process per worker).

    A crash in a single demo must not kill the whole parallel run: each spec
    is wrapped so an exception becomes a recorded failure with the traceback.
    """
    import traceback  # noqa: F401

    import qa_demos as qd

    qd.BASE = os.environ.get("PYQ_BASE", "http://127.0.0.1:8000")

    from playwright.sync_api import sync_playwright

    reports = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for spec in specs:
            try:
                reports.append(qd.run_demo(browser, spec))
            except Exception:
                tb = traceback.format_exc().splitlines()[-6:]
                rep = qd.QAReport(spec["dir"])
                rep.fail("crash during QA", "; ".join(tb))
                reports.append(rep)
        browser.close()
    return reports


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
    print(f"QA {len(specs)} demos across {WORKERS} parallel browser workers "
          f"(BASE={BASE})")
    chunks = [c for c in _chunked(specs, WORKERS) if c]
    with Pool(WORKERS) as pool:
        per_worker = pool.map(worker, chunks)
    reports = [r for chunk in per_worker for r in chunk]

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
