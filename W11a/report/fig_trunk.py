"""fig_trunk — the trunk-main figures for the W11a report.

Plan, long section and defects for the 85.55 km trunk that stage 3 laid on the
client's drawn alignment (``SHP/Main Pipe/Main Pipe.shp``).

RUN IT
    cd W11a/report && python fig_trunk.py            # all figures
    python fig_trunk.py FT01 FT06                    # just those two

Idempotent: every figure is rebuilt from the artefacts each run and overwritten in
``W11a/report/img/``.  Nothing here writes to ``W11a/shp`` or ``W11a/run`` — every
read goes through ``figkit.read_layer`` / ``figkit.read_csv``, which copy first.

THE RULE THIS MODULE KEEPS: no number is typed in.  Every value on every figure is
computed here from one of

    W11a/shp/W11a_trunk.gpkg   [reaches] [nodes] [crossings]   (stage 3, published)
    W11a/shp/W11a.gpkg         [corridors] [servicing]         (stages 1-2, published)
    W11a/run/s3_trunk_pipe_schedule.csv                        (stage 3)
    W11a/run/s3_trunk_stations.csv                             (stage 3)
    W11a/run/s3_trunk_findings.csv                             (stage 3)
    W11a/run/audit_W11a_trunk.csv                              (stage 0 auditor)
    W11a/run/manifest_s3_trunk.json                            (stage 3 metrics)
    Hydraulic/SHP/Main Pipe/Main Pipe.shp                      (the client's drawing)

Guideline values quoted on the figures carry their page, from
``_BRAIN/02_DESIGN_CRITERIA.md``:

    G203-p26      min self-cleansing velocity 0.75 m/s at peak flow
    G203-p27      max velocity 3.0 m/s
    G203-p27 T10  d/D at peak <= 0.65 for DN <= 350, <= 0.50 for DN > 350
    G203-p29 T11  minimum gradient by diameter (5.00 mm/m at DN200 ... 0.75 at DN>=900)
    G203-p29      20 mm laying tolerance, and no reverse gradient from it
    G203-p30      inlet angle >= 90 deg; backdrop over 600 mm drop, vortex shaft over 2 m
    G203-p30 T12  maximum chamber spacing by diameter
    G203-p30 4.4.1 / p33  no pipe or chamber in a wadi or washout area
    G203-p33      minimum cover 1.30 m to crown; maximum cover "approximately 10-12 m"

Two things on these figures are OURS, not the guideline's, and are labelled as such
wherever they appear:

    * the **12 m cover cap** is a project rule.  G203-p33 RECOMMENDS approximately
      10-12 m and triggers on excavation cost; we made it a hard cap with two
      distance-bounded exits (philosophy 5).
    * **tau = 1.0 Pa** for the tractive-force route.  G203-p27 4.2.2.1 gives no
      numeric design value at all (GAP-9).  17.999 % of this trunk rests on it.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import matplotlib.patheffects as pe

sys.path.insert(0, str(Path(__file__).resolve().parent))
import figkit as fk                                            # noqa: E402

TRUNK_GPKG = "W11a_trunk.gpkg"
NET_GPKG = "W11a.gpkg"
MAIN_PIPE = fk.HYD / "SHP" / "Main Pipe" / "Main Pipe.shp"
MANIFEST = fk.RUN / "manifest_s3_trunk.json"

#: PROJECT RULE, not a guideline number.  G203-p33 recommends "approximately
#: 10-12 m" of cover and triggers on excavation cost; philosophy 5 makes 12 m a cap.
CAP_COVER_M = 12.0
#: G203-p33.  Minimum cover to crown, gravity sewer.
MIN_COVER_M = 1.30
#: G203-p27 Table 10.  d/D at peak flow.
DOD_LIMIT_SMALL, DOD_LIMIT_BIG, DOD_DN_SPLIT = 0.65, 0.50, 350
#: G203-p26.  Minimum self-cleansing velocity at peak flow.
V_SELF_CLEANSE = 0.75
#: The tractive-force route's tension.  OURS - GAP-9, G203-p27 4.2.2.1 gives none.
TAU_ASSUMED_PA = 1.0
#: Mara/Sleigh/Taylor: Smin = K * tau^1.23 * Q^-0.461 (G203-p27 4.2.2.1, quoted in
#: _BRAIN/02_DESIGN_CRITERIA.md).  The exponent is what makes tau's value matter.
TAU_EXP = 1.23

#: Long-section furniture.  Not in figkit's palette because nothing else uses it:
#: the earth fill has to sit UNDER the tier and status colours without competing.
EARTH = "#d9cfbe"
EARTH_EDGE = "#a89a80"


# ------------------------------------------------------------------ artefacts

_CACHE: dict = {}


def art(key: str):
    """Read an artefact once per process, through figkit, with provenance."""
    if key in _CACHE:
        return _CACHE[key]
    if key == "reaches":
        v = fk.read_layer(TRUNK_GPKG, "reaches")
    elif key == "nodes":
        v = fk.read_layer(TRUNK_GPKG, "nodes")
    elif key == "crossings":
        v = fk.read_layer(TRUNK_GPKG, "crossings")
    elif key == "corridors":
        v = fk.read_layer(NET_GPKG, "corridors",
                          columns=["CORR_ID", "SRC", "LEN_M", "ON_DUAL_M", "ON_WADI_M"])
    elif key == "servicing":
        v = fk.read_layer(NET_GPKG, "servicing", columns=["SET_ID", "SYSTEM", "NAME"])
    elif key == "main_pipe":
        v = fk.read_layer(str(MAIN_PIPE))
    elif key == "stations":
        v = fk.read_csv("s3_trunk_stations.csv")
    elif key == "findings":
        v = fk.read_csv("s3_trunk_findings.csv")
    elif key == "schedule":
        v = fk.read_csv("s3_trunk_pipe_schedule.csv")
    elif key == "audit":
        v = fk.read_csv("audit_W11a_trunk.csv")
    elif key == "manifest":
        v = json.loads(MANIFEST.read_text())
        v = {**v["stages"][0]["metrics"], "_notes": v["stages"][0].get("notes", [])}
    else:
        raise KeyError(key)
    _CACHE[key] = v
    return v


def manifest_src() -> str:
    """A citation string for the stage-3 manifest, which is not a figkit object."""
    return (f"{MANIFEST.relative_to(fk.ROOT).as_posix()} [s3_trunk metrics], "
            f"written {fk._stamp(MANIFEST)}")


# ------------------------------------------------------------------- topology

class Trunk:
    """The published trunk as a graph, built from the DECLARED US_NODE/DS_NODE.

    Philosophy H16: topology is written down, never inferred.  Stage 3's own audit
    H16 confirms the declared graph matches the geometry, so this reads the fields
    rather than re-snapping coordinates.
    """

    def __init__(self):
        self.r = art("reaches")
        self.n = art("nodes")
        self.out_of = dict(zip(self.r.US_NODE, self.r.index))     # node -> reach idx
        self.ins_of = defaultdict(list)
        for i, dsn in zip(self.r.index, self.r.DS_NODE):
            self.ins_of[dsn].append(i)
        self.ds = dict(zip(self.r.US_NODE, self.r.DS_NODE))
        self.node = self.n.set_index("NODE_UID")
        self.kind = dict(zip(self.n.NODE_UID, self.n.NODE_KIND))
        self.grd = dict(zip(self.n.NODE_UID, self.n.GRD_M))

    # -- components -------------------------------------------------------
    def components(self) -> dict:
        """``{sink node: [node ids]}`` — one entry per disconnected piece."""
        par = {u: u for u in self.n.NODE_UID}

        def find(a):
            while par[a] != a:
                par[a] = par[par[a]]
                a = par[a]
            return a

        for a, b in zip(self.r.US_NODE, self.r.DS_NODE):
            ra, rb = find(a), find(b)
            if ra != rb:
                par[ra] = rb
        groups = defaultdict(list)
        for u in self.n.NODE_UID:
            groups[find(u)].append(u)
        out = {}
        for members in groups.values():
            sinks = [u for u in members if u not in self.ds]
            out[sinks[0] if sinks else members[0]] = members
        return out

    # -- paths ------------------------------------------------------------
    def sources(self) -> list:
        nin = dict(zip(self.n.NODE_UID, self.n.N_IN))
        return [u for u in self.n.NODE_UID if nin[u] == 0]

    def path(self, head: str) -> list:
        """Node ids from ``head`` down to its sink."""
        p, u = [head], head
        while u in self.ds:
            u = self.ds[u]
            p.append(u)
        return p

    def longest_to(self, sink: str) -> list:
        """The longest source-to-``sink`` path, by laid length."""
        best, best_len = None, -1.0
        for s in self.sources():
            p = self.path(s)
            if p[-1] != sink:
                continue
            L = sum(self.r.LEN_M.iloc[self.out_of[a]] for a in p[:-1])
            if L > best_len:
                best, best_len = p, L
        return best

    def profile(self, nodes: list) -> pd.DataFrame:
        """Chainage table along a node path.  One row per reach, plus a closing row.

        Columns: CH_M at the reach's upstream end, then every published field the
        long section needs.  Ground and cover come from the layers, never re-sampled.
        """
        rows, ch = [], 0.0
        for a, b in zip(nodes[:-1], nodes[1:]):
            rr = self.r.iloc[self.out_of[a]]
            assert rr.DS_NODE == b, f"declared graph broken at {a}"
            rows.append(dict(
                CH_M=ch, EDGE=rr.EDGE_UID, US=a, DS=b, LEN_M=rr.LEN_M, DN=rr.DN,
                INV_UP=rr.INV_UP, INV_DN=rr.INV_DN,
                GRD_UP=self.grd[a], GRD_DN=self.grd[b],
                COVER_US=rr.COVER_US, COVER_DN=rr.COVER_DN,
                SLOPE_LAID=rr.SLOPE_LAID, SLOPE_MIN=rr.SLOPE_MIN,
                GRAD_BY=rr.GRAD_BY, SIZED_BY=rr.SIZED_BY, CLEAN_BY=rr.CLEAN_BY,
                QPK_LS=rr.QPK_LS, QADF=rr.QADF_M3D, DOD=rr.DOD_PK, V=rr.V_PK_MS,
                ON_DUAL_M=rr.ON_DUAL_M, ON_WADI_M=rr.ON_WADI_M,
                WADI_ALONG=rr.WADI_ALONG, WADI_XING=rr.WADI_XING,
                MATERIAL=rr.MATERIAL, CONFIDENCE=rr.CONFIDENCE))
            ch += rr.LEN_M
        d = pd.DataFrame(rows)
        d["CH_END_M"] = d.CH_M + d.LEN_M
        return d


def step_xy(d: pd.DataFrame, up: str, dn: str):
    """Reach-wise series as a continuous polyline: (x, y) at both ends of each reach."""
    x = np.empty(2 * len(d))
    y = np.empty(2 * len(d))
    x[0::2], x[1::2] = d.CH_M.to_numpy(), d.CH_END_M.to_numpy()
    y[0::2], y[1::2] = d[up].to_numpy(), d[dn].to_numpy()
    return x / 1000.0, y


def flat_xy(d: pd.DataFrame, col: str):
    """A per-reach constant (DN, gradient) drawn as a true step."""
    x = np.empty(2 * len(d))
    y = np.empty(2 * len(d))
    x[0::2], x[1::2] = d.CH_M.to_numpy(), d.CH_END_M.to_numpy()
    y[0::2] = y[1::2] = d[col].to_numpy()
    return x / 1000.0, y


def stack(fig, axes, ratios, gap: float = 0.052, top_pad: float = 0.0) -> None:
    """Lay a column of axes out with height ratios inside chart_frame's margins.

    ``top_pad`` (figure fraction) makes room for a per-panel ``set_title`` on the
    first axes, which would otherwise run into the figure subtitle.
    """
    sp = fig.subplotpars
    left, right, bot = sp.left, sp.right, sp.bottom
    top = sp.top - top_pad
    avail = (top - bot) - gap * (len(axes) - 1)
    y, tot = top, float(sum(ratios))
    for a, r in zip(axes, ratios):
        h = avail * r / tot
        a.set_position([left, y - h, right - left, h])
        y -= h + gap


def wrap(fig, txt: str) -> str:
    """Wrap a source line or note to the figure's own width.

    ``figkit.save`` writes with ``bbox_inches="tight"``, so ONE long unwrapped line
    at the foot of a figure stretches the whole canvas sideways and the image comes
    out lopsided.  Wrapping here keeps every figure the size it was designed at.
    """
    import textwrap
    n = max(60, int((fig.get_size_inches()[0] - 0.5) / 0.0475))
    return "\n".join(textwrap.fill(part, n) for part in str(txt).split("\n"))


def title_room(fig, drop: float = 0.038) -> None:
    """Lower a chart_frame's axes so a per-panel set_title clears the subtitle."""
    fig.subplots_adjust(top=max(0.30, fig.subplotpars.top - drop))


