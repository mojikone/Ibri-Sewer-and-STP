# W18 R1: scenario SC1 (STP-1 at O1) designed for 2056, checked at 2031 (engineer's design-year rule, 2026-11-16).
# Needs job 060's year loads and the host's transfers (py/make_transfers.py SC1 2056 2031).
$name = 'SC1'; $dy = '2056'; $checks = @('2031')
$src = 'C:\IbriWork\W18\IBRI_W18_R0.stsw'; $dst = 'C:\IbriWork\W18\IBRI_W18_R1_SC1_2056.stsw'
. \VBOXSVR\VBOX\bridge\lib\build_scenario.ps1
