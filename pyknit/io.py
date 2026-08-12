# Copyright (C) 2026 Terri Oda
# SPDX-License-Identifier: GPL-2.0-or-later

#!python
"""
pyKnit: a set of tools for knitters to do math, create charts, customise
patterns and more

pyknit.io: import and export patterns to CSV and JSON
"""

import csv
import json
import os
from io import StringIO
from typing import List, Optional

from pyknit.Chart import (
    Legend,
    Pattern,
    Stitch,
    stitch_legend,
    stitch_legend_japanese,
)


def _reverse_legend(legend: Legend) -> List:
    """Return (Stitch, code) pairs so a Stitch can be mapped back to its code."""
    return [(stitch, code) for code, stitch in legend.items()]


def _find_code(stitch: Stitch, reverse: List) -> Optional[str]:
    """Look up the code for a Stitch by comparing against legend values."""
    for legend_stitch, code in reverse:
        if stitch == legend_stitch:
            return code
    return None


def _fallback_code(stitch: Stitch) -> str:
    """Best-effort code for a Stitch that has no entry in the legend."""
    if os.path.splitext(stitch.symbol)[1].lower() in {".gif", ".jpg", ".png"}:
        return stitch.instruction
    return stitch.symbol


def _legend_name(legend: Legend) -> str:
    """Human-readable name for a legend, used when exporting JSON."""
    if legend is stitch_legend:
        return "default"
    if legend is stitch_legend_japanese:
        return "japanese"
    return "custom"


def pattern_to_csv(pattern: Pattern, legend: Optional[Legend] = None) -> str:
    """Export a Pattern to a CSV string, one row per pattern row.

    Stitches are mapped back to their legend codes; stitches not in the
    legend fall back to their symbol (or instruction for image symbols).
    """
    if legend is None:
        legend = stitch_legend
    reverse = _reverse_legend(legend)
    rows = []
    for row in pattern:
        codes = []
        for stitch in row:
            code = _find_code(stitch, reverse)
            codes.append(code if code is not None else _fallback_code(stitch))
        rows.append(",".join(codes))
    return "\n".join(rows)


def csv_to_pattern(csv_string: str, legend: Optional[Legend] = None) -> Pattern:
    """Parse a CSV string into a Pattern, resolving codes via the legend.

    Raises KeyError if any cell is not present in the legend.
    """
    if legend is None:
        legend = stitch_legend
    pattern = []
    for row in csv.reader(StringIO(csv_string)):
        pattern.append([legend[cell.strip()] for cell in row])
    return pattern


def pattern_to_json(
    pattern: Pattern,
    legend: Optional[Legend] = None,
    metadata: Optional[dict] = None,
) -> str:
    """Export a Pattern to a JSON string with schema_version 1.

    Keys are written in a fixed, canonical order: schema_version, legend,
    rows, then metadata. Any stitch not found in the legend falls back to
    its symbol (or instruction for image symbols).
    """
    if legend is None:
        legend = stitch_legend
    reverse = _reverse_legend(legend)
    rows = []
    for row in pattern:
        stitch_codes = []
        for stitch in row:
            code = _find_code(stitch, reverse)
            stitch_codes.append(code if code is not None else _fallback_code(stitch))
        rows.append(stitch_codes)
    payload = {
        "schema_version": 1,
        "legend": _legend_name(legend),
        "rows": rows,
    }
    if metadata is not None:
        payload["metadata"] = metadata
    return json.dumps(payload)


def json_to_pattern(
    json_string: str, legend: Optional[Legend] = None
) -> Pattern:
    """Parse a JSON string into a Pattern, resolving codes via the legend.

    Rejects JSON without a schema_version field or with an unsupported
    schema_version with a clear ValueError. Raises KeyError if any cell is
    not present in the legend.
    """
    if legend is None:
        legend = stitch_legend
    try:
        data = json.loads(json_string)
    except json.JSONDecodeError as exc:
        raise ValueError("Could not parse pattern JSON") from exc
    if not isinstance(data, dict) or "schema_version" not in data:
        raise ValueError("Pattern JSON must contain a 'schema_version' field")
    version = data["schema_version"]
    if version != 1:
        raise ValueError(
            f"Unsupported schema_version {version}; expected schema_version 1"
        )
    pattern = [[legend[cell] for cell in row] for row in data["rows"]]
    return pattern


def pattern_to_instructions(
    pattern: Pattern, legend: Optional[Legend] = None
) -> str:
    """Convert a Pattern into written instructions, one row per pattern row.

    Consecutive identical stitches are grouped with a count, e.g. "k2, p1".
    """
    if legend is None:
        legend = stitch_legend
    reverse = _reverse_legend(legend)
    lines = []
    for row in pattern:
        runs = []
        for stitch in row:
            code = _find_code(stitch, reverse)
            code = code if code is not None else _fallback_code(stitch)
            if runs and runs[-1][0] == code:
                runs[-1][1] += 1
            else:
                runs.append([code, 1])
        lines.append(
            ", ".join(
                f"{code}{count}" if count > 1 else code for code, count in runs
            )
        )
    return "\n".join(lines)