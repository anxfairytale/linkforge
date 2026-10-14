# Troubleshooting

- **Credentials/region:** run `aws sso login --profile <name>` and `aws sts get-caller-identity --profile <name>`; pass `-Region` or configure one. Confirm the account is intended.
- **IAM:** deployer needs SAM/CloudFormation permissions for declared resources. Runtime Lambda needs only table `GetItem`, `PutItem`, `UpdateItem`; do not widen it to `*`.
- **SAM build/deploy:** check `sam --version`, Python 3.12+, dependency access, `CAPABILITY_IAM`, then inspect CloudFormation Events for the first failed resource.
- **S3 name/permissions:** bucket names are globally unique, lowercase, and 3–63 chars. Check account, region, and permissions. Website content is publicly readable by design; never upload private files.
- **CORS:** exact origin includes `http://` and host, no path/trailing slash. Update `FrontendOrigin`, redeploy, and hard refresh. Inspect API/Lambda logs if browser CORS masks the real error.
- **API 403/404/500:** verify API base, region, routes, and stack status. Unknown codes return 404. 403 often indicates a wrong API URL/route; 500 may indicate Lambda config, IAM, or DynamoDB errors.
- **Lambda exceptions:** find the generated Lambda function and its `/aws/lambda/...` log group. Check handler, runtime, environment variables, and stack status. Public errors intentionally omit internals.
- **DynamoDB:** verify the table output and role policy; key is string `shortCode`. Counter updates use atomic `UpdateItem`.
- **Redirect:** use direct navigation to `/r/<code>` and `curl.exe -i` to inspect `Location`. Old links shaped `/code` are not valid. Browsers follow the 302 response.
- **HTTPS website:** S3 website endpoints are HTTP-only. Use CloudFront with private S3 REST origin/OAC described in `DEPLOYMENT.md`.
