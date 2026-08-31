"""Sections 3 to 9 - the flow chain, from raw data to a sized gravity sewer."""
from docx.enum.text import WD_ALIGN_PARAGRAPH as AL

import os

IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img")

import doc as D
import omml as M

Q = M.Q
UP = M.up
R = M.r


def _params(d, rows):
    D.table(d, ["Symbol", "Meaning", "Unit"], rows,
            widths=[2.6, 10.4, 3.5], font=9)


def _source(d, text):
    D.p(d, "Source: " + text, size=9, italic=True, colour=D.GREY,
        space_after=10)


# ============================================================ 3. DATA
def s3_data(d):
    D.h(d, 1, "3   Preparing the data", page_break=True)

    D.h(d, 2, "3.1   Purpose")
    D.p(d, "Every later number rests on knowing how many properties sit on each "
           "plot and what each one is used for. The cadastral data does not say. "
           "This step builds that layer, and it is the only step whose output is "
           "a dataset rather than a number.")

    D.h(d, 2, "3.2   What the source data does and does not contain")
    D.p(d, "The plot layer from MoHUP carries geometry. It does not distinguish "
           "developed from undeveloped plots, it is missing plots that exist on "
           "the ground, and it carries no land use and no count of dwellings.")
    D.p(d, "The electricity account layer supplies what is missing — but only "
           "partly, and the limit matters. It carries a tariff name and a "
           "coordinate. It carries no land use, no floor area, and no "
           "consumption figure. It can therefore say what kind of customer sits "
           "at a point and how many there are. It can never say how large that "
           "customer is.")

    D.callout(d, "This single limitation decides the demand method.",
              "GUD-201 Table 12 prices non-domestic demand in pupils, beds, "
              "employees and square metres of floor area. None of those "
              "quantities exists in any dataset held for this project. The "
              "percentage-uplift route is therefore the one in use, and Table 12 "
              "is adopted on the day real quantities are supplied. See "
              "Section 5.4.",
              fill="EAF1F8", colour=D.MID)

    D.picture(d, os.path.join(IMG, "F2_data.png"), 15.5)
    D.fig_caption(d, "Building the plot layer. Points matching no plot wait for the corrected cadastre rather than being moved first.")

    D.h(d, 2, "3.3   Method")
    D.numbered(d, "Points sharing an identical coordinate are stacked "
                  "properties at one address, and are counted individually.")
    D.numbered(d, "Points falling inside a plot belong to that plot, whatever "
                  "their spacing.")
    D.numbered(d, "Points falling inside no plot are left unassigned until the "
                  "corrected plot layer is available. Only then are any "
                  "remaining orphans moved to the nearest plot that holds none.")
    D.numbered(d, "Each tariff is mapped to one consumption category. The "
                  "mapping is an inference and is recorded as one.")

    D.callout(d, "Assign orphan points last, not first.",
              "Moving a point to a neighbouring plot moves load between streets "
              "and changes the pipe sizes on both. Many unmatched points will "
              "land naturally once the missing plots are digitised, so shifting "
              "before that step manufactures errors that the corrected data "
              "would have avoided.")

    D.h(d, 2, "3.4   Mapping tariffs to consumption categories")
    D.p(d, "The electricity file names a tariff. The guideline names a "
           "consumption category. The crosswalk between them is the following, "
           "and it is ours rather than NWS's.")
    D.tab_caption(d, "Electricity tariff to guideline consumption category")
    D.table(d,
            ["Tariff as issued", "Category", "Treatment"],
            [["Primary Account", "Domestic", "one dwelling"],
             ["Primary Account with National Subsidy", "Domestic", "one dwelling"],
             ["Additional Account", "Domestic", "a separate dwelling on the same plot"],
             ["Commercial, Fisheries, Tourism", "Non-domestic", "carries the uplift volume"],
             ["Government, MOD", "Governmental", "carries the uplift volume"],
             ["Agricultural", "No sewage load", "an irrigation pump — see below"],
             ["Cost Reflective Tariff (CRT)", "Unresolved", "a size class, not a land use"],
             ["Industrial", "Case by case", "excluded from the uplift ratios by G201 p59"]],
            widths=[6.0, 4.0, 6.5], font=9)

    D.h(d, 3, "Agricultural plots")
    D.p(d, "An agricultural meter powers a borehole pump. The water it lifts "
           "goes onto a field and never reaches a sewer. Where a dwelling stands "
           "on a farm plot it carries its own domestic account, which is counted "
           "normally. The test is therefore whether the plot holds a domestic "
           "meter, not whether it holds an agricultural one.")
    D.bullet(d, "an agricultural meter on a plot that already holds a domestic "
                "meter adds nothing", lead="Rule — ")
    D.bullet(d, "an agricultural-only plot carries no dwelling", lead="Rule — ")

    D.h(d, 3, "Cost Reflective Tariff")
    D.p(d, "CRT is a consumption-threshold tariff, applied to large consumers "
           "and billed at unsubsidised rates. It says a customer is big; it does "
           "not say what the customer is. A shopping centre, a factory, a hotel "
           "and a large government building all fall into it. These accounts are "
           "therefore both the most significant consumers and the only ones the "
           "tariff cannot classify. They must be resolved against the plot "
           "layer or by site inspection before any uplift ratio is applied.")

    _source(d, "G201 §7.3 p59-61 for the consumption categories; the tariff "
               "crosswalk is a project inference recorded in the concept "
               "report's inference register.")


