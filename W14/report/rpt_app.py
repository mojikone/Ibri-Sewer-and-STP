"""Appendices for Revision 2: the working behind Part D, so a reviewer can
check it without the scripts."""
import os

import doc as D
import notes as N
import facts_w14 as F

IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img")


def appendices(d):
    D.part(d, "Appendix A", "Population, land use and flow: the working")
    st = F.settlement_table(); ps = F.plot_summary(); mc = F.meter_counts(); cs = F.crt_summary()

    # ----------------------------------------------------------------- A1
    D.h(d, 1, "A1   Electricity meters: tariff to category")
    D.p(d, "Each tariff in the electricity dataset is assigned to one of the "
           "guideline's categories. The large-consumer tariff is resolved "
           "account by account in A2.")
    tariffs = mc["tariff"]
    D.tab_caption(d, "Tariffs and the category adopted")
    D.table(d, ["Tariff", "Meters", "Category", "People"], [
        ["Primary Account Tariff", F.fmt(tariffs.get("Primary Account Tariff", 0)), "Domestic", "one property"],
        ["Primary Account Tariff (with National Subsidy)", F.fmt(tariffs.get("Primary Account Tariff (with National Subsidy)", 0)), "Domestic", "one property"],
        ["Additional Account Tariff", F.fmt(tariffs.get("Additional Account Tariff", 0)), "Domestic", "one property"],
        ["Commercial", F.fmt(tariffs.get("Commercial", 0)), "Non-domestic", "none"],
        ["Fisheries", F.fmt(tariffs.get("Fisheries", 0)), "Non-domestic", "none"],
        ["Tourism", F.fmt(tariffs.get("Tourism", 0)), "Non-domestic", "none"],
        ["Government", F.fmt(tariffs.get("Government", 0)), "Governmental", "none"],
        ["MOD", F.fmt(tariffs.get("MOD", 0)), "Governmental", "none"],
        ["Agricultural", F.fmt(tariffs.get("Agricultural", 0)), "Agricultural", "none; no sewage"],
        ["Industrial", F.fmt(tariffs.get("Industrial", 0)), "Special", "none"],
        ["CRT Seasonal", F.fmt(tariffs.get("CRT Seasonal", 0)), "Large consumer, see A2", "none"],
        ["CRT Time of Use", F.fmt(tariffs.get("CRT Time of Use", 0)), "Large consumer, see A2", "none"],
        ["CRT Fixed Rate", F.fmt(tariffs.get("CRT Fixed Rate", 0)), "Large consumer, see A2", "none"],
    ], widths=[7.0, 2.2, 4.3, 3.0], font=8.5)
    D.p(d, "")
    D.p(d, f"Of the {F.fmt(mc['total'])} meters, {F.fmt(mc['inside'])} fall "
           f"inside a plot, {F.fmt(mc['snapped'])} were assigned to the nearest "
           f"plot within fifteen metres, and {F.fmt(mc['free'])} lie further "
           f"from any plot; they are listed with their settlement and carry no load in the plot table.")

    # ----------------------------------------------------------------- A2
    D.h(d, 1, "A2   The large-consumer accounts")
    use = cs["use"]; conf = cs["conf"]
    D.p(d, f"The {cs['total']} accounts on the Cost Reflective Tariff were "
           f"placed by clustering them at 120 metres, matching each cluster "
           f"and each single account against the named features of "
           f"OpenStreetMap within eighty metres, reverse geocoding the rest, "
           f"and inspecting the largest clusters on the aerial imagery. The "
           f"register delivered with this report carries, for each account, "
           f"the use found, the category adopted, the evidence and a "
           f"confidence.")
    D.tab_caption(d, "Large-consumer accounts by the use found")
    D.table(d, ["Use found", "Accounts", "Category adopted", "Typical sites"], [
        ["Commercial", F.fmt(use.get("Commercial", 0)), "Non-domestic", "Bawadi shopping centre, the Al Murtafa souq, the Araqi strip, hypermarkets, banks, fuel stations"],
        ["Government", F.fmt(use.get("Government", 0)), "Governmental", "Police headquarters, post office, directorates"],
        ["Education", F.fmt(use.get("Education", 0)), "Governmental", "The university campus, the college, schools"],
        ["Health", F.fmt(use.get("Health", 0)), "Governmental", "Ibri Hospital, clinics"],
        ["Religious", F.fmt(use.get("Religious", 0)), "Governmental", "Mosques"],
        ["Industrial", F.fmt(use.get("Industrial", 0)), "Special", "The Tanam estate"],
        ["Agricultural", F.fmt(use.get("Agricultural", 0)), "Agricultural, no load", "Farm pumps at Aynayn"],
        ["Telecommunications, utility", F.fmt(use.get("Telecom/Utility", 0)), "Non-domestic", "Exchanges, water works, masts"],
        ["Unresolved", F.fmt(use.get("Unresolved", 0)), "Non-domestic", "No recorded feature within eighty metres"],
    ], widths=[3.6, 2.0, 3.6, 7.3], font=8.5)
    D.p(d, "")
    p = D.p(d, f"Confidence: {conf.get('Certain', 0)} accounts certain, "
               f"{conf.get('Likely', 0)} likely, {conf.get('Guessing', 0)} "
               f"placed on weaker evidence. The categories adopted affect "
               f"only where the non-domestic and governmental water is placed, "
               f"not its total.")
    N.add(p, "Certain: a named feature within twenty metres, or inspected. "
             "Likely: a named feature within eighty metres, or a nearest "
             "feature by reverse geocoding. Weaker: the surroundings only.")

    # ----------------------------------------------------------------- A3
    D.h(d, 1, "A3   Occupancy, properties per plot and home share by settlement")
    D.tab_caption(d, "The settlement rates used in Part D: derived from the data, and adopted")
    D.table(d, ["Settlement", "Domestic properties, 2024", "Pop. 2024", "Empty plots", "of which counted as future homes",
                "Occupancy derived", "Occupancy adopted", "Properties per home plot derived", "adopted",
                "Home share derived", "adopted", "Capacity, people"],
            [[r["name"], F.fmt(r["properties"]), F.fmt(r["workbook_2024"]), F.fmt(r["empty_plots"]), F.fmt(r["cap_plots"]),
              f"{r['or_raw']:.2f}", f"{r['or_used']:.2f}", f"{r['ratio_raw']:.2f}", f"{r['ratio']:.2f}",
              f"{r['home_share_raw']:.2f}", f"{r['home_share']:.2f}", F.fmt(r["cap_people"])] for r in st],
            widths=[2.6, 1.5, 1.3, 1.2, 1.4, 1.2, 1.2, 1.3, 1.1, 1.2, 1.1, 1.4], font=6.8)
    D.p(d, "")
    p = D.p(d, "The occupancy adopted is the rate derived, held to a floor of "
               "4.0 and a cap equal to the highest rate among the settlements "
               "of two thousand or more people. A settlement of fewer than a "
               "thousand people in 2024 takes an occupancy of 4.0, one "
               "property per plot and a home share of 0.9, whatever its "
               "meters return: it has no sample to measure on, and it does "
               "not attract second dwellings.")
    N.add(p, "Properties per home plot is measured over built plots whose "
             "meters are more than two thirds domestic and fewer than fifteen. "
             "Home share is the proportion of built, metered plots of home "
             "shape that are homes. Empty plots counted as future homes are "
             "those of 200 to 1,000 square metres, compact, not a strip, and "
             "not a grove, an industrial plot or heritage.")

    # ----------------------------------------------------------------- A4
    D.h(d, 1, "A4   The plot and settlement layers delivered with this report")
    D.p(d, "The plot layer carries, for each of the 77,265 plots, the fields "
           "below. It is the load table of the design: the network model "
           "reads the flow of each plot from it, and every figure in Part D "
           "is a sum over it. The settlement layer carries the same at "
           "settlement level, with the rates and the five-year steps.")
    D.tab_caption(d, "Fields of the plot layer")
    D.table(d, ["Field", "Content"], [
        ["Name", "cadastral identifier, as received"],
        ["Moh_Classi, Classes", "class code and class name of the cadastre, as received"],
        ["Buiding_St", "built or future, as received"],
        ["SETTLE", "the settlement the plot belongs to"],
        ["AREA_M2", "plot area, m²"],
        ["N_ACC", "meters on the plot, all tariffs"],
        ["N_DOM, N_DOMADD", "meters on the primary and subsidised tariffs; on the additional-account tariff"],
        ["N_COM, N_GOV, N_AGR, N_CRT, N_IND", "meters on the commercial tariff (with fisheries and tourism), the government tariff (with defence), and the agricultural, large-consumer and industrial tariffs"],
        ["G_DOM", "domestic meters, one property each (the primary, subsidised and additional tariffs)"],
        ["G_NDOM, G_GOV, G_SPEC, G_AGR", "non-domestic, governmental, special and agricultural meters, the large consumers placed by their identified use"],
        ["DERIVED", "use of the plot (Section 14.5)"],
        ["WHYC", "the rule that set the use"],
        ["ESTATE", "the industrial estate the plot lies in, if any"],
        ["WORKERS", "workers assigned to an estate plot, by area"],
        ["HOMESHAPE", "1 if the plot is home-shaped: 200 to 1,000 m², compact, not a strip"],
        ["COMPACT, ASPECT", "area against the smallest enclosing rectangle; that rectangle's aspect ratio"],
        ["NDVI_MEAN, NDVI_SHARE, GREEN_M2", "the satellite vegetation test: mean index, share of green pixels, green area in m²"],
        ["OR_S", "occupancy adopted for the settlement, persons per property"],
        ["PPP_S", "properties per home plot adopted for the settlement"],
        ["HOMESH_S", "home share adopted for the settlement"],
        ["U_NDOM, U_GOV", "non-domestic water per shop meter and governmental water per government meter in the settlement, l/d"],
        ["POP", "people in 2024: G_DOM × OR_S"],
        ["W_DOM, W_NDOM, W_GOV, W_SPEC, W_TOT", "water by stream and in total, m³/d, 2024"],
        ["S_DOM, S_NDOM, S_GOV, S_SPEC", "sewage by stream, m³/d: 0.85 of the domestic water, 0.54 of the rest"],
        ["QADF", "average dry-weather sewage flow of the plot in 2024, m³/d: the sum of the four streams"],
        ["FUT_CAP", "1 if an empty plot counts as a future home"],
        ["FUT_PROPS", "properties expected per counted plot: the settlement's ratio times its home share"],
        ["SPREAD_W", "weight for placing the settlement's growth: the plot's area capped at 1,000 m² on an empty plot of up to 2,000 m² that is not a grove, industrial or heritage; zero on every other plot; its share is this weight over the settlement's sum"],
        ["POP_2030, POP_2055, POP_ULT", "people on the plot in 2030, 2055 and the saturation year"],
        ["Q_2030, Q_2055, Q_ULT", "average sewage flow in 2030, 2055 and the saturation year, m³/d; a future plot at 171.3 l/d per person"],
        ["SAT_YEAR", "the year the plot's settlement is full"],
        ["ULT_YEAR", "the saturation year of the study area"],
    ], widths=[5.2, 11.3], font=8.2)
    D.p(d, "")
    D.tab_caption(d, "Fields of the settlement layer")
    D.table(d, ["Field", "Content"], [
        ["SETTLE, AREA_KM2", "name; area in km²"],
        ["WB_2024, WB_2100", "population of the Inception Report series in 2024 and 2100"],
        ["PROPS", "domestic properties (meters) in 2024"],
        ["OR_RAW, OR_S", "occupancy derived and adopted"],
        ["PPP_RAW, PPP_S", "properties per home plot derived and adopted"],
        ["HOMESH_RAW, HOMESH_S", "home share derived and adopted"],
        ["SMALL", "1 if under 1,000 people in 2024: the rule of Section 14.4 applies"],
        ["BUILT_PL, EMPTY_PL, HOME_MEAS", "built plots; empty plots; home plots the ratio was measured on"],
        ["CAP_PLOTS, CAP_POP", "empty plots counted as future homes; the people they hold at saturation"],
        ["G_NDOM, NDOM_POOL, G_GOV, GOV_POOL, G_AGR, G_SPEC", "meters by category; of the shop and government meters, those outside the estates that share the pool"],
        ["WORKERS", "workers of the industrial estates in the settlement"],
        ["U_NDOM, U_GOV", "non-domestic water per shop meter, governmental water per government meter, l/d"],
        ["POP_2024", "people in 2024"],
        ["W_DOM, W_NDOM, W_GOV, W_SPEC, W_TOT", "water by stream and in total, m³/d, 2024"],
        ["S_DOM, S_NDOM, S_GOV, S_SPEC, Q_2024", "sewage by stream and in total, m³/d, 2024"],
        ["POP_2025 … POP_2070, Q_2025 … Q_2070", "people and average sewage flow at five-year steps to the saturation year"],
        ["POP_ULT, Q_ULT", "people and flow in the saturation year of the study area"],
        ["SAT_YEAR, SAT_POP, SAT_Q", "the year the settlement is full, and its people and flow then"],
        ["SAT_OWN", "the year it would fill on its own growth alone; 0 if not before 2100"],
        ["IN_PEOPLE, OUT_PEOPLE, MAIN_TO, INSHARE", "people received from and sent to other settlements by the saturation year; the main receiver; the share of capacity taken by overflow"],
        ["ULT_YEAR, UNHOUSED", "the saturation year of the study area; growth of the series to 2100 with nowhere to go"],
    ], widths=[5.2, 11.3], font=8.2)

    # ----------------------------------------------------------------- A5
    D.h(d, 1, "A5   The overflow routes in full")
    D.p(d, "Every route carrying fifty people or more at saturation. The "
           "donor's year is the year its own empty plots are full; the "
           "receiver starts in the first year it takes in overflow from any "
           "settlement, which can be before this donor is full, and is itself "
           "full in the last column.")
    D.tab_caption(d, "Overflow routes")
    D.table(d, ["From", "To", "People at saturation", "Donor full", "Receiver starts", "Receiver full"],
            [[r["donor_name"], r["receiver_name"], F.fmt(r["people"]), str(r["donor_full"] or ""),
              str(r["starts"] or ""), str(r["receiver_full"] or "")] for r in F.routes()],
            widths=[3.2, 3.2, 2.6, 2.3, 2.6, 2.6], font=7.8)

    # ----------------------------------------------------------------- A6
    D.h(d, 1, "A6   Saturation with and without the overflow")
    D.p(d, "The year each settlement fills on its own growth alone, beside "
           "the year it fills when its neighbours' overflow is allowed to "
           "reach it. A settlement that would never fill on its own growth "
           "before 2100 is marked accordingly.")
    D.tab_caption(d, "Saturation year by settlement, own growth only and with overflow")
    D.table(d, ["Settlement", "Capacity, people", "Full on own growth", "Full with overflow", "People received"],
            [[r["name"], F.fmt(r["capacity"]), str(r["own"]) if r["own"] else "not before 2100",
              str(r["with_spill"] or ""), F.fmt(r["inflow"])] for r in F.own_growth_saturation()],
            widths=[4.0, 3.0, 3.2, 3.2, 3.1], font=8.2)
