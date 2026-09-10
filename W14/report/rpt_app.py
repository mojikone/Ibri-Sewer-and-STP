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
           f"from any plot and are carried by their settlement.")

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
    D.tab_caption(d, "The settlement rates used in Part D")
    D.table(d, ["Settlement", "Properties", "Pop. 2024", "Rate derived", "Rate adopted",
                "Properties per home plot", "Home share", "Capacity, people"],
            [[r["name"], F.fmt(r["properties"]), F.fmt(r["workbook_2024"]), f"{r['or_raw']:.2f}",
              f"{r['or_used']:.2f}", f"{r['ratio']:.2f}", f"{r['home_share']:.2f}", F.fmt(r["cap_people"])] for r in st],
            widths=[3.4, 1.9, 1.9, 1.7, 1.7, 2.2, 1.6, 2.1], font=7.8)
    D.p(d, "")
    p = D.p(d, "The rate adopted is the rate derived, held to a floor of 4.0 "
               "and a cap equal to the highest rate among the settlements of "
               "two thousand or more people. A settlement with fewer than ten "
               "built home-shaped plots takes the area-wide properties per "
               "plot and home share.")
    N.add(p, "Properties per home plot is measured over built plots whose "
             "meters are more than two thirds domestic and fewer than fifteen. "
             "Home share is the proportion of built, metered plots of home "
             "shape that are homes.")

    # ----------------------------------------------------------------- A4
    D.h(d, 1, "A4   The plot layer delivered with this report")
    D.p(d, "The plot layer carries, for each of the 77,265 plots, the fields "
           "below. It is the load table of the design: the network model "
           "reads the flow of each plot from it, and every figure in Part D "
           "is a sum over it.")
    D.tab_caption(d, "Fields of the plot layer")
    D.table(d, ["Field", "Content"], [
        ["Name, Classes, Buiding_St", "the cadastral identifier, class and built-or-future flag as received"],
        ["SETTLE", "the settlement the plot belongs to"],
        ["N_DOM, N_DOMADD, N_COM, N_GOV, N_AGR, N_CRT, N_IND", "meters on the plot by tariff group"],
        ["G_DOM, G_NDOM, G_GOV, G_SPEC, G_AGR", "meters by guideline category, the large consumers placed"],
        ["DERIVED, WHYC", "the use of the plot and the rule that set it"],
        ["NDVI_MEAN, NDVI_SHARE, GREEN_M2", "the satellite vegetation index of the plot: mean, green share, green area"],
        ["OR_S, PROPS, POP", "the settlement occupancy, the properties and the people on the plot in 2024"],
        ["W_DOM, W_NDOM, W_GOV, W_SPEC, W_TOT", "water demand by stream, m³/d"],
        ["S_DOM, S_NDOM, S_GOV, S_SPEC, QADF", "sewage by stream and in total, m³/d, 2024"],
        ["HOMESHAPE, FUT_CAP, FUT_PROPS, SPREAD_W", "whether an empty plot is home-shaped, whether it counts for capacity, the properties it will hold, its share of the growth"],
        ["POP_2030, Q_2030, POP_2055, Q_2055, POP_ULT, Q_ULT", "people and sewage in 2030, 2055 and the saturation year"],
        ["SAT_YEAR, ULT_YEAR", "the year the plot's settlement fills, and the saturation year of the study area"],
    ], widths=[6.0, 10.5], font=8.5)
