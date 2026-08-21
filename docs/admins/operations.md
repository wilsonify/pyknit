# Operations Guide

## Running tests

```bash
# Unit tests (fast, no Docker needed)
python -m pytest test/unit/ -x -q

# End-to-end tests (requires Docker)
python -m pytest test/end-to-end/ -x -q

# All tests
python -m pytest test/ -x -q

# Specific test class
python -m pytest test/unit/test_pyscript_demos.py::TestYarnAdvisor -xvs
```

## Local development server

```bash
cd demos
make setup serve
# Open http://localhost:8000/index.html
```

Or manually:

```bash
cd demos
pip wheel --no-deps --wheel-dir _wheel ..
python -m http.server 8000 --directory .
```

## Validating all demos

```bash
# Build wheel and start server
cd demos && make setup serve &

# Check each demo returns 200
for demo in gauge-conversion chart-renderer even-shaping hat-crown pi-shawl \
  raglan-sweater shawl-shapes sleeve-decreases sock-calculator yarn-estimator \
  yarn-advisor needle-advisor knit-simulator; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/$demo/demo.html")
  echo "$code $demo"
done
```

## Checking for browser errors

1. Open a demo in Chrome
2. Open Developer Tools (F12)
3. Go to Console tab
4. Look for red errors
5. Common issues:
   - `ImportError` -- Wheel version mismatch, rebuild wheel
   - `TypeError` -- Input validation issue
   - Network error -- Check internet connection

## Common problems and fixes

### Demo returns 404

**Cause:** nginx configuration issue or missing file.

**Fix:** Check that `demos/nginx.conf` has `try_files $uri $uri/index.html =404;`

### Import error in browser console

**Cause:** Wheel version in HTML doesn't match built wheel.

**Fix:**
```bash
# Rebuild wheel
cd demos && make wheel

# Update version in all demo.html files
grep -r "pyknit-0.1" demos/*/demo.html
# Update to current version
```

### PyScript fails to load

**Cause:** Browser doesn't support WebAssembly, or network issue.

**Fix:** Use a modern browser (Chrome 57+, Firefox 52+, Safari 14.1+).

### Tests fail after version bump

**Cause:** Test files reference old version string.

**Fix:** Update version in:
- `test/unit/test_cli.py`
- `test/end-to-end/test_docker_image.py`
- `test/unit/test_pyscript_demos.py`

### Docker build fails

**Cause:** Network issue downloading Pyodide files, or Docker cache stale.

**Fix:**
```bash
docker build --no-cache -t pyknit-demos -f demos/Dockerfile .
```

## Monitoring

### What to check after deployment

- [ ] Landing page loads at `/`
- [ ] All 13 demo pages return 200
- [ ] At least one demo produces correct output
- [ ] No 500 errors in server logs
- [ ] Wheel file is accessible at `/_wheel/pyknit-*.whl`

### Health check

```bash
# Quick check
curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/

# Check wheel is accessible
curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/_wheel/pyknit-0.1.2-py3-none-any.whl
```
