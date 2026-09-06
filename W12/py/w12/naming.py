"""
W12 — THE NAMING SCHEME
=======================

The engineer cannot read `N0000004` and `S009`. Neither says where the thing is, which
town it serves, what tier it is, or which subnetwork it belongs to. This module turns the
design's internal identities into names a person can navigate:

    I-S03            subnetwork 3 in Ibri
    I-S03-SM-M012    manhole 12, sub-main tier
    I-S03-C012       conduit, named for its UPSTREAM manhole
    I-PMP02          pump - NOT inside a subnetwork, because a station is a SEAM
    I-P02            force main, numbered with its pump

`w12.contract` already owns the GRAMMAR - `concept_name()` formats a name, `NAME_RE` and
`parse_name()` check one, `town_letters()` resolves the town codes. This module owns the
ASSIGNMENT: which town, which subnetwork, and which number each element gets, and it calls
contract's formatter rather than building a single name string of its own.

    from w12.naming import TownIndex, name_network, write_town_prefixes

    towns = TownIndex.load()                       # the 25-settlement gazetteer
    write_town_prefixes(towns)                     # freeze the mapping once issued
    res   = name_network(nodes, reaches=reaches, stations=st, rising_mains=rm,
                         towns=towns)
    res.nodes, res.reaches, res.stations, res.rising_mains   # NAME / TOWN / SUBNET filled
    print(res.report())                            # what was named, and what was not

    python -m w12.naming                # the town table, the clashes, and the self-test
    python -m w12.naming --freeze       # also write W12/run/W12_town_prefixes.csv/.json

NOTHING IN THE PIPELINE IMPORTS THIS YET. It is a standalone module with a clean API, and
the stage that publishes a layer is the one that should call `name_network()` and then
`contract.assert_named()`.


NAMING RUNS AFTER CONNECTIVITY IS KNOWN - AND THE API SAYS SO
-------------------------------------------------------------
The engineer's rule (b): *elements outside any town boundary take the letter of the first
town DOWNSTREAM of them*. "Downstream" is a graph fact, so a chamber cannot be named at the
moment it is minted. `assert_ready()` refuses a frame with no usable `DS_NODE` column and
names the stages that must have run first (`RUNS_AFTER`). `contract`'s `_NAMING` field group
is `required=True, blank_ok=True` for the same reason: the column exists from the first
publish, the value arrives later, and `contract.assert_named()` is the gate that says the
work was actually done.


STABILITY - THE PROPERTY THAT MATTERS MOST
------------------------------------------
A name that changes between runs silently invalidates every drawing, table and figure that
quotes it, and nothing fails while it happens. So **no ordering here comes from row order,
dict iteration, insertion order, or anything a caller could permute.** Every sequence is
derived from geometry or from graph position:

    subnetwork number   the main pipe's runs first, then branches, ordered by their outfall
                        NORTH TO SOUTH (Y descending, then X ascending), coordinates rounded
                        to ORDER_QUANT_M so a float wobble cannot flip two neighbours
    manhole number      a depth-first walk UPSTREAM from the subnetwork's outfall, taking the
                        largest upstream subtree first, ties broken north-to-south. M001 is
                        the outfall, and the numbers then walk the spine before the branches
    conduit number      its UPSTREAM manhole's number - determined, not chosen
    pump number         north to south within its town, same key as the subnetworks
    force main number   its pump's number

`tests/test_naming_scheme.py::test_the_same_design_in_a_different_row_order_gets_the_same_names`
builds one design twice, shuffles the rows and the columns of the second, and asserts the two
name maps are identical.


WHAT IS FLAGGED RATHER THAN INVENTED (concept rule 7)
-----------------------------------------------------
Every element this module cannot name keeps a blank NAME and gains a row in `result.flags`
with the reason and, where it has one, a size. It never guesses a town, never invents a
subnetwork, and never disambiguates a duplicate by bending the grammar. The flags that exist:

    node_ds_missing     DS_NODE names a chamber that is not in the frame. The link is
                        BROKEN, not absent, so the chamber was forced to act as an outfall
                        and a subnetwork was invented around it. Carries the subtree size
    node_no_town        outside every town polygon AND nothing downstream is in one
    subnet_no_town      no member chamber is inside a town and the outfall resolves to none
    node_no_tier        the tier token is IN the manhole name, so an unknown tier cannot be
                        defaulted - it would print a lateral's label on a trunk chamber
    node_tier_ungrammatical
                        the tier HAS a token but the grammar does not admit it. contract's
                        TIER_TOKEN carries five tiers (R / L / M / SM / TM); its NAME_RE
                        admits three (TM / SM / L), which are the three the engineer named.
                        A 'main' or 'rider' chamber therefore has no legal name and is
                        flagged rather than given an unparseable one - see GRAMMAR_TIERS
    reach_no_us_node    the reach's US_NODE is not in the nodes frame
    reach_us_unnamed    the upstream chamber EXISTS but has no name to lend. Kept apart
                        from the one above because filtering them together cannot tell a
                        broken link from an unnamed parent
    reach_dup_us_node   two reaches share one upstream chamber. In a forest that cannot
                        happen; naming it here rather than suffixing the name keeps the
                        graph defect visible
    station_no_town     neither the station nor its rising main's discharge is in a town
    station_town_ambiguous
                        the station's rising mains discharge into more than one town, so
                        rule (b) has more than one answer. The sort is deterministic; which
                        town owns the station is still the engineer's call
    rm_dup_station      two force mains on one pump. They would carry one name, and the
                        grammar has no token for a twin main
    rm_no_station       a rising main with no station to take its number from
    subnet_over_999     a subnetwork with more than 999 chambers. `concept_name()` pads
                        manholes to three digits, so M1000 sorts before M999 - and a
                        subnetwork that big is the defect concept rule 2 exists to stop
                        (W11b had one of 7,871 chambers)

`result.counts` publishes how many were named, RENAMED, and WITHDRAWN. Withdrawal is the
point: this module can take a name away as well as give one, which is inheritance-ledger
row 4 applied to naming - anything a pass can ADD, a later pass must be able to TAKE AWAY,
and the stage publishes how many it removed.


THE TOWN PREFIXES, AND FREEZING THEM
------------------------------------
Source layer: `Hydraulic/SHP/Towns/Towns.shp` (EPSG:32640, 25 polygons), field `NAME_EN`.
Measured 2026-09-06: **20 of the 25 towns collide on a single letter**, in 8 clash groups -
A (Akheedar / Araqi / Aynayn), S (Shiab / Satwah / Sayh al Masarrat / Shalashil / Suwayda al
Ma), D, J, M, Q, T and W of two each. Only Bat, Ghubayrah, Hijar, Ibri and Usaybuq keep one
letter. The clash rule is the engineer's and it is symmetric: BOTH towns extend, so no code
depends on which town serves more plots.

The clash universe is **the whole gazetteer, not the served towns** (declared in
`ASSUMPTIONS`). Codes computed over the served subset would move every time the served set
moved - exactly the instability rule (e) forbids - and the mapping is meant to be issued once
and frozen. `write_town_prefixes()` emits the CSV and a JSON manifest with a checksum;
`TownIndex.load(frozen=...)` reads the frozen codes back and `check_frozen()` reports drift
instead of silently re-deriving.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import sys
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from w12.contract import (ContractError, SUBNET_RE, TIERS, TIER_ALIASES, TIER_TOKEN,
                          concept_name, parse_name, town_letter, town_letters)

__all__ = [
    "ASSUMPTIONS", "RUNS_AFTER", "NamingError", "NamingOrderError",
    "TownIndex", "write_town_prefixes", "load_town_prefixes",
    "NamingResult", "name_network", "assert_ready", "clear_names",
    "default_towns_path", "default_prefix_path",
]


# ======================================================================================
# ASSUMPTIONS - every choice in this file with no guideline page behind it
# ======================================================================================
#
# NAMING HAS NO HYDRAULICS, so there is not one design number in this module and there must
# never be: no slope, no diameter, no depth, no flow. What is below are ordering and
# vocabulary decisions. Each is a PROJECT DECISION with the reason it was made, and each is
# reported by `python -m w12.naming` so a deliverable can carry them.

TOWN_NAME_FIELD = "NAME_EN"          # see ASSUMPTIONS["TOWN_NAME_FIELD"]
ORDER_QUANT_M = 0.01                 # see ASSUMPTIONS["ORDER_QUANT_M"]
MAIN_TIER = "trunk main"             # contract.TIERS member that marks the main pipe
SUBNET_PAD_MIN = 2                   # S03 - contract.SUBNET_RE requires at least two digits
PUMP_PAD_MIN = 2                     # PMP02 - contract.NAME_RE requires at least two
MH_PAD = 3                           # M012 - fixed by contract.concept_name(), not by us
MH_SEQ_SORTS_TO = 999                # past this the 3-digit padding stops sorting; flagged

CRS_EPSG = 32640                     # UTM 40N - the project CRS every W12 layer is in

ASSUMPTIONS: Dict[str, Tuple] = {
    "TOWN_NAME_FIELD": (
        TOWN_NAME_FIELD,
        "the field on Hydraulic/SHP/Towns/Towns.shp the town letter is taken from. The "
        "layer also carries NAME_AR (Arabic script, which cannot go in a DBF code), CODE "
        "(a 6-7 digit gazetteer id) and TOWN (a 9-digit administrative code) - neither "
        "number has a letter in it, so NAME_EN is the only field a letter can come from. "
        "DATA CHOICE, not a design value."),
    "TOWN_CLASH_UNIVERSE": (
        "the whole gazetteer (25 towns)",
        "the codes are resolved against EVERY town in the layer, not only the towns the "
        "design serves. Resolving against the served subset would give Ad Dariz 'D' today "
        "and 'DA' the day Ad Dibayshi is added, renaming a whole town's network for a "
        "reason that has nothing to do with it. PROJECT DECISION, and the reason the "
        "mapping is meant to be frozen once issued."),
    "SUBNET_ORDER": (
        "main-pipe runs first, then branches, each ordered by its outfall NORTH TO SOUTH",
        "the number must not come from row order, area, length or plot count - all four "
        "move when the design moves, and rule (e) requires a rebuild to reproduce every "
        "name. An outfall's coordinate does not move unless the design genuinely moves it. "
        "The main pipe's own runs sort first so I-S01 is the spine through that town. "
        "PROJECT DECISION."),
    "SUBNET_TOWN_RULE": (
        "the town holding the most of the subnetwork's chambers",
        "a subnetwork can straddle a boundary, and the town letter is a property of the "
        "SUBNETWORK rather than of each chamber - otherwise I-S03 and AR-S03 would be the "
        "same subnetwork under two names and neither would identify it. Plurality, with "
        "the share published in the subnets table so a 51/49 call is visible. Where no "
        "chamber is inside any town, the engineer's rule (b) applies: the first town "
        "DOWNSTREAM of the outfall. PROJECT DECISION."),
    "MH_ORDER": (
        "depth-first upstream from the outfall, largest upstream subtree first",
        "M001 is the outfall and the numbers then walk the spine before turning up the "
        "branches, which is how a drawing is read. Subtree size is a graph fact, so the "
        "order survives a row shuffle; ties break north-to-south on rounded coordinates. "
        "PROJECT DECISION."),
    "MH_NUMBER_SCOPE": (
        "unique within the SUBNETWORK, not within the tier",
        "the tier token is in the name (I-S03-SM-M012), so per-tier numbering would also "
        "be unique - but a retier would then renumber the chamber as well as relabel it. "
        "Numbering within the subnetwork means a retier changes SM to L and leaves M012 "
        "alone, so a name quoted on a drawing still points at the same chamber. PROJECT "
        "DECISION."),
    "MAIN_AS_SUBNET": (
        "the main pipe's chambers form their own subnetwork per town",
        "the grammar has no name for a chamber outside a subnetwork except a pump, and the "
        "main pipe is an INPUT that no branch may cross (concept rule 2). Its chambers are "
        "therefore grouped into one subnetwork per town-run and sorted FIRST, so I-S01 is "
        "the main pipe through Ibri. These rows are marked IS_MAIN=1 in the subnets table "
        "so a drawing can colour them apart. PROJECT DECISION, and the one in this file "
        "most likely to want the engineer's word - a reserved token (I-TM) would also work "
        "but is not in the grammar he stated."),
    "ORDER_QUANT_M": (
        ORDER_QUANT_M,
        "m. Coordinates are rounded to this before they are used as a SORT KEY, so two "
        "outfalls that differ in the last bits of a float cannot swap places between runs "
        "and rename half a town. STRUCTURAL tolerance - it bounds a sort, never a pipe - "
        "and it is far below any real spacing (the tightest chamber spacing in the "
        "criteria is metres, not centimetres)."),
    "SUBNET_PAD_MIN": (
        SUBNET_PAD_MIN,
        "digits. Padding is global, taken from the town with the most subnetworks, so "
        "every S-token in the design is the same width and a plain text sort is a "
        "geographic sort. contract.SUBNET_RE already requires at least two. STRUCTURAL. "
        "KNOWN COST, measured 2026-09-06 and NOT fixed here because the remedy is the "
        "engineer's call: the width is recomputed from the design, so the day ONE town "
        "crosses 99 subnetworks every S-token in EVERY town widens and every gravity name "
        "in the design changes (S02 -> S002). Rule (e) - the same design rebuilt gets the "
        "same names - still holds; a design that GROWS does not. The manhole number takes "
        "the opposite choice: it is fixed at three digits and a subnetwork past 999 is "
        "FLAGGED (MH_SEQ_SORTS_TO) rather than repadded, and contract's own note says "
        "padding is a minimum width, not a fixed one. The two want reconciling."),
    "MH_SEQ_SORTS_TO": (
        MH_SEQ_SORTS_TO,
        "chambers in one subnetwork. concept_name() pads a manhole number to three digits, "
        "so a subnetwork past this stops sorting as text (M1000 < M999). Not fixed here - "
        "FLAGGED, because a subnetwork that big is the defect concept rule 2 exists to "
        "stop, and renaming round it would hide it. STRUCTURAL."),
}


# WHICH TIERS THE GRAMMAR CAN ACTUALLY EXPRESS - probed, never listed.
#
# `contract.TIER_TOKEN` maps five tiers to tokens (R / L / M / SM / TM) but `contract.NAME_RE`
# admits only TM, SM and L - the three the engineer named. So a chamber whose TIER is 'main'
# or 'rider' formats as I-S01-M-M003 and then FAILS the contract's own grammar check, which
# is the sort of contradiction that ships a column nobody can filter. This set is derived by
# BUILDING a probe name for each tier and parsing it back, so it cannot go stale if contract
# changes; anything outside it is FLAGGED rather than written (concept rule 7).
GRAMMAR_TIERS: frozenset = frozenset(
    t for t in TIERS
    if parse_name(concept_name("I", "manhole", subnet="S01", tier=t, seq=1)) is not None)


RUNS_AFTER: Tuple[str, ...] = (
    "s2_orient   - the tree, so DS_NODE exists and every node has one downstream node",
    "s3_hierarchy - TIER, so the manhole's tier token can be written",
    "s4_chambers  - the chambers themselves, so there is something to number",
    "s7_pumps     - the stations and their rising mains, so a pump has a number to share",
)


class NamingError(ContractError):
    """Something in the naming input is wrong. Subclasses ContractError so a stage that
    already catches contract failures catches these too."""


class NamingOrderError(NamingError):
    """Naming was asked to run before connectivity was known. This is the ORDERING
    REQUIREMENT of the engineer's rule (b) made mechanical rather than documented."""


