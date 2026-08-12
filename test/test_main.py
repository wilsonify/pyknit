# Copyright (C) 2021 Terri Oda
# SPDX-License-Identifier: GPL-2.0-or-later

"""CLI and module import smoke tests (openspec spec 09)."""

import importlib
import sys

import pytest

from pyknit import VERSION
from pyknit import __main__


def test_main_convert_row(capsys, caplog, monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "pyknit",
            "--convert",
            "row",
            "-ogr",
            "5",
            "-ngr",
            "4",
            "--original-measurement",
            "10",
        ],
    )
    __main__.main()
    out, err = capsys.readouterr()
    # 10in at 5 rows/in -> 50 rows -> 50 / (4 rows/in) = 12.5in
    assert "Converting row gauge..." in caplog.text
    assert "My calculated measurement: 12.5 in" in caplog.text
    assert VERSION in out


def test_main_convert_stitch(capsys, caplog, monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "pyknit",
            "--convert",
            "stitch",
            "-ogs",
            "27.5",
            "-ngs",
            "23.5",
            "--original-measurement",
            "42",
        ],
    )
    __main__.main()
    out, err = capsys.readouterr()
    # 42in at 27.5 sts/in -> 1155 sts -> 1155 / (23.5 sts/in) = 49.1489...in
    assert "Converting stitch gauge..." in caplog.text
    assert f"My calculated measurement: {round(42 * 27.5) / 23.5} in" in caplog.text
    assert VERSION in out


def test_main_without_convert_prints_usage_exits(capsys, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["pyknit"])
    with pytest.raises(SystemExit):
        __main__.main()
    out, err = capsys.readouterr()
    assert "usage:" in out
    assert VERSION in out


@pytest.mark.parametrize(
    "module",
    [
        "pyknit",
        "pyknit.Chart",
        "pyknit.GaugeSwatch",
        "pyknit.Hat",
        "pyknit.Sock",
        "pyknit.Stitches",
        "pyknit.pi_shawl",
    ],
)
def test_modules_importable(module):
    importlib.import_module(module)
