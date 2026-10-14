"""Load the Lambda module without requiring live AWS credentials."""
import os
import sys
import types

os.environ.setdefault("TABLE_NAME", "test-table")
os.environ.setdefault("API_BASE_URL", "https://api.example.test")

try:
    import boto3  # noqa: F401
except ImportError:
    fake_boto3 = types.ModuleType("boto3")
    fake_boto3.resource = lambda *_a, **_k: types.SimpleNamespace(Table=lambda *_a, **_k: None)
    sys.modules["boto3"] = fake_boto3
try:
    import botocore.exceptions  # noqa: F401
except ImportError:
    botocore = types.ModuleType("botocore")
    exceptions = types.ModuleType("botocore.exceptions")
    class ClientError(Exception):
        def __init__(self, response, operation_name):
            self.response, self.operation_name = response, operation_name
            super().__init__(operation_name)
    exceptions.ClientError = ClientError
    botocore.exceptions = exceptions
    sys.modules["botocore"] = botocore
    sys.modules["botocore.exceptions"] = exceptions

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
