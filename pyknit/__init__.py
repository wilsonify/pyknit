# Copyright (C) 2022 Terri Oda
# SPDX-License-Identifier: GPL-2.0-or-later
"""
pyKnit: a set of tools for knitters to do math, create charts, customise
patterns and more
"""

import logging
import math
from logging.config import dictConfig
from typing import List, Set, Tuple

from pydantic import PositiveInt, validate_arguments

from .Chart import (
    Stitch,
    Legend,
    PatternRow,
    Pattern,
    stitch_legend,
    stitch_legend_japanese,
    parse_row,
    parse_chart,
    print_row,
    instruction_to_plot_order,
    plot_chart,
    render_chart_svg,
)
from .GaugeSwatch import (
    GaugeSwatch,
    stitch_operations,
    stitches_consumed,
    stitches_produced,
    chart_width,
    stitch_count,
    convert_stitch_measure,
    convert_row_measure,
)
from .Hat import Hat
from . import browser

logging_config_dict = {
    "version": 1,
    "formatters": {"simple": {"format": """%(asctime)s | %(filename)s | %(lineno)d | %(levelname)s | %(message)s"""}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "simple"}},
    "root": {"handlers": ["console"], "level": logging.DEBUG},
}

VERSION = "pyKnit 0.1.1"

# Increase and decrease functions

@validate_arguments
def increase_evenly(
    starting_count: PositiveInt, increase_number: PositiveInt, in_the_round: bool = False
) -> str:
    """ A function to figure out even spacing for increases

    >>> increase_evenly(11, 3, False)
    'k2, m1, [k3, m1] * 2 times, k3'
    >>> increase_evenly(20, 5, True)
    '[k4, m1] * 5 times'
    """

    if increase_number > starting_count:
        logging.error(
            f"Error: Increase number ({increase_number}) is bigger than the starting count ({starting_count})")
        raise ValueError

    # Calculate the spacing based on whether we're knitting in the round
    increase_spacing = increase_number if in_the_round else increase_number + 1

    interval = math.floor(starting_count / increase_spacing)
    remainder = starting_count % increase_spacing

    # Build the instruction string
    if increase_spacing - remainder > 1:
        instruction_string = f"[k{interval}, m1] * {increase_spacing - remainder} times"
    else:
        instruction_string = f"k{interval}, m1"

    # Add additional sections based on remainder and knitting mode
    if remainder > 0:
        instruction_string += _build_remainder_instruction(interval, remainder, in_the_round)
    elif not in_the_round:
        # Add selvage for flat knitting
        instruction_string += f", k{interval}"

    return instruction_string


def _build_remainder_instruction(interval: int, remainder: int, in_the_round: bool) -> str:
    """Build instruction string for remainder stitches."""
    if in_the_round:
        # In the round: simpler remainder handling
        if remainder > 1:
            return f", [k{interval + 1}, m1] * {remainder} times"
        else:
            return f", k{interval + 1}, m1"
    else:
        # Flat knitting: more complex remainder handling
        if remainder - 1 > 1:
            return f", [k{interval + 1}, m1] * {remainder - 1} times, k{interval + 1}"
        else:
            return f", k{interval + 1}, m1, k{interval + 1}"


def _calculate_spacing(
    total: int, count: int, padding_mode: str = "after"
) -> List[Tuple[int, int]]:
    """Return a balanced spacing plan splitting ``total`` items into ``count`` groups.

    The plan is a list of ``(interval_size, number_of_groups)`` pairs whose
    order is the emission order.  The remainder ``total % count`` is spread
    one item at a time over groups of the next-larger interval.

    ``padding_mode`` chooses where the larger groups sit in the plan:

    * "after" (default): larger interval groups come first
    * "before": larger interval groups come last
    * "both" / "none": same layout as "after" (layout is a caller concern)

    Zero-count groups are omitted.
    """
    if count <= 0:
        raise ValueError("count must be a positive integer")
    interval = total // count
    remainder = total % count
    entries = [(interval + 1, remainder), (interval, count - remainder)]
    if padding_mode == "before":
        entries.reverse()
    return [(size, groups) for size, groups in entries if groups > 0]


