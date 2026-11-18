# W18 final design (engineer, 2026-11-18): SC1 designed for 2056 at 0.75 %, built from R4 with the own design;
# gravity joins carried as transfers (job 080: the API-created join sewers were not solved).
$case = 'SC1-2056'; $name = 'SC1'; $dy = '2056'; $checks = @('2031', '2036')
$src = 'C:\IbriWork\W18\IBRI_W18_R4.stsw'; $dst = 'C:\IbriWork\W18\final\IBRI_SC1-2056_final.stsw'
$in = '\\VBOXSVR\VBOX\bridge\in\final\SC1-2056'
. \\VBOXSVR\VBOX\bridge\lib\build_final.ps1
