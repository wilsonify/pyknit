#!/usr/bin/env python3
"""Rewrite the PyScript demo site for a canonical public URL and validate it.

GitHub Pages serves this project from a sub-path (e.g. https://wilsonify.github.io/pyknit/),
so root-relative asset URLs such as "/pyodide/pyodide.mjs" would resolve against the
domain root and 404. The CI build deliberately ships root-relative URLs because the
same artifact is served from the domain root by Docker/nginx and local dev servers.
This script is the production (GitHub Pages) step: it rewrites every runtime URL to an
absolute URL derived from a single SITE_URL configuration value, then validates that:

  * every PyScript interpreter / packages URL points under SITE_URL
  * every referenced file exists in the deployment artifact
  * no runtime URL starts with a bare "/pyodide/", "/pyscript/", or "/wheels/" path
    (which would escape the project sub-path and hit the domain root)
  * no generated runtime URL contains ".."
  * no root-relative src/href/action URLs or site-internal JS navigation URLs remain

Usage:
    SITE_URL=https://wilsonify.github.io/pyknit/ python scripts/prepare_pages_site.py [SITE_DIR]

SITE_DIR defaults to "site". Local development builds must NOT set SITE_URL: they keep
root-relative URLs and are served from the domain root.
"""

import os
import re
import sys
from pathlib import Path

ATTR_RE = re.compile(r"(?P<attr>(?:src|href|action|poster)\s*=\s*)(?P<q>[\"'])/(?P<path>[^\"']*)[\"']")
PY_CONFIG_RE = re.compile(r"<py-config\b[^>]*>(.*?)</py-config>", re.S | re.I)
INTERPRETER_RE = re.compile(r'interpreter\s*=\s*"([^"]+)"')
PACKAGES_RE = re.compile(r"packages\s*=\s*\[(.*?)\]", re.S)
JS_STR_RE = re.compile(r'"(?P<path>/[^"\s]*)"')
ROOT_REL_ATTR_RE = re.compile(r"(?:src|href|action|poster)\s*=\s*[\"']/(?!/)", re.I)
ATTR_VALUE_RE = re.compile(r"(?:src|href|action|poster)\s*=\s*[\"']([^\"']*)[\"']", re.I)
DOMAIN_ROOT_RE = re.compile(r'="/?(pyodide|pyscript|wheels)/', re.I)
ROOT_REL_QUOTED_RE = re.compile(r"[\"']/(?![/])[^\"']*[\"']")


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def _normalize_site_url(raw: str) -> str:
    url = raw.strip()
    if "://" not in url:
        fail(f"SITE_URL must be an absolute URL, got: {raw!r}")
    return url.rstrip("/") + "/"


def _rewrite_html(text: str, site_url: str) -> str:
    # 1. <base href> becomes the canonical public URL so relative links
    #    (demo cards, sock.jpg, back-to-index links) resolve under the site.
    text = re.sub(
        r"<base\s+href\s*=\s*[\"'][^\"']*[\"']",
        f'<base href="{site_url}"',
        text,
        flags=re.I,
    )
    # 2. Root-relative src/href/action/poster attributes become absolute.

    def _abs_attr(m: re.Match) -> str:
        return f'{m.group("attr")}{m.group("q")}{site_url}{m.group("path")}{m.group("q")}'

    text = ATTR_RE.sub(_abs_attr, text)

    # 3. PyScript configuration strings (interpreter, packages, paths, ...)
    #    become absolute URLs as well.

    def _abs_config(m: re.Match) -> str:
        block = m.group(0)

        def _abs_str(sm: re.Match) -> str:
            return f'{sm.group("q")}{site_url}{sm.group("path")}{sm.group("q")}'

        return re.sub(r'(?P<q>["\'])/(?P<path>[^"\']*)["\']', _abs_str, block)

    return PY_CONFIG_RE.sub(_abs_config, text)


def _rewrite_js(text: str, site_url: str, site_dir: Path) -> str:
    """Rewrite site-internal navigation strings in the site's own JS.

    Only double-quoted root-relative strings that resolve to an actual file in
    the deployment artifact are rewritten (e.g. "/yarn-estimator/demo.html");
    display strings such as "a/b" or "'/'" are left untouched.
    """

    def _maybe_abs(m: re.Match) -> str:
        path = m.group("path")
        if path.startswith("//"):
            return m.group(0)
        if (site_dir / path.lstrip("/")).is_file():
            return f'"{site_url}{path.lstrip("/")}"'
        return m.group(0)

    return JS_STR_RE.sub(_maybe_abs, text)


