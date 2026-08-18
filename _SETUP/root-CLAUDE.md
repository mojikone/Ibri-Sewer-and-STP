# CLAUDE.md — Project Root Bootstrap (2621 Ibri Sewer, TE & STP)

You are continuing an ongoing engineering project. A previous Claude Code instance built a complete knowledge base and delivery pipeline here. **Do not start from scratch and do not re-derive anything — load the existing sources in this exact order before any work:**

1. `Hydraulic/Claude/CLAUDE.md` — working rules, folder map, current state. Follow it as if it were this file.
2. `Hydraulic/Claude/_BRAIN/` — **`07_PROJECT_STATE.md` FIRST** (single-file orientation: data, doctrine, progress, next tasks), then ALL other files. `02_DESIGN_CRITERIA.md` is the only permitted source of numeric design values (PAM-GUD-203/-201/-202, cited by page). Inventing metrics is prohibited.
3. `Hydraulic/Claude/_SETUP/ENVIRONMENT.md` — tools, MCP servers, dependencies, how to re-run pipelines.
4. Auto-memory: if the session shows no recalled memories, read `Hydraulic/Claude/_SETUP/memory-snapshot/` and treat it as project memory (it mirrors `~/.claude/projects/D--Mojtaba-Renardet-2621-Ibri-Sewer-STP/memory/`).
5. `Hydraulic/Claude/_SETUP/global-CLAUDE.md` — the user's global operating instructions (advisor tone, confidence tags, **[PRESERVE-CHECK] before modifying existing code**, no-push rule). If `~/.claude/CLAUDE.md` is not already loaded in this session, follow this copy as if it were.

## First session on this subscription — run once
```
powershell -ExecutionPolicy Bypass -File "Hydraulic/Claude/_SETUP/bootstrap.ps1"
```
It verifies python/node dependencies, restores auto-memory from the snapshot if missing, ensures `.mcp.json` is in place, and reports anything broken. Fix what it reports before proceeding.

## Runtime facts
- The `qgis` MCP server needs QGIS open with `Hydraulic/QGIS/QGIS 2621 ibri sewer stp.qgz` loaded (qgis_mcp plugin). If tools `mcp__qgis__*` are absent, ask the user to open QGIS — do not work around it with blind file edits to the .qgz.
- Git repo root is `Hydraulic/Claude/` (remote: github.com/mojikone/Ibri-Sewer-and-STP, branch main). Commit per logical change; **never push without an explicit user instruction to push**.
- Iterations: work in `Hydraulic/Claude/W#` folders — a rework request means create the next `W#`. Current latest: **W3** (analyses); next planned: **W4 — test-boundary network design**.
- Client data (`Data/`, `Hydraulic/Terrain/`, `Hydraulic/SHP/`, `Hydraulic/Imagery/`) lives in this folder tree and is NOT in git — never move or modify it (Imagery = Claude-downloaded Esri tiles/mosaic; licensing: never push imagery to the repo).
- User style: concise replies, bullets and tables; challenge before agreeing; cite standards with page refs.
