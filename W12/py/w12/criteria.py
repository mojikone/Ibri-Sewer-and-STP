"""w12.criteria - THE ONLY PLACE A NUMBER LIVES. W12 owns this file; it imports nothing.

W12 INHERITS W11b and revises it (user rule, 2026-09-06): a new W# copies the previous folder's code and edits it. Earlier folders are read as data and as lessons, never re-derived from scratch. Superseded folders stay untouched as the record.
`W8/py/sewnet`, `W10/py` or `W11a/py`. Where a value existed there it was re-read from the
source PDF and re-typed here with the page it came from, not copied on trust.

CITATIONS
    G203-p##   PAM-GUD-203 Wastewater Design Guidelines v1.0  (Data/, 201 pp)
    G201-p##   PAM-GUD-201 General Design Guidelines v1.0     (Data/, 152 pp)
    G202-p##   PAM-GUD-202 Water and TSE Design Guidelines v1.0 (_STANDARDS/ + Data/)
    ASSUMPTION every value with no page behind it, listed in ASSUMPTIONS and reported

Everything in the class below either carries a page reference that was READ OUT OF THE PDF
on 2026-09-03 during this session, or appears in ASSUMPTIONS. Two citation errors were
caught the day before this file was written and both are corrected here:
  * G201-p86 is a VALVE-CHAMBER clause on a FORCE MAIN. It is not authority for anything
    about a gravity manhole. The wadi prohibition on gravity pipes AND chambers is
    G203-p30 sec 4.4.1 and G203-p33 sec 4.6.2, both re-read.
  * G203-p52 sec 8.2.4's cover figures sit in the FORCE MAIN chapter. Their preamble reads
    "As for gravitational sewer, the minimum cover should be" and then gives 1.3 m plain /
    0.5 m protected / 1.5 m at a wadi crossing. The 1.3 and 0.5 match the gravity clause at
    p33 exactly; the 1.5 m at a wadi crossing appears NOWHERE in the gravity chapter. We
    adopt it for gravity crossings as a PROJECT DECISION, and the preamble is the reason it
    is a defensible one - but it is still our decision, not a gravity-chapter quotation.

WHAT WAS CARRIED FROM W8/W11a, AND WHAT CHANGED
    carried  the shape of the object (frozen dataclass + DEFAULT, so a sensitivity run is
             `replace(DEFAULT, TAU_PA=2.0)` and never an edit to this file), Table 11, the
             tractive equation, the DN series extended past DN1200, the 0.05 % gradient
             step, the chamber-spacing table, the tertiary slopes, the load basis.
    changed  (1) ONE wall/bedding allowance. W11a carried WALL_ALLOW = 0.05 in criteria and
                 a second AUDITOR_OD_ALLOW_M in contract; when they were 0.05 and 0.10 the
                 auditor demanded 50 mm more cover than the design laid, at EVERY diameter,
                 and a BLOCKING check failed on EVERY reach. Here there is exactly one
                 constant, WALL_ALLOW, and `invert_depth_min()` and `cover()` are the only
                 two functions that touch it. contract.py imports them; it does not
                 re-implement them.
             (2) d/D is a FUNCTION of diameter, `dod_limit(dn)`, not a pair of constants a
                 caller might use the wrong one of. Re-read at G203-p27 Table 10.
             (3) `material()` now takes TIER as well as DN. G203-p22 Table 6 is by
                 APPLICATION and G203-p23 Table 7 is by PRODUCT, and they disagree: PVC-U
                 is a permitted product to OD315 but a permitted MAIN SEWER only to 250 mm.
                 A dn-only function cannot express that and W8's returned "PVC-U" for a
                 DN315 main, which Table 6 does not allow.
             (4) INLET_MIN_DEG is 90.0, the guideline value (G203-p30, verbatim below).
                 W8 relaxed it to 85 deg to stop the layout inserting bend chambers. That
                 relaxation is NOT carried: G203 says "shall", the philosophy makes it H10,
                 and the physical resolution for a sharp inlet is a purpose-made swept
                 channel, which is a priced item, not a softer number.
             (5) NEW - the terrain-first block. W12 derives flow direction from the ground
                 and lets the pipes follow it, so the against-the-grade quantities the
                 philosophy sec 4 demands are first-class here: they have names, they have
                 a benchmark measured off the built network, and BENCHMARKS says loudly
                 that a benchmark is a calibration reference and never a limit.
             (6) TAU_PA carries a banner. The engineer settled tau = 1.0 Pa on 2026-09-03
                 and asked for it flagged on every output. `tau_banner()` is that flag and
                 `tau_sensitivity()` is the number behind it.

FIXED 2026-09-03 AFTER A JUDGE'S REVIEW - four defects, each measured before and after
    (7) GRADIENT_BUILT_MM_M = 4.98 IS RETRACTED. It was a MEAN in this file's note and a
        MEDIAN in the document it came from; it was computed over SEWERLINE.kmz, which is
        111.6 km of built pipe mixed with 77.0 km of unapproved concept; and it is not
        reproducible from any subset of the real dataset. Re-measured here from
        SEWERLINE_IBRI.shp with STATUS filtered: MEDIAN 6.00, MEAN 8.89, LENGTH-WEIGHTED
        8.69 mm/m over 2,142 levelled reaches / 63.20 km of the 95.45 km built. The claim
        attached to it - "against W8's 5.00, the hydraulics calibrate" - did not hold
        either: like for like the design median is 17 % FLATTER than the built one. The
        withdrawal, with the arithmetic, is in the new RETRACTED register.
    (8) NEW REGISTER: `RETRACTED`. Numbers this file used to state that do not hold. A
        withdrawal that lives only in a session transcript is a figure that comes back.
    (9) TWO CONSTANTS FOR ONE QUANTITY, removed. `MH_MIN_CLEAR_M` was a second field
        holding 3.0 beside `MH_SNAP_M` holding 3.0, for one physical clearance; it is now a
        read-only property. The flood-grid thresholds - which classes are washout ground,
        which return period, whether no-data is dry - were declared BOTH here and in
        `hazard.py`, with the washout threshold answered differently in each (4+ here, 5+
        there: a 4.25 km gap on the client's Main Pipe). This file is now the only
        declaration and `hazard.py` reads it. `TRACTIVE_K_M3S`/`TRACTIVE_K_LS` stay as a
        pair because G203-p27 prints both; they are 2.27 % apart, that is registered in
        CONFLICTS, and hydra.py's self-test asserts it.

WHAT THIS FILE IS NOT. It holds no paths, no layer names, no field names and no geometry
tolerances. Those are `contract.py`. It holds no equations either - `hydra.py` owns those
and reads its constants from here.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field, replace  # noqa: F401  (replace re-exported)
from typing import Dict, List, Optional, Tuple

CRITERIA_VERSION = "W12-criteria-1.0"

# Sources, spelled out once so a citation string in this file can be resolved by a reader
# who has never seen the project.
SOURCES: Dict[str, str] = {
    "G203": "PAM-GUD-203 Wastewater Design Guidelines v1.0, Rev 01, 201 pp "
            "(Data/PAM-GUD-203 - Wastewater Design Guidelines v1.0.pdf)",
    "G201": "PAM-GUD-201 General Design Guidelines v1.0, Rev 01, 152 pp "
            "(Data/PAM-GUD-201 - General Design Guidelines v1.0.pdf)",
    "G202": "PAM-GUD-202 Water and TSE Design Guidelines v1.0, Rev 01, 177 pp "
            "(_STANDARDS/ and Data/)",
    "ASSUMPTION": "no guideline value exists; a project decision, listed in "
                  "Criteria.ASSUMPTIONS and reported on every deliverable",
    "MEASURED": "measured from project data (the as-built network, the terrain, the "
                "cadastre); a calibration reference, never a limit",
}


class CriteriaError(Exception):
    """Raised when a criteria helper is asked for something the guideline does not cover -
    an unknown tier, a diameter off the series. Never returns a default: a silent default
    is how a DN315 main got a material Table 6 does not permit."""


@dataclass(frozen=True)
class Criteria:
    """Frozen on purpose. A sensitivity run is a NEW OBJECT, never an edit:

        from w12.criteria import DEFAULT, replace
        tau2 = replace(DEFAULT, TAU_PA=2.0)          # the NWS downside case
        s = hydra.smin_for(200, q, crit=tau2)

    Every stage takes `crit=DEFAULT` as a keyword so the whole pipeline can be re-run at a
    different tau without a single line changing.
    """

    # =========================================================================== hydraulics
    G: float = 9.81                   # m/s2
    KS: float = 0.0015                # m. G203-p24 sec 4.2.1 and p28 sec 4.2.4, both:
                                      # "using a ks value of 1.5 mm for all pipe sizes and
                                      # materials". Not a choice - stated twice.
    NU: float = 1.141e-6              # m2/s. G203-p25 Table 9 at 15 C. The clause reads
                                      # "For basic design purposes, the conservative value
                                      # of 15oC should be used" (25 C -> 0.897, 35 -> 0.727).

    V_SELF_CLEANSING: float = 0.75    # m/s. G203-p26: "the minimum velocity in the pipe
                                      # shall be above 0.75 m/s at peak flow"
    V_PREFERRED: float = 0.90         # m/s. G203-p26: "with preferred velocity at 0.90m/s"
    V_MAX: float = 3.0                # m/s. G203-p27 sec 4.2.2.2: "the maximum velocity
                                      # shall not exceed 3 m/s at the design depth of flow";
                                      # repeated p29 sec 4.3.2.

    # G203-p27 Table 10 "Recommended Depth of Flow at peak flow", read out of the PDF
    # 2026-09-03, verbatim two rows:
    #     Pipe Diameter up to 350 mm    0.65
    #     Pipe Diameter > 350 mm        0.50
    # The threshold is INCLUSIVE at 350 ("up to"). Use dod_limit(dn); the two numbers are
    # deliberately not exported as loose constants, because W11a's 168 trunk d/D failures
    # began as a caller reaching for the wrong one.
    DOD_MAX_SMALL: float = 0.65
    DOD_MAX_LARGE: float = 0.50
    DOD_DN_THRESHOLD: int = 350

    # G203-p29 Table 11 "Minimum Sewer Line Gradient", Colebrook-White at 0.75 m/s, mm/m in
    # the source, stored here in m/m. Transcribed from the PDF 2026-09-03:
    #   200 5.00 | 250 3.75 | 315 2.70 | 400 2.05 | 500 1.55 | 600 1.25 | 700 1.00
    #   800 0.85 | "900 and above" 0.75
    TABLE11: Dict[int, float] = field(default_factory=lambda: {
        200: 0.00500, 250: 0.00375, 315: 0.00270, 400: 0.00205, 500: 0.00155,
        600: 0.00125, 700: 0.00100, 800: 0.00085, 900: 0.00075})
    TABLE11_FLOOR: float = 0.00075    # the "900 and above" row, G203-p29

    # Tractive-force minimum gradient. G203-p27, the equation is an EMBEDDED IMAGE with no
    # text layer, which is how it was miscopied once before. It was rendered at 5x and read
    # on 2026-09-03; it says, exactly:
    #
    #     Smin = K tau^1.23 Q^-0.461
    #
    # under the sentence "Mara, Sleigh, and Taylor (2000) developed the following
    # relationship for minimum slope based on the assumption of d/D = 0.2 and n = 0.013".
    # The surrounding TEXT gives "Q = Flow (m3/s) and K = 2.33 x 10-4 or Q = Flow (L/s) and
    # K = 5.5 x 10-3". Both K values are stored so the pair can be cross-checked.
    TRACTIVE_K_M3S: float = 2.33e-4
    TRACTIVE_K_LS: float = 5.5e-3
    TRACTIVE_TAU_EXP: float = 1.23
    TRACTIVE_Q_EXP: float = -0.461
    TRACTIVE_QMIN: float = 0.0015     # ASSUMPTION - see ASSUMPTIONS. Q floor in m3/s.

    # G203-p27: "Steeper gradient calculated based on self-cleansing velocity and minimum
    # tractive force methodology shall be adopted as minimum pipe gradient." The two routes
    # are ALTERNATIVES and the steeper governs; philosophy H5 requires the route recorded.
    # G203-p27 also says why the tractive route exists: "At the head of the sewerage
    # systems, the flow velocity based on the minimum self-cleansing may not be attainable.
    # In these circumstances, the minimum pipe gradient for the sewer shall be calculated
    # based on the hydraulic design approach of minimum tractive force."

    # =============================================================================== pipes
    # The series. Every size below is a size the guideline itself PRINTS - see DN_SOURCE.
    # W11a stopped at 1200 and 168 reaches (9.57 km, almost all trunk main) breached the
    # G203-p27 Table 10 d/D limit for want of a size the code could not emit. Extending a
    # series can only ADD a candidate, because size_pipe() still returns the smallest that
    # works, so a design that did not need these sizes is unchanged by their presence.
    # OPEN: the SERIES is ours to declare and NWS's to confirm (they print the sizes; they
    # have not confirmed the stock list). Flag DN >= 1400 on every output.
    DN_SERIES: Tuple[int, ...] = (200, 250, 315, 400, 500, 600, 700, 800, 900,
                                  1000, 1200, 1400, 1700, 1800, 2000, 2400)
    DN_LARGE_FLAG: int = 1400         # at and above this, flag the size as "guideline
                                      # tabulates it, NWS has not confirmed stock"
    DN_MIN_MAIN: int = 200            # G203-p22 Table 6, Main sewer row: "OD 200 mm
                                      # (minimal)"; also p23: secondary network "ranging in
                                      # size from 200 mm diameter (minimum) to 400 mm
                                      # diameter, however this last threshold value is not
                                      # mandatory"
    DN_MIN_LATERAL: int = 200         # G203-p22 Table 6, Lateral Sewer row: "OD 200 mm"
    DN_TERTIARY: int = 160            # G203-p22 Table 6, Rider/PC Sewer row: "OD 160 mm
                                      # (minimal)". CONFLICT: G203-p18 Table 4 gives the
                                      # PC Sewer as "150 mm (minimal)". Same document, two
                                      # numbers. We take OD160 (Table 6 is the later and
                                      # explicitly OD-designated table) and REPORT the
                                      # conflict - see CONFLICTS.
    DN_TRUNK_MIN: int = 800           # G203-p35 sec 5: NWS "consider that the Trunk mains
                                      # applies for: Diameter above 800 mm; Length above
                                      # 1,000 mm without connexions; Upstream the STP or
                                      # the Main pumping station". The "1,000 mm" is a
                                      # typo in the source for 1,000 m - see CONFLICTS.
    TRUNK_MIN_RUN_M: float = 1000.0
    DN_TRUNK_MATERIAL_MIN: int = 600  # G203-p35 Table 14 keys the trunk material list to
                                      # "> 600 mm", which is NOT the same threshold as the
                                      # 800 mm definition above. Both are quoted.

    # =========================================================================== gradients
    SLOPE_STEP: float = 0.0005        # 0.05 %. ASSUMPTION (user rule 2026-08-23): pipes are
                                      # laid at a round gradient so the number on the
                                      # drawing is the number the invert levels came from.
    LAY_TOLERANCE_M: float = 0.020    # G203-p29 sec 4.3.1, verbatim: "The lines and level of
                                      # any pipeline shall not deviate from that described
                                      # in the contract by more than 20mm and combination
                                      # of such deviation shall not create a reverse
                                      # gradient."
    FALL_TOLERANCE_M: float = 0.040   # two ends, each at LAY_TOLERANCE_M. ASSUMPTION (the
                                      # guideline states the per-point tolerance, not how
                                      # two of them compose over one reach).

    # ============================================================================ chambers
    # G203-p30 Table 12 "Maximum Spacing between Manholes", transcribed 2026-09-03:
    #   200 to 315 -> 100 m | 350 to 900 -> 120 m | 1 000 to 1 400 -> 150 m
    #   More than 1 400 -> 200 m
    # "Any alteration in the above specified spacing of manholes, consultant has to obtain
    # pre-approval from NWS."  Use mh_max_spacing(dn).
    MH_SPACING_BANDS: Tuple[Tuple[int, float], ...] = ((315, 100.0), (900, 120.0),
                                                       (1400, 150.0), (10 ** 9, 200.0))
    MH_SPLIT_LEN: float = 100.0       # the working split length: satisfies every band, so a
                                      # reach laid at it can never breach Table 12 whatever
                                      # diameter it ends up. ASSUMPTION (method choice).
    MH_ROUND_STEP: float = 10.0       # ASSUMPTION (user rule 2026-08-18) - round spacing to
    MH_ROUND_FALLBACK: float = 5.0    # 10 m, 5 m where 10 leaves an awkward remainder.
    MH_SNAP_M: float = 3.0            # m. THE ONE minimum-chamber-clearance constant, and it
                                      # is also the node-merge radius: two chambers closer
                                      # than this ARE one structure, so the graph cannot hold
                                      # a pair a contractor would build as one. ASSUMPTION -
                                      # no minimum chamber spacing exists in G201/G202/G203
                                      # (searched); 3 m is a physical-size convention.
                                      # `MH_MIN_CLEAR_M` below is a READ-ONLY ALIAS of this
                                      # field, not a second constant - see the property.
    FANOUT_OFFSET_M: float = 10.0     # ASSUMPTION (user rule 2026-08-18) - a branch leaving
                                      # a chamber that already has an outlet starts 10 m
                                      # away, or at the next house connection.

    INLET_MIN_DEG: float = 90.0       # G203-p30, verbatim: "No inlet pipe at manholes shall
                                      # have an angle less than 90 deg to the direction of
                                      # flow." Repeated at p19 sec 3.6 for the connection to
                                      # the main sewer. W8's 85 deg working tolerance is NOT
                                      # carried - see the header.

    DROP_TRIGGER: float = 0.60        # m. G203-p30: "Connections under these conditions
                                      # require the use of a backdrop when the difference in
                                      # invert elevations exceeds 600 mm. Backdrops shall be
                                      # constructed external to the manhole." Also p19 3.6:
                                      # "Falls of more than 600 mm are not permitted and, if
                                      # necessary, a backdrop must be set up outside the
                                      # manhole."
    BACKDROP_MAX: float = 2.0         # m. G203-p30: "The maximum backdrop height should be
                                      # of 2 m. Beyond this limit, specific devices like
                                      # vortex drop shafts should be used."
    MH_DIA_INTERNAL_BACKDROP: float = 1.5   # m. G203-p30: "Internal backdrops are not
                                      # permitted on manholes that are less than 1.5 m in
                                      # diameter since this would restrict access."
    DROP_CEILING_M: float = 20.0      # ASSUMPTION, AND AN OPEN ENGINEERING DECISION.
                                      # G203-p30 sends anything past 2 m to a vortex drop
                                      # shaft and gives NO maximum for one. Philosophy sec 5
                                      # requires a declared ceiling so an over-cap exit can
                                      # be WITHDRAWN rather than clipped. 20.0 m is the
                                      # bound W11a declared (as the DROP_M field range) and
                                      # it is carried here unchanged so the two iterations
                                      # are comparable - it is NOT an engineering judgement
                                      # that a 20 m vortex shaft is buildable. Needs a
                                      # number from the engineer. See ASSUMPTIONS.

    # =========================================================================== depth
    MIN_COVER_CROWN: float = 1.30     # m. G203-p33 sec 4.6.3: "The minimum depth for sewer
                                      # pipes shall be 1.3 m to the crown of the pipe."
    MIN_COVER_PROTECTED: float = 0.50 # m. G203-p33: "If circumstances require installation
                                      # of a pipe with depth less than 1.3 m above the
                                      # crown, then concrete protection is required. The
                                      # minimum cover above the pipe and its protection
                                      # shall be 0.5 m."
    MIN_COVER_WADI_XING: float = 1.50 # m. G203-p52 sec 8.2.4, whose preamble is "As for
                                      # gravitational sewer, the minimum cover should be"
                                      # and whose third bullet is "At Wadi crossing: 1.5 m
                                      # (depth to crown of pipe)". The clause SITS IN THE
                                      # FORCE MAIN CHAPTER; adopting it for a gravity
                                      # crossing is a PROJECT DECISION (see header) and a
                                      # gravity reach at 1.30 m over a crossing is short of
                                      # OUR rule, not of the guideline's.
    MAX_COVER: float = 12.0           # m. G203-p33: "The recommended maximum cover for sewer
                                      # pipes is approximately 10 - 12m. Depths with cover
                                      # greater than this shall be investigated with pipe
                                      # manufacturers... Where the cost of excavation becomes
                                      # prohibitive the Engineer shall incorporate pumping
                                      # stations into the design." It is a RECOMMENDATION on
                                      # a range, triggered by COST - we adopt the top of the
                                      # range as the cap, which is a project decision.
    UTILITY_CLEARANCE_M: float = 3.0  # m. G203-p33: "Minimum horizontal clearance of 3 m is
                                      # required. If utilities are in the same trench, the
                                      # other utility shall be placed on a separate bench on
                                      # un-disturbed soil."

    # THE ONE WALL/BEDDING ALLOWANCE. There is no second copy of this anywhere in W12, and
    # contract.py imports invert_depth_min() and cover() rather than re-deriving them.
    # G203-p33 gives cover TO CROWN and says nothing about what sits between the crown and
    # the invert beyond the pipe itself, so this is an ASSUMPTION: it stands for the wall
    # thickness of an ID-designated pipe (GRP is sized on its bore, so its true outside
    # diameter is nominal + 2 walls) plus a nominal bedding allowance. It is small and it
    # is one number; when W11a carried two (0.05 here, 0.10 in the contract) the auditor
    # demanded 50 mm more cover than the design laid at every diameter and a BLOCKING check
    # failed on every reach.
    WALL_ALLOW: float = 0.05

    # =============================================================== tertiary (G203 sec 3)
    PCS_MIN_SLOPE: float = 0.03       # G203-p18 Table 5, Property Connection Sewer: 3 % min
    PCS_MAX_SLOPE: float = 0.10       # ... 10 % max
    RIDER_MIN_SLOPE: float = 0.01     # G203-p18 Table 5, Rider Sewer: 1 % min
    RIDER_MAX_SLOPE: float = 0.10
    LATERAL_MIN_SLOPE: float = 0.01   # G203-p18 Table 5, Lateral Sewer: 1 % min
    LATERAL_MAX_SLOPE: float = 0.10
    PCS_MAX_LEN: float = 50.0         # m. G203-p18, under Table 4: "The length of the PCS
                                      # should not exceed 50 m in order to allow
                                      # maintenance. If necessary, a manhole will be added."
    PCS_MIN_COVER: float = 0.60       # m. G203-p19 sec 3.5: "For Property Connection Sewer a
                                      # minimum cover of 600 mm is required and can go up to
                                      # 1.50 m depth (in square dimension 800x800)."
    LATERAL_MAX_LEN: float = 45.0     # m. G203-p22 Table 6 puts "Maximum Length 45 m" on the
                                      # LATERAL row only; G203-p17 sec 3.2 reads "Rider
                                      # Sewers and Lateral Sewers (maximum Length 45 m)",
                                      # which attaches it to both. We take the conservative
                                      # reading - 45 m on both - as a declared project cap.
    MAX_HCC_PER_RIDER: int = 3        # G203-p17 sec 3.2: "Several HCC (usually up to 3) may
                                      # be connected together by one or several Rider Sewers
                                      # within the public ROW." "usually" - a convention.
    HCC_OFFSET_M: float = 2.5         # m. G203-p17: "The HCC is usually installed 2.5 m from
                                      # the property boundary in the public right-of-way"
    HCC_DEPTH_MIN: float = 1.2        # m. G203-p19 sec 3.4: HCC depth "ranges between 1.2 m
    HCC_DEPTH_MAX: float = 2.0        # and 2.0 m depending on the size of the plot"

    # ===================================================================== pumping stations
    PS_TYPE1_MAX_LS: float = 100.0    # G203-p40: "Type 1: Design flow up to 100 l/s."
    PS_TYPE2_MAX_LS: float = 300.0    # "Type 2: ... greater than 100 l/s up to 300 l/s."
                                      # "Type 3: Design flow greater than 300 l/s."
    # G203-p40 Table 17 duty/standby: Type 1 = 1+1, Type 2 = 2+1, Type 3 = 3+1.
    PS_DUTY_PUMPS: Tuple[int, int, int] = (1, 2, 3)
    PS_STANDBY_PUMPS: Tuple[int, int, int] = (1, 1, 1)
    PS_LAND_M2_MIN: Tuple[float, float, float] = (50.0, 200.0, 900.0)   # G203-p43 Table 21
    PS_LAND_M2_MAX: Tuple[Optional[float], Optional[float], Optional[float]] = (
        100.0, 400.0, None)           # "50-100 m2 | 200-400 m2 | >=900 m2"
    PS_ACCESS_TURN_M: float = 6.0     # G203-p43 Table 21: "At least 6 m wide turning circle
                                      # with hard standing for vehicles"
    PS_PIPEWORK_V_MAX: float = 2.5    # G203-p41 Table 17, velocity through pipework at
    PS_PIPEWORK_V_MIN: float = 0.6    # maximum flow 2.5 m/s; at minimum flow "0.6 m/s
    PS_PIPEWORK_V_MIN_GRIND: float = 0.5  # standard, 0.5 m/s with grinder pump"
    PS_SOLIDS_MM: float = 76.0        # G203-p41: "76 mm minimum without upstream basket and
    PS_SOLIDS_MM_BASKET: float = 65.0 # 65 mm with upstream basket"
    PS_MOTOR_RPM_MAX: float = 1450.0  # G203-p41: max pump motor speed (> 5 l/s)
    PS_MOTOR_RPM_SMALL: float = 2800.0  # "Max speed for small pumps up to 5 l/s"
    PS_SERVICE_LIFE_YR: int = 15      # G203-p40 Table 17: "Service rating: 15 years design
                                      # life". NOTE p38 says non-structural mechanical
                                      # installations have a 20 yr design life; Table 17 is
                                      # the pump-specific figure and governs pump renewal in
                                      # a life-cycle cost. Both are quoted - see CONFLICTS.
    WELL_STARTS_MIN: float = 10.0     # G203-p48 sec 7.8: "The number of starts per hour for
                                      # the pump/motor shall be minimum 10 for smaller
                                      # motors (Up to 30 Kw)"
    WELL_K: float = 0.25              # G203-p48: "V = 0.25 QT", V m3, Q single-pump capacity
                                      # m3/s, T = 3600 / starts per hour
    WELL_LEVEL_SEP_M: float = 0.20    # G203-p48: successive start/stop levels "separated by
                                      # at least 200 mm to 300 mm"
    PS_CFD_THRESHOLD_M3S: float = 0.5 # G203-p48: "For large pumping stations flow (0.5
                                      # m3/s)" -> CFD and physical modelling
    PS_FLOOR_ABOVE_FLOOD_M: float = 0.30  # G203-p38 sec 7.2: floors min 300 mm above the
                                      # 1:50-yr flood level; transformers, substation and
                                      # emergency generator above maximum flood level
    PS_FLOOD_ARI_YR: int = 50         # G203-p38 sec 7.2: surface/stormwater to 1:50 ARI
    # G203-p40 sec 7.4 Table 16 "Minimum Pump Flow": average flow (l/s) -> minimum flow
    # factor. "the initial minimum flow rate shall be considered in sizing the force main so
    # that deposition at low velocity is avoided."
    PS_MIN_FLOW_FACTORS: Tuple[Tuple[float, float], ...] = ((50.0, 0.25), (500.0, 0.35),
                                                            (2500.0, 0.45), (5000.0, 0.50))

    # ========================================================================== force mains
    FM_V_MIN: float = 0.75            # m/s. G203-p50 sec 8.1: "At design minimum flow (that
                                      # is, maximum static head), a velocity of at least
                                      # 0.75 m/s shall be maintained for raw sewage". The
                                      # floor is held at the DESIGN MINIMUM flow, not at
                                      # average - Table 16 supplies that flow.
    FM_V_MIN_INTERMITTENT: float = 1.0   # G203-p50: "in the case of intermittent flow,
                                         # required minimum velocity shall be 1.0 m/s"
    FM_V_MIN_VERTICAL: float = 1.2    # G203-p50: vertical force mains
    FM_V_MAX: float = 2.5             # G203-p50: "The maximum allowable velocity (worst case
                                      # scenario) in the pipe shall be not greater than 2.5
                                      # m/s." THIS IS NOT THE GRAVITY 3.0 - the two were
                                      # conflated once already.
    FM_ID_MIN_MM: float = 75.0        # G203-p50: "minimum 75 mm inside diameter for non-clog
    FM_ID_MIN_GRINDER_MM: float = 50.0  # pumps and minimum 50 mm inside diameter for
                                      # grinder pumps"
    FM_GRAD_RISING: float = 1.0 / 500.0   # G203-p50 sec 8.2.1: "recommended minimum gradient
    FM_GRAD_FALLING: float = 1.0 / 300.0  # of 1:500 rising and 1:300 falling even if the
    FM_GRAD_NEVER_BELOW: float = 1.0 / 750.0  # terrain is flat (in all cases never below
                                      # 1: 750 gradient)"
    FM_RETENTION_MIN: float = 30.0    # minutes. G203-p50: "short enough to produce a
                                      # retention period no longer than half an hour"
    FM_ACCESS_M: float = 500.0        # G203-p50: "Provision shall be included to access pipe
                                      # every 500 m"
    FM_TERMINATION_ABOVE_MM: float = 300.0  # G203-p55 sec 8.5: discharge to the gravity
                                      # system at a manhole, entering not more than 300 mm
                                      # above the receiving manhole flow line

    # =============================================================================== loads
    LPCD_WATER: float = 164.0         # l/c/d domestic water, Adh Dhahirah. G201-p59-60
                                      # Table 11. The table's own caveats: "indicative
                                      # figures derived from the recent Integrated Master
                                      # Plan (2024)", apply "in absence of any updated
                                      # figures", and "should be validated by NWS as
                                      # essential design criteria, before designing the
                                      # project".
    RETURN_DOM: float = 0.85          # G201-p71 Table 19: "Domestic & Tanker 85%"
    RETURN_NONDOM: float = 0.54       # G201-p71 Table 19: "Non-Domestic (Government and
                                      # commercial) 54%"
    RATIO_NONDOM: float = 0.22        # G201-p60 Table 11 header: "*Distributed* Non-Domestic
    RATIO_GOV: float = 0.14           # Ratio (% LPCD)" - a governorate water-balance volume
                                      # spread over population, NOT a per-person demand.
    WWG_LCD: float = 171.3            # l/c/d area-average wastewater generation including
                                      # the Tier-A non-domestic and governmental uplift.
                                      # DERIVED (project), not a guideline figure - see
                                      # ASSUMPTIONS and PROJECT-STATE sec 2 for the
                                      # derivation and the load-allocation doctrine.
    INFILT_L_D_KM: float = 720.0      # G201-p72 sec 7.4.3: "For newly designed networks, a
                                      # linear infiltration allowance of 720 liters per day
                                      # per kilometer (L/d/km) of sewer should be
                                      # incorporated into the design." Also: "Infiltration
                                      # due to storm water is not considered", and G201-p73:
                                      # "Tanker or vacuum collection do not require to
                                      # account for infiltration volume."
    INFILT_UNPEAKED: bool = True      # ASSUMPTION - G201 does not state the order of
                                      # operations; infiltration is a steady ingress and is
                                      # added AFTER the sanitary peak. Confirm at kickoff.
    INFILT_EXISTING_INLAND: float = 0.10   # G201-p72: existing networks inland / outside
    INFILT_EXISTING_GW: float = 0.40       # groundwater influence 10 %; within groundwater
                                      # table zones or coastal "up to 40%"
    PF_HOLD_PROPERTIES: int = 100     # G201-p71 sec 7.4.2: "The Merrimack formula is to be
                                      # used ... for an area (catchment or sub catchment)
                                      # having over 100 properties." Below that G201
                                      # prescribes NO formula, so the honest answer is
                                      # "held", not a number nobody can reproduce.
    PF_MERRIMACK_A: float = 2.65      # G201-p71: Qpdf = 2.65 Qadf^0.879, BOTH in Ml/day
    PF_MERRIMACK_B: float = 0.879
    PF_PELTIER_A: float = 1.5         # G201-p72: PfWW = 1.5 + 1/sqrt(Qm), "NOTE: The Average
                                      # Daily Flow in this formula is in liters per second"
    PF_REPORT_ABOVE: float = 5.0      # G201-p72 NOTE: "It is recommended that the hourly
                                      # peak factor should not exceed 5.0" - a RECOMMENDATION.
                                      # Never silently truncate; report when it is exceeded.
    STP_MARGIN: float = 0.10          # G201-p73 sec 7.4.5: "A 10% margin should be applied
                                      # when designing new STPs ... over and above any
                                      # redundancies in the design"
    TSE_PRODUCTION_RATIO: float = 0.95     # G201-p73 sec 7.4.6.1

    OCCUPANCY: float = 5.32           # people per property. DERIVED 2026-08-30 from
                                      # settlement population / counted domestic electricity
                                      # accounts. Supersedes the 5.0 the client team set and
                                      # the 6.0 assumed in W1-W4. ASSUMPTION in the sense
                                      # that no guideline gives it.
    PROPS_PER_PLOT: float = 1.456     # MEASURED from electricity accounts over 64,027
                                      # records; this is the FALLBACK for a plot with no
                                      # account on it. The per-plot count is read from the
                                      # data, not from this number.

    # ========================================================================== materials
    # G203-p23 Table 8 "Roughness Coefficient for Commonly Used Non-Metallic Pipes",
    # Manning's n: concrete cement lining 0.012 | FRP 0.009-0.011 | plastic 0.009 |
    # PE 0.009-0.015 | corrugated PE smooth bore 0.010 | PVC/CPVC 0.009-0.011.
    # The DESIGN uses Colebrook-White with ks (G203-p24, mandated); Manning n is carried
    # only for the SewerGEMS export, which wants an n.
    MANNING_N_EXPORT: float = 0.013   # ASSUMPTION - the conservative n behind the tractive
                                      # equation's own derivation (G203-p27 "n = 0.013"), so
                                      # the referee model and the tractive check share it.

    # ================================================================= wadi / flood hazard
    #
    # THIS BLOCK IS THE ONLY DECLARATION OF THE FLOOD-GRID THRESHOLDS IN W12.
    # DEFECT 4, fixed 2026-09-03. Before the fix these quantities had TWO answers each:
    #   "which classes are washout/wadi ground"   criteria (4,5,6)  vs  hazard.py
    #                                             DEFAULT_SCOUR_CLASS = 5
    #   "which return period is the wadi test"    criteria 50       vs  hazard.py's
    #                                             _DUTIES["pipe_washout"] = (50,)
    #   "is no-data dry"                          criteria True     vs  hazard.py's
    #                                             HazardGrids(nodata_is_dry=True)
    # `w12.hazard` now READS these three; it declares none of them.  The measured cost of
    # the disagreement, on the client's Main Pipe at the 50-year event: the H5+ reading
    # called 6.77 km of the alignment washout ground, the registered H4+ reading calls
    # 11.02 km - a 4.25 km gap on one input alignment, from two constants for one quantity.
    #
    # The value itself is the project register's: _BRAIN/02_DESIGN_CRITERIA.md sec 6 row
    # "What counts as 'wadi ground'".  It is an ASSUMPTION, not a guideline threshold.
    HAZARD_WADI_CLASSES: Tuple[int, ...] = (4, 5, 6)   # ASSUMPTION. AR&R flood-hazard
                                      # classes of the 50-year grid standing in for G203's
                                      # "areas subject to washout", which is a SCOUR
                                      # criterion. A defensible proxy; settle with a
                                      # scour-depth check.
                                      # CORRECTION 2026-09-03: the rationale carried here
                                      # and in 02_DESIGN_CRITERIA.md sec 6 - "class 4 is
                                      # about 1.2 m of water" - IS WRONG, and the client's
                                      # own rasscript disproves it. Exhausting that decision
                                      # tree gives H4 a depth band of 0.300-2.000 m, and H4
                                      # can be triggered by d*v > 0.6 with only 0.3 m of
                                      # water. No AR&R class above H3 is a statement about
                                      # depth. The THRESHOLD is unchanged; only the reason
                                      # given for it is withdrawn.
    HAZARD_CHANNEL_MIN_CLASS: int = 3 # ASSUMPTION. The shallowest class whose trigger is
                                      # unambiguously depth (d > 0.5 m in the client's
                                      # rasscript) and the class at which a vehicle can no
                                      # longer stand in the flow - the practical edge of the
                                      # running channel. DISTINCT from HAZARD_WADI_CLASSES:
                                      # "where the water runs" is not "where a pipe would be
                                      # washed out". Both are declared here, once each.
    HAZARD_RETURN_YR: int = 50        # the grid used for the wadi test
    HAZARD_NODATA_IS_DRY: bool = True # ENGINEER'S DECISION 2026-09-03: flood no-data is DRY
                                      # HIGH GROUND, not "untested". Flow runs in the wadis.
                                      # This reverses W11a, where 1,170 reaches were
                                      # "undecidable" because the far bank lay outside a
                                      # grid covering 47 % of the area. Report the covered
                                      # fraction beside every wadi result all the same.
    WADI_XING_SKEW_DEG: float = 25.0  # ASSUMPTION - H1 says a crossing is "perpendicular";
                                      # the tolerance on that word is ours.
    DUAL_XING_MAX_M: float = 70.0     # ASSUMPTION - longest perpendicular crossing of a dual
                                      # carriageway.

    # ================================================================== TERRAIN-FIRST BLOCK
    # New in W12, and the reason W12 exists. W11a built its layout on ROAD CONNECTIVITY
    # and used the terrain only to CHECK the answer; 42.5 % of its length (737.7 km) then
    # drained uphill and it wanted 2,449 vortex drop shafts where the built network has 37.
    # Philosophy sec 4: "The tree drains WITH the ground ... Uphill drainage is not forbidden
    # ... but it is bounded and reported: the share of length draining against the ground,
    # the cumulative climb along the flow path, and the worst single rise. The diagnostic is
    # the drop-structure count."
    #
    # THERE IS NO GUIDELINE NUMBER FOR ANY OF THIS. Nothing below is a limit. They are the
    # names of the quantities that must be measured, plus one MEASURED benchmark.
    TERRAIN_RES_M: float = 0.5        # the 0.5 m bare-earth VRT (project rule 6); recorded
                                      # so a sampled ground level can be traced to a source
    ADVERSE_MIN_M: float = 0.05       # m. ASSUMPTION - a reach is only counted as draining
                                      # AGAINST the ground when the ground rises by more than
                                      # this along it. Below it the "rise" is DEM noise on a
                                      # short reach, and counting it inflates the headline
                                      # number that this whole iteration turns on.

    # ============================================================================ tractive
    TAU_PA: float = 1.0               # Pa. ENGINEER'S DECISION 2026-09-03: keep 1.0 and FLAG
                                      # it on every output. G203-p27 sec 4.2.2.1 gives the
                                      # equation and NO numeric design tau (GAP-9). 1.0 Pa is
                                      # the Mara et al. simplified-sewerage value. It gives
                                      # shallower slopes, so shallower pipes and fewer pumps;
                                      # if NWS return 2.0 the required slopes roughly double
                                      # - exactly 2^1.23 = 2.346x. See tau_sensitivity().

    # =============================================================== derived, one definition
    @property
    def MH_MIN_CLEAR_M(self) -> float:
        """Minimum clear distance between two chambers, m. A READ-ONLY ALIAS of MH_SNAP_M.

        DEFECT 4, fixed 2026-09-03. This was a second FIELD holding 3.0, beside MH_SNAP_M
        holding 3.0, for the same physical quantity - MH_SNAP_M's own comment defined itself
        as "closer than the clearance". Two fields means `replace(DEFAULT, MH_SNAP_M=2.0)`
        silently leaves the clearance at 3.0 and the layout stage and the audit stage then
        disagree about whether two chambers are one structure. It is now a property, so
        there is exactly one editable value and `replace(..., MH_MIN_CLEAR_M=...)` raises
        instead of creating the split."""
        return self.MH_SNAP_M

    @property
    def PLOT_QADF_M3D(self) -> float:
        """Per-property saturation average dry-weather flow, m3/d. DERIVED, not a guideline
        value: OCCUPANCY x WWG_LCD / 1000. The per-PLOT figure multiplies by the counted
        properties on that plot, which is data, not this constant."""
        return self.OCCUPANCY * self.WWG_LCD / 1000.0

    @property
    def TAU_SLOPE_FACTOR_AT_2PA(self) -> float:
        """How much steeper every tractive-governed gradient becomes if NWS answer 2.0 Pa.
        (2.0/1.0)^1.23 exactly - the equation is a power law in tau, so the factor is the
        same at every diameter and every flow."""
        return (2.0 / self.TAU_PA) ** self.TRACTIVE_TAU_EXP

    # ================================================================= helpers (cited each)
    def dod_limit(self, dn: int) -> float:
        """Maximum d/D at peak flow for this diameter. G203-p27 Table 10, verbatim:
        "Pipe Diameter up to 350 mm -> 0.65"; "Pipe Diameter > 350 mm -> 0.50".

        A FUNCTION, not two exported constants. W11a exported the pair and a caller reaching
        for the wrong one is how 168 trunk reaches shipped over the limit."""
        return self.DOD_MAX_SMALL if dn <= self.DOD_DN_THRESHOLD else self.DOD_MAX_LARGE

    def mh_max_spacing(self, dn: int) -> float:
        """Maximum chamber spacing, m. G203-p30 Table 12. Bands, not a formula."""
        for hi, spacing in self.MH_SPACING_BANDS:
            if dn <= hi:
                return spacing
        raise CriteriaError(f"no Table 12 spacing band for DN{dn}")   # unreachable

    def table11(self, dn: int) -> float:
        """Minimum gradient from G203-p29 Table 11, m/m. Sizes between tabulated ones take
        the next SMALLER tabulated diameter's (steeper) value - never interpolated down,
        which would give a flatter gradient than the guideline prints for a pipe of that
        size. Above 900 the table says "900 and above"."""
        if dn in self.TABLE11:
            return self.TABLE11[dn]
        if dn >= 900:
            return self.TABLE11_FLOOR
        smaller = [d for d in self.TABLE11 if d <= dn]
        if not smaller:
            # below DN200 - the tertiary network, where G203-p18 Table 5 governs with
            # percentage slopes, not Table 11.
            raise CriteriaError(
                f"DN{dn} is below the Table 11 range (200-900+). The tertiary network is "
                "governed by G203-p18 Table 5 (PCS 3-10 %, rider and lateral 1-10 %), not "
                "by Table 11 - using Table 11's 0.5 % at DN200 for a lateral is a design "
                "trap the criteria file will not help you into.")
        return self.TABLE11[max(smaller)]

    def outside_diameter(self, dn: int) -> float:
        """Crown-to-invert height, m. The pipe's OUTSIDE diameter, not its bore.

        PVC-U is OD-designated in G203-p22 Table 6 ("OD 200 mm (minimal)"), so OD = DN.
        GRP is sized on its bore, so its true OD is nominal + 2 x wall; the wall class is
        pending (PAM-SPC-207), so nominal is used and WALL_ALLOW carries the difference.
        Geometry uses this; hydraulics use internal_diameter()."""
        return dn / 1000.0

    def internal_diameter(self, dn: int) -> float:
        """True internal bore, m - the diameter every hydraulic calculation runs on.

        To DN315 the series is OD-designated (G203-p22 Table 6) and the bore is smaller than
        the nominal size by two wall thicknesses. PVC-U SN8 is SDR34, so ID = OD(1 - 2/34).
        The wall class is an ASSUMPTION pending PAM-SPC-207. Above 315 the pipe is GRP or
        RCC, whose nominal size IS the internal diameter."""
        if dn <= 315:
            return dn / 1000.0 * (1.0 - 2.0 / 34.0)
        return dn / 1000.0

    def invert_depth_min(self, dn: int) -> float:
        """Minimum depth of INVERT below ground, m, for a reach of this diameter.

        MIN_COVER_CROWN (1.30, G203-p33) + outside diameter + WALL_ALLOW.

        THE ONLY DEFINITION. `cover()` is its exact inverse and nothing else in W12
        computes either. The failure this prevents: W11a had this expression in criteria
        with WALL_ALLOW = 0.05 and a second copy in the contract with 0.10, so a design laid
        to one sat 50 mm shallow against the other at EVERY diameter and a blocking cover
        check failed on EVERY reach.
        """
        return self.MIN_COVER_CROWN + self.outside_diameter(dn) + self.WALL_ALLOW

    def cover(self, dn: int, invert_depth_m: float) -> float:
        """Cover to crown, m, from the depth to invert. The exact inverse of
        invert_depth_min(), on the reach's OWN outside diameter (G203-p33).

        Every published depth or cover statistic - schedule, drawing, audit - goes through
        this one function. W10 used a hardcoded 0.30 m regardless of diameter and shipped
        45.92 km below the minimum cover."""
        return float(invert_depth_m) - (self.outside_diameter(dn) + self.WALL_ALLOW)

    def min_cover_for(self, on_wadi_crossing: bool = False,
                      concrete_protected: bool = False) -> float:
        """The governing minimum cover for this situation, m, and the only place the three
        figures are chosen between.
            plain gravity        1.30   G203-p33 sec 4.6.3
            concrete-protected   0.50   G203-p33 sec 4.6.3
            at a wadi crossing   1.50   G203-p52 sec 8.2.4 - PROJECT DECISION for gravity
        """
        if on_wadi_crossing:
            return self.MIN_COVER_WADI_XING
        if concrete_protected:
            return self.MIN_COVER_PROTECTED
        return self.MIN_COVER_CROWN

    def is_trunk(self, dn: int, run_len_m: float = 0.0, at_works: bool = False) -> bool:
        """G203-p35 sec 5, all three of NWS's criteria, quoted: trunk mains apply for
        "Diameter above 800 mm", "Length above 1,000 mm without connexions" (a typo for
        1,000 m - see CONFLICTS) and "Upstream the STP or the Main pumping station"."""
        return dn > self.DN_TRUNK_MIN or run_len_m > self.TRUNK_MIN_RUN_M or at_works

    # G203-p22 Table 6 is by APPLICATION; G203-p23 Table 7 is by PRODUCT; G203-p35 Table 14
    # is the trunk list. All three transcribed 2026-09-03. The first material in each tuple
    # is the default this project uses.
    MATERIALS_BY_TIER: Dict[str, Tuple[Tuple[int, int, Tuple[str, ...]], ...]] = field(
        default_factory=lambda: {
            # tier            (dn_lo, dn_hi, permitted open-trench materials)
            "rider":   ((160, 10 ** 9, ("PVC-U", "HDPE")),),               # G203-p22 T6 r1
            "lateral": ((200, 10 ** 9, ("PVC-U", "HDPE", "GRP")),),        # G203-p22 T6 r2
            "main":    ((200, 250, ("PVC-U", "HDPE", "GRP")),              # T6 r3: "PVC-U
                        (251, 300, ("HDPE", "GRP")),                       # (up to 250 mm)"
                        (301, 10 ** 9, ("GRP", "HDPE", "GRP/PVC", "lined RCC"))),  # T6 r4
            "sub main": ((200, 250, ("PVC-U", "HDPE", "GRP")),
                         (251, 300, ("HDPE", "GRP")),
                         (301, 10 ** 9, ("GRP", "HDPE", "GRP/PVC", "lined RCC"))),
            "trunk main": ((200, 600, ("GRP", "HDPE", "GRP/PVC", "lined RCC")),
                           (601, 10 ** 9, ("GRP", "lined RCC", "HDPE"))),  # G203-p35 T14
        })

    def materials_allowed(self, tier: str, dn: int) -> Tuple[str, ...]:
        """Permitted open-trench materials for this tier at this diameter.

        Takes TIER as well as DN because the two governing tables ask different questions.
        G203-p23 Table 7 permits U-PVC as a PRODUCT to OD315; G203-p22 Table 6 permits it on
        a MAIN SEWER only "(up to 250 mm)". A dn-only helper cannot express that, and W8's
        returned PVC-U for a DN315 main, which Table 6 does not allow."""
        t = str(tier).strip().lower()
        bands = self.MATERIALS_BY_TIER.get(t)
        if bands is None:
            raise CriteriaError(
                f"no G203 material row for tier {tier!r}. Known tiers: "
                f"{sorted(self.MATERIALS_BY_TIER)}. An unrecognised tier must RAISE - "
                "returning a default is how a pipe gets a material the guideline refuses.")
        for lo, hi, mats in bands:
            if lo <= dn <= hi:
                return mats
        raise CriteriaError(f"DN{dn} is outside every G203 material band for tier {tier!r}")

    def material(self, tier: str, dn: int) -> str:
        """The project's default material: the first permitted one for the tier and size."""
        return self.materials_allowed(tier, dn)[0]

    def ps_type(self, q_design_ls: float) -> str:
        """G203-p40: Type 1 up to 100 l/s, Type 2 >100 to 300, Type 3 >300."""
        if q_design_ls <= self.PS_TYPE1_MAX_LS:
            return "Type 1"
        if q_design_ls <= self.PS_TYPE2_MAX_LS:
            return "Type 2"
        return "Type 3"

    def ps_land_m2(self, ps_type: str) -> Tuple[float, Optional[float]]:
        """G203-p43 Table 21 minimum land area band for a station type, m2."""
        i = {"Type 1": 0, "Type 2": 1, "Type 3": 2}.get(str(ps_type))
        if i is None:
            raise CriteriaError(f"unknown pumping station type {ps_type!r}")
        return self.PS_LAND_M2_MIN[i], self.PS_LAND_M2_MAX[i]

    def ps_min_flow_factor(self, q_avg_ls: float) -> float:
        """G203-p40 Table 16. The table gives four points (50, 500, 2500, 5000 l/s ->
        0.25, 0.35, 0.45, 0.50); between them we interpolate LINEARLY IN log10(Q), which is
        a method choice (ASSUMPTION) because the guideline tabulates rather than fits.
        Below 50 l/s and above 5000 the end values are held."""
        pts = self.PS_MIN_FLOW_FACTORS
        if q_avg_ls <= pts[0][0]:
            return pts[0][1]
        if q_avg_ls >= pts[-1][0]:
            return pts[-1][1]
        for (q0, f0), (q1, f1) in zip(pts, pts[1:]):
            if q0 <= q_avg_ls <= q1:
                t = (math.log10(q_avg_ls) - math.log10(q0)) / (math.log10(q1) - math.log10(q0))
                return f0 + t * (f1 - f0)
        raise CriteriaError("Table 16 interpolation fell through")   # unreachable

    def well_volume_m3(self, q_single_pump_m3s: float,
                       starts_per_hour: Optional[float] = None) -> float:
        """G203-p48 sec 7.8: V = 0.25 Q T, T = 3600 / starts per hour, minimum 10 starts/h
        for motors up to 30 kW."""
        s = self.WELL_STARTS_MIN if starts_per_hour is None else float(starts_per_hour)
        if s < self.WELL_STARTS_MIN:
            raise CriteriaError(
                f"{s} starts/h is below the G203-p48 minimum of {self.WELL_STARTS_MIN} for "
                "motors up to 30 kW. A lower rate buys a smaller wet well by breaching the "
                "cycle rule.")
        return self.WELL_K * float(q_single_pump_m3s) * (3600.0 / s)

    def pf_merrimack(self, qadf_mld: float) -> float:
        """G201-p71 sec 7.4.2, MANDATORY above PF_HOLD_PROPERTIES (100) properties:
        Qpdf = 2.65 Qadf^0.879, BOTH in Ml/day; Pf = Qpdf/Qadf."""
        if qadf_mld <= 0:
            return 1.0
        return self.PF_MERRIMACK_A * qadf_mld ** self.PF_MERRIMACK_B / qadf_mld

    def pf_peltier(self, qm_ls: float) -> float:
        """G201-p72, the IMP2024 alternative: PfWW = 1.5 + 1/sqrt(Qm), Qm in LITRES PER
        SECOND (the guideline puts that in a NOTE because it is the easy mistake)."""
        if qm_ls <= 0:
            return 1.0
        return self.PF_PELTIER_A + 1.0 / math.sqrt(qm_ls)

    def peak_factor(self, qadf_m3d: float, n_prop: float) -> Tuple[float, str]:
        """(peak factor, method). Returns ("held") below 100 properties, because G201
        prescribes NO formula there and a number nobody can reproduce is worse than an
        honest hold. Above it, Merrimack - G201-p71 says "is to be used"."""
        if n_prop is not None and n_prop <= self.PF_HOLD_PROPERTIES:
            return 1.0, "held"
        return self.pf_merrimack(max(qadf_m3d, 1e-9) / 1000.0), "merrimack"

    def infiltration_ls(self, length_m: float) -> float:
        """G201-p72: 720 L/d/km of sewer, for NEW networks. Unpeaked.

        The trap this signature exists to avoid: infiltration is a PER-PIPE load. Summing a
        per-reach value that already includes everything upstream counts every kilometre
        once per downstream reach - which is how a 14.5 L/s total was published as 1,259."""
        return self.INFILT_L_D_KM * (float(length_m) / 1000.0) / 86400.0

    def round_slope_up(self, s: float) -> float:
        """Round a gradient UP to the next SLOPE_STEP. On a single pipe rounding down would
        breach the minimum, so a single pipe always rounds up (ASSUMPTION, user 2026-08-23)."""
        return math.ceil(s / self.SLOPE_STEP - 1e-12) * self.SLOPE_STEP

    def round_slope_down(self, s: float) -> float:
        """Round a gradient DOWN to a SLOPE_STEP. Used to ease a whole RUN, which leaves the
        far end slightly shallower and never deeper. The caller must re-test the minimum."""
        return math.floor(s / self.SLOPE_STEP + 1e-12) * self.SLOPE_STEP

    # ============================================================================== banners
    def tau_banner(self) -> str:
        """The flag the engineer asked for on 2026-09-03, on EVERY output that carries a
        gradient, a depth or a station count."""
        return (
            f"TRACTIVE STRESS tau = {self.TAU_PA:g} Pa - AN ASSUMPTION, NOT A GUIDELINE "
            f"VALUE. PAM-GUD-203 sec 4.2.2.1 (p27) gives the equation "
            f"Smin = K tau^{self.TRACTIVE_TAU_EXP} Q^{self.TRACTIVE_Q_EXP} and no numeric "
            f"design tau (GAP-9). At tau = 1.0 Pa the required gradients are the shallowest "
            f"the method allows, so the pipes are shallower and the stations fewer. If NWS "
            f"return tau = 2.0 Pa every tractive-governed gradient rises by "
            f"{self.TAU_SLOPE_FACTOR_AT_2PA:.3f}x and every level downstream of it changes.")

    def tau_sensitivity(self, tau_alt: float = 2.0) -> Dict[str, float]:
        """The number behind the banner: the multiplier on every tractive-governed gradient
        at an alternative tau. Exact, because the equation is a power law in tau alone."""
        return {"tau_design_pa": self.TAU_PA, "tau_alt_pa": tau_alt,
                "slope_factor": (tau_alt / self.TAU_PA) ** self.TRACTIVE_TAU_EXP}

    def large_dn_banner(self, dns) -> str:
        """The flag for DN1400 and above (engineer's decision 2026-09-03: use the sizes the
        guideline tabulates, and flag them)."""
        big = sorted({int(d) for d in dns if int(d) >= self.DN_LARGE_FLAG})
        if not big:
            return ""
        return (
            "PIPE SIZES ABOVE DN1200 IN USE: " + ", ".join(f"DN{d}" for d in big) + ". "
            "These are sizes PAM-GUD-203 tabulates itself - p32 Table 13 and p35 Table 15 "
            "give service corridor widths for 1400-1700, 1800 and 2000-2400, and p30 Table "
            "12 gives chamber spacing for 'More than 1 400'. A guideline that tabulates a "
            "diameter contemplates it. NWS have NOT confirmed a stock list; the sizes are "
            "declared here and need their written confirmation.")

    # =========================================================================== registers
    @property
    def ASSUMPTIONS(self) -> Dict[str, Tuple]:
        """Every value in this file with no guideline page behind it. Reported verbatim on
        every deliverable - that is the whole purpose of keeping the register."""
        return {
            "TAU_PA": (self.TAU_PA,
                       "design tractive stress, Pa. G203-p27 sec 4.2.2.1 gives the equation "
                       "and NO numeric tau (GAP-9). 1.0 Pa is the Mara/Sleigh/Taylor "
                       "simplified-sewerage value. ENGINEER'S DECISION 2026-09-03: keep 1.0 "
                       "and flag it. At 2.0 Pa every tractive-governed gradient rises "
                       f"{self.TAU_SLOPE_FACTOR_AT_2PA:.3f}x. NWS to confirm."),
            "TRACTIVE_QMIN": (self.TRACTIVE_QMIN,
                              "1.5 L/s floor on Q in the tractive equation - Mara's own "
                              "minimum design flow for simplified sewerage, not a G203 "
                              "value. Unfloored, Smin -> infinity as Q -> 0 and the head of "
                              "every run demands an unbuildable gradient."),
            "WALL_ALLOW": (self.WALL_ALLOW,
                           "m of pipe wall plus bedding between the crown and the invert, "
                           "over and above the nominal diameter. G203-p33 gives cover to "
                           "crown and nothing about what is below it. THE ONLY COPY - "
                           "invert_depth_min() and cover() are the only two readers, and "
                           "contract.py imports them rather than repeating the arithmetic."),
            "PVC_WALL_CLASS": ("SDR34 / SN8",
                               "behind internal_diameter() for DN <= 315. Actual class per "
                               "PAM-SPC-207, pending. Affects capacity by about 6 % of "
                               "diameter on the small pipes."),
            "MAX_COVER": (self.MAX_COVER,
                          "m. G203-p33 RECOMMENDS 'approximately 10 - 12m' and triggers a "
                          "pumping station on excavation COST, not on depth. Taking the top "
                          "of the range as a hard cap is a project decision; philosophy "
                          "sec 5 gives it two bounded exits and flags every use."),
            "DROP_CEILING_M": (self.DROP_CEILING_M,
                               "m. G203-p30 sends a drop past 2 m to a vortex drop shaft and "
                               "gives NO maximum for one. Philosophy sec 5 requires a "
                               "declared ceiling so an over-cap exit can be withdrawn rather "
                               "than clipped. THIS VALUE IS CARRIED FROM W11a UNCHANGED FOR "
                               "COMPARABILITY AND IS NOT AN ENGINEERING JUDGEMENT THAT A "
                               "20 m SHAFT IS BUILDABLE. Needs the engineer's number."),
            "MIN_COVER_WADI_XING": (self.MIN_COVER_WADI_XING,
                                    "m to crown at a wadi crossing. The figure is G203-p52 "
                                    "sec 8.2.4, in the FORCE MAIN chapter, under the preamble "
                                    "'As for gravitational sewer'. Adopting it for gravity is "
                                    "OUR decision - conservative, and pending the scour-depth "
                                    "check that actually governs. G201-p86 raises it to 2.0 m "
                                    "in soft soil, for a force main."),
            "HAZARD_WADI_CLASSES": (self.HAZARD_WADI_CLASSES,
                                    "AR&R flood-hazard classes 4/5/6 of the 50-year grid "
                                    "standing in for G203's 'areas subject to washout', which "
                                    "is a SCOUR criterion. A proxy, and a project assumption. "
                                    "THE ONLY DECLARATION IN W12: w12.hazard reads this "
                                    "field and no longer keeps its own DEFAULT_SCOUR_CLASS. "
                                    "The stated reason 'class 4 is about 1.2 m of water' is "
                                    "RETRACTED - see RETRACTED['HAZARD_CLASS4_IS_1P2M'] - "
                                    "the threshold stands on the danger-to-people scale, not "
                                    "on a depth. NWS to supply the scour criterion they "
                                    "intend (a velocity, a bed shear, or a mapped corridor)."),
            "HAZARD_CHANNEL_MIN_CLASS": (self.HAZARD_CHANNEL_MIN_CLASS,
                                    "H3+ is read as 'in the running channel' - the shallowest "
                                    "class whose trigger is unambiguously depth (d > 0.5 m in "
                                    "the client's rasscript). Distinct from the washout "
                                    "threshold above and declared once, here. No guideline "
                                    "defines a channel edge."),
            "HAZARD_NODATA_IS_DRY": (self.HAZARD_NODATA_IS_DRY,
                                     "ENGINEER'S DECISION 2026-09-03: no-data on the flood "
                                     "grid is dry high ground, not 'untested'. Report the "
                                     "covered fraction beside every wadi result regardless."),
            "WADI_XING_SKEW_DEG": (self.WADI_XING_SKEW_DEG,
                                   "deg off square a crossing may be. H1 says 'perpendicular'; "
                                   "the tolerance on that word is a project rule."),
            "DUAL_XING_MAX_M": (self.DUAL_XING_MAX_M,
                                "m, longest perpendicular crossing of a dual carriageway."),
            "SLOPE_STEP": (self.SLOPE_STEP,
                           "pipes are laid on round 0.05 % steps so the number on the drawing "
                           "is the number the levels came from (user 2026-08-23). Measured "
                           "cost in W8: 1.0 % more excavation, 0.12 m on the deepest chamber, "
                           "no extra station, distinct gradients down from 448 to 103. "
                           "NEVER bought at the price of a pumping station (philosophy P1)."),
            "FALL_TOLERANCE_M": (self.FALL_TOLERANCE_M,
                                 "two ends at G203-p29's 20 mm each. The guideline states the "
                                 "per-point tolerance, not how two compose over one reach."),
            "MH_SNAP_M": (self.MH_SNAP_M,
                          "m. No minimum chamber spacing exists in G201/G202/G203 - "
                          "searched. 3 m is a physical-size convention, and it is also "
                          "the node-merge radius, so the graph cannot hold two chambers "
                          "a contractor would build as one. ONE FIELD: MH_MIN_CLEAR_M is "
                          "now a read-only property returning this, not a second constant."),
            "MH_ROUND_STEP": (self.MH_ROUND_STEP,
                              "round chamber spacing to 10 m (5 m fallback) rather than exact "
                              "equal division - user rule 2026-08-18."),
            "FANOUT_OFFSET_M": (self.FANOUT_OFFSET_M,
                                "a branch leaving a chamber that already has an outlet starts "
                                "10 m away, or at the next house connection - layout "
                                "convention, user rule 2026-08-18."),
            "MH_SPLIT_LEN": (self.MH_SPLIT_LEN,
                             "m working split length. Satisfies every G203-p30 Table 12 band, "
                             "so a reach laid at it cannot breach the table whatever diameter "
                             "it finishes at."),
            "LATERAL_MAX_LEN": (self.LATERAL_MAX_LEN,
                                "m on riders AND laterals. G203-p22 Table 6 puts the 45 m on "
                                "the lateral row only; G203-p17 sec 3.2 attaches it to both. "
                                "The conservative reading is a declared project cap."),
            "OCCUPANCY": (self.OCCUPANCY,
                          "people per property, DERIVED 2026-08-30 from settlement population "
                          "over counted domestic electricity accounts. No guideline gives it. "
                          "Supersedes 5.0 (client team) and 6.0 (W1-W4)."),
            "WWG_LCD": (self.WWG_LCD,
                        "l/c/d area-average wastewater generation including the Tier-A "
                        "non-domestic (+22 %) and governmental (+14 %) uplift on the G201 "
                        "Table 11 domestic LPCD. DERIVED; the load-allocation doctrine is "
                        "fixed in PROJECT-STATE sec 2 and TUTORIALS/T01 - do not re-derive it."),
            "INFILT_UNPEAKED": (self.INFILT_UNPEAKED,
                                "infiltration is added AFTER the sanitary peak factor. G201 "
                                "does not state the order; a steady ingress does not peak "
                                "with diurnal use. Confirm at kickoff."),
            "MANNING_N_EXPORT": (self.MANNING_N_EXPORT,
                                 "n for the SewerGEMS referee model. G203-p23 Table 8 gives "
                                 "0.009-0.011 for the plastics; 0.013 is the n behind G203's "
                                 "OWN tractive derivation (p27), so the referee and the "
                                 "tractive check share an assumption."),
            "ADVERSE_MIN_M": (self.ADVERSE_MIN_M,
                              "m of ground rise below which a reach is NOT counted as "
                              "draining against the grade. On a 20 m reach a 0.05 m rise is "
                              "DEM noise, and the against-grade share is the headline number "
                              "this whole iteration turns on."),
            "PS_MIN_FLOW_INTERP": ("log10", "G203-p40 Table 16 tabulates four points and "
                                   "fits nothing. Interpolating linearly in log10(Q) between "
                                   "them is a method choice."),
            "INLET_MIN_DEG_NO_RELAXATION": (self.INLET_MIN_DEG,
                                            "G203-p30 is a 'shall'. W8's 85 deg working "
                                            "tolerance is NOT carried into W12: a sharp "
                                            "inlet is resolved with a purpose-made swept "
                                            "channel, which is a priced item, not by a softer "
                                            "number. Expect the flagged count to rise."),
        }

    @property
    def CONFLICTS(self) -> Dict[str, str]:
        """Places where the guidelines contradict themselves or each other, and what W12
        does about it. A conflict recorded is a conflict the reviewer can overturn; a
        conflict silently resolved is one nobody can find."""
        return {
            "PC sewer minimum size":
                "G203-p18 Table 4 says the Property Connection Sewer is '150 mm (minimal)'; "
                "G203-p22 Table 6 says the Rider and PC Sewer are 'OD 160 mm (minimal)'. "
                "Same document, two numbers. W12 takes OD160 - Table 6 is the later table "
                "and is explicitly OD-designated.",
            "Trunk main run length":
                "G203-p35 sec 5 reads 'Length above 1,000 mm without connexions'. 1,000 mm "
                "is one metre and cannot be meant; it is read as 1,000 m. Flagged rather "
                "than silently corrected.",
            "Pump design life":
                "G203-p38 gives non-structural mechanical installations 20 years; G203-p40 "
                "Table 17 gives pumps a 'Service rating: 15 years design life'. The 15-year "
                "figure is pump-specific and governs pump renewal in a life-cycle cost. Both "
                "are carried (PS_SERVICE_LIFE_YR = 15).",
            "PVC-U upper size":
                "G203-p23 Table 7 permits U-PVC as a PRODUCT to OD315; G203-p22 Table 6 "
                "permits it on a MAIN SEWER only '(up to 250 mm)'. The tables answer "
                "different questions and both are in force - materials_allowed() takes the "
                "tier so it can honour both.",
            "Trunk threshold vs trunk material threshold":
                "G203-p35 sec 5 defines a trunk main at 'Diameter above 800 mm'; G203-p35 "
                "Table 14 keys the trunk MATERIAL list to '> 600 mm'. Two thresholds in one "
                "page. Both are stored (DN_TRUNK_MIN 800, DN_TRUNK_MATERIAL_MIN 600).",
            "Wadi cover for a gravity sewer":
                "There is none in the gravity chapter. The 1.5 m is G203-p52 sec 8.2.4 in the "
                "FORCE MAIN chapter, under the preamble 'As for gravitational sewer'. Adopted "
                "for gravity as a project decision, so a gravity reach at 1.30 m over a "
                "crossing is short of OUR rule and not of the guideline's.",
            "Two K values for one tractive constant":
                "G203-p27 sec 4.2.2.1 prints BOTH 'Q = Flow (m3/s) and K = 2.33 x 10-4' and "
                "'Q = Flow (L/s) and K = 5.5 x 10-3' for the same K in "
                "Smin = K tau^1.23 Q^-0.461. They are not the same constant in two units: "
                "converting, K_LS must be K_M3S x 1000^0.461 = 5.628e-3, and the guideline "
                "prints 5.5e-3. MEASURED 2026-09-03: the printed pair is 2.27 % apart, so "
                "working in L/s returns gradients 2.27 % flatter than working in m3/s on "
                "the same flow. It is source rounding (3 significant figures against 2), "
                "not an error of ours. W12 works consistently in m3/s with TRACTIVE_K_M3S; "
                "TRACTIVE_K_LS is kept ONLY as the cross-check that catches a mistyped K, "
                "and hydra.py's self-test asserts the 2.27 %. It is the one place this file "
                "holds two constants for one quantity, it is deliberate, and it is tested.",
            "Table 11 vs the tertiary slopes":
                "Table 11 (p29) gives 0.5 % at DN200 for the SECONDARY network. G203-p18 "
                "Table 5 gives a lateral 1 % minimum and a property connection 3 %. Applying "
                "Table 11 to a tertiary pipe is a fivefold error - table11() raises below "
                "DN200 rather than extrapolating into it.",
        }

    @property
    def BENCHMARKS(self) -> Dict[str, Tuple]:
        """MEASURED reference values. A benchmark is a calibration reference and NEVER a
        limit. They exist so a design that is nothing like the network next door announces
        itself, which is the failure the terrain-first rebuild is answering."""
        return {
            "VORTEX_BUILT": (37, "vortex-height drops (> 2 m) in NAMA's built Ibri network. "
                             "W11a's design wanted 2,449 (00_CURRENT) / 2,254 (philosophy "
                             "sec 4) - the two live documents disagree, and the discrepancy "
                             "is itself a finding. Either way the ratio is two orders of "
                             "magnitude and it is the diagnostic for a tree that is not "
                             "following the ground."),
            "UPHILL_SHARE_W11A": (0.425, "share of W11a's 1,731.7 km draining against the "
                                  "ground - 737.7 km. THE DEFECT W12 EXISTS TO FIX. W12 "
                                  "must publish its own value beside this one."),
            "CLIMB_W11A_M": (7061.0, "m of cumulative climb along W11a's flow paths, against "
                             "10,177 m of descent."),
            "NODES_PER_KM_BUILT": (32.3, "chambers per km in the built network; W10 ran 11.1. "
                                   "A design far below it has not been chambered."),
            "TIER_SHARE_BUILT": ((0.66, 0.18, 0.05), "lateral / sub main / trunk share of "
                                 "length in the as-built (philosophy sec 4)."),
            # --- laid gradient. RE-MEASURED 2026-09-03; the old single figure is retracted,
            # --- see RETRACTED["GRADIENT_BUILT_MM_M"]. Three named statistics of ONE
            # --- dataset, because the distribution is skewed (median 6.00, mean 8.89,
            # --- max 160.9) and a benchmark called only "the built gradient" invites the
            # --- reader to compare a median against a mean, which is how 4.98 survived.
            "GRADIENT_BUILT_MEDIAN_MM_M": (
                6.00,
                "MEDIAN laid gradient, mm/m, over the 2,142 built pipes that carry a "
                "recorded US and DS invert - 63.20 km of the 95.45 km of built gravity "
                "pipe. Source: SEWERLINE_IBRI.shp, STATUS == 'Ex', the two schematic "
                "force-main rows (>100 m per vertex) removed, US_INVERT_/DS_INVERT_ both "
                "present and positive, gradient = 1000*(US-DS)/geometry length. Measured "
                "2026-09-03 in this session, and it reproduces W11a's independent 6.00 in "
                "EXISTING_NETWORK_ASSESSMENT.md sec 6. THE REFERENCE STATISTIC - use this "
                "one when comparing a design's typical laid gradient."),
            "GRADIENT_BUILT_MEAN_MM_M": (
                8.89,
                "MEAN of the same 2,142 reaches, mm/m. 48 % above the median because the "
                "distribution has a long steep tail (p95 = 25.4, max = 160.9 mm/m) - the "
                "built network takes the ground where the ground is steep. Quote the mean "
                "only against another mean."),
            "GRADIENT_BUILT_LENGTHWEIGHTED_MM_M": (
                8.69,
                "LENGTH-WEIGHTED mean of the same 2,142 reaches, mm/m - the fall per metre "
                "the network actually delivers over its 63.20 km. Between the mean and the "
                "median, which says the steep reaches are not systematically the short "
                "ones. By pipe size: OD160 (58.67 km) 8.93 mm/m, OD200 (4.53 km) 5.57."),
            "GRADIENT_BUILT_ADVERSE_N": (
                0,
                "built reaches laid against the flow (US invert below DS invert): ZERO of "
                "2,142, with 5 laid exactly flat. G203-p29 sec 4.3.1 forbids a reverse "
                "gradient and NAMA have none. A design with reverse-gradient reaches is "
                "not doing something the built network does."),
            "ASBUILT_KM_GRAVITY": (
                95.45,
                "km of BUILT gravity pipe: SEWERLINE_IBRI.shp STATUS == 'Ex' is 111.57 km, "
                "less the 16.12 km in two schematic rows (L012750, L012751 - the force main "
                "drawn into the gravity layer at 308 and 513 m per vertex). The other "
                "202.71 km in the file is STATUS == 'Design', the unapproved SUREKHA "
                "concept. FILTER STATUS BEFORE QUOTING ANY LENGTH."),
            "ASBUILT_KM_LEVELLED": (
                63.20,
                "km of built pipe carrying inverts, 65.6 % of the 95.45 km. The split is by "
                "package - 5A-2/3/4/5 complete, 5A-1 none - so every level-derived benchmark "
                "here describes 5A-2/3/4/5 and not the whole built network."),
            "DUAL_SHARE_BUILT": (0.001, "share of the built network running along a dual "
                                 "carriageway - 0.1 %. The exclusion rule is not ours; it is "
                                 "what NAMA already do."),
        }

    @property
    def RETRACTED(self) -> Dict[str, Tuple]:
        """Numbers this file used to state that DO NOT HOLD, with what replaced them.

        The file that is the only source of design numbers is also the only sensible place
        to record which numbers must never be quoted again. This project has withdrawn
        eight confident figures in two days; a withdrawal that lives only in a session
        transcript is a figure that comes back.

        Each entry: (retracted value, what is true instead, why the old one was wrong).
        """
        return {
            "GRADIENT_BUILT_MM_M": (
                4.98,
                "median 6.00 mm/m (mean 8.89, length-weighted 8.69) over 2,142 levelled "
                "built reaches, 63.20 km - see BENCHMARKS.",
                "THREE errors in one constant. (1) WRONG DATASET: 4.98 came from "
                "W7/docs/CALIBRATION_vs_EXISTING.md, computed over SEWERLINE.kmz's 3,322 "
                "features / 188.6 km, which is 111.6 km of built pipe MIXED WITH 77.0 km of "
                "the unapproved SUREKHA concept - and the KMZ conversion had already lost "
                "74 features of that concept. (2) WRONG STATISTIC NAME: W7's own table "
                "calls 4.98 a MEDIAN; the note in this file called it a MEAN. (3) NOT "
                "REPRODUCIBLE: re-measured 2026-09-03 on SEWERLINE_IBRI.shp with STATUS "
                "filtered to 'Ex' and the two schematic rows removed, no subset returns "
                "4.98 - not the signed mean (8.889), median (6.001), length-weighted "
                "(8.690), the OD200-only mean (5.594) or median (5.187), the mean with "
                "unlevelled reaches counted as zero (5.832), or the mean GROUND slope "
                "(4.625). W11a reached the same conclusion independently "
                "(EXISTING_NETWORK_ASSESSMENT.md sec 6: 'W7's figure could not be "
                "reproduced from any subset tried here'). "
                "AND THE CLAIM ATTACHED TO IT DID NOT HOLD EITHER: the note read 'against "
                "W8's 5.00 - the hydraulics calibrate'. Like for like, median against "
                "median, W8's design median of 5.00 mm/m sits 17 % FLATTER than the built "
                "6.00 - and 5.00 mm/m is also exactly the Table 11 DN200 minimum, so the "
                "design median is the floor rather than a laid gradient that happened to "
                "land near NAMA's. Whether the gap matters is an engineering question; "
                "reporting it as agreement was not an option."),
            "ASBUILT_KM_188_6": (
                188.6,
                "95.45 km of built gravity pipe (BENCHMARKS['ASBUILT_KM_GRAVITY']), of "
                "which 63.20 km carries inverts.",
                "The 188.6 km 'as-built' does not exist as a built network. It is the "
                "SEWERLINE.kmz total: 111.567 km built + 76.986 km of unapproved SUREKHA "
                "concept. Still quoted in CLAUDE.md, _BRAIN/00_CURRENT.md and "
                "W8/docs/LEARNING_FROM_ASBUILT.md - those documents are not W12's to "
                "edit, but nothing in W12 may cite the figure."),
            "HAZARD_CLASS4_IS_1P2M": (
                1.2,
                "H4's depth band is 0.300-2.000 m and is INDETERMINATE - H4 can be "
                "triggered by d*v > 0.6 at 0.3 m of water.",
                "'class 4 is about 1.2 m of water' was the stated reason for "
                "HAZARD_WADI_CLASSES = (4,5,6), here and in _BRAIN/02_DESIGN_CRITERIA.md "
                "sec 6. The client's own rasscript (Hazard_T100y.rasscript) disproves it: "
                "d > 1.2 is one of THREE routes into H4, and no AR&R class above H3 is a "
                "statement about depth at all. The threshold survives on the "
                "danger-to-people scale it was built on; the depth reason does not."),
        }


