# Copyright (C) 2021 Terri Oda
# SPDX-License-Identifier: GPL-2.0-or-later

import argparse
import logging

from pyknit import VERSION, GaugeSwatch

_CENTIMETERS_PER_INCH = 2.54


def _convert_measurement_units(
    measurement: float, from_unit: str, to_unit: str
) -> float:
    """Convert a measurement between inches and centimetres (1 in = 2.54 cm)."""
    if from_unit == to_unit:
        return measurement
    if from_unit == "cm" and to_unit == "in":
        return measurement / _CENTIMETERS_PER_INCH
    if from_unit == "in" and to_unit == "cm":
        return measurement * _CENTIMETERS_PER_INCH
    raise ValueError(f"Unsupported unit conversion: {from_unit} -> {to_unit}")


def convert_row_gauge(
    original_gauge: GaugeSwatch,
    new_gauge: GaugeSwatch,
    original_measurement: float,
    original_unit: str,
) -> float:
    """Convert a measurement in rows from the original gauge to the new gauge.

    The measurement is counted at the original gauge (rows in the original
    unit), measured at the new gauge (rows -> new unit), and the final
    measurement is reported back in the original unit.
    """
    rows = original_gauge.measurement_to_rows(original_measurement)
    new_measurement = new_gauge.rows_to_measurement(rows)
    return _convert_measurement_units(new_measurement, new_gauge.units, original_unit)


def convert_stitch_gauge(
    original_gauge: GaugeSwatch,
    new_gauge: GaugeSwatch,
    original_measurement: float,
    original_unit: str,
) -> float:
    """Convert a measurement in stitches at the original gauge to the new gauge.

    The measurement is counted at the original gauge (stitches in the original
    unit), measured at the new gauge (stitches -> new unit), and the final
    measurement is reported back in the original unit.
    """
    stitches = original_gauge.measurement_to_stitches(original_measurement)
    new_measurement = new_gauge.stitches_to_measurement(stitches)
    return _convert_measurement_units(new_measurement, new_gauge.units, original_unit)


def main():
    # set up the logger
    logger = logging.getLogger(__package__)
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    print(f"{VERSION}")
    desc = """
    This package is intended for use as a library inside jupyter notebook,
    but has some basic gauge calculations available on the command line.
    Use --convert to convert from one gauge to another.
    """
    logger.warning(desc)
    parser = _create_argument_parser(desc)
    
    args = parser.parse_args()

    if not args.convert:
        parser.print_usage()
        exit()

    if args.convert == "row":
        _handle_row_conversion(args, logger)
    elif args.convert == "stitch":
        _handle_stitch_conversion(args, logger)


def _create_argument_parser(desc: str) -> argparse.ArgumentParser:
    """Create and return the argument parser."""
    parser = argparse.ArgumentParser(prog="pyknit", description=desc)

    conversion_options_group = parser.add_argument_group("Conversion Options")
    conversion_options_group.add_argument(
        "--convert",
        help="Convert from one gauge to another. Specify row or stitch to indicate which direction of measurement you need to convert.",
        choices=["row", "stitch"],
        type=str,
        action="store",
    )

    # Set details for original gauge (often this will be pattern gague)
    original_gauge_group = parser.add_argument_group("Original Gauge Details")
    original_gauge_group.add_argument(
        "--original-gauge-row",
        "-ogr",
        help="Original gauge (typically from the pattern) in rows/inch",
        action="store",
        type=float,
        default=None,
    )
    original_gauge_group.add_argument(
        "--original-gauge-stitch",
        "-ogs",
        help="Original gauge (typically from the pattern) in stitches/inch",
        type=float,
        action="store",
        default=None,
    )
    original_gauge_group.add_argument(
        "--original-gauge-measurement",
        "-ogm",
        help="Original gauge swatch measurement (numbers only)",
        type=float,
        action="store",
        default=1,
    )
    original_gauge_group.add_argument(
        "--original-gauge-unit",
        "-ogu",
        help="Original gauge units (in or cm)",
        type=str,
        action="store",
        default="in",
    )

    # Arguments for my gauge (measured from your own swatch)
    new_gauge_group = parser.add_argument_group("New Gauge Details")
    new_gauge_group.add_argument(
        "--new-gauge-row",
        "-ngr",
        help="New gauge (typically from your swatch) in rows/inch",
        type=float,
        action="store",
        default=None,
    )
    new_gauge_group.add_argument(
        "--new-gauge-stitch",
        "-ngs",
        help="Original gauge (typically from your swatch) in stitches/inch",
        type=float,
        action="store",
        default=None,
    )
    new_gauge_group.add_argument(
        "--new-gauge-measurement",
        "-ngm",
        help="New gauge swatch measurement (numbers only)",
        type=float,
        action="store",
        default=1,
    )
    new_gauge_group.add_argument(
        "--new-gauge-unit",
        "-ngu",
        help="New gauge units (in or cm)",
        type=str,
        action="store",
        default="in",
    )

    parser.add_argument(
        "--original-measurement",
        help="Original measurement (typically from the pattern) that you wish to convert",
        action="store",
        type=float,
    )

    return parser


