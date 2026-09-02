"""W11a stage 1 - SCOPE, as a system choice. Every settlement gets a servicing system.

WHAT THIS STAGE IS FOR
----------------------
Philosophy sec 2 puts "what is served" at step 1, before corridors, before the trunk, before
anything is levelled: "deciding scope after design is how you sewer empty desert." W10 did it
the other way and the bill is measurable - 1,882.9 km designed, then 117.3 km discovered to
collect nothing and convey nothing, 55 of 239 depth breaches and 832 m of the 3,083 m of lift
(27.0 %) sitting on pipe with no load-bearing plot within 60 m. None of that was a hydraulic
error. It was pipe laid to places nobody had decided to serve.

THE FAILURE THIS STAGE PREVENTS, NAMED
--------------------------------------
Two of them, and they pull in opposite directions:

  1. W10's, above: scope discovered after the design, so the design pays for it.
  2. The correction to the correction. W10's research answered "what should we sewer?" with
     a tranche called "3 - do not sewer": 31 settlements, 219 properties, 44.7 km. That is a
     SCOPE CUT and it is illegal here. Scope p4 item 3 - "All plots open and build up shall
     be designed and serviced including these plots located in existing areas" - and p6
     item 2 and p8 item 17 leave no discretion. Philosophy sec 8a withdrew it explicitly:
     "An earlier working assumption in this file said 'do not sewer the 31' - that was wrong
     against the TOR and is withdrawn."

So this stage answers a DIFFERENT question from W10's. Not "which settlements do we sewer"
but "which SYSTEM serves each settlement". Nothing is dropped. A settlement costing 204 m of
exclusive sewer per property is not deleted; it is served on-site under G201 p83, which is
also what it has today (G203 p17: "It is common practice on existing properties to install
the PC chamber within the property immediately upstream of the sewage holding (or septic)
tank"). The output layer therefore has no "not served" state, and the stage FAILS LOUDLY if
one appears.

THE INSTRUMENT, AND WHY IT IS THE ONE THE GUIDELINE ASKS FOR
------------------------------------------------------------
G201 p80 sec 8.1 defines a Remote Area by four alternative tests. Measured against the 187
settlements here, three of them do not discriminate:

    under 500 residents OR under 100 plots  ->  180 of 187 settlements, because the cadastre
                                                fragments into one- and two-plot pieces
    25 km or more from the built network    ->  1 settlement, because Ibri is compact
    not connected to a centralised network  ->  every settlement; nothing is connected yet

The operative test is the fourth - "geographical barriers preventing economical connection"
- and G201 p80 sec 8.2.1 states the objective as "optimize capital and operational
expenditures". That hands the decision to the economics, and G201 p96 sec 12.4 says how:
NPV over 25 years at 5 %. The project holds no unit rates yet (Renardet's own cost data is
still coming), so a full NPV cannot be run today. What CAN be measured is the physical
quantity the NPV is almost entirely a function of: the metres of sewer that exist ONLY for
that settlement, per property served.

That ratio is additive - every metre belongs to exactly one settlement or to the shared
trunk - and it breaks cleanly. 106 settlements sit under 20 m/property and hold 99.1 % of
the properties at 13.8 m each; 48 sit above it and hold 0.9 % of the properties on 65.8 km.
The largest settlement anywhere near the break is BAT at 17.6 m/property; the first above it
is a two-plot pocket at 20.0. WHAT_TO_SEWER sec 4 swept it: "moving the cut between about 18
and 25 m per property changes the answer by a handful of properties either way." That sweep
is reproduced here as the confidence grade - a settlement inside the 18-25 band is
provisional, not settled, and says so on its own row.

WHERE THE RATIO COMES FROM, AND WHY THAT IS FLAGGED
---------------------------------------------------
The exclusive-metres figure is measured on W10's flow tree, and W10 IS NOT ISSUABLE. It is
used here as a RANKING instrument, not as a quantity: the question it answers is "which
settlements are expensive relative to the others", and that ordering is a property of where
the settlements sit, not of whether W10 laid its pipes at a legal cover. Every row carries
it as M_PER_PRP with CONFIDENCE, and stage 2 (corridors) and stage 3 (hierarchy) must
recompute it on W11a's own network before the options appraisal prices anything. If the
recomputed ratio moves a settlement across the break, this stage re-runs; it is cheap.

WHAT IT DOES NOT DO
-------------------
No pipe is routed, no works is sized and no NPV is run. It produces one polygon layer -
one row per settlement - naming the system, the works type that system implies under the
guideline's own size bands, the number that decided it, the alternative it was compared
against, and what the decision is still waiting on. It is not a network layer, so it carries
no US_NODE/DS_NODE; the graph starts at stage 2.

THE ONE DELIBERATE NON-DECISION
-------------------------------
BAT. 1,740 plots, ~2,234 properties, 1,752 m3/d, 22-25 km from the built network - above
every decentralised ceiling in the guidelines (G201 p83 and G203 p96 both stop at 5,000
inhabitants / ~750 m3/d; G203 p101 stops constructed wetlands at 500 m3/d / 4,000 PE), so
its local option is a small conventional works rather than a package plant. The cost test
alone says connect it (17.6 m/property, comfortably under the break). Philosophy sec 8a:
"Do not choose - carry both, conveyance and a satellite works, into the options appraisal."
So BAT's rows carry SYSTEM = central as the working assumption AND BOTH = 1 with
ALT_SYS = satellite, and the appraisal decides. Deciding it here would pre-empt the
appraisal, which is the one thing sec 8a forbids.

A CORRECTION TO AN INHERITED CLAIM, MEASURED
--------------------------------------------
WHAT_TO_SEWER sec 6 says "AL DIREZ is the west leg" and reasons from WEST_LEG.md that it
cannot reach the works by gravity. That is wrong on the geometry and this stage checks it
rather than repeating it. AL DIREZ (SID 116) spans E 455,549-471,257 - the EASTERN side of
the wilayat, 15.0 km from the west closed basin's low point at 442,092 E 2,569,064 N. The
west basin lies INSIDE the core conurbation (SID 18, which spans E 436,769-473,002). So the
west leg is not a settlement-scope question at all: it is a sub-catchment of the central
system that cannot reach the works by gravity, and it belongs to the trunk and the stations,
stages 3 and 5. The check is run every time (see `check_west_basin`) so the claim cannot
quietly come back.

RE-RUNNABLE, AND WRITES NOWHERE BUT W11a
----------------------------------------
Reads W10/ and the client SHP/ read-only; writes only under W11a/. Running it twice produces
the same layer. If an input is missing it prints what it is waiting for and exits 0 rather
than half-writing a layer - a stage that dies mid-publish leaves the next stage reading a
file that looks finished.

    python W11a/py/s1_scope.py

Sources, all quoted from the page: G201 p80 sec 8.1 / 8.2.1 (remote-area definition and
objective), G201 p83 sec 8.4.1-8.4.2 (septic, holding tanks, package plants 50-5,000 pe),
G201 p84 (0.8 kWh/m3, O&M 5 % of CAPEX), G201 p96 sec 12.4 (NPV, 25 years, 5 %),
G203 p96 sec 10.5.1.6 (package plants up to 5,000 inhabitants ~ 750 m3/day), G203 p101
(constructed wetlands up to ~500 m3/d / 4,000 PE), G203 p17 sec 3 (the on-site baseline).
Project: TOR scope p4 item 3, p6 item 2, p8 item 17, p12; _BRAIN/08_DESIGN_PHILOSOPHY.md
sec 2, 8a; W10/docs/research/WHAT_TO_SEWER.md sec 4 and 6 (the measured break and the
tranche tables); W10/docs/WEST_LEG.md.
"""
from __future__ import annotations

import os
import sys
import warnings
from dataclasses import replace

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))          # .../W11a/py
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from w11a import contract as K                             # noqa: E402  the shared contract

import geopandas as gpd                                    # noqa: E402  (K imports it hard)
from shapely.geometry import Point                         # noqa: E402
from shapely.ops import unary_union                        # noqa: E402

warnings.filterwarnings("ignore")
try:                       # Arabic and typographic characters exist in the client data
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

STAGE = "S1"
ORDER = 1

BASE = os.path.dirname(os.path.dirname(K.REPO_ROOT))       # .../2621 Ibri Sewer STP
W10 = os.path.join(K.REPO_ROOT, "W10")
OUT_RUN = os.path.join(K.W11A_ROOT, "run")

# ---------------------------------------------------------------------------------------
# Inputs. Read-only, every one of them.
# ---------------------------------------------------------------------------------------
IN_PLOT_LOADS = os.path.join(W10, "shp", "W10_plot_loads.gpkg")     # layer 'plot_loads'
IN_MARGINAL = os.path.join(W10, "shp", "W10_marginal_branches.shp")
IN_EXISTING = os.path.join(W10, "shp", "W10_existing_built.shp")
IN_SETTLE_CSV = os.path.join(W10, "run", "r5_settlements.csv")
IN_TOWNS = os.path.join(BASE, "Hydraulic", "SHP", "Towns", "Towns.shp")
IN_BOUNDARY = os.path.join(BASE, "Hydraulic", "SHP", "Study area", "Project Boundary.shp")

