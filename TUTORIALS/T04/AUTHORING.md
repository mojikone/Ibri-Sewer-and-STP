# T04 — authoring brief for chapter writers

T04 is **one tutorial that carries the whole method**, from the electricity meter to a sized, self-cleansing gravity sewer
and a sized plant, with the appraisal. It replaces T01 (flows), T02 (gravity sewer hydraulics) and T03_R01 (concept
methodology) as the teaching reference; those three stay frozen as the record. The reader is **the project's hydraulic
engineer, who wants to learn and check the method** — a professional, so no fundamentals, but every step made explicit.

## Every step has the same five parts

1. **What it is for** — one or two sentences.
2. **The rule** — the equation (native OMML via `omml.py`, numbered with `D.next_eq()`, followed by a symbol table) or the
   decision rule, stated exactly.
3. **The source** — guideline and page (G203-p##, G201-p##, G202-p##), or "project rule (engineer, date)", or "outside
   assumption, tagged". Guideline values come from `_BRAIN/02_DESIGN_CRITERIA.md` or the PDF in `Data/`; **never from memory**.
4. **A worked Ibri number** — a real number from the live data, read from `facts_w14` (see below), not typed.
5. **Where it lives** — the script and the field or sheet that does it (e.g. `W14/py/plot_class_v2_apply.py`, field `U_NDOM`).

End each chapter with a short **"Check it yourself"** list: how the reader verifies the step against the data.

## Numbers

- Import the live numbers: `sys.path.append(<repo>/W14/report)  (append, so T04's doc.py is found first)` then `import facts_w14 as F`. Useful: `F.totals()`,
  `F.settlement_table()`, `F.plot_summary()`, `F.meter_counts()`, `F.crt_summary()`, `F.five_year_rows("pop"|"q")`,
  `F.routes()`, `F.own_growth_saturation()`, `F.unit_rate_rows()`, `F.example_plot()`, `F.growth_rates()`, `F.ibri_receivers()`,
  `F.census_rate()`, `F.fmt(x, nd)` (half-up with thousands separator). Constants: `F.LPCD, F.R_ND, F.R_GOV, F.L_IND,
  F.RET_DOM, F.RET_ND, F.OR_FLOOR, F.BASE_YEAR`. The design-flow numbers: `W14/analysis/design_flows.json`.
- Current headline (for orientation only — print them from F): 2024 119,893 people / 20,852 m³/d; saturation 2070 at
  349,029 people / 60,099 m³/d; capacity 229,136; Ibri full 2056.
- A number that cannot come from F or the JSON (a guideline constant, a table value) must carry its page.

## Settled rules to teach (do not re-derive, do not contradict)

- Load chain, W14 class v7: `W14/docs/CONCEPT_NOTE_SATURATION_AND_LOAD.md`, report R2 §14–15 (`W14/report/rpt_cd.py`).
- Existing plot, l/d: **Q = 0.85 × 164 × OR × N_dom + 0.54 × (U_nd × N_nd + U_gov × N_gov + 93 × N_w)**; U_nd = 0.22 × 164 × P_s /
  N_nd,s; U_gov = 0.14 × 164 × P_s / N_gov,s (meters outside the estates). Future plot = people × 171.3 l/d.
- **Two flow cases (engineer, 2026-09-11): size on `Q_ULT`; self-cleansing on `Q_2030` × 0.61**, peaked per pipe (Merrimack
  over 100 properties in Ml/d; Peltier at or under 100, in l/s), fed to both the velocity and the tractive-slope tests. Never
  saturation × a ratio. Four classes: velocity pass, tractive pass, early cleansing, fails both → regrade.
- **G203 §4.2.2.1 (pp 25–27)**: two approaches shall be used; the steeper gradient governs; at the head of a system tractive
  force alone. **τ has no value in G203 (GAP-9)**. **§4.2.6 (p28)** gives no threshold. **1.5 L/s is not in G203** — Mara, tagged.
- **Tier names (G203 p17, p21)**: primary = trunk mains; secondary = headers and main sewers under the streets; tertiary =
  rider and lateral sewers (lateral ≤ 45 m, min 1 %). **Say "secondary main sewer" for the street pipe; "lateral" only for the
  tertiary pipe.** State the mapping from the old engine `TIER` values once.
- Infiltration 720 l/d/km per pipe (G1-p72); plant +10 % (G1-p73); hourly PF ≤ 5.0 is a recommendation (G1-p72).
- Depth: 12 m cover limit with no exceptions (project doctrine, G203-p33 context); pumping station before that point.
- Departures and pending items: report R2 §10.1 (`W14/report/rpt_cd.py`): occupancy from meters, Tab 12 not used, placement on
  meters, the estates, tanker supply, other water sources, connection ratio, design-flow standard, growth beyond the forecast.

## Sources to port (update, do not copy blindly)

- `TUTORIALS/T01_Sewage_Flow_and_Load_Calculation.md` — flow chain, peaks, organic loads, STP incoming flow, R0 reconciliation.
- `TUTORIALS/T02/t02_content.py` — gravity sewer hydraulics, every constraint with its page, worked examples.
- `TUTORIALS/T03_R01/body.py, body2.py, body3.py, body4.py, front.py, EQUATION_REGISTER.md` — the concept methodology.
- `_BRAIN/02_DESIGN_CRITERIA.md`, `_BRAIN/07_PROJECT_STATE.md` §2 (doctrine), `_BRAIN/08_DESIGN_PHILOSOPHY.md`.
- W14: `W14/docs/*.md`, `W14/report/rpt_cd.py`, `W14/report/rpt_app.py`, `W14/docs/DESIGN_FLOWS_FOR_NETWORK.md`.
Where an older tutorial disagrees with the settled rules above (5.32, flat per-plot loads, "lateral" for the street pipe), the
settled rule wins, and the chapter says in one sentence what changed.

## The builder API (`TUTORIALS/T04/doc.py`, `omml.py`)

```python
import doc as D, omml as M
UP, R = M.up, M.r
D.h(d, 1|2|3, "text", page_break=False)        # numbered headings are written in the text: "7   Title", "7.2   Title"
D.p(d, "text", bold=False, italic=False, size=None, colour=None, align=None, space_after=None)
D.bullet(d, "text", lead="Bold lead. ")         # D.numbered(d, "text", lead=None, restart=False)
D.callout(d, "Title", "text")                   # boxed caution; fill="EAF1F8", colour=D.MID for a neutral note
D.tab_caption(d, "caption"); D.table(d, headers, rows, widths=[cm...], font=9)   # "**x**" in a cell renders bold
D.picture(d, os.path.join(IMG, "name.png"), 15.5); D.fig_caption(d, "caption")  # caption AFTER the picture
eq = D.next_eq(); M.display(d, M.seq(M.sub(R("Q"), UP("adf")), M.EQ, R("2.65"), M.TIMES, ...), number=eq)
# M.frac(num, den), M.sqrt(e), M.sup(base, s), M.sub(base, s), M.delim(e), M.nary("∑", lo, hi, e); M.EQ, M.PLUS, M.MINUS, M.TIMES
```
Symbol tables: `D.table(d, ["Symbol", "Meaning", "Unit"], rows, widths=[2.6, 10.4, 3.5], font=9)`. Dimensionless unit: "—".
Units: l/d, l/s, m³/d, Ml/d, m/s, Pa, mm, m. Figures available in `TUTORIALS/T04/img/` (T03 flowcharts F1–F14, R2 charts
C02–C12, flowcharts D3/D6/D7, maps M04/M05/M07/M09/M10, appraisal_method).

## Style

Plain words, full sentences, a colleague explaining at a desk. One idea per sentence. No "It should be noted", no rule-of-three
padding, no em-dash tics. Say what a thing is before what follows from it. Headings numbered in the text. Figure and table
numbers come from the captions only. **No internal chatter** ("W14 class v7", "the engineer said") in the running text except
in the "Where it lives" part and the source line, where script, field and dated project rules belong.

## Your module

Write `TUTORIALS/T04/chNN_name.py` exposing one function per chapter, each `def cX_title(d):`. Put `import doc as D`,
`import omml as M`, `import facts_w14 as F` (after the sys.path insert) at the top. **Smoke-test before you finish**:
`python -c "import sys; sys.path.insert(0,'TUTORIALS/T04'); import doc as D, chNN_name as m; d=D.new_document(); m.cX_title(d); d.save('TUTORIALS/T04/_test/chNN.docx')"`
must run without error. Do not edit `doc.py`, `omml.py` or any file outside your module and `_test/`.
