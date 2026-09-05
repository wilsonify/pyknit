# Documentation and Contributor Workflow

**Status:** [IMPLEMENTED] - Sphinx docs, notebooks, pre-commit, and CI exist. Doctest-driven documentation coverage is [PLANNED] (issue #19).

## Purpose

Make pyKnit discoverable and pleasant to contribute to: readable docs with working examples, automated quality checks, and a documented contributor path from issue to merged PR.

## Documentation Inventory

| Doc               | Location                          | Notes                                          |
| ----------------- | --------------------------------- | ---------------------------------------------- |
| README            | `README.md`                       | install, Jupyter setup, usage, contributing    |
| Sphinx docs       | `documentation/`                  | myst-parser Markdown, alabaster theme, builds to readthedocs |
| Example notebooks | `documentation/*.ipynb`           | SweaterFit, SleeveDecreases, TriangleHat, CowlCable, Japanese_Chart |
| Issue notes       | `documentation/issues/issue-###.md` | one file per GitHub issue: status, description, branch |
| TODO notes        | `documentation/todos/`            | one file per code TODO: file+line, status      |
| Presentation      | `documentation/pycon2021-presentation.rst` | PyCon 2021 slides |

### Requirements

- Every feature change updates the relevant docs and, where behavior is user-facing, an example notebook cell.
- API reference is auto-generated from docstrings (Sphinx autodoc - configure; `conf.py` currently enables only `myst_parser`).
- Issue notes and TODO notes stay in sync with the issue tracker and code - the docs are the index, not a duplicate source of truth.
- Doctests (spec 10) keep every docstring example executable.

## Contributor Workflow

1. **Find work** - open issues (13 at time of writing) and `documentation/todos/`; each issue doc names its branch (`issue-###`).
2. **Set up** - `pip install -r requirements.txt`, install pre-commit (`pre-commit install`), `pip install -e .` for editable install.
3. **Change** - small, focused commits; SPDX header on new files; black formatting.
4. **Verify** - `pytest`, `black --check`, `flake8` locally; CI re-runs them on the PR.
5. **Review & merge** - maintainer review; CI must pass (tests 3.9/3.10/3.11, docs build, security scan).

### Automated Checks

- **pre-commit:** black + flake8 on commit (`.pre-commit-config.yaml`).
- **CI (`.github/workflows/`):** `python-package.yml` (pytest + docs), `black.yml` (format check), `cve-bin-tool.yml` (dependency security).
- Doctests join CI once configured (spec 10 [PLANNED]).

## Ownership

| Value                    | Owner                                        |
| ------------------------ | -------------------------------------------- |
| README + Sphinx + notebooks | maintainers, updated per change           |
| Issue/TODO notes         | contributors, one file per issue/TODO        |
| CI + pre-commit          | `.github/workflows/`, `.pre-commit-config.yaml` |

## Workflow Integration

The OpenSpec process (see README at the openspec root) wraps this: a proposal in `openspec/proposals/` precedes significant work; specs are updated to `[IMPLEMENTED]` and the proposal archived when the work merges.

## Testing

- CI docs job builds `documentation/` with `make html` (existing `python-package.yml` docs job) - a broken docs build blocks merges.
- Doctest CI (planned) fails on any docstring example that no longer matches output.
- Pre-commit hooks block commits that black/flake8 reject.