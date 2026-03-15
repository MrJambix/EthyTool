# EthyTool — Add firewall rules (called by install_all.bat)
# Receives exe path via temp file to avoid batch parsing issues with parentheses in path

param([string]$PathFile)

$exe = if ($PathFile -and (Test-Path $PathFile)) { (Get-Content $PathFile -Raw).Trim() } else { $null }
if (-not $exe -or -not (Test-Path $exe)) {
    Write-Host "    EthyTool.exe path invalid or file not found."
    exit 1
}

$in = Get-NetFirewallRule -DisplayName 'EthyTool Inbound' -ErrorAction SilentlyContinue
if ($in) {
    Write-Host "    Rules already exist."
} else {
    New-NetFirewallRule -DisplayName 'EthyTool Inbound' -Direction Inbound -Program $exe -Action Allow -Profile Any | Out-Null
    New-NetFirewallRule -DisplayName 'EthyTool Outbound' -Direction Outbound -Program $exe -Action Allow -Profile Any | Out-Null
    Write-Host "    Added inbound and outbound rules."
}
