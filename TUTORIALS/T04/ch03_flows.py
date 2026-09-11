"""T04 module ch03_flows - chapters 6, 7 and 8.

6  Water demand
7  The sewage of every plot
8  Flow through time and the two design cases

Every number is read from facts_w14 (the W14 outputs), from
W14/analysis/design_flows.json, or from the Inception Report workbook; every
guideline value carries its page. Nothing numeric is typed into the prose.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(HERE)), "W14", "report"))   # after T04: its doc.py must not shadow ours
import doc as D
import omml as M
import facts_w14 as F
UP, R = M.up, M.r
IMG = os.path.join(HERE, "img")

import json, re
from functools import lru_cache

REPO = os.path.dirname(os.path.dirname(HERE))
JSON = os.path.join(REPO, "W14", "analysis", "design_flows.json")
R0_BOOK = os.path.join(REPO, "_CLIENT", "Ibri Sewer Demand R0 2026 08 03.xlsx")


# ------------------------------------------------------------------ helpers
def _lead(d, lead, text, size=None):
    fmt = {"size": size} if size else {}
    return D.rich(d, (lead, dict(fmt, bold=True)), (text, fmt))


def _for(d, text):
    return _lead(d, "What it is for.  ", text)


def _rule(d, text):
    return _lead(d, "The rule.  ", text)


def _worked(d, text):
    return _lead(d, "Worked for Ibri.  ", text)


def _src(d, text):
    return D.rich(d, ("Source.  ", {"bold": True, "size": 9.5, "colour": D.GREY}),
                  (text, {"size": 9.5, "italic": True, "colour": D.GREY}))


def _lives(d, text):
    return D.rich(d, ("Where it lives.  ", {"bold": True, "size": 9.5, "colour": D.GREY}),
                  (text, {"size": 9.5, "colour": D.GREY}), space_after=10)


def _params(d, rows):
    D.table(d, ["Symbol", "Meaning", "Unit"], rows, widths=[2.6, 10.4, 3.5], font=9)
    D.p(d, "", space_after=2)


def _check(d, heading, items):
    D.h(d, 2, heading)
    for i, t in enumerate(items):
        D.numbered(d, t, restart=(i == 0))


def _and(names):
    names = list(names)
    if not names:
        return ""
    if len(names) == 1:
        return names[0]
    return ", ".join(names[:-1]) + " and " + names[-1]


def _pc(x):
    """A fraction printed as a percentage with a space, the document style: 0.22 -> '22 %'."""
    return f"{x * 100:.0f} %"


def _q(sym, s):
    return M.sub(R(sym), UP(s))


def _settle(key):
    return next(r for r in F.settlement_table() if r["key"] == key)


@lru_cache(None)
def _flows():
    with open(JSON, encoding="utf-8") as fh:
        return json.load(fh)


@lru_cache(None)
def _r0_connection():
    """Connected share of the population by year, Inception Report workbook,
    sheet Pop_Wilayat, row W_Pop_Connected. None if the workbook cannot be read."""
    try:
        import openpyxl
        wb = openpyxl.load_workbook(R0_BOOK, read_only=True, data_only=True)
        rows = list(wb["Pop_Wilayat"].iter_rows(min_row=1, max_row=30, values_only=True))
        yrs = next(r for r in rows if r and r[0] == "Gov_Code")
        con = next(r for r in rows if r and len(r) > 1 and r[1] == "W_Pop_Connected")
        return {int(y): float(con[i]) for i, y in enumerate(yrs)
                if isinstance(y, (int, float)) and i < len(con) and isinstance(con[i], (int, float))}
    except Exception:
        return None


@lru_cache(None)
def _engine():
    """The network engine's design constants, W13/py/sewnet/criteria.py, loaded by file
    path (standard library only), so the tutorial quotes the engine's own values."""
    import importlib.util
    path = os.path.join(REPO, "W13", "py", "sewnet", "criteria.py")
    spec = importlib.util.spec_from_file_location("t04_sewnet_criteria", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod          # dataclasses resolves the module by name
    spec.loader.exec_module(mod)
    return mod.DEFAULT


_SUP = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")


def _sci(x, nd=2):
    """2.33e-4 -> '2.33 × 10⁻⁴'."""
    m, e = f"{x:.{nd}e}".split("e")
    return f"{m} × 10" + str(int(e)).translate(_SUP)


def _rulings():
    """The engineer's confirmed rulings of 2026-09-11, as recorded in design_flows.json.
    Chapter 8 teaches exactly these; the build stops if the record says otherwise."""
    rc = _flows()["rules"]["rulings_confirmed"]
    assert rc["status"].startswith("confirmed"), rc["status"]
    assert rc["classes"] == ["velocity pass", "tractive pass", "needs washing"], rc["classes"]
    assert rc["regrade_class"] == "none" and rc["low_flow_threshold"] == "none"
    assert rc["low_case_infiltration"] == "left out", rc["low_case_infiltration"]
    assert "connected" in rc["low_case_property_count"], rc["low_case_property_count"]
    assert rc["tractive_sets_gradient"].startswith("no"), rc["tractive_sets_gradient"]
    k_rec = float(re.search(r"K = ([\d.eE+-]+)", rc["mara_constant"]).group(1))
    assert "m3/s" in rc["mara_constant"] and "no floor" in rc["mara_constant"]
    assert abs(k_rec - _engine().TRACTIVE_K) < 1e-12, (k_rec, _engine().TRACTIVE_K)
    steps = [float(s) for s in re.findall(r"([\d.]+) %", rc["concept_gradients"])]
    dn = int(re.search(r"DN(\d+)", rc["concept_gradients"]).group(1))
    assert len(steps) == 2 and steps[0] > steps[1], rc["concept_gradients"]
    return dict(rc, k=k_rec, step_sec=steps[0], step_trunk=steps[1], dn_trunk=dn)


# per-person rates, from the constants alone
LP = F.LPCD
ND_PC, GV_PC = F.R_ND * LP, F.R_GOV * LP
WATER_PC = LP + ND_PC + GV_PC
COMPOUND_PC = LP * (1 + F.R_ND) * (1 + F.R_GOV)
SEW_DOM_PC, SEW_ND_PC, SEW_GV_PC = LP * F.RET_DOM, ND_PC * F.RET_ND, GV_PC * F.RET_ND
SEW_PC = SEW_DOM_PC + SEW_ND_PC + SEW_GV_PC          # 171.3 l/d per person


# =================================================================== 6
def c06_demand(d):
    t = F.totals(); ps = F.plot_summary(); st = F.settlement_table()
    ib = _settle("IBRI")
    w_dom = sum(r["w_dom"] for r in st); w_nd = sum(r["w_nd"] for r in st)
    w_gov = sum(r["w_gov"] for r in st); w_spec = sum(r["w_spec"] for r in st)
    nd_pool = sum(r["nd_pool"] for r in st); gov_pool = sum(r["gov_pool"] for r in st)
    p = F.plots()
    nd_all, gov_all = int(p.G_NDOM.sum()), int(p.G_GOV.sum())
    est_split = [(r["name"], r["workers"]) for r in st if r["workers"] > 0]

    D.h(d, 1, "6   Water demand", page_break=True)
    D.p(d, "Sewage is calculated from the water people use, so the chain starts with water demand even "
           "though this is a sewerage scheme. The guideline divides demand into five components. Three of "
           "them are rates applied to the population: domestic, non-domestic and governmental. Two sit "
           "outside those rates and are added separately: special consumption and water delivered by "
           "tanker. On the wastewater side the guideline adds one more duty, an assessment of private wells "
           "and other water that never passes through the network. This chapter takes each in turn, "
           "explains the choice the guideline offers between two methods, and names the items that are "
           "still waiting for data.")

    D.tab_caption(d, "The components of water demand and how each is treated here")
    D.table(d, ["Component", "Guideline basis", "Clause", "Treated here as"], [
        ["Domestic", f"population × {F.fmt(LP)} l/c/d", "G201-p59–60, Tab 11", "applied to every dwelling"],
        ["Non-domestic", f"{_pc(F.R_ND)} of domestic, or G201 Table 12 unit rates", "G201-p60, §7.3.2", "the ratio, placed on the shop meters"],
        ["Governmental", f"{_pc(F.R_GOV)} of domestic, or calculated for the project", "G201-p61, §7.3.3", "the ratio, placed on the government meters"],
        ["Special", "provided by the developer", "G201-p61, §7.3.4", f"the two industrial estates, workers × {F.fmt(F.L_IND)} l/d"],
        ["Blue tankers", "assessed from filling-station records", "G201-p61–62, §7.3.5", "pending: no records held"],
        ["Other sources", "private wells and other abstraction assessed", "G201-p70, §7.4", "pending: no records held"],
    ], widths=[2.6, 5.4, 3.3, 5.2], font=8.5)
    D.p(d, "")

    # ------------------------------------------------------------ 6.1
    D.h(d, 2, "6.1   Domestic demand")
    _for(d, "Domestic demand is the base of the whole chain. The non-domestic and governmental streams are "
            "fractions of it, and it carries most of the sewage.")
    _rule(d, "Domestic water is the population multiplied by the governorate's unit consumption.")
    eq = D.next_eq()
    M.display(d, M.seq(_q("Q", "dom"), M.EQ, R("P"), M.TIMES, UP("LPCD")), number=eq)
    _params(d, [["Q dom", "domestic water demand", "l/d"],
                ["P", "population served", "persons"],
                ["LPCD", f"domestic unit consumption, {F.fmt(LP)} for Adh Dhahirah", "l/c/d"]])
    D.p(d, "The figure is worth understanding before it is used. The guideline derives it from the water "
           "the network delivers to domestic customers:")
    eq = D.next_eq()
    M.display(d, M.seq(UP("LPCD"), M.EQ,
                       M.frac(_q("W", "dom,acc"), M.seq(UP("OR"), M.TIMES, _q("N", "acc")))), number=eq)
    _params(d, [["W dom,acc", "total domestic water accounted for by the network", "l/d"],
                ["OR", "occupancy rate", "persons per property"],
                ["N acc", "active domestic accounts", "—"]])
    D.p(d, "Two things follow. First, the rate measures network water only. Water bought from a tanker or "
           "drawn from a private well is not in it, so those sources are added separately and adding them "
           "is not double counting (Section 6.5). Second, occupancy sits in the denominator: a higher "
           "occupancy gives a lower rate per person for the same metered volume, so the two cannot be "
           "chosen independently. The guideline calls the table values indicative figures from the 2024 "
           "Integrated Master Plan, to be used in the absence of updated figures and to be validated by "
           "Nama Water Services before design. The Inception Report workbook computes 163.5 l/c/d from "
           "actual consumption for 2021 to 2024, which agrees for every practical purpose.")
    _src(d, "G201-p59–60, §7.3.1 and Table 11, row Adh Dhahirah (164 l/c/d). Inception Report R0 workbook, "
            "Water Demand Criteria (163.5 l/c/d), as recorded in _BRAIN/02_DESIGN_CRITERIA.md §12c.")
    _worked(d, f"The study area houses {F.fmt(t['pop_today'])} people in {F.BASE_YEAR}. At {F.fmt(LP)} l/c/d "
               f"their domestic water is {F.fmt(w_dom)} m³/d. Ibri alone, {F.fmt(ib['people_today'])} people, "
               f"uses {F.fmt(ib['w_dom'])} m³/d.")
    _lives(d, "W14/py/plot_class_v2_apply.py. Field POP = G_DOM × OR_S on every plot; field W_DOM = "
              "POP × 164 / 1000, in m³/d. The constant is F.LPCD in W14/report/facts_w14.py.")

    # ------------------------------------------------------------ 6.2
    D.h(d, 2, "6.2   Non-domestic and governmental demand: the two tiers")
    _for(d, "The guideline offers two methods for the water used by shops, offices, schools and government "
            "buildings. Which one applies is set by the data available, not by preference, so the choice has "
            "to be made and stated.")
    _rule(d, "Tier A is the planning method: governorate ratios on domestic demand and published return "
             "rates. Tier B is the project-specific method: unit rates from G201 Table 12 and design flows to a "
             "stated international standard. The guideline's wording is mandatory for Tier B wherever "
             "detailed land use exists.")
    D.tab_caption(d, "The two tiers of the flow chain")
    D.table(d, ["", "Tier A: planning ratios", "Tier B: project-specific design"], [
        ["Applies to", "planning and forecasting across broad service areas",
         "a project where detailed land use information is available"],
        ["Non-domestic", f"{_pc(F.R_ND)} of domestic (G201 Table 11)",
         "G201 Table 12 unit rates per pupil, bed, employee or m² of floor area"],
        ["Governmental", f"{_pc(F.R_GOV)} of domestic (G201 Table 11)", "calculated specifically for the project"],
        ["Sewage", f"return rates {_pc(F.RET_DOM)} and {_pc(F.RET_ND)} (G201 Table 19)",
         "design flows to a stated standard such as BS EN 752, with site evidence"],
        ["Needs", "the population", "counts of pupils, beds, staff and floor areas"],
        ["Used here", "**yes**, declared as a departure", "no: the quantities are not held"],
    ], widths=[2.6, 6.4, 7.5], font=9)
    D.p(d, "")
    D.p(d, "The guideline's own words set the order. For non-domestic water, where the project has detailed "
           "land use, it \"shall be calculated using the reference values presented in the Table 12\". "
           "Governmental water is to be calculated for the project, \"not as a ratio of domestic "
           "consumption\". On the wastewater side, design flows for such a project follow a standard such as "
           "BS EN 752, and \"Calculations shall clearly state which standard has been used.\" The Tier A "
           "return rates are described as a framework for \"planning and forecasting purposes across "
           "broader service areas\". Above both tiers, a developer's calculation made on an approved "
           "method takes precedence over the whole chain.")
    D.tab_caption(d, "G201 Table 12: the unit rates Tier B needs (extract)")
    D.table(d, ["Category", "Quantity it is priced on", "Rate"], [
        ["Educational", "pupils and staff", "130 l/d each"],
        ["Hospitals", "beds and staff", "650 l/d each"],
        ["Commercial shopping", "floor area", "12.2 l/d per m²"],
        ["Office", "employees", "93 l/d each"],
        ["Mosques", "floor area", "185 l/d per m²"],
        ["Dry industry", "employees", "93 l/d each"],
        ["Wet industry", "none", "no rate: supplied by the developer"],
    ], widths=[4.5, 6.0, 6.0], font=9)
    D.p(d, "")
    D.p(d, "Every rate in G201 Table 12, extracted above, is priced on a quantity that describes the building in use: its floor "
           "area, its pupils, its beds, its staff. None is priced on the plot. Replacing floor area with "
           "cadastral plot area is wrong by an order of magnitude, because a mosque or a school stands on a "
           "fraction of its plot. Deriving the quantities from plot area, cover and storeys only disguises "
           "the same guess.")
    D.callout(d, "Departure: Tier A is used.",
              "Detailed land use is known plot by plot, so the condition for Tier B is met in form. It is not "
              "met in substance. No dataset held records pupils, beds, employees or floor areas, and the "
              "electricity file gives the tariff of each meter, not its consumption or the building behind "
              f"it. The published ratios of G201 Table 11 are therefore used for the volume, the return rates "
              f"of G201 Table 19 for the sewage, and no design-flow standard is yet named. G201 Table 12 will be "
              f"adopted "
              f"for non-domestic and governmental demand the day the quantities arrive. It is never applied "
              f"together with the ratios: unit rates on the shops plus the {_pc(F.R_ND)} and {_pc(F.R_GOV)} "
              f"uplifts count the same water twice.")
    _src(d, "G201-p59 §7.3 (precedence), G201-p60 §7.3.2, G201-p61 §7.3.3 and Table 12, G201-p70–71 §7.4.1 "
            "and Table 19; quotations as recorded in _BRAIN/02_DESIGN_CRITERIA.md §11.0. Project rule: the "
            "load basis, locked 2026-08-30. Declared in report R2 §10.1, rows \"Non-domestic and "
            "governmental demand\" and \"Design flow standard\".")
    _worked(d, f"The study area has {F.fmt(nd_all)} shop meters and {F.fmt(gov_all)} government meters on its "
               f"plots. Not one of them carries a floor area, a head count or a metered volume, which is why "
               f"G201 Table 12 cannot be applied to them.")
    _lives(d, "_BRAIN/02_DESIGN_CRITERIA.md §11.0 (the two tiers) and §11.1 (the locked load basis); the "
              "departures table in W14/report/rpt_cd.py, Section 10.1.")

    # ------------------------------------------------------------ 6.3
    D.h(d, 2, "6.3   The distributed ratios, and why they are never compounded")
    _for(d, "The two ratios set how much non-domestic and governmental water a settlement uses. They set the "
            "volume only. Where that volume is placed is a separate step (Chapter 7).")
    _rule(d, "Each ratio is a fraction of domestic demand alone. The three streams are added, never "
             "multiplied.")
    eq = D.next_eq()
    M.display(d, M.seq(_q("Q", "nd"), M.EQ, R(f"{F.R_ND:.2f}"), M.TIMES, _q("Q", "dom")), number=eq)
    eq = D.next_eq()
    M.display(d, M.seq(_q("Q", "gov"), M.EQ, R(f"{F.R_GOV:.2f}"), M.TIMES, _q("Q", "dom")), number=eq)
    eq = D.next_eq()
    M.display(d, M.seq(_q("Q", "water"), M.EQ, _q("Q", "dom"), M.PLUS, _q("Q", "nd"), M.PLUS, _q("Q", "gov"),
                       M.EQ, M.delim(M.seq(R("1"), M.PLUS, R(f"{F.R_ND:.2f}"), M.PLUS, R(f"{F.R_GOV:.2f}"))),
                       M.TIMES, _q("Q", "dom")), number=eq)
    _params(d, [["Q nd", "non-domestic water demand", "l/d"],
                ["Q gov", "governmental water demand", "l/d"],
                ["Q water", "water demand of the three population-based streams", "l/d"]])
    D.p(d, f"Per person the streams are {F.fmt(LP)} l/d domestic, {F.R_ND:.2f} × {F.fmt(LP)} = "
           f"{F.fmt(ND_PC, 2)} l/d non-domestic and {F.R_GOV:.2f} × {F.fmt(LP)} = {F.fmt(GV_PC, 2)} l/d "
           f"governmental, {F.fmt(WATER_PC, 2)} l/d in all.")
    D.p(d, "The column headings of G201 Table 11 read \"Distributed Non-Domestic Ratio (% LPCD)\" and \"Distributed "
           "Governmental Ratio (% LPCD)\". The word distributed matters. These are not demands a person "
           "makes. They are the governorate's recorded non-domestic and governmental volumes from the water "
           "balance, expressed against its domestic consumption. Both are measured against the same domestic "
           "base, which is why neither may be applied on top of the other.")
    D.callout(d, f"Never {F.fmt(LP)} × {1 + F.R_ND:.2f} × {1 + F.R_GOV:.2f}.",
              f"Compounding gives {F.fmt(COMPOUND_PC, 2)} l/c/d instead of {F.fmt(WATER_PC, 2)}. The extra "
              f"{F.fmt(COMPOUND_PC - WATER_PC, 2)} l/c/d is {_pc(F.R_GOV)} of the non-domestic water, a volume "
              f"that appears nowhere in the governorate balance the ratios came from. It is "
              f"{(COMPOUND_PC / WATER_PC - 1) * 100:.1f} % too much water, and it cannot be traced back to any "
              f"line of the guideline.", fill="EAF1F8", colour=D.MID)
    D.p(d, "The guideline also describes the ratios as spatially distributed consumption to be added to the "
           "domestic consumption, which reads as spreading them evenly across the population. This design "
           "keeps the volume and moves the placement: each settlement's non-domestic and governmental water "
           f"is placed on the meters that generate it. A street of houses therefore runs at "
           f"{F.fmt(SEW_DOM_PC, 1)} l/d of sewage per person, not {F.fmt(SEW_PC, 1)}, and a commercial street "
           f"carries the difference. The settlement total is the same either way. This is the second half of "
           f"the departure, and it is declared as such.")
    _src(d, "G201-p59 §7.3.1 (\"spatially distributed\"), G201-p60 Table 11, row Adh Dhahirah "
            f"(164 l/c/d, {_pc(F.R_ND)}, {_pc(F.R_GOV)}). Project rule: the load basis, locked 2026-08-30 "
            "(volume from the ratios, placement from land use). Declared in report R2 §10.1, row "
            "\"Allocation of non-domestic demand\".")
    _worked(d, f"In {F.BASE_YEAR} the study area's non-domestic water is {F.fmt(w_nd)} m³/d and its "
               f"governmental water {F.fmt(w_gov)} m³/d, against {F.fmt(w_dom)} m³/d domestic: ratios of "
               f"{w_nd / w_dom:.2f} and {w_gov / w_dom:.2f}, exactly the published ones. For Ibri the same "
               f"arithmetic gives {F.fmt(ib['w_nd'])} and {F.fmt(ib['w_gov'])} m³/d on "
               f"{F.fmt(ib['w_dom'])} m³/d domestic.")
    _lives(d, "W14/py/plot_class_v2_apply.py, the pools pool_nd_s and pool_gv_s (settlement people × 0.22 × 164 "
              "and × 0.14 × 164); W14/analysis/settlements_today.csv, columns W_NDOM and W_GOV. Constants "
              "F.R_ND and F.R_GOV.")

    # ------------------------------------------------------------ 6.4
    D.h(d, 2, "6.4   Special consumption: the two industrial estates")
    _for(d, "Some water is used by identified projects that the population ratios never covered. It has to be "
            "added on its own line, or it is missing from the flow.")
    _rule(d, f"An industrial-estate plot carries its workers at the dry-industry rate of {F.fmt(F.L_IND)} litres "
             "per employee per day. The estates' meters take no share of the settlement's non-domestic or "
             "governmental water, and any dwelling meter on an estate carries the domestic rate like any other.")
    eq = D.next_eq()
    M.display(d, M.seq(_q("Q", "spec"), M.EQ, R(F.fmt(F.L_IND)), M.TIMES, _q("N", "w")), number=eq)
    _params(d, [["Q spec", "special consumption of an estate plot", "l/d"],
                ["N w", "workers assigned to the plot", "—"],
                [F.fmt(F.L_IND), "G201 Table 12 rate for dry industry", "l/d per employee"]])
    D.p(d, "Two industrial estates lie inside the study area, at Al Tayyeb in the north-east of the town and "
           "at Tanam beside the treatment plant. Their meters are on the commercial tariff, which hid them in "
           "the electricity data. The guideline states that the ratios do not apply to identified "
           "non-domestic projects such as economic zones, which are determined case by case. It also states "
           "that special consumption, such as labour camps and industry with high water use, is provided by "
           "the developer and is not covered by population forecasts. The two estates are exactly that case.")
    D.p(d, "Using the G201 Table 12 rate here does not mix the tiers. The estates sit outside the ratios by the "
           "guideline's own words, so the rate is applied to a stream the ratios never contained and "
           "nothing is counted twice. For the same reason the estates' shop meters are kept out of the "
           "settlement's non-domestic pool: a share of the pool on an estate plot would load the estate's "
           "water a second time.")
    D.callout(d, "Outside assumption, tagged.",
              f"No workforce or discharge record has been supplied. The workforces, "
              f"{F.fmt(F.WORKERS['Al Tayyeb'])} at Al Tayyeb and {F.fmt(F.WORKERS['Tanam'])} at Tanam, are "
              f"estimated from the number of workshop meters and are spread over each estate's industrial "
              f"plots in proportion to area. They are to be replaced by the estates' own records.",
              fill="EAF1F8", colour=D.MID)
    _src(d, "G201-p59 §7.3.1 (identified projects), G201-p61 §7.3.4 (special consumption) and Table 12, "
            "dry industry. Workforce: outside assumption (engineer, 2026-09-09), declared in report R2 §10.1, "
            "row \"Industrial estates\".")
    wa, wt = F.WORKERS["Al Tayyeb"], F.WORKERS["Tanam"]
    _worked(d, f"{F.fmt(wa)} × {F.fmt(F.L_IND)} = {F.fmt(wa * F.L_IND / 1000, 1)} m³/d at Al Tayyeb and "
               f"{F.fmt(wt)} × {F.fmt(F.L_IND)} = {F.fmt(wt * F.L_IND / 1000, 1)} m³/d at Tanam, "
               f"{F.fmt(w_spec, 1)} m³/d of water in all. The Al Tayyeb estate lies in At Tayyib. The Tanam "
               f"estate's plots fall in more than one settlement of the partition, so its workforce is split: "
               + _and([f"{n} {F.fmt(w)}" for n, w in est_split if n != "At Tayyib"]) + " workers. The estates hold "
               f"{F.fmt(nd_all - nd_pool)} shop meters and {F.fmt(gov_all - gov_pool)} government meters that "
               f"take no share of any pool.")
    _lives(d, "W14/py/plot_class_v2_apply.py: field ESTATE marks the estate plots, WORKERS carries the "
              "assigned workers, W_SPEC = WORKERS × 93 / 1000 in m³/d. The workforces are F.WORKERS.")

    # ------------------------------------------------------------ 6.5
    D.h(d, 2, "6.5   Blue tankers and private wells: pending")
    _for(d, "Water that reaches a home by truck or from a well still becomes sewage. Because the domestic rate "
            "measures network water only, these volumes are outside it and must be assessed on their own.")
    _rule(d, "Where a tanker filling station lies within or near the project area, tanker consumption must "
             "be assessed explicitly from Nama Water Services station records (historical use, the area "
             "served and its change over the horizon), validated, and added to demand. Separately, the "
             "designer shall assess private wells, private water providers and other non-network "
             "abstraction so that their contribution to wastewater is accounted for. Tanker water returns "
             f"to the sewer at the domestic rate of {_pc(F.RET_DOM)}.")
    D.p(d, "Neither record is held. The position adopted is stated plainly. A household on tanker supply is "
           "metered for electricity like any other and carries the domestic rate, so its people are in the "
           "flow; the tanker volume itself is not, and no tanker or well term appears in any flow in this "
           "design. Both are open data requests. When the filling-station records arrive, the tanker volume "
           f"joins the domestic stream at {_pc(F.RET_DOM)}.")
    D.callout(d, "G201 Table 13 cannot be used as printed.",
              f"G201 Table 13 gives Adh Dhahirah a tanker volume of 5,145 m³/d, averaged over 2021 to 2023, and a "
              f"ratio of 333 % to network domestic consumption in 2023, by far the highest in Oman. The two "
              f"figures together imply a governorate network domestic consumption of about "
              f"{F.fmt(5145 / 3.33)} m³/d. This study area alone uses {F.fmt(w_dom)} m³/d of domestic water "
              f"at the guideline's own rate. The volume column is usable; the ratio is not, and it should be "
              f"raised with Nama Water Services rather than applied.")
    _src(d, "G201-p61–62 §7.3.5 and Table 13 (Adh Dhahirah 5,145 m³/d, 333 %); G201-p70 §7.4 and §7.4.1 "
            "(other water sources, binding); G201-p71 Table 19 (domestic and tanker 85 %). Declared in report "
            "R2 §10.1, rows \"Water supplied by tanker\" and \"Other water sources\".")
    _worked(d, "There is no Ibri number yet, and that is the point of the step: every flow in this tutorial is "
               "on the network-accounted basis, and a reader quoting one should say so.")
    _lives(d, "Nowhere in the plot table, by design. W14/docs/DESIGN_FLOWS_FOR_NETWORK.md §8 lists both as "
              "not in the flows and not to be assumed; the data request register carries them.")

    _check(d, "6.6   Check it yourself", [
        "Open W14/shp/PLOTS_load.shp. Sum W_DOM and POP. W_DOM × 1000 / POP must be 164.0 l/c/d.",
        "In W14/analysis/settlements_today.csv divide W_NDOM and W_GOV by W_DOM for any settlement. The "
        "answers must be 0.22 and 0.14.",
        f"Sum W_SPEC over the plots. It must equal the {F.fmt(sum(F.WORKERS.values()))} workers × 93 l/d, "
        f"{F.fmt(w_spec, 1)} m³/d.",
        "Filter the plots on ESTATE. Every estate plot must show W_NDOM = 0 and W_GOV = 0.",
        "Open PAM-GUD-201 page 60, Table 11, row Adh Dhahirah, and page 61, Table 12, row Dry Industry, and "
        "confirm 164 l/c/d, 22 %, 14 % and 93 l/d per employee.",
        "Look for a tanker or a well term anywhere in the plot table. There must be none until the records "
        "arrive.",
    ])


# =================================================================== 7
def c07_plot_flow(d):
    t = F.totals(); ps = F.plot_summary(); st = F.settlement_table()
    ib = _settle("IBRI"); ex = F.example_plot(); p = F.plots()
    w_nd = sum(r["w_nd"] for r in st); w_gov = sum(r["w_gov"] for r in st)
    w_dom = sum(r["w_dom"] for r in st); w_spec = sum(r["w_spec"] for r in st)
    nd_pool = sum(r["nd_pool"] for r in st)
    nd_all = int(p.G_NDOM.sum())
    agr = int(p.G_AGR.sum())
    nd_fb = [r["name"] for r in st if r["nd_pool"] == 0]
    gv_fb = [r["name"] for r in st if r["gov_pool"] == 0]
    gv_rows = [r for r in st if r["gov_pool"] > 0]
    gv_hi = max(gv_rows, key=lambda r: r["u_gov"]); gv_lo = min(gv_rows, key=lambda r: r["u_gov"])

    D.h(d, 1, "7   The sewage of every plot", page_break=True)
    D.p(d, f"This chapter turns the water of Chapter 6 into sewage and places it on the ground, plot by plot. "
           f"The cadastre holds {F.fmt(ps['total'])} plots: {F.fmt(ps['metered'])} built plots with electricity "
           f"meters and {F.fmt(ps['empty'])} empty ones. Every built plot gets its own average dry-weather flow "
           f"for {F.BASE_YEAR} from its meters. Every empty plot gets a flow from the people it will house in "
           f"each later year. The network then sums the plots upstream of each pipe.")
    D.p(d, "An earlier tutorial loaded every property at a flat five people and 171 l/c/d. That is replaced "
           "here: dwellings carry the domestic rate at their settlement's own occupancy, and the non-domestic "
           "and governmental water sits on the meters that use it.")

    # ------------------------------------------------------------ 7.1
    D.h(d, 2, "7.1   Return to the sewer")
    _for(d, "Not all water supplied reaches the sewer. The return rate converts each water stream into the flow "
            "the pipe actually receives.")
    _rule(d, f"Domestic and tanker water return {_pc(F.RET_DOM)}. Non-domestic water, which the guideline "
             f"defines as government and commercial together, returns {_pc(F.RET_ND)}.")
    eq = D.next_eq()
    M.display(d, M.seq(_q("Q", "ww"), M.EQ, R(f"{F.RET_DOM:.2f}"),
                       M.delim(M.seq(_q("Q", "dom"), M.PLUS, _q("Q", "tank"))), M.PLUS, R(f"{F.RET_ND:.2f}"),
                       M.delim(M.seq(_q("Q", "nd"), M.PLUS, _q("Q", "gov"), M.PLUS, _q("Q", "spec")))), number=eq)
    _params(d, [["Q ww", "average dry-weather sewage, before infiltration", "l/d or m³/d"],
                ["Q dom", "domestic water", "l/d or m³/d"],
                ["Q tank", "tanker water: zero until the filling-station records arrive", "l/d or m³/d"],
                ["Q nd, Q gov", "non-domestic and governmental water", "l/d or m³/d"],
                ["Q spec", "special consumption of the industrial estates", "l/d or m³/d"]])
    D.p(d, f"Per person, the three population streams give {F.RET_DOM:.2f} × {F.fmt(LP)} = "
           f"{F.fmt(SEW_DOM_PC, 1)}, {F.RET_ND:.2f} × {F.fmt(ND_PC, 2)} = {F.fmt(SEW_ND_PC, 2)} and "
           f"{F.RET_ND:.2f} × {F.fmt(GV_PC, 2)} = {F.fmt(SEW_GV_PC, 2)} litres a day, "
           f"{F.fmt(SEW_PC, 1)} l/d of sewage per person in all. Two rules of this design sit beside the "
           f"guideline's. An agricultural meter supplies an irrigation pump and returns nothing; the dwelling "
           f"on a farm is metered separately and carries the domestic rate. The estates' dry-industry water "
           f"returns {_pc(F.RET_ND)}, as other non-domestic water does.")
    _src(d, "G201-p70–71 §7.4.1 and Table 19 (Domestic & Tanker 85 %; Non-Domestic, government and commercial, "
            "54 %). Project rules: agricultural meters carry no load (engineer, 2026-08-30); the estates return "
            "54 % (engineer, 2026-09-10).")
    D.tab_caption(d, f"Water and sewage of the study area by stream, {F.BASE_YEAR}")
    D.table(d, ["Stream", "Water, m³/d", "Return", "Sewage, m³/d"], [
        ["Domestic", F.fmt(w_dom), f"{F.RET_DOM:.2f}", F.fmt(ps["s_dom"])],
        ["Non-domestic", F.fmt(w_nd), f"{F.RET_ND:.2f}", F.fmt(ps["s_nd"])],
        ["Governmental", F.fmt(w_gov), f"{F.RET_ND:.2f}", F.fmt(ps["s_gov"])],
        ["Industrial estates", F.fmt(w_spec), f"{F.RET_ND:.2f}", F.fmt(ps["s_spec"])],
        [f"Agricultural meters ({F.fmt(agr)})", "not counted", "0", "0"],
        ["**Total**", f"**{F.fmt(ps['w_today'])}**", "", f"**{F.fmt(ps['qadf_today'])}**"],
    ], widths=[5.5, 3.5, 2.5, 5.0], font=9, align_right={1, 3})
    D.p(d, "")
    _worked(d, f"Ibri's {F.fmt(ib['w_dom'])} m³/d of domestic water returns {F.fmt(ib['s_dom'])} m³/d; its "
               f"{F.fmt(ib['w_nd'])} and {F.fmt(ib['w_gov'])} m³/d of non-domestic and governmental water return "
               f"{F.fmt(ib['s_nd'])} and {F.fmt(ib['s_gov'])} m³/d. Over the whole study area "
               f"{F.fmt(ps['qadf_today'] / ps['w_today'] * 100, 1)} % of the water becomes sewage.")
    _lives(d, "W14/py/plot_class_v2_apply.py: S_DOM = W_DOM × 0.85; S_NDOM, S_GOV and S_SPEC = W_NDOM, W_GOV "
              "and W_SPEC × 0.54; QADF = their sum, m³/d. Constants F.RET_DOM and F.RET_ND.")

    # ------------------------------------------------------------ 7.2
    D.h(d, 2, "7.2   The flow of an existing plot")
    _for(d, "Every built plot gets its own average dry-weather sewage flow for the base year, built from the "
            "meters that stand on it and the rates of its settlement.")
    _rule(d, "The flow of an existing plot, in litres a day, is")
    eq = D.next_eq()
    M.display(d, M.seq(_q("Q", "plot"), M.EQ, R(f"{F.RET_DOM:.2f}"), M.TIMES, R(F.fmt(LP)), M.TIMES, R("OR"),
                       M.TIMES, _q("N", "dom"), M.PLUS, R(f"{F.RET_ND:.2f}"), M.TIMES,
                       M.delim(M.seq(_q("U", "nd"), _q("N", "nd"), M.PLUS, _q("U", "gov"), _q("N", "gov"),
                                     M.PLUS, R(F.fmt(F.L_IND)), _q("N", "w")))), number=eq)
    _params(d, [["Q plot", f"average dry-weather sewage of the plot, {F.BASE_YEAR}", "l/d"],
                ["OR", "occupancy adopted for the plot's settlement", "persons per property"],
                ["N dom", "domestic meters on the plot, one property each", "—"],
                ["U nd", "non-domestic water per shop meter in the settlement (Section 7.3)", "l/d per meter"],
                ["N nd", "shop meters on the plot; none counted on an estate plot", "—"],
                ["U gov", "governmental water per government meter in the settlement (Section 7.3)", "l/d per meter"],
                ["N gov", "government meters on the plot; none counted on an estate plot", "—"],
                ["N w", "workers on an industrial-estate plot (Section 6.4)", "—"]])
    D.p(d, "Each term is one stream of Chapter 6 at its return rate. The first is the domestic stream: "
           "properties times occupancy gives people, times 164 gives water, times 0.85 gives sewage. The "
           "bracket holds the three streams that return 54 %. A plot of houses has only the first term. A "
           "shop, a school or a ministry building has only the bracket. Most plots in a town centre have "
           "both. An agricultural meter appears nowhere, because it returns nothing.")
    _src(d, "Project rule (engineer, 2026-09-10), built on G201-p60 Table 11, G201-p61 Table 12 (dry industry) "
            "and G201-p71 Table 19. Report R2 §15.4.")
    _worked(d, "Section 7.4 works one Ibri plot through the equation, term by term.")
    _lives(d, "Field QADF on every plot of W14/shp/PLOTS_load.shp, m³/d, written by W14/py/plot_class_v2_apply.py. "
              "Its inputs are on the same plot: G_DOM, OR_S, G_NDOM, U_NDOM, G_GOV, U_GOV, WORKERS.")

    # ------------------------------------------------------------ 7.3
    D.h(d, 2, "7.3   The unit rates per meter")
    _for(d, "The unit rates turn a settlement's non-domestic and governmental volume into a load on the "
            "particular plots that generate it.")
    _rule(d, "Each settlement's non-domestic and governmental water is a pool, sized by its people. The pool "
             "is divided equally among the settlement's shop meters, and among its government meters, outside "
             "the industrial estates.")
    eq = D.next_eq()
    M.display(d, M.seq(_q("U", "nd"), M.EQ, M.frac(M.seq(R(f"{F.R_ND:.2f}"), M.TIMES, R(F.fmt(LP)), M.TIMES,
                                                         _q("P", "s")), _q("N", "nd,s"))), number=eq)
    eq = D.next_eq()
    M.display(d, M.seq(_q("U", "gov"), M.EQ, M.frac(M.seq(R(f"{F.R_GOV:.2f}"), M.TIMES, R(F.fmt(LP)), M.TIMES,
                                                          _q("P", "s")), _q("N", "gov,s"))), number=eq)
    _params(d, [["P s", f"people of the settlement, {F.BASE_YEAR}", "persons"],
                ["N nd,s", "shop meters of the settlement outside the industrial estates", "—"],
                ["N gov,s", "government meters of the settlement outside the industrial estates", "—"]])
    D.p(d, "The share per meter is equal because the electricity file records no consumption. A large shop "
           "and a small one are the same meter to it. The settlement's total is right; how it splits between "
           "two shops in the same street is not known.")
    D.p(d, f"The estates' meters stay out of the pool for two reasons. Their water is already carried by "
           f"their workers (Section 6.4), so a pool share would load it twice. And their "
           f"{F.fmt(nd_all - nd_pool)} shop meters are {(nd_all - nd_pool) / nd_all * 100:.0f} % of all the "
           f"shop meters in the study area: counted in, they would draw that share of the towns' shop water "
           f"onto two industrial areas and thin the load on every town street.")
    D.p(d, f"A settlement with no shop meter or no government meter outside the estates keeps that share on "
           f"its dwellings, in proportion to their people. {_and(nd_fb)} have no shop meter outside the "
           f"estates; {_and(gv_fb)} have no government meter. Their shares ride on the houses, which is where "
           f"the guideline's own reading of the ratios would have put them in any case.")
    D.p(d, f"Where a settlement has few meters the rate per meter swings widely. The government rate runs from "
           f"{F.fmt(gv_lo['u_gov'])} l/d per meter in {gv_lo['name']} to {F.fmt(gv_hi['u_gov'])} in "
           f"{gv_hi['name']}, which has {gv_hi['gov_pool']} government meters. The settlement total is right "
           f"in both, and the volumes behind the extremes are small.")
    _src(d, "Project rule (engineer, 2026-09-10): unit rates per meter, the estates' meters out of the pool, the "
            "fallback to dwellings. The placement is the declared departure of Section 6.3 (G201-p59).")
    _worked(d, f"Ibri houses {F.fmt(ib['people_today'])} people and has {F.fmt(ib['nd_pool'])} shop meters and "
               f"{F.fmt(ib['gov_pool'])} government meters outside the estates. U nd = {F.R_ND:.2f} × "
               f"{F.fmt(LP)} × {F.fmt(ib['people_today'])} / {F.fmt(ib['nd_pool'])} = {F.fmt(ib['u_nd'])} l/d "
               f"per shop meter. U gov = {F.R_GOV:.2f} × {F.fmt(LP)} × {F.fmt(ib['people_today'])} / "
               f"{F.fmt(ib['gov_pool'])} = {F.fmt(ib['u_gov'])} l/d per government meter. The government rate "
               f"is {ib['u_gov'] / ib['u_nd']:.1f} times the shop rate: the governmental pool is "
               f"{F.R_GOV / F.R_ND * 100:.0f} % of the shop pool, but it is shared among one-tenth as many meters.")
    _lives(d, "Fields U_NDOM and U_GOV on every plot, l/d per meter; columns NDOM_POOL, GOV_POOL, U_NDOM and "
              "U_GOV in W14/analysis/settlements_today.csv. Computed in W14/py/plot_class_v2_apply.py "
              "(u_nd_s, u_gv_s), with the fallback to dwellings in the same block.")

    # ------------------------------------------------------------ 7.4
    D.h(d, 2, "7.4   One plot worked through")
    D.p(d, f"Take an illustrative plot in {ex['name']} with four domestic meters, two shop meters and one "
           f"government meter. The settlement's occupancy is {ex['or_used']:.2f} and its unit rates are "
           f"{F.fmt(ex['u_nd'])} and {F.fmt(ex['u_gov'])} l/d per meter.")
    D.tab_caption(d, "The flow of one plot, worked from its meters")
    D.table(d, ["Stream and meters", "Water, l/d", "Return", "Sewage, l/d"], ex["rows"],
            widths=[7.0, 2.6, 1.8, 5.1], font=9, align_right={1, 3})
    D.p(d, "")
    pure = 4 * ex["or_used"] * LP * F.RET_DOM
    D.p(d, f"The plot houses {F.fmt(ex['people'], 1)} people and sends {F.fmt(ex['q'])} l/d to the sewer, "
           f"{F.fmt(ex['q'] / ex['people'])} l/d per resident. That is well above {F.fmt(SEW_PC, 1)} because "
           f"the plot also carries shop and government water. The same four houses without the shops and the "
           f"office would send {F.fmt(pure)} l/d, {F.fmt(SEW_DOM_PC, 1)} per person. This is the placement at "
           f"work: the flow goes where the meters are.")

    # ------------------------------------------------------------ 7.5
    D.h(d, 2, "7.5   Shares and unit rates by settlement")
    D.p(d, "The table sets out, for every settlement, the three water shares, the meters that carry them, the "
           "unit rates, the estates' water and the resulting sewage. The plots sum to the settlement in every "
           "column. \"On dwellings\" marks the fallback of Section 7.3.")
    D.tab_caption(d, f"Water shares and unit rates by settlement, {F.BASE_YEAR}")
    D.table(d, ["Settlement", "People", "Domestic m³/d", "Non-domestic share m³/d", "Governmental share m³/d",
                "Shop meters", "Government meters", "l/d per shop meter", "l/d per government meter",
                "Estates m³/d", "Sewage m³/d"],
            F.unit_rate_rows(), widths=[2.3, 1.1, 1.2, 1.5, 1.7, 1.0, 1.6, 1.4, 1.6, 1.0, 1.2], font=6.8,
            keep_together=False)
    D.p(d, "")
    D.p(d, f"The Tanam estate's plots lie across more than one settlement, which is why estate water appears "
           f"in several rows. Totals are rounded from unrounded values and may differ by one from the sum of "
           f"the rows. In {F.BASE_YEAR} the study area generates {F.fmt(ps['qadf_today'])} m³/d: "
           f"{F.fmt(ps['s_dom'])} domestic, {F.fmt(ps['s_nd'])} non-domestic, {F.fmt(ps['s_gov'])} "
           f"governmental and {F.fmt(ps['s_spec'])} from the two estates.")
    D.picture(d, os.path.join(IMG, "C11_streams.png"), 14.0)
    D.fig_caption(d, f"Average dry-weather sewage of the study area in {F.BASE_YEAR}, by stream.")
    _worked(d, f"Ibri's row: {F.fmt(ib['s_dom'] + ib['s_nd'] + ib['s_gov'] + ib['s_spec'])} m³/d from "
               f"{F.fmt(ib['people_today'])} people is {F.fmt(ib['q_2024'] * 1000 / ib['people_today'], 1)} l/d "
               f"per person, the per-person rate of Section 7.1. It has to be: the pools are sized on people, so "
               f"a settlement with no estate always averages {F.fmt(SEW_PC, 1)} l/d per person, whatever the "
               f"placement inside it.")
    _lives(d, "F.unit_rate_rows() in W14/report/facts_w14.py reads W14/analysis/settlements_today.csv; chart "
              "C11 is drawn by W14/report/charts_w14.py.")

    # ------------------------------------------------------------ 7.6
    D.h(d, 2, "7.6   The future plot")
    _for(d, "An empty plot has no meters, so its flow is built from the people it houses in each later year.")
    _rule(d, f"A future plot carries its housed people at {F.fmt(SEW_PC, 1)} l/d each, all three streams "
             "together.")
    eq = D.next_eq()
    M.display(d, M.seq(_q("q", "fut"), M.EQ, R(F.fmt(LP)), M.TIMES,
                       M.delim(M.seq(R(f"{F.RET_DOM:.2f}"), M.PLUS, R(f"{F.R_ND:.2f}"), M.TIMES,
                                     R(f"{F.RET_ND:.2f}"), M.PLUS, R(f"{F.R_GOV:.2f}"), M.TIMES,
                                     R(f"{F.RET_ND:.2f}"))), M.EQ, R(F.fmt(SEW_PC, 1))), number=eq)
    eq = D.next_eq()
    M.display(d, M.seq(_q("Q", "fut"), M.EQ, _q("q", "fut"), M.TIMES, _q("P", "new")), number=eq)
    _params(d, [["q fut", "sewage per person on a future plot", "l/d"],
                ["Q fut", "sewage of the plot in the year", "l/d"],
                ["P new", "people housed on the plot in the year", "persons"]])
    D.p(d, "Where the shops, schools and offices of a district that does not yet exist will stand is not "
           "known. Putting each person's share of all three streams on the plot where the person lives keeps "
           "the settlement's total exact, and it lands the load on the street the sewer will run in. It is "
           "the same total per person as an existing settlement's, as Section 7.5 showed; only the "
           "placement differs. The housed people of a settlement are spread over its empty plots of up to "
           "2,000 m², in proportion to plot area capped at 1,000 m², so every plot the network passes "
           "carries a share.")
    D.p(d, "An existing plot keeps its base-year load in every later year. All growth, including the growth "
           "of a settlement's own people, is housed on empty plots. That is why a residential branch that is "
           "already built stays at 139.4 l/d per person, while a new district runs at 171.3.")
    _src(d, "G201-p60 Table 11 and G201-p71 Table 19 for the rates. Project rule (engineer, 2026-09-10): all "
            "three streams on the future plot; growth spread over empty plots of 2,000 m² or less by area "
            "capped at 1,000 m².")
    n30 = t["pop"][2030] - t["pop_today"]
    _worked(d, f"Between {F.BASE_YEAR} and 2030 the study area houses {F.fmt(n30)} more people. At "
               f"{F.fmt(SEW_PC, 1)} l/d they add {F.fmt(n30 * SEW_PC / 1000)} m³/d, which takes the total from "
               f"{F.fmt(t['q_today'])} to {F.fmt(t['q'][2030])} m³/d.")
    _lives(d, "W14/py/growth_by_settlement.py: Q_PER_CAP = 0.1713 m³/d per person; the plot fields POP_2030, "
              "Q_2030, POP_2055, Q_2055, POP_ULT and Q_ULT, where Q_year = QADF + new people × Q_PER_CAP.")

    # ------------------------------------------------------------ 7.7
    D.h(d, 2, "7.7   The fields on the plot")
    D.p(d, "Every term of this chapter is stored on the plot, so any plot's flow can be rebuilt by hand. The "
           "plot layer is W14/shp/PLOTS_load.shp.")
    D.tab_caption(d, "The load fields of the plot layer")
    D.table(d, ["Field", "Meaning", "Unit"], [
        ["SETTLE", "settlement the plot belongs to", "—"],
        ["G_DOM, G_NDOM, G_GOV", "domestic, shop and government meters on the plot", "—"],
        ["ESTATE, WORKERS", "industrial-estate flag and assigned workers", "—"],
        ["OR_S", "occupancy adopted for the settlement", "persons per property"],
        ["POP", f"people, {F.BASE_YEAR}", "persons"],
        ["U_NDOM, U_GOV", "the settlement's unit rates per shop and per government meter", "l/d per meter"],
        ["W_DOM, W_NDOM, W_GOV, W_SPEC, W_TOT", "water by stream and in total", "m³/d"],
        ["S_DOM, S_NDOM, S_GOV, S_SPEC", "sewage by stream", "m³/d"],
        ["QADF", f"average dry-weather sewage, {F.BASE_YEAR}", "m³/d"],
        ["POP_2030, POP_2055, POP_ULT", "people in 2030, 2055 and at saturation", "persons"],
        ["Q_2030, Q_2055, Q_ULT", "average dry-weather sewage in 2030, 2055 and at saturation", "m³/d"],
    ], widths=[5.2, 8.3, 3.0], font=8.5)
    D.p(d, "")
    D.callout(d, "The plot carries average flow only.",
              "It carries no peak, no infiltration, no tanker water and no private-well water. Peaking belongs "
              "to the accumulated flow in a pipe, infiltration to the pipe's length, and the plant margin to the "
              "works. They are added in the design, never stored on the plot.", fill="EAF1F8", colour=D.MID)

    _check(d, "7.8   Check it yourself", [
        "Pick any built plot. Rebuild QADF × 1000 from G_DOM, OR_S, G_NDOM, U_NDOM, G_GOV, U_GOV and WORKERS "
        "with the equation of Section 7.2. It must match to the litre.",
        "Sum QADF by SETTLE and compare with the sewage column of the settlement table. They must agree.",
        f"For any settlement without an estate, divide its sewage by its people. The answer must be "
        f"{F.fmt(SEW_PC, 1)} l/d per person.",
        "Filter the plots on ESTATE: W_NDOM and W_GOV must be zero, and W_SPEC must equal WORKERS × 0.093.",
        f"For any empty plot, (Q_2030 − QADF) / (POP_2030 − POP) must be {SEW_PC / 1000:.4f} m³/d per person.",
        "Pick a plot with only an agricultural meter. Its QADF must be zero.",
    ])


# =================================================================== 8
def c08_time(d):
    t = F.totals(); fl = _flows(); ult = t["ultimate"]
    ib = _settle("IBRI")
    con = _r0_connection()
    c = fl["rules"]["connection_ratio_2030"]
    low = fl["low_case_2030_m3d"]
    q_ult = fl["totals"][str(ult)]["qadf_m3d"] if str(ult) in fl["totals"] else t["q_ult"]
    q30 = fl["totals"]["2030"]["qadf_m3d"]
    wrong = q_ult * c
    S = {s["key"]: s for s in fl["settlements"]}
    props = fl["properties"]

    D.h(d, 1, "8   Flow through time and the two design cases", page_break=True)
    D.p(d, "A single saturation flow sizes the pipes. It says nothing about when the treatment plant must be "
           "built, and nothing about how little the network will carry in its first years. Both answers need "
           "the flow year by year. This chapter builds that series, then sets out the two flows every pipe is "
           "checked against: the saturation flow for size, and the opening-year flow at the connection ratio "
           "for self-cleansing.")

    # ------------------------------------------------------------ 8.1
    D.h(d, 2, "8.1   The model years and the reporting interval")
    _for(d, "The model years fix the flows the deliverables report and the hydraulic models run.")
    _rule(d, "The Terms of Reference name three design years and the ultimate: a start year to be agreed, 2030 "
             "as the middle year, 2055 as the end year, and the ultimate, saturated flow. Population and flow "
             "are projected at five-year intervals. The design horizon is the year of completion plus 25 years, "
             "or the ultimate saturated flow. The series is calculated every year and reported every five.")
    _src(d, "Terms of Reference (Data/scope.pdf) p3 (design horizon), p14 (design years for the models), p15 "
            f"item 12 (five-year interval). Base year {F.BASE_YEAR}: the year of the electricity accounts.")
    D.tab_caption(d, "The model years")
    D.table(d, ["Year", "Role", "People", "Qadf, m³/d"], [
        [str(F.BASE_YEAR), "base year: today's plots, from the meters", F.fmt(t["pop_today"]), F.fmt(t["q_today"])],
        ["2030", "middle design year; the opening-year case", F.fmt(t["pop"][2030]), F.fmt(t["q"][2030])],
        ["2055", "end design year", F.fmt(t["pop"][2055]), F.fmt(t["q"][2055])],
        [str(ult), "saturation: the last settlement is full; the sizing case", F.fmt(t["pop_ult"]), F.fmt(t["q_ult"])],
    ], widths=[1.8, 8.2, 3.0, 3.5], font=9, align_right={2, 3})
    D.p(d, "")
    _worked(d, f"The study area goes from {F.fmt(t['q_today'])} m³/d in {F.BASE_YEAR} to {F.fmt(t['q'][2030])} "
               f"in 2030, {F.fmt(t['q'][2055])} in 2055 and {F.fmt(t['q_ult'])} at saturation in {ult}. Ibri "
               f"itself is full in {ib['sat_year']}.")
    _lives(d, "W14/analysis/W14_growth_by_settlement.xlsx, sheets \"Qadf by year m3d\" (every settlement, every "
              "year 2024 to 2100) and \"Five-year Qadf\"; F.totals() in W14/report/facts_w14.py.")

    # ------------------------------------------------------------ 8.2
    D.h(d, 2, "8.2   How the series is built")
    _for(d, "The series turns today's plots and the growth of each settlement into a flow for every year.")
    _rule(d, f"Existing plots keep their {F.BASE_YEAR} flow. Each settlement grows at its own rate from the "
             "Inception Report, and the new people are housed on its empty plots until they are full; growth a "
             f"full settlement cannot house overflows to its neighbours. Every person housed adds "
             f"{F.fmt(SEW_PC, 1)} l/d.")
    eq = D.next_eq()
    M.display(d, M.seq(M.sub(R("Q"), UP("s")), M.delim(R("y")), M.EQ, M.sub(R("Q"), UP("s")),
                       M.delim(R(str(F.BASE_YEAR))), M.PLUS, _q("q", "fut"), M.TIMES,
                       M.sub(R("H"), UP("s")), M.delim(R("y"))), number=eq)
    _params(d, [["Q s(y)", "average dry-weather sewage of settlement s in year y", "m³/d"],
                ["Q s(" + str(F.BASE_YEAR) + ")", "the sum of its existing plots' QADF", "m³/d"],
                ["q fut", f"sewage per housed person, {F.fmt(SEW_PC / 1000, 4)}", "m³/d per person"],
                ["H s(y)", "people housed on its empty plots by year y, its own growth and overflow received",
                 "persons"]])
    _src(d, "Project rules (engineer, 2026-09-09 and 2026-09-10): growth rates from the Inception Report "
            "workbook, sheet Project Pop Settlements; capacity and overflow as the population chapter sets out.")
    h30 = ib["pop_2030"] - ib["people_today"]
    _worked(d, f"Ibri grows from {F.fmt(ib['people_today'])} people in {F.BASE_YEAR} to {F.fmt(ib['pop_2030'])} in "
               f"2030, so {F.fmt(h30)} people are housed on its empty plots. At {F.fmt(SEW_PC / 1000, 4)} m³/d "
               f"each they add {F.fmt(h30 * SEW_PC / 1000)} m³/d, which takes Ibri from {F.fmt(ib['q_2024'])} "
               f"to {F.fmt(ib['q_2030'])} m³/d.")
    _lives(d, "W14/py/growth_by_settlement.py: q = housed × Q_PER_CAP + q0, where q0 is the sum of QADF by "
              "settlement; sheet \"Qadf by year m3d\" of the workbook.")
    D.picture(d, os.path.join(IMG, "C09_flow.png"), 15.0)
    D.fig_caption(d, "Average dry-weather sewage of the study area by year: today's plots at their base-year "
                     "load, and the empty plots as they fill. The points mark the five-year reporting intervals.")

    # ------------------------------------------------------------ 8.3
    D.h(d, 2, "8.3   The flow at five-year intervals")
    D.p(d, "The table gives every settlement's average flow at five-year steps. A settlement's row is blank "
           "once it is full; its last two columns give the year it fills and the flow it then holds, which is "
           "the flow its pipes are sized on. Columns past the last saturation year are not printed.")
    D.tab_caption(d, "Average dry-weather sewage at five-year intervals to saturation, m³/d")
    cols, rows = F.five_year_rows("q")
    hdr = ["Settlement"] + [str(x) for x in cols[1:-1]] + ["Saturation year", "Saturation flow"]
    D.table(d, hdr, rows, widths=[2.3] + [0.95] * (len(hdr) - 3) + [1.5, 1.65], font=6.4,
            align_right=set(range(1, len(hdr))))
    D.p(d, "")
    first = min((r for r in F.settlement_table() if r["sat_year"]), key=lambda r: r["sat_year"])
    _worked(d, f"Ibri fills in {ib['sat_year']} at {F.fmt(S['IBRI']['q_ult'])} m³/d. The first settlement to "
               f"fill is {first['name']}, in {first['sat_year']}; the last are full in {ult}, when the study "
               f"area carries {F.fmt(t['q_ult'])} m³/d.")
    _lives(d, "F.five_year_rows(\"q\") reads sheet \"Five-year Qadf\" of W14/analysis/W14_growth_by_settlement.xlsx.")

    # ------------------------------------------------------------ 8.4
    D.h(d, 2, "8.4   The opening year and the connection ratio")
    _for(d, "Self-cleansing is decided in the first years, when the pipes carry least. That needs a year and a "
            "share of the people actually connected in that year.")
    _rule(d, f"The opening year is the construction year, or 2030, the first design year the Terms of Reference "
             f"fix; 2030 is used until a construction year is agreed. In that year the connected share is "
             f"{c:.2f}, the connection ratio of the Inception Report.")
    if con:
        D.p(d, f"The Inception Report carries the connected share of the population as a series. It is "
               f"{F.fmt(con[2024], 2)} in 2024, {F.fmt(con[2028], 2)} in 2028 and {F.fmt(con[2030], 2)} in 2030. "
               f"The rule takes {c:.2f}, the value reached in 2028, for the 2030 flow. The Report's own 2030 "
               f"value is higher, so {c:.2f} gives less flow than the Report would. For this check less flow is "
               f"the safe side (Section 8.7).")
    D.p(d, "The guideline assumes that collection coverage reaches 100 % by the end of the planning period, as "
           "customers connect to whatever collection system becomes available, and it asks the designer to "
           "secure self-cleansing velocities at the initial stage of operation. Full connection belongs to the "
           "sizing case; the ratio belongs to the opening years.")
    _src(d, "Terms of Reference p14 (start year to be agreed, 2030 middle year). Inception Report R0 workbook, "
            "sheet Pop_Wilayat, row W_Pop_Connected. G201-p73 §7.4.4 (coverage 100 % by the end of the period; "
            "self-cleansing at the initial stage). Project rule (engineer, 2026-09-11).")
    _worked(d, f"Ibri's 2030 flow is {F.fmt(S['IBRI']['q_2030'])} m³/d; at {c:.2f} connected, "
               f"{F.fmt(S['IBRI']['q_2030_low'])} m³/d. The whole study area: {F.fmt(q30)} × {c:.2f} = "
               f"{F.fmt(low)} m³/d.")
    _lives(d, "W14/analysis/design_flows.json: rules.opening_year, rules.connection_ratio_2030, "
              "low_case_2030_m3d and settlements[].q_2030_low.")

    # ------------------------------------------------------------ 8.5
    rc = _rulings(); E = _engine()
    tau = float(rc["tau_pa"])
    D.h(d, 2, "8.5   The two design cases")
    _for(d, "Every pipe is checked twice, on two different flows, because the two checks fail in opposite "
            "directions.")
    _rule(d, "Size and capacity on the saturation flow, fully connected. Self-cleansing on the 2030 flow at the "
             "connection ratio. Each is summed over the plots upstream of the pipe, then peaked for that pipe.")
    eq_size = D.next_eq()
    M.display(d, M.seq(_q("Q", "size"), M.EQ, M.nary("∑", R("i"), "", _q("Q", "ULT,i"), hide_hi=True)),
              number=eq_size)
    eq_low = D.next_eq()
    M.display(d, M.seq(_q("Q", "low"), M.EQ, R(f"{c:.2f}"), M.TIMES,
                       M.nary("∑", R("i"), "", _q("Q", "2030,i"), hide_hi=True)), number=eq_low)
    _params(d, [["Q size", "average flow for sizing: the sum over the upstream plots", "m³/d"],
                ["Q low", "average flow for the self-cleansing check", "m³/d"],
                ["Q ULT,i, Q 2030,i", "fields Q_ULT and Q_2030 of upstream plot i", "m³/d"],
                [f"{c:.2f}", "connection ratio in the opening year", "—"]])
    D.p(d, f"Both averages are then peaked per pipe. Over 100 properties upstream, the Merrimack formula gives "
           f"the peak daily flow, Qpdf = 2.65 Qadf^0.879, both in Ml/d. At 100 properties or fewer, the Peltier "
           f"alternative gives the peak factor, PF = 1.5 + 1/√Qm, with the average in l/s. The properties "
           f"upstream in a year are counted as G_DOM + (POP_year − POP) / OR_S per plot. The sizing case counts "
           f"the properties at saturation. The low case counts the connected properties, those standing in 2030 "
           f"× {c:.2f}, so that the count choosing the formula describes the same customers as the flow it "
           f"peaks. A pipe with more than 100 properties standing can therefore still take Peltier in the low "
           f"case; the lower count gives the lower peak at small flows, the safe direction for self-cleansing.")
    D.p(d, f"The sizing case adds infiltration at 720 l/d per kilometre of the pipe's own length, along the run. "
           f"The low case adds none. The guideline's infiltration clause says nothing about the opening years, "
           f"and its coverage clause asks only that self-cleansing velocities be secured at the initial stage "
           f"of operation. Leaving infiltration out gives the smaller flow, which is the safe side for this "
           f"check (Section 8.7). So the low case of Equation {eq_low}, peaked on the connected count and "
           f"with no infiltration, is the one flow that feeds both self-cleansing tests.")
    n_which = D.tab_caption(d, "Which flow for which check")
    D.table(d, ["Check", "Flow", "Why this flow"], [
        ["Pipe size and capacity: d/D and velocity limits", "Q_ULT upstream, peaked, plus infiltration",
         "saturation and full connection; an under-estimate surcharges the pipe"],
        ["Self-cleansing: velocity and tractive slope",
         f"Q_2030 × {c:.2f} upstream, peaked on the connected properties; no infiltration",
         "the opening years; an over-estimate declares a silting pipe self-cleansing"],
        ["Plant capacity and phasing", "settlement totals by year, plus infiltration, plus 10 %",
         "the growth curve decides when each stage is needed"],
    ], widths=[5.0, 5.2, 6.3], font=8.5)
    D.p(d, "")

    D.p(d, "The guideline asks for two approaches to self-cleansing, the self-cleansing velocity and the "
           "minimum tractive force. It makes the steeper of the two gradients the minimum gradient of the pipe, "
           "and at the head of a system, where the velocity cannot be reached, it lets the tractive force alone "
           "set the gradient. Its wording is \"shall\".")
    D.p(d, f"At the concept stage the project does not use the tractive force to set any gradient. Every pipe "
           f"is laid at the minimum gradient of G203 Table 11, tertiary pipes at G203 Table 5, on steps of "
           f"{rc['step_sec']:g} % for secondary pipes and {rc['step_trunk']:g} % for primary trunks of "
           f"DN{rc['dn_trunk']} and up (Chapter 11). The tractive force is then the second test of the audit "
           f"below. It will be applied to the gradients at the preliminary design, once Nama Water Services "
           f"confirms the tractive tension. The reason is that tension: the guideline gives no value for it, "
           f"so a gradient set on it now would rest on a number nobody has agreed.")
    D.callout(d, "Departure: the tractive force sets no gradient at the concept stage.",
              f"G203 §4.2.2.1 requires the steeper of the velocity and the tractive-force gradients. At the "
              f"concept stage the gradients are the Table 11 minimum and the tractive force only classifies "
              f"the pipes, at {tau:g} Pa. The departure is declared in report R2 §10.1, row \"Minimum "
              f"gradient\", for Nama Water Services to confirm, together with the tension.")

    D.p(d, "The audit gives every pipe one of three classes on the low case.")
    n_cls = D.tab_caption(d, "The self-cleansing classes on the low case")
    D.table(d, ["Class", "Test", "Action"], [
        ["Velocity pass", "at least 0.75 m/s at the low-case peak", "none"],
        ["Tractive pass",
         f"laid gradient at or above the Mara minimum, Smin = K τ^1.23 Q^−0.461, with τ = {tau:g} Pa, "
         f"K = {_sci(rc['k'])} and Q the true low-case peak in m³/s, with no floor", "none"],
        ["Needs washing", "everything else", "on the flushing list; not regraded, not upsized"],
    ], widths=[3.0, 8.9, 4.6], font=9)
    D.p(d, "")
    D.p(d, f"The classes are tried in the order of Table {n_cls}, and the first test a pipe passes gives its "
           f"class. There is no regrade class. A pipe laid to the guideline gradient that still carries too "
           f"little flow needs washing, not a steeper pipe. That is the guideline's own remedy: in the early "
           f"phases, when the flow is below the design flow, it asks the operator for more frequent inspection "
           f"and cleansing. Chapter 12 works the classes pipe by pipe.")
    D.callout(d, "Two values the guideline does not give.",
              f"The tractive tension: G203 gives no value. The concept stage uses {tau:g} Pa, the class is "
              f"decided at that value, and Nama Water Services is asked to confirm it before the preliminary "
              f"design. A low-flow threshold: G203 gives none, and the 1.5 l/s often quoted from the Mara "
              f"literature is not in PAM-GUD-203. It is not used. The tractive test runs on the true low-case "
              f"flow, however small.", fill="EAF1F8", colour=D.MID)
    _src(d, f"Project rules (engineer, 2026-09-11, confirmed): the two flow cases; the connected property count "
            f"and no infiltration in the low case; the three classes with no regrade class and no low-flow "
            f"threshold; K = {_sci(rc['k'])} with Q in m³/s and τ = {tau:g} Pa; gradients at the Table 11 "
            f"minimum on {rc['step_sec']:g} % and {rc['step_trunk']:g} % steps, the tractive force a test only "
            f"until the preliminary design. G201-p71 §7.4.2 (Merrimack, over 100 properties), G201-p72 (Peltier "
            f"alternative; hourly peak factor not to exceed 5.0, a recommendation), G201-p72 §7.4.3 "
            f"(infiltration 720 l/d per km; silent on the early years), G201-p73 §7.4.4 (self-cleansing at the "
            f"initial stage), G201-p73 §7.4.5 (plant +10 %). G203-p26 (0.75 m/s at peak flow); G203 §4.2.2.1 "
            f"pp 25–27 (two approaches shall be used, the steeper governs, tractive force alone at the head; "
            f"the Mara formula and K on p27); G203-p29 Table 11; G203-p18 Table 5; G203 §4.2.6 p28 (more frequent inspection and "
            f"cleansing in the early phases; no threshold). Tractive tension: none in G203 (GAP-9), NWS to "
            f"confirm. Departure from §4.2.2.1: report R2 §10.1, row \"Minimum gradient\", NWS to confirm.")
    _worked(d, f"For the whole study area the sizing average is {F.fmt(q_ult)} m³/d and the low-case average "
               f"{F.fmt(low)} m³/d, before peaking and before infiltration. Properties number "
               f"{F.fmt(props['y2024'])} in {F.BASE_YEAR}, {F.fmt(props['y2030'])} in 2030 and "
               f"{F.fmt(props['ultimate'])} at saturation. The low case counts {F.fmt(props['y2030'])} × "
               f"{c:.2f} = {F.fmt(props['y2030'] * c)} of them as connected. "
               f"The plant, before infiltration, takes {F.fmt(fl['stp_ultimate_with_margin_m3d'])} m³/d at "
               f"saturation with its margin.")
    _lives(d, f"W14/analysis/design_flows.json: rules, totals, properties, low_case_2030_m3d and "
              f"stp_ultimate_with_margin_m3d; the confirmed rulings under rules.rulings_confirmed "
              f"(low_case_property_count, low_case_infiltration, classes, regrade_class, low_flow_threshold, "
              f"mara_constant, tau_pa, concept_gradients, tractive_sets_gradient). The handoff note "
              f"W14/docs/DESIGN_FLOWS_FOR_NETWORK.md §2 to §4 and §8. The network engine must read Q_ULT and "
              f"Q_2030 from W14/shp/PLOTS_load.shp. In W13/py/sewnet/criteria.py, TRACTIVE_K = "
              f"{E.TRACTIVE_K:g} is the Mara constant; TRACTIVE_QMIN = {E.TRACTIVE_QMIN:g} m³/s is the old "
              f"{E.TRACTIVE_QMIN * 1000:g} l/s floor that W13/py/sewnet/hydra.py applies before the tractive "
              f"test, and the audit must not apply it; SLOPE_STEP = {E.SLOPE_STEP:g} is a single "
              f"{E.SLOPE_STEP * 100:g} % step, to be set by pipe size.")

    # ------------------------------------------------------------ 8.6
    D.h(d, 2, "8.6   Why never the saturation flow times the ratio")
    _for(d, "A shortcut is tempting: take the saturation flow already summed for sizing and multiply it by "
            "the connection ratio. This section shows why that is wrong.")
    _rule(d, f"The low case is always Q_2030 × {c:.2f}, never Q_ULT × {c:.2f}.")
    D.p(d, f"The shortcut mixes the people of {ult} with the connection share of 2028. It assumes that every "
           f"district carries {_pc(c)} of its saturation flow in the opening year. A built-up district is close "
           f"to that; a new district carries almost nothing in 2030, because its plots are still empty. The "
           f"error therefore lands on exactly the pipes where silting happens, and it lands on the unsafe side.")
    D.tab_caption(d, "The low case against the shortcut, m³/d")
    rows = []
    for k in ("IBRI", "AD DARIZ", "AT TAYYIB", "AL QURAYN", "SHALASHIL", "WADI AL MANKAS"):
        s = S[k]
        rows.append([s["settlement"], F.fmt(s["q_2030"]), F.fmt(s["q_2030_low"]), F.fmt(s["q_ult"]),
                     F.fmt(s["q_ult"] * c), f"{s['q_ult'] / s['q_2030']:.1f}"])
    rows.append(["**Study area**", f"**{F.fmt(q30)}**", f"**{F.fmt(low)}**", f"**{F.fmt(q_ult)}**",
                 f"**{F.fmt(wrong)}**", f"**{wrong / low:.1f}**"])
    D.table(d, ["Settlement", "Q 2030", f"Q 2030 × {c:.2f} (right)", "Q saturation",
                f"Q saturation × {c:.2f} (wrong)", "Overstated by, times"],
            rows, widths=[3.2, 2.1, 2.8, 2.4, 3.2, 2.8], font=8.5, align_right={1, 2, 3, 4, 5})
    D.p(d, "")
    sh = S["SHALASHIL"]
    _worked(d, f"Over the study area the shortcut gives {F.fmt(q_ult)} × {c:.2f} = {F.fmt(wrong)} m³/d against "
               f"{F.fmt(low)} m³/d really expected in 2030, {wrong / low:.1f} times too much. In Ibri, already "
               f"built up, the shortcut is {S['IBRI']['q_ult'] / S['IBRI']['q_2030']:.1f} times too "
               f"much. In Shalashil, which is mostly empty plots today, it is "
               f"{sh['q_ult'] / sh['q_2030']:.0f} times too much: the pipes of its new district would be "
               f"declared self-cleansing on a flow that will not arrive for decades.")
    _lives(d, "W14/analysis/design_flows.json, settlements[] (q_2030, q_2030_low, q_ult); "
              "W14/docs/DESIGN_FLOWS_FOR_NETWORK.md §2.")

    # ------------------------------------------------------------ 8.7
    D.h(d, 2, "8.7   Accuracy is directional")
    _for(d, "This is the reason the design carries two cases rather than one best estimate.")
    _rule(d, "One population cannot serve every use, because the safe direction reverses between them. Size "
             "capacity on the high case; set the self-cleansing check and the early washing schedule on the "
             "low case; carry the connection ratio explicitly in the low case.")
    D.tab_caption(d, "The three uses of the flow and their dangerous direction")
    D.table(d, ["Use", "Driven by", "Dangerous direction", "Case used"], [
        ["Pipe sizing", "peak flow and its distribution", "under-estimate: the pipe surcharges",
         f"Q_ULT, {ult}, fully connected"],
        ["Plant capacity and staging", "total average flow and its growth curve",
         "under-estimate: the plant is too small or a stage comes late",
         "settlement totals by year, fully connected"],
        ["Self-cleansing and the early washing schedule", "minimum flow in the opening years",
         "over-estimate: pipes declared self-cleansing while they silt; washing stopped too soon",
         f"Q_2030 × {c:.2f}"],
    ], widths=[3.6, 3.8, 5.0, 4.1], font=8.5)
    D.p(d, "")
    D.p(d, "An earlier tutorial applied a connection ratio to the flow of every year. That is replaced here: "
           "the sizing case and the plant are fully connected, and only the low case carries the ratio.")
    _src(d, "Project doctrine, accuracy is directional (_BRAIN/07_PROJECT_STATE.md §2 item 1d; "
            "_BRAIN/02_DESIGN_CRITERIA.md §11.1), with G201-p73 §7.4.4 and the Inception Report connection "
            "ratio.")
    _worked(d, f"Sized on {F.fmt(q_ult)} m³/d, checked for self-cleansing on {F.fmt(low)} m³/d: the same "
               f"network, two flows {q_ult / low:.1f} times apart, each on its safe side.")
    _lives(d, "The two flows are fields Q_ULT and Q_2030 on every plot of W14/shp/PLOTS_load.shp; the ratio is "
              "rules.connection_ratio_2030 in W14/analysis/design_flows.json.")

    _check(d, "8.8   Check it yourself", [
        f"Open sheet \"Qadf by year m3d\" of W14/analysis/W14_growth_by_settlement.xlsx. The 2030 column must "
        f"sum to {F.fmt(t['q'][2030])} m³/d and the {ult} column to {F.fmt(t['q_ult'])}.",
        f"Sum Q_2030 over the plots and multiply by {c:.2f}. The answer must be {F.fmt(low)} m³/d, the "
        f"low_case_2030_m3d of design_flows.json.",
        "For one settlement, divide (Q in any year − Q in 2024) by (people in that year − people in 2024). The "
        f"answer must be {SEW_PC / 1000:.4f} m³/d per person.",
        "Open the Inception Report workbook, sheet Pop_Wilayat, row W_Pop_Connected, and read the values for "
        "2024, 2028 and 2030.",
        "Pick a settlement that is mostly empty today and compare Q_ULT × 0.61 with Q_2030 × 0.61. The gap "
        "is the error the shortcut would put into its pipes.",
        f"Open rules.rulings_confirmed in design_flows.json. The classes must be the three of Table {n_cls}, "
        f"regrade_class and low_flow_threshold must read none, and low_case_infiltration must read left out.",
        f"Pick a pipe with between 101 and {int(100 / c)} properties standing upstream in 2030. Times "
        f"{c:.2f}, that is 100 or fewer connected, so its low-case peak must come from Peltier, with no "
        f"infiltration added.",
        "Read the Terms of Reference, page 14, for the design years and page 15, item 12, for the five-year "
        "interval.",
    ])
