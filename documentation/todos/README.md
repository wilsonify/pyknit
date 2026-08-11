# TODO Items Documentation Index

This directory contains documentation for all TODO items found in the pyknit codebase.

## Active TODOs

### 1. [Add Yardage/Weight for Calculations](todo-001-gaugeswatch-yardage.md)
- **File:** pyknit/GaugeSwatch.py
- **Line:** 27
- **Also in:** pyknit/Untitled.ipynb (L24)
- **Status:** Open
- **Description:** Add yardage/weight calculations to the GaugeSwatch class to help users estimate yarn needed

### 2. [Add Extra Decreases for Remainder Instead of Erroring](todo-002-hat-decreases.md)
- **File:** pyknit/Hat.py
- **Line:** 18
- **Status:** Open
- **Description:** Improve error handling to automatically add extra decreases for remainder stitches instead of failing

### 3. [Combine sleeve_decreases with decrease_evenly](todo-003-decrease-evenly-refactor.md)
- **File:** pyknit/__init__.py
- **Line:** 233
- **Status:** Open
- **Description:** Refactor duplicate code between sleeve_decreases() and decrease_evenly() functions

### 4. [Automate Math for Remainder Decreases](todo-004-sleeve-math-automation.md)
- **File:** pyknit/__init__.py
- **Line:** 252
- **Status:** Open
- **Description:** Automatically calculate and suggest where to place extra decreases instead of warning users

### 5. [Add Padding Options (Both Sides / Neither)](todo-005-padding-options.md)
- **File:** pyknit/__init__.py
- **Line:** 262
- **Status:** Open
- **Description:** Add configuration options for padding distribution (before, after, both, or neither)

## Summary

- **Total TODOs:** 5
- **All Status:** Open
- **Total Estimated Effort:** 0min (these are information/task suggestions)

## Categorization by Type

### Code Refactoring
- [Combine sleeve_decreases with decrease_evenly](todo-003-decrease-evenly-refactor.md)

### Feature Enhancement
- [Add Yardage/Weight for Calculations](todo-001-gaugeswatch-yardage.md)
- [Add Extra Decreases for Remainder](todo-002-hat-decreases.md)
- [Automate Math for Remainder Decreases](todo-004-sleeve-math-automation.md)
- [Add Padding Options](todo-005-padding-options.md)

## Categorization by File

### pyknit/__init__.py
- [Combine sleeve_decreases with decrease_evenly](todo-003-decrease-evenly-refactor.md) (L233)
- [Automate Math for Remainder Decreases](todo-004-sleeve-math-automation.md) (L252)
- [Add Padding Options](todo-005-padding-options.md) (L262)

### pyknit/GaugeSwatch.py
- [Add Yardage/Weight for Calculations](todo-001-gaugeswatch-yardage.md) (L27)

### pyknit/Hat.py
- [Add Extra Decreases for Remainder](todo-002-hat-decreases.md) (L18)

## Related Issues

Many of these TODO items are related to existing GitHub issues:
- Issue #4: Write the decrease_evenly() function
- Issue #6: Create an interactive Jupyter notebook for the sleeve example
- Issue #9: Add error handling for nonsensical sleeves and increases
- Issue #51: Feature/decrease evenly

## Related Documentation

- [GitHub Issues](../issues/)
- [Main README](../README.md)
