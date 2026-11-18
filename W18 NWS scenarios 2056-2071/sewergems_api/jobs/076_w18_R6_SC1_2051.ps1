# W18 R6 (engineer, 2026-11-18, after the team's review: "check if we go with 0.5% and design SC1 with 2051 flow, how
# many outfalls (pumps) and what length (and %) of pipes won't reach self cleansing"): scenario SC1 (STP-1 at O1)
# designed for 2051, checked at 2031 (self-cleansing) and at 2056 (what the 2051 pipes carry in the next design year).
# Same builder and the same R4 loads as job 074 (R5, SC1-2056); new file R6, R4 and R5 untouched.
# Transfers: py/make_transfers.py SC1 2051 2031 2056 on R4's outfall flows (same 20 routes; plant 929.7 L/s in 2051).
$name = 'SC1'; $dy = '2051'; $checks = @('2031', '2056')
$src = 'C:\IbriWork\W18\IBRI_W18_R4.stsw'; $dst = 'C:\IbriWork\W18\IBRI_W18_R6_SC1_2051.stsw'
. \\VBOXSVR\VBOX\bridge\lib\build_scenario.ps1
