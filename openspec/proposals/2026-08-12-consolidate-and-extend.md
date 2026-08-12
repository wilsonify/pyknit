# Proposal: Consolidate and Extend pyKnit

**Date:** 2026-08-12
**Status:** in-progress

## Relationship to Current Codebase

pyKnit has 13 open GitHub issues and 5 code TODOs (documented in `documentation/issues/` and `documentation/todos/`). Much of the requested functionality already exists in some form or has been recently implemented:

**Completed:**
- Gauge validation (pydantic in GaugeSwatch)
- Core spacing logic extraction (`_calculate_spacing` in `__init__.py`)
- Padding mode support (`padding_mode` parameter in `sleeve_decreases`)
- Yardage/weight fields added to `GaugeSwatch`
- Knitting time estimation (`estimate_knitting_time` in `estimate.py`)
- SVG renderer (`browser.py` with multiple backends)
- JSON import/export with schema_version (`io.py`)
- Half-pi shawl and shawl-shape generators (`pi_shawl.py`, `shawl_shapes.py`)
- `Sock` class refactored and fixed
- Cognitive complexity reduced in key functions
- Code quality improvements (naming conventions, removed unused variables, floating-point comparisons)
- Untitled.ipynb removed

**In Progress / Remaining:**
- Full test matrix expansion (Python 3.12+ in CI)
- Browser/PyScript integration documentation
- Complete doctest coverage for all public functions

## Problem

**Status Update: Most issues have been addressed**

- ✅ The instruction parser (spec 02) now supports repeat notation via repeat expansion in `parse_row`
- ✅ `sleeve_decreases` and `decrease_evenly` share the extracted `_calculate_spacing` core; `padding_mode` is now fully parameterized with defaults; remainder placement is automatic
- ✅ `Hat.crown_decreases` properly distributes remainders without error
- ✅ `Sock` has been refactored and bugs fixed; no longer [DRAFT]
- ✅ `raglan_increases` branch has been completed
- ✅ Yardage/weight fields exist in `GaugeSwatch`; `estimate_knitting_time` is implemented
- ✅ JSON import/export with schema_version exists (`io.py`)
- ✅ SVG rendering support added via `browser.py` with multiple backends (PIL, SVG)
- ✅ Code cleaned of FIXME/TODO comments; cognitive complexity reduced
- ✅ Unused `Untitled.ipynb` removed
- ⏳ Doctests for all public functions (in progress)
- ⏳ Full test matrix expansion (Python 3.12+)
- ⏳ PyScript demo documentation

## Proposed Change

### 1. Core knitting representation (COMPLETED)

- ✅ Repeat expansion in `parse_row`/`parse_chart` - implemented
- ✅ CSV import/export + structured JSON with `schema_version`, typed units - implemented in `io.py`
- ✅ Stitch metadata (category, direction, consumes/produces) available in legends
- ✅ SVG renderer `render_chart_svg` matching PIL layout - implemented in `browser.py`

### 2. Pattern generation and geometry (COMPLETED)

- ✅ Extracted `_calculate_spacing` shared core
- ✅ `padding_mode` (`'before' | 'after' | 'both' | 'none'`, default `'after'`) fully implemented
- ✅ Automatic remainder placement via helper functions
- ✅ Remainder-aware `Hat.crown_decreases` implemented
- ✅ `Sock` fixed and completed
- ✅ Half-pi shawl added (`pi_shawl.py`)
- ✅ Shawl-shape generators added (`shawl_shapes.py`)
- ✅ `yardage_per_unit` / `weight_per_unit` fields in `GaugeSwatch`
- ✅ `estimate_yardage` / `estimate_weight` / `estimate_knitting_time` implemented (`estimate.py`)

### 3. User experience and infrastructure (PARTIALLY COMPLETED)

- ⏳ Doctests on all public functions (in progress)
- ✅ PyScript demo page available (see `documentation/pyscript/`)
- ⏳ Full test matrix expansion (Python 3.12+)
- ✅ Version string unified (0.0.9)
- ✅ CLI supports unit conversion
- ✅ Code quality: no FIXME/TODO comments, reduced cognitive complexity, naming standardized

## Affected Specs

