# Creating a Demo

This guide walks through creating a new interactive browser demo for pyKnit.

## Step 1: Choose the problem

Pick a knitting calculation that benefits from interactive input. Good candidates:
- Takes user measurements or preferences
- Produces a plan or recommendation
- Benefits from visual output

## Step 2: Reuse or add domain logic

Check if pyknit already has the function you need. If not, add it to the
appropriate module in `pyknit/`.

**Rules:**
- `compute()` in the demo module should be thin -- it collects inputs and calls
  pyknit functions
- Heavy math belongs in `pyknit/`, not in the demo module
- This keeps logic testable and reusable

## Step 3: Create the Python module

Create `pyknit/pyscript/_demos/<name>.py`:

```python
"""Short description of what this demo does."""

DEFAULT_INPUTS = {
    "field_name": "default_value",
}

TITLE = "Demo Title"

def compute(inputs):
    """Process inputs and return results.
    
    Must be pure Python -- no DOM access.
    Return a dict with all data needed by to_html().
    """
    value = inputs.get("field_name", "default_value")
    # Call pyknit functions here
    return {
        "result": processed_value,
        "warnings": [],
        "assumptions": [],
    }

def to_html(result):
    """Render results as HTML.
    
    Can access DOM via shared module if needed.
    Return an HTML string.
    """
    parts = []
    if result.get("warnings"):
        items = "".join(f"<li>{w}</li>" for w in result["warnings"])
        parts.append(f"<div class='warning-box'><ul>{items}</ul></div>")
    parts.append(f"<div class='output-box'>Result: {result['result']}</div>")
    return "\n".join(parts)

def _esc(text):
    """Escape HTML entities."""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

DEMO = {
    "TITLE": TITLE,
    "DEFAULT_INPUTS": DEFAULT_INPUTS,
    "compute": compute,
    "to_html": to_html,
}
```

## Step 4: Create the HTML page

Create `demos/<demo-name>/demo.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>pyKnit · Demo Title</title>
  <link rel="stylesheet" href="/_assets/pyscript/core.css" />
  <script type="module" src="/_assets/pyscript/core.js"></script>
  <link rel="stylesheet" href="/_assets/common.css" />
</head>
<body>
  <header class="demo-header">
    <div class="eyebrow">pyKnit · PyScript demo</div>
    <h1>Demo Title</h1>
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
    <p class="form-help">Explain what the user needs to enter.</p>
    <div class="grid-2">
      <div class="form-group">
        <label for="field_name">Field label</label>
        <input id="field_name" type="number" value="20" min="1" />
        <span class="field-hint">What this field means.</span>
      </div>
    </div>
    <div class="button-row">
      <button id="run" class="btn-primary">Calculate</button>
    </div>
    <div id="demo-error" class="error-message" style="display:none;"></div>
  </section>

  <div id="demo-output"></div>

  <footer>
    <p>Powered by <code>pyknit</code>.</p>
  </footer>

  <script type="py">
    from pyknit.pyscript._assets import shared
    from pyknit.pyscript._demos import <name> as DEMO
    shared.bootstrap_demo(DEMO, action_label="Calculate")
  </script>
</body>
</html>
```

## Step 5: Add tests

Add to `test/unit/test_pyscript_demos.py`:

```python
def test_<name>_compute(self):
    module = load_demo("<name>")
    result = module.DEMO["compute"](module.DEMO["DEFAULT_INPUTS"])
    assert "result" in result

def test_<name>_html(self):
    module = load_demo("<name>")
    result = module.DEMO["compute"](module.DEMO["DEFAULT_INPUTS"])
    html = module.DEMO["to_html"](result)
    assert "output-box" in html

def test_<name>_error_on_bad_input(self):
    module = load_demo("<name>")
    inputs = dict(module.DEMO["DEFAULT_INPUTS"])
    inputs["field_name"] = -1
    with pytest.raises(ValueError):
        module.DEMO["compute"](inputs)
```

## Step 6: Add to landing page

Add a card to `demos/index.html` in the appropriate category section.

## Step 7: Verify

```bash
# Run tests
python -m pytest test/unit/test_pyscript_demos.py -x -q

# Test locally
cd demos
make setup serve
# Open http://localhost:8000/<demo-name>/demo.html

# Verify landing page shows your demo
# Open http://localhost:8000/index.html
```

## Checklist

- [ ] Python module with `DEFAULT_INPUTS`, `compute()`, `to_html()`, `DEMO`
- [ ] HTML page with form, status banner, error display, PyScript config
- [ ] Unit tests for compute() and to_html()
- [ ] Error handling for invalid inputs (ValueError with clear message)
- [ ] Landing page card in the right category
- [ ] Field hints explaining what each input means
- [ ] Form help text explaining the tool's purpose
- [ ] Works with default inputs (auto-run on load)
- [ ] Verified in browser
