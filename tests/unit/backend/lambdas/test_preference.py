"""
Unit tests for Preference Lambda function.
"""

import json
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def lambda_context():
    """Mock Lambda context."""
    context = MagicMock()
    context.function_name = "test-function"
    context.invoked_function_arn = "arn:aws:lambda:us-west-2:123456789012:function:test"
    context.memory_limit_in_mb = 128
    context.request_id = "test-request-id"
    return context


@pytest.fixture
def mock_dynamodb():
    """Mock DynamoDB resource."""
    with patch("boto3.resource") as mock_resource:
        mock_table = MagicMock()
        mock_resource.return_value.Table.return_value = mock_table
        yield mock_table


class TestPreferenceLambda:
    """Tests for Preference Lambda handler."""

    def test_handler_missing_user_id(self, lambda_context):
        """Test handler with missing user_id."""
        from backend.lambdas.preference.handler import handler

        event = {"body": json.dumps({"action": "get"})}

        response = handler(event, lambda_context)

        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["error"] == "BadRequest"
        assert "user_id" in body["message"]

    def test_handler_get_preferences(self, lambda_context, mock_dynamodb):
        """Test getting user preferences."""
        from backend.lambdas.preference.handler import handler

        mock_dynamodb.get_item.return_value = {
            "Item": {
                "user_id": "test_user",
                "flavor_preference": "light",
                "sweetness": 3,
                "dryness": 7,
                "favorite_categories": ["junmai_daiginjo"],
            }
        }

        event = {"body": json.dumps({"action": "get", "user_id": "test_user"})}

        response = handler(event, lambda_context)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["data"]["user_id"] == "test_user"
        assert body["data"]["flavor_preference"] == "light"

    def test_handler_get_preferences_not_found(self, lambda_context, mock_dynamodb):
        """Test getting non-existent preferences."""
        from backend.lambdas.preference.handler import handler

        mock_dynamodb.get_item.return_value = {}

        event = {"body": json.dumps({"action": "get", "user_id": "test_user"})}

        response = handler(event, lambda_context)

        assert response["statusCode"] == 404

    def test_handler_update_preferences(self, lambda_context, mock_dynamodb):
        """Test updating user preferences."""
        from backend.lambdas.preference.handler import handler

        mock_dynamodb.put_item.return_value = {}

        event = {
            "body": json.dumps({
                "action": "update",
                "user_id": "test_user",
                "preferences": {
                    "flavor_preference": "rich",
                    "sweetness": 7,
                    "dryness": 3,
                },
            })
        }

        response = handler(event, lambda_context)

        assert response["statusCode"] == 200
        assert mock_dynamodb.put_item.called

    def test_handler_delete_preferences(self, lambda_context, mock_dynamodb):
        """Test deleting user preferences."""
        from backend.lambdas.preference.handler import handler

        mock_dynamodb.delete_item.return_value = {}

        event = {"body": json.dumps({"action": "delete", "user_id": "test_user"})}

        response = handler(event, lambda_context)

        assert response["statusCode"] == 204
        assert mock_dynamodb.delete_item.called

    def test_handler_invalid_action(self, lambda_context):
        """Test handler with invalid action."""
        from backend.lambdas.preference.handler import handler

        event = {"body": json.dumps({"action": "invalid", "user_id": "test_user"})}

        response = handler(event, lambda_context)

        assert response["statusCode"] == 400

    def test_handler_update_with_validation_error(self, lambda_context):
        """Test update with invalid preference data."""
        from backend.lambdas.preference.handler import handler

        event = {
            "body": json.dumps({
                "action": "update",
                "user_id": "test_user",
                "preferences": {
                    "sweetness": 999,  # Invalid: out of range
                },
            })
        }

        response = handler(event, lambda_context)

        assert response["statusCode"] == 400
