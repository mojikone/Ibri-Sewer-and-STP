"""Section 1.2, the study area, from 1.2.4 on: topography and drainage, climate, roads, flood hazard.
Added on the engineer's review of 2026-09-17. Every number is read from facts_area; the maps are
built by qgis_maps_area.py and the charts by charts_area.py. The main pipe is not shown anywhere
in this section: it is not client data."""
import os

import doc as D
import notes as N
import facts_area as A

IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img")


def _map(d, name, caption):
    D.wide_figure(d, os.path.join(IMG, name + ".png"), caption, size="A4")


def _pct(x, dec=0):
    return f"{100.0 * x:.{dec}f} per cent"


def study_area(d):
    topography(d)
    climate(d)
    roads(d)
    flood_hazard(d)


# --------------------------------------------------------------------- 1.2.4
def topography(d):
    g = A.ground(); rows = g["settlements"]; z0 = g["stp_ground"]
    top = max(rows, key=lambda r: r["z_med"]); low = A.below_stp()
    fall = (top["z_med"] - z0) / top["dist_km"]
    D.h(d, 3, "1.2.4.   Topography and drainage")
    p = D.p(d, f"The ground falls from the north-east to the south-west. The plots of the study area lie between "
               f"{g['z_p01']:.0f} and {g['z_p99']:.0f} metres. The built plots of {top['name']}, the highest settlement, "
               f"stand at {top['z_med']:.0f} metres, {top['dist_km']:.0f} kilometres from the existing STP, where the "
               f"ground is at {z0:.0f} metres: an average fall of about {fall:.0f} metres in every kilometre.")
    N.add(p, "Terrain model at 0.5 metre resolution (Section 2.3.2), read at every plot. The range quoted is from the "
             "1st to the 99th percentile of the plots; the level of a settlement is the median of its built plots.")
    D.p(d, "The wadis follow the same fall. They gather from the north and the east, join to the south of Ibri town "
           "and leave the study area to the south-west through Tanam. The map that follows shows the ground and "
           "the wadis of stream order three and above.")
    # the map ahead of the chart: a landscape page always closes the page before it, and this way the
    # chart shares the page after the map with the start of 1.2.5 instead of standing alone
    _map(d, "A01_topography",
         "Topography and drainage of the study area: ground level from the 0.5 m terrain model, the wadis of stream "
         "order three and above, and the existing STP at the low end of the study area.")
    names = " and ".join(r["name"] for r in low)
    drop = sum(z0 - r["z_med"] for r in low) / max(len(low), 1)
    D.p(d, f"The figure below sets the ground of each settlement against the ground at the existing STP, the "
           f"settlements in order of their distance from it. {_count(len(rows) - len(low))} of the {_count(len(rows)).lower()} "
           f"settlements stand above the STP, so their sewage can in principle reach it by gravity. "
           f"{_count(len(low))}, {names}, lie downstream of it, about {drop:.0f} metres lower, and cannot drain to the "
           f"existing STP by gravity. Whether each of the others does so without pumping depends on the ground "
           f"between, which the network design establishes (Section 6.2).")
    D.chart(d, "S01_ground_levels", 13.5)
    D.fig_caption(d, "Ground level of the built plots of each settlement, in order of distance from the existing STP. "
                     "The bar spans the 10th to the 90th percentile of the built plots.")


_WORDS = ["Zero", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten", "Eleven", "Twelve",
          "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen", "Twenty", "Twenty-one",
          "Twenty-two", "Twenty-three", "Twenty-four", "Twenty-five"]


def _count(n):
    return _WORDS[n] if 0 <= n < len(_WORDS) else str(n)


