"""W11a stage 8 - PHASING AND PACKAGES. Cuts the network into buildable, commissionable units.

THE ENGINEERING QUESTION THIS STAGE ANSWERS. A design that is compliant, buildable and
operable can still be un-fundable, because nobody builds 1,883 km at once. Objective 4 of
the philosophy - "it can be built in stages, every package commissionable on its own" -
outranks cost and outranks hydraulic minimality. This stage decides where the scheme is
cut, in what order the pieces go in, and which of them can be switched on without waiting
for the piece below.

WHAT A PACKAGE IS, MEASURED - NOT CHOSEN. NAMA built this town's existing sewer in five
packages, 5A-1 to 5A-5, and they are the only real evidence available of what a
contractor here actually delivers as one unit. Measured off `W10/shp/W10_existing_built.shp`
(3,266 pipes, 101.1 km, 2006) in `W10/docs/research/DELIVERABLE_SPEC.md` part C:

    size            3.5 - 40 km of sewer, median 20.0 km          C.1
    plots           180 - 2,180 plots in 0.3 - 8.7 km2            C.1
    topology        EVERY ONE is a single connected tree with     C.3
                    EXACTLY ONE outlet - not one is a map slice
    territory       under ~15 % of a package's pipes lie within   C.2
                    60 m of another package's; median separation
                    237 - 3,935 m. Packages are territories
    order           5A-3 -> 5A-2 -> 5A-4 -> 5A-1 -> station ->    C.4
                    force main -> STP, and 5A-5 -> STP direct.
                    The chain FORCES the order: downstream first

None of those numbers is a guideline value and this file never pretends otherwise - they
are tagged `measured` in BAND below, against `criteria`/`guideline` for anything cited to a
page. The one guideline obligation is G201-pp19-22 Table 2, which requires **Project
Phasing** at the concept phase (and Construction Phasing only at preliminary - out of
scope here, DELIVERABLE_SPEC D.7).

THE LESSON THAT INVERTS W10's THINKING. 5A-1 terminates at a pumping station rather than
at a gravity trunk, and that station plus the single built force main is what let 60.8 km
and roughly 5,963 properties be commissioned WITHOUT first building 7 km of deep gravity
trunk to the works. So a lifting station is a COMMISSIONING DEVICE, not only a depth
device (philosophy sec 6, build brief P8). W10 treated stations purely as a cost to
minimise. Here every station is a MANDATORY package seam: the tree is cut there whether or
not the size band asks for it, because a seam that carries its own outlet is the only
thing that buys a package independence from the trench below it.

THE W10 FAILURE THIS PREVENTS. W10 published 206 "subnetworks" - median 1.16 km, 99 of 214
under 1 km, the largest 265.8 km with 6,327 plots (DELIVERABLE_SPEC C.5 item 3). They were
not packages; they were an artefact of where the corridor network happened to touch the
trunk, with no size band and no guarantee of a single outlet. This stage cuts on the tree
itself - a package is the set of everything draining through one chosen node, cut AT that
node - so one outlet and one connected tree are true by construction, and the size band is
enforced while cutting rather than discovered afterwards.

TWO FIELDS, DELIBERATELY NOT ONE. `PACKAGE` is a buildable unit inside a phase; `PHASE` is
when it is needed. NAMA's 101 km is one PHASE of a network whose ultimate is far larger,
and collapsing the two loses the distinction (DELIVERABLE_SPEC C.5 item 4). Commissioning
ORDER is a third thing again - it is forced by the dependency chain, is published as
`COMM_SEQ`, and is not the phase either.

    PHASE 1  the package serves plots that already carry structures, so its demand exists
             at the "start" model year (scope p14). CLASS B / U / A in the plot loads:
             B = structures on the plot, U = an unparcelled building the cadastre never
             drew, A = a farm plot whose load comes only from counted electricity accounts.
    PHASE 0  no developed plot at all - it serves platted desert. The contract defines 0 as
             "not yet assigned", and that is the honest answer: the YEAR such a package is
             needed cannot be set without the development percentages G201-p59 requires
             ("development speed must be considered through appropriate phasing
             assumptions ... development percentages must be applied over the design
             period"), and those have not been supplied. Guessing a build-out curve here
             would be exactly the invented metric the project rules prohibit. Pass
             `horizon_targets` when the curve arrives and phases 2/2030, 3/2055, 4/ultimate
             fall out of the same ordering with no code change.

WHAT THIS STAGE DOES NOT DECIDE. Whether the packages become separate tenders. TD-p149
programmes networks, lifting stations, pumping stations and house connections as ONE
tender, so "package" here means a separately-commissionable SECTION inside one contract,
and saying otherwise would imply ~90 procurements that nobody has asked for
(DELIVERABLE_SPEC C.5 item 1). Nor does it decide the temporary arrangement for an
upstream package waiting on its downstream neighbour - tankering, an interim tie into the
2006 network, or sequencing so it never arises. Nobody specifies that; it goes to NWS as a
decision (C.5 item 7).

INPUTS - all from the audited GeoPackage this iteration publishes to, never from W10/W8:
    nodes         the vertex set, with NODE_KIND (station / outfall / tie mark the seams)
    reaches       US_NODE / DS_NODE / LEN_M - the tree itself
    connections   one row per load unit, for the plot count the band is measured in
    stations      optional; absent means no forced seams, and the run says so
    rising_mains  optional; needed to resolve what a station package discharges INTO
Read-only, for the phase split: `W10/shp/W10_plot_loads.gpkg` CLASS, joined on PLOT_ID.

RUN
    python s8_packages.py              partition and publish, or say what it is waiting for
    python s8_packages.py --selftest   invariants, on a synthetic tree - writes only to a
                                       temp directory, never to W11a, W10 or W8
    python s8_packages.py --calibrate  run the partitioner on NAMA's own built network and
                                       compare with NAMA's own 5A-1..5A-5

Stage order is 8 here and 6 in the build brief's table; the brief numbers the seven design
stages, the files number the ten modules. Same stage.
"""

from __future__ import annotations

import os
import sys
import warnings
from collections import defaultdict
from typing import Dict, List, Optional, Sequence, Tuple

warnings.filterwarnings("ignore")

HERE = os.path.dirname(os.path.abspath(__file__))          # .../W11a/py
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import numpy as np                                          # noqa: E402
import pandas as pd                                         # noqa: E402
import geopandas as gpd                                     # noqa: E402
from shapely.geometry import MultiLineString                # noqa: E402
from shapely.ops import unary_union                         # noqa: E402

from w11a import contract as K                              # noqa: E402

W11A = K.W11A_ROOT                                          # .../W11a
REPO = K.REPO_ROOT                                          # .../Hydraulic/Claude
GPKG = K.gpkg_path(W11A)                                    # .../W11a/shp/W11a.gpkg
RUN = os.path.join(W11A, "run")

STAGE = "s8_packages"
ORDER = 8


# --------------------------------------------------------------------------------------
# The band. Every value carries what KIND of number it is, because three kinds are mixed
# here and only one of them is a guideline. A "measured" value is an observation of what
# NAMA delivered on this town; it binds our design because objective 3 says the network
# must read like their own, but it is not a "shall" and it is never quoted as one.
# --------------------------------------------------------------------------------------

BAND: Dict[str, Tuple[float, str, str]] = {
    # key                value  kind        source
    "PKG_LEN_MIN_KM":   (3.5,  "measured", "DELIVERABLE_SPEC C.1 - 5A-3, the smallest "
                                           "package NAMA built (3.45 km, 180 plots)"),
    "PKG_LEN_TARGET_KM": (20.0, "measured", "DELIVERABLE_SPEC C.1 - the median built "
                                            "package (5A-2 at 20.01 km). The value the "
                                            "partitioner cuts AT"),
    "PKG_LEN_MAX_KM":   (40.0, "measured", "DELIVERABLE_SPEC C.1 - 5A-5, the largest "
                                           "built package (40.35 km). Rounded DOWN to 40 "
                                           "as the cap, so NAMA's own largest sits a "
                                           "fraction above our ceiling rather than below "
                                           "it - the cap is ours, not theirs"),
    "PKG_PLOTS_MIN":    (180,  "measured", "DELIVERABLE_SPEC C.1 - 5A-3"),
    "PKG_PLOTS_MAX":    (2180, "measured", "DELIVERABLE_SPEC C.1 - 5A-5 (2,172, rounded)"),
    "SEAM_DIST_M":      (60.0, "measured", "DELIVERABLE_SPEC C.2 - the distance at which "
                                           "a pipe counts as sitting on another package's "
                                           "territory. Same 60 m used for plot frontage "
                                           "in the W10 scope work, so the two are "
                                           "comparable"),
    "SEAM_MAX_PCT":     (15.0, "measured", "DELIVERABLE_SPEC D.6 test F8, from C.2 - "
                                           "NAMA's own worst package is 13.1 %"),
}

PKG_LEN_MIN_M = BAND["PKG_LEN_MIN_KM"][0] * 1000.0
PKG_LEN_TARGET_M = BAND["PKG_LEN_TARGET_KM"][0] * 1000.0
PKG_LEN_MAX_M = BAND["PKG_LEN_MAX_KM"][0] * 1000.0
SEAM_DIST_M = BAND["SEAM_DIST_M"][0]
SEAM_MAX_PCT = BAND["SEAM_MAX_PCT"][0]

# A node kind that terminates gravity flow. Each one gives the package above it its own
# outlet, so the package can be commissioned without the trench below it existing - the
# 5A-1 pattern (philosophy sec 6, DELIVERABLE_SPEC C.4). `tie` counts because a tie-in to
# the 2006 network is a real, already-built discharge point.
SEAM_KINDS = ("station", "outfall", "tie")

# Plot classes that carry structures TODAY, from W10/py/p1_loads.py: B = the cadastre
# marks structures on it, U = an unparcelled building the cadastre never drew, A = a farm
# plot, which is given load ONLY where an electricity account was counted on it (the
# farming carries no load, the houses on it do - project rule, 2026-08-18). P = platted
# and open, i.e. future development.
DEV_CLASSES = ("B", "U", "A")

