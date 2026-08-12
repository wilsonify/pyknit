# Copyright (C) 2021 Terri Oda
# SPDX-License-Identifier: GPL-2.0-or-later

#!python
"""
pyKnit: a set of tools for knitters to do math, create charts, customise
patterns and more

pyKnit.estimate: Rough estimates of yarn usage and knitting time.
"""

from datetime import timedelta


def estimate_knitting_time(total_stitches: int, seconds_per_stitch: float) -> timedelta:
    """
    Return a rough estimate of how long it takes to knit total_stitches.

    This is a rough estimate (total_stitches * seconds_per_stitch). It
    excludes consulting the pattern, learning techniques, and ripping out
    mistakes, so treat it as a ballpark figure, not a prediction.
    """
    if total_stitches <= 0:
        raise ValueError("total_stitches must be positive")
    if seconds_per_stitch <= 0:
        raise ValueError("seconds_per_stitch must be positive")
    return timedelta(seconds=int(total_stitches * seconds_per_stitch))


def format_knitting_time(delta: timedelta) -> str:
    """Format a timedelta as a human-readable string, e.g. "8 hours 20 minutes"."""
    total_seconds = int(delta.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    parts: list = []
    if hours:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    if seconds:
        parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")
    return " ".join(parts) if parts else "0 seconds"
