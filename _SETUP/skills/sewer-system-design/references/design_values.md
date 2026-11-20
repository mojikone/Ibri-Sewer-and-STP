# Design values and their sources

`p##` = PAM-GUD-203 (sewerage design); `G201 p##` = PAM-GUD-201 (demand and flows); `G202 p##` = PAM-GUD-202 (water and TSE).
Quote a value from the guideline page, not from memory or from this file. If a project has its own criteria register,
that governs.

**Type** says who owns the value:
- **G**: a guideline value.
- **D**: the engineer's or the client's decision, recorded with its date.
- **M**: a method assumption carried from earlier work, to confirm at the next stage.

## Gravity sewers

| Value | Use | Source | Type |
|---|---|---|---|
| Colebrook-White, ks 1.5 mm all sizes; ν 1.141e-6 m²/s (15 °C) | sizing, velocity, depth of flow | p24, p25, p28 | G |
| Self-cleansing 0.75 m/s at peak flow (0.90 preferred) | steepening target, audit | p26 | G |
| Which pipes and which year's peak the self-cleansing test uses (Ibri: above DN200, opening-year peak, rechecked five years on) | steepening and the design-year search | the client | D |
| Tractive force (Mara/Sleigh/Taylor) as the second self-cleansing test, "shall" | not used to set gradients at the concept stage (Ibri); record the departure for the client | p25–27 §4.2.2.1 | G, departure D |
| Maximum velocity 3.0 m/s at design depth | checked on every pipe | p27 | G |
| d/D at peak ≤ 0.65 for D ≤ 350 mm, ≤ 0.50 above (inside diameter: DN355, inside 313 mm, takes 0.65) | sizing limit | p27 Table 10 | G |
| Minimum gradient by size, mm/m: DN200 5.00 · 250 3.75 · 315 2.70 · 400 2.05 · 500 1.55 · 600 1.25 · 700 1.00 · 800 0.85 · ≥900 0.75 | laid gradient before steepening | p29 Table 11 | G |
| Tertiary slopes: property connection 3 %, rider and lateral 1 %, all at most 10 % | tertiary pipes only, never the street main | p18 Table 5 | G |
| Lateral at most 45 m, OD200 | tier definition | p22 Table 6, p17 | G |
| Construction tolerance 20 mm, no reverse gradient | margin on flat trunks | p29 §4.3.1 | G |
| Gradient limit when steepening (Ibri 0.75 %) | the steepest a pipe is laid | the engineer, after a 0.50 / 0.75 / 1.00 % study | D |
| One gradient per street run | constructable profiles | the engineer | D |
| Minimum cover 1.3 m to the crown (0.5 m only with concrete protection, measured above it) | head pipes, re-lay | p33 §4.6.3 | G |
| Cover at a wadi crossing 1.5 m, gravity and force main | crossings | p52 §8.2.4 | G |
| Maximum cover "approximately 10–12 m", recommended; the trigger for a station is excavation cost | the depth limit | p33 §4.6.3 | G |
| 12 m as a hard limit until a cost study exists | cut into a station | the engineer | D |
| Ibri's caps: 14.65 m for an added station or outfall, 16.5 m for any manhole, where that saves a station | station removal | the engineer, 2026-11-18 | D |
| Manhole spacing: DN200–315 100 m, 350–900 120 m, 1000–1400 150 m, above 1400 200 m | gravity joins; lift or pump | p30 Table 12 | G |
| Backdrop when the drop exceeds 600 mm, at most 2 m (beyond that a vortex shaft) | drops | p30 | G |
| No pipes or chambers in wadis or washout areas ("must be avoided") | routing | p30 §4.4.1, p33 | G |

## Flows

| Value | Use | Source | Type |
|---|---|---|---|
| Merrimack Qpdf = 2.65·Qadf^0.879 (Ml/d), for over 100 properties | peaking | G201 p71 §7.4.2 | G |
| Peltier PF = 1.5 + 1/√Qm (Qm in L/s), the alternative | peaking | G201 p72 | G |
| The model's table: Peltier to 1 L/s, Merrimack above, with a step row at 1.001 L/s | peaking, as SewerGEMS applies it | the model's Extreme Flow Setup | M |
| Infiltration, new networks 720 L/day per km | on the conduits; plant inflow | G201 p72 §7.4.3 | G |
| STP margin +10 % for new plants | plant capacity | G201 p73 §7.4.5; p65 Table 29 | G |
| TSE production 95 % of the plant inflow; network loss 10 % | TE supply | G201 p73 §7.4.6 | G |

## Pumping stations and force mains

| Value | Use | Source | Type |
|---|---|---|---|
| Types: Type 1 ≤100 L/s (1+1), Type 2 100–300 (2+1), Type 3 >300 (3+1) | station type | p40–41 Table 17 | G |
| Land: Type 1 50–100 m², Type 2 200–400 m², Type 3 ≥900 m² | land take | p43 Table 21 | G |
| Wet-well live volume V = 0.25·Q·T, Q one pump, T = 3600 / starts an hour (10 starts) → 90 × Q per duty pump | station size | p48 §7.8 | G |
| Force main velocity 1.0 m/s minimum (intermittent), 2.5 m/s maximum | duty and size | p50 | G |
| Force main gradients 1:500 rising, 1:300 falling, never below 1:750 | profiles | p50 §8.2.1 | G |
| Head-loss equation: Darcy-Weisbach, or Hazen-Williams for small diameters | head | G202 p104 | G |
| Hazen-Williams C 120, +10 % minor losses | head | Ibri's R7 method | M |
| Wet well 1.5 m below the incoming invert; discharge 0.3 m above the receiving invert, 3.0 m above the ground at a plant | static head | Ibri's R7 method | M |
| Wire-to-water efficiency 0.65 | power | Ibri's R7 method | M |
| Lift or pump: a lift's force main reaches a manhole within one Table 12 spacing; otherwise it is a pump | naming | the engineer | D |

## Design years

| Value | Use | Source | Type |
|---|---|---|---|
| Design horizon: completion + 25 years, or saturation | the design-year search | the project's terms of reference | D |
| Ibri: design 2051 / 2056 / 2061, 2056 (= 2031 + 25) adopted; self-cleansing at 2031, recheck 2036 | the 12 designs | the engineer and the client | D |
| Plant design horizon at least 15 years | plant phasing | p65 | G |
