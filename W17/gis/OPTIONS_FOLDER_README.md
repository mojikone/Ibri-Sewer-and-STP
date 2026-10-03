# Ibri Sewer — STP network options S1 to S7 (October 2026)

Everything needed to review the seven options for where the sewage is treated: the model, the layers, the maps, the
tables, the quantities for the bill of quantities, the report and the presentation. Open
**`Ibri_W17_network_options.qgz`** in QGIS 3.44 or later; every layer is grouped, styled and labelled, the print layouts
are saved in the project, and the background is the Google satellite layer. Each option's group carries its manholes,
shown from 1:25,000 and labelled with their depth from 1:5,000.

**Recommended, in order of priority (report Section 7.11): S1, one STP at O1; S4, three STPs at O1, O4 and O9; S6, six
STPs.** Together they span the choice, one plant, three or six. Each is costed under the three characters of the
guidelines on the same network model (process, solar energy, reuse, materials): nine cases. The cost estimate and the
multi-criteria appraisal confirm or change the order, and the treated effluent network is designed on the three.

## What is in each folder

| Folder | Content |
|---|---|
| `01_Boundaries` | Project boundary, updated and as received |
| `02_Settlements` | The settlements, drawn as a partition (every plot in one settlement) |
| `05_Roads` | Road centrelines as supplied |
| `11_Network_options` | One GeoPackage per option: `pipes`, `manholes`, `outfalls`, `pumping_stations`, `plants`, `rising_mains`, `deep_runs`, `zones`, `subnetworks` |
| `12_SewerGEMS` | The SewerGEMS model with all seven options |
| `Maps` | One overview of the 24 subnetworks, then three maps per option: **zones** (sewers by the STP they drain to, outfalls, the depth of the sewer arriving at each STP), **network** (sewers by STP and size; each pumping station with its outfall depth, average flow in 2070, pump head and duty; the rising mains) and **depth** (sewers by depth to invert; the outfall depth at each station; the deepest manhole of every run deeper than 12 m) |
| `Tables` | `W17_network_options_tables.xlsx` — summary, flow at each STP by year, pipe length by size, pipe length by size and depth for each option, manholes by depth, every pumping station |
| `BOQ` | `Ibri_Sewer_Options_BOQ_Quantities.xlsx` — quantities for the bill of quantities, one column per option: A gravity sewers by size and depth (0.5 m bands to 4 m, then 1 m), B manholes by the largest pipe they serve and depth, C pumping stations (type, pumps, duty, head, power, wet well, land), D rising mains by size, E treatment plants (flow by year, design average with the 10 % margin, depth of the arriving sewer). House connections, crossings, excavation volumes and reinstatement are excluded until the survey |
| `Reports` | Concept Design Report, build R6 (`Ibri_Concept_Design_Report_R6`, Word and PDF; no revision is printed inside it); the options are in Section 6.2 and Appendix B, the flood exposure of the sewers and manholes in Section 7.2, the recommendation in Section 7.11 |
| `Presentation` | `Ibri_Concept_Design_Presentation_2026-10.pptx` (and a PDF copy) — the design-basis deck of 16 September 2026, then 03 Sewer network (the model, the flow to the plants, the seven options with their diagrams and maps, depth, energy, self-cleansing, the recommendation), and placeholders for 04 TE network and 05 Cost analysis; the bottom strip of every slide shows the five sections, the slide's own lit |

## The model

- **24 subnetworks, O1 to O24**, each draining by gravity to its own outfall and named after it; manholes `O#-M#` and
  pipes `O#-P#`, the trunk numbered first.
- **Scenarios** per option: `S#-2070` designs the pipes for 2070; `S#-2070A` analyses the designed pipes for 2070 as a
  check; `S#-2030` to `S#-2060` analyse the designed pipes for the flow at each STP over time.
- **Loads**: the plot flow of every year at its nearest manhole, peaked in each pipe on the flow upstream of it (Peltier
  up to 1 l/s, Merrimack above); the flow pumped from one subnetwork into the next enters the receiving manhole as that
  year's peak, not peaked again; infiltration 720 L/day per km of sewer.
- **Friction**: Colebrook-White, roughness 1.5 mm (PAM-GUD-203 pages 24 and 28).

## Pumping figures are concept values

Rising mains follow roads and streets (across open ground at 1.1 × the straight line where the street route is over
1.6 × it); Hazen-Williams C 120; fittings +10 %; wet well 1.5 m below the incoming sewer; discharge 0.3 m above the
receiving invert, or 3 m above the ground at an STP; pump efficiency 0.65; each main sized for the least power within
1.0 to 2.5 m/s and at least 75 mm.

## Open points

- The station at O23 lifts about 5 l/s through some 9.5 km against about 300 m of head where it pumps into O21; that
  connection is to be reconsidered (shorter route or local treatment).
- Long rising mains with small flows hold the sewage for hours in 2030 (hydrogen sulphide): see the retention column of
  the pumping-station table.
- Self-cleansing: no year brings every pipe to 0.75 m/s, even at 4 %; the decision on the criterion rests with NWS
  (report Section 6.2.8).
