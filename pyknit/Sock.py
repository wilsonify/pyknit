# Copyright (C) 2021 Terri Oda
# SPDX-License-Identifier: GPL-2.0-or-later

"""
pyKnit: a set of tools for knitters to do math, create charts, customise
patterns and more

pyKnit.Sock: Functions for creating socks

The :class:`Sock` class turns a handful of measurements and a gauge into a
complete, beginner-friendly, top-down sock plan:

* cast-on and ankle stitch counts (with configurable negative ease)
* a leg decrease plan (using pyknit's ``decrease_evenly`` spacing) whose
  stitch counts always land exactly back on the ankle count
* a slip-stitch heel flap, heel turn, gusset and wedge toe, all with
  complete step-by-step instructions and consistent, marker-friendly
  stitch counts

Every construction step is validated: the plan either comes out with
stitch counts that all add up, or it raises a :class:`ValueError`
explaining what to re-measure.  A pattern with contradictory numbers is
never produced.

Everything a first-time sock knitter needs to cast on and knit a pair is
available through :meth:`Sock.get_plan`.
"""

import math

# Negative ease (as a factor): socks are knit slightly smaller than the foot
# so they hug the foot instead of sagging.  0.8 means the sock is 80% of the
# measured circumference.  This matches the historical behaviour of pyknit and
# can be changed per-sock via ``Sock.init(negative_ease=...)``.
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
        self.negative_ease = NEGATIVE_EASE

        self.instructions = []
        self.cast_on_stitches = 0
        self.ankle_stitches = 0
        self.length_of_heel_flap = 0  # inches
        self.length_from_sock_top_to_heel_flap = 0  # inches
        self.number_of_decrease_rows = 0
        self.number_of_heel_flap_stitches = 0
        self.length_of_toe_decrease = 0  # inches
        self.length_from_heel_to_beginning_of_toe_decrease = 0  # inches

    def init(
        self,
        rows_per_inch=11,
        stitches_per_inch=9,
        circumference_at_top=10,
        circumference_of_ankle=9.5,
        length_from_sock_top_to_heel_bottom=7.75,
        length_from_heel_to_toe=10.5,
        negative_ease=NEGATIVE_EASE,
    ):

        self.rows_per_inch = float(rows_per_inch)
        self.stitches_per_inch = float(stitches_per_inch)
        self.circumference_at_top = float(circumference_at_top)
        self.circumference_of_ankle = float(circumference_of_ankle)
        self.length_from_sock_top_to_heel_bottom = float(length_from_sock_top_to_heel_bottom)
        self.length_from_heel_to_toe = float(length_from_heel_to_toe)
        self.negative_ease = float(negative_ease)

        if self.rows_per_inch <= 0 or self.stitches_per_inch <= 0:
            raise ValueError("Gauge must be greater than zero.")
        if self.circumference_at_top <= 0 or self.circumference_of_ankle <= 0:
            raise ValueError("Circumference measurements must be greater than zero.")
        if self.length_from_sock_top_to_heel_bottom <= 0 or self.length_from_heel_to_toe <= 0:
            raise ValueError("Length measurements must be greater than zero.")
        if not (0 < self.negative_ease <= 1.2):
            raise ValueError(
                "negative_ease must be greater than 0 and no more than 1.2 "
                "(0.8 means the sock is 20% smaller than the foot)."
            )

        self.get_cast_on_stitches()
        self.get_ankle_stitches()
        self.get_number_of_heel_flap_stitches()
        self.get_length_of_heel_flap()
        self.get_length_from_sock_top_to_heel_flap()
        self.get_number_of_decrease_rows()
        self.get_length_of_toe_decrease()
        self.get_length_from_heel_to_beginning_of_toe_decrease()

    # ------------------------------------------------------------------
    # Elementary rounding helpers
    # ------------------------------------------------------------------

    def round_down_even(self, n):
        """Return the largest even integer no larger than ``n``."""
        return int(math.floor(n / 2.0) * 2)

    def round_up_even(self, n):
        """Return the smallest even integer no smaller than ``n``."""
        return int(math.ceil(n / 2.0) * 2)

    # ------------------------------------------------------------------
    # Classic pyknit measurements (kept for backwards compatibility)
    # ------------------------------------------------------------------

    def get_cast_on_stitches(self):
        x = (self.stitches_per_inch * self.circumference_at_top) * self.negative_ease
        self.cast_on_stitches = self.round_down_even(x)

    def get_ankle_stitches(self):
        x = (self.stitches_per_inch * self.circumference_of_ankle) * self.negative_ease
        self.ankle_stitches = self.round_down_even(x)

    def get_length_of_heel_flap(self):
        # A well-fitting heel flap is roughly "square": as many rows as the
        # number of stitches in the flap.  Each pair of flap rows produces
        # one slipped-stitch edge, which is exactly how many stitches get
        # picked up for the gusset later.
        self.length_of_heel_flap = round(self.number_of_heel_flap_stitches / self.rows_per_inch, 2)

    def get_length_from_sock_top_to_heel_flap(self):
        x = self.length_from_sock_top_to_heel_bottom - self.length_of_heel_flap
        self.length_from_sock_top_to_heel_flap = round(x, 2)

    def get_number_of_heel_flap_stitches(self):
        # The heel flap is worked over a little more than half the stitches:
        # the heel is wider than the top of the foot.  The "+1" is the
        # traditional bit of leeway that stops the heel from stretching.
        self.number_of_heel_flap_stitches = (self.ankle_stitches // 2) + 1

    def get_length_of_toe_decrease(self):
        # Measured from the actual wedge-toe schedule so the foot and toe
        # sections add up to the requested foot length.
        self.length_of_toe_decrease = round(self._toe_row_schedule()["total_rows"] / self.rows_per_inch, 2)

    def get_length_from_heel_to_beginning_of_toe_decrease(self):
        x = self.length_from_heel_to_toe - self.length_of_toe_decrease
        self.length_from_heel_to_beginning_of_toe_decrease = round(x, 2)

    def get_number_of_decrease_rows(self):
        # The number of decrease *rounds* is decided by the leg taper:
        # - usual case: one pair (2 stitches) is removed per decrease round
        # - short leg: 2 pairs (4 stitches) per round, still every round
        # The plan keeps the total exactly cast_on - ankle, so the leg always
        # lands back on the ankle count.  ``leg_decrease_plan`` also raises a
        # clear error when the measurements cannot physically fit the taper.
        self.number_of_decrease_rows = len(self.leg_decrease_plan())

    # ------------------------------------------------------------------
    # More pieces needed to assemble a real sock
    # ------------------------------------------------------------------

    @property
    def instep_stitches(self):
        """Stitches held across the top of the foot (between the markers)."""
        return self.ankle_stitches - self.number_of_heel_flap_stitches

    @property
    def sole_stitches(self):
        """Stitches under the foot after the gusset (equals the heel flap)."""
        return self.ankle_stitches - self.instep_stitches

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

    def _spread_positions(self, plain, count):
        """Return ``count`` distinct positions spread evenly across 1..plain."""
        from pyknit import _calculate_spacing

        plan = _calculate_spacing(plain, count, padding_mode="after")
        positions = []
        cursor = 0
        for interval, groups in plan:
            for _ in range(int(groups)):
                cursor += int(interval)
                positions.append(cursor)
        return positions

    def leg_decrease_plan(self):
        """Return the decrease rounds as ``(round, before, removed)`` triples.

        ``round`` is counted from the cast-on edge (so including the cuff
        ribbing), ``before`` is the stitch count at the start of the round
        and ``removed`` is how many stitches that round removes.  Removing
        the per-round amounts in order always lands exactly on
        ``ankle_stitches``.
        """
        cast = self.cast_on_stitches
        ankle = self.ankle_stitches
        pairs = (cast - ankle) // 2
        if pairs <= 0:
            return []

        plain = self.plain_leg_rounds
        if plain <= 0:
            raise ValueError(
                f"Your leg measurements are too short to fit the decrease "
                f"rounds needed to taper from {cast} down to {ankle} "
                "stitches.  Re-measure the leg length from where the cuff "
                "will sit down to the bottom of your heel."
            )
        if pairs <= plain:
            removed_per_round = 2
            rounds = pairs
        elif pairs <= 2 * plain:
            removed_per_round = 4
            rounds = (pairs + 1) // 2
        else:
            raise ValueError(
                f"Your leg is too short to taper from {cast} stitches to "
                f"{ankle} stitches.  The decreases would have to be crammed "
                "into too few rounds to be knit sensibly.  Re-measure the "
                "leg and ankle, or use a thicker yarn."
            )

        positions = self._spread_positions(plain, rounds)
        plan = []
        before = cast
        for i, pos in enumerate(positions):
            if removed_per_round == 4:
                pairs_left = pairs - 2 * i
                removed = min(2 * pairs_left, 4)
            else:
                removed = 2
            plan.append((self.rib_rounds + pos, before, removed))
            before -= removed
        return plan

    def leg_decrease_schedule(self):
        """Backwards-compatible ``(round, stitches_before)`` pairs."""
        return [(round_no, before) for round_no, before, _ in self.leg_decrease_plan()]

    def heel_turn_rows(self):
        """Explicit right-side/wrong-side rows for the classic heel turn.

        Returns a list of ``(side, knit_or_purl_count, finished)`` tuples,
        plus the number of stitches left on the heel needle when done.
        Every row works exactly the stitches that are available, so the
        counts never overflow: the centre grows and the edges are pulled in
        one pair at a time until the cup is complete.
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
                rows.append(
                    {
                        "side": "RS",
                        "count": k_count,
                        "decrease": "ssk",
                        "finished": i == pull - 1,
                    }
                )
                k_count += 2
            else:
                rows.append(
                    {
                        "side": "WS",
                        "count": p_count,
                        "decrease": "p2tog",
                        "finished": i == pull - 1,
                    }
                )
                p_count += 2

        # Total decreases = set-up decrease (1) + one per pull round.
        remaining = flap - (1 + pull)
        return rows, remaining

    def heel_turn_remaining(self):
        _, remaining = self.heel_turn_rows()
        return remaining

    def gusset_pickup_per_side(self):
        return self.number_of_heel_flap_stitches // 2

    def gusset_stitches_after_pickup(self):
        return 2 * self.gusset_pickup_per_side() + self.instep_stitches + self.heel_turn_remaining()

    def gusset_decrease_rounds(self):
        """Number of gusset decrease rounds (each removes 2 more stitches).

        Returns ``(first_round_single_decrease, remaining_rounds)``: the
        first round removes just 1 stitch when the arithmetic needs an odd
        number removed overall, so the sock always lands back on exactly
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
        ``TOE_FINISH_STITCHES`` or fewer remain.  Every total stays even
        because each round removes 4.
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
            0,
            round(self.length_from_heel_to_beginning_of_toe_decrease * self.rows_per_inch),
        )

    # ------------------------------------------------------------------
    # Validation and warnings
    # ------------------------------------------------------------------

    def _check(self):
        """Raise ValueError whenever the plan would be contradictory."""
        if self.rows_per_inch <= 0 or self.stitches_per_inch <= 0:
            raise ValueError("Gauge must be greater than zero.")
        if self.cast_on_stitches <= 0 or self.ankle_stitches <= 0:
            raise ValueError("Stitch counts came out at zero - please check your gauge and circumference measurements.")
        if not (0 < self.negative_ease <= 1.2):
            raise ValueError("negative_ease must be greater than 0 and no more than 1.2.")

        toe = self._toe_row_schedule()
        if toe["finish_stitches"] < 4:
            raise ValueError(
                f"The ankle works out to only {self.ankle_stitches} stitches, "
                "which is too few to shape a toe.  Re-check your gauge and "
                "ankle circumference (or use a thicker yarn)."
            )
        if self.number_of_heel_flap_stitches < 11:
            raise ValueError(
                f"With only {self.number_of_heel_flap_stitches} heel flap "
                "stitches the heel cannot turn properly.  Re-check your "
                "gauge and ankle circumference."
            )
        if self.length_from_sock_top_to_heel_flap < 0:
            raise ValueError(
                f"The heel flap ({self.length_of_heel_flap:g} in) is longer "
                "than the whole leg-to-heel section, which is impossible. "
                "Re-measure the leg length from where the cuff sits down to "
                "the bottom of your heel."
            )

        # Force the leg/gusset consistency checks so impossible tapers or
        # pick-up numbers surface as clear errors, never silent nonsense.
        self.leg_decrease_plan()
        if self.gusset_stitches_after_pickup() < self.ankle_stitches:
            raise ValueError("The gusset pick-up arithmetic is inconsistent; please re-check your measurements.")
        _, remaining = self.heel_turn_rows()
        if remaining < 1:
            raise ValueError("The heel turn left too few stitches to work.")

    def warnings(self):
        """Return a list of human-readable warnings for this plan."""
        self._check()
        warned = []
        spi, rpi = self.stitches_per_inch, self.rows_per_inch
        ease = self.negative_ease
        ease_pct = round((1 - ease) * 100)

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
        if ease_pct > 30:
            warned.append(
                f"Your sock is being knit at {ease_pct}% negative ease, which "
                "is very snug. Make sure your foot fits through the heel and "
                "foot while the sock is on the needles."
            )
        if ease_pct <= 0:
            warned.append(
                "Your sock has no negative ease, so it will be the same size "
                "as your foot and may sag at the ankle. Most socks use 10-20% "
                "negative ease."
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

        ease_pct = round((1 - m.negative_ease) * 100)

        measurements = {
            "cast_on_stitches": ("Cast on", cast, "stitches"),
            "ankle_stitches": ("Around the ankle", ankle, "stitches"),
            "number_of_decrease_rows": (
                "Leg decrease rounds",
                m.number_of_decrease_rows,
                "rounds",
            ),
            "negative_ease": ("Negative ease", f"{ease_pct}%", ""),
            "length_from_sock_top_to_heel_flap": (
                "Leg (cuff to heel flap)",
                m.length_from_sock_top_to_heel_flap,
                "in",
            ),
            "length_of_heel_flap": ("Heel flap", m.length_of_heel_flap, "in"),
            "number_of_heel_flap_stitches": ("Heel flap stitches", flap, "stitches"),
            "length_from_heel_to_beginning_of_toe_decrease": (
                "Foot (heel to toe)",
                m.length_from_heel_to_beginning_of_toe_decrease,
                "in",
            ),
            "length_of_toe_decrease": ("Toe", m.length_of_toe_decrease, "in"),
        }

        assumptions = [
            "This is a classic top-down sock: you knit from the cuff "
            "(cast-on) down to the toe, finishing with a heel flap and "
            "gusset.",
            f"The sock is knit with {ease_pct}% negative ease, so it comes "
            "out a little smaller than your measurements and hugs the foot. "
            "That is normal and what makes socks stay up.",
            "Two markers are used. The start-of-round marker sits at one "
            "side of the foot; the instep marker is placed after the instep "
            "(top-of-foot) stitches during the gusset, at the other side.",
            "Instructions are written for any needle set-up (double-pointed "
            "needles, a long circular for magic loop, or two circulars).",
            "Measure around the widest part of the calf/leg for the leg "
            "circumference, and around the narrowest part of the ankle, just "
            "above the ankle bone.",
            "Use a gauge swatch in stockinette, blocked as you will block the finished sock.",
        ]

        sections = [
            self._plan_cast_on(cast),
            self._plan_leg(ankle),
            self._plan_heel_flap(flap, instep),
            self._plan_heel_turn(flap),
            self._plan_gusset(pickup, instep, heel_rem, after_pickup, ankle, gusset_first, gusset_rest),
            self._plan_foot(foot_rounds, ankle),
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
                "join into a round without twisting.  Place a marker for "
                "the start of the round.",
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
            steps.append("Your leg length came out at zero, so the heel flap will start right after the cast-on.")
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
            f"{self.plain_leg_rounds} rounds (about {plain_in:g} in), "
            "keeping your start-of-round marker in place."
        )

        plan = self.leg_decrease_plan()
        table = None
        if plan:
            two_per_round = all(removed == 2 for _, _, removed in plan)
            steps.append(
                "Then taper the leg down towards the ankle: each decrease "
                "round removes stitches near each side of the leg"
                + (
                    " (2 stitches per round)."
                    if two_per_round
                    else " (2, or on the busiest rounds 4, stitches per round; "
                    "the table shows the exact count for every round)."
                )
                + f"  After all {self.number_of_decrease_rows} decrease "
                f"rounds you will have exactly {ankle} stitches."
            )
            trows = []
            for round_no, before, removed in plan:
                pattern = decrease_evenly(before, removed, in_the_round=True)
                trows.append([str(round_no), pattern, str(before - removed)])
            table = {
                "columns": ["Round (from cast-on)", "Decrease round", "Stitches after"],
                "rows": trows,
            }
        else:
            steps.append("Your leg and ankle are the same width, so the leg is knit straight with no decreases.")
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
                f"You now move the {flap} sole stitches onto one needle; " "these become the heel.",
                "Place the other "
                f"{instep} stitches (the top of the foot) on a holder or a "
                "spare circular.  They will wait here until the gusset.",
                "Heel flap, Row 1 (right side): k2, then repeat *slip 1 with "
                "the yarn in back, k1* across the remaining heel stitches, "
                "ending with a knit stitch.  If it does not work out exactly, "
                "just slip/k1 as you go - the edge stitches do the important "
                "work.",
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
            f"Set-up row (wrong side): slip 1, purl {flap // 2 + 1}, p2tog, " "p1, turn.",
        ]
        turn_rows, remaining = self.heel_turn_rows()
        side = {"RS": "right", "WS": "wrong"}
        for i, row in enumerate(turn_rows):
            if row["decrease"] == "ssk":
                tail = f"k{row['count']}, ssk, k1"
            else:
                tail = f"p{row['count']}, p2tog, p1"
            if row["finished"]:
                tail += ".  All the heel stitches have now been used - "
                "do not turn."
            else:
                tail += ", turn."
            steps.append(f"Row {i + 2} ({side[row['side']]} side): slip 1, {tail}")
        steps.append(
            f"Count your stitches: you should now have {remaining} stitches "
            "on the heel needle, which will form the rounded cup under your "
            "ankle.  Your start-of-round marker has stayed at the side of "
            "the foot all along."
        )
        return {
            "heading": "4. Turn the heel",
            "intro": None,
            "steps": steps,
        }

    def _plan_gusset(self, pickup, instep, heel_rem, after_pickup, ankle, gusset_first, gusset_rest):
        steps = [
            f"Pick up and knit {pickup} stitches along the left edge of the "
            "heel flap (one into each slipped-stitch loop), knit across the "
            f"{instep} instep stitches, place your instep marker, then pick "
            f"up and knit {pickup} stitches along the right edge.  Finally "
            f"knit the {heel_rem} heel stitches to the start-of-round "
            "marker.  If a tiny hole forms at the corner it will be pulled "
            "shut by the decreases that follow.",
            f"You now have {after_pickup} stitches.  The start of round is "
            f"marked at one side of the foot and the instep marker sits at "
            f"the other side, dividing the round into the {instep} instep "
            f"stitches (top of the foot) and the {after_pickup - instep} "
            "sole stitches.",
        ]
        if after_pickup - ankle <= 0:
            steps.append("The picked-up stitches equal the ankle count, so you can start the foot section directly.")
        else:
            steps.append(
                "Gusset decrease round: from the start-of-round marker, knit "
                f"to 3 stitches before the instep marker, k2tog, k1, slip "
                f"the instep marker, knit across the {instep} instep "
                "stitches, slip the start-of-round marker, k1, ssk, then "
                "knit to the end of the round.  This removes 2 stitches - "
                "one at each side of the foot, right next to the markers."
            )
            gusset_total = gusset_first + gusset_rest
            if gusset_first == 1:
                steps.append(
                    "Because the pick-up count is odd, first remove just 1 "
                    "stitch: from the start-of-round marker, knit to 3 "
                    "stitches before the instep marker, k2tog, k1, slip the "
                    "instep marker, knit across the instep, and knit to the "
                    "end of the round (no decrease on the second side).  "
                    "Work the remaining rounds every other round, with a "
                    "plain knit round in between."
                )
                steps.append(
                    f"Then work {gusset_rest} full decrease rounds as above, "
                    f"every other round, so after the final one you are back "
                    f"to exactly {ankle} stitches: {instep} instep stitches "
                    f"plus {ankle - instep} sole stitches."
                )
            else:
                steps.append(
                    f"Work this decrease round every other round, with a "
                    f"plain knit round in between, for {gusset_total} "
                    f"decrease rounds.  After the last one you are back to "
                    f"exactly {ankle} stitches: {instep} instep stitches "
                    f"plus {ankle - instep} sole stitches."
                )
        return {
            "heading": "5. Shape the gusset",
            "intro": (
                "Picking up stitches along the heel flap closes the heel into "
                "a cup.  The little triangles of picked-up stitches on either "
                "side are the 'gusset', and they are decreased away at the "
                "markers."
            ),
            "steps": steps,
        }

    def _plan_foot(self, foot_rounds, ankle):
        steps = []
        if foot_rounds <= 0:
            steps.append("There is no plain foot section to knit - start the toe immediately after the gusset.")
        else:
            steps.append(
                f"Knit straight in the round (every round knit) for "
                f"{foot_rounds} rounds, about "
                f"{round(foot_rounds / self.rows_per_inch, 2):g} in.  You "
                f"have {ankle} stitches and your two markers are already in "
                "place at the sides of the foot."
            )
            steps.append(
                "Try the sock on as you go: the toe should begin when the "
                "sock reaches the base of your little toe.  The foot length "
                "is measured from the back of the heel to the tip of the "
                "toes, so trust your measurements over how the sock looks "
                "off your foot."
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
                f"You already have a marker on each side of the foot: the "
                f"start-of-round marker and the instep marker.  The two "
                f"markers divide the round into the {self.instep_stitches} "
                f"instep stitches (top of foot) and the "
                f"{ankle - self.instep_stitches} sole stitches.",
                "Toe decrease round: k1, ssk, knit to 3 stitches before the "
                "instep marker, k2tog, k1, slip the instep marker, k1, ssk, "
                "knit to 3 stitches before the start-of-round marker, k2tog, "
                "k1.  This removes 4 stitches - 2 at each side of the foot, "
                "right next to the markers.",
                f"Phase 1: work a decrease round, then a plain knit round, "
                f"repeating until {toe['phase1_end_stitches']} stitches "
                f"remain (about {toe['phase1_decrease_rounds']} decrease "
                "rounds).  This shapes the rounded part of the toe.",
                f"Phase 2: now work a decrease round every round until "
                f"{toe['finish_stitches']} stitches remain (about "
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
                "Wash and block the sock - this evens out the stitches and makes it look much neater.",
                "Knit a second sock exactly the same way (yes, store-bought "
                "socks do not come in pairs - but yours should).",
            ],
        }
