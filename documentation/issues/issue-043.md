# Issue #43: Feature/logging (#38)

**Status:** CLOSED
**Created:** 2022-04-28T01:26:35Z
**Updated:** 2023-10-03T23:51:24Z
**Labels:** None
**URL:** [https://github.com/terriko/pyknit/pull/43](https://github.com/terriko/pyknit/pull/43)

## Description

I added a logging configuration to __init__.py
and raise ValueError after logging "Error:"

this implements #38 

Coincidentally, while doing that; I encountered some name collisions between pyknit  and pyknit.pyknit, so I renamed pyknit.py to pyknitter.py (I could not think of a better name for it, it just needs to be unique.)
I think this resolves #36

minimal usage:
you should really only configure the logger if your __name__ is __main__
```
from logging.config import dictConfig
from pyknit import logging_config_dict   
if __name__ == "__main__":
    dictConfig(logging_config_dict)
    main()
```    
example output:

![image](https://user-images.githubusercontent.com/26659886/165657581-f0fef89c-5a2f-4c78-af04-f7717cb67cbf.png)

![image](https://user-images.githubusercontent.com/26659886/165657628-f21eb7da-a8ed-47e1-93dd-2f0acb807ca1.png)



---

## Branch
Work on this issue using the branch: `issue-43`

```bash
git checkout issue-43
```

## Related Links
- [GitHub Issue](https://github.com/terriko/pyknit/issues/43)
