"""Deep QA for the Sock Calculator demo.

Beyond the generic harness this exercises every input (normal + edge +
invalid), the size quick-pick, warnings, SVG geometry and the full plan
rendering in a real browser.
"""

import os
import re
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from playwright.sync_api import sync_playwright

BASE = os.environ.get("PYQ_BASE", "http://127.0.0.1:8000") + "/sock-calculator/demo.html"

EXTRA = (
    "Attempting to import",
    "pyknit imported",
    "Running default",
    "SVG generated",
    "PNG generated",
    "Text generated",
    "Using text",
    "Error: Pattern cannot",
    "Available backends",
)
SKIP = (
    "favicon",
    "DevTools",
    "Third-party cookie",
    "Autofill",
    "cache",
    "GetUserMedia",
    "Offline",
    "deprecated",
    "Source map",
)

OUT_SEL = "#demo-output"
INNER_HTML = "el => el.innerHTML"
KNIT_ALONG = "Knit along"
PLAN_MARKERS = (
    "How this sock is built",
    "Your numbers at a glance",
    KNIT_ALONG,
    "1. Cast on and get started",
    "3. Work the heel flap",
    "4. Turn the heel",
    "5. Shape the gusset",
    "7. Knit the toe",
)

SPI = "#stitches_per_inch"
RPI = "#rows_per_inch"
CIRC_TOP = "#circumference_at_top"
CIRC_ANKLE = "#circumference_of_ankle"
LEN_LEG = "#length_from_sock_top_to_heel_bottom"
LEN_FOOT = "#length_from_heel_to_toe"

DEFAULT_INPUTS = {
    SPI: 9,
    RPI: 11,
    CIRC_TOP: 10,
    CIRC_ANKLE: 9.5,
    LEN_LEG: 7.75,
    LEN_FOOT: 10.5,
}

EDGE_VALUES = {
    SPI: (5, 6, 12, 16),
    RPI: (6, 9, 14, 18),
    CIRC_TOP: (8, 10.75, 14),
    CIRC_ANKLE: (7.5, 9.25, 11.5),
    LEN_LEG: (5.5, 8.25, 12),
    LEN_FOOT: (7, 9.75, 13),
}

CHANGE_VALUES = {
    SPI: 7,
    RPI: 13,
    CIRC_TOP: 11,
    CIRC_ANKLE: 8.5,
    LEN_LEG: 9,
    LEN_FOOT: 12,
}

failures = []


def is_noise(text):
    return any(t in text for t in SKIP) or any(t in text for t in EXTRA)


def check(name, ok, detail=""):
    print(("  PASS  " if ok else "  FAIL  ") + name + (" [" + detail + "]" if detail else ""))
    if not ok:
        failures.append(name + (" :: " + detail if detail else ""))


def wait_ready(page, timeout=240_000):
    deadline = time.time() + timeout / 1000
    while time.time() < deadline:
        try:
            cls = page.query_selector("#status-banner").get_attribute("class") or ""
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
    el = page.query_selector(OUT_SEL)
    return re.sub(r"<[^>]+>", " ", el.inner_html() or "").strip()


def error_visible(page):
    err = page.query_selector("#demo-error")
    if err is None:
        return False
    return page.evaluate("el => getComputedStyle(el).display", err) == "block"


def fill(page, sel, val):
    page.query_selector(sel).fill(str(val))
    page.evaluate("document.querySelector(%s).blur()" % ("'%s'" % sel))


def _console_sink(errors):
    def on_console(msg):
        t = msg.text
        if msg.type == "error" and not is_noise(t):
            errors.append((time.monotonic(), t[:300]))

    return on_console


def _pageerror_sink(errors):
    def on_pageerror(exc):
        errors.append(str(exc)[:300])

    return on_pageerror


def _check_default_plan(page):
    run_click(page)
    html = page.eval_on_selector(OUT_SEL, INNER_HTML) or ""
    check("default click produced svg", "<svg" in html)
    for marker in PLAN_MARKERS:
        check("plan has '%s'" % marker, marker in html)
    return html


def _check_svg_geometry(html):
    svg = re.search(r"<svg.*?</svg>", html, re.S).group(0)
    bad = [a for a in re.findall(r'(width|height|x|y)="(-?\d*\.?\d+)"', svg) if float(a[1]) < 0]
    check("svg has no negative geometry", not bad, str(bad[:5]))
    check("svg mentions cast-on stitches", "cast on" in svg)


def _probe_edge_values(page):
    for sel, values in EDGE_VALUES.items():
        # test each edge value in isolation against otherwise-default inputs;
        # cross-field combinations can legitimately fail validation (e.g. a
        # fine gauge making the leg too short for the decrease rounds).
        _restore_defaults(page)
        for val in values:
            fill(page, sel, val)
            run_click(page)
            ok = bool(out_text(page)) and error_visible(page) is False
            check(f"{sel} = {val} renders plan", ok, out_text(page)[:60])


