"""sewnet.criteria — the ONLY place numeric design values live (CLAUDE.md: no invented metrics).

Every value cites its source: G203-p## = PAM-GUD-203, G1-p## = PAM-GUD-201,
02 = _BRAIN/02_DESIGN_CRITERIA.md, A9 = W3/analysis/A9_criteria_audit.md.
Values whose source is pending/assumed are grouped under ASSUMPTIONS and must be
reported as such in every deliverable.
"""

import math

# ---------------------------------------------------------------- hydraulics
G = 9.81                 # m/s2
KS = 0.0015              # m  — Colebrook-White roughness, all sizes/materials (G203-p24, p28)
NU = 1.141e-6            # m2/s — kinematic viscosity @15 C, conservative (G203-p25)

V_SELF_CLEANSING = 0.75  # m/s at peak flow, minimum (G203-p26)
V_PREFERRED = 0.90       # m/s preferred (G203-p26)
V_MAX = 3.0              # m/s at design depth of flow (G203-p27); max gradient governed by this (p29)

DOD_MAX_SMALL = 0.65     # d/D at peak, D <= 350 (G203-p27 Tab 10)
DOD_MAX_LARGE = 0.50     # d/D at peak, D > 350 (G203-p27 Tab 10)
DOD_DN_THRESHOLD = 350

# G203-p29 Tab 11 — minimum gradients (m/m), secondary network, CW @ 0.75 m/s, ks 1.5 mm.
# The hydra test gate reproduces these from the CW equation (±5%) before any design runs.
TABLE11 = {200: 0.00500, 250: 0.00375, 315: 0.00270, 400: 0.00205, 500: 0.00155,
           600: 0.00125, 700: 0.00100, 800: 0.00085, 900: 0.00075}
TABLE11_FLOOR = 0.00075  # ">= DN900: 0.75 mm/m" (G203-p29)

DN_SERIES = [200, 250, 315, 400, 500, 600, 700, 800, 900, 1000, 1200]  # design ladder;
# DN interpreted as internal diameter — the interpretation under which Table 11 reproduces (verified in tests).

DN_MIN_MAIN = 200        # OD200 minimum main sewer (G203-p22 Tab 6)

# Tractive-force minimum gradient at low-flow heads (G203-p27 §4.2.2.1, A9-corrected form):
# Smin = K * tau^1.23 * Q^-0.461, Q in m3/s
TRACTIVE_K = 2.33e-4

# ---------------------------------------------------------------- manholes / depth
# Max spacing by DN (G203-p30 Tab 12): DN200-315: 100 m; 350-900: 120; 1000-1400: 150; >1400: 200
def mh_max_spacing(dn):
    if dn <= 315: return 100.0
    if dn <= 900: return 120.0
    if dn <= 1400: return 150.0
    return 200.0

MH_SPLIT_LEN = 100.0     # initial split length — satisfies every spacing class (conservative)

DROP_TRIGGER = 0.60      # m invert difference at a manhole -> backdrop required (G203-p30)
BACKDROP_MAX = 2.0       # m external backdrop max; beyond -> vortex drop shaft (G203-p30 §4.4, A9)

MIN_COVER_CROWN = 1.3    # m to crown (G203-p33 §4.6.3); <1.3 needs concrete protection — not designed here
MAX_DEPTH = 12.0         # m cover; beyond -> pumping (G203-p33) -> SLS pocket per CLAUDE.md rule 9
FALL_TOLERANCE = 0.040   # m — 2 x 20 mm construction line/level tolerance; pipes with less total
                         # fall are flagged reverse-gradient construction risk (G203-p29 §4.3.1, A9)

# SLS consolidation (CLAUDE.md rule 9 / G203-p33)
SLS_MIN_PLOTS = 50
SLS_CASCADE_M = 1500.0

# ---------------------------------------------------------------- tertiary (G203 p17-19, Tab 4-6)
PCS_MIN_SLOPE = 0.03     # property connection sewer 3-10 % (G203-p18 Tab 5)
PCS_MAX_SLOPE = 0.10
PCS_MAX_LEN = 50.0       # m, maintenance limit (G203-p18 Tab 4 note, A9)
PCS_MIN_COVER = 0.60     # m (G203-p19 §3.5)
RIDER_MIN_SLOPE = 0.01   # rider/lateral 1-10 % (G203-p18 Tab 5)
LATERAL_MAX_LEN = 45.0   # m (G203-p22 Tab 6, §3.2 p17)
MAX_HCC_PER_RIDER = 3    # (G203-p19 §3.4, A9)
DN_TERTIARY = 160        # OD160 PCS/rider minimum (G203-p22 Tab 6)