def _check_url(problems, rel, kind, url, site_url, site_dir):
    if ".." in url:
        problems.append(f"{rel}: {kind} URL contains '..': {url}")
        return
    if not url.startswith(site_url):
        problems.append(f"{rel}: {kind} URL {url!r} does not point at the deployed site {site_url!r}")
        return
    rel_path = url[len(site_url) :].split("#", 1)[0].split("?", 1)[0].lstrip("/")
    if not rel_path:
        return
    target = site_dir / rel_path
    if not target.is_file():
        problems.append(f"{rel}: {kind} URL references missing artifact file: {url}")


def _validate(site_dir: Path, site_url: str, html_files, js_files) -> None:
    problems: list[str] = []
    py_config_count = 0

    for path in html_files:
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(site_dir)

        for m in ROOT_REL_ATTR_RE.finditer(text):
            problems.append(f"{rel}: root-relative attribute {m.group(0)!r} must be absolute under {site_url}")
        for m in DOMAIN_ROOT_RE.finditer(text):
            problems.append(f"{rel}: domain-root runtime path {m.group(0)!r} would escape the deployed site")
        for m in ATTR_VALUE_RE.finditer(text):
            if ".." in m.group(1):
                problems.append(f"{rel}: generated URL contains '..': {m.group(1)!r}")
        for m in re.finditer(
            r'(?:src|href|action|poster)\s*=\s*["\'](' + re.escape(site_url) + r'[^"\']*)["\']',
            text,
            flags=re.I,
        ):
            url = m.group(1)
            rel_path = url[len(site_url) :].split("#", 1)[0].split("?", 1)[0].lstrip("/")
            if not rel_path:
                continue
            target = site_dir / rel_path
            if target.is_file():
                continue
            if target.is_dir() and (target / "index.html").is_file():
                continue
            problems.append(f"{rel}: referenced artifact file missing: {url}")

        for cfg in PY_CONFIG_RE.finditer(text):
            py_config_count += 1
            block = cfg.group(1)
            interp = INTERPRETER_RE.search(block)
            if not interp:
                problems.append(f"{rel}: <py-config> is missing an interpreter URL")
            else:
                _check_url(problems, rel, "interpreter", interp.group(1), site_url, site_dir)
            pkgs = PACKAGES_RE.search(block)
            if pkgs:
                for pkg in re.findall(r'"([^"]+)"', pkgs.group(1)):
                    _check_url(problems, rel, "packages", pkg, site_url, site_dir)
            for m in ROOT_REL_QUOTED_RE.finditer(block):
                problems.append(f"{rel}: <py-config> contains a non-absolute URL {m.group(0)!r}")

    if py_config_count == 0:
        problems.append("no <py-config> block found anywhere in the site")

    for path in js_files:
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(site_dir)
        for m in JS_STR_RE.finditer(text):
            p = m.group("path")
            if p.startswith("//"):
                continue
            if (site_dir / p.lstrip("/")).is_file():
                problems.append(f"{rel}: root-relative site URL {m.group(0)!r} still present in JS")

    if problems:
        for p in problems:
            print(f"ERROR: {p}", file=sys.stderr)
        sys.exit(1)


def main() -> int:
    site_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "site").resolve()
    site_url = _normalize_site_url(os.environ.get("SITE_URL", ""))
    if not site_dir.is_dir():
        fail(f"site directory not found: {site_dir}")

    html_files = sorted(site_dir.rglob("*.html"))
    js_files = sorted(site_dir.rglob("*.js"))
    if not html_files:
        fail(f"no HTML files found in {site_dir}")

    rewritten_html = 0
    rewritten_js = 0
    for path in html_files:
        text = path.read_text(encoding="utf-8")
        new_text = _rewrite_html(text, site_url)
        if new_text != text:
            path.write_text(new_text, encoding="utf-8")
            rewritten_html += 1
    for path in js_files:
        text = path.read_text(encoding="utf-8")
        new_text = _rewrite_js(text, site_url, site_dir)
        if new_text != text:
            path.write_text(new_text, encoding="utf-8")
            rewritten_js += 1

    _validate(site_dir, site_url, html_files, js_files)

    print(f"OK: rewrote {rewritten_html} HTML file(s), {rewritten_js} JS file(s) for {site_url}")
    for path in html_files:
        for cfg in PY_CONFIG_RE.finditer(path.read_text(encoding="utf-8")):
            interp = INTERPRETER_RE.search(cfg.group(1))
            if interp:
                print(f"  interpreter = {interp.group(1)!r}")
            pkgs = PACKAGES_RE.search(cfg.group(1))
            if pkgs:
                for pkg in re.findall(r'"([^"]+)"', pkgs.group(1)):
                    print(f"  packages    = {pkg!r}")
            break
    return 0


if __name__ == "__main__":
    sys.exit(main())
