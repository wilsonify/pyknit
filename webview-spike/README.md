# pyKnit WebView spike (investigation prototype, not production)

This directory is a **thin Android shell** prototype for the architecture
spike: host the existing `demos/` PyScript/Pyodide application inside an
Android `WebView` with **no Chaquopy** and **no Python rewrite**.

## What it is

- `app/src/main/kotlin/.../PyknitWebViewActivity.kt` — minimal `WebView`
  wrapper: enables JS/WASM/DOM-storage, serves bundled assets over
  `https://appassets.androidplatform.net` via `WebViewAssetLoader`
  (same-origin, correct MIME incl. `application/wasm`), captures
  console errors / JS exceptions / failed resources, exposes a
  `pyodideReady` signal so tests can tell when Pyodide initialized.
- `smoke/pyodide-smoke.html` — tiny boot test: loads the *real bundled*
  `pyodide.mjs` + stdlib and runs `1+1`. Run this first to isolate
  WebView↔Pyodide compatibility before loading the full app.
- `scripts/package-assets.ps1` — copies the already-built offline runtime
  (`build/pyodide`, `build/pyscript`, `build/wheels`, `build/wheel`,
  `demos/*.html`, `demos/_assets/common.css`, demo JS) into
  `app/src/main/assets/dist/`, rewrites absolute `/_assets/` and
  `/_wheel/` paths to relative ones so the app works under the
  asset-loader origin without a network server.
- This spike deliberately does **not** touch `android/` (Chaquopy app).

## How to build (Windows, Android SDK 34, JDK 17)

```powershell
# 1. Build the offline web runtime (downloads Pyodide/PyScript once, ~23 MB)
python -m pip wheel . -w build/wheel --no-deps
# or: make runtime-cache  (requires curl; Git Bash/WSL easiest)

# 2. Stage web assets into the prototype APK
powershell -ExecutionPolicy Bypass -File webview-spike/scripts/package-assets.ps1

# 3. Build the wrapper APK (copy gradle wrapper from android/ or use studio)
Copy-Item android/gradlew* webview-spike/ -Force
Copy-Item android/gradle webview-spike/gradle -Recurse -Force
Copy-Item android/gradle.properties webview-spike/ -Force
cd webview-spike; ./gradlew assembleDebug
# APK: webview-spike/app/build/outputs/apk/debug/app-debug.apk
```

## How to test on device/emulator

1. Install APK, launch — smoke page loads first (`?smoke=1`).
   `adb logcat | Select-String "PyknitWebView"` shows console/errors.
2. `evaluateJavascript("window.__pyknitSmoke")` should return
   `{"ok":true,"result":2}` once Pyodide is ready.
3. Navigate to `/dist/index.html` (landing) then each demo; the wrapper
   logs `console.error`, uncaught exceptions, and HTTP failures
   (status >= 400, incl. `.wasm`/`.whl` MIME problems).
4. Airplane-mode test: all pages must boot with network disabled —
   anything fetched from `http(s)://` outside the asset-loader origin
   is an offline-packaging bug.

## Status (2026-09-04 spike)

- Static audit + offline-packaging check: DONE (see repo root spike
  report). All app code paths are local; no CDN at runtime.
- Wrapper source + smoke page + packaging script: DONE (this folder).
- Desktop Python workflow tests (`test/unit`, 685 passed): DONE.
- On-device WebView render test: NOT RUN here (no AVD in this
  environment) — the wrapper's logcat hooks + smoke page are provided
  so it can be run on any emulator/device in minutes.