# ======================================================================================
# PATHS
# ======================================================================================

def _project_root() -> str:
    """.../2621 Ibri Sewer STP - walked up from this file, same as w12.asbuilt."""
    env = os.environ.get("W12_PROJECT_ROOT")
    if env:
        return env
    here = os.path.abspath(os.path.dirname(__file__))   # .../Hydraulic/Claude/W12/py/w12
    return os.path.abspath(os.path.join(here, "..", "..", "..", "..", ".."))


def _w12_root() -> str:
    env = os.environ.get("W12_ROOT")
    if env:
        return env
    here = os.path.abspath(os.path.dirname(__file__))
    return os.path.abspath(os.path.join(here, "..", ".."))     # .../W12


def default_towns_path() -> str:
    """The gazetteer. 25 settlement polygons, EPSG:32640, one row per town."""
    return os.path.join(_project_root(), "Hydraulic", "SHP", "Towns", "Towns.shp")


def default_prefix_path() -> str:
    """Where the frozen town-prefix mapping lives once it is issued."""
    return os.path.join(_w12_root(), "run", "W12_town_prefixes.csv")


# ======================================================================================
# SMALL HELPERS
# ======================================================================================

def _blank(s: pd.Series) -> np.ndarray:
    """True where a value is missing in ANY of the forms a round trip produces.

    A GeoPackage stores an empty string; a shapefile DBF hands back None; `astype(str)` on
    a NaN gives the literal 'nan'. contract._blank exists for the same reason and this is
    the same trap - a station's legitimately blank SUBNET must not come back as 'nan'.
    """
    v = pd.Series(s)
    out = v.isna().to_numpy()
    txt = v.astype(str).str.strip().str.lower()
    return out | txt.isin(["", "nan", "none", "<na>", "null"]).to_numpy()


def _str(s: pd.Series) -> np.ndarray:
    """A string column with every blank form normalised to ''."""
    v = pd.Series(s)
    return np.where(_blank(v), "", v.astype(str).str.strip().to_numpy()).astype(object)


def _need(df: pd.DataFrame, cols: Sequence[str], what: str) -> None:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise NamingError(f"{what} is missing {missing}. naming needs {list(cols)}; it "
                          "reads the graph, so a frame with geometry but no topology "
                          "cannot be named (contract H16: topology is written down, never "
                          "inferred from geometry).")


def _q(a) -> np.ndarray:
    """Coordinates quantised for use as a SORT KEY. Never for a distance, never published.

    A NON-FINITE coordinate is REFUSED rather than cast. `np.nan.astype(int64)` gives
    INT64_MIN behind a RuntimeWarning nobody reads on a 57,000-row run, so every element
    with no coordinate sorted to one extreme and was named as though it had a position -
    a fabricated ordering, which is the class of defect this project has paid most for.
    """
    v = np.asarray(a, dtype=float)
    bad = ~np.isfinite(v)
    if bad.any():
        raise NamingError(
            f"{int(bad.sum()):,} of {v.size:,} coordinates are NaN or infinite, and a "
            "coordinate is a SORT KEY here: numpy casts a NaN to INT64_MIN behind a "
            "RuntimeWarning, so the element would sort to one extreme and be named as "
            "though it had a position. Give it a coordinate, or leave it out of the frame "
            "and flag it upstream - naming will not order on a value that is not a number.")
    return np.round(v / ORDER_QUANT_M).astype(np.int64)


def _pad_width(n_max: int, floor: int) -> int:
    return max(int(floor), len(str(int(max(1, n_max)))))


# ======================================================================================
# THE TOWN GAZETTEER
# ======================================================================================