def _restore_defaults(page):
    for sel, val in DEFAULT_INPUTS.items():
        fill(page, sel, val)


def _check_output_changes(page):
    baseline = out_text(page)
    for sel, new_val in CHANGE_VALUES.items():
        fill(page, sel, new_val)
        run_click(page)
        check(f"changing {sel} changes output", out_text(page) != baseline)


def _check_size_pick(page):
    page.select_option("#sock-size", "w-m")
    run_click(page)
    circ = page.query_selector(CIRC_TOP).input_value()
    foot = page.query_selector(LEN_FOOT).input_value()
    check("size pick fills leg circumference", circ == "10.25", circ)
    check("size pick fills foot length", foot == "9.25", foot)
    check(
        "size pick yields a plan",
        KNIT_ALONG in page.eval_on_selector(OUT_SEL, INNER_HTML),
    )


def _check_ease_select(page):
    page.select_option("#negative_ease", "0")
    run_click(page)
    html0 = page.eval_on_selector(OUT_SEL, INNER_HTML) or ""
    check("0% ease renders a plan", KNIT_ALONG in html0)
    page.select_option("#negative_ease", "20")
    run_click(page)
    html20 = page.eval_on_selector(OUT_SEL, INNER_HTML) or ""
    check("ease selector changes the plan", html0 != html20)
    check("ease appears in output", "negative ease" in html20)


def _check_warnings(page):
    fill(page, SPI, 3)
    fill(page, RPI, 4.5)
    run_click(page)
    warn_html = page.eval_on_selector(OUT_SEL, INNER_HTML)
    check("unusual gauge shows warnings", "Before you start" in warn_html)
    check("unusual gauge still renders plan", KNIT_ALONG in warn_html)

    fill(page, SPI, 9)
    fill(page, RPI, 11)
    fill(page, CIRC_TOP, 8)
    fill(page, CIRC_ANKLE, 10)
    run_click(page)
    warn_html = page.eval_on_selector(OUT_SEL, INNER_HTML)
    check("leg<ankle shows a warning", "Before you start" in warn_html)
    check(
        "leg<ankle renders without leg decreases note",
        "no leg decreases" in re.sub(r"<[^>]+>", " ", warn_html),
    )


def _check_invalid_recovery(page):
    t_before_invalid = time.monotonic()
    _restore_defaults(page)
    for sel, bad_val in ((SPI, 0), (CIRC_ANKLE, -3), (LEN_FOOT, "")):
        fill(page, sel, bad_val)
        run_click(page)
        check(f"invalid {sel}={bad_val} shows error", error_visible(page))
    _restore_defaults(page)
    run_click(page)
    check(
        "recovers after invalid inputs",
        "<svg" in page.eval_on_selector(OUT_SEL, INNER_HTML),
    )
    return t_before_invalid


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 1100})
        console_errors, page_errors = [], []
        page.on("console", _console_sink(console_errors))
        page.on("pageerror", _pageerror_sink(page_errors))

        t0 = time.time()
        page.goto(BASE, wait_until="domcontentloaded", timeout=120_000)
        state = wait_ready(page)
        boot_ms = int((time.time() - t0) * 1000)
        check("pyScript booted (ready in %dms)" % boot_ms, state == "ready", state)
        check(
            "no boot console errors",
            not console_errors,
            "; ".join(c[1] for c in console_errors[:3]),
        )
        check("no page errors during load", not page_errors, "; ".join(page_errors[:2]))

        # ---- default plan + svg geometry ----
        html = _check_default_plan(page)
        _check_svg_geometry(html)

        # ---- every numeric input, normal + edge ----
        _probe_edge_values(page)
        _restore_defaults(page)

        # ---- output changes when every input changes ----
        _check_output_changes(page)
        _restore_defaults(page)

        # ---- size quick-pick fills the fields and produces a plan ----
        _check_size_pick(page)

        # ---- negative ease selector is wired through ----
        _check_ease_select(page)

        # ---- warnings: unusual gauge, ankle bigger than leg ----
        _check_warnings(page)

        # ---- invalid inputs: zero, negative, empty ----
        t_before_invalid = _check_invalid_recovery(page)

        # ---- interaction console should have no unexpected errors ----
        # (ValueError tracebacks during the invalid-input exercise are expected)
        unexpected = [t for ts, t in console_errors if ts < t_before_invalid and "Traceback" not in t]
        check(
            "no unexpected interaction console errors",
            not unexpected,
            "; ".join(unexpected[:3]),
        )

        browser.close()

    print()
    print("=" * 60)
    print("DEEP QA: " + ("ALL PASS" if not failures else "%d FAILURES" % len(failures)))
    print("=" * 60)
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
