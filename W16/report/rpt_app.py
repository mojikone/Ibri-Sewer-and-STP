"""Appendix A for Revision 3: the working behind Chapter 4, so a reviewer can check it."""
import os

import doc as D
import notes as N
import facts_w14 as F

IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img")
fmt = F.fmt


def appendices(d):
    D.chapter(d, "Appendix A.   Population, land use and flow: the working")
    st = F.settlement_table(); mc = F.meter_counts(); cs = F.crt_summary(); t = F.totals()

    # ----------------------------------------------------------------- A1
    D.h(d, 2, "A.1.   Electricity meters: tariff to category")
    D.p(d, "Each tariff in the electricity dataset is assigned to one of the "
           "guideline's categories. The large-consumer tariff is resolved "
           "account by account in A.2.")
    tariffs = mc["tariff"]
    D.tab_caption(d, "Tariffs and the category adopted")
    D.table(d, ["Tariff", "Meters", "Category", "People"], [
        ["Primary Account Tariff", fmt(tariffs.get("Primary Account Tariff", 0)), "Domestic", "one property"],
        ["Primary Account Tariff (with National Subsidy)", fmt(tariffs.get("Primary Account Tariff (with National Subsidy)", 0)), "Domestic", "one property"],
        ["Additional Account Tariff", fmt(tariffs.get("Additional Account Tariff", 0)), "Domestic", "one property"],
        ["Commercial", fmt(tariffs.get("Commercial", 0)), "Non-domestic", "none"],
        ["Fisheries", fmt(tariffs.get("Fisheries", 0)), "Non-domestic", "none"],
        ["Tourism", fmt(tariffs.get("Tourism", 0)), "Non-domestic", "none"],
        ["Government", fmt(tariffs.get("Government", 0)), "Governmental", "none"],
        ["MOD", fmt(tariffs.get("MOD", 0)), "Governmental", "none"],
        ["Agricultural", fmt(tariffs.get("Agricultural", 0)), "Agricultural", "none; no sewage"],
        ["Industrial", fmt(tariffs.get("Industrial", 0)), "Special consumption", "none"],
        ["CRT Seasonal", fmt(tariffs.get("CRT Seasonal", 0)), "Large consumer, see A.2", "none"],
        ["CRT Time of Use", fmt(tariffs.get("CRT Time of Use", 0)), "Large consumer, see A.2", "none"],
        ["CRT Fixed Rate", fmt(tariffs.get("CRT Fixed Rate", 0)), "Large consumer, see A.2", "none"],
    ], widths=[7.0, 2.2, 4.3, 3.0], font=8.5)
    D.p(d, "")
    D.p(d, f"Of the {fmt(mc['total'])} meters, {fmt(mc['inside'])} fall inside "
           f"a plot, {fmt(mc['snapped'])} were assigned to the nearest plot "
           f"within fifteen metres, and {fmt(mc['free'])} lie further from any "
           f"plot; they carry no load (Section 4.1.3).")

    # ----------------------------------------------------------------- A2
    D.h(d, 2, "A.2.   The large-consumer accounts")
    use = cs["use"]; conf = cs["conf"]
    D.p(d, f"The {cs['total']} accounts on the Cost Reflective Tariff were "
           f"placed by clustering them at 120 metres, matching each cluster "
           f"and each single account against the named features of "
           f"OpenStreetMap within eighty metres, reverse geocoding the rest, "
           f"and inspecting the largest clusters on the aerial imagery. Each "
           f"account carries the use found, the category adopted, the evidence "
           f"and a confidence.")
    D.tab_caption(d, "Large-consumer accounts by the use found")
    D.table(d, ["Use found", "Accounts", "Category adopted", "Typical sites"], [
        ["Commercial", fmt(use.get("Commercial", 0)), "Non-domestic", "Bawadi shopping centre, the Al Murtafa souq, the Araqi strip, hypermarkets, banks, fuel stations"],
        ["Government", fmt(use.get("Government", 0)), "Governmental", "Police headquarters, post office, directorates"],
        ["Education", fmt(use.get("Education", 0)), "Governmental", "The university campus, the college, schools"],
        ["Health", fmt(use.get("Health", 0)), "Governmental", "Ibri Hospital, clinics"],
        ["Religious", fmt(use.get("Religious", 0)), "Governmental", "Mosques"],
        ["Industrial", fmt(use.get("Industrial", 0)), "Special consumption", "The Tanam estate"],
        ["Agricultural", fmt(use.get("Agricultural", 0)), "Agricultural, no load", "Farm pumps at Al Aynayn"],
        ["Telecommunications, utility", fmt(use.get("Telecom/Utility", 0)), "Non-domestic", "Exchanges, water facilities, masts"],
        ["Unresolved", fmt(use.get("Unresolved", 0)), "Non-domestic", "No recorded feature within eighty metres"],
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
    D.h(d, 2, "A.3.   Occupancy rate, properties per plot, home share and capacity by settlement")
    D.tab_caption(d, "The settlement rates used in Chapter 4: calculated from the data, and adopted")
    D.table(d, ["Settlement", "Domestic properties, 2024", "Pop. 2024", "Empty plots", "of which counted as future homes",
                "Occupancy rate calculated", "adopted", "Properties per home plot calculated", "adopted",
                "Home share calculated", "adopted", "Capacity, people"],
            [[r["name"], fmt(r["properties"]), fmt(r["workbook_2024"]), fmt(r["empty_plots"]), fmt(r["cap_plots"]),
              f"{r['or_raw']:.2f}", f"{r['or_used']:.2f}", f"{r['ratio_raw']:.2f}", f"{r['ratio']:.2f}",
              f"{r['home_share_raw']:.2f}", f"{r['home_share']:.2f}", fmt(r["cap_people"])] for r in st]
            + [["Total", fmt(sum(r["properties"] for r in st)), fmt(sum(r["workbook_2024"] for r in st)), fmt(sum(r["empty_plots"] for r in st)),
                fmt(sum(r["cap_plots"] for r in st)), "", "", "", "", "", "", fmt(t["capacity"])]],
            widths=[2.6, 1.5, 1.3, 1.2, 1.4, 1.2, 1.2, 1.3, 1.1, 1.2, 1.1, 1.4], font=6.8, keep_together=False)
    D.p(d, "")
    p = D.p(d, "The occupancy rate adopted is the rate calculated, held to a "
               "floor of 4.0 and a cap equal to the highest rate among the "
               "settlements of two thousand or more people. A settlement of "
               "fewer than a thousand people in 2024 takes an occupancy rate of "
               "4.0, one property per plot and a home share of 0.9, whatever "
               "its meters return: it has no sample to measure on, and it does "
               "not attract a second property on a plot.")
    N.add(p, "Properties per home plot is measured over built plots whose "
             "meters are more than two thirds domestic and fewer than fifteen. "
             "Home share is the proportion of built, metered plots of home "
             "shape that are residential. Empty plots counted as future homes "
             "are those of 200 to 1,000 square metres, compact, not a strip, "
             "and not planted, industrial or heritage.")

    # ----------------------------------------------------------------- A4
    D.h(d, 2, "A.4.   The overflow routes in full")
    D.p(d, "Every route carrying fifty people or more at saturation. The "
           "donor's year is the year its own empty plots are full; the "
           "receiver starts in the first year it takes in overflow from any "
           "settlement, which can be before this donor is full, and is itself "
           "full in the last column.")
    D.tab_caption(d, "Overflow routes")
    D.table(d, ["From", "To", "People at saturation", "Donor full", "Receiver starts", "Receiver full"],
            [[r["donor_name"], r["receiver_name"], fmt(r["people"]), str(r["donor_full"] or ""),
              str(r["starts"] or ""), str(r["receiver_full"] or "")] for r in F.routes()],
            widths=[3.2, 3.2, 2.6, 2.3, 2.6, 2.6], font=7.8, keep_together=False)
