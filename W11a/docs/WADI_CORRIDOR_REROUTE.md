# Re-routing the corridors that run down wadis

**Analysis only. No stage `.py` file was touched.** Every code block below is a proposal,
marked with the file and the function it replaces. Measured 2026-09-02 against the layers
as published at 14:55: `W11a/shp/W11a.gpkg` [`corridors` 26,450 / 2,234.85 km,
`corridor_nodes` 23,916, `crossings`], `W11a/shp/W11a_corridors_removed.gpkg` [`removed`
586 / 71.02 km], `W10/shp/W10_plot_loads.gpkg` [64,071 plots / 74,701.2 m³/d] and
`Data/04 Lekhuwair/Hazard_T50y.tif`.

Every number here is reproducible with one command:

```
python W11a/report/fig_wadi_reroute.py --patch    # the measurement table + the patch simulation
python W11a/report/fig_wadi_reroute.py            # and the four figures, FR01-FR04
```

---

## 0. The uncomfortable finding

**47.58 km of published corridor runs ALONG a wadi, and `audit.r4` passes every metre of
it — because the along/across test measures the wrong width.**

I ran the auditor myself against the published `corridors` layer, twice, two hours apart:

> 14:20 — `R4 PASS | nothing along a wadi; 2,495 scheduled crossing(s); 53 % of samples
> fall outside the hazard grid and are UNTESTED (6,783 reaches entirely so)`
>
> 15:44 — `R4 FAIL | 10 wadi crossings with no CROSS_ID - H1a(4) requires each in the
> crossings schedule; 53 % of samples … UNTESTED (6,783 reaches entirely so)`

The corridors are byte-identical between the two (26,450 rows, every attribute the same).
What changed is that **a later stage overwrote the `crossings` layer inside
`W11a.gpkg`** — see §7 — so ten corridor `CROSS_ID`s stopped resolving. **Neither run
classifies a single reach as running ALONG a wadi**, which is the claim in question.

That is not evidence. `s2._square_crossing` and `audit._r4_classify` both probe
**perpendicular to the pipe**, capped at 400 m each way, and compare the contact to what
that one ray finds. Philosophy H1a item 1 says something else — the contact must be within
the skew tolerance *"of the **shortest crossing available at that point**"*. Applied as
written, with the philosophy's own tolerance, **561 of the 2,541 contiguous on-wadi
contacts are not crossings at all.** The probe rejects **one**.

Three further things, and only the third was in the brief:

| | |
|---|---|
| The brief's figures **held up** | 100.4 km of on-wadi corridor is now **98.99 km** by the register field and **102.05 km** by the auditor's own contact definition; the longest contiguous run is **786.98 m**, not 789 m. Stage 2's re-run took the corridor set from 784 components to 311 and moved the wadi contact by 1.4 km |
| The brief's four buckets are **for chambers, not corridors** | *"319 slide within 20 m, 472 slide 20-50 m, 1,272 need the crossing redesigned, 291 need the corridor re-routed"* is `TERTIARY_AND_WADI_CHAMBERS` §2c's classification of the **2,354 chambers**. This document is about the **561 corridors** under them, and the two do not map one-to-one |
| The re-route the brief asks me to price **does not exist**, and something far cheaper does | Only **69 of the 561** have any alternative path through the rest of the corridor network, and replacing those 69 costs **59.17 km** of extra corridor. But deleting all 561 and healing the severance costs **150 links totalling 2.57 km** and finishes with **976 m³/d MORE** load connected to the trunk than the layer published today |

**And one correction to my own first pass, because it moves the headline by 24 km.** I first
estimated the shortest crossing as `2 × median` distance to dry ground along the contact,
which gives 1,008 runs and 71.78 km. That is wrong by a factor of two. On a perfect
perpendicular crossing of a band of width *W* the distance to dry ground ramps 0 → *W*/2 → 0
along the pipe, so the median recovers *W*/2 and the test scores a **perfect crossing at
skew 2.00** — over the tolerance. With the **maximum**, `2 × max` recovers *W* and
skew = 1/cos(deviation) exactly, so 1.155 means 30° off square, which is what
`audit.WADI_XING_SKEW` is defined to be. The max set is a strict subset of the median set.
**Everything below uses the maximum.**

---

## 1. What is current, re-measured

Sampled at `audit.WADI_SAMPLE_M` = 1.5 m, half the grid's 3.0 m cell.

| | value |
|---|---:|
| Corridors published | **26,450 / 2,234.85 km** |
| Hazard samples over them | 1,528,113 |
| — **UNTESTED** (nodata −9999.0 or off the grid) | **807,083 = 52.82 %** |
| — corridors with **no** hazard answer anywhere on them | 6,774 (`audit.r4` says 6,783; it steps `int(L/1.5)+1` where this steps `ceil`) |
| Corridors touching wadi ground | **2,539** |
| Contiguous on-wadi runs on them | **2,541** |
| On-wadi length, `ON_WADI_M` field (fraction × length) | **98.99 km** |
| On-wadi length, auditor's contact definition (`ds[b] − ds[a] + 1.5 m`) | **102.05 km** |
| Longest single run — field / contact | **786.98 m / 788.48 m** (`W11a-C010842`) |
| `CROSS_ID` minted on a corridor | 2,539 of 2,539 |
| — resolving to an `OBSTACLE='wadi'` row in `[crossings]` | 2,539 at 14:09, **2,529 at 15:44** — a later stage rewrote the layer (§7) |

The 3.06 km between the two length definitions is one sample step per run, not a
discrepancy: `audit._r4_classify` adds `WADI_SAMPLE_M` to every contact because the contact
extends half a cell past its end samples; `s2` writes the field as `mean(on) × L`. **Quote
the field for the register and the contact for the geometry test**, and say which.

**Coverage travels with every number above.** `s2.WadiMask.at()` returns `False` — *not a
wadi* — for a nodata cell and for anything outside its read window, so every wadi result in
this stage is a statement about the tested 47 %.

---

## 2. The defect: the along/across test measures the wrong width

### 2a. What the code does

`s2_corridors._square_crossing` (line 223) and `audit._r4_classify` (line 528) implement
one test:

```python
# at the MIDDLE of the on-wadi run, take the unit normal to the pipe and walk it
# outwards until the hazard band ends, both ways, capped at WADI_PROBE_M = 400 m
square = contact <= WADI_XING_SKEW * max(width, WADI_SAMPLE_M)
```

For a straight band, `width = W / cos θ` and `contact = W / sin θ` where θ is the angle
between pipe and band axis, so the test reduces to `cot θ ≤ 1.155`, i.e. **θ ≥ 40.9°** —
nominally a 30° tolerance, in practice 49°. That much is defensible.

The cap is not. **The probe hit its 400 m limit on 506 of 2,541 runs, and hit it in both
directions on 58**, returning `width = 800 m`. At `width = 800` the test passes any contact
up to **924 m** — longer than anything in the network. Eight of the ten longest contacts are
in that state.

