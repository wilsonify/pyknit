# pyKnit Android

Thin WebView wrapper around the existing pyKnit web application. The full app
(HTML/CSS/JS + PyScript + Pyodide + Python, all 14 demos) is bundled in the
APK and served from a local `https://` origin. No Chaquopy, no Python
rewrite, no network required.

## Architecture

- **Web app is the source of truth.** `demos/` runs unchanged inside the
  `WebView` through the bundled PyScript/Pyodide runtime. There is exactly
  one knitting implementation.
- **Offline assets.** `scripts/package_android_assets.py` stages `demos/` +
  the `build/` runtime (Pyodide 0.24.1, PyScript 2024.10.1, wheels) into
  `app/src/main/assets/dist/`, preserving the `demos/` layout so absolute
  `/_assets/` and `/_wheel/` URLs keep working. The Gradle `preBuild` hook
  runs this automatically; `scripts/audit_android_assets.py` gates
  completeness (every page + runtime file present, no remote fetches).
- **Kotlin owns only Android concerns** (`MainActivity.kt`): serving assets
  via `WebViewAssetLoader` on `https://appassets.androidplatform.net`
  (never `file://`), back navigation, pattern `.txt` exports, external
  links (opened in the browser), and diagnostics (console/JS/resource
  errors to logcat tag `PyknitWebView`).
- **Exports.** Demo "Export Pattern" buttons produce `data:text/plain`
  downloads. A page shim forwards the exact filename to native code, which
  saves to Documents (MediaStore on API 29+, app files below) and toasts
  the result. No storage permission is needed.

## Build

With Android SDK platform 34 and JDK 17 installed (see `build_app.bat` on
Windows for the exact environment):

```console
cd android
./gradlew assembleDebug
```

The APK is written to `app/build/outputs/apk/debug/app-debug.apk`
(~25–30 MB, dominated by the 24 MB offline runtime).

Asset staging needs Python 3 on `PATH` (`python3` by default; override with
`-PwebPython=...` or `$ANDROID_WEB_PYTHON`). The first staging downloads
the pinned runtime once (~23 MB); pass `--offline` via a manual script run
to fail fast instead of downloading. The SDK location comes from
`ANDROID_HOME` or `android/local.properties`.

## Test

```console
# Python unit tests (incl. Android wrapper architecture tests)
python -m pytest test/unit -q
# Demo math smoke test (the exact code the APK executes via Pyodide)
python scripts/demo_workflow_smoke.py
# Offline audit of the staged bundle
python scripts/audit_android_assets.py
```

On a device/emulator, launch with an extra to run the Pyodide boot smoke
page first (`adb shell am start -n org.pyknit.android/.MainActivity
--es start_url https://appassets.androidplatform.net/smoke/pyodide-smoke.html`),
then watch `adb logcat -s PyknitWebView`, and finally open the real landing
page (`/.../index.html`) with network disabled to confirm offline operation.