# ============================================================ 4. POPULATION
def s4_population(d):
    D.h(d, 1, "4   Population", page_break=True)

    D.h(d, 2, "4.1   Purpose")
    D.p(d, "Population drives every flow in the chain. The guideline permits "
           "three routes to it, and the choice between them is not free: they "
           "answer different questions and are used for different parts of the "
           "design.")

    D.h(d, 2, "4.2   The three permitted routes")
    D.table(d,
            ["Route", "Basis", "What it is good for"],
            [["Developer figures", "supplied directly", "takes precedence where they exist"],
             ["NCSI projection", "official census series", "populations at dated years"],
             ["Plot count", "plots × properties × occupancy", "the saturation ceiling"]],
            widths=[3.6, 5.4, 7.5], font=9)
    D.p(d, "")
    D.p(d, "The two routes used here answer different questions. The census "
           "projection says how many people there will be in a given year. The "
           "plot count says how many there can ever be. Buried pipe, which "
           "lasts fifty years and cannot be economically re-laid, is sized on "
           "the ceiling. The plant, which is built in phases, is sized on the "
           "dated years.")

    D.picture(d, os.path.join(IMG, "F3_population.png"), 15.5)
    D.fig_caption(d, "Two routes to population. The census route dates the plant; the plot route sizes the pipe.")

    D.h(d, 2, "4.3   Population from plots")
    eq = D.next_eq()
    M.display(d, M.seq(UP("Population"), M.EQ, UP("N"), M.sub(R(""), UP("plots")),
                       M.TIMES, UP("p"), M.TIMES, UP("OR")), number=eq)
    _params(d, [
        ["N plots", "number of plots, classified by clear typologies", "count"],
        ["p", "average number of properties per plot", "dimensionless"],
        ["OR", "occupancy rate, persons per housing unit", "persons per unit"]])
    _source(d, "G201 §7.2.2 p58.")

    D.h(d, 2, "4.4   Occupancy rate")
    eq = D.next_eq()
    M.display(d, M.seq(UP("OR"), M.EQ,
                       M.frac(UP("Population"), UP("Housing units"))), number=eq)
    D.p(d, "The guideline requires both terms to come from NCSI, at the "
           "geographic scale of the project, using the most recent data.")

    D.callout(d, "A declared departure.",
              "NCSI does not publish housing units at settlement level. This "
              "project therefore counts properties from active domestic "
              "electricity accounts instead. The guideline itself uses active "
              "domestic accounts in its own derivation of consumption per "
              "capita, which supports the substitution — but it remains a "
              "departure and must be stated as one and agreed with NWS.")

    D.p(d, "Two conditions make the result meaningful. Both halves of the "
           "fraction must describe the same ground: a wilayat population divided "
           "by the meters of one town gives a household size that is too large "
           "purely because people were kept and houses discarded. And only "
           "domestic accounts belong in the denominator, since a shop is not a "
           "dwelling.")
    _source(d, "G201 §7.2.2 p58; the account-based derivation follows the form "
               "of the consumption formula at G201 p60.")

    D.h(d, 2, "4.5   Disaggregation and extrapolation")
    D.p(d, "Where a forecast exists only at wilayat level it must be "
           "distributed to settlements in proportion to the latest census "
           "shares. Below settlement scale, the guideline directs distribution "
           "pro rata to the number of electricity accounts.")

    D.callout(d, "The extrapolation ceiling.",
              "NCSI forecasts run twenty to twenty-five years. Beyond that the "
              "guideline permits polynomial regression but states that it is "
              "not recommended to extrapolate more than ten years past the "
              "forecast period. A projection reaching decades beyond the "
              "underlying data is an assumption presented as a number, and any "
              "capacity argument resting on it should be defended on land "
              "availability instead.")

    D.p(d, "The guideline also requires that build-out be phased. Raw plot "
           "count multiplied by occupancy assumes every plot is developed at "
           "once, which the NOTE at G201 p59 expressly warns against — it "
           "requires development percentages to be applied over the design "
           "period, particularly to avoid overestimation.")
    _source(d, "G201 §7.2.1 p58, and the NOTE at p59.")