`W11a-C010611` is the clean case: **651.8 m of continuous contact**, probe width 800 m
(capped), and dry ground **41.7 m** away. The test says it crosses.

### 2b. What the philosophy says, and how to measure it

`08_DESIGN_PHILOSOPHY.md`, H1a item 1, verbatim:

> **It crosses, it does not run along.** The on-wadi contact is a *single contiguous run*,
> and its length is within the stated skew tolerance of **the shortest crossing available
> at that point**.

The shortest crossing available is the **local channel width**, and the estimator is
`2 × max(distance to the nearest known non-wadi cell)` over the contact's own samples,
read from a distance transform of the hazard grid in which **nodata is not dry**.

Why the maximum and not the median, since the choice is worth 24.64 km:

| statistic | on a perfect square crossing of a band of width *W* | skew it scores |
|---|---|---:|
| 2 × **median** d_dry | recovers *W*/2 — the ramp 0 → *W*/2 → 0 has median *W*/4 | **2.00 — condemned** |
| 2 × **max** d_dry | recovers *W* | **1.00 — passes** |

With the maximum, `skew = 1 / cos(deviation from square)` exactly: 15° off square gives
1.035, 30° gives 1.155, 60° gives 2.000. **The tolerance then means what it says.** The
median form flags 1,008 runs / 71.78 km, the max form 561 / 47.27 km, and the max set is a
strict subset.

### 2c. The two tests, measured

| Test | Runs judged ALONG | Contact |
|---|---:|---:|
| Perpendicular probe — **what the code applies** | **1** of 2,541 | 0.03 km |
| Shortest crossing available — **H1a item 1 as written** | **561** of 2,541 | **47.27 km** |
| *(the median form, shown only to be rejected)* | *1,008* | *71.78 km* |

On the corridors themselves: **561 corridors, 47.58 km**, fronting **518** load-bearing
plots.

**Sensitivity — the tolerance is ours, not the guideline's.** 1.155 is
`audit.WADI_XING_SKEW`, a project value on H1's word *"perpendicular"*:

| Tolerance | Deviation from square | Runs | Contact |
|---:|---:|---:|---:|
| 1.000 | 0° | 719 | 57.14 km |
| **1.155** | **30°** | **561** | **47.27 km** |
| 1.500 | 48° | 276 | 28.57 km |
| 2.000 | 60° | 147 | 18.47 km |
| 3.000 | 71° | 49 | 7.89 km |
| 4.000 | 76° | 18 | 3.36 km |

### 2d. What survives, and one of them is a major structure

**1,980 runs / 54.78 km of contact are crossings on both tests** and stay, scheduled, with
their G201 §9.3 obligations. Contact p50 **12.9 m**, p90 **60.2 m** — but **91 of them
exceed 100 m of contact, 18.57 km in total**, and the widest is `W11a-C010726` at
**589.7 m** across a channel measured at **520.9 m** wide (E 446,430 N 2,558,676, skew 1.1).

That is legal under H1a and it is **not a pipe detail**. G201-p85 §9.3 requires bed profiles
and cross-sections, 1-in-20/50/100 flood analysis, bed-material grading, long-term bed-level
monitoring, scour analysis and **MoAFWR approval**; G201-p86 adds ductile iron over the
crossing plus 15 m each side, anti-flotation design and protection to PAM-STD-404.
Ninety-one of those is a work package, and the register carries `APPROVED = 0` on every one.

### 2e. What the flagged ground actually is

`criteria.HAZARD_WADI_CLASSES = (4, 5, 6)` is an **AR&R flood-hazard** classification keyed
on danger to people and vehicles, standing in for a **scour** criterion. Verbatim from the
source:

> *"**Wadis and Flood-Prone Areas**: Locating pipelines and associated chambers in wadis or
> areas subject to washout during heavy storms **must be avoided**."* — G203-p30 §4.4.1(i)(a)

> *"Locating pipelines and associated chambers in wadis and areas subject to washout during
> heavy storms **shall be avoided**."* — G203-p33 §4.6.2

| Hazard class under the along-wadi contacts | contact |
|---|---:|
| 4 — unsafe for people & vehicles, ≈1.2 m of water | 15.89 km |
| 5 | 26.35 km |
| 6 | 5.03 km |

| Local channel width (2 × max distance to dry ground) | runs | contact | contact p50 |
|---|---:|---:|---:|
| under 10 m | 120 | 1.41 km | 10 m |
| 10 – 20 m | 113 | 3.57 km | 25 m |
| 20 – 40 m | 126 | 6.38 km | 43 m |
| 40 – 80 m | 111 | 11.68 km | 85 m |
| over 80 m | 91 | 24.23 km | 217 m |

**Median local width 24.7 m against a median contact of 44.3 m.** The ground is a channel
and the corridors are running down it. The class-based substitution is defensible here —
but a third of the length is class 4 alone, and a scour study could remove it (D7).

### 2f. Where they are, by source

| SRC | CONFIDENCE | corridors | km | plots |
|---|---|---:|---:|---:|
| auto_road | derived | 139 | 17.15 | 125 |
| draft | drafted | 207 | 17.03 | 246 |
| draft | provisional | 93 | 6.63 | 111 |
| auto_block | provisional | 49 | 2.45 | 10 |
| auto_link | provisional | 28 | 1.42 | 17 |
| **main_pipe** | **drafted** | **45** | **2.90** | **9** |

**The 2.90 km on the trunk alignment is not ours to re-route.** `SRC = main_pipe` is the
user's own drawing (`SHP/Main Pipe/Main Pipe.shp`). That is decision D1.

---

## 3. What a re-route actually costs

### 3a. The street-network detour — rejected on measurement

Delete the 561 and ask, of each, whether the rest of the corridor network still joins its
own two ends:

| | corridors | km |
|---|---:|---:|
| An alternative path exists | **69** | 3.6 |
| **No alternative at all** | **492** | 44.0 |

For the 69, the detour is **59.17 km of extra corridor** — a median ratio well over 30× the
corridor it replaces — and at the DN200 Table 11 minimum of 5.00 mm/m (G203-p29) it costs up
to **26.94 m of extra invert**, past the 12 m cap twice over.

**There is no parallel dry street.** The corridors run down the wadis because the roads do.
A detour along the road network is not the answer and is not in the patch.

### 3b. The frontage cost is negligible — 0.10 %

Using `s2.PLOT_SERVED_M = 60 m`:

* **518** load-bearing plots front an along-wadi corridor;
* **451 of them have another corridor within 60 m**, median 22.5 m away;
* **67 plots lose every corridor within 60 m: 76.7 m³/d, 0.10 % of 74,701.2 m³/d.**

### 3c. The real cost is the LINK — 14.90 %