def decrease_evenly_round(starting_count: PositiveInt, decrease_number: PositiveInt) -> str:
    """
    A function to figure out spacing for decreases across a circular round

    >>> decrease_evenly_round(20, 5)
    '[k2, k2tog] * 5 times'
    """
    plan = _calculate_spacing(starting_count, decrease_number)
    
    if len(plan) == 1:
        return _format_single_plan(plan[0])
    else:
        return _format_multi_plan(plan)


def _format_single_plan(plan_entry: Tuple[int, float]) -> str:
    """Format a single spacing plan entry as a decrease pattern."""
    interval, times = plan_entry
    k = interval - 2
    decrease_pattern = f'[k{k:.0f}, k2tog] * {times:.0f}'
    
    # Add singular/plural form
    if times == 1:
        decrease_pattern += ' time'
    else:
        decrease_pattern += ' times'
    
    return decrease_pattern


def _format_multi_plan(plan: List[Tuple[int, float]]) -> str:
    """Format a multi-part spacing plan as a decrease pattern."""
    (small_interval, times), (large_interval, higher_times) = sorted(plan)
    k = small_interval - 2
    k_higher = large_interval - 2
    
    k_string = 'k2tog' if k == 0 else f'k{k:.0f}, k2tog'
    k_higher_string = 'k2tog' if k_higher == 0 else f'k{k_higher:.0f}, k2tog'
    
    if times % 2 == 0:
        return _handle_even_times(times, k_string, higher_times, k_higher_string)
    elif higher_times % 2 == 0:
        return _handle_even_higher_times(times, k_string, higher_times, k_higher_string)
    else:
        return _handle_odd_times(times, k_string, higher_times, k_higher_string)


def _handle_even_times(times: float, k_string: str, higher_times: float, k_higher_string: str) -> str:
    """Handle case where times is even."""
    times = times / 2
    times_string = k_string if times == 1 else f'[{k_string}] * {times:.0f} times'
    higher_times_string = k_higher_string if higher_times == 1 else f'[{k_higher_string}] * {higher_times:.0f} times'
    return f'{times_string}, {higher_times_string}, {times_string}'


def _handle_even_higher_times(times: float, k_string: str, higher_times: float, k_higher_string: str) -> str:
    """Handle case where higher_times is even."""
    higher_times = higher_times / 2
    times_string = k_string if times == 1 else f'[{k_string}] * {times:.0f} times'
    higher_times_string = k_higher_string if higher_times == 1 else f'[{k_higher_string}] * {higher_times:.0f} times'
    return f'{higher_times_string}, {times_string}, {higher_times_string}'


def _handle_odd_times(times: float, k_string: str, higher_times: float, k_higher_string: str) -> str:
    """Handle case where both times and higher_times are odd."""
    higher_times = math.ceil(higher_times / 2)
    times_string = k_string if times == 1 else f'[{k_string}] {times:.0f} times'
    higher_times_string = k_higher_string if higher_times == 1 else f'[{k_higher_string}] {higher_times:.0f} times'
    
    decrease_pattern = f'{higher_times_string}, {times_string}'
    higher_times -= 1
    if higher_times != 0:
        decrease_pattern += ''

    return decrease_pattern


def decrease_evenly_flat(starting_count: PositiveInt, decrease_number: PositiveInt) -> str:
    """
    A function to figure out spacing for decreases across a flat row

    >>> decrease_evenly_flat(20, 5)
    'k1, [k2tog, k2] * 4 times, k2tog, k1'
    """

    plan = _calculate_spacing(starting_count, decrease_number)
    if len(plan) == 1:
        return _format_flat_single_plan(plan[0])
    else:
        return _format_flat_multi_plan(plan)


def _format_flat_single_plan(plan_entry: Tuple[int, float]) -> str:
    """Format a single spacing plan entry for flat knitting decreases."""
    interval, times = plan_entry
    k = interval - 2
    k_first = math.ceil(k / 2)
    k_second = k - k_first
    
    decrease_pattern = ''
    if k_first != 0:
        times = times - 1
        decrease_pattern += f'k{k_first:.0f}, '
    
    if k != 0:
        decrease_pattern += f'[k2tog, k{k:.0f}]'
    else:
        decrease_pattern += '[k2tog] '
    
    if times > 1:
        decrease_pattern += f' * {times:.0f} times'
    
    if k_second != 0:
        decrease_pattern += f', k2tog, k{k_second:.0f}'
    
    return decrease_pattern


