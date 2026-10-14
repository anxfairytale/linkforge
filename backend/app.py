"""Lambda handler for the AWS URL Shortener (API Gateway HTTP API v2)."""
import base64
import json
import os
import re
import secrets
import string
from datetime import datetime, timezone
from urllib.parse import urlsplit

import boto3
from botocore.exceptions import ClientError

TABLE_NAME = os.environ.get("TABLE_NAME", "URLShortener")
API_BASE_URL = ""
FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN", "")
MAX_URL_LENGTH = 2048
CODE_LENGTH = 7
CODE_CHARS = string.ascii_letters + string.digits
MAX_ATTEMPTS = 8
table = boto3.resource("dynamodb").Table(TABLE_NAME)


def _headers(content_type="application/json"):
    result = {"Content-Type": content_type, "Cache-Control": "no-store"}
    if FRONTEND_ORIGIN:
        result["Access-Control-Allow-Origin"] = FRONTEND_ORIGIN
        result["Vary"] = "Origin"
    return result


def _json(status, data):
    return {"statusCode": status, "headers": _headers(), "body": json.dumps(data)}


def _method(event):
    return (event.get("requestContext", {}).get("http", {}).get("method")
            or event.get("httpMethod", "GET")).upper()


def _path(event):
    return event.get("rawPath") or event.get("path") or "/"


def _body(event):
    raw = event.get("body")
    if event.get("isBase64Encoded") and raw:
        raw = base64.b64decode(raw).decode("utf-8")
    if not raw:
        return {}
    if isinstance(raw, dict):
        return raw
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else None
    except (ValueError, TypeError, UnicodeDecodeError):
        return None


def _valid_url(value):
    if not isinstance(value, str) or not value or len(value) > MAX_URL_LENGTH:
        return False
    if value != value.strip() or any(ord(ch) < 32 or ch.isspace() for ch in value):
        return False
    try:
        parsed = urlsplit(value)
        return (parsed.scheme.lower() in ("http", "https") and bool(parsed.hostname)
                and parsed.username is None and parsed.password is None
                and (parsed.port is None or 1 <= parsed.port <= 65535))
    except ValueError:
        return False


def _api_error(error, operation):
    # Avoid logging URLs or exception messages that can include request data.
    code = error.response.get("Error", {}).get("Code", "Unknown")
    print(f"DynamoDB {operation} failed ({code})")
    return _json(500, {"error": "A storage error occurred. Please try again."})


def _shorten(event):
    data = _body(event)
    if data is None:
        return _json(400, {"error": "Request body must be a JSON object."})
    url = data.get("url")
    if not url:
        return _json(400, {"error": "Please provide a URL."})
    if not _valid_url(url):
        return _json(400, {"error": "Enter a valid HTTP or HTTPS URL (maximum 2048 characters)."})
    request_context = event.get("requestContext", {})
    domain = request_context.get("domainName", "")
    stage = request_context.get("stage", "")
    api_base_url = f"https://{domain}" if domain else ""
    if stage and stage != "$default":
        api_base_url += f"/{stage}"
    if not api_base_url:
        return _json(500, {"error": "Unable to determine API URL."})
    created = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    for _ in range(MAX_ATTEMPTS):
        code = "".join(secrets.choice(CODE_CHARS) for _ in range(CODE_LENGTH))
        try:
            table.put_item(Item={"shortCode": code, "originalUrl": url,
                                 "createdAt": created, "clicks": 0},
                           ConditionExpression="attribute_not_exists(shortCode)")
            return _json(201, {"shortCode": code, "shortUrl": f"{api_base_url}/r/{code}"})
        except ClientError as error:
            error_code = error.response.get("Error", {}).get("Code")
            if error_code == "ConditionalCheckFailedException":
                continue
            return _api_error(error, "put_item")
    return _json(503, {"error": "Could not allocate a short code. Please try again."})


def _stats(code):
    try:
        item = table.get_item(Key={"shortCode": code}, ConsistentRead=True).get("Item")
    except ClientError as error:
        return _api_error(error, "get_item")
    if not item:
        return _json(404, {"error": "Short link not found."})
    return _json(200, {"shortCode": item["shortCode"], "originalUrl": item["originalUrl"],
                       "createdAt": item["createdAt"], "clicks": int(item.get("clicks", 0))})


def _redirect(code):
    try:
        item = table.get_item(Key={"shortCode": code}, ConsistentRead=True).get("Item")
    except ClientError as error:
        return _api_error(error, "get_item")
    if not item:
        return _json(404, {"error": "Short link not found."})
    try:
        table.update_item(Key={"shortCode": code},
                          UpdateExpression="SET clicks = if_not_exists(clicks, :zero) + :inc",
                          ExpressionAttributeValues={":zero": 0, ":inc": 1})
    except ClientError as error:
        return _api_error(error, "update_item")
    return {"statusCode": 302, "headers": _headers("text/plain; charset=utf-8") | {
        "Location": item["originalUrl"]}, "body": "", "isBase64Encoded": False}


def lambda_handler(event, context):
    """Route API Gateway v2 events; also supports legacy REST API event shape."""
    method, path = _method(event), _path(event)
    if method == "OPTIONS":
        headers = _headers()
        headers.update({"Access-Control-Allow-Methods": "GET,POST,OPTIONS",
                        "Access-Control-Allow-Headers": "Content-Type"})
        return {"statusCode": 204, "headers": headers, "body": ""}
    if method == "GET" and path == "/health":
        return _json(200, {"status": "ok"})
    if method == "POST" and path == "/shorten":
        return _shorten(event)
    params = event.get("pathParameters") or {}
    code = params.get("shortCode")
    if method == "GET" and path.startswith("/stats/"):
        code = code or path[len("/stats/"):]
        if code and re.fullmatch(r"[A-Za-z0-9]{1,32}", code):
            return _stats(code)
        return _json(404, {"error": "Short link not found."})
    if method == "GET" and path.startswith("/r/"):
        code = code or path[len("/r/"):]
        if code and re.fullmatch(r"[A-Za-z0-9]{1,32}", code):
            return _redirect(code)
        return _json(404, {"error": "Short link not found."})
    return _json(404, {"error": "Route not found."})