@dataclass
class TownIndex:
    """The settlement names, their codes, and (when loaded from the layer) their polygons.

    Two ways in, deliberately:

        TownIndex.load()                 reads Towns.shp - codes AND point-in-polygon
        TownIndex.from_names([...])      codes only, no geometry, no geopandas import

    The second exists so the naming logic can be tested in milliseconds without a spatial
    library, and so a caller who has already located its own points can pass the town names
    straight in.
    """

    names: Tuple[str, ...]
    codes: Dict[str, str]
    source: str = ""
    name_field: str = TOWN_NAME_FIELD
    frozen_from: str = ""
    _gdf: object = field(default=None, repr=False, compare=False)

    # ---- construction ----------------------------------------------------------------

    @classmethod
    def from_names(cls, names: Iterable[str], *, source: str = "(names)",
                   frozen: Optional[Mapping[str, str]] = None) -> "TownIndex":
        clean: List[str] = []
        for n in names:
            s = str(n).strip()
            if s and s.lower() not in ("nan", "none"):
                clean.append(s)
        uniq = tuple(sorted(set(clean)))
        if not uniq:
            raise NamingError("no settlement names to build town codes from")
        codes = dict(town_letters(uniq))
        if frozen:
            codes = cls._apply_frozen(codes, frozen)
        return cls(names=uniq, codes=codes, source=source,
                   frozen_from=("(frozen mapping)" if frozen else ""))

    @classmethod
    def load(cls, path: Optional[str] = None, *, field_name: str = TOWN_NAME_FIELD,
             frozen: Optional[str] = None) -> "TownIndex":
        """Read the gazetteer layer. Needs geopandas; imported here rather than at module
        top so the pure-graph half of this file has no spatial dependency."""
        import geopandas as gpd

        p = path or default_towns_path()
        if not os.path.isfile(p):
            raise NamingError(
                f"towns layer not found: {p}\nIt is the source of every town letter. Pass "
                "path=, set W12_PROJECT_ROOT, or build the index with "
                "TownIndex.from_names([...]) if you already hold the names.")
        g = gpd.read_file(p)
        if field_name not in g.columns:
            raise NamingError(f"{os.path.basename(p)} has no field {field_name!r}. It "
                              f"holds {[c for c in g.columns if c != 'geometry'][:8]}. "
                              "The town letter can only come from a field with letters in "
                              "it - CODE and TOWN on this layer are numeric ids.")
        if g.crs is not None and g.crs.to_epsg() not in (None, CRS_EPSG):
            raise NamingError(
                f"{os.path.basename(p)} is EPSG:{g.crs.to_epsg()}, not EPSG:{CRS_EPSG}. "
                "Every W12 layer is in the project CRS and the node X/Y this index is "
                "asked to locate are metres in it - reprojecting silently would put a "
                "chamber in the wrong town.")
        frozen_map = load_town_prefixes(frozen) if frozen else None
        idx = cls.from_names(g[field_name].tolist(), source=p, frozen=frozen_map)
        idx = TownIndex(names=idx.names, codes=idx.codes, source=p,
                        name_field=field_name, frozen_from=(frozen or ""), _gdf=g)
        return idx

    @staticmethod
    def _apply_frozen(derived: Dict[str, str], frozen: Mapping[str, str]) -> Dict[str, str]:
        """A frozen code WINS. Once a mapping has been issued, a drawing quotes it; a new
        town appearing in the layer may not renumber the ones already out of the door."""
        out = dict(derived)
        for name, code in frozen.items():
            if name in out:
                out[name] = str(code)
        return out

    # ---- the codes -------------------------------------------------------------------

    def code(self, town_name: str) -> str:
        """The code for one settlement name, or '' when it is not in the gazetteer."""
        return self.codes.get(str(town_name).strip(), "")

    @property
    def by_code(self) -> Dict[str, str]:
        return {c: n for n, c in self.codes.items()}

    def clash_table(self) -> pd.DataFrame:
        """One row per town, with the single-letter code it WOULD have had and who it
        collided with. This is the evidence for the extension rule, not a claim about it."""
        first = {n: town_letter(n, 1) for n in self.names}
        groups: Dict[str, List[str]] = {}
        for n, c in first.items():
            groups.setdefault(c, []).append(n)
        rows = []
        for n in self.names:
            grp = sorted(x for x in groups[first[n]] if x != n)
            rows.append(dict(NAME=n, KEY=self._key(n), CODE=self.codes[n],
                             LETTERS=len(self.codes[n]), FIRST=first[n],
                             CLASHED_WITH="; ".join(grp), N_CLASH=len(grp)))
        return pd.DataFrame(rows).sort_values("NAME").reset_index(drop=True)

    @staticmethod
    def _key(name: str) -> str:
        """The de-articled letters the code is taken from - shown so the reader can see
        WHY 'Ad Dariz' is DA and not AD."""
        return town_letter(name, 99).lower()

    def check_frozen(self, path: Optional[str] = None) -> pd.DataFrame:
        """Compare the codes in use against a frozen file. Returns the DRIFT, empty when
        they agree. Drift is reported, never applied silently: a code that has been issued
        on a drawing is a fact about the world, not a preference."""
        frozen = load_town_prefixes(path or default_prefix_path())
        rows = []
        for name in sorted(set(frozen) | set(self.codes)):
            was, now = frozen.get(name, ""), self.codes.get(name, "")
            if was != now:
                rows.append(dict(NAME=name, FROZEN=was, NOW=now,
                                 WHY=("new town" if not was else
                                      "town gone from the layer" if not now else
                                      "CODE CHANGED - a drawing may already quote the old one")))
        return pd.DataFrame(rows, columns=["NAME", "FROZEN", "NOW", "WHY"])

    # ---- geometry --------------------------------------------------------------------

    @property
    def has_geometry(self) -> bool:
        return self._gdf is not None

    def locate(self, x, y) -> np.ndarray:
        """Town NAME for each point, '' where the point is outside every town.

        A point in two overlapping polygons takes the one whose name sorts first, so the
        answer does not depend on the join's row order. Overlaps are reported by
        `overlap_count()` rather than being assumed away.
        """
        if not self.has_geometry:
            raise NamingError(
                "this TownIndex has no geometry (built with from_names), so it cannot "
                "locate a point. Either build it with TownIndex.load(), or pass the town "
                "names you have already located to name_network(node_town=...).")
        import geopandas as gpd
        from shapely.geometry import Point

        xa = np.asarray(x, dtype=float)
        ya = np.asarray(y, dtype=float)
        if xa.shape != ya.shape:
            raise NamingError("x and y must be the same length")
        pts = gpd.GeoDataFrame({"_i": np.arange(xa.size)},
                               geometry=[Point(float(a), float(b)) for a, b in zip(xa, ya)],
                               crs=self._gdf.crs)
        poly = self._gdf[[self.name_field, "geometry"]].copy()
        poly["_town"] = poly[self.name_field].astype(str).str.strip()
        j = gpd.sjoin(pts, poly[["_town", "geometry"]], how="left", predicate="within")
        # deterministic on an overlap: sort by (_i, _town) and keep the first
        j = j.sort_values(["_i", "_town"], kind="mergesort")
        j = j.drop_duplicates("_i", keep="first")
        out = np.full(xa.size, "", dtype=object)
        got = j["_town"].to_numpy(dtype=object)
        idx = j["_i"].to_numpy(dtype=np.int64)
        got = np.where(pd.isna(got), "", got)
        out[idx] = got
        return out

    def distance_to(self, town_name: str, x: float, y: float) -> float:
        """Metres from a point to a town polygon - a deterministic tie-break, nothing more."""
        if not self.has_geometry:
            return float("inf")
        from shapely.geometry import Point
        sel = self._gdf[self._gdf[self.name_field].astype(str).str.strip() == str(town_name)]
        if not len(sel):
            return float("inf")
        p = Point(float(x), float(y))
        return float(min(g.distance(p) for g in sel.geometry))

    def overlap_count(self) -> int:
        """How many town polygons overlap another. Zero on the issued gazetteer; a non-zero
        answer means `locate()` is choosing between two right answers."""
        if not self.has_geometry:
            return 0
        g = self._gdf.geometry
        n = 0
        for i in range(len(g)):
            for k in range(i + 1, len(g)):
                if g.iloc[i].intersects(g.iloc[k]) and \
                        g.iloc[i].intersection(g.iloc[k]).area > 0:
                    n += 1
        return n


# ======================================================================================
# FREEZING THE MAPPING (engineer's rule f)
# ======================================================================================

def _mapping_digest(codes: Mapping[str, str]) -> str:
    """A checksum over the mapping itself, so a frozen file can be checked without
    re-deriving it. Sorted, so the digest does not depend on dict order."""
    body = "\n".join(f"{k}={codes[k]}" for k in sorted(codes))
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def write_town_prefixes(index: TownIndex, path: Optional[str] = None) -> str:
    """Emit the town-prefix mapping so it can be FROZEN once issued.

    Writes two files beside each other:

        W12_town_prefixes.csv    one row per town: name, de-articled key, code, the single
                                 letter it would have had, and who it collided with
        W12_town_prefixes.json   the same mapping plus a sha256, the source layer and field,
                                 and the date - the manifest a later run checks against

    Returns the CSV path.
    """
    p = os.path.abspath(path or default_prefix_path())
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tab = index.clash_table()
    tab.to_csv(p, index=False, encoding="utf-8")
    man = {
        "generated": _dt.date.today().isoformat(),
        "source_layer": index.source,
        "name_field": index.name_field,
        "clash_universe": ASSUMPTIONS["TOWN_CLASH_UNIVERSE"][0],
        "n_towns": len(index.names),
        "n_single_letter": int((tab.LETTERS == 1).sum()),
        "n_clashing": int((tab.N_CLASH > 0).sum()),
        "sha256": _mapping_digest(index.codes),
        "codes": {n: index.codes[n] for n in sorted(index.codes)},
        "note": ("FROZEN ONCE ISSUED. A code that has appeared on a drawing may not change. "
                 "TownIndex.load(frozen=<this file>) reads it back and a new town cannot "
                 "renumber an existing one; TownIndex.check_frozen() reports drift."),
    }
    with open(os.path.splitext(p)[0] + ".json", "w", encoding="utf-8") as fh:
        json.dump(man, fh, indent=2, ensure_ascii=False)
    return p


