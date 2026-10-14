$ErrorActionPreference = 'Stop'
$required = @('aws', 'sam', 'python')
$missing = @()
foreach ($name in $required) { if (-not (Get-Command $name -ErrorAction SilentlyContinue)) { $missing += $name } }
if ($missing.Count) { throw "Missing required command(s): $($missing -join ', '). Install AWS CLI v2, AWS SAM CLI, and Python 3.12+." }
aws --version
sam --version
python --version
Write-Host 'Prerequisites found. Configure a named AWS profile before deployment.'
