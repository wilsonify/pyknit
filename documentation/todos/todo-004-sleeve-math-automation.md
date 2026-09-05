# TODO: Automate Math for Remainder Decreases

**File:** pyknit/__init__.py
**Line:** 252
**Status:** Open
**Effort:** 0min
**Created:** ~4 years ago

## Task Description

The function currently warns users when desired decreases don't work exactly. This task is to automate the math calculations for remainder decreases.

### Current Code Context

```python
if ((starting_count - ending_count) % decrease_per_row) > 0:
    # TODO: we could probably do this math for people if we wanted
    logging.warning(
        f"Warning: desired decrease doesn't work exactly with a {decrease_per_row} decrease"
    )
    logging.warning(
        "Printing the closest alternative but you'll need to add decreases at the end"
    )
```

## Objective

Automatically calculate and suggest where to place extra decreases for remainder stitches, rather than requiring users to manually add decreases at the end.

## Implementation Notes

- Calculate remainder: `(starting_count - ending_count) % decrease_per_row`
- Distribute these extra decreases evenly throughout the pattern
- Update the instructions to include where these extra decreases occur
- Eliminate manual work for users
- Provide clear output showing exactly what to knit

## Benefits

- Better user experience (no manual adjustment needed)
- More precise patterns
- Reduced errors from manual calculations
- Could handle edge cases automatically

## Related Issues

- Issue #51: Feature/decrease evenly
- Issue #9: Add error handling for nonsensical sleeves and increases

## Priority

This is an informational task with 0min estimated effort.