A corridor down a wadi is rarely serving the plots beside it. It is carrying everything
behind it.

| | before | after deleting all 561 |
|---|---:|---:|
| Corridor pieces still carrying a corridor | **311** | **626** |
| — counting every node in the published node set | 311 | 755 |
| Load with a route to the trunk (a component holding a `main_pipe` corridor) | **66,960.0 m³/d** | **55,832.9 m³/d** |

**Loss: 11,127.1 m³/d — 14.90 % of the project load.**

*Caveat, stated plainly:* the baseline is already poor. Only 35 of the 311 components hold a
trunk corridor, so **6,283.8 m³/d is stranded before anything is deleted**. That belongs to
`OPEN-S4-1`. It inflates nothing here — the 11,127 is a difference measured on one graph,
both ways.

### 3d. 459 chains, of which 15 matter

Consecutive along-wadi corridors are one route, so the unit is the chain. There are **459**.
Deleting **one** chain and keeping every other corridor:

| Deleting the chain strands | chains | contact | plots |
|---|---:|---:|---:|
| **nothing at all** | **292** | 27.63 km | 183 |
| under 10 m³/d | 123 | 11.59 km | 178 |
| 10 – 100 m³/d | 29 | 6.00 km | 133 |
| 100 – 500 m³/d | 5 | 0.42 km | 0 |
| **over 500 m³/d** | **10** | 1.63 km | 24 |

**292 chains — 27.63 km, 58 % of the whole problem — can be deleted for nothing at all.**
The marginal figures do not add: chains in series on one route each carry the same load.

The ten chains over 500 m³/d are one place, between E 451,456 – 453,697 and
N 2,565,794 – 2,566,633 on the main wadi through Ibri, and **all ten are drafted lines**.

### 3e. The severance is metres wide

For each chain that strands load, take the piece it orphans and the nearest piece that still
reaches the trunk, and measure the straight link between them:

| The link is | chains | load behind them | median gap |
|---|---:|---:|---:|
| **clear of the wadi** | 27 | 11,930.0 m³/d | **12.3 m** |
| **a square crossing** (schedulable under H1a) | 19 | 338.2 m³/d | **11.6 m** |
| still along a wadi | 60 | 854.5 m³/d | 37.7 m |
| no trunk-connected corridor within 1.5 km | 25 | 108.4 m³/d | — |
| nothing orphaned | 36 | 111.9 m³/d | — |

**The ten chains that strand over 500 m³/d each resolve to TWO links** — 13.0 m at
E 449,938 N 2,567,622 and 4.5 m at E 452,697 N 2,566,173 — together restoring
**10,833 m³/d**. Both are clear of the hazard grid. Figure **FR04**.

A 13 m gap is wider than `contract.NODE_MERGE_M` (3.0 m) and wider than
`s2.CORRIDOR_CUT_M` (4.0 m), so the cut-hole heal cannot reach it, and `stitch()` only
stitches skeleton pockets. It falls through both. **This is the 4 m cut hole one size up.**

### 3f. What it costs in depth — screening only

Stage 6 has not run, so there are no design levels. What can be measured is the change in
**flow-path length to the trunk** for every load-bearing corridor before and after; times
the minimum gradient for the diameter (G203-p29 Table 11), that bounds the extra invert at
the far end.

Extra path: **p50 0 m, p90 1,077 m, max 7,400 m; load-weighted mean 338 m.**

| Gradient used | mean extra invert | p90 | max | load past the 12 m cap |
|---|---:|---:|---:|---:|
| DN200, 5.00 mm/m — steepest minimum, worst case | 1.69 m | 5.38 m | 37.00 m | 4,291 m³/d |
| DN600, 1.25 mm/m | 0.42 m | 1.35 m | 9.25 m | **0** |
| DN900+, 0.75 mm/m — Table 11 floor | 0.25 m | 0.81 m | 5.55 m | **0** |

**The DN200 row is the bound, not the answer.** A flow path over a kilometre long is a sub
main or a trunk, and Table 11 gives it 1.25 mm/m or less; G203-p22 Table 6 would not allow
DN200 there anyway. **Nothing approaches H4 on a realistic diameter — and this must be
re-checked once stage 6 has run.**

---

## 4. The exact patch to `s2_corridors.py`

Four changes. **Change B is the one that matters**; the rest exist so B does not make the
network worse.

### Change A — `WadiMask`: carry the coverage and the distance to dry ground

```python
# BEFORE — W11a/py/s2_corridors.py, class WadiMask
        self.mask = np.zeros((h, w), dtype=bool)
        lo = min(classes) - 0.5      # >= 4 on a grid whose valid values are integers 1..6
        for r0 in range(0, h, strip):
            r1 = min(h, r0 + strip)
            sub = rasterio.windows.Window(win.col_off, win.row_off + r0, w, r1 - r0)
            a = self.ds.read(1, window=sub)
            self.mask[r0:r1] = np.isfinite(a) & (a > lo)
        self.ds.close()
        self.h, self.w = h, w
        self.wadi_cells = int(self.mask.sum())

    def at(self, xs: np.ndarray, ys: np.ndarray) -> np.ndarray:
        """Vectorised. Outside the window is dry, matching HazardSampler's 'no value = dry'
        (user 2026-08-19) and audit.r4's treatment of a non-finite sample."""
        col = ((np.asarray(xs) - self.tr.c) / self.tr.a).astype(np.int64)
        row = ((np.asarray(ys) - self.tr.f) / self.tr.e).astype(np.int64)
        ok = (row >= 0) & (col >= 0) & (row < self.h) & (col < self.w)
        out = np.zeros(len(col), dtype=bool)
        if ok.any():
            out[ok] = self.mask[row[ok], col[ok]]
        return out
```

