"""Chapter 7 - assessment and appraisal.   Chapter 8 - delivery."""
import doc as D
import notes as N
import omml as M
import facts_w14 as F

UP, R = M.up, M.r


def _params(d, rows):
    D.table(d, ["Symbol", "Meaning", "Unit"], rows,
            widths=[2.6, 10.4, 3.5], font=9)


def flood_exposure(d):
    """Section 7.2: the sewers and the manholes on the flood hazard grids of Section 1.2.7, the same in every option
    (engineer, 2026-10-03: what share of the network lies in the high classes, H4 to H6). The plants and the pumping
    stations are assessed once their sites are fixed. Source: facts_w17.flood (py/flood_exposure.py)."""
    import facts_w17 as FW
    fl = FW.flood(); L = fl["pipes"]["length_m"]; M = fl["manholes"]["count"]; per = fl["periods"]; Ts = list(per)
    hi = ("H4", "H5", "H6")
    rows = [("none", "Not flooded")] + [(f"H{k}", f"H{k}") for k in range(1, 7)]

    def pc(part, total):
        return f"{100 * part / total:.1f}"

    D.sub(d, "Sewers and Manholes")
    p = D.p(d, "The guideline requires sewers and their manholes to be kept out of wadis and of ground subject to "
               "washout in heavy storms. The hazard grids give that ground a measure: the high classes, H4 to H6, where "
               "the flood is unsafe for people and vehicles and damages buildings, are taken as the ground to be avoided.")
    N.add(p, "PAM-GUD-203, Section 4.4.1, page 30, and page 33. The guideline sets no hazard class for washout; taking "
             "H4 to H6 is this design's measure, to be confirmed by a scour check at the preliminary design.")
    D.p(d, f"The sewers and the manholes lie in the same streets in every option, so their exposure does not depend on "
           f"the option chosen. Each of the {FW.fmt(L / 1000)} km of sewer has been sampled every metre along its length, "
           f"and each of the {FW.fmt(M)} manholes at its centre, on the grids of the 10, 25, 50 and 100-year floods. The "
           f"tables below give the length of sewer and the number of manholes in each class.")
    D.tab_caption(d, "Length of sewer in each flood hazard class, km")
    D.table(d, ["Hazard class"] + [f"{T}-year" for T in Ts],
            [[lab] + [FW.fmt(per[T]["pipe_length_m"][k] / 1000, 1) for T in Ts] for k, lab in rows]
            + [["**H4 to H6**"] + [f"**{FW.fmt(per[T]['pipe_length_h4_h6_m'] / 1000, 1)}**" for T in Ts],
               ["**H4 to H6, per cent of the length**"] + [f"**{pc(per[T]['pipe_length_h4_h6_m'], L)}**" for T in Ts]],
            widths=[5.3, 2.8, 2.8, 2.8, 2.8], font=9)
    D.p(d, "")
    D.tab_caption(d, "Manholes in each flood hazard class")
    D.table(d, ["Hazard class"] + [f"{T}-year" for T in Ts],
            [[lab] + [FW.fmt(per[T]["manholes"][k]) for T in Ts] for k, lab in rows]
            + [["**H4 to H6**"] + [f"**{FW.fmt(per[T]['manholes_h4_h6'])}**" for T in Ts],
               ["**H4 to H6, per cent of the manholes**"] + [f"**{pc(per[T]['manholes_h4_h6'], M)}**" for T in Ts]],
            widths=[5.3, 2.8, 2.8, 2.8, 2.8], font=9)
    D.p(d, "")
    D.chart(d, "W07_flood", 16.0)
    D.fig_caption(d, "Share of the sewer length and of the manholes in each flood hazard class. The figure at the right "
                     "of each bar is the share in the high classes, H4 to H6.")
    a, b = per[Ts[-1]], per["25"]
    D.p(d, f"In the 100-year flood {FW.fmt(a['pipe_length_h4_h6_m'] / 1000, 1)} km of sewer, "
           f"{pc(a['pipe_length_h4_h6_m'], L)} per cent of the length, and {FW.fmt(a['manholes_h4_h6'])} manholes, "
           f"{pc(a['manholes_h4_h6'], M)} per cent, lie in H4 to H6. In the 25-year flood the shares are "
           f"{pc(b['pipe_length_h4_h6_m'], L)} per cent of the length and {pc(b['manholes_h4_h6'], M)} per cent of the "
           f"manholes; H6, the highest class, holds {FW.fmt(a['pipe_length_m']['H6'] / 1000, 1)} km of sewer in the "
           f"100-year flood.")
    p = D.p(d, "At the preliminary design each sewer and manhole in these classes is reviewed on the levels of the "
               "survey. The sewer is moved out of the channel where the streets allow. Where it has to cross, the "
               "crossing is designed as a wadi crossing, with 1.5 metres of cover to the crown, protection against scour "
               "and no manhole in the wadi bed or its embankments. Where no other route exists, the length is recorded "
               "as a justified exception, and the manholes that remain in the high classes are sealed against the entry "
               "of flood water.")
    N.add(p, "PAM-GUD-201, Section 9.3, pages 85 and 86; PAM-GUD-203, Section 8.2.4, page 52.")
    D.p(d, "The treatment plants, the pumping stations and the rising mains are assessed on the same grids once their "
           "sites are fixed.")



