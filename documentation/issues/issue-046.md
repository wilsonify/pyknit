# Issue #46: fix: move main functions into __init__.py to fix import problem

**Status:** CLOSED
**Created:** 2022-06-08T00:37:05Z
**Updated:** 2024-01-22T22:55:29Z
**Labels:** None
**URL:** [https://github.com/terriko/pyknit/pull/46](https://github.com/terriko/pyknit/pull/46)

## Description

#43 caused some test failures that turned out to be because of a circular import.  To simplify things, I've removed pyknitter.py and just put the main math functions into __init__.py for now.

---

## Branch
Work on this issue using the branch: `issue-46`

```bash
git checkout issue-46
```

## Related Links
- [GitHub Issue](https://github.com/terriko/pyknit/issues/46)
