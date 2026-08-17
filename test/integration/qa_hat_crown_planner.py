"""Browser regression checks for hat-crown planner clarity and validation."""

import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8000"
URL = f"{BASE}/hat-crown/demo.html"


def _wait_ready(page, timeout_s=90):
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        banner = page.query_selector("#status-banner")
        if banner:
            cls = banner.get_attribute("class") or ""
            if "ready" in cls or "error" in cls:
                return cls
        time.sleep(0.2)
    return "timeout"


def _is_visible(page, selector):
    return page.eval_on_selector(
        selector,
        "el => { const s = getComputedStyle(el); return s.display !== 'none' && el.offsetParent !== null; }",
    )


def main() -> int:
    failures = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1400, "height": 1000})

        page.goto(URL, wait_until="domcontentloaded", timeout=120_000)
        state = _wait_ready(page)
        if "ready" not in state:
            failures.append(f"status not ready: {state}")
            browser.close()
            for failure in failures:
                print("FAIL ", failure)
            return 1

        page.click("#run")
        time.sleep(1.0)

        info = page.evaluate(
            """
() => {
  const out = document.querySelector('#demo-output');
  const firstTransition = out?.querySelector('table.hat-rounds tbody tr td:nth-child(3)')?.textContent?.trim() || '';
  const hasStrategy = (out?.textContent || '').includes('Crown shaping strategy');
  const hasFormula = (out?.textContent || '').includes('Formula:');
  const svgCount = out?.querySelectorAll('svg').length || 0;
  const rowCount = out?.querySelectorAll('table.hat-rounds tbody tr').length || 0;
  return {firstTransition, hasStrategy, hasFormula, svgCount, rowCount};
}
            """
        )

        if info.get("svgCount", 0) != 1:
            failures.append(f"expected 1 crown svg, got {info.get('svgCount')}")
        if info.get("rowCount", 0) < 3:
            failures.append("round-by-round table has too few rows")
        if "80" not in info.get("firstTransition", "") or "72" not in info.get("firstTransition", ""):
            failures.append(f"unexpected first stitch transition: {info.get('firstTransition')}")
        if not info.get("hasStrategy"):
            failures.append("missing crown strategy section")
        if not info.get("hasFormula"):
            failures.append("missing explicit decrease formula")

        page.fill("#stitches", "78")
        page.fill("#repeats", "8")
        page.click("#run")
        time.sleep(0.7)

        try:
            err_visible = _is_visible(page, "#demo-error")
        except Exception:
            err_visible = False

        err_text = page.eval_on_selector("#demo-error", "el => (el.textContent || '').trim()") or ""
        if not err_visible:
            failures.append("error message not visible for invalid divisible input")
        if "divide evenly" not in err_text:
            failures.append(f"unexpected invalid-input error text: {err_text}")

        browser.close()

    if failures:
        for failure in failures:
            print("FAIL ", failure)
        return 1

    print("PASS  hat-crown planner explicit math, transitions, and validation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
