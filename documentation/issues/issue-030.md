# Issue #30: Extend default sitch dictionary & symbols we can draw

**Status:** OPEN
**Created:** 2021-05-18T22:47:39Z
**Updated:** 2021-10-14T21:58:50Z
**Labels:** art, hacktoberfest
**URL:** [https://github.com/terriko/pyknit/issues/30](https://github.com/terriko/pyknit/issues/30)

## Description

The chart function has a fairly small initial stitch dictionary, focusing mostly on stuff we could easily do with a default font.  It would be great to have a larger default library for folk to use.

The craft yarn council has a list of [knit chart symbols](https://www.craftyarncouncil.com/standards/knit-chart-symbols) that would be a good initial library.  We'd need to find a way to draw all those symbols.  I *think* what we'd want is little SVGs for each symbol so they could be resized as needed, but I'm open to other suggestions of things that can be drawn from Python.  (Knitting fonts do exist, but I haven't seen something with a compatible license, and we'd want something we could distribute with this GPL2.0+ project)

---

## Branch
Work on this issue using the branch: `issue-30`

```bash
git checkout issue-30
```

## Related Links
- [GitHub Issue](https://github.com/terriko/pyknit/issues/30)