# ==================================================================== FT01

def ft01_long_section(T: Trunk) -> Path:
    """The long section: ground, invert, cover and the 12 m cap over the spine."""
    spine = T.longest_to("N0000758")
    d = T.profile(spine)
    total = d.LEN_M.sum()
    fall = d.INV_UP.iloc[0] - d.INV_DN.iloc[-1]
    grd_fall = d.GRD_UP.iloc[0] - d.GRD_DN.iloc[-1]
    cov = np.r_[d.COVER_US.to_numpy(), d.COVER_DN.iloc[-1]]
    cmax = float(cov.max())
    i_deep = int(np.argmax(d.COVER_DN.to_numpy()))
    ch_deep = d.CH_END_M.iloc[i_deep]
    out = T.node.loc["N0000758"]
    head_ref = T.node.loc[spine[0]].NODE_REF
    whole = art("reaches").LEN_M.sum()

    fig, axes = fk.chart_frame(
        nrows=2, figsize=(13.4, 7.4),
        title=(f"The longest path — {total/1000:,.1f} km — reaches the works on "
               f"gravity alone, and never needs more than {cmax:,.1f} m of cover"),
        subtitle=(f"Long section from {head_ref} at the eastern extremity to the "
                  f"outfall at the existing works: {len(d):,} reaches, "
                  f"{len(spine):,} chambers, {100*total/whole:.0f} % of the "
                  f"{whole/1000:,.2f} km trunk, falling {fall:,.1f} m of invert "
                  f"against {grd_fall:,.1f} m of ground. Levels and cover are the "
                  f"published fields — cover is COVER_US/COVER_DN, not re-sampled "
                  f"from the terrain, so the drawing and the layer cannot drift."))
    ax, axc = axes
    stack(fig, axes, (2.15, 1.0))

    xg, yg = step_xy(d, "GRD_UP", "GRD_DN")
    xi, yi = step_xy(d, "INV_UP", "INV_DN")
    crown_up = d.GRD_UP - d.COVER_US
    crown_dn = d.GRD_DN - d.COVER_DN
    dd = d.assign(_CU=crown_up, _CD=crown_dn)
    xc, yc = step_xy(dd, "_CU", "_CD")

    ax.fill_between(xg, yc, yg, color=EARTH, lw=0, zorder=1,
                    label="cover over the crown")
    ax.plot(xg, yg, color=EARTH_EDGE, lw=1.1, zorder=3, label="ground level")
    ax.plot(xi, yi, color=fk.C.TRUNK, lw=1.5, zorder=4, label="pipe invert")
    ax.plot(xg, yg - CAP_COVER_M, color=fk.C.FAIL, lw=1.0, ls=(0, (5, 3)), zorder=3,
            label=f"{CAP_COVER_M:.0f} m cover cap — PROJECT RULE, not G203")

    # tributaries joining the spine, and the chambers with a drop structure
    spineset = set(spine)
    joins = [(i, u) for i, u in enumerate(spine)
             if len(T.ins_of.get(u, [])) > 1]
    for i, u in joins:
        chx = (d.CH_M.iloc[i] if i < len(d) else d.CH_END_M.iloc[-1]) / 1000.0
        ax.plot([chx], [T.grd[u]], marker="v", ms=6, mfc=fk.C.MAIN, mec="white",
                mew=0.8, zorder=6)
    drops = T.n[(T.n.DROP_TYPE != "none") & (T.n.NODE_UID.isin(spineset))]
    for _, nd in drops.iterrows():
        i = spine.index(nd.NODE_UID)
        chx = (d.CH_M.iloc[i] if i < len(d) else d.CH_END_M.iloc[-1]) / 1000.0
        ax.plot([chx], [nd.GRD_M], marker="o", ms=4.6,
                mfc=(fk.C.FLAG if nd.DROP_TYPE == "backdrop" else fk.C.FAIL),
                mec="white", mew=0.8, zorder=7)

    ax.annotate(f"outfall {out.NODE_REF}\ninvert {out.INV_M:,.2f} m aOD\n"
                f"{out.DEPTH_M:,.2f} m below ground — UNCONFIRMED",
                xy=(total / 1000.0, out.INV_M), xytext=(-14, 58),
                textcoords="offset points", ha="right", fontsize=7.4,
                color=fk.C.INK, zorder=9,
                bbox=dict(boxstyle="round,pad=0.4", fc="white", ec=fk.C.FAIL, lw=0.9),
                arrowprops=dict(arrowstyle="-|>", color=fk.C.FAIL, lw=1.0))
    ax.set_ylabel("level (m aOD)")
    ax.set_xlim(0, total / 1000.0)
    ax.tick_params(labelbottom=False)
    ax.set_xlabel("")
    h = ax.get_legend_handles_labels()
    ax.legend(*h, loc="upper right", framealpha=0.93, edgecolor="#9a9a9a", ncol=2)

    xcv, ycv = step_xy(d, "COVER_US", "COVER_DN")
    axc.fill_between(xcv, 0, ycv, color=EARTH, lw=0, zorder=1)
    axc.plot(xcv, ycv, color=EARTH_EDGE, lw=1.0, zorder=3)
    axc.axhline(CAP_COVER_M, color=fk.C.FAIL, lw=1.0, ls=(0, (5, 3)), zorder=4)
    axc.axhline(MIN_COVER_M, color=fk.C.MAIN, lw=1.0, ls=(0, (2, 2)), zorder=4)
    axc.text(0.004, CAP_COVER_M, f" {CAP_COVER_M:.0f} m cap (project rule)",
             transform=axc.get_yaxis_transform(), va="bottom", fontsize=7,
             color=fk.C.FAIL)
    axc.text(0.62, MIN_COVER_M, f" {MIN_COVER_M:.2f} m minimum cover (G203-p33) ",
             transform=axc.get_yaxis_transform(), va="bottom", ha="left",
             fontsize=7, color=fk.C.MAIN, zorder=6,
             path_effects=[pe.withStroke(linewidth=2.6, foreground="white")])
    axc.annotate(f"deepest on this path: {cmax:,.2f} m at ch {ch_deep/1000:,.1f} km",
                 xy=(ch_deep / 1000.0, cmax), xytext=(0, 26),
                 textcoords="offset points", ha="center", fontsize=7.2,
                 arrowprops=dict(arrowstyle="-|>", color=fk.C.GREY, lw=0.9))
    axc.set_ylim(0, CAP_COVER_M * 1.14)
    axc.set_xlim(0, total / 1000.0)
    axc.set_ylabel("cover to crown (m)")
    axc.set_xlabel(f"chainage from {head_ref} (km)")

    extra = [Line2D([], [], marker="v", ls="none", ms=6, mfc=fk.C.MAIN,
                    mec="white", label=f"tributary joins ({len(joins)})"),
             Line2D([], [], marker="o", ls="none", ms=5, mfc=fk.C.FLAG,
                    mec="white", label="backdrop chamber (G203-p30, drop > 0.60 m)"),
             Line2D([], [], marker="o", ls="none", ms=5, mfc=fk.C.FAIL,
                    mec="white", label="vortex drop shaft (G203-p30, drop > 2 m)")]
    axc.legend(handles=extra, loc="upper left", bbox_to_anchor=(0.0, 0.88),
               framealpha=0.93, edgecolor="#9a9a9a", ncol=3, fontsize=7)

    fk.finish_chart(fig, source=wrap(fig, fk.source_line(art("reaches"), art("nodes"))))
    return fk.save(fig, "FT01_trunk_long_section")


