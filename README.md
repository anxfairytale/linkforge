# AWS URL Shortener

A demo-ready, serverless URL shortener. Create a link, open it for an HTTP 302 redirect, and read its DynamoDB-backed click count. The frontend is plain HTML/CSS/JavaScript; SAM provisions the HTTP API, Python Lambda, on-demand DynamoDB table, and static website bucket.

## Features

- Validates HTTP/HTTPS destinations (maximum 2,048 characters), without fetching them.
- Uses cryptographic random codes and DynamoDB conditional writes to prevent collisions.
- Counts redirects with atomic DynamoDB updates; stats are read-only from the browser.
- Responsive frontend with copy/open actions, loading feedback, and analytics refresh.
- SAM/CloudFormation deployment, scripts, mocked unit tests, and deployment/demo/cleanup guides.

## Architecture and request flow

The browser loads the static site from S3. `POST /shorten` validates input and conditionally writes a URL mapping. A user opening `GET /r/{shortCode}` reads the destination, atomically increments `clicks`, and receives a 302 `Location` response. `GET /stats/{shortCode}` reads the item. API Gateway invokes the same Lambda for all routes; Lambda alone has scoped DynamoDB permissions. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Project files

```text
backend/app.py                 Lambda handler
frontend/                      Static app; config.js is generated at deploy time
template.yaml                  SAM/CloudFormation resources
tests/                         AWS-mocked pytest suite
scripts/                        Prerequisite, deploy, update, and cleanup scripts
docs/                           Architecture, deployment, demo, troubleshooting, costs
```

## Prerequisites

- AWS account and a configured AWS CLI v2 profile. Prefer IAM Identity Center or temporary credentials; never place access keys in this repository.
- AWS SAM CLI, Python 3.12+ for deployment packaging, and PowerShell 7 or Windows PowerShell 5.1 for the documented scripts.
- A globally unique lowercase S3 bucket name (3–63 characters). Bucket names are public identifiers.

Python 3.12 (`python3.12`, Amazon Linux 2023) is supported by AWS Lambda; check AWS's [current runtime table](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html) before upgrading the template runtime.

## Local development and tests

The site is static and can be served locally with `python -m http.server 8000 -d frontend`, but shortening needs the deployed API and generated `frontend/config.js`. Unit tests mock AWS calls and do not deploy or need credentials:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

## Deploy to AWS

From this directory, first configure and verify a profile, then deploy (the script asks SAM to show/confirm a change set):

```powershell
aws configure sso --profile student
aws sso login --profile student
aws sts get-caller-identity --profile student
.\scripts\check-prerequisites.ps1
.\scripts\deploy.ps1 -BucketName my-unique-url-shortener-2026 -Profile student -Region ap-south-1
```

Deployment creates billable AWS resources and public website content. Review the change set and cost guide before confirming. The script builds/deploys SAM, configures API CORS for the S3 website origin, generates `frontend/config.js`, and uploads assets.

To redeploy frontend-only changes after a successful backend deployment:

```powershell
.\scripts\update-frontend.ps1 -Profile student -Region ap-south-1
```

The script prints the **HTTP-only S3 website URL** and API base URL. Stack outputs are also available at CloudFormation → `aws-url-shortener` → Outputs. For endpoint contracts and exact demo steps see [DEPLOYMENT.md](docs/DEPLOYMENT.md) and [DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md).

## API

- `POST /shorten` with `{"url":"https://example.com/path"}` → 201 `{"shortCode":"…","shortUrl":"https://…/r/…"}`
- `GET /r/{shortCode}` → 302 to the destination; a missing code returns 404.
- `GET /stats/{shortCode}` → code, `originalUrl`, `createdAt`, and clicks.
- `GET /health` → `{"status":"ok"}`.

## Security and deployment limits

The S3 website endpoint is HTTP only and its assets must be publicly readable. Do not use it for sensitive content. The optional HTTPS route is CloudFront with a private S3 REST origin and Origin Access Control; see [DEPLOYMENT.md](docs/DEPLOYMENT.md). The API itself is HTTPS. URL validation checks syntax only: it does not make a destination trustworthy. This class/demo project has no abuse prevention, authentication, quotas, or domain allowlist and is not production hardened.

## Troubleshooting and cost

See [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for credentials, IAM, CORS, API, Lambda, and DynamoDB errors. DynamoDB uses on-demand billing; API Gateway, Lambda, S3 requests/storage, logs, data transfer, and optional CloudFront may incur charges. See [COST_AND_CLEANUP.md](docs/COST_AND_CLEANUP.md) and remove resources after the demo.
