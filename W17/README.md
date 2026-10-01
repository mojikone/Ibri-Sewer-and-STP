# W17 — the modeller's SewerGEMS model, driven through the API (opened 2026-10-01)

W17 works on the SewerGEMS model the modeller designed (`13 IBRI_29092026 12M`), not on the W15 engine.
SewerGEMS (CONNECT 10.4) runs in a VirtualBox Windows 10 guest with **no network adapter but an internal one,
no gateway and no internet**; nothing here changes that. The link is a file drop: `sewergems_api/watcher.ps1`
runs in a PowerShell window inside the guest and executes every script dropped into the shared folder
`D:\VBOX\bridge\jobs`, writing the output to `D:\VBOX\bridge\out`. The scripts load the OpenFlows and Haestad
libraries that ship with SewerGEMS; nothing is installed or downloaded. `compile_check.ps1` compiles the C#
helpers on the host against copies of those libraries before a job is sent.

## Where the model is

| Copy | Path | State |
|---|---|---|
| Modeller's original | `Desktop\Win10 shared folder\IBRI Sewer\13 IBRI_29092026 12M(7.12 PM )\` and `Hydraulic\Model\temp\…` | untouched |
| **W17 R0 (housekeeping done)** | `Desktop\Win10 shared folder\IBRI Sewer\14 IBRI_W17\IBRI_W17_R0.stsw` | live; terrain contours carried (`.\SHP\Contour`, relative path) |

The model files are not in git (300 MB). `data/` holds the renaming maps, the before/after inventories and the log.

## R0 — housekeeping (2026-10-01), as instructed by the engineer

- Calculation options "Base Calculation Options" → **DESIGN** (calculation type design); ANALYSIS kept.
- Physical "Physical Alternative - F" → **2070**. It still inherits through the chain of 32 "Property Inference"
  physical alternatives, so those alternatives are kept; their 33 scenarios are deleted.
- Sanitary "Base Sanitary Loading" (the 2070 loads) → **2070**; the empty, unused alternative already called 2070 deleted.
- Scenario "Scenario - 34" → **2070**.
- System flows dropped: the six year alternatives deleted, the 19 known flows of the base alternative cleared.
- The inactive test pump station (W-2, PMP-1, J-1, J-2, P-1…P-4) deleted.
- **Outfalls renamed O1…O24** in the engineer's order (O-1 first; towards O-4; towards O-19; south from O-8;
  west from O-6). The three deactivated outfalls keep O-56, O-67, O-78.
- **Manholes `O#-M#`, pipes `O#-P#`**: each subnetwork's trunk first (at every junction the branch with more
  manholes upstream), then each branch in full, downstream branch first; a pipe takes its upstream manhole's number.
  All 24 subnetworks are trees (no loops), so the numbering is unambiguous.
- **OLD_ID**: the 10.4 API refuses text user fields ("Invalid data FieldType"), so the old label is written into
  each element's native **Notes** as `OLD_ID=MH-18013` (38,593 elements), and `data/rename_*.csv` keeps the map.

| Old | New | Old | New | Old | New | Old | New |
|---|---|---|---|---|---|---|---|
| O-1 | O1 | O-20 | O5 | O-16 | O10 | O-8 | O16 |
| O-21 | O2 | O-13 | O6 | O-17 | O11 | O-23 | O17 |
| O-2 | O3 | O-4 | O7 | O-9 | O12 | O-24 | O18 |
| O-7 | O4 | O-10 | O8 | O-19 | O13 | O-11 | O19 |
| O-3 | O9 | O-12 | O14 | O-18 | O15 | O-22 | O20 |
| O-6 | O21 | O-14 | O22 | O-15 | O23 | O-5 | O24 |

## What the tests found (scratch copies, nothing saved)

1. **The plot loads are not peaked.** All 16,980 rows (2030) are *pattern loads*; the Extreme Flow Setup has one row,
   for the unit load "Unit Sanitary (Dry Weather) Loads - 1", so it never touches them. The 2030 run gives O1
   50.7 L/s for 49.0 L/s of base; the 1.7 L/s difference is the 720 L/day/km infiltration. The plot flows are
   average flows (`W14/docs/DESIGN_FLOWS_FOR_NETWORK.md`), so **the network is analysed and designed near average flow**.
2. **The fix is proven:** converted to unit loads (load definition 1, unit load 1 per unit, units = the plot flow),
   O12 gives 10.95 L/s for 3.42 L/s of base — the Merrimack hand figure (PF 3.07) plus infiltration.
   The model's curve "Peltier100-Merriamck" switches from Peltier to Merrimack at 1.5 L/s of flow; the guideline
   switches at 100 properties (G1-p71, p72) — about 1 L/s here, to be confirmed.
3. **Transfers:** a pattern load and a fixed inflow each add exactly what is put in (+100 L/s in, +100 L/s out) and
   add to, not override, the loads already at the manhole. With the plot loads as unit loads, a transfer entered as
   a pattern load is **not peaked again**, so the engineer's method (outfall peak flow → pattern load on the
   receiving manhole) works, upstream subnetworks first.
4. In the units: stored flows are cfs; the typed API returns the display unit, m³/d.

## Open — needs the engineer

- Convert the plot loads of all six years to peaked unit loads (finding 1)?
- O-21 (now O2, 1,983 manholes) receives the whole O-4 chain but has no destination in the list; it ends 39 m from
  MH-8112 of the O-1 subnetwork.
- Transfers in the analysis years: each year's own upstream peak, or the 2070 pump rate in every year?
