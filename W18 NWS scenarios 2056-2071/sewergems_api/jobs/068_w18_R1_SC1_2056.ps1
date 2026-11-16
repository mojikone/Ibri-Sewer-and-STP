# W18 R1: scenario SC1 (STP-1 at O1) designed for 2056, checked at 2031 (engineer's design-year rule, 2026-11-16).
# Loads: job 067 (R0, every plot carried at a manhole with a load row; provisional until the engineer sets the
# no-network cut-off). Transfers: py/make_transfers.py SC1 2056 2031. Replaces 061, whose path lost a backslash.
$name = 'SC1'; $dy = '2056'; $checks = @('2031')
$src = 'C:\IbriWork\W18\IBRI_W18_R0.stsw'; $dst = 'C:\IbriWork\W18\IBRI_W18_R1_SC1_2056.stsw'
. \\VBOXSVR\VBOX\bridge\lib\build_scenario.ps1
