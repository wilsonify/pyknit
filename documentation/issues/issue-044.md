# Issue #44: Charting

**Status:** CLOSED
**Created:** 2022-04-29T16:05:20Z
**Updated:** 2022-05-15T19:41:10Z
**Labels:** None
**URL:** [https://github.com/terriko/pyknit/pull/44](https://github.com/terriko/pyknit/pull/44)

## Description

This PR adds colour charting, per Issue #21, and the option to use png symbols, per Issue #30. It also adds the ability to use 2D plots.

For 2D plots, lines are separated by newlines just now. Plot direction can be specified (converting a manually edited grid with colours might be better top to bottom, left to right; knit instructions tend to be the opposite)

Row and column numbers are added to the plots, depending on plotting direction.

Type hints in Chart.py also updated to reflect code use, and Stitch class separated a little more from the legend.

Added colour picker widgets and a plot to the triangle hat demo as that seemed a good fit for demonstration.

Finally added a simple cable in a notebook to demonstrate the charting with symbols.

---

## Branch
Work on this issue using the branch: `issue-44`

```bash
git checkout issue-44
```

## Related Links
- [GitHub Issue](https://github.com/terriko/pyknit/issues/44)
