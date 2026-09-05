# Issue #34: #9: Use pydantic type checking to ensure arguments as positive integers

**Status:** CLOSED
**Created:** 2021-05-20T23:54:14Z
**Updated:** 2021-05-21T00:14:20Z
**Labels:** None
**URL:** [https://github.com/terriko/pyknit/pull/34](https://github.com/terriko/pyknit/pull/34)

## Description

#1

Same note as in #32 
- I changed the int type to pydantic’s `PositiveInt` type. Note that when passing in a float, say 2.8, it will round it down to the nearest integer, 2. If this isn’t desired, perhaps `PositiveFloat` would be better. Or if you want to strictly enforce integers, `from pydantic import conint` and set the type to `conint(strict=True, gt=0)`. For now I've gone for `PositiveInt`.

---

## Branch
Work on this issue using the branch: `issue-34`

```bash
git checkout issue-34
```

## Related Links
- [GitHub Issue](https://github.com/terriko/pyknit/issues/34)
