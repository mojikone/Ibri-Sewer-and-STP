# List the help files shipped with SewerGEMS and copy them to the bridge (read-only on the install).
$roots = 'C:\Program Files (x86)\Bentley\SewerGEMS', 'C:\Program Files\Bentley\SewerGEMS', 'C:\ProgramData\Bentley'
$hits = foreach ($r in $roots) { if (Test-Path $r) { Get-ChildItem $r -Recurse -Include *.chm, *.pdf, *.hlp, *.htm, *.html -ErrorAction SilentlyContinue } }
$hits | Group-Object DirectoryName | ForEach-Object { "{0,6} files  {1}" -f $_.Count, $_.Name }
$dst = '\\VBOXSVR\VBOX\bridge\help'; New-Item -ItemType Directory -Force $dst | Out-Null
$hits | Where-Object { $_.Extension -in '.chm', '.pdf' } | ForEach-Object { Copy-Item $_.FullName $dst -Force; "copied {0} ({1:n0} bytes)" -f $_.Name, $_.Length }
