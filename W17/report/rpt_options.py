"""The sewer network options S1 to S7 (Sections 6.2.5 to 6.2.8), their comparison and recommendation (7.11, 8.4,
the executive summary) and Appendix B.

Every number is read from facts_w17 (the SewerGEMS results of model IBRI_W17_R9, written by
W17/py/); the transfer diagrams are drawn from the same results (W17/py/diagram_layout.py),
the maps in QGIS (W17/gis/make_w17_project.py), the charts by charts_w17.py.
Client register (engineer, 2026-10-01): current names only (O1 ... O24), never the earlier outfall
numbers, no file or folder names, no internal steps; the depth of the sewer at each plant is given.
"""
import json
import os

import doc as D
import notes as N
import facts_w17 as F
import facts_cost as C
from basis_items import APPROVALS, number

IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img")
MAPS = os.path.join(F.W17, "Options 2026-10", "Maps")
fmt = F.fmt
WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven"}


def _img(name):
    return os.path.join(IMG, name + ".png")


def _map(name):
    """The maps are rendered into the deliverable folder and copied here by W17/gis/make_w17_project.py."""
    p = _img(name)
    return p if os.path.exists(p) else os.path.join(MAPS, name + ".png")


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
    """'O1: 19 subnetworks; O4: O4, O5, O6, O7, O8' — the plant list of the options table."""
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
    return "; ".join(sorted(parts, key=lambda t: order.index(t.split(":")[0])))


