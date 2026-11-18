# W18 R5 (engineer, 2026-11-18: "include the SewerGEMS model" in the zip with the QGIS project, the plot layers and the
# SC1 conditions): copy the SC1 model IBRI_W18_R5_SC1_2056 (job 074) and its results to the bridge for the deliverable
# zip (out\w18\model_R5\). Copy only: the model is not opened, nothing in C:\IbriWork changes, backups (.bak) skipped.
$out = '\\VBOXSVR\VBOX\bridge\out\w18\model_R5'; New-Item -ItemType Directory -Force $out | Out-Null
$log = New-Object IO.StringWriter
Get-ChildItem 'C:\IbriWork\W18' -Filter 'IBRI_W18_R5_SC1_2056*' | Where-Object { $_.Name -notlike '*.bak' } | ForEach-Object {
  Copy-Item $_.FullName $out -Force
  $log.WriteLine(('  {0}  {1:n1} MB' -f $_.Name, ($_.Length / 1MB)))
}
$log.WriteLine('== copied to ' + $out)
$log.ToString()