# ============================================================ 5. DEMAND
def s5_demand(d):
    D.h(d, 1, "5   Water demand", page_break=True)

    D.h(d, 2, "5.1   Purpose")
    D.p(d, "Wastewater is derived from water demand, so demand is calculated "
           "first even though the project is a sewerage scheme. Demand has five "
           "components, and three of them are commonly forgotten.")

    D.h(d, 2, "5.2   The five components")
    D.table(d,
            ["Component", "Basis", "Clause"],
            [["Domestic", "population × litres per capita per day", "§7.3.1"],
             ["Non-domestic", "22 % uplift, or Table 12 unit rates", "§7.3.2"],
             ["Governmental", "14 % uplift, or project-specific", "§7.3.3"],
             ["Special", "developer-supplied; labour camps, thirsty industry", "§7.3.4"],
             ["Blue tankers", "from tanker filling station records", "§7.3.5"]],
            widths=[3.4, 9.6, 3.5], font=9)
    D.p(d, "")
    D.p(d, "The last two sit outside the percentage uplifts and are added "
           "separately. The guideline is explicit that special consumption is "
           "not covered by population forecasts, and that the uplift ratios do "
           "not apply to identified projects such as economic zones, which are "
           "determined case by case.")

    D.picture(d, os.path.join(IMG, "F4_demand.png"), 15.5)
    D.fig_caption(d, "Assembling demand, and the point at which the tier is decided.")

    D.h(d, 2, "5.3   Domestic demand")
    eq = D.next_eq()
    M.display(d, M.seq(M.sub(R("Q"), UP("dom")), M.EQ,
                       UP("Population"), M.TIMES, UP("LPCD")), number=eq)
    _params(d, [
        ["Q dom", "domestic water demand", "litres per day"],
        ["LPCD", "unit consumption; 164 for Adh Dhahirah", "l/c/d"]])

    D.p(d, "The 164 figure is indicative, derived from the 2024 Integrated "
           "Master Plan, applies in the absence of updated figures, and the "
           "guideline states it should be validated by NWS before design. It "
           "measures network-accounted water only, so it excludes tanker "
           "deliveries and private wells.")

    D.h(d, 3, "How the figure was derived")
    eq = D.next_eq()
    M.display(d, M.seq(UP("LPCD"), M.EQ,
                       M.frac(UP("Total domestic water accounted"),
                              M.seq(UP("OR"), M.TIMES,
                                    UP("Active domestic accounts")))), number=eq)
    D.p(d, "This is shown because it explains what the number is, not because "
           "it is a routine design step. Note that occupancy rate appears in the "
           "denominator: raising it lowers the consumption per capita, so the "
           "two move together and cannot be chosen independently.")
    _source(d, "G201 §7.3.1 p59-60 and Table 11.")

    D.h(d, 2, "5.4   Non-domestic and governmental — the two tiers")
    D.p(d, "The guideline offers two routes, and the choice is not a matter of "
           "preference.")

    D.table(d,
            ["", "Tier A — ratios", "Tier B — Table 12"],
            [["When", "in the absence of detailed land use allocation",
              "where detailed land use allocation exists"],
             ["Method", "22 % and 14 % of domestic demand",
              "unit rates per pupil, bed, employee, m²"],
             ["Wording", "the published fallback", "\"shall be calculated using\""],
             ["Needs", "population only",
              "counts of pupils, beds, staff, and floor areas"]],
            widths=[2.4, 6.5, 7.6], font=9)

    D.p(d, "")
    eq = D.next_eq()
    M.display(d, M.seq(M.sub(R("Q"), UP("ND")), M.EQ,
                       M.sub(R("Q"), UP("dom")), M.TIMES, R("0.22")), number=eq)
    eq = D.next_eq()
    M.display(d, M.seq(M.sub(R("Q"), UP("gov")), M.EQ,
                       M.sub(R("Q"), UP("dom")), M.TIMES, R("0.14")), number=eq)

    D.p(d, "The word to notice in the table heading is Distributed. These are "
           "not per-person demands. They are the governorate's measured "
           "non-domestic and governmental volumes, taken from the 2021 to 2023 "
           "water balance and spread across the population for convenience. "
           "That is why the total is right and the distribution is not: a "
           "residential-only street generates no commercial flow at all.")

    D.callout(d, "Never apply both routes.",
              "Table 12 unit rates on commercial plots plus the 22 % and 14 % "
              "uplifts counts the same water twice. Use one or the other. "
              "Whichever is used, identified projects, special consumption, "
              "tankers and private wells remain additive — the guideline "
              "excludes those from the ratios by name, so adding them is not "
              "double counting.")

    D.h(d, 3, "If Table 12 is ever used")
    D.p(d, "Its rates are keyed to occupancy of the built area, never to plot "
           "area. Substituting cadastral area is wrong by an order of magnitude: "
           "121 hectares of mosque plots at the mosque rate of 185 litres per "
           "square metre per day would produce roughly four times the entire "
           "ultimate flow of the scheme.")
    _source(d, "G201 §7.3.2 p60, §7.3.3 p61, Table 11 p60 and Table 12 p61.")

    D.h(d, 2, "5.5   Tanker demand")
    D.p(d, "Where a tanker filling station lies within or near the project area, "
           "tanker consumption must be explicitly assessed from NWS station "
           "records — historical use, the area served, and how that is expected "
           "to change over the horizon — and validated by NWS.")

    D.callout(d, "The published governorate ratio does not reconcile.",
              "Table 13 gives Adh Dhahirah a tanker volume of 5,145 m³/d and a "
              "ratio to networked domestic consumption of 333 %. Those two "
              "figures together imply the governorate's entire piped domestic "
              "consumption is about 1,545 m³/d, which at 164 l/c/d serves "
              "roughly 9,400 people. Ibri wilayat alone has many times that. The "
              "volume column of the table sums correctly to its printed total, "
              "so the volumes are sound and the ratio is not. It cannot be "
              "corrected from the document and should be raised with NWS.")
    _source(d, "G201 §7.3.5 p61-62 and Table 13 p62.")


