# Garment Components

**Status:** [IMPLEMENTED] (partial) - Hat crown and Pi shawl work; Sock is [DRAFT]; shawl shapes and further components are [PLANNED].

## Purpose

Reusable geometry generators that turn "a hat that fits / a sock / a pi shawl / a shawl shape" into shaping instructions (spec 06) customized by gauge (spec 05). The approach is functional, not an OOP hierarchy: generator functions returning instruction lists, sharing the spacing core.

## Component Index

| Component        | Status     | Notes                                                     |
| ---------------- | ---------- | --------------------------------------------------------- |
| Hat crown        | [IMPLEMENTED] | `Hat.crown_decreases(repeats, stitches)`; errors on non-even division (remainder handling [PLANNED]) |
| Sock             | [DRAFT]    | `Sock` class partially implemented; has known bugs        |
| Pi shawl         | [IMPLEMENTED] | `pi_shawl.py`; increase rows + total rounds               |
| Half-pi shawl    | [PLANNED]  | flat (back-and-forth) variant of the pi shawl             |
| Shawl shapes     | [PLANNED]  | square, rectangle, biased rectangle, triangle, elongated triangle, asymmetrical triangle, crescent |
| Raglan yoke      | [PLANNED]  | complete the `raglan_increases` FIXME (spec 06)           |
| Sock toe / heel  | [PLANNED]  | dedicated toe and heel generators (issue #11)             |
| Pockets          | [PLANNED]  | opening + lining instructions                             |

## Hat Crown

```
Hat.crown_decreases(repeats, stitches)
```

Works in rounds: each round removes `repeats` stitches, interleaved with plain knit rounds, until fewer than `repeats` stitches remain; finishes with a bind-off note. TODO (issue) instead of erroring on `stitches % repeats != 0`, add extra decreases to absorb the remainder.

## Pi Shawl

A pi shawl doubles its stitch count at geometrically spaced intervals - increase rounds land where the radius has doubled.

```
total_rounds_for_pi_shawl(desired_radius, round_gauge)  -> round(desired_radius * round_gauge)
pi_shawl_increase_rows(desired_radius, round_gauge)     -> [round numbers to double stitches]
```

The gap between increase rounds doubles each time (first increase on round 2, then round 6, 13, 26, ...). Half-pi (flat, back-and-forth) halves the frequency per the same rule.

| Inputs             | total rounds | increase rows        |
| ------------------ | ------------ | -------------------- |
| radius 5, gauge 5  | 25           | [2, 6, 13]           |
| radius 50, gauge 3 | 150          | [2, 6, 13, 26, 51, 100] |

## Sock (status [DRAFT])

`Sock` models a cuff-down sock from gauge, circumferences, and lengths, computing cast-on, ankle stitches, heel flap, and toe decrease geometry. Known defects to fix before use:

- `get_length_from_heel_to_beginning_of_toe_decrease` reads `self.length_from_heel_to_toe_end`, which is never set (`AttributeError`).
- `get_number_of_decrease_rows` calls `round_up_even` unqualified (missing `self.`).
- `get_length_of_toe_decrease` and `get_number_of_decrease_rows` are never called from `init()`.

## Generator API (planned)

```
generate_sock_toe(toe_stitches, gauge) -> List[str]
generate_sock_heel(heel_stitches, gauge) -> List[str]
generate_hat_crown(stitches, repeats, gauge) -> List[str]   # replace Hat method
generate_shawl(shape, dimensions, gauge) -> List[str]
```

Each accepts gauge so stitch budgets derive from measurements (spec 05) and reuses the spacing core (spec 06).

## Ownership

| Value              | Owner                           |
| ------------------ | ------------------------------- |
| Hat crown          | `pyknit/Hat.py`                 |
| Sock               | `pyknit/Sock.py`                |
| Pi shawl math      | `pyknit/pi_shawl.py`            |
| Shape generators   | spec 07 [PLANNED]               |
| Half-pi shawl      | spec 07 [PLANNED]               |

## Workflow Integration

Consumes gauge (spec 05) and spacing (spec 06); produces instruction strings that parse (spec 02) into chartable `Pattern`s (spec 03).

## Testing

- `test_pi_shawl.py`: `(5, 5) -> [2, 6, 13]`, `(50, 3) -> [2, 6, 13, 26, 51, 100]`; total-rounds math.
- Hat crown: even-division sequence ends with the bind-off note; remainder case currently returns an error message (planned: no error, extra decreases distributed).
- Sock: round-trips `init()` without exception once bugs are fixed; cast-on/ankle/heel values match the documented formulas.
- Planned: shape generators produce stitch-count-correct instruction lists for each shape; half-pi matches pi at half frequency.