"""sewnet.maps — PNG deliverable maps (matplotlib Agg). Rule-4 spirit: satellite
background at 30% opacity, scalebar, legend, data box bottom-right."""

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np

MOSAIC = r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Hydraulic\Imagery\esri_z17_mosaic_3857.tif"
DN_COLOR = {200: "#2ecc71", 250: "#27ae60", 315: "#3498db", 400: "#9b59b6",
            500: "#e67e22", 600: "#e74c3c", 700: "#c0392b", 800: "#8e44ad", 900: "#2c3e50"}


def _background(ax, bounds):
    """Esri mosaic (EPSG:3857) warped into 32640 under the view, 30% opacity."""
    try:
        import rasterio
        from rasterio.vrt import WarpedVRT
        from rasterio.windows import from_bounds
        with rasterio.open(MOSAIC) as src:
            with WarpedVRT(src, crs="EPSG:32640") as vrt:
                l, b, r, t = bounds
                win = from_bounds(l, b, r, t, vrt.transform)
                img = vrt.read([1, 2, 3], window=win, out_shape=(3, 1400, 1400))
                ax.imshow(np.transpose(img, (1, 2, 0)), extent=(l, r, b, t),
                          alpha=0.30, zorder=0)
    except Exception as e:
        print(f"  (background mosaic unavailable: {e})")


def _frame(ax, boundary, title, databox):
    x, y = boundary.exterior.xy
    ax.plot(x, y, color="#d35400", lw=1.4, ls="--", zorder=6)
    ax.set_title(title, fontsize=13)
    ax.set_aspect("equal")
    ax.ticklabel_format(style="plain")
    ax.tick_params(labelsize=7)
    # scalebar 500 m
    l, b0 = ax.get_xlim()[0], ax.get_ylim()[0]
    x0, y0 = l + 150, b0 + 150
    ax.plot([x0, x0 + 500], [y0, y0], color="k", lw=3, zorder=9)
    for i in (0, 250, 500):
        ax.text(x0 + i, y0 + 25, f"{i}", fontsize=6, ha="center", zorder=9)
    ax.text(x0 + 250, y0 - 60, "m", fontsize=6, ha="center", zorder=9)
    ax.text(0.985, 0.015, databox, transform=ax.transAxes, fontsize=7.5,
            va="bottom", ha="right", zorder=10, family="monospace",
            bbox=dict(boxstyle="round", fc="white", ec="#555", alpha=0.92))


