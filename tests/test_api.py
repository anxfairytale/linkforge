import json
from unittest.mock import Mock

import pytest
import app
from botocore.exceptions import ClientError


@pytest.fixture(autouse=True)
def fake_table(monkeypatch):
    table = Mock()
    monkeypatch.setattr(app, "table", table)
    monkeypatch.setattr(app, "API_BASE_URL", "https://api.example.test")
    yield table


def post(url):
    return {"requestContext": {"http": {"method": "POST"}}, "rawPath": "/shorten",
            "headers": {"content-type": "application/json"}, "body": json.dumps({"url": url})}


def get(path):
    return {"requestContext": {"http": {"method": "GET"}}, "rawPath": path}


def test_valid_url_shortening_persists_attributes(fake_table, monkeypatch):
    monkeypatch.setattr(app.secrets, "choice", lambda _chars: "a")
    response = app.lambda_handler(post("https://example.com/a?x=1"), None)
    assert response["statusCode"] == 201
    assert json.loads(response["body"]) == {"shortCode": "aaaaaaa", "shortUrl": "https://api.example.test/r/aaaaaaa"}
    item = fake_table.put_item.call_args.kwargs["Item"]
    assert item["originalUrl"] == "https://example.com/a?x=1" and item["clicks"] == 0
    assert "createdAt" in item
    assert fake_table.put_item.call_args.kwargs["ConditionExpression"] == "attribute_not_exists(shortCode)"


@pytest.mark.parametrize("event, expected", [
    (post(""), 400), (post("not a url"), 400), (post("ftp://example.com"), 400),
    ({"requestContext": {"http": {"method": "POST"}}, "rawPath": "/shorten", "body": "{"}, 400),
    (post("https://example.com/" + "x" * 2050), 400),
])
def test_invalid_requests(event, expected, fake_table):
    assert app.lambda_handler(event, None)["statusCode"] == expected
    fake_table.put_item.assert_not_called()


def test_successful_redirect_increments_atomically(fake_table):
    fake_table.get_item.return_value = {"Item": {"shortCode": "abc1234", "originalUrl": "https://example.com/x"}}
    response = app.lambda_handler(get("/r/abc1234"), None)
    assert response["statusCode"] == 302
    assert response["headers"]["Location"] == "https://example.com/x"
    assert fake_table.update_item.call_args.kwargs["UpdateExpression"] == "SET clicks = if_not_exists(clicks, :zero) + :inc"
    assert fake_table.update_item.call_args.kwargs["ExpressionAttributeValues"] == {":zero": 0, ":inc": 1}


def test_unknown_redirect_and_stats_return_404(fake_table):
    fake_table.get_item.return_value = {}
    assert app.lambda_handler(get("/r/unknown1"), None)["statusCode"] == 404
    assert app.lambda_handler(get("/stats/unknown1"), None)["statusCode"] == 404
    fake_table.update_item.assert_not_called()


def test_stats_returns_expected_fields(fake_table):
    fake_table.get_item.return_value = {"Item": {"shortCode": "abc1234", "originalUrl": "https://example.com",
        "createdAt": "2026-01-01T00:00:00Z", "clicks": 3}}
    result = app.lambda_handler(get("/stats/abc1234"), None)
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"shortCode": "abc1234", "originalUrl": "https://example.com", "createdAt": "2026-01-01T00:00:00Z", "clicks": 3}


def test_collision_retries_with_conditional_put(fake_table, monkeypatch):
    choices = iter("abcdefgHIJKLMN")
    monkeypatch.setattr(app.secrets, "choice", lambda _chars: next(choices))
    collision = ClientError({"Error": {"Code": "ConditionalCheckFailedException"}}, "PutItem")
    fake_table.put_item.side_effect = [collision, None]
    response = app.lambda_handler(post("https://example.com"), None)
    assert json.loads(response["body"])["shortCode"] == "HIJKLMN"
    assert fake_table.put_item.call_count == 2


def test_storage_errors_are_safe(fake_table):
    fake_table.put_item.side_effect = ClientError({"Error": {"Code": "AccessDeniedException"}}, "PutItem")
    response = app.lambda_handler(post("https://example.com"), None)
    assert response["statusCode"] == 500
    assert "AccessDenied" not in response["body"]
    fake_table.get_item.side_effect = ClientError({"Error": {"Code": "InternalServerError"}}, "GetItem")
    assert app.lambda_handler(get("/stats/abc1234"), None)["statusCode"] == 500


def test_redirect_does_not_report_success_if_counter_update_fails(fake_table):
    fake_table.get_item.return_value = {"Item": {"shortCode": "abc1234", "originalUrl": "https://example.com"}}
    fake_table.update_item.side_effect = ClientError({"Error": {"Code": "InternalServerError"}}, "UpdateItem")
    response = app.lambda_handler(get("/r/abc1234"), None)
    assert response["statusCode"] == 500
    assert "Location" not in response["headers"]


def test_http_api_v2_and_legacy_event_parsing(fake_table):
    assert app.lambda_handler({"requestContext": {"http": {"method": "GET"}}, "rawPath": "/health"}, None)["statusCode"] == 200
    fake_table.get_item.return_value = {"Item": {"shortCode": "abc", "originalUrl": "https://example.com"}}
    event = {"httpMethod": "GET", "path": "/r/abc", "pathParameters": {"shortCode": "abc"}}
    assert app.lambda_handler(event, None)["statusCode"] == 302

