"""Real-browser QA harness for the pyKnit PyScript demos.

Runs each demo through a headless Chromium via Playwright and verifies:
  - page loads, no failed requests / broken assets
  - no console errors or page errors (JS or Python)
  - status banner reaches 'ready' (pyknit loaded)
  - the demo's run button(s) become enabled
  - clicking produces non-blank output
  - changing an input changes the output
  - invalid input shows a visible error element
"""

import json
import re
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8877"

DEMOS = [
    {"dir": "gauge-conversion", "buttons": ["run-calc", "run-chart"],
     "outputs": ["calc-output", "chart-output"], "errors": ["calc-error", "chart-error"]},
    {"dir": "chart-renderer", "buttons": ["run"], "outputs": ["demo-output"], "errors": ["demo-error"]},
    {"dir": "even-shaping", "buttons": ["run"], "outputs": ["demo-output"], "errors": ["demo-error"]},
    {"dir": "hat-crown", "buttons": ["run"], "outputs": ["demo-output"], "errors": ["demo-error"]},
    {"dir": "pi-shawl", "buttons": ["run"], "outputs": ["demo-output"], "errors": ["demo-error"]},
    {"dir": "pattern-io", "buttons": ["run"], "outputs": ["demo-output"], "errors": ["demo-error"]},
    {"dir": "raglan-sweater", "buttons": ["run"], "outputs": ["demo-output"], "errors": ["demo-error"]},
    {"dir": "shawl-shapes", "buttons": ["run"], "outputs": ["demo-output"], "errors": ["demo-error"]},
    {"dir": "sleeve-decreases", "buttons": ["run"], "outputs": ["demo-output"], "errors": ["demo-error"]},
    {"dir": "sock-calculator", "buttons": ["run"], "outputs": ["demo-output"], "errors": ["demo-error"]},
    {"dir": "yarn-estimator", "buttons": ["run"], "outputs": ["demo-output"], "errors": ["demo-error"]},
]

SKIP_JS_NOISE = (
    "favicon", "DevTools", "Third-party cookie", "Autofill", "cache",
    "GetUserMedia", "Offline", "deprecated", "Source map",
)

# pyknit logs progress to stderr (surfaced as console errors by PyScript);
# these are benign. Real failures are tracebacks or JS errors.
BENIGN_STDERR = (
    "Attempting to import", "pyknit imported", "Running default",
    "SVG generated", "PNG generated", "Text generated", "Using text",
    "Error: Pattern cannot", "Available backends",
)


def is_noise(text):
    if any(tok in text for tok in SKIP_JS_NOISE):
        return True
    if any(tok in text for tok in BENIGN_STDERR):
        return True
    return False


class QAReport:
    def __init__(self, name):
        self.name = name
        self.failures = []
        self.notes = []
        self.console_errors = []       # boot-time console errors (failures)
        self.interaction_console = []  # post-ready console errors (notes)
        self.page_errors = []
        self.failed_requests = []
        self.load_ms = None

    def ok(self, msg):
        print("      PASS  " + msg)

    def note(self, msg):
        print("      note  " + msg)
        self.notes.append(msg)

    def fail(self, msg, detail=""):
        print("      FAIL  " + msg + ("  [" + detail + "]" if detail else ""))
        self.failures.append(msg)

    @property
    def passed(self):
        return not self.failures


def wait_for_ready(page, report, timeout=240_000):
    """Wait until status banner has class 'ready' or buttons are enabled."""
    deadline = time.time() + timeout / 1000
    while time.time() < deadline:
        state = None
        try:
            banner = page.query_selector("#status-banner")
            if banner:
                cls = banner.get_attribute("class") or ""
                if "ready" in cls:
                    state = "ready"
                elif "error" in cls:
                    state = "error"
                elif "loading" in cls:
                    state = "loading"
        except Exception:
            pass
        if state == "ready":
            return "ready"
        if state == "error":
            return "error"
        # also detect boot errors printed to console
        if report.page_errors:
            return "page-error"
        time.sleep(0.5)
    return "timeout"


