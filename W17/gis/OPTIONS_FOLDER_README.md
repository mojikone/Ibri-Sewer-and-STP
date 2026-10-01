# Ibri Sewer — STP network options S1 to S7 (W17, October 2026)

Everything needed to review the seven options for where the sewage is treated: the model, the layers, the maps, the
tables and the report. Open **`Ibri_W17_network_options.qgz`** in QGIS 3.44 or later; every layer is already grouped,
styled and labelled, and the print layouts (two per option) are saved in the project.

## What is in each folder

| Folder | Content |
|---|---|
| `01_Boundaries` | Project boundary, updated and as received |
| `02_Settlements` | The settlements, redrawn as a partition (every plot in one settlement) |
| `03_Imagery` | Esri World Imagery mosaic, 5 m, cut to the project area — the background of the maps |
| `05_Roads` | Road centrelines as supplied |
| `11_Network_options` | One GeoPackage per option: `pipes`, `manholes`, `pumping_stations`, `plants`, `rising_mains`, `zones`, `subnetworks` |
| `12_SewerGEMS` | The model `IBRI_W17_R9.stsw` with all seven options |
| `Maps` | Two maps per option: **network** (sewers by the plant they drain to, width by size; each pumping station with the depth of its outfall, its pump head and duty; the rising mains) and **depth** (sewers by depth to invert, manholes over 9 m and over 12 m) |
| `Tables` | `W17_network_options_tables.xlsx` — summary, plant flows by year, pipe length by size, pipe length by size and depth for each option (BOQ), manholes by depth, every pumping station |
| `Reports` | Concept Design Report, Revision 4 (Word and PDF); the options are in Section 6.2 and Appendix B |

## The model

- **24 subnetworks, O1 to O24**, each draining by gravity to its own outfall; manholes `O#-M#` and pipes `O#-P#`, the
  trunk numbered first. The modeller's labels are kept in the `OLD_ID` notes and in brackets on every figure (O1 (O-1)).
- **Scenarios** per option: `S#-2070` designs the pipes for 2070; `S#-2070A` analyses the designed pipes for 2070 as a
  check; `S#-2030` to `S#-2060` analyse the designed pipes for the flow at each plant over time.
- **Loads**: the plot flow of every year as one unit load per manhole, peaked by SewerGEMS on the flow upstream of each
  pipe (Peltier up to 1 l/s, Merrimack above); the flow pumped from one subnetwork into the next as a pattern load at
  the receiving manhole, that year's own peak, not peaked again; infiltration 720 L/day per km of sewer.
- **Friction**: Colebrook-White, roughness 1.5 mm (PAM-GUD-203 pages 24 and 28).

## Pumping figures are concept values

Rising mains follow roads and streets (across open ground at 1.1 × the straight line where the street route is over
1.6 × it); Hazen-Williams C 120; fittings +10 %; wet well 1.5 m below the incoming sewer; discharge 0.3 m above the
receiving invert, or 3 m above the ground at a plant; pump efficiency 0.65; each main sized for the least power within
1.0 to 2.5 m/s and at least 75 mm.

## Open points

- The station at O23 (O-15) lifts about 5 l/s through some 9.5 km against about 300 m of head where it pumps into O21;
  that connection is to be reconsidered (shorter route or local treatment).
- Long rising mains with small flows hold the sewage for hours in 2030 (hydrogen sulphide): see the retention column of
  the pumping-station table.
- Self-cleansing: no year brings every pipe to 0.75 m/s, even at 4 %; the decision on the criterion rests with NWS
  (report Section 6.2.8).
