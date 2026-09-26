#requires -Version 5.1
[CmdletBinding()]
param(
    [ValidateNotNullOrEmpty()]
    [string] $Destination = $env:USERPROFILE,
    [ValidateSet('Local', 'Remote')]
    [string] $Mode = 'Local',
    [ValidateNotNullOrEmpty()]
    [string] $Ref = 'master',
    [switch] $DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$destinationRoot = [System.IO.Path]::GetFullPath($Destination)
$plannedDirectories = @{}

if (-not (Test-Path -LiteralPath $destinationRoot -PathType Container)) {
    throw "Destination home directory does not exist: $destinationRoot"
}

function Get-ExistingItem {
    param([string] $Path)

    $parent = Split-Path -Parent $Path
    if (-not (Test-Path -LiteralPath $parent -PathType Container)) {
        return $null
    }
    return Get-ChildItem -LiteralPath $parent -Force |
        Where-Object { $_.Name -eq (Split-Path -Leaf $Path) } |
        Select-Object -First 1
}

function Ensure-Directory {
    param([string] $Path)

    if (Test-Path -LiteralPath $Path -PathType Container) {
        $existingDirectory = Get-ExistingItem $Path
        if ($null -ne $existingDirectory -and
            -not [string]::IsNullOrEmpty([string] $existingDirectory.LinkType)) {
            throw "Destination directory is a link: $Path"
        }
        return
    }
    if ($null -ne (Get-ExistingItem $Path)) {
        throw "Expected a directory: $Path"
    }
    if ($DryRun) {
        if (-not $plannedDirectories.ContainsKey($Path)) {
            Write-Host "Would create directory: $Path"
            $plannedDirectories[$Path] = $true
        }
    } else {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
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
    Ensure-Directory $parent
    # Enumerating the parent also finds dangling symbolic links, which Test-Path misses.
    $existing = Get-ExistingItem $LinkPath

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

function Copy-ArchiveEntry {
    param($Entry, [string] $TargetPath, [switch] $Quiet)

    Ensure-Directory (Split-Path -Parent $TargetPath)
    if ($null -ne (Get-ExistingItem $TargetPath)) {
        Write-Warning "Preserving conflicting path: $TargetPath"
        return $false
    }
    if ($DryRun) {
        if (-not $Quiet) {
            Write-Host "Would copy: $TargetPath"
        }
    } else {
        $inputStream = $Entry.Open()
        try {
            $outputStream = [System.IO.File]::Open(
                $TargetPath, [System.IO.FileMode]::CreateNew,
                [System.IO.FileAccess]::Write)
            try {
                $inputStream.CopyTo($outputStream)
            } finally {
                $outputStream.Dispose()
            }
        } finally {
            $inputStream.Dispose()
        }
        if (-not $Quiet) {
            Write-Host "Copied: $TargetPath"
        }
    }
    return $true
}

function Install-LocalSkills {
    $sourceRoot = (Resolve-Path -LiteralPath $PSScriptRoot).Path
    $sourceSkills = Join-Path $sourceRoot '.claude\skills'
    if (-not (Test-Path -LiteralPath $sourceSkills -PathType Container)) {
        throw "Skill source directory does not exist: $sourceSkills"
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
}

function Install-RemoteSkills {
    if ($Ref -notmatch '^[A-Za-z0-9._/-]+$' -or
        $Ref.StartsWith('/') -or $Ref.Contains('..')) {
        throw "Invalid GitHub ref: $Ref"
    }

    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $archivePath = [System.IO.Path]::GetTempFileName()
    try {
        $archiveUrl = "https://codeload.github.com/evandrocoan/dotfiles/zip/$Ref"
        Write-Host "Downloading $archiveUrl"
        Invoke-WebRequest -Uri $archiveUrl -OutFile $archivePath -UseBasicParsing -TimeoutSec 60
        $archive = [System.IO.Compression.ZipFile]::OpenRead($archivePath)
        try {
            $instructionEntries = @($archive.Entries | Where-Object {
                $_.FullName -cmatch '^[^/]+/\.codex/AGENTS\.md$'
            })
            if ($instructionEntries.Count -ne 1) {
                throw 'The GitHub archive must contain one .codex/AGENTS.md file.'
            }
            $instructions = $instructionEntries[0]
            $rootPrefix = $instructions.FullName.Substring(
                0, $instructions.FullName.Length - '.codex/AGENTS.md'.Length)
            $skillPrefix = "${rootPrefix}.claude/skills/"
            $skillFiles = @{}
            $skillManifests = @{}

            foreach ($entry in $archive.Entries) {
                if (-not $entry.FullName.StartsWith(
                    $skillPrefix, [System.StringComparison]::Ordinal)) {
                    continue
                }
                $suffix = $entry.FullName.Substring($skillPrefix.Length)
                $separator = $suffix.IndexOf('/')
                if ($separator -lt 1 -or $entry.Name.Length -eq 0) {
                    continue
                }
                $name = $suffix.Substring(0, $separator)
                $relativePath = $suffix.Substring($separator + 1)
                if ($name -cnotmatch '^[A-Za-z0-9][A-Za-z0-9._-]*$' -or
                    $relativePath.Contains('\') -or $relativePath.Contains(':') -or
                    @($relativePath.Split('/') | Where-Object { $_ -in @('', '.', '..') }).Count -gt 0) {
                    throw "Unsafe skill archive path: $($entry.FullName)"
                }
                if ((($entry.ExternalAttributes -shr 16) -band 0xF000) -eq 0xA000) {
                    throw "Symbolic links inside skills are not supported: $($entry.FullName)"
                }
                if (-not $skillFiles.ContainsKey($name)) {
                    $skillFiles[$name] = [System.Collections.ArrayList]::new()
                }
                [void] $skillFiles[$name].Add([pscustomobject]@{
                    Entry = $entry
                    RelativePath = $relativePath
                })
                if ($relativePath -ceq 'SKILL.md') {
                    $skillManifests[$name] = $true
                }
            }
            if ($skillManifests.Count -eq 0) {
                throw 'No skills with SKILL.md were found in the GitHub archive.'
            }

            foreach ($name in @($skillManifests.Keys | Sort-Object)) {
                $claudePath = Join-Path $destinationRoot ".claude\skills\$name"
                Ensure-Directory (Split-Path -Parent $claudePath)
                if ($null -ne (Get-ExistingItem $claudePath)) {
                    Write-Warning "Preserving conflicting path: $claudePath"
                    continue
                }
                if ($DryRun) {
                    Write-Host "Would copy skill: $claudePath"
                } else {
                    New-Item -ItemType Directory -Path $claudePath | Out-Null
                    foreach ($file in $skillFiles[$name]) {
                        $filePath = Join-Path $claudePath ($file.RelativePath.Replace('/', '\'))
                        if (-not (Copy-ArchiveEntry $file.Entry $filePath -Quiet)) {
                            throw "Could not complete copied skill: $claudePath"
                        }
                    }
                    Write-Host "Copied skill: $claudePath"
                }
                $codexLink = Join-Path $destinationRoot ".agents\skills\$name"
                Set-SkillLink $codexLink "..\..\.claude\skills\$name" | Out-Null
            }

            foreach ($relativePath in @(
                '.codex\AGENTS.md', '.claude\CLAUDE.md',
                '.copilot\copilot-instructions.md')) {
                Copy-ArchiveEntry $instructions (Join-Path $destinationRoot $relativePath) | Out-Null
            }
        } finally {
            $archive.Dispose()
        }
    } finally {
        Remove-Item -LiteralPath $archivePath -Force
    }
}

if ($Mode -eq 'Remote') {
    Install-RemoteSkills
} else {
    Install-LocalSkills
}
