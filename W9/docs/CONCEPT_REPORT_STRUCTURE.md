# Concept Design Report — proposed structure for NWS approval

**Project** T/2719110/2025 — Consultancy Services for Design and Supervision for STP, Sewer & TE Networks Systems in Ibri
**Status** Draft structure. The TOR requires this to be approved before the report is written: *"The Consultant shall submit complete concept design report structure for approval according to that will submit comprehensive concept report"* (Scope of Work, p63 of 204).

---

## Why the structure matters commercially

| Fact | Source |
|---|---|
| Concept Design is **60 days** plus a separate **21-day** NWS review | Tender p147, restated as a contract term p177 |
| **15–20 % of the design fee** is released on NWS approval of the Concept Design | Tender p153 (Option I), p154 (Option II) |
| Delay is charged at **1 % of the Design Stage Contract Value per week**, capped at 10 % of contract value | Tender p151, p180, p193 |
| Preliminary Design starts only **after STP concept approval** — the STP concept is independently on the critical path | Tender p148, p178 |
| The concept fee certifies in **three separable parts**: A1 As-Built & GIS (optional, 52,100 OMR), A2 Sewer & TE concept (83,105), A3 STP concept (64,500) | Financial proposal p7; tender p156–157 |

The report must therefore be a self-contained, formally approvable document whose sections map cleanly onto A1, A2 and A3 so each can be certified independently.

---

## Two terminology problems to fix before drafting

**1. "TE" means Trade Effluent in the governing guidelines.** G201-p16 and G203-p13 define **TE = Trade Effluent** and **TSE = Treated Sewage Effluent**. This project, the TOR and the tender all use "TE" to mean treated effluent. A report saying "TE network" will be read by a guideline-literate NWS reviewer as a trade-effluent network. Either adopt TSE throughout with a one-line note, or open the report with an explicit definition that overrides the guideline abbreviation. Do not leave it ambiguous.

**2. The TOR cites a manual section that no longer exists.** The TOR requires the STP location report to follow *"item 2.1 in WASTEWATER DESIGN MANUAL Section 05"*. PAM-GUD-203 Rev.01 (March 2026) merged the former AM-ENG-WDM-03 to -07 into one document and renumbered (G203-p2). There is no Section 05 and no item 2.1. The equivalent content is now **G203 §10.1, Site Selection, p63–64**. Confirm the mapping with NWS in writing rather than assuming it.

**3. The governing definition of concept content is G201, not G203.** G201 §1.6 and **Table 2 "Minimum contents required for each Design Phase" (p19–22)** is the phase-by-phase deliverable matrix. Everything else is subordinate. G201-p17 also requires that *"the designer should validate the scope and content of the design with the NAMA representative before proceeding at each design stage"* — which is the guideline basis for submitting this structure.

---

## Proposed structure

The third column names the section of **Tutorial T03 Revision 01** that carries the method, the equations and their source pages for that part of the work. A dash marks a section for which the methodology document does not yet carry a method.

| | Section | Method in T03 Rev 01 |
|---|---|---|
| **Front matter** | | |
| F1 | Document control |  |
| F2 | Authorship and discipline signatures |  |
| F3 | Abbreviations and definitions | Front matter |
| F4 | Executive summary |  |
| **Part A** | **Project, scope and process** | |
| 1 | Introduction, background and RG Master Plan context |  |
| 2 | Scope and boundaries |  |
| 3 | Programme, design stage gates and deliverables |  |
| 4 | Meetings, consultation and decisions record |  |
| 5 | Quality plan and HSE plan |  |
| **Part B** | **Data** | |
| 6 | Data collection register | 3 |
| 7 | Data validation and adequacy assessment | 3 |
| 8 | Survey, geotechnical investigation and trial pits | 13 |
| 9 | Existing systems — as-built and GIS | 15 |
| **Part C** | **Basis of design** | |
| 10 | Codes, standards and the deviations register | 22 |
| 11 | Level of service, resilience and contingency | — |
| 12 | Design criteria — networks | 9, 11 |
| 13 | Design criteria — STP and process | 16 |
| **Part D** | **Demand and flows** | |
| 14 | Population and land use | 3, 4 |
| 15 | Wastewater generation and design flows | 5, 6, 7, 8 |
| 16 | Trade effluent and industrial contributions | 16.4 |
| 17 | Treated effluent demand and customers | 17 |
| **Part E** | **Existing system** | |
| 18 | Hydraulic assessment of existing networks | 14, 15 |
| 19 | Rehabilitation and upgrading | 15 |
| 20 | RG Master Plan verification | 4, 7 |
| **Part F** | **Options** | |
| 21 | Options methodology, including the proposed approach per option | 21 |
| 22 | Sewer network options | 9, 10 |
| 23 | Pumping and lifting stations, force mains, surge | 11, 12 |
| 24 | Treated effluent network options | 17 |
| 25 | STP options — technology, siting, phasing | 16 |
| 26 | Excess effluent, emergency provisions, tankers | 16.8 |
| 27 | Sludge management strategy | 18 |
| **Part G** | **Assessment and appraisal** | |
| 28 | Ground model and geotechnical report | 13 |
| 29 | Flood protection assessment | 16.9 |
| 30 | Odour assessment and buffer derivation | 12, 16.9 |
| 31 | Climate resilience | — |
| 32 | Environmental and social assessment, EIA scoping | — |
| 33 | Utility interfaces and the NOC register | 13 |
| 34 | Sustainability — carbon, circular economy, ICV | 20.5 |
| 35 | Cost — CAPEX, OPEX, life cycle cost | 19, 20 |
| 36 | Risk register | 20.6 |
| 37 | Value engineering study | 21.5 |
| 38 | Multi-criteria results and recommendation | 21.4 |
| **Part H** | **Delivery** | |
| 39 | Implementation roadmap | — |
| 40 | Contracting strategy and packaging | — |
| 41 | Project Integration Plan | — |
| 42 | Conclusions and recommendations |  |
| 43 | Appendices |  |

### Sections without a documented method

Six sections have no corresponding method in the current revision of the methodology document, listed so the gap is visible rather than discovered during drafting: level of service and resilience (11), climate resilience (31), environmental and social assessment (32), the implementation roadmap (39), contracting strategy (40), and the Project Integration Plan (41). None blocks the structure; each will be added to T03 before the corresponding report section is drafted.

### Word version

`Concept_Design_Report_Structure.docx` in this folder is the submission copy, built by `W9/py/make_structure_docx.py`. It is the version to send to NWS; this file is the working source.

## Compliance mapping

The TOR lists 40 numbered concept deliverables at p63–64 of 204. Each must map to a section above, and the mapping table is to be attached to the submission so NWS can verify coverage without reading the whole report.

Open items that must be closed before or within the report: the design horizon (2100 versus 2055), the governing programme, the existing STP capacity, the approved boundary, the modelling software, and the double-peaking in the R0 flow series. These are carried in `CLIENT_DECISIONS_REGISTER.md`.
