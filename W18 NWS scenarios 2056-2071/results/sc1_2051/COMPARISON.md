# SC1 designed for 2051: SewerGEMS against my own design, and the 2051 pipes in 2056

- **Sizes:** same on 19,056 of 19,083 pipes (99.86 %); different on 27 (2.21 km).
  O2-P689 own DN1400 / SewerGEMS DN1200, O2-P686 own DN1400 / SewerGEMS DN1200, O2-P694 own DN1400 / SewerGEMS DN1200, O2-P674 own DN1400 / SewerGEMS DN1200, O2-P684 own DN1400 / SewerGEMS DN1200, O2-P680 own DN1400 / SewerGEMS DN1200, O2-P683 own DN1400 / SewerGEMS DN1200, O2-P687 own DN1400 / SewerGEMS DN1200, O2-P672 own DN1400 / SewerGEMS DN1200, O2-P678 own DN1400 / SewerGEMS DN1200, O2-P676 own DN1400 / SewerGEMS DN1200, O2-P679 own DN1400 / SewerGEMS DN1200
  SewerGEMS used DN1200, in its catalogue but on no 2056 pipe, so missing from the catalogue the own design read off the 2056 design. Rerun with it added (not blind):
  2051: same size on 19,083 of 19,083 pipes (4 passes).
  2056: same size on 19,083 of 19,083 pipes (4 passes).
- **SewerGEMS 2051 against its 2056 design:** 689 pipes change size (689 smaller, 0 larger), 59.2 km; above DN200 1,750 pipes, 144.4 km (2056: 1,847, 151.8 km).
- **Design flows 2051:** within 0.1 % on 100.0 % of pipes, largest 0.004 %.

| design | condition | stations | new | joined by gravity | above DN200 under 0.75 m/s at 2031 | manholes > 12 m | deepest |
|---|---|---|---|---|---|---|---|
| SewerGEMS design | C0_as_designed | 23 | 0 | 0 | 122.3 of 144.4 km (84.7 %) | 318 | 22.64 m |
| SewerGEMS design | C1_limit_0.50pc | 25 | 7 | 5 | 19.1 of 144.3 km (13.2 %) | 228 | 16.49 m |
| own design | C0_as_designed | 23 | 0 | 0 | 124.5 of 144.4 km (86.3 %) | 318 | 22.64 m |
| own design | C1_limit_0.50pc | 25 | 7 | 5 | 19.1 of 144.3 km (13.2 %) | 229 | 16.49 m |
| SewerGEMS design 2056 (for reference) | C1_limit_0.50pc | 25 | 7 | 5 | 26.4 of 151.7 km (17.4 %) | 235 | 16.47 m |
- C0_as_designed: 2031 velocity above DN200, own (Colebrook-White at normal depth) minus SewerGEMS: median +0.000, 5-95 % -0.001 to +0.001 m/s; the 0.75 m/s verdict differs on 27 pipes, 2.2 km.
- C1_limit_0.50pc: 2031 velocity above DN200, own (Colebrook-White at normal depth) minus SewerGEMS: median +0.000, 5-95 % -0.001 to +0.001 m/s; the 0.75 m/s verdict differs on 0 pipes, 0.0 km.

**The 2051 pipes in 2056** (SewerGEMS analysis SC1-2051-at-2056, as designed, no steepening): 601 pipes, 51.8 km over the d/D limit (0.65 up to DN355, 0.50 above), 560 of them among the 689 pipes that came out smaller than the 2056 design; 0 running full; largest d/D 0.75 (O3-P2009, DN200); highest velocity 1.07 m/s.
  By size: DN200 121.0 pipes 9.3 km (d/D up to 0.75); DN250 60.0 pipes 5.5 km (d/D up to 0.71); DN280 52.0 pipes 4.4 km (d/D up to 0.70); DN315 90.0 pipes 7.5 km (d/D up to 0.73); DN355 57.0 pipes 5.2 km (d/D up to 0.69); DN450 48.0 pipes 3.8 km (d/D up to 0.53); DN500 14.0 pipes 1.2 km (d/D up to 0.52); DN560 47.0 pipes 4.7 km (d/D up to 0.52); DN710 22.0 pipes 1.6 km (d/D up to 0.53); DN800 27.0 pipes 3.1 km (d/D up to 0.52); DN900 30.0 pipes 2.7 km (d/D up to 0.52); DN1200 3.0 pipes 0.2 km (d/D up to 0.51); DN1400 19.0 pipes 1.5 km (d/D up to 0.51); DN1600 11.0 pipes 0.9 km (d/D up to 0.50)
