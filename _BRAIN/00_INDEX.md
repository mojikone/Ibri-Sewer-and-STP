# BRAIN — Source of Truth (2621 Ibri Sewer & STP)

**Read `07_PROJECT_STATE.md` FIRST (single-file orientation: data, progress, settled doctrine, next tasks), then this index, then `02_DESIGN_CRITERIA.md` before writing any number.**

## Prime rules
1. **No invented metrics.** Every slope, velocity, depth, flow, spacing, buffer used in analysis/report MUST trace to `02_DESIGN_CRITERIA.md` (with PAM-GUD-203 page ref) or be explicitly tagged `[GAP — pending source]` in `05_GAPS.md`.
2. Scope obligations live in `01_SCOPE_REGISTER.md`. Outputs must map to scope items.
3. Data quality flags in `03_DATA_INVENTORY.md` are binding (e.g. DEM is rough DSM → no invert design from it, screening only).
4. Work happens in `../W1`, `../W2`, ... (new folder = rework iteration). BRAIN is shared across all W folders and updated as knowledge grows.
5. Report follows `Data/sample report/Sample.docx` styling (GAP-4 closed; shell used by `W2/report/make_report_r1.py`). Maps use `Hydraulic/QGIS/Layout template.qpt`.
6. Standards PDFs live in `Data/` (client set) and `_STANDARDS/` (repo, portable): PAM-GUD-201, -202, -203. Criteria refs: `p##`=203, `G1-p##`=201, `G2-p##`=202.

## Files
| File | Content |
|---|---|
| 01_SCOPE_REGISTER.md | Client scope obligations (scope.pdf) mapped to our tasks |
| 02_DESIGN_CRITERIA.md | All numeric design constraints from PAM-GUD-203 w/ page refs |
| 03_DATA_INVENTORY.md | Layers, CRS, stats, quality flags |
| 04_TOOLS.md | Repo (SWNETWROK), MCPs, environment, file conventions |
| 05_GAPS.md | Missing sources, open questions, items needing client/user input |
| 06_W2_FEEDBACK.md | Binding user feedback constraints from W1 review (maps, zones, SLS, report style) |
| 07_PROJECT_STATE.md | **START HERE** — orientation snapshot: data, doctrine, progress, key numbers, next tasks |
