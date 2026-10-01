"""Revision 4: the sewer network options S1 to S7 (Sections 6.2.5 to 6.2.8) and Appendix B.

Every number is read from facts_w17 (the SewerGEMS results of model IBRI_W17_R9, written by
W17/py/); the transfer diagrams are drawn in Figma from the same results (W17/py/diagram_layout.py),
the maps in QGIS (W17/gis/make_w17_project.py), the charts by charts_w17.py.
"""
import json
import os

import doc as D
import notes as N
import facts_w17 as F

IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img")
MAPS = os.path.join(F.W17, "Options 2026-10", "Maps")
fmt = F.fmt
WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven"}


def _img(name):
    return os.path.join(IMG, name + ".png")


def _map(name):
    """The maps are rendered into the deliverable folder; the report takes the same file."""
    p = os.path.join(MAPS, name + ".png")
    return p if os.path.exists(p) else _img(name)


def _chart(d, name, caption, width=17.0):
    D.chart(d, name, width, img=IMG)
    return D.fig_caption(d, caption)


def _subs(o):
    """Subnetworks served by each plant of option o, upstream order kept simple: by number."""
    p = F.plant_of(o)
    out = {}
    for s, z in p.items():
        out.setdefault(z, []).append(s)
    return {z: sorted(v, key=lambda s: int(s[1:])) for z, v in out.items()}


def _served(o):
    """'O1 (O-1): 19 subnetworks; O4 (O-7): O4 to O8' — the plant list of the options table."""
    parts = []
    for z, subs in _subs(o).items():
        if len(subs) == 1:
            what = "its own subnetwork only"
        elif len(subs) <= 6:
            what = ", ".join(subs)
        else:
            what = f"{len(subs)} subnetworks"
        parts.append(f"{F.name(z)}: {what}")
    order = F.summary(o)["stp"]
    return "; ".join(sorted(parts, key=lambda t: order.index(t.split(" ")[0])))


def _option_paragraph(d, o):
    """What distinguishes option o, in figures, before its diagram and map."""
    r = F.option_row(o); pl = F.plants(o); ps = F.pumps(o)
    if len(pl) == 1:
        z = next(iter(pl))
        lead = (f"All the flow is treated at one plant at {F.name(z)}: {fmt(pl[z]['avg']['2030'])} cubic metres "
                f"a day on average in 2030 and {fmt(pl[z]['avg']['2070'])} in 2070.")
    else:
        big = max(pl, key=lambda z: pl[z]["avg"]["2070"])
        rest = [z for z in pl if z != big]
        lead = (f"The flow is divided between {WORDS[len(pl)]} plants. The largest, at {F.name(big)}, receives "
                f"{fmt(pl[big]['avg']['2070'])} cubic metres a day on average in 2070; "
                + ", ".join(f"{F.name(z)} {fmt(pl[z]['avg']['2070'])}" for z in rest) + ".")
    big_ps = ps[0]
    far = r["longest_rm"]; high = r["highest_head"]
    text = (f"{lead} It needs {r['n_ps']} pumping stations with {fmt(r['kw'])} kW of pumps in duty; the largest lifts "
            f"{fmt(big_ps['duty'])} l/s from {F.name(big_ps['ps'])}. The longest rising main runs {fmt(far['L'] / 1000, 1)} km "
            f"from {F.name(far['ps'])}")
    text += (f", against {fmt(far['H'])} m of head." if far is high else
             f"; the highest head, {fmt(high['H'])} m, is at {F.name(high['ps'])}.")
    D.bullet(d, text, lead=f"Option {o}.  ")


