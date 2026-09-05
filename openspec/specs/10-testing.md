# Test Requirements

**Status:** [IMPLEMENTED] - pytest suite covers core functions. Doctests are [PLANNED] (issue #19).

## Purpose

pyKnit promises determinism and correct math, so tests prove both: every public function has unit tests, generated instructions are checked against executed stitch counts, and round-trips (parse, import/export) preserve data. Doctests keep docstring examples honest.

## Invariants (global)

1. **Determinism** - identical input produces identical output, every module.
2. **One owner per calculated value** - no module re-derives another's (spec 09 contracts).
3. **Stitch-count correctness** - shaping output, parsed back, yields the documented final count.
4. **Backward compatibility** - existing public outputs stay byte-identical (spec 06 output contract).
5. **No new dependencies** - tests and code avoid new frameworks (no hypothesis, no doctest-only runners beyond pytest).

## Test Suite Map

### Stitch and Symbols (spec 01)
- Stitch equality by attributes; `KeyError` for unknown codes.
- Every legend code resolves to a renderable symbol (planned: dangling-path check).

### Instruction Parsing (spec 02)
- `"k1 p4 k1 p4 k kfb yo ssk k2tog"` -> 15-element array (existing fixture).
- Cable-before-compound ordering; planned repeat expansion and round-trip of generated instructions.

### Chart Rendering (spec 03)
- Row/column counts, multi-width cables, numbering; direction reordering (bt / rl).
- Planned: PIL <-> SVG visual equivalence.

### Import/Export (spec 04)
- Round-trip equality for CSV and JSON; determinism (stable bytes); schema-version rejection.

### Gauge and Conversions (spec 05)
- Construction, `row_gauge`, `stitch_gauge`, all four conversions (existing `test_GaugeSwatch.py`).
- Zero measurement -> pydantic ValidationError; cross-gauge conversion math.

### Shaping (spec 06)
- Parametrized happy paths and error cases for `increase_evenly` / `decrease_evenly` (existing `test_pyknit.py`).
- Sleeve fixture (61 rows / 59 -> 43 / per-row 2) -> 5+3 repeat string.
- Count-execution checks: increase 10->13, decrease 20->15, sleeve 59->43.
- Planned: `padding_mode` matrix, remainder placement, raglan missing branch.

### Garment Components (spec 07)
- Pi shawl fixtures `(5,5)->[2,6,13]`, `(50,3)->[2,6,13,26,51,100]`; total-rounds.
- Hat crown sequence; remainder case (currently error, planned extra decreases).
- Sock `init()` round-trip once bugs are fixed.

### Estimation (spec 08)
- Linear scaling and determinism; `timedelta` formatting; defaulted-field assumption notes.

### API / CLI / Browser (spec 09)
- Import smoke tests; CLI convert output; chart last-expression returns `Image`.

## Doctests (planned, issue #19)

- Every public function's docstring carries at least one `>>>` example; run with `pytest --doctest-modules` and via the Sphinx doctest extension.
- Trigger: issue #18 shipped a doc bug that doctests would have caught; regressions in README/SleeveDecreases.md examples are the acceptance driver.
- CI runs doctests and failures block merges (spec 11).

## Test Commands

```
pytest                      # unit + doctest suite
pytest --doctest-modules    # doctests across pyknit/
black --check .             # formatting (88-col)
flake8                      # lint
```

## CI Pipeline (current)

GitHub Actions (`python-package.yml`): pytest on Python 3.9/3.10/3.11; docs build job; black/flake8 pre-commit; cve-bin-tool security scan. Python 3.12+ compatibility is a known open item (issue #55) to add to the matrix.

## Ownership

| Value                          | Owner              |
| ------------------------------ | ------------------ |
| Invariants and test set        | spec 10 (`test/`)  |
| Doctest configuration          | spec 10 [PLANNED]  |
| Test runner / harness          | pytest in CI       |