```python
# AFTER
        # THREE arrays, not one.  `mask` is hazard class >= 4; `known` is "this cell has an
        # answer at all"; `dnear` is metres to the nearest KNOWN NON-WADI cell.
        #
        # `known` cannot come from a finiteness test.  The declared nodata is -9999.0 and
        # np.isfinite(-9999.0) is True, so `a > lo` scores nodata as NOT a wadi and the run
        # reports a clean result for ground it never tested.  Measured on the layer
        # published 2026-09-02: 807,083 of 1,528,113 corridor samples (52.82 %) are nodata
        # or off the window, and 6,774 corridors have no answer anywhere on them.
        # Philosophy sec 3: the untested fraction is published beside every wadi result.
        # The FLAG does not change - unknown still cannot be deleted, because we do not
        # know - but the SILENCE does.
        #
        # `dnear` is the measurement H1a item 1 actually asks for.  "The shortest crossing
        # available at that point" is the local channel width, and 2 x the MAXIMUM of this
        # field over a contact recovers it: on a square crossing of a band of width W the
        # distance to dry ground ramps 0 -> W/2 -> 0 along the pipe, so the max gives W and
        # the median gives W/2.  With the median a PERFECT crossing scores skew 2.00 and is
        # condemned; with the max, skew = 1/cos(deviation) exactly, so WADI_XING_SKEW =
        # 1.155 means 30 deg off square, which is what it is defined to be.
        #
        # Built in strips with a 500 m halo so peak memory is one strip, and stored as
        # uint16 decimetres (capped 6,553.5 m): 280 MB on this boundary against 560 MB for
        # float32, and the grid is 3.0 m, so a tenth of a metre is already finer than the
        # data.
        from scipy import ndimage        # already a dependency of the report toolkit
        self.mask = np.zeros((h, w), dtype=bool)
        self.known = np.zeros((h, w), dtype=bool)
        lo = min(classes) - 0.5      # >= 4 on a grid whose valid values are integers 1..6
        nod = self.ds.nodata
        for r0 in range(0, h, strip):
            r1 = min(h, r0 + strip)
            sub = rasterio.windows.Window(win.col_off, win.row_off + r0, w, r1 - r0)
            a = self.ds.read(1, window=sub)
            k = np.isfinite(a) & (a != nod) & (a > -1000.0)
            self.known[r0:r1] = k
            self.mask[r0:r1] = k & (a > lo)
        self.ds.close()
        self.h, self.w = h, w
        self.cell = abs(self.tr.a)
        self.wadi_cells = int(self.mask.sum())
        self.known_cells = int(self.known.sum())
        dry = self.known & ~self.mask
        halo = int(500.0 / self.cell)
        self.dnear = np.zeros((h, w), dtype=np.uint16)
        for r0 in range(0, h, strip):
            r1 = min(h, r0 + strip)
            a0, b0 = max(0, r0 - halo), min(h, r1 + halo)
            s = dry[a0:b0]
            d = (ndimage.distance_transform_edt(~s, sampling=self.cell)
                 if s.any() else np.full(s.shape, 6553.5))
            self.dnear[r0:r1] = np.clip(d[r0 - a0:r1 - a0] * 10.0, 0, 65535).astype(np.uint16)

    def _rc(self, xs, ys):
        col = ((np.asarray(xs) - self.tr.c) / self.tr.a).astype(np.int64)
        row = ((np.asarray(ys) - self.tr.f) / self.tr.e).astype(np.int64)
        return row, col, (row >= 0) & (col >= 0) & (row < self.h) & (col < self.w)

    def at(self, xs: np.ndarray, ys: np.ndarray) -> np.ndarray:
        """Vectorised.  UNCHANGED IN MEANING: a cell with no answer is not deleted, because
        an untested cell is not a known wadi.  What changes is that the silence is now
        countable - `known_at` says how much of an answer there was."""
        row, col, ok = self._rc(xs, ys)
        out = np.zeros(len(np.atleast_1d(col)), dtype=bool)
        if ok.any():
            out[ok] = self.mask[row[ok], col[ok]]
        return out

    def known_at(self, xs: np.ndarray, ys: np.ndarray) -> np.ndarray:
        """Does the grid have an answer here at all?  Off the window is UNKNOWN, not dry."""
        row, col, ok = self._rc(xs, ys)
        out = np.zeros(len(np.atleast_1d(col)), dtype=bool)
        if ok.any():
            out[ok] = self.known[row[ok], col[ok]]
        return out

    def d_dry(self, xs: np.ndarray, ys: np.ndarray) -> np.ndarray:
        """Metres to the nearest KNOWN NON-WADI cell."""
        row, col, ok = self._rc(xs, ys)
        out = np.full(len(np.atleast_1d(col)), np.inf)
        if ok.any():
            out[ok] = self.dnear[row[ok], col[ok]] / 10.0
        return out
```

### Change B — `_square_crossing`: measure the shortest crossing, not the perpendicular probe

```python
# BEFORE — W11a/py/s2_corridors.py, def _square_crossing (line 223)
    contact = b - a
    mid = 0.5 * (a + b)
    p0 = g.interpolate(max(0.0, mid - 1.0))
    p1 = g.interpolate(min(g.length, mid + 1.0))
    vx, vy = p1.x - p0.x, p1.y - p0.y
    m = math.hypot(vx, vy) or 1.0
    nx_, ny_ = -vy / m, vx / m
    c = g.interpolate(mid)
    ts = np.arange(0.0, WADI_PROBE_M, WADI_STEP_M)
    width = 0.0
    for sgn in (1.0, -1.0):
        on = wadi.at(c.x + sgn * ts * nx_, c.y + sgn * ts * ny_)
        off = np.where(~on)[0]
        width += float(off[0] * WADI_STEP_M) if len(off) else WADI_PROBE_M
    return contact <= WADI_XING_SKEW * max(width, WADI_STEP_M), contact, width
```

```python
# AFTER
    """H1a item 1, as WRITTEN: the contact against 'the SHORTEST CROSSING AVAILABLE at that
    point' - not against the band width along the pipe's own normal.

    WHY THIS CHANGED, measured on the layers published 2026-09-02.  The perpendicular probe
    reports the band width in ONE direction from ONE station, capped at 2 x WADI_PROBE_M.
    It hit that cap on 506 of 2,541 on-wadi runs and hit it BOTH ways on 58, returning
    width = 800 m - at which the test passes any contact up to 924 m, longer than anything
    in the network.  W11a-C010611 is the clean case: 651.8 m of continuous contact, probe
    width 800 m, and dry ground 41.7 m away.  Under the probe, ONE run of 2,541 fails.
    Under the clause as written, 561 fail - 47.58 km of corridor - and audit.r4 passes
    every one of them today.

    THE STATISTIC IS THE MAXIMUM AND THAT IS NOT A TASTE.  On a perfect perpendicular
    crossing of a band of width W the distance to dry ground ramps 0 -> W/2 -> 0 along the
    pipe.  2 x MEDIAN therefore recovers W/2 and scores a PERFECT crossing at skew 2.00 -
    over the tolerance, condemning every square crossing in the network.  2 x MAX recovers
    W, and skew = 1/cos(deviation) exactly, so WADI_XING_SKEW = 1.155 means 30 deg off
    square, which is what it is defined to be.  The choice is worth 24.64 km: median flags
    1,008 runs / 71.78 km, max flags 561 / 47.27 km, and the max set is a strict subset.

    The perpendicular probe is KEPT and MEASURED, because audit.r4 still applies it: while
    the two differ, s2 deletes more than the auditor demands and the run must say so out
    loud rather than leave the divergence in a comment.  See OPEN ITEMS.
    """
    contact = (b - a) + WADI_STEP_M          # audit._r4_classify's own definition
    n = max(2, int(math.ceil((b - a) / WADI_STEP_M)) + 1)
    d = np.linspace(a, b, n)
    xy = shapely.get_coordinates(shapely.line_interpolate_point(g, d))
    dd = wadi.d_dry(xy[:, 0], xy[:, 1])
    dd = dd[np.isfinite(dd)]
    xing = 2.0 * float(dd.max()) if dd.size else float("inf")

    # the probe the auditor still uses, measured only so the divergence is reportable
    mid = 0.5 * (a + b)
    p0 = g.interpolate(max(0.0, mid - 1.0))
    p1 = g.interpolate(min(g.length, mid + 1.0))
    vx, vy = p1.x - p0.x, p1.y - p0.y
    m = math.hypot(vx, vy) or 1.0
    nx_, ny_ = -vy / m, vx / m
    c = g.interpolate(mid)
    ts = np.arange(0.0, WADI_PROBE_M, WADI_STEP_M)
    probe = 0.0
    for sgn in (1.0, -1.0):
        on = wadi.at(c.x + sgn * ts * nx_, c.y + sgn * ts * ny_)
        off = np.where(~on)[0]
        probe += float(off[0] * WADI_STEP_M) if len(off) else WADI_PROBE_M
    is_x = contact <= WADI_XING_SKEW * max(xing, WADI_STEP_M)
    if is_x != (contact <= WADI_XING_SKEW * max(probe, WADI_STEP_M)):
        _XING_DIVERGENCE.append((float(contact), float(xing), float(probe)))
    return is_x, contact, xing
```

