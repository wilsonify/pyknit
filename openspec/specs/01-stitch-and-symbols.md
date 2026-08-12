# Stitch and Symbols

**Status:** [IMPLEMENTED] - `Stitch`, `stitch_legend`, and `stitch_legend_japanese` work in the current codebase. Extended stitch metadata is [PLANNED].

## Purpose

Represent a single knitting action (`Stitch`) and map terse stitch codes (`k`, `k2tog`, `C4L`) to their human-readable descriptions and chart symbols. This is the atom every other module consumes: parsing produces Stitch objects, charting renders their symbols, and stitch-count validation inspects their widths.

## The Stitch Object

A `Stitch` carries the display and semantic facts needed everywhere:

| Field         | Type   | Meaning                                                        |
| ------------- | ------ | -------------------------------------------------------------- |
| `instruction` | str    | Human-readable description ("knit", "knit two together")       |
| `symbol`      | str    | Display token - see Symbol Representation below                |
| `width`       | int    | Stitch-units occupied in a chart (default 1; cables are 2-4)   |

Planned extension (no current code): `category` (knit, purl, decrease, increase, cable, slip, yarn-over), `direction` (left / right / neutral), `consumes` and `produces` (stitches taken from and returned to the needles). These enable stitch-count correctness without string parsing.

## Symbol Representation

A symbol string is one of three kinds, detected by inspection:

| Kind           | Test                                          | Example        | Renderer   |
| -------------- | --------------------------------------------- | -------------- | ---------- |
| Character      | single non-color, non-path string             | `" "` (knit)   | font glyph |
| Image path     | ends in `.png` / `.jpg`                       | `"C4L.png"`    | image file |
| Color fill     | matches `^#[0-9a-fA-F]{6}$`                   | `"#FF0000"`    | solid cell |

Detection order used by `plot_chart`: color pattern first, `.png` suffix second, otherwise character.

## Legends

A legend is a `Dict[str, Stitch]` mapping codes to Stitch objects. The system keeps two built-in legends and accepts custom ones.

| Legend                    | Origin / coverage                                       | Status       |
| ------------------------- | ------------------------------------------------------- | ------------ |
| `stitch_legend`           | Craft Yarn Council symbol set plus cable PNGs           | [IMPLEMENTED] |
| `stitch_legend_japanese`  | Japanese chart symbols (`box.png`, `ktbl.png`, cables)  | [IMPLEMENTED] - coverage incomplete |

Coverage gaps to close (planned): the Japanese legend lacks a few codes that the default legend has, and the default legend lacks several Craft Yarn Council symbols (issue #30). Missing codes SHALL fall back to the default legend or raise a clear `KeyError`, never silently render the wrong glyph.

## Japanese Symbols

The Japanese legend currently includes: knit (`k`), purl (`p`), knit/purl through back loop (`ktbl`, `ptbl`), yarn over (`yo`), backwards yarn over (`byo`), single/double/triple decreases (`k2tog`, `k3tog`, `k4tog`, `p2tog`, `ssk`, `skp`, `ssp`, `sk2togp`, `sl2kp2`, `s3kp3`), no-stitch (`NA`), and cables (`C1-1L/R`, `C1-1PL/PR`, `C4L`, `C4R`). Sources are PNG assets under `pyknit/symbols/japanese/`.

Selection is per-parse: `parse_row(..., legend=stitch_legend_japanese)` and `parse_chart(..., legend=...)`. The default remains the Craft Yarn Council set (issue #48).

Code-quality note: the Japanese legend builds paths with `symbol_dir + "\japanese"` using a single backslash, which triggers `SyntaxWarning: invalid escape sequence '\j'` (it happens to resolve to `\japanese` literally on Windows). Planned fix: `os.path.join(symbol_dir, "japanese", ...)`. Two entries (`sk2togp`, `s3kp3`) also reference symbol strings without a `.png` extension, so they render as text, not images - and the on-disk file for the third-together decrease is `sl3kp3.png`, not `s3kp3.png`.

## Ownership

| Value                    | Owner                                  |
| ------------------------ | -------------------------------------- |
| Stitch object model      | `pyknit/Chart.py` (`Stitch`)           |
| Built-in legends         | `pyknit/Chart.py` (`stitch_legend`, `stitch_legend_japanese`) |
| Symbol images            | `pyknit/symbols/` and `pyknit/symbols/japanese/` |
| Stitch metadata extension | spec 01 [PLANNED]                     |

## Workflow Integration

Produced by parsing (spec 02), consumed by charting (spec 03). Widths are summed to compute row widths for rendering and stitch-count checks. `hat`, `sock`, and shaping outputs reference stitch codes; those codes must exist in an active legend to be chartable.

## Testing

- Equality: two Stitches are equal iff instruction, symbol, and width all match (`test_parse_row` builds expected arrays via `Stitch(...)`).
- Lookup failure: a code missing from a legend raises `KeyError` (`test_Stitch_unknown_stitch`).
- `parse_row("k1 p4 k1 p4 k kfb yo ssk k2tog")` yields the expected 15-element array using `stitch_legend` (spec 02 contract fixture).
- Cable stitches carry width 2-4 (`C2-1L` = 3 units) and render as images.
- Planned: metadata category/direction tests; every legend code resolves to a renderable symbol (no dangling image paths).