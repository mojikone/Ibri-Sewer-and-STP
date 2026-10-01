# In which year does the network reach 0.75 m/s? — note for the client discussion (W17, 2026-10-01)

**Short answer: in no year does every pipe reach 0.75 m/s at its peak, even if pipes may be laid as steep as 4 %.
Whether a pipe can be self-cleansing by velocity depends on how many houses drain into it, not on the year.**

## The question, read as the engineer proposed

*With head pipes allowed up to the client's 4 % maximum, in which year can all pipes reach the self-cleansing velocity
of 0.75 m/s at peak flow (G203 p26)?*

For every pipe and every year we computed the gradient at which that year's peak flow reaches 0.75 m/s in the pipe's own
diameter (Colebrook-White, ks 1.5 mm, ν 1.141 × 10⁻⁶ m²/s, G203 p24–p25), and counted the pipes for which that gradient
is 4 % or less. Flows are the design flows of the network (option S1; a pipe's own flow is the same in every option).

| Year | Pipes that can reach 0.75 m/s within 4 % | Share of pipes | Share of length | Head pipes |
|---|---|---|---|---|
| 2030 | 5,562 | 29 % | 29 % | 21 of 3,612 |
| 2040 | 6,304 | 33 % | 33 % | 23 of 3,612 |
| 2050 | 6,993 | 37 % | 37 % | 26 of 3,612 |
| 2055 | 7,347 | 39 % | 39 % | 29 of 3,612 |
| 2060 | 7,746 | 41 % | 41 % | 34 of 3,612 |
| 2070 (saturation) | 8,822 | 46 % | 47 % | 38 of 3,612 |

**10,261 pipes (54 %, 790 km) never can, not even at saturation.** All are DN200, and 3,574 of them are head pipes.
Their saturation peak is a median 0.33 L/s.

## Why: the threshold is about 32 houses

A DN200 needs **0.93 L/s** of peak flow to reach 0.75 m/s at 4 % (at 1 % it needs about 4.5 L/s). With the Peltier peak
factor (G201 p72) that is an average of 0.27 L/s — **about 32 houses** at the average occupancy. A street pipe that will
never serve 32 houses upstream will never be self-cleansing by velocity, whatever the year and whatever gradient up to 4 %.
As the land fills, pipes cross that threshold one by one, which is why the share grows from 29 % to 46 % and then stops:
at saturation the number of houses on each street is fixed by the plot layout.

## What the guideline already provides for this

G203 p27: *"At the head of the sewerage systems, the flow velocity based on the minimum self-cleansing may not be
attainable. In these circumstances, the minimum pipe gradient for the sewer shall be calculated based on the hydraulic
design approach of minimum tractive force."* With the tractive force at 1 Pa (Mara, Sleigh and Taylor, G203 p27), the
gradient a head pipe needs is a median 2.5 % in 2030 and 1.3 % in 2070, and it exceeds 4 % only below 0.0135 L/s — pipes
carrying little more than their own infiltration (372 head pipes at saturation). And G203 §4.2.6: *"During early
development phases ... the operator should proceed to more frequent inspections and cleansings during this period."*

## Ideas to put to the client

1. **Answer the question as a curve, not a year:** the table above — the share of the network that is self-cleansing
   by velocity, year by year, at gradients up to 4 %.
2. **Three classes per pipe, and a map of them:** (a) self-cleansing by velocity from a given year (coloured by that
   year); (b) self-cleansing by tractive force at 1 Pa within 4 %; (c) neither — the flushing list. The map gives the
   operator the cleaning programme §4.2.6 asks for, shrinking as the land fills.
3. **Decisions the client has to take:** the year from which self-cleansing is to be guaranteed (2030 low case as in our
   design basis, or a later year), the tractive stress (1 Pa or another value), and whether 4 % is a maximum for all
   pipes or only for head pipes. Steeper pipes mean a deeper network and more pumping, so the choice has a cost we can
   quantify once it is made.
4. **What does not help:** a smaller head pipe would reach 0.75 m/s at lower flows, but G203 Table 6 sets OD200 as the
   minimum main sewer.

Source data: `W17/results/S1/selfcleansing_year.md`, `selfcleansing_year_by_pipe.csv`, `selfcleansing_info.md`;
scripts `W17/py/selfcleansing_info.py`, `selfcleansing_year.py`.
