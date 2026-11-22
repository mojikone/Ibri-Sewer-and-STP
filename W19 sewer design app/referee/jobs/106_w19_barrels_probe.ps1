# W19 sections, step 3 (probe, on a copy, no run): the conduit inputs the typed API offers (looking for the number of
# barrels), the result methods of a conduit, and the conduit result fields of the engine (looking for normal and critical
# depth), so the section export can carry the barrel count and SewerGEMS's own normal depth.
$src = '\\VBOXSVR\Win10_shared_folder\SewerGEMS Block 04 11102026\SewerGEMS Block 04.stsw'
. \\VBOXSVR\VBOX\bridge\lib\load.ps1
$out = "\\VBOXSVR\VBOX\bridge\out\w19\probe_barrels.txt"
$dir = "C:\IbriWork\W19\src\probe_barrels"; New-Item -ItemType Directory -Force $dir | Out-Null
Copy-Item -LiteralPath $src -Destination "$dir\model.stsw" -Force
Copy-Item -LiteralPath "$src.sqlite" -Destination "$dir\model.stsw.sqlite" -Force
$log = New-Object IO.StringWriter
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open("$dir\model.stsw")
  $c = $m.Network.Conduits.Elements() | Select-Object -First 1
  $i = $c.Input
  $log.WriteLine("conduit " + $c.Label + " inputs:")
  foreach ($p in ($i | Get-Member -MemberType Property | ForEach-Object Name)) { try { $log.WriteLine("  {0} = {1}" -f $p, $i.$p) } catch { $log.WriteLine("  {0} = ?" -f $p) } }
  $log.WriteLine("result methods: " + ([B4]::ResultMethods([B4]::Res($c)) -join ', '))
  $s = $m.DomainDataSet.ScenarioManager.Elements() | Select-Object -First 1
  $tmp = New-Object IO.StringWriter
  [ResultFields]::Export($m, $s.Id, [int[]]@(), "$dir\rf.csv", $tmp)
  $log.WriteLine("conduit result fields (normal, critical, barrel, depth):")
  foreach ($l in ($tmp.ToString() -split "`n")) { if ($l -match 'engine|Normal|Critical|Barrel|Depth') { $log.WriteLine($l.TrimEnd()) } }
  $m.Close()
} catch { $log.WriteLine('FAILED: ' + $_.Exception.ToString()) } finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
[IO.File]::WriteAllText($out, $log.ToString())
