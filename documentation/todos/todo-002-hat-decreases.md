# TODO: Add Extra Decreases for Remainder Instead of Erroring

**File:** pyknit/Hat.py
**Line:** 18
**Status:** Open
**Effort:** 0min
**Created:** ~5 years ago

## Task Description

Improve the decrease logic to handle remainder stitches gracefully.

### Current Code Context

```python
if repeats <= 0 or stitches <= 0:
    return("Invalid starting parameters")
if stitches % repeats > 0: 
    # TODO we could add extra decreases for remainder instead of erroring
    return("Error: stitch count does not divide evenly")
```

## Objective

Instead of returning an error when stitch count doesn't divide evenly by repeats, automatically add extra decreases to handle the remainder. This would:
- Make the function more user-friendly
- Handle edge cases automatically
- Reduce manual calculation needed by users

## Implementation Notes

- Calculate the remainder when stitches % repeats > 0
- Distribute extra decreases across the repeat rounds
- May want to spread them out evenly or concentrate them
- Ensure the pattern still looks balanced

## Related Issues

- Issue #51: Feature/decrease evenly
- Issue #4: Write the decrease_evenly() function

## Priority

This is an informational task with 0min estimated effort.
