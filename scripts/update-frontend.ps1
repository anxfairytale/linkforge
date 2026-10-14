param([string]$Profile = 'default', [string]$Region = '')
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$args = @('--stack-name','aws-url-shortener','--query','Stacks[0].Outputs','--output','json','--profile',$Profile)
if ($Region) { $args += @('--region',$Region) }
$outputs = aws cloudformation describe-stacks @args | ConvertFrom-Json
if ($LASTEXITCODE -ne 0 -or -not $outputs) { throw 'Could not read stack outputs. Deploy the backend first.' }
$api = ($outputs | Where-Object OutputKey -eq 'ApiBaseUrl').OutputValue
$bucket = ($outputs | Where-Object OutputKey -eq 'FrontendBucketName').OutputValue
$website = ($outputs | Where-Object OutputKey -eq 'FrontendWebsiteUrl').OutputValue
if (-not $api -or -not $bucket) { throw 'Required stack outputs are missing.' }
Set-Content -LiteralPath (Join-Path $repo 'frontend/config.js') -Value "window.APP_CONFIG = { API_BASE_URL: `"$api`" };`n" -Encoding utf8
$sync = @('s3','sync',(Join-Path $repo 'frontend'),"s3://$bucket",'--exclude','config.js.example','--profile',$Profile)
if ($Region) { $sync += @('--region',$Region) }
aws @sync
if ($LASTEXITCODE -ne 0) { throw 'Frontend upload failed.' }
Write-Host "Frontend: $website"
Write-Host "API: $api"
