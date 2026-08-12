# Chart Rendering

**Status:** [IMPLEMENTED] - `plot_chart` renders PIL images with grid lines, numbering, and direction handling. SVG rendering is [PLANNED].

## Purpose

Turn a `Pattern` (spec 02) into a visual chart a knitter can read: rows of symbol cells with grid lines, row/column numbers, and correct reading direction for right-side and wrong-side rows. One renderer is the Jupyter/browser output; a planned SVG renderer serves browser environments without PIL.

## Inputs

| Input           | Notes                                                        |
| --------------- | ------------------------------------------------------------ |
| `stitch_array`  | `Pattern` (or a single `PatternRow`)                         |
| `lr_direction`  | `"lr"` (left-to-right) or `"rl"` (right-to-left)             |
| `tb_direction`  | `"tb"` (top-to-bottom) or `"bt"` (bottom-to-top)             |
| `legend`        | used symbol set (cells already hold resolved Stitch objects) |

A single row is normalized into a one-row list before the 2D loop. The longest row width sets the canvas width; rows may legitimately differ in width.

## Rendering Rules

- Cell size is fixed (currently 50x50 px; exposed as constants).
- Each stitch occupies `width` cells horizontally; multi-width cables span 2-4 columns.
- Symbols render three ways (spec 01): font glyph, pasted PNG image, or solid color fill.
- White-on-grid line drawing uses `Times.ttf` / `Inkfree.ttf`; font availability is a known fragility (issue #10) - planned fix is bundled fonts or recorded fallback.
- Row numbers repeat along `longest_row_len` and column numbers along row count, positioned by reading direction.

## Reading Direction

`instruction_to_plot_order(input_array, vertical_order, horizontal_order)` reorders rows/cols so writtens rows (odd = right-side, even = wrong-side) read correctly. Bottom-to-top (`bt`) reverses vertical order; right-to-left (`rl`) reverses each row. Default render call: `plot_chart(pattern, lr_direction="lr", tb_direction="tb")`.

## SVG Fallback (planned)

A `render_chart_svg(...)` SHALL produce the same layout as the PIL renderer without PIL:

- Character and color-fill symbols render as native SVG elements.
- Image symbols embed as base64 data URIs, or fall back to a text label when unavailable.
- This is required for the browser/PyScript path (spec 09) and must match the PIL renderer's visual layout.

## Ownership

| Value                    | Owner                                 |
| ------------------------ | ------------------------------------- |
| PIL rendering            | `pyknit/Chart.py` (`plot_chart`, `print_row`) |
| Direction ordering       | `pyknit/Chart.py` (`instruction_to_plot_order`) |
| SVG renderer             | spec 03 [PLANNED]                     |
| Symbol images            | `pyknit/symbols/` (spec 01)           |

## Workflow Integration

Reads `Pattern` from parsing (spec 02). Produces a PIL `Image` for Jupyter cells (last-expression inline display, spec 09) and, later, an SVG string for the browser. Validation (spec 06) verifies stitch counts before rendering so charts always match the math.

## Testing

- `test_pyknit.py` fixtures: parse and rows; image tests compare rendered layouts (row/col counts) for 3x10 and cable-width rows.
- Direction: bottom-to-top with right-to-left WS rows matches standard chart conventions.
- Charts render under both default and Japanese legends (every legend code resolves to a symbol).
- Planned SVG: visual equivalence with PIL for char/color/cable cases; valid XML; base64 embedding.