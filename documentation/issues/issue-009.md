# Issue #9: Add error handling for nonsensical sleeves and increases

**Status:** CLOSED
**Created:** 2021-03-05T01:45:33Z
**Updated:** 2021-05-26T19:15:06Z
**Labels:** good first issue
**URL:** [https://github.com/terriko/pyknit/issues/9](https://github.com/terriko/pyknit/issues/9)

## Description

I didn't put much in the way of error handling into the math functions, and we should probably fix that so people get a warning if they enter something that doesn't make sense.

Examples: 
- The way increasing stitches with m1 (make 1) usually works, you can only add as many stitches as you had to start.  So if `increase_number > starting_count` in the `increase_evenly()` function the instructions don't actually make sense.  We should throw an error instead
- Entering 0s isn't going to make sense in a bunch of these either
- Negative numbers either.  We could maybe import some sort of unsigned type, but for now I think just an error would be fine.

---

## Branch
Work on this issue using the branch: `issue-9`

```bash
git checkout issue-9
```

## Related Links
- [GitHub Issue](https://github.com/terriko/pyknit/issues/9)