with one module-level list beside the other constants:

```python
_XING_DIVERGENCE: List[Tuple[float, float, float]] = []
# (contact, shortest-crossing, perpendicular-probe) for every run the two tests disagree
# on.  audit.r4 applies the probe; this stage applies the clause.  A divergence is not a
# bug in either - it is the reason the auditor has to be fixed too - but it must be a
# PUBLISHED count, never a silent one.
```

and, in `build()` beside the removal summary:

```python
    res["metrics"]["xing_test_divergence"] = len(_XING_DIVERGENCE)
    if _XING_DIVERGENCE:
        print(f"      along/across: this stage and audit.r4 disagree on "
              f"{len(_XING_DIVERGENCE):,} runs. s2 applies philosophy H1a item 1 (contact "
              f"vs the SHORTEST crossing available, 2 x max distance to dry ground); "
              f"audit.r4 probes perpendicular to the pipe, capped at "
              f"{WADI_PROBE_M:.0f} m. Every divergence here is s2 deleting MORE, so R4 "
              f"still passes - but the auditor is not independently confirming H1a until "
              f"it is fixed too.")
```

### Change C — publish the coverage the stage now knows

```python
# ADD in build(), where ON_WADI_M is measured (about line 1447)
    on_wadi: List[float] = []
    untested: List[float] = []
    for g in geoms:
        L = g.length
        k = max(2, int(math.ceil(L / WADI_STEP_M)) + 1)
        xy = shapely.get_coordinates(
            shapely.line_interpolate_point(g, np.linspace(0.0, L, k)))
        on_wadi.append(round(float(wadi.at(xy[:, 0], xy[:, 1]).mean()) * L, 3))
        untested.append(round(float((~wadi.known_at(xy[:, 0], xy[:, 1])).mean()) * L, 3))
    cor["ON_WADI_M"] = on_wadi
    # NOT a new column on the published layer - contract.CORRIDORS does not carry one and
    # inventing a field here would break the schema check.  It is a METRIC, and philosophy
    # sec 3 makes it mandatory beside every wadi number.
    res["metrics"]["untested_km"] = round(float(np.sum(untested)) / 1000.0, 3)
    res["metrics"]["untested_pct_of_length"] = round(
        100.0 * float(np.sum(untested)) / max(sum(g.length for g in geoms), 1.0), 2)
    res["metrics"]["corridors_with_no_hazard_answer"] = int(
        sum(1 for u, g in zip(untested, geoms) if u >= g.length - 1e-6))
    print(f"      hazard COVERAGE: {res['metrics']['untested_pct_of_length']:.1f} % of the "
          f"published corridor length has no answer from the 50-year grid "
          f"({res['metrics']['corridors_with_no_hazard_answer']:,} corridors have none at "
          f"all). Every wadi number above is a statement about the rest.")
```

*If a field on the layer is wanted rather than a metric, `contract.CORRIDORS` has to gain
`UNTESTED_M` first — that file belongs to another agent and I have not touched it.*

### Change D — heal the severance the deletion creates

Applying B without D takes the corridor network from **311 pieces to 626** and 14.90 % of
the load loses its route to the trunk. That is the reason the wadi rule was softened in the
first place, and repeating it would be the same mistake in a new place.

New function beside `stitch()`, called in `build()` immediately after `apply_exclusions` and
before `mint_nodes`:

