import pathlib, re
dist = pathlib.Path("webview-spike/app/src/main/assets/dist")
missing = []
for f in dist.rglob("*.html"):
    t = f.read_text(encoding="utf-8", errors="replace")
    for m in re.finditer(r'"(\.\./[^"]+\.(?:mjs|js|css|wasm|whl|zip|json|png))"', t):
        rel = m.group(1)
        p = (f.parent / rel).resolve()
        if not p.exists():
            missing.append((str(f), rel))
print("missing local refs:", len(missing))
for f, r in missing[:20]:
    print(f, "->", r)
total = sum(p.stat().st_size for p in dist.rglob("*") if p.is_file())
print("dist size MB:", round(total / 1e6, 1))
print("dist files:", sum(1 for _ in dist.rglob("*") if _.is_file()))
