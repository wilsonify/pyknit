# TODO: Combine sleeve_decreases with decrease_evenly

**File:** pyknit/__init__.py
**Line:** 233
**Status:** Open
**Effort:** 0min
**Created:** ~4 years ago

## Task Description

The `sleeve_decreases()` function is very similar to the `decrease_evenly()` function and could be refactored to use shared logic.

### Current Code Context

```python
def sleeve_decreases(
    number_of_rows: PositiveInt,
    starting_count: PositiveInt,
    ending_count: PositiveInt,
    decrease_per_row: PositiveInt = 2,
) -> str:
    """ A function to figure out a nice even sleeve decrease. """

    # TODO: This function is going to be pretty similar to the decrease_evenly()
    # function.  We may want to combine them later.
```

## Objective

Refactor the codebase to avoid duplication between `sleeve_decreases()` and `decrease_evenly()`. Options:
1. Create a shared helper function for common logic
2. Make one function call the other with adapted parameters
3. Create a base function that both inherit from
4. Extract the common calculation logic into a utility

## Benefits

- Reduced code duplication (DRY principle)
- Easier to maintain and bug fix
- Single source of truth for decrease logic
- Potentially simpler API for users

## Related Issues

- Issue #51: Feature/decrease evenly
- Issue #4: Write the decrease_evenly() function

## Priority

This is an informational maintenance task with 0min estimated effort.
