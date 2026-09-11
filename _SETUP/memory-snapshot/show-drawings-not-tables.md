---
name: show-drawings-not-tables
description: The user finds real defects by opening drawings; put KMZ/DXF in front of them early instead of reporting metric tables
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 746a29e0-6af6-4464-8fd5-c6fe1c4d438a
  modified: 2026-09-07T08:49:46.415Z
---

Give the user something to **look at** early, not a table of metrics. He opens the drawing
and finds things no automated check catches.

On 2026-09-06/07 he found, by eye, in minutes: 777.7 km of pipe missing from a DXF (the
export publishes reaches in two layers and the drawing read one); 11,707 chambers published
with an invert above their own ground; manholes visibly too close together; and a pumping
station in an area where two earlier designs need none. A 34-check audit suite, run against
the same layers, found **none of those four**.

**Why:** checks answer questions someone thought to ask. A drawing shows everything at once,
and an engineer reading it brings a model of what the ground should look like that no check
encodes.

**How to apply:**
- Ship a lightweight KMZ or DXF *before* the metrics are polished, not after. Under ~2 MB
  opens; group features per subnetwork rather than one placemark each.
- When reporting a trend table, expect it to be measuring the wrong thing. His judgement that
  "the design is getting worse" was right while every metric in my table said the opposite —
  because the metrics were full-area aggregates and the comparable measurement was on one
  small area where an earlier design could be scored against it.
- Never send a drawing without saying what is known-wrong in it, and never let a layer name
  merge two meanings (a plot that *cannot connect* and a plot that *could not be checked*
  are different findings and must be different layers).

Related: [[no-exemptions-in-compliance-checks]], [[hydraulics-first-verification]],
[[plain-wording-not-literary]]