def _format_flat_multi_plan(plan: List[Tuple[int, float]]) -> str:
    """Format a multi-part spacing plan for flat knitting decreases."""
    (small_interval, times), (large_interval, higher_times) = sorted(plan)
    k = small_interval - 2
    k_higher = large_interval - 2
    
    k_string = f'k2tog, k{k:.0f}' if k != 0 else 'k2tog'
    k_higher_string = f'k2tog, k{k_higher:.0f}' if k_higher != 0 else 'k2tog'
    
    if times % 2 == 0:
        return _handle_flat_even_times(times, k_string, higher_times, k_higher, k_higher_string)
    elif higher_times % 2 == 0:
        return _handle_flat_even_higher_times(times, k, k_string, higher_times, k_higher_string)
    else:
        return _handle_flat_odd_times(times, k_string, higher_times, k_higher, k_higher_string)


def _handle_flat_even_times(times: float, k_string: str, 
                            higher_times: float, k_higher: int, k_higher_string: str) -> str:
    """Handle flat knitting with even times."""
    times = times / 2
    higher_times = higher_times - 1
    higher_times_string = ''
    if higher_times > 0:
        higher_times_string = f', {k_higher_string}' if higher_times == 1 else f', [{k_higher_string}] * {higher_times} times'
    times_string = f', {k_string}' if times == 1 else f', [{k_string}] * {times:.0f} times'
    balanced_str_first = f'k{math.ceil(k_higher / 2):.0f}' if math.ceil(k_higher / 2) != 0 else ''
    balanced_str_last = f', k2tog k{k_higher - math.ceil(k_higher / 2):.0f}' if (k_higher - math.ceil(k_higher / 2)) != 0 else ''
    return f"{balanced_str_first}{times_string}{higher_times_string}{times_string}{balanced_str_last}"


def _handle_flat_even_higher_times(times: float, k: int, k_string: str, higher_times: float, 
                                   k_higher_string: str) -> str:
    """Handle flat knitting with even higher_times."""
    higher_times = higher_times / 2
    times = times - 1
    times_string = ''
    if times > 0:
        times_string = k_string if times == 1 else f'[{k_string}] * {times} times'
    higher_times_string = k_higher_string if higher_times == 1 else f'[{k_higher_string}] * {higher_times:.0f} times'
    balanced_str_first = f'k{math.ceil(k / 2)}, ' if math.ceil(k / 2) != 0 else ''
    balanced_str_last = f', k2tog k{k - math.ceil(k / 2)}' if (k - math.ceil(k / 2)) != 0 else ', k2tog'
    return f"{balanced_str_first}{higher_times_string}{times_string}, {higher_times_string}{balanced_str_last}"


def _handle_flat_odd_times(times: float, k_string: str, higher_times: float, 
                           k_higher: int, k_higher_string: str) -> str:
    """Handle flat knitting with odd times."""
    higher_times = math.ceil(higher_times / 2)
    higher_times_string = ''
    if higher_times > 0:
        higher_times_string = k_higher_string if higher_times == 1 else f'[{k_higher_string}] * {higher_times - 1} times, '
    times_string = k_string if times == 1 else f'[{k_string}] * {times} times, '
    balanced_str_first = f'k{math.ceil(k_higher / 2)}, ' if math.ceil(k_higher / 2) != 0 else ''
    balanced_str_last = f', k2tog k{k_higher - math.ceil(k_higher / 2)}' if (k_higher - math.ceil(k_higher / 2)) != 0 else ', k2tog'
    
    decrease_pattern = f"{balanced_str_first}{higher_times_string}{times_string}"
    higher_times -= 1
    
    if higher_times != 0:
        higher_times_string = k_higher_string if higher_times == 1 else f'[{k_higher_string}] * {higher_times} times'
        decrease_pattern += higher_times_string
    decrease_pattern += balanced_str_last
    return decrease_pattern