# --------------------------------------------------------------------- 1.2.5
def climate(d):
    c = A.climate(); w = A.wind(); m = c["monthly"]
    hot = [A.MONTHS[r["m"] - 1] for r in m if r["t_max"] >= 40.0]
    tmax = max(m, key=lambda r: r["t_max"]); tmin = min(m, key=lambda r: r["t_min"])
    months_long = {"Jan": "January", "Feb": "February", "Mar": "March", "Apr": "April", "May": "May", "Jun": "June", "Jul": "July",
                   "Aug": "August", "Sep": "September", "Oct": "October", "Nov": "November", "Dec": "December"}
    D.h(d, 3, "1.2.5.   Climate")
    p = D.p(d, "Ibri has a hot desert climate, class BWh of the Köppen-Geiger classification.")
    N.add(p, "Beck, H. E. et al. (2018), Present and future Köppen-Geiger climate classification maps at 1-km "
             "resolution, Scientific Data 5, 180214. A desert climate has annual rainfall below half of the aridity "
             f"threshold, here {c['koppen']['threshold_mm']:.0f} millimetres, and is hot where the mean annual "
             "temperature is 18 °C or more; the record below meets both.")
    p = D.p(d, f"No station record has been supplied. The figures below are from the NASA POWER record, a global "
               f"reanalysis on a grid of about 50 kilometres, read at the existing STP: temperature and rainfall for "
               f"{c['years'][0]} to {c['years'][1]}, and hourly wind at 10 metres for {w['years'][0]} to {w['years'][1]}. "
               f"The record describes the regime. It does not replace the station record, which the odour dispersion "
               f"modelling of Section 7.3 requires.")
    N.add(p, "NASA Prediction Of Worldwide Energy Resources, MERRA-2 reanalysis, power.larc.nasa.gov, read in September "
             "2026. The rainfall record after 2020 is not used: at this grid point it carries an implausible total for "
             "August 2024. Storm rainfall on a mountain front is poorly resolved on a grid of this size.")

    D.sub(d, "Temperature and rainfall")
    D.p(d, f"The mean daily maximum is 40 °C or more from {months_long[hot[0]]} to {months_long[hot[-1]]} and reaches "
           f"{tmax['t_max']:.0f} °C in {months_long[A.MONTHS[tmax['m'] - 1]]}; the mean daily minimum falls to {tmin['t_min']:.0f} °C in "
           f"{months_long[A.MONTHS[tmin['m'] - 1]]}. The annual mean is {c['t_mean_annual']:.1f} °C, and the daily maximum reaches 40 °C on "
           f"about {c['days_over_40']:.0f} days of the year. The heat bears on the design: sewage turns septic sooner in "
           f"long sewers and force mains (Section 6.3), and oxygen dissolves less readily in the aeration tanks.")
    D.p(d, f"Rain is scarce and irregular: {c['rain_annual_mean']:.0f} millimetres a year on average, between "
           f"{c['rain_annual_min']:.0f} millimetres in {c['rain_year_min']} and {c['rain_annual_max']:.0f} in {c['rain_year_max']}, "
           f"most of it from a few storms. The sewer system is separate and takes no stormwater, so the rain reaches "
           f"the design through the wadi floods of Section 1.2.7 and not through the design flow.")
    D.chart(d, "S02_climate", 15.0)
    D.fig_caption(d, f"Monthly temperature and rainfall at the existing STP, {c['years'][0]} to {c['years'][1]}, from the NASA POWER record.")

    nw, se = A.axis_share("all")
    D.sub(d, "Wind")
    D.p(d, f"The wind blows along one axis, north-west to south-east. Winds from the north-west quarter, west-north-west "
           f"round to north, take {_pct(nw)} of the hours, and winds from the south-east quarter, east-south-east round "
           f"to south, a further {_pct(se)}. The north-westerly prevails in winter and the south-easterly in summer; by "
           f"night the wind comes from the north-north-west and the north, or from the south-east. The mean speed at 10 metres is "
           f"{w['all']['mean_speed']:.1f} metres a second, and 95 per cent of the hours are below {w['p95_speed']:.1f} metres a second. A "
           f"reanalysis smooths out the calm hours, which matter most for odour, so the {_pct(w['all']['calm_share'])} of "
           f"hours below 1 metre a second shown here is a lower bound. The wind roses are on the next page.")

    dw = A.downwind(8.0); ibri = [r for r in dw if r["name"] == "Ibri"][0]
    worst = max(dw, key=lambda r: r["night"])
    D.p(d, f"The wind decides where the odour of a treatment plant travels. Ibri town lies {ibri['dist_km']:.1f} kilometres "
           f"to the {_sector_words(ibri['towards'])} of the existing STP; the wind that would carry odour from the STP towards it, from the "
           f"{_sector_words(ibri['wind_from'])}, blows for {_pct(ibri['all'])} of the hours and {_pct(ibri['night'])} of the night "
           f"hours, because the prevailing axis runs across that line and not along it. {worst['name']}, to the "
           f"{_sector_words(worst['towards'])}, lies downwind of the night wind from the {_sector_words(worst['wind_from'])} for "
           f"{_pct(worst['night'])} of the night hours. The table below gives "
           f"the same reading for every settlement within 8 kilometres of the existing STP. It is applied to each candidate "
           f"site in the siting assessment (Section 6.5.3); the odour buffer itself is established by dispersion "
           f"modelling (Section 7.3).")
    D.tab_caption(d, "Settlements within 8 km of the existing STP, and the wind that carries air from the STP towards them")
    D.table(d, ["Settlement", "Distance from the STP", "Direction from the STP", "Carried by wind from", "Share of all hours", "Share of night hours"],
            [[r["name"], f"{r['dist_km']:.1f} km", r["towards"], r["wind_from"], f"{100 * r['all']:.0f} %", f"{100 * r['night']:.0f} %"] for r in dw],
            widths=[4.2, 2.9, 2.9, 3.0, 2.5, 2.5], font=9)
    D.p(d, "")
    # page by page: the climate chart, the wind text and this table fill one page; the roses open the next
    # and share it with the text of 1.2.6
    D.chart(d, "S03_windrose", 13.0)
    D.fig_caption(d, f"Wind roses at 10 m at the existing STP, {w['years'][0]} to {w['years'][1]}: the direction the wind blows "
                     f"from and the share of hours in each speed class, for all hours, the night, the summer and the winter.")


