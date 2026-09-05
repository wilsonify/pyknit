# Instruction Parsing

**Status:** [PLANNED] - basic single-row parsing is [IMPLEMENTED]; repeat expansion, round-trip of generated instructions, and chart-to-instruction output are [PLANNED].

## Purpose

Resolve a written instruction string (`"k1 p4 k kfb yo ssk"`, `"[k2, p2] * 6 times"`) into an ordered array of `Stitch` objects - the bridge between human-readable patterns and chartable data. Also the receiving side of the round-trip: shaping functions (spec 06) generate instruction strings that the parser must be able to read back.

## Inputs

| Input             | Notes                                                        |
| ----------------- | ------------------------------------------------------------ |
| `row`             | one instruction row, tokens separated by space and/or comma  |
| `legend`          | `stitch_legend`, `stitch_legend_japanese`, or a custom dict  |

## Grammar

```
instruction_row    := instruction (separator instruction)*
instruction        := stitch_sequence | repeat_block | cable_sequence
stitch_sequence    := stitch_code [count]
repeat_block       := "[" instruction ("," instruction)* "]" "*" count "times"
cable_sequence     := cable_code [count]
stitch_code        := [A-Za-z]+ [0-9]* [A-Za-z]*
cable_code         := "C" [0-9]+ "-" [0-9]+ [A-Za-z]*
count              := [0-9]+
separator          := "," | " "
```

Match order matters: cable pattern first (`C2-1L`, including the `P?[FBLR]` variant), then compound codes (`k2tog`, `m1l` - letters-digits-letters), then simple codes (`p4`, `k`). This prevents `k2tog` from being misread as `k2` + `tog`. A count defaults to 1.

## Repeats (planned)

Shaping output uses bracketed repeats - `"[k3, m1] * 4 times"` (increase_evenly), `"[decrease row, do 7 rows in pattern] * 5 times"` (sleeve_decreases), `"[k2, k2tog] * 5 times"` (decrease_evenly). The parser SHALL:

1. Expand `[items] * N times` inline (first pass, string preprocessing),
2. Run the existing token regexes on the expanded form (second pass).

This is intentionally backward-compatible: inputs without repeats behave exactly as today. Issue #5 (parse the output of `sleeve_decrease`) is the acceptance driver.

## Pattern Model

A parsed multi-line chart becomes a 2D structure:

```
Pattern     := List[PatternRow]
PatternRow  := List[Stitch]
repeat info := optional(start_row, end_row, repeat_count)   # planned
```

Direction semantics for flat knitting: odd rows right-side, even rows wrong-side (charting reads WS rows right-to-left; spec 03).

## Round-Trip Contract

- Shaping output (spec 06) parses back to a Pattern whose row stitch counts are correct.
- Executing increases/decreases yields the documented final stitch count (see spec 06 validation).
- Write-instructions -> chart and chart -> written-instructions (issue #13, spec 04) both pass through this parser.

## Ownership

| Value                | Owner                                  |
| -------------------- | -------------------------------------- |
| Row/pattern parsing  | `pyknit/Chart.py` (`parse_row`, `parse_chart`) |
| Repeat expansion     | spec 02 [PLANNED]                      |
| Written-instructions from charts | spec 04 [PLANNED]        |

## Workflow Integration

Receives instruction strings from shaping (spec 06) and export/import (spec 04); produces `Pattern` consumed by chart rendering (spec 03). Nothing outside this module decides what a token means.

## Testing

- `test_parse_row`: `"k1 p4 k1 p4 k kfb yo ssk k2tog"` -> 15-element array against `stitch_legend`.
- Unknown code raises `KeyError`.
- Cables match before compounds: `k2tog` is one stitch, not `k2`.
- Planned repeat cases: `"[k2, p2] * 6 times"` -> 24 stitches in order; `"[k2tog, k3] * 5 times"` -> 25 stitches; single-instruction braces expand without brackets.
- Planned round-trip: `parse_row(increase_evenly(...))` and `parse_row(sleeve_decreases(...))` produce correct counts.