# ---------------------------------------------------------------- loads (G1 + PROJECT-STATE §2)
LPCD_WATER = 164.0       # l/c/d Adh Dhahirah domestic water (G1-p59-60 Tab 11)
RETURN_DOM = 0.85        # (G1-p70-71 Tab 19)
WWG_LCD = 171.3          # l/c/d area-average wastewater incl. Tier-A ND+Gov uplift (T01 Step 3; G1-p70-71)
INFILT_L_D_KM = 720.0    # L/d per km of sewer, new networks (G1-p72-73) — added UNPEAKED [Likely, kickoff item]

def pf_merrimack(qadf_mld):
    """Peak factor, Merrimack: Qpdf = 2.65 * Qadf^0.879, both Ml/d (G1-p71 — mandatory >100 properties)."""
    if qadf_mld <= 0: return 1.0
    return 2.65 * qadf_mld ** 0.879 / qadf_mld

def pf_peltier(qm_ls):
    """Peak factor, Peltier IMP2024: 1.5 + 1/sqrt(Qm), Qm in L/s (G1-p72 — comparison column)."""
    if qm_ls <= 0: return 1.0
    return 1.5 + 1.0 / math.sqrt(qm_ls)

PF_HOLD_PROPERTIES = 100  # below 100 properties no formula is prescribed (G1-p71); METHOD CHOICE:
                          # hold PF constant at its 100-property value instead of letting
                          # Merrimack blow up as Q -> 0. Reported, not hidden.
PF_REPORT_ABOVE = 5.0     # recommendation only — never truncate, always report (G1-p72 NOTE, A9)

def material(dn):
    """Open-trench material by DN (G203-p22 Tab 6 / p23 Tab 7, conservative PVC-U cap 250)."""
    return "PVC-U" if dn <= 250 else "GRP"

MANNING_N_EXPORT = 0.010  # PVC/GRP mid-range (G203-p23 Tab 8) — SewerGEMS export field only; design uses CW

# ---------------------------------------------------------------- ASSUMPTIONS (tagged, must appear in reports)
ASSUMPTIONS = {
    "TAU_PA": (1.0, "design tractive stress Pa — GUD-203 gives NO numeric value (GAP-9); "
                    "Mara et al. literature basis; confirm with NWS"),
    "OCCUPANCY": (6.0, "persons/property — GAP-5 fallback (NCSI housing units missing)"),
    "PROPS_PER_PLOT": (1.0, "properties per plot — GAP-5"),
    "PLOT_OUTLET_DEPTH": (0.60, "house drain leaves the plot this deep below plot ground — method choice"),
    "CONN_CHECK_SLOPE": (0.02, "blended PCS/rider fall requirement for the plot-connectability check "
                               "(PCS 3% + rider 1% averaged) — method choice"),
    "WALL_ALLOW": (0.05, "pipe wall+bedding allowance added below crown cover when setting invert depth "
                         "— method choice, conservative direction"),
    "MH_SIZES": ("DN1000 to 3 m / DN1200 to 6 m / DN1500 deeper", "manhole internal sizes vs depth — "
                 "ABSENT from 02; typical ladder until GUD-203 §4.4 re-extract; no hydraulic effect at concept"),
    "RIDER_DISCHARGE": ("nearest manhole", "rider discharge point — ABSENT from 02; assumed to nearest MH"),
    "KERB_RULES_GRAVITY": ("applied", "in-carriageway >=1 m from kerb / MH >=0.5 m from kerb is a "
                           "force-main clause (G203-p51) applied to gravity as inference (A9)"),
}
TAU_PA = ASSUMPTIONS["TAU_PA"][0]
OCCUPANCY = ASSUMPTIONS["OCCUPANCY"][0]
PROPS_PER_PLOT = ASSUMPTIONS["PROPS_PER_PLOT"][0]
PLOT_OUTLET_DEPTH = ASSUMPTIONS["PLOT_OUTLET_DEPTH"][0]
CONN_CHECK_SLOPE = ASSUMPTIONS["CONN_CHECK_SLOPE"][0]
WALL_ALLOW = ASSUMPTIONS["WALL_ALLOW"][0]

# Per-plot saturation average dry-weather flow (PROJECT-STATE §2: EVERY plot at saturation;
# CLASS=A farms carry NO sewage load)
PLOT_QADF_M3D = OCCUPANCY * PROPS_PER_PLOT * WWG_LCD / 1000.0   # = 1.028 m3/d/plot
PLOT_QADF_LS = PLOT_QADF_M3D * 1000.0 / 86400.0                 # = 0.0119 L/s/plot


def invert_depth_min(dn):
    """Minimum invert depth below ground: crown cover + internal D + wall/bedding allowance."""
    return MIN_COVER_CROWN + dn / 1000.0 + WALL_ALLOW