# ===================================================================== 6.2.5 to 6.2.8
def network_options(d):
    """Sections 6.2.5 to 6.2.8, in place of Revision 3's note that the options would follow."""
    opts = F.available()
    L = F.loads(); Y = L["years"]
    s0 = F.summary(opts[0])

    # --------------------------------------------------------------- 6.2.5
    D.h(d, 3, "6.2.5.   The model")
    D.p(d, "The network is modelled in SewerGEMS as twenty-four subnetworks. Each collects the flow of its own "
           "catchment by gravity and ends at its lowest point, its outfall. Where an outfall is not at a treatment "
           "plant, a pumping station there lifts the flow through a rising main into a manhole of another "
           "subnetwork, or directly to a plant. The subnetworks are numbered O1 to O24; the figures give in brackets "
           "the outfall numbers of the earlier drawings.")
    D.p(d, f"The flow of every plot, established in Chapter 4, is placed at the manhole nearest to it for each of the "
           f"six model years: 2030, 2040, 2050, 2055, 2060 and 2070. The network carries "
           f"{fmt(Y['2030']['carried_m3d'])} cubic metres a day of it in 2030 and {fmt(Y['2070']['carried_m3d'])} in "
           f"2070. A further {fmt(Y['2030']['outside_m3d'])} cubic metres a day in 2030, rising to "
           f"{fmt(Y['2070']['outside_m3d'])} in 2070, lies at manholes that are not part of these options: branches in "
           "planted areas, where the ground levels are not reliable enough to lay a sewer until the survey is "
           "complete, and three small outlying catchments, where a sewer would be deep for little flow and an "
           "on-site solution such as an absorption well is proposed.")
    p = D.p(d, f"Infiltration of 720 litres a day for every kilometre of sewer is added along the pipes: "
               f"{fmt(L['infiltration_m3d'])} cubic metres a day over the {fmt(L['active_sewer_km'])} km of the network.")
    N.add(p, "PAM-GUD-201, Section 7.4.3, page 72.")
    D.p(d, "The model sets the peak flow in each pipe from the average flow upstream of it, with the peak factor of "
           "Section 4.2.6. The flow pumped from one subnetwork into another enters the receiving manhole as the peak "
           "outflow of the subnetwork that sends it, for the same year, and is not peaked a second time.")
    p = D.p(d, "Pipe friction follows the Colebrook-White equation with a roughness of 1.5 mm for every size.")
    N.add(p, "PAM-GUD-203, pages 24 and 28.")
    clean = all(F.checks_clean(o) for o in opts)
    p = D.p(d, "The pipes are designed for the flow of 2070, the year the land is full, and the design is repeated "
               "until no pipe changes size. The years 2030 to 2060 are then analysed on the designed pipes, which "
               "gives the flow arriving at each plant as the area develops. "
               + ("In every option and every year, no pipe runs faster than 3.0 m/s, and no pipe runs deeper than 65 per "
                  "cent of its diameter up to 350 mm, or 50 per cent above."
                  if clean else
                  "The pipes that exceed 3.0 m/s, or a depth of 65 per cent of the diameter up to 350 mm and 50 per cent "
                  "above, are listed with each option."))
    N.add(p, "PAM-GUD-203, page 27 and Table 10.")

    # --------------------------------------------------------------- 6.2.6
    D.h(d, 3, f"6.2.6.   The {WORDS[len(opts)]} options" if len(opts) > 1 else "6.2.6.   The option")
    D.p(d, "The options differ in where the flow is treated. The pipes run in the same streets in all of them; what "
           "changes is where each subnetwork's flow is sent, the sizes of the pipes that carry it, the pumping stations "
           "and their rising mains, and the number and size of the plants.")
    D.tab_caption(d, "The options and the subnetworks each plant serves")
    D.table(d, ["Option", "Plants", "Plants and the subnetworks they serve"],
            [[o, str(len(F.plants(o))), _served(o)] for o in opts],
            widths=[1.6, 1.6, 14.8], font=8.5)
    D.p(d, "")
    for o in opts:
        _option_paragraph(d, o)
    D.p(d, "For each option a diagram shows where the flow of every subnetwork goes, with the peak flow of each "
           "transfer in 2070, and a map shows the sewers coloured by the plant they drain to, each pumping station "
           "with the depth of its outfall and the head it pumps against, and the rising mains. They follow, option "
           "by option.")
    for o in opts:
        plants = " and ".join(F.name(z) for z in F.summary(o)["stp"])
        D.wide_figure(d, _img(f"W17_{o}_transfer_diagram"),
                      f"Option {o}, treatment at {plants}: where the flow of every subnetwork goes, with the peak "
                      "flow of each transfer in 2070.", size="A3")
        D.wide_figure(d, _map(f"W17_{o}_network"),
                      f"Option {o}: the sewers by the plant they drain to, the pumping stations with the depth of the "
                      "outfall, the pump head and the duty, and the rising mains.", size="A4")

    # --------------------------------------------------------------- 6.2.7
    D.h(d, 3, "6.2.7.   Comparison")
    rows = [F.option_row(o) for o in opts]
    D.tab_caption(d, "The options compared: network, depth and pumping")
    D.table(d, ["Option", "Plants", "Sewer, km", "Manholes deeper than 12 m", "Deepest manhole, m",
                "Pumping stations", "Pumps in duty, kW", "Energy 2030, MWh a year", "Energy 2070, MWh a year",
                "Rising mains, km"],
            [[r["option"], str(r["n_plants"]), fmt(r["pipe_km"]), str(r["mh_over_12"]), fmt(r["deepest"], 1),
              str(r["n_ps"]), fmt(r["kw"]), fmt(r["mwh_2030"]), fmt(r["mwh_2070"]), fmt(r["rm_km"], 1)] for r in rows],
            widths=[1.4, 1.3, 1.6, 2.0, 1.8, 1.8, 1.8, 2.0, 2.0, 1.8], font=8)
    D.p(d, "")
    D.p(d, f"Every option has the same {fmt(s0['pipe_km'])} km of sewer and {fmt(s0['manholes'])} manholes; they differ "
           "in the sizes of the trunk sewers, in the pumping and in the plants. The depth to invert is counted from the "
           "ground at each manhole, so a manhole deeper than 12 m in the table is not necessarily one with more than "
           "12 m of cover.")

    _chart(d, "W01_plant_split", "The average flow arriving at each plant in 2070, by option. Colours as on the maps "
                                 "and diagrams.")
    _chart(d, "W02_plant_years", "The average flow arriving at each plant, 2030 to 2070, by option.")

    D.tab_caption(d, "Average flow arriving at each plant, cubic metres a day, with the 2070 peak flow")
    prow = []
    for o in opts:
        for z, v in F.plants(o).items():
            prow.append([o, F.name(z)] + [fmt(v["avg"][y]) for y in F.YEARS] + [fmt(v["peak"]["2070"])])
    D.table(d, ["Option", "Plant"] + F.YEARS + ["Peak 2070, l/s"], prow,
            widths=[1.4, 2.4, 1.75, 1.75, 1.75, 1.75, 1.75, 1.75, 2.2], font=8)
    D.p(d, "")
    D.p(d, "The flows are the average daily flow of the plots served plus the infiltration of the sewers that drain to "
           "the plant. The peak is the sum of the peak flows of the outfalls that reach the plant. The ten per cent "
           "margin for a new plant is not included; it is applied when the plant is sized, in Section 6.5.")

    _chart(d, "W03_pumping", "Pumping stations by option: the pumps in duty, and the energy they use in 2030 and "
                             "2070. The count of stations is above each bar.")
    _chart(d, "W04_depth", "Manholes deeper than 9 m by option, split at 12 m, with the deepest manhole.")

    D.callout(d, "Pumping figures.",
              "The rising mains follow the roads and streets, and run across open ground where that route is more "
              "than 1.6 times the straight line, at 1.1 times its length. Each station pumps the 2070 peak flow of "
              "everything that reaches it, raised where needed to keep 1.0 m/s in a main of at least 75 mm; the main "
              "is the size that needs the least power within 2.5 m/s. Friction in the mains is taken with a "
              "Hazen-Williams coefficient of 120 and 10 per cent for fittings; the wet well is 1.5 m below the "
              "incoming sewer, the discharge 0.3 m above the invert of the receiving manhole, or 3 m above the ground "
              "at a plant; the pumps run at 65 per cent wire-to-water efficiency. These are concept values, to be "
              "replaced by the routes, the levels and the pumps of the preliminary design.",
              fill="F2F2F2", colour=D.GREY, border="BFBFBF")
    D.p(d, "")

    long = {o: F.retention_flags(o) for o in opts}
    worst = max(((r, o) for o in opts for r in long[o]), key=lambda t: t[0]["ret2030"], default=None)
    counts = {o: len(long[o]) for o in opts}
    lo_o = min(counts, key=counts.get); hi_o = max(counts, key=counts.get)
    many = (f"{counts[lo_o]} stations" + (" in every option" if len(opts) > 1 else f" in option {lo_o}")
            if counts[lo_o] == counts[hi_o] else
            f"from {counts[lo_o]} stations in option {lo_o} to {counts[hi_o]} in option {hi_o}")
    p = D.p(d, "Two features of the pumping need attention whichever option is chosen. First, a long rising main "
               f"carrying a small flow holds the sewage for hours. In 2030, {many} hold it longer than the 30 minutes "
               "the guideline aims for"
               + (f", the longest {fmt(worst[0]['ret2030'] / 60)} hours in the main from {F.name(worst[0]['ps'])}"
                  if worst else "") +
               ". Sulphide forms in that time, and these mains need the hydrogen sulphide evaluation the guideline "
               "asks of the designer, with dosing or a shorter route.")
    N.add(p, "PAM-GUD-203, page 50 (retention) and Section 11.1, page 162 (the evaluation).")
    heads = sorted(((r["H"], r["ps"], o) for o in opts for r in F.pumps(o)), reverse=True)
    if heads and heads[0][0] > 100:
        h, s, _ = heads[0]
        hi_opts = sorted({o for hh, ss, o in heads if ss == s and hh > 100})
        D.p(d, f"Second, the station at {F.name(s)} lifts a few litres a second through a long main against about "
               f"{fmt(round(h, -1))} m of head in option{'s' if len(hi_opts) > 1 else ''} {', '.join(hi_opts)}. "
               "A connection of that kind is to be "
               "reconsidered at the preliminary design: a shorter route to a nearer subnetwork, or local treatment.")

    # --------------------------------------------------------------- 6.2.8
    sy = json.load(open(os.path.join(F.RES, "S1", "selfcleansing_year.json"), encoding="utf-8"))
    si = json.load(open(os.path.join(F.RES, "S1", "selfcleansing_info.json"), encoding="utf-8"))
    D.h(d, 3, "6.2.8.   When the network becomes self-cleansing")
    p = D.p(d, "Nama Water Services asked in which year every pipe reaches the self-cleansing velocity of 0.75 m/s at "
               "its peak flow. The question is answered here with the head pipes allowed as steep as 4 per cent: for "
               "every pipe and every year, the gradient at which that year's peak flow reaches 0.75 m/s in the pipe's "
               "own size is calculated, and the pipe counts as self-cleansing from the first year in which that "
               "gradient is 4 per cent or less.")
    N.add(p, "PAM-GUD-203, page 26 (0.75 m/s at peak flow); Colebrook-White with a roughness of 1.5 mm. Calculated on "
             "option S1; the head pipes, which decide the answer, carry the same flow in every option.")
    D.tab_caption(d, "Pipes that reach 0.75 m/s at their peak flow at a gradient of 4 per cent or less")
    D.table(d, ["Year", "Pipes", "Share of the pipes", "Length, km", "Share of the length", "Head pipes"],
            [[y, fmt(v["pipes"]), f"{100 * v['share']:.0f} %", fmt(v["km"]), f"{100 * v['share_length']:.0f} %",
              f"{fmt(v['head_pipes'])} of {fmt(sy['head_pipes'])}"] for y, v in sy["years"].items()],
            widths=[2.0, 2.4, 2.8, 2.4, 2.8, 3.4], font=8.5)
    D.p(d, "")
    nv = sy["never"]
    D.p(d, f"In no year does every pipe reach it. The share grows from {100 * sy['years']['2030']['share']:.0f} per cent "
           f"of the pipes in 2030 to {100 * sy['years']['2070']['share']:.0f} per cent in 2070 and then stops, because "
           f"at saturation the number of houses on each street is fixed by the plots. The other {fmt(nv['pipes'])} pipes, "
           f"{fmt(nv['km'])} km of 200 mm sewer at the heads of the network, never carry enough: a 200 mm sewer needs "
           f"a peak flow of {sy['dn200_q_need_ls']:.2f} l/s, the flow of about {sy['houses']} houses, to reach 0.75 m/s "
           f"at 4 per cent, and about {si['dn200_q_for_075_at_1pc_ls']:.1f} l/s at 1 per cent. Whether a pipe can "
           "clean itself by velocity depends on how many houses drain into it, not on the year.")
    h30, h70 = si["groups"]["2030 head pipes"], si["groups"]["2070 head pipes"]
    p = D.p(d, f"The guideline provides for this case. At the head of the system, where the self-cleansing velocity "
               f"may not be attainable, the minimum gradient is set by the minimum tractive force. At a tractive stress "
               f"of 1 pascal the head pipes need a median gradient of {h30['median_tractive_pc']:.1f} per cent in 2030 "
               f"and {h70['median_tractive_pc']:.1f} per cent in 2070, and more than 4 per cent only below "
               f"{si['q_tractive_4pc_ls']:.4f} l/s, pipes carrying little more than their own infiltration. The "
               "guideline also asks for more frequent inspection and cleansing in the early years of development.")
    N.add(p, "PAM-GUD-203, page 27 (tractive force at the head of the system) and Section 4.2.6 (early "
             "development).")
    D.callout(d, "Decision required.",
              "The year from which the network is to be self-cleansing (2030, the opening year, or a later year); "
              "the tractive stress for the head pipes (1 pascal, or another value); and whether 4 per cent is the "
              "steepest gradient for every pipe or for the head pipes only. A steeper network is deeper and needs "
              "more pumping, and the cost of each choice will be given once it is made. This completes Decision 7 "
              "(Section 3.3.2).")


