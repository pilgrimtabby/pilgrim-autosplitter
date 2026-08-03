#!/usr/bin/env pwsh
# Builds and launches the settings-UI preview project
# so visual changes can be checked without a running LiveSplit.
# See CONTRIBUTING.md for why Linux native Mono is not used in favor of Wine.
$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$project = Join-Path $repoRoot 'tools/PreviewSettings/PreviewSettings.csproj'
$outDir = Join-Path $repoRoot 'tools/PreviewSettings/bin/Release/net481'
$exe = Join-Path $outDir 'PreviewSettings.exe'

# Check run prerequisites before building, so a missing display or wine fails fast.
if (-not $IsWindows) {
  if (-not $env:DISPLAY) {
    throw 'No X DISPLAY set. Run from a graphical session (or set DISPLAY).'
  }

  # wine only: its bundled Mono renders WinForms via wine's graphics stack, matching the real host.
  # Native Mono (libgdiplus) drops button/label text (Mono bug, not ours: TASEmulators/BizHawk#4469).
  if (-not (Get-Command wine -ErrorAction SilentlyContinue)) {
    throw 'wine not found. Install wine to preview this Windows-only UI on Linux.'
  }
}

dotnet build $project --configuration Release

if ($IsWindows) { & $exe } else { & wine $exe }
