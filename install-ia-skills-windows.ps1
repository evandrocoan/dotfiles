#requires -Version 5.1
<#
.SYNOPSIS
Installs shared Claude, Codex, and Copilot skills on Windows.
.DESCRIPTION
Local mode links this checkout into the selected Windows profile. Remote mode
downloads a GitHub revision and copies its skills. Existing paths are preserved
unless Force is specified. Managed skills are recorded for later cleanup.
.PARAMETER Destination
Windows user home directory. Defaults to USERPROFILE.
.PARAMETER Mode
Local or Remote. Defaults to Local.
.PARAMETER Ref
GitHub branch or tag for Remote mode. Defaults to master.
.PARAMETER Force
Replace existing selected paths and prune unchanged discontinued managed skills.
.PARAMETER DryRun
Preview changes. Remote mode still downloads the archive.
#>
[CmdletBinding()]
param(
    [ValidateNotNullOrEmpty()]
    [string] $Destination = $env:USERPROFILE,
    [ValidateSet('Local', 'Remote')]
    [string] $Mode = 'Local',
    [ValidateNotNullOrEmpty()]
    [string] $Ref = 'master',
    [switch] $Force,
    [switch] $DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$destinationRoot = [System.IO.Path]::GetFullPath($Destination)
$plannedDirectories = @{}
$repository = 'evandrocoan/dotfiles'
$statePath = Join-Path $destinationRoot '.local\state\install-ia-skills\windows-manifest.json'
$previousEntries = @{}
$nextEntries = [ordered]@{}
$desiredSkills = @{}
$installedCount = 0
$skippedCount = 0
$prunedCount = 0
$disownedCount = 0

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

function Test-IsLink {
    param($Item)

    return $null -ne $Item -and
        -not [string]::IsNullOrEmpty([string] $Item.LinkType)
}

function Assert-SafeDestinationPath {
    param([string] $Path)

    $fullPath = [System.IO.Path]::GetFullPath($Path)
    $prefix = $destinationRoot.TrimEnd('\') + '\'
    if (-not $fullPath.StartsWith(
        $prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Path is outside the selected destination: $fullPath"
    }
    $parent = Split-Path -Parent $fullPath
    while ($parent.Length -ge $destinationRoot.Length) {
        if (Test-IsLink (Get-ExistingItem $parent)) {
            throw "Destination parent is a link: $parent"
        }
        if ($parent -ieq $destinationRoot) {
            break
        }
        $parent = Split-Path -Parent $parent
    }
}

function Assert-TreeHasNoLinks {
    param([string] $Path)

    $pending = [System.Collections.Stack]::new()
    $pending.Push($Path)
    while ($pending.Count -gt 0) {
        foreach ($item in Get-ChildItem -LiteralPath $pending.Pop() -Force) {
            if (Test-IsLink $item) {
                throw "Refusing to remove a directory containing a link: $($item.FullName)"
            }
            if ($item.PSIsContainer) {
                $pending.Push($item.FullName)
            }
        }
    }
}

function Remove-InstalledPath {
    param([string] $Path)

    Assert-SafeDestinationPath $Path
    $item = Get-ExistingItem $Path
    if ($null -eq $item) {
        return
    }
    if ($item.PSIsContainer -and -not (Test-IsLink $item)) {
        Assert-TreeHasNoLinks $Path
    }
    if ($DryRun) {
        return
    }
    if ($item.PSIsContainer -and -not (Test-IsLink $item)) {
        Remove-Item -LiteralPath $Path -Recurse -Force
    } else {
        Remove-Item -LiteralPath $Path -Force
    }
}

function Get-SkillDigest {
    param([string] $Path)

    $pending = [System.Collections.Stack]::new()
    $entries = [System.Collections.ArrayList]::new()
    $pending.Push($Path)
    while ($pending.Count -gt 0) {
        foreach ($item in Get-ChildItem -LiteralPath $pending.Pop() -Force) {
            if (Test-IsLink $item) {
                return $null
            }
            $relativePath = $item.FullName.Substring($Path.Length + 1).Replace('\', '/')
            if ($item.PSIsContainer) {
                $pending.Push($item.FullName)
                [void] $entries.Add([pscustomobject]@{
                    Path = $item.FullName
                    RelativePath = $relativePath
                    Kind = 'directory'
                })
            } else {
                [void] $entries.Add([pscustomobject]@{
                    Path = $item.FullName
                    RelativePath = $relativePath
                    Kind = 'file'
                })
            }
        }
    }
    $records = foreach ($entry in $entries | Sort-Object RelativePath) {
        if ($entry.Kind -eq 'directory') {
            "d`t$($entry.RelativePath)`n"
        } else {
            $fileHash = (Get-FileHash -LiteralPath $entry.Path -Algorithm SHA256).Hash.ToLowerInvariant()
            "f`t$($entry.RelativePath)`t$fileHash`n"
        }
    }
    $bytes = [System.Text.UTF8Encoding]::new($false).GetBytes(($records -join ''))
    $hash = [System.Security.Cryptography.SHA256]::Create()
    try {
        return [System.BitConverter]::ToString($hash.ComputeHash($bytes)).Replace('-', '').ToLowerInvariant()
    } finally {
        $hash.Dispose()
    }
}

function Add-ManagedEntry {
    param([string] $Type, [string] $Name, [string] $Kind,
        [string] $Digest = '', [string] $Target = '')

    $key = "$Type=$Name"
    $nextEntries[$key] = [ordered]@{
        type = $Type
        name = $Name
        kind = $Kind
        digest = $Digest
        target = $Target
    }
}

function Preserve-PreviousEntry {
    param([string] $Key)

    if ($previousEntries.ContainsKey($Key)) {
        $nextEntries[$Key] = $previousEntries[$Key]
    }
}

function Read-InstallState {
    $item = Get-ExistingItem $statePath
    if ($null -eq $item) {
        return
    }
    if ($item.PSIsContainer -or (Test-IsLink $item)) {
        throw "Invalid control file: $statePath"
    }
    $state = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
    if ($state.format -ne 1 -or $state.repository -ne $repository -or
        $null -eq $state.entries) {
        throw "Invalid control file header: $statePath"
    }
    foreach ($entry in $state.entries) {
        $name = [string] $entry.name
        $type = [string] $entry.type
        $kind = [string] $entry.kind
        if ($name -cnotmatch '^[A-Za-z0-9][A-Za-z0-9._-]*$' -or
            $type -notin @('canonical', 'shared-link') -or
            $kind -notin @('copy', 'link')) {
            throw "Invalid managed entry in $statePath"
        }
        if ($type -eq 'canonical' -and $kind -eq 'copy' -and
            [string] $entry.digest -cnotmatch '^[0-9a-f]{64}$') {
            throw "Invalid managed digest in $statePath"
        }
        if ($type -eq 'canonical' -and $kind -eq 'link' -and
            -not [System.IO.Path]::IsPathRooted([string] $entry.target)) {
            throw "Invalid managed link in $statePath"
        }
        if ($type -eq 'shared-link' -and $kind -ne 'link') {
            throw "Invalid managed shared link in $statePath"
        }
        $key = "$type=$name"
        if ($previousEntries.ContainsKey($key)) {
            throw "Duplicate managed entry in $statePath"
        }
        $previousEntries[$key] = $entry
    }
}

function Write-InstallState {
    if ($DryRun) {
        return
    }
    $parent = Split-Path -Parent $statePath
    Ensure-Directory $parent
    $existingState = Get-ExistingItem $statePath
    if ($null -ne $existingState -and
        ($existingState.PSIsContainer -or (Test-IsLink $existingState))) {
        throw "Invalid control file: $statePath"
    }
    $temporaryPath = Join-Path $parent ('manifest.tmp.' + [guid]::NewGuid().ToString('N'))
    try {
        $state = [ordered]@{
            format = 1
            repository = $repository
            lastSuccessfulRef = if ($Mode -eq 'Remote') { $Ref } else { 'local' }
            entries = @($nextEntries.Values)
        }
        $json = ConvertTo-Json -InputObject $state -Depth 6
        [System.IO.File]::WriteAllText(
            $temporaryPath, $json + [Environment]::NewLine,
            [System.Text.UTF8Encoding]::new($false))
        Move-Item -LiteralPath $temporaryPath -Destination $statePath -Force
    } finally {
        if (Test-Path -LiteralPath $temporaryPath) {
            Remove-Item -LiteralPath $temporaryPath -Force
        }
    }
    Write-Host "Updated control file: $statePath"
}

function Ensure-Directory {
    param([string] $Path)

    Assert-SafeDestinationPath $Path
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
    param([string] $LinkPath, [string] $Target,
        [string] $ManagedType = '', [string] $ManagedName = '')

    $parent = Split-Path -Parent $LinkPath
    Ensure-Directory $parent
    # Enumerating the parent also finds dangling symbolic links, which Test-Path misses.
    $existing = Get-ExistingItem $LinkPath
    $managedKey = if ($ManagedType) { "$ManagedType=$ManagedName" } else { '' }

    if ($null -ne $existing) {
        $existingTarget = @($existing.Target) | Select-Object -First 1
        if (-not $Force) {
            $script:skippedCount++
            if ($managedKey) {
                Preserve-PreviousEntry $managedKey
            }
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
        Write-Host "Replacing link path: $LinkPath"
        Remove-InstalledPath $LinkPath
    }

    if ($DryRun) {
        Write-Host "Would link: $LinkPath -> $Target"
    } else {
        New-Item -ItemType SymbolicLink -Path $LinkPath -Target $Target | Out-Null
        Write-Host "Linked: $LinkPath -> $Target"
    }
    if ($managedKey) {
        Add-ManagedEntry $ManagedType $ManagedName 'link' '' $Target
    }
    $script:installedCount++
    return $true
}

function Copy-ArchiveEntry {
    param($Entry, [string] $TargetPath, [switch] $Quiet, [switch] $Fresh)

    Ensure-Directory (Split-Path -Parent $TargetPath)
    if ($null -ne (Get-ExistingItem $TargetPath)) {
        if ($Fresh) {
            throw "Duplicate path inside a skill archive: $TargetPath"
        }
        if (-not $Force) {
            Write-Warning "Preserving conflicting path: $TargetPath"
            $script:skippedCount++
            return $false
        }
        Write-Host "Replacing file path: $TargetPath"
        Remove-InstalledPath $TargetPath
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
    if (-not $Fresh) {
        $script:installedCount++
    }
    return $true
}

function Install-LocalSkills {
    $sourceRoot = (Resolve-Path -LiteralPath $PSScriptRoot).Path
    if ($sourceRoot -ieq $destinationRoot) {
        throw 'Local source and destination must differ to protect the checkout.'
    }
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
        $desiredSkills[$skill.Name] = $true
        $claudeLink = Join-Path $destinationRoot ".claude\skills\$($skill.Name)"
        Set-SkillLink $claudeLink $skill.FullName 'canonical' $skill.Name | Out-Null
        $codexLink = Join-Path $destinationRoot ".agents\skills\$($skill.Name)"
        Set-SkillLink $codexLink "..\..\.claude\skills\$($skill.Name)" 'shared-link' $skill.Name | Out-Null
    }

    $codexInstructions = Join-Path $sourceRoot '.codex\AGENTS.md'
    if (-not (Test-Path -LiteralPath $codexInstructions -PathType Leaf)) {
        throw "Global instructions do not exist: $codexInstructions"
    }
    $codexInstructionsLink = Join-Path $destinationRoot '.codex\AGENTS.md'
    Set-SkillLink $codexInstructionsLink $codexInstructions | Out-Null
    $claudeInstructionsLink = Join-Path $destinationRoot '.claude\CLAUDE.md'
    Set-SkillLink $claudeInstructionsLink '..\.codex\AGENTS.md' | Out-Null
    $copilotInstructionsLink = Join-Path $destinationRoot '.copilot\copilot-instructions.md'
    Set-SkillLink $copilotInstructionsLink '..\.claude\CLAUDE.md' | Out-Null
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
                $desiredSkills[$name] = $true
                $claudePath = Join-Path $destinationRoot ".claude\skills\$name"
                Ensure-Directory (Split-Path -Parent $claudePath)
                if ($null -ne (Get-ExistingItem $claudePath)) {
                    if (-not $Force) {
                        Write-Warning "Preserving conflicting path: $claudePath"
                        $script:skippedCount++
                        Preserve-PreviousEntry "canonical=$name"
                        $codexLink = Join-Path $destinationRoot ".agents\skills\$name"
                        Set-SkillLink $codexLink "..\..\.claude\skills\$name" 'shared-link' $name | Out-Null
                        continue
                    }
                    Write-Host "Replacing canonical skill: $claudePath"
                    Remove-InstalledPath $claudePath
                }
                if ($DryRun) {
                    Write-Host "Would copy skill: $claudePath"
                } else {
                    New-Item -ItemType Directory -Path $claudePath | Out-Null
                    foreach ($file in $skillFiles[$name]) {
                        $filePath = Join-Path $claudePath ($file.RelativePath.Replace('/', '\'))
                        Copy-ArchiveEntry $file.Entry $filePath -Quiet -Fresh | Out-Null
                    }
                    Write-Host "Copied skill: $claudePath"
                }
                $digest = if ($DryRun) { '0' * 64 } else { Get-SkillDigest $claudePath }
                if ($null -eq $digest) {
                    throw "Copied skill contains a symbolic link: $claudePath"
                }
                Add-ManagedEntry 'canonical' $name 'copy' $digest
                $script:installedCount++
                $codexLink = Join-Path $destinationRoot ".agents\skills\$name"
                Set-SkillLink $codexLink "..\..\.claude\skills\$name" 'shared-link' $name | Out-Null
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

function Prune-DiscontinuedSkills {
    $previousNames = @($previousEntries.Values | ForEach-Object { $_.name } | Sort-Object -Unique)
    foreach ($name in $previousNames) {
        if ($desiredSkills.ContainsKey($name)) {
            continue
        }
        $canonicalKey = "canonical=$name"
        $sharedKey = "shared-link=$name"
        $canonical = if ($previousEntries.ContainsKey($canonicalKey)) {
            $previousEntries[$canonicalKey]
        } else { $null }
        $shared = if ($previousEntries.ContainsKey($sharedKey)) {
            $previousEntries[$sharedKey]
        } else { $null }
        if (-not $Force) {
            Write-Host "Preserved discontinued managed skill: $name (use -Force to remove)"
            Preserve-PreviousEntry $canonicalKey
            Preserve-PreviousEntry $sharedKey
            if ($null -ne $canonical) { $script:skippedCount++ }
            if ($null -ne $shared) { $script:skippedCount++ }
            continue
        }

        $canonicalPath = Join-Path $destinationRoot ".claude\skills\$name"
        $sharedPath = Join-Path $destinationRoot ".agents\skills\$name"
        $canonicalItem = Get-ExistingItem $canonicalPath
        $sharedItem = Get-ExistingItem $sharedPath
        $changed = $false
        if ($null -ne $canonical -and $null -ne $canonicalItem) {
            if ($canonical.kind -eq 'link') {
                $actualTarget = @($canonicalItem.Target) | Select-Object -First 1
                if (-not (Test-IsLink $canonicalItem) -or $null -eq $actualTarget -or
                    (Get-NormalizedTarget $canonicalPath $actualTarget) -ine
                    (Get-NormalizedTarget $canonicalPath ([string] $canonical.target))) {
                    $changed = $true
                }
            } elseif ($canonicalItem.PSIsContainer -and -not (Test-IsLink $canonicalItem)) {
                $actualDigest = Get-SkillDigest $canonicalPath
                if ($actualDigest -cne [string] $canonical.digest) {
                    $changed = $true
                }
            } else {
                $changed = $true
            }
        }
        if ($null -ne $shared -and $null -ne $sharedItem) {
            $actualTarget = @($sharedItem.Target) | Select-Object -First 1
            $expectedTarget = "..\..\.claude\skills\$name"
            if (-not (Test-IsLink $sharedItem) -or $null -eq $actualTarget -or
                (Get-NormalizedTarget $sharedPath $actualTarget) -ine
                (Get-NormalizedTarget $sharedPath $expectedTarget)) {
                $changed = $true
            }
        }
        if ($changed) {
            Write-Warning "Preserved modified discontinued skill and removed it from the control file: $name"
            $script:disownedCount++
            continue
        }

        if ($null -ne $canonical) {
            Write-Host "Removing discontinued managed canonical skill: $canonicalPath"
            Remove-InstalledPath $canonicalPath
            $script:prunedCount++
        }
        if ($null -ne $shared) {
            Write-Host "Removing discontinued managed shared link: $sharedPath"
            Remove-InstalledPath $sharedPath
            $script:prunedCount++
        }
    }
}

Read-InstallState
if ($Mode -eq 'Remote') {
    Install-RemoteSkills
} else {
    Install-LocalSkills
}
Prune-DiscontinuedSkills
Write-InstallState

if ($DryRun) {
    Write-Host "Dry run complete: $installedCount change(s), $prunedCount managed item(s) would be pruned, $disownedCount modified skill(s) would be preserved and disowned, $skippedCount existing item(s) skipped."
} else {
    Write-Host "Installation complete: $installedCount change(s), $prunedCount managed item(s) pruned, $disownedCount modified skill(s) preserved and disowned, $skippedCount existing item(s) skipped."
}
