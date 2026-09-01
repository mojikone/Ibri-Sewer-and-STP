---
name: no-exemptions-in-compliance-checks
description: A compliance check must never carry an exemption clause; the user reads a PASS as compliance
metadata: 
  node_type: memory
  type: feedback
  originSessionId: c2458709-6ed2-41d1-83f3-e515ea91aff4
  modified: 2026-08-19T18:51:33.521Z
---

Never write an exemption into a design-code check. On 2026-08-19 the user asked "why do you have
manholes deeper than 12 metres (21.3)?" — the audit's max-depth check was skipping any chamber
flagged `sls_pocket`, and the same run then dismissed those pockets as too small to justify a
pumping station. Two get-outs in series produced 71 chambers between 12 m and 21.3 m deep, with
no pump and a compliance table reading PASS.

**Why:** the user reads the audit table as the statement of compliance. An exemption inside a
check does not weaken the check a little — it silently deletes the rule, and the deeper the
design goes the more confident the report looks. The user also said plainly: "we can't remove
pumps at any cost" — a constraint may not be met by moving the cost somewhere unmeasured.

**How to apply:** a limit from a guideline is checked on every element, whatever flags that
element carries, and along the span between elements as well as at the elements. If a rule
cannot be met by geometry, the answer is the physical measure the guideline intends (here a
pumping station), reported with its cost — never a wider tolerance and never a skipped row.
Write a regression test that sets every flag which used to excuse the element and asserts the
check still fails. Related: [[hydraulics-first-verification]].
