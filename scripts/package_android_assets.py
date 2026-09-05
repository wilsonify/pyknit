#!/usr/bin/env python3
"""Stage the pyKnit web app + offline PyScript/Pyodide runtime into the APK.

Copies the existing ``demos/`` application and the offline runtime from
``build/`` into ``android/app/src/main/assets/dist/``, preserving the
``demos/`` layout (absolute ``/_assets/`` and ``/_wheel/`` URLs keep working
because the Android wrapper serves ``dist/`` from the site root of its
local ``https://appassets.androidplatform.net`` origin — no HTML rewriting).

File lists mirror the ``runtime-cache`` target in the Makefile
(Pyodide 0.24.1, PyScript 2024.10.1)::

    python scripts/package_android_assets.py [--root .] [--offline]

``--offline`` fails fast instead of downloading a missing runtime; without it
missing pieces are fetched from the same CDN URLs the Makefile uses and the
pyknit wheel is rebuilt locally when stale.
"""

from __future__ import annotations

import argparse
import pathlib
import shutil
import subprocess
import sys
import urllib.request

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

PYODIDE_URL = "https://cdn.jsdelivr.net/pyodide/v0.24.1/full"
PYSCRIPT_URL = "https://pyscript.net/releases/2024.10.1"

PYODIDE_FILES = [
    "pyodide.mjs",
    "pyodide.asm.js",
    "pyodide.asm.wasm",
    "pyodide-lock.json",
    "python_stdlib.zip",
    "micropip-0.5.0-py3-none-any.whl",
    "packaging-23.1-py3-none-any.whl",
]
WHEEL_FILES = [
    "typing_extensions-4.7.1-py3-none-any.whl",
    "pydantic-1.10.7-py3-none-any.whl",
    "Pillow-10.0.0-cp311-cp311-emscripten_3_1_45_wasm32.whl",
]
PYSCRIPT_FILES = [
    "core.css",
    "core.js",
    "core.js.map",
    "core-DHft4mQJ.js",
    "core-DHft4mQJ.js.map",
    "toml-CvAfdf9_.js",
    "toml-DiUM0_qs.js",
    "zip-Bf48tRr5.js",
    "deprecations-manager-BDRw2fed.js",
    "donkey-c355Wa24.js",
    "error-CdZsd8BO.js",
    "py-editor-BRZBRs2T.js",
    "py-terminal-D_z3jMz-.js",
]


def repo_root(explicit: str | None) -> pathlib.Path:
    if explicit:
        return pathlib.Path(explicit).resolve()
    return pathlib.Path(__file__).resolve().parents[1]


def tool_pages(root: pathlib.Path) -> list[str]:
    """Names of demos/<tool>/ directories containing a demo.html page."""
    demos = root / "demos"
    return sorted(p.name for p in demos.iterdir() if p.is_dir() and (p / "demo.html").is_file())


# urllib's default UA is rejected (403) by some CDNs/proxies; identify the
# fetch as this project's offline-packaging step instead.
USER_AGENT = "pyknit-android-packaging/1.0 (+https://github.com/pyknit)"


def _download(url: str, dest: pathlib.Path, attempts: int = 3) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(request, timeout=120) as resp, open(dest, "wb") as out:
                shutil.copyfileobj(resp, out)
            return
        except Exception as exc:  # noqa: BLE001 - retry transient failures, report the last
            last_error = exc
            print(f"  download attempt {attempt}/{attempts} failed for {url}: {exc}")
            if dest.exists():
                dest.unlink()
    raise SystemExit(f"failed to download {url}: {last_error}")


def project_version(root: pathlib.Path) -> str:
    with open(root / "pyproject.toml", "rb") as fh:
        return tomllib.load(fh)["project"]["version"]


