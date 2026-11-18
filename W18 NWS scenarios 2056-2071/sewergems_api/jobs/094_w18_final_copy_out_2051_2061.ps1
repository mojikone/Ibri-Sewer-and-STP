# W18 final design (2026-11-18): copy the eight models of the 2051 and 2061 designs (jobs 086-093, IBRI_SC#-2051/2061_final)
# with their results to the bridge (out\w18\final_models\), for the deliverables package. Copy only: nothing in
# C:\IbriWork changes, backups skipped.
$out = '\\VBOXSVR\VBOX\bridge\out\w18\final_models'; New-Item -ItemType Directory -Force $out | Out-Null
$log = New-Object IO.StringWriter
Get-ChildItem 'C:\IbriWork\W18\final' | Where-Object { ($_.Name -like 'IBRI_SC?-2051_final*' -or $_.Name -like 'IBRI_SC?-2061_final*') -and $_.Name -notlike '*.bak' } | ForEach-Object {
  Copy-Item $_.FullName $out -Force
  $log.WriteLine(('  {0}  {1:n1} MB' -f $_.Name, ($_.Length / 1MB)))
}
$log.WriteLine('== copied to ' + $out)
$log.ToString()