PLOT_LOADS = os.path.join(REPO, "W10", "shp", "W10_plot_loads.gpkg")
PLOT_LOADS_LAYER = "plot_loads"
EXISTING_BUILT = os.path.join(REPO, "W10", "shp", "W10_existing_built.shp")


# --------------------------------------------------------------------------------------
# Published numbers. P2: one function per published quantity, so a package count cannot be
# recomputed ad hoc at the point of reporting the way the lifting-station count was seven
# different times (19, 21, 25, 37, 140, 184, 239).
# --------------------------------------------------------------------------------------

@K.published("package_count", "-", "s8_packages")
def package_count(pkgs: pd.DataFrame) -> int:
    return int(len(pkgs))


@K.published("package_network_km", "km", "s8_packages")
def package_network_km(pkgs: pd.DataFrame) -> float:
    """Total gravity length carried in packages. Every reach belongs to exactly one, so
    this must equal the network length - a discrepancy means reaches fell out of the
    partition, which is the silent drop invariant 1 exists to make impossible."""
    return float(pd.to_numeric(pkgs["LEN_KM"], errors="coerce").sum())


@K.published("independent_package_count", "-", "s8_packages")
def independent_package_count(pkgs: pd.DataFrame) -> int:
    """Packages commissionable WITHOUT their downstream neighbour - they end at a station,
    at the works, or at the existing network. This is the property a station buys (P8),
    and it is the honest measure of how phaseable the scheme actually is."""
    return int(pd.to_numeric(pkgs["INDEP"], errors="coerce").fillna(0).sum())


# --------------------------------------------------------------------------------------
# The tree
# --------------------------------------------------------------------------------------

class Tree:
    """The gravity forest, read from the PUBLISHED reach layer and nothing else.

    Built from US_NODE / DS_NODE, never from geometry. That is the whole point of P3: W10's
    connectivity existed only inside `p2_sizing.py`, so the published layer had to be
    re-derived by a tolerance and came out in 7,919 pieces. Here the identifiers ARE the
    topology, and a reach whose US_NODE is not a node raises rather than being dropped.

    An edge belongs to the package of its UPSTREAM node. That is NAMA's own convention,
    read off their data: 5A-2's outlet record is `5A-2-TM-MH6032 -> 5A-4-TM-MH6033`, i.e.
    the pipe leaving the package is filed under the package it leaves, not the one it
    enters. Getting this backwards would put every seam pipe in the wrong contract.
    """

    def __init__(self, reaches: pd.DataFrame, node_ids: Sequence[str]):
        self.children: Dict[str, List[str]] = defaultdict(list)
        self.out_edge: Dict[str, str] = {}
        self.edge_len: Dict[str, float] = {}
        self.edge_ds: Dict[str, str] = {}
        self.nodes: List[str] = [str(n) for n in node_ids]
        known = set(self.nodes)

        for r in reaches.itertuples():
            u, d = str(r.US_NODE), str(r.DS_NODE)
            if u not in known or d not in known:
                raise K.ContractError(
                    f"reach {r.EDGE_UID} joins {u} -> {d}, and one of them is not in the "
                    "node layer. The partition is computed on identifiers; an unresolvable "
                    "one is a reach that would silently vanish from every package.")
            if u in self.out_edge:
                raise K.ContractError(
                    f"node {u} has two outgoing reaches ({self.out_edge[u]}, "
                    f"{r.EDGE_UID}). H15: the network is a forest, and a node with two "
                    "parents makes 'everything draining through one node' meaningless - "
                    "there would be no single subtree to cut.")
            self.out_edge[u] = str(r.EDGE_UID)
            self.edge_len[str(r.EDGE_UID)] = float(r.LEN_M)
            self.edge_ds[str(r.EDGE_UID)] = d
            self.children[d].append(u)

    def parent(self, v: str) -> Optional[str]:
        e = self.out_edge.get(v)
        return self.edge_ds[e] if e else None

    def own_len(self, v: str) -> float:
        """Length filed under v - the reach LEAVING it. A terminal node contributes none."""
        e = self.out_edge.get(v)
        return self.edge_len[e] if e else 0.0

    def postorder(self) -> List[str]:
        """Children before parents, iteratively. Recursion is not an option: a lateral run
        chained into a sub main into a trunk is thousands of nodes deep and Python's stack
        is 1,000 frames."""
        pending = {v: 0 for v in self.nodes}
        for d, kids in self.children.items():
            pending[d] = len(kids)
        stack = [v for v in self.nodes if pending[v] == 0]
        order: List[str] = []
        while stack:
            v = stack.pop()
            order.append(v)
            p = self.parent(v)
            if p is not None:
                pending[p] -= 1
                if pending[p] == 0:
                    stack.append(p)
        if len(order) != len(self.nodes):
            stuck = [v for v in self.nodes if pending[v] > 0][:5]
            raise K.ContractError(
                f"{len(self.nodes) - len(order):,} nodes never became reachable in a "
                f"post-order walk, e.g. {stuck}. In a forest that is impossible, so the "
                "reach layer contains a cycle - H15 breached upstream of this stage.")
        return order


# --------------------------------------------------------------------------------------
# The partition
# --------------------------------------------------------------------------------------

def partition(tree: Tree, seams: Sequence[str], *,
              target_m: float = PKG_LEN_TARGET_M,
              max_m: float = PKG_LEN_MAX_M,
              min_m: float = PKG_LEN_MIN_M) -> Tuple[Dict[str, str], List[str], List[str]]:
    """Cut the forest into packages. Returns (node -> package root, roots, notes).

    Bottom-up and greedy, in one post-order sweep, because the constraint that actually
    binds is a subtree property: a package must be everything draining through its outlet,
    so the only free choice is WHERE to cut, and the cheapest place to decide that is the
    moment the accumulated subtree first fills the band.

        1. accumulate the residual length up the tree
        2. the MAX guard, at a junction: if the branches meeting here would together
           overflow the ceiling, cut the largest of them off as its own package until the
           remainder fits. Largest first, because every uncut branch is already under the
           target, so the largest is the one most certain to clear the floor on its own
        3. cut here if this is a forced seam - a station, an outfall, a tie. A seam is cut
           whatever the size, because independence is worth more than tidiness (P8)
        4. otherwise cut here if the residual has reached the target

    Step 2 before step 4 matters. Deciding the seam first and then discovering the package
    is 60 km wide leaves no move except re-cutting from the top, which is how a partition
    ends up with W10's 265.8 km "subnetwork".

    What this deliberately does NOT do is draw a boundary on a map and take what falls
    inside it. That produces packages with several outlets, which is the one thing not a
    single one of NAMA's five is (DELIVERABLE_SPEC C.3).
    """
    notes: List[str] = []
    seam_set = set(seams)
    res: Dict[str, float] = {}
    cut: set = set()

    for v in tree.postorder():
        kids = [(res[c], c) for c in tree.children.get(v, ()) if c not in cut]
        total = tree.own_len(v) + sum(L for L, _ in kids)
        kids.sort(reverse=True)
        i = 0
        while total > max_m and i < len(kids):
            L, c = kids[i]
            cut.add(c)
            total -= L
            i += 1
        if i:
            notes.append(f"{v}: cut {i} branch(es) at the {max_m/1000:.0f} km ceiling")
        res[v] = total
        if v in seam_set or tree.parent(v) is None or total >= target_m:
            cut.add(v)

    pkg_of = _assign(tree, cut)
    roots = sorted(cut, key=lambda r: -_pkg_len(tree, pkg_of, r))
    roots, pkg_of, merge_notes = _merge_small(tree, pkg_of, roots, seam_set,
                                              min_m=min_m, max_m=max_m)
    return pkg_of, roots, notes + merge_notes


def _assign(tree: Tree, cut: set) -> Dict[str, str]:
    """Every node belongs to its nearest downstream cut node, itself included.

    Walking UPSTREAM from each root and stopping at the next root is O(N) and needs no
    tie-breaking: in a forest each node has exactly one downstream path, so it meets
    exactly one root first. Walking downstream per node would be O(N x depth) and would
    re-walk the trunk for every lateral on it.
    """
    pkg_of: Dict[str, str] = {}
    for r in cut:
        stack = [r]
        pkg_of[r] = r
        while stack:
            v = stack.pop()
            for c in tree.children.get(v, ()):
                if c in cut:
                    continue
                pkg_of[c] = r
                stack.append(c)
    missing = [v for v in tree.nodes if v not in pkg_of]
    if missing:
        raise K.ContractError(
            f"{len(missing):,} nodes reached no package root, e.g. {missing[:5]}. Every "
            "terminal is cut, so every downstream walk must end at a root - this means the "
            "reach layer is not the forest the contract guarantees.")
    return pkg_of


def _pkg_len(tree: Tree, pkg_of: Dict[str, str], root: str) -> float:
    return sum(tree.own_len(v) for v, r in pkg_of.items() if r == root)


