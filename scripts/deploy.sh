#!/usr/bin/env bash
set -euo pipefail
if [[ $# -lt 1 ]]; then echo "Usage: $0 <globally-unique-bucket-name> [aws-profile] [region]" >&2; exit 2; fi
BUCKET="$1"; PROFILE="${2:-default}"; REGION="${3:-$(aws configure get region --profile "$PROFILE")}"; ROOT="$(cd "$(dirname "$0")/.." && pwd)"
command -v aws >/dev/null && command -v sam >/dev/null && command -v python3 >/dev/null || { echo 'Install AWS CLI v2, SAM CLI, and Python 3.12+.' >&2; exit 1; }
aws sts get-caller-identity --profile "$PROFILE" ${REGION:+--region "$REGION"} >/dev/null
sam build --template-file "$ROOT/template.yaml"
ORIGIN="http://${BUCKET}.s3-website-${REGION}.amazonaws.com"
sam deploy --stack-name aws-url-shortener --resolve-s3 --capabilities CAPABILITY_IAM --parameter-overrides "FrontendBucketName=${BUCKET}" "FrontendOrigin=${ORIGIN}" --profile "$PROFILE" ${REGION:+--region "$REGION"} --confirm-changeset
API="$(aws cloudformation describe-stacks --stack-name aws-url-shortener --profile "$PROFILE" ${REGION:+--region "$REGION"} --query "Stacks[0].Outputs[?OutputKey=='ApiBaseUrl'].OutputValue | [0]" --output text)"
WEBSITE="$(aws cloudformation describe-stacks --stack-name aws-url-shortener --profile "$PROFILE" ${REGION:+--region "$REGION"} --query "Stacks[0].Outputs[?OutputKey=='FrontendWebsiteUrl'].OutputValue | [0]" --output text)"
printf 'window.APP_CONFIG = { API_BASE_URL: "%s" };\n' "$API" > "$ROOT/frontend/config.js"
aws s3 sync "$ROOT/frontend" "s3://${BUCKET}" --exclude config.js.example --profile "$PROFILE" ${REGION:+--region "$REGION"}
printf 'Frontend: %s\nAPI: %s\n' "$WEBSITE" "$API"
