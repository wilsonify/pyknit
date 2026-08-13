"""Probe served test page: confirm binding approach."""
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8877"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    events = []
    page.on("console", lambda m: events.append(("[console " + m.type + "] " + m.text[:200])))
    page.on("pageerror", lambda e: events.append(("[pageerror] " + str(e)[:300])))

    page.goto(f"{BASE}/_qa-test.html", wait_until="domcontentloaded")
    time.sleep(8)

    page.click("#aw")
    time.sleep(1)
    t1 = page.eval_on_selector("#out", "el => el.textContent")
    page.click("#cp")
    time.sleep(1)
    t2 = page.eval_on_selector("#out", "el => el.textContent")

    print("after #aw click:", repr(t1))
    print("after #cp click:", repr(t2))
    print("--- events ---")
    for e in events:
        print(e)
    browser.close()