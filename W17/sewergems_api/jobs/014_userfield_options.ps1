. \\VBOXSVR\VBOX\bridge\lib\load.ps1
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open('C:\IbriWork\M13\IBRI_3_9_2026_12M.stsw')
  $o = $m.UserFieldManager.NewFieldOptions()
  "options type: " + $o.GetType().FullName
  $o | Get-Member | ? MemberType -in 'Property','Method' | % { "  " + $_.Definition }
  foreach ($p in $o.GetType().GetProperties()) { if ($p.PropertyType.IsEnum) { "  enum " + $p.Name + ": " + ([Enum]::GetNames($p.PropertyType) -join ', ') } }
  $m.Close()
} catch { "FAILED: " + $_.Exception.ToString() } finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