def run_demo(browser, spec):
    name = spec["dir"]
    report = QAReport(name)
    print("  DEMO: " + name)

    page = browser.new_page(viewport={"width": 1280, "height": 1000})
    ready_flag = {"done": False}

    def on_console(msg):
        text = msg.text
        if msg.type == "error" and not is_noise(text):
            if ready_flag["done"]:
                report.interaction_console.append(text[:400])
            else:
                report.console_errors.append(text[:400])
        if msg.type in ("warning", "log", "info") and "pyknit" in text.lower():
            report.note(f"console[{msg.type}]: {text[:120]}")

    def on_requestfailed(req):
        url = req.url
        if "127.0.0.1:8877" in url or url.startswith("http"):
            report.failed_requests.append(f"{url} :: {req.failure}")

    def on_response(resp):
        if resp.status >= 400:
            report.failed_requests.append(
                f"{resp.status} {resp.url[:160]}"
            )

    def on_pageerror(exc):
        report.page_errors.append(str(exc)[:400])

    page.on("console", on_console)
    page.on("requestfailed", on_requestfailed)
    page.on("response", on_response)
    page.on("pageerror", on_pageerror)

    t0 = time.time()
    try:
        page.goto(f"{BASE}/demos/{name}/demo.html", wait_until="domcontentloaded", timeout=120_000)
    except Exception as exc:
        report.fail("navigation failed", str(exc)[:200])
        page.close()
        return report

    # wait for pyScript boot
    state = wait_for_ready(page, report)
    report.load_ms = int((time.time() - t0) * 1000)

    if report.page_errors:
        report.fail("page (JS/Python) errors during load", "; ".join(report.page_errors[:3]))

    if state == "error":
        report.fail("status banner reached error state", _banner_text(page))
    elif state == "page-error":
        report.fail("pyScript boot aborted by page error", "; ".join(report.page_errors[:2]))
    elif state == "timeout":
        report.fail("never became ready (timeout)", _banner_text(page))

    if state in ("error", "page-error", "timeout"):
        ready_flag["done"] = True
        report.note("skipping interaction because boot failed")
        page.close()
        return report

    ready_flag["done"] = True
    report.ok("pyScript booted, status ready (%.1fs)" % (report.load_ms / 1000))

    # buttons enabled?
    for bid in spec["buttons"]:
        btn = page.query_selector(f"#{bid}")
        if btn is None:
            report.fail(f"button #{bid} missing from DOM")
            continue
        disabled = btn.get_attribute("disabled")
        if disabled == "true" or disabled == "":
            report.fail(f"button #{bid} is disabled after ready")

    # interactive: click each button with default inputs
    for bid in spec["buttons"]:
        fails = exercise(page, spec, bid)
        for f in fails:
            report.fail(f)
        if not fails:
            report.ok(f"default click on #{bid} produced output")

    # verify rendered content (SVG chart or table/pre) is present after a run
    render_fails = check_rendered(page, spec)
    for f in render_fails:
        report.fail(f)
    if not render_fails:
        report.ok("rendered chart/svg output verified")

    # invalid input path
    inv_fails = exercise_invalid(page, spec, name)
    for f in inv_fails:
        report.fail(f)
    if not inv_fails:
        report.ok("invalid input produced a visible error")

    page.close()
    return report


def check_rendered(page, spec):
    """Verify the demo actually rendered visible content (svg/table/pre)."""
    fails = []
    if spec["dir"] == "gauge-conversion":
        # calc -> text output; chart -> svg
        chart_html = page.eval_on_selector("#chart-output", "el => el.innerHTML") or ""
        if "<svg" not in chart_html:
            fails.append("gauge-conversion: chart-output has no <svg> after render")
        return fails
    out_id = spec["outputs"][0]
    out_html = page.eval_on_selector(f"#{out_id}", "el => el.innerHTML") or ""
    if not out_html.strip():
        fails.append(f"#{out_id} empty after interaction")
    # every new demo renders an SVG diagram
    if "<svg" not in out_html:
        fails.append(f"#{out_id} has no <svg> element (chart fallback missing)")
    return fails


def out_text(page, oid):
    el = page.query_selector(f"#{oid}")
    if el is None:
        return ""
    html = el.inner_html() or ""
    return re.sub(r"<[^>]+>", " ", html).strip()


def _banner_text(page):
    el = page.query_selector("#status-message")
    return el.inner_text() if el else "(no status message)"


