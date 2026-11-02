[CmdletBinding()]
param(
    [string]$ManifestPath,
    [string]$ManifestUrl,
    [string]$ManifestSha256,
    [string]$OutputDirectory,
    [string]$TargetDirectory,
    [switch]$SkipTests,
    [switch]$DebugBuild
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$cargoManifest = Join-Path $projectRoot 'installer\Cargo.toml'
if (-not $TargetDirectory) { $TargetDirectory = Join-Path $projectRoot 'installer\target' }
if (-not $OutputDirectory) { $OutputDirectory = Join-Path $projectRoot 'dist\windows-installer' }
$cargoCommand = Get-Command cargo.exe -ErrorAction SilentlyContinue
$cargoExe = if ($cargoCommand) { $cargoCommand.Source } else { Join-Path $env:USERPROFILE '.cargo\bin\cargo.exe' }
if (-not (Test-Path -LiteralPath $cargoExe)) { throw 'Rust is required. Install a current stable Rust MSVC toolchain from https://rustup.rs/.' }

if ($ManifestPath -and $ManifestUrl) { throw 'Use either -ManifestPath to embed a manifest or -ManifestUrl with a pinned SHA-256.' }
if ($ManifestUrl -and $ManifestSha256 -notmatch '^[a-fA-F0-9]{64}$') { throw '-ManifestUrl requires -ManifestSha256.' }
if ($ManifestSha256 -and -not $ManifestUrl) { throw '-ManifestSha256 is only used with -ManifestUrl.' }
if ($ManifestPath) { $ManifestPath = (Resolve-Path -LiteralPath $ManifestPath).Path }

$oldPath = $env:PIXEL_MUSEUM_MANIFEST_PATH
$oldUrl = $env:PIXEL_MUSEUM_MANIFEST_URL
$oldHash = $env:PIXEL_MUSEUM_MANIFEST_SHA256
$oldRustFlags = $env:RUSTFLAGS
$oldEncodedRustFlags = $env:CARGO_ENCODED_RUSTFLAGS
try {
    $env:PIXEL_MUSEUM_MANIFEST_PATH = $ManifestPath
    $env:PIXEL_MUSEUM_MANIFEST_URL = $ManifestUrl
    $env:PIXEL_MUSEUM_MANIFEST_SHA256 = $ManifestSha256
    # Setup must start on a clean Windows PC before any VC redistributable exists.
    if ($oldEncodedRustFlags) {
        $flagSeparator = [char]31
        $env:CARGO_ENCODED_RUSTFLAGS = $oldEncodedRustFlags + $flagSeparator + '-C' + $flagSeparator + 'target-feature=+crt-static'
    } else {
        $env:RUSTFLAGS = (($oldRustFlags + ' -C target-feature=+crt-static').Trim())
    }
    if (-not $SkipTests) {
        & $cargoExe test --manifest-path $cargoManifest --target-dir $TargetDirectory --locked
        if ($LASTEXITCODE -ne 0) { throw 'Installer tests failed.' }
    }
    # Use the same Rust validation that setup uses, before producing a release artifact.
    if ($ManifestPath) {
        & $cargoExe run --manifest-path $cargoManifest --target-dir $TargetDirectory --locked -- --validate-manifest --manifest $ManifestPath
        if ($LASTEXITCODE -ne 0) { throw 'The release manifest is invalid.' }
    }
    $arguments = @('build', '--manifest-path', $cargoManifest, '--target-dir', $TargetDirectory, '--locked')
    if (-not $DebugBuild) { $arguments += '--release' }
    & $cargoExe @arguments
    if ($LASTEXITCODE -ne 0) { throw 'Installer build failed.' }
    $profile = if ($DebugBuild) { 'debug' } else { 'release' }
    $binary = Join-Path $TargetDirectory "$profile\pixel-museum-setup.exe"
    New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
    $outputExe = Join-Path $OutputDirectory 'Pixel-Museum-Setup.exe'
    Copy-Item -LiteralPath $binary -Destination $outputExe -Force
    Copy-Item -LiteralPath (Join-Path $projectRoot 'LICENSE') -Destination (Join-Path $OutputDirectory 'LICENSE') -Force
    Copy-Item -LiteralPath (Join-Path $projectRoot 'THIRD_PARTY_NOTICES.md') -Destination (Join-Path $OutputDirectory 'THIRD_PARTY_NOTICES.md') -Force
    Copy-Item -LiteralPath (Join-Path $projectRoot 'installer\licenses\THIRD-PARTY-NOTICES.txt') -Destination (Join-Path $OutputDirectory 'INSTALLER-THIRD-PARTY-NOTICES.txt') -Force
    Copy-Item -LiteralPath (Join-Path $projectRoot 'installer\assets\Inter-LICENSE.txt') -Destination (Join-Path $OutputDirectory 'Inter-LICENSE.txt') -Force
    $digest = (Get-FileHash -LiteralPath $outputExe -Algorithm SHA256).Hash.ToLowerInvariant()
    [IO.File]::WriteAllText((Join-Path $OutputDirectory 'Pixel-Museum-Setup.exe.sha256'), "$digest  Pixel-Museum-Setup.exe`n", [Text.UTF8Encoding]::new($false))
    if (-not $ManifestPath -and -not $ManifestUrl) {
        Write-Warning 'Development setup built without a public Windows release manifest. It will request a local windows-manifest.json.'
    }
    Get-Item -LiteralPath $outputExe | Select-Object FullName, Length
    Write-Output "SHA-256: $digest"
}
finally {
    $env:PIXEL_MUSEUM_MANIFEST_PATH = $oldPath
    $env:PIXEL_MUSEUM_MANIFEST_URL = $oldUrl
    $env:PIXEL_MUSEUM_MANIFEST_SHA256 = $oldHash
    $env:RUSTFLAGS = $oldRustFlags
    $env:CARGO_ENCODED_RUSTFLAGS = $oldEncodedRustFlags
}
