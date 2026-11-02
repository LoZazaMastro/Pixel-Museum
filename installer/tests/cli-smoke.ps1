[CmdletBinding()]
param([string]$SetupPath = (Join-Path $PSScriptRoot '..\target\debug\pixel-museum-setup.exe'))
$ErrorActionPreference = 'Stop'
$SetupPath = (Resolve-Path -LiteralPath $SetupPath).Path
$root = Join-Path $PSScriptRoot ('..\test-output\cli-smoke-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $root -Force | Out-Null
$root = (Resolve-Path -LiteralPath $root).Path
$utf8 = [Text.UTF8Encoding]::new($false)
Add-Type -AssemblyName System.IO.Compression.FileSystem
$app = Join-Path $root 'app'
$collection = Join-Path $root 'collection'
New-Item -ItemType Directory -Path $app, (Join-Path $collection 'assets\images') -Force | Out-Null
[IO.File]::WriteAllText((Join-Path $app 'Pixel Museum.exe'), 'fixture', $utf8)
[IO.File]::WriteAllText((Join-Path $app 'LICENSE'), 'GPL-3.0-or-later fixture', $utf8)
[IO.File]::WriteAllText((Join-Path $app 'THIRD_PARTY_NOTICES.md'), 'Fixture notices', $utf8)
[IO.File]::WriteAllText((Join-Path $collection 'assets\images\manifest.json'), '{"fixture":true}', $utf8)
$appZip = Join-Path $root 'app.zip'
$collectionZip = Join-Path $root 'collection.zip'
[IO.Compression.ZipFile]::CreateFromDirectory($app, $appZip)
[IO.Compression.ZipFile]::CreateFromDirectory($collection, $collectionZip)
function Package([string]$Id, [string]$Kind, [string]$Zip, [string]$Target) {
    $archive = [IO.Compression.ZipFile]::OpenRead($Zip)
    try { $unpacked = ($archive.Entries | Measure-Object -Property Length -Sum).Sum } finally { $archive.Dispose() }
    return @{ id = $Id; kind = $Kind; format = 'zip'; filename = [IO.Path]::GetFileName($Zip); sha256 = (Get-FileHash -LiteralPath $Zip -Algorithm SHA256).Hash.ToLowerInvariant(); bytes = (Get-Item -LiteralPath $Zip).Length; unpacked_bytes = [long]$unpacked; target = $Target }
}
$manifest = @{ schema_version = 1; version = 'local-test'; executable = 'Pixel Museum.exe'; packages = @((Package 'app' 'app' $appZip '.'), (Package 'collection' 'collection' $collectionZip 'collection')) }
$manifestPath = Join-Path $root 'windows-manifest.json'
[IO.File]::WriteAllText($manifestPath, ($manifest | ConvertTo-Json -Depth 8), $utf8)
$destination = Join-Path $root 'Pixel Museum'
& $SetupPath --validate-manifest --manifest $manifestPath | Out-Host
if ($LASTEXITCODE -ne 0) { throw 'Manifest validation failed.' }
& $SetupPath --headless --portable --manifest $manifestPath --install-dir $destination --language it | Out-Host
if ($LASTEXITCODE -eq 0 -or (Test-Path -LiteralPath $destination)) { throw 'Setup did not enforce licence acceptance.' }
& $SetupPath --headless --portable --accept-license --manifest $manifestPath --install-dir $destination --language it | Out-Host
if ($LASTEXITCODE -ne 0) { throw 'Headless local installation failed.' }
if (-not (Test-Path -LiteralPath (Join-Path $destination 'Pixel Museum.exe'))) { throw 'Application is missing.' }
if (-not (Test-Path -LiteralPath (Join-Path $destination 'collection\assets\images\manifest.json'))) { throw 'Collection is missing.' }
if (Test-Path -LiteralPath (Join-Path $destination 'preferences.json')) {
    $prefs = Get-Content -LiteralPath (Join-Path $destination 'preferences.json') -Raw | ConvertFrom-Json
    if ($prefs.language_chosen -or $prefs.language) { throw 'Setup preselected the app language.' }
}
& $SetupPath --headless --portable --accept-license --manifest $manifestPath --install-dir $destination | Out-Host
if ($LASTEXITCODE -eq 0) { throw 'Setup replaced an existing nonempty folder.' }
Write-Output "CLI smoke passed: $destination"