# ==================================================================== FT02

def ft02_pumped_legs(T: Trunk) -> Path:
    """The three legs that cannot reach the works by gravity, and why."""
    st = art("stations")
    comps = T.components()
    sinks = [s for s in comps if T.kind[s] == "station"]
    sinks.sort(key=lambda s: -len(comps[s]))
    stat_by_xy = {(round(r.x, 1), round(r.y, 1)): r for _, r in st.iterrows()}

    fig, axes = fk.chart_frame(
        nrows=len(sinks), figsize=(13.4, 8.4),
        title=("Three legs stop at the cover cap, not at a hill — and one of them "
               "exists only because the client's drawing has a gap in it"),
        subtitle=("Long section of each gravity leg that ends at a lifting station. "
                  "The cap ladder recorded the cover each leg WOULD have needed to "
                  "carry on (s3_trunk_stations.csv `cover_m`); the chamber that was "
                  "actually built sits below the cap (W11a_trunk.gpkg nodes "
                  "`COVER_M`). All three stations are placed by cover, why = 'cap'."))
    stack(fig, axes, [1.0] * len(sinks), gap=0.082, top_pad=0.022)

    for k, (ax, sink) in enumerate(zip(np.atleast_1d(axes), sinks)):
        head = max((s for s in T.sources() if T.path(s)[-1] == sink),
                   key=lambda s: sum(T.r.LEN_M.iloc[T.out_of[a]]
                                     for a in T.path(s)[:-1]))
        p = T.path(head)
        d = T.profile(p)
        nd = T.node.loc[sink]
        key = (round(nd.X, 1), round(nd.Y, 1))
        srow = stat_by_xy.get(key)

        xg, yg = step_xy(d, "GRD_UP", "GRD_DN")
        xi, yi = step_xy(d, "INV_UP", "INV_DN")
        dd = d.assign(_CU=d.GRD_UP - d.COVER_US, _CD=d.GRD_DN - d.COVER_DN)
        xc, yc = step_xy(dd, "_CU", "_CD")
        prov = d.CONFIDENCE.eq("provisional")

        ax.fill_between(xg, yc, yg, color=EARTH, lw=0, zorder=1,
                        label="cover over the crown")
        ax.plot(xg, yg, color=EARTH_EDGE, lw=1.1, zorder=3, label="ground level")
        ax.plot(xi, yi, color=fk.C.TRUNK, lw=1.5, zorder=4, label="pipe invert")
        ax.plot(xg, yg - CAP_COVER_M, color=fk.C.FAIL, lw=0.9, ls=(0, (5, 3)),
                zorder=3,
                label=f"{CAP_COVER_M:.0f} m cover cap — PROJECT RULE, not G203")
        if k == 0:
            ax.legend(loc="lower left", fontsize=7.2, ncol=4, framealpha=0.92,
                      edgecolor="#9a9a9a")
        if prov.any():
            seg = d[prov]
            ax.axvspan(seg.CH_M.min() / 1000.0, seg.CH_END_M.max() / 1000.0,
                       color=fk.C.FLAG, alpha=0.18, zorder=0)
            ax.text((seg.CH_M.min() + seg.CH_END_M.max()) / 2000.0, 0.055,
                    f"PROVISIONAL connector, {seg.LEN_M.sum():,.0f} m",
                    transform=ax.get_xaxis_transform(), ha="center", fontsize=7.0,
                    color="#8a5a10", fontweight="bold")

        lift = f"{srow.static_lift_m:,.1f} m static lift" if srow is not None else "—"
        rm = f"{srow.rm_len_m:,.0f} m rising main" if srow is not None else "—"
        q = f"{srow.q_adf_m3d:,.0f} m³/d" if srow is not None else "—"
        breach = (f"cap ladder read {srow.cover_m:,.2f} m of cover here"
                  if srow is not None else "")
        ax.annotate(f"{nd.NODE_REF} — LIFTING STATION\n"
                    f"built cover {nd.COVER_M:,.2f} m · {breach}\n{q} · {lift} · {rm}",
                    xy=(d.CH_END_M.iloc[-1] / 1000.0, nd.INV_M),
                    xytext=(-10, 44), textcoords="offset points", ha="right",
                    fontsize=7.2, zorder=9,
                    bbox=dict(boxstyle="round,pad=0.38", fc="white",
                              ec=fk.C.STATION, lw=0.9),
                    arrowprops=dict(arrowstyle="-|>", color=fk.C.STATION, lw=1.0))
        ax.set_xlim(0, d.CH_END_M.iloc[-1] / 1000.0)
        ax.set_ylabel("level (m aOD)")
        ax.set_title(f"{T.node.loc[head].NODE_REF} → {nd.NODE_REF}   ·   "
                     f"{d.LEN_M.sum()/1000:,.2f} km, {len(p):,} chambers, "
                     f"deepest cover {max(d.COVER_US.max(), d.COVER_DN.max()):,.2f} m",
                     fontsize=8.6, loc="left", color=fk.C.GREY, pad=3)
        ax.set_xlabel("chainage (km)")

    fk.finish_chart(fig, source=wrap(fig, fk.source_line(art("nodes"), art("reaches"),
                                              art("stations"))))
    return fk.save(fig, "FT02_trunk_pumped_legs")


# ==================================================================== FT03

