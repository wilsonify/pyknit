# TODO: Add Yardage/Weight for Calculations

**File:** pyknit/GaugeSwatch.py
**Line:** 27
**Status:** Open
**Effort:** 0min
**Created:** ~5 years ago

## Task Description

Add yardage/weight calculations to the GaugeSwatch class.

### Current Code Context

```python
class GaugeSwatch:
    """Information from a gauge swatch"""

    row_count: PositiveFloat
    row_measure: PositiveFloat
    stitch_count: PositiveFloat
    stitch_measure: PositiveFloat
    units: Literal["cm", "in"]
    # TODO: add yardage/weight for calculations?
```

## Objective

Extend the GaugeSwatch class to support yardage and weight calculations. This would allow users to:
- Calculate total yardage needed based on finished dimensions
- Estimate yarn weight required
- Better plan yarn purchases for projects

## Implementation Notes

- Consider adding optional fields for yarn yardage and weight
- Create methods to calculate yardage needed for a project
- May need to integrate with other classes (Hat, Sock, etc.)

## Related Issues

- Search related issues: [yardage, weight, calculations](https://github.com/terriko/pyknit/issues)

## Priority

This is an informational task with 0min estimated effort.
