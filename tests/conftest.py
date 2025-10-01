"""Pytest configuration and fixtures for Sake Sensei tests."""

import os
from collections.abc import Generator
from typing import Any
from unittest.mock import MagicMock, patch

import boto3
import pytest
from moto import mock_aws


@pytest.fixture(scope="session")
def aws_credentials() -> None:
    """Mock AWS credentials for testing."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-west-2"


@pytest.fixture
def dynamodb_mock(aws_credentials: None) -> Generator[Any]:
    """Create mock DynamoDB resource."""
    with mock_aws():
        yield boto3.resource("dynamodb", region_name="us-west-2")


@pytest.fixture
def s3_mock(aws_credentials: None) -> Generator[Any]:
    """Create mock S3 client."""
    with mock_aws():
        yield boto3.client("s3", region_name="us-west-2")


@pytest.fixture
def lambda_context() -> MagicMock:
    """Create mock Lambda context."""
    context = MagicMock()
    context.function_name = "test-function"
    context.function_version = "$LATEST"
    context.invoked_function_arn = "arn:aws:lambda:us-west-2:123456789:function:test"
    context.memory_limit_in_mb = 512
    context.aws_request_id = "test-request-id"
    context.log_group_name = "/aws/lambda/test-function"
    context.log_stream_name = "test-log-stream"
    return context


@pytest.fixture
def mock_bedrock_client() -> Generator[MagicMock]:
    """Mock Bedrock client for AgentCore tests."""
    with patch("boto3.client") as mock_client:
        bedrock_mock = MagicMock()
        mock_client.return_value = bedrock_mock
        yield bedrock_mock


@pytest.fixture
def sample_sake_data() -> dict[str, Any]:
    """Sample sake data for testing."""
    return {
        "sake_id": "test-sake-001",
        "name": "獺祭 純米大吟醸 磨き二割三分",
        "brewery": "旭酒造",
        "type": "純米大吟醸",
        "prefecture": "山口県",
        "rice": "山田錦",
        "polishing_ratio": 23,
        "alcohol": 16.0,
        "smv": 4,
        "acidity": 1.5,
        "sweetness": 2,
        "richness": 3,
        "description": "華やかな香りと繊細な味わい",
    }


@pytest.fixture
def sample_user_preferences() -> dict[str, Any]:
    """Sample user preferences for testing."""
    return {
        "user_id": "test-user-001",
        "sweetness": 3,
        "acidity": 2,
        "richness": 2,
        "preferred_types": ["純米大吟醸", "純米吟醸"],
        "preferred_temperatures": ["冷酒"],
        "budget_range": "3000-5000",
    }


@pytest.fixture
def sample_tasting_record() -> dict[str, Any]:
    """Sample tasting record for testing."""
    return {
        "record_id": "test-record-001",
        "user_id": "test-user-001",
        "sake_id": "test-sake-001",
        "rating": 4,
        "temperature": "冷酒",
        "paired_food": "刺身",
        "notes": "フルーティーで飲みやすい",
        "tasted_at": "2025-10-01T12:00:00Z",
    }
