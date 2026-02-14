# Window Restore Context Menu Script
param(
    [string]$Action = "menu",
    [string]$AppPath = "",
    [string]$PythonExe = ""
)

if ([string]::IsNullOrWhiteSpace($AppPath)) {
    $AppPath = Join-Path $PSScriptRoot "src\main.py"
}
if ([string]::IsNullOrWhiteSpace($PythonExe)) {
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCmd) {
        $pythonw = Join-Path ([System.IO.Path]::GetDirectoryName($pythonCmd.Path)) "pythonw.exe"
        if (Test-Path $pythonw) { $PythonExe = $pythonw } else { $PythonExe = $pythonCmd.Path }
    } else {
        $PythonExe = "python"
    }
}

function Get-Presets {
    $presetFile = "$env:APPDATA\WindowRestore\presets.json"
    if (Test-Path $presetFile) {
        try {
            $data = Get-Content $presetFile -Raw | ConvertFrom-Json
            return @($data.presets.name)
        } catch { }
    }
    return @()
}

Add-Type -AssemblyName System.Windows.Forms

$menu = New-Object System.Windows.Forms.ContextMenuStrip

# Save
$item1 = New-Object System.Windows.Forms.ToolStripMenuItem("Save Current Layout...")
$item1.Add_Click({ Start-Process -FilePath $PythonExe -ArgumentList @("""$AppPath""","--save-dialog") -WindowStyle Hidden }.GetNewClosure())
$menu.Items.Add($item1)

# Restore submenu
$presets = Get-Presets
if ($presets.Count -gt 0) {
    $restore = New-Object System.Windows.Forms.ToolStripMenuItem("Restore Layout")
    foreach ($p in $presets) {
        $presetName = $p.ToString()
        $pi = New-Object System.Windows.Forms.ToolStripMenuItem($presetName)
        $pi.Add_Click({ Start-Process -FilePath $PythonExe -ArgumentList @("""$AppPath""","--restore","""$presetName""") -WindowStyle Hidden }.GetNewClosure())
        $restore.DropDownItems.Add($pi)
    }
    $menu.Items.Add($restore)
}

# Manage
$item2 = New-Object System.Windows.Forms.ToolStripMenuItem("Manage Presets...")
$item2.Add_Click({ Start-Process -FilePath $PythonExe -ArgumentList @("""$AppPath""","--manage") -WindowStyle Normal }.GetNewClosure())
$menu.Items.Add($item2)

$menu.Items.Add("-")

# Settings
$item3 = New-Object System.Windows.Forms.ToolStripMenuItem("Settings")
$item3.Add_Click({ Start-Process -FilePath $PythonExe -ArgumentList @("""$AppPath""","--settings") -WindowStyle Hidden }.GetNewClosure())
$menu.Items.Add($item3)

$menu.Items.Add("-")

# Register
$item4 = New-Object System.Windows.Forms.ToolStripMenuItem("Register Context Menu")
$item4.Add_Click({ Start-Process -FilePath $PythonExe -ArgumentList @("""$AppPath""","--register") -WindowStyle Hidden }.GetNewClosure())
$menu.Items.Add($item4)

# Unregister
$item5 = New-Object System.Windows.Forms.ToolStripMenuItem("Unregister Context Menu")
$item5.Add_Click({ Start-Process -FilePath $PythonExe -ArgumentList @("""$AppPath""","--unregister") -WindowStyle Hidden }.GetNewClosure())
$menu.Items.Add($item5)

$menu.Items.Add("-")

# Exit
$item6 = New-Object System.Windows.Forms.ToolStripMenuItem("Exit")
$item6.Add_Click({ })
$menu.Items.Add($item6)

$menu.Show([System.Windows.Forms.Cursor]::Position)
while ($menu.Visible) {
    [System.Windows.Forms.Application]::DoEvents()
    Start-Sleep -Milliseconds 50
}
