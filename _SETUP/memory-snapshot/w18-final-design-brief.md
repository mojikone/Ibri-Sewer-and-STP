---
name: w18-final-design-brief
description: "Engineer's brief of 2026-11-18 for the final W18 design and submission: 0.75 %, SC1-SC4, 2051/2056/2061, pumps P#/lifts P#L# naming, R8-MH report, costs folder"
metadata:
  node_type: memory
  type: project
  originSessionId: 57016b2a-e4dc-482e-953e-69a030c28ebf
  modified: 2026-11-18T17:48:33.280Z
---

The engineer's brief of 2026-11-18 for the final design and the official submission.

- **Gradient limit 0.75 % for every scenario.**
  - The SC1-2056 evidence: 23 stations (the same as the design as laid), 93.9 % of pipe above DN200 self-cleansing at 2031, against 82.6 % at 0.50 % and 98.1 % at 1.00 %.
  - The report must argue the choice from stations and lifts and from the length that self-cleanses in 2031.
- **Scenarios:**
  - SC1: STP 1 only (O1).
  - SC2: STP 16 only (O16).
  - SC3: STP 1 + STP 5 (O1 + O4).
  - SC4: STP 16 + STP 5 (O16 + O4).
- **Design years:**
  - Design each scenario for 2051, 2056 and 2061; 2056 is the base.
  - 2056 = 2031 + 25, the life cycle. The client allows designing for different years: check self-cleansing at 2031 and pick the year that reaches it as the saturation year.
  - 2051 and 2061 show the periods before and after.
- **Self-cleansing checks:**
  - Pipes above DN200 must reach 0.75 m/s at the 2031 peak.
  - Also check the 2036 flow, to see whether the pipes left over self-clean by then.
- **Station logic:**
  - Aim for 12 m, but go deeper where it saves a pump or a lift. Pumps, lifts and new stations may go to 14.65 m (about 15 m); manholes to 16.5 m.
  - This replaces the 12.65 m cap on new stations used in `reduce_stations.py`.
- **Naming** (replaces outfalls O#):
  - Pumps are P1, P2 ...; lifts are P1L1, P1L2 ...
  - Manholes are P1-M1, or P1L1-M1 inside a lift's part.
  - Pipes follow the same rule as before: prefix-P#.
  - The order follows the previous numbering.
  - A lift pumps to a nearby manhole (within one Table 12 spacing); a pump has a long force main. PAM-GUD-203 calls both pumping stations, Type 1/2/3 by design flow (p40, Table 17: duty plus standby).
- **Maps:**
  - The R7 map set and QGIS; self-cleansing velocity maps like the 0.75 % ones.
  - Leave off the joined-by-gravity dots and the force-main arrows.
  - Rising mains in QGIS are drawn from station to receiver; they had been reversed.
- **Report:** follow the team's MH report exactly, adding or changing only what must change.
  - Source: `D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Hydraulic\temp\recent updates by the team\Ibri_Concept_Design_Report_R8-MH.docx`. Work on a copy.
  - No file names, tools or internal workings in any output (official submission; check_clean gate).
- **Costs:** use `W:\2621 Design and Supervision for STP, Sewer & TE Networks System in Ibri_NAMA\06-WORKING\04-Hydraulic\11_Finacial` with the BOQ if possible; otherwise the team handles them.
- **Order of work:**
  1. Build every scenario with my own code first, and make sure it works and is optimal.
  2. Then build SewerGEMS.
  3. Deliverables: BOQ Excel, SewerGEMS projects, maps, QGIS.

**Done on 2026-11-18:** design, naming, products, maps, QGIS, BOQ, the SewerGEMS build and report R9. See W18 README, "Final design at 0.75 %".

**Traps found along the way:**
- **Lifts are pumped flow.** A lift's peak goes to the next manhole as a transfer, not re-peaked. Sizing on the uncut network undersized 99 pipes.
- **Joins can't be built as new sewers through the API.** SewerGEMS 10.4 doesn't solve join sewers created that way: 0.305 m depth, 5–7 m/s, and backwater upstream. Carry each join as a transfer instead.
- **A conduit's start/stop need not follow the flow.** Check both end nodes when reconnecting.
- **Never write PowerShell paths through Python or a bash heredoc.** In Python strings `\f` and `\b` become control characters, and a heredoc eats one leading backslash. Use the Write tool and grep for `\\VBOXSVR` before dropping a job.
- **Word refreshes cross-references on PDF export.** Updating fields in R8-MH exposes the team's dead cross-references as "Error!". Unlink those whose bookmark is gone, and export with `UpdateFieldsAtPrint` off.

**R10 (2026-11-18, the engineer: "review the entire report and update all parts"; rewrite the team's chapters, update STP/TE/OPEX costs from the flows, check TE customers per scenario, write SC4's TE):** `report_final/r10_edits.py` on top of the R9 build, `py/final_financial.py` (team's cost method), `gis/te_map_sc4.py`. SC1 recommended, SC3 alternative.

**Traps found in R10:**
- **A paragraph search over the body also finds the contents and figure lists.** Searching "C.3 Settlement Parameters" hit the TOC entry first and the cut deleted the TOC end and every list of figures. Skip TOC/TableofFigures styles in every finder.
- **The team's cross-references print "Section 0", and the caption STYLEREF printed 1 or 7 in the wrong chapters.** Write every REF as the current number, and every caption's chapter part as text, before Word; fields left to Word were not reliable here.
- **The clean gate's terms are regexes, case-sensitive.** It missed 12 "▶ CHECK:" notes, "To be updated", "[APSR ...]" placeholders and blank rate cells. "Section 0" needs `\b`, or it matches "ToR Section 03".
- **The team's chapters carry yellow highlighting (213 runs).** Strip it for an issued report.
- **Table 4-13 includes infiltration (1,099 m³/d for 1,520 km) and excludes the estates (316 m³/d).** Plant inflow = Table 4-13 + 316 − 1,099 − not conveyed + 1,079 (the 1,498 km modelled). It closes exactly to 2061; after 2064 Ibri's capacity caps the loads, so the report stops at 2061.

Related: [[w18-split-deep-subnetworks]], [[report-detail-team-level]], [[qgis-label-and-arrow-style]].
