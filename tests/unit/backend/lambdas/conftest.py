"""
Pytest configuration for Lambda tests.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Pre-load modules into sys.modules BEFORE any Lambda handler imports
# This simulates Lambda environment where Layer modules are available without 'backend.lambdas.layer' prefix

# Step 1: Add Layer modules to sys.modules first
import backend.lambdas.layer.error_handler
import backend.lambdas.layer.logger
import backend.lambdas.layer.response

sys.modules["error_handler"] = backend.lambdas.layer.error_handler
sys.modules["logger"] = backend.lambdas.layer.logger
sys.modules["response"] = backend.lambdas.layer.response

# Step 2: Import Lambda-specific modules DIRECTLY (avoid __init__.py which imports handler)
# We need to manually load these as standalone modules
import importlib.util

# Load algorithm module
spec_algo = importlib.util.spec_from_file_location(
    "algorithm",
    "backend/lambdas/recommendation/algorithm.py"
)
algo_module = importlib.util.module_from_spec(spec_algo)
sys.modules["algorithm"] = algo_module
spec_algo.loader.exec_module(algo_module)

# Load user module
spec_user = importlib.util.spec_from_file_location(
    "user",
    "backend/lambdas/preference/user.py"
)
user_module = importlib.util.module_from_spec(spec_user)
sys.modules["user"] = user_module
spec_user.loader.exec_module(user_module)

# Load tasting module
spec_tasting = importlib.util.spec_from_file_location(
    "tasting",
    "backend/lambdas/tasting/tasting.py"
)
tasting_module = importlib.util.module_from_spec(spec_tasting)
sys.modules["tasting"] = tasting_module
spec_tasting.loader.exec_module(tasting_module)


@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """Mock environment variables for Lambda functions."""
    monkeypatch.setenv("AWS_REGION", "us-west-2")
    monkeypatch.setenv("USERS_TABLE", "SakeSensei-Users")
    monkeypatch.setenv("TASTING_TABLE", "SakeSensei-TastingRecords")
    monkeypatch.setenv("SAKE_TABLE", "SakeSensei-SakeMaster")
    monkeypatch.setenv("BREWERY_TABLE", "SakeSensei-BreweryMaster")
    monkeypatch.setenv("IMAGES_BUCKET", "sakesensei-images")


@pytest.fixture
def lambda_context():
    """Mock Lambda context."""
    context = MagicMock()
    context.function_name = "test-function"
    context.invoked_function_arn = "arn:aws:lambda:us-west-2:123456789012:function:test"
    context.memory_limit_in_mb = 128
    context.request_id = "test-request-id"
    context.log_group_name = "/aws/lambda/test-function"
    context.log_stream_name = "2025/10/01/[$LATEST]test"
    context.get_remaining_time_in_millis = lambda: 300000
    return context


@pytest.fixture
def mock_dynamodb_table():
    """Mock DynamoDB table."""
    with patch("boto3.resource") as mock_resource:
        mock_table = MagicMock()
        mock_resource.return_value.Table.return_value = mock_table
        yield mock_table


@pytest.fixture
def mock_s3_client():
    """Mock S3 client."""
    with patch("boto3.client") as mock_client:
        mock_s3 = MagicMock()
        mock_client.return_value = mock_s3
        yield mock_s3


@pytest.fixture
def mock_bedrock_client():
    """Mock Bedrock Runtime client."""
    with patch("boto3.client") as mock_client:
        mock_bedrock = MagicMock()
        mock_client.return_value = mock_bedrock
        yield mock_bedrock
