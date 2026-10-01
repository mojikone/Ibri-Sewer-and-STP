. \\VBOXSVR\VBOX\bridge\lib\load.ps1
$ids = New-Object 'System.Collections.Generic.List[int]'; @(2035,9933,23610,26539,32264,35417,36888,39077,39500,40118,40433,41473,42605,42741,43521,45237,47664,47705,47871,126073,276987,277098,277138,277444,277581,278907,279073,279243,279372,279476,279522,279702) | % { $ids.Add($_) }
$out = '\\VBOXSVR\VBOX\bridge\out\peak'
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open('C:\IbriWork\scratch_run\IBRI_W17_R0.stsw')
  $dds = $m.DomainDataSet; $at = $dds.DomainDataSetType().AlternativeType('InfiltrationAndInflow').Id
  $c = $dds.FieldManager.AlternativeField('InflowListCount', $at, 1, 11).GetValues(); $n = 0; foreach ($e in $c) { if ([int]$e.Value -gt 0) { $n++ } }; "manholes with I&I inflows in base alt: $n"
  $sw = New-Object IO.StringWriter
  [ResultFields]::Export($m, 279763, $ids, "$out\outfall_pipes_2030.csv", $sw)
  $sw.ToString()
  $m.Close()
} catch { 'FAILED: ' + $_.Exception.ToString() } finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
