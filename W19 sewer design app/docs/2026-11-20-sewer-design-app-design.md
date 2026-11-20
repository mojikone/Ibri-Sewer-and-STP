# Sewer design app — design (spec)

2026-11-20 · W19 · status: **for the engineer's approval** · W18 stays the live design; W19 is a tool folder

## 1. What it is, in one paragraph

A local application for sewer and stormwater network modelling and design: an interface over our own engines, with an
AI assistant inside it. It aims to give SewerGEMS's answers, and every engine is checked against SewerGEMS through
the VM bridge before it counts. The W18 engine already gives SewerGEMS's sanitary design on all 19,083 Ibri pipes in
seconds, where SewerGEMS takes about 44 minutes. That engine is phase 1. Everything after it is added one phase at a
time, each phase with its own gate.

Engineer's brief, 2026-11-20 (verbatim): *"I want the model UI be as flexible as sewergems, for stormwater it can use
the available samples online from Bentley or other sources. And the engine that can solve those networks too. I want
it to check its engines output with sewegems, and make it 100% working. And test it end to end. Go with all default
and recommended ones."*

## 2. The rule underneath everything

**SewerGEMS is the referee.** An engine option counts only when a SewerGEMS run of the same model agrees with it,
element by element, within a tolerance fixed *before* the comparison is run. Until then the app labels that option
**unverified** in the interface and in every export.

**"100 % working" means**: every element of every verification case is within its tolerance, with no exemptions (a
skipped element reads as a pass, so none are skipped). A failing case blocks its phase. The tolerance is never
widened after seeing a result; a mismatch is investigated by black-box experiment (change one input, compare again).

## 3. Legal boundary (clean room), not negotiable

| Allowed | Not allowed |
|---|---|
| Published methods: PAM-GUD-201/202/203 (pages in `_BRAIN/02_DESIGN_CRITERIA.md`), Colebrook-White, Manning, standard-step GVF, Peltier, Merrimack, the rational method, HEC-22, SCS/NRCS TR-55, EPA SWMM 5 (public domain) | Decompiling, disassembling or patching Bentley binaries |
| SewerGEMS's published documentation (help, manuals) as a description of methods, cited | Reading SewerGEMS's internals or proprietary file formats (`.stsw`, `.sqlite`) directly |
| Driving the licensed SewerGEMS through its documented OpenFlows API, inside the VM, and comparing its exported results | Committing Bentley's sample models, or data exported from them, to the public repo |
| EPA SWMM sample models (public domain) in the repo | Any route from the VM to the internet |

This statement goes into the app's README and the About box. Downloads happen on the host only; the file name, source
and size are stated, and the engineer says yes, before each one.

## 4. What "as flexible as SewerGEMS" means here, and when each part arrives

[Likely] The feature list below is SewerGEMS CONNECT's, from its published documentation and normal use. It is the
target, not a promise for phase 1.

