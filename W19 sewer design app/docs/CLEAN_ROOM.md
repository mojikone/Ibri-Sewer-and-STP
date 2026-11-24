# Clean-room statement

This application is a clean-room implementation. Its engines are written from published methods only: PAM-GUD-201,
-202 and -203 (Nama Water Services), Colebrook-White, Manning, the standard-step method for gradually varied flow,
Peltier and Merrimack peaking, the rational method, FHWA HEC-22, NRCS TR-55 and EPA SWMM 5 (public domain).
SewerGEMS's published documentation is used as a description of methods and is cited where used.

Bentley's binaries are never decompiled, disassembled, patched or inspected, and SewerGEMS's proprietary file formats
are never read directly. SewerGEMS is used only as the licensed product, through its documented OpenFlows API, inside
an offline virtual machine, to run models and export their results; those results are the black-box reference every
engine is checked against. Bentley's sample models and anything exported from them are kept out of this repository.

## Amendment, 2026-11-24 (the engineer's decision)

The engineer lifted the rule against reading SewerGEMS's model files ("now I am asking it. I am the rule"), after being
told that Bentley's licence may forbid reading its format; that risk is the engineer's. Since then
`sewerapp/io/sewergems_db.py` reads a model's `.stsw.sqlite` directly (read-only, SQLite's immutable mode), so a model
opens without SewerGEMS. The rest stands: Bentley's binaries are never decompiled, disassembled or patched, SewerGEMS
is still the referee for the engines through its API, and Bentley's sample models stay out of this repository.
The reader was checked against SewerGEMS's own API export of the Ibri SC1-2056 final model: all 23 scenarios, every
structure and pipe, levels, lengths, sizes and loads equal (`tests/general/test_sewergems_db.py`).

## Note, 2026-11-24 (v7): SewerGEMS's option lists

The names of SewerGEMS's option lists (inlet types, grate types, gutter shapes, headloss methods...) were listed from
the public enum types of the API assemblies in `D:\VBOX\bridge\refs` by a reflection-only load: names and values
only, the same metadata the compiler reads in `compile_check.ps1`; no code executed, nothing decompiled or
disassembled. The inlet equations come from FHWA HEC-22 (3rd ed.) and EPA SWMM 5.2's public-domain `inlet.c`
(docs/INLETS_HEC22.md).
