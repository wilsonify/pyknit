# pyKnit System Overview

**Status:** [IMPLEMENTED] - orientation document for all module specs

## What pyKnit Is

pyKnit is a set of tools for knitters to do math, create charts, and customize patterns. It turns "my gauge swatch + the measurements I want" into shaping instructions, resolves written instruction strings into a structured pattern, and renders that pattern as a chart image - with every number deterministic and every instruction produced by arithmetic, never magic.

pyKnit is a simple, realistic knitting math library, not a pattern-design simulator. It adds complexity only where it materially helps a knitter (even spacing math, gauge conversion, readable charts), and keeps everything deterministic, tested, and beginner-friendly.

**The north-star feel:** a friendly knitter who is also a tiny deterministic calculator - confidence and correctness ahead of fake precision.

## Core Principles

1. **Deterministic math** - identical input produces identical output. Arithmetic only; no random numbers, no hidden heuristics.
2. **One owner per calculated value** - every number is computed by exactly one module; other modules consume the result and never re-derive it.
3. **Written and chart representations stay in sync** - instructions and charts are two views of the same Pattern; round-tripping through the parser must preserve counts.
4. **Minimal dependencies** - Pillow (rendering) and pydantic (validation) only. No frameworks, databases, ML, or solver libraries.
5. **Validated inputs, clear errors** - nonsensical gauge, impossible decreases, and unknown stitches fail loudly with plain-language messages (pydantic + ValueError/KeyError).
6. **Backward-compatible growth** - shaping functions keep their output formats; new options default to current behavior.
7. **Both directions supported** - shaping functions generate instructions; the parser reads them back (see spec 02).

## The Single Pipeline

pyKnit builds one shared representation through the workflow, used by both generation and visualization:

```
Gauge Swatch (measurements, units)
  -> Measurement conversion   (measurement <-> stitches/rows)          spec 05
  -> Shaping                  (increases, decreases, sleeves, raglan)  spec 06
       |                                  |
       v                                  v
  Written instructions          Garment components (hat, sock, shawl, pi) spec 07
       |
       v
  Instruction parsing  ->  Pattern  ->  Chart rendering -> image/SVG      specs 02, 03
       |
       v
  Import / Export (CSV / JSON)  ->  file                                  spec 04
```

Estimation (yardage, weight, knitting time, spec 08) reads the same stitch counts and gauge; it never re-derives them.

Each section writes only its own fields and consumes prior results unchanged. See ownership sections in each spec.

## Module Index

| Spec                                                                 | Capability                                     | Status |
| -------------------------------------------------------------------- | ---------------------------------------------- | ------ |
| [01-stitch-and-symbols.md](01-stitch-and-symbols.md)                 | Stitch, legends, symbol sets (incl. Japanese)  | [IMPLEMENTED] |
| [02-instruction-parsing.md](02-instruction-parsing.md)               | Grammar, repeats, Pattern model                | [PLANNED] - base [IMPLEMENTED] |
| [03-chart-rendering.md](03-chart-rendering.md)                       | Chart representation, PIL rendering            | [IMPLEMENTED] - SVG fallback [PLANNED] |
| [04-import-export.md](04-import-export.md)                           | CSV / JSON interchange                         | [PLANNED] |
| [05-gauge-and-conversions.md](05-gauge-and-conversions.md)           | Gauge swatch, measurement conversions          | [IMPLEMENTED] |
| [06-shaping.md](06-shaping.md)                                       | Increase/decrease spacing, sleeves, raglan     | [IMPLEMENTED] - padding/remainder [PLANNED] |
| [07-garment-components.md](07-garment-components.md)                 | Hat, sock, pi shawl, shawl shapes              | [IMPLEMENTED] (partial) - sock [DRAFT] |
| [08-estimation.md](08-estimation.md)                                 | Yardage, weight, knitting-time estimates       | [PLANNED] |
| [09-python-api.md](09-python-api.md)                                 | Python API, Jupyter, CLI, browser              | [IMPLEMENTED] - PyScript [PLANNED] |
| [10-testing.md](10-testing.md)                                       | Correctness, determinism, doctests             | [IMPLEMENTED] - doctests [PLANNED] |
| [11-docs-and-contributor-workflow.md](11-docs-and-contributor-workflow.md) | Documentation, CI, contributor process    | [IMPLEMENTED] |

## Known Gaps in the Current Code

The spec statuses above reflect these concrete facts in `pyknit/`:

- `parse_row` handles basic stitch codes and cables but **not** repeat blocks, so it cannot parse the output of `sleeve_decreases` or `decrease_evenly` (issue #5, spec 02).
- `GaugeSwatch` has no yardage/weight fields (spec 08).
- `Hat.crown_decreases` errors when the stitch count does not divide evenly instead of distributing the remainder (spec 07).
- `sleeve_decreases` and `decrease_evenly` duplicate spacing logic and `sleeve_decreases` hard-codes padding-after behavior (spec 06).
- `raglan_increases` has a `FIXME` placeholder (`no_increase_rows = 555`) for the no-increase-row case (spec 06).
- `Sock` is a work in progress: `get_length_from_heel_to_beginning_of_toe_decrease` references an unset attribute and `get_number_of_decrease_rows` has a bug (spec 07, status [DRAFT]).
- `__main__.py` (`--convert`) cannot convert between cm and in (FIXME), and hard-codes dummy values for the unused dimension (spec 05, spec 09).

## Deferred / Out of Scope

- A full pattern language (KnitML, machine-knit file formats, `.knitout`).
- 3D garment visualization, draping simulation, or fit prediction.
- ML or statistical models for pattern recognition.
- Social features (sharing, rating patterns), accounts, or a hosted service.
- Video/animation of knitting techniques.

## Status Legend

- **[IMPLEMENTED]** - working in the current codebase
- **[MOCK]** - present in UI but uses simplified client-side approximations
- **[PLANNED]** - documented intent, not yet started
- **[DRAFT]** - proposal or spec under development