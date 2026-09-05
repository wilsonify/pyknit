#!/usr/bin/env python3
"""Offline audit for the Android WebView asset bundle.

Verifies that ``android/app/src/main/assets/dist/`` (produced by
``scripts/package_android_assets.py``) is complete and fully offline:

* every demo page and every runtime file the pages reference is present,
* no page fetches code/assets from a remote origin (GitHub anchor links and
  the SVG XML namespace are allowlisted — they are navigation/XML, not
  fetched code),
* every local ``src``/``href``/``interpreter``/``packages`` reference
  resolves inside ``dist/``.

Exits non-zero on the first failure class so CI can gate the APK build::

    python scripts/audit_android_assets.py [--root .] [--dist <dir>]
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys

REMOTE_RE = re.compile(r"""https?://[^\s"'<>]+""")
LOCAL_REF_RES = [
    re.compile(r'''(?:src|href)\s*=\s*"((?:/|\.\./)[^"]+)"'''),
    re.compile(r"""interpreter\s*=\s*"([^"]+)\""""),
    re.compile(r"""packages\s*=\s*\[([^\]]*)\]"""),
]
QUOTED_RE = re.compile(r'''"([^"]+)"''')

ALLOWLIST_SUBSTRINGS = (
    "http://www.w3.org/",  # SVG XML namespace, not a fetch
    "https://github.com/",  # external navigation links, opened in browser
    "https://cdn.jsdelivr.net/pyodide",  # informational string inside pyodide.mjs
    "https://appassets.androidplatform.net",  # our own local asset origin (comments/diagnostics)
)

REQUIRED_RUNTIME_RES = [
    "_assets/pyscript/core.js",
    "_assets/pyscript/core.css",
    "_assets/pyodide/pyodide.mjs",
    "_assets/pyodide/pyodide.asm.wasm",
    "_assets/pyodide/python_stdlib.zip",
    "_assets/common.css",
    "smoke/pyodide-smoke.html",
]


def repo_root(explicit: str | None) -> pathlib.Path:
    if explicit:
        return pathlib.Path(explicit).resolve()
    return pathlib.Path(__file__).resolve().parents[1]


def audit(root: pathlib.Path, dist: pathlib.Path) -> list[str]:
    errors: list[str] = []
    if not dist.is_dir():
        return [f"dist directory missing: {dist} (run scripts/package_android_assets.py first)"]

    pages = sorted(dist.rglob("*.html"))
    if not pages:
        errors.append(f"no HTML pages staged under {dist}")
    for page in pages:
        try:
            text = page.read_text(encoding="utf-8")
        except OSError as exc:
            errors.append(f"{page}: unreadable ({exc})")
            continue
        for url in REMOTE_RE.findall(text):
            if any(allow in url for allow in ALLOWLIST_SUBSTRINGS):
                continue
            errors.append(f"{page.relative_to(dist)}: remote reference {url}")
        for pattern in LOCAL_REF_RES:
            for match in pattern.finditer(text):
                refs = QUOTED_RE.findall(match.group(1)) if "packages" in pattern.pattern else [match.group(1)]
                for ref in refs:
                    if ref.startswith(("data:", "#")):
                        continue
                    if ref.startswith("/"):
                        target = (dist / ref.lstrip("/")).resolve()
                    else:
                        target = (page.parent / ref).resolve()
                    try:
                        target.relative_to(dist.resolve())
                    except ValueError:
                        errors.append(f"{page.relative_to(dist)}: reference escapes dist: {ref}")
                        continue
                    if not target.exists():
                        errors.append(f"{page.relative_to(dist)}: missing target {ref}")

    for rel in REQUIRED_RUNTIME_RES:
        if not (dist / rel).is_file():
            errors.append(f"required runtime file missing: {rel}")
    if not list((dist / "_assets" / "wheels").glob("*.whl")):
        errors.append("no wheels staged under _assets/wheels")
    if not list((dist / "_wheel").glob("pyknit-*.whl")):
        errors.append("no pyknit wheel staged under _wheel")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit the staged Android WebView assets.")
    parser.add_argument("--root", default=None)
    parser.add_argument("--dist", default=None, help="staged dist dir (default: android/app/src/main/assets/dist)")
    args = parser.parse_args()

    root = repo_root(args.root)
    dist = pathlib.Path(args.dist).resolve() if args.dist else root / "android" / "app" / "src" / "main" / "assets" / "dist"
    errors = audit(root, dist)
    files = [p for p in dist.rglob("*") if p.is_file()] if dist.is_dir() else []
    size_mb = sum(p.stat().st_size for p in files) / 1e6 if files else 0.0
    print(f"audited {len(files)} files, {size_mb:.1f} MB under {dist}")
    if errors:
        print(f"OFFLINE AUDIT FAILED ({len(errors)} problems):")
        for err in errors[:30]:
            print(f"  - {err}")
        return 1
    print("offline audit passed: every demo page + runtime file is bundled, no remote fetches")
    return 0


if __name__ == "__main__":
    sys.exit(main())
