"""
Unit tests for Tasting Lambda function.
"""

import json
from datetime import datetime
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


class TestTastingLambda:
    """Tests for Tasting Lambda handler."""

    def test_handler_create_record(self, lambda_context, mock_dynamodb):
        """Test creating a tasting record."""
        from backend.lambdas.tasting.handler import handler

        mock_dynamodb.put_item.return_value = {}

        event = {
            "body": json.dumps({
                "action": "create",
                "user_id": "test_user",
                "sake_name": "獺祭 純米大吟醸",
                "rating": 5,
                "notes": "とても美味しい",
                "aroma": 5,
                "taste": 5,
                "aftertaste": 4,
            })
        }

        response = handler(event, lambda_context)

        assert response["statusCode"] == 201
        body = json.loads(response["body"])
        assert "record_id" in body["data"]
        assert mock_dynamodb.put_item.called

    def test_handler_get_record(self, lambda_context, mock_dynamodb):
        """Test getting a tasting record."""
        from backend.lambdas.tasting.handler import handler

        mock_dynamodb.get_item.return_value = {
            "Item": {
                "record_id": "R123",
                "user_id": "test_user",
                "sake_name": "獺祭",
                "rating": 5,
                "created_at": "2025-10-01T12:00:00Z",
            }
        }

        event = {
            "body": json.dumps({"action": "get", "user_id": "test_user", "record_id": "R123"})
        }

        response = handler(event, lambda_context)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["data"]["record_id"] == "R123"

    def test_handler_get_record_not_found(self, lambda_context, mock_dynamodb):
        """Test getting non-existent record."""
        from backend.lambdas.tasting.handler import handler

        mock_dynamodb.get_item.return_value = {}

        event = {
            "body": json.dumps({"action": "get", "user_id": "test_user", "record_id": "INVALID"})
        }

        response = handler(event, lambda_context)

        assert response["statusCode"] == 404

    def test_handler_list_records(self, lambda_context, mock_dynamodb):
        """Test listing user's tasting records."""
        from backend.lambdas.tasting.handler import handler

        mock_dynamodb.query.return_value = {
            "Items": [
                {
                    "record_id": "R123",
                    "user_id": "test_user",
                    "sake_name": "獺祭",
                    "rating": 5,
                },
                {
                    "record_id": "R124",
                    "user_id": "test_user",
                    "sake_name": "久保田",
                    "rating": 4,
                },
            ]
        }

        event = {"body": json.dumps({"action": "list", "user_id": "test_user"})}

        response = handler(event, lambda_context)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert len(body["data"]["records"]) == 2

    def test_handler_delete_record(self, lambda_context, mock_dynamodb):
        """Test deleting a tasting record."""
        from backend.lambdas.tasting.handler import handler

        mock_dynamodb.delete_item.return_value = {}

        event = {
            "body": json.dumps({
                "action": "delete",
                "user_id": "test_user",
                "record_id": "R123",
            })
        }

        response = handler(event, lambda_context)

        assert response["statusCode"] == 204
        assert mock_dynamodb.delete_item.called

    def test_handler_missing_required_fields(self, lambda_context):
        """Test create with missing required fields."""
        from backend.lambdas.tasting.handler import handler

        event = {
            "body": json.dumps({"action": "create", "user_id": "test_user"})
            # Missing sake_name and rating
        }

        response = handler(event, lambda_context)

        assert response["statusCode"] == 400

    def test_handler_invalid_rating(self, lambda_context):
        """Test create with invalid rating value."""
        from backend.lambdas.tasting.handler import handler

        event = {
            "body": json.dumps({
                "action": "create",
                "user_id": "test_user",
                "sake_name": "Test Sake",
                "rating": 10,  # Invalid: max is 5
            })
        }

        response = handler(event, lambda_context)

        assert response["statusCode"] == 400

    def test_handler_update_record(self, lambda_context, mock_dynamodb):
        """Test updating a tasting record."""
        from backend.lambdas.tasting.handler import handler

        mock_dynamodb.get_item.return_value = {
            "Item": {"record_id": "R123", "user_id": "test_user", "sake_name": "獺祭"}
        }
        mock_dynamodb.update_item.return_value = {}

        event = {
            "body": json.dumps({
                "action": "update",
                "user_id": "test_user",
                "record_id": "R123",
                "rating": 5,
                "notes": "Updated notes",
            })
        }

        response = handler(event, lambda_context)

        assert response["statusCode"] == 200
        assert mock_dynamodb.update_item.called