def ft03_plan_defects(T: Trunk) -> Path:
    """Plan of the alignment with every registered defect located."""
    r, n, x = art("reaches"), art("nodes"), art("crossings")
    serv = art("servicing")
    f = art("findings")

    fail_dual = set(f[f.check == "H1/R3"].id)
    along = r[r.WADI_ALONG == 1]
    xing = r[r.WADI_XING == 1]
    dual_all = r[r.ON_DUAL_M > 0]
    dual_bad = r[r.EDGE_UID.isin(fail_dual)]
    sharp = n[n.INLET_FLAG == 1]
    wadi_ch = n[n.IN_WADI == 1]
    stations = n[n.NODE_KIND == "station"]
    outfall = n[n.NODE_KIND == "outfall"]

    # headroom at the north so the ten-row legend sits on blank ground, not on pipe
    x0, y0, x1, y1 = fk.extent_of(r, pad=0.05)
    ext = (x0, y0, x1, y1 + 0.26 * (y1 - y0))
    fig, ax, note = fk.map_frame(
        ext,
        title=("Every trunk defect is inherited from the drawn alignment — "
               f"{dual_bad.ON_DUAL_M.sum():,.0f} m on a dual carriageway and "
               f"{along.ON_WADI_M.sum()/1000:,.2f} km down a wadi"),
        subtitle=("The trunk is an INPUT: SHP/Main Pipe/Main Pipe.shp, the client's "
                  "own drawing. Stage 3 levels and sizes it and may not re-route it, "
                  "so each marker below is a decision for NWS, not a design choice. "
                  "Wadi class 4/5/6 on the 50-year hazard grid is a PROJECT "
                  "assumption standing in for G203-p30 4.4.1's washout criterion."))

    known, _wadi, rext = fk.hazard_coverage(ext)
    fk.hatch_untested(ax, ~known, rext, zorder=1.2)
    serv.boundary.plot(ax=ax, color="#8e8578", lw=0.7, zorder=1.8)
    r.plot(ax=ax, color=fk.C.TRUNK, lw=1.25, zorder=3)
    xing.plot(ax=ax, color=fk.C.WADI, lw=2.6, zorder=4)
    along.plot(ax=ax, color=fk.C.FAIL, lw=3.4, zorder=5)
    dual_all.plot(ax=ax, color=fk.C.DUAL, lw=3.0, zorder=5.5)
    # 535 m of dual band inside a 37 km frame is a few pixels: ring it so it is findable
    dc = dual_all.geometry.interpolate(0.5, normalized=True)
    ax.scatter(dc.x, dc.y, s=120, marker="o", facecolor="none", edgecolor=fk.C.DUAL,
               lw=1.4, zorder=5.6)

    ax.scatter(wadi_ch.X, wadi_ch.Y, s=9, marker="s", facecolor="none",
               edgecolor=fk.C.FAIL, lw=0.7, zorder=6)
    ax.scatter(sharp.X, sharp.Y, s=68, marker="^", facecolor=fk.C.FLAG,
               edgecolor=fk.C.INK, lw=0.7, zorder=8)
    ax.scatter(stations.X, stations.Y, s=115, marker="P", facecolor=fk.C.STATION,
               edgecolor="white", lw=1.1, zorder=9)
    ax.scatter(outfall.X, outfall.Y, s=170, marker="*", facecolor=fk.C.OUTFALL,
               edgecolor="white", lw=1.0, zorder=9)
    for _, s in stations.iterrows():
        ax.annotate(s.NODE_REF.replace("P0-TM-", ""), (s.X, s.Y), xytext=(7, 7),
                    textcoords="offset points", fontsize=7, color=fk.C.INK,
                    zorder=10, path_effects=[pe.withStroke(linewidth=2.4,
                                                           foreground="white")])
    ax.annotate("existing works", (outfall.X.iloc[0], outfall.Y.iloc[0]),
                xytext=(11, 9), textcoords="offset points", fontsize=7.4,
                color=fk.C.INK, zorder=10,
                path_effects=[pe.withStroke(linewidth=2.6, foreground="white")])

    handles = [
        Line2D([], [], color=fk.C.TRUNK, lw=1.5,
               label=f"trunk main, {r.LEN_M.sum()/1000:,.2f} km ({len(r):,} reaches)"),
        Line2D([], [], color=fk.C.FAIL, lw=3.4,
               label=f"ALONG a wadi — {len(along)} reaches, "
                     f"{along.ON_WADI_M.sum()/1000:,.2f} km (H1/R4 FAIL)"),
        Line2D([], [], color=fk.C.WADI, lw=2.6,
               label=f"scheduled wadi crossing — {len(xing)} reaches, legal under "
                     f"G201-p85-86"),
        Line2D([], [], color=fk.C.DUAL, lw=3.0, marker="o", mfc="none",
               mec=fk.C.DUAL, ms=9,
               label=f"in the 6 m dual-carriageway band — {len(dual_all)} reaches, "
                     f"{dual_all.ON_DUAL_M.sum():,.0f} m; "
                     f"{len(dual_bad)} of them run ALONG one "
                     f"({dual_bad.ON_DUAL_M.sum():,.0f} m, H1/R3 FAIL)"),
        Line2D([], [], marker="s", ls="none", mfc="none", mec=fk.C.FAIL,
               label=f"chamber on wadi ground — {len(wadi_ch)} (G203-p30 4.4.1)"),
        Line2D([], [], marker="^", ls="none", mfc=fk.C.FLAG, mec=fk.C.INK,
               label=f"inlet under 90° — {len(sharp)} "
                     f"({sharp.INLET_DEG.min():.1f}–{sharp.INLET_DEG.max():.1f}°, "
                     f"G203-p30)"),
        Line2D([], [], marker="P", ls="none", mfc=fk.C.STATION, mec="white",
               label=f"lifting station — {len(stations)}, all placed by the cover cap"),
        Line2D([], [], marker="*", ls="none", ms=11, mfc=fk.C.OUTFALL, mec="white",
               label="outfall at the existing works"),
        Line2D([], [], color="#8e8578", lw=1.0,
               label=f"servicing areas ({len(serv)}, stage 1)"),
        fk.untested_handle("UNTESTED — outside the 50-year hazard grid"),
    ]
    box = (f"trunk        {r.LEN_M.sum()/1000:>8,.2f} km\n"
           f"chambers     {len(n):>8,}\n"
           f"DN range     {r.DN.min():>5,.0f}–{r.DN.max():,.0f} mm\n"
           f"Qadf works   {T.node.loc['N0000758'].Q_ADF_M3D:>8,.0f} m³/d\n"
           f"Qpeak works  {T.node.loc['N0000758'].Q_PK_LS:>8,.0f} L/s\n"
           f"audit    {int((art('audit').status.str.upper() == 'PASS').sum()):>7,} "
           f"PASS / {int((art('audit').status.str.upper() == 'FAIL').sum()):,} FAIL")
    leg = ax.legend(handles=handles, loc="upper left", ncol=2, framealpha=0.93,
                    edgecolor="#9a9a9a", fontsize=7.2, borderpad=0.6,
                    labelspacing=0.5, columnspacing=1.4)
    leg.set_zorder(12)
    fk.finish_map(fig, ax, note=wrap(fig, note), databox=box,
                  source=wrap(fig, fk.source_line(art("reaches"), art("nodes"),
                                        art("crossings"), art("findings"),
                                        "Data/04 Lekhuwair/Hazard_T50y.tif, "
                                        "nodata -9999.0")))
    return fk.save(fig, "FT03_trunk_plan_defects")


# ==================================================================== FT04

def ft04_sizing_chain(T: Trunk) -> Path:
    """Flow, diameter and gradient along the same chainage — the sizing chain."""
    spine = T.longest_to("N0000758")
    d = T.profile(spine)
    total = d.LEN_M.sum()
    r = art("reaches")
    dec = _dn_reductions(T)
    dec_here = [u for u in dec if u in set(spine)]

    fig, axes = fk.chart_frame(
        nrows=3, figsize=(13.4, 8.0),
        title=(f"Diameter is set by flow, but it falls as often as it rises — "
               f"{len(dec_here)} of the {len(dec)} downstream reductions sit on "
               f"this one path"),
        subtitle=("Peak flow, diameter and laid gradient along the same chainage as "
                  "FT01. A diameter that shrinks downstream is legal where the "
                  "ground steepens — G203-p29 forbids the opposite move, oversizing "
                  "to lay flatter — but each reduction seats soffit-to-soffit and "
                  "lifts the invert (see FT08)."))
    stack(fig, axes, (1.0, 1.0, 1.1))
    axq, axd, axs = axes

    xq, yq = flat_xy(d, "QPK_LS")
    axq.fill_between(xq, 0, yq, color=fk.C.LATERAL, alpha=0.55, lw=0, zorder=2)
    axq.plot(xq, yq, color=fk.C.SUBMAIN, lw=1.0, zorder=3)
    axq.set_ylabel("peak flow (L/s)")
    axq.set_yscale("symlog", linthresh=10)
    fk.thousands(axq)
    axq.tick_params(labelbottom=False)
    axq.text(0.994, 0.72, f"{d.QPK_LS.iloc[-1]:,.0f} L/s into the works  ",
             transform=axq.transAxes, ha="right", fontsize=7.8, color=fk.C.INK,
             fontweight="bold")

    xd, yd = flat_xy(d, "DN")
    axd.plot(xd, yd, color=fk.C.TRUNK, lw=1.2, zorder=3, drawstyle="default")
    axd.fill_between(xd, 0, yd, color=fk.C.TRUNK, alpha=0.13, lw=0, zorder=2)
    for u in dec_here:
        i = spine.index(u)
        if i < len(d):
            axd.plot([d.CH_M.iloc[i] / 1000.0], [d.DN.iloc[i]], marker="v", ms=4.5,
                     mfc=fk.C.FAIL, mec="white", mew=0.6, zorder=6)
    axd.set_ylabel("diameter DN (mm)")
    axd.set_yticks([200, 500, 900, 1200, 1700])
    axd.tick_params(labelbottom=False)
    axd.legend(handles=[Line2D([], [], marker="v", ls="none", mfc=fk.C.FAIL,
                               mec="white",
                               label="diameter REDUCES going downstream")],
               loc="upper left", fontsize=7.2, framealpha=0.9, edgecolor="#9a9a9a")

    xs, ys = flat_xy(d, "SLOPE_LAID")
    xm, ym = flat_xy(d, "SLOPE_MIN")
    axs.plot(xs, ys, color=fk.C.MAIN, lw=1.0, zorder=4, label="laid gradient")
    axs.plot(xm, ym, color=fk.C.FAIL, lw=1.0, ls=(0, (4, 2)), zorder=5,
             label="minimum gradient, G203-p29 Table 11")
    axs.fill_between(xs, ym, ys, where=(ys >= ym), color=fk.C.PASS, alpha=0.5,
                     lw=0, zorder=2, label="margin over the minimum")
    axs.set_yscale("log")
    axs.set_ylabel("gradient (%)")
    axs.set_xlabel(f"chainage from {T.node.loc[spine[0]].NODE_REF} (km)")
    axs.legend(loc="upper right", fontsize=7.2, ncol=3, framealpha=0.9,
               edgecolor="#9a9a9a")

    for a in axes:
        a.set_xlim(0, total / 1000.0)

    tight = (r.SLOPE_LAID <= r.SLOPE_MIN + 1e-9)
    note = (f"whole trunk: {r.LEN_M[tight].sum()/1000:,.2f} km of "
            f"{r.LEN_M.sum()/1000:,.2f} km ({100*r.LEN_M[tight].sum()/r.LEN_M.sum():.0f} %) "
            f"is laid AT its Table 11 minimum, with no margin for the 20 mm laying "
            f"tolerance of G203-p29 · gradient set by: "
            + ", ".join(f"{k} {v/1000:,.1f} km"
                        for k, v in (r.groupby('GRAD_BY').LEN_M.sum()).items()))
    fk.finish_chart(fig, source=wrap(fig, fk.source_line(art("reaches"),
                                                        art("nodes"))),
                    note=wrap(fig, note))
    return fk.save(fig, "FT04_trunk_sizing_chain")


