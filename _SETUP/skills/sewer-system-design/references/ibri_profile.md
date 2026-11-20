# Worked example: the Ibri profile (Renardet 2621, W18, November 2026)

The project profile as Ibri filled it. Use it as the model for `profile_template.md`. Figures are for orientation only:
quote them from the project's own records, not from here. The full record is the W18 README in the Ibri repository
(`Hydraulic/Claude/W18 NWS scenarios 2056-2071/README.md`), and every tool and trap is in
`Hydraulic/Claude/_SETUP/TOOLKIT_W18_deliverables.md`.

## Project

- Client: Nama Water Services (NWS), Ibri Wilayat, Oman. Guidelines: PAM-GUD-201, 202, 203.
- CRS: EPSG:32640 (UTM 40N).
- Working folder: `D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Hydraulic\Claude\W18 NWS scenarios 2056-2071\` (git root one
  level up).

## Inputs

| Input | Where | Note |
|---|---|---|
| Plot layer with the manhole of each plot | `C:\Users\mojtaba\Desktop\Win10 shared folder\IBRI Sewer\14 IBRI_W17\SHP\Plots\Plots.shp` | field `HMINNODE`; the W14 plots row for row |
| Plot attributes | `Hydraulic/Claude/W14/shp/PLOTS_load.shp` | area, shape tests, classes, estates, metered flow |
| Settlement boundaries | `Hydraulic/Claude/W14/shp/Settlements_merged.shp` | 25 settlements |
| Population, rate, properties per plot | the team's `New Calculation MH.xlsx` (sheets "Average", "Base Demand" H4, "MOHUP DATA - NA" column D) | in `Hydraulic/temp/recent updates by the team/` |
| Terrain | `Data/Terrain/Sat_0p5m/IBRI_0p5_VRT2.vrt` | 0.5 m bare earth |
| SewerGEMS model | the modeller's file, copied to `C:\IbriWork\W18\` in the VM | R4 = 13 year alternatives 2031–2091 |
| Team's TE models and register | `W:\...\06-WORKING\04-Hydraulic\10_TSE\SHP\Scenarios` | team data, not for the public repo |
| Team's cost estimate | `W:\...\06-WORKING\04-Hydraulic\11_Finacial` | rates in `final_boq.py`, `final_financial.py` |
| Team's report to edit | `Hydraulic/temp/recent updates by the team/Ibri_Concept_Design_Report_R8-MH.docx` | work on a copy |

## Plants and scenarios

| Plant | Model outfall |
|---|---|
| STP-1 | O1 |
| STP-2 | O16 |
| STP-5 | O4 |

| Scenario | Plants |
|---|---|
| SC1 | STP-1 |
| SC2 | STP-2 |
| SC3 | STP-1 + STP-5 |
| SC4 | STP-2 + STP-5 |

Each scenario is designed for 2051, 2056 and 2061, which makes 12 designs. 2056 is the base.

## Decisions (engineer and client, 2026-11-16 to 18)

- **Loads:**
  - population: the team's three-series mean;
  - 171.03 L/person/day, occupancy 4.8;
  - each settlement capped at its capacity, with no overflow; Ibri is full in 2063;
  - growth plots: 200–3,000 m², home-shaped, any zoning but agricultural, heritage and industrial; 43,230 plots;
  - estates additive, 316.4 m³/d;
  - not carried: the inactive network, or more than 200 m from a sewer.
- **Self-cleansing:** pipes above DN200 at 0.75 m/s at the 2031 peak, rechecked at 2036.
- **Gradient limit:** 0.75 %.
- **Depth:** 12 m to an outfall; 14.65 m for an added station or outfall; 16.5 m for any manhole.
- **Naming:** pumps P1, P2 ...; lifts P<n>L<k>; manholes and pipes <section>-M<k> / -P<k>; force mains <station>-RM.
- **Report:** follow the team's R8-MH structure exactly, adding or changing only what must change. Use "property", never
  "dwelling".

## Results to orient by (quote from the record, not from here)

- **Loads, carried:** 22,391 m³/d in 2031 and 37,892 m³/d in 2056. Not carried: 693 and 1,128 m³/d.
- **Network:** 19,083 pipes per design.
- **Own model against SewerGEMS:** the same size on every pipe and flows within 0.1 % in all 12 designs.
- **Under 0.75 m/s above DN200 at 2031:** 4.2 km for the 2051 designs, 9.0 km for 2056, 14.1 km for 2061.
- **Report:** concept design report R12, 240 pages, clean-room gate passed.