def _sector_words(code):
    names = {"N": "north", "NNE": "north-north-east", "NE": "north-east", "ENE": "east-north-east", "E": "east", "ESE": "east-south-east",
             "SE": "south-east", "SSE": "south-south-east", "S": "south", "SSW": "south-south-west", "SW": "south-west",
             "WSW": "west-south-west", "W": "west", "WNW": "west-north-west", "NW": "north-west", "NNW": "north-north-west"}
    return names[code]


# --------------------------------------------------------------------- 1.2.6
def roads(d):
    rd = A.roads(); by = rd["by_class_km"]; tot = rd["total_km"]
    D.h(d, 3, "1.2.6.   Road network")
    p = D.p(d, f"The road centrelines supplied carry a class code, and the map on the next page shows them by that code, as "
               f"supplied; the chart after it gives the lengths. Inside the study area they total {tot:,.0f} kilometres: {by['01']:,.0f} kilometres of class 01, "
               f"{by['02']:,.0f} of class 02, {by['04']:,.0f} of class 04 and {by['05']:,.0f} of class 05. Classes 01 and 02 are "
               f"the through routes that cross the study area. Class 05, {_pct(by['05'] / tot)} of the length, is the street "
               f"grid of the settlements, which the collection network follows.")
    N.add(p, "Road centreline dataset, field StrCls, clipped to the updated project boundary. A dual carriageway is "
             "recorded as two centrelines and is counted on both.")
    D.p(d, f"The dual carriageways among them, {rd['dual_centreline_km']:,.0f} kilometres of centreline, are not used as sewer "
           f"corridors and are crossed at right angles only (Section 6.2.2).")
    _map(d, "A02_roads", "Road network of the study area, by the class code of the centrelines as supplied.")
    # the small chart after the map: it shares the page of 1.2.7, which the hazard maps would otherwise leave half empty
    D.chart(d, "S04_roads", 14.5)
    D.fig_caption(d, "Length of road centreline inside the study area, by the class code supplied.")


# --------------------------------------------------------------------- 1.2.7
def flood_hazard(d):
    D.h(d, 3, "1.2.7.   Flood hazard")
    p = D.p(d, "The wadis of Section 1.2.4 flood. The flood hazard across the study area is taken from the Oman Flood "
               "Mapping project of the Ministry of Agriculture, Fisheries and Water Resources, which maps the area on a "
               "3 metre grid. The four maps that follow show the floods of the 10, 25, 50 and 100-year return periods.")
    N.add(p, "Oman Flood Mapping project, Ministry of Agriculture, Fisheries and Water Resources; flood hazard grids of "
             "the Ibri area.")
    p = D.p(d, "The hazard is given in the six classes of the Australian classification, which combine the depth of the "
               "water and its velocity into what the flood does to people, vehicles and buildings. The table below "
               "gives the classes.")
    N.add(p, "Australian Institute for Disaster Resilience (2017), Guideline 7-3, Flood Hazard, supporting Handbook 7, "
             "Managing the Floodplain; adopted in Australian Rainfall and Runoff 2019.")
    D.tab_caption(d, "Flood hazard classes of the Australian classification")
    D.table(d, ["Class", "What the flood does", "Depth × velocity, m²/s, up to", "Depth, m, up to", "Velocity, m/s, up to"],
            [list(r) for r in A.HAZARD_CLASSES], widths=[1.4, 8.2, 3.2, 2.6, 2.6], font=9)
    D.p(d, "")
    D.p(d, "In every return period the high classes, H5 and H6, keep to the main wadi channels: the wadi that crosses the "
           "south of the study area from Suwayda al Ma through Al Jibayyah to the south of Ibri town, and its continuation "
           "to the south-west through Ad Dibayshi and Tanam. Away from the channels the flooding is shallow sheet flow in "
           "class H1. The channels widen and the classes rise with the return period.")
    D.p(d, "The maps are used in three places. The treatment plant and the pumping stations are sited clear of the high "
           "classes, or protected to the levels of Section 7.2. The wadi crossings of the sewers and force mains are "
           "identified from them. And the flood protection assessment of Section 7.2 works from the 25, 50 and 100-year "
           "floods.")
    caps = [(os.path.join(IMG, f"A{3 + i:02d}_hazard_T{T}.png"),
             f"Flood hazard in the study area, {T}-year return period. Oman Flood Mapping project, MAFWR; Australian hazard classes.")
            for i, T in enumerate((10, 25, 50, 100))]
    D.wide_figures(d, caps, size="A4")