def _option_paragraph(d, o):
    """What distinguishes option o, in figures, before its diagram and map."""
    r = F.option_row(o); pl = F.plants(o); ps = F.pumps(o)
    if len(pl) == 1:
        z = next(iter(pl))
        lead = (f"All the flow is treated at one plant at {F.name(z)}: {fmt(pl[z]['avg']['2030'])} cubic metres "
                f"a day on average in 2030 and {fmt(pl[z]['avg']['2070'])} in 2070. The sewer arrives at the plant "
                f"{pl[z]['inlet']:.1f} m below ground.")
    else:
        big = max(pl, key=lambda z: pl[z]["avg"]["2070"])
        rest = [z for z in pl if z != big]
        lead = (f"The flow is divided between {WORDS[len(pl)]} plants. The largest, at {F.name(big)}, receives "
                f"{fmt(pl[big]['avg']['2070'])} cubic metres a day on average in 2070, its sewer arriving "
                f"{pl[big]['inlet']:.1f} m below ground; "
                + ", ".join(f"{F.name(z)} receives {fmt(pl[z]['avg']['2070'])} at {pl[z]['inlet']:.1f} m" for z in rest)
                + ".")
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
           "subnetwork, or directly to a plant. The subnetworks take the names of their outfalls, O1 to O24, as "
           "shown in the figure on the following page.")
    D.wide_figure(d, _map("W17_overview_subnetworks"),
                  "The twenty-four subnetworks of the sewer network, each with its outfall, and the settlement "
                  "boundaries.", size="A4")
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
    D.p(d, f"The design horizon is still to be decided ({number('The design horizon')}). The pipes are designed for 2070 so that the network "
           "is laid once and is not relieved while the plots around it are still being built (Section 4.1.9). The flow "
           "at each plant is given for every model year, 2055 among them, so that the plants can be phased on either "
           "horizon.")

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
    D.p(d, "Three figures follow for each option: a diagram of where the flow of every subnetwork goes, with the peak "
           "flow of each transfer in 2070; a map of the sewers by the plant they drain to, with the depth of the "
           "sewer arriving at each plant; and a map of the pumping, on which each pumping station carries the depth "
           "of its outfall, the average flow it receives in 2070, its pump head and its duty.")
    for o in opts:
        D.wide_figure(d, _img(f"W17_{o}_transfer_diagram"),
                      f"Option {o}, {F.text(o)}: where the flow of every subnetwork goes, with the peak flow of each "
                      "transfer in 2070.", size="A3")
        D.wide_figure(d, _map(f"W17_{o}_zones"),
                      f"Option {o}: the sewers by the plant they drain to, the outfalls, and the depth of the sewer "
                      "arriving at each plant.", size="A4")
        D.wide_figure(d, _map(f"W17_{o}_network"),
                      f"Option {o}: the sewers by plant and size, the pumping stations and the rising mains. A station "
                      "label gives the outfall, its depth and the average flow in 2070, then the pump head and the "
                      "duty.", size="A4")

    # --------------------------------------------------------------- 6.2.7
    D.h(d, 3, "6.2.7.   Comparison")
    rows = [F.option_row(o) for o in opts]
    D.tab_caption(d, "The options compared: network, depth and pumping")
    D.table(d, ["Option", "Plants", "Sewer at the plants, m deep", "Manholes deeper than 12 m", "Deepest manhole, m",
                "Pumping stations", "Pumps in duty, kW", "Energy 2030, MWh a year", "Energy 2070, MWh a year",
                "Rising mains, km"],
            [[r["option"], str(r["n_plants"]), r["inlet_depths"], str(r["mh_over_12"]), fmt(r["deepest"], 1),
              str(r["n_ps"]), fmt(r["kw"]), fmt(r["mwh_2030"]), fmt(r["mwh_2070"]), fmt(r["rm_km"], 1)] for r in rows],
            widths=[1.4, 1.3, 2.6, 2.0, 1.8, 1.7, 1.7, 1.9, 1.9, 1.7], font=8)
    D.p(d, "")
    D.p(d, f"Every option has the same {fmt(s0['pipe_km'])} km of sewer and {fmt(s0['manholes'])} manholes; they differ "
           "in the sizes of the trunk sewers, in the pumping and in the plants. The depth of the sewer at a plant is the "
           "depth below ground of the gravity sewer arriving at the plant site, one figure for each plant in the order "
           "of the plants table; the plant's inlet works lift the flow from that depth. Manhole depths are measured from "
           "the cover to the invert.")

    _chart(d, "W01_plant_split", "The average flow arriving at each plant in 2070, by option. Colours as on the maps "
                                 "and diagrams.")
    _chart(d, "W02_plant_years", "The average flow arriving at each plant, 2030 to 2070, by option.")

    D.tab_caption(d, "Average flow arriving at each plant, cubic metres a day, with the 2070 peak flow and the depth of "
                     "the incoming sewer")
    prow = []
    for o in opts:
        for z, v in F.plants(o).items():
            prow.append([o, F.name(z)] + [fmt(v["avg"][y]) for y in F.YEARS] + [fmt(v["peak"]["2070"]), f"{v['inlet']:.1f}"])
    D.table(d, ["Option", "Plant"] + F.YEARS + ["Peak 2070, l/s", "Sewer at the plant, m deep"], prow,
            widths=[1.3, 1.3, 1.65, 1.65, 1.65, 1.65, 1.65, 1.65, 1.9, 2.0], font=8)
    D.p(d, "")
    c70 = F.flow_chain("2070")
    D.p(d, "The flows are the average daily flow of the plots served plus the infiltration of the sewers that drain to "
           f"the plant. In every option the plants together receive {fmt(c70['at_plants'])} cubic metres a day in 2070: "
           f"the {fmt(c70['carried'])} the network carries and {fmt(c70['infiltration'])} of infiltration. The ten per "
           f"cent margin for a new plant is not included; it is applied when the plant is sized (Section 6.5), and "
           f"brings the plants together to {fmt(c70['design'])}. The peak is the sum of the peak flows of the outfalls "
           "that reach the plant, the flow its inlet works receive if every catchment peaks at the same time. It is "
           "higher than the peak hourly flow of Section 3.4.1, which applies one peak factor to the plant's whole "
           "average flow, because the peak factor falls as the flow grows.")

    _chart(d, "W03_pumping", "Pumping stations by option: the pumps in duty, and the energy they use in 2030 and "
                             "2070. The count of stations is above each bar.")
    n12s = [r["mh_over_12"] for r in rows]; dms = [r["deepest"] for r in rows]; kms = [r["km_over_12"] for r in rows]
    if max(n12s) - min(n12s) <= 2 and max(dms) - min(dms) <= 0.3:   # near equal: a sentence says it better than bars
        rng = lambda a, b, nd=0: fmt(a, nd) if round(a, nd) == round(b, nd) else f"{fmt(a, nd)} to {fmt(b, nd)}"
        D.p(d, f"The depth hardly changes between the options: in every option {rng(min(n12s), max(n12s))} manholes "
               f"are deeper than 12 m, {rng(min(kms), max(kms), 1)} km of sewer lies deeper than 12 m and the deepest "
               f"manhole is at {rng(min(dms), max(dms), 1)} m. The deep sewers are set by the ground within the "
               "subnetworks, which the options do not change; where the flow is treated changes the trunk sizes and the "
               "pumping, not the depth.")
    else:
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

    # the lift at the plant inlets: the stations are not the only pumping an option needs
    il = {o: F.inlet_lift(o) for o in opts}
    D.p(d, "The stations are not the only lift. Each plant's inlet works lift the arriving flow from the depth of its "
           "sewer to the inlet channels. On the same concept values, the wet well 1.5 m below the arriving sewer and "
           "the inlet works 3 m above the ground, the energy of the stations and of the plant inlets together is as "
           "follows.")
    ref = opts[0]
    D.tab_caption(d, "Pumping energy of the stations and of the plant inlets, MWh a year")
    D.table(d, ["Option", "Stations 2030", "Plant inlets 2030", "Together 2030", "Stations 2070", "Plant inlets 2070",
                "Together 2070", f"Together 2070 against {ref}"],
            [[o, fmt(F.summary(o)["mwh_2030"]), fmt(il[o]["mwh"]["2030"]), fmt(F.energy_total(o, "2030")),
              fmt(F.summary(o)["mwh_2070"]), fmt(il[o]["mwh"]["2070"]), fmt(F.energy_total(o, "2070")),
              "" if o == ref else
              f"{100 * (F.energy_total(o, '2070') / F.energy_total(ref, '2070') - 1):+.0f} %".replace("-", "−")]
             for o in opts],
            widths=[1.6, 2.2, 2.3, 2.3, 2.2, 2.3, 2.3, 2.8], font=8)
    D.p(d, "")
    _chart(d, "W05_energy_total", "Pumping energy in 2070 by option: the network's pumping stations and the lift at "
                                  "the plant inlets.")
    big = max(F.plants(ref), key=lambda z: F.plants(ref)[z]["avg"]["2070"])
    D.p(d, f"The lift at the plants narrows the differences between the options but does not change their order. In "
           f"option {ref} the whole flow arrives {F.plants(ref)[big]['inlet']:.1f} m below ground, and lifting it at the "
           f"plant uses {fmt(il[ref]['mwh']['2070'])} MWh a year in 2070, against {fmt(F.summary(ref)['mwh_2070'])} "
           f"for the {F.summary(ref)['pumping_stations']} stations of the network.")

    long = {o: F.retention_flags(o) for o in opts}
    worst = max(((r, o) for o in opts for r in long[o]), key=lambda t: t[0]["ret2030"], default=None)
    counts = {o: len(long[o]) for o in opts}
    lo_o = min(counts, key=counts.get); hi_o = max(counts, key=counts.get)
    many = (f"{counts[lo_o]} stations" + (" in every option" if len(opts) > 1 else f" in option {lo_o}")
            if counts[lo_o] == counts[hi_o] else
            f"between {counts[lo_o]} and {counts[hi_o]} stations, depending on the option,")
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
        own = {o: hh for hh, ss, o in heads if ss == s}            # that station's head in every option that has it
        lo_h, hi_h = min(own.values()), max(own.values())
        where = ("in every option" if len(own) == len(opts) else
                 "in options " + ", ".join(sorted(own)[:-1]) + " and " + sorted(own)[-1] if len(own) > 1 else
                 f"in option {next(iter(own))}")
        spread = hi_h - lo_h >= 15
        against = (f"{fmt(round(lo_h, -1))} to {fmt(round(hi_h, -1))} m" if spread else f"about {fmt(round(hi_h, -1))} m")
        D.p(d, f"Second, the station at {F.name(s)} lifts a few litres a second through a long main against "
               f"{against} of head {where}{', depending on where it discharges' if spread else ''}. A connection of "
               "that kind is to be reconsidered at the preliminary design: a shorter route to a nearer subnetwork, or "
               "local treatment.")

    # --------------------------------------------------------------- 6.2.8
    sy = json.load(open(os.path.join(F.RES, "S1", "selfcleansing_year.json"), encoding="utf-8"))
    si = json.load(open(os.path.join(F.RES, "S1", "selfcleansing_info.json"), encoding="utf-8"))
    D.h(d, 3, "6.2.8.   When the network becomes self-cleansing")
    p = D.p(d, "This section sets out the year from which each pipe reaches the self-cleansing velocity of 0.75 m/s at "
               "its peak flow, with the head pipes allowed as steep as 4 per cent, the steepest gradient indicated by "
               "Nama Water Services. For every pipe and every year, the gradient at which that year's peak flow "
               "reaches 0.75 m/s in the pipe's own size is calculated, and the pipe counts as self-cleansing from the "
               "first year in which that gradient is 4 per cent or less.")
    N.add(p, "PAM-GUD-203, page 26 (0.75 m/s at peak flow); Colebrook-White with a roughness of 1.5 mm. Calculated on "
             "option S1; the head pipes, which decide the answer, carry the same flow in every option.")
    D.p(d, "The flows are those of the model, with every property connected and the infiltration included, which is "
           "the most favourable reading of the early years. With 61 per cent of the properties connected in 2030 "
           "(Section 4.2.8) and without infiltration, fewer pipes reach the velocity than the table shows.")
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
              f"more pumping. This extends "
              f"{number('Gradients and self-cleansing at the concept stage')} "
              "(Section 3.3.2).")


