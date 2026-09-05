"""Shared garment model for the Raglan Sweater Planner and Knit Simulator.

The garment model is the single source of truth for garment construction.
Both the planner and simulator use it, so the simulator never infers
construction from display text or comments.

The model describes a top-down raglan sweater as a sequence of stages:

    neckline → yoke → separation → body → hem →
    left_sleeve → left_cuff → right_sleeve → right_cuff → finishing

Each stage has:
- stitch counts (before/after)
- operations (what the knitter does)
- garment construction details (held stitches, underarm cast-on, etc.)
"""

from dataclasses import dataclass, field
from enum import Enum

# Reusable string constants to avoid duplication across garment stages
RIB_PATTERN = "k2 p2"
RIB_DESCRIPTION_FMT = "%d rounds of k2 p2 ribbing"
BIND_OFF_DESCRIPTION = "Bind off all stitches"
RIB_AND_BIND_OFF = "Ribbing and bind off"


class StageType(Enum):
    """Canonical stage types for a top-down raglan sweater."""

    NECKLINE = "neckline"
    YOKE = "yoke"
    SEPARATION = "separation"
    BODY = "body"
    HEM = "hem"
    LEFT_SLEEVE = "left_sleeve"
    LEFT_CUFF = "left_cuff"
    RIGHT_SLEEVE = "right_sleeve"
    RIGHT_CUFF = "right_cuff"
    FINISHING = "finishing"


class OpType(Enum):
    """Types of knitting operations."""

    CAST_ON = "cast_on"
    RIB = "rib"
    STOCKINETTE = "stockinette"
    INCREASE = "increase"
    DECREASE = "decrease"
    SHORT_ROW = "short_row"
    BIND_OFF = "bind_off"
    PICKUP = "pickup"
    PLACE_ON_HOLDER = "place_on_holder"
    FINISH = "finish"


@dataclass
class KnitOp:
    """A single knitting operation within a stage."""

    op_type: OpType
    rounds: int = 0
    pattern: str = ""
    count: int = 0
    per_round: int = 0
    frequency: str = ""
    from_holder: bool = False
    underarm_cast_on: int = 0
    description: str = ""

    def to_dict(self):
        d = {"type": self.op_type.value}
        if self.rounds:
            d["rounds"] = self.rounds
        if self.pattern:
            d["pattern"] = self.pattern
        if self.count:
            d["count"] = self.count
        if self.per_round:
            d["per_round"] = self.per_round
        if self.frequency:
            d["frequency"] = self.frequency
        if self.from_holder:
            d["from_holder"] = True
        if self.underarm_cast_on:
            d["underarm_cast_on"] = self.underarm_cast_on
        if self.description:
            d["description"] = self.description
        return d


@dataclass
class GarmentStage:
    """A stage in the garment construction process.

    Each stage represents a distinct phase of knitting with its own stitch
    count, operations, and construction details.
    """

    stage_type: StageType
    label: str
    description: str
    start_stitch_count: int = 0
    end_stitch_count: int = 0
    operations: list = field(default_factory=list)
    held_stitches: int = 0
    held_on_waste_yarn: bool = False
    underarm_cast_on: int = 0
    pickup_from_holder: bool = False
    short_row_shaping: bool = False

    def to_dict(self):
        d = {
            "id": self.stage_type.value,
            "label": self.label,
            "description": self.description,
        }
        if self.start_stitch_count:
            d["start_stitch_count"] = self.start_stitch_count
        if self.end_stitch_count:
            d["end_stitch_count"] = self.end_stitch_count
        if self.operations:
            d["operations"] = [op.to_dict() for op in self.operations]
        if self.held_stitches:
            d["held_stitches"] = self.held_stitches
        if self.held_on_waste_yarn:
            d["held_on_waste_yarn"] = True
        if self.underarm_cast_on:
            d["underarm_cast_on"] = self.underarm_cast_on
        if self.pickup_from_holder:
            d["pickup_from_holder"] = True
        if self.short_row_shaping:
            d["short_row_shaping"] = True
        return d


