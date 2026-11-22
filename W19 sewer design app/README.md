# W19 — sewer design app

A local application for sewer and stormwater network modelling and design: our own engines, an interface over them and
an AI assistant. **W18 stays the live Ibri design; W19 is a tool folder.** Spec:
`docs/2026-11-20-sewer-design-app-design.md`; plan: `docs/2026-11-20-plan-phase0-1.md`; every script and its place in
the UI: `docs/SCRIPT_REGISTER.md`; what the gates found: `docs/FINDINGS.md`.

**Clean-room:** the engines come from published methods only (PAM-GUD-201/202/203, Colebrook-White, Peltier,
Merrimack, EPA SWMM 5, public domain). Bentley's binaries are never decompiled and SewerGEMS's file formats are never
read. SewerGEMS is the referee, driven through its documented API in the offline VM, and its saved exports are what
the engine is checked against. Full statement: `docs/CLEAN_ROOM.md`.

## Start it

    cd "W19 sewer design app"
    python -m sewerapp.api            # then open http://127.0.0.1:8765 (this PC only)

Needs Python 3.12 with numpy, pandas, geopandas, shapely, pyogrio, ezdxf, fastapi, uvicorn, anthropic and swmm-toolkit
(`pip install -e ".[app]"`). The map loads MapLibre and the OpenStreetMap tiles from the internet.

**The assistant** needs `ANTHROPIC_API_KEY` as a user environment variable (set it yourself; it is never written to a
file). Without it the Assistant tab says so and everything else works. Model `claude-opus-5-5` (effort high), with a
`claude-sonnet-5-5` option; billed per token.

## What it does

- **Map** of the 12 W18 designs (SC1-SC4 × 2051/2056/2061), coloured by size, velocity, velocity at 2031, d/D,
  needs-re-lay or failing; click or shift-select pipes.
- **What-if scenarios:** copy a case, edit pipe size or gradient (one or many pipes), and the whole network re-solves
  in under 0.1 s. Inverts are held and the laid gradient kept; the edited pipe and everything downstream are flagged
  "needs re-lay" until the design chain runs. Undo, redo, compare two scenarios.
- **Profile** from any manhole to the outfall: ground, invert, crown, water surface at the peak.
- **Tools menu** (each a tested script): failing pipes, self-cleansing list, design-year check, stations, quantities,
  the whole W18 design chain (about 40 s), comparison with SewerGEMS, EPA SWMM stormwater examples.
- **Export** GeoPackage (opens in QGIS), DXF, CSV.
- **Assistant:** answers questions on a design from the solved results, explains every check with its guideline page,
  and tests a fix as a new what-if (never edits an existing scenario).

## Phase status

| Phase | State | Gate |
|---|---|---|
| 0 Foundations | **passed** 2026-11-21 | `python -m pytest -m gate_p0` |
| 1A Sanitary engine | **passed** 2026-11-21 | `python -m pytest -m gate_p1a` |
| 1B App and assistant | **passed** 2026-11-21 (live assistant test waits for the key) | `python -m pytest tests/api tests/e2e`; `-m live` with the key |
| Stormwater (SWMM) | **passed** 14 of 15 EPA models exactly; Example1 a build difference, reported | `python -m pytest -m gate_swmm` |
| 2 GVF backwater, pressure network, new SewerGEMS runs | not started | — |
| 3 Network editing on the map (add, move, delete, draw) | not started | — |
| 4–6 Rational stormwater, inlets, reports | not started | — |

All tests: `python -m pytest` — 118 passed, 1 skipped (live assistant), 2 expected failures (EPA Example1), 2 min
(2026-11-21).

## Reproduction and speed (2026-11-21)

| Check | Result |
|---|---|
| All 12 W18 cases, whole chain | identical sizes, depths within 1 mm, flows within 0.1 %, same stations, same km under 0.75 m/s, same deepest manhole |
| SC1-2056 against SewerGEMS's saved export | 19,078 pipes, 100 % within 0.1 % (largest 0.0036 %), 0 over d/D, velocity 5-95 % -0.0008 to +0.0006 m/s, 9.01 km under 0.75 m/s in both |
| In-process engine, every pipe of all 12 cases | flows and velocities to 1e-9, identical sizes |
| Design-year check | equal to W18 on all 8 cases |
| EPA SWMM examples (Example1-5, extran1-10) against EPA's benchmark | 14 of 15 equal at every time step (worst 0.0); Example1 up to 0.68 % on 13 of 468 values |
| Speed | re-solve of 19,083 pipes 0.03-0.09 s; design chain one case 38 s, 12 cases 67 s in parallel; SWMM 15 models 1.4 s (SewerGEMS: about 44 min per design) |

Saved comparisons: `docs/GATE_P1A.json`, `docs/GATE_SWMM.json`.

**Finding:** the gravity join O3 → O2-M696 (P1-P151, DN1000) runs at d/D 0.59 against 0.50 at 2056 in W18's design;
DN1200 passes. SewerGEMS never analysed it because the join was carried as a transfer. Decision for the engineer.

## Data

`tests/fixtures/` holds frozen copies of W18's inputs and outputs and SewerGEMS's SC1-2056 export (37 MB, manifest
with SHA-256), and EPA's public SWMM example inputs. EPA's reference results stay in `work/swmm_ref/`, not in git.
To rebuild them, download `benchmark-win64.zip` (21.9 MB) from github.com/USEPA/swmm-nrtestsuite, release
v2.5.0-dev, and extract the `Example_*` and `extran_*` folders' `.out` and `.rpt` files into `work/swmm_ref/`. Without
them the SWMM gate is skipped, not passed.