# ===================================================================== the recommendation
# Written once and used by the executive summary, Section 7.11 and Section 8.4.1, so the three cannot differ.
# The logic (engineer, 2026-10-04): the seven options are costed on one basis (facts_cost, the team's estimate); those
# within 10 per cent of the lowest whole-life cost go forward; S2 is set aside on energy; within the band S1, S3 and S7
# are equal on cost and on sustainability within concept accuracy, and S1 is first on operability. The characters are
# costed at the preliminary design. The treated effluent network is not part of the comparison: its customers are not
# defined at the concept stage.
RANK = ("first", "second", "third")


def _pct(a, b):
    """a against b, in whole per cent."""
    return f"{abs(100 * (a / b - 1)):.0f}"


def _and(items):
    """'O1, O4 and O9'."""
    items = [F.name(i) for i in items]
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


def _span(subs):
    """'O4 to O8' for a run of subnetworks, 'O22 and O23' otherwise."""
    n = [int(s[1:]) for s in subs]
    if len(n) > 2 and n == list(range(n[0], n[0] + len(n))):
        return f"{subs[0]} to {subs[-1]}"
    return _and(subs)


def _musd(x):
    """OMR as millions, one decimal."""
    return f"{fmt(x / 1e6, 1)} million OMR"


def _rec_text(o):
    """One recommended option, in figures: what it is, what it costs over its life, what it gains, what it needs."""
    pl = F.plants(o); r = F.option_row(o); ref = F.RECOMMENDED[0]
    e = F.energy_total(o, "2070"); e_ref = F.energy_total(ref, "2070")
    km = F.km_od_at_least(o); od = F.largest_od(o)
    w = C.whole_life(); lo = min(w.values()); gap = w[o] / lo - 1
    cost = (f"Its whole-life cost over 25 years is {_musd(w[o])}, "
            + ("the lowest of the seven options. " if gap < 1e-9 else f"{100 * gap:.1f} per cent above the lowest. "))
    if len(pl) == 1:
        z = next(iter(pl))
        return (f"One plant at {F.name(z)}, receiving {fmt(pl[z]['avg']['2030'])} cubic metres a day on average in 2030, "
                f"{fmt(pl[z]['avg']['2055'])} in 2055 and {fmt(pl[z]['avg']['2070'])} in 2070, built in phases on one "
                f"site. " + cost + "One plant to staff, supervise and secure, one sludge line, one discharge consent and "
                f"one source of treated effluent. It carries the largest trunk sewers, {fmt(km)} km of sewer of 1,000 mm "
                f"and over, up to {fmt(od)} mm, the deepest arrival at a plant, {pl[z]['inlet']:.1f} m, and {fmt(e)} MWh "
                "a year of pumping energy in 2070 with the lift at the plant.")
    big = max(pl, key=lambda z: pl[z]["avg"]["2070"]); rest = [z for z in pl if z != big]
    subs = _subs(o)
    served = "; ".join(f"{F.name(z)} treats " + ("its own subnetwork" if subs[z] == [z] else f"the flow of {_span(subs[z])}")
                       for z in rest)
    ps_diff = F.summary(ref)["pumping_stations"] - r["n_ps"]
    less_trunk = F.km_od_at_least(ref) - km
    tiny = min(pl, key=lambda z: pl[z]["avg"]["2070"])
    return (f"{WORDS[len(pl)].capitalize()} plants: {F.name(big)} with {fmt(pl[big]['avg']['2070'])} cubic metres a day "
            "in 2070, " + " and ".join(f"{F.name(z)} with {fmt(pl[z]['avg']['2070'])}" for z in rest) + f"; {served}. "
            + cost + f"Against {ref} it needs {_pct(e, e_ref)} per cent less pumping energy, {fmt(e)} MWh a year in "
            "2070, "
            + (f"{WORDS[ps_diff]} fewer pumping station{'s' if ps_diff > 1 else ''}, " if ps_diff > 0 else "")
            + f"{fmt(r['rm_km'], 1)} km of rising main against {fmt(F.option_row(ref)['rm_km'], 1)} km"
            + (f" and {fmt(less_trunk)} km less sewer of 1,000 mm and over" if less_trunk >= 1 else "")
            + f"; the largest sewer is {fmt(od)} mm. "
            + (f"The plant at {F.name(tiny)}, {fmt(pl[tiny]['avg']['2070'])} cubic metres a day in 2070, is small enough "
               "for the nature-based treatment the guideline allows up to about 500 cubic metres a day. "
               if pl[tiny]["avg"]["2070"] <= 500 else "")
            + f"It needs {WORDS[len(rest)]} further plant site{'s' if len(rest) > 1 else ''}, "
            + ("each " if len(rest) > 1 else "") + "with its buffer, access, power supply, staff and sludge line.")


