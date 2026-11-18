# W18 R6 (engineer, 2026-11-18: SC1 designed for 2051, job 076): copy the model IBRI_W18_R6_SC1_2051 and its results
# to the bridge (out\w18\model_R6\), ready for a package. Copy only: the model is not opened, nothing in C:\IbriWork
# changes, backups (.bak) skipped.
$out = '\\VBOXSVR\VBOX\bridge\out\w18\model_R6'; New-Item -ItemType Directory -Force $out | Out-Null
$log = New-Object IO.StringWriter
Get-ChildItem 'C:\IbriWork\W18' -Filter 'IBRI_W18_R6_SC1_2051*' | Where-Object { $_.Name -notlike '*.bak' } | ForEach-Object {
  Copy-Item $_.FullName $out -Force
  $log.WriteLine(('  {0}  {1:n1} MB' -f $_.Name, ($_.Length / 1MB)))
}
$log.WriteLine('== copied to ' + $out)
$log.ToString()