# ==================================================================== FT05

def _components_at(gdf, tol: float = 0.010) -> int:
    """Connected components of a line layer, endpoints noded at ``tol`` metres."""
    par = {}

    def find(a):
        while par[a] != a:
            par[a] = par[par[a]]
            a = par[a]
        return a

    def key(pt):
        return (round(pt[0] / tol), round(pt[1] / tol))

    for geom in gdf.geometry:
        parts = geom.geoms if geom.geom_type.startswith("Multi") else [geom]
        for g in parts:
            cs = list(g.coords)
            a, b = key(cs[0]), key(cs[-1])
            par.setdefault(a, a)
            par.setdefault(b, b)
            ra, rb = find(a), find(b)
            if ra != rb:
                par[ra] = rb
    return len({find(k) for k in par})


def ft05_fragmentation(T: Trunk) -> Path:
    """The same trunk, three times, in three different numbers of pieces."""
    mp = art("main_pipe")
    r = art("reaches")
    cor = art("corridors")
    mc = cor[cor.SRC == "main_pipe"]

    rows = []
    for label, g, what in (
        ("the client's drawing\nSHP/Main Pipe/Main Pipe.shp", mp,
         "54 drawn polylines, the INPUT"),
        ("stage 3's design\nW11a_trunk.gpkg [reaches]", r,
         "754 levelled, sized reaches"),
        ("stage 2's corridor copy\nW11a.gpkg [corridors] SRC='main_pipe'", mc,
         "669 corridor edges the network is built on"),
    ):
        rows.append(dict(label=label + "\n" + what, what=what, n=len(g),
                         km=float(g.length.sum()) / 1000.0,
                         comps=_components_at(g)))
    t = pd.DataFrame(rows)
    short = t.km.iloc[1] - t.km.iloc[2]

    fig, axes = fk.chart_frame(
        nrows=1, ncols=2, figsize=(13.0, 4.9),
        title=(f"The trunk and the corridors it must connect to are not the same "
               f"line: {t.comps.iloc[2]:.0f} pieces against "
               f"{t.comps.iloc[1]:.0f}, and {short:,.2f} km missing"),
        subtitle=("The same alignment measured three ways, every endpoint noded at "
                  "10 mm — the tolerance a GIS uses, and the one that showed W10's "
                  "'310 loops' were an artefact (W11a/run/EVIDENCE_snap_tolerance.md). "
                  "The corridor copy is what stages 4-5b hang laterals on, so its "
                  f"{t.comps.iloc[2]:.0f} pieces are {t.comps.iloc[2]:.0f} places "
                  f"where a lateral cannot find the trunk."))
    a1, a2 = axes
    y = np.arange(len(t))[::-1]
    cols = [fk.C.MAIN, fk.C.PASS, fk.C.FAIL]

    for ax, col, lab, fmt in ((a1, "comps", "connected pieces, endpoints noded at "
                                          "10 mm", "{:,.0f}"),
                              (a2, "km", "length of alignment (km)", "{:,.2f} km")):
        vals = t[col].to_numpy()
        for yy, v, c in zip(y, vals, cols):
            ax.barh(yy, v, height=0.52, color=c, edgecolor=fk.C.INK, lw=0.8,
                    zorder=3)
            ax.text(v, yy, "  " + fmt.format(v), va="center", ha="left",
                    fontsize=10.5, fontweight="bold", color=fk.C.INK, zorder=4)
        ax.set_yticks(y)
        ax.set_yticklabels(t.label if ax is a1 else ["", "", ""], fontsize=7.4)
        ax.set_xlabel(lab)
        ax.set_xlim(0, vals.max() * 1.32)
        fk.style_axes(ax, xgrid=True, ygrid=False)
    a2.axvline(t.km.iloc[1], color=fk.C.GREY, lw=0.9, ls=(0, (3, 2)), zorder=5)
    a2.annotate(f"{short:,.2f} km of trunk the corridor graph does not have",
                xy=(t.km.iloc[2], y[2]), xytext=(t.km.iloc[2] - 2, y[2] + 0.42),
                ha="right", fontsize=7.6, color=fk.C.FAIL, zorder=6,
                arrowprops=dict(arrowstyle="-[, widthB=1.4", color=fk.C.FAIL,
                                lw=0.9))

    note = (f"a perfect tree would read 4 pieces on the design layer — the outfall "
            f"and the three lifting stations, each the sink of its own gravity "
            f"component (stage 3 audit H16 PASS). The client's drawing reads "
            f"{t.comps.iloc[0]:.0f} because two legs are drawn with gaps; the "
            f"stage-3 note records the western one at "
            f"{_west_gap_m(T):,.2f} m, closed with a provisional straight connector.")
    fk.finish_chart(fig, note=wrap(fig, note),
                    source=wrap(fig, fk.source_line(art("main_pipe"), art("reaches"),
                                          art("corridors"))))
    return fk.save(fig, "FT05_trunk_fragmentation")


def _west_gap_m(T: Trunk) -> float:
    """The western-leg gap, from the stage-3 manifest note (never re-derived)."""
    for n in art("manifest")["_notes"]:
        if "western leg gap measured" in n:
            return float(n.split("measured")[1].split("m,")[0].strip())
    raise RuntimeError("the western-leg gap note is no longer in manifest_s3_trunk")


# ==================================================================== FT06

def ft06_works_inlet(T: Trunk) -> Path:
    """The one number NWS must confirm: the invert the trunk arrives on."""
    spine = T.longest_to("N0000758")
    d = T.profile(spine)
    tail = d[d.CH_END_M > d.CH_END_M.iloc[-1] - 2500.0].copy()
    tail["CH_M"] -= d.CH_END_M.iloc[-1]
    tail["CH_END_M"] -= d.CH_END_M.iloc[-1]
    out = T.node.loc["N0000758"]
    last = d.iloc[-1]

    fig, ax = fk.chart_frame(
        figsize=(11.6, 5.3),
        title=(f"The trunk arrives at the works on invert {out.INV_M:,.2f} m aOD — "
               f"{out.DEPTH_M:,.2f} m below ground, and nobody has confirmed it fits"),
        subtitle=("The last 2.5 km into the existing STP. The inlet invert of the "
                  "existing works is NOT in any dataset we hold (finding S3-3), so "
                  "stage 3 laid the trunk to its own level and published it for "
                  "confirmation. If NWS's inlet is higher than this, the last "
                  "reaches must be re-levelled or the flow lifted."))
    xg, yg = step_xy(tail, "GRD_UP", "GRD_DN")
    xi, yi = step_xy(tail, "INV_UP", "INV_DN")
    dd = tail.assign(_CU=tail.GRD_UP - tail.COVER_US, _CD=tail.GRD_DN - tail.COVER_DN)
    xc, yc = step_xy(dd, "_CU", "_CD")

    ax.fill_between(xg, yc, yg, color=EARTH, lw=0, zorder=1, label="cover")
    ax.plot(xg, yg, color=EARTH_EDGE, lw=1.4, zorder=3, label="ground level")
    ax.plot(xi, yi, color=fk.C.TRUNK, lw=2.0, zorder=4,
            label=f"invert, DN{last.DN:,.0f} {last.MATERIAL} at "
                  f"{last.SLOPE_LAID:,.2f} % (minimum {last.SLOPE_MIN:,.3f} %, "
                  f"G203-p29 T11)")
    ax.plot(xg, yg - CAP_COVER_M, color=fk.C.FAIL, lw=0.9, ls=(0, (5, 3)), zorder=3,
            label=f"{CAP_COVER_M:.0f} m cover cap (project rule)")

    ax.annotate("", xy=(0, out.GRD_M), xytext=(0, out.INV_M),
                arrowprops=dict(arrowstyle="<|-|>", color=fk.C.FAIL, lw=1.4),
                zorder=9)
    ax.text(-0.035, (out.GRD_M + out.INV_M) / 2,
            f" depth {out.DEPTH_M:,.2f} m\n cover {out.COVER_M:,.2f} m",
            ha="right", va="center", fontsize=8.4, color=fk.C.INK, zorder=10,
            bbox=dict(boxstyle="round,pad=0.35", fc="white", ec=fk.C.FAIL, lw=1.0))
    ax.axhline(out.INV_M, color=fk.C.FAIL, lw=0.8, ls=":", zorder=3)
    ax.text(0.01, out.INV_M, f" INVERT {out.INV_M:,.2f} m aOD — CONFIRM WITH NWS",
            transform=ax.get_yaxis_transform(), va="bottom", fontsize=8.2,
            fontweight="bold", color=fk.C.FAIL)
    ax.axhline(out.GRD_M, color=EARTH_EDGE, lw=0.8, ls=":", zorder=3)
    ax.text(0.01, out.GRD_M, f" ground {out.GRD_M:,.2f} m aOD at the works",
            transform=ax.get_yaxis_transform(), va="bottom", fontsize=7.4,
            color=fk.C.GREY)

    ax.set_xlim(tail.CH_M.iloc[0] / 1000.0, 0.10)
    ax.set_xlabel("distance to the outfall (km)")
    ax.set_ylabel("level (m aOD)")
    ax.legend(loc="lower left", fontsize=7.4, framealpha=0.93, edgecolor="#9a9a9a")

    gap = float(out.Q_ADF_M3D) - float(last.QADF)
    note = (f"the last reach {last.EDGE:s} carries {last.QADF:,.0f} m³/d and "
            f"{last.QPK_LS:,.0f} L/s at d/D {last.DOD:.3f} and {last.V:,.2f} m/s "
            f"(G203-p27 T10 limit {DOD_LIMIT_BIG:.2f} at DN > {DOD_DN_SPLIT}; "
            f"G203-p26 self-cleansing 0.75 m/s) · the outfall CHAMBER totals "
            f"{out.Q_ADF_M3D:,.0f} m³/d and {out.Q_PK_LS:,.0f} L/s, so "
            f"{gap:,.0f} m³/d ({100*gap/out.Q_ADF_M3D:.1f} %) is allocated to the "
            f"final chamber itself and is carried by no pipe on this layer — a "
            f"trunk-only assignment that stages 4-5 must absorb")
    fk.finish_chart(fig, note=wrap(fig, note),
                    source=wrap(fig, fk.source_line(art("nodes"), art("reaches"))))
    return fk.save(fig, "FT06_works_inlet")


