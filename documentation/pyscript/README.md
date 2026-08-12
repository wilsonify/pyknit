# PyKnit in the Browser

This directory contains a fully interactive PyScript-based demo that runs pyKnit directly in your web browser. No server-side processing needed!

## Quick Start

### Prerequisites

- A modern web browser with WebAssembly support (Chrome 57+, Firefox 52+, Safari 14.1+, Edge 79+)
- A static HTTP server (Python, Node, Ruby, PHP, etc.)
- An internet connection (first visit downloads ~20-30 MB of packages from PyPI)

### Running the Demo

From this directory, run any of these commands:

**Python (built-in):**
```bash
python -m http.server
```

**Node.js:**
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

Then open your browser and navigate to:
```
http://localhost:8000/demo.html
```

## What You'll See

### Initial Load (First Visit)
1. **Loading banner** shows "Loading PyScript runtime and pyknit..." 
2. **Wait 30-60 seconds** while PyScript initializes
3. **Watch the browser console** (F12 > Console) for progress messages
4. **Ready banner** appears when pyknit is loaded
5. **Buttons become enabled** and you can interact with the demo

### Gauge Conversion Tool
- Adjust pattern gauge, your gauge, and measurement values
- Click **Convert** to see how the measurement changes between gauges
- Results show the calculated stitch count adjustment
- Invalid inputs display clear error messages

### Chart Rendering Tool
- Edit the knitting pattern in the textarea
- Click **Render Chart** to parse and visualize the pattern
- Results show:
  - SVG rendering (if available)
  - PNG rendering via Pillow (if available)
  - Plain text grid (always available as fallback)
  - List of backends available on your system
- Parse errors show exactly what went wrong

## How It Works

### Architecture

1. **PyScript Runtime**: Runs Python 3.11 in WebAssembly via PyScript
2. **Package Installation**: `py-config` automatically downloads:
   - `pydantic` (data validation, required by pyknit)
   - `pillow` (image processing, required by pyknit for PNG rendering)
   - `pyknit` (the main package from PyPI)
3. **Event Handling**: JavaScript event listeners trigger Python functions
4. **DOM Access**: Python code directly manipulates the HTML DOM
5. **Rendering**:
   - SVG backend renders as inline SVG
   - Pillow backend renders as base64-encoded PNG
   - Text backend always provides a fallback

### Key Features

- **Status tracking**: Clear loading → ready → error states
- **Input validation**: All inputs are validated before use
- **Error handling**: Every error produces a readable message
- **Graceful fallbacks**: If SVG or Pillow fail, text output works
- **Editable patterns**: Modify the knitting instructions in real time
- **Dynamic rendering**: Chart updates immediately when you change the pattern

## API Verification

The demo uses these real pyknit APIs:

### Gauge Conversion
- `pyknit.GaugeSwatch()` - Create gauge swatch with stitch/row counts
- `pyknit.convert_stitch_measure()` - Convert measurements between gauges

### Chart Rendering
- `pyknit.Chart.parse_chart()` - Parse knitting instructions into a grid
- `pyknit.browser.render_pattern()` - Render patterns with multiple backends
- `pyknit.browser.pattern_to_text()` - Fallback text rendering
- `pyknit.browser.available_backends()` - List available rendering backends

## Supported Knitting Instructions

The parser supports:
- `k` (knit)
- `p` (purl)
- `yo` (yarn over)
- `k2tog` (knit 2 together)
- `p2tog` (purl 2 together)
- `ssk` (slip, slip, knit)
- `m1` (make 1)
- `dec` (decrease)
- Repeats: `[instruction] * N times`
- Row separators: `\n` (newline)

See `pyknit.Chart.stitch_legend` for the complete list.

## Troubleshooting

### Page loads but buttons don't work

**Wait longer.** PyScript initialization takes 30-60 seconds on first visit. Watch the status banner and browser console (F12 > Console) for progress messages.

### "pyknit is not loaded" error

