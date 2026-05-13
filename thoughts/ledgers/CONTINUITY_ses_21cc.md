---
session: ses_21cc
updated: 2026-05-01T14:45:53.972Z
---

<｜｜DSML｜｜tool_calls>
<｜｜DSML｜｜invoke name="bash">
<｜｜DSML｜｜parameter name="command" string="true">Write-Output "=== CACHED PLUGINS CHECK ==="; Get-ChildItem "C:\Users\almaz\.cache\opencode\packages" -Directory | Select-Object Name, LastWriteTime; Write-Output "`n=== EACH PLUGIN's package.json ==="; Get-ChildItem "C:\Users\almaz\.cache\opencode\packages" -Recurse -Depth 2 -Filter "package.json" | ForEach-Object { 
    $pkg = Get-Content $_.FullName -Raw | ConvertFrom-Json 2>$null
    [PSCustomObject]@{
        Package = $pkg.name
        Version = $pkg.version
        Description = if ($pkg.description) { $pkg.description.Substring(0,[Math]::Min(80,$pkg.description.Length)) } else { "—" }
        Path = $_.DirectoryName
    }
} | Format-Table -AutoSize</｜｜DSML｜｜parameter>
<｜｜DSML｜｜parameter name="description" string="true">Check each cached plugin's package.json</｜｜DSML｜｜parameter>
<｜｜DSML｜｜parameter name="timeout" string="false">10000</｜｜DSML｜｜parameter>
</｜｜DSML｜｜invoke>
<｜｜DSML｜｜invoke name="bash">
<｜｜DSML｜｜parameter name="command" string="true">Write-Output "=== MICODE STRUCTURE ==="; Get-ChildItem "C:\Users\almaz\.cache\opencode\packages\micode@latest" -Depth 3 | Select-Object FullName, Length, LastWriteTime | Format-Table -AutoSize -Wrap
Write-Output "`n=== HIVE STRUCTURE ==="; Get-ChildItem "C:\Users\almaz\.cache\opencode\packages\opencode-hive@latest" -Depth 3 -ErrorAction SilentlyContinue | Select-Object FullName, Length, LastWriteTime | Format-Table -AutoSize -Wrap
Write-Output "`n=== OCTTO STRUCTURE ==="; Get-ChildItem "C:\Users\almaz\.cache\opencode\packages\list@latest" -Depth 3 | Select-Object FullName, Length, LastWriteTime | Format-Table -AutoSize -Wrap</｜｜DSML｜｜parameter>
<｜｜DSML｜｜parameter name="description" string="true">Deep inspect micode, hive, and octto caches</｜｜DSML｜｜parameter>
<｜｜DSML｜｜parameter name="timeout" string="false">15000</｜｜DSML｜｜parameter>
</｜｜DSML｜｜invoke>
</｜｜DSML｜｜tool_calls>