def load_town_prefixes(path: Optional[str] = None) -> Dict[str, str]:
    """Read a frozen mapping back. Accepts either the .csv or the .json."""
    p = os.path.abspath(path or default_prefix_path())
    if p.lower().endswith(".json"):
        jp, cp = p, os.path.splitext(p)[0] + ".csv"
    else:
        jp, cp = os.path.splitext(p)[0] + ".json", p
    def _from_csv(path: str) -> Dict[str, str]:
        t = pd.read_csv(path, encoding="utf-8")
        _need(t, ["NAME", "CODE"], os.path.basename(path))
        return {str(a).strip(): str(b).strip() for a, b in zip(t.NAME, t.CODE)}

    if os.path.isfile(jp):
        with open(jp, "r", encoding="utf-8") as fh:
            man = json.load(fh)
        codes = {str(k): str(v) for k, v in man.get("codes", {}).items()}
        if codes and man.get("sha256") and _mapping_digest(codes) != man["sha256"]:
            raise NamingError(
                f"{os.path.basename(jp)} has been edited: its codes do not match its own "
                "sha256. Re-issue the mapping with write_town_prefixes() rather than "
                "hand-editing it - a code nobody can check is a code nobody can trust.")
        # THE CSV IS THE FILE A PERSON READS AND THEREFORE THE FILE A PERSON EDITS, and it
        # was silently ignored whenever the JSON was present: the manifest passed its own
        # checksum, the codes came back from the manifest, and the mapping on the drawing
        # said something else with nothing reporting the disagreement.
        if os.path.isfile(cp):
            try:
                from_csv = _from_csv(cp)
            except NamingError:
                from_csv = None
            if from_csv is not None and from_csv != codes:
                diff = sorted(n for n in set(from_csv) | set(codes)
                              if from_csv.get(n, "") != codes.get(n, ""))
                raise NamingError(
                    f"{os.path.basename(cp)} and {os.path.basename(jp)} disagree on "
                    f"{len(diff)} town(s) (e.g. {diff[:4]}). The CSV is the sheet a person "
                    "reads, the JSON is the one that carries the checksum - a mapping that "
                    "is issued twice and says two things is not frozen. Re-issue both with "
                    "write_town_prefixes().")
        return codes
    if os.path.isfile(cp):
        # a CSV on its own carries NO checksum, so the tamper the JSON path refuses walks
        # straight in through this door. Refuse it by name rather than trusting it.
        raise NamingError(
            f"{os.path.basename(cp)} exists but its manifest {os.path.basename(jp)} does "
            "not. The CSV carries no checksum, so a hand edit to it cannot be detected - "
            "which is the exact tamper the manifest exists to refuse. Re-issue the pair "
            "with write_town_prefixes(); it writes both files together.")
    raise NamingError(f"no frozen town-prefix file at {cp} or {jp}. Write one with "
                      "write_town_prefixes(TownIndex.load()).")


# ======================================================================================
# THE GRAPH - roots, depths, subtree sizes. All of it ordering-free.
# ======================================================================================

def _index_map(uids: np.ndarray, what: str) -> Dict[str, int]:
    seen: Dict[str, int] = {}
    dup: List[str] = []
    for i, u in enumerate(uids):
        if u in seen:
            dup.append(u)
        else:
            seen[u] = i
    if dup:
        raise NamingError(f"{what} has {len(dup):,} duplicate keys (e.g. {sorted(set(dup))[:4]}). "
                          "Identity must be unique before anything can be named by it.")
    return seen


