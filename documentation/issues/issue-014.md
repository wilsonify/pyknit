# Issue #14: Create Pi Shawl function (and also half-pi)

**Status:** OPEN
**Created:** 2021-05-11T08:06:24Z
**Updated:** 2021-05-17T20:01:43Z
**Labels:** enhancement, good first issue
**URL:** [https://github.com/terriko/pyknit/issues/14](https://github.com/terriko/pyknit/issues/14)

## Description

_This is one of the shawl shapes mentioned in #11, but I'm describing it here in more detail so it's a more bite-sized issue._

**A pi shawl is a circular shape with regular increases as the radius of the shawl grows:**

https://www.craftsy.com/post/pi-shawl-patterns/

> But pi shawls, while still worked from the center out, only require a few shaping rows in the entire project. Basically, every time you double your distance from the last increase round worked, you work another increase round. These infrequent increase rounds make pi shawls a great option for lace knitting.

It would be nice to have a function that, given a gauge swatch, could tell you how many rows to work between increase rows to get the desired flat circle, printed as a pattern or as a set of numbers, and maybe also have it calculate how many rounds you'd need to reach a desired size (given the gauge).

Similarly, a half-pi shawl is the same idea but only half the circle is worked.  The math would be the same for how many rows to work but the instructions would be different.  You'd probably want to make half-pi an option on the full-pi function.



---

## Branch
Work on this issue using the branch: `issue-14`

```bash
git checkout issue-14
```

## Related Links
- [GitHub Issue](https://github.com/terriko/pyknit/issues/14)
