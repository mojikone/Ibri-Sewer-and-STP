# Catch basins, inlets and gutters: what SewerGEMS holds and how the app computes them (2026-11-24, v7)

## Sources

1. **SewerGEMS 10.4's own field catalogue** (bridge job 113, `D:\VBOX\bridge\out\w19\catalogue\input_fields.tsv`): the
   input fields of every element type by alternative.
2. **SewerGEMS's option lists**, read on 2026-11-24 as public enum names and values from the API assemblies' metadata
   (`D:\VBOX\bridge\refs`, reflection-only load, nothing executed, nothing decompiled; see `CLEAN_ROOM.md`).
3. **FHWA HEC-22, Urban Drainage Design Manual, 3rd edition** (FHWA-NHI-10-009, 2009, errata 2013), chapter 4. Equation
   numbers below are the manual's.
4. **EPA SWMM 5.2.4, `src/solver/inlet.c`** (public domain, the solver the app's storm run uses through swmm-toolkit
   0.17): the cubic fits of HEC-22 Chart 5B (splash-over velocity) and the grate opening ratios of Chart 9B.

## SewerGEMS's catch basin (element type 2) fields

| Group | Fields |
|---|---|
| Structure | Structure Type (Circular / Box), Diameter, Length and Width (box), Elevation (Ground), Set Rim to Ground?, Elevation (Rim), Elevation (Invert), Sump Depth (design) |
| Inlet | Inlet Type, Inlet Location (On Grade / In Sag), Inlet (catalogue), Capture Efficiency (percent capture), Flow (Maximum in) (maximum capacity), Inflow-Capture Curve (rating curve), Grate Length, Curb Opening Length, Slot Length, Clogging Factor, Longitudinal Slope (Inlet), Manning's n (Inlet) |
| Gutter | Gutter Type (User Defined / Catalog), Gutter Shape, Road Cross Slope, Gutter Cross Slope, Gutter Width, Depressed Gutter?, Curb Cross Slope (V-shaped), Left and Right Side Slope, Bottom Width (Ditch), Height and Width (parabolic), Irregular section, Maximum Gutter Depth |
| Surface storage | Surface Storage Type, Area (Constant Surface), Surface Depth-Area Curve |
| Flows | Flow (Additional Carryover), Flow (Known), External CA, External Tc, Flow (Additional Subsurface), Sanitary Loads, wet inflows, hydrograph loads |
| Headloss | Headloss Method, Standard / Upstream / Downstream coefficients, Absolute Headloss, HEC-22 benching, AASHTO shaping, Flow-Headloss curve |
| Design | Design Inlet Opening?, Maximum Spread, Maximum Gutter Depth (Design), Minimum Efficiency on Grade, Freeboard (Required), cover limits, drop structures |

Option lists (enum names as SewerGEMS declares them):

- **Inlet Type:** MaximumCapacity 0, HydrologicRatingCurve 1, FullCapture 2, HEC22CatalogInlet 3, PercentCapture 4.
- **Inlet Location:** OnGrade 0, InSag 1.
- **Catalogue inlet type:** Combination 0, Curb 1, Ditch 2, Grate 3, Slot 4, Generic (flow vs captured, on grade) 5,
  DepthCapturedFlow (in sag) 6, KerbUK 100, GratingUK 101.
- **Grate type:** P-50 mm, P-30 mm, Curved Vane, 45° Tilt Bar, 30° Tilt Bar, P-50 x 100 mm, Reticuline.
- **Curb throat:** Horizontal, Inclined, Vertical.
- **Gutter shape:** Conventional 0, Trapezoidal 1, Irregular 2, Parabolic 3, V-Shaped 4.
- **Gutter link type:** User Defined, Catalog, Derived from Start Inlet, Derived from Stop Inlet, Use Gutter Sections.
- **Surface storage:** Default storage equation, Depth-area, None, Constant area.
- **Structure type:** Circular, Box (Transition node: no structure).
- **Headloss method:** Absolute, HEC-22 Energy (2nd ed.), Generic, Standard, AASHTO, Flow-Headloss Curve, Wallingford,
  HEC-22 Energy (3rd ed.), HEC-22 Momentum.

## Equations (SI)