def sustainability_energy(d):
    """Section 7.7: the pumping energy of each option against the treatment energy of the estimate."""
    import facts_w17 as FW
    import facts_cost as C
    e = {o: FW.energy_total(o, "2070") for o in FW.available()}
    lo, hi = min(e, key=e.get), max(e, key=e.get)
    plant = C.data()["kw_plants"]["S1"] * 8760 / 1000
    D.p(d, f"At the concept stage the energy of each option is the measurable part of its operating carbon. The pumping "
           f"energy in 2070, with the lift at the plant inlets, runs from {FW.fmt(e[lo])} MWh a year in {lo} to "
           f"{FW.fmt(e[hi])} in {hi} (Section 6.2.7). The treatment plants use about {FW.fmt(round(plant, -2))} MWh a year "
           "on the basis of the cost estimate (Section 7.8.3), the same in every option because the flow treated is the "
           "same, so the pumping is the part that separates the options.")


def cost_section(d):
    """Section 7.8: the estimate of the seven options, its basis, the operating cost and the whole-life cost."""
    import facts_w17 as FW
    import facts_cost as C
    cd = C.data(); opts = C.OPTIONS; w = C.whole_life(); lo = min(w.values()); f = C.factor(); f0 = C.factor(0.0)
    m = lambda x, nd=1: FW.fmt(x / 1e6, nd)

    D.h(d, 3, "7.8.1.   Basis")
    p = D.p(d, "Each option is priced on its own quantities, taken from the network model (Appendix B), on the same "
               "rates. The estimate is made at concept accuracy and compares the options on one basis.")
    N.add(p, "PAM-GUD-201, Table 2, pages 17 to 20: plus or minus 20 per cent at the concept stage.")
    D.table(d, ["Item", "Basis"], [
        ["Accuracy", "plus or minus twenty per cent at concept stage"],
        ["Quantities", "the network model of each option: sewers, manholes, pumping stations, rising mains and plants"],
        ["Rates", "recent tender and contract rates, and rates from Nama Water Services pre-investment appraisals, "
                  "escalated to the base date of the estimate"],
        ["Price basis", "current prices at the date of the estimate; operating cost escalated at "
                        f"{100 * cd['escalation']:.0f} per cent a year"],
        ["Presentation", "by system element"],
        ["Not included", "the treated effluent network, whose customers are defined at the preliminary design; house "
                         "connections and the crossings of roads and wadis, which are the same in every option"],
    ], widths=[4.4, 12.1], font=9.5)

    D.h(d, 3, "7.8.2.   Scope of the estimate")
    D.p(d, "The capital cost of each option is built from five elements.")
    D.bullet(d, "the length of sewer by outside diameter and by depth band, at a rate per metre that rises with the depth.",
             lead="Gravity sewers — ")
    D.bullet(d, "the number of manholes by type and by depth band.", lead="Manholes — ")
    D.bullet(d, "the installed power of each station, at a rate per kilowatt, with the smallest stations in their own "
                "band.", lead="Pumping stations — ")
    D.bullet(d, "the length of rising main by diameter.", lead="Rising mains — ")
    D.bullet(d, "the design capacity of each plant, the average flow of 2070 with the 10 per cent margin, at a rate per "
                "cubic metre a day that falls as the plant grows.", lead="Treatment plants — ")
    D.tab_caption(d, "Capital cost of the options by element, million OMR")
    D.table(d, ["Element"] + opts,
            [[lab] + [m(cd["capex"][lab][o]) for o in opts] for lab in cd["capex"]]
            + [["**Total**"] + [f"**{m(cd['capex_total'][o])}**" for o in opts]],
            widths=[3.6] + [1.85] * len(opts), font=8.5)
    D.p(d, "")
    hi_c = max(opts, key=lambda o: cd["capex_total"][o]); lo_c = min(opts, key=lambda o: cd["capex_total"][o])
    D.p(d, f"The capital cost differs little between the options: from {m(cd['capex_total'][lo_c])} million OMR in {lo_c} "
           f"to {m(cd['capex_total'][hi_c])} in {hi_c}. The more plants, the cheaper the trunk sewers and the pumping, and "
           "the dearer the plants, because a small plant costs more for each cubic metre it treats.")

    D.h(d, 3, "7.8.3.   Operating cost")
    D.p(d, "The operating cost of each option in its first year is built from four items, and escalated at "
           f"{100 * cd['escalation']:.0f} per cent a year over the 25 years.")
    D.bullet(d, "1 per cent of the capital cost a year.", lead="Maintenance and operation — ")
    D.bullet(d, f"the installed power of the pumping stations and the plants, for 24 hours a day, at "
                f"{cd['power_rate']:.2f} OMR per kilowatt hour.", lead="Power — ")
    D.bullet(d, f"the land of the plant and station sites at {cd['rent_rate']:.0f} OMR per square metre a month.",
             lead="Land — ")
    D.bullet(d, f"the staff of the plants and the stations at {FW.fmt(cd['staff_rate'])} OMR a month each, thirteen "
                "months a year.", lead="Staff — ")
    D.tab_caption(d, "Operating cost of the options in the first year, million OMR")
    D.table(d, ["Item"] + opts,
            [[lab] + [m(cd["opex"][lab][o], 2) for o in opts] for lab in cd["opex"]]
            + [["**Total**"] + [f"**{m(cd['opex1'][o], 2)}**" for o in opts],
               ["Staff, number"] + [str(cd["staff"][o]) for o in opts],
               ["Land, thousand m²"] + [FW.fmt(cd["land_m2"][o] / 1000) for o in opts]],
            widths=[3.6] + [1.85] * len(opts), font=8.5)
    D.p(d, "")
    D.p(d, "Staff and land grow with the number of plants and are the items that separate the options; power and "
           "maintenance hardly differ. Sludge, chemicals and laboratory costs follow the flow treated, which is the same "
           "in every option, and do not change the comparison; they are costed with the treatment process at the "
           "preliminary design, as is the replacement of mechanical and electrical plant within the 25 years.")

    D.h(d, 3, "7.8.4.   Life cycle cost and net present value")
    p = D.p(d, "Capital cost and operating cost arise in different years, so they are not comparable until they are "
               "brought to a common date. Each is discounted to present value at the rate the guideline sets, and the "
               "options are compared on the resulting totals.")
    N.add(p, "PAM-GUD-201, page 57, states that the twenty-five year planning life is also the period over which net "
             "present value is calculated for the comparison of schemes; the discount rate of five per cent is given "
             "at pages 95 to 96.")
    eq = D.next_eq()
    M.display(d, M.seq(
        UP("NPV"), M.EQ,
        M.nary("∑", M.seq(R("t"), M.EQ, R("0")), R("n"),
               M.frac(M.sub(R("C"), R("t")),
                      M.sup(M.delim(M.seq(R("1"), M.PLUS, R("r"))), R("t"))))),
        number=eq)
    _params(d, [
        ["NPV", "net present value of the option", "OMR"],
        ["C t", "cost in year t: the capital cost in year 0 and the operating cost of every year", "OMR"],
        ["r", "discount rate, 0.05", "—"],
        ["t", "year, counted from the base date", "—"],
        ["n", "evaluation period, 25 years", "—"]])
    D.p(d, "")
    p = D.p(d, f"The operating cost escalates at {100 * cd['escalation']:.0f} per cent a year and is discounted at 5 per "
               "cent, so the present value of each year's operating cost equals that of the first year, and the "
               f"whole-life cost is the capital cost plus {f:.0f} times the first-year operating cost. It is the "
               "quantity against which the ten per cent band of Section 6.1.4 is applied.")
    N.add(p, "Net present value and life cycle cost are not defined by equation in the Nama Water Services guidelines. "
             "The formulation above follows ISO 15686-5, with the period and discount rate taken from PAM-GUD-201.")
    rank = C.ranking()
    D.tab_caption(d, "Whole-life cost of the options over 25 years, million OMR")
    D.table(d, ["Option", "Plants", "Capital cost", "Operating cost, present value", "Whole-life cost",
                "Above the lowest"],
            [[o, str(cd["n_plants"][o]), m(cd["capex_total"][o]), m(f * cd["opex1"][o]), f"**{m(wv)}**",
              "—" if g < 1e-9 else f"{100 * g:.1f} %"] for o, wv, g in rank],
            widths=[1.8, 1.6, 2.8, 3.8, 3.0, 3.0], font=9)
    D.p(d, "")
    D.chart(d, "W08_costs", 16.0)
    D.fig_caption(d, "Whole-life cost of the options over 25 years: the capital cost and the present value of the "
                     "operating cost, with the line ten per cent above the lowest. The recommended options carry their "
                     "priority.")
    r0 = C.ranking(0.0); band0 = C.within_band(0.0); band = C.within_band()
    out0 = [o for o, _, g in r0 if o not in band0]; g0 = {o: g for o, _, g in r0}
    D.p(d, f"In constant prices, without the escalation, the operating cost weighs less: the whole-life cost is the "
           f"capital cost plus {f0:.1f} times the first-year operating cost. The order is the same, "
           + ("the same options lie within ten per cent of the lowest" if set(band0) == set(band) else
              "the options within ten per cent of the lowest change") +
           f", and {', '.join(out0[:-1])} and {out0[-1]} remain outside the band at "
           f"{100 * min(g0[o] for o in out0):.0f} to {100 * max(g0[o] for o in out0):.0f} per cent above.")
    D.p(d, "Revenue from treated effluent and the costs the scheme avoids are not counted. Treated effluent tariffs are "
           "set by Nama Water Services and the regulator, and the customers are defined at the preliminary design.")


