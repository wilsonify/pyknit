# Developer Guide

## Quick start

The fastest path from zero to a working change:

```bash
# Clone and install
git clone https://github.com/wilsonify/pyknit.git
cd pyknit
pip install -e .

# Run tests
python -m pytest test/unit/ -x -q

# Run a specific demo locally
cd demos
make setup serve
# Open http://localhost:8000/index.html
```

## Architecture

```
pyknit/
  pyknit/                  # Python package
    __init__.py            # Public API: increase_evenly, decrease_evenly,
                           #   raglan_increases, sleeve_decreases, etc.
    Chart.py               # Stitch model, legend, parsing, SVG rendering
    GaugeSwatch.py         # Gauge math, measurement conversions
    Hat.py                 # Hat crown decreases
    Sock.py                # Sock construction math
    estimate.py            # Yarn yardage and knitting time estimation
    shawl_shapes.py        # Shawl shape generation
    browser.py             # Browser-compatible rendering helpers
    pyscript/
      _assets/shared.py    # Shared DOM helpers, feature detection, demo wiring
      _demos/              # Demo Python modules (compute + render logic)
        <name>.py          # Each exposes DEMO dict: TITLE, DEFAULT_INPUTS,
                           #   compute(inputs), to_html(result)
  demos/                   # Static HTML pages (served by nginx or any HTTP server)
    index.html             # Landing page
    <demo-name>/demo.html  # One page per demo
    _assets/common.css     # Shared styles
    _wheel/                # Local pyknit wheel for browser use
    Makefile               # Build, serve, Docker targets
    Dockerfile             # Production image
  test/
    unit/                  # pytest unit tests
    end-to-end/            # Docker image validation tests
  docs/                    # Documentation (you are here)
  openspec/                # Design specifications
```

### Data flow

```
User fills form in demo.html
         |
    shared.collect_inputs()
         |
    demo.compute(inputs)      # Pure Python, uses pyknit functions
         |
    demo.to_html(result)      # Returns HTML string
         |
    shared.set_html("demo-output", html)
         |
    Browser renders result
```

### Key design principles

1. **Demo modules are pure Python** -- No DOM access in compute(), only in to_html()
2. **Everything degrades gracefully** -- Missing features produce fallback output, not crashes
3. **The wheel is the source of truth** -- Demos load from `/_wheel/pyknit-<version>.whl`, never from PyPI
4. **Tests drive correctness** -- Every demo module has unit tests that run without a browser

## API examples

### Gauge conversion

```python
import pyknit

pattern = pyknit.GaugeSwatch(
    stitch_count=27.5, stitch_measure=10,
    row_count=40, row_measure=4, units="in"
)
mine = pyknit.GaugeSwatch(
    stitch_count=23.5, stitch_measure=10,
    row_count=33, row_measure=4, units="in"
)

# What size should I knit for a 42" chest?
my_size = pyknit.convert_stitch_measure(42, pattern, mine)
```

### Even shaping

```python
# Increase 5 stitches evenly across 20 stitches in the round
pyknit.increase_evenly(20, 5, in_the_round=True)
# '[k4, m1] * 5 times'

# Decrease 3 stitches evenly across 15 stitches flat
pyknit.decrease_evenly(15, 3, in_the_round=False)
# 'k5, k2tog, [k4, k2tog] * 2 times, k1'
```

### Sleeve decreases

```python
pyknit.sleeve_decreases(
    number_of_rows=61,
    starting_count=59,
    ending_count=43,
    decrease_per_row=2
)
# '[decrease row, do 7 rows in pattern] * 5 times,
#  [decrease row, do 6 rows in pattern] * 3 times'
```

### Raglan increases

```python
pyknit.raglan_increases(
    number_of_stitches=80,
    number_of_increase_rows=10,
    number_of_markers=4
)
```

### Chart parsing

```python
from pyknit.Chart import parse_chart, render_chart_svg, stitch_legend

pattern = parse_chart("k2 yo k2tog\np2 k1 p1", stitch_legend)
svg = render_chart_svg(pattern)
```

## Creating a new demo

### 1. Create the Python module

Create `pyknit/pyscript/_demos/my_demo.py`:

