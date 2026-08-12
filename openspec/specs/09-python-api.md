# Python API, Jupyter, CLI, and Browser

**Status:** [IMPLEMENTED] - library import, Jupyter inline charts, and the CLI work. PyScript/browser support is [PLANNED].

## Purpose

Define the user-facing surface: how pyKnit is imported, used interactively in Jupyter, driven from a terminal, and - eventually - used in a browser without installing Python. One import surface, one set of public functions, consistent behavior everywhere.

## Python API

- `import pyknit` exposes the public surface: `GaugeSwatch`, `convert_stitch_measure`, `convert_row_measure`, `increase_evenly`, `decrease_evenly`, `sleeve_decreases`, `raglan_increases`, plus submodules `pyknit.Chart`, `pyknit.GaugeSwatch`, `pyknit.Hat`, `pyknit.Sock`, `pyknit.pi_shawl`.
- Re-exports live in `pyknit/__init__.py` (`from .Chart import *`, etc.).
- Version string inconsistency: `VERSION = "pyKnit 0.0.7"` in `__init__.py` vs. `0.0.9` in `pyproject.toml` - to be unified (issue #37 area).

### API Stability Rules

- Public signatures change only through a documented migration note and a deprecation window.
- New optional parameters default to current behavior (e.g. `padding_mode="after"`, spec 06).
- New functions are additive: `increase_evenly` and friends keep their exact output strings.

## Jupyter Support

- PIL `Image` objects render inline when a chart is the last expression of a cell - no extra code.
- Example notebooks live in `documentation/` (`SweaterFit.ipynb`, `SleeveDecreases.ipynb`, `TriangleHat.ipynb`, `CowlCable.ipynb`, `Japanese_Chart.ipynb`).
- Interactive exploration: changing gauge values in a cell recomputes downstream calculations on the next run (deterministic, no state to invalidate).

## CLI

`python -m pyknit` (entry point `pyknit`):

```
pyknit --convert row   --original-gauge-row 7 -ogr ... --new-gauge-row 6 ...
pyknit --convert stitch -ogs ... -ngs ...
```

Constructs `GaugeSwatch` instances and calls `measurement_to_rows/rows_to_measurement` or the stitch equivalents. Documented FIXMEs: no cm<->in conversion when the two gauges' units differ, and the unused dimension is hard-coded to 1 for convenience.

## Browser / PyScript (planned, issue #45)

Goal: run pyKnit in the browser without Jupyter. Architecture:

```html
<py-config>
  packages = ["pyknit"]
</py-config>
<py-script>
  import pyknit
  ...
</py-script>
```

- **Primary path:** PyScript with the real package (requires Pillow + pydantic as Pyodide packages).
- **Fallback:** SVG chart rendering (spec 03) when PIL is unavailable; identical layout.
- **Minimal path:** pure-Python calculations only (no charting) in constrained environments.
- Rendering SHALL degrade gracefully: no dependency, no blank output - text/code fallback instead.

## Ownership

| Value                | Owner                                  |
| -------------------- | -------------------------------------- |
| Public API surface   | `pyknit/__init__.py`                   |
| CLI                  | `pyknit/__main__.py`                   |
| Notebooks            | `documentation/*.ipynb`                |
| Browser/PyScript     | spec 09 [PLANNED]                      |
| SVG renderer         | spec 03 [PLANNED]                      |

## Workflow Integration

Thin layer over specs 01-08 - no logic lives here. Jupyter and CLI are the two supported front-ends today; the browser becomes a third, reusing the same functions.

## Testing

- Import smoke: `import pyknit; pyknit.GaugeSwatch(...)` and `from pyknit.Chart import parse_row, stitch_legend` both work.
- CLI: `--convert row` and `--convert stitch` produce the documented numbers; missing arguments fall back to `input()` prompts.
- Jupyter: chart cell last-expression returns a PIL `Image`.
- Planned: PyScript smoke test (import + a calculation + an SVG render) in CI or a manual demo page.