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


def network_map(path, nodes, pipes, pockets, of_rep, boundary, summary):
    fig, ax = plt.subplots(figsize=(11, 15), dpi=140)
    _background(ax, boundary.bounds)
    for p in pipes:
        xs, ys = zip(*p["geom"].coords)
        ax.plot(xs, ys, color=DN_COLOR.get(p["dn_mm"], "#7f8c8d"),
                lw=0.6 + p["dn_mm"] / 400.0, zorder=3)
    ax.plot(of_rep["x"], of_rep["y"], marker="v", ms=14, color="red", zorder=8)
    ax.annotate("OUTFALL", (of_rep["x"], of_rep["y"]), textcoords="offset points",
                xytext=(8, -12), fontsize=9, color="red", weight="bold", zorder=8)
    for pk in pockets:
        s = nodes[pk["site"]]
        ax.plot(s["x"], s["y"], marker="s", ms=10, mfc="none", mec="red", mew=2, zorder=8)
        ax.annotate(f"SLS ({pk['n_props']}p)", (s["x"], s["y"]), textcoords="offset points",
                    xytext=(8, 8), fontsize=8, color="red", zorder=8)
    dn_km = summary["dn_km"]
    handles = [Line2D([], [], color=DN_COLOR[int(k)], lw=2,
                      label=f"DN{k} — {v:.1f} km") for k, v in dn_km.items() if int(k) in DN_COLOR]
    handles.append(Line2D([], [], color="#d35400", ls="--", label="test boundary"))
    ax.legend(handles=handles, loc="upper left", fontsize=8)
    box = (f"W4 TEST-BOUNDARY SEWER DESIGN\n"
           f"area {summary['s1']['boundary_ha']:.0f} ha | net {summary['net_km']:.1f} km | "
           f"{summary['n_nodes']} MH\n"
           f"units {summary['loads']['loaded_points']} (farms excl. "
           f"{summary['loads']['farms_excluded']})\n"
           f"Qadf {summary['qadf_outfall_m3d']:.0f} m3/d | "
           f"Qpeak {summary['qpeak_outfall_ls']:.0f} L/s ({summary['pf_formula']})\n"
           f"audit violations: {summary['violations']}")
    _frame(ax, boundary, "W4 — Test-Boundary Gravity Sewer Network (by diameter)", box)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def depth_map(path, nodes, pipes, boundary, summary):
    fig, ax = plt.subplots(figsize=(11, 15), dpi=140)
    _background(ax, boundary.bounds)
    import matplotlib.cm as cm
    import matplotlib.colors as mcolors
    norm = mcolors.Normalize(vmin=1.5, vmax=12.0)
    cmap = cm.get_cmap("plasma") if hasattr(cm, "get_cmap") else plt.get_cmap("plasma")
    for p in pipes:
        d = nodes[p["dn"]].get("depth") or 2.0
        xs, ys = zip(*p["geom"].coords)
        ax.plot(xs, ys, color=cmap(norm(d)), lw=1.2, zorder=3)
    sm = cm.ScalarMappable(norm=norm, cmap=cmap)
    cbar = fig.colorbar(sm, ax=ax, shrink=0.5, pad=0.01)
    cbar.set_label("downstream manhole depth (m)", fontsize=9)
    deep = [n for n in nodes.values() if (n.get("depth") or 0) > 8.0]
    box = (f"DEPTH PROFILE\nmax depth {summary['max_depth_m']:.1f} m\n"
           f"manholes > 8 m: {len(deep)}\n"
           f"drops/backdrops: {summary['drops']}\n"
           f"SLS pockets: {summary['solver']['pockets']}")
    _frame(ax, boundary, "W4 — Excavation Depth (invert below ground)", box)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def lowplot_map(path, nodes, pipes, conn, still_low, boundary, summary):
    fig, ax = plt.subplots(figsize=(11, 15), dpi=140)
    _background(ax, boundary.bounds)
    for p in pipes:
        xs, ys = zip(*p["geom"].coords)
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
    _frame(ax, boundary, "W4 — Plot Connectability Check (house vs road elevation)", box)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
