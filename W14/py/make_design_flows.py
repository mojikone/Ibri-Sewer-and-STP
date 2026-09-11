"""W14 — the design-flow handoff for the network and the plant.

Writes, from the live W14 outputs and nothing typed by hand:
    W14/docs/DESIGN_FLOWS_FOR_NETWORK.md   the note an agent reads before designing
    W14/analysis/design_flows.json         the same numbers, machine-readable

Run after plot_class_v2_apply.py and growth_by_settlement.py:
    python W14/py/make_design_flows.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
W14 = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(W14, "report"))
import facts_w14 as F  # noqa: E402
import geopandas as gpd  # noqa: E402
import pandas as pd  # noqa: E402

CONNECT_2030 = 0.61          # Inception R0 connection ratio, reached by 2028
OPEN_YEAR = 2030             # TOR: construction year or 2030
INFIL_LD_KM = 720.0          # G1-p72, new networks
MARGIN = 0.10                # G1-p73, new STPs
MERRIMACK_PROPS = 100        # G1-p71, "over 100 properties"

fmt = F.fmt
t = F.totals()
ult = t["ultimate"]
S = gpd.read_file(os.path.join(W14, "shp", "Settlements_merged.shp"), ignore_geometry=True).set_index("SETTLE")
P = gpd.read_file(os.path.join(W14, "shp", "PLOTS_load.shp"), ignore_geometry=True)

# properties a plot holds in a year: existing dwellings plus the new people over the settlement's occupancy
props_now = float(P.G_DOM.sum())
props_2030 = float((P.G_DOM + (P.POP_2030 - P.POP) / P.OR_S.where(P.OR_S > 0)).fillna(P.G_DOM).sum())
props_ult = float((P.G_DOM + (P.POP_ULT - P.POP) / P.OR_S.where(P.OR_S > 0)).fillna(P.G_DOM).sum())

q = {y: float(t["q"][y]) for y in (2024, 2030, 2055, ult)}
pop = {y: float(t["pop"][y]) for y in (2024, 2030, 2055, ult)}
low = q[2030] * CONNECT_2030

rows = []
for s in S.sort_values("Q_ULT", ascending=False).index:
    r = S.loc[s]
    rows.append(dict(settlement=F.NAME.get(s, s.title()), key=s, q_2024=round(float(r.Q_2024), 1), q_2030=round(float(r.Q_2030), 1),
                     q_2030_low=round(float(r.Q_2030) * CONNECT_2030, 1), q_2055=round(float(r.Q_2055), 1), q_ult=round(float(r.Q_ULT), 1),
                     pop_2024=round(float(r.POP_2024)), pop_ult=round(float(r.POP_ULT)), sat_year=int(r.SAT_YEAR), plots=int((P.SETTLE == s).sum())))

data = dict(
    status="concept stage, W14 class v7 with unit-rate loads, 2026-09-11",
    source_files=dict(plots="W14/shp/PLOTS_load.shp", settlements="W14/shp/Settlements_merged.shp",
                      workbook="W14/analysis/W14_growth_by_settlement.xlsx", method="W14/docs/CONCEPT_NOTE_SATURATION_AND_LOAD.md",
                      report="W14/report/R2/Ibri_Concept_Design_Report_R2.pdf, sections 14 and 15"),
    fields=dict(QADF="average dry-weather sewage of the plot in 2024, m3/d", Q_2030="the same in 2030 (the opening year), m3/d",
                Q_2055="the same in 2055, m3/d", Q_ULT=f"the same at saturation ({ult}), m3/d", POP="people 2024", POP_2030="people 2030",
                POP_ULT="people at saturation", G_DOM="domestic properties 2024", OR_S="occupancy of the settlement", SETTLE="settlement"),
    rules=dict(size_on="Q_ULT, 100 % connected (G1-p73: coverage 100 % by the end of the period)",
               self_cleansing_on=f"Q_{OPEN_YEAR} x {CONNECT_2030}, peaked, fed to the velocity and the tractive-slope tests",
               opening_year=OPEN_YEAR, connection_ratio_2030=CONNECT_2030,
               peak_over_100_properties="Merrimack, Qpdf = 2.65 Qadf^0.879, both in Ml/d (G1-p71)",
               peak_100_properties_or_fewer="Peltier, PF = 1.5 + 1/sqrt(Qm), Qm in l/s (G1-p72)",
               peak_factor_cap="hourly PF should not exceed 5.0: a recommendation (G1-p72)",
               infiltration_l_per_day_per_km=INFIL_LD_KM, infiltration_applies="per pipe, by length; never per plot (G1-p72)",
               stp_margin=MARGIN, tankers="pending: no filling-station records held; not in any flow",
               properties_per_plot_in_year="G_DOM + (POP_year - POP) / OR_S",
               tractive_tension="1 Pa at the concept stage (engineer 2026-09-11); no value in G203 (GAP-9), NWS to confirm",
               low_flow_1_5_l_s="not in PAM-GUD-203 and not used",
               rulings_confirmed=dict(low_case_property_count=f"properties of {OPEN_YEAR} x {CONNECT_2030} (connected)",
                                     low_case_infiltration="left out", classes=["velocity pass", "tractive pass", "needs washing"],
                                     regrade_class="none", low_flow_threshold="none",
                                     mara_constant="K = 2.33e-4 with Q in m3/s, true flow, no floor", tau_pa=1.0,
                                     concept_gradients="G203 Table 11 minimum; steps 0.05 % for secondary pipes, 0.025 % for trunks DN500 and up",
                                     tractive_sets_gradient="no, at the concept stage; applied at preliminary design once NWS confirms tau",
                                     engine_tier_lateral_and_branch="secondary main sewer", status="confirmed by the engineer, 2026-09-11")),
    totals={str(y): dict(people=round(pop[y]), qadf_m3d=round(q[y], 1)) for y in (2024, 2030, 2055, ult)},
    low_case_2030_m3d=round(low, 1), stp_ultimate_with_margin_m3d=round(q[ult] * (1 + MARGIN), 1),
    properties=dict(y2024=round(props_now), y2030=round(props_2030), ultimate=round(props_ult)),
    free_meters=dict(count=126, note="more than 15 m from any plot: no load in the plot table (30 dwellings, about 130 people)"),
    settlements=rows,
)
with open(os.path.join(W14, "analysis", "design_flows.json"), "w", encoding="utf-8") as fh:
    json.dump(data, fh, indent=1, ensure_ascii=False)


def md(cols, rs):
    return "| " + " | ".join(cols) + " |\n|" + "---|" * len(cols) + "\n" + "\n".join("| " + " | ".join(str(c) for c in r) + " |" for r in rs)


tot = md(["Year", "People", "Qadf, m³/d", "Note"], [
    ["2024", fmt(pop[2024]), fmt(q[2024]), "today, from the meters"],
    [f"{OPEN_YEAR}", fmt(pop[2030]), fmt(q[2030]), f"opening year; **low case × {CONNECT_2030} = {fmt(low)} m³/d**"],
    ["2055", fmt(pop[2055]), fmt(q[2055]), "model year"],
    [f"**{ult}, saturation**", f"**{fmt(pop[ult])}**", f"**{fmt(q[ult])}**", f"sizing case; +10 % at the plant = {fmt(q[ult] * (1 + MARGIN))} m³/d"]])
sett = md(["Settlement", "Q 2024", "Q 2030", f"Q 2030 × {CONNECT_2030}", "Q 2055", "Q saturation", "Full in", "Plots"],
          [[r["settlement"], fmt(r["q_2024"]), fmt(r["q_2030"]), fmt(r["q_2030_low"]), fmt(r["q_2055"]), fmt(r["q_ult"]), r["sat_year"], fmt(r["plots"])] for r in rows])

note = f"""# Design flows for the network and the plant — read this before designing

