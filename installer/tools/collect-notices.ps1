[CmdletBinding()]
param([string]$CargoPath = (Join-Path $env:USERPROFILE '.cargo\bin\cargo.exe'))
$ErrorActionPreference = 'Stop'
$installerRoot = Split-Path -Parent $PSScriptRoot
$manifest = Join-Path $installerRoot 'Cargo.toml'
$metadataText = & $CargoPath metadata --manifest-path $manifest --locked --filter-platform x86_64-pc-windows-msvc --format-version 1
if ($LASTEXITCODE -ne 0) { throw 'Cannot inspect installer dependencies.' }
$metadata = $metadataText | ConvertFrom-Json
$nodes = @{}
foreach ($node in $metadata.resolve.nodes) { $nodes[$node.id] = $node }
$reachable = [Collections.Generic.HashSet[string]]::new()
$queue = [Collections.Generic.Queue[string]]::new()
$queue.Enqueue($metadata.resolve.root)
while ($queue.Count -gt 0) {
    $id = $queue.Dequeue()
    if ($reachable.Add($id)) { foreach ($dependency in $nodes[$id].dependencies) { $queue.Enqueue($dependency) } }
}
$licenseRoot = Join-Path $installerRoot 'licenses'
$upstream = Join-Path $licenseRoot 'upstream'
New-Item -ItemType Directory -Path $upstream -Force | Out-Null
$utf8 = [Text.UTF8Encoding]::new($false)
$notice = [Text.StringBuilder]::new()
[void]$notice.AppendLine('Pixel Museum Setup - third-party software and font notices')
[void]$notice.AppendLine('Generated from Cargo.lock for x86_64-pc-windows-msvc. Includes build dependencies.')
[void]$notice.AppendLine('The museum application and collection have additional notices shown separately.')

foreach ($package in ($metadata.packages | Where-Object { $reachable.Contains($_.id) -and $_.source } | Sort-Object name, version)) {
    $directory = Split-Path -Parent $package.manifest_path
    $texts = @(Get-ChildItem -LiteralPath $directory -File | Where-Object { $_.Name -match '^(LICENSE|LICENCE|COPYING|NOTICE|UNLICENSE|COPYRIGHT)([._-].*)?$' })
    $fontDirectory = Join-Path $directory 'fonts'
    if (Test-Path -LiteralPath $fontDirectory) { $texts += @(Get-ChildItem -LiteralPath $fontDirectory -File -Filter '*.txt') }
    if ($texts.Count -eq 0 -or $package.name -eq 'epaint_default_fonts') {
        $repository = $package.repository.TrimEnd('/') -replace '/tree/.*$', ''
        $vcsPath = Join-Path $directory '.cargo_vcs_info.json'
        if (-not (Test-Path -LiteralPath $vcsPath) -or $repository -notmatch '^https://github.com/[^/]+/[^/]+$') { throw "No licence text found for $($package.name)." }
        $commit = (Get-Content -LiteralPath $vcsPath -Raw | ConvertFrom-Json).git.sha1
        if ($repository -eq 'https://github.com/emilk/egui') { $commit = '3c6eb8261c3293ad9c7ea1ed58487e038860ebef' }
        $names = if ($package.license -match 'MIT') { @('LICENSE-MIT', 'LICENSE-APACHE') } else { @('LICENSE') }
        foreach ($name in $names) {
            $output = Join-Path $upstream ($package.name + '-' + $package.version + '-' + $name + '.txt')
            if (-not (Test-Path -LiteralPath $output)) {
                $url = $repository.Replace('https://github.com/', 'https://raw.githubusercontent.com/') + '/' + $commit + '/' + $name
                Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $output
            }
            $texts += Get-Item -LiteralPath $output
        }
    }
    [void]$notice.AppendLine("`n======================================================================")
    [void]$notice.AppendLine("$($package.name) $($package.version)")
    [void]$notice.AppendLine("SPDX: $($package.license)")
    [void]$notice.AppendLine("Source: $($package.repository)")
    foreach ($text in $texts) {
        [void]$notice.AppendLine("`n--- $($text.Name) ---")
        [void]$notice.AppendLine([IO.File]::ReadAllText($text.FullName))
    }
}
$outputPath = Join-Path $licenseRoot 'THIRD-PARTY-NOTICES.txt'
[IO.File]::WriteAllText($outputPath, $notice.ToString(), $utf8)
Get-Item -LiteralPath $outputPath | Select-Object FullName, Length
