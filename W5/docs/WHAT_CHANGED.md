# W5 — what changed, in plain words

W4 built the design pipeline. W5 puts in the rules we agreed on 18–19 August: better road
data, no pipes on roads we cannot dig up, house connections drawn properly, and property
counts taken from real electricity accounts instead of a guess.

Words used below that have no simple alternative are explained in the footnotes.

---

## The headline numbers

| | W4 | W5 | why it moved |
|---|---|---|---|
| Chambers[^1] | 1,655 | **1,744** | more small streets kept, but bends now handled properly |
| Sewer length | 89.5 km | **78.4 km** | dual carriageways (8.0 km), roundabouts and turning links removed |
| Properties served | 2,987 plots (1 each) | **3,017 plots, 4,226 properties** | counted from electricity accounts |
| Average flow at the outfall[^2] | 3,070 m³/day | **3,620 m³/day** | more properties, even though each person now counts 5 not 6 |
| Peak flow | 83 L/s | **96 L/s** | same reason |
| Deepest chamber | 13.4 m | 20.1 m | inside a pumping-station pocket, so it will be pumped, not dug |
| Pumping station spots | 2 | **5** | biggest one now serves 125 properties |
| Checks failing | 2 | **3** | see below |

---

## What the road work did

The road file we now use came from your colleague and carries a `dual` column. That one
column did more than any rule I could have written:

| Step | Result |
|---|---|
| Dual carriageways dropped (`dual` = 1) | 101 lines, **8.0 km** — no pipe on them at all, not even the trunk |
| Roundabouts dropped | 12 rings; 69 more rings were **kept** because plots sit inside them, so they are blocks, not roundabouts |
| Turning links and slip roads dropped | 83 lines |
| Straight streets joined back into one line | 107 joins |
| Dead ends serving nobody | 4 dropped |

Everything removed is in `shp/W5_corridors.shp` with a reason in the `EXCL_RSN` column, so
you can look at each one and put it back if I got it wrong.

One correction worth knowing: my first test for a turning link asked "is there a plot
within 40 m?" In a town the answer is always yes, so it never fired. It now asks the right
question — "is this line the closest one to any plot?" — and drops it only if nobody needs
it and the way round is less than three times longer.

## What the house connections do now

Before, the connection ran from the middle of the plot to whichever chamber was nearest in
a straight line, which drew pipes across blocks and through other plots. Now:

- the plot is projected out to the **nearest sewer line**, so the connection is a short
  spur from the plot edge to the road
- the plot loads **the pipe it faces**, not a chamber across the block
- up to **3 houses share one rider**[^3]; a house on its own gets its own line
- **522 empty plots get a capped stub-out**, ready for when they are built
- the level check uses the pipe level **at the joining point**, worked out along the pipe

They are in **three separate files** so SewerGEMS never reads them as sewers:
`W5_tertiary_connections.shp` (2,495 spurs), `W5_tertiary_riders.shp` (963),
`W5_tertiary_stubouts.shp` (522).

## What the electricity accounts changed

33,970 accounts, each one a property. In the test area, 3,885 accounts sit on 1,322 plots.

- properties per plot is now **counted**, not assumed — average **1.4** across the area
- account type tells us what kind of load it is, so shops and offices are identified
  instead of being estimated as a flat percentage
- people per property set to **5**, as you decided
- **30 farm plots have houses on them** and are now loaded, following the doctrine change

## Bends

- a turn sharper than 30° gets **one chamber at the corner**
- a long sweeping bend gets a chamber roughly every 45° of turn, **never more than 3**
- **18 corner chambers** sit closer than 2 m to a plot — these are flagged for you to nudge
  on the drawing, not redesigned automatically

## The three checks still failing

| Check | Count | What it means |
|---|---|---|
| Inlet angle | 300 of 1,743 | pipes arriving at a chamber at a sharp angle. Real rule (G203 p30), needs the junction layout work in W6 |
| Branch start clearance | 2 of 582 | two branches start slightly under 10 m from another chamber |
| Connection longer than 50 m | 240 of 3,017 | plots far from any usable street — mostly ones that used to face a dual carriageway. Each needs an intermediate chamber or a local answer |

Nothing here changes the hydraulics: pipe sizing, gradients, cover and drop rules are the
same as W4, which passed the Table 11 reproduction test.

---

[^1]: Chamber = manhole, the access pit on the sewer.
[^2]: Outfall = the point where the whole network discharges; here it is the lowest road
      point on the boundary.
[^3]: Rider = the small pipe that runs along the plot frontage and collects a few houses
      before joining the street sewer.
