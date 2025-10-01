"""
Pytest configuration for Streamlit app tests.
"""

import sys
from unittest.mock import MagicMock

import pytest

# Mock streamlit module globally
mock_st = MagicMock()
sys.modules["streamlit"] = mock_st


@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """Mock environment variables for Streamlit app."""
    monkeypatch.setenv("AWS_REGION", "us-west-2")
    monkeypatch.setenv("AWS_ACCOUNT_ID", "123456789012")
    monkeypatch.setenv("COGNITO_USER_POOL_ID", "us-west-2_XXXXX")
    monkeypatch.setenv("COGNITO_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("AGENTCORE_GATEWAY_URL", "")
    monkeypatch.setenv("LAMBDA_PREFERENCE_ARN", "arn:aws:lambda:us-west-2:123:function:pref")
    monkeypatch.setenv(
        "LAMBDA_RECOMMENDATION_ARN", "arn:aws:lambda:us-west-2:123:function:rec"
    )
    monkeypatch.setenv("LAMBDA_TASTING_ARN", "arn:aws:lambda:us-west-2:123:function:tasting")
    monkeypatch.setenv("LAMBDA_BREWERY_ARN", "arn:aws:lambda:us-west-2:123:function:brewery")
    monkeypatch.setenv(
        "LAMBDA_IMAGE_RECOGNITION_ARN", "arn:aws:lambda:us-west-2:123:function:img"
    )
