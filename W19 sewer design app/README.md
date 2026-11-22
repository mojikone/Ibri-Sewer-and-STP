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
| 0 Foundations | in progress | `python -m pytest -m gate_p0` |
| 1A Sanitary engine | not started | `python -m pytest -m gate_p1a` |
| 1B App and assistant | not started | `python -m pytest tests/e2e` |

## Run the tests

    python -m pytest -m "not slow"     # quick
    python -m pytest -m gate_p0        # the W18 port against W18
