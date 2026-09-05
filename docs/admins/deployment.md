# Deployment Guide

## Overview

The pyKnit demos are static HTML files served by any HTTP server. The Python
runtime runs entirely in the browser via WebAssembly -- there is no backend.

## Static hosting

Any static file server works:

```bash
# From the repo root
cd demos
python -m http.server 8000
# Open http://localhost:8000/index.html
```

### Required files

```
demos/
  index.html                 # Landing page
  <demo-name>/demo.html      # One page per demo
  _assets/
    common.css               # Shared styles
    pyscript/core.js         # PyScript runtime
    pyscript/core.css        # PyScript styles
    pyodide/                 # Python WebAssembly runtime
  _wheel/
    pyknit-<version>.whl     # pyknit package for browser use
```

### What NOT to serve

- `demos/_assets/japanese-symbols/` -- Source images, not needed at runtime
- `demos/Makefile` -- Build tool, not needed at runtime
- `demos/Dockerfile` -- Build instructions, not needed at runtime

## Docker

### Build

```bash
cd pyknit
docker build -t pyknit-demos -f demos/Dockerfile .
```

### Run

```bash
docker run -p 8080:8080 pyknit-demos
# Open http://localhost:8080
```

### Validate

```bash
python -m pytest test/end-to-end/ -x -q
```

### What the Docker build does

1. Builds a wheel from the current source (`pip wheel`)
2. Copies demo HTML and assets
3. Downloads PyScript/Pyodide runtime files
4. Copies everything into an nginx container

### Common Docker issues

| Problem | Cause | Fix |
|---------|-------|-----|
| 404 on `/` | nginx config wrong | Check `demos/nginx.conf` |
| Demo shows import error | Wheel version mismatch | Rebuild: `docker build --no-cache` |
| Slow first load | Normal | 30-60s first visit, cached after |

## Releasing

### Version bump

1. Update `version` in `pyproject.toml`
2. Update `VERSION` in `pyknit/__init__.py`
3. Update wheel filename in all `demos/*/demo.html` files
4. Rebuild wheel: `cd demos && make wheel`
5. Update `demos/_wheel/pyknit-<new-version>.whl`

### Pre-release checklist

```bash
# Run all tests
python -m pytest test/ -x -q

# Build and test Docker
cd demos && make docker

# Verify all demos serve
python -m http.server 8000 --directory demos
# Open each demo and verify it works
```

### Post-release

1. Tag the release: `git tag v<version>`
2. Push: `git push origin v<version>`
3. Publish to PyPI (if applicable): `python -m twine upload dist/*`

## Caching behavior

- PyScript/Pyodide caches packages in the browser's IndexedDB
- Changing the wheel version (e.g., `pyknit-0.1.1` to `pyknit-0.1.2`) forces
  browsers to download the new version
- Users can hard-refresh (Ctrl+Shift+R) to clear cached assets

## Performance

| Phase | Time | Notes |
|-------|------|-------|
| First visit | 30-60s | Downloads ~20 MB of packages |
| Subsequent visits | 5-10s | Packages cached in browser |
| Tool execution | Instant | Python runs locally in browser |

## Browser requirements

- Chrome 57+
- Firefox 52+
- Safari 14.1+
- Edge 79+

All modern browsers support WebAssembly.