# ---------------------------------------------------------------------------------------
# Constants. Every one is quoted from a page or measured in a cited note. None is invented.
# ---------------------------------------------------------------------------------------

SETTLE_BUFFER_M = 60.0
# The settlement definition, reproduced EXACTLY from W10/py/research/r5_marginal.py so the
# SIDs in WHAT_TO_SEWER (BAT is 165/184/182, the core is 18) still mean what the note says.
# Verified on this data: 187 clusters, and plot and property counts identical to
# r5_settlements.csv on all 187 rows. Settlements are geometric because VILLAGE_EN is blank
# on 43,557 of 61,272 plots and cannot carry the analysis. NOTE the buffer is applied to
# EACH plot, so two plots merge at a 120 m gap - the note's phrase "plots within 60 m of
# each other" understates it. Kept as-is: matching W10's SIDs is worth more than tidying
# the wording, and the 60/120 m sweep (WHAT_TO_SEWER sec 2) is what justified the value.

BREAK_M_PER_PROP = 20.0
# The cost break, MEASURED not chosen - WHAT_TO_SEWER sec 4. Read off the gap in the
# distribution of 187 settlements: 106 below it holding 99.1 % of properties at 13.8 m
# each, 48 above holding 0.9 % on 65.8 km. It is the operationalisation of G201 p80's
# fourth remote-area test, "geographical barriers preventing economical connection", which
# is the only one of the four that discriminates on this data.

FLIP_BAND = (18.0, 25.0)
# WHAT_TO_SEWER sec 4: "moving the cut between about 18 and 25 m per property changes the
# answer by a handful of properties either way, which is what makes 20 a safe place to cut
# rather than an arbitrary one." A settlement inside this band is decided PROVISIONALLY.

PKG_MIN_POP = 50.0        # G201 p83 sec 8.4.1 - package plants "for communities with a
PKG_MAX_POP = 5000.0      # population between 50-5,000 inhabitants". Below 50 the
                          # guideline's answer is a septic or holding tank, not a plant.
PKG_MIN_Q_M3D = 7.5       # the 50-inhabitant floor expressed as a flow, using the
                          # guideline's OWN implied per-head figure: G203 p96 states the
                          # pair "5,000 inhabitants (approx. 750 m3/day)", i.e. 150 L/pe/d,
                          # and 50 pe x 150 L = 7.5 m3/d. NOT used to decide - the floor is
                          # stated in inhabitants and is applied in inhabitants - but a
                          # settlement under 50 people carrying more than this has
                          # non-domestic load, and the tanker service is sized on the flow.
                          # (The project's own domestic figure is 164 L/c/d water at 85 %
                          # return, 02_DESIGN_CRITERIA sec 11.1, G1-p59-60 Tab 11.)
PKG_MAX_Q_M3D = 750.0     # G203 p96 sec 10.5.1.6 - package plants "typically serve
                          # populations up to 5,000 inhabitants (approx. 750 m3/day)". The
                          # population and the flow ceiling are the SAME ceiling stated two
                          # ways; both are tested because our m3/d comes from properties and
                          # land use, not from the population, so they can disagree.
WETLAND_MAX_Q_M3D = 500.0 # G203 p101 - constructed wetlands "only recommended to be applied
                          # in small STPs in rural areas (approximately up to 500 m3/day
                          # and/or 4000 PE)". Reported, not decided here: it is a treatment
                          # process choice inside the satellite option, for stage 4.

G201_REMOTE_KM = 25.0     # G201 p80 sec 8.1, second bullet
G201_MAX_POP = 500.0      # G201 p80 sec 8.1, third bullet
G201_MAX_PLOTS = 100      # G201 p80 sec 8.1, third bullet

ZERO_LOAD_Q = 0.01        # a settlement carrying less than this m3/d has no load at all;
ZERO_LOAD_PROP = 0.01     # the threshold is numeric noise, not a design value

WORKS_TYPE = ("central STP", "package plant", "local works", "septic/tanker")


# ---------------------------------------------------------------------------------------
# The layer specification.
#
# `contract.py` has no LayerSpec for a servicing layer - it declares the eight layers the
# design graph produces, and scope is decided before the graph exists. The contract's own
# EXCLUDED register refuses "a per-stage schema", and it is right to: an unspecified layer
# is one the auditor will never read. So the spec is declared HERE, in full, with the same
# Field objects the contract uses for the fields it already owns, and registered into
# contract.LAYERS - and if the contract ever grows its own `servicing` spec, THAT one wins
# (see `register_spec`). This is flagged on every run, not buried: it is a contract gap and
# it should be folded into contract.py.
#
# CONFIDENCE and STAGE are the contract's own Field objects with only `why` restated - a
# settlement envelope has no corridor under it, so the corridor wording would be a lie while
# the name, dtype, enum and audit id must not drift. SRC is deliberately ABSENT: it is a
# corridor-provenance enum (draft / auto_road / auto_block / auto_link / main_pipe /
# existing) and no value in it is true of a settlement envelope derived from the cadastre.
# A field carrying a false value is worse than a field that is not there.
# ---------------------------------------------------------------------------------------

def _prov_field(name: str, why: str):
    """Take the contract's own Field and restate only its `why`."""
    for spec in (K.CORRIDORS, K.NODES, K.REACHES):
        f = spec.field(name)
        if f is not None:
            return replace(f, why=why)
    raise K.ContractError(f"contract has no field '{name}' to inherit")


SERVICING = K.LayerSpec(
    name="servicing",
    geom="Polygon",
    key="SET_ID",
    audited=False,
    purpose=(
        "One row per settlement, naming the SYSTEM that serves it. Philosophy sec 2 step 1 "
        "and sec 8a: the TOR (scope p4 item 3) requires every plot to be SERVICED, so this "
        "layer has no 'not served' state - the choice is central network, satellite works "
        "or on-site, and a settlement that costs 204 m of exclusive sewer per property is "
        "served by the system that suits it rather than deleted. It exists because W10 "
        "designed 1,882.9 km and then discovered that 117.3 km of it collected nothing and "
        "27 % of its pumping lift served nothing."
    ),
    fields=(
        K.F("SET_ID", "str", "-", "identity, S### carrying W10's SID so the settlements "
            "named in WHAT_TO_SEWER (BAT = 165/184/182, core = 18) stay traceable"),
        K.F("W10_SID", "int", "-", "the W10 SID as an integer, for joining to "
            "r5_settlements.csv and r6_tranches.csv", lo=0),
        K.F("NAME", "str", "-", "settlement name: the majority VILLAGE_EN of its plots, "
            "else the Towns polygon it sits in, else '-'. VILLAGE_EN is blank on 43,557 of "
            "61,272 plots, which is why settlements are geometric and not named"),
        K.F("TOWN", "str", "-", "the Towns polygon containing the settlement centroid; "
            "blank where it sits outside all 25", blank_ok=True),
        K.F("SYSTEM", "str", "-", "the system that serves it. 'unserved' is in the enum "
            "only so a violation can be recorded - the TOR forbids it and self_check() "
            "fails the run if any row carries it", allowed=K.SYSTEM),
        K.F("WORKS", "str", "-", "the works that system implies under the guideline's own "
            "size bands: package plant 50-5,000 pe (G201 p83, G203 p96 ~750 m3/d), a local "
            "conventional works above that, septic or holding tank below 50 pe (G201 p83)",
            allowed=WORKS_TYPE),
        K.F("ALT_SYS", "str", "-", "the alternative this row was compared against, so a "
            "decision can be re-opened without re-deriving what it beat. Blank only where "
            "no alternative exists (the core conurbation)", allowed=K.SYSTEM, blank_ok=True),
        K.F("BOTH", "int", "0/1", "1 = BOTH systems are carried into the options appraisal "
            "and this stage refuses to choose (philosophy sec 8a, BAT). SYSTEM then holds "
            "the working assumption, not a decision", lo=0, hi=1),
        K.F("DEC_RULE", "str", "-", "which rule decided it, by its source: CORE / COST / "
            "G201-p83 / G203-p96 / ZERO-LOAD / PHIL-8a"),
        K.F("WHY", "str", "-", "the decision in one sentence, including what it was "
            "compared against. Never blank"),
        K.F("M_PER_PRP", "float", "m/prop", "THE NUMBER THAT DECIDED IT: metres of sewer "
            "existing only for this settlement, per property. Measured on W10's flow tree "
            "(NOT ISSUABLE) and used as a RANKING instrument only - stage 3 must recompute "
            "it on W11a's own network. -1 where no property exists to divide by", lo=-1.0),
        K.F("M_PER_M3D", "float", "m/(m3/d)", "the companion ratio; it matters where a "
            "settlement has many plots and little load. -1 where there is no load", lo=-1.0),
        K.F("BREAK_M", "float", "m/prop", "the threshold M_PER_PRP was compared against, "
            "stored on the row so the decision can be reproduced when the threshold moves",
            lo=0.0),
        K.F("MARGIN_M", "float", "m/prop", "M_PER_PRP - BREAK_M. Negative = central by "
            "cost. The distance from the cliff edge, which is what a sensitivity reads",
            blank_ok=True),
        K.F("EXCL_KM", "float", "km", "exclusive sewer length, W10-measured. The numerator "
            "of M_PER_PRP, carried so the ratio is never the only trace", lo=0.0),
        K.F("N_PLOT", "int", "-", "plots in the settlement (contract name, as on corridors "
            "and packages)", lo=0),
        K.F("N_PROP", "float", "-", "properties (electricity accounts, 1.456 per plot "
            "average) - the contract's name on connections", lo=0.0),
        K.F("POP", "float", "-", "people at saturation, N_PROP x OR 5.32", lo=0.0),
        K.F("Q_ADF_M3D", "float", "m3/d", "average dry-weather flow at saturation - the "
            "contract's name on connections", lo=0.0),
        K.F("N_OUTBND", "int", "-", "plots with IN_BND = 0. TOR scope p6 covers plots "
            "WITHIN the project boundary; 44 records sit outside carrying 25.9 m3/d, which "
            "is exactly the difference between the 74,701 m3/d in the source layer and the "
            "74,675 m3/d the project publishes. Kept and counted, never dropped", lo=0),
        K.F("KM_CORE", "float", "km", "envelope-to-envelope distance to the core "
            "conurbation - the conveyance a connection actually needs", lo=0.0),
        K.F("KM_BUILT", "float", "km", "envelope-to-envelope distance to the BUILT 2006 "
            "network, the G201 p80 25 km test. Envelope distance, not centroid distance as "
            "r5 used: the test asks how far the settlement is, not its middle", lo=0.0),
        K.F("REMOTE", "int", "0/1", "G201 p80 sec 8.1 size-or-distance test. 1 on 180 of "
            "187 settlements, which is why it cannot be the deciding test", lo=0, hi=1),
        K.F("PKG_OK", "int", "0/1", "package-plant eligible: 50-5,000 pe (G201 p83) AND "
            "under 750 m3/d (G203 p96)", lo=0, hi=1),
        K.F("MARG_KM", "float", "km", "marginal-branch pipe (the 1 m3/d tree, "
            "W10_marginal_branches.shp) lying inside this envelope", lo=0.0),
        K.F("LIFT_M", "float", "m", "static lift on those marginal branches - what the "
            "system choice removes from the central network. TOR scope p12 requires pumping "
            "to be avoided as far as practically possible, so this is a scope output, not "
            "a footnote", lo=0.0),
        K.F("N_LIFT", "int", "-", "lifting stations on those branches", lo=0),
        K.F("PENDING", "str", "-", "what this decision is still waiting on - the NPV, the "
            "unit rates, the land-use delivery, or NWS. Blank where nothing is pending",
            blank_ok=True),
        _prov_field("CONFIDENCE", "how firm the system choice is. 'derived' where the "
                    "measured ratio settles it clear of the 18-25 m/property sweep; "
                    "'provisional' inside that band, on a zero-load settlement, or where "
                    "both options are carried. Nothing here is 'surveyed' or 'drafted'"),
        _prov_field("STAGE", "the stage that wrote this row (invariant 10, audit G4)"),
    ),
)


