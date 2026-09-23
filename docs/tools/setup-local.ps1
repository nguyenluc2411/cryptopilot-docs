# One-time local setup for Windows. Run from the repository root in PowerShell:
#   powershell -ExecutionPolicy Bypass -File docs\tools\setup-local.ps1
# Same behaviour as setup-local.sh:
# - keeps the project documents and AI tooling out of git (.git/info/exclude, local to this clone)
# - installs the commit-msg and pre-commit hooks (run by Git for Windows' bundled shell)
# Safe to run again; it rewrites only its own managed block.

$ErrorActionPreference = 'Stop'

$root = (git rev-parse --show-toplevel 2>$null)
if (-not $root) { Write-Error 'Run this inside the git repository.'; exit 1 }
Set-Location $root
$gitDir = (git rev-parse --git-dir)
if (-not [System.IO.Path]::IsPathRooted($gitDir)) { $gitDir = Join-Path $root $gitDir }
New-Item -ItemType Directory -Force -Path (Join-Path $gitDir 'info') | Out-Null

$utf8NoBom = New-Object System.Text.UTF8Encoding($false)

# ---- 1. Local-only paths (edit this list if the team decides to publish a file)
$block = @(
  '# >>> cryptopilot-local-only (managed by docs/tools/setup-local)',
  '/CLAUDE.md',
  '/CLAUDE.local.md',
  '/CURRENT_STATE.md',
  '/.claude/',
  '/docs/README.md',
  '/docs/srs/',
  '/docs/design/',
  '/docs/adr/',
  '/docs/test/',
  '/docs/tools/',
  '# The second git dir that syncs everything above between team members, and its wrappers.',
  '/.docs.git/',
  '/docs.ps1',
  '/docs.sh',
  '# <<< cryptopilot-local-only'
)

$exclude = Join-Path $gitDir 'info/exclude'
$existing = @()
if (Test-Path $exclude) { $existing = Get-Content $exclude }
$kept = New-Object System.Collections.Generic.List[string]
$skip = $false
foreach ($line in $existing) {
  if ($line -like '# >>> cryptopilot-local-only*') { $skip = $true; continue }
  if ($line -like '# <<< cryptopilot-local-only*') { $skip = $false; continue }
  if (-not $skip) { $kept.Add($line) }
}
$all = @($kept) + $block
[System.IO.File]::WriteAllText($exclude, (($all -join "`n") + "`n"), $utf8NoBom)
Write-Host "[setup] local-only paths written to $exclude"

# ---- 2. Hooks, written with LF line endings and no BOM so Git Bash can run them
$hooksPath = (git config --get core.hooksPath 2>$null)
if ($hooksPath) {
  Write-Warning "core.hooksPath is set to '$hooksPath'; installing hooks there."
  $target = if ([System.IO.Path]::IsPathRooted($hooksPath)) { $hooksPath } else { Join-Path $root $hooksPath }
} else {
  $target = Join-Path $gitDir 'hooks'
}
New-Item -ItemType Directory -Force -Path $target | Out-Null
foreach ($h in @('commit-msg', 'pre-commit')) {
  $src = Join-Path $root "docs/tools/hooks/$h"
  $text = [System.IO.File]::ReadAllText($src) -replace "`r`n", "`n"
  [System.IO.File]::WriteAllText((Join-Path $target $h), $text, $utf8NoBom)
}
Write-Host "[setup] hooks installed in $target"

# ---- 2b. The documents repository has its own pre-commit, because it shares this working tree
#         and a mistyped command would otherwise stage the whole backend into it.
$docsGit = Join-Path $root '.docs.git'
if (Test-Path $docsGit) {
  $docsHooks = Join-Path $docsGit 'hooks'
  New-Item -ItemType Directory -Force -Path $docsHooks | Out-Null
  $src = Join-Path $root 'docs/tools/hooks/docs-pre-commit'
  $text = (Get-Content $src -Raw) -replace "`r`n", "`n"
  [System.IO.File]::WriteAllText((Join-Path $docsHooks 'pre-commit'), $text)
  & git --git-dir="$docsGit" --work-tree="$root" config status.showUntrackedFiles no
  Write-Host "[setup] documents repository guarded (.docs.git/hooks/pre-commit)"
} else {
  Write-Host "[setup] no .docs.git yet - see docs/BOOTSTRAP.md to clone the documents repository"
}

# ---- 3. Check that nothing local-only is already tracked
$tracked = git ls-files CLAUDE.md CLAUDE.local.md CURRENT_STATE.md .claude docs/README.md docs/srs docs/design docs/adr docs/test docs/tools 2>$null
if ($tracked) {
  Write-Warning 'These local-only files are already tracked by git:'
  $tracked | ForEach-Object { Write-Host "  $_" }
  Write-Warning 'Untrack them (files stay on disk):  git rm -r --cached <path>  then commit.'
}

Write-Host '[setup] done. Verify with: git status --short   (local-only files must not appear)'
