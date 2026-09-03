"""w11b.pumping - PUMPING STATIONS AND FORCE MAINS, DESIGNED.

W11b BORROWS NOTHING (engineer's instruction, 2026-09-03). Nothing here imports from
`W8/py/sewnet`, `W10/py` or `W11a/py`. Every guideline number below was read out of the
source PDF in `Data/` on 2026-09-03 during this session and is quoted beside its page.

WHY THIS FILE EXISTS
    W11a published 226 stations with `Q_DUTY_LS = 0` on every one, no rising mains at all,
    and `LAND_M2` a flat 100 m2 constant. That is a located station, not a designed one. A
    survey of 839 sewer repositories found nothing that sizes a wet well, picks a pump
    against a system curve or designs a force main - there is no upstream source to borrow
    from, so this is built from PAM-GUD-201/202/203 directly.

WHAT IT DOES, AND THE CLAUSE BEHIND EACH STEP
    duty flow ................ G203-p39 sec 7.4 (a)-(f), Table 16 (p40)
    station type ............. G203-p40, verbatim: Type 1 <= 100 l/s, Type 2 > 100 to 300,
                               Type 3 > 300. Duty/standby counts G203-p40 Table 17
    wet well ................. G203-p48 sec 7.8: V = 0.25 Q T, T = 3600 / starts per hour,
                               minimum 10 starts/h to 30 kW; level separation 200-300 mm;
                               CFD above 0.5 m3/s
    pump selection ........... against a SYSTEM CURVE. G202-p91 sec 6.3.2, verbatim: "The
                               point of intersection between the system curve and the pump
                               curve is to be considered as the operating point during
                               design." G201-p133 glossary defines the duty point the same
                               way. Motor margin G202-p96
    NPSH ..................... G203-p47 sec 7.6: NPSHa = Ha - Hvpa - Hst - Hf, margin >= 1 m
    force main ............... G203-p50 sec 8.1: 0.75 m/s at DESIGN MINIMUM flow, 1.0 m/s
                               intermittent, 1.2 m/s vertical, MAXIMUM 2.5 m/s. Friction
                               roughness from G202-p104 Table 21, which G203-p50 itself
                               points to ("Refer to Section 7.1.3.2 of PAM-GUD-202")
    siting ................... G203-p38 sec 7.2 - AND SEE THE CITATION DEFECT BELOW
    wadi crossing ............ G201-p85-86 sec 9.3, in full, as a register
    economics ................ G201-p95-96 sec 12: 25 years, 5 % discount unless NWS say
                               otherwise; OPEX must include labour

THREE CITATION DEFECTS FOUND WHILE WRITING THIS, ALL AGAINST THE SOURCE PDF
    (1) `_BRAIN/08_DESIGN_PHILOSOPHY.md` sec 3, flood table, says a pumping station's floor
        and electrical plant sit above the **1:100** level, cited to G203-p38 sec 7.2. THE
        CLAUSE SAYS 1:50. Read out of the PDF, verbatim: "Pump pedestal level or building
        floor, electrical transformers/ pad mounted substation or emergency generator are to
        be located above maximum flood level, with the floors being a minimum of 300 mm
        above the 1:50 year flood level." The only 100-year mention anywhere in G203 is
        p63 Table 27 row (i), which is STP SITE SELECTION, not a pumping station. W11b's
        `criteria.PS_FLOOD_ARI_YR = 50` and `hazard._DUTIES['pumping_station']` are both
        right; the philosophy document is wrong and must be corrected. This module designs
        to 1:50 and reports 1:100 as a supplementary sensitivity, never as the duty.
    (2) The floor test CANNOT BE EVALUATED at all. G203-p38 wants 300 mm above a flood
        LEVEL; the project holds AR&R hazard-CLASS grids and no water surface. See
        `hazard.flood_level_m_aod`, which raises rather than inventing one. What this module
        can answer is the siting question - is the footprint wet at 1:50, and how far is dry
        ground - and it says so on every station rather than reporting a pass.
    (3) There is NO WET-WELL RETENTION-TIME LIMIT anywhere in PAM-GUD-201, -202 or -203.
        Searched all three, every page, for retention / detention / septic. What exists is:
        the FORCE MAIN retention "no longer than half an hour" (G203-p50 sec 8.2.1); the
        starts-per-hour rule, which bounds the wet-well cycle to T = 3600/starts and nothing
        else (G203-p48); and G203-p47 sec 7.7, which names "long retention times, septic
        conditions" as the H2S trigger and gives no number. So the septicity limit the brief
        asked for does not exist as a guideline value. This module COMPUTES the wet-well
        retention at design minimum inflow and reports it against the 30-minute force-main
        figure as a DECLARED PROJECT COMPARATOR (`WELL_RETENTION_COMPARATOR_MIN`), flagged
        on every row. It is not a quotation and it is a live data request.

WHAT THIS FILE IS NOT
    No file I/O, no geometry files, no layer names, no paths. Those are `s7_pumps.py`. It
    reads `w11b.criteria` for every value that file already holds, and declares here - with
    its page - only what criteria does not yet carry. Those belong in criteria.py; this
    module does not own that file and says so in `TO_MIGRATE`.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

from . import hydra
from .criteria import DEFAULT, Criteria, CriteriaError, replace

PUMPING_VERSION = "W11b-pumping-1.0"


class PumpingError(Exception):
    """Raised when a station or a main cannot be designed to the guideline. NEVER returns a
    plausible-looking number instead: W11a's `Q_DUTY_LS = 0` on 226 rows is what a silent
    default looks like six months later."""


# ======================================================================================
# 1. THE NUMBERS THIS MODULE ADDS - what `criteria.py` does not yet carry
# ======================================================================================

@dataclass(frozen=True)
class PumpCriteria:
    """Pumping and force-main values with no home in `criteria.py` yet.

    Frozen, like `Criteria`, so a sensitivity run is a new object and never an edit:

        from w11b.pumping import PUMP, replace
        cheap = replace(PUMP, TARIFF_OMR_KWH=0.010)

    EVERY field is either (a) quoted from a guideline page read on 2026-09-03, or (b) in
    `ASSUMPTIONS` below with what it would take to retire it.
    """

    # ---------------------------------------------------------------- friction, force main
    # G203-p50 sec 8.1 ends: "Refer to Section 7.1.3.2 of PAM-GUD-202 Water and TSE
    # Guidelines." That section is G202-p104 Table 21, "Typical head loss coefficient for
    # Darcy-Weisbach (D-W) & Hazen-Williams (H-W)", tabulated by material AND PIPE AGE.
    # Values below are the D-W absolute roughness epsilon in METRES, read from that table.
    #
    # THIS IS NOT criteria.KS. criteria.KS = 1.5 mm is the GRAVITY sewer roughness, G203-p24
    # sec 4.2.1 / p28 sec 4.2.4 ("using a k_s value of 1.5 mm for all pipe sizes"). Using it
    # on a ductile-iron rising main overstates friction by a factor of three to six. The two
    # are different clauses about different pipes and they must not be conflated - the same
    # class of error as the 2.5 / 3.0 m/s velocity conflation this project has already made.
    FM_EPS_M: Dict[Tuple[str, int], float] = field(default_factory=lambda: {
        # (material, pipe age in years) -> epsilon, m.  G202-p104 Table 21.
        ("DI", 0): 0.00026, ("DI", 5): 0.00030, ("DI", 10): 0.00035,
        ("DI", 15): 0.00040, ("DI", 20): 0.00045,
        ("HDPE", 0): 0.000007, ("HDPE", 5): 0.000007, ("HDPE", 10): 0.000007,
        ("HDPE", 15): 0.000007, ("HDPE", 20): 0.000007,
        ("SS", 0): 0.00015, ("SS", 5): 0.00018, ("SS", 10): 0.00021,
        ("SS", 15): 0.00024, ("SS", 20): 0.00028,     # G202 row "Steel"
        ("GRP", 0): 0.000005, ("GRP", 20): 0.000005,
        ("PVC-U", 0): 0.0000015, ("PVC-U", 20): 0.0000015,
    })
    FM_DESIGN_AGE_YR: int = 20        # ASSUMPTION - which row of G202-p104 Table 21 governs.
                                      # The table runs 0 to 20 years; the design horizon is
                                      # 25 years (G201-p96) so the AGED row is the design
                                      # case and the t=0 row is the max-velocity check. The
                                      # table's own note raises epsilon 30 % for TSE; that
                                      # note is for TREATED EFFLUENT and is NOT applied here.
    FM_TEMP_C: float = 15.0           # G203-p25 Table 9 is stated at 15 C and criteria.NU
                                      # (1.141e-6 m2/s) is that row. Held so this module and
                                      # the gravity hydraulics use ONE viscosity.

    # ------------------------------------------------------------------ force-main sizes
    # G203 gives NO force-main size series. It gives one hard floor: G203-p50 sec 8.1, "A
    # force main shall be a minimum 75 mm inside diameter for non-clog pumps and minimum 50
    # mm inside diameter for grinder pumps" (criteria.FM_ID_MIN_MM / FM_ID_MIN_GRINDER_MM).
    # The series below is the EN 545 ductile-iron preferred range - an ASSUMPTION about
    # procurement, not a guideline value.
    FM_DN_SERIES: Tuple[int, ...] = (80, 100, 150, 200, 250, 300, 350, 400, 450, 500,
                                     600, 700, 800, 900, 1000, 1200)
    DI_ID_EQUALS_DN: bool = True      # ASSUMPTION - EN 545 designates ductile iron by its
                                      # NOMINAL BORE, so ID ~ DN. Actual bore is the
                                      # manufacturer's; PAM-SPC-207 pending (GAP, same one
                                      # that holds up the plastic wall class).
    HDPE_SDR: float = 17.0            # ASSUMPTION - PN10. ID = OD (1 - 2/SDR). The pressure
                                      # class is a PAM-SPC-207 question and is OPEN; at
                                      # SDR11 (PN16) the same OD loses 8 % of its bore and
                                      # ~40 % more friction head.

    # ------------------------------------------------------------------- minor losses
    # NO GUIDELINE GIVES A LOSS COEFFICIENT. Searched G201, G202, G203 for "minor loss",
    # "local loss", "singular loss": G201-p140 requires a model to carry a "minor loss
    # factor" and none of the three supplies one. Both numbers below are ASSUMPTIONS, and
    # they are stated as a fitting schedule rather than a fudge so a reviewer can price them.
    SUM_K_STATION: float = 8.0        # ASSUMPTION - station internal pipework, sum of K:
                                      # bellmouth/entry 0.5, two 90 bends 2 x 0.3, tee
                                      # branch 1.0, non-return valve 2.0 (G203-p42 Table 19
                                      # requires an NRV), isolation valve 0.2, discharge
                                      # header tee 1.0, exit 1.0, contingency 1.7.
    MINOR_LOSS_FRAC: float = 0.10     # ASSUMPTION - bends, air valves and washouts along the
                                      # main, as a fraction of its friction head. G203-p51
                                      # sec 8.2.2 requires straight lines and pre-formed
                                      # anchored bends, so the fitting count is low.

    # --------------------------------------------------------------------- the pump itself
    SHUTOFF_RATIO: float = 1.30       # ASSUMPTION - closed-valve head / duty head for a
                                      # non-clog sewage impeller. G202-p96 requires the motor
                                      # to run the pump "in any point on the pump curve", so
                                      # a shutoff head is needed and no guideline gives one.
                                      # The curve is modelled H(Q) = H0 - a Q^2 (two-point
                                      # fit). A manufacturer curve REPLACES this; the field
                                      # exists so the substitution is one line.
    ETA_PUMP: float = 0.72            # ASSUMPTION - wire-to-water hydraulic efficiency of a
                                      # non-clog sewage pump near BEP. G202-p93 sec 6.4.1
                                      # makes efficiency "the main criteria" for selection
                                      # and gives no value; G203 gives none either.
    ETA_MOTOR: float = 0.92           # ASSUMPTION - IE3 induction motor, 4-pole. G202-p96
                                      # asks for "class F with a service factor of 1.1" and
                                      # names no efficiency.
    MOTOR_MARGIN: float = 0.10        # G202-p96, verbatim: "Motor capacity shall have run
                                      # off power demand of the pump, sufficient margin min
                                      # 10% over the maximum operating point."
    MOTOR_SERVICE_FACTOR: float = 1.15  # G202-p96: "overloading service factor minimum of
                                      # 1.15%" - the % sign is a typo in the source; 1.15 is
                                      # the standard NEMA service factor. Flagged in CONFLICTS.
    MOTOR_RPM_PREFERRED: float = 1500.0  # G202-p96: "Prefer a motor running 1500 rpm rather
                                      # than 3000 rpm to maximize longevity and reliability."
                                      # G203-p41 caps pump motor speed at 1450 rpm above
                                      # 5 l/s - see CONFLICTS.

    # --------------------------------------------------------------------------- NPSH
    NPSH_MARGIN_M: float = 1.0        # G203-p47 sec 7.6: "NPSH margin of at least 1 meter
                                      # should be considered for the pump." G202-p92 repeats
                                      # it: "the available NPSH must always be greater than
                                      # the required NPSH of at least 1 m ... In the worst-
                                      # case operation."
    # NPSHR_FRACTION IS RETRACTED (2026-09-03, inside the session that wrote this file).
    # It guessed NPSHr as 25 % of DUTY HEAD. NPSHr scales with flow and speed, NOT with
    # system head, so on the as-built calibration case - 10 km of main, 98 m of head - it
    # produced a "-13.03 m NPSH margin", which is not a fact about any pump. `select_pump()`
    # now publishes the PROCUREMENT LIMIT, NPSHR_MAX = NPSHa - the 1 m G203-p47 margin, and
    # leaves the check UNANSWERED until a manufacturer's curve is quoted. The field is kept
    # as NaN so a reader who meets the name in an older output finds the withdrawal here.
    NPSHR_FRACTION: float = float("nan")
    VAPOUR_PRESSURE_M: float = 0.174  # m of water at 15 C (1.706 kPa). A PHYSICAL PROPERTY
                                      # (steam tables), not a design value; 35 C is 0.585 m.
                                      # G203 gives no sewage design temperature and 15 C is
                                      # what G203-p25 Table 9 states its viscosity at, so the
                                      # force main and the gravity sewers share one.

    # ------------------------------------------------------------ wet well and septicity
    WELL_RETENTION_COMPARATOR_MIN: float = 30.0
    # DECLARED PROJECT COMPARATOR, NOT A GUIDELINE LIMIT. See module docstring defect (3):
    # no wet-well retention limit exists in G201/G202/G203. 30 minutes is G203-p50 sec 8.2.1's
    # FORCE MAIN figure ("short enough to produce a retention period no longer than half an
    # hour"), adopted here as the comparator for the wet well because it is the only
    # retention number the guideline set contains and it is about the same sewage in the same
    # anaerobic condition. Every station reports its retention AND this flag.
    WELL_PLAN_MIN_DIA_M: float = 2.0  # ASSUMPTION - smallest practical wet-well internal
                                      # diameter. G203-p42 Table 19 requires "At least 1 m
                                      # clear access around pumps" in a dry well and gives no
                                      # wet-well dimension; G203-p48 sec 7.8 (a) says only
                                      # "adequate for accommodating pump and piping".
    WELL_FREEBOARD_M: float = 0.50    # ASSUMPTION - between top water level and cover slab.
                                      # G203-p47 sec 7.5 requires emergency storage "above
                                      # the start level for the last duty pump"; it gives no
                                      # depth, so this is a project allowance, reported.

    # ------------------------------------------------------------------------- economics
    # G201-p96 sec 12.4: "For the purposes of comparing alternatives, the period used is
    # 25 years"; "Unless otherwise instructed by NWS, the discount rate to be applied is 5%."
    # G201-p95 sec 12 repeats the 25-year horizon. Both are GUIDELINE.
    LCC_YEARS: int = 25
    DISCOUNT: float = 0.05
    # G201-p96 sec 12.3 requires OPEX to include "Labour and staffing costs" and "Power and
    # utility consumption (based on the latest APSR tariff)" and names no rate. The three
    # rates below come from NWS's OWN PIAD investment appraisals, read end to end and
    # recorded in `W9/analysis/W9_PIAD_financial_review.md` sec 2.2. They are NWS PRACTICE,
    # not guideline values, and they are the most decision-relevant numbers in this file.
    MANNING_OMR_YR: float = 12000.0   # NWS PIAD: 1,000 OMR/month PER PUMPING STATION.
    TARIFF_OMR_KWH: float = 0.020     # NWS PIAD range 0.010-0.030; 0.020 adopted.
    ME_OM_FRAC: float = 0.02          # NWS PIAD: M&E O&M + insurance, 2.0 %/yr of ...
    ME_SHARE_OF_CAPITAL: float = 0.45 # ... 45 % of station capital (the M&E share).
    # Station capital: Cabral et al., fitted over 360 Portuguese stations.
    #   C_cap (k EUR) = exp(4.3184) * P^0.5329,  P = 9.81 * Q_peak(m3/s) * H(m)  [kW]
    # ASSUMPTION and NON-OMANI. Renardet's own priced BoQs are the pending replacement (see
    # 00_CURRENT "Still open"). Until they land every absolute OMR figure here is indicative.
    CABRAL_A: float = 4.3184
    CABRAL_B: float = 0.5329
    EUR_TO_OMR: float = 0.42
    RM_OMR_PER_M_DN200: float = 152.0 # ASSUMPTION - rising main all-in rate, DN200. Central
                                      # Coast Council (NSW) DSP 2019/20 Appendix I gives
                                      # 459 AUD/m; x 0.265 OMR/AUD x 1.25 escalation to the
                                      # tender date = 152 OMR/m. Used ONLY for the
                                      # consolidation break-even, and the break-even is
                                      # reported as a LENGTH so the rate can be swapped.
    # G203-p50 requires "A cost comparison ... to determine which pressure main size will
    # result in the optimum whole life cost of the pressure main and associated pumping
    # costs." That needs a rate PER SIZE, and no Omani rate set exists on this project yet.
    # Same source as above, same conversion (x 0.265 OMR/AUD x 1.25): Central Coast Council
    # (NSW) DSP 2019/20 Appendix I, "Rising mains", AUD/m:
    #   DN100 368 | DN150 423 | DN200 459 | DN225 479 | DN250 513 | DN300 586 | DN375 714
    #   | DN450 842 | DN600 1473
    # ASSUMPTION, NON-OMANI, and the replacement is Renardet's own priced BoQs.
    RM_RATE_OMR_M: Dict[int, float] = field(default_factory=lambda: {
        100: 121.9, 150: 140.1, 200: 152.1, 225: 158.7, 250: 169.9, 300: 194.1,
        375: 236.5, 450: 278.9, 600: 487.9})
    RUN_HOURS_BASIS: str = "duty_ratio"   # energy is Q_adf / Q_duty x 8766 h, i.e. the pump
                                      # runs only long enough to pass the day's flow. Stated
                                      # because the alternative (continuous running) is
                                      # wrong by the peak factor.

    # ------------------------------------------------------------------------- registers
    @property
    def PVAF(self) -> float:
        """Present-value annuity factor, G201-p96: 25 years at 5 %."""
        r, n = self.DISCOUNT, self.LCC_YEARS
        return (1.0 - (1.0 + r) ** (-n)) / r

    @property
    def MANNING_PV_OMR(self) -> float:
        """Present value of NWS's manning rule for ONE station. The single most important
        number in the whole pumping economics, and it does not depend on the station's
        size - which is why FEWER, LARGER beats MANY, SMALLER."""
        return self.MANNING_OMR_YR * self.PVAF

    def eps(self, material: str, age_yr: Optional[int] = None) -> float:
        """Absolute roughness in m for a force-main material, G202-p104 Table 21."""
        age = self.FM_DESIGN_AGE_YR if age_yr is None else int(age_yr)
        key = (material, age)
        if key in self.FM_EPS_M:
            return self.FM_EPS_M[key]
        # fall back to the nearest tabulated age for that material, never to a guess
        ages = sorted(a for (m, a) in self.FM_EPS_M if m == material)
        if not ages:
            raise PumpingError(
                f"no G202-p104 Table 21 roughness for material {material!r}. Tabulated "
                f"materials here: {sorted({m for m, _ in self.FM_EPS_M})}")
        nearest = min(ages, key=lambda a: abs(a - age))
        return self.FM_EPS_M[(material, nearest)]

    def rm_rate(self, dn: int) -> float:
        """All-in rising-main rate in OMR/m for a nominal size, log-log interpolated between
        the tabulated points and log-log EXTRAPOLATED beyond them. G203-p50 needs a rate per
        size to run its whole-life comparison; the table stops at DN600, so anything above it
        is an extrapolation and is flagged by `optimise_force_main`."""
        tab = sorted(self.RM_RATE_OMR_M.items())
        if dn in self.RM_RATE_OMR_M:
            return self.RM_RATE_OMR_M[dn]
        if dn < tab[0][0]:
            lo, hi = tab[0], tab[1]
        elif dn > tab[-1][0]:
            lo, hi = tab[-2], tab[-1]
        else:
            lo = max((p for p in tab if p[0] <= dn), key=lambda p: p[0])
            hi = min((p for p in tab if p[0] >= dn), key=lambda p: p[0])
        if lo[0] == hi[0]:
            return lo[1]
        b = math.log(hi[1] / lo[1]) / math.log(hi[0] / lo[0])
        return lo[1] * (dn / lo[0]) ** b

    def internal_diameter(self, dn: int, material: str) -> float:
        """Internal bore in metres for a force main of nominal size `dn`."""
        if material in ("DI", "SS"):
            if not self.DI_ID_EQUALS_DN:
                raise PumpingError("DI_ID_EQUALS_DN is False and no bore table is loaded")
            return dn / 1000.0
        if material == "HDPE":
            return (dn / 1000.0) * (1.0 - 2.0 / self.HDPE_SDR)
        raise PumpingError(
            f"no bore rule for force-main material {material!r}. G203-p53 sec 8.3 recommends "
            "Ductile Iron and HDPE for the pressure main; stainless steel inside stations "
            "under 100 L/s (G203-p52 sec 8.3).")

    @property
    def ASSUMPTIONS(self) -> Dict[str, Tuple]:
        """Every value in this file with no guideline page behind it, and what retires it.
        Reported verbatim on every deliverable - that is the point of keeping the register."""
        return {
            "FM_DESIGN_AGE_YR": (
                self.FM_DESIGN_AGE_YR,
                "which row of G202-p104 Table 21 is the design case. The table runs 0-20 yr; "
                "the appraisal horizon is 25 yr (G201-p96), so the AGED row governs friction "
                "and the t=0 row is the maximum-velocity check. Retired by NWS naming a "
                "design age."),
            "FM_DN_SERIES": (
                self.FM_DN_SERIES,
                "EN 545 ductile-iron preferred sizes. G203 gives NO force-main size series - "
                "only the 75 mm ID floor at p50 sec 8.1. Retired by PAM-SPC-207."),
            "HDPE_SDR": (
                self.HDPE_SDR,
                "PN10. The pressure class is a PAM-SPC-207 question and is OPEN. At SDR11 the "
                "same OD loses 8 % of bore and gains ~40 % friction head, which can move a "
                "size."),
            "SUM_K_STATION": (
                self.SUM_K_STATION,
                "station internal pipework fitting losses. NO GUIDELINE GIVES A LOSS "
                "COEFFICIENT (G201/202/203 all searched); G201-p140 requires a model to carry "
                "one and supplies none. Stated as a fitting schedule in the field comment so "
                "it can be priced and argued with."),
            "MINOR_LOSS_FRAC": (
                self.MINOR_LOSS_FRAC,
                "bends, air valves and washouts along the main, as a fraction of friction "
                "head. G203-p51 sec 8.2.2 requires straight lines and anchored pre-formed "
                "bends, so the count is low."),
            "SHUTOFF_RATIO": (
                self.SHUTOFF_RATIO,
                "closed-valve head / duty head, behind the two-point pump curve H = H0 - aQ^2. "
                "Retired the moment a manufacturer's curve is quoted - which G202-p93 requires "
                "from at least three suppliers."),
            "ETA_PUMP": (
                self.ETA_PUMP,
                "non-clog sewage pump efficiency near BEP. G202-p93 makes efficiency 'the main "
                "criteria' for selection and gives no value. Energy is 0.4 % of a station's "
                "operating cost (see `economics`), so this assumption is almost inert "
                "financially - it matters for the MOTOR RATING, not for the business case."),
            "ETA_MOTOR": (self.ETA_MOTOR, "IE3 4-pole induction motor. G202-p96 specifies "
                          "winding class and service factor, not efficiency."),
            "NPSHR_FRACTION": (
                self.NPSHR_FRACTION,
                "RETRACTED 2026-09-03. It guessed NPSHr as 25 % of DUTY HEAD; NPSHr scales "
                "with flow and speed, not with system head, and on the as-built calibration "
                "case it produced a -13.03 m 'margin' that is not a fact about any pump. "
                "select_pump() now publishes NPSHR_MAX = NPSHa - 1.0 m as a PROCUREMENT "
                "LIMIT and leaves the check UNANSWERED until a curve is quoted."),
            "WELL_RETENTION_COMPARATOR_MIN": (
                self.WELL_RETENTION_COMPARATOR_MIN,
                "THE ONE THE BRIEF ASKED FOR AND THE GUIDELINES DO NOT CONTAIN. No wet-well "
                "retention limit exists in PAM-GUD-201, -202 or -203 (all three searched page "
                "by page for retention / detention / septic). 30 min is G203-p50 sec 8.2.1's "
                "FORCE MAIN figure, adopted as the wet-well comparator because it is the only "
                "retention number in the guideline set and it governs the same sewage in the "
                "same anaerobic state. DATA REQUEST to NWS."),
            "WELL_PLAN_MIN_DIA_M": (self.WELL_PLAN_MIN_DIA_M,
                                    "smallest practical wet-well internal diameter. G203-p48 "
                                    "sec 7.8 (a) says only 'adequate for accommodating pump "
                                    "and piping'."),
            "WELL_FREEBOARD_M": (self.WELL_FREEBOARD_M,
                                 "top water level to cover slab. G203-p47 sec 7.5 requires "
                                 "emergency storage above the last duty pump's start level "
                                 "and gives no depth."),
            "MANNING_OMR_YR": (
                self.MANNING_OMR_YR,
                "NWS PIAD rule, 1,000 OMR/month per pumping station "
                "(W9/analysis/W9_PIAD_financial_review.md sec 2.2). NWS PRACTICE, not a "
                "guideline value, and THE DECISIVE NUMBER: its 25-year present value is "
                f"{self.MANNING_PV_OMR:,.0f} OMR per station whatever the station's size."),
            "TARIFF_OMR_KWH": (self.TARIFF_OMR_KWH, "NWS PIAD range 0.010-0.030 OMR/kWh. "
                               "G201-p96 sec 12.3 says 'based on the latest APSR tariff' and "
                               "names no figure. Negligible: energy is ~0.4 % of OPEX."),
            "ME_OM_FRAC/ME_SHARE_OF_CAPITAL": (
                (self.ME_OM_FRAC, self.ME_SHARE_OF_CAPITAL),
                "NWS PIAD: M&E O&M plus insurance at 2.0 %/yr of 45 % of station capital."),
            "CABRAL": ((self.CABRAL_A, self.CABRAL_B, self.EUR_TO_OMR),
                       "station capital C(kEUR) = exp(4.3184) P^0.5329, P = 9.81 Q H kW, "
                       "fitted over 360 Portuguese stations. NON-OMANI. Renardet's priced "
                       "BoQs are the pending replacement."),
            "RM_OMR_PER_M_DN200": (
                self.RM_OMR_PER_M_DN200,
                "Central Coast Council (NSW) DSP 2019/20 Appendix I, DN200 rising main "
                "459 AUD/m x 0.265 x 1.25 escalation. Used ONLY in the consolidation "
                "break-even, which is reported as a LENGTH so the rate can be swapped."),
            "VAPOUR_PRESSURE_M": (self.VAPOUR_PRESSURE_M,
                                  "water vapour pressure at 15 C, from steam tables - a "
                                  "physical property, not a design value. G203 gives no "
                                  "sewage design temperature; 15 C is the temperature "
                                  "G203-p25 Table 9 states its viscosity at, so this module "
                                  "and the gravity hydraulics share one. 35 C sensitivity is "
                                  "reported by `npsh()`."),
        }

    @property
    def CONFLICTS(self) -> Dict[str, str]:
        """Places where the guidelines contradict themselves, and what this module does."""
        return {
            "Duty pump count, Type 3":
                "G203-p40 Table 17 'Minimum number of duty pumps' reads 1 / 2 / 3 for Types "
                "1 / 2 / 3. G203-p42 Table 19 'Wet Well/Dry Arrangement -> Number of pumps "
                "and arrangement' reads '1 duty, 1 standby | 2 duty, 1 standby | 2 duty, 1 "
                "standby' - i.e. TWO duty pumps on a Type 3, not three. Same document, two "
                "answers. This module takes Table 17, because that table's own row label is "
                "MINIMUM and a minimum cannot be reduced by a later table. Both are printed "
                "on the station schedule so a reviewer can overturn it.",
            "Motor speed ceiling":
                "G203-p41 Table 17 caps pump motor speed at 1,450 rpm above 5 l/s (2,800 rpm "
                "below). G202-p96 lists the 50 Hz synchronous speeds and says 'Prefer a motor "
                "running 1500 rpm rather than 3000 rpm'. 1,450 rpm IS the loaded speed of a "
                "4-pole 1,500 rpm machine, so they agree in substance; the module reports "
                "1,450 rpm as the ceiling (G203, the wastewater document) and notes it.",
            "Motor service factor":
                "G202-p96 reads 'proper overloading service factor minimum of 1.15%'. A 1.15 % "
                "service factor is meaningless; 1.15 is the standard NEMA value. Read as 1.15 "
                "and flagged rather than silently corrected.",
            "Pump design life":
                "G203-p38 gives non-structural mechanical installations 20 years; G203-p40 "
                "Table 17 gives pumps 'Service rating: 15 years design life'. The life-cycle "
                "run is 25 years (G201-p96), so BOTH imply a mid-life pump replacement. "
                "criteria.PS_SERVICE_LIFE_YR carries 15; `economics()` prices one replacement "
                "at year 15 and says so.",
            "Rising main velocity vs gravity velocity":
                "2.5 m/s is the FORCE MAIN maximum (G203-p50 sec 8.1). 3.0 m/s is the GRAVITY "
                "maximum (G203-p27 sec 4.2.2.2). They have already been conflated once on this "
                "project. This module never reads criteria.V_MAX; it reads criteria.FM_V_MAX.",
            "Wadi crossing cover":
                "G203-p52 sec 8.2.4 gives 1.5 m to crown at a wadi crossing; G201-p86 sec 9.3 "
                "gives 'a minimum cover of 2 meters' in SOFT SOIL. Both apply - 2.0 m where "
                "the soil is soft. Neither is a scour calculation, which is what actually "
                "governs (G201-p85 requires the scour analysis).",
        }

    @property
    def TO_MIGRATE(self) -> Tuple[str, ...]:
        """Fields that belong in `criteria.py` - the project's single source of numbers -
        and are declared here only because this module does not own that file."""
        return ("FM_EPS_M (G202-p104 Table 21)", "FM_DESIGN_AGE_YR", "FM_DN_SERIES",
                "HDPE_SDR", "SUM_K_STATION", "MINOR_LOSS_FRAC", "SHUTOFF_RATIO",
                "ETA_PUMP", "ETA_MOTOR", "MOTOR_MARGIN (G202-p96)",
                "NPSH_MARGIN_M (G203-p47 sec 7.6)", "NPSHR_FRACTION",
                "WELL_RETENTION_COMPARATOR_MIN", "WELL_PLAN_MIN_DIA_M", "WELL_FREEBOARD_M",
                "LCC_YEARS / DISCOUNT (G201-p96 sec 12.4)", "MANNING_OMR_YR",
                "TARIFF_OMR_KWH", "ME_OM_FRAC", "CABRAL_*", "RM_OMR_PER_M_DN200")


PUMP = PumpCriteria()          # THE pumping design basis. Functions take `pc=PUMP`.


# ======================================================================================
# 2. MEASURED - the only built pumping asset in the study area, and what it teaches
# ======================================================================================

#: NAMA's built station and its rising main, measured 2026-09-03 from
#: `Data/Received/09-RECEIVED/NAMA/IBRI/WW/SHIP/FORCELINE_IBRI.shp` (STATUS = 'Ex', the one
#: built record of nine) and the 0.5 m terrain VRT.
#:
#: READ THE THIRD ROW. The built rising main has NEGATIVE static lift: it FALLS 22.36 m over
#: 9,993.5 m. NAMA did not pump because they had to lift. They pumped because 2.24 m/km of
#: fall is LESS THAN HALF the 5.00 mm/m minimum gradient a DN200 may be laid at (G203-p29
#: Table 11), so a gravity sewer on that route sinks about 27.6 m below the surface before it
#: arrives - and G203-p29 forbids fixing that by oversizing the pipe to lay it flatter.
#:
#: This is the calibration case for every station in this design, and it is also the answer
#: to "why is there a station here at all" on flat ground: FLATNESS, not lift.
ASBUILT_STATION: Dict[str, object] = {
    "station_xy": (449899.59, 2567301.72),
    "station_ground_m": 351.10,
    "discharge_xy": (444422.80, 2563337.90),
    "discharge_ground_m": 328.68,
    "main_length_m": 9993.50,
    "static_lift_m": -22.36,               # NEGATIVE: the main falls
    "ground_fall_per_km": 2.238,           # m/km
    "dn_recorded": None,                   # N_DIAMETER / OUT_DIAMET / IN_DIAMETE are all 0
    "material_recorded": None,             # MATERIAL is null on the built record
    "installed": 2006,
    "source": "FORCELINE_IBRI.shp FEATUREID L021671, STATUS='Ex', PROJECTCOD 5A-1; "
              "REMARKS: 'Data is not reliable and must be used only for reference purpose'",
    "what_it_cannot_calibrate":
        "NO diameter, NO material, NO invert and NO pump data are recorded on the built "
        "record. GR_TEPS_IBRI.shp, the pumping-station layer, holds ONE feature and it is "
        "STATUS='Design' from the unapproved SUREKHA concept, with NO_OF_PUMP = 0. So this "
        "project has NO measured force-main diameter and NO measured pump duty to calibrate "
        "against. Every hydraulic number in this module is derived from the guidelines and "
        "checked against itself, never against a built asset. That is a real limit and it "
        "is a data request, not a modelling choice.",
    "what_it_does_calibrate":
        "the DECISION. One station plus 10.0 km of main is what let 5A-1 be commissioned "
        "without first building a deep gravity trunk - the commissioning argument in "
        "philosophy sec 6, measured rather than asserted.",
}


# ======================================================================================
# 3. FLOWS - what the station has to pass
# ======================================================================================

@dataclass(frozen=True)
class Flows:
    """The four flows G203-p39 sec 7.4 says shall be considered, and where each is used."""

    q_peak_ls: float          # (a) design peak - THE PUMPS SHALL BE CAPABLE OF HANDLING IT
    q_adf_ls: float           # (b) design average - efficient operation, and the energy bill
    q_avg_initial_ls: float   # (b) initial average - the start-year case
    q_min_initial_ls: float   # (c) initial minimum - SIZES THE FORCE MAIN against deposition
    min_flow_factor: float    # G203-p40 Table 16, the multiplier that produced (c)
    n_prop: float = 0.0

    @property
    def q_peak_m3s(self) -> float:
        return self.q_peak_ls / 1000.0

    @property
    def q_adf_m3d(self) -> float:
        return self.q_adf_ls * 86.4

    def as_row(self) -> dict:
        return {
            "Q_PK_LS": round(self.q_peak_ls, 3),
            "Q_ADF_LS": round(self.q_adf_ls, 3),
            "Q_INI_LS": round(self.q_avg_initial_ls, 3),
            "Q_MIN_LS": round(self.q_min_initial_ls, 3),
            "MINF_FAC": round(self.min_flow_factor, 4),
        }


def flows(q_peak_ls: float, q_adf_ls: float, *, q_avg_initial_ls: Optional[float] = None,
          n_prop: float = 0.0, crit: Criteria = DEFAULT) -> Flows:
    """The station's design flows, from the accumulated peak it receives.

    `q_peak_ls` is the peak flow ARRIVING at the station - the same number the incoming
    gravity reach was sized on, including unpeaked infiltration. G203-p39 sec 7.4 (d): "The
    pumps shall be capable of handling the design peak flow."

    `q_min_initial_ls` is the one that sizes the FORCE MAIN, and it is not the average.
    G203-p39 sec 7.4 (e), verbatim: "the initial minimum flow rate shall be considered in
    sizing the force main so that deposition at low velocity is avoided", and (f) "Initial
    minimum flows to be pumped shall be approximated by using the multipliers in Table 16."
    Table 16 (G203-p40) is keyed on AVERAGE flow, so the factor is applied to the INITIAL
    average - which is why `q_avg_initial_ls` is a separate argument and defaults, loudly, to
    the design average (the conservative-on-velocity, pessimistic-on-siltation reading).
    """
    if q_peak_ls <= 0:
        raise PumpingError(
            "a station with zero peak flow is not a station. W11a published 226 rows with "
            "Q_DUTY_LS = 0; refusing to repeat it.")
    if q_adf_ls <= 0:
        raise PumpingError("average flow must be positive to size a wet well or an energy bill")
    if q_adf_ls > q_peak_ls:
        raise PumpingError(f"average {q_adf_ls:.2f} L/s exceeds peak {q_peak_ls:.2f} L/s")
    q_ini = float(q_avg_initial_ls) if q_avg_initial_ls is not None else float(q_adf_ls)
    f = crit.ps_min_flow_factor(q_ini)
    return Flows(q_peak_ls=float(q_peak_ls), q_adf_ls=float(q_adf_ls),
                 q_avg_initial_ls=q_ini, q_min_initial_ls=q_ini * f,
                 min_flow_factor=f, n_prop=float(n_prop))


# ======================================================================================
# 4. STATION TYPE AND PUMP COUNT
# ======================================================================================

@dataclass(frozen=True)
class StationType:
    name: str                 # "Type 1" / "Type 2" / "Type 3"
    n_duty: int
    n_standby: int
    land_min_m2: float
    land_max_m2: Optional[float]
    table19_duty: int         # the CONFLICTING count from G203-p42 Table 19
    cite: str = "G203-p40 (types), G203-p40 Table 17 (duty/standby), G203-p43 Table 21 (land)"

    @property
    def n_installed(self) -> int:
        return self.n_duty + self.n_standby


#: G203-p42 Table 19 "Number of pumps and arrangement": 1+1 | 2+1 | 2+1. Kept beside Table
#: 17's 1/2/3 duty so the conflict travels with the design instead of being resolved
#: silently. See PumpCriteria.CONFLICTS["Duty pump count, Type 3"].
_TABLE19_DUTY = {"Type 1": 1, "Type 2": 2, "Type 3": 2}


def station_type(q_design_ls: float, crit: Criteria = DEFAULT) -> StationType:
    """G203-p40, verbatim: "Type 1: Design flow up to 100 l/s. Type 2: Design flow greater
    than 100 l/s up to 300 l/s. Type 3: Design flow greater than 300 l/s."

    `q_design_ls` is the DESIGN PEAK flow, because that is the flow the pumps must handle
    (G203-p39 sec 7.4 d)."""
    name = crit.ps_type(q_design_ls)
    i = {"Type 1": 0, "Type 2": 1, "Type 3": 2}[name]
    lo, hi = crit.ps_land_m2(name)
    return StationType(name=name, n_duty=crit.PS_DUTY_PUMPS[i],
                       n_standby=crit.PS_STANDBY_PUMPS[i],
                       land_min_m2=lo, land_max_m2=hi,
                       table19_duty=_TABLE19_DUTY[name])


# ======================================================================================
# 5. THE WET WELL
# ======================================================================================

@dataclass(frozen=True)
class WetWell:
    # THE CYCLE-RULE PAIR, and they satisfy V = 0.25 Q T exactly. This is what G203-p48
    # sec 7.8 defines and what `contract.STATIONS.WELL_M3` / `WW_STARTS` mean.
    live_volume_m3: float          # G203-p48: V = 0.25 Q T, Q = SINGLE PUMP capacity
    q_single_pump_ls: float
    starts_per_hour: float         # the SPECIFIED rate: G203-p48's 10/h minimum for motors
                                   # up to 30 kW, unless the caller names another
    cycle_time_s: float
    # THE BUILT PAIR - what a well wide enough to house the pump, with the 200 mm level
    # separation G203-p48 also requires, actually holds and actually cycles at. On a small
    # station the sensor separation governs and the built volume is LARGER than the cycle
    # rule needs, so the pump starts LESS often. That is legal and better for the motor -
    # 10/h is the rate the motor must TOLERATE - but it lengthens retention, which is the
    # septicity term G203 sets no limit on.
    built_volume_m3: float
    built_starts_per_hour: float
    plan_dia_m: float
    plan_area_m2: float
    live_depth_m: float
    level_sep_required_m: float    # G203-p48: 200-300 mm between successive pumps' levels
    level_sep_ok: bool
    retention_at_min_flow_min: float
    retention_comparator_min: float
    retention_flag: str
    cfd_required: bool             # G203-p48: at and above 0.5 m3/s
    emergency_storage_note: str
    screens_note: str

    def as_row(self) -> dict:
        return {
            # the cycle-rule pair - these two and Q_DUTY_LS satisfy V = 0.25 Q T exactly
            "WELL_M3": round(self.live_volume_m3, 4),
            "WW_STARTS": round(self.starts_per_hour, 3),
            "WW_CYC_S": round(self.cycle_time_s, 0),
            # what actually gets built, and what it actually does
            "WW_BLT_M3": round(self.built_volume_m3, 3),
            "WW_BLT_S": round(self.built_starts_per_hour, 3),
            "WW_DIA_M": round(self.plan_dia_m, 2),
            "WW_LIVE_M": round(self.live_depth_m, 3),
            "WW_RET_MI": round(self.retention_at_min_flow_min, 1),
            "WW_SEPTIC": int(self.retention_at_min_flow_min
                             > self.retention_comparator_min),
            "WW_CFD": int(self.cfd_required),
            "WW_SEPOK": int(self.level_sep_ok),
        }


def wet_well(q_single_pump_ls: float, st: StationType, fl: Flows, *,
             starts_per_hour: Optional[float] = None,
             plan_dia_m: Optional[float] = None,
             crit: Criteria = DEFAULT, pc: PumpCriteria = PUMP) -> WetWell:
    """G203-p48 sec 7.8, verbatim: "The minimum live volume (i.e. the volume between the
    start level and the stop level of the pump) is calculated using the formula: V = 0.25 QT
    ... Q = single pump capacity in m3/sec, T = on off cycle time in seconds = 3600 / starts
    per hour ... The number of starts per hour for the pump/motor shall be minimum 10 for
    smaller motors (Up to 30 Kw)."

    THE Q IN THAT FORMULA IS THE SINGLE PUMP, NOT THE STATION. Feeding it the station peak
    on a Type 2 doubles the wet well and halves the start rate, which fails the clause it
    was meant to satisfy.

    RETENTION. There is NO wet-well retention limit in PAM-GUD-201, -202 or -203 - all three
    searched. What is reported here is the live volume's residence at the DESIGN MINIMUM
    inflow (the worst case for septicity, G203-p47 sec 7.7's "long retention times, septic
    conditions"), compared against `pc.WELL_RETENTION_COMPARATOR_MIN`, which is the FORCE
    MAIN's half hour borrowed as a project comparator and flagged as such on every row.
    """
    s_spec = crit.WELL_STARTS_MIN if starts_per_hour is None else float(starts_per_hour)
    q_m3s = q_single_pump_ls / 1000.0
    v_min = crit.well_volume_m3(q_m3s, s_spec)              # raises below 10 starts/h

    dia = float(plan_dia_m) if plan_dia_m else max(
        pc.WELL_PLAN_MIN_DIA_M,
        # a well whose live depth would exceed ~1.5 m on the minimum plan area is widened
        # rather than deepened: deep live bands cost excavation the design is trying to avoid
        math.sqrt(4.0 * v_min / (math.pi * 1.5)) if v_min > 0 else pc.WELL_PLAN_MIN_DIA_M)
    area = math.pi * dia * dia / 4.0

    # G203-p48: "Start and stop levels for successive pumps should be separated by at least
    # 200 mm to 300 mm for liquid-level sensing devices to operate reliably."
    #
    # THIS GOVERNS THE LIVE BAND ON A SMALL STATION, and getting the direction right matters.
    # V = 0.25 QT is a MINIMUM volume, derived from a MINIMUM start rate - 10/h is the number
    # of starts the MOTOR MUST TOLERATE, not a target. So a live band deeper than the
    # equation demands is legal and better for the machine: it starts LESS often. What is NOT
    # legal is a live band too thin for the level sensors to resolve.
    #
    # On a small station a wet well wide enough to house a pump is far wider than the cycle
    # rule needs, so the sensor separation sets the depth and the volume goes UP. The
    # consequences - a longer cycle and a longer retention - are computed and reported rather
    # than being allowed to fail the station. (An earlier version tested live depth against
    # the separation and REFUSED six small stations; that inverted the rule.)
    sep_needed = crit.WELL_LEVEL_SEP_M * max(1, st.n_duty)
    live_depth = max(v_min / area, sep_needed)
    v = live_depth * area
    sep_ok = live_depth >= sep_needed - 1e-12
    # publish the start rate that ACTUALLY follows from the published volume, so
    # V = 0.25 Q T holds on the row and the contract equation can be checked
    s = 3600.0 / (v / (crit.WELL_K * q_m3s)) if q_m3s > 0 else s_spec
    t_cycle = 3600.0 / s if s > 0 else float("inf")

    q_min = max(fl.q_min_initial_ls, 1e-9) / 1000.0
    ret = v / q_min / 60.0        # on the BUILT volume - that is what the sewage sits in
    flag = ("WITHIN the 30-min FORCE-MAIN comparator (G203-p50 sec 8.2.1) - NOT a wet-well "
            "guideline limit; none exists"
            if ret <= pc.WELL_RETENTION_COMPARATOR_MIN else
            f"EXCEEDS the 30-min comparator at {ret:.0f} min. NO GUIDELINE LIMIT EXISTS for "
            "a wet well (G201/202/203 all searched); G203-p47 sec 7.7 names long retention "
            "as the H2S trigger and gives no number. Septicity control is a DESIGN ITEM here")

    v_cycle = v_min                     # the G203-p48 cycle-rule volume, at s_spec
    note_starts = ""
    if s < crit.WELL_STARTS_MIN - 1e-9:
        note_starts = (
            f"the live band is SENSOR-GOVERNED, not cycle-governed: a wet well wide enough "
            f"to house the pump ({dia:.2f} m) with the {crit.WELL_LEVEL_SEP_M*1000:.0f} mm "
            f"level separation G203-p48 requires holds {v:.2f} m3, against the "
            f"{v_min:.2f} m3 the V = 0.25 QT minimum asks for. The pump therefore starts "
            f"{s:.2f} times an hour, not {s_spec:.0f} - which is FEWER starts and better for "
            f"the motor, since 10/h is a minimum the motor must tolerate. The cost is "
            f"retention: {ret:.0f} min at the design minimum inflow. A smaller sump or a "
            "packaged station is the detail-design answer.")

    return WetWell(
        live_volume_m3=v_cycle, q_single_pump_ls=q_single_pump_ls, starts_per_hour=s_spec,
        cycle_time_s=3600.0 / s_spec,
        built_volume_m3=v, built_starts_per_hour=s,
        plan_dia_m=dia, plan_area_m2=area, live_depth_m=live_depth,
        level_sep_required_m=sep_needed, level_sep_ok=sep_ok,
        retention_at_min_flow_min=ret,
        retention_comparator_min=pc.WELL_RETENTION_COMPARATOR_MIN,
        retention_flag=(flag + (" || " + note_starts if note_starts else "")),
        cfd_required=(fl.q_peak_m3s >= crit.PS_CFD_THRESHOLD_M3S),
        emergency_storage_note=(
            "G203-p47 sec 7.5: every station shall have an emergency overflow; 'Storage "
            "shall be provided above the start level for the last duty pump.' Overflows are "
            "NOT to be provided at upstream manholes. Wet-well overflow to carry a dip tube "
            "or baffle board accessible from above. Approval by the Environmental Authority."),
        screens_note=(
            "G203-p41 Table 18: screens COMPULSORY at every type; Type 1 removable, Type 2 "
            "removable or motorised, Type 3 motorised automatic. Inlet baffle on all "
            "stations; benching shaped to prevent deposition."),
    )


# ======================================================================================
# 6. FORCE MAIN HYDRAULICS
# ======================================================================================

def friction_slope(q_m3s: float, id_m: float, eps_m: float,
                   crit: Criteria = DEFAULT) -> float:
    """Hydraulic gradient (m/m) for full-bore flow `q_m3s` in a pipe of internal bore `id_m`.

    Solved by inverting the SAME Colebrook-White expression the gravity design uses
    (`hydra.q_full`, G203-p24 sec 4.2.1) with the roughness swapped to the force-main value
    from G202-p104 Table 21. The equation is not re-implemented here - one friction law in
    the project, and it is the one the guideline prints.
    """
    if q_m3s <= 0 or id_m <= 0:
        return 0.0
    c = replace(crit, KS=float(eps_m))
    lo, hi = 1e-9, 1e-3
    for _ in range(60):                       # bracket
        if hydra.q_full(id_m, hi, c) >= q_m3s:
            break
        hi *= 2.0
    else:
        raise PumpingError(f"no gradient passes {q_m3s*1000:.1f} L/s in a {id_m*1000:.0f} mm "
                           "bore - the pipe is too small at any pressure")
    for _ in range(80):                       # bisect
        mid = 0.5 * (lo + hi)
        if hydra.q_full(id_m, mid, c) < q_m3s:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def velocity(q_m3s: float, id_m: float) -> float:
    return q_m3s / (math.pi * id_m * id_m / 4.0) if id_m > 0 else 0.0


@dataclass(frozen=True)
class ForceMain:
    dn: int
    material: str
    id_m: float
    length_m: float
    static_lift_m: float
    eps_m: float
    v_duty_ms: float
    v_min_ms: float
    v_max_check_ms: float          # velocity at the highest flow the station can deliver
    hf_duty_m: float
    hminor_duty_m: float
    total_head_m: float
    retention_min: float
    n_air_valves: int
    n_washouts: int
    n_isolation: int
    air_valve_dn: int
    washout_dn: int
    v_max_ok: bool                 # G203-p50: <= 2.5 m/s
    v_min_ok: bool                 # G203-p50: >= 0.75 m/s AT DESIGN MINIMUM FLOW
    retention_ok: bool             # G203-p50: <= 30 min
    id_min_ok: bool                # G203-p50: >= 75 mm ID (non-clog)
    notes: Tuple[str, ...] = ()

    def as_row(self) -> dict:
        return {
            "DN": int(self.dn),
            "MATERIAL": self.material,
            "LEN_M": round(self.length_m, 2),
            "V_DUTY_MS": round(self.v_duty_ms, 3),
            "V_MIN_MS": round(self.v_min_ms, 3),
            "STAT_HD_M": round(self.static_lift_m, 3),
            "TOT_HD_M": round(self.total_head_m, 3),
            "RETENT_M": round(self.retention_min, 1),
            "N_AIRV": int(self.n_air_valves),
            "N_WASH": int(self.n_washouts),
            "SEPTIC_FL": 1,
        }


# G203-p53 Table 24 Air Valve Sizes: pipeline bore -> nominal air valve size, mm.
_AIR_VALVE_TABLE: Tuple[Tuple[int, int], ...] = ((300, 80), (500, 100), (900, 150),
                                                 (1200, 200), (1600, 400))
# G203-p54 sec 8.4.2 washout sizing: "Up to 400 mm - 100 mm washout pipe; 500 to 800 mm -
# 150 mm; 900 to 1200 mm - 200 mm; 1200 mm and above - 300 mm." Minimum 100 mm.
_WASHOUT_TABLE: Tuple[Tuple[int, int], ...] = ((400, 100), (800, 150), (1200, 200),
                                               (10_000, 300))


def _lookup(table: Sequence[Tuple[int, int]], dn: int) -> int:
    for hi, val in table:
        if dn <= hi:
            return val
    return table[-1][1]


def velocity_band_feasibility(fl: Flows, q_single_pump_ls: Optional[float] = None,
                              crit: Criteria = DEFAULT) -> Dict[str, object]:
    """CAN ONE RISING MAIN MEET BOTH G203-p50 VELOCITY LIMITS AT ALL? Usually not, and the
    arithmetic is exact.

    In a full pipe velocity is proportional to flow, so ONE main can only span a flow ratio
    equal to the ratio of the two velocity limits:

        Q_max / Q_min  <=  V_max / V_min  =  2.5 / 0.75  =  3.33

    A station whose peak flow is more than 3.33 times its design minimum flow CANNOT satisfy
    both clauses with a single pipe, at any diameter. That is not a modelling artefact; it is
    the two clauses read together.

    On this project the ratio is always far higher. The Merrimack peak factor (G201-p71) is
    around 2 to 3, and G203-p40 Table 16 puts the initial minimum at 0.25 to 0.50 of average,
    so peak / design-minimum runs about 4 to 12. EVERY station therefore hits this.

    THERE ARE TWO DEFENSIBLE READINGS OF "DESIGN MINIMUM FLOW", AND THIS FUNCTION REPORTS
    BOTH, because G203 does not settle it:

      A. LITERAL. G203-p39 sec 7.4 (e): "the initial minimum flow rate shall be considered in
         sizing the force main so that deposition at low velocity is avoided", with (f)
         pointing at Table 16. Read literally, the main must hold 0.75 m/s at the Table-16
         flow, and on these ratios no single diameter can also stay under 2.5 m/s at peak.

      B. AS PUMPED. Table 16 is titled "Minimum Pump FLOW", and a FIXED-SPEED duty pump does
         not deliver the sewer's minimum inflow - it delivers its own duty flow whenever it
         runs, and the wet well does the buffering (that is what G203-p48's V = 0.25 QT
         cycle IS). The lowest flow such a main ever sees is therefore ONE DUTY PUMP running,
         not the catchment's night flow. Under this reading most mains self-cleanse on every
         pump cycle.

    Reading B is what a fixed-speed station physically does; reading A is what the clause
    says. The design cannot choose one silently, so both velocities go on the schedule and
    the resolution is named:

      * a smaller FIRST-STAGE main now and a second main later - G203-p50 sec 8.1 in terms:
        "For cases where initial flows are significantly lower than future flows two or more
        rising mains may be warranted";
      * TWIN mains under G203-p52 sec 8.2.3, which requires a dedicated hydraulic study to
        "Guarantee the minimum velocity requirement of 0.75 m/s in any case" and to "Reduce
        stagnation time and sedimentation by alternating or flushing";
      * or a scheduled flush - the wet well emptied in one long run at duty.

    NONE of these is a diameter, which is why the sizing function refuses to fix it by
    resizing.
    """
    ratio_limit = crit.FM_V_MAX / crit.FM_V_MIN
    r_literal = fl.q_peak_ls / max(fl.q_min_initial_ls, 1e-9)
    r_pumped = (fl.q_peak_ls / max(q_single_pump_ls, 1e-9)
                if q_single_pump_ls else float("nan"))
    return {
        "single_main_max_flow_ratio": ratio_limit,
        "ratio_reading_A_literal": r_literal,
        "ratio_reading_B_as_pumped": r_pumped,
        "feasible_reading_A": bool(r_literal <= ratio_limit),
        "feasible_reading_B": bool(r_pumped <= ratio_limit) if q_single_pump_ls else None,
        "note": (
            f"one main can span a flow ratio of {ratio_limit:.2f} (2.5 / 0.75 m/s, G203-p50 "
            f"sec 8.1). This station's peak / design-minimum ratio is {r_literal:.1f} on the "
            "LITERAL reading of G203-p39 sec 7.4 (e)"
            + (f" and {r_pumped:.2f} on the AS-PUMPED reading (one duty pump running)."
               if q_single_pump_ls else ".")
            + " Resolutions are staged mains, twin mains (G203-p52 sec 8.2.3) or a scheduled "
              "flush - never a different diameter."),
    }


def optimise_force_main(q_duty_ls: float, fl: Flows, length_m: float, static_lift_m: float,
                        *, material: str = "DI", q_max_ls: Optional[float] = None,
                        n_duty: int = 1,
                        crit: Criteria = DEFAULT,
                        pc: PumpCriteria = PUMP) -> Tuple[int, List[dict]]:
    """The whole-life size comparison G203-p50 REQUIRES, run over every legal size.

    G203-p50, verbatim: "Alternative diameters shall be considered which produce a range of
    velocities between the minimum and maximum acceptable velocities, and which adhere to
    acceptable pumping ranges indicated on manufacturer's pump characteristic curves. A cost
    comparison shall be performed to determine which pressure main size will result in the
    optimum whole life cost of the pressure main and associated pumping costs."

    So the smallest legal size is NOT the answer, and W11b said it was until the as-built
    calibration case exposed it: a DN300 over NAMA's 10 km route burns 109 m of friction
    head and 17 % of the station's life-cycle cost in electricity. The comparison below is
    capital of the main plus the present value of the pumping energy, over G201-p96's 25
    years at 5 %, with the energy taken from Q_adf x head (which is all it depends on -
    `energy_equals_manning()`).

    Returns (chosen DN, the full comparison table) so the table can be published. The
    guideline asks for the comparison, not just its winner.
    """
    eps = pc.eps(material)
    q_duty = q_duty_ls / 1000.0
    q_min = fl.q_min_initial_ls / 1000.0
    q_max = (q_max_ls if q_max_ls is not None else q_duty_ls * 1.15) / 1000.0
    k_energy = 1000.0 * crit.G * 8766.0 / (pc.ETA_PUMP * pc.ETA_MOTOR) / 1000.0

    rows: List[dict] = []
    for dn in pc.FM_DN_SERIES:
        idm = pc.internal_diameter(dn, material)
        if idm * 1000.0 < crit.FM_ID_MIN_MM:
            continue
        v_duty = velocity(q_duty, idm)
        v_max = velocity(q_max, idm)
        v_min = velocity(q_min, idm)
        # ONE duty pump running - the lowest flow the station ever DELIVERS. This is the
        # velocity that has to clear the self-cleansing floor.
        v_one = velocity(q_duty / max(1, n_duty), idm)
        # G203-p50, verbatim: "Alternative diameters shall be considered which produce a
        # range of velocities BETWEEN THE MINIMUM AND MAXIMUM acceptable velocities". The
        # cost comparison runs over the ACCEPTABLE set, not over every size under 2.5 m/s -
        # otherwise the whole-life term buys a bigger main by silting it, which is what
        # happened when the station-capital term was first added: the optimum walked up to
        # DN250 and 72 of 112 stations then failed the self-cleansing gate.
        if v_max > crit.FM_V_MAX or v_one < crit.FM_V_MIN:
            continue
        hf = friction_slope(q_duty, idm, eps, crit) * length_m
        head = static_lift_m + hf * (1.0 + pc.MINOR_LOSS_FRAC)
        head_pos = max(head, 0.0)
        cap = pc.rm_rate(dn) * length_m
        kwh = k_energy * (fl.q_adf_ls / 1000.0) * head_pos
        energy_pv = kwh * pc.TARIFF_OMR_KWH * pc.PVAF
        # "and ASSOCIATED PUMPING COSTS" - G203-p50's own words, and they are not just the
        # electricity. A bigger main means a lower head, which means a smaller pump, a
        # smaller motor and a smaller station: Cabral's fit is C ~ (Q H)^0.5329, so halving
        # the head takes about 31 % off the station's capital. Leaving this term out is how a
        # sizing routine talks itself into a main that burns 109 m of friction over 10 km.
        p_hyd_kw = 9.81 * q_duty * max(head_pos, 1e-6)
        st_cap = math.exp(pc.CABRAL_A) * p_hyd_kw ** pc.CABRAL_B * 1000.0 * pc.EUR_TO_OMR
        rows.append({
            "DN": dn, "v_duty_ms": v_duty, "v_min_ms": v_min, "v_max_ms": v_max,
            "hf_m": hf, "total_head_m": head,
            "v_one_pump_ms": v_one,
            "main_capital_omr": cap, "station_capital_omr": st_cap,
            "energy_kwh_yr": kwh, "energy_pv_omr": energy_pv,
            "whole_life_omr": cap + st_cap + energy_pv,
            "v_min_ok": v_min >= crit.FM_V_MIN,
            "rate_extrapolated": dn > max(pc.RM_RATE_OMR_M),
        })
    if not rows:
        raise PumpingError(
            f"no size in {pc.FM_DN_SERIES} puts this station inside the G203-p50 velocity "
            f"band: {crit.FM_V_MAX} m/s at the worst case ({q_max*1000:.1f} L/s) AND "
            f"{crit.FM_V_MIN} m/s with one duty pump ({q_duty*1000/max(1,n_duty):.1f} L/s). "
            "The resolutions are a grinder pump on a 50 mm ID main (G203-p50), twin mains "
            "(G203-p52 sec 8.2.3), or taking this catchment out of the central network.")
    best = min(rows, key=lambda r: r["whole_life_omr"])
    for r in rows:
        r["chosen"] = (r["DN"] == best["DN"])
    return int(best["DN"]), rows


def size_force_main(q_duty_ls: float, fl: Flows, length_m: float, static_lift_m: float, *,
                    material: str = "DI",
                    q_max_ls: Optional[float] = None,
                    n_summits: int = 0, n_low_points: int = 0,
                    whole_life: bool = True, n_duty: int = 1,
                    crit: Criteria = DEFAULT, pc: PumpCriteria = PUMP) -> ForceMain:
    """Size the rising main to the velocity band, then report everything that band implies.

    THE BAND, from G203-p50 sec 8.1 read out of the PDF:
      * "The maximum allowable velocity (worst case scenario) in the pipe shall be not
        greater than 2.5 m/s."   <- NOT the 3.0 m/s gravity maximum at G203-p27 sec 4.2.2.2.
      * "At design minimum flow (that is, maximum static head), a velocity of at least
        0.75 m/s shall be maintained for raw sewage."   <- held at the DESIGN MINIMUM flow,
        which G203-p40 Table 16 supplies. Sizing on duty alone silts the main in year one.
      * "A force main shall be a minimum 75 mm inside diameter for non-clog pumps."

    THE RULE APPLIED HERE, and it changed on 2026-09-03: the size is chosen on WHOLE-LIFE
    COST over every size that meets the 2.5 m/s ceiling - `optimise_force_main()` - because
    that is what G203-p50 demands in terms. W11b previously took the SMALLEST legal size on
    the argument that pumping energy is negligible; the as-built calibration case killed
    that argument, because on NAMA's own 10 km route the smallest legal size (DN300) burns
    109 m of friction head and 17 % of the station's life-cycle cost. Pass
    `whole_life=False` to see the old smallest-legal answer.

    The minimum-flow velocity is then REPORTED, and where it falls below 0.75 m/s the main
    is NOT silently resized - the conflict is named, because G203-p50 sec 8.1 answers it
    with a different device: "For cases where initial flows are significantly lower than
    future flows two or more rising mains may be warranted", and sec 8.2.3 sets out the
    twin-pipeline study. That is a design decision, not a diameter. Note the direction of
    the trade: whole-life sizing makes the main BIGGER, which makes the minimum-flow
    velocity WORSE. Both facts belong on the schedule.
    """
    if length_m <= 0:
        raise PumpingError("a rising main of zero length is not a rising main")
    eps = pc.eps(material)
    q_duty = q_duty_ls / 1000.0
    q_min = fl.q_min_initial_ls / 1000.0
    q_max = (q_max_ls if q_max_ls is not None else q_duty_ls * 1.15) / 1000.0

    if whole_life:
        dn, _table = optimise_force_main(q_duty_ls, fl, length_m, static_lift_m,
                                         material=material, q_max_ls=q_max_ls,
                                         n_duty=n_duty, crit=crit, pc=pc)
        idm = pc.internal_diameter(dn, material)
    else:
        chosen = None
        for dn_i in pc.FM_DN_SERIES:
            idm_i = pc.internal_diameter(dn_i, material)
            if idm_i * 1000.0 < crit.FM_ID_MIN_MM:      # G203-p50 75 mm ID floor
                continue
            if velocity(q_max, idm_i) <= crit.FM_V_MAX:  # G203-p50 2.5 m/s, worst case
                chosen = (dn_i, idm_i)
                break
        if chosen is None:
            raise PumpingError(
                f"no size in {pc.FM_DN_SERIES} keeps {q_max*1000:.0f} L/s under the "
                f"{crit.FM_V_MAX} m/s force-main maximum (G203-p50). Extend FM_DN_SERIES or "
                "split the flow between twin mains (G203-p52 sec 8.2.3).")
        dn, idm = chosen

    v_duty = velocity(q_duty, idm)
    v_min = velocity(q_min, idm)
    v_max = velocity(q_max, idm)
    s = friction_slope(q_duty, idm, eps, crit)
    hf = s * length_m
    hmin = pc.MINOR_LOSS_FRAC * hf
    total = static_lift_m + hf + hmin
    ret = (length_m / v_duty / 60.0) if v_duty > 0 else float("inf")

    notes: List[str] = []
    if v_min < crit.FM_V_MIN:
        vb = velocity_band_feasibility(fl, crit=crit)
        notes.append(
            f"MINIMUM-FLOW VELOCITY {v_min:.2f} m/s is below the {crit.FM_V_MIN} m/s "
            f"self-cleansing floor (G203-p50 sec 8.1) at the initial minimum flow "
            f"{fl.q_min_initial_ls:.1f} L/s (Table 16 factor {fl.min_flow_factor:.2f}). "
            f"AND NO DIAMETER FIXES IT: one main can span a flow ratio of only "
            f"{vb['single_main_max_flow_ratio']:.2f} (2.5 / 0.75 m/s) and this station's "
            f"peak / design-minimum ratio is {vb['ratio_reading_A_literal']:.1f}. See "
            "velocity_band_feasibility() for the two readings of 'design minimum flow' and "
            "the three resolutions G203 itself offers - staged mains (p50 sec 8.1), twin "
            "mains (p52 sec 8.2.3), or a scheduled flush. Do not resize silently.")
    if ret > crit.FM_RETENTION_MIN:
        notes.append(
            f"RETENTION {ret:.0f} min exceeds the half hour G203-p50 sec 8.2.1 asks for. "
            "The guideline itself says 'In practice, this is very rarely achieved' - so this "
            "is not a breach, it is a SEPTICITY DESIGN TRIGGER: G203-p47 sec 7.7 sets the "
            "H2S design concentrations (50-100 ppm average, <= 200 ppm peak at the "
            "termination) and G203-p55 sec 8.5 requires a water seal, forced venting and a "
            "corrosion-resistant receiving manhole.")
    if static_lift_m < 0:
        notes.append(
            f"STATIC LIFT IS NEGATIVE ({static_lift_m:.1f} m): the main FALLS to its "
            "discharge. The station exists because the ground is too flat for a gravity "
            "sewer, not because there is a hill - the same reason NAMA's own built main "
            "falls 22.4 m over 10.0 km (see ASBUILT_STATION). G203-p50 sec 8.2.1 still "
            "requires the profile to be laid at a gradient and to run full: 1:500 rising, "
            "1:300 falling, never below 1:750, with air valves at summits and washouts at "
            "low points.")

    return ForceMain(
        dn=dn, material=material, id_m=idm, length_m=float(length_m),
        static_lift_m=float(static_lift_m), eps_m=eps,
        v_duty_ms=v_duty, v_min_ms=v_min, v_max_check_ms=v_max,
        hf_duty_m=hf, hminor_duty_m=hmin, total_head_m=total, retention_min=ret,
        # G203-p53 sec 8.4.1: air valves at HIGH POINTS and at significant gradient changes,
        # kept to a minimum. G203-p54 sec 8.4.2: washouts at LOW POINTS.
        n_air_valves=int(n_summits),
        n_washouts=int(n_low_points),
        # G203-p54 sec 8.4.3: "In-line valves shall be considered in the pumping mains at
        # intervals of about 500 m, but not exceeding 800 m".
        n_isolation=max(0, int(math.ceil(length_m / 500.0)) - 1),
        air_valve_dn=_lookup(_AIR_VALVE_TABLE, dn),
        washout_dn=_lookup(_WASHOUT_TABLE, dn),
        v_max_ok=(v_max <= crit.FM_V_MAX),
        v_min_ok=(v_min >= crit.FM_V_MIN),
        retention_ok=(ret <= crit.FM_RETENTION_MIN),
        id_min_ok=(idm * 1000.0 >= crit.FM_ID_MIN_MM),
        notes=tuple(notes),
    )


# ======================================================================================
# 7. THE SYSTEM CURVE AND THE DUTY POINT
# ======================================================================================

@dataclass(frozen=True)
class DutyPoint:
    q_ls: float
    head_m: float
    n_running: int
    v_main_ms: float
    within_velocity_band: bool
    p_hydraulic_kw: float
    p_shaft_kw: float
    p_electrical_kw: float
    specific_energy_kwh_m3: float


@dataclass(frozen=True)
class PumpSelection:
    """A pump chosen against the system curve, G202-p91 sec 6.3.2."""

    q_per_pump_ls: float           # rated flow of ONE pump at the duty point
    head_duty_m: float
    shutoff_head_m: float
    curve_a: float                 # H(Q) = H0 - a Q^2, Q in m3/s
    duty_all: DutyPoint            # all duty pumps running - the design condition
    duty_one: DutyPoint            # ONE pump running - what happens most of the time
    motor_rating_kw: float
    motor_speed_rpm: float
    npsha_m: float
    npshr_max_allowed_m: float     # THE PROCUREMENT LIMIT: NPSHa - the 1 m margin
    npshr_quoted_m: Optional[float]
    npsh_margin_m: Optional[float]
    npsh_ok: Optional[bool]        # None = no machine quoted yet, so UNANSWERED not passed
    notes: Tuple[str, ...] = ()


def system_head(q_m3s: float, static_lift_m: float, fm: ForceMain, *,
                crit: Criteria = DEFAULT, pc: PumpCriteria = PUMP) -> float:
    """The system curve: static lift + friction in the main + minor losses + station
    pipework losses. Evaluated at any flow, which is what makes it a CURVE rather than a
    single number, and what lets a duty point be found at all (G202-p91 sec 6.3.2)."""
    if q_m3s <= 0:
        return static_lift_m
    hf = friction_slope(q_m3s, fm.id_m, fm.eps_m, crit) * fm.length_m
    hminor = pc.MINOR_LOSS_FRAC * hf
    # station internal pipework: G203-p41 Table 17 caps it at 2.5 m/s at maximum flow, so
    # the pipework is sized on the same bore as the main unless it is smaller.
    v_st = velocity(q_m3s, fm.id_m)
    h_station = pc.SUM_K_STATION * v_st * v_st / (2.0 * crit.G)
    return static_lift_m + hf + hminor + h_station


def _point(q_m3s: float, head_m: float, n_running: int, fm: ForceMain,
           fl: Flows, crit: Criteria, pc: PumpCriteria) -> DutyPoint:
    v = velocity(q_m3s, fm.id_m)
    p_hyd = 1000.0 * crit.G * q_m3s * head_m / 1000.0          # kW, rho = 1000 kg/m3
    p_shaft = p_hyd / pc.ETA_PUMP
    p_el = p_shaft / pc.ETA_MOTOR
    se = (p_el / (q_m3s * 3600.0)) if q_m3s > 0 else 0.0        # kWh per m3 pumped
    return DutyPoint(q_ls=q_m3s * 1000.0, head_m=head_m, n_running=n_running, v_main_ms=v,
                     within_velocity_band=(crit.FM_V_MIN <= v <= crit.FM_V_MAX),
                     p_hydraulic_kw=p_hyd, p_shaft_kw=p_shaft, p_electrical_kw=p_el,
                     specific_energy_kwh_m3=se)


def select_pump(fl: Flows, st: StationType, fm: ForceMain, static_lift_m: float, *,
                submergence_m: float = 2.0,
                site_level_m: float = 350.0,
                npshr_m: Optional[float] = None,
                crit: Criteria = DEFAULT, pc: PumpCriteria = PUMP) -> PumpSelection:
    """Pick a pump against the SYSTEM CURVE and report the operating point.

    G202-p91 sec 6.3.2, verbatim: "The point of intersection between the system curve and
    the pump curve is to be considered as the operating point during design."

    THE PART A PLACEHOLDER ALWAYS GETS WRONG. On a Type 2 or Type 3 station the duty is
    shared, and TWO PUMPS IN PARALLEL DO NOT DELIVER TWICE ONE PUMP'S FLOW - the system
    curve is quadratic, so the second pump buys less than the first. Selecting each pump at
    Q_peak / n from its own single-pump curve therefore under-delivers at the design
    condition. Here the pump is chosen so that the PARALLEL duty point equals the design
    peak (G203-p39 sec 7.4 d), and the single-pump point - which is what actually runs for
    most of the day - is reported beside it, because that is the flow the force main sees at
    part load and it is the one that decides whether the main self-cleanses.

    The pump curve is modelled H(Q) = H0 - a Q^2 with H0 = SHUTOFF_RATIO x H_duty
    (`pc.SHUTOFF_RATIO`, an ASSUMPTION). A manufacturer's curve replaces both parameters and
    G202-p93 requires one from at least three suppliers; until then this is a stated model,
    not a claim about a machine.
    """
    n = max(1, st.n_duty)
    q_design = fl.q_peak_m3s
    h_design = system_head(q_design, static_lift_m, fm, crit=crit, pc=pc)

    # Each pump passes q_design / n at the design head. Fit its curve through that point.
    q_pp = q_design / n
    h0 = pc.SHUTOFF_RATIO * h_design
    a = (h0 - h_design) / (q_pp * q_pp) if q_pp > 0 else 0.0

    def head_pump(q_total_m3s: float, running: int) -> float:
        """n identical pumps in parallel: each passes q_total/running at the common head."""
        qi = q_total_m3s / max(1, running)
        return h0 - a * qi * qi

    def intersect(running: int) -> Tuple[float, float]:
        lo, hi = 1e-9, q_design * 4.0
        # pump head falls with Q, system head rises: exactly one crossing
        for _ in range(100):
            mid = 0.5 * (lo + hi)
            if head_pump(mid, running) > system_head(mid, static_lift_m, fm,
                                                     crit=crit, pc=pc):
                lo = mid
            else:
                hi = mid
        q = 0.5 * (lo + hi)
        return q, system_head(q, static_lift_m, fm, crit=crit, pc=pc)

    q_all, h_all = intersect(n)
    q_one, h_one = intersect(1)

    duty_all = _point(q_all, h_all, n, fm, fl, crit, pc)
    duty_one = _point(q_one, h_one, 1, fm, fl, crit, pc)
    vb = velocity_band_feasibility(fl, q_single_pump_ls=duty_one.q_ls, crit=crit)

    # G202-p96: motor "sufficient margin min 10% over the maximum operating point".
    p_max_shaft = max(duty_all.p_shaft_kw / n, duty_one.p_shaft_kw)
    motor_kw = p_max_shaft * (1.0 + pc.MOTOR_MARGIN)

    # NPSH. G203-p47 sec 7.6: NPSHa = Ha - Hvpa - Hst - Hf, and "NPSH margin of at least 1
    # meter should be considered for the pump". Submersible in a wet well: the suction is
    # FLOODED, so Hst is negative - a gain, not a loss.
    #
    # NPSHr IS NOT FABRICATED HERE. G202-p91: NPSHr "is a function of pump design and is
    # usually determined experimentally for each pump". So what this function publishes is
    # the PROCUREMENT LIMIT - the largest NPSHr the selected machine may have and still
    # satisfy G203-p47 - and it leaves `npsh_ok` as None until a real curve is quoted.
    # (An earlier version guessed NPSHr as 25 % of duty head. On the as-built calibration
    # case that gave a -13.03 m "margin", which is not a fact about any pump: NPSHr scales
    # with flow and speed, not with system head. The guess is withdrawn.)
    ha = 10.33 * (1.0 - 2.25577e-5 * site_level_m) ** 5.25588     # ISA, m of water
    hvp = pc.VAPOUR_PRESSURE_M
    hst = -float(submergence_m)                                   # flooded suction
    hf_suction = 0.5 * pc.SUM_K_STATION * velocity(q_pp, fm.id_m) ** 2 / (2.0 * crit.G)
    npsha = ha - hvp - hst - hf_suction
    npshr_max = npsha - pc.NPSH_MARGIN_M
    npshr = float(npshr_m) if npshr_m is not None else None
    margin = (npsha - npshr) if npshr is not None else None

    notes: List[str] = []
    if n > 1:
        gain = q_all / q_one if q_one > 0 else float("nan")
        notes.append(
            f"PARALLEL GAIN {gain:.2f}x, not {n}.00x - {n} pumps on this system curve "
            f"deliver {q_all*1000:.1f} L/s against one pump's {q_one*1000:.1f} L/s. Sizing "
            f"each pump at Q_peak/{n} from its own curve would under-deliver at the design "
            "condition (G202-p91 sec 6.3.2).")
    notes.append(
        f"VELOCITY BAND: one main spans a flow ratio of "
        f"{vb['single_main_max_flow_ratio']:.2f}. Literal reading (G203-p39 sec 7.4 e, "
        f"Table 16): ratio {vb['ratio_reading_A_literal']:.1f} - "
        f"{'FEASIBLE' if vb['feasible_reading_A'] else 'INFEASIBLE with one main'}. "
        f"As-pumped reading (one duty pump running, {duty_one.q_ls:.1f} L/s at "
        f"{duty_one.v_main_ms:.2f} m/s): ratio {vb['ratio_reading_B_as_pumped']:.2f} - "
        f"{'FEASIBLE' if vb['feasible_reading_B'] else 'INFEASIBLE with one main'}. "
        "G203 does not settle which reading governs; both are published.")
    if not duty_one.within_velocity_band:
        notes.append(
            f"ONE PUMP RUNNING gives {duty_one.v_main_ms:.2f} m/s in the main, outside the "
            f"{crit.FM_V_MIN}-{crit.FM_V_MAX} m/s band (G203-p50). Single-pump operation is "
            "the normal condition for most of the day, so this is the case that decides "
            "whether the main silts, not the design peak.")
    if npshr is None:
        notes.append(
            f"NPSH: NPSHa = {npsha:.2f} m at this site "
            f"(atmosphere {ha:.2f} - vapour {hvp:.2f} + submergence {submergence_m:.2f} - "
            f"suction friction {hf_suction:.2f}). G203-p47 sec 7.6 requires at least 1 m of "
            f"margin, so THE SPECIFICATION IS: the selected pump's NPSHr at duty shall not "
            f"exceed {npshr_max:.2f} m. NPSHr is NOT assumed here - G202-p91 says it 'is "
            "usually determined experimentally for each pump', and G202-p93 requires a "
            "commercially available machine from at least three suppliers. UNANSWERED until "
            "a curve is quoted, not passed.")
    elif margin is not None and margin < pc.NPSH_MARGIN_M:
        notes.append(
            f"NPSH MARGIN {margin:.2f} m is below the {pc.NPSH_MARGIN_M:.1f} m G203-p47 sec "
            f"7.6 requires. NPSHa {npsha:.2f} m against a quoted NPSHr of {npshr:.2f} m. "
            "Resolutions: more submergence, a larger suction bell, or a different machine.")
    if fl.q_peak_m3s >= crit.PS_CFD_THRESHOLD_M3S:
        notes.append(
            f"G203-p48 sec 7.8: at {fl.q_peak_m3s:.2f} m3/s this is a 'large pumping station' "
            "and CFD numerical models and physical models shall be considered. G202-p91 also "
            "requires a CFD cavitation check at peak hour / lowest level in the design report.")

    return PumpSelection(
        q_per_pump_ls=q_pp * 1000.0, head_duty_m=h_design, shutoff_head_m=h0, curve_a=a,
        duty_all=duty_all, duty_one=duty_one,
        motor_rating_kw=motor_kw,
        motor_speed_rpm=(crit.PS_MOTOR_RPM_SMALL if fl.q_peak_ls <= 5.0
                         else crit.PS_MOTOR_RPM_MAX),
        npsha_m=npsha, npshr_max_allowed_m=npshr_max, npshr_quoted_m=npshr,
        npsh_margin_m=margin,
        npsh_ok=(None if margin is None else bool(margin >= pc.NPSH_MARGIN_M)),
        notes=tuple(notes))


# ======================================================================================
# 8. SITING - G203-p38 sec 7.2, and the test that cannot be run
# ======================================================================================

@dataclass(frozen=True)
class Siting:
    x: float
    y: float
    ground_m: float
    wet_at_50yr: bool
    hazard_class_50yr: int
    in_channel: bool
    scour_risk: bool
    dry_found: bool
    dry_distance_m: Optional[float]
    dry_xy: Optional[Tuple[float, float]]
    publishable: bool
    verdict: str
    level_test: str
    supplementary: Dict[str, object]

    def as_row(self) -> dict:
        return {
            "SITE_WET": int(self.wet_at_50yr),
            "SITE_CLS": int(self.hazard_class_50yr),
            "SITE_OK": int(self.publishable),
            "DRY_DIST": None if self.dry_distance_m is None else round(self.dry_distance_m, 1),
            "SITE_WHY": self.verdict[:250],
        }


#: The exact wording of the clause, so nobody has to take this module's word for it.
G203_P38_S72 = (
    "Pump pedestal level or building floor, electrical transformers/ pad mounted substation "
    "or emergency generator are to be located above maximum flood level, with the floors "
    "being a minimum of 300 mm above the 1:50 year flood level. The design consultant should "
    "fully acquire the site info and metrological data during the preliminary/detailed design "
    "stage; properly design the surface/stormwater management considering the 1:50 ARI."
)

PHILOSOPHY_CITATION_DEFECT = (
    "_BRAIN/08_DESIGN_PHILOSOPHY.md sec 3 tabulates 1:100 for a pumping station's floor, "
    "transformers and generator and cites G203-p38 sec 7.2. THE CLAUSE SAYS 1:50 - quoted in "
    "full as `G203_P38_S72`. The only 100-year duty in G203 is p63 Table 27 row (i), which is "
    "STP SITE SELECTION. criteria.PS_FLOOD_ARI_YR = 50 and hazard._DUTIES['pumping_station'] "
    "= (50,) are both correct; the philosophy document is not, and it is the binding one. "
    "Correction required before it is quoted again."
)


def site_station(x: float, y: float, ground_m: float, grids, *,
                 max_search_m: float = 500.0,
                 crit: Criteria = DEFAULT, pc: PumpCriteria = PUMP) -> Siting:
    """Test a station site against G203-p38 sec 7.2 and refuse to publish a wet one.

    `grids` is a `w11b.hazard.HazardGrids`.

    TWO SEPARATE TESTS, AND ONLY ONE OF THEM CAN BE RUN:

      1. IS THE FOOTPRINT WET at the 1:50 event? Answerable from the hazard-class grids.
         A station on ground the model floods at 1:50 fails the clause however high its
         floor slab is built, because the access road, the cabling and the sump discharge
         are all at grade. This module REFUSES to publish such a station and names it.

      2. IS THE FLOOR 300 mm ABOVE THE 1:50 LEVEL? NOT ANSWERABLE. The project holds hazard
         CLASSES, not water surfaces - `hazard.flood_level_m_aod()` raises rather than adding
         an invented depth to a terrain reading. This is reported as UNEVALUABLE with the
         data request attached, never as a pass. Philosophy sec 8: a check that cannot run is
         a FAILURE, not a blank.

    The 1:100 and 1:500 grids are sampled as SUPPLEMENTARY information only - the 1:100
    because the philosophy document (wrongly) asks for it, the 1:500 as the upper-bound
    sensitivity `hazard._DUTIES['sensitivity_high']` allows. Neither is the duty.
    """
    s50 = grids.sample(x, y, rp=crit.PS_FLOOD_ARI_YR)
    dry = grids.distance_to_dry(x, y, rp=crit.PS_FLOOD_ARI_YR, max_search_m=max_search_m)

    supp: Dict[str, object] = {}
    for rp in (100, 500):
        try:
            s = grids.sample(x, y, rp=rp)
            supp[f"wet_at_{rp}yr"] = bool(s.is_wet)
            supp[f"class_at_{rp}yr"] = int(s.hazard_class)
        except Exception as e:                      # a grid may be missing; say so
            supp[f"wet_at_{rp}yr"] = f"unavailable: {e}"
    supp["philosophy_citation_defect"] = PHILOSOPHY_CITATION_DEFECT

    if s50.is_wet:
        verdict = (
            f"REFUSED: the footprint is hazard class {s50.hazard_class} at the 1:50 event, "
            f"which G203-p38 sec 7.2 makes the governing return period. "
            + (f"Nearest ground the model does not flood is {dry.distance_m:.0f} m away "
               f"on a bearing of {dry.bearing_deg:.0f} deg."
               if dry.found and dry.distance_m is not None else
               f"NO dry ground found within the {dry.searched_m:.0f} m searched - the cap is "
               "not a distance and is not reported as one.")
        )
        publishable = False
    else:
        verdict = (f"site is dry at the 1:50 event (hazard class {s50.hazard_class}; "
                   f"{'no-data, read as DRY HIGH GROUND per the engineer 2026-09-03' if s50.hazard_class == 0 else 'modelled'}).")
        publishable = True

    level_test = (
        "UNEVALUABLE. G203-p38 sec 7.2 requires the floor a minimum of 300 mm above the 1:50 "
        "year flood LEVEL and every electrical item above the maximum flood level. The "
        "project holds AR&R hazard-CLASS grids and no water surface, so no level can be "
        "derived without inventing a depth. DATA REQUEST: full-coverage 1:50 (and 1:100) "
        "flood LEVELS in m aOD from NWS / MoAFWR. Philosophy sec 8 makes this a FAILURE, not "
        "a blank, and it is reported as one on every station."
    )

    return Siting(
        x=float(x), y=float(y), ground_m=float(ground_m),
        wet_at_50yr=bool(s50.is_wet), hazard_class_50yr=int(s50.hazard_class),
        in_channel=bool(s50.in_channel), scour_risk=bool(s50.scour_risk),
        dry_found=bool(dry.found), dry_distance_m=dry.distance_m,
        dry_xy=((dry.x, dry.y) if dry.found and dry.x is not None else None),
        publishable=publishable, verdict=verdict, level_test=level_test,
        supplementary=supp)


# ======================================================================================
# 9. WADI CROSSINGS ON A FORCE MAIN - G201-p85-86 sec 9.3, in full
# ======================================================================================

def wadi_crossing_obligations(length_on_wadi_m: float, soft_soil: bool = False,
                              crit: Criteria = DEFAULT) -> Dict[str, object]:
    """Every obligation G201 sec 9.3 puts on a force main crossing a wadi, quoted.

    This is a REGISTER, not a calculation. It exists because a crossing with a `CROSS_ID`
    and no obligations behind it schedules nothing (philosophy H1a condition 4)."""
    return {
        "data_to_collect": (
            "G201-p85 sec 9.3: 'hydrogeological, hydrological and meteorological data (wadi "
            "bed profiles & cross-sections, flood frequency analysis (1-in-20 year, 1-in-50 "
            "year, 1-in-100 year, etc... floods), grain size distribution of the bed material "
            "and long-term bed-level change monitoring) from the respective agency (CAA & "
            "MoAFWR)'. WE HOLD NONE OF IT - the project has hazard classes at 10/25/50/100/500 "
            "and no bed profile, no grain size and no bed-level monitoring."),
        "investigations": (
            "G201-p85: 'geophysical, geotechnical, topographic surveys, georesistivity "
            "surveys, environmental Impact assessment, hydraulic & scour analysis'. THE SCOUR "
            "ANALYSIS IS THE ONE THAT SETS THE COVER, and it is what the hazard-class proxy "
            "in criteria.HAZARD_WADI_CLASSES is standing in for."),
        "approvals": "G201-p85: 'Approvals shall be obtained from MoAFWR and any other "
                     "relevant agencies.'",
        "pipe_material": (
            f"G201-p86: 'Ductile Iron pipes and fittings shall be used over the length of "
            f"wadi crossings plus 15 m on either side. The use of mechanical or detachable "
            f"joints is necessary.' Here: {length_on_wadi_m:.0f} m + 15 m each side = "
            f"{length_on_wadi_m + 30.0:.0f} m of DI."),
        "protection": "G201-p86: 'Wadi protection is to be designed according to NWS standard "
                      "drawings PAM-STD-404' and 'shall be designed to prevent flotation of "
                      "the pipeline in the event of flooding ... while the pipe is empty.'",
        "minimum_cover_m": (2.0 if soft_soil else crit.MIN_COVER_WADI_XING),
        "cover_source": ("G201-p86: 'Wadi crossings in soft soil will be constructed with a "
                         "minimum cover of 2 meters.'" if soft_soil else
                         "G203-p52 sec 8.2.4: 'At Wadi crossing: 1.5 m (depth to crown of "
                         "pipe)'. G201-p86 raises it to 2.0 m in soft soil."),
        "valves": ("G201-p86: 'Isolation and air valves shall be installed either side of "
                   "active and major wadi crossings ... A washout will be included at the low "
                   "point on one side of the crossing.'"),
        "no_structures_in_the_bed": (
            "G201-p86: 'No valve chambers or marker posts shall be constructed in the wadi bed "
            "or on the embankments of the wadi and all valves and marker posts must be visible "
            "and fully accessible when the Wadi is in flood.' THIS IS THE CLAUSE THAT WAS "
            "MISCITED as the authority for banning a GRAVITY MANHOLE in a wadi - it is about "
            "valve chambers and marker posts on a FORCE MAIN, and here it is on point."),
        "marking": ("G203-p51 sec 8.2.2: cross-country rising mains marked at every field "
                    "boundary and change of direction with concrete posts reading 'PUMPED "
                    "SEWER' and the depth to the top of the pipe; non-degradable marker tape "
                    "300 mm above the pipe with a trace wire to a post every ~1,000 m."),
        "twin_option": ("G203-p52 sec 8.2.3: 'In case twin pipelines are selected for punctual "
                        "obstacle crossing (highway, wadi, ...) the same shall be considered' - "
                        "each pipeline mechanically restrained independently of the other."),
    }


# ======================================================================================
# 10. THE ECONOMICS - and why it changes the answer
# ======================================================================================

@dataclass(frozen=True)
class Economics:
    capital_omr: float
    manning_pv_omr: float
    energy_pv_omr: float
    me_om_pv_omr: float
    pump_replacement_pv_omr: float
    lifecycle_pv_omr: float
    energy_kwh_yr: float
    energy_omr_yr: float
    share_manning: float
    share_energy: float
    qh_product_ls_m: float      # Q_adf (L/s) x total head (m) - the regime coordinate
    qh_crossover_ls_m: float    # where energy cost equals manning cost
    regime: str
    headline: str


def energy_equals_manning(pc: PumpCriteria = PUMP, crit: Criteria = DEFAULT) -> Dict[str, float]:
    """The one number that decides whether energy matters at a station, DERIVED not asserted.

    Annual pumped energy does NOT depend on the pump's duty flow. The pump runs only long
    enough to pass the day's flow, so the running hours fall exactly as the duty rises:

        kWh/yr = P_elec x hours
               = [rho g Q_duty H / (eta_p eta_m)] x [(Q_adf / Q_duty) x 8766]
               = rho g H Q_adf x 8766 / (eta_p eta_m)          <- Q_duty cancels

    So the whole energy bill is set by the AVERAGE FLOW and the TOTAL HEAD, and the regime
    coordinate for a station is the single product  Q_adf (L/s) x H (m).

    Setting the annual energy cost equal to NWS's manning rule (`MANNING_OMR_YR`) gives the
    crossover product returned here. Below it, energy is a rounding error and the design
    should optimise station COUNT. Above it, energy is a real term and a longer, higher route
    chosen to delete a station has to be paid for in the sum rather than waved through.

    THIS REPLACES A CLAIM THIS PROJECT HAS BEEN REPEATING. "Pumping energy is 0.4 % of a
    station's operating cost" is true of the MEDIAN station W10 measured (49 OMR/yr, a few
    L/s at a few metres of lift) and is NOT a general law: at the crossover it is 100 % of
    the manning term, and a large high-head station passes it easily. The share is reported
    per station, and the 0.4 % figure is never quoted as universal.
    """
    # kWh per year per (m3/s of average flow) per (m of head)
    k = 1000.0 * crit.G * 8766.0 / (pc.ETA_PUMP * pc.ETA_MOTOR) / 1000.0     # kW.h units
    omr_per_m3s_per_m = k * pc.TARIFF_OMR_KWH
    product_m4s = pc.MANNING_OMR_YR / omr_per_m3s_per_m           # m3/s x m
    return {
        "kwh_per_yr_per_m3s_per_m": k,
        "omr_per_yr_per_m3s_per_m": omr_per_m3s_per_m,
        "crossover_qadf_ls_x_head_m": product_m4s * 1000.0,
        "manning_omr_yr": pc.MANNING_OMR_YR,
        "note": ("energy cost equals manning cost when Q_adf (L/s) x total head (m) reaches "
                 "this product. Q_duty cancels out of the energy bill entirely."),
    }


def economics(sel: PumpSelection, fl: Flows, st: StationType, fm: ForceMain, *,
              crit: Criteria = DEFAULT, pc: PumpCriteria = PUMP) -> Economics:
    """Life-cycle cost of one station over G201-p96's 25 years at 5 %.

    THE FINDING THIS FUNCTION EXISTS TO PUBLISH, and it changes the design:

        MANNING IS A FLAT 12,000 OMR/YEAR PER STATION, WHATEVER THE STATION'S SIZE
        - {MANNING_PV} OMR of present value at G201-p96's 25 years and 5 %.

    NWS's own PIAD rule is 1,000 OMR/month per pumping station. Because it does not scale
    with duty, the design consequence is direct:

      * FEWER, LARGER STATIONS BEAT MANY SMALL ONES. Halving the station count halves the
        manning bill; doubling a station's duty does not move it at all.
        `consolidation_breakeven()` turns that into a distance - about 1.1 km on provisional
        rates, which is where the project's own rule-9 cascade radius of 1.5 km comes from.
      * THE DISCHARGE CHAMBER IS NOT CHOSEN ON LEAST HEAD. Rank it on `DISCHARGE_LADDER`:
        stations avoided first, commissionability second, receiving capacity and septicity
        next, head LAST.

    AND THE CAVEAT THAT KEEPS THIS HONEST. The often-repeated "pumping energy is 0.4 % of a
    station's cost" is a statement about SMALL stations, not a law - see
    `energy_equals_manning()`. Energy depends on Q_adf x head and nothing else, and it
    equals the manning bill at a product of about
    {CROSSOVER} L/s x m. Below that, optimise station count and ignore head. Above it, a
    consolidation that adds head has to be paid for in the sum. Both regimes are reported on
    every station in `regime`.

    G201-p96 sec 12.3 requires OPEX to include labour, so none of this is an optional
    refinement; it is the guideline's own OPEX definition applied to NWS's own staffing rule.
    """
    # Capital - Cabral et al., on the hydraulic power at the design point.
    p_hyd_kw = 9.81 * fl.q_peak_m3s * sel.head_duty_m
    cap_keur = math.exp(pc.CABRAL_A) * max(p_hyd_kw, 1e-6) ** pc.CABRAL_B
    capital = cap_keur * 1000.0 * pc.EUR_TO_OMR

    # Energy - the pump runs only long enough to pass the day's flow.
    hours = (fl.q_adf_ls / max(sel.duty_all.q_ls, 1e-9)) * 8766.0
    kwh_yr = sel.duty_all.p_electrical_kw * hours
    energy_yr = kwh_yr * pc.TARIFF_OMR_KWH

    pvaf = pc.PVAF
    manning_pv = pc.MANNING_OMR_YR * pvaf
    energy_pv = energy_yr * pvaf
    me_pv = capital * pc.ME_SHARE_OF_CAPITAL * pc.ME_OM_FRAC * pvaf
    # G203-p40 Table 17 gives the pump a 15-year service life inside a 25-year appraisal, so
    # one M&E replacement falls due at year 15.
    repl_pv = (capital * pc.ME_SHARE_OF_CAPITAL) / (1.0 + pc.DISCOUNT) ** crit.PS_SERVICE_LIFE_YR

    total = capital + manning_pv + energy_pv + me_pv + repl_pv

    x = energy_equals_manning(pc, crit)
    qh = fl.q_adf_ls * sel.head_duty_m
    crossover = x["crossover_qadf_ls_x_head_m"]
    if qh < 0.10 * crossover:
        regime = ("SMALL / LOW-HEAD: energy is a rounding error. Optimise STATION COUNT and "
                  "ignore head entirely.")
    elif qh < crossover:
        regime = ("MID: energy is real but below the manning bill. Consolidation still wins "
                  "on manning; check the sum before adding much head.")
    else:
        regime = ("LARGE / HIGH-HEAD: energy EXCEEDS the manning bill. 'Energy is 0.4 %' does "
                  "NOT apply here - a consolidation that adds head must be paid for in the "
                  "sum, not assumed away.")

    head = (
        f"manning {manning_pv/total:.1%} of life-cycle PV, energy {energy_pv/total:.2%}, "
        f"capital {capital/total:.1%}. Manning is {pc.MANNING_OMR_YR:,.0f} OMR/yr WHATEVER "
        f"the station's size ({manning_pv:,.0f} OMR PV), so fewer larger stations beat many "
        f"small ones. Energy regime: Q_adf x head = {qh:,.0f} against a crossover of "
        f"{crossover:,.0f} L/s.m - {regime}")

    return Economics(
        capital_omr=capital, manning_pv_omr=manning_pv, energy_pv_omr=energy_pv,
        me_om_pv_omr=me_pv, pump_replacement_pv_omr=repl_pv, lifecycle_pv_omr=total,
        energy_kwh_yr=kwh_yr, energy_omr_yr=energy_yr,
        share_manning=manning_pv / total, share_energy=energy_pv / total,
        qh_product_ls_m=qh, qh_crossover_ls_m=crossover, regime=regime, headline=head)


def consolidation_breakeven(pc: PumpCriteria = PUMP,
                            conveyance_omr_per_m: Optional[float] = None) -> Dict[str, float]:
    """How far it is worth conveying flow to DELETE a station.

    Deleting a station saves its manning present value outright - `pc.MANNING_PV_OMR`, and
    it does not scale with size. The cost is the conveyance to the surviving station. So:

        break-even length = MANNING_PV / conveyance rate per metre

    At `RM_OMR_PER_M_DN200` this lands near 1.1 km, which is worth noticing: the project's
    own working rule 9 already cascades stations within ~1.5 km, and that rule turns out to
    be within about a third of the cost break-even rather than an arbitrary radius. Both the
    rate and the manning figure are ASSUMPTIONS, so the OUTPUT IS A LENGTH - swap the rate
    and the answer moves transparently.
    """
    rate = conveyance_omr_per_m if conveyance_omr_per_m is not None else pc.RM_OMR_PER_M_DN200
    L = pc.MANNING_PV_OMR / rate
    return {
        "manning_pv_omr_per_station": pc.MANNING_PV_OMR,
        "conveyance_omr_per_m": rate,
        "breakeven_length_m": L,
        "project_rule9_cascade_m": 1500.0,
        "ratio_rule9_to_breakeven": 1500.0 / L,
    }


# ======================================================================================
# 11. DISCHARGE-CHAMBER CHOICE - the gravity-terminal problem
# ======================================================================================

#: The ladder for choosing where a station discharges. It is deliberately NOT "least head".
#:
#: A station that is a gravity TERMINAL has no downstream gravity path to follow, and W11a
#: had no answer for that at all - which is why it published zero rising mains. The ladder:
#:
#:   0. ASK THE NEIGHBOURS FIRST (philosophy sec 5). Before any of this, test whether joining
#:      a neighbouring gravity subnetwork keeps the catchment on gravity. A station avoided
#:      is worth more than any discharge point chosen well.
#:   1. FEWEST STATIONS IN SERIES. A station discharging into another station's catchment
#:      doubles the manning bill for one catchment and puts two failure points in series.
#:      Prefer a chamber whose own route to the works is gravity all the way.
#:   2. COMMISSIONABILITY. A discharge that makes the upstream package independently
#:      buildable earns its place even when the head is higher - philosophy sec 6, and the
#:      only case where objective 4 beats objective 5. NAMA's own 5A-1 is the measured
#:      example (see ASBUILT_STATION).
#:   3. RECEIVING CAPACITY. G203-p55 sec 8.5 puts the main into a MANHOLE, not more than
#:      300 mm above its flow line, so the receiving chamber must have the depth and the
#:      downstream pipe must have the capacity for the pumped peak on top of its own.
#:   4. SEPTICITY. A rising main is anaerobic by definition; its discharge chamber needs a
#:      water seal, forced venting and corrosion-resistant construction (G203-p55 sec 8.5,
#:      G203-p47 sec 7.7). A chamber at the head of a long flat gravity run is the worst
#:      place to put it.
#:   5. ONLY THEN, HEAD - and only in the regime where head is cheap. `energy_equals_manning()`
#:      gives the crossover: energy costs what manning costs at Q_adf (L/s) x head (m) of
#:      about 4,600. Below a tenth of that a route chosen on least head is optimising the
#:      smallest term in the sum; ABOVE it, head is a real cost and the ladder's earlier
#:      rungs have to beat it on the arithmetic rather than on principle.
DISCHARGE_LADDER: Tuple[str, ...] = (
    "0 ask the neighbours - can gravity reach a neighbouring subnetwork instead",
    "1 fewest stations in series",
    "2 commissionability of the upstream package",
    "3 receiving chamber depth and downstream capacity (G203-p55 sec 8.5, 300 mm rule)",
    "4 septicity of the receiving chamber (G203-p55 sec 8.5, G203-p47 sec 7.7)",
    "5 least head - LAST, and only within the regime energy_equals_manning() defines",
)


def rank_discharge(candidates: Sequence[dict], pc: PumpCriteria = PUMP) -> List[dict]:
    """Rank candidate discharge chambers by `DISCHARGE_LADDER`, not by head.

    Each candidate is a dict with at least:
        node        identity
        stations_in_series   int   how many stations the flow passes after this one
        commissions_package  bool  does discharging here make the upstream package standalone
        receiving_ok         bool  depth and capacity are there (G203-p55 sec 8.5)
        static_lift_m        float
        route_length_m       float

    Returns the same dicts, sorted best first, each with a `rank_why` string added.
    """
    out = []
    for c in candidates:
        d = dict(c)
        d["rank_why"] = (
            f"series={d.get('stations_in_series', 0)}, "
            f"commissions={bool(d.get('commissions_package'))}, "
            f"receiving_ok={bool(d.get('receiving_ok', True))}, "
            f"lift={d.get('static_lift_m', 0.0):.1f} m, "
            f"route={d.get('route_length_m', 0.0):.0f} m - ranked on the ladder, and head is "
            "the LAST term because energy is ~0.4 % of life-cycle cost")
        out.append(d)
    out.sort(key=lambda d: (
        int(d.get("stations_in_series", 0)),
        0 if d.get("commissions_package") else 1,
        0 if d.get("receiving_ok", True) else 1,
        float(d.get("route_length_m", 0.0)),          # proxy for capital, ahead of head
        float(d.get("static_lift_m", 0.0)),           # head LAST
    ))
    return out


# ======================================================================================
# 12. THE WHOLE STATION
# ======================================================================================

@dataclass(frozen=True)
class Station:
    """One designed station. Everything the schedule, the drawing and the appraisal need."""

    ident: str
    x: float
    y: float
    ground_m: float
    invert_in_m: float
    flows: Flows
    st_type: StationType
    well: WetWell
    main: ForceMain
    pump: PumpSelection
    siting: Siting
    econ: Economics
    why: str                      # contract.STATION_WHY: cap / veto / economics / commissioning
    land_m2: float
    publishable: bool
    blocking: Tuple[str, ...]
    reporting: Tuple[str, ...]

    def station_row(self) -> dict:
        """The `contract.STATIONS` row, plus short extra design fields (all <= 10 chars)."""
        r = {
            "WHY": self.why,
            "ST_TYPE": self.st_type.name,
            "Q_DUTY_LS": round(self.pump.duty_all.q_ls, 3),
            "LIFT_M": round(max(self.main.static_lift_m, 0.0), 3),
            "N_PROP": round(self.flows.n_prop, 1),
            "Q_ADF_M3D": round(self.flows.q_adf_m3d, 2),
            "GRD_M": round(self.ground_m, 3),
            "LAND_M2": round(self.land_m2, 1),
            # --- extra design fields, undeclared in contract.STATIONS. See TO_MIGRATE.
            "N_DUTY": self.st_type.n_duty,
            "N_STBY": self.st_type.n_standby,
            "Q_PP_LS": round(self.pump.q_per_pump_ls, 3),
            "HEAD_M": round(self.pump.head_duty_m, 3),
            "MOTOR_KW": round(self.pump.motor_rating_kw, 2),
            "NPSHA_M": round(self.pump.npsha_m, 2),
            "NPSHR_MAX": round(self.pump.npshr_max_allowed_m, 2),
            # the flow the main actually sees at its quietest: ONE duty pump running.
            "V_1PUMP": round(self.pump.duty_one.v_main_ms, 3),
            "Q_1PUMP": round(self.pump.duty_one.q_ls, 2),
            # peak / design-minimum on the LITERAL reading of G203-p39 sec 7.4 (e). One main
            # can only span 3.33 (2.5 / 0.75 m/s), so anything above that says the station
            # needs staged or twin mains, not a different diameter.
            "FLOW_RAT": round(self.flows.q_peak_ls / max(self.flows.q_min_initial_ls, 1e-9), 2),
            "KWH_YR": round(self.econ.energy_kwh_yr, 0),
            "LCC_OMR": round(self.econ.lifecycle_pv_omr, 0),
            "PCT_MAN": round(100.0 * self.econ.share_manning, 1),
            "PCT_NRG": round(100.0 * self.econ.share_energy, 2),
        }
        r.update(self.well.as_row())
        r.update(self.siting.as_row())
        return r

    def main_row(self) -> dict:
        r = self.main.as_row()
        r["Q_DUTY_LS"] = round(self.pump.duty_all.q_ls, 3)
        # V_MIN_MS above is the LITERAL reading of G203-p39 sec 7.4 (e) - the Table 16 flow.
        # V_1PUMP is the AS-PUMPED reading: what the main actually sees with one duty pump
        # running, which is the lowest flow a fixed-speed station ever delivers. G203 does
        # not settle which governs, so both are published. See velocity_band_feasibility().
        r["V_1PUMP"] = round(self.pump.duty_one.v_main_ms, 3)
        r["Q_1PUMP"] = round(self.pump.duty_one.q_ls, 2)
        return r


def design_station(ident: str, x: float, y: float, ground_m: float, invert_in_m: float,
                   q_peak_ls: float, q_adf_ls: float, *,
                   main_length_m: float, discharge_ground_m: float,
                   discharge_invert_m: Optional[float] = None,
                   n_prop: float = 0.0, why: str = "cap",
                   material: str = "DI",
                   n_summits: int = 0, n_low_points: int = 0,
                   grids=None, wadi_length_m: float = 0.0,
                   q_avg_initial_ls: Optional[float] = None,
                   crit: Criteria = DEFAULT, pc: PumpCriteria = PUMP) -> Station:
    """Design one station end to end and refuse to publish one that fails a 'shall'.

    STATIC LIFT is measured from the WET WELL's lowest operating water level to the
    DISCHARGE chamber's soffit-entry level, not from ground to ground. G203-p55 sec 8.5
    fixes the top: the main "shall enter the gravity sewer system at a manhole and at a point
    not more than 300 mm above the flow line of the receiving manhole", so the delivery level
    is the receiving invert plus at most 300 mm. The bottom is the pump stop level, which is
    the incoming invert less the live band and the pump submergence.
    """
    if why not in ("cap", "veto", "economics", "commissioning"):
        raise PumpingError(f"WHY must be one of contract.STATION_WHY, got {why!r}")

    fl = flows(q_peak_ls, q_adf_ls, q_avg_initial_ls=q_avg_initial_ls, n_prop=n_prop,
               crit=crit)
    st = station_type(fl.q_peak_ls, crit=crit)

    # provisional per-pump flow to size the well; refined once the duty point is known
    q_pp_ls = fl.q_peak_ls / max(1, st.n_duty)
    well = wet_well(q_pp_ls, st, fl, crit=crit, pc=pc)

    # levels
    stop_level = invert_in_m - well.live_depth_m - 0.30      # 0.30 m submergence allowance
    deliver_level = ((discharge_invert_m if discharge_invert_m is not None
                      else discharge_ground_m - crit.MIN_COVER_CROWN)
                     + crit.FM_TERMINATION_ABOVE_MM / 1000.0)
    static_lift = deliver_level - stop_level

    fm = size_force_main(fl.q_peak_ls, fl, main_length_m, static_lift, material=material,
                         n_summits=n_summits, n_low_points=n_low_points,
                         n_duty=st.n_duty, crit=crit, pc=pc)
    sel = select_pump(fl, st, fm, static_lift,
                      submergence_m=max(0.30, invert_in_m - stop_level),
                      site_level_m=ground_m, crit=crit, pc=pc)
    econ = economics(sel, fl, st, fm, crit=crit, pc=pc)

    if grids is not None:
        sit = site_station(x, y, ground_m, grids, crit=crit, pc=pc)
    else:
        sit = Siting(x=x, y=y, ground_m=ground_m, wet_at_50yr=False, hazard_class_50yr=-1,
                     in_channel=False, scour_risk=False, dry_found=False,
                     dry_distance_m=None, dry_xy=None, publishable=False,
                     verdict="NOT TESTED - no hazard grids supplied. Philosophy sec 8: a "
                             "check that cannot run is a FAILURE, not a blank.",
                     level_test="not run", supplementary={})

    land = st.land_min_m2
    blocking: List[str] = []
    reporting: List[str] = list(fm.notes) + list(sel.notes)

    if not fm.v_max_ok:
        blocking.append(f"force main exceeds {crit.FM_V_MAX} m/s (G203-p50 sec 8.1)")
    # THE UNAMBIGUOUS SELF-CLEANSING GATE. `V_MIN_MS` (the Table-16 reading) fails on almost
    # every main here and is arguable; the velocity at ONE DUTY PUMP RUNNING is not. That is
    # the lowest flow a fixed-speed station ever DELIVERS, so if the main cannot reach
    # 0.75 m/s there it cannot self-cleanse under EITHER reading of G203-p50 sec 8.1, at any
    # diameter, ever. Blocking, and the resolutions are a grinder pump on a 50 mm ID main
    # (G203-p50) or taking the catchment out of the central network (philosophy sec 8a).
    if sel.duty_one.v_main_ms < crit.FM_V_MIN:
        blocking.append(
            f"the rising main runs at {sel.duty_one.v_main_ms:.2f} m/s with one duty pump "
            f"running - the LOWEST flow this station ever delivers - against the "
            f"{crit.FM_V_MIN} m/s self-cleansing floor (G203-p50 sec 8.1). No diameter in the "
            f"series is small enough: DN{fm.dn} is already carrying only "
            f"{sel.duty_one.q_ls:.2f} L/s. This main cannot self-cleanse under EITHER reading "
            "of the clause. Resolutions: a grinder pump on a 50 mm ID main (G203-p50), or "
            "this catchment leaves the central network for a satellite or on-site system "
            "(philosophy sec 8a).")
    if not fm.id_min_ok:
        blocking.append(f"force main below {crit.FM_ID_MIN_MM:.0f} mm ID (G203-p50 sec 8.1)")
    if not sit.publishable:
        blocking.append(sit.verdict)
    if not well.level_sep_ok:
        blocking.append(
            f"wet-well live depth {well.live_depth_m:.2f} m cannot hold {st.n_duty} start "
            f"levels {crit.WELL_LEVEL_SEP_M*1000:.0f} mm apart (G203-p48 sec 7.8)")
    if sel.npsh_ok is False:
        blocking.append(
            f"NPSH margin {sel.npsh_margin_m:.2f} m against the quoted machine, below the "
            f"1.0 m G203-p47 sec 7.6 requires")

    reporting.append(sit.level_test)
    reporting.append(well.retention_flag)
    reporting.append(econ.headline)
    reporting.append(crit.tau_banner())
    if wadi_length_m > 0:
        reporting.append(
            f"force main crosses {wadi_length_m:.0f} m of wadi ground - G201 sec 9.3 register "
            "attached; DI over the crossing plus 15 m each side, MoAFWR approval, PAM-STD-404 "
            "protection, anti-flotation check, no valve chamber or marker post in the bed")

    return Station(ident=ident, x=x, y=y, ground_m=ground_m, invert_in_m=invert_in_m,
                   flows=fl, st_type=st, well=well, main=fm, pump=sel, siting=sit,
                   econ=econ, why=why, land_m2=land,
                   publishable=not blocking, blocking=tuple(blocking),
                   reporting=tuple(reporting))


# ======================================================================================
# 13. BANNER AND SELF-TEST
# ======================================================================================

def banner(pc: PumpCriteria = PUMP, crit: Criteria = DEFAULT) -> str:
    return "\n".join([
        f"W11b pumping {PUMPING_VERSION} - flags that travel with every number below:",
        "  * G203-p38 sec 7.2 governs siting at 1:50, NOT 1:100. The philosophy document's "
        "1:100 is a MIS-CITATION - see PHILOSOPHY_CITATION_DEFECT.",
        "  * the 300 mm-above-flood-LEVEL test CANNOT BE EVALUATED: hazard-class grids, no "
        "water surface. Reported as a failure, never as a blank.",
        "  * NO WET-WELL RETENTION LIMIT EXISTS in G201/G202/G203. The 30-minute figure is "
        "the FORCE MAIN's (G203-p50 sec 8.2.1), adopted as a project comparator.",
        "  * force-main velocity band is 0.75-2.5 m/s (G203-p50). The gravity 3.0 m/s "
        "(G203-p27) is a different clause and is never used here.",
        "  * force-main friction uses G202-p104 Table 21 roughness, not the 1.5 mm gravity "
        f"ks: {pc.eps('DI')*1000:.2f} mm for DI at {pc.FM_DESIGN_AGE_YR} years.",
        f"  * economics: {crit.PS_SERVICE_LIFE_YR}-yr pump life inside G201-p96's "
        f"{pc.LCC_YEARS}-yr / {pc.DISCOUNT:.0%} appraisal. Manning "
        f"{pc.MANNING_PV_OMR:,.0f} OMR PV per station, independent of size.",
        "  * NO built pumping station or force main in this project records a diameter, a "
        "material or a pump duty - nothing here is calibrated against a built asset.",
        "  * " + crit.tau_banner().splitlines()[0],
    ])


def _self_test(verbose: bool = True) -> bool:
    ok = True

    def chk(name, cond, detail=""):
        nonlocal ok
        ok = ok and bool(cond)
        if verbose:
            print(f"  [{'PASS' if cond else 'FAIL'}] {name}{('  ' + detail) if detail else ''}")

    if verbose:
        print(banner())
        print("\n-- criteria echo, read back from the source PDF 2026-09-03 --")
    c = DEFAULT
    chk("G203-p40 Type 1 ceiling 100 L/s", c.PS_TYPE1_MAX_LS == 100.0)
    chk("G203-p40 Type 2 ceiling 300 L/s", c.PS_TYPE2_MAX_LS == 300.0)
    chk("G203-p40 T17 duty pumps 1/2/3", c.PS_DUTY_PUMPS == (1, 2, 3))
    chk("G203-p48 V = 0.25 Q T", c.WELL_K == 0.25)
    chk("G203-p48 min 10 starts/h", c.WELL_STARTS_MIN == 10.0)
    chk("G203-p50 FM max 2.5 m/s (NOT the gravity 3.0)",
        c.FM_V_MAX == 2.5 and c.V_MAX == 3.0)
    chk("G203-p50 FM min 0.75 m/s at design minimum", c.FM_V_MIN == 0.75)
    chk("G203-p50 FM min ID 75 mm", c.FM_ID_MIN_MM == 75.0)
    chk("G203-p38 station flood ARI is 50 yr", c.PS_FLOOD_ARI_YR == 50)
    chk("G201-p96 25 yr at 5 % -> PVAF 14.0939", abs(PUMP.PVAF - 14.09394) < 1e-4,
        f"PVAF = {PUMP.PVAF:.5f}")
    chk("G202-p104 T21 DI roughness is not the gravity 1.5 mm",
        PUMP.eps("DI") == 0.00045 and c.KS == 0.0015,
        f"DI@20yr {PUMP.eps('DI')*1000:.2f} mm vs gravity ks {c.KS*1000:.1f} mm")

    if verbose:
        print("\n-- Table 16 minimum-flow factors, G203-p40 --")
    chk("Table 16 at 50 L/s -> 0.25", abs(c.ps_min_flow_factor(50.0) - 0.25) < 1e-9)
    chk("Table 16 at 5000 L/s -> 0.50", abs(c.ps_min_flow_factor(5000.0) - 0.50) < 1e-9)

    if verbose:
        print("\n-- wet well, G203-p48 --")
    fl = flows(60.0, 18.0)
    st = station_type(fl.q_peak_ls)
    chk("60 L/s peak is Type 1", st.name == "Type 1" and st.n_duty == 1)
    w = wet_well(fl.q_peak_ls / st.n_duty, st, fl)
    hand = 0.25 * 0.060 * 360.0
    chk("V = 0.25 Q T reproduced by hand", abs(w.live_volume_m3 - hand) < 1e-9,
        f"{w.live_volume_m3:.3f} m3")
    chk("start rate below 10/h is refused",
        _raises(lambda: wet_well(60.0, st, fl, starts_per_hour=6.0)))

    if verbose:
        print("\n-- force main, G203-p50 --")
    fm = size_force_main(fl.q_peak_ls, fl, 2000.0, 12.0)
    chk("duty velocity within 2.5 m/s", fm.v_duty_ms <= 2.5, f"{fm.v_duty_ms:.2f} m/s")
    chk("chosen bore at least 75 mm ID", fm.id_m * 1000 >= 75.0, f"DN{fm.dn}")
    # friction sanity: a known-order check against the Darcy form at fully rough flow
    s = friction_slope(0.060, fm.id_m, fm.eps_m)
    chk("friction slope is physical (0.1-100 m/km)", 1e-4 < s < 0.1, f"{s*1000:.2f} m/km")

    if verbose:
        print("\n-- system curve and duty point, G202-p91 --")
    sel = select_pump(fl, st, fm, 12.0)
    chk("duty point sits on the system curve",
        abs(sel.duty_all.head_m - system_head(sel.duty_all.q_ls / 1000.0, 12.0, fm)) < 1e-6)
    chk("one duty pump -> duty flow equals design peak",
        abs(sel.duty_all.q_ls - fl.q_peak_ls) < 0.5,
        f"{sel.duty_all.q_ls:.1f} vs {fl.q_peak_ls:.1f} L/s")
    chk("motor carries the G202-p96 10 % margin",
        sel.motor_rating_kw >= 1.10 * sel.duty_all.p_shaft_kw / st.n_duty - 1e-9)

    if verbose:
        print("\n-- parallel operation is NOT n x single-pump flow --")
    fl2 = flows(200.0, 60.0)
    st2 = station_type(fl2.q_peak_ls)
    fm2 = size_force_main(fl2.q_peak_ls, fl2, 3000.0, 20.0)
    sel2 = select_pump(fl2, st2, fm2, 20.0)
    chk("200 L/s peak is Type 2, 2 duty + 1 standby",
        st2.name == "Type 2" and st2.n_duty == 2 and st2.n_standby == 1)
    gain = sel2.duty_all.q_ls / sel2.duty_one.q_ls
    chk("two pumps in parallel give less than 2.00x one pump", 1.0 < gain < 2.0,
        f"gain {gain:.3f}x")
    chk("parallel duty point equals the design peak",
        abs(sel2.duty_all.q_ls - fl2.q_peak_ls) < 1.0)

    if verbose:
        print("\n-- economics, G201-p96 - TWO REGIMES, not one law --")
    x = energy_equals_manning()
    chk("energy is independent of duty flow (Q_duty cancels)",
        abs(x["crossover_qadf_ls_x_head_m"] - 1000.0 * PUMP.MANNING_OMR_YR /
            (1000.0 * c.G * 8766.0 / (PUMP.ETA_PUMP * PUMP.ETA_MOTOR) / 1000.0
             * PUMP.TARIFF_OMR_KWH)) < 1e-6,
        f"crossover Q_adf x H = {x['crossover_qadf_ls_x_head_m']:,.0f} L/s.m")
    # small station: the regime W10's "energy is 0.4 %" was measured in
    fl_s = flows(8.0, 2.5)
    st_s = station_type(fl_s.q_peak_ls)
    fm_s = size_force_main(fl_s.q_peak_ls, fl_s, 400.0, 4.0)
    sel_s = select_pump(fl_s, st_s, fm_s, 4.0)
    ec_s = economics(sel_s, fl_s, st_s, fm_s)
    chk("SMALL station: manning dominates, energy is a rounding error",
        ec_s.share_manning > 0.60 and ec_s.share_energy < 0.02,
        f"manning {ec_s.share_manning:.1%}, energy {ec_s.share_energy:.3%}, "
        f"{ec_s.energy_omr_yr:,.0f} OMR/yr")
    # large high-head station: the regime the 0.4 % claim does NOT cover
    ec = economics(sel2, fl2, st2, fm2)
    chk("LARGE high-head station: energy is NOT negligible",
        ec.share_energy > 0.05,
        f"manning {ec.share_manning:.1%}, energy {ec.share_energy:.2%} at "
        f"Q_adf x H = {ec.qh_product_ls_m:,.0f} vs crossover {ec.qh_crossover_ls_m:,.0f}")
    chk("manning PV does not move with station size",
        abs(ec.manning_pv_omr - ec_s.manning_pv_omr) < 1e-6,
        f"{ec.manning_pv_omr:,.0f} OMR on both")
    if verbose:
        print('\n-- the velocity band, and why no diameter fixes it --')
    vb = velocity_band_feasibility(fl2, q_single_pump_ls=sel2.duty_one.q_ls)
    chk("one main spans a flow ratio of exactly V_max / V_min",
        abs(vb["single_main_max_flow_ratio"] - c.FM_V_MAX / c.FM_V_MIN) < 1e-12,
        f"{vb['single_main_max_flow_ratio']:.3f} = {c.FM_V_MAX} / {c.FM_V_MIN}")
    chk("the LITERAL reading is infeasible on this project's flow regime",
        not vb["feasible_reading_A"],
        f"peak / design-min ratio {vb['ratio_reading_A_literal']:.1f} vs a limit of "
        f"{vb['single_main_max_flow_ratio']:.2f}")
    chk("the AS-PUMPED reading is feasible (a fixed-speed pump delivers its duty)",
        vb["feasible_reading_B"],
        f"one pump {sel2.duty_one.q_ls:.1f} L/s at {sel2.duty_one.v_main_ms:.2f} m/s, "
        f"ratio {vb['ratio_reading_B_as_pumped']:.2f}")

    if verbose:
        print('\n-- the whole-life size comparison G203-p50 requires --')
    dn_best, tbl = optimise_force_main(fl2.q_peak_ls, fl2, 3000.0, 20.0)
    chk("the comparison considers more than one size", len(tbl) > 1, f"{len(tbl)} sizes")
    chk("the chosen size minimises capital + energy PV",
        dn_best == min(tbl, key=lambda r: r["whole_life_omr"])["DN"],
        f"DN{dn_best}; smallest legal would be DN{tbl[0]['DN']}")
    chk("sizes above the DN600 rate table are flagged as extrapolated",
        all(r["rate_extrapolated"] for r in tbl if r["DN"] > 600))

    be = consolidation_breakeven()
    chk("consolidation break-even is a plausible distance",
        500.0 < be["breakeven_length_m"] < 5000.0,
        f"{be['breakeven_length_m']:,.0f} m vs project rule 9's 1,500 m")

    if verbose:
        print("\n-- the as-built calibration case --")
    ab = ASBUILT_STATION
    chk("built main has NEGATIVE static lift", ab["static_lift_m"] < 0,
        f"{ab['static_lift_m']} m over {ab['main_length_m']:,.0f} m")
    fall_mm_m = ab["ground_fall_per_km"]
    chk("ground fall is below the DN200 Table 11 minimum",
        fall_mm_m < c.table11(200) * 1000.0,
        f"{fall_mm_m:.2f} mm/m ground vs {c.table11(200)*1000:.2f} mm/m minimum -> a gravity "
        f"DN200 sinks {(c.table11(200)*1000 - fall_mm_m) * ab['main_length_m'] / 1000:.1f} m "
        "over that route. THAT is why NAMA pumped.")

    if verbose:
        print("\n-- refusals --")
    chk("zero peak flow is refused", _raises(lambda: flows(0.0, 1.0)))
    chk("average above peak is refused", _raises(lambda: flows(10.0, 20.0)))
    chk("an unknown WHY is refused",
        _raises(lambda: design_station("X", 0, 0, 100, 98, 10, 3, main_length_m=100,
                                       discharge_ground_m=95, why="because")))
    chk("an unknown force-main material is refused",
        _raises(lambda: PUMP.internal_diameter(200, "concrete")))

    if verbose:
        print(f"\n{'ALL PASS' if ok else 'FAILURES ABOVE'}")
    return ok


def _raises(fn) -> bool:
    try:
        fn()
    except Exception:
        return True
    return False


if __name__ == "__main__":
    raise SystemExit(0 if _self_test() else 1)
