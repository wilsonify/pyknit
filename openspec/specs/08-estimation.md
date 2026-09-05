# Estimation

**Status:** [PLANNED] - nothing implemented. Requested via issue #50 (knitting time) and a code TODO (yardage/weight).

## Purpose

Optional, honest estimates from numbers already computed elsewhere: yarn needed for a project and roughly how long it will take to knit. These are estimates, not predictions - no models, no ML, deterministic arithmetic with the limitation stated in the output.

## Yardage and Weight

A `GaugeSwatch` gains optional fields (pydantic):

| Field               | Meaning                                                      |
| ------------------- | ------------------------------------------------------------ |
| `yardage_per_unit`  | yarn length used per stitch (e.g. m/stitch), derived from a swatch + yarn label |
| `weight_per_unit`   | yarn weight used per stitch (e.g. g/stitch)                  |

Methods:

```
estimate_yardage(stitch_count)   -> yardage_per_unit * stitch_count
estimate_weight(stitch_count)    -> weight_per_unit * stitch_count
```

The total stitch count for a project is the sum of stitch counts across its Pattern rows (computed by validation, spec 10) - estimation reads it, never re-derives it.

## Knitting Time (issue #50)

```
estimate_knitting_time(total_stitches, seconds_per_stitch) -> timedelta
```

`X stitches * N seconds` with a docstring and output note: this excludes consulting the pattern, learning techniques, and ripping mistakes. An optional per-stitch-type weighting factor may be added later, defaulting to uniform. The result is a `timedelta` for easy formatting.

## Design Rules

1. Deterministic arithmetic only - no stochastic, no fatigue/experience modeling.
2. Every estimate carries its assumptions (defaulted inputs recorded, spec 04 JSON carries them).
3. Results are labeled "rough estimate" - no false precision (a timedelta to the minute, not the second).

## Ownership

| Value                    | Owner                    |
| ------------------------ | ------------------------ |
| Yardage/weight fields    | `GaugeSwatch` (spec 05)  |
| Time estimate function   | spec 08 (`pyknit/estimate/`) |
| Stitch-count source      | validation (spec 10)     |

## Workflow Integration

Reads stitch counts from patterns and gauge from `GaugeSwatch`; used interactively in Jupyter (spec 09) and, later, in the browser. Optional feature - nothing in the core pipeline depends on it.

## Testing

- `estimate_yardage`/`estimate_weight` scale linearly with stitch count and are deterministic.
- `estimate_knitting_time(6000, 5)` -> `timedelta(seconds=30000)` (8h20m); zero and negative inputs rejected.
- Defaulted fields produce a stated assumption, never silent numbers.
- Fixture with a fixed `GaugeSwatch` reproduces the exact documented totals.