def _merge_small(tree: Tree, pkg_of: Dict[str, str], roots: List[str], seam_set: set, *,
                 min_m: float, max_m: float) -> Tuple[List[str], Dict[str, str], List[str]]:
    """Absorb anything under the floor into the package it discharges into.

    Philosophy sec 4 prunes fingers on cost grounds; the same argument applies to a 400 m
    "package" - it carries a contract, a commissioning test and a set of drawings for
    nothing. Merging an upstream package into its downstream one keeps a connected subtree
    with a single outlet, so nothing about the package invariant is put at risk.

    Two cases are left alone deliberately, and reported rather than forced:
      - a package rooted on a FORCED SEAM - a station, an outfall, a tie. A station's
        outlet is a wet well, not a chamber; it discharges through a rising main into a
        different physical system, and merging it downstream would mean a gravity package
        spanning a pump. A short seam package is a real thing (a small pocket the ground
        made unavoidable), not an artefact, and independence is worth more than a tidy
        length band (P8, objective 4 over objective 5).
      - a merge that would push the receiving package over the ceiling. Two band failures
        are worse than one, and the honest answer is a package outside the band with a
        reason attached.
    """
    notes: List[str] = []
    changed = True
    while changed:
        changed = False
        lengths = {r: _pkg_len(tree, pkg_of, r) for r in roots}
        for r in sorted(roots, key=lambda x: lengths[x]):
            if lengths[r] >= min_m:
                break                                   # ascending, so the rest are fine
            if tree.parent(r) is None:
                # A TERMINAL tail under the floor - the outlet chamber, the works, or a
                # station, with only a stub of pipe above it. It has nowhere downstream to
                # go, so the merge runs the other way: absorb the upstream package into
                # THIS one. The union is still one connected tree, and its single outlet is
                # still this terminal, so the seam is preserved rather than destroyed. This
                # is NAMA's 5A-1 exactly - the whole 32 km catchment is filed under the
                # package that ends at the pumping station, not split off from it.
                # A forced seam is never absorbed, in EITHER direction. The guard further
                # down protects a seam package that would merge DOWNSTREAM; without the
                # same guard here a 1.9 km terminal stub swallows the 19 km station
                # package above it and the union spans a pump - the one thing the
                # downstream branch refuses by name. Independence outranks the length band
                # both ways (P8, objective 4 over objective 5).
                above = [u for u in roots if u != r and tree.parent(u) is not None
                         and pkg_of.get(tree.parent(u)) == r]
                ups = [u for u in above if u not in seam_set]
                fit = [u for u in ups if lengths[u] + lengths[r] <= max_m]
                if not fit:
                    held = [u for u in above if u in seam_set]
                    why = (f"{len(held)} upstream package(s) are rooted on a forced seam "
                           "and are never absorbed (P8)" if held else
                           "no upstream package fits under the "
                           f"{max_m/1000:.0f} km ceiling")
                    notes.append(f"{r}: terminal package of {lengths[r]/1000:.2f} km is "
                                 f"under the {min_m/1000:.1f} km floor and {why}")
                    continue
                u = max(fit, key=lambda x: lengths[x])
                for v, p in list(pkg_of.items()):
                    if p == u:
                        pkg_of[v] = r
                roots = [x for x in roots if x != u]
                notes.append(f"{u}: {lengths[u]/1000:.2f} km absorbed INTO the terminal "
                             f"package {r} ({lengths[r]/1000:.2f} km) - a package is not "
                             "cut off from its own outlet")
                changed = True
                break
            if r in seam_set:
                notes.append(f"{r}: {lengths[r]/1000:.2f} km is under the "
                             f"{min_m/1000:.1f} km floor but its outlet is a forced seam - "
                             "kept, because independence outranks the length band (P8)")
                continue
            ds_root = pkg_of.get(tree.parent(r))
            if ds_root is None or ds_root == r:
                continue
            if lengths[r] + lengths[ds_root] > max_m:
                notes.append(f"{r}: {lengths[r]/1000:.2f} km is under the "
                             f"{min_m/1000:.1f} km floor but merging it downstream would "
                             f"breach the ceiling - left as an under-band package")
                continue
            for v, p in list(pkg_of.items()):
                if p == r:
                    pkg_of[v] = ds_root
            roots = [x for x in roots if x != r]
            notes.append(f"{r}: {lengths[r]/1000:.2f} km absorbed into {ds_root}")
            changed = True
            break
    return roots, pkg_of, list(dict.fromkeys(notes))


# --------------------------------------------------------------------------------------
# Dependency, order, independence
# --------------------------------------------------------------------------------------

def dependencies(tree: Tree, pkg_of: Dict[str, str], roots: Sequence[str],
                 node_kind: Dict[str, str],
                 rm_ds: Optional[Dict[str, str]] = None) -> pd.DataFrame:
    """Which package each one discharges into, whether it needs it, and the build order.

    INDEP is the whole point of the exercise. A package that ends at the works, at a tie
    into the 2006 network, or at a station whose rising main discharges OUTSIDE this design
    has its own outlet and can be switched on while the trench below it is still a drawing.
    Everything else is inert until its downstream neighbour exists - measured, not assumed:
    5A-3 is 3.5 km serving 303 properties and it does nothing at all until 5A-2 is built
    (DELIVERABLE_SPEC C.4). A station whose rising main lands in a package of ours is in
    that second group, not the first: the pump buys independence from the TRENCH below, not
    from the discharge chamber it needs at the far end.

    COMM_SEQ is therefore computed on the dependency graph with the INDEP edges REMOVED.
    That is the 5A-1 lesson expressed as arithmetic: a station upstream of a long gravity
    trunk collapses the whole chain above it from "wait for the trunk" to "wait for
    nothing", and if the sequence still counted that edge the number would tell the client
    to wait for work that buys them nothing.

    `rm_ds` maps a station node to the chamber its rising main discharges at, so a station
    package still records WHERE it goes even though it does not depend on it.
    """
    rm_ds = rm_ds or {}
    rows = []
    for r in roots:
        kind = node_kind.get(r, "chamber")
        gravity_ds = tree.parent(r)
        # A station is independent only where its rising main lands somewhere that ALREADY
        # exists. 5A-1 was commissionable because its force main ends at the STP, not
        # because it ends at a pump (DELIVERABLE_SPEC C.4). Where the rising main
        # discharges into a chamber inside THIS design, that package is a real dependency:
        # nothing can be switched on into a discharge chamber nobody has built. Asserting
        # independence from the node kind alone overstates `independent_package_count` and
        # hands the client COMM_SEQ = 1 for work that cannot be commissioned first.
        rm_pkg = pkg_of.get(str(rm_ds[r])) if r in rm_ds else None
        if rm_pkg == r:
            rm_pkg = None            # discharges into its own package: not a dependency
        indep = kind in SEAM_KINDS and gravity_ds is None and rm_pkg is None
        if gravity_ds is not None:
            ds_pkg = pkg_of[gravity_ds]
        elif rm_pkg is not None:
            ds_pkg = rm_pkg                              # via its own rising main
        else:
            ds_pkg = ""                                  # the works, or an existing outfall
        # Terminal in the reach layer but not a recognised outlet: the flow leaves the
        # design and nothing says where. The contract's own node cross-field check blocks
        # this upstream ("no DS_NODE but not an outfall, a station or a tie"), so it can
        # only appear on foreign data - it does appear on NAMA's, where the pipe joining
        # 5A-4 to 5A-1 is simply not in the dataset (DELIVERABLE_SPEC C.3). Shouted, never
        # silently rendered as an independent package, which is what it would look like.
        dangling = gravity_ds is None and not indep and not ds_pkg
        if dangling:
            print(f"  WARNING: package outlet {r} is terminal but its NODE_KIND is "
                  f"{kind!r} - it is neither an outfall, a station nor a tie, so this "
                  "package discharges to nowhere the design records")
        rows.append(dict(root=r, kind=kind, ds_root=ds_pkg, indep=int(indep),
                         dangling=int(dangling)))
    dep = pd.DataFrame(rows).set_index("root")

    # Longest-path depth over the dependency edges that actually bind. Iterative rather
    # than recursive, and it detects a cycle by refusing to converge - a forest cannot
    # produce one, so a failure here means the tree was not a forest.
    seq = {r: 1 for r in roots}
    for _ in range(len(roots) + 1):
        moved = False
        for r in roots:
            if dep.at[r, "indep"]:
                continue
            d = dep.at[r, "ds_root"]
            if d and seq[r] <= seq[d]:
                seq[r] = seq[d] + 1
                moved = True
        if not moved:
            break
    else:
        raise K.ContractError(
            "the package dependency graph did not settle - it contains a cycle, so no "
            "commissioning order exists (DELIVERABLE_SPEC D.6 test F7). Two sources are "
            "possible: a cycle in the reaches, which H15 forbids, or a cascade of stations "
            "whose rising mains discharge into each other's packages, which is a layout "
            "nobody can commission in any order and is stage 7's to resolve.")
    dep["comm_seq"] = pd.Series(seq)
    return dep


# --------------------------------------------------------------------------------------
# The territorial test (DELIVERABLE_SPEC C.2 / D.6 F8)
# --------------------------------------------------------------------------------------

def seam_share(reaches: gpd.GeoDataFrame, pkg_col: str = "PACKAGE") -> pd.Series:
    """Share of each package's reaches lying within 60 m of a different package's.

    This is the test that separates a territory from a slice. NAMA's packages score 0 to
    13.1 %; a partition that interleaves scores far higher, and interleaving is what makes
    two contractors work the same street. Every reach is tested, not a sample - T02 sec 16,
    and the no-exemption rule in memory: a skipped row reads as a pass.
    """
    if reaches.empty:
        return pd.Series(dtype=float)
    geoms = reaches.geometry.values
    pkg = reaches[pkg_col].astype(str).values
    tree_idx = reaches.sindex
    buf = gpd.GeoSeries(geoms, crs=reaches.crs).buffer(SEAM_DIST_M)
    left, right = tree_idx.query(buf.values, predicate="intersects")
    foreign = pkg[left] != pkg[right]
    hit = np.zeros(len(reaches), dtype=bool)
    np.logical_or.at(hit, left[foreign], True)
    df = pd.DataFrame({"pkg": pkg, "hit": hit})
    return (df.groupby("pkg")["hit"].mean() * 100.0).round(2)


# --------------------------------------------------------------------------------------
# Phase
# --------------------------------------------------------------------------------------

def _plot_key(s: pd.Series) -> pd.Series:
    """Normalise a plot identifier so the two sides of the join actually meet.

    `W10_plot_loads` stores PLOT_ID as an integer (negative for the unparcelled buildings);
    the contract stores it as a string. A float round trip anywhere in between turns
    1104406 into '1104406.0' and the join then matches nothing at all - silently, and the
    phase would come out 0 everywhere with no sign that anything had failed. Stripping the
    trailing '.0' costs one line and removes the whole failure mode.
    """
    return s.astype(str).str.strip().str.replace(r"\.0$", "", regex=True)


