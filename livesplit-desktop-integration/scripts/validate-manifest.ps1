#!/usr/bin/env pwsh
<#
.SYNOPSIS
  Validate the auto-update manifest the way LiveSplit's UpdateManager parses it.

.DESCRIPTION
  UpdateManager parses the manifest with no null checks inside a silent catch-all, so any
  malformed node aborts parsing and offers zero updates with no error. This script fails loudly
  (GitHub `::error::` annotations) on any shape that would break that parse.

  With -ReleaseVersion, also asserts that version's entry is release-ready: it exists, has a
  download/v<version>/ asset path, and a non-empty changelog.
#>
param(
  [string]$Path = 'update.LiveSplit.AutoSplitIntegration.xml',
  [string]$ReleaseVersion = ''
)
$ErrorActionPreference = 'Stop'
$errs = @()
$versions = @()

[xml]$doc = Get-Content -Raw -LiteralPath $Path
$root = $doc.DocumentElement
if ($root.Name -ne 'updates') { $errs += "root is <$($root.Name)>, expected <updates>" }

foreach ($node in $root.ChildNodes) {
  if ($node.NodeType -ne [System.Xml.XmlNodeType]::Element -or $node.Name -ne 'update') {
    $errs += "non-<update> node inside <updates> ($($node.NodeType) '$($node.Name)'). The updater aborts on it. Keep comments above the <updates> root"
    continue
  }
  $v = $node.GetAttribute('version')
  if ([string]::IsNullOrEmpty($v)) {
    $errs += '<update> without a version attribute'
    $v = '?'
  }
  $versions += $v

  # The updater iterates ALL children of <files> (FileChange.Parse each) and of <changelog>
  # (InnerText each). A comment in <files> NREs and aborts parsing. A comment in <changelog>
  # leaks its text in as a visible change line. So every child must be the expected element.
  $files = $node.SelectSingleNode('files')
  if ($null -eq $files) { $errs += "<update $v> is missing <files> (use <files /> if it has none)" }
  else {
    foreach ($c in $files.ChildNodes) {
      if ($c.NodeType -ne [System.Xml.XmlNodeType]::Element -or $c.Name -ne 'file') {
        $errs += "<update $v> <files> contains a non-<file> node ($($c.NodeType) '$($c.Name)'). Aborts the updater's parse"
        continue
      }
      if ([string]::IsNullOrEmpty($c.GetAttribute('path'))) { $errs += "<update $v> has a <file> without a path attribute" }
      if ([string]::IsNullOrEmpty($c.GetAttribute('status'))) { $errs += "<update $v> has a <file> without a status attribute" }
    }
  }

  $changelog = $node.SelectSingleNode('changelog')
  if ($null -eq $changelog) { $errs += "<update $v> is missing <changelog>" }
  else {
    foreach ($c in $changelog.ChildNodes) {
      if ($c.NodeType -ne [System.Xml.XmlNodeType]::Element -or $c.Name -ne 'change') {
        $errs += "<update $v> <changelog> contains a non-<change> node ($($c.NodeType) '$($c.Name)'). Its text would leak into the shown changelog"
      }
    }
  }
}

# A manifest with only the 0.0.0 staging block has nothing to release.
if (@($versions | Where-Object { $_ -ne '0.0.0' }).Count -eq 0) {
  $errs += 'no releasable <update> entry (only the 0.0.0 staging block). Promote it to a real version'
}

if ($ReleaseVersion) {
  $u = $root.SelectSingleNode("update[@version='$ReleaseVersion']")
  if ($null -eq $u) {
    $errs += "no <update version=""$ReleaseVersion""> to release (promote the 0.0.0 staging block to this version)"
  }
  else {
    if ($u.SelectNodes("files/file[contains(@path,'download/v$ReleaseVersion/')]").Count -eq 0) {
      $errs += "<update $ReleaseVersion> has no download/v$ReleaseVersion/ asset path"
    }
    $hasChange = $false
    foreach ($c in $u.SelectNodes('changelog/change')) { if ($c.InnerText.Trim()) { $hasChange = $true } }
    if (-not $hasChange) { $errs += "<update $ReleaseVersion> has no non-empty <change> changelog entry" }
  }
}

if ($errs.Count) {
  # file= attaches each as a GitHub annotation on the manifest (no line numbers tracked).
  $errs | ForEach-Object { Write-Host "::error file=$($Path)::$_" }
  exit 1
}

$n = @($doc.updates.update).Count
$suffix = if ($ReleaseVersion) { "; release entry $ReleaseVersion is ready" } else { '' }
Write-Host "Manifest OK: $n <update> entries parse cleanly$suffix."