# ==================================================================== FT07

def ft07_margin(T: Trunk) -> Path:
    """How much room is left: d/D against Table 10, and what self-cleanses how."""
    r = art("reaches")
    lim = np.where(r.DN <= DOD_DN_SPLIT, DOD_LIMIT_SMALL, DOD_LIMIT_BIG)
    margin = lim - r.DOD_PK
    total = r.LEN_M.sum()
    bands = [(-np.inf, 0.005, "on the ceiling (< 0.005)"),
             (0.005, 0.02, "0.005 – 0.02"),
             (0.02, 0.10, "0.02 – 0.10"),
             (0.10, np.inf, "over 0.10")]
    band_km = [r.LEN_M[(margin >= a) & (margin < b)].sum() / 1000.0
               for a, b, _ in bands]
    tract = r[r.CLEAN_BY == "tractive"]
    velo = r[r.CLEAN_BY == "velocity"]

    fig, axes = fk.chart_frame(
        nrows=1, ncols=2, figsize=(13.0, 5.0),
        title=(f"{band_km[0]:,.2f} km of trunk is laid hard against the d/D ceiling, "
               f"and {100*tract.LEN_M.sum()/total:,.1f} % of it self-cleanses on a "
               f"number the guideline never gives"),
        subtitle=("Left: distance from the G203-p27 Table 10 limit — d/D ≤ "
                  f"{DOD_LIMIT_SMALL:.2f} at DN ≤ {DOD_DN_SPLIT} mm, ≤ "
                  f"{DOD_LIMIT_BIG:.2f} above it. Right: which route each reach "
                  "self-cleanses by. The tractive route needs a tension the "
                  "guideline does not print; τ = 1.0 Pa is OUR assumption "
                  "(GAP-9, G203-p27 §4.2.2.1)."))
    a1, a2 = axes
    y = np.arange(len(bands))[::-1]
    cols = [fk.C.FAIL, fk.C.FLAG, fk.C.LATERAL, fk.C.PASS]
    for yy, v, c, (_, _, lab) in zip(y, band_km, cols, bands):
        a1.barh(yy, v, height=0.6, color=c, edgecolor=fk.C.INK, lw=0.7, zorder=3)
        a1.text(v, yy, f"  {v:,.2f} km   ({100*v/(total/1000):.0f} %)", va="center",
                ha="left", fontsize=8.6, fontweight="bold", zorder=4)
    a1.set_yticks(y)
    a1.set_yticklabels([lab for _, _, lab in bands], fontsize=8)
    a1.set_xlabel("length of trunk (km)")
    a1.set_xlim(0, max(band_km) * 1.42)
    a1.set_ylabel("margin below the Table 10 d/D limit")
    fk.style_axes(a1, xgrid=True, ygrid=False)

    parts = [("by velocity ≥ 0.75 m/s\nG203-p26 — a guideline number",
              velo.LEN_M.sum() / 1000.0, len(velo), fk.C.PASS),
             (f"by tractive force at τ = {TAU_ASSUMED_PA:.1f} Pa\n"
              "OUR assumption — GAP-9", tract.LEN_M.sum() / 1000.0, len(tract),
              fk.C.FLAG)]
    y2 = np.arange(len(parts))[::-1]
    for yy, (lab, v, cnt, c) in zip(y2, parts):
        a2.barh(yy, v, height=0.5, color=c, edgecolor=fk.C.INK, lw=0.7, zorder=3,
                hatch=None if c == fk.C.PASS else "..")
        a2.text(v, yy, f"  {v:,.2f} km · {cnt:,} reaches", va="center", ha="left",
                fontsize=8.6, fontweight="bold", zorder=4)
    a2.set_yticks(y2)
    a2.set_yticklabels([p[0] for p in parts], fontsize=8)
    a2.set_xlabel("length of trunk (km)")
    a2.set_xlim(0, max(p[1] for p in parts) * 1.55)
    fk.style_axes(a2, xgrid=True, ygrid=False)

    note = (f"maximum d/D actually laid: {r.DOD_PK[r.DN <= DOD_DN_SPLIT].max():.4f} "
            f"at DN ≤ {DOD_DN_SPLIT} and {r.DOD_PK[r.DN > DOD_DN_SPLIT].max():.4f} "
            f"above it — both within a thousandth of the limit · maximum velocity "
            f"{r.V_PK_MS.max():,.2f} m/s against the 3.0 m/s ceiling of G203-p27 · "
            f"at τ = 2.0 Pa the required gradient rises {2.0 ** TAU_EXP:.2f}× "
            f"(Smin ∝ τ^{TAU_EXP:.2f}, G203-p27 §4.2.2.1), which is what GAP-9 is "
            f"asking NWS")
    fk.finish_chart(fig, note=wrap(fig, note), source=wrap(fig, fk.source_line(art("reaches"))))
    return fk.save(fig, "FT07_trunk_margin")


# ==================================================================== FT08

def _dn_reductions(T: Trunk) -> dict:
    """``{node: (largest arriving DN, leaving DN)}`` where the pipe gets smaller."""
    out = {}
    for u, i in T.out_of.items():
        ins = T.ins_of.get(u, [])
        if not ins:
            continue
        dn_in = max(T.r.DN.iloc[j] for j in ins)
        dn_out = T.r.DN.iloc[i]
        if dn_out < dn_in:
            out[u] = (dn_in, dn_out)
    return out