def risk_register(d):
    """Section 7.9: the initial register at the concept stage."""
    D.tab_caption(d, "Initial risk register")
    D.table(d, ["Risk", "Effect", "Likelihood", "Impact", "Mitigation", "Owner"], [
        ["The survey finds existing sewers fit to keep", "Part of the new network in those streets not needed",
         "Medium", "Cost lower", "Assess the existing network on the survey (Chapter 5)", "Consultant"],
        ["The survey finds ground levels different from the terrain model", "Depths, pumping and sizes change",
         "Medium", "Cost and time", "Re-run the model on the surveyed levels", "Consultant"],
        ["Plant or station sites not available, or in flood hazard", "Sites move; trunk sewers and pumping change",
         "Medium", "Cost and time", "Early site selection with Nama Water Services and the Ministry of Housing; "
         "flood check of each site", "Nama Water Services"],
        ["Rock or shallow groundwater on deep sewers", "Slower excavation, dewatering", "Medium", "Cost",
         "Geotechnical investigation along the deep runs", "Consultant"],
        ["The design horizon decided late", "Plant phasing and capacity held open", "Medium", "Time",
         "Decision of Section 1.5.2", "Nama Water Services"],
        ["Tankered sewage greater than assumed", "Plant load and tanker reception undersized", "Medium", "Cost",
         "Records of the existing plant and of the tanker sources (Section 1.5.5)", "Nama Water Services"],
        ["Treated effluent demand lower than production", "Surplus to be disposed of", "Medium", "Cost",
         "Customers and demand confirmed; excess effluent provision (Section 6.6.2)", "Nama Water Services"],
        ["Hydrogen sulphide in long rising mains", "Corrosion and odour", "High", "Cost",
         "Hydrogen sulphide evaluation; dosing or shorter routes (Section 6.2.7)", "Consultant"],
        ["Low flows in the early years", "Deposits in the head pipes", "High", "Operation",
         "Washing schedule; the decision of Section 6.2.8", "Nama Water Services"],
        ["Approvals for wadi and road crossings", "Delay", "Medium", "Time",
         "Applications at the preliminary design (Section 7.6.5)", "Consultant"],
        ["Prices rise between the estimate and the tender", "Cost higher", "Medium", "Cost",
         "Estimate updated at each design stage", "Consultant"],
    ], widths=[3.4, 3.2, 1.7, 1.6, 4.4, 2.2], font=8, keep_together=False)
    D.p(d, "")


