# W18 final design (engineer, 2026-11-18: 0.75 %, SC1-SC4, 2051/2056/2061, cleansing checked at 2031 and 2036): read
# from R4 the full conduit catalogue (label, inside diameter) and every sanitary-loading alternative (id, label, parent),
# for the own design and the scenario builder (2036 is not yet in its year map). Read only: opened, listed, closed, not saved.
. \\VBOXSVR\VBOX\bridge\lib\load.ps1
$log = New-Object IO.StringWriter
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open('C:\IbriWork\W18\IBRI_W18_R4.stsw')
  $cat = [SizeCheck]::Catalogue($m)
  foreach ($k in $cat.Keys) { $log.WriteLine(('CAT|{0}|{1}' -f $cat[$k].Item1, $cat[$k].Item2)) }
  $dds = $m.DomainDataSet
  foreach ($t in @('SanitaryLoading', 'Physical')) {
    $am = $dds.AlternativeManager($dds.DomainDataSetType().AlternativeType($t).Id)
    foreach ($a in $am.Elements()) { $log.WriteLine(('ALT|{0}|{1}|{2}|{3}' -f $t, $a.Id, $a.Label, $a.ParentID)) }
  }
  foreach ($s in $m.Scenarios.Elements()) { $log.WriteLine(('SCN|{0}|{1}' -f $s.Id, $s.Label)) }
  $m.Close()
} catch { $log.WriteLine('FAILED: ' + $_.Exception.ToString()) } finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
$log.ToString()
