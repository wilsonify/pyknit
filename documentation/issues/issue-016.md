# Issue #16: Improve Jupyter-lab setup instructions

**Status:** CLOSED
**Created:** 2021-05-16T21:01:56Z
**Updated:** 2021-05-16T21:21:57Z
**Labels:** None
**URL:** [https://github.com/terriko/pyknit/issues/16](https://github.com/terriko/pyknit/issues/16)

## Description

In the setup, the first two lines are:

```
virtualenv -p python 3.8 venv-3.8-jupyter
source ~/venv-3.8-jupyter/bin/activate
```

1. I think it should be `python3.8` not `python 3.8`
2. I think it would be better to be `source venv-3.8-jupyter/bin/activate` without the `~/`, seeing as most people probably won't set up the virtualenv in `~/`

---

## Branch
Work on this issue using the branch: `issue-16`

```bash
git checkout issue-16
```

## Related Links
- [GitHub Issue](https://github.com/terriko/pyknit/issues/16)
