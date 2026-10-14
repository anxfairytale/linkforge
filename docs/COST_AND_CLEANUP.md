# Cost and cleanup

Possible charges include API Gateway requests, Lambda duration/invocations, CloudWatch log storage, DynamoDB on-demand reads/writes and storage, S3 requests/storage/transfer, and optional CloudFront/domain. Costs vary by region and use; Free Tier eligibility is not guaranteed. Configure an AWS Budget alert and check Cost Explorer. Log retention follows account defaults.

The frontend bucket is retained when the stack is deleted because it may contain files. Its public-read policy also remains until bucket deletion. DynamoDB uses `DeletionPolicy: Delete`, so stack removal permanently deletes mappings; export any data first.

```powershell
.\scripts\cleanup.ps1 -Profile student -Region ap-south-1
```

Verify the account at the prompt and type exactly `DELETE aws-url-shortener`. This removes only that stack. To additionally remove the frontend bucket:

```powershell
.\scripts\cleanup.ps1 -Profile student -Region ap-south-1 -DeleteFrontendBucket
```

After stack removal, enter the exact bucket name. The script empties and deletes that bucket. Confirm it contains no unrelated files before this option. Check CloudFormation Events if deletion stalls; verify S3, stack state, and Billing afterward.
