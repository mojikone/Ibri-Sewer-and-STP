# Prompt for the W13/tmp3 chat — read the W14 plot flows, lay the concept gradients, audit self-cleansing

*Written 2026-09-11 from the design-flow discussion; rulings confirmed by the engineer the same day. Paste the block below
into the chat that works on the engine in `W13/tmp3`.*

---

Work in `W13/tmp3`, the live engine copy. First read `W14/docs/DESIGN_FLOWS_FOR_NETWORK.md` (which field and year for which
check, and the confirmed rulings in its §4 and §8) and `_BRAIN/02_DESIGN_CRITERIA.md` section 1 (the rows dated 2026-09-11)
and section 2 (the tier names). Show the PRESERVE-CHECK before changing any code. Run the test-boundary gate after each step.

1. **Read the W14 plot flows.** Replace the flat per-plot load — `OCCUPANCY` 5.0 × properties per plot × return, `PLOT_QADF_M3D`
   in `sewnet/criteria.py`, properties from `W4/shp/ELE_accounts.shp` — with each plot's own **`Q_ULT`** (sizing) and **`Q_2030`**
   (self-cleansing) from `W14/shp/PLOTS_load.shp`, both average dry-weather flow in m³/d. Check which plot file the engine reads:
   join on the cadastral `Name` if it is the same September MoH file, otherwise spatially by plot centroid. Report how many plots
   joined and the total flow joined against the layer's total. Properties per plot in a year: `G_DOM + (POP_year − POP) / OR_S`.
   `W13/py/sewnet/export_gems.py` must carry the same per-plot loads to SewerGEMS.
2. **Re-baseline the gate's flow numbers.** The layout gate must still hold: 71.6 km, about 1,415 chambers, zero pumping stations.
   The flow figures (Qadf 3,620 m³/d, peak 96 L/s) were built at the flat 5.0 and change; record the new ones.
3. **Size on `Q_ULT`.** Sum the plots upstream, peak per pipe — Merrimack for more than 100 properties (Qpdf = 2.65 Qadf^0.879,
   both in Ml/d), Peltier for 100 or fewer (PF = 1.5 + 1/√Qm, Qm in l/s) — and add infiltration of 720 l/d per km by pipe length.
4. **Lay the concept gradients.** G203 Table 11 minimum (tertiary pipes: Table 5), in **steps of 0.05 % (0.5 mm/m) for secondary
   pipes and 0.025 % (0.25 mm/m) for primary trunks of DN500 and up** — set `SLOPE_STEP` by pipe size. **The tractive force sets no
   gradient at the concept stage**: switch off any place the engine raises a minimum gradient from the Mara slope (for example at
   pipe heads). It is applied at preliminary design, once NWS confirms τ.
5. **Add the self-cleansing audit on the low case.** Flow = `Q_2030` × 0.61 of the plots upstream, peaked as in step 3 with the
   properties counted **connected** (2030 × 0.61) to choose Merrimack or Peltier, and **no infiltration**. The audit changes no
   size and no gradient. Each pipe takes one class:
   - **velocity pass** — at least 0.75 m/s at the low-case peak (G203 p26);
   - **tractive pass** — laid gradient at least the Mara slope Smin = K·τ^1.23·Q^−0.461 with **τ = 1 Pa**, **K = 2.33e-4 with Q in
     m³/s**, on the **true** flow — do not apply the `TRACTIVE_QMIN` 1.5 l/s floor here (G203 p27);
   - **needs washing** — everything else: the flushing list (G203 §4.2.6, p28).
   There is **no regrade class** and **no low-flow threshold**: a pipe laid to the guideline gradient that still carries too little
   flow needs washing, not a steeper pipe.
6. **Rename the tiers to the guideline's words** in tmp3 and after: `trunk` → **primary**, `sub main` → **secondary header**,
   `lateral` and `branch` → **secondary main sewer**. "Lateral" is reserved for the tertiary pipe (G203 p17, p21). W8 and older
   outputs keep their old values.
7. **Correct the rising-main limits** in `sewnet/stages/hydraulic.py` (`_size_rising_mains`, `V_MAX = 3.0`, docstring "0.75 and
   3.0 m/s (G203-p50 8.1)"). G203 p50 §8.1: at least 0.75 m/s at design minimum flow, **1.0 m/s for intermittent (start-stop)
   pumping**, 1.2 m/s in a vertical main, and **not greater than 2.5 m/s**. 3.0 m/s is the gravity sewer's limit (p27).
8. **Map and tabulate it.** Pipes coloured by class in QGIS (group `Claude W13 temp 3`), a shapefile field `CLEANSE`
   (velocity / tractive / washing), and a table of pipe counts and lengths by class and by tier, plus the washing list.
