# What is current, and what is not — checked 2026-08-19

Read this before trusting any file in the repo. The job has grown, so this page says
plainly which document is live and which is a record of past work.

## Live — use these

| File | What it holds | Last checked |
|---|---|---|
| `CLAUDE.md` | working rules, folder map, current state | 2026-08-19 |
| `_BRAIN/07_PROJECT_STATE.md` | the one-page orientation: data, doctrine, progress | 2026-08-19 |
| `_BRAIN/02_DESIGN_CRITERIA.md` | every design number with its guideline page | 2026-08-19 |
| `W5/docs/CRITERIA_UPDATE_R1.md` | the register of rules agreed 18–19 Aug and what is built | 2026-08-19 |
| `W5/docs/WHAT_CHANGED.md` | plain-words summary of the current run | 2026-08-19 |
| `W5/report/W5_Sewer_Network_Design.docx / .pdf` | the current report, numbers read live from the run | 2026-08-19 |
| `W5/py/` | the design code that produced the current outputs | 2026-08-19 |
| `W5/shp/ dxf/ img/ sewergems/` | the current design outputs | 2026-08-19 |
| `TUTORIALS/T01…docx` | how the flow and load are worked out — **Rev 4** | 2026-08-19 |

## Superseded — keep for the record, do not quote as current

| File | Why it is out of date |
|---|---|
| `W4/**` (all of it) | W4 was the first design pipeline. W5 replaces it. The one live file is `W4/shp/ELE_accounts.shp`, which W5 still reads |
| `W4/report/*`, `W4/docs/METHODOLOGY.md`, `W4/docs/PLAN.md` | describe the W4 design: 1,655 chambers, 89.5 km, one property per plot, OR 6.0 |
| `W2/report/*` | the R1 concept screening report, built on 36 zones and OR 6.0 |
| `W3/analysis/*` | still valid as analysis, but every population figure uses OR 6.0 and one property per plot — rescale before reuse |
| `TUTORIALS/T01…pdf` | **PDF is still Rev 3** — Word was open when Rev 4 was built, so only the .docx was refreshed. Re-export when Word is free |

## Numbers that changed, so old documents disagree with new ones

| Item | Old (W1–W4) | Now (W5) |
|---|---|---|
| People per property | 6.0 assumed | **5.0**, set by the client team |
| Properties per plot | 1.0 assumed | **counted from electricity accounts**, 1.4 average |
| Farms | no sewage load at all | **the farming carries none, the houses on it do** |
| Dual carriageways | merged into one corridor | **excluded entirely**, trunk included |
| Sewage per plot | 1.03 m³/day | **0.86 m³/day per property**, several properties per plot |
| Road source | `W1/shp/roads_study.shp` | `SHP/Road centerline 2` with the `dual` column |

## Still open

| Item | Waiting on |
|---|---|
| Drag value for self-cleaning (1 Pascal assumed) | NWS — 1,124 pipes need steeper gradients if it is 2 |
| Plastic pipe wall class | NWS / PAM-SPC-207 |
| Floor areas, staff and pupil numbers | derived for now; colleague's treated land-use data will replace them |
| Junction inlet angles | design work in W6 |
| The trunk line | your drawing; the side networks then grow into it |
| SewerGEMS comparison | your model run against the package in `W5/sewergems/` |
