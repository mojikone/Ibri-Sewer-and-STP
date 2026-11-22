# W19 sections, step 4 (probe, on a copy): the barrel count and solver of Block 04, then after running the first scenario,
# how SewerGEMS's normal and critical depth result fields (GVFConduitResults_NormalDepth, _CriticalDepth) are filled:
# time-variant or not, how many steps, the values at the first step and at the step of peak flow (storage units, ft).
$src = '\\VBOXSVR\Win10_shared_folder\SewerGEMS Block 04 11102026\SewerGEMS Block 04.stsw'
. \\VBOXSVR\VBOX\bridge\lib\load.ps1
$out = "\\VBOXSVR\VBOX\bridge\out\w19\probe_gvf.txt"
$dir = "C:\IbriWork\W19\src\probe_gvf"; New-Item -ItemType Directory -Force $dir | Out-Null
Copy-Item -LiteralPath $src -Destination "$dir\model.stsw" -Force
Copy-Item -LiteralPath "$src.sqlite" -Destination "$dir\model.stsw.sqlite" -Force
$log = New-Object IO.StringWriter
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open("$dir\model.stsw")
  $cs = @($m.Network.Conduits.Elements() | Select-Object -First 4)
  foreach ($c in $cs) {
    $i = $c.Input
    $vals = foreach ($p in 'NumberOfBarrels','AllowMultipleBarrels','MaximumBarrels','ConduitShape','ConduitRise','ConduitSpan','ManningsN','IsCulvert') { try { $p + '=' + $i.$p } catch { $p + '=ERR ' + $_.Exception.Message } }
    $log.WriteLine(("conduit {0}: {1}" -f $c.Label, ($vals -join '; ')))
  }
  $s = $m.DomainDataSet.ScenarioManager.Elements() | Select-Object -First 1
  $hs = $m.Scenarios.Element($s.Id)
  try { $log.WriteLine("scenario members: " + (($hs | Get-Member -MemberType Property | ForEach-Object Name) -join ', ')) } catch {}
  try { $o = $hs.Options; $log.WriteLine("options: " + (($o | Get-Member -MemberType Property | ForEach-Object { $_.Name + '=' + $o.($_.Name) }) -join '; ')) } catch { $log.WriteLine("options: " + $_.Exception.Message) }
  [Scen]::Run($m, $s.Id, $log)
  $dds = $m.DomainDataSet; $sc = $dds.ScenarioManager.Element($s.Id)
  $eng = 'DelawareProductEngine'; try { $e2 = $sc.GetActiveNumericalEngineTypeName('StormSewerResultRecordType'); if ($e2) { $eng = $e2 } } catch {}
  $fc = $dds.FieldManager.ResultFields($eng, 'GVFConduitResults', 3)
  foreach ($f in $fc) {
    if ($f.Name -notmatch 'NormalDepth$|CriticalDepth$') { continue }
    $log.WriteLine(("field {0} ({1}); time-variant {2}" -f $f.Name, $f.GetType().FullName, ($f -is [Haestad.Domain.IResultTimeVariantField])))
    foreach ($c in $cs) {
      try {
        if ($f -is [Haestad.Domain.IResultTimeVariantField]) {
          $n = 0; try { $n = $sc.TimeStepsCount } catch {}
          $v0 = $f.GetValue($c.Id, $s.Id, 0)
          $flows = @($c.Results.Flows()); $k = 0; $best = -1; for ($t = 0; $t -lt $flows.Count; $t++) { if ($flows[$t] -gt $best) { $best = $flows[$t]; $k = $t } }
          $vk = $f.GetValue($c.Id, $s.Id, $k)
          $log.WriteLine(("  {0}: steps {1}, flows {2}, peak step {3} flow {4}; value at 0 = {5}, at peak = {6}" -f $c.Label, $n, $flows.Count, $k, $best, $v0, $vk))
        } else { $log.WriteLine(("  {0}: {1}" -f $c.Label, $f.GetValue($c.Id))) }
      } catch { $log.WriteLine(("  {0}: ERR {1}" -f $c.Label, $_.Exception.Message)) }
    }
  }
  $log.WriteLine(("typed Flow() of {0}: {1}" -f $cs[0].Label, $cs[0].Results.Flow()))
  $m.Close()
} catch { $log.WriteLine('FAILED: ' + $_.Exception.ToString()) } finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
[IO.File]::WriteAllText($out, $log.ToString())
