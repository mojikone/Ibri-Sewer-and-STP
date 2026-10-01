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
| W17 R0 (housekeeping) | `Desktop\Win10 shared folder\IBRI Sewer\14 IBRI_W17\IBRI_W17_R0.stsw` | superseded, kept as the record |
| W17 R1 (physical flattened) | `…\14 IBRI_W17\IBRI_W17_R1.stsw` | superseded by R2, kept as the record |
| **W17 R2 (loads peaked)** | `…\14 IBRI_W17\IBRI_W17_R2.stsw` | **live**; terrain contours carried (`.\SHP\Contour`, relative path) |

Each revision is a new file, so the engineer can keep an older one open in SewerGEMS while the next is built: the
scripts work on copies inside the guest (`C:\IbriWork\W17`) and only add new files to the shared folder.

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

## R1 — the 2070 design as the base physical alternative (2026-10-01)

The modeller's design ("F", renamed 2070 in R0) sat at the end of a chain of 32 inference alternatives. R1 merges it
down the chain into Base Physical (`Flatten.cs`: scenarios moved to the parent before each merge, one unused side
branch deleted first), names the base **2070** and adds seven empty children **S1-2070 … S7-2070**, one per STP
option, to hold each option's design. Check: every scalar physical field of every manhole, pipe and outfall read
before and after — **1,980,581 values, none of the design values changed**; the 1,520 that read differently are
unused fields (weir, cutoff, curve counts, surface storage) that were 0 and are now not stored, on 157 pipes and
132 manholes. Log: `data/r1_log.txt`.

## R2 — the plot loads peaked (2026-10-01, engineer's yes)

- The unit load "Unit Sanitary (Dry Weather) Loads - 1" (the one row of the Extreme Flow Setup) is now
  **"Plot average flow (1 m3/d per unit)"**, discharge-based, 1 m³/d per unit.
- Every pattern-load row in the six sanitary alternatives became a unit-load row with loading units = its flow in
  m³/d (2070: 18,002 rows; 2030–2060: 16,980–16,994). Totals read back identical to the m³/d.
- **Check** (scratch copy, 2030 and 2070 run as ANALYSIS): the outfall flow equals PF × base + infiltration
  (PF from "Peltier100-Merriamck", linear between table rows, on the pipe's cumulative upstream unit load;
  infiltration 720 L/day/km) to **0.0 % at 19 of 24 outfalls**; the 5 others (O3, O10, O11, O15, O20) have two
  incoming pipes, each peaked on its own flow. `data/r2/peak_check_r2.txt`.
- **Transfer** as a pattern load: +100 L/s at O13-M1 gives +100.000 L/s at O13 and no change anywhere else — not
  re-peaked, and it does not change the peaking of the receiving network's own loads.
- The peaking table "Peltier100-Merriamck" is Peltier to 1 L/s and Merrimack from the next row (1.5 L/s); between
  1 and 1.5 L/s SewerGEMS interpolates (2.50 → 3.39). Kept as the modeller set it (engineer, 2026-10-01).

## The year loads are short (found 2026-10-01, not yet corrected)

2070 carries the plot layer's saturation flow (60,355 against 60,099 m³/d, +0.4 %, and every subnetwork within
noise), but **the five year alternatives are 7–10 % below the plot layer**: 2030 21,789 against 24,216; 2040 28,160
against 30,938; 2050 34,675 against 37,814; 2055 38,904 against 42,266; 2060 44,034 against 47,523 m³/d. The
shortfall sits in almost every subnetwork (O3 the largest, 830–990 m³/d) and in no single plot status or use, so the
year loads were most likely built from another version of the plot layer or another LoadBuilder setup than 2070.
Nearest-manhole re-assignment and the breakdown: `py/loads_vs_plots.py`, `data/loads_vs_plots.txt`.
Several rows on one manhole (2,023 manholes, up to 4 rows) are separate plot batches, not duplicates.
About 86–118 m³/d sits on the inactive manholes of the three deactivated subnetworks (the absorption-well areas).

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

## Decided by the engineer (2026-10-01)

- O-21 (now O2) drains to **MH-8112** (O1 subnetwork; OLD_ID in Notes).
- Transfers in the analysis years use **each year's own upstream peak**, so every year runs upstream first.

## Open

- Reload the five year alternatives from the current plot layer (`Q_2030` … `Q_2060`), the same way as 2070.