def _why(d):
    """Why these three, and in this order: cost, the 10 per cent band, sustainability, operability."""
    rec = F.RECOMMENDED; ref = rec[0]
    rank = C.ranking(); w = C.whole_life(); lo = min(w.values())
    band = C.within_band(); gap = {o: g for o, _, g in rank}
    near = [o for o in band if o != ref]
    out = [o for o, _, _ in rank if o not in band]
    p = D.p(d, f"The seven options are first compared on whole-life cost, the capital cost and 25 years of operating "
               f"cost discounted at 5 per cent (Section 7.8). {ref} has the lowest, {_musd(lo)}. "
               + _and(near) + " are within 10 per cent of it, at "
               + ", ".join(f"{100 * gap[o]:.1f}" for o in near[:-1]) + f" and {100 * gap[near[-1]]:.1f} per cent above. "
               + _and(out) + f" are {100 * min(gap[o] for o in out):.0f} to {100 * max(gap[o] for o in out):.0f} per cent "
               "above it, outside the 10 per cent band, and are not taken further.")
    N.add(p, "PAM-GUD-201, page 106: options within ten per cent of one another on total lifetime cost are decided on "
             "sustainability.")
    e = {o: F.energy_total(o, "2070") for o in F.available()}
    setaside = [o for o in near if e[o] > e[ref]]
    for o in setaside:
        D.p(d, f"{o} is set aside within the band. It treats all the flow at {_and(F.summary(o)['stp'])}, so the whole "
               f"flow of {_and(F.plants(ref))} is pumped there: {fmt(e[o])} MWh a year in 2070, {_pct(e[o], e[ref])} per "
               f"cent more than {ref}. It is neither cheaper nor more sustainable than {ref}.")
    alt = [o for o in near if o not in setaside]
    plant_mwh = C.data()["kw_plants"][ref] * 8760 / 1000
    shares = [100 * (e[ref] - e[o]) / (e[ref] + plant_mwh) for o in alt]
    D.p(d, "Within that band the guideline adopts the more sustainable option. "
           + _and(alt) + " use " + " and ".join(f"{_pct(e[o], e[ref])}" for o in alt)
           + f" per cent less pumping energy than {ref}, " + " and ".join(fmt(e[ref] - e[o]) for o in alt)
           + " MWh a year in 2070. With the energy of the treatment plants counted, that is "
           + (f"{min(shares):.0f} to {max(shares):.0f}" if round(min(shares)) != round(max(shares)) else f"{max(shares):.0f}")
           + " per cent of the energy of the whole system, while a second or third plant uses more energy for each "
             "cubic metre treated than one large plant and adds its own construction. Within the accuracy of a concept "
             f"estimate, plus or minus 20 per cent, {_and(rec)} are therefore equal on whole-life cost and on "
             "sustainability.")
    ns = {o: F.option_row(o)["n_ps"] for o in rec}
    D.p(d, f"{ref} is placed first on operability. It has one plant to staff, supervise and secure, one sludge line, "
           "one discharge consent, one odour buffer and one source of treated effluent, against two or three of each, "
           f"while its network is almost the same: {ns[ref]} pumping stations against "
           + " and ".join(f"{ns[o]} in {o}" for o in rec[1:]) + f". {rec[1]} follows as the lower cost of the two "
           f"alternatives, and {rec[2]} third.")


