# Issue #38: Convert error messages from print statements to error statements

**Status:** CLOSED
**Created:** 2021-05-24T20:14:24Z
**Updated:** 2022-05-12T18:43:17Z
**Labels:** hacktoberfest
**URL:** [https://github.com/terriko/pyknit/issues/38](https://github.com/terriko/pyknit/issues/38)

## Description

Currently, the pyknit error messages are all print statements that go to standard io.  Before we get too entrenched in our ways, it might be nice to change them to "proper" error messages.  (I don't really think anyone cares too much at this stage, but I'd like to model best practices)

Likely options:
1. Use the logging facility for errors: https://docs.python.org/3/library/logging.html
2. Raise exceptions and handle them per https://docs.python.org/3/tutorial/errors.html

Other projects i'm on use a combo of both.  However, part of the fun of having a tiny project is being able to try new things, so if there's any brilliant new error handling system we might want to check out, this issue is a good place to mention it.

---

## Branch
Work on this issue using the branch: `issue-38`

```bash
git checkout issue-38
```

## Related Links
- [GitHub Issue](https://github.com/terriko/pyknit/issues/38)
