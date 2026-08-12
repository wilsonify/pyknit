# PyKnit in the Browser

This directory contains a PyScript-based demo that runs pyKnit directly in your web browser. No server-side processing needed!

## ⚠️ First Time Setup

On first load, **wait 30-60 seconds** for PyScript to initialize. You'll see no output during this time - this is normal. Watch the browser console (F12 > Console) for progress messages.

Once loaded, buttons should work immediately.

## Quick Start

### Option 1: Using Python's built-in server

From this directory, run:

```bash
python -m http.server
```

Then open your browser and navigate to:

```
http://localhost:8000/demo.html
```

### Option 2: Using other web servers

You can use any static file server. For example:

**Node.js http-server:**
```bash
npx http-server
```

**Ruby:**
```bash
ruby -run -ehttpd . -p 8000
```

**PHP:**
```bash
php -S localhost:8000
```

## Features

The demo includes two interactive tools:

### Gauge Conversion
Convert a measurement from one gauge to another. For example:
- Pattern gauge: 27.5 stitches / 10 inches
- Your gauge: 23.5 stitches / 10 inches
- Result: See how a 42-inch measurement adjusts between gauges

### Chart Rendering
Parse knitting instructions and render them as a chart. The demo includes:
- Automatic backend selection (SVG preferred, falls back to Pillow/PNG, then plain text)
- Graceful degradation if rendering libraries aren't available
- Live preview with no compilation step

## How It Works

- **PyScript runtime**: Runs Python in the browser via WebAssembly
- **pyKnit package**: Loaded directly from PyPI
- **Dependencies**: The `py-config` block automatically downloads and installs required packages:
  - `pydantic` - for data validation
  - `pyknit` - the main package
- **Fallback behavior**: If SVG and Pillow aren't available, the page still works with plain-text output

Note: First visit requires downloading ~10-30 MB of packages. Subsequent visits use browser cache.

## Browser Compatibility

Works on modern browsers that support WebAssembly:
- Chrome/Chromium 57+
- Firefox 52+
- Safari 14.1+
- Edge 79+

## Troubleshooting

### "pydantic failed to load" or "cannot import name 'pydantic'"

**This is now fixed in demo.html** - pydantic is explicitly listed in `py-config`.

If you see this error:
1. Hard refresh your browser (Ctrl+Shift+R or Cmd+Shift+R)
2. Clear your browser's service worker cache and local storage
3. Wait for PyScript to download and install pydantic (1-2 minutes)

### Buttons don't respond

**Symptoms:** Buttons appear but clicking them does nothing

**Solutions:**
1. Wait longer - PyScript takes 30-60 seconds to initialize on first load
2. Open browser console (F12 > Console) and look for error messages
3. Make sure you're serving over HTTP/HTTPS (not opening the file directly with `file://`)
4. Hard refresh the page (Ctrl+Shift+R or Cmd+Shift+R) to clear cache
5. Check that JavaScript is enabled in your browser

**If errors mention "module not found":**
- Your internet connection may be slow; PyScript needs to download packages from PyPI
- Try again after a few minutes

### "pyknit failed to load"

- Check your internet connection (packages are loaded from PyPI)
- Open browser console (F12 > Console) to see detailed errors
- Make sure you're serving over HTTP (not opening the file directly)
- Wait for all packages to finish downloading

### Chart not rendering

- If SVG backend isn't available, Pillow is tried as a fallback
- If both fail, the chart is shown as plain text (this still works!)
- Check the "Backends available" line in the output

### Page is slow on first load

- PyScript downloads and initializes the Python runtime (~30-60 seconds on first visit)
- Additional time needed to download pydantic and pyknit packages from PyPI
- Subsequent visits are faster due to browser caching
- This is expected behavior for WebAssembly-based tools
- You can watch progress in the browser console (F12 > Console)

## Customization

Edit `demo.html` to:
- Change the example pattern (line 139-140)
- Modify gauge values (lines 115-121)
- Add more interactive tools using the `pyknit` API
- Style the page with your own CSS

## Production Deployment

To deploy this demo to production:

1. Ensure you have a static file hosting service (GitHub Pages, Netlify, Vercel, etc.)
2. Copy the `demo.html` file to your deployment
3. No special server-side setup required—it's 100% client-side

## API Examples

Once the page loads, you can use the full pyKnit API in the browser console:

```python
# Gauge conversion
from pyknit import GaugeSwatch, convert_stitch_measure
my_gauge = GaugeSwatch(stitch_count=23.5, stitch_measure=10, ...)
result = convert_stitch_measure(42, pattern_gauge, my_gauge)

# Parse and render
from pyknit.Chart import parse_chart
from pyknit import browser
pattern = parse_chart("k2 yo k2tog yo k1")
fmt, content = browser.render_pattern(pattern)

# Pattern generation
from pyknit import decrease_evenly, sleeve_decreases
pattern = decrease_evenly(20, 15)  # 20 stitches down to 15
```

## References

- [PyScript Documentation](https://docs.pyscript.com/)
- [pyKnit API Documentation](https://github.com/terriko/pyknit)
- [WebAssembly](https://webassembly.org/)

## Notes

This is a proof-of-concept demonstrating that pyKnit can run in any modern web browser with zero installation. The same Python code that runs on your desktop works identically in the browser environment.
