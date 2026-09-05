# pyKnit OpenSpec

OpenSpec is the source of truth for pyKnit development. All significant changes to the system are proposed, reviewed, and archived here before and after implementation.

## What is pyKnit?

pyKnit is a set of tools for knitters to do math, create charts, and customize patterns. It turns gauge swatch measurements into shaping instructions, written instructions into chart images, and (eventually) a set of reusable garment components into complete patterns.

pyKnit is intentionally simple: a small Python library with two runtime dependencies (Pillow, pydantic), deterministic math, and both written-instruction and chart representations of a pattern. See [system-overview.md](specs/system-overview.md) for orientation.

## Spec Index

- [system-overview.md](specs/system-overview.md) - Orientation: what pyKnit is, principles, module map
- [01-stitch-and-symbols.md](specs/01-stitch-and-symbols.md) - Stitch, legends, symbol sets (incl. Japanese)
- [02-instruction-parsing.md](specs/02-instruction-parsing.md) - Instruction grammar, repeats, Pattern model
- [03-chart-rendering.md](specs/03-chart-rendering.md) - Chart representation and rendering (PIL, SVG fallback)
- [04-import-export.md](specs/04-import-export.md) - CSV / JSON interchange, round-trip fidelity
- [05-gauge-and-conversions.md](specs/05-gauge-and-conversions.md) - Gauge swatch and measurement conversions
- [06-shaping.md](specs/06-shaping.md) - Increase/decrease spacing, sleeves, raglan
- [07-garment-components.md](specs/07-garment-components.md) - Hat, sock, pi shawl, shawl shapes
- [08-estimation.md](specs/08-estimation.md) - Yardage, weight, and knitting-time estimates
- [09-python-api.md](specs/09-python-api.md) - Python API, Jupyter, CLI, browser (PyScript)
- [10-testing.md](specs/10-testing.md) - Correctness, determinism, and doctest tests
- [11-docs-and-contributor-workflow.md](specs/11-docs-and-contributor-workflow.md) - Documentation, CI, contributor process

## Development Workflow

Before implementing significant work, follow this process:

1. **Propose** - Create a proposal file in `openspec/proposals/` describing the change (dated, `YYYY-MM-DD-name.md`). Reference which specs it modifies.
2. **Review** - Verify the proposal is consistent with existing specs; consolidate overlapping issues into the proposal rather than implementing each one independently.
3. **Apply** - Implement the change against the current codebase.
4. **Verify** - Confirm the implementation matches the proposal; run `pytest`, `black`, `flake8`.
5. **Sync** - Update the relevant spec(s) to reflect the new state (move status markers to `[IMPLEMENTED]`). Move the proposal to `openspec/archive/`.

## Status Legend

Specs use these markers to distinguish implementation states:

- **[IMPLEMENTED]** - working in the current codebase
- **[MOCK]** - present in UI but uses simplified client-side approximations
- **[PLANNED]** - documented intent, not yet started
- **[DRAFT]** - proposal or spec under development

A spec may carry more than one marker (e.g. `[IMPLEMENTED]` core with a `[PLANNED]` extension); the head of the file states the mix.

## Related Documentation

Outside the OpenSpec tree, the repository keeps human-facing docs:

- `documentation/` - Sphinx docs, Jupyter notebooks, issue notes (`documentation/issues/`), TODO notes (`documentation/todos/`)
- `README.md` - installation and usage