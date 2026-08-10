# bootstrap.ps1 — one-shot environment check/restore for a fresh Claude Code instance
# Safe to re-run. Prints PASS/FIX lines; fixes what it can automatically.
$ErrorActionPreference = "Continue"
$root  = "D:\Mojtaba\Renardet\2621 Ibri Sewer STP"
$setup = Join-Path $root "Hydraulic\Claude\_SETUP"
$mem   = "$env:USERPROFILE\.claude\projects\D--Mojtaba-Renardet-2621-Ibri-Sewer-STP\memory"
Write-Host "=== Ibri 2621 bootstrap ==="

# 1. Root CLAUDE.md + .mcp.json present (restore from _SETUP copies if deleted)
foreach ($pair in @(
    @{src = Join-Path $setup "root-CLAUDE.md"; dst = Join-Path $root "CLAUDE.md"},
    @{src = Join-Path $setup "mcp.json";       dst = Join-Path $root ".mcp.json"})) {
  if (-not (Test-Path $pair.dst)) {
    Copy-Item $pair.src $pair.dst
    Write-Host ("FIXED  restored " + $pair.dst)
  } else { Write-Host ("PASS   " + $pair.dst) }
}

# 2. Auto-memory: restore snapshot if machine memory folder is empty/missing
if (-not (Test-Path $mem)) { New-Item -ItemType Directory -Force $mem | Out-Null }
$have = @(Get-ChildItem $mem -Filter *.md -ErrorAction SilentlyContinue)
if ($have.Count -eq 0) {
  Copy-Item (Join-Path $setup "memory-snapshot\*.md") $mem
  Write-Host "FIXED  auto-memory restored from snapshot"
} else { Write-Host ("PASS   auto-memory present (" + $have.Count + " files)") }

# 3. Python deps
$pyMods = "networkx","shapely","shapefile","rasterio","numpy","scipy","matplotlib","fitz","docx"
$missing = @()
foreach ($m in $pyMods) {
  python -c "import $m" 2>$null
  if ($LASTEXITCODE -ne 0) { $missing += $m }
}
if ($missing.Count -gt 0) {
  Write-Host ("FIXING pip install: " + ($missing -join ", "))
  python -m pip install --quiet networkx shapely pyshp rasterio numpy scipy matplotlib pymupdf python-docx
} else { Write-Host "PASS   python deps" }

# 4. Data paths that scripts depend on
$paths = @(
  "$root\Data\PAM-GUD-203 - Wastewater Design Guidelines v1.0.pdf",
  "$root\Data\PAM-GUD-201 - General Design Guidelines v1.0.pdf",
  "$root\Data\sample report\Sample.docx",
  "$root\Hydraulic\Terrain\DTM_terrain_mask.tif",
  "$root\Hydraulic\SHP\Landuse\Landuse.shp",
  "$root\Hydraulic\QGIS\QGIS 2621 ibri sewer stp.qgz",
  "$root\Hydraulic\Claude\W1\shp\roads_graph.shp",
  "$root\Hydraulic\Claude\W2\shp\zones.shp")
foreach ($p in $paths) {
  if (Test-Path $p) { Write-Host "PASS   $p" } else { Write-Host "MISSING $p  <-- resolve before GIS work" }
}

# 5. Git remote reachable
Set-Location (Join-Path $root "Hydraulic\Claude")
git fetch --dry-run 2>$null
if ($LASTEXITCODE -eq 0) { Write-Host "PASS   git remote reachable" } else { Write-Host "WARN   git remote not reachable (offline or auth needed: gh auth login)" }

# 6. Word COM (used for report PDF export)
try { $w = New-Object -ComObject Word.Application; $w.Quit(); Write-Host "PASS   MS Word COM" }
catch { Write-Host "WARN   MS Word COM unavailable - report PDF export needs Word" }

Write-Host "=== bootstrap complete. Reminder: open QGIS with the project .qgz so the qgis MCP connects. ==="