def _get_or_input(value: float, prompt: str) -> float:
    """Get a value from args or prompt user for input."""
    if not value:
        return float(input(prompt))
    return value


def _handle_row_conversion(args, logger):
    """Handle row gauge conversion."""
    logger.info("Converting row gauge...")
    
    original_gauge_row = _get_or_input(
        args.original_gauge_row,
        f"Please enter a valid original gauge (row/{args.original_gauge_unit}): "
    )
    new_gauge_row = _get_or_input(
        args.new_gauge_row,
        f"Please enter a valid new gauge (row/{args.new_gauge_unit}): "
    )
    original_measurement = _get_or_input(
        args.original_measurement,
        f"Please enter the measurement you want to convert ({args.original_gauge_unit}): "
    )

    # Show what numbers we're using
    logger.info("")
    logger.info(f"Original gauge: {original_gauge_row} rows/{args.original_gauge_unit}")
    logger.info(f"New gauge: {new_gauge_row} rows/{args.new_gauge_unit}")
    logger.info(f"Original pattern measurement: {original_measurement} {args.original_gauge_unit}")

    # Construct the gauges in their own units
    original_gauge = GaugeSwatch(
        row_count=original_gauge_row,
        stitch_count=1,
        row_measure=args.original_gauge_measurement,
        stitch_measure=1,
        units=args.original_gauge_unit,
    )
    new_gauge = GaugeSwatch(
        row_count=new_gauge_row,
        stitch_count=1,
        row_measure=args.new_gauge_measurement,
        stitch_measure=1,
        units=args.new_gauge_unit,
    )
    
    new_measurement = convert_row_gauge(
        original_gauge,
        new_gauge,
        original_measurement,
        args.original_gauge_unit,
    )
    logger.info(f"My calculated measurement: {new_measurement} {args.original_gauge_unit}")
    logger.info("")


def _handle_stitch_conversion(args, logger):
    """Handle stitch gauge conversion."""
    logger.info("Converting stitch gauge...")
    
    original_gauge_stitch = _get_or_input(
        args.original_gauge_stitch,
        f"Please enter a valid original gauge (stitch/{args.original_gauge_unit}): "
    )
    new_gauge_stitch = _get_or_input(
        args.new_gauge_stitch,
        f"Please enter a valid new gauge (stitch/{args.new_gauge_unit}): "
    )
    original_measurement = _get_or_input(
        args.original_measurement,
        f"Please enter the measurement you want to convert ({args.original_gauge_unit}): "
    )

    # Show what numbers we're using
    logger.info("")
    logger.info(f"Original gauge: {original_gauge_stitch} stitchs/{args.original_gauge_unit}")
    logger.info(f"New gauge: {new_gauge_stitch} stitchs/{args.new_gauge_unit}")
    logger.info(f"Original pattern measurement: {original_measurement} {args.original_gauge_unit}")

    # Construct the gauges in their own units
    original_gauge = GaugeSwatch(
        stitch_count=original_gauge_stitch,
        row_count=1,
        row_measure=1,
        stitch_measure=args.original_gauge_measurement,
        units=args.original_gauge_unit,
    )
    new_gauge = GaugeSwatch(
        stitch_count=new_gauge_stitch,
        row_count=1,
        row_measure=1,
        stitch_measure=args.new_gauge_measurement,
        units=args.new_gauge_unit,
    )
    
    new_measurement = convert_stitch_gauge(
        original_gauge,
        new_gauge,
        original_measurement,
        args.original_gauge_unit,
    )
    logger.info(f"My calculated measurement: {new_measurement} {args.original_gauge_unit}")
    logger.info("")

    # legend = {
    #    "k": "k",
    #    "p": "p",
    #    "kfb": "kfb",
    #    "ssk": "ssk",
    #    "k2tog": "k2tog",
    #    "p2tog": "p2tog",
    # }

    # print(parse_written(args.instruction_row, legend))


if __name__ == "__main__":
    main()