*Concept stage. Generated by `W14/py/make_design_flows.py` from the live W14 outputs on 2026-09-11; rerun it
after any change to the load chain. The same numbers, machine-readable: `W14/analysis/design_flows.json`.*

**One sentence:** every plot in `W14/shp/PLOTS_load.shp` carries its average dry-weather sewage flow for 2024,
{OPEN_YEAR}, 2055 and saturation ({ult}); **size every pipe on the saturation flow `Q_ULT`, check self-cleansing on
`Q_{OPEN_YEAR}` × {CONNECT_2030}, peak per pipe, add infiltration per pipe, and size the plant on the settlement totals by year.**

---

## 1. Where the flows are

| File | What it holds |
|---|---|
| `W14/shp/PLOTS_load.shp` | 77,265 plots. **`QADF`** (2024), **`Q_2030`**, **`Q_2055`**, **`Q_ULT`**: average dry-weather sewage, m³/d. `POP`, `POP_2030`, `POP_2055`, `POP_ULT`: people. `G_DOM`: domestic properties 2024. `OR_S`: the settlement's occupancy. `SETTLE`: settlement. The streams behind `QADF`: `W_*` water and `S_*` sewage, m³/d |
| `W14/shp/Settlements_merged.shp` | 25 settlements. `Q_2024` … `Q_{ult}` at five-year steps, `Q_ULT`, `SAT_YEAR`, and the rates behind them. The plots sum to it in every column |
| `W14/analysis/W14_growth_by_settlement.xlsx` | sheet *Qadf by year m3d*: every settlement, every year 2024–2100; *Five-year Qadf* as the report prints it |
| `W14/docs/CONCEPT_NOTE_SATURATION_AND_LOAD.md` | the method, step by step |
| `TUTORIALS/T04/` | the whole method taught, with worked Ibri numbers |
| Report R2 §14–15 | the client-facing statement of all of the above |