# ============================================================ 6. WASTEWATER
def s6_wastewater(d):
    D.h(d, 1, "6   Wastewater generation", page_break=True)

    D.h(d, 2, "6.1   Purpose")
    D.p(d, "Not all supplied water returns to the sewer. Irrigation evaporates, "
           "process water is consumed, some is lost. The return rate converts "
           "demand into the flow the pipe actually receives.")

    D.h(d, 2, "6.2   Return rates")
    D.p(d, "The guideline gives two rates, and only two. Governmental "
           "consumption is folded into the non-domestic figure rather than "
           "carrying its own.")
    D.tab_caption(d, "Return ratio, as a percentage of drinking water demand")
    D.table(d, ["Type of consumption", "Discharge ratio"],
            [["Domestic and tanker", "**85 %**"],
             ["Non-domestic, including government and commercial", "**54 %**"]],
            widths=[10.5, 6.0], font=9.5)

    D.p(d, "")
    eq = D.next_eq()
    M.display(d, M.seq(M.sub(R("Q"), UP("ww")), M.EQ,
                       R("0.85"), M.sub(R("Q"), UP("dom+tank")), M.PLUS,
                       R("0.54"), M.sub(R("Q"), UP("ND+gov"))), number=eq)
    _params(d, [
        ["Q ww", "wastewater generated, before infiltration", "m³/d"],
        ["Q dom+tank", "domestic demand plus tanker deliveries", "m³/d"],
        ["Q ND+gov", "non-domestic plus governmental demand", "m³/d"]])

    D.callout(d, "Tankered water generates sewage.",
              "The 85 % applies to domestic and tanker together. Water that "
              "arrives by truck is drunk, washed with and flushed exactly as "
              "piped water is; the delivery method changes nothing downstream. "
              "Omitting it understates the load, and in this governorate the "
              "tankered volume is substantial.",
              fill="EAF1F8", colour=D.MID)

    D.h(d, 2, "6.3   Non-network water sources")
    D.p(d, "The guideline places a binding duty on the designer to assess other "
           "water sources within the project area — private wells, private water "
           "providers and other non-network abstraction — so that their "
           "contribution to wastewater is accounted for. No rate is given. The "
           "assessment has to be made and the assumption declared.")
    _source(d, "G201 §7.4 p70, §7.4.1 p70-71 and Table 19 p71.")

    D.h(d, 2, "6.4   The alternative route where land use is detailed")
    D.p(d, "Where detailed land use information exists, the guideline requires "
           "design flows to be calculated to a recognised international standard "
           "such as BS EN 752, with the standard used clearly stated and "
           "supported by site-specific evidence. This is the wastewater-side "
           "counterpart of the Table 12 switch on the demand side, and it is "
           "governed by the same condition.")
    _source(d, "G201 §7.4.1 p71.")


