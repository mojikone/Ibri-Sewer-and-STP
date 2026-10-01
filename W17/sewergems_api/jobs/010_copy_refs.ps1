$dst = '\\VBOXSVR\VBOX\bridge\refs'; New-Item -ItemType Directory -Force $dst | Out-Null
Get-ChildItem 'C:\Program Files (x86)\Bentley\SewerGEMS\x64' -Filter *.dll | Where-Object { $_.Name -match '^(OpenFlows|Haestad\.)' } | Copy-Item -Destination $dst -Force
(Get-ChildItem $dst).Count