def exercise(page, spec, button_id):
    """Click with current inputs and check output non-blank + changed on input change."""
    fails = []
    bid = button_id

    btn = page.query_selector(f"#{bid}")
    if btn is None:
        return ["missing button #" + bid]
    btn.click()
    time.sleep(1.5)

    if bid == "run-calc":
        oids, eids = ["calc-output"], ["calc-error"]
    elif bid == "run-chart":
        oids, eids = ["chart-output"], ["chart-error"]
    else:
        oids, eids = ["demo-output"], ["demo-error"]

    for oid in oids:
        text = out_text(page, oid)
        if not text.strip():
            fails.append(f"output #{oid} blank after default click")
    for eid in eids:
        el = page.query_selector(f"#{eid}")
        if el is not None:
            style = el.get_attribute("style") or ""
            if "display: block" in style or "display:block" in style:
                fails.append(f"error #{eid} visible after valid click")

    if not fails and not change_input_and_compare(page, oids, bid):
        fails.append("changing an input did not change the output")

    return fails


def _all_cards():
    return "section.card input[type=number], section.card textarea"


def change_input_and_compare(page, oids, bid):
    """Alter one input, click, and verify the corresponding output changes."""
    if bid == "run-calc":
        target, out_id = "#measurement", "calc-output"
        before = out_text(page, out_id)
        page.query_selector(target).fill("8")
        page.query_selector(f"#{bid}").click()
        time.sleep(1.2)
        after = out_text(page, out_id)
        return after != before and bool(after.strip())
    if bid == "run-chart":
        target, out_id = "#pattern-input", "chart-output"
        before = out_text(page, out_id)
        page.query_selector(target).fill("k2 yo k2tog")
        page.query_selector(f"#{bid}").click()
        time.sleep(1.2)
        after = out_text(page, out_id)
        page.query_selector(target).fill(
            "k2 yo k2tog yo k1\np1 k2 yo k2tog p2"
        )
        return after != before and bool(after.strip())

    out_id = oids[0]

    # textarea-based demos: append a valid row
    ta = page.query_selector("section.card textarea")
    if ta is not None:
        original = ta.input_value()
        before = out_text(page, out_id)
        ta.fill(original + "\nk2tog yo k3")
        page.query_selector(f"#{bid}").click()
        time.sleep(1.2)
        after = out_text(page, out_id)
        ta.fill(original)
        return after != before and bool(after.strip())

    # numeric demos: bump numeric inputs until output changes
    inputs = page.query_selector_all("section.card input[type=number]")
    if not inputs:
        return True
    before = out_text(page, out_id)
    for el in inputs:
        old = el.input_value()
        try:
            num = float(old)
        except ValueError:
            continue
        new = str(int(num) + 1) if float(num).is_integer() else str(num + 1)
        el.fill(new)
        page.query_selector(f"#{bid}").click()
        time.sleep(1.2)
        after = out_text(page, out_id)
        el.fill(old)
        if after != before and bool(after.strip()):
            return True
    return False


def exercise_invalid(page, spec, name):
    """Enter an invalid value, click, and require a visible error element."""
    fails = []
    if name == "gauge-conversion":
        el = page.query_selector("#measurement")
        el.fill("-5")
        page.query_selector("#run-calc").click()
        time.sleep(1.0)
        cerr = page.query_selector("#calc-error")
        if cerr is None or (cerr.get_attribute("style") or "").find("display: block") == -1:
            fails.append("gauge-conversion: invalid measurement produced no visible error")
        el.fill("42")
        page.evaluate("document.querySelector('#measurement').blur()")
        # chart: invalid pattern
        sel = page.query_selector("#pattern-input")
        sel.fill("not a valid pattern xyz")
        page.query_selector("#run-chart").click()
        time.sleep(1.0)
        ch = page.query_selector("#chart-error")
        if ch is None or (ch.get_attribute("style") or "").find("display: block") == -1:
            fails.append("gauge-conversion: invalid pattern produced no visible error")
        sel.fill("k2 yo k2tog yo k1\np1 k2 yo k2tog p2")
        page.query_selector("#run-chart").click()
        return fails

    bid = spec["buttons"][0]
    eid = spec["errors"][0]

    def error_visible():
        err = page.query_selector(f"#{eid}")
        if err is None:
            return False
        # true visibility = computed display (hidden errors keep stale text)
        disp = page.evaluate(
            "el => getComputedStyle(el).display", err
        )
        return disp == "block"

    # textarea-first demos: a non-parseable pattern must raise
    ta = page.query_selector("section.card textarea")
    if ta is not None:
        original = ta.input_value()
        ta.fill("this is not a valid knitting pattern zzz qqq")
        page.query_selector(f"#{bid}").click()
        time.sleep(1.2)
        if not error_visible():
            fails.append(f"invalid (garbage) pattern produced no visible error in #{eid}")
        ta.fill(original)
        return fails

    # numeric demos: zero each numeric input until an error appears
    inputs = page.query_selector_all("section.card input[type=number]")
    if not inputs:
        return []
    triggered = False
    for el in inputs:
        original = el.input_value()
        try:
            float(original)
        except ValueError:
            continue
        el.fill("0")
        page.query_selector(f"#{bid}").click()
        time.sleep(1.2)
        if error_visible():
            triggered = True
            el.fill(original or "5")
            break
        el.fill(original)
    if not triggered:
        fails.append(f"no numeric input (zeroed) produced a visible error in #{eid}")
        return fails

    # recover: valid click again works
    page.query_selector(f"#{bid}").click()
    time.sleep(1.2)
    out_html = (page.eval_on_selector(f"#{spec['outputs'][0]}", "el => el.innerHTML") or "").strip()
    if not out_html or error_visible():
        fails.append("demo did not recover after restoring valid input")
    return fails


