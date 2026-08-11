# Issue #36: pyknit.py main() fails to run

**Status:** CLOSED
**Created:** 2021-05-21T00:36:34Z
**Updated:** 2022-05-12T18:42:43Z
**Labels:** None
**URL:** [https://github.com/terriko/pyknit/issues/36](https://github.com/terriko/pyknit/issues/36)

## Description

The `main()` function isn't working properly.

Attempt 1: in the CLI: `pyknit 'k2 p4'`:
```bash
pyKnit 0.0.3
Traceback (most recent call last):
  File "/Users/bhampson/code/learn/pycon-us-2021/pyknit/venv-3.8-jupyter/bin/pyknit", line 33, in <module>
    sys.exit(load_entry_point('pyknit', 'console_scripts', 'pyknit')())
  File "/Users/bhampson/code/learn/pycon-us-2021/pyknit/pyknit/pyknit/pyknit.py", line 213, in main
    print(pyknit.parse_written(args.instruction_row, legend))
NameError: name 'pyknit' is not defined
```

Attempt 2: Running using the venv Python interpreter: `/Users/bhampson/code/learn/pycon-us-2021/pyknit/venv-3.8-jupyter/bin/python /Users/bhampson/code/learn/pycon-us-2021/pyknit/pyknit/pyknit/pyknit.py`:
```bash
Traceback (most recent call last):
  File "/Users/bhampson/code/learn/pycon-us-2021/pyknit/pyknit/pyknit/pyknit.py", line 13, in <module>
    from pyknit import GaugeSwatch, Chart
  File "/Users/bhampson/code/learn/pycon-us-2021/pyknit/pyknit/pyknit/pyknit.py", line 13, in <module>
    from pyknit import GaugeSwatch, Chart
ImportError: cannot import name 'GaugeSwatch' from partially initialized module 'pyknit' (most likely due to a circular import) (/Users/bhampson/code/learn/pycon-us-2021/pyknit/pyknit/pyknit/pyknit.py)
```

Related error: 
https://github.com/terriko/pyknit/blame/main/pyknit/pyknit.py#L200
`parse_written` is not imported.

---

## Branch
Work on this issue using the branch: `issue-36`

```bash
git checkout issue-36
```

## Related Links
- [GitHub Issue](https://github.com/terriko/pyknit/issues/36)
