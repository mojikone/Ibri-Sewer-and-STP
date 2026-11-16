# W18 R2: scenario SC1 (STP-1 at O1) designed for 2056, checked at 2031, on the FINAL loads (job 069: estates
# additive, growth on home-shaped plots inside the settlement boundaries, plots off the network not carried).
# Transfers: py/make_transfers.py SC1 2056 2031 after job 069. Overwrites the provisional exports in
# out\w18\scen\SC1-2056 (kept in results/SC1-2056_provisional).
$name = 'SC1'; $dy = '2056'; $checks = @('2031')
$src = 'C:\IbriWork\W18\IBRI_W18_R0.stsw'; $dst = 'C:\IbriWork\W18\IBRI_W18_R2_SC1_2056.stsw'
. \\VBOXSVR\VBOX\bridge\lib\build_scenario.ps1
