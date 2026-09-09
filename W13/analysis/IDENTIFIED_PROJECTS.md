# Identified projects and special consumption — what public data shows (2026-09-09)

GUD-201 keeps two streams outside the 22 % / 14 % ratios: *specific identified non-domestic
projects such as economic zones* (§7.3.1, G1-p59, "case-by-case") and *special consumption*
(§7.3.4, G1-p61: labour camps, high-water industry, "must be provided by the developer").
This register lists every candidate found in OpenStreetMap, the electricity accounts, the
7 September plot file and the press, with its position against the 531.4 km² project
boundary and what it means for the load. Footprints: `W13/shp/Identified_projects_OSM.shp`,
QGIS layer *Identified projects, OSM footprints (W13)*.

Confidence tags: [Certain] measured in the data; [Likely] one public source plus a map check;
[Guessing] press only, not located.

## 1. Inside the boundary — the load lands on our pipes

| Site | Where | Size | Metered as | Stream | Confidence |
|---|---|---|---|---|---|
| **Al Tayyeb industrial area** (صناعية الطيب) | Al Araqi, NE of town, E455400 N2572700 | 93.8 ha, **205 Industrial plots** | **1,044 accounts on the Commercial tariff**, 2 CRT, 0 Industrial tariff | Identified project — this is the "AL TAYYEB IND." the criteria name. GAP-17 said the estate was not identifiable: it is, under the Commercial tariff | [Certain] |
| **Tanam industrial area** (صناعية تنعم) | Al Mukhtobiyah, 2.5 km E of the STP, E445300 N2561300 | 61.1 ha, **106 Industrial plots** | **410 Commercial accounts**, 10 CRT, 1 Industrial tariff (the only one in the file) | Identified project, second estate. Its 13 CRT accounts are the "Industrial" cluster 35 | [Certain] |
| Ibri industrial (صناعية عبري), town | Hayy Almazra / Al Orobah, E447900 N2569500 | 12.3 ha | 402 Commercial + 130 additional-dwelling accounts | Workshops in the town fabric; mixed with housing, not an estate. Stays in the 22 % | [Likely] |
| MOT Centre | Bu Khabi, next to the Police HQ, E436800 N2573900 | 7.1 ha | 2 CRT Seasonal | Ministry of Transport yard; governmental | [Likely] |
| **Royal Army of Oman, Northern Frontier Regiment (Malik bin Faham camp)** | E442000 N2565100, 3.0 km from the STP | **296 ha** military landuse | **0 accounts in the file** — self-metered | Special consumption: Tab 12 *army camps 185 l/d per occupant* (G1-p61). Occupancy must come from MOD; nothing in the data | [Likely] |
| Ibri Regional Hospital | E441400 N2569100 | 240 beds at opening (1995), referral hospital | in cluster 54, 6 CRT | Governmental, Tab 12 *650 l/d per bed + staff*. Bed count to be confirmed by MoH | [Likely] |
| UTAS Ibri (College of Technology, Al Akhdar campus) | two sites, clusters 81 and 50 | est. 2007 | 16 CRT | Governmental, Tab 12 *130 l/d per pupil + staff* | [Likely] |
| Hotels: Ayla Ibri (74 rooms, at Bawadi Mall), F&M Grand, Al Majd, Remal, Alnebras, Ibri Oasis | town | 6 hotels | Commercial tariff | Non-domestic, Tab 12 *200–500 l/cap/d*; small | [Likely] |
| Ibri Landfill (مردم عبري الهندسي) | E449000 N2561200 | 37 ha | 0 accounts | No sewage; leachate is not our load | [Certain] |
| Ibri Police HQ campus | Bu Khabi, cluster 21 | — | 17 CRT | Governmental | [Likely] |

## 2. Planned inside or at the edge — not in any dataset yet

| Project | What | Where | Status | Source |
|---|---|---|---|---|
| **Ibri View** (OMRAN + Governorate) | **2,000,000 m²**: three hotels, shopping centre, residential, youth centre, parks; RO 183 million, first phase within two years | "Al Salif area of Ibri" — As Sulayf lies inside the boundary south of the town (cluster 87 sits there), so [Likely] inside | MoU signed; RO 10 million allocated for phase 1 | Oman Observer 1170935 |
| Ibri Central Slaughterhouse | high-strength trade effluent (blood, FOG); p74 pre-treatment rule | not located | design / tender | Muscat Daily 2024-11-03 |
| Ibri Market | wholesale/retail market | not located | "under creation" | Oman Observer 1178157 |
| Ibri Youth Centre, Science and Innovation Centre, public park | governmental | not located | design / tender | Muscat Daily, Oman Observer |
| Ibri–Dhank road dualisation | a new dual carriageway = a new sewer exclusion corridor (rule 7) | west of town | advancing | Oman Observer 1178157 |
| Ibri Structure Plan (Cundall for MoHUP) | 330 km² plan, one of 14 cities; land use and projects not public | — | done | cundall.com |

## 3. Outside the boundary — no pipe, but possibly a tanker to the STP (GAP-19)

| Site | Where | Size | What it sends |
|---|---|---|---|
| **Madayn Ibri Industrial City** | 8.6 km SW of the boundary, on the Saudi road, E434150 N2555031, 13 km from the STP | 10 km² gross, 3 km² phase 1 opened Feb 2024; 17 agreements, 250,000 m² let, RO 25 million by June 2026; food, oil-and-gas services, marble, fertiliser | Phase 1 has its own sewer network and a **collection tank** — so it is tankered. Ask NWS where those tankers go |
| **Ibri IPP 1,539 MW (gas) + Ibri II solar 500 MW + Ibri III solar 500 MW (COD Q4 2026)** | 7.5–11 km NW of the boundary, 27–31 km from the STP | the construction camp built for the CCGT houses the solar contractors (AIIB ESIA) | A labour camp, exactly the §7.3.4 case, and the likely source of the "labour camps tankered to Ibri STP" reported at the site visit |
| Marble quarries (Omani Marble, International Marble, Al Ajmi, Al Nasr) | in the hills, not located | — | dry process, workers' camps possible; nothing in OSM |

## 4. What this changes

1. **GAP-17 is answered.** Two estates, 167 ha and 311 Industrial plots, carry 1,454 Commercial-tariff
   accounts. The industrial load is inside the 22 % today; per G1-p59 it should be taken out and
   costed case by case. What the estates discharge (wet or dry) still needs NWS / Madayn.
2. **The army camp is a hole in the data.** 296 ha, 3 km from the STP, no account. Tab 12 has the
   rate; the occupancy is a data request.
3. **Ibri View is the one planned project big enough to move a pipe.** 2 km² of hotels and housing
   inside the boundary within the horizon. Ask NWS/OMRAN for the masterplan.
4. **Tankers**: Madayn phase 1 and the IPP camp are the two named candidates for GAP-19.

Sources: OSM via Overpass (ways 314948590, 456581689, 366934573, 1465668244, 830305309,
1100731219 and others in the shapefile); gem.wiki Ibri Independent power plant; Oman Observer
1170935, 1178157, 1150140, 1193786; Madayn press release 2026-08; AIIB Ibri II ESIA; Muscat Daily
2024-11-03; Wikipedia Northern Frontier Regiment; MoH Ibri Hospital page.
