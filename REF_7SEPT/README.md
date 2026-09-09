# REF_7SEPT — the reference network of 7 September evening

The engine and outputs of commit `3897c0e` (W13, 2026-09-07 21:55), the run the engineer
called constructable: the long straight streets as whole sub-mains, one outlet per street,
the west settlement converging on the south-west corner and leaving along NAMA's corridor to
the works. Kept in its own folder so nothing later writes into it. `inputs/Main_Pipe_7sept.shp`
is the main pipe as it was drawn then, recovered from the drawing's `A_MAIN_PIPE` layer,
because the client copy has since been redrawn. Rerun with `python py/run_stage_a.py` from
`py/`; it writes to this folder only. Every later layout is measured against this one.
