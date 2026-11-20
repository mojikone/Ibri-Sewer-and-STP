---
name: sewergems-new-year-alternative-copy
description: "SewerGEMS 10.4 API - a new sanitary-loading year alternative must be a Copy(id) of a loaded one, never Add(parent)"
metadata:
  node_type: memory
  type: reference
  originSessionId: 57016b2a-e4dc-482e-953e-69a030c28ebf
  modified: 2026-11-17T20:04:15.157Z
---

In the SewerGEMS 10.4 API (OpenFlows/Haestad), make a new year alternative with `IModelingElementManager.Copy(loadedAltId)` on the sanitary-loading alternative manager. The copy is a top-level sibling (parent 0) that carries its own records, so `YearLoads.SetYear` can fill it. Job 072 (2026-11-17) made seven this way from alternative 14 in `IBRI_W18_R4.stsw`, and every year stored = file.

Never use `Add(parentId)` for this. Jobs 060–065 showed that a new child with no local records cannot be read once a sibling holds records: `GetParentID` fails with "Value does not fall within the expected range". That holds even with all the alternatives created first, and even after reopening the model.

Related: the VM bridge rules in the global CLAUDE.md, and `W18…/sewergems_api/jobs/072_w18_R4_years_2031_2091.ps1`.