The flow of an existing plot, in l/d, is
**Q = 0.85 × 164 × OR × N_dom + 0.54 × (U_nd × N_nd + U_gov × N_gov + 93 × workers)** (report 15.4); a future plot carries
its people × 171.3 l/d. **The plot carries average flow only.** It does not carry peak, infiltration, tankers or private wells.

## 2. Which flow for which check

| Check | Flow | Rule |
|---|---|---|
| **Pipe size and capacity** (d/D ≤ 0.65 up to 350 mm, ≤ 0.50 above; v ≤ 3.0 m/s) | **`Q_ULT`** of the plots upstream, summed, then peaked, plus infiltration | saturation, 100 % connected (G1-p73: coverage 100 % by the end of the period). Under-estimating surcharges the pipe |
| **Self-cleansing** (0.75 m/s at peak flow, 0.90 preferred; and the tractive slope) | **`Q_{OPEN_YEAR}` × {CONNECT_2030}** of the plots upstream, summed, then peaked | the opening year the TOR names (construction year or {OPEN_YEAR}) at the Inception R0 connection ratio. **Over-estimating is the danger here**: the pipe is declared self-cleansing while it silts |
| **Plant capacity and phasing** | the settlement totals by year (workbook) + infiltration of the network + 10 % margin; tankers when their records arrive | G1-p73 §7.4.5; G203 p65 Tab 29 |

**Never use saturation × a connection ratio for self-cleansing.** It mixes {ult} people with a 2028 connection share, and it
gives a pipe in a new district {int(CONNECT_2030 * 100)} % of its saturation flow in {OPEN_YEAR}, when it carries almost nothing. Whole
area: {fmt(q[ult])} × {CONNECT_2030} = {fmt(q[ult] * CONNECT_2030)} m³/d, against {fmt(low)} m³/d really expected in {OPEN_YEAR}.

## 3. Peak, infiltration and units, per pipe

1. **Sum the plots upstream** of the pipe: m³/d. Count the properties upstream: `G_DOM + (POP_year − POP) / OR_S` per plot.
2. **Peak.** More than 100 properties: **Merrimack**, Qpdf = 2.65 Qadf^0.879, both in **Ml/d** (m³/d ÷ 1,000) (G1-p71).
   100 or fewer: **Peltier**, PF = 1.5 + 1/√Qm, Qm in **l/s** (m³/d ÷ 86.4) (G1-p72). The guideline recommends the hourly
   peak factor not exceed 5.0; it is a recommendation, not a cap to apply silently.
3. **Infiltration**: 720 l/d per km of new sewer, by the pipe's own length, added along the run; never a plot load (G1-p72).
   Storm water is not considered.
4. **Early-year check**: the same summation on `Q_{OPEN_YEAR}` × {CONNECT_2030}, peaked the same way with the properties counted
   **connected** ({OPEN_YEAR} × {CONNECT_2030}), and **no infiltration**, gives the flow for the velocity test and the tractive test.

## 4. Gradients and the self-cleansing audit (engineer, 2026-09-11)

**Gradients at the concept stage** are the G203 Table 11 minimum (tertiary pipes: Table 5), laid in **steps of 0.05 % (0.5 mm/m)
for secondary pipes and 0.025 % (0.25 mm/m) for primary trunks of DN500 and up**. **The tractive force sets no gradient at this
stage**; it is applied to the gradients at the preliminary design, once NWS confirms the tractive tension. G203 §4.2.2.1 (pp 25–27)
asks for both approaches to set the minimum gradient, so this is a departure, recorded in report R2 §10.1 for NWS confirmation.

**The audit**, on the low case (§3.4), gives every pipe one of three classes:

| Class | Test | Action |
|---|---|---|
| **Velocity pass** | ≥ 0.75 m/s at the low-case peak (G203-p26) | none |
| **Tractive pass** | laid gradient ≥ Mara Smin = K·τ^1.23·Q^−0.461 with **τ = 1 Pa**, **K = 2.33 × 10⁻⁴, Q in m³/s**, on the true flow (no floor) (G203-p27) | none |
| **Needs washing** | everything else | on the flushing list (G203 §4.2.6, p28: more frequent inspection and cleansing in the early years); **not regraded, not upsized** |

- **No regrade class**: a pipe laid to the guideline gradient that still carries too little flow needs washing, not a steeper pipe.
- **No low-flow threshold.** 1.5 L/s is not in PAM-GUD-203 and is not used. The engine's `TRACTIVE_QMIN` floor must not be applied in the audit.
- **τ = 1 Pa is the concept-stage value** (G203 gives none, GAP-9); NWS is asked to confirm it before preliminary design.

## 5. Pipe tiers — the guideline's words (G203 p17, p21)

| Guideline | Meaning | W8/W13 `TIER` (old) |
|---|---|---|
| **Primary** — trunk main | the trunk mains to the plant | `trunk` |
| **Secondary** — header | the collecting mains of a district | `sub main` |
| **Secondary** — main sewer | the street sewer every plot connects to | `lateral` ← **clashes** |
| **Tertiary** — rider and lateral sewers | the short pipes from the house connection chamber to the main sewer, lateral ≤ 45 m, min 1 % | not modelled |

From W13/tmp3 on, the street pipe is a **secondary main sewer**; "lateral" means only the tertiary pipe.

## 6. The engine does not read these flows yet

`W13/py/sewnet/criteria.py` (and the tmp copies) loads every plot with the same flat figure: `OCCUPANCY` 5.0 × properties per
plot × a fixed return (`PLOT_QADF_M3D`), with properties from `W4/shp/ELE_accounts.shp`. **Before any design run, replace that
with the plot's own `Q_ULT` and `Q_{OPEN_YEAR}` from `PLOTS_load.shp`** — joined on the cadastral `Name` where the engine uses the
same September MoH plot file, otherwise spatially by plot centroid [Likely: check which plot file the engine reads].

**The test-boundary gate changes in part.** Its layout numbers — 71.6 km, about 1,415 chambers, zero pumping stations — must still
hold. Its **flow numbers (Qadf 3,620 m³/d, peak 96 L/s) were built at the flat 5.0 and are re-baselined** once the engine reads
these loads.

## 7. The numbers

{tot}

Properties: {fmt(props_now)} in 2024, {fmt(props_2030)} in {OPEN_YEAR}, {fmt(props_ult)} at saturation.

**By settlement, average dry-weather sewage, m³/d:**

{sett}

## 8. Rulings (engineer, 2026-09-11, confirmed)

| Question | Ruling |
|---|---|
| Property count for Merrimack or Peltier in the low case | **connected**: properties of {OPEN_YEAR} × {CONNECT_2030} |
| Infiltration in the low case | **left out** (G201 is silent; §7.4.4 p73 asks only that the early flow be checked for self-cleansing) |
| Classes | **velocity pass, tractive pass, needs washing**; no regrade, no low-flow threshold |
| Mara constant | **K = 2.33 × 10⁻⁴ with Q in m³/s**, τ = 1 Pa at the concept stage |
| Gradients at concept | **Table 11 minimum, steps 0.05 % (secondary) and 0.025 % (trunks DN500 and up)**; tractive sets no gradient until preliminary |
| Engine `TIER` values `lateral` and `branch` | **secondary main sewer** |

## 9. What is not in the flows, and must not be assumed

- **Tanker supply and sewage tankers**: no filling-station or delivery records held; not in any flow (report §10.1).
- **Private wells and other non-network water**: not assessed; every flow is on the network-accounted basis (report §10.1).
- **The 126 meters more than 15 m from any plot** (30 dwellings, about 130 people): no load in the plot table. Open with the engineer.
- **Peak, infiltration and the plant margin**: added in the design, never stored on the plot.

## 10. Rerun order

`W14/py/plots_meters_load.py` (in QGIS) → `W14/py/plot_class_v2_apply.py` → `W14/py/growth_by_settlement.py` →
`W14/py/make_design_flows.py` → `W14/report/build.py --pdf`.
"""
with open(os.path.join(W14, "docs", "DESIGN_FLOWS_FOR_NETWORK.md"), "w", encoding="utf-8", newline="\n") as fh:
    fh.write(note)
print("wrote DESIGN_FLOWS_FOR_NETWORK.md and design_flows.json | low case", fmt(low), "| props", fmt(props_now), fmt(props_2030), fmt(props_ult))