def ensure_runtime(root: pathlib.Path, offline: bool) -> None:
    """Make sure build/{pyodide,pyscript,wheels,wheel} is complete."""
    build = root / "build"
    missing = [
        name
        for subdir, names, base in (
            ("pyodide", PYODIDE_FILES, PYODIDE_URL),
            ("wheels", WHEEL_FILES, PYODIDE_URL),
            ("pyscript", PYSCRIPT_FILES, PYSCRIPT_URL),
        )
        for name in names
        if not (build / subdir / name).is_file()
    ]
    wheel_dir = build / "wheel"
    expected_wheel = wheel_dir / f"pyknit-{project_version(root)}-py3-none-any.whl"
    if not expected_wheel.is_file():
        # A stale wheel (old version) is worse than none: drop it so the
        # rebuild below produces exactly the current version.
        for stale in wheel_dir.glob("pyknit-*.whl"):
            stale.unlink()
        missing.append(f"wheel/pyknit-{project_version(root)}-py3-none-any.whl")
    if not missing:
        return
    if offline:
        raise SystemExit(f"missing runtime files (re-run without --offline): {missing[:5]}...")
    print(f"fetching {len(missing)} missing runtime files...")
    for subdir, names, base in (
        ("pyodide", PYODIDE_FILES, PYODIDE_URL),
        ("wheels", WHEEL_FILES, PYODIDE_URL),
        ("pyscript", PYSCRIPT_FILES, PYSCRIPT_URL),
    ):
        for name in names:
            dest = build / subdir / name
            if not dest.is_file():
                _download(f"{base}/{name}", dest)
    if not expected_wheel.is_file():
        print("building pyknit wheel...")
        wheel_dir.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [sys.executable, "-m", "pip", "wheel", ".", "-w", str(wheel_dir), "--no-deps"],
            cwd=root,
            check=True,
        )
        if not expected_wheel.is_file():
            got = [p.name for p in wheel_dir.glob("*.whl")]
            raise SystemExit(f"wheel build produced {got}, expected {expected_wheel.name}")


def stage(root: pathlib.Path) -> pathlib.Path:
    """Copy web app + runtime into android/app/src/main/assets/dist/."""
    demos = root / "demos"
    build = root / "build"
    dist = root / "android" / "app" / "src" / "main" / "assets" / "dist"
    if dist.exists():
        shutil.rmtree(dist)

    def copy(src: pathlib.Path, rel: str) -> None:
        dest = dist / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)

    copy(demos / "index.html", "index.html")
    if (demos / "favicon.ico").is_file():
        copy(demos / "favicon.ico", "favicon.ico")
    for tool in tool_pages(root):
        copy(demos / tool / "demo.html", f"{tool}/demo.html")
        for js in (demos / tool).glob("*.js"):
            copy(js, f"{tool}/{js.name}")
    for js in (demos / "_shared").glob("*.js"):
        copy(js, f"_shared/{js.name}")
    copy(demos / "_assets" / "common.css", "_assets/common.css")
    # Bootstrap loaded by gauge-conversion/demo.html via
    # <script type="py" src="/_assets/gauge-conversion.py">. Recreate it exactly
    # like the Makefile demo-assets target when it is missing.
    bootstrap = demos / "_assets" / "gauge-conversion.py"
    if not bootstrap.is_file():
        bootstrap.write_text(
            '"""Gauge conversion demo bootstrap (recreated by make demo-assets)."""\n'
            "from pyknit.pyscript._demos import gauge_conversion_page  # noqa: F401  # auto-bootstraps\n"
        )
    copy(bootstrap, "_assets/gauge-conversion.py")
    for name in PYSCRIPT_FILES:
        copy(build / "pyscript" / name, f"_assets/pyscript/{name}")
    for name in PYODIDE_FILES:
        copy(build / "pyodide" / name, f"_assets/pyodide/{name}")
    for name in WHEEL_FILES:
        copy(build / "wheels" / name, f"_assets/wheels/{name}")
    for whl in (build / "wheel").glob("pyknit-*.whl"):
        copy(whl, f"_wheel/{whl.name}")
    smoke = root / "android" / "smoke" / "pyodide-smoke.html"
    copy(smoke, "smoke/pyodide-smoke.html")
    return dist


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage offline web assets for the Android APK.")
    parser.add_argument("--root", default=None, help="repository root (default: parent of scripts/)")
    parser.add_argument("--offline", action="store_true", help="fail if the runtime must be downloaded")
    args = parser.parse_args()

    root = repo_root(args.root)
    ensure_runtime(root, offline=args.offline)
    dist = stage(root)
    files = [p for p in dist.rglob("*") if p.is_file()]
    size_mb = sum(p.stat().st_size for p in files) / 1e6
    print(f"staged {len(files)} files, {size_mb:.1f} MB -> {dist}")


if __name__ == "__main__":
    main()
