# Troubleshooting

## Users

### Tools won't load

**Symptom:** Page loads but shows "Loading pyknit..." forever.

**Causes and fixes:**
1. **First visit is slow** -- Wait 30-60 seconds. This is normal.
2. **Internet connection** -- First visit needs to download packages. Check your connection.
3. **Browser too old** -- Use Chrome 57+, Firefox 52+, Safari 14.1+, or Edge 79+.
4. **Stale cache** -- Hard refresh (Ctrl+Shift+R or Cmd+Shift+R).

### Results look wrong

**Symptom:** Numbers don't match expectations.

**Check:**
- Are your gauge values correct? (stitches and rows per inch)
- Are you using the right units? (inches vs centimeters)
- Read the warnings -- tools warn when inputs seem unusual

### Buttons don't respond

**Symptom:** Clicking "Calculate" does nothing.

**Fix:** Hard refresh (Ctrl+Shift+R). If that doesn't work, clear browser data:
- Chrome: Settings > Privacy > Clear browsing data > Cached images and files
- Firefox: Settings > Privacy > Clear Data > Cache

## Developers

### `pip install -e .` fails

**Check:**
- You're in the right directory (should contain `pyproject.toml`)
- Python version is 3.9 or higher
- `pip` is up to date: `pip install --upgrade pip`

### Tests fail with import errors

**Fix:**
```bash
pip install -e .
pip install -r requirements.txt
```

### `make wheel` fails

**Check:**
- You're in the `demos/` directory
- Python is available: `python3 --version`
- pip wheel is available: `python3 -m pip wheel --help`

### Demo module not found in browser

**Symptom:** `ImportError: cannot import name 'xxx' from 'pyknit.pyscript._demos'`

**Fix:**
1. Rebuild the wheel: `cd demos && make wheel`
2. Hard refresh the browser (Ctrl+Shift+R)
3. If that doesn't work, bump the version in `pyproject.toml` and rebuild

## Admins

### Docker build fails

**Check:**
- Docker is running: `docker ps`
- Network is available (downloads Pyodide files)
- Try with no cache: `docker build --no-cache -t pyknit-demos -f demos/Dockerfile .`

### Demo returns 404

**Check:**
- nginx config: `demos/nginx.conf` should have `try_files $uri $uri/index.html =404;`
- File exists: `ls demos/<demo-name>/demo.html`

### Wheel file not accessible

**Symptom:** Browser console shows network error loading wheel.

**Check:**
- Wheel exists: `ls demos/_wheel/pyknit-*.whl`
- Correct version: matches what's in the `<py-config>` block
- File is served: `curl -I http://localhost:8000/_wheel/pyknit-0.1.2-py3-none-any.whl`

### Stale cached assets

**Symptom:** Old version of a demo loads after deploying new version.

**Fix:** Bump the wheel version number. This forces browsers to download the new wheel.
