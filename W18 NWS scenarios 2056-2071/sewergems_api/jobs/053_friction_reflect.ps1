. \\VBOXSVR\VBOX\bridge\lib\load.ps1
# Enum values for the gravity friction method and the Darcy friction factor method; conduit roughness field names.
$log = New-Object IO.StringWriter
foreach ($asm in [AppDomain]::CurrentDomain.GetAssemblies()) {
  $ts = try { $asm.GetTypes() } catch { $_.Exception.Types | ? { $_ } }
  foreach ($t in $ts | ? { $_.IsEnum -and $_.Name -match 'Friction' }) {
    $log.WriteLine("enum " + $t.FullName + ": " + (([Enum]::GetNames($t) | % { $_ + '=' + [int][Enum]::Parse($t, $_) }) -join ', ')) }
}
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open('C:\IbriWork\scratch_f0\IBRI_W17_R4.stsw')
  $dds = $m.DomainDataSet; $pt = $dds.DomainDataSetType().AlternativeType('Physical').Id
  foreach ($f in $dds.FieldManager.AlternativeFields($pt, 3, 6)) { if ($f.Name -match 'Darcy|Rough|Kutter|Hazen') { $log.WriteLine("conduit physical field: " + $f.Name + "  sample " + $f.GetValue(562)) } }
  $com = $dds.ScenarioManager.CalculationOptionsManager('DelawareProductEngine')
  foreach ($n in 'HmFrictionMethod', 'DarcyFrictionFactorMethod', 'DarcyWeisbachType_KinematicViscosity', 'PressureFrictionMethod') { $f = $com.CalculationOptionsField($n); $log.WriteLine("$n : " + $f.GetValue(31) + " | " + $f.GetType().Name + " | " + $f.Label) }
  $m.Close()
} catch { $log.WriteLine('FAILED: ' + $_.Exception.ToString()) } finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
$log.ToString()