def decrease_evenly(
        starting_count: PositiveInt, decrease_number: PositiveInt, in_the_round: bool = False
) -> str:
    """
    A function to figure out spacing for decreases

    >>> decrease_evenly(20, 5, True)
    '[k2, k2tog] * 5 times'
    """
    _validate_decrease_parameters(starting_count, decrease_number)
    
    if in_the_round:
        result = decrease_evenly_round(starting_count, decrease_number)
    else:
        result = decrease_evenly_flat(starting_count, decrease_number)
    return result


def _validate_decrease_parameters(starting_count: int, decrease_number: int) -> None:
    """Validate parameters for decrease functions."""
    if starting_count < 2:
        msg = f"You need to have at least 2 stitches; starting_count={starting_count}"
        logging.error(msg)
        raise ValueError(msg)
    
    if decrease_number < 2:
        msg = f"the amount of decrease needs to be at least 2; decrease_number={decrease_number}."
        logging.error(msg)
        raise ValueError(msg)
    
    if decrease_number > starting_count / 2:
        msg = f"""the amount of decrease needs to be less than half of starting_count;
        decrease_number={decrease_number} > starting_count/2={starting_count / 2}"""
        logging.error(msg)
        raise ValueError(msg)
    
    if decrease_number > starting_count:
        msg = f"Error: Decrease number ({decrease_number}) is bigger than the starting count ({starting_count})"
        logging.error(msg)
        raise ValueError(msg)


def sleeve_decreases(
    number_of_rows: PositiveInt,
    starting_count: PositiveInt,
    ending_count: PositiveInt,
    decrease_per_row: PositiveInt = 2,
    padding_mode: str = "after",
) -> str:
    """A function to figure out a nice even sleeve decrease.

    >>> sleeve_decreases(61, 59, 43, 2)  # doctest: +ELLIPSIS
    '[decrease row, do 7 rows in pattern] * 5 times,...'

    ``padding_mode`` controls where the plain non-decrease rows are placed
    relative to each decrease row:

    * "after" (default): plain rows follow each decrease row (the historical
      behaviour, kept for backwards compatibility)
    * "before": plain rows precede each decrease row
    * "both": each run of plain rows is split evenly around its decrease row
    * "none": only the decrease rows are listed, back to back

    When ``starting_count - ending_count`` is not a multiple of
    ``decrease_per_row`` the leftover stitches are scheduled as extra single
    decreases (k2tog) on the last row, so the sleeve finishes at exactly
    ``ending_count`` stitches instead of a "closest alternative".
    """
    if padding_mode not in ("before", "after", "both", "none"):
        msg = (
            f"padding_mode must be one of 'before', 'after', 'both' or 'none';"
            f" got '{padding_mode}'"
        )
        logging.error(msg)
        raise ValueError(msg)

    if starting_count < ending_count:
        msg = (
            "No decreases needed, "
            f"{starting_count} is already smaller than {ending_count}"
        )
        logging.error(msg)
        raise ValueError(msg)
    elif starting_count == ending_count:
        msg = (
            "No decreases needed, the starting count is the same as the ending count"
        )
        logging.error(msg)
        raise ValueError(msg)

    total_decrease = starting_count - ending_count
    number_of_decrease_rows = total_decrease // decrease_per_row
    remainder = total_decrease % decrease_per_row

    if number_of_decrease_rows < 1:
        msg = (
            f"Error: cannot schedule any decrease rows: decreasing "
            f"{starting_count} to {ending_count} needs {total_decrease} "
            f"decreases but each decrease row only removes {decrease_per_row}"
        )
        logging.error(msg)
        raise ValueError(msg)

    padding_rows = number_of_rows - number_of_decrease_rows
    plan = _calculate_spacing(padding_rows, number_of_decrease_rows, padding_mode)

    instruction_string = _format_padding_mode(padding_mode, plan, number_of_decrease_rows)

    if remainder > 0:
        instruction_string += (
            f"\nextra decrease: work {remainder} k2tog at the end of the "
            f"last row so the final count is {ending_count} stitches"
        )

    return instruction_string


def _format_padding_mode(padding_mode: str, plan, number_of_decrease_rows: int) -> str:
    """Format instruction string based on padding mode."""
    if padding_mode == "none":
        return ", ".join(["decrease row"] * number_of_decrease_rows)
    elif padding_mode == "before":
        return ", ".join(
            f"[do {interval} rows in pattern, decrease row] * {groups} times"
            for interval, groups in plan
        )
    elif padding_mode == "both":
        segments = []
        for interval, groups in plan:
            segments.append(_format_both_mode_segment(interval, groups))
        return ", ".join(segments)
    else:  # padding_mode == "after"
        return ", ".join(
            f"[decrease row, do {interval} rows in pattern] * {groups} times"
            for interval, groups in plan
        )