**Check your internet connection.** PyScript needs to download ~20-30 MB from PyPI on first visit, including Pillow (5 MB) which is required by pyknit. If the download fails:
1. Hard refresh (Ctrl+Shift+R or Cmd+Shift+R)
2. Clear service worker cache: F12 > Application > Service Workers > Unregister
3. Wait for packages to download (may take 1-2 minutes with Pillow)
4. Reload the page

**If error mentions "pillow" or "PIL":**
- Pillow is now explicitly listed in `py-config` and will auto-install
- Just wait longer and reload the page
- First visit is slower due to Pillow download (~5 MB)

### Browser console shows errors

Open F12 > Console and look for:
- **ImportError**: Missing package dependency (try hard refresh)
- **TypeError**: Python code error (check input values)
- **Network error**: PyPI unreachable (check internet connection)

### Chart won't render

If "Text backend" is shown but pattern is blank:
- Check the pattern syntax (use simple patterns like `k2 yo k2tog`)
- Look for red error messages below the render button
- Try the default pattern (`k2 yo k2tog yo k1`)

If SVG or Pillow aren't available:
- The demo automatically falls back to text rendering
- This is normal—not all browsers have graphical libraries
- Text rendering still shows you the chart correctly

### Measurement calculation shows weird results

1. Check all gauge values are positive and non-zero
2. Check measurement value is non-negative
3. Ensure you're entering decimal values correctly (e.g., `27.5` not `27,5`)

## Browser Compatibility

Tested and working on:
- ✅ Chrome/Chromium 90+
- ✅ Firefox 88+
- ✅ Safari 14.1+
- ✅ Edge 90+

Older browsers may not support WebAssembly. Update your browser for the best experience.

## First-Time Performance

| Step | Time |
|------|------|
| Page load | Instant |
| PyScript download | 5-10 seconds |
| Python runtime startup | 10-20 seconds |
| Package download (pydantic, pyknit) | 15-30 seconds |
| First interaction | Ready! |
| **Total** | **30-60 seconds** |

**Subsequent visits are much faster** (~5-10 seconds) because packages are cached in the browser.

## How It's Different from Local Installation

| Aspect | Browser Demo | Local Installation |
|--------|--------------|-------------------|
| Setup | None | `pip install pyknit` |
| First run | 30-60 seconds | Immediate |
| Subsequent runs | 5-10 seconds | Immediate |
| Dependencies | Auto-installed from PyPI | Pre-installed |
| Code editing | Not needed | Can modify and reload |
| Offline use | No (needs internet for first visit) | Yes |

## Customization

You can edit `demo.html` to:

1. **Change default values** (search for `value=` attributes)
2. **Add more knitting functions** (call other pyknit APIs in Python)
3. **Style the interface** (modify the `<style>` block)
4. **Add more examples** (add buttons and handler functions)

Example: To use `sleeve_decreases`:

```python
def handle_sleeve_decreases(event=None):
    if not READY:
        return
    # Get inputs, call: pyknit.sleeve_decreases(61, 59, 43, 2)
    # Display result
```

## Known Limitations

1. **First visit is slow** - PyScript must download and initialize the Python runtime
2. **Internet required** - First visit needs to download packages from PyPI
3. **No offline mode** - Requires internet for package downloads
4. **Some libraries unavailable** - Pillow may not be available in PyScript (SVG is always available)
5. **No file I/O** - Cannot read/write files on your computer
6. **No debugging** - Cannot use `pdb` debugger; use `print()` statements

## References

- [PyScript Documentation](https://docs.pyscript.com/)
- [pyKnit Repository](https://github.com/terriko/pyknit)
- [WebAssembly](https://webassembly.org/)
- [Pyodide (Python in browser)](https://pyodide.org/)

## Contributing

Found an issue? Here's how to debug it:

1. **Check the status banner** - Does it show "ready" or "error"?
2. **Open browser console** - F12 > Console, look for Python tracebacks
3. **Try the default examples** - Do they work?
4. **Check inputs** - Are all values valid?
5. **Hard refresh** - Ctrl+Shift+R to clear cache

If the issue persists, report it with:
- Your browser and version
- Screenshot of the error
- The pattern or gauge values you were using
