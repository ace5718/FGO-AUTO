# Publish PRD and child issues to ace5718/FGO-AUTO
# Prereq: gh auth login
#
# Usage:
#   .\scripts\publish-prd-issues.ps1              # create PRD + child issues
#   .\scripts\publish-prd-issues.ps1 -ParentIssue 1   # PRD already exists; only children
param(
  [int]$ParentIssue = 0
)

$ErrorActionPreference = "Stop"
$gh = "C:\Program Files\GitHub CLI\gh.exe"
$repo = "ace5718/FGO-AUTO"
$label = "ready-for-agent"
$root = "d:\FGO-AUTO"

function Ensure-Label($name) {
  $prevEap = $ErrorActionPreference
  $ErrorActionPreference = "Continue"
  & $gh label create $name --repo $repo 2>&1 | Out-Null
  $ErrorActionPreference = $prevEap
}

foreach ($l in @("ready-for-agent", "needs-triage", "needs-info", "ready-for-human", "wontfix")) {
  Ensure-Label $l
}

if ($ParentIssue -gt 0) {
  $prdNum = "$ParentIssue"
  Write-Host "Using existing PRD parent #$prdNum"
} else {
  $prdBody = Get-Content -Raw "$root\docs\prd\0001-v1-screen-state-and-quest-loop.md"
  $prdUrl = & $gh issue create --repo $repo --title "PRD: v1 Screen state skeleton and Quest loop (TW / BlueStacks 5)" --body $prdBody --label $label
  $prdNum = ($prdUrl -split '/')[-1]
  Write-Host "PRD issue #$prdNum -> $prdUrl"
}

$specs = @(
  @{ file = "01-bootstrap-cli-runconfig.md"; blocked = @() },
  @{ file = "02-host-capture-window-binding.md"; blocked = @("01-bootstrap-cli-runconfig.md") },
  @{ file = "03-state-catalog-v0.md"; blocked = @("02-host-capture-window-binding.md") },
  @{ file = "04-quest-anchor-match-tap.md"; blocked = @("02-host-capture-window-binding.md") },
  @{ file = "05-quest-loop-v0.md"; blocked = @("03-state-catalog-v0.md", "04-quest-anchor-match-tap.md") },
  @{ file = "06-window-pick-followup.md"; blocked = @("02-host-capture-window-binding.md") }
)

$created = @{}
foreach ($spec in $specs) {
  $path = "$root\docs\prd\issues\$($spec.file)"
  $raw = Get-Content -Raw $path
  if ($raw -notmatch '(?m)^# (.+)$') { throw "No title in $($spec.file)" }
  $title = $Matches[1]
  $body = [regex]::Replace($raw, '(?m)^# .+\r?\n', '', 1).Trim()
  $blockedLines = if ($spec.blocked.Count -eq 0) {
    "None - can start immediately"
  } else {
    ($spec.blocked | ForEach-Object { "- #$($created[$_]) ($_" }) -join "`n"
  }
  $body = [regex]::Replace($body, '(?ms)\r?\n## Blocked by\r?\n.*\z', "`n## Blocked by`n`n$blockedLines`n")
  $body = "## Parent`n`n#$prdNum`n`n" + $body
  $url = & $gh issue create --repo $repo --title $title --body $body --label $label
  $num = ($url -split '/')[-1]
  $created[$spec.file] = $num
  Write-Host "#$num $title"
}

Write-Host "`nDone. PRD parent: #$prdNum"
$created.GetEnumerator() | Sort-Object Name | ForEach-Object { Write-Host "  $($_.Key) -> #$($_.Value)" }