def _format_both_mode_segment(interval: int, groups: int) -> str:
    """Format a segment for 'both' padding mode."""
    before = interval // 2
    after = interval - before
    
    if before > 0 and after > 0:
        return (
            f"[do {before} rows in pattern, decrease row, "
            f"do {after} rows in pattern] * {groups} times"
        )
    elif after > 0:
        return f"[decrease row, do {after} rows in pattern] * {groups} times"
    elif before > 0:
        return f"[do {before} rows in pattern, decrease row] * {groups} times"
    else:
        return f"[decrease row] * {groups} times"


def raglan_increases(
    neck_stitches: PositiveInt,
    arm_stitches: PositiveInt,
    bust_stitches: PositiveInt,
    neck_to_bust_rows: PositiveInt,
    increase_per_increase_row: PositiveInt = 8,
    armpit_stitches: PositiveInt = 4,
) -> str:
    """Tool for adjusting raglan sweaters to increase arm size or bust size.

    For a standard raglan, you increase along 4 diagonal lines over the front
    and back of the shoulders.  Each line has an increase on either side.

    Tutorial for a well-documented raglan here:
    https://blog.tincanknits.com/2013/10/25/lets-knit-a-sweater/

    >>> raglan_increases(80, 30, 100, 8)
    'Marker setup: k15, pm, k10 (arm), pm, k30, pm, k10 (arm), pm k15'
    """

    if increase_per_increase_row % 4 != 0:
        msg = (
            "increase_per_increase_row must be a multiple of 4 so the "
            f"increases divide evenly across the four sections; got "
            f"{increase_per_increase_row}"
        )
        logging.error(msg)
        raise ValueError(msg)

    # Adjusting from collar to start of raglan
    instruction_string = ""
    # the final stitch count is bust_stitches + 2 * arm stitches
    # but that includes the added armpit stitches on both sides+sleeves
    working_stitches = bust_stitches + (2 * arm_stitches) - (4 * armpit_stitches)

    # Work backwards and see if you get the collar number
    calculated_neck = working_stitches - neck_to_bust_rows * increase_per_increase_row

    # The marker setup below distributes stitches around the body and each
    # arm; validate that these stay positive so we never emit "k-5 (arm)".
    # Each increase round adds increase_per_increase_row / 4 stitches to each
    # of the four sections (front, back and both sleeves), so the starting
    # counts back out that growth.
    increments_per_section = increase_per_increase_row // 4
    body_start = (
        bust_stitches / 2
        - neck_to_bust_rows * increments_per_section
        - armpit_stitches
    )
    arm = (
        arm_stitches
        - armpit_stitches
        - neck_to_bust_rows * increments_per_section
    )
    if body_start < 1 or arm < 1:
        raise ValueError(
            "The stitch counts or row counts are too small for a raglan "
            "with this many neck-to-bust rows. Try fewer neck_to_bust_rows, "
            "a larger arm_stitches/bust_stitches, or a smaller armpit_stitches."
        )

    # if calculated_neck and neck_stitches don't match, make adjustments

    if calculated_neck > neck_stitches:
        # Add an increase row to go from your actual collar size to raglan start
        instruction_string += "Increase row: "
        instruction_string += increase_evenly(
            neck_stitches, calculated_neck - neck_stitches, in_the_round=True
        )

    if calculated_neck < neck_stitches:
        # you don't need to increase every row in the raglan section
        # We'll put the non-increase rows at the end before the armpit section
        pass

    # generate some standard raglan instructions
    # we're assuming the beginning of row is the middle of the back here
    # in case our count is uneven
    front = math.ceil(body_start)
    back = math.floor(body_start)

    instruction_string += f"Marker setup: k{math.floor(back/2)}, pm, k{arm} (arm), pm, "
    instruction_string += f"k{front}, pm, k{arm} (arm), pm k{math.ceil(back/2)}"

    return instruction_string
