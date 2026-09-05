"""Browser regression checks for chart-renderer lifecycle and symbol rendering.

Validates real DOM behavior:
- repeated renders replace output (exactly one chart SVG)
- switching default <-> japanese legend keeps one chart
- japanese render does not leak package filesystem paths
- rendered symbols are visible (text and/or embedded images)
"""

import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8000"
URL = f"{BASE}/chart-renderer/demo.html"


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


def _render(page):
    page.click("#run")
    time.sleep(0.8)


def _assert_one_chart(page, failures, context):
    count = page.eval_on_selector_all("#demo-output svg", "els => els.length")
    if count != 1:
        failures.append(f"{context}: expected exactly 1 SVG in demo-output, got {count}")


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
            for f in failures:
                print("FAIL ", f)
            return 1

        # Repeated default renders should replace, not append.
        _render(page)
        _assert_one_chart(page, failures, "default render #1")

        _render(page)
        _assert_one_chart(page, failures, "default render #2")

        # Switch to Japanese legend and render.
        page.select_option("#legend", "japanese")
        _render(page)
        _assert_one_chart(page, failures, "japanese render")

        html_jp = page.eval_on_selector("#demo-output", "el => el.innerHTML") or ""
        if "/site-packages/" in html_jp or "/lib/python" in html_jp:
            failures.append("japanese output leaked filesystem path in DOM")

        info = page.evaluate("""
() => {
  const out = document.querySelector('#demo-output');
  const svg = out?.querySelector('svg');
  if (!svg) {
    return { missing: true };
  }
  const textNodes = [...svg.querySelectorAll('text')]
    .map(n => (n.textContent || '').trim())
    .filter(Boolean);
  const imageNodes = svg.querySelectorAll('image').length;
  const visibleText = textNodes.filter(t => !t.includes('/site-packages/') && !t.includes('/lib/python'));
  return {
    missing: false,
    imageCount: imageNodes,
    textCount: textNodes.length,
    visibleTextCount: visibleText.length,
    uniqueVisibleText: [...new Set(visibleText)].slice(0, 12),
  };
}
            """)

        if info.get("missing"):
            failures.append("missing svg after japanese render")
        else:
            if info.get("imageCount", 0) == 0:
                failures.append("japanese render has no symbol images")

        # Switch back to default and verify still one chart.
        page.select_option("#legend", "default")
        _render(page)
        _assert_one_chart(page, failures, "default-after-japanese render")

        browser.close()

    if failures:
        for f in failures:
            print("FAIL ", f)
        return 1

    print("PASS  chart-renderer lifecycle and japanese symbol rendering")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