def recommendation(d, numbered=True):
    """The reasoning, the three recommended options in order, and what the order rests on.
    numbered: the options as a numbered list (7.11); else as bullets led by the option (summary)."""
    rec = F.RECOMMENDED
    _why(d)
    for i, o in enumerate(rec):
        if numbered:
            D.numbered(d, _rec_text(o), lead=f"{o}.  ", restart=(i == 0))
        else:
            D.bullet(d, _rec_text(o), lead=f"{o}, {RANK[i]}.  ")
    p = D.p(d, "The order is the consultant's assessment; the weight given to each criterion is set by Nama Water "
               "Services (Section 6.1.4). The three characters of the guidelines (Section 6.1.1) change the treatment "
               "process, the energy supply and the reuse, not the network on which the order rests; they are costed at "
               "the preliminary design, where the treatment process is selected.")
    N.add(p, "PAM-GUD-201, Section 12.1, page 95, and Sections 12.6 to 12.9, pages 104 to 106. The accuracy of a "
             "concept estimate: PAM-GUD-201, Table 2, pages 17 to 20.")


# ===================================================================== Sections 7.11, 8.4 and 8.4.1
def appraisal(d):
    """Section 7.11: the sewer network options compared on their technical results and their whole-life cost, and the
    three recommended."""
    rec = F.RECOMMENDED
    D.sub(d, "The sewer network options")
    D.p(d, f"The {WORDS[len(F.available())]} sewer network options of Section 6.2 are compared on their technical "
           "results (Section 6.2.7) and on their whole-life cost (Section 7.8). The depth of the network does not "
           "separate them; the trunk sewers, the pumping and the number of plants do.")
    recommendation(d, numbered=True)
    pl = {o: F.plants(o) for o in rec}; r = {o: F.option_row(o) for o in rec}
    w = C.whole_life(); lo = min(w.values()); cd = C.data()
    D.tab_caption(d, "The three recommended options")
    D.table(d, [""] + rec, [
        ["Priority"] + [RANK[i].capitalize() for i in range(len(rec))],
        ["Plants"] + [", ".join(F.name(z) for z in pl[o]) for o in rec],
        ["Largest plant, average 2070, m³/d"] + [fmt(r[o]["largest_plant_2070"]) for o in rec],
        ["Sewer at the plants, m deep"] + [r[o]["inlet_depths"] for o in rec],
        ["Pumping stations"] + [str(r[o]["n_ps"]) for o in rec],
        ["Rising mains, km"] + [fmt(r[o]["rm_km"], 1) for o in rec],
        ["Sewers of 1,000 mm and over, km"] + [fmt(F.km_od_at_least(o)) for o in rec],
        ["Largest sewer, mm"] + [fmt(F.largest_od(o)) for o in rec],
        ["Pumping energy with the plant inlets, 2030, MWh a year"] + [fmt(F.energy_total(o, "2030")) for o in rec],
        ["Pumping energy with the plant inlets, 2070, MWh a year"] + [fmt(F.energy_total(o, "2070")) for o in rec],
        ["Rising mains holding the 2030 flow longer than 30 minutes"] + [str(len(F.retention_flags(o))) for o in rec],
        ["Capital cost, million OMR"] + [fmt(cd["capex_total"][o] / 1e6, 1) for o in rec],
        ["Operating cost in the first year, million OMR"] + [fmt(cd["opex1"][o] / 1e6, 2) for o in rec],
        ["Whole-life cost, 25 years, million OMR"] + [fmt(w[o] / 1e6, 1) for o in rec],
        ["Above the lowest whole-life cost"] + ["—" if w[o] == lo else f"{100 * (w[o] / lo - 1):.1f} %" for o in rec],
    ], widths=[6.6, 3.8, 3.8, 3.8], font=9)
    D.p(d, "")


