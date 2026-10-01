. \\VBOXSVR\VBOX\bridge\lib\load.ps1
$src  = 'C:\IbriWork\M13\IBRI_3_9_2026_12M.stsw'
$dir  = 'C:\IbriWork\W17'
$dst  = "$dir\IBRI_W17_R0.stsw"
$inv  = '\\VBOXSVR\VBOX\bridge\out\inv'
New-Item -ItemType Directory -Force $dir | Out-Null
$log = New-Object IO.StringWriter
function Step($name, [scriptblock]$b) { $log.WriteLine("== $name"); try { & $b; $log.WriteLine("   ok") } catch { $log.WriteLine("   FAILED: " + $_.Exception.InnerException + " " + $_.Exception.Message); throw } }
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open($src)
  Step 'save as new file' { $m.SaveAs($dst) }
  Step 'calc options -> DESIGN'      { [Housekeeping]::RenameCalcOptions($m, 'DelawareProductEngine', 31, 'DESIGN', $log) }
  Step 'physical F -> 2070'          { [Housekeeping]::RenameAlternative($m, 'Physical', 279727, '2070', $log) }
  Step 'empty 2070 sanitary deleted' { [Housekeeping]::DeleteAlternativeIfUnused($m, 'SanitaryLoading', 279774, $log) }
  Step 'base sanitary -> 2070'       { [Housekeeping]::RenameAlternative($m, 'SanitaryLoading', 14, '2070', $log) }
  Step 'scenario 34 -> 2070'         { [Housekeeping]::RenameScenario($m, 279744, '2070', $log) }
  Step 'drop system flows'           { [Housekeeping]::DropSystemFlows($m, $log) }
  Step 'delete property inference scenarios' { [Housekeeping]::DeleteScenarios($m, 'Property Inference Scenario', 279744, $log) }
  Step 'delete test pump station'    { [Housekeeping]::DeleteTestPump($m, $log) }
  Step 'OLD_ID field'                { [Housekeeping]::CreateOldIdField($m, $log) }
  Step 'OLD_ID fill'                 { foreach ($t in 'Manhole','Conduit','Outfall') { [void][Housekeeping]::FillOldId($m, $t, 'OLD_ID', $log) } }
  Step 'rename nodes'                { [Housekeeping]::ApplyLabels($m, "$inv\rename_nodes.csv", $log) }
  Step 'rename conduits'             { [Housekeeping]::ApplyLabels($m, "$inv\rename_links.csv", $log) }
  Step 'save'                        { $m.Save() }
  $m.Close()
} catch { $log.WriteLine("ABORTED: " + $_.Exception.ToString()) }
finally {
  [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession()
  [IO.File]::WriteAllText("$inv\housekeeping_log.txt", $log.ToString(), (New-Object Text.UTF8Encoding($false)))
}
Get-ChildItem $dir | % { "{0,12}  {1}" -f $_.Length, $_.Name }