# ============================================================ 7. TIME
def s7_time(d):
    D.h(d, 1, "7   Projecting through time", page_break=True)

    D.h(d, 2, "7.1   Purpose")
    D.p(d, "A single ultimate flow sizes the pipes but says nothing about when "
           "the plant must be built, or how long the network will run at a "
           "fraction of its design flow. Both answers come from a year-by-year "
           "series.")

    D.h(d, 2, "7.2   Interval")
    D.p(d, "The TOR requires population forecasting and flow projection at "
           "five-year intervals. Calculate annually and report at five-year "
           "steps: the finer series costs nothing extra and is needed for the "
           "self-cleansing assessment, which turns on the earliest years rather "
           "than on any reporting milestone.")

    D.h(d, 2, "7.3   Connection ratio")
    D.p(d, "Population is not the same as connected population. A new network "
           "fills gradually as properties are joined to it, and until they are, "
           "the flow is a fraction of what the population implies.")
    eq = D.next_eq()
    M.display(d, M.seq(M.sub(R("Q"), UP("year")), M.EQ,
                       M.sub(UP("P"), UP("year")), M.TIMES,
                       M.sub(UP("c"), UP("year")), M.TIMES, UP("q")), number=eq)
    _params(d, [
        ["P year", "population in that year", "persons"],
        ["c year", "connection ratio, connected divided by total population", "fraction"],
        ["q", "wastewater generated per person", "m³/person/day"]])

    D.callout(d, "The connection ratio is what makes the washing schedule "
                 "answerable.",
              "It is the reason early-year flows are low enough to leave solids "
              "in the pipe. Leave it out and the network appears to reach "
              "self-cleansing velocity on the day it opens, which it does not.",
              fill="EAF1F8", colour=D.MID)

    D.h(d, 2, "7.4   Saturation")
    D.p(d, "Two different meanings are in circulation and they must not be "
           "confused in the same document.")
    D.bullet(d, "the year the last developable plot is built out. A property of "
                "the land.", lead="Development ceiling — ")
    D.bullet(d, "the year a particular asset reaches its capacity. A property "
                "of the design.", lead="Capacity trigger — ")
    D.p(d, "The first bounds the second. Where a projection carries population "
           "past the ceiling, the surplus has nowhere to live and the projection "
           "has left the physical world — which is the practical form of the "
           "extrapolation limit in Section 4.5.")


