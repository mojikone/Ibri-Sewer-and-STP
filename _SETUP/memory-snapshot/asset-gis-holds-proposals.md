---
name: asset-gis-holds-proposals
description: An asset GIS may hold proposed alignments beside built ones — filter on status before quoting any length
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 500d9f05-728a-49e7-8634-fc0d041cfafd
  modified: 2026-09-01T04:13:38.455Z
---

Before quoting a length, a count or a coverage figure from a client's asset
GIS, check whether the dataset holds proposals as well as built assets. In the
Ibri wastewater data the `OP_STATUE` field splits it in two, and four further
fields agree on every record: `INSTALLDAT`, `SOURCE`, `PROJECTCOD`, `REMARKS`.
Built carries a date and a drawing or CCTV source; proposed carries an
asset-planning source and a planning project code.

**Why:** Revision 0 of the Concept Design Report was issued to the client
saying 310.9 km of gravity sewer and 45.7 km of treated effluent main existed.
The true figures are 111.6 km built and no treated effluent asset at all. The
user spotted it from site knowledge ("I heard rumours it was built in 2006"),
not from the data — the correction should have come from reading the
attributes in the first place.

**How to apply:** filter on the status field first, measure second, and state
the two figures separately wherever either is quoted. Extend the same suspicion
to any client dataset that mixes record types in one layer. Related:
[[no-exemptions-in-compliance-checks]], [[hydraulics-first-verification]].