def developed_load(conns: pd.DataFrame, plot_class: Optional[pd.Series]) -> pd.Series:
    """Per-connection load that sits on a plot carrying structures today.

    NOT a measurement of present-day flow. The load on a developed plot is still computed
    at the saturation ratio (1.456 properties per plot, OR 5.32), so this is the ultimate
    load OF THE DEVELOPED PLOTS - an upper bound on what those plots discharge now.
    [Likely] It is nonetheless the right phase driver available: it separates a package
    serving a built quarter from one serving platted desert, which is the distinction the
    phase is for. It does not, and cannot, place a package in 2030 rather than 2055.
    """
    q = pd.to_numeric(conns.get("Q_ADF_M3D"), errors="coerce").fillna(0.0)
    if plot_class is None:
        return pd.Series(np.nan, index=conns.index)
    cls = _plot_key(conns["PLOT_ID"]).map(plot_class)
    hit = float(cls.notna().mean())
    if hit < 0.5:
        # A join that mostly misses returns zeros, and a zero here reads as "no developed
        # plots" - a finding, not a failure. Refuse to make that claim on a broken join.
        print(f"  WARNING: only {hit:.1%} of load units matched a plot in "
              f"{os.path.basename(PLOT_LOADS)}. PHASE cannot be set from a join this "
              "incomplete, so it is left unassigned rather than reported as zero.")
        return pd.Series(np.nan, index=conns.index)
    if hit < 1.0:
        print(f"  {1 - hit:.1%} of load units matched no plot record; their load counts "
              "as undeveloped, which understates the start-year demand rather than "
              "overstating it")
    return q.where(cls.isin(DEV_CLASSES), 0.0)


def assign_phase(pkg_stats: pd.DataFrame,
                 horizon_targets: Optional[Dict[int, float]] = None) -> pd.Series:
    """PHASE per package. 1 where demand exists at the start year, 0 where it cannot be set.

    The refusal to guess is deliberate and it is the point of this function. G201-p59 makes
    development percentages over the design period MANDATORY input to any phasing
    ("development speed must be considered through appropriate phasing assumptions ...
    particularly avoiding overestimation"), and they have not been supplied. Splitting the
    remaining packages across 2030 / 2055 / ultimate on a curve of our own invention would
    put a fabricated number in a client deliverable and make the phasing look settled.

    `horizon_targets` = {model_year: cumulative m3/d to be served by then} turns this into
    the full four-phase split with no other change: packages are ordered by developed load
    per kilometre - most demand per metre of pipe first, which is the same marginal
    ordering the options appraisal uses - and accumulated into each horizon in turn.
    """
    dev = pd.to_numeric(pkg_stats["Q_DEV_M3D"], errors="coerce").fillna(0.0)
    phase = pd.Series(np.where(dev > 0, 1, 0), index=pkg_stats.index, dtype=int)
    if not horizon_targets:
        return phase
    order = (dev / pd.to_numeric(pkg_stats["LEN_KM"], errors="coerce").replace(0, np.nan))
    ranked = order.sort_values(ascending=False).index
    cum, ph = 0.0, {}
    years = sorted(horizon_targets)
    bucket = 0
    for r in ranked:
        cum += float(pd.to_numeric(pkg_stats.at[r, "Q_ULT_M3D"], errors="coerce") or 0.0)
        while bucket < len(years) and cum > horizon_targets[years[bucket]]:
            bucket += 1
        ph[r] = min(bucket + 1, len(years))
    return pd.Series(ph, dtype=int).reindex(pkg_stats.index).fillna(0).astype(int)


# --------------------------------------------------------------------------------------
# Build the package table
# --------------------------------------------------------------------------------------

def build_packages(tree: Tree, pkg_of: Dict[str, str], roots: Sequence[str],
                   nodes: gpd.GeoDataFrame, reaches: gpd.GeoDataFrame,
                   conns: Optional[pd.DataFrame],
                   plot_class: Optional[pd.Series],
                   rm_ds: Optional[Dict[str, str]],
                   horizon_targets: Optional[Dict[int, float]] = None
                   ) -> Tuple[gpd.GeoDataFrame, pd.DataFrame, Dict[str, str]]:
    """The `packages` layer, plus the diagnostics the contract's schema does not carry.

    SEAM_PCT, the band flags and the developed-load split are genuinely useful and are
    genuinely NOT contract fields. They go to a CSV beside the layer rather than onto it:
    the contract's EXCLUDED register exists because a schema that grows one field per stage
    ends up carrying nine nothing reads, and adding a column here would be a stage-local
    schema decision - exactly the thing that register refuses. If SEAM_PCT belongs on the
    layer, it belongs in `contract.PACKAGES`, edited there.
    """
    node_kind = dict(zip(nodes["NODE_UID"].astype(str), nodes["NODE_KIND"].astype(str)))
    dep = dependencies(tree, pkg_of, roots, node_kind, rm_ds)

    # Name in commissioning order, so the identifier itself reads as the build sequence on
    # a drawing. NAMA's own 5A-n numbering does not encode order and their chain has to be
    # reconstructed from outlet coordinates every time somebody asks - ours should not.
    order = sorted(roots, key=lambda r: (int(dep.at[r, "comm_seq"]),
                                         -_pkg_len(tree, pkg_of, r), r))
    name = {r: f"P{i + 1:02d}" for i, r in enumerate(order)}

    node_pkg = pd.Series({v: name[r] for v, r in pkg_of.items()})
    edge_pkg = reaches["US_NODE"].astype(str).map(node_pkg)

    rows = []
    for r in order:
        members = [v for v, p in pkg_of.items() if p == r]
        rows.append(dict(
            PACKAGE=name[r],
            OUTLET=r,
            DS_PKG=name.get(dep.at[r, "ds_root"], "") if dep.at[r, "ds_root"] else "",
            COMM_SEQ=int(dep.at[r, "comm_seq"]),
            INDEP=int(dep.at[r, "indep"]),
            DANGLING=int(dep.at[r, "dangling"]),
            LEN_KM=round(_pkg_len(tree, pkg_of, r) / 1000.0, 3),
            N_NODE=len(members),
            KIND=node_kind.get(r, "chamber"),
        ))
    pk = pd.DataFrame(rows).set_index("PACKAGE", drop=False)

    # ---- plots and load, from the connections layer. The band is measured in PLOTS, so a
    #      package with no plot count is a package whose size cannot be checked at all.
    if conns is not None and len(conns):
        c = conns.copy()
        c["PACKAGE"] = c["OUT_NODE"].astype(str).map(node_pkg)
        c["Q_DEV"] = developed_load(c, plot_class)
        g = c.groupby("PACKAGE")
        pk["N_PLOT"] = g["PLOT_ID"].nunique().reindex(pk.index).fillna(0).astype(int)
        pk["N_PROP"] = g["N_PROP"].sum().reindex(pk.index).fillna(0.0).round(1)
        pk["Q_ULT_M3D"] = pd.to_numeric(g["Q_ADF_M3D"].sum(), errors="coerce") \
            .reindex(pk.index).fillna(0.0).round(1)
        # NaN, not 0.0, when the plot build-status is unavailable or the join failed. "No
        # developed load" and "nobody looked" are different findings, and a zero reports
        # the first while meaning the second - which is how a phasing plan gets published
        # on no evidence at all.
        pk["Q_DEV_M3D"] = (g["Q_DEV"].sum().reindex(pk.index).round(1)
                           if c["Q_DEV"].notna().any() else np.nan)
    else:
        pk["N_PLOT"] = 0
        pk["N_PROP"] = 0.0
        pk["Q_ULT_M3D"] = 0.0
        pk["Q_DEV_M3D"] = np.nan

    pk["PHASE"] = assign_phase(pk, horizon_targets)

    # ---- ONE_TREE, recomputed rather than asserted. The partition makes it true by
    #      construction; checking it independently from the published reaches is what
    #      turns "true by construction" into evidence, and it is DELIVERABLE_SPEC F6.
    one_tree, outlets = {}, {}
    for r in order:
        members = {v for v, p in pkg_of.items() if p == r}
        leaving = [v for v in members
                   if tree.parent(v) is None or tree.parent(v) not in members]
        # connectivity: walking down from every member must reach r without leaving the set
        connected = True
        for v in members:
            cur, hops = v, 0
            while cur != r and hops <= len(members):
                nxt = tree.parent(cur)
                if nxt is None or nxt not in members:
                    connected = False
                    break
                cur, hops = nxt, hops + 1
            if not connected:
                break
        outlets[name[r]] = len(leaving)
        one_tree[name[r]] = int(connected and len(leaving) == 1)
    pk["ONE_TREE"] = pd.Series(one_tree).reindex(pk.index).fillna(0).astype(int)
    pk["N_OUTLET"] = pd.Series(outlets).reindex(pk.index).fillna(0).astype(int)

    # ---- territory, and the band
    seam = seam_share(reaches.assign(PACKAGE=edge_pkg))
    pk["SEAM_PCT"] = seam.reindex(pk.index).fillna(0.0)
    pk["BAND_LEN"] = np.where(
        (pk["LEN_KM"] >= BAND["PKG_LEN_MIN_KM"][0]) & (pk["LEN_KM"] <= BAND["PKG_LEN_MAX_KM"][0]),
        "in", "OUT")
    pk["BAND_PLOT"] = np.where(
        (pk["N_PLOT"] >= BAND["PKG_PLOTS_MIN"][0]) & (pk["N_PLOT"] <= BAND["PKG_PLOTS_MAX"][0]),
        "in", "OUT")
    pk["BAND_SEAM"] = np.where(pk["SEAM_PCT"] <= SEAM_MAX_PCT, "in", "OUT")

    # ---- geometry: the convex hull of the package's own reaches. A hull, not a dissolve,
    #      because the drawing this feeds is the phasing plan (DELIVERABLE_SPEC D.3) where
    #      the reader needs the territory, not the pipe. The layer's contract geom is
    #      "none" - the hull is a convenience for QGIS and is not audited.
    hulls = {}
    for p, sub in reaches.assign(PACKAGE=edge_pkg).groupby("PACKAGE"):
        h = unary_union(MultiLineString([g for g in sub.geometry if g is not None])).convex_hull
        hulls[p] = h if h.geom_type == "Polygon" else h.buffer(1.0)
    # A package holding only its outlet chamber carries no reach and so no hull. It can
    # only arise where a terminal had nothing upstream that would fit under the ceiling,
    # which is reported as an under-band package - but a null geometry would break the
    # write and lose the row, so it falls back to the outlet itself.
    node_pt = dict(zip(nodes["NODE_UID"].astype(str), nodes.geometry))
    geom = [hulls.get(p) if p in hulls
            else node_pt[o].buffer(5.0) if o in node_pt else None
            for p, o in zip(pk.index, pk["OUTLET"])]

    layer = gpd.GeoDataFrame(
        pk[["PACKAGE", "PHASE", "LEN_KM", "N_PLOT", "OUTLET", "DS_PKG",
            "COMM_SEQ", "INDEP", "ONE_TREE"]].reset_index(drop=True),
        geometry=geom, crs=K.CRS_EPSG)
    diag = pk.reset_index(drop=True)
    return layer, diag, name