def conclusions(d):
    """Section 8.4: what the network options and their costs established."""
    opts = F.available(); s0 = F.summary(opts[0]); c30 = F.flow_chain("2030"); c70 = F.flow_chain("2070")
    e = {o: F.energy_total(o, "2070") for o in opts}
    lo_e, hi_e = min(e, key=e.get), max(e, key=e.get)
    D.p(d, f"The sewer network has been modelled over the whole study area: twenty-four subnetworks, "
           f"{fmt(s0['pipe_km'])} km of sewer and {fmt(s0['manholes'])} manholes, designed for the flow of 2070 and "
           "within the guideline's limits on velocity and depth of flow in every option and every year. Whichever "
           f"option is chosen, the plants receive {fmt(c30['at_plants'])} cubic metres a day on average in 2030 and "
           f"{fmt(c70['at_plants'])} in 2070, infiltration included, and are designed for {fmt(c70['design'])} with "
           f"the ten per cent margin. The {WORDS[len(opts)]} options for where the flow is treated, from one plant to "
           "six, differ in the trunk sewers, the pumping and the plants, not in the depth of the network: the pumping "
           f"energy in 2070, with the lift at the plant inlets, runs from {fmt(e[lo_e])} MWh a year in {lo_e} to "
           f"{fmt(e[hi_e])} in {hi_e}.")
    rec = F.RECOMMENDED; rank = C.ranking(); band = C.within_band(); gap = {o: g for o, _, g in rank}
    out = [o for o, _, _ in rank if o not in band]
    D.p(d, f"Costed on one basis, {rec[0]} has the lowest whole-life cost, {_musd(C.whole_life()[rec[0]])} over 25 "
           f"years; {_and([o for o in band if o != rec[0]])} are within 10 per cent of it and {_and(out)} "
           f"{100 * min(gap[o] for o in out):.0f} to {100 * max(gap[o] for o in out):.0f} per cent above. Three are "
           f"recommended, in order of priority: {rec[0]}, one plant at {_and(F.plants(rec[0]))}; {rec[1]}, "
           f"{WORDS[len(F.plants(rec[1]))]} plants at {_and(F.plants(rec[1]))}; and {rec[2]}, "
           f"{WORDS[len(F.plants(rec[2]))]} plants at {_and(F.plants(rec[2]))}. The three are equal on whole-life cost "
           f"and on sustainability within the accuracy of a concept estimate, and {rec[0]} is the simplest to operate "
           "(Section 7.11). In every option some long rising mains hold the sewage for hours and need hydrogen "
           "sulphide control, the station at O23 pumps a few litres a second against a very high head, and the head "
           "pipes do not reach the self-cleansing velocity in any year.")


