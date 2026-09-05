# TODO: Add Padding Options (Both Sides / Neither)

**File:** pyknit/__init__.py
**Line:** 262
**Status:** Open
**Effort:** 0min
**Created:** ~4 years ago

## Task Description

Add configuration options for how to distribute padding rows around decreases.

### Current Code Context

```python
# divide up the number of rows.
# This gives you a decrease on the first row but padding after the last
# TODO: make an option for padding both sides, padding neither?

interval = math.floor(
    (number_of_rows - number_of_decrease_rows) / number_of_decrease_rows
)
remainder = (number_of_rows - number_of_decrease_rows) % number_of_decrease_rows
```

## Objective

Add a parameter to control padding distribution options:
- **Padding on both sides:** Center the decreases within the available rows
- **Padding on neither:** Decreases only, no padding rows
- **Padding after only:** Current behavior (decreases on first row, padding at end)
- **Padding before only:** Padding first, then decreases

## Implementation Notes

- Add a `padding_mode` or `alignment` parameter to the function
- Options could be: `'after'`, `'before'`, `'both'`, `'none'`
- Update the interval calculation based on chosen mode
- Provide sensible defaults (probably current behavior)
- Update documentation with examples for each option

## Benefits

- More flexibility for different sweater/garment designs
- Users can achieve different aesthetic effects
- Better control over how ease is distributed
- More professional-looking finished projects

## Related Issues

- Issue #51: Feature/decrease evenly
- Issue #6: Create an interactive Jupyter notebook for the sleeve example

## Priority

This is an informational task with 0min estimated effort.