def network_map(path, net, pockets, of_rep, boundary, summary):
    nodes, pipes = net.chambers, net.reaches
    fig, ax = plt.subplots(figsize=(11, 15), dpi=140)
    _background(ax, boundary.bounds)
    for p in pipes:
        xs, ys = zip(*p.geom.coords)
        ax.plot(xs, ys, color=DN_COLOR.get(p.dn_mm, "#7f8c8d"),
                lw=0.6 + p.dn_mm / 400.0, zorder=3)
    ax.plot(of_rep["x"], of_rep["y"], marker="v", ms=14, color="red", zorder=8)
    ax.annotate("OUTFALL", (of_rep["x"], of_rep["y"]), textcoords="offset points",
                xytext=(8, -12), fontsize=9, color="red", weight="bold", zorder=8)
    for pk in pockets:
        s = nodes[pk["site"]]
        ax.plot(s.x, s.y, marker="s", ms=10, mfc="none", mec="red", mew=2, zorder=8)
        ax.annotate(f"SLS ({pk['n_props']}p)", (s.x, s.y), textcoords="offset points",
                    xytext=(8, 8), fontsize=8, color="red", zorder=8)
    dn_km = summary["dn_km"]
    handles = [Line2D([], [], color=DN_COLOR[int(k)], lw=2,
                      label=f"DN{k} — {v:.1f} km") for k, v in dn_km.items() if int(k) in DN_COLOR]
    handles.append(Line2D([], [], color="#d35400", ls="--", label="test boundary"))
    ax.legend(handles=handles, loc="upper left", fontsize=8)
    box = (f"W8 TEST-BOUNDARY SEWER DESIGN\n"
           f"area {summary['s1']['boundary_ha']:.0f} ha | net {summary['net_km']:.1f} km | "
           f"{summary['n_nodes']} MH\n"
           f"{summary['loads']['loaded_points']} plots, "
           f"{summary['loads'].get('total_properties', 0):.0f} properties\n"
           f"Qadf {summary['qadf_outfall_m3d']:.0f} m3/d | "
           f"Qpeak {summary['qpeak_outfall_ls']:.0f} L/s ({summary['pf_formula']})\n"
           f"audit violations: {summary['violations']}")
    _frame(ax, boundary, "W8 — Test-Boundary Gravity Sewer Network (by pipe size)", box)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def depth_map(path, net, boundary, summary):
    nodes, pipes = net.chambers, net.reaches
    fig, ax = plt.subplots(figsize=(11, 15), dpi=140)
    _background(ax, boundary.bounds)
    import matplotlib.cm as cm
    import matplotlib.colors as mcolors
    norm = mcolors.Normalize(vmin=1.5, vmax=12.0)
    cmap = cm.get_cmap("plasma") if hasattr(cm, "get_cmap") else plt.get_cmap("plasma")
    for p in pipes:
        d = nodes[p.dn].depth or 2.0
        xs, ys = zip(*p.geom.coords)
        ax.plot(xs, ys, color=cmap(norm(d)), lw=1.2, zorder=3)
    sm = cm.ScalarMappable(norm=norm, cmap=cmap)
    cbar = fig.colorbar(sm, ax=ax, shrink=0.5, pad=0.01)
    cbar.set_label("downstream manhole depth (m)", fontsize=9)
    for p in pipes:                                  # pumped pipes stand out
        if p.is_rising_main:
            xs, ys = zip(*p.geom.coords)
            ax.plot(xs, ys, color="#e74c3c", lw=2.6, ls="--", zorder=5)
    st = [n for n in nodes.values() if n.is_station]
    if st:
        ax.scatter([n.x for n in st], [n.y for n in st], s=150, marker="v",
                   facecolor="#e74c3c", edgecolor="k", lw=0.8, zorder=6,
                   label=f"pumping station ({len(st)})")
        for n in st:
            ax.annotate(f"{n.label} lift {n.lift_m:.1f} m", (n.x, n.y),
                        xytext=(9, 6), textcoords="offset points", fontsize=7,
                        color="#c0392b", zorder=7)
        ax.legend(loc="lower left", fontsize=8, framealpha=0.9)
    deep = [n for n in nodes.values() if (n.depth or 0) > 8.0]
    stt = summary.get("stations") or {}
    box = ("DEPTH PROFILE\n"
           f"max depth {summary['max_depth_m']:.1f} m (limit 12.0)\n"
           f"manholes over 8 m: {len(deep)}\n"
           f"drops/backdrops: {summary['drops']}\n"
           f"pumping stations: {stt.get('count', 0)}\n"
           f"properties pumped: {stt.get('properties_pumped', 0)}\n"
           f"total lift: {stt.get('total_lift_m', 0)} m")
    _frame(ax, boundary, "W8 — How deep the pipes sit below ground", box)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def lowplot_map(path, net, conn, still_low, boundary, summary):
    nodes, pipes = net.chambers, net.reaches
    fig, ax = plt.subplots(figsize=(11, 15), dpi=140)
    _background(ax, boundary.bounds)
    for p in pipes:
        xs, ys = zip(*p.geom.coords)
        ax.plot(xs, ys, color="#7f8c8d", lw=0.5, zorder=2)
    ok = [r for r in conn if r["ok"]]
    ax.scatter([r["x"] for r in ok], [r["y"] for r in ok], s=2, color="#27ae60",
               alpha=0.4, zorder=3, label=f"connectable ({len(ok)})")
    fixed = [r for r in conn if not r["ok"] and r not in still_low]
    ax.scatter([r["x"] for r in fixed], [r["y"] for r in fixed], s=14, color="#f39c12",
               zorder=4, label=f"recovered by deepening ({len(fixed)})")
    ax.scatter([r["x"] for r in still_low], [r["y"] for r in still_low], s=40, marker="x",
               color="red", zorder=5, label=f"local solution needed ({len(still_low)})")
    ax.legend(loc="upper left", fontsize=8)
    box = (f"HOUSE CONNECTABILITY (user mandate)\n"
           f"checked {summary['lowplots']['checked']} units\n"
           f"low plots {summary['lowplots']['flagged']} | deepened MH "
           f"{summary['lowplots']['deepened_mh']}\nresidual {summary['lowplots']['residual']}")
    _frame(ax, boundary, "W8 — Can every house drain into the sewer?", box)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def catchment_map(path, net, cats, boundary, summary):
    """One polygon per subnetwork: the ground it collects from, and where it joins the
    main pipe. Colours only separate neighbours — they carry no other meaning."""
    import itertools
    from matplotlib.patches import Polygon as MplPoly
    fig, ax = plt.subplots(figsize=(11, 15), dpi=140)
    _background(ax, boundary.bounds)
    palette = ["#8dd3c7", "#ffffb3", "#bebada", "#fb8072", "#80b1d3", "#fdb462",
               "#b3de69", "#fccde5", "#d9d9d9", "#bc80bd", "#ccebc5", "#ffed6f"]
    cyc = itertools.cycle(palette)
    for c in sorted(cats, key=lambda c: -c["area_ha"]):
        col = next(cyc)
        for poly in list(getattr(c["geom"], "geoms", [c["geom"]])):
            ax.add_patch(MplPoly(list(poly.exterior.coords), closed=True,
                                 facecolor=col, edgecolor="#2c3e50", lw=0.7,
                                 alpha=0.55, zorder=2))
    for p in net.reaches:                       # the sewer, faint, for orientation
        xs, ys = zip(*p.geom.coords)
        ax.plot(xs, ys, color="#34495e", lw=0.35, alpha=0.8, zorder=3)
    jx = [c["join_x"] for c in cats]
    jy = [c["join_y"] for c in cats]
    ax.scatter(jx, jy, s=26, marker="o", facecolor="#ffffff", edgecolor="#c0392b",
               lw=1.1, zorder=5, label=f"joins the main pipe ({len(cats)})")
    big = sorted(cats, key=lambda c: -c["n_props"])[:12]
    for c in big:
        p = c["geom"].representative_point()
        ax.annotate(f"C{c['cid']}\n{c['n_props']:.0f}", (p.x, p.y), ha="center",
                    fontsize=7, color="#1a1a1a", zorder=7)
    st = [n for n in net.chambers.values() if n.is_station]
    if st:
        ax.scatter([n.x for n in st], [n.y for n in st], s=120, marker="v",
                   facecolor="#e74c3c", edgecolor="k", lw=0.8, zorder=6,
                   label=f"pumping station ({len(st)})")
    ax.legend(loc="lower left", fontsize=8, framealpha=0.9)
    tot_p = sum(c["n_props"] for c in cats)
    pumped = [c for c in cats if c["pumped"]]
    box = ("CATCHMENTS\n"
           f"subnetworks: {len(cats)}\n"
           f"properties covered: {tot_p:,.0f}\n"
           f"largest: {max(c['n_props'] for c in cats):,.0f} props "
           f"({max(cats, key=lambda c: c['n_props'])['join_mh']})\n"
           f"smallest: {min(c['n_props'] for c in cats):,.0f} props\n"
           f"needing a pump on the way: {len(pumped)}")
    _frame(ax, boundary, "W8 — what each subnetwork collects", box)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
