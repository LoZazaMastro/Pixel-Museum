# Run only after the verified checkpoint and explicit user shutdown request.
param([int]$DelaySeconds = 30)
$ErrorActionPreference = 'Stop'
$museumRoot = Split-Path -Parent $PSScriptRoot
$statePath = Join-Path $museumRoot 'build/overnight-checkpoint-state.json'
$receiptPath = Join-Path $museumRoot 'build/shutdown-request.json'
Start-Sleep -Seconds $DelaySeconds
$checkpointState = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
if ($checkpointState.status -ne 'verified_checkpoint_ready_for_shutdown' -or
    $checkpointState.shutdown_authorized -ne $true -or
    $checkpointState.all_agents_frozen -ne $true) {
    throw 'The final checkpoint is not marked saved and verified; shutdown aborted.'
}
$transferPath = Join-Path $museumRoot $checkpointState.transfer_receipt
$transferReceipt = Get-Content -LiteralPath $transferPath -Raw | ConvertFrom-Json
if ($transferReceipt.status -ne 'updated_and_byte_verified') {
    throw 'The console transfer is not verified; shutdown aborted.'
}
$shutdownRecord = [ordered]@{
    requested_utc = [DateTime]::UtcNow.ToString('o')
    authorized_by = 'Explicit user request after verified build and FTP transfer'
    command = 'shutdown.exe /s /t 0'
    forced_application_close = $false
    transfer_receipt = $checkpointState.transfer_receipt
    status = 'requesting_shutdown'
}
$shutdownRecord | ConvertTo-Json | Set-Content -LiteralPath $receiptPath -Encoding UTF8
& "$env:SystemRoot\System32\shutdown.exe" /s /t 0
$shutdownRecord['exit_code'] = $LASTEXITCODE
$shutdownRecord['status'] = if ($LASTEXITCODE -eq 0) { 'shutdown_request_accepted' } else { 'shutdown_request_failed' }
$shutdownRecord | ConvertTo-Json | Set-Content -LiteralPath $receiptPath -Encoding UTF8
