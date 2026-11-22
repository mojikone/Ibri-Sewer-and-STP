# Clean-room statement

This application is a clean-room implementation. Its engines are written from published methods only: PAM-GUD-201,
-202 and -203 (Nama Water Services), Colebrook-White, Manning, the standard-step method for gradually varied flow,
Peltier and Merrimack peaking, the rational method, FHWA HEC-22, NRCS TR-55 and EPA SWMM 5 (public domain).
SewerGEMS's published documentation is used as a description of methods and is cited where used.

Bentley's binaries are never decompiled, disassembled, patched or inspected, and SewerGEMS's proprietary file formats
are never read directly. SewerGEMS is used only as the licensed product, through its documented OpenFlows API, inside
an offline virtual machine, to run models and export their results; those results are the black-box reference every
engine is checked against. Bentley's sample models and anything exported from them are kept out of this repository.
