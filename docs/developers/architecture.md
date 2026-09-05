# Architecture

## Overview

pyKnit has two main components:

1. **Python library** -- Core knitting math and pattern logic
2. **Browser demos** -- Interactive tools that run the library in WebAssembly

```
                    pyKnit Architecture

  ┌─────────────────────────────────────────────┐
  │              Python Library                 │
  │                                             │
  │  Chart.py        GaugeSwatch.py             │
  │  (stitch model,  (gauge math,               │
  │   parsing,        conversions)              │
  │   rendering)                                │
  │                                             │
  │  Hat.py  Sock.py  shawl_shapes.py           │
  │  (garment-specific calculations)            │
  │                                             │
  │  estimate.py    __init__.py                 │
  │  (yarn/time)    (public API)                │
  └──────────────┬──────────────┬───────────────┘
                 │              │
    ┌────────────┘              └────────────┐
    ▼                                        ▼
┌───────────────┐                  ┌──────────────────┐
│ Python Users  │                  │  Browser Demos   │
│ (pip install) │                  │  (PyScript/      │
│               │                  │   WebAssembly)   │
│ import pyknit │                  │                  │
│ pyknit.func() │                  │  shared.py       │
└───────────────┘                  │  _demos/*.py     │
                                   │  demo.html       │
                                   └──────────────────┘
```

## Module map

| Module | Purpose |
|--------|---------|
| `pyknit/__init__.py` | Public API: `increase_evenly`, `decrease_evenly`, `raglan_increases`, `sleeve_decreases`, `pi_shawl` |
| `pyknit/Chart.py` | Stitch model, legends (English + Japanese), instruction parsing, SVG rendering |
| `pyknit/GaugeSwatch.py` | Gauge math, measurement conversions, yardage/weight estimation |
| `pyknit/Hat.py` | Hat crown decrease calculations |
| `pyknit/Sock.py` | Sock construction (heel flap, gusset, toe) |
| `pyknit/estimate.py` | Knitting time estimation |
| `pyknit/shawl_shapes.py` | Shawl shape generation (crescent, triangle, square, rectangle) |
| `pyknit/browser.py` | Browser-compatible rendering helpers |
| `pyknit/pyscript/_assets/shared.py` | DOM helpers, feature detection, demo wiring for PyScript |
| `pyknit/pyscript/_demos/*.py` | Demo modules (each exposes `DEMO` dict) |

## Browser demo architecture

Each demo consists of:

1. **`pyknit/pyscript/_demos/<name>.py`** -- Pure Python module
   - `DEFAULT_INPUTS` -- Default form values
   - `compute(inputs)` -- Process inputs, return results dict
   - `to_html(result)` -- Render results as HTML string
   - `DEMO` -- Dict wiring everything together

2. **`demos/<name>/demo.html`** -- Static HTML page
   - Loads PyScript runtime from `/_assets/pyscript/`
   - Installs pyknit from local wheel `/_wheel/pyknit-<version>.whl`
   - Calls `shared.bootstrap_demo(DEMO)` to wire everything up

3. **`demos/_assets/shared.py`** -- Shared Python helpers
   - DOM access (safe outside browser)
   - Input collection
   - Status banner management
   - Export/download support
   - pyknit feature detection

### Key constraint

The `compute()` function must be pure Python with no DOM access. Only `to_html()`
and the shared module touch the browser DOM. This allows unit testing without a
browser.

## Dependencies

### Python library

- `pydantic` -- Data validation (used by `@validate_arguments`)
- `Pillow` -- Image processing (chart rendering to PNG)

### Browser demos

- `pyodide` -- Python runtime compiled to WebAssembly
- `PyScript` -- Browser Python execution framework
- `pydantic` (wasm wheel)
- `Pillow` (wasm wheel)
- `pyknit` (local wheel)

## Testing strategy

| Test type | What it covers | How to run |
|-----------|---------------|------------|
| Unit tests | Python functions, demo compute() | `pytest test/unit/` |
| End-to-end tests | Docker image serves correctly | `pytest test/end-to-end/` |
| Demo tests | All demo modules load and compute | `pytest test/unit/test_pyscript_demos.py` |

## Design principles

1. **Deterministic** -- Same inputs always produce same outputs
2. **Explainable** -- Results include math breakdowns and assumptions
3. **Graceful degradation** -- Missing features produce fallbacks, not crashes
4. **Testable** -- Every demo module can be tested without a browser
5. **Independent** -- Each demo works standalone, no cross-demo dependencies
