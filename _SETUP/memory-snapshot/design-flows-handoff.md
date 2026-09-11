---
name: design-flows-handoff
description: Where a network or plant design takes its flows, and the two flow cases (size on Q_ULT, self-cleansing on Q_2030 x 0.61) — engineer 2026-09-11
metadata:
  type: project
---

**Any network or plant design reads `W14/docs/DESIGN_FLOWS_FOR_NETWORK.md` first** (generated with `W14/analysis/design_flows.json` by `W14/py/make_design_flows.py` from the live W14 outputs). The flows per plot are in `W14/shp/PLOTS_load.shp`: `QADF` 2024, `Q_2030`, `Q_2055`, `Q_ULT`, average dry-weather, m³/d.

- **Size every pipe on `Q_ULT`** (saturation, 100 % connected per G1-p73).
- **Self-cleansing on `Q_2030` × 0.61**: 2030 is the TOR opening year (construction year or 2030), 0.61 the Inception R0 connection ratio. Peaked per pipe with properties counted **connected** (Merrimack > 100 in Ml/d, Peltier ≤ 100 in l/s), **no infiltration**. **Three classes (engineer 2026-09-11): velocity pass (≥ 0.75 m/s); tractive pass (laid gradient ≥ Mara Smin at τ = 1 Pa, K = 2.33e-4 m³/s, true flow, no floor); needs washing.** No regrade class — a pipe laid to the guideline gradient that still carries too little flow needs washing, not a steeper pipe. No 1.5 L/s threshold.
- **Gradients at concept (engineer 2026-09-11): G203 Table 11 minimum in 0.05 % steps for secondary pipes, 0.025 % for trunks DN500+.** The tractive force sets no gradient until preliminary design — a departure from G203 §4.2.2.1 recorded in R2 §10.1 for NWS; he checks it with the client. W13 rule 8 (a tenth of the minimum) is superseded.
- **Never saturation × a connection ratio** — the engineer proposed it; it mixes 2070 people with a 2028 share and gives new districts 61 % of saturation in 2030, where silting happens. He agreed to the two-case rule.
- τ has no value in G203 (GAP-9): **1 Pa at concept**, NWS to confirm. **1.5 L/s is not in G203** and is not used.
- **Tier words are the guideline's**: primary trunk, secondary header and main sewer, tertiary rider and lateral. The street pipe is a "secondary main sewer", never a "lateral".
- **The W13 engine still loads a flat 5.0 per plot.** The engineer takes `W14/docs/PROMPT_W13_SELFCLEANSING_AUDIT.md` to the W13/tmp3 chat, which wires the plot loads in, re-baselines the gate's flow, lays the concept gradients and runs the audit.

**Why:** the engineer will design the network in other chats and asked that every chat find the flows without searching the report. **How to apply:** point to the note, never copy numbers from memory; rerun `make_design_flows.py` after any load change. The method is taught in `TUTORIALS/T04/`. Related: [[concept-saturation-population-and-load]], [[load-basis-locked-tier-a-volume]].
