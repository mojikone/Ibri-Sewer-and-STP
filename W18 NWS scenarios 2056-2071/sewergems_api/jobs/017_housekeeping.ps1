. \\VBOXSVR\VBOX\bridge\lib\load.ps1
$share = '\\VBOXSVR\Win10_shared_folder\IBRI Sewer\13 IBRI_29092026 12M(7.12 PM )'
$m13b = 'C:\IbriWork\M13b'
Remove-Item -Recurse -Force 'C:\IbriWork\W17' -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force $m13b | Out-Null
foreach ($f in 'IBRI_3_9_2026_12M.stsw','IBRI_3_9_2026_12M.stsw.sqlite','IBRI_3_9_2026_12M.stsw.dwh','IBRI_3_9_2026_12M.stsw.profiles.dwh') { Copy-Item -LiteralPath (Join-Path $share $f) -Destination $m13b -Force }
Copy-Item -LiteralPath (Join-Path $share 'SHP') -Destination $m13b -Recurse -Force
$src  = 'C:\IbriWork\M13b\IBRI_3_9_2026_12M.stsw'
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
  Step 'terrain reference' { $dds=$m.DomainDataSet; $st=$dds.DomainDataSetType().SupportElementType('DigitalTerrainModel'); foreach($el in $dds.SupportElementManager($st.Id).Elements()){ foreach($fl in $dds.FieldManager.SupportElementFields($st.Id)){ $log.WriteLine('  DTM ' + $el.Label + ' ' + $fl.Name + ' = ' + $fl.GetValue($el.Id)) } } }
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