# ============================================================ 8. PEAK
def s8_peak(d):
    D.h(d, 1, "8   Peak flow and infiltration", page_break=True)

    D.h(d, 2, "8.1   Purpose")
    D.p(d, "Sewers are not sized on average flow. They are sized on the peak, "
           "plus whatever groundwater leaks in through the joints.")

    D.h(d, 2, "8.2   Merrimack")
    D.p(d, "For any catchment or sub-catchment of more than one hundred "
           "properties, the guideline states that the Merrimack formula is to be "
           "used. It gives no method for smaller catchments.")
    eq = D.next_eq()
    M.display(d, M.seq(M.sub(R("Q"), UP("pdf")), M.EQ, R("2.65"),
                       M.sup(M.sub(R("Q"), UP("adf")), R("0.879"))), number=eq)
    _params(d, [
        ["Q pdf", "peak daily flow", "**Ml/day**"],
        ["Q adf", "average daily flow", "**Ml/day**"]])

    D.callout(d, "Both flows are in megalitres per day.",
              "Because the exponent is 0.879 and not 1, feeding this formula "
              "cubic metres per day does not merely scale the answer — it "
              "returns a different number. One megalitre per day is one thousand "
              "cubic metres per day. This is the single most common error in the "
              "whole chain.")

    eq = D.next_eq()
    M.display(d, M.seq(UP("Pf"), M.EQ,
                       M.frac(M.sub(R("Q"), UP("pdf")),
                              M.sub(R("Q"), UP("adf")))), number=eq)

    D.h(d, 2, "8.3   Peltier, the master plan alternative")
    D.p(d, "The guideline also records the method used in the 2024 Integrated "
           "Master Plan. It is described rather than mandated, and Merrimack "
           "carries the obligatory wording.")
    eq = D.next_eq()
    M.display(d, M.seq(M.sub(UP("Pf"), UP("ww")), M.EQ, R("1.5"), M.PLUS,
                       M.frac(R("1"), M.sqrt(M.sub(R("Q"), UP("m"))))), number=eq)
    _params(d, [
        ["Pf ww", "wastewater peak factor", "dimensionless"],
        ["Q m", "average daily flow", "**litres per second**"]])

    D.callout(d, "This formula differs from the published Peltier relation.",
              "The classical form carries 2.5 in the numerator; the guideline "
              "prints 1. This was confirmed three separate ways — a "
              "high-resolution render of the page, a coordinate-level dump of "
              "the text showing a single raised glyph, and the text layer "
              "itself. The guideline as issued prints 1, and that is what is "
              "reproduced here. Whether NWS intended the classical form is a "
              "question for NWS. In practice it changes nothing for this "
              "project, because Merrimack is the mandated route.")

    D.p(d, "Note also that Merrimack wants megalitres per day and Peltier wants "
           "litres per second, on facing pages, using symbols the abbreviation "
           "list defines identically.")

    D.h(d, 2, "8.4   The cap on hourly peak factor")
    D.p(d, "The guideline states that it is recommended the hourly peak factor "
           "should not exceed 5.0. The wording is doubly hedged and is not an "
           "obligation. Truncating a small headworks at 5.0 without saying so "
           "hides a real peak.")

    D.h(d, 2, "8.5   Infiltration")
    D.p(d, "Accounting for infiltration is mandatory. The three values "
           "themselves are recommendations, and they do not share a common "
           "basis — two are proportions of flow and one is a rate per length of "
           "pipe, so they are not interchangeable.")
    D.tab_caption(d, "Infiltration allowances")
    D.table(d, ["Case", "Allowance"],
            [["Existing network in a groundwater zone or coastal area",
              "up to 40 % of wastewater flow"],
             ["Existing network inland, outside groundwater influence",
              "10 % of wastewater flow"],
             ["**Newly designed network**", "**720 litres per day per km of sewer**"]],
            widths=[10.5, 6.0], font=9.5)
    D.p(d, "")
    D.p(d, "Stormwater infiltration is expressly not considered, and tanker or "
           "vacuum collection carries no infiltration allowance at all.")
    _source(d, "G201 §7.4.2 p71-72 and §7.4.3 p72.")

    D.picture(d, os.path.join(IMG, "F5_flow.png"), 15.5)
    D.fig_caption(d, "From demand to the flow the pipe is sized on.")

    D.h(d, 2, "8.6   Assembling the design flow")
    eq = D.next_eq()
    M.display(d, M.seq(M.sub(R("Q"), UP("design")), M.EQ,
                       M.sub(R("Q"), UP("ww")), M.TIMES, UP("Pf"), M.PLUS,
                       M.sub(R("Q"), UP("inf"))), number=eq)
    D.p(d, "Infiltration is added after peaking, not before. It is a steady "
           "leak and does not peak with the diurnal cycle.")