# --------------------------------------------------------------------------------------
# Stamping PACKAGE / PHASE back onto the network layers
# --------------------------------------------------------------------------------------

def stamp(gdf: gpd.GeoDataFrame, key: str, node_pkg: pd.Series, node_phase: pd.Series,
          layer_name: str, rec=None, unassigned_ok: bool = False) -> gpd.GeoDataFrame:
    """Write PACKAGE and PHASE onto a layer, keyed on whichever node identifies it.

    Both are `_PROV` fields on every layer in the contract, and they are `required=False`
    precisely so a layer is publishable at stage 4 and only complete at stage 8 - this is
    the stage that completes them. The chamber, pipe, station, rising main and connection
    schedules all print PACKAGE (contract SCHEDULES), so a layer that leaves here without
    it makes six deliverables unprintable.

    `unassigned_ok` is for `connections` alone, and it is not laxity. The contract lets a
    load unit carry no OUT_NODE when its `WHY` says why - a plot served by a satellite
    works or an on-site system is SERVICED as the TOR requires without being connected to
    this network (philosophy sec 8a). Such a plot has no package because it is in no
    package. Every one is counted into a funnel and named, never dropped: that difference
    is exactly the 1,233 m3/d W10 lost.
    """
    out = gdf.copy()
    k = out[key].astype(str)
    out["PACKAGE"] = k.map(node_pkg).fillna("")
    out["PHASE"] = pd.to_numeric(k.map(node_phase), errors="coerce").fillna(0).astype(int)
    # STAGE is "the stage that LAST wrote this row" and it is the only field that makes
    # invariant 10 - no stage silently no-ops - checkable after the fact (audit G4). This
    # stage writes two columns onto five layers; leaving STAGE naming s6 would say s8 never
    # touched them, which is the exact claim the field exists to disprove.
    if "STAGE" in out.columns:
        out["STAGE"] = STAGE
    lost = out.index[out["PACKAGE"] == ""]
    if len(lost):
        if not unassigned_ok:
            raise K.ContractError(
                f"{len(lost):,} rows of '{layer_name}' could not be given a package - "
                f"their {key} is not in the partition. Every feature belongs to exactly "
                "one package, or the phasing plan has holes in it that no drawing shows.")
        ids = out.loc[lost, gdf.columns[0]].astype(str).tolist()
        print(f"  {layer_name}: {len(lost):,} rows carry no package because their {key} "
              "is blank - they are not served by this network")
        if rec is not None:
            rec.funnel(f"{layer_name} into packages", len(out)).drop(
                "no OUT_NODE - served by another system, or not served (contract "
                "connections.WHY carries the reason)", ids=ids)
    return out


def relabel(nodes: gpd.GeoDataFrame, tree: Tree, pkg_of: Dict[str, str],
            name: Dict[str, str]) -> gpd.GeoDataFrame:
    """Rebuild NODE_REF in NAMA's own grammar now that the package is known.

    `P03-SM-MH0117`, against their `5A-2-SM.2-MH391`. Objective 3: NAMA runs this for fifty
    years and it has to read like their network. This is safe to do here and would not have
    been safe anywhere else - NODE_REF is referenced by NOTHING (the contract is explicit,
    and SewerGEMS labels manholes with NODE_UID for exactly this reason), so a relabel
    after the packages are known cannot orphan a single reference. Sequence is per package
    and follows the post-order, so numbers rise from the head of a branch towards the
    outlet the way a manhole schedule is read.
    """
    out = nodes.copy()
    seq: Dict[str, int] = defaultdict(int)
    refs = {}
    for v in tree.postorder():
        p = name[pkg_of[v]]
        seq[p] += 1
        refs[v] = (p, seq[p])
    tier = dict(zip(out["NODE_UID"].astype(str), out["TIER"].astype(str)))
    out["NODE_REF"] = [
        f"{refs[u][0]}-{K.TIER_TOKEN.get(tier.get(u, 'lateral'), 'L')}-MH{refs[u][1]:04d}"
        if u in refs else r
        for u, r in zip(out["NODE_UID"].astype(str), out["NODE_REF"].astype(str))]
    return out


# --------------------------------------------------------------------------------------
# Acceptance tests F6-F8, which audit.py does not implement
# --------------------------------------------------------------------------------------

def acceptance(diag: pd.DataFrame) -> pd.DataFrame:
    """DELIVERABLE_SPEC D.6 additions F6, F7, F8 - stated here because they are not in
    `audit.REGISTRY`. Philosophy sec 8 makes a check that cannot run a failure, so a check
    that does not exist is worse; running them here and printing the result is the interim,
    and the permanent home is `audit.py`."""
    rows = [
        dict(check="F6", requirement="every package has exactly one outlet chamber",
             source="DELIVERABLE_SPEC C.3 / D.6",
             n_bad=int((diag["N_OUTLET"] != 1).sum())),
        dict(check="F6b", requirement="every package is one connected tree",
             source="DELIVERABLE_SPEC C.3 / D.6",
             n_bad=int((diag["ONE_TREE"] != 1).sum())),
        dict(check="F6c", requirement="every package discharges somewhere the design "
                                      "records - a package, a station, the works or a tie",
             source="philosophy H15 / contract nodes cross-field",
             n_bad=int(diag["DANGLING"].sum())),
        dict(check="F7", requirement="COMM_SEQ respects the dependency graph",
             source="DELIVERABLE_SPEC C.4 / D.6",
             n_bad=int(sum(1 for r in diag.itertuples()
                           if r.DS_PKG and not r.INDEP
                           and r.COMM_SEQ <= int(diag.set_index("PACKAGE")
                                                 .at[r.DS_PKG, "COMM_SEQ"])))),
        dict(check="F8", requirement=f"SEAM_PCT <= {SEAM_MAX_PCT:.0f} % per package",
             source="DELIVERABLE_SPEC C.2 / D.6",
             n_bad=int((diag["SEAM_PCT"] > SEAM_MAX_PCT).sum())),
        dict(check="B1", requirement=f"length within "
                                     f"{BAND['PKG_LEN_MIN_KM'][0]}-"
                                     f"{BAND['PKG_LEN_MAX_KM'][0]} km",
             source="DELIVERABLE_SPEC C.1 (measured, not a guideline)",
             n_bad=int((diag["BAND_LEN"] == "OUT").sum())),
        dict(check="B2", requirement=f"plots within {BAND['PKG_PLOTS_MIN'][0]}-"
                                     f"{BAND['PKG_PLOTS_MAX'][0]}",
             source="DELIVERABLE_SPEC C.1 (measured, not a guideline)",
             n_bad=int((diag["BAND_PLOT"] == "OUT").sum())),
    ]
    df = pd.DataFrame(rows)
    df["status"] = np.where(df["n_bad"] == 0, "pass", "FAIL")
    return df


# --------------------------------------------------------------------------------------
# Loading, and the graceful stop
# --------------------------------------------------------------------------------------

def _read(path: str, layer: str) -> Optional[gpd.GeoDataFrame]:
    """None means the layer IS NOT THERE, and nothing else.

    A blanket `except: return None` here would turn a locked, corrupt or half-written
    GeoPackage into "stage 4 has not run yet": `_waiting()` would then name the wrong stage,
    `rec.did_nothing()` would file the wrong reason, and the run would exit 0. That is the
    W10 failure mode exactly - RoadTreatment called with units=None, three stages quietly
    doing nothing. A read that fails for any reason other than absence is raised.
    """
    if not os.path.exists(path):
        return None
    if layer not in set(gpd.list_layers(path)["name"].astype(str)):
        return None
    return gpd.read_file(path, layer=layer)


def _waiting(missing: Sequence[Tuple[str, str]]) -> None:
    print("STAGE 8 (phasing and packages) IS WAITING ON UPSTREAM WORK.")
    print(f"audited artefact: {GPKG}"
          + ("" if os.path.exists(GPKG) else "   <- does not exist yet"))
    print()
    w = max(len(m[0]) for m in missing)
    for name, why in missing:
        print(f"  {name:<{w}}  {why}")
    print()
    print("Nothing was written. A package is a subtree of the design graph, so it cannot "
          "be\ncomputed before the graph is published - and inventing one from W10's "
          "layers would\nreproduce the 206 'subnetworks' this stage exists to replace "
          "(median 1.16 km,\nlargest 265.8 km, DELIVERABLE_SPEC C.5 item 3).")


