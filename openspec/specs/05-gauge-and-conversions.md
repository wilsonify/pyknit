# Gauge and Conversions

**Status:** [IMPLEMENTED] - `GaugeSwatch` (pydantic), conversions, and cross-gauge conversion work with validation. Yardage/weight fields are [PLANNED] (spec 08).

## Purpose

Own the relationship between stitch/row counts and physical measurement, so every other module (shaping, components, estimation) converts through one place. A gauge swatch is the single source of truth for "how many stitches per inch / cm".

## GaugeSwatch Model

Pydantic `BaseModel` - validation lives in the constructor, not scattered checks:

| Field           | Type                       | Notes                          |
| --------------- | -------------------------- | ------------------------------ |
| `row_count`     | PositiveFloat              | rows in the swatch             |
| `row_measure`   | PositiveFloat              | height the rows spanned        |
| `stitch_count`  | PositiveFloat              | stitches in the swatch         |
| `stitch_measure`| PositiveFloat              | width the stitches spanned     |
| `units`         | Literal["cm", "in"]        | consistent unit for all values |

Planned fields (spec 08): `yardage_per_unit`, `weight_per_unit` for yarn estimation.

## Conversions

| Method                            | Math                  | Notes                                  |
| --------------------------------- | --------------------- | -------------------------------------- |
| `row_gauge()`                     | rows / measure        | rows per unit                          |
| `stitch_gauge()`                  | stitches / measure    | stitches per unit                      |
| `measurement_to_stitches(m)`      | round(m x stitch_gauge) | measurement -> stitch count          |
| `measurement_to_rows(m)`          | round(m x row_gauge)  | measurement -> row count               |
| `rows_to_measurement(n)`          | n / row_gauge         | row count -> length                    |
| `stitches_to_measurement(n)`      | n / stitch_gauge      | stitch count -> width                  |

All four round-trip conversions take `PositiveFloat` / `PositiveInt` and round to whole stitch/row counts via pydantic validation.

## Cross-Gauge Conversion

Convert a pattern measurement into "what it becomes at my gauge":

```
convert_stitch_measure(m, oldGauge, newGauge)  = new.stitches_to_measurement(old.measurement_to_stitches(m))
convert_row_measure(m, oldGauge, newGauge)     = new.rows_to_measurement(old.measurement_to_rows(m))
```

Contract: one owner per value - conversions never write back to either swatch.

## Validation Rules

1. Any measurement of `0` is rejected at construction (`PositiveFloat`). This closes issue #8 (nonsensical swatches give bad math).
2. Negative or zero counts rejected by `PositiveInt` / `PositiveFloat`.
3. Units are restricted to `cm` / `in` by `Literal`; converting across units requires an explicit unit step (CLI currently has a documented FIXME for cm<->in - spec 09).

## Ownership

| Value                  | Owner                                  |
| ---------------------- | -------------------------------------- |
| Gauge model + methods  | `pyknit/GaugeSwatch.py` (`GaugeSwatch`) |
| Cross-gauge conversion | `pyknit/GaugeSwatch.py` (`convert_stitch_measure`, `convert_row_measure`) |
| Yardage/weight fields  | spec 08 [PLANNED]                      |

## Workflow Integration

Read by shaping (spec 06) to turn a desired measurement into a row/stitch budget, by components (spec 07) for gauge customization, and by estimation (spec 08). CLI gauge conversion (`pyknit --convert row|stitch`) constructs `GaugeSwatch` instances and calls these methods.

## Testing

- `test_GaugeSwatch.py`: construction, `row_gauge`, `stitch_gauge`, and all four round-trip conversions against `GaugeSwatch(row_count=18, row_measure=3.25, stitch_count=24, stitch_measure=4, units="in")`:
  - `measurement_to_stitches(5) == 30`, `measurement_to_rows(11) == 61`, `stitches_to_measurement(18) == 3`, `rows_to_measurement(10) == 10/(18/3.25)`.
- Zero measurement construction raises a pydantic ValidationError.
- Cross-gauge: a 40-inch pattern piece at pattern gauge 6 st/in = 240 st; at my gauge 5 st/in that knits to 48 in (`convert_stitch_measure(40, pattern_6spi, mine_5spi) == 48`).
- Planned: cm/in unit conversion helper with explicit rounding.