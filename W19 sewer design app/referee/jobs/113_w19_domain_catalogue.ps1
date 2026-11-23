# W19 (2026-11-23): SewerGEMS's data model as the installed program declares it (element types, alternative fields,
# calculation options, support types, result fields), read through the API from a copy of a small model.
. \\VBOXSVR\VBOX\bridge\lib\load.ps1
$src = '\\VBOXSVR\VBOX\bridge\models\Pond_Mouj\Pond_Mouj.stsw'
$dir = 'C:\IbriWork\W19\src\catalogue'; New-Item -ItemType Directory -Force $dir | Out-Null
$out = '\\VBOXSVR\VBOX\bridge\out\w19\catalogue'; New-Item -ItemType Directory -Force $out | Out-Null
Copy-Item -LiteralPath $src -Destination "$dir\model.stsw" -Force
Copy-Item -LiteralPath "$src.sqlite" -Destination "$dir\model.stsw.sqlite" -Force
$log = New-Object IO.StringWriter
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open("$dir\model.stsw")
  [DomainCatalogue]::Run($m, $out, $log)
  $m.Close()
} catch { $log.WriteLine('FAILED: ' + $_.Exception.ToString()) } finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
[IO.File]::WriteAllText("$out\log.txt", $log.ToString())
$log.ToString()
