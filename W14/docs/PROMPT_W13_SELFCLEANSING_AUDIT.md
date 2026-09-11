# Prompt for the network-design chat — W14 loads into the engine, then the self-cleansing audit

*Written 2026-09-11 from the design-flow discussion. Paste the block below into the chat that works on the W13 engine.*

---

Work in `W13/tmp3` (the live engine copy). Read `W14/docs/DESIGN_FLOWS_FOR_NETWORK.md` and `_BRAIN/02_DESIGN_CRITERIA.md`
(section 1, the two-approach and two-flow-case rows, and section 2, the tier names) first. Show the PRESERVE-CHECK before
changing any code, and run the test-boundary gate after each step.

1. **Wire the W14 loads into the engine.** Replace the flat per-plot load (`OCCUPANCY` 5.0 × properties per plot × return,
   `PLOT_QADF_M3D` in `sewnet/criteria.py`) with each plot's own `Q_ULT` and `Q_2030` from `W14/shp/PLOTS_load.shp`, joined on
   the cadastral `Name` if the engine reads the same September MoH plot file, otherwise spatially by plot centroid — check
   which file it reads first. Properties per plot for the Merrimack threshold: `G_DOM + (POP_year − POP) / OR_S`.
2. **Re-baseline the gate's flow numbers.** The layout gate must still hold (71.6 km, about 1,415 chambers, zero pumping
   stations). The flow figures (Qadf 3,620 m³/d, peak 96 L/s) were built at the flat 5.0 and change; record the new ones.
3. **Size on `Q_ULT`**: sum upstream, peak (Merrimack over 100 properties, both flows in Ml/d; Peltier at or under 100, flow in
   l/s), add infiltration 720 l/d per km by pipe length.
4. **Add the G203 §4.2.2.1 self-cleansing audit on the low case `Q_2030` × 0.61**, peaked the same way and fed to both the
   velocity test (0.75 m/s at peak) and the Mara tractive slope (Smin = K·τ^1.23·Q^−0.461, K = 5.5e-3 with Q in l/s). **τ has no
   value in G203 (GAP-9): make it a parameter, report the class counts against it, and do not present one τ as the guideline's.**
   The audit changes no pipe size or gradient.
5. **Class every pipe** (primary, secondary header, secondary main sewer — not only one tier): **velocity pass**, **tractive
   pass**, **early cleansing** (low flow — flushing list per §4.2.6, not upsized), **fails both → regrade** (real flow, too flat).
   The early-cleansing threshold: **1.5 L/s is not in PAM-GUD-203** (whole PDF searched); if used, tag it as an outside (Mara)
   assumption in the output and the map legend.
6. **Rename the tiers to the guideline's words in tmp3 and after**: `trunk` → primary, `sub main` → secondary header,
   `lateral` → secondary main sewer. "Lateral" is reserved for the tertiary pipe (G203 p17, p21). W8 and older keep their values.
7. **Map it**: the pipes coloured by class, in QGIS in the `Claude W13 temp 3` group, plus a shapefile field `CLEANSE` and a
   table of counts and lengths per class and per tier.