def load_inputs() -> Tuple[Optional[Dict], List[Tuple[str, str]]]:
    nodes = _read(GPKG, "nodes")
    reaches = _read(GPKG, "reaches")
    conns = _read(GPKG, "connections")
    stations = _read(GPKG, "stations")
    rms = _read(GPKG, "rising_mains")

    missing: List[Tuple[str, str]] = []
    # Named BY FILE, not by build-brief stage number. The brief numbers the seven design
    # stages and the files number the ten modules, so "stage 5" here pointed at
    # s5_chambers.py when the stations it wants come from s7_stations.py.
    if nodes is None:
        missing.append(("nodes", "s5_chambers.py - the vertex set, and NODE_KIND, which "
                                 "marks the station / outfall / tie seams"))
    if reaches is None:
        missing.append(("reaches", "s4_hierarchy.py / s5_chambers.py - US_NODE / DS_NODE / "
                                   "LEN_M are the tree the partition cuts"))
    if conns is None:
        missing.append(("connections", "s1_scope.py / s5b_tertiary.py - one row per load "
                                       "unit. The package band is measured in PLOTS "
                                       "(180-2,180), so without it no package size can be "
                                       "checked at all"))
    if missing:
        return None, missing

    notes = []
    if stations is None:
        notes.append("no `stations` layer from s7_stations.py: the NODE_KIND='station' "
                     "seams still bind, but no station carries a duty, a wet well or a "
                     "COMM_PT, so the phasing plan cannot say which packages a station "
                     "makes independently commissionable (P8).")
    if rms is None:
        notes.append("no `rising_mains` layer: a station package cannot record which "
                     "package it discharges into, only that it does not depend on one. "
                     "Note this is also the correct state where every lift is taken inside "
                     "its own chamber - s7 publishes the layer EMPTY in that case, and an "
                     "empty layer is different from an absent one.")
    return dict(nodes=nodes, reaches=reaches, connections=conns,
                stations=stations, rising_mains=rms, notes=notes), []


def plot_class_map() -> Optional[pd.Series]:
    """PLOT_ID -> CLASS, read from the W10 plot loads. Read-only; W10 is never written."""
    if not os.path.exists(PLOT_LOADS):
        print(f"  WARNING: {PLOT_LOADS} is not there, so no plot carries a build status.")
        return None
    try:
        g = gpd.read_file(PLOT_LOADS, layer=PLOT_LOADS_LAYER,
                          columns=["PLOT_ID", "CLASS"], ignore_geometry=True)
    except Exception:
        # The column-subset read is an optimisation, not a contract; falling back to the
        # full read is legitimate. Failing BOTH is not, and it is said out loud - a
        # swallowed read here publishes PHASE 0 on every package with no sign that the
        # evidence was never opened.
        try:
            g = gpd.read_file(PLOT_LOADS, layer=PLOT_LOADS_LAYER)
        except Exception as e:
            print(f"  WARNING: {PLOT_LOADS} exists but layer {PLOT_LOADS_LAYER!r} could "
                  f"not be read ({type(e).__name__}: {e}). No plot build status.")
            return None
    return pd.Series(g["CLASS"].astype(str).values, index=_plot_key(g["PLOT_ID"]))


# --------------------------------------------------------------------------------------
# The run
# --------------------------------------------------------------------------------------

def run(horizon_targets: Optional[Dict[int, float]] = None, publish: bool = True) -> int:
    data, missing = load_inputs()
    # Stage-specific manifest file, deliberately. `contract.Manifest` keeps its records in
    # a class attribute per PROCESS and rewrites the whole file on save, so every stage
    # writing to the shared `run/manifest.json` erases the record of every stage that ran
    # before it in a different process. Same convention as s7 and s9.
    mpath = os.path.join(RUN, f"manifest_{STAGE}.json")
    with K.Manifest.stage(STAGE, ORDER, path=mpath) as rec:
        if data is None:
            _waiting(missing)
            rec.did_nothing("upstream layers absent: "
                            + ", ".join(m[0] for m in missing)
                            + ". A package is a subtree of the design graph and cannot be "
                              "computed before the graph exists.")
            return 0

        nodes, reaches = data["nodes"], data["reaches"]
        conns, stations, rms = data["connections"], data["stations"], data["rising_mains"]
        for n in data["notes"]:
            print(f"NOTE: {n}")
            rec.note(n)
        rec.read("nodes", GPKG, len(nodes))
        rec.read("reaches", GPKG, len(reaches))
        rec.read("connections", GPKG, len(conns))

        # every node must be in the tree; an isolated one is a chamber nothing drains
        # through, which the contract already calls a defect. Counted, never dropped.
        used = set(reaches["US_NODE"].astype(str)) | set(reaches["DS_NODE"].astype(str))
        f = rec.funnel("nodes into packages", len(nodes))
        iso = [u for u in nodes["NODE_UID"].astype(str) if u not in used]
        if iso:
            f.drop("isolated - no reach at all (contract Network.check calls this a "
                   "defect; it cannot belong to a package)", ids=iso)

        node_ids = [u for u in nodes["NODE_UID"].astype(str) if u in used]
        tree = Tree(reaches, node_ids)

        kinds = dict(zip(nodes["NODE_UID"].astype(str), nodes["NODE_KIND"].astype(str)))
        seams = [u for u in node_ids if kinds.get(u) in SEAM_KINDS]
        if stations is not None:
            st_ids = set(stations["NODE_UID"].astype(str))
            orphan_st = sorted(st_ids - set(node_ids))
            if orphan_st:
                raise K.ContractError(
                    f"{len(orphan_st):,} stations are not nodes in the reach graph, e.g. "
                    f"{orphan_st[:5]}. A station is a node in the SAME graph (contract "
                    "STATIONS.refs), and one that is not cannot be a package seam - the "
                    "package above it would silently keep draining to the trunk below.")
            seams = sorted(set(seams) | st_ids)
        print(f"{len(node_ids):,} nodes, {len(reaches):,} reaches, "
              f"{reaches['LEN_M'].sum()/1000:.1f} km, {len(seams):,} forced seams "
              f"({', '.join(SEAM_KINDS)})")

        pkg_of, roots, notes = partition(tree, seams)
        f.close(len(pkg_of))

        rm_ds = None
        if rms is not None and len(rms):
            rm_ds = dict(zip(rms["US_NODE"].astype(str), rms["DS_NODE"].astype(str)))

        # PHASE 0 means two different things and only one of them is a finding: "platted
        # desert" and "nobody could read the build status". Q_DEV_M3D keeps them apart (NaN
        # against 0.0) but the PUBLISHED layer carries only PHASE, so the second case has
        # to be said in the run and filed in the manifest or the phasing plan reads as
        # evidence when it is an absence.
        plot_class = plot_class_map()
        if plot_class is None:
            msg = ("plot build status unavailable, so PHASE is 0 on every package meaning "
                   "'not yet assigned', NOT 'platted desert'. Q_DEV_M3D stays NaN and the "
                   "phasing plan is not evidence until it is re-run with the plot loads.")
            print(f"  WARNING: {msg}")
            rec.note(msg)
        layer, diag, name = build_packages(
            tree, pkg_of, roots, nodes, reaches, conns, plot_class, rm_ds,
            horizon_targets)

        node_pkg = pd.Series({v: name[r] for v, r in pkg_of.items()})
        phase_of = dict(zip(diag["PACKAGE"], diag["PHASE"]))
        node_phase = node_pkg.map(phase_of)

        print()
        print(diag[["PACKAGE", "PHASE", "COMM_SEQ", "LEN_KM", "N_PLOT", "N_PROP",
                    "Q_ULT_M3D", "Q_DEV_M3D", "SEAM_PCT", "INDEP", "ONE_TREE",
                    "DANGLING", "DS_PKG", "KIND"]].to_string(index=False))
        for n in notes[:20]:
            print(f"  partition: {n}")
        if len(notes) > 20:
            print(f"  partition: ... and {len(notes) - 20} more")

        # The length must close. Every reach is filed under exactly one package, so the
        # packages must add back up to the network - the same arithmetic the funnel does
        # for load units. W10's 1,233 m3/d went missing because nobody ever subtracted.
        km_pkg = K.value("package_network_km", diag)
        km_net = float(pd.to_numeric(reaches["LEN_M"], errors="coerce").sum()) / 1000.0
        if abs(km_pkg - km_net) > 0.005 * len(diag) + 0.001:
            raise K.ContractError(
                f"the packages carry {km_pkg:,.3f} km against the reach layer's "
                f"{km_net:,.3f} km. Every reach belongs to exactly one package, so the "
                f"{abs(km_pkg - km_net):,.3f} km difference is pipe that fell out of the "
                "partition - a silent drop, not a rounding error.")

        acc = acceptance(diag)
        print()
        print(acc.to_string(index=False))

        rec.metric("package_count", K.value("package_count", diag))
        rec.metric("package_network_km", round(K.value("package_network_km", diag), 1))
        rec.metric("independent_package_count",
                   K.value("independent_package_count", diag))
        rec.metric("phase_0_packages", int((diag["PHASE"] == 0).sum()))

        os.makedirs(RUN, exist_ok=True)
        diag.to_csv(os.path.join(RUN, "s8_packages_diagnostics.csv"), index=False)
        acc.to_csv(os.path.join(RUN, "s8_packages_acceptance.csv"), index=False)

        # The STRUCTURAL checks block; the measured band does not. Philosophy sec 8 splits
        # them exactly there - "any breach of a settled project rule" is blocking, while
        # "as-built calibration" is reporting only, and 3.5-40 km / 180-2,180 plots / 15 %
        # are calibration against NAMA, not a "shall". But a package that is not one
        # connected tree with one outlet, or that discharges nowhere, or that is told to
        # commission before the thing it drains into, is a FAILED package - the contract
        # says so on the field itself ("ONE_TREE ... 0 is a failed package, not a note").
        # Printing that and publishing anyway is how a checklist becomes decoration.
        bad = acc[(acc["check"].isin(["F6", "F6b", "F6c", "F7"]))
                  & (acc["status"] == "FAIL")]
        if len(bad):
            raise K.ContractError(
                "structural acceptance failed, so nothing was published:\n"
                + bad[["check", "requirement", "n_bad", "source"]].to_string(index=False)
                + f"\n\nThe evidence is in {os.path.join(RUN, 's8_packages_acceptance.csv')}"
                  f" and {os.path.join(RUN, 's8_packages_diagnostics.csv')}. These four are "
                  "true by construction of the partition, so a failure means the reach "
                  "layer is not the forest the contract guarantees - fix it upstream, not "
                  "here. The length and plot bands (B1, B2) and the territorial test (F8) "
                  "are measured against NAMA and stay reporting-only.")

        if not publish:
            rec.wrote("diagnostics", RUN, len(diag))
            return 0

        # ---- publish. The packages layer, then PACKAGE/PHASE onto everything else, then
        #      the schedule. Republishing the network layers re-runs contract.validate on
        #      them, which is a feature: a stage that only appends a column still has to
        #      hand back a layer that passes.
        K.publish(layer, "packages", W11A, stage=STAGE)
        K.mirror_shapefile(layer, "packages", W11A)
        rec.wrote("packages", GPKG, len(layer))

        # isolated nodes are already named in the funnel above, so they may leave here
        # without a package - but they leave VISIBLY, and they are a defect stage 4 owns.
        nodes_out = relabel(stamp(nodes, "NODE_UID", node_pkg, node_phase, "nodes",
                                  unassigned_ok=bool(iso)),
                            tree, pkg_of, name)
        K.publish(nodes_out, "nodes", W11A, stage=STAGE)
        rec.wrote("nodes", GPKG, len(nodes_out))

        reaches_out = stamp(reaches, "US_NODE", node_pkg, node_phase, "reaches")
        K.publish(reaches_out, "reaches", W11A, stage=STAGE)
        rec.wrote("reaches", GPKG, len(reaches_out))

        conns_out = stamp(conns, "OUT_NODE", node_pkg, node_phase, "connections",
                          rec=rec, unassigned_ok=True)
        K.publish(conns_out, "connections", W11A, stage=STAGE)
        rec.wrote("connections", GPKG, len(conns_out))

        if stations is not None and len(stations):
            st = stamp(stations, "NODE_UID", node_pkg, node_phase, "stations")
            # The relabel above rewrote NODE_REF on the CHAMBERS. The stations layer carries
            # its own copy of the same label, and leaving it behind means the station
            # schedule prints `P1-L-MH0014` for the chamber the chamber schedule now calls
            # `P02-SM-MH0007` - two deliverables naming one structure differently. Copied,
            # not recomputed: the chamber layer is where the label is minted, and a second
            # derivation here is a second definition (P2).
            ref_of = dict(zip(nodes_out["NODE_UID"].astype(str),
                              nodes_out["NODE_REF"].astype(str)))
            st["NODE_REF"] = (st["NODE_UID"].astype(str).map(ref_of)
                              .fillna(st["NODE_REF"].astype(str)))
            # COMM_PT - "1 where this station makes its package commissionable on its own,
            # the P8 case where objective 4 beats objective 5". It was declared on the
            # contract's STATIONS spec and written by NO stage: s7 defers it here in as many
            # words ("package seams are stage 8's; this stage would be inventing them") and
            # this stage did not pick it up, so the field shipped blank on every station and
            # the one property a station is bought for was unreadable in the deliverable.
            # It is computable here and only here: a station is a commissioning point when
            # it is the OUTLET of a package that INDEP says can be switched on without its
            # downstream neighbour. Same number, same source - COMM_PT on the station and
            # INDEP on the package can never now disagree.
            indep_at = {str(o): int(i) for o, i in zip(diag["OUTLET"], diag["INDEP"])}
            st["COMM_PT"] = (st["NODE_UID"].astype(str).map(indep_at)
                             .fillna(0).astype(int))
            n_cp = int(st["COMM_PT"].sum())
            rec.metric("commissioning_point_stations", n_cp)
            rec.note(f"COMM_PT set on {len(st):,} station(s); {n_cp:,} of them are a "
                     "commissioning point - the outlet of a package that can be switched "
                     "on without the trench below it (P8, DELIVERABLE_SPEC C.4). A station "
                     "in mid-tree still drains onward and is not one.")
            K.publish(st, "stations", W11A, stage=STAGE)
            rec.wrote("stations", GPKG, len(st))
        if rms is not None and len(rms):
            rm = stamp(rms, "US_NODE", node_pkg, node_phase, "rising_mains")
            K.publish(rm, "rising_mains", W11A, stage=STAGE)
            rec.wrote("rising_mains", GPKG, len(rm))

        K.schedule_frame(layer, "packages", stage=STAGE).to_csv(
            os.path.join(RUN, "schedule_packages.csv"), index=False)

        # invariant 2, on what was just written rather than on what is in memory
        K.Network.assert_round_trip(_read(GPKG, "nodes"), _read(GPKG, "reaches"))
        print(f"\npublished to {GPKG}")
    return 0


