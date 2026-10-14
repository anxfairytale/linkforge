# Architecture

```text
Browser -> S3 static website
   | HTTPS fetch
   v
API Gateway HTTP API -> Lambda (Python 3.12) -> DynamoDB
```

- **S3** serves static HTML, CSS, JavaScript, and generated API config. Website endpoints are HTTP-only, with public object reads enabled for this demonstration.
- **API Gateway HTTP API** supplies HTTPS API access and CORS, and invokes Lambda using HTTP API payload v2.
- **Lambda** validates inputs, creates codes with Python `secrets`, and is the only component that accesses DynamoDB. It never fetches submitted destinations.
- **DynamoDB** stores one item per short code with on-demand billing and encryption. `PutItem` uses `attribute_not_exists(shortCode)`; redirects use an atomic `if_not_exists(clicks, :zero) + :inc` update.
- **IAM** grants Lambda only `GetItem`, `PutItem`, and `UpdateItem` on this table.
- **CloudWatch Logs** captures Lambda logs. Destination URLs and exception messages are omitted.
- **SAM/CloudFormation** manages the API, Lambda, table, bucket, roles, and policies as a stack.

## Data flow

1. Browser POSTs JSON to `/shorten`; Lambda independently checks URL syntax, protocol, hostname, length, whitespace, and credentials-in-URL.
2. Lambda retries conditional writes when a random code collides.
3. Browser navigates directly to `/r/{shortCode}`; Lambda reads the mapping, increments clicks, and returns `302 Location`.
4. Frontend reads `/stats/{shortCode}` and renders using text nodes. It has no analytics write operation.

The `FrontendOrigin` parameter restricts browser CORS to the website origin. CORS is not authorization. This demo has no abuse controls and accepts arbitrary syntactically valid HTTP(S) destinations.