def register_spec() -> bool:
    """Put SERVICING into contract.LAYERS unless the contract already owns one.

    Returns True if this module supplied the spec - which is a contract gap worth printing,
    not a success. A layer whose schema lives in the stage that writes it is exactly the
    drift EXCLUDED's "a per-stage schema" entry warns about; the difference here is that the
    spec is complete, declared before any row is built, and validate() still gates the write.
    """
    if "servicing" in K.LAYERS:
        return False
    K.LAYERS["servicing"] = SERVICING
    return True


# ---------------------------------------------------------------------------------------
# Published numbers. P2: one function per published quantity, and no second definition.
# ---------------------------------------------------------------------------------------

@K.published("settlement_count", "-", "s1_scope.build_settlements")
def settlement_count(sv: pd.DataFrame) -> int:
    return int(len(sv))


@K.published("served_plot_count", "-", "s1_scope, W10_plot_loads.gpkg")
def served_plot_count(sv: pd.DataFrame) -> int:
    return int(sv.N_PLOT.sum())


@K.published("served_load_m3d", "m3/d", "s1_scope, W10_plot_loads.gpkg Q_AVG_M3D")
def served_load_m3d(sv: pd.DataFrame) -> float:
    return round(float(sv.Q_ADF_M3D.sum()), 1)


@K.published("central_load_m3d", "m3/d", "s1_scope.decide")
def central_load_m3d(sv: pd.DataFrame) -> float:
    return round(float(sv.loc[sv.SYSTEM == "central", "Q_ADF_M3D"].sum()), 1)


@K.published("decentral_load_m3d", "m3/d", "s1_scope.decide")
def decentral_load_m3d(sv: pd.DataFrame) -> float:
    return round(float(sv.loc[sv.SYSTEM.isin(("satellite", "onsite")), "Q_ADF_M3D"].sum()), 1)


@K.published("decentral_property_share_pct", "%", "s1_scope.decide")
def decentral_property_share_pct(sv: pd.DataFrame) -> float:
    tot = float(sv.N_PROP.sum())
    if tot <= 0:
        return 0.0
    off = float(sv.loc[sv.SYSTEM.isin(("satellite", "onsite")), "N_PROP"].sum())
    return round(100.0 * off / tot, 2)


@K.published("lift_avoided_m", "m", "s1_scope, W10_marginal_branches.shp")
def lift_avoided_m(sv: pd.DataFrame) -> float:
    """Static lift on marginal branches inside settlements taken off the central network.

    TOR scope p12: "avoid pumping and utilize gravity as much as practically possible."
    It is a lower bound: removing a branch also changes depths downstream, and only a
    re-solve gives the real saving (WHAT_TO_SEWER sec 7 item 5)."""
    return round(float(sv.loc[sv.SYSTEM.isin(("satellite", "onsite")), "LIFT_M"].sum()), 1)


# ---------------------------------------------------------------------------------------
# Inputs, and the graceful stop
# ---------------------------------------------------------------------------------------

def missing_inputs() -> list:
    need = [
        (IN_PLOT_LOADS, "W10 plot loads (64,071 records, layer 'plot_loads')"),
        (IN_SETTLE_CSV, "W10 r5_settlements.csv - the exclusive-pipe measure per settlement "
                        "(re-create with: python W10/py/research/r5_marginal.py)"),
        (IN_MARGINAL, "W10_marginal_branches.shp - the 1 m3/d marginal tree"),
        (IN_EXISTING, "W10_existing_built.shp - the built 2006 network, for the G201 p80 "
                      "25 km test"),
        (IN_TOWNS, "Towns.shp - settlement naming and the population cross-check"),
    ]
    return [(p, w) for p, w in need if not os.path.exists(p)]


# ---------------------------------------------------------------------------------------
# Settlements
# ---------------------------------------------------------------------------------------

