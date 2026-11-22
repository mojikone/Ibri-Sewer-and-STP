# Findings of the gates (dated, newest first)

- 2026-11-21 **Gate P0 passed.** The ported W18 chain (design, split, self-cleansing, naming, products), run from the frozen fixtures in a work root, reproduces W18 SC1-2056 in every output file to 1e-9: exports, cuts, joins, named network, stations, quantities, summaries. Whole chain 38 s (design and split 12 s); W18's git status unchanged by the run.
- 2026-11-21 From scratch (no seeded cuts) SC1-2056 converges in 3 passes and 58 s to exactly the same result: the chain does not depend on its starting state (spec risk 3 closed).
- 2026-11-21 `named/links.csv` rows come out in a different order on each run (Python's per-process hash seed in the naming step); the content by key is identical, so it is compared by key.
- 2026-11-21 **In-process engine** (flows, sizing, normal depth) equals W18 on every pipe of all 12 cases: flows and velocities to 1e-9, identical sizes, same number of sizing passes. Analysis of the whole 19,083-pipe network: 0.033 s.
- 2026-11-21 **Gate P1A passed.** The whole chain for all 12 cases equals W18 at the spec's tolerances; SC1-2056 against SewerGEMS's saved export: 19,078 pipes, 100 % within 0.1 % (largest 0.0036 %), 0 over the d/D limit, dv 5-95 % -0.0008/+0.0006 m/s, 9.01 km under 0.75 m/s both. 12 cases 67 s in parallel. No new SewerGEMS run.
