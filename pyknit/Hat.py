# Copyright (C) 2021 Terri Oda
# SPDX-License-Identifier: GPL-2.0-or-later

"""
pyKnit: a set of tools for knitters to do math, create charts, customise
patterns and more

pyKnit.Hat: Functions for creating a hat
"""


class Hat:
    def crown_decreases(self, repeats: int, stitches: int):
        if repeats <= 0 or stitches <= 0:
            return "Invalid starting parameters"

        remainder = stitches % repeats
        count_per_repeat = stitches // repeats

        instructions = []
        current_stitches = stitches

        while current_stitches - repeats > 0:
            current_stitches = current_stitches - repeats
            if count_per_repeat - 2 > 0:
                line = f"[k{int(count_per_repeat-2)}, k2tog] repeat {repeats} times"
            else:
                line = f"k2tog {repeats} times"

            if remainder > 0 and current_stitches + repeats == stitches:
                current_stitches = current_stitches - remainder
                line = f"{line}, k2tog {remainder} times"

            instructions.append(f"{line} ({current_stitches} stitches)")

            instructions.append("Knit 1 round")
            count_per_repeat = count_per_repeat - 1
        instructions.append("Cut yarn leaving 4 inch tail, thread through remaining stitches and pull closed")
        return instructions
