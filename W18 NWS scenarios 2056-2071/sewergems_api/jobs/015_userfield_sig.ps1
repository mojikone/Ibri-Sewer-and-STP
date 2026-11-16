. \\VBOXSVR\VBOX\bridge\lib\load.ps1
$a = [AppDomain]::CurrentDomain.GetAssemblies() | ? { $_.GetName().Name -eq 'OpenFlows' }
$types = try { $a.GetTypes() } catch { $_.Exception.InnerException.Types | ? { $_ } }
foreach ($t in $types | ? { $_.Name -match 'UserField|UserNetworkfield' }) {
  "== " + $t.FullName + "  generic=" + $t.IsGenericTypeDefinition
  foreach ($mi in $t.GetMethods() | ? { -not $_.IsSpecialName -and $_.DeclaringType -eq $t }) {
    "  M " + $mi.ToString() + "  genericDef=" + $mi.IsGenericMethodDefinition }
  foreach ($p in $t.GetProperties()) { "  P " + $p.PropertyType.ToString() + " " + $p.Name + "  set=" + $p.CanWrite }
}
foreach ($t in $types | ? { $_.IsEnum -and $_.Name -match 'Field.*Type|DataType' }) { "  enum " + $t.FullName + ": " + ([Enum]::GetNames($t) -join ', ') }