| What | Equation | HEC-22 |
|---|---|---|
| Gutter flow, uniform cross slope | Q = (0.376/n) Sx^1.67 SL^0.5 T^2.67 | Eq. 4-2, p 4-9 |
| Frontal-flow ratio | Eo = 1 / {1 + (Sw/Sx) / [(1 + (Sw/Sx)/(T/W - 1))^2.67 - 1]}; uniform: 1 - (1 - W/T)^2.67 | Eq. 4-4, 4-16 |
| Any gutter section | the app integrates Izzard's strip form Q = (SL^0.5 / n) ∫ y(x)^(5/3) dx across the section, which is Eq. 4-2 for a triangle (8/3 · 0.375 = 0.376) and handles depressed, V-shaped, parabolic and irregular gutters alike | App. B |
| Grate on grade | Rf = 1 - 0.295 (V - Vo), Rf ≤ 1; Rs = 1 / (1 + 0.0828 V^1.8 / (Sx L^2.3)); E = Rf Eo + Rs (1 - Eo); E'o = Eo Aw'/Aw for a grate narrower than W | Eq. 4-18 to 4-21, p 4-42/43 |
| Splash-over velocity | Vo = α + β L - γ L² + η L³ (L ft, Vo ft/s), per grate (SWMM 5.2 inlet.c, fitted to Chart 5B): P-50 2.22 4.03 0.65 0.06; P-50x100 0.74 2.44 0.27 0.02; P-30 1.76 3.12 0.45 0.03; Curved vane 0.30 4.85 1.31 0.15; 45° tilt bar 0.99 2.64 0.36 0.03; 30° tilt bar 0.51 2.34 0.20 0.01; Reticuline 0.28 2.28 0.18 0.01 | Chart 5 |
| Curb opening on grade | LT = 0.817 Q^0.42 SL^0.3 (1/(n Se))^0.6; E = 1 - (1 - L/LT)^1.8; Se = Sx + (a/W) Eo | Eq. 4-22, 4-23, 4-24, p 4-46 |
| Slotted on grade | as a curb opening (FHWA tests, slots ≥ 45 mm) | p 4-51 |
| Combination on grade | grate alone; with a curb opening upstream of the grate (sweeper): that length first, the grate on what passes it | p 4-52 |
| Grate in sag | weir Qi = 1.66 P d^1.5 (P = L + 2W against a curb), orifice Qi = 0.67 Ag (2 g d)^0.5, Ag = L W × opening ratio × (1 - clogging); orifice from d > 1.79 Ag/P (where the two meet) | Eq. 4-26, 4-27, p 4-57 |
| Opening ratios | P-50 0.90, P-50x100 0.80, P-30 0.60, curved vane 0.35, 45° tilt bar 0.17 (SWMM's assumption: HEC-22 gives none), 30° tilt bar 0.34, reticuline 0.80 | Chart 9 |
| Curb opening in sag | depressed weir Qi = 1.25 (L + 1.8 W) d^1.5 for d ≤ h + a; undepressed (or L > 3.6 m) 1.60 L d^1.5 for d ≤ h; orifice Qi = 0.67 h L (2 g do)^0.5 above 1.4 h (do = d - h/2 horizontal throat, d - 0.7071 h/2 inclined, d vertical); linear between | Eq. 4-28 to 4-31, p 4-59/60 |
| Slotted in sag | weir Qi = 1.4 L d^1.5, orifice Qi = 0.8 L W (2 g d)^0.5, switching where they meet (d = 2.587 W) | Eq. 4-32, 4-33, p 4-63 |
| Combination in sag | weir: the grate alone; orifice: grate plus curb opening | Eq. 4-35, p 4-65 |

Checks the code must pass (HEC-22's own worked examples): Example 4-8, gutter T 3 m, SL 0.04, Sx 0.025, n 0.016:
Q 0.19 m3/s, Eo 0.45, V 1.66 m/s; P-50 0.6 × 0.6 m Rf 1.0, Rs 0.036, Qi 0.091 m3/s; reticuline 0.6 × 0.6 m Rf 0.9,
Qi 0.082 m3/s. Example 4-9 (curb opening): Q 0.05, SL 0.01, Sx 0.02, n 0.016: LT 7.29 m, a 3 m opening E 0.61,
Qi 0.031 m3/s. Chart 5A's example: reticuline 0.91 m at 2.4 m/s, Rf 0.8.

The curved-vane fit drifts above about 0.9 m (2.27 m/s at 1.0 m where Chart 5A reads about 2.43): the app uses
SWMM's fit for every grate so that the steady run and the storm run agree.