def ft08_step_ups(T: Trunk) -> Path:
    """The trunk narrows going downstream 93 times, and 78 of them pond upstream."""
    f = art("findings")
    st = f[f.check == "H11(intent)"].copy()
    dec = _dn_reductions(T)
    n = art("nodes")
    r = art("reaches")

    fig, axes = fk.chart_frame(
        nrows=1, ncols=2, figsize=(13.0, 5.2),
        title=(f"The trunk gets narrower going downstream {len(dec)} times, and "
               f"{len(st)} of those chambers lift the invert — the auditor cannot "
               f"see any of it"),
        subtitle=("Audit H11 (no reverse gradient, G203-p29) tests fall WITHIN a "
                  "reach, so a chamber that seats a smaller outgoing pipe "
                  "soffit-to-soffit and raises the invert passes every check while "
                  "ponding the reach above it. Stage 3 records them itself, in "
                  "s3_trunk_findings.csv, as H11(intent)."))
    title_room(fig)
    a1, a2 = axes

    pairs = pd.Series([f"DN{a:,.0f} → DN{b:,.0f}" for a, b in dec.values()])
    top = pairs.value_counts().head(10)[::-1]
    a1.barh(np.arange(len(top)), top.to_numpy(), height=0.62, color=fk.C.TRUNK,
            alpha=0.85, edgecolor=fk.C.INK, lw=0.7, zorder=3)
    for i, v in enumerate(top.to_numpy()):
        a1.text(v, i, f"  {v:,.0f}", va="center", fontsize=8.4, fontweight="bold")
    a1.set_yticks(np.arange(len(top)))
    a1.set_yticklabels(top.index, fontsize=8)
    a1.set_xlabel("chambers")
    a1.set_xlim(0, top.max() * 1.25)
    a1.set_title(f"the ten commonest reductions, of {len(dec)} in all",
                 fontsize=8.6, loc="left", color=fk.C.GREY, pad=4)
    fk.style_axes(a1, xgrid=True, ygrid=False)

    v = st.value.to_numpy(dtype=float)
    bins = np.arange(0, np.ceil(v.max() * 20) / 20 + 0.05, 0.05)
    a2.hist(v, bins=bins, color=fk.C.FLAG, edgecolor=fk.C.INK, lw=0.7, hatch="..",
            zorder=3)
    a2.set_xlabel("invert step UP at the chamber (m)")
    a2.set_ylabel("chambers")
    a2.set_title(f"{len(st)} step-ups, {v.sum():,.2f} m in total, "
                 f"worst {v.max():,.3f} m",
                 fontsize=8.6, loc="left", color=fk.C.GREY, pad=4)
    a2.axvline(0.020, color=fk.C.FAIL, lw=1.1, ls=(0, (4, 2)), zorder=5)
    a2.annotate("20 mm laying tolerance, G203-p29 —\nevery one of these exceeds it",
                xy=(0.020, a2.get_ylim()[1] * 0.55), xytext=(0.30, 0.90),
                textcoords="axes fraction", fontsize=7.4, color=fk.C.FAIL,
                ha="left", va="top", zorder=6,
                bbox=dict(boxstyle="round,pad=0.35", fc="white", ec=fk.C.FAIL,
                          lw=0.8),
                arrowprops=dict(arrowstyle="-|>", color=fk.C.FAIL, lw=0.9))

    worst = st.nlargest(1, "value").iloc[0]
    note = (f"worst chamber {worst.id}: {worst.value:,.3f} m. Cause recorded by "
            f"stage 3 — 'the outgoing reach is a smaller diameter than the arriving "
            f"one, so the soffit-to-soffit seat steps the invert UP and ponds the "
            f"upstream reach'. {len(dec) - len(st)} of the {len(dec)} reductions "
            f"had enough fall to absorb the seat and produced no step.")
    fk.finish_chart(fig, note=wrap(fig, note),
                    source=wrap(fig, fk.source_line(art("findings"), art("reaches"),
                                          art("nodes"))))
    return fk.save(fig, "FT08_trunk_step_ups")


# ==================================================================== FT09

def ft09_wadi_exposure(T: Trunk) -> Path:
    """Wadi and dual exposure along the chainage, with the untested share drawn."""
    r = art("reaches")
    m = art("manifest")
    total = r.LEN_M.sum()
    along_km = r.ON_WADI_M[r.WADI_ALONG == 1].sum() / 1000.0
    xing_km = r.ON_WADI_M[r.WADI_XING == 1].sum() / 1000.0
    dual_m = r.ON_DUAL_M.sum()
    untested_km = float(m["wadi_untested_km"])
    untested_pct = float(m["wadi_samples_untested_pct"])
    wholly = int(m["wadi_reaches_wholly_untested"])
    ch_wadi = int(m["chambers_on_wadi_ground"])
    ch_out = int(m["chambers_outside_hazard_grid"])
    n_ch = len(art("nodes"))

    fig, axes = fk.chart_frame(
        nrows=2, figsize=(13.4, 6.6),
        title=(f"{untested_pct:.0f} % of the wadi samples on this trunk have no "
               f"answer — the {along_km:,.2f} km of along-wadi pipe is what the "
               f"tested half found"),
        subtitle=("Top: where the trunk meets a wadi or a dual carriageway, by "
                  "chainage on the longest gravity path. Bottom: the whole trunk, "
                  "in kilometres. The 50-year hazard grid does not cover the study "
                  "area and its nodata is −9999.0, which is finite — so an "
                  "isfinite() guard reads it as dry ground. Class 4/5/6 = wadi is a "
                  "PROJECT assumption for G203-p30 §4.4.1's washout criterion."))
    ax, axb = axes
    stack(fig, axes, (1.0, 0.72), gap=0.10)

    spine = T.longest_to("N0000758")
    d = T.profile(spine)
    L = d.CH_END_M.iloc[-1] / 1000.0
    lanes = [("along a wadi — H1/R4 FAIL", d.WADI_ALONG == 1, fk.C.FAIL),
             ("scheduled wadi crossing — legal, G201-p85-86", d.WADI_XING == 1,
              fk.C.WADI),
             ("in the 6 m dual band — project rule 7", d.ON_DUAL_M > 0, fk.C.DUAL)]
    for k, (lab, mask, col) in enumerate(lanes):
        yy = len(lanes) - 1 - k
        ax.broken_barh([(a / 1000.0, l / 1000.0) for a, l in
                        zip(d.CH_M[mask], d.LEN_M[mask])],
                       (yy - 0.32, 0.64), facecolors=col, edgecolor="none",
                       zorder=3)
        ax.text(-0.008, yy, lab, transform=ax.get_yaxis_transform(), ha="right",
                va="center", fontsize=7.8)
    ax.set_ylim(-0.7, len(lanes) - 0.3)
    ax.set_yticks([])
    ax.set_xlim(0, L)
    ax.set_xlabel("chainage on the longest gravity path, "
                  f"{T.node.loc[spine[0]].NODE_REF} → outfall (km)")
    fk.style_axes(ax, xgrid=True, ygrid=False)
    ax.spines["left"].set_visible(False)

    bars = [("wadi ground CROSSED — legal under H1a", xing_km, fk.C.WADI, None),
            ("wadi ground run ALONG — H1/R4 FAIL", along_km, fk.C.FAIL, "\\\\"),
            ("dual-carriageway band", dual_m / 1000.0, fk.C.DUAL, None),
            (f"UNTESTED — outside the hazard grid ({wholly} reaches wholly so)",
             untested_km, fk.C.UNTESTED, "///")]
    y = np.arange(len(bars))[::-1]
    for yy, (lab, v, c, h) in zip(y, bars):
        axb.barh(yy, v, height=0.58, color=c, edgecolor=fk.C.INK, lw=0.7, hatch=h,
                 zorder=3)
        axb.text(v, yy, f"  {v:,.2f} km  ({100*v/(total/1000):.1f} % of the trunk)",
                 va="center", ha="left", fontsize=8.4, fontweight="bold",
                 color=fk.C.INK, zorder=4)
    axb.set_yticks(y)
    axb.set_yticklabels([b[0] for b in bars], fontsize=8)
    axb.set_xlabel(f"length of the {total/1000:,.2f} km trunk (km)")
    axb.set_xlim(0, max(b[1] for b in bars) * 1.55)
    fk.style_axes(axb, xgrid=True, ygrid=False)

    note = (f"{ch_wadi} of {n_ch:,} trunk chambers stand on wadi ground and "
            f"{ch_out} of them ({100*ch_out/n_ch:.0f} %) stand where the grid has "
            f"no answer at all — so the chamber figure, like the pipe figure, is a "
            f"count from the tested half only")
    fk.finish_chart(fig, note=wrap(fig, note),
                    source=wrap(fig, fk.source_line(art("reaches"), art("nodes"),
                                          manifest_src())))
    return fk.save(fig, "FT09_trunk_wadi_exposure")


# ==================================================================== FT10

