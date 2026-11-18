# W18 final design (2026-11-18): copy the four final models (jobs 081-084, IBRI_SC#-2056_final) and their results to the
# bridge (out\w18\final_models\), ready for the deliverables. Copy only: nothing in C:\IbriWork changes, backups skipped.
$out = '\\VBOXSVR\VBOX\bridge\out\w18\final_models'; New-Item -ItemType Directory -Force $out | Out-Null
$log = New-Object IO.StringWriter
Get-ChildItem 'C:\IbriWork\W18\final' -Filter 'IBRI_SC*-2056_final*' | Where-Object { $_.Name -notlike '*.bak' } | ForEach-Object {
  Copy-Item $_.FullName $out -Force
  $log.WriteLine(('  {0}  {1:n1} MB' -f $_.Name, ($_.Length / 1MB)))
}
$log.WriteLine('== copied to ' + $out)
$log.ToString()