| SewerGEMS capability | Our part | Phase |
|---|---|---|
| Sanitary loading: unit loads, Extreme Flow Setup peaking tables, infiltration per length | `engine/loads`, `engine/flows` | 1 |
| Steady gravity hydraulics, Colebrook-White, normal depth | `engine/hydraulics` | 1 |
| Automated design: catalogue, velocity / cover / slope / d/D constraints, crowns matched | `engine/design` | 1 |
| The W18 design chain: steepen to 0.75 m/s, re-lay, cut / join / fewer stations, names, station sizing | `engine/chain` | 1 |
| Map, property grid (edit attributes), scenarios, run, results tables, profile, export GPKG/DXF/CSV | `api`, `web` | 1 |
| AI assistant: run, query, explain with the guideline page, what-if as a new scenario | `assistant` | 1 |
| Manning, Kutter, Darcy-Weisbach, Hazen-Williams friction (Manning was offered for phase 1 "with its own gate"; its gate needs a SewerGEMS run of the network on Manning, which needs the phase-2 bridge harness, so it moves here) | `engine/hydraulics` | 2 |
| GVF backwater (tailwater, surcharge), structure headloss methods (standard, absolute, generic, AASHTO, HEC-22) | `engine/gvf` | 2 |
| Pressure network: pumps with curves, wet wells, force mains, pressure junctions, simple controls | `engine/pressure` | 2 |
| The referee harness: build a model in SewerGEMS from our project through the API, run a named solver, export | `referee` | 2 |
| Full editing: draw / move / split / delete / connect, prototypes, undo/redo, alternatives with inheritance, scenarios manager, FlexTables with global edit, engineering libraries, calculation options, validation, colour coding, annotation, selection sets and queries, GIS import with field mapping | `model`, `web` | 3 |
| Stormwater, steady: catchments, rational and modified rational, IDF curves, time-of-concentration methods, inlets and gutters (HEC-22 on-grade and sag, bypass), catch basins, GVF-rational | `engine/storm` | 4 |
| Dynamic: EPA SWMM 5 engine (SewerGEMS's "Explicit" solver is SWMM 5), hydrographs, SCS unit hydrograph, SWMM runoff, RTK, ponds and outlet structures, storage, pattern loads | `engine/swmm` | 5 |
| SewerGEMS's own "Implicit" dynamic solver | compared within a stated tolerance only; its numerics are Bentley's | 5 |
| Report tables, profile sheets, PDF | `reports` | 6 |

## 5. Architecture

One unit, one job. Each is testable without the others.

| Unit | Does | Depends on |
|---|---|---|
| `sewerapp/model/` | element-type registry (one schema per element type drives the property grid, validation, storage, API and the assistant's tool descriptions); network; alternatives and scenarios; project store | — |
| `sewerapp/io/` | readers and writers: W18 CSV (the bridge's export format), GeoPackage, SHP, DXF, the referee input set; SWMM `.inp` (phase 5) | `model` |
| `sewerapp/engine/` | pure computation on arrays: hydraulics, loads, flows, design, chain; later gvf, pressure, storm, swmm | `model` |
| `sewerapp/w18port/` | the W18 scripts copied with their paths moved into a config; the reference implementation the engine is gated against | fixtures |
| `sewerapp/referee/` | comparisons with SewerGEMS exports; from phase 2 the bridge job templates (C# helpers and PowerShell copied from W18's `sewergems_api`) | `io` |
| `sewerapp/api/` | FastAPI on 127.0.0.1 only: project, elements, scenarios, run, results, profile, export, assistant stream | all |
| `web/` | browser interface: React + TypeScript + Vite, MapLibre GL for the map, AG Grid Community for tables | `api` |
| `sewerapp/assistant/` | Claude through the Messages API with the SDK's tool runner; tools call the API layer | `api` |

**Project file: an open GeoPackage** (QGIS opens it directly): one layer per element type, tables for alternatives,
scenarios, calculation options and results. No proprietary format of ours either.

**Alternatives and scenarios** follow SewerGEMS's published concept: a scenario picks one alternative of each type
(physical, sanitary loading, design constraints, calculation options, later boundary, hydrology ...); a child
alternative stores only what it changes from its parent. Phase 1 needs physical, loading, constraints and routing
(which outfalls are plant inlets); the full manager arrives in phase 3.

**Coordinates.** Ibri is EPSG:32640, reprojected to WGS84 for the map. Public stormwater samples often have no CRS; the
map then runs in local coordinates with no basemap.

## 6. Engines, phase 1 (what W18 proved)

| Step | Rule | Source |
|---|---|---|
| Flow | PF × cumulative upstream unit load (its upstream manhole included) + 720 L/day per km of upstream conduit (its own length included) + transfers, not re-peaked | G201 p71–72; model's Extreme Flow Setup |
| Peaking table | 'Peltier100-Merriamck': Peltier to 1 L/s, Merrimack above, step row 1.001 L/s → 3.56, linear between rows | the model's table |
| Friction | Colebrook-White, ks 1.5 mm, ν 1.141e-6 m²/s | p24, p25, p28 |
| Limits | d/D ≤ 0.65 to DN355, ≤ 0.50 above; 3.0 m/s maximum | p27 Table 10, p27 |
| Gradient | Table 11 minimum of the size | p29 Table 11 |
| Size | smallest catalogue size that carries the flow at the d/D limit at the gradient of the pipe's current size, pass after pass from the modeller's sizes until nothing changes; full catalogue (DN1200 included) | SewerGEMS's procedure, proved blind |
| Inverts | crowns matched, 1.3 m cover over the soffit | p33 §4.6.3 |
| Chain | steepen above DN200 to 0.75 m/s at the 2031 peak up to 0.75 %, one gradient per street run; re-lay; cut where deeper than 12 m for good; join by gravity within one Table 12 spacing; the engineer's fixed stations; self-cleansing at 2031 and 2036; names P# / P#L#; stations sized | `references/network_design.md` §3 of the skill |

**One change from W18, kept under the gate:** W18 reads each subnetwork's outfall flow for the transfers from
SewerGEMS exports (`bridge\out\w18\f0`). The app computes it itself. It must equal those exports within 0.1 %, and the
design must stay identical.

**Speed.** [Guessing] Targets, reported as measured, not gates: analysis of the 19,083-pipe network under 1 s, one full
design case under 60 s, all 12 cases under 5 minutes.

## 7. Verification

| Layer | What | When it runs |
|---|---|---|
| Unit | each function against hand values and the guideline (Table 11 full-bore 0.74–0.76 m/s, Peltier and Merrimack values) | every change |
| Golden, W18 | the engine against W18's own outputs of all 12 cases | every engine change |
| Referee | the engine against SewerGEMS exports, frozen as fixtures | every engine change; new fixtures made through the bridge when a case is added |
| API | FastAPI test client on every endpoint | every change |
| End to end | Playwright drives the real interface in Chromium: open, select, edit, run, compare, export, ask the assistant (stub) | every change to `api` or `web` |
| Assistant, live | one real question against the API, only when `ANTHROPIC_API_KEY` is set; prints its token cost | on request |

**Tolerances, fixed now:**

| Quantity | Phase 1 (steady sanitary) | Phases 2–4 (steady, GVF, pressure, storm) | Phase 5 (SWMM explicit) | Phase 5 (Implicit) |
|---|---|---|---|---|
| Pipe size | identical | identical | — | — |
| Flow | 0.1 % | 0.1 % | peak 1 %, volume 0.5 % | peak 2 %, volume 1 % [Guessing — to agree at phase 5] |
| Velocity | ±0.001 m/s on 5–95 %, verdict at 0.75 m/s identical | ±0.01 m/s | ±2 % at peak | ±5 % at peak |
| Invert, depth | ±1 mm | HGL ±5 mm | HGL ±10 mm | HGL ±50 mm |
| Stations, pump flow, head | same stations at the same manholes | pump flow 0.5 %, head ±0.05 m | as steady | as steady |

**Fixtures.** Phase-1 golden files are copied once from W18 (read only) and from `D:\VBOX\bridge\out\...`, gzipped, with
a manifest of source path, size and SHA-256, into `tests/fixtures/` (about 20 MB, in git). They carry the Ibri network,
whose manhole coordinates are already in the public repo through W18. Bentley sample models and their exports stay out
of git; tests that need them are skipped when absent.

## 8. Interface, phase 1

- **Map** of pipes, manholes and stations, coloured by any result (size, d/D, velocity at 2031, depth); click to select.
- **Property grid** from the element schema; editable fields write to the scenario's alternative, never the base.
- **Scenarios bar**: SC1–SC4 × 2051/2056/2061, plus any what-if; run analysis or the design chain; run time shown.
- **Results tables** with filter and sort; **profile** between two manholes (ground, invert, crown, water surface).
- **Export** of the active scenario to GPKG, DXF and CSV, plus the input set the SewerGEMS rebuild job reads.
- **Assistant pane** (below).
- Runs on `http://127.0.0.1:8765`, opened in a browser on this PC. Not reachable from the phone (no tunnel); that is
  deliberate.

## 9. Assistant

- Claude through the Messages API with the Python SDK's tool runner, the loop on this PC. Model `claude-opus-5-5`
  (effort `high`, adaptive thinking), switchable to `claude-sonnet-5-5` for speed; server-side fallback on refusal on.
- **Key:** read from `ANTHROPIC_API_KEY` only. The engineer sets it as a user environment variable; it is never written
  to a file, a log or a commit. Without a key the pane says so and the rest of the app works.
- **Tools** (strict schemas): `list_scenarios`, `run_scenario`, `query_elements` (filter by field), `get_element`,
  `explain_element` (every check on one element, pass or fail, with the rule and its guideline page from
  `_BRAIN/02_DESIGN_CRITERIA.md`), `compare_scenarios`, `make_whatif` (a new child scenario with stated changes, then run),
  `lookup_criterion`.
- **It never edits the base model or an existing scenario.** A what-if is a new scenario; making it permanent is the
  engineer's click.
- **Data:** tool results (element tables) go to Anthropic's API. Each answer shows its token use.

## 10. Stormwater test models (phases 4–5)

| Source | What | Download? |
|---|---|---|
| SewerGEMS installation in the VM | the sample models Bentley ships with the product | no — a bridge job lists them, opens each in SewerGEMS and exports through the API; nothing leaves the VM except numeric results, kept out of git |
| EPA SWMM 5 (public domain) | the example `.inp` models of SWMM 5 and its Applications Manual | yes, on the host: name, source and size stated first. SewerGEMS imports SWMM 5 `.inp`; if the API cannot run the import, the engineer imports each one in the SewerGEMS window once |
| FHWA HEC-22 (public) | the worked inlet and gutter examples | the PDF, on the host, for unit tests |
| Bentley online samples | only those open without a sign-in | stated one by one; if a sign-in is needed, the engineer downloads |

## 11. Phases and gates

| Phase | Delivers | Gate (all automated, `pytest -m gate_pN`) |
|---|---|---|
| **0** Foundations | W19 folder, fixtures with manifest, the W18 port with paths in a config | the port reproduces W18 SC1-2056 (named network, stations, quantities, summary, exports) exactly; W18's git status unchanged by the run |
| **1A** Sanitary engine as a library | hydraulics, peaking, network, flows, own transfers, sizing, analysis mode, the design step; the ported chain (split, naming, products) driven by the clean design step | the clean design step writes what W18's did (1e-9); own outfall flows equal SewerGEMS's within 0.1 % and leave the design unchanged; all 12 cases equal W18: identical sizes, depths ±1 mm, flows 0.1 %, same stations at the same manholes, same km under 0.75 m/s at 2031 and 2036, same deepest manhole; SC1-2056 against the SewerGEMS export within the phase-1 tolerances; timing reported |
| **1B** App and assistant | API, interface, assistant | the end-to-end suite passes: open Ibri, map shows 19,083 pipes, select a pipe, edit its size in a what-if, run, see the result change, profile, export GPKG that QGIS opens; assistant tools tested with a stub; live: asked why a named pipe misses 0.75 m/s, it answers with the right velocity and cites G203 p26 |
| **2** Referee harness, analysis breadth | bridge build-and-run jobs; friction options; GVF; structure losses; pressure network | a verification suite of bridge-built cases (tailwater, surcharge, each friction and loss method, a pump station with a curve, Ibri SC1-2056 on Manning) all within tolerance |
| **3** Full editing | the SewerGEMS-like editing set (section 4) | end to end: build a network from scratch in the interface, run, export, rebuild in SewerGEMS through the bridge, results within tolerance |
| **4** Stormwater, steady | catchments, rational, IDF, Tc, inlets, gutters, GVF-rational | Bentley's shipped samples and bridge-built storm cases within tolerance |
| **5** Dynamic | SWMM 5 engine, hydrology, ponds, storage, patterns | EPA SWMM examples solved in SewerGEMS (Explicit) and here within tolerance; Implicit within its stated tolerance |
| **6** Reports | tables, profile sheets, PDF | the report built from a scenario passes the clean gate where it is client-facing |

[Guessing] Size: phase 0 and 1 in this session; phases 2–5 are each one or more sessions. Each phase leaves a working
app, so stopping after any phase loses nothing.

## 12. Risks

1. **Bentley's numerics are not public.** GVF-convex, GVF-rational and Implicit may differ from textbook methods in
   details (convergence, structure losses). Black-box experiments find the rule; if a tolerance still fails, the case
   is reported as failing, not exempted.
2. **Bridge throughput.** A SewerGEMS run takes minutes to 44 minutes. Verification cases are kept small (tens to
   hundreds of elements) except the Ibri regression, and each result is frozen as a fixture once.
3. **The W18 chain may depend on its starting state** (each pass starts from the previous pass's cuts). If a run from
   scratch does not converge to W18's stations, the fixture carries W18's converged cuts as the start, and the finding
   goes to the engineer.
4. **SWMM import through the API may not exist** in 10.4; then the engineer imports each sample once in the GUI.
5. **API cost and data.** Every assistant call is billed per token and sends element data to Anthropic.

## 13. Out of scope

Water distribution (WaterGEMS), water quality, cost optimisation, cloud hosting, multi-user editing, phone access.
