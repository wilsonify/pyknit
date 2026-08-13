"""Inventory public names available in the PyPI pyknit 0.0.9 wheel."""
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

WHL = r"C:\Users\toman\AppData\Local\Temp\opencode\pyknit_pypi\pyknit-0.0.9-py3-none-any.whl"
z = zipfile.ZipFile(WHL)

import re

for name in z.namelist():
    if not name.endswith(".py") or name in ("pyknit/__init__.py",):
        continue
    src = z.read(name).decode("utf-8")
    funcs = sorted(set(re.findall(r"^def (\w+)", src, re.M)))
    classes = sorted(set(re.findall(r"^class (\w+)", src, re.M)))
    print(f"=== {name} ===")
    print("  classes:", classes)
    print("  funcs  :", funcs)

# __init__ names
src = z.read("pyknit/__init__.py").decode("utf-8")
funcs = sorted(set(re.findall(r"^def (\w+)", src, re.M)))
imports = sorted(set(re.findall(r"^from pyknit\.[A-Za-z_]+ import ([\w, \*]+)", src, re.M)))
print("=== pyknit/__init__.py ===")
print("  funcs:", funcs)
print("  module imports:", imports)