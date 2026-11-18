# W18 final design (engineer, 2026-11-18): SC3 designed for 2061 at 0.75 %, the SewerGEMS check of the own design for the
# year after the base 2056; built from R4 as jobs 081-084, gravity joins carried as transfers.
$free = (Get-PSDrive C).Free / 1GB; 'C: free {0:n1} GB' -f $free
if ($free -lt 2) { 'FAILED: less than 2 GB free on C:'; exit 1 }
$case = 'SC3-2061'; $name = 'SC3'; $dy = '2061'; $checks = @('2031', '2036')
$src = 'C:\IbriWork\W18\IBRI_W18_R4.stsw'; $dst = 'C:\IbriWork\W18\final\IBRI_SC3-2061_final.stsw'
$in = '\\VBOXSVR\VBOX\bridge\in\final\SC3-2061'
. \\VBOXSVR\VBOX\bridge\lib\build_final.ps1