```python
HEAL_CAP_M = 50.0
# How far a severance heal may reach.  A PROJECT value, and the answer moves with it:
# measured on the layers published 2026-09-02, a 10 m cap leaves 2,449 m3/d off the trunk,
# 25 m recovers +570 against the published baseline, 50 m recovers +976 and 400 m recovers
# +3,339 for eight times the connector.  50 m is where the curve turns; anything longer is
# a route, not a heal, and belongs to a person.  `stitch()` reaches 400 m because it is
# connecting a whole unserved pocket, which is a different job.


def heal_severances(lines: List[LineString], srcs: List[str], on_dual: List[float],
                    wadi: Optional[WadiMask], cap: float = HEAL_CAP_M
                    ) -> Tuple[List[LineString], List[str], List[float], Dict]:
    """Re-join what H1 severed, with links that are themselves legal.

    H1 is applied by deleting ground, and deleting ground cuts routes.  Measured on the
    layers published 2026-09-02: removing the 561 corridors that run ALONG a wadi takes the
    network from 311 pieces to 626 and drops the load with a route to the trunk from 66,960
    to 55,833 m3/d.  But the severance is METRES wide - the ten chains that strand more
    than 500 m3/d each resolve to TWO links, 13.0 m and 4.5 m, both clear of the hazard
    grid, together worth 10,833 m3/d.  A 13 m gap is wider than CORRIDOR_CUT_M (4.0 m) and
    wider than contract.NODE_MERGE_M (3.0 m), so the cut-hole heal cannot reach it and
    stitch() only stitches skeleton pockets: it falls through both.  This is the 4 m cut
    hole one size up.

    THE LINK MUST ITSELF BE LEGAL.  A heal that runs down a wadi has re-created the thing
    that was deleted, so every candidate is tested with the rule Change B applies and
    dropped if it fails.  Measured: at the 50 m cap, 150 links, 2.573 km, of which 111 are
    clear of the hazard grid and 39 are square crossings that go into the schedule.

    RIGHT OF WAY IS NOT PROVEN.  129 of the 150 cross no registered plot in
    SHP/MoHUP_DATA/MoH_Plots.shp - they run in the street - but 21 (0.507 km, median
    21.3 m) cross one and need an answer.  Every link is written with SRC = auto_link,
    CONFIDENCE = provisional (SRC_CONFIDENCE_CEILING will not allow better), and the 21 are
    listed in the report so a person decides, not this function.
    """
    import networkx as nx
    if not lines:
        return [], [], [], {"links": 0}

    idx = contract.NodeIndex()
    G = nx.Graph()
    ends = []
    for g in lines:
        c = list(g.coords)
        a = idx.get_or_create(c[0][0], c[0][1])
        b = idx.get_or_create(c[-1][0], c[-1][1])
        ends.append((a, b))
        G.add_node(a); G.add_node(b)
        if a != b:
            G.add_edge(a, b)
    comp: Dict[int, int] = {}
    for k, cc in enumerate(nx.connected_components(G)):
        for n in cc:
            comp[n] = k

    # a piece that can reach the trunk is "landed"; everything else is looking for a link
    landed = {comp[ends[i][0]] for i, s in enumerate(srcs) if s == "main_pipe"}
    if not landed:                       # no main pipe in the set - heal to the largest
        landed = {int(pd.Series([comp[a] for a, _ in ends]).value_counts().index[0])}

    new_g: List[LineString] = []
    rep = {"links": 0, "km": 0.0, "clear": 0, "crossing": 0, "refused_illegal": 0,
           "refused_far": 0, "still_severed": 0}
    for _ in range(60):
        cur = np.array([comp[a] for a, _ in ends])
        free = sorted({int(c) for c in cur} - landed,
                      key=lambda c: -sum(lines[i].length for i in np.where(cur == c)[0]))
        if not free:
            break
        tgt_i = [i for i in range(len(lines)) if cur[i] in landed]
        if not tgt_i:
            break
        tree = STRtree([lines[i] for i in tgt_i])
        made = 0
        for c in free:
            gsrc = unary_union([lines[i] for i in np.where(cur == c)[0]])
            hit = np.atleast_1d(tree.query_nearest(gsrc, all_matches=False))
            if not hit.size:
                continue
            p, q = nearest_points(gsrc, lines[tgt_i[int(hit[0])]])
            if p.distance(q) < STITCH_MIN_M:
                continue                          # already meeting; noding will join them
            link = LineString([p, q])
            if link.length > cap:
                rep["refused_far"] += 1
                continue
            ok, why = _link_is_legal(link, wadi)
            if not ok:
                rep["refused_illegal"] += 1
                continue
            new_g.append(link)
            rep["links"] += 1
            rep["km"] += link.length / 1000.0
            rep["clear" if why == "clear" else "crossing"] += 1
            for n, cc in list(comp.items()):      # merge the two components and carry on
                if cc == c:
                    comp[n] = min(landed)
            landed.add(c)
            made += 1
        if not made:
            break
    rep["still_severed"] = len({comp[a] for a, _ in ends} - landed)
    rep["km"] = round(rep["km"], 4)
    return new_g, ["auto_link"] * len(new_g), [0.0] * len(new_g), rep


def _link_is_legal(link: LineString, wadi: Optional[WadiMask]) -> Tuple[bool, str]:
    """A generated link is subject to H1 like everything else: clear, or a square crossing
    under H1a - never a third thing.  Same statistic as _square_crossing (2 x MAX distance
    to dry ground over the ON-WADI samples); taking it at the link's midpoint instead is
    worse still, because on a 4 m link the midpoint often lands on a dry cell and returns a
    shortest crossing of zero."""
    if wadi is None:
        return True, "clear"
    n = max(2, int(math.ceil(link.length / WADI_STEP_M)) + 1)
    xy = shapely.get_coordinates(
        shapely.line_interpolate_point(link, np.linspace(0.0, link.length, n)))
    on = wadi.at(xy[:, 0], xy[:, 1])
    if not on.any():
        return True, "clear"
    contact = float(on.mean()) * link.length + WADI_STEP_M
    dd = wadi.d_dry(xy[on, 0], xy[on, 1])
    dd = dd[np.isfinite(dd)]
    xing = 2.0 * float(dd.max()) if dd.size else float("inf")
    return contact <= WADI_XING_SKEW * max(xing, WADI_STEP_M), "crossing"
```

and in `build()`:

```python
    kept, kept_src, kept_dual, removed = apply_exclusions(
        noded, noded_src, band, band_prep, dual_lines, dual_tree, wadi)

    # ---- heal what H1 severed, before identity is minted -------------------------------
    heal_g, heal_s, heal_d, heal_rep = heal_severances(kept, kept_src, kept_dual, wadi)
    kept += heal_g; kept_src += heal_s; kept_dual += heal_d
    res["metrics"]["severance_heal"] = heal_rep
    print(f"      severance heal: {heal_rep['links']:,} links, {heal_rep['km']:.3f} km "
          f"({heal_rep['clear']:,} clear of the hazard grid, {heal_rep['crossing']:,} "
          f"square crossings that go into the schedule); {heal_rep['refused_illegal']:,} "
          f"candidates refused because the LINK would itself run along a wadi, "
          f"{heal_rep['refused_far']:,} because they exceed the {HEAL_CAP_M:.0f} m cap; "
          f"{heal_rep['still_severed']:,} pieces still have no legal way back")
```

The healed links are `auto_link` / `provisional`, so `SRC_CONFIDENCE_CEILING` already blocks
promotion, `_mint_cross_ids` already schedules the ones that touch wadi ground, and the
removal funnel already carries the extra deletions under the existing `"wadi (along)"`
reason.

---

## 5. What the patch recovers

Simulated on the published layers (`python W11a/report/fig_wadi_reroute.py --patch`).

| Heal cap | links | link km | pieces | trunk-connected load | vs published |
|---:|---:|---:|---:|---:|---:|
| — (published baseline) | — | — | **311** | **66,960.0 m³/d** | — |
| delete only, no heal | — | — | 626 | 55,832.9 | −11,127.1 |
| 10 m | 60 | 0.338 | 566 | 64,510.9 | −2,449.2 |
| 25 m | 107 | 1.097 | 519 | 67,530.3 | +570.3 |
| **50 m** | **150** | **2.573** | **476** | **67,935.7** | **+975.6** |
| 100 m | 226 | 7.409 | 400 | 69,886.1 | +2,926.0 |
| 200 m | 270 | 13.096 | 356 | 70,162.6 | +3,202.6 |
| 400 m | 286 | 19.359 | 340 | 70,298.9 | +3,338.9 |

**At the 50 m cap the patch removes 47.58 km of illegal corridor, adds 2.57 km of legal
connector, and finishes with 976 m³/d MORE load connected to the trunk than the layer
published today.** 111 of the 150 links are clear of the hazard grid, 39 are square
crossings that enter the schedule, median link 13.5 m.

Three honest qualifications:

* **Most of the gain above baseline is not a wadi fix.** The heal closes gaps that were
  already there — which is why the 100 m and 200 m caps go on gaining. **Change D is worth
  applying on its own merits, independently of Change B**, and its benefit should not be
  claimed for the wadi rule.
* **The piece count gets worse, not better** — 311 → 476 at the 50 m cap. The extra pieces
  are fragments that carried no load and had no trunk route before either; the load number
  is the one that moves in the right direction. **H15 is not satisfied by this stage, and
  was not satisfied before it.**
* **21 of the 150 links cross a registered plot** (0.507 km, median 21.3 m). 129 cross none
  — they run in the street. The 21 need a right-of-way answer before they are built.

---

## 6. What needs a decision, and what needs data we do not have

| # | Item | Size | Who |
|---|---|---|---|
| **D1** | **45 trunk corridors, 2.90 km, run ALONG a wadi.** `SRC = main_pipe` is the user's own drawn alignment; the patch deliberately does not touch it. Worst: `W11a-C025945`, **361 m** of contact at E 450,484 N 2,571,407; then `W11a-C026200` 234 m at E 450,073 N 2,569,431 with `W11a-C026199` 146 m at E 450,079 N 2,569,621 — the same north–south leg, 380 m between them; then `W11a-C026052` 215 m at E 452,686 N 2,573,183 and `W11a-C026076` 196 m at E 449,835 N 2,568,677 | 45 corridors | **User / draftsman** |
| **D2** | **The ten chains that strand over 500 m³/d resolve to two links** — 13.0 m at **E 449,938 N 2,567,622** and 4.5 m at **E 452,697 N 2,566,173**, together worth **10,833 m³/d**. Both are clear of the hazard grid. Confirm both are real ground on the imagery before that load is routed through them | 2 links | **User**, on the imagery |
| **D3** | **60 chains still have no legal link** (median gap 37.7 m, 854.5 m³/d behind them) and **25 more have no trunk-connected corridor within 1.5 km** (108.4 m³/d). Worst: the chain at **E 466,655 N 2,565,546**, 252.1 m³/d, whose 4.0 m heal would itself run along the wadi; then E 449,297 N 2,567,819 (85.1 m³/d, 60.5 m gap) and E 457,604 N 2,567,053 (49.9 m³/d, 274 m gap, 1.6 km of chain). These are philosophy §3's fourth resolution — a station and a rising main across, another system, or not serving | ~963 m³/d | **Client**, on life-cycle cost |
| **D4** | **91 scheduled wadi crossings exceed 100 m of contact, 18.57 km in total**, the widest `W11a-C010726` at **589.7 m** across a 520.9 m channel (E 446,430 N 2,558,676). Legal under H1a, but each carries the full G201 §9.3 package — bed profile and cross-sections, 1-in-20/50/100 flood levels, bed material, scour analysis, MoAFWR approval, DI plus 15 m each side, anti-flotation, PAM-STD-404. `APPROVED = 0` on every row | 91 crossings | **Client / MoAFWR** |
| **D5** | **21 of the 150 healing links cross a registered plot.** G203-p17 §3.2 puts the connection in the public right-of-way; at concept scale we cannot show one exists | 0.507 km | **User**, with the GIS land-use data |
| **D6** | **The skew tolerance and the statistic are both ours.** 1.155 with `2 × max` gives 47.27 km; 2.000 gives 18.47 km; the `2 × median` form I rejected gives 71.78 km. Record 1.155-with-max in `02` as a deviation, with H1's *"perpendicular"* and the ramp argument beside it | 29 km of headroom | **User** |
| **D7** | **`HAZARD_WADI_CLASSES = (4,5,6)` is a flood-SAFETY classification standing in for a SCOUR criterion.** 15.89 km of the 47.27 is class 4 alone — 1.2 m of water in a 50-year event. A scour-depth study could take a third of the problem away | 15.89 km | **Client / MoAFWR**, per G201-p85 |
| **D8** | **52.82 % of the corridor network has no hazard answer**, and 6,774 corridors have none anywhere on them. G201-p85 §9.3 already obliges the designer to obtain wadi bed profiles, cross-sections and 1-in-20/50/100 flood levels from **CAA and MoAFWR** for every crossing. Request full 50-year coverage in the same letter | half the network | **Client / data request** |

---

## 7. Defects found elsewhere — reported, not fixed

None of these files is mine to edit.

| Where | Defect | Why it matters |
|---|---|---|
| **`W11a/py/w11a/audit.py`, `_r4_classify`** | R4's along/across test is the same perpendicular probe with the same 400 m cap. **It is the specification, and it certifies 2,495 crossings of which 561 run along a wadi.** Change B must land here too, or `s2` enforces a rule the auditor does not check — the "W8's engineering was carried into W10 and W8's auditor was not" failure, inverted | R4 currently PASSES a blocking regression it should FAIL |
| **`W11a/py/w11a/audit.py`, the probe** | `off = np.where(pknown & ~pon)` requires *known* dry ground to stop the probe, while `s2.WadiMask.at` stops at the first non-wadi sample including nodata. Two samplers, two widths on the same run — 615 runs cap under the auditor's convention against 506 under `s2`'s. `s2`'s own comment says the auditor is the specification precisely to prevent this | the parity `s2` asserts is not actually held |
| **`_BRAIN/08_DESIGN_PHILOSOPHY.md`, H1a item 1** | *"within the stated skew tolerance of the shortest crossing available at that point"* does not say how the shortest crossing is measured, and the two obvious estimators differ by a factor of two (§2b). Add one line: *the local channel width, taken as twice the maximum distance to non-wadi ground over the contact* | 24.64 km turns on it |
| **`_BRAIN/08_DESIGN_PHILOSOPHY.md`, H1a item 3** | It says the 1.5 m cover figure is *"G203-p52 §8.2.4, which sits in the FORCE MAIN section"* and that G201-p86 *"raises it to 2.0 m in soft soil"* for a force main. Read back today, **G201-p86's *"Wadi crossings in soft soil will be constructed with a minimum cover of 2 meters"* sits in §9.3 *Wadi crossings* and is not qualified to force mains** — the valve-chamber and air-valve sentences around it are, that one is not. The project decision to adopt 1.5 m for gravity may still be right; the citation supporting it is weaker than the file says | affects the cover on all 2,539 scheduled crossings |
| **`W11a/shp/W11a.gpkg` [crossings] — overwritten in place** | Stage 2 writes a corridor-referenced register (2,539 rows, `EDGE_UID = W11a-C…`, all `OBSTACLE = wadi`). At 15:44 the same layer holds a **reach**-referenced register (3,290 rows, `EDGE_UID = E…`, 3,239 wadi + 51 dual), and **10 of stage 2's `CROSS_ID`s no longer resolve to any row** — `W11a-XG00766, -01223, -01440, -01623, -01625, -01661, -01941, -02149, -02162, -02459`. Re-referencing the schedule to reaches is right; doing it by replacing the layer destroys the corridor-level register, and after that R4 can no longer be run against the corridors at all. Write the reach register to its own layer, or keep both keys | R4 on the corridors went PASS → FAIL without a corridor changing |
| **`W11a/shp/W11a.gpkg` [corridors], `USED`** | `USED = 0` on all 26,450 rows. Already reported in `TERTIARY_AND_WADI_CHAMBERS` §1d and still true | a corridor carrying no pipe cannot be told from one deliberately unused |
| **`s2_corridors.py` module docstring, line 78** | *"EVERY on-wadi run is deleted at this stage, so `ON_WADI_M` is 0 on every published corridor"* — the code and the layer both say otherwise (2,539 corridors, 98.99 km). The docstring predates the H1a crossing rule | a docstring that contradicts its own output |

