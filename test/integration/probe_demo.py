"""Probe a new-style demo after the bind_click fix."""
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8877"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 1000})
    events = []
    page.on("console", lambda m: events.append(("[console " + m.type + "] " + m.text[:200])))
    page.on("pageerror", lambda e: events.append(("[pageerror] " + str(e)[:300])))

    page.goto(f"{BASE}/demos/chart-renderer/demo.html", wait_until="domcontentloaded")
    for _ in range(150):
        cls = page.eval_on_selector("#status-banner", "el => el.className")
        if "ready" in cls or "error" in cls:
            break
        time.sleep(0.5)

    print("banner:", page.eval_on_selector("#status-banner", "el => el.className"))
    print("message:", repr(page.eval_on_selector("#status-message", "el => el.textContent")))

    # Check python globals via pyodide
    info = page.evaluate("""
      () => {
        let out = {};
        try { out.hasDEMO = Object.keys(Object.fromEntries(Object.entries(pyodide.globals))).
                    includes('DEMO'); } catch(e) { out.demoErr = String(e); }
        return out;
      }
    """)
    print("pyodide globals DEMO present?", info)

    # click run and inspect output
    page.click("#run")
    time.sleep(2)
    html = page.eval_on_selector("#demo-output", "el => el.innerHTML") or ""
    print("demo-output len:", len(html), "head:", html[:120])
    print("demo-error display:", page.eval_on_selector("#demo-error", "el => el.style.display"))

    print("--- console/page events ---")
    for e in events:
        print(e)
    browser.close()