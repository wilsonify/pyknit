import re
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

DEMOS = [
    "gauge-conversion",
    "chart-renderer",
    "even-shaping",
    "hat-crown",
    "pi-shawl",
    "pattern-io",
    "raglan-sweater",
    "shawl-shapes",
    "sleeve-decreases",
    "sock-calculator",
    "yarn-estimator",
]

REQUIRED_ASSETS = [
    "_assets/common.css",
    "_assets/gauge-conversion.py",
    "_assets/pyscript/core.js",
    "_assets/pyscript/core.css",
    "_assets/pyodide/pyodide.mjs",
    "_assets/pyodide/pyodide.asm.js",
    "_assets/pyodide/pyodide.asm.wasm",
    "_assets/pyodide/pyodide-lock.json",
    "_assets/pyodide/python_stdlib.zip",
    "_assets/pyodide/micropip-0.5.0-py3-none-any.whl",
    "_assets/pyodide/packaging-23.1-py3-none-any.whl",
    "_assets/wheels/Pillow-10.0.0-cp311-cp311-emscripten_3_1_45_wasm32.whl",
    "_assets/wheels/pydantic-1.10.7-py3-none-any.whl",
    "_assets/wheels/typing_extensions-4.7.1-py3-none-any.whl",
    "_wheel/pyknit-0.1.2-py3-none-any.whl",
]

OUTPUT_SELECTORS = {
    "gauge-conversion": ["#calc-output", "#chart-output"],
}


def _fetch(url):
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            return r.status, r.headers, r.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.headers, exc.read()


def _get(demo_url, path):
    return _fetch(demo_url + "/" + path)


def _wait_ready(page, timeout=120):
    deadline = time.time() + timeout
    while time.time() < deadline:
        banner = page.query_selector("#status-banner")
        if banner and "loading" not in (banner.get_attribute("class") or ""):
            return banner.get_attribute("class")
        page.wait_for_timeout(500)
    return page.query_selector("#status-banner").get_attribute("class")


def test_index_and_all_demo_pages_serve_200(demo_url):
    paths = ["index.html"] + [f"{d}/demo.html" for d in DEMOS]
    for path in paths:
        status, _, body = _get(demo_url, path)
        assert status == 200, path
        assert len(body) > 0, path


def test_runtime_assets_serve_200(demo_url):
    for asset in REQUIRED_ASSETS:
        status, _, body = _get(demo_url, asset)
        assert status == 200, asset
        assert len(body) > 0, asset


def test_wasm_and_mjs_served_with_javascript_compatible_types(demo_url):
    _, headers, _ = _get(demo_url, "_assets/pyodide/pyodide.asm.wasm")
    assert headers["Content-Type"].startswith("application/wasm")
    _, headers, _ = _get(demo_url, "_assets/pyodide/pyodide.mjs")
    assert headers["Content-Type"].startswith("text/javascript")


def test_wasm_served_gzip_encoded(demo_url):
    req = urllib.request.Request(
        demo_url + "/_assets/pyodide/pyodide.asm.wasm",
        headers={"Accept-Encoding": "gzip"},
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        assert r.headers.get("Content-Encoding") == "gzip"


def test_every_asset_referenced_by_pages_resolves(demo_url):
    pages = [REPO_ROOT / "demos" / "index.html"] + [
        REPO_ROOT / "demos" / d / "demo.html" for d in DEMOS
    ]
    refs = set()
    for page in pages:
        html = page.read_text(encoding="utf-8")
        for ref in re.findall(r'(?:src|href)="(/[^"]+)"', html):
            refs.add(ref)
    assert refs, "no local references found to check"
    for ref in sorted(refs):
        status, _, _ = _get(demo_url, ref.lstrip("/"))
        assert status == 200, f"referenced asset returned {status}: {ref}"


def test_missing_path_returns_404(demo_url):
    status, _, _ = _get(demo_url, "definitely-not-a-page.html")
    assert status == 404


@pytest.mark.parametrize("demo", DEMOS)
def test_demo_boots_and_computes_in_browser(demo_url, browser, demo):
    page = browser.new_page()
    failed_requests = []
    console_errors = []
    page.on(
        "response",
        lambda r: failed_requests.append((r.status, r.url))
        if r.status >= 400
        else None,
    )
    page.on(
        "console",
        lambda m: console_errors.append(m.text)
        if m.type == "error" and "Traceback" in m.text
        else None,
    )
    try:
        page.goto(f"{demo_url}/{demo}/demo.html", wait_until="domcontentloaded", timeout=30000)
        banner = _wait_ready(page)
        assert "ready" in banner, f"{demo} never reached ready (banner={banner})"
        page.wait_for_timeout(800)

        selectors = OUTPUT_SELECTORS.get(demo, ["#demo-output"])
        before = sum(
            page.evaluate(f"(document.querySelector('{s}')||{{innerHTML:''}}).innerHTML.length")
            for s in selectors
        )
        assert before > 0, f"{demo} rendered no output on load"

        btn = page.query_selector("button.btn-primary, #run, #run-calc")
        assert btn is not None, f"{demo} has no run button"
        btn.click()
        page.wait_for_timeout(2000)
        after = sum(
            page.evaluate(f"(document.querySelector('{s}')||{{innerHTML:''}}).innerHTML.length")
            for s in selectors
        )
        assert after > 0, f"{demo} produced no output after clicking run"
        assert before <= after, f"{demo} output shrank after clicking run"
    finally:
        page.close()

    bad = [f"{s} {u}" for s, u in failed_requests if s >= 400]
    assert not bad, f"{demo} had failed requests: {bad[:5]}"
    assert not console_errors, f"{demo} had python tracebacks: {console_errors[:3]}"


@pytest.mark.parametrize(
    "planner,expected_mode,status_contains",
    [
        ("raglan-sweater", "advanced", "stitches from planner"),
        ("hat-crown", "friendly", "project type from planner"),
    ],
)
def test_send_to_estimator_flow(demo_url, browser, planner, expected_mode, status_contains):
    """Send-to-Estimator must run the mode that uses the planner's data.

    A raglan workload is used by the advanced estimator, while a hat planner
    (which only knows cast-on stitches) falls back to the friendly estimator
    instead of reporting absurdly low yardage.
    """
    page = browser.new_page()
    try:
        page.goto(f"{demo_url}/{planner}/demo.html", wait_until="domcontentloaded", timeout=30000)
        _wait_ready(page)
        page.wait_for_timeout(500)
        send = page.query_selector(".send-to-estimator")
        assert send is not None, f"{planner} has no send-to-estimator button"
        send.click()
        page.wait_for_load_state("domcontentloaded", timeout=30000)
        _wait_ready(page)
        page.wait_for_timeout(1500)

        status = page.evaluate(
            "[...document.querySelectorAll('#status-message, #status-detail')].map(e => e.textContent)"
        )
        joined = " / ".join(status)
        assert status_contains in joined, f"unexpected status after {planner} prefill: {status}"

        out = page.evaluate(
            "(document.querySelector('#demo-output') || {textContent:''}).textContent"
        )
        assert out.strip(), f"{planner} flow produced blank estimator output"
        if expected_mode == "advanced":
            assert "yd/st" in out, "advanced estimate must use per-stitch yardage"
        else:
            assert "yd/st" not in out, "friendly estimate must not use per-stitch yardage"
    finally:
        page.close()