# BRAIN — Source of Truth (2621 Ibri Sewer & STP)

**Read this folder before ANY analysis, script, map, or report work. Re-check `02_DESIGN_CRITERIA.md` before writing any number.**

## Prime rules
1. **No invented metrics.** Every slope, velocity, depth, flow, spacing, buffer used in analysis/report MUST trace to `02_DESIGN_CRITERIA.md` (with PAM-GUD-203 page ref) or be explicitly tagged `[GAP — pending source]` in `05_GAPS.md`.
2. Scope obligations live in `01_SCOPE_REGISTER.md`. Outputs must map to scope items.
3. Data quality flags in `03_DATA_INVENTORY.md` are binding (e.g. DEM is rough DSM → no invert design from it, screening only).
4. Work happens in `../W1`, `../W2`, ... (new folder = rework iteration). BRAIN is shared across all W folders and updated as knowledge grows.
5. Report follows `Data/sample report` styling — **currently EMPTY → styling unresolved, see 05_GAPS**. Maps use `Hydraulic/QGIS/Layout template.qpt`.

## Files
| File | Content |
|---|---|
| 01_SCOPE_REGISTER.md | Client scope obligations (scope.pdf) mapped to our tasks |
| 02_DESIGN_CRITERIA.md | All numeric design constraints from PAM-GUD-203 w/ page refs |
| 03_DATA_INVENTORY.md | Layers, CRS, stats, quality flags |
| 04_TOOLS.md | Repo (SWNETWROK), MCPs, environment, file conventions |
| 05_GAPS.md | Missing sources, open questions, items needing client/user input |
