[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [string]$SkillsDir,

    [Parameter(Position = 1)]
    [string]$PipSource,

    [string]$Python = $(if ($env:PYTHON) { $env:PYTHON } else { "python" }),

    [string]$PipTarget = $env:PIP_TARGET,

    [string]$ToolkitDir,

    [switch]$Overwrite
)

$ErrorActionPreference = "Stop"

<#
Install the ModularResearchDocWriter Codex skill via pip.

Usage:
  ./scripts/install-skill.ps1 [[-SkillsDir] <path>] [[-PipSource] <path-or-pip-url>] [-ToolkitDir <path>] [-Overwrite]

Examples:
  ./scripts/install-skill.ps1
  ./scripts/install-skill.ps1 "$HOME/.codex/skills" . -ToolkitDir "$HOME/.mrm-toolkit" -Overwrite
  ./scripts/install-skill.ps1 "C:\codex\skills" "git+https://github.com/<owner>/<repo>.git"

Environment:
  PYTHON      Python executable to use. Default: python.
  PIP_TARGET       Temporary pip --target folder. Default: a new temp folder.
  MRM_TOOLKIT_HOME  Default toolkit folder when -ToolkitDir is omitted.
#>

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-Path (Join-Path $scriptDir "..")

if (-not $SkillsDir) {
    if ($env:CODEX_HOME) {
        $SkillsDir = Join-Path $env:CODEX_HOME "skills"
    } else {
        $SkillsDir = Join-Path $HOME ".codex/skills"
    }
}

if (-not $PipSource) {
    $PipSource = $repoRoot.Path
}

if (-not $ToolkitDir) {
    if ($env:MRM_TOOLKIT_HOME) {
        $ToolkitDir = $env:MRM_TOOLKIT_HOME
    } else {
        $ToolkitDir = Join-Path $HOME ".mrm-toolkit"
    }
}

$cleanupPipTarget = $false
if (-not $PipTarget) {
    $PipTarget = Join-Path ([System.IO.Path]::GetTempPath()) ("mrm-skill-pip-" + [System.Guid]::NewGuid().ToString("N"))
    $cleanupPipTarget = $true
}
New-Item -ItemType Directory -Force -Path $PipTarget | Out-Null

try {
    Write-Host "Installing Python package from '$PipSource' into temporary pip target '$PipTarget'..."
    & $Python -m pip install $PipSource --target $PipTarget --upgrade
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    Write-Host "Installing Codex skill into '$SkillsDir' and MRM toolkit into '$ToolkitDir'..."
    $oldPythonPath = $env:PYTHONPATH
    if ($oldPythonPath) {
        $env:PYTHONPATH = "$PipTarget$([System.IO.Path]::PathSeparator)$oldPythonPath"
    } else {
        $env:PYTHONPATH = $PipTarget
    }

    $installerArgs = @("-m", "modular_research_doc_writer.installer", "--target", $SkillsDir, "--toolkit-target", $ToolkitDir)
    if ($Overwrite) { $installerArgs += "--overwrite" }
    & $Python @installerArgs
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
finally {
    if ($null -ne $oldPythonPath) {
        $env:PYTHONPATH = $oldPythonPath
    }
    if ($cleanupPipTarget -and (Test-Path $PipTarget)) {
        Remove-Item -Recurse -Force $PipTarget
    }
}