# ===================================================================== Appendix B
def appendix_b(d):
    """The depth maps and the quantities of every option."""
    opts = F.available()
    D.chapter(d, "Appendix B.   Network options: depth and quantities")
    D.p(d, "This appendix gives, for each option, the depth of the 2070 design on a map, and the quantities of pipe "
           "and manholes the options are compared on.")
    ods = sorted({od for o in opts for od in F.od_classes(o)})
    D.tab_caption(d, "Length of sewer by outside diameter, metres")
    D.table(d, ["Outside diameter, mm"] + opts,
            [[str(od)] + [fmt(1000 * F.od_classes(o).get(od, 0)) if F.od_classes(o).get(od, 0) else "" for o in opts]
             for od in ods] + [["Total"] + [fmt(1000 * F.summary(o)["pipe_km"]) for o in opts]],
            widths=[3.4] + [14.6 / len(opts)] * len(opts), font=8)
    D.p(d, "")
    bands = list(F.summary(opts[0])["manholes_by_band"])
    D.tab_caption(d, "Manholes by depth to invert")
    D.table(d, ["Depth"] + opts,
            [[b.replace("-", " to ").replace(">", "over ")] + [fmt(F.summary(o)["manholes_by_band"].get(b, 0)) for o in opts]
             for b in bands] + [["Total"] + [fmt(F.summary(o)["manholes"]) for o in opts]],
            widths=[3.4] + [14.6 / len(opts)] * len(opts), font=8)
    D.p(d, "")
    D.tab_caption(d, "Length of sewer by depth to invert, metres")
    pb = list(F.summary(opts[0])["pipe_km_by_band"])
    D.table(d, ["Depth"] + opts,
            [[b.replace("-", " to ").replace(">", "over ")] + [fmt(1000 * F.summary(o)["pipe_km_by_band"].get(b, 0)) for o in opts]
             for b in pb],
            widths=[3.4] + [14.6 / len(opts)] * len(opts), font=8)
    D.p(d, "")
    D.p(d, "The pumping stations of every option, with their flows, rising mains, heads and energy, are listed in the "
           "tables delivered with this report.")
    D.wide_figures(d, [(_map(f"W17_{o}_depth"), f"Option {o}: depth of the 2070 design. Sewers by depth to invert, "
                                                "width by size; manholes deeper than 9 m marked, those deeper than 12 m "
                                                "in red.") for o in opts], size="A4")
