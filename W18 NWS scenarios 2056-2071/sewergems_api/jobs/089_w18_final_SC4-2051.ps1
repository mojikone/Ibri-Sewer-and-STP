# W18 final design (engineer, 2026-11-18): SC4 designed for 2051 at 0.75 %, the SewerGEMS check of the own design for the
# year before the base 2056; built from R4 as jobs 081-084, gravity joins carried as transfers.
$free = (Get-PSDrive C).Free / 1GB; 'C: free {0:n1} GB' -f $free
if ($free -lt 2) { 'FAILED: less than 2 GB free on C:'; exit 1 }
$case = 'SC4-2051'; $name = 'SC4'; $dy = '2051'; $checks = @('2031', '2036')
$src = 'C:\IbriWork\W18\IBRI_W18_R4.stsw'; $dst = 'C:\IbriWork\W18\final\IBRI_SC4-2051_final.stsw'
$in = '\\VBOXSVR\VBOX\bridge\in\final\SC4-2051'
. \\VBOXSVR\VBOX\bridge\lib\build_final.ps1
