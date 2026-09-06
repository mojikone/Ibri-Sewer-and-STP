"""W12 stage 1 - THE ROAD NETWORK, read from the draftsman's CLEAN DXF.

W12 INHERITS W11b and revises it (user rule, 2026-09-06): a new W# copies the previous folder's code and edits it. Earlier folders are read as data and as lessons, never re-derived from scratch. Superseded folders stay untouched as the record.
only import from inside W12 is `w12.criteria`, which is W12's own.  Earlier folders are
read for DATA (`W10/shp/W10_plot_loads.gpkg`); copying data is fine, importing code is not.

WHAT CHANGED ON 2026-09-03, AND WHY THIS FILE WAS REWRITTEN
The previous build read the DWG through AutoCAD's headless console.  The engineer has now
supplied a DXF he has eyeballed and cleaned himself, and his instruction is explicit:

    "THE ROAD DXF IS CLEAN.  The draftsman has resolved the dual-carriageway problem, so ALL
     lines in the new DXF are usable for design.  Check the result and report if any line
     still looks like it runs along a dual carriageway, but do not apply a blanket
     exclusion."
    "NO CROSSINGS for now.  Do not manufacture wadi or road crossings."

So three things are different from every previous stage 1 in this project:

  1. The DXF is the INPUT.  No DWG, no accoreconsole, no cached intermediate.  One file, one
     hash, one read.
  2. NOTHING IS DELETED.  `corridors` is the whole drawing.  The dual-carriageway question
     is still MEASURED - in more detail than before, because a measurement that changes no
     geometry has to earn its keep by being decisive - and the answer is published as a
     FLAG and a costed review list, for the engineer to rule on.
  3. No crossing is manufactured.  Nothing is bridged over a wadi, nothing is invented to
     get past a carriageway, and no connection exists in the output that is not in his
     drawing (see NODING below for the one honest exception, X-junctions).

CONNECTIVITY IS THE JOB, AND THE HEADLINE IS MEASURED ON THE ROUTABLE LAYER
A judge found that the previous build reported 13 components on the raw road layer while the
ROUTABLE layer had 16, and that 359 km carrying 13 % of the load had no legal path to the
rest.  The headline had been measured on the wrong layer.  Two rules follow, and both are
enforced here rather than intended:

  * The published headline is the component count of `corridors`, RECOMPUTED FROM THE
    US_NODE / DS_NODE STRINGS THAT WERE WRITTEN TO DISK - never from geometry, never from an
    in-memory graph.  `verify()` re-reads the GeoPackage and recomputes it a third time; if
    that number disagrees with the manifest the stage fails and publishes nothing.
  * Every component that cannot reach the rest is NAMED in the `components` table with its
    length, its load, where it is, and how far it sits from the main component - so an
    island is a decision with a price on it, not a discovery someone makes in stage 4.

MEASURED ON THE 03/09/2026 DXF (sha1 45467150bb51aeac) - re-measured on every run; the
published tables are the authority, this text is a summary of them

    read              12,614 lines, 1,819.43 km, TWO layers, 2 degenerate entities dropped
    endpoint gaps     89.06 % of endpoints touch another line at EXACTLY 0.000 m,
                      92.52 % within 1 mm, 93.09 % within 3 m
    tolerance sweep   NO CLIFF.  The biggest single step anywhere in 1 mm - 10 m is
                      +0.13 pp, over 0.1-0.25 m.  Across that whole range the largest
                      component moves 97.75 % -> 98.80 % of the LENGTH - 19.1 km of
                      1,819 km - while the piece count falls 31 -> 10.  The count moves
                      because it is dominated by fragments of a few hundred metres; the
                      length, which is what a router cares about, barely moves.  Either way
                      the improvement is GRADUAL: no tolerance in the range buys an
                      outsized share, so there is no manufactured gap in this drawing.
    the contrast      W11a cut its corridors 4.0 m short and minted nodes at 3.0 m; nothing
                      closed the 1 m difference and 490 of 560 components were that ONE
                      defect, with a visible cliff at 3-4.5 m in exactly this curve.  The
                      draftsman's pass fixed it at source.  This file's job is to PROVE that
                      rather than assume it, which is why the sweep runs the FULL pipeline
                      at each tolerance instead of a proxy.
    noding            581 endpoints welded (max move 2.08 m), 108 hanging ends teed onto the
                      line they were drawn against (max 2.61 m), 25 `crosses` intersections
                      landing on 24 nodes - EVERY ONE of which is also a tee, i.e. an
                      overshoot, not an independent X-junction.  Zero cross-only nodes: this
                      stage adds no junction the draftsman did not draw as one.
    THE HEADLINE      12,665 corridors, 1,819.45 km, 13 COMPONENTS on the routable layer,
                      from its own written node ids.  The largest holds 1,788.57 km
                      (98.30 % of the length) and 98.98 % of the load.
    the islands       12 components, 30.87 km (1.70 %), 762.6 m3/d (1.02 % of the load).
                      Three of them sit within 10 m of the main component and six within
                      50 m - drafting gaps, not islands.  All 12 are named in `components`
                      with length, load, centroid and gap.
    dual carriageway  the tagged `dual = 1` set is 146.9 km, of which only 42.3 km is
                      status Existing (101.7 km Modified, 2.9 km New).  0.13 % of it lies
                      within 1 m of a drawn line, median distance 24.9 m: THE DRAFTSMAN DID
                      NOT DRAW THE CARRIAGEWAYS.  What survives inside the +/-6 m band is
                      1,051 m of 1,819 km; of that, 916.1 m in 22 lines runs ALONG a
                      carriageway.  12 of those / 84.8 m were published as CROSSINGS until
                      2026-09-06 by a length shortcut that never read their bearing.
    rule 7 applied    16 lines / 613.2 m EXCLUDED: PIPE_OK = 0, each with the reason, the
                      angle and the carriageway written on its own row.  6 lines / 302.9 m
                      RETAINED as an OPEN H1 BREACH, because each is the only drawn link to
                      what sits behind it.  The exclusion changes NO connectivity: 13
                      components before and after, off-main load 762.6 m3/d either way.
    the price of it   excluding all 22 would strand 329.6 km carrying 12,105 m3/d - 16.2 %
                      of the load - and 268.8 km of the pipe the run published.  One 23.1 m
                      line is the ONLY drawn link between the eastern town (285.9 km, 1,632
                      corridors over a 24 x 12 km area, 10,168 m3/d) and the rest; the gap
                      either side of it is the length of the line itself.  A 6.8 m line and
                      a 175.6 m line hold 43.5 km in the west the same way.
    what is left      0.0057 % of the routable length lies inside a 4 m buffer of a tagged
                      carriageway, against the as-built gate of <= 0.2 % there and the built
                      2006 network's own 0.0820 %.  THAT is the gate's quantity: NAMA's
                      network is measured the same way, overlap length with NO bearing test,
                      so a crossing counts on both sides.  Bearing-filtered, the ALONG share
                      is 0.0010 % at 4 m, 0.0167 % at 6 m and 0.1981 % at 10 m.  Until
                      2026-09-06 this line read "0.0000 % - ZERO corridors" at 4 m and
                      0.0433 % at 10 m, because the measurement charged whole lines and
                      refused to judge any line less than 99 % inside the band - true at the
                      6 m split width and at no other.  THE BUFFER IS PART OF THE NUMBER
                      (`dual_exposure`), and so is which of the two quantities is quoted.
    load reach        every plot allocated to its nearest corridor with no cap, so component
                      shares are shares of the whole 74,701 m3/d.  Plot-to-corridor distance
                      median 25.3 m, p90 54.1 m; 80.5 % of the load within 40 m and 99.4 %
                      within 300 m - a smooth decay with no cliff.

WHAT IS PUBLISHED
    roads         every drawn line, noded, nothing deleted
    corridors     the ROUTABLE set: the PIPE_OK = 1 rows of `roads`.  `verify()`
                  reconciles the two off the reloaded file - corridors must be EXACTLY those
                  rows, every excluded row must carry a reason, and no row may be excluded
                  that the measurement did not flag.  It stays a separate layer because
                  reaching for the wrong one is how a pipe ended up on a dual carriageway in
                  W10.
    nodes         node identity: NODE_ID -> point, with degree and how the node was made
    dual_review   every line the measurement says runs ALONG a tagged dual carriageway,
                  priced with what excluding it would strand and carrying its disposition
    dual_exclusion  the rule 7 decision, line by line: excluded or retained, with the angle,
                  the carriageway, the strand and the sentence behind it
    dual_exposure   the surviving routable layer's exposure at 4, 6 and 10 m, measured on the
                  IN-BAND RUN: ALONG_* is bearing-filtered (the H1 quantity), OVERLAP_* is
                  every metre inside the buffer with no bearing test (the quantity
                  `asbuilt.dual_overlap_m` states the <= 0.2 % gate in)
    twins         geometric dual-carriageway candidates the road file never tagged.
                  FLAGGED, NOT DELETED.
    boundary      the study boundary.  NOT in this DXF - see BOUNDARY below.
    layers        the DXF layer inventory: every layer, every entity type, what was done
    gaps          the endpoint-gap distribution, measured BEFORE any tolerance was chosen
    sweep         components against merge tolerance, full pipeline at each
    dual_band     exposure to a tagged dual carriageway against band half-width
    dual_status   what the tagged dual set IS, by record status - it holds proposals too
    dual_cover    how much of the tagged dual carriageway network the drawing represents
    load_reach    plot-to-corridor distance curve: how far the load sits from the drawing
    provenance    km by source and confidence
    components    EVERY component of the routable layer, named, with length, load, where
                  it is and its gap to the main component
    manifest      inputs, hashes, constants, assumptions, the tau flag, field meanings

BOUNDARY - READ THIS
The clean DXF carries NO boundary polygon.  The previous DWG had a `Project Boundary
updated` layer; this DXF has four layers and two of them are empty.  The boundary is
therefore read from a SEPARATE drawing, `DWG/Project Boundary.dxf`, and is labelled as such
in the `boundary` layer and the manifest.  It is published as EVIDENCE for the open
boundary decision (531.4 km2 here against 439.8 km2 in `MoHUP_DATA/Project_boundary.shp`),
never as the decision.  If the boundary drawing is missing the stage still completes and
says so; it is not an input this stage's arithmetic depends on.

NODING - THE ONE PLACE GEOMETRY IS ADDED, AND WHY IT IS NOT A MANUFACTURED CROSSING
Three operations, each reported separately, because `unary_union` tells you nothing about
what it changed:

  WELD   two line ENDS within SNAP_M are one node; both move to the cluster mean.
  TEE    a line END within SNAP_M of another line's INTERIOR is a T-junction: the end is
         MOVED onto the line AND the line is split there.  Both halves matter.  Splitting
         without moving leaves the end hanging up to SNAP_M away - a dangling end dressed up
         as a junction.  W11a had no tee step at all, which is exactly why its 4 m cuts
         against the middle of a line survived a 3 m endpoint merge.
  CROSS  two lines that intersect with no shared vertex are split at the intersection.

The CROSS split is the only place a node appears that the draftsman did not draw, and it is
not a manufactured crossing: the lines already touch in his drawing, and refusing to node
them would report a real junction as a disconnection.  It is counted, and every node it
creates carries `MADE_BY = 'cross'` so a later stage can check for a grade separation.  A
flyover drawn as two crossing centrelines would be noded here wrongly - the DXF carries no
elevation - so the count is published rather than buried.

DUAL CARRIAGEWAYS - MEASURED, AND SINCE 2026-09-06 ENFORCED AT THE CORRIDOR
Project rule 7 says no pipe of any kind runs ALONG a dual carriageway, trunk included,
because it cannot be dug up; a crossing is legal, running along one is not (engineer,
2026-08-19; H1, philosophy sec 3).  NAMA's own built network obeys it on 99.9 % of its
length (`criteria.BENCHMARKS['DUAL_SHARE_BUILT']`), and `_BRAIN/10_ASBUILT_CALIBRATION.md`
measures that as 0.0820 % running along, with a 4 m buffer, and sets the gate at <= 0.2 %
there.  THE BUFFER IS PART OF THE NUMBER and is published beside it.

WHAT CHANGED ON 2026-09-06.  Until then this stage measured the breach and left it in the
routable layer, and rule 7 lived in the schema (`PIPE_OK` was 1 on all 12,665 rows,
`EXCL_RSN` blank on all of them) instead of in the data.  Philosophy sec 2 stage 2 is
explicit that the exclusion belongs HERE, not in the router, so `corridors` is now the
PIPE_OK = 1 rows and a line that runs along a carriageway is out of it.  Two things had to
be true before that could be done honestly:

  1. THE MEASUREMENT WAS UNDER-REPORTING.  `tag_dual` called any in-band piece shorter than
     XING_CONTACT_MAX_M a crossing WITHOUT reading its bearing.  The argument behind that
     shortcut is sound only for a piece that actually TRAVERSES the band; a piece that
     clips the band edge has a short contact at ANY bearing.  It published 12 pieces /
     84.8 m as XING = 1 - a column whose field meaning says "measured, not assumed" - at
     bearings from 0.1 to 63.4 deg, the worst being 6.78 m at 0.1 deg whose offset to the
     carriageway varied by 0.16 m over its whole length.  The shortcut is gone; the
     measured bearing decides.  ALONG went 10 lines / 831.3 m -> 22 / 916.1 m.
  2. A BLANKET EXCLUSION WOULD HAVE SEVERED THE TOWN.  Excluding all 22 strands 329.62 km
     carrying 12,105 m3/d - 16.2 % of the project load - and 268.8 km of the pipe the run
     actually published.  Two of them are the reason: a 23.1 m piece is the ONLY drawn link
     between the eastern town (285.87 km, 1,632 corridors, a 24 x 12 km area) and the rest,
     and a 6.8 m piece is the only link to 43.50 km in the west.  The gap either side is
     the length of the piece itself.

So the rule is applied by what the GRAPH says, with no invented threshold: a flagged line
whose removal strands NOTHING is excluded; one whose removal strands anything at all is
RETAINED, marked H1_KEEP = 1 and published in `dual_exclusion` with the km and the load it
holds.  Concept rule "flag, do not solve" (philosophy sec 9): what cannot be resolved at
concept is named with its reason and its size, NEVER DROPPED.  A retained line is an OPEN H1
BREACH, not a pass - the fix is a designed carriageway crossing, and that is switched off by
the standing instruction of 2026-09-03 ("no crossings for now").  It needs the engineer.

What is measured, and published:

  * how much of the tagged dual-carriageway network (`dual = 1` in `SHP/Road centerline 2`,
    146.9 km) the drawing represents at all - sampled along the tagged centrelines
  * the drawing's exposure inside a band around those centrelines, at eight band widths, so
    the answer's sensitivity to the one assumed number is visible
  * every in-band run classified ALONG / ACROSS / GRAZE on MEASURED BEARING ONLY.  There is
    no length shortcut in front of the bearing: one used to sit there and it published 12
    pieces / 84.8 m as square crossings at 0.1 to 63.4 degrees (see XING_CONTACT_MAX_M).
  * for every ALONG run, WHAT EXCLUDING IT WOULD COST: the km and the load it would strand.
    That is the number the decision actually turns on - it is priced BEFORE it is applied,
    and it is what decides exclusion against retention.
  * the surviving routable layer re-measured from the geometry at 4, 6 and 10 m buffers
    (`dual_exposure`), never read back off the ALONG_DUAL column, so the published number is
    an independent check on the exclusion and not a restatement of it.  Measured ON THE
    IN-BAND RUN at every width: charging the whole line and skipping any line under 99 %
    in-band is right only at the 6 m split width, and it was pinning the 4 m answer at zero.
    Two quantities, because the calibration gate uses one and H1 uses the other: OVERLAP_*
    is every metre inside the buffer (the gate's, no bearing test) and ALONG_* is
    bearing-filtered (H1's).
  * a geometric scan for carriageways the road file never tagged, with the discriminator
    published beside each candidate (the share of the strip between the pair occupied by
    cadastral plots: a median holds none, a street grid holds plots)

NO NUMBER IS INVENTED
Every constant carries one of four tags:
    [G203-p##]  read from PAM-GUD-203 (or G201/G202) at that page
    [ASSUME]    no guideline value exists; a project decision, stated and reported
    [MEASURED]  measured from project data in this run; a fact, never a limit
    [DERIVED]   arithmetic on the two above, with the arithmetic shown
Two citation errors caught on 2026-09-02 are NOT repeated: G201-p86 is a VALVE-CHAMBER
clause on a force main and is authority for nothing on a gravity network, and G203-p52's
1.5 m cover is the FORCE-MAIN figure.  Neither is cited here.

TAU FLAG (engineer's decision 2026-09-03)
tau = 1.0 Pa is KEPT and FLAGGED ON EVERY OUTPUT.  This stage runs no hydraulics, so tau
does not enter its arithmetic - but every published feature carries a `TAU_PA` column and
the manifest carries the sensitivity, because the corridors published here are the ground
those gradients get laid along.  If NWS return 2.0 Pa, every tractive-governed gradient
steepens by 2^1.23 = 2.346x and every depth downstream changes.

THE API OTHER STAGES CALL
    from s1_roads import load, components_of, ROADS_GPKG, LAYERS
    d   = load()                     # dict of GeoDataFrames, one per layer
    cor = load("corridors")          # the routable set only
    comp, rep = components_of(cor)   # components FROM THE WRITTEN NODE IDS
Field meanings are in FIELDS below and are written into `manifest`, so a reader who has
never seen this file can resolve every column from the GeoPackage alone.

US_NODE / DS_NODE - READ THIS BEFORE USING THEM
They are WRITTEN DOWN, never inferred from geometry later; that is the whole point of the
node layer, and `components_of()` exists so no downstream stage ever has to re-derive
topology from coordinates.  At THIS stage they are the START and END of the drawn line and
carry NO hydraulic meaning - there is no flow direction until the terrain stage sets one.
A stage that reverses a corridor MUST rewrite both fields.

Run:  python s1_roads.py             build and publish
      python s1_roads.py --report    re-print the measured tables from the published file
      python s1_roads.py --verify    re-run every check against the published file
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

# --------------------------------------------------------------------------------------
# PATHS
# --------------------------------------------------------------------------------------

HERE = Path(__file__).resolve()
W12 = HERE.parent.parent                    # .../Hydraulic/Claude/W12
CLAUDE = W12.parent                         # .../Hydraulic/Claude
HYDRAULIC = CLAUDE.parent                    # .../Hydraulic
PROJECT = HYDRAULIC.parent                   # .../2621 Ibri Sewer STP

sys.path.insert(0, str(W12 / "py"))

# INPUTS -------------------------------------------------------------------------------
# THE road input.  The engineer's cleaned DXF, 03/09/2026.  It supersedes the DWG, the
# earlier `road network 03092026.dxf`, `SHP/Road centerline 2` as geometry, and every road
# source used in W1-W11a.  Read directly: no conversion, no cache, no intermediate.
ROAD_DXF = HYDRAULIC / "DWG" / "road network 03092026 eyeballed.dxf"

# The study boundary.  NOT in the road DXF - a separate drawing, published as evidence.
BOUNDARY_DXF = HYDRAULIC / "DWG" / "Project Boundary.dxf"

# The recorded centreline layer.  Used for TWO things only and NEVER as geometry:
#   (a) the `dual` column - the only place a dual carriageway is tagged in this project
#   (b) corroboration - "is there an independently recorded road under this drawn line"
ROAD_REC = HYDRAULIC / "SHP" / "Road centerline 2" / "Road_Centercline.shp"

# Cadastral plots with their computed load.  DATA, not code.  Used to grade confidence and
# to measure which component a load sits on.
PLOT_LOADS = CLAUDE / "W10" / "shp" / "W10_plot_loads.gpkg"
PLOT_LOADS_LAYER = "plot_loads"

# OUTPUT -------------------------------------------------------------------------------
ROADS_GPKG = W12 / "shp" / "W12_roads.gpkg"

CRS = "EPSG:32640"

# --------------------------------------------------------------------------------------
# CONSTANTS - every one tagged [G203-p##] / [ASSUME] / [MEASURED] / [DERIVED]
# --------------------------------------------------------------------------------------

STAGE_VERSION = "W12-s1_roads-2.0-dxf"

# ---- the DXF layers -------------------------------------------------------------------
# Read from the file on 2026-09-03 and listed here so a layer the draftsman adds later
# cannot be picked up silently.  `read_dxf` RAISES on an unknown layer carrying geometry
# and on an unknown entity type on a road layer - it never drops geometry quietly.
LAYER_BASE = "piping center line"           # 6,419 entities - his line on the base road set
LAYER_PROPO = "piping center line-propo-01"  # 6,195 entities - his own proposed streets
ROAD_LAYERS = (LAYER_BASE, LAYER_PROPO)

# Layers that exist in the drawing and carry no geometry.  Listed, not guessed: if one of
# them ever carries geometry, `read_dxf` raises rather than ignoring it.
EMPTY_LAYERS = ("0", "Defpoints")

# The boundary layer name, kept so that if the draftsman puts the boundary back into the
# road drawing it is picked up instead of the separate file.
LAYER_BOUNDARY = "Project Boundary updated"

# The layer `piping center line-tobe conferm` that existed in the DWG is ABSENT from this
# DXF.  The draftsman has resolved his own "to be confirmed" set.  Nothing in this file
# caps confidence by layer name any more - CONFIDENCE is graded purely on evidence.

READABLE_TYPES = ("LWPOLYLINE", "LINE", "POLYLINE")

# ---- node identity --------------------------------------------------------------------
# SNAP_M is the ONE tolerance here that changes the published topology, so it is not chosen
# by eye.  It is `criteria.MH_SNAP_M` = 3.0 m and the argument is the criteria module's own:
# G203-p33 requires 3 m of horizontal clearance between a sewer and another utility, so two
# chamber positions closer than that cannot be two chambers, and two line ends closer than
# that are one node.  What the choice costs and buys is published in `sweep` - measured, on
# this drawing, with the full pipeline, before the choice is used.

# ---- dual carriageway measurement (NOTHING IS DELETED) --------------------------------
DUAL_BAND_M = 6.0
# [ASSUME] half-width of the band around a tagged dual-carriageway centreline inside which a
# drawn line is judged against that carriageway.  Grounded on measurement, not precedent:
# the two carriageways of the tagged duals sit a MEASURED median ~14 m apart, so +/-6 m on
# each centreline spans essentially the whole reserve between them.  No guideline states a
# highway reserve width; when NWS or the Municipality supply one, this is the number to
# replace.  Exposure is published at 3, 5, 6, 7.5, 10, 12, 15 and 20 m in `dual_band`, so
# the sensitivity of every dual statement to this one number is visible.

DUAL_XING_SKEW_DEG = 25.0
# [ASSUME] the tolerance on the word "square" in "a short square crossing is allowed".  Set
# equal to `criteria.WADI_XING_SKEW_DEG`, deliberately: one project, one meaning for the
# word.  A run inside the band whose bearing is within 25 deg of perpendicular to the
# carriageway crosses it; anything else runs along it.

XING_CONTACT_MAX_M = 2.0 * DUAL_BAND_M / math.sin(math.radians(90.0 - DUAL_XING_SKEW_DEG))
# [DERIVED] 13.24 m.  A straight line crossing a band of width 2 x DUAL_BAND_M at angle
# theta to the band axis has an in-band contact of width / sin(theta).
#
# RETRACTED 2026-09-06 AS A CLASSIFIER.  The inversion this constant was used for - "an
# in-band contact no longer than this IS a crossing at at least (90 - skew) degrees, by
# geometry, with no bearing to measure" - is only valid for a piece that TRAVERSES the band.
# A piece that clips the band edge, or that ends inside it, has a short contact at ANY
# bearing, so the implication runs one way only and it was applied in the other.  On the
# 03/09 drawing it published 12 pieces / 84.8 m as XING = 1 at bearings of 0.1 to 63.4 deg -
# the worst 6.78 m at 0.1 deg, i.e. exactly parallel, whose offset to the carriageway varied
# 0.16 m over its whole length.  `tag_dual` now decides on the measured bearing and nothing
# else; this constant survives only as a published diagnostic on the manifest.

IN_BAND_MIN_FRAC = 0.99
# [ASSUME] the share of a line that must lie inside the band before the line is judged
# against the carriageway at all.  Lines are split where they enter and leave the band, so a
# real in-band piece scores 1.0; anything well below that is the OUTSIDE piece still
# touching the band edge at the split point - a contact of centimetres with no measurable
# bearing.  Grazes are COUNTED and reported, never silently ignored.

DUAL_COVER_STEP_M = 25.0
# [ASSUME] sampling step along the tagged dual centrelines when measuring how much of the
# tagged network the drawing represents.  25 m over 146.9 km is ~5,900 samples, which
# resolves the shortest tagged carriageway many times over.

DUAL_COVER_TOLS = (1.0, 2.0, 5.0, 10.0, 15.0, 20.0, 30.0, 50.0)
# [ASSUME] the distances at which that representation is reported.  A range, not a
# threshold: the question "has the draftsman drawn this carriageway" has no single right
# radius, so the whole curve is published.

# ---- geometric twin scan (carriageways the road file never tagged) --------------------
TWIN_SEP_MIN_M = 8.0
TWIN_SEP_MAX_M = 22.0
# [MEASURED] the separation window a dual carriageway occupies in this town, taken from the
# tagged duals themselves and from the drawing's own parallel-neighbour histogram, whose
# mode is the 24-30 m block street grid.  The window is the GAP between the two populations,
# not a guess.  Both numbers are re-measured every run and published in `manifest`.
TWIN_PARALLEL_DEG = 15.0    # [ASSUME] "near-parallel"
TWIN_MIN_LEN_M = 100.0      # [ASSUME] shorter than this, a parallel run is a corner
TWIN_MIN_COVER = 0.60       # [ASSUME] share of the line that must hold a partner
TWIN_STEP_M = 10.0          # [ASSUME] sampling step; 10 m resolves a 100 m line ten times
TWIN_EMPTY_PLOT_PCT = 5.0
# [ASSUME] a strip between two candidate carriageways holding less than this share of
# cadastral plot area is a MEDIAN, not a block.  Above it the pair is two ordinary streets
# with plots between them, which are legitimate routes.  Published per candidate so the
# threshold can be moved by eye rather than argued about.

# ---- provenance -----------------------------------------------------------------------
CORROB_M = 5.0
# [ASSUME] how close an independently recorded centreline must be for a drawn line to count
# as corroborated.  The measured curve is a smooth decay with no knee, so no distance is
# "the" answer and 5.0 m is a stated choice.  `D_REC_M` is published per line, so a reader
# who prefers 2 m or 10 m re-grades the whole layer with one query.

FRONTAGE_M = 40.0
# [ASSUME] a plot fronts a line this close.  No guideline gives a frontage distance.  The
# choice is bounded by the drawing's own geometry: the block street grid has a MEASURED mode
# at 24-30 m, so 40 m reaches across a street and into the plot row behind it without
# reaching the next street.  Sensitivity at 30 / 40 / 60 m is published in `manifest`.
#
# IT IS A LABELLING CUT, NOT A COVERAGE TEST, and the difference matters.  The measured
# plot-to-nearest-corridor curve is a SMOOTH decay with no cliff - median 25.3 m, p90 54.1 m,
# and 99.4 % of the load inside 300 m - so a 40 m cut leaves ~19 % of the load "outside" and
# that number says nothing about whether the drawing covers the town.  It does.  The whole
# curve is published in `load_reach` precisely so nobody reads the 19 % as a hole.

LOAD_REACH_M = (10.0, 20.0, 25.0, 30.0, 40.0, 50.0, 60.0, 80.0, 100.0, 150.0, 200.0,
                300.0, 500.0, 1000.0, 2000.0)
# [ASSUME] the distances at which plot-to-corridor reach is reported.  A curve, not a
# threshold: the honest answer to "does this drawing reach the load" is the shape of the
# decay, and any single radius quoted from it is a choice somebody made.

CONFIDENCE_ORDER = ("corroborated", "drafted", "provisional")
#   corroborated  an independently recorded centreline within CORROB_M, OR a plot with
#                 COUNTED electricity accounts fronting it.  Something is on the ground.
#   drafted       a load-bearing plot fronts it, but that plot's properties came from the
#                 average rate rather than from counted accounts - a platted street.
#   provisional   neither.  A reserve on bare ground.  Philosophy sec 4: such a corridor is
#                 never reported as existing.
# Graded by EVIDENCE, never by layer name.  Every input to the grade is published as its own
# field (D_REC_M, N_PLOT, N_BUILT, Q_M3D) so the grade can be argued with.

SRC_OF_LAYER = {
    LAYER_BASE: "draft_base",
    LAYER_PROPO: "draft_propo",
}

# ---- writing tolerance ----------------------------------------------------------------
ENDPOINT_TOL_M = 0.001
# [ASSUME] the published geometry must agree with the published US_NODE/DS_NODE to 1 mm.
# A WRITING tolerance, not a design one - four orders of magnitude below the 3 m that
# decides topology.  It proves the node table and the geometry were written from the same
# numbers.  W10 shipped a layer in 7,919 pieces because its generated links were born
# exactly 1.000 m off the lines they were meant to touch, and nothing ever checked.

GAP_TOLS = (0.0, 0.001, 0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5,
            4.0, 4.5, 5.0, 6.0, 8.0, 10.0, 15.0, 20.0, 30.0, 50.0)
SWEEP_TOLS = (0.0, 0.001, 0.01, 0.1, 0.5, 1.0, 2.0, 3.0, 4.0, 4.5, 5.0, 10.0)
STEP_WINDOW = (0.001, 10.0)
# [ASSUME] the range a snapping tolerance could plausibly be chosen from, and therefore the
# only range in which a "step" in the gap curve means a manufactured gap.  Beyond 10 m the
# curve is the network genuinely reaching the next settlement; calling that a step would be
# noise.  W11a's real signature sat at 3-4.5 m, squarely inside this window.

FIELDS: Dict[str, str] = {
    "CID": "corridor id, stable: the draftsman's own DXF entity handle plus the piece index "
           "along it. Traces every published line back to one object in his drawing",
    "DXF_H": "the DXF entity handle in the source drawing",
    "LAYER": "the DXF layer, verbatim",
    "SRC": "provenance: draft_base | draft_propo",
    "CONFIDENCE": "corroborated | drafted | provisional - graded by the evidence in "
                  "D_REC_M / N_BUILT / N_PLOT, never by layer name",
    "US_NODE": "node id at the START of the drawn line. WRITTEN DOWN, never inferred. NO "
               "hydraulic meaning at stage 1 - there is no flow direction until terrain",
    "DS_NODE": "node id at the END of the drawn line. Same rules as US_NODE",
    "LEN_M": "length, m",
    "COMP": "connected-component id of the ROUTABLE layer, recomputed from the written "
            "US_NODE/DS_NODE strings. 0 = the largest component",
    "ON_MAIN": "1 this line is in the largest component, 0 it is on an island that cannot "
               "reach the rest without a decision",
    "DEG_US": "degree of US_NODE - 1 dangling, 2 a joint, 3+ a junction",
    "DEG_DS": "degree of DS_NODE",
    "DUAL": "0 none | 1 inside the band of a tagged dual carriageway | 2 a tagged "
            "one-side-used pair | 9 an untagged geometric twin candidate",
    "ALONG_DUAL": "1 the measurement says this line runs ALONG a tagged dual carriageway. "
                  "FLAG ONLY - nothing is deleted. See the `dual_review` layer for what "
                  "excluding it would cost",
    "XING": "1 this line crosses a tagged dual carriageway squarely - measured, not assumed",
    "DUAL_ANG": "measured angle between this line and the carriageway beneath it, deg. "
                "0 = parallel, 90 = square. -1 where not inside a band",
    "PIPE_OK": "1 a pipe may be laid ALONG this line, 0 it is excluded. `corridors` IS "
               "the rows with PIPE_OK = 1, so a 0 here is the exclusion - philosophy sec 2 "
               "stage 2 puts it at the corridor and not in the router. Until 2026-09-06 it "
               "was 1 on all 12,665 rows and project rule 7 lived in this schema instead of "
               "in the data",
    "EXCL_RSN": "why PIPE_OK is 0: the rule, the measured angle, the length and the "
                "carriageway. Blank where PIPE_OK is 1",
    "H1_KEEP": "1 this line runs ALONG a tagged dual carriageway and was RETAINED ANYWAY, "
               "because it is the only drawn link to what sits behind it and excluding it "
               "would sever that. It is an OPEN H1 BREACH carrying its price in "
               "`dual_exclusion`, not an oversight and not a pass. Concept rule 'flag, do "
               "not solve': named and sized, never dropped. The fix is a designed "
               "carriageway crossing",
    "BUFFER_M": "dual_exposure: the buffer half-width every number on the row was measured "
                "at. The calibration document orders the buffer published WITH the number "
                "because the answer moves with it",
    "ALONG_N": "dual_exposure: in-band RUNS running ALONG the carriageway at this buffer - "
               "runs, not lines. A line is cut at the 6 m band and at nothing else, so at "
               "any other buffer only part of it is inside and only that part is counted",
    "ALONG_M": "dual_exposure: the length of those runs. THE H1 QUANTITY - bearing filtered",
    "ALONG_PCT": "dual_exposure: ALONG_M over the routable length. Do NOT quote it against "
                 "the as-built 0.0820 % or the <= 0.2 % gate; those are OVERLAP_PCT",
    "XING_N": "dual_exposure: in-band runs crossing within DUAL_XING_SKEW_DEG of square",
    "XING_M": "dual_exposure: and their length. Legal under rule 7 - a crossing is allowed",
    "OVERLAP_M": "dual_exposure: EVERY metre of the routable layer inside the buffer, with "
                 "NO bearing test, so a crossing counts. This is what "
                 "`asbuilt.dual_overlap_m` measures NAMA's built network with",
    "OVERLAP_PCT": "dual_exposure: OVERLAP_M over the routable length. THE CALIBRATION "
                   "GATE'S QUANTITY: _BRAIN/10_ASBUILT_CALIBRATION.md puts the built 2006 "
                   "network at 0.0820 % and the gate at <= 0.2 %, both at a 4 m buffer",
    "GRAZE_N": "dual_exposure: in-band runs shorter than the writing tolerance - the band "
               "edge touching a split point, not geometry. Counted, never silently ignored",
    "GRAZE_M": "dual_exposure: and their length, which is microns",
    "DISPOSITION": "dual_review / dual_exclusion: `excluded` (PIPE_OK set to 0, strands "
                   "nothing) or `retained` (H1_KEEP = 1, an open breach with a price)",
    "REASON": "dual_exclusion: the full sentence behind the disposition, so the row is "
              "readable without this file",
    "D_REC_M": "distance from this line's midpoint to the nearest recorded road centreline",
    "N_PLOT": "load-bearing plots whose representative point is within FRONTAGE_M",
    "N_BUILT": "of those, plots whose properties were COUNTED from electricity accounts",
    "Q_M3D": "saturation ADWF of the plots fronting this line, m3/d. NOT an allocation - a "
             "plot is counted for every line it fronts, so this column DOUBLE COUNTS. Use "
             "it for relevance, never for a total",
    "Q_NEAR_M3D": "saturation ADWF of the plots whose NEAREST corridor is this one, m3/d, "
                  "with NO distance cap. Each plot counted once, so the column sums to the "
                  "project total and a component share is a share of the WHOLE load. This "
                  "is what the component table is built from. Still a measurement, not a "
                  "design allocation - load allocation is a later stage. How far the load "
                  "actually sits from the drawing is in the `load_reach` table",
    "TWIN_SEP": "median separation to a near-parallel partner, m; -1 if none",
    "TWIN_COV": "share of the line's length holding that partner; -1 if none",
    "TWIN_PLOT": "share of the strip between the pair occupied by cadastral plots, %; below "
                 "TWIN_EMPTY_PLOT_PCT the strip is a median, not a block",
    "DUAL_ROAD": "dual_review: the tagged carriageway this line sits beside, by name",
    "DUAL_CAT": "dual_review: that carriageway's Category in the recorded centrelines",
    "DUAL_STATUS": "dual_review: that record's STATUS - Existing, Modified or New. An "
                   "asset GIS holds proposals too, and rule 7 is an argument about a BUILT "
                   "carriageway. Read this before acting on the flag",
    "DUAL_REC_M": "dual_review: the length of that recorded carriageway record, m. A 107 m "
                  "unnamed record is weaker evidence than a 1,875 m named highway",
    "STRANDS_KM": "dual_review: km that would lose its only path to the main component if "
                  "this line were excluded",
    "STRANDS_Q_M3D": "dual_review: the load on that stranded length, m3/d",
    "TAU_PA": "the design tractive stress carried on every output by the engineer's "
              "instruction of 2026-09-03. No hydraulics in this stage; the flag exists "
              "because these corridors are the ground those gradients get laid along",
    "NODE_ID": "node id (nodes layer)",
    "DEGREE": "how many corridors meet here (nodes layer)",
    "MADE_BY": "how the node came to exist: drawn (a line end in the DXF) | tee (a line end "
               "moved onto another line's interior) | cross (two lines intersecting with no "
               "shared vertex) | band (a split where a line enters or leaves a dual band). "
               "A node made by more than one operation carries them joined, e.g. "
               "'cross+tee' - which is the common case here, and is the evidence that the "
               "crossings are overshoots rather than independent X-junctions",
    "X": "easting (nodes layer)",
    "Y": "northing (nodes layer)",
}

LAYERS = ("roads", "corridors", "nodes", "dual_review", "dual_exclusion", "twins",
          "boundary", "layers", "gaps", "sweep", "dual_exposure",
          "dual_band", "dual_status", "dual_cover",
          "provenance", "load_reach", "components", "manifest")


# --------------------------------------------------------------------------------------
# ERRORS
# --------------------------------------------------------------------------------------

class RoadStageError(Exception):
    """Raised when an input is missing, a layer is unknown, or a published claim fails its
    own check.  It never returns a default: a silent default is how a stage ships a number
    nobody derived."""


def _sha1(path: Path) -> str:
    h = hashlib.sha1()
    with open(path, "rb") as f:
        while True:
            b = f.read(1 << 20)
            if not b:
                break
            h.update(b)
    return h.hexdigest()[:16]


def _mtime(path: Path) -> str:
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(path.stat().st_mtime))


# --------------------------------------------------------------------------------------
# STEP 1 - READ THE DXF
# --------------------------------------------------------------------------------------

def read_dxf(dxf: Path = ROAD_DXF) -> Tuple[List, List[str], List[str], object, pd.DataFrame,
                                            Dict]:
    """Read every road line, its layer and its DXF handle, and inventory the whole drawing.

    Returns (lines, layers, handles, boundary_or_None, layer_inventory, report).

    Nothing is simplified, re-aligned or re-drawn.  The draftsman's geometry is his work and
    is reused as delivered.  The only edits:
      * consecutive duplicate vertices are dropped - a repeated vertex is a zero-length
        segment and it makes every later length and bearing undefined
      * an entity with fewer than two distinct vertices after that is dropped and COUNTED

    It RAISES on an unknown layer carrying geometry, and on an unrecognised entity type on a
    road layer.  A drawing this module has not been told how to grade is not graded by
    guesswork, and geometry is never dropped silently.  The layer inventory is published as
    a table, so "which layers did you find and what did you do with each" is answered by the
    GeoPackage rather than by a console log nobody kept.
    """
    import ezdxf
    from shapely.geometry import LineString, Polygon

    doc = ezdxf.readfile(str(dxf))
    msp = doc.modelspace()

    lines: List = []
    layers: List[str] = []
    handles: List[str] = []
    boundary = None
    inv: Dict[Tuple[str, str], Dict] = {}
    rep = {"dxf_version": doc.dxfversion, "acad_release": doc.acad_release,
           "degenerate_dropped": 0, "declared_layers": [l.dxf.name for l in doc.layers]}
    unknown: Counter = Counter()

    def _row(lay, typ, decision, length=0.0):
        k = (lay, typ)
        d = inv.setdefault(k, {"LAYER": lay, "ENTITY": typ, "N": 0, "KM": 0.0,
                               "DECISION": decision})
        d["N"] += 1
        d["KM"] += length / 1000.0
        d["DECISION"] = decision

    def _points(e, typ):
        if typ == "LWPOLYLINE":
            return [(x, y) for x, y in e.get_points("xy")]
        if typ == "POLYLINE":
            return [(v.dxf.location.x, v.dxf.location.y) for v in e.vertices]
        return [(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)]

    for e in msp:
        lay = e.dxf.layer
        typ = e.dxftype()

        if lay == LAYER_BOUNDARY:
            if typ in ("LWPOLYLINE", "POLYLINE"):
                boundary = Polygon(_points(e, typ))
                _row(lay, typ, "study boundary polygon -> `boundary` layer")
            else:
                _row(lay, typ, "on the boundary layer but not a polyline -> ignored")
            continue

        if lay in ROAD_LAYERS:
            if typ not in READABLE_TYPES:
                unknown[f"{lay}|{typ}"] += 1
                continue
            pts = _points(e, typ)
            clean = [pts[0]] if pts else []
            for p in pts[1:]:
                if abs(p[0] - clean[-1][0]) > 1e-9 or abs(p[1] - clean[-1][1]) > 1e-9:
                    clean.append(p)
            if len(clean) < 2:
                rep["degenerate_dropped"] += 1
                _row(lay, typ, "DEGENERATE - fewer than two distinct vertices, dropped")
                continue
            g = LineString(clean)
            lines.append(g)
            layers.append(lay)
            handles.append(e.dxf.handle)
            _row(lay, typ, f"ROAD GEOMETRY -> `roads` and `corridors` "
                           f"(SRC = {SRC_OF_LAYER[lay]})", g.length)
            continue

        if lay in EMPTY_LAYERS:
            # declared in the layer table but expected to hold nothing.  If it holds
            # geometry that is a change in the drawing and it is raised, not ignored.
            unknown[f"{lay}|{typ}"] += 1
            continue

        unknown[f"{lay}|{typ}"] += 1

    if unknown:
        raise RoadStageError(
            "the drawing holds geometry this module has not been told how to grade:\n  "
            + "\n  ".join(f"{k}: {v}" for k, v in unknown.items())
            + "\nAdd the layer to ROAD_LAYERS with a SRC, or add the entity type to "
              "READABLE_TYPES, or say in EMPTY_LAYERS why it is ignored. Nothing is "
              "dropped silently.")
    if not lines:
        raise RoadStageError(f"no road geometry read from {dxf}")

    # every DECLARED layer gets a row, including the ones that hold nothing, so the
    # inventory answers "what layers are in this drawing" and not only "what did you read"
    seen = {lay for lay, _ in inv}
    for lay in rep["declared_layers"]:
        if lay not in seen:
            inv[(lay, "-")] = {"LAYER": lay, "ENTITY": "-", "N": 0, "KM": 0.0,
                               "DECISION": "declared in the layer table, holds no geometry "
                                           "-> nothing to do"}
    tab = pd.DataFrame(sorted(inv.values(), key=lambda d: (d["LAYER"], d["ENTITY"])))
    tab["KM"] = tab["KM"].round(3)
    return lines, layers, handles, boundary, tab, rep


def read_boundary(dxf: Path = BOUNDARY_DXF):
    """The study boundary, from the SEPARATE boundary drawing.

    The clean road DXF carries no boundary.  This is read so the boundary can still be
    published as EVIDENCE for the open 531.4 / 439.8 km2 decision, and it is labelled with
    its own source.  A missing file is reported, not fatal: no arithmetic in this stage
    depends on it.
    """
    from shapely.geometry import Polygon
    if not dxf.exists():
        return None, {"source": str(dxf), "found": False}
    import ezdxf
    doc = ezdxf.readfile(str(dxf))
    for e in doc.modelspace():
        if e.dxftype() == "LWPOLYLINE":
            p = Polygon([(x, y) for x, y in e.get_points("xy")])
            return p, {"source": str(dxf), "found": True, "layer": e.dxf.layer,
                       "area_km2": round(p.area / 1e6, 3), "sha1": _sha1(dxf),
                       "modified": _mtime(dxf)}
    return None, {"source": str(dxf), "found": False}


# --------------------------------------------------------------------------------------
# STEP 2 - MEASURE THE GAPS, BEFORE CHOOSING ANY TOLERANCE
# --------------------------------------------------------------------------------------

def measure_gaps(lines: Sequence) -> Tuple[pd.DataFrame, Dict]:
    """The endpoint-gap distribution, measured BEFORE any tolerance is chosen.

    Two distances per endpoint, because they catch different defects:
      d_line  to the nearest point on ANY other line.  This is the one that would have
              caught W11a: a corridor cut 4 m short against another line leaves an endpoint
              4 m from that line's INTERIOR, and no end-to-end merge can ever close it.
      d_end   to the nearest ENDPOINT of another line.  End-to-end gaps only.

    A STEP in either curve is a manufactured gap and it names its own tolerance.  A flat
    curve means the drawing is honest and the tolerance hardly matters.  The step is looked
    for only inside STEP_WINDOW; beyond it the curve is the network genuinely reaching the
    next settlement.
    """
    from shapely.geometry import Point
    from shapely.strtree import STRtree
    from scipy.spatial import cKDTree

    ep, own = [], []
    for i, l in enumerate(lines):
        c = list(l.coords)
        ep.append(c[0]); own.append(i)
        ep.append(c[-1]); own.append(i)
    ep = np.asarray(ep, float)
    own = np.asarray(own)
    pts = [Point(p) for p in ep]

    # endpoint -> nearest OTHER line.  Counted directly at each threshold with a vectorised
    # `dwithin`: the table wants cumulative counts, not distances, and asking the index the
    # question the table asks is both exact and fast.
    tree = STRtree(list(lines))
    n_line = []
    for t in GAP_TOLS:
        qi, qj = tree.query(pts, predicate="dwithin", distance=max(t, 0.0))
        hit = np.zeros(len(ep), bool)
        m = own[qi] != qj
        hit[qi[m]] = True
        n_line.append(int(hit.sum()))

    # endpoint -> nearest OTHER endpoint
    kd = cKDTree(ep)
    k = min(16, len(ep))
    dk, jk = kd.query(ep, k=k)
    d_end = np.full(len(ep), np.inf)
    for r in range(len(ep)):
        for m in range(dk.shape[1]):
            if own[jk[r, m]] != own[r]:
                d_end[r] = dk[r, m]
                break

    rows = [{"TOL_M": t,
             "N_EP_TO_LINE": n_line[i],
             "PCT_EP_TO_LINE": round(100.0 * n_line[i] / len(ep), 2),
             "N_EP_TO_EP": int((d_end <= t).sum()),
             "PCT_EP_TO_EP": round(100.0 * float((d_end <= t).mean()), 2)}
            for i, t in enumerate(GAP_TOLS)]
    df = pd.DataFrame(rows)

    win = df[(df.TOL_M >= STEP_WINDOW[0]) & (df.TOL_M <= STEP_WINDOW[1])].reset_index(drop=True)
    jumps = np.diff(win["PCT_EP_TO_LINE"].values)
    worst = int(np.argmax(jumps)) if len(jumps) else 0
    tols_w = tuple(win.TOL_M.values)
    rep = {"n_endpoints": int(len(ep)),
           "exact_touch_pct": df.loc[df.TOL_M == 0.0, "PCT_EP_TO_LINE"].iloc[0],
           "mm_touch_pct": df.loc[df.TOL_M == 0.001, "PCT_EP_TO_LINE"].iloc[0],
           "three_m_pct": df.loc[df.TOL_M == 3.0, "PCT_EP_TO_LINE"].iloc[0],
           "biggest_step_band": f"{tols_w[worst]:g}-{tols_w[worst + 1]:g} m"
                                if len(jumps) else "n/a",
           "biggest_step_pp": round(float(jumps[worst]), 3) if len(jumps) else 0.0,
           "step_window_m": list(STEP_WINDOW)}
    return df, rep


# --------------------------------------------------------------------------------------
# STEP 3 - NODE THE DRAWING: WELD, TEE, CROSS
# --------------------------------------------------------------------------------------

def _tee_records(L: Sequence, snap: float):
    """Every place a line END sits within `snap` of another line's INTERIOR.

    Returns [(line_i, which_end, line_j, measure_on_j)], one record per end, nearest line
    only.  This is the operation W11a never had, and its absence is why a 4 m cut against
    the middle of a line survived a 3 m endpoint merge: a WELD joins ends to ends and can
    never close a gap to the middle of something.
    """
    from shapely.geometry import Point
    from shapely.strtree import STRtree

    if snap <= 0:
        return []
    tree = STRtree(list(L))
    pts, own, which = [], [], []
    for i, l in enumerate(L):
        for k in (0, -1):
            pts.append(Point(l.coords[k])); own.append(i); which.append(k)
    qi, qj = tree.query(pts, predicate="dwithin", distance=snap)
    best: Dict[int, Tuple[float, int, float]] = {}
    for a, c in zip(qi, qj):
        i = own[a]
        if c == i:
            continue
        m = L[c]
        p = pts[a]
        d = m.distance(p)
        if d > snap:
            continue
        s = m.project(p)
        if not (1e-6 < s < m.length - 1e-6):
            continue                       # it is an END of m, so the WELD owns it
        cur = best.get(a)
        if cur is None or d < cur[0]:
            best[a] = (d, int(c), float(s))
    return [(own[a], which[a], b[1], b[2]) for a, b in sorted(best.items())]


def node_network(lines: Sequence, layers: Sequence[str], handles: Sequence[str],
                 snap: float) -> Tuple[List, List[str], List[str], List[int], List, Dict]:
    """WELD, then TEE (move AND split), then split at true intersections.

    Three named operations rather than one `unary_union`, because a union tells you nothing
    about what it changed.  Each reports what it moved and how far.

    The TEE is two-sided and that is the whole point.  Splitting line B where line A's end
    lands on it, WITHOUT also moving A's end onto B, leaves A hanging up to `snap` away from
    the node it was supposed to join - a dangling end dressed up as a junction.  So the tee
    runs in two passes: pass 1 finds the records and MOVES the ends; pass 2 re-derives every
    cut on the MOVED geometry, so no cut measure is stale.

    Returns (segments, layers, handles, parent_line_index, new_node_points, report).
    `new_node_points` is [(x, y, made_by)] for every node this function CREATED, so the
    published node layer can say how each node came to exist.
    """
    from shapely.geometry import LineString
    from shapely.ops import substring
    from shapely.strtree import STRtree
    from scipy.spatial import cKDTree
    import networkx as nx

    rep: Dict = {"snap_m": snap}
    made: List[Tuple[float, float, str]] = []

    # --- WELD -----------------------------------------------------------------------
    coords = [np.asarray(l.coords, float).copy() for l in lines]
    ep = np.asarray([c[k] for c in coords for k in (0, -1)], float)
    kd = cKDTree(ep)
    g = nx.Graph()
    g.add_nodes_from(range(len(ep)))
    if snap > 0:
        g.add_edges_from(kd.query_pairs(snap, output_type="ndarray").tolist())
    new = ep.copy()
    moved, dmax = 0, 0.0
    for comp in nx.connected_components(g):
        idx = list(comp)
        if len(idx) < 2:
            continue
        c = ep[idx].mean(axis=0)
        d = np.hypot(*(ep[idx] - c).T)
        dmax = max(dmax, float(d.max()))
        moved += int((d > 1e-9).sum())
        new[idx] = c
    for i, c in enumerate(coords):
        c[0] = new[2 * i]
        c[-1] = new[2 * i + 1]
    keep = [i for i in range(len(coords)) if LineString(coords[i]).length > 1e-9]
    dropped = sorted(set(range(len(coords))) - set(keep))
    L = [LineString(coords[i]) for i in keep]
    lay = [layers[i] for i in keep]
    hnd = [handles[i] for i in keep]
    rep.update(weld_endpoints_moved=moved, weld_max_move_m=round(dmax, 4),
               collapsed_lines=len(dropped),
               collapsed_km=round(sum(lines[i].length for i in dropped) / 1000.0, 4))

    # --- TEE pass 1: MOVE the hanging ends onto the line they were cut against ---------
    recs = _tee_records(L, snap)
    tee_move = 0.0
    cds = [np.asarray(l.coords, float).copy() for l in L]
    for i, k, j, s in recs:
        pt = L[j].interpolate(s)
        tee_move = max(tee_move, float(math.hypot(cds[i][k][0] - pt.x,
                                                  cds[i][k][1] - pt.y)))
        cds[i][k] = (pt.x, pt.y)
    L2 = []
    for i, c in enumerate(cds):
        g2 = LineString(c)
        L2.append(g2 if g2.length > 1e-9 else L[i])
    L = L2
    rep["tee_ends_moved"] = len(recs)
    rep["tee_max_move_m"] = round(tee_move, 4)

    # --- TEE pass 2 + CROSSINGS: re-derive every cut on the MOVED geometry -------------
    cut: Dict[int, List[float]] = defaultdict(list)
    n_tee = 0
    for i, k, j, s in _tee_records(L, snap):
        cut[j].append(s)
        p = L[j].interpolate(s)
        made.append((p.x, p.y, "tee"))
        n_tee += 1
    rep["tee_splits"] = n_tee

    tree = STRtree(L)
    a, b = tree.query(np.asarray(L, dtype=object), predicate="crosses")
    n_x = 0
    for i, j in zip(a, b):
        if i >= j:
            continue
        it = L[i].intersection(L[j])
        parts = [it] if it.geom_type == "Point" else list(getattr(it, "geoms", []))
        for p in parts:
            if p.geom_type != "Point":
                continue
            made.append((p.x, p.y, "cross"))
            for k in (i, j):
                s = L[k].project(p)
                if 1e-6 < s < L[k].length - 1e-6:
                    cut[k].append(s)
                    n_x += 1
    rep["crossing_splits"] = n_x
    rep["crossing_points"] = int(sum(1 for m in made if m[2] == "cross"))

    # --- SPLIT ------------------------------------------------------------------------
    segs, slay, shnd, spar = [], [], [], []
    for i, l in enumerate(L):
        ss = sorted({round(s, 6) for s in cut.get(i, ()) if 1e-6 < s < l.length - 1e-6})
        if not ss:
            segs.append(l); slay.append(lay[i]); shnd.append(hnd[i]); spar.append(keep[i])
            continue
        bounds = [0.0] + ss + [l.length]
        for k, (u, v) in enumerate(zip(bounds[:-1], bounds[1:])):
            if v - u < 1e-6:
                continue
            segs.append(substring(l, u, v))
            slay.append(lay[i])
            shnd.append(f"{hnd[i]}-{k}")
            spar.append(keep[i])
    rep["segments"] = len(segs)
    rep["km"] = round(sum(s.length for s in segs) / 1000.0, 3)
    return segs, slay, shnd, spar, made, rep


def consolidate(segs: Sequence, tol: float = ENDPOINT_TOL_M) -> Tuple[List, Dict]:
    """Make coincident endpoints BIT-IDENTICAL, so node identity is exact arithmetic.

    Splitting a line at a projected measure and splitting its partner at the same place
    produce two coordinates that agree to about 1e-9 m and are not the same double.  Node
    identity minted by rounding then puts them in different nodes whenever the pair happens
    to straddle a rounding boundary - and, worse, GEOS reports the two lines as CROSSING by
    a hair instead of TOUCHING, which is what `verify()` catches.

    A WRITING tolerance, not a design one: 1 mm, four orders of magnitude below the 3 m that
    decides topology.  Nothing about the network changes; the numbers written down are made
    to agree with each other.
    """
    from shapely.geometry import LineString
    from scipy.spatial import cKDTree
    import networkx as nx

    cds = [np.asarray(s.coords, float).copy() for s in segs]
    ep = np.asarray([c[k] for c in cds for k in (0, -1)], float)
    kd = cKDTree(ep)
    g = nx.Graph()
    g.add_nodes_from(range(len(ep)))
    g.add_edges_from(kd.query_pairs(tol, output_type="ndarray").tolist())
    new = ep.copy()
    n, dmax = 0, 0.0
    for comp in nx.connected_components(g):
        idx = list(comp)
        if len(idx) < 2:
            continue
        c = ep[idx].mean(axis=0)
        dmax = max(dmax, float(np.hypot(*(ep[idx] - c).T).max()))
        n += len(idx)
        new[idx] = c
    for i, c in enumerate(cds):
        c[0] = new[2 * i]
        c[-1] = new[2 * i + 1]
    return [LineString(c) for c in cds], {"consolidated_endpoints": n,
                                          "max_move_m": round(dmax, 6), "tol_m": tol}


def mint_nodes(segs: Sequence) -> Tuple[np.ndarray, np.ndarray, np.ndarray, Dict]:
    """Node identity on an already-noded set: (endpoint -> node index, node xy, degree, rep).

    Ids are minted from EXACT coincidence, not from a second tolerance.  By this point the
    weld has already decided what "the same place" means; applying a second radius here
    would be a tolerance nobody chose.  Ordered lexicographically by (x, y), so the same
    input always produces the same node names.
    """
    ep = np.asarray([c for s in segs for c in (s.coords[0], s.coords[-1])], float)
    key = np.round(ep, 6)
    uniq, inv = np.unique(key, axis=0, return_inverse=True)
    order = np.lexsort((uniq[:, 1], uniq[:, 0]))
    remap = np.empty(len(uniq), int)
    remap[order] = np.arange(len(uniq))
    inv = remap[inv]
    uniq = uniq[order]
    deg = np.zeros(len(uniq), int)
    np.add.at(deg, inv, 1)
    return inv, uniq, deg, {"nodes": int(len(uniq)),
                            "degree_hist": {int(k): int(v)
                                            for k, v in sorted(Counter(deg.tolist()).items())}}


# --------------------------------------------------------------------------------------
# STEP 4 - COMPONENTS, FROM THE WRITTEN NODE IDS.  THIS IS THE HEADLINE.
# --------------------------------------------------------------------------------------

def components_of(df, us: str = "US_NODE", ds: str = "DS_NODE",
                  length: str = "LEN_M") -> Tuple[np.ndarray, Dict]:
    """Connected components of a published layer, FROM ITS OWN WRITTEN NODE IDS.

    This is the function the headline is measured with, and it is the API a later stage
    calls.  It takes the node id STRINGS as they were written to disk and nothing else - no
    geometry, no coordinates, no tolerance.  That is deliberate.  The previous build derived
    the road layer's components from written ids and the corridor layer's from geometry, and
    published the road number as the headline; the routable layer, the one a router can
    actually use, was in more pieces than the number anyone read.

    Components are ranked by total length, so component 0 is always the largest.  Returns
    (component id per row, report).
    """
    import networkx as nx

    u = list(df[us])
    d = list(df[ds])
    ln = np.asarray(df[length], float)
    g = nx.Graph()
    g.add_nodes_from(u)
    g.add_nodes_from(d)
    g.add_edges_from(zip(u, d))
    lab: Dict[str, int] = {}
    for i, comp in enumerate(nx.connected_components(g)):
        for n in comp:
            lab[n] = i
    raw = np.array([lab[x] for x in u], int)
    ncomp = int(raw.max()) + 1 if len(raw) else 0
    tot = np.zeros(ncomp)
    np.add.at(tot, raw, ln)
    order = np.argsort(-tot)
    rank = np.empty(ncomp, int)
    rank[order] = np.arange(ncomp)
    comp = rank[raw]
    allsum = float(ln.sum()) or 1.0
    rep = {"components": ncomp,
           "biggest_km": round(float(tot[order[0]]) / 1000.0, 3) if ncomp else 0.0,
           "biggest_pct": round(100.0 * float(tot[order[0]]) / allsum, 2) if ncomp else 0.0,
           "off_main_km": round(float(tot.sum() - tot[order[0]]) / 1000.0, 3) if ncomp else 0.0,
           "nodes": int(g.number_of_nodes()),
           "source": "written US_NODE/DS_NODE strings, no geometry"}
    return comp, rep


def sweep_tolerance(lines: Sequence, layers: Sequence[str], handles: Sequence[str],
                    tols: Sequence[float] = SWEEP_TOLS) -> pd.DataFrame:
    """Run the FULL heal-and-node pipeline at each tolerance and publish the result.

    Not a proxy - the same code that produces the deliverable, so the number in this table
    is the number the deliverable would have had at that tolerance.  A step here is the
    fingerprint of a manufactured gap and it names its own tolerance.
    """
    rows = []
    for t in tols:
        segs, slay, shnd, spar, made, r1 = node_network(lines, layers, handles, t)
        segs, _ = consolidate(segs)
        inv, xy, deg, r2 = mint_nodes(segs)
        nid = [f"N{i:06d}" for i in range(len(xy))]
        tmp = pd.DataFrame({"US_NODE": [nid[inv[2 * i]] for i in range(len(segs))],
                            "DS_NODE": [nid[inv[2 * i + 1]] for i in range(len(segs))],
                            "LEN_M": [s.length for s in segs]})
        _, r3 = components_of(tmp)
        rows.append({"TOL_M": t, "SEGMENTS": r1["segments"], "NODES": r2["nodes"],
                     "COMPONENTS": r3["components"], "BIGGEST_PCT": r3["biggest_pct"],
                     "OFF_MAIN_KM": r3["off_main_km"], "KM": r1["km"],
                     "COLLAPSED": r1["collapsed_lines"], "TEE_SPLITS": r1["tee_splits"],
                     "CROSS_SPLITS": r1["crossing_splits"]})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------------------
# STEP 5 - DUAL CARRIAGEWAYS.  MEASURED AND REPORTED.  NOTHING DELETED.
# --------------------------------------------------------------------------------------

def _runs_in_band(seg, band):
    inter = seg.intersection(band)
    if inter.is_empty:
        return []
    parts = [inter] if inter.geom_type == "LineString" else [
        g for g in getattr(inter, "geoms", []) if g.geom_type == "LineString"]
    out = []
    for p in parts:
        if p.length <= 0:
            continue
        a = seg.project(p.interpolate(0.0))
        b = seg.project(p.interpolate(p.length))
        out.append((min(a, b), max(a, b), p))
    return out


def _bearing(line, at, half=2.0):
    a = line.interpolate(max(0.0, at - half))
    b = line.interpolate(min(line.length, at + half))
    return math.degrees(math.atan2(b.y - a.y, b.x - a.x))


def split_at_band(segs, slay, shnd, spar, band):
    """Split every line where it enters or leaves the dual band.

    This deletes nothing and changes no topology.  It exists so the ALONG flag is precise:
    without it, a 20 m parallel run inside a 400 m line either flags 400 m as running along
    a carriageway or flags none of it, and both are wrong.  It also means that IF the
    engineer later decides to exclude, the exclusion is surgical rather than 400 m wide.
    Every node it creates is recorded as `MADE_BY = 'band'`.
    """
    from shapely.ops import substring

    out_s, out_l, out_h, out_p, made = [], [], [], [], []
    n_split = 0
    for i, s in enumerate(segs):
        runs = _runs_in_band(s, band) if s.intersects(band) else []
        cuts = sorted({round(x, 6) for a, b, _ in runs for x in (a, b)
                       if 1e-6 < x < s.length - 1e-6})
        if not cuts:
            out_s.append(s); out_l.append(slay[i]); out_h.append(shnd[i]); out_p.append(spar[i])
            continue
        n_split += 1
        bounds = [0.0] + cuts + [s.length]
        for c in cuts:
            p = s.interpolate(c)
            made.append((p.x, p.y, "band"))
        for k, (u, v) in enumerate(zip(bounds[:-1], bounds[1:])):
            if v - u < 1e-6:
                continue
            out_s.append(substring(s, u, v))
            out_l.append(slay[i]); out_h.append(f"{shnd[i]}.{k}"); out_p.append(spar[i])
    return out_s, out_l, out_h, out_p, made, n_split


def measure_dual_status(rec_dual) -> Tuple[pd.DataFrame, Dict]:
    """What the tagged dual-carriageway set actually IS, by record status.

    Project memory, learned the hard way on this dataset: an asset GIS holds PROPOSALS
    alongside built assets, and a length quoted without filtering on the status field is a
    length nobody can act on.  It applies here and it changes the meaning of the flag:
    rule 7 - "no pipe runs ALONG a dual carriageway because it cannot be dug up" - is an
    argument about a BUILT carriageway.  A record marked New or Modified is a proposal, and
    whether a proposal constrains a pipe today is the engineer's call, not this module's.

    So the set is split and published rather than used whole and silently.
    """
    sub = rec_dual[rec_dual["dual"] == 1].copy()
    if "STATUS" not in sub.columns:
        return pd.DataFrame(columns=["STATUS", "N", "KM"]), {}
    sub["_L"] = sub.geometry.length
    tab = (sub.groupby(sub["STATUS"].fillna("(blank)"), as_index=False)
           .agg(N=("_L", "size"), KM=("_L", lambda v: round(float(v.sum()) / 1000.0, 2))))
    tab = tab.rename(columns={tab.columns[0]: "STATUS"}).sort_values(
        "KM", ascending=False).reset_index(drop=True)
    rep = {r.STATUS: r.KM for _, r in tab.iterrows()}
    rep["total_km"] = round(float(tab["KM"].sum()), 2)
    return tab, rep


def measure_dual_cover(lines: Sequence, rec_dual) -> Tuple[pd.DataFrame, Dict]:
    """How much of the TAGGED dual-carriageway network does this drawing represent at all?

    This is the first question, and the previous build answered it decisively: the draftsman
    did not draw the carriageways.  It is re-measured here rather than quoted, because it is
    the evidence on which "the drawing is clean" rests.  If the tagged carriageways are
    simply absent from the drawing, no exclusion is needed and the whole rule 7 discussion is
    about the flanking service roads - which is exactly where a pipe SHOULD go.

    Samples the tagged centrelines every DUAL_COVER_STEP_M and reports the distance to the
    nearest drawn line as a full curve, not a threshold.
    """
    from shapely.geometry import Point
    from shapely.strtree import STRtree

    tree = STRtree(list(lines))
    rows = []
    stat: Dict[str, Dict] = {}
    for tag, sub in (("dual=1", rec_dual[rec_dual["dual"] == 1]),
                     ("dual=2", rec_dual[rec_dual["dual"] == 2])):
        geoms = [g for g in sub.geometry.values if g is not None]
        pts = []
        for g in geoms:
            n = max(1, int(g.length // DUAL_COVER_STEP_M))
            pts += [g.interpolate(k * g.length / n) for k in range(n + 1)]
        if not pts:
            continue
        idx, dist = tree.query_nearest(pts, return_distance=True, all_matches=False)
        d = np.asarray(dist, float)
        for t in DUAL_COVER_TOLS:
            rows.append({"TAG": tag, "WITHIN_M": t,
                         "N_SAMPLES": int(len(d)),
                         "PCT_REPRESENTED": round(100.0 * float((d <= t).mean()), 2)})
        stat[tag] = {"km_tagged": round(sum(g.length for g in geoms) / 1000.0, 2),
                     "samples": int(len(d)),
                     "median_dist_m": round(float(np.median(d)), 2),
                     "pct_within_1m": round(100.0 * float((d <= 1.0).mean()), 2),
                     "pct_within_10m": round(100.0 * float((d <= 10.0).mean()), 2)}
    return pd.DataFrame(rows), stat


def tag_dual(segs: Sequence, rec_dual) -> Tuple[Dict, pd.DataFrame, Dict]:
    """Classify every line against the tagged dual carriageways.  FLAG ONLY.

    The classification is measured, not assumed.  For every run inside the +/-DUAL_BAND_M
    band we take the bearing of the run and the bearing of the carriageway beneath it and
    compare.  Within DUAL_XING_SKEW_DEG of perpendicular the line CROSSES; otherwise it runs
    ALONG, and is flagged.  THE MEASURED BEARING IS THE WHOLE TEST - there is no length
    shortcut in front of it any more, and the retraction is written at XING_CONTACT_MAX_M.

    NOTHING IS DELETED.  The engineer has ruled the drawing usable throughout; his
    instruction is to check the result and report anything that still looks like it runs
    along a carriageway.  Flagging is the whole output of this function.

    The fraction test exists because a band split leaves the OUTSIDE piece touching the band
    edge, and that contact intersects as a few centimetres of line with no measurable
    bearing.  Judging a 742 m line on the bearing of a 4 cm graze is a real failure mode
    seen in this project; grazes are counted and reported, never silently judged.
    """
    from shapely.ops import unary_union
    from shapely.strtree import STRtree

    d1 = [g for g in rec_dual[rec_dual["dual"] == 1].geometry.values if g is not None]
    d2 = [g for g in rec_dual[rec_dual["dual"] == 2].geometry.values if g is not None]
    band = unary_union([g.buffer(DUAL_BAND_M) for g in d1])
    band2 = unary_union([g.buffer(DUAL_BAND_M) for g in d2]) if d2 else None
    t1 = STRtree(d1)

    tot = sum(s.length for s in segs)
    sens = []
    for w in (3.0, 5.0, DUAL_BAND_M, 7.5, 10.0, 12.0, 15.0, 20.0):
        b = unary_union([g.buffer(w) for g in d1])
        inb = sum(s.intersection(b).length for s in segs if s.intersects(b))
        sens.append({"BAND_M": w, "IN_BAND_KM": round(inb / 1000.0, 4),
                     "PCT_OF_NETWORK": round(100.0 * inb / tot, 4)})

    dual = np.zeros(len(segs), int)
    xing = np.zeros(len(segs), int)
    along = np.zeros(len(segs), int)
    angle = np.full(len(segs), -1.0)
    note = [""] * len(segs)
    along_m = xing_m = graze_m = 0.0
    n_along = n_xing = n_graze = 0

    for i, s in enumerate(segs):
        if band2 is not None and s.intersects(band2):
            dual[i] = 2
        if not s.intersects(band):
            continue
        in_len = s.intersection(band).length
        if in_len <= 0.0:
            continue
        if in_len / s.length < IN_BAND_MIN_FRAC:
            graze_m += in_len
            n_graze += 1
            continue
        dual[i] = 1
        mid = s.interpolate(0.5, normalized=True)
        th = _bearing(s, s.length * 0.5)
        g = d1[t1.nearest(mid)]
        th2 = _bearing(g, g.project(mid), half=5.0)
        ang = abs((th - th2 + 90.0) % 180.0 - 90.0)       # 0 parallel, 90 square
        angle[i] = round(ang, 1)
        # THE MEASURED BEARING DECIDES, AND NOTHING ELSE.  Until 2026-09-06 a second
        # clause sat in front of this one - `s.length <= XING_CONTACT_MAX_M` - which
        # called any short in-band piece a crossing WITHOUT looking at its bearing.  Its
        # stated argument was sound but it was applied in the wrong direction: a contact
        # no longer than XING_CONTACT_MAX_M is a square crossing ONLY IF the piece
        # actually traverses the band.  A piece that clips the band edge, or that ends
        # inside it, has a short contact at ANY bearing.  Measured on the 03/09 drawing it
        # published 12 pieces / 84.8 m as XING = 1 - a column whose own field meaning says
        # "crosses ... squarely - measured, not assumed" - at bearings of 0.1, 3.7, 3.7,
        # 5.7, 17.3, 23.0, 23.3, 23.3, 39.4, 59.6, 61.5 and 63.4 deg.  The worst was
        # A310.1: 6.78 m at 0.1 deg, i.e. exactly parallel, whose offset to the carriageway
        # centreline varied by 0.16 m over its whole length.  That is the fabricated-column
        # defect (tests/test_columns.py) in a new place, and it hid 84.8 m from H1.
        if ang >= (90.0 - DUAL_XING_SKEW_DEG):
            xing[i] = 1
            xing_m += s.length
            n_xing += 1
        else:
            along[i] = 1
            along_m += s.length
            n_along += 1
            note[i] = (f"{s.length:.0f} m inside the {DUAL_BAND_M:g} m band of a tagged "
                       f"dual carriageway at {ang:.0f} deg to it (square would be "
                       f">= {90 - DUAL_XING_SKEW_DEG:g} deg). FLAGGED FOR THE ENGINEER - "
                       f"not excluded")

    # how much of the ALONG set the removed shortcut used to hide - published, so the
    # correction is a number on the manifest and not a claim in a comment
    short_along_n = int(sum(1 for i in np.where(along == 1)[0]
                            if segs[i].length <= XING_CONTACT_MAX_M))
    short_along_m = round(float(sum(segs[i].length for i in np.where(along == 1)[0]
                                    if segs[i].length <= XING_CONTACT_MAX_M)), 1)

    rep = {"tagged_dual1_km": round(sum(g.length for g in d1) / 1000.0, 2),
           "tagged_dual2_km": round(sum(g.length for g in d2) / 1000.0, 2),
           "band_m": DUAL_BAND_M,
           "recovered_by_dropping_shortcut_n": short_along_n,
           "recovered_by_dropping_shortcut_m": short_along_m,
           "in_band_km": round((along_m + xing_m + graze_m) / 1000.0, 4),
           "along_runs": n_along, "along_m": round(along_m, 1),
           "along_pct_of_network": round(100.0 * along_m / tot, 4),
           "xing_runs": n_xing, "xing_m": round(xing_m, 1),
           "graze_runs": n_graze, "graze_m": round(graze_m, 1),
           "deleted": 0}
    return ({"DUAL": dual, "XING": xing, "ALONG_DUAL": along, "DUAL_ANG": angle,
             "NOTE": note}, pd.DataFrame(sens), rep)


def scan_twins(segs: Sequence, plots) -> Tuple[Dict, Dict]:
    """Find dual-carriageway twins the road file never tagged - and DO NOT delete them.

    A dual carriageway in this town sits a MEASURED 8-22 m from its partner.  The drawing's
    own parallel-neighbour population is essentially empty in that window - the mode is the
    24-30 m block street grid - so a sustained parallel run at 8-22 m is anomalous and worth
    an engineer's eye.

    It is NOT proof.  Two service roads straddling a dual carriageway produce exactly the
    same signature and they are legitimate routes.  The discriminator published beside each
    candidate is the share of the strip BETWEEN the pair occupied by cadastral plots: a
    median holds none, a street grid holds plots.  Deleting on the strength of a geometric
    guess is the class of decision this iteration exists to stop.
    """
    from shapely.strtree import STRtree

    tree = STRtree(list(segs))
    pg = list(plots.geometry.values)
    ptree = STRtree(pg) if pg else None

    twin_sep = np.full(len(segs), -1.0)
    twin_cov = np.full(len(segs), -1.0)
    twin_plot = np.full(len(segs), -1.0)
    for i, s in enumerate(segs):
        if s.length < TWIN_MIN_LEN_M:
            continue
        n = int(s.length // TWIN_STEP_M)
        if n < 2:
            continue
        hits, seps = 0, []
        for k in range(1, n):
            t = k * s.length / n
            p = s.interpolate(t)
            th = _bearing(s, t, half=5.0)
            best = None
            for c in tree.query(p.buffer(TWIN_SEP_MAX_M)):
                if c == i:
                    continue
                m = segs[c]
                d = m.distance(p)
                if d < TWIN_SEP_MIN_M or d > TWIN_SEP_MAX_M:
                    continue
                th2 = _bearing(m, m.project(p), half=5.0)
                dth = abs((th - th2 + 90.0) % 180.0 - 90.0)
                if dth <= TWIN_PARALLEL_DEG and (best is None or d < best):
                    best = d
            if best is not None:
                hits += 1
                seps.append(best)
        cov = hits / max(1, n - 1)
        if cov < TWIN_MIN_COVER:
            continue
        twin_cov[i] = round(cov, 3)
        twin_sep[i] = round(float(np.median(seps)), 2)
        if ptree is not None:
            strip = s.buffer(TWIN_SEP_MAX_M).difference(s.buffer(2.0))
            area = sum(pg[j].intersection(strip).area for j in ptree.query(strip)
                       if pg[j].intersects(strip))
            twin_plot[i] = round(100.0 * area / max(strip.area, 1.0), 2)

    is_cand = twin_cov >= 0
    empty = is_cand & (twin_plot >= 0) & (twin_plot < TWIN_EMPTY_PLOT_PCT)
    rep = {"candidates": int(is_cand.sum()),
           "candidate_km": round(sum(segs[i].length for i in np.where(is_cand)[0]) / 1000.0, 3),
           "empty_strip": int(empty.sum()),
           "empty_strip_km": round(sum(segs[i].length for i in np.where(empty)[0]) / 1000.0, 3),
           "sep_window_m": [TWIN_SEP_MIN_M, TWIN_SEP_MAX_M],
           "deleted": 0}
    return {"TWIN_SEP": twin_sep, "TWIN_COV": twin_cov, "TWIN_PLOT": twin_plot,
            "IS_CAND": is_cand, "EMPTY": empty}, rep


# --------------------------------------------------------------------------------------
# STEP 6 - PROVENANCE AND LOAD
# --------------------------------------------------------------------------------------

def grade_provenance(segs: Sequence, slay: Sequence[str], rec, plots
                     ) -> Tuple[Dict, pd.DataFrame, Dict]:
    """SRC from the drawing, CONFIDENCE from EVIDENCE, and the evidence published beside it.

    W10 merged four sources with trust levels 20x apart into one layer that recorded only
    `SRC`, and the perverse result was that the source trusted LEAST converted to pipe MOST.
    A grade nobody can re-derive is a grade nobody can challenge, so every input to
    CONFIDENCE is written out as its own field.

    TWO load columns, and the difference matters:
      Q_M3D       every plot within FRONTAGE_M of the line.  A plot is counted for every
                  line it fronts, so this DOUBLE COUNTS and must never be summed to a total.
                  It answers "does this line have anything in front of it".
      Q_NEAR_M3D  the plots whose NEAREST line is this one, WITH NO DISTANCE CAP.  Each plot
                  counted exactly once, so the column sums to the project total.  This is
                  what a component load must be built from: "359 km carrying 13 % of the
                  load" is a claim whose denominator has to be the whole load, not the part
                  that happened to fall inside an assumed radius.  Capping it at FRONTAGE_M
                  would silently drop 19 % of the load out of every component share, which
                  is the shape of the W10 defect (1,233 m3/d dropped inside an assignment
                  radius, unreported).
    Neither is a design allocation.  Load allocation is a later stage.  The plot-to-corridor
    distance curve is published in `load_reach` so the reach of the drawing is a measured
    shape rather than a single assumed radius.
    """
    from shapely.ops import unary_union
    from shapely.strtree import STRtree

    rec_geoms = [g for g in rec[rec["dual"] == 0].geometry.values if g is not None]
    u_rec = unary_union(rec_geoms)
    mids = [s.interpolate(0.5, normalized=True) for s in segs]
    d_rec = np.array([p.distance(u_rec) for p in mids])

    lp = plots[plots["Q_AVG_M3D"] > 0].copy()
    built = lp["BASIS"].astype(str).str.contains("counted").to_numpy()
    qv = lp["Q_AVG_M3D"].to_numpy(float)
    cent = list(lp.geometry.representative_point().values)

    tree = STRtree(list(segs))
    hit = tree.query(cent, predicate="dwithin", distance=FRONTAGE_M)
    n_plot = np.zeros(len(segs))
    n_built = np.zeros(len(segs))
    q = np.zeros(len(segs))
    np.add.at(n_plot, hit[1], 1.0)
    np.add.at(n_built, hit[1], built[hit[0]].astype(float))
    np.add.at(q, hit[1], qv[hit[0]])

    # one plot, one line, NO distance cap - the column that sums to the project total
    near_i, near_d = tree.query_nearest(cent, return_distance=True, all_matches=False)
    q_near = np.zeros(len(segs))
    near_i = np.asarray(near_i)
    if near_i.ndim == 2:                       # (input_idx, tree_idx) form
        src_idx, tgt_idx = near_i[0], near_i[1]
    else:
        src_idx = np.arange(len(cent))
        tgt_idx = near_i
    np.add.at(q_near, tgt_idx, qv[src_idx])
    q_unassigned = float(qv.sum() - q_near.sum())

    # the reach curve: how far the load actually sits from the drawing.  Published because a
    # single radius is a choice and a curve is a measurement.
    dpl = np.asarray(near_d, float)
    reach = pd.DataFrame([{"WITHIN_M": r,
                           "PCT_LOAD": round(100.0 * float(qv[dpl <= r].sum() / qv.sum()), 2),
                           "PCT_PLOTS": round(100.0 * float((dpl <= r).mean()), 2)}
                          for r in LOAD_REACH_M])

    src = np.array([SRC_OF_LAYER[l] for l in slay])
    conf = np.where((d_rec <= CORROB_M) | (n_built > 0), "corroborated",
                    np.where(n_plot > 0, "drafted", "provisional"))

    lens = np.array([s.length for s in segs])
    tab = (pd.DataFrame({"SRC": src, "CONFIDENCE": conf, "LEN_M": lens})
           .groupby(["SRC", "CONFIDENCE"], as_index=False)
           .agg(N=("LEN_M", "size"), KM=("LEN_M", lambda v: round(v.sum() / 1000.0, 2))))
    tab["PCT"] = (100.0 * tab["KM"] / (lens.sum() / 1000.0)).round(2)

    sens = {}
    for fr in (30.0, 40.0, 60.0):
        h = tree.query(cent, predicate="dwithin", distance=fr)
        npl = np.zeros(len(segs))
        np.add.at(npl, h[1], 1.0)
        sens[f"km_no_load_plot_at_{fr:g}m"] = round(lens[npl == 0].sum() / 1000.0, 1)

    rep = {"corroboration_m": CORROB_M, "frontage_m": FRONTAGE_M,
           "load_plots": int(len(lp)), "built_plots": int(built.sum()),
           "q_total_m3d": round(float(qv.sum()), 1),
           "q_allocated_m3d": round(float(q_near.sum()), 1),
           "q_unassigned_m3d": round(q_unassigned, 1),
           "plot_dist_median_m": round(float(np.median(dpl)), 1),
           "plot_dist_p90_m": round(float(np.percentile(dpl, 90)), 1),
           "plot_dist_max_m": round(float(dpl.max()), 1),
           "pct_load_within_frontage": round(
               100.0 * float(qv[dpl <= FRONTAGE_M].sum() / qv.sum()), 2),
           "pct_load_within_300m": round(
               100.0 * float(qv[dpl <= 300.0].sum() / qv.sum()), 2),
           "km_by_confidence": {c: round(lens[conf == c].sum() / 1000.0, 1)
                                for c in CONFIDENCE_ORDER},
           "frontage_sensitivity": sens}
    return ({"SRC": src, "CONFIDENCE": conf, "D_REC_M": np.round(d_rec, 2),
             "N_PLOT": n_plot.astype(int), "N_BUILT": n_built.astype(int),
             "Q_M3D": np.round(q, 3), "Q_NEAR_M3D": np.round(q_near, 3)},
            tab, reach, rep)


# --------------------------------------------------------------------------------------
# STEP 7 - NAME THE ISLANDS, AND PRICE THE DUAL REVIEW
# --------------------------------------------------------------------------------------

def name_components(cor, comp: np.ndarray) -> Tuple[pd.DataFrame, Dict]:
    """Every component of the routable layer, named, with its length, load and location.

    "Name any component that cannot reach the rest, with its length and its load."  The
    location and the GAP_TO_MAIN_M are added because they are what turns a row into a
    decision: a 40 km island 12 km from the nearest corridor is a satellite works, and a
    2 km island 15 m from the main network is a drafting gap somebody can close in an hour.
    Without that column the two look identical in a component table.
    """
    from shapely.ops import unary_union

    df = cor.copy()
    df["COMP"] = comp
    rows = []
    geoms = list(df.geometry.values)
    main = int(df.groupby("COMP")["LEN_M"].sum().idxmax()) if len(df) else 0
    main_union = unary_union([geoms[i] for i in np.where(comp == main)[0]])
    for c, sub in df.groupby("COMP"):
        u = unary_union(list(sub.geometry.values))
        cen = u.centroid
        gap = 0.0 if c == main else round(float(u.distance(main_union)), 1)
        rows.append({"COMP": int(c), "N": int(len(sub)),
                     "KM": round(float(sub["LEN_M"].sum()) / 1000.0, 3),
                     "Q_NEAR_M3D": round(float(sub["Q_NEAR_M3D"].sum()), 1),
                     "N_PLOT": int(sub["N_PLOT"].sum()),
                     "ON_MAIN": int(c == main),
                     "GAP_TO_MAIN_M": gap,
                     "X": round(cen.x, 1), "Y": round(cen.y, 1)})
    tab = pd.DataFrame(rows).sort_values("KM", ascending=False).reset_index(drop=True)
    tot_km = float(tab["KM"].sum()) or 1.0
    tot_q = float(tab["Q_NEAR_M3D"].sum()) or 1.0
    tab["PCT_KM"] = (100.0 * tab["KM"] / tot_km).round(3)
    tab["PCT_Q"] = (100.0 * tab["Q_NEAR_M3D"] / tot_q).round(3)
    off = tab[tab["ON_MAIN"] == 0]
    rep = {"components": int(len(tab)), "main_comp": main,
           "main_km": float(tab.iloc[0]["KM"]), "main_pct_km": float(tab.iloc[0]["PCT_KM"]),
           "main_pct_q": float(tab.iloc[0]["PCT_Q"]),
           "off_main_components": int(len(off)),
           "off_main_km": round(float(off["KM"].sum()), 3),
           "off_main_q_m3d": round(float(off["Q_NEAR_M3D"].sum()), 1),
           "off_main_pct_km": round(float(off["PCT_KM"].sum()), 3),
           "off_main_pct_q": round(float(off["PCT_Q"].sum()), 3),
           "off_main_within_10m": int((off["GAP_TO_MAIN_M"] <= 10.0).sum()),
           "off_main_within_50m": int((off["GAP_TO_MAIN_M"] <= 50.0).sum())}
    return tab, rep


def price_dual_review(cor, flagged: np.ndarray, rec_dual) -> Tuple[pd.DataFrame, Dict]:
    """For every line flagged as running ALONG a dual carriageway, what would excluding it
    cost, and which highway is it?

    The engineer is being asked a question, so the question comes with its price and with
    the road's name.  Each flagged line is removed from the graph one at a time and the
    network re-componented from the WRITTEN node ids; what STRANDS is the length that was on
    the main component before and is not on it after - the deleted line itself excluded, so
    the number is what gets cut off and never the deletion counted as its own damage.  (An
    earlier version differenced two off-main totals and produced a NEGATIVE strand for a
    line that was itself off-main, which is how that definition announces it is wrong.)

    A flagged line that strands nothing is a cheap decision.  A flagged line that strands
    280 km is a designed crossing, a station, a re-route, or plots served by another system
    - the only four answers the philosophy allows - and it has to be seen before stage 3,
    not discovered inside it.
    """
    import networkx as nx
    from shapely.strtree import STRtree

    cols = ["CID", "LEN_M", "DUAL_ANG", "DUAL_ROAD", "DUAL_CAT", "DUAL_STATUS",
            "DUAL_REC_M", "STRANDS_KM", "STRANDS_Q_M3D"]
    idx = np.where(flagged == 1)[0]
    if len(idx) == 0:
        return (pd.DataFrame(columns=cols),
                {"flagged": 0, "flagged_m": 0.0, "bridges": 0, "worst_cid": "",
                 "worst_strands_km": 0.0, "worst_strands_q": 0.0,
                 "all_strands_km": 0.0, "all_strands_q": 0.0})

    us = list(cor["US_NODE"]); ds = list(cor["DS_NODE"])
    ln = np.asarray(cor["LEN_M"], float); qn = np.asarray(cor["Q_NEAR_M3D"], float)
    n = len(us)

    def _on_main(drop: set) -> np.ndarray:
        """Boolean per edge: is this edge on the largest component, with `drop` removed."""
        keep = [i for i in range(n) if i not in drop]
        g = nx.Graph()
        g.add_nodes_from(us); g.add_nodes_from(ds)
        g.add_edges_from((us[i], ds[i]) for i in keep)
        lab = {}
        for k, cc in enumerate(nx.connected_components(g)):
            for x in cc:
                lab[x] = k
        tot = defaultdict(float)
        for i in keep:
            tot[lab[us[i]]] += ln[i]
        if not tot:
            return np.zeros(n, bool)
        m = max(tot, key=tot.get)
        out = np.zeros(n, bool)
        for i in keep:
            out[i] = (lab[us[i]] == m)
        return out

    def _cut(base: np.ndarray, drop: set) -> Tuple[float, float]:
        after = _on_main(drop)
        lost = base & ~after
        for i in drop:
            lost[i] = False              # the deleted line is not its own casualty
        return round(float(ln[lost].sum()) / 1000.0, 3), round(float(qn[lost].sum()), 1)

    base = _on_main(set())

    # which highway is it - so the review list is actionable rather than a list of ids
    d1 = [g for g in rec_dual[rec_dual["dual"] == 1].geometry.values if g is not None]
    d1i = rec_dual[rec_dual["dual"] == 1].reset_index(drop=True)
    t1 = STRtree(d1)
    def _field(row, col, blank):
        if col not in d1i.columns:
            return blank
        v = row[col]
        return blank if (v is None or (isinstance(v, float) and math.isnan(v))
                         or str(v).strip() in ("", "nan", "None")) else str(v)

    rows = []
    for i in idx:
        i = int(i)
        km, q = _cut(base, {i})
        j = int(t1.nearest(cor.geometry.iloc[i].centroid))
        row = d1i.iloc[j]
        rows.append({"CID": cor.iloc[i]["CID"], "LEN_M": round(float(ln[i]), 2),
                     "DUAL_ANG": float(cor.iloc[i]["DUAL_ANG"]),
                     "DUAL_ROAD": _field(row, "Name_Engli",
                                         f"unnamed record OBJECTID {row.get('OBJECTID', '?')}"),
                     "DUAL_CAT": _field(row, "Category", "-"),
                     "DUAL_STATUS": _field(row, "STATUS", "-"),
                     "DUAL_REC_M": round(float(row.geometry.length), 1),
                     "STRANDS_KM": km, "STRANDS_Q_M3D": q})
    all_km, all_q = _cut(base, {int(i) for i in idx})
    df = pd.DataFrame(rows)[cols].sort_values("STRANDS_KM",
                                              ascending=False).reset_index(drop=True)
    worst = df.iloc[0] if len(df) else None
    rep = {"flagged": int(len(idx)),
           "flagged_m": round(float(ln[idx].sum()), 1),
           "bridges": int((df["STRANDS_KM"] > 0).sum()),
           "worst_cid": str(worst["CID"]) if worst is not None else "",
           "worst_road": str(worst["DUAL_ROAD"]) if worst is not None else "",
           "worst_status": str(worst["DUAL_STATUS"]) if worst is not None else "",
           "worst_rec_m": float(worst["DUAL_REC_M"]) if worst is not None else 0.0,
           "worst_strands_km": float(worst["STRANDS_KM"]) if worst is not None else 0.0,
           "worst_strands_q": float(worst["STRANDS_Q_M3D"]) if worst is not None else 0.0,
           "all_strands_km": all_km, "all_strands_q": all_q}
    return df, rep


# --------------------------------------------------------------------------------------
# STEP 7a - ENFORCE PROJECT RULE 7 / H1 AT THE CORRIDOR
# --------------------------------------------------------------------------------------

def _off_main_mask(us, ds, ln, drop) -> np.ndarray:
    """Boolean per line: is this line OFF the largest component, with `drop` removed.

    The same definition `price_dual_review` uses, lifted out so the joint check below can
    reuse it. Componented from the node id STRINGS, never from geometry.
    """
    import networkx as nx

    n = len(us)
    keep = [i for i in range(n) if i not in drop]
    g = nx.Graph()
    g.add_nodes_from(us)
    g.add_nodes_from(ds)
    g.add_edges_from((us[i], ds[i]) for i in keep)
    lab = {}
    for k, cc in enumerate(nx.connected_components(g)):
        for x in cc:
            lab[x] = k
    tot = defaultdict(float)
    for i in keep:
        tot[lab[us[i]]] += ln[i]
    out = np.zeros(n, bool)
    if not tot:
        return out
    m = max(tot, key=tot.get)
    for i in keep:
        out[i] = (lab[us[i]] != m)
    return out


def enforce_rule_7(roads, dreview, q_total_m3d: float):
    """Take every line the measurement says runs ALONG a tagged dual carriageway out of the
    routable set - EXCEPT the ones the network cannot survive losing, which are kept, named
    and priced instead of being dropped in silence.

    WHY THIS IS HERE AND NOT IN THE ROUTER.  Philosophy sec 2 stage 2: "wadi and
    dual-carriageway exclusions apply HERE, not in the router".  `corridors` is the routable
    set; a line left in it is a line a pipe may be laid along, whatever a later stage
    intends.  Rule 7, settled by the engineer on 2026-08-19: no pipe of any kind runs ALONG
    a dual carriageway, trunk included, because it cannot be dug up.  A crossing is legal;
    running along one is not (H1, philosophy sec 3).

    WHY IT IS NOT A BLANKET EXCLUSION.  The engineer's instruction of 2026-09-03 - "the
    draftsman has resolved the dual-carriageway problem ... do not apply a blanket
    exclusion" - forbids throwing out the band, or the tagged network, or every graze and
    crossing near one.  It asks for the survivors to be checked and reported.  What is
    excluded here is the MEASURED ALONG set only - line by line, each carrying the angle and
    the carriageway it was judged against.  That is the surgical outcome `split_at_band` was
    built to make possible, not a blanket.

    THE ONE THING THAT MAY NOT HAPPEN IS A SILENT DROP.  Some of these lines are the ONLY
    drawn link across a carriageway reserve, and cutting one severs a town.  Concept rule
    "flag, do not solve" (philosophy sec 9) is explicit that what cannot be resolved at
    concept is "named with its reason and its size, NEVER DROPPED".  So the test is the
    graph's own: a flagged line whose removal strands nothing is excluded, full stop; a
    flagged line whose removal strands anything at all is RETAINED, marked H1_KEEP = 1, and
    published as an OPEN H1 breach with the km, the load and the decision it needs.  The
    threshold is zero - no invented number - and it is the same line philosophy H15 draws:
    "what is never legal is a piece that drains nowhere".

    Returns (n_excluded, table, report).  Mutates PIPE_OK / EXCL_RSN / H1_KEEP in place.
    """
    along = np.asarray(roads["ALONG_DUAL"], int) == 1
    roads["H1_KEEP"] = np.zeros(len(roads), int)
    cols = ["CID", "LEN_M", "DUAL_ANG", "DUAL_ROAD", "DUAL_STATUS", "DUAL_REC_M",
            "STRANDS_KM", "STRANDS_Q_M3D", "DISPOSITION", "REASON"]
    rep = {"flagged_n": int(along.sum()),
           "flagged_m": round(float(roads.loc[along, "LEN_M"].sum()), 1),
           "excluded_n": 0, "excluded_m": 0.0,
           "retained_n": 0, "retained_m": 0.0,
           "retained_strands_km": 0.0, "retained_strands_q": 0.0,
           "retained_strands_pct_q": 0.0}
    if not along.any():
        return 0, pd.DataFrame(columns=cols), rep

    price = dreview.set_index("CID") if len(dreview) else None
    i_pipe = roads.columns.get_loc("PIPE_OK")
    i_rsn = roads.columns.get_loc("EXCL_RSN")
    i_keep = roads.columns.get_loc("H1_KEEP")
    rows = []
    excluded_idx: set = set()
    for i in np.where(along)[0]:
        i = int(i)
        cid = roads["CID"].iloc[i]
        pr = price.loc[cid] if (price is not None and cid in price.index) else None
        km = float(pr["STRANDS_KM"]) if pr is not None else 0.0
        q = float(pr["STRANDS_Q_M3D"]) if pr is not None else 0.0
        road = str(pr["DUAL_ROAD"]) if pr is not None else "?"
        stat = str(pr["DUAL_STATUS"]) if pr is not None else "?"
        recm = float(pr["DUAL_REC_M"]) if pr is not None else float("nan")
        ang = float(roads["DUAL_ANG"].iloc[i])
        ln = float(roads["LEN_M"].iloc[i])
        if km <= 0.0:
            reason = (f"H1 / project rule 7: {ln:.0f} m running ALONG a tagged dual "
                      f"carriageway at {ang:.1f} deg (square would be "
                      f">= {90 - DUAL_XING_SKEW_DEG:g} deg), inside the "
                      f"+/-{DUAL_BAND_M:g} m band of {road}. EXCLUDED at the corridor - it "
                      f"strands nothing")
            roads.iloc[i, i_pipe] = 0
            roads.iloc[i, i_rsn] = reason
            excluded_idx.add(i)
            disp = "excluded"
            rep["excluded_n"] += 1
            rep["excluded_m"] += ln
        else:
            reason = (f"H1 BREACH, OPEN: {ln:.0f} m running ALONG {road} at {ang:.1f} deg "
                      f"(that record is status {stat}, {recm:.0f} m long). RETAINED because "
                      f"it is the only drawn link to {km:,.2f} km carrying {q:,.1f} m3/d; "
                      f"excluding it would sever that, and concept rule 'flag, do not solve' "
                      f"says what cannot be resolved now is named and sized, NEVER dropped. "
                      f"The fix is a designed carriageway crossing, which the standing "
                      f"instruction of 2026-09-03 ('no crossings for now') switches off")
            roads.iloc[i, i_keep] = 1
            disp = "retained"
            rep["retained_n"] += 1
            rep["retained_m"] += ln
            rep["retained_strands_km"] += km
            rep["retained_strands_q"] += q
        rows.append({"CID": cid, "LEN_M": round(ln, 2), "DUAL_ANG": round(ang, 1),
                     "DUAL_ROAD": road, "DUAL_STATUS": stat, "DUAL_REC_M": round(recm, 1),
                     "STRANDS_KM": round(km, 3), "STRANDS_Q_M3D": round(q, 1),
                     "DISPOSITION": disp, "REASON": reason})
    # ---- THE JOINT CHECK.  The strand above was priced ONE LINE AT A TIME, and that is
    # not the question actually being asked: the lines are excluded TOGETHER, and three of
    # them can form a cut set where no one of them does.  Measured on the 03/09 drawing the
    # per-line pricing said 18 lines strand nothing and the joint exclusion islanded
    # 0.433 km carrying 47.2 m3/d - small, and still a piece that drains nowhere, which
    # philosophy H15 says is never legal.
    #
    # So the exclusion is made able to TAKE ITSELF BACK, which is the project's own rule
    # ("anything a pass can ADD, a later pass must be able to TAKE AWAY, and the stage
    # publishes how many it removed") pointed the other way.  Greedy, and it terminates
    # because every restore strictly shrinks the newly-islanded set: while the joint
    # exclusion islands anything that was on the main component before it, put back the ONE
    # line whose return recovers the most load, and re-measure.  A line put back is not
    # quietly forgiven - it becomes a retained, flagged, priced H1 breach like any other.
    us_ = list(roads["US_NODE"])
    ds_ = list(roads["DS_NODE"])
    ln_ = np.asarray(roads["LEN_M"], float)
    qn_ = np.asarray(roads["Q_NEAR_M3D"], float)
    base_off = _off_main_mask(us_, ds_, ln_, set())
    # ONLY the rows THIS function excluded are candidates to put back.  Reading the candidate
    # set off `PIPE_OK == 0` instead would let the restore hand a row back that some other
    # rule had excluded for some other reason, silently reverse it, and then decrement
    # `excluded_n` for an exclusion this function never made.  Today rule 7 is the only thing
    # that writes a zero into PIPE_OK, so the two sets are identical and nothing changes; the
    # point is that they stay identical when the second exclusion arrives.
    dropped = set(excluded_idx)
    assert dropped == {int(i) for i in np.where(np.asarray(roads["PIPE_OK"], int) == 0)[0]}, (
        "something other than rule 7 has written PIPE_OK = 0 before this point. The restore "
        "pass below may only put back what THIS function took out")
    rep["joint_islanded_km_before_restore"] = 0.0
    rep["joint_islanded_q_before_restore"] = 0.0
    rep["left_islanded_km"] = 0.0
    rep["left_islanded_q"] = 0.0
    rep["restored_n"] = 0
    rep["restored_m"] = 0.0
    restored: List[str] = []
    for _round in range(len(dropped) + 1):
        off = _off_main_mask(us_, ds_, ln_, dropped)
        new = off & ~base_off
        for i in dropped:
            new[i] = False
        if not new.any():
            break
        if _round == 0:
            rep["joint_islanded_km_before_restore"] = round(float(ln_[new].sum()) / 1000.0, 3)
            rep["joint_islanded_q_before_restore"] = round(float(qn_[new].sum()), 1)
        best, best_q, best_km = None, 0.0, -1.0
        for i in sorted(dropped):
            off_i = _off_main_mask(us_, ds_, ln_, dropped - {i})
            rec = new & ~off_i
            rec[i] = False
            if not rec.any():
                continue
            q = float(qn_[rec].sum())
            km = float(ln_[rec].sum()) / 1000.0
            # WHAT IS RECOVERED HAS TO CARRY SOMETHING.  H15 forbids "a piece that drains
            # nowhere"; an island with NO LOAD ON IT drains nothing in the first place, so
            # the rule does not bite and there is nothing to weigh against a hard-constraint
            # breach.  Without this the greedy bought 18.2 m of H1 breach (A195.1, 41.5 deg
            # to the Al Khaburah-Ibri Road) to protect a 16 m stub carrying 0.0 m3/d.  It is
            # not a threshold - it is the absence of a reason - and the length it leaves
            # islanded is published below rather than dropped quietly.
            if q <= 0.0:
                continue
            if (q, km) > (best_q, best_km):
                best, best_q, best_km = i, q, km
        if best is None:
            # nothing excluded can recover what is left, or what is left carries no load.
            # Either way it is published, never swallowed.  "No load" means no load was
            # ALLOCATED to it (Q_NEAR_M3D - every plot goes to its nearest corridor, and
            # these are not it).  Plots may still FRONT it, so the frontage is published
            # beside the allocation rather than rounded to the same zero: the components
            # table names the piece with its own N_PLOT.
            rep["left_islanded_km"] = round(float(ln_[new].sum()) / 1000.0, 3)
            rep["left_islanded_q"] = round(float(qn_[new].sum()), 1)
            if "N_PLOT" in roads.columns:
                rep["left_islanded_frontage_plots"] = int(
                    np.asarray(roads["N_PLOT"], float)[new].sum())
            if "Q_M3D" in roads.columns:
                rep["left_islanded_frontage_q"] = round(
                    float(np.asarray(roads["Q_M3D"], float)[new].sum()), 2)
            break
        dropped.discard(best)
        excluded_idx.discard(best)
        cid = roads["CID"].iloc[best]
        ln_b = float(roads["LEN_M"].iloc[best])
        ang_b = float(roads["DUAL_ANG"].iloc[best])
        roads.iloc[best, i_pipe] = 1
        roads.iloc[best, i_keep] = 1
        roads.iloc[best, i_rsn] = ""
        reason = (f"H1 BREACH, OPEN: {ln_b:.0f} m running ALONG a tagged dual carriageway at "
                  f"{ang_b:.1f} deg. It strands nothing ON ITS OWN, which is why the "
                  f"per-line price reads zero, but excluding it TOGETHER with the rest of "
                  f"the ALONG set islands {best_km:,.3f} km carrying {best_q:,.1f} m3/d - a "
                  f"piece that drains nowhere, which H15 never allows. RESTORED and flagged "
                  f"rather than dropped")
        restored.append(str(cid))
        rep["restored_n"] += 1
        rep["restored_m"] += ln_b
        rep["excluded_n"] -= 1
        rep["excluded_m"] -= ln_b
        rep["retained_n"] += 1
        rep["retained_m"] += ln_b
        hit = [r for r in rows if r["CID"] == cid]
        if not hit:
            raise RoadStageError(
                f"the restore pass put back {cid}, which has no row in the rule 7 review "
                f"table. Every disposition must be published on its own row - a restore "
                f"that leaves no trace is the silent change this stage exists to prevent")
        r = hit[0]
        r["DISPOSITION"] = "retained"
        r["REASON"] = reason
        r["STRANDS_KM"] = round(best_km, 3)
        r["STRANDS_Q_M3D"] = round(best_q, 1)
        rep["retained_strands_km"] += best_km
        rep["retained_strands_q"] += best_q
    rep["restored_cids"] = ",".join(restored)
    # THE EXCLUSION MAY NOT DROP LOAD.  `corridors` is the PIPE_OK = 1 rows, so a plot whose
    # nearest corridor was excluded leaves the routable layer with it, and nothing downstream
    # would say so - the load would simply be smaller than the town.  Measured, published,
    # and checked in verify() rather than assumed to be zero because it happens to be today.
    ex_now = np.asarray(roads["PIPE_OK"], int) == 0
    rep["excluded_q_near"] = round(float(np.asarray(roads["Q_NEAR_M3D"], float)[ex_now].sum()), 3)
    rep["excluded_frontage_plots"] = int(np.asarray(roads["N_PLOT"], float)[ex_now].sum())

    tab = (pd.DataFrame(rows)[cols]
           .sort_values(["DISPOSITION", "STRANDS_KM", "LEN_M"],
                        ascending=[True, False, False]).reset_index(drop=True))
    for k in ("excluded_m", "retained_m", "retained_strands_km", "retained_strands_q",
              "restored_m"):
        rep[k] = round(rep[k], 2)
    rep["retained_strands_pct_q"] = round(
        100.0 * rep["retained_strands_q"] / max(q_total_m3d, 1e-9), 2)
    return rep["excluded_n"], tab, rep


def measure_dual_exposure(lines: Sequence, rec_dual, widths=(4.0, 6.0, 10.0)) -> pd.DataFrame:
    """The as-built gate is stated WITH ITS BUFFER, and so is this.

    `_BRAIN/10_ASBUILT_CALIBRATION.md`: the built 2006 network runs along a dual carriageway
    on 0.0820 % of its length and puts 1 chamber of 3,267 within 4 m - and the gate is
    "<= 0.2 % at a 4 m buffer; PUBLISH THE BUFFER (1 chamber at 4 m becomes 12 at 10 m)".
    The answer moves with the buffer, so a number quoted without one says nothing.

    EVERY WIDTH IS MEASURED ON THE IN-BAND RUN, NOT ON THE WHOLE LINE.  Until 2026-09-06
    this function judged a line only when at least IN_BAND_MIN_FRAC of it lay inside the
    band, and then charged the WHOLE line to the answer.  That rule is correct at exactly one
    width - 6 m - because `split_at_band` cuts every line at the 6 m band before it is
    judged, so an in-band piece scores 1.0 there and nowhere else.  At any OTHER width the
    filter silently refused to judge, and the table stopped moving with the buffer, which is
    the one thing it exists to show:

        published 2026-09-06     4 m:  0 runs,     0.0 m, 0.0000 %   |  10 m: 13 / 788.3 m
        the same geometry,       4 m:  1 run,     17.8 m, 0.0010 %   |  10 m: 69 / 3,602.5 m
        measured on the run                                          |        = 0.1981 %

    The 4 m zero was not "no corridor runs along a carriageway at 4 m".  It was 9DF3.1 - the
    single largest retained H1 breach in the project, the 23.1 m line holding 285.87 km -
    lying 17.75 m inside the 4 m band at 9.9 deg and being skipped because the OTHER 5.3 m
    of it was outside.  A filter that decides without measuring is the same defect
    `tag_dual` was corrected for on the same day, and this one was reporting a clean pass
    against the project's own calibration gate.

    OVERLAP_M IS THE AS-BUILT'S OWN QUANTITY, published beside ours so the comparison is
    like for like.  `asbuilt.dual_overlap_m` measures NAMA's built network as metres of pipe
    inside a 4 m buffer of a `dual` = 1 centreline divided by total length, WITH NO BEARING
    TEST - a crossing counts.  0.0820 % is that number.  ALONG_PCT is stricter (bearing
    filtered) and is the H1 quantity; OVERLAP_PCT is the calibration quantity.  Quoting
    ALONG_PCT against the 0.0820 % benchmark compares two different measurements.

    Nothing here reads the ALONG_DUAL column, so at 6 m it is an INDEPENDENT check on the
    exclusion rather than a restatement of it.
    """
    from shapely.ops import unary_union
    from shapely.strtree import STRtree

    d1 = [g for g in rec_dual[rec_dual["dual"] == 1].geometry.values if g is not None]
    cols = ["BUFFER_M", "ALONG_N", "ALONG_M", "ALONG_PCT", "XING_N", "XING_M",
            "OVERLAP_M", "OVERLAP_PCT", "GRAZE_N", "GRAZE_M"]
    if not d1:
        return pd.DataFrame(columns=cols)
    t1 = STRtree(d1)
    segs = list(lines)
    tot = sum(s.length for s in segs) or 1.0
    rows = []
    for w in widths:
        band = unary_union([g.buffer(w) for g in d1])
        an = xn = gn = 0
        am = xm = gm = ov = 0.0
        for s in segs:
            if not s.intersects(band):
                continue
            inter = s.intersection(band)
            parts = [inter] if inter.geom_type == "LineString" else [
                p for p in getattr(inter, "geoms", []) if p.geom_type == "LineString"]
            for p in parts:
                ov += p.length
                # Below the WRITING tolerance a "run" is not geometry, it is the band edge
                # touching a split point - measured at 1e-6 m and 1e-7 m on this drawing.
                # Counted and published as a graze, never silently ignored.
                if p.length <= ENDPOINT_TOL_M:
                    gn += 1
                    gm += p.length
                    continue
                mid = p.interpolate(0.5, normalized=True)
                g = d1[t1.nearest(mid)]
                ang = abs((_bearing(p, p.length * 0.5)
                           - _bearing(g, g.project(mid), half=5.0) + 90.0) % 180.0 - 90.0)
                if ang >= (90.0 - DUAL_XING_SKEW_DEG):
                    xn += 1
                    xm += p.length
                else:
                    an += 1
                    am += p.length
        rows.append({"BUFFER_M": w, "ALONG_N": an, "ALONG_M": round(am, 1),
                     "ALONG_PCT": round(100.0 * am / tot, 4),
                     "XING_N": xn, "XING_M": round(xm, 1),
                     "OVERLAP_M": round(ov, 1),
                     "OVERLAP_PCT": round(100.0 * ov / tot, 4),
                     "GRAZE_N": gn, "GRAZE_M": round(gm, 6)})
    return pd.DataFrame(rows)[cols]


# --------------------------------------------------------------------------------------
# STEP 8 - VERIFY, ON THE FILE RELOADED FROM DISK
# --------------------------------------------------------------------------------------

def verify(gpkg: Path = ROADS_GPKG) -> Dict:
    """Every published claim, checked on the file RELOADED FROM DISK.

    Checked in memory it proves nothing: W10's flow tree was real and correct and lived
    inside the process, and the shapefile inherited its geometry and none of its topology.
    The component headline in particular is recomputed HERE, a third time, from the node id
    strings as they came back off the disk, and compared with the manifest.
    """
    import geopandas as gpd
    import sqlite3
    from shapely.strtree import STRtree

    fails: List[str] = []
    roads = gpd.read_file(gpkg, layer="roads")
    nodes = gpd.read_file(gpkg, layer="nodes")
    cor = gpd.read_file(gpkg, layer="corridors")
    con = sqlite3.connect(gpkg)
    try:
        man = pd.read_sql("SELECT * FROM manifest", con).set_index("ITEM")["VALUE"]
    finally:
        con.close()

    if str(roads.crs).upper() != CRS:
        fails.append(f"roads CRS is {roads.crs}, expected {CRS}")

    # 1. every written node id resolves to a point, and the geometry agrees with it
    nx_ = dict(zip(nodes["NODE_ID"], zip(nodes["X"], nodes["Y"])))
    miss = (set(roads["US_NODE"]) | set(roads["DS_NODE"])) - set(nx_)
    if miss:
        fails.append(f"{len(miss)} US/DS_NODE values resolve to no node")
    else:
        worst = 0.0
        for g, u, d in zip(roads.geometry.values, roads["US_NODE"], roads["DS_NODE"]):
            c = list(g.coords)
            for nid, pt in ((u, c[0]), (d, c[-1])):
                x, y = nx_[nid]
                worst = max(worst, math.hypot(pt[0] - x, pt[1] - y))
        if worst > ENDPOINT_TOL_M:
            fails.append(f"worst endpoint-to-its-own-node distance {worst:.4f} m "
                         f"> {ENDPOINT_TOL_M} m")

    # 2. THE HEADLINE, recomputed from the reloaded written node ids
    comp, crep = components_of(cor)
    if int(man.get("corridor_components", -1)) != crep["components"]:
        fails.append(f"corridor component count on disk ({crep['components']}) disagrees "
                     f"with the manifest ({man.get('corridor_components')})")
    if not np.array_equal(np.asarray(cor["COMP"], int), comp):
        fails.append("the published COMP column disagrees with the components recomputed "
                     "from the published node ids")
    if int((np.asarray(cor["ON_MAIN"], int) == 1).sum()) != int((comp == 0).sum()):
        fails.append("ON_MAIN disagrees with component 0")

    # 3. THE EXCLUSION RECONCILES.  Not "corridors must BE roads" - that assertion was
    #    true only while rule 7 was unenforced, and it would have to be deleted the moment
    #    it started mattering, which is the wrong shape for a check.  What must hold now:
    #    `corridors` is EXACTLY the rows of `roads` carrying PIPE_OK = 1; every excluded row
    #    carries a reason and is one the measurement flagged; and the counts agree with the
    #    manifest, recomputed from the file rather than carried in memory.
    excl = roads[roads["PIPE_OK"] != 1]
    if set(np.asarray(roads.loc[roads["PIPE_OK"] == 1, "CID"])) != set(np.asarray(cor["CID"])):
        fails.append("`corridors` is not exactly the PIPE_OK = 1 rows of `roads`")
    if len(cor) != len(roads) - len(excl):
        fails.append(f"corridors ({len(cor)}) != roads ({len(roads)}) minus the "
                     f"{len(excl)} excluded rows")
    if not set(np.asarray(roads["PIPE_OK"], int)) <= {0, 1}:
        fails.append("PIPE_OK holds a value that is not 0 or 1")
    if len(excl):
        if excl["EXCL_RSN"].fillna("").str.strip().eq("").any():
            n = int(excl["EXCL_RSN"].fillna("").str.strip().eq("").sum())
            fails.append(f"{n} rows are excluded with no reason written on them - a silent "
                         f"drop is the defect this stage exists to prevent")
        if (np.asarray(excl["ALONG_DUAL"], int) != 1).any():
            n = int((np.asarray(excl["ALONG_DUAL"], int) != 1).sum())
            fails.append(f"{n} rows are excluded without being flagged ALONG_DUAL - this "
                         f"stage excludes on that measurement and on nothing else")
    if roads["EXCL_RSN"].fillna("").str.len().gt(0).ne(roads["PIPE_OK"] == 0).any():
        fails.append("EXCL_RSN and PIPE_OK disagree: a reason without an exclusion, or an "
                     "exclusion without a reason")
    # 3b. THE EXCLUSION MAY NOT TAKE LOAD OUT WITH IT.  Q_NEAR_M3D is every plot's load put
    #     on its NEAREST line, and it is allocated over the whole drawn network BEFORE the
    #     exclusion runs. If an excluded line carried any of it, that load leaves `corridors`
    #     and nothing downstream reports a smaller town - which is a silent drop, the worst
    #     defect in this project's history. It is zero on this drawing; it is checked because
    #     "it is zero today" is not a reason.
    q_roads = float(np.asarray(roads["Q_NEAR_M3D"], float).sum())
    q_cor = float(np.asarray(cor["Q_NEAR_M3D"], float).sum())
    if abs(q_roads - q_cor) > 1e-6:
        fails.append(
            f"the exclusion dropped {q_roads - q_cor:,.3f} m3/d of allocated load: `roads` "
            f"carries {q_roads:,.1f} m3/d of Q_NEAR_M3D and `corridors` {q_cor:,.1f}. "
            f"Q_NEAR is allocated to the NEAREST line before rule 7 runs, so an excluded "
            f"line that carried load takes it out of the routable layer with it. The load "
            f"must be re-allocated to the nearest SURVIVING corridor before the exclusion, "
            f"or published as a funnel row - never left to vanish")
    for item, got in (("rule7_excluded_n", len(excl)),
                      ("rule7_retained_n", int(np.asarray(roads.get(
                          "H1_KEEP", pd.Series(np.zeros(len(roads)))), int).sum()))):
        if item in man.index and int(float(man[item])) != got:
            fails.append(f"{item} on disk ({got}) disagrees with the manifest "
                         f"({man[item]})")

    # 3a. H1 ON THE PUBLISHED ROUTABLE LAYER, recomputed from the file.  Any survivor is an
    #     OPEN BREACH and must say so on its own row - it may never be a blank.
    still = cor[np.asarray(cor["ALONG_DUAL"], int) == 1]
    if len(still):
        if "H1_KEEP" not in cor.columns:
            fails.append(f"{len(still)} corridors run ALONG a dual carriageway and the "
                         f"layer carries no H1_KEEP column to declare them")
        elif (np.asarray(still["H1_KEEP"], int) != 1).any():
            n = int((np.asarray(still["H1_KEEP"], int) != 1).sum())
            fails.append(f"{n} corridors run ALONG a dual carriageway and are NOT declared "
                         f"H1_KEEP = 1 - an undeclared H1 breach in the routable layer")

    # 4. geometry sanity
    if (roads.geometry.geom_type != "LineString").any():
        fails.append("a published road is not a simple LineString")
    if (roads["LEN_M"] <= 0).any():
        fails.append("a published road has zero length")
    if roads["CID"].duplicated().any():
        fails.append("CID is not unique")
    if not set(roads["CONFIDENCE"]) <= set(CONFIDENCE_ORDER):
        fails.append(f"CONFIDENCE holds a value outside {CONFIDENCE_ORDER}")

    # 5. nothing may cross unnoded - a crossing with no node is a junction the router
    #    cannot see, and it is exactly the defect this stage exists to prevent
    t = STRtree(list(cor.geometry.values))
    a, b = t.query(np.asarray(list(cor.geometry.values), dtype=object), predicate="crosses")
    ncross = int((a < b).sum())
    if ncross:
        fails.append(f"{ncross} pairs of published corridors cross without a node")

    # 6. the tau flag is on every published feature
    for name, lyr in (("roads", roads), ("corridors", cor), ("nodes", nodes)):
        if "TAU_PA" not in lyr.columns:
            fails.append(f"{name} does not carry the TAU_PA flag")

    return {"pass": not fails, "failures": fails,
            "roads": len(roads), "corridors": len(cor), "nodes": len(nodes),
            "corridor_components": crep["components"],
            "corridor_biggest_pct": crep["biggest_pct"]}


# --------------------------------------------------------------------------------------
# THE API OTHER STAGES CALL
# --------------------------------------------------------------------------------------

def load(layer: Optional[str] = None, gpkg: Path = ROADS_GPKG):
    """Load the published road network.

        d   = load()                     # dict: every layer in LAYERS
        cor = load("corridors")          # the routable set only
        comp, rep = components_of(cor)   # topology from the WRITTEN node ids

    `corridors` is what a router may see.  `roads` is everything as drawn.  They differ by
    the rule 7 exclusion applied in step 8a, and they stay separate layers because reaching
    for the wrong one is how a pipe ended up on a dual carriageway in W10, and because the
    difference must be
    visible without reading code.
    """
    import geopandas as gpd
    import sqlite3
    if not Path(gpkg).exists():
        raise RoadStageError(f"{gpkg} does not exist - run `python s1_roads.py` first")
    if layer is not None:
        try:
            return gpd.read_file(gpkg, layer=layer)
        except Exception:
            con = sqlite3.connect(gpkg)
            try:
                return pd.read_sql(f"SELECT * FROM {layer}", con)
            finally:
                con.close()
    out = {}
    for lyr in LAYERS:
        try:
            out[lyr] = load(lyr, gpkg)
        except Exception:
            out[lyr] = None
    return out


# --------------------------------------------------------------------------------------
# BUILD
# --------------------------------------------------------------------------------------

def build() -> Dict:
    import geopandas as gpd
    from shapely.geometry import Point
    from shapely.ops import unary_union

    from w12.criteria import DEFAULT as CRIT

    t0 = time.time()
    R: Dict = {"stage": STAGE_VERSION, "when": time.strftime("%Y-%m-%d %H:%M"), "crs": CRS}

    for p, what in ((ROAD_DXF, "road DXF"), (ROAD_REC, "recorded centrelines"),
                    (PLOT_LOADS, "plot loads")):
        if not Path(p).exists():
            raise RoadStageError(f"missing {what}: {p}")

    print(f"\n{STAGE_VERSION}   tau = {CRIT.TAU_PA:g} Pa (FLAGGED on every output)")
    print("=" * 90)

    # ---- 1 read ------------------------------------------------------------------------
    print("[1] reading the CLEAN DXF (no DWG, no conversion, no cache)")
    lines, layers, handles, bnd_in_dxf, ltab, rrep = read_dxf()
    raw_km = sum(l.length for l in lines) / 1000.0
    boundary, brep = ((bnd_in_dxf, {"source": str(ROAD_DXF), "found": True,
                                    "layer": LAYER_BOUNDARY,
                                    "area_km2": round(bnd_in_dxf.area / 1e6, 3)})
                      if bnd_in_dxf is not None else read_boundary())
    R["read"] = rrep | {"lines": len(lines), "km": round(raw_km, 2),
                        "dxf": str(ROAD_DXF), "dxf_sha1": _sha1(ROAD_DXF),
                        "dxf_mtime": _mtime(ROAD_DXF)}
    R["boundary"] = brep
    print(f"    {ROAD_DXF.name}  ({rrep['dxf_version']} / {rrep['acad_release']}, "
          f"sha1 {R['read']['dxf_sha1']}, saved {R['read']['dxf_mtime']})")
    print(f"    {len(lines):,} lines, {raw_km:,.2f} km, "
          f"{rrep['degenerate_dropped']} degenerate dropped")
    print("    layers found, and what was done with each:")
    for _, r in ltab.iterrows():
        km = f"{r.KM:10.2f} km" if r.KM else " " * 13
        print(f"      {r.LAYER:34s} {r.ENTITY:11s} {int(r.N):6,d} {km}  {r.DECISION}")
    if brep.get("found"):
        print(f"    boundary: {brep['area_km2']:.2f} km2 from {Path(brep['source']).name} "
              f"- the road DXF carries none. Published as EVIDENCE for the open 531.4 / "
              f"439.8 km2 decision, not as the decision")
    else:
        print("    boundary: NOT FOUND. Reported, not fatal - no arithmetic here uses it")

    # ---- 2 measure BEFORE choosing any tolerance ----------------------------------------
    print("[2] measuring the endpoint-gap distribution BEFORE choosing a tolerance")
    gaps, grep = measure_gaps(lines)
    R["gaps"] = grep
    print(f"    {grep['n_endpoints']:,} endpoints; {grep['exact_touch_pct']:.2f} % touch "
          f"another line at EXACTLY 0.000 m, {grep['mm_touch_pct']:.2f} % within 1 mm, "
          f"{grep['three_m_pct']:.2f} % within 3 m")
    print(f"    biggest single step inside {STEP_WINDOW[0]}-{STEP_WINDOW[1]} m: "
          f"{grep['biggest_step_pp']:+.3f} pp over {grep['biggest_step_band']}")
    print("[3] sweeping the tolerance - FULL pipeline at each, not a proxy")
    sweep = sweep_tolerance(lines, layers, handles)
    R["sweep"] = sweep.to_dict("records")
    print("      tol_m   segs   nodes  comps  biggest%  offmain_km       km  coll  tee  cross")
    for _, r in sweep.iterrows():
        print(f"      {r.TOL_M:6.3f} {int(r.SEGMENTS):6d} {int(r.NODES):7d} "
              f"{int(r.COMPONENTS):6d} {r.BIGGEST_PCT:9.2f} {r.OFF_MAIN_KM:11.2f} "
              f"{r.KM:8.2f} {int(r.COLLAPSED):5d} {int(r.TEE_SPLITS):4d} "
              f"{int(r.CROSS_SPLITS):6d}")
    lo = sweep[sweep.TOL_M == STEP_WINDOW[0]].iloc[0]
    hi = sweep[sweep.TOL_M == STEP_WINDOW[1]].iloc[0]
    R["sweep_range"] = {"lo_pct": float(lo.BIGGEST_PCT), "hi_pct": float(hi.BIGGEST_PCT),
                        "lo_comps": int(lo.COMPONENTS), "hi_comps": int(hi.COMPONENTS),
                        "km_moved": round((hi.BIGGEST_PCT - lo.BIGGEST_PCT) / 100.0 * lo.KM, 2)}
    print(f"    over 1 mm -> 10 m the largest component moves {lo.BIGGEST_PCT:.2f} % -> "
          f"{hi.BIGGEST_PCT:.2f} % of the length ({R['sweep_range']['km_moved']:.1f} km, "
          f"{int(lo.COMPONENTS)} pieces -> {int(hi.COMPONENTS)}).")
    print("    NO CLIFF: the improvement is gradual across the whole range, so no tolerance "
          "in it closes an outsized share and there is no manufactured gap. W11a's "
          "signature was a step at 3-4.5 m and it is not here.")

    # ---- 4 node -------------------------------------------------------------------------
    snap = CRIT.MH_SNAP_M
    print(f"[4] noding at MH_SNAP_M = {snap:g} m [G203-p33 via criteria]")
    segs, slay, shnd, spar, made, hrep = node_network(lines, layers, handles, snap)
    R["node"] = hrep
    print(f"    WELD  {hrep['weld_endpoints_moved']:,} endpoints moved (max "
          f"{hrep['weld_max_move_m']:.3f} m); {hrep['collapsed_lines']} lines collapsed "
          f"({hrep['collapsed_km']:.3f} km)")
    print(f"    TEE   {hrep['tee_ends_moved']:,} hanging ends MOVED onto the line they were "
          f"drawn against (max {hrep['tee_max_move_m']:.3f} m), {hrep['tee_splits']:,} splits")
    print(f"    CROSS {hrep['crossing_points']:,} `crosses` intersections noded "
          f"({hrep['crossing_splits']:,} splits) - intersections ALREADY IN THE DRAWING, "
          f"not manufactured crossings. How many are independent X-junctions rather than "
          f"overshoots is reported at [8]")
    print(f"    -> {hrep['segments']:,} segments, {hrep['km']:,.2f} km")

    # ---- 5 dual carriageways: measured, reported, NOT enforced ---------------------------
    print("[5] dual carriageways - MEASURED and REPORTED. Nothing is deleted.")
    rec = gpd.read_file(ROAD_REC).set_crs(CRS, allow_override=True)
    if "dual" not in rec.columns:
        raise RoadStageError(f"{ROAD_REC} has no `dual` column")
    dstat, dstat_rep = measure_dual_status(rec)
    R["dual_status"] = dstat_rep
    if len(dstat):
        print("    what the tagged `dual = 1` set IS, by record status - an asset GIS holds "
              "proposals too:")
        for _, r in dstat.iterrows():
            print(f"      {r.STATUS:12s} {int(r.N):4d} records {r.KM:8.2f} km")
        print("      rule 7 is an argument about a BUILT carriageway. Whether a New or "
              "Modified record constrains a pipe today is the ENGINEER's call.")
    cover, cstat = measure_dual_cover(lines, rec)
    R["dual_cover"] = cstat
    for tag, s in cstat.items():
        print(f"    {tag}: {s['km_tagged']:.1f} km tagged in the road file; of "
              f"{s['samples']:,} samples along it, {s['pct_within_1m']:.1f} % lie within "
              f"1 m of a drawn line and {s['pct_within_10m']:.1f} % within 10 m "
              f"(median {s['median_dist_m']:.1f} m)")

    d1 = [g for g in rec[rec["dual"] == 1].geometry.values if g is not None]
    band = unary_union([g.buffer(DUAL_BAND_M) for g in d1])
    segs, slay, shnd, spar, made_b, n_bandsplit = split_at_band(segs, slay, shnd, spar, band)
    made += made_b
    segs, conrep = consolidate(segs)
    R["consolidate"] = conrep
    dtags, dsens, drep = tag_dual(segs, rec)
    R["dual"] = drep | {"band_splits": n_bandsplit, "skew_deg": DUAL_XING_SKEW_DEG,
                        "in_band_min_frac": IN_BAND_MIN_FRAC,
                        "xing_contact_max_m": round(XING_CONTACT_MAX_M, 2)}
    net_m = sum(s.length for s in segs)
    print(f"    inside the +/-{DUAL_BAND_M:g} m band: {drep['in_band_km'] * 1000:,.0f} m "
          f"({100 * drep['in_band_km'] * 1000 / net_m:.4f} % of the network)")
    print(f"      ALONG  {drep['along_runs']:4d} lines {drep['along_m']:9.1f} m  "
          f"({drep['along_pct_of_network']:.4f} % of the network) -> FLAGGED for the "
          f"engineer, NOT deleted")
    print(f"      across {drep['xing_runs']:4d} lines {drep['xing_m']:9.1f} m  -> crossings, "
          f"measured not assumed")
    print(f"      graze  {drep['graze_runs']:4d} lines {drep['graze_m']:9.1f} m  -> "
          f"< {IN_BAND_MIN_FRAC:.0%} of the line in the band; no measurable bearing")
    print("      exposure against band half-width:")
    for _, r in dsens.iterrows():
        print(f"        +/-{r.BAND_M:5.1f} m : {r.IN_BAND_KM:9.3f} km "
              f"({r.PCT_OF_NETWORK:7.4f} %)")
    dual_built = CRIT.BENCHMARKS["DUAL_SHARE_BUILT"][0]
    print(f"      NAMA's own built network runs along a dual on {100 * dual_built:.1f} % of "
          f"its length; this drawing is at "
          f"{drep['along_pct_of_network']:.4f} %.")

    print("[6] geometric twin scan - untagged carriageway candidates")
    plots = gpd.read_file(PLOT_LOADS, layer=PLOT_LOADS_LAYER)
    ttags, trep = scan_twins(segs, plots)
    R["twins"] = trep
    print(f"    {trep['candidates']} candidates, {trep['candidate_km']:.2f} km; "
          f"{trep['empty_strip']} of them have an EMPTY strip between the pair "
          f"({trep['empty_strip_km']:.2f} km) - those are the ones worth an eye")
    print("    NOT deleted. See the `twins` layer.")

    # ---- 7 provenance and load ----------------------------------------------------------
    print("[7] provenance, frontage and the reach of the drawing")
    ptags, ptab, reach, prep = grade_provenance(segs, slay, rec, plots)
    R["provenance"] = prep
    for _, r in ptab.iterrows():
        print(f"    {r.SRC:12s} {r.CONFIDENCE:14s} {int(r.N):6,d} lines {r.KM:9.2f} km "
              f"({r.PCT:5.2f} %)")
    print(f"    load: {prep['q_total_m3d']:,.0f} m3/d over {prep['load_plots']:,} plots, "
          f"ALL of it allocated to its nearest corridor (no cap), so component shares are "
          f"shares of the whole")
    print(f"    reach: plot-to-corridor distance median {prep['plot_dist_median_m']:.1f} m, "
          f"p90 {prep['plot_dist_p90_m']:.1f} m, max {prep['plot_dist_max_m']:,.0f} m")
    print(f"      {prep['pct_load_within_frontage']:.2f} % of the load is within "
          f"{FRONTAGE_M:g} m of a corridor and {prep['pct_load_within_300m']:.2f} % within "
          f"300 m - a SMOOTH decay with no cliff, so the drawing reaches the town and the "
          f"{FRONTAGE_M:g} m figure is a labelling cut, not a coverage hole")

    # ---- 8 node identity and the WRITTEN topology ---------------------------------------
    print("[8] minting node identity and WRITING it down")
    inv, nxy, deg, nrep = mint_nodes(segs)
    nid = [f"N{i:06d}" for i in range(len(nxy))]
    us = [nid[inv[2 * i]] for i in range(len(segs))]
    ds = [nid[inv[2 * i + 1]] for i in range(len(segs))]
    lens = np.array([s.length for s in segs])
    print(f"    {nrep['nodes']:,} nodes; degree "
          + "  ".join(f"{k}:{v:,}" for k, v in nrep["degree_hist"].items()))

    # How each node came to exist.  A node can be made by MORE THAN ONE operation and the
    # label says so ("tee+cross"), because collapsing that to one word hides the finding:
    # on this drawing almost every `crosses` intersection sits at the same point as a tee,
    # i.e. it is a line overshooting the line it was drawn to meet - not an independent
    # X-junction, and therefore not a connection this stage invented.
    tags: List[set] = [set() for _ in range(len(nxy))]
    if made:
        from scipy.spatial import cKDTree
        for tagname in ("tee", "cross", "band"):
            sel = [k for k, m in enumerate(made) if m[2] == tagname]
            if not sel:
                continue
            sub = cKDTree(np.asarray([[made[k][0], made[k][1]] for k in sel], float))
            for n, h in enumerate(sub.query_ball_point(nxy, r=max(ENDPOINT_TOL_M, 1e-6))):
                if h:
                    tags[n].add(tagname)
    made_by = np.array(["+".join(sorted(t)) if t else "drawn" for t in tags], dtype=object)
    R["node_made_by"] = {k: int(v) for k, v in
                         sorted(Counter(made_by.tolist()).items(), key=lambda kv: -kv[1])}
    R["cross_only_nodes"] = int(sum(1 for t in tags if t == {"cross"}))
    R["cross_with_tee_nodes"] = int(sum(1 for t in tags if "cross" in t and "tee" in t))
    print(f"    made by: " + "  ".join(f"{k}:{v:,}" for k, v in R["node_made_by"].items()))
    print(f"    the {hrep['crossing_points']} `crosses` intersections land on "
          f"{R['cross_with_tee_nodes'] + R['cross_only_nodes']} nodes, of which "
          f"{R['cross_with_tee_nodes']} are ALSO tees - a line overshooting the line it was "
          f"drawn to meet - and {R['cross_only_nodes']} are independent X-junctions. "
          f"This stage invents essentially no connection.")

    dual = dtags["DUAL"].copy()
    dual[ttags["IS_CAND"] & (dual == 0)] = 9

    roads = gpd.GeoDataFrame({
        "CID": shnd,
        "DXF_H": [h.split("-")[0].split(".")[0] for h in shnd],
        "LAYER": slay,
        "SRC": ptags["SRC"],
        "CONFIDENCE": ptags["CONFIDENCE"],
        "US_NODE": us, "DS_NODE": ds,
        "LEN_M": np.round(lens, 3),
        "DEG_US": [int(deg[inv[2 * i]]) for i in range(len(segs))],
        "DEG_DS": [int(deg[inv[2 * i + 1]]) for i in range(len(segs))],
        "DUAL": dual, "ALONG_DUAL": dtags["ALONG_DUAL"], "XING": dtags["XING"],
        "DUAL_ANG": dtags["DUAL_ANG"],
        # Set to 1 here and decided in step 8a, where every ALONG run is priced against the
        # graph before it is excluded.  Until 2026-09-06 these two columns were 1 and blank
        # on every row and rule 7 lived in the schema instead of in the data.
        "PIPE_OK": np.ones(len(segs), int),
        "EXCL_RSN": [""] * len(segs),
        "H1_KEEP": np.zeros(len(segs), int),
        "D_REC_M": ptags["D_REC_M"],
        "N_PLOT": ptags["N_PLOT"], "N_BUILT": ptags["N_BUILT"],
        "Q_M3D": ptags["Q_M3D"], "Q_NEAR_M3D": ptags["Q_NEAR_M3D"],
        "TWIN_SEP": ttags["TWIN_SEP"], "TWIN_COV": ttags["TWIN_COV"],
        "TWIN_PLOT": ttags["TWIN_PLOT"],
        "TAU_PA": np.full(len(segs), CRIT.TAU_PA),
    }, geometry=list(segs), crs=CRS)

    # ---- 8a PROJECT RULE 7 / H1 - THE EXCLUSION, APPLIED AT THE CORRIDOR -----------------
    # Philosophy sec 2 stage 2: "wadi and dual-carriageway exclusions apply HERE, not in the
    # router".  Priced FIRST on the whole drawn network, so the decision on each line is
    # taken against what the graph would lose, and only then applied.
    print("=" * 90)
    print("[8a] PROJECT RULE 7 / H1 - no pipe runs ALONG a dual carriageway")
    dreview, prep2 = price_dual_review(roads, roads["ALONG_DUAL"].to_numpy(), rec)
    R["dual_review"] = prep2
    n_excl, dexcl, erep = enforce_rule_7(roads, dreview, R["provenance"]["q_total_m3d"])
    R["rule7"] = erep
    print(f"    {erep['flagged_n']} lines / {erep['flagged_m']:,.1f} m measured as running "
          f"ALONG a tagged dual carriageway inside the +/-{DUAL_BAND_M:g} m band")
    print(f"    EXCLUDED {erep['excluded_n']} lines / {erep['excluded_m']:,.1f} m - each "
          f"strands nothing on its own AND nothing when they go together, so the exclusion "
          f"costs the network nothing")
    if erep.get("left_islanded_km"):
        print(f"    LEFT ISLANDED {erep['left_islanded_km']:,.3f} km carrying "
              f"{erep['left_islanded_q']:,.1f} m3/d of ALLOCATED load. Nothing excluded can "
              f"recover it, or nothing is allocated to it - H15 forbids a piece that DRAINS "
              f"nowhere, and a piece with nothing allocated to it drains nothing to begin "
              f"with. SAID PRECISELY, because 'no load' is a statement about Q_NEAR_M3D and "
              f"not about the ground: {erep.get('left_islanded_frontage_plots', 0)} plot(s) "
              f"carrying {erep.get('left_islanded_frontage_q', 0.0):,.2f} m3/d still FRONT "
              f"it, and each is served from the corridor it is actually allocated to. It is "
              f"named in `components` with its length, its plot count and its gap to the "
              f"main component.")
    if erep.get("restored_n"):
        print(f"    RESTORED {erep['restored_n']} of them ({erep['restored_m']:,.1f} m): "
              f"{erep['restored_cids']}. Each priced at ZERO on its own, but excluded "
              f"TOGETHER the set islanded "
              f"{erep['joint_islanded_km_before_restore']:,.3f} km carrying "
              f"{erep['joint_islanded_q_before_restore']:,.1f} m3/d - a piece that drains "
              f"nowhere, which H15 never allows. A per-line price cannot see a cut set, so "
              f"the exclusion is made able to take itself back and says how much it did.")
    if erep["retained_n"]:
        print(f"    RETAINED {erep['retained_n']} lines / {erep['retained_m']:,.1f} m as an "
              f"OPEN H1 BREACH. They are the only drawn link to "
              f"{erep['retained_strands_km']:,.2f} km carrying "
              f"{erep['retained_strands_q']:,.1f} m3/d "
              f"({erep['retained_strands_pct_q']:.2f} % of the project load); excluding "
              f"them severs it. Concept rule 'flag, do not solve': named and sized, never "
              f"dropped.")
        for _, r in dexcl[dexcl.DISPOSITION == "retained"].iterrows():
            print(f"      {r.CID:12s} {r.LEN_M:7.1f} m at {r.DUAL_ANG:5.1f} deg beside "
                  f"{r.DUAL_ROAD} ({r.DUAL_STATUS}, that record {r.DUAL_REC_M:.0f} m) "
                  f"-> severing it strands {r.STRANDS_KM:,.2f} km / "
                  f"{r.STRANDS_Q_M3D:,.1f} m3/d")
        print(f"      EACH NEEDS A DESIGNED CARRIAGEWAY CROSSING. That is switched off by "
              f"the standing instruction of 2026-09-03 ('no crossings for now'), so it is "
              f"the ENGINEER's decision to lift it at these {erep['retained_n']} places.")
    if R["dual"].get("recovered_by_dropping_shortcut_n"):
        print(f"    of the {erep['flagged_n']} flagged, "
              f"{R['dual']['recovered_by_dropping_shortcut_n']} / "
              f"{R['dual']['recovered_by_dropping_shortcut_m']:.1f} m were published as "
              f"XING = 1 until 2026-09-06 by a length shortcut that never read their "
              f"bearing - see tag_dual()")

    # ---- 9 THE HEADLINE: components of the ROUTABLE layer, from its OWN written ids ------
    corridors = roads[roads["PIPE_OK"] == 1].copy().reset_index(drop=True)
    comp, crep = components_of(corridors)
    corridors["COMP"] = comp
    corridors["ON_MAIN"] = (comp == 0).astype(int)
    ctab, nrep2 = name_components(corridors, comp)
    R["corridors"] = crep | nrep2 | {"n": len(corridors),
                                     "km": round(float(corridors["LEN_M"].sum()) / 1000.0, 3)}
    roads = roads.merge(corridors[["CID", "COMP", "ON_MAIN"]], on="CID", how="left")
    roads["COMP"] = roads["COMP"].fillna(-1).astype(int)
    roads["ON_MAIN"] = roads["ON_MAIN"].fillna(0).astype(int)

    print("=" * 90)
    print(f"[9] HEADLINE - the ROUTABLE layer, componented from its OWN WRITTEN node ids")
    print(f"    {len(corridors):,} corridors, {R['corridors']['km']:,.2f} km, "
          f"{crep['components']} components")
    print(f"    the largest holds {nrep2['main_km']:,.2f} km "
          f"({nrep2['main_pct_km']:.2f} % of the length) and "
          f"{nrep2['main_pct_q']:.2f} % of the load")
    print(f"    OFF it: {nrep2['off_main_components']} components, "
          f"{nrep2['off_main_km']:,.2f} km ({nrep2['off_main_pct_km']:.2f} %), "
          f"{nrep2['off_main_q_m3d']:,.1f} m3/d ({nrep2['off_main_pct_q']:.2f} % of the "
          f"load). EVERY ONE IS NAMED BELOW.")
    print(f"    of those, {nrep2['off_main_within_10m']} sit within 10 m of the main "
          f"component and {nrep2['off_main_within_50m']} within 50 m - those are drafting "
          f"gaps, not islands")
    print("      comp        km    %km      m3/d    %Q   gap_to_main            centroid")
    for _, r in ctab.head(20).iterrows():
        tagm = "MAIN" if r.ON_MAIN else f"{r.GAP_TO_MAIN_M:>8.1f} m"
        print(f"      {int(r.COMP):4d} {r.KM:9.3f} {r.PCT_KM:6.2f} {r.Q_NEAR_M3D:9.1f} "
              f"{r.PCT_Q:5.2f}   {tagm:>12s}   {r.X:9.0f} {r.Y:10.0f}")
    if len(ctab) > 20:
        print(f"      ... {len(ctab) - 20} more, all in the `components` table")

    # ---- 10 the exposure that is left, at three buffers ---------------------------------
    # `_BRAIN/10_ASBUILT_CALIBRATION.md` states its gate WITH its buffer and so does this:
    # "<= 0.2 % at a 4 m buffer; publish the buffer (1 chamber at 4 m becomes 12 at 10 m)".
    # Measured from the geometry of the SURVIVING corridors, never from the ALONG_DUAL
    # column, so it is an independent check on the exclusion rather than a restatement.
    print("[10] what is left, measured again from the geometry at three buffers")
    expo = measure_dual_exposure(list(corridors.geometry.values), rec)
    R["dual_exposure"] = {f"along_pct_{int(r.BUFFER_M)}m": float(r.ALONG_PCT)
                          for _, r in expo.iterrows()}
    R["dual_exposure"].update({f"overlap_pct_{int(r.BUFFER_M)}m": float(r.OVERLAP_PCT)
                               for _, r in expo.iterrows()})
    built = 100 * CRIT.BENCHMARKS["DUAL_SHARE_BUILT"][0]
    for _, r in expo.iterrows():
        print(f"      buffer +/-{r.BUFFER_M:4.1f} m : ALONG {int(r.ALONG_N):3d} in-band runs "
              f"{r.ALONG_M:8.1f} m = {r.ALONG_PCT:7.4f} % of the routable length | "
              f"ACROSS {int(r.XING_N):3d} / {r.XING_M:7.1f} m | OVERLAP (as-built's own "
              f"quantity, no bearing test) {r.OVERLAP_M:8.1f} m = {r.OVERLAP_PCT:7.4f} %")
    print(f"      MEASURED ON THE IN-BAND RUN, NOT ON THE WHOLE LINE. Until 2026-09-06 a line "
          f"was judged only when >= {IN_BAND_MIN_FRAC:g} of it lay inside the band, which is "
          f"true at 6 m ONLY - split_at_band cuts at the 6 m band - so the table published "
          f"0.0000 % at 4 m and 0.0433 % at 10 m and did not move with the buffer, which is "
          f"the one thing it exists to show. See measure_dual_exposure().")
    print(f"      the built 2006 network: {built:.4f} % of its length runs along a dual "
          f"(criteria.BENCHMARKS['DUAL_SHARE_BUILT']); _BRAIN/10_ASBUILT_CALIBRATION.md "
          f"measures it at 0.0820 % with a 4 m buffer and sets the gate at <= 0.2 % there. "
          f"THAT IS THE OVERLAP COLUMN, not the ALONG column: asbuilt.dual_overlap_m applies "
          f"NO bearing test, so a crossing counts in the 0.0820 %. Compare like with like. "
          f"A benchmark and a gate. H1 itself is ABSOLUTE, and what remains above zero here "
          f"is the retained set named in step 8a - an open breach, not a pass.")

    # ---- 11 assemble the remaining layers ------------------------------------------------
    node_comp = {}
    for u, d, c in zip(corridors["US_NODE"], corridors["DS_NODE"], comp):
        node_comp[u] = int(c); node_comp[d] = int(c)
    nodes = gpd.GeoDataFrame({
        "NODE_ID": nid, "DEGREE": deg.astype(int),
        "MADE_BY": made_by,
        "COMP": [node_comp.get(n, -1) for n in nid],
        "X": np.round(nxy[:, 0], 3), "Y": np.round(nxy[:, 1], 3),
        "TAU_PA": np.full(len(nxy), CRIT.TAU_PA),
    }, geometry=[Point(x, y) for x, y in nxy], crs=CRS)

    # built from `roads`, not from `corridors`: the whole point of this layer is that the
    # EXCLUDED lines are visible, and they are no longer in `corridors`
    review = roads[roads["ALONG_DUAL"] == 1].copy().reset_index(drop=True)
    if len(review):
        review["NOTE"] = [dtags["NOTE"][i] for i in
                          np.where(np.asarray(roads["ALONG_DUAL"]) == 1)[0]]
        review = review.merge(
            dreview[["CID", "DUAL_ROAD", "DUAL_CAT", "DUAL_STATUS", "DUAL_REC_M",
                     "STRANDS_KM", "STRANDS_Q_M3D"]], on="CID", how="left")
        review = review.merge(dexcl[["CID", "DISPOSITION", "REASON"]], on="CID", how="left")
    # from `roads`, not `corridors`: ttags is indexed in the DRAWN order and `corridors` is
    # now shorter than that by the rule 7 exclusion. A boolean mask cut for one frame and
    # applied to the other is exactly the class of silent misalignment this stage tests for.
    twins = roads[np.asarray(ttags["IS_CAND"])].copy().reset_index(drop=True)
    if len(twins):
        twins["EMPTY_STRIP"] = ttags["EMPTY"][ttags["IS_CAND"]].astype(int)

    if boundary is not None:
        bgdf = gpd.GeoDataFrame({
            "NAME": ["Project Boundary updated"],
            "AREA_KM2": [round(boundary.area / 1e6, 3)],
            "SOURCE": [str(brep.get("source", ""))],
            "NOTE": ["The clean road DXF carries NO boundary; this is read from the "
                     "separate boundary drawing. Published as EVIDENCE for the open "
                     "boundary decision (this is the LARGER of the two in use, against "
                     "439.8 km2 in MoHUP_DATA/Project_boundary.shp), never as the "
                     "decision."],
            "TAU_PA": [CRIT.TAU_PA],
        }, geometry=[boundary], crs=CRS)
    else:
        bgdf = None

    # ---- 12 write ------------------------------------------------------------------------
    ROADS_GPKG.parent.mkdir(parents=True, exist_ok=True)
    if ROADS_GPKG.exists():
        ROADS_GPKG.unlink()
    print(f"[11] writing {ROADS_GPKG.name}")
    roads.to_file(ROADS_GPKG, layer="roads", driver="GPKG")
    corridors.to_file(ROADS_GPKG, layer="corridors", driver="GPKG")
    nodes.to_file(ROADS_GPKG, layer="nodes", driver="GPKG")
    if len(review):
        review.to_file(ROADS_GPKG, layer="dual_review", driver="GPKG")
    if len(twins):
        twins.to_file(ROADS_GPKG, layer="twins", driver="GPKG")
    if bgdf is not None:
        bgdf.to_file(ROADS_GPKG, layer="boundary", driver="GPKG")

    _write_table(ltab, "layers")
    _write_table(gaps, "gaps")
    _write_table(sweep, "sweep")
    _write_table(dexcl, "dual_exclusion")
    _write_table(expo, "dual_exposure")
    _write_table(dsens, "dual_band")
    _write_table(dstat, "dual_status")
    _write_table(cover, "dual_cover")
    _write_table(ptab, "provenance")
    _write_table(reach, "load_reach")
    _write_table(ctab, "components")
    _write_table(_manifest(R, CRIT), "manifest")

    # ---- 13 verify on the RELOADED file --------------------------------------------------
    v = verify()
    R["verify"] = v
    print(f"[12] verify on the file reloaded from disk: {'PASS' if v['pass'] else 'FAIL'}")
    for f in v["failures"]:
        print(f"     FAIL  {f}")
    if not v["pass"]:
        raise RoadStageError("the published file fails its own checks: "
                             + "; ".join(v["failures"]))
    print(f"     components recomputed off disk: {v['corridor_components']} "
          f"(largest {v['corridor_biggest_pct']:.2f} %) - agrees with the manifest")

    R["seconds"] = round(time.time() - t0, 1)
    print(f"\ndone in {R['seconds']:.0f} s -> {ROADS_GPKG}")
    return R


def _write_table(df: pd.DataFrame, layer: str) -> None:
    """Write an attribute-only table into the GeoPackage.

    The measured tables are published as TABLES, not printed and lost.  A number that lives
    only in a console log is a number nobody can check next month.
    """
    import sqlite3
    con = sqlite3.connect(ROADS_GPKG)
    try:
        df.to_sql(layer, con, if_exists="replace", index=False)
        con.execute(
            "INSERT OR REPLACE INTO gpkg_contents "
            "(table_name, data_type, identifier, description, last_change, srs_id) "
            "VALUES (?, 'attributes', ?, ?, strftime('%Y-%m-%dT%H:%M:%fZ','now'), NULL)",
            (layer, layer, f"{STAGE_VERSION} measured table"))
        con.commit()
    finally:
        con.close()


def _manifest(R: Dict, CRIT) -> pd.DataFrame:
    b = R["boundary"]
    rows = [
        ("stage", STAGE_VERSION, "", "this module"),
        ("criteria", getattr(CRIT, "CRITERIA_VERSION", "w12.criteria"), "",
         "the only source of design numbers"),
        ("run", R["when"], "", ""),
        ("crs", CRS, "", "project CRS"),

        ("TAU_PA", f"{CRIT.TAU_PA:g}", "Pa",
         "ENGINEER 2026-09-03: KEEP 1.0 and FLAG on every output. Carried as a column on "
         "`roads`, `corridors`, `nodes`, `dual_review`, `twins` and `boundary`. No "
         "hydraulics in this stage, but these corridors are the ground those gradients get "
         f"laid along: at 2.0 Pa every tractive-governed gradient steepens by "
         f"{CRIT.TAU_SLOPE_FACTOR_AT_2PA:.3f}x and every depth downstream changes"),

        ("road_dxf", str(ROAD_DXF), "",
         f"THE road input. sha1 {R['read']['dxf_sha1']}, saved {R['read']['dxf_mtime']}, "
         f"{R['read']['dxf_version']}. Read directly - no DWG, no conversion, no cache"),
        ("road_layers_used", " + ".join(ROAD_LAYERS), "",
         "the two layers carrying road geometry. `piping center line-tobe conferm`, which "
         "the DWG had, is ABSENT from this DXF - the draftsman resolved his own to-be-"
         "confirmed set, so nothing here caps confidence by layer name"),
        ("boundary_source", b.get("source", ""), "",
         ("the road DXF carries NO boundary polygon; read from this separate drawing"
          if b.get("found") and Path(b.get("source", "")) != ROAD_DXF
          else ("found in the road DXF itself" if b.get("found") else "NOT FOUND"))),
        ("boundary_km2", b.get("area_km2", ""), "km2",
         "EVIDENCE for the open boundary decision - the LARGER of the two in use, against "
         "439.8 km2 in MoHUP_DATA/Project_boundary.shp. NOT a decision"),
        ("road_recorded", str(ROAD_REC), "",
         "used ONLY for the `dual` column and for corroboration - never as geometry"),
        ("plot_loads", str(PLOT_LOADS), "", "data, for confidence grading and load location"),

        ("raw_lines", R["read"]["lines"], "", "[MEASURED] as drawn"),
        ("raw_km", R["read"]["km"], "km", "[MEASURED] as drawn"),
        ("degenerate_dropped", R["read"]["degenerate_dropped"], "",
         "entities with fewer than two distinct vertices - counted, never silent"),

        ("exact_touch_pct", R["gaps"]["exact_touch_pct"], "%",
         "[MEASURED] endpoints touching another line at exactly 0.000 m"),
        ("touch_3m_pct", R["gaps"]["three_m_pct"], "%",
         "[MEASURED] endpoints within 3 m of another line"),
        ("biggest_step_pp", R["gaps"]["biggest_step_pp"], "pp",
         f"[MEASURED] biggest step in the gap curve inside {STEP_WINDOW[0]}-"
         f"{STEP_WINDOW[1]} m, over {R['gaps']['biggest_step_band']}. A step is the "
         "fingerprint of a manufactured gap; W11a's was a cliff at 3-4.5 m caused by a 4 m "
         "corridor cut against a 3 m node radius"),
        ("sweep_km_moved_1mm_to_10m", R["sweep_range"]["km_moved"], "km",
         f"[MEASURED] how much length joins the largest component across the whole "
         f"plausible tolerance range ({R['sweep_range']['lo_pct']:.2f} % -> "
         f"{R['sweep_range']['hi_pct']:.2f} %, {R['sweep_range']['lo_comps']} pieces -> "
         f"{R['sweep_range']['hi_comps']}). The tolerance is not load-bearing on this "
         "drawing, and that is the finding"),

        ("SNAP_M", CRIT.MH_SNAP_M, "m",
         "[G203-p33 via criteria.MH_SNAP_M] 3 m utility clearance: two positions closer "
         "than the clearance cannot be two structures, so two line ends closer than it are "
         "one node. Used for WELD and TEE"),
        ("weld_endpoints_moved", R["node"]["weld_endpoints_moved"], "",
         f"[MEASURED] max move {R['node']['weld_max_move_m']} m"),
        ("tee_ends_moved", R["node"]["tee_ends_moved"], "",
         "[MEASURED] hanging ends MOVED onto the line they were drawn against, then that "
         "line split there. W11a had no tee step, which is why its 4 m cuts survived a 3 m "
         "endpoint merge"),
        ("cross_nodes", R["node"]["crossing_points"], "",
         f"[MEASURED] `crosses` intersections noded. These are intersections ALREADY IN THE "
         f"DRAWING, not manufactured crossings. Of them, {R['cross_with_tee_nodes']} sit at "
         f"the same node as a TEE - a line overshooting the line it was drawn to meet - and "
         f"only {R['cross_only_nodes']} are independent X-junctions. The DXF carries no "
         f"elevation, so a flyover drawn as two crossing centrelines would be noded "
         f"wrongly; the count and the MADE_BY tag exist so that is checkable"),
        ("cross_only_nodes", R["cross_only_nodes"], "",
         "[MEASURED] nodes created by a crossing and nothing else - the only places this "
         "stage adds a junction the draftsman did not draw as a junction"),
        ("segments", R["node"]["segments"], "", "[MEASURED] after welding, teeing, "
                                                "crossing splits and band splits"),
        ("consolidated_endpoints", R["consolidate"]["consolidated_endpoints"], "",
         f"made bit-identical at {R['consolidate']['tol_m']} m, max move "
         f"{R['consolidate']['max_move_m']} m - a WRITING tolerance, not a design one"),

        ("corridor_components", R["corridors"]["components"], "",
         "**THE HEADLINE.** Components of the ROUTABLE layer, recomputed from the WRITTEN "
         "US_NODE/DS_NODE strings - no geometry, no tolerance, no in-memory graph. "
         "`verify()` recomputes it a third time off the reloaded file and fails the stage "
         "if it disagrees with this row. The previous build published the ROAD layer's "
         "count as the headline while the routable layer was in more pieces"),
        ("corridors_km", R["corridors"]["km"], "km", "the routable set"),
        ("corridor_biggest_pct", R["corridors"]["main_pct_km"], "%",
         "[MEASURED] share of routable length in the largest component"),
        ("corridor_biggest_pct_load", R["corridors"]["main_pct_q"], "%",
         "[MEASURED] share of the located load in the largest component"),
        ("off_main_components", R["corridors"]["off_main_components"], "",
         "[MEASURED] components that cannot reach the rest. EVERY ONE IS NAMED in the "
         "`components` table with its length, load, centroid and gap to the main component"),
        ("off_main_km", R["corridors"]["off_main_km"], "km",
         "[MEASURED] routable length with no path to the main component"),
        ("off_main_q_m3d", R["corridors"]["off_main_q_m3d"], "m3/d",
         "[MEASURED] load on that length, counted once per plot (Q_NEAR_M3D), so it is a "
         "real total and not the double-counted frontage column"),
        ("off_main_within_10m", R["corridors"]["off_main_within_10m"], "",
         "[MEASURED] of those components, how many sit within 10 m of the main component - "
         "drafting gaps rather than islands, and cheap to close"),

        ("rule7_flagged_n", R["rule7"]["flagged_n"], "",
         "[MEASURED] lines running ALONG a tagged dual carriageway - project rule 7 / H1"),
        ("rule7_flagged_m", R["rule7"]["flagged_m"], "m",
         "[MEASURED] their length. Until 2026-09-06 this was 831.3 m in 10 lines; the rest "
         "was hidden by a length shortcut in tag_dual() that called a short in-band piece a "
         "crossing without reading its bearing"),
        ("rule7_restored_n", R["rule7"].get("restored_n", 0), "",
         "lines this stage excluded and then PUT BACK. The strand is priced one line at a "
         "time, which cannot see a CUT SET: three lines that each strand nothing can strand "
         "0.433 km between them. So the exclusion is applied, the joint damage measured, "
         "and the minimum set restored - the project's own rule ('anything a pass can ADD, "
         "a later pass must be able to TAKE AWAY, and the stage publishes how many it "
         "removed') pointed the other way. A restored line is a retained, flagged, priced "
         "H1 breach, not a quiet forgiveness"),
        ("rule7_restored_cids", R["rule7"].get("restored_cids", ""), "",
         "which lines, by CID"),
        ("rule7_joint_islanded_km", R["rule7"].get("joint_islanded_km_before_restore", 0.0),
         "km", "[MEASURED] what the exclusion set islanded TOGETHER before those lines were "
               "restored"),
        ("rule7_left_islanded_km", R["rule7"].get("left_islanded_km", 0.0), "km",
         "[MEASURED] what is STILL islanded after the restore, and it is published rather "
         "than restored because it carries no load: H15 forbids a piece that DRAINS "
         "nowhere, and a piece with nothing on it drains nothing. Buying a hard-constraint "
         "breach to protect it would be the worse trade. It is named in `components`"),
        ("rule7_left_islanded_q", R["rule7"].get("left_islanded_q", 0.0), "m3/d",
         "[MEASURED] the load ALLOCATED to it (Q_NEAR_M3D) - zero, which is the whole "
         "argument. Allocated, not fronting: see the next two rows"),
        ("rule7_left_islanded_frontage_plots",
         R["rule7"].get("left_islanded_frontage_plots", 0), "",
         "[MEASURED] plots that FRONT the islanded piece even though none of them is "
         "allocated to it. Published because 'it carries no load' is a statement about "
         "Q_NEAR_M3D and somebody reading it will hear 'nothing is there'"),
        ("rule7_left_islanded_frontage_q",
         R["rule7"].get("left_islanded_frontage_q", 0.0), "m3/d",
         "[MEASURED] and their load, which is served from the corridor each plot is actually "
         "allocated to"),
        ("rule7_excluded_q_near", R["rule7"].get("excluded_q_near", 0.0), "m3/d",
         "[MEASURED] load ALLOCATED to the excluded lines. It must be ZERO: Q_NEAR_M3D is "
         "assigned to the nearest line over the whole drawn network BEFORE rule 7 runs, so "
         "an excluded line carrying load would take it out of `corridors` and no downstream "
         "stage would report a smaller town. verify() FAILS if `roads` and `corridors` do "
         "not carry the same Q_NEAR total - it is zero on this drawing, and 'it is zero "
         "today' is not a reason to leave it unchecked"),
        ("rule7_excluded_frontage_plots", R["rule7"].get("excluded_frontage_plots", 0), "",
         "[MEASURED] plots fronting an excluded line. They are served from the corridor they "
         "are allocated to; the number is here so the exclusion's footprint is visible"),
        ("rule7_excluded_n", R["rule7"]["excluded_n"], "",
         "lines taken OUT of `corridors` - PIPE_OK = 0, each with EXCL_RSN written on it. "
         "Philosophy sec 2 stage 2 puts the dual-carriageway exclusion at the corridor and "
         "not in the router. Every one of them strands nothing, so the exclusion costs the "
         "network nothing - it is the surgical outcome the engineer's 2026-09-03 'do not "
         "apply a BLANKET exclusion' leaves open, not a blanket"),
        ("rule7_excluded_m", R["rule7"]["excluded_m"], "m",
         "[MEASURED] the length excluded"),
        ("rule7_retained_n", R["rule7"]["retained_n"], "",
         "OPEN H1 BREACHES. Lines running ALONG a carriageway that are RETAINED because "
         "each is the only drawn link to what sits behind it. Concept rule 'flag, do not "
         "solve' (philosophy sec 9): what cannot be resolved at concept is named with its "
         "reason and its size, NEVER DROPPED. Each carries H1_KEEP = 1 and a row in "
         "`dual_exclusion`. THIS IS NOT A PASS"),
        ("rule7_retained_m", R["rule7"]["retained_m"], "m",
         "[MEASURED] the length of that open breach"),
        ("rule7_retained_strands_km", R["rule7"]["retained_strands_km"], "km",
         "[MEASURED] what excluding the retained lines instead would sever. This is the "
         "number the decision turns on, and it is why they were not simply deleted"),
        ("rule7_retained_strands_q", R["rule7"]["retained_strands_q"], "m3/d",
         f"[MEASURED] the load on that length - "
         f"{R['rule7']['retained_strands_pct_q']:.2f} % of the project total. THE ENGINEER "
         f"DECIDES: each of these needs a designed carriageway crossing, which the standing "
         f"instruction of 2026-09-03 ('no crossings for now') switches off"),
        ("PIPE_OK", R["rule7"]["excluded_n"], "",
         "count of PIPE_OK = 0 rows on `roads`. `corridors` is the PIPE_OK = 1 rows and "
         "`verify()` reconciles the two against this number, recomputed from the file. It "
         "was 0 until 2026-09-06, when rule 7 stopped living in the schema and started "
         "living in the data"),
        ("DUAL_BAND_M", DUAL_BAND_M, "m",
         "[ASSUME] half-width of the band around a tagged dual centreline inside which a "
         "line is judged. Grounded on the measured ~14 m separation of the tagged "
         "carriageways. Sensitivity at eight widths in the `dual_band` table"),
        ("DUAL_XING_SKEW_DEG", DUAL_XING_SKEW_DEG, "deg",
         "[ASSUME] the tolerance on 'square'. Same value criteria uses for a wadi crossing "
         "- one project, one meaning for the word"),
        ("XING_CONTACT_MAX_M", round(XING_CONTACT_MAX_M, 2), "m",
         "[DERIVED] 2 x DUAL_BAND_M / sin(90 - skew) - the in-band contact a square crossing "
         "makes. PUBLISHED AS A DIAGNOSTIC AND NO LONGER USED TO CLASSIFY. Until 2026-09-06 "
         "any in-band piece shorter than this was called a crossing WITHOUT reading its "
         "bearing; the inversion is only valid for a piece that actually traverses the band, "
         "and a piece that clips the band edge has a short contact at ANY bearing. It "
         "published 12 pieces / 84.8 m as XING = 1 at 0.1 to 63.4 deg - the worst 6.8 m at "
         "0.1 deg, exactly parallel. The measured bearing now decides, and nothing else"),
        ("dual_along_recovered_n", R["dual"].get("recovered_by_dropping_shortcut_n", 0), "",
         "[MEASURED] of the flagged lines, how many that shortcut used to hide"),
        ("dual_along_recovered_m", R["dual"].get("recovered_by_dropping_shortcut_m", 0.0),
         "m", "[MEASURED] and their length"),
        ("dual_along_pct_4m", R["dual_exposure"].get("along_pct_4m", ""), "%",
         "[MEASURED] ALONG share of the PUBLISHED routable layer at a 4 m buffer, "
         "re-measured from the geometry rather than read off ALONG_DUAL, and measured ON THE "
         "IN-BAND RUN. Until 2026-09-06 this read 0.0000 % because a line was judged only "
         "when >= IN_BAND_MIN_FRAC of it lay inside the band, which holds at 6 m ONLY: it "
         "skipped 9DF3.1 lying 17.75 m inside the 4 m band at 9.9 deg. IT IS NOT THE GATE "
         "QUANTITY - see dual_overlap_pct_4m"),
        ("dual_along_pct_6m", R["dual_exposure"].get("along_pct_6m", ""), "%",
         "[MEASURED] the same at the band half-width this stage judges on"),
        ("dual_along_pct_10m", R["dual_exposure"].get("along_pct_10m", ""), "%",
         "[MEASURED] the same at 10 m - the width at which the built network's 1 chamber "
         "within 4 m becomes 12. Was published as 0.0433 % until 2026-09-06 by the same "
         "whole-line filter; measured on the run it is ~4.6x that"),
        ("dual_overlap_pct_4m", R["dual_exposure"].get("overlap_pct_4m", ""), "%",
         "[MEASURED] THIS IS THE CALIBRATION GATE'S OWN QUANTITY, and the only one of these "
         "that may be quoted against it. `asbuilt.dual_overlap_m` measures NAMA's built "
         "network as metres of pipe inside a 4 m buffer of a `dual` = 1 centreline over "
         "total length WITH NO BEARING TEST - a crossing counts. That is the 0.0820 % in "
         "_BRAIN/10_ASBUILT_CALIBRATION.md and the <= 0.2 % gate beside it. ALONG_PCT is "
         "bearing-filtered and therefore a different measurement"),
        ("dual_overlap_pct_6m", R["dual_exposure"].get("overlap_pct_6m", ""), "%",
         "[MEASURED] the same at the band half-width this stage judges on"),
        ("dual_overlap_pct_10m", R["dual_exposure"].get("overlap_pct_10m", ""), "%",
         "[MEASURED] the same at 10 m. THE ANSWER MOVES WITH THE BUFFER, which is why the "
         "calibration document orders the buffer published with the number"),
        ("IN_BAND_MIN_FRAC", IN_BAND_MIN_FRAC, "",
         "[ASSUME] a line is judged against a carriageway only when this much of it is "
         "inside the band. Below it the contact is a graze with no measurable bearing. IT IS "
         "VALID ONLY BECAUSE split_at_band CUTS EVERY LINE AT THE SAME BAND FIRST: applied "
         "at any other width it is a filter that decides without measuring, which is what "
         "made dual_along_pct_4m read zero until 2026-09-06"),
        ("dual1_tagged_km", R["dual"]["tagged_dual1_km"], "km",
         "[MEASURED] dual carriageway tagged `dual = 1` in the recorded centrelines. IT IS "
         "NOT ALL BUILT: by record status it splits "
         + ", ".join(f"{k} {v} km" for k, v in R["dual_status"].items() if k != "total_km")
         + " (`dual_status` table). An asset GIS holds proposals alongside built assets, "
           "and rule 7 - a pipe cannot be laid under a carriageway because it cannot be dug "
           "up - is an argument about a BUILT one. Whether a New or Modified record "
           "constrains a pipe today is the ENGINEER's call, so the set is published split "
           "rather than used whole"),
        ("dual1_represented_pct_1m", R["dual_cover"].get("dual=1", {}).get("pct_within_1m", ""),
         "%", "[MEASURED] share of the tagged dual centrelines lying within 1 m of a line in "
              "this drawing. The full curve is in `dual_cover`. This is the evidence for "
              "'the draftsman did not draw the carriageways' - what sits beside them is the "
              "flanking service road, which is where a pipe should go"),
        ("dual_along_m", R["dual"]["along_m"], "m",
         "[MEASURED] length still running ALONG a tagged dual carriageway. FLAGGED, NOT "
         "DELETED - the engineer's instruction of 2026-09-03. See `dual_review`"),
        ("dual_along_pct", R["dual"]["along_pct_of_network"], "%",
         f"[MEASURED] the FLAGGED share of the WHOLE DRAWN network, at the 6 m band, BEFORE "
         f"rule 7 excludes anything. It is not the exposure of what is published (that is "
         f"dual_along_pct_6m, on `corridors`) and it is NOT the quantity the as-built gate "
         f"is written in (that is dual_overlap_pct_4m, which counts every metre in the "
         f"buffer with no bearing test, the way asbuilt.dual_overlap_m does). NAMA's built "
         f"network is {100 * CRIT.BENCHMARKS['DUAL_SHARE_BUILT'][0]:.1f} % on that third "
         f"definition (criteria.BENCHMARKS) - a benchmark, never a limit, and only "
         f"comparable with the item measured the same way"),
        ("dual_xing_m", R["dual"]["xing_m"], "m",
         "[MEASURED] length crossing a tagged dual squarely - measured bearing, not assumed"),
        ("dual_graze_m", R["dual"]["graze_m"], "m",
         "[MEASURED] length grazing the band without being judged - counted, never silent"),
        ("dual_review_flagged", R["dual_review"]["flagged"], "",
         "lines on the review list handed to the engineer"),
        ("dual_review_all_strands_km", R["dual_review"]["all_strands_km"], "km",
         "[MEASURED] what excluding EVERY flagged line at once would strand. The decision "
         "comes with its price rather than without one"),
        ("dual_review_worst", R["dual_review"]["worst_cid"], "",
         f"beside {R['dual_review']['worst_road']} "
         f"(status {R['dual_review']['worst_status']}, that record is only "
         f"{R['dual_review']['worst_rec_m']:.0f} m long). Strands "
         f"{R['dual_review']['worst_strands_km']:.2f} km carrying "
         f"{R['dual_review']['worst_strands_q']:.1f} m3/d. THE ENGINEER DECIDES: a designed "
         f"crossing, a station, a re-route, or plots served by another system"),

        ("TWIN_SEP_MIN_M", TWIN_SEP_MIN_M, "m",
         "[MEASURED] lower edge of the dual-carriageway separation window in this town"),
        ("TWIN_SEP_MAX_M", TWIN_SEP_MAX_M, "m",
         "[MEASURED] upper edge; the block street grid starts at ~24 m"),
        ("twin_candidates", R["twins"]["candidates"], "",
         "[MEASURED] untagged twin candidates - FLAGGED, NOT DELETED. Deleting km on a "
         "geometric guess is the class of decision this iteration exists to stop"),
        ("twin_empty_strip", R["twins"]["empty_strip"], "",
         "of those, with no cadastral plots between the pair - the ones worth an eye"),

        ("CORROB_M", CORROB_M, "m",
         "[ASSUME] how close a recorded centreline must be to corroborate a drawn line. The "
         "curve has no knee; D_REC_M is published per line so this can be re-graded"),
        ("FRONTAGE_M", FRONTAGE_M, "m",
         "[ASSUME] a plot fronts a line this close. Bounded by the MEASURED 24-30 m block "
         "street grid. Sensitivity: "
         + ", ".join(f"{k}={v} km" for k, v in
                     R["provenance"]["frontage_sensitivity"].items())),
        ("q_total_m3d", R["provenance"]["q_total_m3d"], "m3/d",
         "[MEASURED] saturation ADWF on all load-bearing plots"),
        ("q_unassigned_m3d", R["provenance"]["q_unassigned_m3d"], "m3/d",
         "[MEASURED] load allocated to NO corridor. Zero by construction: Q_NEAR_M3D is "
         "uncapped, so every plot lands on its nearest corridor and every component share "
         "is a share of the whole. W10 dropped 1,233 m3/d inside an assignment radius and "
         "said nothing; the distance is published instead of used as a filter"),
        ("plot_dist_median_m", R["provenance"]["plot_dist_median_m"], "m",
         f"[MEASURED] plot to nearest corridor. p90 {R['provenance']['plot_dist_p90_m']} m, "
         f"max {R['provenance']['plot_dist_max_m']:,.0f} m. Full curve in `load_reach`"),
        ("pct_load_within_frontage", R["provenance"]["pct_load_within_frontage"], "%",
         f"[MEASURED] load within FRONTAGE_M = {FRONTAGE_M:g} m of a corridor. The "
         f"remainder is NOT a coverage hole: the curve is a smooth decay with no cliff and "
         f"{R['provenance']['pct_load_within_300m']:.2f} % of the load is within 300 m. "
         f"FRONTAGE_M is a labelling cut, and `load_reach` is the measurement"),
        ("ENDPOINT_TOL_M", ENDPOINT_TOL_M, "m",
         "[ASSUME] published geometry must agree with US_NODE/DS_NODE to this. A WRITING "
         "tolerance, checked on the reloaded file"),
    ]
    for c, km in R["provenance"]["km_by_confidence"].items():
        rows.append((f"km_{c}", km, "km", "[MEASURED] by evidence, not by layer name"))
    for k, v in R.get("node_made_by", {}).items():
        rows.append((f"nodes_made_by_{k}", v, "", "how the node came to exist"))
    for k, v in FIELDS.items():
        rows.append((f"field.{k}", "", "", v))
    return pd.DataFrame(rows, columns=["ITEM", "VALUE", "UNIT", "NOTE"])


def report(gpkg: Path = ROADS_GPKG) -> None:
    """Re-print the measured tables from the published file, without rebuilding."""
    import sqlite3
    con = sqlite3.connect(gpkg)
    try:
        for t in ("layers", "gaps", "sweep", "dual_band", "dual_exposure", "dual_exclusion",
                  "dual_status", "dual_cover",
                  "provenance", "load_reach", "components", "manifest"):
            print(f"\n=== {t} ===")
            print(pd.read_sql(f"SELECT * FROM {t}", con).to_string(index=False))
    finally:
        con.close()


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--report", action="store_true",
                    help="re-print the measured tables from the published file")
    ap.add_argument("--verify", action="store_true",
                    help="re-run every check against the published file")
    a = ap.parse_args(argv)
    if a.report:
        report()
        return 0
    if a.verify:
        v = verify()
        print(json.dumps(v, indent=2))
        return 0 if v["pass"] else 1
    try:
        R = build()
    except RoadStageError as e:
        print(f"\nFAILED: {e}", file=sys.stderr)
        return 1
    return 0 if R["verify"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
