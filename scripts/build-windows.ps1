# Single self-contained Pilgrim Autosplitter.exe (PyInstaller onefile).
# Run on Windows from repo root:
#   .\scripts\build-windows.ps1
#
# Requires: py -m pip install -r requirements.txt pyinstaller
#
# Output: dist\Pilgrim Autosplitter.exe — copy that file anywhere and run it.

$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
py -m PyInstaller --noconfirm "Pilgrim Autosplitter-windows-onefile.spec"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "Built: dist\Pilgrim Autosplitter.exe"
