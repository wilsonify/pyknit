# Shaping

**Status:** [IMPLEMENTED] - `increase_evenly`, `decrease_evenly` (round + flat), `sleeve_decreases`, and `raglan_increases` work. `padding_mode`, automatic remainder handling, and DRY refactor are [PLANNED].

## Purpose

Turn "I need to add/remove N stitches over M rows" into evenly-spaced written instructions. This is the arithmetic heart of pyKnit: every garment component (spec 07) and measurement (spec 05) funnels through these generators, and their output must parse back cleanly (spec 02).

## Functions

### increase_evenly(starting_count, increase_number, in_the_round=False) -> str

Spacing = `floor(starting_count / (increase_number + 1))` for flat (keeps selvage, no increases at row ends) or `floor(starting_count / increase_number)` in the round. A remainder is split into a second interval and emitted with bracket-repeat notation.

| Case                                  | Inputs                  | Output                              |
| ------------------------------------- | ----------------------- | ----------------------------------- |
| flat, no remainder                    | 11, 3, False            | `k2, m1, [k3, m1] * 2 times, k3`    |
| round, no remainder                   | 20, 5, True             | `[k4, m1] * 5 times`                |
| round with remainder                  | 21, 5, True             | `[k4, m1] * 4 times, k5, m1`        |
| flat remainder (selvage-aware)        | 10, 7, False            | `[k1, m1] * 6 times, k2, m1, k2`    |

Validation: `increase_number > starting_count` raises `ValueError`.

### decrease_evenly(starting_count, decrease_number, in_the_round=False) -> str

Dispatches to `decrease_evenly_round` (circular rows) or `decrease_evenly_flat` (with selvage). Balances two interval sizes across the row so the decrease count lands exactly.

| Case                                  | Inputs                  | Output                              |
| ------------------------------------- | ----------------------- | ----------------------------------- |
| round                                  | 11, 3, True             | `k2, k2tog, k1, k2tog, k2, k2tog`  |
| flat                                   | 11, 3, False            | `k1, k2tog, k2, k2tog, k2, k2tog`  |
| round, divisible                       | 20, 5, True             | `[k2, k2tog] * 5 times`             |

Validation: `starting_count < 2`, `decrease_number < 2`, and `decrease_number > starting_count / 2` all raise `ValueError` with descriptive messages (issues #4, #9).

### sleeve_decreases(number_of_rows, starting_count, ending_count, decrease_per_row=2) -> str

Distributes `(starting_count - ending_count) / decrease_per_row` decrease rows evenly across `number_of_rows`:

| Inputs                                    | Output                                                                 |
| ----------------------------------------- | ---------------------------------------------------------------------- |
| 61, 59, 43, 2                             | `[decrease row, do 7 rows in pattern] * 5 times, [decrease row, do 6 rows in pattern] * 3 times` |

Behavior today: interval = `floor((rows - decrease_rows) / decrease_rows)`; remainder pads the early repeats (padding-after). If the decrease doesn't divide evenly, a warning is logged and the closest alternative printed - the plan (TODO) is to compute and place the remainder decreases automatically and to support `padding_mode` in `'before' | 'after' | 'both' | 'none'` with `'after'` as the backward-compatible default.

### raglan_increases(neck, arm, bust, neck_to_bust_rows, increase_per_increase_row=8, armpit_stitches=4) -> str

Marker-setup instructions plus an adjustment increase row when the computed neck count differs from the actual one. Known FIXME: the `calculated_neck < neck_stitches` branch has a placeholder value and the non-increase-row spacing is unimplemented.

## Shared Spacing Core (planned)

`decrease_evenly` and `sleeve_decreases` duplicate the "divide total, distribute remainder" logic (a code TODO). Plan: extract `_calculate_spacing(total, count, padding_mode)` used by both; each function keeps its own output wording (stitch codes vs. "decrease row"). Output strings for existing inputs must remain byte-identical.

## Output Format Contract

Generated strings always use bracket-repeat notation (`[k3, m1] * 4 times`), `m1` / `k2tog` for increases/decreases, and avoid repeats for single occurrences (`k2, m1` without brackets). The parser (spec 02) reads this notation back; round-trip counts are tested in spec 10.

## Ownership

| Value                       | Owner                              |
| --------------------------- | ---------------------------------- |
| Increase/decrease spacing   | `pyknit/__init__.py`               |
| Sleeve + raglan             | `pyknit/__init__.py`               |
| Shared spacing core         | spec 06 [PLANNED]                  |
| Remainder automation / padding | spec 06 [PLANNED]              |

## Workflow Integration

Receives budgets from gauge conversions (spec 05) and components (spec 07). Emits instruction strings that feeding the parser (spec 02) yields chartable `Pattern`s.

## Testing

- `test_increase_evenly` (6 parametrized cases) and `test_increase_evenly_error` (6 cases).
- `test_decrease_evenly` (8 cases) and `test_decrease_evenly_error` (4 cases).
- Sleeve fixture: 61 rows / 59 -> 43 / per-row 2 produces the documented 5+3 repeat string.
- Planned: count-execution checks (increase 10->13, decrease 20->15, sleeve 59->43), `padding_mode` matrix, remainder placement, raglan `calculated_neck < neck_stitches` branch.