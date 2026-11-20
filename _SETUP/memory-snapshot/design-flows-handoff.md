---
name: design-flows-handoff
description: Where a network or plant design takes its flows now (W18, NWS basis): manhole_loads.csv, design years 2051/2056/2061, 2031 self-cleansing above DN200; the W14 Q_ULT / Q_2030 x 0.61 rule is superseded
metadata:
  type: project
---

**Since 2026-11-16 every network or plant design takes its flows from W18** (`W18 NWS scenarios 2056-2071/`), not from W14.

- **Loads:** `results/loads/manhole_loads.csv`, every manhole, 2026–2091 every 5 years, from `py/nws_loads.py`; per plot in `gis/W18_plots_2026_2100.shp`. How they were built and checked: `_SETUP/TOOLKIT_W18_deliverables.md` 10a–10b.
- **Model:** `C:\IbriWork\W18\IBRI_W18_R4.stsw` (job 072), 13 year alternatives, unit loads peaked by the Extreme Flow Setup 'Peltier100-Merriamck', 720 L/km/day on the conduits, transfers as additional loads (toolkit 10c).
- **Design years:** each scenario SC1–SC4 designed for 2051, 2056 (base, 2031 + 25) and 2061.
- **Self-cleansing:** pipes above DN200 reach 0.75 m/s at the 2031 peak, gradient steepened up to the 0.75 % limit; 2036 also checked.
- **Sizing:** Table 11 minimum gradient, Colebrook-White ks 1.5 mm, d/D 0.65 to DN355 and 0.50 above, 1.3 m cover (toolkit 10d–10f).
- **Final designs:** `results/final_0.75pc_SC1-SC4/<case>/`.

**Superseded:** the W14 rule (size on `Q_ULT`, self-cleansing on `Q_2030` × 0.61, tractive force at 1 Pa) in `W14/docs/DESIGN_FLOWS_FOR_NETWORK.md` is the record of R2–R7 only.

**Why:** the engineer designs in several chats and wants each to find the flows without searching; a recall of the old W14 rule would size the network on the wrong basis without any error. **How to apply:** point to these files, never copy numbers from memory. Related: [[nws-basis-change-nov-2026]], [[w18-growth-plot-rule]], [[w18-final-design-brief]].