def build_settlements(plots: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """The 60 m envelopes, reproduced from r5_marginal.py verbatim so the SIDs still match.

    Reproducing rather than importing is deliberate: r5 lives in W10 and this stage may not
    modify or depend on W10 code, and `verify_sids` proves the reproduction is exact instead
    of assuming it.
    """
    blob = gpd.GeoDataFrame(
        geometry=[unary_union(plots.geometry.buffer(SETTLE_BUFFER_M))], crs=K.CRS_EPSG)
    blob = blob.explode(index_parts=False).reset_index(drop=True)
    blob["SID"] = blob.index
    return blob


def assign_plots(plots: gpd.GeoDataFrame, blob: gpd.GeoDataFrame) -> pd.Series:
    j = gpd.sjoin(plots, blob[["SID", "geometry"]], how="left", predicate="intersects")
    j = j[~j.index.duplicated(keep="first")]
    return j["SID"]


def verify_sids(agg: pd.DataFrame, ref: pd.DataFrame) -> str:
    """Do our envelopes reproduce W10's settlements row for row?

    If they do not, every SID in WHAT_TO_SEWER means something else here and the exclusive-
    pipe join is silently wrong. It is one comparison and it is worth having: shapely's
    unary_union part ordering is not a documented guarantee.
    """
    left = ref[["SID", "plots", "props"]].rename(
        columns={"plots": "plots_w10", "props": "props_w10"})
    m = left.merge(agg[["SID", "N_PLOT", "N_PROP"]], on="SID", how="outer", indicator=True)
    if (m._merge != "both").any():
        return (f"SID SETS DIFFER: {int((m._merge != 'both').sum())} settlements do not "
                "appear in both. The exclusive-pipe join cannot be trusted.")
    bad_p = (m.plots_w10 != m.N_PLOT).sum()
    bad_q = ((m.props_w10 - m.N_PROP).abs() > 0.01).sum()
    if bad_p or bad_q:
        return (f"SID MISMATCH: {int(bad_p)} settlements differ on plot count, {int(bad_q)} "
                "on property count. W10's SIDs do not mean here what they mean there.")
    return ""


def check_west_basin(blob: gpd.GeoDataFrame, agg: pd.DataFrame) -> str:
    """Which settlement holds the west closed basin's low point?

    WHAT_TO_SEWER sec 6 asserts "AL DIREZ is the west leg". WEST_LEG.md puts the west low
    point at 442,092 E 2,569,064 N. If that point falls inside the core envelope rather than
    AL DIREZ's, the west leg is a sub-catchment of the central system - a trunk and station
    question for stages 3 and 5 - and not a settlement-scope question at all. Checked every
    run so the claim cannot come back by being repeated.
    """
    west = Point(442092.0, 2569064.0)
    hit = blob[blob.contains(west)]
    core_sid = int(agg.loc[agg.N_PROP.idxmax(), "SID"])
    if hit.empty:
        return "the west low point falls outside every settlement envelope"
    sid = int(hit.SID.iloc[0])
    where = "the CORE conurbation" if sid == core_sid else f"settlement SID {sid}"
    return (f"the west closed basin's low point (442092 E 2569064 N) lies in {where} "
            f"(SID {sid}). WHAT_TO_SEWER sec 6's 'AL DIREZ is the west leg' does not hold: "
            "the west is a sub-catchment of the central system, so pumped conveyance versus "
            "a west satellite works is a stage 3/5 question, not a stage 1 scope question")


# ---------------------------------------------------------------------------------------
# The decision
# ---------------------------------------------------------------------------------------

def _works_for(system: str, pop: float, q: float) -> str:
    if system == "central":
        return "central STP"
    if system == "onsite":
        return "septic/tanker"
    return "package plant" if (PKG_MIN_POP <= pop <= PKG_MAX_POP
                               and q <= PKG_MAX_Q_M3D) else "local works"


def _decentral_option(pop: float, q: float) -> str:
    """Which decentralised system a settlement of this size qualifies for, G201 p83.

    Below 50 inhabitants the guideline offers no plant at all - septic tank to the OPSDC or
    a holding tank emptied by vacuum tanker. Above that it is a works, package or
    conventional depending on whether it fits inside the 5,000 pe / 750 m3/d ceiling.
    """
    return "onsite" if pop < PKG_MIN_POP else "satellite"


def decide(r: pd.Series) -> dict:
    """The ladder. Returns SYSTEM, ALT_SYS, BOTH, DEC_RULE, WHY, PENDING, CONFIDENCE.

    Order matters. The cost test is applied to every settlement that has properties to
    divide by, and only where it cannot be applied does the guideline's size test take over.
    That order is the fix for the first version of W10's classifier, which sorted small
    settlements into "do not sewer" by size and put 60 free connections - plots on streets
    the core network already runs down - in the wrong tranche.
    """
    pop, q, prop = float(r.POP), float(r.Q_ADF_M3D), float(r.N_PROP)
    mpp = float(r.M_PER_PRP)
    alt_dec = _decentral_option(pop, q)

    # -- the core conurbation. 51,487 plots, 81,706 properties, 61,672 m3/d. There is no
    #    alternative to a central system at this scale and no guideline contemplates one.
    if bool(r.IS_CORE):
        return dict(SYSTEM="central", ALT_SYS="", BOTH=0, DEC_RULE="CORE",
                    WHY=("the Ibri conurbation - 82 % of the load. No decentralised option "
                         "in G201 p83 or G203 p96 reaches this scale; the only question is "
                         "how many works serve it, which is stage 4"),
                    PENDING="", CONFIDENCE="derived")

    # -- no load at all. 33 settlements, 45 plots, 0 properties, 0 m3/d. The cost test has
    #    no denominator, so the fall-back is G201 p80's only numeric distance test.
    #    NOT a scope cut: the row stays, and it says what it is waiting for.
    if prop < ZERO_LOAD_PROP and q < ZERO_LOAD_Q:
        far = float(r.KM_CORE) >= G201_REMOTE_KM
        sysm = "onsite" if far else "central"
        return dict(SYSTEM=sysm, ALT_SYS="central" if far else "onsite", BOTH=0,
                    DEC_RULE="ZERO-LOAD",
                    WHY=(f"no wastewater load at all under the current land-use "
                         f"classification, so the cost test has no denominator. "
                         f"{'25 km or more from the core (G201 p80) - on-site' if far else 'inside the 25 km of G201 p80 and 0 exclusive metres - it connects at no marginal cost'}"),
                    PENDING=("zero load: land-use classification. The GIS expert's treated "
                             "data decides whether these plots are vacant or misclassified; "
                             "if they carry load, re-run S1"),
                    CONFIDENCE="provisional")

    # -- the cost test. G201 p80's fourth remote-area bullet, made measurable.
    in_band = FLIP_BAND[0] <= mpp < FLIP_BAND[1]
    if mpp < BREAK_M_PER_PROP:
        return dict(SYSTEM="central", ALT_SYS=alt_dec, BOTH=0, DEC_RULE="COST",
                    WHY=(f"{mpp:.1f} m of exclusive sewer per property, under the measured "
                         f"{BREAK_M_PER_PROP:.0f} m break - cheaper to connect than to run "
                         f"a {'package plant' if alt_dec == 'satellite' else 'septic/tanker service'} "
                         f"for {prop:.0f} properties"),
                    PENDING=("break sensitivity: this row moves if the cut is set anywhere "
                             "in 18-25 m/property (WHAT_TO_SEWER sec 4)") if in_band else "",
                    CONFIDENCE="provisional" if in_band else "derived")

    # -- above the break. The system follows the guideline's own size bands.
    #    The FLOOR is stated in inhabitants (G201 p83: "communities with a population
    #    between 50-5,000") and the CEILING binds in both units (G203 p96 states the pair
    #    "5,000 inhabitants (approx. 750 m3/day)"). They are applied in the units the
    #    guideline states them in, and where population and flow disagree the row says so
    #    rather than picking whichever suits - see the tanker-sizing note below.
    sysm = alt_dec
    km = float(r.KM_CORE)
    rule = "G201-p83" if pop < PKG_MIN_POP else (
        "G201-p83" if (pop <= PKG_MAX_POP and q <= PKG_MAX_Q_M3D) else "G203-p96")
    pend = ("NPV over 25 years at 5 % (G201 p96 sec 12.4) decides this against connection; "
            "Renardet unit rates not yet held, so the ratio stands in for the money")
    if sysm == "onsite":
        why = (f"{mpp:.0f} m of exclusive sewer per property against a {BREAK_M_PER_PROP:.0f} m "
               f"break, and {pop:.0f} people - below the 50-inhabitant floor for any plant "
               f"(G201 p83), so septic tank to the OPSDC or a holding tank emptied by "
               f"tanker. Compared against connection to the central network, "
               f"{km:.2f} km away")
        if q >= PKG_MIN_Q_M3D:
            # The floor caught it on population, but the flow says otherwise. That happens
            # where the load is commercial or governmental and carries no population at all,
            # and it matters because the tanker service is sized on the flow, not the people.
            pend += (f". NOTE the population floor and the flow disagree here: {pop:.0f} "
                     f"people but {q:.1f} m3/d, so the load is non-domestic. Size the tanker "
                     f"service on the flow (G201 p83 requires access routes and turning "
                     f"radii for it), not on the population")
    elif rule == "G201-p83":
        why = (f"{mpp:.0f} m of exclusive sewer per property against a {BREAK_M_PER_PROP:.0f} m "
               f"break; {pop:.0f} pe and {q:.0f} m3/d sit inside the package-plant band "
               f"(G201 p83 50-5,000 pe, G203 p96 ~750 m3/d). Compared against connection to "
               f"the central network, {km:.2f} km away")
        if q <= WETLAND_MAX_Q_M3D:
            pend += (f". Under {WETLAND_MAX_Q_M3D:.0f} m3/d, so a constructed wetland is also "
                     f"open to it (G203 p101) - a treatment-process choice for stage 4, not "
                     f"a system choice")
    else:
        why = (f"{mpp:.0f} m of exclusive sewer per property against a {BREAK_M_PER_PROP:.0f} m "
               f"break, but {pop:.0f} pe / {q:.0f} m3/d is above every decentralised ceiling "
               f"in the guidelines - a local conventional works, not a package plant. "
               f"Compared against connection to the central network, {km:.2f} km away")
    return dict(SYSTEM=sysm, ALT_SYS="central", BOTH=0, DEC_RULE=rule, WHY=why,
                PENDING=pend, CONFIDENCE="provisional" if in_band else "derived")


def apply_bat_doctrine(sv: gpd.GeoDataFrame) -> tuple:
    """BAT carries BOTH options. Philosophy sec 8a, and it is not ours to decide.

    Found by NAME rather than by hard-coded SID, then CHECKED against the figures sec 8a
    quotes (2,231 properties, 1,752 m3/d, 22-25 km out). If the name test finds a different
    group the run says so rather than silently flagging the wrong settlements.
    """
    m = sv.NAME.astype(str).str.upper().str.startswith("BAT")
    if not m.any():
        return sv, "BAT NOT FOUND by name - philosophy sec 8a's both-options flag is UNSET"
    prop, q = float(sv.loc[m, "N_PROP"].sum()), float(sv.loc[m, "Q_ADF_M3D"].sum())
    kmb = (float(sv.loc[m, "KM_BUILT"].min()), float(sv.loc[m, "KM_BUILT"].max()))
    sv.loc[m, "BOTH"] = 1
    sv.loc[m, "ALT_SYS"] = "satellite"
    sv.loc[m, "DEC_RULE"] = "PHIL-8a"
    sv.loc[m, "CONFIDENCE"] = "provisional"
    sv.loc[m, "WHY"] = (
        f"BAT: {prop:,.0f} properties, {q:,.0f} m3/d, {kmb[0]:.0f}-{kmb[1]:.0f} km from the "
        f"built network. The cost test says connect ({sv.loc[m, 'M_PER_PRP'].max():.1f} "
        f"m/property, under the break), but at {q:,.0f} m3/d it is above every decentralised "
        f"ceiling in the guidelines (G201 p83 and G203 p96 both stop at 5,000 pe / ~750 "
        f"m3/d), so its local option is a small conventional works. Philosophy sec 8a: carry "
        f"BOTH - conveyance and a satellite works - into the options appraisal")
    sv.loc[m, "PENDING"] = ("BOTH options carried to the options appraisal: 10 km of "
                            "conveyance versus a local works. Deciding it here would "
                            "pre-empt the appraisal (philosophy sec 8a)")
    note = (f"BAT flagged BOTH on {int(m.sum())} settlements: {prop:,.0f} properties, "
            f"{q:,.0f} m3/d, {kmb[0]:.1f}-{kmb[1]:.1f} km from the built network "
            f"(philosophy sec 8a says 22-25 km, measured from settlement CENTROIDS in r5; "
            f"these are ENVELOPE distances, which is the distance the G201 p80 test asks "
            f"for and is shorter for a 6.8 km2 settlement)")
    # philosophy sec 8a quotes 2,231 properties and 1,752 m3/d. A 2 % drift is the
    # rounding in the source table; more than that means the group is not the same group.
    if abs(prop - 2231) / 2231 > 0.02 or abs(q - 1752) / 1752 > 0.02:
        note += (f"  <- DOES NOT MATCH philosophy sec 8a (2,231 properties, 1,752 m3/d). "
                 f"Check which settlements the name test caught before relying on this flag")
    return sv, note


# ---------------------------------------------------------------------------------------
# Sensitivity - the break is a cliff, and a cliff has an edge worth measuring
# ---------------------------------------------------------------------------------------

def sensitivity(sv: pd.DataFrame) -> pd.DataFrame:
    """How the answer moves as the cut moves. Every row that HAS a cost ratio participates.

    The filter chain, stated in full because an undeclared one is the "re-filtered metric"
    philosophy sec 8 blocks on. Excluded: CORE (no decentralised option exists at that
    scale) and ZERO-LOAD (M_PER_PRP is the -1 sentinel, there is no denominator to divide
    by). INCLUDED, and it was not before: the PHIL-8a rows. BAT sits at 17.6 m/property, so
    at any cut of 17.6 or below the cost test moves it off the central network - leaving it
    out understated the 15 m column by 1,877 properties (13,562 shown against 15,439 real)
    while the WATCH line below invited the reader to consider exactly that cut. That both
    options are carried for BAT is a reason to grade it provisional, not a reason to hide it
    from the sensitivity."""
    m = sv.DEC_RULE.isin(("COST", "G201-p83", "G203-p96", "PHIL-8a"))
    d = sv.loc[m, ["M_PER_PRP", "N_PROP", "Q_ADF_M3D", "EXCL_KM"]].copy()
    rows = []
    for cut in (10.0, 15.0, 18.0, 20.0, 25.0, 30.0, 40.0, 80.0, 150.0):
        off = d.M_PER_PRP >= cut
        rows.append(dict(
            break_m_per_prop=cut,
            decentralised_settlements=int(off.sum()),
            properties_off_network=round(float(d.loc[off, "N_PROP"].sum()), 0),
            pct_of_properties=round(100 * float(d.loc[off, "N_PROP"].sum())
                                    / float(sv.N_PROP.sum()), 2),
            load_off_network_m3d=round(float(d.loc[off, "Q_ADF_M3D"].sum()), 1),
            pct_of_load=round(100 * float(d.loc[off, "Q_ADF_M3D"].sum())
                              / float(sv.Q_ADF_M3D.sum()), 2),
            exclusive_km_not_built=round(float(d.loc[off, "EXCL_KM"].sum()), 1)))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------------------
# The checks this stage is responsible for
# ---------------------------------------------------------------------------------------

def self_check(sv: gpd.GeoDataFrame, plots: gpd.GeoDataFrame) -> pd.DataFrame:
    """Stage 1 publishes no network layer, so H1-H15 do not reach it. These do.

    Philosophy sec 8 makes a check that cannot run a FAILURE, so each returns PASS or FAIL
    and never a blank.
    """
    rows = []

    def add(cid, what, ok, detail, src):
        rows.append(dict(check=cid, requirement=what,
                         result="PASS" if ok else "FAIL", detail=detail, source=src))

    n_un = int((sv.SYSTEM == "unserved").sum())
    add("S1-1", "no settlement is left unserved", n_un == 0,
        f"{n_un} rows carry SYSTEM='unserved'", "TOR scope p4 item 3, p6 item 2, p8 item 17")

    lost_n = len(plots) - int(sv.N_PLOT.sum())
    lost_q = round(float(plots.Q_AVG_M3D.sum()) - float(sv.Q_ADF_M3D.sum()), 3)
    add("S1-2", "every plot record reaches exactly one settlement",
        lost_n == 0 and abs(lost_q) < 0.05,
        f"{len(plots):,} plot records in, {int(sv.N_PLOT.sum()):,} out, "
        f"{lost_n} unaccounted, {lost_q} m3/d unaccounted",
        "philosophy invariant 1 - W10 dropped 1,233 m3/d silently")

    dup = int(sv.SET_ID.duplicated().sum())
    add("S1-3", "settlement identity is unique", dup == 0, f"{dup} duplicate SET_ID", "contract")

    blank = int((sv.WHY.astype(str).str.strip() == "").sum())
    add("S1-4", "every decision states its reason and its alternative", blank == 0,
        f"{blank} rows with a blank WHY", "the task: 'the alternative it was compared against'")

    bad_conf = int((~sv.CONFIDENCE.isin(K.CONFIDENCE)).sum())
    add("S1-5", "CONFIDENCE on every row, from the contract enum", bad_conf == 0,
        f"{bad_conf} rows outside {list(K.CONFIDENCE)}", "audit G5 (planned), P6")

    both = int(sv.BOTH.sum())
    add("S1-6", "the both-options settlements are flagged, not decided", both > 0,
        f"{both} settlements carry BOTH=1", "philosophy sec 8a - BAT")

    # A settlement above the break that was nonetheless put on the central network, or the
    # reverse, is not forbidden - but it must be because a NAMED rule overrode the cost
    # test, never because the ladder fell through.
    odd = sv[(sv.M_PER_PRP >= BREAK_M_PER_PROP) & (sv.SYSTEM == "central")
             & (~sv.DEC_RULE.isin(("CORE", "PHIL-8a", "ZERO-LOAD")))]
    add("S1-7", "no row sits on the wrong side of its own rule", len(odd) == 0,
        f"{len(odd)} rows above the break are central without a named override",
        "internal consistency")

    # M_PER_PRP = -1 is a SENTINEL, not a ratio, and -1 < 20 is True. The ZERO-LOAD branch
    # catches it only when BOTH properties and flow are zero, so a settlement carrying
    # non-domestic load with no electricity account falls straight through into the cost
    # test and is decided "central" on a WHY reading "-1.0 m of exclusive sewer per
    # property". It does not fire on today's data - all 33 sentinel rows carry zero load -
    # but the PENDING note on those very rows says the land-use delivery may give them load
    # and asks for a re-run, so the trigger is named and expected.
    sent = sv[(sv.M_PER_PRP < 0) & (sv.DEC_RULE.isin(("COST", "G201-p83", "G203-p96")))]
    add("S1-8", "no row is decided by the cost test on a sentinel ratio", len(sent) == 0,
        f"{len(sent)} rows carry M_PER_PRP < 0 and a cost-test DEC_RULE"
        + (f": {list(sent.SET_ID)[:8]}" if len(sent) else ""),
        "philosophy sec 3 - a decision must trace to a measured value, not a placeholder")
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------------------

def main() -> int:
    print("=" * 88)
    print("W11a STAGE 1 - SCOPE AND SERVICING STRATEGY")
    print("  philosophy sec 2 step 1 (what is served) and sec 8a (served is not connected)")
    print("=" * 88)

    miss = missing_inputs()
    if miss:
        print("\nWAITING ON UPSTREAM INPUTS - nothing written, exiting 0:\n")
        for p, w in miss:
            print(f"   MISSING  {w}\n            {p}")
        print("\nStage 1 needs all of them: the loads set the numerator, the settlements "
              "\nset the unit of decision, and the exclusive-pipe measure is what decides.")
        return 0

    if register_spec():
        print("\nNOTE  contract.py declares no LayerSpec for 'servicing'. This stage supplies "
              "\n      one and registers it. It should be folded into contract.py - a schema "
              "\n      that lives in the stage that writes it is the drift EXCLUDED warns of.")

    # Per-stage manifest, not the shared one. Manifest.records is class-level and every
    # stage runs as its OWN process, so each would save a manifest.json holding only its own
    # record and silently overwrite the last stage's. A per-stage file cannot clobber, and
    # the run report reads the set.
    man = os.path.join(OUT_RUN, "manifest_s1_scope.json")
    with K.Manifest.stage(STAGE, ORDER, path=man) as rec:
        # ---------------------------------------------------------------- read
        plots = gpd.read_file(IN_PLOT_LOADS, layer="plot_loads")
        if plots.crs is None or plots.crs.to_epsg() != K.CRS_EPSG:
            plots = plots.set_crs(K.CRS_EPSG, allow_override=True)
        rec.read("plot_loads", IN_PLOT_LOADS, len(plots))

        ref = pd.read_csv(IN_SETTLE_CSV)
        rec.read("r5_settlements", IN_SETTLE_CSV, len(ref))

        marg = gpd.read_file(IN_MARGINAL).to_crs(K.CRS_EPSG)
        rec.read("marginal_branches", IN_MARGINAL, len(marg))

        built = gpd.read_file(IN_EXISTING).to_crs(K.CRS_EPSG)
        rec.read("existing_built", IN_EXISTING, len(built))

        towns = gpd.read_file(IN_TOWNS).to_crs(K.CRS_EPSG)
        rec.read("towns", IN_TOWNS, len(towns))

        print(f"\nread {len(plots):,} plot records, {float(plots.Q_AVG_M3D.sum()):,.1f} m3/d, "
              f"{float(plots.N_PROP.sum()):,.0f} properties")

        # ---------------------------------------------------------------- settlements
        fn = rec.funnel("plot records -> settlement rows", len(plots))
        blob = build_settlements(plots)
        plots = plots.copy()
        plots["SID"] = assign_plots(plots, blob).values
        orphan = plots.SID.isna()
        if orphan.any():
            # Cannot happen - every plot is inside its own buffer - but an uncounted drop is
            # a silent one, and the funnel refuses to close if it is not named.
            fn.drop("plot outside every settlement envelope",
                    ids=plots.loc[orphan, "PLOT_ID"].tolist(),
                    qty=float(plots.loc[orphan, "Q_AVG_M3D"].sum()))
            plots = plots[~orphan]
        plots["SID"] = plots.SID.astype(int)

        agg = plots.groupby("SID").agg(
            N_PLOT=("PLOT_ID", "size"),
            N_PROP=("N_PROP", "sum"),
            POP=("POP", "sum"),
            Q_ADF_M3D=("Q_AVG_M3D", "sum"),
            N_OUTBND=("IN_BND", lambda s: int((s == 0).sum()))).reset_index()

        bad = verify_sids(agg, ref)
        if bad:
            print("\n" + bad)
            print("Stage 1 stops: W10's exclusive-pipe measure cannot be joined to these "
                  "settlements.\nRe-run W10/py/research/r5_marginal.py, or the SIDs have "
                  "moved under a shapely change.")
            rec.did_nothing("settlement SIDs do not reproduce W10's; the exclusive-pipe "
                            "join would be silently wrong")
            # NON-ZERO. A missing upstream input is "waiting" and exits 0 by project
            # convention; a FAILED integrity check is not waiting, it is a check that could
            # not be satisfied, which philosophy sec 8 makes blocking. Exiting 0 here would
            # tell an orchestrator the stage succeeded while stage 2 went on reading the
            # PREVIOUS run's s1_plot_system.csv, which is still on disk and looks finished.
            return 1
        print(f"settlements: {len(agg)} envelopes at a {SETTLE_BUFFER_M:.0f} m plot buffer; "
              f"plot and property counts reproduce W10's SIDs exactly")

        # ---------------------------------------------------------------- geometry + names
        sv = gpd.GeoDataFrame(agg.merge(blob[["SID", "geometry"]], on="SID"),
                              geometry="geometry", crs=K.CRS_EPSG)

        # The settlement name comes from the CADASTRE, not from the Towns polygons. W10's
        # r5_settlements.csv already carries it, derived by sjoin_nearest of each plot's
        # representative point onto MoH_Plots.VILLAGE_EN at 200 m and taking the majority
        # per settlement (r5_marginal.py). Reused rather than recomputed so a settlement
        # called BAT here is the settlement WHAT_TO_SEWER calls BAT - the whole point of
        # reproducing W10's SIDs. VILLAGE_EN is blank on 43,557 of 61,272 plots, so most
        # settlements have no cadastral name and fall through to the Towns polygon.
        #
        # This matters more than a label: the philosophy sec 8a both-options flag is found
        # BY NAME. An earlier version of this stage read VILLAGE_EN off plot_loads, which
        # does not carry it, so every name silently became the Towns polygon - five separate
        # settlements called TANAM - and the BAT group came out as 1,881 properties instead
        # of 2,231. The apply_bat_doctrine() total check is what caught it.
        nm = ref.set_index("SID").village.astype(str).str.strip()
        nm = nm[nm.ne("") & nm.ne("-") & nm.ne("nan")]
        sv["NAME"] = sv.SID.map(nm)
        # Towns is the FALLBACK name and a population cross-check. It is never a load input:
        # the load basis is locked (Tier A ratios set the volume, land use sets the
        # placement), and a second population series would quietly become a second basis.
        cen = gpd.GeoDataFrame(geometry=sv.geometry.representative_point(), crs=K.CRS_EPSG)
        tn = gpd.sjoin(cen, towns[["NAME_EN", "geometry"]], how="left", predicate="within")
        tn = tn[~tn.index.duplicated(keep="first")]
        sv["TOWN"] = tn["NAME_EN"].fillna("").astype(str).values
        sv["NAME"] = sv.NAME.fillna(pd.Series(sv.TOWN.values, index=sv.index)).replace("", "-")
        sv["NAME"] = sv.NAME.fillna("-").astype(str)

        # ---------------------------------------------------------------- distances
        core_sid = int(sv.loc[sv.N_PROP.idxmax(), "SID"])
        sv["IS_CORE"] = sv.SID == core_sid
        core_geom = sv.loc[sv.SID == core_sid, "geometry"].iloc[0]
        # THE BUFFER MUST BE TAKEN BACK OFF. Both envelopes are the plots grown by
        # SETTLE_BUFFER_M, so the gap between two envelopes is the real plot-to-plot gap
        # minus TWO buffers, and the gap to an unbuffered feature is short by ONE. Left
        # uncorrected, a settlement 120 m from the core reads as 0.0 km and the G201 p80
        # 25 km test is 120 m optimistic on every row. Exact, not approximate: for uniform
        # buffers of radius r, d_buffered = max(0, d_raw - 2r), and no two envelopes here
        # touch (they would have merged), so d_buffered > 0 and the inverse is exact.
        b = SETTLE_BUFFER_M / 1000.0
        sv["KM_CORE"] = (sv.geometry.distance(core_geom) / 1000.0 + 2 * b).round(3)
        sv.loc[sv.SID == core_sid, "KM_CORE"] = 0.0
        # Envelope distance to the BUILT network, not centroid distance as r5 used: G201 p80
        # asks how far the settlement is from a centralised network, and a 6.8 km2 envelope's
        # centroid can sit kilometres from its nearest edge. r5's centroid figures therefore
        # read LONGER than the truth for a large settlement and shorter by one buffer here.
        built_u = unary_union(built.geometry.values)
        raw_built = sv.geometry.distance(built_u) / 1000.0
        sv["KM_BUILT"] = np.where(raw_built > 0, raw_built + b, 0.0).round(3)

        # ---------------------------------------------------------------- the ratio (W10)
        r = ref.set_index("SID")
        sv["EXCL_KM"] = sv.SID.map(r.pipe_km_exclusive).fillna(0.0).round(3)
        sv["M_PER_PRP"] = np.where(sv.N_PROP > ZERO_LOAD_PROP,
                                   sv.EXCL_KM * 1000.0 / sv.N_PROP.replace(0, np.nan), -1.0)
        sv["M_PER_M3D"] = np.where(sv.Q_ADF_M3D > ZERO_LOAD_Q,
                                   sv.EXCL_KM * 1000.0 / sv.Q_ADF_M3D.replace(0, np.nan), -1.0)
        sv["M_PER_PRP"] = sv.M_PER_PRP.fillna(-1.0).round(2)
        sv["M_PER_M3D"] = sv.M_PER_M3D.fillna(-1.0).round(2)
        sv["BREAK_M"] = BREAK_M_PER_PROP
        sv["MARGIN_M"] = np.where(sv.M_PER_PRP >= 0,
                                  (sv.M_PER_PRP - BREAK_M_PER_PROP).round(2), np.nan)

        # ---------------------------------------------------------------- guideline tests
        sv["REMOTE"] = (((sv.POP < G201_MAX_POP) | (sv.N_PLOT < G201_MAX_PLOTS))
                        | (sv.KM_BUILT >= G201_REMOTE_KM)).astype(int)
        sv["PKG_OK"] = ((sv.POP >= PKG_MIN_POP) & (sv.POP <= PKG_MAX_POP)
                        & (sv.Q_ADF_M3D <= PKG_MAX_Q_M3D)).astype(int)

        # ---------------------------------------------------------------- marginal pipe
        # What the system choice takes off the central network. Attributed by the length of
        # branch actually inside the envelope, so a branch straddling two settlements lands
        # on the one it mostly serves rather than on whichever the join met first.
        # LENGTH is a property of the PART; LIFT_M and N_LIFT are properties of the BRANCH.
        # explode() copies every attribute onto every part, so summing lift over parts
        # multiplies a MultiLineString's lift by its part count: the source holds 242.3 m of
        # lift over 12 stations across 1,889 branches, the exploded frame holds 2,167.7 m
        # over 106. The branch is therefore attributed ONCE, by BR_ID, to the settlement
        # holding most of it; only the metres are summed per part.
        marg_br = marg                                   # one row per branch - lift lives here
        marg = marg.explode(index_parts=False).reset_index(drop=True)
        pair = gpd.sjoin(marg, sv[["SID", "geometry"]], how="inner", predicate="intersects")
        if len(pair):
            poly = sv.set_index("SID").geometry
            pair["INSIDE_M"] = [
                g.intersection(poly.loc[s]).length
                for g, s in zip(pair.geometry.values, pair.SID.values)]
            best = pair.sort_values("INSIDE_M", ascending=False)
            best = best[~best.index.duplicated(keep="first")]
            mg_km = best.groupby("SID").INSIDE_M.sum() / 1000.0
            own = best.groupby(["BR_ID", "SID"], as_index=False).INSIDE_M.sum()
            own = own.sort_values("INSIDE_M", ascending=False).drop_duplicates("BR_ID")
            lift = marg_br[["BR_ID", "LIFT_M", "N_LIFT"]].merge(
                own[["BR_ID", "SID"]], on="BR_ID", how="inner")
            mg_lift = lift.groupby("SID").agg(LIFT_M=("LIFT_M", "sum"),
                                              N_LIFT=("N_LIFT", "sum"))
            sv["MARG_KM"] = sv.SID.map(mg_km).fillna(0.0).round(3)
            sv["LIFT_M"] = sv.SID.map(mg_lift.LIFT_M).fillna(0.0).round(1)
            sv["N_LIFT"] = sv.SID.map(mg_lift.N_LIFT).fillna(0).astype(int)
            outside_km = round(float(marg.length.sum() - best.INSIDE_M.sum()) / 1000.0, 1)
        else:
            sv["MARG_KM"], sv["LIFT_M"], sv["N_LIFT"] = 0.0, 0.0, 0
            outside_km = round(float(marg.length.sum()) / 1000.0, 1)
        # The reconciliation that would have caught the explode: what is attributed can never
        # exceed what the source holds. A metric, not a comment, so it is checkable after run.
        src_lift, src_nlift = float(marg_br.LIFT_M.sum()), int(marg_br.N_LIFT.sum())
        if float(sv.LIFT_M.sum()) > src_lift + 0.05 or int(sv.N_LIFT.sum()) > src_nlift:
            raise K.ContractError(
                f"marginal lift attributed ({float(sv.LIFT_M.sum()):.1f} m / "
                f"{int(sv.N_LIFT.sum())} stations) exceeds the source "
                f"({src_lift:.1f} m / {src_nlift}). A branch has been counted more than once "
                "- explode() copies branch attributes onto every part.")
        rec.metric("marginal_km_outside_every_settlement", outside_km, "km")
        rec.metric("marginal_lift_source_m", round(src_lift, 1), "m")
        rec.metric("marginal_lift_attributed_m", round(float(sv.LIFT_M.sum()), 1), "m")

        # ---------------------------------------------------------------- decide
        d = pd.DataFrame([decide(row) for _, row in sv.iterrows()], index=sv.index)
        for c in ("SYSTEM", "ALT_SYS", "BOTH", "DEC_RULE", "WHY", "PENDING", "CONFIDENCE"):
            sv[c] = d[c]
        sv, bat_note = apply_bat_doctrine(sv)
        sv["WORKS"] = [_works_for(s, p, q) for s, p, q
                       in zip(sv.SYSTEM, sv.POP, sv.Q_ADF_M3D)]
        sv["SET_ID"] = ["S%03d" % s for s in sv.SID]
        sv["W10_SID"] = sv.SID.astype(int)
        sv["STAGE"] = STAGE

        fn.close(len(plots))

        # ---------------------------------------------------------------- publish
        cols = [f.name for f in SERVICING.fields] + ["geometry"]
        out = gpd.GeoDataFrame(sv[cols].copy(), geometry="geometry", crs=K.CRS_EPSG)
        out["N_PLOT"] = out.N_PLOT.astype(int)
        out["N_OUTBND"] = out.N_OUTBND.astype(int)
        out["W10_SID"] = out.W10_SID.astype(int)
        for c in ("N_PROP", "POP", "Q_ADF_M3D", "EXCL_KM", "KM_CORE", "KM_BUILT"):
            out[c] = out[c].astype(float).round(3)
        out = out.sort_values("M_PER_PRP").reset_index(drop=True)

        gpkg = K.publish(out, "servicing", K.W11A_ROOT, stage=STAGE)
        shp = K.mirror_shapefile(out, "servicing", K.W11A_ROOT)
        rec.wrote("servicing (audited, GeoPackage)", gpkg, len(out))
        rec.wrote("servicing (CAD mirror)", shp, len(out))

        os.makedirs(OUT_RUN, exist_ok=True)
        p_csv = os.path.join(OUT_RUN, "s1_servicing.csv")
        out.drop(columns="geometry").to_csv(p_csv, index=False, encoding="utf-8")
        rec.wrote("s1_servicing.csv", p_csv, len(out))

        # The plot-level map stage 2 needs to filter corridors by system. Not a published
        # layer - it is 64,071 rows of join key, and the contract's home for a per-load-unit
        # SYSTEM is the connections layer, which does not exist until stage 5.
        pm = plots[["PLOT_ID", "SID", "Q_AVG_M3D", "N_PROP", "IN_BND"]].copy()
        pm = pm.merge(out[["W10_SID", "SET_ID", "NAME", "SYSTEM", "WORKS", "BOTH"]],
                      left_on="SID", right_on="W10_SID", how="left").drop(columns="W10_SID")
        p_map = os.path.join(OUT_RUN, "s1_plot_system.csv")
        pm.to_csv(p_map, index=False, encoding="utf-8")
        rec.wrote("s1_plot_system.csv", p_map, len(pm))

        sens = sensitivity(out)
        p_sens = os.path.join(OUT_RUN, "s1_break_sensitivity.csv")
        sens.to_csv(p_sens, index=False)
        rec.wrote("s1_break_sensitivity.csv", p_sens, len(sens))

        chk = self_check(out, plots)
        p_chk = os.path.join(OUT_RUN, "s1_checks.csv")
        chk.to_csv(p_chk, index=False, encoding="utf-8")
        rec.wrote("s1_checks.csv", p_chk, len(chk))

        # ---------------------------------------------------------------- metrics
        rec.metric("settlements", K.value("settlement_count", out))
        rec.metric("plots", K.value("served_plot_count", out))
        rec.metric("load_m3d", K.value("served_load_m3d", out))
        rec.metric("central_load_m3d", K.value("central_load_m3d", out))
        rec.metric("decentral_load_m3d", K.value("decentral_load_m3d", out))
        rec.metric("decentral_property_share_pct",
                   K.value("decentral_property_share_pct", out))
        rec.metric("lift_avoided_m", K.value("lift_avoided_m", out))
        rec.note(bat_note)
        west = check_west_basin(blob, agg)
        rec.note(west)

        # ---------------------------------------------------------------- report
        print("\n" + "-" * 88)
        print("SERVICING STRATEGY - every settlement, no exceptions")
        print("-" * 88)
        g = out.groupby(["SYSTEM", "WORKS"]).agg(
            settlements=("SET_ID", "size"), plots=("N_PLOT", "sum"),
            properties=("N_PROP", "sum"), people=("POP", "sum"),
            load_m3d=("Q_ADF_M3D", "sum"), excl_km=("EXCL_KM", "sum"),
            lift_m=("LIFT_M", "sum")).round(1)
        g["pct_prop"] = (100 * g.properties / out.N_PROP.sum()).round(2)
        g["pct_load"] = (100 * g.load_m3d / out.Q_ADF_M3D.sum()).round(2)
        print(g.to_string())

        print(f"\ntotals: {K.value('settlement_count', out)} settlements, "
              f"{K.value('served_plot_count', out):,} plots, "
              f"{float(out.N_PROP.sum()):,.0f} properties, "
              f"{K.value('served_load_m3d', out):,.1f} m3/d")
        nb = int(out.N_OUTBND.sum())
        qb = round(float(plots.loc[plots.IN_BND == 0, "Q_AVG_M3D"].sum()), 1)
        # COMPUTED, not quoted. An earlier version printed "74,675.3 m3/d" as a literal and
        # asserted it was "exactly the difference"; if the load basis ever moves the sentence
        # goes false in silence, which is the provenance failure philosophy sec 8 blocks on.
        in_bnd = round(K.value("served_load_m3d", out) - qb, 1)
        print(f"  of which {nb} plot records carry IN_BND = 0 ({qb} m3/d), leaving "
              f"{in_bnd:,.1f} m3/d\n  inside the boundary - this layer's "
              f"{K.value('served_load_m3d', out):,.1f} m3/d less the out-of-boundary "
              f"records. Kept and counted here\n  rather than dropped; TOR scope p6 covers "
              f"plots WITHIN the boundary, so stage 4 sizes on the in-boundary number. "
              f"(The\n  project's standing figure is 74,675.3 m3/d - if the line above does "
              f"not read 74,675.3 the\n  load basis has moved and README/PROJECT-STATE are "
              f"behind.)")

        print(f"\ncentral network : {K.value('central_load_m3d', out):,.1f} m3/d")
        print(f"decentralised   : {K.value('decentral_load_m3d', out):,.1f} m3/d "
              f"({K.value('decentral_property_share_pct', out)} % of properties)")
        print(f"lift taken off the central network by the choice: "
              f"{K.value('lift_avoided_m', out):,.1f} m over "
              f"{int(out.loc[out.SYSTEM != 'central', 'N_LIFT'].sum())} stations "
              f"(lower bound - only a re-solve gives the real saving)")
        print(f"marginal pipe inside no settlement at all: {outside_km:,.1f} km. It serves "
              f"nobody\n  and belongs to no settlement - it is a CORRIDOR deletion for "
              f"stage 2, not a scope\n  decision, and it is the bulk of W10's 117.3 km that "
              f"collects and conveys nothing.")

        print("\n" + "-" * 88)
        print("THE SETTLEMENTS NOT ON THE CENTRAL NETWORK")
        print("-" * 88)
        off = out[out.SYSTEM != "central"].sort_values("M_PER_PRP", ascending=False)
        print(off[["SET_ID", "NAME", "N_PLOT", "N_PROP", "POP", "Q_ADF_M3D", "EXCL_KM",
                   "M_PER_PRP", "KM_CORE", "SYSTEM", "WORKS", "CONFIDENCE"]]
              .round(1).to_string(index=False))

        # The instrument is the cost ratio and nothing else, so the rows worth arguing about
        # are the ones where the ratio and the geography disagree: a two-plot pocket a few
        # hundred metres from a network we are building anyway, condemned to a septic tank by
        # a ratio that is large only because its denominator is 1.5 properties. No proximity
        # override is applied - there is no distance in G201 or G203 that would justify one,
        # and inventing a threshold here is exactly what philosophy sec 3 forbids. They are
        # PRINTED instead, because these are the first rows the NPV should be run on.
        near = off[off.KM_CORE <= off.KM_CORE.median()].sort_values("KM_CORE")
        print("\n" + "-" * 88)
        print("WHERE THE RATIO AND THE GEOGRAPHY DISAGREE - run the NPV on these first")
        print("-" * 88)
        print(f"{len(near)} decentralised settlements sit closer to the central envelope than "
              f"the median\n({off.KM_CORE.median():.2f} km). Every one of them is small "
              f"enough that its m/property is dominated by\na denominator of a handful of "
              f"properties, not by a long spur. No distance in G201 p80 or\nG203 justifies "
              f"overriding the cost test, so none is applied - but a 220 m spur to pick up\n"
              f"one house beside a town already being sewered is a judgement an operator "
              f"will want to\nmake, and it is reversible at detail design.")
        print(near[["SET_ID", "NAME", "N_PLOT", "N_PROP", "Q_ADF_M3D", "M_PER_PRP",
                    "KM_CORE", "SYSTEM"]].head(20).round(2).to_string(index=False))

        print("\n" + "-" * 88)
        print("CARRIED BOTH WAYS (philosophy sec 8a - not ours to decide)")
        print("-" * 88)
        bo = out[out.BOTH == 1]
        print(bo[["SET_ID", "NAME", "N_PROP", "Q_ADF_M3D", "M_PER_PRP", "KM_BUILT",
                  "SYSTEM", "ALT_SYS", "PKG_OK"]].round(1).to_string(index=False))
        print("  " + bat_note)

        print("\n" + "-" * 88)
        print("PROVISIONAL DECISIONS - what each is waiting on")
        print("-" * 88)
        pv = out[out.CONFIDENCE == "provisional"]
        print(f"{len(pv)} of {len(out)} settlements, "
              f"{float(pv.N_PROP.sum()):,.0f} properties, "
              f"{float(pv.Q_ADF_M3D.sum()):,.1f} m3/d")
        for why, grp in pv.groupby(pv.PENDING.str.slice(0, 60)):
            print(f"   {len(grp):3d} settlements  {why}")

        print("\n" + "-" * 88)
        print("SENSITIVITY - where the cut is, and what it costs")
        print("-" * 88)
        print(sens.to_string(index=False))
        print(f"  the stated safe band is {FLIP_BAND[0]:.0f}-{FLIP_BAND[1]:.0f} m/property "
              f"(WHAT_TO_SEWER sec 4); "
              f"{int(((out.M_PER_PRP >= FLIP_BAND[0]) & (out.M_PER_PRP < FLIP_BAND[1])).sum())}"
              f" settlements sit inside it and are graded provisional.")
        # The table says something the source note does not: the break is safe ABOVE 18 and
        # is NOT symmetric below it. Between 18 and 15 the properties going decentralised
        # jump from 931 to 13,562, because one large settlement sits just under the cut.
        # Naming it is the point - "a handful of properties either way" is true of the
        # 18-25 band only, and a reader who moved the cut to 15 on the strength of that
        # sentence would take a 9,500 m3/d settlement off the central network.
        cost_c = out[(out.DEC_RULE == "COST") & (out.SYSTEM == "central")]
        edge = cost_c.sort_values("M_PER_PRP", ascending=False).head(6)
        print("\n  the CENTRAL decisions nearest the cliff edge - the least safe, ranked by "
              "how close\n  they sit to the break and weighted by what flipping them would "
              "move:")
        print(edge[["SET_ID", "NAME", "N_PROP", "Q_ADF_M3D", "M_PER_PRP", "MARGIN_M",
                    "KM_CORE"]].round(2).to_string(index=False))
        big = cost_c[(cost_c.M_PER_PRP >= BREAK_M_PER_PROP - 5)
                     & (cost_c.Q_ADF_M3D > PKG_MAX_Q_M3D)]
        for _, b in big.iterrows():
            print(f"  WATCH {b.SET_ID} {b.NAME}: {b.N_PROP:,.0f} properties and "
                  f"{b.Q_ADF_M3D:,.0f} m3/d at {b.M_PER_PRP:.1f} m/property, only "
                  f"{abs(b.MARGIN_M):.1f} m\n        under the break. It is far above every "
                  f"decentralised ceiling, so if it ever flips it flips to a\n        "
                  f"SATELLITE WORKS, not to tankers - and that is a scheme option, not a "
                  f"detail. The break\n        would have to move to 15 m/property for it to "
                  f"flip, which is outside the stated safe band.")

        print("\n" + "-" * 88)
        print("CHECKS THIS STAGE IS RESPONSIBLE FOR")
        print("-" * 88)
        print(chk.to_string(index=False))

        print("\n" + "-" * 88)
        print("MEASURED, NOT REPEATED")
        print("-" * 88)
        print("  " + west)
        # A branch that never fires is worth saying out loud - it is the difference between
        # "the rule allowed it and nothing qualified" and "the rule was never reached".
        z = out[out.DEC_RULE == "ZERO-LOAD"]
        print(f"  the G201 p80 25 km fall-back for the {len(z)} zero-load settlements did "
              f"not fire on this data:\n  the furthest is {z.KM_CORE.max():.2f} km from the "
              f"core, so all {len(z)} are held on the central system at no\n  marginal cost "
              f"until the land-use delivery says whether they carry load at all.")
        n25 = int((out.KM_BUILT >= G201_REMOTE_KM).sum())
        print(f"  the G201 p80 25 km distance test catches {n25} settlement(s) of {len(out)}; "
              f"the size test\n  catches {int(out.REMOTE.sum())}. Neither discriminates, "
              f"which is why the cost ratio decides.")
        print("  M_PER_PRP is W10-measured on a design that is NOT ISSUABLE. It ranks "
              "settlements,\n  it does not price them. Stage 3 recomputes it on W11a's own "
              "network before the\n  options appraisal touches a rate.")

        print(f"\nwritten:\n   {gpkg}  (layer 'servicing' - the audited artefact)"
              f"\n   {shp}  (CAD mirror)"
              f"\n   {p_csv}\n   {p_map}\n   {p_sens}\n   {p_chk}")

    print("\n" + K.Manifest.report())
    fails = chk[chk.result == "FAIL"]
    if len(fails):
        print(f"\n{len(fails)} CHECK(S) FAILED - see {p_chk}")
        return 1
    print("\nstage 1 complete: every settlement has a system, nothing is dropped.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