def roadmap(d):
    """Section 8.1: the stages after the concept design, what each needs, and the phasing of construction."""
    import facts_w17 as FW
    rec = FW.RECOMMENDED[0]; pl = FW.plants(rec)
    D.tab_caption(d, "Implementation roadmap")
    D.table(d, ["Stage", "Scope", "What it needs before it starts"], [
        ["Concept approval", "The recommended option and the design basis approved", "This report reviewed by Nama "
         "Water Services; the decisions of Section 1.5.2"],
        ["Preliminary design", "The survey taken into the model; the existing network assessed; the plant and station "
         "sites selected and investigated for flood, ground and odour; the treated effluent customers and demand "
         "confirmed; the characters costed and the treatment process selected; the estimate to plus or minus 10 per "
         "cent", "The survey; the sites; the data requests of Section 1.5.5"],
        ["Detailed design", "Drawings, specifications and priced bills of quantities", "The approved preliminary design"],
        ["Tender", "Tender documents for each package, and support to the award", "The approved detailed design and "
         "the contracting strategy"],
        ["Construction", "The network in packages by groups of subnetworks; the plant in phases", "The awarded "
         "contracts and the approvals of Section 7.6.5"],
    ], widths=[3.0, 8.4, 5.1], font=8.5, keep_together=False)
    D.p(d, "")
    z = next(iter(pl)) if len(pl) == 1 else max(pl, key=lambda q: pl[q]["avg"]["2070"])
    D.p(d, f"The sewers are laid once, for the flow of 2070. The plant is built in phases that follow the flow: in "
           f"option {rec} it receives {FW.fmt(pl[z]['avg']['2030'])} cubic metres a day on average in 2030, "
           f"{FW.fmt(pl[z]['avg']['2040'])} in 2040, {FW.fmt(pl[z]['avg']['2055'])} in 2055 and "
           f"{FW.fmt(pl[z]['avg']['2070'])} in 2070 (Section 6.5.1). The size of each phase follows from the design "
           "horizon decided in Section 1.5.2.")


