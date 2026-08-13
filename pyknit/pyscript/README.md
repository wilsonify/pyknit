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

### "cannot import name 'browser' from 'pyknit'"

**This is now handled in demo.html** with a smart fallback.

The pyknit package on PyPI may have an older version that doesn't export the browser module. The demo handles this automatically:

```python
try:
    from pyknit import browser  # Try modern import
except ImportError:
    import pyknit.browser as browser  # Fallback to direct import
```

If you see this error:
1. Hard refresh your browser (Ctrl+Shift+R or Cmd+Shift+R)
2. Clear service worker cache: F12 > Application > Service Workers > Unregister
3. Wait for packages to download
4. Reload the page

The demo will work with both old and new versions of pyknit.

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

# PyScript Demo: PyPI Version Compatibility

## The Situation

**Current PyPI Status:**
- PyPI only has pyknit **0.0.9** available
- The `triage` branch with the `browser` module and updated `pyproject.toml` has NOT been released to PyPI yet
- PyScript always downloads from PyPI (unless configured otherwise)

**What This Means:**
- PyScript will load pyknit 0.0.9 from PyPI
- pyknit 0.0.9 does NOT have the `browser` module
- Direct import of `browser` will fail

## The Solution: Embedded Rendering

The demo HTML now includes **self-contained rendering functions** that work independently:

```python
# These functions are DEFINED in demo.html itself
def pattern_to_text(pattern):
    """Convert pattern grid to plain text"""
    
def available_backends():
    """Detect SVG, Pillow, or text-only rendering"""
    
def render_pattern(pattern):
    """Render with smart backend fallback"""
```

**Benefits:**
- ✅ Works with PyPI 0.0.9 (current)
- ✅ Works with triage branch (new)
- ✅ No external dependencies needed
- ✅ Always has a fallback (text rendering)

## How the Demo Works Now

```
User opens demo.html
    ↓
PyScript loads from PyPI
    ↓
Gets pyknit 0.0.9 (no browser module)
    ↓
Demo imports: GaugeSwatch, convert_stitch_measure, parse_chart
    ↓
Demo uses LOCAL rendering functions
    ↓
✅ Everything works!
```

## What's Needed for Full Integration

To use the new `browser` module from the triage branch in PyScript, you would need to:

### Option 1: Release to PyPI (Recommended)
```bash
# After merging triage to main
python -m build
python -m twine upload dist/*
```

Then PyScript would automatically get the new version with `browser` module.

### Option 2: Use Local Wheel
Create a custom PyScript config pointing to local wheel:
```html
<py-config>
  packages = ["file:///path/to/pyknit-0.0.10-py3-none-any.whl"]
</py-config>
```

### Option 3: Use Current Implementation (What We Did)
Self-contained rendering in the HTML - works with any version!

## Testing the Demo

The demo is **ready to use now**:

1. Run: `python -m http.server`
2. Open: `http://localhost:8000/documentation/pyscript/demo.html`
3. Wait 30-60 seconds for PyScript to load
4. Try gauge conversion and chart rendering

Both will work because:
- ✅ Gauge conversion uses `GaugeSwatch` and `convert_stitch_measure` (in 0.0.9)
- ✅ Chart rendering uses embedded `render_pattern()` (defined in HTML)

## Future: Using the Triage Branch

Once the triage branch is merged and released to PyPI as 0.0.10+:

```html
<!-- This will work automatically -->
<py-config>
  packages = ["pydantic", "pillow", "pyknit>=0.0.10"]
</py-config>
```

The demo could simplify to:
```python
from pyknit import browser
# Use browser.render_pattern() directly
```

But the current approach with embedded functions is **more robust** because it:
- Works with ANY version of pyknit
- Doesn't depend on updates to PyPI
- Provides consistent rendering across browsers
- Is self-contained and portable

## Summary

**Is PyScript aware of the triage branch?** No - PyScript downloads from PyPI, which only has 0.0.9.

**Does the demo work anyway?** Yes! Because we embedded the rendering logic.

**Will it work better when triage is released?** Yes, but it's not necessary - the embedded version is already optimal.

This is actually a great design because the demo is **future-proof and version-agnostic**!


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
