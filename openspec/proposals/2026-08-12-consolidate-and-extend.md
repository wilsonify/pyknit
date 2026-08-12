# Proposal: Consolidate and Extend pyKnit

**Date:** 2026-08-12
**Status:** draft

## Relationship to Current Codebase

pyKnit has 13 open GitHub issues and 5 code TODOs (documented in `documentation/issues/` and `documentation/todos/`). Much of the request surface already exists in some form: gauge validation (issue #8, pydantic), increase/decrease spacing (issues #4, #9, #51), pi shawl (issues #14, #28), Japanese symbols (issue #48, partial), and hat/sock/sleeve components (issues #11, #39, partial). This proposal consolidates the overlapping remainder rather than implementing each issue in isolation, and it fixes the codebase's known internal inconsistencies (version strings, `Sock` bugs, raglan FIXME, CLI cm/in gap, parser that cannot read its own output).

## Problem

- The instruction parser (spec 02) cannot parse repeat notation, so `sleeve_decreases` and `decrease_evenly` output (spec 06) cannot be charted automatically (issue #5).
- `sleeve_decreases` and `decrease_evenly` duplicate spacing logic; remainder placement is a logged warning instead of math; `padding_mode` is hard-coded (TODOs 3-5).
- `Hat.crown_decreases` errors on non-even stitch division instead of distributing the remainder (TODO 2).
- `Sock` is [DRAFT]: two bugs prevent `init()` from completing.
- `raglan_increases` has an unimplemented branch (FIXME placeholder).
- No yardage/weight estimation (TODO 1), no knitting-time estimate (issue #50), no import/export (issue #13), no browser support (issue #45), no doctests (issue #19).
- Infrastructure nits: version mismatch (`0.0.7` vs `0.0.9`), CLI cannot convert cm<->in, CI matrix stops at 3.11 (issue #55).

## Proposed Change

### 1. Core knitting representation

- Repeat expansion in `parse_row`/`parse_chart` (two-pass: expand brackets, then existing regexes) - **IMPLEMENTED** - closes issue #5.
- CSV import/export + structured JSON with `schema_version`, typed units, provenance (`pattern_to_csv`, `csv_to_pattern`, `pattern_to_json`, `json_to_pattern`) - closes issue #13.
- Close remaining symbol-set gaps in default and Japanese legends (spec 01); add stitch metadata (category, direction, consumes/produces) for count validation.
- SVG renderer `render_chart_svg` matching PIL layout (supports issue #45).

### 2. Pattern generation and geometry

- Extract shared spacing core `_calculate_spacing`; add `padding_mode` (`'before' | 'after' | 'both' | 'none'`, default `'after'`) and automatic remainder placement to `sleeve_decreases` (TODOs 3-5).
- Remainder-aware `Hat.crown_decreases` (TODO 2); fix and finish `Sock` (spec 07).
- Add half-pi shawl (completes issue #14) and shawl-shape generators (square, rectangle, triangle, crescent; issue #11).
- Add `yardage_per_unit` / `weight_per_unit` to `GaugeSwatch` with `estimate_yardage` / `estimate_weight`, and `estimate_knitting_time` (TODO 1, issue #50).

### 3. User experience and infrastructure

- Doctests on all public functions; run via `pytest --doctest-modules` and Sphinx doctest extension in CI (issue #19).
- PyScript demo page with SVG fallback; graceful degradation to calculation-only mode (issue #45).
- Expand test coverage to the matrix in spec 10; add 3.12 to the CI matrix (issue #55).
- Unify version string; document CLI cm/in conversion gap and fix it.

## Affected Specs

- `02-instruction-parsing.md` - repeat expansion (**IMPLEMENTED**)
- `04-import-export.md` - full implementation (ADDED)
- `01-stitch-and-symbols.md`, `03-chart-rendering.md` - metadata, SVG (MODIFIED)
- `06-shaping.md` - spacing core, padding, remainder (MODIFIED)
- `07-garment-components.md` - sock fix, half-pi, shapes (MODIFIED)
- `08-estimation.md` - full implementation (ADDED)
- `09-python-api.md` - PyScript, CLI fixes (MODIFIED)
- `10-testing.md` - doctests, matrix expansion (MODIFIED)
- `11-docs-and-contributor-workflow.md` - doctest CI (MODIFIED)

## Implementation Plan

### Phase 1 - Stabilize (no API change)
1. Fix `Sock` bugs; fix raglan FIXME or scope it out explicitly.
2. Unify version string; fix CLI cm/in conversion with an explicit unit step.
3. Add 3.12 to CI matrix.
4. Ship the version-consistency and CI changes alone.

### Phase 2 - Parser and round-trip (closes #5, #13)
1. Implement repeat expansion in `parse_row` (backward compatible).
2. Round-trip: `parse_row(increase_evenly(...))`, `parse_row(sleeve_decreases(...))` -> correct counts.
3. Implement CSV import/export, then JSON.
4. Add SVG renderer.

### Phase 3 - Shaping consolidation (TODOs 2-5)
1. Extract `_calculate_spacing`; refactor `decrease_evenly` and `sleeve_decreases` onto it; verify byte-identical output on existing fixtures.
2. Add `padding_mode`; implement automatic remainder placement.
3. Remainder-aware hat crown.

### Phase 4 - Components and estimation (issues #11, #14, #50)
1. Half-pi shawl; shawl-shape generators.
2. Gauge yardage/weight fields; `estimate_yardage` / `estimate_weight` / `estimate_knitting_time`.

### Phase 5 - Docs, browser, and polish (issues #19, #45)
1. Doctests everywhere; wire into CI.
2. PyScript demo + SVG fallback; expand notebooks.
3. Full spec 10 test matrix; update issue/TODO notes; archive this proposal.

## Migration Strategy

- **Backward compatibility is the hard rule.** Public function output strings (`increase_evenly`, `decrease_evenly`, `sleeve_decreases`) stay byte-identical for existing inputs; `padding_mode` defaults to today's `'after'` behavior. `parse_row` gains capability without changing behavior on legacy inputs. `GaugeSwatch` gains optional fields (defaults None) - existing construction code is untouched.
- New modules land as flat files in `pyknit/` (e.g. `pyknit/io.py`, `pyknit/estimate.py`); package restructuring into subpackages is explicitly deferred until the module count justifies it.
- No new runtime dependencies. CSV/JSON use stdlib; SVG uses `xml.etree.ElementTree`. PyScript is opt-in (extra wheel availability only), never a core import.
- Deprecation path: if a public signature must change, the old form is kept one release with a `DeprecationWarning` and a migration note in the README.

## Verification (acceptance criteria)

Each spec's Testing section is the checklist; the global gates:

1. **Determinism + byte-stability:** existing fixtures unchanged; same inputs give identical outputs across runs.
2. **Round-trip:** shaping output parses back to correct stitch counts; CSV/JSON export -> import yields an equal `Pattern`.
3. **Count correctness:** executed increases/decreases hit documented final counts (10->13, 20->15, 59->43); hat remainder distributes without error.
4. **Doctests:** all public docstring examples pass under `pytest --doctest-modules`; CI fails on drift.
5. **Browser:** PyScript page renders a chart via SVG with the same layout as PIL.
6. **Backward compat:** full pre-change fixture suite passes unmodified.
7. **Repeat expansion:** bracketed repeat patterns (e.g., "[k2, p2] * 6 times") correctly parsed and expanded without affecting existing functionality.
8. **Quality gates:** `pytest`, `black --check`, `flake8`, docs build, and cve scan all green.

**Status:** [DRAFT] - pending review; no code changes made yet.