---

## 8. Figures

Drawn by `W11a/report/fig_wadi_reroute.py` into `W11a/report/img/`, through `figkit`, from
copies of the published layers, with the source line and the project assumptions on every
one. `img/*.png` is gitignored by repo policy (2.8 and 4.1 MB for the two maps), so the
committed copies are the document-sized ones in `W11a/report/img_doc/`, built by
`python W11a/report/img_for_doc.py`.

| File | What it shows |
|---|---|
| **`FR01_along_wadi_corridors.png`** | The whole study area: the 54.78 km of contact that is a crossing on either test, the 47.27 km that runs along, the class 4/5/6 ground, and the 52.8 % with no answer drawn as hatch |
| **`FR02_two_tests.png`** | The two tests side by side — 0.03 km against 47.27 km — the rejected median form beside them, and the tolerance swept 1.000 to 4.000 |
| **`FR03_chain_marginal_cost.png`** | 459 chains banded by the load that loses its route to the trunk when each is deleted alone, with the heal outcome beneath |
| **`FR04_severance_heal.png`** | The cluster on the main wadi through Ibri: the along-wadi corridors in red, and the 4.5 m and 13.0 m links that restore 10,833 m³/d |

---

## 9. Every number, and where it came from

| Number | Source |
|---|---|
| 26,450 corridors / 2,234.85 km; `ON_WADI_M` 98.99 km; 2,539 with `CROSS_ID` | `W11a/shp/W11a.gpkg[corridors]`, written 2026-09-02 14:55 |
| 586 removed pieces / 71.02 km, 478 of them `wadi (along)` for 67.12 km | `W11a/shp/W11a_corridors_removed.gpkg[removed]` |
| `R4 PASS … 2,495 scheduled crossing(s)` at 14:20 and `R4 FAIL … 10 wadi crossings with no CROSS_ID` at 15:44, zero "along" in both | `w11a.audit.run_one("R4", …)` against the published `corridors` layer, 2026-09-02 |
| the `crossings` layer went 2,539 corridor-referenced rows → 3,290 reach-referenced rows; 10 ids orphaned | the same GeoPackage, snapshotted at 14:09 and at 15:44 |
| 1,528,113 samples, 807,083 (52.82 %) untested, 6,774 corridors with no answer | 1.5 m sampling of `[corridors]` on `Data/04 Lekhuwair/Hazard_T50y.tif` |
| 2,541 runs, 102.05 km of contact, longest 788.48 m | same, `audit._r4_classify`'s contact definition |
| 561 ALONG / 47.27 km contact / 47.58 km corridor / 518 plots; the tolerance sweep | same, contact ÷ (2 × **max** distance to nearest known non-wadi cell) |
| the median form: 1,008 runs / 71.78 km, a strict superset | same, with the median instead — reported only to be rejected |
| probe fails 1 of 2,541; capped on 506; both ways on 58 | reproduction of `s2._square_crossing` in `fig_wadi_reroute._probe_width` |
| 1,980 crossings survive / 54.78 km; 91 over 100 m / 18.57 km; widest 589.7 m across 520.9 m | the same classification, complemented |
| hazard class split 15.89 / 26.35 / 5.03 km; local width p50 24.7 m | hazard grid point-sampled at each contact midpoint + the distance transform |
| 311 → 626 pieces; 66,960.0 → 55,832.9 m³/d | corridor graph on `US_NODE`/`DS_NODE`; load from `W10/shp/W10_plot_loads.gpkg[plot_loads].Q_AVG_M3D` pinned to the nearest corridor within `PLOT_SERVED_M` = 60 m |
| 67 plots / 76.7 m³/d frontage loss; 451 with another corridor at p50 22.5 m | `sjoin_nearest` of the load-bearing plots before and after |
| 459 chains; the 292/123/29/5/10 bands | one component labelling per chain deletion |
| 27 clear / 19 crossing / 60 still along / 25 no corridor / 36 nothing orphaned | nearest points between each orphan and the trunk-connected set |
| 2 links (13.0 m, 4.5 m) restoring 10,833 m³/d | the 10 chains over 500 m³/d resolve to two distinct link positions |
| 69 of 561 with a street detour; 59.17 km extra; 26.94 m extra invert | Dijkstra on the corridor graph with the ALONG set removed |
| 150 links / 2.573 km / 476 pieces / 67,935.7 m³/d at the 50 m cap, and the sweep | `fig_wadi_reroute.simulate_patch` |
| 129 of 150 links cross no registered plot; 21 cross one (0.507 km, p50 21.3 m) | `sjoin` against `Hydraulic/SHP/MoHUP_DATA/MoH_Plots.shp`, 61,272 plots |
| extra path p90 1,077 m; extra invert 1.69 / 0.42 / 0.25 m load-weighted | multi-source Dijkstra to the `main_pipe` nodes, before and after, × Table 11 |
| DN200 5.00 mm/m, DN600 1.25, DN900+ 0.75 | **G203-p29 Table 11**, read from `Data/PAM-GUD-203 …pdf` 2026-09-02 |
| *"must be avoided"* / *"shall be avoided"* | **G203-p30 §4.4.1(i)(a)** and **G203-p33 §4.6.2**, same read |
| corridor width DN200–500 = 2.00 m | **G203-p32 Table 13**, same read |
| wadi-crossing obligations: bed profile, 1-in-20/50/100, MoAFWR approval, DI + 15 m, PAM-STD-404, 2 m cover in soft soil | **G201-p85–86 §9.3**, read from `Data/PAM-GUD-201 …pdf` 2026-09-02 |
| `WADI_SAMPLE_M` 1.5, `WADI_XING_SKEW` 1.155, `WADI_PROBE_M` 400 | `W11a/py/w11a/audit.py` lines 50–57 — **project values, not guideline** |
| `HAZARD_WADI_CLASSES` (4,5,6), `MH_SNAP_M` 3.0, `TABLE11` | `W8/py/sewnet/criteria.py` |
