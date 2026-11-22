# W19 sections, step 2 (probe, on a copy): the units the typed API reports in, and SewerGEMS's own conduit results after
# running the first scenario of the copy (flow, velocity, depths, normal and critical depth), for the app's section check.
$src = '\\VBOXSVR\Win10_shared_folder\SewerGEMS Block 04 11102026\SewerGEMS Block 04.stsw'
. \\VBOXSVR\VBOX\bridge\lib\load.ps1
$out = "\\VBOXSVR\VBOX\bridge\out\w19\probe_units.txt"
$dir = "C:\IbriWork\W19\src\probe_units"; New-Item -ItemType Directory -Force $dir | Out-Null
Copy-Item -LiteralPath $src -Destination "$dir\model.stsw" -Force
Copy-Item -LiteralPath "$src.sqlite" -Destination "$dir\model.stsw.sqlite" -Force
$log = New-Object IO.StringWriter
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open("$dir\model.stsw")
  $log.WriteLine("model members with Unit: " + (($m | Get-Member | Where-Object Name -match 'Unit' | ForEach-Object Name) -join ', '))
  try { $u = $m.Units; $log.WriteLine("Units members: " + (($u | Get-Member -MemberType Property | ForEach-Object Name) -join ', '))
        foreach ($p in ($u | Get-Member -MemberType Property | ForEach-Object Name)) { $o = $u.$p; $log.WriteLine(("  {0}: {1}" -f $p, (($o | Get-Member -MemberType Property | Where-Object Name -match 'Flow|Length|Velocity|Depth|Elevation|Diameter' | ForEach-Object { $_.Name + '=' + $o.($_.Name) }) -join '; '))) } } catch { $log.WriteLine("Units: " + $_.Exception.Message) }
  $s = $m.DomainDataSet.ScenarioManager.Elements() | Select-Object -First 1
  $m.SetActiveScenario($m.Scenarios.Element($s.Id))
  $t0 = Get-Date; [Scen]::Run($m, $s.Id, $log); $log.WriteLine(("ran scenario {0} '{1}' in {2:n0} s" -f $s.Id, $s.Label, ((Get-Date) - $t0).TotalSeconds))
  $k = 0
  foreach ($c in $m.Network.Conduits.Elements()) {
    if ($k -ge 6) { break }; $r = $c.Results; $i = $c.Input
    $vals = foreach ($n in 'Flow','Velocity','DepthIn','DepthOut','NormalDepth','CriticalDepth','FullFlowCapacity','Capacity') { try { $n + '=' + ($r.GetType().GetMethod($n, [Type[]]@()).Invoke($r, $null)) } catch { $n + '=?' } }
    $log.WriteLine(("conduit {0}: shape {1} rise {2} span {3} n {4} length {5} inverts {6}/{7}: {8}" -f $c.Label, $i.ConduitShape, $i.ConduitRise, $i.ConduitSpan, $i.ManningsN, $i.Length, $i.StartInvert, $i.StopInvert, ($vals -join '; ')))
    $k += 1
  }
  $m.Close()
} catch { $log.WriteLine('FAILED: ' + $_.Exception.ToString()) } finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
[IO.File]::WriteAllText($out, $log.ToString())
