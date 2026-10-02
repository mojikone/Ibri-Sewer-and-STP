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
| W17 R2 (loads peaked) | `…\14 IBRI_W17\IBRI_W17_R2.stsw` | superseded by R3, kept as the record |
| W17 R3 (one load per manhole) | `…\14 IBRI_W17\IBRI_W17_R3.stsw` | superseded; **the shared-folder copy was saved again from SewerGEMS at 10:18 before the engineer's Save As, so the R3 record is the guest copy `C:\IbriWork\W17\IBRI_W17_R3.stsw`** |
| R4_loads (engineer's LoadBuilder reload) | `…\14 IBRI_W17\IBRI_W17_R4_loads.stsw` | the engineer's input to R4, kept |
| W17 R4 (years reloaded) | `…\14 IBRI_W17\IBRI_W17_R4.stsw` | the loads every option builds on |
| W17 R5, R6 (first S1 builds) | `…\14 IBRI_W17\IBRI_W17_R5/R6.stsw` | **DO NOT USE** — see the section below |
| W17 R7 (option S1, Manning) | `…\14 IBRI_W17\IBRI_W17_R7.stsw` | superseded by R9: designed with Manning's n (0.013 catalogue), before the friction decision |
| W17 R8 (Colebrook-White) | guest only, `C:\IbriWork\W17\IBRI_W17_R8.stsw` | R4 with the gravity friction switched to Colebrook-White, ks 1.5 mm |
| **W17 R9 (options S1–S7)** | `…\14 IBRI_W17\IBRI_W17_R9.stsw` (also in `Options 2026-10/12_SewerGEMS/`) | **live**: all seven options on Colebrook-White, delivered 2026-10-01 17:44 |

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

## R3 — one sanitary load per manhole; a hard Peltier/Merrimack step (2026-10-01, engineer's decision)

- **Each manhole carries one sanitary load** (engineer: only a manhole receiving an upstream outfall carries a second,
  the transfer). The 2–4 rows on 2,023 manholes are summed into one row in all six years, totals unchanged to the m³/d
  (2070: 2,224 rows removed; 2030–2060: 2,043–2,056).
- "Peltier100-Merriamck" gets a row **1.001 L/s → 3.56** (Merrimack at 1 L/s), so the switch is a step at 1 L/s instead
  of a ramp to 1.5 L/s. Only outfalls in that band moved: 2030 O14 4.69→4.94, O15 3.31→4.33, O19 4.23→4.68 L/s;
  2070 O23 4.91→5.05 L/s.
- *Correction (R4):* the extra rows are **not** from *Append* runs, as first written here — a single fresh LoadBuilder run with *Override* writes the same 2–4 rows on 2,022 manholes. LoadBuilder splits them itself; the merge after every reload is the fix.

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

**Tested 2026-10-01 — not the deactivated areas.** Plots whose nearest manhole is one of the 197 inactive ones carry
539–719 m³/d (2030–2060), a fifth of the gap, and the inactive manholes do carry loads in every year. At 783 manholes
the 2030 gap is exactly one plot: those plots are 4.3 km (median) from any inactive manhole, in every settlement, 548
of them existing plots (mostly residential, agricultural, commercial). `py/year_gap_check.py`, `data/year_gap_check.txt`.

## R4 — the year loads reloaded by the engineer (2026-10-01)

The engineer re-ran LoadBuilder for all six sanitary alternatives from the current `Plots.shp` (`Q_2030` … `Q_2060`,
`Q_SAT`) with *Override* and saved `IBRI_W17_R4_loads.stsw`. *Override* replaces loads only on the manholes it writes to:
**70 old 2070 rows (259.4 m³/d, 162 of it on 11 manholes of O12) survived on manholes the new run did not load** — the
same +256 m³/d the old 2070 carried over the plot layer. They were removed, then the loads converted to the peaked unit
load and merged to one row per manhole. **Every year now equals the plot layer to the decimal**: 2030 24,216.31; 2040
30,938.43; 2050 37,814.53; 2055 42,265.79; 2060 47,523.06; 2070 60,098.79 m³/d, on 15,708–15,711 manholes. The full plot
layer is loaded, so plots in unpiped land and the military area are carried at their nearest manhole in every year.
Peak outfall flow, sum of the 24 outfalls: 2030 613.9 → 674.0 L/s; 2070 1,541.5 → 1,535.2 L/s. `data/r4/`.

## 2026-10-02 — the report reviewed, the recommendation, the BOQ workbook and the deck

- **Report build R5** (`report/R5/Ibri_Concept_Design_Report_R4.docx` + `.pdf`, 159 pages): `build.py` has `REV = "R5"`
  (the folder) and `DOC_REV = "R4"` (what the cover, footers and file name print); the engineer: none of the revisions is
  issued, R5 is internal and never appears in the report. Read end to end against itself; fixed: the plant flow tied
  through (Table 1, 4.2.8, 4.4, 6.2.7, 8.4: 60,099 from the plots, 60,456 at the plants, 66,502 with the margin), the
  structure (1.1, 1.1.2, 8.5 with Appendix B, Chapter 6 intro, 6.1.1, 6.1.2, 6.2.1, 6.2.4, 6.3, 6.5.1), footnotes without
  "Revision 1" or "test area", the 12 m cover sentence removed from 6.2.7 (engineer: state how many and how deep only),
  6.2.8's flows stated (model flows, all connected, infiltration in), Decision 7 pointing to 6.2.8, G203 p50's 30 min in
  Table 45, Appendix B's lengths from the unrounded pipes (one total, 1,498,295 m, in every option).
- **Plant-inlet lift** (`report/facts_w17.inlet_lift`): depth of the arriving sewer + 1.5 m wet well + 3 m, 65 %, the
  stations' own values. 2070: 1,172–1,371 MWh/yr, S1's equal to its 23 stations; the order of the options is unchanged.
  Table 44 and chart W05 in 6.2.7; chart W06 (the options side by side) in the executive summary.
- **Recommendation** (`facts_w17.RECOMMENDED`, the engineer's priority 2026-10-02): **S1, S4, S6**, one of each character;
  S2 not recommended (+57 % energy on S1); S3, S5, S7 between. In the executive summary, 7.11, 8.4 and 8.4.1, 6.1.1, 6.4
  and the deliverables register. The TE network is designed on the three.
- **BOQ workbook** `Options 2026-10/BOQ/Ibri_Sewer_Options_BOQ_Quantities.xlsx` (`py/boq_workbook.py`): Read me, Summary,
  A sewers by OD and depth (0.5 m bands to 4 m, then 1 m), B manholes by the largest pipe and depth (model rim − invert,
  not the GeoPackage's 0.01 m rounding, which moves the minimum-cover manholes across 1.5 m), C pumping stations (G203
  Table 17 type and pumps, Table 21 land), D rising mains, E plants. Checked against the report: 1,498,295 m, 19,083
  manholes, the same bands. Excluded until the survey: house connections, crossings, excavation volumes, reinstatement.
- **Deck** `Options 2026-10/Presentation/Ibri_Concept_Design_Presentation_2026-10.pptx` (`presentation/build_deck_w17.py`,
  51 slides): the engineer's deck "- 2-1" (WeTransfer, 2026-10-02; byte-identical to his Downloads copy of 16 September)
  with only the cover's title, date and revision changed; section 03 (the model, the flow to the plants, the seven options
  with diagram and map each, depth, the options side by side, energy, two matters, self-cleansing, the recommendation)
  cloned from his own slides; placeholders 04 TE network and 05 Cost analysis. **PowerPoint pitfall:** opening, SaveAs,
  editing and saving again re-reads his pictures lazily by their old part names and swaps maps for logos and icons; copy
  the file, open it, edit, save once (tested clean). His slides 2–22 compared pixel by pixel with the base render.
- Open for the engineer: the GeoPackages in `11_Network_options` still carry an `old_id` field with the modeller's labels.

## R9 — the seven options on Colebrook-White (done 2026-10-01, 17:45)

Job `055_make_R9_all_options.ps1` built S1–S7 in one file from R8, ~44 min an option at Colebrook speed, and delivered
`IBRI_W17_R9.stsw` to the shared folder (exit 0); `py/process_options.py` followed it and processed each option as its
last run was exported. **Every option:** the design converged in four passes; the 2070 analysis and every year kept
the 2070 sizes and inverts (guard, both in the VM and on the host); no pipe over 3.0 m/s or the d/D limit in any year;
the flow check 0.0000 %. Side by side (`results/options_comparison.md`, the workbook in the deliverable folder):

| Option | STPs | Sewer at the STPs, m deep | Stations | kW | MWh/yr 2030 / 2070 | Rising mains km |
|---|---|---|---|---|---|---|
| S1 | O1 | 10.3 | 23 | 422 | 465 / 1,367 | 43.9 |
| S2 | O16 | 5.9 | 23 | 884 | 1,311 / 3,337 | 37.3 |
| S3 | O1, O4 | 10.1 / 6.9 | 22 | 361 | 367 / 1,148 | 43.2 |
| S4 | O1, O4, O9 | 10.0 / 6.9 / 8.8 | 21 | 319 | 339 / 974 | 43.0 |
| S5 | O1, O3, O4, O9 | 9.8 / 5.8 / 6.9 / 8.8 | 20 | 277 | 259 / 797 | 43.0 |
| S6 | O1, O3, O4, O9, O16, O22 | 9.8 / 5.8 / 6.9 / 8.8 / 4.9 / 1.5 | 18 | 198 | 220 / 616 | 28.7 |
| S7 | O1, O16, O22 | 10.3 / 4.9 / 1.5 | 21 | 343 | 426 / 1,186 | 29.5 |

- **Depth does not separate the options:** 40 manholes over 12 m, 3.2 km of sewer over 12 m and the deepest manhole at
  15.0–15.1 m (O21-M21) in every option; the deep sewers are set by the ground inside the subnetworks.
- **S2 doubles the pumping** (884 kW): all of O1's 1,450 L/s is pumped 3.0 km to O16 (DN1200, 24 m).
- **O23** lifts 5 L/s against 220–300 m of head in every option (9.5 km to O21, or to the O22 plant in S6/S7) —
  to be reconsidered; **retention** over 30 min in 2030 at 10–14 stations, up to 73 h (O18 to the plant).
- **S1 (first, 13:25):** plant O1 24,756 → 60,456 m³/d, peak 674 → 1,535 L/s. `results/S#/` for every option.
- **d/D is compared at three decimals**, the design's own precision: O2-P203 sat at 0.65006 against 0.65 (0.06 mm).
- **8,712 of 19,083 pipes are drawn against the flow** (start node downstream). By the tree none falls the wrong way;
  the exported gradient is now absolute, the GeoPackage swaps their end depths, and the self-cleansing scripts take the
  upstream end from the inverts. The self-cleansing year table did not change (29 % in 2030, 46 % in 2070).
- **Outputs:**
  - **Concept Design Report R4**, `report/R4/` (153 pages): R3 + 6.2.5–6.2.8 and Appendix B from
    `report/facts_w17.py`, executive summary and deliverables updated. **Client register (engineer, 2026-10-01): current
    names only (O1–O24, never the modeller's O-#), no file, field, sheet or folder names, no internal steps** — nine R3
    footnotes reworded; the depth of the sewer arriving at each STP given everywhere.
  - **Transfer diagrams** drawn locally by `py/diagram_png.py` (approved by the engineer) from `py/diagram_layout.py`;
    the Figma code (`diagram_js.py`, file `rm7tdwnSGW5HefJlXQPWDW`) is current but unused — the Starter plan's MCP
    limit blocks it; the `EXPORT2X …` frames left on that canvas carry old names and can be deleted.
  - **Maps** (`gis/make_w17_project.py`, engineer's notes 2026-10-01): one overview of the 24 subnetworks and three per
    option (zones, network, depth), Google satellite at 50 % (rendered per map: the standalone exporter crashes on web
    tiles), legend bottom-left kept clear of the network, labels "O21 8.3m 4,519 m3/d / PMP 15m 126L/s".
  - **Deliverable folder** `Options 2026-10/` (not in git): QGIS project (86 layers, 22 layouts), GeoPackages on the
    true pipe geometry (job 056), maps, `W17_network_options_tables.xlsx`, R4, the R9 model; the downloaded Esri
    mosaic removed.
- **Report build trap, fixed:** `W16/report_basis/facts_basis.py` puts `W16/report` at the head of the import path, so
  every chapter imported after it came from R3; `build.py` and `charts_r3.py` now put `W17/report` back in front.

## R8 — Colebrook-White friction (engineer's decision, 2026-10-01)

G203 p24 and p28: *"Gravity sewerage systems shall be designed by using the recognised hydraulic formulas such as
Colebrook-White, or Manning's Formula"* and *"Colebrook-White ... shall be designed using a ks value of 1.5 mm for all pipe
sizes and materials"*; p25 Table 9: viscosity 1.141 × 10⁻⁶ m²/s at 15 °C, *"the conservative value of 15°C should be used"*;
p23 Table 8 gives typical Manning's n by material (plastic 0.009, PVC 0.009–0.011, PE 0.009–0.015). **Table 11 (p29) is
Colebrook-White at ks 1.5 mm**: every row gives 0.74–0.76 m/s full bore at 15 °C (`py` check in the session; Manning
equivalent n 0.0128–0.0133). The client asked for Colebrook-White. R8 = R4 with *Gravity Friction Method* = Darcy-Weisbach,
*Friction Factor Method* = Colebrook-White, viscosity 1.141 × 10⁻⁶ m²/s on both calculation options, e = 1.5 mm on all
19,286 conduits and every catalogue size (catalogue Manning's n left at 0.010, unused). Flows unchanged; velocities a
median 13 % lower than with the old Manning roughness (2030, modeller's pipes). A Colebrook run takes ~8 times longer.

## Self-cleansing — for information (the audit waits for the client's decision)

`results/S1/selfcleansing_info.md` (S1, R7 flows; required gradients by Colebrook-White ks 1.5 mm): **no year has every
pipe at 0.75 m/s at its peak** — 1.0 % of pipes in 2030, 5.8 % in 2070; 1 to 5 of 3,612 head pipes. The median gradient
a head pipe would need is 35 % (2030) / 19 % (2070); 1 % of head pipes could do it within the client's 4 %. A DN200 needs
**0.93 L/s** of peak flow to reach 0.75 m/s at 4 %. The tractive gradient at 1 Pa (Mara, G203 p27) is a median 2.5 % (2030)
/ 1.3 % (2070) for head pipes; it passes 4 % only below 0.0135 L/s (1,272 head pipes in 2030, 372 in 2070 — pipes carrying
little more than their infiltration).

## R7 — option S1, centralised STP at O-1 (2026-10-01)

- **Structure** (the same for every option): sanitary children `S1-2030` … `S1-2070` under the shared year
  alternatives, holding only the transfer rows (pattern loads, 120 rows = 20 transfers × 6 years); physical `S1-2070`
  (child of the modeller's 2070); scenarios `S1-2070` (DESIGN), `S1-2070A` (the same 2070 run as an analysis, the
  check on the design), `S1-2030` … `S1-2060` (ANALYSIS, own year's transfers) — every alternative and calculation
  option set local. Catalogue Manning's n set to 0.013 (the modeller's value on 18,750 pipes; the catalogue had 0.010).
- **Transfers** = each outfall's own peak + everything transferred into its subnetwork (additive, tested), upstream
  first, per year: `py/routing.py` (S1–S7 routing), `py/make_transfers.py`. Flow check: SewerGEMS outfall flows equal
  the computed transfers to 0.0000 %.
- **Design** converged in four passes (2,627, 1,538, 210, 0 sizes changed). 2070 analysis and every year: **no pipe over
  3.0 m/s, none over the d/D limit**; 42 pipes break the 12 m cover limit; **40 manholes deeper than 12 m** (modeller's
  design: 260), deepest 15.10 m (O21-M21). 1,498 km of pipe; length by size and depth band in`results/S1/S1_summary.md`.
- **Plant O1:** 24,756 m³/d (2030) → 60,456 m³/d (2070) average with infiltration; peak 674 → 1,535 L/s.
- **Pumping:** 23 stations, 431 kW duty, 0.48 GWh/yr (2030), 1.39 GWh/yr (2070) — with the assumptions tagged in the
  table (straight-line main × 1.25, C = 120, efficiency 0.65). Long small mains (O-23, O-24 to the plant 7–9 km; O-15
  to MH-18772 9.2 km lifting 45 m) give 2–3 days' retention in 2030: H2S risk (G203 §7.7), to be weighed in the appraisal.
- **Not yet run:** the self-cleansing audit on 2030 × 0.61 with no infiltration (project rule); 17,977 of 19,083 pipes
  are below 0.75 m/s at their 2070 peak — mostly DN200 heads, where G203 lets tractive force govern.

## R5, R6 — first S1 builds: DO NOT USE (2026-10-01)

Both are kept only as the record of a fault. The year scenarios S1-2030 … S1-2060 were created with calculation
options equal to their parent's, so they stayed **inherited**; switching S1-2070 to DESIGN made every year run a
design too, each re-sizing the shared S1 pipes for its own year (O9-P715: 450 mm after 2030, 560 mm after 2060, 900 mm
after the 2070 design). The pipes saved in R5 and R6 are therefore a 2060 design. Also found on the way: the typed
API's diameter field is stale for catalogue pipes (the size reference holds the real size), and one design pass is
not converged (R6: 1,429, 545, 49, 0 sizes changed over four passes). Fixed in R7: scenario alternatives and
calculation options are set *local* explicitly, exports read the catalogue size, the design repeats until no size
changes, and the job fails if an analysis run changes any pipe size.

## Open

- Confirm that the plots in unpiped land are meant to be carried at their nearest manhole (the reload loads the whole layer).