@dataclass
class GarmentModel:
    """The complete garment model shared between planner and simulator.

    This is the single source of truth for garment construction. The planner
    generates it from measurements and gauge, and the simulator consumes it
    to visualize the knitting process.
    """

    garment_type: str = "raglan"
    stages: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        return {
            "garment_type": self.garment_type,
            "stages": [s.to_dict() for s in self.stages],
            "metadata": self.metadata,
        }

    def get_stage(self, stage_type):
        """Get a stage by its type."""
        for stage in self.stages:
            if stage.stage_type == stage_type:
                return stage
        return None

    def get_stage_index(self, stage_type):
        """Get the index of a stage by its type."""
        for i, stage in enumerate(self.stages):
            if stage.stage_type == stage_type:
                return i
        return -1


def build_raglan_model(meta):
    """Build a GarmentModel from the planner's computed metadata.

    This function translates the planner's internal representation into the
    shared garment model that both planner and simulator use.
    """
    stages = []

    # Stage 1: Neckline
    neckline_ops = [
        KnitOp(OpType.CAST_ON, count=meta["neck"], description="Cast on %d stitches" % meta["neck"]),
    ]
    if meta.get("collar_rounds", 0) > 0:
        neckline_ops.append(
            KnitOp(
                OpType.RIB,
                rounds=meta["collar_rounds"],
                pattern=RIB_PATTERN,
                description=RIB_DESCRIPTION_FMT % meta["collar_rounds"],
            )
        )
    if meta.get("pre", 0) > 0:
        neckline_ops.append(
            KnitOp(
                OpType.INCREASE,
                rounds=1,
                count=meta["pre"],
                description="Neck increase: +%d evenly" % meta["pre"],
            )
        )
    stages.append(
        GarmentStage(
            stage_type=StageType.NECKLINE,
            label="Neckline",
            description="Cast on and collar ribbing",
            start_stitch_count=meta["neck"],
            end_stitch_count=meta.get("calc_neck", meta["neck"]),
            operations=neckline_ops,
        )
    )

    # Stage 2: Yoke (raglan increases)
    yoke_ops = [
        KnitOp(
            OpType.INCREASE,
            rounds=meta["raglan_total_rounds"],
            count=meta["inc"],
            per_round=meta["seg"],
            frequency=meta["freq"],
            description="Raglan increase: +%d per increase round, %s"
            % (meta["inc"], "every round" if meta["freq"] == "every_round" else "every other round"),
        )
    ]
    stages.append(
        GarmentStage(
            stage_type=StageType.YOKE,
            label="Raglan Yoke",
            description="Increase along four raglan seams",
            start_stitch_count=meta.get("calc_neck", meta["neck"]),
            end_stitch_count=meta["working"],
            operations=yoke_ops,
        )
    )

    # Stage 3: Sleeve Separation
    separation_ops = [
        KnitOp(
            OpType.PLACE_ON_HOLDER,
            count=meta["arm"],
            description="Place %d-stitch sleeves on waste yarn" % meta["arm"],
        ),
        KnitOp(
            OpType.CAST_ON,
            count=meta["bust"],
            description="Cast on %d stitches for body" % meta["bust"],
        ),
    ]
    stages.append(
        GarmentStage(
            stage_type=StageType.SEPARATION,
            label="Sleeve Separation",
            description="Divide for body and sleeves",
            start_stitch_count=meta["working"],
            end_stitch_count=meta["bust"],
            operations=separation_ops,
            held_stitches=meta["arm"],
            held_on_waste_yarn=True,
            underarm_cast_on=meta["armpit"],
        )
    )

    # Stage 4: Body
    body_ops = [
        KnitOp(
            OpType.STOCKINETTE,
            rounds=meta["body_stock_rounds"],
            description="%d rounds of stockinette" % meta["body_stock_rounds"],
        )
    ]
    stages.append(
        GarmentStage(
            stage_type=StageType.BODY,
            label="Body",
            description="Knit body in stockinette",
            start_stitch_count=meta["bust"],
            end_stitch_count=meta["bust"],
            operations=body_ops,
        )
    )

    # Stage 5: Hem
    hem_ops = [
        KnitOp(
            OpType.RIB,
            rounds=meta["hem_rounds"],
            pattern=RIB_PATTERN,
            description=RIB_DESCRIPTION_FMT % meta["hem_rounds"],
        ),
        KnitOp(OpType.BIND_OFF, description=BIND_OFF_DESCRIPTION),
    ]
    stages.append(
        GarmentStage(
            stage_type=StageType.HEM,
            label="Hem",
            description=RIB_AND_BIND_OFF,
            start_stitch_count=meta["bust"],
            end_stitch_count=0,
            operations=hem_ops,
        )
    )

    # Stage 6: Left Sleeve
    sleeve_ops = [
        KnitOp(
            OpType.PICKUP,
            count=meta["sleeve_final"],
            from_holder=True,
            underarm_cast_on=meta["armpit"],
            description="Pick up %d held stitches + %d underarm" % (meta["sleeve_final"], meta["armpit"]),
        ),
    ]
    if meta.get("sleeve_shaping_rounds", 0) > 0:
        sleeve_ops.append(
            KnitOp(
                OpType.DECREASE,
                rounds=meta["sleeve_shaping_rounds"],
                per_round=2,
                description="%d rounds with decreases at underarm markers" % meta["sleeve_shaping_rounds"],
            )
        )
    stages.append(
        GarmentStage(
            stage_type=StageType.LEFT_SLEEVE,
            label="Left Sleeve",
            description="Pick up held stitches and knit sleeve",
            start_stitch_count=meta["arm"],
            end_stitch_count=meta["wrist"],
            operations=sleeve_ops,
            pickup_from_holder=True,
            underarm_cast_on=meta["armpit"],
        )
    )

    # Stage 7: Left Cuff
    cuff_ops = [
        KnitOp(
            OpType.RIB,
            rounds=meta["cuff_rounds"],
            pattern=RIB_PATTERN,
            description=RIB_DESCRIPTION_FMT % meta["cuff_rounds"],
        ),
        KnitOp(OpType.BIND_OFF, description=BIND_OFF_DESCRIPTION),
    ]
    stages.append(
        GarmentStage(
            stage_type=StageType.LEFT_CUFF,
            label="Left Cuff",
            description=RIB_AND_BIND_OFF,
            start_stitch_count=meta["wrist"],
            end_stitch_count=0,
            operations=cuff_ops,
        )
    )

    # Stage 8: Right Sleeve (same as left)
    stages.append(
        GarmentStage(
            stage_type=StageType.RIGHT_SLEEVE,
            label="Right Sleeve",
            description="Pick up held stitches and knit sleeve",
            start_stitch_count=meta["arm"],
            end_stitch_count=meta["wrist"],
            operations=[
                KnitOp(
                    OpType.PICKUP,
                    count=meta["sleeve_final"],
                    from_holder=True,
                    underarm_cast_on=meta["armpit"],
                    description="Pick up %d held stitches + %d underarm" % (meta["sleeve_final"], meta["armpit"]),
                ),
            ]
            + (
                [
                    KnitOp(
                        OpType.DECREASE,
                        rounds=meta["sleeve_shaping_rounds"],
                        per_round=2,
                        description="%d rounds with decreases at underarm markers" % meta["sleeve_shaping_rounds"],
                    )
                ]
                if meta.get("sleeve_shaping_rounds", 0) > 0
                else []
            ),
            pickup_from_holder=True,
            underarm_cast_on=meta["armpit"],
        )
    )

    # Stage 9: Right Cuff (same as left)
    stages.append(
        GarmentStage(
            stage_type=StageType.RIGHT_CUFF,
            label="Right Cuff",
            description=RIB_AND_BIND_OFF,
            start_stitch_count=meta["wrist"],
            end_stitch_count=0,
            operations=[
                KnitOp(
                    OpType.RIB,
                    rounds=meta["cuff_rounds"],
                    pattern=RIB_PATTERN,
                    description=RIB_DESCRIPTION_FMT % meta["cuff_rounds"],
                ),
                KnitOp(OpType.BIND_OFF, description=BIND_OFF_DESCRIPTION),
            ],
        )
    )

    # Stage 10: Finishing
    stages.append(
        GarmentStage(
            stage_type=StageType.FINISHING,
            label="Finishing",
            description="Weave in ends, block, and enjoy your sweater!",
            operations=[KnitOp(OpType.FINISH, description="Weave in ends and block")],
        )
    )

    return GarmentModel(
        garment_type="raglan",
        stages=stages,
        metadata={
            "gauge": meta.get("gauge", {}),
            "measurements": meta.get("measurements", {}),
            "yarn": meta.get("yarn"),
            "needles": meta.get("needles"),
        },
    )
