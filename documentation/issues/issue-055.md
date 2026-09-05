# Issue #55: Compatibility with Python>=3.12

**Status:** OPEN
**Created:** 2026-04-30T02:29:22Z
**Updated:** 2026-04-30T02:30:18Z
**Labels:** None
**URL:** [https://github.com/terriko/pyknit/pull/55](https://github.com/terriko/pyknit/pull/55)

## Description

Per #54, if this is welcome! This PR does three things:

- Migrates `requirements.txt` to the `[project]` table of `pyproject.toml`. Fixes `ModuleNotFoundError` for Pydantic on 3.12 and 3.13.
- Updates the packaging workflow to include 3.12/3.13 and upgrades to checkout@v4 and setup-python@v5
- Fixes `SyntaxWarning` in `Chart.py` by removing backslashes from `"\japanese"`

This all came from cloning pyKnit locally to Debian Linux Trixie with system Python 3.13. I also tested my fixes in a venv with 3.12.11. On cloning, I set up my environment with

```
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
pip install -r requirements
```
which skips pydantic, somehow:

```
Python 3.13.5 (main, Jun 25 2025, 18:55:22) [GCC 14.2.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> import pyknit
Traceback (most recent call last):
  File "<python-input-0>", line 1, in <module>
    import pyknit
  File "/home/sailorfe/s/pyknit/pyknit/__init__.py", line 13, in <module>
    from pydantic import PositiveInt, validate_arguments
ModuleNotFoundError: No module named 'pydantic'
```

And the `SyntaxWarning` after fixing this Pydantic problem was:

```
/home/sailorfe/s/pyknit/pyknit/Chart.py:104: SyntaxWarning: invalid escape sequence '\j'
  symbol=os.path.join(symbol_dir + "\japanese", "no-stitch.png"), width=1),
/home/sailorfe/s/pyknit/pyknit/Chart.py:107: SyntaxWarning: invalid escape sequence '\j'
  symbol=os.path.join(symbol_dir + "\japanese", "box.png"), width=1),
/home/sailorfe/s/pyknit/pyknit/Chart.py:110: SyntaxWarning: invalid escape sequence '\j'
  symbol=os.path.join(symbol_dir + "\japanese", "ktbl.png"), width=1),
/home/sailorfe/s/pyknit/pyknit/Chart.py:113: SyntaxWarning: invalid escape sequence '\j'
  symbol=os.path.join(symbol_dir + "\japanese", "k2tog.png"), width=1),
/home/sailorfe/s/pyknit/pyknit/Chart.py:116: SyntaxWarning: invalid escape sequence '\j'
  symbol=os.path.join(symbol_dir + "\japanese", "k3tog.png"), width=1),
/home/sailorfe/s/pyknit/pyknit/Chart.py:119: SyntaxWarning: invalid escape sequence '\j'
  symbol=os.path.join(symbol_dir + "\japanese", "k4tog.png"), width=1),
/home/sailorfe/s/pyknit/pyknit/Chart.py:122: SyntaxWarning: invalid escape sequence '\j'
  symbol=os.path.join(symbol_dir + "\japanese", "yarn_over.png"), width=1),
/home/sailorfe/s/pyknit/pyknit/Chart.py:125: SyntaxWarning: invalid escape sequence '\j'
  symbol=os.path.join(symbol_dir + "\japanese", "byo.png"), width=1),
/home/sailorfe/s/pyknit/pyknit/Chart.py:128: SyntaxWarning: invalid escape sequence '\j'
  symbol=os.path.join(symbol_dir + "\japanese", "purl.png"), width=1),
/home/sailorfe/s/pyknit/pyknit/Chart.py:131: SyntaxWarning: invalid escape sequence '\j'
  symbol=os.path.join(symbol_dir + "\japanese", "ptbl.png"), width=1),
/home/sailorfe/s/pyknit/pyknit/Chart.py:134: SyntaxWarning: invalid escape sequence '\j'
  symbol=os.path.join(symbol_dir + "\japanese", "p2tog.png"), width=1),
/home/sailorfe/s/pyknit/pyknit/Chart.py:137: SyntaxWarning: invalid escape sequence '\j'
  symbol=os.path.join(symbol_dir + "\japanese", "ssk.png"), width=1),  # left leaning decrease
/home/sailorfe/s/pyknit/pyknit/Chart.py:140: SyntaxWarning: invalid escape sequence '\j'
  symbol=os.path.join(symbol_dir + "\japanese", "ssk.png"), width=1),  # left leaning decrease
/home/sailorfe/s/pyknit/pyknit/Chart.py:143: SyntaxWarning: invalid escape sequence '\j'
  symbol=os.path.join(symbol_dir + "\japanese", "ssp.png"), width=1),
/home/sailorfe/s/pyknit/pyknit/Chart.py:146: SyntaxWarning: invalid escape sequence '\j'
  symbol=os.path.join(symbol_dir + "\japanese", "sk2togp"), width=1),
/home/sailorfe/s/pyknit/pyknit/Chart.py:149: SyntaxWarning: invalid escape sequence '\j'
  symbol=os.path.join(symbol_dir + "\japanese", "sl2kp2.png"), width=1),
/home/sailorfe/s/pyknit/pyknit/Chart.py:152: SyntaxWarning: invalid escape sequence '\j'
  symbol=os.path.join(symbol_dir + "\japanese", "s3kp3"),width=1),
/home/sailorfe/s/pyknit/pyknit/Chart.py:155: SyntaxWarning: invalid escape sequence '\j'
  symbol=os.path.join(symbol_dir + "\japanese", "C1-1L.png"), width=2),
/home/sailorfe/s/pyknit/pyknit/Chart.py:158: SyntaxWarning: invalid escape sequence '\j'
  symbol=os.path.join(symbol_dir + "\japanese", "C1-1R.png"), width=2),
/home/sailorfe/s/pyknit/pyknit/Chart.py:161: SyntaxWarning: invalid escape sequence '\j'
  symbol=os.path.join(symbol_dir + "\japanese", "C1-1PL.png"), width=2),
/home/sailorfe/s/pyknit/pyknit/Chart.py:164: SyntaxWarning: invalid escape sequence '\j'
  symbol=os.path.join(symbol_dir + "\japanese", "C1-1PR.png"), width=2),
/home/sailorfe/s/pyknit/pyknit/Chart.py:167: SyntaxWarning: invalid escape sequence '\j'
  symbol=os.path.join(symbol_dir + "\japanese", "C4L.png"), width=4),
/home/sailorfe/s/pyknit/pyknit/Chart.py:170: SyntaxWarning: invalid escape sequence '\j'
  symbol=os.path.join(symbol_dir + "\japanese", "C4R.png"), width=4),
```

This could also be fixed with raw strings like `r"\japanese"` or in a more involved update, PathLib instead of `os.path.join`.

---

## Branch
Work on this issue using the branch: `issue-55`

```bash
git checkout issue-55
```

## Related Links
- [GitHub Issue](https://github.com/terriko/pyknit/issues/55)
