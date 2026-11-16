. \\VBOXSVR\VBOX\bridge\lib\load.ps1
# Which GvfCalculationType value means design? Which physical alternative does each S1 scenario use?
$log = New-Object IO.StringWriter
foreach ($asm in [AppDomain]::CurrentDomain.GetAssemblies()) {
  $ts = try { $asm.GetTypes() } catch { $_.Exception.Types | ? { $_ } }
  foreach ($t in $ts | ? { $_.IsEnum -and $_.Name -match 'Gvf.*Calc|CalculationType|CalcType' }) {
    $log.WriteLine("enum " + $t.FullName + ": " + (([Enum]::GetNames($t) | % { $_ + '=' + [int][Enum]::Parse($t, $_) }) -join ', ')) }
}
$work = 'C:\IbriWork\scratch_calc'; New-Item -ItemType Directory -Force $work | Out-Null
Copy-Item 'C:\IbriWork\W17\IBRI_W17_R6.stsw', 'C:\IbriWork\W17\IBRI_W17_R6.stsw.sqlite' $work -Force
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open("$work\IBRI_W17_R6.stsw")
  $sm = $m.DomainDataSet.ScenarioManager
  foreach ($id in 279744, 279800, 279801, 279805) {
    $s = $sm.Element($id)
    $log.WriteLine(("scenario {0} '{1}': physical {2} (local {3}), sanitary {4}, calc {5}" -f $id, $s.Label, $s.AlternativeID('Physical'),
      $s.IsAlternativeLocal($m.DomainDataSet.DomainDataSetType().AlternativeType('Physical').Id), $s.AlternativeID('SanitaryLoading'), $s.CalculationOptionsID('DelawareProductEngine')))
  }
  $com = $sm.CalculationOptionsManager('DelawareProductEngine')
  foreach ($n in 'GvfCalculationType', 'CalculationType', 'TimeAnalysisType') { $f = $com.CalculationOptionsField($n); $log.WriteLine("$n : 31=" + $f.GetValue(31) + "  279786=" + $f.GetValue(279786)) }
  $pt = $m.DomainDataSet.DomainDataSetType().AlternativeType('Physical').Id
  $c = $m.Network.Conduits.Elements() | ? { $_.Label -eq 'O9-P715' }
  foreach ($alt in 6, 279787) { $log.WriteLine("O9-P715 size in physical $alt : " + $m.DomainDataSet.FieldManager.AlternativeField('CatalogPipeType_CatalogPipeSize', $pt, 3, $alt).GetValue($c.Id)) }
  foreach ($id in 279800, 279801, 279805) { $m.SetActiveScenario($m.Scenarios.Element($id)); $log.WriteLine("O9-P715 typed Size with active $id : " + $c.Input.Size) }
  $m.Close()
} catch { $log.WriteLine('FAILED: ' + $_.Exception.ToString()) } finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
$log.ToString()
