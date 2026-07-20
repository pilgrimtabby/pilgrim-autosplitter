#!/usr/bin/env pwsh
<#
.SYNOPSIS
  Promote the staged 0.0.0 block in the auto-update manifest to a real release version.

.DESCRIPTION
  This is the release action: the manifest is promoted by running this script, not by hand.

  The staged <update version="0.0.0"> block is renamed to X.Y.Z (its staged <change>s become
  this release's changelog), the current newest release's <files> is moved onto it with the
  asset paths rewritten download/v<old>/ -> download/v<new>/ (only the newest release may list
  files, so the old entry is left an empty <files />), and a fresh empty version="0.0.0" block
  is added on top for the next cycle.

  Existing formatting and the header comment are byte-preserved (PreserveWhitespace); only the
  inserted/edited nodes are touched. The result is validated with validate-manifest.ps1.
#>
param(
  [Parameter(Mandatory)]
  [ValidatePattern('^\d+\.\d+\.\d+$')]
  [string]$Version,
  [string]$Path = 'update.LiveSplit.AutoSplitIntegration.xml'
)
$ErrorActionPreference = 'Stop'

if ($Version -eq '0.0.0') { throw '0.0.0 is the staging version, not a release version' }

$file = (Resolve-Path -LiteralPath $Path).Path
[xml]$doc = New-Object System.Xml.XmlDocument
$doc.PreserveWhitespace = $true
$doc.Load($file)
$root = $doc.DocumentElement

$staging = $root.SelectSingleNode("update[@version='0.0.0']")
if ($null -eq $staging) { throw 'no <update version="0.0.0"> staging block to promote' }
if ($root.SelectSingleNode("update[@version='$Version']")) { throw "manifest already has an <update version=""$Version"">" }

# Refuse before writing anything: a release needs at least one staged <change>, else it ships an
# empty changelog and the manifest fails validation (which the Release workflow runs per version).
$staged = @($staging.SelectNodes('changelog/change') | Where-Object { $_.InnerText.Trim() })
if ($staged.Count -eq 0) { throw 'the 0.0.0 staging block has no <change> to release. Write at least 1 entry first' }

# The current newest release is the only entry that lists files. Move that <files> onto the
# staging entry (rewriting the version in each asset path), and empty out the old one.
$oldRelease = $root.SelectSingleNode('update[files/file]')
if ($null -eq $oldRelease) {
  Write-Host "::warning::no existing release lists <files>; add this release's <file> entries manually"
}
else {
  $oldVersion = $oldRelease.GetAttribute('version')
  $srcFiles = $oldRelease.SelectSingleNode('files')
  $dstFiles = $staging.SelectSingleNode('files')

  foreach ($f in @($srcFiles.SelectNodes('file'))) {
    $f.SetAttribute('path', $f.GetAttribute('path').Replace("download/v$oldVersion/", "download/v$Version/"))
  }
  $dstFiles.IsEmpty = $false
  foreach ($child in @($srcFiles.ChildNodes)) { [void]$dstFiles.AppendChild($child) }  # moves the node
  $srcFiles.IsEmpty = $true  # old release back to <files />
}

# Promote the staging block to the release version.
$staging.SetAttribute('version', $Version)

# Insert a fresh empty 0.0.0 staging block above the promoted one, matching indentation.
$frag = $doc.CreateDocumentFragment()
$frag.InnerXml = "<update version=`"0.0.0`">`n    <files />`n    <changelog>`n    </changelog>`n  </update>"
[void]$root.InsertBefore($frag.FirstChild, $staging)
[void]$root.InsertBefore($doc.CreateTextNode("`n  "), $staging)

# Save without a BOM and without re-indenting (the tree already carries its whitespace).
$settings = New-Object System.Xml.XmlWriterSettings
$settings.Encoding = New-Object System.Text.UTF8Encoding($false)
$settings.NewLineChars = "`n"  # match the manifest's LF (.editorconfig end_of_line = lf)
$writer = [System.Xml.XmlWriter]::Create($file, $settings)
try { $doc.Save($writer) } finally { $writer.Dispose() }
Write-Host "Promoted 0.0.0 -> $Version in $Path (moved <file> attributes onto one line each)"

& "$PSScriptRoot/validate-manifest.ps1" -Path $Path -ReleaseVersion $Version
