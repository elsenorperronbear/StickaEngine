# PowerShell script to create desktop shortcut for StickaEngine
# Run this after building the executable

param(
    [string]$TargetPath = "$PSScriptRoot\dist\StickaEngine.exe",
    [string]$WorkingDir = "$PSScriptRoot\dist",
    [string]$ShortcutName = "StickaEngine"
)

# Get desktop path
$desktop = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path -Path $desktop -ChildPath "$ShortcutName.lnk"

# Check if target exists
if (-not (Test-Path -Path $TargetPath)) {
    Write-Host "ERROR: Target executable not found: $TargetPath"
    exit 1
}

# Create shortcut using WScript.Shell
try {
    $ws = New-Object -ComObject WScript.Shell
    $shortcut = $ws.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = $TargetPath
    $shortcut.WorkingDirectory = $WorkingDir
    $shortcut.Description = "StickaEngine - Desktop Sticker Hub with iOS-style glassmorphism UI"
    $shortcut.IconLocation = "$TargetPath,0"
    $shortcut.Save()
    
    Write-Host "SUCCESS: Desktop shortcut created at $shortcutPath"
    exit 0
} catch {
    Write-Host "ERROR: Failed to create shortcut: $_"
    exit 1
}
