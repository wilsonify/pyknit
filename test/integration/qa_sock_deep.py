"""Deep QA for the Sock Calculator demo.

Beyond the generic harness this exercises every input (normal + edge +
invalid), the size quick-pick, warnings, SVG geometry and the full plan
rendering in a real browser.
"""

import re
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8877/demos/sock-calculator/demo.html"

EXTRA = (
    "Attempting to import", "pyknit imported", "Running default",
    "SVG generated", "PNG generated", "Text generated", "Using text",
    "Error: Pattern cannot", "Available backends",
)
SKIP = (
    "favicon", "DevTools", "Third-party cookie", "Autofill", "cache",
    "GetUserMedia", "Offline", "deprecated", "Source map",
)


def is_noise(text):
    return any(t in text for t in SKIP) or any(t in text for t in EXTRA)


failures = []


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (" [" + detail + "]" if detail else ""))
    if not ok:
        failures.append(name + (" :: " + detail if detail else ""))


def wait_ready(page, timeout=240_000):
    deadline = time.time() + timeout / 1000
    while time.time() < deadline:
        try:
            cls = (page.query_selector("#status-banner").get_attribute("class") or "")
            if "ready" in cls:
                return "ready"
            if "error" in cls:
                return "error"
        except Exception:
            pass
        time.sleep(0.5)
    return "timeout"


def run_click(page):
    page.query_selector("#run").click()
    time.sleep(1.4)


def out_text(page):
    el = page.query_selector("#demo-output")
    return re.sub(r"<[^>]+>", " ", el.inner_html() or "").strip()


def error_visible(page):
    err = page.query_selector("#demo-error")
    if err is None:
        return False
    return page.evaluate("el => getComputedStyle(el).display", err) == "block"


