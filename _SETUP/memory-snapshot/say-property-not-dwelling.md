---
name: say-property-not-dwelling
description: "Use \"property\" (the team's agreed term, as in their Residential Properties per Plot), never \"dwelling\""
metadata:
  node_type: memory
  type: feedback
  originSessionId: 57016b2a-e4dc-482e-953e-69a030c28ebf
  modified: 2026-11-19T11:06:11.592Z
---

Say **property**, not dwelling: "properties per growth plot", "future residential properties".

**Why:** the engineer, 2026-11-17: "instead of dwelling use property as agreed". The team's sheet (MOHUP DATA - NA) counts Residential Properties and Properties per Plot; one domestic meter = one property.

**How to apply:** in replies, maps, tables, new fields, and the team's text copied into a report as well. On 2026-11-19 he asked "why you're still using dwelling" after I quoted the team's "dwelling at 380 m" in a reply and R11 still carried it in six places. The R11 build now rewrites it, and `report_final/forbidden_terms.txt` bans it, so the clean gate fails on it. Older W18 outputs (plot_layer_check.md column "dwellings ... per growth plot") still say dwelling; rename when next rebuilt. Related: [[nws-basis-change-nov-2026]].
