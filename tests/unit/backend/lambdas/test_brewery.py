"""
Unit tests for Brewery Lambda function.
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


class TestBreweryLambda:
    """Tests for Brewery Lambda handler."""

    def test_handler_get_brewery(self, lambda_context, mock_dynamodb):
        """Test getting brewery information."""
        from backend.lambdas.brewery.handler import handler

        mock_dynamodb.get_item.return_value = {
            "Item": {
                "brewery_id": "B001",
                "name": "旭酒造",
                "prefecture": "山口県",
                "established_year": 1948,
                "famous_brands": ["獺祭"],
            }
        }

        event = {"body": json.dumps({"action": "get", "brewery_id": "B001"})}

        response = handler(event, lambda_context)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["data"]["brewery_id"] == "B001"
        assert body["data"]["name"] == "旭酒造"

    def test_handler_get_brewery_not_found(self, lambda_context, mock_dynamodb):
        """Test getting non-existent brewery."""
        from backend.lambdas.brewery.handler import handler

        mock_dynamodb.get_item.return_value = {}

        event = {"body": json.dumps({"action": "get", "brewery_id": "INVALID"})}

        response = handler(event, lambda_context)

        assert response["statusCode"] == 404

    def test_handler_search_by_prefecture(self, lambda_context, mock_dynamodb):
        """Test searching breweries by prefecture."""
        from backend.lambdas.brewery.handler import handler

        mock_dynamodb.query.return_value = {
            "Items": [
                {"brewery_id": "B001", "name": "旭酒造", "prefecture": "山口県"},
                {"brewery_id": "B002", "name": "獺祭酒造", "prefecture": "山口県"},
            ]
        }

        event = {"body": json.dumps({"action": "search", "prefecture": "山口県"})}

        response = handler(event, lambda_context)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert len(body["data"]["breweries"]) == 2

    def test_handler_search_by_name(self, lambda_context, mock_dynamodb):
        """Test searching breweries by name."""
        from backend.lambdas.brewery.handler import handler

        mock_dynamodb.scan.return_value = {
            "Items": [{"brewery_id": "B001", "name": "旭酒造", "prefecture": "山口県"}]
        }

        event = {"body": json.dumps({"action": "search", "name": "旭酒造"})}

        response = handler(event, lambda_context)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert len(body["data"]["breweries"]) == 1
        assert body["data"]["breweries"][0]["name"] == "旭酒造"

    def test_handler_list_all_breweries(self, lambda_context, mock_dynamodb):
        """Test listing all breweries."""
        from backend.lambdas.brewery.handler import handler

        mock_dynamodb.scan.return_value = {
            "Items": [
                {"brewery_id": "B001", "name": "旭酒造"},
                {"brewery_id": "B002", "name": "久保田"},
                {"brewery_id": "B003", "name": "八海山"},
            ]
        }

        event = {"body": json.dumps({"action": "list"})}

        response = handler(event, lambda_context)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert len(body["data"]["breweries"]) == 3

    def test_handler_missing_brewery_id(self, lambda_context):
        """Test get action without brewery_id."""
        from backend.lambdas.brewery.handler import handler

        event = {"body": json.dumps({"action": "get"})}

        response = handler(event, lambda_context)

        assert response["statusCode"] == 400

    def test_handler_invalid_action(self, lambda_context):
        """Test handler with invalid action."""
        from backend.lambdas.brewery.handler import handler

        event = {"body": json.dumps({"action": "invalid"})}

        response = handler(event, lambda_context)

        assert response["statusCode"] == 400