def recommendations(d):
    """Section 8.4.1, as a numbered list."""
    rec = F.RECOMMENDED
    items = [
        f"option {rec[0]} is taken forward to the preliminary design as the recommended option, with {rec[1]} and "
        f"{rec[2]} as the alternatives in that order (Section 7.11), and its treatment process, energy supply and reuse "
        "are selected there through the three characters of the guidelines (Section 6.1);",
        f"Nama Water Services takes the {WORDS[len(APPROVALS)]} decisions of Section 1.5.2, the design horizon and "
        "the overflow first among them, and the decision on the self-cleansing of the head pipes of Section 6.2.8, "
        f"which extends {number('Gradients and self-cleansing at the concept stage')};",
        "the connection of O23 and the long rising mains that hold the sewage for more than half an hour are "
        "reconsidered at the preliminary design: a shorter route, a nearer receiving subnetwork, local treatment or "
        "dosing (Section 6.2.7);",
        "Nama Water Services confirms the other matters of Section 1.5.4 and supplies the data requested in Section "
        "1.5.5, so that the preliminary design proceeds on an agreed basis.",
    ]
    for i, t in enumerate(items):
        D.numbered(d, t, restart=(i == 0))


# ===================================================================== executive summary
def summary_block(d):
    """The options in the executive summary: what was modelled, the options side by side with their whole-life cost,
    the recommendation and what needs attention whichever option is chosen."""
    opts = F.available()
    if not opts:
        return
    s0 = F.summary(opts[0]); rows = [F.option_row(o) for o in opts]
    n12 = sorted({r["mh_over_12"] for r in rows}); dms = [r["deepest"] for r in rows]
    w = C.whole_life(); lo = min(w.values())
    D.title(d, "The sewer network options", size=12, space_before=8)
    D.p(d, f"The sewer network is modelled in SewerGEMS as twenty-four subnetworks, {fmt(s0['pipe_km'])} km of sewer "
           f"and {fmt(s0['manholes'])} manholes. Each drains by gravity to its lowest point, its outfall, and the pipes "
           f"are designed for the flow of 2070. {WORDS[len(opts)].capitalize()} options have been modelled for where the "
           "flow is treated, from one plant to six; where an outfall is not at a plant, a pumping station lifts its "
           "flow into another subnetwork or to a plant. "
           + ("In every option and every year the pipes stay within the guideline's limits on velocity and depth of "
              "flow. " if all(F.checks_clean(o) for o in opts) else "")
           + f"The pipes run in the same streets in every option, and the depth hardly changes: "
             f"{'/'.join(str(n) for n in n12)} manholes are deeper than 12 m, the deepest {fmt(max(dms), 1)} m. The "
             "options differ in the trunk sewers, the pumping and the number and size of the plants, and so in their "
             "cost.")
    _chart(d, "W06_glance", "The seven options side by side in 2070: the plants and their flow, the pumping energy of "
                            "the stations and of the plant inlets, the trunk sewers, and the pumping stations with "
                            "their rising mains. The recommended options carry their priority.")
    D.tab_caption(d, "The sewer network options at a glance: 2070, and the whole-life cost over 25 years")
    D.table(d, ["Option", "Plants", "Largest plant, m³/d", "Sewer at the plants, m deep", "Pumping stations",
                "Sewers of 1,000 mm and over, km", "Pumping energy with the plant inlets, MWh a year",
                "Whole-life cost, million OMR"],
            [[r["option"], str(r["n_plants"]), fmt(r["largest_plant_2070"]), r["inlet_depths"], str(r["n_ps"]),
              fmt(F.km_od_at_least(r["option"])), fmt(F.energy_total(r["option"], "2070")),
              fmt(w[r["option"]] / 1e6, 1) + ("" if w[r["option"]] == lo else f" (+{100 * (w[r['option']] / lo - 1):.1f} %)")]
             for r in rows],
            widths=[1.4, 1.3, 2.3, 3.6, 1.9, 2.6, 2.9, 2.9], font=8.5)
    D.p(d, "")
    D.title(d, "Recommendation", size=12, space_before=8)
    D.p(d, "Three options are recommended, in this order of priority, on the reasoning below.")
    recommendation(d, numbered=False)
    D.p(d, "Three matters need attention whichever option is chosen. Long rising mains carrying small flows hold the "
           "sewage for hours and call for hydrogen sulphide control. The station at O23 lifts a few litres a second "
           "against a very high head and is to be reconsidered at the preliminary design. And no year brings every pipe "
           "to the self-cleansing velocity, even at 4 per cent: the criterion for the head pipes is the decision of "
           "Section 6.2.8. Section 6.2 presents the options in full.")