# --------------------------------------------------------------------------------------
# Calibration against NAMA's own packages
# --------------------------------------------------------------------------------------

def calibrate() -> int:
    """Run the partitioner on the 2006 built network and compare with NAMA's own 5A-1..5A-5.

    The only reference partition that exists. Be clear about what it does and does not
    prove: the size band was MEASURED from this same network, so recovering packages of a
    similar size is close to tautological and is not independent evidence. What it does
    test independently is everything else - that the sweep terminates on a real 3,267-pipe
    tree, that every package it produces is one connected tree with one outlet, that the
    dependency graph is acyclic, and whether the seams it chooses land anywhere near the
    seams a human engineer chose in 2006. Reads W10; writes only to W11a/run.
    """
    if not os.path.exists(EXISTING_BUILT):
        print(f"no built network at {EXISTING_BUILT}")
        return 0
    g = gpd.read_file(EXISTING_BUILT)
    g = g[(pd.to_numeric(g["IS_DUP"], errors="coerce").fillna(0) == 0)].copy()
    g["US_NODE"] = g["US_MHID"].astype(str)
    g["DS_NODE"] = g["DS_MHID"].astype(str)
    g["EDGE_UID"] = g["FEATUREID"].astype(str)
    g["LEN_M"] = pd.to_numeric(g["LEN_M"], errors="coerce").fillna(0.0)

    # NAMA's data has nodes with two outgoing pipes (a record artefact, not a built
    # bifurcation). Keep the longest and count the rest - a forest is required and a
    # silently dropped pipe is not acceptable even in a calibration read.
    g = g.sort_values("LEN_M", ascending=False)
    dup = g.duplicated("US_NODE", keep="first")
    if dup.any():
        print(f"calibration: {int(dup.sum())} pipes drop - their upstream manhole already "
              "has an outgoing pipe (NAMA record artefact, not a built bifurcation)")
    g = g[~dup]
    g = g[g["US_NODE"] != g["DS_NODE"]]

    ids = sorted(set(g["US_NODE"]) | set(g["DS_NODE"]))
    tree = Tree(g, ids)
    # NAMA's real seam: the pumping station at the end of 5A-1, plus every terminal.
    seams = [v for v in ids if tree.parent(v) is None or "SPS" in v or "STP" in v]
    pkg_of, roots, notes = partition(tree, seams)

    edge_pkg = g["US_NODE"].map({v: r for v, r in pkg_of.items()})
    out = pd.DataFrame({
        "ours": edge_pkg.values,
        "nama": g["PROJECTCOD"].astype(str).values,
        "len": g["LEN_M"].values,
    })
    ours = (out.groupby("ours")["len"].agg(["count", "sum"])
            .rename(columns={"count": "pipes", "sum": "m"}))
    ours["km"] = (ours["m"] / 1000).round(2)
    ours["nama_majority"] = out.groupby("ours")["nama"].agg(
        lambda s: s.value_counts().idxmax())
    ours["purity_pct"] = (out.groupby("ours")["nama"].agg(
        lambda s: s.value_counts(normalize=True).iloc[0]) * 100).round(1)
    ours = ours.sort_values("km", ascending=False)[
        ["pipes", "km", "nama_majority", "purity_pct"]]

    nama = g.groupby("PROJECTCOD")["LEN_M"].agg(["count", "sum"])
    nama["km"] = (nama["sum"] / 1000).round(2)

    print("NAMA's own five packages, on the same cleaned tree:")
    print(nama[["count", "km"]].to_string())
    print()
    print(f"our partition, target {BAND['PKG_LEN_TARGET_KM'][0]:.0f} km, "
          f"cap {BAND['PKG_LEN_MAX_KM'][0]:.0f} km, floor "
          f"{BAND['PKG_LEN_MIN_KM'][0]:.1f} km:")
    print(ours.to_string())
    # the reverse view: how many of ours each of NAMA's is spread over. A package of
    # theirs landing in one of ours means the seam agrees; landing in three means our
    # cut runs straight through the middle of a real contract.
    back = out.groupby("nama").agg(ours_n=("ours", "nunique"),
                                   km=("len", lambda s: round(s.sum() / 1000, 2)))
    back["in_one_of_ours_pct"] = (out.groupby("nama")["ours"].agg(
        lambda s: s.value_counts(normalize=True).iloc[0]) * 100).round(1)
    print("NAMA's packages seen from ours:")
    print(back.to_string())

    # The two claims below are VERIFIED here rather than asserted in prose. One outlet per
    # package is the property DELIVERABLE_SPEC C.3 measured on all five of NAMA's; an
    # acyclic dependency graph is test F7. Neither is worth stating unless it was run.
    bad_outlet = []
    for r in roots:
        members = {v for v, p in pkg_of.items() if p == r}
        leaving = [v for v in members
                   if tree.parent(v) is None or tree.parent(v) not in members]
        if len(leaving) != 1:
            bad_outlet.append((r, len(leaving)))
    kinds = {v: ("station" if "SPS" in v else "outfall" if "STP" in v else "chamber")
             for v in ids}
    dep = dependencies(tree, pkg_of, roots, kinds, rm_ds=None)
    chain = dep.sort_values("comm_seq")[["comm_seq", "ds_root", "indep"]]
    print()
    print("commissioning order our partition derives (1 = build first):")
    print(chain.to_string())
    print(f"one outlet per package: {'YES' if not bad_outlet else bad_outlet}")
    print("NAMA's own chain, from DELIVERABLE_SPEC C.4, for comparison: "
          "5A-3 -> 5A-2 -> 5A-4 -> 5A-1 -> station -> force main -> STP, "
          "and 5A-5 -> STP direct.")
    print()
    print(f"{len(ours)} packages against NAMA's {len(nama)}; median "
          f"{ours['km'].median():.2f} km against their {nama['km'].median():.2f} km. "
          f"'purity_pct' is the share of each of our packages that falls inside ONE of "
          f"NAMA's - high means our seam sits where theirs does.")
    print("The size band was measured from this very network, so size agreement is not "
          "independent evidence.\nWhat is: the sweep terminated on a real 3,266-pipe tree, "
          "the dependency graph was acyclic,\nand every package above is one connected "
          "tree with exactly one outlet.")
    os.makedirs(RUN, exist_ok=True)
    ours.to_csv(os.path.join(RUN, "s8_calibration_vs_nama.csv"))
    print(f"\nwritten to {os.path.join(RUN, 's8_calibration_vs_nama.csv')}")
    return 0