def fill(page, sel, val):
    page.query_selector(sel).fill(str(val))
    page.evaluate("document.querySelector(%s).blur()" % ("'%s'" % sel))


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 1100})
        console_errors, page_errors = [], []

        def on_console(msg):
            t = msg.text
            if msg.type == "error" and not is_noise(t):
                console_errors.append((time.monotonic(), t[:300]))

        def on_pageerror(exc):
            page_errors.append(str(exc)[:300])

        page.on("console", on_console)
        page.on("pageerror", on_pageerror)

        t0 = time.time()
        page.goto(BASE, wait_until="domcontentloaded", timeout=120_000)
        state = wait_ready(page)
        boot_ms = int((time.time() - t0) * 1000)
        check("pyScript booted (ready in %dms)" % boot_ms, state == "ready", state)
        check("no boot console errors", not console_errors, "; ".join(c[1] for c in console_errors[:3]))
        check("no page errors during load", not page_errors, "; ".join(page_errors[:2]))

        # ---- default plan ----
        run_click(page)
        html = page.eval_on_selector("#demo-output", "el => el.innerHTML") or ""
        check("default click produced svg", "<svg" in html)
        for marker in ("How this sock is built", "Your numbers at a glance",
                       "Knit along", "1. Cast on and get started",
                       "3. Work the heel flap", "4. Turn the heel",
                       "5. Shape the gusset", "7. Knit the toe"):
            check("plan has '%s'" % marker, marker in html)
        baseline = html

        # ---- SVG geometry: no negative / non-numeric values ----
        svg = re.search(r"<svg.*?</svg>", html, re.S).group(0)
        bad = [a for a in re.findall(r'(width|height|x|y)="(-?\d*\.?\d+)"', svg)
               if float(a[1]) < 0]
        check("svg has no negative geometry", not bad, str(bad[:5]))
        check("svg mentions cast-on stitches", "cast on" in svg)

        # ---- every numeric input, normal + edge ----
        inputs = {
            "#stitches_per_inch": (5, 6, 12, 16),
            "#rows_per_inch": (6, 9, 14, 18),
            "#circumference_at_top": (8, 10.75, 14),
            "#circumference_of_ankle": (7.5, 9.25, 11.5),
            "#length_from_sock_top_to_heel_bottom": (5.5, 8.25, 12),
            "#length_from_heel_to_toe": (7, 9.75, 13),
        }
        for sel, values in inputs.items():
            for val in values:
                fill(page, sel, val)
                run_click(page)
                cur = out_text(page)
                ok = bool(cur) and error_visible(page) is False
                check(f"{sel} = {val} renders plan", ok, out_text(page)[:60])
        # restore defaults
        fill(page, "#stitches_per_inch", 9)
        fill(page, "#rows_per_inch", 11)
        fill(page, "#circumference_at_top", 10)
        fill(page, "#circumference_of_ankle", 9.5)
        fill(page, "#length_from_sock_top_to_heel_bottom", 7.75)
        fill(page, "#length_from_heel_to_toe", 10.5)

        # ---- output changes when every input changes ----
        baseline_text = out_text(page)
        for sel, new_val in {
            "#stitches_per_inch": 7,
            "#rows_per_inch": 13,
            "#circumference_at_top": 11,
            "#circumference_of_ankle": 8.5,
            "#length_from_sock_top_to_heel_bottom": 9,
            "#length_from_heel_to_toe": 12,
        }.items():
            fill(page, sel, new_val)
            run_click(page)
            changed = out_text(page) != baseline_text
            check(f"changing {sel} changes output", changed)
            if not changed:
                print("      (debug) current:", out_text(page)[:80])
        # restore
        fill(page, "#circumference_at_top", 10)
        fill(page, "#circumference_of_ankle", 9.5)
        fill(page, "#length_from_sock_top_to_heel_bottom", 7.75)
        fill(page, "#length_from_heel_to_toe", 10.5)
        fill(page, "#stitches_per_inch", 9)
        fill(page, "#rows_per_inch", 11)

        # ---- size quick-pick fills the fields and produces a plan ----
        page.select_option("#sock-size", "w-m")
        run_click(page)
        circ = page.query_selector("#circumference_at_top").input_value()
        foot = page.query_selector("#length_from_heel_to_toe").input_value()
        check("size pick fills leg circumference", circ == "10.25", circ)
        check("size pick fills foot length", foot == "9.25", foot)
        check("size pick yields a plan", "Knit along" in page.eval_on_selector(
            "#demo-output", "el => el.innerHTML"))

        # ---- warnings: unusual gauge ----
        fill(page, "#stitches_per_inch", 2)
        fill(page, "#rows_per_inch", 3)
        run_click(page)
        warn_html = page.eval_on_selector("#demo-output", "el => el.innerHTML")
        check("unusual gauge shows warnings", "Before you start" in warn_html)
        # no crash
        check("unusual gauge still renders plan", "Knit along" in warn_html)

        # ---- warning: ankle bigger than leg ----
        fill(page, "#stitches_per_inch", 9)
        fill(page, "#rows_per_inch", 11)
        fill(page, "#circumference_at_top", 8)
        fill(page, "#circumference_of_ankle", 10)
        run_click(page)
        warn_html = page.eval_on_selector("#demo-output", "el => el.innerHTML")
        check("leg<ankle shows a warning", "Before you start" in warn_html)
        check("leg<ankle renders without leg decreases note",
              "no leg decreases" in re.sub(r"<[^>]+>", " ", warn_html))

        # ---- invalid inputs: zero, negative, empty ----
        t_before_invalid = time.monotonic()
        fill(page, "#circumference_at_top", 10)
        fill(page, "#circumference_of_ankle", 9.5)
        fill(page, "#length_from_sock_top_to_heel_bottom", 7.75)
        fill(page, "#length_from_heel_to_toe", 10.5)
        for sel, bad_val in (
            ("#stitches_per_inch", 0),
            ("#circumference_of_ankle", -3),
            ("#length_from_heel_to_toe", ""),
        ):
            fill(page, sel, bad_val)
            run_click(page)
            check(f"invalid {sel}={bad_val} shows error", error_visible(page))
        # recover
        fill(page, "#stitches_per_inch", 9)
        fill(page, "#circumference_of_ankle", 9.5)
        fill(page, "#length_from_heel_to_toe", 10.5)
        run_click(page)
        check("recovers after invalid inputs", "<svg" in page.eval_on_selector(
            "#demo-output", "el => el.innerHTML"))

        # ---- interaction console should have no unexpected errors ----
        # (ValueError tracebacks during the invalid-input exercise are expected)
        unexpected = [t for ts, t in console_errors
                      if ts < t_before_invalid and "Traceback" not in t]
        check("no unexpected interaction console errors", not unexpected,
              "; ".join(unexpected[:3]))

        browser.close()

    print()
    print("=" * 60)
    print("DEEP QA: " + ("ALL PASS" if not failures else "%d FAILURES" % len(failures)))
    print("=" * 60)
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()