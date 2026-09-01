---
name: load-basis-locked-tier-a-volume
description: "Ibri load basis is locked — Tier A ratios set the volume, land use sets the placement, Table 12 unused"
metadata: 
  node_type: memory
  type: project
  originSessionId: 500d9f05-728a-49e7-8634-fc0d041cfafd
  modified: 2026-08-30T19:49:03.393Z
---

Locked 2026-08-30 for the rest of the 2621 Ibri project: **Tier A ratios (22 % non-domestic,
14 % governmental) set the demand VOLUME; electricity-derived land use sets its PLACEMENT.**
GUD-201 Table 12 is not used. Table 12 and the ratios must never be applied together.

**Why:** the NAMA electricity file has no land-use attribute, no floor area and no consumption
figure — only a tariff name, coordinates, and a `Wilaya` field empty on all 33,970 records. It
classifies and locates accounts but cannot size them. Table 12 is priced entirely in pupils,
beds, employees and floor area, so the §7.3.2 "shall" condition is unmet in substance rather
than merely inconvenient. Deriving those drivers from plot area × cover × storeys would stack
three assumptions to reach one number and produce false precision.

**How to apply:** quote the locked rule from `_BRAIN/02_DESIGN_CRITERIA.md` §11.1 or
PROJECT-STATE §2 item 1b. Occupancy rate is **5.32** (derived, not the old 5.0 placeholder).
Four streams stay additive outside the ratios and are not double counting: identified projects,
special consumption, tankers, private wells. Tanker water DOES generate sewage at 85 %.
Every land-use statement is our inference, never NAMA's — cite
`W9/docs/INFERENCE_REGISTER.md` in client-facing work.

Related: [[no-exemptions-in-compliance-checks]], [[hydraulics-first-verification]].
