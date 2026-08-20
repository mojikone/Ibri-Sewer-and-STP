"""sewnet.criteria — the ONLY place numeric design values live (CLAUDE.md: no invented metrics).

Every value cites its source: G203-p## = PAM-GUD-203, G1-p## = PAM-GUD-201,
02 = _BRAIN/02_DESIGN_CRITERIA.md, A9 = W3/analysis/A9_criteria_audit.md.

The values sit on a FROZEN dataclass, so a sensitivity run (say tau = 2 Pa, or a
different branch offset) is `replace(DEFAULT, TAU_PA=2.0)` — a new object handed to the
pipeline, never an edit to this file. `DEFAULT` is the design basis; modules do
`from .criteria import DEFAULT as C` and read `C.MIN_COVER_CROWN` exactly as before.

Values whose source is pending or assumed are listed in ASSUMPTIONS and must be
reported as such in every deliverable.
"""

import math
from dataclasses import dataclass, field, replace  # noqa: F401  (replace re-exported)
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class Criteria:
    # ---------------------------------------------------------------- hydraulics
    G: float = 9.81
    KS: float = 0.0015        # m — Colebrook-White roughness, all sizes (G203-p24, p28)
    NU: float = 1.141e-6      # m2/s — kinematic viscosity @15 C (G203-p25)

    V_SELF_CLEANSING: float = 0.75    # m/s at peak flow (G203-p26)
    V_PREFERRED: float = 0.90         # m/s preferred (G203-p26)
    V_MAX: float = 3.0                # m/s at design depth (G203-p27, p29)

    DOD_MAX_SMALL: float = 0.65       # d/D at peak, D <= 350 (G203-p27 Tab 10)
    DOD_MAX_LARGE: float = 0.50       # d/D at peak, D > 350
    DOD_DN_THRESHOLD: int = 350

    # G203-p29 Tab 11 — minimum gradients (m/m), CW @ 0.75 m/s, ks 1.5 mm.
    # The hydra gate reproduces these from the CW equation (+/-5%) before any design runs.
    TABLE11: Dict[int, float] = field(default_factory=lambda: {
        200: 0.00500, 250: 0.00375, 315: 0.00270, 400: 0.00205, 500: 0.00155,
        600: 0.00125, 700: 0.00100, 800: 0.00085, 900: 0.00075})
    TABLE11_FLOOR: float = 0.00075    # ">= DN900: 0.75 mm/m" (G203-p29)

    DN_SERIES: List[int] = field(default_factory=lambda:
                                 [200, 250, 315, 400, 500, 600, 700, 800, 900, 1000, 1200])
    DN_MIN_MAIN: int = 200            # OD200 minimum main sewer (G203-p22 Tab 6)

    # Tractive-force minimum gradient (G203-p27 4.2.2.1, A9-corrected):
    # Smin = K * tau^1.23 * Q^-0.461, Q in m3/s
    TRACTIVE_K: float = 2.33e-4
    TRACTIVE_QMIN: float = 0.0015     # m3/s — Mara's 1.5 L/s minimum design flow; at the
                                      # floor tractive ~= Table 11 DN200, the methods meet

    # ---------------------------------------------------------------- chambers
    MH_SPLIT_LEN: float = 100.0       # split length satisfying every Tab-12 class
    MH_ROUND_STEP: float = 10.0       # round spacing to this step (user rule 2026-08-18);
    MH_ROUND_FALLBACK: float = 5.0    # finer step when 10 m leaves an awkward remainder

    # One physical outlet per structure (user rule; SWNETWROK FANOUT_GAP_M = 10 m)
    FANOUT_OFFSET_M: float = 10.0
    MH_MIN_CLEAR_M: float = 3.0       # distinct chambers never closer than this
    MH_SNAP_M: float = 3.0            # closer than the clearance => ONE structure, merge

    DROP_TRIGGER: float = 0.60        # m invert difference -> backdrop (G203-p30)
    BACKDROP_MAX: float = 2.0         # m; beyond -> vortex drop shaft (G203-p30, A9)

    MIN_COVER_CROWN: float = 1.3      # m to crown (G203-p33 4.6.3)
    MAX_DEPTH: float = 12.0           # m cover; beyond -> pumping (G203-p33) -> SLS
    FALL_TOLERANCE: float = 0.040     # m — 2 x 20 mm line/level tolerance (G203-p29, A9)

    SLS_MIN_PLOTS: int = 50           # absorb smaller pockets (CLAUDE.md rule 9)
    SLS_CASCADE_M: float = 1500.0

    # ---------------------------------------------------------------- road treatment
    ROAD_DEDUP_M: float = 0.20        # drop points closer together than this
    ROAD_SIMPLIFY_M: float = 0.50     # smoothing tolerance (removes survey wobble)
    ROAD_COLLINEAR_DEG: float = 10.0  # a break this straight is dissolved away
    GATE_SEARCH_M: float = 45.0       # how far off a street a house gate may sit
    INLET_MIN_DEG: float = 75.0       # smallest angle an inlet may make with the flow
    ROAD_BEND_DEG: float = 30.0       # a turn sharper than this needs a chamber
    ROAD_CHORD_DEV_M: float = 0.50    # how far the pipe may sit off the road line on a curve
    BEND_MAX_CHAMBERS: int = 3        # never more than 3 chambers on one bend (user 2026-08-19)
    BEND_CORNER_CLEAR_M: float = 2.0  # a corner chamber must be this clear of any plot boundary
    ROUNDABOUT_PERIM_M: float = 150.0 # ring shorter than this may be a roundabout
    ROUNDABOUT_R_MAX: float = 30.0    # equivalent radius cap — roundabouts are small.
                                      # (A circularity test was tried and REMOVED: a square
                                      #  scores 0.785 and a triangle 0.605, so every city
                                      #  block passed it — review RT-2. A ring is now a
                                      #  roundabout only if no plot lies inside it, every
                                      #  node has an approach arm, and the arcs are curved.)
    STUB_MIN_M: float = 8.0           # dangling stub shorter than this, no plots -> drop
    ORPHAN_LINK_M: float = 80.0       # dead-end serving no plot -> drop, repeatedly
    DUAL_CROSS_MAX_M: float = 70.0    # longest perpendicular crossing of a dual carriageway
    DUAL_CROSS_SQUARE_DEG: float = 35.0   # how far off square a crossing may be

    # traffic links: turning fillets, slip roads, diagonal links between two carriageways.
    # These exist so cars can turn; sewage joins at a point, so they are dropped (B9).
    LINK_MAX_LEN_M: float = 120.0     # a link is short ...
    LINK_MIN_TURN_DEG: float = 45.0   # ... or strongly curved
    LINK_DETOUR_RATIO: float = 3.0    # only drop it if the way round is no more than 3x longer

    # flood hazard (50-year grid). Classes 4/5/6 = wadi, no pipes or chambers; 1/2/3 = safe;
    # nodata = dry (user 2026-08-19)
    HAZARD_WADI_CLASSES: tuple = (4, 5, 6)

    # ---------------------------------------------------------------- tertiary
    PCS_MIN_SLOPE: float = 0.03       # property connection 3-10 % (G203-p18 Tab 5)
    PCS_MAX_SLOPE: float = 0.10
    PCS_MAX_LEN: float = 50.0         # m (G203-p18 Tab 4 note, A9)
    PCS_MIN_COVER: float = 0.60       # m (G203-p19 3.5)
    RIDER_MIN_SLOPE: float = 0.01     # rider/lateral 1-10 % (G203-p18 Tab 5)
    LATERAL_MAX_LEN: float = 45.0     # m (G203-p22 Tab 6)
    MAX_HCC_PER_RIDER: int = 3        # (G203-p19 3.4, A9)
    DN_TERTIARY: int = 160            # OD160 minimum (G203-p22 Tab 6)

    # ---------------------------------------------------------------- loads
    # counted properties per plot now come from electricity accounts, so PROPS_PER_PLOT is
    # only the fallback where a plot has no account on it (B10)
    ACCOUNT_TARIFF_DOMESTIC: tuple = ("Primary Account Tariff",
                                      "Primary Account Tariff (with National Subsidy)",
                                      "Additional Account Tariff")
    ACCOUNT_TARIFF_NONDOM: tuple = ("Commercial", "Government", "Fisheries", "Industrial",
                                    "Tourism", "MOD", "CRT Seasonal", "CRT Time of Use",
                                    "CRT Fixed Rate")
    ACCOUNT_TARIFF_AGRI: tuple = ("Agricultural",)

    # Tab 12 drivers we have to derive because nobody supplies them (B11). All assumptions.
    FLOOR_RATIO_DEFAULT: float = 0.40   # share of the plot covered by building
    STOREYS_DEFAULT: float = 1.5
    AREA_PER_EMPLOYEE_M2: float = 15.0
    AREA_PER_PUPIL_M2: float = 4.0
    AREA_PER_BED_M2: float = 30.0
    RATE_COMMERCIAL_L_M2: float = 12.2  # G1-p61 Tab 12 shopping
    RATE_MOSQUE_L_M2: float = 185.0     # G1-p61 Tab 12
    RATE_OFFICE_L_EMP: float = 93.0     # G1-p61 Tab 12
    RATE_SCHOOL_L_PUPIL: float = 130.0  # G1-p61 Tab 12
    RATE_HOSPITAL_L_BED: float = 650.0  # G1-p61 Tab 12

    LPCD_WATER: float = 164.0         # l/c/d domestic water (G1-p59-60 Tab 11)
    RETURN_DOM: float = 0.85          # (G1-p70-71 Tab 19)
    WWG_LCD: float = 171.3            # l/c/d area-average WW incl. Tier-A ND+Gov uplift
    INFILT_L_D_KM: float = 720.0      # L/d per km, new networks (G1-p72-73), unpeaked
    PF_HOLD_PROPERTIES: int = 100     # below this G1 prescribes no formula -> hold
    PF_REPORT_ABOVE: float = 5.0      # advisory only — never truncate (G1-p72 NOTE, A9)

    MANNING_N_EXPORT: float = 0.013   # ks-equivalent for the SewerGEMS model (review HYD-3)

    # ---------------------------------------------------------------- assumptions
    TAU_PA: float = 1.0               # GAP-9 — no numeric design value in GUD-203
    OCCUPANCY: float = 5.0            # people per property — user decision 2026-08-19
    PROPS_PER_PLOT: float = 1.0       # GAP-5
    PLOT_OUTLET_DEPTH: float = 0.60   # method choice
    CONN_CHECK_SLOPE: float = 0.02    # blended PCS/rider fall for connectability
    WALL_ALLOW: float = 0.05          # pipe wall + bedding below crown cover
    CROSS_STREET_FRONTAGE: float = 40.0

    # ---------------------------------------------------------------- derived
    @property
    def PLOT_QADF_M3D(self) -> float:
        """Per-plot saturation average dry-weather flow (PROJECT-STATE 2)."""
        return self.OCCUPANCY * self.PROPS_PER_PLOT * self.WWG_LCD / 1000.0

    @property
    def PLOT_QADF_LS(self) -> float:
        return self.PLOT_QADF_M3D * 1000.0 / 86400.0

    # ---------------------------------------------------------------- helpers
    def mh_max_spacing(self, dn: int) -> float:
        """Maximum chamber spacing by diameter (G203-p30 Tab 12)."""
        if dn <= 315:
            return 100.0
        if dn <= 900:
            return 120.0
        if dn <= 1400:
            return 150.0
        return 200.0

    def internal_diameter(self, dn: int) -> float:
        """True internal bore (review HYD-2): plastic mains are OD-designated
        (G203-p22 Tab 6 'OD 200 mm'); PVC-U SN8 = SDR34 -> ID = OD*(1-2/34).
        GRP nominal size IS the internal diameter."""
        if dn <= 315:
            return dn / 1000.0 * (1.0 - 2.0 / 34.0)
        return dn / 1000.0

    def material(self, dn: int) -> str:
        """PVC-U through the OD series to 315 (G203-p23 Tab 7), GRP above (p22 Tab 6)."""
        return "PVC-U" if dn <= 315 else "GRP"

    def outside_diameter(self, dn: int) -> float:
        """Crown-to-invert height is the pipe's OUTSIDE diameter, not its bore.
        PVC-U is OD-designated so OD = DN. GRP is ID-designated, so its true OD is
        nominal + 2 x wall; the wall is unknown at concept, so nominal is used and the
        gap (a few cm) is tagged. Geometry uses this; hydraulics use internal_diameter()."""
        return dn / 1000.0

    def invert_depth_min(self, dn: int) -> float:
        """Minimum invert depth below ground: crown cover + outside diameter + bedding."""
        return self.MIN_COVER_CROWN + self.outside_diameter(dn) + self.WALL_ALLOW

    def pf_merrimack(self, qadf_mld: float) -> float:
        """Qpdf = 2.65 * Qadf^0.879, both Ml/d (G1-p71, mandatory >100 properties)."""
        if qadf_mld <= 0:
            return 1.0
        return 2.65 * qadf_mld ** 0.879 / qadf_mld

    def pf_peltier(self, qm_ls: float) -> float:
        """Peltier IMP2024: 1.5 + 1/sqrt(Qm), Qm in L/s (G1-p72) — comparison column."""
        if qm_ls <= 0:
            return 1.0
        return 1.5 + 1.0 / math.sqrt(qm_ls)

    # ---------------------------------------------------------------- register
    @property
    def ASSUMPTIONS(self) -> Dict[str, Tuple]:
        return {
            "TAU_PA": (self.TAU_PA, "design tractive stress Pa — GUD-203 gives NO numeric "
                       "value (GAP-9); Mara et al. literature basis; confirm with NWS"),
            "TRACTIVE_QMIN": (self.TRACTIVE_QMIN, "Mara simplified-sewerage minimum design "
                              "flow; unfloored the formula demands unbounded slopes as Q->0"),
            "PVC_SDR": ("SDR34/SN8", "PVC-U wall class behind internal_diameter(); actual "
                        "class per PAM-SPC-207 pending"),
            "OCCUPANCY": (self.OCCUPANCY, "people per property — set to 5 by the user 2026-08-19 (was a 6.0 fallback)"),
            "PROPS_PER_PLOT": (self.PROPS_PER_PLOT, "properties per plot — now COUNTED from electricity accounts; this value is only the fallback for a plot with no account"),
            "PLOT_OUTLET_DEPTH": (self.PLOT_OUTLET_DEPTH, "house drain leaves the plot this "
                                  "deep below plot ground — method choice"),
            "CONN_CHECK_SLOPE": (self.CONN_CHECK_SLOPE, "blended PCS/rider fall for the "
                                 "plot-connectability check — method choice"),
            "WALL_ALLOW": (self.WALL_ALLOW, "pipe wall + bedding below crown cover"),
            "HEAD_AT_GATE": (self.GATE_SEARCH_M,
                             "A run starts at the first house gate on that street, not at a "
                             "fixed offset from the junction (user 2026-08-20). The gate is "
                             "taken as the plot centroid dropped square onto the street; "
                             "FANOUT_OFFSET_M is only the fallback when no plot faces it."),
            "INLET_ANGLE": (self.INLET_MIN_DEG,
                            "G203-p30 says no inlet shall meet the flow at less than 90 deg. "
                            "The user set 75 deg on 2026-08-20 to stop the design inserting "
                            "bend chambers purely to satisfy the rule, which added roughly 200 "
                            "chambers for no construction benefit. STATED DEVIATION from the "
                            "guideline: anything sharper than 75 deg is flagged for a look, "
                            "never fixed by adding a chamber."),
            "FANOUT_OFFSET": (self.FANOUT_OFFSET_M, "a branch leaving a chamber that already "
                              "has an outlet starts at the next house connection, or 10 m "
                              "away — user rule 2026-08-18, SWNETWROK FANOUT_GAP_M; layout "
                              "convention, not a PAM-GUD value"),
            "MH_MIN_CLEAR": (self.MH_MIN_CLEAR_M, "no minimum chamber spacing exists in "
                             "GUD-201/202/203 (verified in the source PDFs); 3 m is a "
                             "physical-size convention"),
            "MH_ROUND_STEP": (self.MH_ROUND_STEP, "round spacing to 10 m (5 m fallback) "
                              "rather than exact equal division — user rule 2026-08-18"),
            "ROAD_TREATMENT": ((self.ROAD_COLLINEAR_DEG, self.ROAD_BEND_DEG),
                               "collinear-dissolve and bend-split thresholds for turning raw "
                               "centrelines into sewer corridors — method choices, tune on "
                               "review. ROAD_CHORD_DEV_M is declared but NOT yet enforced "
                               "(chord-deviation splitting is a W5 item)"),
            "MH_SIZES": ("DN1000 to 3 m / DN1200 to 6 m / DN1500 deeper", "chamber internal "
                         "sizes vs depth — GUD-203 says only 'sufficient size'; no table "
                         "exists (verified); no hydraulic effect at concept"),
            "RIDER_DISCHARGE": ("nearest chamber", "rider discharge point — absent from 02"),
            "KERB_RULES_GRAVITY": ("applied", "in-carriageway >=1 m from kerb / chamber "
                                   ">=0.5 m from kerb is a force-main clause (G203-p51) "
                                   "applied to gravity as inference (A9)"),
            "PF_COMPARISON_HOLD": ("100-property flow", "Peltier comparison held like "
                                   "Merrimack; no design decision rests on it"),
            "CROSS_STREET_FRONTAGE": (self.CROSS_STREET_FRONTAGE, "an off-tree street gets a "
                                      "sewer when a loaded unit lies within this distance"),
            "TIER_B_DRIVERS": ((self.FLOOR_RATIO_DEFAULT, self.STOREYS_DEFAULT),
                               "floor area, staff and pupil counts are DERIVED (plot area x cover "
                               "x storeys, then a density figure) because nobody supplies them. "
                               "Plot cover is known for only 17% of plots and storeys for 18%, so "
                               "defaults carry the rest — replace when the land-use data arrives"),
            "BEND_CORNER": ((self.BEND_MAX_CHAMBERS, self.BEND_CORNER_CLEAR_M),
                            "at a tight corner one chamber sits at the corner point if it is 2 m "
                            "clear of every plot; otherwise the curve is followed with 2 chambers, "
                            "3 only on a wide long bend"),
            "ORPHAN_LINKS": (self.ORPHAN_LINK_M,
                             "After dual carriageways and roundabouts come out, their slip "
                             "roads and approach arms are left dangling. Anything that dead-"
                             "ends and serves no plot is removed, and the removal repeats "
                             "because taking one away exposes the next (user 2026-08-20)."),
            "DUAL_CROSSING": ((self.DUAL_CROSS_MAX_M, self.DUAL_CROSS_SQUARE_DEG),
                              "No pipe runs ALONG a dual carriageway, but a short pipe may "
                              "cross one at right angles. Joining the two sides is allowed "
                              "where it gives the gravity network a better route and saves a "
                              "pumping station (user 2026-08-20)."),
            "TRAFFIC_LINKS": ((self.LINK_MAX_LEN_M, self.LINK_MIN_TURN_DEG,
                               self.LINK_DETOUR_RATIO),
                              "turning fillets and slip roads are dropped when they serve no plot, "
                              "join two attached ends, and the way round is under 3x longer"),
        }


DEFAULT = Criteria()          # the design basis