# ===================================================== PART G
def part_g(d):
    D.chapter(d, "7.   Assessment and appraisal")
    D.p(d, "This chapter carries the technical and financial appraisal: ground "
           "conditions, flood, odour, climate, environment, utility interfaces, "
           "sustainability, cost, risk, value engineering and the comparison of the "
           "options.")

    # --------------------------------------------------------------- 28
    D.h(d, 2, "7.1.   Ground conditions")
    D.p(d, "Geophysical investigation is required for all infrastructure and "
           "geotechnical investigation for all above-ground assets. At this "
           "stage the purpose is to establish a site-wide ground model and a "
           "range of parameters sufficient to select foundation types and "
           "platform levels, and to identify the risks that the detailed "
           "investigation must resolve.")
    D.p(d, "Boreholes at the treatment plant and lifting station sites are "
           "taken to a minimum depth of fifteen metres or to a competent "
           "stratum, and are closely spaced at wet wells, valve chambers and "
           "electrical rooms. Groundwater monitoring is required, as the depth "
           "to groundwater governs both the excavation method and the "
           "infiltration allowance.")
    D.p(d, "The treatment plant and pumping station sites are tentative at "
           "the concept stage, and the investigation of each site is carried "
           "out as soon as it is decided. Along the sewer routes the "
           "investigation follows the spacing of the guideline: 100 metres on "
           "the secondary sewers and 500 metres on the primary sewers and the "
           "rising mains.")


    # --------------------------------------------------------------- 29
    D.h(d, 2, "7.2.   Flood protection")
    D.p(d, "The study area is crossed by a wadi system, and flood behaviour "
           "governs both the alignment of the works and the siting of the "
           "treatment plant. The site is assessed against the twenty-five and "
           "one hundred year flood levels, and the plant is to remain "
           "operational during floods. The flood hazard across the study area "
           "for the 10, 25, 50 and 100-year floods is mapped in Section 1.2.7.")
    D.p(d, "Pumping station floor levels, transformers and standby generators "
           "are set not less than 300 millimetres above the one in fifty year "
           "flood level. Wadi crossings are designed with a minimum cover of "
           "1.5 metres to the crown of the pipe.")
    flood_exposure(d)

    # --------------------------------------------------------------- 30
    D.h(d, 2, "7.3.   Odour assessment")
    p = D.p(d, "Odour governs the buffer distance between the treatment plant "
               "and residential development, and for a plant of this size the "
               "buffer is established from dispersion modelling rather than "
               "from a fixed distance. The modelling establishes the distance "
               "to the five odour unit contour, using site meteorological "
               "records and the treatment processes proposed.")
    N.add(p, "PAM-GUD-201, Table 8, page 43; PAM-GUD-203, Table 90, page 170, "
             "which sets five odour units per cubic metre at the site boundary "
             "where the surrounding area is sensitive.")

    D.p(d, "The prevailing winds are described in Section 1.2.5 from a regional "
           "record, which serves the comparison of sites. The plant sites are "
           "tentative at the concept stage, and the modelling is carried out "
           "for each site as soon as it is decided, on the record of the "
           "nearest meteorological station, which is requested (Section "
           "1.5.5).")

    D.p(d, "Odour control is provided at the inlet works, the sludge "
           "facilities and the pumping stations, with the treatment train "
           "selected from the assessment. Compliance is verified by continuous "
           "monitoring at the site boundary.")


    # --------------------------------------------------------------- 31
    D.h(d, 2, "7.4.   Climate resilience")
    p = D.p(d, "The works are assessed for resilience to the climate "
               "conditions anticipated over their service life. The assessment "
               "considers a fifty-year horizon at two and at four degrees "
               "Celsius of warming, and addresses the effect of changes in "
               "rainfall frequency and intensity on site selection and on the "
               "design of the infrastructure.")
    N.add(p, "PAM-GUD-201, Section 4.3, page 33.")


    # --------------------------------------------------------------- 32
    D.h(d, 2, "7.5.   Environmental and social assessment")
    D.p(d, "An environmental impact assessment is required for the treatment "
           "plant and its associated works. The Environment Authority is "
           "informed of the project, its objectives and its anticipated "
           "impact, and is consulted on the location of the facilities.")
    D.p(d, "Each option is assessed against resource use, ecosystem "
           "disruption, pollution risk, climate resilience, socio-economic "
           "impact and land use, and the assessment forms part of the "
           "comparison described in Section 7.11.")
    D.p(d, "The scope required at this stage is the subject of Section 1.5.4.")

    # --------------------------------------------------------------- 33
    D.h(d, 2, "7.6.   Utility interfaces and approvals")

    D.h(d, 3, "7.6.1.   Approach")
    D.p(d, "The proposed alignments are superimposed on the service records of "
           "each authority holding assets in the area. Where a conflict "
           "cannot be avoided by re-routing within the corridor, the cost of "
           "relocating the proposed works is compared with the cost of "
           "relocating the existing service, and the agreement of the owning "
           "authority is obtained for whichever is adopted.")

    D.h(d, 3, "7.6.2.   Records held and required")
    D.p(d, "The potable water network is available from the dataset described "
           "in Section 2.2.2 and provides 647.8 kilometres of mains within the "
           "study area. Records for electricity distribution, telecommunications "
           "and, where present, gas and fuel pipelines are being requested "
           "from the respective owners.")
    p = D.p(d, "The electricity data held records the position of consumer "
               "connections. It does not record the routes of the distribution "
               "cables, which are required for clash assessment and are "
               "requested separately.")
    N.add(p, "The account dataset described in Section 2.2.3 comprises point "
             "locations of metered connections.")

    D.h(d, 3, "7.6.3.   Clearances")
    D.tab_caption(d, "Separation from other services")
    D.table(d, ["Situation", "Requirement"], [
        ["Force main to water main, horizontal", "3.0 m"],
        ["Force main crossing a water main",
         "the force main passes beneath, with 450 mm vertical clearance"],
        ["Shallow sewer beneath a major road", "3.0 m horizontal clearance"],
        ["Another service in the same trench",
         "placed on a separate bench on undisturbed ground"],
    ], widths=[7.0, 9.5], font=9.5)
    D.p(d, "")
    D.p(d, "Beyond these, the clearance applied is that specified by the "
           "authority owning the service.")

    D.h(d, 3, "7.6.4.   Trial pits")
    D.p(d, "Fifty trial pits are provided for. Their locations are selected at "
           "road intersections, along the routes of major existing services "
           "and along the expected routes of the trunk sewers and force mains. "
           "The programme is agreed with Nama Water Services and the municipal "
           "excavation approvals obtained before work begins.")

    D.h(d, 3, "7.6.5.   Approvals register")
    D.p(d, "Approvals and no objection certificates are required from the "
           "authorities listed below. A register is maintained recording the "
           "authority, the consent required, the date of application and the "
           "current position, and is reported to Nama Water Services.")
    D.tab_caption(d, "Authorities from which approvals are required")
    D.table(d, ["Authority"], [
        ["Ministry of Housing and Urban Planning"],
        ["Environment Authority"],
        ["Ministry of Agriculture, Fisheries and Water Resources"],
        ["Directorate General of Roads"],
        ["Regional electricity distribution company"],
        ["Oman Telecommunications Company"],
        ["Royal Oman Police"],
        ["Ministry of Heritage and Tourism"],
        ["Municipality of Ibri"],
    ], widths=[16.5], font=9.5)

    # --------------------------------------------------------------- 34
    D.h(d, 2, "7.7.   Sustainability")
    p = D.p(d, "The carbon footprint of each option is evaluated for both "
               "construction and operation in accordance with recognised "
               "greenhouse gas accounting standards, and is expressed in "
               "tonnes of carbon dioxide equivalent per year and per cubic "
               "metre of effluent produced.")
    N.add(p, "PAM-GUD-201, Section 12.5.1, pages 98 to 100, which cites ISO "
             "14064 and the Greenhouse Gas Protocol and gives a benchmark of "
             "1.17 × 10⁻³ tonnes of carbon dioxide equivalent per cubic metre "
             "of treated effluent.")

    D.p(d, "Because the greater part of operational emissions arises from "
           "electricity consumption, the measures that reduce carbon are "
           "largely the same as those that reduce operating cost: conveying "
           "the flow by gravity wherever possible, minimising lift, selecting "
           "efficient equipment, and generating renewable energy on site. "
           "Photovoltaic generation on site is one of the factors the three "
           "characters vary (Section 6.1.2).")
    sustainability_energy(d)
    D.p(d, "Resource efficiency, in-country value and the use of nature-based "
           "solutions are assessed with the three characters at the "
           "preliminary design, where the treatment process is selected.")

    # --------------------------------------------------------------- 35
    D.h(d, 2, "7.8.   Cost")
    cost_section(d)


    # --------------------------------------------------------------- 36
    D.h(d, 2, "7.9.   Risk")
    D.p(d, "A risk register is established at this stage and maintained "
           "through the project. Each risk carries a description, a "
           "likelihood, an impact expressed in cost or time, an owner and the "
           "mitigation adopted. Risks that fall on one option and not on "
           "another are identified as such, as they affect the comparison "
           "rather than only the total.")
    risk_register(d)

    # --------------------------------------------------------------- 37
    D.h(d, 2, "7.10.   Value engineering")
    p = D.p(d, "A formal value engineering study is required at the concept "
               "and preliminary stages for a treatment plant or pumping "
               "station above the stated threshold, carried out by an "
               "independent certified consultant. The study is arranged within "
               "the concept programme and its outcome reported.")
    N.add(p, "PAM-GUD-201, Table 27, page 93, and its accompanying note.")

    # --------------------------------------------------------------- 38
    D.h(d, 2, "7.11.   Comparison and recommendation")
    D.p(d, "The options are compared by the method of Sections 6.1.3 and "
           "6.1.4: on their whole-life cost, the net present value of Section "
           "7.8.4 at five per cent over twenty-five years, and, within ten per "
           "cent of the lowest, on sustainability and operability.")
    import rpt_options             # the sewer network options compared, and the three recommended
    rpt_options.appraisal(d)


