"""Tests for the Android WebView wrapper around the canonical pyKnit demos.

The Android app is a thin WebView shell: it serves the existing ``demos/``
PyScript/Pyodide application from bundled offline assets and owns only
Android concerns (asset serving, back navigation, exports, external links,
diagnostics). There must be no second Python engine and no duplicated
native UI.
"""

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import package_android_assets as packager

ANDROID = ROOT / "android"
BUILD = ANDROID / "app" / "build.gradle.kts"
ACTIVITY = ANDROID / "app" / "src" / "main" / "kotlin" / "org" / "pyknit" / "android" / "MainActivity.kt"
MANIFEST = ANDROID / "app" / "src" / "main" / "AndroidManifest.xml"


def test_no_chaquopy_in_android_build():
    assert "com.chaquo.python" not in BUILD.read_text()
    assert "chaquopy" not in BUILD.read_text().lower()
    assert not (ROOT / "pyknit" / "chaquopy").exists()
    assert not (ANDROID / "requirements-android.txt").exists()


def test_activity_is_a_thin_webview_wrapper():
    activity = ACTIVITY.read_text()
    assert "android.webkit.WebView" in activity
    assert "WebViewAssetLoader" in activity
    assert "appassets.androidplatform.net" in activity
    assert "allowFileAccess = false" in activity
    assert "Python.getInstance" not in activity
    assert "com.chaquo" not in activity
    assert "mobile_api" not in activity


def test_no_duplicated_native_ui():
    ui_dir = ACTIVITY.parent / "ui"
    assert not ui_dir.exists(), f"native UI reimplementation still present: {ui_dir}"
    kotlin_files = list(ACTIVITY.parent.rglob("*.kt"))
    assert [p.name for p in kotlin_files] == ["MainActivity.kt"]


def test_wrapper_covers_back_nav_downloads_external_links_and_diagnostics():
    activity = ACTIVITY.read_text()
    assert "canGoBack" in activity  # back navigation
    assert "DownloadListener" in activity or "__pyknitExport" in activity  # exports
    assert "ACTION_VIEW" in activity  # external links
    assert "onConsoleMessage" in activity  # diagnostics
    assert "onReceivedError" in activity


def test_packaging_covers_every_demo_page():
    assert set(packager.tool_pages(ROOT)) == {
        "chart-renderer",
        "even-shaping",
        "gauge-conversion",
        "hat-crown",
        "knit-simulator",
        "needle-advisor",
        "pattern-io",
        "pi-shawl",
        "raglan-sweater",
        "shawl-shapes",
        "sleeve-decreases",
        "sock-calculator",
        "yarn-advisor",
        "yarn-estimator",
    }


def test_packaging_pins_the_offline_runtime():
    assert "0.24.1" in packager.PYODIDE_URL
    assert "2024.10.1" in packager.PYSCRIPT_URL
    assert any(name.endswith(".wasm") for name in packager.PYODIDE_FILES)
    assert any("Pillow" in name for name in packager.WHEEL_FILES)


def test_manifest_keeps_single_launcher_activity():
    manifest = MANIFEST.read_text()
    assert manifest.count("android.intent.action.MAIN") == 1
    assert ".MainActivity" in manifest