# --------------------------------------------------------------------------------------
# Self-test. Proves the partition invariants on a tree small enough to check by hand.
# --------------------------------------------------------------------------------------

def _selftest() -> int:
    from shapely.geometry import LineString

    # A spine of 200 x 100 m reaches (20 km) with a 12 km branch joining at the middle and
    # a station two thirds of the way down. Hand-checkable: the branch plus the upper spine
    # must not end up in one 32 km package, and the station must be a seam whatever its
    # residual length.
    rows, x = [], 0.0
    def edge(u, d, ux, uy, dx, dy):
        rows.append(dict(EDGE_UID=f"E{len(rows):04d}", US_NODE=u, DS_NODE=d,
                         LEN_M=LineString([(ux, uy), (dx, dy)]).length,
                         geometry=LineString([(ux, uy), (dx, dy)])))

    for i in range(200):                       # spine N000 -> N200, 100 m each
        edge(f"N{i:03d}", f"N{i+1:03d}", i * 100.0, 0.0, (i + 1) * 100.0, 0.0)
    for i in range(120):                       # branch B000 -> B120 -> joins N100
        d = f"B{i+1:03d}" if i < 119 else "N100"
        dy = (i + 1) * 100.0 if i < 119 else 0.0
        edge(f"B{i:03d}", d, 10000.0, (i + 1) * -100.0 + 12000.0, 10000.0, 12000.0 - dy)
    reaches = gpd.GeoDataFrame(rows, geometry="geometry", crs=K.CRS_EPSG)
    ids = sorted(set(reaches.US_NODE) | set(reaches.DS_NODE))
    tree = Tree(reaches, ids)

    station = "N130"
    pkg_of, roots, _ = partition(tree, [station, "N200"])

    # 1. every node in exactly one package
    assert len(pkg_of) == len(ids), (len(pkg_of), len(ids))
    # 2. every package one connected tree with one outlet
    for r in roots:
        members = {v for v, p in pkg_of.items() if p == r}
        leaving = [v for v in members
                   if tree.parent(v) is None or tree.parent(v) not in members]
        assert len(leaving) == 1, (r, len(leaving))
        for v in members:                       # walking down stays inside until the root
            cur = v
            while cur != r:
                cur = tree.parent(cur)
                assert cur is not None and cur in members, (r, v)
    # 3. nothing exceeds the ceiling, and anything under the floor is a declared seam -
    #    the only sanctioned way to be under-band (P8: independence over tidiness)
    lens = {r: _pkg_len(tree, pkg_of, r) / 1000.0 for r in roots}
    assert max(lens.values()) <= BAND["PKG_LEN_MAX_KM"][0] + 1e-6, lens
    under = [r for r, v in lens.items() if v < BAND["PKG_LEN_MIN_KM"][0] - 1e-6]
    assert set(under) <= {station, "N200"}, under
    # 4. the station is a seam whatever its size - it must survive the merge pass
    assert station in roots, "a station must be cut as a package outlet (P8)"
    # 5. the 32 km of spine-plus-branch is not one package
    assert len(roots) >= 3, lens

    # 6. dependency order: downstream first, and an independent package waits for nobody
    kinds = {v: "chamber" for v in ids}
    kinds[station] = "station"
    kinds["N200"] = "outfall"
    dep = dependencies(tree, pkg_of, roots, kinds, rm_ds=None)
    for r in roots:
        d = dep.at[r, "ds_root"]
        if d and not dep.at[r, "indep"]:
            assert dep.at[r, "comm_seq"] > dep.at[d, "comm_seq"], (r, d)
    assert dep.at[station, "indep"] == 0, ("a station in mid-tree still drains onward; "
                                           "INDEP is for a package whose OUTLET terminates")

    # 7. the seam metric runs and is a percentage
    edge_pkg = reaches["US_NODE"].map(pkg_of)
    s = seam_share(reaches.assign(PACKAGE=edge_pkg))
    assert ((s >= 0) & (s <= 100)).all(), s

    # 7b. the whole publish path, on a temp GeoPackage - the packages layer has to pass
    #     contract.validate and print its schedule, or the deliverable does not exist. Only
    #     a temp directory is touched; nothing under W11a, W10 or W8 is written.
    import tempfile
    from shapely.geometry import Point as _P
    nodes_g = gpd.GeoDataFrame(
        {"NODE_UID": ids, "NODE_REF": ids, "TIER": "lateral",
         "NODE_KIND": [kinds.get(v, "chamber") for v in ids]},
        geometry=[_P(i, 0) for i, _ in enumerate(ids)], crs=K.CRS_EPSG)
    conns_g = pd.DataFrame({"PLOT_ID": [f"PL{i}" for i in range(len(ids))],
                            "OUT_NODE": ids, "N_PROP": 1.456, "Q_ADF_M3D": 1.08})
    layer, diag, name = build_packages(tree, pkg_of, roots, nodes_g, reaches, conns_g,
                                       None, None)
    assert set(layer.PACKAGE) == set(name.values())
    assert (layer.ONE_TREE == 1).all(), layer
    assert (diag.N_OUTLET == 1).all(), diag
    assert (diag.Q_DEV_M3D.isna()).all(), "no plot classes supplied -> phase must not guess"
    assert (diag.PHASE == 0).all(), "PHASE must stay unassigned with no developed-load data"
    with tempfile.TemporaryDirectory() as td:
        K.publish(layer, "packages", td, stage="selftest")
        K.mirror_shapefile(layer, "packages", td)
        sch = K.schedule_frame(layer, "packages", stage="selftest")
        assert "Commissioning order" in sch.columns and len(sch) == len(layer)
    acc = acceptance(diag)
    assert set(acc.loc[acc.check.isin(["F6", "F6b", "F7"]), "status"]) == {"pass"}, acc

    # 7c. stamping is keyed on the node, and a load unit with no chamber is named, not lost
    st = stamp(reaches, "US_NODE", pd.Series({v: name[r] for v, r in pkg_of.items()}),
               pd.Series({v: 1 for v in ids}), "reaches")
    assert (st.PACKAGE != "").all()
    orphan = conns_g.copy()
    orphan.loc[0, "OUT_NODE"] = ""
    st = stamp(orphan, "OUT_NODE", pd.Series({v: name[r] for v, r in pkg_of.items()}),
               pd.Series({v: 1 for v in ids}), "connections", unassigned_ok=True)
    assert (st.PACKAGE == "").sum() == 1
    try:
        stamp(orphan, "OUT_NODE", pd.Series({v: name[r] for v, r in pkg_of.items()}),
              pd.Series({v: 1 for v in ids}), "connections")
        raise AssertionError("an unpackaged row passed without unassigned_ok")
    except K.ContractError:
        pass

    # 8. a two-outgoing-edge node is refused, not silently kept
    bad = pd.concat([reaches, reaches.iloc[[0]].assign(EDGE_UID="EDUP", DS_NODE="N005")])
    try:
        Tree(bad, ids)
        raise AssertionError("a second outgoing reach was accepted")
    except K.ContractError as e:
        assert "forest" in str(e)

    # 9. phase refuses to guess without the build-out curve
    stats = pd.DataFrame({"Q_DEV_M3D": [10.0, 0.0], "Q_ULT_M3D": [10.0, 5.0],
                          "LEN_KM": [5.0, 5.0]}, index=["P01", "P02"])
    ph = assign_phase(stats)
    assert list(ph) == [1, 0], list(ph)
    ph = assign_phase(stats, {2030: 8.0, 2055: 20.0})
    assert set(ph) <= {1, 2}, list(ph)

    print(f"s8 self-test OK - {len(ids):,} nodes, {len(reaches):,} reaches, "
          f"{reaches.LEN_M.sum()/1000:.1f} km cut into {len(roots)} packages "
          + ", ".join(f"{v:.1f} km" for v in sorted(lens.values(), reverse=True))
          + f"; station seam held, {len(dep)} dependency rows acyclic.")
    return 0


def main(argv: Sequence[str]) -> int:
    if "--selftest" in argv:
        return _selftest()
    if "--calibrate" in argv:
        return calibrate()
    rc = run()
    # The calibration is shown only when the real run could not happen. Gate it on the
    # inputs, not on whether the GeoPackage file exists - it exists as soon as ANY stage
    # publishes into it, and gating on the file made this block vanish the moment stage 1
    # wrote its first layer while the layers stage 8 needs were still absent.
    if rc == 0 and load_inputs()[0] is None:
        print()
        print("-" * 86)
        print("Partitioner evidence, since the design graph does not exist yet: the same "
              "code run\nagainst NAMA's own built network.")
        print("-" * 86)
        calibrate()
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