- `02-instruction-parsing.md` - repeat expansion (✅ IMPLEMENTED)
- `04-import-export.md` - full implementation (✅ IMPLEMENTED)
- `01-stitch-and-symbols.md`, `03-chart-rendering.md` - metadata, SVG (✅ IMPLEMENTED)
- `06-shaping.md` - spacing core, padding, remainder (✅ IMPLEMENTED)
- `07-garment-components.md` - sock fix, half-pi, shapes (✅ IMPLEMENTED)
- `08-estimation.md` - full implementation (✅ IMPLEMENTED)
- `09-python-api.md` - PyScript, CLI fixes (✅ IMPLEMENTED)
- `10-testing.md` - doctests, matrix expansion (⏳ IN PROGRESS)
- `11-docs-and-contributor-workflow.md` - doctest CI (⏳ IN PROGRESS)

## Implementation Status

### Completed Phases

**Phase 1 - Stabilize (no API change)** ✅
- ✅ Fixed `Sock` bugs
- ✅ Completed raglan FIXME branch
- ✅ Unified version string (0.0.9)
- ✅ CLI supports cm/in conversion
- ✅ Improved code quality and maintainability

**Phase 2 - Parser and round-trip** ✅
- ✅ Repeat expansion in `parse_row`
- ✅ Round-trip parsing works correctly
- ✅ CSV import/export implemented
- ✅ JSON import/export with schema_version
- ✅ SVG renderer implemented

**Phase 3 - Shaping consolidation** ✅
- ✅ `_calculate_spacing` extracted and shared
- ✅ `padding_mode` fully parameterized
- ✅ Automatic remainder placement
- ✅ Remainder-aware hat crown

**Phase 4 - Components and estimation** ✅
- ✅ Half-pi shawl implemented
- ✅ Shawl-shape generators implemented
- ✅ Gauge yardage/weight fields
- ✅ `estimate_yardage` / `estimate_weight` / `estimate_knitting_time`

### In-Progress Phases

**Phase 5 - Docs, browser, and polish** ⏳
- ⏳ Doctests for all public functions (see `documentation/todos/`)
- ✅ PyScript demo available (see `documentation/pyscript/`)
- ⏳ Full spec 10 test matrix (Python 3.12+)
- ⏳ Archive this proposal after completion

## Migration Strategy

- **Backward compatibility maintained.** Public function output strings (`increase_evenly`, `decrease_evenly`, `sleeve_decreases`) remain byte-identical for existing inputs; `padding_mode` defaults to `'after'` (historical behavior). `parse_row` gained repeat expansion capability without changing behavior on legacy inputs. `GaugeSwatch` gained optional fields (defaults None) - existing code unchanged.
- New modules implemented as flat files in `pyknit/` (`io.py`, `estimate.py`, `browser.py`, `pi_shawl.py`, `shawl_shapes.py`).
- No new runtime dependencies for core functionality; optional backends (PIL, SVG) use stdlib or common libraries.
- Deprecation path: old forms kept one release with `DeprecationWarning` if a public signature must change.

## Recent Code Quality Improvements

- Fixed 4 FIXME comments in GaugeSwatch.py and __init__.py
- Removed 4 unused variables (draw, no_increase_rows, bad_stitch, err)
- Replaced dict() constructors with literals
- Renamed camelCase variables to snake_case (oldGauge→old_gauge, newGauge→new_gauge)
- Removed unused parameter k_higher from _handle_flat_even_higher_times
- Fixed floating-point equality checks using pytest.approx
- Reduced cognitive complexity in sleeve_decreases via helper functions
- Removed abandoned Untitled.ipynb notebook

## Verification (acceptance criteria)

Each spec's Testing section is the checklist; the global gates:

1. **Determinism + byte-stability:** ✅ existing fixtures unchanged; same inputs give identical outputs across runs.
2. **Round-trip:** ✅ shaping output parses back to correct stitch counts; JSON export → import yields equal `Pattern`.
3. **Count correctness:** ✅ executed increases/decreases hit documented final counts; hat remainder distributes without error.
4. **Doctests:** ⏳ all public docstring examples pass under `pytest --doctest-modules` (in progress).
5. **Browser:** ✅ PyScript page renders charts; SVG with same layout as PIL available.
6. **Backward compat:** ✅ full pre-change fixture suite passes unmodified.
7. **Repeat expansion:** ✅ bracketed repeat patterns correctly parsed and expanded.
8. **Code quality:** ✅ FIXME/TODO comments removed; cognitive complexity reduced; naming standardized; floating-point comparisons fixed.
9. **Quality gates:** ⏳ `pytest`, `black --check`, `flake8`, docs build (in progress for doctests).

**Status:** [IN-PROGRESS] - Phase 1-4 complete; Phase 5 (doctests and CI matrix) in progress.