```python
"""My Demo: short description of what it does."""

DEFAULT_INPUTS = {
    "stitch_count": 20,
    "operation": "increase",
}

TITLE = "My Demo"

def compute(inputs):
    """Process inputs and return results."""
    count = int(inputs.get("stitch_count", 20))
    # ... your logic here ...
    return {
        "result": count * 2,
        "steps": [...],
    }

def to_html(result):
    """Render results as HTML."""
    return f"<div class='output-box'>Result: {result['result']}</div>"

DEMO = {
    "TITLE": TITLE,
    "DEFAULT_INPUTS": DEFAULT_INPUTS,
    "compute": compute,
    "to_html": to_html,
}
```

### 2. Create the HTML page

Create `demos/my-demo/demo.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>pyKnit · My Demo</title>
  <link rel="stylesheet" href="/_assets/pyscript/core.css" />
  <script type="module" src="/_assets/pyscript/core.js"></script>
  <link rel="stylesheet" href="/_assets/common.css" />
</head>
<body>
  <header class="demo-header">
    <div class="eyebrow">pyKnit · PyScript demo</div>
    <h1>My Demo</h1>
    <p>What this tool does for knitters.</p>
    <div class="linkbar"><a href="/index.html">&larr; all tools</a></div>
  </header>

  <div id="status-banner" class="status-banner loading">
    <div class="status-icon"></div>
    <div class="status-text">
      <p id="status-message">Loading pyknit...</p>
      <p id="status-detail" class="detail"></p>
    </div>
  </div>

  <py-config>
    interpreter = "/_assets/pyodide/pyodide.mjs"
    packages = ["/_assets/wheels/typing_extensions-4.7.1-py3-none-any.whl", "/_assets/wheels/pydantic-1.10.7-py3-none-any.whl", "/_assets/wheels/Pillow-10.0.0-cp311-cp311-emscripten_3_1_45_wasm32.whl", "/_wheel/pyknit-0.1.2-py3-none-any.whl"]
    terminal = false
  </py-config>

  <section class="card">
    <h2>Inputs</h2>
    <div class="form-group">
      <label for="stitch_count">Stitch count</label>
      <input id="stitch_count" type="number" value="20" min="1" />
    </div>
    <div class="button-row">
      <button id="run" class="btn-primary">Calculate</button>
    </div>
    <div id="demo-error" class="error-message" style="display:none;"></div>
  </section>

  <div id="demo-output"></div>

  <script type="py">
    from pyknit.pyscript._assets import shared
    from pyknit.pyscript._demos import my_demo as DEMO
    shared.bootstrap_demo(DEMO, action_label="Calculate")
  </script>
</body>
</html>
```

### 3. Add tests

Add tests to `test/unit/test_pyscript_demos.py`:

```python
def test_my_demo_compute(self):
    module = load_demo("my_demo")
    result = module.DEMO["compute"](module.DEMO["DEFAULT_INPUTS"])
    assert result["result"] > 0

def test_my_demo_html(self):
    module = load_demo("my_demo")
    result = module.DEMO["compute"](module.DEMO["DEFAULT_INPUTS"])
    html = module.DEMO["to_html"](result)
    assert "output-box" in html
```

### 4. Add to landing page

Add a card to `demos/index.html` in the appropriate category.

### 5. Verify

```bash
python -m pytest test/unit/test_pyscript_demos.py -x -q
cd demos && make setup serve
# Open http://localhost:8000/index.html and test your demo
```

## Testing

```bash
# Run all unit tests
python -m pytest test/unit/ -x -q

# Run all tests including end-to-end
python -m pytest test/ -x -q

# Run a specific test class
python -m pytest test/unit/test_pyscript_demos.py::TestYarnAdvisor -xvs

# Run with coverage
python -m pytest test/unit/ --cov=pyknit
```

## Code style

```bash
# Format code
black pyknit/ test/

# Check linting
flake8 pyknit/ test/
```

## Useful links

- [openspec/](../openspec/) -- Design specifications
- [documentation/](../documentation/) -- Legacy notebooks and notes
- [demos/](../demos/) -- Browser demo source
