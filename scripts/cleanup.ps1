param([string]$Profile = 'default', [string]$Region = '', [switch]$DeleteFrontendBucket)
$ErrorActionPreference = 'Stop'
$awsArgs = @('--profile',$Profile)
if ($Region) { $awsArgs += @('--region',$Region) }
$account = aws sts get-caller-identity --query Account --output text @awsArgs
if ($LASTEXITCODE -ne 0) { throw 'Could not verify AWS account/profile.' }
Write-Host "This removes stack aws-url-shortener and its DynamoDB data. AWS account: $account"
if ($DeleteFrontendBucket) { Write-Host 'The frontend bucket will also be emptied and deleted.' }
if ((Read-Host 'Type DELETE aws-url-shortener to continue') -cne 'DELETE aws-url-shortener') { Write-Host 'Cleanup cancelled.'; exit 0 }
aws cloudformation delete-stack --stack-name aws-url-shortener @awsArgs
if ($LASTEXITCODE -ne 0) { throw 'CloudFormation stack deletion could not be started.' }
aws cloudformation wait stack-delete-complete --stack-name aws-url-shortener @awsArgs
if ($LASTEXITCODE -ne 0) { throw 'Stack deletion did not complete. Check CloudFormation events.' }
if ($DeleteFrontendBucket) {
  $bucket = Read-Host 'Enter the exact frontend bucket name to empty and delete'
  if ($bucket -notmatch '^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$') { throw 'Bucket name format was invalid; not deleting.' }
  aws s3 rm "s3://$bucket" --recursive @awsArgs
  if ($LASTEXITCODE -ne 0) { throw 'Could not empty the named bucket.' }
  aws s3api delete-bucket --bucket $bucket @awsArgs
  if ($LASTEXITCODE -ne 0) { throw 'Could not delete the named bucket.' }
}
Write-Host 'Cleanup complete.'