DEFAULT = Criteria()          # THE design basis. Stages take `crit=DEFAULT` as a keyword.


# ======================================================================================
# Self-test. `python -m w12.criteria` - proves the claims above rather than asserting them.
# ======================================================================================

def _self_test(verbose: bool = True) -> None:
    C = DEFAULT

    # --- the one wall allowance: cover() is the exact inverse of invert_depth_min()
    for dn in C.DN_SERIES + (160,):
        d = C.invert_depth_min(dn)
        assert abs(C.cover(dn, d) - C.MIN_COVER_CROWN) < 1e-12, dn
        # and there is no second allowance hiding anywhere: the round trip is exact
        assert abs(d - (C.MIN_COVER_CROWN + dn / 1000.0 + C.WALL_ALLOW)) < 1e-12, dn

    # --- d/D is diameter-dependent, at the exact G203-p27 Table 10 threshold
    assert C.dod_limit(315) == 0.65 and C.dod_limit(350) == 0.65      # "up to 350 mm"
    assert C.dod_limit(351) == 0.50 and C.dod_limit(400) == 0.50      # "> 350 mm"

    # --- the series carries the sizes G203 itself tabulates above DN1200
    for dn in (1400, 1700, 1800, 2000, 2400):
        assert dn in C.DN_SERIES, dn
    assert C.DN_SERIES == tuple(sorted(C.DN_SERIES)), "series must be ascending: size_pipe "\
        "returns the FIRST that works and relies on the order"

    # --- Table 11 never interpolates DOWN to a flatter gradient than the guideline prints
    assert C.table11(200) == 0.005 and C.table11(900) == 0.00075
    assert C.table11(1200) == C.TABLE11_FLOOR                 # "900 and above"
    assert C.table11(350) == C.table11(315)                   # next smaller, steeper
    try:
        C.table11(160)
    except CriteriaError:
        pass
    else:                                                     # pragma: no cover
        raise AssertionError("table11 must refuse a tertiary diameter")

    # --- materials honour BOTH G203-p22 Table 6 (application) and p23 Table 7 (product)
    assert "PVC-U" in C.materials_allowed("main", 250)
    assert "PVC-U" not in C.materials_allowed("main", 315), \
        "G203-p22 Table 6 permits PVC-U on a main sewer only up to 250 mm"
    assert "PVC-U" in C.materials_allowed("lateral", 315)
    assert C.material("trunk main", 1200) == "GRP"
    try:
        C.materials_allowed("submain", 300)                   # underscore/typo form
    except CriteriaError:
        pass
    else:                                                     # pragma: no cover
        raise AssertionError("an unrecognised tier must raise, never default")

    # --- G203-p30 Table 12 bands
    assert (C.mh_max_spacing(200), C.mh_max_spacing(315)) == (100.0, 100.0)
    assert (C.mh_max_spacing(350), C.mh_max_spacing(900)) == (120.0, 120.0)
    assert (C.mh_max_spacing(1000), C.mh_max_spacing(1400)) == (150.0, 150.0)
    assert C.mh_max_spacing(1700) == 200.0

    # --- G203-p40/43: type by duty flow, land by type
    assert (C.ps_type(100.0), C.ps_type(100.1), C.ps_type(301.0)) == (
        "Type 1", "Type 2", "Type 3")
    assert C.ps_land_m2("Type 3")[0] == 900.0

    # --- G203-p48 wet well, and the 10 starts/h floor bites
    assert abs(C.well_volume_m3(0.050, 10.0) - 0.25 * 0.050 * 360.0) < 1e-12
    try:
        C.well_volume_m3(0.050, 6.0)
    except CriteriaError:
        pass
    else:                                                     # pragma: no cover
        raise AssertionError("below 10 starts/h must raise (G203-p48)")

    # --- G201-p71: Merrimack is a mandatory formula above 100 properties, held below
    pf, meth = C.peak_factor(3000.0, 40)
    assert meth == "held" and pf == 1.0
    pf, meth = C.peak_factor(3000.0, 4000)
    assert meth == "merrimack" and 1.0 < pf < 6.0, (pf, meth)

    # --- the tau sensitivity is exact, because the equation is a power law in tau alone
    assert abs(C.TAU_SLOPE_FACTOR_AT_2PA - 2.0 ** 1.23) < 1e-12
    assert abs(C.TAU_SLOPE_FACTOR_AT_2PA - 2.3457) < 1e-3, C.TAU_SLOPE_FACTOR_AT_2PA

    # --- a sensitivity run is a NEW OBJECT
    tau2 = replace(C, TAU_PA=2.0)
    assert tau2.TAU_PA == 2.0 and C.TAU_PA == 1.0, "DEFAULT must be untouched"

    # --- gradient rounding lands on the step, and up/down do what they say
    for s in (0.00123, 0.005, 0.0201):
        up, dn_ = C.round_slope_up(s), C.round_slope_down(s)
        assert up >= s - 1e-15 and dn_ <= s + 1e-15
        for v in (up, dn_):
            assert abs(v / C.SLOPE_STEP - round(v / C.SLOPE_STEP)) < 1e-9, v

    # --- infiltration is per-km and unpeaked
    assert abs(C.infiltration_ls(1000.0) - 720.0 / 86400.0) < 1e-15

    # --- every register entry is non-empty; an empty assumption register is the worst state
    assert len(C.ASSUMPTIONS) >= 20 and len(C.CONFLICTS) >= 5 and len(C.BENCHMARKS) >= 5
    assert len(C.RETRACTED) >= 3, "the retraction register must not be emptied"

    # ---------------------------------------------------------------- DEFECT 3, proved here
    # The retracted gradient must not be reachable under any benchmark key, and the
    # replacements must be the three named statistics of ONE dataset, ordered as measured.
    assert "GRADIENT_BUILT_MM_M" not in C.BENCHMARKS, \
        "the ambiguous single gradient benchmark is retracted - see RETRACTED"
    med = C.BENCHMARKS["GRADIENT_BUILT_MEDIAN_MM_M"][0]
    mean = C.BENCHMARKS["GRADIENT_BUILT_MEAN_MM_M"][0]
    lw = C.BENCHMARKS["GRADIENT_BUILT_LENGTHWEIGHTED_MM_M"][0]
    assert med < lw < mean, (med, lw, mean)          # the measured skew, not an assumption
    assert 4.98 not in (med, mean, lw)
    assert C.RETRACTED["GRADIENT_BUILT_MM_M"][0] == 4.98
    # the two lengths are the ones the STATUS filter gives, and levelled is a subset
    assert C.BENCHMARKS["ASBUILT_KM_LEVELLED"][0] < C.BENCHMARKS["ASBUILT_KM_GRAVITY"][0]
    assert C.RETRACTED["ASBUILT_KM_188_6"][0] == 188.6

    # ---------------------------------------------------------------- DEFECT 4, proved here
    # (a) ONE clearance. MH_MIN_CLEAR_M is a property, so it cannot be set independently and
    #     it cannot drift away from MH_SNAP_M.
    assert C.MH_MIN_CLEAR_M == C.MH_SNAP_M
    assert "MH_MIN_CLEAR_M" not in {f for f in C.__dataclass_fields__}, \
        "MH_MIN_CLEAR_M must be a derived property, not a second field"
    tight = replace(C, MH_SNAP_M=2.0)
    assert tight.MH_MIN_CLEAR_M == 2.0, "the alias must follow the one field it aliases"
    try:
        replace(C, MH_MIN_CLEAR_M=2.0)
    except TypeError:
        pass
    else:                                                     # pragma: no cover
        raise AssertionError("setting the alias must raise, not create a second value")

    # (b) the flood-grid thresholds are declared HERE and nowhere else in W12. hazard.py is
    #     expected to import them; if it has grown its own copy again, this fails.
    assert min(C.HAZARD_WADI_CLASSES) > C.HAZARD_CHANNEL_MIN_CLASS, \
        "washout ground must be a strict subset of channel ground, or the two thresholds " \
        "are answering the same question and one of them is redundant"
    try:
        from w12 import hazard as _hz                        # sibling, no cycle
    except Exception:                                          # pragma: no cover
        _hz = None
    if _hz is not None:
        for name in ("DEFAULT_SCOUR_CLASS", "DEFAULT_CHANNEL_CLASS"):
            assert not hasattr(_hz, name), (
                f"w12.hazard has re-declared {name}. The flood-grid thresholds have ONE "
                "declaration, in criteria.HAZARD_WADI_CLASSES / HAZARD_CHANNEL_MIN_CLASS.")
        assert _hz.scour_min_class(C) == min(C.HAZARD_WADI_CLASSES)
        assert _hz.channel_min_class(C) == C.HAZARD_CHANNEL_MIN_CLASS
        assert _hz.governing("pipe_washout").return_periods == (C.HAZARD_RETURN_YR,)

    # (c) the ONE deliberate pair, and the gap that justifies keeping it, are both asserted
    ratio = C.TRACTIVE_K_LS / (C.TRACTIVE_K_M3S * 1000.0 ** 0.461)
    assert 0.97 < ratio < 1.0, ratio
    assert "Two K values for one tractive constant" in C.CONFLICTS

    if verbose:
        print(f"{CRITERIA_VERSION}: self-test PASSED")
        print(f"  {len(C.ASSUMPTIONS)} assumptions, {len(C.CONFLICTS)} guideline conflicts, "
              f"{len(C.BENCHMARKS)} measured benchmarks, {len(C.RETRACTED)} retractions")
        print(f"  built gradient, re-measured: median {med:.2f}  length-weighted {lw:.2f}  "
              f"mean {mean:.2f} mm/m  (4.98 retracted)")
        print(f"  G203-p27's two K values are {(1 - ratio) * 100:.2f} % apart - registered")
        print("  " + C.tau_banner())


if __name__ == "__main__":          # pragma: no cover
    _self_test()
