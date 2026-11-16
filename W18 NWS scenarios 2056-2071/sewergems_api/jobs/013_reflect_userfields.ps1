. \\VBOXSVR\VBOX\bridge\lib\load.ps1
function Sig($t) { $all = @($t) + $t.GetInterfaces(); foreach ($it in $all) {
  foreach ($m in $it.GetMethods() | ? { -not $_.IsSpecialName }) { "  M {0}.{1}({2}) : {3}" -f $it.Name, $m.Name, (($m.GetParameters() | % { $_.ParameterType.Name + ' ' + $_.Name }) -join ', '), $m.ReturnType.Name }
  foreach ($p in $it.GetProperties()) { "  P {0}.{1} : {2}" -f $it.Name, $p.Name, $p.PropertyType.Name } } }
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open('C:\IbriWork\M13\IBRI_3_9_2026_12M.stsw')
  $u = $m.UserFieldManager; "== UserFieldManager " + $u.GetType().FullName; Sig $u.GetType()
  "== existing user fields on manholes"
  $dst = $m.DomainDataSet.DomainDataSetType()
  $at = $dst.AlternativeType(100)
  foreach ($id in 1,3,5) { "  type $id : " + (($at.FieldTypes($id) | % { $_.Name }) -join ', ') }
  "== IAlternativeType.AddFieldType / IDomainElementType.AddFieldType signature check done"
  $sm = $m.DomainDataSet.ScenarioManager
  "== ScenarioManager type " + $sm.GetType().FullName
  $com = $sm.CalculationOptionsManager('DelawareProductEngine'); "== CalcOptionsManager " + $com.GetType().FullName; Sig $com.GetType() | select -First 40
  $m.Close()
} catch { "FAILED: " + $_.Exception.ToString() } finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
