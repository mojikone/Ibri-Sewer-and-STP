# W18 R5: scenario SC1 (STP-1 at O1) designed for 2056 and checked at 2031 on the R4 loads (job 072: loads of
# 2026-11-17 - growth plots 200-3,000 m2 any zoning, capacity = 2026 population + growth plots x properties per plot
# x 4.8 - as unit loads peaked by the Extreme Flow Setup, infiltration 720 L/km/day). As job 070 (R2, on R0's loads),
# whose exports were archived to out\w18\scen\SC1-2056_R2 on the host first. Transfers: py/make_transfers.py SC1 2056
# 2031 on R4's outfall flows (same 20 routes as R2; 2056 469 m3/d less in all).
$name = 'SC1'; $dy = '2056'; $checks = @('2031')
$src = 'C:\IbriWork\W18\IBRI_W18_R4.stsw'; $dst = 'C:\IbriWork\W18\IBRI_W18_R5_SC1_2056.stsw'
. \\VBOXSVR\VBOX\bridge\lib\build_scenario.ps1
