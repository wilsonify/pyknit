# Copyright (C) 2026 Terri Oda
# SPDX-License-Identifier: GPL-2.0-or-later

"""Tests for pyknit.io CSV/JSON pattern import and export."""

import json

import pytest

from pyknit import io
from pyknit.Chart import (
    parse_chart,
    stitch_legend,
    stitch_legend_japanese,
)


def test_csv_round_trip_default_legend():
    """CSV export -> import reproduces a mult-row pattern exactly."""
    pattern = parse_chart("k p k\nkfb yo k2tog\nssk C2-1L k", stitch_legend)
    csv_string = io.pattern_to_csv(pattern, stitch_legend)
    assert io.csv_to_pattern(csv_string, stitch_legend) == pattern


def test_csv_round_trip_japanese_legend():
    """CSV round-trip works with the Japanese legend."""
    pattern = parse_chart("k p ktbl\nyo k2tog ptbl", stitch_legend_japanese)
    csv_string = io.pattern_to_csv(pattern, stitch_legend_japanese)
    assert io.csv_to_pattern(csv_string, stitch_legend_japanese) == pattern


def test_csv_unknown_code_raises_keyerror():
    """A code missing from the legend raises KeyError on import."""
    with pytest.raises(KeyError):
        io.csv_to_pattern("k,r\n", stitch_legend)


def test_json_round_trip_with_metadata():
    """JSON export -> import reproduces the pattern and carries metadata."""
    pattern = parse_chart("k p k\nkfb yo k2tog", stitch_legend)
    metadata = {
        "name": "seed stitch",
        "gauge": {
            "row_count": 18,
            "row_measure": 3.25,
            "stitch_count": 24,
            "stitch_measure": 4,
            "units": "in",
        },
    }
    json_string = io.pattern_to_json(pattern, stitch_legend, metadata=metadata)
    assert io.json_to_pattern(json_string, stitch_legend) == pattern
    payload = json.loads(json_string)
    assert payload["metadata"] == metadata


def test_json_unknown_schema_version_rejected():
    """Unknown schema_version must be rejected with a clear error."""
    bad_json = json.dumps({"schema_version": 2, "legend": "default", "rows": [["k"]]})
    with pytest.raises(ValueError, match="schema_version"):
        io.json_to_pattern(bad_json, stitch_legend)


def test_json_missing_schema_version_rejected():
    """JSON without schema_version must be rejected."""
    bad_json = json.dumps({"rows": [["k"]]})
    with pytest.raises(ValueError, match="schema_version"):
        io.json_to_pattern(bad_json, stitch_legend)


def test_exports_are_deterministic():
    """Two exports of the same pattern are byte-identical."""
    pattern = parse_chart("k p k\nkfb yo k2tog", stitch_legend)
    csv1 = io.pattern_to_csv(pattern, stitch_legend)
    csv2 = io.pattern_to_csv(pattern, stitch_legend)
    assert csv1 == csv2
    json1 = io.pattern_to_json(pattern, stitch_legend)
    json2 = io.pattern_to_json(pattern, stitch_legend)
    assert json1 == json2


def test_json_canonical_key_order():
    """JSON keys appear in canonical order: schema_version, legend, rows."""
    pattern = parse_chart("k", stitch_legend)
    payload = json.loads(io.pattern_to_json(pattern, stitch_legend))
    assert list(payload.keys()) == ["schema_version", "legend", "rows"]
    assert io.pattern_to_json(pattern, stitch_legend).startswith('{"schema_version": 1,')


def test_json_canonical_key_order_with_metadata():
    """metadata is the last key when present."""
    pattern = parse_chart("k", stitch_legend)
    payload = json.loads(io.pattern_to_json(pattern, stitch_legend, metadata={"name": "x"}))
    assert list(payload.keys()) == [
        "schema_version",
        "legend",
        "rows",
        "metadata",
    ]


def test_stitch_codes_round_trip():
    """Specific stitch codes (k2tog, cable C2-1L) survive export."""
    pattern = parse_chart("k2tog p ssk\nC2-1L C2-1R yo", stitch_legend)
    csv_string = io.pattern_to_csv(pattern, stitch_legend)
    assert "k2tog" in csv_string
    assert "C2-1L" in csv_string
    assert io.csv_to_pattern(csv_string, stitch_legend) == pattern


def test_pattern_to_instructions():
    """Pattern becomes written instructions with counts."""
    pattern = parse_chart("k k p p p", stitch_legend)
    assert io.pattern_to_instructions(pattern, stitch_legend) == "k2, p3"
