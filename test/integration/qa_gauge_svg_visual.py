"""Focused browser QA for gauge-conversion SVG visual quality.

Checks real rendered output, not just presence of an SVG string:
- chart output includes an inline SVG
- stitch labels are concise symbols (not verbose names)
- symbols are visually distinct (multiple glyphs + multiple colors)
- inline SVG CSS is syntactically valid for browser parsing
"""

import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8000"
URL = f"{BASE}/gauge-conversion/demo.html"


def main() -> int:
    failures = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1400, "height": 1100})

        try:
            page.goto(URL, wait_until="domcontentloaded", timeout=120_000)
        except Exception as exc:
            print("FAIL  navigation failed", str(exc)[:200])
            browser.close()
            return 1

        # Wait for pyScript init and default run.
        for _ in range(300):
            banner = page.query_selector("#status-banner")
            if banner:
                cls = banner.get_attribute("class") or ""
                if "ready" in cls or "error" in cls:
                    break
            time.sleep(0.25)

        state = page.eval_on_selector("#status-banner", "el => el.className")
        if "ready" not in state:
            failures.append(f"status not ready: {state}")

        chart_html = page.eval_on_selector("#chart-output", "el => el.innerHTML") or ""
        if "<svg" not in chart_html:
            failures.append("chart-output does not contain <svg>")

        info = page.evaluate("""
() => {
  const svg = document.querySelector('#chart-output svg');
  if (!svg) return { missing: true };

  const labels = [...svg.querySelectorAll('text.stitch-label')];
  const labelTexts = labels
    .map(el => (el.textContent || '').trim())
    .filter(Boolean);
  const uniqueLabels = [...new Set(labelTexts)];
  const fills = [...new Set(labels.map(el => getComputedStyle(el).fill))];
    const hasVerboseLabels = labels.some(el => /\\s/.test((el.textContent || '').trim()));
  const styleText = svg.querySelector('style')?.textContent || '';

  return {
    missing: false,
    labelCount: labels.length,
    uniqueLabelCount: uniqueLabels.length,
    uniqueLabels,
    fillCount: fills.length,
    fills,
    hasVerboseLabels,
    hasDoubleBraceCss: styleText.includes('{{') || styleText.includes('}}'),
  };
}
            """)

        if info.get("missing"):
            failures.append("svg element missing in chart-output")
        else:
            if info.get("labelCount", 0) < 4:
                failures.append("expected at least 4 stitch labels")
            if info.get("uniqueLabelCount", 0) < 3:
                failures.append("expected at least 3 distinct stitch symbols")
            if info.get("hasVerboseLabels"):
                failures.append("labels contain verbose stitch names (expected concise symbols)")
            if info.get("fillCount", 0) < 2:
                failures.append("expected at least 2 distinct computed label colors")
            if info.get("hasDoubleBraceCss"):
                failures.append("inline svg css still contains invalid double braces")

        browser.close()

    if failures:
        for failure in failures:
            print("FAIL ", failure)
        return 1

    print("PASS  gauge-conversion SVG is visually distinct and CSS-valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