def _follow(parent: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """root[] and depth[] for a forest given as a parent array (-1 = a root).

    Iterative with path compression, so a 57,000-node chain does not need 57,000 stack
    frames, and cycle-safe: a cycle raises with the nodes in it rather than hanging.
    """
    n = parent.size
    root = np.full(n, -1, dtype=np.int64)
    depth = np.full(n, -1, dtype=np.int64)
    onpath = np.zeros(n, dtype=bool)
    for start in range(n):
        if root[start] >= 0:
            continue
        path: List[int] = []
        i = int(start)
        while i >= 0 and root[i] < 0:
            if onpath[i]:
                cyc = path[path.index(i):]
                raise NamingError(
                    f"the DS_NODE chain contains a CYCLE of {len(cyc)} nodes (indices "
                    f"{cyc[:6]}). The network must be a forest (philosophy H15); a cycle "
                    "means the tree was written down wrong, and naming would loop forever "
                    "trying to find the outfall.")
            onpath[i] = True
            path.append(i)
            i = int(parent[i])
        if i < 0:
            # the walk fell off the end: the last node on the path IS the root, depth 0
            r, d = path[-1], 0
        else:
            # the walk met a node already resolved. The last node on the path is its CHILD,
            # so it is one deeper - NOT the same depth.
            #
            # This +1 was missing on 2026-09-06 and the bug is worth the comment. Depth is
            # only used to ORDER things (the town propagation and the subtree-size
            # accumulation), so a wrong depth produced no error and no wrong root - it
            # produced NAMES THAT MOVED WHEN THE ROWS MOVED, on 34,932 of 56,930 chambers,
            # silently. The synthetic fixtures were too symmetric to show it; the real
            # published layer showed it in one run.
            r, d = int(root[i]), int(depth[i]) + 1
        for k in reversed(path):
            root[k] = r
            depth[k] = d
            d += 1
            onpath[k] = False

    # The invariant, checked rather than trusted, because nothing downstream would notice
    # it being wrong: a node is exactly one deeper than its parent, and a root is depth 0.
    has_p = parent >= 0
    if has_p.any() and not (depth[has_p] == depth[parent[has_p]] + 1).all():
        bad = int((depth[has_p] != depth[parent[has_p]] + 1).sum())
        raise NamingError(
            f"_follow() produced an inconsistent depth on {bad:,} nodes. Depth ORDERS the "
            "town propagation and the subtree-size accumulation, so a wrong one does not "
            "fail - it makes the numbering depend on row order, which is the one property "
            "naming must never lose.")
    if (depth[~has_p] != 0).any():
        raise NamingError("_follow() gave a root a non-zero depth")
    return root, depth


def _subtree_sizes(parent: np.ndarray, depth: np.ndarray) -> np.ndarray:
    """Nodes at or above each node. Accumulated deepest-first, so no recursion."""
    size = np.ones(parent.size, dtype=np.int64)
    for i in np.argsort(-depth, kind="stable"):
        p = int(parent[int(i)])
        if p >= 0:
            size[p] += size[int(i)]
    return size


# ======================================================================================
# THE RESULT
# ======================================================================================

@dataclass
class NamingResult:
    """What naming produced, and - just as important - what it refused to produce.

    `nodes` / `reaches` / `stations` / `rising_mains` are COPIES of the frames handed in,
    with NAME, TOWN and SUBNET written. Nothing is mutated in place: another stage may hold
    the same frame, and a naming pass that edited it underneath them would be the silent
    kind of defect this project has paid most for.
    """

    nodes: pd.DataFrame
    reaches: Optional[pd.DataFrame]
    stations: Optional[pd.DataFrame]
    rising_mains: Optional[pd.DataFrame]
    subnets: pd.DataFrame
    node_towns: pd.DataFrame
    flags: pd.DataFrame
    counts: Dict[str, int]
    towns: Optional[TownIndex] = field(default=None, repr=False)

    # ---- convenience -----------------------------------------------------------------

    def name_map(self) -> Dict[str, str]:
        """Every element's key -> its name, in ONE dict. The stability test compares two
        of these; a drawing that quotes a name can be checked against it."""
        out: Dict[str, str] = {}
        for df, key in ((self.nodes, "NODE_UID"), (self.reaches, "EDGE_UID"),
                        (self.stations, "NODE_UID"), (self.rising_mains, "EDGE_UID")):
            if df is None or key not in df.columns:
                continue
            pre = "ST:" if (df is self.stations) else ("RM:" if df is self.rising_mains else "")
            for k, v in zip(df[key].astype(str), df["NAME"].astype(str)):
                out[pre + k] = v
        return out

    def flags_by_kind(self) -> pd.Series:
        if not len(self.flags):
            return pd.Series(dtype=int)
        return self.flags.groupby("KIND").size().sort_values(ascending=False)

    def report(self) -> str:
        c = self.counts
        L: List[str] = []
        A = L.append
        A("W12 NAMING")
        A("=" * 66)
        A(f"  towns in the gazetteer   {c['towns_total']:>8,}   "
          f"({c['towns_single_letter']} keep one letter, {c['towns_clashing']} collided)")
        A(f"  towns actually used      {c['towns_used']:>8,}")
        A(f"  subnetworks              {c['subnets']:>8,}   "
          f"({c['subnets_main']} of them main-pipe runs)")
        A(f"  chambers named           {c['nodes_named']:>8,} of {c['nodes_total']:,}")
        A(f"  conduits named           {c['reaches_named']:>8,} of {c['reaches_total']:,}")
        A(f"  pumps named              {c['stations_named']:>8,} of {c['stations_total']:,}")
        A(f"  force mains named        {c['mains_named']:>8,} of {c['mains_total']:,}")
        A("")
        A("  CHANGE against the names the frames arrived with "
          "(inheritance row 4: a pass that ADDS must be able to TAKE AWAY)")
        A(f"    kept the same          {c['unchanged']:>8,}")
        A(f"    renamed                {c['renamed']:>8,}")
        A(f"    WITHDRAWN              {c['withdrawn']:>8,}   "
          "had a name, has none now - each one is flagged below")
        A("")
        A(f"  town taken from the polygon it sits in   {c['town_inside']:>8,}")
        A(f"  town taken from the first town DOWNSTREAM {c['town_downstream']:>7,}   "
          "(engineer's rule b)")
        A(f"  no town resolvable                      {c['town_none']:>8,}")
        if len(self.flags):
            A("")
            A(f"  FLAGGED, NOT SOLVED - {len(self.flags):,} rows (concept rule 7)")
            for kind, n in self.flags_by_kind().items():
                ex = self.flags[self.flags.KIND == kind].iloc[0]
                A(f"    {kind:<20} {int(n):>7,}   e.g. {ex.REF}: {ex.WHY}")
        else:
            A("")
            A("  nothing flagged - every element resolved to a town, a subnetwork and a number")
        return "\n".join(L)


# ======================================================================================
# THE GATE - naming runs after connectivity is known (rule b)
# ======================================================================================

def assert_ready(nodes: pd.DataFrame, *, key: str = "NODE_UID",
                 ds_col: str = "DS_NODE") -> None:
    """Refuse to name a frame whose connectivity is not written down yet.

    This is the engineer's rule (b) made mechanical. An element outside a town takes the
    letter of the first town DOWNSTREAM of it, so naming CANNOT run before the tree exists.
    A stage that calls this and gets an exception is being told the ordering, not blocked.
    """
    _need(nodes, [key, ds_col, "X", "Y"], "nodes")
    if not len(nodes):
        raise NamingOrderError("the nodes frame is empty - nothing to name. Naming runs "
                               "after " + RUNS_AFTER[2].split(" - ")[0].strip() + ".")
    ds = _str(nodes[ds_col])
    if not (ds != "").any():
        raise NamingOrderError(
            f"every {ds_col} is blank, so the graph has no downstream direction and the "
            "rule 'an element outside a town takes the letter of the first town DOWNSTREAM "
            "of it' cannot be applied.\nNaming runs after:\n  " + "\n  ".join(RUNS_AFTER))


def clear_names(gdf: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """Blank NAME / TOWN / SUBNET and say how many names were removed.

    The counterpart to naming, and it exists on purpose: inheritance-ledger row 4 says
    anything a pass can ADD a later pass must be able to TAKE AWAY, and the stage must
    publish how many it removed. Losing that rule for pumping stations cost the last
    iteration 69 spurious stations.
    """
    out = gdf.copy()
    had = 0
    if "NAME" in out.columns:
        had = int((~_blank(out["NAME"])).sum())
    for c in ("NAME", "TOWN", "SUBNET"):
        out[c] = ""
    return out, had


# ======================================================================================
# THE ASSIGNMENT
# ======================================================================================

def name_network(nodes: pd.DataFrame,
                 *,
                 reaches: Optional[pd.DataFrame] = None,
                 stations: Optional[pd.DataFrame] = None,
                 rising_mains: Optional[pd.DataFrame] = None,
                 towns: Optional[TownIndex] = None,
                 node_town: Optional[Sequence[str]] = None,
                 key: str = "NODE_UID",
                 ds_col: str = "DS_NODE",
                 tier_col: str = "TIER",
                 main_tier: str = MAIN_TIER,
                 is_main: Optional[Sequence[bool]] = None,
                 subnet_order: Optional[Sequence[float]] = None) -> NamingResult:
    """Give every element in a design its name. See the module docstring for the grammar.

    Parameters
    ----------
    nodes
        The chamber frame. Needs `NODE_UID`, `DS_NODE`, `X`, `Y` and `TIER`.
    reaches, stations, rising_mains
        Optional. A reach needs `EDGE_UID` and `US_NODE`; a station needs `NODE_UID`,
        `X`, `Y`; a rising main needs `EDGE_UID` and either `STATION` or `US_NODE`.
    towns
        A `TownIndex`. With geometry it locates the chambers itself; without geometry
        `node_town` must be supplied.
    node_town
        Optional pre-located town NAME per node (not code) - '' where the node is outside
        every town. Use it when the caller has already done the spatial join.
    is_main
        Optional boolean mask marking the main pipe. Defaults to `TIER == main_tier`.
    subnet_order
        Optional numeric key per NODE, read at the subnetwork's OUTFALL - e.g. chainage
        along the main pipe, so subnetworks number downstream to upstream. It sits INSIDE
        the town and after the main-pipe-first rule (the full key is TOWN, main-first,
        this, then north to south, then the outfall id), so it reorders subnetworks within
        a town and cannot move one between towns or ahead of the trunk. When absent the
        ordering is north to south, which is fully determined on its own.

    Returns
    -------
    NamingResult - copies of the frames with NAME/TOWN/SUBNET written, the subnets table,
    the per-node town resolution, and the flags for everything it refused to name.
    """
    assert_ready(nodes, key=key, ds_col=ds_col)
    _need(nodes, [tier_col], "nodes")

    nd = nodes.copy()
    n = len(nd)
    uid = _str(nd[key])
    ds_uid = _str(nd[ds_col])
    xs = nd["X"].to_numpy(dtype=float)
    ys = nd["Y"].to_numpy(dtype=float)
    tier = np.array([str(t).strip().lower() for t in nd[tier_col].to_numpy()], dtype=object)

    idx_of = _index_map(uid, "nodes." + key)
    ds_idx = np.array([idx_of.get(u, -1) for u in ds_uid], dtype=np.int64)
    # A DS_NODE that names a chamber which is not in the frame is a BROKEN LINK, not a
    # terminal. Treating it as one invents an outfall and a whole subnetwork around it, so
    # it is recorded here and flagged with its size once the subtrees are known.
    dangling = np.nonzero((ds_uid != "") & (ds_idx < 0))[0]

    flags: List[dict] = []

    def flag(kind: str, ref: str, why: str, size: float = 0.0) -> None:
        flags.append(dict(KIND=kind, REF=str(ref), WHY=why, SIZE=float(size)))

    # ---- 1. main-pipe mask -----------------------------------------------------------
    if is_main is not None:
        main = np.asarray(is_main, dtype=bool)
        if main.size != n:
            raise NamingError("is_main must have one value per node")
        main_src = "caller's mask"
    else:
        mt = str(main_tier).strip().lower()
        mt = TIER_ALIASES.get(mt, mt)
        if mt not in TIERS:
            # A misspelling here does not fail - it produces an EMPTY main-pipe mask, and
            # then concept rule 2 (no subnetwork crosses the main pipe and grows past it)
            # silently stops being applied: every branch merges into one subnetwork and
            # nothing says so. 'trunk_main' is the exact spelling contract.TIER_ALIASES
            # exists for, so it is the one a caller will reach for.
            raise NamingError(
                f"main_tier={main_tier!r} is not one of {list(TIERS)} (aliases: "
                f"{sorted(TIER_ALIASES)}). An unrecognised tier would mark NO chamber as "
                "main pipe, and concept rule 2 - a subnetwork stops where it MEETS the "
                "main pipe - would quietly stop being applied. Pass a tier, or pass an "
                "explicit is_main mask.")
        main = tier == mt
        main_src = f"{tier_col} == {mt!r}"

    # ---- 2. the town of every node ---------------------------------------------------
    if node_town is not None:
        loc = np.array([str(t).strip() if t is not None else "" for t in node_town],
                       dtype=object)
        if loc.size != n:
            raise NamingError("node_town must have one value per node")
        if towns is None:
            towns = TownIndex.from_names([t for t in loc if t], source="(node_town)")
    else:
        if towns is None:
            towns = TownIndex.load()
        loc = towns.locate(xs, ys)

    unknown = sorted({t for t in loc if t and towns.code(t) == ""})
    if unknown:
        raise NamingError(
            f"{len(unknown)} located town name(s) are not in the gazetteer "
            f"({unknown[:4]}). The code set must be resolved over ONE list of towns or two "
            "stages will disagree about which town is 'A'.")

    # rule (b): an element outside every town takes the letter of the first town DOWNSTREAM.
    # Resolved by walking down the tree, cheapest-first: depth 0 (terminals) cannot inherit,
    # then each node takes its own town or, failing that, its downstream node's resolved one.
    root0, depth0 = _follow(ds_idx)
    town_name = loc.copy()
    town_src = np.where(loc != "", "inside", "").astype(object)
    for i in np.argsort(depth0, kind="stable"):      # shallow (downstream) first
        i = int(i)
        if town_name[i]:
            continue
        j = int(ds_idx[i])
        if j >= 0 and town_name[j]:
            town_name[i] = town_name[j]
            town_src[i] = "downstream"
    town_code = np.array([towns.code(t) if t else "" for t in town_name], dtype=object)
    for i in np.nonzero(town_code == "")[0]:
        flag("node_no_town", uid[int(i)],
             "outside every town polygon and nothing downstream of it is in one, so rule "
             "(b) has no town to borrow. Serve it, reroute it, or extend the gazetteer.",
             1.0)
    town_src = np.where(town_code == "", "unresolved", town_src).astype(object)

    # ---- 3. the subnetworks ----------------------------------------------------------
    # A branch subnetwork ends where it MEETS the main pipe (concept rule 2). A main-pipe
    # chamber belongs to the trunk run through its own town - see ASSUMPTIONS/MAIN_AS_SUBNET.
    stay = np.zeros(n, dtype=bool)
    for i in range(n):
        j = int(ds_idx[i])
        if j < 0:
            continue
        if main[i]:
            stay[i] = bool(main[j]) and (town_code[i] == town_code[j])
        else:
            stay[i] = not bool(main[j])
    parent = np.where(stay, ds_idx, -1)
    root, depth = _follow(parent)
    size = _subtree_sizes(parent, depth)

    for i in dangling:
        i = int(i)
        flag("node_ds_missing", uid[i],
             f"DS_NODE is {ds_uid[i]!r}, which is not a chamber in this frame. The link is "
             "BROKEN, not absent: naming had to treat the chamber as an outfall, so it and "
             "everything above it were given their own subnetwork number and a name that "
             "says they discharge here. Restore the downstream chamber, or record the real "
             "terminal", float(size[i]))

    outfalls = np.unique(root)
    sub_rows: List[dict] = []
    for r in outfalls:
        r = int(r)
        mem = np.nonzero(root == r)[0]
        is_m = bool(main[r])
        # the town of the subnetwork: plurality of the members that are INSIDE a town
        inside = mem[(town_src[mem] == "inside")]
        if inside.size:
            vals, cnt = np.unique(town_code[inside].astype(str), return_counts=True)
            best = int(cnt.max())
            tied = sorted(vals[cnt == best])
            if len(tied) == 1:
                code = tied[0]
                why = "plurality"
            else:
                # deterministic tie-break: nearest town polygon to the outfall, then code
                d = {c: towns.distance_to(towns.by_code.get(c, ""), xs[r], ys[r])
                     for c in tied}
                code = sorted(tied, key=lambda c: (d[c], c))[0]
                why = f"tie between {tied} broken on distance from the outfall"
            # SHARE OF THE WHOLE SUBNETWORK, not of the part that is inside some town.
            # Read it as "how much of the thing wearing this letter is actually in that
            # town": a low share means most of its chambers are outside every settlement,
            # which is a fact about where the design goes, not a close-run plurality.
            # Measured on the published 56,930-chamber graph 2026-09-06: 82 of 278
            # subnetworks straddle a boundary and the lowest share is 0.019.
            share = best / float(mem.size)
        else:
            code = str(town_code[r])
            share = 0.0
            why = ("no chamber inside any town - rule (b), the first town downstream of "
                   "the outfall") if code else "no town resolvable"
        sub_rows.append(dict(_ROOT=r, IS_MAIN=int(is_m), TOWN=code, N_NODES=int(mem.size),
                             OUTFALL=uid[r], X=float(xs[r]), Y=float(ys[r]),
                             TOWN_SHARE=float(share), TOWN_WHY=why))

    subs = pd.DataFrame(sub_rows)

    # ORDER. Nothing here may come from row order: the key is (main first, an optional
    # caller key, then the outfall north to south on quantised coordinates, then the
    # outfall's own id as a last resort so the sort is total).
    if subnet_order is not None:
        so = np.asarray(subnet_order, dtype=float)
        if so.size != n:
            raise NamingError("subnet_order must have one value per node")
        subs["_ORD"] = [float(so[int(r)]) for r in subs._ROOT]
    else:
        subs["_ORD"] = 0.0
    subs["_MAINFIRST"] = 1 - subs.IS_MAIN
    subs["_NY"] = [-int(v) for v in _q(subs.Y.to_numpy())]
    subs["_NX"] = [int(v) for v in _q(subs.X.to_numpy())]
    subs = subs.sort_values(["TOWN", "_MAINFIRST", "_ORD", "_NY", "_NX", "OUTFALL"],
                            kind="mergesort").reset_index(drop=True)

    per_town = subs[subs.TOWN != ""].groupby("TOWN").size()
    pad = _pad_width(int(per_town.max()) if len(per_town) else 1, SUBNET_PAD_MIN)
    seq: Dict[str, int] = {}
    codes_out: List[str] = []
    for t in subs.TOWN:
        if not t:
            codes_out.append("")
            continue
        seq[t] = seq.get(t, 0) + 1
        codes_out.append(f"S{seq[t]:0{pad}d}")
    subs["SUBNET"] = codes_out
    subs["NAME"] = [concept_name(t, "subnet", subnet=s) if t and s else ""
                    for t, s in zip(subs.TOWN, subs.SUBNET)]

    for _, r in subs[subs.TOWN == ""].iterrows():
        flag("subnet_no_town", str(r.OUTFALL),
             "no chamber of this subnetwork is inside a town and nothing downstream of its "
             "outfall is either, so it has no letter and none of its chambers can be named",
             r.N_NODES)
    for _, r in subs[subs.N_NODES > MH_SEQ_SORTS_TO].iterrows():
        flag("subnet_over_999", f"{r.TOWN}-{r.SUBNET}" if r.SUBNET else str(r.OUTFALL),
             f"{int(r.N_NODES):,} chambers. concept_name() pads a manhole to three digits, "
             "so past 999 the names stop sorting as text - and a subnetwork this big is "
             "what concept rule 2 exists to prevent (no subnetwork crosses the main pipe "
             "and grows past it)", r.N_NODES)

    sub_of_root = {int(r._ROOT): (r.TOWN, r.SUBNET) for _, r in subs.iterrows()}

    # ---- 4. the chamber numbers ------------------------------------------------------
    # Depth-first upstream from each outfall, largest subtree first. `children` is built
    # from `parent`, so it holds graph facts; it is SORTED before it is walked, so the
    # frame's row order cannot reach the answer.
    children: Dict[int, List[int]] = {}
    for i in range(n):
        p = int(parent[i])
        if p >= 0:
            children.setdefault(p, []).append(i)
    nq, xq = -_q(ys), _q(xs)
    for p, kids in children.items():
        kids.sort(key=lambda k: (-int(size[k]), int(nq[k]), int(xq[k]), uid[k]))

    mh_seq = np.zeros(n, dtype=np.int64)
    for r in subs._ROOT:
        r = int(r)
        stack = [r]
        k = 0
        while stack:
            i = stack.pop()
            k += 1
            mh_seq[i] = k
            kids = children.get(i)
            if kids:
                stack.extend(reversed(kids))

    node_name = np.full(n, "", dtype=object)
    node_sub = np.full(n, "", dtype=object)
    node_town_code = np.full(n, "", dtype=object)
    for i in range(n):
        t, s = sub_of_root.get(int(root[i]), ("", ""))
        if not t or not s:
            continue
        node_town_code[i] = t
        node_sub[i] = s
        tk = TIER_TOKEN.get(tier[i], "")
        if not tk:
            flag("node_no_tier", uid[i],
                 f"TIER is {nd[tier_col].to_numpy()[i]!r}, which is not one of {list(TIERS)}. "
                 "The tier token is IN the manhole name, so it cannot be defaulted - that "
                 "would print a lateral's label on a trunk chamber", 1.0)
            continue
        if tier[i] not in GRAMMAR_TIERS:
            flag("node_tier_ungrammatical", uid[i],
                 f"TIER {tier[i]!r} formats as token {tk!r}, which contract.NAME_RE does not "
                 f"admit - the grammar carries only {sorted(GRAMMAR_TIERS)}. Writing the name "
                 "anyway would put a value on the layer that the contract's own check "
                 "rejects. Either retier the chamber or widen NAME_RE; naming will not "
                 "invent a token", 1.0)
            continue
        node_name[i] = concept_name(t, "manhole", subnet=s, tier=tier[i],
                                    seq=int(mh_seq[i]))

    # ---- 5. write the node frame -----------------------------------------------------
    had_name = _str(nd["NAME"]) if "NAME" in nd.columns else np.full(n, "", dtype=object)
    nd["NAME"] = node_name
    nd["TOWN"] = node_town_code
    nd["SUBNET"] = node_sub

    counts = dict(
        towns_total=len(towns.names),
        towns_single_letter=sum(1 for c in towns.codes.values() if len(c) == 1),
        towns_clashing=int((towns.clash_table().N_CLASH > 0).sum()),
        towns_used=int(len({t for t in node_town_code if t})),
        subnets=int(len(subs)), subnets_main=int(subs.IS_MAIN.sum()),
        nodes_total=n, nodes_named=int((node_name != "").sum()),
        town_inside=int((town_src == "inside").sum()),
        town_downstream=int((town_src == "downstream").sum()),
        town_none=int((town_src == "unresolved").sum()),
        main_nodes=int(main.sum()),
        reaches_total=0, reaches_named=0,
        stations_total=0, stations_named=0,
        mains_total=0, mains_named=0,
        unchanged=int(((had_name == node_name) & (node_name != "")).sum()),
        renamed=int(((had_name != "") & (node_name != "") & (had_name != node_name)).sum()),
        withdrawn=int(((had_name != "") & (node_name == "")).sum()),
    )

    # ---- 6. the conduits -------------------------------------------------------------
    rc = None
    if reaches is not None:
        rc = reaches.copy()
        _need(rc, ["EDGE_UID", "US_NODE"], "reaches")
        us = _str(rc["US_NODE"])
        eid = _str(rc["EDGE_UID"])
        # the same rule nodes get: a duplicate key makes name_map() - the oracle the
        # stability test compares - collapse two rows into one, so a name that moved
        # between runs could hide inside it
        _index_map(eid, "reaches.EDGE_UID")
        counts["reaches_total"] = len(rc)
        had_r = _str(rc["NAME"]) if "NAME" in rc.columns else np.full(len(rc), "", dtype=object)
        rname = np.full(len(rc), "", dtype=object)
        rsub = np.full(len(rc), "", dtype=object)
        rtown = np.full(len(rc), "", dtype=object)
        # a forest gives every chamber ONE outgoing reach; two reaches on one upstream
        # chamber is a graph defect, and suffixing the name would hide it
        seen_us: Dict[str, str] = {}
        for k in np.argsort(eid, kind="stable"):
            k = int(k)
            u = us[k]
            i = idx_of.get(u, -1)
            if i < 0:
                flag("reach_no_us_node", eid[k],
                     f"US_NODE {u!r} is not in the nodes frame, so the conduit has no "
                     "upstream chamber to take its number from", 1.0)
                continue
            if u in seen_us:
                flag("reach_dup_us_node", eid[k],
                     f"chamber {u} already has outgoing conduit {seen_us[u]}. A conduit is "
                     "named for its upstream manhole, so two of them cannot share one - and "
                     "in a forest (H15) they cannot exist", 1.0)
                continue
            t, s = node_town_code[i], node_sub[i]
            if not t or not s:
                flag("reach_us_unnamed", eid[k],
                     f"upstream chamber {u} exists but is itself unnamed (no town, no tier "
                     "the grammar admits, or its whole subnetwork has no letter), so there "
                     "is no manhole number for the conduit to take", 1.0)
                continue
            seen_us[u] = eid[k]
            rtown[k], rsub[k] = t, s
            rname[k] = concept_name(t, "conduit", subnet=s, seq=int(mh_seq[i]))
        rc["NAME"], rc["TOWN"], rc["SUBNET"] = rname, rtown, rsub
        counts["reaches_named"] = int((rname != "").sum())
        counts["unchanged"] += int(((had_r == rname) & (rname != "")).sum())
        counts["renamed"] += int(((had_r != "") & (rname != "") & (had_r != rname)).sum())
        counts["withdrawn"] += int(((had_r != "") & (rname == "")).sum())

    # ---- 7. the pumps, and the force mains that carry their number -------------------
    st = None
    rm = None
    pump_seq: Dict[str, int] = {}
    if stations is not None:
        st = stations.copy()
        _need(st, ["NODE_UID", "X", "Y"], "stations")
        suid = _str(st["NODE_UID"])
        _index_map(suid, "stations.NODE_UID")
        counts["stations_total"] = len(st)
        # a station's town: where it stands, else the first town downstream - which for a
        # station means the town of the chamber its rising main discharges into
        if node_town is not None or not towns.has_geometry:
            sloc = np.array([town_name[idx_of[u]] if u in idx_of else ""
                             for u in suid], dtype=object)
        else:
            sloc = towns.locate(st["X"].to_numpy(dtype=float),
                                st["Y"].to_numpy(dtype=float))
        # SORTED, never row order. A station with two rising mains discharging into two
        # different towns used to take its letter from whichever main happened to be listed
        # first, so reversing the rising-main rows renamed the station AND both its mains -
        # exactly the property rule (e) says this module does not have. The headline
        # stability test shuffles nodes and reaches and never touched this frame.
        ds_of_station: Dict[str, str] = {}
        rm_towns: Dict[str, List[str]] = {}
        if rising_mains is not None and "STATION" in rising_mains.columns \
                and "DS_NODE" in rising_mains.columns:
            pairs = sorted({(a, b) for a, b in zip(_str(rising_mains["STATION"]),
                                                   _str(rising_mains["DS_NODE"]))
                            if a and b})
            for a, b in pairs:
                ds_of_station.setdefault(a, b)
                i = idx_of.get(b, -1)
                if i >= 0 and town_name[i] and town_name[i] not in rm_towns.setdefault(a, []):
                    rm_towns[a].append(town_name[i])
        scode = np.full(len(st), "", dtype=object)
        for k in range(len(st)):
            t = sloc[k]
            if not t:
                d = ds_of_station.get(suid[k], "")
                i = idx_of.get(d, -1)
                if i >= 0:
                    t = town_name[i]
            if not t:
                i = idx_of.get(suid[k], -1)
                if i >= 0:
                    t = town_name[i]
            scode[k] = towns.code(t) if t else ""
        ordk = list(zip([int(v) for v in -_q(st["Y"].to_numpy(dtype=float))],
                        [int(v) for v in _q(st["X"].to_numpy(dtype=float))],
                        list(suid)))
        order = sorted(range(len(st)), key=lambda k: (str(scode[k]),) + ordk[k])
        had_s = _str(st["NAME"]) if "NAME" in st.columns else np.full(len(st), "", dtype=object)
        sname = np.full(len(st), "", dtype=object)
        cnt: Dict[str, int] = {}
        for k in order:
            t = str(scode[k])
            if not t:
                flag("station_no_town", suid[k],
                     "the station is outside every town and its rising main does not "
                     "discharge into one either, so rule (b) has no letter to give it",
                     1.0)
                continue
            cand = rm_towns.get(suid[k], [])
            if len(cand) > 1:
                flag("station_town_ambiguous", suid[k],
                     f"the station's rising mains discharge into {len(cand)} different "
                     f"towns ({sorted(cand)}), so rule (b) - the first town DOWNSTREAM - "
                     "has more than one answer. Naming took the lowest DS_NODE so the "
                     "answer cannot depend on row order, but which town owns the station "
                     "is the engineer's call, not a sort's", float(len(cand)))
            cnt[t] = cnt.get(t, 0) + 1
            sname[k] = concept_name(t, "pump", seq=cnt[t])
            pump_seq[suid[k]] = cnt[t]
        st["NAME"], st["TOWN"] = sname, scode
        st["SUBNET"] = ""     # a station is a SEAM between subnetworks, not a member of one
        counts["stations_named"] = int((sname != "").sum())
        counts["unchanged"] += int(((had_s == sname) & (sname != "")).sum())
        counts["renamed"] += int(((had_s != "") & (sname != "") & (had_s != sname)).sum())
        counts["withdrawn"] += int(((had_s != "") & (sname == "")).sum())
        # the width concept_name() ACTUALLY used, measured after numbering. The old value
        # came from a value_counts() that included the BLANK code, so a run with 120
        # unnamed stations published pump_pad=3 while every name written was two digits -
        # and it was never applied to anything, because concept_name() pads to PUMP_PAD_MIN.
        counts["pump_pad"] = _pad_width(max(cnt.values()) if cnt else 1, PUMP_PAD_MIN)

    if rising_mains is not None:
        rm = rising_mains.copy()
        _need(rm, ["EDGE_UID"], "rising_mains")
        _index_map(_str(rm["EDGE_UID"]), "rising_mains.EDGE_UID")
        counts["mains_total"] = len(rm)
        link = "STATION" if "STATION" in rm.columns else (
            "US_NODE" if "US_NODE" in rm.columns else "")
        if not link:
            raise NamingError(
                "rising_mains has neither STATION nor US_NODE, so a force main cannot find "
                "the pump whose number it shares. The engineer's rule is 'I-P02, numbered "
                "with its pump' - the link is the whole of it.")
        owner = _str(rm[link])
        mid = _str(rm["EDGE_UID"])
        st_town = ({} if st is None else
                   dict(zip(_str(st["NODE_UID"]), _str(st["TOWN"]))))
        had_m = _str(rm["NAME"]) if "NAME" in rm.columns else np.full(len(rm), "", dtype=object)
        mname = np.full(len(rm), "", dtype=object)
        mtown = np.full(len(rm), "", dtype=object)
        # sorted on EDGE_UID, so which of two mains keeps the number does not depend on
        # row order; and a SECOND main on one pump is FLAGGED, not given the same name.
        # "I-P02, numbered with its pump" has no token for a twin main, and two rows with
        # one name is what contract.validate() refuses at publication.
        seen_owner: Dict[str, str] = {}
        for k in np.argsort(mid, kind="stable"):
            k = int(k)
            o = owner[k]
            if o in pump_seq and st_town.get(o, ""):
                if o in seen_owner:
                    flag("rm_dup_station", mid[k],
                         f"pumping station {o} already has force main {seen_owner[o]}. A "
                         "force main is NUMBERED WITH ITS PUMP, so a second one on the same "
                         "station would carry the same name, and a name that identifies two "
                         "things identifies neither. Either the station has one main, or "
                         "twin mains need a grammar the engineer has not stated",
                         1.0)
                    continue
                seen_owner[o] = mid[k]
                mtown[k] = st_town[o]
                mname[k] = concept_name(st_town[o], "main", seq=int(pump_seq[o]))
            else:
                flag("rm_no_station", mid[k],
                     f"{link} is {o!r}, which is not a named pumping station - a force main "
                     "is numbered with its pump, so an unnamed pump leaves it unnamed",
                     1.0)
        rm["NAME"], rm["TOWN"] = mname, mtown
        rm["SUBNET"] = ""
        counts["mains_named"] = int((mname != "").sum())
        counts["unchanged"] += int(((had_m == mname) & (mname != "")).sum())
        counts["renamed"] += int(((had_m != "") & (mname != "") & (had_m != mname)).sum())
        counts["withdrawn"] += int(((had_m != "") & (mname == "")).sum())

    # ---- 8. the tables the engineer reads --------------------------------------------
    # TWO COLUMNS, BECAUSE THEY ARE TWO DIFFERENT FACTS and one name for both is how
    # SLOPE_PCT got itself banned. `TOWN` here is the town the CHAMBER resolves to (its own
    # polygon, or the first one downstream). `TOWN_NAMED` is the letter its NAME actually
    # carries, which is its SUBNETWORK's town - the plurality of the members - and the two
    # differ on every chamber of a subnetwork that straddles a boundary. `nodes.TOWN` on
    # the published layer is TOWN_NAMED, never this one.
    node_towns = pd.DataFrame({
        key: uid, "TOWN_NAME": town_name, "TOWN": town_code, "TOWN_SRC": town_src,
        "TOWN_NAMED": node_town_code,
        "SUBNET": node_sub, "MH_SEQ": mh_seq, "IS_MAIN": main.astype(int),
        "DEPTH_FROM_OUTFALL": depth,
    })
    subs_out = subs.drop(columns=["_ROOT", "_ORD", "_MAINFIRST", "_NY", "_NX"])
    subs_out = subs_out[["NAME", "TOWN", "SUBNET", "IS_MAIN", "N_NODES", "OUTFALL",
                         "X", "Y", "TOWN_SHARE", "TOWN_WHY"]]
    fl = pd.DataFrame(flags, columns=["KIND", "REF", "WHY", "SIZE"])
    counts["flags"] = int(len(fl))
    counts["subnet_pad"] = pad
    counts["main_mask_from"] = main_src

    return NamingResult(nodes=nd, reaches=rc, stations=st, rising_mains=rm,
                        subnets=subs_out, node_towns=node_towns, flags=fl,
                        counts=counts, towns=towns)


# ======================================================================================
# SELF-TEST - the guards proved to BITE, not merely asserted to exist
# ======================================================================================

def _demo() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, TownIndex]:
    """A tiny synthetic design: one main pipe through 'Ibri', two branches hanging off it,
    one branch reaching in from outside every town, and one pumping station.

        main:    T1 -> T2 -> T3            (trunk main, north to south)
        branch A: A3 -> A2 -> A1 -> T2     (A1 is the outfall onto the main pipe)
        branch B: B2 -> B1 -> T3
        outside : O1 -> B1                 (no town of its own - takes B's, downstream)
        station : P1 (its own terminal), rising main into T3
    """
    rows = [
        # uid,  x,      y,      ds,   tier
        ("T1", 100.0, 500.0, "T2", "trunk main"),
        ("T2", 100.0, 400.0, "T3", "trunk main"),
        ("T3", 100.0, 300.0, "",   "trunk main"),
        ("A1", 150.0, 400.0, "T2", "sub main"),
        ("A2", 200.0, 420.0, "A1", "lateral"),
        ("A3", 250.0, 440.0, "A2", "lateral"),
        ("B1",  60.0, 300.0, "T3", "sub main"),
        ("B2",  40.0, 320.0, "B1", "lateral"),
        ("O1", -500.0, 320.0, "B1", "lateral"),      # outside every town
        ("P1",  60.0, 260.0, "",   "sub main"),      # the station node
    ]
    nodes = pd.DataFrame(rows, columns=["NODE_UID", "X", "Y", "DS_NODE", "TIER"])
    reaches = pd.DataFrame(
        [(f"E{i:02d}", u, d) for i, (u, d) in enumerate(
            [(r[0], r[3]) for r in rows if r[3]], start=1)],
        columns=["EDGE_UID", "US_NODE", "DS_NODE"])
    stations = pd.DataFrame([dict(NODE_UID="P1", X=60.0, Y=260.0)])
    mains = pd.DataFrame([dict(EDGE_UID="RM1", STATION="P1", DS_NODE="T3")])
    # a gazetteer with no geometry: the towns are supplied per node instead
    towns = TownIndex.from_names(["Ibri", "Al Araqi", "Ad Dariz"], source="(demo)")
    return nodes, reaches, stations, mains, towns


def _demo_town_of(nodes: pd.DataFrame) -> List[str]:
    """Everything at x >= 0 is in Ibri; the O1 chamber at x = -500 is in no town."""
    return ["Ibri" if float(x) >= 0 else "" for x in nodes.X]


def _raises(fn, *must) -> None:
    try:
        fn()
    except Exception as e:                      # noqa: BLE001 - the message is the assertion
        msg = str(e)
        for m in must:
            assert m.lower() in msg.lower(), f"expected {m!r} in:\n{msg}"
        return
    raise AssertionError(f"expected a raise containing {must}")


def _self_test() -> None:
    nodes, reaches, stations, mains, towns = _demo()
    tn = _demo_town_of(nodes)

    # --- the town codes ------------------------------------------------------------
    assert towns.code("Ibri") == "I"
    assert towns.code("Al Araqi") == "A"        # no clash in this 3-town demo
    ct = towns.clash_table()
    assert set(ct.columns) >= {"NAME", "KEY", "CODE", "CLASHED_WITH"}
    assert ct.loc[ct.NAME == "Ad Dariz", "KEY"].iloc[0] == "dariz"   # the article is dropped

    # --- the ordering gate ---------------------------------------------------------
    blind = nodes.copy()
    blind["DS_NODE"] = ""
    _raises(lambda: name_network(blind, towns=towns, node_town=tn),
            "DOWNSTREAM", "Naming runs after")
    _raises(lambda: assert_ready(nodes.drop(columns=["DS_NODE"])), "missing", "DS_NODE")

    # --- the whole assignment ------------------------------------------------------
    res = name_network(nodes, reaches=reaches, stations=stations, rising_mains=mains,
                       towns=towns, node_town=tn)
    nm = dict(zip(res.nodes.NODE_UID, res.nodes.NAME))

    # the main pipe is its own subnetwork and sorts FIRST in its town
    assert nm["T1"].startswith("I-S01-TM-M"), nm["T1"]
    assert nm["T3"] == "I-S01-TM-M001", nm["T3"]        # M001 is the outfall
    assert nm["T1"] == "I-S01-TM-M003"                  # numbering walks upstream
    # the branches are separate subnetworks - a branch STOPS at the main pipe (rule 2)
    assert res.nodes.set_index("NODE_UID").SUBNET["A1"] != \
           res.nodes.set_index("NODE_UID").SUBNET["T2"]
    assert nm["A1"].endswith("-SM-M001") and nm["A3"].endswith("-M003")
    # rule (b): O1 is in no town and takes the letter of the first town DOWNSTREAM
    assert nm["O1"].startswith("I-"), nm["O1"]
    assert res.node_towns.set_index("NODE_UID").TOWN_SRC["O1"] == "downstream"
    assert res.counts["town_downstream"] >= 1
    # a conduit is named for its UPSTREAM manhole
    rr = res.reaches.set_index("EDGE_UID")
    for _, r in res.reaches.iterrows():
        if not r.NAME:
            continue
        us = nm[r.US_NODE]
        assert r.NAME == us.replace("-TM-M", "-C").replace("-SM-M", "-C") \
                           .replace("-L-M", "-C").replace("-M-M", "-C"), (r.NAME, us)
    # a pump is not inside a subnetwork, and its force main carries its number
    assert res.stations.NAME.iloc[0] == "I-PMP01"
    assert res.stations.SUBNET.iloc[0] == ""
    assert res.rising_mains.NAME.iloc[0] == "I-P01"
    # every name parses, and the parts agree with the columns
    for df in (res.nodes, res.reaches, res.stations, res.rising_mains):
        for v, t, s in zip(df.NAME, df.TOWN, df.SUBNET):
            if not v:
                continue
            p = parse_name(v)
            assert p is not None, v
            assert p["town"] == t and p["sub"] == (s or "")
    assert res.nodes.NAME.nunique() == int((res.nodes.NAME != "").sum())

    # --- STABILITY: the same design, built in a different order, gets the same names --
    perm = [7, 2, 9, 0, 5, 3, 8, 1, 6, 4]
    n2 = nodes.iloc[perm].reset_index(drop=True)
    t2 = [tn[i] for i in perm]
    r2 = reaches.iloc[::-1].reset_index(drop=True)
    res2 = name_network(n2, reaches=r2, stations=stations, rising_mains=mains,
                        towns=towns, node_town=t2)
    assert res.name_map() == res2.name_map(), "NAMES MOVED WHEN THE ROWS MOVED"

    # --- flags rather than inventions ------------------------------------------------
    lost = nodes.copy()
    lost.loc[lost.NODE_UID == "O1", "DS_NODE"] = ""      # now nothing downstream either
    r3 = name_network(lost, towns=towns, node_town=tn)
    assert (r3.flags.KIND == "node_no_town").any()
    assert r3.nodes.set_index("NODE_UID").NAME["O1"] == ""
    bad = nodes.copy()
    bad.loc[bad.NODE_UID == "A2", "TIER"] = "boulevard"
    r4 = name_network(bad, towns=towns, node_town=tn)
    assert (r4.flags.KIND == "node_no_tier").any()
    assert r4.nodes.set_index("NODE_UID").NAME["A2"] == ""

    # a tier the grammar cannot express is FLAGGED, not written as an unparseable name.
    # contract.TIER_TOKEN has five tiers; contract.NAME_RE admits three.
    assert GRAMMAR_TIERS == {"lateral", "sub main", "trunk main"}, sorted(GRAMMAR_TIERS)
    assert parse_name(concept_name("I", "manhole", subnet="S01", tier="main", seq=3)) is None
    mid = nodes.copy()
    mid.loc[mid.NODE_UID == "A2", "TIER"] = "main"
    r5 = name_network(mid, towns=towns, node_town=tn)
    assert (r5.flags.KIND == "node_tier_ungrammatical").any()
    assert r5.nodes.set_index("NODE_UID").NAME["A2"] == ""

    # --- a cycle is named, not hung on -----------------------------------------------
    loop = nodes.copy()
    loop.loc[loop.NODE_UID == "T3", "DS_NODE"] = "T1"
    _raises(lambda: name_network(loop, towns=towns, node_town=tn), "CYCLE", "forest")

    # --- ADD and TAKE AWAY (inheritance row 4) ---------------------------------------
    cleared, removed = clear_names(res.nodes)
    assert removed == int((res.nodes.NAME != "").sum()) and (cleared.NAME == "").all()
    again = name_network(res.nodes, towns=towns, node_town=tn)      # already named
    assert again.counts["renamed"] == 0 and again.counts["withdrawn"] == 0
    assert again.counts["unchanged"] == int((res.nodes.NAME != "").sum())
    gone = name_network(bad, towns=towns, node_town=tn)             # A2 loses its name
    named_before = res.nodes.set_index("NODE_UID").NAME
    bad2 = bad.copy()
    bad2["NAME"] = [named_before[u] for u in bad2.NODE_UID]
    gone = name_network(bad2, towns=towns, node_town=tn)
    assert gone.counts["withdrawn"] >= 1, gone.counts

    # --- the frozen mapping ----------------------------------------------------------
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        p = write_town_prefixes(towns, os.path.join(d, "prefixes.csv"))
        back = load_town_prefixes(p)
        assert back == towns.codes
        with open(os.path.splitext(p)[0] + ".json", encoding="utf-8") as fh:
            man = json.load(fh)
        man["codes"]["Ibri"] = "Z"
        with open(os.path.splitext(p)[0] + ".json", "w", encoding="utf-8") as fh:
            json.dump(man, fh)
        _raises(lambda: load_town_prefixes(p), "sha256", "hand-editing")

    # --- nothing was mutated under the caller ---------------------------------------
    assert "NAME" not in nodes.columns and "NAME" not in reaches.columns

    print("naming self-test OK")


# ======================================================================================
# CLI
# ======================================================================================

def _print_towns(idx: TownIndex) -> None:
    t = idx.clash_table()
    w = max(len(x) for x in t.NAME)
    print(f"{len(t)} towns from {idx.source} field {idx.name_field!r}")
    print(f"  {'NAME'.ljust(w)}  CODE  would-be  clashed with")
    for _, r in t.iterrows():
        print(f"  {r.NAME.ljust(w)}  {r.CODE:<5} {r.FIRST:<9} {r.CLASHED_WITH}")
    print(f"\n  {int((t.LETTERS == 1).sum())} keep a single letter, "
          f"{int((t.N_CLASH > 0).sum())} collided and BOTH sides extended "
          f"(the town with more served plots is not favoured)")
    print(f"  sha256 {_mapping_digest(idx.codes)[:16]}...")


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="W12 naming scheme")
    ap.add_argument("--towns", default=None, help="path to the towns layer")
    ap.add_argument("--field", default=TOWN_NAME_FIELD)
    ap.add_argument("--freeze", nargs="?", const="", default=None, metavar="CSV",
                    help="write the town-prefix mapping (default W12/run/)")
    ap.add_argument("--check-frozen", action="store_true",
                    help="report drift against the frozen mapping")
    ap.add_argument("--no-self-test", action="store_true")
    a = ap.parse_args(argv)

    try:
        idx = TownIndex.load(a.towns, field_name=a.field)
        _print_towns(idx)
        if a.freeze is not None:
            p = write_town_prefixes(idx, a.freeze or None)
            print(f"\n  wrote {p}\n  wrote {os.path.splitext(p)[0]}.json")
        if a.check_frozen:
            d = idx.check_frozen()
            print("\n  frozen mapping: no drift" if not len(d) else
                  "\n  DRIFT against the frozen mapping:\n" + d.to_string(index=False))
    except NamingError as e:
        print(f"[towns] {e}")

    print("\nASSUMPTIONS (naming has no hydraulics - not one design number is in this file)")
    for k, (v, why) in ASSUMPTIONS.items():
        print(f"  {k} = {v!r}\n      {why}")

    if not a.no_self_test:
        print()
        _self_test()
    return 0


if __name__ == "__main__":
    sys.exit(main())