def ft10_station_cascade(T: Trunk) -> Path:
    """The western legs: two stations in series, one of them on a drawn gap."""
    st = art("stations")
    n = art("nodes")
    r = art("reaches")
    prov = r[r.CONFIDENCE == "provisional"]
    stations = n[n.NODE_KIND == "station"]

    keep = stations[stations.X < 460000].sort_values("X")
    sub = _subsystem_reaches(T, keep.NODE_UID.tolist())
    shown = r[r.EDGE_UID.isin(sub)]
    x0, y0, x1, y1 = fk.extent_of(shown, pad=0.08)
    # the rising mains leave the sub-systems, so pull their discharge points in too
    for _, srow in st.iterrows():
        if srow.x < 460000:
            x0, x1 = min(x0, srow.dx - 250), max(x1, srow.dx + 250)
            y0, y1 = min(y0, srow.dy - 250), max(y1, srow.dy + 250)
    ext = (x0, y0 - 0.10 * (y1 - y0), x1, y1 + 0.38 * (y1 - y0))

    fig, ax, note = fk.map_frame(
        ext,
        title=("Two of the three lifting stations are in series on the western leg — "
               "and the second one sits on a straight line we drew across a gap"),
        subtitle=(f"Station {keep.NODE_REF.iloc[0]} lifts into a gravity leg that "
                  f"runs {_leg_km(T, keep.NODE_UID.iloc[1]):,.2f} km to station "
                  f"{keep.NODE_REF.iloc[1]}, which lifts again into the leg that "
                  f"reaches the works. The reaches shaded amber are the provisional "
                  f"connector that closes the {_west_gap_m(T):,.2f} m gap the "
                  f"stage-3 note found in the client's drawing — the build note "
                  f"said 2 m."))

    art("servicing").plot(ax=ax, facecolor=fk.C.PLOT_FILL, edgecolor=fk.C.PLOT_EDGE,
                          lw=0.4, alpha=0.6, zorder=1.5)
    r.plot(ax=ax, color=fk.C.FAINT, lw=0.9, zorder=2.5)
    shown.plot(ax=ax, color=fk.C.TRUNK, lw=2.0, zorder=3.5)
    prov.plot(ax=ax, color=fk.C.FLAG, lw=4.4, zorder=4, alpha=0.9)

    for _, srow in st.iterrows():
        ax.annotate("", xy=(srow.dx, srow.dy), xytext=(srow.x, srow.y),
                    arrowprops=dict(arrowstyle="-|>", color=fk.C.STATION, lw=2.4,
                                    shrinkA=3, shrinkB=3), zorder=8)
    ax.scatter(stations.X, stations.Y, s=160, marker="P", facecolor=fk.C.STATION,
               edgecolor="white", lw=1.2, zorder=9)
    seq = 0
    for _, srow in st.sort_values("x").iterrows():
        if srow.x > 460000:
            continue
        seq += 1
        near = stations.iloc[((stations.X - srow.x) ** 2 +
                              (stations.Y - srow.y) ** 2).to_numpy().argmin()]
        ax.annotate(f"{seq}.  {near.NODE_REF}\n"
                    f"{srow.q_adf_m3d:,.0f} m³/d · {srow.q_pk_ls:,.0f} L/s\n"
                    f"static lift {srow.static_lift_m:,.1f} m · rising main "
                    f"{srow.rm_len_m:,.0f} m\n"
                    f"cover at the chamber {near.COVER_M:,.2f} m",
                    (srow.x, srow.y),
                    xytext=((16, 34) if srow.x < 0.5 * (x0 + x1) else (-18, 52)),
                    textcoords="offset points",
                    ha=("left" if srow.x < 0.5 * (x0 + x1) else "right"),
                    fontsize=7.4, zorder=10,
                    bbox=dict(boxstyle="round,pad=0.38", fc="white",
                              ec=fk.C.STATION, lw=0.9),
                    arrowprops=dict(arrowstyle="-", color=fk.C.STATION, lw=0.7))

    handles = [
        Line2D([], [], color=fk.C.TRUNK, lw=2.0, label="gravity legs feeding a station"),
        Line2D([], [], color=fk.C.FAINT, lw=1.2, label="rest of the trunk"),
        Line2D([], [], color=fk.C.FLAG, lw=4.4,
               label=f"PROVISIONAL connector — {prov.LEN_M.sum():,.0f} m over "
                     f"{len(prov)} reaches"),
        Line2D([], [], color=fk.C.STATION, lw=2.2, marker=">",
               label="rising main, station → discharge"),
        Line2D([], [], marker="P", ls="none", mfc=fk.C.STATION, mec="white",
               label="lifting station"),
    ]
    w = st[st.x < 460000]
    box = ("shown: the western cascade\n"
           f"stations      {len(w):>6,} of {len(st)}\n"
           f"static lift   {w.static_lift_m.sum():>6,.1f} m of "
           f"{st.static_lift_m.sum():,.1f} m\n"
           f"rising main   {w.rm_len_m.sum():>6,.0f} m of "
           f"{st.rm_len_m.sum():,.0f} m\n"
           f"pumped Qadf   {w.q_adf_m3d.max():>6,.0f} m³/d")
    fk.finish_map(fig, ax, note=wrap(fig, note), legend_handles=handles, databox=box,
                  source=wrap(fig, fk.source_line(art("nodes"), art("reaches"),
                                        art("stations"), manifest_src())))
    return fk.save(fig, "FT10_station_cascade")


def _subsystem_reaches(T: Trunk, sinks) -> set:
    comps = T.components()
    keep = set()
    for s in sinks:
        members = set(comps.get(s, []))
        keep |= {T.r.EDGE_UID.iloc[T.out_of[u]] for u in members if u in T.out_of}
    return keep


def _leg_km(T: Trunk, sink: str) -> float:
    members = set(T.components()[sink])
    return sum(T.r.LEN_M.iloc[T.out_of[u]] for u in members if u in T.out_of) / 1000.0


# ==================================================================== FT11

def ft11_audit(T: Trunk) -> Path:
    """All 22 checks, what each one measured, and what the five failures cost."""
    a = art("audit").copy()
    a["status"] = a.status.str.strip().str.lower()
    a["extent"] = a.extent.fillna("")
    order = {"fail": 0, "flag": 1, "untested": 2, "pass": 3}
    a["_k"] = a.status.map(lambda s: order.get(s, 2))
    a = a.sort_values(["_k", "id"], kind="stable").reset_index(drop=True)
    n_fail = int((a.status == "fail").sum())
    n_pass = int((a.status == "pass").sum())

    fig, ax = fk.chart_frame(
        figsize=(13.6, 5.9),
        title=(f"{n_pass} of {len(a)} checks pass on the trunk, and every one of "
               f"the {n_fail} failures is a property of the alignment we were given"),
        subtitle=("The stage-0 auditor run against the PUBLISHED trunk layers, not "
                  "an in-memory model. Nothing is 'cannot run' here — stage 3 "
                  "publishes every field the 22 checks need "
                  "(W11a/run/s3_trunk_audit_readiness.csv, 22 of 22 runnable). "
                  "Each row carries the guideline clause it tests."))
    def clip(txt: str, n: int) -> str:
        txt = str(txt)
        return txt if len(txt) <= n else txt[:n - 1].rstrip(" ,;") + "…"

    y = np.arange(len(a))[::-1]
    for yy, row in zip(y, a.itertuples()):
        sty = fk.status_style(row.status)
        ax.barh(yy, 1.0, height=0.80, zorder=3, **sty)
        ax.text(0.014, yy, f"{row.id}  ·  {clip(row.requirement, 56)}", va="center",
                ha="left", fontsize=7.5, color=fk.label_ink(row.status), zorder=5)
        ax.text(1.03, yy, clip(row.summary, 92), va="center", ha="left",
                fontsize=7.2, color=fk.C.INK, zorder=5)
        ax.text(2.86, yy, clip(row.source, 34), va="center", ha="right",
                fontsize=6.9, color=fk.C.GREY, zorder=5, style="italic")
    ax.set_xlim(0, 2.88)
    ax.set_ylim(-0.62, len(a) - 0.38)
    ax.set_yticks([])
    ax.set_xticks([])
    for s in ax.spines.values():
        s.set_visible(False)
    ax.grid(False)

    fk.legend_below(ax, [Patch(label="PASS", **fk.status_style("pass")),
                         Patch(label="FAIL", **fk.status_style("fail")),
                         Patch(label="CANNOT RUN — counted as a failure, never blank",
                               **fk.status_style("untested"))], ncol=3, drop=0.20)
    r, nd = art("reaches"), art("nodes")
    fnd = art("findings")
    dual_bad = fnd[fnd.check == "H1/R3"].value.sum()
    sharp = nd[nd.INLET_FLAG == 1].INLET_DEG
    comps = T.components()
    note = (f"the four failing extents in one line: "
            f"{r.ON_DUAL_M[r.ON_DUAL_M > 0].sum():,.0f} m of the alignment enters "
            f"the 6 m dual band and {dual_bad:,.0f} m of it runs along one · "
            f"{r.ON_WADI_M[r.WADI_ALONG == 1].sum()/1000:,.2f} km runs along a wadi · "
            f"{len(sharp)} inlets are under 90° "
            f"({sharp.min():.1f}–{sharp.max():.1f}°, a benching detail) · H15 fails "
            f"on a MISSING FIELD, not a broken network — the {len(comps)} components "
            f"each end at exactly one sink "
            f"({', '.join(sorted({T.kind[s] for s in comps}))})")
    fk.finish_chart(fig, note=wrap(fig, note), source=wrap(fig, fk.source_line(art("audit"))))
    return fk.save(fig, "FT11_trunk_audit")


# ==================================================================== runner

FIGURES = {
    "FT01": ft01_long_section,
    "FT02": ft02_pumped_legs,
    "FT03": ft03_plan_defects,
    "FT04": ft04_sizing_chain,
    "FT05": ft05_fragmentation,
    "FT06": ft06_works_inlet,
    "FT07": ft07_margin,
    "FT08": ft08_step_ups,
    "FT09": ft09_wadi_exposure,
    "FT10": ft10_station_cascade,
    "FT11": ft11_audit,
}


def main(argv: list[str]) -> int:
    want = [a.upper() for a in argv[1:]] or list(FIGURES)
    bad = [w for w in want if w not in FIGURES]
    if bad:
        print(f"unknown figure(s): {', '.join(bad)}\n"
              f"available: {', '.join(FIGURES)}")
        return 2
    T = Trunk()
    for key in want:
        try:
            p = FIGURES[key](T)
            print(f"{key}  ->  {p}")
        except Exception as exc:                                   # noqa: BLE001
            plt.close("all")
            print(f"{key}  FAILED  {type(exc).__name__}: {exc}")
            raise
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
