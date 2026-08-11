# Issue #8: Add error handling for nonsensical gauge swatches.

**Status:** OPEN
**Created:** 2021-03-05T01:39:10Z
**Updated:** 2021-10-14T21:58:01Z
**Labels:** good first issue, hacktoberfest
**URL:** [https://github.com/terriko/pyknit/issues/8](https://github.com/terriko/pyknit/issues/8)

## Description

If you make a gauge swatch with measurements set to 0, it's going to give you bad math.  We should probably handle that with an appropriate error when you initially try to set something to 0 so you don't get surprised later.

We might also want to make some way for a user to specify "I never measured this part of my gauge" if they want to do measurement conversions for only rows or only stitches.

---

## Branch
Work on this issue using the branch: `issue-8`

```bash
git checkout issue-8
```

## Related Links
- [GitHub Issue](https://github.com/terriko/pyknit/issues/8)
