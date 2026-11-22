# W19 — sewer design app

A local application for sewer (and later stormwater) network modelling and design: our own engines, an interface over
them and an AI assistant. **W18 stays the live Ibri design; W19 is a tool folder.** Spec:
`docs/2026-11-20-sewer-design-app-design.md`; plan: `docs/2026-11-20-plan-phase0-1.md`; scripts and their UI places:
`docs/SCRIPT_REGISTER.md`.

**Clean-room:** the engines come from published methods only; Bentley's binaries are never decompiled and SewerGEMS's
file formats are never read. SewerGEMS is the referee, driven through its documented API in the offline VM. Full
statement: `docs/CLEAN_ROOM.md`.

## Phase status

| Phase | State | Gate |
|---|---|---|
| 0 Foundations | **passed** 2026-11-21 | `python -m pytest -m gate_p0` |
| 1A Sanitary engine | **passed** 2026-11-21 | `python -m pytest -m gate_p1a` |
| 1B App and assistant | in progress | `python -m pytest tests/e2e` |

## Run the tests

    python -m pytest -m "not slow"     # quick
    python -m pytest -m gate_p0        # the W18 port against W18

## Reproduction and speed (gate P1A, 2026-11-21)

| Check | Result |
|---|---|
| All 12 W18 cases (SC1-SC4 x 2051/2056/2061), whole chain | identical sizes, depths within 1 mm, flows within 0.1 %, same stations, same km under 0.75 m/s, same deepest manhole |
| SC1-2056 against SewerGEMS's saved export | 19,078 pipes compared, 100 % within 0.1 % (largest 0.0036 %), 0 over d/D limit, velocity difference 5-95 %: -0.0008 to +0.0006 m/s, 9.01 km under 0.75 m/s in both |
| In-process engine, every pipe of all 12 cases | flows and velocities to 1e-9, identical sizes |
| Speed | analysis of 19,083 pipes 0.033 s; whole chain one case 38 s; all 12 cases 67 s in parallel (SewerGEMS: about 44 min per design) |

Saved comparison: `docs/GATE_P1A.json`.
