# Copyright (C) 2021 Terri Oda
# SPDX-License-Identifier: GPL-2.0-or-later

#!python
"""
pyKnit: a set of tools for knitters to do math, create charts, customise
patterns and more

pyKnit.Sock: Functions for creating socks

The :class:`Sock` class turns a handful of measurements and a gauge into a
complete, beginner-friendly, top-down sock plan:

* cast-on and ankle stitch counts (with negative ease)
* a leg decrease schedule (using pyknit's ``decrease_evenly`` spacing)
* a slip-stitch heel flap, heel turn, gusset and wedge toe, all with
  complete step-by-step instructions

Everything a first-time sock knitter needs to cast on and knit a pair is
available through :meth:`Sock.get_plan`.
"""

import math


# Negative ease (as a factor): socks are knit slightly smaller than the foot
# so they hug the foot instead of sagging.  0.8 means the sock is 80% of the
# measured circumference.  This matches the historical behaviour of pyknit.
NEGATIVE_EASE = 0.8

# Ribbing forms the neat, stretchy cuff at the top of the sock.
CUFF_RIB_INCHES = 1.0

# Per-round safety used to keep the toe from vanishing into a point.
TOE_FINISH_STITCHES = 8


class Sock:
    def __init__(self):
        self.rows_per_inch = None
        self.stitches_per_inch = None
        self.circumference_at_top = None  # inches
        self.circumference_of_ankle = None  # inches
        self.length_from_sock_top_to_heel_bottom = None  # inches
        self.length_from_heel_to_toe = None  # inches

        self.instructions = []
        self.cast_on_stitches = 0
        self.ankle_stitches = 0
        self.length_of_heel_flap = 0  # inches
        self.length_from_sock_top_to_heel_flap = 0  # inches
        self.number_of_decrease_rows = 0
        self.number_of_heel_flap_stitches = 0
        self.length_of_toe_decrease = 0  # inches
        self.length_from_heel_to_beginning_of_toe_decrease = 0  # inches

    def init(self,
             rows_per_inch=11,
             stitches_per_inch=9,
             circumference_at_top=10,
             circumference_of_ankle=9.5,
             length_from_sock_top_to_heel_bottom=7.75,
             length_from_heel_to_toe=10.5):

        self.rows_per_inch = rows_per_inch
        self.stitches_per_inch = stitches_per_inch
        self.circumference_at_top = circumference_at_top
        self.circumference_of_ankle = circumference_of_ankle
        self.length_from_sock_top_to_heel_bottom = length_from_sock_top_to_heel_bottom
        self.length_from_heel_to_toe = length_from_heel_to_toe

        self.get_cast_on_stitches()
        self.get_ankle_stitches()
        self.get_number_of_decrease_rows()
        self.get_number_of_heel_flap_stitches()
        self.get_length_of_heel_flap()
        self.get_length_from_sock_top_to_heel_flap()
        self.get_length_of_toe_decrease()
        self.get_length_from_heel_to_beginning_of_toe_decrease()

    # ------------------------------------------------------------------
    # Elementary rounding helpers
    # ------------------------------------------------------------------

    def round_down_even(self, n):
        answer = round(n)
        if not answer % 2:
            return answer
        else:
            return answer - 1

    def round_up_even(self, n):
        answer = round(n)
        if not answer % 2:
            return answer
        else:
            return answer + 1

    # ------------------------------------------------------------------
    # Classic pyknit measurements (kept for backwards compatibility)
    # ------------------------------------------------------------------

    def get_cast_on_stitches(self):
        x = (self.stitches_per_inch * self.circumference_at_top) * NEGATIVE_EASE
        self.cast_on_stitches = self.round_down_even(x)

    def get_ankle_stitches(self):
        x = (self.stitches_per_inch * self.circumference_of_ankle) * NEGATIVE_EASE
        self.ankle_stitches = self.round_down_even(x)

    def get_length_of_heel_flap(self):
        # A well-fitting heel flap is roughly "square": as many rows as the
        # number of stitches in the flap.  Each pair of flap rows produces
        # one slipped-stitch edge, which is exactly how many stitches get
        # picked up for the gusset later.
        self.length_of_heel_flap = round(
            self.number_of_heel_flap_stitches / self.rows_per_inch, 2
        )

    def get_length_from_sock_top_to_heel_flap(self):
        x = self.length_from_sock_top_to_heel_bottom - self.length_of_heel_flap
        self.length_from_sock_top_to_heel_flap = round(x, 2)

    def get_number_of_decrease_rows(self):
        # Going from the cast-on count to the ankle count, each leg decrease
        # round removes exactly 2 stitches (one at each side).  Both counts
        # are rounded to even numbers, so the difference is always even and
        # the number of decrease rounds is exact.
        if self.cast_on_stitches <= self.ankle_stitches:
            self.number_of_decrease_rows = 0
            return
        self.number_of_decrease_rows = (
            self.cast_on_stitches - self.ankle_stitches
        ) // 2

    def get_number_of_heel_flap_stitches(self):
        # The heel flap is worked over a little more than half the stitches:
        # the heel is wider than the top of the foot.  The "+1" is the
        # traditional bit of leeway that stops the heel from stretching.
        self.number_of_heel_flap_stitches = (self.ankle_stitches // 2) + 1

    def get_length_of_toe_decrease(self):
        # Measured from the actual wedge-toe schedule so the foot and toe
        # sections add up to the requested foot length.
        self.length_of_toe_decrease = round(
            self._toe_row_schedule()["total_rows"] / self.rows_per_inch, 2
        )

    def get_length_from_heel_to_beginning_of_toe_decrease(self):
        x = self.length_from_heel_to_toe - self.length_of_toe_decrease
        self.length_from_heel_to_beginning_of_toe_decrease = round(x, 2)

    # ------------------------------------------------------------------
    # More pieces needed to assemble a real sock
    # ------------------------------------------------------------------

    @property
    def instep_stitches(self):
        """Stitches held across the top of the foot (between the marker)."""
        return self.ankle_stitches - self.number_of_heel_flap_stitches

    @property
    def rib_rounds(self):
        leg = self.length_from_sock_top_to_heel_flap
        if leg <= 0:
            return 0
        rib = min(CUFF_RIB_INCHES, leg / 2)
        return max(1, round(rib * self.rows_per_inch))

    @property
    def plain_leg_rounds(self):
        rib = self.rib_rounds / self.rows_per_inch
        plain = self.length_from_sock_top_to_heel_flap - rib
        return max(0, round(plain * self.rows_per_inch))

    def leg_decrease_schedule(self):
        """Return the list of leg decrease rounds.

        Each entry is ``(round_number_from_cast_on, stitches_before)`` where
        the decrease round reduces the count by 2 (one stitch at each side).
        Round numbers are counted from the cast-on edge (so including the
        cuff ribbing).  Positions are spread evenly through the plain part of
        the leg using the same spacing engine as pyknit's
        :func:`pyknit.pyknit.sleeve_decreases`.
        """
        from pyknit import _calculate_spacing

        schedule = []
        total = self.number_of_decrease_rows
        if total <= 0:
            return schedule

        plain = self.plain_leg_rounds
        if plain <= 0:
            return schedule

        plan = _calculate_spacing(plain, total, padding_mode="after")
        current = 0
        positions = []
        for interval, groups in plan:
            for _ in range(int(groups)):
                current += 1          # the decrease row
                positions.append(current)
                current += interval   # the plain rows that follow

        count = self.cast_on_stitches
        used = set()
        for pos in positions:
            pos = max(1, min(plain, int(pos)))
            if pos in used:
                continue
            used.add(pos)
            schedule.append((self.rib_rounds + pos, count))
            count -= 2

        # If spacing collapsed to fewer unique rounds than needed, cram the
        # remaining decrease rounds into the last plain round(s).
        leftover = total - len(schedule)
        for _ in range(leftover):
            last = schedule[-1][0] if schedule else self.rib_rounds + plain
            if last in used:
                last = min(plain, last + 1)
            used.add(last)
            schedule.append((self.rib_rounds + last, count))
            count -= 2

        if count != self.ankle_stitches:
            # Keep the arithmetic honest no matter what.
            schedule = schedule[: self.number_of_decrease_rows]
        return sorted(schedule)

    def heel_turn_rows(self):
        """Explicit right-side/wrong-side rows for the classic heel turn.

        Returns a list of ``(side, knit_or_purl_count, finished)`` tuples,
        plus the number of stitches left on the heel needle when done.
        """
        flap = self.number_of_heel_flap_stitches
        purl_setup = flap // 2 + 1
        # After the set-up row we have worked flap - (purl_setup + 3)
        # stitches; every following row pulls one more stitch in and removes
        # one via the decrease, so the number of rows after the set-up equals
        # the number of stitches still waiting to be worked.
        pull = flap - (purl_setup + 3)

        rows = []
        k_count = 5
        p_count = 6
        for i in range(pull):
            if i % 2 == 0:
                # Right side, as seen from the outside of the sock.
                rows.append({"side": "RS", "count": k_count,
                             "decrease": "ssk",
                             "last": i == pull - 1})
                k_count += 2
            else:
                rows.append({"side": "WS", "count": p_count,
                             "decrease": "p2tog",
                             "last": i == pull - 1})
                p_count += 2

        # Total decreases = set-up decrease (1) + one per pull round.
        remaining = flap - (1 + pull)
        return rows, remaining

    def heel_turn_remaining(self):
        rows, remaining = self.heel_turn_rows()
        return remaining

    def gusset_pickup_per_side(self):
        return self.number_of_heel_flap_stitches // 2

    def gusset_stitches_after_pickup(self):
        return (
            2 * self.gusset_pickup_per_side()
            + self.instep_stitches
            + self.heel_turn_remaining()
        )

    def gusset_decrease_rounds(self):
        """Number of gusset decrease rounds (2 sts removed per round).

        The first round removes only 1 stitch when the arithmetic needs an
        odd number removed overall, so the sock always lands back on exactly
        ``ankle_stitches``.
        """
        to_remove = self.gusset_stitches_after_pickup() - self.ankle_stitches
        if to_remove <= 0:
            return 0, 0
        first_round = to_remove % 2
        rest = (to_remove - first_round) // 2
        return first_round, rest

    def _toe_row_schedule(self):
        """Stitch counts for a classic wedge toe.

        Phase 1 decreases 4 stitches (2 at each side) every other round until
        about half the stitches remain; phase 2 decreases every round until
        ``TOE_FINISH_STITCHES`` or fewer remain.
        """
        total = self.ankle_stitches

        phase1_decrease_rounds = 0
        while total > self.ankle_stitches // 2:
            total -= 4
            phase1_decrease_rounds += 1

        phase1_span = max(0, 2 * phase1_decrease_rounds - 1)

        phase2_decrease_rounds = 0
        while total > TOE_FINISH_STITCHES:
            total -= 4
            phase2_decrease_rounds += 1

        return {
            "phase1_decrease_rounds": phase1_decrease_rounds,
            "phase1_span_rows": phase1_span,
            "phase1_end_stitches": total + 4 * phase2_decrease_rounds,
            "phase2_decrease_rounds": phase2_decrease_rounds,
            "finish_stitches": total,
            "total_rows": phase1_span + phase2_decrease_rounds,
        }

    def foot_rounds(self):
        return max(
            0, round(self.length_from_heel_to_beginning_of_toe_decrease
                     * self.rows_per_inch)
        )

    # ------------------------------------------------------------------
    # Validation and warnings
    # ------------------------------------------------------------------

    def _check(self):
        if self.cast_on_stitches <= 0 or self.ankle_stitches <= 0:
            raise ValueError(
                "Stitch counts came out at zero - please check your gauge "
                "and circumference measurements."
            )
        if self.rows_per_inch <= 0 or self.stitches_per_inch <= 0:
            raise ValueError("Gauge must be greater than zero.")

    def warnings(self):
        """Return a list of human-readable warnings for this plan."""
        self._check()
        warned = []
        spi, rpi = self.stitches_per_inch, self.rows_per_inch

        if spi < 4 or spi > 16:
            warned.append(
                f"With {spi:g} stitches per inch the gauge is outside the "
                "usual sock range (roughly 5-12 per inch). Recheck your "
                "swatch, and try again with the correct gauge for your yarn."
            )
        if rpi < 5 or rpi > 20:
            warned.append(
                f"With {rpi:g} rows per inch the row gauge is unusual for "
                "socks. Make sure you measured a stockinette swatch that you "
                "did not stretch."
            )
        if self.ankle_stitches < 24:
            warned.append(
                f"Your ankle only gives {self.ankle_stitches} stitches, which "
                "is a very narrow sock. Double-check the ankle circumference "
                "and gauge before you begin."
            )
        if self.cast_on_stitches < self.ankle_stitches:
            warned.append(
                "Your leg circumference is smaller than your ankle "
                f"({self.cast_on_stitches} vs {self.ankle_stitches} "
                "stitches), so no leg decreases are needed - the sock will "
                "simply be knit without shaping until the heel."
            )
        elif self.cast_on_stitches == self.ankle_stitches:
            warned.append(
                "Your leg and ankle measure the same width, so there are no "
                "leg decreases - just knit straight down to the heel."
            )
        if self.length_from_sock_top_to_heel_flap <= 0.5:
            warned.append(
                "Your leg is very short. Consider increasing the "
                "'leg length' measurement so the sock actually reaches your "
                "calf."
            )
        if self.length_from_heel_to_beginning_of_toe_decrease < 1:
            warned.append(
                "Your foot is barely longer than the toe, which leaves almost "
                "no plain foot section. Re-measure the foot from the back of "
                "the heel to the tip of the longest toe."
            )
        if self.length_from_heel_to_toe < 5:
            warned.append(
                "A foot length under 5 inches is very small - check that "
                "you measured from the heel to the longest toe."
            )
        return warned

    # ------------------------------------------------------------------
    # The guided plan
    # ------------------------------------------------------------------

    def get_plan(self):
        """Build the full guided sock plan as a dictionary.

        Returns a dict containing ``measurements``, ``assumptions``,
        ``warnings`` and ``sections`` (a list of steps with optional tables)
        that a UI can render directly.
        """
        self._check()

        m = self

        cast = m.cast_on_stitches
        ankle = m.ankle_stitches
        flap = m.number_of_heel_flap_stitches
        instep = m.instep_stitches
        pickup = m.gusset_pickup_per_side()
        heel_rem = m.heel_turn_remaining()
        after_pickup = m.gusset_stitches_after_pickup()

        toe = m._toe_row_schedule()
        foot_rounds = m.foot_rounds()
        gusset_first, gusset_rest = m.gusset_decrease_rounds()

        measurements = {
            "cast_on_stitches": ("Cast on", cast, "stitches"),
            "ankle_stitches": ("Around the ankle", ankle, "stitches"),
            "number_of_decrease_rows": ("Leg decrease rounds",
                                        m.number_of_decrease_rows, "rounds"),
            "length_from_sock_top_to_heel_flap": (
                "Leg (cuff to heel flap)",
                m.length_from_sock_top_to_heel_flap, "in"),
            "length_of_heel_flap": ("Heel flap", m.length_of_heel_flap, "in"),
            "number_of_heel_flap_stitches": (
                "Heel flap stitches", flap, "stitches"),
            "length_from_heel_to_beginning_of_toe_decrease": (
                "Foot (heel to toe)", 
                m.length_from_heel_to_beginning_of_toe_decrease, "in"),
            "length_of_toe_decrease": ("Toe", m.length_of_toe_decrease, "in"),
        }

        assumptions = [
            "This is a classic top-down sock: you knit from the cuff (cast-on) "
            "down to the toe, finishing with a heel flap and gusset.",
            "The sock is knit with about 20% negative ease, so it comes out a "
            "little smaller than your measurements and hugs the foot.  That is "
            "normal and what makes socks stay up.",
            "Instructions are written for any needle set-up (double-pointed "
            "needles, a long circular for magic loop, or two circulars).  You "
            "only ever need a marker for the start of the round, plus a second "
            "marker when you reach the toe.",
            "Measure around the widest part of the calf/leg for the leg "
            "circumference, and around the narrowest part of the ankle, just "
            "above the ankle bone.",
            "Use a gauge swatch in stockinette, blocked as you will block the "
            "finished sock.",
        ]

        sections = [
            self._plan_cast_on(cast),
            self._plan_leg(ankle),
            self._plan_heel_flap(flap, instep),
            self._plan_heel_turn(flap),
            self._plan_gusset(pickup, instep, heel_rem, after_pickup, ankle,
                              gusset_first, gusset_rest),
            self._plan_foot(foot_rounds),
            self._plan_toe(ankle, toe),
            self._plan_finish(),
        ]

        return {
            "measurements": measurements,
            "assumptions": assumptions,
            "warnings": m.warnings(),
            "sections": sections,
        }

    # ------------------------------------------------------------------
    # Guided-plan helpers
    # ------------------------------------------------------------------

    def _plan_cast_on(self, cast):
        return {
            "heading": "1. Cast on and get started",
            "intro": (
                f"You will cast on {cast} stitches.  A stretchy edge makes "
                "the cuff comfortable, which matters more than you might "
                "think."
            ),
            "steps": [
                f"Cast on {cast} stitches using a stretchy cast-on (the "
                "long-tail or German twisted cast-on both work well), and "
                "join into a round without twisting.  Place a marker for the "
                "start of the round.",
                "Distribute the stitches evenly over your needles/magic loop "
                "so you can knit around easily.  The exact split does not "
                "matter yet.",
            ],
        }

    def _plan_leg(self, ankle):
        """Section 2: cuff ribbing, plain leg and the decrease schedule."""
        from pyknit import decrease_evenly

        steps = []
        if self.length_from_sock_top_to_heel_flap <= 0:
            steps.append(
                "Your leg length came out at zero, so the heel flap will "
                "start right after the cast-on."
            )
            return {
                "heading": "2. The leg (cuff to heel)",
                "intro": None,
                "steps": steps,
            }

        rib = self.rib_rounds
        rib_in = round(rib / self.rows_per_inch, 2)
        unit = "inch" if rib_in == 1 else "inches"
        steps.append(
            f"Knit {rib} rounds of k2, p2 ribbing (about {rib_in:g} "
            f"{unit}).  The ribbing keeps the cuff from rolling."
        )
        plain_in = round(self.plain_leg_rounds / self.rows_per_inch, 2)
        steps.append(
            f"Then knit every round in stockinette for "
            f"{self.plain_leg_rounds} rounds (about {plain_in:g} in) until "
            f"the leg measures {self.length_from_sock_top_to_heel_flap:g} "
            "in from the cast-on edge to the heel."
        )

        schedule = self.leg_decrease_schedule()
        table = None
        if schedule:
            steps.append(
                "The leg tapers from the calf down to the ankle.  "
                "Decrease 2 stitches per decrease round; after all "
                f"{self.number_of_decrease_rows} decrease rounds you will "
                f"have exactly {ankle} stitches."
            )
            trows = []
            for round_no, before in schedule:
                pattern = decrease_evenly(before, 2, in_the_round=True)
                trows.append([str(round_no), pattern, str(before - 2)])
            table = {
                "columns": ["Round (from cast-on)", "Decrease round",
                            "Stitches after"],
                "rows": trows,
            }
        else:
            steps.append(
                "Your leg and ankle are the same width, so the leg is "
                "knit straight with no decreases."
            )
        return {
            "heading": "2. The leg (cuff to heel)",
            "intro": None,
            "steps": steps,
            "table": table,
        }

    def _plan_heel_flap(self, flap, instep):
        return {
            "heading": "3. Work the heel flap",
            "intro": (
                "The heel flap is knit back and forth over the sole stitches "
                "in a slip-stitch pattern.  It feels odd at first because you "
                "abandon half your stitches for a while - that is expected."
            ),
            "steps": [
                f"You now move the {flap} sole stitches onto one needle; "
                "these become the heel.  The other "
                f"{instep} stitches (the top of the foot) wait on their "
                "holders.",
                "Heel flap, Row 1 (right side): k2, then repeat *slip 1 with "
                "the yarn in back, k1* across the remaining heel stitches, "
                "ending with a knit stitch.  If the maths does not work out "
                "exactly, just slip/k1 as you go - the edges matter more "
                "than the middle.",
                "Row 2 (wrong side): slip 1, purl across, turn.",
                "Row 3 (right side): *slip 1, k1* across, turn.",
                "Repeat rows 2 and 3 until the flap is square - you will "
                f"have about {flap} rows in total.  Finish with a right-side "
                "row.  The slipped stitches make a firm, durable fabric and "
                "give you the little edge-loops you will pick into later.",
            ],
        }

    def _plan_heel_turn(self, flap):
        steps = [
            f"Set-up row (wrong side): slip 1, purl {flap // 2 + 1}, p2tog, "
            "p1, turn.",
        ]
        turn_rows, remaining = self.heel_turn_rows()
        for i, row in enumerate(turn_rows):
            side = "right" if row["decrease"] == "ssk" else "wrong"
            if row["decrease"] == "ssk":
                tail = f"slip 1, k{row['count']}, ssk, k1"
            else:
                tail = f"slip 1, p{row['count']}, p2tog, p1"
            if row["last"]:
                tail += " - all heel stitches have now been used, so do not turn."
            else:
                tail += ", turn."
            steps.append(f"Row {i + 2} ({side} side): {tail}")
        steps.append(
            f"Count your stitches: you should now have {remaining} stitches "
            "on the heel needle, which will form the rounded cup under your "
            "ankle."
        )
        return {
            "heading": "4. Turn the heel",
            "intro": None,
            "steps": steps,
        }

    def _plan_gusset(self, pickup, instep, heel_rem, after_pickup, ankle,
                     gusset_first, gusset_rest):
        steps = [
            f"Pick up and knit {pickup} stitches along the left edge of the "
            "heel flap (one into each slipped-stitch loop), knit across the "
            f"{instep} instep stitches, place a marker, then pick up and knit "
            f"{pickup} stitches along the right edge.  "
            f"Finally knit the {heel_rem} heel stitches.  (If you find a gap "
            "at the corners, pick up one extra stitch there - the extra "
            "stitch is removed again by the decreases.)",
            f"You now have {after_pickup} stitches: the instep marker sits "
            f"between the {instep} instep stitches and the sole stitches.",
        ]
        if after_pickup - ankle <= 0:
            steps.append(
                "The picked-up stitches match the ankle count, so you can "
                "start the foot section directly."
            )
        else:
            steps.append(
                "Gusset decrease round: knit to 3 stitches before the first "
                "marker, k2tog, k1, slip marker, knit across the instep, "
                "slip marker, k1, ssk, knit to the end of the round.  This "
                "removes 2 stitches (one at each edge of the sole)."
            )
            gusset_total = gusset_first + gusset_rest
            if gusset_first == 1:
                steps.append(
                    "Work this decrease round every other round, with a plain "
                    "knit round between, but start by removing just 1 "
                    "stitch: first decrease round work "
                    "knit to 3 stitches before the first marker, k2tog, k1, "
                    "slip marker, knit across the instep, slip marker, k1, "
                    "knit to the end of the round (no decrease on the second "
                    "side).  This makes the stitch counts come out exactly."
                )
                steps.append(
                    f"Then do {gusset_rest} full decrease rounds as above, "
                    f"every other round, so after the final one you are back "
                    f"to {ankle} stitches."
                )
            else:
                steps.append(
                    f"Work this decrease round every other round, with a "
                    f"plain knit round in between, for {gusset_total} "
                    f"decrease rounds.  After the last one you are back to "
                    f"{ankle} stitches."
                )
        return {
            "heading": "5. Shape the gusset",
            "intro": (
                "Picking up stitches along the heel flap closes the heel into "
                "a cup.  The little triangles of picked-up stitches on either "
                "side are the 'gusset', and they are decreased away."
            ),
            "steps": steps,
        }

    def _plan_foot(self, foot_rounds):
        steps = []
        if foot_rounds <= 0:
            steps.append(
                "There is no plain foot section to knit - start the toe "
                "immediately after the gusset."
            )
        else:
            steps.append(
                f"Knit straight in the round (every round knit) for "
                f"{foot_rounds} rounds, about "
                f"{round(foot_rounds / self.rows_per_inch, 2):g} in.  Try "
                "the sock on as you go: the toe should begin when the sock "
                "reaches the base of your little toe."
            )
            steps.append(
                "The foot length is measured from the back of the heel to "
                "the bend of the toes, so trust your measurements over how "
                "the sock looks off your foot."
            )
        return {
            "heading": "6. Knit the foot",
            "intro": None,
            "steps": steps,
        }

    def _plan_toe(self, ankle, toe):
        return {
            "heading": "7. Knit the toe",
            "intro": None,
            "steps": [
                "Place a second marker halfway around, so the round is "
                f"split into two halves of {ankle // 2} stitches each.",
                "Toe decrease round: k1, ssk, knit to 3 stitches before the "
                "marker, k2tog, k1, slip marker, k1, ssk, knit to 3 stitches "
                "before the start-of-round marker, k2tog, k1.  This removes "
                "4 stitches (2 at each side of the foot).",
                f"Phase 1: work a decrease round, then a plain knit round, "
                f"repeating until {toe['phase1_end_stitches']} stitches "
                f"remain (about {toe['phase1_decrease_rounds']} decrease "
                "rounds).  This shapes the rounded part of the toe.",
                f"Phase 2: now work a decrease round every round until "
                f"{toe['finish_stitches']} stitches (or fewer) remain (about "
                f"{toe['phase2_decrease_rounds']} rounds).",
                f"Cut the yarn leaving a 6 in tail, thread it through the "
                f"remaining {toe['finish_stitches']} stitches, pull firmly "
                "closed and weave the end inside.  (For an invisible finish, "
                "graft the last stitches with Kitchener stitch instead.)",
            ],
        }

    def _plan_finish(self):
        return {
            "heading": "8. Finish and repeat",
            "intro": None,
            "steps": [
                "Weave in all loose ends on the inside of the sock.",
                "Wash and block the sock - this evens out the stitches and "
                "makes it look much neater.",
                "Knit a second sock exactly the same way (yes, store-bought "
                "socks do not come in pairs - but yours should).",
            ],
        }