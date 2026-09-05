# Issue #13: Read charts from .csv files (or other spreadsheet files?)

**Status:** OPEN
**Created:** 2021-05-11T07:42:07Z
**Updated:** 2021-05-22T16:57:12Z
**Labels:** enhancement
**URL:** [https://github.com/terriko/pyknit/issues/13](https://github.com/terriko/pyknit/issues/13)

## Description

Currently, we have a (somewhat simplistic) parser for written instructions that generates charts, but we'd like to be able to also generate written instructions from charts.  One step for this would be reading charts out of spreadsheets or other formats.  I'm not actually entirely sure how this would work, as a typical chart includes colours and stuff that wouldn't necessarily be seen in a .csv export.  But let's start with the easiest part of the problem and see if we can at least read symbols from a .csv file and get them into some sort of Chart data structure for further manipulation.

---

## Branch
Work on this issue using the branch: `issue-13`

```bash
git checkout issue-13
```

## Related Links
- [GitHub Issue](https://github.com/terriko/pyknit/issues/13)
