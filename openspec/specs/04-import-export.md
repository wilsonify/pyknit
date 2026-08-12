# Import / Export

**Status:** [PLANNED] - no interchange capability exists yet. CSV reading was originally requested in issue #13.

## Purpose

Let a pattern leave pyKnit as a file and come back losslessly: charts encoded as grids, plus structured pattern data (metadata, repeats, legend) when needed. Two formats cover both shapes - CSV for the grid itself, JSON for a full structured pattern.

## Inputs

| Function (planned)        | Inputs                                        | Returns      |
| ------------------------- | --------------------------------------------- | ------------ |
| `pattern_to_csv(pattern)` | `Pattern`                                     | CSV string   |
| `csv_to_pattern(csv, legend)` | CSV string, legend                        | `Pattern`    |
| `pattern_to_json(pattern)` | `Pattern` + optional metadata                 | JSON string  |
| `json_to_pattern(json)`   | JSON string, legend                           | `Pattern`    |

## CSV Format

One row per pattern row; stitch codes separated by commas. Cells hold codes (`k`, `p`, `k2tog`), never symbols, so the legend resolves them on import.

```
k,p,k,p
k,kfb,yo,k
```

Design notes:

- A typical CSV export from spreadsheet software won't carry color or symbol style; codes + legend reproduce the chart correctly (this matches issue #13's "start with symbols" scope).
- Round-trip contract: export -> import yields a `Pattern` equivalent to the original (Stitch-defined equality, spec 01).

## JSON Format (planned)

Full structured form carrying metadata and provenance:

```json
{
  "schema_version": 1,
  "legend": "default",
  "rows": [["k", "p", "k"], ["k", "kfb", "yo"]],
  "metadata": {
    "name": "seed stitch",
    "repeat": {"start_row": 1, "end_row": 2, "repeat_count": null},
    "gauge": {"row_count": 18, "row_measure": 3.25, "stitch_count": 24, "stitch_measure": 4, "units": "in"}
  }
}
```

Rules:

- `schema_version` is always present and read first; unknown versions are rejected with a plain-language error, leaving current state unchanged.
- Typed numbers carry explicit units - never strings like `"3.25in"`.
- On import, each owner reassigns its own fields; no module re-derives another's (spec 09).

## Ownership

| Value                    | Owner                     |
| ------------------------ | ------------------------- |
| CSV/JSON schema & codecs | spec 04 (`pyknit/io/`)    |
| Value serialization      | owners of each value (spec 09) |
| Round-trip guarantees    | spec 04 + spec 10         |

## Workflow Integration

Import produces `Pattern` for charting (spec 03); export consumes `Pattern`. Chart-to-written-instructions (issue #13's second half) uses the parser (spec 02) in reverse and is scoped here as a later step.

## Testing

- Round-trip: export -> import yields an equal `Pattern` for CSV and JSON.
- Code resolution: import against a specified legend (default and Japanese) resolves every cell; unknown codes raise `KeyError`.
- Determinism: same pattern state always exports identical bytes (stable field order).
- JSON: unknown `schema_version` rejected without state change; typed units survive round-trip.