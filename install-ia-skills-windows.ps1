#requires -Version 5.1
[CmdletBinding()]
param(
    [ValidateNotNullOrEmpty()]
    [string] $Destination = $env:USERPROFILE,
    [switch] $DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$sourceRoot = (Resolve-Path -LiteralPath $PSScriptRoot).Path
$sourceSkills = Join-Path $sourceRoot '.claude\skills'
$destinationRoot = [System.IO.Path]::GetFullPath($Destination)
$plannedDirectories = @{}

if (-not (Test-Path -LiteralPath $sourceSkills -PathType Container)) {
    throw "Skill source directory does not exist: $sourceSkills"
}
if (-not (Test-Path -LiteralPath $destinationRoot -PathType Container)) {
    throw "Destination home directory does not exist: $destinationRoot"
}

function Get-NormalizedTarget {
    param([string] $LinkPath, [string] $Target)

    $targetPath = if ([System.IO.Path]::IsPathRooted($Target)) {
        $Target
    } else {
        Join-Path (Split-Path -Parent $LinkPath) $Target
    }
    return [System.IO.Path]::GetFullPath($targetPath)
}

function Set-SkillLink {
    param([string] $LinkPath, [string] $Target)

    $parent = Split-Path -Parent $LinkPath
    if (Test-Path -LiteralPath $parent) {
        if (-not (Test-Path -LiteralPath $parent -PathType Container)) {
            throw "Link parent is not a directory: $parent"
        }
        # Enumerating the parent also finds dangling symbolic links, which Test-Path misses.
        $existing = Get-ChildItem -LiteralPath $parent -Force |
            Where-Object { $_.Name -eq (Split-Path -Leaf $LinkPath) } |
            Select-Object -First 1
    } else {
        $existing = $null
        if ($DryRun) {
            if (-not $plannedDirectories.ContainsKey($parent)) {
                Write-Host "Would create directory: $parent"
                $plannedDirectories[$parent] = $true
            }
        } else {
            New-Item -ItemType Directory -Path $parent -Force | Out-Null
        }
    }

    if ($null -ne $existing) {
        $existingTarget = @($existing.Target) | Select-Object -First 1
        if ($existing.LinkType -eq 'SymbolicLink' -and
            $null -ne $existingTarget -and
            (Get-NormalizedTarget $LinkPath $existingTarget) -ieq
            (Get-NormalizedTarget $LinkPath $Target)) {
            Write-Host "Already linked: $LinkPath"
            return $true
        }
        Write-Warning "Preserving conflicting path: $LinkPath"
        return $false
    }

    if ($DryRun) {
        Write-Host "Would link: $LinkPath -> $Target"
    } else {
        New-Item -ItemType SymbolicLink -Path $LinkPath -Target $Target | Out-Null
        Write-Host "Linked: $LinkPath -> $Target"
    }
    return $true
}

$skills = @(Get-ChildItem -LiteralPath $sourceSkills -Directory | Where-Object {
    Test-Path -LiteralPath (Join-Path $_.FullName 'SKILL.md') -PathType Leaf
} | Sort-Object Name)
if ($skills.Count -eq 0) {
    throw "No skills with SKILL.md were found in $sourceSkills"
}

foreach ($skill in $skills) {
    $claudeLink = Join-Path $destinationRoot ".claude\skills\$($skill.Name)"
    if (Set-SkillLink $claudeLink $skill.FullName) {
        $codexLink = Join-Path $destinationRoot ".agents\skills\$($skill.Name)"
        Set-SkillLink $codexLink "..\..\.claude\skills\$($skill.Name)" | Out-Null
    }
}

$codexInstructions = Join-Path $sourceRoot '.codex\AGENTS.md'
if (-not (Test-Path -LiteralPath $codexInstructions -PathType Leaf)) {
    throw "Global instructions do not exist: $codexInstructions"
}

$codexInstructionsLink = Join-Path $destinationRoot '.codex\AGENTS.md'
if (Set-SkillLink $codexInstructionsLink $codexInstructions) {
    $claudeInstructionsLink = Join-Path $destinationRoot '.claude\CLAUDE.md'
    if (Set-SkillLink $claudeInstructionsLink '..\.codex\AGENTS.md') {
        $copilotInstructionsLink = Join-Path $destinationRoot '.copilot\copilot-instructions.md'
        Set-SkillLink $copilotInstructionsLink '..\.claude\CLAUDE.md' | Out-Null
    }
}
