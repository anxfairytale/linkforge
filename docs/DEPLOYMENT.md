# Deployment guide

## Prepare

Install AWS CLI v2, AWS SAM CLI, Python 3.12+, and PowerShell. Prefer IAM Identity Center/temporary credentials:

```powershell
aws configure sso --profile student
aws sso login --profile student
aws sts get-caller-identity --profile student
aws configure get region --profile student
```

Choose a globally unique lowercase S3 name (for example `student-linkforge-2026-abc`) and region. Never store keys in project files.

## Deploy

At repository root:

```powershell
.\scripts\check-prerequisites.ps1
.\scripts\deploy.ps1 -BucketName student-linkforge-2026-abc -Profile student -Region ap-south-1
```

The first script verifies AWS CLI, SAM, and Python. The second verifies caller credentials, runs `sam build`, then deploys stack `aws-url-shortener` with `CAPABILITY_IAM` and a reviewable change set. Confirm when SAM prompts. It provisions API, Lambda, table, and S3 bucket, generates `frontend/config.js`, and uploads assets. These are real resources and may incur charges.

The script infers the bucket's region if it exists. For a new bucket it uses the passed/default region. It configures CORS with `http://<bucket>.s3-website-<region>.amazonaws.com`; verify the `FrontendWebsiteUrl` output because endpoint names vary by region. If needed, update CloudFormation parameter `FrontendOrigin` to the exact website origin and redeploy.

## Outputs and smoke checks

CloudFormation → **Stacks** → `aws-url-shortener` → **Outputs** shows API, website, bucket, and table. The frontend is HTTP-only; the API is HTTPS.

```powershell
$api = 'https://replace-with-api-id.execute-api.ap-south-1.amazonaws.com'
curl.exe -i "$api/health"
curl.exe -i -X POST "$api/shorten" -H "Content-Type: application/json" -d '{"url":"https://example.com/a/path"}'
curl.exe -i "$api/stats/REPLACE_CODE"
curl.exe -i "$api/r/REPLACE_CODE"
```

Redirect responds 302 with `Location`. Inspect rows in DynamoDB → Tables → stack table → Explore items. Lambda logs are in CloudWatch → Log groups `/aws/lambda/<generated function name>`.

## Updates

For frontend-only changes:

```powershell
.\scripts\update-frontend.ps1 -Profile student -Region ap-south-1
```

For backend/template changes rerun `deploy.ps1` and review the change set.

## Optional HTTPS frontend

S3 website endpoints do not support HTTPS. Use CloudFront with an S3 **REST endpoint** origin, Origin Access Control (OAC), and a bucket policy granting `s3:GetObject` only to that distribution. Disable S3 public access and website hosting/public policy; configure an ACM certificate in us-east-1 for a custom domain if used. Set API CORS `FrontendOrigin` to the CloudFront HTTPS origin, redeploy, and regenerate/upload config. CloudFront/domain may add cost. The current SAM template creates a public HTTP website and is not this upgrade.

## Cleanup

See [COST_AND_CLEANUP.md](COST_AND_CLEANUP.md). Stack deletion deletes DynamoDB mappings; the website bucket is retained and must be removed separately by explicit option.