# ===================================================================== Appendix B
def appendix_b(d):
    """The depth maps and the quantities of every option."""
    opts = F.available()
    D.chapter(d, "Appendix B.   Network options: quantities, pumping stations and depth")
    D.p(d, "This appendix gives the quantities of pipe and manholes the options are compared on, the pumping stations "
           "of each option, and the depth of each option's 2070 design on a map.")
    ods = sorted({od for o in opts for od in F.od_lengths_m(o)})
    D.tab_caption(d, "Length of sewer by outside diameter, metres")
    D.table(d, ["Outside diameter, mm"] + opts,
            [[str(od)] + [fmt(F.od_lengths_m(o).get(od, 0)) if F.od_lengths_m(o).get(od, 0) else "" for o in opts]
             for od in ods] + [["Total"] + [fmt(sum(F.od_lengths_m(o).values())) for o in opts]],
            widths=[3.4] + [14.6 / len(opts)] * len(opts), font=8)
    D.p(d, "Lengths are rounded to the metre, so a total can differ by a metre or two from the sum of its rows.")
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
    D.p(d, "The pumping stations of each option follow, largest duty first. The duty is the 2070 peak flow of everything "
           "that reaches the station; the head is the static lift plus the friction in the rising main; the retention is "
           "the time the 2030 average flow takes to pass through the main. The figures rest on the concept values of "
           "Section 6.2.7.")
    for o in opts:
        D.tab_caption(d, f"Pumping stations of option {o}")
        D.table(d, ["Station", "Discharges to", "Duty, l/s", "Main, mm", "Main, m", "Static lift, m", "Head, m", "kW",
                    "MWh a year 2030", "MWh a year 2070", "Retention 2030, h"],
                [[F.name(r["ps"]), f"STP at {r['to']}" if r["kind"] == "plant" else r["to"], fmt(r["duty"], 1), str(r["dn"]),
                  fmt(r["L"]), fmt(r["static"], 1), fmt(r["H"], 1), fmt(r["kw"], 1), fmt(r["kwh2030"] / 1000, 1),
                  fmt(r["kwh2070"] / 1000, 1), fmt(r["ret2030"] / 60, 1)] for r in F.pumps(o)],
                widths=[2.2, 2.3, 1.4, 1.3, 1.4, 1.5, 1.4, 1.2, 1.7, 1.7, 1.9], font=7.5)
        D.p(d, "")
    D.wide_figures(d, [(_map(f"W17_{o}_depth"), f"Option {o}: depth of the sewers to invert in the 2070 design, the "
                                                "depth of each pumping station's outfall, and the deepest manhole of "
                                                "every run deeper than 12 m.") for o in opts], size="A4")