# ===================================================== PART H
def part_h(d):
    D.chapter(d, "8.   Delivery")
    D.p(d, "This chapter covers the delivery of the scheme: the implementation "
           "roadmap, the contracting strategy, project integration, and the "
           "conclusions and recommendations of this report.")

    # --------------------------------------------------------------- 39
    D.h(d, 2, "8.1.   Implementation roadmap")
    D.p(d, "The roadmap sets out, for the recommended option, the scope of the "
           "design stages that follow, what each needs before it starts, and "
           "the phasing of construction. Performance is monitored once the "
           "works are in service against the flows and loads of Chapter 4.")
    roadmap(d)


    # --------------------------------------------------------------- 40
    D.h(d, 2, "8.2.   Contracting strategy")
    D.p(d, "The contracting strategy establishes how the works are packaged "
           "and procured. It is developed with Nama Water Services in a "
           "dedicated workshop, and considers the division of the works into "
           "packages, the procurement route for each, and the interfaces "
           "between them.")
    D.p(d, "Three packages follow from the recommended option and are proposed "
           "for the workshop: the sewer network with its pumping stations and "
           "rising mains, divided by groups of subnetworks so that each "
           "package can be built and commissioned on its own; the treatment "
           "plant, procured for design and construction and built in phases; "
           "and the treated effluent network, once its customers are defined. "
           "The interfaces between them are the inlet works of the plant and "
           "its treated effluent outlet.")

    # --------------------------------------------------------------- 41
    D.h(d, 2, "8.3.   Project integration")
    p = D.p(d, "A project integration plan sets out how the water and "
               "wastewater components are coordinated through design, "
               "construction and commissioning. It also addresses the "
               "rehabilitation or replacement of the existing potable water "
               "network where its performance is found to be unsatisfactory.")
    N.add(p, "PAM-GUD-201, Section 13, page 107.")

    # --------------------------------------------------------------- 42
    D.h(d, 2, "8.4.   Conclusions")
    D.p(d, "The design basis for the wastewater and treated effluent systems "
           "is established and is set out in Chapter 3. The data supplied has "
           "been assessed, and the datasets that are usable, those that "
           "require correction and those that relate to areas outside the "
           "project have been identified in Chapter 2.")
    D.p(d, "The existing wastewater assets within the study area comprise "
           "111.6 kilometres of constructed gravity sewer and 10.0 "
           "kilometres of constructed force main, together with a further "
           "268.2 kilometres of gravity sewer, pumping main and treated "
           "effluent main recorded as proposed. The potable water "
           "network within the area comprises 647.8 kilometres of mains. The "
           "number of properties on each plot and the use of each plot have "
           "been established from 33,971 electricity meters and a satellite "
           "image, the occupancy rate has been calculated for each settlement, "
           "and every plot carries a population and an average sewage flow "
           "for 2024 and for every year to the saturation of its settlement. "
           f"The study area is saturated in {F.totals()['ultimate']} at "
           f"{F.fmt(F.totals()['pop_ult'])} people and "
           f"{F.fmt(F.totals()['q_ult'])} cubic metres of sewage a day.")
    import rpt_options             # what the sewer network options and their costs established
    rpt_options.conclusions(d)
    D.p(d, "A topographic and utility survey covering the whole study area is "
           "in progress. It will establish the levels, diameters and condition "
           "that the supplied datasets do not carry, and the assessment of the "
           "existing networks follows it.")

    D.h(d, 3, "8.4.1.   Recommendations")
    D.p(d, "It is recommended that:")
    rpt_options.recommendations(d)

    # --------------------------------------------------------------- 43
    D.h(d, 2, "8.5.   Appendices")
    D.table(d, ["Appendix", "Content"], [
        ["A", "Population, land use and flow: the working behind Chapter 4"],
        ["B", "Network options: quantities, pumping stations and depth"],
        ["C", "Design criteria, with the guideline page of each"],
        ["D", "Drawings: the subnetworks, and the network of each recommended option"],
    ], widths=[3.0, 13.5], font=9.5)
    D.p(d, "")
    D.p(d, "The decisions requested, the values adopted and the data requests "
           "are set out in Section 1.5.")