# ============================================================ 9. GRAVITY
def s9_gravity(d):
    D.h(d, 1, "9   Gravity sewer design", page_break=True)

    D.h(d, 2, "9.1   Purpose")
    D.p(d, "Turning a design flow into a diameter, a gradient and an invert "
           "level, while keeping the pipe fast enough to scour itself and slow "
           "enough not to erode.")

    D.h(d, 2, "9.2   Which formula")
    D.p(d, "The guideline requires that a recognised hydraulic formula be used "
           "and names Colebrook-White and Manning. Neither is exclusively "
           "mandated, but Colebrook-White is the one given a mandatory input and "
           "the one from which the minimum gradient table is derived.")

    eq = D.next_eq()
    M.display(d, M.seq(
        R("V"), M.EQ, R("−2"), M.sqrt(M.seq(R("2"), R("g"), R("D"), R("S"))),
        M.func("log", M.sub(R(""), R("10"))),
        M.delim(M.seq(
            M.frac(M.sub(R("k"), UP("s")), M.seq(R("3.7"), R("D"))),
            M.PLUS,
            M.frac(M.seq(R("2.51"), R("ν")),
                   M.seq(R("D"), M.sqrt(M.seq(R("2"), R("g"), R("D"), R("S")))))),
            "[", "]")), number=eq)
    _params(d, [
        ["V", "pipe-full velocity", "m/s"],
        ["g", "acceleration due to gravity", "m/s²"],
        ["D", "pipe internal diameter", "m"],
        ["S", "hydraulic gradient", "m/m"],
        ["k s", "roughness — **1.5 mm, mandatory for all sizes and materials**", "m"],
        ["ν", "kinematic viscosity; 1.141 × 10⁻⁶ at 15 °C", "m²/s"]])

    D.h(d, 3, "Manning, where it is used")
    eq = D.next_eq()
    M.display(d, M.seq(R("v"), M.EQ, M.frac(R("1"), R("n")),
                       M.sup(M.sub(R("R"), UP("h")), M.frac(R("2"), R("3"))),
                       M.sup(R("S"), M.frac(R("1"), R("2")))), number=eq)
    _params(d, [
        ["n", "roughness coefficient; 0.009 to 0.011 for the plastics specified",
         "dimensionless"],
        ["R h", "hydraulic radius, area divided by wetted perimeter", "m"]])

    D.callout(d, "One equation in the guideline is dimensionally impossible.",
              "The relation between full-bore flow and velocity is printed as "
              "flow equals velocity divided by area, which yields units of "
              "reciprocal metre-seconds. It was verified at high resolution that "
              "the document really does print a division. Flow is velocity "
              "multiplied by area. Use the correct form and note the defect if "
              "the calculation is ever audited against the page.")
    _source(d, "G203 §4.2.1 p24 and §4.2.4 p25.")

    D.picture(d, os.path.join(IMG, "F6_gravity.png"), 15.5)
    D.fig_caption(d, "Sizing a gravity run. Both self-cleansing checks apply, and the steeper gradient governs.")

    D.h(d, 2, "9.3   Velocity and depth of flow")
    D.tab_caption(d, "Velocity and flow-depth criteria")
    D.table(d, ["Criterion", "Value", "Condition", "Force"],
            [["Self-cleansing velocity", "above 0.75 m/s", "at peak flow", "mandatory"],
             ["Preferred velocity", "0.90 m/s", "at peak flow", "advisory"],
             ["Maximum velocity", "3 m/s", "at design depth", "mandatory"],
             ["Flow depth, up to 350 mm", "d/D = 0.65", "at peak flow", "recommended"],
             ["Flow depth, above 350 mm", "d/D = 0.50", "at peak flow", "recommended"]],
            widths=[5.0, 3.6, 4.2, 3.7], font=9)

    D.p(d, "")
    D.p(d, "Two checks are required together, not as alternatives: the "
           "self-cleansing velocity, and the minimum tractive force. Where they "
           "disagree, the steeper gradient governs. At the head of a system, "
           "where the velocity cannot be reached at all, the tractive force "
           "method is the one that decides the gradient.")

    D.h(d, 2, "9.4   Tractive force")
    eq = D.next_eq()
    M.display(d, M.seq(R("τ"), M.EQ,
                       M.frac(M.seq(R("W"), R(" "), M.func("sin", R("θ"))),
                              M.seq(R("p"), R(" "), R("L")))), number=eq)
    _params(d, [
        ["τ", "tractive tension, or boundary shear stress", "Pa"],
        ["W", "weight of fluid", "N"],
        ["θ", "angle of the pipe to the horizontal", "degrees"],
        ["p", "wetted perimeter", "m"],
        ["L", "length of pipe", "m"]])

    eq = D.next_eq()
    M.display(d, M.seq(M.sub(R("S"), UP("min")), M.EQ, R("K"),
                       M.sup(R("τ"), R("1.23")),
                       M.sup(R("Q"), R("−0.461"))), number=eq)
    D.p(d, "The coefficient depends on the units of flow: 2.33 × 10⁻⁴ where "
           "flow is in cubic metres per second, or 5.5 × 10⁻³ where it is in "
           "litres per second. The relation assumes a flow depth of 0.2 and a "
           "Manning roughness of 0.013 — the latter inconsistent with the "
           "roughness table for the plastic pipes actually specified.")

    D.callout(d, "This mandatory method cannot be completed from NWS documents.",
              "The guideline requires the tractive force check, gives the "
              "equation, and never states the required value of shear stress in "
              "pascals — not in the wastewater guideline's 201 pages, nor in the "
              "general guideline's 152. A value must be taken from the "
              "literature and agreed with NWS in writing. It must not be "
              "presented as though it came from the guideline.")

    D.p(d, "Both equations above exist in the source only as images. They cannot "
           "be found by searching the text of the PDF, which is worth knowing "
           "for anyone checking them.")
    _source(d, "G203 §4.2.2.1 p26-27.")

    D.h(d, 2, "9.5   Minimum gradients")
    D.p(d, "The guideline tabulates a minimum gradient against diameter, derived "
           "from Colebrook-White at a self-cleansing velocity of 0.75 m/s.")
    D.tab_caption(d, "Minimum sewer gradient by diameter")
    D.table(d, ["Diameter (mm)", "Minimum gradient (mm/m)",
                "Diameter (mm)", "Minimum gradient (mm/m)"],
            [["200", "5.00", "600", "1.25"],
             ["250", "3.75", "700", "1.00"],
             ["315", "2.70", "800", "0.85"],
             ["400", "2.05", "900 and above", "0.75"],
             ["500", "1.55", "", ""]],
            widths=[4.1, 4.2, 4.1, 4.2], font=9)

    D.callout(d, "These gradients are full-bore values, and that matters.",
              "Reproducing all nine rows with Colebrook-White at the mandated "
              "roughness returns 0.75 m/s running full, to within two per cent. "
              "But the velocity requirement is stated at peak flow, not full "
              "bore. At the mandated flow depth of 0.65 a pipe reaches about "
              "0.82 m/s and passes; at 0.50 it reaches exactly 0.75 and has no "
              "margin at all; at a depth of 0.20 it manages 0.46 m/s and fails. "
              "Laying to this table is therefore not by itself compliance, and "
              "in the opening years every pipe in the network sits below the "
              "threshold. That is what the maintenance washing schedule exists "
              "to cover.")
    _source(d, "G203 §4.3 p29; the part-full check is a project calculation.")

    D.h(d, 2, "9.6   Cover, depth and manholes")
    D.p(d, "The minimum depth is 1.3 m to the crown of the pipe. Where that "
           "cannot be achieved, concrete protection is required and the minimum "
           "cover over pipe and protection together becomes 0.5 m.")

    D.callout(d, "The maximum depth rule is widely mis-stated.",
              "The guideline recommends a maximum cover of approximately 10 to "
              "12 metres. It is a recommendation, not a limit; it refers to "
              "cover, not invert depth; and exceeding it is permitted, with the "
              "consequence being a mandatory consultation with pipe "
              "manufacturers. What obliges a pumping station is excavation cost "
              "becoming prohibitive, and no depth figure is attached to that "
              "clause.")

    D.tab_caption(d, "Maximum spacing between manholes")
    D.table(d, ["Pipe diameter (mm)", "Maximum spacing (m)"],
            [["200 to 315", "100"], ["350 to 900", "120"],
             ["1000 to 1400", "150"], ["above 1400", "200"]],
            widths=[8.2, 8.3], font=9.5)
    D.p(d, "")
    D.p(d, "Any departure from this spacing needs NWS approval in advance. "
           "Manholes are required at every change of gradient, every change of "
           "diameter, every junction and the end of each lateral. A backdrop is "
           "required where invert levels differ by more than 600 mm, and is to "
           "be built outside the manhole.")

    D.callout(d, "No inlet may meet the flow at less than 90 degrees.",
              "The rule is stated twice in mandatory voice. It is a common "
              "source of non-compliance in automated layouts, because a "
              "geometrically convenient junction is often a hydraulically bad "
              "one.")
    _source(d, "G203 §4.4 p29-30 and §4.6.3 p33.")

    D.h(d, 2, "9.7   Lengths and materials")
    D.p(d, "A lateral sewer has a maximum length of 45 m. A property connection "
           "should not exceed 50 m, so that it can be maintained; beyond that a "
           "manhole is added. Minimum sizes are 160 mm outside diameter for "
           "riders and property connections, and 200 mm for laterals and main "
           "sewers.")
    _source(d, "G203 §3.2 p17, Table 5 p18 and Table 6 p22.")


def build_part1(d):
    s3_data(d)
    s4_population(d)
    s5_demand(d)
    s6_wastewater(d)
    s7_time(d)
    s8_peak(d)
    s9_gravity(d)
