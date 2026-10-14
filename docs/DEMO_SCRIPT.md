# Five-minute live demonstration

1. **0:00–0:40:** Open `FrontendWebsiteUrl` from CloudFormation Outputs. Explain the S3 website is HTTP-only; the API calls use HTTPS.
2. **0:40–1:20:** Paste `https://example.com/college/demo?source=aws` and choose **Shorten link**. Explain conditional writes prevent code collisions.
3. **1:20–2:10:** Submit a blank value, then `ftp://example.com`; show the helpful validation messages. Mention validation does not establish destination safety.
4. **2:10–3:00:** Copy/open the generated link in a new tab. Show the browser following the 302 redirect.
5. **3:00–3:40:** Return to the app. Show link code, destination, created time, and click count. Reopen the link, then choose **Refresh** and show the increased count.
6. **3:40–4:30:** In DynamoDB → table → Explore items, show the stored record. In CloudWatch → Logs, show Lambda activity.
7. **4:30–5:00:** Show CloudFormation outputs and explain the cleanup script and the project's demo-only abuse limitations.

If calls fail, check generated `frontend/config.js`, exact CORS origin, API routes, and Lambda logs.
