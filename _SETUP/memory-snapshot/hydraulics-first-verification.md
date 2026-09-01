---
name: hydraulics-first-verification
description: W4+ mandate — hydraulic design correctness outranks pipeline machinery; never port donor/SWNETWROK logic on trust
metadata: 
  node_type: memory
  type: feedback
  originSessionId: c2458709-6ed2-41d1-83f3-e515ea91aff4
  modified: 2026-08-18T14:31:24.443Z
---

User mandate (2026-08-18, W4): act as senior hydraulic engineer first, pipeline builder second. Do not accept anything from the SWNETWROK donor repo without engineering review — re-derive, justify, or replace.

**Why:** the network design is the deliverable that carries professional risk; a slick pipeline around wrong hydraulics is worse than useless.

**How to apply:** every hydraulic rule/solver gets (1) clause-by-clause justification against PAM-GUD with page refs, (2) a validation gate before use — e.g. CW partial-full solver must reproduce G203 Table 11 gradients ±5%, hand-calc fixtures must match, (3) independent cross-check: SewerGEMS run must agree with pipeline results pipe-by-pipe within 5%. Regime written into `W4/docs/PLAN.md` §3b. Related: [[figma-flowcharts-for-docs]], [[plain-wording-not-literary]].