def check_index(browser):
    """Verify index.html loads and every demo link resolves to a page."""
    page = browser.new_page()
    problems = []
    try:
        resp = page.goto(f"{BASE}/demos/index.html", wait_until="domcontentloaded", timeout=30000)
        if resp is None or resp.status != 200:
            problems.append(f"index.html status {resp.status if resp else 'None'}")
            page.close()
            return problems
        links = page.eval_on_selector_all(
            "a[href$='.html']", "els => els.map(e => e.getAttribute('href'))"
        )
        for href in links:
            full = href if href.startswith("http") else f"{BASE}/demos/{href.lstrip('/')}"
            try:
                r = page.request.get(full)
                if r.status != 200:
                    problems.append(f"{href} -> {r.status}")
            except Exception as exc:
                problems.append(f"{href} -> {str(exc)[:80]}")
    except Exception as exc:
        problems.append("index.html navigation failed: " + str(exc)[:120])
    page.close()
    return problems


def main():
    use_headless = "--headed" not in sys.argv
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=use_headless, slow_mo=60 if not use_headless else 0)
        all_reports = []
        for spec in DEMOS:
            report = run_demo(browser, spec)
            all_reports.append(report)

        browser.close()

    print("\n" + "=" * 70)
    print("QA SUMMARY")
    print("=" * 70)
    passed_all = True
    # index check
    with sync_playwright() as p2:
        b2 = p2.chromium.launch(headless=True)
        idx_problems = check_index(b2)
        b2.close()
    if idx_problems:
        passed_all = False
        print("\n[index.html] PROBLEMS")
        for p_ in idx_problems:
            print("     FAIL: " + p_)
    else:
        print("\n[index.html] PASS  (all demo links resolve)")
    for r in all_reports:
        status = "PASS" if r.passed else "FAIL"
        if not r.passed:
            passed_all = False
        print(f"\n[{status}] {r.name}  (loaded in {r.load_ms} ms)")
        for n in r.notes:
            print("     note: " + n)
        for f in r.failures:
            print("     FAIL: " + f)
        if r.console_errors:
            print("     boot console errors: %d" % len(r.console_errors))
            for c in r.console_errors[:5]:
                print("        - " + c)
            passed_all = False
        if r.page_errors:
            print("     page errors (%d):" % len(r.page_errors))
            for pe in r.page_errors[:5]:
                print("        - " + pe)
            passed_all = False
        if r.interaction_console:
            print("     interaction console messages (expected tracebacks): %d" % len(r.interaction_console))
            for c in r.interaction_console[:3]:
                print("        - " + c[:160])
        if r.failed_requests:
            print("     failed requests (%d):" % len(r.failed_requests))
            for fr in r.failed_requests[:8]:
                print("        - " + fr)
            passed_all = False
    print("\n" + "=" * 70)
    print("ALL PASS" if passed_all else "SOME DEMOS FAILED")
    print("=" * 70)
    sys.exit(0 if passed_all else 1)


if __name__ == "__main__":
    main()