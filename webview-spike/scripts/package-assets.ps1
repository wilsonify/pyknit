#Requires -Version 5.1
<#
.SYNOPSIS
  Stage the existing demos/ web app + offline runtime into the WebView
  prototype's assets (no Chaquopy, no rewrite, no network at runtime).
#>
$ErrorActionPreference = 'Stop'
$Root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
# When run from repo root the layout is <root>/webview-spike/scripts; be tolerant:
if (-not (Test-Path "$Root/demos")) { $Root = (Get-Location).Path }
$Dist = "$Root/webview-spike/app/src/main/assets/dist"
Write-Host "Staging web assets from $Root into $Dist"

$needs = @('build/pyodide/pyodide.mjs', 'build/pyscript/core.js', 'build/wheels', 'demos/index.html')
foreach ($n in $needs) {
  if (-not (Test-Path "$Root/$n")) { throw "Missing $n - run the runtime-cache/wheel build first (see webview-spike/README.md)." }
}

New-Item -ItemType Directory -Path $Dist -Force | Out-Null
# HTML demos (index + 14 tools)
Copy-Item "$Root/demos/index.html" "$Dist/index.html" -Force
foreach ($d in Get-ChildItem "$Root/demos" -Directory) {
  if ($d.Name -eq '_assets') { continue }
  if (Test-Path "$($d.FullName)/demo.html") {
    New-Item -ItemType Directory -Path "$Dist/$($d.Name)" -Force | Out-Null
    Copy-Item "$($d.FullName)/demo.html" "$Dist/$($d.Name)/demo.html" -Force
    Get-ChildItem "$($d.FullName)/*.js" -ErrorAction SilentlyContinue | Copy-Item -Destination "$Dist/$($d.Name)/" -Force
  }
}
# Shared JS + CSS
New-Item -ItemType Directory -Path "$Dist/_shared" -Force | Out-Null
Copy-Item "$Root/demos/_shared/*.js" "$Dist/_shared/" -Force -ErrorAction SilentlyContinue
Copy-Item "$Root/demos/_assets/common.css" "$Dist/common.css" -Force -ErrorAction SilentlyContinue
# Offline runtime (the whole point: no CDN at runtime)
foreach ($dir in @('pyscript', 'pyodide', 'wheels')) {
  New-Item -ItemType Directory -Path "$Dist/$dir" -Force | Out-Null
  Copy-Item "$Root/build/$dir/*" "$Dist/$dir/" -Recurse -Force
}
New-Item -ItemType Directory -Path "$Dist/wheel" -Force | Out-Null
Copy-Item "$Root/build/wheel/*.whl" "$Dist/wheel/" -Force
# Smoke page (tiny Pyodide boot test, uses same ../pyodide files)
New-Item -ItemType Directory -Path "$Dist/smoke" -Force | Out-Null
Copy-Item "$Root/webview-spike/smoke/pyodide-smoke.html" "$Dist/smoke/pyodide-smoke.html" -Force

# Rewrite absolute server-root paths to relative ones so the asset-loader
# origin (https://appassets.androidplatform.net/dist/...) resolves locally.
Get-ChildItem $Dist -Recurse -Filter *.html | ForEach-Object {
  $t = Get-Content $_.FullName -Raw
  $t = $t -replace '/_assets/pyscript/', '../pyscript/'
  $t = $t -replace '/_assets/pyodide/', '../pyodide/'
  $t = $t -replace '/_assets/wheels/', '../wheels/'
  $t = $t -replace '/_assets/common.css', '../common.css'
  $t = $t -replace '/_assets/', '../'
  $t = $t -replace '/_wheel/', '../wheel/'
  $t = $t -replace 'href="/index.html"', 'href="../index.html"'
  $t = $t -replace 'href="/', 'href="../'
  Set-Content $_.FullName $t -NoNewline
}
# Root index.html lives at dist/ (not dist/<tool>/), so ../ would escape dist.
# Rewrite its refs from ../ to ./ after the blanket pass above.
$RootIndex = Join-Path $Dist 'index.html'
if (Test-Path $RootIndex) {
  $t = Get-Content $RootIndex -Raw
  $t = $t -replace '\.\./pyscript/', './pyscript/'
  $t = $t -replace '\.\./pyodide/', './pyodide/'
  $t = $t -replace '\.\./wheels/', './wheels/'
  $t = $t -replace '\.\./wheel/', './wheel/'
  $t = $t -replace '\.\./common.css', './common.css'
  Set-Content $RootIndex $t -NoNewline
}
$mb = [math]::Round(((Get-ChildItem $Dist -Recurse -File | Measure-Object Length -Sum).Sum / 1MB), 1)
Write-Host ("Staged " + @(Get-ChildItem $Dist -Recurse -File).Count + " files, " + $mb + " MB into " + $Dist)
Write-Host 'Next: build the wrapper APK (see webview-spike/README.md).'
