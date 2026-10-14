param(
  [Parameter(Mandatory=$true)][ValidatePattern('^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$')][string]$BucketName,
  [string]$Profile = 'default', [string]$Region = '', [switch]$SkipConfirm
)
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
& "$PSScriptRoot/check-prerequisites.ps1"
$awsArgs = @('--profile', $Profile)
if ($Region) { $awsArgs += @('--region', $Region) }
aws sts get-caller-identity @awsArgs | Out-Null
if ($LASTEXITCODE -ne 0) { throw "AWS credentials are unavailable for profile '$Profile'." }
$location = aws s3api get-bucket-location --bucket $BucketName @awsArgs 2>$null | ConvertFrom-Json -ErrorAction SilentlyContinue
if ($LASTEXITCODE -eq 0) { $bucketRegion = if ($location.LocationConstraint) {$location.LocationConstraint} else {'us-east-1'} }
else { $bucketRegion = if ($Region) {$Region} else {(aws configure get region --profile $Profile)} }
if (-not $bucketRegion) { throw 'Pass -Region or configure a default region for this AWS profile.' }
$origin = "http://$BucketName.s3-website-$bucketRegion.amazonaws.com"
sam build --template-file (Join-Path $repo 'template.yaml')
if ($LASTEXITCODE -ne 0) { throw 'SAM build failed.' }
$deployArgs = @('deploy','--stack-name','aws-url-shortener','--resolve-s3','--capabilities','CAPABILITY_IAM','--parameter-overrides',"FrontendBucketName=$BucketName","FrontendOrigin=$origin",'--no-fail-on-empty-changeset','--profile',$Profile)
if ($Region) { $deployArgs += @('--region',$Region) }
if ($SkipConfirm) { $deployArgs += '--no-confirm-changeset' } else { $deployArgs += '--confirm-changeset' }
sam @deployArgs
if ($LASTEXITCODE -ne 0) { throw 'SAM deploy failed.' }
& "$PSScriptRoot/update-frontend.ps1" -Profile $Profile -Region $Region
