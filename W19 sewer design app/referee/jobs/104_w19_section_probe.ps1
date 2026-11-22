# W19 sections, step 1 (probe, read-only, on a copy): what SewerGEMS's documented API tells about a conduit's cross-section,
# so the app can solve box and open-channel conduits. Lists the catalogue's support fields and the columns of its size
# table, the shape label, size and diameter of the first conduits, and the network's element collections.
$src = '\\VBOXSVR\Win10_shared_folder\SewerGEMS Block 04 11102026\SewerGEMS Block 04.stsw'
. \\VBOXSVR\VBOX\bridge\lib\load.ps1
$out = "\\VBOXSVR\VBOX\bridge\out\w19\probe_sections.txt"
$dir = "C:\IbriWork\W19\src\probe_sections"; New-Item -ItemType Directory -Force $dir | Out-Null
Copy-Item -LiteralPath $src -Destination "$dir\model.stsw" -Force
Copy-Item -LiteralPath "$src.sqlite" -Destination "$dir\model.stsw.sqlite" -Force
$log = New-Object IO.StringWriter
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open("$dir\model.stsw")
  $dds = $m.DomainDataSet
  $log.WriteLine("network collections: " + (($m.Network | Get-Member -MemberType Property | ForEach-Object Name) -join ', '))
  $st = $dds.DomainDataSetType().SupportElementType("CatalogConduit")
  try { $fs = $dds.FieldManager.SupportElementFields($st.Id); $log.WriteLine("catalogue fields: " + (($fs | ForEach-Object { $_.Name }) -join ', ')) }
  catch { $log.WriteLine("SupportElementFields: " + $_.Exception.Message); $log.WriteLine("field manager: " + (($dds.FieldManager | Get-Member -MemberType Method | ForEach-Object Name) -join ', ')) }
  $f = $dds.FieldManager.SupportElementField("ClassSizeCollection", $st.Id)
  foreach ($el in $dds.SupportElementManager($st.Id).Elements()) {
    $lm = $f.GetValue($el.Id); $dv = $lm.GetType().GetProperty("DataView").GetValue($lm, $null)
    $log.WriteLine(("class {0} '{1}': {2} sizes; columns: {3}" -f $el.Id, $el.Label, $dv.Count, (($dv.Table.Columns | ForEach-Object ColumnName) -join ', ')))
    if ($fs) { foreach ($x in $fs) { try { $v = $x.GetValue($el.Id); if ($v -isnot [System.Collections.IEnumerable] -or $v -is [string]) { $log.WriteLine(("    {0} = {1}" -f $x.Name, $v)) } } catch {} } }
    $k = 0; foreach ($r in $dv) { if ($k -lt 3) { $log.WriteLine("    size: " + (($dv.Table.Columns | ForEach-Object { $_.ColumnName + '=' + $r[$_.ColumnName] }) -join '; ')) }; $k += 1 }
  }
  $k = 0
  foreach ($c in $m.Network.Conduits.Elements()) {
    if ($k -ge 5) { break }; $i = $c.Input
    $log.WriteLine(("conduit {0}: shape '{1}', size {2}, diameter {3}, Manning? {4}" -f $c.Label, $i.ConduitShapeLabel, $i.Size, $i.ConduitDiameter, (($i | Get-Member -MemberType Property | Where-Object Name -match 'Mann|Rough|Shape|Rise|Span|Width|Slope|Section' | ForEach-Object { $_.Name + '=' + $i.($_.Name) }) -join '; ')))
    $k += 1
  }
  $m.Close()
} catch { $log.WriteLine('FAILED: ' + $_.Exception.ToString()) } finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
[IO.File]::WriteAllText($out, $log.ToString())
